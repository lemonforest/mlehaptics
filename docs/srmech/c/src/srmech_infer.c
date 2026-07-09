/* srmech_infer.c — the F929 OPEN/infer ROUTER in C (0.9.0rc176; the
 * ORCHESTRATION->C spine, batch 6; the CARRIER-FFI foundation).
 *
 * The C peer of srmech.amsc.dispatch.infer — the META-dispatcher over srmech's
 * shipped closed-form reduction-theory rows (F929: the 14 A-N classes ARE a
 * DISPATCH TABLE over reduction theories humans already built). Given a STORED
 * RELATIONSHIP marshalled as JSON, DETECT which row its operand structure
 * matches, DISPATCH the matching C reducer, VERIFY the reducer's OWN contract,
 * and return the DECISION (reducible / row / reducer) as a small JSON
 * descriptor. The Python caller reconstructs the closed_form OBJECT from the
 * SAME reducer this op verified, so the native path is byte-identical to the
 * pure infer path (a bare-C host reads the decision + calls the reducer for the
 * form).
 *
 * rc176 SCOPE — the two EXACT-SYMBOLIC bignum-carrier rows that share ONE
 * carrier-FFI marshal (JSON with bignum-decimal-string coefficients — the
 * foundation the DSL make_class / loop / fold interpreter will reuse):
 *   * cyclic       (the_one) — operand (sigma, theta_num, theta_den). Dispatch
 *                  srmech_the_one; VERIFY the n1_is_sigma_only invariant read
 *                  from the reducer's ACTUAL output: flat[1] == (sigma, 1) (the
 *                  (1,3,7,3)/(0,1,3) partition invariants are structural
 *                  constants). reducible iff sigma in {+1,-1} AND theta_den > 0
 *                  AND the n=1 imaginary entry == (sigma, 1).
 *   * sigma-gosper (gosper)  — operand (term_ratio_num, term_ratio_den) as
 *                  ascending (num, den) rational coefficient lists. Dispatch
 *                  srmech_gosper; VERIFY = a hypergeometric antidifference
 *                  exists (has == 1) — a (non-None) certificate IS the proof.
 *
 * rc103 inform-don't-limit: ANY other row (the definite-sum wz / spectral /
 * multivariate / q / elliptic sub-rows, whose live carriers need their own
 * bridge — deferred to rc177+), any malformed operand, or any arena overflow ->
 * non-OK, and the Python caller runs the COMPLETE pure infer (never a wrong
 * answer; NEVER a false reducible). The honest OPEN residue IS the
 * no-hallucination discipline: the C path returns "not reducible" identically,
 * never a fabricated reduction.
 *
 * ARENA: ONE caller arena `ws`, bump-allocated forward (size with
 * srmech_infer_arena_bytes). All bignum limbs alias into `ws`. JPL Power-of-Ten:
 * caller-arena only (no malloc), <=60-line functions, >=2 asserts/function, no
 * goto/recursion/abs/libm. Additive symbols -> SRMECH_ABI_VERSION stays 3 (the
 * Python ctypes shim hasattr-guards them). See docs/srmech/python/srmech/amsc/
 * dispatch.py for the pure-Python oracle + the row semantics.
 */

#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

#include "srmech.h"

#define INF_ONE_DIM  14u        /* the One's 1+3+7+3 = 14 flat rationals   */
#define INF_ONE_TERMS 24u       /* DEFAULT_TERMS in srmech.amsc.cascade.one */

/* ------------------------------------------------------------------
 * Bump arena — forward-only carve, void*-aligned (the srmech_compose_run
 * pattern). NULL (no partial carve) if a request does not fit.
 * ------------------------------------------------------------------ */

typedef struct { unsigned char *cur; unsigned char *end; } inf_bump_t;

static unsigned char *inf_align(unsigned char *p)
{
    uintptr_t a = (uintptr_t)sizeof(void *);
    uintptr_t pad;
    assert(p != NULL);
    assert(a >= 4u);
    pad = (a - ((uintptr_t)p % a)) % a;
    return p + pad;
}

static unsigned char *inf_carve(inf_bump_t *b, size_t n)
{
    unsigned char *p;
    assert(b != NULL);
    assert(b->cur <= b->end);
    p = inf_align(b->cur);
    if (p > b->end || n > (size_t)(b->end - p)) { return NULL; }
    b->cur = p + n;
    return p;
}

/* Carve a zeroed srmech_bigint with `cap` limbs (a fresh value carrier). */
static srmech_bigint_t *inf_new_bigint(inf_bump_t *b, uint32_t cap)
{
    srmech_bigint_t *bi;
    uint32_t *limbs;
    assert(b != NULL);
    assert(cap > 0u);
    bi = (srmech_bigint_t *)inf_carve(b, sizeof(srmech_bigint_t));
    if (bi == NULL) { return NULL; }
    limbs = (uint32_t *)inf_carve(b, (size_t)cap * sizeof(uint32_t));
    if (limbs == NULL) { return NULL; }
    bi->sign = 0; bi->n = 0u; bi->cap = cap; bi->limbs = limbs;
    return bi;
}

/* Carve `count` zeroed srmech_bigint carriers of `cap` limbs each (a fresh
 * coefficient array). NULL if any carve does not fit. */
static srmech_bigint_t *inf_bigint_array(inf_bump_t *b, size_t count, uint32_t cap)
{
    srmech_bigint_t *arr;
    size_t i;
    assert(b != NULL);
    assert(cap > 0u && count > 0u);
    arr = (srmech_bigint_t *)inf_carve(b, count * sizeof(srmech_bigint_t));
    if (arr == NULL) { return NULL; }
    for (i = 0u; i < count; i++) {
        uint32_t *limbs = (uint32_t *)inf_carve(b, (size_t)cap * sizeof(uint32_t));
        if (limbs == NULL) { return NULL; }
        arr[i].sign = 0; arr[i].n = 0u; arr[i].cap = cap; arr[i].limbs = limbs;
    }
    return arr;
}

/* Fill an EXISTING bigint carrier from a JSON scalar (int64 OR decimal string).
 * BAD_INPUT on a NULL / wrong-typed node. */
static srmech_status_t inf_fill_bigint(const srmech_json_value_t *j,
                                       srmech_bigint_t *dest)
{
    assert(dest != NULL);
    assert(dest->limbs != NULL);
    if (j == NULL) { return SRMECH_ERR_BAD_INPUT; }
    if (j->type == SRMECH_JSON_INT) { return srmech_bigint_set_i64(dest, j->u.i); }
    if (j->type == SRMECH_JSON_STRING && j->u.str.len > 0u) {
        return srmech_bigint_from_dec(dest, j->u.str.ptr, j->u.str.len);
    }
    return SRMECH_ERR_BAD_INPUT;
}

/* ------------------------------------------------------------------
 * CYCLIC row (the_one).
 * ------------------------------------------------------------------ */

/* Build S(sigma, theta) via srmech_the_one and VERIFY n1_is_sigma_only:
 * the n=1 imaginary flat entry (index 1) equals the rational (sigma, 1).
 * Sets *out_reducible; non-OK ONLY on arena / reducer failure (-> pure). */
static srmech_status_t inf_one_reduce(inf_bump_t *b, int32_t sigma,
        const srmech_bigint_t *tn, const srmech_bigint_t *td,
        size_t tn_len, size_t td_len, int *out_reducible)
{
    srmech_bigint_t *on, *od, *chk;
    unsigned char *wsp;
    size_t wsb, nl, dl;
    uint32_t cap;
    srmech_status_t st;
    assert(b != NULL && tn != NULL && td != NULL && out_reducible != NULL);
    assert(sigma == 1 || sigma == -1);
    cap = (uint32_t)(32u * (INF_ONE_TERMS + tn_len + td_len) + 256u);
    on = inf_bigint_array(b, INF_ONE_DIM, cap);
    od = inf_bigint_array(b, INF_ONE_DIM, cap);
    if (on == NULL || od == NULL) { return SRMECH_ERR_OVERFLOW; }
    nl = (tn_len / 9u) + 2u;
    dl = (td_len / 9u) + 2u;
    wsb = srmech_the_one_ws_bound(nl, dl, INF_ONE_TERMS);
    wsp = inf_carve(b, wsb);
    if (wsp == NULL) { return SRMECH_ERR_OVERFLOW; }
    st = srmech_the_one(sigma, tn, td, INF_ONE_TERMS, on, od, wsp, wsb);
    if (st != SRMECH_OK) { return st; }
    chk = inf_new_bigint(b, 3u);
    if (chk == NULL) { return SRMECH_ERR_OVERFLOW; }
    if (srmech_bigint_set_i64(chk, (int64_t)sigma) != SRMECH_OK) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (srmech_bigint_cmp(&on[1], chk) == 0 &&
        od[1].sign == 1 && od[1].n == 1u && od[1].limbs[0] == 1u) {
        *out_reducible = 1;
    }
    return SRMECH_OK;
}

/* The CYCLIC dispatch: read (sigma, theta_num, theta_den), guard the reducibility
 * preconditions (sigma in {+1,-1}, theta_den > 0), then verify via the_one. A
 * valid-but-not-reducible relationship sets *out_reducible = 0 and returns OK. */
static srmech_status_t inf_cyclic(const srmech_json_value_t *root, inf_bump_t *b,
                                  int *out_reducible)
{
    const srmech_json_value_t *js, *jn, *jd;
    srmech_bigint_t *tn, *td;
    int32_t sigma;
    size_t tn_len, td_len;
    uint32_t cap;
    assert(root != NULL && b != NULL && out_reducible != NULL);
    assert(sizeof(int32_t) == 4u);
    *out_reducible = 0;
    js = srmech_json_object_get(root, "sigma");
    jn = srmech_json_object_get(root, "theta_num");
    jd = srmech_json_object_get(root, "theta_den");
    if (js == NULL || js->type != SRMECH_JSON_INT || jn == NULL || jd == NULL) {
        return SRMECH_ERR_BAD_INPUT;
    }
    sigma = (int32_t)js->u.i;
    if (sigma != 1 && sigma != -1) { return SRMECH_OK; }   /* not reducible */
    tn_len = (jn->type == SRMECH_JSON_STRING) ? (size_t)jn->u.str.len : 20u;
    td_len = (jd->type == SRMECH_JSON_STRING) ? (size_t)jd->u.str.len : 20u;
    cap = (uint32_t)srmech_bigint_from_dec_bound(tn_len > td_len ? tn_len : td_len);
    tn = inf_new_bigint(b, cap);
    td = inf_new_bigint(b, cap);
    if (tn == NULL || td == NULL) { return SRMECH_ERR_OVERFLOW; }
    if (inf_fill_bigint(jn, tn) != SRMECH_OK) { return SRMECH_ERR_BAD_INPUT; }
    if (inf_fill_bigint(jd, td) != SRMECH_OK) { return SRMECH_ERR_BAD_INPUT; }
    if (td->sign <= 0) { return SRMECH_OK; }               /* theta_den <= 0 */
    return inf_one_reduce(b, sigma, tn, td, tn_len, td_len, out_reducible);
}

/* ------------------------------------------------------------------
 * SIGMA row — the indefinite gosper sub-case.
 * ------------------------------------------------------------------ */

/* Max decimal-digit length over a term-ratio array's [num, den] coefficient
 * pairs (a JSON int node bounds at 20 digits; a string node at its length). */
static size_t inf_poly_maxlen(const srmech_json_value_t *arr)
{
    size_t m = 1u;
    uint32_t i, k;
    assert(arr != NULL);
    assert(arr->type == SRMECH_JSON_ARRAY);
    for (i = 0u; i < arr->u.arr.n; i++) {
        const srmech_json_value_t *pair = arr->u.arr.items[i];
        if (pair == NULL || pair->type != SRMECH_JSON_ARRAY) { continue; }
        for (k = 0u; k < pair->u.arr.n; k++) {
            const srmech_json_value_t *e = pair->u.arr.items[k];
            size_t L = 20u;
            if (e != NULL && e->type == SRMECH_JSON_STRING) { L = (size_t)e->u.str.len; }
            if (L > m) { m = L; }
        }
    }
    return m;
}

/* Read a term-ratio array [[num, den], ...] (ascending degree) into parallel
 * numerator / denominator bigint coefficient arrays of `cap` limbs each.
 * BAD_INPUT on a malformed entry; OVERFLOW on arena exhaustion. */
static srmech_status_t inf_read_poly(inf_bump_t *b, const srmech_json_value_t *arr,
        uint32_t cap, srmech_bigint_t **out_num, srmech_bigint_t **out_den)
{
    srmech_bigint_t *ns, *ds;
    uint32_t i, cnt;
    assert(b != NULL && arr != NULL);
    assert(out_num != NULL && out_den != NULL);
    if (arr->type != SRMECH_JSON_ARRAY || arr->u.arr.n == 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    cnt = arr->u.arr.n;
    ns = inf_bigint_array(b, cnt, cap);
    ds = inf_bigint_array(b, cnt, cap);
    if (ns == NULL || ds == NULL) { return SRMECH_ERR_OVERFLOW; }
    for (i = 0u; i < cnt; i++) {
        const srmech_json_value_t *pair = arr->u.arr.items[i];
        if (pair == NULL || pair->type != SRMECH_JSON_ARRAY ||
            pair->u.arr.n != 2u) {
            return SRMECH_ERR_BAD_INPUT;
        }
        if (inf_fill_bigint(pair->u.arr.items[0], &ns[i]) != SRMECH_OK ||
            inf_fill_bigint(pair->u.arr.items[1], &ds[i]) != SRMECH_OK) {
            return SRMECH_ERR_BAD_INPUT;
        }
    }
    *out_num = ns; *out_den = ds;
    return SRMECH_OK;
}

/* The SIGMA (gosper) dispatch: read the two term-ratio polys, run srmech_gosper,
 * and set *out_reducible = 1 iff a hypergeometric antidifference exists (has).
 * Non-OK ONLY on arena / reducer failure (-> pure). */
static srmech_status_t inf_gosper(const srmech_json_value_t *root, inf_bump_t *b,
                                  int *out_reducible)
{
    const srmech_json_value_t *jnum, *jden;
    srmech_bigint_t *num_n, *num_d, *den_n, *den_d, *rnn, *rnd, *rdn, *rdd;
    size_t n_num, n_den, deg, cl, cap_l, wsb, rnl, rdl;
    unsigned char *wsp;
    uint32_t cap;
    int has = 0;
    srmech_status_t st;
    assert(root != NULL && b != NULL && out_reducible != NULL);
    assert(sizeof(size_t) >= 4u);
    *out_reducible = 0;
    jnum = srmech_json_object_get(root, "term_ratio_num");
    jden = srmech_json_object_get(root, "term_ratio_den");
    if (jnum == NULL || jden == NULL || jnum->type != SRMECH_JSON_ARRAY ||
        jden->type != SRMECH_JSON_ARRAY || jden->u.arr.n == 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    n_num = (size_t)jnum->u.arr.n; n_den = (size_t)jden->u.arr.n;
    deg = n_num > n_den ? n_num : n_den;
    cl = srmech_bigint_from_dec_bound(
        inf_poly_maxlen(jnum) > inf_poly_maxlen(jden)
        ? inf_poly_maxlen(jnum) : inf_poly_maxlen(jden));
    cap_l = srmech_gosper_out_cap(cl, deg);
    cap = (uint32_t)cap_l;
    if (inf_read_poly(b, jnum, cap, &num_n, &num_d) != SRMECH_OK ||
        inf_read_poly(b, jden, cap, &den_n, &den_d) != SRMECH_OK) {
        return SRMECH_ERR_BAD_INPUT;
    }
    rnn = inf_bigint_array(b, deg + 2u, cap); rnd = inf_bigint_array(b, deg + 2u, cap);
    rdn = inf_bigint_array(b, deg + 2u, cap); rdd = inf_bigint_array(b, deg + 2u, cap);
    wsb = srmech_gosper_ws_bound(cl, deg);
    wsp = inf_carve(b, wsb);
    if (rnn == NULL || rnd == NULL || rdn == NULL || rdd == NULL || wsp == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    st = srmech_gosper(num_n, num_d, n_num, den_n, den_d, n_den, &has,
                       rnn, rnd, &rnl, rdn, rdd, &rdl, wsp, wsb);
    if (st != SRMECH_OK) { return st; }
    *out_reducible = has ? 1 : 0;
    return SRMECH_OK;
}

/* ------------------------------------------------------------------
 * SIGMA-DEFINITE row (wz_certificate) — rc192, the #796 payoff. Consumes the
 * rc191 PUBLIC srmech_carrier_read_bipoly reader for the four (n,k) BiPoly
 * term-ratios, then reproduces srmech.amsc.wz_certificate.wz_certificate in C:
 *   FIND  — srmech_zeilberger at max_order=1 (the forced f(n+1)-f(n)=0
 *           recurrence); accept only its WZ shape a_0(n)+a_1(n)=0 with a_0,a_1
 *           NONZERO constants in n.
 *   PROVE — rescale the raw certificate by 1/a_1 (x_num = cert*(a1_den/a1_num),
 *           sign-normalised to a positive denominator; x_den = rn_den) and run
 *           srmech_wz_verify (the COMPLETE degree-bounded WZ-equation check).
 * reducible iff the WZ equation VERIFIES — the genuine identity proof, not the
 * FIND alone (the anti-shell discipline). All scratch/ws carves off the MB-scale
 * infer arena (srmech_infer_sigma_definite_arena_bytes), NOT the vtable arena
 * (the rc191 finding). Any arena / reducer non-OK -> the pure wz_certificate.
 * ------------------------------------------------------------------ */

/* A BiPoly operand read from the wire (flat k-then-n num/den + per-k klen). */
typedef struct {
    srmech_bigint_t *num;
    srmech_bigint_t *den;
    size_t          *klen;
    size_t           kdeg;
} inf_bipoly_t;

/* The srmech_zeilberger output block (order-1 recurrence + raw certificate). */
typedef struct {
    srmech_bigint_t *coeff_n, *coeff_d; size_t *coeff_nlen;
    srmech_bigint_t *cert_n,  *cert_d;  size_t *cert_klen; size_t cert_kdeg;
    int has; size_t order; uint32_t out_cap;
} inf_zeil_t;

/* Bump-carve off the PUBLIC marshal arena (the rc191 srmech_carrier_read_bipoly
 * arena type). NULL (no partial carve) if a request does not fit. */
static unsigned char *inf_ma_carve(srmech_marshal_arena_t *a, size_t n)
{
    unsigned char *p;
    assert(a != NULL);
    assert(a->cur <= a->end);
    p = inf_align(a->cur);
    if (p > a->end || n > (size_t)(a->end - p)) { return NULL; }
    a->cur = p + n;
    return p;
}

/* Carve `count` zeroed srmech_bigint carriers of `cap` limbs each off `a`. */
static srmech_bigint_t *inf_ma_bigints(srmech_marshal_arena_t *a,
                                       size_t count, uint32_t cap)
{
    srmech_bigint_t *arr;
    size_t i;
    assert(a != NULL);
    assert(cap > 0u && count > 0u);
    arr = (srmech_bigint_t *)inf_ma_carve(a, count * sizeof(srmech_bigint_t));
    if (arr == NULL) { return NULL; }
    for (i = 0u; i < count; i++) {
        uint32_t *limbs = (uint32_t *)inf_ma_carve(a, (size_t)cap * sizeof(uint32_t));
        if (limbs == NULL) { return NULL; }
        arr[i].sign = 0; arr[i].n = 0u; arr[i].cap = cap; arr[i].limbs = limbs;
    }
    return arr;
}

/* Read the BiPoly under `key` into `out` via the rc191 public reader. */
static srmech_status_t inf_read_bipoly_key(const srmech_json_value_t *root,
        srmech_marshal_arena_t *a, const char *key, uint32_t cap, inf_bipoly_t *out)
{
    const srmech_json_value_t *node;
    assert(root != NULL && a != NULL && key != NULL && out != NULL);
    assert(cap > 0u);
    node = srmech_json_object_get(root, key);
    if (node == NULL) { return SRMECH_ERR_BAD_INPUT; }
    return srmech_carrier_read_bipoly(node, a, cap, &out->num, &out->den,
                                      &out->klen, &out->kdeg);
}

/* Max significant 32-bit limb count over all input coefficients (num + den of
 * all four ratios) — the tight zeilberger cl (never from rel_len, which would
 * over-size the ws to GB). >= 1. */
static uint32_t inf_bipoly_max_limbs(const inf_bipoly_t r[4])
{
    uint32_t m = 1u;
    size_t b, t, tot, i;
    assert(r != NULL);
    assert(sizeof(uint32_t) == 4u);
    for (b = 0u; b < 4u; b++) {
        tot = 0u;
        for (i = 0u; i < r[b].kdeg; i++) { tot += r[b].klen[i]; }
        for (t = 0u; t < tot; t++) {
            if (r[b].num[t].n > m) { m = r[b].num[t].n; }
            if (r[b].den[t].n > m) { m = r[b].den[t].n; }
        }
    }
    return m;
}

/* Allocate the zeilberger output block + ws and run srmech_zeilberger at
 * max_order=1. Sets z->has / z->order / the coeff+cert pointers. */
static srmech_status_t inf_wz_zeilberger(const inf_bipoly_t r[4],
        srmech_marshal_arena_t *a, uint32_t cl, size_t deg, inf_zeil_t *z)
{
    size_t nbound, coeff_slots, cert_slots, wsb, ck = 0u;
    unsigned char *ws;
    uint32_t oc;
    int has = 0; size_t order = 0u;
    srmech_status_t st;
    assert(r != NULL && a != NULL && z != NULL);
    assert(cl > 0u && deg > 0u);
    oc = (uint32_t)srmech_zeilberger_out_cap(cl, 1u, deg);
    nbound = (deg + 2u) * 3u + 8u;                 /* (deg+2)*(order+2), order=1 */
    coeff_slots = 2u * nbound + 8u;                /* (order+1)*nbound           */
    cert_slots = nbound * nbound + 8u;
    z->coeff_n = inf_ma_bigints(a, coeff_slots, oc);
    z->coeff_d = inf_ma_bigints(a, coeff_slots, oc);
    z->cert_n  = inf_ma_bigints(a, cert_slots, oc);
    z->cert_d  = inf_ma_bigints(a, cert_slots, oc);
    z->coeff_nlen = (size_t *)inf_ma_carve(a, 3u * sizeof(size_t));
    z->cert_klen  = (size_t *)inf_ma_carve(a, (nbound + 2u) * sizeof(size_t));
    wsb = srmech_zeilberger_ws_bound(cl, 1u, deg);
    ws = inf_ma_carve(a, wsb);
    if (z->coeff_n == NULL || z->coeff_d == NULL || z->cert_n == NULL ||
        z->cert_d == NULL || z->coeff_nlen == NULL || z->cert_klen == NULL ||
        ws == NULL) { return SRMECH_ERR_OVERFLOW; }
    st = srmech_zeilberger(
        r[0].num, r[0].den, r[0].klen, r[0].kdeg,
        r[1].num, r[1].den, r[1].klen, r[1].kdeg,
        r[2].num, r[2].den, r[2].klen, r[2].kdeg,
        r[3].num, r[3].den, r[3].klen, r[3].kdeg,
        1u, deg, &has, &order, z->coeff_n, z->coeff_d, z->coeff_nlen,
        z->cert_n, z->cert_d, z->cert_klen, &ck, ws, wsb);
    if (st != SRMECH_OK) { return st; }
    z->has = has; z->order = order; z->cert_kdeg = ck; z->out_cap = oc;
    return SRMECH_OK;
}

/* Sets *out_ok = 1 iff the order-1 recurrence is the WZ recurrence
 * a_0(n) + a_1(n) = 0 with a_0, a_1 NONZERO constants in n (both klen == 1),
 * returning a_1 = (num,den) at flat index 1. `cap` sizes the cleared-sum
 * scratch (a0n*a1d + a1n*a0d == 0). */
static srmech_status_t inf_wz_recurrence_ok(const inf_zeil_t *z,
        srmech_marshal_arena_t *a, uint32_t cap,
        const srmech_bigint_t **out_a1n, const srmech_bigint_t **out_a1d, int *out_ok)
{
    const srmech_bigint_t *a0n, *a0d, *a1n, *a1d;
    srmech_bigint_t *t1, *t2, *t3;
    srmech_status_t st;
    assert(z != NULL && a != NULL && out_ok != NULL);
    assert(out_a1n != NULL && out_a1d != NULL);
    *out_ok = 0;
    if (z->coeff_nlen[0] != 1u || z->coeff_nlen[1] != 1u) { return SRMECH_OK; }
    a0n = &z->coeff_n[0]; a0d = &z->coeff_d[0];
    a1n = &z->coeff_n[1]; a1d = &z->coeff_d[1];    /* offset = coeff_nlen[0] = 1 */
    if (a0n->sign == 0 || a1n->sign == 0) { return SRMECH_OK; }
    t1 = inf_ma_bigints(a, 1u, cap);
    t2 = inf_ma_bigints(a, 1u, cap);
    t3 = inf_ma_bigints(a, 1u, cap);
    if (t1 == NULL || t2 == NULL || t3 == NULL) { return SRMECH_ERR_OVERFLOW; }
    st = srmech_bigint_mul(t1, a0n, a1d);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_mul(t2, a1n, a0d);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_add(t3, t1, t2);
    if (st != SRMECH_OK) { return st; }
    if (srmech_bigint_is_zero(t3)) { *out_a1n = a1n; *out_a1d = a1d; *out_ok = 1; }
    return SRMECH_OK;
}

/* Rescale the raw certificate by 1/a_1 (x_num[i] = cert_n[i]*a1d over
 * cert_d[i]*a1n, sign-normalised to a positive denominator; unreduced is fine —
 * srmech_wz_verify clears denominators) and PROVE the WZ equation with
 * x_den = rn_den. Sets *out_equal. */
static srmech_status_t inf_wz_prove(const inf_bipoly_t r[4], const inf_zeil_t *z,
        const srmech_bigint_t *a1n, const srmech_bigint_t *a1d,
        srmech_marshal_arena_t *a, uint32_t cl, size_t deg, int *out_equal)
{
    srmech_bigint_t *xn, *xd;
    size_t total = 0u, alloc, i; uint32_t xcap; unsigned char *ws; size_t wsb;
    int eq = 0; srmech_status_t st;
    assert(r != NULL && z != NULL && a != NULL && out_equal != NULL);
    assert(a1n != NULL && a1d != NULL);
    for (i = 0u; i < z->cert_kdeg; i++) { total += z->cert_klen[i]; }
    alloc = (total == 0u) ? 1u : total;
    xcap = (uint32_t)srmech_bigint_mul_bound(z->out_cap, z->out_cap);
    xn = inf_ma_bigints(a, alloc, xcap);
    xd = inf_ma_bigints(a, alloc, xcap);
    if (xn == NULL || xd == NULL) { return SRMECH_ERR_OVERFLOW; }
    for (i = 0u; i < total; i++) {
        st = srmech_bigint_mul(&xn[i], &z->cert_n[i], a1d);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_mul(&xd[i], &z->cert_d[i], a1n);
        if (st != SRMECH_OK) { return st; }
        if (xd[i].sign < 0) { xd[i].sign = -xd[i].sign; xn[i].sign = -xn[i].sign; }
    }
    wsb = srmech_wz_verify_ws_bound(cl, deg);
    ws = inf_ma_carve(a, wsb);
    if (ws == NULL) { return SRMECH_ERR_OVERFLOW; }
    st = srmech_wz_verify(
        r[0].num, r[0].den, r[0].klen, r[0].kdeg,
        r[1].num, r[1].den, r[1].klen, r[1].kdeg,
        r[2].num, r[2].den, r[2].klen, r[2].kdeg,
        r[3].num, r[3].den, r[3].klen, r[3].kdeg,
        xn, xd, z->cert_klen, z->cert_kdeg,
        r[1].num, r[1].den, r[1].klen, r[1].kdeg,   /* x_den = rn_den */
        &eq, ws, wsb);
    if (st != SRMECH_OK) { return st; }
    *out_equal = eq;
    return SRMECH_OK;
}

/* The SIGMA-DEFINITE (wz_certificate) dispatch: read the four (n,k) BiPoly
 * term-ratios, FIND the order-1 WZ recurrence via srmech_zeilberger, and PROVE
 * the WZ equation via srmech_wz_verify. *out_reducible = 1 iff the identity
 * verifies; a valid-but-not-WZ relationship sets 0 + returns OK (honest OPEN).
 * Non-OK ONLY on arena / reducer failure (-> the pure wz_certificate). */
static srmech_status_t inf_sigma_wz(const srmech_json_value_t *root,
        srmech_marshal_arena_t *a, size_t rel_len, int *out_reducible)
{
    inf_bipoly_t r[4]; inf_zeil_t z;
    const srmech_bigint_t *a1n = NULL, *a1d = NULL;
    static const char *const keys[4] = {"rn_num", "rn_den", "rk_num", "rk_den"};
    uint32_t cap, cl; size_t deg = 1u, i; int ok = 0, eq = 0; srmech_status_t st;
    assert(root != NULL && a != NULL && out_reducible != NULL);
    assert(rel_len > 0u);
    *out_reducible = 0;
    cap = (uint32_t)(srmech_bigint_from_dec_bound(rel_len) + 8u);
    for (i = 0u; i < 4u; i++) {
        st = inf_read_bipoly_key(root, a, keys[i], cap, &r[i]);
        if (st != SRMECH_OK) { return st; }
    }
    if (r[1].kdeg == 0u || r[3].kdeg == 0u) { return SRMECH_ERR_BAD_INPUT; }
    for (i = 0u; i < 4u; i++) { if (r[i].kdeg > deg) { deg = r[i].kdeg; } }
    cl = inf_bipoly_max_limbs(r);
    st = inf_wz_zeilberger(r, a, cl, deg, &z);
    if (st != SRMECH_OK) { return st; }
    if (!z.has || z.order != 1u) { return SRMECH_OK; }   /* not order-1 -> OPEN */
    st = inf_wz_recurrence_ok(&z, a,
            (uint32_t)srmech_bigint_mul_bound(z.out_cap, z.out_cap), &a1n, &a1d, &ok);
    if (st != SRMECH_OK) { return st; }
    if (!ok) { return SRMECH_OK; }                       /* not WZ recurrence -> OPEN */
    st = inf_wz_prove(r, &z, a1n, a1d, a, cl, deg, &eq);
    if (st != SRMECH_OK) { return st; }
    *out_reducible = eq ? 1 : 0;
    return SRMECH_OK;
}

/* ------------------------------------------------------------------
 * Emit + top-level entry.
 * ------------------------------------------------------------------ */

/* Copy a fixed decision literal into out (no trailing NUL). OVERFLOW if too big. */
static srmech_status_t inf_emit(char *out, size_t out_cap, size_t *out_len,
                                const char *lit)
{
    size_t n;
    assert(out != NULL && out_len != NULL && lit != NULL);
    assert(out_cap > 0u);
    n = strlen(lit);
    if (n > out_cap) { return SRMECH_ERR_OVERFLOW; }
    memcpy(out, lit, n);
    *out_len = n;
    return SRMECH_OK;
}

/* Minimum caller-arena BYTES srmech_infer needs for a `rel_len`-byte JSON
 * relationship whose largest operand carries `max_terms` coefficients (the
 * gosper term-ratio degree; 1 for cyclic). The gosper ws grows super-linearly in
 * the DEGREE, so the arena is sized on the ACTUAL coefficient count, NOT on
 * rel_len (bytes) — exactly as srmech.amsc._native.gosper_c sizes ws from
 * max(n_num, n_den). A generous static over-approximation; too small ->
 * OVERFLOW -> the pure path. No malloc; the caller owns the arena. */
size_t srmech_infer_arena_bytes(size_t rel_len, size_t max_terms)
{
    size_t digits = rel_len + 32u;
    size_t limbs = srmech_bigint_from_dec_bound(digits);
    size_t degree = max_terms < 1u ? 1u : max_terms;   /* the ACTUAL coeff count */
    size_t bi = sizeof(srmech_bigint_t);
    size_t parse = 160u * rel_len + 65536u;
    size_t one_cap = 32u * (INF_ONE_TERMS + 2u * digits) + 256u;
    size_t one_ws = srmech_the_one_ws_bound(limbs, limbs, INF_ONE_TERMS);
    size_t cyclic = one_ws + 2u * INF_ONE_DIM * (bi + one_cap * 4u)
                  + 8u * (bi + limbs * 4u) + 8192u;
    size_t g_cap = srmech_gosper_out_cap(limbs, degree);
    size_t g_ws = srmech_gosper_ws_bound(limbs, degree);
    size_t g_car = 6u * (degree + 2u);
    size_t gosper = g_ws + g_car * (bi + g_cap * 4u) + 8192u;
    size_t work = cyclic > gosper ? cyclic : gosper;
    assert(bi <= 64u);
    assert(limbs > 0u);
    return parse + work + 65536u;
}

/* Minimum caller-arena BYTES for the SIGMA-DEFINITE (wz_certificate) row (rc192)
 * over a `rel_len`-byte JSON whose four (n,k) BiPoly term-ratios carry a max
 * k-degree `max_terms` and a max coefficient of `coeff_limbs` significant 32-bit
 * limbs. The zeilberger creative-telescoping scratch dominates and grows in
 * BOTH the degree AND the coefficient-limb count, so this is sized on the ACTUAL
 * coefficient limbs (from the marshalled operand) — NOT on rel_len, which would
 * over-size the ws to GB (the same "size on the real shape" contract as the
 * gosper arena). A generous static over-approximation; too small -> OVERFLOW ->
 * the pure wz_certificate. No malloc; the caller owns the arena. This is a
 * SEPARATE sizer from srmech_infer_arena_bytes so the cheap cyclic / gosper rows
 * never pay the MB-scale zeilberger floor. */
size_t srmech_infer_sigma_definite_arena_bytes(size_t rel_len, size_t max_terms,
                                               size_t coeff_limbs)
{
    size_t read_cap = srmech_bigint_from_dec_bound(rel_len) + 8u;
    size_t cl = coeff_limbs < 1u ? 1u : coeff_limbs;
    size_t deg = max_terms < 1u ? 1u : max_terms;
    size_t oc = srmech_zeilberger_out_cap(cl, 1u, deg);
    size_t z_ws = srmech_zeilberger_ws_bound(cl, 1u, deg);
    size_t w_ws = srmech_wz_verify_ws_bound(cl, deg);
    size_t nbound = (deg + 2u) * 3u + 8u;
    size_t coeff_slots = 2u * nbound + 8u;
    size_t cert_slots = nbound * nbound + 8u;
    size_t bi = sizeof(srmech_bigint_t);
    size_t parse = 160u * rel_len + 65536u;
    size_t inputs = 8u * (rel_len + 8u) * (bi + read_cap * 4u);
    size_t outputs = 2u * (coeff_slots + cert_slots) * (bi + oc * 4u);
    size_t xcap = srmech_bigint_mul_bound(oc, oc);
    size_t xnum = 2u * cert_slots * (bi + xcap * 4u);
    size_t scratch = 8u * (bi + xcap * 4u);
    assert(bi <= 64u);
    assert(cl > 0u);
    return parse + z_ws + w_ws + inputs + outputs + xnum + scratch + 262144u;
}

/* Route a stored relationship: parse JSON, detect the row from the marshalled
 * operand structure (term_ratio_* -> gosper; sigma -> cyclic), dispatch + verify
 * the C reducer, and emit the DECISION literal. Any other structure / malformed
 * operand / overflow -> non-OK (-> the Python pure infer). */
srmech_status_t srmech_infer(const char *rel_json, size_t rel_len,
                             void *ws, size_t ws_len,
                             char *out, size_t out_cap, size_t *out_len)
{
    inf_bump_t b;
    srmech_json_value_t *root = NULL;
    const srmech_json_value_t *g, *cyc, *rn;
    unsigned char *pa;
    size_t pj;
    const char *lit;
    int red = 0;
    srmech_status_t st;
    assert(out_len != NULL);
    assert(rel_json != NULL || rel_len == 0u);
    if (rel_json == NULL || ws == NULL || out == NULL || out_len == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    b.cur = (unsigned char *)ws; b.end = b.cur + ws_len;
    pj = 160u * rel_len + 65536u;
    pa = inf_carve(&b, pj);
    if (pa == NULL) { return SRMECH_ERR_OVERFLOW; }
    st = srmech_json_parse(rel_json, rel_len, pa, pj, &root);
    if (st != SRMECH_OK) { return st; }
    if (root == NULL || root->type != SRMECH_JSON_OBJECT) {
        return SRMECH_ERR_BAD_INPUT;
    }
    rn = srmech_json_object_get(root, "rn_num");
    g = srmech_json_object_get(root, "term_ratio_num");
    cyc = srmech_json_object_get(root, "sigma");
    if (rn != NULL) {                       /* SIGMA-DEFINITE (wz) row — rc192   */
        srmech_marshal_arena_t ma;
        srmech_marshal_arena_init(&ma, b.cur, (size_t)(b.end - b.cur));
        st = inf_sigma_wz(root, &ma, rel_len, &red);
        lit = red
            ? "{\"reducer\":\"wz_certificate\",\"reducible\":true,\"row\":\"sigma\",\"verified\":true}"
            : "{\"reducible\":false,\"row\":\"sigma\"}";
    } else if (g != NULL) {
        st = inf_gosper(root, &b, &red);
        lit = red
            ? "{\"reducer\":\"gosper\",\"reducible\":true,\"row\":\"sigma\",\"verified\":true}"
            : "{\"reducible\":false,\"row\":\"sigma\"}";
    } else if (cyc != NULL) {
        st = inf_cyclic(root, &b, &red);
        lit = red
            ? "{\"reducer\":\"the_one\",\"reducible\":true,\"row\":\"cyclic\",\"verified\":true}"
            : "{\"reducible\":false,\"row\":\"cyclic\"}";
    } else {
        return SRMECH_ERR_BAD_INPUT;   /* not a rc176 clean row -> pure infer */
    }
    if (st != SRMECH_OK) { return st; }
    return inf_emit(out, out_cap, out_len, lit);
}
