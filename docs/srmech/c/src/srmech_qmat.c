/*
 * srmech_qmat.c — EXACT-RATIONAL dense matrix over srmech_bigint (the C peer of
 * srmech.amsc.qmat.QMat; the exact ℚ-linear-algebra carrier the §76 gosper
 * undetermined-coefficient solve needs in C).
 *
 * A matrix is carried ROW-MAJOR as two parallel caller-owned arrays of
 * srmech_bigint: nums[r*ncols + c] / dens[r*ncols + c] is the exact-rational
 * entry at (r, c) (dens > 0, gcd(|nums|, dens) == 1; the zero entry is 0/1).
 * Every op below computes the SAME exact rational entries the Python
 * srmech.amsc.qmat.QMat computes — exact Gauss-Jordan over ℚ on the shared
 * _rref_augmented kernel (the same elimination, over plain Q) — over
 * caller-arena srmech_bigint (NO malloc, JPL Rule 3), reduced to lowest terms
 * with positive denominator. Byte-identical to Python's (num, den) at ANY
 * magnitude (full bignum — no int64/Q61 ceiling).
 *
 *   rref     : reduced row echelon over ℚ (leading-1 pivots, cleared above +
 *              below); returns the rref matrix + rank + the column->pivot-row map.
 *   rank     : the pivot count of the rref.
 *   det      : square determinant via forward Gauss elimination with explicit
 *              pivoting; the swap sign is a Class-K int ±1 pin-slot (never abs).
 *   inverse  : [A | I] Gauss-Jordan; left half == I iff invertible.
 *   solve    : [A | b] Gauss-Jordan; unique solution iff A is full-rank-square.
 *   nullspace: the classical free-variable basis (one column per free column),
 *              mirroring QMat's exact basis convention element-for-element.
 *
 * The shared kernel is qmat_rref_augmented (mirrors Python _rref_augmented):
 * pivot on the first nonzero Q at or below the current row (Q != 0, never a
 * float tolerance), scale the pivot row to a leading 1, clear EVERY other row.
 *
 * ARENA SOUNDNESS (the load-bearing claim). Every entry of the exact RREF is a
 * ratio of MINORS of the input (Cramer's rule on the row-reduction), so after
 * the per-op gcd-reduction each numerator and denominator divides a minor whose
 * magnitude Hadamard-bounds at k^(k/2) * M^k for a k x k minor of integer-scaled
 * entries of magnitude M (k <= min(n_rows, total_cols)). qmat_cap_for sizes each
 * working carrier to coeff_limbs * (n_rows + total_cols) + a log-headroom slack
 * — which dominates that minor bit-length (n*(log2 n / 2 + log2 M) bits) by a
 * wide margin — and the unreduced cross-product intermediates (a Q add/mul before
 * reduce) get a further x2. Any residual overflow returns SRMECH_ERR_OVERFLOW
 * (never a silent wrap); the Python QMat falls back to its ceiling-free
 * pure-bigint Gauss-Jordan — so the standalone-complete honor holds (a C-only
 * host either succeeds exactly or reports OVERFLOW, never wraps).
 *
 * STANDALONE-COMPLETE: every working entry carrier + the matrix scratch + the
 * divmod/reduce scratch is carved from the caller arena `ws` (>= the matching
 * srmech_qmat_*_ws_bound), so the bound is the CALLER's RAM, not a compiled-in
 * cap. Caller-arena, no fallback baked in.
 *
 * Carrier-internal, like srmech_poly.c / srmech_bigexp.c: NOT a Rosetta ledger
 * op (no ToolEntry, no count-test). Additive symbols -> ABI unchanged (stays 3).
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto/recursion): OK — iterative, flat helpers
 *   - Rule 2 (bounded loops)    : OK — bounds are row/col counts
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

/* A roster of scratch bigints carved from the caller arena `ws` for the exact-Q
 * scalar arithmetic (each entry is num/den). qa/qb hold running rationals, the
 * tN are integer scratch, g/rem/rs0/rs1 are the reducer's private sinks, z0/z1
 * are read-only units. Every carrier is `cap` limbs. Mirrors poly_ctx_t. */
typedef struct qmat_ctx {
    srmech_bigint_t qa_n;   /* accumulator rational numerator   */
    srmech_bigint_t qa_d;   /* accumulator rational denominator */
    srmech_bigint_t qb_n;   /* second operand numerator         */
    srmech_bigint_t qb_d;   /* second operand denominator       */
    srmech_bigint_t fa_n;   /* axpy factor snapshot numerator   */
    srmech_bigint_t fa_d;   /* axpy factor snapshot denominator */
    srmech_bigint_t pr_n;   /* det running-product numerator    */
    srmech_bigint_t pr_d;   /* det running-product denominator  */
    srmech_bigint_t t0;     /* integer scratch (Q add cross)    */
    srmech_bigint_t g;      /* gcd sink (reduce-private)        */
    srmech_bigint_t rem;    /* divmod remainder sink (reduce)   */
    srmech_bigint_t rs0;    /* reduce-private quotient scratch  */
    srmech_bigint_t rs1;    /* reduce-private quotient scratch  */
    srmech_bigint_t z0;     /* read-only 0                      */
    srmech_bigint_t z1;     /* read-only 1                      */
    uint32_t limb_cap;      /* per-carrier limb capacity        */
    void  *scratch;         /* divmod/gcd scratch arena tail    */
    size_t scratch_len;     /* its length in BYTES              */
} qmat_ctx_t;

#define QMAT_N_CARRIERS 15u  /* qa,qb,fa,pr (×2) + t0,g,rem,rs0,rs1,z0,z1 */

/* ---- forward declarations (Rule 1: no recursion) ------------------- */

static uint32_t *qmat_take(uint32_t *base, size_t words, size_t *cur,
                           size_t count);
static srmech_status_t qmat_bind(srmech_bigint_t *b, uint32_t *base,
                                 size_t words, size_t *cur, uint32_t cap);
static srmech_status_t qmat_ctx_init(qmat_ctx_t *c, uint32_t cap,
                                     void *ws, size_t ws_len);
static srmech_status_t qmat_q_reduce(qmat_ctx_t *c, srmech_bigint_t *num,
                                     srmech_bigint_t *den);
static srmech_status_t qmat_q_add(qmat_ctx_t *c, srmech_bigint_t *out_num,
                                  srmech_bigint_t *out_den,
                                  const srmech_bigint_t *an,
                                  const srmech_bigint_t *ad,
                                  const srmech_bigint_t *bn,
                                  const srmech_bigint_t *bd, int sub);
static srmech_status_t qmat_q_mul(qmat_ctx_t *c, srmech_bigint_t *out_num,
                                  srmech_bigint_t *out_den,
                                  const srmech_bigint_t *an,
                                  const srmech_bigint_t *ad,
                                  const srmech_bigint_t *bn,
                                  const srmech_bigint_t *bd);
static size_t qmat_max_coeff_limbs(const srmech_bigint_t *nums,
                                   const srmech_bigint_t *dens, size_t n);
static size_t qmat_cap_for(size_t coeff_limbs, size_t span);
static srmech_status_t qmat_scale_row(qmat_ctx_t *c, srmech_bigint_t *rn,
                                      srmech_bigint_t *rd, size_t total_cols,
                                      const srmech_bigint_t *pn,
                                      const srmech_bigint_t *pd);
static srmech_status_t qmat_axpy_row(qmat_ctx_t *c, srmech_bigint_t *dn,
                                     srmech_bigint_t *dd,
                                     const srmech_bigint_t *sn,
                                     const srmech_bigint_t *sd,
                                     const srmech_bigint_t *fn,
                                     const srmech_bigint_t *fd,
                                     size_t total_cols);
static void qmat_swap_rows(srmech_bigint_t *nums, srmech_bigint_t *dens,
                           size_t total_cols, size_t a, size_t b);
static srmech_status_t qmat_rref_augmented(qmat_ctx_t *c, srmech_bigint_t *nums,
                                           srmech_bigint_t *dens, size_t n_rows,
                                           size_t total_cols, size_t n_cols_left,
                                           size_t *pivot_cols, size_t *n_piv,
                                           int32_t *piv_row_of_col);

/* ---- caller-arena carve (mirrors poly_take / poly_bind) ------------ */

static uint32_t *qmat_take(uint32_t *base, size_t words, size_t *cur,
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

static srmech_status_t qmat_bind(srmech_bigint_t *b, uint32_t *base,
                                 size_t words, size_t *cur, uint32_t cap)
{
    uint32_t *limbs = qmat_take(base, words, cur, cap);
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

static srmech_status_t qmat_ctx_init(qmat_ctx_t *c, uint32_t cap,
                                     void *ws, size_t ws_len)
{
    uint32_t *base = (uint32_t *)ws;
    size_t words = ws_len / sizeof(uint32_t), cur = 0u;
    srmech_status_t st = SRMECH_OK;
    assert(c != NULL);
    assert((uintptr_t)ws % sizeof(uint32_t) == 0u || ws == NULL);
    c->limb_cap = cap;
    st |= qmat_bind(&c->qa_n, base, words, &cur, cap);
    st |= qmat_bind(&c->qa_d, base, words, &cur, cap);
    st |= qmat_bind(&c->qb_n, base, words, &cur, cap);
    st |= qmat_bind(&c->qb_d, base, words, &cur, cap);
    st |= qmat_bind(&c->fa_n, base, words, &cur, cap);
    st |= qmat_bind(&c->fa_d, base, words, &cur, cap);
    st |= qmat_bind(&c->pr_n, base, words, &cur, cap);
    st |= qmat_bind(&c->pr_d, base, words, &cur, cap);
    st |= qmat_bind(&c->t0, base, words, &cur, cap);
    st |= qmat_bind(&c->g, base, words, &cur, cap);
    st |= qmat_bind(&c->rem, base, words, &cur, cap);
    st |= qmat_bind(&c->rs0, base, words, &cur, cap);
    st |= qmat_bind(&c->rs1, base, words, &cur, cap);
    st |= qmat_bind(&c->z0, base, words, &cur, cap);
    st |= qmat_bind(&c->z1, base, words, &cur, cap);
    if (st != SRMECH_OK) {
        return SRMECH_ERR_OVERFLOW;
    }
    st = srmech_bigint_set_i64(&c->z0, 0);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&c->z1, 1);
    if (st != SRMECH_OK) { return st; }
    c->scratch = (void *)(base + cur);
    c->scratch_len = (words - cur) * sizeof(uint32_t);
    assert(cur <= words);
    return SRMECH_OK;
}

/* ---- exact-Q helpers (reduce / add / mul) — copied from the poly path -- */

/* Reduce num/den IN PLACE to lowest terms, positive denominator. den != 0;
 * 0/d -> 0/1. Uses ONLY the reduce-private carriers (g, rem, rs0, rs1) + the
 * scratch tail, so num/den may be any caller carrier without self-aliasing. */
static srmech_status_t qmat_q_reduce(qmat_ctx_t *c, srmech_bigint_t *num,
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
static srmech_status_t qmat_q_add(qmat_ctx_t *c, srmech_bigint_t *out_num,
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
    return qmat_q_reduce(c, out_num, out_den);
}

/* out = a * b (exact Q), reduced. out_* may NOT alias the inputs. */
static srmech_status_t qmat_q_mul(qmat_ctx_t *c, srmech_bigint_t *out_num,
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
    return qmat_q_reduce(c, out_num, out_den);
}

/* ---- magnitude / arena bounds ------------------------------------- */

static size_t qmat_max_coeff_limbs(const srmech_bigint_t *nums,
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

/* The per-entry limb cap. Every reduced RREF entry divides a minor whose
 * Hadamard bound is k^(k/2) * M^k (k <= span = n_rows + total_cols). In limbs
 * that bit-length is ~span * (coeff_limbs + log-headroom); we take
 * coeff_limbs * span for the M^k product, plus span for the k^(k/2) log term
 * (each limb is 32 bits, far above the per-step (log2 k)/2 bit growth), then x2
 * for the UNREDUCED Q-add/mul cross-product intermediate, plus slack. */
static size_t qmat_cap_for(size_t coeff_limbs, size_t span)
{
    size_t cl = (coeff_limbs == 0u) ? 1u : coeff_limbs;
    size_t sp = (span == 0u) ? 1u : span;
    size_t minor = cl * sp + sp + 2u;        /* one reduced minor envelope */
    size_t cap = minor * 2u + cl * 2u + 16u; /* unreduced cross-product + slack */
    assert(cap >= minor);
    assert(cap >= cl);
    return cap;
}

/* Header words per srmech_bigint (for the matrix + nullvec header arrays). */
static size_t qmat_hdr_words(void)
{
    size_t hw = (sizeof(srmech_bigint_t) + sizeof(uint32_t) - 1u)
                / sizeof(uint32_t);
    assert(sizeof(srmech_bigint_t) > 0u);
    assert(hw >= 1u);
    return hw;
}

/* Bytes the caller hands every srmech_qmat_* op for inputs of `coeff_limbs`
 * significant limbs per entry and a working matrix whose row-reduction spans
 * `n_rows` rows by `total_cols` columns (total_cols = the augmented width, e.g.
 * 2*n for inverse, n+b_cols for solve). Covers (a) the working matrix entry
 * storage (n_rows*total_cols cells, num + den, each cap limbs, plus the two
 * header arrays), (b) an n_cols-wide nullvec lane (folded into the cell count via
 * the +total_cols slack so nullspace's basis scratch always fits), (c) the
 * QMAT_N_CARRIERS scalar carriers of cap limbs, and (d) the gcd/divmod scratch
 * tail (heaviest: gcd over two cap-limb values ~4*cap; 8*cap + 256 is safe).
 * 8-byte-aligned uint32. */
size_t srmech_qmat_ws_bound(size_t coeff_limbs, size_t n_rows,
                            size_t total_cols)
{
    size_t span = n_rows + total_cols;
    size_t cap = qmat_cap_for(coeff_limbs, span == 0u ? 1u : span);
    size_t hw = qmat_hdr_words();
    /* matrix cells + an extra total_cols-row of slack for the nullvec lane */
    size_t cells = n_rows * total_cols + (total_cols == 0u ? 1u : total_cols) + 2u;
    size_t headers = 2u * hw * (cells + 2u);          /* num + den header arrays */
    size_t cell_limbs = 2u * cells * cap;             /* num + den limb runs     */
    size_t carriers = cap * (size_t)QMAT_N_CARRIERS;
    size_t scratch = cap * 8u + 256u;
    size_t words = headers + cell_limbs + carriers + scratch + 16u;
    assert(cap >= 2u);
    assert(words >= cell_limbs);
    return words * sizeof(uint32_t);
}

/* The per-entry limb cap a caller must give each srmech_bigint in the nums/dens
 * matrix output arrays (so a reduced RREF/inverse/solve entry never overflows
 * its own slot before the op's guard fires). Same envelope as the ctx cap. */
size_t srmech_qmat_entry_cap(size_t coeff_limbs, size_t n_rows,
                             size_t total_cols)
{
    size_t span = n_rows + total_cols;
    size_t cap = qmat_cap_for(coeff_limbs, span == 0u ? 1u : span);
    assert(cap >= 2u);
    assert(cap >= coeff_limbs);
    return cap;
}

/* ---- row operations over the row-major (nums, dens) matrix --------- */

/* row r <- row r * (pn/pd reciprocal): each entry *= pd/pn (so the pivot
 * becomes 1). pn/pd is the pivot rational (nonzero, an entry WITHIN this row, so
 * the reciprocal is snapshotted into rs0/rs1 FIRST — scaling rn[col] would
 * otherwise clobber the live pivot pointer before later columns are scaled).
 * total_cols entries. */
static srmech_status_t qmat_scale_row(qmat_ctx_t *c, srmech_bigint_t *rn,
                                      srmech_bigint_t *rd, size_t total_cols,
                                      const srmech_bigint_t *pn,
                                      const srmech_bigint_t *pd)
{
    size_t j;
    srmech_status_t st;
    assert(c != NULL && rn != NULL && rd != NULL);
    assert(pn != NULL && pd != NULL && pn->sign != 0);
    st = srmech_bigint_copy(&c->qb_n, pd);            /* recip numerator = pd */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&c->qb_d, pn);            /* recip denominator = pn */
    if (st != SRMECH_OK) { return st; }
    for (j = 0u; j < total_cols; j++) {
        st = qmat_q_mul(c, &c->qa_n, &c->qa_d, &rn[j], &rd[j], &c->qb_n, &c->qb_d);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_copy(&rn[j], &c->qa_n);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_copy(&rd[j], &c->qa_d);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* dst row <- dst - (fn/fd) * src row (the elimination axpy). The factor fn/fd is
 * typically an entry WITHIN dst (dst[col]) — modifying dst[col] mid-loop would
 * clobber the live factor pointer — so it is snapshotted by VALUE into the ctx's
 * dedicated fa_n/fa_d carriers FIRST (the inner Q ops never read those). The src
 * row (the pivot row) is a DIFFERENT row, so sn[j]/sd[j] stay valid. total_cols. */
static srmech_status_t qmat_axpy_row(qmat_ctx_t *c, srmech_bigint_t *dn,
                                     srmech_bigint_t *dd,
                                     const srmech_bigint_t *sn,
                                     const srmech_bigint_t *sd,
                                     const srmech_bigint_t *fn,
                                     const srmech_bigint_t *fd,
                                     size_t total_cols)
{
    size_t j;
    srmech_status_t st;
    assert(c != NULL && dn != NULL && sn != NULL && fn != NULL);
    assert(dd != NULL && sd != NULL && fd != NULL);
    st = srmech_bigint_copy(&c->fa_n, fn);            /* factor snapshot (by value) */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&c->fa_d, fd);
    if (st != SRMECH_OK) { return st; }
    for (j = 0u; j < total_cols; j++) {
        st = qmat_q_mul(c, &c->qb_n, &c->qb_d, &c->fa_n, &c->fa_d,
                        &sn[j], &sd[j]);
        if (st != SRMECH_OK) { return st; }            /* term = f * src[j] */
        st = qmat_q_add(c, &c->qa_n, &c->qa_d, &dn[j], &dd[j],
                        &c->qb_n, &c->qb_d, 1);          /* dst[j] - term     */
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_copy(&dn[j], &c->qa_n);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_copy(&dd[j], &c->qa_d);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* Swap two rows of the row-major matrix by exchanging their srmech_bigint
 * headers (limb-pointer swap; no value copy). a, b < n_rows. */
static void qmat_swap_rows(srmech_bigint_t *nums, srmech_bigint_t *dens,
                           size_t total_cols, size_t a, size_t b)
{
    size_t j;
    assert(nums != NULL && dens != NULL);
    assert(a != b || total_cols == 0u);
    for (j = 0u; j < total_cols; j++) {
        srmech_bigint_t tn = nums[a * total_cols + j];
        srmech_bigint_t td = dens[a * total_cols + j];
        nums[a * total_cols + j] = nums[b * total_cols + j];
        dens[a * total_cols + j] = dens[b * total_cols + j];
        nums[b * total_cols + j] = tn;
        dens[b * total_cols + j] = td;
    }
}

/* The shared exact Gauss-Jordan kernel (mirror of Python _rref_augmented):
 * reduce (nums, dens) in place to RREF over the first n_cols_left columns; the
 * trailing columns are carried but never pivoted on (the [A|I] / [A|b] block).
 * Writes pivot_cols[0.. *n_piv) (increasing), *n_piv, and piv_row_of_col[col]
 * = pivot row (or -1). Pivot = first nonzero Q at or below the current row. */
static srmech_status_t qmat_rref_augmented(qmat_ctx_t *c, srmech_bigint_t *nums,
                                           srmech_bigint_t *dens, size_t n_rows,
                                           size_t total_cols, size_t n_cols_left,
                                           size_t *pivot_cols, size_t *n_piv,
                                           int32_t *piv_row_of_col)
{
    size_t col, r = 0u, np = 0u;
    srmech_status_t st;
    assert(c != NULL && nums != NULL && pivot_cols != NULL);
    assert(n_piv != NULL && piv_row_of_col != NULL);
    for (col = 0u; col < n_cols_left; col++) { piv_row_of_col[col] = -1; }
    for (col = 0u; col < n_cols_left && r < n_rows; col++) {
        size_t rr, piv = n_rows;                       /* n_rows == "none" */
        for (rr = r; rr < n_rows; rr++) {
            if (!srmech_bigint_is_zero(&nums[rr * total_cols + col])) {
                piv = rr; break;
            }
        }
        if (piv == n_rows) { continue; }                /* free column */
        if (piv != r) { qmat_swap_rows(nums, dens, total_cols, r, piv); }
        st = qmat_scale_row(c, &nums[r * total_cols], &dens[r * total_cols],
                            total_cols, &nums[r * total_cols + col],
                            &dens[r * total_cols + col]);
        if (st != SRMECH_OK) { return st; }
        for (rr = 0u; rr < n_rows; rr++) {              /* clear all other rows */
            if (rr == r) { continue; }
            if (srmech_bigint_is_zero(&nums[rr * total_cols + col])) { continue; }
            st = qmat_axpy_row(c, &nums[rr * total_cols], &dens[rr * total_cols],
                               &nums[r * total_cols], &dens[r * total_cols],
                               &nums[rr * total_cols + col],
                               &dens[rr * total_cols + col], total_cols);
            if (st != SRMECH_OK) { return st; }
        }
        pivot_cols[np] = col;
        piv_row_of_col[col] = (int32_t)r;
        np++; r++;
    }
    *n_piv = np;
    return SRMECH_OK;
}

/* ---- public ops: the matrix-entry arena carve + the six surfaces ---- *
 * Each op carves its working matrix (n_rows x total_cols entries, num + den)
 * from the caller arena FIRST, copies the input in, then hands the remaining
 * tail to qmat_ctx_init as the scalar/divmod scratch — the same FIRST-carve
 * pattern poly_gcd uses. */

/* Carve a row-major (nums, dens) matrix of n_rows*total_cols entries, each a
 * cap-limb bigint, from the arena; bind the ctx from the remaining tail. */
static srmech_status_t qmat_carve(srmech_bigint_t **nums, srmech_bigint_t **dens,
                                  qmat_ctx_t *c, uint32_t *base, size_t words,
                                  size_t *cur, uint32_t cap, size_t cells)
{
    size_t hw = qmat_hdr_words(), k;
    uint32_t *hn, *hd;
    srmech_status_t st;
    assert(nums != NULL && dens != NULL && c != NULL && cur != NULL);
    assert(cap > 0u);
    hn = qmat_take(base, words, cur, hw * (cells == 0u ? 1u : cells));
    hd = qmat_take(base, words, cur, hw * (cells == 0u ? 1u : cells));
    if (hn == NULL || hd == NULL) { return SRMECH_ERR_OVERFLOW; }
    *nums = (srmech_bigint_t *)(void *)hn;
    *dens = (srmech_bigint_t *)(void *)hd;
    for (k = 0u; k < cells; k++) {
        st = qmat_bind(&(*nums)[k], base, words, cur, cap);
        if (st != SRMECH_OK) { return st; }
        st = qmat_bind(&(*dens)[k], base, words, cur, cap);
        if (st != SRMECH_OK) { return st; }
    }
    return qmat_ctx_init(c, cap, (void *)(base + *cur),
                         (words - *cur) * sizeof(uint32_t));
}

/* Copy the input A (n_rows x n_cols) into the left block of the working matrix
 * (n_rows x total_cols), and fill the trailing block per `aug`:
 *   aug == 0 : nothing (rref/rank/nullspace; total_cols == n_cols).
 *   aug == 1 : the n x n identity (inverse; total_cols == 2*n_cols).
 * The [A|b] solve fills its own b block via qmat_load_b. */
static srmech_status_t qmat_load_left(srmech_bigint_t *nums,
                                      srmech_bigint_t *dens, size_t n_rows,
                                      size_t n_cols, size_t total_cols,
                                      const srmech_bigint_t *a_n,
                                      const srmech_bigint_t *a_d, int aug)
{
    size_t r, j;
    srmech_status_t st;
    assert(nums != NULL && a_n != NULL);
    assert(total_cols >= n_cols);
    for (r = 0u; r < n_rows; r++) {
        for (j = 0u; j < total_cols; j++) {
            srmech_bigint_t *dn = &nums[r * total_cols + j];
            srmech_bigint_t *dd = &dens[r * total_cols + j];
            if (j < n_cols) {
                st = srmech_bigint_copy(dn, &a_n[r * n_cols + j]);
                if (st == SRMECH_OK) { st = srmech_bigint_copy(dd, &a_d[r * n_cols + j]); }
            } else if (aug == 1) {
                st = srmech_bigint_set_i64(dn, (j - n_cols == r) ? 1 : 0);
                if (st == SRMECH_OK) { st = srmech_bigint_set_i64(dd, 1); }
            } else {
                st = srmech_bigint_set_i64(dn, 0);
                if (st == SRMECH_OK) { st = srmech_bigint_set_i64(dd, 1); }
            }
            if (st != SRMECH_OK) { return st; }
        }
    }
    return SRMECH_OK;
}

/* Read the reduced left block (n_rows x n_cols) of the working matrix out to the
 * caller's out_n/out_d arrays (row-major, n_cols wide). */
static srmech_status_t qmat_store_block(const srmech_bigint_t *nums,
                                        const srmech_bigint_t *dens,
                                        size_t n_rows, size_t n_cols,
                                        size_t total_cols, size_t col0,
                                        srmech_bigint_t *out_n,
                                        srmech_bigint_t *out_d)
{
    size_t r, j;
    srmech_status_t st;
    assert(nums != NULL && out_n != NULL && out_d != NULL);
    assert(col0 + n_cols <= total_cols);
    for (r = 0u; r < n_rows; r++) {
        for (j = 0u; j < n_cols; j++) {
            st = srmech_bigint_copy(&out_n[r * n_cols + j],
                                    &nums[r * total_cols + col0 + j]);
            if (st != SRMECH_OK) { return st; }
            st = srmech_bigint_copy(&out_d[r * n_cols + j],
                                    &dens[r * total_cols + col0 + j]);
            if (st != SRMECH_OK) { return st; }
        }
    }
    return SRMECH_OK;
}

/* ---- rref / rank -------------------------------------------------- */

/* Shared rref driver: carve, load A, reduce, hand back the working matrix +
 * pivot info via the caller's pivot_cols/n_piv/piv_row_of_col (sized n_cols).
 * out_n/out_d (if non-NULL) receive the reduced left block. */
static srmech_status_t qmat_run_rref(const srmech_bigint_t *a_n,
                                     const srmech_bigint_t *a_d, size_t n_rows,
                                     size_t n_cols, srmech_bigint_t *out_n,
                                     srmech_bigint_t *out_d, size_t *pivot_cols,
                                     size_t *n_piv, int32_t *piv_row_of_col,
                                     void *ws, size_t ws_len)
{
    uint32_t *base = (uint32_t *)ws;
    size_t words = ws_len / sizeof(uint32_t), cur = 0u, cl, span;
    srmech_bigint_t *nums = NULL, *dens = NULL;
    qmat_ctx_t c;
    srmech_status_t st;
    uint32_t cap;
    assert(a_n != NULL && pivot_cols != NULL && n_piv != NULL);
    assert(piv_row_of_col != NULL && (ws != NULL || ws_len == 0u));
    cl = qmat_max_coeff_limbs(a_n, a_d, n_rows * n_cols);
    span = n_rows + n_cols;
    cap = (uint32_t)qmat_cap_for(cl, span);
    st = qmat_carve(&nums, &dens, &c, base, words, &cur, cap, n_rows * n_cols);
    if (st != SRMECH_OK) { return st; }
    st = qmat_load_left(nums, dens, n_rows, n_cols, n_cols, a_n, a_d, 0);
    if (st != SRMECH_OK) { return st; }
    st = qmat_rref_augmented(&c, nums, dens, n_rows, n_cols, n_cols,
                             pivot_cols, n_piv, piv_row_of_col);
    if (st != SRMECH_OK) { return st; }
    if (out_n != NULL) {
        st = qmat_store_block(nums, dens, n_rows, n_cols, n_cols, 0,
                              out_n, out_d);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

srmech_status_t srmech_qmat_rref(const srmech_bigint_t *a_n,
                                 const srmech_bigint_t *a_d, size_t n_rows,
                                 size_t n_cols, srmech_bigint_t *out_n,
                                 srmech_bigint_t *out_d, size_t *out_rank,
                                 size_t *pivot_cols, void *ws, size_t ws_len)
{
    int32_t prc[SRMECH_QMAT_MAX_DIM];
    size_t piv[SRMECH_QMAT_MAX_DIM], np = 0u;
    srmech_status_t st;
    assert(out_n != NULL && out_d != NULL && out_rank != NULL);
    assert(pivot_cols != NULL && a_n != NULL);
    if (out_n == NULL || out_d == NULL || out_rank == NULL
        || pivot_cols == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n_cols > SRMECH_QMAT_MAX_DIM) { return SRMECH_ERR_BAD_INPUT; }
    st = qmat_run_rref(a_n, a_d, n_rows, n_cols, out_n, out_d, piv, &np, prc,
                       ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    *out_rank = np;
    { size_t k; for (k = 0u; k < np; k++) { pivot_cols[k] = piv[k]; } }
    return SRMECH_OK;
}

srmech_status_t srmech_qmat_rank(const srmech_bigint_t *a_n,
                                 const srmech_bigint_t *a_d, size_t n_rows,
                                 size_t n_cols, size_t *out_rank,
                                 void *ws, size_t ws_len)
{
    int32_t prc[SRMECH_QMAT_MAX_DIM];
    size_t piv[SRMECH_QMAT_MAX_DIM], np = 0u;
    srmech_status_t st;
    assert(out_rank != NULL);
    assert(a_n != NULL && a_d != NULL);
    if (out_rank == NULL) { return SRMECH_ERR_NULL_ARG; }
    if (n_cols > SRMECH_QMAT_MAX_DIM) { return SRMECH_ERR_BAD_INPUT; }
    st = qmat_run_rref(a_n, a_d, n_rows, n_cols, NULL, NULL, piv, &np, prc,
                       ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    *out_rank = np;
    return SRMECH_OK;
}

/* ---- det (forward Gauss elimination with explicit pivoting) -------- */

/* Eliminate below the pivot at (col,col) for the det forward sweep; multiply
 * `prod` by the pivot. Returns SRMECH_OK or an arithmetic error. *singular set
 * when a zero column is found (det 0). */
static srmech_status_t qmat_det_step(qmat_ctx_t *c, srmech_bigint_t *nums,
                                     srmech_bigint_t *dens, size_t n, size_t col,
                                     int *sign, srmech_bigint_t *prod_n,
                                     srmech_bigint_t *prod_d, int *singular)
{
    size_t rr, piv = n;
    srmech_status_t st;
    assert(c != NULL && nums != NULL && sign != NULL && singular != NULL);
    assert(prod_n != NULL && prod_d != NULL);
    for (rr = col; rr < n; rr++) {
        if (!srmech_bigint_is_zero(&nums[rr * n + col])) { piv = rr; break; }
    }
    if (piv == n) { *singular = 1; return SRMECH_OK; }
    if (piv != col) { qmat_swap_rows(nums, dens, n, col, piv); *sign = -(*sign); }
    st = qmat_q_mul(c, &c->qa_n, &c->qa_d, prod_n, prod_d,
                    &nums[col * n + col], &dens[col * n + col]);
    if (st != SRMECH_OK) { return st; }                /* prod *= pivot (via qa) */
    st = srmech_bigint_copy(prod_n, &c->qa_n);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(prod_d, &c->qa_d);
    if (st != SRMECH_OK) { return st; }
    for (rr = col + 1u; rr < n; rr++) {
        if (srmech_bigint_is_zero(&nums[rr * n + col])) { continue; }
        st = qmat_q_mul(c, &c->qa_n, &c->qa_d, &nums[rr * n + col],
                        &dens[rr * n + col], &dens[col * n + col],
                        &nums[col * n + col]);          /* f = row/pivot */
        if (st != SRMECH_OK) { return st; }
        st = qmat_axpy_row(c, &nums[rr * n], &dens[rr * n],
                           &nums[col * n], &dens[col * n],
                           &c->qa_n, &c->qa_d, n);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

srmech_status_t srmech_qmat_det(const srmech_bigint_t *a_n,
                                const srmech_bigint_t *a_d, size_t n,
                                srmech_bigint_t *out_num,
                                srmech_bigint_t *out_den, void *ws, size_t ws_len)
{
    uint32_t *base = (uint32_t *)ws;
    size_t words = ws_len / sizeof(uint32_t), cur = 0u, cl, col;
    srmech_bigint_t *nums = NULL, *dens = NULL;
    qmat_ctx_t c;
    srmech_status_t st;
    uint32_t cap;
    int sign = 1, singular = 0;
    assert(out_num != NULL && out_den != NULL);
    assert(a_n != NULL && (ws != NULL || ws_len == 0u));
    if (out_num == NULL || out_den == NULL) { return SRMECH_ERR_NULL_ARG; }
    cl = qmat_max_coeff_limbs(a_n, a_d, n * n);
    cap = (uint32_t)qmat_cap_for(cl, n + n);
    st = qmat_carve(&nums, &dens, &c, base, words, &cur, cap, (n == 0u ? 1u : n * n));
    if (st != SRMECH_OK) { return st; }
    st = qmat_load_left(nums, dens, n, n, n, a_n, a_d, 0);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&c.pr_n, 1);            /* prod = 1/1 */
    if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&c.pr_d, 1); }
    if (st != SRMECH_OK) { return st; }
    for (col = 0u; col < n && !singular; col++) {
        st = qmat_det_step(&c, nums, dens, n, col, &sign, &c.pr_n, &c.pr_d,
                           &singular);
        if (st != SRMECH_OK) { return st; }
    }
    if (singular) {
        st = srmech_bigint_set_i64(out_num, 0);
        if (st == SRMECH_OK) { st = srmech_bigint_set_i64(out_den, 1); }
        return st;
    }
    st = srmech_bigint_copy(out_num, &c.pr_n);          /* det = sign * prod */
    if (st == SRMECH_OK && sign < 0 && out_num->n != 0u) { out_num->sign = -out_num->sign; }
    if (st == SRMECH_OK) { st = srmech_bigint_copy(out_den, &c.pr_d); }
    return st;
}

/* ---- inverse / solve (augmented Gauss-Jordan) --------------------- */

/* Shared augmented driver for inverse ([A|I]) and solve ([A|b]). Carves the
 * n x total working matrix, loads A in the left n cols + the trailing block,
 * runs RREF over the LEFT n columns; iff every left column is a pivot (full
 * rank, in order) the trailing block is the answer. *ok set 0 when singular. */
static srmech_status_t qmat_run_augmented(const srmech_bigint_t *a_n,
                                          const srmech_bigint_t *a_d, size_t n,
                                          size_t rhs_cols, int aug,
                                          const srmech_bigint_t *b_n,
                                          const srmech_bigint_t *b_d,
                                          srmech_bigint_t *out_n,
                                          srmech_bigint_t *out_d, int *ok,
                                          void *ws, size_t ws_len)
{
    uint32_t *base = (uint32_t *)ws;
    size_t words = ws_len / sizeof(uint32_t), cur = 0u, cl, total = n + rhs_cols;
    size_t piv[SRMECH_QMAT_MAX_DIM], np = 0u, k;
    int32_t prc[SRMECH_QMAT_MAX_DIM];
    srmech_bigint_t *nums = NULL, *dens = NULL;
    qmat_ctx_t c;
    srmech_status_t st;
    uint32_t cap;
    assert(a_n != NULL && out_n != NULL && ok != NULL);
    assert(out_d != NULL && (ws != NULL || ws_len == 0u));
    *ok = 1;
    cl = qmat_max_coeff_limbs(a_n, a_d, n * n);
    if (b_n != NULL) {
        size_t cb = qmat_max_coeff_limbs(b_n, b_d, n * rhs_cols);
        if (cb > cl) { cl = cb; }
    }
    cap = (uint32_t)qmat_cap_for(cl, n + total);
    st = qmat_carve(&nums, &dens, &c, base, words, &cur, cap,
                    (total == 0u ? 1u : n * total));
    if (st != SRMECH_OK) { return st; }
    st = qmat_load_left(nums, dens, n, n, total, a_n, a_d, aug);
    if (st != SRMECH_OK) { return st; }
    if (aug == 0 && b_n != NULL) {                     /* solve: load b block */
        for (k = 0u; k < n; k++) {
            size_t j;
            for (j = 0u; j < rhs_cols; j++) {
                st = srmech_bigint_copy(&nums[k * total + n + j],
                                        &b_n[k * rhs_cols + j]);
                if (st == SRMECH_OK) {
                    st = srmech_bigint_copy(&dens[k * total + n + j],
                                            &b_d[k * rhs_cols + j]);
                }
                if (st != SRMECH_OK) { return st; }
            }
        }
    }
    st = qmat_rref_augmented(&c, nums, dens, n, total, n, piv, &np, prc);
    if (st != SRMECH_OK) { return st; }
    if (np != n) { *ok = 0; return SRMECH_OK; }        /* singular */
    for (k = 0u; k < n; k++) { if (piv[k] != k) { *ok = 0; return SRMECH_OK; } }
    return qmat_store_block(nums, dens, n, rhs_cols, total, n, out_n, out_d);
}

srmech_status_t srmech_qmat_inverse(const srmech_bigint_t *a_n,
                                    const srmech_bigint_t *a_d, size_t n,
                                    srmech_bigint_t *out_n,
                                    srmech_bigint_t *out_d, int *out_singular,
                                    void *ws, size_t ws_len)
{
    int ok = 1;
    srmech_status_t st;
    assert(out_n != NULL && out_d != NULL && out_singular != NULL);
    assert(a_n != NULL && a_d != NULL);
    if (out_n == NULL || out_d == NULL || out_singular == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n > SRMECH_QMAT_MAX_DIM) { return SRMECH_ERR_BAD_INPUT; }
    st = qmat_run_augmented(a_n, a_d, n, n, 1, NULL, NULL, out_n, out_d, &ok,
                            ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    *out_singular = ok ? 0 : 1;
    return SRMECH_OK;
}

srmech_status_t srmech_qmat_solve(const srmech_bigint_t *a_n,
                                  const srmech_bigint_t *a_d, size_t n,
                                  const srmech_bigint_t *b_n,
                                  const srmech_bigint_t *b_d, size_t b_cols,
                                  srmech_bigint_t *out_n, srmech_bigint_t *out_d,
                                  int *out_singular, void *ws, size_t ws_len)
{
    int ok = 1;
    srmech_status_t st;
    assert(out_n != NULL && out_d != NULL && out_singular != NULL && b_n != NULL);
    assert(a_n != NULL && b_d != NULL);
    if (out_n == NULL || out_d == NULL || out_singular == NULL
        || b_n == NULL || b_d == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n > SRMECH_QMAT_MAX_DIM) { return SRMECH_ERR_BAD_INPUT; }
    st = qmat_run_augmented(a_n, a_d, n, b_cols, 0, b_n, b_d, out_n, out_d, &ok,
                            ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    *out_singular = ok ? 0 : 1;
    return SRMECH_OK;
}

/* ---- nullspace (free-variable basis; mirror of QMat.nullspace) ----- */

/* Build basis vector for the `fc`-th free column into out (n_cols entries):
 * v[fc] = 1; for each pivot column c, v[c] = -RREF[piv_row_of_col[c]][fc];
 * other free columns 0. Mirrors QMat.nullspace exactly. */
static srmech_status_t qmat_nullvec(srmech_bigint_t *nums, srmech_bigint_t *dens,
                                    size_t n_cols, size_t total_cols,
                                    const size_t *pivot_cols, size_t n_piv,
                                    const int32_t *prc, size_t fc,
                                    srmech_bigint_t *vn, srmech_bigint_t *vd)
{
    size_t i, p;
    srmech_status_t st;
    assert(nums != NULL && vn != NULL && pivot_cols != NULL && prc != NULL);
    assert(fc < n_cols);
    for (i = 0u; i < n_cols; i++) {
        st = srmech_bigint_set_i64(&vn[i], (i == fc) ? 1 : 0);
        if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&vd[i], 1); }
        if (st != SRMECH_OK) { return st; }
    }
    for (p = 0u; p < n_piv; p++) {
        size_t col = pivot_cols[p];
        size_t pr = (size_t)prc[col];
        st = srmech_bigint_copy(&vn[col], &nums[pr * total_cols + fc]);
        if (st == SRMECH_OK) { st = srmech_bigint_copy(&vd[col], &dens[pr * total_cols + fc]); }
        if (st == SRMECH_OK && vn[col].n != 0u) { vn[col].sign = -vn[col].sign; }
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* nullspace: write the kernel basis as out_n/out_d, a (n_cols x n_free) ROW-MAJOR
 * matrix whose COLUMN j is the j-th basis vector (so out[i*n_free + j] is entry i
 * of basis vector j). *out_nfree <- the free-column count (basis size). The
 * caller sizes out for n_cols * (n_cols) entries (n_free <= n_cols). */
srmech_status_t srmech_qmat_nullspace(const srmech_bigint_t *a_n,
                                      const srmech_bigint_t *a_d, size_t n_rows,
                                      size_t n_cols, srmech_bigint_t *out_n,
                                      srmech_bigint_t *out_d, size_t *out_nfree,
                                      void *ws, size_t ws_len)
{
    uint32_t *base = (uint32_t *)ws;
    size_t words = ws_len / sizeof(uint32_t), cur = 0u, cl, span;
    size_t piv[SRMECH_QMAT_MAX_DIM], np = 0u, col, nfree = 0u, bi = 0u, i;
    int32_t prc[SRMECH_QMAT_MAX_DIM];
    srmech_bigint_t *nums = NULL, *dens = NULL, *vn = NULL, *vd = NULL;
    qmat_ctx_t c;
    srmech_status_t st;
    uint32_t cap;
    assert(a_n != NULL && out_n != NULL && out_nfree != NULL);
    assert(out_d != NULL && (ws != NULL || ws_len == 0u));
    if (out_n == NULL || out_d == NULL || out_nfree == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n_cols > SRMECH_QMAT_MAX_DIM) { return SRMECH_ERR_BAD_INPUT; }
    cl = qmat_max_coeff_limbs(a_n, a_d, n_rows * n_cols);
    span = n_rows + n_cols;
    cap = (uint32_t)qmat_cap_for(cl, span);
    st = qmat_carve(&nums, &dens, &c, base, words, &cur, cap,
                    (n_rows * n_cols == 0u ? 1u : n_rows * n_cols));
    if (st != SRMECH_OK) { return st; }
    /* a single n_cols-wide basis-vector scratch carved AFTER the matrix but the
     * ctx took the tail; carve vn/vd from a fresh slice of the ctx scratch. */
    { uint32_t *vb = (uint32_t *)c.scratch;
      size_t vw = c.scratch_len / sizeof(uint32_t), vc = 0u, hw = qmat_hdr_words();
      uint32_t *hvn = qmat_take(vb, vw, &vc, hw * (n_cols == 0u ? 1u : n_cols));
      uint32_t *hvd = qmat_take(vb, vw, &vc, hw * (n_cols == 0u ? 1u : n_cols));
      if (hvn == NULL || hvd == NULL) { return SRMECH_ERR_OVERFLOW; }
      vn = (srmech_bigint_t *)(void *)hvn; vd = (srmech_bigint_t *)(void *)hvd;
      for (i = 0u; i < n_cols; i++) {
          st = qmat_bind(&vn[i], vb, vw, &vc, cap);
          if (st == SRMECH_OK) { st = qmat_bind(&vd[i], vb, vw, &vc, cap); }
          if (st != SRMECH_OK) { return st; }
      }
      c.scratch = (void *)(vb + vc); c.scratch_len = (vw - vc) * sizeof(uint32_t);
    }
    st = qmat_load_left(nums, dens, n_rows, n_cols, n_cols, a_n, a_d, 0);
    if (st != SRMECH_OK) { return st; }
    st = qmat_rref_augmented(&c, nums, dens, n_rows, n_cols, n_cols, piv, &np, prc);
    if (st != SRMECH_OK) { return st; }
    for (col = 0u; col < n_cols; col++) {
        if (prc[col] >= 0) { continue; }                /* a pivot column */
        st = qmat_nullvec(nums, dens, n_cols, n_cols, piv, np, prc, col, vn, vd);
        if (st != SRMECH_OK) { return st; }
        for (i = 0u; i < n_cols; i++) {                 /* store as column bi */
            st = srmech_bigint_copy(&out_n[i * n_cols + bi], &vn[i]);
            if (st == SRMECH_OK) { st = srmech_bigint_copy(&out_d[i * n_cols + bi], &vd[i]); }
            if (st != SRMECH_OK) { return st; }
        }
        bi++; nfree++;
    }
    *out_nfree = nfree;
    return SRMECH_OK;
}
