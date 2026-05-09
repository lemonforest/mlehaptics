/* Channels 1-4: pure-phase STD4 coord-residual channels (1.18.0+).
 *
 * Float baseline (cs_channels_std4_4d):
 *   out_d[s] = COORD_RESID[d][s] × sig[s]
 *
 * Pure-phase: COORD_RESID is quarter-integer (multiples of 0.25, range
 * [-5.25, +5.25]), so scaling by 4 makes every entry an exact integer
 * in [-21, +21] and fits int8. The 1/4 dequantization factor is
 * absorbed in CHANNEL_DEQUANT_SCALES_4D[STD4_*].
 *
 * Output overflow envelope: |COORD_RESID_INT8| <= 21,
 * |sig| <= 48 (king, scaled), so |product| <= 21 × 48 = 1008 — int16
 * easily, int32 with vast margin.
 *
 * JPL discipline:
 *   - Two nested for-loops with fixed bounds (CS_N_DIMS, CS_N_SQUARES_4D).
 *   - Pointer + dimension assertions.
 *   - int32 promotion for the multiply explicit (no UB risk).
 */
#include <assert.h>
#include "cs_encoder_pure_phase_4d.h"

void cs_channels_pure_phase_std4_4d(
    const int16_t sig[CS_N_SQUARES_4D],
    int32_t out[CS_N_DIMS * CS_N_SQUARES_4D])
{
    assert(sig != NULL);
    assert(out != NULL);
    assert(CS_N_DIMS == 4);

    for (int d = 0; d < CS_N_DIMS; d++) {
        const int8_t *resid_d = COORD_RESID_INT8[d];
        int32_t      *out_d   = out + d * CS_N_SQUARES_4D;
        for (int s = 0; s < CS_N_SQUARES_4D; s++) {
            out_d[s] = (int32_t)resid_d[s] * (int32_t)sig[s];
        }
    }
}
