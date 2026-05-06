/* es_channel_bases.c — channel-basis construction (Tier 2a).
 *
 * Mirrors python/ephemerides_spectral/_research/portable_prng.py +
 * the `_initialize_bases` step in
 * python/ephemerides_spectral/_research/ephemeris_reference_instrument.py
 *
 * The basis for one channel is a deterministic random unit-magnitude
 * complex hypervector of dimension D. Generating it on the C side
 * lets `bridge.get_local_view` and `bridge.get_eclipse_probability`
 * have a `backend="c"` path in Tier 2b.
 *
 * Basis construction:
 *
 *   state = seed
 *   for k in range(D):
 *       state, u = splitmix64_next(state)
 *       phi      = (u >> 11) * (2π / 2**53)         in [0, 2π)
 *       out[k]   = (cosf(phi), sinf(phi))           complex64
 *
 * The Python side uses `numpy.complex128` whereas the C side stores
 * `complex64` (real + imag as `float`). Bit-parity is verified at
 * the float32 level — promote both sides to float32 if you're
 * comparing.
 */

#include "ephemerides_spectral.h"
#include "es_prng.h"

#include <assert.h>
#include <math.h>
#include <stddef.h>

es_status_t es_channel_basis(uint64_t seed,
                             es_complex64_t *out,
                             size_t D)
{
    if (out == NULL) {
        return ES_ERR_NULL_OUTPUT;
    }
    assert(out != NULL);  /* post-validation */
    uint64_t state = seed;
    for (size_t k = 0; k < D; ++k) {
        const uint64_t u = es_splitmix64_next(&state);
        const double phi = es_splitmix64_uniform_2pi(u);
        assert(phi >= 0.0 && phi < 6.283185307179587);  /* invariant per call */
        /* cos/sin in double precision; cast to float for storage.
         * The deterministic float-truncation step is the only place
         * the C and Python sides could disagree at the bit level —
         * verified by the parity test that compares float32 cast of
         * Python's complex128 output against C's complex64.
         */
        out[k].real = (float)cos(phi);
        out[k].imag = (float)sin(phi);
    }
    return ES_OK;
}
