/* Pure-phase 4D encoder orchestration (1.18.0+).
 *
 * Mirror of cs_encode_4d in integer arithmetic. Builds the int16
 * board signal once and dispatches to per-channel implementations
 * in the same order as the Python reference (A1, STD4, FIB_SYM,
 * FA_PAWN_W, FA_PAWN_Y, FD_DIAG).
 *
 * Output is int32 throughout (no float in the hot path). Callers
 * that want float64 values comparable to encode_4d can dequantize
 * post-hoc via CHANNEL_DEQUANT_SCALES_4D.
 *
 * Bit-exact parity target: chess_spectral.encoder_pure_phase_4d's
 * encode_4d_pure_phase. Tolerance 0 (true bit-equality) on all
 * channels for reasonable chess positions; the only allowed source
 * of divergence would be int32 overflow at extreme synthetic dense
 * positions (which would also affect the Python reference).
 *
 * JPL discipline:
 *   - Single function, ~25 lines.
 *   - 2 assertions on input args.
 *   - All channel functions called with bounded sub-buffers.
 */
#include <assert.h>
#include <string.h>
#include "cs_encoder_pure_phase_4d.h"

void cs_encode_pure_phase_4d(
    const cs_position_4d_t *pos,
    cs_pure_phase_encoding_4d_t *enc)
{
    assert(pos != NULL);
    assert(enc != NULL);

    /* Build the int16 signal once. Stack: 8 KB. */
    int16_t sig[CS_N_SQUARES_4D];
    cs_board_signal_pure_phase_4d(pos, sig);

    /* Zero up front so any channel writer accumulating into its
     * slab starts from a clean slate. */
    memset(enc->v, 0, sizeof(enc->v));

    int32_t *base = enc->v;
    cs_channel_pure_phase_a1_4d(
        sig,      base + CS_CHANNEL_A1_OFFSET);
    cs_channels_pure_phase_std4_4d(
        sig,      base + CS_CHANNEL_STD4_OFFSET);
    cs_channels_pure_phase_fiber_sym_4d(
        pos, sig, base + CS_CHANNEL_FIB_SYM_OFFSET);
    cs_channel_pure_phase_fa_pawn_w_4d(
        pos,      base + CS_CHANNEL_FA_PAWN_W_OFFSET);
    cs_channel_pure_phase_fa_pawn_y_4d(
        pos,      base + CS_CHANNEL_FA_PAWN_Y_OFFSET);
    cs_channel_pure_phase_diag_4d(
        pos, sig, base + CS_CHANNEL_FD_DIAG_OFFSET);
}
