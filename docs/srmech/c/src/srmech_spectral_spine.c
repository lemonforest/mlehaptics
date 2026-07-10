/*
 * srmech_spectral_spine.c — the spectral SPINE of a relational graph
 * (0.9.0rc204; gh#1324 / F1167–F1169).
 *
 * `srmech_spectral_spine` is a Class-L COMPOSITE over the existing kernels —
 * it writes no new eigensolver and no new graph builder: the spine
 *
 *   spine(G) = the top-|component| nodes of the DOMINANT eigenvector of the
 *              (signed) graph Laplacian L = D̄ − A
 *
 * completes the community/spine PAIR srmech already ships. The LOW modes are
 * community structure (srmech_laplacian_fiedler_sparse = 2-way normalized cut,
 * srmech_three_fold_bands = 3-way band split); the DOMINANT mode (largest λ)
 * concentrates on the structurally CENTRAL items — its top-|component| nodes
 * ARE the spine. Domain-free (edges = any relational graph).
 *
 * Kernels reused (no re-implementation here):
 *   - srmech_graph_dense_adjacency         (A from the edge list)   [Class L]
 *   - srmech_hermitian_eigendecompose_ws   (ascending spectrum + eigenvectors)
 *
 * The signed degree D̄_ii = Σ_j |A_ij| uses the Class-K magnitude of each
 * coupling (an explicit sign branch, NOT fabs) so L is PSD even with negative
 * (frustrated) edges (mirrors srmech.amsc.laplacian.signed_laplacian). The
 * top-k selection ranks by |component|² = re²+im² (a Class-K magnitude-square,
 * NO fabs / NO sqrt), descending, ties broken by ascending index — bit-matching
 * the Python op's sort key.
 *
 * NUMERIC (FPU-tol): the eigenvector basis is non-unique, so native == pure
 * agrees WITHIN-TOL (the selected index set / order is stable for a
 * non-degenerate dominant eigenvalue), NOT byte-for-byte — contrast the
 * exact-integer ops. Standalone-complete honor ([[feedback_c_must_be_
 * standalone_complete_no_python_fallback]]): all scratch is bump-carved from the
 * CALLER arena `ws` (no malloc, JPL Rule 3) — the bound is the caller's RAM.
 * Size `ws` from srmech_spectral_spine_arena_bytes. The Python op is the
 * COMPLETE alternative implementation for a no-C host (value-parity, not a
 * rescue).
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto)        : OK
 *   - Rule 2 (bounded loops)  : OK — all loops bounded by n / n_edges / k
 *                               (top-k selection bounded k·n)
 *   - Rule 3 (no malloc)      : OK — caller arena bump only
 *   - Rule 4 (≤60 lines/func) : OK — split into build / select helpers
 *   - Rule 5 (≥2 asserts/fn)  : OK
 *   - Rule 7 (return-value)   : OK — srmech_status_t throughout
 *   - Rule 10 (warnings clean): OK — pedantic -Werror
 *
 * License: MIT (parent project: mlehaptics).
 */

#include "srmech.h"

#include <assert.h>
#include <stddef.h>
#include <stdint.h>

/* 8-byte-aligned bump of `need` doubles out of the caller arena (the
 * heat_trace / resonant_spectrum bump pattern). Advances *off; returns NULL
 * (caller maps to OVERFLOW) if the arena is exhausted. */
static double *spine_bump(double *ws, size_t ws_cap, size_t *off, size_t need)
{
    assert(ws != NULL || ws_cap == 0);
    assert(off != NULL);
    if (*off + need > ws_cap) {
        return NULL;
    }
    double *p = ws + *off;
    *off += need;
    return p;
}

/* Build the interleaved-complex signed Laplacian L_il (2·n·n doubles, row-
 * major (re, im) pairs, imag == 0) from the real adjacency A (n·n row-major).
 * L_ii = D̄_ii = Σ_{c≠i} |A_ic| (Class-K magnitude, explicit sign branch — NOT
 * fabs); L_ic = −A_ic for c≠i. Mirrors srmech.amsc.laplacian.signed_laplacian
 * exactly (the A diagonal / self-loop term is dropped, as the Python op does). */
static void spine_signed_laplacian_il(uint32_t n, const double *A, double *L_il)
{
    assert(A != NULL || n == 0);
    assert(L_il != NULL || n == 0);
    for (uint32_t r = 0; r < n; r++) {
        double deg = 0.0;
        for (uint32_t c = 0; c < n; c++) {
            if (c != r) {
                size_t idx = (size_t)r * n + c;
                double a = A[idx];
                deg += (a >= 0.0) ? a : -a;   /* |a| — Class-K, no fabs */
                L_il[idx * 2u] = -a;
                L_il[idx * 2u + 1u] = 0.0;
            }
        }
        size_t d = (size_t)r * n + r;
        L_il[d * 2u] = deg;
        L_il[d * 2u + 1u] = 0.0;
    }
}

/* Select the top-min(k, n) nodes by |component|² of the DOMINANT eigenvector
 * (the LAST column, since srmech_hermitian_eigendecompose_ws sorts eigenvalues
 * ASCENDING) into `out_spine`, descending magnitude, ties by ascending index.
 * `magsq` is n-double scratch. Selection sort (bounded k·n): each pass takes the
 * global max with a STRICT `>` so the lowest index wins on a tie, then removes it
 * by setting its magsq to −1 (magsq = re²+im² ≥ 0 always, so −1 is below any). */
static void spine_select_topk(uint32_t n, const double *V_il, uint32_t k,
                              double *magsq, uint32_t *out_spine,
                              uint32_t *out_count)
{
    assert(V_il != NULL || n == 0);
    assert(magsq != NULL || n == 0);
    assert(out_count != NULL);
    uint32_t col = (n > 0u) ? (n - 1u) : 0u;   /* dominant = largest λ */
    for (uint32_t i = 0; i < n; i++) {
        size_t idx = ((size_t)i * n + col) * 2u;
        double re = V_il[idx];
        double im = V_il[idx + 1u];
        magsq[i] = re * re + im * im;          /* Class-K magnitude-square */
    }
    uint32_t want = (k < n) ? k : n;
    for (uint32_t s = 0; s < want; s++) {
        uint32_t best = 0;
        double best_m = -1.0;
        for (uint32_t i = 0; i < n; i++) {
            if (magsq[i] > best_m) {           /* strict → lowest index on tie */
                best_m = magsq[i];
                best = i;
            }
        }
        out_spine[s] = best;
        magsq[best] = -1.0;                     /* remove the picked node */
    }
    *out_count = want;
}

size_t srmech_spectral_spine_arena_bytes(uint32_t n)
{
    /* Carved doubles: real adjacency A (nn) + interleaved-H signed Laplacian
     * (2nn) + eigenvector staging (2nn) + eigensolve workspace (2nn) + eigvals
     * (n) + magnitude-square scratch (n). Returned in BYTES. n is an eigensolve
     * dim, far below sqrt(SIZE_MAX). */
    size_t nn = (size_t)n * (size_t)n;
    assert(n == 0u || nn / (size_t)n == (size_t)n);   /* n*n no overflow  */
    assert(nn <= SIZE_MAX / (8u * sizeof(double)));   /* 7nn+2n no overflow */
    size_t doubles = nn * 7u + (size_t)n * 2u;
    return doubles * sizeof(double);
}

srmech_status_t srmech_spectral_spine(
    uint32_t        n,
    uint32_t        n_edges,
    const uint32_t *edges_u,
    const uint32_t *edges_v,
    const double   *weights,
    uint32_t        k,
    uint32_t       *out_spine,
    uint32_t       *out_count,
    double         *ws,
    size_t          ws_len)
{
    assert(out_count != NULL);
    assert(n == 0 || ws != NULL);
    if (out_count == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    *out_count = 0;
    if (n == 0) {
        return SRMECH_OK;                    /* empty graph → no spine */
    }
    if (ws == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (k > 0 && out_spine == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n_edges > 0 && (edges_u == NULL || edges_v == NULL)) {
        return SRMECH_ERR_NULL_ARG;
    }
    size_t cap = ws_len / sizeof(double);
    size_t off = 0;
    size_t nn = (size_t)n * (size_t)n;
    double *A = spine_bump(ws, cap, &off, nn);
    double *L_il = spine_bump(ws, cap, &off, nn * 2u);
    double *V = spine_bump(ws, cap, &off, nn * 2u);
    double *eig_ws = spine_bump(ws, cap, &off, nn * 2u);
    double *lam = spine_bump(ws, cap, &off, (size_t)n);
    double *magsq = spine_bump(ws, cap, &off, (size_t)n);
    if (A == NULL || L_il == NULL || V == NULL || eig_ws == NULL
        || lam == NULL || magsq == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    srmech_status_t st = srmech_graph_dense_adjacency(
        n, n_edges, edges_u, edges_v, weights, A);
    if (st != SRMECH_OK) {
        return st;                           /* e.g. out-of-range edge endpoint */
    }
    spine_signed_laplacian_il(n, A, L_il);
    st = srmech_hermitian_eigendecompose_ws(n, L_il, lam, V, eig_ws, nn * 2u);
    if (st != SRMECH_OK) {
        return st;                           /* non-convergent eigensolve */
    }
    spine_select_topk(n, V, k, magsq, out_spine, out_count);
    return SRMECH_OK;
}
