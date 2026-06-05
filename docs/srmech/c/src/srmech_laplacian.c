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
 *   - SRMECH_LAPLACIAN_MAX_NODES = 256 caps the stack-allocated
 *     degree / row-scaling buffers so the C path stays embedded-
 *     safe. Larger graphs fall back to the Python numpy path.
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto)        : OK
 *   - Rule 2 (bounded loops)  : OK — every loop bounded by either a
 *                              caller-supplied size_t (n / n_edges,
 *                              caller's responsibility) or by
 *                              SRMECH_LAPLACIAN_JACOBI_MAX_SWEEPS
 *   - Rule 3 (no malloc)      : OK — fixed-size stack buffers only
 *   - Rule 4 (≤60 lines/func) : OK — Jacobi split into rotation +
 *                              sweep helpers
 *   - Rule 5 (≥2 asserts/fn)  : OK
 *   - Rule 7 (return-value)   : OK — srmech_status_t throughout
 *   - Rule 10 (warnings clean): OK under -Wall -Wextra -Wpedantic
 *
 * License: GPL-3.0-or-later.
 */

#include "srmech.h"

#include <assert.h>
#include <stddef.h>
#include <stdint.h>

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

#define SRMECH_LAPLACIAN_MAX_NODES        256
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
    if (n > SRMECH_LAPLACIAN_MAX_NODES) {
        return SRMECH_ERR_OVERFLOW;
    }
    srmech_status_t st = srmech_graph_dense_adjacency(
        n, n_edges, edges_u, edges_v, weights, out_matrix);
    if (st != SRMECH_OK) {
        return st;
    }
    /* Capture degrees BEFORE we mutate the matrix. Stack-allocated
     * buffer bounded by SRMECH_LAPLACIAN_MAX_NODES. */
    double degree[SRMECH_LAPLACIAN_MAX_NODES];
    for (uint32_t i = 0; i < n; i++) {
        degree[i] = srmech_laplacian_row_degree(n, i, out_matrix);
    }
    /* L = D − A: negate off-diagonals, replace diagonal with degree. */
    for (uint32_t r = 0; r < n; r++) {
        for (uint32_t c = 0; c < n; c++) {
            size_t idx = (size_t)r * n + c;
            if (r == c) {
                out_matrix[idx] = degree[r];
            } else {
                out_matrix[idx] = -out_matrix[idx];
            }
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
    if (n > SRMECH_LAPLACIAN_MAX_NODES) {
        return SRMECH_ERR_OVERFLOW;
    }
    srmech_status_t st = srmech_graph_dense_adjacency(
        n, n_edges, edges_u, edges_v, weights, out_matrix);
    if (st != SRMECH_OK) {
        return st;
    }
    /* Compute d_i^(−1/2). Isolated vertices (degree 0) → 0 (the
     * normalised Laplacian's diagonal is 0, not 1, at isolated
     * vertices by convention). */
    double d_inv_sqrt[SRMECH_LAPLACIAN_MAX_NODES];
    for (uint32_t i = 0; i < n; i++) {
        double d = srmech_laplacian_row_degree(n, i, out_matrix);
        d_inv_sqrt[i] = (d > 0.0) ? (1.0 / lap_sqrt(d)) : 0.0;
    }
    /* L_sym = I − D^(−1/2) A D^(−1/2). */
    for (uint32_t r = 0; r < n; r++) {
        for (uint32_t c = 0; c < n; c++) {
            size_t idx = (size_t)r * n + c;
            double val;
            if (r == c) {
                val = (d_inv_sqrt[r] != 0.0) ? 1.0 : 0.0;
            } else {
                val = -out_matrix[idx] * d_inv_sqrt[r] * d_inv_sqrt[c];
            }
            out_matrix[idx] = val;
        }
    }
    assert(n == 0 || out_matrix != NULL);
    return SRMECH_OK;
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
    assert(n <= SRMECH_LAPLACIAN_MAX_NODES);
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
    if (n > SRMECH_LAPLACIAN_MAX_NODES) {
        return SRMECH_ERR_OVERFLOW;
    }
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
 * Four new ops extending Class L from "graph Laplacian" to
 * "dense-matrix linear algebra including eigendecomposition +
 * matrix-vector multiplication + elementwise operations":
 *
 *   - srmech_hermitian_eigendecompose
 *   - srmech_dense_matvec_complex
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
    assert(n <= SRMECH_LAPLACIAN_MAX_NODES);
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
    /* Phase factor e^(iθ) = γ/|γ| — pure algebra, no atan2. */
    double cosphi = g_re / g_mag;
    double sinphi = g_im / g_mag;
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
    assert(n <= SRMECH_LAPLACIAN_MAX_NODES);
    size_t total = (size_t)n * n * 2;
    for (size_t i = 0; i < total; i++) {
        V_il[i] = 0.0;
    }
    for (uint32_t i = 0; i < n; i++) {
        V_il[((size_t)i * n + i) * 2] = 1.0;
    }
}

/* Helper: sort eigenpairs in ascending eigenvalue order. Selection-
 * sort over n (bounded by SRMECH_LAPLACIAN_MAX_NODES, so O(n²) is
 * embedded-safe). Swaps eigvals[i] with eigvals[min_idx] AND column i
 * of V with column min_idx of V. */
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
    assert(n <= SRMECH_LAPLACIAN_MAX_NODES);
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
    assert(n <= SRMECH_LAPLACIAN_MAX_NODES);
    if (H_interleaved == NULL || out_eigvals == NULL
        || out_eigvecs_interleaved == NULL || workspace == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n > SRMECH_LAPLACIAN_MAX_NODES) {
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

srmech_status_t srmech_hermitian_eigendecompose(
    uint32_t       n,
    const double  *H_interleaved,
    double        *out_eigvals,
    double        *out_eigvecs_interleaved)
{
    assert(out_eigvals != NULL);
    assert(out_eigvecs_interleaved != NULL);
    /* Per-thread workspace (#772 reentrancy). Static duration (a
     * complex 256×256 working matrix is ~1 MiB — too large to stack)
     * but thread-local, so concurrent callers on different threads
     * each get a private copy. Rule-3-clean: static duration, no
     * malloc. Routes through the _ws core so both entries share one
     * numeric path. */
    static SRMECH_THREAD_LOCAL double Hwork[SRMECH_HERMITIAN_WS_MAX];
    return srmech_hermitian_eigendecompose_ws(
        n, H_interleaved, out_eigvals, out_eigvecs_interleaved,
        Hwork, SRMECH_HERMITIAN_WS_MAX);
}

srmech_status_t srmech_dense_matvec_complex(
    uint32_t       rows,
    uint32_t       cols,
    const double  *M_interleaved,
    const double  *v_interleaved,
    double        *out_interleaved)
{
    assert(M_interleaved != NULL);
    assert(out_interleaved != NULL);
    if (M_interleaved == NULL || v_interleaved == NULL
        || out_interleaved == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (rows > SRMECH_LAPLACIAN_MAX_NODES
        || cols > SRMECH_LAPLACIAN_MAX_NODES) {
        return SRMECH_ERR_OVERFLOW;
    }
    for (uint32_t r = 0; r < rows; r++) {
        double acc_re = 0.0;
        double acc_im = 0.0;
        for (uint32_t c = 0; c < cols; c++) {
            size_t mi = ((size_t)r * cols + c) * 2;
            size_t vi = (size_t)c * 2;
            double m_re = M_interleaved[mi];
            double m_im = M_interleaved[mi + 1];
            double v_re = v_interleaved[vi];
            double v_im = v_interleaved[vi + 1];
            acc_re += m_re * v_re - m_im * v_im;
            acc_im += m_re * v_im + m_im * v_re;
        }
        out_interleaved[(size_t)r * 2]     = acc_re;
        out_interleaved[(size_t)r * 2 + 1] = acc_im;
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
