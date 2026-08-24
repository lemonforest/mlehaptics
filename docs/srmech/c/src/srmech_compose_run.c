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
    /* THE BYTES CARRIER IS A FLAG ON CR_STR, NOT A SEVENTH KIND (rc452,
     * gh #1653 — the klein4_from_one closure). Python's chain vocabulary
     * distinguishes str from bytes and the ops enforce it (utf8_encode wants
     * a str, sha256_bytes/byte_slice/int_parse_le want bytes — handing either
     * the other RAISES in Python, so the C twin must DECLINE, never coerce).
     * The precedent is `is_tuple` above, and for the same reason: every
     * in-chain consumer reads the buffer identically; only the TYPE CONTRACT
     * differs. Unlike `is_tuple` this flag has NO wire letter yet — a bytes
     * FINAL value cannot cross srmech_chain_run's output wire and the run
     * declines (see cr_run_and_write) until the `b` kind ships with
     * encode_loe_content's closure, which is the chain that returns one. */
    int is_bytes;              /* CR_STR only: 1 -> the value is bytes      */
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
    v->is_bytes = 0;   /* STR unless an op says otherwise (utf8_encode etc.) */
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
/* 12: the measured maximum over the packaged descriptors is 9 binds on one
 * frame (kuramoto_step/general's outer map), and 8 — the rc452 first cut —
 * declined that frame with every op arm present, which read as an op-table
 * gap until measured. Slack of 3 over the live maximum, still bounded. */
#define CR_BIND_MAX  12u

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

/* Which of the five *_series_truncate kernels a series step runs. An ENUM, not
 * a function pointer: JPL Rule 9 bans function pointers, and the `cr_series_fn_t`
 * typedef that stood here through the first rc452 cut was one of the 14 measured
 * Rule-9 declarator sites the A1 conversion drains (see JPL_AUDIT.md Rule 9). */
typedef enum {
    CR_SER_EXP = 0, CR_SER_SIN, CR_SER_COS, CR_SER_LOG1P, CR_SER_ATAN
} cr_series_id_t;

/* The kernel switch. NO default arm, so gcc/clang's -Wswitch (in -Wall,
 * promoted by -Werror under SRMECH_PEDANTIC) makes "enum grew, case forgotten"
 * a COMPILE ERROR; MSVC gets the same property from /w44062 in CMakeLists.
 * The trailing return is the open-enum path (a value outside the enum). */
static srmech_status_t cr_series_kernel(cr_series_id_t id,
                                        const srmech_bigint_t *xn,
                                        const srmech_bigint_t *xd, uint32_t nt,
                                        srmech_bigint_t *on, srmech_bigint_t *od,
                                        void *ws, size_t wl)
{
    assert(xn != NULL && xd != NULL);
    assert(on != NULL && od != NULL);
    switch (id) {
    case CR_SER_EXP:   return srmech_exp_series_truncate_big(xn, xd, nt, on, od, ws, wl);
    case CR_SER_SIN:   return srmech_sin_series_truncate_big(xn, xd, nt, on, od, ws, wl);
    case CR_SER_COS:   return srmech_cos_series_truncate_big(xn, xd, nt, on, od, ws, wl);
    case CR_SER_LOG1P: return srmech_log1p_series_truncate_big(xn, xd, nt, on, od, ws, wl);
    case CR_SER_ATAN:  return srmech_atan_series_truncate_big(xn, xd, nt, on, od, ws, wl);
    }
    return SRMECH_ERR_INTERNAL;
}

/* Shared driver for the five *_series_truncate ops:
 * (numerator, denominator, num_terms) -> reduced (num, den) rational. */
static srmech_status_t cr_op_series(cr_ctx_t *c, const srmech_json_value_t *args,
                                    cr_series_id_t id, cr_value_t **out)
{
    cr_value_t *xn = cr_arg(c, args, "numerator");
    cr_value_t *xd = cr_arg(c, args, "denominator");
    cr_value_t *nt = cr_arg(c, args, "num_terms"), *ov;
    int64_t nterms; uint32_t cap, dig; void *ws; size_t wl; srmech_status_t st;
    assert(c != NULL && out != NULL);
    assert(args != NULL);
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
    st = cr_series_kernel(id, xn->num, xd->num, (uint32_t)nterms,
                          ov->num, ov->den, ws, wl);
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

/* Which f64 sequence kernel a dseq step runs. An ENUM, not a function-pointer
 * parameter — the inline `(*fn)(const double *, size_t, double *)` param that
 * stood here through the first rc452 cut was a Rule-9 declarator site (it
 * PREDATES rc452; see JPL_AUDIT.md Rule 9). */
typedef enum { CR_DSEQ_CHIRAL_FLIP = 0, CR_DSEQ_AUTOCORR } cr_dseq_id_t;

/* The kernel switch — same no-default drift gate as cr_series_kernel. */
static srmech_status_t cr_dseq_kernel(cr_dseq_id_t id, const double *in,
                                      size_t n, double *res)
{
    assert(in != NULL && res != NULL);
    assert(n > 0u);
    switch (id) {
    case CR_DSEQ_CHIRAL_FLIP: return srmech_cascade_chiral_flip_f64(in, n, res);
    case CR_DSEQ_AUTOCORR:    return srmech_autocorrelation_f64(in, n, res);
    }
    return SRMECH_ERR_INTERNAL;
}

/* A unary f64 sequence op: resolve `key` as a real vector, run the kernel `id`
 * names, wrap the result. `out` must not alias the input, so a second buffer
 * is carved. */
static srmech_status_t cr_op_dseq(cr_ctx_t *c, const srmech_json_value_t *args,
                                  const char *key, cr_dseq_id_t id,
                                  cr_value_t **out)
{
    cr_value_t *v; double *in, *res; size_t n = 0u; srmech_status_t st;
    assert(c != NULL && args != NULL && out != NULL);
    assert(key != NULL);
    v = cr_arg(c, args, key);
    if (v == NULL) { return SRMECH_ERR_NOT_IMPL; }
    in = cr_as_dvec(c->b, v, &n);
    if (in == NULL) { return SRMECH_ERR_NOT_IMPL; }
    res = (double *)cr_carve(c->b, n * sizeof(double) + sizeof(double));
    if (res == NULL) { return SRMECH_ERR_OVERFLOW; }
    if (n > 0u) {
        st = cr_dseq_kernel(id, in, n, res);
        if (st != SRMECH_OK) { return st; }
    }
    *out = cr_dvec_value(c->b, res, n);
    return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* The real-sequence helpers. Through rc451 these were the arms of
 * cr_dispatch_real, a second dispatcher split out only to keep cr_dispatch
 * under JPL Rule 4's 60 lines; the rc452 A1 reshape DELETED that function, and
 * dispatch now reaches these bodies through a CR_OP_REG row's dom/sub enums
 * via cr_exec_<domain>(). An unmatched op still returns NOT_IMPL. */
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
 * So `CR_OP_REG` stops being a name-to-name index and becomes the atom
 * registry the interpreter resolves against: a bare-C, config-addressable
 * table of pure DATA rows. `cr_dispatch` collapses from a 57-line if-chain to
 * a row lookup plus a bounded per-domain switch tree, and `cr_dispatch_real` —
 * which existed only to absorb the overflow — is GONE. Adding an op is now
 * adding a ROW plus one `case` line, which is why the table can carry 56.
 *
 * ⚠️ NO FUNCTION POINTERS — the A1 dispatch (JPL Rule 9). The first rc452 cut
 * gave rows `fn`/`bin` FUNCTION-POINTER columns, which Rule 9 bans outright
 * ("Function pointers are not permitted."), and which the mechanical audit
 * never saw because tests/test_jpl_audit.py checks Rules 1/3/4/5/8 only. The
 * rows instead carry three small-int ENUM columns (`dom`/`sub`/`bin`) and
 * `cr_dispatch` hands `sub` to one `cr_exec_<domain>()` per domain. Each exec
 * switches on its OWN enum type with NO `default:` arm, so gcc/clang's
 * -Wswitch under the existing -Werror makes "row added, case forgotten" a
 * COMPILE ERROR (MSVC needs /w44062, added to SRMECH_PEDANTIC in CMakeLists —
 * C4062 is off by default even at /W4). That compile-time drift gate is the
 * point of this shape over a flat enum, whose single switch would have needed
 * `default:` arms and let a deleted case compile green and fail at runtime.
 *
 * ⚠️ THE TABLE IS THE ONLY DISPATCH PATH. `cr_dispatch` contains zero
 * `cr_op_is` calls of its own; the one call site is inside the loop, against
 * the row's own `bare`/`len`. tests/test_t1158_registry_param_order_rc449.py
 * asserts exactly that, so a future arm added BESIDE the table (leaving the
 * table decorative — the shape a green could otherwise be bought with) is red.
 *
 * FIVE COLUMNS, and the fifth is the one that closes the fold body:
 *   bare/len  the segment-boundary match cr_op_is performs
 *   full      the ToolEntry name cr_args_keyset_ok validates `args` keys against
 *   dom       which cr_exec_<domain>() runs the op (cr_dom_t)
 *   sub       the case label inside that exec (the domain's own op enum)
 *   bin       non-NONE iff the op can also serve as a FOLD BODY (cr_bin_id_t)
 *
 * ⚠️ WHY `bin` IS A COLUMN AND NOT A SECOND TABLE. A fold body receives two
 * POSITIONAL carriers (acc, elem) that are already evaluated — there is no
 * `args` JSON object to pull from, so the plain-op entry shape genuinely
 * cannot serve. Through rc451 that difference was expressed as a PRIVATE
 * single-entry table (`cr_fold_body`, orientation_compose only), which is why
 * a fold over any other op declined and why CEIL_SURFACE_A_UNSUPPORTED_FORMS
 * still counted `fold` unsupported with a real fold chain shipping. Making it
 * a column on the SAME table keeps one registry — so the bijection gate still
 * sees every op exactly once — while stating honestly that the two entry
 * shapes differ.
 * ------------------------------------------------------------------ */

/* Which cr_exec_<domain>() runs an op. CR_DOM_NONE is the deliberate,
 * expressible "fold-body-ONLY row" state (cr_dispatch returns NOT_IMPL for
 * it) — the same state the first cut's `fn == NULL` encoded. */
typedef enum { CR_DOM_NONE = 0, CR_DOM_RAT, CR_DOM_CYC, CR_DOM_CAS } cr_dom_t;

/* The Class-N rational-domain ops (srmech.math.rational.*). */
typedef enum {
    CR_RAT_PI = 0, CR_RAT_EXP, CR_RAT_SIN, CR_RAT_COS, CR_RAT_LOG1P,
    CR_RAT_ATAN, CR_RAT_POW, CR_RAT_ADD, CR_RAT_MUL, CR_RAT_DIV,
    CR_RAT_SCALE_ROUND, CR_RAT_BEST_RATIONAL
} cr_rat_op_t;

/* The Class-I cyclic-domain ops (srmech.math.cyclic.*). MOD_MUL and
 * MOD_MUL_WIDE are separate case labels dispatching the SAME driver arm, so
 * the row-to-case mapping stays 1:1 for the bijection gate. */
typedef enum {
    CR_CYC_GCD = 0, CR_CYC_MOD_ADD, CR_CYC_MOD_MUL, CR_CYC_MOD_MUL_WIDE,
    CR_CYC_MOD_POW, CR_CYC_MOD_INV
} cr_cyc_op_t;

/* The cascade-domain ops (srmech.cascade.*): Classes B / C / K / L — plus,
 * since rc452 Phase 3 (`#T1166`), the Class-N/M/C kuramoto term ops and the
 * Class-M/C/N hypercomplex-DFT step ops (the OP-granular arms of the three
 * map chains this phase unblocks; the fused whole-transform symbols exist and
 * are deliberately NOT dispatched — see the atom-table note below). */
typedef enum {
    CR_CAS_SEQ_LEN = 0, CR_CAS_CORR_PRODUCT, CR_CAS_COMPENSATED_SUM,
    CR_CAS_PIN_SLOT, CR_CAS_REORIENT, CR_CAS_CHIRAL_FLIP,
    CR_CAS_AUTOCORRELATION, CR_CAS_DEAD_BAND, CR_CAS_PAIR,
    CR_CAS_SEQ_GET, CR_CAS_VEC_SCALE,
    CR_CAS_KUR_INV_N, CR_CAS_KUR_SIN_TERM, CR_CAS_KUR_OUT_SIMPLE,
    CR_CAS_KUR_GEN_TERM, CR_CAS_KUR_GEN_OUT,
    CR_CAS_AS_QUAT4, CR_CAS_AS_OCT8,
    CR_CAS_QDFT_RESOLVE_MU, CR_CAS_ODFT_RESOLVE_MU,
    CR_CAS_DFT_SIGMA, CR_CAS_DFT_SCALE,
    CR_CAS_QDFT_SUMMAND, CR_CAS_ODFT_SUMMAND,
    /* wave C (rc452, gh #1653): the klein4_from_one chain's string/bytes
     * leaves — Classes F / B / A at step granularity. 30 of the documented
     * 51-case split threshold; the growth path is a new domain enum, not a
     * default: arm. */
    CR_CAS_RENDER_TEMPLATE, CR_CAS_UTF8_ENCODE, CR_CAS_SHA256_BYTES,
    CR_CAS_STR_CONCAT, CR_CAS_BYTE_SLICE, CR_CAS_INT_PARSE_LE,
    /* wave D (rc452, gh #1653): the encode_loe_content chain's Class-A mint /
     * Class-C permute / Class-M bind leaves, plus the raw-digest Class-A twin.
     * Each delegates to ONE step-granular compiled export the Python op itself
     * composes (srmech_sha256_hex / srmech_mint_vector / srmech_hdc_permute /
     * srmech_hdc_bind) — there is no fused whole-chain symbol for this chain
     * to reach for, and the no-coarse source gate derives that population
     * itself. 34 of the documented 51-case split threshold. */
    CR_CAS_SHA256_RAW, CR_CAS_MINT_VECTOR, CR_CAS_HDC_PERMUTE, CR_CAS_HDC_BIND
} cr_cas_op_t;

/* Which fold body a row provides. CR_BIN_NONE = the op cannot fold.
 * F64_ADD / VEC_ADD (rc452 Phase 3) are the Σ accumulators of the kuramoto
 * and hypercomplex-DFT map chains — fold-body-ONLY rows, like ORIENT. */
typedef enum {
    CR_BIN_NONE = 0, CR_BIN_GCD, CR_BIN_ORIENT, CR_BIN_F64_ADD, CR_BIN_VEC_ADD
} cr_bin_id_t;

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
    return cr_op_dseq(c, a, "x", CR_DSEQ_AUTOCORR, o);
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
 * EXACT-DYADIC MACHINERY (v0.9.0rc452 Phase 3, `#T1166`) — the kuramoto
 * chains' middle is EXACT-ℚ in Python: `kuramoto_sin_term` returns the Q61
 * rational Q(v, 2^61) (srmech.math.rational.sin — never libm), the fold
 * accumulates it exactly (float + Q promotes the float via as_integer_ratio),
 * and ONE `float(...)` collapse happens in the Euler-combine op. Every
 * denominator on that path is a power of two, so the collapse is a
 * correctly-rounded DYADIC→double conversion (CPython int/int truediv,
 * round-half-even) — implemented here on the bigint carrier. A non-dyadic
 * denominator or an out-of-envelope exponent DECLINES to pure, never rounds
 * wrongly.
 * ------------------------------------------------------------------ */

/* IEEE-754 2^e as a double, e in [-1022, 1023] (normal range only). */
static double cr_pow2(int e)
{
    uint64_t bits; double out;
    assert(e >= -1022);
    assert(e <= 1023);
    bits = ((uint64_t)(e + 1023)) << 52;
    memcpy(&out, &bits, sizeof(out));
    return out;
}

/* A fresh bigint holding mag * 2^shift (mag as uint64). NULL on overflow. */
static srmech_bigint_t *cr_bi_u64_shl(cr_bump_t *b, uint64_t mag, uint32_t shift)
{
    srmech_bigint_t *bi; uint32_t w = shift / 32u, s = shift % 32u, i, n;
    assert(b != NULL);
    assert(shift <= 4096u);
    bi = cr_new_bigint(b, w + 4u);
    if (bi == NULL) { return NULL; }
    for (i = 0u; i < w + 3u; i++) { bi->limbs[i] = 0u; }
    bi->limbs[w] = (uint32_t)((mag << s) & 0xFFFFFFFFu);
    bi->limbs[w + 1u] = (uint32_t)((s == 0u) ? (mag >> 32)
                                  : ((mag >> (32u - s)) & 0xFFFFFFFFu));
    bi->limbs[w + 2u] = (uint32_t)((s == 0u) ? 0u : (mag >> (64u - s)));
    n = w + 3u;
    while (n > 0u && bi->limbs[n - 1u] == 0u) { n--; }
    bi->n = n; bi->sign = (n == 0u) ? 0 : 1;
    return bi;
}

/* float.as_integer_ratio: the EXACT reduced (num, den) of a finite double.
 * 0 on a non-finite x (no rational exists — the caller declines). */
static int cr_q_of_dbl(cr_bump_t *b, double x,
                       srmech_bigint_t **num, srmech_bigint_t **den)
{
    uint64_t bits, mant; int e, raw, neg;
    assert(b != NULL);
    assert(num != NULL && den != NULL);
    memcpy(&bits, &x, sizeof(bits));
    raw = (int)((bits >> 52) & 0x7FFu);
    neg = (bits >> 63) != 0u;
    if (raw == 0x7FF) { return 0; }              /* nan / inf — no rational */
    mant = bits & ((UINT64_C(1) << 52) - 1u);
    if (raw == 0) { e = -1074; } else { mant |= (UINT64_C(1) << 52); e = raw - 1075; }
    if (mant == 0u) {                            /* ±0.0 -> (0, 1) */
        *num = cr_bi_u64_shl(b, 0u, 0u); *den = cr_bi_u64_shl(b, 1u, 0u);
        return (*num != NULL && *den != NULL);
    }
    while ((mant & 1u) == 0u && e < 0) { mant >>= 1; e++; }
    if (e >= 0) {
        *num = cr_bi_u64_shl(b, mant, (uint32_t)e);
        *den = cr_bi_u64_shl(b, 1u, 0u);
    } else {
        *num = cr_bi_u64_shl(b, mant, 0u);
        *den = cr_bi_u64_shl(b, 1u, (uint32_t)(-e));
    }
    if (*num == NULL || *den == NULL) { return 0; }
    if (neg) { (*num)->sign = -(*num)->sign; }
    return 1;
}

/* Bit `i` of a bigint's magnitude (0 past the top). */
static int cr_bi_bit(const srmech_bigint_t *m, uint32_t i)
{
    assert(m != NULL);
    assert(m->cap >= m->n);
    if ((i / 32u) >= m->n) { return 0; }
    return (int)((m->limbs[i / 32u] >> (i % 32u)) & 1u);
}

/* den == 2^k exactly? Yes -> *k_out; else 0 (the caller declines). */
static int cr_bi_pow2_log(const srmech_bigint_t *den, uint32_t *k_out)
{
    uint32_t i, t = 0u, top;
    assert(den != NULL);
    assert(k_out != NULL);
    if (den->sign <= 0 || den->n == 0u) { return 0; }
    for (i = 0u; i + 1u < den->n; i++) {
        if (den->limbs[i] != 0u) { return 0; }
    }
    top = den->limbs[den->n - 1u];
    if (top == 0u || (top & (top - 1u)) != 0u) { return 0; }
    while (((top >> t) & 1u) == 0u) { t++; }
    *k_out = (den->n - 1u) * 32u + t;
    return 1;
}

/* Correctly-rounded (round-half-even) double of num / 2^k — CPython's
 * int.__truediv__ on the dyadic domain. 0 -> decline (non-dyadic den or an
 * exponent outside the guarded normal envelope). */
static int cr_q_dyadic_dbl(const srmech_bigint_t *num,
                           const srmech_bigint_t *den, double *out)
{
    uint32_t k = 0u, L, i; uint64_t keep = 0u; int sticky = 0, e2;
    double d;
    assert(num != NULL && den != NULL);
    assert(out != NULL);
    if (!cr_bi_pow2_log(den, &k)) { return 0; }
    if (num->n == 0u) { *out = 0.0; return 1; }
    L = (num->n - 1u) * 32u + 32u;
    while (L > 0u && cr_bi_bit(num, L - 1u) == 0) { L--; }
    if (L <= 53u) {
        d = 0.0;
        for (i = num->n; i-- > 0u; ) { d = d * 4294967296.0 + (double)num->limbs[i]; }
        e2 = -(int)k;
    } else {
        uint32_t shift = L - 54u; uint64_t top54 = 0u; int guard;
        for (i = 0u; i < 54u; i++) {
            top54 |= ((uint64_t)cr_bi_bit(num, shift + i)) << i;
        }
        for (i = 0u; i < shift && !sticky; i++) {
            if (cr_bi_bit(num, i)) { sticky = 1; }
        }
        guard = (int)(top54 & 1u);
        keep = top54 >> 1;
        if (guard && (sticky || (keep & 1u))) { keep++; }
        e2 = (int)shift + 1 - (int)k;
        if (keep == (UINT64_C(1) << 53)) { keep >>= 1; e2++; }
        d = (double)keep;                        /* <= 2^53: exact */
    }
    if (e2 < -960 || e2 > 960) { return 0; }     /* stay well inside normal */
    d = d * cr_pow2(e2);                         /* pow-of-two scale: exact */
    *out = (num->sign < 0) ? -d : d;
    return 1;
}

/* One exact rational binop into FRESH arena carriers (reduced, den > 0). */
static srmech_status_t cr_q_apply(cr_bump_t *b, char op,
                                  const srmech_bigint_t *an, const srmech_bigint_t *ad,
                                  const srmech_bigint_t *bn, const srmech_bigint_t *bd,
                                  srmech_bigint_t **on, srmech_bigint_t **od)
{
    cr_qctx_t q; uint32_t lim, cap;
    assert(b != NULL && on != NULL && od != NULL);
    assert(an != NULL && ad != NULL && bn != NULL && bd != NULL);
    lim = an->n + ad->n + bn->n + bd->n + 4u;
    cap = lim * 2u + 8u;
    *on = cr_new_bigint(b, cap); *od = cr_new_bigint(b, cap);
    if (*on == NULL || *od == NULL) { return SRMECH_ERR_OVERFLOW; }
    if (!cr_qctx_init(b, &q, lim)) { return SRMECH_ERR_OVERFLOW; }
    return cr_q_binop(&q, op, an, ad, bn, bd, *on, *od);
}

/* The Q61 rational Q(v, 2^61), REDUCED — what srmech.math.rational.sin
 * returns (Q.__init__ reduces; on a power-of-two denominator the whole gcd
 * is the shared factor of two, i.e. v's trailing zeros capped at 61). */
static cr_value_t *cr_q61_rat(cr_bump_t *b, int64_t v)
{
    cr_value_t *ov; uint64_t mag; uint32_t t = 0u;
    assert(b != NULL);
    assert(b->cur <= b->end);
    ov = cr_new_value(b, CR_RATIONAL);
    if (ov == NULL) { return NULL; }
    if (v == 0) {
        ov->num = cr_bi_u64_shl(b, 0u, 0u); ov->den = cr_bi_u64_shl(b, 1u, 0u);
        return (ov->num != NULL && ov->den != NULL) ? ov : NULL;
    }
    mag = (v < 0) ? (uint64_t)(-v) : (uint64_t)v;   /* Class-K pin read */
    while (((mag >> t) & 1u) == 0u && t < 61u) { t++; }
    ov->num = cr_bi_u64_shl(b, mag >> t, 0u);
    ov->den = cr_bi_u64_shl(b, 1u, 61u - t);
    if (ov->num == NULL || ov->den == NULL) { return NULL; }
    if (v < 0) { ov->num->sign = -1; }              /* Class-C re-application */
    return ov;
}

/* ------------------------------------------------------------------
 * THE KURAMOTO STEP OPS (rc452 Phase 3) — the five per-term atoms of
 * kuramoto_step.toml's two chains, at STEP granularity. The fused
 * srmech_cascade_kuramoto_step_f64 / _general_f64 symbols exist and are
 * deliberately NOT referenced from this TU: a chain that runs because one
 * coarse symbol recognised its shape is the bypass the step-mutation
 * witness exists to refuse. The sin is srmech_sin_q61 — the SAME Q61
 * cascade srmech.math.rational.sin projects (byte-exact pure mirror), so
 * the chain's exact-ℚ middle is reproduced, not approximated.
 * ------------------------------------------------------------------ */

/* One list element as a double, i64-indexed with bounds. 1 on success. */
static int cr_list_at_dbl(const cr_value_t *lst, int64_t i, double *out)
{
    assert(out != NULL);
    assert(i >= INT64_MIN);
    if (lst == NULL || lst->kind != CR_LIST) { return 0; }
    if (i < 0 || (uint64_t)i >= (uint64_t)lst->n) { return 0; }
    return cr_elem_dbl(lst, (uint32_t)i, out);
}

/* kuramoto_inv_n(coupling, n): the mean-field scale K/n (0.0 when n == 0). */
static srmech_status_t cr_op_kur_inv_n(cr_ctx_t *c, const srmech_json_value_t *a,
                                       cr_value_t **o)
{
    double coupling = 0.0; int64_t n = 0; cr_value_t *nv;
    assert(c != NULL && a != NULL);
    assert(o != NULL);
    if (!cr_arg_dbl(c, a, "coupling", &coupling)) { return SRMECH_ERR_NOT_IMPL; }
    nv = cr_arg(c, a, "n");
    if (nv == NULL || !cr_as_i64(nv, &n) || n < 0) { return SRMECH_ERR_NOT_IMPL; }
    if (n > (INT64_C(1) << 53)) { return SRMECH_ERR_NOT_IMPL; }
    *o = cr_dbl(c->b, (n > 0) ? (coupling / (double)n) : 0.0);
    return (*o == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* kuramoto_sin_term(theta, i, j) -> the EXACT Q61 rational sin(θj − θi). */
static srmech_status_t cr_op_kur_sin_term(cr_ctx_t *c, const srmech_json_value_t *a,
                                          cr_value_t **o)
{
    cr_value_t *th, *vi, *vj; int64_t i, j; double xi, xj, s; int64_t q61 = 0;
    assert(c != NULL && a != NULL);
    assert(o != NULL);
    th = cr_arg(c, a, "theta"); vi = cr_arg(c, a, "i"); vj = cr_arg(c, a, "j");
    if (th == NULL || vi == NULL || vj == NULL) { return SRMECH_ERR_NOT_IMPL; }
    if (!cr_as_i64(vi, &i) || !cr_as_i64(vj, &j)) { return SRMECH_ERR_NOT_IMPL; }
    if (!cr_list_at_dbl(th, i, &xi) || !cr_list_at_dbl(th, j, &xj)) {
        return SRMECH_ERR_NOT_IMPL;
    }
    s = xj - xi;
    if (srmech_sin_q61(s, &q61) != SRMECH_OK) { return SRMECH_ERR_NOT_IMPL; }
    *o = cr_q61_rat(c->b, q61);
    return (*o == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* w * Q — the float coefficient promoted exactly, the product reduced (the
 * Q.__rmul__ path both kuramoto term/combine ops ride). */
static srmech_status_t cr_q_scale(cr_bump_t *b, double w, const cr_value_t *q,
                                  srmech_bigint_t **on, srmech_bigint_t **od)
{
    srmech_bigint_t *wn, *wd;
    assert(b != NULL && q != NULL);
    assert(on != NULL && od != NULL);
    if (!cr_q_of_dbl(b, w, &wn, &wd)) { return SRMECH_ERR_NOT_IMPL; }
    return cr_q_apply(b, '*', wn, wd, q->num, q->den, on, od);
}

/* kuramoto_gen_term(theta, adjacency, coupling, inv_n, alpha, i, j) ->
 * the EXACT rational w·sin(θj − θi − α); w = K·A[i][j], or inv_n when the
 * adjacency is None (the mean-field row). */
static srmech_status_t cr_op_kur_gen_term(cr_ctx_t *c, const srmech_json_value_t *a,
                                          cr_value_t **o)
{
    cr_value_t *th, *adj, *vi, *vj, *qs, *ov;
    double kc = 0.0, inv_n = 0.0, alpha = 0.0, xi, xj, w; int64_t i, j, q61 = 0;
    srmech_status_t st;
    assert(c != NULL && a != NULL);
    assert(o != NULL);
    th = cr_arg(c, a, "theta"); adj = cr_arg(c, a, "adjacency");
    vi = cr_arg(c, a, "i"); vj = cr_arg(c, a, "j");
    if (th == NULL || adj == NULL || vi == NULL || vj == NULL) {
        return SRMECH_ERR_NOT_IMPL;
    }
    if (!cr_arg_dbl(c, a, "coupling", &kc) || !cr_arg_dbl(c, a, "inv_n", &inv_n) ||
        !cr_arg_dbl(c, a, "alpha", &alpha)) { return SRMECH_ERR_NOT_IMPL; }
    if (!cr_as_i64(vi, &i) || !cr_as_i64(vj, &j)) { return SRMECH_ERR_NOT_IMPL; }
    if (!cr_list_at_dbl(th, i, &xi) || !cr_list_at_dbl(th, j, &xj)) {
        return SRMECH_ERR_NOT_IMPL;
    }
    if (adj->kind == CR_NONE) { w = inv_n; }
    else {
        double aij;
        if (adj->kind != CR_LIST || i < 0 || (uint64_t)i >= (uint64_t)adj->n ||
            !cr_list_at_dbl(adj->items[i], j, &aij)) { return SRMECH_ERR_NOT_IMPL; }
        w = kc * aij;
    }
    if (srmech_sin_q61((xj - xi) - alpha, &q61) != SRMECH_OK) {
        return SRMECH_ERR_NOT_IMPL;
    }
    qs = cr_q61_rat(c->b, q61);
    ov = cr_new_value(c->b, CR_RATIONAL);
    if (qs == NULL || ov == NULL) { return SRMECH_ERR_OVERFLOW; }
    st = cr_q_scale(c->b, w, qs, &ov->num, &ov->den);
    if (st != SRMECH_OK) { return st; }
    *o = ov;
    return SRMECH_OK;
}

/* float(theta_i + dt·(om + coef·s)) with s an EXACT rational — the shared
 * exact tail of both Euler-combine ops. Every op reduces, then ONE dyadic
 * collapse (the chain's single float() boundary). */
static srmech_status_t cr_kur_combine_q(cr_bump_t *b, double theta_i, double om,
                                        double coef, double dt,
                                        const srmech_bigint_t *sn,
                                        const srmech_bigint_t *sd, cr_value_t **o)
{
    srmech_bigint_t *pn, *pd, *fn, *fd, *gn, *gd, *hn, *hd, *xn, *xd;
    double r = 0.0; srmech_status_t st;
    assert(b != NULL && o != NULL);
    assert(sn != NULL && sd != NULL);
    if (!cr_q_of_dbl(b, coef, &xn, &xd)) { return SRMECH_ERR_NOT_IMPL; }
    st = cr_q_apply(b, '*', xn, xd, sn, sd, &pn, &pd);       /* coef * s   */
    if (st != SRMECH_OK) { return st; }
    if (!cr_q_of_dbl(b, om, &xn, &xd)) { return SRMECH_ERR_NOT_IMPL; }
    st = cr_q_apply(b, '+', xn, xd, pn, pd, &fn, &fd);       /* om + .     */
    if (st != SRMECH_OK) { return st; }
    if (!cr_q_of_dbl(b, dt, &xn, &xd)) { return SRMECH_ERR_NOT_IMPL; }
    st = cr_q_apply(b, '*', xn, xd, fn, fd, &gn, &gd);       /* dt * .     */
    if (st != SRMECH_OK) { return st; }
    if (!cr_q_of_dbl(b, theta_i, &xn, &xd)) { return SRMECH_ERR_NOT_IMPL; }
    st = cr_q_apply(b, '+', xn, xd, gn, gd, &hn, &hd);       /* theta_i + .*/
    if (st != SRMECH_OK) { return st; }
    if (!cr_q_dyadic_dbl(hn, hd, &r)) { return SRMECH_ERR_NOT_IMPL; }
    *o = cr_dbl(b, r);
    return (*o == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* kuramoto_out_simple(theta, omega, i, s, inv_n, dt). */
static srmech_status_t cr_op_kur_out_simple(cr_ctx_t *c, const srmech_json_value_t *a,
                                            cr_value_t **o)
{
    cr_value_t *th, *om, *vi, *sv; int64_t i;
    double theta_i, om_i, inv_n = 0.0, dt = 0.0, s_d;
    assert(c != NULL && a != NULL);
    assert(o != NULL);
    th = cr_arg(c, a, "theta"); om = cr_arg(c, a, "omega");
    vi = cr_arg(c, a, "i"); sv = cr_arg(c, a, "s");
    if (th == NULL || om == NULL || vi == NULL || sv == NULL) {
        return SRMECH_ERR_NOT_IMPL;
    }
    if (!cr_arg_dbl(c, a, "inv_n", &inv_n) || !cr_arg_dbl(c, a, "dt", &dt)) {
        return SRMECH_ERR_NOT_IMPL;
    }
    if (!cr_as_i64(vi, &i)) { return SRMECH_ERR_NOT_IMPL; }
    if (!cr_list_at_dbl(th, i, &theta_i) || !cr_list_at_dbl(om, i, &om_i)) {
        return SRMECH_ERR_NOT_IMPL;
    }
    if (sv->kind == CR_RATIONAL && sv->num != NULL && sv->den != NULL) {
        return cr_kur_combine_q(c->b, theta_i, om_i, inv_n, dt,
                                sv->num, sv->den, o);
    }
    /* a float (or int) s: Python's whole expression stays in float ops */
    if (sv->kind == CR_DBL) { s_d = sv->d; }
    else {
        int64_t s_i;
        if (!cr_as_i64(sv, &s_i)) { return SRMECH_ERR_NOT_IMPL; }
        if (s_i > (INT64_C(1) << 53) || s_i < -(INT64_C(1) << 53)) {
            return SRMECH_ERR_NOT_IMPL;
        }
        s_d = (double)s_i;
    }
    *o = cr_dbl(c->b, theta_i + dt * (om_i + inv_n * s_d));
    return (*o == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* kuramoto_gen_out(theta, omega, i, s, psi, ps, dt) — the general-path
 * combine: f = om + s [+ pᵢ·sin(ψᵢ − θᵢ)]; θᵢ + dt·f; one float() collapse. */
static srmech_status_t cr_op_kur_gen_out(cr_ctx_t *c, const srmech_json_value_t *a,
                                         cr_value_t **o)
{
    cr_value_t *th, *om, *vi, *sv, *psi, *ps, *qterm; int64_t i, q61 = 0;
    double theta_i, om_i, dt = 0.0, p_i;
    srmech_bigint_t *fn, *fd, *tn, *td, *xn, *xd; srmech_status_t st;
    assert(c != NULL && a != NULL);
    assert(o != NULL);
    th = cr_arg(c, a, "theta"); om = cr_arg(c, a, "omega");
    vi = cr_arg(c, a, "i"); sv = cr_arg(c, a, "s");
    psi = cr_arg(c, a, "psi"); ps = cr_arg(c, a, "ps");
    if (th == NULL || om == NULL || vi == NULL || sv == NULL || psi == NULL ||
        ps == NULL) { return SRMECH_ERR_NOT_IMPL; }
    if (!cr_arg_dbl(c, a, "dt", &dt) || !cr_as_i64(vi, &i)) {
        return SRMECH_ERR_NOT_IMPL;
    }
    if (!cr_list_at_dbl(th, i, &theta_i) || !cr_list_at_dbl(om, i, &om_i)) {
        return SRMECH_ERR_NOT_IMPL;
    }
    if (sv->kind != CR_RATIONAL || sv->num == NULL || sv->den == NULL) {
        return SRMECH_ERR_NOT_IMPL;      /* s is the fold's exact-ℚ output */
    }
    if (!cr_q_of_dbl(c->b, om_i, &xn, &xd)) { return SRMECH_ERR_NOT_IMPL; }
    st = cr_q_apply(c->b, '+', xn, xd, sv->num, sv->den, &fn, &fd);
    if (st != SRMECH_OK) { return st; }
    if (psi->kind != CR_NONE) {                      /* the pinning branch */
        double psi_i;
        if (ps->kind == CR_LIST) {
            if (!cr_list_at_dbl(ps, i, &p_i)) { return SRMECH_ERR_NOT_IMPL; }
        } else if (!cr_arg_dbl(c, a, "ps", &p_i)) { return SRMECH_ERR_NOT_IMPL; }
        if (!cr_list_at_dbl(psi, i, &psi_i)) { return SRMECH_ERR_NOT_IMPL; }
        if (srmech_sin_q61(psi_i - theta_i, &q61) != SRMECH_OK) {
            return SRMECH_ERR_NOT_IMPL;
        }
        qterm = cr_q61_rat(c->b, q61);
        if (qterm == NULL) { return SRMECH_ERR_OVERFLOW; }
        st = cr_q_scale(c->b, p_i, qterm, &tn, &td);     /* p_i * sin(...) */
        if (st != SRMECH_OK) { return st; }
        st = cr_q_apply(c->b, '+', fn, fd, tn, td, &xn, &xd);
        if (st != SRMECH_OK) { return st; }
        fn = xn; fd = xd;
    }
    /* theta_i + dt * f, exactly, with coef 1.0 folding the dt in: */
    return cr_kur_combine_q(c->b, theta_i, 0.0, dt, 1.0, fn, fd, o);
}

/* ------------------------------------------------------------------
 * THE HYPERCOMPLEX-DFT STEP OPS (rc452 Phase 3) — the per-(k, m) atoms of
 * quaternion_dft.toml / octonion_dft.toml. Each summand delegates to the
 * STEP-granular exports the Python op itself composes
 * (srmech_quaternion_twiddle + srmech_quaternion_{left,right}_mult;
 * srmech_octonion_twiddle + srmech_loop_{left,right}_op_f64) — the
 * best_rational precedent. The fused whole-transform symbols
 * (srmech_quaternion_dft / srmech_octonion_dft) are NOT referenced here:
 * they are the coarse bypass the step-mutation witness refuses.
 * ------------------------------------------------------------------ */

/* CR_STR equality against a C literal. */
static int cr_str_is(const cr_value_t *v, const char *want)
{
    size_t n;
    assert(want != NULL);
    assert(want[0] != '\0');
    if (v == NULL || v->kind != CR_STR || v->s == NULL) { return 0; }
    n = strlen(want);
    return v->slen == (uint32_t)n && memcmp(v->s, want, n) == 0;
}

/* as_quat4(v): coerce one QDFT sample to 4 doubles (8-vec tail must be 0). */
static srmech_status_t cr_op_as_quat4(cr_ctx_t *c, const srmech_json_value_t *a,
                                      cr_value_t **o)
{
    cr_value_t *v; double buf[8]; size_t n = 0u, i; double *dv;
    assert(c != NULL && a != NULL);
    assert(o != NULL);
    v = cr_arg(c, a, "v");
    if (v == NULL) { return SRMECH_ERR_NOT_IMPL; }
    dv = cr_as_dvec(c->b, v, &n);
    if (dv == NULL || (n != 4u && n != 8u)) { return SRMECH_ERR_NOT_IMPL; }
    for (i = 0u; i < n; i++) { buf[i] = dv[i]; }
    if (n == 8u) {
        for (i = 4u; i < 8u; i++) {
            if (buf[i] != 0.0) { return SRMECH_ERR_NOT_IMPL; }   /* -> pure raise */
        }
    }
    *o = cr_dvec_value(c->b, buf, 4u);
    return (*o == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* as_oct8(vec): zero-extend a quaternion into ℍ ⊂ 𝕆, pass an octonion through. */
static srmech_status_t cr_op_as_oct8(cr_ctx_t *c, const srmech_json_value_t *a,
                                     cr_value_t **o)
{
    cr_value_t *v; double buf[8]; size_t n = 0u, i; double *dv;
    assert(c != NULL && a != NULL);
    assert(o != NULL);
    v = cr_arg(c, a, "vec");
    if (v == NULL) { return SRMECH_ERR_NOT_IMPL; }
    dv = cr_as_dvec(c->b, v, &n);
    if (dv == NULL || (n != 4u && n != 8u)) { return SRMECH_ERR_NOT_IMPL; }
    for (i = 0u; i < 8u; i++) { buf[i] = (i < n) ? dv[i] : 0.0; }
    *o = cr_dvec_value(c->b, buf, 8u);
    return (*o == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* 1/float(√x) via the SAME Q61 cascade srmech.math.rational.sqrt projects:
 * √x = root·2^p exactly (srmech_sqrt_q61), float() of that exact rational
 * (dyadic — correctly rounded), then one IEEE divide. 0 -> decline. */
static int cr_inv_sqrt(cr_bump_t *b, double x, double *out)
{
    int64_t root = 0, p = 0; srmech_bigint_t *num, *den; double f = 0.0;
    assert(b != NULL);
    assert(out != NULL);
    if (srmech_sqrt_q61(x, &root, &p) != SRMECH_OK || root <= 0) { return 0; }
    if (p >= 0) {
        if (p > 2048) { return 0; }
        num = cr_bi_u64_shl(b, (uint64_t)root, (uint32_t)p);
        den = cr_bi_u64_shl(b, 1u, 0u);
    } else {
        if (p < -2048) { return 0; }
        num = cr_bi_u64_shl(b, (uint64_t)root, 0u);
        den = cr_bi_u64_shl(b, 1u, (uint32_t)(-p));
    }
    if (num == NULL || den == NULL) { return 0; }
    if (!cr_q_dyadic_dbl(num, den, &f) || f == 0.0) { return 0; }
    *out = 1.0 / f;
    return 1;
}

/* qdft_resolve_mu(mu_axis): the NAMED unit axes ('i'/'j'/'k'/'ijk'; for ℍ
 * 'diagonal' IS 'ijk'). A general vector axis declines to pure (its
 * normalisation walks the Class-N sqrt over an arbitrary radicand). */
static srmech_status_t cr_op_qdft_resolve_mu(cr_ctx_t *c, const srmech_json_value_t *a,
                                             cr_value_t **o)
{
    cr_value_t *ax; double mu[4] = {0.0, 0.0, 0.0, 0.0}; double s3 = 0.0;
    assert(c != NULL && a != NULL);
    assert(o != NULL);
    ax = cr_arg(c, a, "mu_axis");
    if (ax == NULL || ax->kind != CR_STR) { return SRMECH_ERR_NOT_IMPL; }
    if (cr_str_is(ax, "i"))      { mu[1] = 1.0; }
    else if (cr_str_is(ax, "j")) { mu[2] = 1.0; }
    else if (cr_str_is(ax, "k")) { mu[3] = 1.0; }
    else if (cr_str_is(ax, "ijk") || cr_str_is(ax, "diagonal")) {
        if (!cr_inv_sqrt(c->b, 3.0, &s3)) { return SRMECH_ERR_NOT_IMPL; }
        mu[1] = s3; mu[2] = s3; mu[3] = s3;
    }
    else { return SRMECH_ERR_NOT_IMPL; }         /* unknown -> pure raises */
    *o = cr_dvec_value(c->b, mu, 4u);
    return (*o == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* odft_resolve_mu(mu_axis): the NAMED octonion axes ('i'/'j'/'k' alias
 * 'e1'..'e3', 'e4'..'e7', 'ijk', 'diagonal'). General vectors decline. */
static srmech_status_t cr_op_odft_resolve_mu(cr_ctx_t *c, const srmech_json_value_t *a,
                                             cr_value_t **o)
{
    cr_value_t *ax; double mu[8] = {0.0}; double s = 0.0; uint32_t i;
    assert(c != NULL && a != NULL);
    assert(o != NULL);
    ax = cr_arg(c, a, "mu_axis");
    if (ax == NULL || ax->kind != CR_STR) { return SRMECH_ERR_NOT_IMPL; }
    if (cr_str_is(ax, "i") || cr_str_is(ax, "e1"))      { mu[1] = 1.0; }
    else if (cr_str_is(ax, "j") || cr_str_is(ax, "e2")) { mu[2] = 1.0; }
    else if (cr_str_is(ax, "k") || cr_str_is(ax, "e3")) { mu[3] = 1.0; }
    else if (cr_str_is(ax, "e4")) { mu[4] = 1.0; }
    else if (cr_str_is(ax, "e5")) { mu[5] = 1.0; }
    else if (cr_str_is(ax, "e6")) { mu[6] = 1.0; }
    else if (cr_str_is(ax, "e7")) { mu[7] = 1.0; }
    else if (cr_str_is(ax, "ijk")) {
        if (!cr_inv_sqrt(c->b, 3.0, &s)) { return SRMECH_ERR_NOT_IMPL; }
        mu[1] = s; mu[2] = s; mu[3] = s;
    }
    else if (cr_str_is(ax, "diagonal")) {
        if (!cr_inv_sqrt(c->b, 7.0, &s)) { return SRMECH_ERR_NOT_IMPL; }
        for (i = 1u; i < 8u; i++) { mu[i] = s; }
    }
    else { return SRMECH_ERR_NOT_IMPL; }
    *o = cr_dvec_value(c->b, mu, 8u);
    return (*o == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* dft_sigma(inverse): +1 inverse, −1 forward (the Class-C which-way). */
static srmech_status_t cr_op_dft_sigma(cr_ctx_t *c, const srmech_json_value_t *a,
                                       cr_value_t **o)
{
    cr_value_t *inv; int64_t v = 0;
    assert(c != NULL && a != NULL);
    assert(o != NULL);
    inv = cr_arg(c, a, "inverse");
    if (inv == NULL || !cr_as_i64(inv, &v)) { return SRMECH_ERR_NOT_IMPL; }
    *o = cr_int_i64(c->b, (v != 0) ? 1 : -1);
    return (*o == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* dft_scale(inverse, n): 1/n on the inverse (n > 0), else 1.0. */
static srmech_status_t cr_op_dft_scale(cr_ctx_t *c, const srmech_json_value_t *a,
                                       cr_value_t **o)
{
    cr_value_t *inv, *nv; int64_t v = 0, n = 0;
    assert(c != NULL && a != NULL);
    assert(o != NULL);
    inv = cr_arg(c, a, "inverse"); nv = cr_arg(c, a, "n");
    if (inv == NULL || nv == NULL) { return SRMECH_ERR_NOT_IMPL; }
    if (!cr_as_i64(inv, &v) || !cr_as_i64(nv, &n)) { return SRMECH_ERR_NOT_IMPL; }
    if (n > (INT64_C(1) << 53)) { return SRMECH_ERR_NOT_IMPL; }
    *o = cr_dbl(c->b, (v != 0 && n > 0) ? (1.0 / (double)n) : 1.0);
    return (*o == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* Shared summand argument unpack: xs[m] -> x (dim doubles), k/m/n/sigma
 * validated to the twiddle exports' uint32/±1 wire, mu -> unit dim-vector. */
static int cr_dft_args(cr_ctx_t *c, const srmech_json_value_t *a, uint32_t dim,
                       const char *mu_key, double *x, double *mu,
                       uint32_t *k, uint32_t *m, uint32_t *n, int32_t *sigma)
{
    cr_value_t *xs, *vk, *vm, *vn, *vs, *vmu; int64_t ik, im, in_, is;
    double *dv; size_t nn = 0u; uint32_t i;
    assert(c != NULL && a != NULL);
    assert(x != NULL && mu != NULL);
    xs = cr_arg(c, a, "xs"); vk = cr_arg(c, a, "k"); vm = cr_arg(c, a, "m");
    vn = cr_arg(c, a, "n"); vs = cr_arg(c, a, "sigma"); vmu = cr_arg(c, a, mu_key);
    if (xs == NULL || vk == NULL || vm == NULL || vn == NULL || vs == NULL ||
        vmu == NULL || xs->kind != CR_LIST) { return 0; }
    if (!cr_as_i64(vk, &ik) || !cr_as_i64(vm, &im) || !cr_as_i64(vn, &in_) ||
        !cr_as_i64(vs, &is)) { return 0; }
    if (ik < 0 || im < 0 || in_ < 1 || ik >= INT64_C(0x100000000) ||
        im >= INT64_C(0x100000000) || in_ >= INT64_C(0x100000000)) { return 0; }
    if (is != 1 && is != -1) { return 0; }
    if ((uint64_t)im >= (uint64_t)xs->n) { return 0; }
    dv = cr_as_dvec(c->b, xs->items[im], &nn);
    if (dv == NULL || nn != (size_t)dim) { return 0; }
    for (i = 0u; i < dim; i++) { x[i] = dv[i]; }
    dv = cr_as_dvec(c->b, vmu, &nn);
    if (dv == NULL || nn != (size_t)dim) { return 0; }
    for (i = 0u; i < dim; i++) { mu[i] = dv[i]; }
    *k = (uint32_t)ik; *m = (uint32_t)im; *n = (uint32_t)in_;
    *sigma = (int32_t)is;
    return 1;
}

/* rows(dim×dim) · v — the row-dot accumulated LEFT-TO-RIGHT in a scalar t:
 * the exact float-op order of the Python summand ops (parity, not tolerance). */
static void cr_matvec_lr(const double *rows, const double *v, uint32_t dim,
                         double *out)
{
    uint32_t i, cN;
    assert(rows != NULL && v != NULL);
    assert(out != NULL);
    for (i = 0u; i < dim; i++) {
        double t = 0.0;
        for (cN = 0u; cN < dim; cN++) { t += rows[i * dim + cN] * v[cN]; }
        out[i] = t;
    }
}

/* qdft_summand(xs, k, m, n, left, sigma, mu_hat) -> W·x[m] or x[m]·W. */
static srmech_status_t cr_op_qdft_summand(cr_ctx_t *c, const srmech_json_value_t *a,
                                          cr_value_t **o)
{
    double x[4], mu[4], w[4], rows[16], r[4]; uint32_t k, m, n; int32_t sigma;
    cr_value_t *vl; int64_t left = 0; srmech_status_t st;
    assert(c != NULL && a != NULL);
    assert(o != NULL);
    if (!cr_dft_args(c, a, 4u, "mu_hat", x, mu, &k, &m, &n, &sigma)) {
        return SRMECH_ERR_NOT_IMPL;
    }
    vl = cr_arg(c, a, "left");
    if (vl == NULL || !cr_as_i64(vl, &left)) { return SRMECH_ERR_NOT_IMPL; }
    st = srmech_quaternion_twiddle(k, m, n, sigma, mu, 4u, w);
    if (st != SRMECH_OK) { return SRMECH_ERR_NOT_IMPL; }
    st = (left != 0) ? srmech_quaternion_left_mult(w, 4u, rows)
                     : srmech_quaternion_right_mult(w, 4u, rows);
    if (st != SRMECH_OK) { return SRMECH_ERR_NOT_IMPL; }
    cr_matvec_lr(rows, x, 4u, r);
    *o = cr_dvec_value(c->b, r, 4u);
    return (*o == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* Apply L_q (side != 0) or R_q (side == 0) to `v` in place of `out` — one
 * octonion operator build + the left-to-right matvec (the shared inner move
 * of every ODFT summand form). 1 on success. */
static int cr_oct_apply(const double *q, int side, const double *v, double *out)
{
    double rows[64]; srmech_status_t st;
    assert(q != NULL && v != NULL);
    assert(out != NULL);
    st = side ? srmech_loop_left_op_f64(q, 8u, rows)
              : srmech_loop_right_op_f64(q, 8u, rows);
    if (st != SRMECH_OK) { return 0; }
    cr_matvec_lr(rows, v, 8u, out);
    return 1;
}

/* odft_summand(xs, k, m, n, form, bracketing, sigma, mu_hat, mu_r_hat) —
 * the one-sided single product, or the two-sided product in the DECLARED
 * F378 association order. */
static srmech_status_t cr_op_odft_summand(cr_ctx_t *c, const srmech_json_value_t *a,
                                          cr_value_t **o)
{
    double x[8], mu[8], mur[8], w[8], t1[8], inner[8], r[8];
    uint32_t k, m, n; int32_t sigma; cr_value_t *fv, *bv, *vmr;
    int left_assoc; size_t nn = 0u; double *dv; uint32_t i; srmech_status_t st;
    assert(c != NULL && a != NULL);
    assert(o != NULL);
    if (!cr_dft_args(c, a, 8u, "mu_hat", x, mu, &k, &m, &n, &sigma)) {
        return SRMECH_ERR_NOT_IMPL;
    }
    fv = cr_arg(c, a, "form"); bv = cr_arg(c, a, "bracketing");
    if (fv == NULL || bv == NULL) { return SRMECH_ERR_NOT_IMPL; }
    st = srmech_octonion_twiddle(k, m, n, sigma, mu, 8u, w);
    if (st != SRMECH_OK) { return SRMECH_ERR_NOT_IMPL; }
    if (cr_str_is(fv, "left")) {
        if (!cr_oct_apply(w, 1, x, r)) { return SRMECH_ERR_NOT_IMPL; }
    } else if (cr_str_is(fv, "right")) {
        if (!cr_oct_apply(w, 0, x, r)) { return SRMECH_ERR_NOT_IMPL; }
    } else if (cr_str_is(fv, "two_sided")) {
        left_assoc = cr_str_is(bv, "left_associated");
        if (!left_assoc && !cr_str_is(bv, "right_associated")) {
            return SRMECH_ERR_NOT_IMPL;
        }
        vmr = cr_arg(c, a, "mu_r_hat");
        dv = (vmr == NULL) ? NULL : cr_as_dvec(c->b, vmr, &nn);
        if (dv == NULL || nn != 8u) { return SRMECH_ERR_NOT_IMPL; }
        for (i = 0u; i < 8u; i++) { mur[i] = dv[i]; }
        st = srmech_octonion_twiddle(k, m, n, sigma, mur, 8u, t1);
        if (st != SRMECH_OK) { return SRMECH_ERR_NOT_IMPL; }
        if (left_assoc) {                          /* (W_l · x) · W_r */
            if (!cr_oct_apply(w, 1, x, inner) ||
                !cr_oct_apply(t1, 0, inner, r)) { return SRMECH_ERR_NOT_IMPL; }
        } else {                                   /* W_l · (x · W_r) */
            if (!cr_oct_apply(t1, 0, x, inner) ||
                !cr_oct_apply(w, 1, inner, r)) { return SRMECH_ERR_NOT_IMPL; }
        }
    } else { return SRMECH_ERR_NOT_IMPL; }
    *o = cr_dvec_value(c->b, r, 8u);
    return (*o == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* seq_get(seq, i): dynamic element access — the degenerate catalog lookup.
 * The returned carrier ALIASES the element (step outputs are write-once, so
 * an alias is exact); a negative index declines to pure, which answers
 * Python's wrap semantics. */
static srmech_status_t cr_op_seq_get(cr_ctx_t *c, const srmech_json_value_t *a,
                                     cr_value_t **o)
{
    cr_value_t *seq, *vi; int64_t i;
    assert(c != NULL && a != NULL);
    assert(o != NULL);
    seq = cr_arg(c, a, "seq"); vi = cr_arg(c, a, "i");
    if (seq == NULL || vi == NULL || seq->kind != CR_LIST) {
        return SRMECH_ERR_NOT_IMPL;
    }
    if (!cr_as_i64(vi, &i) || i < 0 || (uint64_t)i >= (uint64_t)seq->n) {
        return SRMECH_ERR_NOT_IMPL;
    }
    if (seq->items[i] == NULL) { return SRMECH_ERR_NOT_IMPL; }
    *o = seq->items[i];
    return SRMECH_OK;
}

/* vec_scale(v, s): elementwise v[i] * s (the DFT output scale). */
static srmech_status_t cr_op_vec_scale(cr_ctx_t *c, const srmech_json_value_t *a,
                                       cr_value_t **o)
{
    cr_value_t *v; double s = 0.0, *dv, *r; size_t n = 0u, i;
    assert(c != NULL && a != NULL);
    assert(o != NULL);
    v = cr_arg(c, a, "v");
    if (v == NULL || !cr_arg_dbl(c, a, "s", &s)) { return SRMECH_ERR_NOT_IMPL; }
    dv = cr_as_dvec(c->b, v, &n);
    if (dv == NULL) { return SRMECH_ERR_NOT_IMPL; }
    r = (double *)cr_carve(c->b, n * sizeof(double) + sizeof(double));
    if (r == NULL) { return SRMECH_ERR_OVERFLOW; }
    for (i = 0u; i < n; i++) { r[i] = dv[i] * s; }
    *o = cr_dvec_value(c->b, r, n);
    return (*o == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* ------------------------------------------------------------------
 * THE STRING / BYTES LEAVES (rc452, gh #1653 — wave C: the klein4_from_one
 * chain's own steps). Classes F / B / A at STEP granularity.
 *
 * ⚠️ THE FUSED SYMBOL IS NOT CALLED. `srmech_klein4_from_one` exists and
 * computes the whole coupling address; the no-coarse source gate
 * (tests/test_no_coarse_cascade_symbol_in_the_interpreter_rc451.py) derives
 * it into its pinned population the moment the chain runs, so this TU must
 * reach the address the way the DESCRIPTOR says: render -> utf8 -> sha256 ->
 * counter block -> crumb arithmetic, each op its own dispatch arm. The one
 * compiled symbol these arms share with the fused path is srmech_sha256_hex —
 * the STEP-granular Class-A export the Python op itself composes.
 *
 * str vs bytes: the carrier flag `is_bytes` (see cr_value_t). Each arm below
 * states which side of that boundary it requires and DECLINES the other —
 * Python RAISES on the same misuse (bytes has no .encode; hashlib refuses a
 * str), and co-equal projections must agree on what they refuse.
 * ------------------------------------------------------------------ */

/* A CR_STR carrier aliasing [s, s+n) (arena or parsed-JSON text — both
 * outlive the run). `is_bytes` says which side of the boundary it is. */
static cr_value_t *cr_str_value(cr_bump_t *b, const char *s, uint32_t n,
                                int is_bytes)
{
    cr_value_t *v;
    assert(b != NULL);
    assert(s != NULL || n == 0u);
    v = cr_new_value(b, CR_STR);
    if (v == NULL) { return NULL; }
    v->s = s; v->slen = n; v->is_bytes = (is_bytes != 0);
    return v;
}

/* utf8_encode(text) -> bytes. Class B: the str -> bytes framing boundary.
 * The carrier already holds UTF-8 (srmech_json decodes escapes to UTF-8), so
 * the encode is byte-IDENTITY and only the TYPE moves. A bytes input
 * declines: Python's bytes has no .encode, so the pure path raises. */
static srmech_status_t cr_op_utf8_encode(cr_ctx_t *c, const srmech_json_value_t *a,
                                         cr_value_t **o)
{
    cr_value_t *t;
    assert(c != NULL && a != NULL);
    assert(o != NULL);
    t = cr_arg(c, a, "text");
    if (t == NULL || t->kind != CR_STR || t->is_bytes) { return SRMECH_ERR_NOT_IMPL; }
    *o = cr_str_value(c->b, t->s, t->slen, 1);
    return (*o == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* sha256_bytes(data) -> str. Class A: the content digest, returned as the
 * 64-char lowercase hex STRING the Python op returns (its `_bytes` suffix
 * names the INPUT type). A str input declines — hashlib refuses a str, so
 * the pure path raises the documented TypeError. */
static srmech_status_t cr_op_sha256_bytes(cr_ctx_t *c, const srmech_json_value_t *a,
                                          cr_value_t **o)
{
    cr_value_t *d; char *hex; const uint8_t *p;
    assert(c != NULL && a != NULL);
    assert(o != NULL);
    d = cr_arg(c, a, "data");
    if (d == NULL || d->kind != CR_STR || !d->is_bytes) { return SRMECH_ERR_NOT_IMPL; }
    hex = (char *)cr_carve(c->b, 65u);
    if (hex == NULL) { return SRMECH_ERR_OVERFLOW; }
    p = (const uint8_t *)((d->s != NULL) ? d->s : "");
    if (srmech_sha256_hex(p, (size_t)d->slen, hex) != SRMECH_OK) {
        return SRMECH_ERR_BAD_INPUT;
    }
    *o = cr_str_value(c->b, hex, 64u, 0);
    return (*o == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* str_concat(prefix, text) -> str. Class F: the degenerate template. Both
 * operands must be str — Python's str + bytes raises TypeError. */
static srmech_status_t cr_op_str_concat(cr_ctx_t *c, const srmech_json_value_t *a,
                                        cr_value_t **o)
{
    cr_value_t *p, *t; char *buf;
    assert(c != NULL && a != NULL);
    assert(o != NULL);
    p = cr_arg(c, a, "prefix"); t = cr_arg(c, a, "text");
    if (p == NULL || t == NULL || p->kind != CR_STR || t->kind != CR_STR ||
        p->is_bytes || t->is_bytes) { return SRMECH_ERR_NOT_IMPL; }
    buf = (char *)cr_carve(c->b, (size_t)p->slen + (size_t)t->slen + 1u);
    if (buf == NULL) { return SRMECH_ERR_OVERFLOW; }
    if (p->slen > 0u) { memcpy(buf, p->s, p->slen); }
    if (t->slen > 0u) { memcpy(buf + p->slen, t->s, t->slen); }
    *o = cr_str_value(c->b, buf, p->slen + t->slen, 0);
    return (*o == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* byte_slice(data, start, stop) -> bytes: Python's data[start:stop], the
 * slice rule transcribed WHOLE — a negative index counts from the end, both
 * bounds clamp to [0, len], and stop <= start is the EMPTY bytes, never an
 * error. The result aliases the parent buffer (the arena persists). */
static srmech_status_t cr_op_byte_slice(cr_ctx_t *c, const srmech_json_value_t *a,
                                        cr_value_t **o)
{
    cr_value_t *d, *vs, *ve; int64_t start = 0, stop = 0, len;
    assert(c != NULL && a != NULL);
    assert(o != NULL);
    d = cr_arg(c, a, "data");
    if (d == NULL || d->kind != CR_STR || !d->is_bytes) { return SRMECH_ERR_NOT_IMPL; }
    vs = cr_arg(c, a, "start"); ve = cr_arg(c, a, "stop");
    if (vs == NULL || ve == NULL ||
        !cr_as_i64(vs, &start) || !cr_as_i64(ve, &stop)) {
        return SRMECH_ERR_NOT_IMPL;
    }
    len = (int64_t)d->slen;
    if (start < 0) { start += len; }
    if (start < 0) { start = 0; }
    if (start > len) { start = len; }
    if (stop < 0) { stop += len; }
    if (stop < 0) { stop = 0; }
    if (stop > len) { stop = len; }
    if (stop < start) { stop = start; }
    /* NULL + 0 is formally UB; an empty parent stays the NULL/0 carrier. */
    *o = cr_str_value(c->b, (d->s != NULL) ? d->s + start : NULL,
                      (uint32_t)(stop - start), 1);
    return (*o == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* int_parse_le(data) -> int: int.from_bytes(data, "little"), unsigned. The
 * little-endian byte order IS the 32-bit limb order, so the bigint fills
 * directly — limb k is bytes [4k, 4k+4), missing high bytes zero. The empty
 * bytes is the int 0, exactly as in Python. */
static srmech_status_t cr_op_int_parse_le(cr_ctx_t *c, const srmech_json_value_t *a,
                                          cr_value_t **o)
{
    cr_value_t *d, *ov; uint32_t nl, i;
    assert(c != NULL && a != NULL);
    assert(o != NULL);
    d = cr_arg(c, a, "data");
    if (d == NULL || d->kind != CR_STR || !d->is_bytes) { return SRMECH_ERR_NOT_IMPL; }
    ov = cr_new_value(c->b, CR_INT);
    if (ov == NULL) { return SRMECH_ERR_OVERFLOW; }
    nl = d->slen / 4u + 1u;
    ov->num = cr_new_bigint(c->b, nl);
    if (ov->num == NULL) { return SRMECH_ERR_OVERFLOW; }
    for (i = 0u; i < nl; i++) { ov->num->limbs[i] = 0u; }
    for (i = 0u; i < d->slen; i++) {
        ov->num->limbs[i / 4u] |=
            ((uint32_t)(unsigned char)d->s[i]) << (8u * (i % 4u));
    }
    while (nl > 0u && ov->num->limbs[nl - 1u] == 0u) { nl--; }
    ov->num->n = nl;
    ov->num->sign = (nl == 0u) ? 0 : 1;
    *o = ov;
    return SRMECH_OK;
}

/* ---- render_template: the Class-F {key} substitution, three pieces ---- */

/* The length of the {placeholder} starting at tmpl[i] (the opening brace),
 * or 0 when no placeholder starts there; writes the key's span (braces
 * excluded) to *k / *klen. The charclass is descriptor.py's
 * _TEMPLATE_PATTERN, [A-Za-z0-9_.:%\-+ ], transcribed. Greedy-scan-then-
 * check-'}' is EQUIVALENT to the regex here because '}' is not in the class,
 * so no shorter run could match either — which is why literal JSON braces
 * (klein4_from_one's preimage template) pass through untouched, exactly as
 * they do in Python. */
static uint32_t cr_tpl_span(const char *tmpl, uint32_t n, uint32_t i,
                            const char **k, uint32_t *klen)
{
    uint32_t j = i + 1u;
    assert(tmpl != NULL && k != NULL);
    assert(klen != NULL && i < n);
    if (tmpl[i] != '{') { return 0u; }
    while (j < n) {
        char ch = tmpl[j];
        int in_class = (ch >= 'a' && ch <= 'z') || (ch >= 'A' && ch <= 'Z') ||
                       (ch >= '0' && ch <= '9') || ch == '_' || ch == '.' ||
                       ch == ':' || ch == '%' || ch == '-' || ch == '+' ||
                       ch == ' ';
        if (!in_class) { break; }
        j++;
    }
    if (j == i + 1u || j >= n || tmpl[j] != '}') { return 0u; }
    *k = tmpl + i + 1u; *klen = j - (i + 1u);
    return (j - i) + 1u;
}

/* Render a CR_INT's i64 as decimal text in the arena (str(int); a wider
 * integer declines one level up). Sign rides as a rendered '-' — the
 * Class-K/Class-C split, never an ALU abs(): the magnitude is read
 * two's-complement-safely and the sign re-applied as a character. */
static const char *cr_i64_text(cr_bump_t *b, int64_t v, uint32_t *out_len)
{
    char tmp[24]; uint32_t n = 0u, i; char *dst; uint64_t mag;
    assert(b != NULL);
    assert(out_len != NULL);
    if (v < 0) { mag = (uint64_t)(-(v + 1)) + 1u; } else { mag = (uint64_t)v; }
    do {
        tmp[n++] = (char)('0' + (char)(mag % 10u));
        mag /= 10u;
    } while (mag != 0u && n < 21u);
    if (v < 0) { tmp[n++] = '-'; }
    dst = (char *)cr_carve(b, n);
    if (dst == NULL) { return NULL; }
    for (i = 0u; i < n; i++) { dst[i] = tmp[n - 1u - i]; }
    *out_len = n;
    return dst;
}

#define CR_TPL_MAX_KEYS 16u

/* One resolved context entry, rendered to text. */
typedef struct {
    const char *k; uint32_t kl;
    const char *v; uint32_t vl;
} cr_tpl_pair_t;

/* Resolve the `context` object's members to rendered text pairs: str(value)
 * for the kinds this arm transcribes — a str is itself, an i64 int its
 * decimal, a null "None". Anything else (float / list / rational / a wider
 * int / an unresolvable ref) returns -1 and the chain defers to pure, whose
 * str() is the contract. */
static int32_t cr_tpl_context(cr_ctx_t *c, const srmech_json_value_t *ctx,
                              cr_tpl_pair_t *pairs, uint32_t cap)
{
    uint32_t i;
    assert(c != NULL && pairs != NULL);
    assert(ctx != NULL);
    if (ctx->type != SRMECH_JSON_OBJECT || ctx->u.obj.n > cap) { return -1; }
    for (i = 0u; i < ctx->u.obj.n; i++) {
        cr_value_t *v = cr_resolve_arg(c, ctx->u.obj.vals[i]);
        int64_t iv;
        if (v == NULL) { return -1; }
        pairs[i].k = ctx->u.obj.keys[i];
        pairs[i].kl = (uint32_t)strlen(ctx->u.obj.keys[i]);
        if (v->kind == CR_STR && !v->is_bytes) {
            pairs[i].v = v->s; pairs[i].vl = v->slen;
        } else if (v->kind == CR_INT && cr_as_i64(v, &iv)) {
            pairs[i].v = cr_i64_text(c->b, iv, &pairs[i].vl);
            if (pairs[i].v == NULL) { return -1; }
        } else if (v->kind == CR_NONE) {
            pairs[i].v = "None"; pairs[i].vl = 4u;
        } else {
            return -1;
        }
    }
    return (int32_t)ctx->u.obj.n;
}

/* One pass over the template: substitute placeholders from `pairs`, write
 * into `dst` when non-NULL, return the rendered length. -1 = DECLINE — a
 * {key:fmt} format spec or a dotted key, Python semantics this arm does not
 * transcribe (the pure path's format()/mapping walk is the contract). A key
 * found in no pair renders EMPTY — context.get(part, "") — exactly as
 * descriptor.py's _replace does. */
static int64_t cr_tpl_pass(const char *tmpl, uint32_t n,
                           const cr_tpl_pair_t *pairs, uint32_t np, char *dst)
{
    uint32_t i = 0u; int64_t w = 0;
    assert(tmpl != NULL || n == 0u);
    assert(pairs != NULL || np == 0u);
    while (i < n) {
        const char *k = NULL; uint32_t kl = 0u, span, j;
        span = (tmpl[i] == '{') ? cr_tpl_span(tmpl, n, i, &k, &kl) : 0u;
        if (span == 0u) {
            if (dst != NULL) { dst[w] = tmpl[i]; }
            w++; i++;
            continue;
        }
        for (j = 0u; j < kl; j++) {
            if (k[j] == ':' || k[j] == '.') { return -1; }   /* fmt / dotted */
        }
        for (j = 0u; j < np; j++) {
            if (pairs[j].kl == kl && memcmp(pairs[j].k, k, kl) == 0) {
                if (dst != NULL && pairs[j].vl > 0u) {
                    memcpy(dst + w, pairs[j].v, pairs[j].vl);
                }
                w += (int64_t)pairs[j].vl;
                break;
            }
        }
        i += span;
    }
    return w;
}

/* render_template(template, context) -> str. Class F: the {key} substitution
 * of srmech.amsc.descriptor.render_template, transcribed for the subset the
 * shipped chains use. `context` is the one args value that is itself an
 * OBJECT, so it is read from the raw args node and resolved member-by-member
 * — the flat cr_resolve_arg path deliberately has no object arm, and growing
 * one for every op would widen the whole grammar for a need one op has. */
static srmech_status_t cr_op_render_template(cr_ctx_t *c,
                                             const srmech_json_value_t *a,
                                             cr_value_t **o)
{
    cr_tpl_pair_t pairs[CR_TPL_MAX_KEYS];
    cr_value_t *t; const srmech_json_value_t *ctx; int32_t np; int64_t need;
    char *buf;
    assert(c != NULL && a != NULL);
    assert(o != NULL);
    t = cr_arg(c, a, "template");
    ctx = srmech_json_object_get(a, "context");
    if (t == NULL || t->kind != CR_STR || t->is_bytes || ctx == NULL) {
        return SRMECH_ERR_NOT_IMPL;
    }
    np = cr_tpl_context(c, ctx, pairs, CR_TPL_MAX_KEYS);
    if (np < 0) { return SRMECH_ERR_NOT_IMPL; }
    need = cr_tpl_pass(t->s, t->slen, pairs, (uint32_t)np, NULL);
    if (need < 0) { return SRMECH_ERR_NOT_IMPL; }
    buf = (char *)cr_carve(c->b, (size_t)need + 1u);
    if (buf == NULL) { return SRMECH_ERR_OVERFLOW; }
    if (cr_tpl_pass(t->s, t->slen, pairs, (uint32_t)np, buf) != need) {
        return SRMECH_ERR_INTERNAL;      /* the two passes must agree */
    }
    *o = cr_str_value(c->b, buf, (uint32_t)need, 0);
    return (*o == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* ------------------------------------------------------------------
 * THE HDC / DIGEST LEAVES (rc452, gh #1653 — wave D: the encode_loe_content
 * chain's own steps). Classes A / C / M at STEP granularity.
 *
 * Every arm delegates to exactly ONE compiled export that the PYTHON op of
 * the same name delegates to as well — srmech_sha256_hex (the Class-A core
 * srmech.amsc.format.sha256_raw composes), srmech_mint_vector,
 * srmech_hdc_permute, srmech_hdc_bind. None of the four is a multi-step
 * cascade symbol, so this block adds nothing to the population
 * test_no_coarse_cascade_symbol_in_the_interpreter_rc451.py derives.
 *
 * All four are BYTES-typed on at least one side of their contract. Python
 * RAISES on the wrong side (bytes has no .encode; hdc._check_pair raises on
 * a length mismatch or an empty vector; _validate_D raises on a bad D), so
 * each arm DECLINES there rather than coercing — co-equal projections must
 * refuse the same inputs.
 * ------------------------------------------------------------------ */

/* sha256_raw(data) -> bytes: the RAW 32-byte digest.
 *
 * ⚠️ COMPOSED THE WAY THE PYTHON OP COMPOSES IT — `bytes.fromhex(
 * sha256_bytes(data))` — rather than through srmech_sha256_shani, which also
 * writes 32 raw bytes. Both are bit-exact, so no value-level gate could tell
 * them apart; the reason to prefer this one is that it keeps ONE Class-A core
 * referenced from this TU for BOTH digest arms, so a future divergence between
 * the two entry points cannot reach the chain interpreter through the back
 * door. The hex nibbles are unconditionally [0-9a-f] by srmech_sha256_hex's
 * own contract, which is why the decode below needs no table and no guard. */
static srmech_status_t cr_op_sha256_raw(cr_ctx_t *c, const srmech_json_value_t *a,
                                        cr_value_t **o)
{
    cr_value_t *d; char hex[65]; char *raw; const uint8_t *p; uint32_t i;
    assert(c != NULL && a != NULL);
    assert(o != NULL);
    d = cr_arg(c, a, "data");
    if (d == NULL || d->kind != CR_STR || !d->is_bytes) { return SRMECH_ERR_NOT_IMPL; }
    raw = (char *)cr_carve(c->b, 33u);
    if (raw == NULL) { return SRMECH_ERR_OVERFLOW; }
    p = (const uint8_t *)((d->s != NULL) ? d->s : "");
    if (srmech_sha256_hex(p, (size_t)d->slen, hex) != SRMECH_OK) {
        return SRMECH_ERR_BAD_INPUT;
    }
    for (i = 0u; i < 32u; i++) {
        char hi = hex[2u * i], lo = hex[2u * i + 1u];
        int hv = (hi <= '9') ? (hi - '0') : (hi - 'a' + 10);
        int lv = (lo <= '9') ? (lo - '0') : (lo - 'a' + 10);
        raw[i] = (char)((hv << 4) | lv);
    }
    *o = cr_str_value(c->b, raw, 32u, 1);
    return (*o == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* mint_vector(name, D) -> bytes: the Class-A content-addressed hypervector,
 * SHA-256(name || u64_be(counter)) chained to D/8 bytes.
 *
 * D IS VALIDATED, NOT CLAMPED. srmech.signal_processing._validate_D raises on
 * a non-int, on D < D_MIN (256), on D > D_MAX (65536) and on D % 8 != 0, so
 * every one of those DECLINES here. The three bounds are transcribed from
 * srmech/signal_processing/_paths.py; a clamp would answer where Python
 * raises, which is the co-equal-refusal rule this whole block turns on. */
static srmech_status_t cr_op_mint_vector(cr_ctx_t *c, const srmech_json_value_t *a,
                                         cr_value_t **o)
{
    cr_value_t *nm, *vd; int64_t dbits = 0; char *buf; uint32_t nb;
    assert(c != NULL && a != NULL);
    assert(o != NULL);
    nm = cr_arg(c, a, "name"); vd = cr_arg(c, a, "D");
    if (nm == NULL || nm->kind != CR_STR || nm->is_bytes) { return SRMECH_ERR_NOT_IMPL; }
    if (vd == NULL || !cr_as_i64(vd, &dbits)) { return SRMECH_ERR_NOT_IMPL; }
    if (dbits < 256 || dbits > 65536 || (dbits % 8) != 0) {
        return SRMECH_ERR_NOT_IMPL;
    }
    nb = (uint32_t)(dbits / 8);
    buf = (char *)cr_carve(c->b, (size_t)nb + 1u);
    if (buf == NULL) { return SRMECH_ERR_OVERFLOW; }
    if (srmech_mint_vector((const uint8_t *)((nm->s != NULL) ? nm->s : ""),
                           (size_t)nm->slen, nb, (uint8_t *)buf) != SRMECH_OK) {
        return SRMECH_ERR_BAD_INPUT;
    }
    *o = cr_str_value(c->b, buf, nb, 1);
    return (*o == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* permute(a, rotate_bits) -> bytes: the Class-C cyclic BIT rotation.
 *
 * `rotate_bits` is reduced HERE, with Python's floor-mod sign convention
 * (`eff = rotate_bits % D` is non-negative in Python even for a negative
 * operand), before the int32 hand-off — so a rotation whose magnitude exceeds
 * int32 cannot wrap on the cast. An empty vector declines: hdc.permute raises
 * ValueError on it. */
static srmech_status_t cr_op_hdc_permute(cr_ctx_t *c, const srmech_json_value_t *a,
                                         cr_value_t **o)
{
    cr_value_t *av, *rv; int64_t rot = 0, dbits, eff; char *buf;
    assert(c != NULL && a != NULL);
    assert(o != NULL);
    av = cr_arg(c, a, "a"); rv = cr_arg(c, a, "rotate_bits");
    if (av == NULL || av->kind != CR_STR || !av->is_bytes || av->slen == 0u) {
        return SRMECH_ERR_NOT_IMPL;
    }
    if (rv == NULL || !cr_as_i64(rv, &rot)) { return SRMECH_ERR_NOT_IMPL; }
    dbits = (int64_t)av->slen * 8;
    if (dbits > (int64_t)INT32_MAX) { return SRMECH_ERR_NOT_IMPL; }
    eff = rot % dbits;
    if (eff < 0) { eff += dbits; }       /* Python's % floors; C's truncates */
    buf = (char *)cr_carve(c->b, (size_t)av->slen + 1u);
    if (buf == NULL) { return SRMECH_ERR_OVERFLOW; }
    if (srmech_hdc_permute((const uint8_t *)av->s, av->slen, (int32_t)eff,
                           (uint8_t *)buf) != SRMECH_OK) {
        return SRMECH_ERR_BAD_INPUT;
    }
    *o = cr_str_value(c->b, buf, av->slen, 1);
    return (*o == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* bind(a, b) -> bytes: the Class-M component-wise XOR. hdc._check_pair raises
 * on unequal lengths and on the empty vector, so both DECLINE here. */
static srmech_status_t cr_op_hdc_bind(cr_ctx_t *c, const srmech_json_value_t *a,
                                      cr_value_t **o)
{
    cr_value_t *x, *y; char *buf;
    assert(c != NULL && a != NULL);
    assert(o != NULL);
    x = cr_arg(c, a, "a"); y = cr_arg(c, a, "b");
    if (x == NULL || y == NULL || x->kind != CR_STR || y->kind != CR_STR ||
        !x->is_bytes || !y->is_bytes) { return SRMECH_ERR_NOT_IMPL; }
    if (x->slen != y->slen || x->slen == 0u) { return SRMECH_ERR_NOT_IMPL; }
    buf = (char *)cr_carve(c->b, (size_t)x->slen + 1u);
    if (buf == NULL) { return SRMECH_ERR_OVERFLOW; }
    if (srmech_hdc_bind((const uint8_t *)x->s, (const uint8_t *)y->s,
                        x->slen, (uint8_t *)buf) != SRMECH_OK) {
        return SRMECH_ERR_BAD_INPUT;
    }
    *o = cr_str_value(c->b, buf, x->slen, 1);
    return (*o == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* ---- fold bodies (rc452 Phase 3): the Σ accumulators ---- */

/* A scalar as a double for the fold's float tier: a CR_DBL directly, a
 * CR_INT widened only where the widening is EXACT (|v| <= 2^53 — Python's
 * int-to-float conversion at that magnitude). 0 -> decline. */
static int cr_fold_dbl(const cr_value_t *v, double *out)
{
    int64_t iv;
    assert(v != NULL);
    assert(out != NULL);
    if (v->kind == CR_DBL) { *out = v->d; return 1; }
    if (v->kind == CR_INT && cr_as_i64(v, &iv) &&
        iv <= (INT64_C(1) << 53) && iv >= -(INT64_C(1) << 53)) {
        *out = (double)iv;
        return 1;
    }
    return 0;
}

/* A value as an exact (num, den): a rational ALIASES its own carriers, a
 * finite double promotes via as_integer_ratio, an int rides over den 1.
 * 0 -> the value has no exact rational (non-finite / wrong kind). */
static int cr_val_as_q(cr_bump_t *b, const cr_value_t *v,
                       srmech_bigint_t **n, srmech_bigint_t **d)
{
    assert(b != NULL && v != NULL);
    assert(n != NULL && d != NULL);
    if (v->kind == CR_RATIONAL && v->num != NULL && v->den != NULL) {
        *n = v->num; *d = v->den;
        return 1;
    }
    if (v->kind == CR_DBL) { return cr_q_of_dbl(b, v->d, n, d); }
    if (v->kind == CR_INT && v->num != NULL) {
        *n = v->num; *d = cr_bi_u64_shl(b, 1u, 0u);
        return *d != NULL;
    }
    return 0;
}

/* f64_add(a, b) as a fold body. Python's `a + b` tiering, transcribed:
 * float+float is one IEEE add; int+float widens the int (exact <= 2^53);
 * anything meeting an exact-ℚ operand promotes through as_integer_ratio and
 * adds EXACTLY (Q.__radd__); int+int stays int. A non-finite double cannot
 * promote — the rational arm declines rather than guesses. */
static srmech_status_t cr_b_f64_add(cr_bump_t *b, const cr_value_t *acc,
                                    const cr_value_t *elem, cr_value_t **out)
{
    srmech_bigint_t *n0, *d0, *n1, *d1; cr_value_t *ov; srmech_status_t st;
    assert(b != NULL && out != NULL);
    assert(acc != NULL && elem != NULL);
    if (acc->kind == CR_RATIONAL || elem->kind == CR_RATIONAL) {
        if (!cr_val_as_q(b, acc, &n0, &d0) || !cr_val_as_q(b, elem, &n1, &d1)) {
            return SRMECH_ERR_NOT_IMPL;
        }
        ov = cr_new_value(b, CR_RATIONAL);
        if (ov == NULL) { return SRMECH_ERR_OVERFLOW; }
        st = cr_q_apply(b, '+', n0, d0, n1, d1, &ov->num, &ov->den);
        if (st != SRMECH_OK) { return st; }
        *out = ov;
        return SRMECH_OK;
    }
    if (acc->kind == CR_INT && elem->kind == CR_INT) {
        uint32_t cap = acc->num->n + elem->num->n + 2u;
        ov = cr_new_value(b, CR_INT);
        if (ov == NULL) { return SRMECH_ERR_OVERFLOW; }
        ov->num = cr_new_bigint(b, cap);
        if (ov->num == NULL) { return SRMECH_ERR_OVERFLOW; }
        st = srmech_bigint_add(ov->num, acc->num, elem->num);
        if (st != SRMECH_OK) { return st; }
        *out = ov;
        return SRMECH_OK;
    }
    {   /* float + float, or int widened over the float tier (exact <= 2^53) */
        double x, y;
        if (!cr_fold_dbl(acc, &x) || !cr_fold_dbl(elem, &y)) {
            return SRMECH_ERR_NOT_IMPL;
        }
        *out = cr_dbl(b, x + y);
        return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
    }
}

/* vec_add(a, b) as a fold body: elementwise; equal length or decline (the
 * pure path raises the documented ValueError). Element pairs ride the float
 * tier only — an int-int pair stays int in Python, so it DECLINES here
 * rather than widening to a float Python would not produce. */
static srmech_status_t cr_b_vec_add(cr_bump_t *b, const cr_value_t *acc,
                                    const cr_value_t *elem, cr_value_t **out)
{
    cr_value_t *ov; uint32_t i; double x, y;
    assert(b != NULL && out != NULL);
    assert(acc != NULL && elem != NULL);
    if (acc->kind != CR_LIST || elem->kind != CR_LIST || acc->n != elem->n) {
        return SRMECH_ERR_NOT_IMPL;
    }
    ov = cr_list_of(b, acc->n);
    if (ov == NULL) { return SRMECH_ERR_OVERFLOW; }
    for (i = 0u; i < acc->n; i++) {
        if (acc->items[i] == NULL || elem->items[i] == NULL ||
            (acc->items[i]->kind == CR_INT && elem->items[i]->kind == CR_INT)) {
            return SRMECH_ERR_NOT_IMPL;      /* int+int is int in Python */
        }
        if (!cr_elem_dbl(acc, i, &x) || !cr_elem_dbl(elem, i, &y)) {
            return SRMECH_ERR_NOT_IMPL;
        }
        ov->items[i] = cr_dbl(b, x + y);
        if (ov->items[i] == NULL) { return SRMECH_ERR_OVERFLOW; }
    }
    *out = ov;
    return SRMECH_OK;
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
    uint8_t     dom;   /* cr_dom_t   — which cr_exec_<domain>() runs the op   */
    uint8_t     sub;   /* per-domain — the case label inside that exec        */
    uint8_t     bin;   /* cr_bin_id_t — non-NONE iff the op can fold          */
} CR_OP_REG[55] = {
 /* wave A (rc452) — the autocorrelation CHAIN's own steps */
 { "seq_len",             7u, "srmech.cascade.seq_len",
   CR_DOM_CAS, CR_CAS_SEQ_LEN, CR_BIN_NONE },
 { "correlation_product", 19u, "srmech.cascade.correlation_product",
   CR_DOM_CAS, CR_CAS_CORR_PRODUCT, CR_BIN_NONE },
 { "compensated_sum",    15u, "srmech.cascade.compensated_sum",
   CR_DOM_CAS, CR_CAS_COMPENSATED_SUM, CR_BIN_NONE },
 { "pi_cascade_digits",  17u, "srmech.math.rational.pi_cascade_digits",
   CR_DOM_RAT, CR_RAT_PI, CR_BIN_NONE },
 { "exp_series_truncate", 19u, "srmech.math.rational.exp_series_truncate",
   CR_DOM_RAT, CR_RAT_EXP, CR_BIN_NONE },
 { "sin_series_truncate", 19u, "srmech.math.rational.sin_series_truncate",
   CR_DOM_RAT, CR_RAT_SIN, CR_BIN_NONE },
 { "cos_series_truncate", 19u, "srmech.math.rational.cos_series_truncate",
   CR_DOM_RAT, CR_RAT_COS, CR_BIN_NONE },
 { "log1p_series_truncate", 21u, "srmech.math.rational.log1p_series_truncate",
   CR_DOM_RAT, CR_RAT_LOG1P, CR_BIN_NONE },
 { "atan_series_truncate", 20u, "srmech.math.rational.atan_series_truncate",
   CR_DOM_RAT, CR_RAT_ATAN, CR_BIN_NONE },
 { "rational_pow_uint",  17u, "srmech.math.rational.rational_pow_uint",
   CR_DOM_RAT, CR_RAT_POW, CR_BIN_NONE },
 { "rational_add",       12u, "srmech.math.rational.rational_add",
   CR_DOM_RAT, CR_RAT_ADD, CR_BIN_NONE },
 { "rational_mul",       12u, "srmech.math.rational.rational_mul",
   CR_DOM_RAT, CR_RAT_MUL, CR_BIN_NONE },
 { "rational_div",       12u, "srmech.math.rational.rational_div",
   CR_DOM_RAT, CR_RAT_DIV, CR_BIN_NONE },
 { "gcd",                 3u, "srmech.math.cyclic.gcd",
   CR_DOM_CYC, CR_CYC_GCD, CR_BIN_GCD },
 { "mod_add",             7u, "srmech.math.cyclic.mod_add",
   CR_DOM_CYC, CR_CYC_MOD_ADD, CR_BIN_NONE },
 { "mod_mul",             7u, "srmech.math.cyclic.mod_mul",
   CR_DOM_CYC, CR_CYC_MOD_MUL, CR_BIN_NONE },
 { "mod_mul_wide",       12u, "srmech.math.cyclic.mod_mul_wide",
   CR_DOM_CYC, CR_CYC_MOD_MUL_WIDE, CR_BIN_NONE },
 { "mod_pow",             7u, "srmech.math.cyclic.mod_pow",
   CR_DOM_CYC, CR_CYC_MOD_POW, CR_BIN_NONE },
 { "mod_inv",             7u, "srmech.math.cyclic.mod_inv",
   CR_DOM_CYC, CR_CYC_MOD_INV, CR_BIN_NONE },
 { "pin_slot_at_zero",   16u, "srmech.cascade.pin_slot_at_zero",
   CR_DOM_CAS, CR_CAS_PIN_SLOT, CR_BIN_NONE },
 { "reorient",            8u, "srmech.cascade.reorient",
   CR_DOM_CAS, CR_CAS_REORIENT, CR_BIN_NONE },
 { "chiral_flip",        11u, "srmech.cascade.chiral_flip",
   CR_DOM_CAS, CR_CAS_CHIRAL_FLIP, CR_BIN_NONE },
 { "autocorrelation",    15u, "srmech.cascade.autocorrelation",
   CR_DOM_CAS, CR_CAS_AUTOCORRELATION, CR_BIN_NONE },
 { "dead_band",           9u, "srmech.cascade.dead_band",
   CR_DOM_CAS, CR_CAS_DEAD_BAND, CR_BIN_NONE },
 { "scale_round_half_even", 21u, "srmech.math.rational.scale_round_half_even",
   CR_DOM_RAT, CR_RAT_SCALE_ROUND, CR_BIN_NONE },
 { "best_rational",      13u, "srmech.math.rational.best_rational",
   CR_DOM_RAT, CR_RAT_BEST_RATIONAL, CR_BIN_NONE },
 { "pair",                4u, "srmech.cascade.pair",
   CR_DOM_CAS, CR_CAS_PAIR, CR_BIN_NONE },
 /* wave B (rc452 Phase 3) — the kuramoto_step and hypercomplex-DFT chains'
  * own steps, at STEP granularity (the fused whole-transform symbols are
  * deliberately not referenced from this TU — see the section comments). */
 { "seq_get",             7u, "srmech.cascade.seq_get",
   CR_DOM_CAS, CR_CAS_SEQ_GET, CR_BIN_NONE },
 { "vec_scale",           9u, "srmech.cascade.vec_scale",
   CR_DOM_CAS, CR_CAS_VEC_SCALE, CR_BIN_NONE },
 { "kuramoto_inv_n",     14u, "srmech.cascade.kuramoto_inv_n",
   CR_DOM_CAS, CR_CAS_KUR_INV_N, CR_BIN_NONE },
 { "kuramoto_sin_term",  17u, "srmech.cascade.kuramoto_sin_term",
   CR_DOM_CAS, CR_CAS_KUR_SIN_TERM, CR_BIN_NONE },
 { "kuramoto_out_simple", 19u, "srmech.cascade.kuramoto_out_simple",
   CR_DOM_CAS, CR_CAS_KUR_OUT_SIMPLE, CR_BIN_NONE },
 { "kuramoto_gen_term",  17u, "srmech.cascade.kuramoto_gen_term",
   CR_DOM_CAS, CR_CAS_KUR_GEN_TERM, CR_BIN_NONE },
 { "kuramoto_gen_out",   16u, "srmech.cascade.kuramoto_gen_out",
   CR_DOM_CAS, CR_CAS_KUR_GEN_OUT, CR_BIN_NONE },
 { "as_quat4",            8u, "srmech.cascade.as_quat4",
   CR_DOM_CAS, CR_CAS_AS_QUAT4, CR_BIN_NONE },
 { "as_oct8",             7u, "srmech.cascade.as_oct8",
   CR_DOM_CAS, CR_CAS_AS_OCT8, CR_BIN_NONE },
 { "qdft_resolve_mu",    15u, "srmech.cascade.qdft_resolve_mu",
   CR_DOM_CAS, CR_CAS_QDFT_RESOLVE_MU, CR_BIN_NONE },
 { "odft_resolve_mu",    15u, "srmech.cascade.odft_resolve_mu",
   CR_DOM_CAS, CR_CAS_ODFT_RESOLVE_MU, CR_BIN_NONE },
 { "dft_sigma",           9u, "srmech.cascade.dft_sigma",
   CR_DOM_CAS, CR_CAS_DFT_SIGMA, CR_BIN_NONE },
 { "dft_scale",           9u, "srmech.cascade.dft_scale",
   CR_DOM_CAS, CR_CAS_DFT_SCALE, CR_BIN_NONE },
 { "qdft_summand",       12u, "srmech.cascade.qdft_summand",
   CR_DOM_CAS, CR_CAS_QDFT_SUMMAND, CR_BIN_NONE },
 { "odft_summand",       12u, "srmech.cascade.odft_summand",
   CR_DOM_CAS, CR_CAS_ODFT_SUMMAND, CR_BIN_NONE },
 /* wave C (rc452, gh #1653) — the klein4_from_one chain's string/bytes
  * leaves. `sha256_bytes` and `render_template` carry their REAL registered
  * homes (srmech.amsc.format / srmech.amsc.descriptor) — NOT a same-params
  * sibling — per the aliasing warning at the head of this table. Their
  * ToolEntries were REGISTERED in this same change; cr_args_keyset_ok
  * answers INTERNAL, not silent acceptance, if either row's `full` stops
  * resolving. */
 { "render_template",    15u, "srmech.amsc.descriptor.render_template",
   CR_DOM_CAS, CR_CAS_RENDER_TEMPLATE, CR_BIN_NONE },
 { "utf8_encode",        11u, "srmech.cascade.utf8_encode",
   CR_DOM_CAS, CR_CAS_UTF8_ENCODE, CR_BIN_NONE },
 { "sha256_bytes",       12u, "srmech.amsc.format.sha256_bytes",
   CR_DOM_CAS, CR_CAS_SHA256_BYTES, CR_BIN_NONE },
 { "str_concat",         10u, "srmech.cascade.str_concat",
   CR_DOM_CAS, CR_CAS_STR_CONCAT, CR_BIN_NONE },
 { "byte_slice",         10u, "srmech.cascade.byte_slice",
   CR_DOM_CAS, CR_CAS_BYTE_SLICE, CR_BIN_NONE },
 { "int_parse_le",       12u, "srmech.cascade.int_parse_le",
   CR_DOM_CAS, CR_CAS_INT_PARSE_LE, CR_BIN_NONE },
 /* wave D (rc452, gh #1653) — encode_loe_content's Class-A / C / M leaves.
  * Each `full` names the op's REAL registered home, never a same-params
  * sibling: `sha256_raw` is srmech.amsc.format's own entry (NOT sha256_bytes,
  * which takes the same single `data` param and would validate against the
  * wrong contract — the exact aliasing trap the head of this table names),
  * and `mint_vector` / `permute` / `bind` carry their defining modules. */
 { "sha256_raw",         10u, "srmech.amsc.format.sha256_raw",
   CR_DOM_CAS, CR_CAS_SHA256_RAW, CR_BIN_NONE },
 { "mint_vector",        11u, "srmech.signal_processing.mint_vector",
   CR_DOM_CAS, CR_CAS_MINT_VECTOR, CR_BIN_NONE },
 { "permute",             7u, "srmech.math.hdc.permute",
   CR_DOM_CAS, CR_CAS_HDC_PERMUTE, CR_BIN_NONE },
 { "bind",                4u, "srmech.math.hdc.bind",
   CR_DOM_CAS, CR_CAS_HDC_BIND, CR_BIN_NONE },
 /* FOLD-BODY-ONLY: `dom` is CR_DOM_NONE because orientation_compose is never
  * a plain step in any shipped descriptor — it exists to be folded. A
  * CR_DOM_NONE row is a deliberate, expressible state (cr_dispatch returns
  * NOT_IMPL for it), not an omission; the alternative was a second table,
  * which is what rc451 had. Its `sub` is a bare 0u: there is no domain enum
  * for a row no exec runs. f64_add / vec_add (rc452 Phase 3) are the same
  * state: the Σ accumulators the kuramoto / DFT chains fold, never plain. */
 { "orientation_compose", 19u, "srmech.cascade.orientation_compose",
   CR_DOM_NONE, 0u, CR_BIN_ORIENT },
 { "f64_add",             7u, "srmech.cascade.f64_add",
   CR_DOM_NONE, 0u, CR_BIN_F64_ADD },
 { "vec_add",             7u, "srmech.cascade.vec_add",
   CR_DOM_NONE, 0u, CR_BIN_VEC_ADD }
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

/* ------------------------------------------------------------------
 * THE PER-DOMAIN EXECS — the switch half of the A1 dispatch. Each switches on
 * its OWN enum type with NO `default:` arm, so -Wswitch under -Werror (and
 * /w44062 under /WX on MSVC) makes a table row whose `sub` has no case a
 * COMPILE ERROR, and a deleted case line equally so. The trailing return is
 * the open-enum path: `sub` rides the table as a uint8_t, so a value outside
 * the enum is expressible data, and it must answer INTERNAL rather than fall
 * off the end. tests/test_t1158_registry_param_order_rc449.py parses each
 * exec's case labels and pins them SET-EQUAL to the table's per-domain `sub`
 * column, so the two cannot drift apart even where a compiler is lenient.
 * ------------------------------------------------------------------ */

static srmech_status_t cr_exec_rat(cr_ctx_t *c, uint8_t sub,
                                   const srmech_json_value_t *args,
                                   cr_value_t **out)
{
    assert(c != NULL && out != NULL);
    assert(args != NULL);
    switch ((cr_rat_op_t)sub) {
    case CR_RAT_PI:            return cr_op_pi(c, args, out);
    case CR_RAT_EXP:           return cr_op_series(c, args, CR_SER_EXP, out);
    case CR_RAT_SIN:           return cr_op_series(c, args, CR_SER_SIN, out);
    case CR_RAT_COS:           return cr_op_series(c, args, CR_SER_COS, out);
    case CR_RAT_LOG1P:         return cr_op_series(c, args, CR_SER_LOG1P, out);
    case CR_RAT_ATAN:          return cr_op_series(c, args, CR_SER_ATAN, out);
    case CR_RAT_POW:           return cr_op_pow(c, args, out);
    case CR_RAT_ADD:           return cr_op_rat(c, args, '+', out);
    case CR_RAT_MUL:           return cr_op_rat(c, args, '*', out);
    case CR_RAT_DIV:           return cr_op_rat(c, args, '/', out);
    case CR_RAT_SCALE_ROUND:   return cr_op_scale_round(c, args, out);
    case CR_RAT_BEST_RATIONAL: return cr_op_best_rational(c, args, out);
    }
    return SRMECH_ERR_INTERNAL;
}

static srmech_status_t cr_exec_cyc(cr_ctx_t *c, uint8_t sub,
                                   const srmech_json_value_t *args,
                                   cr_value_t **out)
{
    assert(c != NULL && out != NULL);
    assert(args != NULL);
    switch ((cr_cyc_op_t)sub) {
    case CR_CYC_GCD:          return cr_op_cyclic(c, args, CR_CY_GCD, out);
    case CR_CYC_MOD_ADD:      return cr_op_cyclic(c, args, CR_CY_ADD, out);
    case CR_CYC_MOD_MUL:      return cr_op_cyclic(c, args, CR_CY_MUL, out);
    case CR_CYC_MOD_MUL_WIDE: return cr_op_cyclic(c, args, CR_CY_MUL, out);
    case CR_CYC_MOD_POW:      return cr_op_cyclic(c, args, CR_CY_POW, out);
    case CR_CYC_MOD_INV:      return cr_op_cyclic_inv(c, args, out);
    }
    return SRMECH_ERR_INTERNAL;
}

static srmech_status_t cr_exec_cas(cr_ctx_t *c, uint8_t sub,
                                   const srmech_json_value_t *args,
                                   cr_value_t **out)
{
    assert(c != NULL && out != NULL);
    assert(args != NULL);
    switch ((cr_cas_op_t)sub) {
    case CR_CAS_SEQ_LEN:         return cr_a_seq_len(c, args, out);
    case CR_CAS_CORR_PRODUCT:    return cr_a_corr_product(c, args, out);
    case CR_CAS_COMPENSATED_SUM: return cr_a_compensated_sum(c, args, out);
    case CR_CAS_PIN_SLOT:        return cr_op_pin_slot(c, args, out);
    case CR_CAS_REORIENT:        return cr_op_reorient(c, args, out);
    case CR_CAS_CHIRAL_FLIP:
        return cr_op_dseq(c, args, "seq", CR_DSEQ_CHIRAL_FLIP, out);
    case CR_CAS_AUTOCORRELATION: return cr_a_autocorrelation(c, args, out);
    case CR_CAS_DEAD_BAND:       return cr_op_dead_band(c, args, out);
    case CR_CAS_PAIR:            return cr_op_pair(c, args, out);
    case CR_CAS_SEQ_GET:         return cr_op_seq_get(c, args, out);
    case CR_CAS_VEC_SCALE:       return cr_op_vec_scale(c, args, out);
    case CR_CAS_KUR_INV_N:       return cr_op_kur_inv_n(c, args, out);
    case CR_CAS_KUR_SIN_TERM:    return cr_op_kur_sin_term(c, args, out);
    case CR_CAS_KUR_OUT_SIMPLE:  return cr_op_kur_out_simple(c, args, out);
    case CR_CAS_KUR_GEN_TERM:    return cr_op_kur_gen_term(c, args, out);
    case CR_CAS_KUR_GEN_OUT:     return cr_op_kur_gen_out(c, args, out);
    case CR_CAS_AS_QUAT4:        return cr_op_as_quat4(c, args, out);
    case CR_CAS_AS_OCT8:         return cr_op_as_oct8(c, args, out);
    case CR_CAS_QDFT_RESOLVE_MU: return cr_op_qdft_resolve_mu(c, args, out);
    case CR_CAS_ODFT_RESOLVE_MU: return cr_op_odft_resolve_mu(c, args, out);
    case CR_CAS_DFT_SIGMA:       return cr_op_dft_sigma(c, args, out);
    case CR_CAS_DFT_SCALE:       return cr_op_dft_scale(c, args, out);
    case CR_CAS_QDFT_SUMMAND:    return cr_op_qdft_summand(c, args, out);
    case CR_CAS_ODFT_SUMMAND:    return cr_op_odft_summand(c, args, out);
    case CR_CAS_RENDER_TEMPLATE: return cr_op_render_template(c, args, out);
    case CR_CAS_UTF8_ENCODE:     return cr_op_utf8_encode(c, args, out);
    case CR_CAS_SHA256_BYTES:    return cr_op_sha256_bytes(c, args, out);
    case CR_CAS_STR_CONCAT:      return cr_op_str_concat(c, args, out);
    case CR_CAS_BYTE_SLICE:      return cr_op_byte_slice(c, args, out);
    case CR_CAS_INT_PARSE_LE:    return cr_op_int_parse_le(c, args, out);
    case CR_CAS_SHA256_RAW:      return cr_op_sha256_raw(c, args, out);
    case CR_CAS_MINT_VECTOR:     return cr_op_mint_vector(c, args, out);
    case CR_CAS_HDC_PERMUTE:     return cr_op_hdc_permute(c, args, out);
    case CR_CAS_HDC_BIND:        return cr_op_hdc_bind(c, args, out);
    }
    return SRMECH_ERR_INTERNAL;
}

/* Dispatch one plain step's op. A row lookup plus the domain switch — no
 * if-chain, and (deliberately) no cr_op_is call of its own. An op with no
 * row, or a row that is fold-body-ONLY (dom == CR_DOM_NONE), returns NOT_IMPL
 * and the whole chain defers to the complete pure path. The explicit
 * CR_DOM_NONE arm keeps THIS switch exhaustive too — same -Wswitch gate. */
static srmech_status_t cr_dispatch(cr_ctx_t *c, const char *op, uint32_t opl,
                                   const srmech_json_value_t *args, cr_value_t **out)
{
    int32_t r;
    assert(c != NULL && op != NULL && out != NULL);
    assert(args != NULL);
    r = cr_op_row(op, opl);
    if (r < 0) { return SRMECH_ERR_NOT_IMPL; }
    switch ((cr_dom_t)CR_OP_REG[r].dom) {
    case CR_DOM_NONE: return SRMECH_ERR_NOT_IMPL;
    case CR_DOM_RAT:  return cr_exec_rat(c, CR_OP_REG[r].sub, args, out);
    case CR_DOM_CYC:  return cr_exec_cyc(c, CR_OP_REG[r].sub, args, out);
    case CR_DOM_CAS:  return cr_exec_cas(c, CR_OP_REG[r].sub, args, out);
    }
    return SRMECH_ERR_INTERNAL;
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

/* Lowercase-hex expansion of a byte buffer, carved from `tmp`. The payload
 * encoding of the `b` (BYTES) wire kind.
 *
 * ⚠️ WHY HEX AND NOT BASE64. The choice is forced by the same reasoning the
 * mapping kind's key ordering is: pick the encoding whose spelling leaves the
 * two projections NO decision to disagree about. Base64 has an alphabet
 * variant (standard vs URL-safe) and a padding rule, and each is a place a C
 * writer and a Python reader can differ while both look correct; lowercase hex
 * has exactly one spelling for any input, `bytes.hex()` produces it and
 * `bytes.fromhex()` inverts it exactly, and it is already the alphabet
 * srmech_sha256_hex emits, so no new encoder alphabet enters the library.
 *
 * (Not to be confused with the MCP tool surface's `bytes` coercer, which reads
 * BASE64 — that is an INPUT coercion on a different surface. Measured this rc:
 * feeding it hex raises `Incorrect padding`. The two are not interchangeable
 * and this comment exists so nobody "unifies" them by guess.) */
static char *cr_bytes_hex(cr_bump_t *tmp, const char *s, uint32_t n)
{
    static const char DIG[16] = { '0','1','2','3','4','5','6','7',
                                  '8','9','a','b','c','d','e','f' };
    char *out; uint32_t i;
    assert(tmp != NULL);
    assert(s != NULL || n == 0u);
    if (n > 0x3FFFFFFFu) { return NULL; }      /* 2n must not wrap uint32 */
    out = (char *)cr_carve(tmp, (size_t)n * 2u + 1u);
    if (out == NULL) { return NULL; }
    for (i = 0u; i < n; i++) {
        unsigned char by = (unsigned char)s[i];
        out[2u * i] = DIG[(by >> 4) & 0x0Fu];
        out[2u * i + 1u] = DIG[by & 0x0Fu];
    }
    out[2u * n] = '\0';
    return out;
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
        if (v->is_bytes) {
            /* rc452 (`#T1166`, gh #1653): the `b` kind. Through the wave-C
             * phase this arm returned NULL and cr_run_and_write declined a
             * bytes FINAL outright, because spelling bytes as `s` would erase
             * the str/bytes type on the wire — the exact collapse class the
             * rc450 comparator pins. The kind lands in the SAME change as
             * encode_loe_content, the chain that emits it, so it is never a
             * declared-but-unemitted letter. */
            char *hx = cr_bytes_hex(tmp, v->s, v->slen);
            if (hx == NULL) { return NULL; }
            vals[0] = srmech_json_new_string(bd, "b", 1u);
            vals[1] = srmech_json_new_string(bd, hx, v->slen * 2u);
            return srmech_json_new_object(bd, keys, vals, 2u);
        }
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
 * column. An op with no row, or a row whose `bin` is CR_BIN_NONE (an op that
 * exists but cannot serve as a fold body), returns NOT_IMPL and the WHOLE
 * chain defers to pure — the inform-don't-limit contract, never a wrong
 * answer. The switch has no `default:` arm for the same -Wswitch drift gate
 * the per-domain execs carry.
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
    if (r < 0) { return SRMECH_ERR_NOT_IMPL; }
    switch ((cr_bin_id_t)CR_OP_REG[r].bin) {
    case CR_BIN_NONE:    return SRMECH_ERR_NOT_IMPL;
    case CR_BIN_GCD:     return cr_b_gcd(b, acc, elem, out);
    case CR_BIN_ORIENT:  return cr_b_orient_compose(b, acc, elem, out);
    case CR_BIN_F64_ADD: return cr_b_f64_add(b, acc, elem, out);
    case CR_BIN_VEC_ADD: return cr_b_vec_add(b, acc, elem, out);
    }
    return SRMECH_ERR_INTERNAL;
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
    /* rc452 Phase 3: the seed is resolved GENERALLY — an int (the original
     * arm), a real (the kuramoto Σ's 0.0), a LIST (the DFT Σ's zero vector),
     * or a reference — exactly compose.py's `_resolve_args(step.fold_init)`.
     * Through the first half of rc452 only a JSON_INT seed was accepted, so
     * every float/vector fold declined at the SEED, and the gate blamed the
     * op table. */
    if (fi == NULL) { return SRMECH_ERR_NOT_IMPL; }
    acc = cr_resolve_arg(c, fi);
    if (acc == NULL) { return SRMECH_ERR_NOT_IMPL; }
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
 * ⚠️ The key-set check lives HERE and not in cr_dispatch. When that function
 * was a 16-arm if-chain it measured 57 of JPL Rule 4's 60 lines and a per-op
 * check inline there broke the rule immediately; the CR_OP_REG conversion
 * shrank it, but the separation stands because validate-then-dispatch is the
 * contract shape (the validator answers BAD_INPUT where the dispatch would
 * merely defer, and the two must stay distinguishable). */
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

/* Parse chain + ctx trees, then drive the steps (kept < 60 lines).
 *
 * THE REQUIRED CHAIN HEADER (rc452, gh #1653 — co-equal-projection finding
 * (b)). Through rc452 Phase 3 this runner ACCEPTED a chain object carrying
 * neither `name` nor `summary`, while Python's parse_chain_spec REJECTS both
 * with ChainSpecError — and Python is the side the CONTRACT backs: this
 * file's own header doc declares chain_json "the FULL chain object
 * {name,summary,returns,on_error?,steps}", and the C parse peer
 * (srmech_chain_spec_parse, srmech_compose.c cr_parse_chain_header) has
 * required all three since it shipped. So the runner now refuses what every
 * parse layer refuses. PRESENCE, not string-ness, is the test: the pure
 * parser coerces any value through str(), and the native parse peer's
 * stricter string check merely defers to pure, which accepts — so requiring
 * a STRING here would refuse what Python accepts, the same divergence class
 * mirrored. Measured cost of the old acceptance: the shipped parity
 * harnesses' `_chain_only` stripped `summary`/`returns` on the reasoning
 * "the runner never reads them", and the bare-C TOML host fed
 * [[cascade.chain]] entries that carry no `name` at all — both ran
 * headerless chains for four rcs with no instrument able to say so. */
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
    /* the required header — the block comment above this function */
    if (srmech_json_object_get(chain, "name") == NULL ||
        srmech_json_object_get(chain, "summary") == NULL ||
        srmech_json_object_get(chain, "returns") == NULL) {
        return SRMECH_ERR_BAD_INPUT;
    }
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
    /* (The rc452 wave-C FINAL-decline for a bytes carrier stood HERE and is
     * GONE: the `b` kind ships with encode_loe_content in this change, so a
     * bytes final now marshals rather than declining. cr_desc_scalar's `b`
     * arm is the whole replacement — there is no residual special case.) */
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
