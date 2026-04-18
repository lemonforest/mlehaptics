/* Channels 1-4: std-4D coordinate-residual channels.
 *
 *   out_d[s] = COORD_RESID[d][s] * sig[s]   for d in 0..3
 *
 * One channel per lattice axis (x, y, z, w). The output slab points at
 * channel 1; four consecutive 4096-blocks are written. Multiplication
 * in float64 then single cast to float32 per element — matches Python
 *   (coord_resid[a] * sig).astype(np.float32)
 * exactly, bit-for-bit.
 */
#include "cs_encoder_4d.h"
#include "cs_tables_4d.h"

void cs_channels_std4_4d(const double sig[CS_N_SQUARES_4D],
                         float out[CS_N_DIMS * CS_N_SQUARES_4D]) {
    for (int d = 0; d < CS_N_DIMS; d++) {
        const double *resid_d = COORD_RESID[d];
        float        *out_d   = out + d * CS_N_SQUARES_4D;
        for (int s = 0; s < CS_N_SQUARES_4D; s++) {
            out_d[s] = (float)(resid_d[s] * sig[s]);
        }
    }
}
