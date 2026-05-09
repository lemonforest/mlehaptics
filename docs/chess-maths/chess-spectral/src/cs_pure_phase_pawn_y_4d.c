/* Channel 9: pure-phase FA_PAWN_Y (1.18.0+).
 *
 * Mirror of cs_channel_fa_pawn_y_4d in integer arithmetic. Identical
 * structure to FA_PAWN_W but the 8x8 antisymmetric block sits on the
 * y-tensor leg of the Kronecker product:
 *
 *   For each Y-axis pawn at s = (sx, sy, sz, sw):
 *     pawn_ch[(sx, ty, sz, sw)] += sign × Y_ANTI_DCT_INT16[sy, ty]
 *   for ty in 0..7  (stride 64 along the y-axis bits)
 *
 * The 1/scale_y_anti_dct/32767 dequantization factor is in
 * CHANNEL_DEQUANT_SCALES_4D[FA_PAWN_Y].
 *
 * Overflow envelope: same as FA_PAWN_W — int64 accumulator handles
 * any realistic chess position; final cast to int32 is safe.
 *
 * JPL discipline: same shape as FA_PAWN_W (3 assertions, fixed loops).
 */
#include <assert.h>
#include <string.h>
#include "cs_encoder_pure_phase_4d.h"

void cs_channel_pure_phase_fa_pawn_y_4d(
    const cs_position_4d_t *pos,
    int32_t out[CS_N_SQUARES_4D])
{
    assert(pos != NULL);
    assert(out != NULL);
    assert(CS_N_SQUARES_4D == 4096);

    int64_t pawn_ch[CS_N_SQUARES_4D];
    memset(pawn_ch, 0, sizeof(pawn_ch));

    /* y-axis bits (6..8) of the square index. */
    const int Y_MASK = 7 << 6;  /* 0x1C0 */

    for (int s = 0; s < CS_N_SQUARES_4D; s++) {
        const int8_t pc = pos->sq[s];
        if (pc != 'P' && pc != 'p') {
            continue;
        }
        if (pos->pawn_axis[s] != CS_PAWN_AXIS_Y) {
            continue;
        }
        const int sign = (pc == 'P') ? 1 : -1;
        const int sy   = (s >> 6) & 7;
        const int base = s & ~Y_MASK;  /* (sx, 0, sz, sw) */
        const int16_t *row = Y_ANTI_DCT_INT16[sy];
        for (int ty = 0; ty < 8; ty++) {
            pawn_ch[base | (ty << 6)] += (int64_t)sign * (int64_t)row[ty];
        }
    }

    for (int k = 0; k < CS_N_SQUARES_4D; k++) {
        out[k] = (int32_t)pawn_ch[k];
    }
}
