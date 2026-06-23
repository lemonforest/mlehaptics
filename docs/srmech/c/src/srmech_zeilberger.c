/*
 * srmech_zeilberger.c -- Zeilberger's creative telescoping (the SECOND public op
 * of the section 76 "telescope" Sigma-row closed-form prover, F929). The C peer
 * of srmech.amsc.zeilberger.zeilberger.
 *
 * Input: a proper hypergeometric term F(n,k) given by its TWO term ratios
 *   r_n(n,k) = F(n+1,k)/F(n,k) = rn_num(n,k)/rn_den(n,k)
 *   r_k(n,k) = F(n,k+1)/F(n,k) = rk_num(n,k)/rk_den(n,k)
 * each an exact-rational BIVARIATE polynomial over Q[n,k] (a k-ascending list of
 * Poly-in-n coefficients; each Poly-in-n a parallel (num,den) bigint array).
 * Output: the minimal-order linear recurrence with polynomial coefficients
 *   Sum_{j=0}^{L} a_j(n) * f(n+j) = 0     (f(n) = Sum_k F(n,k))
 * as the order L + the coefficient polynomials a_j(n), plus the rational
 * certificate x(n,k) (R(n,k) = x/D_P). Byte-identical to the Python certificate at
 * ANY magnitude (full bignum coefficients; no int64/Q61 ceiling).
 *
 * The algorithm (Zeilberger 1990/1991; PWZ A=B ch. 6), exact over Q[n,k]:
 *   For L = 0, 1, ..., max_order:
 *     1. rho_j = prod_{i=0}^{j-1} r_n(n+i,k); P = Sum_j a_j(n) rho_j = N_P/D_P with
 *        D_P = prod_j rho_den_j (a common k-denominator). N_P is LINEAR in {a_j}.
 *     2. Gosper-in-k telescoping of T = F*P: find x(n,k) (the certificate
 *        numerator over D_P) with
 *          Sum_j a_j(n) rho_common_j * rk_d * D_P(k+1)
 *            = x(n,k+1) rk_n D_P(k) - x(n,k) rk_d D_P(k+1).
 *        Both sides are LINEAR in the unknowns {a_j(n) coeffs} U {x(n,k) coeffs};
 *        matching (n,k)-powers gives a HOMOGENEOUS exact-Q linear system.
 *     3. A kernel vector with a NONZERO a-block (read off the PUBLIC
 *        srmech_qmat_rref) gives the recurrence + certificate; the first such L is
 *        the minimal order. No a-nonzero kernel at any L <= max_order -> none.
 *
 * This file carries its own compact exact-Q BIVARIATE polynomial toolkit (a 2-D
 * grid of Q, n-degree x k-degree, over caller-arena srmech_bigint) and COMPOSES
 * the public srmech_qmat_rref for the kernel. No malloc (JPL Rule 3): every
 * working carrier + working bipoly + the qmat marshalling is carved from the
 * caller arena `ws`. Any residual overflow returns SRMECH_ERR_OVERFLOW (never a
 * wrap); the Python op then runs its ceiling-free pure-Q path -- so the
 * standalone-complete honor holds.
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

/* The largest ansatz order + per-direction degree the C orchestrator handles in a
 * sane caller arena. The C peer ACCELERATES the common low-order case (order 0-1
 * covers the canonical definite hypergeometric identities -- C(n,k) -> 2^n,
 * C(n,k)^2 -> C(2n,n), C(n,k) x^k -> (1+x)^n are all order 1); a higher-order
 * recurrence (or a system past the QMat dimension cap) falls to the complete
 * pure-Python path -- the C never returns a false "no recurrence", it just
 * declines to decide (the Python dispatch trusts only a has=1 C result). */
#define ZB_MAX_ORDER 1u
#define ZB_MAX_DEG   16u

/* ---- scalar exact-Q context (mirrors gosper's gos_ctx) ------------- */
typedef struct zb_ctx {
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
} zb_ctx_t;

#define ZB_N_CARRIERS 16u  /* qa,qb,sub (x2)=6, t0,t1,g,rem,rs0,rs1,z0,z1=8, +2 pad */

/* A Poly-in-n: a parallel (num,den) srmech_bigint array + a live length. */
typedef struct zb_poly {
    srmech_bigint_t *n;
    srmech_bigint_t *d;
    size_t           len;
    size_t           cap_terms;
} zb_poly_t;

/* A BiPoly(n,k): an array of (k_cap) Poly-in-n slots + a live k-length. */
typedef struct zb_bipoly {
    zb_poly_t *kc;          /* kc[dk] is the Poly-in-n coeff of k^dk          */
    size_t     klen;        /* live k-length (trimmed)                        */
    size_t     k_cap;       /* slot count                                     */
} zb_bipoly_t;

/* ---- forward declarations (Rule 1: no recursion) ------------------- */
static uint32_t *zb_take(uint32_t *base, size_t words, size_t *cur, size_t cnt);
static srmech_status_t zb_bind(srmech_bigint_t *b, uint32_t *base, size_t words,
                               size_t *cur, uint32_t cap);
static size_t zb_hdr_words(void);
static srmech_status_t zb_ctx_init(zb_ctx_t *c, uint32_t cap, void *ws,
                                   size_t ws_len);
static srmech_status_t zb_q_reduce(zb_ctx_t *c, srmech_bigint_t *num,
                                   srmech_bigint_t *den);
static srmech_status_t zb_q_add(zb_ctx_t *c, srmech_bigint_t *on,
                                srmech_bigint_t *od, const srmech_bigint_t *an,
                                const srmech_bigint_t *ad, const srmech_bigint_t *bn,
                                const srmech_bigint_t *bd, int sub);
static srmech_status_t zb_q_mul(zb_ctx_t *c, srmech_bigint_t *on,
                                srmech_bigint_t *od, const srmech_bigint_t *an,
                                const srmech_bigint_t *ad, const srmech_bigint_t *bn,
                                const srmech_bigint_t *bd);
static size_t zb_trim(const srmech_bigint_t *nums, size_t n);
static srmech_status_t zb_poly_alloc(zb_ctx_t *c, zb_poly_t *p, size_t terms);
static srmech_status_t zb_poly_zero(zb_poly_t *p);
static srmech_status_t zb_poly_copy(zb_ctx_t *c, zb_poly_t *dst,
                                    const zb_poly_t *src);
static srmech_status_t zb_poly_addsub(zb_ctx_t *c, zb_poly_t *out,
                                      const zb_poly_t *a, const zb_poly_t *b,
                                      int sub);
static srmech_status_t zb_poly_mul(zb_ctx_t *c, zb_poly_t *out,
                                   const zb_poly_t *a, const zb_poly_t *b);
static srmech_status_t zb_poly_shift_n(zb_ctx_t *c, zb_poly_t *out,
                                       const zb_poly_t *p, int64_t h);
static srmech_status_t zb_bipoly_alloc(zb_ctx_t *c, zb_bipoly_t *b, size_t k_terms,
                                       size_t n_terms);
static srmech_status_t zb_bipoly_zero(zb_bipoly_t *b);
static void zb_bipoly_trim(zb_bipoly_t *b);
static srmech_status_t zb_bipoly_copy(zb_ctx_t *c, zb_bipoly_t *dst,
                                      const zb_bipoly_t *src);
static srmech_status_t zb_bipoly_mul(zb_ctx_t *c, zb_bipoly_t *out,
                                     const zb_bipoly_t *a, const zb_bipoly_t *b,
                                     zb_poly_t *acc, zb_poly_t *prod);
static srmech_status_t zb_bipoly_shift_n(zb_ctx_t *c, zb_bipoly_t *out,
                                         const zb_bipoly_t *p, int64_t h);
static srmech_status_t zb_bipoly_shift_k(zb_ctx_t *c, zb_bipoly_t *out,
                                         const zb_bipoly_t *p,
                                         zb_bipoly_t *acc, zb_bipoly_t *tmp,
                                         zb_poly_t *pacc, zb_poly_t *pprod);

/* ---- caller-arena carve (mirror gosper) --------------------------- */

static uint32_t *zb_take(uint32_t *base, size_t words, size_t *cur, size_t cnt)
{
    uint32_t *p;
    assert(base != NULL && cur != NULL);
    assert(*cur <= words);
    if (cnt > words || *cur > words - cnt) { return NULL; }
    p = base + *cur;
    *cur += cnt;
    return p;
}

static srmech_status_t zb_bind(srmech_bigint_t *b, uint32_t *base, size_t words,
                               size_t *cur, uint32_t cap)
{
    uint32_t *limbs = zb_take(base, words, cur, cap);
    assert(b != NULL && cap > 0u);
    assert(base != NULL || words == 0u);
    if (limbs == NULL) { return SRMECH_ERR_OVERFLOW; }
    b->limbs = limbs;
    b->cap = cap;
    b->n = 0u;
    b->sign = 0;
    return SRMECH_OK;
}

static size_t zb_hdr_words(void)
{
    size_t hw = (sizeof(srmech_bigint_t) + sizeof(uint32_t) - 1u)
                / sizeof(uint32_t);
    assert(sizeof(srmech_bigint_t) > 0u);
    assert(hw >= 1u);
    return hw;
}

static srmech_status_t zb_ctx_init(zb_ctx_t *c, uint32_t cap, void *ws,
                                   size_t ws_len)
{
    uint32_t *base = (uint32_t *)ws;
    size_t words = ws_len / sizeof(uint32_t);
    size_t carrier_words = (size_t)cap * (size_t)ZB_N_CARRIERS;
    size_t scratch_words = (size_t)cap * 8u + 256u;
    srmech_status_t st = SRMECH_OK;
    assert(c != NULL);
    assert((uintptr_t)ws % sizeof(uint32_t) == 0u || ws == NULL);
    c->cap = cap;
    if (words < carrier_words + scratch_words) { return SRMECH_ERR_OVERFLOW; }
    c->pool = base;
    c->pool_words = words - scratch_words;
    c->pool_cur = 0u;
    st |= zb_bind(&c->qa_n, base, c->pool_words, &c->pool_cur, cap);
    st |= zb_bind(&c->qa_d, base, c->pool_words, &c->pool_cur, cap);
    st |= zb_bind(&c->qb_n, base, c->pool_words, &c->pool_cur, cap);
    st |= zb_bind(&c->qb_d, base, c->pool_words, &c->pool_cur, cap);
    st |= zb_bind(&c->sub_n, base, c->pool_words, &c->pool_cur, cap);
    st |= zb_bind(&c->sub_d, base, c->pool_words, &c->pool_cur, cap);
    st |= zb_bind(&c->t0, base, c->pool_words, &c->pool_cur, cap);
    st |= zb_bind(&c->t1, base, c->pool_words, &c->pool_cur, cap);
    st |= zb_bind(&c->g, base, c->pool_words, &c->pool_cur, cap);
    st |= zb_bind(&c->rem, base, c->pool_words, &c->pool_cur, cap);
    st |= zb_bind(&c->rs0, base, c->pool_words, &c->pool_cur, cap);
    st |= zb_bind(&c->rs1, base, c->pool_words, &c->pool_cur, cap);
    st |= zb_bind(&c->z0, base, c->pool_words, &c->pool_cur, cap);
    st |= zb_bind(&c->z1, base, c->pool_words, &c->pool_cur, cap);
    if (st != SRMECH_OK) { return SRMECH_ERR_OVERFLOW; }
    st = srmech_bigint_set_i64(&c->z0, 0);
    if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&c->z1, 1); }
    if (st != SRMECH_OK) { return st; }
    c->scratch = (void *)(base + (words - scratch_words));
    c->scratch_len = scratch_words * sizeof(uint32_t);
    assert(c->pool_cur <= c->pool_words);
    return SRMECH_OK;
}

/* ---- exact-Q scalar helpers (mirror gosper) ----------------------- */

static srmech_status_t zb_q_reduce(zb_ctx_t *c, srmech_bigint_t *num,
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

static srmech_status_t zb_q_add(zb_ctx_t *c, srmech_bigint_t *on,
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
    return zb_q_reduce(c, on, od);
}

static srmech_status_t zb_q_mul(zb_ctx_t *c, srmech_bigint_t *on,
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
    return zb_q_reduce(c, on, od);
}

/* ---- Poly-in-n carve + ops ---------------------------------------- */

static size_t zb_trim(const srmech_bigint_t *nums, size_t n)
{
    size_t k = n;
    assert(nums != NULL || n == 0u);
    while (k > 0u && srmech_bigint_is_zero(&nums[k - 1u])) { k--; }
    assert(k <= n);
    return k;
}

static srmech_status_t zb_poly_alloc(zb_ctx_t *c, zb_poly_t *p, size_t terms)
{
    size_t hw = zb_hdr_words(), k;
    uint32_t *hn, *hd;
    srmech_status_t st;
    assert(c != NULL && p != NULL && terms > 0u);
    assert(hw >= 1u);
    hn = zb_take(c->pool, c->pool_words, &c->pool_cur, hw * terms);
    hd = zb_take(c->pool, c->pool_words, &c->pool_cur, hw * terms);
    if (hn == NULL || hd == NULL) { return SRMECH_ERR_OVERFLOW; }
    p->n = (srmech_bigint_t *)(void *)hn;
    p->d = (srmech_bigint_t *)(void *)hd;
    p->len = 0u;
    p->cap_terms = terms;
    for (k = 0u; k < terms; k++) {
        st = zb_bind(&p->n[k], c->pool, c->pool_words, &c->pool_cur, c->cap);
        if (st == SRMECH_OK) { st = zb_bind(&p->d[k], c->pool, c->pool_words,
                                            &c->pool_cur, c->cap); }
        if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&p->n[k], 0); }
        if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&p->d[k], 1); }
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

static srmech_status_t zb_poly_zero(zb_poly_t *p)
{
    assert(p != NULL);
    assert(p->len <= p->cap_terms);
    p->len = 0u;
    return SRMECH_OK;
}

static srmech_status_t zb_poly_copy(zb_ctx_t *c, zb_poly_t *dst,
                                    const zb_poly_t *src)
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

static srmech_status_t zb_poly_addsub(zb_ctx_t *c, zb_poly_t *out,
                                      const zb_poly_t *a, const zb_poly_t *b,
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
        st = zb_q_add(c, &out->n[k], &out->d[k], an, ad, bn, bd, sub);
        if (st != SRMECH_OK) { return st; }
    }
    out->len = zb_trim(out->n, m);
    return SRMECH_OK;
}

static srmech_status_t zb_poly_mul(zb_ctx_t *c, zb_poly_t *out,
                                   const zb_poly_t *a, const zb_poly_t *b)
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
            st = zb_q_mul(c, &c->qa_n, &c->qa_d, &a->n[i], &a->d[i],
                          &b->n[j], &b->d[j]);
            if (st == SRMECH_OK) { st = srmech_bigint_copy(&c->qb_n, &out->n[i + j]); }
            if (st == SRMECH_OK) { st = srmech_bigint_copy(&c->qb_d, &out->d[i + j]); }
            if (st == SRMECH_OK) { st = zb_q_add(c, &out->n[i + j], &out->d[i + j],
                                                 &c->qb_n, &c->qb_d,
                                                 &c->qa_n, &c->qa_d, 0); }
            if (st != SRMECH_OK) { return st; }
        }
    }
    out->len = zb_trim(out->n, m);
    return SRMECH_OK;
}

/* One synthetic-Horner step for Poly-in-n shift: acc <- acc*(n+h) + coeff. */
static srmech_status_t zb_shift_step(zb_ctx_t *c, zb_poly_t *acc,
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
            st = zb_q_mul(c, &c->qa_n, &c->qa_d, &c->t1, &c->z1,
                          &acc->n[idx], &acc->d[idx]);     /* h*acc[idx] */
        } else {
            st = srmech_bigint_set_i64(&c->qa_n, 0);
            if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&c->qa_d, 1); }
        }
        if (st != SRMECH_OK) { return st; }
        if (idx > 0u) {
            st = zb_q_add(c, &acc->n[idx], &acc->d[idx], &c->qa_n, &c->qa_d,
                          &acc->n[idx - 1u], &acc->d[idx - 1u], 0);
        } else {
            st = zb_q_add(c, &acc->n[idx], &acc->d[idx], &c->qa_n, &c->qa_d,
                          cn, cd, 0);
        }
        if (st != SRMECH_OK) { return st; }
    }
    *deg = nd;
    return SRMECH_OK;
}

static srmech_status_t zb_poly_shift_n(zb_ctx_t *c, zb_poly_t *out,
                                       const zb_poly_t *p, int64_t h)
{
    size_t k, deg = 0u;
    srmech_status_t st;
    assert(c != NULL && out != NULL && p != NULL);
    if (p->len == 0u) { out->len = 0u; return SRMECH_OK; }
    assert(out->cap_terms >= p->len);
    if (h == 0) { return zb_poly_copy(c, out, p); }
    out->len = 0u;
    for (k = p->len; k > 0u; k--) {
        st = zb_shift_step(c, out, &p->n[k - 1u], &p->d[k - 1u], &deg, h);
        if (st != SRMECH_OK) { return st; }
    }
    out->len = zb_trim(out->n, deg);
    return SRMECH_OK;
}

/* ---- BiPoly carve + ops ------------------------------------------- */

static srmech_status_t zb_bipoly_alloc(zb_ctx_t *c, zb_bipoly_t *b, size_t k_terms,
                                       size_t n_terms)
{
    size_t hw = zb_hdr_words(), dk;
    uint32_t *hk;
    srmech_status_t st;
    assert(c != NULL && b != NULL && k_terms > 0u && n_terms > 0u);
    assert(hw >= 1u);
    hk = zb_take(c->pool, c->pool_words, &c->pool_cur,
                 ((sizeof(zb_poly_t) + sizeof(uint32_t) - 1u) / sizeof(uint32_t))
                 * k_terms);
    (void)hw;
    if (hk == NULL) { return SRMECH_ERR_OVERFLOW; }
    b->kc = (zb_poly_t *)(void *)hk;
    b->klen = 0u;
    b->k_cap = k_terms;
    for (dk = 0u; dk < k_terms; dk++) {
        st = zb_poly_alloc(c, &b->kc[dk], n_terms);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

static srmech_status_t zb_bipoly_zero(zb_bipoly_t *b)
{
    assert(b != NULL);
    assert(b->klen <= b->k_cap);
    b->klen = 0u;
    return SRMECH_OK;
}

static void zb_bipoly_trim(zb_bipoly_t *b)
{
    assert(b != NULL);
    assert(b->klen <= b->k_cap);
    while (b->klen > 0u && b->kc[b->klen - 1u].len == 0u) { b->klen--; }
}

static srmech_status_t zb_bipoly_copy(zb_ctx_t *c, zb_bipoly_t *dst,
                                      const zb_bipoly_t *src)
{
    size_t dk;
    srmech_status_t st;
    assert(c != NULL && dst != NULL && src != NULL);
    assert(dst->k_cap >= src->klen);
    for (dk = 0u; dk < src->klen; dk++) {
        st = zb_poly_copy(c, &dst->kc[dk], &src->kc[dk]);
        if (st != SRMECH_OK) { return st; }
    }
    dst->klen = src->klen;
    return SRMECH_OK;
}

/* out = a * b  (bipoly product). acc/prod are Poly-in-n scratch. */
static srmech_status_t zb_bipoly_mul(zb_ctx_t *c, zb_bipoly_t *out,
                                     const zb_bipoly_t *a, const zb_bipoly_t *b,
                                     zb_poly_t *acc, zb_poly_t *prod)
{
    size_t i, j, m, dk;
    srmech_status_t st;
    assert(c != NULL && out != NULL && a != NULL && b != NULL);
    assert(acc != NULL && prod != NULL);
    if (a->klen == 0u || b->klen == 0u) { out->klen = 0u; return SRMECH_OK; }
    m = a->klen + b->klen - 1u;
    assert(out->k_cap >= m);
    for (dk = 0u; dk < m; dk++) { (void)zb_poly_zero(&out->kc[dk]); }
    for (i = 0u; i < a->klen; i++) {
        if (a->kc[i].len == 0u) { continue; }
        for (j = 0u; j < b->klen; j++) {
            if (b->kc[j].len == 0u) { continue; }
            st = zb_poly_mul(c, prod, &a->kc[i], &b->kc[j]);
            if (st == SRMECH_OK) { st = zb_poly_copy(c, acc, &out->kc[i + j]); }
            if (st == SRMECH_OK) { st = zb_poly_addsub(c, &out->kc[i + j],
                                                       acc, prod, 0); }
            if (st != SRMECH_OK) { return st; }
        }
    }
    out->klen = m;
    zb_bipoly_trim(out);
    return SRMECH_OK;
}

/* out(n,k) = p(n+h, k): shift every k-coefficient Poly-in-n by +h. */
static srmech_status_t zb_bipoly_shift_n(zb_ctx_t *c, zb_bipoly_t *out,
                                         const zb_bipoly_t *p, int64_t h)
{
    size_t dk;
    srmech_status_t st;
    assert(c != NULL && out != NULL && p != NULL);
    assert(out->k_cap >= p->klen);
    for (dk = 0u; dk < p->klen; dk++) {
        st = zb_poly_shift_n(c, &out->kc[dk], &p->kc[dk], h);
        if (st != SRMECH_OK) { return st; }
    }
    out->klen = p->klen;
    zb_bipoly_trim(out);
    return SRMECH_OK;
}

/* out(n,k) = p(n, k+1): synthetic Horner over (k+1) in the k-variable. acc/tmp
 * are bipoly scratch (ping-pong; neither may alias `out` or `p`); pacc/pprod
 * Poly-in-n scratch. */
static srmech_status_t zb_bipoly_shift_k(zb_ctx_t *c, zb_bipoly_t *out,
                                         const zb_bipoly_t *p,
                                         zb_bipoly_t *acc, zb_bipoly_t *tmp,
                                         zb_poly_t *pacc, zb_poly_t *pprod)
{
    size_t i, dk;
    srmech_status_t st;
    assert(c != NULL && out != NULL && p != NULL);
    assert(acc != NULL && tmp != NULL && acc != tmp);
    (void)pprod;
    if (p->klen == 0u) { out->klen = 0u; return SRMECH_OK; }
    /* acc = 0; for c_i from high to low: tmp = acc*(k+1) + c_i; swap acc<->tmp.
     * tmp = acc*(k+1) is built by SHIFT-UP (tmp[dk]=acc[dk-1]) PLUS acc[dk]. */
    (void)zb_bipoly_zero(acc);
    for (i = p->klen; i > 0u; i--) {
        size_t alen = acc->klen, m = alen + 1u;
        assert(tmp->k_cap >= m);
        for (dk = 0u; dk < m; dk++) {
            const zb_poly_t *shifted = (dk >= 1u) ? &acc->kc[dk - 1u] : NULL;
            const zb_poly_t *same = (dk < alen) ? &acc->kc[dk] : NULL;
            if (shifted != NULL && same != NULL) {
                st = zb_poly_addsub(c, &tmp->kc[dk], shifted, same, 0);
            } else if (shifted != NULL) {
                st = zb_poly_copy(c, &tmp->kc[dk], shifted);
            } else if (same != NULL) {
                st = zb_poly_copy(c, &tmp->kc[dk], same);
            } else {
                st = zb_poly_zero(&tmp->kc[dk]);
            }
            if (st != SRMECH_OK) { return st; }
        }
        tmp->klen = m;
        /* tmp[0] += c_i (the new constant-in-k coefficient); via pacc to avoid the
         * out-aliases-operand case zb_q_add forbids. */
        st = zb_poly_addsub(c, pacc, &tmp->kc[0], &p->kc[i - 1u], 0);
        if (st == SRMECH_OK) { st = zb_poly_copy(c, &tmp->kc[0], pacc); }
        if (st != SRMECH_OK) { return st; }
        zb_bipoly_trim(tmp);
        st = zb_bipoly_copy(c, acc, tmp);             /* acc <- tmp (next round) */
        if (st != SRMECH_OK) { return st; }
    }
    return zb_bipoly_copy(c, out, acc);
}

/* ===================================================================
 * The orchestration: try L=0..max_order, build the homogeneous system, solve via
 * srmech_qmat_rref, read a nonzero-a-block kernel vector.
 * =================================================================== */

/* The working-bipoly roster (a fixed set + the per-order rho num/den pairs). */
typedef struct zb_solve {
    zb_bipoly_t rn_n, rn_d, rk_n, rk_d;        /* the four input ratios          */
    zb_bipoly_t den_p, dp_k1;                  /* D_P and D_P(k+1)               */
    zb_bipoly_t lhs_clear, xp_clear, xm_clear; /* the three clearing factors     */
    zb_bipoly_t b0, b1, b2;                    /* general scratch                */
    zb_bipoly_t sk_acc, sk_tmp;               /* shift_k scratch                 */
    zb_bipoly_t contrib, xmono;                /* per-column contribution / x mono */
    zb_bipoly_t *rho_n, *rho_d, *rho_common;   /* the order-indexed rho arrays    */
    zb_poly_t   pacc, pprod, pscr;            /* Poly-in-n scratch               */
    size_t      max_order;
    size_t      kt, nt;
} zb_solve_t;

static size_t zb_count(const size_t *klen, size_t kdeg)
{
    size_t k, total = 0u;
    assert(klen != NULL || kdeg == 0u);
    assert(kdeg <= (size_t)ZB_MAX_DEG + 2u);
    for (k = 0u; k < kdeg; k++) { total += klen[k]; }
    return total;
}

/* Load a flat (num,den) bigint pair stream + per-k lengths into a bipoly. */
static srmech_status_t zb_load_bipoly(zb_ctx_t *c, zb_bipoly_t *b,
                                      const srmech_bigint_t *cn,
                                      const srmech_bigint_t *cd,
                                      const size_t *klen, size_t kdeg)
{
    size_t dk, idx = 0u, j;
    srmech_status_t st;
    assert(c != NULL && b != NULL);
    assert(b->k_cap >= kdeg);
    (void)c;                                     /* copies use no ctx scratch      */
    for (dk = 0u; dk < kdeg; dk++) {
        size_t nlen = klen[dk];
        assert(b->kc[dk].cap_terms >= nlen);
        for (j = 0u; j < nlen; j++) {
            st = srmech_bigint_copy(&b->kc[dk].n[j], &cn[idx + j]);
            if (st == SRMECH_OK) { st = srmech_bigint_copy(&b->kc[dk].d[j],
                                                           &cd[idx + j]); }
            if (st != SRMECH_OK) { return st; }
        }
        b->kc[dk].len = zb_trim(b->kc[dk].n, nlen);
        idx += nlen;
    }
    b->klen = kdeg;
    zb_bipoly_trim(b);
    return SRMECH_OK;
}

static srmech_status_t zb_solve_alloc(zb_ctx_t *c, zb_solve_t *s, size_t kt,
                                      size_t nt, size_t order)
{
    size_t hdr = ((sizeof(zb_bipoly_t) + sizeof(uint32_t) - 1u) / sizeof(uint32_t));
    uint32_t *arr;
    size_t j;
    srmech_status_t st = SRMECH_OK;
    assert(c != NULL && s != NULL && kt > 0u && nt > 0u);
    assert(order <= ZB_MAX_ORDER);
    s->max_order = order; s->kt = kt; s->nt = nt;
    st |= zb_bipoly_alloc(c, &s->rn_n, kt, nt); st |= zb_bipoly_alloc(c, &s->rn_d, kt, nt);
    st |= zb_bipoly_alloc(c, &s->rk_n, kt, nt); st |= zb_bipoly_alloc(c, &s->rk_d, kt, nt);
    st |= zb_bipoly_alloc(c, &s->den_p, kt, nt); st |= zb_bipoly_alloc(c, &s->dp_k1, kt, nt);
    st |= zb_bipoly_alloc(c, &s->lhs_clear, kt, nt);
    st |= zb_bipoly_alloc(c, &s->xp_clear, kt, nt);
    st |= zb_bipoly_alloc(c, &s->xm_clear, kt, nt);
    st |= zb_bipoly_alloc(c, &s->b0, kt, nt); st |= zb_bipoly_alloc(c, &s->b1, kt, nt);
    st |= zb_bipoly_alloc(c, &s->b2, kt, nt);
    st |= zb_bipoly_alloc(c, &s->sk_acc, kt, nt); st |= zb_bipoly_alloc(c, &s->sk_tmp, kt, nt);
    st |= zb_bipoly_alloc(c, &s->contrib, kt, nt); st |= zb_bipoly_alloc(c, &s->xmono, kt, nt);
    st |= zb_poly_alloc(c, &s->pacc, nt); st |= zb_poly_alloc(c, &s->pprod, nt);
    st |= zb_poly_alloc(c, &s->pscr, nt);
    if (st != SRMECH_OK) { return SRMECH_ERR_OVERFLOW; }
    arr = zb_take(c->pool, c->pool_words, &c->pool_cur, hdr * (order + 1u) * 3u);
    if (arr == NULL) { return SRMECH_ERR_OVERFLOW; }
    s->rho_n = (zb_bipoly_t *)(void *)arr;
    s->rho_d = s->rho_n + (order + 1u);
    s->rho_common = s->rho_d + (order + 1u);
    for (j = 0u; j <= order; j++) {
        st = zb_bipoly_alloc(c, &s->rho_n[j], kt, nt);
        if (st == SRMECH_OK) { st = zb_bipoly_alloc(c, &s->rho_d[j], kt, nt); }
        if (st == SRMECH_OK) { st = zb_bipoly_alloc(c, &s->rho_common[j], kt, nt); }
        if (st != SRMECH_OK) { return SRMECH_ERR_OVERFLOW; }
    }
    return SRMECH_OK;
}

/* Max n-degree across a bipoly's k-coefficients (-1 -> 0 length convention). */
static size_t zb_bi_ndeg1(const zb_bipoly_t *b)
{
    size_t dk, d = 0u;
    assert(b != NULL);
    assert(b->klen <= b->k_cap);
    for (dk = 0u; dk < b->klen; dk++) {
        if (b->kc[dk].len > d) { d = b->kc[dk].len; }
    }
    return d;                                   /* a coefficient-COUNT (deg+1)    */
}

/* The n-degree bound (count) for a_j(n): max input n-count + order + 2. */
static size_t zb_ndeg_bound(const zb_solve_t *s, size_t order)
{
    size_t d = 2u, i;
    const zb_bipoly_t *ins[3];
    assert(s != NULL);
    assert(order <= s->max_order);
    ins[0] = &s->den_p; ins[1] = &s->rk_n; ins[2] = &s->rk_d;
    for (i = 0u; i < 3u; i++) {
        size_t nd = zb_bi_ndeg1(ins[i]);
        if (nd > d) { d = nd; }
    }
    for (i = 0u; i <= order; i++) {
        size_t nd = zb_bi_ndeg1(&s->rho_common[i]);
        if (nd > d) { d = nd; }
    }
    (void)order;
    return d + 1u;                               /* an n-coefficient COUNT (deg+2)  */
}

/* The certificate x degree bounds (k-count, n-count) -- mirror the Python tight
 * _ansatz_x_degree: k-count = max input k-count + 1, n-count = max input n-count
 * + 1. ndeg_cnt is unused here (kept for the Python signature parity). */
static void zb_xdeg_bound(const zb_solve_t *s, size_t order, size_t ndeg_cnt,
                          size_t *xk_cnt, size_t *xn_cnt)
{
    size_t kd = s->den_p.klen, i, nd = 2u;
    const zb_bipoly_t *ins[3];
    assert(s != NULL && xk_cnt != NULL && xn_cnt != NULL);
    assert(order <= s->max_order);
    (void)ndeg_cnt;
    for (i = 0u; i <= order; i++) {
        if (s->rho_common[i].klen > kd) { kd = s->rho_common[i].klen; }
    }
    if (s->rk_n.klen > kd) { kd = s->rk_n.klen; }
    if (s->rk_d.klen > kd) { kd = s->rk_d.klen; }
    ins[0] = &s->den_p; ins[1] = &s->rk_n; ins[2] = &s->rk_d;
    for (i = 0u; i < 3u; i++) {
        size_t v = zb_bi_ndeg1(ins[i]);
        if (v > nd) { nd = v; }
    }
    *xk_cnt = kd + 1u;                            /* k-coefficient COUNT             */
    *xn_cnt = nd + 1u;                            /* n-coefficient COUNT             */
}

/* === the matrix assembly (mirror _assemble_rows) ===
 * Build the homogeneous system into the caller-marshalled a_n/a_d (row-major,
 * total wide). Rows are (n_deg_used, k_deg_used) monomials; columns are the
 * a_j(n) coeffs (a_block) then the x(n,k) coeffs. Returns the live n_rows in
 * *out_rows. The marshalling region is carved by zb_qsolve below.
 */

/* Accumulate +/- a bipoly contrib into the dense system at column `col`. The
 * system is indexed (dn, dk) -> row r = dk*nrow_n + dn, with nrow_n/nrow_k the
 * per-direction row spans. */
static srmech_status_t zb_acc_contrib(zb_ctx_t *c, const zb_bipoly_t *contrib,
                                      srmech_bigint_t *a_n, srmech_bigint_t *a_d,
                                      size_t col, int sign, size_t total,
                                      size_t nrow_n, size_t nrow_k)
{
    size_t dk, dn;
    srmech_status_t st;
    assert(c != NULL && contrib != NULL && a_n != NULL);
    assert(nrow_n > 0u && nrow_k > 0u);
    for (dk = 0u; dk < contrib->klen; dk++) {
        const zb_poly_t *kp = &contrib->kc[dk];
        if (dk >= nrow_k) { return SRMECH_ERR_OVERFLOW; }
        for (dn = 0u; dn < kp->len; dn++) {
            size_t row, idx;
            if (srmech_bigint_is_zero(&kp->n[dn])) { continue; }
            if (dn >= nrow_n) { return SRMECH_ERR_OVERFLOW; }
            row = dk * nrow_n + dn;
            idx = row * total + col;
            /* accumulate into a TEMP first (zb_q_add forbids out aliasing its a/b
             * operand denominators), then copy back into the cell. */
            st = zb_q_add(c, &c->sub_n, &c->sub_d, &a_n[idx], &a_d[idx],
                          &kp->n[dn], &kp->d[dn], (sign > 0) ? 0 : 1);
            if (st == SRMECH_OK) { st = srmech_bigint_copy(&a_n[idx], &c->sub_n); }
            if (st == SRMECH_OK) { st = srmech_bigint_copy(&a_d[idx], &c->sub_d); }
            if (st != SRMECH_OK) { return st; }
        }
    }
    return SRMECH_OK;
}

/* Set bipoly `out` to the single monomial n^dn * k^dk. */
static srmech_status_t zb_set_monomial(zb_ctx_t *c, zb_bipoly_t *out,
                                       size_t dn, size_t dk)
{
    size_t i;
    srmech_status_t st;
    assert(c != NULL && out != NULL);
    assert(out->k_cap > dk && out->kc[dk].cap_terms > dn);
    (void)c;                                     /* sets literals, no ctx scratch  */
    for (i = 0u; i <= dk; i++) { (void)zb_poly_zero(&out->kc[i]); }
    for (i = 0u; i <= dn; i++) {
        st = srmech_bigint_set_i64(&out->kc[dk].n[i], (i == dn) ? 1 : 0);
        if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&out->kc[dk].d[i], 1); }
        if (st != SRMECH_OK) { return st; }
    }
    out->kc[dk].len = dn + 1u;
    out->klen = dk + 1u;
    return SRMECH_OK;
}

/* Scale every k-coefficient of `in` by the monomial n^dn -> out. */
static srmech_status_t zb_scale_nmono(zb_ctx_t *c, zb_bipoly_t *out,
                                      const zb_bipoly_t *in, size_t dn,
                                      zb_poly_t *mono)
{
    size_t dk, i;
    srmech_status_t st;
    assert(c != NULL && out != NULL && in != NULL && mono != NULL);
    assert(mono->cap_terms > dn);
    for (i = 0u; i <= dn; i++) {
        st = srmech_bigint_set_i64(&mono->n[i], (i == dn) ? 1 : 0);
        if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&mono->d[i], 1); }
        if (st != SRMECH_OK) { return st; }
    }
    mono->len = dn + 1u;
    for (dk = 0u; dk < in->klen; dk++) {
        st = zb_poly_mul(c, &out->kc[dk], &in->kc[dk], mono);
        if (st != SRMECH_OK) { return st; }
    }
    out->klen = in->klen;
    zb_bipoly_trim(out);
    return SRMECH_OK;
}

/* Build rho_common[j], den_p, dp_k1, and the three clearing factors for the given
 * order (rho_common[j] = rho_n[j] * D_P / rho_d[j], over the common D_P). */
static srmech_status_t zb_build_rhos(zb_ctx_t *c, zb_solve_t *s, size_t order)
{
    size_t j;
    srmech_status_t st;
    assert(c != NULL && s != NULL && order <= s->max_order);
    assert(s->rho_n != NULL);
    /* rho_n[0]=1, rho_d[0]=1; rho_j = rho_{j-1} * r_n(n+(j-1),k). */
    st = srmech_bigint_set_i64(&s->rho_n[0].kc[0].n[0], 1);
    if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&s->rho_n[0].kc[0].d[0], 1); }
    if (st != SRMECH_OK) { return st; }
    s->rho_n[0].kc[0].len = 1u; s->rho_n[0].klen = 1u;
    st = srmech_bigint_set_i64(&s->rho_d[0].kc[0].n[0], 1);
    if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&s->rho_d[0].kc[0].d[0], 1); }
    if (st != SRMECH_OK) { return st; }
    s->rho_d[0].kc[0].len = 1u; s->rho_d[0].klen = 1u;
    for (j = 1u; j <= order; j++) {
        st = zb_bipoly_shift_n(c, &s->b0, &s->rn_n, (int64_t)(j - 1u));
        if (st == SRMECH_OK) { st = zb_bipoly_mul(c, &s->rho_n[j], &s->rho_n[j - 1u],
                                                  &s->b0, &s->pacc, &s->pprod); }
        if (st == SRMECH_OK) { st = zb_bipoly_shift_n(c, &s->b1, &s->rn_d,
                                                      (int64_t)(j - 1u)); }
        if (st == SRMECH_OK) { st = zb_bipoly_mul(c, &s->rho_d[j], &s->rho_d[j - 1u],
                                                  &s->b1, &s->pacc, &s->pprod); }
        if (st != SRMECH_OK) { return st; }
    }
    /* D_P = product of rho_d[j]. */
    st = zb_bipoly_copy(c, &s->den_p, &s->rho_d[0]);
    for (j = 1u; st == SRMECH_OK && j <= order; j++) {
        st = zb_bipoly_mul(c, &s->b0, &s->den_p, &s->rho_d[j], &s->pacc, &s->pprod);
        if (st == SRMECH_OK) { st = zb_bipoly_copy(c, &s->den_p, &s->b0); }
    }
    if (st != SRMECH_OK) { return st; }
    /* rho_common[j] = rho_n[j] * (D_P / rho_d[j]) = rho_n[j] * prod_{i!=j} rho_d[i]. */
    for (j = 0u; j <= order; j++) {
        size_t i;
        st = zb_bipoly_copy(c, &s->b2, &s->rho_n[j]);     /* b2 = rho_n[j]          */
        for (i = 0u; st == SRMECH_OK && i <= order; i++) {
            if (i == j) { continue; }
            st = zb_bipoly_mul(c, &s->b0, &s->b2, &s->rho_d[i], &s->pacc, &s->pprod);
            if (st == SRMECH_OK) { st = zb_bipoly_copy(c, &s->b2, &s->b0); }
        }
        if (st == SRMECH_OK) { st = zb_bipoly_copy(c, &s->rho_common[j], &s->b2); }
        if (st != SRMECH_OK) { return st; }
    }
    /* dp_k1 = D_P(k+1); clearing factors. */
    st = zb_bipoly_shift_k(c, &s->dp_k1, &s->den_p, &s->sk_acc, &s->sk_tmp,
                           &s->pacc, &s->pprod);
    if (st == SRMECH_OK) { st = zb_bipoly_mul(c, &s->lhs_clear, &s->rk_d, &s->dp_k1,
                                              &s->pacc, &s->pprod); }
    if (st == SRMECH_OK) { st = zb_bipoly_mul(c, &s->xp_clear, &s->rk_n, &s->den_p,
                                              &s->pacc, &s->pprod); }
    if (st == SRMECH_OK) { st = zb_bipoly_copy(c, &s->xm_clear, &s->lhs_clear); }
    return st;
}

/* Fill the homogeneous matrix a_n/a_d (n_rows x total, row-major) for the given
 * order + degree bounds + column layout. Zeroes it first. */
static srmech_status_t zb_fill_matrix(zb_ctx_t *c, zb_solve_t *s, size_t order,
                                      size_t ndeg_cnt, size_t xk_cnt, size_t xn_cnt,
                                      srmech_bigint_t *a_n, srmech_bigint_t *a_d,
                                      size_t n_rows, size_t total, size_t a_block,
                                      size_t nrow_n, size_t nrow_k)
{
    size_t j, p, dk, dn, i, col;
    srmech_status_t st;
    assert(c != NULL && s != NULL && a_n != NULL);
    assert(a_d != NULL && total > 0u);
    for (i = 0u; i < n_rows * total; i++) {
        st = srmech_bigint_set_i64(&a_n[i], 0);
        if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&a_d[i], 1); }
        if (st != SRMECH_OK) { return st; }
    }
    /* a_j columns: contrib = rho_common[j] * lhs_clear, scaled by n^p. */
    for (j = 0u; j <= order; j++) {
        st = zb_bipoly_mul(c, &s->b0, &s->rho_common[j], &s->lhs_clear,
                           &s->pacc, &s->pprod);            /* base = rho_c[j]*lhs */
        if (st != SRMECH_OK) { return st; }
        for (p = 0u; p < ndeg_cnt; p++) {
            col = j * ndeg_cnt + p;
            st = zb_scale_nmono(c, &s->contrib, &s->b0, p, &s->pscr);
            if (st == SRMECH_OK) { st = zb_acc_contrib(c, &s->contrib, a_n, a_d,
                                                       col, +1, total, nrow_n, nrow_k); }
            if (st != SRMECH_OK) { return st; }
        }
    }
    /* x columns: x = n^dn * k^dk. xp = x(k+1)*xp_clear (sign -); xm = x*xm_clear (+). */
    for (dk = 0u; dk < xk_cnt; dk++) {
        for (dn = 0u; dn < xn_cnt; dn++) {
            col = a_block + dk * xn_cnt + dn;
            st = zb_set_monomial(c, &s->xmono, dn, dk);
            if (st == SRMECH_OK) { st = zb_bipoly_shift_k(c, &s->b1, &s->xmono,
                                                          &s->sk_acc, &s->sk_tmp,
                                                          &s->pacc, &s->pprod); }
            if (st == SRMECH_OK) { st = zb_bipoly_mul(c, &s->b2, &s->b1, &s->xp_clear,
                                                      &s->pacc, &s->pprod); }
            if (st == SRMECH_OK) { st = zb_acc_contrib(c, &s->b2, a_n, a_d, col, -1,
                                                       total, nrow_n, nrow_k); }
            if (st == SRMECH_OK) { st = zb_bipoly_mul(c, &s->b2, &s->xmono, &s->xm_clear,
                                                      &s->pacc, &s->pprod); }
            if (st == SRMECH_OK) { st = zb_acc_contrib(c, &s->b2, a_n, a_d, col, +1,
                                                       total, nrow_n, nrow_k); }
            if (st != SRMECH_OK) { return st; }
        }
    }
    return SRMECH_OK;
}

/* The qmat-solve scratch carved from the ctx pool tail. */
typedef struct zb_qarena {
    srmech_bigint_t *a_n, *a_d;    /* the small-cap assembly/input matrix (full)    */
    srmech_bigint_t *o_n, *o_d;    /* the ecap RREF output (compacted-row count)     */
    size_t          *piv;
    void            *qws;
    size_t           qws_words;
} zb_qarena_t;

/* Carve the small-cap INPUT/assembly matrix (nrow_full * total entries of cap
 * limbs -- assembly entries stay small) + zero it. */
static srmech_status_t zb_qcarve_in(zb_ctx_t *c, zb_qarena_t *q, size_t nrow_full,
                                    size_t total)
{
    size_t hw = zb_hdr_words(), cells = nrow_full * total, i;
    uint32_t *hn, *hd;
    srmech_status_t st;
    assert(c != NULL && q != NULL && nrow_full > 0u && total > 0u);
    assert(cells == nrow_full * total && hw >= 1u);
    hn = zb_take(c->pool, c->pool_words, &c->pool_cur, hw * cells);
    hd = zb_take(c->pool, c->pool_words, &c->pool_cur, hw * cells);
    if (hn == NULL || hd == NULL) { return SRMECH_ERR_OVERFLOW; }
    q->a_n = (srmech_bigint_t *)(void *)hn; q->a_d = (srmech_bigint_t *)(void *)hd;
    for (i = 0u; i < cells; i++) {
        st = zb_bind(&q->a_n[i], c->pool, c->pool_words, &c->pool_cur, c->cap);
        if (st == SRMECH_OK) { st = zb_bind(&q->a_d[i], c->pool, c->pool_words,
                                            &c->pool_cur, c->cap); }
        if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&q->a_n[i], 0); }
        if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&q->a_d[i], 1); }
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* Carve the ecap RREF OUTPUT (n_rows_c * total entries of ecap limbs) + the pivot
 * array + the qmat ws, sized from the COMPACTED row count + the assembled-entry
 * limb count `qcl` (the qmat reads `qcl`-limb input entries). */
static srmech_status_t zb_qcarve_out(zb_ctx_t *c, zb_qarena_t *q, size_t n_rows_c,
                                     size_t total, size_t ecap, size_t qcl)
{
    size_t hw = zb_hdr_words(), cells = n_rows_c * total, i;
    uint32_t *on, *od;
    srmech_status_t st;
    assert(c != NULL && q != NULL && n_rows_c > 0u && total > 0u);
    assert(ecap >= 2u && qcl >= 1u);
    on = zb_take(c->pool, c->pool_words, &c->pool_cur, hw * cells);
    od = zb_take(c->pool, c->pool_words, &c->pool_cur, hw * cells);
    q->piv = (size_t *)(void *)zb_take(c->pool, c->pool_words, &c->pool_cur,
                  (sizeof(size_t) / sizeof(uint32_t)) * total + 2u);
    if (on == NULL || od == NULL || q->piv == NULL) { return SRMECH_ERR_OVERFLOW; }
    q->o_n = (srmech_bigint_t *)(void *)on; q->o_d = (srmech_bigint_t *)(void *)od;
    for (i = 0u; i < cells; i++) {
        st = zb_bind(&q->o_n[i], c->pool, c->pool_words, &c->pool_cur, (uint32_t)ecap);
        if (st == SRMECH_OK) { st = zb_bind(&q->o_d[i], c->pool, c->pool_words,
                                            &c->pool_cur, (uint32_t)ecap); }
        if (st != SRMECH_OK) { return st; }
    }
    q->qws_words = srmech_qmat_ws_bound(qcl, n_rows_c, total) / sizeof(uint32_t);
    q->qws = (void *)zb_take(c->pool, c->pool_words, &c->pool_cur, q->qws_words);
    if (q->qws == NULL) { return SRMECH_ERR_OVERFLOW; }
    return SRMECH_OK;
}

/* Compact the small-cap assembly matrix in place: copy every row that has a
 * nonzero entry down to the next free compacted slot, returning the compacted row
 * count. Rows are total wide. */
static srmech_status_t zb_compact_rows(zb_qarena_t *q, size_t nrow_full,
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

/* Read a kernel vector with a NONZERO a-block from the RREF output into x_out[]
 * (n_unknowns Q pairs in c->scratch? no -- into caller-provided dual arrays).
 * Returns *found=1 + writes the kernel into vec_n/vec_d when an a-nonzero kernel
 * exists, else *found=0. Mirrors the Python _homogeneous_kernel free-column scan. */
static srmech_status_t zb_read_kernel(zb_ctx_t *c, const zb_qarena_t *q,
                                      size_t n_rows, size_t total, size_t rank,
                                      size_t n_unknowns, size_t a_block,
                                      srmech_bigint_t *vec_n, srmech_bigint_t *vec_d,
                                      int *found)
{
    size_t r, j, f, pc;
    srmech_status_t st;
    assert(c != NULL && q != NULL && vec_n != NULL && found != NULL);
    assert(total == n_unknowns);
    (void)c;                                     /* reads RREF out, sets vec only  */
    *found = 0;
    (void)rank;
    /* scan free columns low->high; for each, set it = 1, back-substitute pivots. */
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
            /* vec[pc] = -(row[f] * vec[f]) = -row[f] since vec[f]=1, others 0 (only
             * the single free f is set). row pivot value is 1 in RREF. */
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

/* Find the live (trailing-zero-trimmed) length of vec[base..base+span). */
static size_t zb_live_len(const srmech_bigint_t *vec_n, size_t base, size_t span)
{
    size_t p, live = 0u;
    assert(vec_n != NULL);
    assert(base + span >= base);
    for (p = 0u; p < span; p++) {
        if (!srmech_bigint_is_zero(&vec_n[base + p])) { live = p + 1u; }
    }
    return live;
}

/* Write the kernel vector's a-block into the caller coeff arrays CONTIGUOUSLY
 * (a_0's live coeffs, then a_1's, ...; coeff_nlen[j] is each segment length so the
 * caller walks them sequentially), and the x-block into the certificate arrays
 * CONTIGUOUSLY (k-slot dk's live n-coeffs, then dk+1's; cert_klen[dk] the length).
 * Both are PACKED -- no fixed stride the caller must know. */
static srmech_status_t zb_write_out(const srmech_bigint_t *vec_n,
                                    const srmech_bigint_t *vec_d, size_t order,
                                    size_t ndeg_cnt, size_t a_block, size_t xk_cnt,
                                    size_t xn_cnt, srmech_bigint_t *coeff_n,
                                    srmech_bigint_t *coeff_d, size_t *coeff_nlen,
                                    srmech_bigint_t *cert_n, srmech_bigint_t *cert_d,
                                    size_t *cert_klen, size_t *out_cert_kdeg)
{
    size_t j, p, dk, dn, w = 0u, live_k = 0u;
    srmech_status_t st;
    assert(vec_n != NULL && coeff_n != NULL && cert_n != NULL);
    assert(coeff_d != NULL && cert_d != NULL);
    for (j = 0u; j <= order; j++) {
        size_t live = zb_live_len(vec_n, j * ndeg_cnt, ndeg_cnt);
        for (p = 0u; p < live; p++) {
            st = srmech_bigint_copy(&coeff_n[w], &vec_n[j * ndeg_cnt + p]);
            if (st == SRMECH_OK) { st = srmech_bigint_copy(&coeff_d[w],
                                                           &vec_d[j * ndeg_cnt + p]); }
            if (st != SRMECH_OK) { return st; }
            w++;
        }
        coeff_nlen[j] = live;
    }
    w = 0u;
    for (dk = 0u; dk < xk_cnt; dk++) {
        size_t live = zb_live_len(vec_n, a_block + dk * xn_cnt, xn_cnt);
        for (dn = 0u; dn < live; dn++) {
            st = srmech_bigint_copy(&cert_n[w], &vec_n[a_block + dk * xn_cnt + dn]);
            if (st == SRMECH_OK) { st = srmech_bigint_copy(&cert_d[w],
                                            &vec_d[a_block + dk * xn_cnt + dn]); }
            if (st != SRMECH_OK) { return st; }
            w++;
        }
        cert_klen[dk] = live;
        if (live > 0u) { live_k = dk + 1u; }
    }
    *out_cert_kdeg = (live_k == 0u) ? 1u : live_k;
    return SRMECH_OK;
}

/* Carve the RREF output + kernel-vector storage, RREF the compacted system, and
 * read an a-nonzero kernel vector into the caller vec arrays. Sets *found. */
static srmech_status_t zb_solve_kernel(zb_ctx_t *c, zb_qarena_t *q, size_t n_rows_c,
                                       size_t total, size_t ecap, size_t qcl,
                                       size_t n_unknowns, size_t a_block,
                                       srmech_bigint_t **vec_n,
                                       srmech_bigint_t **vec_d, int *found)
{
    size_t hw = zb_hdr_words(), i, rank = 0u;
    uint32_t *vh_n, *vh_d;
    srmech_status_t st;
    assert(c != NULL && q != NULL && found != NULL);
    assert(vec_n != NULL && vec_d != NULL && n_unknowns > 0u);
    st = zb_qcarve_out(c, q, n_rows_c, total, ecap, qcl);
    if (st != SRMECH_OK) { return st; }
    vh_n = zb_take(c->pool, c->pool_words, &c->pool_cur, hw * n_unknowns);
    vh_d = zb_take(c->pool, c->pool_words, &c->pool_cur, hw * n_unknowns);
    if (vh_n == NULL || vh_d == NULL) { return SRMECH_ERR_OVERFLOW; }
    *vec_n = (srmech_bigint_t *)(void *)vh_n;
    *vec_d = (srmech_bigint_t *)(void *)vh_d;
    for (i = 0u; i < n_unknowns; i++) {
        st = zb_bind(&(*vec_n)[i], c->pool, c->pool_words, &c->pool_cur, c->cap);
        if (st == SRMECH_OK) { st = zb_bind(&(*vec_d)[i], c->pool, c->pool_words,
                                            &c->pool_cur, c->cap); }
        if (st != SRMECH_OK) { return st; }
    }
    st = srmech_qmat_rref(q->a_n, q->a_d, n_rows_c, total, q->o_n, q->o_d, &rank,
                          q->piv, q->qws, q->qws_words * sizeof(uint32_t));
    if (st != SRMECH_OK) { return st; }
    return zb_read_kernel(c, q, n_rows_c, total, rank, n_unknowns, a_block,
                          *vec_n, *vec_d, found);
}

/* Attempt one order: build rhos, bounds, matrix; rref; read kernel; on a found
 * a-nonzero kernel write the output and set *out_has. Carves the qmat region from
 * a SAVED pool mark (restored by the caller between orders). */
static srmech_status_t zb_try_order(zb_ctx_t *c, zb_solve_t *s, size_t order,
                                    int *out_has, srmech_bigint_t *coeff_n,
                                    srmech_bigint_t *coeff_d, size_t *coeff_nlen,
                                    srmech_bigint_t *cert_n, srmech_bigint_t *cert_d,
                                    size_t *cert_klen, size_t *out_cert_kdeg)
{
    size_t ndeg_cnt, xk_cnt, xn_cnt, n_a, a_block, x_block, n_unknowns;
    size_t nrow_n, nrow_k, n_rows, n_rows_c = 0u, total, ecap, qcl = 1u, i;
    zb_qarena_t q;
    srmech_bigint_t *vec_n = NULL, *vec_d = NULL;
    int found = 0;
    srmech_status_t st;
    assert(c != NULL && s != NULL && out_has != NULL);
    assert(coeff_n != NULL && cert_n != NULL);
    *out_has = 0;
    st = zb_build_rhos(c, s, order);
    if (st != SRMECH_OK) { return st; }
    ndeg_cnt = zb_ndeg_bound(s, order);
    zb_xdeg_bound(s, order, ndeg_cnt, &xk_cnt, &xn_cnt);
    n_a = order + 1u;
    a_block = n_a * ndeg_cnt;
    x_block = xk_cnt * xn_cnt;
    n_unknowns = a_block + x_block;
    total = n_unknowns;
    /* the FULL row span: monomials (dn, dk). compacted to nonzero rows before rref. */
    nrow_n = ndeg_cnt + xn_cnt + 4u;
    nrow_k = xk_cnt + s->den_p.klen + 4u;
    n_rows = nrow_n * nrow_k;
    if (total > SRMECH_QMAT_MAX_DIM) { return SRMECH_ERR_BAD_INPUT; }
    /* assemble into the small-cap input matrix, then compact the nonzero rows. */
    st = zb_qcarve_in(c, &q, n_rows, total);
    if (st != SRMECH_OK) { return st; }
    st = zb_fill_matrix(c, s, order, ndeg_cnt, xk_cnt, xn_cnt, q.a_n, q.a_d,
                        n_rows, total, a_block, nrow_n, nrow_k);
    if (st != SRMECH_OK) { return st; }
    st = zb_compact_rows(&q, n_rows, total, &n_rows_c);
    if (st != SRMECH_OK) { return st; }
    if (n_rows_c == 0u) { return SRMECH_OK; }            /* the all-zero system     */
    /* the assembled-entry limb count drives the RREF output cap (small for the
     * common integer inputs; a genuinely huge entry -> OVERFLOW -> pure path). */
    for (i = 0u; i < n_rows_c * total; i++) {
        if (q.a_n[i].n > qcl) { qcl = q.a_n[i].n; }
        if (q.a_d[i].n > qcl) { qcl = q.a_d[i].n; }
    }
    ecap = srmech_qmat_entry_cap(qcl, n_rows_c, total);
    st = zb_solve_kernel(c, &q, n_rows_c, total, ecap, qcl, n_unknowns, a_block,
                         &vec_n, &vec_d, &found);
    if (st != SRMECH_OK) { return st; }
    if (!found) { return SRMECH_OK; }
    st = zb_write_out(vec_n, vec_d, order, ndeg_cnt, a_block, xk_cnt, xn_cnt,
                      coeff_n, coeff_d, coeff_nlen, cert_n, cert_d, cert_klen,
                      out_cert_kdeg);
    if (st != SRMECH_OK) { return st; }
    *out_has = 1;
    return SRMECH_OK;
}

/* The orchestrating run: try orders 0..max_order; the first a-nonzero kernel is
 * the minimal recurrence. Restores the pool mark between orders. */
static srmech_status_t zb_run(zb_ctx_t *c, zb_solve_t *s, size_t max_order,
                              int *out_has, size_t *out_order,
                              srmech_bigint_t *coeff_n, srmech_bigint_t *coeff_d,
                              size_t *coeff_nlen, srmech_bigint_t *cert_n,
                              srmech_bigint_t *cert_d, size_t *cert_klen,
                              size_t *out_cert_kdeg)
{
    size_t order, mark = c->pool_cur;
    srmech_status_t st;
    assert(c != NULL && s != NULL && out_has != NULL && out_order != NULL);
    assert(coeff_n != NULL && cert_n != NULL);
    *out_has = 0;
    for (order = 0u; order <= max_order; order++) {
        int has = 0;
        c->pool_cur = mark;                              /* reset the bump tail    */
        st = zb_try_order(c, s, order, &has, coeff_n, coeff_d, coeff_nlen,
                          cert_n, cert_d, cert_klen, out_cert_kdeg);
        if (st != SRMECH_OK) { return st; }
        if (has) { *out_has = 1; *out_order = order; return SRMECH_OK; }
    }
    return SRMECH_OK;
}

/* ---- input limb estimate + arena bounds --------------------------- */

static size_t zb_input_limbs(const srmech_bigint_t *cn, size_t total)
{
    size_t k, cl = 1u;
    assert(cn != NULL || total == 0u);
    assert(cl >= 1u);
    for (k = 0u; k < total; k++) { if (cn[k].n > cl) { cl = cn[k].n; } }
    return cl;
}

static size_t zb_cap_for(size_t coeff_limbs, size_t order, size_t degree)
{
    size_t cl = (coeff_limbs == 0u) ? 1u : coeff_limbs;
    size_t dg = (degree == 0u) ? 1u : degree;
    size_t og = (order > ZB_MAX_ORDER) ? ZB_MAX_ORDER : order;
    /* The bivariate products accumulate Q over an order-scaled, degree-scaled
     * chain; an envelope dominating the worst intermediate for the COMMON
     * (small-coefficient, low-order) inputs. A genuinely huge input that exceeds
     * this returns OVERFLOW -> the Python pure-Q path (the standalone-honor). */
    size_t step = cl * (dg + 2u) * (og + 2u) + 8u;
    size_t cap = step * 2u + cl * 4u + 48u;
    assert(cap >= step);
    assert(cap >= cl);
    return cap;
}

size_t srmech_zeilberger_out_cap(size_t coeff_limbs, size_t order, size_t degree)
{
    size_t cap = zb_cap_for(coeff_limbs, order, degree);
    assert(cap >= 2u);
    assert(cap >= coeff_limbs);
    return cap;
}

/* per-direction term counts the working bipolys carry. The heaviest intermediate
 * is D_P (k- and n-degree ~ order*degree) and the clearing-factor products (one
 * more order-fold of the inputs), plus the shift-up headroom -- bound generously
 * at ~2*(order+1)*degree to keep every product/shift in-slot. */
static size_t zb_kterms_for(size_t order, size_t degree)
{
    size_t dg = (degree == 0u) ? 1u : degree;
    size_t terms = 2u * (order + 1u) * dg + dg + 8u;
    assert(terms >= dg);
    assert(terms >= 8u);
    return terms;
}

static size_t zb_nterms_for(size_t order, size_t degree)
{
    size_t dg = (degree == 0u) ? 1u : degree;
    size_t terms = 2u * (order + 1u) * dg + dg + 8u;
    assert(terms >= dg);
    assert(terms >= 8u);
    return terms;
}

/* The realistic max matrix dimensions (n_rows, total) the order-`order` system
 * reaches at this degree -- the degree-based bounds (NOT the slot caps), each
 * clamped at SRMECH_QMAT_MAX_DIM (a larger one returns BAD_INPUT -> pure path). */
static void zb_matrix_dims(size_t order, size_t degree, size_t *n_rows,
                           size_t *total)
{
    size_t dg = (degree == 0u) ? 1u : degree;
    size_t og = (order > ZB_MAX_ORDER) ? ZB_MAX_ORDER : order;
    assert(n_rows != NULL && total != NULL);
    assert(og <= ZB_MAX_ORDER);
    /* the TIGHT degree-based counts (mirror zb_ndeg_bound / zb_xdeg_bound on the
     * worst-case input degrees: D_P has k-degree ~ og*dg, n-degree ~ og*dg). */
    size_t in_kcnt = dg + 2u;                       /* max input k-coeff count     */
    size_t in_ncnt = dg + 2u;                       /* max input n-coeff count     */
    size_t dp_kcnt = og * (in_kcnt - 1u) + 1u;      /* D_P k-coeff count           */
    size_t dp_ncnt = og * (in_ncnt - 1u) + 1u;      /* D_P n-coeff count           */
    size_t ndeg_cnt = (dp_ncnt > in_ncnt ? dp_ncnt : in_ncnt) + 1u;
    size_t xk_cnt = (dp_kcnt > in_kcnt ? dp_kcnt : in_kcnt) + 1u;
    size_t xn_cnt = (dp_ncnt > in_ncnt ? dp_ncnt : in_ncnt) + 1u;
    size_t a_block = (og + 1u) * ndeg_cnt;
    size_t x_block = xk_cnt * xn_cnt;
    size_t nrow_n = ndeg_cnt + xn_cnt + 4u;
    size_t nrow_k = xk_cnt + dp_kcnt + 4u;
    size_t t = a_block + x_block;
    size_t r = nrow_n * nrow_k;
    if (t > SRMECH_QMAT_MAX_DIM) { t = SRMECH_QMAT_MAX_DIM; }
    *total = t;
    *n_rows = r;
}

/* The arena WORDS one single order `og` needs (0 if that order bails immediately
 * because its system exceeds SRMECH_QMAT_MAX_DIM -- it allocates nothing). */
static size_t zb_order_words(size_t coeff_limbs, size_t og, size_t dg)
{
    size_t cap = zb_cap_for(coeff_limbs, og, dg);
    size_t hw = zb_hdr_words();
    assert(og <= ZB_MAX_ORDER);
    assert(dg >= 1u && cap >= 2u);
    size_t kt = zb_kterms_for(og, dg);
    size_t nt = zb_nterms_for(og, dg);
    size_t bipolys = 32u + 2u * (og + 1u);
    size_t poly_hdr = ((sizeof(zb_poly_t) + sizeof(uint32_t) - 1u)
                       / sizeof(uint32_t));
    size_t per_bipoly = poly_hdr * kt + kt * (2u * hw * nt + 2u * nt * cap);
    size_t bipoly_words = per_bipoly * bipolys;
    size_t carriers = (size_t)cap * (size_t)ZB_N_CARRIERS;
    size_t scratch = (size_t)cap * 8u + 256u;
    size_t n_rows = 0u, total = 0u, n_rows_c, cells_in, cells_out, ecap, qcl;
    size_t in_words, out_words, qws, vecwords;
    zb_matrix_dims(og, dg, &n_rows, &total);
    if (total >= SRMECH_QMAT_MAX_DIM) { return 0u; } /* this order bails -> no alloc */
    n_rows_c = 2u * total + 8u;
    if (n_rows_c > n_rows) { n_rows_c = n_rows; }
    qcl = coeff_limbs * (og + 2u) + 4u;
    cells_in = n_rows * total;
    cells_out = n_rows_c * total;
    ecap = srmech_qmat_entry_cap(qcl, n_rows_c, total);
    in_words = 2u * cells_in * (hw + cap);
    out_words = 2u * cells_out * (hw + ecap)
                + (sizeof(size_t) / sizeof(uint32_t)) * total + 64u;
    qws = srmech_qmat_ws_bound(qcl, n_rows_c, total) / sizeof(uint32_t);
    vecwords = 2u * total * (hw + cap);
    return bipoly_words + carriers + scratch + in_words + out_words + qws
           + vecwords + 2048u;
}

size_t srmech_zeilberger_ws_bound(size_t coeff_limbs, size_t order, size_t degree)
{
    size_t dg = (degree == 0u) ? 1u : degree;
    size_t omax = (order > ZB_MAX_ORDER) ? ZB_MAX_ORDER : order;
    size_t og, best = 0u;
    assert(dg >= 1u);
    assert(omax <= ZB_MAX_ORDER);
    /* each order is tried with a pool RESET (zb_run's mark), so the arena need only
     * fit the LARGEST single feasible order <= max_order (orders whose system
     * exceeds SRMECH_QMAT_MAX_DIM bail before allocating). */
    for (og = 0u; og <= omax; og++) {
        size_t w = zb_order_words(coeff_limbs, og, dg);
        if (w > best) { best = w; }
    }
    if (best < 4096u) { best = 4096u; }
    assert(best >= 4096u);
    return best * sizeof(uint32_t);
}

/* ---- the public entry --------------------------------------------- */

srmech_status_t srmech_zeilberger(
        const srmech_bigint_t *rn_num_n, const srmech_bigint_t *rn_num_d,
        const size_t *rn_num_klen, size_t rn_num_kdeg,
        const srmech_bigint_t *rn_den_n, const srmech_bigint_t *rn_den_d,
        const size_t *rn_den_klen, size_t rn_den_kdeg,
        const srmech_bigint_t *rk_num_n, const srmech_bigint_t *rk_num_d,
        const size_t *rk_num_klen, size_t rk_num_kdeg,
        const srmech_bigint_t *rk_den_n, const srmech_bigint_t *rk_den_d,
        const size_t *rk_den_klen, size_t rk_den_kdeg,
        size_t max_order, size_t n_stride,
        int *out_has, size_t *out_order,
        srmech_bigint_t *coeff_n, srmech_bigint_t *coeff_d, size_t *coeff_nlen,
        srmech_bigint_t *cert_n, srmech_bigint_t *cert_d, size_t *cert_klen,
        size_t *out_cert_kdeg,
        void *ws, size_t ws_len)
{
    zb_ctx_t c;
    zb_solve_t s;
    uint32_t cap;
    size_t cl, deg, og, kt, nt;
    srmech_status_t st;
    assert(out_has != NULL && out_order != NULL);
    assert(coeff_n != NULL && cert_n != NULL);
    if (out_has == NULL || out_order == NULL || coeff_n == NULL
        || cert_n == NULL || coeff_nlen == NULL || cert_klen == NULL
        || out_cert_kdeg == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    *out_has = 0;
    if (rn_den_kdeg == 0u || rk_den_kdeg == 0u) { return SRMECH_ERR_BAD_INPUT; }
    if (max_order > ZB_MAX_ORDER) { max_order = ZB_MAX_ORDER; }
    deg = rn_num_kdeg;
    if (rn_den_kdeg > deg) { deg = rn_den_kdeg; }
    if (rk_num_kdeg > deg) { deg = rk_num_kdeg; }
    if (rk_den_kdeg > deg) { deg = rk_den_kdeg; }
    if (n_stride > deg) { deg = n_stride; }
    if (deg == 0u) { deg = 1u; }
    if (deg > ZB_MAX_DEG) { return SRMECH_ERR_BAD_INPUT; }
    og = max_order;
    cl = zb_input_limbs(rn_num_n, zb_count(rn_num_klen, rn_num_kdeg));
    {
        size_t cl2 = zb_input_limbs(rk_den_n, zb_count(rk_den_klen, rk_den_kdeg));
        if (cl2 > cl) { cl = cl2; }
    }
    cap = (uint32_t)zb_cap_for(cl, og, deg);
    st = zb_ctx_init(&c, cap, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    kt = zb_kterms_for(og, deg);
    nt = zb_nterms_for(og, deg);
    st = zb_solve_alloc(&c, &s, kt, nt, og);
    if (st != SRMECH_OK) { return st; }
    /* load the four input ratios */
    st = zb_load_bipoly(&c, &s.rn_n, rn_num_n, rn_num_d, rn_num_klen, rn_num_kdeg);
    if (st == SRMECH_OK) { st = zb_load_bipoly(&c, &s.rn_d, rn_den_n, rn_den_d,
                                               rn_den_klen, rn_den_kdeg); }
    if (st == SRMECH_OK) { st = zb_load_bipoly(&c, &s.rk_n, rk_num_n, rk_num_d,
                                               rk_num_klen, rk_num_kdeg); }
    if (st == SRMECH_OK) { st = zb_load_bipoly(&c, &s.rk_d, rk_den_n, rk_den_d,
                                               rk_den_klen, rk_den_kdeg); }
    if (st != SRMECH_OK) { return st; }
    return zb_run(&c, &s, og, out_has, out_order, coeff_n, coeff_d, coeff_nlen,
                  cert_n, cert_d, cert_klen, out_cert_kdeg);
}
