/*
 * srmech_quasimodular_forms_ring.c — the EXACT-rational level-1 C[E2,E4,E6]
 * QUASIMODULAR-forms-ring MEMBERSHIP DECISION (the C peer of
 * srmech.amsc.quasimodular_forms_ring.QuasiModularFormsRing.represent; the FOURTH
 * rung of the WEIGHT axis, after the rc82 eta-quotient + rc83 Eisenstein + rc84
 * ModularFormsRing C[E4,E6]).
 *
 * THE QUASIMODULAR RING, ONE GENERATOR UP
 *   M~_*(SL2(Z)) = C[E2, E4, E6]: every level-1 weight-k quasimodular form is a
 *   UNIQUE exact-rational polynomial in E2, E4, E6 — a Q-linear combination of the
 *   weight-k monomials E2^a E4^b E6^c with 2a + 4b + 6c = k, a,b,c >= 0 (Kaneko &
 *   Zagier, The Moduli Space of Curves, Progr. Math. 129 (1995), pp. 165-172;
 *   Zagier, The 1-2-3 of Modular Forms, Springer (2008), section 5.3). The rc84
 *   modular ring C[E4,E6] is exactly the a=0 subring; E2 (weight 2, the
 *   QUASIMODULAR generator) is the new third coordinate, so this ring genuinely
 *   EXTENDS the modular one (e.g. E2^2 @4 -> {(2,0,0):1}, NOT in C[E4,E6]).
 *
 * THE DECISION (decompose-and-compute, NOT a search):
 *   given an exact q-series f (reduced (num,den) coefficients) claimed to be a
 *   weight-k quasimodular form, this op
 *     1. enumerates the weight-k monomial basis (a,b,c): 2a+4b+6c=k (ascending a,b);
 *     2. builds each monomial column E2^a E4^b E6^c as an exact-Q truncated q-series
 *        (the rc83 srmech_eisenstein_qseries: k=2 for E2 — its quasimodular branch —
 *        + k=4/k=6 for E4/E6 + an exact-Q convolution);
 *     3. solves the SQUARE leading-d-rows subsystem A x = b over Q by dispatching
 *        to the PUBLIC srmech_qmat_solve (exact Gauss-Jordan over bignum-Q — reuse,
 *        not reimplement);
 *     4. VERIFIES the candidate reproduces EVERY provided term;
 *   returns the reduced rep coefficients out_num[j]/out_den[j] (one per monomial,
 *   monomial order) with *out_has = 1, or *out_has = 0 (no representation: a
 *   non-quasimodular series).
 *
 * The C is STANDALONE-COMPLETE: every working carrier + the E2/E4/E6 q-series + the
 * monomial columns + the qmat marshalling arrays are carved from the caller arena
 * `ws` (sized via srmech_quasimodular_forms_ring_represent_ws_bound), so the
 * magnitude bound is the CALLER's RAM, not a compiled-in cap. out_num[]/out_den[]
 * are caller-owned.
 *
 * Like srmech_modular_forms_ring, represent is a genuine REDUCER (q-series -> exact
 * closed form, or honest OPEN) — a Rosetta ledger op (c_dispatched). Additive
 * symbol -> ABI unchanged (stays 3).
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto/recursion): OK — iterative, flat helpers
 *   - Rule 2 (bounded loops)    : OK — bounds are d, n_terms, k
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

/* The largest weight-k monomial-basis dimension the fixed bookkeeping supports
 * (d = #{(a,b,c): 2a+4b+6c=k} ~ k^2/48; this cap covers any realistic k up to a
 * few hundred). Past it the op returns SRMECH_ERR_BAD_INPUT and the Python carrier
 * keeps its pure path. */
#define QMFR_MAX_DIM 256u

/* A roster of working exact-Q carriers carved from the caller arena `ws`, plus the
 * divmod/gcd scratch tail. Every carrier is `cap` limbs. */
typedef struct qmfr_ctx {
    srmech_bigint_t t0;    /* exact-Q / integer scratch          */
    srmech_bigint_t t1;    /* exact-Q / integer scratch          */
    srmech_bigint_t t2;    /* product scratch (non-aliasing)     */
    srmech_bigint_t acc_n; /* convolution accumulator numerator  */
    srmech_bigint_t acc_d; /* convolution accumulator denominator*/
    srmech_bigint_t g;     /* gcd sink (reduce-private)           */
    srmech_bigint_t rem;   /* divmod remainder sink (reduce)      */
    srmech_bigint_t rs0;   /* reduce-private quotient scratch     */
    srmech_bigint_t rs1;   /* reduce-private quotient scratch     */
    uint32_t        limb_cap;
    void           *scratch;     /* divmod/gcd arena tail          */
    size_t          scratch_len;
} qmfr_ctx_t;

#define QMFR_N_CARRIERS 9u   /* t0,t1,t2,acc_n,acc_d,g,rem,rs0,rs1 */

/* ---- forward declarations (Rule 1: no recursion) ------------------- */

static uint32_t *qmfr_take(uint32_t *base, size_t words, size_t *cur,
                           size_t count);
static srmech_status_t qmfr_bind(srmech_bigint_t *b, uint32_t *base,
                                 size_t words, size_t *cur, uint32_t cap);
static srmech_status_t qmfr_ctx_init(qmfr_ctx_t *c, uint32_t cap, uint32_t *base,
                                     size_t words, size_t *cur);
static size_t qmfr_hdr_words(void);
static srmech_status_t qmfr_q_reduce(qmfr_ctx_t *c, srmech_bigint_t *num,
                                     srmech_bigint_t *den);
static srmech_status_t qmfr_q_addmul(qmfr_ctx_t *c, srmech_bigint_t *acc_n,
                                     srmech_bigint_t *acc_d,
                                     const srmech_bigint_t *an,
                                     const srmech_bigint_t *ad,
                                     const srmech_bigint_t *bn,
                                     const srmech_bigint_t *bd);
static size_t qmfr_dim(size_t k);
static srmech_status_t qmfr_convolve(qmfr_ctx_t *c, size_t nt,
                                     srmech_bigint_t *res_n,
                                     srmech_bigint_t *res_d,
                                     const srmech_bigint_t *o_n,
                                     const srmech_bigint_t *o_d);

/* ---- caller-arena carve (mirrors mfr_take / mfr_bind) -------------- */

static uint32_t *qmfr_take(uint32_t *base, size_t words, size_t *cur,
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

static srmech_status_t qmfr_bind(srmech_bigint_t *b, uint32_t *base,
                                 size_t words, size_t *cur, uint32_t cap)
{
    uint32_t *limbs = qmfr_take(base, words, cur, cap);
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

static srmech_status_t qmfr_ctx_init(qmfr_ctx_t *c, uint32_t cap, uint32_t *base,
                                     size_t words, size_t *cur)
{
    srmech_status_t st = SRMECH_OK;
    assert(c != NULL && base != NULL && cur != NULL);
    assert(cap > 0u);
    c->limb_cap = cap;
    st |= qmfr_bind(&c->t0, base, words, cur, cap);
    st |= qmfr_bind(&c->t1, base, words, cur, cap);
    st |= qmfr_bind(&c->t2, base, words, cur, cap);
    st |= qmfr_bind(&c->acc_n, base, words, cur, cap);
    st |= qmfr_bind(&c->acc_d, base, words, cur, cap);
    st |= qmfr_bind(&c->g, base, words, cur, cap);
    st |= qmfr_bind(&c->rem, base, words, cur, cap);
    st |= qmfr_bind(&c->rs0, base, words, cur, cap);
    st |= qmfr_bind(&c->rs1, base, words, cur, cap);
    if (st != SRMECH_OK) {
        return SRMECH_ERR_OVERFLOW;
    }
    /* Carve a DEDICATED divmod/gcd scratch block (advancing cur) so it does NOT
     * overlap the e2/e4/e6 series + monomial columns carved later from the same
     * arena. Sized to dominate the gcd/divmod working set (cap-wide operands). */
    {
        size_t sw = (size_t)cap * 16u + 512u;
        uint32_t *sp = qmfr_take(base, words, cur, sw);
        if (sp == NULL) {
            return SRMECH_ERR_OVERFLOW;
        }
        c->scratch = (void *)sp;
        c->scratch_len = sw * sizeof(uint32_t);
    }
    assert(*cur <= words);
    return SRMECH_OK;
}

/* The srmech_bigint header size, in arena words (rounded up). */
static size_t qmfr_hdr_words(void)
{
    size_t hw = (sizeof(srmech_bigint_t) + sizeof(uint32_t) - 1u) / sizeof(uint32_t);
    assert(hw >= 1u);
    assert(sizeof(uint32_t) >= 1u);
    return hw;
}

/* ---- exact-Q reduce (mirrors mfr_q_reduce) ------------------------ *
 * Reduce num/den IN PLACE to lowest terms, positive denominator. den nonzero;
 * 0/d -> 0/1. Uses ONLY the reduce-private carriers (g, rem, rs0, rs1) + scratch. */
static srmech_status_t qmfr_q_reduce(qmfr_ctx_t *c, srmech_bigint_t *num,
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

/* ---- acc += (an/ad) * (bn/bd)  (exact Q, reduced) ---------------- *
 * acc_n/acc_d gets (an/ad)*(bn/bd) added in place. All products go into the
 * non-aliasing t0/t1/t2 scratch (srmech_bigint_mul zeros its `out`, so out must
 * never alias an input). acc_* must NOT alias t0/t1/t2. */
static srmech_status_t qmfr_q_addmul(qmfr_ctx_t *c, srmech_bigint_t *acc_n,
                                     srmech_bigint_t *acc_d,
                                     const srmech_bigint_t *an,
                                     const srmech_bigint_t *ad,
                                     const srmech_bigint_t *bn,
                                     const srmech_bigint_t *bd)
{
    srmech_status_t st;
    assert(c != NULL && acc_n != NULL && acc_d != NULL);
    assert(an != NULL && ad != NULL && bn != NULL && bd != NULL);
    st = srmech_bigint_mul(&c->t0, an, bn);            /* t0 = an*bn (prod num) */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_mul(&c->t1, ad, bd);            /* t1 = ad*bd (prod den) */
    if (st != SRMECH_OK) { return st; }
    /* acc = acc + t0/t1 : num = acc_n*t1 + t0*acc_d, den = acc_d*t1 */
    st = srmech_bigint_mul(&c->t2, acc_n, &c->t1);     /* t2 = acc_n*t1 */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_mul(&c->g, &c->t0, acc_d);      /* g = t0*acc_d (reuse g) */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_mul(&c->rem, acc_d, &c->t1);    /* rem = acc_d*t1 (new den) */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_add(acc_n, &c->t2, &c->g);      /* acc_n = new num */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(acc_d, &c->rem);           /* acc_d = new den */
    if (st != SRMECH_OK) { return st; }
    return qmfr_q_reduce(c, acc_n, acc_d);
}

/* dim M~_k = #{(a,b,c): 2a+4b+6c=k, a,b,c>=0} for even k>=0; 0 for odd k. Computed
 * by enumeration (no two-term closed form like the modular C[E4,E6] case — the
 * third generator E2 makes it a three-variable partition count). */
static size_t qmfr_dim(size_t k)
{
    size_t a, b, d = 0u;
    assert(sizeof(k) >= 1u);
    if ((k % 2u) != 0u) {
        return 0u;
    }
    for (a = 0u; 2u * a <= k; ++a) {
        for (b = 0u; 2u * a + 4u * b <= k; ++b) {
            size_t rem = k - 2u * a - 4u * b;
            if ((rem % 6u) == 0u) {
                d++;
            }
        }
    }
    assert(d <= k * k + 1u);
    return d;
}

/* res (an exact-Q q-series, nt terms) *= o (another exact-Q q-series, nt terms),
 * TRUNCATED to nt terms, in place. res must NOT alias o. Backward convolution
 * over the acc_n/acc_d accumulator (so res[i] is consumed before it is rewritten).
 * res_n[i]/res_d[i] and o_n[i]/o_d[i] are reduced rationals. */
static srmech_status_t qmfr_convolve(qmfr_ctx_t *c, size_t nt,
                                     srmech_bigint_t *res_n,
                                     srmech_bigint_t *res_d,
                                     const srmech_bigint_t *o_n,
                                     const srmech_bigint_t *o_d)
{
    size_t i, j;
    srmech_status_t st;
    assert(c != NULL && res_n != NULL && res_d != NULL);
    assert(o_n != NULL && o_d != NULL && nt >= 1u);
    for (i = nt; i-- > 0u; ) {                /* high-to-low: res[i] uses res[<=i] */
        st = srmech_bigint_set_i64(&c->acc_n, 0);
        if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&c->acc_d, 1); }
        if (st != SRMECH_OK) { return st; }
        for (j = 0u; j <= i; ++j) {
            /* acc += res[i-j] * o[j] */
            st = qmfr_q_addmul(c, &c->acc_n, &c->acc_d,
                               &res_n[i - j], &res_d[i - j], &o_n[j], &o_d[j]);
            if (st != SRMECH_OK) { return st; }
        }
        st = srmech_bigint_copy(&res_n[i], &c->acc_n);
        if (st == SRMECH_OK) { st = srmech_bigint_copy(&res_d[i], &c->acc_d); }
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* ================================================================== *
 *  Public: ws_bound + entry_cap + represent                           *
 * ================================================================== */

/* Minimum `ws_len` BYTES for srmech_quasimodular_forms_ring_represent: the working
 * carriers + the E2/E4/E6 q-series rosters + the d monomial columns + the qmat
 * marshalling arrays + the qmat working arena, each `coeff_limbs` wide, over
 * n_terms terms and a weight-k basis of up to qmfr_dim(k) monomials. */
size_t srmech_quasimodular_forms_ring_represent_ws_bound(size_t coeff_limbs,
                                                         size_t n_terms, size_t k)
{
    size_t cl = (coeff_limbs > 0u) ? coeff_limbs : 1u;
    size_t nt = (n_terms > 0u) ? n_terms : 1u;
    size_t d = qmfr_dim(k);
    size_t hw = qmfr_hdr_words();
    /* the actual carrier width: represent binds the ctx carriers + E2/E4/E6 series +
     * monomial columns at cap = out_num[0].cap = entry_cap (NOT cl), so size every
     * term at entry_cap to match what the op carves. */
    size_t ec = srmech_quasimodular_forms_ring_entry_cap(cl, nt, k);
    size_t dd = (d == 0u ? 1u : d);
    size_t carriers = ec * (size_t)QMFR_N_CARRIERS;
    /* E2 + E4 + E6 q-series rosters (2*nt bigints each: headers + limbs) */
    size_t eis = 3u * (2u * nt) * (ec + hw);
    /* d monomial columns (one d*nt block: headers + limbs) */
    size_t cols = (dd * nt) * 2u * (ec + hw);
    /* a small headroom roster */
    size_t work = 4u * nt * (ec + hw);
    /* the qmat solve arena + marshalling: qmfr_solve_with_stride carves A (d*d),
     * b (d), x (d) at qcap = ec + d + 4 limbs + the qmat working arena. */
    size_t qcl = ec + d + 4u;
    size_t qbound = srmech_qmat_ws_bound(qcl, dd, dd + 1u);
    size_t qcells = dd * dd + 2u * dd;                  /* A + b + x */
    size_t qmarsh = qcells * (qcl + hw);
    /* the DEDICATED divmod/gcd scratch carved in qmfr_ctx_init (ec*16 + 512) +
     * the eisenstein peer's own working arena (carved separately for E2/E4/E6). */
    size_t scratch = ec * 16u + 512u;
    size_t eis_ws = srmech_eisenstein_ws_bound(ec, 6u) / sizeof(uint32_t);
    size_t words = carriers + eis + cols + work + qmarsh + scratch + eis_ws
                 + (qbound / sizeof(uint32_t)) + 256u;
    assert(cl >= 1u);
    assert(words >= carriers);
    return words * sizeof(uint32_t);
}

/* The per-entry limb cap the caller must give each srmech_bigint in the OUTPUT
 * rep arrays + the working columns (so a reduced result entry never overflows its
 * slot before the op's guard fires). */
size_t srmech_quasimodular_forms_ring_entry_cap(size_t coeff_limbs, size_t n_terms,
                                                size_t k)
{
    size_t cl = (coeff_limbs > 0u) ? coeff_limbs : 1u;
    size_t d = qmfr_dim(k);
    size_t nt = (n_terms > 0u) ? n_terms : 1u;
    /* a monomial coeff is a sum of nt products of d-deep rationals; the Cramer
     * solve denominators add log-headroom. Over-bound. */
    size_t cap = cl * (d + 2u) + (nt / 4u) + 16u;
    assert(cl >= 1u);
    assert(cap >= cl);
    return cap;
}

/* ---- monomial-basis + column build (more forward decls) ----------- */

static srmech_status_t qmfr_enum_monomials(size_t k, size_t d, uint16_t *aexp,
                                           uint16_t *bexp, uint16_t *cexp);
static srmech_status_t qmfr_carve_series(uint32_t *base, size_t words,
                                         size_t *cur, uint32_t cap, size_t nt,
                                         srmech_bigint_t **sn,
                                         srmech_bigint_t **sd);
static srmech_status_t qmfr_carve_block(uint32_t *base, size_t words,
                                        size_t *cur, uint32_t cap, size_t count,
                                        srmech_bigint_t **bn,
                                        srmech_bigint_t **bd);
static srmech_status_t qmfr_set_one(size_t nt,
                                    srmech_bigint_t *rn, srmech_bigint_t *rd);
static srmech_status_t qmfr_verify(qmfr_ctx_t *c, size_t nt, size_t d,
                                   srmech_bigint_t *cols_n,
                                   srmech_bigint_t *cols_d,
                                   const srmech_bigint_t *x_n,
                                   const srmech_bigint_t *x_d,
                                   const srmech_bigint_t *f_n,
                                   const srmech_bigint_t *f_d, int *out_ok);
static srmech_status_t qmfr_solve_with_stride(
    uint32_t *base, size_t words, size_t *cur, uint32_t cap, size_t d,
    size_t stride, srmech_bigint_t *cols_n, srmech_bigint_t *cols_d,
    const srmech_bigint_t *f_n, const srmech_bigint_t *f_d,
    srmech_bigint_t *out_num, srmech_bigint_t *out_den, int *out_sing);
static srmech_status_t qmfr_build_columns(qmfr_ctx_t *c, size_t d, size_t nt,
                                          const uint16_t *aexp,
                                          const uint16_t *bexp,
                                          const uint16_t *cexp,
                                          srmech_bigint_t *col_n,
                                          srmech_bigint_t *col_d,
                                          const srmech_bigint_t *e2n,
                                          const srmech_bigint_t *e2d,
                                          const srmech_bigint_t *e4n,
                                          const srmech_bigint_t *e4d,
                                          const srmech_bigint_t *e6n,
                                          const srmech_bigint_t *e6d);
static srmech_status_t qmfr_fill_e246(uint32_t *base, size_t words, size_t *cur,
                                      size_t cap, size_t nt,
                                      srmech_bigint_t *e2n, srmech_bigint_t *e2d,
                                      srmech_bigint_t *e4n, srmech_bigint_t *e4d,
                                      srmech_bigint_t *e6n, srmech_bigint_t *e6d);
static srmech_status_t qmfr_prepare_e246(
    uint32_t *base, size_t words, size_t *cur, uint32_t cap, size_t nt,
    srmech_bigint_t **e2n, srmech_bigint_t **e2d,
    srmech_bigint_t **e4n, srmech_bigint_t **e4d,
    srmech_bigint_t **e6n, srmech_bigint_t **e6d);

/* Enumerate the weight-k monomial basis (a,b,c): 2a+4b+6c=k, a,b,c>=0, ascending
 * a then b; writes the d exponent triples into aexp[]/bexp[]/cexp[]. d == qmfr_dim. */
static srmech_status_t qmfr_enum_monomials(size_t k, size_t d, uint16_t *aexp,
                                           uint16_t *bexp, uint16_t *cexp)
{
    size_t a, b, idx = 0u;
    assert(aexp != NULL && bexp != NULL && cexp != NULL);
    assert(d <= QMFR_MAX_DIM);
    for (a = 0u; 2u * a <= k; ++a) {
        for (b = 0u; 2u * a + 4u * b <= k; ++b) {
            size_t rem = k - 2u * a - 4u * b;
            if ((rem % 6u) == 0u) {
                if (idx >= d) { return SRMECH_ERR_OVERFLOW; }
                aexp[idx] = (uint16_t)a;
                bexp[idx] = (uint16_t)b;
                cexp[idx] = (uint16_t)(rem / 6u);
                idx++;
            }
        }
    }
    if (idx != d) { return SRMECH_ERR_OVERFLOW; }   /* dim mismatch -> bail */
    return SRMECH_OK;
}

/* Carve a fresh nt-term exact-Q q-series roster (num + den) from the arena: the
 * 2 header runs (cast from arena words) + 2*nt limb runs. */
static srmech_status_t qmfr_carve_series(uint32_t *base, size_t words,
                                         size_t *cur, uint32_t cap, size_t nt,
                                         srmech_bigint_t **sn,
                                         srmech_bigint_t **sd)
{
    size_t hw = qmfr_hdr_words(), i;
    uint32_t *hn, *hd;
    srmech_status_t st;
    assert(base != NULL && cur != NULL && sn != NULL && sd != NULL);
    assert(nt >= 1u && cap > 0u);
    hn = qmfr_take(base, words, cur, hw * nt);
    if (hn == NULL) { return SRMECH_ERR_OVERFLOW; }
    hd = qmfr_take(base, words, cur, hw * nt);
    if (hd == NULL) { return SRMECH_ERR_OVERFLOW; }
    *sn = (srmech_bigint_t *)(void *)hn;
    *sd = (srmech_bigint_t *)(void *)hd;
    for (i = 0u; i < nt; ++i) {
        st = qmfr_bind(&(*sn)[i], base, words, cur, cap);
        if (st == SRMECH_OK) { st = qmfr_bind(&(*sd)[i], base, words, cur, cap); }
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* Carve ONE contiguous block of `count` exact-Q carriers (num + den), each `cap`
 * limbs: the num header run (count headers) then the den header run, then 2*count
 * limb runs. So a d x nt column block is *bn + j*nt for column j. */
static srmech_status_t qmfr_carve_block(uint32_t *base, size_t words,
                                        size_t *cur, uint32_t cap, size_t count,
                                        srmech_bigint_t **bn,
                                        srmech_bigint_t **bd)
{
    size_t hw = qmfr_hdr_words(), i;
    uint32_t *hn, *hd;
    srmech_status_t st;
    assert(base != NULL && cur != NULL && bn != NULL && bd != NULL);
    assert(count >= 1u && cap > 0u);
    hn = qmfr_take(base, words, cur, hw * count);
    if (hn == NULL) { return SRMECH_ERR_OVERFLOW; }
    hd = qmfr_take(base, words, cur, hw * count);
    if (hd == NULL) { return SRMECH_ERR_OVERFLOW; }
    *bn = (srmech_bigint_t *)(void *)hn;
    *bd = (srmech_bigint_t *)(void *)hd;
    for (i = 0u; i < count; ++i) {
        st = qmfr_bind(&(*bn)[i], base, words, cur, cap);
        if (st == SRMECH_OK) { st = qmfr_bind(&(*bd)[i], base, words, cur, cap); }
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* rn/rd <- the constant q-series 1 (1/1 then 0/1 ... 0/1) over nt terms. */
static srmech_status_t qmfr_set_one(size_t nt,
                                    srmech_bigint_t *rn, srmech_bigint_t *rd)
{
    size_t i;
    srmech_status_t st;
    assert(rn != NULL && rd != NULL);
    assert(nt >= 1u);
    st = srmech_bigint_set_i64(&rn[0], 1);
    if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&rd[0], 1); }
    if (st != SRMECH_OK) { return st; }
    for (i = 1u; i < nt; ++i) {
        st = srmech_bigint_set_i64(&rn[i], 0);
        if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&rd[i], 1); }
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* VERIFY: for every term n, sum_j x[j]*cols[j][n] == f[n]. *out_ok set 0 on the
 * first mismatch. cols_n/cols_d is the d-column block (column j at offset j*nt). */
static srmech_status_t qmfr_verify(qmfr_ctx_t *c, size_t nt, size_t d,
                                   srmech_bigint_t *cols_n,
                                   srmech_bigint_t *cols_d,
                                   const srmech_bigint_t *x_n,
                                   const srmech_bigint_t *x_d,
                                   const srmech_bigint_t *f_n,
                                   const srmech_bigint_t *f_d, int *out_ok)
{
    size_t n, j;
    srmech_status_t st;
    assert(c != NULL && cols_n != NULL && x_n != NULL && f_n != NULL);
    assert(out_ok != NULL && d >= 1u);
    *out_ok = 1;
    for (n = 0u; n < nt; ++n) {
        st = srmech_bigint_set_i64(&c->acc_n, 0);
        if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&c->acc_d, 1); }
        if (st != SRMECH_OK) { return st; }
        for (j = 0u; j < d; ++j) {
            st = qmfr_q_addmul(c, &c->acc_n, &c->acc_d, &x_n[j], &x_d[j],
                               &cols_n[j * nt + n], &cols_d[j * nt + n]);
            if (st != SRMECH_OK) { return st; }
        }
        /* compare acc (reduced) to f[n] (reduced): equal iff num & den match */
        if (srmech_bigint_cmp(&c->acc_n, &f_n[n]) != 0
                || srmech_bigint_cmp(&c->acc_d, &f_d[n]) != 0) {
            *out_ok = 0;
            return SRMECH_OK;
        }
    }
    return SRMECH_OK;
}

/* Build the leading d x d matrix A (A[r][j] = cols[j][r], reading column j at the
 * stride offset j*stride) + the RHS b[r] = f[r], carve the qmat marshalling +
 * working arena, and dispatch the exact-Q solve to the PUBLIC srmech_qmat_solve.
 * The solution x (d entries, reduced) lands in out_num[]/out_den[]. *out_sing set 1
 * when the leading block is singular (the caller then returns has=0; the pure path
 * has the over-determined RREF fallback). */
static srmech_status_t qmfr_solve_with_stride(
    uint32_t *base, size_t words, size_t *cur, uint32_t cap, size_t d,
    size_t stride, srmech_bigint_t *cols_n, srmech_bigint_t *cols_d,
    const srmech_bigint_t *f_n, const srmech_bigint_t *f_d,
    srmech_bigint_t *out_num, srmech_bigint_t *out_den, int *out_sing)
{
    size_t cells = d * d, i, r, j;
    uint32_t qcap = (uint32_t)((size_t)cap + d + 4u);
    srmech_bigint_t *a_n, *a_d, *b_n, *b_d, *x_n, *x_d;
    void *qws;
    size_t qws_words = srmech_qmat_ws_bound((size_t)qcap, d, d + 1u)
                     / sizeof(uint32_t);
    int sing = 0;
    srmech_status_t st;
    assert(base != NULL && cur != NULL && cols_n != NULL && out_num != NULL);
    assert(out_sing != NULL && d >= 1u && stride >= d);
    *out_sing = 0;
    st = qmfr_carve_block(base, words, cur, qcap, cells, &a_n, &a_d);
    if (st != SRMECH_OK) { return st; }
    st = qmfr_carve_block(base, words, cur, qcap, d, &b_n, &b_d);
    if (st != SRMECH_OK) { return st; }
    st = qmfr_carve_block(base, words, cur, qcap, d, &x_n, &x_d);
    if (st != SRMECH_OK) { return st; }
    for (r = 0u; r < d; ++r) {
        for (j = 0u; j < d; ++j) {
            st = srmech_bigint_copy(&a_n[r * d + j], &cols_n[j * stride + r]);
            if (st == SRMECH_OK) {
                st = srmech_bigint_copy(&a_d[r * d + j], &cols_d[j * stride + r]);
            }
            if (st != SRMECH_OK) { return st; }
        }
        st = srmech_bigint_copy(&b_n[r], &f_n[r]);
        if (st == SRMECH_OK) { st = srmech_bigint_copy(&b_d[r], &f_d[r]); }
        if (st != SRMECH_OK) { return st; }
    }
    qws = (void *)qmfr_take(base, words, cur, qws_words);
    if (qws == NULL) { return SRMECH_ERR_OVERFLOW; }
    st = srmech_qmat_solve(a_n, a_d, d, b_n, b_d, 1u, x_n, x_d, &sing,
                           qws, qws_words * sizeof(uint32_t));
    if (st != SRMECH_OK) { return st; }
    if (sing) { *out_sing = 1; return SRMECH_OK; }
    for (i = 0u; i < d; ++i) {
        st = srmech_bigint_copy(&out_num[i], &x_n[i]);
        if (st == SRMECH_OK) { st = srmech_bigint_copy(&out_den[i], &x_d[i]); }
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* Fill the d monomial columns (one contiguous d*nt block, column j at j*nt): each
 * column = E2^aexp[j] * E4^bexp[j] * E6^cexp[j] truncated to nt terms (start from 1,
 * convolve by E2 a times, E4 b times, E6 c times). */
static srmech_status_t qmfr_build_columns(qmfr_ctx_t *c, size_t d, size_t nt,
                                          const uint16_t *aexp,
                                          const uint16_t *bexp,
                                          const uint16_t *cexp,
                                          srmech_bigint_t *col_n,
                                          srmech_bigint_t *col_d,
                                          const srmech_bigint_t *e2n,
                                          const srmech_bigint_t *e2d,
                                          const srmech_bigint_t *e4n,
                                          const srmech_bigint_t *e4d,
                                          const srmech_bigint_t *e6n,
                                          const srmech_bigint_t *e6d)
{
    size_t j, pw;
    srmech_status_t st;
    assert(c != NULL && aexp != NULL && bexp != NULL && cexp != NULL);
    assert(col_n != NULL && e2n != NULL && e4n != NULL && e6n != NULL && d >= 1u);
    for (j = 0u; j < d; ++j) {
        srmech_bigint_t *cn = col_n + j * nt;
        srmech_bigint_t *cd = col_d + j * nt;
        size_t a = aexp[j], b = bexp[j], cc = cexp[j];
        st = qmfr_set_one(nt, cn, cd);
        if (st != SRMECH_OK) { return st; }
        for (pw = 0u; pw < a; ++pw) {
            st = qmfr_convolve(c, nt, cn, cd, e2n, e2d);
            if (st != SRMECH_OK) { return st; }
        }
        for (pw = 0u; pw < b; ++pw) {
            st = qmfr_convolve(c, nt, cn, cd, e4n, e4d);
            if (st != SRMECH_OK) { return st; }
        }
        for (pw = 0u; pw < cc; ++pw) {
            st = qmfr_convolve(c, nt, cn, cd, e6n, e6d);
            if (st != SRMECH_OK) { return st; }
        }
    }
    return SRMECH_OK;
}

/* Compute the E2/E4/E6 q-series (the rc83 eisenstein peer; E2 via its k=2
 * quasimodular branch) into the carved rosters, carving the eisenstein working
 * arena from the tail. */
static srmech_status_t qmfr_fill_e246(uint32_t *base, size_t words, size_t *cur,
                                      size_t cap, size_t nt,
                                      srmech_bigint_t *e2n, srmech_bigint_t *e2d,
                                      srmech_bigint_t *e4n, srmech_bigint_t *e4d,
                                      srmech_bigint_t *e6n, srmech_bigint_t *e6d)
{
    size_t eis_ws_words, e2len = 0u, e4len = 0u, e6len = 0u;
    void *eis_ws;
    srmech_status_t st;
    assert(base != NULL && cur != NULL && e2n != NULL && e4n != NULL);
    assert(e6n != NULL && cap >= 1u && nt >= 1u);
    eis_ws_words = srmech_eisenstein_ws_bound(cap, 6u) / sizeof(uint32_t);
    eis_ws = (void *)qmfr_take(base, words, cur, eis_ws_words);
    if (eis_ws == NULL) { return SRMECH_ERR_OVERFLOW; }
    st = srmech_eisenstein_qseries(2u, nt, e2n, e2d, &e2len,
                                   eis_ws, eis_ws_words * sizeof(uint32_t));
    if (st != SRMECH_OK) { return st; }
    st = srmech_eisenstein_qseries(4u, nt, e4n, e4d, &e4len,
                                   eis_ws, eis_ws_words * sizeof(uint32_t));
    if (st != SRMECH_OK) { return st; }
    st = srmech_eisenstein_qseries(6u, nt, e6n, e6d, &e6len,
                                   eis_ws, eis_ws_words * sizeof(uint32_t));
    return st;
}

/* Carve the three E2/E4/E6 q-series rosters from the arena AND fill them (the rc83
 * eisenstein peer; E2 via its k=2 quasimodular branch) — the represent entry point's
 * series-prep step, factored out to keep that function under the JPL 60-line bound. */
static srmech_status_t qmfr_prepare_e246(
    uint32_t *base, size_t words, size_t *cur, uint32_t cap, size_t nt,
    srmech_bigint_t **e2n, srmech_bigint_t **e2d,
    srmech_bigint_t **e4n, srmech_bigint_t **e4d,
    srmech_bigint_t **e6n, srmech_bigint_t **e6d)
{
    srmech_status_t st;
    assert(base != NULL && cur != NULL && e2n != NULL && e2d != NULL);
    assert(e4n != NULL && e4d != NULL && e6n != NULL && e6d != NULL && nt >= 1u);
    st = qmfr_carve_series(base, words, cur, cap, nt, e2n, e2d);
    if (st == SRMECH_OK) {
        st = qmfr_carve_series(base, words, cur, cap, nt, e4n, e4d);
    }
    if (st == SRMECH_OK) {
        st = qmfr_carve_series(base, words, cur, cap, nt, e6n, e6d);
    }
    if (st != SRMECH_OK) { return st; }
    return qmfr_fill_e246(base, words, cur, (size_t)cap, nt,
                          *e2n, *e2d, *e4n, *e4d, *e6n, *e6d);
}

/* The level-1 quasimodular-forms-ring membership decision. Inputs: the weight k
 * (even >= 0), the claimed q-series f (f_n[i]/f_d[i] reduced, i = 0..n_terms-1). On
 * a representable form: *out_has = 1 and out_num[j]/out_den[j] (j = 0..dim(k)-1) are
 * the reduced rep coefficients of E2^a E4^b E6^c (monomial order, ascending a then
 * b). On a non-form: *out_has = 0 (out_* unspecified). The out_num[]/out_den[]
 * arrays are caller-owned (>= qmfr_dim(k) srmech_bigint, each pre-bound to >=
 * entry_cap limbs). SRMECH_ERR_BAD_INPUT on n_terms too small / a NULL pointer /
 * d > QMFR_MAX_DIM; SRMECH_ERR_OVERFLOW on an arena shortfall. */
srmech_status_t srmech_quasimodular_forms_ring_represent(
    size_t k, const srmech_bigint_t *f_n, const srmech_bigint_t *f_d,
    size_t n_terms, srmech_bigint_t *out_num, srmech_bigint_t *out_den,
    size_t *out_has, void *ws, size_t ws_len)
{
    qmfr_ctx_t c;
    uint16_t aexp[QMFR_MAX_DIM], bexp[QMFR_MAX_DIM], cexp[QMFR_MAX_DIM];
    srmech_bigint_t *e2n = NULL, *e2d = NULL, *e4n = NULL, *e4d = NULL;  /* NULL-init: MSVC /WX C4701/C4703 */
    srmech_bigint_t *e6n = NULL, *e6d = NULL, *col_n = NULL, *col_d = NULL;
    uint32_t *base, cap;
    size_t words, cur = 0u, d, j;
    int sing = 0, ok = 0;
    srmech_status_t st;
    assert(f_n != NULL && f_d != NULL && out_has != NULL);
    assert(out_num != NULL && out_den != NULL);
    if (f_n == NULL || f_d == NULL || out_num == NULL || out_den == NULL
            || out_has == NULL || ws == NULL) {
        return SRMECH_ERR_BAD_INPUT;
    }
    *out_has = 0u;
    d = qmfr_dim(k);
    if (d > QMFR_MAX_DIM) { return SRMECH_ERR_BAD_INPUT; }
    if (d == 0u) {                              /* M~_k = {0} (odd k) */
        for (j = 0u; j < n_terms; ++j) {
            if (!srmech_bigint_is_zero(&f_n[j])) { return SRMECH_OK; }
        }
        *out_has = 1u;                          /* the zero series IS the rep */
        return SRMECH_OK;
    }
    if (n_terms < d + 2u) { return SRMECH_ERR_BAD_INPUT; }
    base = (uint32_t *)ws;
    words = ws_len / sizeof(uint32_t);
    cap = out_num[0].cap;
    if (cap < 1u) { return SRMECH_ERR_OVERFLOW; }
    st = qmfr_ctx_init(&c, cap, base, words, &cur);
    if (st != SRMECH_OK) { return st; }
    st = qmfr_enum_monomials(k, d, aexp, bexp, cexp);
    if (st != SRMECH_OK) { return st; }
    st = qmfr_prepare_e246(base, words, &cur, cap, n_terms,
                           &e2n, &e2d, &e4n, &e4d, &e6n, &e6d);
    if (st != SRMECH_OK) { return st; }
    st = qmfr_carve_block(base, words, &cur, cap, d * n_terms, &col_n, &col_d);
    if (st != SRMECH_OK) { return st; }
    st = qmfr_build_columns(&c, d, n_terms, aexp, bexp, cexp, col_n, col_d,
                            e2n, e2d, e4n, e4d, e6n, e6d);
    if (st != SRMECH_OK) { return st; }
    st = qmfr_solve_with_stride(base, words, &cur, cap, d, n_terms,
                                col_n, col_d, f_n, f_d, out_num, out_den, &sing);
    if (st != SRMECH_OK) { return st; }
    if (sing) { return SRMECH_OK; }             /* singular block -> has=0 */
    st = qmfr_verify(&c, n_terms, d, col_n, col_d, out_num, out_den,
                     f_n, f_d, &ok);
    if (st != SRMECH_OK) { return st; }
    if (ok) { *out_has = 1u; }
    return SRMECH_OK;
}
