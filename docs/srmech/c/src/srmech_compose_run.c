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

typedef struct cr_value {
    cr_kind_t kind;
    srmech_bigint_t *num;      /* CR_INT: the value; CR_RATIONAL: numerator */
    srmech_bigint_t *den;      /* CR_RATIONAL: denominator (> 0, reduced)   */
    const char *s; uint32_t slen;          /* CR_STR (aliases arena)        */
    struct cr_value **items; uint32_t n;   /* CR_LIST                       */
    double d;                              /* CR_DBL                        */
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
    if (j->type != SRMECH_JSON_STRING) { return NULL; }   /* array / obj / bool */
    out = cr_new_value(b, CR_STR);
    if (out == NULL) { return NULL; }
    out->s = j->u.str.ptr; out->slen = j->u.str.len;
    return out;
}

/* Convert an ARRAY json node to a flat CR_LIST of scalars (one level; a nested
 * array element → NULL → defer). No recursion. */
static cr_value_t *cr_json_list(cr_bump_t *b, const srmech_json_value_t *j)
{
    cr_value_t *out; cr_value_t **items; uint32_t i;
    assert(b != NULL && j != NULL);
    assert(j->type == SRMECH_JSON_ARRAY);
    out = cr_new_value(b, CR_LIST);
    if (out == NULL) { return NULL; }
    out->n = j->u.arr.n;
    items = (cr_value_t **)cr_carve(b, (size_t)out->n * sizeof(void *) + 1u);
    if (items == NULL) { return NULL; }
    for (i = 0u; i < out->n; i++) {
        items[i] = cr_json_scalar(b, j->u.arr.items[i]);   /* NO recursion */
        if (items[i] == NULL) { return NULL; }
    }
    out->items = items;
    return out;
}

/* Convert a resolved JSON node (from a @row/@input walk) to a value carrier:
 * a flat list, else a scalar. NULL → defer. */
static cr_value_t *cr_json_to_value(cr_bump_t *b, const srmech_json_value_t *j)
{
    assert(b != NULL);
    assert(j == NULL || j->type <= SRMECH_JSON_OBJECT);
    if (j != NULL && j->type == SRMECH_JSON_ARRAY) { return cr_json_list(b, j); }
    return cr_json_scalar(b, j);
}

/* ------------------------------------------------------------------
 * The run context (row / inputs JSON + the persisting step outputs).
 * ------------------------------------------------------------------ */

typedef struct cr_ctx {
    const srmech_json_value_t *row;      /* or NULL */
    const srmech_json_value_t *inputs;   /* or NULL */
    cr_value_t **step_out;               /* [n_steps]; filled up to cur */
    uint32_t cur;                        /* index of the step being run */
    cr_bump_t *b;
} cr_ctx_t;

/* Resolve a `@...` reference string to a value carrier. NULL → defer. */
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
        if (rest != e) { return NULL; }   /* only bare `.output` supported */
        return c->step_out[idx];
    }
    return NULL;   /* @catalog or unknown → defer */
}

/* A list ELEMENT: a `@...` ref or a scalar literal (no nesting → no recursion). */
static cr_value_t *cr_resolve_elem(cr_ctx_t *c, const srmech_json_value_t *j)
{
    assert(c != NULL);
    assert(c->b != NULL);
    if (j == NULL) { return NULL; }
    if (j->type == SRMECH_JSON_STRING && j->u.str.len > 0u &&
        j->u.str.ptr[0] == '@') {
        return cr_resolve_ref(c, j->u.str.ptr, j->u.str.len);
    }
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

/* pi_cascade_digits(num_digits[, max_cascade_depth, precision_bits]) -> str.
 * Auto-scales depth/precision the same as rational.pi_cascade_digits. */
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
    dep = cr_arg(c, args, "max_cascade_depth"); prc = cr_arg(c, args, "precision_bits");
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
    va = cr_arg(c, args, "a");
    vb = cr_arg(c, args, (which == CR_CY_POW) ? "k" : "b");
    if (va == NULL || vb == NULL) { return SRMECH_ERR_NOT_IMPL; }
    if (va->kind != CR_INT || vb->kind != CR_INT) { return SRMECH_ERR_NOT_IMPL; }
    A = va->num; B = vb->num;
    if (which != CR_CY_GCD) {
        vn = cr_arg(c, args, "n");
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
static srmech_status_t cr_dispatch_real(cr_ctx_t *c, const char *op, uint32_t opl,
                                        const srmech_json_value_t *args,
                                        cr_value_t **out)
{
    assert(c != NULL && op != NULL);
    assert(args != NULL && out != NULL);
    if (opl >= 11u && memcmp(op + (opl - 11u), "chiral_flip", 11u) == 0) {
        return cr_op_dseq(c, args, "seq", srmech_cascade_chiral_flip_f64, out);
    }
    if (opl >= 15u && memcmp(op + (opl - 15u), "autocorrelation", 15u) == 0) {
        return cr_op_dseq(c, args, "x", srmech_autocorrelation_f64, out);
    }
    return SRMECH_ERR_NOT_IMPL;
}

static srmech_status_t cr_dispatch(cr_ctx_t *c, const char *op, uint32_t opl,
                                   const srmech_json_value_t *args, cr_value_t **out)
{
    assert(c != NULL && op != NULL && out != NULL);
    assert(args != NULL);
    if (opl == 17u && memcmp(op, "pi_cascade_digits", 17u) == 0) {
        return cr_op_pi(c, args, out);
    }
    if (opl == 19u && memcmp(op, "exp_series_truncate", 19u) == 0) {
        return cr_op_series(c, args, srmech_exp_series_truncate_big, out);
    }
    if (opl == 19u && memcmp(op, "sin_series_truncate", 19u) == 0) {
        return cr_op_series(c, args, srmech_sin_series_truncate_big, out);
    }
    if (opl == 19u && memcmp(op, "cos_series_truncate", 19u) == 0) {
        return cr_op_series(c, args, srmech_cos_series_truncate_big, out);
    }
    if (opl == 21u && memcmp(op, "log1p_series_truncate", 21u) == 0) {
        return cr_op_series(c, args, srmech_log1p_series_truncate_big, out);
    }
    if (opl == 20u && memcmp(op, "atan_series_truncate", 20u) == 0) {
        return cr_op_series(c, args, srmech_atan_series_truncate_big, out);
    }
    if (opl == 17u && memcmp(op, "rational_pow_uint", 17u) == 0) {
        return cr_op_pow(c, args, out);
    }
    if (opl == 12u && memcmp(op, "rational_add", 12u) == 0) {
        return cr_op_rat(c, args, '+', out);
    }
    if (opl == 12u && memcmp(op, "rational_mul", 12u) == 0) {
        return cr_op_rat(c, args, '*', out);
    }
    if (opl == 12u && memcmp(op, "rational_div", 12u) == 0) {
        return cr_op_rat(c, args, '/', out);
    }
    /* Class-I cyclic group (gh #1653). Declines out-of-uint64 operands. */
    if (opl == 3u && memcmp(op, "gcd", 3u) == 0) {
        return cr_op_cyclic(c, args, CR_CY_GCD, out);
    }
    if (opl == 7u && memcmp(op, "mod_add", 7u) == 0) {
        return cr_op_cyclic(c, args, CR_CY_ADD, out);
    }
    if (opl == 7u && memcmp(op, "mod_mul", 7u) == 0) {
        return cr_op_cyclic(c, args, CR_CY_MUL, out);
    }
    if (opl == 12u && memcmp(op, "mod_mul_wide", 12u) == 0) {
        return cr_op_cyclic(c, args, CR_CY_MUL, out);
    }
    if (opl == 7u && memcmp(op, "mod_pow", 7u) == 0) {
        return cr_op_cyclic(c, args, CR_CY_POW, out);
    }
    if (opl == 7u && memcmp(op, "mod_inv", 7u) == 0) {
        return cr_op_cyclic_inv(c, args, out);
    }
    return cr_dispatch_real(c, op, opl, args, out);   /* else: not in the
                                                      * table → pure */
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

/* Marshal a flat CR_LIST as {"items": [...], "k": "l"} (keys canonical-sorted).
 * One level, a plain loop, NO recursion.
 *
 * ⚠️ Python's _reconstruct_value has ALWAYS had a `k == "l"` branch, so the
 * scripting projection could read a list descriptor the compiled one could not
 * produce. That asymmetry ran the OTHER way from the one gh #1653 is about —
 * the reader was ahead of the writer — and it went unnoticed because nothing
 * exercised it. Closing it needs no Python change, which is exactly why it was
 * invisible. */
static srmech_json_value_t *cr_desc_list(srmech_json_builder_t *bd,
                                         const cr_value_t *v, cr_bump_t *tmp)
{
    const char *keys[2]; srmech_json_value_t *vals[2];
    srmech_json_value_t **items; uint32_t i;
    assert(bd != NULL && v != NULL);
    assert(v->kind == CR_LIST);
    items = (srmech_json_value_t **)cr_carve(tmp, (size_t)v->n * sizeof(void *) + 1u);
    if (items == NULL) { return NULL; }
    for (i = 0u; i < v->n; i++) {
        items[i] = cr_desc_scalar(bd, v->items[i], tmp);   /* NO recursion */
        if (items[i] == NULL) { return NULL; }
    }
    keys[0] = "items"; keys[1] = "k";
    vals[0] = srmech_json_new_array(bd, items, v->n);
    vals[1] = srmech_json_new_string(bd, "l", 1u);
    if (vals[0] == NULL) { return NULL; }
    return srmech_json_new_object(bd, keys, vals, 2u);
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


/* 1 iff `op` names orientation_compose — bare, or any dotted spelling ending
 * `.orientation_compose` (descriptors write the dotted form). */
static int cr_body_is_orient_compose(const char *op, uint32_t opl)
{
    static const char dotted[21] = ".orientation_compose";
    assert(op != NULL);
    assert(opl > 0u);
    if (opl == 19u && memcmp(op, "orientation_compose", 19u) == 0) { return 1; }
    if (opl > 20u && memcmp(op + (opl - 20u), dotted, 20u) == 0) { return 1; }
    return 0;
}

/* One binary fold step. An op outside the table, or an operand outside the
 * int64 shape, returns NOT_IMPL and the WHOLE chain defers to pure — the
 * inform-don't-limit contract, never a wrong answer. */
static srmech_status_t cr_fold_body(cr_bump_t *b, const char *op, uint32_t opl,
                                    const cr_value_t *acc,
                                    const cr_value_t *elem, cr_value_t **out)
{
    int64_t a, e, r; srmech_status_t st;
    assert(b != NULL && op != NULL && out != NULL);
    assert(acc != NULL && elem != NULL);
    if (!cr_body_is_orient_compose(op, opl)) { return SRMECH_ERR_NOT_IMPL; }
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

/* One PLAIN step: validate the `op` / `args` shape, then dispatch. Split out
 * of cr_run_steps so the loop can branch on step form and both stay < 60
 * lines (JPL Rule 4). */
static srmech_status_t cr_run_plain(cr_ctx_t *c, const srmech_json_value_t *step,
                                    cr_value_t **out)
{
    const srmech_json_value_t *args = srmech_json_object_get(step, "args");
    const srmech_json_value_t *o = srmech_json_object_get(step, "op");
    assert(c != NULL && step != NULL && out != NULL);
    assert(step->type == SRMECH_JSON_OBJECT);
    if (o == NULL || o->type != SRMECH_JSON_STRING) { return SRMECH_ERR_BAD_INPUT; }
    if (args == NULL || args->type != SRMECH_JSON_OBJECT) { return SRMECH_ERR_BAD_INPUT; }
    return cr_dispatch(c, o->u.str.ptr, o->u.str.len, args, out);
}

/* Parse chain + ctx trees, then drive the steps (kept < 60 lines). */
static srmech_status_t cr_run_steps(const srmech_json_value_t *chain,
                                    const srmech_json_value_t *ctx, cr_bump_t *b,
                                    cr_value_t **final_out)
{
    const srmech_json_value_t *steps = srmech_json_object_get(chain, "steps");
    const srmech_json_value_t *oe = srmech_json_object_get(chain, "on_error");
    cr_ctx_t c; uint32_t i, ns; srmech_status_t st;
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
    c.b = b;
    c.step_out = (cr_value_t **)cr_carve(b, (size_t)ns * sizeof(void *) + 1u);
    if (c.step_out == NULL) { return SRMECH_ERR_OVERFLOW; }
    for (i = 0u; i < ns; i++) {
        const srmech_json_value_t *step = steps->u.arr.items[i];
        const srmech_json_value_t *so;
        cr_value_t *out = NULL;
        if (step == NULL || step->type != SRMECH_JSON_OBJECT) { return SRMECH_ERR_BAD_INPUT; }
        so = srmech_json_object_get(step, "on_error");
        if (so != NULL && so->type != SRMECH_JSON_NULL) { return SRMECH_ERR_BAD_INPUT; }
        c.cur = i;
        switch (cr_step_form(step)) {
        case CR_FORM_PLAIN: st = cr_run_plain(&c, step, &out); break;
        case CR_FORM_FOLD:  st = cr_run_fold(&c, step, &out); break;
        /* MAP needs an explicit frame stack (JPL Rule 1 bans the recursive
         * body walk), so it is filed rather than half-done here. NOT_IMPL —
         * a recognised form this projection does not yet run — is deliberately
         * distinct from the BAD_INPUT that MIXED / NONE earn, which are
         * malformed rather than unimplemented. */
        case CR_FORM_MAP:   st = SRMECH_ERR_NOT_IMPL; break;
        default:            st = SRMECH_ERR_BAD_INPUT; break;
        }
        if (st != SRMECH_OK) { return st; }
        c.step_out[i] = out;
    }
    *final_out = c.step_out[ns - 1u];
    return SRMECH_OK;
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
