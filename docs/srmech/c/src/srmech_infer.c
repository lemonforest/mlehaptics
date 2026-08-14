/* srmech_infer.c — the F929 OPEN/infer ROUTER in C (0.9.0rc176; the
 * ORCHESTRATION->C spine, batch 6; the CARRIER-FFI foundation).
 *
 * The C peer of srmech.math.dispatch.infer — the META-dispatcher over srmech's
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
 * rc192 added the sigma-definite wz row; rc223 the sigma_multivar / sigma_q /
 * sigma_elliptic exact-Q rows; rc224 the SPECTRAL row — the LAST #796 row:
 *   * spectral     — operand = a coupling-Laplacian payload (edges(+weights,n)
 *                  / an explicit matrix / an adjacency grid) whose f64 leaves
 *                  ride the wire as IEEE-754 BIT PATTERNS (signed int64 — the
 *                  bit-EXACT float wire; no decimal float parse in the
 *                  decision path). Build L in C (edges -> the Class-L
 *                  srmech_graph_dense_laplacian kernel, the SAME builder the
 *                  pure path dispatches to; matrix -> the raw grid;
 *                  adjacency -> the in-place D-A transform in the pure
 *                  _build_laplacian's exact float-op order) and decide the
 *                  STRUCTURAL verdict: reducible iff L is bit-exact
 *                  real-symmetric (L[i][j] == L[j][i] IEEE equality over all
 *                  pairs — the spectral theorem's own hypothesis). NO
 *                  eigensolve, NO resonant_spectrum call, NO float tolerance
 *                  in the C decision path: the eigenvalue payload is
 *                  re-derived pure-side by _finish_native. Because the
 *                  verdict is a symmetry PREDICATE over bit-identical
 *                  operands, the native decision equals the pure decision on
 *                  EVERY platform by construction (the Python marshal
 *                  declines non-finite leaves to pure, so no NaN can arise
 *                  from finite accumulation and break self-equality
 *                  asymmetrically).
 *
 * rc103 inform-don't-limit: ANY other row (the elliptic-multivar Cn Jackson,
 * whose per-call proof is carrier-symbolic), any malformed operand, or any
 * arena overflow -> non-OK, and the Python caller runs the COMPLETE pure infer
 * (never a wrong answer; NEVER a false reducible). The honest OPEN residue IS
 * the no-hallucination discipline: the C path returns "not reducible"
 * identically, never a fabricated reduction.
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
#define INF_ONE_TERMS 24u       /* DEFAULT_TERMS in srmech.cascade.one */

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
 * term-ratios, then reproduces srmech.apokatastasis.wz_certificate.wz_certificate in C:
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
 * rc223 (#796): the three remaining EXACT-Q rows, over the rc223 public
 * carrier readers srmech_carrier_read_{tripoly,qbipoly,ellratio}.
 *
 *   * sigma_multivar -> srmech_apagodu_zeilberger @max_order=1 (has=1 IS the
 *     verification; has=0 is NOT definitive -> non-OK -> pure).
 *   * sigma_q DEFINITE -> FIND srmech_q_zeilberger @order-1 + the q-WZ shape
 *     + PROVE srmech_q_wz_verify (the COMPLETE mirror) on the 1/a1-rescaled
 *     certificate. A FIND decline -> non-OK -> pure; a found-but-not-WZ /
 *     verify-fail -> reducible:false (definitive within the byte-identical
 *     k-free FIND class).
 *   * sigma_q INDEFINITE -> srmech_q_gosper (has=1 IS the verification;
 *     has=0 -> non-OK -> pure — the constant-ratio native scope declines).
 *   * sigma_elliptic -> srmech_elliptic_wz_certificate (has=1 IS the
 *     verification; has=0 -> non-OK -> pure, the conservative fall).
 *
 * NEVER a false reducible: every reducible:true is the reducer's OWN verified
 * contract, and the rows whose C reducer declines non-definitively never emit
 * reducible:false — they return non-OK so the COMPLETE pure infer decides.
 * ------------------------------------------------------------------ */

/* A TriPoly operand read from the wire (flat j-major/k/n num/den + nlen grid). */
typedef struct {
    srmech_bigint_t *num;
    srmech_bigint_t *den;
    size_t          *nlen;
    size_t           jdeg;
    size_t           kdeg;
} inf_tripoly_t;

/* A QBiPoly operand read from the wire (flat Y-major/X-major q-runs). */
typedef struct {
    srmech_bigint_t *num;
    srmech_bigint_t *den;
    size_t          *qlen;
    int64_t         *xlow;
    size_t          *xcells;
    size_t           ycells;
} inf_qbipoly_t;

/* Read the TriPoly under `key` into `out` via the rc223 public reader. */
static srmech_status_t inf_read_tripoly_key(const srmech_json_value_t *root,
        srmech_marshal_arena_t *a, const char *key, uint32_t cap,
        inf_tripoly_t *out)
{
    const srmech_json_value_t *node;
    assert(root != NULL && a != NULL && key != NULL && out != NULL);
    assert(cap > 0u);
    node = srmech_json_object_get(root, key);
    if (node == NULL) { return SRMECH_ERR_BAD_INPUT; }
    return srmech_carrier_read_tripoly(node, a, cap, &out->num, &out->den,
                                       &out->nlen, &out->jdeg, &out->kdeg);
}

/* Read the QBiPoly under `key` into `out` via the rc223 public reader. */
static srmech_status_t inf_read_qbipoly_key(const srmech_json_value_t *root,
        srmech_marshal_arena_t *a, const char *key, uint32_t cap,
        inf_qbipoly_t *out)
{
    const srmech_json_value_t *node;
    assert(root != NULL && a != NULL && key != NULL && out != NULL);
    assert(cap > 0u);
    node = srmech_json_object_get(root, key);
    if (node == NULL) { return SRMECH_ERR_BAD_INPUT; }
    return srmech_carrier_read_qbipoly(node, a, cap, &out->num, &out->den,
                                       &out->qlen, &out->xlow, &out->xcells,
                                       &out->ycells);
}

/* Max significant limb count + max shape envelope over `nr` TriPoly operands
 * (the tight apagodu cl/deg — sized on the ACTUAL coefficients, never rel_len). */
static void inf_tri_stats(const inf_tripoly_t *r, size_t nr,
                          uint32_t *out_cl, size_t *out_deg)
{
    uint32_t m = 1u;
    size_t b, i, t, tot, deg = 1u;
    assert(r != NULL && out_cl != NULL);
    assert(out_deg != NULL && nr > 0u);
    for (b = 0u; b < nr; b++) {
        tot = 0u;
        if (r[b].jdeg > deg) { deg = r[b].jdeg; }
        if (r[b].kdeg > deg) { deg = r[b].kdeg; }
        for (i = 0u; i < r[b].jdeg * r[b].kdeg; i++) {
            if (r[b].nlen[i] > deg) { deg = r[b].nlen[i]; }
            tot += r[b].nlen[i];
        }
        for (t = 0u; t < tot; t++) {
            if (r[b].num[t].n > m) { m = r[b].num[t].n; }
            if (r[b].den[t].n > m) { m = r[b].den[t].n; }
        }
    }
    *out_cl = m;
    *out_deg = deg;
}

/* Max significant limb count + max shape envelope (ycells / xcells / qlen —
 * the Python _qbi_degree) over `nr` QBiPoly operands. */
static void inf_qbi_stats(const inf_qbipoly_t *r, size_t nr,
                          uint32_t *out_cl, size_t *out_deg)
{
    uint32_t m = 1u;
    size_t b, y, c, t, cells, tot, deg = 1u;
    assert(r != NULL && out_cl != NULL);
    assert(out_deg != NULL && nr > 0u);
    for (b = 0u; b < nr; b++) {
        cells = 0u;
        if (r[b].ycells > deg) { deg = r[b].ycells; }
        for (y = 0u; y < r[b].ycells; y++) {
            if (r[b].xcells[y] > deg) { deg = r[b].xcells[y]; }
            cells += r[b].xcells[y];
        }
        tot = 0u;
        for (c = 0u; c < cells; c++) {
            if (r[b].qlen[c] > deg) { deg = r[b].qlen[c]; }
            tot += r[b].qlen[c];
        }
        for (t = 0u; t < tot; t++) {
            if (r[b].num[t].n > m) { m = r[b].num[t].n; }
            if (r[b].den[t].n > m) { m = r[b].den[t].n; }
        }
    }
    *out_cl = m;
    *out_deg = deg;
}

/* ------------------------------------------------------------------
 * SIGMA-MULTIVAR row (apagodu_zeilberger).
 * ------------------------------------------------------------------ */

/* The apagodu output block (recurrence + the two certificate grids). */
typedef struct {
    srmech_bigint_t *coeff_n, *coeff_d; size_t *coeff_nlen;
    srmech_bigint_t *cj_n, *cj_d; size_t *cj_nlen;
    srmech_bigint_t *ck_n, *ck_d; size_t *ck_nlen;
    unsigned char *ws; size_t wsb;
} inf_az_out_t;

/* Carve the apagodu output block + ws off `a` (order = 1). NULL-slot -> the
 * caller returns OVERFLOW -> pure. Mirrors apagodu_zeilberger_c's sizing. */
static srmech_status_t inf_az_alloc(srmech_marshal_arena_t *a, uint32_t cl,
                                    size_t deg, inf_az_out_t *z)
{
    size_t nbound, cells, coeff_slots, cert_slots;
    uint32_t oc;
    assert(a != NULL && z != NULL);
    assert(cl > 0u && deg > 0u);
    oc = (uint32_t)srmech_apagodu_zeilberger_out_cap(cl, 1u, deg);
    nbound = (deg + 2u) * 3u + 8u;                 /* (deg+2)*(order+2), order=1 */
    cells = (deg + 4u) * (deg + 4u) + 8u;
    coeff_slots = 2u * nbound + 8u;
    cert_slots = cells * nbound + 8u;
    z->coeff_n = inf_ma_bigints(a, coeff_slots, oc);
    z->coeff_d = inf_ma_bigints(a, coeff_slots, oc);
    z->cj_n = inf_ma_bigints(a, cert_slots, oc);
    z->cj_d = inf_ma_bigints(a, cert_slots, oc);
    z->ck_n = inf_ma_bigints(a, cert_slots, oc);
    z->ck_d = inf_ma_bigints(a, cert_slots, oc);
    z->coeff_nlen = (size_t *)inf_ma_carve(a, 4u * sizeof(size_t));
    z->cj_nlen = (size_t *)inf_ma_carve(a, (cells + 2u) * sizeof(size_t));
    z->ck_nlen = (size_t *)inf_ma_carve(a, (cells + 2u) * sizeof(size_t));
    z->wsb = srmech_apagodu_zeilberger_ws_bound(cl, 1u, deg);
    z->ws = inf_ma_carve(a, z->wsb);
    if (z->coeff_n == NULL || z->coeff_d == NULL || z->cj_n == NULL ||
        z->cj_d == NULL || z->ck_n == NULL || z->ck_d == NULL ||
        z->coeff_nlen == NULL || z->cj_nlen == NULL || z->ck_nlen == NULL ||
        z->ws == NULL) { return SRMECH_ERR_OVERFLOW; }
    return SRMECH_OK;
}

/* The SIGMA-MULTIVAR dispatch: read the six (n,j,k) TriPoly term-ratios, run
 * srmech_apagodu_zeilberger @max_order=1; a has=1 minimal-order recurrence IS
 * the verification (the non-None-is-the-proof contract). has=0 is NOT
 * definitive (the C peer declines above order 1) -> BAD_INPUT -> pure. */
static srmech_status_t inf_sigma_multivar(const srmech_json_value_t *root,
        srmech_marshal_arena_t *a, size_t rel_len, int *out_reducible)
{
    inf_tripoly_t r[6]; inf_az_out_t z;
    static const char *const keys[6] = {"rn_num", "rn_den", "rj_num", "rj_den",
                                        "rk_num", "rk_den"};
    uint32_t cap, cl; size_t deg = 1u, i, order = 0u;
    size_t cjj = 0u, cjk = 0u, ckj = 0u, ckk = 0u;
    int has = 0; srmech_status_t st;
    assert(root != NULL && a != NULL && out_reducible != NULL);
    assert(rel_len > 0u);
    *out_reducible = 0;
    cap = (uint32_t)(srmech_bigint_from_dec_bound(rel_len) + 8u);
    for (i = 0u; i < 6u; i++) {
        st = inf_read_tripoly_key(root, a, keys[i], cap, &r[i]);
        if (st != SRMECH_OK) { return st; }
    }
    if (r[1].jdeg == 0u || r[3].jdeg == 0u || r[5].jdeg == 0u) {
        return SRMECH_ERR_BAD_INPUT;                 /* a zero denominator      */
    }
    inf_tri_stats(r, 6u, &cl, &deg);
    st = inf_az_alloc(a, cl, deg, &z);
    if (st != SRMECH_OK) { return st; }
    st = srmech_apagodu_zeilberger(
        r[0].num, r[0].den, r[0].nlen, r[0].jdeg, r[0].kdeg,
        r[1].num, r[1].den, r[1].nlen, r[1].jdeg, r[1].kdeg,
        r[2].num, r[2].den, r[2].nlen, r[2].jdeg, r[2].kdeg,
        r[3].num, r[3].den, r[3].nlen, r[3].jdeg, r[3].kdeg,
        r[4].num, r[4].den, r[4].nlen, r[4].jdeg, r[4].kdeg,
        r[5].num, r[5].den, r[5].nlen, r[5].jdeg, r[5].kdeg,
        1u, deg, &has, &order,
        z.coeff_n, z.coeff_d, z.coeff_nlen,
        z.cj_n, z.cj_d, z.cj_nlen, &cjj, &cjk,
        z.ck_n, z.ck_d, z.ck_nlen, &ckj, &ckk,
        z.ws, z.wsb);
    if (st != SRMECH_OK) { return st; }
    if (!has) { return SRMECH_ERR_BAD_INPUT; }       /* NOT definitive -> pure  */
    *out_reducible = 1;
    return SRMECH_OK;
}

/* ------------------------------------------------------------------
 * SIGMA-Q row — the DEFINITE (q_wz_certificate) sub-case.
 * ------------------------------------------------------------------ */

/* The srmech_q_zeilberger output block (order-1 q-recurrence + certificate). */
typedef struct {
    srmech_bigint_t *coeff_n, *coeff_d;
    size_t *coeff_qlen; int64_t *coeff_xlow; size_t *coeff_xcells;
    size_t coeff_count;
    srmech_bigint_t *cert_n, *cert_d;
    size_t *cert_qlen; int64_t *cert_xlow; size_t *cert_xcells;
    size_t cert_ycells;
    int has; size_t order; uint32_t out_cap;
} inf_qzeil_t;

/* Allocate the q-zeilberger output block + ws and run srmech_q_zeilberger at
 * max_order=1. Mirrors q_zeilberger_c's slot sizing. */
static srmech_status_t inf_qwz_zeilberger(const inf_qbipoly_t r[4],
        srmech_marshal_arena_t *a, uint32_t cl, size_t qdeg, inf_qzeil_t *z)
{
    size_t coeff_total, cert_total, cell_q_cap, cc = 0u, cy = 0u;
    int has = 0; size_t order = 0u;
    srmech_status_t st;
    assert(r != NULL && a != NULL && z != NULL);
    assert(cl > 0u && qdeg > 0u);
    z->out_cap = (uint32_t)srmech_q_zeilberger_out_cap(cl, 1u, qdeg);
    cell_q_cap = qdeg + 4u;
    coeff_total = 3u * cell_q_cap + 8u;              /* (max_order+2) cells     */
    cert_total = (qdeg + 4u) * cell_q_cap + 8u;
    z->coeff_n = inf_ma_bigints(a, coeff_total, z->out_cap);
    z->coeff_d = inf_ma_bigints(a, coeff_total, z->out_cap);
    z->cert_n = inf_ma_bigints(a, cert_total, z->out_cap);
    z->cert_d = inf_ma_bigints(a, cert_total, z->out_cap);
    z->coeff_qlen = (size_t *)inf_ma_carve(a, 5u * sizeof(size_t));
    z->coeff_xlow = (int64_t *)inf_ma_carve(a, 5u * sizeof(int64_t));
    z->coeff_xcells = (size_t *)inf_ma_carve(a, 5u * sizeof(size_t));
    z->cert_qlen = (size_t *)inf_ma_carve(a, (qdeg + 8u) * sizeof(size_t));
    z->cert_xlow = (int64_t *)inf_ma_carve(a, (qdeg + 8u) * sizeof(int64_t));
    z->cert_xcells = (size_t *)inf_ma_carve(a, (qdeg + 8u) * sizeof(size_t));
    {
        size_t wsb = srmech_q_zeilberger_ws_bound(cl, 1u, qdeg);
        unsigned char *ws = inf_ma_carve(a, wsb);
        if (z->coeff_n == NULL || z->coeff_d == NULL || z->cert_n == NULL ||
            z->cert_d == NULL || z->coeff_qlen == NULL || z->coeff_xlow == NULL ||
            z->coeff_xcells == NULL || z->cert_qlen == NULL ||
            z->cert_xlow == NULL || z->cert_xcells == NULL || ws == NULL) {
            return SRMECH_ERR_OVERFLOW;
        }
        st = srmech_q_zeilberger(
            r[0].num, r[0].den, r[0].qlen, r[0].xlow, r[0].xcells, r[0].ycells,
            r[1].num, r[1].den, r[1].qlen, r[1].xlow, r[1].xcells, r[1].ycells,
            r[2].num, r[2].den, r[2].qlen, r[2].xlow, r[2].xcells, r[2].ycells,
            r[3].num, r[3].den, r[3].qlen, r[3].xlow, r[3].xcells, r[3].ycells,
            1u, &has, &order,
            z->coeff_n, z->coeff_d, z->coeff_qlen, z->coeff_xlow,
            z->coeff_xcells, &cc,
            z->cert_n, z->cert_d, z->cert_qlen, z->cert_xlow,
            z->cert_xcells, &cy, ws, wsb);
    }
    if (st != SRMECH_OK) { return st; }
    z->has = has; z->order = order; z->coeff_count = cc; z->cert_ycells = cy;
    return SRMECH_OK;
}

/* Sets *out_ok = 1 iff the order-1 q-recurrence is the q-WZ recurrence
 * a_0 + a_1 = 0 with both coefficients NONZERO rational SCALARS (single X^0
 * cell, q-degree 0 — the Python _is_wz_recurrence mirror). Returns a_1 at
 * flat index 1. `cap` sizes the cleared-sum scratch. */
static srmech_status_t inf_qwz_recurrence_ok(const inf_qzeil_t *z,
        srmech_marshal_arena_t *a, uint32_t cap,
        const srmech_bigint_t **out_a1n, const srmech_bigint_t **out_a1d,
        int *out_ok)
{
    const srmech_bigint_t *a0n, *a0d, *a1n, *a1d;
    srmech_bigint_t *t1, *t2, *t3;
    srmech_status_t st;
    assert(z != NULL && a != NULL && out_ok != NULL);
    assert(out_a1n != NULL && out_a1d != NULL);
    *out_ok = 0;
    if (z->coeff_count != 2u) { return SRMECH_OK; }
    if (z->coeff_xlow[0] != 0 || z->coeff_xlow[1] != 0 ||
        z->coeff_xcells[0] != 1u || z->coeff_xcells[1] != 1u ||
        z->coeff_qlen[0] != 1u || z->coeff_qlen[1] != 1u) { return SRMECH_OK; }
    a0n = &z->coeff_n[0]; a0d = &z->coeff_d[0];
    a1n = &z->coeff_n[1]; a1d = &z->coeff_d[1];      /* offset = qlen[0] = 1    */
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

/* Rescale the raw q-certificate by 1/a_1 (x_num[i] = cert_n[i]*a1d over
 * cert_d[i]*a1n, sign-normalised to a positive denominator; unreduced is fine —
 * srmech_q_wz_verify clears denominators) and PROVE the q-WZ equation with
 * x_den = qrn_den. Sets *out_equal. */
static srmech_status_t inf_qwz_prove(const inf_qbipoly_t r[4],
        const inf_qzeil_t *z, const srmech_bigint_t *a1n,
        const srmech_bigint_t *a1d, srmech_marshal_arena_t *a, size_t qdeg,
        int *out_equal)
{
    srmech_bigint_t *xn, *xd;
    size_t cells = 0u, total = 0u, alloc, i, wsb; uint32_t xcap, clv = 1u;
    unsigned char *ws; int eq = 0; srmech_status_t st;
    assert(r != NULL && z != NULL && a != NULL && out_equal != NULL);
    assert(a1n != NULL && a1d != NULL);
    for (i = 0u; i < z->cert_ycells; i++) { cells += z->cert_xcells[i]; }
    for (i = 0u; i < cells; i++) { total += z->cert_qlen[i]; }
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
        if (xn[i].n > clv) { clv = xn[i].n; }
        if (xd[i].n > clv) { clv = xd[i].n; }
    }
    inf_qbi_stats(r, 4u, &xcap, &i);                 /* reuse: input cl / deg   */
    if (xcap > clv) { clv = xcap; }
    if (i > qdeg) { qdeg = i; }
    if (z->cert_ycells > qdeg) { qdeg = z->cert_ycells; }
    wsb = srmech_q_wz_verify_ws_bound(clv, qdeg);
    ws = inf_ma_carve(a, wsb);
    if (ws == NULL) { return SRMECH_ERR_OVERFLOW; }
    st = srmech_q_wz_verify(
        r[0].num, r[0].den, r[0].qlen, r[0].xlow, r[0].xcells, r[0].ycells,
        r[1].num, r[1].den, r[1].qlen, r[1].xlow, r[1].xcells, r[1].ycells,
        r[2].num, r[2].den, r[2].qlen, r[2].xlow, r[2].xcells, r[2].ycells,
        r[3].num, r[3].den, r[3].qlen, r[3].xlow, r[3].xcells, r[3].ycells,
        xn, xd, z->cert_qlen, z->cert_xlow, z->cert_xcells, z->cert_ycells,
        r[1].num, r[1].den, r[1].qlen, r[1].xlow, r[1].xcells, r[1].ycells,
        &eq, ws, wsb);
    if (st != SRMECH_OK) { return st; }
    *out_equal = eq;
    return SRMECH_OK;
}

/* The SIGMA-Q DEFINITE (q_wz_certificate) dispatch: read the four (X,Y)
 * QBiPoly q-term-ratios, FIND via srmech_q_zeilberger @order-1, accept only
 * the q-WZ shape, PROVE via srmech_q_wz_verify. A FIND decline (has=0 — the
 * k-free native scope) -> BAD_INPUT -> pure (NOT definitive); a found-but-
 * not-WZ / verify-fail -> *out_reducible = 0 + OK (definitive: the k-free
 * FIND class is byte-identical to pure, and the verify is a complete mirror). */
static srmech_status_t inf_sigma_q_wz(const srmech_json_value_t *root,
        srmech_marshal_arena_t *a, size_t rel_len, int *out_reducible)
{
    inf_qbipoly_t r[4]; inf_qzeil_t z;
    const srmech_bigint_t *a1n = NULL, *a1d = NULL;
    static const char *const keys[4] = {"qrn_num", "qrn_den", "qrk_num",
                                        "qrk_den"};
    uint32_t cap, cl; size_t qdeg = 1u, i;
    int ok = 0, eq = 0; srmech_status_t st;
    assert(root != NULL && a != NULL && out_reducible != NULL);
    assert(rel_len > 0u);
    *out_reducible = 0;
    cap = (uint32_t)(srmech_bigint_from_dec_bound(rel_len) + 8u);
    for (i = 0u; i < 4u; i++) {
        st = inf_read_qbipoly_key(root, a, keys[i], cap, &r[i]);
        if (st != SRMECH_OK) { return st; }
    }
    if (r[1].ycells == 0u || r[3].ycells == 0u) { return SRMECH_ERR_BAD_INPUT; }
    inf_qbi_stats(r, 4u, &cl, &qdeg);
    st = inf_qwz_zeilberger(r, a, cl, qdeg, &z);
    if (st != SRMECH_OK) { return st; }
    if (!z.has || z.order != 1u) { return SRMECH_ERR_BAD_INPUT; } /* -> pure   */
    st = inf_qwz_recurrence_ok(&z, a,
            (uint32_t)srmech_bigint_mul_bound(z.out_cap, z.out_cap),
            &a1n, &a1d, &ok);
    if (st != SRMECH_OK) { return st; }
    if (!ok) { return SRMECH_OK; }              /* not the q-WZ shape -> OPEN  */
    st = inf_qwz_prove(r, &z, a1n, a1d, a, qdeg, &eq);
    if (st != SRMECH_OK) { return st; }
    *out_reducible = eq ? 1 : 0;
    return SRMECH_OK;
}

/* ------------------------------------------------------------------
 * SIGMA-Q row — the INDEFINITE (q_gosper) sub-case.
 * ------------------------------------------------------------------ */

/* The SIGMA-Q INDEFINITE dispatch: the QPoly q-term-ratio rides as a ONE-Y-cell
 * QBiPoly wire; run srmech_q_gosper. has=1 IS the verification (a q-hyper-
 * geometric antidifference exists); has=0 is NOT definitive (the constant-
 * ratio native scope declines) -> BAD_INPUT -> pure. */
static srmech_status_t inf_sigma_q_gosper(const srmech_json_value_t *root,
        srmech_marshal_arena_t *a, size_t rel_len, int *out_reducible)
{
    inf_qbipoly_t num, den;
    srmech_bigint_t *rn_n, *rn_d, *rd_n, *rd_d;
    size_t *rn_q, *rd_q, qdeg = 1u, cert_cap, wsb, rn_cells = 0u, rd_cells = 0u;
    int64_t rn_xlow = 0, rd_xlow = 0;
    uint32_t cap, cl, oc; unsigned char *ws; int has = 0;
    srmech_status_t st;
    assert(root != NULL && a != NULL && out_reducible != NULL);
    assert(rel_len > 0u);
    *out_reducible = 0;
    cap = (uint32_t)(srmech_bigint_from_dec_bound(rel_len) + 8u);
    st = inf_read_qbipoly_key(root, a, "q_term_ratio_num", cap, &num);
    if (st != SRMECH_OK) { return st; }
    st = inf_read_qbipoly_key(root, a, "q_term_ratio_den", cap, &den);
    if (st != SRMECH_OK) { return st; }
    if (num.ycells != 1u || den.ycells != 1u || den.xcells[0] == 0u) {
        return SRMECH_ERR_BAD_INPUT;                 /* not the QPoly wire      */
    }
    {
        inf_qbipoly_t both[2]; both[0] = num; both[1] = den;
        inf_qbi_stats(both, 2u, &cl, &qdeg);
    }
    oc = (uint32_t)srmech_q_gosper_out_cap(cl, qdeg);
    cert_cap = qdeg + 4u;
    rn_n = inf_ma_bigints(a, cert_cap, oc); rn_d = inf_ma_bigints(a, cert_cap, oc);
    rd_n = inf_ma_bigints(a, cert_cap, oc); rd_d = inf_ma_bigints(a, cert_cap, oc);
    rn_q = (size_t *)inf_ma_carve(a, 4u * sizeof(size_t));
    rd_q = (size_t *)inf_ma_carve(a, 4u * sizeof(size_t));
    wsb = srmech_q_gosper_ws_bound(cl, qdeg);
    ws = inf_ma_carve(a, wsb);
    if (rn_n == NULL || rn_d == NULL || rd_n == NULL || rd_d == NULL ||
        rn_q == NULL || rd_q == NULL || ws == NULL) { return SRMECH_ERR_OVERFLOW; }
    st = srmech_q_gosper(num.num, num.den, num.qlen, num.xcells[0], num.xlow[0],
                         den.num, den.den, den.qlen, den.xcells[0], den.xlow[0],
                         &has, rn_n, rn_d, rn_q, &rn_cells, &rn_xlow,
                         rd_n, rd_d, rd_q, &rd_cells, &rd_xlow, ws, wsb);
    if (st != SRMECH_OK) { return st; }
    if (!has) { return SRMECH_ERR_BAD_INPUT; }       /* NOT definitive -> pure  */
    *out_reducible = 1;
    return SRMECH_OK;
}

/* ------------------------------------------------------------------
 * SIGMA-ELLIPTIC row (elliptic_wz_certificate).
 * ------------------------------------------------------------------ */

/* The SIGMA-ELLIPTIC dispatch: read the PRE-INTERNED EllRatio wire and run
 * srmech_elliptic_wz_certificate — has=1 iff the 8w7 is recognized AND the
 * connection-coefficient certificate decides exactly zero (the reducer's own
 * verification). has=0 -> BAD_INPUT -> pure (the conservative fall — never a
 * possibly-divergent native false). */
static srmech_status_t inf_sigma_elliptic(const srmech_json_value_t *root,
        srmech_marshal_arena_t *a, size_t rel_len, int *out_reducible)
{
    const srmech_json_value_t *node;
    srmech_ellratio_wire_t w;
    size_t n_mono, i, wsb; uint32_t cap, cl = 2u, work_cap;
    unsigned char *ws; int has = 0;
    srmech_status_t st;
    assert(root != NULL && a != NULL && out_reducible != NULL);
    assert(rel_len > 0u);
    *out_reducible = 0;
    node = srmech_json_object_get(root, "elliptic_term_ratio");
    if (node == NULL || node->type != SRMECH_JSON_OBJECT) {
        return SRMECH_ERR_BAD_INPUT;
    }
    cap = (uint32_t)(srmech_bigint_from_dec_bound(rel_len) + 8u);
    st = srmech_carrier_read_ellratio(node, a, cap, &w);
    if (st != SRMECH_OK) { return st; }
    n_mono = 1u + w.n_num + w.n_den;
    for (i = 0u; i < n_mono; i++) {
        if (w.coeff_num[i].n > cl) { cl = w.coeff_num[i].n; }
        if (w.coeff_den[i].n > cl) { cl = w.coeff_den[i].n; }
    }
    work_cap = cl + 16u;                              /* the wrapper's headroom */
    wsb = srmech_elliptic_wz_certificate_ws_bound(w.n_syms, w.n_num, w.n_den,
                                                  work_cap);
    ws = inf_ma_carve(a, wsb);
    if (ws == NULL) { return SRMECH_ERR_OVERFLOW; }
    st = srmech_elliptic_wz_certificate(w.n_syms, w.xsym, w.psym, w.qsym,
                                        w.ysym, w.nsym, w.ksym, w.n_num,
                                        w.n_den, w.coeff_num, w.coeff_den,
                                        w.exps_flat, work_cap, &has, ws, wsb);
    if (st != SRMECH_OK) { return st; }
    if (!has) { return SRMECH_ERR_BAD_INPUT; }       /* conservative -> pure    */
    *out_reducible = 1;
    return SRMECH_OK;
}

/* ------------------------------------------------------------------
 * SPECTRAL row (rc224 — the LAST #796 row). The verdict is the EXACT
 * operator-level structural fact "L is real-symmetric" (the spectral
 * theorem's own hypothesis), decided by bit-exact IEEE equality over the
 * mirrored entries — NO eigensolve, NO resonant_spectrum, NO float
 * tolerance anywhere in the C decision path. The f64 leaves ride the wire
 * as IEEE-754 bit patterns (signed int64), so no decimal float parse sits
 * between the pure and native builds; the eigenvalue payload is re-derived
 * pure-side by _finish_native on a reducible verdict.
 * ------------------------------------------------------------------ */

/* Read a f64 from its marshalled IEEE-754 bit pattern (a signed-int64 JSON
 * node — the bit-EXACT float wire; never a JSON decimal double, never
 * strtod, in the decision path). BAD_INPUT on a NULL / non-int node. */
static srmech_status_t inf_f64_bits(const srmech_json_value_t *j, double *out)
{
    int64_t bits;
    assert(out != NULL);
    assert(sizeof(double) == sizeof(int64_t));
    if (j == NULL || j->type != SRMECH_JSON_INT) { return SRMECH_ERR_BAD_INPUT; }
    bits = j->u.i;
    memcpy(out, &bits, sizeof bits);
    return SRMECH_OK;
}

/* Read the {"n": N, "bits": [i64 x N*N]} grid object under `key` into a fresh
 * row-major n*n double buffer carved off `b`. BAD_INPUT on a malformed node
 * (n < 1, n over uint32, a bits-count mismatch, a non-int leaf); OVERFLOW on
 * arena exhaustion (-> the pure path). */
static srmech_status_t inf_read_f64_grid(const srmech_json_value_t *root,
        inf_bump_t *b, const char *key, double **out_grid, size_t *out_n)
{
    const srmech_json_value_t *node, *jn, *jb;
    double *g;
    size_t n, cells, i;
    assert(root != NULL && b != NULL);
    assert(key != NULL && out_grid != NULL && out_n != NULL);
    node = srmech_json_object_get(root, key);
    if (node == NULL || node->type != SRMECH_JSON_OBJECT) {
        return SRMECH_ERR_BAD_INPUT;
    }
    jn = srmech_json_object_get(node, "n");
    jb = srmech_json_object_get(node, "bits");
    if (jn == NULL || jn->type != SRMECH_JSON_INT || jn->u.i < 1 ||
        jn->u.i > (int64_t)0xFFFFFFFF ||
        jb == NULL || jb->type != SRMECH_JSON_ARRAY) {
        return SRMECH_ERR_BAD_INPUT;
    }
    n = (size_t)jn->u.i;
    cells = n * n;
    if (cells / n != n || (size_t)jb->u.arr.n != cells) {
        return SRMECH_ERR_BAD_INPUT;
    }
    g = (double *)inf_carve(b, cells * sizeof(double));
    if (g == NULL) { return SRMECH_ERR_OVERFLOW; }
    for (i = 0u; i < cells; i++) {
        if (inf_f64_bits(jb->u.arr.items[i], &g[i]) != SRMECH_OK) {
            return SRMECH_ERR_BAD_INPUT;
        }
    }
    *out_grid = g;
    *out_n = n;
    return SRMECH_OK;
}

/* adjacency -> L = D - A IN PLACE, mirroring the pure _build_laplacian's
 * exact float-op ORDER (deg accumulates ALL columns of the row INCLUDING the
 * diagonal, every entry is negated, then diag = deg + (-A[i][i])) so the
 * built L is entry-for-entry the pure path's build. Pure IEEE add/negate
 * only — deterministic, platform-stable. */
static void inf_adjacency_to_laplacian(double *g, size_t n)
{
    size_t i, j;
    assert(g != NULL);
    assert(n > 0u);
    for (i = 0u; i < n; i++) {
        double deg = 0.0;
        for (j = 0u; j < n; j++) {
            double a = g[i * n + j];
            deg = deg + a;
            g[i * n + j] = -a;
        }
        g[i * n + i] = deg + g[i * n + i];
    }
}

/* Read one [u, v] edge pair (ints in [0, n)) into eu/ev slot `i`. */
static srmech_status_t inf_read_edge_pair(const srmech_json_value_t *p,
        int64_t n, uint32_t *eu, uint32_t *ev, size_t i)
{
    const srmech_json_value_t *ju, *jv;
    assert(eu != NULL && ev != NULL);
    assert(n > 0);
    if (p == NULL || p->type != SRMECH_JSON_ARRAY || p->u.arr.n != 2u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    ju = p->u.arr.items[0];
    jv = p->u.arr.items[1];
    if (ju == NULL || jv == NULL || ju->type != SRMECH_JSON_INT ||
        jv->type != SRMECH_JSON_INT || ju->u.i < 0 || jv->u.i < 0 ||
        ju->u.i >= n || jv->u.i >= n) {
        return SRMECH_ERR_BAD_INPUT;
    }
    eu[i] = (uint32_t)ju->u.i;
    ev[i] = (uint32_t)jv->u.i;
    return SRMECH_OK;
}

/* The spectral EDGES sub-case: read "n" (int >= 1), "edges" [[u,v]...] and
 * the optional "weights" (i64 f64-bit patterns, one per edge), then build L
 * via the Class-L srmech_graph_dense_laplacian kernel — the SAME builder the
 * pure path dispatches to (identical accumulation order; symmetric by
 * construction for finite weights). */
static srmech_status_t inf_spectral_edges(const srmech_json_value_t *root,
        inf_bump_t *b, double **out_grid, size_t *out_n)
{
    const srmech_json_value_t *je, *jn, *jw;
    uint32_t *eu, *ev;
    double *w = NULL, *g;
    size_t n, ne, i, cells;
    assert(root != NULL && b != NULL);
    assert(out_grid != NULL && out_n != NULL);
    je = srmech_json_object_get(root, "edges");
    jn = srmech_json_object_get(root, "n");
    jw = srmech_json_object_get(root, "weights");
    if (je == NULL || je->type != SRMECH_JSON_ARRAY || jn == NULL ||
        jn->type != SRMECH_JSON_INT || jn->u.i < 1 ||
        jn->u.i > (int64_t)0xFFFFFFFF) {
        return SRMECH_ERR_BAD_INPUT;
    }
    n = (size_t)jn->u.i;
    ne = (size_t)je->u.arr.n;
    cells = n * n;
    if (cells / n != n) { return SRMECH_ERR_BAD_INPUT; }
    eu = (uint32_t *)inf_carve(b, (ne + 1u) * sizeof(uint32_t));
    ev = (uint32_t *)inf_carve(b, (ne + 1u) * sizeof(uint32_t));
    g = (double *)inf_carve(b, cells * sizeof(double));
    if (eu == NULL || ev == NULL || g == NULL) { return SRMECH_ERR_OVERFLOW; }
    for (i = 0u; i < ne; i++) {
        if (inf_read_edge_pair(je->u.arr.items[i], jn->u.i, eu, ev, i)
                != SRMECH_OK) {
            return SRMECH_ERR_BAD_INPUT;
        }
    }
    if (jw != NULL) {
        if (jw->type != SRMECH_JSON_ARRAY || (size_t)jw->u.arr.n != ne) {
            return SRMECH_ERR_BAD_INPUT;
        }
        w = (double *)inf_carve(b, (ne + 1u) * sizeof(double));
        if (w == NULL) { return SRMECH_ERR_OVERFLOW; }
        for (i = 0u; i < ne; i++) {
            if (inf_f64_bits(jw->u.arr.items[i], &w[i]) != SRMECH_OK) {
                return SRMECH_ERR_BAD_INPUT;
            }
        }
    }
    if (srmech_graph_dense_laplacian((uint32_t)n, (uint32_t)ne, eu, ev, w, g)
            != SRMECH_OK) {
        return SRMECH_ERR_BAD_INPUT;
    }
    *out_grid = g;
    *out_n = n;
    return SRMECH_OK;
}

/* The bit-exact real-symmetry PREDICATE — the rc224 spectral VERDICT: the
 * reduction EXISTS iff L is real-symmetric (pure IEEE == on the mirrored
 * entries, including the diagonal self-compare, which is false only for a
 * NaN). NO eigensolve, NO tolerance — the same predicate, over the same
 * doubles, the upgraded pure _try_spectral runs. */
static int inf_spectral_symmetric(const double *g, size_t n)
{
    size_t i, j;
    assert(g != NULL);
    assert(n > 0u);
    for (i = 0u; i < n; i++) {
        for (j = i; j < n; j++) {
            if (!(g[i * n + j] == g[j * n + i])) { return 0; }
        }
    }
    return 1;
}

/* The SPECTRAL dispatch: build L per the payload shape (matrix -> the raw
 * bit-exact grid; adjacency -> grid + in-place D-A; edges -> the Class-L
 * kernel) and decide the structural verdict. A valid-but-asymmetric L sets
 * *out_reducible = 0 and returns OK (the DEFINITIVE false — the C-built L is
 * entry-for-entry the pure build, so the pure predicate reads the same);
 * non-OK ONLY on a malformed / unbuildable payload or arena overflow
 * (-> the pure path decides). */
static srmech_status_t inf_spectral(const srmech_json_value_t *root,
                                    inf_bump_t *b, int *out_reducible)
{
    const srmech_json_value_t *mx, *ad;
    double *g = NULL;
    size_t n = 0u;
    srmech_status_t st;
    assert(root != NULL && b != NULL);
    assert(out_reducible != NULL);
    *out_reducible = 0;
    mx = srmech_json_object_get(root, "matrix");
    ad = srmech_json_object_get(root, "adjacency");
    if (mx != NULL) {
        st = inf_read_f64_grid(root, b, "matrix", &g, &n);
    } else if (ad != NULL) {
        st = inf_read_f64_grid(root, b, "adjacency", &g, &n);
        if (st == SRMECH_OK) { inf_adjacency_to_laplacian(g, n); }
    } else {
        st = inf_spectral_edges(root, b, &g, &n);
    }
    if (st != SRMECH_OK) { return st; }
    *out_reducible = inf_spectral_symmetric(g, n);
    return SRMECH_OK;
}

/* rc224 route — detect + dispatch the SPECTRAL row wire (matrix / adjacency /
 * edges present). Sets *out_handled = 1 when the relationship is spectral
 * (the caller emits *out_lit). BOTH verdict literals are emittable here: the
 * reducible:false is DEFINITIVE (the C-built L is entry-for-entry the pure
 * path's build, so the pure symmetry predicate reads identically). */
static srmech_status_t inf_route_spectral(const srmech_json_value_t *root,
        inf_bump_t *b, const char **out_lit, int *out_handled)
{
    int red = 0;
    srmech_status_t st;
    assert(root != NULL && b != NULL);
    assert(out_lit != NULL && out_handled != NULL);
    *out_handled = 0;
    if (srmech_json_object_get(root, "matrix") == NULL &&
        srmech_json_object_get(root, "adjacency") == NULL &&
        srmech_json_object_get(root, "edges") == NULL) {
        return SRMECH_OK;                            /* not the spectral row    */
    }
    *out_handled = 1;
    st = inf_spectral(root, b, &red);
    if (st != SRMECH_OK) { return st; }
    *out_lit = red
        ? "{\"reducer\":\"resonant_spectrum\",\"reducible\":true,"
          "\"row\":\"spectral\",\"verified\":true}"
        : "{\"reducible\":false,\"row\":\"spectral\"}";
    return SRMECH_OK;
}

/* ------------------------------------------------------------------
 * rc223 route — detect + dispatch the four new-row shapes. Sets *out_handled
 * = 1 when the relationship is one of them (the caller emits *out_lit).
 * ------------------------------------------------------------------ */

static srmech_status_t inf_route_rc223(const srmech_json_value_t *root,
        inf_bump_t *b, size_t rel_len, const char **out_lit, int *out_handled)
{
    const srmech_json_value_t *rj, *qrn, *qtr, *ell;
    srmech_marshal_arena_t ma;
    int red = 0;
    srmech_status_t st;
    assert(root != NULL && b != NULL);
    assert(out_lit != NULL && out_handled != NULL);
    *out_handled = 0;
    rj = srmech_json_object_get(root, "rj_num");
    qrn = srmech_json_object_get(root, "qrn_num");
    qtr = srmech_json_object_get(root, "q_term_ratio_num");
    ell = srmech_json_object_get(root, "elliptic_term_ratio");
    if (rj == NULL && qrn == NULL && qtr == NULL && ell == NULL) {
        return SRMECH_OK;                            /* not an rc223 row        */
    }
    *out_handled = 1;
    srmech_marshal_arena_init(&ma, b->cur, (size_t)(b->end - b->cur));
    if (rj != NULL) {                                /* SIGMA-MULTIVAR          */
        st = inf_sigma_multivar(root, &ma, rel_len, &red);
        *out_lit = "{\"reducer\":\"apagodu_zeilberger\",\"reducible\":true,"
                   "\"row\":\"sigma_multivar\",\"verified\":true}";
    } else if (qrn != NULL) {                        /* SIGMA-Q definite        */
        st = inf_sigma_q_wz(root, &ma, rel_len, &red);
        *out_lit = red
            ? "{\"reducer\":\"q_wz_certificate\",\"reducible\":true,"
              "\"row\":\"sigma_q\",\"verified\":true}"
            : "{\"reducible\":false,\"row\":\"sigma_q\"}";
        return st;                                   /* false IS emittable here */
    } else if (qtr != NULL) {                        /* SIGMA-Q indefinite      */
        st = inf_sigma_q_gosper(root, &ma, rel_len, &red);
        *out_lit = "{\"reducer\":\"q_gosper\",\"reducible\":true,"
                   "\"row\":\"sigma_q\",\"verified\":true}";
    } else {                                         /* SIGMA-ELLIPTIC          */
        st = inf_sigma_elliptic(root, &ma, rel_len, &red);
        *out_lit = "{\"reducer\":\"elliptic_wz_certificate\",\"reducible\":true,"
                   "\"row\":\"sigma_elliptic\",\"verified\":true}";
    }
    if (st != SRMECH_OK) { return st; }
    /* these rows emit ONLY the verified-positive decision (their reducers
     * decline non-definitively) — a non-reducible OK is defensive-impossible;
     * route it to the pure path, never an unverified literal. */
    return red ? SRMECH_OK : SRMECH_ERR_BAD_INPUT;
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
 * rel_len (bytes) — exactly as srmech._native.gosper_c sizes ws from
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

/* Minimum caller-arena BYTES for the SIGMA-MULTIVAR (apagodu_zeilberger) row
 * (rc223) over a `rel_len`-byte JSON whose six (n,j,k) TriPoly term-ratios
 * carry a max shape envelope `max_terms` (jdeg / kdeg / nlen max) and a max
 * coefficient of `coeff_limbs` significant 32-bit limbs. The apagodu dense
 * exact-Q RREF ws dominates (hundreds of MB even for small genuine systems —
 * the Python caller gates it behind a ceiling and falls to the bounded-memory
 * pure CRT path, the same honor as apagodu_zeilberger_c). Sized on the ACTUAL
 * shape, never rel_len alone. No malloc; the caller owns the arena. */
size_t srmech_infer_sigma_multivar_arena_bytes(size_t rel_len, size_t max_terms,
                                               size_t coeff_limbs)
{
    size_t read_cap = srmech_bigint_from_dec_bound(rel_len) + 8u;
    size_t cl = coeff_limbs < 1u ? 1u : coeff_limbs;
    size_t deg = max_terms < 1u ? 1u : max_terms;
    size_t oc = srmech_apagodu_zeilberger_out_cap(cl, 1u, deg);
    size_t a_ws = srmech_apagodu_zeilberger_ws_bound(cl, 1u, deg);
    size_t nbound = (deg + 2u) * 3u + 8u;
    size_t cells = (deg + 4u) * (deg + 4u) + 8u;
    size_t coeff_slots = 2u * nbound + 8u;
    size_t cert_slots = cells * nbound + 8u;
    size_t bi = sizeof(srmech_bigint_t);
    size_t parse = 160u * rel_len + 65536u;
    size_t inputs = 12u * (rel_len + 8u) * (bi + read_cap * 4u);
    size_t outputs = (2u * coeff_slots + 4u * cert_slots) * (bi + oc * 4u);
    assert(bi <= 64u);
    assert(cl > 0u);
    return parse + a_ws + inputs + outputs + 262144u;
}

/* Minimum caller-arena BYTES for the SIGMA-Q rows (rc223): the DEFINITE
 * q_wz_certificate chain (q_zeilberger @order-1 FIND + q_wz_verify PROVE) and
 * the INDEFINITE q_gosper, over a `rel_len`-byte JSON whose QBiPoly / QPoly
 * q-term-ratios carry a max shape envelope `max_terms` (ycells / xcells /
 * qlen max) and a max coefficient of `coeff_limbs` significant limbs. The
 * q_wz_verify scratch dominates; it is sized at 4*cl+4 limbs (the rescaled
 * certificate headroom over the k-free FIND class) — a genuinely bigger
 * rescale overflows the arena and falls to pure (never a wrap). */
size_t srmech_infer_sigma_q_arena_bytes(size_t rel_len, size_t max_terms,
                                        size_t coeff_limbs)
{
    size_t read_cap = srmech_bigint_from_dec_bound(rel_len) + 8u;
    size_t cl = coeff_limbs < 1u ? 1u : coeff_limbs;
    size_t deg = max_terms < 1u ? 1u : max_terms;
    size_t oc = srmech_q_zeilberger_out_cap(cl, 1u, deg);
    size_t z_ws = srmech_q_zeilberger_ws_bound(cl, 1u, deg);
    size_t v_ws = srmech_q_wz_verify_ws_bound(4u * cl + 4u, deg);
    size_t g_ws = srmech_q_gosper_ws_bound(cl, deg);
    size_t cell_q_cap = deg + 4u;
    size_t coeff_total = 3u * cell_q_cap + 8u;
    size_t cert_total = (deg + 4u) * cell_q_cap + 8u;
    size_t xcap = srmech_bigint_mul_bound(oc, oc);
    size_t bi = sizeof(srmech_bigint_t);
    size_t parse = 160u * rel_len + 65536u;
    size_t inputs = 8u * (rel_len + 8u) * (bi + read_cap * 4u);
    size_t outputs = 2u * (coeff_total + cert_total) * (bi + oc * 4u);
    size_t xnum = 2u * cert_total * (bi + xcap * 4u);
    size_t gosper = srmech_q_gosper_out_cap(cl, deg);
    size_t g_out = 4u * (deg + 4u) * (bi + gosper * 4u);
    assert(bi <= 64u);
    assert(cl > 0u);
    return parse + z_ws + v_ws + g_ws + inputs + outputs + xnum + g_out
         + 262144u;
}

/* Minimum caller-arena BYTES for the SIGMA-ELLIPTIC (elliptic_wz_certificate)
 * row (rc223) over a `rel_len`-byte JSON whose pre-interned EllRatio wire
 * carries `max_terms` >= n_syms + (1 + n_num + n_den) and a max coefficient of
 * `coeff_limbs` significant limbs. The connection-coefficient certificate ws
 * is sub-MB at 8w7 scale; a generous static over-approximation. */
size_t srmech_infer_sigma_elliptic_arena_bytes(size_t rel_len, size_t max_terms,
                                               size_t coeff_limbs)
{
    size_t read_cap = srmech_bigint_from_dec_bound(rel_len) + 8u;
    size_t cl = coeff_limbs < 1u ? 1u : coeff_limbs;
    size_t mt = max_terms < 4u ? 4u : max_terms;
    size_t e_ws = srmech_elliptic_wz_certificate_ws_bound(mt, mt, mt, cl + 16u);
    size_t bi = sizeof(srmech_bigint_t);
    size_t parse = 160u * rel_len + 65536u;
    size_t inputs = (2u * mt + 8u) * (bi + read_cap * 4u);
    size_t exps = (mt + 8u) * (mt + 8u) * 4u;
    assert(bi <= 64u);
    assert(cl > 0u);
    return parse + e_ws + inputs + exps + 262144u;
}

/* Minimum caller-arena BYTES for the SPECTRAL row (rc224) over a `rel_len`-byte
 * JSON whose Laplacian dimension is `n` (the marshalled "n"). The row's
 * decision path holds ONE n*n double grid plus the parallel edge arrays
 * (bounded by the wire bytes) and runs NO eigensolve — the verdict is the
 * bit-exact real-symmetry predicate, so the arena is parse + grid + edges.
 * An over-large n returns SIZE_MAX-shaped bytes so the Python ceiling check
 * declines to the pure path (never a wrapped size). */
size_t srmech_infer_spectral_arena_bytes(size_t rel_len, size_t n)
{
    size_t dim = n < 1u ? 1u : n;
    size_t parse = 160u * rel_len + 65536u;
    size_t edges = (rel_len / 4u + 8u)
                 * (2u * sizeof(uint32_t) + sizeof(double));
    assert(sizeof(double) == 8u);
    assert(dim >= 1u);
    if (dim > 1000000u) { return (size_t)-1; }         /* decline, never wrap */
    return parse + dim * dim * sizeof(double) + edges + 65536u;
}

/* Route a stored relationship: parse JSON, detect the row from the marshalled
 * operand structure (matrix/adjacency/edges -> the rc224 spectral row;
 * rj_/qrn_/q_term_ratio_/elliptic_term_ratio -> the rc223 rows; rn_num ->
 * sigma-wz; term_ratio_* -> gosper; sigma -> cyclic), dispatch + verify the C
 * reducer, and emit the DECISION literal. Any other structure / malformed
 * operand / overflow -> non-OK (-> the Python pure infer). */
/* The rc176/rc192 CLASSIC rows (sigma-wz / sigma-gosper / cyclic), detected
 * from the marshalled keys. Sets *out_lit + returns OK; BAD_INPUT when no
 * classic row matches (-> the Python pure infer). */
static srmech_status_t inf_route_classic(const srmech_json_value_t *root,
        inf_bump_t *b, size_t rel_len, const char **out_lit)
{
    const srmech_json_value_t *g, *cyc, *rn;
    int red = 0;
    srmech_status_t st;
    assert(root != NULL && b != NULL);
    assert(out_lit != NULL);
    rn = srmech_json_object_get(root, "rn_num");
    g = srmech_json_object_get(root, "term_ratio_num");
    cyc = srmech_json_object_get(root, "sigma");
    if (rn != NULL) {                       /* SIGMA-DEFINITE (wz) row — rc192   */
        srmech_marshal_arena_t ma;
        srmech_marshal_arena_init(&ma, b->cur, (size_t)(b->end - b->cur));
        st = inf_sigma_wz(root, &ma, rel_len, &red);
        *out_lit = red
            ? "{\"reducer\":\"wz_certificate\",\"reducible\":true,\"row\":\"sigma\",\"verified\":true}"
            : "{\"reducible\":false,\"row\":\"sigma\"}";
    } else if (g != NULL) {
        st = inf_gosper(root, b, &red);
        *out_lit = red
            ? "{\"reducer\":\"gosper\",\"reducible\":true,\"row\":\"sigma\",\"verified\":true}"
            : "{\"reducible\":false,\"row\":\"sigma\"}";
    } else if (cyc != NULL) {
        st = inf_cyclic(root, b, &red);
        *out_lit = red
            ? "{\"reducer\":\"the_one\",\"reducible\":true,\"row\":\"cyclic\",\"verified\":true}"
            : "{\"reducible\":false,\"row\":\"cyclic\"}";
    } else {
        return SRMECH_ERR_BAD_INPUT;   /* not a clean C row -> pure infer */
    }
    return st;
}

srmech_status_t srmech_infer(const char *rel_json, size_t rel_len,
                             void *ws, size_t ws_len,
                             char *out, size_t out_cap, size_t *out_len)
{
    inf_bump_t b;
    srmech_json_value_t *root = NULL;
    unsigned char *pa;
    size_t pj;
    const char *lit = NULL;
    int handled = 0;
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
    st = inf_route_spectral(root, &b, &lit, &handled);         /* rc224 row    */
    if (!handled) {
        st = inf_route_rc223(root, &b, rel_len, &lit, &handled); /* rc223 rows */
    }
    if (!handled) {
        st = inf_route_classic(root, &b, rel_len, &lit);       /* rc176/rc192  */
    }
    if (st != SRMECH_OK) { return st; }
    return inf_emit(out, out_cap, out_len, lit);
}
