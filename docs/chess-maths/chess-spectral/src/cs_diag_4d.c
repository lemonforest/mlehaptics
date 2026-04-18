/* Channel 9: diagonal-deviation (rook shadow) in DCT-mode space.
 * P2a stub — zero-fills the slab. Real impl in P2b accumulates
 * sig[s] * DIAG_DEV_4D[piece_row(pc), :] over occupied squares. */
#include <string.h>
#include "cs_encoder_4d.h"

void cs_channel_diag_4d(const cs_position_4d_t *pos,
                        const double sig[CS_N_SQUARES_4D],
                        float out[CS_N_SQUARES_4D]) {
    (void)pos;
    (void)sig;
    memset(out, 0, sizeof(float) * CS_N_SQUARES_4D);
}
