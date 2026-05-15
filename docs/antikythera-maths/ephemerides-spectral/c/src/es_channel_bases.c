/* es_channel_bases.c — channel-basis construction (Tier 2a).
 *
 * Mirrors python/ephemerides_spectral/_research/portable_prng.py +
 * the `_initialize_bases` step in
 * python/ephemerides_spectral/_research/ephemeris_reference_instrument.py
 *
 * Two construction routes are exposed (v0.29.0rc1, ABI v10):
 *
 *   ES_BASIS_METHOD_LEGACY (default, byte-parity with Python):
 *     state = seed
 *     for k in range(D):
 *         state, u = splitmix64_next(state)
 *         phi      = (u >> 11) * (2π / 2**53)    in [0, 2π)
 *         out[k]   = (cosf(phi), sinf(phi))      complex64
 *
 *   ES_BASIS_METHOD_TURN_INTEGER (v0.29.0rc1 spike, bench-and-quantify):
 *     state = seed
 *     for k in range(D):
 *         state, u = splitmix64_next(state)
 *         phase    = (uint32_t)(u >> 32)         in Z_{2^32}   turns
 *         quadrant = phase >> 30                 in {0, 1, 2, 3}
 *         within   = phase & 0x3FFFFFFF          in [0, 2^30)
 *         if within == 0:
 *             out[k] = quarter-turn dispatch      (±1, 0) / (0, ±1)
 *         else:
 *             a   = (double)within * (π/2 / 2^30)  in [0, π/2)
 *             c,s = cos(a), sin(a)
 *             out[k] = i^quadrant · (c, s)        sign/swap, no math
 *
 * The TURN_INTEGER route honours the project's algebraic stance: the
 * phase residue IS the cyclic-group element in Z_{2^32}, and quarter
 * turns are bit patterns (low 30 bits zero). The native cyclic-group
 * structure handles the structural decomposition; libm cos/sin only
 * touches the within-quadrant fraction on a small argument range
 * [0, π/2). No cospi/sinpi libm dependency; no π in the global
 * argument; quarter-turn channels collapse to bit-exact (±1, 0) /
 * (0, ±1) on every toolchain.
 *
 * The public `es_channel_basis()` entry is preserved as-is: it
 * delegates to the LEGACY route so the Python-vs-C byte-parity test
 * (test_channel_basis_parity.py) continues to hold without changing
 * any caller.
 */

#include "ephemerides_spectral.h"
#include "es_prng.h"

#include <assert.h>
#include <math.h>
#include <stddef.h>
#include <stdint.h>

/* ------------------------------------------------------------------ *
 * LEGACY route — shipped path, byte-parity with Python
 * ------------------------------------------------------------------ */

static es_status_t es_channel_basis_legacy(uint64_t seed,
                                           es_complex64_t *out,
                                           size_t D)
{
    assert(out != NULL);
    assert(D == 0 || out != NULL);  /* pin: out is valid for D > 0 */
    uint64_t state = seed;
    for (size_t k = 0; k < D; ++k) {
        const uint64_t u = es_splitmix64_next(&state);
        const double phi = es_splitmix64_uniform_2pi(u);
        assert(phi >= 0.0 && phi < 6.283185307179587);
        /* cos/sin in double precision; cast to float for storage.
         * Deterministic float-truncation is the only place the C and
         * Python sides could disagree at the bit level — verified by
         * the parity test that compares float32 cast of Python's
         * complex128 output against C's complex64.
         */
        out[k].real = (float)cos(phi);
        out[k].imag = (float)sin(phi);
    }
    return ES_OK;
}

/* ------------------------------------------------------------------ *
 * TURN_INTEGER route — v0.29.0rc1 spike (cyclic-group-native)
 * ------------------------------------------------------------------ */

static es_status_t es_channel_basis_turn_integer_route(uint64_t seed,
                                                       es_complex64_t *out,
                                                       size_t D)
{
    /* Constant: scale a 30-bit within-quadrant fraction to radians in
     * [0, π/2). The × (π/2 / 2^30) multiply has ≤1 ULP rounding at
     * double precision (the constant is irrational); the float32 cast
     * at storage discards bits well below that — pure ceremony at this
     * precision target. See research notebook §4 v0.29.0rc1 entry.
     */
    static const double PI_HALF_PER_2P30 = 1.5707963267948966 / (double)(1u << 30);
    assert(out != NULL);
    assert(D == 0 || out != NULL);
    uint64_t state = seed;
    for (size_t k = 0; k < D; ++k) {
        const uint64_t u = es_splitmix64_next(&state);
        const uint32_t phase = (uint32_t)(u >> 32);
        const uint32_t quadrant = phase >> 30;
        const uint32_t within = phase & 0x3FFFFFFFu;
        assert(quadrant < 4u);
        float re;
        float im;
        if (within == 0u) {
            /* Bit-exact quarter turn — no float arithmetic at all. */
            switch (quadrant) {
                case 0u:  re =  1.0f; im =  0.0f; break;
                case 1u:  re =  0.0f; im =  1.0f; break;
                case 2u:  re = -1.0f; im =  0.0f; break;
                default:  re =  0.0f; im = -1.0f; break;
            }
        } else {
            const double a = (double)within * PI_HALF_PER_2P30;
            assert(a >= 0.0 && a < 1.5707963267948966);
            const double c = cos(a);
            const double s = sin(a);
            /* Quadrant rotation = multiply by i^quadrant. Sign/swap
             * only — no float math, no rounding loss.
             */
            switch (quadrant) {
                case 0u:  re =  (float)c; im =  (float)s; break;
                case 1u:  re = -(float)s; im =  (float)c; break;
                case 2u:  re = -(float)c; im = -(float)s; break;
                default:  re =  (float)s; im = -(float)c; break;
            }
        }
        out[k].real = re;
        out[k].imag = im;
    }
    return ES_OK;
}

/* ------------------------------------------------------------------ *
 * Public entry points
 * ------------------------------------------------------------------ */

es_status_t es_channel_basis(uint64_t seed,
                             es_complex64_t *out,
                             size_t D)
{
    if (out == NULL) {
        return ES_ERR_NULL_OUTPUT;
    }
    assert(out != NULL);
    return es_channel_basis_legacy(seed, out, D);
}

es_status_t es_channel_basis_method(uint64_t seed,
                                    es_complex64_t *out,
                                    size_t D,
                                    es_basis_method_t method)
{
    if (out == NULL) {
        return ES_ERR_NULL_OUTPUT;
    }
    assert(out != NULL);
    switch (method) {
        case ES_BASIS_METHOD_LEGACY:
            return es_channel_basis_legacy(seed, out, D);
        case ES_BASIS_METHOD_TURN_INTEGER:
            return es_channel_basis_turn_integer_route(seed, out, D);
        default:
            return ES_ERR_INVALID_KIND;
    }
}
