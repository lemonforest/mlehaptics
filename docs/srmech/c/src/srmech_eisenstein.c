/*
 * srmech_eisenstein.c — the EXACT-RATIONAL q-series of a normalized EISENSTEIN
 * SERIES E_k (the C peer of srmech.amsc.eisenstein.Eisenstein; the SECOND rung
 * of the WEIGHT axis, after the rc82 eta-quotient).
 *
 * The normalized Eisenstein series of even weight k >= 4 is
 *
 *     E_k(tau) = 1 - (2k / B_k) * SUM_{n>=1} sigma_{k-1}(n) q^n,
 *
 * with B_k the k-th Bernoulli number (an EXACT RATIONAL, e.g. B_4 = -1/30,
 * B_6 = 1/42, B_12 = -691/2730) and sigma_{k-1}(n) = SUM_{d|n} d^{k-1} the
 * exact-integer divisor power sum. The coefficients are RATIONAL in general:
 * for k in {4,6,8,10,14} the prefactor -2k/B_k happens to be an integer
 * (240,-504,480,-264,-24), but for k=12 it is 65520/691 and for k=16 it is
 * 16320/3617 — so this op returns each coefficient as a REDUCED (num, den) pair
 * of full srmech_bigint, byte-identical to the Python carrier (NO int64 ceiling;
 * the genuine rational case k=12 -> 65520/691 is covered, NOT just integer k).
 *
 * Anchors (the build gates):
 *   E_4 : k=4  -> [1, 240, 2160, 6720, 17520]            (240*sigma_3)
 *   E_6 : k=6  -> [1, -504, -16632, -122976, -532728]    (-504*sigma_5)
 *   E_12: k=12 -> [1, 65520/691, ...]                    (genuine rational coeff)
 *   cross-rung E_4^3 - E_6^2 = 1728*Delta = 1728*eta^24  (ties to rc82)
 *
 * Method:
 *   B_k is computed exact-Q by the standard recurrence
 *       B_m = -(1/(m+1)) * SUM_{j=0}^{m-1} C(m+1, j) B_j,   B_0 = 1
 *   over a roster of m+1 (num, den) bigint rationals carved from the caller
 *   arena. sigma_{k-1}(n) is an exact integer (divisor-pair trial division,
 *   each divisor power via srmech_bigint_pow_u32). The coefficient is the exact
 *   rational product pref * sigma reduced to lowest terms (gcd-reduce, positive
 *   denominator) — the same Class-N rational arithmetic as srmech_poly /
 *   srmech_rational. Only bigint add/sub/mul/divmod/gcd/pow are used.
 *
 * The C is STANDALONE-COMPLETE: every working carrier + the Bernoulli rational
 * roster + the divmod/gcd/pow scratch is carved from the caller arena `ws`
 * (sized via srmech_eisenstein_ws_bound), so the magnitude bound is the CALLER's
 * RAM, not a compiled-in cap. out_num[]/out_den[] are caller-owned.
 *
 * Carrier-internal, like srmech_poly.c / srmech_eta_quotient.c: NOT a Rosetta
 * ledger op (no ToolEntry, no count-test). Additive symbols -> ABI unchanged
 * (stays 3). The is_modular / quasimodular-boundary DECISION logic stays
 * Python-only (the carrier precedent: the q-series is the compute kernel that
 * needs the C peer).
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto/recursion): OK — iterative, flat helpers
 *   - Rule 2 (bounded loops)    : OK — bounds are k, n_terms, sqrt(n), m
 *   - Rule 3 (no malloc)        : OK — caller arena + caller out only
 *   - Rule 4 (<=60 lines/func)  : OK — factored into static helpers
 *   - Rule 5 (>=2 asserts/fn)   : OK — entry-pointer + pre/postcondition
 *   - Rule 7 (return-value)     : OK — srmech_status_t propagated
 *   - Rule 8 (no multi-line mac): OK — no function-like macros
 *   - Rule 10 (warnings clean)  : OK under -Wall -Wextra -Wpedantic -Werror
 *
 * License: MIT.
 */

#include "srmech.h"

#include <assert.h>
#include <stdint.h>

/* A roster of working exact-Q carriers carved from the caller arena `ws`, plus
 * the divmod/gcd/pow scratch tail. The Bernoulli rationals bern_n[]/bern_d[]
 * (k+1 entries) ride a separate caller-passed array (carved by the entry point).
 * Every carrier is `cap` limbs. */
typedef struct eis_ctx {
    srmech_bigint_t a_n;   /* exact-Q accumulator numerator    */
    srmech_bigint_t a_d;   /* exact-Q accumulator denominator  */
    srmech_bigint_t b_n;   /* second operand numerator         */
    srmech_bigint_t b_d;   /* second operand denominator        */
    srmech_bigint_t t0;    /* integer cross-product scratch     */
    srmech_bigint_t t1;    /* integer scratch (sigma term/pow)  */
    srmech_bigint_t g;     /* gcd sink (reduce-private)          */
    srmech_bigint_t rem;   /* divmod remainder sink (reduce)     */
    srmech_bigint_t rs0;   /* reduce-private quotient scratch    */
    srmech_bigint_t rs1;   /* reduce-private quotient scratch    */
    uint32_t        limb_cap;
    void           *scratch;     /* divmod/gcd/pow arena tail     */
    size_t          scratch_len;
} eis_ctx_t;

#define EIS_N_CARRIERS 10u   /* a_n,a_d,b_n,b_d,t0,t1,g,rem,rs0,rs1 */

/* ---- forward declarations (Rule 1: no recursion) ------------------- */

static uint32_t *eis_take(uint32_t *base, size_t words, size_t *cur,
                          size_t count);
static srmech_status_t eis_bind(srmech_bigint_t *b, uint32_t *base,
                                size_t words, size_t *cur, uint32_t cap);
static srmech_status_t eis_ctx_init(eis_ctx_t *c, uint32_t cap, uint32_t *base,
                                    size_t words, size_t *cur);
static srmech_status_t eis_q_reduce(eis_ctx_t *c, srmech_bigint_t *num,
                                    srmech_bigint_t *den);
static srmech_status_t eis_q_addmul(eis_ctx_t *c, srmech_bigint_t *acc_n,
                                    srmech_bigint_t *acc_d,
                                    const srmech_bigint_t *cn,
                                    const srmech_bigint_t *bn,
                                    const srmech_bigint_t *bd);
static srmech_status_t eis_set_binom(eis_ctx_t *c, srmech_bigint_t *out,
                                     int64_t n, int64_t r);
static srmech_status_t eis_bernoulli(eis_ctx_t *c, int64_t k,
                                     srmech_bigint_t *bern_n,
                                     srmech_bigint_t *bern_d);
static srmech_status_t eis_sigma(eis_ctx_t *c, int64_t e, int64_t n,
                                 srmech_bigint_t *out);
static size_t eis_hdr_words(void);
static srmech_status_t eis_carve_roster(eis_ctx_t *c, uint32_t *base,
                                        size_t words, size_t *cur, uint32_t cap,
                                        size_t need, srmech_bigint_t **bn_arr,
                                        srmech_bigint_t **bd_arr);
static srmech_status_t eis_prefactor(eis_ctx_t *c, size_t k,
                                     srmech_bigint_t *bn_arr,
                                     srmech_bigint_t *bd_arr);
static srmech_status_t eis_fill_coeffs(eis_ctx_t *c, size_t k, size_t n_terms,
                                       srmech_bigint_t *out_num,
                                       srmech_bigint_t *out_den);

/* ---- caller-arena carve (mirrors poly_take / poly_bind) ------------ */

static uint32_t *eis_take(uint32_t *base, size_t words, size_t *cur,
                          size_t count)
{
    uint32_t *p;
    assert(base != NULL && cur != NULL);
    assert(*cur <= words);
    if (count > words || *cur > words - count) {
        return NULL;
    }
    p = base + *cur;
    *cur += count;
    return p;
}

static srmech_status_t eis_bind(srmech_bigint_t *b, uint32_t *base,
                                size_t words, size_t *cur, uint32_t cap)
{
    uint32_t *limbs = eis_take(base, words, cur, cap);
    assert(b != NULL);
    assert(cap > 0u);
    if (limbs == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    b->limbs = limbs;
    b->cap = cap;
    b->n = 0u;
    b->sign = 0;
    return SRMECH_OK;
}

static srmech_status_t eis_ctx_init(eis_ctx_t *c, uint32_t cap, uint32_t *base,
                                    size_t words, size_t *cur)
{
    srmech_status_t st = SRMECH_OK;
    assert(c != NULL && base != NULL && cur != NULL);
    assert(cap > 0u);
    c->limb_cap = cap;
    st |= eis_bind(&c->a_n, base, words, cur, cap);
    st |= eis_bind(&c->a_d, base, words, cur, cap);
    st |= eis_bind(&c->b_n, base, words, cur, cap);
    st |= eis_bind(&c->b_d, base, words, cur, cap);
    st |= eis_bind(&c->t0, base, words, cur, cap);
    st |= eis_bind(&c->t1, base, words, cur, cap);
    st |= eis_bind(&c->g, base, words, cur, cap);
    st |= eis_bind(&c->rem, base, words, cur, cap);
    st |= eis_bind(&c->rs0, base, words, cur, cap);
    st |= eis_bind(&c->rs1, base, words, cur, cap);
    if (st != SRMECH_OK) {
        return SRMECH_ERR_OVERFLOW;
    }
    c->scratch = (void *)(base + *cur);
    c->scratch_len = (words - *cur) * sizeof(uint32_t);
    assert(*cur <= words);
    return SRMECH_OK;
}

/* ---- exact-Q reduce (mirrors poly_q_reduce) ----------------------- */

/* Reduce num/den IN PLACE to lowest terms, positive denominator. den nonzero;
 * 0/d -> 0/1. Uses ONLY the reduce-private carriers (g, rem, rs0, rs1) + the
 * scratch tail, so num/den may safely be any caller carrier. */
static srmech_status_t eis_q_reduce(eis_ctx_t *c, srmech_bigint_t *num,
                                    srmech_bigint_t *den)
{
    srmech_status_t st;
    assert(c != NULL && num != NULL && den != NULL);
    assert(den->sign != 0);
    if (den->sign < 0) {                      /* force positive denominator */
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

/* ---- acc += cn * (bn/bd)  (exact Q, reduced) ---------------------- *
 * acc_n/acc_d (a reduced rational) gets cn*(bn/bd) added in place. cn is an
 * INTEGER (the binomial C(m+1,j) carried as a bigint). All products go into
 * NON-aliasing scratch (a_n/a_d/t0/t1) — srmech_bigint_mul zeros its `out`
 * first, so out must never alias an input. acc_* must NOT alias a/b/t0/t1. */
static srmech_status_t eis_q_addmul(eis_ctx_t *c, srmech_bigint_t *acc_n,
                                    srmech_bigint_t *acc_d,
                                    const srmech_bigint_t *cn,
                                    const srmech_bigint_t *bn,
                                    const srmech_bigint_t *bd)
{
    srmech_status_t st;
    assert(c != NULL && acc_n != NULL && acc_d != NULL);
    assert(cn != NULL && bn != NULL && bd != NULL);
    st = srmech_bigint_mul(&c->a_n, cn, bn);          /* a = (cn*bn) / bd */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&c->a_d, bd);
    if (st != SRMECH_OK) { return st; }
    /* acc = acc + a : num = acc_n*a_d + a_n*acc_d, den = acc_d*a_d */
    st = srmech_bigint_mul(&c->t0, acc_n, &c->a_d);   /* t0 = acc_n*a_d  */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_mul(&c->t1, &c->a_n, acc_d);   /* t1 = a_n*acc_d  */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_mul(&c->a_n, acc_d, &c->a_d);  /* a_n = acc_d*a_d (den) */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_add(acc_n, &c->t0, &c->t1);    /* acc_n = t0 + t1 (num) */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(acc_d, &c->a_n);          /* acc_d = new den  */
    if (st != SRMECH_OK) { return st; }
    return eis_q_reduce(c, acc_n, acc_d);
}

/* ---- C(n, r) as an exact bigint (multiplicative, mirrors Python) --- *
 * out = n! / (r! (n-r)!). The CALLER passes out == &c->t1, so this MUST NOT use
 * t1 as its own scratch: it uses a_n (running numerator product), a_d (the
 * non-aliasing multiply temp — srmech_bigint_mul zeros its out, so out must never
 * alias an input), t0 (the running factor) + g/rem (the divmod sinks). out is
 * read only as the divisor + written only by the final copy. The symmetric
 * smaller r is used. */
static srmech_status_t eis_set_binom(eis_ctx_t *c, srmech_bigint_t *out,
                                     int64_t n, int64_t r)
{
    int64_t rr, i;
    srmech_status_t st;
    assert(c != NULL && out != NULL);
    assert(n >= 0 && r >= 0 && r <= n);
    rr = (r + r <= n) ? r : (n - r);          /* fewer multiplies */
    st = srmech_bigint_set_i64(&c->a_n, 1);   /* numerator product */
    if (st != SRMECH_OK) { return st; }
    for (i = 0; i < rr; ++i) {
        st = srmech_bigint_set_i64(&c->t0, n - i);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_mul(&c->a_d, &c->a_n, &c->t0);  /* a_d = a_n*t0 */
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_copy(&c->a_n, &c->a_d);         /* a_n <- a_d   */
        if (st != SRMECH_OK) { return st; }
    }
    st = srmech_bigint_set_i64(out, 1);       /* denominator product */
    if (st != SRMECH_OK) { return st; }
    for (i = 1; i <= rr; ++i) {
        st = srmech_bigint_set_i64(&c->t0, i);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_mul(&c->a_d, out, &c->t0);      /* a_d = out*t0 */
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_copy(out, &c->a_d);             /* out <- a_d   */
        if (st != SRMECH_OK) { return st; }
    }
    /* out = a_n / out (exact: a binomial coefficient is an integer). Quotient
     * into a_d (NOT aliasing the divisor out), then copy back. */
    st = srmech_bigint_divmod(&c->a_d, &c->rem, &c->a_n, out,
                              c->scratch, c->scratch_len);
    if (st != SRMECH_OK) { return st; }
    return srmech_bigint_copy(out, &c->a_d);
}

/* ---- B_k by the standard recurrence, into bern_n/bern_d roster ----- *
 * bern_n[m]/bern_d[m] (m = 0..k) are caller-carved reduced rationals. After this
 * bern_n[k]/bern_d[k] is B_k. Uses b_n/b_d as the running accumulator + a_n/a_d
 * (via eis_q_addmul) + t0/t1 + the reduce scratch. */
static srmech_status_t eis_bernoulli(eis_ctx_t *c, int64_t k,
                                     srmech_bigint_t *bern_n,
                                     srmech_bigint_t *bern_d)
{
    int64_t m, j;
    srmech_status_t st;
    assert(c != NULL && bern_n != NULL && bern_d != NULL);
    assert(k >= 0);
    st = srmech_bigint_set_i64(&bern_n[0], 1);   /* B_0 = 1/1 */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&bern_d[0], 1);
    if (st != SRMECH_OK) { return st; }
    for (m = 1; m <= k; ++m) {
        st = srmech_bigint_set_i64(&c->b_n, 0);  /* acc = 0/1 */
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_set_i64(&c->b_d, 1);
        if (st != SRMECH_OK) { return st; }
        for (j = 0; j < m; ++j) {
            st = eis_set_binom(c, &c->t1, m + 1, j);     /* t1 = C(m+1, j) */
            if (st != SRMECH_OK) { return st; }
            st = eis_q_addmul(c, &c->b_n, &c->b_d, &c->t1,
                              &bern_n[j], &bern_d[j]);   /* acc += C*B_j */
            if (st != SRMECH_OK) { return st; }
        }
        /* B_m = -acc / (m+1): num = -acc_n, den = acc_d*(m+1) */
        st = srmech_bigint_set_i64(&c->t0, m + 1);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_mul(&bern_d[m], &c->b_d, &c->t0);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_copy(&bern_n[m], &c->b_n);
        if (st != SRMECH_OK) { return st; }
        bern_n[m].sign = (bern_n[m].sign == 0) ? 0 : -bern_n[m].sign;
        st = eis_q_reduce(c, &bern_n[m], &bern_d[m]);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* ---- sigma_e(n) = SUM_{d|n} d^e as an exact integer bigint --------- *
 * out gets the divisor power sum (out must NOT alias a/b/g/rem/rs0/rs1). Uses
 * t0 (running d^e via pow) + t1 (running sum). Divisor-pair trial division. */
static srmech_status_t eis_sigma(eis_ctx_t *c, int64_t e, int64_t n,
                                 srmech_bigint_t *out)
{
    int64_t d, cof;
    srmech_status_t st;
    assert(c != NULL && out != NULL);
    assert(e >= 0 && n >= 1);
    st = srmech_bigint_set_i64(&c->t1, 0);    /* running sum */
    if (st != SRMECH_OK) { return st; }
    for (d = 1; d * d <= n; ++d) {
        if (n % d != 0) {
            continue;
        }
        st = srmech_bigint_set_i64(&c->t0, d);            /* t0 = d^e */
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_pow_u32(&c->a_n, &c->t0, (uint32_t)e,
                                   c->scratch, c->scratch_len);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_add(&c->t1, &c->t1, &c->a_n);
        if (st != SRMECH_OK) { return st; }
        cof = n / d;
        if (cof != d) {                                   /* + (n/d)^e */
            st = srmech_bigint_set_i64(&c->t0, cof);
            if (st != SRMECH_OK) { return st; }
            st = srmech_bigint_pow_u32(&c->a_n, &c->t0, (uint32_t)e,
                                       c->scratch, c->scratch_len);
            if (st != SRMECH_OK) { return st; }
            st = srmech_bigint_add(&c->t1, &c->t1, &c->a_n);
            if (st != SRMECH_OK) { return st; }
        }
    }
    return srmech_bigint_copy(out, &c->t1);
}

/* ================================================================== *
 *  Public: srmech_eisenstein_ws_bound + srmech_eisenstein_qseries     *
 * ================================================================== */

/* The srmech_bigint header size, in arena words (rounded up). */
static size_t eis_hdr_words(void)
{
    size_t hw = (sizeof(srmech_bigint_t) + sizeof(uint32_t) - 1u) / sizeof(uint32_t);
    assert(hw >= 1u);
    assert(sizeof(uint32_t) >= 1u);
    return hw;
}

/* Minimum `ws_len` BYTES for srmech_eisenstein_qseries: EIS_N_CARRIERS working
 * carriers of `coeff_limbs` limbs each, PLUS the (k+1) Bernoulli rational roster
 * (2*(k+1) bigints — both HEADERS and LIMB runs carved from the arena), PLUS a
 * divmod/gcd/pow scratch tail. The divisor powers d^{k-1} (d up to ~sqrt(n_terms),
 * e = k-1) and the Bernoulli intermediates set the coefficient magnitude; the
 * caller sizes coeff_limbs to hold them. */
size_t srmech_eisenstein_ws_bound(size_t coeff_limbs, size_t k)
{
    size_t cl = (coeff_limbs > 0u) ? coeff_limbs : 1u;
    size_t kk = (k > 0u) ? k : 1u;
    size_t n_roster = 2u * (kk + 1u);         /* bern_n[k+1] + bern_d[k+1] */
    size_t carriers = cl * (size_t)EIS_N_CARRIERS;
    size_t roster_limbs = cl * n_roster;
    size_t roster_hdrs = eis_hdr_words() * n_roster;
    size_t scratch = cl * 8u + 256u;          /* divmod/gcd/pow envelope   */
    size_t words = carriers + roster_limbs + roster_hdrs + scratch;
    assert(cl >= 1u);
    assert(words >= carriers);
    return words * sizeof(uint32_t);
}

/* Carve the (k+1)-entry Bernoulli rational roster from the arena: 2*(k+1) headers
 * (cast from arena words) + 2*(k+1) limb runs, then re-anchor the ctx scratch
 * tail to whatever remains. No static / no malloc — arena-only (mirrors
 * poly_gcd_carve). On return *bn_arr / *bd_arr point at the carved arrays. */
static srmech_status_t eis_carve_roster(eis_ctx_t *c, uint32_t *base,
                                        size_t words, size_t *cur, uint32_t cap,
                                        size_t need, srmech_bigint_t **bn_arr,
                                        srmech_bigint_t **bd_arr)
{
    size_t hw = eis_hdr_words(), i;
    uint32_t *hb;
    srmech_status_t st;
    assert(c != NULL && base != NULL && cur != NULL);
    assert(bn_arr != NULL && bd_arr != NULL && need >= 1u);
    hb = eis_take(base, words, cur, hw * need);
    if (hb == NULL) { return SRMECH_ERR_OVERFLOW; }
    *bn_arr = (srmech_bigint_t *)(void *)hb;
    hb = eis_take(base, words, cur, hw * need);
    if (hb == NULL) { return SRMECH_ERR_OVERFLOW; }
    *bd_arr = (srmech_bigint_t *)(void *)hb;
    for (i = 0u; i < need; ++i) {
        st = eis_bind(&(*bn_arr)[i], base, words, cur, cap);
        if (st != SRMECH_OK) { return st; }
        st = eis_bind(&(*bd_arr)[i], base, words, cur, cap);
        if (st != SRMECH_OK) { return st; }
    }
    c->scratch = (void *)(base + *cur);
    c->scratch_len = (words - *cur) * sizeof(uint32_t);
    return SRMECH_OK;
}

/* Compute B_k into the roster, then the reduced prefactor pref = -2k / B_k into
 * c->b_n / c->b_d (kept across the coefficient loop). pref num = -2k * B_k_den,
 * pref den = B_k_num. */
static srmech_status_t eis_prefactor(eis_ctx_t *c, size_t k,
                                     srmech_bigint_t *bn_arr,
                                     srmech_bigint_t *bd_arr)
{
    srmech_status_t st;
    assert(c != NULL && bn_arr != NULL && bd_arr != NULL);
    assert(k >= 2u);   /* k=2 is the QUASIMODULAR E_2 branch (pref -4/B_2 = -24) */
    st = eis_bernoulli(c, (int64_t)k, bn_arr, bd_arr);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&c->t0, -2 * (int64_t)k);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_mul(&c->b_n, &c->t0, &bd_arr[k]);   /* pref num */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&c->b_d, &bn_arr[k]);          /* pref den */
    if (st != SRMECH_OK) { return st; }
    return eis_q_reduce(c, &c->b_n, &c->b_d);              /* reduced prefactor */
}

/* Fill out_num[]/out_den[] = the reduced E_k coefficients given the prefactor in
 * c->b_n/c->b_d: c_0 = 1/1, c_i = pref * sigma_{k-1}(i) reduced. */
static srmech_status_t eis_fill_coeffs(eis_ctx_t *c, size_t k, size_t n_terms,
                                       srmech_bigint_t *out_num,
                                       srmech_bigint_t *out_den)
{
    int64_t e = (int64_t)k - 1;
    size_t i;
    srmech_status_t st;
    assert(c != NULL && out_num != NULL && out_den != NULL);
    assert(n_terms >= 1u);
    st = srmech_bigint_set_i64(&out_num[0], 1);   /* c_0 = 1/1 */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&out_den[0], 1);
    if (st != SRMECH_OK) { return st; }
    for (i = 1u; i < n_terms; ++i) {
        st = eis_sigma(c, e, (int64_t)i, &c->t0);            /* t0 = sigma (int) */
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_mul(&out_num[i], &c->b_n, &c->t0);/* pref_n * sigma   */
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_copy(&out_den[i], &c->b_d);       /* pref_d           */
        if (st != SRMECH_OK) { return st; }
        st = eis_q_reduce(c, &out_num[i], &out_den[i]);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* The exact-rational q-series of E_k = 1 - (2k/B_k) SUM sigma_{k-1}(n) q^n:
 * out_num[e]/out_den[e] (e = 0..n_terms-1) <- the REDUCED coefficient of q^e
 * (out_num[0]/out_den[0] = 1/1), *out_len <- n_terms. k must be EVEN >= 2: k>=4 is
 * the modular E_k; k=2 is the QUASIMODULAR E_2 = 1 - 24 SUM sigma_1(n) q^n branch
 * (same formula, pref -4/B_2 = -24; the modularity DECISION stays Python-side).
 * The out_num[]/out_den[] arrays are caller-owned (n_terms srmech_bigint each, each
 * pre-bound to >= coeff_limbs limbs). SRMECH_ERR_BAD_INPUT on n_terms<1 / k<2 /
 * k odd / a NULL pointer; SRMECH_ERR_OVERFLOW if a coefficient (or the arena) is
 * too small. */
srmech_status_t srmech_eisenstein_qseries(
    size_t k, size_t n_terms, srmech_bigint_t *out_num, srmech_bigint_t *out_den,
    size_t *out_len, void *ws, size_t ws_len)
{
    eis_ctx_t c;
    srmech_bigint_t *bn_arr, *bd_arr;
    uint32_t *base, cap;
    size_t words, cur = 0u;
    srmech_status_t st;
    assert(out_num != NULL && out_den != NULL);
    assert(out_len != NULL);
    if (out_num == NULL || out_den == NULL || out_len == NULL || ws == NULL) {
        return SRMECH_ERR_BAD_INPUT;
    }
    /* k must be EVEN >= 2. k=2 is the QUASIMODULAR E_2 branch (the q-series is the
     * SAME normalized-Eisenstein formula at k=2: pref -4/B_2 = -24; E_2 is the
     * weight-2 quasimodular generator. The modular/quasimodular DECISION stays
     * Python-side — the Eisenstein(k) carrier still rejects k=2; E_2 enters only
     * through srmech.amsc.quasimodular_forms_ring). k=4,6,... are the modular E_k. */
    if (n_terms < 1u || k < 2u || (k % 2u) != 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    base = (uint32_t *)ws;
    words = ws_len / sizeof(uint32_t);
    cap = out_num[0].cap;                      /* one carrier at per-coeff width */
    if (cap < 1u) {
        return SRMECH_ERR_OVERFLOW;
    }
    st = eis_ctx_init(&c, cap, base, words, &cur);
    if (st != SRMECH_OK) { return st; }
    st = eis_carve_roster(&c, base, words, &cur, cap, (size_t)(k + 1u),
                          &bn_arr, &bd_arr);
    if (st != SRMECH_OK) { return st; }
    st = eis_prefactor(&c, k, bn_arr, bd_arr);
    if (st != SRMECH_OK) { return st; }
    st = eis_fill_coeffs(&c, k, n_terms, out_num, out_den);
    if (st != SRMECH_OK) { return st; }
    *out_len = n_terms;
    return SRMECH_OK;
}
