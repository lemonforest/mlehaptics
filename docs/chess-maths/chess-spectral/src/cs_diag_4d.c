/* Channel 9: diagonal-deviation (rook shadow), DCT-mode space.
 *
 *   out[k] = sum over occupied s: sig[s] * DIAG_DEV_4D[piece_row(s), k]
 *
 * Iterate ascending square index so float64 summation order matches the
 * Python reference (encoder_4d.py uses sorted_items here, see v1.1 plan
 * P0 note). Accumulate in float64, cast once at the end.
 *
 * Vector DIAG_DEV_4D[row, :] is 4096 float64 (32 KB), stride-1. Each
 * occupied square costs one full-row fmadd sweep — cheap at 12-piece
 * fixtures, still fast on a full opening position (~32 pieces).
 */
#include <string.h>
#include "cs_encoder_4d.h"
#include "cs_fiber_tables_4d.h"
#include "cs_tables_4d.h"
#include "cs_types_4d.h"

void cs_channel_diag_4d(const cs_position_4d_t *pos,
                        const double sig[CS_N_SQUARES_4D],
                        float out[CS_N_SQUARES_4D]) {
    double accum[CS_N_SQUARES_4D];
    memset(accum, 0, sizeof(accum));

    for (int s = 0; s < CS_N_SQUARES_4D; s++) {
        int8_t pc = pos->sq[s];
        if (pc == 0) continue;
        int row = cs_piece_row_4d(pc);
        if (row < 0) continue;

        double val = sig[s];
        const double *diag_row = DIAG_DEV_4D[row];
        for (int k = 0; k < CS_N_SQUARES_4D; k++) {
            accum[k] += val * diag_row[k];
        }
    }

    for (int k = 0; k < CS_N_SQUARES_4D; k++) {
        out[k] = (float)accum[k];
    }
}
