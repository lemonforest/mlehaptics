/* Channel 10: pure-phase FD_DIAG (1.18.0+).
 *
 * Mirror of cs_channel_diag_4d in integer arithmetic, with the 1.17.0
 * group-by-piece-type optimization: instead of accumulating into a
 * 4096-vector per occupied square, group by piece-row (6 piece types:
 * P, N, B, R, Q, K), sum sig values per group, then do ONE 4096-vector
 * add per group.
 *
 * Algorithm:
 *   coef[piece_row] = sum over occupied squares s of sig[s]
 *                     restricted to piece_row(s) == piece_row
 *   diag_ch[k] = sum over piece_row of:
 *                  coef[piece_row] × DIAG_DEV_INT16_4D[piece_row, k]
 *
 * Overflow envelope (int64 accumulator):
 *   |coef[row]|         <= 32 pieces × 48 (king)            = 1 536
 *   |coef × DIAG|       <= 1 536 × 32 767                   = 5.0e7
 *   |sum over 6 rows|   <= 6 × 5.0e7                        = 3.0e8
 *   Well within int32 (2.1e9). Use int64 anyway for safety
 *   margin against pathological all-K positions.
 *
 * JPL discipline:
 *   - Stack: 4096 × 8 = 32 KB (int64 accumulator), 6 × 4 = 24 B (coef).
 *   - Two passes (gather + scatter), each fixed-bound.
 *   - 4 assertions covering pos/sig/out + table dimensions.
 */
#include <assert.h>
#include <string.h>
#include "cs_encoder_pure_phase_4d.h"

void cs_channel_pure_phase_diag_4d(
    const cs_position_4d_t *pos,
    const int16_t sig[CS_N_SQUARES_4D],
    int32_t out[CS_N_SQUARES_4D])
{
    assert(pos != NULL);
    assert(sig != NULL);
    assert(out != NULL);
    assert(CS_PIECE_4D_COUNT == 6);

    /* Pass 1: group-by-piece-type sum. coef[row] = sum sig[s] over
     * squares where cs_piece_row_4d(sq[s]) == row. */
    int32_t coef[CS_PIECE_4D_COUNT];
    memset(coef, 0, sizeof(coef));

    for (int s = 0; s < CS_N_SQUARES_4D; s++) {
        const int8_t pc = pos->sq[s];
        if (pc == 0) {
            continue;
        }
        const int row = cs_piece_row_4d(pc);
        if (row < 0) {
            continue;
        }
        coef[row] += (int32_t)sig[s];
    }

    /* Pass 2: scatter — diag_ch[k] = sum_row coef[row] × DIAG_DEV[row, k]. */
    int64_t diag_ch[CS_N_SQUARES_4D];
    memset(diag_ch, 0, sizeof(diag_ch));

    for (int row = 0; row < CS_PIECE_4D_COUNT; row++) {
        const int32_t c = coef[row];
        if (c == 0) {
            continue;  /* avoid pointless 4096-vector add */
        }
        const int16_t *dd_row = DIAG_DEV_INT16_4D[row];
        for (int k = 0; k < CS_N_SQUARES_4D; k++) {
            diag_ch[k] += (int64_t)c * (int64_t)dd_row[k];
        }
    }

    for (int k = 0; k < CS_N_SQUARES_4D; k++) {
        out[k] = (int32_t)diag_ch[k];
    }
}
