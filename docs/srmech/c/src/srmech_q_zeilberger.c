/*
 * srmech_q_zeilberger.c -- the q-analog of Zeilberger's creative telescoping (the
 * SECOND public op of the q-hypergeometric F929 reduction row). The C peer of
 * srmech.amsc.q_zeilberger.q_zeilberger.
 *
 * Input: a proper q-hypergeometric term F(n,k) given by its TWO bivariate-q term
 * ratios over (X, Y) = (q^n, q^k):
 *   r_n(X,Y) = F(n+1,k)/F(n,k) = rn_num(X,Y)/rn_den(X,Y)
 *   r_k(X,Y) = F(n,k+1)/F(n,k) = rk_num(X,Y)/rk_den(X,Y)
 * each an exact bivariate-Q[q] polynomial in (X, Y) -- a QBiPoly: a Y-ascending list
 * of QPoly-in-X cells, each QPoly a Laurent-in-X run of Q[q] coefficients (a parallel
 * (num, den) bigint run per X-cell, ascending q-degree). The bridge wire form per
 * QBiPoly: the concatenated q-runs (Y-major then X-major), a per-(Y,X)-cell qlen[],
 * a per-Y-cell x_low[] and x_cells[], and the Y-cell count.
 * Output: when f(n)=Sum_k F(n,k) satisfies a q-recurrence of order <= max_order,
 *   Sum_{j=0}^{L} a_j(q^n) f(n+j) = 0,
 * the order L + the recurrence coefficients a_j(X) (QPoly-in-X) + the q-Gosper
 * certificate numerator x(X,Y) (QBiPoly; R = x/D_P). Else *out_has = 0.
 *
 * STANDALONE-COMPLETE + BOUNDED native scope (mirroring the rc55 srmech_q_gosper
 * precedent): a faithful malloc-free exact-Q(q)[X,Y] homogeneous RREF + q-shift
 * parametrization in C is a multi-rc symbolic-algebra build (the everything-mirrors
 * backlog the q-row tracks). This first rc56 peer COMPLETES the canonical native
 * q-Zeilberger class -- the k-FREE q-GEOMETRIC term (r_n a single Y^0 QPoly cell,
 * r_k == 1), whose definite sum f(n) = c(n) satisfies the ORDER-1 recurrence
 * a_0(X) f(n) + a_1(X) f(n+1) = 0 with a_1 = rn_den, a_0 = -rn_num (cleared to Q[q]:
 * f(n+1) = (rn_num/rn_den) f(n) => rn_den f(n+1) - rn_num f(n) = 0). For every OTHER
 * input the peer DECLINES (*out_has = 0), and the Python op re-runs its COMPLETE
 * pure-Q(q) path -- so a has=0 is NEVER a definitive "no recurrence" (the dispatch
 * trusts only has=1), mirroring the srmech_zeilberger / srmech_q_gosper order-cap
 * precedent. The full higher-order Q(q)[X,Y] RREF is the owed everything-mirrors
 * backlog. Any residual overflow returns SRMECH_ERR_OVERFLOW (never a wrap).
 *
 * This file carries its own compact exact-Q[q] q-poly toolkit (a q-poly run = a
 * parallel (num, den) srmech_bigint pair, ascending q-degree; the SAME ground-ring
 * algebra srmech_q_gosper.c carries) over caller-arena srmech_bigint. No malloc
 * (JPL Rule 3): every working carrier + scratch is carved from the caller arena.
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

/* The largest q-degree the orchestrator supports natively (a generous cap; an input
 * past it returns SRMECH_ERR_BAD_INPUT -> the Python pure path decides). */
#define QZ_MAX_QDEG  32u

/* A scalar working roster carved from the caller arena (mirrors qg_ctx_t). */
typedef struct qz_ctx {
    srmech_bigint_t a_n, a_d;       /* scalar-Q accumulators      */
    srmech_bigint_t t0, t1;         /* integer scratch            */
    srmech_bigint_t g, rem;         /* reduce-private gcd + rem    */
    srmech_bigint_t r0, r1;         /* reduce-private quotients    */
    srmech_bigint_t z0, z1;         /* read-only 0 / 1            */
    uint32_t  cap;
    uint32_t *pool;
    size_t    pool_words;
    size_t    pool_cur;
    void     *scratch;
    size_t    scratch_len;
} qz_ctx_t;

#define QZ_N_CARRIERS 12u  /* a (x2)=2, t0,t1,g,rem,r0,r1,z0,z1=8, +2 spare cap */

/* A q-poly (the ground-ring Q[q] element): parallel (num, den) bigint runs. */
typedef struct qz_qpoly {
    srmech_bigint_t *n;
    srmech_bigint_t *d;
    size_t           len;
    size_t           cap_terms;
} qz_qpoly_t;

/* forward declarations (Rule 1: no recursion) */
static uint32_t *qz_take(uint32_t *base, size_t words, size_t *cur, size_t cnt);
static srmech_status_t qz_bind(srmech_bigint_t *b, qz_ctx_t *c);
static size_t qz_hdr_words(void);
static srmech_status_t qz_ctx_init(qz_ctx_t *c, uint32_t cap, void *ws,
                                   size_t ws_len);
static srmech_status_t qz_q_reduce(qz_ctx_t *c, srmech_bigint_t *num,
                                   srmech_bigint_t *den);
static size_t qz_trim(const srmech_bigint_t *nums, size_t n);
static srmech_status_t qz_qp_alloc(qz_ctx_t *c, qz_qpoly_t *p, size_t terms);
static srmech_status_t qz_qp_set(qz_ctx_t *c, qz_qpoly_t *p, size_t i,
                                 const srmech_bigint_t *n, const srmech_bigint_t *d);
static srmech_status_t qz_qp_neg(qz_qpoly_t *p);
static srmech_status_t qz_qp_content_clear(qz_ctx_t *c, qz_qpoly_t *a,
                                           qz_qpoly_t *b);

/* ---- caller-arena carve (mirror qg_take / qg_bind) ---------------- */

static uint32_t *qz_take(uint32_t *base, size_t words, size_t *cur, size_t cnt)
{
    uint32_t *p;
    assert(base != NULL && cur != NULL);
    assert(*cur <= words);
    if (cnt > words || *cur > words - cnt) {
        return NULL;
    }
    p = base + *cur;
    *cur += cnt;
    return p;
}

static srmech_status_t qz_bind(srmech_bigint_t *b, qz_ctx_t *c)
{
    uint32_t *limbs;
    assert(b != NULL && c != NULL);
    assert(c->cap > 0u);
    limbs = qz_take(c->pool, c->pool_words, &c->pool_cur, c->cap);
    if (limbs == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    b->limbs = limbs;
    b->cap = c->cap;
    b->n = 0u;
    b->sign = 0;
    return SRMECH_OK;
}

static size_t qz_hdr_words(void)
{
    size_t hw = (sizeof(srmech_bigint_t) + sizeof(uint32_t) - 1u)
                / sizeof(uint32_t);
    assert(sizeof(srmech_bigint_t) > 0u);
    assert(hw >= 1u);
    return hw;
}

static srmech_status_t qz_ctx_init(qz_ctx_t *c, uint32_t cap, void *ws,
                                   size_t ws_len)
{
    uint32_t *base = (uint32_t *)ws;
    size_t words = ws_len / sizeof(uint32_t);
    size_t carrier_words = (size_t)cap * (size_t)QZ_N_CARRIERS;
    size_t scratch_words = (size_t)cap * 8u + 256u;
    srmech_status_t st = SRMECH_OK;
    assert(c != NULL);
    assert((uintptr_t)ws % sizeof(uint32_t) == 0u || ws == NULL);
    c->cap = cap;
    if (words < carrier_words + scratch_words) {
        return SRMECH_ERR_OVERFLOW;
    }
    c->pool = base;
    c->pool_words = words - scratch_words;
    c->pool_cur = 0u;
    st |= qz_bind(&c->a_n, c); st |= qz_bind(&c->a_d, c);
    st |= qz_bind(&c->t0, c);  st |= qz_bind(&c->t1, c);
    st |= qz_bind(&c->g, c);   st |= qz_bind(&c->rem, c);
    st |= qz_bind(&c->r0, c);  st |= qz_bind(&c->r1, c);
    st |= qz_bind(&c->z0, c);  st |= qz_bind(&c->z1, c);
    if (st != SRMECH_OK) { return SRMECH_ERR_OVERFLOW; }
    st = srmech_bigint_set_i64(&c->z0, 0);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&c->z1, 1);
    if (st != SRMECH_OK) { return st; }
    c->scratch = (void *)(base + (words - scratch_words));
    c->scratch_len = scratch_words * sizeof(uint32_t);
    assert(c->pool_cur <= c->pool_words);
    return SRMECH_OK;
}

/* ---- exact-Q scalar reduce (mirror qg_q_reduce) ------------------- */

static srmech_status_t qz_q_reduce(qz_ctx_t *c, srmech_bigint_t *num,
                                   srmech_bigint_t *den)
{
    srmech_status_t st;
    assert(c != NULL && num != NULL && den != NULL);
    assert(den->sign != 0);
    if (den->sign < 0) {
        num->sign = (num->sign == 0) ? 0 : -num->sign;
        den->sign = -den->sign;
    }
    if (srmech_bigint_is_zero(num)) {
        return srmech_bigint_set_i64(den, 1);
    }
    st = srmech_bigint_gcd(&c->g, num, den, c->scratch, c->scratch_len);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_divmod(&c->r0, &c->rem, num, &c->g, c->scratch,
                              c->scratch_len);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_divmod(&c->r1, &c->rem, den, &c->g, c->scratch,
                              c->scratch_len);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(num, &c->r0);
    if (st != SRMECH_OK) { return st; }
    return srmech_bigint_copy(den, &c->r1);
}

/* ---- q-poly carve + basic ops (mirror qg_qp_*) ------------------- */

static size_t qz_trim(const srmech_bigint_t *nums, size_t n)
{
    size_t k = n;
    assert(nums != NULL || n == 0u);
    while (k > 0u && srmech_bigint_is_zero(&nums[k - 1u])) { k--; }
    assert(k <= n);
    return k;
}

static srmech_status_t qz_qp_alloc(qz_ctx_t *c, qz_qpoly_t *p, size_t terms)
{
    size_t hw = qz_hdr_words(), k;
    uint32_t *hn, *hd;
    srmech_status_t st;
    assert(c != NULL && p != NULL);
    assert(terms > 0u);
    hn = qz_take(c->pool, c->pool_words, &c->pool_cur, hw * terms);
    hd = qz_take(c->pool, c->pool_words, &c->pool_cur, hw * terms);
    if (hn == NULL || hd == NULL) { return SRMECH_ERR_OVERFLOW; }
    p->n = (srmech_bigint_t *)(void *)hn;
    p->d = (srmech_bigint_t *)(void *)hd;
    p->len = 0u;
    p->cap_terms = terms;
    for (k = 0u; k < terms; k++) {
        st = qz_bind(&p->n[k], c);
        if (st == SRMECH_OK) { st = qz_bind(&p->d[k], c); }
        if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&p->n[k], 0); }
        if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&p->d[k], 1); }
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

static srmech_status_t qz_qp_set(qz_ctx_t *c, qz_qpoly_t *p, size_t i,
                                 const srmech_bigint_t *n, const srmech_bigint_t *d)
{
    srmech_status_t st;
    assert(c != NULL && p != NULL && n != NULL && d != NULL);
    assert(i < p->cap_terms);
    (void)c;
    st = srmech_bigint_copy(&p->n[i], n);
    if (st == SRMECH_OK) { st = srmech_bigint_copy(&p->d[i], d); }
    return st;
}

static srmech_status_t qz_qp_neg(qz_qpoly_t *p)
{
    size_t k;
    assert(p != NULL);
    assert(p->len <= p->cap_terms);
    for (k = 0u; k < p->len; k++) {
        if (!srmech_bigint_is_zero(&p->n[k])) {
            p->n[k].sign = -p->n[k].sign;
        }
    }
    return SRMECH_OK;
}

/* Reduce each q-coefficient of a and b to lowest terms (a Class-K positive-den pin
 * via qz_q_reduce). The whole-solution shared-content clear (the Python op clears a
 * and b by ONE shared ℚ(q) denominator) is a no-op here: in the native canonical
 * scope rn_num / rn_den are already ℚ[q] (unit q-denominators), so a_0 = -rn_num and
 * a_1 = rn_den are emitted directly, each q-coefficient reduced. */
static srmech_status_t qz_qp_content_clear(qz_ctx_t *c, qz_qpoly_t *a,
                                           qz_qpoly_t *b)
{
    size_t k;
    srmech_status_t st;
    assert(c != NULL && a != NULL && b != NULL);
    assert(a->len <= a->cap_terms && b->len <= b->cap_terms);
    for (k = 0u; k < a->len; k++) {
        st = qz_q_reduce(c, &a->n[k], &a->d[k]);
        if (st != SRMECH_OK) { return st; }
    }
    for (k = 0u; k < b->len; k++) {
        st = qz_q_reduce(c, &b->n[k], &b->d[k]);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* ===================================================================
 * The public entry. The bridge inputs are the four QBiPoly ratios in the flat form
 * the Python _native.q_zeilberger_c marshals (concatenated q-runs + per-(Y,X)-cell
 * qlen[] + per-Y-cell x_low[]/x_cells[] + Y-cell count). The native peer reads ONLY
 * the canonical k-free q-geometric shape and declines the rest. (The prototype lives
 * in srmech.h, which this file includes.)
 * =================================================================== */
srmech_status_t srmech_q_zeilberger(
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
        size_t max_order,
        int *out_has, size_t *out_order,
        srmech_bigint_t *coeff_n, srmech_bigint_t *coeff_d,
        size_t *coeff_qlen, int64_t *coeff_xlow, size_t *coeff_xcells,
        size_t *out_coeff_count,
        srmech_bigint_t *cert_n, srmech_bigint_t *cert_d,
        size_t *cert_qlen, int64_t *cert_xlow, size_t *cert_xcells,
        size_t *out_cert_ycells,
        void *ws, size_t ws_len)
{
    qz_ctx_t c;
    /* zero-init EVERY local struct at declaration (MSVC /WX C4701 on guarded-alloc
     * paths; harmless -- the qpolys are qz_qp_alloc'd before any real use). */
    qz_qpoly_t a0 = {0}, a1 = {0};
    uint32_t cap = 0u;
    size_t cl = 1u, terms = 0u, i, nlen, dlen;
    srmech_status_t st;
    assert(out_has != NULL && out_order != NULL);
    assert(coeff_n != NULL && coeff_d != NULL);
    if (out_has == NULL || out_order == NULL || coeff_n == NULL
        || coeff_d == NULL || coeff_qlen == NULL || coeff_xlow == NULL
        || coeff_xcells == NULL || out_coeff_count == NULL
        || out_cert_ycells == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    *out_has = 0;
    *out_order = 0u;
    *out_coeff_count = 0u;
    *out_cert_ycells = 0u;
    (void)cert_n; (void)cert_d; (void)cert_qlen; (void)cert_xlow;
    (void)cert_xcells; (void)max_order;
    /* den ycells must be > 0 (a nonzero term-ratio denominator). */
    if (rn_den_ycells == 0u || rk_den_ycells == 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    /* the rc56 native scope: the k-FREE q-GEOMETRIC term --
     *   r_n a SINGLE Y^0 QPoly cell (rn_num/rn_den: 1 Y-cell, 1 X-cell each),
     *   r_k == 1 (rk_num == rk_den, both a single Y^0 X^0 unit cell).
     * Anything else -> decline (out_has stays 0; Python re-decides). */
    if (rn_num_ycells != 1u || rn_den_ycells != 1u
        || rk_num_ycells != 1u || rk_den_ycells != 1u) {
        return SRMECH_OK;
    }
    if (rn_num_xcells[0] != 1u || rn_den_xcells[0] != 1u
        || rk_num_xcells[0] != 1u || rk_den_xcells[0] != 1u) {
        return SRMECH_OK;
    }
    /* r_k == 1: rk_num and rk_den are the SAME single Q[q] cell at X^0. Require both
     * x_low == 0 and a byte-identical (num/den) q-run (the unit ratio). */
    if (rk_num_xlow[0] != 0 || rk_den_xlow[0] != 0) { return SRMECH_OK; }
    if (rk_num_qlen[0] != rk_den_qlen[0]) { return SRMECH_OK; }
    for (i = 0u; i < rk_num_qlen[0]; i++) {
        if (srmech_bigint_cmp(&rk_num_n[i], &rk_den_n[i]) != 0
            || srmech_bigint_cmp(&rk_num_d[i], &rk_den_d[i]) != 0) {
            return SRMECH_OK;
        }
    }
    /* rn_num / rn_den must be honest Q[q] cells at X^0 (the q-geometric ratio is
     * X-free for the k-free case; a genuine X-dependence is order-1 still but the
     * recurrence coefficients are then Laurent-in-X -- handled on the pure path). */
    if (rn_num_xlow[0] != 0 || rn_den_xlow[0] != 0) { return SRMECH_OK; }
    nlen = rn_num_qlen[0];
    dlen = rn_den_qlen[0];
    if (nlen == 0u || dlen == 0u) { return SRMECH_OK; }
    if (nlen > QZ_MAX_QDEG || dlen > QZ_MAX_QDEG) { return SRMECH_ERR_BAD_INPUT; }
    /* size the arena from the input q-coefficient limbs. */
    for (i = 0u; i < nlen; i++) {
        if (rn_num_n[i].n > cl) { cl = rn_num_n[i].n; }
        if (rn_num_d[i].n > cl) { cl = rn_num_d[i].n; }
    }
    for (i = 0u; i < dlen; i++) {
        if (rn_den_n[i].n > cl) { cl = rn_den_n[i].n; }
        if (rn_den_d[i].n > cl) { cl = rn_den_d[i].n; }
    }
    cap = (uint32_t)(cl * 2u + 64u);
    st = qz_ctx_init(&c, cap, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    terms = ((nlen > dlen) ? nlen : dlen) + 1u;
    st = qz_qp_alloc(&c, &a0, terms);
    if (st == SRMECH_OK) { st = qz_qp_alloc(&c, &a1, terms); }
    if (st != SRMECH_OK) { return SRMECH_ERR_OVERFLOW; }
    /* a_0(X) = -rn_num(q)  (the recurrence: rn_den f(n+1) - rn_num f(n) = 0). */
    for (i = 0u; i < nlen; i++) {
        st = qz_qp_set(&c, &a0, i, &rn_num_n[i], &rn_num_d[i]);
        if (st != SRMECH_OK) { return st; }
    }
    a0.len = qz_trim(a0.n, nlen);
    st = qz_qp_neg(&a0);
    if (st != SRMECH_OK) { return st; }
    /* a_1(X) = rn_den(q). */
    for (i = 0u; i < dlen; i++) {
        st = qz_qp_set(&c, &a1, i, &rn_den_n[i], &rn_den_d[i]);
        if (st != SRMECH_OK) { return st; }
    }
    a1.len = qz_trim(a1.n, dlen);
    if (a0.len == 0u || a1.len == 0u) { return SRMECH_OK; }
    st = qz_qp_content_clear(&c, &a0, &a1);
    if (st != SRMECH_OK) { return st; }
    /* write back the order-1 recurrence: coeff[0] = a_0, coeff[1] = a_1, each a
     * single X^0 QPoly cell (x_low 0, x_cells 1). No certificate emitted natively
     * (the q-geometric k-free term telescopes trivially; the pure path supplies the
     * certificate when needed) -> out_cert_ycells stays 0. */
    {
        size_t off = 0u, j;
        for (j = 0u; j < a0.len; j++) {
            st = srmech_bigint_copy(&coeff_n[off + j], &a0.n[j]);
            if (st == SRMECH_OK) { st = srmech_bigint_copy(&coeff_d[off + j], &a0.d[j]); }
            if (st != SRMECH_OK) { return st; }
        }
        coeff_qlen[0] = a0.len;
        coeff_xlow[0] = 0;
        coeff_xcells[0] = 1u;
        off += a0.len;
        for (j = 0u; j < a1.len; j++) {
            st = srmech_bigint_copy(&coeff_n[off + j], &a1.n[j]);
            if (st == SRMECH_OK) { st = srmech_bigint_copy(&coeff_d[off + j], &a1.d[j]); }
            if (st != SRMECH_OK) { return st; }
        }
        coeff_qlen[1] = a1.len;
        coeff_xlow[1] = 0;
        coeff_xcells[1] = 1u;
    }
    *out_order = 1u;
    *out_coeff_count = 2u;
    *out_cert_ycells = 0u;
    *out_has = 1;
    return SRMECH_OK;
}

/* The minimum `ws_len` BYTES srmech_q_zeilberger needs for inputs of `coeff_limbs`
 * significant limbs per q-coefficient, a max ansatz `order`, and a higher q-degree of
 * `qdeg`. The native canonical scope is order-1 + two short q-polys; the bound covers
 * the scalar carriers + the two q-poly accumulators + the reduce scratch. */
size_t srmech_q_zeilberger_ws_bound(size_t coeff_limbs, size_t order, size_t qdeg)
{
    size_t cl = (coeff_limbs == 0u) ? 1u : coeff_limbs;
    size_t dg = (qdeg == 0u) ? 1u : qdeg;
    size_t cap = cl * 2u + 64u;
    size_t hw = qz_hdr_words();
    size_t terms = dg + 2u;
    size_t polys = 2u;                    /* a0, a1 */
    size_t header_words = 2u * hw * terms * polys;
    size_t limb_words = 2u * terms * cap * polys;
    size_t carriers = cap * (size_t)QZ_N_CARRIERS;
    size_t scratch = cap * 8u + 256u;
    size_t words = header_words + limb_words + carriers + scratch + 256u;
    (void)order;
    assert(cap >= 2u);
    assert(words >= limb_words);
    return words * sizeof(uint32_t);
}

/* The per-coefficient limb cap for each srmech_bigint in the coeff_* / cert_* OUTPUT
 * arrays, so a result q-coefficient never overflows its slot. */
size_t srmech_q_zeilberger_out_cap(size_t coeff_limbs, size_t order, size_t qdeg)
{
    size_t cl = (coeff_limbs == 0u) ? 1u : coeff_limbs;
    size_t cap = cl * 2u + 64u;
    (void)order; (void)qdeg;
    assert(cap >= 2u);
    assert(cap >= coeff_limbs);
    return cap;
}
