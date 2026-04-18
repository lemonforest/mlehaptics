/* 4D encoder orchestration — cs_encode_4d.
 *
 * Writes the 10-channel, 40 960-float32 encoding. Per-channel impls
 * live in sibling TUs; this orchestrator only zero-inits the output,
 * builds the board signal, and dispatches. Channel-dispatch order is
 * independent of memory layout, so we preserve the Python reference
 * order (A1, STD4, FIB_SYM, FA_PAWN, FD_DIAG) for debuggability.
 *
 * Implementation cadence:
 *   P2a (this commit): scaffold + signal + zero-stub channel TUs
 *   P2b:  cs_a1_4d / cs_std4_4d / cs_diag_4d real impls
 *   P3:   cs_pawn_anti_4d real impl
 *   P4:   cs_fiber_sym_4d real impl
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
    cs_channel_a1_4d(         sig,      base + 0 * CS_N_SQUARES_4D);
    cs_channels_std4_4d(      sig,      base + 1 * CS_N_SQUARES_4D);
    cs_channels_fiber_sym_4d( pos, sig, base + 5 * CS_N_SQUARES_4D);
    cs_channel_pawn_antisym_4d(pos,     base + 8 * CS_N_SQUARES_4D);
    cs_channel_diag_4d(       pos, sig, base + 9 * CS_N_SQUARES_4D);
}
