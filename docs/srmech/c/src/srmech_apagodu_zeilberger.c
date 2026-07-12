/*
 * srmech_apagodu_zeilberger.c -- the Apagodu-Zeilberger multivariate "sums of
 * sums" creative-telescoping recurrence-finder (the rc53 op that CLOSES the
 * multivariate F929 reduction row). The C peer of
 * srmech.amsc.apagodu_zeilberger.apagodu_zeilberger.
 *
 * Input: a proper hypergeometric term F(n,j,k) given by its THREE term ratios
 *   r_n(n,j,k) = F(n+1,j,k)/F(n,j,k) = rn_num/rn_den
 *   r_j(n,j,k) = F(n,j+1,k)/F(n,j,k) = rj_num/rj_den
 *   r_k(n,j,k) = F(n,j,k+1)/F(n,j,k) = rk_num/rk_den
 * each an exact-rational TRIVARIATE polynomial over Q[n,j,k]. A trivariate poly is
 * encoded FLAT as a j-ascending list of BiPoly(n,k) blocks; each BiPoly is a
 * k-ascending list of Poly-in-n; each Poly-in-n a parallel (num,den) bigint run.
 * The bridge form is the nested [[[ (num,den) ]_n ]_k ]_j the srmech_tripoly peer
 * uses, FLATTENED here to one (num,den) stream + a per-(j,k)-cell n-run length array
 * + the (jdeg, kdeg) per-block shape.
 *
 * Output: when a recurrence of order <= max_order exists, *out_has = 1, *out_order
 * = L, and coeff_n/coeff_d (coeff_nlen[i] the per-i length, i = 0..L) carry the
 * recurrence coefficient polynomials a_i(n) so Sum_i a_i(n) f(n+i) = 0
 * (f(n) = Sum_{j,k} F(n,j,k)); cert_j_* and cert_k_* carry the two rational
 * certificate numerators x_j(n,j,k) / x_k(n,j,k) (R_j = x_j/D_P, R_k = x_k/D_P).
 * Else *out_has = 0.
 *
 * The algorithm (Apagodu & Zeilberger 2006, Adv. Appl. Math. 37:139-152), exact
 * over Q[n,j,k]:
 *   For L = 0, 1, ..., max_order (the C peer ACCELERATES L <= 1):
 *     rho_i = prod_{t<i} r_n(n+t,j,k); D_P = prod_i rho_den_i (a common LHS den).
 *     The two-certificate ansatz (divided by F):
 *       Sum_i a_i(n) rho_i = [R_j(j+1) r_j - R_j] + [R_k(k+1) r_k - R_k]
 *     with R_j = x_j/D_P, R_k = x_k/D_P. Clear to one common denominator -> a
 *     polynomial identity in (n,j,k), LINEAR in {a_i coeffs} U {x_j coeffs} U
 *     {x_k coeffs}; matching (n,j,k)-powers gives a HOMOGENEOUS exact-Q system.
 *     A kernel vector with a NONZERO a-block (read off srmech_qmat_rref) gives the
 *     recurrence + certificates; the first such L is the minimal order.
 *
 * This file carries its own compact exact-Q TRIVARIATE polynomial toolkit (a 3-D
 * grid of Q, n x k x j, over caller-arena srmech_bigint) and COMPOSES the public
 * srmech_qmat_rref for the kernel. No malloc (JPL Rule 3): every working carrier +
 * working tripoly + the qmat marshalling is carved from the caller arena `ws`. Any
 * residual overflow returns SRMECH_ERR_OVERFLOW (never a wrap); the Python op then
 * runs its ceiling-free pure-Q path -- so the standalone-complete honor holds, and
 * the genuinely order->=2 multivariate sums are proved entirely on the pure path
 * (the C declines, never returns a false "no recurrence": the dispatch trusts only
 * a has=1 C result).
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto/recursion): OK -- iterative, flat helpers
 *   - Rule 2 (bounded loops)    : OK -- bounds are degree / order counts
 *   - Rule 3 (no malloc)        : OK -- caller arena + caller out only
 *   - Rule 4 (<=60 lines/func)  : OK -- factored into static helpers
 *   - Rule 5 (>=2 asserts/fn)   : OK -- entry-pointer + pre/postcondition
 *   - Rule 7 (return-value)     : OK -- srmech_status_t propagated
 *   - Rule 8 (no multi-line mac): OK -- no function-like macros
 *   - Rule 10 (warnings clean)  : OK under -Wall -Wextra -Wpedantic -Werror
 *
 * License: MIT.
 */

#include "srmech.h"

#include <assert.h>
#include <stdint.h>

/* The largest ansatz order the C orchestrator handles in a sane caller arena. The
 * C peer ACCELERATES the common low-order case (order 0-1 covers the textbook
 * double-sum identities, e.g. Sum_{j,k} C(n,j)C(j,k) -> 3^n is order 1); a
 * higher-order recurrence (the genuinely-2D Apery-like sums) falls to the COMPLETE
 * pure-Python path -- the C never returns a false "no recurrence", it just declines
 * to decide (the Python dispatch trusts only a has=1 C result). */
#define AZ_MAX_ORDER 1u
#define AZ_MAX_DEG   12u

/* The largest homogeneous-system column count the C peer assembles with the DENSE
 * srmech_qmat_rref. The dense RREF's intermediate exact-Q entries Hadamard-bound at
 * a width that makes a wide system's caller arena balloon (the Python path dodges
 * this via the CRT re-fibration rref_crt; the C dense path does not). So the C peer
 * only ACCELERATES a small system (the order ≤ 1 textbook double sums solve well
 * within this); a wider one returns SRMECH_ERR_BAD_INPUT and the Python op decides
 * on its bounded-memory CRT path. */
#define AZ_DENSE_MAX_TOTAL 48u

/* The certificate-degree sweep width above the structural base (mirrors the Python
 * default _MAX_CERT_BUMP): jk_deg = jk_base + bump for bump = 0..AZ_MAX_CERT_BUMP. */
#define AZ_MAX_CERT_BUMP 1u

/* ---- scalar exact-Q context (mirror zeilberger's zb_ctx) ---------- */
typedef struct az_ctx {
    srmech_bigint_t qa_n, qa_d;
    srmech_bigint_t qb_n, qb_d;
    srmech_bigint_t sub_n, sub_d;
    srmech_bigint_t t0, t1;
    srmech_bigint_t g, rem;
    srmech_bigint_t rs0, rs1;
    srmech_bigint_t z0, z1;
    uint32_t  cap;
    uint32_t *pool;
    size_t    pool_words;
    size_t    pool_cur;
    void     *scratch;
    size_t    scratch_len;
} az_ctx_t;

#define AZ_N_CARRIERS 16u

/* A Poly-in-n: a parallel (num,den) srmech_bigint array + a live length. */
typedef struct az_poly {
    srmech_bigint_t *n;
    srmech_bigint_t *d;
    size_t           len;
    size_t           cap_terms;
} az_poly_t;

/* A BiPoly(n,k): an array of (k_cap) Poly-in-n slots + a live k-length. */
typedef struct az_bipoly {
    az_poly_t *kc;
    size_t     klen;
    size_t     k_cap;
} az_bipoly_t;

/* A TriPoly(n,j,k): an array of (j_cap) BiPoly(n,k) slots + a live j-length. */
typedef struct az_tripoly {
    az_bipoly_t *jb;
    size_t       jlen;
    size_t       j_cap;
} az_tripoly_t;

/* ---- forward declarations (Rule 1: no recursion) ------------------ */
static uint32_t *az_take(uint32_t *base, size_t words, size_t *cur, size_t cnt);
static srmech_status_t az_bind(srmech_bigint_t *b, uint32_t *base, size_t words,
                               size_t *cur, uint32_t cap);
static size_t az_hdr_words(void);
static srmech_status_t az_ctx_init(az_ctx_t *c, uint32_t cap, void *ws,
                                   size_t ws_len);
static srmech_status_t az_q_reduce(az_ctx_t *c, srmech_bigint_t *num,
                                   srmech_bigint_t *den);
static srmech_status_t az_q_add(az_ctx_t *c, srmech_bigint_t *on,
                                srmech_bigint_t *od, const srmech_bigint_t *an,
                                const srmech_bigint_t *ad, const srmech_bigint_t *bn,
                                const srmech_bigint_t *bd, int sub);
static srmech_status_t az_q_mul(az_ctx_t *c, srmech_bigint_t *on,
                                srmech_bigint_t *od, const srmech_bigint_t *an,
                                const srmech_bigint_t *ad, const srmech_bigint_t *bn,
                                const srmech_bigint_t *bd);
static size_t az_trim(const srmech_bigint_t *nums, size_t n);
static srmech_status_t az_poly_alloc(az_ctx_t *c, az_poly_t *p, size_t terms);
static srmech_status_t az_poly_zero(az_poly_t *p);
static srmech_status_t az_poly_copy(az_ctx_t *c, az_poly_t *dst,
                                    const az_poly_t *src);
static srmech_status_t az_poly_addsub(az_ctx_t *c, az_poly_t *out,
                                      const az_poly_t *a, const az_poly_t *b,
                                      int sub);
static srmech_status_t az_poly_mul(az_ctx_t *c, az_poly_t *out,
                                   const az_poly_t *a, const az_poly_t *b);
static srmech_status_t az_poly_shift_n(az_ctx_t *c, az_poly_t *out,
                                       const az_poly_t *p, int64_t h);
static srmech_status_t az_bipoly_alloc(az_ctx_t *c, az_bipoly_t *b, size_t k_terms,
                                       size_t n_terms);
static void az_bipoly_trim(az_bipoly_t *b);
static srmech_status_t az_bipoly_copy(az_ctx_t *c, az_bipoly_t *dst,
                                      const az_bipoly_t *src);
static srmech_status_t az_bipoly_add(az_ctx_t *c, az_bipoly_t *out,
                                     const az_bipoly_t *a, const az_bipoly_t *b,
                                     az_poly_t *pacc);
static srmech_status_t az_bipoly_mul(az_ctx_t *c, az_bipoly_t *out,
                                     const az_bipoly_t *a, const az_bipoly_t *b,
                                     az_poly_t *acc, az_poly_t *prod);
static srmech_status_t az_bipoly_shift_k(az_ctx_t *c, az_bipoly_t *out,
                                         const az_bipoly_t *p,
                                         az_bipoly_t *acc, az_bipoly_t *tmp,
                                         az_poly_t *pacc);
static srmech_status_t az_tripoly_alloc(az_ctx_t *c, az_tripoly_t *t, size_t j_terms,
                                        size_t k_terms, size_t n_terms);
static void az_tripoly_trim(az_tripoly_t *t);
static srmech_status_t az_tripoly_copy(az_ctx_t *c, az_tripoly_t *dst,
                                       const az_tripoly_t *src);
static srmech_status_t az_tripoly_mul(az_ctx_t *c, az_tripoly_t *out,
                                      const az_tripoly_t *a, const az_tripoly_t *b,
                                      az_bipoly_t *bacc, az_bipoly_t *bprod,
                                      az_poly_t *pacc, az_poly_t *pprod);
static srmech_status_t az_tripoly_shift_n(az_ctx_t *c, az_tripoly_t *out,
                                          const az_tripoly_t *p, int64_t h);
static srmech_status_t az_tripoly_shift_j(az_ctx_t *c, az_tripoly_t *out,
                                          const az_tripoly_t *p,
                                          az_tripoly_t *acc, az_tripoly_t *tmp,
                                          az_bipoly_t *bacc, az_bipoly_t *bprod,
                                          az_poly_t *pacc, az_poly_t *pprod);
static srmech_status_t az_tripoly_shift_k(az_ctx_t *c, az_tripoly_t *out,
                                          const az_tripoly_t *p,
                                          az_bipoly_t *bacc, az_bipoly_t *btmp,
                                          az_poly_t *pacc);

/* ---- caller-arena carve (mirror zeilberger) ----------------------- */

static uint32_t *az_take(uint32_t *base, size_t words, size_t *cur, size_t cnt)
{
    uint32_t *p;
    assert(base != NULL && cur != NULL);
    assert(*cur <= words);
    if (cnt > words || *cur > words - cnt) { return NULL; }
    p = base + *cur;
    *cur += cnt;
    return p;
}

static srmech_status_t az_bind(srmech_bigint_t *b, uint32_t *base, size_t words,
                               size_t *cur, uint32_t cap)
{
    uint32_t *limbs = az_take(base, words, cur, cap);
    assert(b != NULL && cap > 0u);
    assert(base != NULL || words == 0u);
    if (limbs == NULL) { return SRMECH_ERR_OVERFLOW; }
    b->limbs = limbs;
    b->cap = cap;
    b->n = 0u;
    b->sign = 0;
    return SRMECH_OK;
}

static size_t az_hdr_words(void)
{
    size_t hw = (sizeof(srmech_bigint_t) + sizeof(uint32_t) - 1u)
                / sizeof(uint32_t);
    assert(sizeof(srmech_bigint_t) > 0u);
    assert(hw >= 1u);
    return hw;
}

static srmech_status_t az_ctx_init(az_ctx_t *c, uint32_t cap, void *ws,
                                   size_t ws_len)
{
    uint32_t *base = (uint32_t *)ws;
    size_t words = ws_len / sizeof(uint32_t);
    size_t carrier_words = (size_t)cap * (size_t)AZ_N_CARRIERS;
    size_t scratch_words = (size_t)cap * 8u + 256u;
    srmech_status_t st = SRMECH_OK;
    assert(c != NULL);
    assert((uintptr_t)ws % sizeof(uint32_t) == 0u || ws == NULL);
    c->cap = cap;
    if (words < carrier_words + scratch_words) { return SRMECH_ERR_OVERFLOW; }
    c->pool = base;
    c->pool_words = words - scratch_words;
    c->pool_cur = 0u;
    st |= az_bind(&c->qa_n, base, c->pool_words, &c->pool_cur, cap);
    st |= az_bind(&c->qa_d, base, c->pool_words, &c->pool_cur, cap);
    st |= az_bind(&c->qb_n, base, c->pool_words, &c->pool_cur, cap);
    st |= az_bind(&c->qb_d, base, c->pool_words, &c->pool_cur, cap);
    st |= az_bind(&c->sub_n, base, c->pool_words, &c->pool_cur, cap);
    st |= az_bind(&c->sub_d, base, c->pool_words, &c->pool_cur, cap);
    st |= az_bind(&c->t0, base, c->pool_words, &c->pool_cur, cap);
    st |= az_bind(&c->t1, base, c->pool_words, &c->pool_cur, cap);
    st |= az_bind(&c->g, base, c->pool_words, &c->pool_cur, cap);
    st |= az_bind(&c->rem, base, c->pool_words, &c->pool_cur, cap);
    st |= az_bind(&c->rs0, base, c->pool_words, &c->pool_cur, cap);
    st |= az_bind(&c->rs1, base, c->pool_words, &c->pool_cur, cap);
    st |= az_bind(&c->z0, base, c->pool_words, &c->pool_cur, cap);
    st |= az_bind(&c->z1, base, c->pool_words, &c->pool_cur, cap);
    if (st != SRMECH_OK) { return SRMECH_ERR_OVERFLOW; }
    st = srmech_bigint_set_i64(&c->z0, 0);
    if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&c->z1, 1); }
    if (st != SRMECH_OK) { return st; }
    c->scratch = (void *)(base + (words - scratch_words));
    c->scratch_len = scratch_words * sizeof(uint32_t);
    assert(c->pool_cur <= c->pool_words);
    return SRMECH_OK;
}

/* ---- exact-Q scalar helpers (mirror zeilberger) ------------------- */

static srmech_status_t az_q_reduce(az_ctx_t *c, srmech_bigint_t *num,
                                   srmech_bigint_t *den)
{
    srmech_status_t st;
    assert(c != NULL && num != NULL && den != NULL);
    assert(den->sign != 0);
    if (den->sign < 0) {
        num->sign = (num->sign == 0) ? 0 : -num->sign;
        den->sign = -den->sign;
    }
    if (srmech_bigint_is_zero(num)) { return srmech_bigint_set_i64(den, 1); }
    st = srmech_bigint_gcd(&c->g, num, den, c->scratch, c->scratch_len);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_divmod(&c->rs0, &c->rem, num, &c->g,
                              c->scratch, c->scratch_len);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_divmod(&c->rs1, &c->rem, den, &c->g,
                              c->scratch, c->scratch_len);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(num, &c->rs0);
    if (st != SRMECH_OK) { return st; }
    return srmech_bigint_copy(den, &c->rs1);
}

static srmech_status_t az_q_add(az_ctx_t *c, srmech_bigint_t *on,
                                srmech_bigint_t *od, const srmech_bigint_t *an,
                                const srmech_bigint_t *ad, const srmech_bigint_t *bn,
                                const srmech_bigint_t *bd, int sub)
{
    srmech_status_t st;
    assert(c != NULL && on != NULL && od != NULL);
    assert(an != NULL && bn != NULL);
    st = srmech_bigint_mul(&c->t0, an, bd);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_mul(on, bn, ad);
    if (st != SRMECH_OK) { return st; }
    if (sub) { st = srmech_bigint_sub(od, &c->t0, on); }
    else     { st = srmech_bigint_add(od, &c->t0, on); }
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(on, od);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_mul(od, ad, bd);
    if (st != SRMECH_OK) { return st; }
    return az_q_reduce(c, on, od);
}

static srmech_status_t az_q_mul(az_ctx_t *c, srmech_bigint_t *on,
                                srmech_bigint_t *od, const srmech_bigint_t *an,
                                const srmech_bigint_t *ad, const srmech_bigint_t *bn,
                                const srmech_bigint_t *bd)
{
    srmech_status_t st;
    assert(c != NULL && on != NULL && od != NULL);
    assert(an != NULL && bn != NULL);
    st = srmech_bigint_mul(on, an, bn);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_mul(od, ad, bd);
    if (st != SRMECH_OK) { return st; }
    return az_q_reduce(c, on, od);
}

/* ---- Poly-in-n carve + ops (mirror zeilberger) -------------------- */

static size_t az_trim(const srmech_bigint_t *nums, size_t n)
{
    size_t k = n;
    assert(nums != NULL || n == 0u);
    while (k > 0u && srmech_bigint_is_zero(&nums[k - 1u])) { k--; }
    assert(k <= n);
    return k;
}

static srmech_status_t az_poly_alloc(az_ctx_t *c, az_poly_t *p, size_t terms)
{
    size_t hw = az_hdr_words(), k;
    uint32_t *hn, *hd;
    srmech_status_t st;
    assert(c != NULL && p != NULL && terms > 0u);
    assert(hw >= 1u);
    hn = az_take(c->pool, c->pool_words, &c->pool_cur, hw * terms);
    hd = az_take(c->pool, c->pool_words, &c->pool_cur, hw * terms);
    if (hn == NULL || hd == NULL) { return SRMECH_ERR_OVERFLOW; }
    p->n = (srmech_bigint_t *)(void *)hn;
    p->d = (srmech_bigint_t *)(void *)hd;
    p->len = 0u;
    p->cap_terms = terms;
    for (k = 0u; k < terms; k++) {
        st = az_bind(&p->n[k], c->pool, c->pool_words, &c->pool_cur, c->cap);
        if (st == SRMECH_OK) { st = az_bind(&p->d[k], c->pool, c->pool_words,
                                            &c->pool_cur, c->cap); }
        if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&p->n[k], 0); }
        if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&p->d[k], 1); }
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

static srmech_status_t az_poly_zero(az_poly_t *p)
{
    assert(p != NULL);
    assert(p->len <= p->cap_terms);
    p->len = 0u;
    return SRMECH_OK;
}

static srmech_status_t az_poly_copy(az_ctx_t *c, az_poly_t *dst,
                                    const az_poly_t *src)
{
    size_t k;
    srmech_status_t st;
    assert(c != NULL && dst != NULL && src != NULL);
    assert(dst->cap_terms >= src->len);
    (void)c;
    for (k = 0u; k < src->len; k++) {
        st = srmech_bigint_copy(&dst->n[k], &src->n[k]);
        if (st == SRMECH_OK) { st = srmech_bigint_copy(&dst->d[k], &src->d[k]); }
        if (st != SRMECH_OK) { return st; }
    }
    dst->len = src->len;
    return SRMECH_OK;
}

static srmech_status_t az_poly_addsub(az_ctx_t *c, az_poly_t *out,
                                      const az_poly_t *a, const az_poly_t *b,
                                      int sub)
{
    size_t k, m = (a->len > b->len) ? a->len : b->len;
    srmech_status_t st;
    assert(c != NULL && out != NULL && a != NULL && b != NULL);
    assert(out->cap_terms >= m);
    for (k = 0u; k < m; k++) {
        const srmech_bigint_t *an = (k < a->len) ? &a->n[k] : &c->z0;
        const srmech_bigint_t *ad = (k < a->len) ? &a->d[k] : &c->z1;
        const srmech_bigint_t *bn = (k < b->len) ? &b->n[k] : &c->z0;
        const srmech_bigint_t *bd = (k < b->len) ? &b->d[k] : &c->z1;
        st = az_q_add(c, &out->n[k], &out->d[k], an, ad, bn, bd, sub);
        if (st != SRMECH_OK) { return st; }
    }
    out->len = az_trim(out->n, m);
    return SRMECH_OK;
}

static srmech_status_t az_poly_mul(az_ctx_t *c, az_poly_t *out,
                                   const az_poly_t *a, const az_poly_t *b)
{
    size_t i, j, m;
    srmech_status_t st;
    assert(c != NULL && out != NULL && a != NULL && b != NULL);
    if (a->len == 0u || b->len == 0u) { out->len = 0u; return SRMECH_OK; }
    m = a->len + b->len - 1u;
    assert(out->cap_terms >= m);
    for (i = 0u; i < m; i++) {
        st = srmech_bigint_set_i64(&out->n[i], 0);
        if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&out->d[i], 1); }
        if (st != SRMECH_OK) { return st; }
    }
    for (i = 0u; i < a->len; i++) {
        if (srmech_bigint_is_zero(&a->n[i])) { continue; }
        for (j = 0u; j < b->len; j++) {
            if (srmech_bigint_is_zero(&b->n[j])) { continue; }
            st = az_q_mul(c, &c->qa_n, &c->qa_d, &a->n[i], &a->d[i],
                          &b->n[j], &b->d[j]);
            if (st == SRMECH_OK) { st = srmech_bigint_copy(&c->qb_n, &out->n[i + j]); }
            if (st == SRMECH_OK) { st = srmech_bigint_copy(&c->qb_d, &out->d[i + j]); }
            if (st == SRMECH_OK) { st = az_q_add(c, &out->n[i + j], &out->d[i + j],
                                                 &c->qb_n, &c->qb_d,
                                                 &c->qa_n, &c->qa_d, 0); }
            if (st != SRMECH_OK) { return st; }
        }
    }
    out->len = az_trim(out->n, m);
    return SRMECH_OK;
}

/* One synthetic-Horner step for Poly-in-n shift: acc <- acc*(n+h) + coeff. */
static srmech_status_t az_shift_step(az_ctx_t *c, az_poly_t *acc,
                                     const srmech_bigint_t *cn,
                                     const srmech_bigint_t *cd, size_t *deg,
                                     int64_t h)
{
    size_t i, nd = (*deg) + 1u;
    srmech_status_t st;
    assert(c != NULL && acc != NULL && cn != NULL && deg != NULL);
    assert(nd <= acc->cap_terms);
    st = srmech_bigint_set_i64(&c->t1, h);
    if (st != SRMECH_OK) { return st; }
    for (i = nd; i > 0u; i--) {
        size_t idx = i - 1u;
        if (idx < *deg) {
            st = az_q_mul(c, &c->qa_n, &c->qa_d, &c->t1, &c->z1,
                          &acc->n[idx], &acc->d[idx]);
        } else {
            st = srmech_bigint_set_i64(&c->qa_n, 0);
            if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&c->qa_d, 1); }
        }
        if (st != SRMECH_OK) { return st; }
        if (idx > 0u) {
            st = az_q_add(c, &acc->n[idx], &acc->d[idx], &c->qa_n, &c->qa_d,
                          &acc->n[idx - 1u], &acc->d[idx - 1u], 0);
        } else {
            st = az_q_add(c, &acc->n[idx], &acc->d[idx], &c->qa_n, &c->qa_d,
                          cn, cd, 0);
        }
        if (st != SRMECH_OK) { return st; }
    }
    *deg = nd;
    return SRMECH_OK;
}

static srmech_status_t az_poly_shift_n(az_ctx_t *c, az_poly_t *out,
                                       const az_poly_t *p, int64_t h)
{
    size_t k, deg = 0u;
    srmech_status_t st;
    assert(c != NULL && out != NULL && p != NULL);
    if (p->len == 0u) { out->len = 0u; return SRMECH_OK; }
    assert(out->cap_terms >= p->len);
    if (h == 0) { return az_poly_copy(c, out, p); }
    out->len = 0u;
    for (k = p->len; k > 0u; k--) {
        st = az_shift_step(c, out, &p->n[k - 1u], &p->d[k - 1u], &deg, h);
        if (st != SRMECH_OK) { return st; }
    }
    out->len = az_trim(out->n, deg);
    return SRMECH_OK;
}

/* ---- BiPoly carve + ops (mirror zeilberger) ----------------------- */

static srmech_status_t az_bipoly_alloc(az_ctx_t *c, az_bipoly_t *b, size_t k_terms,
                                       size_t n_terms)
{
    size_t dk;
    uint32_t *hk;
    srmech_status_t st;
    assert(c != NULL && b != NULL && k_terms > 0u && n_terms > 0u);
    assert(c->pool != NULL || c->pool_words == 0u);
    hk = az_take(c->pool, c->pool_words, &c->pool_cur,
                 ((sizeof(az_poly_t) + sizeof(uint32_t) - 1u) / sizeof(uint32_t))
                 * k_terms);
    if (hk == NULL) { return SRMECH_ERR_OVERFLOW; }
    b->kc = (az_poly_t *)(void *)hk;
    b->klen = 0u;
    b->k_cap = k_terms;
    for (dk = 0u; dk < k_terms; dk++) {
        st = az_poly_alloc(c, &b->kc[dk], n_terms);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

static void az_bipoly_trim(az_bipoly_t *b)
{
    assert(b != NULL);
    assert(b->klen <= b->k_cap);
    while (b->klen > 0u && b->kc[b->klen - 1u].len == 0u) { b->klen--; }
}

static srmech_status_t az_bipoly_copy(az_ctx_t *c, az_bipoly_t *dst,
                                      const az_bipoly_t *src)
{
    size_t dk;
    srmech_status_t st;
    assert(c != NULL && dst != NULL && src != NULL);
    assert(dst->k_cap >= src->klen);
    for (dk = 0u; dk < src->klen; dk++) {
        st = az_poly_copy(c, &dst->kc[dk], &src->kc[dk]);
        if (st != SRMECH_OK) { return st; }
    }
    dst->klen = src->klen;
    return SRMECH_OK;
}

/* out = a + b (bipoly add), cellwise over k. pacc is reserved scratch (the cellwise
 * exact-Q add uses no cross-cell scratch). */
static srmech_status_t az_bipoly_add(az_ctx_t *c, az_bipoly_t *out,
                                     const az_bipoly_t *a, const az_bipoly_t *b,
                                     az_poly_t *pacc)
{
    size_t dk, m = (a->klen > b->klen) ? a->klen : b->klen;
    srmech_status_t st;
    az_poly_t z;
    assert(c != NULL && out != NULL && a != NULL && b != NULL);
    assert(out->k_cap >= m);
    (void)pacc;
    z.n = NULL; z.d = NULL; z.len = 0u; z.cap_terms = 0u;
    for (dk = 0u; dk < m; dk++) {
        const az_poly_t *ap = (dk < a->klen) ? &a->kc[dk] : &z;
        const az_poly_t *bp = (dk < b->klen) ? &b->kc[dk] : &z;
        st = az_poly_addsub(c, &out->kc[dk], ap, bp, 0);
        if (st != SRMECH_OK) { return st; }
    }
    out->klen = m;
    az_bipoly_trim(out);
    return SRMECH_OK;
}

/* out = a * b (bipoly product). acc/prod Poly-in-n scratch. */
static srmech_status_t az_bipoly_mul(az_ctx_t *c, az_bipoly_t *out,
                                     const az_bipoly_t *a, const az_bipoly_t *b,
                                     az_poly_t *acc, az_poly_t *prod)
{
    size_t i, j, m, dk;
    srmech_status_t st;
    assert(c != NULL && out != NULL && a != NULL && b != NULL);
    assert(acc != NULL && prod != NULL);
    if (a->klen == 0u || b->klen == 0u) { out->klen = 0u; return SRMECH_OK; }
    m = a->klen + b->klen - 1u;
    assert(out->k_cap >= m);
    for (dk = 0u; dk < m; dk++) { (void)az_poly_zero(&out->kc[dk]); }
    for (i = 0u; i < a->klen; i++) {
        if (a->kc[i].len == 0u) { continue; }
        for (j = 0u; j < b->klen; j++) {
            if (b->kc[j].len == 0u) { continue; }
            st = az_poly_mul(c, prod, &a->kc[i], &b->kc[j]);
            if (st == SRMECH_OK) { st = az_poly_copy(c, acc, &out->kc[i + j]); }
            if (st == SRMECH_OK) { st = az_poly_addsub(c, &out->kc[i + j],
                                                       acc, prod, 0); }
            if (st != SRMECH_OK) { return st; }
        }
    }
    out->klen = m;
    az_bipoly_trim(out);
    return SRMECH_OK;
}

/* out(n,k) = p(n, k+1): synthetic Horner over (k+1). acc/tmp bipoly scratch
 * (ping-pong; neither aliases out or p); pacc Poly-in-n scratch. */
static srmech_status_t az_bipoly_shift_k(az_ctx_t *c, az_bipoly_t *out,
                                         const az_bipoly_t *p,
                                         az_bipoly_t *acc, az_bipoly_t *tmp,
                                         az_poly_t *pacc)
{
    size_t i, dk;
    srmech_status_t st;
    assert(c != NULL && out != NULL && p != NULL);
    assert(acc != NULL && tmp != NULL && acc != tmp);
    if (p->klen == 0u) { out->klen = 0u; return SRMECH_OK; }
    acc->klen = 0u;
    for (i = p->klen; i > 0u; i--) {
        size_t alen = acc->klen, m = alen + 1u;
        assert(tmp->k_cap >= m);
        for (dk = 0u; dk < m; dk++) {
            const az_poly_t *shifted = (dk >= 1u) ? &acc->kc[dk - 1u] : NULL;
            const az_poly_t *same = (dk < alen) ? &acc->kc[dk] : NULL;
            if (shifted != NULL && same != NULL) {
                st = az_poly_addsub(c, &tmp->kc[dk], shifted, same, 0);
            } else if (shifted != NULL) {
                st = az_poly_copy(c, &tmp->kc[dk], shifted);
            } else if (same != NULL) {
                st = az_poly_copy(c, &tmp->kc[dk], same);
            } else {
                st = az_poly_zero(&tmp->kc[dk]);
            }
            if (st != SRMECH_OK) { return st; }
        }
        tmp->klen = m;
        st = az_poly_addsub(c, pacc, &tmp->kc[0], &p->kc[i - 1u], 0);
        if (st == SRMECH_OK) { st = az_poly_copy(c, &tmp->kc[0], pacc); }
        if (st != SRMECH_OK) { return st; }
        az_bipoly_trim(tmp);
        st = az_bipoly_copy(c, acc, tmp);
        if (st != SRMECH_OK) { return st; }
    }
    return az_bipoly_copy(c, out, acc);
}

/* ---- TriPoly carve + ops ------------------------------------------ */

static srmech_status_t az_tripoly_alloc(az_ctx_t *c, az_tripoly_t *t, size_t j_terms,
                                        size_t k_terms, size_t n_terms)
{
    size_t dj;
    uint32_t *hj;
    srmech_status_t st;
    assert(c != NULL && t != NULL && j_terms > 0u && k_terms > 0u && n_terms > 0u);
    assert(c->pool != NULL || c->pool_words == 0u);
    hj = az_take(c->pool, c->pool_words, &c->pool_cur,
                 ((sizeof(az_bipoly_t) + sizeof(uint32_t) - 1u) / sizeof(uint32_t))
                 * j_terms);
    if (hj == NULL) { return SRMECH_ERR_OVERFLOW; }
    t->jb = (az_bipoly_t *)(void *)hj;
    t->jlen = 0u;
    t->j_cap = j_terms;
    for (dj = 0u; dj < j_terms; dj++) {
        st = az_bipoly_alloc(c, &t->jb[dj], k_terms, n_terms);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

static void az_tripoly_trim(az_tripoly_t *t)
{
    assert(t != NULL);
    assert(t->jlen <= t->j_cap);
    while (t->jlen > 0u && t->jb[t->jlen - 1u].klen == 0u) { t->jlen--; }
}

static srmech_status_t az_tripoly_copy(az_ctx_t *c, az_tripoly_t *dst,
                                       const az_tripoly_t *src)
{
    size_t dj;
    srmech_status_t st;
    assert(c != NULL && dst != NULL && src != NULL);
    assert(dst->j_cap >= src->jlen);
    for (dj = 0u; dj < src->jlen; dj++) {
        st = az_bipoly_copy(c, &dst->jb[dj], &src->jb[dj]);
        if (st != SRMECH_OK) { return st; }
    }
    dst->jlen = src->jlen;
    return SRMECH_OK;
}

/* out = a * b (tripoly product: j-convolution of BiPoly blocks). */
static srmech_status_t az_tripoly_mul(az_ctx_t *c, az_tripoly_t *out,
                                      const az_tripoly_t *a, const az_tripoly_t *b,
                                      az_bipoly_t *bacc, az_bipoly_t *bprod,
                                      az_poly_t *pacc, az_poly_t *pprod)
{
    size_t i, j, m, dj;
    srmech_status_t st;
    assert(c != NULL && out != NULL && a != NULL && b != NULL);
    assert(bacc != NULL && bprod != NULL);
    if (a->jlen == 0u || b->jlen == 0u) { out->jlen = 0u; return SRMECH_OK; }
    m = a->jlen + b->jlen - 1u;
    assert(out->j_cap >= m);
    for (dj = 0u; dj < m; dj++) { out->jb[dj].klen = 0u; }
    for (i = 0u; i < a->jlen; i++) {
        if (a->jb[i].klen == 0u) { continue; }
        for (j = 0u; j < b->jlen; j++) {
            if (b->jb[j].klen == 0u) { continue; }
            st = az_bipoly_mul(c, bprod, &a->jb[i], &b->jb[j], pacc, pprod);
            if (st == SRMECH_OK) { st = az_bipoly_copy(c, bacc, &out->jb[i + j]); }
            if (st == SRMECH_OK) { st = az_bipoly_add(c, &out->jb[i + j], bacc,
                                                      bprod, pacc); }
            if (st != SRMECH_OK) { return st; }
        }
    }
    out->jlen = m;
    az_tripoly_trim(out);
    return SRMECH_OK;
}

/* out(n,j,k) = p(n+h,j,k): shift every (j,k) Poly-in-n by +h. */
static srmech_status_t az_tripoly_shift_n(az_ctx_t *c, az_tripoly_t *out,
                                          const az_tripoly_t *p, int64_t h)
{
    size_t dj, dk;
    srmech_status_t st;
    assert(c != NULL && out != NULL && p != NULL);
    assert(out->j_cap >= p->jlen);
    for (dj = 0u; dj < p->jlen; dj++) {
        const az_bipoly_t *src = &p->jb[dj];
        az_bipoly_t *dst = &out->jb[dj];
        assert(dst->k_cap >= src->klen);
        for (dk = 0u; dk < src->klen; dk++) {
            st = az_poly_shift_n(c, &dst->kc[dk], &src->kc[dk], h);
            if (st != SRMECH_OK) { return st; }
        }
        dst->klen = src->klen;
        az_bipoly_trim(dst);
    }
    out->jlen = p->jlen;
    az_tripoly_trim(out);
    return SRMECH_OK;
}

/* out(n,j,k) = p(n,j,k+1): shift_k each j-block. */
static srmech_status_t az_tripoly_shift_k(az_ctx_t *c, az_tripoly_t *out,
                                          const az_tripoly_t *p,
                                          az_bipoly_t *bacc, az_bipoly_t *btmp,
                                          az_poly_t *pacc)
{
    size_t dj;
    srmech_status_t st;
    assert(c != NULL && out != NULL && p != NULL);
    assert(out->j_cap >= p->jlen);
    for (dj = 0u; dj < p->jlen; dj++) {
        st = az_bipoly_shift_k(c, &out->jb[dj], &p->jb[dj], bacc, btmp, pacc);
        if (st != SRMECH_OK) { return st; }
    }
    out->jlen = p->jlen;
    az_tripoly_trim(out);
    return SRMECH_OK;
}

/* out(n,j,k) = p(n,j+1,k): synthetic Horner over (j+1) on the BiPoly blocks. acc/tmp
 * tripoly scratch (ping-pong; neither aliases out or p); bacc/bprod BiPoly scratch;
 * pacc/pprod Poly-in-n scratch. */
static srmech_status_t az_tripoly_shift_j(az_ctx_t *c, az_tripoly_t *out,
                                          const az_tripoly_t *p,
                                          az_tripoly_t *acc, az_tripoly_t *tmp,
                                          az_bipoly_t *bacc, az_bipoly_t *bprod,
                                          az_poly_t *pacc, az_poly_t *pprod)
{
    size_t i, dj;
    srmech_status_t st;
    assert(c != NULL && out != NULL && p != NULL);
    assert(acc != NULL && tmp != NULL && acc != tmp);
    (void)bprod;
    (void)pprod;
    if (p->jlen == 0u) { out->jlen = 0u; return SRMECH_OK; }
    acc->jlen = 0u;
    for (i = p->jlen; i > 0u; i--) {
        size_t alen = acc->jlen, m = alen + 1u;
        assert(tmp->j_cap >= m);
        for (dj = 0u; dj < m; dj++) {
            const az_bipoly_t *shifted = (dj >= 1u) ? &acc->jb[dj - 1u] : NULL;
            const az_bipoly_t *same = (dj < alen) ? &acc->jb[dj] : NULL;
            if (shifted != NULL && same != NULL) {
                st = az_bipoly_copy(c, bacc, shifted);
                if (st == SRMECH_OK) { st = az_bipoly_add(c, &tmp->jb[dj], bacc,
                                                          same, pacc); }
            } else if (shifted != NULL) {
                st = az_bipoly_copy(c, &tmp->jb[dj], shifted);
            } else if (same != NULL) {
                st = az_bipoly_copy(c, &tmp->jb[dj], same);
            } else {
                tmp->jb[dj].klen = 0u;
                st = SRMECH_OK;
            }
            if (st != SRMECH_OK) { return st; }
        }
        tmp->jlen = m;
        st = az_bipoly_copy(c, bacc, &tmp->jb[0]);
        if (st == SRMECH_OK) { st = az_bipoly_add(c, &tmp->jb[0], bacc,
                                                  &p->jb[i - 1u], pacc); }
        if (st != SRMECH_OK) { return st; }
        az_tripoly_trim(tmp);
        st = az_tripoly_copy(c, acc, tmp);
        if (st != SRMECH_OK) { return st; }
    }
    return az_tripoly_copy(c, out, acc);
}

/* ===================================================================
 * The orchestration: try L=0..AZ_MAX_ORDER, build the homogeneous system, solve via
 * srmech_qmat_rref, read a nonzero-a-block kernel vector.
 * =================================================================== */

/* The working-tripoly roster for one order attempt. */
typedef struct az_solve {
    az_tripoly_t rn_n, rn_d, rj_n, rj_d, rk_n, rk_d;  /* the six input ratios       */
    az_tripoly_t den_p, dp_j1, dp_k1;                 /* D_P, D_P(j+1), D_P(k+1)     */
    az_tripoly_t b0, b1, b2, b3;                      /* general scratch             */
    az_tripoly_t sj_acc, sj_tmp;                      /* shift_j scratch             */
    az_tripoly_t contrib, xmono;                      /* per-column / x monomial     */
    az_tripoly_t *rho_n, *rho_d, *rho_common;         /* order-indexed rho arrays    */
    az_bipoly_t  bacc, bprod;                         /* BiPoly scratch              */
    az_poly_t    pacc, pprod, pscr;                   /* Poly-in-n scratch           */
    size_t       max_order, jt, kt, nt;
} az_solve_t;

/* Count of n-coefficients across a flat (j,k)-cell length array of `cells` cells. */
static size_t az_count(const size_t *nlen, size_t cells)
{
    size_t i, total = 0u;
    assert(nlen != NULL || cells == 0u);
    assert(cells == 0u || nlen != NULL);
    for (i = 0u; i < cells; i++) { total += nlen[i]; }
    return total;
}

/* Load a nested-bridge tripoly (flat (num,den) stream + per-(j,k)-cell n-run lengths
 * + the (jdeg, kdeg) shape) into an az_tripoly. The stream is j-major then k then n. */
static srmech_status_t az_load_tripoly(az_ctx_t *c, az_tripoly_t *t,
                                       const srmech_bigint_t *cn,
                                       const srmech_bigint_t *cd,
                                       const size_t *nlen, size_t jdeg, size_t kdeg)
{
    size_t dj, dk, j, idx = 0u, cell = 0u;
    srmech_status_t st;
    assert(c != NULL && t != NULL);
    assert(t->j_cap >= jdeg);
    (void)c;
    for (dj = 0u; dj < jdeg; dj++) {
        az_bipoly_t *bib = &t->jb[dj];
        assert(bib->k_cap >= kdeg);
        for (dk = 0u; dk < kdeg; dk++) {
            size_t nn = nlen[cell];
            assert(bib->kc[dk].cap_terms >= nn);
            for (j = 0u; j < nn; j++) {
                st = srmech_bigint_copy(&bib->kc[dk].n[j], &cn[idx + j]);
                if (st == SRMECH_OK) { st = srmech_bigint_copy(&bib->kc[dk].d[j],
                                                               &cd[idx + j]); }
                if (st != SRMECH_OK) { return st; }
            }
            bib->kc[dk].len = az_trim(bib->kc[dk].n, nn);
            idx += nn;
            cell++;
        }
        bib->klen = kdeg;
        az_bipoly_trim(bib);
    }
    t->jlen = jdeg;
    az_tripoly_trim(t);
    return SRMECH_OK;
}

static srmech_status_t az_set_one(az_ctx_t *c, az_tripoly_t *t)
{
    srmech_status_t st;
    assert(c != NULL && t != NULL);
    assert(t->j_cap >= 1u && t->jb[0].k_cap >= 1u && t->jb[0].kc[0].cap_terms >= 1u);
    (void)c;
    st = srmech_bigint_set_i64(&t->jb[0].kc[0].n[0], 1);
    if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&t->jb[0].kc[0].d[0], 1); }
    if (st != SRMECH_OK) { return st; }
    t->jb[0].kc[0].len = 1u;
    t->jb[0].klen = 1u;
    t->jlen = 1u;
    return SRMECH_OK;
}

static srmech_status_t az_solve_alloc(az_ctx_t *c, az_solve_t *s, size_t jt,
                                      size_t kt, size_t nt, size_t order)
{
    size_t hdr = ((sizeof(az_tripoly_t) + sizeof(uint32_t) - 1u) / sizeof(uint32_t));
    uint32_t *arr;
    size_t i;
    srmech_status_t st = SRMECH_OK;
    assert(c != NULL && s != NULL && jt > 0u && kt > 0u && nt > 0u);
    assert(order <= AZ_MAX_ORDER);
    s->max_order = order; s->jt = jt; s->kt = kt; s->nt = nt;
    st |= az_tripoly_alloc(c, &s->rn_n, jt, kt, nt);
    st |= az_tripoly_alloc(c, &s->rn_d, jt, kt, nt);
    st |= az_tripoly_alloc(c, &s->rj_n, jt, kt, nt);
    st |= az_tripoly_alloc(c, &s->rj_d, jt, kt, nt);
    st |= az_tripoly_alloc(c, &s->rk_n, jt, kt, nt);
    st |= az_tripoly_alloc(c, &s->rk_d, jt, kt, nt);
    st |= az_tripoly_alloc(c, &s->den_p, jt, kt, nt);
    st |= az_tripoly_alloc(c, &s->dp_j1, jt, kt, nt);
    st |= az_tripoly_alloc(c, &s->dp_k1, jt, kt, nt);
    st |= az_tripoly_alloc(c, &s->b0, jt, kt, nt);
    st |= az_tripoly_alloc(c, &s->b1, jt, kt, nt);
    st |= az_tripoly_alloc(c, &s->b2, jt, kt, nt);
    st |= az_tripoly_alloc(c, &s->b3, jt, kt, nt);
    st |= az_tripoly_alloc(c, &s->sj_acc, jt, kt, nt);
    st |= az_tripoly_alloc(c, &s->sj_tmp, jt, kt, nt);
    st |= az_tripoly_alloc(c, &s->contrib, jt, kt, nt);
    st |= az_tripoly_alloc(c, &s->xmono, jt, kt, nt);
    st |= az_bipoly_alloc(c, &s->bacc, kt, nt);
    st |= az_bipoly_alloc(c, &s->bprod, kt, nt);
    st |= az_poly_alloc(c, &s->pacc, nt);
    st |= az_poly_alloc(c, &s->pprod, nt);
    st |= az_poly_alloc(c, &s->pscr, nt);
    if (st != SRMECH_OK) { return SRMECH_ERR_OVERFLOW; }
    arr = az_take(c->pool, c->pool_words, &c->pool_cur, hdr * (order + 1u) * 3u);
    if (arr == NULL) { return SRMECH_ERR_OVERFLOW; }
    s->rho_n = (az_tripoly_t *)(void *)arr;
    s->rho_d = s->rho_n + (order + 1u);
    s->rho_common = s->rho_d + (order + 1u);
    for (i = 0u; i <= order; i++) {
        st = az_tripoly_alloc(c, &s->rho_n[i], jt, kt, nt);
        if (st == SRMECH_OK) { st = az_tripoly_alloc(c, &s->rho_d[i], jt, kt, nt); }
        if (st == SRMECH_OK) { st = az_tripoly_alloc(c, &s->rho_common[i], jt, kt, nt); }
        if (st != SRMECH_OK) { return SRMECH_ERR_OVERFLOW; }
    }
    return SRMECH_OK;
}

/* tri-multiply wrapper (s scratch BiPoly/Poly threaded). out != a,b. */
static srmech_status_t az_smul(az_ctx_t *c, az_solve_t *s, az_tripoly_t *out,
                               const az_tripoly_t *a, const az_tripoly_t *b)
{
    assert(c != NULL && s != NULL && out != NULL);
    assert(a != NULL && b != NULL);
    return az_tripoly_mul(c, out, a, b, &s->bacc, &s->bprod, &s->pacc, &s->pprod);
}

/* Build rho_common[i], D_P, D_P(j+1), D_P(k+1) for the given order. */
static srmech_status_t az_build_rhos(az_ctx_t *c, az_solve_t *s, size_t order)
{
    size_t i, t;
    srmech_status_t st;
    assert(c != NULL && s != NULL && order <= s->max_order);
    assert(s->rho_n != NULL && s->rho_d != NULL);
    st = az_set_one(c, &s->rho_n[0]);
    if (st == SRMECH_OK) { st = az_set_one(c, &s->rho_d[0]); }
    if (st != SRMECH_OK) { return st; }
    for (i = 1u; i <= order; i++) {
        st = az_tripoly_shift_n(c, &s->b0, &s->rn_n, (int64_t)(i - 1u));
        if (st == SRMECH_OK) { st = az_smul(c, s, &s->rho_n[i], &s->rho_n[i - 1u], &s->b0); }
        if (st == SRMECH_OK) { st = az_tripoly_shift_n(c, &s->b1, &s->rn_d, (int64_t)(i - 1u)); }
        if (st == SRMECH_OK) { st = az_smul(c, s, &s->rho_d[i], &s->rho_d[i - 1u], &s->b1); }
        if (st != SRMECH_OK) { return st; }
    }
    st = az_tripoly_copy(c, &s->den_p, &s->rho_d[0]);
    for (i = 1u; st == SRMECH_OK && i <= order; i++) {
        st = az_smul(c, s, &s->b0, &s->den_p, &s->rho_d[i]);
        if (st == SRMECH_OK) { st = az_tripoly_copy(c, &s->den_p, &s->b0); }
    }
    if (st != SRMECH_OK) { return st; }
    for (i = 0u; i <= order; i++) {
        st = az_tripoly_copy(c, &s->b2, &s->rho_n[i]);
        for (t = 0u; st == SRMECH_OK && t <= order; t++) {
            if (t == i) { continue; }
            st = az_smul(c, s, &s->b0, &s->b2, &s->rho_d[t]);
            if (st == SRMECH_OK) { st = az_tripoly_copy(c, &s->b2, &s->b0); }
        }
        if (st == SRMECH_OK) { st = az_tripoly_copy(c, &s->rho_common[i], &s->b2); }
        if (st != SRMECH_OK) { return st; }
    }
    st = az_tripoly_shift_j(c, &s->dp_j1, &s->den_p, &s->sj_acc, &s->sj_tmp,
                            &s->bacc, &s->bprod, &s->pacc, &s->pprod);
    if (st == SRMECH_OK) { st = az_tripoly_shift_k(c, &s->dp_k1, &s->den_p,
                                                   &s->bacc, &s->bprod, &s->pacc); }
    return st;
}

/* Max n-degree (coefficient COUNT) across a tripoly's (j,k) cells. */
static size_t az_tri_ndeg1(const az_tripoly_t *t)
{
    size_t dj, dk, d = 0u;
    assert(t != NULL);
    assert(t->jlen <= t->j_cap);
    for (dj = 0u; dj < t->jlen; dj++) {
        const az_bipoly_t *bib = &t->jb[dj];
        for (dk = 0u; dk < bib->klen; dk++) {
            if (bib->kc[dk].len > d) { d = bib->kc[dk].len; }
        }
    }
    return d;                                    /* a coefficient COUNT (deg+1)    */
}

/* The n-degree bound (count) for a_i(n): max input n-count + 1 (the +1 over the
 * count = deg+2). Mirrors the Python _ansatz_n_degree (returns deg+1; here a count
 * deg+2). */
static size_t az_ndeg_bound(const az_solve_t *s, size_t order)
{
    size_t d = 1u, i;
    const az_tripoly_t *ins[5];
    assert(s != NULL);
    assert(order <= s->max_order);
    ins[0] = &s->den_p; ins[1] = &s->rj_n; ins[2] = &s->rj_d;
    ins[3] = &s->rk_n; ins[4] = &s->rk_d;
    for (i = 0u; i < 5u; i++) {
        size_t nd = az_tri_ndeg1(ins[i]);
        if (nd > d) { d = nd; }
    }
    for (i = 0u; i <= order; i++) {
        size_t nd = az_tri_ndeg1(&s->rho_common[i]);
        if (nd > d) { d = nd; }
    }
    return d + 1u;                               /* n-coefficient COUNT (deg+2)     */
}

/* Set tripoly `out` to the single monomial n^dn * j^dj * k^dk. */
static srmech_status_t az_set_monomial(az_ctx_t *c, az_tripoly_t *out,
                                       size_t dn, size_t dj, size_t dk)
{
    size_t i;
    srmech_status_t st;
    assert(c != NULL && out != NULL);
    assert(out->j_cap > dj && out->jb[dj].k_cap > dk);
    assert(out->jb[dj].kc[dk].cap_terms > dn);
    (void)c;
    for (i = 0u; i <= dj; i++) { out->jb[i].klen = 0u; }
    for (i = 0u; i <= dk; i++) { (void)az_poly_zero(&out->jb[dj].kc[i]); }
    for (i = 0u; i <= dn; i++) {
        st = srmech_bigint_set_i64(&out->jb[dj].kc[dk].n[i], (i == dn) ? 1 : 0);
        if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&out->jb[dj].kc[dk].d[i], 1); }
        if (st != SRMECH_OK) { return st; }
    }
    out->jb[dj].kc[dk].len = dn + 1u;
    out->jb[dj].klen = dk + 1u;
    out->jlen = dj + 1u;
    return SRMECH_OK;
}

/* Scale every (j,k) coefficient of `in` by the monomial n^dn -> out. */
static srmech_status_t az_scale_nmono(az_ctx_t *c, az_tripoly_t *out,
                                      const az_tripoly_t *in, size_t dn,
                                      az_poly_t *mono)
{
    size_t dj, dk, i;
    srmech_status_t st;
    assert(c != NULL && out != NULL && in != NULL && mono != NULL);
    assert(mono->cap_terms > dn);
    for (i = 0u; i <= dn; i++) {
        st = srmech_bigint_set_i64(&mono->n[i], (i == dn) ? 1 : 0);
        if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&mono->d[i], 1); }
        if (st != SRMECH_OK) { return st; }
    }
    mono->len = dn + 1u;
    for (dj = 0u; dj < in->jlen; dj++) {
        const az_bipoly_t *bsrc = &in->jb[dj];
        az_bipoly_t *bdst = &out->jb[dj];
        for (dk = 0u; dk < bsrc->klen; dk++) {
            st = az_poly_mul(c, &bdst->kc[dk], &bsrc->kc[dk], mono);
            if (st != SRMECH_OK) { return st; }
        }
        bdst->klen = bsrc->klen;
        az_bipoly_trim(bdst);
    }
    out->jlen = in->jlen;
    az_tripoly_trim(out);
    return SRMECH_OK;
}

/* Accumulate +/- a tripoly contrib into the dense system at column `col`. The system
 * is indexed (dn, dj, dk) -> row = (dj*nrow_k + dk)*nrow_n + dn. */
static srmech_status_t az_acc_contrib(az_ctx_t *c, const az_tripoly_t *contrib,
                                      srmech_bigint_t *a_n, srmech_bigint_t *a_d,
                                      size_t col, int sign, size_t total,
                                      size_t nrow_n, size_t nrow_j, size_t nrow_k)
{
    size_t dj, dk, dn;
    srmech_status_t st;
    assert(c != NULL && contrib != NULL && a_n != NULL);
    assert(nrow_n > 0u && nrow_j > 0u && nrow_k > 0u);
    for (dj = 0u; dj < contrib->jlen; dj++) {
        const az_bipoly_t *bib = &contrib->jb[dj];
        if (dj >= nrow_j) { return SRMECH_ERR_OVERFLOW; }
        for (dk = 0u; dk < bib->klen; dk++) {
            const az_poly_t *kp = &bib->kc[dk];
            if (dk >= nrow_k) { return SRMECH_ERR_OVERFLOW; }
            for (dn = 0u; dn < kp->len; dn++) {
                size_t row, idx;
                if (srmech_bigint_is_zero(&kp->n[dn])) { continue; }
                if (dn >= nrow_n) { return SRMECH_ERR_OVERFLOW; }
                row = (dj * nrow_k + dk) * nrow_n + dn;
                idx = row * total + col;
                st = az_q_add(c, &c->sub_n, &c->sub_d, &a_n[idx], &a_d[idx],
                              &kp->n[dn], &kp->d[dn], (sign > 0) ? 0 : 1);
                if (st == SRMECH_OK) { st = srmech_bigint_copy(&a_n[idx], &c->sub_n); }
                if (st == SRMECH_OK) { st = srmech_bigint_copy(&a_d[idx], &c->sub_d); }
                if (st != SRMECH_OK) { return st; }
            }
        }
    }
    return SRMECH_OK;
}

/* The certificate column layout sizes. */
typedef struct az_dims {
    size_t ndeg_cnt;      /* a_i(n) n-coefficient count                          */
    size_t xn_cnt;        /* certificate n-coefficient count                     */
    size_t xjk_cnt;       /* certificate per-(j,k) degree count (each of j, k)   */
    size_t a_block;       /* (order+1) * ndeg_cnt                                */
    size_t x_block;       /* xn_cnt * xjk_cnt * xjk_cnt (one certificate)        */
    size_t total;         /* a_block + 2 * x_block                               */
    size_t nrow_n, nrow_j, nrow_k, n_rows;
} az_dims_t;

/* The clearing factors for the a-block + the two certificate blocks. b0..b3 +
 * contrib hold scratch products; xmono the per-x monomial. */
static srmech_status_t az_fill_a_cols(az_ctx_t *c, az_solve_t *s, size_t order,
                                      const az_dims_t *d, srmech_bigint_t *a_n,
                                      srmech_bigint_t *a_d)
{
    size_t i, p;
    srmech_status_t st;
    assert(c != NULL && s != NULL && d != NULL && a_n != NULL);
    assert(a_d != NULL && d->ndeg_cnt > 0u);
    /* lhs_tail = D_P(j+1) * D_P(k+1) * rj_den * rk_den */
    st = az_smul(c, s, &s->b0, &s->dp_j1, &s->dp_k1);
    if (st == SRMECH_OK) { st = az_smul(c, s, &s->b1, &s->b0, &s->rj_d); }
    if (st == SRMECH_OK) { st = az_smul(c, s, &s->b2, &s->b1, &s->rk_d); } /* b2 = lhs_tail */
    if (st != SRMECH_OK) { return st; }
    for (i = 0u; i <= order; i++) {
        /* cof = (Prod_{t!=i} rho_d[t]) * lhs_tail; base = rho_n[i] * cof. We build
         * Prod_{t!=i} rho_d[t] into b0 then * lhs_tail (b2) then * rho_n[i]. */
        size_t t;
        st = az_set_one(c, &s->b0);
        for (t = 0u; st == SRMECH_OK && t <= order; t++) {
            if (t == i) { continue; }
            st = az_smul(c, s, &s->b1, &s->b0, &s->rho_d[t]);
            if (st == SRMECH_OK) { st = az_tripoly_copy(c, &s->b0, &s->b1); }
        }
        if (st == SRMECH_OK) { st = az_smul(c, s, &s->b1, &s->b0, &s->b2); }
        if (st == SRMECH_OK) { st = az_smul(c, s, &s->b3, &s->b1, &s->rho_n[i]); }
        if (st != SRMECH_OK) { return st; }
        for (p = 0u; p < d->ndeg_cnt; p++) {
            size_t col = i * d->ndeg_cnt + p;
            st = az_scale_nmono(c, &s->contrib, &s->b3, p, &s->pscr);
            if (st == SRMECH_OK) { st = az_acc_contrib(c, &s->contrib, a_n, a_d, col,
                                                       +1, d->total, d->nrow_n,
                                                       d->nrow_j, d->nrow_k); }
            if (st != SRMECH_OK) { return st; }
        }
    }
    return SRMECH_OK;
}

/* Fill one certificate block (j or k). `is_k` selects the k-direction; cof1/cof2 +
 * rdir_n + shift carry the direction. b0..b3/contrib/xmono scratch. */
static srmech_status_t az_fill_cert_cols(az_ctx_t *c, az_solve_t *s,
                                         const az_dims_t *d, srmech_bigint_t *a_n,
                                         srmech_bigint_t *a_d, size_t base_col,
                                         int is_k)
{
    size_t dn, dj, dk, idx = 0u;
    srmech_status_t st;
    const az_tripoly_t *rdir_n = is_k ? &s->rk_n : &s->rj_n;
    assert(c != NULL && s != NULL && d != NULL && a_n != NULL);
    assert(a_d != NULL && rdir_n != NULL);
    /* cof1 = D_P * D_P(other+1) * rdir_other_den ; cof2 = D_P(j+1)*D_P(k+1)*rj_d*rk_d.
     * For j: cof1 = D_P * D_P(k+1) * rk_den ; for k: cof1 = D_P * D_P(j+1) * rj_den. */
    st = az_smul(c, s, &s->b0, &s->den_p, is_k ? &s->dp_j1 : &s->dp_k1);
    if (st == SRMECH_OK) { st = az_smul(c, s, &s->b1, &s->b0,
                                        is_k ? &s->rj_d : &s->rk_d); } /* b1 = cof1 */
    if (st == SRMECH_OK) { st = az_smul(c, s, &s->b2, &s->dp_j1, &s->dp_k1); }
    if (st == SRMECH_OK) { st = az_smul(c, s, &s->b3, &s->b2, &s->rj_d); }
    if (st == SRMECH_OK) { st = az_smul(c, s, &s->b0, &s->b3, &s->rk_d); } /* b0 = cof2 */
    if (st != SRMECH_OK) { return st; }
    /* b1 = cof1, b0 = cof2. Pre-multiply cof1 by rdir_n into b2 = rdir_n*cof1. */
    st = az_smul(c, s, &s->b2, rdir_n, &s->b1);
    if (st != SRMECH_OK) { return st; }
    for (dn = 0u; dn < d->xn_cnt; dn++) {
        for (dj = 0u; dj < d->xjk_cnt; dj++) {
            for (dk = 0u; dk < d->xjk_cnt; dk++) {
                size_t col = base_col + idx;
                st = az_set_monomial(c, &s->xmono, dn, dj, dk);
                /* term1: mono(shift+1) * rdir_n * cof1 = mono(shift) * b2 */
                if (st == SRMECH_OK) {
                    if (is_k) {
                        st = az_tripoly_shift_k(c, &s->contrib, &s->xmono,
                                                &s->bacc, &s->bprod, &s->pacc);
                    } else {
                        st = az_tripoly_shift_j(c, &s->contrib, &s->xmono,
                                                &s->sj_acc, &s->sj_tmp, &s->bacc,
                                                &s->bprod, &s->pacc, &s->pprod);
                    }
                }
                if (st == SRMECH_OK) { st = az_smul(c, s, &s->b3, &s->contrib, &s->b2); }
                if (st == SRMECH_OK) { st = az_acc_contrib(c, &s->b3, a_n, a_d, col,
                                                           -1, d->total, d->nrow_n,
                                                           d->nrow_j, d->nrow_k); }
                /* term2: mono * cof2 (b0) */
                if (st == SRMECH_OK) { st = az_smul(c, s, &s->b3, &s->xmono, &s->b0); }
                if (st == SRMECH_OK) { st = az_acc_contrib(c, &s->b3, a_n, a_d, col,
                                                           +1, d->total, d->nrow_n,
                                                           d->nrow_j, d->nrow_k); }
                if (st != SRMECH_OK) { return st; }
                idx++;
            }
        }
    }
    return SRMECH_OK;
}

/* Zero the homogeneous matrix, then fill the a-block + the two certificate blocks. */
static srmech_status_t az_fill_matrix(az_ctx_t *c, az_solve_t *s, size_t order,
                                      const az_dims_t *d, srmech_bigint_t *a_n,
                                      srmech_bigint_t *a_d)
{
    size_t i;
    srmech_status_t st;
    assert(c != NULL && s != NULL && d != NULL && a_n != NULL);
    assert(a_d != NULL && d->total > 0u);
    for (i = 0u; i < d->n_rows * d->total; i++) {
        st = srmech_bigint_set_i64(&a_n[i], 0);
        if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&a_d[i], 1); }
        if (st != SRMECH_OK) { return st; }
    }
    st = az_fill_a_cols(c, s, order, d, a_n, a_d);
    if (st == SRMECH_OK) { st = az_fill_cert_cols(c, s, d, a_n, a_d,
                                                  d->a_block, 0); }
    if (st == SRMECH_OK) { st = az_fill_cert_cols(c, s, d, a_n, a_d,
                                                  d->a_block + d->x_block, 1); }
    return st;
}

/* The qmat-solve scratch carved from the ctx pool tail (mirror zeilberger). */
typedef struct az_qarena {
    srmech_bigint_t *a_n, *a_d;
    srmech_bigint_t *o_n, *o_d;
    size_t          *piv;
    void            *qws;
    size_t           qws_words;
} az_qarena_t;

static srmech_status_t az_qcarve_in(az_ctx_t *c, az_qarena_t *q, size_t nrow_full,
                                    size_t total)
{
    size_t hw = az_hdr_words(), cells = nrow_full * total, i;
    uint32_t *hn, *hd;
    srmech_status_t st;
    assert(c != NULL && q != NULL && nrow_full > 0u && total > 0u);
    assert(cells == nrow_full * total && hw >= 1u);
    hn = az_take(c->pool, c->pool_words, &c->pool_cur, hw * cells);
    hd = az_take(c->pool, c->pool_words, &c->pool_cur, hw * cells);
    if (hn == NULL || hd == NULL) { return SRMECH_ERR_OVERFLOW; }
    q->a_n = (srmech_bigint_t *)(void *)hn; q->a_d = (srmech_bigint_t *)(void *)hd;
    for (i = 0u; i < cells; i++) {
        st = az_bind(&q->a_n[i], c->pool, c->pool_words, &c->pool_cur, c->cap);
        if (st == SRMECH_OK) { st = az_bind(&q->a_d[i], c->pool, c->pool_words,
                                            &c->pool_cur, c->cap); }
        if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&q->a_n[i], 0); }
        if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&q->a_d[i], 1); }
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

static srmech_status_t az_qcarve_out(az_ctx_t *c, az_qarena_t *q, size_t n_rows_c,
                                     size_t total, size_t ecap, size_t qcl)
{
    size_t hw = az_hdr_words(), cells = n_rows_c * total, i;
    uint32_t *on, *od;
    srmech_status_t st;
    assert(c != NULL && q != NULL && n_rows_c > 0u && total > 0u);
    assert(ecap >= 2u && qcl >= 1u);
    on = az_take(c->pool, c->pool_words, &c->pool_cur, hw * cells);
    od = az_take(c->pool, c->pool_words, &c->pool_cur, hw * cells);
    q->piv = (size_t *)(void *)az_take(c->pool, c->pool_words, &c->pool_cur,
                  (sizeof(size_t) / sizeof(uint32_t)) * total + 2u);
    if (on == NULL || od == NULL || q->piv == NULL) { return SRMECH_ERR_OVERFLOW; }
    q->o_n = (srmech_bigint_t *)(void *)on; q->o_d = (srmech_bigint_t *)(void *)od;
    for (i = 0u; i < cells; i++) {
        st = az_bind(&q->o_n[i], c->pool, c->pool_words, &c->pool_cur, (uint32_t)ecap);
        if (st == SRMECH_OK) { st = az_bind(&q->o_d[i], c->pool, c->pool_words,
                                            &c->pool_cur, (uint32_t)ecap); }
        if (st != SRMECH_OK) { return st; }
    }
    q->qws_words = srmech_qmat_ws_bound(qcl, n_rows_c, total) / sizeof(uint32_t);
    q->qws = (void *)az_take(c->pool, c->pool_words, &c->pool_cur, q->qws_words);
    if (q->qws == NULL) { return SRMECH_ERR_OVERFLOW; }
    return SRMECH_OK;
}

static srmech_status_t az_compact_rows(az_qarena_t *q, size_t nrow_full,
                                       size_t total, size_t *n_rows_c)
{
    size_t r, j, w = 0u;
    srmech_status_t st;
    assert(q != NULL && n_rows_c != NULL);
    assert(total > 0u || nrow_full == 0u);
    for (r = 0u; r < nrow_full; r++) {
        int nz = 0;
        for (j = 0u; j < total; j++) {
            if (!srmech_bigint_is_zero(&q->a_n[r * total + j])) { nz = 1; break; }
        }
        if (!nz) { continue; }
        if (w != r) {
            for (j = 0u; j < total; j++) {
                st = srmech_bigint_copy(&q->a_n[w * total + j], &q->a_n[r * total + j]);
                if (st == SRMECH_OK) { st = srmech_bigint_copy(&q->a_d[w * total + j],
                                                               &q->a_d[r * total + j]); }
                if (st != SRMECH_OK) { return st; }
            }
        }
        w++;
    }
    *n_rows_c = w;
    return SRMECH_OK;
}

/* Read a kernel vector with a NONZERO a-block from the RREF output. Mirrors
 * zeilberger's zb_read_kernel free-column scan. */
static srmech_status_t az_read_kernel(az_ctx_t *c, const az_qarena_t *q,
                                      size_t n_rows, size_t total, size_t n_unknowns,
                                      size_t a_block, srmech_bigint_t *vec_n,
                                      srmech_bigint_t *vec_d, int *found)
{
    size_t r, j, f, pc;
    srmech_status_t st;
    assert(c != NULL && q != NULL && vec_n != NULL && found != NULL);
    assert(total == n_unknowns);
    (void)c;
    *found = 0;
    for (f = 0u; f < n_unknowns; f++) {
        int is_pivot = 0, nonzero_a = 0;
        for (r = 0u; r < n_rows; r++) {
            pc = total;
            for (j = 0u; j < total; j++) {
                if (!srmech_bigint_is_zero(&q->o_n[r * total + j])) { pc = j; break; }
            }
            if (pc == f) { is_pivot = 1; break; }
        }
        if (is_pivot) { continue; }
        for (j = 0u; j < n_unknowns; j++) {
            st = srmech_bigint_set_i64(&vec_n[j], (j == f) ? 1 : 0);
            if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&vec_d[j], 1); }
            if (st != SRMECH_OK) { return st; }
        }
        for (r = 0u; r < n_rows; r++) {
            pc = total;
            for (j = 0u; j < total; j++) {
                if (!srmech_bigint_is_zero(&q->o_n[r * total + j])) { pc = j; break; }
            }
            if (pc == total || pc == f) { continue; }
            st = srmech_bigint_copy(&vec_n[pc], &q->o_n[r * total + f]);
            if (st == SRMECH_OK) { st = srmech_bigint_copy(&vec_d[pc],
                                                           &q->o_d[r * total + f]); }
            if (st == SRMECH_OK && !srmech_bigint_is_zero(&vec_n[pc])) {
                vec_n[pc].sign = -vec_n[pc].sign;        /* negate (Class-K sign)  */
            }
            if (st != SRMECH_OK) { return st; }
        }
        for (j = 0u; j < a_block; j++) {
            if (!srmech_bigint_is_zero(&vec_n[j])) { nonzero_a = 1; break; }
        }
        if (nonzero_a) { *found = 1; return SRMECH_OK; }
    }
    return SRMECH_OK;
}

/* Live (trailing-zero-trimmed) length of vec[base..base+span). */
static size_t az_live_len(const srmech_bigint_t *vec_n, size_t base, size_t span)
{
    size_t p, live = 0u;
    assert(vec_n != NULL);
    assert(base + span >= base);
    for (p = 0u; p < span; p++) {
        if (!srmech_bigint_is_zero(&vec_n[base + p])) { live = p + 1u; }
    }
    return live;
}

/* Write the a-block into coeff_* CONTIGUOUSLY (coeff_nlen[i] each segment length).
 * Write one certificate block (j or k) into cert_* as the nested (j,k)-cell grid:
 * cert_nlen[cell] is each cell's live n-run; the per-block (jdeg, kdeg) shape goes to
 * *out_jdeg / *out_kdeg. Both blocks are PACKED. */
static srmech_status_t az_write_coeffs(const srmech_bigint_t *vec_n,
                                       const srmech_bigint_t *vec_d, size_t order,
                                       size_t ndeg_cnt, srmech_bigint_t *coeff_n,
                                       srmech_bigint_t *coeff_d, size_t *coeff_nlen)
{
    size_t i, p, w = 0u;
    srmech_status_t st;
    assert(vec_n != NULL && coeff_n != NULL && coeff_d != NULL && coeff_nlen != NULL);
    assert(vec_d != NULL && ndeg_cnt > 0u);
    for (i = 0u; i <= order; i++) {
        size_t live = az_live_len(vec_n, i * ndeg_cnt, ndeg_cnt);
        for (p = 0u; p < live; p++) {
            st = srmech_bigint_copy(&coeff_n[w], &vec_n[i * ndeg_cnt + p]);
            if (st == SRMECH_OK) { st = srmech_bigint_copy(&coeff_d[w],
                                                           &vec_d[i * ndeg_cnt + p]); }
            if (st != SRMECH_OK) { return st; }
            w++;
        }
        coeff_nlen[i] = live;
    }
    return SRMECH_OK;
}

/* Write one certificate block: x[base + ((dn*xjk + dj)*xjk + dk)] is the coeff of
 * n^dn j^dj k^dk. Emit the nested (j,k)-cell grid (jdeg x kdeg), each cell an n-run;
 * the cell n-run length goes to cert_nlen, the live (jdeg, kdeg) to *out_jdeg/kdeg. */
static srmech_status_t az_write_cert(const srmech_bigint_t *vec_n,
                                     const srmech_bigint_t *vec_d, size_t base,
                                     size_t xn_cnt, size_t xjk_cnt,
                                     srmech_bigint_t *cert_n, srmech_bigint_t *cert_d,
                                     size_t *cert_nlen, size_t *out_jdeg,
                                     size_t *out_kdeg)
{
    size_t dj, dk, dn, w = 0u, cell = 0u;
    srmech_status_t st;
    assert(vec_n != NULL && cert_n != NULL && cert_nlen != NULL);
    assert(out_jdeg != NULL && out_kdeg != NULL);
    for (dj = 0u; dj < xjk_cnt; dj++) {
        for (dk = 0u; dk < xjk_cnt; dk++) {
            size_t live = 0u, p;
            for (p = 0u; p < xn_cnt; p++) {
                size_t off = base + (p * xjk_cnt + dj) * xjk_cnt + dk;
                if (!srmech_bigint_is_zero(&vec_n[off])) { live = p + 1u; }
            }
            for (dn = 0u; dn < live; dn++) {
                size_t off = base + (dn * xjk_cnt + dj) * xjk_cnt + dk;
                st = srmech_bigint_copy(&cert_n[w], &vec_n[off]);
                if (st == SRMECH_OK) { st = srmech_bigint_copy(&cert_d[w], &vec_d[off]); }
                if (st != SRMECH_OK) { return st; }
                w++;
            }
            cert_nlen[cell] = live;
            cell++;
        }
    }
    *out_jdeg = xjk_cnt;
    *out_kdeg = xjk_cnt;
    return SRMECH_OK;
}


/* Compute the column-layout dims for the given order + degree bounds. The certificate
 * n-degree count is the a_i n-degree count (the certificate tracks the a_i n-degree);
 * the per-(j,k) degree count is `xjk_cnt`. */
static void az_dims_for(const az_solve_t *s, size_t order, size_t ndeg_cnt,
                        size_t xjk_cnt, az_dims_t *d)
{
    assert(s != NULL && d != NULL);
    assert(ndeg_cnt > 0u && xjk_cnt > 0u);
    d->ndeg_cnt = ndeg_cnt;
    /* The certificate grid MUST match the Python _jk_monomials(jk_deg): all three of
     * n, j, k range over degree <= jk_deg (a (jk_deg+1)^3 cube), so xn_cnt ==
     * xjk_cnt == (jk_deg+1) here (xjk_cnt is that count). The recurrence-coeff
     * n-degree count ndeg_cnt is independent. This byte-matches the pure path. */
    d->xn_cnt = xjk_cnt;
    d->xjk_cnt = xjk_cnt;
    d->a_block = (order + 1u) * ndeg_cnt;
    d->x_block = d->xn_cnt * xjk_cnt * xjk_cnt;
    d->total = d->a_block + 2u * d->x_block;
    /* the cleared-identity (dn, dj, dk) row span: generous headroom over the input
     * degrees so no contributed monomial is dropped (a dropped monomial -> OVERFLOW
     * -> the pure path). */
    d->nrow_n = ndeg_cnt + az_tri_ndeg1(&s->den_p) + 4u;
    d->nrow_j = xjk_cnt + s->den_p.jlen + 4u;
    d->nrow_k = xjk_cnt + s->den_p.jlen + 4u;
    d->n_rows = d->nrow_n * d->nrow_j * d->nrow_k;
}

/* Attempt one (order, xjk) configuration: assemble, compact, RREF, read kernel; on a
 * found a-nonzero kernel write the outputs + set *out_has. */
/* Assemble + compact + RREF + read a kernel for the dims `d`. Sets *found + writes
 * the kernel into caller-bound vec_n/vec_d (n-unknowns wide). The qmat scratch is
 * carved from the ctx pool (the caller restores the pool mark between configs). */
static srmech_status_t az_assemble_and_solve(az_ctx_t *c, az_solve_t *s, size_t order,
                                             const az_dims_t *d,
                                             srmech_bigint_t *vec_n,
                                             srmech_bigint_t *vec_d, int *found)
{
    az_qarena_t q;
    size_t n_rows_c = 0u, ecap, qcl = 1u, i, rank = 0u;
    srmech_status_t st;
    assert(c != NULL && s != NULL && d != NULL && found != NULL);
    assert(vec_n != NULL && vec_d != NULL);
    *found = 0;
    st = az_qcarve_in(c, &q, d->n_rows, d->total);
    if (st != SRMECH_OK) { return st; }
    st = az_fill_matrix(c, s, order, d, q.a_n, q.a_d);
    if (st != SRMECH_OK) { return st; }
    st = az_compact_rows(&q, d->n_rows, d->total, &n_rows_c);
    if (st != SRMECH_OK) { return st; }
    if (n_rows_c == 0u) { return SRMECH_OK; }
    for (i = 0u; i < n_rows_c * d->total; i++) {
        if (q.a_n[i].n > qcl) { qcl = q.a_n[i].n; }
        if (q.a_d[i].n > qcl) { qcl = q.a_d[i].n; }
    }
    ecap = srmech_qmat_entry_cap(qcl, n_rows_c, d->total);
    st = az_qcarve_out(c, &q, n_rows_c, d->total, ecap, qcl);
    if (st != SRMECH_OK) { return st; }
    st = srmech_qmat_rref(q.a_n, q.a_d, n_rows_c, d->total, q.o_n, q.o_d, &rank,
                          q.piv, q.qws, q.qws_words * sizeof(uint32_t));
    if (st != SRMECH_OK) { return st; }
    return az_read_kernel(c, &q, n_rows_c, d->total, d->total, d->a_block,
                          vec_n, vec_d, found);
}

/* Carve the n-unknowns-wide kernel vector pair from the ctx pool. */
static srmech_status_t az_carve_vec(az_ctx_t *c, size_t total,
                                    srmech_bigint_t **vec_n, srmech_bigint_t **vec_d)
{
    size_t hw = az_hdr_words(), i;
    uint32_t *vh_n, *vh_d;
    srmech_status_t st;
    assert(c != NULL && vec_n != NULL && vec_d != NULL);
    assert(total > 0u);
    vh_n = az_take(c->pool, c->pool_words, &c->pool_cur, hw * total);
    vh_d = az_take(c->pool, c->pool_words, &c->pool_cur, hw * total);
    if (vh_n == NULL || vh_d == NULL) { return SRMECH_ERR_OVERFLOW; }
    *vec_n = (srmech_bigint_t *)(void *)vh_n;
    *vec_d = (srmech_bigint_t *)(void *)vh_d;
    for (i = 0u; i < total; i++) {
        st = az_bind(&(*vec_n)[i], c->pool, c->pool_words, &c->pool_cur, c->cap);
        if (st == SRMECH_OK) { st = az_bind(&(*vec_d)[i], c->pool, c->pool_words,
                                            &c->pool_cur, c->cap); }
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

static srmech_status_t az_try_config(az_ctx_t *c, az_solve_t *s, size_t order,
                                     size_t xjk_cnt, int *out_has,
                                     srmech_bigint_t *coeff_n, srmech_bigint_t *coeff_d,
                                     size_t *coeff_nlen, srmech_bigint_t *cert_j_n,
                                     srmech_bigint_t *cert_j_d, size_t *cert_j_nlen,
                                     size_t *out_jdeg_j, size_t *out_kdeg_j,
                                     srmech_bigint_t *cert_k_n, srmech_bigint_t *cert_k_d,
                                     size_t *cert_k_nlen, size_t *out_jdeg_k,
                                     size_t *out_kdeg_k)
{
    az_dims_t d;
    srmech_bigint_t *vec_n = NULL, *vec_d = NULL;
    size_t ndeg_cnt;
    int found = 0;
    srmech_status_t st;
    assert(c != NULL && s != NULL && out_has != NULL);
    assert(coeff_n != NULL && cert_j_n != NULL && cert_k_n != NULL);
    *out_has = 0;
    ndeg_cnt = az_ndeg_bound(s, order);
    az_dims_for(s, order, ndeg_cnt, xjk_cnt, &d);
    /* decline a wide system to the bounded-memory Python CRT path (the dense qmat
     * arena balloons past AZ_DENSE_MAX_TOTAL; the C never returns a false "no
     * recurrence", it just declines and the pure path decides). */
    if (d.total > AZ_DENSE_MAX_TOTAL) { return SRMECH_OK; }
    st = az_carve_vec(c, d.total, &vec_n, &vec_d);
    if (st != SRMECH_OK) { return st; }
    st = az_assemble_and_solve(c, s, order, &d, vec_n, vec_d, &found);
    if (st != SRMECH_OK) { return st; }
    if (!found) { return SRMECH_OK; }
    st = az_write_coeffs(vec_n, vec_d, order, ndeg_cnt, coeff_n, coeff_d, coeff_nlen);
    if (st == SRMECH_OK) { st = az_write_cert(vec_n, vec_d, d.a_block, d.xn_cnt,
                                              xjk_cnt, cert_j_n, cert_j_d, cert_j_nlen,
                                              out_jdeg_j, out_kdeg_j); }
    if (st == SRMECH_OK) { st = az_write_cert(vec_n, vec_d, d.a_block + d.x_block,
                                              d.xn_cnt, xjk_cnt, cert_k_n, cert_k_d,
                                              cert_k_nlen, out_jdeg_k, out_kdeg_k); }
    if (st != SRMECH_OK) { return st; }
    *out_has = 1;
    return SRMECH_OK;
}

/* The certificate base (n,j,k) DEGREE the C peer sweeps from — mirrors the Python
 * _ansatz_jk_base: the max per-variable degree across D_P + the r_j / r_k ratios.
 * (n-degree included so the cube grid matches Python's _jk_monomials.) Returns a
 * DEGREE (not a count); the sweep adds the count +1 when sizing the grid. */
static size_t az_xjk_base(const az_solve_t *s)
{
    size_t d = 1u, dj, i;
    const az_tripoly_t *ins[5];
    assert(s != NULL);
    assert(s->den_p.j_cap > 0u || s->den_p.jlen == 0u);
    ins[0] = &s->den_p; ins[1] = &s->rj_n; ins[2] = &s->rj_d;
    ins[3] = &s->rk_n; ins[4] = &s->rk_d;
    for (i = 0u; i < 5u; i++) {
        const az_tripoly_t *t = ins[i];
        size_t nd = az_tri_ndeg1(t);             /* n-coeff count = n-degree + 1     */
        if (t->jlen > 0u && t->jlen - 1u > d) { d = t->jlen - 1u; }   /* j-degree    */
        if (nd > 0u && nd - 1u > d) { d = nd - 1u; }                  /* n-degree    */
        for (dj = 0u; dj < t->jlen; dj++) {
            const az_bipoly_t *bib = &t->jb[dj];
            if (bib->klen > 0u && bib->klen - 1u > d) { d = bib->klen - 1u; } /* k */
        }
    }
    return d;                                    /* a per-variable DEGREE           */
}

/* ---- input limb estimate + arena bounds (mirror zeilberger) ------- */

static size_t az_input_limbs(const srmech_bigint_t *cn, size_t total)
{
    size_t k, cl = 1u;
    assert(cn != NULL || total == 0u);
    assert(cl >= 1u);
    for (k = 0u; k < total; k++) { if (cn[k].n > cl) { cl = cn[k].n; } }
    return cl;
}

static size_t az_cap_for(size_t coeff_limbs, size_t order, size_t degree)
{
    size_t cl = (coeff_limbs == 0u) ? 1u : coeff_limbs;
    size_t dg = (degree == 0u) ? 1u : degree;
    size_t og = (order > AZ_MAX_ORDER) ? AZ_MAX_ORDER : order;
    /* The trivariate products accumulate Q over an order-scaled, degree-scaled chain
     * (one more direction than the bivariate zeilberger); an envelope dominating the
     * worst intermediate for the COMMON small-coefficient low-order inputs. A huge
     * input that exceeds this returns OVERFLOW, routing to the pure-Q path. */
    size_t step = cl * (dg + 2u) * (dg + 2u) * (og + 2u) + 8u;
    size_t cap = step * 2u + cl * 4u + 64u;
    assert(cap >= step);
    assert(cap >= cl);
    return cap;
}

size_t srmech_apagodu_zeilberger_out_cap(size_t coeff_limbs, size_t order,
                                         size_t degree)
{
    size_t cap = az_cap_for(coeff_limbs, order, degree);
    assert(cap >= 2u);
    assert(cap >= coeff_limbs);
    return cap;
}

/* per-direction term counts the working tripolys carry. D_P (k/j/n-degree about
 * order*degree) plus the clearing-factor products dominate; bound at about
 * 2*(order+1)*deg. */
static size_t az_terms_for(size_t order, size_t degree)
{
    size_t dg = (degree == 0u) ? 1u : degree;
    size_t terms = 2u * (order + 1u) * dg + 2u * dg + 8u;
    assert(terms >= dg);
    assert(terms >= 8u);
    return terms;
}

/* The realistic max matrix dimension `total` the order-`order` system reaches at
 * this degree (the certificate sweep ceiling), clamped at SRMECH_QMAT_MAX_DIM. */
static size_t az_total_dim(size_t order, size_t degree)
{
    size_t dg = (degree == 0u) ? 1u : degree;
    size_t og = (order > AZ_MAX_ORDER) ? AZ_MAX_ORDER : order;
    size_t ndeg_cnt = (og + 1u) * dg + 2u;
    size_t xjk = dg + 2u;
    size_t a_block = (og + 1u) * ndeg_cnt;
    size_t x_block = ndeg_cnt * xjk * xjk;
    size_t t = a_block + 2u * x_block;
    assert(dg >= 1u && og <= AZ_MAX_ORDER);
    assert(t >= a_block);
    /* the dense C peer only attempts a system at or under AZ_DENSE_MAX_TOTAL (a
     * wider one declines to the Python CRT path), so the ws_bound sizes to that
     * cap, never the full SRMECH_QMAT_MAX_DIM dense width. */
    if (t > AZ_DENSE_MAX_TOTAL) { t = AZ_DENSE_MAX_TOTAL; }
    return t;
}

size_t srmech_apagodu_zeilberger_ws_bound(size_t coeff_limbs, size_t order,
                                          size_t degree)
{
    size_t dg = (degree == 0u) ? 1u : degree;
    size_t omax = (order > AZ_MAX_ORDER) ? AZ_MAX_ORDER : order;
    size_t cap = az_cap_for(coeff_limbs, omax, dg);
    size_t hw = az_hdr_words();
    size_t jt = az_terms_for(omax, dg), kt = jt, nt = jt;
    assert(dg >= 1u && cap >= 2u);
    assert(hw >= 1u && jt >= 8u);
    size_t tripolys = 28u + 3u * (omax + 1u);
    size_t poly_hdr = ((sizeof(az_poly_t) + sizeof(uint32_t) - 1u) / sizeof(uint32_t));
    size_t bip_hdr = ((sizeof(az_bipoly_t) + sizeof(uint32_t) - 1u) / sizeof(uint32_t));
    size_t per_poly = poly_hdr + (2u * hw * nt + 2u * nt * cap);
    size_t per_bipoly = bip_hdr + kt * per_poly;
    size_t per_tripoly = jt * per_bipoly;
    size_t tripoly_words = per_tripoly * tripolys;
    size_t carriers = (size_t)cap * (size_t)AZ_N_CARRIERS;
    size_t scratch = (size_t)cap * 8u + 256u;
    size_t total = az_total_dim(omax, dg), n_rows, n_rows_c, ecap, qcl;
    size_t in_words, out_words, qws, vecwords;
    if (total > AZ_DENSE_MAX_TOTAL) { total = AZ_DENSE_MAX_TOTAL; }
    /* the (dn,dj,dk) monomial row span the assembly fills (degree-bounded), bounded
     * generously; the compacted nonzero-row count feeds the qmat. */
    n_rows = 6u * total + 64u;
    n_rows_c = 2u * total + 16u;
    if (n_rows_c > n_rows) { n_rows_c = n_rows; }
    qcl = coeff_limbs * (omax + 2u) + 4u;
    ecap = srmech_qmat_entry_cap(qcl, n_rows_c, total);
    in_words = 2u * n_rows * total * (hw + cap);
    out_words = 2u * n_rows_c * total * (hw + ecap)
                + (sizeof(size_t) / sizeof(uint32_t)) * total + 64u;
    qws = srmech_qmat_ws_bound(qcl, n_rows_c, total) / sizeof(uint32_t);
    vecwords = 2u * total * (hw + cap);
    {
        size_t best = tripoly_words + carriers + scratch + in_words + out_words
                      + qws + vecwords + 4096u;
        if (best < 8192u) { best = 8192u; }
        return best * sizeof(uint32_t);
    }
}

/* ---- the public entry --------------------------------------------- */

srmech_status_t srmech_apagodu_zeilberger(
        const srmech_bigint_t *rn_num_n, const srmech_bigint_t *rn_num_d,
        const size_t *rn_num_nlen, size_t rn_num_jdeg, size_t rn_num_kdeg,
        const srmech_bigint_t *rn_den_n, const srmech_bigint_t *rn_den_d,
        const size_t *rn_den_nlen, size_t rn_den_jdeg, size_t rn_den_kdeg,
        const srmech_bigint_t *rj_num_n, const srmech_bigint_t *rj_num_d,
        const size_t *rj_num_nlen, size_t rj_num_jdeg, size_t rj_num_kdeg,
        const srmech_bigint_t *rj_den_n, const srmech_bigint_t *rj_den_d,
        const size_t *rj_den_nlen, size_t rj_den_jdeg, size_t rj_den_kdeg,
        const srmech_bigint_t *rk_num_n, const srmech_bigint_t *rk_num_d,
        const size_t *rk_num_nlen, size_t rk_num_jdeg, size_t rk_num_kdeg,
        const srmech_bigint_t *rk_den_n, const srmech_bigint_t *rk_den_d,
        const size_t *rk_den_nlen, size_t rk_den_jdeg, size_t rk_den_kdeg,
        size_t max_order, size_t degree_hint,
        int *out_has, size_t *out_order,
        srmech_bigint_t *coeff_n, srmech_bigint_t *coeff_d, size_t *coeff_nlen,
        srmech_bigint_t *cert_j_n, srmech_bigint_t *cert_j_d, size_t *cert_j_nlen,
        size_t *out_cert_j_jdeg, size_t *out_cert_j_kdeg,
        srmech_bigint_t *cert_k_n, srmech_bigint_t *cert_k_d, size_t *cert_k_nlen,
        size_t *out_cert_k_jdeg, size_t *out_cert_k_kdeg,
        void *ws, size_t ws_len)
{
    az_ctx_t c;
    az_solve_t s;
    uint32_t cap;
    size_t cl, deg, og, jt, kt, nt, order, xjk_base, mark;
    srmech_status_t st;
    assert(out_has != NULL && out_order != NULL);
    assert(coeff_n != NULL && cert_j_n != NULL && cert_k_n != NULL);
    if (out_has == NULL || out_order == NULL || coeff_n == NULL
        || cert_j_n == NULL || cert_k_n == NULL || coeff_nlen == NULL
        || cert_j_nlen == NULL || cert_k_nlen == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    *out_has = 0;
    if (rn_den_jdeg == 0u || rj_den_jdeg == 0u || rk_den_jdeg == 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (max_order > AZ_MAX_ORDER) { max_order = AZ_MAX_ORDER; }
    deg = rn_num_kdeg;
    if (rn_den_kdeg > deg) { deg = rn_den_kdeg; }
    if (rj_num_kdeg > deg) { deg = rj_num_kdeg; }
    if (rk_den_kdeg > deg) { deg = rk_den_kdeg; }
    if (rn_num_jdeg > deg) { deg = rn_num_jdeg; }
    if (rn_den_jdeg > deg) { deg = rn_den_jdeg; }
    if (degree_hint > deg) { deg = degree_hint; }
    if (deg == 0u) { deg = 1u; }
    if (deg > AZ_MAX_DEG) { return SRMECH_ERR_BAD_INPUT; }
    og = max_order;
    cl = az_input_limbs(rn_num_n, az_count(rn_num_nlen, rn_num_jdeg * rn_num_kdeg));
    {
        size_t cl2 = az_input_limbs(rk_den_n,
                                    az_count(rk_den_nlen, rk_den_jdeg * rk_den_kdeg));
        if (cl2 > cl) { cl = cl2; }
    }
    cap = (uint32_t)az_cap_for(cl, og, deg);
    st = az_ctx_init(&c, cap, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    jt = az_terms_for(og, deg); kt = jt; nt = jt;
    st = az_solve_alloc(&c, &s, jt, kt, nt, og);
    if (st != SRMECH_OK) { return st; }
    st = az_load_tripoly(&c, &s.rn_n, rn_num_n, rn_num_d, rn_num_nlen,
                         rn_num_jdeg, rn_num_kdeg);
    if (st == SRMECH_OK) { st = az_load_tripoly(&c, &s.rn_d, rn_den_n, rn_den_d,
                                                rn_den_nlen, rn_den_jdeg, rn_den_kdeg); }
    if (st == SRMECH_OK) { st = az_load_tripoly(&c, &s.rj_n, rj_num_n, rj_num_d,
                                                rj_num_nlen, rj_num_jdeg, rj_num_kdeg); }
    if (st == SRMECH_OK) { st = az_load_tripoly(&c, &s.rj_d, rj_den_n, rj_den_d,
                                                rj_den_nlen, rj_den_jdeg, rj_den_kdeg); }
    if (st == SRMECH_OK) { st = az_load_tripoly(&c, &s.rk_n, rk_num_n, rk_num_d,
                                                rk_num_nlen, rk_num_jdeg, rk_num_kdeg); }
    if (st == SRMECH_OK) { st = az_load_tripoly(&c, &s.rk_d, rk_den_n, rk_den_d,
                                                rk_den_nlen, rk_den_jdeg, rk_den_kdeg); }
    if (st != SRMECH_OK) { return st; }
    mark = c.pool_cur;
    for (order = 0u; order <= og; order++) {
        size_t xjk;
        st = az_build_rhos(&c, &s, order);
        if (st != SRMECH_OK) { return st; }
        xjk_base = az_xjk_base(&s);
        /* sweep the certificate degree as the Python _try_order does: jk_deg =
         * jk_base + bump for bump = 0..AZ_MAX_CERT_BUMP, with the grid count xjk_cnt =
         * jk_deg + 1 (the (jk_deg+1)^3 cube of _jk_monomials). A config whose system
         * exceeds AZ_DENSE_MAX_TOTAL declines to the Python CRT path; the C never
         * returns a false "no recurrence" (the dispatch trusts only has=1). */
        for (xjk = xjk_base; xjk <= xjk_base + AZ_MAX_CERT_BUMP; xjk++) {
            int has = 0;
            size_t saved = c.pool_cur;
            st = az_try_config(&c, &s, order, xjk + 1u, &has,
                               coeff_n, coeff_d, coeff_nlen,
                               cert_j_n, cert_j_d, cert_j_nlen,
                               out_cert_j_jdeg, out_cert_j_kdeg,
                               cert_k_n, cert_k_d, cert_k_nlen,
                               out_cert_k_jdeg, out_cert_k_kdeg);
            if (st != SRMECH_OK) { return st; }
            if (has) { *out_has = 1; *out_order = order; return SRMECH_OK; }
            c.pool_cur = saved;                  /* reset the per-config qmat tail  */
        }
        c.pool_cur = mark;                       /* reset before the next order     */
    }
    return SRMECH_OK;
}
