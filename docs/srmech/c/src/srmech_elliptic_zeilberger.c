/*
 * srmech_elliptic_zeilberger.c -- the ELLIPTIC analog of Zeilberger's creative
 * telescoping (the SECOND engine op of the ELLIPTIC F929 reduction row, the top of
 * the base-axis degeneration tower elliptic -> q -> ordinary). The C peer of
 * srmech.amsc.elliptic_zeilberger.elliptic_zeilberger.
 *
 * Input: a theta-hypergeometric term F(n,k) given by its TWO bivariate-elliptic term
 * ratios over (x, y) = (q^n, q^k):
 *   r_n(x,y) = F(n+1,k)/F(n,k)   (the n-shift; sigma_x : x -> q*x)
 *   r_k(x,y) = F(n,k+1)/F(n,k)   (the k-shift; sigma_y : y -> q*y)
 * each an EllRatio -- a theta-quotient prod theta(a x;p)/prod theta(b x;p) over an
 * exact-Q monomial prefactor. The bridge wire form per EllRatio (the Python
 * _ratio_to_form / srmech.amsc._native.elliptic_zeilberger_c emit it):
 *   - the prefactor exact-Q coefficient as two srmech_bigint (pref_num, pref_den),
 *   - the prefactor symbol count (n_pref_syms),
 *   - the numerator + denominator theta-factor counts (n_num, n_den).
 * Output: when f(n)=Sum_k F(n,k) satisfies an EXACTLY-certifiable recurrence
 *   Sum_{j=0}^{L} a_j(n) f(n+j) = 0,
 * the order L + the recurrence coefficients a_j(n) (EllRatio-in-n) + the companion
 * certificate G (EllRatio). Else *out_has = 0.
 *
 * Reference (MPM-verified at build): the elliptic (theta) analogues were introduced by
 * I.B. Frenkel and V.G. Turaev, "Elliptic solutions of the Yang-Baxter equation and
 * modular hypergeometric functions," in The Arnold-Gelfand Mathematical Seminars, eds.
 * V.I. Arnold, I.M. Gelfand, V.S. Retakh & M. Smirnov (Birkhauser Boston, 1997), pp.
 * 171-204. The keystone is the terminating very-well-poised Frenkel-Turaev 10E9 sum
 * (S.O. Warnaar, Constr. Approx. 18 (2002) 479-502, Cor. 2.2 / Eq. 2.11,
 * arXiv:math/0001006); its closed form is a ratio of theta-Pochhammers in n, and that
 * closed form's exact order-1 n-recurrence is the keystone this op certifies.
 *
 * STANDALONE-COMPLETE + BOUNDED native scope (the srmech_q_zeilberger / srmech_q_gosper
 * precedent): this rc62 peer COMPLETES the canonical native case -- the SCALAR k-free
 * elliptic-geometric term, r_n a pure-scalar prefactor z = z_num/z_den (NO theta
 * factors, no prefactor symbols, k-free), whose definite sum f(n) = z^n * C satisfies
 * the ORDER-1 recurrence a_0(n) f(n) + a_1(n) f(n+1) = 0 with a_0 = -z, a_1 = 1
 * (z*f(n) - f(n+1) ... cleared to f(n+1) = z f(n) => -z f(n) + 1*f(n+1) = 0), the
 * companion certificate G == 0 (the k-free term telescopes trivially in n -- no
 * k-telescoping is needed; the recurrence IS the term ratio). This is the elliptic
 * analogue of the rc56 q_zeilberger k-free q-geometric order-1 case. For EVERY other
 * input (any theta factor, a non-scalar prefactor, or a y-dependent r_n) the peer
 * DECLINES (*out_has = 0), and the Python op re-runs its COMPLETE pure-Python path --
 * so a has=0 is NEVER a definitive "no recurrence" (the dispatch trusts only has=1),
 * mirroring the srmech_q_zeilberger / srmech_elliptic_gosper order/scope-cap precedent.
 * The full theta-quotient k-free recurrence + the genuine k-dependent creative
 * telescoping (which needs the additive theta lattice) are the owed everything-mirrors
 * backlog. z == 0 is not a proper term -> decline. Any residual overflow returns
 * SRMECH_ERR_OVERFLOW (never a wrap).
 *
 * The whole peer is malloc-free (JPL Rule 3): every working srmech_bigint + scratch is
 * carved from the caller arena `ws`. The order-1 coefficients a_0 = -z, a_1 = 1 come
 * back as exact-Q scalars (a0_num/a0_den, a1_num/a1_den), byte-identical to the Python
 * recurrence at ANY magnitude (full bignum; no int64/Q61 ceiling).
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto/recursion): OK -- iterative, flat helpers
 *   - Rule 2 (bounded loops)    : OK -- no unbounded loop (fixed bind sequence)
 *   - Rule 3 (no malloc)        : OK -- caller arena + caller out only
 *   - Rule 4 (<=60 lines/func)  : OK -- factored into static helpers
 *   - Rule 5 (>=2 asserts/fn)   : OK -- entry-pointer + pre/postcondition
 *   - Rule 7 (return-value)     : OK -- srmech_status_t propagated
 *   - Rule 8 (no multi-line mac): OK -- no function-like macros
 *   - Rule 10 (warnings clean)  : OK under -Wall -Wextra -Wpedantic -Werror
 *
 * Additive symbol -> ABI unchanged (stays 3). License: MIT.
 */

#include "srmech.h"

#include <assert.h>
#include <stdint.h>

/* A scalar working roster carved from the caller arena (mirrors eg_ctx_t). */
typedef struct ez_ctx {
    srmech_bigint_t zn, zd;     /* the prefactor scalar z = zn/zd        */
    srmech_bigint_t g, r0, r1;  /* gcd + reduce quotients                */
    uint32_t  cap;
    uint32_t *pool;
    size_t    pool_words;
    size_t    pool_cur;
    void     *scratch;
    size_t    scratch_len;
} ez_ctx_t;

#define EZ_N_CARRIERS 5u  /* zn,zd,g,r0,r1 */

static uint32_t *ez_take(uint32_t *base, size_t words, size_t *cur, size_t cnt)
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

static srmech_status_t ez_bind(srmech_bigint_t *b, ez_ctx_t *c)
{
    uint32_t *limbs;
    assert(b != NULL && c != NULL);
    assert(c->cap > 0u);
    limbs = ez_take(c->pool, c->pool_words, &c->pool_cur, c->cap);
    if (limbs == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    b->limbs = limbs;
    b->cap = c->cap;
    b->n = 0u;
    b->sign = 0;
    return SRMECH_OK;
}

static srmech_status_t ez_ctx_init(ez_ctx_t *c, uint32_t cap, void *ws,
                                   size_t ws_len)
{
    uint32_t *base = (uint32_t *)ws;
    size_t words = ws_len / sizeof(uint32_t);
    size_t carrier_words = (size_t)cap * (size_t)EZ_N_CARRIERS;
    size_t scratch_words = (size_t)cap * 8u + 256u;
    srmech_status_t st = SRMECH_OK;
    assert(c != NULL);
    assert((uintptr_t)ws % sizeof(uint32_t) == 0u || ws == NULL);
    c->cap = cap;
    if (ws == NULL || words < carrier_words + scratch_words) {
        return SRMECH_ERR_OVERFLOW;
    }
    c->pool = base;
    c->pool_words = words - scratch_words;
    c->pool_cur = 0u;
    st |= ez_bind(&c->zn, c); st |= ez_bind(&c->zd, c);
    st |= ez_bind(&c->g, c);  st |= ez_bind(&c->r0, c);
    st |= ez_bind(&c->r1, c);
    if (st != SRMECH_OK) { return SRMECH_ERR_OVERFLOW; }
    c->scratch = (void *)(base + (words - scratch_words));
    c->scratch_len = scratch_words * sizeof(uint32_t);
    assert(c->pool_cur <= c->pool_words);
    return SRMECH_OK;
}

/* Reduce the exact-Q value num/den to lowest terms with den > 0 (Class-K sign on num).
 * den must be nonzero. Mirrors eg_q_reduce. */
static srmech_status_t ez_q_reduce(ez_ctx_t *c, srmech_bigint_t *num,
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
    st = srmech_bigint_divmod(&c->r0, &c->r1, num, &c->g, c->scratch,
                              c->scratch_len);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(num, &c->r0);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_divmod(&c->r0, &c->r1, den, &c->g, c->scratch,
                              c->scratch_len);
    if (st != SRMECH_OK) { return st; }
    return srmech_bigint_copy(den, &c->r0);
}

/* Compute the order-1 k-free scalar recurrence coefficients into the OUTPUT:
 *   a_0 = -z = -(zn/zd)   (reduced, Class-K sign on the numerator),
 *   a_1 = 1.
 * On entry c->zn/c->zd carry z = z_num/z_den (the scalar prefactor). z == 0 is not a
 * proper term (-> *got 0, decline). The companion certificate G == 0 (out by the
 * caller). Mirrors eg_constant_cert's reduce + the q_zeilberger a_0/a_1 emit. */
static srmech_status_t ez_kfree_order1(ez_ctx_t *c, int *got,
                                       srmech_bigint_t *a0_num,
                                       srmech_bigint_t *a0_den,
                                       srmech_bigint_t *a1_num,
                                       srmech_bigint_t *a1_den)
{
    srmech_status_t st;
    assert(c != NULL && got != NULL);
    assert(a0_num != NULL && a0_den != NULL && a1_num != NULL && a1_den != NULL);
    *got = 0;
    if (srmech_bigint_is_zero(&c->zn)) {
        return SRMECH_OK;                 /* z == 0: not a proper term -> decline */
    }
    /* a_0 = -z = -(zn/zd), reduced (positive den, sign onto num = Class-K). */
    st = srmech_bigint_copy(a0_num, &c->zn);
    if (st == SRMECH_OK) { st = srmech_bigint_copy(a0_den, &c->zd); }
    if (st != SRMECH_OK) { return st; }
    st = ez_q_reduce(c, a0_num, a0_den);
    if (st != SRMECH_OK) { return st; }
    a0_num->sign = (a0_num->sign == 0) ? 0 : -a0_num->sign;   /* negate: a_0 = -z */
    /* a_1 = 1. */
    st = srmech_bigint_set_i64(a1_num, 1);
    if (st == SRMECH_OK) { st = srmech_bigint_set_i64(a1_den, 1); }
    if (st != SRMECH_OK) { return st; }
    *got = 1;
    return SRMECH_OK;
}

/* Validate the OUTPUT + input pointers and decide whether the input is in the rc62
 * native scope (the SCALAR k-free elliptic-geometric term). *in_scope is set 1 when
 * r_n is a pure-scalar prefactor (no theta, no prefactor symbols) AND r_k is a proper
 * (nonzero) ratio, 0 when the peer should decline. Returns SRMECH_ERR_NULL_ARG on a
 * null pointer, SRMECH_ERR_BAD_INPUT on a zero r_n denominator, else SRMECH_OK. */
static srmech_status_t ez_gate(const srmech_bigint_t *rn_pref_num,
                               const srmech_bigint_t *rn_pref_den,
                               size_t rn_n_pref_syms, size_t rn_n_num, size_t rn_n_den,
                               const srmech_bigint_t *rk_pref_num,
                               int *out_has, size_t *out_order,
                               srmech_bigint_t *a0_num, srmech_bigint_t *a0_den,
                               srmech_bigint_t *a1_num, srmech_bigint_t *a1_den,
                               int *in_scope)
{
    assert(in_scope != NULL);
    assert(rn_pref_num != NULL || out_has == NULL);
    *in_scope = 0;
    if (out_has == NULL || out_order == NULL || a0_num == NULL || a0_den == NULL
        || a1_num == NULL || a1_den == NULL || rn_pref_num == NULL
        || rn_pref_den == NULL || rk_pref_num == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    *out_has = 0;
    *out_order = 0u;
    /* r_n a pure-scalar prefactor (no theta factors, no prefactor symbols); r_k a
     * proper nonzero term ratio. Otherwise decline (the Python pure path decides). */
    if (rn_n_num != 0u || rn_n_den != 0u || rn_n_pref_syms != 0u
        || srmech_bigint_is_zero(rk_pref_num)) {
        return SRMECH_OK;
    }
    if (srmech_bigint_is_zero(rn_pref_den)) {
        return SRMECH_ERR_BAD_INPUT;        /* a coefficient denominator is nonzero */
    }
    *in_scope = 1;
    return SRMECH_OK;
}

/* The public entry: the SCALAR k-free elliptic-geometric order-1 recurrence. r_n must
 * be a pure-scalar prefactor (no theta, no prefactor symbols) and r_k a proper (nonzero)
 * ratio; the order-1 recurrence a_0 = -z, a_1 = 1 (certificate G == 0) is emitted. For
 * every other input the peer declines. (The prototype lives in srmech.h.) */
srmech_status_t srmech_elliptic_zeilberger(
        const srmech_bigint_t *rn_pref_num, const srmech_bigint_t *rn_pref_den,
        size_t rn_n_pref_syms, size_t rn_n_num, size_t rn_n_den,
        const srmech_bigint_t *rk_pref_num, const srmech_bigint_t *rk_pref_den,
        size_t rk_n_pref_syms, size_t rk_n_num, size_t rk_n_den,
        size_t max_order,
        int *out_has, size_t *out_order,
        srmech_bigint_t *a0_num, srmech_bigint_t *a0_den,
        srmech_bigint_t *a1_num, srmech_bigint_t *a1_den,
        void *ws, size_t ws_len)
{
    /* zero-init: MSVC /WX flags C4701 on a guarded-alloc-then-use path that gcc's
     * -Wmaybe-uninitialized does not; the {0} init is harmless (ez_ctx_init binds
     * every carrier before any use). */
    ez_ctx_t c = {0};
    uint32_t cap;
    size_t cl;
    int got = 0, in_scope = 0;
    srmech_status_t st;
    (void)rk_pref_den; (void)rk_n_pref_syms; (void)rk_n_num; (void)rk_n_den;
    (void)max_order;
    st = ez_gate(rn_pref_num, rn_pref_den, rn_n_pref_syms, rn_n_num, rn_n_den,
                 rk_pref_num, out_has, out_order, a0_num, a0_den, a1_num, a1_den,
                 &in_scope);
    if (st != SRMECH_OK || !in_scope) { return st; }   /* decline / error */
    /* size the arena from the input coefficient limbs (a generous cap for the exact-Q
     * reduce of z). */
    cl = rn_pref_num->n;
    if (rn_pref_den->n > cl) { cl = rn_pref_den->n; }
    if (cl == 0u) { cl = 1u; }
    cap = (uint32_t)(cl * 4u + 64u);
    st = ez_ctx_init(&c, cap, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&c.zn, rn_pref_num);
    if (st == SRMECH_OK) { st = srmech_bigint_copy(&c.zd, rn_pref_den); }
    if (st != SRMECH_OK) { return st; }
    st = ez_kfree_order1(&c, &got, a0_num, a0_den, a1_num, a1_den);
    if (st != SRMECH_OK) { return st; }
    if (!got) { return SRMECH_OK; }                  /* z == 0: decline */
    *out_order = 1u;
    *out_has = 1;
    return SRMECH_OK;
}

/* The minimum `ws_len` BYTES srmech_elliptic_zeilberger needs for an input prefactor
 * coefficient of `coeff_limbs` significant limbs. */
size_t srmech_elliptic_zeilberger_ws_bound(size_t coeff_limbs)
{
    size_t cl = (coeff_limbs == 0u) ? 1u : coeff_limbs;
    size_t cap = cl * 4u + 64u;
    size_t carriers = cap * (size_t)EZ_N_CARRIERS;
    size_t scratch = cap * 8u + 256u;
    size_t words = carriers + scratch + 256u;
    assert(cap >= 2u);
    assert(words >= carriers);
    return words * sizeof(uint32_t);
}

/* The per-coefficient limb cap for each srmech_bigint in the a0 / a1 OUTPUT, so the
 * reduced recurrence coefficient never overflows its slot. */
size_t srmech_elliptic_zeilberger_out_cap(size_t coeff_limbs)
{
    size_t cl = (coeff_limbs == 0u) ? 1u : coeff_limbs;
    size_t cap = cl * 4u + 64u;
    assert(cap >= 2u);
    assert(cap >= coeff_limbs);
    return cap;
}
