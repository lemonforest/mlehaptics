/* Channels 5-7: cross-piece fiber-sym (rank-3 SVD basis).
 *
 * Mirrors encoder_4d.py channel-5-7 loop byte-for-byte:
 *
 *   sorted_items = sorted(pos4.items(), key=lambda kv: int(kv[0]))
 *   for d in 0..2:
 *       fc = np.zeros(4096, float64)
 *       for (s, pc) in sorted_items:
 *           pidx = _FIBER_IDX_4D[pc.upper()]        (skip pawn)
 *           cols = PIECE_ADJ[pidx].getrow(s).indices
 *           if cols.size == 0: continue
 *           gradient = float(sig[cols].sum())
 *           fib_d    = float(FIBER_LOCAL_4D[pidx, s, d])
 *           fc[cols] += gradient * fib_d
 *       out[d] = fc.astype(float32)
 *
 * Iteration order is load-bearing for 1e-10 parity: float64 vector
 * accumulation is non-associative, and Python's dict-insertion order
 * would diverge from C's ascending sq-index walk. The ascending walk
 * here matches sorted_items, and the CSR column indices are sorted by
 * construction (scipy.tocsr + A.maximum(A.T)), so gradient and fc
 * updates both see targets in ascending order.
 *
 * Rook is dropped (CS_FIBER_DROPPED_MASK == 0x04). The dropped rows of
 * FIBER_LOCAL_4D are zero, so the rook contribution would be zero
 * regardless, but the early-continue skips a pointless full-row walk.
 */
#include <string.h>
#include "cs_encoder_4d.h"
#include "cs_fiber_tables_4d.h"
#include "cs_tables_4d.h"
#include "cs_types_4d.h"

/* Dispatch adjacency by fiber-piece index. Keeps the inner loop free of
 * per-square pointer-indirection while still sharing one code path. */
static inline const int32_t *adj_indptr_for(int pidx)
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

static inline const int32_t *adj_indices_for(int pidx)
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

void cs_channels_fiber_sym_4d(const cs_position_4d_t *pos,
                              const double sig[CS_N_SQUARES_4D],
                              float out[CS_N_SYM_FIBER_4D * CS_N_SQUARES_4D]) {
    double fc[CS_N_SQUARES_4D];

    for (int d = 0; d < CS_N_SYM_FIBER_4D; d++) {
        memset(fc, 0, sizeof(fc));

        for (int s = 0; s < CS_N_SQUARES_4D; s++) {
            int8_t pc = pos->sq[s];
            if (pc == 0) continue;
            int pidx = cs_fiber_row_4d(pc);
            if (pidx < 0) continue;  /* pawn: handled in channel 8 */
            if (CS_FIBER_DROPPED_MASK & (1u << pidx)) continue;

            const int32_t *indptr  = adj_indptr_for(pidx);
            const int32_t *indices = adj_indices_for(pidx);
            int32_t start = indptr[s];
            int32_t end   = indptr[s + 1];
            if (start == end) continue;  /* isolated square - no neighbors */

            /* gradient = sig[cols].sum() - float64 sum in ascending
             * index order, matching np.sum over the sorted CSR row. */
            double gradient = 0.0;
            for (int32_t i = start; i < end; i++) {
                gradient += sig[indices[i]];
            }

            double fib_d = (double)FIBER_LOCAL_4D[pidx][s][d];
            double scale = gradient * fib_d;
            for (int32_t i = start; i < end; i++) {
                fc[indices[i]] += scale;
            }
        }

        float *out_d = out + d * CS_N_SQUARES_4D;
        for (int k = 0; k < CS_N_SQUARES_4D; k++) {
            out_d[k] = (float)fc[k];
        }
    }
}
