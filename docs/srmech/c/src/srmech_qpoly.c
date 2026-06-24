/*
 * srmech_qpoly.c — EXACT q-shift CARRIER over srmech_bigint (the C peer of
 * srmech.amsc.qpoly.QPoly; the q-hypergeometric F929 reduction-row foundation,
 * the q-analog of the srmech_poly.c univariate polynomial carrier).
 *
 * A QPoly is a LAURENT polynomial in the formal variable x = q^n whose
 * coefficients are exact polynomials in q (the ground ring Q[q]). It is carried
 * as a ROW of q-polynomial CELLS over an x-exponent window [x_low, x_low+cells):
 * cell i is the Q[q] coefficient of x^(x_low + i), itself a run of exact-rational
 * coefficients in ASCENDING q-degree. The cell q-runs are stored CONCATENATED in
 * a single pair of caller-owned srmech_bigint arrays (nums[] / dens[], ascending
 * q within each cell, cells in ascending-x order), with a parallel `qlen[]` array
 * (length `cells`) giving each cell's q-run length. A cell coefficient
 * nums[..]/dens[..] is the exact rational of q^dq (dens > 0, gcd(|nums|, dens) ==
 * 1; zero coefficient = 0/1). The x_low offset is the caller's bookkeeping (the
 * Python QPoly carries it); these ops align by INDEX and let the caller carry the
 * final x_low. (Mirrors srmech_tripoly.c's concatenated-cell + nlen[] layout, one
 * dimension lighter — a single x-row, not a (j,k) grid.)
 *
 * Each op computes the SAME exact rational coefficients the Python QPoly computes
 * — Class-N rational arithmetic over Class-J reduction — over caller-arena
 * srmech_bigint (NO malloc, JPL Rule 3), each output coefficient reduced to lowest
 * terms with positive denominator. Byte-identical to Python's (num, den) at ANY
 * magnitude (full bignum; no int64/Q61 ceiling).
 *
 *   add/sub : cellwise (x-index-aligned) coefficientwise exact-Q add/sub of the
 *             two cells' q-runs, then trim. The caller pre-aligns both inputs to
 *             the SAME x-window (cells count), padding missing cells to empty
 *             q-runs (mirroring how the Python QPoly._addsub spans the union).
 *   mul     : 1-D x-convolution; each output x-cell accumulates the exact-Q q-run
 *             convolution (a Q[q] polynomial multiply) of the input cells. The
 *             output x-window is [x_low_a + x_low_b, …] (caller bookkeeping).
 *   qshift  : the q-shift sigma^s : x -> q^s * x. Cell i (x-exponent x_low+i,
 *             coefficient c_i(q)) becomes c_i(q) * q^(s*(x_low+i)) — i.e. each
 *             cell's q-run is SHIFTED UP by s*(x_low+i) q-degrees (prepend that
 *             many zero q-coefficients). The x-window is UNCHANGED. The caller
 *             guarantees every s*(x_low+i) >= 0 (the Q[q] ground ring; q-Gosper
 *             feeds only non-negative shifts) — a negative shift would leave Q[q]
 *             and returns SRMECH_ERR_BAD_INPUT.
 *
 * The C is STANDALONE-COMPLETE: every working carrier is carved from the caller
 * arena `ws` (sized via the matching srmech_qpoly_ws_bound), so the magnitude
 * bound is the CALLER's RAM, not a compiled-in cap. A too-small arena or an out
 * coefficient capacity returns SRMECH_ERR_OVERFLOW (never a silent wrap), and the
 * Python QPoly falls back to its ceiling-free pure-Python path.
 *
 * Carrier-internal, like srmech_poly.c / srmech_tripoly.c / srmech_bigexp.c: NOT
 * a Rosetta ledger op (no ToolEntry, no count-test). Additive symbols -> ABI
 * unchanged (stays 3).
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto/recursion): OK — iterative, flat helpers
 *   - Rule 2 (bounded loops)    : OK — bounds are the cell + coefficient counts
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

/* A roster of working bigints carved from the caller arena `ws`. qa/qb hold
 * running exact-Q values; t0 is integer scratch for the Q ops; g/rem/rs0/rs1 are
 * the reducer's private gcd + divmod sinks; z0/z1 are read-only 0 / 1. Every
 * carrier is `cap` limbs. (Mirrors srmech_tripoly.c's tri_ctx_t.) */
typedef struct qp_ctx {
    srmech_bigint_t qa_n;   /* accumulator rational numerator   */
    srmech_bigint_t qa_d;   /* accumulator rational denominator */
    srmech_bigint_t qb_n;   /* second operand numerator         */
    srmech_bigint_t qb_d;   /* second operand denominator       */
    srmech_bigint_t t0;     /* integer scratch                  */
    srmech_bigint_t g;      /* gcd sink (reduce-private)        */
    srmech_bigint_t rem;    /* divmod remainder sink (reduce)   */
    srmech_bigint_t rs0;    /* reduce-private quotient scratch  */
    srmech_bigint_t rs1;    /* reduce-private quotient scratch  */
    srmech_bigint_t z0;     /* read-only 0 (missing-term num)   */
    srmech_bigint_t z1;     /* read-only 1 (missing-term den)   */
    uint32_t limb_cap;      /* per-carrier limb capacity        */
    void  *scratch;         /* divmod/gcd scratch arena tail    */
    size_t scratch_len;     /* its length in BYTES              */
} qp_ctx_t;

#define QP_N_CARRIERS 11u  /* qa_n,qa_d,qb_n,qb_d,t0,g,rem,rs0,rs1,z0,z1 */

/* ---- forward declarations (Rule 1: no recursion) ------------------- */

static uint32_t *qp_take(uint32_t *base, size_t words, size_t *cur, size_t count);
static srmech_status_t qp_bind(srmech_bigint_t *b, uint32_t *base,
                               size_t words, size_t *cur, uint32_t cap);
static srmech_status_t qp_ctx_init(qp_ctx_t *c, uint32_t cap,
                                   void *ws, size_t ws_len);
static srmech_status_t qp_q_reduce(qp_ctx_t *c, srmech_bigint_t *num,
                                   srmech_bigint_t *den);
static srmech_status_t qp_q_add(qp_ctx_t *c, srmech_bigint_t *out_num,
                                srmech_bigint_t *out_den,
                                const srmech_bigint_t *an,
                                const srmech_bigint_t *ad,
                                const srmech_bigint_t *bn,
                                const srmech_bigint_t *bd, int sub);
static srmech_status_t qp_q_mul(qp_ctx_t *c, srmech_bigint_t *out_num,
                                srmech_bigint_t *out_den,
                                const srmech_bigint_t *an,
                                const srmech_bigint_t *ad,
                                const srmech_bigint_t *bn,
                                const srmech_bigint_t *bd);
static size_t qp_trim_len(const srmech_bigint_t *nums, size_t n);
static size_t qp_cap_for(size_t coeff_limbs, size_t accum_terms);
static size_t qp_row_max_limbs(const srmech_bigint_t *nums,
                               const srmech_bigint_t *dens, size_t total);
static size_t qp_q_total(const size_t *qlen, size_t cells);
static srmech_status_t qp_addsub_cell(qp_ctx_t *c, const srmech_bigint_t *a_n,
                                      const srmech_bigint_t *a_d, size_t na,
                                      const srmech_bigint_t *b_n,
                                      const srmech_bigint_t *b_d, size_t nb,
                                      int sub, srmech_bigint_t *o_n,
                                      srmech_bigint_t *o_d, size_t *o_len);
static srmech_status_t qp_mac_cell(qp_ctx_t *c, const srmech_bigint_t *a_n,
                                   const srmech_bigint_t *a_d, size_t na,
                                   const srmech_bigint_t *b_n,
                                   const srmech_bigint_t *b_d, size_t nb,
                                   srmech_bigint_t *o_n, srmech_bigint_t *o_d,
                                   size_t *o_len);
static srmech_status_t qp_shift_cell(const srmech_bigint_t *a_n,
                                     const srmech_bigint_t *a_d, size_t na,
                                     size_t shift, srmech_bigint_t *o_n,
                                     srmech_bigint_t *o_d, size_t *o_len);

/* ---- caller-arena carve (mirrors tri_take / tri_bind) -------------- */

static uint32_t *qp_take(uint32_t *base, size_t words, size_t *cur, size_t count)
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

static srmech_status_t qp_bind(srmech_bigint_t *b, uint32_t *base,
                               size_t words, size_t *cur, uint32_t cap)
{
    uint32_t *limbs = qp_take(base, words, cur, cap);
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

static srmech_status_t qp_ctx_init(qp_ctx_t *c, uint32_t cap,
                                   void *ws, size_t ws_len)
{
    uint32_t *base = (uint32_t *)ws;
    size_t words = ws_len / sizeof(uint32_t), cur = 0u;
    srmech_status_t st = SRMECH_OK;
    assert(c != NULL);
    assert((uintptr_t)ws % sizeof(uint32_t) == 0u || ws == NULL);
    c->limb_cap = cap;
    st |= qp_bind(&c->qa_n, base, words, &cur, cap);
    st |= qp_bind(&c->qa_d, base, words, &cur, cap);
    st |= qp_bind(&c->qb_n, base, words, &cur, cap);
    st |= qp_bind(&c->qb_d, base, words, &cur, cap);
    st |= qp_bind(&c->t0, base, words, &cur, cap);
    st |= qp_bind(&c->g, base, words, &cur, cap);
    st |= qp_bind(&c->rem, base, words, &cur, cap);
    st |= qp_bind(&c->rs0, base, words, &cur, cap);
    st |= qp_bind(&c->rs1, base, words, &cur, cap);
    st |= qp_bind(&c->z0, base, words, &cur, cap);
    st |= qp_bind(&c->z1, base, words, &cur, cap);
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
 * nonzero; 0/d normalizes to 0/1. Uses ONLY the reduce-private carriers (g, rem,
 * rs0, rs1) + the scratch tail. (Mirrors tri_q_reduce.) */
static srmech_status_t qp_q_reduce(qp_ctx_t *c, srmech_bigint_t *num,
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

/* out = a +/- b (exact Q), reduced. sub != 0 selects subtraction. out_* may NOT
 * alias the four input carriers. Uses t0 (cross product). (Mirrors tri_q_add.) */
static srmech_status_t qp_q_add(qp_ctx_t *c, srmech_bigint_t *out_num,
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
    return qp_q_reduce(c, out_num, out_den);
}

/* out = a * b (exact Q), reduced. out_* may NOT alias the inputs. (Mirrors
 * tri_q_mul.) */
static srmech_status_t qp_q_mul(qp_ctx_t *c, srmech_bigint_t *out_num,
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
    return qp_q_reduce(c, out_num, out_den);
}

/* ---- trim + sizing helpers ----------------------------------------- */

/* The trimmed q-run length: drop trailing-zero (high-q-degree) coefficients. A
 * coefficient is zero iff its numerator is zero. */
static size_t qp_trim_len(const srmech_bigint_t *nums, size_t n)
{
    size_t k = n;
    assert(nums != NULL || n == 0u);
    while (k > 0u && srmech_bigint_is_zero(&nums[k - 1u])) {
        k--;
    }
    assert(k <= n);                          /* trim never grows the length */
    return k;
}

/* The largest significant limb count across a CONCATENATED row's num/den
 * coefficient arrays (`total` coefficients in all). */
static size_t qp_row_max_limbs(const srmech_bigint_t *nums,
                               const srmech_bigint_t *dens, size_t total)
{
    size_t k, cl = 1u;
    assert(nums != NULL || total == 0u);
    assert(dens != NULL || total == 0u);
    for (k = 0u; k < total; k++) {
        if (nums[k].n > cl) { cl = nums[k].n; }
        if (dens[k].n > cl) { cl = dens[k].n; }
    }
    return cl;
}

/* The total coefficient count across all cells (sum of qlen[]). */
static size_t qp_q_total(const size_t *qlen, size_t cells)
{
    size_t k, tot = 0u;
    assert(qlen != NULL || cells == 0u);
    for (k = 0u; k < cells; k++) {
        tot += qlen[k];
    }
    assert(k == cells);                      /* the bounded loop ran to the end */
    return tot;
}

/* ---- arena bound --------------------------------------------------- *
 * Each output cell coefficient is an exact-Q combination (sum of products) of
 * input coefficients, reduced after every op. The UNREDUCED intermediate reaches
 * the PRODUCT of input num+den magnitudes accumulated over the longest q-run
 * convolution (`accum_terms` products into one output coefficient). We size each
 * carrier to hold that worst-case product. (Mirrors tri_cap_for.) */
static size_t qp_cap_for(size_t coeff_limbs, size_t accum_terms)
{
    size_t cl = (coeff_limbs == 0u) ? 1u : coeff_limbs;
    size_t at = (accum_terms == 0u) ? 1u : accum_terms;
    size_t common = cl * at + 2u;            /* common-denominator scale  */
    size_t prod = common * 2u + cl * 2u;     /* unreduced cross-product    */
    size_t cap = prod + 16u;
    assert(cap >= common);
    assert(cap >= cl);
    return cap;
}

/* Bytes the caller hands every srmech_qpoly_* op for inputs of `coeff_limbs`
 * significant limbs per coefficient and a worst-case output q-run of `n_terms`
 * coefficients. Covers QP_N_CARRIERS carriers of `cap` limbs each, plus a divmod
 * scratch tail (8*cap + 256 is a safe envelope). 8-byte-aligned uint32. (Mirrors
 * srmech_tripoly_ws_bound.) */
size_t srmech_qpoly_ws_bound(size_t coeff_limbs, size_t n_terms)
{
    size_t cap = qp_cap_for(coeff_limbs, n_terms == 0u ? 1u : n_terms);
    size_t carriers = cap * (size_t)QP_N_CARRIERS;
    size_t scratch = cap * 8u + 256u;
    size_t words = carriers + scratch;
    assert(cap >= 2u);
    assert(words >= carriers);
    return words * sizeof(uint32_t);
}

/* ---- per-cell q-run kernels ---------------------------------------- */

/* o = a +/- b for two q-runs (lengths na, nb), each cell coefficient exact-Q +
 * reduced; *o_len is the TRIMMED output length. The o arrays hold max(na, nb)
 * coefficients (pre-trim). Missing high-degree terms read as 0/1. (Mirrors
 * tri_addsub_cell.) */
static srmech_status_t qp_addsub_cell(qp_ctx_t *c, const srmech_bigint_t *a_n,
                                      const srmech_bigint_t *a_d, size_t na,
                                      const srmech_bigint_t *b_n,
                                      const srmech_bigint_t *b_d, size_t nb,
                                      int sub, srmech_bigint_t *o_n,
                                      srmech_bigint_t *o_d, size_t *o_len)
{
    srmech_status_t st;
    size_t k, m = (na > nb) ? na : nb;
    assert(c != NULL && o_n != NULL && o_d != NULL && o_len != NULL);
    assert(sub == 0 || sub == 1);
    for (k = 0u; k < m; k++) {
        const srmech_bigint_t *an, *ad, *bn, *bd;
        an = (k < na) ? &a_n[k] : &c->z0;  ad = (k < na) ? &a_d[k] : &c->z1;
        bn = (k < nb) ? &b_n[k] : &c->z0;  bd = (k < nb) ? &b_d[k] : &c->z1;
        st = qp_q_add(c, &o_n[k], &o_d[k], an, ad, bn, bd, sub);
        if (st != SRMECH_OK) { return st; }
    }
    *o_len = qp_trim_len(o_n, m);
    return SRMECH_OK;
}

/* o += a * b for two q-runs (a multiply-ACCUMULATE: the output cell o already
 * holds a partial sum of length *o_len, and the product of the two q-run
 * polynomials is added in). o arrays must hold na+nb-1 coefficients (and at least
 * the prior *o_len). *o_len is updated to the trimmed length. (Mirrors
 * tri_mac_cell.) */
static srmech_status_t qp_mac_cell(qp_ctx_t *c, const srmech_bigint_t *a_n,
                                   const srmech_bigint_t *a_d, size_t na,
                                   const srmech_bigint_t *b_n,
                                   const srmech_bigint_t *b_d, size_t nb,
                                   srmech_bigint_t *o_n, srmech_bigint_t *o_d,
                                   size_t *o_len)
{
    srmech_status_t st;
    size_t i, jj, prod_len, new_len;
    assert(c != NULL && o_n != NULL && o_d != NULL && o_len != NULL);
    assert(a_n != NULL || na == 0u);
    if (na == 0u || nb == 0u) { return SRMECH_OK; }
    prod_len = na + nb - 1u;
    new_len = (prod_len > *o_len) ? prod_len : *o_len;
    for (i = *o_len; i < new_len; i++) {     /* extend the accumulator with 0/1 */
        st = srmech_bigint_set_i64(&o_n[i], 0);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_set_i64(&o_d[i], 1);
        if (st != SRMECH_OK) { return st; }
    }
    for (i = 0u; i < na; i++) {
        if (srmech_bigint_is_zero(&a_n[i])) { continue; }
        for (jj = 0u; jj < nb; jj++) {
            if (srmech_bigint_is_zero(&b_n[jj])) { continue; }
            st = qp_q_mul(c, &c->qa_n, &c->qa_d, &a_n[i], &a_d[i],
                          &b_n[jj], &b_d[jj]);             /* term = a_i*b_j */
            if (st != SRMECH_OK) { return st; }
            st = srmech_bigint_copy(&c->qb_n, &o_n[i + jj]);
            if (st != SRMECH_OK) { return st; }
            st = srmech_bigint_copy(&c->qb_d, &o_d[i + jj]);
            if (st != SRMECH_OK) { return st; }
            st = qp_q_add(c, &o_n[i + jj], &o_d[i + jj],
                          &c->qb_n, &c->qb_d, &c->qa_n, &c->qa_d, 0);
            if (st != SRMECH_OK) { return st; }
        }
    }
    *o_len = qp_trim_len(o_n, new_len);
    return SRMECH_OK;
}

/* ---- add / sub ----------------------------------------------------- *
 * The two rows must have the SAME `cells` count (the caller pre-aligns both to
 * the union x-window, padding missing cells to empty q-runs — mirroring how the
 * Python QPoly._addsub spans [min x_low, max x_high]). Each output cell is the
 * cellwise exact-Q add/sub of the two input cells' q-runs; *out_qlen[cell] gets
 * the trimmed q-run length. (Mirrors tri_addsub, one dimension lighter.) */

static srmech_status_t qp_addsub(const srmech_bigint_t *a_n,
                                 const srmech_bigint_t *a_d,
                                 const size_t *a_qlen, size_t cells,
                                 const srmech_bigint_t *b_n,
                                 const srmech_bigint_t *b_d,
                                 const size_t *b_qlen, int sub,
                                 srmech_bigint_t *out_n, srmech_bigint_t *out_d,
                                 size_t *out_qlen, void *ws, size_t ws_len)
{
    qp_ctx_t c;
    srmech_status_t st;
    size_t cell, a_off = 0u, b_off = 0u, o_off = 0u, atot, btot, cl;
    uint32_t cap;
    assert(out_n != NULL && out_d != NULL && out_qlen != NULL);
    assert(sub == 0 || sub == 1);
    atot = qp_q_total(a_qlen, cells);
    btot = qp_q_total(b_qlen, cells);
    cl = qp_row_max_limbs(a_n, a_d, atot);
    { size_t cb = qp_row_max_limbs(b_n, b_d, btot); if (cb > cl) { cl = cb; } }
    cap = (uint32_t)qp_cap_for(cl, 2u);
    st = qp_ctx_init(&c, cap, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    for (cell = 0u; cell < cells; cell++) {
        size_t na = a_qlen[cell], nb = b_qlen[cell], olen = 0u;
        st = qp_addsub_cell(&c, &a_n[a_off], &a_d[a_off], na,
                            &b_n[b_off], &b_d[b_off], nb, sub,
                            &out_n[o_off], &out_d[o_off], &olen);
        if (st != SRMECH_OK) { return st; }
        out_qlen[cell] = olen;
        a_off += na;
        b_off += nb;
        o_off += (na > nb) ? na : nb;       /* the pre-trim cell stride */
    }
    return SRMECH_OK;
}

srmech_status_t srmech_qpoly_add(const srmech_bigint_t *a_n,
                                 const srmech_bigint_t *a_d,
                                 const size_t *a_qlen, size_t cells,
                                 const srmech_bigint_t *b_n,
                                 const srmech_bigint_t *b_d,
                                 const size_t *b_qlen,
                                 srmech_bigint_t *out_n, srmech_bigint_t *out_d,
                                 size_t *out_qlen, void *ws, size_t ws_len)
{
    assert(out_n != NULL && out_d != NULL && out_qlen != NULL);
    assert(a_qlen != NULL || cells == 0u);
    if (out_n == NULL || out_d == NULL || out_qlen == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    return qp_addsub(a_n, a_d, a_qlen, cells, b_n, b_d, b_qlen, 0,
                     out_n, out_d, out_qlen, ws, ws_len);
}

srmech_status_t srmech_qpoly_sub(const srmech_bigint_t *a_n,
                                 const srmech_bigint_t *a_d,
                                 const size_t *a_qlen, size_t cells,
                                 const srmech_bigint_t *b_n,
                                 const srmech_bigint_t *b_d,
                                 const size_t *b_qlen,
                                 srmech_bigint_t *out_n, srmech_bigint_t *out_d,
                                 size_t *out_qlen, void *ws, size_t ws_len)
{
    assert(out_n != NULL && out_d != NULL && out_qlen != NULL);
    assert(a_qlen != NULL || cells == 0u);
    if (out_n == NULL || out_d == NULL || out_qlen == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    return qp_addsub(a_n, a_d, a_qlen, cells, b_n, b_d, b_qlen, 1,
                     out_n, out_d, out_qlen, ws, ws_len);
}

/* ---- mul (1-D x-convolution; each cell a q-run convolution) -------- *
 * Input rows: A is `acells` x-cells, B is `bcells` x-cells. The product row is
 * acells+bcells-1 cells. Output cell (ai+bi) += A[ai] * B[bi] (a q-run
 * convolution, multiply-accumulated). The caller pre-zeros the output (total
 * slots) and passes the per-output-cell q-run capacity in out_qlen[cell] on ENTRY
 * (the caller-sized stride); the op fills + trims each, writing the final trimmed
 * length back. out_off[cell] is the flat offset of cell `cell` in the output
 * arrays. (Mirrors tri_mul_body, one dimension lighter.) */

static srmech_status_t qp_mul_body(qp_ctx_t *c, const srmech_bigint_t *a_n,
                                   const srmech_bigint_t *a_d,
                                   const size_t *a_qlen, size_t acells,
                                   const srmech_bigint_t *b_n,
                                   const srmech_bigint_t *b_d,
                                   const size_t *b_qlen, size_t bcells,
                                   srmech_bigint_t *out_n, srmech_bigint_t *out_d,
                                   size_t *out_qlen, const size_t *out_off)
{
    srmech_status_t st;
    size_t ai, bi, a_o = 0u;
    assert(c != NULL && out_n != NULL && out_qlen != NULL && out_off != NULL);
    assert(out_d != NULL && (a_qlen != NULL || acells == 0u));
    for (ai = 0u; ai < acells; ai++) {
        size_t b_o = 0u;
        for (bi = 0u; bi < bcells; bi++) {
            size_t ocell = ai + bi;
            st = qp_mac_cell(c, &a_n[a_o], &a_d[a_o], a_qlen[ai],
                             &b_n[b_o], &b_d[b_o], b_qlen[bi],
                             &out_n[out_off[ocell]], &out_d[out_off[ocell]],
                             &out_qlen[ocell]);
            if (st != SRMECH_OK) { return st; }
            b_o += b_qlen[bi];
        }
        a_o += a_qlen[ai];
    }
    return SRMECH_OK;
}

srmech_status_t srmech_qpoly_mul(const srmech_bigint_t *a_n,
                                 const srmech_bigint_t *a_d,
                                 const size_t *a_qlen, size_t acells,
                                 const srmech_bigint_t *b_n,
                                 const srmech_bigint_t *b_d,
                                 const size_t *b_qlen, size_t bcells,
                                 srmech_bigint_t *out_n, srmech_bigint_t *out_d,
                                 size_t *out_qlen, const size_t *out_off,
                                 size_t accum_terms, void *ws, size_t ws_len)
{
    qp_ctx_t c;
    srmech_status_t st;
    size_t atot, btot, cl;
    uint32_t cap;
    assert(out_n != NULL && out_d != NULL && out_qlen != NULL);
    assert(out_off != NULL);
    if (out_n == NULL || out_d == NULL || out_qlen == NULL || out_off == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (acells == 0u || bcells == 0u) { return SRMECH_OK; }
    atot = qp_q_total(a_qlen, acells);
    btot = qp_q_total(b_qlen, bcells);
    cl = qp_row_max_limbs(a_n, a_d, atot);
    { size_t cb = qp_row_max_limbs(b_n, b_d, btot); if (cb > cl) { cl = cb; } }
    cap = (uint32_t)qp_cap_for(cl, accum_terms + 1u);
    st = qp_ctx_init(&c, cap, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    return qp_mul_body(&c, a_n, a_d, a_qlen, acells, b_n, b_d, b_qlen, bcells,
                       out_n, out_d, out_qlen, out_off);
}

/* ---- qshift (the q-shift sigma^s : x -> q^s * x) ------------------- *
 * Cell i (x-exponent x_low+i, coefficient c_i(q)) -> c_i(q) * q^(s*(x_low+i)):
 * each cell's q-run is SHIFTED UP by `shift = s*(x_low+i)` q-degrees (prepend
 * `shift` zero q-coefficients). The x-window is UNCHANGED (out has the same
 * `cells` count). The caller must guarantee every shift >= 0 (the Q[q] ground
 * ring); a negative shift -> SRMECH_ERR_BAD_INPUT (a Laurent-in-q result needs the
 * Q(q) carrier, which q-Gosper never asks of this op). The op copies each input
 * coefficient up by `shift` slots and zero-fills the low q-degrees. The caller
 * pre-zeros the output + passes each cell's output capacity in out_qlen[cell] on
 * ENTRY (>= in q-len + shift). out_off[cell] is the flat output offset. */

static srmech_status_t qp_shift_cell(const srmech_bigint_t *a_n,
                                     const srmech_bigint_t *a_d, size_t na,
                                     size_t shift, srmech_bigint_t *o_n,
                                     srmech_bigint_t *o_d, size_t *o_len)
{
    srmech_status_t st;
    size_t k, m;
    assert(o_n != NULL && o_d != NULL && o_len != NULL);
    assert(a_n != NULL || na == 0u);
    if (na == 0u) { *o_len = 0u; return SRMECH_OK; }
    m = na + shift;
    for (k = 0u; k < shift; k++) {           /* zero-fill the low q-degrees */
        st = srmech_bigint_set_i64(&o_n[k], 0);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_set_i64(&o_d[k], 1);
        if (st != SRMECH_OK) { return st; }
    }
    for (k = 0u; k < na; k++) {              /* copy each coeff up by `shift` */
        st = srmech_bigint_copy(&o_n[shift + k], &a_n[k]);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_copy(&o_d[shift + k], &a_d[k]);
        if (st != SRMECH_OK) { return st; }
    }
    *o_len = qp_trim_len(o_n, m);
    return SRMECH_OK;
}

srmech_status_t srmech_qpoly_qshift(const srmech_bigint_t *a_n,
                                    const srmech_bigint_t *a_d,
                                    const size_t *a_qlen, size_t cells,
                                    int64_t s, int64_t x_low,
                                    srmech_bigint_t *out_n,
                                    srmech_bigint_t *out_d, size_t *out_qlen,
                                    const size_t *out_off, void *ws,
                                    size_t ws_len)
{
    qp_ctx_t c;
    srmech_status_t st;
    size_t cell, a_off = 0u, atot, cl;
    uint32_t cap;
    assert(out_n != NULL && out_d != NULL && out_qlen != NULL && out_off != NULL);
    assert(a_qlen != NULL || cells == 0u);
    if (out_n == NULL || out_d == NULL || out_qlen == NULL || out_off == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (cells == 0u) { return SRMECH_OK; }
    atot = qp_q_total(a_qlen, cells);
    cl = qp_row_max_limbs(a_n, a_d, atot);
    cap = (uint32_t)qp_cap_for(cl, 2u);      /* qshift is a copy — no growth */
    st = qp_ctx_init(&c, cap, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    for (cell = 0u; cell < cells; cell++) {
        int64_t e = x_low + (int64_t)cell;   /* the cell's x-exponent */
        int64_t sh = s * e;                  /* the q-power shift s*e */
        size_t olen = 0u;
        if (sh < 0) { return SRMECH_ERR_BAD_INPUT; }   /* would leave Q[q] */
        st = qp_shift_cell(&a_n[a_off], &a_d[a_off], a_qlen[cell],
                           (size_t)sh, &out_n[out_off[cell]],
                           &out_d[out_off[cell]], &olen);
        if (st != SRMECH_OK) { return st; }
        out_qlen[cell] = olen;
        a_off += a_qlen[cell];
    }
    return SRMECH_OK;
}
