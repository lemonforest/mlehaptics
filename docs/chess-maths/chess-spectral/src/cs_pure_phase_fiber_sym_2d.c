/* Channels 5-7: pure-phase fiber-symmetric 2D (1.19.0+).
 *
 * Mirrors chess_spectral.encoder_pure_phase._fiber_symmetric_int_batched
 * (1.17.0+ vectorize): outer per-fiber-piece-type loop over (n_sqs, 64)
 * tiles, batched gradient + scatter for all 3 d-channels.
 *
 * For each fiber-piece type p (N=0, B=1, R=2, Q=3, K=4):
 *   For each occupied square s with that piece type:
 *     adj_row    = LOCAL_ADJ_ROWS_INT8[p, s]   (64 int8)
 *     fib_d_vec  = LOCAL_FIBER_3D_INT16[p, s]  (3 int16)
 *     gradient   = sum_t adj_row[t] * sig[t]
 *     for d in 0..2:
 *       weighted_d = gradient * fib_d_vec[d]
 *       for t in 0..63:
 *         fc[d][t] += weighted_d * adj_row[t]
 *
 * Mathematical operation is fully integer + associative/commutative
 * across both s and p, so any deterministic iteration order produces
 * bit-identical output. We iterate piece types in p=0..4 order and
 * squares in s=0..63 order (ascending) for a single-pass scan.
 *
 * Overflow envelope (int64 accumulator):
 *   |gradient|         <= 64 * 200          = 12 800
 *   |gradient * fib_d| <= 12 800 * 32 767   = 4.2e8
 *   per-cell sum over up to 32 pieces: <= 32 * 4.2e8 = 1.3e10
 *   That overflows int32 (2.1e9), so int64 accumulator required.
 *   Final cast to int32 at output is safe in practice; the worst
 *   pathological case (all kings, all squares) would clamp; but
 *   real chess positions stay well under int32.
 *
 * JPL discipline:
 *   - Two helper functions split out so each <= 60 lines.
 *   - Stack: 3 * 64 * 8 = 1.5 KB int64 accumulator.
 *   - 4 assertions (pos/sig/out + invariant on CS_NUM_SYM_FIBER).
 */
#include <assert.h>
#include <string.h>
#include "cs_encoder_pure_phase_2d.h"

/* Map piece char to fiber-piece index (0..4). Pawns return -1
 * (not in symmetric fiber). Lowercase mapped to same fiber index
 * as uppercase. */
static int fiber_piece_idx(int8_t pc)
{
    switch (pc) {
        case 'N': case 'n': return 0;
        case 'B': case 'b': return 1;
        case 'R': case 'r': return 2;
        case 'Q': case 'q': return 3;
        case 'K': case 'k': return 4;
        default:            return -1;
    }
}

/* Process one occupied non-pawn square: read its dense adj_row,
 * compute the gradient, then scatter (gradient * fib_d * adj_row[t])
 * into all 3 d-channels of fc.
 *
 * Split out from the orchestrator to keep both functions <= 60 lines
 * (JPL rule). */
static void pp_fiber_sym_one_piece_2d(
    int s,
    int pidx,
    const int16_t sig[CS_BOARD_DIM],
    int64_t fc[CS_NUM_SYM_FIBER][CS_BOARD_DIM])
{
    assert(sig != NULL);
    assert(pidx >= 0 && pidx < CS_NUM_FIBER_PIECES);

    const int8_t *adj_row = LOCAL_ADJ_ROWS_INT8[pidx][s];
    const int16_t fib_0 = LOCAL_FIBER_3D_INT16[pidx][s][0];
    const int16_t fib_1 = LOCAL_FIBER_3D_INT16[pidx][s][1];
    const int16_t fib_2 = LOCAL_FIBER_3D_INT16[pidx][s][2];
    if (fib_0 == 0 && fib_1 == 0 && fib_2 == 0) {
        return;
    }

    /* gradient = sum_t adj_row[t] * sig[t]. */
    int32_t gradient = 0;
    for (int t = 0; t < CS_BOARD_DIM; t++) {
        if (adj_row[t] != 0) {
            gradient += (int32_t)sig[t];
        }
    }
    if (gradient == 0) {
        return;
    }

    const int64_t w0 = (int64_t)gradient * (int64_t)fib_0;
    const int64_t w1 = (int64_t)gradient * (int64_t)fib_1;
    const int64_t w2 = (int64_t)gradient * (int64_t)fib_2;

    for (int t = 0; t < CS_BOARD_DIM; t++) {
        if (adj_row[t] != 0) {
            fc[0][t] += w0;
            fc[1][t] += w1;
            fc[2][t] += w2;
        }
    }
}

void cs_channels_pure_phase_fiber_sym_2d(
    const cs_pure_phase_position_2d_t *pos,
    const int16_t sig[CS_BOARD_DIM],
    int32_t out[CS_NUM_SYM_FIBER * CS_BOARD_DIM])
{
    assert(pos != NULL);
    assert(sig != NULL);
    assert(out != NULL);
    assert(CS_NUM_SYM_FIBER == 3);

    /* int64 accumulator avoids intermediate overflow during the
     * piece-by-piece contraction. See module header for envelope. */
    int64_t fc[CS_NUM_SYM_FIBER][CS_BOARD_DIM];
    memset(fc, 0, sizeof(fc));

    /* Single ascending-square pass; per-piece-type filtering happens
     * inside the loop. The math is order-independent (associative
     * integer add) so this matches Python's group-by-type batched
     * implementation bit-for-bit. */
    for (int s = 0; s < CS_BOARD_DIM; s++) {
        const int8_t pc = pos->sq[s];
        const int pidx = fiber_piece_idx(pc);
        if (pidx < 0) {
            continue;  /* empty square or pawn */
        }
        pp_fiber_sym_one_piece_2d(s, pidx, sig, fc);
    }

    /* Cast int64 accumulator to int32 output. */
    for (int d = 0; d < CS_NUM_SYM_FIBER; d++) {
        int32_t *out_d = out + (d * CS_BOARD_DIM);
        for (int k = 0; k < CS_BOARD_DIM; k++) {
            out_d[k] = (int32_t)fc[d][k];
        }
    }
}
