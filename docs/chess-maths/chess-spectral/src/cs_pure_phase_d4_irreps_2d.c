/* Channels 0-4: pure-phase D₄ irrep projections (1.19.0+).
 *
 * Float baseline (cs_project_irrep with VALS):
 *   out[s] = (dim_mu / 8) * sum_g CHARS[mu][g] * sig[D4_PERMS[g][s]]
 *
 * Pure-phase: drop the dim_mu/8 division and absorb it into the
 * channel dequantization scale. CHARS entries are integer-valued
 * (±1, ±2, 0) so the character formula is already integer at the
 * core — no scale-by-LCM trick needed (unlike 4D's A_1 orbit sum).
 *
 *   out[s] = sum_g CHARS[mu][g] * sig[D4_PERMS[g][s]]
 *
 * The dim_mu/8/_VALS_INT_SCALE_2D factor is reapplied via
 * CHANNEL_DEQUANT_SCALES_2D[*] at the float boundary.
 *
 * Mirror of the Python ``_project_irrep_int`` reference, expanded
 * over all 5 irreps. The `c == 0` / `c == 1` / `c == -1` fast paths
 * match Python's branching exactly so iteration order and zero-skip
 * behaviour are bit-identical.
 *
 * Overflow envelope (per output cell, signed int32):
 *   max |sig|             = 200          (king, scaled)
 *   max |CHARS|           = 2            (E channel)
 *   max |sum over 8 g's|  = 8 * 2 * 200 = 3200    -- fits int16
 *   For the all-king extreme: still well within int32 (2.1e9).
 *
 * JPL discipline:
 *   - Three nested for-loops with fixed bounds (5, 8, 64).
 *   - Three assertions; all variable scope minimized.
 *   - Single int32 accumulator per output cell.
 */
#include <assert.h>
#include "cs_encoder_pure_phase_2d.h"

void cs_channels_pure_phase_d4_irreps_2d(
    const int16_t sig[CS_BOARD_DIM],
    int32_t out[CS_NUM_IRREPS * CS_BOARD_DIM])
{
    assert(sig != NULL);
    assert(out != NULL);
    assert(CS_NUM_IRREPS == 5);

    for (int mu = 0; mu < CS_NUM_IRREPS; mu++) {
        const int8_t *chars_mu = CHARS[mu];
        int32_t *out_mu = out + (mu * CS_BOARD_DIM);

        /* Initialize this irrep's slab to zero. */
        for (int s = 0; s < CS_BOARD_DIM; s++) {
            out_mu[s] = 0;
        }

        for (int g = 0; g < 8; g++) {
            const int c = (int)chars_mu[g];
            if (c == 0) {
                continue;  /* skip zero-character contributions (E has 6) */
            }
            const uint8_t *perm = D4_PERMS[g];
            if (c == 1) {
                for (int s = 0; s < CS_BOARD_DIM; s++) {
                    out_mu[s] += (int32_t)sig[perm[s]];
                }
            } else if (c == -1) {
                for (int s = 0; s < CS_BOARD_DIM; s++) {
                    out_mu[s] -= (int32_t)sig[perm[s]];
                }
            } else {
                /* c is ±2 (E channel). */
                for (int s = 0; s < CS_BOARD_DIM; s++) {
                    out_mu[s] += (int32_t)c * (int32_t)sig[perm[s]];
                }
            }
        }
    }
}
