/* srmech_compose_run.c — the cascade.compose LINEAR CHAIN-RUNNER *RUN LOOP* in C
 * (0.9.0rc174; the ORCHESTRATION→C spine, batch 4).
 *
 * rc173 put the PARSE half (parse_chain_spec / parse_catalog_chains) in C. The
 * RUN loop stayed owed. This file RUNS a declared `[[catalog.operator_chain]]`
 * end-to-end in C, to BYTE-IDENTICAL OUTPUT — resolving each step's argument
 * references (@row / @input / @step[N].output) and dispatching a BOUNDED set of
 * shipped-chain ops (all Class N: pi_cascade_digits, the five *_series_truncate,
 * rational_add / _mul / _div / _pow_uint) to the EXISTING C kernels
 * (srmech_pi_archimedes / srmech_*_series_truncate_big / srmech_rational_pow_
 * uint_big + a bignum-ℚ add/mul/div composed from srmech_bigint, the bigexp
 * common-denominator pattern). So a bare-C host with NO Python runs the WHOLE
 * shipped apparatus (pi digits / asymptotic-calculus series / Friedmann
 * dark-fraction).
 *
 * PARITY IS ON OUTPUT, NOT THE CLOSURE. The Python resolve_chain returns a
 * live closure over the object graph; that is NOT mirrored. Instead the peer
 * runs the chain and marshals the FINAL value back as a small canonical-JSON
 * VALUE DESCRIPTOR ({"k":"s"/"q"/"i"/"n"/"l", ...} with bignums as decimal
 * strings), which the Python caller reconstructs. rc103 inform-don't-limit: any
 * op NOT in the dispatch table, any @catalog ref, any non-"raise" error policy,
 * any float / unsupported arg, any domain error / overflow → the peer returns
 * non-OK and the COMPLETE pure path runs (never a wrong answer; the pure path
 * raises the exact ChainSpecError / ValueError).
 *
 * ARENA: ONE caller arena `ws`, bump-allocated FORWARD, never reset — each
 * step's op scratch is carved + abandoned, each step OUTPUT persists (later
 * @step[N] refs read it). All bignum limbs alias into `ws`. Size it with
 * srmech_chain_run_arena_bytes (a generous static over-approximation; a
 * too-small arena → SRMECH_ERR_OVERFLOW → pure).
 *
 * JPL Power-of-Ten: caller-arena only (no malloc), <=60-line functions, >=2
 * asserts per function, no goto/recursion/abs/libm. Additive symbols →
 * SRMECH_ABI_VERSION stays 3 (the Python ctypes shim hasattr-guards them).
 */

#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

#include "srmech.h"

/* ------------------------------------------------------------------
 * Bump arena — forward-only carve, void*-aligned.
 * ------------------------------------------------------------------ */

typedef struct { unsigned char *cur; unsigned char *end; } cr_bump_t;

static unsigned char *cr_align(unsigned char *p)
{
    uintptr_t a = (uintptr_t)sizeof(void *);
    uintptr_t pad;
    assert(p != NULL);
    assert(a >= 4u);
    pad = (a - ((uintptr_t)p % a)) % a;
    return p + pad;
}

/* Carve `n` aligned bytes; NULL (no partial carve) if it does not fit. */
static unsigned char *cr_carve(cr_bump_t *b, size_t n)
{
    unsigned char *p;
    assert(b != NULL);
    assert(b->cur <= b->end);
    p = cr_align(b->cur);
    if (p > b->end || n > (size_t)(b->end - p)) { return NULL; }
    b->cur = p + n;
    return p;
}

/* Carve a zeroed srmech_bigint with `cap` limbs (a fresh value carrier). */
static srmech_bigint_t *cr_new_bigint(cr_bump_t *b, uint32_t cap)
{
    srmech_bigint_t *bi;
    uint32_t *limbs;
    assert(b != NULL);
    assert(cap > 0u);
    bi = (srmech_bigint_t *)cr_carve(b, sizeof(srmech_bigint_t));
    if (bi == NULL) { return NULL; }
    limbs = (uint32_t *)cr_carve(b, (size_t)cap * sizeof(uint32_t));
    if (limbs == NULL) { return NULL; }
    bi->sign = 0; bi->n = 0u; bi->cap = cap; bi->limbs = limbs;
    return bi;
}

/* ------------------------------------------------------------------
 * Chain value carrier — a tagged union threaded between steps.
 * ------------------------------------------------------------------ */

typedef enum {
    CR_NONE = 0, CR_INT, CR_STR, CR_RATIONAL, CR_LIST, CR_DBL
} cr_kind_t;

/* THE TUPLE CARRIER IS A FLAG ON CR_LIST, NOT A SIXTH KIND (v0.9.0rc451,
 * `#T1164`, gh #1653 item 4 — the RC-A slice).
 *
 * Python's chain vocabulary distinguishes a list from a 2-tuple and the
 * shipped comparator pins `tuple != list` as a required-DIVERGENT witness, so
 * the WIRE has to carry the distinction: srmech_chain_run's output-kind set
 * grows {n,i,s,q,f,l} -> +t, which IS a discriminator widening and is why this
 * rc bumps SRMECH_ABI_VERSION 19 -> 20 (the exact v18 shape — that bump added
 * f/l to THIS SAME wire).
 *
 * ⚠️ WHY A FLAG AND NOT A `CR_TUPLE` ENUM MEMBER. The in-tree precedent is the
 * sibling DSL interpreter, whose dv_value_t has carried `int is_tuple;` beside
 * DV_LIST since it shipped (srmech_dsl_chain_run.c) and emits 't' or 'l' off
 * it. A sixth enum member would instead have to widen every place that reads
 * the kind as CR_LIST — the kind-bounds assert in cr_new_value, cr_as_rational's
 * list arm, the @step[N].output[K] indexer cr_index_value, cr_list_to_f64 and
 * cr_desc — five switches, any one of which is a silent wrong answer if missed.
 * The flag touches NONE of them: a tuple is still a flat CR_LIST for every
 * consumer, and only the MARSHALLER asks the question. The discriminator that
 * widens is the wire's, which is the type the ruling names.
 */
typedef struct cr_value {
    cr_kind_t kind;
    srmech_bigint_t *num;      /* CR_INT: the value; CR_RATIONAL: numerator */
    srmech_bigint_t *den;      /* CR_RATIONAL: denominator (> 0, reduced)   */
    const char *s; uint32_t slen;          /* CR_STR (aliases arena)        */
    struct cr_value **items; uint32_t n;   /* CR_LIST                       */
    double d;                              /* CR_DBL                        */
    int is_tuple;              /* CR_LIST only: 1 -> marshals as {"k":"t"}  */
} cr_value_t;


static cr_value_t *cr_new_value(cr_bump_t *b, cr_kind_t kind)
{
    cr_value_t *v;
    assert(b != NULL);
    /* Bounds the WHOLE kind set — widen this with the enum or a new kind
     * aborts here. It caught CR_DBL on its first run, which is the assert
     * doing its job: a discriminator set has more members than the switch
     * statements that read it. */
    assert(kind >= CR_NONE && kind <= CR_DBL);
    v = (cr_value_t *)cr_carve(b, sizeof(cr_value_t));
    if (v == NULL) { return NULL; }
    v->kind = kind; v->num = NULL; v->den = NULL;
    v->s = NULL; v->slen = 0u; v->items = NULL; v->n = 0u; v->d = 0.0;
    v->is_tuple = 0;   /* LIST unless an op says otherwise — see cr_desc_list */
    return v;
}

/* A CR_DBL carrier. The carrier is EXACT: srmech's JSON writer formats a
 * double via srmech_double_repr (an integer-only Ryu matching CPython
 * repr(float) / json.dumps byte for byte), so a double survives the
 * C -> JSON -> Python trip with no last-bit drift and parity can be claimed
 * bit-exact. A snprintf("%.17g") writer could NOT carry that claim — which is
 * why this type was only safe to add after rc403 replaced it.
 *
 * ⚠️ A CR_DBL is deliberately NOT coercible to CR_INT or CR_RATIONAL. Every op
 * wanting an exact operand tests its kind and therefore DECLINES on a double
 * rather than rounding one: a silent float -> rational coercion would turn a
 * capability gap into a WRONG ANSWER, and would breach the stay-rational
 * discipline mid-cascade. Doubles enter and leave; they never become exact
 * operands along the way. */
static cr_value_t *cr_dbl(cr_bump_t *b, double v)
{
    cr_value_t *out;
    assert(b != NULL);
    assert(b->cur <= b->end);
    out = cr_new_value(b, CR_DBL);
    if (out == NULL) { return NULL; }
    out->d = v;
    return out;
}

/* A CR_INT carrier holding int64 v (small literals / row ints). */
static cr_value_t *cr_int_i64(cr_bump_t *b, int64_t v)
{
    cr_value_t *out;
    assert(b != NULL);
    assert(sizeof(v) == 8u);
    out = cr_new_value(b, CR_INT);
    if (out == NULL) { return NULL; }
    out->num = cr_new_bigint(b, 3u);
    if (out->num == NULL) { return NULL; }
    if (srmech_bigint_set_i64(out->num, v) != SRMECH_OK) { return NULL; }
    return out;
}

/* Read a CR_INT (or a 1-limb rational-free int) as a bounded uint32; -1 on a
 * negative / non-int / too-large value (the caller then defers to pure). */
static int64_t cr_as_uint(const cr_value_t *v)
{
    const srmech_bigint_t *bi;
    assert(v != NULL);
    if (v->kind != CR_INT || v->num == NULL) { return -1; }
    bi = v->num;
    assert(bi->cap >= bi->n);
    if (bi->sign < 0) { return -1; }
    if (bi->sign == 0) { return 0; }
    if (bi->n > 1u) { return -1; }               /* keep it <= 32-bit */
    return (int64_t)bi->limbs[0];
}

/* Coerce a value to a rational (num, den): a CR_RATIONAL directly, or a
 * CR_LIST of exactly two CR_INTs (the [num, den] arg form). 1 on success. */
static int cr_as_rational(const cr_value_t *v, const srmech_bigint_t **num,
                          const srmech_bigint_t **den)
{
    assert(v != NULL);
    assert(num != NULL && den != NULL);
    if (v->kind == CR_RATIONAL && v->num != NULL && v->den != NULL) {
        *num = v->num; *den = v->den; return 1;
    }
    if (v->kind == CR_LIST && v->n == 2u && v->items != NULL &&
        v->items[0] != NULL && v->items[1] != NULL &&
        v->items[0]->kind == CR_INT && v->items[1]->kind == CR_INT &&
        v->items[0]->num != NULL && v->items[1]->num != NULL) {
        *num = v->items[0]->num;   /* [num, den] list form */
        *den = v->items[1]->num;
        return 1;
    }
    return 0;
}

/* ------------------------------------------------------------------
 * Reference resolution — @row / @input / @step[N].output(.path). Mirrors
 * compose._resolve_reference. @catalog is NOT supported here (→ defer). A
 * JSON node is converted to a value carrier (int / string / list); a float /
 * object / bool arg → NULL (defer to pure).
 * ------------------------------------------------------------------ */

struct cr_ctx;   /* forward */

/* Walk a `.key` / `[N]` path into a JSON node (compose._resolve_dotted_path).
 * NULL on any miss (→ defer). Non-recursive. */
static const srmech_json_value_t *cr_walk_json(const srmech_json_value_t *node,
                                               const char *p, const char *e)
{
    assert(p != NULL && e != NULL);
    assert(p <= e);
    while (p < e && node != NULL) {
        if (*p == '.') {
            const char *k = p + 1; char key[64]; size_t kl = 0u;
            while (k < e && *k != '.' && *k != '[') {
                if (kl + 1u >= sizeof(key)) { return NULL; }
                key[kl++] = *k++;
            }
            key[kl] = '\0';
            if (node->type != SRMECH_JSON_OBJECT) { return NULL; }
            node = srmech_json_object_get(node, key);
            p = k;
        } else if (*p == '[') {
            const char *k = p + 1; uint32_t idx = 0u;
            while (k < e && *k >= '0' && *k <= '9') { idx = idx * 10u + (uint32_t)(*k++ - '0'); }
            if (k >= e || *k != ']') { return NULL; }
            if (node->type != SRMECH_JSON_ARRAY || idx >= node->u.arr.n) { return NULL; }
            node = node->u.arr.items[idx];
            p = k + 1;
        } else { return NULL; }
    }
    return node;
}

/* Convert a SCALAR json node (int / double / null / string-literal) to a value
 * carrier. NULL for ARRAY / OBJECT / BOOL — the run's args are flat (a rational
 * pair is a list of scalars), so NO nesting + NO recursion (JPL Rule 1).
 *
 * DOUBLE returned NULL through rc446, which is the `real_literal_arg` gate:
 * a chain carrying a real-number literal in its args could not be ingested at
 * all, whatever its ops were. That gate blocked 9 of the 18 executable chains. */
static cr_value_t *cr_json_scalar(cr_bump_t *b, const srmech_json_value_t *j)
{
    cr_value_t *out;
    assert(b != NULL);
    assert(j == NULL || j->type <= SRMECH_JSON_OBJECT);
    if (j == NULL) { return NULL; }
    if (j->type == SRMECH_JSON_INT) { return cr_int_i64(b, j->u.i); }
    if (j->type == SRMECH_JSON_DOUBLE) { return cr_dbl(b, j->u.f); }
    if (j->type == SRMECH_JSON_NULL) { return cr_new_value(b, CR_NONE); }
    /* BOOL -> CR_INT 0/1 (v0.9.0rc452, `#T1166`).
     *
     * ⚠️ THIS GAP WAS NAMED BY NO LISTED GATE. Through rc451 a BOOL arg returned
     * NULL here, so BOTH DFT chains deferred WHOLE — their proof cases pass
     * `inverse: false` (and `left` on the quaternion side) — and the rejection
     * was attributed to the op table and the carrier width, which were also
     * true and which no amount of work on would have released the chain.
     *
     * NO OUTPUT KIND IS ADDED, and that is MEASURED rather than assumed: over
     * the 21 packaged descriptors, ZERO declare a bool return (the census also
     * says bools appear ONLY as inputs, on exactly octonion_dft.inverse,
     * quaternion_dft.inverse and quaternion_dft.left). So a bool can enter and
     * be consumed but can never be the value that crosses the wire, and
     * carrying it as CR_INT cannot silently change an output type. Python
     * agrees on the arithmetic — `bool` IS an `int` subclass there, so
     * `int(False) == 0` is the same coercion, not a C-side convention.
     * If a chain ever DOES declare a bool return, this comment is the reason
     * it needs its own kind letter rather than riding `i`. */
    if (j->type == SRMECH_JSON_BOOL) { return cr_int_i64(b, j->u.b ? 1 : 0); }
    if (j->type != SRMECH_JSON_STRING) { return NULL; }   /* array / object */
    out = cr_new_value(b, CR_STR);
    if (out == NULL) { return NULL; }
    out->s = j->u.str.ptr; out->slen = j->u.str.len;
    return out;
}

/* ------------------------------------------------------------------
 * NESTED VALUE INGEST (v0.9.0rc452, `#T1166`) — depth-bounded, explicit stack.
 *
 * Through rc451 an array ingested ONE level: `cr_json_list` called
 * `cr_json_scalar` per element and a nested array element returned NULL, so the
 * whole chain deferred. That is gap-ledger row `chain_run_list_is_flat_only`,
 * and it is wider than the two DFT chains the BLOCKED table attributes it to —
 * klein4's depth-2 bind literals, kuramoto-general's `adjacency`, and schur's
 * `L` all need it too.
 *
 * ⚠️ NO NEW KIND, NO READER CHANGE. Nesting is a CR_LIST holding CR_LISTs; the
 * `l` kind already exists and Python's `_reconstruct_value` has been recursive
 * all along. So this widens a CAPABILITY, not a discriminator — which is why
 * the gap-ledger row carries new_type=false and why no ABI implication follows
 * from this half.
 *
 * ⚠️ WHY A STACK AND NOT RECURSION. JPL Rule 1 bans new recursion, and the
 * obvious shape here (a walker that re-enters itself per element) is exactly
 * that. The frame array is carved from the CALLER ARENA (Rule 3: no malloc) and
 * the depth is capped by an assert. Cap 4 against a MEASURED maximum of 2 over
 * every packaged descriptor's proof cases — generous, and bounded, so an
 * adversarial document cannot walk the stack off its end.
 * ------------------------------------------------------------------ */

#define CR_MAX_DEPTH 4u

typedef struct {
    const srmech_json_value_t *node;   /* the ARRAY being ingested */
    cr_value_t *val;                   /* its CR_LIST carrier */
    uint32_t i;                        /* next child slot */
} cr_iframe_t;

/* Carve a CR_LIST carrier sized for `n` items. NULL on overflow. */
static cr_value_t *cr_list_of(cr_bump_t *b, uint32_t n)
{
    cr_value_t *v;
    assert(b != NULL);
    assert(b->cur <= b->end);
    v = cr_new_value(b, CR_LIST);
    if (v == NULL) { return NULL; }
    v->n = n;
    v->items = (cr_value_t **)cr_carve(b, (size_t)n * sizeof(void *) + sizeof(void *));
    return (v->items == NULL) ? NULL : v;
}

/* Ingest an ARRAY node to a (possibly nested) CR_LIST. NULL → defer. */
static cr_value_t *cr_json_nested(cr_bump_t *b, const srmech_json_value_t *j)
{
    cr_iframe_t st[CR_MAX_DEPTH]; uint32_t sp = 0u;
    assert(b != NULL && j != NULL);
    assert(j->type == SRMECH_JSON_ARRAY);
    st[0].node = j; st[0].val = cr_list_of(b, j->u.arr.n); st[0].i = 0u;
    if (st[0].val == NULL) { return NULL; }
    sp = 1u;
    while (sp > 0u) {
        cr_iframe_t *f = &st[sp - 1u];
        if (f->i < f->node->u.arr.n) {
            const srmech_json_value_t *ch = f->node->u.arr.items[f->i];
            if (ch != NULL && ch->type == SRMECH_JSON_ARRAY) {
                if (sp >= CR_MAX_DEPTH) { return NULL; }   /* too deep → defer */
                st[sp].node = ch; st[sp].val = cr_list_of(b, ch->u.arr.n);
                st[sp].i = 0u;
                if (st[sp].val == NULL) { return NULL; }
                sp++;                       /* parent's i advances on POP */
                continue;
            }
            f->val->items[f->i] = cr_json_scalar(b, ch);
            if (f->val->items[f->i] == NULL) { return NULL; }
            f->i++;
            continue;
        }
        sp--;                               /* frame complete */
        if (sp == 0u) { return st[0].val; }
        st[sp - 1u].val->items[st[sp - 1u].i] = f->val;
        st[sp - 1u].i++;
    }
    return st[0].val;
}

/* Convert a resolved JSON node (from a @row/@input walk) to a value carrier:
 * a (possibly nested) list, else a scalar. NULL → defer. */
static cr_value_t *cr_json_to_value(cr_bump_t *b, const srmech_json_value_t *j)
{
    assert(b != NULL);
    assert(j == NULL || j->type <= SRMECH_JSON_OBJECT);
    if (j != NULL && j->type == SRMECH_JSON_ARRAY) { return cr_json_nested(b, j); }
    return cr_json_scalar(b, j);
}

/* ------------------------------------------------------------------
 * The run context (row / inputs JSON + the persisting step outputs).
 * ------------------------------------------------------------------ */

/* ------------------------------------------------------------------
 * THE MAP FRAME (v0.9.0rc452, `#T1166`).
 *
 * A map body is "a chain in miniature" (compose.py's rc420 scoping decision):
 * it runs with its OWN body-local step outputs and a LAYERED idx/bind
 * environment. Measured map nesting over the packaged descriptors: 2
 * (autocorrelation, kuramoto_step and both DFTs are map-inside-map), so the
 * cap of 4 is generous and, being a cap, is what keeps JPL Rule 1 satisfiable
 * without recursion.
 *
 * ⚠️ THE TOP LEVEL IS FRAME 0, AS A DEGENERATE MAP OF n == 1. That is not a
 * trick to save code — it is what makes the trampoline uniform, so the body
 * of a map and the body of the chain cannot drift apart in how they resolve
 * `@step[N]`, scope their outputs, or decide what "the final value" is. Frame 0
 * is the one with `acc == NULL`, which is precisely the statement "my result is
 * my last step's output, not a list of my iterations".
 * ------------------------------------------------------------------ */

#define CR_MAP_DEPTH 4u
#define CR_BIND_MAX  8u

typedef struct {
    const srmech_json_value_t *body;   /* the step ARRAY this frame runs   */
    uint32_t si;                       /* next step index within `body`    */
    uint32_t k;                        /* current iteration                */
    uint32_t n;                        /* iteration count, PINNED at entry */
    cr_value_t **outs;                 /* body-local step outputs          */
    cr_value_t *acc;                   /* the result list; NULL at frame 0 */
    const char *idx_name; uint32_t idx_len;
    const char *bname[CR_BIND_MAX]; uint32_t blen[CR_BIND_MAX];
    cr_value_t *bval[CR_BIND_MAX]; uint32_t nb;
} cr_mapframe_t;

typedef struct cr_ctx {
    const srmech_json_value_t *row;      /* or NULL */
    const srmech_json_value_t *inputs;   /* or NULL */
    cr_value_t **step_out;               /* the ACTIVE frame's outputs */
    uint32_t cur;                        /* index of the step being run */
    cr_bump_t *b;
    cr_mapframe_t *fr;                   /* [CR_MAP_DEPTH] frame stack */
    uint32_t nfr;                        /* active frame count (>= 1) */
} cr_ctx_t;

/* Resolve `@idx.<name>` by walking the frame stack INNERMOST-OUTWARD.
 *
 * Walking outward IS the layering: compose.py builds each body's environment as
 * `{**idx_env, index: k}`, so an inner name shadows an outer one of the same
 * spelling. Scanning from the innermost frame and stopping at the first hit
 * reproduces that without copying an environment per iteration. -1 = unbound. */
static int64_t cr_env_idx(const cr_ctx_t *c, const char *nm, uint32_t nl)
{
    uint32_t d;
    assert(c != NULL && nm != NULL);
    assert(c->nfr >= 1u);
    for (d = c->nfr; d > 0u; d--) {
        const cr_mapframe_t *f = &c->fr[d - 1u];
        if (f->idx_name != NULL && f->idx_len == nl &&
            memcmp(f->idx_name, nm, nl) == 0) {
            return (int64_t)f->k;
        }
    }
    return -1;
}

/* Resolve `@bind.<name>` the same way. NULL = unbound. */
static cr_value_t *cr_env_bind(const cr_ctx_t *c, const char *nm, uint32_t nl)
{
    uint32_t d, i;
    assert(c != NULL && nm != NULL);
    assert(c->nfr >= 1u);
    for (d = c->nfr; d > 0u; d--) {
        const cr_mapframe_t *f = &c->fr[d - 1u];
        for (i = 0u; i < f->nb; i++) {
            if (f->blen[i] == nl && memcmp(f->bname[i], nm, nl) == 0) {
                return f->bval[i];
            }
        }
    }
    return NULL;
}

/* Resolve a `@...` reference string to a value carrier. NULL → defer. */
/* Index a step output: the `[K]` tail of `@step[N].output[K]`. Returns NULL
 * (defer) for a non-list carrier, an out-of-range K, or any tail that is not
 * exactly one bracketed decimal — a `.key` tail would need a MAPPING carrier,
 * which does not exist, so it declines rather than pretending.
 *
 * Through rc447 the step arm accepted only a BARE `.output` and rejected this
 * outright. Note the shapes differ from the @row / @input walk: those descend a
 * parsed JSON tree, this indexes an already-computed cr_value_t, so cr_walk_json
 * cannot be reused however similar the syntax looks. */
static cr_value_t *cr_index_value(cr_value_t *v, const char *p, const char *e)
{
    uint32_t idx = 0u; int digits = 0;
    assert(p != NULL && e != NULL);
    assert(p <= e);
    if (v == NULL || v->kind != CR_LIST) { return NULL; }
    if (p >= e || *p != '[') { return NULL; }
    p++;
    while (p < e && *p >= '0' && *p <= '9') {
        idx = idx * 10u + (uint32_t)(*p++ - '0');
        digits++;
        if (digits > 9) { return NULL; }        /* absurd index → defer */
    }
    if (digits == 0 || p >= e || *p != ']') { return NULL; }
    if (p + 1 != e) { return NULL; }            /* a chained tail → defer */
    if (idx >= v->n) { return NULL; }           /* out of range → defer, never wrap */
    return v->items[idx];
}

static cr_value_t *cr_resolve_ref(cr_ctx_t *c, const char *ref, uint32_t len)
{
    const char *e = ref + len; const char *p;
    assert(c != NULL && ref != NULL);
    assert(c->b != NULL);
    if (len < 2u || ref[0] != '@') { return NULL; }
    p = ref + 1;
    if (len >= 5u && memcmp(p, "row.", 4u) == 0) {
        return cr_json_to_value(c->b, cr_walk_json(c->row, p + 3, e));
    }
    if (len >= 7u && memcmp(p, "input.", 6u) == 0) {
        return cr_json_to_value(c->b, cr_walk_json(c->inputs, p + 5, e));
    }
    if (len >= 6u && memcmp(p, "step[", 5u) == 0) {
        const char *k = p + 5; uint32_t idx = 0u; const char *rest;
        while (k < e && *k >= '0' && *k <= '9') { idx = idx * 10u + (uint32_t)(*k++ - '0'); }
        if (k >= e || *k != ']') { return NULL; }
        if (idx >= c->cur) { return NULL; }
        rest = k + 1;
        if (rest + 7 <= e && memcmp(rest, ".output", 7u) == 0) { rest += 7; }
        if (rest == e) { return c->step_out[idx]; }
        return cr_index_value(c->step_out[idx], rest, e);
    }
    /* @idx.<name> / @bind.<name> (v0.9.0rc452, `#T1166`) — two of the three
     * namespaces GATE_REF_GRAMMAR names.
     *
     * ⚠️ THEY ARE FRAME BINDINGS, NOT A WIDER PATH WALKER, AND THAT IS
     * MEASURED. Probing the refspaces of all five map chains: `@idx` and
     * `@bind` occur ONLY inside map bodies — never at a chain's top level. So
     * they are not addresses into the row/input trees that cr_walk_json
     * descends; they are lexical bindings of the enclosing map frames, and
     * resolving them needs the frame stack rather than a longer path grammar.
     * That is why they could not be closed before the map form existed.
     *
     * `@bind.x` may carry a `.key`/`[N]` tail; `@idx.k` is a bare integer and
     * a tail on it is a malformed ref, so it declines rather than ignoring it. */
    if (len >= 6u && memcmp(p, "idx.", 4u) == 0) {
        const char *nm = p + 4; int64_t v;
        if (nm >= e) { return NULL; }
        v = cr_env_idx(c, nm, (uint32_t)(e - nm));
        if (v < 0) { return NULL; }              /* unbound → defer */
        return cr_int_i64(c->b, v);
    }
    if (len >= 7u && memcmp(p, "bind.", 5u) == 0) {
        const char *nm = p + 5; const char *t = nm; cr_value_t *bv;
        if (nm >= e) { return NULL; }
        while (t < e && *t != '.' && *t != '[') { t++; }
        bv = cr_env_bind(c, nm, (uint32_t)(t - nm));
        if (bv == NULL) { return NULL; }         /* unbound → defer */
        if (t == e) { return bv; }
        return cr_index_value(bv, t, e);         /* a `[N]` tail */
    }
    return NULL;   /* @catalog / @op or unknown → defer */
}

/* A list ELEMENT: a `@...` ref, a NESTED array literal, or a scalar literal.
 *
 * The nested arm rides cr_json_nested's explicit stack, so still no recursion.
 * It carries LITERALS only — a ref inside a nested literal would need the ctx,
 * which cr_json_nested deliberately does not take. Measured over the packaged
 * descriptors: nested literals (kuramoto-general `adjacency`, schur `L`, the
 * klein4 bind literals) are pure data, and refs appear only at the top level or
 * as whole args. A ref nested inside an array literal therefore declines rather
 * than resolving wrongly. */
static cr_value_t *cr_resolve_elem(cr_ctx_t *c, const srmech_json_value_t *j)
{
    assert(c != NULL);
    assert(c->b != NULL);
    if (j == NULL) { return NULL; }
    if (j->type == SRMECH_JSON_STRING && j->u.str.len > 0u &&
        j->u.str.ptr[0] == '@') {
        return cr_resolve_ref(c, j->u.str.ptr, j->u.str.len);
    }
    if (j->type == SRMECH_JSON_ARRAY) { return cr_json_nested(c->b, j); }
    return cr_json_scalar(c->b, j);
}

/* Resolve one arg JSON node to a value carrier: a `@...` string → a ref, a flat
 * list → per-element refs/scalars, a literal → a scalar. NULL → defer. No
 * recursion — the args are at most one list level deep (a rational pair). */
static cr_value_t *cr_resolve_arg(cr_ctx_t *c, const srmech_json_value_t *j)
{
    cr_value_t *out; cr_value_t **items; uint32_t i;
    assert(c != NULL);
    assert(c->b != NULL);
    if (j == NULL) { return NULL; }
    if (j->type == SRMECH_JSON_STRING && j->u.str.len > 0u &&
        j->u.str.ptr[0] == '@') {
        return cr_resolve_ref(c, j->u.str.ptr, j->u.str.len);
    }
    if (j->type != SRMECH_JSON_ARRAY) { return cr_json_scalar(c->b, j); }
    out = cr_new_value(c->b, CR_LIST);
    if (out == NULL) { return NULL; }
    out->n = j->u.arr.n;
    items = (cr_value_t **)cr_carve(c->b, (size_t)out->n * sizeof(void *) + 1u);
    if (items == NULL) { return NULL; }
    for (i = 0u; i < out->n; i++) {
        items[i] = cr_resolve_elem(c, j->u.arr.items[i]);   /* NO recursion */
        if (items[i] == NULL) { return NULL; }
    }
    out->items = items;
    return out;
}

/* Resolve a named arg from the step's `args` object. NULL → missing / defer. */
static cr_value_t *cr_arg(cr_ctx_t *c, const srmech_json_value_t *args,
                          const char *key)
{
    const srmech_json_value_t *j;
    assert(c != NULL && args != NULL && key != NULL);
    assert(args->type == SRMECH_JSON_OBJECT);
    j = srmech_json_object_get(args, key);
    if (j == NULL) { return NULL; }
    return cr_resolve_arg(c, j);
}

/* ------------------------------------------------------------------
 * Bignum-ℚ arithmetic (the rational_add / _mul / _div wrappers) — the
 * bigexp common-denominator pattern, over caller-arena carriers. Reduces to
 * lowest terms with positive denominator (byte-identical to bigq_*_c).
 * ------------------------------------------------------------------ */

typedef struct {
    srmech_bigint_t *t0, *t1, *t2, *g, *q, *r;   /* scratch carriers */
    void *scr; size_t scr_len;                   /* divmod/gcd arena */
} cr_qctx_t;

/* Carve the ℚ scratch context sized for operands up to `lim` limbs. */
static int cr_qctx_init(cr_bump_t *b, cr_qctx_t *q, uint32_t lim)
{
    uint32_t cap = lim * 2u + 8u; size_t scr;
    assert(b != NULL && q != NULL);
    assert(lim > 0u);
    q->t0 = cr_new_bigint(b, cap); q->t1 = cr_new_bigint(b, cap);
    q->t2 = cr_new_bigint(b, cap); q->g = cr_new_bigint(b, cap);
    q->q = cr_new_bigint(b, cap);  q->r = cr_new_bigint(b, cap);
    if (q->t0 == NULL || q->t1 == NULL || q->t2 == NULL ||
        q->g == NULL || q->q == NULL || q->r == NULL) { return 0; }
    scr = (size_t)cap * 12u * sizeof(uint32_t) + 512u;
    q->scr = cr_carve(b, scr);
    if (q->scr == NULL) { return 0; }
    q->scr_len = scr;
    return 1;
}

/* out_num/out_den = reduce(n/d) to lowest terms, positive denominator. */
static srmech_status_t cr_q_reduce(cr_qctx_t *q, srmech_bigint_t *n,
                                   srmech_bigint_t *d, srmech_bigint_t *out_num,
                                   srmech_bigint_t *out_den)
{
    srmech_status_t st;
    assert(q != NULL && n != NULL && d != NULL);
    assert(out_num != NULL && out_den != NULL);
    if (d->sign < 0) { d->sign = 1; n->sign = -n->sign; }   /* den > 0 */
    if (srmech_bigint_is_zero(n)) {
        st = srmech_bigint_set_i64(out_num, 0);
        if (st != SRMECH_OK) { return st; }
        return srmech_bigint_set_i64(out_den, 1);
    }
    st = srmech_bigint_gcd(q->g, n, d, q->scr, q->scr_len);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_divmod(out_num, q->r, n, q->g, q->scr, q->scr_len);
    if (st != SRMECH_OK) { return st; }
    return srmech_bigint_divmod(out_den, q->r, d, q->g, q->scr, q->scr_len);
}

/* out = a * b (via scratch t0 so out may alias neither a nor b uniquely). */
static srmech_status_t cr_q_mul(cr_qctx_t *q, srmech_bigint_t *out,
                                const srmech_bigint_t *a, const srmech_bigint_t *b)
{
    srmech_status_t st;
    assert(q != NULL && out != NULL && a != NULL && b != NULL);
    assert(out != a && out != b);
    st = srmech_bigint_mul(q->t0, a, b);
    if (st != SRMECH_OK) { return st; }
    return srmech_bigint_copy(out, q->t0);
}

/* out = (an/ad) OP (bn/bd), reduced; op in {'+','*','/'} */
static srmech_status_t cr_q_binop(cr_qctx_t *q, char op,
                                  const srmech_bigint_t *an, const srmech_bigint_t *ad,
                                  const srmech_bigint_t *bn, const srmech_bigint_t *bd,
                                  srmech_bigint_t *out_num, srmech_bigint_t *out_den)
{
    srmech_status_t st;
    assert(q != NULL);
    assert(out_num != NULL && out_den != NULL);
    if (op == '*') {
        st = cr_q_mul(q, q->t1, an, bn); if (st != SRMECH_OK) { return st; }
        st = cr_q_mul(q, q->t2, ad, bd); if (st != SRMECH_OK) { return st; }
    } else if (op == '/') {
        if (srmech_bigint_is_zero(bn)) { return SRMECH_ERR_BAD_INPUT; }
        st = cr_q_mul(q, q->t1, an, bd); if (st != SRMECH_OK) { return st; }
        st = cr_q_mul(q, q->t2, ad, bn); if (st != SRMECH_OK) { return st; }
    } else {   /* '+' : num = an*bd + bn*ad ; den = ad*bd */
        st = cr_q_mul(q, q->g, an, bd); if (st != SRMECH_OK) { return st; }
        st = cr_q_mul(q, q->q, bn, ad); if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_add(q->t1, q->g, q->q); if (st != SRMECH_OK) { return st; }
        st = cr_q_mul(q, q->t2, ad, bd); if (st != SRMECH_OK) { return st; }
    }
    return cr_q_reduce(q, q->t1, q->t2, out_num, out_den);
}

/* ------------------------------------------------------------------
 * Dispatch wrappers — op name → unpack value-carrier args + call the EXISTING
 * C kernel + wrap the result. Each writes *out (a fresh persisting carrier) and
 * returns SRMECH_OK, or non-OK to DEFER the whole chain to the pure path. Only
 * the bounded shipped-chain op set (all Class N). Bignum outputs are sized
 * generously from the input magnitudes (rc156 _bigexp_call envelope).
 * ------------------------------------------------------------------ */

/* Output-carrier + bigexp-arena limb budget for a series/pow op of `num_terms`
 * over an input of `dig` significant decimal digits (both operands). */
static uint32_t cr_big_out_cap(uint32_t num_terms, uint32_t dig)
{
    uint32_t cap = 32u * (num_terms + dig) + 64u;
    assert(num_terms <= 65535u);
    assert(cap >= 64u);
    return cap;
}

/* Decimal-digit count of a bigint's magnitude (for the arena envelope). */
static uint32_t cr_bigint_digits(const srmech_bigint_t *a)
{
    uint32_t d;
    assert(a != NULL);
    assert(a->cap >= a->n);
    d = a->n * 10u + 2u;   /* 32-bit limb ~ <=10 decimal digits */
    return d;
}

/* pi_cascade_digits(num_digits[, max_cascade_depth, precision]) -> str.
 * Auto-scales depth/precision the same as rational.pi_cascade_digits.
 *
 * ⚠️ rc449 (`#T1158`): this read "precision_bits" until now — the pre-rc318 name.
 * rc318 renamed the Python kwarg to `precision` for the uniform Class-N precision
 * contract ("a pure rename, digits bit-identical", rational.py) and the rename
 * never reached this file, so the two projections had disagreed on the key's NAME
 * for 131 rcs, in BOTH directions and silently:
 *
 *   * `precision` — legal in Python, and IGNORED here. MEASURED at rc448:
 *     pi_cascade_digits(100, precision=64) returns
 *     3.14159265358979323704913602655075521852... from Python (it honours the
 *     narrow precision and degrades after ~19 places) while this runner never read
 *     the key, auto-scaled to 1024 bits, and returned the fully correct expansion.
 *     Same declaration, two co-equal projections, DIFFERENT DIGITS OF PI, no error.
 *   * `precision_bits` — refused by Python (TypeError) and honoured here: the
 *     `#T1158` divergence proper, on an op whose whole output is a number.
 *
 * Nothing in the tree passes `precision_bits` on a chain, so this is a rename, not
 * a break. It also had to be settled before the params[*] validator above could
 * ship: that rule reads the registry, the registry says `precision`, and leaving
 * this line alone would have made the validator refuse the very key C reads. */
static srmech_status_t cr_op_pi(cr_ctx_t *c, const srmech_json_value_t *args,
                                cr_value_t **out)
{
    cr_value_t *nd = cr_arg(c, args, "num_digits"), *dep, *prc, *ov;
    int64_t num_digits, depth, prec; char *buf; size_t olen; void *ws; size_t wl;
    uint32_t m_limbs, d_limbs, cap, ws_words; srmech_status_t st;
    assert(c != NULL && out != NULL);
    assert(args != NULL);
    if (nd == NULL) { return SRMECH_ERR_BAD_INPUT; }
    num_digits = cr_as_uint(nd);
    if (num_digits < 1 || num_digits > 100000) { return SRMECH_ERR_BAD_INPUT; }
    dep = cr_arg(c, args, "max_cascade_depth"); prc = cr_arg(c, args, "precision");
    depth = dep ? cr_as_uint(dep) : (num_digits * 90 + 49) / 50;
    if (depth < 90) { depth = 90; }
    prec = prc ? cr_as_uint(prc) : (num_digits * 512 + 49) / 50;
    if (prec < 512) { prec = 512; }
    if (depth <= 0 || prec <= 0) { return SRMECH_ERR_BAD_INPUT; }
    m_limbs = (uint32_t)(prec / 32 + 2); d_limbs = (uint32_t)(num_digits / 9 + 2);
    cap = 2u * m_limbs + d_limbs + 32u;
    ws_words = cap * 9u + 24u * m_limbs + 8u * d_limbs + 512u;
    ws = cr_carve(c->b, (size_t)ws_words * 4u);
    buf = (char *)cr_carve(c->b, (size_t)num_digits + 8u);
    if (ws == NULL || buf == NULL) { return SRMECH_ERR_OVERFLOW; }
    wl = (size_t)ws_words * 4u;
    st = srmech_pi_archimedes((uint32_t)num_digits, (uint32_t)depth,
                              (uint32_t)prec, buf, (size_t)num_digits + 8u,
                              &olen, ws, wl);
    if (st != SRMECH_OK) { return st; }
    ov = cr_new_value(c->b, CR_STR);
    if (ov == NULL) { return SRMECH_ERR_OVERFLOW; }
    ov->s = buf; ov->slen = (uint32_t)olen; *out = ov;
    return SRMECH_OK;
}

typedef srmech_status_t (*cr_series_fn_t)(const srmech_bigint_t *, const srmech_bigint_t *,
                                          uint32_t, srmech_bigint_t *, srmech_bigint_t *,
                                          void *, size_t);

/* Shared driver for the five *_series_truncate ops:
 * (numerator, denominator, num_terms) -> reduced (num, den) rational. */
static srmech_status_t cr_op_series(cr_ctx_t *c, const srmech_json_value_t *args,
                                    cr_series_fn_t fn, cr_value_t **out)
{
    cr_value_t *xn = cr_arg(c, args, "numerator");
    cr_value_t *xd = cr_arg(c, args, "denominator");
    cr_value_t *nt = cr_arg(c, args, "num_terms"), *ov;
    int64_t nterms; uint32_t cap, dig; void *ws; size_t wl; srmech_status_t st;
    assert(c != NULL && out != NULL);
    assert(fn != NULL && args != NULL);
    if (xn == NULL || xd == NULL || nt == NULL) { return SRMECH_ERR_BAD_INPUT; }
    if (xn->kind != CR_INT || xd->kind != CR_INT || xn->num == NULL ||
        xd->num == NULL) { return SRMECH_ERR_BAD_INPUT; }
    nterms = cr_as_uint(nt);
    if (nterms < 0 || nterms > 512) { return SRMECH_ERR_BAD_INPUT; }
    dig = cr_bigint_digits(xn->num) + cr_bigint_digits(xd->num);
    cap = cr_big_out_cap((uint32_t)nterms, dig);
    ov = cr_new_value(c->b, CR_RATIONAL);
    if (ov == NULL) { return SRMECH_ERR_OVERFLOW; }
    ov->num = cr_new_bigint(c->b, cap); ov->den = cr_new_bigint(c->b, cap);
    wl = (size_t)srmech_bigexp_ws_bound(xn->num->n, xd->num->n, (uint32_t)nterms);
    ws = cr_carve(c->b, wl);
    if (ov->num == NULL || ov->den == NULL || ws == NULL) { return SRMECH_ERR_OVERFLOW; }
    st = fn(xn->num, xd->num, (uint32_t)nterms, ov->num, ov->den, ws, wl);
    if (st != SRMECH_OK) { return st; }
    *out = ov;
    return SRMECH_OK;
}

/* rational_pow_uint(base=[num,den], exp) -> reduced (num, den). */
static srmech_status_t cr_op_pow(cr_ctx_t *c, const srmech_json_value_t *args,
                                 cr_value_t **out)
{
    cr_value_t *base = cr_arg(c, args, "base"), *ex = cr_arg(c, args, "exp"), *ov;
    const srmech_bigint_t *bn, *bd; int64_t e; uint32_t cap, dig; void *ws;
    size_t wl; srmech_status_t st;
    assert(c != NULL && out != NULL);
    assert(args != NULL);
    if (base == NULL || ex == NULL || !cr_as_rational(base, &bn, &bd)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    e = cr_as_uint(ex);
    if (e < 0 || e > 65535) { return SRMECH_ERR_BAD_INPUT; }
    dig = cr_bigint_digits(bn) + cr_bigint_digits(bd);
    cap = cr_big_out_cap((uint32_t)e, dig);
    ov = cr_new_value(c->b, CR_RATIONAL);
    if (ov == NULL) { return SRMECH_ERR_OVERFLOW; }
    ov->num = cr_new_bigint(c->b, cap); ov->den = cr_new_bigint(c->b, cap);
    wl = (size_t)srmech_bigexp_ws_bound(bn->n, bd->n, (uint32_t)e);
    ws = cr_carve(c->b, wl);
    if (ov->num == NULL || ov->den == NULL || ws == NULL) { return SRMECH_ERR_OVERFLOW; }
    st = srmech_rational_pow_uint_big(bn, bd, (uint32_t)e, ov->num, ov->den, ws, wl);
    if (st != SRMECH_OK) { return st; }
    *out = ov;
    return SRMECH_OK;
}

/* rational_add / _mul / _div(a=[num,den], b=[num,den]) -> reduced (num, den). */
static srmech_status_t cr_op_rat(cr_ctx_t *c, const srmech_json_value_t *args,
                                 char op, cr_value_t **out)
{
    cr_value_t *va = cr_arg(c, args, "a"), *vb = cr_arg(c, args, "b"), *ov;
    const srmech_bigint_t *an, *ad, *bn, *bd; uint32_t lim, cap; cr_qctx_t q;
    srmech_status_t st;
    assert(c != NULL && out != NULL);
    assert(op == '+' || op == '*' || op == '/');
    if (va == NULL || vb == NULL || !cr_as_rational(va, &an, &ad) ||
        !cr_as_rational(vb, &bn, &bd)) { return SRMECH_ERR_BAD_INPUT; }
    lim = an->n + ad->n + bn->n + bd->n + 4u;
    cap = lim * 2u + 8u;
    ov = cr_new_value(c->b, CR_RATIONAL);
    if (ov == NULL) { return SRMECH_ERR_OVERFLOW; }
    ov->num = cr_new_bigint(c->b, cap); ov->den = cr_new_bigint(c->b, cap);
    if (ov->num == NULL || ov->den == NULL) { return SRMECH_ERR_OVERFLOW; }
    if (!cr_qctx_init(c->b, &q, lim)) { return SRMECH_ERR_OVERFLOW; }
    st = cr_q_binop(&q, op, an, ad, bn, bd, ov->num, ov->den);
    if (st != SRMECH_OK) { return st; }
    *out = ov;
    return SRMECH_OK;
}

/* ------------------------------------------------------------------
 * Class-I cyclic-group ops (gh #1653). The chain carrier is arbitrary
 * precision; the shipped Class-I exports take uint64. Where an operand does
 * not fit that wire this DECLINES (SRMECH_ERR_NOT_IMPL, so the chain defers
 * to the pure runner) rather than narrowing it — a narrower projection must
 * REFUSE, never silently answer, or the two projections disagree on a value
 * instead of on a capability.
 * ------------------------------------------------------------------ */

/* Read a non-negative CR_INT as uint64. 1 on success, 0 → caller declines.
 * cr_as_uint above stops at ONE limb (32-bit); the Class-I wire is 64. */
static int cr_as_u64(const cr_value_t *v, uint64_t *out)
{
    const srmech_bigint_t *bi;
    assert(out != NULL);
    assert(v != NULL);
    if (v->kind != CR_INT || v->num == NULL) { return 0; }
    bi = v->num;
    if (bi->sign < 0) { return 0; }              /* Class-I wire is unsigned */
    if (bi->sign == 0) { *out = 0u; return 1; }
    if (bi->n > 2u) { return 0; }                /* exceeds the uint64 wire */
    *out = (uint64_t)bi->limbs[0];
    if (bi->n == 2u) { *out |= ((uint64_t)bi->limbs[1]) << 32; }
    return 1;
}

/* THE rc176 DECIMAL-STRING BIGNUM TRANSPORT, applied to the chain runner.
 *
 * srmech_json_parse DECLINES an integer literal wider than int64 with
 * SRMECH_ERR_LIMIT — deliberately, since int64_t genuinely cannot hold it and a
 * clamped value would be a silent wrong answer (rc402/rc404). The established
 * in-tree answer is NOT to widen the parser but to carry such a value as a
 * DECIMAL STRING: srmech_carrier_marshal.c has read coefficients that way since
 * rc176 ("each scalar is a JSON int64 OR a decimal STRING ... a bignum
 * coefficient rides as a decimal string, never clamped").
 *
 * The chain runner was the one numeric surface that did NOT honour that
 * convention, which is why rc447's bigint widening was measurably unreachable
 * from a descriptor: the carrier was arbitrary-precision while its only input
 * path was int64. Found by the bare-C host proof.
 *
 * ⚠️ CONVERTED AT THE POINT OF USE, NOT AT INGEST. cr_json_scalar must keep
 * building a CR_STR for a digit-shaped string, because args are heterogeneous
 * here — `combine="4"` is a mode name, not a number — and auto-converting at
 * ingest would silently retype it. Only an op that KNOWS it wants a number
 * calls this, exactly as the marshal's coefficient reader does.
 *
 * Returns `v` unchanged when it is not a decimal string; NULL only on a real
 * failure (bad digits / arena), so the caller declines rather than guesses. */
static cr_value_t *cr_widen_dec(cr_bump_t *b, cr_value_t *v)
{
    cr_value_t *out; uint32_t i, start; size_t limbs;
    assert(b != NULL);
    assert(b->cur <= b->end);
    if (v == NULL || v->kind != CR_STR || v->slen == 0u) { return v; }
    start = (v->s[0] == '-') ? 1u : 0u;
    if (v->slen == start) { return v; }              /* a bare "-" is not a number */
    for (i = start; i < v->slen; i++) {
        if (v->s[i] < '0' || v->s[i] > '9') { return v; }   /* a real string */
    }
    out = cr_new_value(b, CR_INT);
    if (out == NULL) { return NULL; }
    limbs = srmech_bigint_from_dec_bound((size_t)v->slen);
    out->num = cr_new_bigint(b, (uint32_t)limbs);
    if (out->num == NULL) { return NULL; }
    if (srmech_bigint_from_dec(out->num, v->s, (size_t)v->slen) != SRMECH_OK) {
        return NULL;
    }
    return out;
}

/* Read a CR_INT as a signed int64. Distinct from cr_as_u64, whose Class-I wire
 * is unsigned by contract — an orientation is signed by nature. */
static int cr_as_i64(const cr_value_t *v, int64_t *out)
{
    const srmech_bigint_t *bi; uint64_t mag;
    assert(v != NULL);
    assert(out != NULL);
    if (v->kind != CR_INT || v->num == NULL) { return 0; }
    bi = v->num;
    if (bi->sign == 0) { *out = 0; return 1; }
    if (bi->n > 2u) { return 0; }
    mag = (uint64_t)bi->limbs[0];
    if (bi->n == 2u) { mag |= ((uint64_t)bi->limbs[1]) << 32; }
    if (mag > (uint64_t)INT64_MAX) { return 0; }
    /* Class-K pin-slot reads the sign; Class-C re-applies it. Never the
     * ALU-magnitude idiom. */
    *out = (bi->sign < 0) ? -(int64_t)mag : (int64_t)mag;
    return 1;
}

/* A CR_INT carrier holding uint64 v, exact across the whole range. */
static cr_value_t *cr_int_u64(cr_bump_t *b, uint64_t v)
{
    cr_value_t *out;
    assert(b != NULL);
    assert(sizeof(v) == 8u);
    out = cr_new_value(b, CR_INT);
    if (out == NULL) { return NULL; }
    out->num = cr_new_bigint(b, 3u);
    if (out->num == NULL) { return NULL; }
    out->num->sign = (v == 0u) ? 0 : 1;
    out->num->limbs[0] = (uint32_t)(v & 0xFFFFFFFFu);
    out->num->limbs[1] = (uint32_t)(v >> 32);
    out->num->n = (v == 0u) ? 0u : ((v >> 32) != 0u ? 2u : 1u);
    return out;
}

enum { CR_CY_GCD = 0, CR_CY_ADD, CR_CY_MUL, CR_CY_POW, CR_CY_INV };

/* Scratch for the bigint Class-I arm: two accumulators + a divmod/gcd arena. */
typedef struct {
    srmech_bigint_t *t0, *t1, *acc;
    void *scr; size_t scr_len;
} cr_cyctx_t;

/* Carve the Class-I scratch sized for operands up to `lim` limbs. */
static int cr_cyctx_init(cr_bump_t *b, cr_cyctx_t *y, uint32_t lim)
{
    uint32_t cap = lim * 2u + 8u;
    assert(b != NULL && y != NULL);
    assert(lim > 0u);
    y->t0 = cr_new_bigint(b, cap); y->t1 = cr_new_bigint(b, cap);
    y->acc = cr_new_bigint(b, cap);
    y->scr_len = (size_t)cap * 8u + 4096u;
    y->scr = cr_carve(b, y->scr_len);
    return (y->t0 != NULL && y->t1 != NULL && y->acc != NULL && y->scr != NULL);
}

/* out = a mod n, Python-floor (0 <= out < n). srmech_bigint_divmod's own
 * convention, so no sign fixup is layered on top of it here. */
static srmech_status_t cr_bi_mod(cr_cyctx_t *y, srmech_bigint_t *out,
                                 const srmech_bigint_t *a,
                                 const srmech_bigint_t *n)
{
    assert(y != NULL && out != NULL);
    assert(a != NULL && n != NULL);
    return srmech_bigint_divmod(NULL, out, a, n, y->scr, y->scr_len);
}

/* acc = (a ** k) mod n by square-and-multiply, MSB first. The loop is bounded
 * by k's bit count (<= 32 * k->n), so it is a BOUNDED loop with no recursion —
 * a bigint_pow-then-mod would blow the arena for any real exponent. */
static srmech_status_t cr_bi_modpow(cr_cyctx_t *y, srmech_bigint_t *out,
                                    const srmech_bigint_t *a,
                                    const srmech_bigint_t *k,
                                    const srmech_bigint_t *n)
{
    uint32_t bit, top; srmech_status_t st;
    assert(y != NULL && out != NULL);
    assert(a != NULL && k != NULL && n != NULL);
    st = srmech_bigint_set_i64(out, 1);
    if (st != SRMECH_OK) { return st; }
    st = cr_bi_mod(y, y->acc, out, n);            /* 1 mod n handles n == 1 */
    if (st != SRMECH_OK) { return st; }
    if (k->sign == 0) { return srmech_bigint_copy(out, y->acc); }
    st = cr_bi_mod(y, y->t1, a, n);      /* the base as a RESIDUE, cyclic-native */
    if (st != SRMECH_OK) { return st; }
    top = k->n * 32u;
    for (bit = top; bit-- > 0u; ) {
        st = srmech_bigint_mul(y->t0, y->acc, y->acc);
        if (st != SRMECH_OK) { return st; }
        st = cr_bi_mod(y, y->acc, y->t0, n);
        if (st != SRMECH_OK) { return st; }
        if (((k->limbs[bit >> 5] >> (bit & 31u)) & 1u) != 0u) {
            st = srmech_bigint_mul(y->t0, y->acc, y->t1);
            if (st != SRMECH_OK) { return st; }
            st = cr_bi_mod(y, y->acc, y->t0, n);
            if (st != SRMECH_OK) { return st; }
        }
    }
    return srmech_bigint_copy(out, y->acc);
}

/* gcd(a,b) / mod_add(a,b,n) / mod_mul(a,b,n) / mod_pow(a,k,n) — ALL on the
 * FULL bigint carrier, no uint64 cap anywhere. ``mod_mul_wide`` and ``mod_mul``
 * are the same arm here: "wide" named the absence of a cap, and there is no cap
 * to be wide of once the arithmetic is bigint.
 *
 * CR_CY_INV is NOT handled here — see cr_op_cyclic_inv. There is no bigint
 * extended-Euclid export, and inventing one is new math rather than a dispatch
 * arm, so it keeps the uint64 wire and the decline contract. Filed, not silent:
 * notes/_1653_gap_ledger.ndjson row `bigint_modinv`. */
static srmech_status_t cr_op_cyclic(cr_ctx_t *c, const srmech_json_value_t *args,
                                    int which, cr_value_t **out)
{
    const srmech_bigint_t *A, *B, *N = NULL; cr_value_t *va, *vb, *vn, *ov;
    cr_cyctx_t y; uint32_t lim; srmech_status_t st;
    assert(c != NULL && out != NULL);
    assert(which >= CR_CY_GCD && which <= CR_CY_POW);
    /* cr_widen_dec applies the rc176 decimal-string bignum transport: an
     * operand wider than int64 cannot arrive as a JSON literal (the parser
     * declines it, ERR_LIMIT), so it rides as a decimal STRING exactly as
     * srmech_carrier_marshal.c's coefficient reader has taken it since rc176. */
    va = cr_widen_dec(c->b, cr_arg(c, args, "a"));
    vb = cr_widen_dec(c->b, cr_arg(c, args, (which == CR_CY_POW) ? "k" : "b"));
    if (va == NULL || vb == NULL) { return SRMECH_ERR_NOT_IMPL; }
    if (va->kind != CR_INT || vb->kind != CR_INT) { return SRMECH_ERR_NOT_IMPL; }
    A = va->num; B = vb->num;
    if (which != CR_CY_GCD) {
        vn = cr_widen_dec(c->b, cr_arg(c, args, "n"));
        if (vn == NULL || vn->kind != CR_INT) { return SRMECH_ERR_NOT_IMPL; }
        N = vn->num;
        if (N->sign <= 0) { return SRMECH_ERR_BAD_INPUT; }   /* n > 0 required */
    }
    lim = A->n + B->n + (N != NULL ? N->n : 0u) + 4u;
    if (!cr_cyctx_init(c->b, &y, lim)) { return SRMECH_ERR_OVERFLOW; }
    ov = cr_new_value(c->b, CR_INT);
    if (ov == NULL) { return SRMECH_ERR_OVERFLOW; }
    ov->num = cr_new_bigint(c->b, lim * 2u + 8u);
    if (ov->num == NULL) { return SRMECH_ERR_OVERFLOW; }
    if (which == CR_CY_GCD) {
        st = srmech_bigint_gcd(ov->num, A, B, y.scr, y.scr_len);
    } else if (which == CR_CY_POW) {
        st = cr_bi_modpow(&y, ov->num, A, B, N);
    } else {
        /* CYCLIC-NATIVE ORDER: reduce to RESIDUES first, then operate inside
         * Z/nZ. Computing a*b in full and reducing afterwards is the
         * PROJECTION-shaped order — it makes the intermediate grow with the
         * OPERANDS when the algebra says every element is bounded by n. Reduce
         * first and the intermediate is bounded by n^2 no matter how large the
         * operands were, which is both the framework-correct order and the one
         * that bounds the arena. */
        st = cr_bi_mod(&y, y.t1, A, N);
        if (st == SRMECH_OK) { st = cr_bi_mod(&y, y.acc, B, N); }
        if (st == SRMECH_OK) {
            st = (which == CR_CY_ADD) ? srmech_bigint_add(y.t0, y.t1, y.acc)
                                      : srmech_bigint_mul(y.t0, y.t1, y.acc);
        }
        if (st == SRMECH_OK) { st = cr_bi_mod(&y, ov->num, y.t0, N); }
    }
    if (st != SRMECH_OK) { return st; }
    *out = ov;
    return SRMECH_OK;
}

/* mod_inv(a, n) — the ONE Class-I op still on the uint64 wire, because no
 * bigint extended-Euclid ships. DECLINES an out-of-range operand rather than
 * narrowing it: a narrower projection must refuse, never answer wrongly. */
static srmech_status_t cr_op_cyclic_inv(cr_ctx_t *c, const srmech_json_value_t *args,
                                        cr_value_t **out)
{
    uint64_t a = 0u, n = 0u, r = 0u;
    cr_value_t *va, *vn, *ov; srmech_status_t st;
    assert(c != NULL && out != NULL);
    assert(args != NULL);
    va = cr_arg(c, args, "a"); vn = cr_arg(c, args, "n");
    if (va == NULL || vn == NULL) { return SRMECH_ERR_NOT_IMPL; }
    if (!cr_as_u64(va, &a) || !cr_as_u64(vn, &n)) { return SRMECH_ERR_NOT_IMPL; }
    st = srmech_mod_inv(a, n, &r);
    if (st != SRMECH_OK) { return st; }
    ov = cr_int_u64(c->b, r);
    if (ov == NULL) { return SRMECH_ERR_OVERFLOW; }
    *out = ov;
    return SRMECH_OK;
}

/* Dispatch one step by op name. Non-OK → the whole chain defers to pure. */
/* ------------------------------------------------------------------
 * The REAL-SEQUENCE arm (Class C / Class L over f64 vectors).
 *
 * Unblocked by CR_DBL: through rc446 a real literal could not even be INGESTED
 * (cr_json_scalar returned NULL for a JSON double), so these ops were
 * unreachable regardless of the op table.
 * ------------------------------------------------------------------ */

/* Materialise a CR_LIST as a flat double array carved from the run bump.
 * A CR_INT element is WIDENED to double (a JSON `1` and `1.0` are the same
 * mathematical operand and Python treats them alike here); any other element
 * kind declines. n == 0 yields a non-NULL zero-length buffer so the caller can
 * distinguish "empty" from "failed". */
static double *cr_as_dvec(cr_bump_t *b, const cr_value_t *v, size_t *n_out)
{
    double *buf; uint32_t i;
    assert(v != NULL && n_out != NULL);
    assert(b != NULL);
    if (v->kind != CR_LIST) { return NULL; }
    *n_out = (size_t)v->n;
    buf = (double *)cr_carve(b, (size_t)v->n * sizeof(double) + sizeof(double));
    if (buf == NULL) { return NULL; }
    for (i = 0u; i < v->n; i++) {
        const cr_value_t *e = v->items[i];
        int64_t iv;
        if (e == NULL) { return NULL; }
        if (e->kind == CR_DBL) { buf[i] = e->d; continue; }
        if (e->kind == CR_INT && cr_as_i64(e, &iv)) { buf[i] = (double)iv; continue; }
        return NULL;                      /* a non-real element — decline */
    }
    return buf;
}

/* Wrap a double array as a CR_LIST of CR_DBL. */
static cr_value_t *cr_dvec_value(cr_bump_t *b, const double *src, size_t n)
{
    cr_value_t *out; cr_value_t **items; size_t i;
    assert(b != NULL);
    assert(src != NULL || n == 0u);
    out = cr_new_value(b, CR_LIST);
    if (out == NULL) { return NULL; }
    out->n = (uint32_t)n;
    items = (cr_value_t **)cr_carve(b, n * sizeof(void *) + sizeof(void *));
    if (items == NULL) { return NULL; }
    for (i = 0u; i < n; i++) {
        items[i] = cr_dbl(b, src[i]);
        if (items[i] == NULL) { return NULL; }
    }
    out->items = items;
    return out;
}

/* A unary f64 sequence op: resolve `key` as a real vector, run `fn`, wrap the
 * result. `out` must not alias the input, so a second buffer is carved. */
static srmech_status_t cr_op_dseq(cr_ctx_t *c, const srmech_json_value_t *args,
                                  const char *key,
                                  srmech_status_t (*fn)(const double *, size_t,
                                                        double *),
                                  cr_value_t **out)
{
    cr_value_t *v; double *in, *res; size_t n = 0u; srmech_status_t st;
    assert(c != NULL && args != NULL && out != NULL);
    assert(key != NULL && fn != NULL);
    v = cr_arg(c, args, key);
    if (v == NULL) { return SRMECH_ERR_NOT_IMPL; }
    in = cr_as_dvec(c->b, v, &n);
    if (in == NULL) { return SRMECH_ERR_NOT_IMPL; }
    res = (double *)cr_carve(c->b, n * sizeof(double) + sizeof(double));
    if (res == NULL) { return SRMECH_ERR_OVERFLOW; }
    if (n > 0u) {
        st = fn(in, n, res);
        if (st != SRMECH_OK) { return st; }
    }
    *out = cr_dvec_value(c->b, res, n);
    return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* The real-sequence arms, split out ONLY to keep cr_dispatch under JPL Rule 4's
 * 60 lines. Unmatched returns NOT_IMPL, which is exactly what cr_dispatch's own
 * fall-through returns — so calling this last composes with no change in
 * semantics. */
/* Read one arg as a double. A CR_INT widens (a JSON `1` and `1.0` name the same
 * operand); anything else declines. */
static int cr_arg_dbl(cr_ctx_t *c, const srmech_json_value_t *args,
                      const char *key, double *out)
{
    cr_value_t *v; int64_t iv;
    assert(c != NULL && args != NULL);
    assert(key != NULL && out != NULL);
    v = cr_arg(c, args, key);
    if (v == NULL) { return 0; }
    if (v->kind == CR_DBL) { *out = v->d; return 1; }
    if (v->kind == CR_INT && cr_as_i64(v, &iv)) { *out = (double)iv; return 1; }
    return 0;
}

/* pin_slot_at_zero: Class K — split a real into (orientation, magnitude).
 * Returns a 2-element CR_LIST so `@step[N].output[0]` / `[1]` address the two
 * halves, which is exactly how the shipped descriptors read it.
 *
 * This IS the sign-handling primitive: the pin-slot phase boundary, never an
 * ALU-magnitude call. Class C re-applies the orientation downstream. */
static srmech_status_t cr_op_pin_slot(cr_ctx_t *c, const srmech_json_value_t *args,
                                      cr_value_t **out)
{
    double x = 0.0, mag = 0.0; int8_t ori = 0; srmech_status_t st;
    cr_value_t *lst; cr_value_t **items;
    assert(c != NULL && args != NULL);
    assert(out != NULL);
    if (!cr_arg_dbl(c, args, "x", &x)) { return SRMECH_ERR_NOT_IMPL; }
    st = srmech_cascade_pin_slot_at_zero_f64(x, &ori, &mag);
    if (st != SRMECH_OK) { return st; }
    lst = cr_new_value(c->b, CR_LIST);
    if (lst == NULL) { return SRMECH_ERR_OVERFLOW; }
    items = (cr_value_t **)cr_carve(c->b, 2u * sizeof(void *));
    if (items == NULL) { return SRMECH_ERR_OVERFLOW; }
    items[0] = cr_int_i64(c->b, (int64_t)ori);
    items[1] = cr_dbl(c->b, mag);
    if (items[0] == NULL || items[1] == NULL) { return SRMECH_ERR_OVERFLOW; }
    lst->items = items; lst->n = 2u;
    /* rc451: the Python peer returns Tuple[int, Real] (atoms.py), so the
     * carrier is flagged a tuple. A LATENT divergence until now, invisible only
     * because every ACCEPTED CATALOG variant uses pin_slot INTERMEDIATELY — a
     * chain ENDING here crossed the wire as a list against a Python tuple,
     * which the rc450 comparator pins DIVERGENT.
     *
     * ⚠️ WHAT IT COSTS. This comment said "Costs no shipped chain anything",
     * and that is MEASURABLY FALSE for the one case it named safe. A chain
     * ENDING at pin_slot changes its emitted kind l -> t, so its reconstructed
     * value moves [-1, 3.5] -> (-1, 3.5) — which IS the fix (Python answers the
     * tuple), not a side effect. tests/test_c_ref_indexing_rc447.py ships
     * exactly such a single-step chain and went red on it. INDEXING is what is
     * genuinely unaffected: @step[N].output[K] reads the flat CR_LIST as
     * before, because cr_index_value never asks about the flag. */
    lst->is_tuple = 1;
    *out = lst;
    return SRMECH_OK;
}

/* reorient: Class C — re-apply an orientation to a real value.
 *
 * ⚠️ TYPE-PRESERVING SINCE v0.9.0rc451 (`#T1164`). The Python op's docstring
 * states the contract outright — "int in -> int out, float in -> float out" —
 * and dispatches to srmech_cascade_reorient_i64 or _f64 accordingly. This arm
 * read EVERY operand through cr_arg_dbl and answered CR_DBL unconditionally,
 * so `reorient(22, orientation=+1)` returned 22.0 where Python returns 22.
 *
 * That is a WRONG ANSWER, not a capability gap, and the rc450 comparator pins
 * int != float as a required-DIVERGENT witness — but nothing had ever caught it
 * because no ACCEPTED chain reached reorient with an integer operand: every
 * shipped variant fed it a pin-slot magnitude, which is a double. rc451's
 * best_rational_signed is the first chain to feed it the INT numerator out of
 * best_rational, and the tuple wire is the first thing able to carry the result
 * to a comparator. Measured on the shipped descriptor's case 0 the moment the
 * chain first ran: C (22.0, 7) against Python (22, 7).
 *
 * Fixed at root rather than routed around. The int arm declines an out-of-int64
 * operand (Python's own native dispatch does too, falling back to its
 * arbitrary-precision path) so a bignum is deferred, never truncated. */
/* A FRESH CR_RATIONAL carrying `num`/`den` with the numerator's sign set to
 * `sgn`. The limb ARRAYS are ALIASED, never copied: every bigint reaching here
 * is write-once (built by cr_op_rat / cr_op_pow / cr_op_series and never
 * mutated afterwards), so aliasing is exact at any magnitude and costs two
 * struct carves instead of an unbounded copy.
 *
 * ⚠️ WHY THIS IS A SEPARATE CARRIER AND NOT `v->num->sign = -v->num->sign`.
 * Step outputs PERSIST in the chain arena so a later step can read
 * @step[N].output. Config C's rev2 negated in place on the real rebuilt
 * library and shipped a SILENT WRONG ANSWER: a three-step chain
 * (step0 = 1/2 + 1/3; step1 = reorient(step0, -1); step2 = step0 + 0/1)
 * returned -5/6 for step2 instead of 5/6, with rc=0 and a well-formed wire.
 * Nothing in the value channel can see that — step2's answer is a perfectly
 * plausible rational — so the discipline is structural, not a check:
 * NEVER mutate a value another step can still read.
 * Pinned by tests/test_exact_q_pipeline_rc452.py's 3-step regression. */
static cr_value_t *cr_rat_signed(cr_bump_t *b, const srmech_bigint_t *num,
                                 const srmech_bigint_t *den, int32_t sgn)
{
    cr_value_t *ov; srmech_bigint_t *n2, *d2;
    assert(b != NULL);
    assert(num != NULL && den != NULL);
    ov = cr_new_value(b, CR_RATIONAL);
    n2 = (srmech_bigint_t *)cr_carve(b, sizeof(srmech_bigint_t));
    d2 = (srmech_bigint_t *)cr_carve(b, sizeof(srmech_bigint_t));
    if (ov == NULL || n2 == NULL || d2 == NULL) { return NULL; }
    *n2 = *num; *d2 = *den;
    /* Class-K pin-slot: a ZERO numerator has sign 0 and MUST keep it — the
     * bigint invariant is `sign == 0 iff n == 0`, so stamping -1 on a zero
     * would build a malformed carrier that prints "-0". */
    n2->sign = (num->n == 0u) ? 0 : sgn;
    ov->num = n2; ov->den = d2;
    return ov;
}

static srmech_status_t cr_op_reorient(cr_ctx_t *c, const srmech_json_value_t *args,
                                      cr_value_t **out)
{
    cr_value_t *v; double value = 0.0, ori = 0.0, r = 0.0;
    const srmech_bigint_t *qn, *qd;
    int64_t iv = 0, ir = 0; srmech_status_t st;
    assert(c != NULL && args != NULL);
    assert(out != NULL);
    if (!cr_arg_dbl(c, args, "orientation", &ori)) { return SRMECH_ERR_NOT_IMPL; }
    if (ori < -128.0 || ori > 127.0) { return SRMECH_ERR_NOT_IMPL; }
    v = cr_arg(c, args, "value");
    if (v == NULL) { return SRMECH_ERR_NOT_IMPL; }
    /* rc452 (`#T1166`): the exact-Q arm. Class C re-application is
     * negate-iff-orientation < 0, identical to the i64 and f64 arms below; the
     * sign lives on the numerator because the carrier keeps den > 0.
     *
     * ⚠️ CR_RATIONAL ONLY — this arm deliberately does NOT call
     * cr_as_rational, whose second arm would also admit a bare 2-int CR_LIST.
     * Two reasons, both measured, and rc452's plan asked for the opposite:
     *
     *  1. IT WOULD MAKE C ANSWER WHERE PYTHON RAISES. `reorient((5, 6),
     *     orientation=-1)` raises TypeError in Python (unary minus on a tuple)
     *     and `orientation=+1` passes the tuple through un-negated. Admitting
     *     the list here would return an exact -5/6 from C against a raise from
     *     Python — a value-vs-capability divergence, which is the defect class
     *     this rc exists to close, one level up.
     *  2. IT WOULD RE-CREATE THE COLLISION THAT DISQUALIFIED ADJ-4. A 2-int
     *     list is ALSO how a Class-K pin pair and a Class-B `pair` step spell
     *     themselves. Config B measured that `pin_slot_at_zero(-1) = (-1, 1)`
     *     and the rational -1/1 are byte-identical on the wire, that the
     *     collision lands on THIS op, and that the repair is UNDECIDABLE — one
     *     input, two correct answers. The ruling used that to reject the tuple
     *     spelling; re-admitting it here would import the same ambiguity.
     *
     * So the pair stays a legal INPUT to the ops whose C peers take it
     * (cr_op_rat, cr_op_pow via cr_as_rational — re-verified by execution),
     * and reorient keeps DECLINING it on both projections. A mutual decline is
     * parity; an answer on one side only is not. */
    if (v->kind == CR_RATIONAL && v->num != NULL && v->den != NULL) {
        int32_t sgn = (ori < 0.0) ? -v->num->sign : v->num->sign;
        qn = v->num; qd = v->den;
        *out = cr_rat_signed(c->b, qn, qd, sgn);
        return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
    }
    if (v->kind == CR_INT) {
        if (!cr_as_i64(v, &iv)) { return SRMECH_ERR_NOT_IMPL; }
        st = srmech_cascade_reorient_i64((int8_t)ori, iv, &ir);
        if (st != SRMECH_OK) { return st; }
        *out = cr_int_i64(c->b, ir);
        return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
    }
    if (!cr_arg_dbl(c, args, "value", &value)) { return SRMECH_ERR_NOT_IMPL; }
    st = srmech_cascade_reorient_f64((int8_t)ori, value, &r);
    if (st != SRMECH_OK) { return st; }
    *out = cr_dbl(c->b, r);
    return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* ------------------------------------------------------------------
 * The best_rational_signed step ops (v0.9.0rc451, `#T1164`, gh #1653 item 4).
 *
 * ⚠️ THESE ARE FOUR SEPARATE ARMS AT STEP GRANULARITY, ON PURPOSE — and the
 * fused srmech_cascade_best_rational_signed_f64 is deliberately NOT called
 * from this translation unit. It would be the cheap way to make the chain
 * return rc=0, it is measured value-identical to the fine pipeline over the
 * entire C-accepted domain, and it would therefore satisfy every value-level
 * gate while the descriptor's declared steps drove NOTHING. A chain that runs
 * because one coarse symbol recognised its shape is not a chain the C host can
 * run. `srmech_cascade_scale_round_half_even_i64` is the honest opposite: an
 * OP-granular export the fused symbol and this arm both call, so the two
 * agree by construction.
 * ------------------------------------------------------------------ */

/* pair: Class B (framing) — assemble two carriers into a 2-TUPLE.
 *
 * The framing ops have no math, only a carrier shape, so this is an
 * INTERPRETER PRIMITIVE and not an export: a bare-C host that already holds
 * the two operands needs nothing from the library to put them side by side.
 * The sibling DSL interpreter settled the same question the same way (its
 * static dv_pair). What DOES cross the library boundary is the tuple's WIRE
 * spelling, which is why this rc bumps the ABI. */
static srmech_status_t cr_op_pair(cr_ctx_t *c, const srmech_json_value_t *args,
                                  cr_value_t **out)
{
    cr_value_t *first, *second, *lst; cr_value_t **items;
    assert(c != NULL && args != NULL);
    assert(out != NULL);
    first = cr_arg(c, args, "first");
    second = cr_arg(c, args, "second");
    if (first == NULL || second == NULL) { return SRMECH_ERR_NOT_IMPL; }
    lst = cr_new_value(c->b, CR_LIST);
    items = (cr_value_t **)cr_carve(c->b, 2u * sizeof(void *));
    if (lst == NULL || items == NULL) { return SRMECH_ERR_OVERFLOW; }
    items[0] = first; items[1] = second;
    lst->items = items; lst->n = 2u;
    lst->is_tuple = 1;      /* Python's pair() returns a tuple, so must this */
    *out = lst;
    return SRMECH_OK;
}

/* dead_band: Class K (pin-slot dead-band). Delegates to the rc451 export so
 * the fused chain symbol and this step share one implementation.
 *
 * ⚠️ DECLINES A NON-DOUBLE `value`, DELIBERATELY. The Python op is TYPE-
 * PRESERVING — dead_band(5, band) is the int 5 and dead_band(5e-13, band) is
 * the float 0.0 — and the shipped comparator pins int != float as a required
 * DIVERGENT. Reading the operand through cr_arg_dbl (which widens a CR_INT the
 * way `1` and `1.0` name the same operand elsewhere) would therefore answer
 * 5.0 where Python answers 5: a silent wrong answer, not a capability gap. So
 * the int arm is REFUSED rather than guessed, and the chain defers to the pure
 * projection, which is right. Filed as its own ledger row. */
static srmech_status_t cr_op_dead_band(cr_ctx_t *c, const srmech_json_value_t *args,
                                       cr_value_t **out)
{
    cr_value_t *v; double band = 0.0, r = 0.0; srmech_status_t st;
    assert(c != NULL && args != NULL);
    assert(out != NULL);
    v = cr_arg(c, args, "value");
    if (v == NULL || v->kind != CR_DBL) { return SRMECH_ERR_NOT_IMPL; }
    if (!cr_arg_dbl(c, args, "band", &band)) { return SRMECH_ERR_NOT_IMPL; }
    st = srmech_cascade_dead_band_f64(v->d, band, &r);
    if (st != SRMECH_OK) { return st; }
    *out = cr_dbl(c->b, r);
    return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* scale_round_half_even: Class K ∘ N ∘ C. Delegates to the rc451 export.
 *
 * `value` must be a CR_DBL for the same reason dead_band's must not be widened
 * from CR_INT: a bigint operand cannot round-trip through a double exactly
 * above 2^53, and answering approximately is worse than declining. */
static srmech_status_t cr_op_scale_round(cr_ctx_t *c, const srmech_json_value_t *args,
                                         cr_value_t **out)
{
    cr_value_t *v, *s; int64_t scale = 0, r = 0; srmech_status_t st;
    assert(c != NULL && args != NULL);
    assert(out != NULL);
    v = cr_arg(c, args, "value");
    s = cr_arg(c, args, "scale");
    if (v == NULL || v->kind != CR_DBL) { return SRMECH_ERR_NOT_IMPL; }
    if (s == NULL || !cr_as_i64(s, &scale)) { return SRMECH_ERR_NOT_IMPL; }
    st = srmech_cascade_scale_round_half_even_i64(v->d, scale, &r);
    if (st != SRMECH_OK) { return st; }
    *out = cr_int_i64(c->b, r);
    return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* best_rational: Class N — the small-denominator anchor. Delegates to the
 * step-granular srmech_best_rational, which already shipped.
 *
 * TWO STATED NARROWINGS, both DECLINES rather than guesses:
 *   - the C symbol's wire is uint64 while the CR_INT carrier and the Python op
 *     are both arbitrary-precision, so an out-of-uint64 or negative operand
 *     declines through cr_as_u64 — the SAME convention the Class-I cyclic arm
 *     documents. A narrower projection must REFUSE, never silently narrow.
 *   - `with_path=True` returns a THIRD element (the convergent CF) that this
 *     wire has no shape for, so its mere presence declines.
 * The result is a 2-TUPLE because Python's best_rational returns one; it rides
 * as a flagged CR_LIST so @step[N].output[K] still indexes it mid-chain. */
static srmech_status_t cr_op_best_rational(cr_ctx_t *c, const srmech_json_value_t *args,
                                           cr_value_t **out)
{
    cr_value_t *n, *d, *m, *lst; cr_value_t **items;
    uint64_t nu = 0u, du = 0u, mu = 0u, p = 0u, q = 0u; srmech_status_t st;
    assert(c != NULL && args != NULL);
    assert(out != NULL);
    if (srmech_json_object_get(args, "with_path") != NULL) {
        return SRMECH_ERR_NOT_IMPL;
    }
    n = cr_arg(c, args, "numerator");
    d = cr_arg(c, args, "denominator");
    m = cr_arg(c, args, "max_denominator");
    if (n == NULL || d == NULL || m == NULL) { return SRMECH_ERR_NOT_IMPL; }
    if (!cr_as_u64(n, &nu) || !cr_as_u64(d, &du) || !cr_as_u64(m, &mu)) {
        return SRMECH_ERR_NOT_IMPL;
    }
    st = srmech_best_rational(nu, du, mu, &p, &q);
    if (st != SRMECH_OK) { return st; }
    lst = cr_new_value(c->b, CR_LIST);
    items = (cr_value_t **)cr_carve(c->b, 2u * sizeof(void *));
    if (lst == NULL || items == NULL) { return SRMECH_ERR_OVERFLOW; }
    items[0] = cr_int_u64(c->b, p); items[1] = cr_int_u64(c->b, q);
    if (items[0] == NULL || items[1] == NULL) { return SRMECH_ERR_OVERFLOW; }
    lst->items = items; lst->n = 2u; lst->is_tuple = 1;
    *out = lst;
    return SRMECH_OK;
}

/* Does `op` name `want`? TRUE for the BARE name, or any DOTTED spelling whose
 * last segment is exactly `want` — `srmech.cascade.atoms.chiral_flip` and
 * `chiral_flip` both match, `poly_gcd` does NOT match `gcd`.
 *
 * ⚠️ THE SEGMENT BOUNDARY IS THE POINT, and a raw suffix compare does not have
 * it: `memcmp(op + (opl - 3), "gcd", 3)` matches `poly_gcd` and `bigint_gcd`
 * too, which would dispatch a DIFFERENT op's chain to this one. Requiring a
 * '.' immediately before the match makes the comparison respect the dotted
 * namespace it is reading.
 *
 * Applied UNIFORMLY as of rc447. Before that the table mixed two rules: the
 * Class-N arms used an exact bare `memcmp(op, ...)` while the rc447 arms used a
 * raw suffix, so `srmech.math.rational.sin_series_truncate` was NOT_IMPL while
 * `srmech.cascade.atoms.chiral_flip` ran. Measured, and it put the Python
 * eligibility predicate (which uses the last segment) out of agreement with the
 * runner on any dotted Class-N chain. One rule removes that class of
 * disagreement rather than encoding it on both sides. */
static int cr_op_is(const char *op, uint32_t opl, const char *want, uint32_t n)
{
    assert(op != NULL && want != NULL);
    assert(n > 0u);
    if (opl == n) { return memcmp(op, want, n) == 0; }
    if (opl > n + 1u && op[opl - n - 1u] == '.') {
        return memcmp(op + (opl - n), want, n) == 0;
    }
    return 0;
}

/* ------------------------------------------------------------------
 * THE ATOM TABLE (v0.9.0rc452, `#T1166`).
 *
 * ⚠️ THIS IS "cascade.atoms IN C" — gh #1653's mandate clause 2 — and it is
 * closed HERE rather than as a separate deliverable, because it is also the
 * mechanism clause 1 needs. Through rc451 the dispatch was an if-chain, and
 * `cr_dispatch` was MEASURED at 57 of JPL Rule 4's 60 lines with 16 arms; the
 * eight remaining blocked chains need 32 more op spellings between them. Those
 * arms could not be added AS AN IF-CHAIN AT ALL — not "would be untidy",
 * cannot: the 17th arm breaks Rule 4 and the split that produced
 * `cr_dispatch_real` had already been spent once to buy four.
 *
 * So `CR_OP_REG` stops being a name-to-name index and becomes a name-to-
 * FUNCTION-POINTER atom registry: a bare-C, config-addressable table that IS
 * the callable registry the interpreter resolves against. `cr_dispatch`
 * collapses from a 57-line if-chain to a ~12-line bounded loop over it, and
 * `cr_dispatch_real` — which existed only to absorb the overflow — is GONE.
 * Adding an op is now adding a ROW, which is why the table can carry 56.
 *
 * ⚠️ THE TABLE IS THE ONLY DISPATCH PATH. `cr_dispatch` contains zero
 * `cr_op_is` calls of its own; the one call site is inside the loop, against
 * the row's own `bare`/`len`. tests/test_t1158_registry_param_order_rc449.py
 * asserts exactly that, so a future arm added BESIDE the table (leaving the
 * table decorative — the shape a green could otherwise be bought with) is red.
 *
 * FOUR COLUMNS, and the fourth is the one that closes the fold body:
 *   bare/len  the segment-boundary match cr_op_is performs
 *   full      the ToolEntry name cr_args_keyset_ok validates `args` keys against
 *   fn        the op itself: pull operands from `args` BY NAME, write *out
 *   bin       non-NULL iff the op can also serve as a FOLD BODY
 *
 * ⚠️ WHY `bin` IS A COLUMN AND NOT A SECOND TABLE. A fold body receives two
 * POSITIONAL carriers (acc, elem) that are already evaluated — there is no
 * `args` JSON object to pull from, so `fn` genuinely cannot serve. Through
 * rc451 that difference was expressed as a PRIVATE single-entry table
 * (`cr_fold_body`, orientation_compose only), which is why a fold over any
 * other op declined and why CEIL_SURFACE_A_UNSUPPORTED_FORMS still counted
 * `fold` unsupported with a real fold chain shipping. Making it a column on
 * the SAME table keeps one registry — so the bijection gate still sees every
 * op exactly once — while stating honestly that the two entry shapes differ.
 * ------------------------------------------------------------------ */

/* The op shape: operands arrive BY NAME inside `args` (cr_arg pulls them). */
typedef srmech_status_t (*cr_op_fn_t)(cr_ctx_t *c, const srmech_json_value_t *args,
                                      cr_value_t **out);

/* The FOLD-BODY shape: two already-evaluated POSITIONAL carriers. */
typedef srmech_status_t (*cr_bin_fn_t)(cr_bump_t *b, const cr_value_t *acc,
                                       const cr_value_t *elem, cr_value_t **out);

/* ---- thin wrappers giving the parameterised drivers the uniform shape ---- */

static srmech_status_t cr_a_exp_series(cr_ctx_t *c, const srmech_json_value_t *a,
                                       cr_value_t **o)
{
    assert(c != NULL && a != NULL);
    assert(o != NULL);
    return cr_op_series(c, a, srmech_exp_series_truncate_big, o);
}

static srmech_status_t cr_a_sin_series(cr_ctx_t *c, const srmech_json_value_t *a,
                                       cr_value_t **o)
{
    assert(c != NULL && a != NULL);
    assert(o != NULL);
    return cr_op_series(c, a, srmech_sin_series_truncate_big, o);
}

static srmech_status_t cr_a_cos_series(cr_ctx_t *c, const srmech_json_value_t *a,
                                       cr_value_t **o)
{
    assert(c != NULL && a != NULL);
    assert(o != NULL);
    return cr_op_series(c, a, srmech_cos_series_truncate_big, o);
}

static srmech_status_t cr_a_log1p_series(cr_ctx_t *c, const srmech_json_value_t *a,
                                         cr_value_t **o)
{
    assert(c != NULL && a != NULL);
    assert(o != NULL);
    return cr_op_series(c, a, srmech_log1p_series_truncate_big, o);
}

static srmech_status_t cr_a_atan_series(cr_ctx_t *c, const srmech_json_value_t *a,
                                        cr_value_t **o)
{
    assert(c != NULL && a != NULL);
    assert(o != NULL);
    return cr_op_series(c, a, srmech_atan_series_truncate_big, o);
}

static srmech_status_t cr_a_rat_add(cr_ctx_t *c, const srmech_json_value_t *a,
                                    cr_value_t **o)
{
    assert(c != NULL && a != NULL);
    assert(o != NULL);
    return cr_op_rat(c, a, '+', o);
}

static srmech_status_t cr_a_rat_mul(cr_ctx_t *c, const srmech_json_value_t *a,
                                    cr_value_t **o)
{
    assert(c != NULL && a != NULL);
    assert(o != NULL);
    return cr_op_rat(c, a, '*', o);
}

static srmech_status_t cr_a_rat_div(cr_ctx_t *c, const srmech_json_value_t *a,
                                    cr_value_t **o)
{
    assert(c != NULL && a != NULL);
    assert(o != NULL);
    return cr_op_rat(c, a, '/', o);
}

static srmech_status_t cr_a_gcd(cr_ctx_t *c, const srmech_json_value_t *a,
                                cr_value_t **o)
{
    assert(c != NULL && a != NULL);
    assert(o != NULL);
    return cr_op_cyclic(c, a, CR_CY_GCD, o);
}

static srmech_status_t cr_a_mod_add(cr_ctx_t *c, const srmech_json_value_t *a,
                                    cr_value_t **o)
{
    assert(c != NULL && a != NULL);
    assert(o != NULL);
    return cr_op_cyclic(c, a, CR_CY_ADD, o);
}

static srmech_status_t cr_a_mod_mul(cr_ctx_t *c, const srmech_json_value_t *a,
                                    cr_value_t **o)
{
    assert(c != NULL && a != NULL);
    assert(o != NULL);
    return cr_op_cyclic(c, a, CR_CY_MUL, o);
}

static srmech_status_t cr_a_mod_pow(cr_ctx_t *c, const srmech_json_value_t *a,
                                    cr_value_t **o)
{
    assert(c != NULL && a != NULL);
    assert(o != NULL);
    return cr_op_cyclic(c, a, CR_CY_POW, o);
}

static srmech_status_t cr_a_chiral_flip(cr_ctx_t *c, const srmech_json_value_t *a,
                                        cr_value_t **o)
{
    assert(c != NULL && a != NULL);
    assert(o != NULL);
    return cr_op_dseq(c, a, "seq", srmech_cascade_chiral_flip_f64, o);
}

/* ⚠️ THE `autocorrelation` OP, NOT THE `autocorrelation` CHAIN. This arm backs
 * a step whose op IS srmech.cascade.autocorrelation — the shipped leaf. The
 * CHAIN of the same name is a different object: its steps are seq_len /
 * correlation_product / compensated_sum and NONE of them names this op, so
 * running that chain cannot reach this symbol and no coarse bypass exists
 * between them structurally. */
static srmech_status_t cr_a_autocorrelation(cr_ctx_t *c, const srmech_json_value_t *a,
                                            cr_value_t **o)
{
    assert(c != NULL && a != NULL);
    assert(o != NULL);
    return cr_op_dseq(c, a, "x", srmech_autocorrelation_f64, o);
}

/* ---- fold bodies: two positional carriers ---- */

/* orientation_compose(acc, elem) — Class K absorbing zero, else Class C
 * reorient. Lifted verbatim out of the rc446 private cr_fold_body. */
static srmech_status_t cr_b_orient_compose(cr_bump_t *b, const cr_value_t *acc,
                                           const cr_value_t *elem, cr_value_t **out)
{
    int64_t a, e, r; srmech_status_t st;
    assert(b != NULL && out != NULL);
    assert(acc != NULL && elem != NULL);
    if (!cr_as_i64(acc, &a) || !cr_as_i64(elem, &e)) { return SRMECH_ERR_NOT_IMPL; }
    if (e < -128 || e > 127) { return SRMECH_ERR_NOT_IMPL; }
    if (e == 0) {                        /* the ABSORBING zero — Class K     */
        *out = cr_int_i64(b, 0);
        return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
    }
    st = srmech_cascade_reorient_i64((int8_t)e, a, &r);   /* Class C         */
    if (st != SRMECH_OK) { return st; }
    *out = cr_int_i64(b, r);
    return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* ---- Class-B / L / M leaf atoms (rc452 wave A: the autocorrelation chain) ----
 *
 * ⚠️ THESE ARE THE CHAIN'S STEPS, NOT THE FUSED KERNEL. `srmech_autocorrelation_f64`
 * exists and computes the whole transform, and the `autocorrelation` OP row above
 * dispatches it. The autocorrelation CHAIN is a different object: its steps are
 * seq_len / mod_add / correlation_product / compensated_sum and NONE of them names
 * the fused symbol, so running the chain cannot reach it. Dispatching the kernel
 * for the chain would move the ceiling with one arm while the descriptor's steps
 * drove nothing — and no value-level gate could tell, since the two agree. */

/* Read one element of a CR_LIST as a double. A CR_INT widens (a JSON `1` and
 * `1.0` name the same operand); anything else declines. */
static int cr_elem_dbl(const cr_value_t *v, uint32_t i, double *out)
{
    const cr_value_t *e; int64_t iv;
    assert(v != NULL && out != NULL);
    assert(i < 0x7fffffffu);
    if (v->kind != CR_LIST || i >= v->n || v->items == NULL) { return 0; }
    e = v->items[i];
    if (e == NULL) { return 0; }
    if (e->kind == CR_DBL) { *out = e->d; return 1; }
    if (e->kind == CR_INT && cr_as_i64(e, &iv)) { *out = (double)iv; return 1; }
    return 0;
}

/* seq_len(seq) -> int. Class B: the L in TLV, the frame's element count. */
static srmech_status_t cr_a_seq_len(cr_ctx_t *c, const srmech_json_value_t *a,
                                    cr_value_t **o)
{
    cr_value_t *v;
    assert(c != NULL && a != NULL);
    assert(o != NULL);
    v = cr_arg(c, a, "seq");
    if (v == NULL || v->kind != CR_LIST) { return SRMECH_ERR_NOT_IMPL; }
    *o = cr_int_i64(c->b, (int64_t)v->n);
    return (*o == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* correlation_product(x, i, j) -> float(x[i]) * float(x[j]). Class L. */
static srmech_status_t cr_a_corr_product(cr_ctx_t *c, const srmech_json_value_t *a,
                                         cr_value_t **o)
{
    cr_value_t *x = cr_arg(c, a, "x");
    cr_value_t *vi = cr_arg(c, a, "i"), *vj = cr_arg(c, a, "j");
    int64_t i, j; double xi, xj;
    assert(c != NULL && a != NULL);
    assert(o != NULL);
    if (x == NULL || vi == NULL || vj == NULL) { return SRMECH_ERR_NOT_IMPL; }
    if (!cr_as_i64(vi, &i) || !cr_as_i64(vj, &j)) { return SRMECH_ERR_NOT_IMPL; }
    if (i < 0 || j < 0) { return SRMECH_ERR_NOT_IMPL; }
    if (!cr_elem_dbl(x, (uint32_t)i, &xi) ||
        !cr_elem_dbl(x, (uint32_t)j, &xj)) { return SRMECH_ERR_NOT_IMPL; }
    *o = cr_dbl(c->b, xi * xj);
    return (*o == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* compensated_sum(values) -> Kahan-Babuska-NEUMAIER compensated summation.
 *
 * Transcribed operation-for-operation from composites.py, because the Python
 * op's docstring pins its float-op ORDER as the contract ("shipped as one leaf
 * so the float-op order stays pinned to this exact body"). A mathematically
 * equivalent reassociation would be a different answer in the last bits, and
 * the shipped comparator is BYTE-typed.
 *
 * ⚠️ THE LARGER TERM IS SELECTED BY A SQUARE COMPARISON (`s*s >= v*v`), NOT BY
 * abs(). That is the Class-K honest form the Python body uses and the house
 * rule requires; writing `fabs` here would also pull in libm, which this
 * library does not link. */
static srmech_status_t cr_a_compensated_sum(cr_ctx_t *c, const srmech_json_value_t *a,
                                            cr_value_t **o)
{
    cr_value_t *vs; double s = 0.0, cc = 0.0, v, t; uint32_t i;
    assert(c != NULL && a != NULL);
    assert(o != NULL);
    vs = cr_arg(c, a, "values");
    if (vs == NULL || vs->kind != CR_LIST) { return SRMECH_ERR_NOT_IMPL; }
    for (i = 0u; i < vs->n; i++) {
        if (!cr_elem_dbl(vs, i, &v)) { return SRMECH_ERR_NOT_IMPL; }
        t = s + v;
        if (s * s >= v * v) { cc += (s - t) + v; }
        else                { cc += (v - t) + s; }
        s = t;
    }
    *o = cr_dbl(c->b, s + cc);
    return (*o == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* gcd(acc, elem) as a fold body — the op the ratchet's form probe folds. */
static srmech_status_t cr_b_gcd(cr_bump_t *b, const cr_value_t *acc,
                                const cr_value_t *elem, cr_value_t **out)
{
    uint64_t a, e, t;
    assert(b != NULL && out != NULL);
    assert(acc != NULL && elem != NULL);
    if (!cr_as_u64(acc, &a) || !cr_as_u64(elem, &e)) { return SRMECH_ERR_NOT_IMPL; }
    while (e != 0u) { t = a % e; a = e; e = t; }
    *out = cr_int_u64(b, a);
    return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* ------------------------------------------------------------------
 * THE TABLE. Order and membership are read by
 * tests/test_t1158_registry_param_order_rc449.py, which resolves every `full`
 * against the LIVE ToolEntry registry and asserts the declared `len` matches
 * the string — a wrong length silently disables the row, because cr_op_is
 * compares it BEFORE memcmp.
 *
 * ⚠️ A ROW'S `full` MUST NAME THE OP THE ROW ACTUALLY RUNS. Pointing it at a
 * registered SIBLING with the same param names (sha256_bytes for sha256_raw,
 * say) passes every shipped gate — the entry resolves, the lengths agree, the
 * params match — while validating `args` against the wrong contract. The three
 * ops that had no ToolEntry at all were REGISTERED in this rc rather than
 * aliased, for exactly that reason.
 *
 * .rodata beside map_k / fold_k / plain_k; JPL Rule 3 is untouched.
 * ------------------------------------------------------------------ */
static const struct {
    const char *bare;
    uint32_t    len;
    const char *full;
    cr_op_fn_t  fn;
    cr_bin_fn_t bin;
} CR_OP_REG[28] = {
 /* wave A (rc452) — the autocorrelation CHAIN's own steps */
 { "seq_len",             7u, "srmech.cascade.seq_len",
   cr_a_seq_len, NULL },
 { "correlation_product", 19u, "srmech.cascade.correlation_product",
   cr_a_corr_product, NULL },
 { "compensated_sum",    15u, "srmech.cascade.compensated_sum",
   cr_a_compensated_sum, NULL },
 { "pi_cascade_digits",  17u, "srmech.math.rational.pi_cascade_digits",
   cr_op_pi, NULL },
 { "exp_series_truncate", 19u, "srmech.math.rational.exp_series_truncate",
   cr_a_exp_series, NULL },
 { "sin_series_truncate", 19u, "srmech.math.rational.sin_series_truncate",
   cr_a_sin_series, NULL },
 { "cos_series_truncate", 19u, "srmech.math.rational.cos_series_truncate",
   cr_a_cos_series, NULL },
 { "log1p_series_truncate", 21u, "srmech.math.rational.log1p_series_truncate",
   cr_a_log1p_series, NULL },
 { "atan_series_truncate", 20u, "srmech.math.rational.atan_series_truncate",
   cr_a_atan_series, NULL },
 { "rational_pow_uint",  17u, "srmech.math.rational.rational_pow_uint",
   cr_op_pow, NULL },
 { "rational_add",       12u, "srmech.math.rational.rational_add",
   cr_a_rat_add, NULL },
 { "rational_mul",       12u, "srmech.math.rational.rational_mul",
   cr_a_rat_mul, NULL },
 { "rational_div",       12u, "srmech.math.rational.rational_div",
   cr_a_rat_div, NULL },
 { "gcd",                 3u, "srmech.math.cyclic.gcd",
   cr_a_gcd, cr_b_gcd },
 { "mod_add",             7u, "srmech.math.cyclic.mod_add",
   cr_a_mod_add, NULL },
 { "mod_mul",             7u, "srmech.math.cyclic.mod_mul",
   cr_a_mod_mul, NULL },
 { "mod_mul_wide",       12u, "srmech.math.cyclic.mod_mul_wide",
   cr_a_mod_mul, NULL },
 { "mod_pow",             7u, "srmech.math.cyclic.mod_pow",
   cr_a_mod_pow, NULL },
 { "mod_inv",             7u, "srmech.math.cyclic.mod_inv",
   cr_op_cyclic_inv, NULL },
 { "pin_slot_at_zero",   16u, "srmech.cascade.pin_slot_at_zero",
   cr_op_pin_slot, NULL },
 { "reorient",            8u, "srmech.cascade.reorient",
   cr_op_reorient, NULL },
 { "chiral_flip",        11u, "srmech.cascade.chiral_flip",
   cr_a_chiral_flip, NULL },
 { "autocorrelation",    15u, "srmech.cascade.autocorrelation",
   cr_a_autocorrelation, NULL },
 { "dead_band",           9u, "srmech.cascade.dead_band",
   cr_op_dead_band, NULL },
 { "scale_round_half_even", 21u, "srmech.math.rational.scale_round_half_even",
   cr_op_scale_round, NULL },
 { "best_rational",      13u, "srmech.math.rational.best_rational",
   cr_op_best_rational, NULL },
 { "pair",                4u, "srmech.cascade.pair",
   cr_op_pair, NULL },
 /* FOLD-BODY-ONLY: `fn` is NULL because orientation_compose is never a plain
  * step in any shipped descriptor — it exists to be folded. A NULL `fn` row is
  * a deliberate, expressible state (cr_dispatch returns NOT_IMPL for it), not
  * an omission; the alternative was a second table, which is what rc451 had. */
 { "orientation_compose", 19u, "srmech.cascade.orientation_compose",
   NULL, cr_b_orient_compose }
};

/* The table's own length, DERIVED. It was written out as a bare literal in the
 * loop bounds through rc450, and nothing read those: the shipped gate pins the
 * ARRAY DECLARATION via the marker string "} CR_OP_REG[N] = {" and then compares
 * index rows to dispatch arms, never a bound. So growing the array while leaving
 * a stale bound would have left the key-set validator silently OFF for exactly
 * the tail entries — with every other gate green. Deriving it removes the class. */
#define CR_OP_REG_N (sizeof(CR_OP_REG) / sizeof(CR_OP_REG[0]))

/* Find a row by op spelling. -1 when the op is not ours (→ the defer channel).
 * ONE matcher for dispatch, for the fold body and for the key-set validator, so
 * none of the three can disagree with the others about which op a dotted
 * spelling names. */
static int32_t cr_op_row(const char *op, uint32_t opl)
{
    uint32_t i;
    assert(op != NULL);
    assert(opl > 0u);
    for (i = 0u; i < (uint32_t)CR_OP_REG_N; i++) {
        if (cr_op_is(op, opl, CR_OP_REG[i].bare, CR_OP_REG[i].len)) {
            return (int32_t)i;
        }
    }
    return -1;
}

/* Dispatch one plain step's op. A bounded loop over the table — no if-chain,
 * and (deliberately) no cr_op_is call of its own. An op with no row, or a row
 * that is fold-body-ONLY (fn == NULL), returns NOT_IMPL and the whole chain
 * defers to the complete pure path. */
static srmech_status_t cr_dispatch(cr_ctx_t *c, const char *op, uint32_t opl,
                                   const srmech_json_value_t *args, cr_value_t **out)
{
    int32_t r;
    assert(c != NULL && op != NULL && out != NULL);
    assert(args != NULL);
    r = cr_op_row(op, opl);
    if (r < 0) { return SRMECH_ERR_NOT_IMPL; }
    if (CR_OP_REG[r].fn == NULL) { return SRMECH_ERR_NOT_IMPL; }
    return CR_OP_REG[r].fn(c, args, out);
}

/* ------------------------------------------------------------------
 * Marshal the final value back as a canonical-JSON VALUE DESCRIPTOR the
 * Python caller reconstructs. Bignums ride as decimal strings.
 * ------------------------------------------------------------------ */

/* A plain JSON STRING node holding a bigint's decimal expansion. */
static srmech_json_value_t *cr_dec_node(srmech_json_builder_t *bd,
                                        const srmech_bigint_t *bi, cr_bump_t *tmp)
{
    char *dec; size_t dl;
    size_t cap = (size_t)bi->n * 10u + 4u;
    void *scr; size_t sl = (size_t)bi->n * 4u + 64u;
    assert(bd != NULL && bi != NULL);
    assert(bi->cap >= bi->n);
    dec = (char *)cr_carve(tmp, cap); scr = cr_carve(tmp, sl);
    if (dec == NULL || scr == NULL) { return NULL; }
    if (srmech_bigint_to_dec(bi, dec, cap, &dl, scr, sl) != SRMECH_OK) { return NULL; }
    return srmech_json_new_string(bd, dec, (uint32_t)dl);
}

/* Marshal a SCALAR carrier to its value descriptor. Split from cr_desc so the
 * list arm can loop over elements WITHOUT re-entering cr_desc — that would be
 * mutual recursion, which JPL Rule 1 bans. Safe because cr_json_list builds
 * lists from cr_json_scalar only, so a list is flat by construction and a
 * nested element cannot arise. Returns NULL for CR_LIST. */
static srmech_json_value_t *cr_desc_scalar(srmech_json_builder_t *bd,
                                           const cr_value_t *v, cr_bump_t *tmp)
{
    const char *keys[3]; srmech_json_value_t *vals[3];
    assert(bd != NULL);
    assert(tmp != NULL);
    if (v == NULL || v->kind == CR_NONE) {
        keys[0] = "k"; vals[0] = srmech_json_new_string(bd, "n", 1u);
        return srmech_json_new_object(bd, keys, vals, 1u);
    }
    if (v->kind == CR_INT) {
        keys[0] = "k"; keys[1] = "v";
        vals[0] = srmech_json_new_string(bd, "i", 1u);
        vals[1] = cr_dec_node(bd, v->num, tmp);
        if (vals[1] == NULL) { return NULL; }
        return srmech_json_new_object(bd, keys, vals, 2u);
    }
    if (v->kind == CR_STR) {
        keys[0] = "k"; keys[1] = "v";
        vals[0] = srmech_json_new_string(bd, "s", 1u);
        vals[1] = srmech_json_new_string(bd, v->s, v->slen);
        return srmech_json_new_object(bd, keys, vals, 2u);
    }
    if (v->kind == CR_RATIONAL) {
        srmech_json_value_t *n = cr_dec_node(bd, v->num, tmp);
        srmech_json_value_t *d = cr_dec_node(bd, v->den, tmp);
        if (n == NULL || d == NULL) { return NULL; }
        keys[0] = "d"; keys[1] = "k"; keys[2] = "n";
        vals[0] = d; vals[1] = srmech_json_new_string(bd, "q", 1u); vals[2] = n;
        return srmech_json_new_object(bd, keys, vals, 3u);
    }
    if (v->kind == CR_DBL) {
        keys[0] = "k"; keys[1] = "v";
        vals[0] = srmech_json_new_string(bd, "f", 1u);
        vals[1] = srmech_json_new_double(bd, v->d);
        if (vals[1] == NULL) { return NULL; }
        return srmech_json_new_object(bd, keys, vals, 2u);
    }
    return NULL;   /* CR_LIST — handled by cr_desc, never here */
}

/* Marshal a flat CR_LIST as {"k": "l", "v": [...]} — or {"k": "t", "v": [...]}
 * when the carrier is flagged a TUPLE (keys canonical-sorted). One level, a
 * plain loop, NO recursion.
 *
 * ⚠️ Python's _reconstruct_value has ALWAYS had a `k == "l"` branch, so the
 * scripting projection could read a list descriptor the compiled one could not
 * produce. That asymmetry ran the OTHER way from the one gh #1653 is about —
 * the reader was ahead of the writer — and it went unnoticed because nothing
 * exercised it. Closing it needs no Python change, which is exactly why it was
 * invisible.
 *
 * ⚠️ THE PAYLOAD KEY IS "v", CHANGED FROM "items" AT v0.9.0rc451. That closes
 * gap-ledger row wire_l_payload_key_divergence, which assigned the decision to
 * "the rc that next changes a wire" — this one. Through rc450 the two chain
 * wires spelled the SAME kind differently: chain-run's `l` carried its payload
 * under "items" while the sibling DSL wire's `l`/`t` carried theirs under "v".
 * Adding `t` FORCED the decision rather than merely permitting it: spelling t
 * with "items" would have grown the divergence from one kind to two, and
 * spelling t with "v" while l kept "items" would have made ONE wire internally
 * inconsistent. Unifying on "v" rides the ABI 19 -> 20 bump this rc already
 * pays for; deferring it would have cost its own bump later. Exactly ONE
 * in-tree reader of the old key exists (compose.py::_reconstruct_value) and it
 * moves in this same change.
 *
 * ⚠️ THE KIND IS EMITTED THROUGH TWO BARE-LITERAL BRANCHES, NEVER A TERNARY.
 * The rc450 value-parity gate re-derives the writer's kind set by parsing this
 * region for JSON-string constructions whose first argument is a ONE-CHARACTER
 * LITERAL. The sibling DSL interpreter writes its equivalent as a ternary
 * selecting between two kind letters in the argument position; copying that
 * idiom here would make the parse lose BOTH kinds and red the bijection pin —
 * and the tempting repair is to loosen the predicate, which is how a
 * measurement stops being one. Same class as the require_native
 * single-line-literal rule. If the predicate ever must change, change it
 * deliberately and in the same commit.
 *
 * (Measured while writing this: an earlier draft of THIS COMMENT spelled the
 * predicate out as a sample call with a placeholder letter, and the gate parsed
 * the placeholder as an eighth emitted kind and went red. The gate returning
 * otherwise on a comment is the gate being a measurement — so the comment
 * moved, not the predicate.) */
/* Close ONE completed list frame into its {"k": l|t, "v": [...]} object. Split
 * out so the walker below stays well inside JPL Rule 4. */
static srmech_json_value_t *cr_desc_close(srmech_json_builder_t *bd,
                                          const cr_value_t *v,
                                          srmech_json_value_t **items)
{
    const char *keys[2]; srmech_json_value_t *vals[2];
    assert(bd != NULL && v != NULL);
    assert(items != NULL || v->n == 0u);
    keys[0] = "k"; keys[1] = "v";
    if (v->is_tuple) {
        vals[0] = srmech_json_new_string(bd, "t", 1u);
    } else {
        vals[0] = srmech_json_new_string(bd, "l", 1u);
    }
    vals[1] = srmech_json_new_array(bd, items, v->n);
    if (vals[0] == NULL || vals[1] == NULL) { return NULL; }
    return srmech_json_new_object(bd, keys, vals, 2u);
}

typedef struct {
    const cr_value_t *v;             /* the CR_LIST being marshalled */
    srmech_json_value_t **items;     /* its built children */
    uint32_t i;                      /* next child slot */
} cr_mframe_t;

/* Marshal a (possibly NESTED) CR_LIST. POST-ORDER over an explicit frame stack:
 * a JSON array node cannot be built until all its children exist, so a frame
 * closes only when its last child has.
 *
 * ⚠️ THIS IS THE WRITER HALF OF `chain_run_list_is_flat_only`, AND IT WAS THE
 * HALF WITH TEETH. The rc451 version looped `cr_desc_scalar` over the elements
 * and returned NULL for a CR_LIST element — its comment reasoned that a list
 * "is flat by construction and a nested element cannot arise", which was TRUE
 * only because the INGEST could not build one. The two halves propped each
 * other up: widening either alone yields a chain that runs and cannot report.
 * Both move in this commit for that reason. */
static srmech_json_value_t *cr_desc_list(srmech_json_builder_t *bd,
                                         const cr_value_t *v, cr_bump_t *tmp)
{
    cr_mframe_t st[CR_MAX_DEPTH]; uint32_t sp;
    assert(bd != NULL && v != NULL);
    assert(v->kind == CR_LIST);
    st[0].v = v; st[0].i = 0u;
    st[0].items = (srmech_json_value_t **)cr_carve(
        tmp, (size_t)v->n * sizeof(void *) + sizeof(void *));
    if (st[0].items == NULL) { return NULL; }
    sp = 1u;
    while (sp > 0u) {
        cr_mframe_t *f = &st[sp - 1u];
        if (f->i < f->v->n) {
            const cr_value_t *ch = f->v->items[f->i];
            if (ch != NULL && ch->kind == CR_LIST) {
                if (sp >= CR_MAX_DEPTH) { return NULL; }
                st[sp].v = ch; st[sp].i = 0u;
                st[sp].items = (srmech_json_value_t **)cr_carve(
                    tmp, (size_t)ch->n * sizeof(void *) + sizeof(void *));
                if (st[sp].items == NULL) { return NULL; }
                sp++;                    /* parent's i advances on POP */
                continue;
            }
            f->items[f->i] = cr_desc_scalar(bd, ch, tmp);
            if (f->items[f->i] == NULL) { return NULL; }
            f->i++;
            continue;
        }
        {   /* frame complete → close it into the parent, or return it */
            srmech_json_value_t *node = cr_desc_close(bd, f->v, f->items);
            if (node == NULL) { return NULL; }
            sp--;
            if (sp == 0u) { return node; }
            st[sp - 1u].items[st[sp - 1u].i] = node;
            st[sp - 1u].i++;
        }
    }
    return NULL;                          /* unreachable: sp starts at 1 */
}

/* Marshal any carrier to its value descriptor. */
static srmech_json_value_t *cr_desc(srmech_json_builder_t *bd,
                                    const cr_value_t *v, cr_bump_t *tmp)
{
    assert(bd != NULL);
    assert(tmp != NULL);
    if (v != NULL && v->kind == CR_LIST) { return cr_desc_list(bd, v, tmp); }
    return cr_desc_scalar(bd, v, tmp);
}

/* ------------------------------------------------------------------
 * srmech_chain_run — the entry point.
 * ------------------------------------------------------------------ */

size_t srmech_chain_run_arena_bytes(size_t chain_len, size_t ctx_len)
{
    size_t parse = 128u * chain_len + 128u * ctx_len + 65536u;
    /* Per-step op scratch (the pi isqrt / bigexp factorial arenas dominate) +
     * the persisting step-output carriers; a generous static envelope (an op
     * that outgrows it → OVERFLOW → the pure path). */
    size_t run = 4096u * chain_len + (1u << 20);
    size_t writer = 32768u + 16u * (chain_len + ctx_len);
    assert(sizeof(srmech_bigint_t) <= 64u);
    assert(sizeof(cr_value_t) <= 128u);
    return parse + run + writer;
}

/* ------------------------------------------------------------------
 * THE SURFACE-A FOLD STEP FORM.
 *
 * `cr_run_steps` required every step to carry `op`, so a FOLD step (which
 * carries `fold_op`) was rejected BAD_INPUT before dispatch was ever reached.
 * That is a STEP-FORM gate, not an op-table gate: the grammar's own shape was
 * unrecognised, so no amount of op work could reach it.
 *
 * Ported from notes/_1653_proto_fold.c (12/12 checks, JPL-clean) with its
 * three named pieces kept intact: the form classifier, the bounded body table,
 * and the fold arm itself. NO body step list => NO re-entry into the step
 * loop => no recursion, so JPL Rule 1 holds without a frame stack (the MAP
 * form needs one, which is why it is filed separately rather than done here).
 * ------------------------------------------------------------------ */

typedef enum {
    CR_FORM_NONE = 0, CR_FORM_PLAIN, CR_FORM_FOLD, CR_FORM_MAP, CR_FORM_MIXED
} cr_form_t;

/* 1 iff `step` carries ANY of the `n` keys in `keys`. */
static int cr_has_any(const srmech_json_value_t *step, const char *const *keys,
                      uint32_t n)
{
    uint32_t i;
    assert(step != NULL && keys != NULL);
    assert(n > 0u && n <= 8u);
    for (i = 0u; i < n; i++) {
        if (srmech_json_object_get(step, keys[i]) != NULL) { return 1; }
    }
    return 0;
}

/* Classify one step. MIXED is a HARD reject — compose.py's mutual-exclusion
 * rule — and is kept DISTINCT from NONE so a step carrying two discriminators
 * can never be silently read as whichever one is tested first. The key lists
 * mirror compose.py's _MAP_KEYS / _FOLD_KEYS plus the plain triple; a widening
 * on either side must move both. */
static cr_form_t cr_step_form(const srmech_json_value_t *step)
{
    static const char *const map_k[4] = {"map_over", "index", "bind", "body"};
    static const char *const fold_k[5] = {"fold_class", "fold_op", "fold_init",
                                          "over", "fold_args"};
    static const char *const plain_k[3] = {"class", "op", "args"};
    int m, f, p;
    assert(step != NULL);
    assert(step->type == SRMECH_JSON_OBJECT);
    m = cr_has_any(step, map_k, 4u);
    f = cr_has_any(step, fold_k, 5u);
    p = cr_has_any(step, plain_k, 3u);
    if ((m + f + p) > 1) { return CR_FORM_MIXED; }
    if (m) { return CR_FORM_MAP; }
    if (f) { return CR_FORM_FOLD; }
    if (p) { return CR_FORM_PLAIN; }
    return CR_FORM_NONE;
}


/* One binary fold step, dispatched through the SHARED atom table's `bin`
 * column. An op with no row, or a row with no `bin` (an op that exists but
 * cannot serve as a fold body), returns NOT_IMPL and the WHOLE chain defers to
 * pure — the inform-don't-limit contract, never a wrong answer.
 *
 * ⚠️ THIS REPLACES A PRIVATE SINGLE-ENTRY TABLE. Through rc451 the body was
 * matched by a bespoke `cr_body_is_orient_compose` predicate that knew exactly
 * one op, which is why CEIL_SURFACE_A_UNSUPPORTED_FORMS kept counting `fold`
 * unsupported while a real fold chain shipped: the FORM ran, the BODY table
 * had one row. Sharing the op table is what makes the ratchet's `gcd` probe —
 * chosen precisely because it is in the shared table and was NOT in the
 * private one — able to return otherwise. */
static srmech_status_t cr_fold_body(cr_bump_t *b, const char *op, uint32_t opl,
                                    const cr_value_t *acc,
                                    const cr_value_t *elem, cr_value_t **out)
{
    int32_t r;
    assert(b != NULL && op != NULL && out != NULL);
    assert(acc != NULL && elem != NULL);
    r = cr_op_row(op, opl);
    if (r < 0 || CR_OP_REG[r].bin == NULL) { return SRMECH_ERR_NOT_IMPL; }
    return CR_OP_REG[r].bin(b, acc, elem, out);
}

/* acc = fold_init; for elem in resolve(over): acc = fold_op(acc, elem).
 * compose.py's iteration contract for the fold_args-absent (positional) case.
 * An empty sequence returns the seed unchanged — which is why the `[]` proof
 * case is the one that proves the seed is read at all. */
static srmech_status_t cr_run_fold(cr_ctx_t *c, const srmech_json_value_t *step,
                                   cr_value_t **out)
{
    const srmech_json_value_t *fo = srmech_json_object_get(step, "fold_op");
    const srmech_json_value_t *fi = srmech_json_object_get(step, "fold_init");
    const srmech_json_value_t *ov = srmech_json_object_get(step, "over");
    cr_value_t *acc, *seq; uint32_t i; srmech_status_t st;
    assert(c != NULL && step != NULL && out != NULL);
    assert(c->b != NULL);
    /* `fold_args` selects the KEYWORD-named fold, a different iteration
     * contract this arm does not implement. Decline rather than mis-run it. */
    if (srmech_json_object_get(step, "fold_args") != NULL) { return SRMECH_ERR_NOT_IMPL; }
    if (fo == NULL || fo->type != SRMECH_JSON_STRING) { return SRMECH_ERR_BAD_INPUT; }
    if (ov == NULL) { return SRMECH_ERR_BAD_INPUT; }
    if (fi == NULL || fi->type != SRMECH_JSON_INT) { return SRMECH_ERR_NOT_IMPL; }
    acc = cr_int_i64(c->b, fi->u.i);
    if (acc == NULL) { return SRMECH_ERR_OVERFLOW; }
    seq = cr_resolve_arg(c, ov);
    if (seq == NULL || seq->kind != CR_LIST) { return SRMECH_ERR_NOT_IMPL; }
    for (i = 0u; i < seq->n; i++) {
        cr_value_t *nxt = NULL;
        if (seq->items[i] == NULL) { return SRMECH_ERR_BAD_INPUT; }
        st = cr_fold_body(c->b, fo->u.str.ptr, fo->u.str.len,
                          acc, seq->items[i], &nxt);
        if (st != SRMECH_OK) { return st; }
        acc = nxt;
    }
    *out = acc;
    return SRMECH_OK;
}

/* ------------------------------------------------------------------
 * `args` KEY-SET REFUSAL (v0.9.0rc449, `#T1158` — the gh #1653 residual)
 *
 * The Surface-A twin of the stage-kwarg refusal in srmech_dsl_chain_run.c. Every
 * cr_op_* above reads its arguments by PULL (cr_arg(c, args, "a")), so an `args`
 * key naming nothing was silently ignored and the step computed anyway. MEASURED
 * bare-C at rc448: gcd{a:12, b:18, bogus:99} returned OK and 6, and gcd{a, b, n:5}
 * returned OK and 6 — `n` being a real key of the tree's vocabulary that is legal
 * on mod_add and meaningless on gcd.
 *
 * ⚠️ THE LEGAL SET IS params[*] HERE, NOT params[1..]. On the DSL surface the data
 * rides IMPLICITLY as the threaded chain value, so params[0] is not a legal stage
 * kwarg. Here every operand arrives BY NAME inside `args`, so every declared param
 * is legal — a params[1..] rule would refuse gcd{a, b}. The asymmetry is deliberate
 * and both directions are pinned in c/test/test_srmech_chain_run.c, so that nobody
 * "unifies" the two rules later.
 * ------------------------------------------------------------------ */

/* 1 iff `name` is a declared param of `e`. Every declared param is a legal `args`
 * key on this surface — see the params[*] note above. */
static int cr_key_is_legal(const char *name, const srmech_tool_entry_t *e)
{
    uint32_t j;
    assert(name != NULL && e != NULL);
    assert(e->param_count > 0u);
    for (j = 0u; j < e->param_count; j++) {
        if (strcmp(name, e->params[j].name) == 0) { return 1; }
    }
    return 0;
}

/* SRMECH_OK when every `args` key is legal for `op`, or when `op` is not an op this
 * runner dispatches (the defer channel, untouched). BAD_INPUT on an unknown key.
 * Matched with cr_op_is — the SAME predicate the dispatch uses, so the validator
 * and the dispatch cannot disagree about which op a dotted spelling names. */
static srmech_status_t cr_args_keyset_ok(const char *op, uint32_t opl,
                                         const srmech_json_value_t *args)
{
    const srmech_tool_entry_t *e = NULL;
    uint32_t i; int32_t r;
    assert(op != NULL && args != NULL);
    assert(args->type == SRMECH_JSON_OBJECT);
    r = cr_op_row(op, opl);                  /* the SAME matcher dispatch uses */
    if (r < 0) { return SRMECH_OK; }         /* not in the table → dispatch defers */
    e = srmech_tool_registry_find(CR_OP_REG[r].full);
    /* ⚠️ NOT silent acceptance — a dispatched op with no registry entry is a broken
     * library invariant. Accepting here would let ONE typo in the table above
     * disable the validator for that op forever, with every other op still green. */
    if (e == NULL) { return SRMECH_ERR_INTERNAL; }
    for (i = 0u; i < args->u.obj.n; i++) {
        if (!cr_key_is_legal(args->u.obj.keys[i], e)) {
            return SRMECH_ERR_BAD_INPUT;
        }
    }
    return SRMECH_OK;
}

/* One PLAIN step: validate the `op` / `args` shape, then dispatch. Split out
 * of cr_run_steps so the loop can branch on step form and both stay < 60
 * lines (JPL Rule 4).
 *
 * ⚠️ The key-set check lives HERE and not in cr_dispatch: that function is a
 * 16-arm if-chain measured at 57 of JPL Rule 4's 60 lines, and it exists in its
 * current split only because it hit the cap once already (see cr_dispatch_real).
 * A per-op check inline there breaks the rule immediately. */
static srmech_status_t cr_run_plain(cr_ctx_t *c, const srmech_json_value_t *step,
                                    cr_value_t **out)
{
    const srmech_json_value_t *args = srmech_json_object_get(step, "args");
    const srmech_json_value_t *o = srmech_json_object_get(step, "op");
    srmech_status_t kst;
    assert(c != NULL && step != NULL && out != NULL);
    assert(step->type == SRMECH_JSON_OBJECT);
    if (o == NULL || o->type != SRMECH_JSON_STRING) { return SRMECH_ERR_BAD_INPUT; }
    if (args == NULL || args->type != SRMECH_JSON_OBJECT) { return SRMECH_ERR_BAD_INPUT; }
    kst = cr_args_keyset_ok(o->u.str.ptr, o->u.str.len, args);
    if (kst != SRMECH_OK) { return kst; }
    return cr_dispatch(c, o->u.str.ptr, o->u.str.len, args, out);
}

/* Bind one map frame's `bind` object into `f`, resolving each ref in the
 * ENCLOSING scope. compose.py resolves binds ONCE, before the loop, against the
 * environment in force at the map step — not per iteration — so a bind cannot
 * see the index it is about to introduce. Resolving here (while the parent
 * frame is still the active one) is that contract. */
static srmech_status_t cr_map_binds(cr_ctx_t *c, const srmech_json_value_t *step,
                                    cr_mapframe_t *f)
{
    const srmech_json_value_t *bo = srmech_json_object_get(step, "bind");
    uint32_t i;
    assert(c != NULL && step != NULL && f != NULL);
    assert(c->nfr >= 1u);
    f->nb = 0u;
    if (bo == NULL) { return SRMECH_OK; }
    if (bo->type != SRMECH_JSON_OBJECT) { return SRMECH_ERR_BAD_INPUT; }
    if (bo->u.obj.n > CR_BIND_MAX) { return SRMECH_ERR_NOT_IMPL; }
    for (i = 0u; i < bo->u.obj.n; i++) {
        cr_value_t *v = cr_resolve_arg(c, bo->u.obj.vals[i]);
        if (v == NULL) { return SRMECH_ERR_NOT_IMPL; }
        f->bname[i] = bo->u.obj.keys[i];
        f->blen[i] = (uint32_t)strlen(bo->u.obj.keys[i]);
        f->bval[i] = v;
    }
    f->nb = bo->u.obj.n;
    return SRMECH_OK;
}

/* Open a map frame: pin `n` at entry, resolve the binds, carve the body-local
 * outputs and the result list. The caller has already checked depth. */
static srmech_status_t cr_map_enter(cr_ctx_t *c, const srmech_json_value_t *step,
                                    cr_mapframe_t *f)
{
    const srmech_json_value_t *mo = srmech_json_object_get(step, "map_over");
    const srmech_json_value_t *ix = srmech_json_object_get(step, "index");
    const srmech_json_value_t *bd = srmech_json_object_get(step, "body");
    cr_value_t *seq; srmech_status_t st;
    assert(c != NULL && step != NULL && f != NULL);
    assert(c->b != NULL);
    if (mo == NULL || bd == NULL || bd->type != SRMECH_JSON_ARRAY ||
        bd->u.arr.n == 0u) { return SRMECH_ERR_BAD_INPUT; }
    if (ix != NULL && ix->type != SRMECH_JSON_STRING) { return SRMECH_ERR_BAD_INPUT; }
    seq = cr_resolve_arg(c, mo);
    /* `n` is FIXED AT ENTRY — the totality pin. A non-list map_over is
     * compose.py's ChainSpecError ("must resolve to a SIZED sequence"); C
     * declines so the pure path raises that exact error. */
    if (seq == NULL || seq->kind != CR_LIST) { return SRMECH_ERR_NOT_IMPL; }
    st = cr_map_binds(c, step, f);         /* binds see the ENCLOSING scope */
    if (st != SRMECH_OK) { return st; }
    f->body = bd; f->si = 0u; f->k = 0u; f->n = seq->n;
    f->idx_name = (ix != NULL) ? ix->u.str.ptr : NULL;
    f->idx_len = (ix != NULL) ? ix->u.str.len : 0u;
    f->outs = (cr_value_t **)cr_carve(
        c->b, (size_t)bd->u.arr.n * sizeof(void *) + sizeof(void *));
    f->acc = cr_list_of(c->b, seq->n);
    if (f->outs == NULL || f->acc == NULL) { return SRMECH_ERR_OVERFLOW; }
    return SRMECH_OK;
}

/* Run ONE non-map step of the active frame. */
static srmech_status_t cr_step_exec(cr_ctx_t *c, const srmech_json_value_t *step,
                                    cr_value_t **out)
{
    const srmech_json_value_t *so;
    assert(c != NULL && out != NULL);
    assert(step != NULL);
    if (step->type != SRMECH_JSON_OBJECT) { return SRMECH_ERR_BAD_INPUT; }
    so = srmech_json_object_get(step, "on_error");
    if (so != NULL && so->type != SRMECH_JSON_NULL) { return SRMECH_ERR_BAD_INPUT; }
    switch (cr_step_form(step)) {
    case CR_FORM_PLAIN: return cr_run_plain(c, step, out);
    case CR_FORM_FOLD:  return cr_run_fold(c, step, out);
    /* MAP is handled by the trampoline, never here. MIXED / NONE are malformed
     * and earn BAD_INPUT, deliberately distinct from a NOT_IMPL decline. */
    default:            return SRMECH_ERR_BAD_INPUT;
    }
}

/* ------------------------------------------------------------------
 * THE TRAMPOLINE (v0.9.0rc452, `#T1166`) — the MAP step form, last of the
 * three Surface-A forms.
 *
 * ⚠️ WHY THIS SHAPE AND NOT A RECURSIVE BODY WALK. compose.py's spine is
 * frankly recursive (`_run_resolved_steps` re-enters itself per map body) and
 * JPL Rule 1 forbids that here. The frame stack is the same computation with
 * the call stack made explicit and BOUNDED: frames come from the caller arena
 * (Rule 3), depth is capped, and the audit's recursion census stays at its
 * seeded population.
 *
 * The loop is uniform over frames because frame 0 IS the chain body as a
 * degenerate map of n == 1 — see the cr_mapframe_t note. A frame advances its
 * parent's step index only when it POPS, which is the same discipline the
 * nested value walkers use, and is what keeps a map's result landing in
 * exactly one output slot.
 * ------------------------------------------------------------------ */
static srmech_status_t cr_drive(cr_ctx_t *c, cr_value_t **final_out)
{
    assert(c != NULL && final_out != NULL);
    assert(c->nfr == 1u);
    while (c->nfr > 0u) {
        cr_mapframe_t *f = &c->fr[c->nfr - 1u];
        c->step_out = f->outs; c->cur = f->si;
        if (f->si < f->body->u.arr.n) {
            const srmech_json_value_t *step = f->body->u.arr.items[f->si];
            cr_value_t *out = NULL; srmech_status_t st;
            if (step == NULL || step->type != SRMECH_JSON_OBJECT) {
                return SRMECH_ERR_BAD_INPUT;
            }
            if (cr_step_form(step) == CR_FORM_MAP) {
                if (c->nfr >= CR_MAP_DEPTH) { return SRMECH_ERR_NOT_IMPL; }
                st = cr_map_enter(c, step, &c->fr[c->nfr]);
                if (st != SRMECH_OK) { return st; }
                /* n == 0: the body runs ZERO times and the result is the empty
                 * list — compose.py's `for k in range(0)`. Handled WITHOUT
                 * pushing, because a pushed frame would immediately execute its
                 * body once (si starts at 0 and the pop test only runs after a
                 * pass). An empty `x` / `theta` is a real proof case on both
                 * autocorrelation and kuramoto_step, so this is a live path,
                 * not a defensive one. */
                if (c->fr[c->nfr].n == 0u) {
                    f->outs[f->si] = c->fr[c->nfr].acc;
                    f->si++;
                    continue;
                }
                c->nfr++;                  /* parent's si advances on POP */
                continue;
            }
            st = cr_step_exec(c, step, &out);
            if (st != SRMECH_OK) { return st; }
            f->outs[f->si] = out;
            f->si++;
            continue;
        }
        if (f->acc != NULL) {              /* a MAP frame finished one pass */
            if (f->n > 0u) { f->acc->items[f->k] = f->outs[f->body->u.arr.n - 1u]; }
            f->k++;
            if (f->k < f->n) { f->si = 0u; continue; }   /* next iteration */
        }
        c->nfr--;                          /* frame complete */
        if (c->nfr == 0u) {
            *final_out = f->outs[f->body->u.arr.n - 1u];
            return SRMECH_OK;
        }
        c->fr[c->nfr - 1u].outs[c->fr[c->nfr - 1u].si] = f->acc;
        c->fr[c->nfr - 1u].si++;
    }
    return SRMECH_ERR_BAD_INPUT;           /* unreachable: nfr starts at 1 */
}

/* Parse chain + ctx trees, then drive the steps (kept < 60 lines). */
static srmech_status_t cr_run_steps(const srmech_json_value_t *chain,
                                    const srmech_json_value_t *ctx, cr_bump_t *b,
                                    cr_value_t **final_out)
{
    const srmech_json_value_t *steps = srmech_json_object_get(chain, "steps");
    const srmech_json_value_t *oe = srmech_json_object_get(chain, "on_error");
    cr_mapframe_t frames[CR_MAP_DEPTH];
    cr_ctx_t c; uint32_t ns;
    assert(chain != NULL && b != NULL && final_out != NULL);
    assert(b->cur <= b->end);
    if (steps == NULL || steps->type != SRMECH_JSON_ARRAY || steps->u.arr.n == 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (oe != NULL && (oe->type != SRMECH_JSON_STRING || oe->u.str.len != 5u ||
        memcmp(oe->u.str.ptr, "raise", 5u) != 0)) { return SRMECH_ERR_BAD_INPUT; }
    ns = steps->u.arr.n;
    c.row = ctx ? srmech_json_object_get(ctx, "row") : NULL;
    c.inputs = ctx ? srmech_json_object_get(ctx, "inputs") : NULL;
    if (c.row != NULL && c.row->type != SRMECH_JSON_OBJECT) { c.row = NULL; }
    if (c.inputs != NULL && c.inputs->type != SRMECH_JSON_OBJECT) { c.inputs = NULL; }
    c.b = b; c.fr = frames; c.nfr = 1u;
    /* Frame 0 — the chain body, run ONCE. `acc == NULL` is what marks it as
     * the frame whose result is its last step's output rather than a list. */
    frames[0].body = steps; frames[0].si = 0u; frames[0].k = 0u; frames[0].n = 1u;
    frames[0].acc = NULL; frames[0].idx_name = NULL; frames[0].idx_len = 0u;
    frames[0].nb = 0u;
    frames[0].outs = (cr_value_t **)cr_carve(b, (size_t)ns * sizeof(void *) + 1u);
    if (frames[0].outs == NULL) { return SRMECH_ERR_OVERFLOW; }
    c.step_out = frames[0].outs; c.cur = 0u;
    return cr_drive(&c, final_out);
}

/* Run a validated chain node end-to-end + marshal the final value back as a
 * canonical VALUE DESCRIPTOR written into `out`. Reserves a writer arena at the
 * TAIL of the run bump `b` (builder half | write-scratch half); the run bump is
 * the middle and ALSO backs the descriptor's decimal strings (they must outlive
 * the write, so they cannot share the writer scratch new_string does not copy).
 * Both writer bases are 8-byte aligned — the json builder + emit-frame stack
 * require it (UBSAN-checked). `wsz` sizes the writer reserve. Shared by
 * srmech_chain_run + srmech_catalog_run_chain (kept < 60 lines). */
static srmech_status_t cr_run_and_write(const srmech_json_value_t *chain,
                                        const srmech_json_value_t *ctx,
                                        cr_bump_t *b, size_t wsz,
                                        char *out, size_t out_cap,
                                        size_t *out_len)
{
    cr_bump_t wb; cr_value_t *final_v = NULL; srmech_json_builder_t bd;
    srmech_json_value_t *desc; unsigned char *tail_end, *wa; size_t region, half;
    srmech_status_t st;
    assert(chain != NULL && b != NULL && out_len != NULL);
    assert(b->cur <= b->end);
    tail_end = b->end;
    if ((size_t)(b->end - b->cur) <= wsz + 4096u) { return SRMECH_ERR_OVERFLOW; }
    b->end = tail_end - wsz;                    /* shrink run bump */
    st = cr_run_steps(chain, ctx, b, &final_v);
    if (st != SRMECH_OK) { return st; }
    wa = cr_align(b->end);                      /* builder base, 8-aligned */
    if (wa >= tail_end) { return SRMECH_ERR_OVERFLOW; }
    region = (size_t)(tail_end - wa); half = region / 2u;
    st = srmech_json_builder_init(&bd, wa, half);
    if (st != SRMECH_OK) { return st; }
    desc = cr_desc(&bd, final_v, b);            /* dec strings from run bump */
    if (desc == NULL || bd.failed) { return SRMECH_ERR_OVERFLOW; }
    wb.cur = cr_align(wa + half); wb.end = tail_end;   /* write scratch */
    { size_t need = srmech_json_write_arena_bytes(desc);
      if (wb.cur >= wb.end || need > (size_t)(wb.end - wb.cur)) {
          return SRMECH_ERR_OVERFLOW;
      }
      return srmech_json_write_ws(desc, out, out_cap, out_len, wb.cur, need); }
}

srmech_status_t srmech_chain_run(const char *chain_json, size_t chain_len,
                                 const char *ctx_json, size_t ctx_len,
                                 void *ws, size_t ws_len,
                                 char *out, size_t out_cap, size_t *out_len)
{
    cr_bump_t b; srmech_json_value_t *chain = NULL, *ctx = NULL;
    srmech_status_t st; size_t pj, cj; unsigned char *pa, *ca;
    assert(out_len != NULL);
    assert(chain_json != NULL || chain_len == 0u);
    if (chain_json == NULL || ws == NULL || out == NULL || out_len == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    b.cur = (unsigned char *)ws; b.end = b.cur + ws_len;
    pj = 128u * chain_len + 16384u; cj = 128u * ctx_len + 16384u;
    pa = cr_carve(&b, pj); ca = cr_carve(&b, cj);
    if (pa == NULL || ca == NULL) { return SRMECH_ERR_OVERFLOW; }
    st = srmech_json_parse(chain_json, chain_len, pa, pj, &chain);
    if (st != SRMECH_OK) { return st; }
    if (ctx_json != NULL && ctx_len > 0u) {
        st = srmech_json_parse(ctx_json, ctx_len, ca, cj, &ctx);
        if (st != SRMECH_OK) { return st; }
    }
    return cr_run_and_write(chain, ctx, &b, 16384u + 8u * (chain_len + ctx_len),
                            out, out_cap, out_len);
}

/* ------------------------------------------------------------------
 * srmech_catalog_run_chain — run_catalog_chain: resolve a catalog's NAMED
 * operator chain + run it (0.9.0rc175; the ORCHESTRATION→C spine, batch 5).
 * COMPOSES the rc173 catalog parse (find the chain by name in operator_chain)
 * + the rc174 chain-runner (cr_run_and_write). A bare-C host runs a declared
 * catalog chain by name with this one call. cat_json = {chain_schema_version,
 * operator_chain:[...]} (the Python catalog's chains, json.dumps'd);
 * chain_name = the chain's "name"; ctx_json = {"row":.., "inputs":..}. A chain
 * not found / a non-table op / a non-i64 input / overflow -> non-OK so the
 * Python caller runs the COMPLETE pure path (the not-found KeyError / the run
 * over the live object graph). Same value-descriptor OUTPUT contract as
 * srmech_chain_run.
 * ------------------------------------------------------------------ */

/* Linear scan operator_chain for the chain whose "name" equals [name,name_len).
 * NULL if not found (the Python caller then raises KeyError on the pure path). */
static const srmech_json_value_t *cr_find_named_chain(
    const srmech_json_value_t *chains, const char *name, size_t name_len)
{
    uint32_t i;
    assert(chains != NULL && name != NULL);
    assert(chains->type == SRMECH_JSON_ARRAY);
    for (i = 0u; i < chains->u.arr.n; i++) {
        const srmech_json_value_t *ch = chains->u.arr.items[i];
        const srmech_json_value_t *nm;
        if (ch == NULL || ch->type != SRMECH_JSON_OBJECT) { continue; }
        nm = srmech_json_object_get(ch, "name");
        if (nm != NULL && nm->type == SRMECH_JSON_STRING &&
            (size_t)nm->u.str.len == name_len &&
            (name_len == 0u || memcmp(nm->u.str.ptr, name, name_len) == 0)) {
            return ch;
        }
    }
    return NULL;
}

size_t srmech_catalog_run_chain_arena_bytes(size_t cat_len, size_t ctx_len)
{
    size_t parse = 128u * cat_len + 128u * ctx_len + 65536u;
    size_t run = 4096u * cat_len + (1u << 20);
    size_t writer = 32768u + 16u * (cat_len + ctx_len);
    assert(sizeof(srmech_bigint_t) <= 64u);
    assert(sizeof(cr_value_t) <= 128u);
    return parse + run + writer;
}

srmech_status_t srmech_catalog_run_chain(const char *cat_json, size_t cat_len,
                                         const char *chain_name, size_t name_len,
                                         const char *ctx_json, size_t ctx_len,
                                         void *ws, size_t ws_len,
                                         char *out, size_t out_cap,
                                         size_t *out_len)
{
    cr_bump_t b; srmech_json_value_t *tree = NULL, *ctx = NULL;
    const srmech_json_value_t *chains, *ver, *chain; srmech_status_t st;
    size_t pj, cj; unsigned char *pa, *ca;
    assert(out_len != NULL);
    assert(cat_json != NULL || cat_len == 0u);
    if (cat_json == NULL || chain_name == NULL || ws == NULL || out == NULL ||
        out_len == NULL) { return SRMECH_ERR_NULL_ARG; }
    b.cur = (unsigned char *)ws; b.end = b.cur + ws_len;
    pj = 128u * cat_len + 32768u; cj = 128u * ctx_len + 16384u;
    pa = cr_carve(&b, pj); ca = cr_carve(&b, cj);
    if (pa == NULL || ca == NULL) { return SRMECH_ERR_OVERFLOW; }
    st = srmech_json_parse(cat_json, cat_len, pa, pj, &tree);
    if (st != SRMECH_OK) { return st; }
    if (tree->type != SRMECH_JSON_OBJECT) { return SRMECH_ERR_BAD_INPUT; }
    ver = srmech_json_object_get(tree, "chain_schema_version");
    if (ver == NULL || ver->type != SRMECH_JSON_INT || ver->u.i != 1) {
        return SRMECH_ERR_BAD_INPUT;
    }
    chains = srmech_json_object_get(tree, "operator_chain");
    if (chains == NULL || chains->type != SRMECH_JSON_ARRAY) {
        return SRMECH_ERR_BAD_INPUT;
    }
    chain = cr_find_named_chain(chains, chain_name, name_len);
    if (chain == NULL) { return SRMECH_ERR_BAD_INPUT; }   /* -> pure KeyError */
    if (ctx_json != NULL && ctx_len > 0u) {
        st = srmech_json_parse(ctx_json, ctx_len, ca, cj, &ctx);
        if (st != SRMECH_OK) { return st; }
    }
    return cr_run_and_write(chain, ctx, &b, 16384u + 8u * (cat_len + ctx_len),
                            out, out_cap, out_len);
}
