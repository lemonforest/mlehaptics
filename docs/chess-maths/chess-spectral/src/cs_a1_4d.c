/* Channel 0: A_1 orbit-mean projection.
 *
 * Implements (P_A1 @ sig) where P_A1 is the B_4-averaging projector:
 *   out[s] = (1 / |orbit(s)|) * sum_{t in orbit(s)} sig[t]
 *
 * Orbits are stored CSR-style:
 *   ORBIT_OFFSETS[o..o+1]  -> [start,end) slice into ORBIT_MEMBERS[]
 *   ORBIT_INV_SIZE[o]      -> 1.0 / |orbit o|
 *
 * Per-orbit work: one pass to sum sig[members], one to write mean
 * back. Total ~2*4096 = 8192 fp ops. All accumulation in float64;
 * single cast to float32 at write time (matches Python reference).
 */
#include "cs_encoder_4d.h"
#include "cs_tables_4d.h"

void cs_channel_a1_4d(const double sig[CS_N_SQUARES_4D],
                      float out[CS_N_SQUARES_4D]) {
    for (int o = 0; o < CS_N_ORBITS_4D; o++) {
        uint16_t start = ORBIT_OFFSETS[o];
        uint16_t end   = ORBIT_OFFSETS[o + 1];

        double sum = 0.0;
        for (uint16_t i = start; i < end; i++) {
            sum += sig[ORBIT_MEMBERS[i]];
        }
        float mean = (float)(sum * ORBIT_INV_SIZE[o]);

        for (uint16_t i = start; i < end; i++) {
            out[ORBIT_MEMBERS[i]] = mean;
        }
    }
}
