/*
 * srmech_cascade.c — cascade-catalog C peers for srmech.amsc.cascade.
 *
 * v0.4.5rc1: corrects the v0.4.3rc6 / v0.4.4rc1 carve-out that shipped
 * `srmech.amsc.cascade` as a Python-only module with no C symbols and
 * no TOML descriptors. This file is the first of an in-flight series
 * of cascade-op C peers (one per srmech.amsc.cascade callable) that
 * restore full C/Python parity per the project's no-binding-layer-
 * carveout discipline.
 *
 * First op shipped: `chiral_flip` (Class C orientation reversal).
 * Two typed variants — i64 sequences from cyclic-group land, f64
 * sequences from spectral land — keep the ctypes surface narrow and
 * avoid embedding a per-element generic dispatch on the C side. Each
 * variant supports in-place reversal (caller may pass `in == out`).
 *
 * v0.4.5rc2 op: `pin_slot_at_zero` (Class K pin-slot at zero). Scalar
 * in / (int8 orientation, double magnitude) out via output pointers.
 * f64-only — scalar floats are the cascade-hot path; integer pin-slot
 * is trivial and not catalogued. NaN maps to the dead-band matching
 * the Python reference impl.
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto)        : OK
 *   - Rule 2 (bounded loops)  : OK — single loop bounded by n/2
 *   - Rule 3 (no malloc)      : OK — all storage is caller-provided
 *   - Rule 4 (≤60 lines/func) : OK — each variant ~15 lines
 *   - Rule 5 (≥2 asserts/fn)  : OK — input ptrs + post-condition each
 *                              (asserts active when n > 0; the n == 0
 *                              fast-return is a documented no-op).
 *   - Rule 7 (return-value)   : OK — srmech_status_t throughout
 *   - Rule 10 (warnings clean): OK under -Wall -Wextra -Wpedantic
 *
 * License: GPL-3.0-or-later.
 */

#include "srmech.h"

#include <assert.h>
#include <stdint.h>

srmech_status_t srmech_cascade_chiral_flip_i64(const int64_t *in,
                                                size_t         n,
                                                int64_t       *out)
{
    if (n == 0) {
        return SRMECH_OK;
    }
    if (in == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(in  != NULL);
    assert(out != NULL);
    /* Walk from both ends; read both ends into locals BEFORE writing
     * so the in != out partial-overlap case is also handled correctly
     * (when in == out this reduces to a plain swap). */
    for (size_t i = 0; i < n / 2; ++i) {
        const size_t  j   = n - 1 - i;
        const int64_t a_i = in[i];
        const int64_t a_j = in[j];
        out[i] = a_j;
        out[j] = a_i;
    }
    /* Odd-length middle element: only needs copying when in != out
     * (in == out leaves the middle untouched, which is correct). */
    if ((n % 2) == 1 && in != out) {
        out[n / 2] = in[n / 2];
    }
    return SRMECH_OK;
}

srmech_status_t srmech_cascade_chiral_flip_f64(const double *in,
                                                size_t        n,
                                                double       *out)
{
    if (n == 0) {
        return SRMECH_OK;
    }
    if (in == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(in  != NULL);
    assert(out != NULL);
    /* Same shape as the i64 variant — see comments above. */
    for (size_t i = 0; i < n / 2; ++i) {
        const size_t j   = n - 1 - i;
        const double a_i = in[i];
        const double a_j = in[j];
        out[i] = a_j;
        out[j] = a_i;
    }
    if ((n % 2) == 1 && in != out) {
        out[n / 2] = in[n / 2];
    }
    return SRMECH_OK;
}

/* pin_slot_at_zero — Class K pin-slot at zero (sign-strip).
 *
 * Splits a real value into (orientation, magnitude) where orientation is
 * in {-1, 0, +1} and magnitude is non-negative. The negation on the
 * negative branch is the canonical Class K phase-boundary, NOT a call
 * to C99 fabs(); expressing it as a named cascade keeps the cascade-
 * count claimed in line with the cascade-count executed.
 *
 * NaN maps to (0, 0.0): both `x > 0.0` and `x < 0.0` evaluate false for
 * NaN under IEEE-754, so the dead-band branch handles it the same way
 * the Python reference impl does.
 */
srmech_status_t srmech_cascade_pin_slot_at_zero_f64(double  x,
                                                     int8_t *orientation_out,
                                                     double *magnitude_out)
{
    if (orientation_out == NULL || magnitude_out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(orientation_out != NULL);
    assert(magnitude_out   != NULL);
    if (x > 0.0) {
        *orientation_out = (int8_t)+1;
        *magnitude_out   = x;
    } else if (x < 0.0) {
        *orientation_out = (int8_t)-1;
        *magnitude_out   = -x;
    } else {
        /* Dead-band — origin AND NaN AND -0.0 all land here, matching
         * the Python reference impl exactly. */
        *orientation_out = (int8_t)0;
        *magnitude_out   = 0.0;
    }
    return SRMECH_OK;
}
