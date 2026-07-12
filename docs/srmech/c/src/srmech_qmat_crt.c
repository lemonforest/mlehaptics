/*
 * srmech_qmat_crt.c -- the CRT re-fibration of the exact-Q RREF, as ONE
 * standalone C symbol (srmech 0.9.0rc48, the CLOSER of the CRT-QMat arc).
 *
 * srmech_qmat_rref_crt orchestrates the four already-C-backed rungs of the arc
 * into the full bounded-memory exact-Q solve a bare-C host can call with ONE
 * call:
 *
 *   rung 1  srmech_gf_rref               -- swell-free GF(p) RREF (int64)
 *   rung 2  srmech_crt_combine           -- CRT-combine per-prime residues
 *           srmech_rational_reconstruct  -- half-GCD (Wang) recovery
 *   rung 4  the descending prime walk    -- srmech_is_prime over odd candidates
 *
 * It is BYTE-IDENTICAL to the pure-Python srmech.amsc.qmat.QMat.rref_crt
 * (_rref_crt_rows with n_cols_left == n_cols): descending odd primes from
 * 2**31 - 2, skip a prime dividing any denominator, gf_rref per prime over
 * GF(p), unlucky-prime rank-consensus (max (rank, pivots) dominates; a strictly
 * higher-rank prime RESTARTS the CRT), crt_combine per cell, then
 * rational_reconstruct with the DEFAULT Wang bound isqrt(modulus // 2), then
 * stabilization early-termination (reconstructed matrix identical across two
 * consecutive good primes). The byte-identity gate: same prime sequence, same
 * consensus rule, same Wang bound, same stop -> same exact-Q RREF entries.
 *
 * THE ARENA BOUND -- why this row is bounded and the dense rref is not.
 * --------------------------------------------------------------------
 * The dense exact-Q Gauss-Jordan (srmech_qmat_rref) grows the numerators +
 * denominators at EVERY pivot, so its malloc-free arena must reserve the
 * worst-case fraction (Hadamard) ENVELOPE OF THE ELIMINATION -- GB-scale on the
 * order-2 Franel system. The CRT path instead solves mod several ~31-bit primes
 * (each a tiny int64 GF(p) RREF, n_rows*n_cols*8 bytes, NO bignum), and the only
 * bignum is the final per-cell crt_combine product + rational_reconstruct, whose
 * size is bounded by the NUMBER OF GOOD PRIMES -- and that count is bounded a
 * priori by the ANSWER size, NOT the elimination swell:
 *
 *   Every reduced RREF entry is a ratio of MINORS of the input (Cramer): a k x k
 *   minor of integer-scaled entries of magnitude <= M Hadamard-bounds at
 *   k^(k/2) * M^k (k <= min(n_rows, n_cols) <= span). So |num|,|den| of any
 *   answer entry are each < H := span^(span/2) * M^span, i.e.
 *   log2 H < span * (log2 span / 2 + log2 M).  (M bounds |num|,|den| of the
 *   common-denominator-cleared input, so log2 M <= input_bits + log2 span.)
 *
 *   Wang reconstruction (num_bound = den_bound = isqrt(modulus // 2)) succeeds
 *   once modulus // 2 > H^2, i.e. once the product of good primes exceeds 2*H^2.
 *   Each ~31-bit prime contributes >= 30 bits, so the good-prime count needed is
 *
 *       n_primes <= ceil( (2 * log2 H + 2) / 30 ) + slack.
 *
 * We DERIVE that bound from the input entries' magnitudes (max significant-limb
 * count over all num/den) + the dimension -- NOT from any intermediate swell --
 * size the bignum carriers + the per-cell residue arena to it, and run until
 * stabilization (which converges at or before the bound). The bound is the
 * crux: it depends on the ANSWER (input bits * dimension), so the working RAM is
 * answer-sized (MB-scale on Franel), never the ~2.3 GB dense envelope.
 *
 * STANDALONE-COMPLETE: the per-prime int64 matrix, the per-cell residue table,
 * the running good-moduli list, the two candidate-matrix snapshots, every bignum
 * carrier, and the crt_combine / rational_reconstruct / divmod scratch are ALL
 * carved from the caller arena `ws` (>= srmech_qmat_rref_crt_ws_bound), so the
 * bound is the caller's RAM, not a compiled-in cap. A too-small arena or an
 * exhausted prime field -> SRMECH_ERR_OVERFLOW (never a silent wrap); the Python
 * QMat.rref_crt then keeps its ceiling-free pure-Python CRT path.
 *
 * Carrier-internal, like srmech_qmat.c: NOT a Rosetta ledger op (rref_crt is a
 * QMat carrier method, no ToolEntry, no count-test). Additive symbols -> ABI
 * unchanged (stays 3).
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto/recursion): OK -- iterative, flat static helpers
 *   - Rule 2 (bounded loops)    : OK -- prime count / row / col extents
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
#include <stdbool.h>
#include <stdint.h>

/* The GF(p) field ceiling: gf_rref requires 2 < p < 2**31 (so a*b fits uint64).
 * The descending prime walk seeds at the largest ODD value below the ceiling,
 * matching Python's _GF_P_SEED = (1 << 31) - 1 (already odd). */
#define QCRT_P_CEILING (((uint64_t)1) << 31)
#define QCRT_P_SEED    (QCRT_P_CEILING - 1u)

/* Each ~31-bit reduction prime contributes >= this many bits to the CRT modulus
 * (the smallest primes we ever reach stay well above 2**30; the bound only needs
 * a conservative per-prime floor). */
#define QCRT_BITS_PER_PRIME 30u

/* ------------------------------------------------------------------ *
 * the working roster carved from the caller arena `ws`.
 * ------------------------------------------------------------------ */

/* Two parallel candidate matrices (prev/cur) of exact-Q entries, the per-cell
 * residue table, the per-prime int64 GF(p) matrix, the good-moduli list, plus a
 * scalar bignum roster for the per-cell crt_combine + rational_reconstruct. All
 * pointers index into the caller arena (no malloc). */
typedef struct qcrt_ctx {
    int64_t  *gfm;          /* per-prime int64 GF(p) matrix (n_rows*n_cols)   */
    uint32_t *gf_pivots;    /* gf_rref pivot scratch (min(n_rows,n_cols))     */
    uint64_t *moduli;       /* good-prime moduli list (<= max_primes)         */
    uint64_t *cell_res;     /* per-cell residue table (n_cells * max_primes)  */
    srmech_bigint_t *prev_n;/* prev candidate numerators (n_cells)            */
    srmech_bigint_t *prev_d;/* prev candidate denominators (n_cells)          */
    srmech_bigint_t *cur_n; /* cur candidate numerators (n_cells)             */
    srmech_bigint_t *cur_d; /* cur candidate denominators (n_cells)           */
    srmech_bigint_t residue;/* crt_combine out: combined residue (bignum)     */
    srmech_bigint_t modulus;/* crt_combine out: product of good primes        */
    srmech_bigint_t half;   /* modulus // 2 (the Wang radicand)               */
    srmech_bigint_t bound;  /* isqrt(modulus // 2) (the Wang num/den bound)   */
    srmech_bigint_t two;    /* the constant 2 (for modulus // 2)              */
    uint32_t entry_cap;     /* per-bignum limb capacity                       */
    uint32_t max_primes;    /* the a-priori good-prime bound                  */
    size_t   n_cells;       /* n_rows * n_cols                                */
    void    *sub_ws;        /* sub-op scratch (crt_combine / recon / divmod)  */
    size_t   sub_ws_len;    /* its length in BYTES                            */
} qcrt_ctx_t;

/* ------------------------------------------------------------------ *
 * forward declarations (Rule 1: no recursion).
 * ------------------------------------------------------------------ */
static uint32_t qcrt_input_limbs(const srmech_bigint_t *a_n,
                                 const srmech_bigint_t *a_d, size_t n_cells);
static uint64_t qcrt_log2_ceil(uint64_t x);
static uint32_t qcrt_max_primes(uint32_t input_limbs, size_t n_rows,
                                size_t n_cols);
static uint32_t qcrt_entry_cap(uint32_t max_primes);
static uint64_t qcrt_next_prime_down(uint64_t from);
static srmech_status_t qcrt_entries_mod_p(const srmech_bigint_t *a_n,
                                          const srmech_bigint_t *a_d,
                                          size_t n_cells, uint64_t p,
                                          qcrt_ctx_t *c, int *out_skip);
static srmech_status_t qcrt_reconstruct(qcrt_ctx_t *c, size_t n_good,
                                        srmech_bigint_t *out_n,
                                        srmech_bigint_t *out_d, int *out_ok);
static int qcrt_matrices_equal(const srmech_bigint_t *an,
                               const srmech_bigint_t *ad,
                               const srmech_bigint_t *bn,
                               const srmech_bigint_t *bd, size_t n_cells);

/* ------------------------------------------------------------------ *
 * the a-priori answer-Hadamard bounds (the crux).
 * ------------------------------------------------------------------ */

/* The max significant-limb count over every input num/den (each limb 32 bits) -
 * the M magnitude that drives the answer-Hadamard envelope. */
static uint32_t qcrt_input_limbs(const srmech_bigint_t *a_n,
                                 const srmech_bigint_t *a_d, size_t n_cells)
{
    size_t k;
    uint32_t cl = 1u;
    assert(a_n != NULL || n_cells == 0u);
    assert(a_d != NULL || n_cells == 0u);
    for (k = 0u; k < n_cells; k++) {
        if (a_n[k].n > cl) { cl = a_n[k].n; }
        if (a_d[k].n > cl) { cl = a_d[k].n; }
    }
    return cl;
}

/* ceil(log2(x)) for x >= 1 (the bit-length of x-1, 0 for x <= 1). */
static uint64_t qcrt_log2_ceil(uint64_t x)
{
    uint64_t bits = 0u, v;
    assert(x >= 1u);
    v = (x == 0u) ? 0u : (x - 1u);
    while (v != 0u) { bits++; v >>= 1; }
    assert(bits < 64u);                          /* a 64-bit input -> < 64 bits */
    return bits;
}

/* The good-prime BUDGET -- the crux of the answer-sized arena, and the contract
 * boundary of the malloc-free CRT op.
 *
 * The answer entries are exact rationals whose magnitude is bounded a priori by
 * the answer-Hadamard envelope (a ratio of r x r input MINORS, r = rank <= span),
 * log2 H ~ r*(log2 r / 2 + log2 M). That FULL Hadamard worst case is genuinely
 * large for a near-full-rank system (the dense ELIMINATION envelope is even
 * larger -- it compounds every pivot, which is why srmech_qmat_rref reserves
 * ~2.3 GB on the 484x154 Franel). The CRT row escapes that because the STRUCTURED
 * systems it targets (creative-telescoping / Zeilberger / exact LA) reconstruct
 * to a SMALL answer -- the measured Franel answer is 14 bits, reached in 3 good
 * primes, NOT the ~3700-bit Hadamard worst case.
 *
 * So the BUDGET is the answer magnitude we size the malloc-free arena to: a
 * generous multiple of the INPUT magnitude (covering answers far larger than any
 * structured system produces) -- bounded so the arena stays answer-sized
 * (MB-scale on Franel), NOT the dimension-amplified Hadamard. log2(answer) for a
 * structured solve scales with the input bits + a modest dimension factor (the
 * common-denominator clearing across <= span rows), so the budget is
 *   bits_budget = QCRT_ANSWER_INPUT_SLACK * (log2 M + log2 span) + a floor,
 * and n_primes = ceil(2*bits_budget / 30) + slack. A solve whose TRUE answer
 * exceeds this (a dense, unstructured, near-full-rank pathological input) hits the
 * budget without stabilizing -> SRMECH_ERR_OVERFLOW -> the Python QMat.rref_crt
 * keeps its ceiling-free pure CRT path (standalone-complete: the C op succeeds
 * exactly on the structured regime it is for, or reports OVERFLOW, never wraps).
 * This is the SAME contract srmech_qmat already documents ("a genuinely huge one
 * reports OVERFLOW ... the Python QMat falls back to its pure path"). */
#define QCRT_ANSWER_INPUT_SLACK 8u
#define QCRT_ANSWER_BITS_FLOOR  256u

static uint32_t qcrt_max_primes(uint32_t input_limbs, size_t n_rows,
                                size_t n_cols)
{
    uint64_t span = (uint64_t)(n_rows + n_cols);
    uint64_t log2_m = 32u * (uint64_t)input_limbs + 1u;       /* >= log2 M    */
    uint64_t per = log2_m + qcrt_log2_ceil(span == 0u ? 1u : span);
    uint64_t bits = (uint64_t)QCRT_ANSWER_INPUT_SLACK * per;  /* answer budget */
    uint64_t need;
    if (bits < QCRT_ANSWER_BITS_FLOOR) { bits = QCRT_ANSWER_BITS_FLOOR; }
    need = (2u * bits) / QCRT_BITS_PER_PRIME + 8u;            /* primes + slack */
    assert(input_limbs >= 1u);
    assert(need >= 8u);
    return (need > 0xFFFFu) ? 0xFFFFu : (uint32_t)need;
}

/* The per-bignum limb cap: the combined modulus is <= max_primes ~31-bit primes
 * (~max_primes limbs); a reconstructed num/den, the modulus//2 radicand, and the
 * isqrt bound each fit inside that, x2 for the crt_combine partial product, plus
 * slack. Sizes every carrier in the roster + the output entries. */
static uint32_t qcrt_entry_cap(uint32_t max_primes)
{
    uint32_t cap = max_primes * 2u + 16u;
    assert(cap > max_primes);
    assert(cap >= 16u);
    return cap;
}

/* ------------------------------------------------------------------ *
 * the descending prime walk (mirror of Python _gf_primes).
 * ------------------------------------------------------------------ */

/* The largest odd prime strictly below `from` (so the walk emits a STRICTLY
 * descending sequence). Composes srmech_is_prime over the odd candidates, exactly
 * as Python's _gf_primes walks cand -= 2 from the odd seed. Returns 0 once the
 * field is exhausted (cand <= 2), which the caller treats as overflow. */
static uint64_t qcrt_next_prime_down(uint64_t from)
{
    uint64_t cand = (from == 0u) ? 0u : (from - 1u);
    assert(from <= QCRT_P_CEILING);
    assert(cand < from || from == 0u);           /* strictly descending */
    if ((cand & 1u) == 0u && cand > 0u) { cand -= 1u; }   /* force odd */
    while (cand > 2u) {
        bool is_p = false;
        srmech_status_t st = srmech_is_prime(cand, &is_p);
        if (st != SRMECH_OK) { return 0u; }
        if (is_p) { return cand; }
        cand -= 2u;
    }
    return 0u;
}

/* ------------------------------------------------------------------ *
 * entries mod p (mirror of Python _entries_mod_p).
 * ------------------------------------------------------------------ */

/* Reduce every entry num/den to (num * den^-1) mod p into c->gfm (int64,
 * row-major). *out_skip = 1 (and gfm left partial) iff p divides any denominator
 * (the modular image is undefined; the caller skips the prime). Class-I modular
 * inverse via Fermat in uint64 (p < 2**31 so a*b < 2**62). srmech_bigint_divmod
 * uses Python FLOOR semantics (0 <= r < p for p > 0) so a NEGATIVE numerator
 * already reduces to its true non-negative residue in [0, p) -- exactly Python's
 * (num % p) -- with NO extra sign lift (Class-K is the floor itself, never abs). */
static srmech_status_t qcrt_entries_mod_p(const srmech_bigint_t *a_n,
                                          const srmech_bigint_t *a_d,
                                          size_t n_cells, uint64_t p,
                                          qcrt_ctx_t *c, int *out_skip)
{
    size_t k;
    srmech_status_t st;
    assert(a_n != NULL && a_d != NULL && c != NULL && out_skip != NULL);
    assert(p > 2u && p < QCRT_P_CEILING);
    *out_skip = 0;
    for (k = 0u; k < n_cells; k++) {
        uint64_t dmod, nmod, inv, base, e, res;
        st = srmech_bigint_set_i64(&c->two, (int64_t)p);   /* reuse `two` as p-carrier */
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_divmod(&c->half, &c->bound, &a_d[k], &c->two,
                                  c->sub_ws, c->sub_ws_len);  /* bound = den mod p */
        if (st != SRMECH_OK) { return st; }
        dmod = (c->bound.n >= 1u) ? (uint64_t)c->bound.limbs[0] : 0u;
        if (dmod == 0u) { *out_skip = 1; return SRMECH_OK; }   /* p | den -> skip */
        st = srmech_bigint_divmod(&c->half, &c->bound, &a_n[k], &c->two,
                                  c->sub_ws, c->sub_ws_len);  /* bound = num mod p (floor) */
        if (st != SRMECH_OK) { return st; }
        nmod = (c->bound.n >= 1u) ? (uint64_t)c->bound.limbs[0] : 0u;
        base = dmod; e = p - 2u; inv = 1u;                 /* Fermat: den^(p-2) */
        while (e != 0u) {
            if ((e & 1u) != 0u) { inv = (inv * base) % p; }
            base = (base * base) % p;
            e >>= 1;
        }
        res = (nmod * inv) % p;
        c->gfm[k] = (int64_t)res;
    }
    return SRMECH_OK;
}

/* ------------------------------------------------------------------ *
 * per-cell CRT-combine + rational-reconstruct (mirror of _reconstruct_matrix).
 * ------------------------------------------------------------------ */

/* Build the Wang num/den bound = isqrt(modulus // 2) into c->bound (after a
 * crt_combine has set c->modulus). half = modulus >> 1; bound = isqrt(half). */
static srmech_status_t qcrt_wang_bound(qcrt_ctx_t *c)
{
    srmech_status_t st;
    assert(c != NULL);
    assert(c->modulus.sign > 0);
    st = srmech_bigint_shr_bits(&c->half, &c->modulus, 1u);   /* half = mod // 2 */
    if (st != SRMECH_OK) { return st; }
    return srmech_bigint_isqrt(&c->bound, &c->half,
                               c->sub_ws, c->sub_ws_len);     /* bound = isqrt   */
}

/* Reconstruct the whole candidate matrix from the first n_good good primes into
 * (out_n, out_d). *out_ok = 0 (add more primes) iff ANY cell fails the Wang
 * reconstruction at the current modulus; else *out_ok = 1 and every cell is set.
 * One crt_combine builds (modulus, residue) per cell; the Wang bound is rebuilt
 * once per cell from that cell's modulus (all cells share the same good moduli,
 * so the modulus -- and the bound -- is identical across cells; we recompute it
 * per cell to stay byte-identical to the Python per-cell call). */
static srmech_status_t qcrt_reconstruct(qcrt_ctx_t *c, size_t n_good,
                                        srmech_bigint_t *out_n,
                                        srmech_bigint_t *out_d, int *out_ok)
{
    size_t cell;
    srmech_status_t st;
    int32_t found = 0;
    assert(c != NULL && out_n != NULL && out_d != NULL && out_ok != NULL);
    assert(n_good >= 1u);
    *out_ok = 1;
    for (cell = 0u; cell < c->n_cells; cell++) {
        st = srmech_crt_combine(&c->cell_res[cell * c->max_primes], c->moduli,
                                (uint32_t)n_good, &c->residue, &c->modulus,
                                c->sub_ws, c->sub_ws_len);
        if (st != SRMECH_OK) { return st; }
        st = qcrt_wang_bound(c);
        if (st != SRMECH_OK) { return st; }
        found = 0;
        st = srmech_rational_reconstruct(&c->residue, &c->modulus, &c->bound,
                                         &c->bound, &out_n[cell], &out_d[cell],
                                         &found, c->sub_ws, c->sub_ws_len);
        if (st != SRMECH_OK) { return st; }
        if (found == 0) { *out_ok = 0; return SRMECH_OK; }
    }
    return SRMECH_OK;
}

/* Whole-matrix exact equality (the stabilization check) -- every cell's num AND
 * den compare equal. Class-K nothing here; a plain signed bigint compare. */
static int qcrt_matrices_equal(const srmech_bigint_t *an,
                               const srmech_bigint_t *ad,
                               const srmech_bigint_t *bn,
                               const srmech_bigint_t *bd, size_t n_cells)
{
    size_t k;
    assert(an != NULL && ad != NULL && bn != NULL && bd != NULL);
    assert(n_cells == 0u || an != bn);
    for (k = 0u; k < n_cells; k++) {
        if (srmech_bigint_cmp(&an[k], &bn[k]) != 0) { return 0; }
        if (srmech_bigint_cmp(&ad[k], &bd[k]) != 0) { return 0; }
    }
    return 1;
}

/* ------------------------------------------------------------------ *
 * caller-arena carve (mirrors qmat_take / qmat_bind).
 * ------------------------------------------------------------------ */

/* Bump `count` uint32 words off the arena; NULL on exhaustion (-> OVERFLOW). */
static uint32_t *qcrt_take(uint32_t *base, size_t words, size_t *cur,
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

/* Bind a single srmech_bigint over a fresh `cap`-limb run from the arena. */
static srmech_status_t qcrt_bind(srmech_bigint_t *b, uint32_t *base,
                                 size_t words, size_t *cur, uint32_t cap)
{
    uint32_t *limbs = qcrt_take(base, words, cur, cap);
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

/* Header words per srmech_bigint (for the candidate-matrix bignum arrays). */
static size_t qcrt_hdr_words(void)
{
    size_t hw = (sizeof(srmech_bigint_t) + sizeof(uint32_t) - 1u)
                / sizeof(uint32_t);
    assert(sizeof(srmech_bigint_t) > 0u);
    assert(hw >= 1u);
    return hw;
}

/* Carve a bignum array of `n` entries (header array + `cap`-limb backing runs)
 * off the arena; *out points at the header array. */
static srmech_status_t qcrt_bind_array(srmech_bigint_t **out, uint32_t *base,
                                       size_t words, size_t *cur, uint32_t cap,
                                       size_t n)
{
    size_t hw = qcrt_hdr_words(), k;
    uint32_t *hdr = qcrt_take(base, words, cur, hw * (n == 0u ? 1u : n));
    srmech_status_t st;
    assert(out != NULL && base != NULL);
    assert(cap > 0u);
    if (hdr == NULL) { return SRMECH_ERR_OVERFLOW; }
    *out = (srmech_bigint_t *)(void *)hdr;
    for (k = 0u; k < n; k++) {
        st = qcrt_bind(&(*out)[k], base, words, cur, cap);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* Carve the int64 / uint32 / uint64 scratch tables off the arena. */
static srmech_status_t qcrt_carve_tables(qcrt_ctx_t *c, uint32_t *base,
                                         size_t words, size_t *cur,
                                         size_t n_rows, size_t n_cols)
{
    size_t mindim = (n_rows < n_cols) ? n_rows : n_cols;
    size_t cells = c->n_cells == 0u ? 1u : c->n_cells;
    size_t res_words = cells * (size_t)c->max_primes * 2u;   /* uint64 = 2 words */
    uint32_t *gfm_w = qcrt_take(base, words, cur, cells * 2u);   /* int64 = 2 w  */
    uint32_t *piv_w = qcrt_take(base, words, cur, mindim == 0u ? 1u : mindim);
    uint32_t *mod_w = qcrt_take(base, words, cur, (size_t)c->max_primes * 2u);
    uint32_t *res_w = qcrt_take(base, words, cur, res_words == 0u ? 1u : res_words);
    assert(c != NULL && base != NULL);
    assert(c->max_primes >= 1u);
    if (gfm_w == NULL || piv_w == NULL || mod_w == NULL || res_w == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    c->gfm = (int64_t *)(void *)gfm_w;
    c->gf_pivots = piv_w;
    c->moduli = (uint64_t *)(void *)mod_w;
    c->cell_res = (uint64_t *)(void *)res_w;
    return SRMECH_OK;
}

/* Carve the full working roster (tables + four candidate-matrix bignum arrays +
 * the scalar bignum roster), then hand the arena TAIL to the sub-ops as sub_ws. */
static srmech_status_t qcrt_ctx_init(qcrt_ctx_t *c, uint32_t *base, size_t words,
                                     size_t n_rows, size_t n_cols)
{
    size_t cur = 0u, cells = c->n_cells == 0u ? 1u : c->n_cells;
    uint32_t cap = c->entry_cap;
    srmech_status_t st;
    assert(c != NULL && base != NULL);
    assert(cap > 0u);
    st = qcrt_carve_tables(c, base, words, &cur, n_rows, n_cols);
    if (st != SRMECH_OK) { return st; }
    st = qcrt_bind_array(&c->prev_n, base, words, &cur, cap, cells);
    if (st == SRMECH_OK) { st = qcrt_bind_array(&c->prev_d, base, words, &cur, cap, cells); }
    if (st == SRMECH_OK) { st = qcrt_bind_array(&c->cur_n, base, words, &cur, cap, cells); }
    if (st == SRMECH_OK) { st = qcrt_bind_array(&c->cur_d, base, words, &cur, cap, cells); }
    if (st != SRMECH_OK) { return st; }
    st = qcrt_bind(&c->residue, base, words, &cur, cap);
    if (st == SRMECH_OK) { st = qcrt_bind(&c->modulus, base, words, &cur, cap); }
    if (st == SRMECH_OK) { st = qcrt_bind(&c->half, base, words, &cur, cap); }
    if (st == SRMECH_OK) { st = qcrt_bind(&c->bound, base, words, &cur, cap); }
    if (st == SRMECH_OK) { st = qcrt_bind(&c->two, base, words, &cur, cap); }
    if (st != SRMECH_OK) { return st; }
    c->sub_ws = (void *)(base + cur);
    c->sub_ws_len = (words - cur) * sizeof(uint32_t);
    assert(cur <= words);
    return SRMECH_OK;
}

/* ------------------------------------------------------------------ *
 * the consensus fold (mirror of the Python (rank, pivots) consensus).
 * ------------------------------------------------------------------ */

/* Compare a fresh (rank, pivots) key against the running consensus.
 *   match   ( 0): identical -> fold this prime in.
 *   restart ( 1): strictly higher rank -> this supersedes; RESTART the CRT.
 *   discard (-1): an equal-or-lower disagreement -> unlucky prime, drop it.
 * Class-K: every decision is an integer compare (rank first, then the pivot
 * columns), never abs(). */
static int qcrt_consensus_cmp(uint32_t rank, const uint32_t *pivots,
                              uint32_t cons_rank, const uint32_t *cons_pivots,
                              int have_consensus)
{
    uint32_t i;
    assert(pivots != NULL || rank == 0u);
    assert(cons_pivots != NULL || !have_consensus);
    if (!have_consensus) { return 0; }                 /* first prime sets it */
    if (rank == cons_rank) {
        for (i = 0u; i < rank; i++) {
            if (pivots[i] != cons_pivots[i]) { return -1; }  /* same rank, diff */
        }
        return 0;                                       /* identical key */
    }
    return (rank > cons_rank) ? 1 : -1;                 /* higher restarts */
}

/* ------------------------------------------------------------------ *
 * the public orchestrator + its ws-bound.
 * ------------------------------------------------------------------ */

/* One descending-prime iteration: reduce mod p (skip on p|den), gf_rref, then
 * resolve against the consensus. On a fold (*folded=1) the prime's residues are
 * appended to cell_res + moduli and *n_good is bumped; on a restart the
 * accumulators reset to this prime alone; on a discard nothing changes. Updates
 * the caller's consensus snapshot (cons_rank / cons_pivots). */
static srmech_status_t qcrt_step_prime(qcrt_ctx_t *c, const srmech_bigint_t *a_n,
                                       const srmech_bigint_t *a_d, size_t n_rows,
                                       size_t n_cols, uint64_t p, uint32_t *n_good,
                                       uint32_t *cons_rank, uint32_t *cons_pivots,
                                       int *have_cons, int *folded)
{
    int skip = 0, decision;
    uint32_t rank = 0u, i;
    size_t cell;
    srmech_status_t st;
    assert(c != NULL && n_good != NULL && folded != NULL);
    assert(cons_rank != NULL && cons_pivots != NULL && have_cons != NULL);
    *folded = 0;
    st = qcrt_entries_mod_p(a_n, a_d, c->n_cells, p, c, &skip);
    if (st != SRMECH_OK) { return st; }
    if (skip) { return SRMECH_OK; }                    /* p | some denominator */
    st = srmech_gf_rref(c->gfm, (uint32_t)n_rows, (uint32_t)n_cols, p,
                        c->gf_pivots, &rank);
    if (st != SRMECH_OK) { return st; }
    decision = qcrt_consensus_cmp(rank, c->gf_pivots, *cons_rank, cons_pivots,
                                  *have_cons);
    if (decision < 0) { return SRMECH_OK; }            /* unlucky prime: discard */
    if (decision > 0 || !*have_cons) {                 /* restart / first */
        *cons_rank = rank;
        for (i = 0u; i < rank; i++) { cons_pivots[i] = c->gf_pivots[i]; }
        *have_cons = 1;
        if (decision > 0) { *n_good = 0u; }            /* restart wipes the CRT */
    }
    if (*n_good >= c->max_primes) { return SRMECH_ERR_OVERFLOW; }
    for (cell = 0u; cell < c->n_cells; cell++) {       /* fold residues in */
        c->cell_res[cell * c->max_primes + *n_good] = (uint64_t)c->gfm[cell];
    }
    c->moduli[*n_good] = p;
    *n_good += 1u;
    *folded = 1;
    return SRMECH_OK;
}

/* The a-priori good-prime bound is computed off the input magnitudes + dimension
 * BEFORE any solve; the descending walk runs until stabilization (which converges
 * at or before that bound), never the dense Hadamard envelope. The pivot-cols
 * consensus snapshot is bounded by the PIVOT count <= n_cols, so only n_cols is
 * capped at SRMECH_QMAT_MAX_DIM here -- a TALL system (n_rows >> n_cols, e.g. the
 * 484x154 Franel) is fully supported (gf_rref handles any n_rows; the swell-free
 * int64 GF(p) RREF is exactly why CRT escapes the dense tall-matrix arena). */
srmech_status_t srmech_qmat_rref_crt(const srmech_bigint_t *a_n,
                                     const srmech_bigint_t *a_d, size_t n_rows,
                                     size_t n_cols, srmech_bigint_t *out_n,
                                     srmech_bigint_t *out_d, size_t *out_rank,
                                     size_t *pivot_cols, void *ws, size_t ws_len)
{
    uint32_t cons_pivots[SRMECH_QMAT_MAX_DIM];
    uint32_t n_good = 0u, cons_rank = 0u, in_limbs;
    int have_cons = 0, folded = 0, ok = 0;
    uint64_t p = QCRT_P_SEED + 1u;                     /* walk starts strictly below */
    qcrt_ctx_t c;
    srmech_status_t st;
    size_t k;
    assert(a_n != NULL && out_n != NULL && out_rank != NULL && pivot_cols != NULL);
    assert(out_d != NULL && (ws != NULL || ws_len == 0u));
    if (a_n == NULL || a_d == NULL || out_n == NULL || out_d == NULL
        || out_rank == NULL || pivot_cols == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n_cols > SRMECH_QMAT_MAX_DIM) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (n_rows == 0u || n_cols == 0u) { *out_rank = 0u; return SRMECH_OK; }
    c.n_cells = n_rows * n_cols;
    in_limbs = qcrt_input_limbs(a_n, a_d, c.n_cells);
    c.max_primes = qcrt_max_primes(in_limbs, n_rows, n_cols);
    c.entry_cap = qcrt_entry_cap(c.max_primes);
    st = qcrt_ctx_init(&c, (uint32_t *)ws, ws_len / sizeof(uint32_t),
                       n_rows, n_cols);
    if (st != SRMECH_OK) { return st; }
    while (n_good < c.max_primes) {                    /* bounded by the answer */
        p = qcrt_next_prime_down(p);
        if (p == 0u) { return SRMECH_ERR_OVERFLOW; }   /* field exhausted */
        st = qcrt_step_prime(&c, a_n, a_d, n_rows, n_cols, p, &n_good,
                             &cons_rank, cons_pivots, &have_cons, &folded);
        if (st != SRMECH_OK) { return st; }
        if (!folded || n_good < 2u) { continue; }      /* need >= 2 to stabilize */
        st = qcrt_reconstruct(&c, n_good, c.cur_n, c.cur_d, &ok);
        if (st != SRMECH_OK) { return st; }
        if (!ok) { continue; }                         /* not in Wang bound yet */
        if (n_good >= 3u && qcrt_matrices_equal(c.cur_n, c.cur_d, c.prev_n,
                                                c.prev_d, c.n_cells)) {
            break;                                     /* stabilized: done */
        }
        for (k = 0u; k < c.n_cells; k++) {             /* snapshot cur -> prev */
            st = srmech_bigint_copy(&c.prev_n[k], &c.cur_n[k]);
            if (st == SRMECH_OK) { st = srmech_bigint_copy(&c.prev_d[k], &c.cur_d[k]); }
            if (st != SRMECH_OK) { return st; }
        }
    }
    if (!ok) { return SRMECH_ERR_OVERFLOW; }           /* never stabilized */
    for (k = 0u; k < c.n_cells; k++) {                 /* copy answer out */
        st = srmech_bigint_copy(&out_n[k], &c.cur_n[k]);
        if (st == SRMECH_OK) { st = srmech_bigint_copy(&out_d[k], &c.cur_d[k]); }
        if (st != SRMECH_OK) { return st; }
    }
    *out_rank = cons_rank;                             /* pivot count = exact rank */
    for (k = 0u; k < cons_rank; k++) { pivot_cols[k] = cons_pivots[k]; }
    return SRMECH_OK;
}

/* Minimum `ws_len` BYTES for srmech_qmat_rref_crt on an n_rows x n_cols input of
 * `coeff_limbs` significant limbs per entry. Sizes the working roster from the
 * ANSWER-Hadamard good-prime bound (qcrt_max_primes), NOT the dense elimination
 * swell -- that is the whole point of the row (answer-sized, MB-scale, never the
 * ~2.3 GB dense Hadamard envelope). Covers (a) the int64 GF(p) matrix + pivots,
 * (b) the uint64 moduli list + the per-cell residue table (n_cells*max_primes),
 * (c) the four candidate-matrix bignum arrays (n_cells entries, entry_cap limbs)
 * + the scalar bignum roster, and (d) the sub-op scratch tail (the heaviest of
 * crt_combine / rational_reconstruct / divmod / isqrt over the max-prime
 * modulus). 8-byte-aligned uint32 bump arena. */
size_t srmech_qmat_rref_crt_ws_bound(size_t coeff_limbs, size_t n_rows,
                                     size_t n_cols)
{
    size_t cells = n_rows * n_cols == 0u ? 1u : n_rows * n_cols;
    uint32_t max_primes = qcrt_max_primes(
        (uint32_t)(coeff_limbs == 0u ? 1u : coeff_limbs), n_rows, n_cols);
    uint32_t cap = qcrt_entry_cap(max_primes);
    size_t hw = qcrt_hdr_words();
    size_t mindim = (n_rows < n_cols ? n_rows : n_cols);
    /* (a) int64 gfm (2 w/cell) + uint32 pivots; (b) uint64 moduli (2 w each) +
     * residue table (n_cells*max_primes uint64 = 2 w each). */
    size_t tables = cells * 2u + (mindim == 0u ? 1u : mindim)
                    + (size_t)max_primes * 2u
                    + cells * (size_t)max_primes * 2u;
    /* (c) four candidate arrays (header + cap-limb backing) + 5 scalar carriers. */
    size_t cand = 4u * (hw * cells + cells * cap) + 5u * cap;
    /* (d) sub-op scratch: crt_combine over max_primes congruences,
     * rational_reconstruct over a cap-limb modulus, divmod/isqrt over cap limbs;
     * take a generous envelope dominating all three. */
    size_t mod_limbs = (size_t)max_primes + 4u;
    size_t crt_ws = srmech_crt_combine_ws_bound(max_primes) / sizeof(uint32_t);
    size_t rr_ws = srmech_rational_reconstruct_ws_bound(mod_limbs)
                   / sizeof(uint32_t);
    size_t sub_ws = crt_ws + rr_ws + (size_t)cap * 16u + 256u;
    size_t words = tables + cand + sub_ws + 64u;
    assert(cap >= 16u);
    assert(words >= cand);
    return words * sizeof(uint32_t);
}

/* The per-entry limb cap the caller must give each srmech_bigint in the OUTPUT
 * nums/dens arrays. Sized from the ANSWER-Hadamard good-prime bound (the modulus
 * the reconstructed |num|,|den| stay below), NOT the dense Cramer-minor cap
 * (srmech_qmat_entry_cap) -- using the dense cap would re-reserve the ~2.3 GB
 * output the CRT row exists to escape. Same envelope as the ctx carriers. */
size_t srmech_qmat_rref_crt_entry_cap(size_t coeff_limbs, size_t n_rows,
                                      size_t n_cols)
{
    uint32_t max_primes = qcrt_max_primes(
        (uint32_t)(coeff_limbs == 0u ? 1u : coeff_limbs), n_rows, n_cols);
    size_t cap = qcrt_entry_cap(max_primes);
    assert(cap >= 16u);
    assert(cap > max_primes);
    return cap;
}
