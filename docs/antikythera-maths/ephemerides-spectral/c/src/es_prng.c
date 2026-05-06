/* es_prng.c — splitmix64 deterministic PRNG.
 *
 * Mirrors python/ephemerides_spectral/_research/portable_prng.py
 * byte-for-byte. The Tier 2 parity programme uses this PRNG to seed
 * channel-basis hypervectors so Python + C produce bit-identical
 * basis bytes.
 *
 * The function is a textbook splitmix64. It is deliberately simple
 * (no 128-bit arithmetic, no extended state) because the cross-
 * language byte-parity contract requires implementations to match
 * trivially. Splitmix64 isn't cryptographic, but it has no observable
 * statistical bias for our use case (channel-basis phase seeding).
 */

#include "es_prng.h"

#include <assert.h>
#include <math.h>

#define ES_PRNG_INC  ((uint64_t)0x9E3779B97F4A7C15ULL)
#define ES_PRNG_M1   ((uint64_t)0xBF58476D1CE4E5B9ULL)
#define ES_PRNG_M2   ((uint64_t)0x94D049BB133111EBULL)

uint64_t es_splitmix64_next(uint64_t *state)
{
    assert(state != NULL);
    uint64_t s = *state + ES_PRNG_INC;
    *state = s;
    uint64_t z = s;
    z = (z ^ (z >> 30)) * ES_PRNG_M1;
    z = (z ^ (z >> 27)) * ES_PRNG_M2;
    z = z ^ (z >> 31);
    assert(*state == s);  /* state advanced exactly once */
    return z;
}

double es_splitmix64_uniform_2pi(uint64_t u)
{
    /* Take the high 53 bits and scale to [0, 2π). Identical
     * conversion to the Python side: `(u >> 11) * (2π / 2**53)`.
     * 2π / 2**53 ≈ 6.97...e-16; pre-computed at compile time.
     */
    static const double SCALE_2PI = 6.283185307179586 / 9007199254740992.0;
    const double r = (double)(u >> 11) * SCALE_2PI;
    assert(r >= 0.0);
    assert(r < 6.283185307179587);  /* < 2π (loose upper, accounts for round-up) */
    return r;
}
