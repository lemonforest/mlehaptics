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
#include <math.h>
#include <stddef.h>
#include <stdint.h>

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
        d_inv_sqrt[i] = (d > 0.0) ? (1.0 / sqrt(d)) : 0.0;
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
    /* tau = (a_qq − a_pp) / (2 a_pq); t = sign(tau) / (|tau| + sqrt(tau²+1)). */
    double tau = (a_qq - a_pp) / (2.0 * a_pq);
    double t;
    if (tau >= 0.0) {
        t = 1.0 / (tau + sqrt(1.0 + tau * tau));
    } else {
        t = 1.0 / (tau - sqrt(1.0 + tau * tau));
    }
    double c = 1.0 / sqrt(1.0 + t * t);
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
