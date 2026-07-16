/*
 * srmech_riemann_theta_multisum.c -- the 1:1 native C peer of
 * srmech.amsc.riemann_theta_multisum.{riemann_theta_multisum_lhs,
 * multivariate_riemann_theta_sum} (rc232), the HIGHER-GENUS (genus-g Riemann
 * theta) multisum reduction-row builders: the exact ThetaBracketSum construction
 * of the LEFT-hand side (the n+1-term multisum) and the closed-form RIGHT-hand
 * side (PROD g_k - PROD h_k) of Spiridonov's multiparameter summation formula.
 *
 * A C-MIRROR PARITY build (NOT a new algorithm): it constructs the EXACT
 * bracket-product MONOMIALS the already-shipped pure-Python _lhs_py / _rhs_py
 * build, byte-for-byte; the Python side folds them into the ThetaBracketSum
 * (combining like monomials + coeffs), exactly as srmech_an_vwp_multisum_lhs
 * returns its per-composition terms for the Python carrier to sum.
 *
 * The identity (MPM-verified at build from the extracted arXiv source, PDF
 * sha256 8478af7407d26d0b0504d381cbe3c32a00f950c3b0c6ab8001a023b7e0c4c319:
 * V. P. Spiridonov, "A multiparameter summation formula for Riemann theta
 * functions", arXiv:math/0408366v2 [math.CA] (2004); Contemp. Math. 417 (2006),
 * 345-353, the Theorem, Eq. sum): with the genus-g odd theta [u] ([-u] = -[u]),
 * v(a,b) the abelian integral (path-additive), and per point-tuple k the three
 * 4-bracket products
 *   g_k = [z, z+v(a,c)+v(b,d), v(c,d), v(a,b)]
 *   h_k = [z+v(a,c), z+v(b,d), v(c,b), v(a,d)]
 *   L_k = [z+v(b,c), z+v(a,d), v(a,c), v(b,d)]   (Fay: L_k = g_k - h_k)
 *
 *   LHS (side 0) = SUM_{k=0}^n  L_k * PROD_{j<k} g_j * PROD_{j>k} h_j    (n+1 monomials)
 *   RHS (side 1) = PROD_{k=0}^n g_k  -  PROD_{k=0}^n h_k                 (2 monomials)
 *
 * Each monomial has exactly nb = 4*(n+1) brackets. The additive genus-g argument
 * u is carried as an int32 exponent row over the interned symbol table (Python
 * sorted-symbol-NAME order): additive '+' is row addition, v(a,b) = -P_a + P_b is
 * row axpy, and the odd-theta antisymmetry [-u] = -[u] is canonicalized by
 * orienting the row so its FIRST NONZERO entry (index order == name order) is
 * NEGATIVE, folding a Class-K +-1 sign into the monomial coeff (never abs()).
 * The all-zero argument is the zero bracket [0]=0 (kills the whole monomial).
 *
 * Wire form: `n_syms` the interned symbol dimension; `n` the summation ceiling
 * (n+1 point-tuples); `side` 0 = LHS, 1 = RHS. `z_exps_flat` = int32[(n+1)*n_syms]
 * the z-vector rows; `pt_exps_flat` = int32[(n+1)*4*n_syms] the point rows (per k
 * the four rows a,b,c,d). Output: `out_coeff[m]` the m-th monomial's coeff (+-1
 * before the Python combine); `out_args_flat` the m-th monomial's nb canonical
 * argument rows appended flat (nb*n_syms int32 per monomial, in build order --
 * the Python rebuild re-sorts). `*out_n_monos` = monomials emitted (a zero-bracket
 * monomial is skipped); `*out_nb` = nb. `max_monos` the caller's monomial capacity;
 * too small -> SRMECH_ERR_OVERFLOW. n_syms == 0 or a NULL required pointer ->
 * SRMECH_ERR_NULL_ARG; side not in {0,1} -> SRMECH_ERR_BAD_INPUT.
 *
 * Malloc-free (JPL Rule 3): builds each argument in place in the output buffer,
 * canonicalizes in place -- NO scratch arena. Sign travels in the Class-K coeff
 * branch, never abs()/fabs(). No libm, no <complex.h>. Self-contained (no
 * srmech_bigint / ellbase dependency -- the coeffs are +-1 and the exponents are
 * small ints). Additive symbol -> ABI unchanged (stays 4). License: MIT.
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto/recursion): OK -- iterative, flat static helpers
 *   - Rule 2 (bounded loops)    : OK -- bounded by n / n_syms / nb
 *   - Rule 3 (no malloc)        : OK -- writes into the caller output buffer only
 *   - Rule 4 (<=60 lines/func)  : OK -- factored into static helpers
 *   - Rule 5 (>=2 asserts/fn)   : OK -- entry-pointer + pre/postcondition
 *   - Rule 7 (return-value)     : OK -- srmech_status_t propagated
 *   - Rule 8 (no multi-line mac): OK -- no function-like macros
 *   - Rule 10 (warnings clean)  : OK under -Wall -Wextra -Wpedantic -Werror
 */

#include "srmech.h"

#include <assert.h>
#include <stddef.h>
#include <stdint.h>

/* dst[0..n_syms) := 0. */
static void rtm_row_zero(int32_t *dst, size_t n_syms)
{
    size_t i;
    assert(dst != NULL);
    assert(n_syms >= 1u);
    for (i = 0; i < n_syms; i++) { dst[i] = 0; }
}

/* dst += s * src  (row axpy; s in {-1,0,+1} — s == 0 is a no-op, used by the
 * pure-[z] bracket whose argument carries no point contribution). */
static void rtm_row_axpy(int32_t *dst, const int32_t *src, int32_t s, size_t n_syms)
{
    size_t i;
    assert(dst != NULL && src != NULL);
    assert(s == 0 || s == 1 || s == -1);
    for (i = 0; i < n_syms; i++) { dst[i] += s * src[i]; }
}

/* Canonicalize the odd-theta argument row IN PLACE: [-u] = -[u], oriented so the
 * FIRST NONZERO entry (index order) is NEGATIVE. Returns the Class-K +-1 sign
 * (never abs()), or 0 for the all-zero (zero-bracket) argument. */
static int rtm_canon(int32_t *row, size_t n_syms)
{
    size_t i;
    size_t i0 = n_syms;
    assert(row != NULL);
    assert(n_syms >= 1u);
    for (i = 0; i < n_syms; i++) {
        if (row[i] != 0) { i0 = i; break; }
    }
    if (i0 == n_syms) { return 0; }             /* all-zero -> [0] = 0            */
    if (row[i0] > 0) {                          /* first nonzero positive -> flip */
        for (i = 0; i < n_syms; i++) { row[i] = -row[i]; }
        return -1;
    }
    return 1;
}

/* Emit ONE bracket argument u = z + s_a*P_a + s_b*P_b (+ optional s_c*P_c + s_d*P_d)
 * into out_args[slot], canonicalize it, multiply *sign by its antisymmetry sign;
 * a zero bracket sets *iszero = 1. `z` may be NULL (a pure v(.,.) argument). */
static void rtm_emit_arg(int32_t *out_args, size_t slot, int64_t *sign, int *iszero,
                         const int32_t *z, const int32_t *pa, int32_t sa,
                         const int32_t *pb, int32_t sb, const int32_t *pc, int32_t sc,
                         const int32_t *pd, int32_t sd, size_t n_syms)
{
    int32_t *dst = out_args + slot * n_syms;
    int sg;
    assert(out_args != NULL && sign != NULL && iszero != NULL);
    assert(pa != NULL && pb != NULL);
    rtm_row_zero(dst, n_syms);
    if (z != NULL) { rtm_row_axpy(dst, z, 1, n_syms); }
    rtm_row_axpy(dst, pa, sa, n_syms);
    rtm_row_axpy(dst, pb, sb, n_syms);
    if (pc != NULL) { rtm_row_axpy(dst, pc, sc, n_syms); }
    if (pd != NULL) { rtm_row_axpy(dst, pd, sd, n_syms); }
    sg = rtm_canon(dst, n_syms);
    if (sg == 0) { *iszero = 1; } else { *sign *= (int64_t)sg; }
}

/* The four g_k brackets [z, z+v(a,c)+v(b,d), v(c,d), v(a,b)] into out at *slot. */
static void rtm_emit_g(int32_t *out_args, size_t *slot, int64_t *sign, int *iszero,
                       const int32_t *z, const int32_t *a, const int32_t *b,
                       const int32_t *c, const int32_t *d, size_t n_syms)
{
    assert(out_args != NULL && slot != NULL);
    assert(z != NULL && a != NULL && b != NULL && c != NULL && d != NULL);
    rtm_emit_arg(out_args, *slot, sign, iszero, z, a, 0, a, 0, NULL, 0, NULL, 0, n_syms);
    (*slot)++;                                              /* [z]                */
    rtm_emit_arg(out_args, *slot, sign, iszero, z, a, -1, c, 1, b, -1, d, 1, n_syms);
    (*slot)++;                                              /* [z+v(a,c)+v(b,d)]  */
    rtm_emit_arg(out_args, *slot, sign, iszero, NULL, c, -1, d, 1, NULL, 0, NULL, 0, n_syms);
    (*slot)++;                                              /* [v(c,d)]           */
    rtm_emit_arg(out_args, *slot, sign, iszero, NULL, a, -1, b, 1, NULL, 0, NULL, 0, n_syms);
    (*slot)++;                                              /* [v(a,b)]           */
}

/* The four h_k brackets [z+v(a,c), z+v(b,d), v(c,b), v(a,d)] into out at *slot. */
static void rtm_emit_h(int32_t *out_args, size_t *slot, int64_t *sign, int *iszero,
                       const int32_t *z, const int32_t *a, const int32_t *b,
                       const int32_t *c, const int32_t *d, size_t n_syms)
{
    assert(out_args != NULL && slot != NULL);
    assert(z != NULL && a != NULL && b != NULL && c != NULL && d != NULL);
    rtm_emit_arg(out_args, *slot, sign, iszero, z, a, -1, c, 1, NULL, 0, NULL, 0, n_syms);
    (*slot)++;                                              /* [z+v(a,c)]         */
    rtm_emit_arg(out_args, *slot, sign, iszero, z, b, -1, d, 1, NULL, 0, NULL, 0, n_syms);
    (*slot)++;                                              /* [z+v(b,d)]         */
    rtm_emit_arg(out_args, *slot, sign, iszero, NULL, c, -1, b, 1, NULL, 0, NULL, 0, n_syms);
    (*slot)++;                                              /* [v(c,b)]           */
    rtm_emit_arg(out_args, *slot, sign, iszero, NULL, a, -1, d, 1, NULL, 0, NULL, 0, n_syms);
    (*slot)++;                                              /* [v(a,d)]           */
}

/* The four L_k brackets [z+v(b,c), z+v(a,d), v(a,c), v(b,d)] into out at *slot. */
static void rtm_emit_l(int32_t *out_args, size_t *slot, int64_t *sign, int *iszero,
                       const int32_t *z, const int32_t *a, const int32_t *b,
                       const int32_t *c, const int32_t *d, size_t n_syms)
{
    assert(out_args != NULL && slot != NULL);
    assert(z != NULL && a != NULL && b != NULL && c != NULL && d != NULL);
    rtm_emit_arg(out_args, *slot, sign, iszero, z, b, -1, c, 1, NULL, 0, NULL, 0, n_syms);
    (*slot)++;                                              /* [z+v(b,c)]         */
    rtm_emit_arg(out_args, *slot, sign, iszero, z, a, -1, d, 1, NULL, 0, NULL, 0, n_syms);
    (*slot)++;                                              /* [z+v(a,d)]         */
    rtm_emit_arg(out_args, *slot, sign, iszero, NULL, a, -1, c, 1, NULL, 0, NULL, 0, n_syms);
    (*slot)++;                                              /* [v(a,c)]           */
    rtm_emit_arg(out_args, *slot, sign, iszero, NULL, b, -1, d, 1, NULL, 0, NULL, 0, n_syms);
    (*slot)++;                                              /* [v(b,d)]           */
}

/* Pointers into the k-th point-tuple's four rows a,b,c,d. */
static void rtm_pts(const int32_t *pt_exps_flat, size_t k, size_t n_syms,
                    const int32_t **a, const int32_t **b, const int32_t **c,
                    const int32_t **d)
{
    const int32_t *base = pt_exps_flat + k * 4u * n_syms;
    assert(pt_exps_flat != NULL);
    assert(a != NULL && b != NULL && c != NULL && d != NULL);
    *a = base;
    *b = base + n_syms;
    *c = base + 2u * n_syms;
    *d = base + 3u * n_syms;
}

/* Build the LHS summand `kk` = L_kk * PROD_{j<kk} g_j * PROD_{j>kk} h_j into
 * out_args (nb brackets), returning the net Class-K coeff (0 if a zero bracket). */
static int64_t rtm_lhs_summand(const int32_t *z_exps_flat, const int32_t *pt_exps_flat,
                               size_t n, size_t kk, size_t n_syms, int32_t *out_args)
{
    size_t j;
    size_t slot = 0;
    int64_t sign = 1;
    int iszero = 0;
    const int32_t *a;
    const int32_t *b;
    const int32_t *c;
    const int32_t *d;
    assert(z_exps_flat != NULL && out_args != NULL);
    assert(kk <= n);
    rtm_pts(pt_exps_flat, kk, n_syms, &a, &b, &c, &d);
    rtm_emit_l(out_args, &slot, &sign, &iszero, z_exps_flat + kk * n_syms, a, b, c, d, n_syms);
    for (j = 0; j < kk; j++) {
        rtm_pts(pt_exps_flat, j, n_syms, &a, &b, &c, &d);
        rtm_emit_g(out_args, &slot, &sign, &iszero, z_exps_flat + j * n_syms, a, b, c, d, n_syms);
    }
    for (j = kk + 1u; j <= n; j++) {
        rtm_pts(pt_exps_flat, j, n_syms, &a, &b, &c, &d);
        rtm_emit_h(out_args, &slot, &sign, &iszero, z_exps_flat + j * n_syms, a, b, c, d, n_syms);
    }
    assert(slot == 4u * (n + 1u));
    return iszero ? 0 : sign;
}

/* Build the RHS product `which` (0 = PROD g, 1 = PROD h) into out_args (nb
 * brackets), returning the net Class-K coeff (0 if a zero bracket). */
static int64_t rtm_rhs_product(const int32_t *z_exps_flat, const int32_t *pt_exps_flat,
                               size_t n, int which, size_t n_syms, int32_t *out_args)
{
    size_t k;
    size_t slot = 0;
    int64_t sign = 1;
    int iszero = 0;
    const int32_t *a;
    const int32_t *b;
    const int32_t *c;
    const int32_t *d;
    assert(z_exps_flat != NULL && out_args != NULL);
    assert(which == 0 || which == 1);
    for (k = 0; k <= n; k++) {
        rtm_pts(pt_exps_flat, k, n_syms, &a, &b, &c, &d);
        if (which == 0) {
            rtm_emit_g(out_args, &slot, &sign, &iszero, z_exps_flat + k * n_syms, a, b, c, d, n_syms);
        } else {
            rtm_emit_h(out_args, &slot, &sign, &iszero, z_exps_flat + k * n_syms, a, b, c, d, n_syms);
        }
    }
    assert(slot == 4u * (n + 1u));
    return iszero ? 0 : sign;
}

srmech_status_t srmech_riemann_theta_multisum(
    size_t n_syms, size_t n, int side,
    const int32_t *z_exps_flat, const int32_t *pt_exps_flat,
    int64_t *out_coeff, int32_t *out_args_flat, size_t max_monos,
    size_t *out_n_monos, size_t *out_nb)
{
    size_t nb;
    size_t stride;
    size_t m = 0;
    size_t kk;
    int64_t coeff;
    assert(out_n_monos != NULL && out_nb != NULL);
    assert(out_coeff != NULL && out_args_flat != NULL);
    if (n_syms == 0u || z_exps_flat == NULL || pt_exps_flat == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (out_coeff == NULL || out_args_flat == NULL || out_n_monos == NULL
        || out_nb == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (side != 0 && side != 1) { return SRMECH_ERR_BAD_INPUT; }
    nb = 4u * (n + 1u);
    stride = nb * n_syms;
    *out_nb = nb;
    if (side == 0) {
        for (kk = 0; kk <= n; kk++) {
            if (m >= max_monos) { return SRMECH_ERR_OVERFLOW; }
            coeff = rtm_lhs_summand(z_exps_flat, pt_exps_flat, n, kk, n_syms,
                                    out_args_flat + m * stride);
            if (coeff != 0) { out_coeff[m] = coeff; m++; }
        }
    } else {
        if (2u > max_monos) { return SRMECH_ERR_OVERFLOW; }
        coeff = rtm_rhs_product(z_exps_flat, pt_exps_flat, n, 0, n_syms,
                                out_args_flat + m * stride);
        if (coeff != 0) { out_coeff[m] = coeff; m++; }
        coeff = rtm_rhs_product(z_exps_flat, pt_exps_flat, n, 1, n_syms,
                                out_args_flat + m * stride);
        if (coeff != 0) { out_coeff[m] = -coeff; m++; }   /* the subtraction ∏g − ∏h */
    }
    *out_n_monos = m;
    return SRMECH_OK;
}
