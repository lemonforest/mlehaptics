/*
 * srmech_walsh.c — the exact Walsh–Hadamard transform on (ℤ/2)ⁿ (Class L ∘ I).
 *
 * v0.9.0rc437 (local task T1142). The native twin of
 * srmech.cascade.walsh_hadamard.walsh_hadamard_transform.
 *
 * WHY THIS IS A DIFFERENT OBJECT FROM srmech_exact_dft_i64, and not a special
 * case of it: that kernel transforms over the CYCLIC group ℤ/N, whose characters
 * are Nth roots of unity, so its exact answer lives in the cyclotomic ring
 * ℤ[ζ_N] and each output coefficient is a length-φ(N) integer VECTOR. This
 * kernel transforms over the BOOLEAN CUBE (ℤ/2)ⁿ of order N = 2ⁿ. Every
 * character of that group takes values in {+1, −1} ONLY:
 *
 *     χ_k(j) = (−1)^{popcount(j & k)},     j, k ∈ [0, 2ⁿ)
 *
 * so the transform needs no roots of unity, no cyclotomic field and no ring
 * extension at all. Each output is a single integer:
 *
 *     X[k] = Σ_j x[j] · (−1)^{popcount(j & k)}
 *
 * The sign is a Class-K pin-slot flip realised as a SUBTRACTION, never as
 * abs/fabs and never as a multiply by a stored ±1 table.
 *
 * THE BUTTERFLY, AND WHY THE DENSE FORM IS NOT SHIPPED. The character table
 * factors as H_{2ⁿ} = H_2 ⊗ H_2 ⊗ … ⊗ H_2, so the transform is n = log2(N)
 * passes of pairwise (a+b, a−b) over a stride that doubles each pass:
 * N·log2(N) add/subtracts and ZERO multiplies. Materialising the N×N sign
 * matrix instead would cost N² storage to carry an operator with only N·log2(N)
 * degrees of freedom — the container-declares-more-DoF-than-the-object defect.
 * The kernel is in-place on the caller's buffer: no scratch, no arena, no
 * malloc (JPL Rule 3 is satisfied structurally rather than by a ws parameter).
 *
 * INVOLUTION. H·H = N·I exactly, so the inverse transform is this same kernel
 * followed by an exact division by N. The division is NOT performed here: it is
 * exact in ℤ only when N divides every coefficient, and swallowing that
 * condition inside an integer kernel would silently truncate. The caller owns
 * the scale (the Python wrapper documents the same contract, and the exact_dft
 * family already puts its 1/N at lift time for the identical reason).
 *
 * Public API:
 *   - srmech_walsh_hadamard_i64 (in-place, natural/Sylvester order)
 *
 * Conventions:
 *   - `data` is a caller-allocated length-N int64 array, transformed IN PLACE.
 *   - N must be a power of two ≥ 1 (else SRMECH_ERR_BAD_INPUT). N == 1 is the
 *     identity (the trivial group; zero passes) and is accepted, not refused —
 *     a NON-power-of-two is the error, matching exact_dft's refusal style
 *     rather than silently zero-padding to the next power of two.
 *   - There is NO compiled-in N size cap: the kernel writes only into the
 *     caller's own buffer, so the bound is the caller's RAM (standalone-
 *     complete honor, same argument as srmech_exact_dft_i64).
 *   - The int64 element domain is the genuine limit and it is a REAL one here:
 *     one pass can double a coefficient, so N·max|x| must stay int64-safe. The
 *     Python wrapper enforces that bound and routes larger magnitudes to its
 *     arbitrary-precision path, exactly as the exact-DFT wrapper does.
 *
 * NON-CLAIM. The index law of this transform is XOR (χ_k·χ_l = χ_{k⊕l}), and
 * that fact is NOT offered here as evidence of correctness. A census run in
 * this project measured 200/200 random sign tables on the XOR lane passing
 * every structural predicate while 0/200 were associative — "the index law is
 * XOR" is a valid REFUTER and an invalid CERTIFIER. Correctness rests on the
 * character values being ±1 and is verified by round-trip (H·H == N·I) and by
 * differential test against the dense character sum, both on the Python side.
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto)        : OK
 *   - Rule 2 (bounded loops)  : OK — every loop bounded by N
 *   - Rule 3 (no malloc)      : OK — in-place on the caller buffer, no scratch
 *   - Rule 4 (≤60 lines/func) : OK
 *   - Rule 5 (≥2 asserts/fn)  : OK
 *   - Rule 7 (return-value)   : OK — srmech_status_t throughout
 *   - Rule 8 (no multi-line macros) : OK — none
 *   - Rule 10 (warnings clean): OK under -Wall -Wextra -Wpedantic / /W4
 *
 * ABI: additive — srmech_walsh_hadamard_i64 is a NEW exported symbol and no
 * existing signature or status contract moves, so SRMECH_ABI_VERSION stays 14
 * (the Python ctypes shim hasattr-guards it; a stale lib simply runs the pure
 * path, which is the COMPLETE alternative implementation, not a rescue).
 *
 * SSoT: Walsh, "A closed set of normal orthogonal functions", Amer. J. Math.
 * 45 (1923) 5–24; Fino & Algazi, "Unified matrix treatment of the fast
 * Walsh-Hadamard transform", IEEE Trans. Computers C-25 (1976) 1142–1146.
 *
 * License: MIT.
 */

#include "srmech.h"

#include <assert.h>
#include <stddef.h>
#include <stdint.h>

/* One butterfly pass at half-block width `half`: for every pair (a, b) that is
 * `half` apart inside a block of width 2·half, write back (a+b, a−b). The
 * subtraction IS the Class-K sign-flip — the −1 character value is never stored
 * and never multiplied by. */
static void walsh_pass(int64_t *data, uint32_t n, uint32_t half)
{
    assert(data != NULL);
    assert(half > 0u);
    uint32_t width = half * 2u;
    for (uint32_t base = 0; base < n; base += width) {
        for (uint32_t j = base; j < base + half; j++) {
            int64_t a = data[j];
            int64_t b = data[j + half];
            data[j] = a + b;
            data[j + half] = a - b;
        }
    }
}

srmech_status_t srmech_walsh_hadamard_i64(uint32_t n, int64_t *data)
{
    assert(data != NULL);
    assert(n != 0u);
    if (data == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n == 0u || (n & (n - 1u)) != 0u) {
        return SRMECH_ERR_BAD_INPUT;    /* need a power of two >= 1 */
    }
    /* n == 1 is the trivial group: zero passes, data unchanged, SRMECH_OK. */
    for (uint32_t half = 1u; half < n; half *= 2u) {
        walsh_pass(data, n, half);
    }
    return SRMECH_OK;
}
