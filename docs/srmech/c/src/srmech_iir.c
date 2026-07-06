/*
 * srmech_iir.c — C parity for the NUMERIC IIR / recursive filter primitive
 * (BATCH B4b, 0.9.0rc149; the sp_transform filter family).
 *
 * THE OP. The direct-form-I linear constant-coefficient difference equation
 *
 *     y[i] = ( Σ_{j=0}^{nb-1} b[j]·x[i-j]  −  Σ_{k=1}^{na-1} a[k]·y[i-k] ) / a[0]
 *
 * (x[i-j] / y[i-k] taken as 0 for a negative index — zero initial rest). This
 * is the recursive IIR filter y = lfilter(b, a, x): the feed-forward numerator
 * b(z) convolved with the input, minus the feed-back denominator a(z) convolved
 * with the already-computed output. An FIR filter is the a = [1] special case;
 * an all-pass section is the mirrored-coefficient (b, a) pair. This SINGLE
 * kernel therefore backs both `closed_form_ops.iir` and `closed_form_ops.allpass`
 * (a biquad cascade is this kernel applied per second-order section in Python).
 *
 * WHY A NEW C SYMBOL (not a composition). The feedback term reads y[i-k] — the
 * output the loop is still producing — so the recursion is inherently SEQUENTIAL
 * and does NOT decompose into a single matmul / FFT the way a (feed-forward-only)
 * convolution does. There is no existing C op whose shape fits, so this is the
 * minimal genuinely-new numeric kernel the filter family needs. It composes no
 * transcendental: just bounded multiply-add loops over caller buffers.
 *
 * NUMERIC (FPU-tol), NOT byte-exact — the accumulation may FMA-fuse ~1 ULP on
 * some platforms (macOS clang), so the Python parity contract is WITHIN-TOL
 * (reldiff ≤ 1e-9), matching the F1-FFT / F2-SVD numeric-foundation contract.
 * The pure-Python direct-form-II-transposed reference (`_lfilter_direct`) /
 * direct-form-I reference (allpass) is the COMPLETE alternative for no-C hosts
 * and the parity oracle.
 *
 * HONEST CASCADE SHAPE. Class N (the b/a rational transfer function) ∘ Class C
 * (the cyclic-recursive streaming of the difference equation). No abs(), no
 * sign branch, no libm, no privileged new primitive class.
 *
 * THREAD/STATE. Pure function over caller buffers; `out` MUST NOT alias `x`
 * (the feed-forward term re-reads x[i-j] AFTER out[i] would overwrite it). No
 * shared static state; reentrant.
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto / recursion): early returns; flat nested loops.
 *   - Rule 2 (bounded loops)       : outer bound n, inner bounds nb / na.
 *   - Rule 3 (no malloc)           : caller buffers only (no state scratch —
 *                                     direct-form-I reads x[] and out[]).
 *   - Rule 4 (<=60 lines/func)     : single ~24-line function.
 *   - Rule 5 (>=2 asserts/fn)      : null + aliasing pre-conditions.
 *   - Rule 7 (return-value)        : srmech_status_t.
 *   - Rule 10 (warnings clean)     : -Wall -Wextra -Wpedantic -Werror / /WX.
 *
 * ABI: new symbol only — SRMECH_ABI_VERSION stays 3 (additive).
 *
 * License: MIT.
 */

#include "srmech.h"

#include <assert.h>
#include <stddef.h>

srmech_status_t srmech_iir_lfilter_f64(
    const double *b, size_t nb,
    const double *a, size_t na,
    const double *x, size_t n,
    double *out)
{
    if (nb == 0 || na == 0 || b == NULL || a == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n > 0 && (x == NULL || out == NULL)) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(b != NULL && a != NULL);
    assert(n == 0 || (x != NULL && out != NULL && x != out));
    const double a0 = a[0];
    if (a0 == 0.0) {
        return SRMECH_ERR_BAD_INPUT;   /* a[0] == 0 -> not a valid recursion */
    }
    for (size_t i = 0; i < n; ++i) {
        double acc = 0.0;
        for (size_t j = 0; j < nb; ++j) {
            if (i >= j) {
                acc += b[j] * x[i - j];
            }
        }
        for (size_t k = 1; k < na; ++k) {
            if (i >= k) {
                acc -= a[k] * out[i - k];
            }
        }
        out[i] = acc / a0;
    }
    return SRMECH_OK;
}
