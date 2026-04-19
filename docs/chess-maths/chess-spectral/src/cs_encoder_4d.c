/* 4D encoder orchestration -- cs_encode_4d.
 *
 * Writes the 11-channel, 45 056-float32 encoding (v1.1.1). Per-channel
 * impls live in sibling TUs; this orchestrator only zero-inits the
 * output, builds the board signal, and dispatches. Channel-dispatch
 * order is independent of memory layout, so we preserve the Python
 * reference order (A1, STD4, FIB_SYM, FA_PAWN_W, FA_PAWN_Y, FD_DIAG)
 * for debuggability.
 *
 * Implementation cadence:
 *   P2a (initial):  scaffold + signal + zero-stub channel TUs
 *   P2b:            cs_a1_4d / cs_std4_4d / cs_diag_4d real impls
 *   P3 (v1.0):      cs_pawn_anti_4d real impl (w-axis only)
 *   P4 (v1.0):      cs_fiber_sym_4d real impl
 *   P4 (v1.1.1):    offset macros + cs_channel_fa_pawn_y_4d hook
 *                   (FA_PAWN_Y output is zero-stub until P6)
 *   P6 (v1.1.1):    cs_channel_fa_pawn_w_4d routes on pos->pawn_axis;
 *                   cs_channel_fa_pawn_y_4d gets its real impl
 */
#include <string.h>
#include "cs_encoder_4d.h"

void cs_encode_4d(const cs_position_4d_t *pos,
                  cs_encoding_4d_t *enc) {
    double sig[CS_N_SQUARES_4D];
    cs_board_signal_4d(pos, sig);

    /* Zero up front so any channel writer accumulating into its slab
     * starts from a clean slate. */
    memset(enc->v, 0, sizeof(enc->v));

    float *base = enc->v;
    cs_channel_a1_4d(         sig,      base + CS_CHANNEL_A1_OFFSET);
    cs_channels_std4_4d(      sig,      base + CS_CHANNEL_STD4_OFFSET);
    cs_channels_fiber_sym_4d( pos, sig, base + CS_CHANNEL_FIB_SYM_OFFSET);
    cs_channel_fa_pawn_w_4d(  pos,      base + CS_CHANNEL_FA_PAWN_W_OFFSET);
    cs_channel_fa_pawn_y_4d(  pos,      base + CS_CHANNEL_FA_PAWN_Y_OFFSET);
    cs_channel_diag_4d(       pos, sig, base + CS_CHANNEL_FD_DIAG_OFFSET);
}
