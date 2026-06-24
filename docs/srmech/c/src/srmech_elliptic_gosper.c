/*
 * srmech_elliptic_gosper.c -- the ELLIPTIC analog of Gosper's indefinite
 * hypergeometric summation (the FIRST engine op of the ELLIPTIC F929 reduction
 * row, the top of the base-axis degeneration tower elliptic -> q -> ordinary). The
 * C peer of srmech.amsc.elliptic_gosper.elliptic_gosper.
 *
 * Input: an elliptic-hypergeometric term given by its TERM RATIO t(n+1)/t(n) = r(x)
 * (x = q^n) as an EllRatio -- a theta-quotient prod theta(a x;p)/prod theta(b x;p)
 * over an exact-Q monomial prefactor. The bridge wire form (the Python
 * _ratio_to_form / srmech.amsc._native.elliptic_gosper_c emit it):
 *   - the prefactor exact-Q coefficient as two srmech_bigint (pref_num, pref_den),
 *   - the prefactor symbol count (n_pref_syms),
 *   - the numerator + denominator theta-factor counts (n_num, n_den).
 * Output: when t(n) HAS an elliptic-hypergeometric antidifference T(n) = R(x)*t(n)
 * (so T(n+1) - T(n) = t(n)), the CERTIFICATE R(x) (an EllRatio) satisfying the
 * elliptic Gosper equation R(qx)*r(x) - R(x) = 1; else *out_has = 0.
 *
 * Reference (MPM-verified at build): George Gasper and Michael Schlosser,
 * "Summation, transformation, and expansion formulas for multibasic theta
 * hypergeometric series," Adv. Stud. Contemp. Math. (Kyungshang) 11, no. 1 (2005),
 * 67-84 (arXiv:math/0505215) -- the results are derived "using indefinite
 * summation," the elliptic / theta analogue of Gosper's indefinite-summation
 * telescoping.
 *
 * STANDALONE-COMPLETE + BOUNDED native scope (the srmech_q_gosper precedent): this
 * rc61 peer COMPLETES the canonical elliptic-GEOMETRIC core natively -- a CONSTANT
 * term ratio r = z (a pure-scalar prefactor z = z_num/z_den, NO theta factors, no
 * prefactor symbols), whose certificate is the closed form R = z_den / (z_num -
 * z_den) (then R(qx)*r - R = R*(z - 1) = [z_den/(z_num-z_den)]*[(z_num-z_den)/z_den]
 * = 1, exact at any truncation since R carries no theta). This is the exact elliptic
 * analogue of the ordinary / q-geometric closed form (R = 1/(z-1)). For EVERY other
 * input (any theta factor or a non-scalar prefactor) the peer DECLINES (*out_has =
 * 0), and the Python op re-runs its COMPLETE pure-Python path -- so a has=0 is NEVER
 * a definitive "no certificate" (the dispatch trusts only has=1), mirroring the
 * srmech_q_gosper / srmech_zeilberger order-cap precedent. The full single-x theta-
 * telescoper decision is the owed everything-mirrors backlog (and is mathematically
 * empty in the single-x lattice -- the genuine elliptic telescopers live in a
 * multi-x q^{2n} lattice, a future carrier extension). z = 1 has no finite
 * certificate -> decline. Any residual overflow returns SRMECH_ERR_OVERFLOW (never
 * a wrap).
 *
 * The whole peer is malloc-free (JPL Rule 3): every working srmech_bigint + scratch
 * is carved from the caller arena `ws`. Byte-identical to the Python certificate at
 * ANY magnitude (full bignum; no int64/Q61 ceiling).
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

/* A scalar working roster carved from the caller arena (mirrors qg_ctx_t). */
typedef struct eg_ctx {
    srmech_bigint_t zn, zd;     /* the prefactor scalar z = zn/zd        */
    srmech_bigint_t dn;         /* zn - zd  (the z - 1 numerator)        */
    srmech_bigint_t rn, rd;     /* the certificate R = rn/rd             */
    srmech_bigint_t g, r0, r1;  /* gcd + reduce quotients                */
    uint32_t  cap;
    uint32_t *pool;
    size_t    pool_words;
    size_t    pool_cur;
    void     *scratch;
    size_t    scratch_len;
} eg_ctx_t;

#define EG_N_CARRIERS 8u  /* zn,zd,dn,rn,rd,g,r0,r1 */

static uint32_t *eg_take(uint32_t *base, size_t words, size_t *cur, size_t cnt)
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

static srmech_status_t eg_bind(srmech_bigint_t *b, eg_ctx_t *c)
{
    uint32_t *limbs;
    assert(b != NULL && c != NULL);
    assert(c->cap > 0u);
    limbs = eg_take(c->pool, c->pool_words, &c->pool_cur, c->cap);
    if (limbs == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    b->limbs = limbs;
    b->cap = c->cap;
    b->n = 0u;
    b->sign = 0;
    return SRMECH_OK;
}

static srmech_status_t eg_ctx_init(eg_ctx_t *c, uint32_t cap, void *ws,
                                   size_t ws_len)
{
    uint32_t *base = (uint32_t *)ws;
    size_t words = ws_len / sizeof(uint32_t);
    size_t carrier_words = (size_t)cap * (size_t)EG_N_CARRIERS;
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
    st |= eg_bind(&c->zn, c); st |= eg_bind(&c->zd, c);
    st |= eg_bind(&c->dn, c); st |= eg_bind(&c->rn, c);
    st |= eg_bind(&c->rd, c); st |= eg_bind(&c->g, c);
    st |= eg_bind(&c->r0, c); st |= eg_bind(&c->r1, c);
    if (st != SRMECH_OK) { return SRMECH_ERR_OVERFLOW; }
    c->scratch = (void *)(base + (words - scratch_words));
    c->scratch_len = scratch_words * sizeof(uint32_t);
    assert(c->pool_cur <= c->pool_words);
    return SRMECH_OK;
}

/* Reduce the exact-Q value num/den to lowest terms with den > 0 (Class-K sign on
 * num). den must be nonzero. Mirrors qg_q_reduce. */
static srmech_status_t eg_q_reduce(eg_ctx_t *c, srmech_bigint_t *num,
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

/* Compute the constant-ratio certificate R = z_den/(z_num - z_den) into c->rn/c->rd
 * (reduced, Class-K sign). On entry c->zn/c->zd carry z = z_num/z_den. *got is set 1
 * when a finite certificate exists, 0 when z == 1 (no finite certificate -> decline).
 * Mirrors the qg constant-ratio R = den0/(num0 - den0) leaf. */
static srmech_status_t eg_constant_cert(eg_ctx_t *c, int *got)
{
    srmech_status_t st;
    assert(c != NULL && got != NULL);
    assert(c->zd.sign != 0);
    *got = 0;
    /* normalize the input sign onto zn (zd > 0). */
    if (c->zd.sign < 0) {
        c->zn.sign = (c->zn.sign == 0) ? 0 : -c->zn.sign;
        c->zd.sign = -c->zd.sign;
    }
    /* z - 1 = (zn - zd) / zd. zn == zd (z == 1) -> no finite certificate. */
    st = srmech_bigint_sub(&c->dn, &c->zn, &c->zd);   /* dn = zn - zd */
    if (st != SRMECH_OK) { return st; }
    if (srmech_bigint_is_zero(&c->dn)) {
        return SRMECH_OK;                             /* z == 1: *got stays 0 */
    }
    /* certificate R = zd / dn = z_den / (z_num - z_den), reduced. */
    st = srmech_bigint_copy(&c->rn, &c->zd);
    if (st == SRMECH_OK) { st = srmech_bigint_copy(&c->rd, &c->dn); }
    if (st != SRMECH_OK) { return st; }
    st = eg_q_reduce(c, &c->rn, &c->rd);
    if (st != SRMECH_OK) { return st; }
    *got = 1;
    return SRMECH_OK;
}

/* The public entry: compute the elliptic-Gosper certificate for the CONSTANT-ratio
 * elliptic-geometric core r = z = zn/zd (no theta factors, no prefactor symbols).
 * (The prototype lives in srmech.h, which this file includes.) */
srmech_status_t srmech_elliptic_gosper(const srmech_bigint_t *pref_num,
                                       const srmech_bigint_t *pref_den,
                                       size_t n_pref_syms,
                                       size_t n_num, size_t n_den,
                                       int *out_has,
                                       srmech_bigint_t *rn, srmech_bigint_t *rd,
                                       void *ws, size_t ws_len)
{
    /* zero-init: MSVC /WX flags C4701 on a guarded-alloc-then-use path that gcc's
     * -Wmaybe-uninitialized does not; the {0} init is harmless (eg_ctx_init binds
     * every carrier before any use). */
    eg_ctx_t c = {0};
    uint32_t cap;
    size_t cl;
    int got = 0;
    srmech_status_t st;
    assert(out_has != NULL && rn != NULL && rd != NULL);
    assert(pref_num != NULL && pref_den != NULL);
    if (out_has == NULL || rn == NULL || rd == NULL
        || pref_num == NULL || pref_den == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    *out_has = 0;
    /* the rc61 native scope: the CONSTANT-ratio elliptic-geometric core only -- no
     * theta factors AND no prefactor symbols; otherwise decline so the Python pure
     * path decides (a has=0 is not a definitive "no certificate"). */
    if (n_num != 0u || n_den != 0u || n_pref_syms != 0u) {
        return SRMECH_OK;
    }
    if (srmech_bigint_is_zero(pref_den)) {
        return SRMECH_ERR_BAD_INPUT;        /* a coefficient denominator is nonzero */
    }
    /* size the arena from the input coefficient limbs (a generous cap for the exact-Q
     * reciprocal-of-difference + its reduce). */
    cl = pref_num->n;
    if (pref_den->n > cl) { cl = pref_den->n; }
    if (cl == 0u) { cl = 1u; }
    cap = (uint32_t)(cl * 4u + 64u);
    st = eg_ctx_init(&c, cap, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&c.zn, pref_num);
    if (st == SRMECH_OK) { st = srmech_bigint_copy(&c.zd, pref_den); }
    if (st != SRMECH_OK) { return st; }
    st = eg_constant_cert(&c, &got);
    if (st != SRMECH_OK) { return st; }
    if (!got) { return SRMECH_OK; }                  /* z == 1: decline */
    /* write back the certificate scalar prefactor coefficient rn/rd (no theta). */
    st = srmech_bigint_copy(rn, &c.rn);
    if (st == SRMECH_OK) { st = srmech_bigint_copy(rd, &c.rd); }
    if (st != SRMECH_OK) { return st; }
    *out_has = 1;
    return SRMECH_OK;
}

/* The minimum `ws_len` BYTES srmech_elliptic_gosper needs for an input prefactor
 * coefficient of `coeff_limbs` significant limbs. */
size_t srmech_elliptic_gosper_ws_bound(size_t coeff_limbs)
{
    size_t cl = (coeff_limbs == 0u) ? 1u : coeff_limbs;
    size_t cap = cl * 4u + 64u;
    size_t carriers = cap * (size_t)EG_N_CARRIERS;
    size_t scratch = cap * 8u + 256u;
    size_t words = carriers + scratch + 256u;
    assert(cap >= 2u);
    assert(words >= carriers);
    return words * sizeof(uint32_t);
}

/* The per-coefficient limb cap for each srmech_bigint in the rn / rd OUTPUT, so the
 * reduced certificate coefficient never overflows its slot. */
size_t srmech_elliptic_gosper_out_cap(size_t coeff_limbs)
{
    size_t cl = (coeff_limbs == 0u) ? 1u : coeff_limbs;
    size_t cap = cl * 4u + 64u;
    assert(cap >= 2u);
    assert(cap >= coeff_limbs);
    return cap;
}
