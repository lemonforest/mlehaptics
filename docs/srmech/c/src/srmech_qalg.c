/*
 * srmech_qalg.c — EXACT algebraic-number linear algebra: the Qalg NUMBER-FIELD
 * carrier (ℚ[x]/(m)) + the exact EIGENVECTOR null space of A − λI over ℚ(λ)
 * (the C peer of srmech.amsc.cascade.matrix_cascades.eigvec_exact /
 * eigvec_exact_float; Qalg TAIL Batch 7a).
 *
 * An algebraic eigenvalue λ is a root of an IRREDUCIBLE monic integer polynomial
 * m of degree d, so ℚ(λ) = ℚ[x]/(m) is a FIELD; each field element is a degree-<d
 * polynomial with exact-rational coefficients (num/den srmech_bigint pairs). The
 * eigenvector is the null space of M = A − λI over that field, read off the exact
 * REDUCED ROW ECHELON form: pivot on the first nonzero Qalg entry at/below the
 * current row, normalise by the pivot's Qalg INVERSE (extended Euclid on ℚ[x]),
 * clear every other row, then each free column gives one null-space basis vector
 * (v[fc]=1, pivot vars = −M[pivot row][fc]). This is byte/structurally-identical to
 * the pure _eigvec_exact_qalg: the RREF is canonical (unique), so the same reduced
 * ℚ(λ) coordinates come out.
 *
 * The Qalg field arithmetic COMPOSES the exact-ℚ srmech_poly_* kernels:
 *   add / sub : coefficientwise exact-Q (srmech_poly_add / srmech_poly_sub);
 *   mul       : polynomial convolution (srmech_poly_mul) then REDUCE mod m
 *               (srmech_poly_divmod remainder — the monic relation
 *               αⁿ = −Σ_{i<d} m[i]αⁱ done as exact long division);
 *   inverse   : the extended Euclidean algorithm on the coordinate polynomial
 *               b(x) and m(x) in ℚ[x] (u·b + v·m = g, g a nonzero constant since
 *               m is irreducible and b ≠ 0), so b⁻¹ = (u / g) reduced mod m —
 *               built from srmech_poly_divmod / _mul / _sub, cofactor-tracked.
 *
 * All arithmetic is exact ℚ over srmech_bigint (NO malloc, JPL Rule 3): every
 * working carrier + the Qalg matrix + the poly-op scratch is carved from the
 * caller arena `ws` (>= srmech_eigvec_exact_ws_bound), so the magnitude bound is
 * the CALLER's RAM. Any residual overflow returns SRMECH_ERR_OVERFLOW (never a
 * silent wrap), and the Python eigvec_exact falls back to its byte-identical
 * pure-ℚ path (the parity oracle) — so the standalone-complete honor holds. A
 * REDUCIBLE m (ℚ[x]/(m) not a field: a zero-divisor pivot with no inverse) returns
 * SRMECH_ERR_BAD_INPUT, and the caller raises the same ValueError from the pure
 * path.
 *
 * Carrier-internal, like srmech_poly.c / srmech_qmat.c for the field arithmetic;
 * srmech_eigvec_exact IS the Rosetta peer of eigvec_exact / eigvec_exact_float.
 * Additive symbols -> SRMECH_ABI_VERSION unchanged (stays 3).
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto/recursion): OK — iterative, flat helpers
 *   - Rule 2 (bounded loops)    : OK — bounds are dimension / degree counts
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

/* n and deg are both bounded (a stack permutation / pivot roster, Rule 2). */
#define QALG_MAX_DIM 256

/* The working roster carved from the caller arena `ws`. Each `*_n`/`*_d` pair is
 * a coefficient array (SB slots wide unless noted); M is the n·n Qalg matrix,
 * each entry a `deg`-coefficient run. mm is the modulus poly (den == 1). */
typedef struct qalg_eng {
    int deg;                 /* field degree = deg(m)                     */
    int n;                   /* matrix dimension                          */
    uint32_t cap;            /* per-coefficient limb capacity             */
    size_t sb;               /* small-buffer coefficient slots (2*deg+2)  */
    srmech_bigint_t *mn, *md;      /* modulus poly m (deg+1, den 1)       */
    srmech_bigint_t *lamn, *lamd;  /* λ coords (deg)                      */
    srmech_bigint_t *Mn, *Md;      /* the n·n·deg Qalg matrix              */
    /* field-op scratch (SB-wide) */
    srmech_bigint_t *cvn, *cvd;    /* convolution                         */
    srmech_bigint_t *rqn, *rqd;    /* reduce/divmod quotient sink         */
    srmech_bigint_t *rrn, *rrd;    /* reduce/divmod remainder sink        */
    srmech_bigint_t *asn, *asd;    /* add/sub poly output                 */
    /* extended-Euclid inverse scratch (SB-wide) */
    srmech_bigint_t *e0n, *e0d, *e1n, *e1d;   /* r0, r1                    */
    srmech_bigint_t *w0n, *w0d, *w1n, *w1d;   /* u0, u1                    */
    srmech_bigint_t *eqn, *eqd, *ern, *erd;   /* quot, rem                 */
    srmech_bigint_t *gun, *gud, *nun, *nud;   /* quot·u1, new u            */
    srmech_bigint_t *rcn, *rcd;               /* reciprocal 1/g0           */
    srmech_bigint_t *ipn, *ipd;               /* inverse product          */
    /* deg-wide Qalg element temporaries */
    srmech_bigint_t *invn, *invd;  /* pivot inverse                       */
    srmech_bigint_t *tmn, *tmd;    /* row-scale product                   */
    srmech_bigint_t *fen, *fed;    /* elimination factor                  */
    srmech_bigint_t *pen, *ped;    /* elimination product                 */
    srmech_bigint_t *den_, *ded;   /* elimination difference              */
    /* JORDAN-CHAIN matrix buffers (carved only by qalg_jordan_carve; the
     * eigvec path leaves them NULL). All n·n·deg cells unless noted. */
    int powcap;              /* stored-powers slot count (= n + 2)         */
    int cn_cols;             /* column-rank scratch width (= 2n + 1)       */
    srmech_bigint_t *Nn, *Nd;      /* base N = A − λI                      */
    srmech_bigint_t *tn, *td;      /* matmul product / power accumulator   */
    srmech_bigint_t *sn, *sd;      /* RREF scratch (destructible copy)     */
    srmech_bigint_t *lon, *lod;    /* lower null basis (≤ n vecs of n·deg) */
    srmech_bigint_t *can, *cad;    /* candidate null basis                 */
    srmech_bigint_t *cn, *cd;      /* column-rank scratch (n·(2n+1)·deg)   */
    srmech_bigint_t *pwn, *pwd;    /* powers[0..powcap-1] (powcap·n·n·deg) */
    srmech_bigint_t *van, *vad;    /* matvec temp vector (n·deg)           */
    srmech_bigint_t *jp0n, *jp0d;  /* field product temp (deg)             */
    srmech_bigint_t *jp1n, *jp1d;  /* field add temp (deg)                 */
    void  *pws;              /* srmech_poly_* scratch arena               */
    size_t pws_len;          /* its length in BYTES                       */
} qalg_eng_t;

/* Jordan-chain dimension cap: an exact-symbolic DEFECTIVE matrix is small in
 * practice; the Python wrapper caps the native path well below this and falls
 * to the byte-identical pure path above it. */
#define QALG_JORDAN_MAX_DIM 64

/* ---- forward declarations (Rule 1: no recursion) ------------------- */

static uint32_t *qalg_take(uint32_t *base, size_t words, size_t *cur,
                           size_t count);
static srmech_bigint_t *qalg_carve(uint32_t *base, size_t words, size_t *cur,
                                   size_t count, uint32_t cap, int *ok);
static size_t qalg_cap_for(size_t coeff_limbs, int n, int deg);
static size_t qalg_input_limbs(const srmech_bigint_t *arr, size_t n);
static size_t qalg_trim(const srmech_bigint_t *nums, size_t n);
static srmech_status_t qalg_copy_run(srmech_bigint_t *dn, srmech_bigint_t *dd,
                                     const srmech_bigint_t *sn,
                                     const srmech_bigint_t *sd, size_t len);
static srmech_status_t qalg_set_scalar(srmech_bigint_t *on, srmech_bigint_t *od,
                                       int deg, const srmech_bigint_t *num,
                                       const srmech_bigint_t *den);
static srmech_status_t qalg_zero_elem(srmech_bigint_t *on, srmech_bigint_t *od,
                                      int deg);
static int qalg_is_zero_elem(const srmech_bigint_t *on, int deg);
static srmech_status_t qalg_pad_into(srmech_bigint_t *on, srmech_bigint_t *od,
                                     const srmech_bigint_t *sn,
                                     const srmech_bigint_t *sd, size_t slen,
                                     int deg);
static srmech_status_t qalg_field_mul(qalg_eng_t *e, srmech_bigint_t *on,
                                      srmech_bigint_t *od,
                                      const srmech_bigint_t *an,
                                      const srmech_bigint_t *ad,
                                      const srmech_bigint_t *bn,
                                      const srmech_bigint_t *bd);
static srmech_status_t qalg_field_sub(qalg_eng_t *e, srmech_bigint_t *on,
                                      srmech_bigint_t *od,
                                      const srmech_bigint_t *an,
                                      const srmech_bigint_t *ad,
                                      const srmech_bigint_t *bn,
                                      const srmech_bigint_t *bd);
static srmech_status_t qalg_field_inverse(qalg_eng_t *e, srmech_bigint_t *on,
                                          srmech_bigint_t *od,
                                          const srmech_bigint_t *an,
                                          const srmech_bigint_t *ad);
static srmech_status_t qalg_eng_carve(qalg_eng_t *e, void *ws, size_t ws_len);
static srmech_status_t qalg_build_matrix(qalg_eng_t *e,
                                         const srmech_bigint_t *a_n,
                                         const srmech_bigint_t *a_d);
static srmech_status_t qalg_rref(qalg_eng_t *e, int *row_perm,
                                 int *piv_row_of_col, int *is_pivot);
static srmech_status_t qalg_extract(qalg_eng_t *e, const int *row_perm,
                                    const int *piv_row_of_col,
                                    const int *is_pivot,
                                    srmech_bigint_t *out_n,
                                    srmech_bigint_t *out_d, int *out_k);
/* ---- jordan-chain helpers (Qalg TAIL Batch 7b) --------------------- */
static srmech_status_t qalg_field_add(qalg_eng_t *e, srmech_bigint_t *on,
                                      srmech_bigint_t *od,
                                      const srmech_bigint_t *an,
                                      const srmech_bigint_t *ad,
                                      const srmech_bigint_t *bn,
                                      const srmech_bigint_t *bd);
static srmech_status_t qalg_gmatmul(qalg_eng_t *e, srmech_bigint_t *on,
                                    srmech_bigint_t *od,
                                    const srmech_bigint_t *an,
                                    const srmech_bigint_t *ad,
                                    const srmech_bigint_t *bn,
                                    const srmech_bigint_t *bd, int n);
static srmech_status_t qalg_gmatvec(qalg_eng_t *e, srmech_bigint_t *on,
                                    srmech_bigint_t *od,
                                    const srmech_bigint_t *mn,
                                    const srmech_bigint_t *md,
                                    const srmech_bigint_t *vn,
                                    const srmech_bigint_t *vd, int n);
static srmech_status_t qalg_geliminate(qalg_eng_t *e, srmech_bigint_t *mn,
                                       srmech_bigint_t *md, int nr, int nc,
                                       const int *row_perm, int r, int c,
                                       int pr);
static srmech_status_t qalg_grref(qalg_eng_t *e, srmech_bigint_t *mn,
                                  srmech_bigint_t *md, int nr, int nc,
                                  int *row_perm, int *piv_row_of_col,
                                  int *is_pivot, int *out_rank);
static srmech_status_t qalg_gnullspace(qalg_eng_t *e, const srmech_bigint_t *mn,
                                       const srmech_bigint_t *md, int n,
                                       const int *rp, const int *pc,
                                       const int *ip, srmech_bigint_t *out_n,
                                       srmech_bigint_t *out_d, int *out_k);
static srmech_status_t qalg_rank_of(qalg_eng_t *e, const srmech_bigint_t *mn,
                                    const srmech_bigint_t *md, int n,
                                    int *rank, int *rp, int *pc, int *ip);
static srmech_status_t qalg_nullspace_of(qalg_eng_t *e,
                                         const srmech_bigint_t *mn,
                                         const srmech_bigint_t *md, int n,
                                         srmech_bigint_t *out_n,
                                         srmech_bigint_t *out_d, int *out_k,
                                         int *rp, int *pc, int *ip);
static srmech_status_t qalg_set_identity(qalg_eng_t *e, srmech_bigint_t *mn,
                                         srmech_bigint_t *md, int n);
static srmech_status_t qalg_fill_col(qalg_eng_t *e, int K, int col,
                                     const srmech_bigint_t *vn,
                                     const srmech_bigint_t *vd, int n);
static srmech_status_t qalg_build_context(qalg_eng_t *e, int K, int lk,
                                          const srmech_bigint_t *out_n,
                                          const srmech_bigint_t *out_d, int vi,
                                          const srmech_bigint_t *cvn,
                                          const srmech_bigint_t *cvd, int n);
static srmech_status_t qalg_col_rank(qalg_eng_t *e, int K, int *rank,
                                     int *rp, int *pc, int *ip);
static srmech_status_t qalg_cand_independent(qalg_eng_t *e,
                                             const srmech_bigint_t *cvn,
                                             const srmech_bigint_t *cvd, int lk,
                                             const srmech_bigint_t *out_n,
                                             const srmech_bigint_t *out_d,
                                             int vi, int *out_indep,
                                             int *rp, int *pc, int *ip);
static srmech_status_t qalg_build_chain(qalg_eng_t *e, srmech_bigint_t *out_n,
                                        srmech_bigint_t *out_d, int vi,
                                        const srmech_bigint_t *candn,
                                        const srmech_bigint_t *candd,
                                        int s, int n);
static srmech_status_t qalg_jordan_powers(qalg_eng_t *e, int *ranks, int *nul,
                                          int *out_p, int *rp, int *pc,
                                          int *ip);
static void qalg_block_counts(const int *ranks, int p, int *nblocks);
static srmech_status_t qalg_topdown_s(qalg_eng_t *e, int s, int need,
                                      srmech_bigint_t *out_n,
                                      srmech_bigint_t *out_d, int *out_bs,
                                      int *vi, int *nc, int *rp, int *pc,
                                      int *ip);
static srmech_status_t qalg_jordan_carve(qalg_eng_t *e, void *ws,
                                         size_t ws_len);
static srmech_status_t qalg_jordan_prepare(qalg_eng_t *e,
                                           const srmech_bigint_t *a_n,
                                           const srmech_bigint_t *a_d, int n,
                                           const srmech_bigint_t *m, int deg,
                                           const srmech_bigint_t *lam_n,
                                           const srmech_bigint_t *lam_d,
                                           void *ws, size_t ws_len);

/* ---- caller-arena carve -------------------------------------------- */

static uint32_t *qalg_take(uint32_t *base, size_t words, size_t *cur,
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

/* Carve `count` srmech_bigint headers + their `cap`-limb runs from the arena,
 * each initialised to the integer 0 (n == 0, sign == 0). Returns the header
 * array, or NULL (with *ok cleared) on arena exhaustion. */
static srmech_bigint_t *qalg_carve(uint32_t *base, size_t words, size_t *cur,
                                   size_t count, uint32_t cap, int *ok)
{
    size_t hdr_words = (sizeof(srmech_bigint_t) + sizeof(uint32_t) - 1u)
                       / sizeof(uint32_t);
    uint32_t *h;
    srmech_bigint_t *arr;
    size_t k;
    assert(base != NULL && cur != NULL && ok != NULL);
    assert(cap > 0u && count > 0u);
    h = qalg_take(base, words, cur, hdr_words * count);
    if (h == NULL) { *ok = 0; return NULL; }
    arr = (srmech_bigint_t *)(void *)h;
    for (k = 0u; k < count; k++) {
        uint32_t *limbs = qalg_take(base, words, cur, cap);
        if (limbs == NULL) { *ok = 0; return NULL; }
        arr[k].limbs = limbs;
        arr[k].cap = cap;
        arr[k].n = 0u;
        arr[k].sign = 0;
    }
    return arr;
}

/* Per-coefficient limb capacity: generous headroom for the number-field RREF
 * growth (each entry a ratio of ℚ(α)-minors). `coeff_limbs` is the largest
 * significant limb count of any input coefficient. Overflow past this -> a clean
 * SRMECH_ERR_OVERFLOW + the pure-ℚ fallback, so generosity only trades RAM. */
static size_t qalg_cap_for(size_t coeff_limbs, int n, int deg)
{
    size_t cl = (coeff_limbs == 0u) ? 1u : coeff_limbs;
    size_t span = (size_t)n + (size_t)deg + 4u;
    size_t cap = (cl + 2u) * span * ((size_t)deg + 2u) * 2u + 64u;
    assert(cap >= cl);
    assert(cap >= 64u);
    return cap;
}

/* The largest significant limb count over `n` srmech_bigint. */
static size_t qalg_input_limbs(const srmech_bigint_t *arr, size_t n)
{
    size_t k, cl = 1u;
    assert(arr != NULL || n == 0u);
    for (k = 0u; k < n; k++) {
        if (arr[k].n > cl) { cl = arr[k].n; }
    }
    assert(cl >= 1u);
    return cl;
}

/* Significant coefficient count (trailing-zero-numerator coeffs dropped). */
static size_t qalg_trim(const srmech_bigint_t *nums, size_t n)
{
    size_t k = n;
    assert(nums != NULL || n == 0u);
    while (k > 0u && srmech_bigint_is_zero(&nums[k - 1u])) {
        k--;
    }
    assert(k <= n);
    return k;
}

/* dst[0..len) <- src[0..len) (deep copy of num + den). */
static srmech_status_t qalg_copy_run(srmech_bigint_t *dn, srmech_bigint_t *dd,
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

/* out = the constant Qalg element num/den (coord 0), coords 1..deg-1 = 0/1. */
static srmech_status_t qalg_set_scalar(srmech_bigint_t *on, srmech_bigint_t *od,
                                       int deg, const srmech_bigint_t *num,
                                       const srmech_bigint_t *den)
{
    srmech_status_t st;
    int k;
    assert(on != NULL && od != NULL && num != NULL && den != NULL);
    assert(deg >= 1);
    st = srmech_bigint_copy(&on[0], num);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&od[0], den);
    if (st != SRMECH_OK) { return st; }
    for (k = 1; k < deg; k++) {
        st = srmech_bigint_set_i64(&on[k], 0);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_set_i64(&od[k], 1);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* out = the zero Qalg element (all coords 0/1). */
static srmech_status_t qalg_zero_elem(srmech_bigint_t *on, srmech_bigint_t *od,
                                      int deg)
{
    srmech_status_t st;
    int k;
    assert(on != NULL && od != NULL);
    assert(deg >= 1);
    for (k = 0; k < deg; k++) {
        st = srmech_bigint_set_i64(&on[k], 0);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_set_i64(&od[k], 1);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* 1 iff every coordinate numerator is zero. */
static int qalg_is_zero_elem(const srmech_bigint_t *on, int deg)
{
    int k;
    assert(on != NULL);
    assert(deg >= 1);
    for (k = 0; k < deg; k++) {
        if (!srmech_bigint_is_zero(&on[k])) { return 0; }
    }
    return 1;
}

/* Copy a poly result src[0..slen) into a deg-length Qalg element, zero-padding
 * the high coordinates. slen <= deg (a field element has degree < deg). */
static srmech_status_t qalg_pad_into(srmech_bigint_t *on, srmech_bigint_t *od,
                                     const srmech_bigint_t *sn,
                                     const srmech_bigint_t *sd, size_t slen,
                                     int deg)
{
    int k;
    srmech_status_t st;
    assert(on != NULL && od != NULL);
    assert(slen <= (size_t)deg);
    for (k = 0; k < deg; k++) {
        if ((size_t)k < slen) {
            st = srmech_bigint_copy(&on[k], &sn[k]);
            if (st != SRMECH_OK) { return st; }
            st = srmech_bigint_copy(&od[k], &sd[k]);
            if (st != SRMECH_OK) { return st; }
        } else {
            st = srmech_bigint_set_i64(&on[k], 0);
            if (st != SRMECH_OK) { return st; }
            st = srmech_bigint_set_i64(&od[k], 1);
            if (st != SRMECH_OK) { return st; }
        }
    }
    return SRMECH_OK;
}

/* out = a · b in ℚ[x]/(m): convolution then reduce mod m. out is a deg element;
 * a, b are deg elements (zero-padded). Distinct from a/b (no aliasing). */
static srmech_status_t qalg_field_mul(qalg_eng_t *e, srmech_bigint_t *on,
                                      srmech_bigint_t *od,
                                      const srmech_bigint_t *an,
                                      const srmech_bigint_t *ad,
                                      const srmech_bigint_t *bn,
                                      const srmech_bigint_t *bd)
{
    srmech_status_t st;
    size_t clen = 0u, rn = 0u, qn = 0u;
    int deg = e->deg;
    assert(e != NULL && on != NULL && od != NULL);
    assert(an != NULL && bn != NULL);
    st = srmech_poly_mul(an, ad, (size_t)deg, bn, bd, (size_t)deg,
                         e->cvn, e->cvd, &clen, e->pws, e->pws_len);
    if (st != SRMECH_OK) { return st; }
    if (clen >= (size_t)(deg + 1)) {
        st = srmech_poly_divmod(e->cvn, e->cvd, clen, e->mn, e->md,
                                (size_t)(deg + 1), e->rqn, e->rqd, &qn,
                                e->rrn, e->rrd, &rn, e->pws, e->pws_len);
        if (st != SRMECH_OK) { return st; }
        return qalg_pad_into(on, od, e->rrn, e->rrd, rn, deg);
    }
    return qalg_pad_into(on, od, e->cvn, e->cvd, clen, deg);
}

/* out = a − b coordinatewise (exact-Q). out a deg element; a, b deg elements. */
static srmech_status_t qalg_field_sub(qalg_eng_t *e, srmech_bigint_t *on,
                                      srmech_bigint_t *od,
                                      const srmech_bigint_t *an,
                                      const srmech_bigint_t *ad,
                                      const srmech_bigint_t *bn,
                                      const srmech_bigint_t *bd)
{
    srmech_status_t st;
    size_t slen = 0u;
    int deg = e->deg;
    assert(e != NULL && on != NULL && od != NULL);
    assert(an != NULL && bn != NULL);
    st = srmech_poly_sub(an, ad, (size_t)deg, bn, bd, (size_t)deg,
                         e->asn, e->asd, &slen, e->pws, e->pws_len);
    if (st != SRMECH_OK) { return st; }
    return qalg_pad_into(on, od, e->asn, e->asd, slen, deg);
}

/* One extended-Euclid step over the (r0, u0) / (r1, u1) pairs: compute
 * quot,rem = divmod(r0, r1); qu = quot·u1; nu = u0 − qu; then shift
 * (r0,r1) <- (r1,rem), (u0,u1) <- (u1,nu). Lengths updated in place. */
static srmech_status_t qalg_euclid_step(qalg_eng_t *e, size_t *lr0, size_t *lr1,
                                        size_t *lu0, size_t *lu1)
{
    srmech_status_t st;
    size_t lq = 0u, lrem = 0u, lqu = 0u, lnu = 0u;
    assert(e != NULL && lr0 != NULL && lr1 != NULL);
    assert(lu0 != NULL && lu1 != NULL && *lr1 > 0u);
    st = srmech_poly_divmod(e->e0n, e->e0d, *lr0, e->e1n, e->e1d, *lr1,
                            e->eqn, e->eqd, &lq, e->ern, e->erd, &lrem,
                            e->pws, e->pws_len);
    if (st != SRMECH_OK) { return st; }
    st = srmech_poly_mul(e->eqn, e->eqd, lq, e->w1n, e->w1d, *lu1,
                         e->gun, e->gud, &lqu, e->pws, e->pws_len);
    if (st != SRMECH_OK) { return st; }
    st = srmech_poly_sub(e->w0n, e->w0d, *lu0, e->gun, e->gud, lqu,
                         e->nun, e->nud, &lnu, e->pws, e->pws_len);
    if (st != SRMECH_OK) { return st; }
    st = qalg_copy_run(e->e0n, e->e0d, e->e1n, e->e1d, *lr1);   /* r0 <- r1  */
    if (st != SRMECH_OK) { return st; }
    *lr0 = *lr1;
    st = qalg_copy_run(e->e1n, e->e1d, e->ern, e->erd, lrem);   /* r1 <- rem */
    if (st != SRMECH_OK) { return st; }
    *lr1 = lrem;
    st = qalg_copy_run(e->w0n, e->w0d, e->w1n, e->w1d, *lu1);   /* u0 <- u1  */
    if (st != SRMECH_OK) { return st; }
    *lu0 = *lu1;
    st = qalg_copy_run(e->w1n, e->w1d, e->nun, e->nud, lnu);    /* u1 <- nu  */
    if (st != SRMECH_OK) { return st; }
    *lu1 = lnu;
    return SRMECH_OK;
}

/* out = a⁻¹ in ℚ[x]/(m) via extended Euclid on (a, m): u·a + v·m = g (g a
 * nonzero constant since m is irreducible + a ≠ 0), so a⁻¹ = (u / g) mod m.
 * SRMECH_ERR_BAD_INPUT if a is zero or g is non-constant (reducible m). */
static srmech_status_t qalg_field_inverse(qalg_eng_t *e, srmech_bigint_t *on,
                                          srmech_bigint_t *od,
                                          const srmech_bigint_t *an,
                                          const srmech_bigint_t *ad)
{
    srmech_status_t st;
    size_t la = qalg_trim(an, (size_t)e->deg), lr0, lr1, lu0, lu1, lip = 0u, gk;
    size_t qn = 0u, rn = 0u;
    int deg = e->deg, guard = 0;
    assert(e != NULL && on != NULL && od != NULL);
    assert(an != NULL && ad != NULL);
    if (la == 0u) { return SRMECH_ERR_BAD_INPUT; }        /* zero element  */
    st = qalg_copy_run(e->e0n, e->e0d, an, ad, la); lr0 = la;   /* r0 <- a   */
    if (st != SRMECH_OK) { return st; }
    st = qalg_copy_run(e->e1n, e->e1d, e->mn, e->md, (size_t)(deg + 1));
    if (st != SRMECH_OK) { return st; }
    lr1 = (size_t)(deg + 1);                                    /* r1 <- m   */
    st = srmech_bigint_set_i64(&e->w0n[0], 1); if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&e->w0d[0], 1); if (st != SRMECH_OK) { return st; }
    lu0 = 1u;                                                   /* u0 <- [1] */
    lu1 = 0u;                                                   /* u1 <- 0   */
    while (lr1 > 0u && guard <= deg + 4) {
        st = qalg_euclid_step(e, &lr0, &lr1, &lu0, &lu1);
        if (st != SRMECH_OK) { return st; }
        guard++;
    }
    gk = qalg_trim(e->e0n, lr0);
    if (gk != 1u) { return SRMECH_ERR_BAD_INPUT; }        /* reducible m   */
    st = srmech_bigint_copy(&e->rcn[0], &e->e0d[0]);      /* recip = d/n   */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&e->rcd[0], &e->e0n[0]);
    if (st != SRMECH_OK) { return st; }
    if (e->rcd[0].sign < 0) {                             /* positive denom */
        e->rcd[0].sign = 1;
        e->rcn[0].sign = (e->rcn[0].sign == 0) ? 0 : -e->rcn[0].sign;
    }
    st = srmech_poly_mul(e->w0n, e->w0d, lu0, e->rcn, e->rcd, 1u,
                         e->ipn, e->ipd, &lip, e->pws, e->pws_len);
    if (st != SRMECH_OK) { return st; }
    if (lip >= (size_t)(deg + 1)) {
        st = srmech_poly_divmod(e->ipn, e->ipd, lip, e->mn, e->md,
                                (size_t)(deg + 1), e->rqn, e->rqd, &qn,
                                e->rrn, e->rrd, &rn, e->pws, e->pws_len);
        if (st != SRMECH_OK) { return st; }
        return qalg_pad_into(on, od, e->rrn, e->rrd, rn, deg);
    }
    return qalg_pad_into(on, od, e->ipn, e->ipd, lip, deg);
}

/* ---- engine carve -------------------------------------------------- */

/* Carve every roster buffer from the caller arena. On exhaustion the carve
 * returns NULL and *ok is cleared -> SRMECH_ERR_OVERFLOW. */
static srmech_status_t qalg_eng_carve(qalg_eng_t *e, void *ws, size_t ws_len)
{
    uint32_t *base = (uint32_t *)ws;
    size_t words = ws_len / sizeof(uint32_t), cur = 0u;
    size_t sb = e->sb, mm = (size_t)(e->deg + 1), dg = (size_t)e->deg;
    size_t cells = (size_t)e->n * (size_t)e->n * dg;
    uint32_t cap = e->cap;
    int ok = 1;
    assert(e != NULL);
    assert(ws != NULL || ws_len == 0u);
    e->mn = qalg_carve(base, words, &cur, mm, cap, &ok);
    e->md = qalg_carve(base, words, &cur, mm, cap, &ok);
    e->lamn = qalg_carve(base, words, &cur, dg, cap, &ok);
    e->lamd = qalg_carve(base, words, &cur, dg, cap, &ok);
    e->Mn = qalg_carve(base, words, &cur, cells, cap, &ok);
    e->Md = qalg_carve(base, words, &cur, cells, cap, &ok);
    e->cvn = qalg_carve(base, words, &cur, sb, cap, &ok);
    e->cvd = qalg_carve(base, words, &cur, sb, cap, &ok);
    e->rqn = qalg_carve(base, words, &cur, sb, cap, &ok);
    e->rqd = qalg_carve(base, words, &cur, sb, cap, &ok);
    e->rrn = qalg_carve(base, words, &cur, sb, cap, &ok);
    e->rrd = qalg_carve(base, words, &cur, sb, cap, &ok);
    e->asn = qalg_carve(base, words, &cur, sb, cap, &ok);
    e->asd = qalg_carve(base, words, &cur, sb, cap, &ok);
    e->e0n = qalg_carve(base, words, &cur, sb, cap, &ok);
    e->e0d = qalg_carve(base, words, &cur, sb, cap, &ok);
    e->e1n = qalg_carve(base, words, &cur, sb, cap, &ok);
    e->e1d = qalg_carve(base, words, &cur, sb, cap, &ok);
    e->w0n = qalg_carve(base, words, &cur, sb, cap, &ok);
    e->w0d = qalg_carve(base, words, &cur, sb, cap, &ok);
    e->w1n = qalg_carve(base, words, &cur, sb, cap, &ok);
    e->w1d = qalg_carve(base, words, &cur, sb, cap, &ok);
    e->eqn = qalg_carve(base, words, &cur, sb, cap, &ok);
    e->eqd = qalg_carve(base, words, &cur, sb, cap, &ok);
    e->ern = qalg_carve(base, words, &cur, sb, cap, &ok);
    e->erd = qalg_carve(base, words, &cur, sb, cap, &ok);
    e->gun = qalg_carve(base, words, &cur, sb, cap, &ok);
    e->gud = qalg_carve(base, words, &cur, sb, cap, &ok);
    e->nun = qalg_carve(base, words, &cur, sb, cap, &ok);
    e->nud = qalg_carve(base, words, &cur, sb, cap, &ok);
    e->rcn = qalg_carve(base, words, &cur, sb, cap, &ok);
    e->rcd = qalg_carve(base, words, &cur, sb, cap, &ok);
    e->ipn = qalg_carve(base, words, &cur, sb, cap, &ok);
    e->ipd = qalg_carve(base, words, &cur, sb, cap, &ok);
    e->invn = qalg_carve(base, words, &cur, dg, cap, &ok);
    e->invd = qalg_carve(base, words, &cur, dg, cap, &ok);
    e->tmn = qalg_carve(base, words, &cur, dg, cap, &ok);
    e->tmd = qalg_carve(base, words, &cur, dg, cap, &ok);
    e->fen = qalg_carve(base, words, &cur, dg, cap, &ok);
    e->fed = qalg_carve(base, words, &cur, dg, cap, &ok);
    e->pen = qalg_carve(base, words, &cur, dg, cap, &ok);
    e->ped = qalg_carve(base, words, &cur, dg, cap, &ok);
    e->den_ = qalg_carve(base, words, &cur, dg, cap, &ok);
    e->ded = qalg_carve(base, words, &cur, dg, cap, &ok);
    if (!ok) { return SRMECH_ERR_OVERFLOW; }
    e->pws = (void *)(base + cur);
    e->pws_len = (words - cur) * sizeof(uint32_t);
    return SRMECH_OK;
}

/* ---- matrix build / RREF / extract --------------------------------- */

/* Build M = A − λI with Qalg entries: each M[i][j] the constant a[i][j];
 * M[i][i] then subtracts λ (coordinatewise). */
static srmech_status_t qalg_build_matrix(qalg_eng_t *e,
                                         const srmech_bigint_t *a_n,
                                         const srmech_bigint_t *a_d)
{
    int i, j, n = e->n, deg = e->deg;
    size_t dg = (size_t)deg;
    srmech_status_t st;
    assert(e != NULL && a_n != NULL && a_d != NULL);
    assert(n >= 1 && deg >= 1);
    for (i = 0; i < n; i++) {
        for (j = 0; j < n; j++) {
            size_t off = ((size_t)i * (size_t)n + (size_t)j) * dg;
            const srmech_bigint_t *en = &a_n[(size_t)i * (size_t)n + (size_t)j];
            const srmech_bigint_t *ed = &a_d[(size_t)i * (size_t)n + (size_t)j];
            st = qalg_set_scalar(&e->Mn[off], &e->Md[off], deg, en, ed);
            if (st != SRMECH_OK) { return st; }
        }
    }
    for (i = 0; i < n; i++) {
        size_t off = ((size_t)i * (size_t)n + (size_t)i) * dg;
        st = qalg_field_sub(e, e->den_, e->ded, &e->Mn[off], &e->Md[off],
                            e->lamn, e->lamd);
        if (st != SRMECH_OK) { return st; }
        st = qalg_copy_run(&e->Mn[off], &e->Md[off], e->den_, e->ded, dg);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* Normalise the pivot row (physical `pr`) by `inv`, then clear column `c` from
 * every other logical row. Helper for qalg_rref (keeps it <= 60 lines). */
static srmech_status_t qalg_eliminate(qalg_eng_t *e, const int *row_perm,
                                      int r, int c, int pr)
{
    int j, rr, n = e->n;
    size_t dg = (size_t)e->deg, po;
    srmech_status_t st;
    assert(e != NULL && row_perm != NULL);
    assert(r >= 0 && c >= 0 && pr >= 0);
    for (j = 0; j < n; j++) {
        po = ((size_t)pr * (size_t)n + (size_t)j) * dg;
        st = qalg_field_mul(e, e->tmn, e->tmd, &e->Mn[po], &e->Md[po],
                            e->invn, e->invd);
        if (st != SRMECH_OK) { return st; }
        st = qalg_copy_run(&e->Mn[po], &e->Md[po], e->tmn, e->tmd, dg);
        if (st != SRMECH_OK) { return st; }
    }
    for (rr = 0; rr < n; rr++) {
        int prr = row_perm[rr];
        size_t fo = ((size_t)prr * (size_t)n + (size_t)c) * dg;
        if (rr == r) { continue; }
        if (qalg_is_zero_elem(&e->Mn[fo], e->deg)) { continue; }
        st = qalg_copy_run(e->fen, e->fed, &e->Mn[fo], &e->Md[fo], dg);
        if (st != SRMECH_OK) { return st; }
        for (j = 0; j < n; j++) {
            size_t ro = ((size_t)prr * (size_t)n + (size_t)j) * dg;
            po = ((size_t)pr * (size_t)n + (size_t)j) * dg;
            st = qalg_field_mul(e, e->pen, e->ped, e->fen, e->fed,
                                &e->Mn[po], &e->Md[po]);
            if (st != SRMECH_OK) { return st; }
            st = qalg_field_sub(e, e->den_, e->ded, &e->Mn[ro], &e->Md[ro],
                                e->pen, e->ped);
            if (st != SRMECH_OK) { return st; }
            st = qalg_copy_run(&e->Mn[ro], &e->Md[ro], e->den_, e->ded, dg);
            if (st != SRMECH_OK) { return st; }
        }
    }
    return SRMECH_OK;
}

/* Exact reduced row echelon over ℚ(λ) via a row permutation (no data move).
 * Records piv_row_of_col[c] (LOGICAL pivot row) + is_pivot[c] for each column. */
static srmech_status_t qalg_rref(qalg_eng_t *e, int *row_perm,
                                 int *piv_row_of_col, int *is_pivot)
{
    int r = 0, c, rr, n = e->n;
    size_t dg = (size_t)e->deg;
    srmech_status_t st;
    assert(e != NULL && row_perm != NULL && piv_row_of_col != NULL);
    assert(is_pivot != NULL && n >= 1);
    for (c = 0; c < n; c++) {
        int piv = -1, tmp, pr;
        size_t pco;
        for (rr = r; rr < n; rr++) {
            size_t co = ((size_t)row_perm[rr] * (size_t)n + (size_t)c) * dg;
            if (!qalg_is_zero_elem(&e->Mn[co], e->deg)) { piv = rr; break; }
        }
        if (piv < 0) { continue; }
        tmp = row_perm[r]; row_perm[r] = row_perm[piv]; row_perm[piv] = tmp;
        pr = row_perm[r];
        pco = ((size_t)pr * (size_t)n + (size_t)c) * dg;
        st = qalg_field_inverse(e, e->invn, e->invd, &e->Mn[pco], &e->Md[pco]);
        if (st != SRMECH_OK) { return st; }          /* reducible m / overflow */
        st = qalg_eliminate(e, row_perm, r, c, pr);
        if (st != SRMECH_OK) { return st; }
        piv_row_of_col[c] = r;
        is_pivot[c] = 1;
        r++;
        if (r == n) { break; }
    }
    return SRMECH_OK;
}

/* Read the null-space basis off the RREF: each free column fc gives one vector
 * v (v[fc]=1, v[pivot col c] = −M[pivot row][fc], else 0), written to out. */
static srmech_status_t qalg_extract(qalg_eng_t *e, const int *row_perm,
                                    const int *piv_row_of_col,
                                    const int *is_pivot,
                                    srmech_bigint_t *out_n,
                                    srmech_bigint_t *out_d, int *out_k)
{
    int fc, c, comp, n = e->n, deg = e->deg, k = 0;
    size_t dg = (size_t)deg;
    srmech_status_t st;
    assert(e != NULL && out_n != NULL && out_d != NULL && out_k != NULL);
    assert(row_perm != NULL && is_pivot != NULL);
    for (fc = 0; fc < n; fc++) {
        srmech_bigint_t *vn, *vd;
        if (is_pivot[fc]) { continue; }
        for (comp = 0; comp < n; comp++) {
            size_t vo = (((size_t)k * (size_t)n + (size_t)comp)) * dg;
            st = qalg_zero_elem(&out_n[vo], &out_d[vo], deg);
            if (st != SRMECH_OK) { return st; }
        }
        vn = &out_n[(((size_t)k * (size_t)n + (size_t)fc)) * dg];
        vd = &out_d[(((size_t)k * (size_t)n + (size_t)fc)) * dg];
        st = srmech_bigint_set_i64(&vn[0], 1); if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_set_i64(&vd[0], 1); if (st != SRMECH_OK) { return st; }
        for (c = 0; c < n; c++) {
            int pr, cc;
            size_t fo, vco;
            if (!is_pivot[c]) { continue; }
            pr = row_perm[piv_row_of_col[c]];
            fo = ((size_t)pr * (size_t)n + (size_t)fc) * dg;
            vco = (((size_t)k * (size_t)n + (size_t)c)) * dg;
            st = qalg_copy_run(&out_n[vco], &out_d[vco], &e->Mn[fo], &e->Md[fo],
                               dg);
            if (st != SRMECH_OK) { return st; }
            for (cc = 0; cc < deg; cc++) {           /* negate: −M[pr][fc]  */
                srmech_bigint_t *t = &out_n[vco + (size_t)cc];
                t->sign = (t->sign == 0) ? 0 : -t->sign;
            }
        }
        k++;
    }
    *out_k = k;
    return SRMECH_OK;
}

/* ---- public API ---------------------------------------------------- */

/* Per-coefficient limb cap the caller must give each srmech_bigint in the out_n /
 * out_d arrays (so a reduced null-vector coordinate never overflows). */
size_t srmech_eigvec_exact_entry_cap(size_t coeff_limbs, int n, int deg)
{
    assert(n >= 0);
    assert(deg >= 0);
    if (n < 1 || deg < 1) { return 1u; }
    return qalg_cap_for(coeff_limbs, n, deg);
}

/* Minimum `ws_len` BYTES for srmech_eigvec_exact: the modulus/λ carriers, the
 * n·n·deg Qalg matrix, the field-op + Euclid scratch, and the srmech_poly_*
 * arena tail. 8-byte-aligned uint32 bump region. */
size_t srmech_eigvec_exact_ws_bound(size_t coeff_limbs, int n, int deg)
{
    size_t cap, sb, dg, cells, hdr, small_pairs, headers, limbs, poly_ws, words;
    assert(n >= 0);
    assert(deg >= 0);
    if (n < 1 || deg < 1) { return 64u; }
    cap = qalg_cap_for(coeff_limbs, n, deg);
    sb = (size_t)(2 * deg + 2);
    dg = (size_t)deg;
    cells = (size_t)n * (size_t)n * dg;
    hdr = (sizeof(srmech_bigint_t) + sizeof(uint32_t) - 1u) / sizeof(uint32_t);
    /* mm(2) + lam(2) + 14 sb-pairs(28) coeff-slots; element temps(6 pairs=12 dg);
     * plus M (2·cells). Count total srmech_bigint slots. */
    small_pairs = 2u * (size_t)(deg + 1)            /* mm num+den            */
                  + 2u * dg                          /* lam                  */
                  + 28u * sb                         /* 14 sb pairs          */
                  + 12u * dg;                        /* 6 element-temp pairs */
    headers = (small_pairs + 2u * cells) * hdr;
    limbs = (small_pairs + 2u * cells) * cap;
    poly_ws = srmech_poly_ws_bound(cap, (size_t)(2 * deg + 4)) / sizeof(uint32_t);
    words = headers + limbs + poly_ws + 64u;
    return words * sizeof(uint32_t);
}

/* The exact eigenvectors of the integer/rational matrix A (n·n, num/den) for the
 * algebraic eigenvalue λ = Σ lam[i]·αⁱ, α a root of the monic irreducible integer
 * m (deg+1 coeffs low->high, denominators implied 1): the null space of A − λI
 * over ℚ(λ) = ℚ[x]/(m), read off the exact RREF. out_n/out_d receive *out_k basis
 * vectors, each n components of deg ℚ(λ) coordinates (num/den), at
 * out[((v·n + comp)·deg + coeff)] — the caller sizes them n·n·deg slots, each
 * >= srmech_eigvec_exact_entry_cap limbs. *out_k is the null-space dimension
 * (0 iff λ is not an eigenvalue). n/deg in [1, QALG_MAX_DIM]; reducible m or a
 * zero-divisor pivot -> SRMECH_ERR_BAD_INPUT; a too-small arena / coordinate cap
 * -> SRMECH_ERR_OVERFLOW (the caller falls back to the byte-identical pure path). */
srmech_status_t srmech_eigvec_exact(
        const srmech_bigint_t *a_n, const srmech_bigint_t *a_d, int n,
        const srmech_bigint_t *m, int deg,
        const srmech_bigint_t *lam_n, const srmech_bigint_t *lam_d,
        srmech_bigint_t *out_n, srmech_bigint_t *out_d, int *out_k,
        void *ws, size_t ws_len)
{
    qalg_eng_t e;
    srmech_status_t st;
    size_t cl, cm, cll, k;
    int row_perm[QALG_MAX_DIM];
    int piv_row_of_col[QALG_MAX_DIM];
    int is_pivot[QALG_MAX_DIM];
    int i;
    assert(out_k != NULL);
    assert(a_n != NULL && m != NULL && lam_n != NULL);
    if (a_n == NULL || a_d == NULL || m == NULL || lam_n == NULL
        || lam_d == NULL || out_n == NULL || out_d == NULL || out_k == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n < 1 || n > QALG_MAX_DIM || deg < 1 || deg > QALG_MAX_DIM) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (m[deg].sign != 1 || m[deg].n != 1u || m[deg].limbs[0] != 1u) {
        return SRMECH_ERR_BAD_INPUT;                 /* m must be monic     */
    }
    cl = qalg_input_limbs(a_n, (size_t)n * (size_t)n);
    cm = qalg_input_limbs(m, (size_t)(deg + 1));
    if (cm > cl) { cl = cm; }
    cll = qalg_input_limbs(lam_n, (size_t)deg);
    if (cll > cl) { cl = cll; }
    e.deg = deg; e.n = n;
    e.cap = (uint32_t)qalg_cap_for(cl, n, deg);
    e.sb = (size_t)(2 * deg + 2);
    st = qalg_eng_carve(&e, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    for (k = 0u; k < (size_t)(deg + 1); k++) {       /* mm = m, den 1       */
        st = srmech_bigint_copy(&e.mn[k], &m[k]);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_set_i64(&e.md[k], 1);
        if (st != SRMECH_OK) { return st; }
    }
    st = qalg_copy_run(e.lamn, e.lamd, lam_n, lam_d, (size_t)deg);
    if (st != SRMECH_OK) { return st; }
    for (i = 0; i < n; i++) {
        row_perm[i] = i; piv_row_of_col[i] = -1; is_pivot[i] = 0;
    }
    st = qalg_build_matrix(&e, a_n, a_d);
    if (st != SRMECH_OK) { return st; }
    st = qalg_rref(&e, row_perm, piv_row_of_col, is_pivot);
    if (st != SRMECH_OK) { return st; }
    return qalg_extract(&e, row_perm, piv_row_of_col, is_pivot,
                        out_n, out_d, out_k);
}

/* ==================================================================== *
 * Qalg TAIL Batch 7b — the exact JORDAN CHAINS (generalized eigenvectors)
 * of an integer/rational matrix for an eigenvalue λ, over ℚ(λ) = ℚ[x]/(m):
 * the C peer of srmech.amsc.cascade.matrix_cascades.jordan_chains_exact.
 *
 * With N = A − λI (Qalg entries over ℚ(λ)), the generalized eigenspace
 * null(Nᵘ) has dimension μ and N is nilpotent on it. The Jordan structure is
 * read off the exact Qalg-RREF ranks r_k = rank(Nᵏ): # blocks of size exactly
 * k = r_{k-1} − 2·r_k + r_{k+1}. The chains are built TOP-DOWN — for block size
 * s from p (the smallest stabilising power) down to 1, pick a generalized
 * eigenvector v in null(N^s) that is independent (over ℚ(λ)) of null(N^{s-1})
 * ∪ the chains already chosen, and form the chain v, N·v, …, N^{s-1}·v (stored
 * bottom→top). All arithmetic COMPOSES the rc163 Qalg field (qalg_field_mul /
 * qalg_field_sub / qalg_field_inverse over the exact-ℚ srmech_poly_* kernels)
 * — the added ops here are the Qalg matrix MATMUL (for Nᵏ), RANK, and nested
 * NULLSPACE / column-rank. Byte/structurally-identical to the pure
 * _jordan_chains_build_pure (the RREF is canonical + the selection
 * deterministic). Additive symbols -> SRMECH_ABI_VERSION unchanged (stays 3).
 * ==================================================================== */

/* out = a + b coordinatewise (exact-ℚ). out a deg element; a, b deg elements. */
static srmech_status_t qalg_field_add(qalg_eng_t *e, srmech_bigint_t *on,
                                      srmech_bigint_t *od,
                                      const srmech_bigint_t *an,
                                      const srmech_bigint_t *ad,
                                      const srmech_bigint_t *bn,
                                      const srmech_bigint_t *bd)
{
    srmech_status_t st;
    size_t slen = 0u;
    int deg = e->deg;
    assert(e != NULL && on != NULL && od != NULL);
    assert(an != NULL && bn != NULL);
    st = srmech_poly_add(an, ad, (size_t)deg, bn, bd, (size_t)deg,
                         e->asn, e->asd, &slen, e->pws, e->pws_len);
    if (st != SRMECH_OK) { return st; }
    return qalg_pad_into(on, od, e->asn, e->asd, slen, deg);
}

/* out = A·B over ℚ(λ): out[i][j] = Σ_k A[i][k]·B[k][j]. out MUST NOT alias A/B
 * (out is a distinct n·n·deg buffer). */
static srmech_status_t qalg_gmatmul(qalg_eng_t *e, srmech_bigint_t *on,
                                    srmech_bigint_t *od,
                                    const srmech_bigint_t *an,
                                    const srmech_bigint_t *ad,
                                    const srmech_bigint_t *bn,
                                    const srmech_bigint_t *bd, int n)
{
    int i, j, k, deg = e->deg;
    size_t dg = (size_t)deg;
    srmech_status_t st;
    assert(e != NULL && on != NULL && an != NULL && bn != NULL);
    assert(n >= 1 && deg >= 1);
    for (i = 0; i < n; i++) {
        for (j = 0; j < n; j++) {
            size_t oo = ((size_t)i * (size_t)n + (size_t)j) * dg;
            st = qalg_zero_elem(&on[oo], &od[oo], deg);
            if (st != SRMECH_OK) { return st; }
            for (k = 0; k < n; k++) {
                size_t ao = ((size_t)i * (size_t)n + (size_t)k) * dg;
                size_t bo = ((size_t)k * (size_t)n + (size_t)j) * dg;
                if (qalg_is_zero_elem(&an[ao], deg)) { continue; }
                if (qalg_is_zero_elem(&bn[bo], deg)) { continue; }
                st = qalg_field_mul(e, e->jp0n, e->jp0d, &an[ao], &ad[ao],
                                    &bn[bo], &bd[bo]);
                if (st != SRMECH_OK) { return st; }
                st = qalg_field_add(e, e->jp1n, e->jp1d, &on[oo], &od[oo],
                                    e->jp0n, e->jp0d);
                if (st != SRMECH_OK) { return st; }
                st = qalg_copy_run(&on[oo], &od[oo], e->jp1n, e->jp1d, dg);
                if (st != SRMECH_OK) { return st; }
            }
        }
    }
    return SRMECH_OK;
}

/* out = M·v over ℚ(λ): out[i] = Σ_j M[i][j]·v[j]. out MUST NOT alias v (out is
 * a distinct n·deg buffer). */
static srmech_status_t qalg_gmatvec(qalg_eng_t *e, srmech_bigint_t *on,
                                    srmech_bigint_t *od,
                                    const srmech_bigint_t *mn,
                                    const srmech_bigint_t *md,
                                    const srmech_bigint_t *vn,
                                    const srmech_bigint_t *vd, int n)
{
    int i, j, deg = e->deg;
    size_t dg = (size_t)deg;
    srmech_status_t st;
    assert(e != NULL && on != NULL && mn != NULL && vn != NULL);
    assert(n >= 1 && deg >= 1);
    for (i = 0; i < n; i++) {
        size_t oo = (size_t)i * dg;
        st = qalg_zero_elem(&on[oo], &od[oo], deg);
        if (st != SRMECH_OK) { return st; }
        for (j = 0; j < n; j++) {
            size_t mo = ((size_t)i * (size_t)n + (size_t)j) * dg;
            size_t vo = (size_t)j * dg;
            if (qalg_is_zero_elem(&mn[mo], deg)) { continue; }
            if (qalg_is_zero_elem(&vn[vo], deg)) { continue; }
            st = qalg_field_mul(e, e->jp0n, e->jp0d, &mn[mo], &md[mo],
                                &vn[vo], &vd[vo]);
            if (st != SRMECH_OK) { return st; }
            st = qalg_field_add(e, e->jp1n, e->jp1d, &on[oo], &od[oo],
                                e->jp0n, e->jp0d);
            if (st != SRMECH_OK) { return st; }
            st = qalg_copy_run(&on[oo], &od[oo], e->jp1n, e->jp1d, dg);
            if (st != SRMECH_OK) { return st; }
        }
    }
    return SRMECH_OK;
}

/* Normalise pivot row `pr` (physical) by e->inv over nc cols, then clear column
 * `c` from every other logical row. General (nr × nc) sibling of qalg_eliminate. */
static srmech_status_t qalg_geliminate(qalg_eng_t *e, srmech_bigint_t *mn,
                                       srmech_bigint_t *md, int nr, int nc,
                                       const int *row_perm, int r, int c,
                                       int pr)
{
    int j, rr;
    size_t dg = (size_t)e->deg, po;
    srmech_status_t st;
    assert(e != NULL && mn != NULL && row_perm != NULL);
    assert(r >= 0 && c >= 0 && pr >= 0);
    for (j = 0; j < nc; j++) {
        po = ((size_t)pr * (size_t)nc + (size_t)j) * dg;
        st = qalg_field_mul(e, e->tmn, e->tmd, &mn[po], &md[po],
                            e->invn, e->invd);
        if (st != SRMECH_OK) { return st; }
        st = qalg_copy_run(&mn[po], &md[po], e->tmn, e->tmd, dg);
        if (st != SRMECH_OK) { return st; }
    }
    for (rr = 0; rr < nr; rr++) {
        int prr = row_perm[rr];
        size_t fo = ((size_t)prr * (size_t)nc + (size_t)c) * dg;
        if (rr == r) { continue; }
        if (qalg_is_zero_elem(&mn[fo], e->deg)) { continue; }
        st = qalg_copy_run(e->fen, e->fed, &mn[fo], &md[fo], dg);
        if (st != SRMECH_OK) { return st; }
        for (j = 0; j < nc; j++) {
            size_t ro = ((size_t)prr * (size_t)nc + (size_t)j) * dg;
            po = ((size_t)pr * (size_t)nc + (size_t)j) * dg;
            st = qalg_field_mul(e, e->pen, e->ped, e->fen, e->fed,
                                &mn[po], &md[po]);
            if (st != SRMECH_OK) { return st; }
            st = qalg_field_sub(e, e->den_, e->ded, &mn[ro], &md[ro],
                                e->pen, e->ped);
            if (st != SRMECH_OK) { return st; }
            st = qalg_copy_run(&mn[ro], &md[ro], e->den_, e->ded, dg);
            if (st != SRMECH_OK) { return st; }
        }
    }
    return SRMECH_OK;
}

/* Exact reduced row echelon of an (nr × nc) Qalg matrix via a row permutation.
 * Records piv_row_of_col[c] (LOGICAL pivot row) + is_pivot[c]; *out_rank = the
 * pivot count. General sibling of qalg_rref (caller inits row_perm/piv/is_pivot). */
static srmech_status_t qalg_grref(qalg_eng_t *e, srmech_bigint_t *mn,
                                  srmech_bigint_t *md, int nr, int nc,
                                  int *row_perm, int *piv_row_of_col,
                                  int *is_pivot, int *out_rank)
{
    int r = 0, c, rr;
    size_t dg = (size_t)e->deg;
    srmech_status_t st;
    assert(e != NULL && mn != NULL && row_perm != NULL);
    assert(out_rank != NULL && nr >= 1);
    for (c = 0; c < nc; c++) {
        int piv = -1, tmp, pr;
        size_t pco;
        for (rr = r; rr < nr; rr++) {
            size_t co = ((size_t)row_perm[rr] * (size_t)nc + (size_t)c) * dg;
            if (!qalg_is_zero_elem(&mn[co], e->deg)) { piv = rr; break; }
        }
        if (piv < 0) { continue; }
        tmp = row_perm[r]; row_perm[r] = row_perm[piv]; row_perm[piv] = tmp;
        pr = row_perm[r];
        pco = ((size_t)pr * (size_t)nc + (size_t)c) * dg;
        st = qalg_field_inverse(e, e->invn, e->invd, &mn[pco], &md[pco]);
        if (st != SRMECH_OK) { return st; }
        st = qalg_geliminate(e, mn, md, nr, nc, row_perm, r, c, pr);
        if (st != SRMECH_OK) { return st; }
        piv_row_of_col[c] = r;
        is_pivot[c] = 1;
        r++;
        if (r == nr) { break; }
    }
    *out_rank = r;
    return SRMECH_OK;
}

/* Read the null-space basis of an n×n Qalg matrix off its RREF (`mn`/`md`, and
 * the rp/pc/ip a preceding qalg_grref produced): each free column fc gives one
 * vector (v[fc]=1, v[pivot col c] = −M[pivot row][fc], else 0). Byte-identical
 * to qalg_extract (which is byte-identical to the pure _qalg_nullspace). */
static srmech_status_t qalg_gnullspace(qalg_eng_t *e, const srmech_bigint_t *mn,
                                       const srmech_bigint_t *md, int n,
                                       const int *rp, const int *pc,
                                       const int *ip, srmech_bigint_t *out_n,
                                       srmech_bigint_t *out_d, int *out_k)
{
    int fc, c, comp, deg = e->deg, k = 0;
    size_t dg = (size_t)deg;
    srmech_status_t st;
    assert(e != NULL && mn != NULL && out_n != NULL && out_k != NULL);
    assert(rp != NULL && ip != NULL);
    for (fc = 0; fc < n; fc++) {
        srmech_bigint_t *vn, *vd;
        if (ip[fc]) { continue; }
        for (comp = 0; comp < n; comp++) {
            size_t vo = ((size_t)k * (size_t)n + (size_t)comp) * dg;
            st = qalg_zero_elem(&out_n[vo], &out_d[vo], deg);
            if (st != SRMECH_OK) { return st; }
        }
        vn = &out_n[((size_t)k * (size_t)n + (size_t)fc) * dg];
        vd = &out_d[((size_t)k * (size_t)n + (size_t)fc) * dg];
        st = srmech_bigint_set_i64(&vn[0], 1); if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_set_i64(&vd[0], 1); if (st != SRMECH_OK) { return st; }
        for (c = 0; c < n; c++) {
            int pr, cc;
            size_t fo, vco;
            if (!ip[c]) { continue; }
            pr = rp[pc[c]];
            fo = ((size_t)pr * (size_t)n + (size_t)fc) * dg;
            vco = ((size_t)k * (size_t)n + (size_t)c) * dg;
            st = qalg_copy_run(&out_n[vco], &out_d[vco], &mn[fo], &md[fo], dg);
            if (st != SRMECH_OK) { return st; }
            for (cc = 0; cc < deg; cc++) {           /* negate: −M[pr][fc] */
                srmech_bigint_t *t = &out_n[vco + (size_t)cc];
                t->sign = (t->sign == 0) ? 0 : -t->sign;
            }
        }
        k++;
    }
    *out_k = k;
    return SRMECH_OK;
}

/* rank(M) for an n×n Qalg matrix M — RREF a scratch COPY (e->sn), count pivots. */
static srmech_status_t qalg_rank_of(qalg_eng_t *e, const srmech_bigint_t *mn,
                                    const srmech_bigint_t *md, int n,
                                    int *rank, int *rp, int *pc, int *ip)
{
    size_t cells = (size_t)n * (size_t)n * (size_t)e->deg;
    int i, rk = 0;
    srmech_status_t st;
    assert(e != NULL && rank != NULL && rp != NULL);
    assert(n >= 1);
    st = qalg_copy_run(e->sn, e->sd, mn, md, cells);
    if (st != SRMECH_OK) { return st; }
    for (i = 0; i < n; i++) { rp[i] = i; pc[i] = -1; ip[i] = 0; }
    st = qalg_grref(e, e->sn, e->sd, n, n, rp, pc, ip, &rk);
    if (st != SRMECH_OK) { return st; }
    *rank = rk;
    return SRMECH_OK;
}

/* null(M) basis for an n×n Qalg matrix M into out — RREF a scratch COPY, extract. */
static srmech_status_t qalg_nullspace_of(qalg_eng_t *e,
                                         const srmech_bigint_t *mn,
                                         const srmech_bigint_t *md, int n,
                                         srmech_bigint_t *out_n,
                                         srmech_bigint_t *out_d, int *out_k,
                                         int *rp, int *pc, int *ip)
{
    size_t cells = (size_t)n * (size_t)n * (size_t)e->deg;
    int i, rk = 0;
    srmech_status_t st;
    assert(e != NULL && out_n != NULL && out_k != NULL);
    assert(n >= 1);
    st = qalg_copy_run(e->sn, e->sd, mn, md, cells);
    if (st != SRMECH_OK) { return st; }
    for (i = 0; i < n; i++) { rp[i] = i; pc[i] = -1; ip[i] = 0; }
    st = qalg_grref(e, e->sn, e->sd, n, n, rp, pc, ip, &rk);
    if (st != SRMECH_OK) { return st; }
    return qalg_gnullspace(e, e->sn, e->sd, n, rp, pc, ip, out_n, out_d, out_k);
}

/* out = the n×n identity over ℚ(λ) (diagonal = the field element 1). */
static srmech_status_t qalg_set_identity(qalg_eng_t *e, srmech_bigint_t *mn,
                                         srmech_bigint_t *md, int n)
{
    int i, j, deg = e->deg;
    size_t dg = (size_t)deg;
    srmech_status_t st;
    assert(e != NULL && mn != NULL);
    assert(n >= 1 && deg >= 1);
    for (i = 0; i < n; i++) {
        for (j = 0; j < n; j++) {
            size_t off = ((size_t)i * (size_t)n + (size_t)j) * dg;
            st = qalg_zero_elem(&mn[off], &md[off], deg);
            if (st != SRMECH_OK) { return st; }
            if (i == j) {
                st = srmech_bigint_set_i64(&mn[off], 1);
                if (st != SRMECH_OK) { return st; }
            }
        }
    }
    return SRMECH_OK;
}

/* Copy the column vector `v` (n components of deg coords) into column `col` of
 * the n×K column-rank scratch matrix e->cn. */
static srmech_status_t qalg_fill_col(qalg_eng_t *e, int K, int col,
                                     const srmech_bigint_t *vn,
                                     const srmech_bigint_t *vd, int n)
{
    int i, deg = e->deg;
    size_t dg = (size_t)deg;
    srmech_status_t st;
    assert(e != NULL && vn != NULL);
    assert(K >= 1 && col >= 0 && col < K);
    for (i = 0; i < n; i++) {
        size_t dst = ((size_t)i * (size_t)K + (size_t)col) * dg;
        size_t src = (size_t)i * dg;
        st = qalg_copy_run(&e->cn[dst], &e->cd[dst], &vn[src], &vd[src], dg);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* Assemble the context column matrix e->cn (n × K): the lk lower-null vectors,
 * then the vi already-chosen chain vectors (from out), then optionally cvn/cvd
 * (the candidate). K = lk + vi + (cvn != NULL). */
static srmech_status_t qalg_build_context(qalg_eng_t *e, int K, int lk,
                                          const srmech_bigint_t *out_n,
                                          const srmech_bigint_t *out_d, int vi,
                                          const srmech_bigint_t *cvn,
                                          const srmech_bigint_t *cvd, int n)
{
    int col = 0, j;
    size_t vc = (size_t)n * (size_t)e->deg;
    srmech_status_t st;
    assert(e != NULL && K >= 0);
    assert(lk >= 0 && vi >= 0);
    for (j = 0; j < lk; j++) {
        size_t lo = (size_t)j * vc;
        st = qalg_fill_col(e, K, col, &e->lon[lo], &e->lod[lo], n);
        if (st != SRMECH_OK) { return st; }
        col++;
    }
    for (j = 0; j < vi; j++) {
        size_t oo = (size_t)j * vc;
        st = qalg_fill_col(e, K, col, &out_n[oo], &out_d[oo], n);
        if (st != SRMECH_OK) { return st; }
        col++;
    }
    if (cvn != NULL) {
        st = qalg_fill_col(e, K, col, cvn, cvd, n);
        if (st != SRMECH_OK) { return st; }
        col++;
    }
    assert(col == K);
    return SRMECH_OK;
}

/* rank of the K columns currently assembled in e->cn (n × K) — RREF it. */
static srmech_status_t qalg_col_rank(qalg_eng_t *e, int K, int *rank,
                                     int *rp, int *pc, int *ip)
{
    int i, rk = 0;
    srmech_status_t st;
    assert(e != NULL && rank != NULL);
    assert(K >= 0);
    if (K == 0) { *rank = 0; return SRMECH_OK; }
    for (i = 0; i < e->n; i++) { rp[i] = i; }
    for (i = 0; i < K; i++) { pc[i] = -1; ip[i] = 0; }
    st = qalg_grref(e, e->cn, e->cd, e->n, K, rp, pc, ip, &rk);
    if (st != SRMECH_OK) { return st; }
    *rank = rk;
    return SRMECH_OK;
}

/* 1 iff the candidate cvn/cvd is linearly INDEPENDENT (over ℚ(λ)) of the lk
 * lower-null vectors ∪ the vi already-chosen chain vectors: column-rank rises. */
static srmech_status_t qalg_cand_independent(qalg_eng_t *e,
                                             const srmech_bigint_t *cvn,
                                             const srmech_bigint_t *cvd, int lk,
                                             const srmech_bigint_t *out_n,
                                             const srmech_bigint_t *out_d,
                                             int vi, int *out_indep,
                                             int *rp, int *pc, int *ip)
{
    int n = e->n, r0 = 0, r1 = 0, base = lk + vi;
    srmech_status_t st;
    assert(e != NULL && out_indep != NULL);
    assert(lk >= 0 && vi >= 0);
    st = qalg_build_context(e, base, lk, out_n, out_d, vi, NULL, NULL, n);
    if (st != SRMECH_OK) { return st; }
    st = qalg_col_rank(e, base, &r0, rp, pc, ip);
    if (st != SRMECH_OK) { return st; }
    st = qalg_build_context(e, base + 1, lk, out_n, out_d, vi, cvn, cvd, n);
    if (st != SRMECH_OK) { return st; }
    st = qalg_col_rank(e, base + 1, &r1, rp, pc, ip);
    if (st != SRMECH_OK) { return st; }
    *out_indep = (r1 > r0) ? 1 : 0;
    return SRMECH_OK;
}

/* Build the chain v, N·v, …, N^{s-1}·v from the top `cand`, stored BOTTOM→TOP
 * into out[vi .. vi+s-1] (out[vi+s-1] = cand; out[vi] = N^{s-1}·cand). */
static srmech_status_t qalg_build_chain(qalg_eng_t *e, srmech_bigint_t *out_n,
                                        srmech_bigint_t *out_d, int vi,
                                        const srmech_bigint_t *candn,
                                        const srmech_bigint_t *candd,
                                        int s, int n)
{
    int t;
    size_t vc = (size_t)n * (size_t)e->deg;
    size_t top = (size_t)(vi + s - 1) * vc;
    srmech_status_t st;
    assert(e != NULL && out_n != NULL && candn != NULL);
    assert(s >= 1 && vi >= 0);
    st = qalg_copy_run(&out_n[top], &out_d[top], candn, candd, vc);
    if (st != SRMECH_OK) { return st; }
    for (t = 1; t < s; t++) {
        size_t dst = (size_t)(vi + s - 1 - t) * vc;
        size_t src = (size_t)(vi + s - t) * vc;
        st = qalg_gmatvec(e, e->van, e->vad, e->Nn, e->Nd,
                          &out_n[src], &out_d[src], n);
        if (st != SRMECH_OK) { return st; }
        st = qalg_copy_run(&out_n[dst], &out_d[dst], e->van, e->vad, vc);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* Phase 1: pw[0]=I; iterate pw[k+1]=pw[k]·N recording ranks[k+1]=rank(pw[k+1])
 * until the rank stops dropping (ranks[idx]==ranks[idx-1]) or the safety index
 * idx>n; *out_p = the stabilising power p (= len(ranks)-1 in the pure path). */
static srmech_status_t qalg_jordan_powers(qalg_eng_t *e, int *ranks, int *nul,
                                          int *out_p, int *rp, int *pc, int *ip)
{
    int n = e->n, kk = 0, rk = 0, idx;
    size_t cells = (size_t)n * (size_t)n * (size_t)e->deg;
    srmech_status_t st;
    assert(e != NULL && ranks != NULL && out_p != NULL);
    assert(n >= 1);
    st = qalg_set_identity(e, e->pwn, e->pwd, n);
    if (st != SRMECH_OK) { return st; }
    ranks[0] = n; nul[0] = 0;
    for (;;) {
        size_t pko = (size_t)kk * cells;
        size_t pk1 = (size_t)(kk + 1) * cells;
        idx = kk + 1;
        st = qalg_gmatmul(e, e->tn, e->td, &e->pwn[pko], &e->pwd[pko],
                          e->Nn, e->Nd, n);
        if (st != SRMECH_OK) { return st; }
        st = qalg_rank_of(e, e->tn, e->td, n, &rk, rp, pc, ip);
        if (st != SRMECH_OK) { return st; }
        st = qalg_copy_run(&e->pwn[pk1], &e->pwd[pk1], e->tn, e->td, cells);
        if (st != SRMECH_OK) { return st; }
        ranks[idx] = rk; nul[idx] = n - rk;
        if (rk == ranks[idx - 1]) { *out_p = idx; return SRMECH_OK; }
        if (idx > n) { *out_p = idx; return SRMECH_OK; }
        kk = idx;
    }
}

/* # Jordan blocks of size EXACTLY k = r_{k-1} − 2·r_k + r_{k+1}, for k = 1..p
 * (r_{p+1} := r_p — the pure path's ranks[-1] clamp). */
static void qalg_block_counts(const int *ranks, int p, int *nblocks)
{
    int k;
    assert(ranks != NULL && nblocks != NULL);
    assert(p >= 0);
    for (k = 1; k <= p; k++) {
        int rm1 = ranks[k - 1], rk = ranks[k];
        int rp1 = (k + 1 <= p) ? ranks[k + 1] : ranks[p];
        nblocks[k] = rm1 - 2 * rk + rp1;
    }
}

/* Process one block size s (need = # blocks of size exactly s): pick `need`
 * independent tops from null(N^s) modulo null(N^{s-1}) ∪ the chosen chains,
 * build each chain, append to out[*vi..] + record its length in out_bs. */
static srmech_status_t qalg_topdown_s(qalg_eng_t *e, int s, int need,
                                      srmech_bigint_t *out_n,
                                      srmech_bigint_t *out_d, int *out_bs,
                                      int *vi, int *nc, int *rp, int *pc,
                                      int *ip)
{
    int lk = 0, ck = 0, ci, picked = 0, n = e->n;
    size_t cells = (size_t)n * (size_t)n * (size_t)e->deg;
    size_t vc = (size_t)n * (size_t)e->deg;
    srmech_status_t st;
    assert(e != NULL && out_n != NULL && vi != NULL && nc != NULL);
    assert(s >= 1 && need >= 1);
    if (s - 1 >= 1) {
        size_t po = (size_t)(s - 1) * cells;
        st = qalg_nullspace_of(e, &e->pwn[po], &e->pwd[po], n,
                               e->lon, e->lod, &lk, rp, pc, ip);
        if (st != SRMECH_OK) { return st; }
    }
    {
        size_t po = (size_t)s * cells;
        st = qalg_nullspace_of(e, &e->pwn[po], &e->pwd[po], n,
                               e->can, e->cad, &ck, rp, pc, ip);
        if (st != SRMECH_OK) { return st; }
    }
    for (ci = 0; ci < ck && picked < need; ci++) {
        size_t co = (size_t)ci * vc;
        int indep = 0;
        st = qalg_cand_independent(e, &e->can[co], &e->cad[co], lk,
                                   out_n, out_d, *vi, &indep, rp, pc, ip);
        if (st != SRMECH_OK) { return st; }
        if (!indep) { continue; }
        st = qalg_build_chain(e, out_n, out_d, *vi, &e->can[co], &e->cad[co],
                              s, n);
        if (st != SRMECH_OK) { return st; }
        out_bs[*nc] = s;
        *vi += s;
        *nc += 1;
        picked++;
    }
    if (picked != need) { return SRMECH_ERR_BAD_INPUT; }
    return SRMECH_OK;
}

/* Carve the jordan-chain matrix buffers from the caller arena, AFTER the shared
 * qalg_eng_carve (field scratch + Mn); the poly-op tail e->pws shrinks to the
 * remainder (still >= srmech_poly_ws_bound by the jordan ws bound's design). */
static srmech_status_t qalg_jordan_carve(qalg_eng_t *e, void *ws, size_t ws_len)
{
    uint32_t *base;
    size_t words, cur = 0u, dg, cells, colcols, powcells;
    uint32_t cap;
    int ok = 1;
    srmech_status_t st = qalg_eng_carve(e, ws, ws_len);
    assert(e != NULL);
    assert(ws != NULL || ws_len == 0u);
    if (st != SRMECH_OK) { return st; }
    base = (uint32_t *)e->pws;
    words = e->pws_len / sizeof(uint32_t);
    dg = (size_t)e->deg; cap = e->cap;
    cells = (size_t)e->n * (size_t)e->n * dg;
    colcols = (size_t)e->cn_cols;
    powcells = (size_t)e->powcap * cells;
    e->Nn = qalg_carve(base, words, &cur, cells, cap, &ok);
    e->Nd = qalg_carve(base, words, &cur, cells, cap, &ok);
    e->tn = qalg_carve(base, words, &cur, cells, cap, &ok);
    e->td = qalg_carve(base, words, &cur, cells, cap, &ok);
    e->sn = qalg_carve(base, words, &cur, cells, cap, &ok);
    e->sd = qalg_carve(base, words, &cur, cells, cap, &ok);
    e->lon = qalg_carve(base, words, &cur, cells, cap, &ok);
    e->lod = qalg_carve(base, words, &cur, cells, cap, &ok);
    e->can = qalg_carve(base, words, &cur, cells, cap, &ok);
    e->cad = qalg_carve(base, words, &cur, cells, cap, &ok);
    e->cn = qalg_carve(base, words, &cur, (size_t)e->n * colcols * dg, cap, &ok);
    e->cd = qalg_carve(base, words, &cur, (size_t)e->n * colcols * dg, cap, &ok);
    e->pwn = qalg_carve(base, words, &cur, powcells, cap, &ok);
    e->pwd = qalg_carve(base, words, &cur, powcells, cap, &ok);
    e->van = qalg_carve(base, words, &cur, (size_t)e->n * dg, cap, &ok);
    e->vad = qalg_carve(base, words, &cur, (size_t)e->n * dg, cap, &ok);
    e->jp0n = qalg_carve(base, words, &cur, dg, cap, &ok);
    e->jp0d = qalg_carve(base, words, &cur, dg, cap, &ok);
    e->jp1n = qalg_carve(base, words, &cur, dg, cap, &ok);
    e->jp1d = qalg_carve(base, words, &cur, dg, cap, &ok);
    if (!ok) { return SRMECH_ERR_OVERFLOW; }
    e->pws = (void *)(base + cur);
    e->pws_len = (words - cur) * sizeof(uint32_t);
    return SRMECH_OK;
}

/* ---- jordan public API --------------------------------------------- */

/* Per-coefficient limb cap for the out_n / out_d chain-vector coordinates. */
size_t srmech_jordan_chains_entry_cap(size_t coeff_limbs, int n, int deg)
{
    assert(n >= 0);
    assert(deg >= 0);
    if (n < 1 || deg < 1) { return 1u; }
    return qalg_cap_for(coeff_limbs, n, deg);
}

/* Minimum ws_len BYTES for srmech_jordan_chains: the eigvec arena bound (field
 * scratch + Mn + a poly tail) PLUS the jordan matrix buffers (N, matmul temp,
 * RREF scratch, lower/cand null, column-rank scratch, the n+2 stored powers,
 * matvec temp, field temps). */
size_t srmech_jordan_chains_ws_bound(size_t coeff_limbs, int n, int deg)
{
    size_t base, cap, dg, cells, hdr, slots, powcap, colcols, extra;
    assert(n >= 0);
    assert(deg >= 0);
    if (n < 1 || deg < 1) { return 64u; }
    base = srmech_eigvec_exact_ws_bound(coeff_limbs, n, deg);
    cap = qalg_cap_for(coeff_limbs, n, deg);
    dg = (size_t)deg;
    cells = (size_t)n * (size_t)n * dg;
    powcap = (size_t)n + 2u;
    colcols = 2u * (size_t)n + 1u;
    hdr = (sizeof(srmech_bigint_t) + sizeof(uint32_t) - 1u) / sizeof(uint32_t);
    /* 5 cell-pairs (N, t, s, lo, ca) + col scratch (2·n·colcols·dg) + powers
     * (2·powcap·cells) + matvec (2·n·dg) + 2 field-temp pairs (4·dg). */
    slots = 10u * cells + 2u * (size_t)n * colcols * dg + 2u * powcap * cells
            + 2u * (size_t)n * dg + 4u * dg;
    extra = slots * (hdr + cap);
    return base + (extra + 64u) * sizeof(uint32_t);
}

/* The exact JORDAN CHAINS of the integer/rational matrix A (n·n, num/den) for
 * the algebraic eigenvalue λ = Σ lam[i]·αⁱ (α a root of the monic irreducible
 * integer m, deg+1 coeffs low->high). out_n/out_d receive *out_total generalized
 * eigenvectors (≤ n), each n components of deg ℚ(λ) coordinates, at
 * out[((v·n + comp)·deg + coeff)] — the chains CONCATENATED in build order
 * (block size p down to 1; each chain BOTTOM→TOP). out_block_sizes[0..*out_nchains)
 * receive the chain lengths in that same order (Σ = *out_total = μ). The caller
 * sizes out_n/out_d n·n·deg slots (each >= srmech_jordan_chains_entry_cap limbs)
 * and out_block_sizes n ints. n/deg in [1, QALG_JORDAN_MAX_DIM]; a non-monic /
 * out-of-range / REDUCIBLE m -> SRMECH_ERR_BAD_INPUT; a too-small arena / cap ->
 * SRMECH_ERR_OVERFLOW (the caller falls back to the byte-identical pure path).
 * Byte/structurally-identical to matrix_cascades.jordan_chains_exact; attested by
 * tests/test_qalg_jordan_c_rc164.py. Additive symbols -> ABI unchanged (3). */
/* Engine init + caller-arena carve + load m/λ + build N = A − λI (into e->Nn).
 * Split from srmech_jordan_chains to keep both functions <= 60 lines (Rule 4). */
static srmech_status_t qalg_jordan_prepare(qalg_eng_t *e,
                                           const srmech_bigint_t *a_n,
                                           const srmech_bigint_t *a_d, int n,
                                           const srmech_bigint_t *m, int deg,
                                           const srmech_bigint_t *lam_n,
                                           const srmech_bigint_t *lam_d,
                                           void *ws, size_t ws_len)
{
    srmech_status_t st;
    size_t cl, cm, cll, k, cells;
    assert(e != NULL && a_n != NULL && m != NULL);
    assert(lam_n != NULL && n >= 1 && deg >= 1);
    cl = qalg_input_limbs(a_n, (size_t)n * (size_t)n);
    cm = qalg_input_limbs(m, (size_t)(deg + 1));
    if (cm > cl) { cl = cm; }
    cll = qalg_input_limbs(lam_n, (size_t)deg);
    if (cll > cl) { cl = cll; }
    e->deg = deg; e->n = n;
    e->cap = (uint32_t)qalg_cap_for(cl, n, deg);
    e->sb = (size_t)(2 * deg + 2);
    e->powcap = n + 2;
    e->cn_cols = 2 * n + 1;
    st = qalg_jordan_carve(e, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    for (k = 0u; k < (size_t)(deg + 1); k++) {
        st = srmech_bigint_copy(&e->mn[k], &m[k]);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_set_i64(&e->md[k], 1);
        if (st != SRMECH_OK) { return st; }
    }
    st = qalg_copy_run(e->lamn, e->lamd, lam_n, lam_d, (size_t)deg);
    if (st != SRMECH_OK) { return st; }
    st = qalg_build_matrix(e, a_n, a_d);             /* e->Mn = A − λI */
    if (st != SRMECH_OK) { return st; }
    cells = (size_t)n * (size_t)n * (size_t)deg;
    return qalg_copy_run(e->Nn, e->Nd, e->Mn, e->Md, cells);   /* N = A − λI */
}

srmech_status_t srmech_jordan_chains(
        const srmech_bigint_t *a_n, const srmech_bigint_t *a_d, int n,
        const srmech_bigint_t *m, int deg,
        const srmech_bigint_t *lam_n, const srmech_bigint_t *lam_d,
        srmech_bigint_t *out_n, srmech_bigint_t *out_d, int *out_total,
        int *out_block_sizes, int *out_nchains, void *ws, size_t ws_len)
{
    qalg_eng_t e;
    srmech_status_t st;
    int rp[QALG_JORDAN_MAX_DIM];
    int pc[2 * QALG_JORDAN_MAX_DIM + 1];
    int ip[2 * QALG_JORDAN_MAX_DIM + 1];
    int ranks[QALG_JORDAN_MAX_DIM + 2];
    int nul[QALG_JORDAN_MAX_DIM + 2];
    int nblocks[QALG_JORDAN_MAX_DIM + 2];
    int p = 0, vi = 0, nc = 0, s;
    assert(out_total != NULL && out_nchains != NULL);
    assert(a_n != NULL && m != NULL && lam_n != NULL);
    if (a_n == NULL || a_d == NULL || m == NULL || lam_n == NULL
        || lam_d == NULL || out_n == NULL || out_d == NULL
        || out_total == NULL || out_block_sizes == NULL || out_nchains == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n < 1 || n > QALG_JORDAN_MAX_DIM || deg < 1
        || deg > QALG_JORDAN_MAX_DIM) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (m[deg].sign != 1 || m[deg].n != 1u || m[deg].limbs[0] != 1u) {
        return SRMECH_ERR_BAD_INPUT;                 /* m must be monic */
    }
    st = qalg_jordan_prepare(&e, a_n, a_d, n, m, deg, lam_n, lam_d, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    st = qalg_jordan_powers(&e, ranks, nul, &p, rp, pc, ip);
    if (st != SRMECH_OK) { return st; }
    qalg_block_counts(ranks, p, nblocks);
    for (s = p; s >= 1; s--) {
        int need = nblocks[s];
        if (need == 0) { continue; }
        st = qalg_topdown_s(&e, s, need, out_n, out_d, out_block_sizes,
                            &vi, &nc, rp, pc, ip);
        if (st != SRMECH_OK) { return st; }
    }
    *out_total = vi;
    *out_nchains = nc;
    return SRMECH_OK;
}
