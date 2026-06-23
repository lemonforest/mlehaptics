/*
 * srmech_gosper.c -- Gosper's indefinite hypergeometric summation (the FIRST
 * public op of the section 76 "telescope" Sigma-row closed-form prover, F929). The C
 * peer of srmech.amsc.gosper.gosper.
 *
 * Input: the TERM RATIO t(k+1)/t(k) = num(k)/den(k) as two exact-rational
 * polynomials over Q[k] (parallel srmech_bigint coefficient arrays, ascending
 * degree). Output: when Sum t(k) has a hypergeometric antidifference T(k) =
 * R(k)*t(k) (so T(k+1) - T(k) = t(k)), the rational certificate R(k) =
 * r_num(k)/r_den(k); else "no solution". Byte-identical to the Python certificate
 * at ANY magnitude (full bignum coefficients; no int64/Q61 ceiling).
 *
 * The algorithm (Gosper 1978; PWZ A=B ch. 5), exact over Q[k]:
 *   1. r = num/den.
 *   2. Gosper-Petkovsek normal form r = (a/b)*(c(k+1)/c(k)) with
 *      gcd(a(k), b(k+h)) = 1 for all integer h >= 0, by peeling g = gcd(a(k),
 *      b(k+h)) at the smallest non-negative integer shift h in the DISPERSION
 *      set. The dispersion is found by a bounded DIRECT shift-test: a common root
 *      of a(k) and b(k+h) forces h = (root of b) - (root of a), so h is bounded
 *      by the Cauchy root bounds of a and b; each integer h in that finite range
 *      is tested with the exact poly gcd/shift. (Same shifts the Python
 *      _dispersion finds -- no resultant needed.)
 *   3. Gosper equation a(k)*x(k+1) - b(k-1)*x(k) = c(k): solve for a polynomial x
 *      of the standard Gosper degree bound by undetermined coefficients -- the
 *      augmented [A|c] system's exact-Q RREF (the PUBLIC srmech_qmat_rref) reads
 *      the solution.
 *   4. If x exists: R(k) = b(k-1)*x(k)/c(k), reduced. Else: no solution.
 *
 * This file carries its own compact exact-Q polynomial toolkit (the same
 * q_reduce/q_add/q_mul + poly add/mul/divmod/gcd/shift/eval the poly.c peer has,
 * over caller-arena srmech_bigint) and COMPOSES the public srmech_qmat_rref for
 * the linear stage. No malloc (JPL Rule 3): every working carrier + working poly
 * + the divmod/gcd scratch is carved from the caller arena `ws`. Any residual
 * overflow returns SRMECH_ERR_OVERFLOW (never a wrap); the Python op then runs
 * its ceiling-free pure-Q path -- so the standalone-complete honor holds.
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

/* The largest term-ratio / intermediate degree the orchestrator supports. */
#define GOSPER_MAX_DEG 64u

/* A roster of scalar working bigints carved from the caller arena `ws`, plus a
 * poly coefficient pool + the divmod/gcd scratch tail. The carriers mirror
 * poly_ctx_t (qa/qb running rationals, sub a subtract sink, hh the shift/eval
 * scalar, t0/t1 integer scratch, g/rem/rs0/rs1 the reduce-private sinks, z0/z1
 * read-only units). Every carrier is `cap` limbs. */
typedef struct gos_ctx {
    srmech_bigint_t qa_n, qa_d;
    srmech_bigint_t qb_n, qb_d;
    srmech_bigint_t sub_n, sub_d;
    srmech_bigint_t hh_n, hh_d;
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
} gos_ctx_t;

#define GOS_N_CARRIERS 18u  /* qa,qb,sub,hh (x2)=8, t0,t1,g,rem,rs0,rs1,z0,z1=10 */

/* A poly: a parallel (num, den) pair of srmech_bigint arrays + a live length. */
typedef struct gos_poly {
    srmech_bigint_t *n;
    srmech_bigint_t *d;
    size_t           len;
    size_t           cap_terms;
} gos_poly_t;

/* ---- forward declarations (Rule 1: no recursion) ------------------- */
static uint32_t *gos_take(uint32_t *base, size_t words, size_t *cur, size_t cnt);
static srmech_status_t gos_bind(srmech_bigint_t *b, gos_ctx_t *c);
static size_t gos_hdr_words(void);
static srmech_status_t gos_ctx_init(gos_ctx_t *c, uint32_t cap, void *ws,
                                    size_t ws_len);
static srmech_status_t gos_q_reduce(gos_ctx_t *c, srmech_bigint_t *num,
                                    srmech_bigint_t *den);
static srmech_status_t gos_q_add(gos_ctx_t *c, srmech_bigint_t *on,
                                 srmech_bigint_t *od, const srmech_bigint_t *an,
                                 const srmech_bigint_t *ad,
                                 const srmech_bigint_t *bn,
                                 const srmech_bigint_t *bd, int sub);
static srmech_status_t gos_q_mul(gos_ctx_t *c, srmech_bigint_t *on,
                                 srmech_bigint_t *od, const srmech_bigint_t *an,
                                 const srmech_bigint_t *ad,
                                 const srmech_bigint_t *bn,
                                 const srmech_bigint_t *bd);
static size_t gos_trim(const srmech_bigint_t *nums, size_t n);
static srmech_status_t gos_poly_alloc(gos_ctx_t *c, gos_poly_t *p, size_t terms);
static srmech_status_t gos_poly_set_pair(gos_ctx_t *c, gos_poly_t *p, size_t i,
                                         const srmech_bigint_t *n,
                                         const srmech_bigint_t *d);
static srmech_status_t gos_poly_copy(gos_ctx_t *c, gos_poly_t *dst,
                                     const gos_poly_t *src);
static srmech_status_t gos_poly_addsub(gos_ctx_t *c, gos_poly_t *out,
                                       const gos_poly_t *a, const gos_poly_t *b,
                                       int sub);
static srmech_status_t gos_poly_mul(gos_ctx_t *c, gos_poly_t *out,
                                    const gos_poly_t *a, const gos_poly_t *b);
static srmech_status_t gos_rem_step(gos_ctx_t *c, const gos_poly_t *b,
                                    gos_poly_t *q, gos_poly_t *r, size_t *nr,
                                    int want_q);
static srmech_status_t gos_poly_divmod(gos_ctx_t *c, gos_poly_t *q,
                                       gos_poly_t *r, const gos_poly_t *a,
                                       const gos_poly_t *b);
static srmech_status_t gos_poly_monic(gos_ctx_t *c, gos_poly_t *p);
static srmech_status_t gos_poly_gcd(gos_ctx_t *c, gos_poly_t *out,
                                    const gos_poly_t *a, const gos_poly_t *b,
                                    gos_poly_t *sa, gos_poly_t *sb,
                                    gos_poly_t *sr);
static srmech_status_t gos_shift_step(gos_ctx_t *c, gos_poly_t *acc,
                                      const srmech_bigint_t *coeff_n,
                                      const srmech_bigint_t *coeff_d, size_t *deg);
static srmech_status_t gos_poly_shift(gos_ctx_t *c, gos_poly_t *out,
                                      const gos_poly_t *p, int64_t hnum,
                                      int64_t hden);
static srmech_status_t gos_root_bound(gos_ctx_t *c, const gos_poly_t *p,
                                      int64_t *out_bound);
static srmech_status_t gos_dispersion(gos_ctx_t *c, const gos_poly_t *a,
                                      const gos_poly_t *b, gos_poly_t *bs,
                                      gos_poly_t *g, gos_poly_t *s1,
                                      gos_poly_t *s2, gos_poly_t *s3,
                                      int64_t *out_h, size_t *n_h);
static int64_t gos_bigint_to_i64(const srmech_bigint_t *v);
static size_t gos_input_limbs(const srmech_bigint_t *num_n,
                              const srmech_bigint_t *num_d, size_t n_num,
                              const srmech_bigint_t *den_n,
                              const srmech_bigint_t *den_d, size_t n_den);

/* ---- caller-arena carve ------------------------------------------- */

static uint32_t *gos_take(uint32_t *base, size_t words, size_t *cur, size_t cnt)
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

static srmech_status_t gos_bind(srmech_bigint_t *b, gos_ctx_t *c)
{
    uint32_t *limbs;
    assert(b != NULL && c != NULL);
    assert(c->cap > 0u);
    limbs = gos_take(c->pool, c->pool_words, &c->pool_cur, c->cap);
    if (limbs == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    b->limbs = limbs;
    b->cap = c->cap;
    b->n = 0u;
    b->sign = 0;
    return SRMECH_OK;
}

static size_t gos_hdr_words(void)
{
    size_t hw = (sizeof(srmech_bigint_t) + sizeof(uint32_t) - 1u)
                / sizeof(uint32_t);
    assert(sizeof(srmech_bigint_t) > 0u);
    assert(hw >= 1u);
    return hw;
}

/* Bind a bigint header to a fresh `cap`-limb run carved from an arbitrary base
 * (used by the qmat-marshal carve, which bumps the ctx pool tail). */
static srmech_status_t gos_bind_at(srmech_bigint_t *b, uint32_t *base,
                                   size_t words, size_t *cur, uint32_t cap)
{
    uint32_t *limbs = gos_take(base, words, cur, cap);
    assert(b != NULL && cap > 0u);
    assert(base != NULL || words == 0u);
    if (limbs == NULL) { return SRMECH_ERR_OVERFLOW; }
    b->limbs = limbs;
    b->cap = cap;
    b->n = 0u;
    b->sign = 0;
    return SRMECH_OK;
}

static srmech_status_t gos_ctx_init(gos_ctx_t *c, uint32_t cap, void *ws,
                                    size_t ws_len)
{
    uint32_t *base = (uint32_t *)ws;
    size_t words = ws_len / sizeof(uint32_t);
    size_t carrier_words = (size_t)cap * (size_t)GOS_N_CARRIERS;
    size_t scratch_words = (size_t)cap * 8u + 256u;
    srmech_status_t st = SRMECH_OK;
    assert(c != NULL);
    assert((uintptr_t)ws % sizeof(uint32_t) == 0u || ws == NULL);
    c->cap = cap;
    if (words < carrier_words + scratch_words) {
        return SRMECH_ERR_OVERFLOW;
    }
    c->pool = base;
    c->pool_words = words - scratch_words;     /* pool ends where scratch starts */
    c->pool_cur = 0u;
    st |= gos_bind(&c->qa_n, c); st |= gos_bind(&c->qa_d, c);
    st |= gos_bind(&c->qb_n, c); st |= gos_bind(&c->qb_d, c);
    st |= gos_bind(&c->sub_n, c); st |= gos_bind(&c->sub_d, c);
    st |= gos_bind(&c->hh_n, c); st |= gos_bind(&c->hh_d, c);
    st |= gos_bind(&c->t0, c);   st |= gos_bind(&c->t1, c);
    st |= gos_bind(&c->g, c);    st |= gos_bind(&c->rem, c);
    st |= gos_bind(&c->rs0, c);  st |= gos_bind(&c->rs1, c);
    st |= gos_bind(&c->z0, c);   st |= gos_bind(&c->z1, c);
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

/* ---- exact-Q scalar helpers (mirror poly_q_reduce/add/mul) --------- */

static srmech_status_t gos_q_reduce(gos_ctx_t *c, srmech_bigint_t *num,
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

static srmech_status_t gos_q_add(gos_ctx_t *c, srmech_bigint_t *on,
                                 srmech_bigint_t *od, const srmech_bigint_t *an,
                                 const srmech_bigint_t *ad,
                                 const srmech_bigint_t *bn,
                                 const srmech_bigint_t *bd, int sub)
{
    srmech_status_t st;
    assert(c != NULL && on != NULL && od != NULL);
    assert(an != NULL && bn != NULL);
    st = srmech_bigint_mul(&c->t0, an, bd);          /* t0 = an*bd */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_mul(on, bn, ad);              /* on = bn*ad */
    if (st != SRMECH_OK) { return st; }
    if (sub) { st = srmech_bigint_sub(od, &c->t0, on); }
    else     { st = srmech_bigint_add(od, &c->t0, on); }
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(on, od);                 /* num = combined */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_mul(od, ad, bd);              /* den = ad*bd */
    if (st != SRMECH_OK) { return st; }
    return gos_q_reduce(c, on, od);
}

static srmech_status_t gos_q_mul(gos_ctx_t *c, srmech_bigint_t *on,
                                 srmech_bigint_t *od, const srmech_bigint_t *an,
                                 const srmech_bigint_t *ad,
                                 const srmech_bigint_t *bn,
                                 const srmech_bigint_t *bd)
{
    srmech_status_t st;
    assert(c != NULL && on != NULL && od != NULL);
    assert(an != NULL && bn != NULL);
    st = srmech_bigint_mul(on, an, bn);              /* num = an*bn */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_mul(od, ad, bd);              /* den = ad*bd */
    if (st != SRMECH_OK) { return st; }
    return gos_q_reduce(c, on, od);
}

/* ---- poly carve + basic ops (over the ctx pool) ------------------- */

static size_t gos_trim(const srmech_bigint_t *nums, size_t n)
{
    size_t k = n;
    assert(nums != NULL || n == 0u);
    while (k > 0u && srmech_bigint_is_zero(&nums[k - 1u])) { k--; }
    assert(k <= n);                              /* trim never grows the length */
    return k;
}

static srmech_status_t gos_poly_alloc(gos_ctx_t *c, gos_poly_t *p, size_t terms)
{
    size_t hw = gos_hdr_words(), k;
    uint32_t *hn, *hd;
    srmech_status_t st;
    assert(c != NULL && p != NULL);
    assert(terms > 0u);
    hn = gos_take(c->pool, c->pool_words, &c->pool_cur, hw * terms);
    hd = gos_take(c->pool, c->pool_words, &c->pool_cur, hw * terms);
    if (hn == NULL || hd == NULL) { return SRMECH_ERR_OVERFLOW; }
    p->n = (srmech_bigint_t *)(void *)hn;
    p->d = (srmech_bigint_t *)(void *)hd;
    p->len = 0u;
    p->cap_terms = terms;
    for (k = 0u; k < terms; k++) {
        st = gos_bind(&p->n[k], c);
        if (st == SRMECH_OK) { st = gos_bind(&p->d[k], c); }
        if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&p->n[k], 0); }
        if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&p->d[k], 1); }
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

static srmech_status_t gos_poly_set_pair(gos_ctx_t *c, gos_poly_t *p, size_t i,
                                         const srmech_bigint_t *n,
                                         const srmech_bigint_t *d)
{
    srmech_status_t st;
    assert(c != NULL && p != NULL && n != NULL && d != NULL);
    assert(i < p->cap_terms);
    (void)c;
    st = srmech_bigint_copy(&p->n[i], n);
    if (st == SRMECH_OK) { st = srmech_bigint_copy(&p->d[i], d); }
    return st;
}

static srmech_status_t gos_poly_copy(gos_ctx_t *c, gos_poly_t *dst,
                                     const gos_poly_t *src)
{
    size_t k;
    srmech_status_t st;
    assert(c != NULL && dst != NULL && src != NULL);
    assert(dst->cap_terms >= src->len);
    for (k = 0u; k < src->len; k++) {
        st = gos_poly_set_pair(c, dst, k, &src->n[k], &src->d[k]);
        if (st != SRMECH_OK) { return st; }
    }
    dst->len = src->len;
    return SRMECH_OK;
}

static srmech_status_t gos_poly_addsub(gos_ctx_t *c, gos_poly_t *out,
                                       const gos_poly_t *a, const gos_poly_t *b,
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
        st = gos_q_add(c, &out->n[k], &out->d[k], an, ad, bn, bd, sub);
        if (st != SRMECH_OK) { return st; }
    }
    out->len = gos_trim(out->n, m);
    return SRMECH_OK;
}

static srmech_status_t gos_poly_mul(gos_ctx_t *c, gos_poly_t *out,
                                    const gos_poly_t *a, const gos_poly_t *b)
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
            st = gos_q_mul(c, &c->qa_n, &c->qa_d, &a->n[i], &a->d[i],
                           &b->n[j], &b->d[j]);
            if (st == SRMECH_OK) { st = srmech_bigint_copy(&c->qb_n, &out->n[i + j]); }
            if (st == SRMECH_OK) { st = srmech_bigint_copy(&c->qb_d, &out->d[i + j]); }
            if (st == SRMECH_OK) {
                st = gos_q_add(c, &out->n[i + j], &out->d[i + j],
                               &c->qb_n, &c->qb_d, &c->qa_n, &c->qa_d, 0);
            }
            if (st != SRMECH_OK) { return st; }
        }
    }
    out->len = gos_trim(out->n, m);
    return SRMECH_OK;
}

/* r %= b in place (length in *nr), optionally writing q. r distinct from b. */
static srmech_status_t gos_rem_step(gos_ctx_t *c, const gos_poly_t *b,
                                    gos_poly_t *q, gos_poly_t *r, size_t *nr,
                                    int want_q)
{
    srmech_status_t st;
    size_t guard = 0u, nb = b->len;
    assert(c != NULL && b != NULL && r != NULL && nr != NULL && nb > 0u);
    assert(want_q == 0 || q != NULL);            /* a quotient sink iff wanted */
    while (*nr >= nb && *nr > 0u && guard <= (size_t)GOSPER_MAX_DEG * 8u) {
        size_t rdeg = *nr - 1u, shift = rdeg - (nb - 1u), j;
        st = gos_q_mul(c, &c->qa_n, &c->qa_d, &r->n[rdeg], &r->d[rdeg],
                       &b->d[nb - 1u], &b->n[nb - 1u]);   /* factor = lead/lead */
        if (st != SRMECH_OK) { return st; }
        if (want_q) {
            st = srmech_bigint_copy(&q->n[shift], &c->qa_n);
            if (st == SRMECH_OK) { st = srmech_bigint_copy(&q->d[shift], &c->qa_d); }
            if (st != SRMECH_OK) { return st; }
        }
        for (j = 0u; j < nb; j++) {
            st = gos_q_mul(c, &c->qb_n, &c->qb_d, &c->qa_n, &c->qa_d,
                           &b->n[j], &b->d[j]);                  /* factor*b[j] */
            if (st == SRMECH_OK) {
                st = gos_q_add(c, &c->sub_n, &c->sub_d, &r->n[shift + j],
                               &r->d[shift + j], &c->qb_n, &c->qb_d, 1); /* sub */
            }
            if (st == SRMECH_OK) { st = srmech_bigint_copy(&r->n[shift + j], &c->sub_n); }
            if (st == SRMECH_OK) { st = srmech_bigint_copy(&r->d[shift + j], &c->sub_d); }
            if (st != SRMECH_OK) { return st; }
        }
        *nr = gos_trim(r->n, *nr);
        guard++;
    }
    return SRMECH_OK;
}

static srmech_status_t gos_poly_divmod(gos_ctx_t *c, gos_poly_t *q,
                                       gos_poly_t *r, const gos_poly_t *a,
                                       const gos_poly_t *b)
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
        st = gos_poly_set_pair(c, r, k, &a->n[k], &a->d[k]);
        if (st != SRMECH_OK) { return st; }
    }
    nr = gos_trim(r->n, a->len);
    st = gos_rem_step(c, b, q, r, &nr, q != NULL ? 1 : 0);
    if (st != SRMECH_OK) { return st; }
    r->len = nr;
    if (q != NULL) { q->len = gos_trim(q->n, qcap); }
    return SRMECH_OK;
}

static srmech_status_t gos_poly_monic(gos_ctx_t *c, gos_poly_t *p)
{
    size_t k, ld;
    srmech_status_t st;
    assert(c != NULL && p != NULL);
    assert(p->len <= p->cap_terms);
    if (p->len == 0u) { return SRMECH_OK; }
    ld = p->len - 1u;
    for (k = 0u; k < p->len; k++) {
        st = gos_q_mul(c, &c->qa_n, &c->qa_d, &p->n[k], &p->d[k],
                       &p->d[ld], &p->n[ld]);            /* coeff*(d_lead/n_lead) */
        if (st == SRMECH_OK) { st = srmech_bigint_copy(&p->n[k], &c->qa_n); }
        if (st == SRMECH_OK) { st = srmech_bigint_copy(&p->d[k], &c->qa_d); }
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

static srmech_status_t gos_poly_gcd(gos_ctx_t *c, gos_poly_t *out,
                                    const gos_poly_t *a, const gos_poly_t *b,
                                    gos_poly_t *sa, gos_poly_t *sb,
                                    gos_poly_t *sr)
{
    srmech_status_t st;
    size_t guard = 0u, nr;
    assert(c != NULL && out != NULL && a != NULL && b != NULL);
    assert(sa != NULL && sb != NULL && sr != NULL);
    if (a->len >= b->len) {
        st = gos_poly_copy(c, sa, a);
        if (st == SRMECH_OK) { st = gos_poly_copy(c, sb, b); }
    } else {
        st = gos_poly_copy(c, sa, b);
        if (st == SRMECH_OK) { st = gos_poly_copy(c, sb, a); }
    }
    if (st != SRMECH_OK) { return st; }
    while (sb->len > 0u && guard <= (size_t)GOSPER_MAX_DEG * 2u) {
        st = gos_poly_copy(c, sr, sa);                   /* r <- a */
        if (st != SRMECH_OK) { return st; }
        nr = sr->len;
        st = gos_rem_step(c, sb, NULL, sr, &nr, 0);      /* r %= b */
        if (st != SRMECH_OK) { return st; }
        sr->len = nr;
        st = gos_poly_monic(c, sr);                      /* monic -- the taming lever */
        if (st != SRMECH_OK) { return st; }
        st = gos_poly_copy(c, sa, sb);                   /* a <- b */
        if (st == SRMECH_OK) { st = gos_poly_copy(c, sb, sr); }   /* b <- r */
        if (st != SRMECH_OK) { return st; }
        guard++;
    }
    st = gos_poly_monic(c, sa);
    if (st != SRMECH_OK) { return st; }
    return gos_poly_copy(c, out, sa);
}

/* One synthetic-Horner step: acc <- acc*(k + h) + coeff, h in c->hh_n/c->hh_d. */
static srmech_status_t gos_shift_step(gos_ctx_t *c, gos_poly_t *acc,
                                      const srmech_bigint_t *coeff_n,
                                      const srmech_bigint_t *coeff_d, size_t *deg)
{
    size_t i, nd = (*deg) + 1u;
    srmech_status_t st;
    assert(c != NULL && acc != NULL && coeff_n != NULL && deg != NULL);
    assert(nd <= acc->cap_terms);
    for (i = nd; i > 0u; i--) {
        size_t idx = i - 1u;
        if (idx < *deg) {
            st = gos_q_mul(c, &c->qa_n, &c->qa_d, &c->hh_n, &c->hh_d,
                           &acc->n[idx], &acc->d[idx]);          /* h*acc[idx] */
        } else {
            st = srmech_bigint_set_i64(&c->qa_n, 0);
            if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&c->qa_d, 1); }
        }
        if (st != SRMECH_OK) { return st; }
        if (idx > 0u) {
            st = gos_q_add(c, &acc->n[idx], &acc->d[idx], &c->qa_n, &c->qa_d,
                           &acc->n[idx - 1u], &acc->d[idx - 1u], 0);
        } else {
            st = gos_q_add(c, &acc->n[idx], &acc->d[idx], &c->qa_n, &c->qa_d,
                           coeff_n, coeff_d, 0);                 /* new[0]=h*acc[0]+coeff */
        }
        if (st != SRMECH_OK) { return st; }
    }
    *deg = nd;
    return SRMECH_OK;
}

static srmech_status_t gos_poly_shift(gos_ctx_t *c, gos_poly_t *out,
                                      const gos_poly_t *p, int64_t hnum,
                                      int64_t hden)
{
    size_t k, deg = 0u;
    srmech_status_t st;
    assert(c != NULL && out != NULL && p != NULL);
    assert(hden != 0);
    st = srmech_bigint_set_i64(&c->hh_n, hnum);          /* h = hnum/hden */
    if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&c->hh_d, hden); }
    if (st != SRMECH_OK) { return st; }
    if (p->len == 0u) { out->len = 0u; return SRMECH_OK; }
    assert(out->cap_terms >= p->len);
    out->len = 0u;
    for (k = p->len; k > 0u; k--) {
        st = gos_shift_step(c, out, &p->n[k - 1u], &p->d[k - 1u], &deg);
        if (st != SRMECH_OK) { return st; }
    }
    out->len = gos_trim(out->n, deg);
    return SRMECH_OK;
}


/* ===================================================================
 * DISPERSION (the GP-form's only consumer): the sorted non-negative integer
 * shifts h with deg gcd(a(k), b(k+h)) >= 1. A common root of a(k), b(k+h) forces
 * h = (root of b) - (root of a), bounded by the Cauchy root bounds of a and b.
 * Each integer h in 0..rootbound(a)+rootbound(b) is tested with the exact poly
 * gcd/shift -- the SAME shifts the Python _dispersion finds.
 * =================================================================== */

static int64_t gos_bigint_to_i64(const srmech_bigint_t *v)
{
    int64_t r;
    assert(v != NULL);
    assert(v->n <= v->cap);
    if (v->n == 0u) { return 0; }
    r = (int64_t)v->limbs[0];
    if (v->n >= 2u) { r |= ((int64_t)v->limbs[1]) << 32; }
    return (v->sign < 0) ? -r : r;
}

/* The integer Cauchy root bound 1 + ceil(max_i |c_i / c_lead|) of p. */
static srmech_status_t gos_root_bound(gos_ctx_t *c, const gos_poly_t *p,
                                      int64_t *out_bound)
{
    size_t k;
    srmech_status_t st;
    int64_t best = 1;
    assert(c != NULL && p != NULL && out_bound != NULL);
    assert(p->len <= p->cap_terms);
    if (p->len <= 1u) { *out_bound = 1; return SRMECH_OK; }
    for (k = 0u; k + 1u < p->len; k++) {
        st = gos_q_mul(c, &c->qa_n, &c->qa_d, &p->n[k], &p->d[k],
                       &p->d[p->len - 1u], &p->n[p->len - 1u]);    /* c_k / c_lead */
        if (st != SRMECH_OK) { return st; }
        if (c->qa_n.sign < 0) { c->qa_n.sign = -c->qa_n.sign; }    /* |.| Class-K */
        /* ceil(|num|/den) = (|num| + den - 1) / den */
        st = srmech_bigint_add(&c->t0, &c->qa_n, &c->qa_d);
        if (st == SRMECH_OK) { st = srmech_bigint_sub(&c->sub_n, &c->t0, &c->z1); }
        if (st == SRMECH_OK) {
            st = srmech_bigint_divmod(&c->rs0, &c->rem, &c->sub_n, &c->qa_d,
                                      c->scratch, c->scratch_len);
        }
        if (st != SRMECH_OK) { return st; }
        if (c->rs0.n <= 2u) {
            int64_t v = gos_bigint_to_i64(&c->rs0);
            if (v > best) { best = v; }
        } else {
            best = (int64_t)GOSPER_MAX_DEG * 4096;                 /* a large cap */
        }
    }
    *out_bound = best + 1;
    return SRMECH_OK;
}

static srmech_status_t gos_dispersion(gos_ctx_t *c, const gos_poly_t *a,
                                      const gos_poly_t *b, gos_poly_t *bs,
                                      gos_poly_t *g, gos_poly_t *s1,
                                      gos_poly_t *s2, gos_poly_t *s3,
                                      int64_t *out_h, size_t *n_h)
{
    int64_t ra = 0, rb = 0, hmax, h;
    srmech_status_t st;
    size_t cnt = 0u;
    assert(c != NULL && a != NULL && b != NULL && out_h != NULL && n_h != NULL);
    assert(bs != NULL && g != NULL);
    *n_h = 0u;
    if (a->len < 2u || b->len < 2u) { return SRMECH_OK; }   /* a const shares none */
    st = gos_root_bound(c, a, &ra);
    if (st == SRMECH_OK) { st = gos_root_bound(c, b, &rb); }
    if (st != SRMECH_OK) { return st; }
    hmax = ra + rb;
    if (hmax > (int64_t)GOSPER_MAX_DEG * 8192) { hmax = (int64_t)GOSPER_MAX_DEG * 8192; }
    for (h = 0; h <= hmax; h++) {
        st = gos_poly_shift(c, bs, b, h, 1);                /* bs = b(k+h) */
        if (st == SRMECH_OK) { st = gos_poly_gcd(c, g, a, bs, s1, s2, s3); }
        if (st != SRMECH_OK) { return st; }
        if (g->len >= 2u) {                                 /* deg gcd >= 1 */
            if (cnt >= (size_t)GOSPER_MAX_DEG * 4u) { return SRMECH_ERR_OVERFLOW; }
            out_h[cnt++] = h;
        }
    }
    *n_h = cnt;
    return SRMECH_OK;
}

/* ---- input limb estimate + arena bounds --------------------------- */

static size_t gos_input_limbs(const srmech_bigint_t *num_n,
                              const srmech_bigint_t *num_d, size_t n_num,
                              const srmech_bigint_t *den_n,
                              const srmech_bigint_t *den_d, size_t n_den)
{
    size_t k, cl = 1u;
    assert(num_n != NULL || n_num == 0u);
    assert(den_n != NULL || n_den == 0u);
    for (k = 0u; k < n_num; k++) {
        if (num_n[k].n > cl) { cl = num_n[k].n; }
        if (num_d[k].n > cl) { cl = num_d[k].n; }
    }
    for (k = 0u; k < n_den; k++) {
        if (den_n[k].n > cl) { cl = den_n[k].n; }
        if (den_d[k].n > cl) { cl = den_d[k].n; }
    }
    return cl;
}

static size_t gos_cap_for(size_t coeff_limbs, size_t degree)
{
    size_t cl = (coeff_limbs == 0u) ? 1u : coeff_limbs;
    size_t dg = (degree == 0u) ? 1u : degree;
    /* the GP-form + degree-bounded Q solve accumulate Q products over a degree-
     * scaled chain; a deg^2-scaled per-coefficient envelope with a generous
     * unreduced-cross-product x2 dominates the worst intermediate. */
    size_t step = cl * (dg * dg + dg + 2u) + 4u;
    size_t cap = step * 2u + cl * 2u + 64u;
    assert(cap >= step);
    assert(cap >= cl);
    return cap;
}

size_t srmech_gosper_out_cap(size_t coeff_limbs, size_t degree)
{
    size_t cap = gos_cap_for(coeff_limbs, degree);
    assert(cap >= 2u);
    assert(cap >= coeff_limbs);
    return cap;
}

/* The number of coefficient slots each working poly carries (the GP-form / solve
 * intermediates never exceed this). */
static size_t gos_terms_for(size_t degree)
{
    size_t dg = (degree == 0u) ? 1u : degree;
    size_t terms = dg * dg + dg + 6u;
    assert(terms >= dg);
    assert(terms >= 6u);
    return terms;
}

size_t srmech_gosper_ws_bound(size_t coeff_limbs, size_t degree)
{
    size_t dg = (degree == 0u) ? 1u : degree;
    size_t cap = gos_cap_for(coeff_limbs, dg);
    size_t hw = gos_hdr_words();
    size_t terms = gos_terms_for(dg);
    size_t polys = 20u;                       /* the named working-poly roster   */
    size_t header_words = 2u * hw * terms * polys;
    size_t limb_words = 2u * terms * cap * polys;
    size_t carriers = (size_t)cap * (size_t)GOS_N_CARRIERS;
    size_t scratch = (size_t)cap * 8u + 256u;
    /* the qmat-marshal region carved from the pool tail: the augmented system is
     * n_rows x total with n_rows <= deg^2+1, total <= deg+2; 4 entry arrays of
     * srmech_qmat_entry_cap limbs each + headers + the qmat ws-bound. */
    size_t n_rows = dg * dg + 1u, total = dg + 2u, cells = n_rows * total;
    size_t ecap = srmech_qmat_entry_cap(cap, n_rows, total);
    size_t qmarshal = 4u * cells * (ecap + hw) + 16u;
    size_t qws = srmech_qmat_ws_bound(cap, n_rows, total) / sizeof(uint32_t);
    size_t hbuf = (sizeof(int64_t) / sizeof(uint32_t)) * ((size_t)GOSPER_MAX_DEG * 4u + 4u);
    size_t words = header_words + limb_words + carriers + scratch
                   + qmarshal + qws + hbuf + 256u;
    assert(cap >= 2u);
    assert(words >= limb_words);
    return words * sizeof(uint32_t);
}

/* ===================================================================
 * The orchestrating run: GP-form + degree-bounded undetermined-coefficient solve
 * (the exact-Q RREF delegated to the PUBLIC srmech_qmat_rref) + R = b(k-1)x/c.
 * The named working-poly roster is carved up-front from the ctx pool.
 * =================================================================== */

/* The working-poly roster (20 polys; each `terms` slots wide). */
typedef struct gos_work {
    gos_poly_t a, b, cc;          /* the GP-form a/b/c            */
    gos_poly_t g, bs;             /* gcd + shifted-b scratch      */
    gos_poly_t gq, gs;            /* divmod q/r scratch           */
    gos_poly_t s1, s2, s3;        /* gcd internal scratch (sa/sb/sr) */
    gos_poly_t bm, sp, dp;        /* b(k-1), a+bm, a-bm           */
    gos_poly_t kp, kp1, col;      /* k^j, (k+1)^j, column poly    */
    gos_poly_t x, rn, t1;         /* the solution x, R numerator, temp */
} gos_work_t;

/* forward declarations for the run/solve roster (Rule 1: no recursion) */
static srmech_status_t gos_gp_form(gos_ctx_t *c, gos_work_t *w, int64_t *hbuf);
static srmech_status_t gos_degree_bound(gos_ctx_t *c, gos_work_t *w,
                                        int *out_deg);
static srmech_status_t gos_build_col(gos_ctx_t *c, gos_work_t *w, size_t j,
                                     size_t *max_deg);
static srmech_status_t gos_qmat_solve(gos_ctx_t *c, gos_work_t *w, size_t n_rows,
                                      size_t n_cols, int *out_ok);
static srmech_status_t gos_read_solution(gos_ctx_t *c, gos_work_t *w,
                                         const srmech_bigint_t *o_n,
                                         const srmech_bigint_t *o_d, size_t n_rows,
                                         size_t n_cols, size_t total, int *out_ok);
static srmech_status_t gos_fill_aug(gos_ctx_t *c, gos_work_t *w,
                                    srmech_bigint_t *a_n, srmech_bigint_t *a_d,
                                    size_t n_rows, size_t n_cols, size_t total);
static srmech_status_t gos_finish_cert(gos_ctx_t *c, gos_work_t *w, int *out_has,
                                       srmech_bigint_t *rn_n,
                                       srmech_bigint_t *rn_d, size_t *out_rnum,
                                       srmech_bigint_t *rd_n,
                                       srmech_bigint_t *rd_d, size_t *out_rden);
static srmech_status_t gos_run(gos_ctx_t *c, gos_work_t *w, size_t deg,
                               int *out_has, srmech_bigint_t *rn_n,
                               srmech_bigint_t *rn_d, size_t *out_rnum,
                               srmech_bigint_t *rd_n, srmech_bigint_t *rd_d,
                               size_t *out_rden);

static srmech_status_t gos_alloc_all(gos_ctx_t *c, gos_work_t *w, size_t terms)
{
    srmech_status_t st = SRMECH_OK;
    assert(c != NULL && w != NULL);
    assert(terms > 0u);
    st |= gos_poly_alloc(c, &w->a, terms);   st |= gos_poly_alloc(c, &w->b, terms);
    st |= gos_poly_alloc(c, &w->cc, terms);  st |= gos_poly_alloc(c, &w->g, terms);
    st |= gos_poly_alloc(c, &w->bs, terms);  st |= gos_poly_alloc(c, &w->gq, terms);
    st |= gos_poly_alloc(c, &w->gs, terms);  st |= gos_poly_alloc(c, &w->s1, terms);
    st |= gos_poly_alloc(c, &w->s2, terms);  st |= gos_poly_alloc(c, &w->s3, terms);
    st |= gos_poly_alloc(c, &w->bm, terms);  st |= gos_poly_alloc(c, &w->sp, terms);
    st |= gos_poly_alloc(c, &w->dp, terms);  st |= gos_poly_alloc(c, &w->kp, terms);
    st |= gos_poly_alloc(c, &w->kp1, terms); st |= gos_poly_alloc(c, &w->col, terms);
    st |= gos_poly_alloc(c, &w->x, terms);   st |= gos_poly_alloc(c, &w->rn, terms);
    st |= gos_poly_alloc(c, &w->t1, terms);
    return (st != SRMECH_OK) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* Load an input (num, den) coefficient array into poly p (trimmed). */
static srmech_status_t gos_load_input(gos_ctx_t *c, gos_poly_t *p,
                                      const srmech_bigint_t *cn,
                                      const srmech_bigint_t *cd, size_t n)
{
    size_t k;
    srmech_status_t st;
    assert(c != NULL && p != NULL);
    assert(n <= p->cap_terms);
    for (k = 0u; k < n; k++) {
        st = gos_poly_set_pair(c, p, k, &cn[k], &cd[k]);
        if (st != SRMECH_OK) { return st; }
    }
    p->len = gos_trim(p->n, n);
    return SRMECH_OK;
}

/* The Gosper-Petkovsek normal form, in place over w->a / w->b / w->cc. */
static srmech_status_t gos_gp_form(gos_ctx_t *c, gos_work_t *w, int64_t *hbuf)
{
    size_t n_h, guard = 0u, j;
    int64_t h;
    srmech_status_t st;
    assert(c != NULL && w != NULL && hbuf != NULL);
    assert(w->cc.cap_terms >= 1u);
    st = srmech_bigint_set_i64(&w->cc.n[0], 1);          /* cc = 1 */
    if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&w->cc.d[0], 1); }
    if (st != SRMECH_OK) { return st; }
    w->cc.len = 1u;
    while (guard <= (size_t)GOSPER_MAX_DEG * 2u) {
        st = gos_dispersion(c, &w->a, &w->b, &w->bs, &w->g, &w->s1, &w->s2,
                            &w->s3, hbuf, &n_h);
        if (st != SRMECH_OK) { return st; }
        if (n_h == 0u) { break; }
        h = hbuf[0];                                     /* smallest dispersion */
        st = gos_poly_shift(c, &w->bs, &w->b, h, 1);     /* bs = b(k+h) */
        if (st == SRMECH_OK) { st = gos_poly_gcd(c, &w->g, &w->a, &w->bs,
                                                  &w->s1, &w->s2, &w->s3); }
        if (st != SRMECH_OK) { return st; }
        if (w->g.len < 2u) { break; }
        st = gos_poly_divmod(c, &w->gq, &w->gs, &w->a, &w->g);  /* a /= g(k) */
        if (st == SRMECH_OK) { st = gos_poly_copy(c, &w->a, &w->gq); }
        if (st == SRMECH_OK) { st = gos_poly_shift(c, &w->t1, &w->g, -h, 1); } /* g(k-h) */
        if (st == SRMECH_OK) { st = gos_poly_divmod(c, &w->gq, &w->gs, &w->b, &w->t1); }
        if (st == SRMECH_OK) { st = gos_poly_copy(c, &w->b, &w->gq); }   /* b /= g(k-h) */
        if (st != SRMECH_OK) { return st; }
        for (j = 1u; (int64_t)j <= h; j++) {             /* cc *= g(k-j) */
            st = gos_poly_shift(c, &w->t1, &w->g, -(int64_t)j, 1);
            if (st == SRMECH_OK) { st = gos_poly_mul(c, &w->s1, &w->cc, &w->t1); }
            if (st == SRMECH_OK) { st = gos_poly_copy(c, &w->cc, &w->s1); }
            if (st != SRMECH_OK) { return st; }
        }
        guard++;
    }
    return SRMECH_OK;
}

/* The candidate degree -2 lc(d)/lc(s): set *cand to it iff a non-negative int. */
static srmech_status_t gos_lc_ratio_cand(gos_ctx_t *c, const gos_poly_t *s,
                                         const gos_poly_t *d, int64_t *cand)
{
    srmech_status_t st;
    assert(c != NULL && s != NULL && d != NULL && cand != NULL);
    assert(s->len <= s->cap_terms && d->len <= d->cap_terms);
    *cand = -1;
    if (s->len == 0u || d->len == 0u) { return SRMECH_OK; }
    st = srmech_bigint_set_i64(&c->t0, -2);
    if (st == SRMECH_OK) { st = gos_q_mul(c, &c->qa_n, &c->qa_d, &c->t0, &c->z1,
                                          &d->n[d->len - 1u], &d->d[d->len - 1u]); }
    if (st == SRMECH_OK) { st = srmech_bigint_copy(&c->sub_n, &c->qa_n); }
    if (st == SRMECH_OK) { st = srmech_bigint_copy(&c->sub_d, &c->qa_d); }
    if (st == SRMECH_OK) { st = gos_q_mul(c, &c->qa_n, &c->qa_d, &c->sub_n, &c->sub_d,
                                          &s->d[s->len - 1u], &s->n[s->len - 1u]); }
    if (st != SRMECH_OK) { return st; }
    if (c->qa_d.n == 1u && c->qa_d.limbs[0] == 1u && c->qa_n.sign >= 0
        && c->qa_n.n <= 2u) {
        *cand = gos_bigint_to_i64(&c->qa_n);
    }
    return SRMECH_OK;
}

/* The Gosper degree bound on x (PWZ section 5.3). bm = b(k-1) must be in w->bm. */
static srmech_status_t gos_degree_bound(gos_ctx_t *c, gos_work_t *w, int *out_deg)
{
    int dc, da, ds, dd, base;
    int64_t bcand = -1;
    srmech_status_t st;
    assert(c != NULL && w != NULL && out_deg != NULL);
    assert(w->a.len <= w->a.cap_terms);
    st = gos_poly_addsub(c, &w->sp, &w->a, &w->bm, 0);   /* s = a + bm */
    if (st == SRMECH_OK) { st = gos_poly_addsub(c, &w->dp, &w->a, &w->bm, 1); } /* d=a-bm */
    if (st != SRMECH_OK) { return st; }
    dc = (int)w->cc.len - 1; da = (int)w->a.len - 1;
    ds = (int)w->sp.len - 1; dd = (int)w->dp.len - 1;
    if (w->dp.len == 0u) {                               /* a == bm */
        *out_deg = dc - da + 1;
        return SRMECH_OK;
    }
    if (dd >= ds) { *out_deg = dc - dd; return SRMECH_OK; }
    st = gos_lc_ratio_cand(c, &w->sp, &w->dp, &bcand);
    if (st != SRMECH_OK) { return st; }
    base = dc - ds + 1;
    *out_deg = (bcand >= 0 && bcand > (int64_t)base) ? (int)bcand : base;
    return SRMECH_OK;
}

/* ===================================================================
 * The undetermined-coefficient linear solve. Build the augmented [A|c] matrix
 * (row r, col j = coeff of k^r in P_j(k) = a(k)*(k+1)^j - b(k-1)*k^j; last col =
 * c[r]) as ROW-MAJOR srmech_bigint arrays, RREF it via the PUBLIC srmech_qmat_rref,
 * and read the solution x_j from the pivots (free cols -> 0; a pivot in the RHS
 * col -> inconsistent -> no solution). Carves the qmat marshalling arrays + the
 * qmat working arena from the ctx pool tail (a fresh slice, since the ctx pool is
 * a bump region and the working polys are still live).
 * =================================================================== */

/* Build column j's polynomial P_j = a*(k+1)^j - b(k-1)*k^j into w->col, tracking
 * the running k^j in w->kp. On entry w->kp holds k^j; on exit it holds k^(j+1). */
static srmech_status_t gos_build_col(gos_ctx_t *c, gos_work_t *w, size_t j,
                                     size_t *max_deg)
{
    srmech_status_t st;
    size_t k;
    assert(c != NULL && w != NULL && max_deg != NULL);
    assert(w->kp.cap_terms >= 2u);
    if (j == 0u) {                                       /* k^0 = 1 */
        st = srmech_bigint_set_i64(&w->kp.n[0], 1);
        if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&w->kp.d[0], 1); }
        if (st != SRMECH_OK) { return st; }
        w->kp.len = 1u;
    } else {                                             /* k^j = k^(j-1) * k */
        st = srmech_bigint_set_i64(&w->t1.n[0], 0);
        if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&w->t1.d[0], 1); }
        if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&w->t1.n[1], 1); }
        if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&w->t1.d[1], 1); }
        if (st != SRMECH_OK) { return st; }
        w->t1.len = 2u;                                  /* the monomial k */
        st = gos_poly_mul(c, &w->s1, &w->kp, &w->t1);    /* k^j = k^(j-1)*k */
        if (st == SRMECH_OK) { st = gos_poly_copy(c, &w->kp, &w->s1); }
        if (st != SRMECH_OK) { return st; }
    }
    st = gos_poly_shift(c, &w->kp1, &w->kp, 1, 1);       /* (k+1)^j */
    if (st == SRMECH_OK) { st = gos_poly_mul(c, &w->s2, &w->a, &w->kp1); }  /* a*(k+1)^j */
    if (st == SRMECH_OK) { st = gos_poly_mul(c, &w->s3, &w->bm, &w->kp); }  /* bm*k^j */
    if (st == SRMECH_OK) { st = gos_poly_addsub(c, &w->col, &w->s2, &w->s3, 1); }
    if (st != SRMECH_OK) { return st; }
    for (k = 0u; k < w->col.len; k++) { if (k > *max_deg) { *max_deg = k; } }
    return SRMECH_OK;
}

/* Carve the qmat marshalling arrays (a_n/a_d, n_rows*total cells; o_n/o_d same;
 * piv) + the qmat working arena from a FRESH slice of the ctx pool tail, then
 * solve the augmented system. *out_ok set 0 when inconsistent. x_out receives
 * the solution coefficients (n_cols of them, ascending). */
static srmech_status_t gos_qmat_solve(gos_ctx_t *c, gos_work_t *w, size_t n_rows,
                                      size_t n_cols, int *out_ok)
{
    size_t total = n_cols + 1u, cells = n_rows * total, hw = gos_hdr_words();
    size_t cl, ecap, ws_words, i, rank = 0u;
    uint32_t *base = c->pool;
    uint32_t *hn, *hd, *on, *od;
    srmech_bigint_t *a_n, *a_d, *o_n, *o_d;
    size_t *piv;
    void *qws;
    srmech_status_t st;
    assert(c != NULL && w != NULL && out_ok != NULL);
    assert(n_rows > 0u && n_cols > 0u);
    *out_ok = 1;
    cl = (size_t)c->cap;
    ecap = srmech_qmat_entry_cap(cl, n_rows, total);
    ws_words = srmech_qmat_ws_bound(cl, n_rows, total) / sizeof(uint32_t);
    /* carve the qmat marshalling from the ctx POOL bump tail (after the working
     * polys; the divmod scratch is a separate region at the very end). */
    hn = gos_take(base, c->pool_words, &c->pool_cur, hw * cells);
    hd = gos_take(base, c->pool_words, &c->pool_cur, hw * cells);
    on = gos_take(base, c->pool_words, &c->pool_cur, hw * cells);
    od = gos_take(base, c->pool_words, &c->pool_cur, hw * cells);
    piv = (size_t *)(void *)gos_take(base, c->pool_words, &c->pool_cur,
                                     (sizeof(size_t) / sizeof(uint32_t)) * total + 2u);
    if (hn == NULL || hd == NULL || on == NULL || od == NULL || piv == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    a_n = (srmech_bigint_t *)(void *)hn; a_d = (srmech_bigint_t *)(void *)hd;
    o_n = (srmech_bigint_t *)(void *)on; o_d = (srmech_bigint_t *)(void *)od;
    for (i = 0u; i < cells; i++) {
        st = gos_bind_at(&a_n[i], base, c->pool_words, &c->pool_cur, (uint32_t)ecap);
        if (st == SRMECH_OK) { st = gos_bind_at(&a_d[i], base, c->pool_words, &c->pool_cur, (uint32_t)ecap); }
        if (st == SRMECH_OK) { st = gos_bind_at(&o_n[i], base, c->pool_words, &c->pool_cur, (uint32_t)ecap); }
        if (st == SRMECH_OK) { st = gos_bind_at(&o_d[i], base, c->pool_words, &c->pool_cur, (uint32_t)ecap); }
        if (st != SRMECH_OK) { return st; }
    }
    qws = (void *)gos_take(base, c->pool_words, &c->pool_cur, ws_words);
    if (qws == NULL) { return SRMECH_ERR_OVERFLOW; }
    st = gos_fill_aug(c, w, a_n, a_d, n_rows, n_cols, total);
    if (st != SRMECH_OK) { return st; }
    st = srmech_qmat_rref(a_n, a_d, n_rows, total, o_n, o_d, &rank, piv,
                          qws, ws_words * sizeof(uint32_t));
    if (st != SRMECH_OK) { return st; }
    return gos_read_solution(c, w, o_n, o_d, n_rows, n_cols, total, out_ok);
}

/* Read the solution x from the RREF output o_n/o_d (mirrors the Python pivot
 * read): each pivot col < n_cols -> the RHS entry; free cols -> 0; a pivot in
 * the RHS col -> inconsistent (*out_ok = 0). */
static srmech_status_t gos_read_solution(gos_ctx_t *c, gos_work_t *w,
                                         const srmech_bigint_t *o_n,
                                         const srmech_bigint_t *o_d, size_t n_rows,
                                         size_t n_cols, size_t total, int *out_ok)
{
    size_t j, r;
    srmech_status_t st;
    assert(c != NULL && w != NULL && o_n != NULL && out_ok != NULL);
    assert(total == n_cols + 1u);
    for (j = 0u; j < n_cols; j++) {
        st = srmech_bigint_set_i64(&w->x.n[j], 0);
        if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&w->x.d[j], 1); }
        if (st != SRMECH_OK) { return st; }
    }
    w->x.len = n_cols;
    for (r = 0u; r < n_rows; r++) {
        size_t pcol = total;                             /* total == "none" */
        for (j = 0u; j < total; j++) {
            if (!srmech_bigint_is_zero(&o_n[r * total + j])) { pcol = j; break; }
        }
        if (pcol == total) { continue; }                 /* all-zero row */
        if (pcol == n_cols) { *out_ok = 0; return SRMECH_OK; }   /* inconsistent */
        st = srmech_bigint_copy(&w->x.n[pcol], &o_n[r * total + n_cols]);
        if (st == SRMECH_OK) { st = srmech_bigint_copy(&w->x.d[pcol], &o_d[r * total + n_cols]); }
        if (st != SRMECH_OK) { return st; }
    }
    w->x.len = gos_trim(w->x.n, n_cols);
    return SRMECH_OK;
}

/* Fill the augmented [A|c] matrix a_n/a_d (row-major, total wide): col j (j <
 * n_cols) is P_j's coeff of k^r; the last col is c[r]. Rebuilds each P_j via
 * gos_build_col, writing its coefficients column-by-column. */
static srmech_status_t gos_fill_aug(gos_ctx_t *c, gos_work_t *w,
                                    srmech_bigint_t *a_n, srmech_bigint_t *a_d,
                                    size_t n_rows, size_t n_cols, size_t total)
{
    size_t j, r, dummy = 0u;
    srmech_status_t st;
    assert(c != NULL && w != NULL && a_n != NULL && a_d != NULL);
    assert(total >= n_cols + 1u);
    for (j = 0u; j < n_cols; j++) {
        st = gos_build_col(c, w, j, &dummy);
        if (st != SRMECH_OK) { return st; }
        for (r = 0u; r < n_rows; r++) {
            const srmech_bigint_t *cn = (r < w->col.len) ? &w->col.n[r] : &c->z0;
            const srmech_bigint_t *cd = (r < w->col.len) ? &w->col.d[r] : &c->z1;
            st = srmech_bigint_copy(&a_n[r * total + j], cn);
            if (st == SRMECH_OK) { st = srmech_bigint_copy(&a_d[r * total + j], cd); }
            if (st != SRMECH_OK) { return st; }
        }
    }
    for (r = 0u; r < n_rows; r++) {                      /* the RHS column = c[r] */
        const srmech_bigint_t *cn = (r < w->cc.len) ? &w->cc.n[r] : &c->z0;
        const srmech_bigint_t *cd = (r < w->cc.len) ? &w->cc.d[r] : &c->z1;
        st = srmech_bigint_copy(&a_n[r * total + n_cols], cn);
        if (st == SRMECH_OK) { st = srmech_bigint_copy(&a_d[r * total + n_cols], cd); }
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* The orchestrating run (factored to keep srmech_gosper short). */
static srmech_status_t gos_run(gos_ctx_t *c, gos_work_t *w, size_t deg,
                               int *out_has, srmech_bigint_t *rn_n,
                               srmech_bigint_t *rn_d, size_t *out_rnum,
                               srmech_bigint_t *rd_n, srmech_bigint_t *rd_d,
                               size_t *out_rden)
{
    int deg_bound, ok = 1;
    int64_t *hbuf;
    size_t n_rows, n_cols, max_deg = 0u, j;
    srmech_status_t st;
    assert(c != NULL && w != NULL && out_has != NULL);
    assert(rn_n != NULL && rd_n != NULL);
    (void)deg;
    *out_has = 0;
    hbuf = (int64_t *)(void *)gos_take(c->pool, c->pool_words, &c->pool_cur,
                                       (sizeof(int64_t) / sizeof(uint32_t))
                                       * ((size_t)GOSPER_MAX_DEG * 4u + 4u));
    if (hbuf == NULL) { return SRMECH_ERR_OVERFLOW; }
    st = gos_gp_form(c, w, hbuf);
    if (st != SRMECH_OK) { return st; }
    st = gos_poly_shift(c, &w->bm, &w->b, -1, 1);        /* bm = b(k-1) */
    if (st != SRMECH_OK) { return st; }
    st = gos_degree_bound(c, w, &deg_bound);
    if (st != SRMECH_OK) { return st; }
    if (deg_bound < 0) { *out_has = 0; return SRMECH_OK; }
    n_cols = (size_t)deg_bound + 1u;
    /* determine n_rows = max(deg c, deg of any P_j) + 1 by a dry pass */
    for (j = 0u; j < n_cols; j++) {
        st = gos_build_col(c, w, j, &max_deg);
        if (st != SRMECH_OK) { return st; }
    }
    if (w->cc.len > max_deg + 1u) { max_deg = w->cc.len - 1u; }
    n_rows = max_deg + 1u;
    st = gos_qmat_solve(c, w, n_rows, n_cols, &ok);
    if (st != SRMECH_OK) { return st; }
    if (!ok || w->x.len == 0u) { *out_has = 0; return SRMECH_OK; }
    return gos_finish_cert(c, w, out_has, rn_n, rn_d, out_rnum,
                           rd_n, rd_d, out_rden);
}

/* R = b(k-1)*x / c, reduced; written to the caller's r_* arrays. */
static srmech_status_t gos_finish_cert(gos_ctx_t *c, gos_work_t *w, int *out_has,
                                       srmech_bigint_t *rn_n,
                                       srmech_bigint_t *rn_d, size_t *out_rnum,
                                       srmech_bigint_t *rd_n,
                                       srmech_bigint_t *rd_d, size_t *out_rden)
{
    size_t k;
    srmech_status_t st;
    assert(c != NULL && w != NULL && out_has != NULL);
    assert(rn_n != NULL && rd_n != NULL && out_rnum != NULL && out_rden != NULL);
    st = gos_poly_mul(c, &w->rn, &w->bm, &w->x);         /* rn = b(k-1)*x */
    if (st != SRMECH_OK) { return st; }
    /* reduce rn / cc by their gcd */
    st = gos_poly_gcd(c, &w->g, &w->rn, &w->cc, &w->s1, &w->s2, &w->s3);
    if (st != SRMECH_OK) { return st; }
    if (w->g.len >= 2u) {
        st = gos_poly_divmod(c, &w->gq, &w->gs, &w->rn, &w->g);
        if (st == SRMECH_OK) { st = gos_poly_copy(c, &w->rn, &w->gq); }
        if (st == SRMECH_OK) { st = gos_poly_divmod(c, &w->gq, &w->gs, &w->cc, &w->g); }
        if (st == SRMECH_OK) { st = gos_poly_copy(c, &w->cc, &w->gq); }
        if (st != SRMECH_OK) { return st; }
    }
    for (k = 0u; k < w->rn.len; k++) {
        st = srmech_bigint_copy(&rn_n[k], &w->rn.n[k]);
        if (st == SRMECH_OK) { st = srmech_bigint_copy(&rn_d[k], &w->rn.d[k]); }
        if (st != SRMECH_OK) { return st; }
    }
    for (k = 0u; k < w->cc.len; k++) {
        st = srmech_bigint_copy(&rd_n[k], &w->cc.n[k]);
        if (st == SRMECH_OK) { st = srmech_bigint_copy(&rd_d[k], &w->cc.d[k]); }
        if (st != SRMECH_OK) { return st; }
    }
    *out_rnum = w->rn.len;
    *out_rden = w->cc.len;
    *out_has = 1;
    return SRMECH_OK;
}

/* ---- the public entry --------------------------------------------- */

srmech_status_t srmech_gosper(const srmech_bigint_t *num_n,
                              const srmech_bigint_t *num_d, size_t n_num,
                              const srmech_bigint_t *den_n,
                              const srmech_bigint_t *den_d, size_t n_den,
                              int *out_has_solution,
                              srmech_bigint_t *r_num_n, srmech_bigint_t *r_num_d,
                              size_t *out_rnum,
                              srmech_bigint_t *r_den_n, srmech_bigint_t *r_den_d,
                              size_t *out_rden,
                              void *ws, size_t ws_len)
{
    gos_ctx_t c;
    gos_work_t w;
    uint32_t cap;
    size_t cl, deg, terms;
    srmech_status_t st;
    assert(out_has_solution != NULL && r_num_n != NULL && r_den_n != NULL);
    assert(out_rnum != NULL && out_rden != NULL);
    if (out_has_solution == NULL || r_num_n == NULL || r_den_n == NULL
        || out_rnum == NULL || out_rden == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n_den == 0u) { return SRMECH_ERR_BAD_INPUT; }
    deg = (n_num > n_den) ? n_num : n_den;
    if (deg == 0u) { *out_has_solution = 0; return SRMECH_OK; }
    if (deg > GOSPER_MAX_DEG) { return SRMECH_ERR_BAD_INPUT; }
    cl = gos_input_limbs(num_n, num_d, n_num, den_n, den_d, n_den);
    cap = (uint32_t)gos_cap_for(cl, deg);
    st = gos_ctx_init(&c, cap, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    terms = gos_terms_for(deg);
    st = gos_alloc_all(&c, &w, terms);
    if (st != SRMECH_OK) { return st; }
    st = gos_load_input(&c, &w.a, num_n, num_d, n_num);
    if (st == SRMECH_OK) { st = gos_load_input(&c, &w.b, den_n, den_d, n_den); }
    if (st != SRMECH_OK) { return st; }
    return gos_run(&c, &w, deg, out_has_solution, r_num_n, r_num_d, out_rnum,
                   r_den_n, r_den_d, out_rden);
}
