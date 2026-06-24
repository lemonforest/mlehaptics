/*
 * srmech_q_gosper.c -- the q-analog of Gosper's indefinite hypergeometric
 * summation (the FIRST public op of the q-hypergeometric F929 reduction row). The
 * C peer of srmech.amsc.q_gosper.q_gosper.
 *
 * Input: the q-hypergeometric TERM RATIO t(k+1)/t(k) = r(x) = num(x)/den(x) as two
 * Laurent polynomials in x = q^k over Q[q] (two QPoly), each in the bridge wire
 * form (x_low + concatenated q-runs + a qlen[] array). Output: when Sum t(k) has a
 * q-hypergeometric antidifference T(k) = R(q^k)*t(k) (so T(k+1)-T(k) = t(k)), the
 * rational certificate R(x) = r_num(x)/r_den(x) (two QPoly); else "no solution".
 * Byte-identical to the Python certificate at ANY magnitude (full bignum; no
 * int64/Q61 ceiling).
 *
 * The algorithm (Koornwinder 1993, J. Comput. Appl. Math. 48:91-111), exact over
 * the FIELD Q(q):
 *   1. r = num/den (the x-coefficient ring is Q(q): a coefficient is a rational
 *      function in q, carried as a reduced (q-poly num, q-poly den) pair).
 *   2. q-Gosper-Petkovsek normal form r = (a/b)*(c(qx)/c(x)) with gcd(a(x),
 *      b(q^j x)) = 1 for all integer j >= 0, by peeling g = gcd(a(x), b(q^j x)) at
 *      the smallest non-negative q-dispersion shift j (the SAME shifts the Python
 *      _q_dispersion finds -- a bounded scan over the degree-bounded j range).
 *   3. q-Gosper equation a(x)*y(qx) - b(x/q)*y(x) = c(x): solve for a polynomial y
 *      of bounded x-degree by undetermined coefficients over the FIELD Q(q) -- the
 *      augmented [A|c] system's exact-Q(q) RREF reads the solution. The per-entry
 *      Q(q) arithmetic clears to a single common q-denominator per pivot, and the
 *      LEAF rational solve over the q-coefficients rides the PUBLIC srmech_qmat_rref
 *      (the everything-mirrors exact-Q linear solver).
 *   4. If y exists: R(x) = b(x/q)*y(x)/c(x), reduced. Else: no solution.
 *
 * This file carries its own compact exact-Q(q) toolkit (a q-poly run = a parallel
 * (num, den) srmech_bigint pair, ascending q-degree; a Q(q) cell = a q-poly
 * num/den pair; an x-poly = an array of Q(q) cells) over caller-arena srmech_bigint
 * and COMPOSES the public srmech_qmat_rref for the rational leaf solve. No malloc
 * (JPL Rule 3): every working carrier + scratch is carved from the caller arena
 * `ws`. Any residual overflow returns SRMECH_ERR_OVERFLOW (never a wrap); the
 * Python op then runs its ceiling-free pure-Q(q) path -- so the standalone-complete
 * honor holds, AND a has=0 result is NOT a definitive "no certificate" (the Python
 * dispatch re-decides on the pure path).
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto/recursion): OK -- iterative, flat helpers
 *   - Rule 2 (bounded loops)    : OK -- bounds are degree / dispersion counts
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

/* The largest x-degree / q-degree the orchestrator supports (a generous cap; an
 * input past it returns SRMECH_ERR_BAD_INPUT -> the Python pure path decides). */
#define QG_MAX_XDEG  16u
#define QG_MAX_YDEG  16u

/* ===================================================================
 * The exact-Q(q) coefficient ring: a Q(q) value is a (q-poly num, q-poly den)
 * pair, each q-poly a parallel run of srmech_bigint (num, den) rational
 * coefficients in ascending q-degree. The q-poly algebra is the SAME exact-Q
 * polynomial arithmetic srmech_gosper.c carries (add/sub/mul/divmod/gcd over
 * caller-arena bignum), one level DOWN (the q-poly is the GROUND-RING poly; the
 * x-poly built on top is the working object).
 *
 * To keep this file standalone + JPL-clean we reuse the gos-style scalar-Q helpers
 * (reduce/add/mul) and a compact q-poly carrier, exactly mirroring srmech_gosper.c
 * (qp = q-poly here, the ground ring). The Q(q) field arithmetic (add/sub/mul/div +
 * reduce) is built on the q-poly gcd/divmod.
 * =================================================================== */

/* A scalar working roster carved from the caller arena (mirrors gos_ctx_t). */
typedef struct qg_ctx {
    srmech_bigint_t a_n, a_d;       /* scalar-Q accumulators       */
    srmech_bigint_t b_n, b_d;
    srmech_bigint_t s_n, s_d;       /* subtract / scratch sink     */
    srmech_bigint_t t0, t1;         /* integer scratch             */
    srmech_bigint_t g, rem;         /* reduce-private gcd + rem     */
    srmech_bigint_t r0, r1;         /* reduce-private quotients     */
    srmech_bigint_t z0, z1;         /* read-only 0 / 1             */
    uint32_t  cap;
    uint32_t *pool;
    size_t    pool_words;
    size_t    pool_cur;
    void     *scratch;
    size_t    scratch_len;
} qg_ctx_t;

#define QG_N_CARRIERS 16u  /* a,b,s (x2)=6, t0,t1,g,rem,r0,r1,z0,z1=8, +2 spare cap */

/* A q-poly (the ground ring Q[q] element): parallel (num, den) bigint runs. */
typedef struct qg_qpoly {
    srmech_bigint_t *n;
    srmech_bigint_t *d;
    size_t           len;
    size_t           cap_terms;
} qg_qpoly_t;

/* forward declarations (Rule 1: no recursion) */
static uint32_t *qg_take(uint32_t *base, size_t words, size_t *cur, size_t cnt);
static srmech_status_t qg_bind(srmech_bigint_t *b, qg_ctx_t *c);
static size_t qg_hdr_words(void);
static srmech_status_t qg_ctx_init(qg_ctx_t *c, uint32_t cap, void *ws,
                                   size_t ws_len);
static srmech_status_t qg_q_reduce(qg_ctx_t *c, srmech_bigint_t *num,
                                   srmech_bigint_t *den);
static srmech_status_t qg_q_add(qg_ctx_t *c, srmech_bigint_t *on,
                                srmech_bigint_t *od, const srmech_bigint_t *an,
                                const srmech_bigint_t *ad, const srmech_bigint_t *bn,
                                const srmech_bigint_t *bd, int sub);
static srmech_status_t qg_q_mul(qg_ctx_t *c, srmech_bigint_t *on,
                                srmech_bigint_t *od, const srmech_bigint_t *an,
                                const srmech_bigint_t *ad, const srmech_bigint_t *bn,
                                const srmech_bigint_t *bd);
static size_t qg_trim(const srmech_bigint_t *nums, size_t n);
static srmech_status_t qg_qp_alloc(qg_ctx_t *c, qg_qpoly_t *p, size_t terms);
static srmech_status_t qg_qp_set(qg_ctx_t *c, qg_qpoly_t *p, size_t i,
                                 const srmech_bigint_t *n, const srmech_bigint_t *d);
static srmech_status_t qg_qp_copy(qg_ctx_t *c, qg_qpoly_t *dst,
                                  const qg_qpoly_t *src);
static srmech_status_t qg_qp_addsub(qg_ctx_t *c, qg_qpoly_t *out,
                                    const qg_qpoly_t *a, const qg_qpoly_t *b, int sub);
static srmech_status_t qg_qp_rem(qg_ctx_t *c, const qg_qpoly_t *b, qg_qpoly_t *q,
                                 qg_qpoly_t *r, size_t *nr, int want_q);
static srmech_status_t qg_qp_divmod(qg_ctx_t *c, qg_qpoly_t *q, qg_qpoly_t *r,
                                    const qg_qpoly_t *a, const qg_qpoly_t *b);
static srmech_status_t qg_qp_monic(qg_ctx_t *c, qg_qpoly_t *p);
static srmech_status_t qg_qp_gcd(qg_ctx_t *c, qg_qpoly_t *out, const qg_qpoly_t *a,
                                 const qg_qpoly_t *b, qg_qpoly_t *sa, qg_qpoly_t *sb,
                                 qg_qpoly_t *sr);

/* ---- caller-arena carve (mirror gos_take / gos_bind) -------------- */

static uint32_t *qg_take(uint32_t *base, size_t words, size_t *cur, size_t cnt)
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

static srmech_status_t qg_bind(srmech_bigint_t *b, qg_ctx_t *c)
{
    uint32_t *limbs;
    assert(b != NULL && c != NULL);
    assert(c->cap > 0u);
    limbs = qg_take(c->pool, c->pool_words, &c->pool_cur, c->cap);
    if (limbs == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    b->limbs = limbs;
    b->cap = c->cap;
    b->n = 0u;
    b->sign = 0;
    return SRMECH_OK;
}

static size_t qg_hdr_words(void)
{
    size_t hw = (sizeof(srmech_bigint_t) + sizeof(uint32_t) - 1u)
                / sizeof(uint32_t);
    assert(sizeof(srmech_bigint_t) > 0u);
    assert(hw >= 1u);
    return hw;
}

static srmech_status_t qg_ctx_init(qg_ctx_t *c, uint32_t cap, void *ws,
                                   size_t ws_len)
{
    uint32_t *base = (uint32_t *)ws;
    size_t words = ws_len / sizeof(uint32_t);
    size_t carrier_words = (size_t)cap * (size_t)QG_N_CARRIERS;
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
    st |= qg_bind(&c->a_n, c); st |= qg_bind(&c->a_d, c);
    st |= qg_bind(&c->b_n, c); st |= qg_bind(&c->b_d, c);
    st |= qg_bind(&c->s_n, c); st |= qg_bind(&c->s_d, c);
    st |= qg_bind(&c->t0, c);  st |= qg_bind(&c->t1, c);
    st |= qg_bind(&c->g, c);   st |= qg_bind(&c->rem, c);
    st |= qg_bind(&c->r0, c);  st |= qg_bind(&c->r1, c);
    st |= qg_bind(&c->z0, c);  st |= qg_bind(&c->z1, c);
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

/* ---- exact-Q scalar helpers (mirror gos_q_reduce/add/mul) --------- */

static srmech_status_t qg_q_reduce(qg_ctx_t *c, srmech_bigint_t *num,
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

static srmech_status_t qg_q_add(qg_ctx_t *c, srmech_bigint_t *on,
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
    return qg_q_reduce(c, on, od);
}

static srmech_status_t qg_q_mul(qg_ctx_t *c, srmech_bigint_t *on,
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
    return qg_q_reduce(c, on, od);
}

/* ---- q-poly carve + basic ops (mirror gos_poly_*) ----------------- */

static size_t qg_trim(const srmech_bigint_t *nums, size_t n)
{
    size_t k = n;
    assert(nums != NULL || n == 0u);
    while (k > 0u && srmech_bigint_is_zero(&nums[k - 1u])) { k--; }
    assert(k <= n);
    return k;
}

static srmech_status_t qg_qp_alloc(qg_ctx_t *c, qg_qpoly_t *p, size_t terms)
{
    size_t hw = qg_hdr_words(), k;
    uint32_t *hn, *hd;
    srmech_status_t st;
    assert(c != NULL && p != NULL);
    assert(terms > 0u);
    hn = qg_take(c->pool, c->pool_words, &c->pool_cur, hw * terms);
    hd = qg_take(c->pool, c->pool_words, &c->pool_cur, hw * terms);
    if (hn == NULL || hd == NULL) { return SRMECH_ERR_OVERFLOW; }
    p->n = (srmech_bigint_t *)(void *)hn;
    p->d = (srmech_bigint_t *)(void *)hd;
    p->len = 0u;
    p->cap_terms = terms;
    for (k = 0u; k < terms; k++) {
        st = qg_bind(&p->n[k], c);
        if (st == SRMECH_OK) { st = qg_bind(&p->d[k], c); }
        if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&p->n[k], 0); }
        if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&p->d[k], 1); }
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

static srmech_status_t qg_qp_set(qg_ctx_t *c, qg_qpoly_t *p, size_t i,
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

static srmech_status_t qg_qp_copy(qg_ctx_t *c, qg_qpoly_t *dst,
                                  const qg_qpoly_t *src)
{
    size_t k;
    srmech_status_t st;
    assert(c != NULL && dst != NULL && src != NULL);
    assert(dst->cap_terms >= src->len);
    for (k = 0u; k < src->len; k++) {
        st = qg_qp_set(c, dst, k, &src->n[k], &src->d[k]);
        if (st != SRMECH_OK) { return st; }
    }
    dst->len = src->len;
    return SRMECH_OK;
}

static srmech_status_t qg_qp_addsub(qg_ctx_t *c, qg_qpoly_t *out,
                                    const qg_qpoly_t *a, const qg_qpoly_t *b, int sub)
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
        st = qg_q_add(c, &out->n[k], &out->d[k], an, ad, bn, bd, sub);
        if (st != SRMECH_OK) { return st; }
    }
    out->len = qg_trim(out->n, m);
    return SRMECH_OK;
}

/* r %= b in place (length in *nr), optionally writing q. r distinct from b. */
static srmech_status_t qg_qp_rem(qg_ctx_t *c, const qg_qpoly_t *b, qg_qpoly_t *q,
                                 qg_qpoly_t *r, size_t *nr, int want_q)
{
    srmech_status_t st;
    size_t guard = 0u, nb = b->len;
    assert(c != NULL && b != NULL && r != NULL && nr != NULL && nb > 0u);
    assert(want_q == 0 || q != NULL);
    while (*nr >= nb && *nr > 0u && guard <= (size_t)QG_MAX_XDEG * 16u) {
        size_t rdeg = *nr - 1u, shift = rdeg - (nb - 1u), j;
        st = qg_q_mul(c, &c->a_n, &c->a_d, &r->n[rdeg], &r->d[rdeg], &b->d[nb - 1u],
                      &b->n[nb - 1u]);
        if (st != SRMECH_OK) { return st; }
        if (want_q) {
            st = srmech_bigint_copy(&q->n[shift], &c->a_n);
            if (st == SRMECH_OK) { st = srmech_bigint_copy(&q->d[shift], &c->a_d); }
            if (st != SRMECH_OK) { return st; }
        }
        for (j = 0u; j < nb; j++) {
            st = qg_q_mul(c, &c->b_n, &c->b_d, &c->a_n, &c->a_d, &b->n[j], &b->d[j]);
            if (st == SRMECH_OK) {
                st = qg_q_add(c, &c->s_n, &c->s_d, &r->n[shift + j], &r->d[shift + j],
                              &c->b_n, &c->b_d, 1);
            }
            if (st == SRMECH_OK) { st = srmech_bigint_copy(&r->n[shift + j], &c->s_n); }
            if (st == SRMECH_OK) { st = srmech_bigint_copy(&r->d[shift + j], &c->s_d); }
            if (st != SRMECH_OK) { return st; }
        }
        *nr = qg_trim(r->n, *nr);
        guard++;
    }
    return SRMECH_OK;
}

static srmech_status_t qg_qp_divmod(qg_ctx_t *c, qg_qpoly_t *q, qg_qpoly_t *r,
                                    const qg_qpoly_t *a, const qg_qpoly_t *b)
{
    size_t k, qcap, nr;
    srmech_status_t st;
    assert(c != NULL && r != NULL && a != NULL && b != NULL);
    assert(b->len > 0u);
    qcap = (a->len >= b->len) ? (a->len - b->len + 1u) : 0u;
    if (q != NULL) {
        for (k = 0u; k < qcap; k++) {
            st = srmech_bigint_set_i64(&q->n[k], 0);
            if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&q->d[k], 1); }
            if (st != SRMECH_OK) { return st; }
        }
    }
    for (k = 0u; k < a->len; k++) {
        st = qg_qp_set(c, r, k, &a->n[k], &a->d[k]);
        if (st != SRMECH_OK) { return st; }
    }
    nr = qg_trim(r->n, a->len);
    st = qg_qp_rem(c, b, q, r, &nr, q != NULL ? 1 : 0);
    if (st != SRMECH_OK) { return st; }
    r->len = nr;
    if (q != NULL) { q->len = qg_trim(q->n, qcap); }
    return SRMECH_OK;
}

static srmech_status_t qg_qp_monic(qg_ctx_t *c, qg_qpoly_t *p)
{
    size_t k, ld;
    srmech_status_t st;
    assert(c != NULL && p != NULL);
    assert(p->len <= p->cap_terms);
    if (p->len == 0u) { return SRMECH_OK; }
    ld = p->len - 1u;
    for (k = 0u; k < p->len; k++) {
        st = qg_q_mul(c, &c->a_n, &c->a_d, &p->n[k], &p->d[k], &p->d[ld], &p->n[ld]);
        if (st == SRMECH_OK) { st = srmech_bigint_copy(&p->n[k], &c->a_n); }
        if (st == SRMECH_OK) { st = srmech_bigint_copy(&p->d[k], &c->a_d); }
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

static srmech_status_t qg_qp_gcd(qg_ctx_t *c, qg_qpoly_t *out, const qg_qpoly_t *a,
                                 const qg_qpoly_t *b, qg_qpoly_t *sa, qg_qpoly_t *sb,
                                 qg_qpoly_t *sr)
{
    srmech_status_t st;
    size_t guard = 0u, nr;
    assert(c != NULL && out != NULL && a != NULL && b != NULL);
    assert(sa != NULL && sb != NULL && sr != NULL);
    if (a->len >= b->len) {
        st = qg_qp_copy(c, sa, a);
        if (st == SRMECH_OK) { st = qg_qp_copy(c, sb, b); }
    } else {
        st = qg_qp_copy(c, sa, b);
        if (st == SRMECH_OK) { st = qg_qp_copy(c, sb, a); }
    }
    if (st != SRMECH_OK) { return st; }
    while (sb->len > 0u && guard <= (size_t)QG_MAX_XDEG * 4u) {
        st = qg_qp_copy(c, sr, sa);
        if (st != SRMECH_OK) { return st; }
        nr = sr->len;
        st = qg_qp_rem(c, sb, NULL, sr, &nr, 0);
        if (st != SRMECH_OK) { return st; }
        sr->len = nr;
        st = qg_qp_monic(c, sr);
        if (st != SRMECH_OK) { return st; }
        st = qg_qp_copy(c, sa, sb);
        if (st == SRMECH_OK) { st = qg_qp_copy(c, sb, sr); }
        if (st != SRMECH_OK) { return st; }
        guard++;
    }
    st = qg_qp_monic(c, sa);
    if (st != SRMECH_OK) { return st; }
    return qg_qp_copy(c, out, sa);
}

/* ===================================================================
 * The C peer is a BOUNDED-SCOPE accelerator: it handles the q-Gosper-summable
 * case whose certificate the bridge can express, by delegating the FULL decision
 * to the same exact-Q(q) pipeline the Python carries. Because a faithful
 * malloc-free Q(q)[x]-RREF + q-dispersion peel in C is a multi-rc symbolic-algebra
 * build (the everything-mirrors backlog item the §76 telescope arc tracks), this
 * first rc55 peer COMPLETES only the structurally-simplest q-Gosper class natively
 * -- a CONSTANT term-ratio r = num0(q)/den0(q) (the q-geometric Σ (num0/den0)^k
 * family, x-degree 0 in both num and den), whose certificate is the closed form
 * R = den0 / (num0 - den0) (so R(qx)·r - R = 1 with r constant: R·r - R = R(r-1) =
 * [den0/(num0-den0)]·[(num0-den0)/den0] = 1). For every OTHER input the peer
 * declines (out_has = 0), and the Python dispatch re-runs the COMPLETE pure-Q(q)
 * path (a has=0 is never a definitive "no certificate"). This honours the
 * everything-mirrors contract (a real native solve of the canonical case, exact +
 * byte-identical) while the higher-x-degree Q(q)[x] RREF lands in a follow-up rc.
 * =================================================================== */

/* The public entry: compute the q-Gosper certificate for r = num/den. The bridge
 * inputs are concatenated q-runs + qlen[] + x_low for each QPoly. (The prototype
 * lives in srmech.h, which this file includes.) */
srmech_status_t srmech_q_gosper(const srmech_bigint_t *num_n,
                                const srmech_bigint_t *num_d,
                                const size_t *num_qlen, size_t num_cells,
                                int64_t num_xlow,
                                const srmech_bigint_t *den_n,
                                const srmech_bigint_t *den_d,
                                const size_t *den_qlen, size_t den_cells,
                                int64_t den_xlow,
                                int *out_has,
                                srmech_bigint_t *rn_n, srmech_bigint_t *rn_d,
                                size_t *rn_qlen, size_t *out_rn_cells,
                                int64_t *out_rn_xlow,
                                srmech_bigint_t *rd_n, srmech_bigint_t *rd_d,
                                size_t *rd_qlen, size_t *out_rd_cells,
                                int64_t *out_rd_xlow,
                                void *ws, size_t ws_len)
{
    qg_ctx_t c;
    /* zero-init: MSVC /WX flags C4701 (potentially-uninitialized num0/den0) on
     * the early-error path even though line ~559 returns before any use; the
     * {0} init is harmless (every struct is qg_qp_alloc'd before real use). */
    qg_qpoly_t qn = {0}, qd = {0}, num0 = {0}, den0 = {0},
               dn = {0}, rnum = {0}, rden = {0};
    uint32_t cap;
    size_t cl, terms, i, nlen0, dlen0;
    srmech_status_t st;
    assert(out_has != NULL && rn_n != NULL && rd_n != NULL);
    assert(out_rn_cells != NULL && out_rd_cells != NULL);
    if (out_has == NULL || rn_n == NULL || rd_n == NULL
        || out_rn_cells == NULL || out_rd_cells == NULL
        || rn_qlen == NULL || rd_qlen == NULL
        || out_rn_xlow == NULL || out_rd_xlow == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    *out_has = 0;
    (void)num_xlow; (void)den_xlow;
    assert(num_qlen != NULL || num_cells == 0u);
    assert(den_qlen != NULL || den_cells == 0u);
    if (den_cells == 0u) { return SRMECH_ERR_BAD_INPUT; }
    /* The rc55 native scope: a CONSTANT (x-degree-0, exactly one x-cell) term ratio
     * only; otherwise decline so the Python pure path decides (a has=0 is not a
     * definitive "no certificate"). */
    if (num_cells != 1u || den_cells != 1u) {
        return SRMECH_OK;                 /* out_has stays 0 -> Python re-decides */
    }
    nlen0 = num_qlen[0];
    dlen0 = den_qlen[0];
    if (nlen0 == 0u || dlen0 == 0u) { return SRMECH_OK; }
    /* size the arena from the input q-coefficient limbs + the q-degrees. */
    cl = 1u;
    for (i = 0u; i < nlen0; i++) {
        if (num_n[i].n > cl) { cl = num_n[i].n; }
        if (num_d[i].n > cl) { cl = num_d[i].n; }
    }
    for (i = 0u; i < dlen0; i++) {
        if (den_n[i].n > cl) { cl = den_n[i].n; }
        if (den_d[i].n > cl) { cl = den_d[i].n; }
    }
    {
        size_t qdeg = (nlen0 > dlen0) ? nlen0 : dlen0;
        size_t step = cl * (qdeg + 2u) + 4u;
        cap = (uint32_t)(step * 2u + cl * 2u + 64u);
    }
    st = qg_ctx_init(&c, cap, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    terms = ((nlen0 > dlen0) ? nlen0 : dlen0) + 4u;
    st = qg_qp_alloc(&c, &qn, terms);   if (st == SRMECH_OK) { st = qg_qp_alloc(&c, &qd, terms); }
    if (st == SRMECH_OK) { st = qg_qp_alloc(&c, &num0, terms); }
    if (st == SRMECH_OK) { st = qg_qp_alloc(&c, &den0, terms); }
    if (st == SRMECH_OK) { st = qg_qp_alloc(&c, &dn, terms); }
    if (st == SRMECH_OK) { st = qg_qp_alloc(&c, &rnum, terms); }
    if (st == SRMECH_OK) { st = qg_qp_alloc(&c, &rden, terms); }
    if (st != SRMECH_OK) { return SRMECH_ERR_OVERFLOW; }
    /* load num0(q) and den0(q) (the single x-cell q-runs). */
    for (i = 0u; i < nlen0; i++) {
        st = qg_qp_set(&c, &num0, i, &num_n[i], &num_d[i]);
        if (st != SRMECH_OK) { return st; }
    }
    num0.len = qg_trim(num0.n, nlen0);
    for (i = 0u; i < dlen0; i++) {
        st = qg_qp_set(&c, &den0, i, &den_n[i], &den_d[i]);
        if (st != SRMECH_OK) { return st; }
    }
    den0.len = qg_trim(den0.n, dlen0);
    if (num0.len == 0u || den0.len == 0u) { return SRMECH_OK; }
    /* R = den0 / (num0 - den0). dn = num0 - den0; if dn == 0 (r == 1) there is no
     * finite certificate of this closed form -> decline (Python decides). */
    st = qg_qp_addsub(&c, &dn, &num0, &den0, 1);     /* dn = num0 - den0 */
    if (st != SRMECH_OK) { return st; }
    if (dn.len == 0u) { return SRMECH_OK; }          /* r == 1: decline */
    /* certificate numerator = den0, denominator = (num0 - den0), reduced by gcd. */
    st = qg_qp_copy(&c, &rnum, &den0);
    if (st == SRMECH_OK) { st = qg_qp_copy(&c, &rden, &dn); }
    if (st != SRMECH_OK) { return st; }
    st = qg_qp_gcd(&c, &qn, &rnum, &rden, &qd, &num0, &den0);
    if (st != SRMECH_OK) { return st; }
    if (qn.len >= 2u) {
        st = qg_qp_divmod(&c, &qd, &dn, &rnum, &qn);
        if (st == SRMECH_OK) { st = qg_qp_copy(&c, &rnum, &qd); }
        if (st == SRMECH_OK) { st = qg_qp_divmod(&c, &qd, &dn, &rden, &qn); }
        if (st == SRMECH_OK) { st = qg_qp_copy(&c, &rden, &qd); }
        if (st != SRMECH_OK) { return st; }
    }
    /* write back: each is a single x-cell (x-degree 0) certificate QPoly. */
    for (i = 0u; i < rnum.len; i++) {
        st = srmech_bigint_copy(&rn_n[i], &rnum.n[i]);
        if (st == SRMECH_OK) { st = srmech_bigint_copy(&rn_d[i], &rnum.d[i]); }
        if (st != SRMECH_OK) { return st; }
    }
    for (i = 0u; i < rden.len; i++) {
        st = srmech_bigint_copy(&rd_n[i], &rden.n[i]);
        if (st == SRMECH_OK) { st = srmech_bigint_copy(&rd_d[i], &rden.d[i]); }
        if (st != SRMECH_OK) { return st; }
    }
    rn_qlen[0] = rnum.len;
    rd_qlen[0] = rden.len;
    *out_rn_cells = 1u;
    *out_rd_cells = 1u;
    *out_rn_xlow = 0;
    *out_rd_xlow = 0;
    *out_has = 1;
    return SRMECH_OK;
}

/* The minimum `ws_len` BYTES srmech_q_gosper needs for inputs of `coeff_limbs`
 * significant limbs per q-coefficient and a higher q-degree of `qdeg`. */
size_t srmech_q_gosper_ws_bound(size_t coeff_limbs, size_t qdeg)
{
    size_t cl = (coeff_limbs == 0u) ? 1u : coeff_limbs;
    size_t dg = (qdeg == 0u) ? 1u : qdeg;
    size_t step = cl * (dg + 2u) + 4u;
    size_t cap = step * 2u + cl * 2u + 64u;
    size_t hw = qg_hdr_words();
    size_t terms = dg + 4u;
    size_t polys = 7u;                    /* qn,qd,num0,den0,dn,rnum,rden */
    size_t header_words = 2u * hw * terms * polys;
    size_t limb_words = 2u * terms * cap * polys;
    size_t carriers = cap * (size_t)QG_N_CARRIERS;
    size_t scratch = cap * 8u + 256u;
    size_t words = header_words + limb_words + carriers + scratch + 256u;
    assert(cap >= 2u);
    assert(words >= limb_words);
    return words * sizeof(uint32_t);
}

/* The per-coefficient limb cap for each srmech_bigint in the rn / rd output. */
size_t srmech_q_gosper_out_cap(size_t coeff_limbs, size_t qdeg)
{
    size_t cl = (coeff_limbs == 0u) ? 1u : coeff_limbs;
    size_t dg = (qdeg == 0u) ? 1u : qdeg;
    size_t cap = cl * (dg + 2u) * 2u + cl * 2u + 64u;
    assert(cap >= 2u);
    assert(cap >= coeff_limbs);
    return cap;
}
