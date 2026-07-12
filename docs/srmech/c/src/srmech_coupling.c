/*
 * srmech_coupling.c — the resonant-spectrum closure (§75 / F928).
 *
 * `srmech_resonant_spectrum` is a Class-L coupling-cascade COMPOSITE: it
 * orchestrates the EXISTING C kernels — it writes no new eigensolver,
 * matmul, or factoriser. Given a real-symmetric coupling Laplacian L it
 * reads L as a stored (excitation-free) object:
 *
 *   tensions     = eigenvalues ASCENDING (the stored "dark" tension
 *                  spectrum; the MFO field, no excitation)        [Class L]
 *   modes        = eigenvectors, columns (the excitation modes)   [Class L]
 *   force_orders = [L, L^2, ..., L^orders] via L^k = V·diag(Λ^k)·Vᵀ
 *                  reconstructed from the ONE eigensolve           [Class L]
 *   resonances   = adjacent nonzero-tension ratios read as best_rational
 *                  (num,den) + the LOCK (smooth/2-adic den) vs LIBRATION
 *                  (large-prime den) verdict from the denom's factors
 *                  [Class N best_rational + Class J factor]
 *
 * Kernels reused (no re-implementation here):
 *   - srmech_hermitian_eigendecompose_ws  (spectrum + modes; the real L is
 *       fed as interleaved-complex with imag=0, the modes come back real)
 *   - srmech_best_rational                (the Class-N ratio read)
 *   - srmech_factor                       (the Class-J denom factorisation)
 *
 * Standalone-complete honor ([[feedback_c_must_be_standalone_complete_no_
 * python_fallback]]): all scratch is bump-carved from the CALLER arena `ws`
 * (no malloc, JPL Rule 3) — the bound is the caller's RAM. Size `ws` from
 * srmech_resonant_spectrum_arena_bytes. The Python op is the COMPLETE
 * alternative implementation for no-C hosts (value-parity, not a rescue).
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto)        : OK
 *   - Rule 2 (bounded loops)  : OK — all loops bounded by n / orders / the
 *                               u64-isqrt Newton (~6 iters) / factor's u64 cap
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

/* The relative floor below which an eigenvalue is a free / bulk (zero) mode
 * — mirrors the Python _ZERO_TENSION_REL so both paths drop the same modes. */
#define SRMECH_RESONANT_ZERO_REL 1e-9

/* The float→integer scale for the best_rational ratio read — mirrors the
 * Python _RATIO_SCALE (a ratio in (0,1] resolved to 6 decimals). */
#define SRMECH_RESONANT_RATIO_SCALE 1000000u

/* The per-resonance denominator factor buffer size (u64 has ≤15 distinct
 * primes); reused for the lock test only, never returned. */
#define SRMECH_RESONANT_FACTOR_MAX 16u

/* 8-byte-aligned bump of `need` doubles out of the caller arena. Advances
 * *off; returns NULL (caller maps to OVERFLOW) if the arena is exhausted. */
static double *resonant_bump(double *ws, size_t ws_len, size_t *off, size_t need)
{
    assert(ws != NULL || ws_len == 0);
    assert(off != NULL);
    if (*off + need > ws_len) {
        return NULL;
    }
    double *p = ws + *off;
    *off += need;
    return p;
}

/* Floor integer sqrt of a u64 by Newton's cascade (no libm). Used for the
 * lock cutoff = isqrt(max_den): a denominator whose every prime ≤ this is a
 * smooth / 2-adic LOCK; a larger prime factor is a LIBRATION. */
static uint64_t resonant_isqrt(uint64_t v)
{
    assert(v <= 0xFFFFFFFFFFFFFFFFull);
    if (v < 2) {
        return v;
    }
    uint64_t x = v;
    uint64_t y = (x + 1u) / 2u;
    while (y < x) {
        x = y;
        y = (x + v / x) / 2u;
    }
    assert(x * x <= v || x == 0);
    return x;
}

/* Class-J lock test: factor `den` and return 1 iff every prime factor is
 * ≤ isqrt(max_den) (a smooth / 2-adic-ladder denominator), else 0. den==1
 * (no factors) is an exact-integer lock. */
static int resonant_den_is_locked(uint64_t den, uint64_t max_den)
{
    assert(den >= 1u);
    assert(max_den >= 1u);
    uint64_t cutoff = resonant_isqrt(max_den);
    uint64_t primes[SRMECH_RESONANT_FACTOR_MAX];
    uint8_t  exps[SRMECH_RESONANT_FACTOR_MAX];
    uint32_t count = 0;
    if (den <= 1u) {
        return 1;
    }
    srmech_status_t st = srmech_factor(den, primes, exps,
                                       SRMECH_RESONANT_FACTOR_MAX, &count);
    if (st != SRMECH_OK) {
        return 0;
    }
    for (uint32_t i = 0; i < count; i++) {
        if (primes[i] > cutoff) {
            return 0;
        }
    }
    return 1;
}

/* Reconstruct one force order L^k = V·diag(Λ^k)·Vᵀ (real) into out_Lk
 * (n*n row-major). V is the real eigenvector matrix (columns = modes), lam
 * the n ascending eigenvalues, k≥1 the order. No new matmul kernel: the
 * V·diag·Vᵀ contraction is the closed form over the ONE eigensolve. */
static void resonant_force_order(uint32_t n, const double *V,
                                 const double *lam, uint32_t k, double *out_Lk)
{
    assert(V != NULL);
    assert(out_Lk != NULL);
    for (uint32_t i = 0; i < n; i++) {
        for (uint32_t j = 0; j < n; j++) {
            double acc = 0.0;
            for (uint32_t c = 0; c < n; c++) {
                double lam_k = 1.0;
                for (uint32_t e = 0; e < k; e++) {
                    lam_k *= lam[c];
                }
                acc += V[(size_t)i * n + c] * lam_k * V[(size_t)j * n + c];
            }
            out_Lk[(size_t)i * n + j] = acc;
        }
    }
}

/* Pin each real eigenvector column's sign (Class K): flip column j so its
 * largest-|·| entry (selected via v*v, no abs/sqrt) is positive. Mirrors the
 * Python _canonicalize_eigenvector_signs so `modes` matches value-for-value.
 * V is n*n row-major real (columns = eigenvectors), edited in place. */
static void resonant_canon_signs(uint32_t n, double *V)
{
    assert(V != NULL);
    assert(n >= 1u || n == 0u);
    for (uint32_t j = 0; j < n; j++) {
        uint32_t krow = 0;
        double best = V[j] * V[j];
        for (uint32_t r = 1; r < n; r++) {
            double cur = V[(size_t)r * n + j] * V[(size_t)r * n + j];
            if (cur > best) {
                best = cur;
                krow = r;
            }
        }
        if (V[(size_t)krow * n + j] < 0.0) {
            for (uint32_t r = 0; r < n; r++) {
                V[(size_t)r * n + j] = -V[(size_t)r * n + j];
            }
        }
    }
}

/* Read the eigensolve outputs into the caller's modes/tensions buffers:
 * copy ascending eigenvalues to out_tensions; take the real part of each
 * interleaved-complex eigenvector into out_modes (n*n row-major), then
 * sign-canonicalise. */
static void resonant_emit_spectrum(uint32_t n, const double *eigvals,
                                   const double *eigvecs_il,
                                   double *out_tensions, double *out_modes)
{
    assert(eigvals != NULL);
    assert(out_modes != NULL);
    for (uint32_t i = 0; i < n; i++) {
        out_tensions[i] = eigvals[i];
    }
    for (uint32_t i = 0; i < n; i++) {
        for (uint32_t j = 0; j < n; j++) {
            out_modes[(size_t)i * n + j] = eigvecs_il[((size_t)i * n + j) * 2];
        }
    }
    resonant_canon_signs(n, out_modes);
}

/* Read the resonances: for each ADJACENT nonzero-tension pair (ascending),
 * best_rational of (lo/hi) ∈ (0,1] + the lock verdict. Writes pairs / ratios
 * / locked flags and *out_count. Returns a status from best_rational. */
static srmech_status_t resonant_emit_resonances(
    uint32_t n, const double *lam, uint64_t max_den,
    int32_t *out_pairs, uint64_t *out_ratio, int32_t *out_locked,
    uint32_t *out_count)
{
    assert(lam != NULL);
    assert(out_count != NULL);
    double top = (n > 0) ? lam[n - 1] : 0.0;
    double floor_v = top * SRMECH_RESONANT_ZERO_REL;
    uint32_t cnt = 0;
    int32_t prev = -1;
    for (uint32_t i = 0; i < n; i++) {
        if (lam[i] <= floor_v) {
            continue;
        }
        if (prev >= 0) {
            double lo = lam[prev];
            double hi = lam[i];
            double ratio = lo / hi;
            uint64_t num_in = (uint64_t)(ratio * SRMECH_RESONANT_RATIO_SCALE + 0.5);
            uint64_t p = 0, q = 1;
            srmech_status_t st = srmech_best_rational(
                num_in, SRMECH_RESONANT_RATIO_SCALE, max_den, &p, &q);
            if (st != SRMECH_OK) {
                return st;
            }
            out_pairs[(size_t)cnt * 2] = prev;
            out_pairs[(size_t)cnt * 2 + 1] = (int32_t)i;
            out_ratio[(size_t)cnt * 2] = p;
            out_ratio[(size_t)cnt * 2 + 1] = q;
            out_locked[cnt] = resonant_den_is_locked(q, max_den);
            cnt++;
        }
        prev = (int32_t)i;
    }
    *out_count = cnt;
    return SRMECH_OK;
}

size_t srmech_resonant_spectrum_arena_bytes(uint32_t n)
{
    /* Carved doubles: H_il interleaved input (2nn) + eig workspace (2nn) +
     * eigvecs_il staging (2nn) + the real eigenvector copy V (nn) = 7nn.
     * Returned in BYTES. n is an eigensolve dim, far below sqrt(SIZE_MAX). */
    size_t nn = (size_t)n * (size_t)n;
    assert(n == 0u || nn / (size_t)n == (size_t)n);   /* n*n no overflow */
    assert(nn <= SIZE_MAX / 7u);                      /* 7*nn no overflow */
    return nn * 7u * sizeof(double);
}

/* Inner driver: arena pointers already carved. Builds the interleaved-complex
 * H, runs the ONE eigensolve, emits spectrum + modes + every force order +
 * the resonances. Split out so the public entry stays ≤60 lines (JPL Rule 4). */
static srmech_status_t resonant_run(
    uint32_t n, const double *L_rowmajor, uint32_t orders, uint64_t max_den,
    double *out_tensions, double *out_modes, double *out_force_orders,
    int32_t *out_pairs, uint64_t *out_ratio, int32_t *out_locked,
    uint32_t *out_count, double *H_il, double *eig_ws, double *Vc, double *V)
{
    assert(H_il != NULL);
    assert(eig_ws != NULL);
    size_t nn = (size_t)n * (size_t)n;
    for (size_t e = 0; e < nn; e++) {       /* real L → interleaved (re,0). */
        H_il[e * 2] = L_rowmajor[e];
        H_il[e * 2 + 1] = 0.0;
    }
    srmech_status_t st = srmech_hermitian_eigendecompose_ws(
        n, H_il, out_tensions, Vc, eig_ws, nn * 2u);
    if (st != SRMECH_OK) {
        return st;
    }
    resonant_emit_spectrum(n, out_tensions, Vc, out_tensions, out_modes);
    for (uint32_t r = 0; r < n; r++) {      /* the real V copy (post-sign-pin). */
        for (uint32_t c = 0; c < n; c++) {
            V[(size_t)r * n + c] = out_modes[(size_t)r * n + c];
        }
    }
    for (uint32_t k = 1; k <= orders; k++) {
        resonant_force_order(n, V, out_tensions, k,
                             out_force_orders + (size_t)(k - 1) * nn);
    }
    return resonant_emit_resonances(n, out_tensions, max_den,
                                    out_pairs, out_ratio, out_locked, out_count);
}

srmech_status_t srmech_resonant_spectrum(
    uint32_t       n,
    const double  *L_rowmajor,
    uint32_t       orders,
    uint64_t       max_den,
    double        *out_tensions,
    double        *out_modes,
    double        *out_force_orders,
    int32_t       *out_res_pairs,
    uint64_t      *out_res_ratio,
    int32_t       *out_res_locked,
    uint32_t      *out_res_count,
    double        *ws,
    size_t         ws_len)
{
    assert(out_tensions != NULL || n == 0);
    assert(out_res_count != NULL || n == 0);
    if (orders < 1u || max_den < 1u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (n == 0) {
        if (out_res_count != NULL) {
            *out_res_count = 0;
        }
        return SRMECH_OK;
    }
    if (L_rowmajor == NULL || out_tensions == NULL || out_modes == NULL
        || out_force_orders == NULL || out_res_pairs == NULL
        || out_res_ratio == NULL || out_res_locked == NULL
        || out_res_count == NULL || ws == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    size_t nn = (size_t)n * (size_t)n;
    size_t cap = ws_len / sizeof(double);
    size_t off = 0;
    double *H_il = resonant_bump(ws, cap, &off, nn * 2u);
    double *eig_ws = resonant_bump(ws, cap, &off, nn * 2u);
    double *Vc = resonant_bump(ws, cap, &off, nn * 2u);
    double *V = resonant_bump(ws, cap, &off, nn);
    if (H_il == NULL || eig_ws == NULL || Vc == NULL || V == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    return resonant_run(n, L_rowmajor, orders, max_den, out_tensions,
                        out_modes, out_force_orders, out_res_pairs,
                        out_res_ratio, out_res_locked, out_res_count,
                        H_il, eig_ws, Vc, V);
}
