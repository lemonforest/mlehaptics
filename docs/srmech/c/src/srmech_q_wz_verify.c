/*
 * srmech_q_wz_verify.c -- the q-analog of the Wilf-Zeilberger VERIFY primitive (the
 * THIRD and FINAL public op of the q-hypergeometric F929 reduction row, the q-row
 * CLOSER). The C peer of the VERIFY half of srmech.amsc.q_wz_certificate.
 *
 * srmech_q_wz_verify CHECKS that a candidate q-WZ certificate R(X,Y) = Xn/Xd satisfies
 * the q-WZ equation for the proper q-hypergeometric term F(n,k) given by its two
 * bivariate-q term ratios r_n = An/Ad, r_k = Bn/Bd over (X,Y) = (q^n, q^k). Each is a
 * QBiPoly -- a Y-ascending list of QPoly-in-X cells, each QPoly a Laurent-in-X run of
 * Q[q] coefficients (a parallel (num,den) bigint run per X-cell, ascending q-degree;
 * the SAME flat bridge wire form srmech_q_zeilberger consumes: the concatenated q-runs
 * Y-major then X-major, a per-(Y,X)-cell qlen[], a per-Y-cell x_low[]/x_cells[], and
 * the Y-cell count).
 *
 *   F(n+1,k) - F(n,k) = G(n,k+1) - G(n,k),   G(n,k) = R(X,Y) * F(n,k),
 * with G(n,k+1) = (sigma_y R)*(sigma_y F) and sigma_y : Y -> q*Y (the k-direction
 * q-shift: the Y^d cell picks up the Q[q] monomial q^d).
 *
 * Dividing by F(n,k) gives the rational identity r_n - 1 = R(X,qY)*r_k - R(X,Y), and
 * clearing denominators turns it into the single bivariate POLYNOMIAL identity
 *   (An - Ad) * (sigma_y(Xd) * Bd * Xd) ==
 *       (sigma_y(Xn) * Bn * Xd - Xn * sigma_y(Xd) * Bd) * Ad,
 * where sigma_y(Xn)/sigma_y(Xd) are the Y->qY q-shifts of the certificate. This is a
 * COMPLETE verification -- bounded only by the input DEGREES, NOT by any order (unlike
 * the rc56 srmech_q_zeilberger order-<=1 cap). So srmech_q_wz_verify is a FULL C mirror
 * of the Python verify.
 *
 * Method (exact over Q[q], no float): build both sides as exact bivariate-Q[q] QBiPoly
 * (a Y-ascending list of Q[q] QPoly-in-X cells over caller-arena srmech_bigint) and
 * compare them coefficient-by-coefficient. NO solve, NO order loop, NO qmat.
 * out_equal = 1 iff the identity holds. No malloc (JPL Rule 3): every working carrier
 * is carved from the caller arena `ws`. Any residual overflow returns
 * SRMECH_ERR_OVERFLOW (never a wrap); the Python op then runs its ceiling-free pure-Q
 * compare (standalone-honor). Sign is the Class-K pin-slot via the bigint sign branch
 * (never an ALU abs / fabs).
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto/recursion): OK -- iterative, flat helpers
 *   - Rule 2 (bounded loops)    : OK -- bounds are degree / cell counts
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

/* The largest per-direction extent the C verify handles in a sane caller arena (the X-
 * window span, the Y-degree, and the q-degree of any working carrier). A genuinely huge
 * input returns SRMECH_ERR_OVERFLOW / BAD_INPUT -> the Python pure-Q compare. */
#define QWZ_MAX_DEG 32u

/* ---- scalar exact-Q context (mirrors the wz_ctx) ------------------ */
typedef struct qwz_ctx {
    srmech_bigint_t qa_n, qa_d;
    srmech_bigint_t qb_n, qb_d;
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
} qwz_ctx_t;

#define QWZ_N_CARRIERS 16u  /* qa,qb (x2)=4, t0,t1,g,rem,rs0,rs1,z0,z1=8, +4 pad */

/* A q-poly (a Q[q] element): a parallel (num,den) bigint run, ascending q-degree. */
typedef struct qwz_qpoly {
    srmech_bigint_t *n;
    srmech_bigint_t *d;
    size_t           len;
    size_t           cap_terms;
} qwz_qpoly_t;

/* A QPoly-in-X: a contiguous run of (x_cells) Q[q] cells over [x_low, x_low+x_cells),
 * each cell a qwz_qpoly. */
typedef struct qwz_xpoly {
    qwz_qpoly_t *xc;          /* xc[i] = Q[q] coeff of X^(x_low + i)             */
    int64_t      x_low;       /* lowest X-exponent carried                      */
    size_t       x_cells;     /* live X-cell count                              */
    size_t       x_cap;       /* slot count                                     */
} qwz_xpoly_t;

/* A QBiPoly(X,Y): a Y-ascending array of QPoly-in-X cells + a live Y-length. */
typedef struct qwz_qbipoly {
    qwz_xpoly_t *yc;          /* yc[dy] = QPoly-in-X coeff of Y^dy               */
    size_t       ylen;        /* live Y-length (trimmed)                        */
    size_t       y_cap;       /* slot count                                     */
} qwz_qbipoly_t;

/* ---- forward declarations (Rule 1: no recursion) ------------------ */
static uint32_t *qwz_take(uint32_t *base, size_t words, size_t *cur, size_t cnt);
static srmech_status_t qwz_bind(srmech_bigint_t *b, uint32_t *base, size_t words,
                                size_t *cur, uint32_t cap);
static size_t qwz_hdr_words(void);
static srmech_status_t qwz_ctx_init(qwz_ctx_t *c, uint32_t cap, void *ws,
                                    size_t ws_len);
static srmech_status_t qwz_q_reduce(qwz_ctx_t *c, srmech_bigint_t *num,
                                    srmech_bigint_t *den);
static srmech_status_t qwz_q_add(qwz_ctx_t *c, srmech_bigint_t *on,
                                 srmech_bigint_t *od, const srmech_bigint_t *an,
                                 const srmech_bigint_t *ad, const srmech_bigint_t *bn,
                                 const srmech_bigint_t *bd, int sub);
static srmech_status_t qwz_q_mul(qwz_ctx_t *c, srmech_bigint_t *on,
                                 srmech_bigint_t *od, const srmech_bigint_t *an,
                                 const srmech_bigint_t *ad, const srmech_bigint_t *bn,
                                 const srmech_bigint_t *bd);
static size_t qwz_trim(const srmech_bigint_t *nums, size_t n);
static srmech_status_t qwz_qp_alloc(qwz_ctx_t *c, qwz_qpoly_t *p, size_t terms);
static srmech_status_t qwz_qp_zero(qwz_qpoly_t *p);
static srmech_status_t qwz_qp_copy(qwz_qpoly_t *dst, const qwz_qpoly_t *src);
static srmech_status_t qwz_qp_addsub(qwz_ctx_t *c, qwz_qpoly_t *out,
                                     const qwz_qpoly_t *a, const qwz_qpoly_t *b,
                                     int sub);
static srmech_status_t qwz_qp_mul(qwz_ctx_t *c, qwz_qpoly_t *out,
                                  const qwz_qpoly_t *a, const qwz_qpoly_t *b);
static srmech_status_t qwz_qp_qshift(qwz_qpoly_t *out, const qwz_qpoly_t *a,
                                     size_t s);
static int qwz_qp_eq(const qwz_qpoly_t *a, const qwz_qpoly_t *b);
static srmech_status_t qwz_xp_alloc(qwz_ctx_t *c, qwz_xpoly_t *p, size_t x_terms,
                                    size_t n_terms);
static void qwz_xp_trim(qwz_xpoly_t *p);
static srmech_status_t qwz_xp_copy(qwz_xpoly_t *dst, const qwz_xpoly_t *src);
static srmech_status_t qwz_xp_addsub(qwz_ctx_t *c, qwz_xpoly_t *out,
                                     const qwz_xpoly_t *a, const qwz_xpoly_t *b,
                                     int sub);
static srmech_status_t qwz_xp_mul(qwz_ctx_t *c, qwz_xpoly_t *out,
                                  const qwz_xpoly_t *a, const qwz_xpoly_t *b,
                                  qwz_qpoly_t *acc, qwz_qpoly_t *prod);
static int qwz_xp_eq(const qwz_xpoly_t *a, const qwz_xpoly_t *b);
static srmech_status_t qwz_qb_alloc(qwz_ctx_t *c, qwz_qbipoly_t *b, size_t y_terms,
                                    size_t x_terms, size_t n_terms);
static void qwz_qb_trim(qwz_qbipoly_t *b);
static srmech_status_t qwz_qb_addsub(qwz_ctx_t *c, qwz_qbipoly_t *out,
                                     const qwz_qbipoly_t *a, const qwz_qbipoly_t *b,
                                     int sub);
static srmech_status_t qwz_qb_mul(qwz_ctx_t *c, qwz_qbipoly_t *out,
                                  const qwz_qbipoly_t *a, const qwz_qbipoly_t *b,
                                  qwz_xpoly_t *acc, qwz_xpoly_t *prod,
                                  qwz_qpoly_t *qa, qwz_qpoly_t *qp);
static srmech_status_t qwz_qb_qshift_y(qwz_qbipoly_t *out, const qwz_qbipoly_t *a);
static int qwz_qb_eq(const qwz_qbipoly_t *a, const qwz_qbipoly_t *b);

/* ---- caller-arena carve (mirror wz_take / wz_bind) ---------------- */

static uint32_t *qwz_take(uint32_t *base, size_t words, size_t *cur, size_t cnt)
{
    uint32_t *p;
    assert(base != NULL && cur != NULL);
    assert(*cur <= words);
    if (cnt > words || *cur > words - cnt) { return NULL; }
    p = base + *cur;
    *cur += cnt;
    return p;
}

static srmech_status_t qwz_bind(srmech_bigint_t *b, uint32_t *base, size_t words,
                                size_t *cur, uint32_t cap)
{
    uint32_t *limbs = qwz_take(base, words, cur, cap);
    assert(b != NULL && cap > 0u);
    assert(base != NULL || words == 0u);
    if (limbs == NULL) { return SRMECH_ERR_OVERFLOW; }
    b->limbs = limbs;
    b->cap = cap;
    b->n = 0u;
    b->sign = 0;
    return SRMECH_OK;
}

static size_t qwz_hdr_words(void)
{
    size_t hw = (sizeof(srmech_bigint_t) + sizeof(uint32_t) - 1u)
                / sizeof(uint32_t);
    assert(sizeof(srmech_bigint_t) > 0u);
    assert(hw >= 1u);
    return hw;
}

static srmech_status_t qwz_ctx_init(qwz_ctx_t *c, uint32_t cap, void *ws,
                                    size_t ws_len)
{
    uint32_t *base = (uint32_t *)ws;
    size_t words = ws_len / sizeof(uint32_t);
    size_t carrier_words = (size_t)cap * (size_t)QWZ_N_CARRIERS;
    size_t scratch_words = (size_t)cap * 8u + 256u;
    srmech_status_t st = SRMECH_OK;
    assert(c != NULL);
    assert((uintptr_t)ws % sizeof(uint32_t) == 0u || ws == NULL);
    c->cap = cap;
    if (words < carrier_words + scratch_words) { return SRMECH_ERR_OVERFLOW; }
    c->pool = base;
    c->pool_words = words - scratch_words;
    c->pool_cur = 0u;
    st |= qwz_bind(&c->qa_n, base, c->pool_words, &c->pool_cur, cap);
    st |= qwz_bind(&c->qa_d, base, c->pool_words, &c->pool_cur, cap);
    st |= qwz_bind(&c->qb_n, base, c->pool_words, &c->pool_cur, cap);
    st |= qwz_bind(&c->qb_d, base, c->pool_words, &c->pool_cur, cap);
    st |= qwz_bind(&c->t0, base, c->pool_words, &c->pool_cur, cap);
    st |= qwz_bind(&c->t1, base, c->pool_words, &c->pool_cur, cap);
    st |= qwz_bind(&c->g, base, c->pool_words, &c->pool_cur, cap);
    st |= qwz_bind(&c->rem, base, c->pool_words, &c->pool_cur, cap);
    st |= qwz_bind(&c->rs0, base, c->pool_words, &c->pool_cur, cap);
    st |= qwz_bind(&c->rs1, base, c->pool_words, &c->pool_cur, cap);
    st |= qwz_bind(&c->z0, base, c->pool_words, &c->pool_cur, cap);
    st |= qwz_bind(&c->z1, base, c->pool_words, &c->pool_cur, cap);
    if (st != SRMECH_OK) { return SRMECH_ERR_OVERFLOW; }
    st = srmech_bigint_set_i64(&c->z0, 0);
    if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&c->z1, 1); }
    if (st != SRMECH_OK) { return st; }
    c->scratch = (void *)(base + (words - scratch_words));
    c->scratch_len = scratch_words * sizeof(uint32_t);
    assert(c->pool_cur <= c->pool_words);
    return SRMECH_OK;
}

/* ---- exact-Q scalar helpers (mirror wz) --------------------------- */

static srmech_status_t qwz_q_reduce(qwz_ctx_t *c, srmech_bigint_t *num,
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

static srmech_status_t qwz_q_add(qwz_ctx_t *c, srmech_bigint_t *on,
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
    return qwz_q_reduce(c, on, od);
}

static srmech_status_t qwz_q_mul(qwz_ctx_t *c, srmech_bigint_t *on,
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
    return qwz_q_reduce(c, on, od);
}

/* ---- q-poly (Q[q]) carve + ops ------------------------------------ */

static size_t qwz_trim(const srmech_bigint_t *nums, size_t n)
{
    size_t k = n;
    assert(nums != NULL || n == 0u);
    while (k > 0u && srmech_bigint_is_zero(&nums[k - 1u])) { k--; }
    assert(k <= n);
    return k;
}

static srmech_status_t qwz_qp_alloc(qwz_ctx_t *c, qwz_qpoly_t *p, size_t terms)
{
    size_t hw = qwz_hdr_words(), k;
    uint32_t *hn, *hd;
    srmech_status_t st;
    assert(c != NULL && p != NULL && terms > 0u);
    assert(hw >= 1u);
    hn = qwz_take(c->pool, c->pool_words, &c->pool_cur, hw * terms);
    hd = qwz_take(c->pool, c->pool_words, &c->pool_cur, hw * terms);
    if (hn == NULL || hd == NULL) { return SRMECH_ERR_OVERFLOW; }
    p->n = (srmech_bigint_t *)(void *)hn;
    p->d = (srmech_bigint_t *)(void *)hd;
    p->len = 0u;
    p->cap_terms = terms;
    for (k = 0u; k < terms; k++) {
        st = qwz_bind(&p->n[k], c->pool, c->pool_words, &c->pool_cur, c->cap);
        if (st == SRMECH_OK) { st = qwz_bind(&p->d[k], c->pool, c->pool_words,
                                             &c->pool_cur, c->cap); }
        if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&p->n[k], 0); }
        if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&p->d[k], 1); }
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

static srmech_status_t qwz_qp_zero(qwz_qpoly_t *p)
{
    assert(p != NULL);
    assert(p->len <= p->cap_terms);
    p->len = 0u;
    return SRMECH_OK;
}

static srmech_status_t qwz_qp_copy(qwz_qpoly_t *dst, const qwz_qpoly_t *src)
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

/* out = a +/- b (per-q-degree Q add/sub over the union q-window). */
static srmech_status_t qwz_qp_addsub(qwz_ctx_t *c, qwz_qpoly_t *out,
                                     const qwz_qpoly_t *a, const qwz_qpoly_t *b,
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
        st = qwz_q_add(c, &out->n[k], &out->d[k], an, ad, bn, bd, sub);
        if (st != SRMECH_OK) { return st; }
    }
    out->len = qwz_trim(out->n, m);
    return SRMECH_OK;
}

/* out = a * b (q-convolution over Q[q]). */
static srmech_status_t qwz_qp_mul(qwz_ctx_t *c, qwz_qpoly_t *out,
                                  const qwz_qpoly_t *a, const qwz_qpoly_t *b)
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
            st = qwz_q_mul(c, &c->qa_n, &c->qa_d, &a->n[i], &a->d[i],
                           &b->n[j], &b->d[j]);
            if (st == SRMECH_OK) { st = srmech_bigint_copy(&c->qb_n, &out->n[i + j]); }
            if (st == SRMECH_OK) { st = srmech_bigint_copy(&c->qb_d, &out->d[i + j]); }
            if (st == SRMECH_OK) { st = qwz_q_add(c, &out->n[i + j], &out->d[i + j],
                                                  &c->qb_n, &c->qb_d,
                                                  &c->qa_n, &c->qa_d, 0); }
            if (st != SRMECH_OK) { return st; }
        }
    }
    out->len = qwz_trim(out->n, m);
    return SRMECH_OK;
}

/* out = q^s * a : shift the Q[q] q-degree run UP by s (prepend s zero q-degrees). */
static srmech_status_t qwz_qp_qshift(qwz_qpoly_t *out, const qwz_qpoly_t *a,
                                     size_t s)
{
    size_t k;
    srmech_status_t st;
    assert(out != NULL && a != NULL);
    if (a->len == 0u) { out->len = 0u; return SRMECH_OK; }
    assert(out->cap_terms >= a->len + s);
    for (k = 0u; k < s; k++) {
        st = srmech_bigint_set_i64(&out->n[k], 0);
        if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&out->d[k], 1); }
        if (st != SRMECH_OK) { return st; }
    }
    for (k = 0u; k < a->len; k++) {
        st = srmech_bigint_copy(&out->n[k + s], &a->n[k]);
        if (st == SRMECH_OK) { st = srmech_bigint_copy(&out->d[k + s], &a->d[k]); }
        if (st != SRMECH_OK) { return st; }
    }
    out->len = a->len + s;
    return SRMECH_OK;
}

/* exact equality of two trimmed Q[q] q-polys. */
static int qwz_qp_eq(const qwz_qpoly_t *a, const qwz_qpoly_t *b)
{
    size_t k;
    assert(a != NULL && b != NULL);
    assert(a->len <= a->cap_terms && b->len <= b->cap_terms);
    if (a->len != b->len) { return 0; }
    for (k = 0u; k < a->len; k++) {
        if (srmech_bigint_cmp(&a->n[k], &b->n[k]) != 0) { return 0; }
        if (srmech_bigint_cmp(&a->d[k], &b->d[k]) != 0) { return 0; }
    }
    return 1;
}

/* ---- QPoly-in-X carve + ops --------------------------------------- */

static srmech_status_t qwz_xp_alloc(qwz_ctx_t *c, qwz_xpoly_t *p, size_t x_terms,
                                    size_t n_terms)
{
    size_t i;
    uint32_t *hx;
    srmech_status_t st;
    assert(c != NULL && p != NULL && x_terms > 0u && n_terms > 0u);
    assert(c->pool != NULL || c->pool_words == 0u);
    hx = qwz_take(c->pool, c->pool_words, &c->pool_cur,
                  ((sizeof(qwz_qpoly_t) + sizeof(uint32_t) - 1u) / sizeof(uint32_t))
                  * x_terms);
    if (hx == NULL) { return SRMECH_ERR_OVERFLOW; }
    p->xc = (qwz_qpoly_t *)(void *)hx;
    p->x_low = 0;
    p->x_cells = 0u;
    p->x_cap = x_terms;
    for (i = 0u; i < x_terms; i++) {
        st = qwz_qp_alloc(c, &p->xc[i], n_terms);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* drop trailing-zero (high-X) AND leading-zero (low-X) cells; renormalize x_low. */
static void qwz_xp_trim(qwz_xpoly_t *p)
{
    size_t lo = 0u;
    assert(p != NULL);
    assert(p->x_cells <= p->x_cap);
    while (p->x_cells > 0u && p->xc[p->x_cells - 1u].len == 0u) { p->x_cells--; }
    while (lo < p->x_cells && p->xc[lo].len == 0u) { lo++; }
    if (lo > 0u && lo < p->x_cells) {
        size_t i, keep = p->x_cells - lo;
        for (i = 0u; i < keep; i++) {
            qwz_qpoly_t tmp = p->xc[i];
            p->xc[i] = p->xc[i + lo];
            p->xc[i + lo] = tmp;
        }
        p->x_low += (int64_t)lo;
        p->x_cells = keep;
    } else if (lo >= p->x_cells) {
        p->x_cells = 0u;
        p->x_low = 0;
    }
}

/* dst = src (a QPoly-in-X copy: per-X-cell Q[q] copy + x_low). */
static srmech_status_t qwz_xp_copy(qwz_xpoly_t *dst, const qwz_xpoly_t *src)
{
    size_t i;
    srmech_status_t st;
    assert(dst != NULL && src != NULL);
    assert(dst->x_cap >= src->x_cells);
    dst->x_low = src->x_low;
    for (i = 0u; i < src->x_cells; i++) {
        st = qwz_qp_copy(&dst->xc[i], &src->xc[i]);
        if (st != SRMECH_OK) { return st; }
    }
    dst->x_cells = src->x_cells;
    return SRMECH_OK;
}

/* out = a +/- b over the union X-window (per-X-cell Q[q] add/sub). out is distinct. */
static srmech_status_t qwz_xp_addsub(qwz_ctx_t *c, qwz_xpoly_t *out,
                                     const qwz_xpoly_t *a, const qwz_xpoly_t *b,
                                     int sub)
{
    int64_t lo, hi, e;
    size_t idx;
    srmech_status_t st;
    qwz_qpoly_t zp = {0};
    assert(c != NULL && out != NULL && a != NULL && b != NULL);
    if (a->x_cells == 0u && b->x_cells == 0u) { out->x_cells = 0u; out->x_low = 0;
                                                return SRMECH_OK; }
    lo = a->x_low; hi = a->x_low + (int64_t)a->x_cells - 1;
    if (b->x_cells > 0u) {
        if (a->x_cells == 0u || b->x_low < lo) { lo = b->x_low; }
        if (a->x_cells == 0u || b->x_low + (int64_t)b->x_cells - 1 > hi) {
            hi = b->x_low + (int64_t)b->x_cells - 1;
        }
    }
    assert(out->x_cap >= (size_t)(hi - lo + 1));
    out->x_low = lo;
    idx = 0u;
    for (e = lo; e <= hi; e++) {
        const qwz_qpoly_t *ap = &zp, *bp = &zp;
        if (a->x_cells > 0u && e >= a->x_low
            && e < a->x_low + (int64_t)a->x_cells) { ap = &a->xc[e - a->x_low]; }
        if (b->x_cells > 0u && e >= b->x_low
            && e < b->x_low + (int64_t)b->x_cells) { bp = &b->xc[e - b->x_low]; }
        st = qwz_qp_addsub(c, &out->xc[idx], ap, bp, sub);
        if (st != SRMECH_OK) { return st; }
        idx++;
    }
    out->x_cells = idx;
    qwz_xp_trim(out);
    return SRMECH_OK;
}

/* out = a * b (X-convolution; result x_low = a.x_low + b.x_low). acc/prod q-scratch. */
static srmech_status_t qwz_xp_mul(qwz_ctx_t *c, qwz_xpoly_t *out,
                                  const qwz_xpoly_t *a, const qwz_xpoly_t *b,
                                  qwz_qpoly_t *acc, qwz_qpoly_t *prod)
{
    size_t i, j, m;
    srmech_status_t st;
    assert(c != NULL && out != NULL && a != NULL && b != NULL);
    assert(acc != NULL && prod != NULL);
    if (a->x_cells == 0u || b->x_cells == 0u) { out->x_cells = 0u; out->x_low = 0;
                                                return SRMECH_OK; }
    m = a->x_cells + b->x_cells - 1u;
    assert(out->x_cap >= m);
    for (i = 0u; i < m; i++) { (void)qwz_qp_zero(&out->xc[i]); }
    for (i = 0u; i < a->x_cells; i++) {
        if (a->xc[i].len == 0u) { continue; }
        for (j = 0u; j < b->x_cells; j++) {
            if (b->xc[j].len == 0u) { continue; }
            st = qwz_qp_mul(c, prod, &a->xc[i], &b->xc[j]);
            if (st == SRMECH_OK) { st = qwz_qp_copy(acc, &out->xc[i + j]); }
            if (st == SRMECH_OK) { st = qwz_qp_addsub(c, &out->xc[i + j],
                                                      acc, prod, 0); }
            if (st != SRMECH_OK) { return st; }
        }
    }
    out->x_low = a->x_low + b->x_low;
    out->x_cells = m;
    qwz_xp_trim(out);
    return SRMECH_OK;
}

/* exact equality of two trimmed QPoly-in-X (same x_low + per-cell Q[q] equality). */
static int qwz_xp_eq(const qwz_xpoly_t *a, const qwz_xpoly_t *b)
{
    size_t i;
    assert(a != NULL && b != NULL);
    assert(a->x_cells <= a->x_cap && b->x_cells <= b->x_cap);
    if (a->x_cells != b->x_cells) { return 0; }
    if (a->x_cells == 0u) { return 1; }
    if (a->x_low != b->x_low) { return 0; }
    for (i = 0u; i < a->x_cells; i++) {
        if (!qwz_qp_eq(&a->xc[i], &b->xc[i])) { return 0; }
    }
    return 1;
}

/* ---- QBiPoly(X,Y) carve + ops ------------------------------------- */

static srmech_status_t qwz_qb_alloc(qwz_ctx_t *c, qwz_qbipoly_t *b, size_t y_terms,
                                    size_t x_terms, size_t n_terms)
{
    size_t dy;
    uint32_t *hy;
    srmech_status_t st;
    assert(c != NULL && b != NULL && y_terms > 0u && x_terms > 0u && n_terms > 0u);
    assert(c->pool != NULL || c->pool_words == 0u);
    hy = qwz_take(c->pool, c->pool_words, &c->pool_cur,
                  ((sizeof(qwz_xpoly_t) + sizeof(uint32_t) - 1u) / sizeof(uint32_t))
                  * y_terms);
    if (hy == NULL) { return SRMECH_ERR_OVERFLOW; }
    b->yc = (qwz_xpoly_t *)(void *)hy;
    b->ylen = 0u;
    b->y_cap = y_terms;
    for (dy = 0u; dy < y_terms; dy++) {
        st = qwz_xp_alloc(c, &b->yc[dy], x_terms, n_terms);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

static void qwz_qb_trim(qwz_qbipoly_t *b)
{
    assert(b != NULL);
    assert(b->ylen <= b->y_cap);
    while (b->ylen > 0u && b->yc[b->ylen - 1u].x_cells == 0u) { b->ylen--; }
}

/* out = a +/- b (per-Y-cell QPoly-in-X add/sub over the union Y-window). */
static srmech_status_t qwz_qb_addsub(qwz_ctx_t *c, qwz_qbipoly_t *out,
                                     const qwz_qbipoly_t *a, const qwz_qbipoly_t *b,
                                     int sub)
{
    size_t dy, m = (a->ylen > b->ylen) ? a->ylen : b->ylen;
    qwz_xpoly_t zx = {0};
    srmech_status_t st;
    assert(c != NULL && out != NULL && a != NULL && b != NULL);
    assert(out->y_cap >= m);
    for (dy = 0u; dy < m; dy++) {
        const qwz_xpoly_t *ap = (dy < a->ylen) ? &a->yc[dy] : &zx;
        const qwz_xpoly_t *bp = (dy < b->ylen) ? &b->yc[dy] : &zx;
        st = qwz_xp_addsub(c, &out->yc[dy], ap, bp, sub);
        if (st != SRMECH_OK) { return st; }
    }
    out->ylen = m;
    qwz_qb_trim(out);
    return SRMECH_OK;
}

/* out = a * b (Y-convolution; each product an X-poly mul). acc/prod X-poly scratch;
 * qa/qp Q[q] scratch (handed down to the X-poly mul). */
static srmech_status_t qwz_qb_mul(qwz_ctx_t *c, qwz_qbipoly_t *out,
                                  const qwz_qbipoly_t *a, const qwz_qbipoly_t *b,
                                  qwz_xpoly_t *acc, qwz_xpoly_t *prod,
                                  qwz_qpoly_t *qa, qwz_qpoly_t *qp)
{
    size_t i, j, m, dy;
    srmech_status_t st;
    assert(c != NULL && out != NULL && a != NULL && b != NULL);
    assert(acc != NULL && prod != NULL && qa != NULL && qp != NULL);
    if (a->ylen == 0u || b->ylen == 0u) { out->ylen = 0u; return SRMECH_OK; }
    m = a->ylen + b->ylen - 1u;
    assert(out->y_cap >= m);
    for (dy = 0u; dy < m; dy++) { out->yc[dy].x_cells = 0u; out->yc[dy].x_low = 0; }
    for (i = 0u; i < a->ylen; i++) {
        if (a->yc[i].x_cells == 0u) { continue; }
        for (j = 0u; j < b->ylen; j++) {
            if (b->yc[j].x_cells == 0u) { continue; }
            st = qwz_xp_mul(c, prod, &a->yc[i], &b->yc[j], qa, qp);
            if (st == SRMECH_OK) { st = qwz_xp_addsub(c, acc, &out->yc[i + j],
                                                      prod, 0); }       /* acc=out+prod */
            if (st == SRMECH_OK) { st = qwz_xp_copy(&out->yc[i + j], acc); }
            if (st != SRMECH_OK) { return st; }
        }
    }
    out->ylen = m;
    qwz_qb_trim(out);
    return SRMECH_OK;
}

/* out = sigma_y(a) : Y -> q*Y, the Y^dy cell c_dy(X)*Y^dy -> (q^dy * c_dy(X))*Y^dy.
 * Multiplying a Q[q] cell by q^dy shifts every q-coefficient run UP by dy. The
 * Y-window is UNCHANGED. out is distinct from a. */
static srmech_status_t qwz_qb_qshift_y(qwz_qbipoly_t *out, const qwz_qbipoly_t *a)
{
    size_t dy, i;
    srmech_status_t st;
    assert(out != NULL && a != NULL);
    assert(out->y_cap >= a->ylen);
    for (dy = 0u; dy < a->ylen; dy++) {
        const qwz_xpoly_t *src = &a->yc[dy];
        qwz_xpoly_t *dst = &out->yc[dy];
        assert(dst->x_cap >= src->x_cells);
        dst->x_low = src->x_low;
        for (i = 0u; i < src->x_cells; i++) {
            st = qwz_qp_qshift(&dst->xc[i], &src->xc[i], dy);
            if (st != SRMECH_OK) { return st; }
        }
        dst->x_cells = src->x_cells;
        qwz_xp_trim(dst);
    }
    out->ylen = a->ylen;
    qwz_qb_trim(out);
    return SRMECH_OK;
}

/* exact equality of two trimmed exact-Q[q] QBiPoly. */
static int qwz_qb_eq(const qwz_qbipoly_t *a, const qwz_qbipoly_t *b)
{
    size_t dy;
    assert(a != NULL && b != NULL);
    assert(a->ylen <= a->y_cap && b->ylen <= b->y_cap);
    if (a->ylen != b->ylen) { return 0; }
    for (dy = 0u; dy < a->ylen; dy++) {
        if (!qwz_xp_eq(&a->yc[dy], &b->yc[dy])) { return 0; }
    }
    return 1;
}

/* ===================================================================
 * The VERIFY orchestration: build lhs + rhs of the cleared q-WZ identity and compare.
 * =================================================================== */

/* The working-QBiPoly roster: the six inputs + the q-shift / product scratch. */
typedef struct qwz_solve {
    qwz_qbipoly_t an, ad, bn, bd, xn, xd;   /* the six inputs                      */
    qwz_qbipoly_t xn1, xd1;                  /* sigma_y(Xn), sigma_y(Xd)            */
    qwz_qbipoly_t lhs, rhs;                  /* the two cleared sides               */
    qwz_qbipoly_t t0, t1, t2;                /* general product scratch             */
    qwz_xpoly_t   xacc, xprod;               /* X-poly mul scratch                  */
    qwz_qpoly_t   qa, qp;                    /* Q[q] mul scratch                    */
    size_t        yt, xt, nt;
} qwz_solve_t;

/* Load a flat QBiPoly bridge (n/d q-runs Y-major-then-X, per-(Y,X) qlen[], per-Y
 * xlow[]/xcells[]) into a working QBiPoly. */
static srmech_status_t qwz_load_qb(qwz_qbipoly_t *b, const srmech_bigint_t *cn,
                                   const srmech_bigint_t *cd, const size_t *qlen,
                                   const int64_t *xlow, const size_t *xcells,
                                   size_t ycells)
{
    size_t dy, xi, qi, cell = 0u, idx = 0u;
    srmech_status_t st;
    assert(b != NULL);
    assert(b->y_cap >= ycells);
    for (dy = 0u; dy < ycells; dy++) {
        qwz_xpoly_t *yc = &b->yc[dy];
        size_t xn = xcells[dy];
        assert(yc->x_cap >= xn);
        yc->x_low = xlow[dy];
        for (xi = 0u; xi < xn; xi++) {
            size_t ql = qlen[cell];
            qwz_qpoly_t *xc = &yc->xc[xi];
            assert(xc->cap_terms >= ql);
            for (qi = 0u; qi < ql; qi++) {
                st = srmech_bigint_copy(&xc->n[qi], &cn[idx + qi]);
                if (st == SRMECH_OK) { st = srmech_bigint_copy(&xc->d[qi],
                                                               &cd[idx + qi]); }
                if (st != SRMECH_OK) { return st; }
            }
            xc->len = qwz_trim(xc->n, ql);
            idx += ql;
            cell++;
        }
        yc->x_cells = xn;
        qwz_xp_trim(yc);
    }
    b->ylen = ycells;
    qwz_qb_trim(b);
    return SRMECH_OK;
}

static srmech_status_t qwz_solve_alloc(qwz_ctx_t *c, qwz_solve_t *s, size_t yt,
                                       size_t xt, size_t nt)
{
    srmech_status_t st = SRMECH_OK;
    assert(c != NULL && s != NULL && yt > 0u && xt > 0u && nt > 0u);
    assert(c->cap > 0u);
    s->yt = yt; s->xt = xt; s->nt = nt;
    st |= qwz_qb_alloc(c, &s->an, yt, xt, nt); st |= qwz_qb_alloc(c, &s->ad, yt, xt, nt);
    st |= qwz_qb_alloc(c, &s->bn, yt, xt, nt); st |= qwz_qb_alloc(c, &s->bd, yt, xt, nt);
    st |= qwz_qb_alloc(c, &s->xn, yt, xt, nt); st |= qwz_qb_alloc(c, &s->xd, yt, xt, nt);
    st |= qwz_qb_alloc(c, &s->xn1, yt, xt, nt); st |= qwz_qb_alloc(c, &s->xd1, yt, xt, nt);
    st |= qwz_qb_alloc(c, &s->lhs, yt, xt, nt); st |= qwz_qb_alloc(c, &s->rhs, yt, xt, nt);
    st |= qwz_qb_alloc(c, &s->t0, yt, xt, nt); st |= qwz_qb_alloc(c, &s->t1, yt, xt, nt);
    st |= qwz_qb_alloc(c, &s->t2, yt, xt, nt);
    st |= qwz_xp_alloc(c, &s->xacc, xt, nt); st |= qwz_xp_alloc(c, &s->xprod, xt, nt);
    st |= qwz_qp_alloc(c, &s->qa, nt); st |= qwz_qp_alloc(c, &s->qp, nt);
    if (st != SRMECH_OK) { return SRMECH_ERR_OVERFLOW; }
    return SRMECH_OK;
}

/* Build lhs = (An - Ad) * (sigma_y(Xd) * Bd * Xd). */
static srmech_status_t qwz_build_lhs(qwz_ctx_t *c, qwz_solve_t *s)
{
    srmech_status_t st;
    assert(c != NULL && s != NULL);
    assert(s->an.y_cap >= 1u);
    st = qwz_qb_addsub(c, &s->t0, &s->an, &s->ad, 1);                 /* An - Ad      */
    if (st == SRMECH_OK) { st = qwz_qb_mul(c, &s->t1, &s->xd1, &s->bd,
                                           &s->xacc, &s->xprod, &s->qa, &s->qp); }
    if (st == SRMECH_OK) { st = qwz_qb_mul(c, &s->t2, &s->t1, &s->xd,
                                           &s->xacc, &s->xprod, &s->qa, &s->qp); }
    if (st == SRMECH_OK) { st = qwz_qb_mul(c, &s->lhs, &s->t0, &s->t2,
                                           &s->xacc, &s->xprod, &s->qa, &s->qp); }
    return st;
}

/* Build rhs = (sigma_y(Xn) * Bn * Xd - Xn * sigma_y(Xd) * Bd) * Ad. */
static srmech_status_t qwz_build_rhs(qwz_ctx_t *c, qwz_solve_t *s)
{
    srmech_status_t st;
    assert(c != NULL && s != NULL);
    assert(s->ad.y_cap >= 1u);
    st = qwz_qb_mul(c, &s->t0, &s->xn1, &s->bn, &s->xacc, &s->xprod, &s->qa, &s->qp);
    if (st == SRMECH_OK) { st = qwz_qb_mul(c, &s->t1, &s->t0, &s->xd,
                                           &s->xacc, &s->xprod, &s->qa, &s->qp); }
    if (st == SRMECH_OK) { st = qwz_qb_mul(c, &s->t0, &s->xn, &s->xd1,
                                           &s->xacc, &s->xprod, &s->qa, &s->qp); }
    if (st == SRMECH_OK) { st = qwz_qb_mul(c, &s->t2, &s->t0, &s->bd,
                                           &s->xacc, &s->xprod, &s->qa, &s->qp); }
    if (st == SRMECH_OK) { st = qwz_qb_addsub(c, &s->t0, &s->t1, &s->t2, 1); }
    if (st == SRMECH_OK) { st = qwz_qb_mul(c, &s->rhs, &s->t0, &s->ad,
                                           &s->xacc, &s->xprod, &s->qa, &s->qp); }
    return st;
}

/* ---- input estimate + arena bounds -------------------------------- */

static size_t qwz_input_limbs(const srmech_bigint_t *cn, size_t total)
{
    size_t k, cl = 1u;
    assert(cn != NULL || total == 0u);
    assert(cl >= 1u);
    for (k = 0u; k < total; k++) { if (cn[k].n > cl) { cl = cn[k].n; } }
    return cl;
}

static size_t qwz_flat_total(const size_t *qlen, const size_t *xcells, size_t ycells)
{
    size_t dy, xi, cell = 0u, total = 0u;
    assert(qlen != NULL || ycells == 0u);
    assert(xcells != NULL || ycells == 0u);
    for (dy = 0u; dy < ycells; dy++) {
        for (xi = 0u; xi < xcells[dy]; xi++) { total += qlen[cell]; cell++; }
    }
    return total;
}

static size_t qwz_cap_for(size_t coeff_limbs, size_t degree)
{
    size_t cl = (coeff_limbs == 0u) ? 1u : coeff_limbs;
    size_t dg = (degree == 0u) ? 1u : degree;
    /* The cleared identity is a 4-fold bivariate-q product of the inputs; an envelope
     * dominating the worst intermediate (coeff growth ~ 4x input bits + the bivariate-q
     * convolution carry). A huge input that exceeds this returns OVERFLOW -> the Python
     * pure-Q compare (the standalone-honor). */
    size_t step = cl * 6u * (dg + 2u) + 8u;
    size_t cap = step * 2u + cl * 4u + 48u;
    assert(cap >= step);
    assert(cap >= cl);
    return cap;
}

size_t srmech_q_wz_verify_out_cap(size_t coeff_limbs, size_t degree)
{
    size_t cap = qwz_cap_for(coeff_limbs, degree);
    assert(cap >= 2u);
    assert(cap >= coeff_limbs);
    return cap;
}

/* per-dimension term count the working QBiPolys carry in one variable. The heaviest
 * intermediate is the 4-fold product, so a dimension of input extent `dim_cells` grows
 * to ~4x; bound generously per-variable (NOT a shared max -> no cubic blow-up). */
static size_t qwz_dim_terms(size_t dim_cells)
{
    size_t dc = (dim_cells == 0u) ? 1u : dim_cells;
    size_t terms = 4u * dc + 6u;
    assert(terms >= dc);
    assert(terms >= 6u);
    return terms;
}

/* The arena estimate for the working roster, given the per-dimension term counts yt
 * (Y), xt (X), nt (q) and the per-coefficient limb cap. Shared by ws_bound (which
 * passes a single `degree` for all three) and the public entry's internal sizing
 * cross-check. */
static size_t qwz_arena_words(size_t yt, size_t xt, size_t nt, size_t cap)
{
    size_t hw = qwz_hdr_words();
    assert(yt > 0u && xt > 0u && nt > 0u);
    assert(cap > 0u);
    size_t qbipolys = 14u;                           /* the qwz_solve roster + pad  */
    size_t qp_hdr = ((sizeof(qwz_qpoly_t) + sizeof(uint32_t) - 1u) / sizeof(uint32_t));
    size_t xp_hdr = ((sizeof(qwz_xpoly_t) + sizeof(uint32_t) - 1u) / sizeof(uint32_t));
    size_t per_qp = 2u * hw * nt + 2u * nt * cap;    /* one Q[q] q-poly             */
    size_t per_xp = xp_hdr * xt + xt * (qp_hdr + per_qp);
    size_t per_qb = xp_hdr * yt + yt * per_xp;
    size_t qb_words = per_qb * qbipolys;
    size_t scratch_xp = 2u * per_xp;                 /* xacc, xprod                 */
    size_t scratch_qp = 2u * (qp_hdr + per_qp);      /* qa, qp                      */
    size_t carriers = (size_t)cap * (size_t)QWZ_N_CARRIERS;
    size_t scratch = (size_t)cap * 8u + 256u;
    size_t best = qb_words + scratch_xp + scratch_qp + carriers + scratch + 8192u;
    assert(best >= qb_words);
    return best;
}

size_t srmech_q_wz_verify_ws_bound(size_t coeff_limbs, size_t degree)
{
    size_t dg = (degree == 0u) ? 1u : degree;
    size_t cl = (coeff_limbs == 0u) ? 1u : coeff_limbs;
    size_t cap = qwz_cap_for(cl, dg);
    /* the conservative upper bound: size the X- and Y-dimensions to the single `degree`
     * the Python bridge passes (the max over the X-span / Y-degree / q-degree), and the
     * q-dimension to 2*degree (the internal alloc sizes nt off (qd + yd) <= 2*deg to
     * absorb the sigma_y shift). The internal per-dimension sizing is always <= this. */
    size_t txy = qwz_dim_terms(dg);
    size_t tq = qwz_dim_terms(2u * dg);
    size_t best = qwz_arena_words(txy, txy, tq, cap);
    assert(dg >= 1u && cap >= 2u);
    assert(tq >= txy && best >= cap);
    return best * sizeof(uint32_t);
}

/* ---- per-input degree estimate (per-dimension: Y-deg, X-span, q-deg) ---------
 *
 * The cleared identity is a 4-fold product, so the result's Y-degree / X-span /
 * q-degree each grow ~4x the max input degree in THAT variable -- but the three
 * dimensions are INDEPENDENT, so sizing each tightly (not a single shared `deg`)
 * keeps the working QBiPoly carriers from a cubic blow-up (the fiber is bounded per
 * variable; sizing the cube to the max-over-all-variables is the missed fiber). */

static void qwz_in_dims(const size_t *qlen, const size_t *xcells, size_t ycells,
                        size_t *yd, size_t *xs, size_t *qd)
{
    size_t dy, xi, cell = 0u, y = ycells, x = 0u, q = 0u;
    assert(qlen != NULL || ycells == 0u);
    assert(xcells != NULL || ycells == 0u);
    for (dy = 0u; dy < ycells; dy++) {
        if (xcells[dy] > x) { x = xcells[dy]; }
        for (xi = 0u; xi < xcells[dy]; xi++) { if (qlen[cell] > q) { q = qlen[cell]; }
                                               cell++; }
    }
    *yd = y; *xs = x; *qd = q;
}

static void qwz_fold_dims(const size_t *qlen, const size_t *xcells, size_t ycells,
                          size_t *yd, size_t *xs, size_t *qd)
{
    size_t y, x, q;
    assert(yd != NULL && xs != NULL && qd != NULL);
    assert(qlen != NULL || ycells == 0u);
    qwz_in_dims(qlen, xcells, ycells, &y, &x, &q);
    if (y > *yd) { *yd = y; }
    if (x > *xs) { *xs = x; }
    if (q > *qd) { *qd = q; }
}

/* ---- the public entry --------------------------------------------- */

srmech_status_t srmech_q_wz_verify(
        const srmech_bigint_t *rn_num_n, const srmech_bigint_t *rn_num_d,
        const size_t *rn_num_qlen, const int64_t *rn_num_xlow,
        const size_t *rn_num_xcells, size_t rn_num_ycells,
        const srmech_bigint_t *rn_den_n, const srmech_bigint_t *rn_den_d,
        const size_t *rn_den_qlen, const int64_t *rn_den_xlow,
        const size_t *rn_den_xcells, size_t rn_den_ycells,
        const srmech_bigint_t *rk_num_n, const srmech_bigint_t *rk_num_d,
        const size_t *rk_num_qlen, const int64_t *rk_num_xlow,
        const size_t *rk_num_xcells, size_t rk_num_ycells,
        const srmech_bigint_t *rk_den_n, const srmech_bigint_t *rk_den_d,
        const size_t *rk_den_qlen, const int64_t *rk_den_xlow,
        const size_t *rk_den_xcells, size_t rk_den_ycells,
        const srmech_bigint_t *cert_num_n, const srmech_bigint_t *cert_num_d,
        const size_t *cert_num_qlen, const int64_t *cert_num_xlow,
        const size_t *cert_num_xcells, size_t cert_num_ycells,
        const srmech_bigint_t *cert_den_n, const srmech_bigint_t *cert_den_d,
        const size_t *cert_den_qlen, const int64_t *cert_den_xlow,
        const size_t *cert_den_xcells, size_t cert_den_ycells,
        int *out_equal, void *ws, size_t ws_len)
{
    qwz_ctx_t c;
    qwz_solve_t s = {0};
    uint32_t cap;
    size_t cl, deg, v, yt, xt, nt;
    size_t yd = 0u, xs = 0u, qd = 0u;
    srmech_status_t st;
    assert(out_equal != NULL);
    assert(rn_num_n != NULL && cert_num_n != NULL);
    if (out_equal == NULL) { return SRMECH_ERR_NULL_ARG; }
    if (rn_num_n == NULL || rn_den_n == NULL || rk_num_n == NULL
        || rk_den_n == NULL || cert_num_n == NULL || cert_den_n == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    *out_equal = 0;
    if (rn_den_ycells == 0u || rk_den_ycells == 0u || cert_den_ycells == 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    /* per-dimension degree envelopes (Y-degree / X-span / q-degree), each sized
     * independently so the working carriers do NOT blow up cubically. */
    qwz_fold_dims(rn_num_qlen, rn_num_xcells, rn_num_ycells, &yd, &xs, &qd);
    qwz_fold_dims(rn_den_qlen, rn_den_xcells, rn_den_ycells, &yd, &xs, &qd);
    qwz_fold_dims(rk_num_qlen, rk_num_xcells, rk_num_ycells, &yd, &xs, &qd);
    qwz_fold_dims(rk_den_qlen, rk_den_xcells, rk_den_ycells, &yd, &xs, &qd);
    qwz_fold_dims(cert_num_qlen, cert_num_xcells, cert_num_ycells, &yd, &xs, &qd);
    qwz_fold_dims(cert_den_qlen, cert_den_xcells, cert_den_ycells, &yd, &xs, &qd);
    deg = yd; if (xs > deg) { deg = xs; } if (qd > deg) { deg = qd; }
    if (deg == 0u) { deg = 1u; }
    if (deg > QWZ_MAX_DEG) { return SRMECH_ERR_BAD_INPUT; }
    cl = qwz_input_limbs(rn_num_n,
                         qwz_flat_total(rn_num_qlen, rn_num_xcells, rn_num_ycells));
    v = qwz_input_limbs(cert_num_n,
                        qwz_flat_total(cert_num_qlen, cert_num_xcells, cert_num_ycells));
    if (v > cl) { cl = v; }
    v = qwz_input_limbs(rk_den_n,
                        qwz_flat_total(rk_den_qlen, rk_den_xcells, rk_den_ycells));
    if (v > cl) { cl = v; }
    cap = (uint32_t)qwz_cap_for(cl, deg);
    st = qwz_ctx_init(&c, cap, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    /* the TIGHT per-dimension term counts (always <= the ws_bound's conservative
     * all-dims-at-`deg` sizing, so the caller arena from ws_bound always suffices).
     * The q-dimension also absorbs the sigma_y shift, which adds up to the Y-degree
     * to a cell's q-run BEFORE the 4-fold product -> size nt off (qd + yd). */
    yt = qwz_dim_terms(yd);
    xt = qwz_dim_terms(xs);
    nt = qwz_dim_terms(qd + yd);
    st = qwz_solve_alloc(&c, &s, yt, xt, nt);
    if (st != SRMECH_OK) { return st; }
    st = qwz_load_qb(&s.an, rn_num_n, rn_num_d, rn_num_qlen, rn_num_xlow,
                     rn_num_xcells, rn_num_ycells);
    if (st == SRMECH_OK) { st = qwz_load_qb(&s.ad, rn_den_n, rn_den_d, rn_den_qlen,
                                            rn_den_xlow, rn_den_xcells, rn_den_ycells); }
    if (st == SRMECH_OK) { st = qwz_load_qb(&s.bn, rk_num_n, rk_num_d, rk_num_qlen,
                                            rk_num_xlow, rk_num_xcells, rk_num_ycells); }
    if (st == SRMECH_OK) { st = qwz_load_qb(&s.bd, rk_den_n, rk_den_d, rk_den_qlen,
                                            rk_den_xlow, rk_den_xcells, rk_den_ycells); }
    if (st == SRMECH_OK) { st = qwz_load_qb(&s.xn, cert_num_n, cert_num_d,
                                            cert_num_qlen, cert_num_xlow,
                                            cert_num_xcells, cert_num_ycells); }
    if (st == SRMECH_OK) { st = qwz_load_qb(&s.xd, cert_den_n, cert_den_d,
                                            cert_den_qlen, cert_den_xlow,
                                            cert_den_xcells, cert_den_ycells); }
    if (st != SRMECH_OK) { return st; }
    /* the Y->qY q-shifts of the certificate. */
    st = qwz_qb_qshift_y(&s.xn1, &s.xn);
    if (st == SRMECH_OK) { st = qwz_qb_qshift_y(&s.xd1, &s.xd); }
    if (st == SRMECH_OK) { st = qwz_build_lhs(&c, &s); }
    if (st == SRMECH_OK) { st = qwz_build_rhs(&c, &s); }
    if (st != SRMECH_OK) { return st; }
    *out_equal = qwz_qb_eq(&s.lhs, &s.rhs);
    return SRMECH_OK;
}
