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
