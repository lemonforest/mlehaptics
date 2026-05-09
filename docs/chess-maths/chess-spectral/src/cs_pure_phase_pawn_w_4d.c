/* Channel 8: pure-phase FA_PAWN_W (1.18.0+).
 *
 * Mirror of cs_channel_fa_pawn_w_4d in integer arithmetic. Pawn weight
 * is ±1 (no piece-value scaling); the 1/scale_w_anti_dct/32767
 * dequantization factor is in CHANNEL_DEQUANT_SCALES_4D[FA_PAWN_W].
 *
 *   For each W-axis pawn at s = (sx, sy, sz, sw):
 *     pawn_ch[(sx, sy, sz, tw)] += sign × W_ANTI_DCT_INT16[sw, tw]
 *   for tw in 0..7
 *
 * Overflow envelope: |W_ANTI_DCT_INT16| <= 32767, sign is ±1, max
 * pawns per (sx, sy, sz) line is 8 → |pawn_ch[k]| <= 8 × 32767
 * = 262 136. int32 storage with vast margin.
 *
 * JPL discipline:
 *   - 3 assertions; all loops fixed-bound; int64 accumulator on
 *     stack only at 32 KB.
 *   - Output cast to int32 once at the end.
 */
#include <assert.h>
#include <string.h>
#include "cs_encoder_pure_phase_4d.h"

void cs_channel_pure_phase_fa_pawn_w_4d(
    const cs_position_4d_t *pos,
    int32_t out[CS_N_SQUARES_4D])
{
    assert(pos != NULL);
    assert(out != NULL);
    assert(CS_N_SQUARES_4D == 4096);

    int64_t pawn_ch[CS_N_SQUARES_4D];
    memset(pawn_ch, 0, sizeof(pawn_ch));

    for (int s = 0; s < CS_N_SQUARES_4D; s++) {
        const int8_t pc = pos->sq[s];
        if (pc != 'P' && pc != 'p') {
            continue;
        }
        if (pos->pawn_axis[s] != CS_PAWN_AXIS_W) {
            continue;
        }
        const int sign = (pc == 'P') ? 1 : -1;
        const int sw   = s & 7;
        const int base = s & ~7;  /* (sx, sy, sz, 0) */
        const int16_t *row = W_ANTI_DCT_INT16[sw];
        for (int tw = 0; tw < 8; tw++) {
            pawn_ch[base + tw] += (int64_t)sign * (int64_t)row[tw];
        }
    }

    for (int k = 0; k < CS_N_SQUARES_4D; k++) {
        out[k] = (int32_t)pawn_ch[k];
    }
}
