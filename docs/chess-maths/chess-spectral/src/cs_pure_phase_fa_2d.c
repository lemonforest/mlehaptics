/* Channel 8: pure-phase FA (pawn antisymmetric) 2D (1.19.0+).
 *
 * Mirror of chess_spectral.encoder_pure_phase._fiber_antisymmetric_int.
 * Pawn contributions only; the per-pawn weight is the integer pawn
 * value (P=2 with CS_VALS_INT_SCALE_2D=2 applied) signed by color.
 *
 *   For each pawn at s (any color):
 *     weight = +SIGNED_VALS_INT_2D[P_idx] if uppercase 'P'
 *              -SIGNED_VALS_INT_2D[P_idx] if lowercase 'p'
 *     out[k] += weight * PAWN_ANTI_FIBER_INT16[s][k]
 *
 * The 1/_VALS_INT_SCALE_2D / scale_pawn_anti / 32767 dequantization
 * factor is in CHANNEL_DEQUANT_SCALES_2D[FA].
 *
 * Overflow envelope (int64 accumulator):
 *   |weight|              = 2
 *   |PAWN_ANTI_FIBER|     <= 32 767
 *   |per-cell single pawn|<= 2 * 32 767                = 65 534
 *   max pawns (16 white + 16 black on full 64-cell)   = 32
 *   |out[k]|              <= 32 * 65 534               = 2.1e6
 *   Well within int32.
 *
 * JPL discipline:
 *   - 3 assertions; all loops fixed-bound.
 *   - Single int32 accumulator on stack (256 B).
 *   - Pawn idx index lookup via two case branches, no
 *     function pointers.
 */
#include <assert.h>
#include <string.h>
#include "cs_encoder_pure_phase_2d.h"

/* Index 0 in SIGNED_VALS_INT_2D is 'P' (white pawn); we compute
 * the magnitude once per call. The compiler should constant-fold
 * SIGNED_VALS_INT_2D[0] but we read it explicitly for clarity. */

void cs_channel_pure_phase_fa_2d(
    const cs_pure_phase_position_2d_t *pos,
    int32_t out[CS_BOARD_DIM])
{
    assert(pos != NULL);
    assert(out != NULL);
    assert(CS_BOARD_DIM == 64);

    /* Pawn magnitude (scaled): +SIGNED_VALS_INT_2D[0] is for 'P'. */
    const int32_t pawn_mag = (int32_t)SIGNED_VALS_INT_2D[0];

    int32_t acc[CS_BOARD_DIM];
    memset(acc, 0, sizeof(acc));

    for (int s = 0; s < CS_BOARD_DIM; s++) {
        const int8_t pc = pos->sq[s];
        if (pc != 'P' && pc != 'p') {
            continue;
        }
        const int32_t weight = (pc == 'P') ? pawn_mag : -pawn_mag;
        const int16_t *row = PAWN_ANTI_FIBER_INT16[s];
        for (int k = 0; k < CS_BOARD_DIM; k++) {
            acc[k] += weight * (int32_t)row[k];
        }
    }

    for (int k = 0; k < CS_BOARD_DIM; k++) {
        out[k] = acc[k];
    }
}
