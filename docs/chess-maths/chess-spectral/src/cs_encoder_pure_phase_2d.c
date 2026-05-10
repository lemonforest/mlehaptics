/* Pure-phase 2D encoder orchestration (1.19.0+).
 *
 * Mirror of cs_encode_640 in integer arithmetic. Builds the int16
 * board signal once and dispatches to per-channel implementations
 * in the same order as the Python reference (A1, A2, B1, B2, E,
 * F1, F2, F3, FA, FD).
 *
 * Output is int32 throughout (no float in the hot path). Callers
 * that want float64 values comparable to encode_640(pos, vals=VALS)
 * can dequantize post-hoc via CHANNEL_DEQUANT_SCALES_2D.
 *
 * Bit-exact parity target: chess_spectral.encoder_pure_phase's
 * encode_2d_pure_phase. Tolerance 0 (true bit-equality) on all
 * channels for reasonable chess positions.
 *
 * JPL discipline:
 *   - Single function, ~25 lines.
 *   - 2 assertions on input args + 1 invariant.
 *   - All channel functions called with bounded sub-buffers.
 */
#include <assert.h>
#include <string.h>
#include "cs_encoder_pure_phase_2d.h"

void cs_encode_pure_phase_2d(
    const cs_pure_phase_position_2d_t *pos,
    cs_pure_phase_encoding_2d_t *enc)
{
    assert(pos != NULL);
    assert(enc != NULL);
    assert(CS_PURE_PHASE_DIM_2D == 640);

    /* Build the int16 signal once. Stack: 128 B. */
    int16_t sig[CS_BOARD_DIM];
    cs_board_signal_pure_phase_2d(pos, sig);

    /* Zero up front so any channel writer accumulating into its
     * slab starts from a clean slate. */
    memset(enc->v, 0, sizeof(enc->v));

    int32_t *base = enc->v;
    cs_channels_pure_phase_d4_irreps_2d(
        sig,      base + CS_CHANNEL_A1_OFFSET_2D);
    cs_channels_pure_phase_fiber_sym_2d(
        pos, sig, base + CS_CHANNEL_F1_OFFSET_2D);
    cs_channel_pure_phase_fa_2d(
        pos,      base + CS_CHANNEL_FA_OFFSET_2D);
    cs_channel_pure_phase_diag_2d(
        pos, sig, base + CS_CHANNEL_FD_OFFSET_2D);
}
