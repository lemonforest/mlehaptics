/* Channel 0: A_1 orbit-mean projection. P2a stub — zero-fills the slab.
 * Real implementation lands in P2b using ORBIT_OF / ORBIT_MEMBERS /
 * ORBIT_OFFSETS / ORBIT_INV_SIZE from cs_tables_data_4d.c. */
#include <string.h>
#include "cs_encoder_4d.h"

void cs_channel_a1_4d(const double sig[CS_N_SQUARES_4D],
                      float out[CS_N_SQUARES_4D]) {
    (void)sig;
    memset(out, 0, sizeof(float) * CS_N_SQUARES_4D);
}
