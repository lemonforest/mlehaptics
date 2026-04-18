/* Channels 1-4: standard-rep (coord-residual) channels. P2a stub —
 * zero-fills four 4096-slabs. Real impl in P2b does
 * out_d[s] = COORD_RESID[d][s] * sig[s] for d in 0..3. */
#include <string.h>
#include "cs_encoder_4d.h"

void cs_channels_std4_4d(const double sig[CS_N_SQUARES_4D],
                         float out[CS_N_DIMS * CS_N_SQUARES_4D]) {
    (void)sig;
    memset(out, 0, sizeof(float) * CS_N_DIMS * CS_N_SQUARES_4D);
}
