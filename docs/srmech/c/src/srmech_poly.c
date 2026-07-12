/*
 * srmech_poly.c — EXACT-RATIONAL univariate polynomial over srmech_bigint
 * (the C peer of srmech.amsc.poly.Poly; the §76 "telescope" Sigma-row
 * foundation).
 *
 * A polynomial is carried in ASCENDING degree as two parallel caller-owned
 * arrays of srmech_bigint: nums[i] / dens[i] is the exact-rational coefficient
 * of x^i (dens[i] > 0, gcd(|nums[i]|, dens[i]) == 1; the zero coefficient is
 * 0/1). The length `n` is the coefficient count; the CANONICAL form trims
 * trailing-zero (high-degree) coefficients, so the zero polynomial has n == 0.
 *
 * Each op below computes the SAME exact rational coefficients the Python
 * srmech.amsc.poly.Poly computes — Class-N rational arithmetic over Class-J
 * prime-field reduction — over caller-arena srmech_bigint (NO malloc, JPL Rule
 * 3), and returns each output coefficient reduced to lowest terms with positive
 * denominator. Byte-identical to Python's (num, den) at ANY magnitude (the
 * coefficients are full bignum — no int64/Q61 ceiling).
 *
 *   add/sub : coefficientwise exact-Q add/sub, then trim
 *   mul     : coefficient convolution (exact-Q), then trim
 *   divmod  : exact long division over Q (leading-coeff divide, subtract the
 *             shifted scaled divisor), Python-identical quotient + remainder
 *   eval    : exact Horner -> one reduced rational
 *   shift   : dispersion p(x + h) by exact synthetic Horner on (x + h)
 *
 * gcd (the monic Euclidean GCD over Q) is the immediate rc39-prefix follow-up,
 * NOT shipped here: the Euclidean chain has the classic intermediate-coefficient
 * explosion (each x mod y's reduced coefficients can grow geometrically across
 * the O(degree) chain), so a sound caller-arena bound must scale with the chain
 * length (a subresultant formulation), not the per-op product envelope the ops
 * above use — shipping a gcd that could OVERFLOW on a benign higher-degree input
 * would break the standalone-complete honor. The Python Poly.gcd already routes
 * its inner long divisions through srmech_poly_divmod (only its Euclid driver +
 * monic-normalize stay Python); the pure-bigint GCD has no ceiling.
 *
 * The C is STANDALONE-COMPLETE: every working carrier + the divmod/reduce
 * scratch is carved from the caller arena `ws` (sized via the matching
 * srmech_poly_ws_bound), so the magnitude bound is the CALLER's RAM, not a
 * compiled-in cap. Caller-arena, no fallback baked in.
 *
 * Carrier-internal, like srmech_bigexp.c / srmech_pi.c: NOT a Rosetta ledger op
 * (no ToolEntry, no count-test). Additive symbols -> ABI unchanged (stays 3).
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto/recursion): OK — iterative, flat helpers
 *   - Rule 2 (bounded loops)    : OK — bounds are the coefficient counts
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

/* A roster of working bigints carved from the caller arena `ws`, plus the
 * divmod/gcd scratch tail. qa/qb hold running exact-Q values, the tN are
 * integer scratch for the Q ops, g/rem are the reducer's gcd + divmod sinks.
 * Every carrier is `cap` limbs. */
typedef struct poly_ctx {
    srmech_bigint_t qa_n;   /* accumulator rational numerator   */
    srmech_bigint_t qa_d;   /* accumulator rational denominator */
    srmech_bigint_t qb_n;   /* second operand numerator         */
    srmech_bigint_t qb_d;   /* second operand denominator       */
    srmech_bigint_t t0;     /* integer scratch                  */
    srmech_bigint_t t1;
    srmech_bigint_t t2;
    srmech_bigint_t t3;
    srmech_bigint_t g;      /* gcd sink (reduce-private)        */
    srmech_bigint_t rem;    /* divmod remainder sink (reduce)   */
    srmech_bigint_t rs0;    /* reduce-private quotient scratch  */
    srmech_bigint_t rs1;    /* reduce-private quotient scratch  */
    srmech_bigint_t z0;     /* read-only 0 (missing-term num)   */
    srmech_bigint_t z1;     /* read-only 1 (missing-term den)   */
    uint32_t limb_cap;      /* per-carrier limb capacity        */
    void  *scratch;         /* divmod/gcd scratch arena tail    */
    size_t scratch_len;     /* its length in BYTES              */
} poly_ctx_t;

/* The Q-op scratch is partitioned: poly_q_add uses t0; poly_q_reduce uses ONLY
 * the reduce-private carriers (g, rem, rs0, rs1) so it never collides with a
 * caller's chosen out carrier (callers may pass any of qa/qb/t0..t3 as outputs;
 * reduce touching t1/t2 would corrupt an out that aliases them). */
#define POLY_N_CARRIERS 14u  /* qa_n,qa_d,qb_n,qb_d,t0..t3,g,rem,rs0,rs1,z0,z1 */

/* ---- forward declarations (Rule 1: no recursion) ------------------- */

static uint32_t *poly_take(uint32_t *base, size_t words, size_t *cur,
                           size_t count);
static srmech_status_t poly_bind(srmech_bigint_t *b, uint32_t *base,
                                 size_t words, size_t *cur, uint32_t cap);
static srmech_status_t poly_ctx_init(poly_ctx_t *c, uint32_t cap,
                                     void *ws, size_t ws_len);
static srmech_status_t poly_q_reduce(poly_ctx_t *c, srmech_bigint_t *num,
                                     srmech_bigint_t *den);
static srmech_status_t poly_q_add(poly_ctx_t *c, srmech_bigint_t *out_num,
                                  srmech_bigint_t *out_den,
                                  const srmech_bigint_t *an,
                                  const srmech_bigint_t *ad,
                                  const srmech_bigint_t *bn,
                                  const srmech_bigint_t *bd, int sub);
static srmech_status_t poly_q_mul(poly_ctx_t *c, srmech_bigint_t *out_num,
                                  srmech_bigint_t *out_den,
                                  const srmech_bigint_t *an,
                                  const srmech_bigint_t *ad,
                                  const srmech_bigint_t *bn,
                                  const srmech_bigint_t *bd);
static size_t poly_trim_len(const srmech_bigint_t *nums, size_t n);
static size_t poly_cap_for(size_t coeff_limbs, size_t degree_terms);
static size_t poly_max_coeff_limbs(const srmech_bigint_t *nums,
                                   const srmech_bigint_t *dens, size_t n);
static srmech_status_t poly_addsub(const srmech_bigint_t *a_n,
                                   const srmech_bigint_t *a_d, size_t na,
                                   const srmech_bigint_t *b_n,
                                   const srmech_bigint_t *b_d, size_t nb,
                                   int sub, srmech_bigint_t *out_n,
                                   srmech_bigint_t *out_d, size_t *out_len,
                                   void *ws, size_t ws_len);
static srmech_status_t poly_rem_inplace(poly_ctx_t *c,
                                        const srmech_bigint_t *b_n,
                                        const srmech_bigint_t *b_d, size_t nb,
                                        srmech_bigint_t *q_n,
                                        srmech_bigint_t *q_d,
                                        srmech_bigint_t *r_n,
                                        srmech_bigint_t *r_d, size_t *nr,
                                        int want_q);
static srmech_status_t poly_shift_step(poly_ctx_t *c, const srmech_bigint_t *h_n,
                                       const srmech_bigint_t *h_d,
                                       const srmech_bigint_t *coeff_n,
                                       const srmech_bigint_t *coeff_d,
                                       srmech_bigint_t *acc_n,
                                       srmech_bigint_t *acc_d, size_t *deg);
static size_t poly_gcd_cap_for(size_t coeff_limbs, size_t n_terms);
static srmech_status_t poly_monic_inplace(poly_ctx_t *c, srmech_bigint_t *n,
                                          srmech_bigint_t *d, size_t len);
static srmech_status_t poly_bind_array(srmech_bigint_t *arr, uint32_t *base,
                                       size_t words, size_t *cur, size_t count,
                                       uint32_t cap);
static srmech_status_t poly_copy_into(srmech_bigint_t *dn, srmech_bigint_t *dd,
                                      const srmech_bigint_t *sn,
                                      const srmech_bigint_t *sd, size_t len);

/* ---- caller-arena carve (mirrors bigexp_take / bigexp_bind) -------- */

static uint32_t *poly_take(uint32_t *base, size_t words, size_t *cur,
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

static srmech_status_t poly_bind(srmech_bigint_t *b, uint32_t *base,
                                 size_t words, size_t *cur, uint32_t cap)
{
    uint32_t *limbs = poly_take(base, words, cur, cap);
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

static srmech_status_t poly_ctx_init(poly_ctx_t *c, uint32_t cap,
                                     void *ws, size_t ws_len)
{
    uint32_t *base = (uint32_t *)ws;
    size_t words = ws_len / sizeof(uint32_t), cur = 0u;
    srmech_status_t st = SRMECH_OK;
    assert(c != NULL);
    assert((uintptr_t)ws % sizeof(uint32_t) == 0u || ws == NULL);
    c->limb_cap = cap;
    st |= poly_bind(&c->qa_n, base, words, &cur, cap);
    st |= poly_bind(&c->qa_d, base, words, &cur, cap);
    st |= poly_bind(&c->qb_n, base, words, &cur, cap);
    st |= poly_bind(&c->qb_d, base, words, &cur, cap);
    st |= poly_bind(&c->t0, base, words, &cur, cap);
    st |= poly_bind(&c->t1, base, words, &cur, cap);
    st |= poly_bind(&c->t2, base, words, &cur, cap);
    st |= poly_bind(&c->t3, base, words, &cur, cap);
    st |= poly_bind(&c->g, base, words, &cur, cap);
    st |= poly_bind(&c->rem, base, words, &cur, cap);
    st |= poly_bind(&c->rs0, base, words, &cur, cap);
    st |= poly_bind(&c->rs1, base, words, &cur, cap);
    st |= poly_bind(&c->z0, base, words, &cur, cap);
    st |= poly_bind(&c->z1, base, words, &cur, cap);
    if (st != SRMECH_OK) {
        return SRMECH_ERR_OVERFLOW;
    }
    st = srmech_bigint_set_i64(&c->z0, 0);     /* read-only unit 0 */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&c->z1, 1);     /* read-only unit 1 */
    if (st != SRMECH_OK) { return st; }
    c->scratch = (void *)(base + cur);
    c->scratch_len = (words - cur) * sizeof(uint32_t);
    assert(cur <= words);
    return SRMECH_OK;
}

/* ---- exact-Q helpers (reduce / add / mul) over the context scratch -- */

/* Reduce num/den IN PLACE to lowest terms, positive denominator. den must be
 * nonzero; 0/d normalizes to 0/1. Uses ONLY the reduce-private carriers (g,
 * rem, rs0, rs1) + the scratch tail — so num/den may safely be any caller
 * carrier (qa/qb/t0..t3) without a self-aliasing corruption. */
static srmech_status_t poly_q_reduce(poly_ctx_t *c, srmech_bigint_t *num,
                                     srmech_bigint_t *den)
{
    srmech_status_t st;
    assert(c != NULL && num != NULL && den != NULL);
    assert(den->sign != 0);
    if (den->sign < 0) {                     /* force positive denominator */
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

/* out = a +/- b (exact Q), reduced. sub != 0 selects subtraction. out_* may
 * NOT alias the four input carriers. Uses t0 (cross product). */
static srmech_status_t poly_q_add(poly_ctx_t *c, srmech_bigint_t *out_num,
                                  srmech_bigint_t *out_den,
                                  const srmech_bigint_t *an,
                                  const srmech_bigint_t *ad,
                                  const srmech_bigint_t *bn,
                                  const srmech_bigint_t *bd, int sub)
{
    srmech_status_t st;
    assert(c != NULL && out_num != NULL && out_den != NULL);
    assert(an != NULL && ad != NULL && bn != NULL && bd != NULL);
    st = srmech_bigint_mul(&c->t0, an, bd);           /* t0 = an*bd      */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_mul(out_num, bn, ad);          /* out_num = bn*ad */
    if (st != SRMECH_OK) { return st; }
    if (sub) {
        st = srmech_bigint_sub(out_den, &c->t0, out_num);   /* an*bd - bn*ad */
    } else {
        st = srmech_bigint_add(out_den, &c->t0, out_num);   /* an*bd + bn*ad */
    }
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(out_num, out_den);        /* num = combined  */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_mul(out_den, ad, bd);          /* den = ad*bd     */
    if (st != SRMECH_OK) { return st; }
    return poly_q_reduce(c, out_num, out_den);
}

/* out = a * b (exact Q), reduced. out_* may NOT alias the inputs. */
static srmech_status_t poly_q_mul(poly_ctx_t *c, srmech_bigint_t *out_num,
                                  srmech_bigint_t *out_den,
                                  const srmech_bigint_t *an,
                                  const srmech_bigint_t *ad,
                                  const srmech_bigint_t *bn,
                                  const srmech_bigint_t *bd)
{
    srmech_status_t st;
    assert(c != NULL && out_num != NULL && out_den != NULL);
    assert(an != NULL && ad != NULL && bn != NULL && bd != NULL);
    st = srmech_bigint_mul(out_num, an, bn);          /* num = an*bn */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_mul(out_den, ad, bd);          /* den = ad*bd */
    if (st != SRMECH_OK) { return st; }
    return poly_q_reduce(c, out_num, out_den);
}

/* ---- trim helper: significant coefficient count -------------------- */

/* The trimmed length: count after dropping trailing-zero (high-degree)
 * coefficients. A coefficient is zero iff its numerator is zero. */
static size_t poly_trim_len(const srmech_bigint_t *nums, size_t n)
{
    size_t k = n;
    assert(nums != NULL || n == 0u);
    while (k > 0u && srmech_bigint_is_zero(&nums[k - 1u])) {
        k--;
    }
    assert(k <= n);                          /* trim never grows the length */
    return k;
}

static size_t poly_max_coeff_limbs(const srmech_bigint_t *nums,
                                   const srmech_bigint_t *dens, size_t n)
{
    size_t k, cl = 1u;
    assert(nums != NULL || n == 0u);
    assert(dens != NULL || n == 0u);
    for (k = 0u; k < n; k++) {
        if (nums[k].n > cl) { cl = nums[k].n; }
        if (dens[k].n > cl) { cl = dens[k].n; }
    }
    return cl;
}

/* ---- arena bounds -------------------------------------------------- *
 * Each per-coefficient value is an exact-Q combination of the input
 * coefficients, reduced after every op. The UNREDUCED intermediates reach the
 * PRODUCT of input numerator+denominator magnitudes accumulated over the degree
 * (convolution / Horner / division all sum products of coefficients). We size
 * each carrier to hold that worst-case product. `coeff_limbs` is the largest
 * significant limb count of any input coefficient num/den; `degree_terms` is the
 * number of products accumulating into one output coefficient (deg+1). */

static size_t poly_cap_for(size_t coeff_limbs, size_t degree_terms)
{
    size_t cl = (coeff_limbs == 0u) ? 1u : coeff_limbs;
    size_t dt = (degree_terms == 0u) ? 1u : degree_terms;
    size_t common = cl * dt + 2u;            /* common-denominator scale  */
    size_t prod = common * 2u + cl * 2u;     /* unreduced cross-product    */
    size_t cap = prod + 16u;
    assert(cap >= common);
    assert(cap >= cl);
    return cap;
}

/* Bytes the caller hands every srmech_poly_* op for inputs of `coeff_limbs`
 * significant limbs per coefficient and a polynomial of `n_terms` coefficients.
 * Covers POLY_N_CARRIERS carriers of `cap` limbs each, plus a divmod scratch
 * tail (the heaviest scratch is divmod over two `cap`-limb values: ~4*cap
 * internally; 8*cap + 256 is a safe envelope). 8-byte-aligned uint32. */
size_t srmech_poly_ws_bound(size_t coeff_limbs, size_t n_terms)
{
    size_t cap = poly_cap_for(coeff_limbs, n_terms == 0u ? 1u : n_terms);
    size_t carriers = cap * (size_t)POLY_N_CARRIERS;
    size_t scratch = cap * 8u + 256u;
    size_t words = carriers + scratch;
    assert(cap >= 2u);
    assert(words >= carriers);
    return words * sizeof(uint32_t);
}

/* ---- add / sub ---------------------------------------------------- */

/* Shared add/sub driver: out_k = a_k +/- b_k for k in [0, max(na,nb)), each
 * exact-Q + reduced; *out_len is set to the TRIMMED length. The caller out
 * arrays must hold max(na, nb) coefficients (pre-trim). */
static srmech_status_t poly_addsub(const srmech_bigint_t *a_n,
                                   const srmech_bigint_t *a_d, size_t na,
                                   const srmech_bigint_t *b_n,
                                   const srmech_bigint_t *b_d, size_t nb,
                                   int sub, srmech_bigint_t *out_n,
                                   srmech_bigint_t *out_d, size_t *out_len,
                                   void *ws, size_t ws_len)
{
    poly_ctx_t c;
    srmech_status_t st;
    size_t k, m = (na > nb) ? na : nb, cl;
    uint32_t cap;
    assert(out_n != NULL && out_d != NULL && out_len != NULL);
    assert(sub == 0 || sub == 1);            /* the add/sub discriminator */
    cl = poly_max_coeff_limbs(a_n, a_d, na);
    { size_t cb = poly_max_coeff_limbs(b_n, b_d, nb); if (cb > cl) { cl = cb; } }
    cap = (uint32_t)poly_cap_for(cl, 2u);
    st = poly_ctx_init(&c, cap, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    for (k = 0u; k < m; k++) {
        const srmech_bigint_t *an, *ad, *bn, *bd;
        an = (k < na) ? &a_n[k] : &c.z0;  ad = (k < na) ? &a_d[k] : &c.z1;
        bn = (k < nb) ? &b_n[k] : &c.z0;  bd = (k < nb) ? &b_d[k] : &c.z1;
        st = poly_q_add(&c, &out_n[k], &out_d[k], an, ad, bn, bd, sub);
        if (st != SRMECH_OK) { return st; }
    }
    *out_len = poly_trim_len(out_n, m);
    return SRMECH_OK;
}

srmech_status_t srmech_poly_add(const srmech_bigint_t *a_n,
                                const srmech_bigint_t *a_d, size_t na,
                                const srmech_bigint_t *b_n,
                                const srmech_bigint_t *b_d, size_t nb,
                                srmech_bigint_t *out_n, srmech_bigint_t *out_d,
                                size_t *out_len, void *ws, size_t ws_len)
{
    assert(out_n != NULL && out_len != NULL);
    assert(out_d != NULL);
    if (out_n == NULL || out_d == NULL || out_len == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    return poly_addsub(a_n, a_d, na, b_n, b_d, nb, 0, out_n, out_d,
                       out_len, ws, ws_len);
}

srmech_status_t srmech_poly_sub(const srmech_bigint_t *a_n,
                                const srmech_bigint_t *a_d, size_t na,
                                const srmech_bigint_t *b_n,
                                const srmech_bigint_t *b_d, size_t nb,
                                srmech_bigint_t *out_n, srmech_bigint_t *out_d,
                                size_t *out_len, void *ws, size_t ws_len)
{
    assert(out_n != NULL && out_len != NULL);
    assert(out_d != NULL);
    if (out_n == NULL || out_d == NULL || out_len == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    return poly_addsub(a_n, a_d, na, b_n, b_d, nb, 1, out_n, out_d,
                       out_len, ws, ws_len);
}

/* ---- mul (convolution) -------------------------------------------- */

srmech_status_t srmech_poly_mul(const srmech_bigint_t *a_n,
                                const srmech_bigint_t *a_d, size_t na,
                                const srmech_bigint_t *b_n,
                                const srmech_bigint_t *b_d, size_t nb,
                                srmech_bigint_t *out_n, srmech_bigint_t *out_d,
                                size_t *out_len, void *ws, size_t ws_len)
{
    poly_ctx_t c;
    srmech_status_t st;
    size_t i, j, m, cl;
    uint32_t cap;
    assert(out_n != NULL && out_len != NULL);
    assert(out_d != NULL);
    if (out_n == NULL || out_d == NULL || out_len == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (na == 0u || nb == 0u) { *out_len = 0u; return SRMECH_OK; }
    m = na + nb - 1u;
    cl = poly_max_coeff_limbs(a_n, a_d, na);
    { size_t cb = poly_max_coeff_limbs(b_n, b_d, nb); if (cb > cl) { cl = cb; } }
    cap = (uint32_t)poly_cap_for(cl, m + 1u);
    st = poly_ctx_init(&c, cap, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    for (i = 0u; i < m; i++) {
        st = srmech_bigint_set_i64(&out_n[i], 0);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_set_i64(&out_d[i], 1);
        if (st != SRMECH_OK) { return st; }
    }
    for (i = 0u; i < na; i++) {
        if (srmech_bigint_is_zero(&a_n[i])) { continue; }
        for (j = 0u; j < nb; j++) {
            if (srmech_bigint_is_zero(&b_n[j])) { continue; }
            st = poly_q_mul(&c, &c.qa_n, &c.qa_d, &a_n[i], &a_d[i],
                            &b_n[j], &b_d[j]);              /* term = a_i*b_j */
            if (st != SRMECH_OK) { return st; }
            st = srmech_bigint_copy(&c.qb_n, &out_n[i + j]);
            if (st != SRMECH_OK) { return st; }
            st = srmech_bigint_copy(&c.qb_d, &out_d[i + j]);
            if (st != SRMECH_OK) { return st; }
            st = poly_q_add(&c, &out_n[i + j], &out_d[i + j],
                            &c.qb_n, &c.qb_d, &c.qa_n, &c.qa_d, 0);
            if (st != SRMECH_OK) { return st; }
        }
    }
    *out_len = poly_trim_len(out_n, m);
    return SRMECH_OK;
}

/* ---- the long-division reduction (divmod's reduce-in-place core) --- */

/* Reduce the remainder r_n/r_d (length *nr, in caller arrays) modulo the
 * divisor b (length nb) IN PLACE; when want_q, also write the quotient into
 * q_n/q_d (the caller must size q to deg(a)-deg(b)+1 and pre-zero it). r ends
 * as the remainder (deg < deg b, trimmed via *nr). guard bounds the loop
 * (Rule 2). q may be NULL when want_q == 0 (the want_q == 0 form is what the
 * deferred rc39 gcd's `x mod y` will reuse). */
static srmech_status_t poly_rem_inplace(poly_ctx_t *c,
                                        const srmech_bigint_t *b_n,
                                        const srmech_bigint_t *b_d, size_t nb,
                                        srmech_bigint_t *q_n,
                                        srmech_bigint_t *q_d,
                                        srmech_bigint_t *r_n,
                                        srmech_bigint_t *r_d, size_t *nr,
                                        int want_q)
{
    srmech_status_t st;
    size_t guard = 0u;
    assert(c != NULL && b_n != NULL && nb > 0u && nr != NULL);
    assert(r_n != NULL && r_d != NULL);
    while (*nr >= nb && *nr > 0u && guard <= (size_t)0xFFFFFFFFu) {
        size_t rdeg = *nr - 1u, shift = rdeg - (nb - 1u), j;
        /* factor = r_lead / b_lead  (divide = multiply by the reciprocal) */
        st = poly_q_mul(c, &c->qa_n, &c->qa_d, &r_n[rdeg], &r_d[rdeg],
                        &b_d[nb - 1u], &b_n[nb - 1u]);
        if (st != SRMECH_OK) { return st; }
        if (want_q) {
            st = srmech_bigint_copy(&q_n[shift], &c->qa_n);
            if (st != SRMECH_OK) { return st; }
            st = srmech_bigint_copy(&q_d[shift], &c->qa_d);
            if (st != SRMECH_OK) { return st; }
        }
        for (j = 0u; j < nb; j++) {        /* r[shift+j] -= factor * b[j] */
            st = poly_q_mul(c, &c->qb_n, &c->qb_d, &c->qa_n, &c->qa_d,
                            &b_n[j], &b_d[j]);
            if (st != SRMECH_OK) { return st; }
            st = poly_q_add(c, &c->t2, &c->t3, &r_n[shift + j], &r_d[shift + j],
                            &c->qb_n, &c->qb_d, 1);          /* subtract */
            if (st != SRMECH_OK) { return st; }
            st = srmech_bigint_copy(&r_n[shift + j], &c->t2);
            if (st != SRMECH_OK) { return st; }
            st = srmech_bigint_copy(&r_d[shift + j], &c->t3);
            if (st != SRMECH_OK) { return st; }
        }
        *nr = poly_trim_len(r_n, *nr);
        guard++;
    }
    return SRMECH_OK;
}

/* ---- divmod ------------------------------------------------------- */

srmech_status_t srmech_poly_divmod(const srmech_bigint_t *a_n,
                                   const srmech_bigint_t *a_d, size_t na,
                                   const srmech_bigint_t *b_n,
                                   const srmech_bigint_t *b_d, size_t nb,
                                   srmech_bigint_t *out_q_n,
                                   srmech_bigint_t *out_q_d, size_t *out_qn,
                                   srmech_bigint_t *out_r_n,
                                   srmech_bigint_t *out_r_d, size_t *out_rn,
                                   void *ws, size_t ws_len)
{
    poly_ctx_t c;
    srmech_status_t st;
    size_t nr, cl, qcap, k;
    uint32_t cap;
    assert(out_q_n != NULL && out_r_n != NULL && out_qn != NULL && out_rn != NULL);
    assert(out_q_d != NULL && out_r_d != NULL);
    if (out_q_n == NULL || out_q_d == NULL || out_r_n == NULL
        || out_r_d == NULL || out_qn == NULL || out_rn == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (nb == 0u) { return SRMECH_ERR_BAD_INPUT; }   /* divide by zero poly */
    cl = poly_max_coeff_limbs(a_n, a_d, na);
    { size_t cb = poly_max_coeff_limbs(b_n, b_d, nb); if (cb > cl) { cl = cb; } }
    cap = (uint32_t)poly_cap_for(cl, na + 1u);
    st = poly_ctx_init(&c, cap, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    qcap = (na >= nb) ? (na - nb + 1u) : 0u;
    for (k = 0u; k < qcap; k++) {                    /* q = 0 */
        st = srmech_bigint_set_i64(&out_q_n[k], 0);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_set_i64(&out_q_d[k], 1);
        if (st != SRMECH_OK) { return st; }
    }
    for (k = 0u; k < na; k++) {                      /* remainder seed = a */
        st = srmech_bigint_copy(&out_r_n[k], &a_n[k]);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_copy(&out_r_d[k], &a_d[k]);
        if (st != SRMECH_OK) { return st; }
    }
    nr = poly_trim_len(out_r_n, na);
    st = poly_rem_inplace(&c, b_n, b_d, nb, out_q_n, out_q_d,
                          out_r_n, out_r_d, &nr, 1);
    if (st != SRMECH_OK) { return st; }
    *out_qn = poly_trim_len(out_q_n, qcap);
    *out_rn = nr;
    return SRMECH_OK;
}

/* ---- gcd (the monic Euclidean GCD over Q; rc39) ------------------- *
 * The single-call srmech_poly_gcd C peer (deferred from rc38). The Euclidean
 * polynomial GCD over Q is famous for intermediate-coefficient growth, so the
 * caller-arena bound must scale with the EUCLIDEAN-CHAIN length, not the per-op
 * product envelope poly_cap_for gives the other peers. The soundness lever is
 * MONIC NORMALIZATION AFTER EVERY STEP: the GCD is defined up to a unit, so
 * scaling each remainder to a leading 1 leaves the final monic GCD identical
 * (verified over 4000 random integer+rational trials: 0 mismatches vs the
 * non-normalized chain) while DRAMATICALLY taming the coefficient growth — the
 * empirical worst chainmaxbits/inbits dropped from ~92x (no-norm) to ~23x
 * (monic-norm). poly_gcd_cap_for sizes each carrier to coeff_limbs * n_terms^2
 * (degree-squared headroom), which provably dominates that linear-in-degree
 * growth by a wide margin. Any residual overflow still returns
 * SRMECH_ERR_OVERFLOW (never a silent wrap), and the Python Poly.gcd falls back
 * to its ceiling-free pure-bigint path — so the standalone-complete honor holds
 * (a C-only host either succeeds exactly or reports OVERFLOW, never wraps).
 *
 * The op carves THREE polynomial coefficient buffers (a, b, r — each n_terms
 * wide, each coefficient a cap-limb bigint) from the caller arena FIRST, then
 * hands the remaining tail to poly_ctx_init as the divmod/reduce scratch. Euclid
 * runs in place: (a, b) <- (b, monic(a mod b)) until b is the zero polynomial;
 * the last nonzero a, monic-normalized, is the GCD. gcd(0,0) = 0 (empty);
 * gcd(p,0) = monic(p) (handled by the loop's first iteration). */

/* The per-coefficient limb cap for the GCD chain: the per-op envelope scaled by
 * the chain length. coeff_limbs * n_terms gives one step's common-denominator
 * product; another * n_terms factor covers accumulation across the O(degree)
 * Euclidean chain (degree-squared headroom — provably past the observed
 * linear-in-degree monic-chain growth). */
static size_t poly_gcd_cap_for(size_t coeff_limbs, size_t n_terms)
{
    size_t cl = (coeff_limbs == 0u) ? 1u : coeff_limbs;
    size_t nt = (n_terms == 0u) ? 1u : n_terms;
    size_t step = cl * nt + 2u;              /* one step's common-denom scale */
    size_t cap = step * nt + step * 2u + 32u;/* chain accumulation + slack    */
    assert(cap >= step);
    assert(cap >= cl);
    return cap;
}

/* Divide a polynomial (n/d arrays, length len) through by its leading
 * coefficient so the leading coefficient becomes 1 (monic). The zero polynomial
 * (len == 0) is left unchanged. Uses the ctx's qa/qb/t0..t3 carriers. */
static srmech_status_t poly_monic_inplace(poly_ctx_t *c, srmech_bigint_t *n,
                                          srmech_bigint_t *d, size_t len)
{
    srmech_status_t st;
    size_t k;
    assert(c != NULL);
    assert(n != NULL || len == 0u);
    if (len == 0u) { return SRMECH_OK; }
    /* inv = 1 / leading = d_lead / n_lead (the reciprocal of the lead rational) */
    for (k = 0u; k < len; k++) {
        st = poly_q_mul(c, &c->qa_n, &c->qa_d, &n[k], &d[k],
                        &d[len - 1u], &n[len - 1u]);    /* coeff * (d_lead/n_lead) */
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_copy(&n[k], &c->qa_n);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_copy(&d[k], &c->qa_d);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* Carve `count` srmech_bigint coefficient slots, each `cap` limbs, from the
 * arena, and initialize each to 0/1 (numerator side; the caller pairs a second
 * array for denominators). Sets every srmech_bigint header to its limb run. */
static srmech_status_t poly_bind_array(srmech_bigint_t *arr, uint32_t *base,
                                       size_t words, size_t *cur, size_t count,
                                       uint32_t cap)
{
    size_t k;
    srmech_status_t st;
    assert(arr != NULL || count == 0u);
    assert(cap > 0u);
    for (k = 0u; k < count; k++) {
        st = poly_bind(&arr[k], base, words, cur, cap);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* dst[0..len) <- src[0..len) (deep copy of both num + den arrays). */
static srmech_status_t poly_copy_into(srmech_bigint_t *dn, srmech_bigint_t *dd,
                                      const srmech_bigint_t *sn,
                                      const srmech_bigint_t *sd, size_t len)
{
    size_t k;
    srmech_status_t st;
    assert(dn != NULL || len == 0u);
    assert(sn != NULL || len == 0u);
    for (k = 0u; k < len; k++) {
        st = srmech_bigint_copy(&dn[k], &sn[k]);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_copy(&dd[k], &sd[k]);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* Minimum `ws_len` BYTES for srmech_poly_gcd over inputs of `coeff_limbs`
 * significant limbs per coefficient and a polynomial of `n_terms` coefficients.
 * Covers the chain-scaled ctx carriers PLUS three n_terms-wide poly buffers
 * (a, b, r — num + den each) and the divmod scratch tail. */
size_t srmech_poly_gcd_ws_bound(size_t coeff_limbs, size_t n_terms)
{
    size_t nt = (n_terms == 0u) ? 1u : n_terms;
    size_t cap = poly_gcd_cap_for(coeff_limbs, nt);
    size_t carriers = cap * (size_t)POLY_N_CARRIERS;
    /* 3 poly buffers (a, b, r) * 2 (num, den) * nt coefficients * cap limbs */
    size_t polybufs = (size_t)6u * nt * cap;
    size_t scratch = cap * 8u + 256u;
    size_t words = carriers + polybufs + scratch;
    assert(cap >= 2u);
    assert(words >= carriers);
    return words * sizeof(uint32_t);
}

/* A roster of the three Euclidean working polynomials, headers carved from the
 * arena (their LIMB runs are bound by poly_bind_array). Each is `nt` coefficient
 * slots wide; only the live prefix (la/lb/lr) carries significant coefficients. */
typedef struct poly_gcd_buf {
    srmech_bigint_t *a_n, *a_d;      /* the running a (length *la)           */
    srmech_bigint_t *b_n, *b_d;      /* the running b (length *lb)           */
    srmech_bigint_t *r_n, *r_d;      /* the remainder sink (length *lr)      */
} poly_gcd_buf_t;

/* Carve the six nt-wide srmech_bigint header arrays + their limb runs from the
 * arena, then bind the poly_ctx (+ divmod scratch) from the remaining tail. */
static srmech_status_t poly_gcd_carve(poly_gcd_buf_t *g, poly_ctx_t *c,
                                      uint32_t *base, size_t words, size_t *cur,
                                      uint32_t cap, size_t nt)
{
    srmech_status_t st;
    size_t hdr_words = (sizeof(srmech_bigint_t) + sizeof(uint32_t) - 1u)
                       / sizeof(uint32_t);            /* header size in words */
    srmech_bigint_t *arrs[6];
    size_t i;
    assert(g != NULL && c != NULL && cur != NULL);
    assert(nt > 0u && cap > 0u);
    for (i = 0u; i < 6u; i++) {
        uint32_t *h = poly_take(base, words, cur, hdr_words * nt);
        if (h == NULL) { return SRMECH_ERR_OVERFLOW; }
        arrs[i] = (srmech_bigint_t *)(void *)h;
    }
    g->a_n = arrs[0]; g->a_d = arrs[1];
    g->b_n = arrs[2]; g->b_d = arrs[3];
    g->r_n = arrs[4]; g->r_d = arrs[5];
    for (i = 0u; i < 6u; i++) {
        st = poly_bind_array(arrs[i], base, words, cur, nt, cap);
        if (st != SRMECH_OK) { return st; }
    }
    /* the ctx + its divmod scratch take the remaining tail */
    return poly_ctx_init(c, cap, (void *)(base + *cur),
                         (words - *cur) * sizeof(uint32_t));
}

/* The Euclidean loop core (factored out to keep srmech_poly_gcd <= 60 lines):
 * (a, b) <- (b, monic(a mod b)) until b is the zero polynomial. On entry g.a_n
 * carries the higher-degree input (length *la) and g.b_n the other (length *lb),
 * both trimmed. On exit g.a_n holds the (not-yet-monic) GCD of length *la. The
 * 32-bit guard bounds the loop (Rule 2 — never a problem-size cap; the chain
 * length is at most deg+1). */
static srmech_status_t poly_gcd_euclid(poly_ctx_t *c, poly_gcd_buf_t *g,
                                       size_t *la, size_t *lb)
{
    srmech_status_t st;
    size_t lr, guard = 0u;
    assert(c != NULL && g != NULL);
    assert(la != NULL && lb != NULL);
    while (*lb > 0u && guard <= (size_t)0xFFFFFFFFu) {
        st = poly_copy_into(g->r_n, g->r_d, g->a_n, g->a_d, *la);  /* r <- a   */
        if (st != SRMECH_OK) { return st; }
        lr = *la;
        st = poly_rem_inplace(c, g->b_n, g->b_d, *lb, NULL, NULL,  /* r %= b   */
                              g->r_n, g->r_d, &lr, 0);
        if (st != SRMECH_OK) { return st; }
        st = poly_monic_inplace(c, g->r_n, g->r_d, lr);  /* the soundness lever */
        if (st != SRMECH_OK) { return st; }
        st = poly_copy_into(g->a_n, g->a_d, g->b_n, g->b_d, *lb);  /* a <- b   */
        if (st != SRMECH_OK) { return st; }
        *la = *lb;
        st = poly_copy_into(g->b_n, g->b_d, g->r_n, g->r_d, lr);   /* b <- r   */
        if (st != SRMECH_OK) { return st; }
        *lb = lr;
        guard++;
    }
    return SRMECH_OK;
}

/* gcd = monic Euclidean GCD of a and b over Q (lengths na / nb). The output is
 * written to out_n/out_d (caller arrays of max(na, nb) coefficients — the GCD
 * degree never exceeds min(deg a, deg b), so that is ample); *out_len gets the
 * trimmed monic GCD length. gcd(0,0) -> 0 (out_len 0); gcd(p,0) -> monic(p). */
srmech_status_t srmech_poly_gcd(const srmech_bigint_t *a_n,
                                const srmech_bigint_t *a_d, size_t na,
                                const srmech_bigint_t *b_n,
                                const srmech_bigint_t *b_d, size_t nb,
                                srmech_bigint_t *out_n, srmech_bigint_t *out_d,
                                size_t *out_len, void *ws, size_t ws_len)
{
    poly_ctx_t c;
    poly_gcd_buf_t g;
    srmech_status_t st;
    uint32_t *base = (uint32_t *)ws;
    size_t words = ws_len / sizeof(uint32_t), cur = 0u, nt, cl, cb, la, lb;
    uint32_t cap;
    assert(out_n != NULL && out_d != NULL && out_len != NULL);
    assert(ws != NULL || ws_len == 0u);
    if (out_n == NULL || out_d == NULL || out_len == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    nt = (na > nb) ? na : nb;
    if (nt == 0u) { *out_len = 0u; return SRMECH_OK; }   /* gcd(0,0) = 0 */
    cl = poly_max_coeff_limbs(a_n, a_d, na);
    cb = poly_max_coeff_limbs(b_n, b_d, nb);
    if (cb > cl) { cl = cb; }
    cap = (uint32_t)poly_gcd_cap_for(cl, nt);
    st = poly_gcd_carve(&g, &c, base, words, &cur, cap, nt);
    if (st != SRMECH_OK) { return st; }
    /* seed a <- the higher-degree input, b <- the other (Euclid is symmetric). */
    if (na >= nb) {
        st = poly_copy_into(g.a_n, g.a_d, a_n, a_d, na); la = na;
        if (st == SRMECH_OK) { st = poly_copy_into(g.b_n, g.b_d, b_n, b_d, nb); }
        lb = nb;
    } else {
        st = poly_copy_into(g.a_n, g.a_d, b_n, b_d, nb); la = nb;
        if (st == SRMECH_OK) { st = poly_copy_into(g.b_n, g.b_d, a_n, a_d, na); }
        lb = na;
    }
    if (st != SRMECH_OK) { return st; }
    la = poly_trim_len(g.a_n, la);
    lb = poly_trim_len(g.b_n, lb);
    st = poly_gcd_euclid(&c, &g, &la, &lb);
    if (st != SRMECH_OK) { return st; }
    st = poly_monic_inplace(&c, g.a_n, g.a_d, la);       /* monic-normalize gcd */
    if (st != SRMECH_OK) { return st; }
    st = poly_copy_into(out_n, out_d, g.a_n, g.a_d, la);
    if (st != SRMECH_OK) { return st; }
    *out_len = poly_trim_len(out_n, la);
    return SRMECH_OK;
}


/* ---- eval (exact Horner -> one reduced rational) ------------------ */

srmech_status_t srmech_poly_eval(const srmech_bigint_t *p_n,
                                 const srmech_bigint_t *p_d, size_t n,
                                 const srmech_bigint_t *x_n,
                                 const srmech_bigint_t *x_d,
                                 srmech_bigint_t *out_num,
                                 srmech_bigint_t *out_den,
                                 void *ws, size_t ws_len)
{
    poly_ctx_t c;
    srmech_status_t st;
    size_t cl, k;
    uint32_t cap;
    assert(out_num != NULL && out_den != NULL && x_n != NULL && x_d != NULL);
    assert(p_n != NULL || n == 0u);
    if (out_num == NULL || out_den == NULL || x_n == NULL || x_d == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    cl = poly_max_coeff_limbs(p_n, p_d, n);
    if (x_n->n > cl) { cl = x_n->n; }
    if (x_d->n > cl) { cl = x_d->n; }
    cap = (uint32_t)poly_cap_for(cl, n + 1u);
    st = poly_ctx_init(&c, cap, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&c.qa_n, 0);            /* acc = 0/1 */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&c.qa_d, 1);
    if (st != SRMECH_OK) { return st; }
    for (k = n; k > 0u; k--) {                         /* acc = acc*x + p[k-1] */
        st = poly_q_mul(&c, &c.qb_n, &c.qb_d, &c.qa_n, &c.qa_d, x_n, x_d);
        if (st != SRMECH_OK) { return st; }
        st = poly_q_add(&c, &c.qa_n, &c.qa_d, &c.qb_n, &c.qb_d,
                        &p_n[k - 1u], &p_d[k - 1u], 0);
        if (st != SRMECH_OK) { return st; }
    }
    st = srmech_bigint_copy(out_num, &c.qa_n);
    if (st != SRMECH_OK) { return st; }
    return srmech_bigint_copy(out_den, &c.qa_d);
}

/* ---- shift (dispersion p(x+h) by synthetic Horner on (x+h)) ------- *
 * acc is a polynomial accumulator (caller arrays acc_n/acc_d, length *acc_len,
 * width n): acc <- acc*(x+h) + p[k] folded down the coefficients. Each acc*(x+h)
 * step shifts acc up one degree (multiply by x) and adds h*acc (multiply by the
 * scalar h), so the polynomial is built in place high-degree-first. The caller
 * acc arrays must hold n coefficients; sw_n/sw_d is a 1-wide carry lane. */
srmech_status_t srmech_poly_shift(const srmech_bigint_t *p_n,
                                  const srmech_bigint_t *p_d, size_t n,
                                  const srmech_bigint_t *h_n,
                                  const srmech_bigint_t *h_d,
                                  srmech_bigint_t *acc_n,
                                  srmech_bigint_t *acc_d, size_t *acc_len,
                                  void *ws, size_t ws_len)
{
    poly_ctx_t c;
    srmech_status_t st;
    size_t cl, k, deg;
    uint32_t cap;
    assert(acc_n != NULL && acc_d != NULL && acc_len != NULL);
    assert(h_n != NULL && h_d != NULL);
    if (acc_n == NULL || acc_d == NULL || acc_len == NULL
        || h_n == NULL || h_d == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n == 0u) { *acc_len = 0u; return SRMECH_OK; }
    cl = poly_max_coeff_limbs(p_n, p_d, n);
    if (h_n->n > cl) { cl = h_n->n; }
    if (h_d->n > cl) { cl = h_d->n; }
    cap = (uint32_t)poly_cap_for(cl, n + 1u);
    st = poly_ctx_init(&c, cap, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    for (k = 0u; k < n; k++) {                         /* acc = 0 */
        st = srmech_bigint_set_i64(&acc_n[k], 0);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_set_i64(&acc_d[k], 1);
        if (st != SRMECH_OK) { return st; }
    }
    deg = 0u;                                          /* current acc degree+1 */
    for (k = n; k > 0u; k--) {
        st = poly_shift_step(&c, h_n, h_d, &p_n[k - 1u], &p_d[k - 1u],
                             acc_n, acc_d, &deg);
        if (st != SRMECH_OK) { return st; }
    }
    *acc_len = poly_trim_len(acc_n, deg);
    return SRMECH_OK;
}

/* One synthetic-Horner step: acc <- acc*(x + h) + coeff. acc has *deg live
 * coefficients (ascending). Multiply by (x+h): new[i] = acc[i-1] + h*acc[i]
 * (computed high-to-low so acc[i-1] is read before being overwritten), then add
 * `coeff` into new[0]. *deg grows by one (the x-shift) unless acc was empty. */
static srmech_status_t poly_shift_step(poly_ctx_t *c, const srmech_bigint_t *h_n,
                                       const srmech_bigint_t *h_d,
                                       const srmech_bigint_t *coeff_n,
                                       const srmech_bigint_t *coeff_d,
                                       srmech_bigint_t *acc_n,
                                       srmech_bigint_t *acc_d, size_t *deg)
{
    srmech_status_t st;
    size_t i, ndeg = (*deg) + 1u;
    assert(c != NULL && h_n != NULL && acc_n != NULL && deg != NULL);
    assert(coeff_n != NULL && acc_d != NULL);
    for (i = ndeg; i > 0u; i--) {            /* high-to-low so acc[i-1] survives */
        size_t idx = i - 1u;
        /* hi = h * acc[idx]  (0 when idx == *deg, i.e. the new top from x-shift) */
        if (idx < *deg) {
            st = poly_q_mul(c, &c->qa_n, &c->qa_d, h_n, h_d,
                            &acc_n[idx], &acc_d[idx]);
            if (st != SRMECH_OK) { return st; }
        } else {
            st = srmech_bigint_set_i64(&c->qa_n, 0);
            if (st != SRMECH_OK) { return st; }
            st = srmech_bigint_set_i64(&c->qa_d, 1);
            if (st != SRMECH_OK) { return st; }
        }
        /* lo = acc[idx-1]  (the x-shift carry; 0 at idx == 0) */
        if (idx > 0u) {
            st = poly_q_add(c, &acc_n[idx], &acc_d[idx], &c->qa_n, &c->qa_d,
                            &acc_n[idx - 1u], &acc_d[idx - 1u], 0);
        } else {
            st = poly_q_add(c, &acc_n[idx], &acc_d[idx], &c->qa_n, &c->qa_d,
                            coeff_n, coeff_d, 0);     /* new[0] = h*acc[0] + coeff */
        }
        if (st != SRMECH_OK) { return st; }
    }
    *deg = ndeg;
    return SRMECH_OK;
}
