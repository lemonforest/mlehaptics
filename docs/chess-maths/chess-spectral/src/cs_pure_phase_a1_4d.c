/* Channel 0: pure-phase A_1 orbit projection (1.18.0+).
 *
 * Float baseline (cs_channel_a1_4d):
 *   out[s] = (1/|orbit(s)|) × sum_{t in orbit(s)} sig[t]
 *
 * Pure-phase: drop the 1/|orbit| division and absorb it into the
 * channel dequantization scale. The integer formula is:
 *   out[s] = (384 / |orbit(s)|) × sum_{t in orbit(s)} sig[t]
 *          = ORBIT_INT_SCALE[ORBIT_OF[s]] × sum sig[t]
 *
 * 384 is the LCM of all B_4 orbit sizes (each orbit size divides
 * |B_4| = 384), so ORBIT_INT_SCALE[o] = 384/|orbit_o| is an integer.
 * The 1/384 factor is reapplied via CHANNEL_DEQUANT_SCALES_4D[A1] at
 * the float boundary.
 *
 * Overflow envelope (per output cell):
 *   |out[s]| <= max ORBIT_INT_SCALE × max sum
 *             = 384 × (max_orbit_size × max_|sig|)
 *             = 384 × 384 × 48          (pathological all-K position)
 *             = 7 077 888                (well within int32)
 *
 * Realistic overflow (orbit member with all-king fill):
 *   max scale = 384 (orbit size 1)
 *   sum bounded by orbit_size × |K|_int = 1 × 48 = 48
 *   so |out[s]| <= 384 × 48 = 18 432 — comfortably int16.
 *
 * JPL discipline:
 *   - Two nested for-loops, both with fixed orbit-table bounds.
 *   - Three assertions (pointers + invariant on N_ORBITS).
 *   - int32 accumulator declared per-orbit (smallest scope).
 */
#include <assert.h>
#include "cs_encoder_pure_phase_4d.h"
#include "cs_tables_4d.h"

void cs_channel_pure_phase_a1_4d(
    const int16_t sig[CS_N_SQUARES_4D],
    int32_t out[CS_N_SQUARES_4D])
{
    assert(sig != NULL);
    assert(out != NULL);
    assert(CS_N_ORBITS_4D > 0);

    for (int o = 0; o < CS_N_ORBITS_4D; o++) {
        const uint16_t start = ORBIT_OFFSETS[o];
        const uint16_t end   = ORBIT_OFFSETS[o + 1];

        int32_t sum = 0;
        for (uint16_t i = start; i < end; i++) {
            sum += (int32_t)sig[ORBIT_MEMBERS[i]];
        }

        const int32_t scale = (int32_t)ORBIT_INT_SCALE[o];
        const int32_t scaled_sum = scale * sum;

        for (uint16_t i = start; i < end; i++) {
            out[ORBIT_MEMBERS[i]] = scaled_sum;
        }
    }
}
