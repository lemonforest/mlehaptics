/* Channel 8: pawn antisymmetric fiber (DCT-mode space).
 *
 * Kronecker factorization: the full DCT-basis pawn-antisymmetry matrix
 * is I ⊗ I ⊗ I ⊗ W_ANTI_DCT, so each pawn at s = (sx,sy,sz,sw) writes
 * into only the 8 modes sharing (sx,sy,sz) along w:
 *     out[(sx,sy,sz,tw)] += sign * W_ANTI_DCT[sw, tw]   for tw in 0..7
 * where sign = +1 for 'P' and -1 for 'p'. 8 fp ops per pawn instead of
 * 4096 for the dense form — and exactly zero for the off-w modes that
 * the dense form would carry at < 1e-8 FP noise.
 *
 * Accumulate in a float64 scratch buffer (32 KB on the stack) and cast
 * once at the end, mirroring Python's
 *   pawn_ch = np.zeros(..., dtype=np.float64)
 *   ... pawn_ch[base:base+8] += sign * W_ANTI_DCT[sw]
 *   out[...] = pawn_ch.astype(np.float32)
 * bit-for-bit. Iteration order is ascending square index (pos->sq[s]
 * for s in 0..4095), matching the sorted_items loop in Python.
 */
#include <string.h>
#include "cs_encoder_4d.h"
#include "cs_fiber_tables_4d.h"
#include "cs_tables_4d.h"
#include "cs_types_4d.h"

void cs_channel_pawn_antisym_4d(const cs_position_4d_t *pos,
                                float out[CS_N_SQUARES_4D]) {
    double pawn_ch[CS_N_SQUARES_4D];
    memset(pawn_ch, 0, sizeof(pawn_ch));

    for (int s = 0; s < CS_N_SQUARES_4D; s++) {
        int8_t pc = pos->sq[s];
        if (pc != 'P' && pc != 'p') continue;
        double sign = (pc == 'P') ? 1.0 : -1.0;

        int sw   = s & 7;
        int base = s & ~7;  /* zero the low 3 bits — (sx,sy,sz,0) */
        const double *row = W_ANTI_DCT[sw];
        for (int tw = 0; tw < 8; tw++) {
            pawn_ch[base + tw] += sign * row[tw];
        }
    }

    for (int k = 0; k < CS_N_SQUARES_4D; k++) {
        out[k] = (float)pawn_ch[k];
    }
}
