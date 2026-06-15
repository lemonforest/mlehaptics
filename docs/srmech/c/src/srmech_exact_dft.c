/*
 * srmech_exact_dft.c — exact cyclotomic-integer DFT (Class I ∘ K ∘ M).
 *
 * v0.7.5rc29 ([#928](https://github.com/lemonforest/mlehaptics/issues/928)).
 * The native twin of srmech.amsc.cascade.exact_dft. A DFT's twiddle factors
 * e^{-2πi·j/N} are roots of unity = algebraic integers in the cyclotomic ring
 * ℤ[ζ_N]. For a power-of-two N the cyclotomic polynomial is Φ_N(x)=x^{N/2}+1,
 * so ζ^{N/2} = -1 (a Class-K pin-slot sign-flip, never abs/fabs) and the ring
 * collapses to the negacyclic integers ℤ[x]/(x^{N/2}+1) — a length-N/2 integer
 * vector. The DFT of an integer (Gaussian-integer) signal is then PURE INTEGER
 * add/subtract: bit-for-bit deterministic, no floating point at all. The single
 * FPU lift ζ → e^{-2πi/N} happens on the Python side (this surface is the exact
 * integer substrate; floats are for the lift, per
 * [[user_stance_epicycle_via_gear_plus_pin]]).
 *
 *   X[k] = Σ_n signal[n] · ζ^{±nk mod N},  ζ^{N/2} = -1.
 *
 * Public API:
 *   - srmech_exact_dft_i64 (forward/inverse; int64 signal → int64 spectrum)
 *
 * Conventions:
 *   - re/im are length-N int64 component arrays (caller-allocated). The output
 *     out_re/out_im are length N·(N/2) int64 (k-major: row k is the N/2
 *     cyclotomic coefficients of X[k] at [k·(N/2), (k+1)·(N/2))).
 *   - inverse != 0 uses ζ^{-nk} (the Python lift applies the 1/N scale).
 *   - N must be a power of two ≥ 2 (general-N cyclotomic reduction is a Python
 *     bignum follow-up). There is NO compiled-in N size cap: the kernel writes
 *     straight into the caller's out_re/out_im (length N·(N/2)), so the bound is
 *     the caller's own buffers, not a hardcoded limit (standalone-complete honor).
 *   - The int64 element domain is a genuine fixed-width-integer bound, not a size
 *     cap: the caller must keep N·max|signal| int64-safe (the Python wrapper
 *     enforces this and routes larger magnitudes to its arbitrary-precision path).
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto)        : OK
 *   - Rule 2 (bounded loops)  : OK — every loop bounded by N / (N/2)
 *   - Rule 3 (no malloc)      : OK — writes directly into caller buffers
 *   - Rule 4 (≤60 lines/func) : OK — per-row accumulate factored out
 *   - Rule 5 (≥2 asserts/fn)  : OK
 *   - Rule 7 (return-value)   : OK — srmech_status_t throughout
 *   - Rule 8 (no multi-line macros) : OK — single-line #define only
 *   - Rule 10 (warnings clean): OK under -Wall -Wextra -Wpedantic / /W4
 *
 * ABI: additive — srmech_exact_dft_i64 is a NEW exported symbol, so
 * SRMECH_ABI_VERSION stays 3 (the Python ctypes shim hasattr-guards it).
 *
 * License: GPL-3.0-or-later.
 */

#include "srmech.h"

#include <assert.h>
#include <stddef.h>
#include <stdint.h>

/* Accumulate one spectrum row X[k] into row_re/row_im (length h = N/2). Pure
 * integer add/subtract; the j ≥ h case is the ζ^{N/2} = -1 Class-K sign-flip
 * (a branch, never abs). Forward uses ζ^{nk}; inverse uses ζ^{-nk} = ζ^{(N-j)k}. */
static void exact_dft_row(uint32_t n, uint32_t h, int inverse,
                          const int64_t *re, const int64_t *im,
                          uint32_t k, int64_t *row_re, int64_t *row_im)
{
    assert(re != NULL);
    assert(row_re != NULL);
    for (uint32_t j = 0; j < h; j++) {
        row_re[j] = 0;
        row_im[j] = 0;
    }
    for (uint32_t idx = 0; idx < n; idx++) {
        uint32_t j = (uint32_t)(((uint64_t)idx * (uint64_t)k) % (uint64_t)n);
        if (inverse != 0) {
            j = (n - j) % n;            /* ζ^{-jk}: (-idx·k) mod N */
        }
        if (j >= h) {                   /* Class K: ζ^{N/2} = -1 */
            j -= h;
            row_re[j] -= re[idx];
            row_im[j] -= im[idx];
        } else {
            row_re[j] += re[idx];
            row_im[j] += im[idx];
        }
    }
}

srmech_status_t srmech_exact_dft_i64(uint32_t      n,
                                     int           inverse,
                                     const int64_t *re,
                                     const int64_t *im,
                                     int64_t       *out_re,
                                     int64_t       *out_im)
{
    assert(re != NULL);
    assert(im != NULL);
    assert(out_re != NULL);
    assert(out_im != NULL);
    if (re == NULL || im == NULL || out_re == NULL || out_im == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n < 2u || (n & (n - 1u)) != 0u) {
        return SRMECH_ERR_BAD_INPUT;        /* need power-of-two ≥ 2 */
    }
    /* No N size cap: out_re/out_im are caller-sized (length N·N/2), so the
     * bound is the caller's RAM, not a compiled limit. The int64 element
     * magnitude is the caller's documented contract (see file header). */
    uint32_t h = n / 2u;
    for (uint32_t k = 0; k < n; k++) {
        exact_dft_row(n, h, inverse, re, im, k,
                      &out_re[(size_t)k * h], &out_im[(size_t)k * h]);
    }
    return SRMECH_OK;
}
