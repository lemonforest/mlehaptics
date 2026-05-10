/* Channel 9: pure-phase FD diagonal deviation 2D (1.19.0+).
 *
 * Mirror of chess_spectral.encoder_pure_phase._fiber_diagonal_int with
 * the group-by-piece-type optimization (mirrors the 4D port's
 * cs_pure_phase_diag_4d.c approach): instead of accumulating into a
 * 64-vector per occupied square, group by piece-row (6 piece types:
 * P, N, B, R, Q, K), sum sig values per group, then do ONE 64-vector
 * add per non-zero group.
 *
 * Algorithm:
 *   coef[piece_row] = sum over occupied squares s of sig[s]
 *                     restricted to piece_row(s) == piece_row
 *   diag_ch[k] = sum over piece_row of:
 *                  coef[piece_row] * DIAG_DEV_INT16_2D[piece_row][k]
 *
 * Mathematically equivalent to the per-square Python loop because
 * integer addition is associative + commutative.
 *
 * Overflow envelope (int64 accumulator):
 *   |coef[row]|         <= 32 pieces * 200 (king)            = 6 400
 *   |coef * DIAG_INT16| <= 6 400 * 32 767                    = 2.1e8
 *   |sum over 6 rows|   <= 6 * 2.1e8                         = 1.3e9
 *   Within int32 (2.1e9). Use int64 anyway for safety
 *   margin against pathological all-K positions.
 *
 * JPL discipline:
 *   - Stack: 64 * 8 = 512 B (int64 accumulator), 6 * 4 = 24 B (coef).
 *   - Two passes (gather + scatter), each fixed-bound.
 *   - 4 assertions covering pos/sig/out + invariant.
 */
#include <assert.h>
#include <string.h>
#include "cs_encoder_pure_phase_2d.h"

/* Map piece char to diag-piece row (0..5 for P,N,B,R,Q,K).
 * Lowercase folded to same row as uppercase. Returns -1 for empty
 * squares. */
static int diag_piece_idx(int8_t pc)
{
    switch (pc) {
        case 'P': case 'p': return 0;
        case 'N': case 'n': return 1;
        case 'B': case 'b': return 2;
        case 'R': case 'r': return 3;
        case 'Q': case 'q': return 4;
        case 'K': case 'k': return 5;
        default:            return -1;
    }
}

void cs_channel_pure_phase_diag_2d(
    const cs_pure_phase_position_2d_t *pos,
    const int16_t sig[CS_BOARD_DIM],
    int32_t out[CS_BOARD_DIM])
{
    assert(pos != NULL);
    assert(sig != NULL);
    assert(out != NULL);
    assert(CS_NUM_DIAG_PIECES == 6);

    /* Pass 1: group-by-piece-type sum. coef[row] = sum sig[s] over
     * squares where diag_piece_idx(sq[s]) == row. */
    int32_t coef[CS_NUM_DIAG_PIECES];
    memset(coef, 0, sizeof(coef));

    for (int s = 0; s < CS_BOARD_DIM; s++) {
        const int8_t pc = pos->sq[s];
        if (pc == 0) {
            continue;
        }
        const int row = diag_piece_idx(pc);
        if (row < 0) {
            continue;
        }
        coef[row] += (int32_t)sig[s];
    }

    /* Pass 2: scatter — diag[k] = sum_row coef[row] * DIAG_DEV[row][k]. */
    int64_t diag[CS_BOARD_DIM];
    memset(diag, 0, sizeof(diag));

    for (int row = 0; row < CS_NUM_DIAG_PIECES; row++) {
        const int32_t c = coef[row];
        if (c == 0) {
            continue;  /* avoid pointless 64-vector add */
        }
        const int16_t *dd_row = DIAG_DEV_INT16_2D[row];
        for (int k = 0; k < CS_BOARD_DIM; k++) {
            diag[k] += (int64_t)c * (int64_t)dd_row[k];
        }
    }

    for (int k = 0; k < CS_BOARD_DIM; k++) {
        out[k] = (int32_t)diag[k];
    }
}
