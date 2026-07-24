/*
 * srmech_laplacian.c — Class L primitive: graph Laplacian.
 *
 * Task #217 Phase C1 second ship — four load-bearing graph-Laplacian
 * operations on dense row-major double matrices. Class L is the
 * structural workhorse of Spike #24 (instantiated at six of six bonus
 * substrates per the cumulative cross-substrate audit) and the
 * spectral substrate underpinning cascade-composition mass-spectrum
 * reproduction (bonus 10 SUCCESS at log-L2 = 0.614 dex).
 *
 * Pi-free implementation per [[user_stance_pi_as_projection]]: this
 * Class L surface does NOT use pi anywhere. Cyclic-graph closed-form
 * spectra (which classically read λ_k = 2(1−cos(2πk/n))) are NOT
 * shipped in C — those are downstream projections of the integer-
 * cyclic upstream that Class I represents. Class L here is strict
 * graph-Laplacian construction + symmetric Jacobi eigendecomposition
 * via algebraic c/s computation (no trig calls).
 *
 * Public API:
 *   - srmech_graph_dense_adjacency      (build A from edge list)
 *   - srmech_graph_dense_laplacian      (L = D − A)
 *   - srmech_graph_normalized_laplacian (L_sym = I − D^(−1/2) A D^(−1/2))
 *   - srmech_jacobi_eigvals             (symmetric Jacobi, bounded n)
 *
 * Conventions:
 *   - Matrices are row-major n×n doubles (caller-allocated).
 *   - Edge lists are parallel uint32 arrays (edges_u, edges_v) +
 *     optional double weights. NULL weights → unit weights.
 *   - The construction operations overwrite the output buffer; for
 *     `srmech_graph_dense_laplacian` the user supplies the same
 *     buffer for adjacency build-up and final L (in-place transform).
 *   - Jacobi takes its matrix in-place; the diagonal at exit holds
 *     the eigenvalues. Eigvals are also copied to a dedicated output.
 *   - No node cap: every graph op writes only into the caller's matrix
 *     (degree / row-scaling are computed per-row or stashed in the
 *     diagonal; Jacobi rotates in place), so the bound is the caller's
 *     RAM, not a compiled limit (standalone-complete honor).
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto)        : OK
 *   - Rule 2 (bounded loops)  : OK — every loop bounded by either a
 *                              caller-supplied size_t (n / n_edges,
 *                              caller's responsibility) or by
 *                              SRMECH_LAPLACIAN_JACOBI_MAX_SWEEPS
 *   - Rule 3 (no malloc)      : OK — caller buffers + scalar locals (plus
 *                              a thread-local static eig scratch); no malloc
 *   - Rule 4 (≤60 lines/func) : OK — Jacobi split into rotation +
 *                              sweep helpers
 *   - Rule 5 (≥2 asserts/fn)  : OK
 *   - Rule 7 (return-value)   : OK — srmech_status_t throughout
 *   - Rule 10 (warnings clean): OK under -Wall -Wextra -Wpedantic
 *
 * License: MIT.
 */

#include "srmech.h"
#include "srmech_platform.h"   /* §52 Part 2: PAL streaming-read for the out-of-core Fiedler */

#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>             /* snprintf — rc284 tome/queue path building (pure string
                                * formatting; all OS I/O still goes through the PAL) */
#include <string.h>            /* memcpy — parse packed edge records (no aliasing UB) */

/* BYTE-EXACT parity contract (rc309): quaternion_cycle_holonomy's per-cycle
 * quaternion product must match the pure-Python mirror's float-op ORDER, so
 * FMA contraction must be OFF (a fused multiply-add rounds once where mul+add
 * round twice). GCC -std=c11 defaults to off; CLANG defaults to ON (the macOS
 * arm64 CI cell diverged in the rc309 holonomy accumulation, exactly as rc110's
 * DFT did — see srmech_quaternion.c), so the C11 pragma is applied for clang. */
#if defined(__clang__)
#pragma STDC FP_CONTRACT OFF
#endif


/* Class-N rational sqrt (srmech_rational_sqrt) — the native Jacobi eigensolver
 * computes its rotation-angle roots via the cascade, not libm (rc45,
 * C-transpile triality). All call sites pass provably non-negative args. */
static double lap_sqrt(double x)
{
    assert(x >= 0.0);
    double out = 0.0;
    (void)srmech_rational_sqrt(x, &out);
    assert(out >= 0.0);
    return out;
}

#define SRMECH_LAPLACIAN_JACOBI_MAX_SWEEPS 100

srmech_status_t srmech_graph_dense_adjacency(uint32_t        n,
                                             uint32_t        n_edges,
                                             const uint32_t *edges_u,
                                             const uint32_t *edges_v,
                                             const double   *weights,
                                             double         *out_matrix)
{
    assert(out_matrix != NULL);
    if (out_matrix == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n_edges > 0 && (edges_u == NULL || edges_v == NULL)) {
        return SRMECH_ERR_NULL_ARG;
    }
    /* Zero the n×n output. */
    size_t cells = (size_t)n * (size_t)n;
    for (size_t i = 0; i < cells; i++) {
        out_matrix[i] = 0.0;
    }
    /* Accumulate edges (undirected: A[u,v] += w and A[v,u] += w).
     * Self-loops add 2*w to the diagonal by this rule, matching the
     * standard graph-theory convention. */
    for (uint32_t e = 0; e < n_edges; e++) {
        uint32_t uu = edges_u[e];
        uint32_t vv = edges_v[e];
        if (uu >= n || vv >= n) {
            return SRMECH_ERR_BAD_INPUT;
        }
        double w = (weights != NULL) ? weights[e] : 1.0;
        /* Add w to both A[u, v] and A[v, u]. For self-loops (u == v),
         * this naturally accumulates 2*w on the diagonal — the
         * standard graph-theory convention (a self-loop contributes
         * to a vertex's degree by 2). */
        out_matrix[(size_t)uu * n + vv] += w;
        out_matrix[(size_t)vv * n + uu] += w;
    }
    assert(n == 0 || out_matrix != NULL);
    return SRMECH_OK;
}

/* Helper: compute row-sum degree from adjacency in `mat` row-major. */
static double srmech_laplacian_row_degree(uint32_t n,
                                          uint32_t row,
                                          const double *mat)
{
    assert(mat != NULL);
    assert(row < n);
    double sum = 0.0;
    for (uint32_t c = 0; c < n; c++) {
        if (c != row) {
            sum += mat[(size_t)row * n + c];
        }
    }
    return sum;
}

srmech_status_t srmech_graph_dense_laplacian(uint32_t        n,
                                             uint32_t        n_edges,
                                             const uint32_t *edges_u,
                                             const uint32_t *edges_v,
                                             const double   *weights,
                                             double         *out_matrix)
{
    assert(out_matrix != NULL);
    srmech_status_t st = srmech_graph_dense_adjacency(
        n, n_edges, edges_u, edges_v, weights, out_matrix);
    if (st != SRMECH_OK) {
        return st;
    }
    /* L = D − A, computed row-by-row: deg_r depends only on row r of A
     * (read before row r is overwritten), so there is NO per-node scratch
     * and no compiled node cap — the bound is the caller's out_matrix
     * (standalone-complete honor). */
    for (uint32_t r = 0; r < n; r++) {
        double deg = srmech_laplacian_row_degree(n, r, out_matrix);
        for (uint32_t c = 0; c < n; c++) {
            size_t idx = (size_t)r * n + c;
            out_matrix[idx] = (r == c) ? deg : -out_matrix[idx];
        }
    }
    assert(n == 0 || out_matrix != NULL);
    return SRMECH_OK;
}

srmech_status_t srmech_graph_normalized_laplacian(uint32_t        n,
                                                  uint32_t        n_edges,
                                                  const uint32_t *edges_u,
                                                  const uint32_t *edges_v,
                                                  const double   *weights,
                                                  double         *out_matrix)
{
    assert(out_matrix != NULL);
    srmech_status_t st = srmech_graph_dense_adjacency(
        n, n_edges, edges_u, edges_v, weights, out_matrix);
    if (st != SRMECH_OK) {
        return st;
    }
    /* Stash d_i^(−1/2) IN the diagonal (which L_sym overwrites anyway), so
     * there is NO per-node scratch and no compiled node cap — the bound is
     * the caller's out_matrix (standalone-complete honor). The row-degree
     * reads off-diagonals only, so stashing on the diagonal is safe.
     * Isolated vertices (degree 0) → 0 (the normalised Laplacian's diagonal
     * is 0 there by convention). */
    for (uint32_t i = 0; i < n; i++) {
        double d = srmech_laplacian_row_degree(n, i, out_matrix);
        out_matrix[(size_t)i * n + i] = (d > 0.0) ? (1.0 / lap_sqrt(d)) : 0.0;
    }
    /* L_sym = I − D^(−1/2) A D^(−1/2): off-diagonals first (reading the
     * stashed d^(−1/2) from the diagonals, which this pass never writes),
     * then finalise the diagonal to {0, 1}. */
    for (uint32_t r = 0; r < n; r++) {
        double dr = out_matrix[(size_t)r * n + r];
        for (uint32_t c = 0; c < n; c++) {
            if (r != c) {
                size_t idx = (size_t)r * n + c;
                double dc = out_matrix[(size_t)c * n + c];
                out_matrix[idx] = -out_matrix[idx] * dr * dc;
            }
        }
    }
    for (uint32_t i = 0; i < n; i++) {
        size_t d = (size_t)i * n + i;
        out_matrix[d] = (out_matrix[d] != 0.0) ? 1.0 : 0.0;
    }
    assert(n == 0 || out_matrix != NULL);
    return SRMECH_OK;
}

/* ------------------------------------------------------------------
 * 0.9.0rc105 (issue #1234 Item 3 / F1006 / F1007): magnetic (Hermitian)
 * Laplacian of a directed graph — the standalone-C builder peer of
 * `laplacian.magnetic_laplacian`. See srmech.h for the two-mode wire
 * contract (scalar-q vs per-edge charges). The trig is the srmech Q61
 * cascade (srmech_cos_q61 / srmech_sin_q61), byte-exact with the pure-
 * Python Class-N cascade the Python path runs; the Q61 -> double
 * projection `(double)v / (double)SRMECH_Q61_ONE` is an exact power-of-
 * two scale of the rounded int64, bit-identical to Python's
 * `float(Q(v, 2**61))`. pi = 4 * atan_q61(1) — the SAME derivation the
 * Python module-level `_PI` uses (no libm, no M_PI).
 * ------------------------------------------------------------------ */

/* Zero the 2*n*n interleaved output and accumulate the DIRECTED
 * adjacency W[u,v] += w into the IMAGINARY slots (odd indices). Unlike
 * the undirected builder this does NOT mirror the transpose — direction
 * is preserved (W is generally asymmetric). The imag slots serve as the
 * W staging area so the scalar mode needs NO scratch arena (the final
 * imaginary pass rewrites them). */
static srmech_status_t lap_mag_build_w(uint32_t n, uint32_t n_edges,
                                       const uint32_t *eu, const uint32_t *ev,
                                       const double *w, double *out)
{
    assert(out != NULL);
    assert(n_edges == 0 || (eu != NULL && ev != NULL));
    size_t cells = 2u * (size_t)n * (size_t)n;
    for (size_t i = 0; i < cells; i++) {
        out[i] = 0.0;
    }
    for (uint32_t e = 0; e < n_edges; e++) {
        uint32_t uu = eu[e];
        uint32_t vv = ev[e];
        if (uu >= n || vv >= n) {
            return SRMECH_ERR_BAD_INPUT;
        }
        double we = (w != NULL) ? w[e] : 1.0;
        out[2u * ((size_t)uu * n + vv) + 1u] += we;
    }
    return SRMECH_OK;
}

/* Scalar-q mode pass 1: REAL parts + the degree diagonal. Reads W from
 * the intact imaginary slots; writes only real (even) slots. Mirrors the
 * Python row-major accumulation order (deg_r sums A_s[r,c] for c
 * ascending, INCLUDING c == r) so the float sums are bit-identical. */
static srmech_status_t lap_mag_scalar_real(uint32_t n, double two_pi_q,
                                           double *out)
{
    assert(out != NULL);
    for (uint32_t r = 0; r < n; r++) {
        double deg = 0.0;
        for (uint32_t c = 0; c < n; c++) {
            double wrc = out[2u * ((size_t)r * n + c) + 1u];
            double wcr = out[2u * ((size_t)c * n + r) + 1u];
            double a_s = 0.5 * (wrc + wcr);
            deg += a_s;
            if (c == r) {
                continue;   /* no self-phase; degree carries the diagonal */
            }
            int64_t cv = 0;
            srmech_status_t st = srmech_cos_q61(two_pi_q * (wrc - wcr), &cv);
            if (st != SRMECH_OK) {
                return st;
            }
            assert(cv >= -SRMECH_Q61_ONE && cv <= SRMECH_Q61_ONE);
            out[2u * ((size_t)r * n + c)] =
                -(a_s * ((double)cv / (double)SRMECH_Q61_ONE));
        }
        out[2u * ((size_t)r * n + r)] = deg;
    }
    return SRMECH_OK;
}

/* Scalar-q mode pass 2: IMAGINARY parts, pairwise (r < c). Each pair
 * reads BOTH W values from the still-intact imaginary slots before
 * overwriting them (the mirror cell's sine is computed independently,
 * exactly as the Python per-cell loop does — no evenness assumption on
 * the Q61 reduction). Diagonal imaginary = 0 (real degree). */
static srmech_status_t lap_mag_scalar_imag(uint32_t n, double two_pi_q,
                                           double *out)
{
    assert(out != NULL);
    for (uint32_t r = 0; r < n; r++) {
        for (uint32_t c = r + 1u; c < n; c++) {
            size_t irc = 2u * ((size_t)r * n + c) + 1u;
            size_t icr = 2u * ((size_t)c * n + r) + 1u;
            double wrc = out[irc];
            double wcr = out[icr];
            double a_s = 0.5 * (wrc + wcr);
            int64_t s_rc = 0;
            int64_t s_cr = 0;
            srmech_status_t st = srmech_sin_q61(two_pi_q * (wrc - wcr), &s_rc);
            if (st != SRMECH_OK) {
                return st;
            }
            st = srmech_sin_q61(two_pi_q * (wcr - wrc), &s_cr);
            if (st != SRMECH_OK) {
                return st;
            }
            assert(s_rc >= -SRMECH_Q61_ONE && s_rc <= SRMECH_Q61_ONE);
            out[irc] = -(a_s * ((double)s_rc / (double)SRMECH_Q61_ONE));
            out[icr] = -(a_s * ((double)s_cr / (double)SRMECH_Q61_ONE));
        }
        out[2u * ((size_t)r * n + r) + 1u] = 0.0;
    }
    return SRMECH_OK;
}

/* Per-edge CHIRAL mode (charges != NULL): each edge k = (u, v, w, c)
 * accumulates the conjugate Hermitian pair -(w/2)*e^{+i 2*pi*c} at
 * [u,v] and -(w/2)*e^{-i 2*pi*c} at [v,u]; the degree accumulates in
 * the DIAGONAL REAL slot (never touched by the off-diagonal phases, so
 * no scratch). Self-loops contribute w to the degree and no phase —
 * matching the scalar mode's diagonal convention. */
static srmech_status_t lap_mag_charges(uint32_t n, uint32_t n_edges,
                                       const uint32_t *eu, const uint32_t *ev,
                                       const double *w, const double *ch,
                                       double two_pi, double *out)
{
    assert(out != NULL);
    assert(n_edges == 0 || ch != NULL);
    size_t cells = 2u * (size_t)n * (size_t)n;
    for (size_t i = 0; i < cells; i++) {
        out[i] = 0.0;
    }
    for (uint32_t e = 0; e < n_edges; e++) {
        uint32_t uu = eu[e];
        uint32_t vv = ev[e];
        if (uu >= n || vv >= n) {
            return SRMECH_ERR_BAD_INPUT;
        }
        double we = (w != NULL) ? w[e] : 1.0;
        double hw = 0.5 * we;
        out[2u * ((size_t)uu * n + uu)] += hw;   /* deg[u] (diagonal real) */
        out[2u * ((size_t)vv * n + vv)] += hw;   /* deg[v] */
        if (uu == vv) {
            continue;   /* no self-phase; degree carries the diagonal */
        }
        int64_t cv = 0;
        int64_t sv = 0;
        srmech_status_t st = srmech_cos_q61(two_pi * ch[e], &cv);
        if (st != SRMECH_OK) {
            return st;
        }
        st = srmech_sin_q61(two_pi * ch[e], &sv);
        if (st != SRMECH_OK) {
            return st;
        }
        double re = (double)cv / (double)SRMECH_Q61_ONE;
        double im = (double)sv / (double)SRMECH_Q61_ONE;
        out[2u * ((size_t)uu * n + vv)] += -(hw * re);
        out[2u * ((size_t)uu * n + vv) + 1u] += -(hw * im);
        out[2u * ((size_t)vv * n + uu)] += -(hw * re);
        out[2u * ((size_t)vv * n + uu) + 1u] += hw * im;
    }
    return SRMECH_OK;
}

srmech_status_t srmech_graph_magnetic_laplacian(uint32_t        n,
                                                uint32_t        n_edges,
                                                const uint32_t *edges_u,
                                                const uint32_t *edges_v,
                                                const double   *weights,
                                                double          q,
                                                const double   *charges,
                                                double         *out_matrix)
{
    assert(out_matrix != NULL);
    if (out_matrix == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n_edges > 0 && (edges_u == NULL || edges_v == NULL)) {
        return SRMECH_ERR_NULL_ARG;
    }
    /* pi = 4 * atan_q61(1) — the exact derivation the Python module-level
     * _PI uses (4 * float(Q(atan_q61(1), 2^61))); no libm M_PI. */
    int64_t atan1 = 0;
    srmech_status_t st = srmech_atan_q61(1.0, &atan1);
    if (st != SRMECH_OK) {
        return st;
    }
    double pi = 4.0 * ((double)atan1 / (double)SRMECH_Q61_ONE);
    assert(pi > 3.0 && pi < 3.3);
    if (charges != NULL) {
        return lap_mag_charges(n, n_edges, edges_u, edges_v, weights,
                               charges, 2.0 * pi, out_matrix);
    }
    st = lap_mag_build_w(n, n_edges, edges_u, edges_v, weights, out_matrix);
    if (st != SRMECH_OK) {
        return st;
    }
    double two_pi_q = 2.0 * pi * q;
    st = lap_mag_scalar_real(n, two_pi_q, out_matrix);
    if (st != SRMECH_OK) {
        return st;
    }
    return lap_mag_scalar_imag(n, two_pi_q, out_matrix);
}

/* ------------------------------------------------------------------
 * 0.9.0rc229 (#687): the V4-gain (Klein-4-sector) Laplacian — the
 * EVEN-channel fuller partner of srmech_graph_magnetic_laplacian. Each
 * edge carries a V4 = Z2 x Z2 gain g = (g0, g1) — TWO sign bits, packed
 * low..high in a uint8 in {0,1,2,3}. V4 has FOUR real characters
 * chi_ab(g) = (-1)^(a*g0 + b*g1), (a,b) in {0,1}^2, so the object
 * decomposes into FOUR real signed Laplacians L_chi = D_bar - chi(g_e)*A
 * — the two-bit generalization of the one-bit signed Laplacian. `out` is
 * 4*n*n doubles, SECTOR-major: sector k in {0,1,2,3} = (a = k>>1, b = k&1)
 * occupies out[k*n*n ...], so k=0 -> chi00 (trivial), 1 -> chi01,
 * 2 -> chi10, 3 -> chi11, each real row-major n*n. The two gain bits are
 * treated SYMMETRICALLY (no bit is privileged). The signed degree
 * D_bar_ii = sum_{j != i} |A_ij| uses the Class-K magnitude sign-branch
 * (a >= 0 ? a : -a) — NOT an ALU abs(); |chi*w| = |w|, so the degree is
 * character-INDEPENDENT (same across the four sectors).
 *
 * No node cap, NO scratch: the signed adjacency is staged in each sector
 * block then converted to L = D - A in place per row (the caller's `out`
 * is the only buffer). An out-of-range endpoint or a gain > 3 ->
 * SRMECH_ERR_BAD_INPUT. ABI-additive: a new symbol, SRMECH_ABI_VERSION
 * stays 4.
 * ------------------------------------------------------------------ */

/* Character sign chi_ab(g) in {+1,-1}: parity of (a & g0) ^ (b & g1). */
static int klein4_char_sign(unsigned a, unsigned b, uint8_t g)
{
    assert(a <= 1u && b <= 1u);
    assert(g <= 3u);
    unsigned g0 = (unsigned)(g & 1u);
    unsigned g1 = (unsigned)((g >> 1) & 1u);
    unsigned p = (a & g0) ^ (b & g1);
    return (p != 0u) ? -1 : 1;
}

/* Convert one sector's signed adjacency block A (row-major n*n) into the
 * signed Laplacian L = D_bar - A in place. D_bar_ii = sum_{c != i} |A_ic|
 * via the Class-K magnitude sign-branch (no abs()); off-diag L = -A. */
static void klein4_laplacianize_block(uint32_t n, double *blk)
{
    assert(blk != NULL);
    for (uint32_t r = 0; r < n; r++) {
        double deg = 0.0;
        for (uint32_t c = 0; c < n; c++) {
            if (c == r) {
                continue;
            }
            double a = blk[(size_t)r * n + c];
            deg += (a >= 0.0) ? a : -a;   /* Class-K magnitude, not abs() */
            blk[(size_t)r * n + c] = -a;  /* L off-diag = -A */
        }
        blk[(size_t)r * n + r] = deg;
    }
    assert(n == 0 || blk != NULL);
}

srmech_status_t srmech_graph_klein4_gain_laplacian(uint32_t        n,
                                                   uint32_t        n_edges,
                                                   const uint32_t *edges_u,
                                                   const uint32_t *edges_v,
                                                   const double   *weights,
                                                   const uint8_t  *gains,
                                                   double         *out_matrix)
{
    assert(out_matrix != NULL);
    if (out_matrix == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n_edges > 0 && (edges_u == NULL || edges_v == NULL)) {
        return SRMECH_ERR_NULL_ARG;
    }
    size_t block = (size_t)n * (size_t)n;
    size_t cells = 4u * block;
    for (size_t i = 0; i < cells; i++) {
        out_matrix[i] = 0.0;
    }
    /* Accumulate the signed adjacency for all four sectors in one edge
     * loop (undirected: A[u,v] += s*w and A[v,u] += s*w; a self-loop lands
     * 2*s*w on the diagonal, which the degree pass drops). */
    for (uint32_t e = 0; e < n_edges; e++) {
        uint32_t uu = edges_u[e];
        uint32_t vv = edges_v[e];
        if (uu >= n || vv >= n) {
            return SRMECH_ERR_BAD_INPUT;
        }
        uint8_t g = (gains != NULL) ? gains[e] : 0u;
        if (g > 3u) {
            return SRMECH_ERR_BAD_INPUT;
        }
        double w = (weights != NULL) ? weights[e] : 1.0;
        for (unsigned k = 0; k < 4u; k++) {
            double sw = (double)klein4_char_sign(k >> 1, k & 1u, g) * w;
            double *blk = out_matrix + (size_t)k * block;
            blk[(size_t)uu * n + vv] += sw;
            blk[(size_t)vv * n + uu] += sw;
        }
    }
    for (unsigned k = 0; k < 4u; k++) {
        klein4_laplacianize_block(n, out_matrix + (size_t)k * block);
    }
    assert(n == 0 || out_matrix != NULL);
    return SRMECH_OK;
}

/* ------------------------------------------------------------------
 * 0.9.0rc229 (#687): cycle_holonomy — the ODD channel the (Hermitian /
 * signed) SPECTRUM provably cannot carry. A gain graph is determined up
 * to switching (node re-gauging) by its cycle gains (Zaslavsky, signed
 * graphs, DAM 4 (1982) 47-74). This computes exactly: a spanning forest
 * (union-find, first-encountered edge = tree edge) -> the fundamental
 * cycle for each co-tree edge -> that cycle's NET charge (per-edge
 * charges in TURNS, rational, reduced mod 1). It is Class I (mod-1
 * cyclic) o Class L (graph): exact int64-rational arithmetic, NO
 * eigensolve. The per-cycle holonomy is invariant under node re-gauging
 * (a coboundary telescopes around any cycle) and is 0 for every cycle
 * IFF the gain graph is balanced (Zaslavsky's balance criterion); a
 * genuine odd cycle-gain makes it nonzero, and it distinguishes +c from
 * -c (1/4 vs 3/4 mod 1) — the chirality the sector spectra CANNOT (a
 * conjugated Hermitian matrix has the same eigenvalues).
 *
 * Charges are per-edge reduced rationals (charge_num[e]/charge_den[e], in
 * turns); NULL arrays -> 0. Denominators must be positive and both
 * |charge_num| and charge_den <= SRMECH_HOLO_RAT_LIMIT (1e9) so the exact
 * int64 add/reduce cannot overflow; a magnitude past that, or an
 * intermediate whose reduced denominator would exceed the limit, returns
 * SRMECH_ERR_OVERFLOW (the pure-Python Fraction path is the exact
 * complete alternative). Outputs (each length >= n_edges): out_num/out_den
 * = the reduced holonomy in [0,1) per fundamental cycle; out_cycle_u/v =
 * the co-tree edge indexing each cycle; *out_n_cycles = the cyclomatic
 * number (n_edges - tree_edges). `ws` is a caller arena of at least
 * srmech_graph_cycle_holonomy_arena_bytes(n, n_edges) bytes (no malloc).
 * ABI-additive: new symbols, SRMECH_ABI_VERSION stays 4.
 * ------------------------------------------------------------------ */

#define SRMECH_HOLO_RAT_LIMIT ((int64_t)1000000000)

size_t srmech_graph_cycle_holonomy_arena_bytes(uint32_t n, uint32_t n_edges)
{
    /* int64: pot_num[n] + pot_den[n] + tnum[ne] + tden[ne] = 8*(2n + 2ne)
     * int32: parent[n] + rnk[n] + visited[n] + queue[n] + tu[ne] + tv[ne]
     *        = 4*(4n + 2ne). +64 alignment/padding slop. */
    size_t bn = (size_t)n;
    size_t be = (size_t)n_edges;
    size_t bytes = 8u * (2u * bn + 2u * be) + 4u * (4u * bn + 2u * be) + 64u;
    assert(bytes >= 64u);            /* always includes the alignment/pad slop */
    assert(bytes >= 16u * bn);       /* room for the int64 pot_num/pot_den[n] */
    return bytes;
}

/* Euclid gcd on non-negative int64 (bounded by the bit-width). */
static int64_t holo_gcd(int64_t a, int64_t b)
{
    assert(a >= 0);
    assert(b >= 0);
    while (b != 0) {
        int64_t t = a % b;
        a = b;
        b = t;
    }
    return a;
}

/* Canonicalize num/den: den > 0, gcd(|num|, den) == 1. */
static void holo_reduce(int64_t *num, int64_t *den)
{
    assert(num != NULL);
    assert(den != NULL && *den != 0);
    int64_t nu = *num;
    int64_t d = *den;
    if (d < 0) {              /* Class-K sign move to den > 0 */
        d = -d;
        nu = -nu;
    }
    int64_t an = (nu >= 0) ? nu : -nu;    /* |num| sign-branch, no abs() */
    int64_t g = holo_gcd(an, d);
    if (g > 1) {
        nu /= g;
        d /= g;
    }
    *num = nu;
    *den = d;
}

/* r = a/ad + b/bd (exact), reduced. Overflow-guarded against the int64
 * limit -> SRMECH_ERR_OVERFLOW. */
static srmech_status_t holo_add(int64_t an, int64_t ad, int64_t bn, int64_t bd,
                                int64_t *rn, int64_t *rd)
{
    assert(ad != 0 && bd != 0);
    assert(rn != NULL && rd != NULL);
    int64_t aan = (an >= 0) ? an : -an;
    int64_t abn = (bn >= 0) ? bn : -bn;
    if (ad > SRMECH_HOLO_RAT_LIMIT || bd > SRMECH_HOLO_RAT_LIMIT ||
        aan > SRMECH_HOLO_RAT_LIMIT || abn > SRMECH_HOLO_RAT_LIMIT) {
        return SRMECH_ERR_OVERFLOW;   /* fall to the exact pure path */
    }
    int64_t d = ad * bd;              /* <= 1e18, fits int64 */
    int64_t nu = an * bd + bn * ad;   /* |terms| <= 1e18 each, sum <= 2e18 */
    holo_reduce(&nu, &d);
    *rn = nu;
    *rd = d;
    return SRMECH_OK;
}

/* Reduce num/den into [0,1): num <- ((num mod den) + den) mod den. */
static void holo_mod1(int64_t *num, int64_t *den)
{
    assert(num != NULL);
    assert(den != NULL && *den > 0);
    int64_t r = *num % *den;
    if (r < 0) {
        r += *den;
    }
    *num = r;
    holo_reduce(num, den);
}

/* Union-find find with path halving (iterative, bounded by n). */
static uint32_t holo_find(int32_t *parent, uint32_t x)
{
    assert(parent != NULL);
    while ((uint32_t)parent[x] != x) {
        parent[x] = parent[(uint32_t)parent[x]];   /* halve */
        x = (uint32_t)parent[x];
    }
    assert((uint32_t)parent[x] == x);   /* the returned node is its own root */
    return x;
}

/* Build pot[i] = tree-path charge (root -> i) by BFS over the tree edges.
 * A tree edge (tu,tv) with charge tnum/tden means charge(tu -> tv) =
 * +tnum/tden. Returns SRMECH_ERR_OVERFLOW if any accumulation exceeds the
 * int64 rational limit. */
static srmech_status_t holo_build_pot(uint32_t n, uint32_t n_tree,
    const int32_t *tu, const int32_t *tv,
    const int64_t *tnum, const int64_t *tden,
    int64_t *pot_num, int64_t *pot_den, int32_t *visited, int32_t *queue)
{
    assert(pot_num != NULL && pot_den != NULL);
    assert(visited != NULL && queue != NULL);
    for (uint32_t i = 0; i < n; i++) {
        visited[i] = 0;
        pot_num[i] = 0;
        pot_den[i] = 1;
    }
    for (uint32_t s = 0; s < n; s++) {
        if (visited[s]) {
            continue;
        }
        uint32_t head = 0, tail = 0;
        visited[s] = 1;
        queue[tail++] = (int32_t)s;
        while (head < tail) {
            uint32_t x = (uint32_t)queue[head++];
            for (uint32_t e = 0; e < n_tree; e++) {
                uint32_t a = (uint32_t)tu[e];
                uint32_t b = (uint32_t)tv[e];
                uint32_t nb;
                int64_t cn;
                if (a == x && !visited[b]) {
                    nb = b; cn = tnum[e];        /* x -> nb: +charge */
                } else if (b == x && !visited[a]) {
                    nb = a; cn = -tnum[e];       /* x -> nb: -charge */
                } else {
                    continue;
                }
                srmech_status_t st = holo_add(pot_num[x], pot_den[x],
                                              cn, tden[e],
                                              &pot_num[nb], &pot_den[nb]);
                if (st != SRMECH_OK) {
                    return st;
                }
                visited[nb] = 1;
                queue[tail++] = (int32_t)nb;
            }
        }
    }
    return SRMECH_OK;
}

srmech_status_t srmech_graph_cycle_holonomy(uint32_t        n,
                                            uint32_t        n_edges,
                                            const uint32_t *edges_u,
                                            const uint32_t *edges_v,
                                            const int64_t  *charge_num,
                                            const int64_t  *charge_den,
                                            int64_t        *out_num,
                                            int64_t        *out_den,
                                            uint32_t       *out_cycle_u,
                                            uint32_t       *out_cycle_v,
                                            uint32_t       *out_n_cycles,
                                            void           *ws,
                                            size_t          ws_len)
{
    assert(out_n_cycles != NULL);
    if (out_n_cycles == NULL || ws == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n_edges > 0 && (edges_u == NULL || edges_v == NULL)) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (ws_len < srmech_graph_cycle_holonomy_arena_bytes(n, n_edges)) {
        return SRMECH_ERR_OVERFLOW;
    }
    /* Carve the arena: int64 arrays first (8-aligned base), then int32. */
    int64_t *pot_num = (int64_t *)ws;
    int64_t *pot_den = pot_num + n;
    int64_t *tnum = pot_den + n;
    int64_t *tden = tnum + n_edges;
    int32_t *parent = (int32_t *)(tden + n_edges);
    int32_t *rnk = parent + n;
    int32_t *visited = rnk + n;
    int32_t *queue = visited + n;
    int32_t *tu = queue + n;
    int32_t *tv = tu + n_edges;
    for (uint32_t i = 0; i < n; i++) {
        parent[i] = (int32_t)i;
        rnk[i] = 0;
    }
    /* Union-find pass: first-encountered spanning edge = tree edge; a
     * spanning cycle-closing edge = co-tree edge (a fundamental cycle). */
    uint32_t n_tree = 0;
    uint32_t n_cyc = 0;
    for (uint32_t e = 0; e < n_edges; e++) {
        uint32_t uu = edges_u[e];
        uint32_t vv = edges_v[e];
        if (uu >= n || vv >= n) {
            return SRMECH_ERR_BAD_INPUT;
        }
        int64_t cn = (charge_num != NULL) ? charge_num[e] : 0;
        int64_t cd = (charge_den != NULL) ? charge_den[e] : 1;
        if (cd == 0) {
            return SRMECH_ERR_BAD_INPUT;
        }
        uint32_t ru = holo_find(parent, uu);
        uint32_t rv = holo_find(parent, vv);
        if (ru != rv) {
            if (rnk[ru] < rnk[rv]) {
                uint32_t tmp = ru; ru = rv; rv = tmp;
            }
            parent[rv] = (int32_t)ru;
            if (rnk[ru] == rnk[rv]) {
                rnk[ru]++;
            }
            tu[n_tree] = (int32_t)uu;
            tv[n_tree] = (int32_t)vv;
            tnum[n_tree] = cn;
            tden[n_tree] = cd;
            n_tree++;
        } else {
            out_cycle_u[n_cyc] = uu;
            out_cycle_v[n_cyc] = vv;
            out_num[n_cyc] = cn;   /* stash co-tree charge; folded in below */
            out_den[n_cyc] = cd;
            n_cyc++;
        }
    }
    *out_n_cycles = n_cyc;
    srmech_status_t st = holo_build_pot(n, n_tree, tu, tv, tnum, tden,
                                        pot_num, pot_den, visited, queue);
    if (st != SRMECH_OK) {
        return st;
    }
    /* holonomy(u,v,c) = c + pot[u] - pot[v], reduced mod 1. */
    for (uint32_t i = 0; i < n_cyc; i++) {
        uint32_t uu = out_cycle_u[i];
        uint32_t vv = out_cycle_v[i];
        int64_t hn = out_num[i];
        int64_t hd = out_den[i];
        st = holo_add(hn, hd, pot_num[uu], pot_den[uu], &hn, &hd);
        if (st != SRMECH_OK) {
            return st;
        }
        st = holo_add(hn, hd, -pot_num[vv], pot_den[vv], &hn, &hd);
        if (st != SRMECH_OK) {
            return st;
        }
        holo_mod1(&hn, &hd);
        out_num[i] = hn;
        out_den[i] = hd;
    }
    return SRMECH_OK;
}

/* ------------------------------------------------------------------
 * 0.9.0rc309 (#944 follow-on): quaternion_cycle_holonomy — the NON-ABELIAN
 * generalization of the abelian srmech_graph_cycle_holonomy above. The edge
 * gains are unit quaternions (Q8 = {+-1,+-i,+-j,+-k} and its continuous
 * re-gauges); the per-cycle holonomy is the ordered quaternion product
 * H = P_u . g_uv . conj(P_v), classified by its SU(2) conjugacy class (the
 * scalar part w = Re(H), a conjugation invariant). Reuses the union-find
 * spanning-forest scaffolding (holo_find) + the exported quaternion product
 * (srmech_quaternion_left_mult) + conjugate (srmech_quaternion_conjugate), so
 * the product convention is the SINGLE srmech_quaternion.c source of truth
 * (byte-exact with the pure-Python mirror). See the header for the full
 * gauge-invariance derivation + the 5-vs-3 class note.
 * ------------------------------------------------------------------ */

#define SRMECH_QHOLO_DIM  ((size_t)4)     /* the quaternion carrier dimension */
#define SRMECH_QHOLO_TOL  (1e-9)          /* scalar-part class bucket radius   */

size_t srmech_quaternion_cycle_holonomy_arena_bytes(uint32_t n,
                                                    uint32_t n_edges)
{
    /* double: pot[4n] + tree_gains[4ne] + cotree_gains[4ne] = 8*(4n + 8ne)
     * int32: parent[n] + rnk[n] + visited[n] + queue[n] + tu[ne] + tv[ne]
     *        = 4*(4n + 2ne). +64 alignment/padding slop. */
    size_t bn = (size_t)n;
    size_t be = (size_t)n_edges;
    size_t bytes = 8u * (4u * bn + 8u * be) + 4u * (4u * bn + 2u * be) + 64u;
    assert(bytes >= 64u);            /* always includes the alignment/pad slop */
    assert(bytes >= 32u * bn);       /* room for the double pot[4n] block      */
    return bytes;
}

/* out = a . b (Hamilton product, fixed Cayley-Dickson convention) via the
 * exported left-multiplication operator: (L_a . b)_i = (a . b)_i. L_a's basis
 * columns are exact +-a_i (no rounding), so this IS srmech_quaternion.c's
 * product, byte-exact with the pure-Python quaternion mult. `out` MUST NOT
 * alias a or b. */
static srmech_status_t qholo_mul(const double *a, const double *b, double *out)
{
    assert(a != NULL && b != NULL);
    assert(out != NULL);
    double la[SRMECH_QHOLO_DIM * SRMECH_QHOLO_DIM];
    srmech_status_t st = srmech_quaternion_left_mult(a, SRMECH_QHOLO_DIM, la);
    if (st != SRMECH_OK) {
        return st;
    }
    for (size_t i = 0; i < SRMECH_QHOLO_DIM; ++i) {
        double t = 0.0;
        for (size_t k = 0; k < SRMECH_QHOLO_DIM; ++k) {
            t += la[i * SRMECH_QHOLO_DIM + k] * b[k];
        }
        out[i] = t;
    }
    return SRMECH_OK;
}

/* Classify a unit-quaternion holonomy `h` into its SU(2) conjugacy class from
 * the scalar part w = h[0]: w ~ +1 -> class 0 (parity +1); w ~ -1 -> class 1
 * (parity -1); w ~ 0 -> class 2 (parity 0). |.| via a signed branch (Class-K
 * pin-slot; no abs()). A scalar far from {-1,0,1} -> SRMECH_ERR_BAD_INPUT. */
static srmech_status_t qholo_class(const double *h, uint32_t *cls, int32_t *par)
{
    assert(h != NULL);
    assert(cls != NULL && par != NULL);
    double w = h[0];
    double dp = w - 1.0;
    double dm = w + 1.0;
    double adp = (dp >= 0.0) ? dp : -dp;
    double adm = (dm >= 0.0) ? dm : -dm;
    double aw  = (w  >= 0.0) ? w  : -w;
    if (adp < SRMECH_QHOLO_TOL) {
        *cls = 0u; *par = 1;
    } else if (adm < SRMECH_QHOLO_TOL) {
        *cls = 1u; *par = -1;
    } else if (aw < SRMECH_QHOLO_TOL) {
        *cls = 2u; *par = 0;
    } else {
        return SRMECH_ERR_BAD_INPUT;
    }
    return SRMECH_OK;
}

/* Copy a quaternion gain (4 doubles) from `src` (or identity when NULL) into
 * `dst`. The identity (1,0,0,0) is the missing-gains default (a balanced graph). */
static void qholo_copy_gain(const double *src, double *dst)
{
    assert(dst != NULL);
    if (src != NULL) {
        dst[0] = src[0]; dst[1] = src[1]; dst[2] = src[2]; dst[3] = src[3];
    } else {
        dst[0] = 1.0; dst[1] = 0.0; dst[2] = 0.0; dst[3] = 0.0;
    }
    assert(dst[0] == dst[0]);   /* NaN-free scalar postcondition (a NaN gain
                                 * would silently corrupt the holonomy class) */
}

/* Union-find edge partition: first-encountered spanning edge = tree edge (its
 * gain stashed in `tg`, stored direction uu->vv); a cycle-closing edge =
 * co-tree edge (its gain stashed in `cg`, endpoints in out_cycle_u/v). Fills
 * *n_tree, *n_cyc. An out-of-range endpoint -> SRMECH_ERR_BAD_INPUT. */
static srmech_status_t qholo_partition(uint32_t n, uint32_t n_edges,
    const uint32_t *edges_u, const uint32_t *edges_v, const double *gains,
    int32_t *parent, int32_t *rnk, int32_t *tu, int32_t *tv,
    double *tg, double *cg, uint32_t *out_cycle_u, uint32_t *out_cycle_v,
    uint32_t *n_tree, uint32_t *n_cyc)
{
    assert(parent != NULL && rnk != NULL);
    assert(n_tree != NULL && n_cyc != NULL);
    for (uint32_t i = 0; i < n; i++) {
        parent[i] = (int32_t)i;
        rnk[i] = 0;
    }
    uint32_t nt = 0;
    uint32_t nc = 0;
    for (uint32_t e = 0; e < n_edges; e++) {
        uint32_t uu = edges_u[e];
        uint32_t vv = edges_v[e];
        if (uu >= n || vv >= n) {
            return SRMECH_ERR_BAD_INPUT;
        }
        const double *ge = (gains != NULL) ? &gains[(size_t)e * SRMECH_QHOLO_DIM]
                                            : NULL;
        uint32_t ru = holo_find(parent, uu);
        uint32_t rv = holo_find(parent, vv);
        if (ru != rv) {
            if (rnk[ru] < rnk[rv]) { uint32_t t = ru; ru = rv; rv = t; }
            parent[rv] = (int32_t)ru;
            if (rnk[ru] == rnk[rv]) { rnk[ru]++; }
            tu[nt] = (int32_t)uu;
            tv[nt] = (int32_t)vv;
            qholo_copy_gain(ge, &tg[(size_t)nt * SRMECH_QHOLO_DIM]);
            nt++;
        } else {
            out_cycle_u[nc] = uu;
            out_cycle_v[nc] = vv;
            qholo_copy_gain(ge, &cg[(size_t)nc * SRMECH_QHOLO_DIM]);
            nc++;
        }
    }
    *n_tree = nt;
    *n_cyc = nc;
    return SRMECH_OK;
}

/* Build pot[i] = the ordered quaternion product along the UNIQUE tree path
 * root->i (root = the component seed; pot[root] = identity). BFS over the tree
 * edges; a reversed edge (nb->x stored) contributes conj(gain). The path is
 * unique so the product is traversal-order-independent (byte-exact BFS/DFS). */
static srmech_status_t qholo_build_pot(uint32_t n, uint32_t n_tree,
    const int32_t *tu, const int32_t *tv, const double *tg,
    double *pot, int32_t *visited, int32_t *queue)
{
    assert(pot != NULL);
    assert(visited != NULL && queue != NULL);
    for (uint32_t i = 0; i < n; i++) {
        visited[i] = 0;
        double *p = &pot[(size_t)i * SRMECH_QHOLO_DIM];
        p[0] = 1.0; p[1] = 0.0; p[2] = 0.0; p[3] = 0.0;
    }
    for (uint32_t s = 0; s < n; s++) {
        if (visited[s]) {
            continue;
        }
        uint32_t head = 0, tail = 0;
        visited[s] = 1;
        queue[tail++] = (int32_t)s;
        while (head < tail) {
            uint32_t x = (uint32_t)queue[head++];
            for (uint32_t e = 0; e < n_tree; e++) {
                uint32_t a = (uint32_t)tu[e];
                uint32_t b = (uint32_t)tv[e];
                const double *te = &tg[(size_t)e * SRMECH_QHOLO_DIM];
                double g[SRMECH_QHOLO_DIM];
                uint32_t nb;
                if (a == x && !visited[b]) {
                    nb = b;                       /* x->nb: +gain */
                    g[0] = te[0]; g[1] = te[1]; g[2] = te[2]; g[3] = te[3];
                } else if (b == x && !visited[a]) {
                    nb = a;                       /* x->nb reversed: conj(gain) */
                    srmech_status_t cs = srmech_quaternion_conjugate(
                        te, SRMECH_QHOLO_DIM, g);
                    if (cs != SRMECH_OK) { return cs; }
                } else {
                    continue;
                }
                srmech_status_t st = qholo_mul(
                    &pot[(size_t)x * SRMECH_QHOLO_DIM], g,
                    &pot[(size_t)nb * SRMECH_QHOLO_DIM]);   /* pot[nb] = pot[x].g */
                if (st != SRMECH_OK) { return st; }
                visited[nb] = 1;
                queue[tail++] = (int32_t)nb;
            }
        }
    }
    return SRMECH_OK;
}

/* Per co-tree cycle: H = pot[u] . g_uv . conj(pot[v]); classify by scalar part
 * and (when out_holonomy != NULL) emit the raw H quaternion. */
static srmech_status_t qholo_finalize(uint32_t n_cyc, const double *pot,
    const double *cg, const uint32_t *out_cycle_u, const uint32_t *out_cycle_v,
    uint32_t *out_class_index, int32_t *out_center_parity, double *out_holonomy)
{
    assert(pot != NULL && cg != NULL);
    assert(out_class_index != NULL && out_center_parity != NULL);
    for (uint32_t i = 0; i < n_cyc; i++) {
        uint32_t uu = out_cycle_u[i];
        uint32_t vv = out_cycle_v[i];
        double cpv[SRMECH_QHOLO_DIM];
        double t1[SRMECH_QHOLO_DIM];
        double hol[SRMECH_QHOLO_DIM];
        srmech_status_t st = srmech_quaternion_conjugate(
            &pot[(size_t)vv * SRMECH_QHOLO_DIM], SRMECH_QHOLO_DIM, cpv);
        if (st != SRMECH_OK) { return st; }
        st = qholo_mul(&pot[(size_t)uu * SRMECH_QHOLO_DIM],
                       &cg[(size_t)i * SRMECH_QHOLO_DIM], t1);   /* pot[u].g_uv */
        if (st != SRMECH_OK) { return st; }
        st = qholo_mul(t1, cpv, hol);                           /* .conj(pot[v]) */
        if (st != SRMECH_OK) { return st; }
        st = qholo_class(hol, &out_class_index[i], &out_center_parity[i]);
        if (st != SRMECH_OK) { return st; }
        if (out_holonomy != NULL) {
            double *o = &out_holonomy[(size_t)i * SRMECH_QHOLO_DIM];
            o[0] = hol[0]; o[1] = hol[1]; o[2] = hol[2]; o[3] = hol[3];
        }
    }
    return SRMECH_OK;
}

srmech_status_t srmech_quaternion_cycle_holonomy(
    uint32_t        n,
    uint32_t        n_edges,
    const uint32_t *edges_u,
    const uint32_t *edges_v,
    const double   *gains,
    uint32_t       *out_class_index,
    int32_t        *out_center_parity,
    uint32_t       *out_cycle_u,
    uint32_t       *out_cycle_v,
    double         *out_holonomy,
    uint32_t       *out_n_cycles,
    void           *ws,
    size_t          ws_len)
{
    assert(out_n_cycles != NULL);
    if (out_n_cycles == NULL || ws == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n_edges > 0 && (edges_u == NULL || edges_v == NULL)) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (out_class_index == NULL || out_center_parity == NULL ||
        out_cycle_u == NULL || out_cycle_v == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (ws_len < srmech_quaternion_cycle_holonomy_arena_bytes(n, n_edges)) {
        return SRMECH_ERR_OVERFLOW;
    }
    /* Carve the arena: doubles first (8-aligned base), then int32. */
    double *pot = (double *)ws;
    double *tg = pot + (size_t)SRMECH_QHOLO_DIM * n;
    double *cg = tg + (size_t)SRMECH_QHOLO_DIM * n_edges;
    int32_t *parent = (int32_t *)(cg + (size_t)SRMECH_QHOLO_DIM * n_edges);
    int32_t *rnk = parent + n;
    int32_t *visited = rnk + n;
    int32_t *queue = visited + n;
    int32_t *tu = queue + n;
    int32_t *tv = tu + n_edges;
    uint32_t n_tree = 0;
    uint32_t n_cyc = 0;
    srmech_status_t st = qholo_partition(n, n_edges, edges_u, edges_v, gains,
                                         parent, rnk, tu, tv, tg, cg,
                                         out_cycle_u, out_cycle_v,
                                         &n_tree, &n_cyc);
    if (st != SRMECH_OK) {
        return st;
    }
    *out_n_cycles = n_cyc;
    st = qholo_build_pot(n, n_tree, tu, tv, tg, pot, visited, queue);
    if (st != SRMECH_OK) {
        return st;
    }
    return qholo_finalize(n_cyc, pot, cg, out_cycle_u, out_cycle_v,
                          out_class_index, out_center_parity, out_holonomy);
}

/* Helper: apply a single Givens rotation to symmetric `mat` at index
 * pair (p, q). Updates rows + columns p, q in place. Pi-free —
 * c, s computed algebraically from matrix entries (no trig). */
static void srmech_laplacian_jacobi_rotate(uint32_t n, double *mat,
                                           uint32_t p, uint32_t q)
{
    assert(mat != NULL);
    assert(p < q);
    double a_pp = mat[(size_t)p * n + p];
    double a_qq = mat[(size_t)q * n + q];
    double a_pq = mat[(size_t)p * n + q];
    if (a_pq == 0.0) {
        return;
    }
    /* tau = (a_qq − a_pp) / (2 a_pq); t = sign(tau) / (|tau| + lap_sqrt(tau²+1)). */
    double tau = (a_qq - a_pp) / (2.0 * a_pq);
    double t;
    if (tau >= 0.0) {
        t = 1.0 / (tau + lap_sqrt(1.0 + tau * tau));
    } else {
        t = 1.0 / (tau - lap_sqrt(1.0 + tau * tau));
    }
    double c = 1.0 / lap_sqrt(1.0 + t * t);
    double s = t * c;
    /* Update rows p and q across all columns. */
    for (uint32_t k = 0; k < n; k++) {
        double a_pk = mat[(size_t)p * n + k];
        double a_qk = mat[(size_t)q * n + k];
        mat[(size_t)p * n + k] = c * a_pk - s * a_qk;
        mat[(size_t)q * n + k] = s * a_pk + c * a_qk;
    }
    /* Update columns p and q across all rows. */
    for (uint32_t k = 0; k < n; k++) {
        double a_kp = mat[(size_t)k * n + p];
        double a_kq = mat[(size_t)k * n + q];
        mat[(size_t)k * n + p] = c * a_kp - s * a_kq;
        mat[(size_t)k * n + q] = s * a_kp + c * a_kq;
    }
}

/* Helper: Frobenius norm of off-diagonal entries (squared). */
static double srmech_laplacian_off_diag_sq(uint32_t n, const double *mat)
{
    assert(mat != NULL);
    assert(n < 0xFFFFFFFFu);          /* loop-bound sanity; no node cap */
    double s = 0.0;
    for (uint32_t r = 0; r < n; r++) {
        for (uint32_t c = r + 1; c < n; c++) {
            double v = mat[(size_t)r * n + c];
            s += 2.0 * v * v;
        }
    }
    assert(s >= 0.0);
    return s;
}

srmech_status_t srmech_jacobi_eigvals(uint32_t  n,
                                      double   *matrix,
                                      uint32_t  max_sweeps,
                                      double    tolerance,
                                      double   *out_eigvals)
{
    assert(matrix != NULL);
    assert(out_eigvals != NULL);
    if (matrix == NULL || out_eigvals == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    /* No node cap: the Jacobi sweeps rotate the caller's `matrix` IN PLACE
     * (eigenvalues read off the diagonal), so there is no scratch — the
     * bound is the caller's matrix (standalone-complete honor). */
    if (n == 0) {
        return SRMECH_OK;
    }
    if (max_sweeps == 0 || max_sweeps > SRMECH_LAPLACIAN_JACOBI_MAX_SWEEPS) {
        max_sweeps = SRMECH_LAPLACIAN_JACOBI_MAX_SWEEPS;
    }
    /* Convergence threshold: tolerance × initial off-diagonal norm. */
    double init_off = srmech_laplacian_off_diag_sq(n, matrix);
    double target = tolerance * tolerance * init_off;
    /* Sweeps: each sweep rotates every (p, q) pair with p < q. */
    for (uint32_t sweep = 0; sweep < max_sweeps; sweep++) {
        double off = srmech_laplacian_off_diag_sq(n, matrix);
        if (off <= target || off < 1e-300) {
            break;
        }
        for (uint32_t p = 0; p < n; p++) {
            for (uint32_t q = p + 1; q < n; q++) {
                srmech_laplacian_jacobi_rotate(n, matrix, p, q);
            }
        }
    }
    /* Extract diagonal as eigenvalues. */
    for (uint32_t i = 0; i < n; i++) {
        out_eigvals[i] = matrix[(size_t)i * n + i];
    }
    return SRMECH_OK;
}

/* ================================================================ *
 * Class L broadening — ADR-0002 Phase 2 (v0.4.1rc5)
 *
 * Three new ops extending Class L from "graph Laplacian" to
 * "dense-matrix linear algebra including eigendecomposition +
 * elementwise operations":
 *
 *   - srmech_hermitian_eigendecompose
 *   - srmech_elementwise_multiply_complex
 *   - srmech_elementwise_transcendental
 *
 * Complex numbers travel as interleaved-double pairs (re, im, re, im).
 * Pi-free throughout: complex-Jacobi phase factor computed algebraically
 * as γ/|γ| (no atan2). Per [[user_stance_pi_as_projection]].
 * ================================================================ */

/* Forward decls for the Hermitian-Jacobi helper chain (avoid mutual-
 * recursion ordering issue). */
static void srmech_hermitian_apply_rotation(uint32_t n, double *H,
                                            double *V,
                                            uint32_t p, uint32_t q,
                                            double c, double s,
                                            double cosphi, double sinphi);

/* Helper: complex-Jacobi off-diagonal Frobenius norm² for an n×n
 * interleaved-doubles Hermitian matrix. Sum over strict upper
 * triangle (mirror is conjugate, hence same magnitude); doubled to
 * account for both triangles. */
static double srmech_hermitian_off_diag_sq(uint32_t n,
                                           const double *mat_il)
{
    assert(mat_il != NULL);
    assert(n <= srmech_config_hermitian_max_nodes());
    double s = 0.0;
    for (uint32_t r = 0; r < n; r++) {
        for (uint32_t c = r + 1; c < n; c++) {
            size_t idx = ((size_t)r * n + c) * 2;
            double re = mat_il[idx];
            double im = mat_il[idx + 1];
            s += 2.0 * (re * re + im * im);
        }
    }
    assert(s >= 0.0);
    return s;
}

/* Helper: apply one complex-Jacobi rotation to the n×n interleaved-
 * doubles Hermitian matrix `H` at index pair (p, q), and accumulate
 * the rotation into the eigenvector matrix V (also n×n interleaved
 * doubles, row-major). Pi-free: phase factor γ/|γ| computed
 * algebraically. */
static void srmech_hermitian_jacobi_rotate(uint32_t n, double *H,
                                           double *V,
                                           uint32_t p, uint32_t q)
{
    assert(H != NULL);
    assert(V != NULL);
    assert(p < q);
    size_t pp = ((size_t)p * n + p) * 2;
    size_t qq = ((size_t)q * n + q) * 2;
    size_t pq = ((size_t)p * n + q) * 2;
    double a_pp = H[pp];               /* real diagonal */
    double a_qq = H[qq];
    double g_re = H[pq];
    double g_im = H[pq + 1];
    double g_mag_sq = g_re * g_re + g_im * g_im;
    if (g_mag_sq < 1e-300) {
        return;
    }
    double g_mag = lap_sqrt(g_mag_sq);
    /* Phase factor — pure algebra, no atan2. rc108 FIX (found by the
     * srmech_heat_trace parity gate): the update below applies
     * H -> M H M^H with M = [[c, -s*e^(-i*phi_enc)], [s*e^(+i*phi_enc), c]]
     * (phi_enc = the angle encoded by cosphi/sinphi). Zeroing H[p][q] =
     * gamma = |gamma|*e^(i*phi) under THAT transform needs the CONJUGATE
     * phase, e^(i*phi_enc) = conj(gamma)/|gamma| (then H'[p][q] =
     * e^(i*phi)*[c*s*(a_pp - a_qq) + |gamma|*(c^2 - s^2)] — one common
     * phase, killed by the real-tau rotation). The old non-conjugate
     * phase left mixed e^(i*phi)/e^(-3i*phi) terms, so a GENERIC complex
     * off-diagonal never annihilated: the sweep stalled and the kernel
     * returned OVERFLOW (silently masked by the pure-Python fallback).
     * Real input (g_im = 0) and the zero-diagonal pure-imaginary case
     * (sigma_y) were the two coincidences that worked. */
    double cosphi = g_re / g_mag;
    double sinphi = -(g_im / g_mag);
    /* Real symmetric reduction: tau = (a_qq − a_pp) / (2|γ|). */
    double tau = (a_qq - a_pp) / (2.0 * g_mag);
    double t;
    if (tau >= 0.0) {
        t = 1.0 / (tau + lap_sqrt(1.0 + tau * tau));
    } else {
        t = 1.0 / (tau - lap_sqrt(1.0 + tau * tau));
    }
    double c = 1.0 / lap_sqrt(1.0 + t * t);
    double s = t * c;
    /* Update H and V rows/columns p, q. Helper to keep ≤60 lines. */
    srmech_hermitian_apply_rotation(n, H, V, p, q, c, s, cosphi, sinphi);
}

/* Update a single complex (a, b) pair in-place under the rotation
 * (sign_left, sign_right) ∈ {+1, -1}². sign_left controls whether
 * the conjugate (sign_left = +1 → e^(-iφ)) or non-conjugate
 * (sign_left = -1 → e^(+iφ)) phase factor multiplies b in a's update;
 * sign_right is dual for a's appearance in b's update. */
static void srmech_hermitian_pair_update(double *a_re, double *a_im,
                                         double *b_re, double *b_im,
                                         double c, double s,
                                         double cosphi, double sinphi,
                                         double sign_left,
                                         double sign_right)
{
    assert(a_re != NULL);
    assert(b_re != NULL);
    double ar = *a_re, ai = *a_im;
    double br = *b_re, bi = *b_im;
    double sb_re = s * (cosphi * br + sign_left * sinphi * bi);
    double sb_im = s * (cosphi * bi - sign_left * sinphi * br);
    double sa_re = s * (cosphi * ar - sign_right * sinphi * ai);
    double sa_im = s * (cosphi * ai + sign_right * sinphi * ar);
    *a_re = c * ar - sb_re;
    *a_im = c * ai - sb_im;
    *b_re = sa_re + c * br;
    *b_im = sa_im + c * bi;
}

/* Apply unitary U = [[c, -s*e^(-iφ)], [s*e^(iφ), c]] to H (similarity
 * H -> U^H H U) and accumulate U into V (V <- V U). Rows/cols indexed
 * p, q. */
static void srmech_hermitian_apply_rotation(uint32_t n, double *H,
                                            double *V,
                                            uint32_t p, uint32_t q,
                                            double c, double s,
                                            double cosphi, double sinphi)
{
    assert(H != NULL);
    assert(V != NULL);
    /* H row block: sb uses + sinphi*bi (sign_left = +1),
     *              sa uses - sinphi*ai (sign_right = +1). */
    for (uint32_t k = 0; k < n; k++) {
        size_t ipk = ((size_t)p * n + k) * 2;
        size_t iqk = ((size_t)q * n + k) * 2;
        srmech_hermitian_pair_update(&H[ipk], &H[ipk + 1],
                                     &H[iqk], &H[iqk + 1],
                                     c, s, cosphi, sinphi, 1.0, 1.0);
    }
    /* H col + V col blocks: sb uses - sinphi*bi (sign_left = -1),
     *                       sa uses + sinphi*ai (sign_right = -1). */
    for (uint32_t k = 0; k < n; k++) {
        size_t ikp = ((size_t)k * n + p) * 2;
        size_t ikq = ((size_t)k * n + q) * 2;
        srmech_hermitian_pair_update(&H[ikp], &H[ikp + 1],
                                     &H[ikq], &H[ikq + 1],
                                     c, s, cosphi, sinphi, -1.0, -1.0);
    }
    for (uint32_t k = 0; k < n; k++) {
        size_t ikp = ((size_t)k * n + p) * 2;
        size_t ikq = ((size_t)k * n + q) * 2;
        srmech_hermitian_pair_update(&V[ikp], &V[ikp + 1],
                                     &V[ikq], &V[ikq + 1],
                                     c, s, cosphi, sinphi, -1.0, -1.0);
    }
}

/* Helper: initialise V to the n×n identity (interleaved doubles). */
static void srmech_hermitian_init_identity(uint32_t n, double *V_il)
{
    assert(V_il != NULL);
    assert(n <= srmech_config_hermitian_max_nodes());
    size_t total = (size_t)n * n * 2;
    for (size_t i = 0; i < total; i++) {
        V_il[i] = 0.0;
    }
    for (uint32_t i = 0; i < n; i++) {
        V_il[((size_t)i * n + i) * 2] = 1.0;
    }
}

/* Helper: sort eigenpairs in ascending eigenvalue order. Selection-
 * sort over n (O(n²) over the caller's n eigenpairs). Swaps eigvals[i]
 * with eigvals[min_idx] AND column i of V with column min_idx of V. */
static void srmech_hermitian_sort_eigenpairs(uint32_t n,
                                             double *eigvals,
                                             double *V_il)
{
    assert(eigvals != NULL);
    assert(V_il != NULL);
    for (uint32_t i = 0; i + 1 < n; i++) {
        uint32_t min_idx = i;
        for (uint32_t j = i + 1; j < n; j++) {
            if (eigvals[j] < eigvals[min_idx]) {
                min_idx = j;
            }
        }
        if (min_idx == i) {
            continue;
        }
        double tmp = eigvals[i];
        eigvals[i] = eigvals[min_idx];
        eigvals[min_idx] = tmp;
        /* Swap column i with column min_idx of V. */
        for (uint32_t k = 0; k < n; k++) {
            size_t a = ((size_t)k * n + i) * 2;
            size_t b = ((size_t)k * n + min_idx) * 2;
            double t_re = V_il[a],     t_im = V_il[a + 1];
            V_il[a]     = V_il[b];
            V_il[a + 1] = V_il[b + 1];
            V_il[b]     = t_re;
            V_il[b + 1] = t_im;
        }
    }
}

/* Helper: drive the complex-Jacobi sweep loop to convergence on the
 * working matrix `Hwork` (in-place rotations), accumulating the
 * rotations into V. Returns SRMECH_ERR_OVERFLOW on non-convergence
 * within SRMECH_LAPLACIAN_JACOBI_MAX_SWEEPS, else SRMECH_OK. Split
 * out of srmech_hermitian_eigendecompose_ws to keep both the _ws
 * entry and the wrapper under JPL Rule 4's 60-line limit. */
static srmech_status_t srmech_hermitian_run_sweeps(uint32_t n,
                                                   double *Hwork,
                                                   double *V)
{
    assert(Hwork != NULL);
    assert(V != NULL);
    /* Convergence target = 1e-12² × initial off-diagonal norm. */
    double target = 1e-24 * srmech_hermitian_off_diag_sq(n, Hwork);
    uint32_t sweep;
    for (sweep = 0; sweep < SRMECH_LAPLACIAN_JACOBI_MAX_SWEEPS; sweep++) {
        double off = srmech_hermitian_off_diag_sq(n, Hwork);
        if (off <= target || off < 1e-300) {
            break;
        }
        for (uint32_t p = 0; p < n; p++) {
            for (uint32_t q = p + 1; q < n; q++) {
                srmech_hermitian_jacobi_rotate(n, Hwork, V, p, q);
            }
        }
    }
    if (sweep >= SRMECH_LAPLACIAN_JACOBI_MAX_SWEEPS
        && srmech_hermitian_off_diag_sq(n, Hwork) > target) {
        return SRMECH_ERR_OVERFLOW;
    }
    return SRMECH_OK;
}

srmech_status_t srmech_hermitian_eigendecompose_ws(
    uint32_t       n,
    const double  *H_interleaved,
    double        *out_eigvals,
    double        *out_eigvecs_interleaved,
    double        *workspace,
    size_t         ws_len)
{
    assert(out_eigvals != NULL);
    assert(out_eigvecs_interleaved != NULL);
    if (H_interleaved == NULL || out_eigvals == NULL
        || out_eigvecs_interleaved == NULL || workspace == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    /* Compute-guard ceiling is CONFIG-DRIVEN (rc161): default 2048, settable
     * via srmech_config_load_toml/_file. The real bound is ws_len >= 2*n*n. */
    if (n > srmech_config_hermitian_max_nodes()) {
        return SRMECH_ERR_OVERFLOW;
    }
    if (n == 0) {
        return SRMECH_OK;
    }
    /* Caller-supplied working copy of H (in-place rotations). */
    size_t total = (size_t)n * n * 2;
    if (ws_len < total) {
        return SRMECH_ERR_OVERFLOW;
    }
    assert(ws_len >= total);
    for (size_t i = 0; i < total; i++) {
        workspace[i] = H_interleaved[i];
    }
    srmech_hermitian_init_identity(n, out_eigvecs_interleaved);
    srmech_status_t st = srmech_hermitian_run_sweeps(
        n, workspace, out_eigvecs_interleaved);
    if (st != SRMECH_OK) {
        return st;
    }
    /* Extract diagonal (real part) as eigenvalues. */
    for (uint32_t i = 0; i < n; i++) {
        out_eigvals[i] = workspace[((size_t)i * n + i) * 2];
    }
    srmech_hermitian_sort_eigenpairs(n, out_eigvals,
                                     out_eigvecs_interleaved);
    return SRMECH_OK;
}

/* (rc161) The no-`_ws` convenience overload srmech_hermitian_eigendecompose
 * was REMOVED — it self-buffered a 1 MiB thread-local static (the last
 * compiled-in-buffer + its own n<=256 cap) and had no live caller on a
 * current build. Callers use srmech_hermitian_eigendecompose_ws with a
 * caller-sized workspace; the config getter is the (overridable) ceiling. */

srmech_status_t srmech_dense_matmul_complex(
    uint32_t       m,
    uint32_t       k,
    uint32_t       n,
    const double  *A_interleaved,
    const double  *B_interleaved,
    double        *out_interleaved)
{
    assert(A_interleaved != NULL);
    assert(out_interleaved != NULL);
    if (A_interleaved == NULL || B_interleaved == NULL
        || out_interleaved == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    /* No m/k/n cap: the product accumulates in scalar locals and writes
     * the caller's out_interleaved (no scratch) — the bound is the caller's
     * buffers (standalone-complete honor). */
    for (uint32_t i = 0; i < m; i++) {
        for (uint32_t j = 0; j < n; j++) {
            double acc_re = 0.0;
            double acc_im = 0.0;
            for (uint32_t p = 0; p < k; p++) {
                size_t ai = ((size_t)i * k + p) * 2;
                size_t bi = ((size_t)p * n + j) * 2;
                double a_re = A_interleaved[ai];
                double a_im = A_interleaved[ai + 1];
                double b_re = B_interleaved[bi];
                double b_im = B_interleaved[bi + 1];
                acc_re += a_re * b_re - a_im * b_im;
                acc_im += a_re * b_im + a_im * b_re;
            }
            size_t oi = ((size_t)i * n + j) * 2;
            out_interleaved[oi]     = acc_re;
            out_interleaved[oi + 1] = acc_im;
        }
    }
    return SRMECH_OK;
}

srmech_status_t srmech_elementwise_multiply_complex(
    uint32_t       n,
    const double  *a_interleaved,
    const double  *b_interleaved,
    double        *out_interleaved)
{
    assert(out_interleaved != NULL);
    assert(n == 0 || a_interleaved != NULL);
    if (out_interleaved == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n > 0 && (a_interleaved == NULL || b_interleaved == NULL)) {
        return SRMECH_ERR_NULL_ARG;
    }
    for (uint32_t i = 0; i < n; i++) {
        size_t k = (size_t)i * 2;
        double a_re = a_interleaved[k];
        double a_im = a_interleaved[k + 1];
        double b_re = b_interleaved[k];
        double b_im = b_interleaved[k + 1];
        out_interleaved[k]     = a_re * b_re - a_im * b_im;
        out_interleaved[k + 1] = a_re * b_im + a_im * b_re;
    }
    return SRMECH_OK;
}

srmech_status_t srmech_elementwise_transcendental(
    uint32_t       n,
    const double  *arr,
    int            op_id,
    double        *out)
{
    assert(out != NULL);
    assert(n == 0 || arr != NULL);
    if (out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n > 0 && arr == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (op_id < SRMECH_TRANS_EXP || op_id > SRMECH_TRANS_LOG) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (op_id == SRMECH_TRANS_LOG) {
        for (uint32_t i = 0; i < n; i++) {
            if (arr[i] <= 0.0) {
                return SRMECH_ERR_BAD_INPUT;
            }
        }
    }
    for (uint32_t i = 0; i < n; i++) {
        double x = arr[i];
        if (op_id == SRMECH_TRANS_EXP) {
            (void)srmech_exp(x, &out[i]);          /* Class-N exp cascade, not libm */
        } else if (op_id == SRMECH_TRANS_COS) {
            (void)srmech_cos(x, &out[i]);
        } else if (op_id == SRMECH_TRANS_SIN) {
            (void)srmech_sin(x, &out[i]);
        } else {
            (void)srmech_log(x, &out[i]);          /* Class-N log cascade, not libm */
        }
    }
    return SRMECH_OK;
}

srmech_status_t srmech_three_fold_bands(uint32_t n, uint32_t *out_low,
                                        uint32_t *out_mid, uint32_t *out_high)
{
    assert(out_low != NULL && out_mid != NULL && out_high != NULL);
    if (out_low == NULL || out_mid == NULL || out_high == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    /* Harmonic-3 three-fold band split (F150): partition n eigenvectors into
     * contiguous low/mid/high bands; the remainder rows go to the later bands
     * so |low| <= |mid| <= |high|. Bit-exact with the Python reference. */
    uint32_t base = n / 3u;
    uint32_t rem = n - 3u * base;
    *out_low = base;
    *out_mid = base + (rem >= 2u ? 1u : 0u);
    *out_high = n - *out_low - *out_mid;
    assert(*out_low + *out_mid + *out_high == n);
    return SRMECH_OK;
}

/* --- §51 (issue #1097): the SPARSE / iterative normalized-cut Fiedler -------
 * Power iteration on the normalized operator B = I + D^-1/2 W D^-1/2
 * (= 2I - L_sym; eigenvalues in [0,2] -> well-conditioned, unlike sigma*I - L on
 * a dense graph). Deflate the sqrt(deg) (lambda0) mode each step; the converged
 * direction is the Fiedler (lambda2 of L_sym) and its SIGN is the normalized-cut
 * bisection. Matvec-only (by edge, no CSR) -> O(edges), n unbounded. The caller
 * supplies a >= 8*n-double scratch arena, so there is NO compiled-in node cap
 * (the bound is the caller's RAM). Bit-identical SIGN to the Python cascade. */

/* Accumulate the weighted degree of every node from the undirected edge list
 * (both endpoints). Returns BAD_INPUT on an out-of-range endpoint. */
static srmech_status_t fiedler_degrees(uint32_t n, uint32_t n_edges,
                                       const uint32_t *eu, const uint32_t *ev,
                                       const double *w, double *deg)
{
    assert(deg != NULL);
    assert(n_edges == 0u || (eu != NULL && ev != NULL));
    for (uint32_t i = 0; i < n; i++) {
        deg[i] = 0.0;
    }
    for (uint32_t e = 0; e < n_edges; e++) {
        uint32_t uu = eu[e];
        uint32_t vv = ev[e];
        if (uu >= n || vv >= n) {
            return SRMECH_ERR_BAD_INPUT;
        }
        double we = (w != NULL) ? w[e] : 1.0;
        deg[uu] += we;
        deg[vv] += we;
    }
    return SRMECH_OK;
}

/* Build the D^-1/2 diagonal (s) + the unit lambda0 eigenvector p ~ sqrt(deg).
 * Returns the pre-normalisation L2 norm of p, or 0.0 if every degree is 0
 * (an edgeless graph -> no cut). Normalises p in place when nonzero. */
static double fiedler_build_sp(uint32_t n, const double *deg,
                               double *s, double *p)
{
    assert(deg != NULL && s != NULL);
    assert(p != NULL);
    double pn2 = 0.0;
    for (uint32_t i = 0; i < n; i++) {
        if (deg[i] > 0.0) {
            double r = lap_sqrt(deg[i]);
            s[i] = 1.0 / r;
            p[i] = r;
        } else {
            s[i] = 0.0;
            p[i] = 0.0;
        }
        pn2 += p[i] * p[i];
    }
    if (pn2 <= 0.0) {
        return 0.0;
    }
    double pnorm = lap_sqrt(pn2);
    for (uint32_t i = 0; i < n; i++) {
        p[i] /= pnorm;
    }
    return pnorm;
}

/* Subtract the projection onto the unit lambda0 vector p: u <- u - (u . p) p.
 * Keeps the iterate orthogonal to the trivial sqrt(deg) mode. */
static void fiedler_deflate(uint32_t n, double *u, const double *p)
{
    assert(u != NULL);
    assert(p != NULL);
    double dot = 0.0;
    for (uint32_t i = 0; i < n; i++) {
        dot += u[i] * p[i];
    }
    for (uint32_t i = 0; i < n; i++) {
        u[i] -= dot * p[i];
    }
}

/* Deterministic, order-independent init: a Class-I multiplicative scramble
 * keyed by node index (Knuth 2654435761, uint32 wrap == Python & 0xFFFFFFFF),
 * mapped to [-1, 1), then deflate lambda0. NOT the parity vector [1,-1,...]:
 * that is orthogonal to the Fiedler on a block-ordered regular graph. */
static void fiedler_init(uint32_t n, const double *p, double *v)
{
    assert(p != NULL);
    assert(v != NULL);
    for (uint32_t i = 0; i < n; i++) {
        uint32_t h = i * 2654435761u + 1013904223u;   /* mod 2^32 */
        v[i] = ((double)h / 4294967296.0) * 2.0 - 1.0;
    }
    fiedler_deflate(n, v, p);
}

/* One normalized-operator step: u = deflate(B v), B = I + D^-1/2 W D^-1/2.
 * t = s o v; y = W t (the O(edges) edge loop); u = v + s o y; deflate lambda0. */
static void fiedler_step(uint32_t n, uint32_t n_edges, const uint32_t *eu,
                         const uint32_t *ev, const double *w, const double *s,
                         const double *p, const double *v, double *t,
                         double *y, double *u)
{
    assert(s != NULL && v != NULL && u != NULL);
    assert(t != NULL && y != NULL);
    for (uint32_t i = 0; i < n; i++) {
        t[i] = s[i] * v[i];
        y[i] = 0.0;
    }
    for (uint32_t e = 0; e < n_edges; e++) {
        uint32_t uu = eu[e];
        uint32_t vv = ev[e];
        double we = (w != NULL) ? w[e] : 1.0;
        y[uu] += we * t[vv];
        y[vv] += we * t[uu];
    }
    for (uint32_t i = 0; i < n; i++) {
        u[i] = v[i] + s[i] * y[i];
    }
    fiedler_deflate(n, u, p);
}

/* Rescale by the Class-K max-magnitude (no fabs: scan u_i^2, one Class-N root).
 * Writes v = u / max|u|. Returns 0 if u is all-zero (caller breaks), else 1. */
static int fiedler_rescale(uint32_t n, const double *u, double *v)
{
    assert(u != NULL);
    assert(v != NULL);
    double max_sq = 0.0;
    for (uint32_t i = 0; i < n; i++) {
        double sq = u[i] * u[i];      /* magnitude-square (pin-slot-free) */
        if (sq > max_sq) {
            max_sq = sq;
        }
    }
    if (max_sq <= 0.0) {
        return 0;
    }
    double mx = lap_sqrt(max_sq);
    for (uint32_t i = 0; i < n; i++) {
        v[i] = u[i] / mx;
    }
    return 1;
}

/* Compute the sign partition of v (1 if v_i >= 0 else 0), compare against the
 * previous partition in `prev`, and overwrite `prev` with the new one. Returns
 * 1 iff the partition is unchanged (prev seeded to -1.0 -> first call != ). */
static int fiedler_update_sign(uint32_t n, const double *v, double *prev)
{
    assert(v != NULL);
    assert(prev != NULL);
    int all_match = 1;
    for (uint32_t i = 0; i < n; i++) {
        double cur = (v[i] >= 0.0) ? 1.0 : 0.0;
        if (prev[i] != cur) {
            all_match = 0;
        }
        prev[i] = cur;
    }
    return all_match;
}

size_t srmech_laplacian_fiedler_sparse_arena_bytes(uint32_t n)
{
    /* Carved doubles: deg, s, p, v, u, t, y, prev — eight length-n vectors.
     * Returned in BYTES (rc307: BYTES like the rest of the caller-arena surface;
     * this replaces the pre-rc307 DOUBLES-count guard). n is a uint32 node count;
     * 8*n*8 <= 2^37 never overflows size_t (64-bit). */
    size_t doubles = (size_t)8u * (size_t)n;
    assert(sizeof(double) == 8u);
    assert(doubles / 8u == (size_t)n);            /* the *8 did not overflow size_t */
    return doubles * sizeof(double);
}

srmech_status_t srmech_laplacian_fiedler_sparse(uint32_t n, uint32_t n_edges,
    const uint32_t *edge_u, const uint32_t *edge_v, const double *weights,
    uint32_t max_iters, double *out_vec, double *ws, size_t ws_len)
{
    assert(out_vec != NULL && ws != NULL);
    if (out_vec == NULL || ws == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n_edges > 0u && (edge_u == NULL || edge_v == NULL)) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (ws_len < srmech_laplacian_fiedler_sparse_arena_bytes(n)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    assert(ws_len >= srmech_laplacian_fiedler_sparse_arena_bytes(n));  /* BYTES: 8 length-n vecs */
    for (uint32_t i = 0; i < n; i++) {
        out_vec[i] = 0.0;
    }
    if (n < 2u) {
        return SRMECH_OK;                          /* no cut */
    }
    double *deg = ws;
    double *s = ws + (size_t)1u * n;
    double *p = ws + (size_t)2u * n;
    double *v = ws + (size_t)3u * n;
    double *u = ws + (size_t)4u * n;
    double *t = ws + (size_t)5u * n;
    double *y = ws + (size_t)6u * n;
    double *prev = ws + (size_t)7u * n;
    srmech_status_t st = fiedler_degrees(n, n_edges, edge_u, edge_v, weights, deg);
    if (st != SRMECH_OK) {
        return st;
    }
    if (fiedler_build_sp(n, deg, s, p) <= 0.0) {
        return SRMECH_OK;                          /* edgeless -> zero vector */
    }
    fiedler_init(n, p, v);
    for (uint32_t i = 0; i < n; i++) {
        prev[i] = -1.0;
    }
    uint32_t stable = 0u;
    for (uint32_t it = 0; it < max_iters; it++) {
        fiedler_step(n, n_edges, edge_u, edge_v, weights, s, p, v, t, y, u);
        if (fiedler_rescale(n, u, v) == 0) {
            break;
        }
        if (fiedler_update_sign(n, v, prev) && it >= 20u) {
            stable++;
            if (stable >= 5u) {
                break;
            }
        } else {
            stable = 0u;
        }
    }
    for (uint32_t i = 0; i < n; i++) {
        out_vec[i] = v[i];
    }
    return SRMECH_OK;
}

/* --- §52 Part 2 (F793): the OUT-OF-CORE streaming Fiedler -------------------
 * The same normalized-cut power iteration as srmech_laplacian_fiedler_sparse,
 * but the adjacency is NEVER resident: each edge pass streams a packed edge file
 * (one 16-byte record = uint32 u | uint32 v | double w, host byte order) through
 * the PAL streaming-read. Only the O(n) working vectors (the caller arena) live
 * in RAM, so a low-RAM target can partition a graph whose edge list does not fit
 * — the LOW-RAM ENCODE for graph PARTITION (composes §52.1 cooccurrence_topk for
 * the bounded edge SET; this bounds the partition's RAM too). Records never
 * straddle a read chunk (chunk = a whole number of records). */

#define FIEDLER_REC_BYTES 16u                 /* uint32 u | uint32 v | double w */
#define FIEDLER_CHUNK_RECS 256u
#define FIEDLER_CHUNK_BYTES (FIEDLER_REC_BYTES * FIEDLER_CHUNK_RECS)

/* Per-record callback over a streamed edge file (no Python — standalone C). */
typedef srmech_status_t (*fiedler_rec_cb)(uint32_t u, uint32_t v, double w, void *ctx);

/* Stream `path` (a packed 16-byte-record edge file) and call `cb` per record.
 * A read that is not a whole number of records -> BAD_INPUT (truncated file). */
static srmech_status_t fiedler_file_scan(const char *path, fiedler_rec_cb cb, void *ctx)
{
    assert(path != NULL);
    assert(cb != NULL);
    srmech_plat_rstream_t rs;
    srmech_status_t st = srmech_plat_rstream_open(path, &rs);
    if (st != SRMECH_OK) {
        return st;
    }
    unsigned char chunk[FIEDLER_CHUNK_BYTES];
    int eof = 0;
    while (eof == 0) {
        size_t n_read = 0u;
        st = srmech_plat_rstream_read(&rs, chunk, FIEDLER_CHUNK_BYTES, &n_read);
        if (st != SRMECH_OK) { srmech_plat_rstream_close(&rs); return st; }
        if (n_read == 0u) { break; }
        if ((n_read % FIEDLER_REC_BYTES) != 0u) {
            srmech_plat_rstream_close(&rs);
            return SRMECH_ERR_BAD_INPUT;
        }
        size_t recs = n_read / FIEDLER_REC_BYTES;
        for (size_t i = 0; i < recs; i++) {
            const unsigned char *rec = chunk + i * FIEDLER_REC_BYTES;
            uint32_t u = 0u, v = 0u;
            double w = 0.0;
            memcpy(&u, rec, sizeof(uint32_t));
            memcpy(&v, rec + 4, sizeof(uint32_t));
            memcpy(&w, rec + 8, sizeof(double));
            st = cb(u, v, w, ctx);
            if (st != SRMECH_OK) { srmech_plat_rstream_close(&rs); return st; }
        }
        if (n_read < FIEDLER_CHUNK_BYTES) { eof = 1; }
    }
    srmech_plat_rstream_close(&rs);
    return SRMECH_OK;
}

typedef struct { uint32_t n; double *deg; } fiedler_deg_ctx;
typedef struct { uint32_t n; const double *t; double *y; } fiedler_y_ctx;

/* Degree-accumulation callback (undirected: both endpoints). */
static srmech_status_t fiedler_deg_cb(uint32_t u, uint32_t v, double w, void *ctx)
{
    fiedler_deg_ctx *c = (fiedler_deg_ctx *)ctx;
    assert(c != NULL);
    assert(c->deg != NULL);
    if (u >= c->n || v >= c->n) { return SRMECH_ERR_BAD_INPUT; }
    c->deg[u] += w;
    c->deg[v] += w;
    return SRMECH_OK;
}

/* Matvec y += W t accumulation callback (one streamed pass = one matvec). */
static srmech_status_t fiedler_y_cb(uint32_t u, uint32_t v, double w, void *ctx)
{
    fiedler_y_ctx *c = (fiedler_y_ctx *)ctx;
    assert(c != NULL);
    assert(c->t != NULL && c->y != NULL);
    if (u >= c->n || v >= c->n) { return SRMECH_ERR_BAD_INPUT; }
    c->y[u] += w * c->t[v];
    c->y[v] += w * c->t[u];
    return SRMECH_OK;
}

/* One out-of-core step: u = deflate(B v), the W t matvec streamed from `path`. */
static srmech_status_t fiedler_step_file(const char *path, uint32_t n, const double *s,
                                         const double *p, const double *v, double *t,
                                         double *y, double *u)
{
    assert(s != NULL && v != NULL && u != NULL);
    assert(t != NULL && y != NULL && p != NULL);
    for (uint32_t i = 0; i < n; i++) {
        t[i] = s[i] * v[i];
        y[i] = 0.0;
    }
    fiedler_y_ctx ctx = { n, t, y };
    srmech_status_t st = fiedler_file_scan(path, fiedler_y_cb, &ctx);
    if (st != SRMECH_OK) {
        return st;
    }
    for (uint32_t i = 0; i < n; i++) {
        u[i] = v[i] + s[i] * y[i];
    }
    fiedler_deflate(n, u, p);
    return SRMECH_OK;
}

/* Out-of-core power iteration: stream-step until rescale-zero or sign-stability
 * (5 stable-sign steps past a 20-iteration warmup). v holds the running vector.
 * §101: an optional per-iteration progress tick (NULL == off); a nonzero tick
 * return is a CLEAN cancel -> SRMECH_CANCELLED (the caller leaves out_vec zeroed). */
static srmech_status_t fiedler_file_iterate(const char *path, uint32_t n,
    const double *s, const double *p, double *v, double *u, double *t,
    double *y, double *prev, uint32_t max_iters,
    srmech_progress_tick_cb_t tick, void *tick_user)
{
    assert(s != NULL && p != NULL);
    assert(v != NULL && prev != NULL);
    uint32_t stable = 0u;
    for (uint32_t it = 0; it < max_iters; it++) {
        if (tick != NULL) {
            srmech_progress_ev_t ev = { (uint32_t)sizeof(srmech_progress_ev_t),
                                        (uint32_t)SRMECH_PHASE_PARTITIONING,
                                        (uint64_t)it + 1u, (uint64_t)max_iters };
            if (tick(&ev, tick_user) != 0) {
                return SRMECH_CANCELLED;            /* clean abort, JPL Rule-1 return */
            }
        }
        srmech_status_t st = fiedler_step_file(path, n, s, p, v, t, y, u);
        if (st != SRMECH_OK) {
            return st;
        }
        if (fiedler_rescale(n, u, v) == 0) {
            break;
        }
        if (fiedler_update_sign(n, v, prev) && it >= 20u) {
            stable++;
            if (stable >= 5u) {
                break;
            }
        } else {
            stable = 0u;
        }
    }
    return SRMECH_OK;
}

/* §101: the plain symbol keeps its exact ABI signature and forwards to the
 * _progress overload with a NULL tick (runs exactly as before rc275). */
srmech_status_t srmech_laplacian_fiedler_sparse_file(uint32_t n, const char *path,
    uint32_t max_iters, double *out_vec, double *ws, size_t ws_len)
{
    assert(out_vec != NULL);
    assert(ws != NULL);
    return srmech_laplacian_fiedler_sparse_file_progress(
        n, path, max_iters, out_vec, ws, ws_len, NULL, NULL);
}

/* §101: the ENCODE-PROGRESS overload — the plain body + the per-iteration tick
 * threaded into fiedler_file_iterate. A cancelled iterate returns SRMECH_CANCELLED
 * with out_vec left zeroed (the early return skips the v -> out_vec copy). */
srmech_status_t srmech_laplacian_fiedler_sparse_file_progress(uint32_t n, const char *path,
    uint32_t max_iters, double *out_vec, double *ws, size_t ws_len,
    srmech_progress_tick_cb_t tick, void *tick_user)
{
    assert(out_vec != NULL && ws != NULL);
    if (out_vec == NULL || ws == NULL || path == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (ws_len < srmech_laplacian_fiedler_sparse_arena_bytes(n)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    assert(ws_len >= srmech_laplacian_fiedler_sparse_arena_bytes(n));   /* BYTES (rc307) */
    for (uint32_t i = 0; i < n; i++) {
        out_vec[i] = 0.0;
    }
    if (n < 2u) {
        return SRMECH_OK;
    }
    double *deg = ws;
    double *s = ws + (size_t)1u * n;
    double *p = ws + (size_t)2u * n;
    double *v = ws + (size_t)3u * n;
    double *u = ws + (size_t)4u * n;
    double *t = ws + (size_t)5u * n;
    double *y = ws + (size_t)6u * n;
    double *prev = ws + (size_t)7u * n;
    for (uint32_t i = 0; i < n; i++) {
        deg[i] = 0.0;
    }
    fiedler_deg_ctx dctx = { n, deg };
    srmech_status_t st = fiedler_file_scan(path, fiedler_deg_cb, &dctx);   /* degree pass */
    if (st != SRMECH_OK) {
        return st;
    }
    if (fiedler_build_sp(n, deg, s, p) <= 0.0) {
        return SRMECH_OK;                          /* edgeless -> zero vector */
    }
    fiedler_init(n, p, v);
    for (uint32_t i = 0; i < n; i++) {
        prev[i] = -1.0;
    }
    st = fiedler_file_iterate(path, n, s, p, v, u, t, y, prev, max_iters,
                              tick, tick_user);
    if (st != SRMECH_OK) {
        return st;                                 /* incl. SRMECH_CANCELLED: out_vec stays zeroed */
    }
    for (uint32_t i = 0; i < n; i++) {
        out_vec[i] = v[i];
    }
    return SRMECH_OK;
}

/* --- §75-sparse (issue #698): the STREAMING k-extreme resonant read ---------
 * The bottom-k + top-k modes of the COMBINATORIAL Laplacian L = D - W, read by
 * power iteration + Gram-Schmidt deflation streaming the packed edge file — the
 * n-unbounded C twin of coupling.resonant_spectrum_sparse. Bottom modes ride the
 * shift sigma*I - L (sigma = 2*max_deg + 1, a Gershgorin upper bound on
 * lambda_max), top modes ride L; each new mode deflates against every found mode
 * (the out_modes rows), so bottom/top never collide and, when 2k >= n, the union
 * is the full spectrum. RAM O(k*n) (the caller out_modes) + O(n) (the ws arena);
 * time O(k*|E|*iters), n unbounded. Reuses the fiedler_file_scan streaming-matvec
 * machinery (fiedler_y_cb accumulates W*v). The Rayleigh convergence floor +
 * stable-run mirror the Python op verbatim, so native == pure within float tol. */

#define KEXT_TOL 1e-13
#define KEXT_STABLE_RUN 3u

/* One streamed adjacency matvec y = W*v (reuses fiedler_y_cb; y zeroed first). */
static srmech_status_t kext_wv(const char *path, uint32_t n, const double *v, double *y)
{
    assert(path != NULL && v != NULL);
    assert(y != NULL);
    for (uint32_t i = 0; i < n; i++) {
        y[i] = 0.0;
    }
    fiedler_y_ctx ctx = { n, v, y };
    return fiedler_file_scan(path, fiedler_y_cb, &ctx);
}

/* Gram-Schmidt-deflate v against the first `count` mode ROWS of modes (row m at
 * modes + m*n, length n) — keep the new iterate orthogonal to every found mode. */
static void kext_deflate(uint32_t n, uint32_t count, const double *modes, double *v)
{
    assert(v != NULL);
    assert(count == 0u || modes != NULL);
    for (uint32_t m = 0; m < count; m++) {
        const double *bm = modes + (size_t)m * n;
        double dot = 0.0;
        for (uint32_t i = 0; i < n; i++) {
            dot += v[i] * bm[i];
        }
        for (uint32_t i = 0; i < n; i++) {
            v[i] -= dot * bm[i];
        }
    }
}

/* Unit-normalise v (Class-N root of the Class-K magnitude-square sum). Returns 0
 * if v is the zero vector (caller stops that mode), else 1. */
static int kext_normalize(uint32_t n, double *v)
{
    assert(v != NULL);
    assert(n > 0u);
    double n2 = 0.0;
    for (uint32_t i = 0; i < n; i++) {
        n2 += v[i] * v[i];
    }
    if (n2 <= 0.0) {
        return 0;
    }
    double nrm = lap_sqrt(n2);
    for (uint32_t i = 0; i < n; i++) {
        v[i] /= nrm;
    }
    return 1;
}

/* The L-Rayleigh quotient v^T L v = sum deg_i v_i^2 - v^T W v on a unit v (the
 * tension read; accurate even when v converged on the shifted operator). */
static srmech_status_t kext_rayleigh_l(const char *path, uint32_t n, const double *deg,
                                       const double *v, double *y, double *out)
{
    assert(deg != NULL && v != NULL);
    assert(y != NULL && out != NULL);
    srmech_status_t st = kext_wv(path, n, v, y);
    if (st != SRMECH_OK) {
        return st;
    }
    double r = 0.0;
    for (uint32_t i = 0; i < n; i++) {
        r += deg[i] * v[i] * v[i] - v[i] * y[i];
    }
    *out = r;
    return SRMECH_OK;
}

/* Deterministic Class-I scramble init (bit-identical to Python _kext_scramble_
 * init): Knuth 2654435761 uint32-wrap hash mapped to [-1, 1). */
static void kext_init(uint32_t n, double *v)
{
    assert(v != NULL);
    assert(n > 0u);
    for (uint32_t i = 0; i < n; i++) {
        uint32_t h = i * 2654435761u + 1013904223u;   /* mod 2^32 */
        v[i] = ((double)h / 4294967296.0) * 2.0 - 1.0;
    }
}

/* Power-iterate one extreme eigenvector into v, deflated against modes[0..count).
 * top != 0 -> operator L (largest tension); top == 0 -> sigma*I - L (smallest).
 * Stops on Rayleigh convergence (KEXT_STABLE_RUN settled steps past warmup). */
static srmech_status_t kext_iterate(const char *path, uint32_t n, const double *deg,
    double sigma, int top, uint32_t count, const double *modes, uint32_t max_iters,
    double *v, double *av, double *y)
{
    assert(deg != NULL && v != NULL);
    assert(av != NULL && y != NULL);
    double lam_prev = 0.0;
    int have_prev = 0;
    uint32_t stable = 0u;
    for (uint32_t it = 0; it < max_iters; it++) {
        srmech_status_t st = kext_wv(path, n, v, y);
        if (st != SRMECH_OK) {
            return st;
        }
        for (uint32_t i = 0; i < n; i++) {
            double lv = deg[i] * v[i] - y[i];                 /* L*v */
            av[i] = (top != 0) ? lv : (sigma * v[i] - lv);    /* L or sigma*I-L */
        }
        kext_deflate(n, count, modes, av);
        double lam = 0.0;
        for (uint32_t i = 0; i < n; i++) {
            lam += v[i] * av[i];              /* Rayleigh of the iterated operator */
        }
        if (kext_normalize(n, av) == 0) {
            break;
        }
        for (uint32_t i = 0; i < n; i++) {
            v[i] = av[i];
        }
        if (have_prev != 0) {
            double d = lam - lam_prev;
            double mag = (d >= 0.0) ? d : -d;                 /* Class-K sign branch */
            double ref = 1.0 + ((lam >= 0.0) ? lam : -lam);
            if (mag <= KEXT_TOL * ref) {
                stable++;
                if (stable >= KEXT_STABLE_RUN && it >= 5u) {
                    break;
                }
            } else {
                stable = 0u;
            }
        }
        lam_prev = lam;
        have_prev = 1;
    }
    return SRMECH_OK;
}

/* Find ONE extreme eigenpair: init -> deflate -> iterate -> write the mode row
 * to modes[count*n] + its L-tension to *tension. *found = 0 when the deflated
 * subspace is exhausted (a zero init after deflation). */
static srmech_status_t kext_one_mode(const char *path, uint32_t n, const double *deg,
    double sigma, int top, uint32_t count, double *modes, uint32_t max_iters,
    double *v, double *av, double *y, double *tension, int *found)
{
    assert(modes != NULL && tension != NULL && found != NULL);
    assert(v != NULL && av != NULL && y != NULL);
    *found = 0;
    kext_init(n, v);
    kext_deflate(n, count, modes, v);
    if (kext_normalize(n, v) == 0) {
        return SRMECH_OK;                    /* exhausted subspace -> not found */
    }
    srmech_status_t st = kext_iterate(path, n, deg, sigma, top, count, modes,
                                      max_iters, v, av, y);
    if (st != SRMECH_OK) {
        return st;
    }
    double *dst = modes + (size_t)count * n;
    for (uint32_t i = 0; i < n; i++) {
        dst[i] = v[i];
    }
    st = kext_rayleigh_l(path, n, deg, v, y, tension);
    if (st == SRMECH_OK) {
        *found = 1;
    }
    return st;
}

/* Collect up to k extreme modes of one side into out_tensions/out_modes from
 * index *count. top != 0 -> L largest; else the shift -> L smallest. Stops at
 * min(k, n), a not-found (degenerate) mode, or *count == n total modes. */
static srmech_status_t kext_collect_side(const char *path, uint32_t n,
    const double *deg, double sigma, int top, uint32_t k, uint32_t max_iters,
    double *out_tensions, double *out_modes, uint32_t *count,
    double *v, double *av, double *y)
{
    assert(out_tensions != NULL && out_modes != NULL && count != NULL);
    assert(deg != NULL && v != NULL);
    uint32_t kk = (k < n) ? k : n;
    for (uint32_t m = 0; m < kk; m++) {
        if (*count >= n) {
            break;
        }
        double tension = 0.0;
        int found = 0;
        srmech_status_t st = kext_one_mode(path, n, deg, sigma, top, *count,
            out_modes, max_iters, v, av, y, &tension, &found);
        if (st != SRMECH_OK) {
            return st;
        }
        if (found == 0) {
            break;
        }
        out_tensions[*count] = tension;
        (*count)++;
    }
    return SRMECH_OK;
}

size_t srmech_laplacian_k_extreme_modes_arena_bytes(uint32_t n)
{
    /* Carved doubles: deg, v, av, y — four length-n vectors. Returned in BYTES.
     * n is a uint32 node count; 4*n*8 <= 2^37 never overflows size_t (64-bit). */
    size_t doubles = (size_t)4u * (size_t)n;
    assert(sizeof(double) == 8u);
    assert(doubles / 4u == (size_t)n);            /* the *4 did not overflow size_t */
    return doubles * sizeof(double);
}

/* Stream the degree pass into `deg` and return sigma = 2*max_deg + 1 (the
 * Gershgorin upper bound on lambda_max used for the bottom-mode shift). */
static srmech_status_t kext_setup(const char *path, uint32_t n, double *deg,
                                  double *sigma)
{
    assert(deg != NULL && sigma != NULL);
    assert(path != NULL);
    for (uint32_t i = 0; i < n; i++) {
        deg[i] = 0.0;
    }
    fiedler_deg_ctx dctx = { n, deg };
    srmech_status_t st = fiedler_file_scan(path, fiedler_deg_cb, &dctx);
    if (st != SRMECH_OK) {
        return st;
    }
    double max_deg = 0.0;
    for (uint32_t i = 0; i < n; i++) {
        if (deg[i] > max_deg) {
            max_deg = deg[i];
        }
    }
    *sigma = 2.0 * max_deg + 1.0;
    return SRMECH_OK;
}

/* Pin the EXACT trivial mode (constant eigenvector, L*1 = 0; always the smallest
 * tension) as bottom mode 0 — row 0 of out_modes, tension 0. It converges slowly
 * by power iteration on a near-degenerate low-frequency spectrum, so inject it
 * exactly (== the Python op; analytic-deflation of the known trivial mode).
 * Sets *count = 1 and returns the number of bottom modes STILL to find (kb-1). */
static uint32_t kext_inject_trivial(uint32_t n, uint32_t kb, double *out_tensions,
                                    double *out_modes, uint32_t *count)
{
    assert(out_tensions != NULL && out_modes != NULL);
    assert(count != NULL && kb >= 1u);
    double c = 1.0 / lap_sqrt((double)n);
    for (uint32_t i = 0; i < n; i++) {
        out_modes[i] = c;                               /* row 0 = the constant mode */
    }
    out_tensions[0] = 0.0;
    *count = 1u;
    return kb - 1u;
}

srmech_status_t srmech_laplacian_k_extreme_modes_file(uint32_t n, const char *path,
    uint32_t k, uint32_t max_iters, double *out_tensions, double *out_modes,
    uint32_t *out_count, double *ws, size_t ws_len)
{
    assert(out_tensions != NULL && out_modes != NULL);
    assert(out_count != NULL && ws != NULL);
    if (out_tensions == NULL || out_modes == NULL || out_count == NULL
        || ws == NULL || path == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    *out_count = 0u;
    if (ws_len < srmech_laplacian_k_extreme_modes_arena_bytes(n)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (n == 0u) {
        return SRMECH_OK;
    }
    double *deg = ws;
    double *v = ws + (size_t)1u * n;
    double *av = ws + (size_t)2u * n;
    double *y = ws + (size_t)3u * n;
    double sigma = 0.0;
    srmech_status_t st = kext_setup(path, n, deg, &sigma);
    if (st != SRMECH_OK) {
        return st;
    }
    uint32_t kb = (k < n) ? k : n;
    uint32_t count = 0u;
    uint32_t bottom_more = 0u;
    if (kb >= 1u) {
        bottom_more = kext_inject_trivial(n, kb, out_tensions, out_modes, &count);
    }
    st = kext_collect_side(path, n, deg, sigma, 0, bottom_more, max_iters,   /* bottom */
                           out_tensions, out_modes, &count, v, av, y);
    if (st != SRMECH_OK) {
        return st;
    }
    st = kext_collect_side(path, n, deg, sigma, 1, k, max_iters,                /* top */
                           out_tensions, out_modes, &count, v, av, y);
    if (st != SRMECH_OK) {
        return st;
    }
    *out_count = count;
    return SRMECH_OK;
}

/* ================================================================== *
 * §100 G1 (rc284): the OUT-OF-CORE RECURSIVE SPECTRAL BISECTION driver.
 *
 * The `while pending` loop that srmech_laplacian_fiedler_sparse_file could
 * not express on its own. Every sub-graph, every pending node set and every
 * finished tome lives ON DISK; peak RAM is the single caller arena (O(n)),
 * not the structure. This is the piece whose absence made §100 G1 the
 * deepest C-host parity gap: the Fiedler ENGINE has been native since
 * rc168, but the RECURSION around it was Python-only, so a bare-C host
 * could bisect once and no further.
 *
 * NOT recursive in C (JPL Rule 1): an explicit arena-backed LIFO stack
 * carries (serial, depth), mirroring the Python driver's `pending` list
 * pop/append order EXACTLY so both projections emit byte-identical tomes
 * in byte-identical order.
 *
 * The node sets are SORTED ASCENDING by construction — the root is
 * 0..n-1 and each child preserves the parent's relative order — so the
 * original->local relabel is a BINARY SEARCH over the set itself. No map,
 * no hash, no allocation: the invariant the Python dict was hiding.
 * ================================================================== */

#define RCUT_PATH_MAX    512u    /* one on-disk path (work_dir + stem + index) */
#define RCUT_NODE_REC      4u    /* one node-set record = uint32 original id */
#define RCUT_WBUF_RECS  4096u    /* induced-subgraph write buffer, in records */

size_t srmech_laplacian_recursive_cut_arena_bytes(uint32_t n)
{
    /* 9n doubles (8n Fiedler ws + n Fiedler out) then 4n+4 uint32
     * (ids + partition scratch + the (serial,depth) LIFO stack). */
    size_t d = (size_t)9u * (size_t)n;
    size_t u = (size_t)4u * (size_t)n + 4u;
    assert(sizeof(double) == 8u);
    assert(d / 9u == (size_t)n);            /* the *9 did not overflow size_t */
    return d * sizeof(double) + u * sizeof(uint32_t);
}

/* Build "<dir>/<stem><idx>.bin". Truncation is an error, never a silent cut. */
static srmech_status_t rcut_path(char *out, size_t cap, const char *dir,
                                 const char *stem, uint32_t idx)
{
    assert(out != NULL && dir != NULL && stem != NULL);
    assert(cap > 0u);
    int k = snprintf(out, cap, "%s/%s%lu.bin", dir, stem, (unsigned long)idx);
    if (k < 0 || (size_t)k >= cap) {
        return SRMECH_ERR_OVERFLOW;
    }
    return SRMECH_OK;
}

/* Write `count` original node ids to `path` as packed uint32 records. */
static srmech_status_t rcut_write_set(const char *path, const uint32_t *ids,
                                      uint32_t count)
{
    assert(path != NULL);
    assert(ids != NULL || count == 0u);
    unsigned char buf[RCUT_WBUF_RECS * RCUT_NODE_REC];
    srmech_status_t st = srmech_plat_file_write(path, 0, NULL, 0u);  /* truncate */
    if (st != SRMECH_OK) { return st; }
    uint32_t done = 0u;
    while (done < count) {
        uint32_t take = count - done;
        if (take > RCUT_WBUF_RECS) { take = RCUT_WBUF_RECS; }
        for (uint32_t i = 0u; i < take; i++) {
            uint32_t v = ids[done + i];
            memcpy(buf + (size_t)i * RCUT_NODE_REC, &v, sizeof v);
        }
        st = srmech_plat_file_write(path, 1, buf,
                                    (size_t)take * RCUT_NODE_REC);
        if (st != SRMECH_OK) { return st; }
        done += take;
    }
    return SRMECH_OK;
}

/* Read a packed node-set file back into `ids` (capacity `cap`). */
static srmech_status_t rcut_read_set(const char *path, uint32_t *ids,
                                     uint32_t cap, uint32_t *out_count)
{
    assert(path != NULL);
    assert(ids != NULL && out_count != NULL);
    size_t bytes = 0u;
    srmech_status_t st = srmech_plat_file_size(path, &bytes);
    if (st != SRMECH_OK) { return st; }
    if (bytes % RCUT_NODE_REC != 0u) { return SRMECH_ERR_BAD_INPUT; }
    size_t count = bytes / RCUT_NODE_REC;
    if (count > (size_t)cap) { return SRMECH_ERR_OVERFLOW; }
    unsigned char buf[RCUT_WBUF_RECS * RCUT_NODE_REC];
    size_t done = 0u;
    while (done < count) {
        size_t take = count - done;
        if (take > RCUT_WBUF_RECS) { take = RCUT_WBUF_RECS; }
        st = srmech_plat_file_read_region(path, done * RCUT_NODE_REC, buf,
                                          take * RCUT_NODE_REC);
        if (st != SRMECH_OK) { return st; }
        for (size_t i = 0u; i < take; i++) {
            memcpy(&ids[done + i], buf + i * RCUT_NODE_REC, sizeof(uint32_t));
        }
        done += take;
    }
    *out_count = (uint32_t)count;
    return SRMECH_OK;
}

/* Local index of `orig` in the ASCENDING set `ids`, or UINT32_MAX if absent.
 * The relabel the Python `orig_to_local` dict performed — as a binary search
 * over the sorted set, so it needs no auxiliary structure at all. */
static uint32_t rcut_find_local(const uint32_t *ids, uint32_t count, uint32_t orig)
{
    assert(ids != NULL || count == 0u);
    assert(count <= UINT32_MAX);
    uint32_t lo = 0u;
    uint32_t hi = count;
    while (lo < hi) {
        uint32_t mid = lo + ((hi - lo) >> 1);
        if (ids[mid] == orig) { return mid; }
        if (ids[mid] < orig) { lo = mid + 1u; } else { hi = mid; }
    }
    return UINT32_MAX;
}

/* Streaming induced-subgraph writer state (one buffered output file). */
typedef struct rcut_ind_ctx {
    const uint32_t *ids;
    uint32_t        count;
    const char     *out_path;
    unsigned char   buf[FIEDLER_CHUNK_BYTES];
    size_t          fill;        /* bytes currently buffered */
    int             opened;      /* 0 -> next flush truncates, 1 -> appends */
    srmech_status_t st;
} rcut_ind_ctx_t;

static srmech_status_t rcut_ind_flush(rcut_ind_ctx_t *c)
{
    assert(c != NULL);
    assert(c->fill <= FIEDLER_CHUNK_BYTES);
    srmech_status_t st = srmech_plat_file_write(c->out_path, c->opened,
                                                c->buf, c->fill);
    c->opened = 1;
    c->fill = 0u;
    return st;
}

/* Per-record callback: keep an edge iff BOTH endpoints are in the set, and
 * write it RELABELLED to local ids so the streaming Fiedler can run directly. */
static srmech_status_t rcut_ind_rec(uint32_t u, uint32_t v, double w, void *ctx)
{
    assert(ctx != NULL);
    rcut_ind_ctx_t *c = (rcut_ind_ctx_t *)ctx;
    assert(c->fill <= FIEDLER_CHUNK_BYTES);
    uint32_t lu = rcut_find_local(c->ids, c->count, u);
    if (lu == UINT32_MAX) { return SRMECH_OK; }
    uint32_t lv = rcut_find_local(c->ids, c->count, v);
    if (lv == UINT32_MAX) { return SRMECH_OK; }
    if (c->fill + FIEDLER_REC_BYTES > FIEDLER_CHUNK_BYTES) {
        srmech_status_t st = rcut_ind_flush(c);
        if (st != SRMECH_OK) { return st; }
    }
    memcpy(c->buf + c->fill, &lu, sizeof lu);
    memcpy(c->buf + c->fill + 4u, &lv, sizeof lv);
    memcpy(c->buf + c->fill + 8u, &w, sizeof w);
    c->fill += FIEDLER_REC_BYTES;
    return SRMECH_OK;
}

/* Stream `parent` and write the sub-graph induced on `ids` to `out_path`. */
static srmech_status_t rcut_induced(const char *parent, const uint32_t *ids,
                                    uint32_t count, const char *out_path)
{
    assert(parent != NULL && out_path != NULL);
    assert(ids != NULL || count == 0u);
    rcut_ind_ctx_t c;
    memset(&c, 0, sizeof c);
    c.ids = ids;
    c.count = count;
    c.out_path = out_path;
    c.st = SRMECH_OK;
    srmech_status_t st = fiedler_file_scan(parent, rcut_ind_rec, &c);
    if (st != SRMECH_OK) { return st; }
    return rcut_ind_flush(&c);          /* always runs: creates an empty file too */
}

/* Driver state — the on-disk layout plus the arena slices, carried between the
 * ≤60-line helpers so none of them needs a 14-parameter signature. */
typedef struct rcut_state {
    char      queue_dir[RCUT_PATH_MAX];
    char      tomes_dir[RCUT_PATH_MAX];
    char      graph_path[RCUT_PATH_MAX];
    char      sub_path[RCUT_PATH_MAX];
    uint32_t *ids;        /* the popped set, ascending          (n)          */
    uint32_t *scratch;    /* stable left|right partition buffer (n)          */
    uint32_t *stack;      /* LIFO of (serial, depth)            (2*(n+2))    */
    uint32_t  sp;         /* stack depth, in ENTRIES                          */
    double   *fv;         /* Fiedler vector                     (n doubles)  */
    double   *ws;         /* Fiedler scratch                    (8n doubles) */
    uint32_t  n;          /* node count == the ids/scratch capacity           */
    uint32_t  n_tomes;
    uint32_t  serial;
    uint64_t  resolved;   /* §101: Σ finalized-tome sizes (exact, monotone)  */
} rcut_state_t;

/* Retire a node set into tome slot `n_tomes`. `src` != NULL MOVES the existing
 * file (never copies — the queue's whole low-RAM point); `src` == NULL writes
 * `ids` out fresh (the uncuttable-block path, whose set file is already gone). */
static srmech_status_t rcut_emit_tome(rcut_state_t *s, const char *src,
                                      const uint32_t *ids, uint32_t count,
                                      uint32_t *sizes_out, char *paths_out,
                                      size_t paths_cap)
{
    assert(s != NULL);
    assert(sizes_out != NULL && paths_out != NULL);
    if ((size_t)s->n_tomes >= paths_cap) { return SRMECH_ERR_OVERFLOW; }
    char dest[RCUT_PATH_MAX];
    srmech_status_t st = rcut_path(dest, sizeof dest, s->tomes_dir,
                                   "tome_", s->n_tomes);
    if (st != SRMECH_OK) { return st; }
    st = (src != NULL) ? srmech_plat_file_replace(src, dest)
                       : rcut_write_set(dest, ids, count);
    if (st != SRMECH_OK) { return st; }
    memcpy(paths_out + (size_t)s->n_tomes * RCUT_PATH_MAX, dest, sizeof dest);
    sizes_out[s->n_tomes] = count;
    s->n_tomes += 1u;
    return SRMECH_OK;
}

/* Create work_dir/queue + work_dir/tomes and seed the queue with the root set
 * 0..n-1 (ascending — the invariant every later binary-search relabel rides). */
static srmech_status_t rcut_setup(rcut_state_t *s, uint32_t n,
                                  const char *work_dir, const char *edges_path)
{
    assert(s != NULL);
    assert(work_dir != NULL && edges_path != NULL);
    int k = snprintf(s->queue_dir, sizeof s->queue_dir, "%s/queue", work_dir);
    int k2 = snprintf(s->tomes_dir, sizeof s->tomes_dir, "%s/tomes", work_dir);
    int k3 = snprintf(s->sub_path, sizeof s->sub_path, "%s/sub.bin", work_dir);
    int k4 = snprintf(s->graph_path, sizeof s->graph_path, "%s", edges_path);
    if (k < 0 || (size_t)k >= sizeof s->queue_dir ||
        k2 < 0 || (size_t)k2 >= sizeof s->tomes_dir ||
        k3 < 0 || (size_t)k3 >= sizeof s->sub_path ||
        k4 < 0 || (size_t)k4 >= sizeof s->graph_path) {
        return SRMECH_ERR_OVERFLOW;
    }
    srmech_status_t st = srmech_plat_mkdir(work_dir);
    if (st != SRMECH_OK) { return st; }
    st = srmech_plat_mkdir(s->queue_dir);
    if (st != SRMECH_OK) { return st; }
    st = srmech_plat_mkdir(s->tomes_dir);
    if (st != SRMECH_OK) { return st; }
    for (uint32_t i = 0u; i < n; i++) { s->ids[i] = i; }
    char root[RCUT_PATH_MAX];
    st = rcut_path(root, sizeof root, s->queue_dir, "set_", 0u);
    if (st != SRMECH_OK) { return st; }
    st = rcut_write_set(root, s->ids, n);
    if (st != SRMECH_OK) { return st; }
    s->stack[0] = 0u;        /* serial 0 */
    s->stack[1] = 0u;        /* depth  0 */
    s->sp = 1u;
    s->serial = 1u;
    return SRMECH_OK;
}

/* §101 CLEAN partial: promote every STILL-PENDING set to a coarse, uncut tome.
 * Finalized + promoted still partition ALL n nodes — a valid (coarser)
 * partition plus a status, never a torn strand. Mirrors the Python promotion
 * order exactly (stack index 0 upward == the `pending` list in order). */
static srmech_status_t rcut_cancel(rcut_state_t *s, uint32_t *sizes_out,
                                   char *paths_out, size_t paths_cap)
{
    assert(s != NULL);
    assert(sizes_out != NULL && paths_out != NULL);
    for (uint32_t i = 0u; i < s->sp; i++) {
        char sp_path[RCUT_PATH_MAX];
        srmech_status_t st = rcut_path(sp_path, sizeof sp_path, s->queue_dir,
                                       "set_", s->stack[(size_t)i * 2u]);
        if (st != SRMECH_OK) { return st; }
        size_t bytes = 0u;
        st = srmech_plat_file_size(sp_path, &bytes);
        if (st != SRMECH_OK) { return st; }
        uint32_t count = (uint32_t)(bytes / RCUT_NODE_REC);
        st = rcut_emit_tome(s, sp_path, NULL, count, sizes_out, paths_out,
                            paths_cap);
        if (st != SRMECH_OK) { return st; }
    }
    s->sp = 0u;
    return srmech_plat_file_remove(s->sub_path);
}

/* One bisection: stream the induced sub-graph, run the streaming Fiedler, and
 * SIGN-SPLIT it. `*out_nleft` == 0 or == count means an uncuttable homogeneous
 * block (the caller then emits it whole). The split is stable — both sides keep
 * the parent's relative order, which is what preserves the ASCENDING invariant
 * that rcut_find_local's binary search depends on. */
static srmech_status_t rcut_bisect(rcut_state_t *s, uint32_t count,
                                   uint32_t max_iters, uint32_t *out_nleft)
{
    assert(s != NULL);
    assert(out_nleft != NULL && count >= 2u);
    srmech_status_t st = rcut_induced(s->graph_path, s->ids, count, s->sub_path);
    if (st != SRMECH_OK) { return st; }
    /* rc307: fiedler_sparse_file now guards ws_len in BYTES (was a DOUBLES count).
     * s->ws spans exactly 8n doubles up to s->fv, so for count <= n the arena is
     * always sufficient — but the SIZE we pass must be BYTES to match the flipped
     * guard, else this internal caller under-sizes the workspace 8x and corrupts. */
    st = srmech_laplacian_fiedler_sparse_file(count, s->sub_path, max_iters,
                                              s->fv, s->ws,
                                              srmech_laplacian_fiedler_sparse_arena_bytes(count));
    if (st != SRMECH_OK) { return st; }
    uint32_t nl = 0u;
    for (uint32_t i = 0u; i < count; i++) {         /* Class-K pin-slot at 0 */
        if (s->fv[i] < 0.0) { s->scratch[nl] = s->ids[i]; nl += 1u; }
    }
    uint32_t nr = nl;
    for (uint32_t i = 0u; i < count; i++) {
        if (!(s->fv[i] < 0.0)) { s->scratch[nr] = s->ids[i]; nr += 1u; }
    }
    assert(nr == count);
    *out_nleft = nl;
    return SRMECH_OK;
}

/* Write the two children out and push them LIFO. Python appends left then
 * right and pops from the END, so RIGHT is processed first — mirrored here so
 * the tome ORDER (and therefore every tome file name) matches byte-for-byte. */
static srmech_status_t rcut_push_children(rcut_state_t *s, uint32_t count,
                                          uint32_t nleft, uint32_t depth)
{
    assert(s != NULL);
    assert(nleft > 0u && nleft < count);
    char lp[RCUT_PATH_MAX];
    char rp[RCUT_PATH_MAX];
    uint32_t ls = s->serial;
    uint32_t rs = s->serial + 1u;
    s->serial += 2u;
    srmech_status_t st = rcut_path(lp, sizeof lp, s->queue_dir, "set_", ls);
    if (st != SRMECH_OK) { return st; }
    st = rcut_path(rp, sizeof rp, s->queue_dir, "set_", rs);
    if (st != SRMECH_OK) { return st; }
    st = rcut_write_set(lp, s->scratch, nleft);
    if (st != SRMECH_OK) { return st; }
    st = rcut_write_set(rp, s->scratch + nleft, count - nleft);
    if (st != SRMECH_OK) { return st; }
    s->stack[(size_t)s->sp * 2u]      = ls;
    s->stack[(size_t)s->sp * 2u + 1u] = depth + 1u;
    s->sp += 1u;
    s->stack[(size_t)s->sp * 2u]      = rs;
    s->stack[(size_t)s->sp * 2u + 1u] = depth + 1u;
    s->sp += 1u;
    return SRMECH_OK;
}

/* Carve the caller arena: 9n doubles then 4n+4 uint32 (doubles first so the
 * strictest alignment is satisfied by the arena base itself). */
static void rcut_carve(rcut_state_t *s, uint32_t n, double *ws)
{
    assert(s != NULL);
    assert(ws != NULL);
    s->n  = n;
    s->ws = ws;
    s->fv = ws + (size_t)8u * n;
    uint32_t *u = (uint32_t *)(void *)(ws + (size_t)9u * n);
    s->ids     = u;
    s->scratch = u + (size_t)n;
    s->stack   = u + (size_t)2u * n;
}

/* ONE pop of the work queue: retire the set as a tome, or bisect it and push
 * the two children. The three terminal conditions mirror the Python driver
 * exactly — at-or-under max_tome, under 2 nodes, or at the depth guard. */
static srmech_status_t rcut_step(rcut_state_t *s, uint32_t max_tome,
                                 uint32_t max_iters, uint32_t max_depth,
                                 uint32_t *sizes_out, char *paths_out,
                                 size_t paths_cap)
{
    assert(s != NULL);
    assert(s->sp > 0u);
    s->sp -= 1u;
    uint32_t serial = s->stack[(size_t)s->sp * 2u];
    uint32_t depth  = s->stack[(size_t)s->sp * 2u + 1u];
    char set_path[RCUT_PATH_MAX];
    srmech_status_t st = rcut_path(set_path, sizeof set_path, s->queue_dir,
                                   "set_", serial);
    if (st != SRMECH_OK) { return st; }
    uint32_t count = 0u;
    st = rcut_read_set(set_path, s->ids, s->n, &count);
    if (st != SRMECH_OK) { return st; }
    if (count <= max_tome || count < 2u || depth >= max_depth) {
        st = rcut_emit_tome(s, set_path, NULL, count, sizes_out, paths_out,
                            paths_cap);
        if (st != SRMECH_OK) { return st; }
        s->resolved += count;
        return SRMECH_OK;
    }
    uint32_t nleft = 0u;
    st = rcut_bisect(s, count, max_iters, &nleft);
    if (st != SRMECH_OK) { return st; }
    st = srmech_plat_file_remove(set_path);
    if (st != SRMECH_OK) { return st; }
    if (nleft == 0u || nleft == count) {      /* uncuttable homogeneous block */
        st = rcut_emit_tome(s, NULL, s->ids, count, sizes_out, paths_out,
                            paths_cap);
        if (st != SRMECH_OK) { return st; }
        s->resolved += count;
        return SRMECH_OK;
    }
    return rcut_push_children(s, count, nleft, depth);
}

srmech_status_t srmech_laplacian_recursive_cut(uint32_t                  n,
                                               const char               *edges_path,
                                               const char               *work_dir,
                                               uint32_t                  max_tome,
                                               uint32_t                  max_iters,
                                               uint32_t                  max_depth,
                                               uint32_t                 *tome_sizes_out,
                                               char                     *tome_paths_out,
                                               size_t                    paths_cap,
                                               uint32_t                 *n_tomes_out,
                                               double                   *ws,
                                               size_t                    ws_len,
                                               srmech_progress_tick_cb_t tick,
                                               void                     *tick_user)
{
    if (edges_path == NULL || work_dir == NULL || tome_sizes_out == NULL ||
        tome_paths_out == NULL || n_tomes_out == NULL || ws == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (ws_len < srmech_laplacian_recursive_cut_arena_bytes(n)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    assert(ws_len >= srmech_laplacian_recursive_cut_arena_bytes(n));
    assert(n_tomes_out != NULL);
    rcut_state_t s;
    memset(&s, 0, sizeof s);
    rcut_carve(&s, n, ws);
    *n_tomes_out = 0u;
    /* NO n == 0 early-out: the Python projection seeds the queue with the empty
     * root set and retires it as ONE empty tome, so an early return here would
     * be a real byte-parity divergence (caught by the rc284 parity matrix).
     * The capability is the invariant — C mirrors the shipped contract. */
    srmech_status_t st = rcut_setup(&s, n, work_dir, edges_path);
    if (st != SRMECH_OK) { return st; }
    while (s.sp > 0u) {
        if (tick != NULL) {
            srmech_progress_ev_t ev = { (uint32_t)sizeof(srmech_progress_ev_t),
                                        (uint32_t)SRMECH_PHASE_PARTITIONING,
                                        s.resolved, (uint64_t)n };
            if (tick(&ev, tick_user) != 0) {
                st = rcut_cancel(&s, tome_sizes_out, tome_paths_out, paths_cap);
                *n_tomes_out = s.n_tomes;
                return (st == SRMECH_OK) ? SRMECH_CANCELLED : st;
            }
        }
        st = rcut_step(&s, max_tome, max_iters, max_depth, tome_sizes_out,
                       tome_paths_out, paths_cap);
        if (st != SRMECH_OK) { return st; }
    }
    st = srmech_plat_file_remove(s.sub_path);
    if (st != SRMECH_OK) { return st; }
    if (tick != NULL) {                    /* §101 terminal 100% heartbeat */
        srmech_progress_ev_t ev = { (uint32_t)sizeof(srmech_progress_ev_t),
                                    (uint32_t)SRMECH_PHASE_PARTITIONING,
                                    s.resolved, (uint64_t)n };
        (void)tick(&ev, tick_user);        /* return ignored — already done */
    }
    *n_tomes_out = s.n_tomes;
    return SRMECH_OK;
}

/* ================================================================== *
 * §100 G3 (rc321, task #904): the WHOLE-OP GRAPH PARTITION —
 * srmech_genome_graph_partition. Composes srmech_laplacian_recursive_cut (the
 * out-of-core community assignment) with an EXACT-INTEGER participation read
 * (cross/tot per node, streamed once from the same packed edge file), the
 * antimode histogram DECISION, a per-node nuclear/plasmid classify, and group
 * assembly — all in C, so a bare-C host builds the whole partition. Mirrors the
 * pure srmech.amsc.genome.genome_partition body BIT-FOR-BIT (ADR-0009: the two
 * projections emit the SAME structure). NEVER abs — every value is non-negative.
 * ================================================================== */

/* Class-I gcd for the exact participation reduction (den never fractional). */
static uint64_t ggp_gcd(uint64_t a, uint64_t b)
{
    assert(a <= UINT64_MAX);
    assert(b <= UINT64_MAX);
    while (b != 0u) {
        uint64_t t = a % b;
        a = b;
        b = t;
    }
    return a;
}

/* Reduce a non-negative (num, den); den == 0 -> (0, 1). Mirrors _reduce_pair. */
static void ggp_reduce(uint64_t num, uint64_t den, uint64_t *rn, uint64_t *rd)
{
    assert(rn != NULL);
    assert(rd != NULL);
    if (den == 0u) {
        *rn = 0u;
        *rd = 1u;
        return;
    }
    uint64_t g = ggp_gcd(num, den);
    if (g == 0u) {
        g = 1u;
    }
    *rn = num / g;
    *rd = den / g;
}

/* Participation accumulator: per-node cross/tot exact integer mass (undirected;
 * a self-loop adds to tot twice, never to cross — same community). */
typedef struct ggp_part_ctx {
    uint32_t        n;
    const uint32_t *community;
    uint64_t       *cross;
    uint64_t       *tot;
} ggp_part_ctx_t;

static srmech_status_t ggp_part_cb(uint32_t u, uint32_t v, double w, void *ctx)
{
    ggp_part_ctx_t *c = (ggp_part_ctx_t *)ctx;
    assert(c != NULL);
    assert(c->cross != NULL && c->tot != NULL);
    if (u >= c->n || v >= c->n) {
        return SRMECH_ERR_BAD_INPUT;
    }
    assert(w >= 0.0);                        /* genome weights are non-negative ints */
    uint64_t iw = (uint64_t)w;               /* exact: write_packed_graph stored an int */
    c->tot[u] += iw;
    c->tot[v] += iw;
    if (c->community[u] != c->community[v]) {
        c->cross[u] += iw;
        c->cross[v] += iw;
    }
    return SRMECH_OK;
}

/* Read each tome back and stamp community_out[node] = tome index (cid). The tomes
 * partition ALL n nodes, so every node is assigned exactly once. */
static srmech_status_t ggp_read_communities(const char *paths, uint32_t n_tomes,
                                            uint32_t *ids, uint32_t cap,
                                            uint32_t *community_out)
{
    assert(paths != NULL);
    assert(ids != NULL || cap == 0u);
    for (uint32_t cid = 0u; cid < n_tomes; cid++) {
        const char *path = paths + (size_t)cid * SRMECH_RECURSIVE_CUT_PATH_MAX;
        uint32_t count = 0u;
        srmech_status_t st = rcut_read_set(path, ids, cap, &count);
        if (st != SRMECH_OK) {
            return st;
        }
        for (uint32_t i = 0u; i < count; i++) {
            assert(ids[i] < cap);
            community_out[ids[i]] = cid;
        }
    }
    return SRMECH_OK;
}

/* The participation histogram bin of one node — pure integer, mirrors
 * _partition_bin: floor(cross*n_bins / tot) clamped to [0, n_bins-1]; tot==0 -> 0. */
static uint32_t ggp_bin(uint64_t cross_v, uint64_t tot_v, uint32_t n_bins)
{
    assert(n_bins >= 2u);
    assert(cross_v <= tot_v);                /* participation <= 1 (cross subset of tot) */
    if (tot_v == 0u) {
        return 0u;
    }
    uint64_t b = (cross_v * (uint64_t)n_bins) / tot_v;
    if (b >= (uint64_t)n_bins) {
        return n_bins - 1u;
    }
    return (uint32_t)b;
}

/* Fill node_bin[] + the counts[] histogram over all n nodes. */
static void ggp_histogram(const uint64_t *cross, const uint64_t *tot, uint32_t n,
                          uint32_t n_bins, uint32_t *node_bin, uint64_t *counts)
{
    assert(counts != NULL);
    assert(node_bin != NULL || n == 0u);
    for (uint32_t b = 0u; b < n_bins; b++) {
        counts[b] = 0u;
    }
    for (uint32_t v = 0u; v < n; v++) {
        uint32_t b = ggp_bin(cross[v], tot[v], n_bins);
        node_bin[v] = b;
        counts[b] += 1u;
    }
}

/* The bin of the maximum count in counts[lo..hi] (lowest index on a tie) — the
 * dominant mode of one side of a gap. Mirrors _side_argmax. */
static uint32_t ggp_side_argmax(const uint64_t *counts, uint32_t lo, uint32_t hi)
{
    assert(counts != NULL);
    assert(lo <= hi);
    uint32_t best = lo;
    for (uint32_t b = lo; b <= hi; b++) {
        if (counts[b] > counts[best]) {
            best = b;
        }
    }
    return best;
}

/* min(counts[lo_occ+1 : hi_occ]) — the in-gap antimode. width >= 2 guarantees at
 * least one in-between bin. Mirrors the Python slice-min. */
static uint64_t ggp_valley_min(const uint64_t *counts, uint32_t lo_occ, uint32_t hi_occ)
{
    assert(counts != NULL);
    assert(hi_occ >= lo_occ + 2u);
    uint64_t m = counts[lo_occ + 1u];
    for (uint32_t b = lo_occ + 2u; b < hi_occ; b++) {
        if (counts[b] < m) {
            m = counts[b];
        }
    }
    return m;
}

/* The widest qualifying antimode gap between consecutive OCCUPIED bins (ties ->
 * larger smaller-mode, then the lower bin — the FIRST maximum is kept). */
typedef struct ggp_gap { int have; uint32_t width; uint64_t smaller;
                         uint32_t lo; uint32_t hi; } ggp_gap_t;

static ggp_gap_t ggp_scan_gaps(const uint64_t *counts, uint32_t n_bins)
{
    assert(counts != NULL);
    assert(n_bins >= 2u);
    ggp_gap_t best = { 0, 0u, 0u, 0u, 0u };
    int have_prev = 0;
    uint32_t prev = 0u;
    for (uint32_t b = 0u; b < n_bins; b++) {
        if (counts[b] == 0u) {
            continue;
        }
        if (have_prev && (b - prev) >= 2u) {
            uint32_t lo = prev, hi = b;
            uint64_t pl = counts[ggp_side_argmax(counts, 0u, lo)];
            uint64_t ph = counts[ggp_side_argmax(counts, hi, n_bins - 1u)];
            uint64_t smaller = (pl < ph) ? pl : ph;
            uint64_t valley = ggp_valley_min(counts, lo, hi);
            uint32_t width = hi - lo;
            if (smaller >= 2u && 2u * valley < smaller &&
                (!best.have || width > best.width ||
                 (width == best.width && smaller > best.smaller))) {
                best.have = 1; best.width = width; best.smaller = smaller;
                best.lo = lo; best.hi = hi;
            }
        }
        have_prev = 1;
        prev = b;
    }
    return best;
}

/* MEASURE the antimode + the single mode, filling the scalar result fields.
 * Mirrors _partition_antimode: unimodal defaults, then the widest qualifying gap. */
static void ggp_antimode(const uint64_t *counts, uint32_t n_bins,
                         srmech_genome_graph_partition_result_t *r)
{
    assert(counts != NULL);
    assert(r != NULL);
    uint32_t mode_bin = 0u;
    uint32_t n_occ = 0u;
    for (uint32_t b = 0u; b < n_bins; b++) {
        if (counts[b] > counts[mode_bin]) {
            mode_bin = b;
        }
        if (counts[b] > 0u) {
            n_occ += 1u;
        }
    }
    r->bimodal = 0u;
    r->threshold_bin = -1; r->peak_low_bin = -1; r->peak_high_bin = -1;
    r->valley_count = -1; r->gap = 0u; r->mode_bin = mode_bin;
    if (n_occ < 2u) {
        return;
    }
    ggp_gap_t g = ggp_scan_gaps(counts, n_bins);
    if (!g.have) {
        return;
    }
    uint64_t valley = ggp_valley_min(counts, g.lo, g.hi);
    r->bimodal = 1u;
    r->threshold_bin = (int32_t)g.lo;
    r->peak_low_bin = (int32_t)ggp_side_argmax(counts, 0u, g.lo);
    r->peak_high_bin = (int32_t)ggp_side_argmax(counts, g.hi, n_bins - 1u);
    r->valley_count = (int64_t)valley;
    r->gap = g.smaller - valley;
}

/* Per-node type: nuclear=0, plasmid=1. Mirrors the classify branch. */
static uint32_t ggp_node_type(uint32_t node_bin_v, int bimodal, int32_t threshold,
                              uint32_t one_dna)
{
    assert(one_dna <= 1u);
    assert(bimodal == 0 || bimodal == 1);
    if (bimodal) {
        return (node_bin_v > (uint32_t)threshold) ? 1u : 0u;
    }
    return one_dna;
}

/* Group OUT surface — the caller's per-group arrays + the flat member cursor. */
typedef struct ggp_group_out {
    uint32_t *comm;
    uint32_t *type;
    uint32_t *size;
    uint64_t *num;
    uint64_t *den;
    uint32_t *members;
    uint32_t  cap;
    uint32_t  n_groups;
    uint32_t  n_members;
} ggp_group_out_t;

/* Emit community `cid`'s nuclear group THEN its plasmid group (empty groups
 * skipped), members in ascending tome order — mirrors the Python group loop. */
static srmech_status_t ggp_emit_community_groups(
    const char *paths, uint32_t cid, uint32_t *ids, uint32_t cap,
    const uint64_t *cross, const uint64_t *tot, const uint32_t *node_bin,
    int bimodal, int32_t threshold, uint32_t one_dna, ggp_group_out_t *go)
{
    assert(paths != NULL && go != NULL);
    assert(ids != NULL || cap == 0u);
    const char *path = paths + (size_t)cid * SRMECH_RECURSIVE_CUT_PATH_MAX;
    uint32_t count = 0u;
    srmech_status_t st = rcut_read_set(path, ids, cap, &count);
    if (st != SRMECH_OK) {
        return st;
    }
    for (uint32_t gt = 0u; gt < 2u; gt++) {
        uint64_t gc = 0u, gtt = 0u;
        uint32_t start = go->n_members, size = 0u;
        for (uint32_t i = 0u; i < count; i++) {
            uint32_t vv = ids[i];
            if (ggp_node_type(node_bin[vv], bimodal, threshold, one_dna) != gt) {
                continue;
            }
            go->members[start + size] = vv;
            gc += cross[vv];
            gtt += tot[vv];
            size += 1u;
        }
        if (size == 0u) {
            continue;
        }
        if (go->n_groups >= go->cap) {
            return SRMECH_ERR_OVERFLOW;
        }
        go->comm[go->n_groups] = cid;
        go->type[go->n_groups] = gt;
        go->size[go->n_groups] = size;
        ggp_reduce(gc, gtt, &go->num[go->n_groups], &go->den[go->n_groups]);
        go->n_groups += 1u;
        go->n_members += size;
    }
    return SRMECH_OK;
}

/* The driver's carved arena slices — doubles first (the recursive_cut sub-arena),
 * then the uint64 accumulators, then the uint32 scratch + the tome-path buffer. */
typedef struct ggp_state {
    uint32_t  n;
    uint32_t  n_bins;
    uint32_t  n_tomes;
    double   *rc_ws;
    uint64_t *cross;
    uint64_t *tot;
    uint64_t *counts;
    uint32_t *sizes;
    uint32_t *node_bin;
    uint32_t *ids;
    char     *paths;
} ggp_state_t;

static void ggp_carve(uint32_t n, uint32_t n_bins, size_t paths_cap, void *ws,
                      ggp_state_t *s)
{
    assert(ws != NULL);
    assert(s != NULL);
    s->n = n; s->n_bins = n_bins; s->n_tomes = 0u;
    unsigned char *base = (unsigned char *)ws;
    size_t rc = srmech_laplacian_recursive_cut_arena_bytes(n);
    rc = (rc + 7u) & ~(size_t)7u;
    s->rc_ws = (double *)(void *)base;
    uint64_t *q = (uint64_t *)(void *)(base + rc);
    s->cross = q; q += n;
    s->tot = q; q += n;
    s->counts = q; q += n_bins;
    uint32_t *d = (uint32_t *)(void *)q;
    s->sizes = d; d += paths_cap;
    s->node_bin = d; d += n;
    s->ids = d; d += n;
    s->paths = (char *)(void *)d;
}

size_t srmech_genome_graph_partition_arena_bytes(uint32_t n, uint32_t n_edges,
                                                 uint32_t n_bins, size_t paths_cap)
{
    (void)n_edges;                           /* participation STREAMS the file */
    assert(n_bins >= 2u);
    assert(paths_cap >= 1u);
    size_t rc = srmech_laplacian_recursive_cut_arena_bytes(n);
    rc = (rc + 7u) & ~(size_t)7u;
    size_t u64s = ((size_t)2u * n + n_bins) * sizeof(uint64_t);   /* cross,tot,counts */
    size_t u32s = (paths_cap + (size_t)2u * n) * sizeof(uint32_t);/* sizes,node_bin,ids */
    size_t paths = paths_cap * SRMECH_RECURSIVE_CUT_PATH_MAX;
    return rc + u64s + u32s + paths;
}

/* recursive_cut + read the community assignment back. On a §101 cancel the tomes
 * still partition ALL n nodes, so the community read is valid either way. */
static srmech_status_t ggp_step_cut(ggp_state_t *s, const char *edges_path,
    const char *work_dir, uint32_t max_tome, uint32_t max_iters, uint32_t max_depth,
    uint32_t *community_out, srmech_progress_tick_cb_t tick, void *tick_ctx,
    int *cancelled)
{
    assert(s != NULL && cancelled != NULL);
    assert(edges_path != NULL && work_dir != NULL);
    size_t paths_cap = (size_t)s->n + 1u;
    srmech_status_t st = srmech_laplacian_recursive_cut(
        s->n, edges_path, work_dir, max_tome, max_iters, max_depth,
        s->sizes, s->paths, paths_cap, &s->n_tomes, s->rc_ws,
        srmech_laplacian_recursive_cut_arena_bytes(s->n), tick, tick_ctx);
    *cancelled = (st == SRMECH_CANCELLED) ? 1 : 0;
    if (st != SRMECH_OK && st != SRMECH_CANCELLED) {
        return st;
    }
    return ggp_read_communities(s->paths, s->n_tomes, s->ids, s->n, community_out);
}

/* Stream the edge file ONCE -> cross/tot, then reduce per-node participation. */
static srmech_status_t ggp_step_participation(ggp_state_t *s, const char *edges_path,
    const uint32_t *community, uint64_t *part_num_out, uint64_t *part_den_out)
{
    assert(s != NULL && edges_path != NULL);
    assert(part_num_out != NULL && part_den_out != NULL);
    for (uint32_t v = 0u; v < s->n; v++) {
        s->cross[v] = 0u;
        s->tot[v] = 0u;
    }
    ggp_part_ctx_t pc;
    pc.n = s->n; pc.community = community; pc.cross = s->cross; pc.tot = s->tot;
    srmech_status_t st = fiedler_file_scan(edges_path, ggp_part_cb, &pc);
    if (st != SRMECH_OK) {
        return st;
    }
    for (uint32_t v = 0u; v < s->n; v++) {
        ggp_reduce(s->cross[v], s->tot[v], &part_num_out[v], &part_den_out[v]);
    }
    return SRMECH_OK;
}

/* Histogram + antimode + one_dna_type. */
static void ggp_step_antimode(ggp_state_t *s, uint64_t *counts_out,
                              srmech_genome_graph_partition_result_t *r)
{
    assert(s != NULL && counts_out != NULL);
    assert(r != NULL);
    ggp_histogram(s->cross, s->tot, s->n, s->n_bins, s->node_bin, s->counts);
    for (uint32_t b = 0u; b < s->n_bins; b++) {
        counts_out[b] = s->counts[b];
    }
    ggp_antimode(s->counts, s->n_bins, r);
    if (r->bimodal) {
        r->one_dna_type = -1;                /* None — the split fixes each node */
    } else {
        r->one_dna_type =
            ((uint64_t)r->mode_bin * 2u < (uint64_t)s->n_bins) ? 0 : 1;
    }
}

/* Build the groups per community + tally the per-type node counts. */
static srmech_status_t ggp_step_groups(ggp_state_t *s,
    srmech_genome_graph_partition_result_t *r, ggp_group_out_t *go)
{
    assert(s != NULL && r != NULL && go != NULL);
    assert(go->members != NULL || s->n == 0u);
    int bimodal = (int)r->bimodal;
    int32_t threshold = r->threshold_bin;
    uint32_t one_dna = (r->one_dna_type < 0) ? 0u : (uint32_t)r->one_dna_type;
    for (uint32_t cid = 0u; cid < s->n_tomes; cid++) {
        srmech_status_t st = ggp_emit_community_groups(
            s->paths, cid, s->ids, s->n, s->cross, s->tot, s->node_bin,
            bimodal, threshold, one_dna, go);
        if (st != SRMECH_OK) {
            return st;
        }
    }
    uint64_t nuc = 0u, pla = 0u;
    for (uint32_t g = 0u; g < go->n_groups; g++) {
        if (go->type[g] == 0u) {
            nuc += go->size[g];
        } else {
            pla += go->size[g];
        }
    }
    r->node_nuclear = nuc;
    r->node_plasmid = pla;
    return SRMECH_OK;
}

srmech_status_t srmech_genome_graph_partition(
    uint32_t n, const char *edges_path, const char *work_dir,
    uint32_t max_tome, uint32_t n_bins, uint32_t max_iters, uint32_t max_depth,
    uint32_t *community_out, uint64_t *part_num_out, uint64_t *part_den_out,
    uint64_t *counts_out,
    uint32_t *group_comm_out, uint32_t *group_type_out, uint32_t *group_size_out,
    uint64_t *group_num_out, uint64_t *group_den_out,
    uint32_t *group_members_out, uint32_t groups_cap,
    srmech_genome_graph_partition_result_t *result_out,
    void *ws, size_t ws_len,
    srmech_progress_tick_cb_t tick, void *tick_ctx)
{
    if (edges_path == NULL || work_dir == NULL || community_out == NULL ||
        part_num_out == NULL || part_den_out == NULL || counts_out == NULL ||
        group_comm_out == NULL || group_type_out == NULL || group_size_out == NULL ||
        group_num_out == NULL || group_den_out == NULL || group_members_out == NULL ||
        result_out == NULL || ws == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n_bins < 2u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    size_t paths_cap = (size_t)n + 1u;
    size_t need = srmech_genome_graph_partition_arena_bytes(n, 0u, n_bins, paths_cap);
    if (ws_len < need) {
        return SRMECH_ERR_BAD_INPUT;
    }
    assert(ws_len >= need);
    assert(result_out != NULL);
    ggp_state_t s;
    ggp_carve(n, n_bins, paths_cap, ws, &s);
    memset(result_out, 0, sizeof *result_out);
    result_out->struct_size = (uint32_t)sizeof *result_out;
    int cancelled = 0;
    srmech_status_t st = ggp_step_cut(&s, edges_path, work_dir, max_tome, max_iters,
                                      max_depth, community_out, tick, tick_ctx,
                                      &cancelled);
    if (st != SRMECH_OK && st != SRMECH_CANCELLED) {
        return st;
    }
    result_out->n_communities = s.n_tomes;
    result_out->cancelled = (uint32_t)(cancelled ? 1 : 0);
    if (cancelled) {
        return SRMECH_CANCELLED;              /* community assignment only (clean partial) */
    }
    st = ggp_step_participation(&s, edges_path, community_out, part_num_out,
                                part_den_out);
    if (st != SRMECH_OK) {
        return st;
    }
    ggp_step_antimode(&s, counts_out, result_out);
    ggp_group_out_t go;
    go.comm = group_comm_out; go.type = group_type_out; go.size = group_size_out;
    go.num = group_num_out; go.den = group_den_out; go.members = group_members_out;
    go.cap = groups_cap; go.n_groups = 0u; go.n_members = 0u;
    st = ggp_step_groups(&s, result_out, &go);
    if (st != SRMECH_OK) {
        return st;
    }
    result_out->n_groups = go.n_groups;
    return SRMECH_OK;
}
