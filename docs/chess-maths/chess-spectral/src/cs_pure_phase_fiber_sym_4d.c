/* Channels 5-7: pure-phase fiber-symmetric (1.18.0+).
 *
 * Mirrors chess_spectral.encoder_pure_phase_4d's loop-swap +
 * broadcast pattern (1.17.0 vectorize): outer per-occupied-square,
 * batch all 3 d-channels via a (3, len(cols)) broadcast add.
 *
 * Per occupied non-pawn square s with piece p:
 *   gradient = sum sig[col] for col in PIECE_ADJ[p][s].indices
 *   for d in 0..2:
 *     fib_d_int16 = FIBER_LOCAL_INT16_4D[p, s, d]
 *     for col in PIECE_ADJ[p][s].indices:
 *         fc[d, col] += gradient × fib_d_int16
 *
 * The 1.14.0 fiber-quantize-tables story (int16 with abs-max scale)
 * applies here unchanged. The 1/scale_fiber/32767/_VALS_INT_SCALE
 * dequantization is in CHANNEL_DEQUANT_SCALES_4D[FIB_SYM_*].
 *
 * Overflow envelope (int64 accumulator):
 *   |gradient|        <= |max_adj_row_nnz| × |sig_max| ~= 100 × 48 = 4800
 *   |gradient × fib|  <= 4800 × 32767                  ~= 1.6e8
 *   |fc[d, c] sum|    <= 32 pieces × 1.6e8             ~= 5.0e9
 * 5.0e9 overflows int32 (2.1e9), so int64 accumulator required.
 * Final cast to int32 at output is safe because each cell's actual
 * accumulator stays well below 2³¹ on real chess positions.
 *
 * Stack usage: 3 × 4096 × 8 = 96 KB. Acceptable on desktop / server.
 *
 * JPL discipline:
 *   - Adjacency pointers via switch (data pointers, not function ptrs).
 *   - All loops bounded; CS_FIBER_DROPPED_MASK skips zero-rows.
 *   - 4 assertions (pos/sig/out non-null + table invariant).
 *   - inner functions <= 60 lines.
 */
#include <assert.h>
#include <string.h>
#include "cs_encoder_pure_phase_4d.h"
#include "cs_tables_4d.h"

/* Dispatch CSR row-pointer arrays by fiber-piece index. Mirrors the
 * float pattern in cs_fiber_sym_4d.c so the iteration order matches
 * exactly (sorted ascending col indices). */
static const int32_t *pp_adj_indptr_for(int pidx)
{
    switch (pidx) {
        case CS_FIBER_PIECE_4D_N: return PIECE_ADJ_INDPTR_N;
        case CS_FIBER_PIECE_4D_B: return PIECE_ADJ_INDPTR_B;
        case CS_FIBER_PIECE_4D_R: return PIECE_ADJ_INDPTR_R;
        case CS_FIBER_PIECE_4D_Q: return PIECE_ADJ_INDPTR_Q;
        case CS_FIBER_PIECE_4D_K: return PIECE_ADJ_INDPTR_K;
        default:                  return NULL;
    }
}

static const int32_t *pp_adj_indices_for(int pidx)
{
    switch (pidx) {
        case CS_FIBER_PIECE_4D_N: return PIECE_ADJ_INDICES_N;
        case CS_FIBER_PIECE_4D_B: return PIECE_ADJ_INDICES_B;
        case CS_FIBER_PIECE_4D_R: return PIECE_ADJ_INDICES_R;
        case CS_FIBER_PIECE_4D_Q: return PIECE_ADJ_INDICES_Q;
        case CS_FIBER_PIECE_4D_K: return PIECE_ADJ_INDICES_K;
        default:                  return NULL;
    }
}

/* Process one occupied non-pawn square: read CSR row, compute the
 * gradient, scatter (gradient × fib_d) into all 3 d-channels.
 *
 * Split out from the orchestrator to keep both functions <= 60 lines
 * (JPL rule). */
static void pp_fiber_sym_one_piece(
    int s,
    int pidx,
    const int16_t sig[CS_N_SQUARES_4D],
    int64_t fc_all[CS_N_SYM_FIBER_4D][CS_N_SQUARES_4D])
{
    assert(sig != NULL);
    assert(pidx >= 0 && pidx < CS_FIBER_PIECE_4D_COUNT);

    const int32_t *indptr  = pp_adj_indptr_for(pidx);
    const int32_t *indices = pp_adj_indices_for(pidx);
    if (indptr == NULL || indices == NULL) {
        return;
    }
    const int32_t start = indptr[s];
    const int32_t end   = indptr[s + 1];
    if (start == end) {
        return;  /* isolated square */
    }

    /* gradient = sum of sig[col] over the CSR row. */
    int32_t gradient = 0;
    for (int32_t i = start; i < end; i++) {
        gradient += (int32_t)sig[indices[i]];
    }
    if (gradient == 0) {
        return;
    }

    /* Fetch the 3 d-channel fiber values once. */
    const int16_t fib_0 = FIBER_LOCAL_INT16_4D[pidx][s][0];
    const int16_t fib_1 = FIBER_LOCAL_INT16_4D[pidx][s][1];
    const int16_t fib_2 = FIBER_LOCAL_INT16_4D[pidx][s][2];
    if (fib_0 == 0 && fib_1 == 0 && fib_2 == 0) {
        return;
    }

    const int64_t w0 = (int64_t)gradient * (int64_t)fib_0;
    const int64_t w1 = (int64_t)gradient * (int64_t)fib_1;
    const int64_t w2 = (int64_t)gradient * (int64_t)fib_2;

    for (int32_t i = start; i < end; i++) {
        const int32_t col = indices[i];
        fc_all[0][col] += w0;
        fc_all[1][col] += w1;
        fc_all[2][col] += w2;
    }
}

void cs_channels_pure_phase_fiber_sym_4d(
    const cs_position_4d_t *pos,
    const int16_t sig[CS_N_SQUARES_4D],
    int32_t out[CS_N_SYM_FIBER_4D * CS_N_SQUARES_4D])
{
    assert(pos != NULL);
    assert(sig != NULL);
    assert(out != NULL);
    assert(CS_N_SYM_FIBER_4D == 3);

    /* int64 accumulator (3 × 4096 × 8 = 96 KB stack). See module
     * header for overflow envelope justification. */
    static int64_t fc_all[CS_N_SYM_FIBER_4D][CS_N_SQUARES_4D];
    memset(fc_all, 0, sizeof(fc_all));

    /* Outer per-square loop (ascending sq order matches Python). */
    for (int s = 0; s < CS_N_SQUARES_4D; s++) {
        const int8_t pc = pos->sq[s];
        if (pc == 0) {
            continue;
        }
        const int pidx = cs_fiber_row_4d(pc);
        if (pidx < 0) {
            continue;  /* pawn: handled in FA channels */
        }
        /* Skip pieces structurally dropped from the SVD basis (rook). */
        if ((CS_FIBER_DROPPED_MASK & (1u << (unsigned)pidx)) != 0u) {
            continue;
        }
        pp_fiber_sym_one_piece(s, pidx, sig, fc_all);
    }

    /* Cast int64 accumulator to int32 output. */
    for (int d = 0; d < CS_N_SYM_FIBER_4D; d++) {
        int32_t *out_d = out + d * CS_N_SQUARES_4D;
        for (int k = 0; k < CS_N_SQUARES_4D; k++) {
            out_d[k] = (int32_t)fc_all[d][k];
        }
    }
}
