/*
 * srmech_autocorr.c — C parity for the Class-L autocorrelation primitive
 * (MS#21 v0.7.0rc8; the F290 §C un-flatten Wiener-Khinchin op).
 *
 * Closes the last C/Python parity gap blocking the F290 §C "un-flatten
 * catalog" composite (autocorr -> difference-graph -> conservation-validate):
 * srmech had no native autocorrelation primitive, so the un-flatten op could
 * not be a pure-TOML composite over named ops. This adds it.
 *
 * THE OP. The circular autocorrelation
 *
 *     r[k] = Σ_i x[i] · x[(i + k) mod n],   k = 0 .. n-1
 *
 * with r[0] = Σ x² = the signal energy. This is EXACTLY the Wiener-Khinchin
 * spectral object r = Re(IFFT(|FFT(x)|²)) (the circular-convolution theorem)
 * — that identity is WHY autocorrelation is Class L (the spectral side:
 * autocorrelation ↔ power spectrum). The Python wrapper computes it the fast
 * way (numpy FFT); this C peer computes the DIRECT O(n²) multiply-add sum,
 * which is the identical object and is JPL-clean: no FFT, hence no recursion
 * (Rule 1) and no transcendentals — just bounded loops over caller buffers.
 *
 * HONEST CASCADE SHAPE. Class L (the spectral / Wiener-Khinchin reading);
 * computationally a Σ-reduce of products (no abs(), no sign branch). NOT a
 * new privileged primitive class.
 *
 * THREAD/STATE. Pure function over caller buffers; `out` MUST NOT alias `x`.
 * No shared static state; reentrant.
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto / recursion): early return; flat nested loops.
 *   - Rule 2 (bounded loops)       : both loops bounded by n.
 *   - Rule 3 (no malloc)           : caller buffers only.
 *   - Rule 4 (<=60 lines/func)     : single ~13-line function.
 *   - Rule 5 (>=2 asserts/fn)      : null + aliasing pre-conditions.
 *   - Rule 7 (return-value)        : srmech_status_t.
 *   - Rule 10 (warnings clean)     : -Wall -Wextra -Wpedantic -Werror / /WX.
 *
 * ABI: new symbol only — SRMECH_ABI_VERSION stays 3 (additive).
 *
 * License: GPL-3.0-or-later.
 */

#include "srmech.h"

#include <assert.h>
#include <stddef.h>

srmech_status_t srmech_autocorrelation_f64(
    const double *x, size_t n, double *out)
{
    if (n > 0 && (x == NULL || out == NULL)) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(n == 0 || (x != NULL && out != NULL));
    assert(n == 0 || x != out);  /* out must not alias x */
    for (size_t k = 0; k < n; ++k) {
        double acc = 0.0;
        for (size_t i = 0; i < n; ++i) {
            acc += x[i] * x[(i + k) % n];
        }
        out[k] = acc;
    }
    return SRMECH_OK;
}
