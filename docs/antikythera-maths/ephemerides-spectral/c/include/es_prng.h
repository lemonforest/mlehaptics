/* es_prng.h — splitmix64 deterministic PRNG (internal header).
 *
 * Used by es_channel_bases.c (and any future code that needs a
 * portable bit-identical PRNG matching the Python side). NOT part of
 * the public ABI — callers should use the higher-level
 * es_channel_basis() / es_encode_state_hd() / etc. surface that
 * wraps this PRNG.
 *
 * Mirrors python/ephemerides_spectral/_research/portable_prng.py.
 */

#ifndef ES_PRNG_H
#define ES_PRNG_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Advance `*state` by one step; return the next splitmix64 output.
 * Mirrors python `splitmix64_next(state) -> (next_state, output)`.
 */
uint64_t es_splitmix64_next(uint64_t *state);

/* Convert a splitmix64 uint64 output to a uniform double in [0, 2π).
 * `(u >> 11) * (2π / 2**53)` — identical to the Python side.
 */
double es_splitmix64_uniform_2pi(uint64_t u);

#ifdef __cplusplus
}
#endif

#endif /* ES_PRNG_H */
