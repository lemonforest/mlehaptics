/* Channels 5-7: cross-piece fiber-sym. P2a stub — zero-fills three
 * consecutive 4096-slabs. Real impl lands in P4 using sparse CSR
 * piece-adjacency tables + FIBER_LOCAL_4D[piece][s][d]. */
#include <string.h>
#include "cs_encoder_4d.h"

void cs_channels_fiber_sym_4d(const cs_position_4d_t *pos,
                              const double sig[CS_N_SQUARES_4D],
                              float out[CS_N_SYM_FIBER_4D * CS_N_SQUARES_4D]) {
    (void)pos;
    (void)sig;
    memset(out, 0, sizeof(float) * CS_N_SYM_FIBER_4D * CS_N_SQUARES_4D);
}
