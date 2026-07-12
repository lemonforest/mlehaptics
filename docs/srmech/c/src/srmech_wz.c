/*
 * srmech_wz.c -- the Wilf-Zeilberger VERIFY primitive (the THIRD and FINAL public
 * op of the section 76 "telescope" Sigma-row closed-form prover, F929). The C peer
 * of the VERIFY half of srmech.amsc.wz_certificate.wz_certificate.
 *
 * srmech_wz_verify CHECKS that a candidate WZ certificate R(n,k) = Xn/Xd satisfies
 * the WZ equation for the proper hypergeometric term F(n,k) given by its two term
 * ratios r_n = An/Ad, r_k = Bn/Bd (each an exact-rational BIVARIATE polynomial over
 * Q[n,k], the same flat k-ascending-Poly-in-n encoding the zeilberger peer uses):
 *
 *   F(n+1,k) - F(n,k) = G(n,k+1) - G(n,k),   G(n,k) = R(n,k) * F(n,k).
 *
 * Dividing the WZ equation by F(n,k) gives the rational identity
 *   r_n - 1 = R(n,k+1) * r_k - R(n,k),
 * and clearing denominators turns it into the single bivariate POLYNOMIAL identity
 *   (An - Ad) * (Xd1 * Bd * Xd)  ==  (Xn1 * Bn * Xd - Xn * Xd1 * Bd) * Ad,
 * where Xn1/Xd1 are the k->k+1 shifts of Xn/Xd. This is a COMPLETE verification --
 * bounded only by the input degrees, NOT by any order (unlike the rc42 zeilberger
 * peer's order<=1 cap). So srmech_wz_verify is a FULL C mirror of the Python verify.
 *
 * Method (exact over Q[n,k], no float): build both sides as exact-Q bivariate
 * polynomials (a 2-D grid of Q over caller-arena srmech_bigint) and compare them
 * coefficient-by-coefficient. NO solve, NO order loop, NO qmat. out_equal = 1 iff
 * the identity holds. No malloc (JPL Rule 3): every working bipoly is carved from
 * the caller arena `ws`. Any residual overflow returns SRMECH_ERR_OVERFLOW (never a
 * wrap); the Python op then runs its ceiling-free pure-Q compare (standalone-honor).
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto/recursion): OK -- iterative, flat helpers
 *   - Rule 2 (bounded loops)    : OK -- bounds are degree counts
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

/* The largest per-direction degree the C verify handles in a sane caller arena.
 * A genuinely huge-degree input returns SRMECH_ERR_OVERFLOW (or BAD_INPUT) -> the
 * Python pure-Q compare (the standalone-complete honor). */
#define WZ_MAX_DEG 32u

/* ---- scalar exact-Q context (mirrors the zeilberger zb_ctx) ------- */
typedef struct wz_ctx {
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
} wz_ctx_t;

#define WZ_N_CARRIERS 16u  /* qa,qb,sub (x2)=6, t0,t1,g,rem,rs0,rs1,z0,z1=8, +2 pad */

/* A Poly-in-n: a parallel (num,den) srmech_bigint array + a live length. */
typedef struct wz_poly {
    srmech_bigint_t *n;
    srmech_bigint_t *d;
    size_t           len;
    size_t           cap_terms;
} wz_poly_t;

/* A BiPoly(n,k): an array of (k_cap) Poly-in-n slots + a live k-length. */
typedef struct wz_bipoly {
    wz_poly_t *kc;          /* kc[dk] is the Poly-in-n coeff of k^dk           */
    size_t     klen;        /* live k-length (trimmed)                         */
    size_t     k_cap;       /* slot count                                      */
} wz_bipoly_t;

/* ---- forward declarations (Rule 1: no recursion) ------------------ */
static uint32_t *wz_take(uint32_t *base, size_t words, size_t *cur, size_t cnt);
static srmech_status_t wz_bind(srmech_bigint_t *b, uint32_t *base, size_t words,
                               size_t *cur, uint32_t cap);
static size_t wz_hdr_words(void);
static srmech_status_t wz_ctx_init(wz_ctx_t *c, uint32_t cap, void *ws,
                                   size_t ws_len);
static srmech_status_t wz_q_reduce(wz_ctx_t *c, srmech_bigint_t *num,
                                   srmech_bigint_t *den);
static srmech_status_t wz_q_add(wz_ctx_t *c, srmech_bigint_t *on,
                                srmech_bigint_t *od, const srmech_bigint_t *an,
                                const srmech_bigint_t *ad, const srmech_bigint_t *bn,
                                const srmech_bigint_t *bd, int sub);
static srmech_status_t wz_q_mul(wz_ctx_t *c, srmech_bigint_t *on,
                                srmech_bigint_t *od, const srmech_bigint_t *an,
                                const srmech_bigint_t *ad, const srmech_bigint_t *bn,
                                const srmech_bigint_t *bd);
static size_t wz_trim(const srmech_bigint_t *nums, size_t n);
static srmech_status_t wz_poly_alloc(wz_ctx_t *c, wz_poly_t *p, size_t terms);
static srmech_status_t wz_poly_zero(wz_poly_t *p);
static srmech_status_t wz_poly_copy(wz_poly_t *dst, const wz_poly_t *src);
static srmech_status_t wz_poly_addsub(wz_ctx_t *c, wz_poly_t *out,
                                      const wz_poly_t *a, const wz_poly_t *b,
                                      int sub);
static srmech_status_t wz_poly_mul(wz_ctx_t *c, wz_poly_t *out,
                                   const wz_poly_t *a, const wz_poly_t *b);
static srmech_status_t wz_bipoly_alloc(wz_ctx_t *c, wz_bipoly_t *b, size_t k_terms,
                                       size_t n_terms);
static void wz_bipoly_trim(wz_bipoly_t *b);
static srmech_status_t wz_bipoly_copy(wz_bipoly_t *dst, const wz_bipoly_t *src);
static srmech_status_t wz_bipoly_addsub(wz_ctx_t *c, wz_bipoly_t *out,
                                        const wz_bipoly_t *a, const wz_bipoly_t *b,
                                        int sub);
static srmech_status_t wz_bipoly_mul(wz_ctx_t *c, wz_bipoly_t *out,
                                     const wz_bipoly_t *a, const wz_bipoly_t *b,
                                     wz_poly_t *acc, wz_poly_t *prod);
static srmech_status_t wz_bipoly_shift_k1(wz_ctx_t *c, wz_bipoly_t *out,
                                          const wz_bipoly_t *p,
                                          wz_bipoly_t *acc, wz_bipoly_t *tmp,
                                          wz_poly_t *pacc);
static int wz_bipoly_eq(const wz_bipoly_t *a, const wz_bipoly_t *b);

/* ---- caller-arena carve (mirror zeilberger) ----------------------- */

static uint32_t *wz_take(uint32_t *base, size_t words, size_t *cur, size_t cnt)
{
    uint32_t *p;
    assert(base != NULL && cur != NULL);
    assert(*cur <= words);
    if (cnt > words || *cur > words - cnt) { return NULL; }
    p = base + *cur;
    *cur += cnt;
    return p;
}

static srmech_status_t wz_bind(srmech_bigint_t *b, uint32_t *base, size_t words,
                               size_t *cur, uint32_t cap)
{
    uint32_t *limbs = wz_take(base, words, cur, cap);
    assert(b != NULL && cap > 0u);
    assert(base != NULL || words == 0u);
    if (limbs == NULL) { return SRMECH_ERR_OVERFLOW; }
    b->limbs = limbs;
    b->cap = cap;
    b->n = 0u;
    b->sign = 0;
    return SRMECH_OK;
}

static size_t wz_hdr_words(void)
{
    size_t hw = (sizeof(srmech_bigint_t) + sizeof(uint32_t) - 1u)
                / sizeof(uint32_t);
    assert(sizeof(srmech_bigint_t) > 0u);
    assert(hw >= 1u);
    return hw;
}

static srmech_status_t wz_ctx_init(wz_ctx_t *c, uint32_t cap, void *ws,
                                   size_t ws_len)
{
    uint32_t *base = (uint32_t *)ws;
    size_t words = ws_len / sizeof(uint32_t);
    size_t carrier_words = (size_t)cap * (size_t)WZ_N_CARRIERS;
    size_t scratch_words = (size_t)cap * 8u + 256u;
    srmech_status_t st = SRMECH_OK;
    assert(c != NULL);
    assert((uintptr_t)ws % sizeof(uint32_t) == 0u || ws == NULL);
    c->cap = cap;
    if (words < carrier_words + scratch_words) { return SRMECH_ERR_OVERFLOW; }
    c->pool = base;
    c->pool_words = words - scratch_words;
    c->pool_cur = 0u;
    st |= wz_bind(&c->qa_n, base, c->pool_words, &c->pool_cur, cap);
    st |= wz_bind(&c->qa_d, base, c->pool_words, &c->pool_cur, cap);
    st |= wz_bind(&c->qb_n, base, c->pool_words, &c->pool_cur, cap);
    st |= wz_bind(&c->qb_d, base, c->pool_words, &c->pool_cur, cap);
    st |= wz_bind(&c->sub_n, base, c->pool_words, &c->pool_cur, cap);
    st |= wz_bind(&c->sub_d, base, c->pool_words, &c->pool_cur, cap);
    st |= wz_bind(&c->t0, base, c->pool_words, &c->pool_cur, cap);
    st |= wz_bind(&c->t1, base, c->pool_words, &c->pool_cur, cap);
    st |= wz_bind(&c->g, base, c->pool_words, &c->pool_cur, cap);
    st |= wz_bind(&c->rem, base, c->pool_words, &c->pool_cur, cap);
    st |= wz_bind(&c->rs0, base, c->pool_words, &c->pool_cur, cap);
    st |= wz_bind(&c->rs1, base, c->pool_words, &c->pool_cur, cap);
    st |= wz_bind(&c->z0, base, c->pool_words, &c->pool_cur, cap);
    st |= wz_bind(&c->z1, base, c->pool_words, &c->pool_cur, cap);
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

static srmech_status_t wz_q_reduce(wz_ctx_t *c, srmech_bigint_t *num,
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

static srmech_status_t wz_q_add(wz_ctx_t *c, srmech_bigint_t *on,
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
    return wz_q_reduce(c, on, od);
}

static srmech_status_t wz_q_mul(wz_ctx_t *c, srmech_bigint_t *on,
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
    return wz_q_reduce(c, on, od);
}

/* ---- Poly-in-n carve + ops ---------------------------------------- */

static size_t wz_trim(const srmech_bigint_t *nums, size_t n)
{
    size_t k = n;
    assert(nums != NULL || n == 0u);
    while (k > 0u && srmech_bigint_is_zero(&nums[k - 1u])) { k--; }
    assert(k <= n);
    return k;
}

static srmech_status_t wz_poly_alloc(wz_ctx_t *c, wz_poly_t *p, size_t terms)
{
    size_t hw = wz_hdr_words(), k;
    uint32_t *hn, *hd;
    srmech_status_t st;
    assert(c != NULL && p != NULL && terms > 0u);
    assert(hw >= 1u);
    hn = wz_take(c->pool, c->pool_words, &c->pool_cur, hw * terms);
    hd = wz_take(c->pool, c->pool_words, &c->pool_cur, hw * terms);
    if (hn == NULL || hd == NULL) { return SRMECH_ERR_OVERFLOW; }
    p->n = (srmech_bigint_t *)(void *)hn;
    p->d = (srmech_bigint_t *)(void *)hd;
    p->len = 0u;
    p->cap_terms = terms;
    for (k = 0u; k < terms; k++) {
        st = wz_bind(&p->n[k], c->pool, c->pool_words, &c->pool_cur, c->cap);
        if (st == SRMECH_OK) { st = wz_bind(&p->d[k], c->pool, c->pool_words,
                                            &c->pool_cur, c->cap); }
        if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&p->n[k], 0); }
        if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&p->d[k], 1); }
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

static srmech_status_t wz_poly_zero(wz_poly_t *p)
{
    assert(p != NULL);
    assert(p->len <= p->cap_terms);
    p->len = 0u;
    return SRMECH_OK;
}

static srmech_status_t wz_poly_copy(wz_poly_t *dst, const wz_poly_t *src)
{
    size_t k;
    srmech_status_t st;
    assert(dst != NULL && src != NULL);
    assert(dst->cap_terms >= src->len);
    for (k = 0u; k < src->len; k++) {
        st = srmech_bigint_copy(&dst->n[k], &src->n[k]);
        if (st == SRMECH_OK) { st = srmech_bigint_copy(&dst->d[k], &src->d[k]); }
        if (st != SRMECH_OK) { return st; }
    }
    dst->len = src->len;
    return SRMECH_OK;
}

static srmech_status_t wz_poly_addsub(wz_ctx_t *c, wz_poly_t *out,
                                      const wz_poly_t *a, const wz_poly_t *b,
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
        st = wz_q_add(c, &out->n[k], &out->d[k], an, ad, bn, bd, sub);
        if (st != SRMECH_OK) { return st; }
    }
    out->len = wz_trim(out->n, m);
    return SRMECH_OK;
}

static srmech_status_t wz_poly_mul(wz_ctx_t *c, wz_poly_t *out,
                                   const wz_poly_t *a, const wz_poly_t *b)
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
            st = wz_q_mul(c, &c->qa_n, &c->qa_d, &a->n[i], &a->d[i],
                          &b->n[j], &b->d[j]);
            if (st == SRMECH_OK) { st = srmech_bigint_copy(&c->qb_n, &out->n[i + j]); }
            if (st == SRMECH_OK) { st = srmech_bigint_copy(&c->qb_d, &out->d[i + j]); }
            if (st == SRMECH_OK) { st = wz_q_add(c, &out->n[i + j], &out->d[i + j],
                                                 &c->qb_n, &c->qb_d,
                                                 &c->qa_n, &c->qa_d, 0); }
            if (st != SRMECH_OK) { return st; }
        }
    }
    out->len = wz_trim(out->n, m);
    return SRMECH_OK;
}

/* ---- BiPoly carve + ops ------------------------------------------- */

static srmech_status_t wz_bipoly_alloc(wz_ctx_t *c, wz_bipoly_t *b, size_t k_terms,
                                       size_t n_terms)
{
    size_t dk;
    uint32_t *hk;
    srmech_status_t st;
    assert(c != NULL && b != NULL && k_terms > 0u && n_terms > 0u);
    assert(c->pool != NULL || c->pool_words == 0u);
    hk = wz_take(c->pool, c->pool_words, &c->pool_cur,
                 ((sizeof(wz_poly_t) + sizeof(uint32_t) - 1u) / sizeof(uint32_t))
                 * k_terms);
    if (hk == NULL) { return SRMECH_ERR_OVERFLOW; }
    b->kc = (wz_poly_t *)(void *)hk;
    b->klen = 0u;
    b->k_cap = k_terms;
    for (dk = 0u; dk < k_terms; dk++) {
        st = wz_poly_alloc(c, &b->kc[dk], n_terms);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

static void wz_bipoly_trim(wz_bipoly_t *b)
{
    assert(b != NULL);
    assert(b->klen <= b->k_cap);
    while (b->klen > 0u && b->kc[b->klen - 1u].len == 0u) { b->klen--; }
}

static srmech_status_t wz_bipoly_copy(wz_bipoly_t *dst, const wz_bipoly_t *src)
{
    size_t dk;
    srmech_status_t st;
    assert(dst != NULL && src != NULL);
    assert(dst->k_cap >= src->klen);
    for (dk = 0u; dk < src->klen; dk++) {
        st = wz_poly_copy(&dst->kc[dk], &src->kc[dk]);
        if (st != SRMECH_OK) { return st; }
    }
    dst->klen = src->klen;
    return SRMECH_OK;
}

/* out = a +/- b (per k-coefficient Poly-in-n add/sub). */
static srmech_status_t wz_bipoly_addsub(wz_ctx_t *c, wz_bipoly_t *out,
                                        const wz_bipoly_t *a, const wz_bipoly_t *b,
                                        int sub)
{
    size_t dk, m = (a->klen > b->klen) ? a->klen : b->klen;
    wz_poly_t zp;
    srmech_status_t st;
    assert(c != NULL && out != NULL && a != NULL && b != NULL);
    assert(out->k_cap >= m);
    zp.n = NULL; zp.d = NULL; zp.len = 0u; zp.cap_terms = 0u;  /* the zero Poly  */
    for (dk = 0u; dk < m; dk++) {
        const wz_poly_t *ap = (dk < a->klen) ? &a->kc[dk] : &zp;
        const wz_poly_t *bp = (dk < b->klen) ? &b->kc[dk] : &zp;
        st = wz_poly_addsub(c, &out->kc[dk], ap, bp, sub);
        if (st != SRMECH_OK) { return st; }
    }
    out->klen = m;
    wz_bipoly_trim(out);
    return SRMECH_OK;
}

/* out = a * b (bipoly product). acc/prod are Poly-in-n scratch. */
static srmech_status_t wz_bipoly_mul(wz_ctx_t *c, wz_bipoly_t *out,
                                     const wz_bipoly_t *a, const wz_bipoly_t *b,
                                     wz_poly_t *acc, wz_poly_t *prod)
{
    size_t i, j, m, dk;
    srmech_status_t st;
    assert(c != NULL && out != NULL && a != NULL && b != NULL);
    assert(acc != NULL && prod != NULL);
    if (a->klen == 0u || b->klen == 0u) { out->klen = 0u; return SRMECH_OK; }
    m = a->klen + b->klen - 1u;
    assert(out->k_cap >= m);
    for (dk = 0u; dk < m; dk++) { (void)wz_poly_zero(&out->kc[dk]); }
    for (i = 0u; i < a->klen; i++) {
        if (a->kc[i].len == 0u) { continue; }
        for (j = 0u; j < b->klen; j++) {
            if (b->kc[j].len == 0u) { continue; }
            st = wz_poly_mul(c, prod, &a->kc[i], &b->kc[j]);
            if (st == SRMECH_OK) { st = wz_poly_copy(acc, &out->kc[i + j]); }
            if (st == SRMECH_OK) { st = wz_poly_addsub(c, &out->kc[i + j],
                                                       acc, prod, 0); }
            if (st != SRMECH_OK) { return st; }
        }
    }
    out->klen = m;
    wz_bipoly_trim(out);
    return SRMECH_OK;
}

/* out(n,k) = p(n, k+1): synthetic Horner over (k+1) in the k-variable. acc/tmp are
 * bipoly scratch (ping-pong; neither may alias `out` or `p`); pacc Poly-in-n
 * scratch. tmp = acc*(k+1) is built by SHIFT-UP (tmp[dk]=acc[dk-1]) PLUS acc[dk]. */
static srmech_status_t wz_bipoly_shift_k1(wz_ctx_t *c, wz_bipoly_t *out,
                                          const wz_bipoly_t *p,
                                          wz_bipoly_t *acc, wz_bipoly_t *tmp,
                                          wz_poly_t *pacc)
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
            const wz_poly_t *shifted = (dk >= 1u) ? &acc->kc[dk - 1u] : NULL;
            const wz_poly_t *same = (dk < alen) ? &acc->kc[dk] : NULL;
            if (shifted != NULL && same != NULL) {
                st = wz_poly_addsub(c, &tmp->kc[dk], shifted, same, 0);
            } else if (shifted != NULL) {
                st = wz_poly_copy(&tmp->kc[dk], shifted);
            } else if (same != NULL) {
                st = wz_poly_copy(&tmp->kc[dk], same);
            } else {
                st = wz_poly_zero(&tmp->kc[dk]);
            }
            if (st != SRMECH_OK) { return st; }
        }
        tmp->klen = m;
        st = wz_poly_addsub(c, pacc, &tmp->kc[0], &p->kc[i - 1u], 0);
        if (st == SRMECH_OK) { st = wz_poly_copy(&tmp->kc[0], pacc); }
        if (st != SRMECH_OK) { return st; }
        wz_bipoly_trim(tmp);
        st = wz_bipoly_copy(acc, tmp);
        if (st != SRMECH_OK) { return st; }
    }
    return wz_bipoly_copy(out, acc);
}

/* exact equality of two trimmed exact-Q bipolys. */
static int wz_bipoly_eq(const wz_bipoly_t *a, const wz_bipoly_t *b)
{
    size_t dk, dn;
    assert(a != NULL && b != NULL);
    assert(a->klen <= a->k_cap && b->klen <= b->k_cap);
    if (a->klen != b->klen) { return 0; }
    for (dk = 0u; dk < a->klen; dk++) {
        const wz_poly_t *ap = &a->kc[dk];
        const wz_poly_t *bp = &b->kc[dk];
        if (ap->len != bp->len) { return 0; }
        for (dn = 0u; dn < ap->len; dn++) {
            if (srmech_bigint_cmp(&ap->n[dn], &bp->n[dn]) != 0) { return 0; }
            if (srmech_bigint_cmp(&ap->d[dn], &bp->d[dn]) != 0) { return 0; }
        }
    }
    return 1;
}

/* ===================================================================
 * The VERIFY orchestration: build lhs + rhs of the cleared WZ identity and compare.
 * =================================================================== */

/* The working-bipoly roster: the six inputs + the shift/product scratch. */
typedef struct wz_solve {
    wz_bipoly_t an, ad, bn, bd, xn, xd;     /* the six inputs                      */
    wz_bipoly_t xn1, xd1;                    /* Xn(k+1), Xd(k+1)                    */
    wz_bipoly_t lhs, rhs;                    /* the two cleared sides               */
    wz_bipoly_t t0, t1, t2;                  /* general product scratch             */
    wz_bipoly_t sk_acc, sk_tmp;             /* shift_k scratch                      */
    wz_poly_t   pacc, pprod;                /* Poly-in-n scratch                    */
    size_t      kt, nt;
} wz_solve_t;

static size_t wz_count(const size_t *klen, size_t kdeg)
{
    size_t k, total = 0u;
    assert(klen != NULL || kdeg == 0u);
    assert(kdeg <= (size_t)WZ_MAX_DEG + 2u);
    for (k = 0u; k < kdeg; k++) { total += klen[k]; }
    return total;
}

/* The max n-coefficient COUNT across a flat bivariate input's k-slots (the input's
 * n-degree + 1) -- used to size the degree envelope, since the cleared identity's
 * n-degree grows with the product n-degrees, not just the k-degrees. */
static size_t wz_max_ncount(const srmech_bigint_t *cn, const size_t *klen,
                            size_t kdeg)
{
    size_t dk, d = 0u;
    assert(cn != NULL || kdeg == 0u);
    assert(klen != NULL || kdeg == 0u);
    (void)cn;
    for (dk = 0u; dk < kdeg; dk++) { if (klen[dk] > d) { d = klen[dk]; } }
    return d;
}

/* Load a flat (num,den) bigint pair stream + per-k lengths into a bipoly. */
static srmech_status_t wz_load_bipoly(wz_bipoly_t *b, const srmech_bigint_t *cn,
                                      const srmech_bigint_t *cd,
                                      const size_t *klen, size_t kdeg)
{
    size_t dk, idx = 0u, j;
    srmech_status_t st;
    assert(b != NULL);
    assert(b->k_cap >= kdeg);
    for (dk = 0u; dk < kdeg; dk++) {
        size_t nlen = klen[dk];
        assert(b->kc[dk].cap_terms >= nlen);
        for (j = 0u; j < nlen; j++) {
            st = srmech_bigint_copy(&b->kc[dk].n[j], &cn[idx + j]);
            if (st == SRMECH_OK) { st = srmech_bigint_copy(&b->kc[dk].d[j],
                                                           &cd[idx + j]); }
            if (st != SRMECH_OK) { return st; }
        }
        b->kc[dk].len = wz_trim(b->kc[dk].n, nlen);
        idx += nlen;
    }
    b->klen = kdeg;
    wz_bipoly_trim(b);
    return SRMECH_OK;
}

static srmech_status_t wz_solve_alloc(wz_ctx_t *c, wz_solve_t *s, size_t kt,
                                      size_t nt)
{
    srmech_status_t st = SRMECH_OK;
    assert(c != NULL && s != NULL && kt > 0u && nt > 0u);
    assert(kt <= (size_t)WZ_MAX_DEG * 8u + 64u);
    s->kt = kt; s->nt = nt;
    st |= wz_bipoly_alloc(c, &s->an, kt, nt); st |= wz_bipoly_alloc(c, &s->ad, kt, nt);
    st |= wz_bipoly_alloc(c, &s->bn, kt, nt); st |= wz_bipoly_alloc(c, &s->bd, kt, nt);
    st |= wz_bipoly_alloc(c, &s->xn, kt, nt); st |= wz_bipoly_alloc(c, &s->xd, kt, nt);
    st |= wz_bipoly_alloc(c, &s->xn1, kt, nt); st |= wz_bipoly_alloc(c, &s->xd1, kt, nt);
    st |= wz_bipoly_alloc(c, &s->lhs, kt, nt); st |= wz_bipoly_alloc(c, &s->rhs, kt, nt);
    st |= wz_bipoly_alloc(c, &s->t0, kt, nt); st |= wz_bipoly_alloc(c, &s->t1, kt, nt);
    st |= wz_bipoly_alloc(c, &s->t2, kt, nt);
    st |= wz_bipoly_alloc(c, &s->sk_acc, kt, nt); st |= wz_bipoly_alloc(c, &s->sk_tmp, kt, nt);
    st |= wz_poly_alloc(c, &s->pacc, nt); st |= wz_poly_alloc(c, &s->pprod, nt);
    if (st != SRMECH_OK) { return SRMECH_ERR_OVERFLOW; }
    return SRMECH_OK;
}

/* Build lhs = (An - Ad) * (Xd1 * Bd * Xd). */
static srmech_status_t wz_build_lhs(wz_ctx_t *c, wz_solve_t *s)
{
    srmech_status_t st;
    assert(c != NULL && s != NULL);
    assert(s->an.k_cap >= 1u);
    st = wz_bipoly_addsub(c, &s->t0, &s->an, &s->ad, 1);          /* An - Ad         */
    if (st == SRMECH_OK) { st = wz_bipoly_mul(c, &s->t1, &s->xd1, &s->bd,
                                              &s->pacc, &s->pprod); }  /* Xd1 * Bd    */
    if (st == SRMECH_OK) { st = wz_bipoly_mul(c, &s->t2, &s->t1, &s->xd,
                                              &s->pacc, &s->pprod); }  /* * Xd        */
    if (st == SRMECH_OK) { st = wz_bipoly_mul(c, &s->lhs, &s->t0, &s->t2,
                                              &s->pacc, &s->pprod); }
    return st;
}

/* Build rhs = (Xn1 * Bn * Xd - Xn * Xd1 * Bd) * Ad. */
static srmech_status_t wz_build_rhs(wz_ctx_t *c, wz_solve_t *s)
{
    srmech_status_t st;
    assert(c != NULL && s != NULL);
    assert(s->ad.k_cap >= 1u);
    st = wz_bipoly_mul(c, &s->t0, &s->xn1, &s->bn, &s->pacc, &s->pprod); /* Xn1*Bn  */
    if (st == SRMECH_OK) { st = wz_bipoly_mul(c, &s->t1, &s->t0, &s->xd,
                                              &s->pacc, &s->pprod); }     /* *Xd     */
    if (st == SRMECH_OK) { st = wz_bipoly_mul(c, &s->t0, &s->xn, &s->xd1,
                                              &s->pacc, &s->pprod); }     /* Xn*Xd1  */
    if (st == SRMECH_OK) { st = wz_bipoly_mul(c, &s->t2, &s->t0, &s->bd,
                                              &s->pacc, &s->pprod); }     /* *Bd     */
    if (st == SRMECH_OK) { st = wz_bipoly_addsub(c, &s->t0, &s->t1, &s->t2, 1); }
    if (st == SRMECH_OK) { st = wz_bipoly_mul(c, &s->rhs, &s->t0, &s->ad,
                                              &s->pacc, &s->pprod); }
    return st;
}

/* ---- input limb estimate + arena bounds --------------------------- */

static size_t wz_input_limbs(const srmech_bigint_t *cn, size_t total)
{
    size_t k, cl = 1u;
    assert(cn != NULL || total == 0u);
    assert(cl >= 1u);
    for (k = 0u; k < total; k++) { if (cn[k].n > cl) { cl = cn[k].n; } }
    return cl;
}

static size_t wz_cap_for(size_t coeff_limbs, size_t degree)
{
    size_t cl = (coeff_limbs == 0u) ? 1u : coeff_limbs;
    size_t dg = (degree == 0u) ? 1u : degree;
    /* The cleared identity is a 4-fold bivariate product of the inputs; an
     * envelope dominating the worst intermediate (coeff growth ~ 4x input bits,
     * plus the bivariate convolution carry). A genuinely huge input that exceeds
     * this returns OVERFLOW -> the Python pure-Q compare (the standalone-honor). */
    size_t step = cl * 6u * (dg + 2u) + 8u;
    size_t cap = step * 2u + cl * 4u + 48u;
    assert(cap >= step);
    assert(cap >= cl);
    return cap;
}

size_t srmech_wz_verify_out_cap(size_t coeff_limbs, size_t degree)
{
    size_t cap = wz_cap_for(coeff_limbs, degree);
    assert(cap >= 2u);
    assert(cap >= coeff_limbs);
    return cap;
}

/* per-direction term counts the working bipolys carry. The heaviest intermediate
 * is the 4-fold product (k- and n-degree ~ 4x input); bound generously. */
static size_t wz_terms_for(size_t degree)
{
    size_t dg = (degree == 0u) ? 1u : degree;
    size_t terms = 5u * (dg + 1u) + 8u;
    assert(terms >= dg);
    assert(terms >= 8u);
    return terms;
}

size_t srmech_wz_verify_ws_bound(size_t coeff_limbs, size_t degree)
{
    size_t dg = (degree == 0u) ? 1u : degree;
    size_t cl = (coeff_limbs == 0u) ? 1u : coeff_limbs;
    size_t cap = wz_cap_for(cl, dg);
    size_t hw = wz_hdr_words();
    size_t kt = wz_terms_for(dg);
    size_t nt = wz_terms_for(dg);
    size_t bipolys = 16u;                            /* the wz_solve roster + pad   */
    size_t poly_hdr = ((sizeof(wz_poly_t) + sizeof(uint32_t) - 1u)
                       / sizeof(uint32_t));
    size_t per_bipoly = poly_hdr * kt + kt * (2u * hw * nt + 2u * nt * cap);
    size_t bipoly_words = per_bipoly * bipolys;
    size_t carriers = (size_t)cap * (size_t)WZ_N_CARRIERS;
    size_t scratch = (size_t)cap * 8u + 256u;
    size_t poly_scr = 2u * (poly_hdr + nt * (2u * hw + 2u * cap));
    size_t best = bipoly_words + carriers + scratch + poly_scr + 4096u;
    assert(dg >= 1u && cap >= 2u);
    assert(best >= bipoly_words);
    return best * sizeof(uint32_t);
}

/* ---- the public entry --------------------------------------------- */

srmech_status_t srmech_wz_verify(
        const srmech_bigint_t *rn_num_n, const srmech_bigint_t *rn_num_d,
        const size_t *rn_num_klen, size_t rn_num_kdeg,
        const srmech_bigint_t *rn_den_n, const srmech_bigint_t *rn_den_d,
        const size_t *rn_den_klen, size_t rn_den_kdeg,
        const srmech_bigint_t *rk_num_n, const srmech_bigint_t *rk_num_d,
        const size_t *rk_num_klen, size_t rk_num_kdeg,
        const srmech_bigint_t *rk_den_n, const srmech_bigint_t *rk_den_d,
        const size_t *rk_den_klen, size_t rk_den_kdeg,
        const srmech_bigint_t *cert_num_n, const srmech_bigint_t *cert_num_d,
        const size_t *cert_num_klen, size_t cert_num_kdeg,
        const srmech_bigint_t *cert_den_n, const srmech_bigint_t *cert_den_d,
        const size_t *cert_den_klen, size_t cert_den_kdeg,
        int *out_equal, void *ws, size_t ws_len)
{
    wz_ctx_t c;
    wz_solve_t s;
    uint32_t cap;
    size_t cl, deg, kt, nt;
    srmech_status_t st;
    assert(out_equal != NULL);
    assert(rn_num_n != NULL && cert_num_n != NULL);
    if (out_equal == NULL) { return SRMECH_ERR_NULL_ARG; }
    if (rn_num_n == NULL || rn_den_n == NULL || rk_num_n == NULL
        || rk_den_n == NULL || cert_num_n == NULL || cert_den_n == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    *out_equal = 0;
    if (rn_den_kdeg == 0u || rk_den_kdeg == 0u || cert_den_kdeg == 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    deg = rn_num_kdeg;
    if (rn_den_kdeg > deg) { deg = rn_den_kdeg; }
    if (rk_num_kdeg > deg) { deg = rk_num_kdeg; }
    if (rk_den_kdeg > deg) { deg = rk_den_kdeg; }
    if (cert_num_kdeg > deg) { deg = cert_num_kdeg; }
    if (cert_den_kdeg > deg) { deg = cert_den_kdeg; }
    /* the cleared identity also raises the n-degree; fold the max input n-count. */
    {
        size_t nd = wz_max_ncount(rn_num_n, rn_num_klen, rn_num_kdeg);
        size_t v;
        v = wz_max_ncount(rk_den_n, rk_den_klen, rk_den_kdeg); if (v > nd) { nd = v; }
        v = wz_max_ncount(cert_num_n, cert_num_klen, cert_num_kdeg); if (v > nd) { nd = v; }
        v = wz_max_ncount(cert_den_n, cert_den_klen, cert_den_kdeg); if (v > nd) { nd = v; }
        if (nd > deg) { deg = nd; }
    }
    if (deg == 0u) { deg = 1u; }
    if (deg > WZ_MAX_DEG) { return SRMECH_ERR_BAD_INPUT; }
    cl = wz_input_limbs(rn_num_n, wz_count(rn_num_klen, rn_num_kdeg));
    {
        size_t cl2 = wz_input_limbs(cert_num_n, wz_count(cert_num_klen, cert_num_kdeg));
        if (cl2 > cl) { cl = cl2; }
        cl2 = wz_input_limbs(rk_den_n, wz_count(rk_den_klen, rk_den_kdeg));
        if (cl2 > cl) { cl = cl2; }
    }
    cap = (uint32_t)wz_cap_for(cl, deg);
    st = wz_ctx_init(&c, cap, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    kt = wz_terms_for(deg);
    nt = wz_terms_for(deg);
    st = wz_solve_alloc(&c, &s, kt, nt);
    if (st != SRMECH_OK) { return st; }
    st = wz_load_bipoly(&s.an, rn_num_n, rn_num_d, rn_num_klen, rn_num_kdeg);
    if (st == SRMECH_OK) { st = wz_load_bipoly(&s.ad, rn_den_n, rn_den_d,
                                               rn_den_klen, rn_den_kdeg); }
    if (st == SRMECH_OK) { st = wz_load_bipoly(&s.bn, rk_num_n, rk_num_d,
                                               rk_num_klen, rk_num_kdeg); }
    if (st == SRMECH_OK) { st = wz_load_bipoly(&s.bd, rk_den_n, rk_den_d,
                                               rk_den_klen, rk_den_kdeg); }
    if (st == SRMECH_OK) { st = wz_load_bipoly(&s.xn, cert_num_n, cert_num_d,
                                               cert_num_klen, cert_num_kdeg); }
    if (st == SRMECH_OK) { st = wz_load_bipoly(&s.xd, cert_den_n, cert_den_d,
                                               cert_den_klen, cert_den_kdeg); }
    if (st != SRMECH_OK) { return st; }
    /* the k->k+1 shifts of the certificate. */
    st = wz_bipoly_shift_k1(&c, &s.xn1, &s.xn, &s.sk_acc, &s.sk_tmp, &s.pacc);
    if (st == SRMECH_OK) { st = wz_bipoly_shift_k1(&c, &s.xd1, &s.xd, &s.sk_acc,
                                                   &s.sk_tmp, &s.pacc); }
    if (st == SRMECH_OK) { st = wz_build_lhs(&c, &s); }
    if (st == SRMECH_OK) { st = wz_build_rhs(&c, &s); }
    if (st != SRMECH_OK) { return st; }
    *out_equal = wz_bipoly_eq(&s.lhs, &s.rhs);
    return SRMECH_OK;
}
