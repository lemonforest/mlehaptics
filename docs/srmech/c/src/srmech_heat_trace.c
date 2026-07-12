/*
 * srmech_heat_trace.c — the spectral theta / heat trace of a Laplacian
 * (0.9.0rc108; issue #1234 Item 2 / F1007).
 *
 * `srmech_heat_trace` is a Class-L COMPOSITE over the existing kernels —
 * it writes no new eigensolver and no new exp: the heat trace
 *
 *   Θ(t) = Tr(e^{−tL}) = Σ_k exp(−t·λ_k)
 *
 * IS a theta function of the Laplacian (on a cycle, the Jacobi-θ family) —
 * the read-independent spectral summary. F1007: under magnetic flux the
 * FULL trace is flux-invariant (Poisson → the modular / holomorphic part)
 * while the flux shadow lives only in the ground state λ_min(Φ) — the
 * companion `srmech_ground_state_flux_response` is that shadow reader.
 *
 * Kernels reused (no re-implementation here):
 *   - srmech_jacobi_eigvals               (real-symmetric spectrum) [Class L]
 *   - srmech_hermitian_eigendecompose_ws  (complex-Hermitian spectrum)
 *   - srmech_exp                          (the Q61 libm-free exp)   [Class N]
 *   - srmech_graph_magnetic_laplacian     (the rc105 chiral builder)
 *
 * Standalone-complete honor ([[feedback_c_must_be_standalone_complete_no_
 * python_fallback]]): all scratch is bump-carved from the CALLER arena `ws`
 * (no malloc, JPL Rule 3) — the bound is the caller's RAM. Size `ws` from
 * srmech_heat_trace_arena_bytes / srmech_ground_state_flux_response_arena_
 * bytes. The Python ops are the COMPLETE alternative implementation for
 * no-C hosts (value-parity, not a rescue).
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto)        : OK
 *   - Rule 2 (bounded loops)  : OK — all loops bounded by n / n_t / n_flux /
 *                               n_edges (insertion sort bounded n²)
 *   - Rule 3 (no malloc)      : OK — caller arena bump only
 *   - Rule 4 (≤60 lines/func) : OK — split into kernel-driver helpers
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

/* Jacobi off-diagonal tolerance — mirrors the Python jacobi_eigvals default
 * so the native / pure real-symmetric spectra agree to Jacobi round-off. */
#define SRMECH_HEAT_JACOBI_TOL 1e-12

/* 8-byte-aligned bump of `need` doubles out of the caller arena (the
 * resonant_spectrum bump pattern). Advances *off; returns NULL (caller maps
 * to OVERFLOW) if the arena is exhausted. */
static double *heat_bump(double *ws, size_t ws_cap, size_t *off, size_t need)
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

/* Ascending insertion sort of the n eigenvalues. srmech_jacobi_eigvals
 * returns the converged diagonal UNSORTED; the Python op sums the spectrum
 * ASCENDING — match that order so the native / pure float sums agree
 * addend-for-addend. Bounded n² (an eigensolve dim; the eigensolve itself
 * is n³). */
static void heat_sort_ascending(uint32_t n, double *v)
{
    assert(v != NULL || n == 0);
    assert(n < 0xFFFFFFFFu);
    for (uint32_t i = 1; i < n; i++) {
        double key = v[i];
        uint32_t j = i;
        while (j > 0 && v[j - 1] > key) {
            v[j] = v[j - 1];
            j--;
        }
        v[j] = key;
    }
}

/* Θ(t) = Σ_k exp(−t·λ_k) for each of the n_t t-values — srmech_exp (the
 * Q61 libm-free Class-N cascade, byte-matched with the Python
 * rational.exp float projection) per term, summed in ascending-λ order. */
static srmech_status_t heat_emit_theta(uint32_t n, const double *lam,
                                       uint32_t n_t, const double *t_values,
                                       double *out_theta)
{
    assert(n == 0 || lam != NULL);
    assert(n_t == 0 || (t_values != NULL && out_theta != NULL));
    for (uint32_t i = 0; i < n_t; i++) {
        double acc = 0.0;
        for (uint32_t k = 0; k < n; k++) {
            double e = 0.0;
            srmech_status_t st = srmech_exp(-(t_values[i] * lam[k]), &e);
            if (st != SRMECH_OK) {
                return st;
            }
            acc += e;
        }
        out_theta[i] = acc;
    }
    return SRMECH_OK;
}

/* Eigenvalues of L into `lam` (ascending) via the EXISTING kernels: the
 * real path copies L into the arena for the in-place real Jacobi
 * (srmech_jacobi_eigvals mutates its matrix) and sorts; the complex path
 * runs the caller-workspace Hermitian Jacobi (already ascending). */
static srmech_status_t heat_eigvals(uint32_t n, int is_complex,
                                    const double *L, double *lam,
                                    double *ws, size_t ws_cap, size_t *off)
{
    assert(L != NULL);
    assert(lam != NULL);
    size_t nn = (size_t)n * (size_t)n;
    if (is_complex != 0) {
        double *Vc = heat_bump(ws, ws_cap, off, nn * 2u);
        double *eig_ws = heat_bump(ws, ws_cap, off, nn * 2u);
        if (Vc == NULL || eig_ws == NULL) {
            return SRMECH_ERR_OVERFLOW;
        }
        return srmech_hermitian_eigendecompose_ws(n, L, lam, Vc,
                                                  eig_ws, nn * 2u);
    }
    double *work = heat_bump(ws, ws_cap, off, nn);
    if (work == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    for (size_t e = 0; e < nn; e++) {
        work[e] = L[e];
    }
    srmech_status_t st = srmech_jacobi_eigvals(n, work, 0u,
                                               SRMECH_HEAT_JACOBI_TOL, lam);
    if (st != SRMECH_OK) {
        return st;
    }
    heat_sort_ascending(n, lam);
    return SRMECH_OK;
}

size_t srmech_heat_trace_arena_bytes(uint32_t n, int is_complex)
{
    /* Carved doubles — real: eigvals (n) + the in-place Jacobi work copy
     * (nn); complex: eigvals (n) + eigvecs staging (2nn) + eig workspace
     * (2nn). Returned in BYTES. n is an eigensolve dim, far below
     * sqrt(SIZE_MAX). */
    size_t nn = (size_t)n * (size_t)n;
    assert(n == 0u || nn / (size_t)n == (size_t)n);   /* n*n no overflow  */
    assert(nn <= SIZE_MAX / (5u * sizeof(double)));   /* 4nn+n no overflow */
    size_t doubles = (is_complex != 0) ? (nn * 4u + (size_t)n)
                                       : (nn + (size_t)n);
    return doubles * sizeof(double);
}

srmech_status_t srmech_heat_trace(
    uint32_t       n,
    int            is_complex,
    const double  *L,
    uint32_t       n_t,
    const double  *t_values,
    double        *out_theta,
    double        *ws,
    size_t         ws_len)
{
    assert(n == 0 || n_t == 0 || L != NULL);
    assert(n_t == 0 || out_theta != NULL);
    if (n_t == 0) {
        return SRMECH_OK;                    /* nothing asked, nothing written */
    }
    if (t_values == NULL || out_theta == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n == 0) {
        for (uint32_t i = 0; i < n_t; i++) {
            out_theta[i] = 0.0;              /* the empty spectrum: Θ(t) = 0 */
        }
        return SRMECH_OK;
    }
    if (L == NULL || ws == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    size_t cap = ws_len / sizeof(double);
    size_t off = 0;
    double *lam = heat_bump(ws, cap, &off, (size_t)n);
    if (lam == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    srmech_status_t st = heat_eigvals(n, is_complex, L, lam, ws, cap, &off);
    if (st != SRMECH_OK) {
        return st;
    }
    return heat_emit_theta(n, lam, n_t, t_values, out_theta);
}

/* Inner driver for the flux sweep — arena already carved. For each flux Φ:
 * scale the per-edge charge pattern (charge[k] = Φ·pattern[k]; a NULL
 * pattern is the uniform 1/n_edges default, so a single cycle's total
 * holonomy is Φ turns — the F1007 convention), build the magnetic
 * Laplacian via the rc105 chiral kernel, run the ONE eigensolve, and read
 * λ_min = the ascending spectrum's head (the flux shadow). */
static srmech_status_t gsfr_run(
    uint32_t n, uint32_t n_edges,
    const uint32_t *eu, const uint32_t *ev, const double *w,
    const double *pattern, uint32_t n_flux, const double *fluxes,
    double *out_lambda_min,
    double *H_il, double *Vc, double *eig_ws, double *lam, double *cbuf)
{
    assert(H_il != NULL);
    assert(lam != NULL);
    size_t nn = (size_t)n * (size_t)n;
    double unif = (n_edges > 0) ? (1.0 / (double)n_edges) : 0.0;
    for (uint32_t i = 0; i < n_flux; i++) {
        for (uint32_t k = 0; k < n_edges; k++) {
            double p = (pattern != NULL) ? pattern[k] : unif;
            cbuf[k] = fluxes[i] * p;
        }
        srmech_status_t st = srmech_graph_magnetic_laplacian(
            n, n_edges, eu, ev, w, 0.0, cbuf, H_il);
        if (st != SRMECH_OK) {
            return st;
        }
        st = srmech_hermitian_eigendecompose_ws(n, H_il, lam, Vc,
                                                eig_ws, nn * 2u);
        if (st != SRMECH_OK) {
            return st;
        }
        out_lambda_min[i] = lam[0];
    }
    return SRMECH_OK;
}

size_t srmech_ground_state_flux_response_arena_bytes(uint32_t n,
                                                     uint32_t n_edges)
{
    /* Carved doubles: H_il interleaved (2nn) + eigvecs staging (2nn) +
     * eig workspace (2nn) + eigvals (n) + the scaled per-edge charge
     * buffer (n_edges). Returned in BYTES. */
    size_t nn = (size_t)n * (size_t)n;
    assert(n == 0u || nn / (size_t)n == (size_t)n);   /* n*n no overflow  */
    assert(nn <= SIZE_MAX / (8u * sizeof(double)));   /* 6nn+… no overflow */
    size_t doubles = nn * 6u + (size_t)n + (size_t)n_edges;
    return doubles * sizeof(double);
}

srmech_status_t srmech_ground_state_flux_response(
    uint32_t        n,
    uint32_t        n_edges,
    const uint32_t *edges_u,
    const uint32_t *edges_v,
    const double   *weights,
    const double   *charge_pattern,
    uint32_t        n_flux,
    const double   *fluxes,
    double         *out_lambda_min,
    double         *ws,
    size_t          ws_len)
{
    assert(n_flux == 0 || fluxes != NULL);
    assert(n_flux == 0 || out_lambda_min != NULL);
    if (n < 1u) {
        return SRMECH_ERR_BAD_INPUT;   /* an empty graph has no ground state */
    }
    if (n_flux == 0) {
        return SRMECH_OK;              /* nothing asked, nothing written */
    }
    if (fluxes == NULL || out_lambda_min == NULL || ws == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n_edges > 0 && (edges_u == NULL || edges_v == NULL)) {
        return SRMECH_ERR_NULL_ARG;
    }
    size_t cap = ws_len / sizeof(double);
    size_t off = 0;
    size_t nn = (size_t)n * (size_t)n;
    double *H_il = heat_bump(ws, cap, &off, nn * 2u);
    double *Vc = heat_bump(ws, cap, &off, nn * 2u);
    double *eig_ws = heat_bump(ws, cap, &off, nn * 2u);
    double *lam = heat_bump(ws, cap, &off, (size_t)n);
    double *cbuf = heat_bump(ws, cap, &off, (size_t)n_edges);
    if (H_il == NULL || Vc == NULL || eig_ws == NULL || lam == NULL
        || cbuf == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    return gsfr_run(n, n_edges, edges_u, edges_v, weights, charge_pattern,
                    n_flux, fluxes, out_lambda_min, H_il, Vc, eig_ws, lam,
                    cbuf);
}
