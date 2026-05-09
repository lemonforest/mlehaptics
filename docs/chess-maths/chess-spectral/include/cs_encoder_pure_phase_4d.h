/* Pure-phase 4D spectral encoder public API (1.18.0+).
 *
 * C port of chess_spectral.encoder_pure_phase_4d.encode_4d_pure_phase.
 * Computes the 11-channel × 4096-cell encoding using integer arithmetic
 * throughout (int8 / int16 / int32; no float in the hot path).
 *
 * JPL coding standards (Power of Ten):
 *   - All loops bounded (CS_N_SQUARES_4D = 4096 max for any inner loop).
 *   - No dynamic memory allocation (caller-provided buffers).
 *   - Functions <= 60 lines.
 *   - >= 2 assertions per function.
 *   - Restricted variable scope.
 *   - Return values checked.
 *   - No goto, no recursion, no function pointers.
 *   - Preprocessor limited to header guards + table dimensions.
 *
 * Output layout matches CHANNELS_4D in chess_spectral.encoder_4d:
 *   [   0:4096]  A_1 orbit projection                  int32
 *   [4096:8192]  STD4_X coord-residual × signal        int32
 *   [8192:12288] STD4_Y coord-residual × signal        int32
 *   [12288:16384] STD4_Z                                int32
 *   [16384:20480] STD4_W                                int32
 *   [20480:24576] FIB_SYM_1                             int32
 *   [24576:28672] FIB_SYM_2                             int32
 *   [28672:32768] FIB_SYM_3                             int32
 *   [32768:36864] FA_PAWN_W                             int32
 *   [36864:40960] FA_PAWN_Y                             int32
 *   [40960:45056] FD_DIAG                               int32
 *
 * Each channel block carries its own dequantization scale in
 * CHANNEL_DEQUANT_SCALES_4D (see cs_pure_phase_tables_4d.h). Multiply
 * an int32 channel value by its scale to recover the float64 result
 * comparable to encode_4d(pos, vals=PIECE_VALUES_4D).
 */
#ifndef CS_ENCODER_PURE_PHASE_4D_H
#define CS_ENCODER_PURE_PHASE_4D_H

#include <stdint.h>
#include "cs_types_4d.h"
#include "cs_pure_phase_tables_4d.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Pure-phase 4D encoding: 11 channels × 4096 cells = 45 056 int32. */
typedef struct {
    int32_t v[CS_ENCODING_DIM_4D];
} cs_pure_phase_encoding_4d_t;

_Static_assert(sizeof(((cs_pure_phase_encoding_4d_t *)0)->v)
               == CS_ENCODING_DIM_4D * sizeof(int32_t),
               "pure-phase encoding must be CS_ENCODING_DIM_4D int32s");

/* Build the 4096-square scaled-integer signal from a position.
 *
 * sig[s] = +SIGNED_VALS_INT_4D[type]  if sq[s] is a white piece char
 *          -SIGNED_VALS_INT_4D[type]  if sq[s] is a black piece char
 *          0                          if sq[s] == 0 (empty)
 *
 * Output is int16 because the signal values are scaled by
 * CS_VALS_INT_SCALE_4D=4 (so K becomes 48; well within int16). */
void cs_board_signal_pure_phase_4d(
    const cs_position_4d_t *pos,
    int16_t sig[CS_N_SQUARES_4D]);

/* Channel 0: A_1 orbit-sum projection (integer).
 *   out[s] = ORBIT_INT_SCALE[ORBIT_OF[s]] × sum_{t in orbit(s)} sig[t]
 * The (1/384) factor is absorbed in CHANNEL_DEQUANT_SCALES_4D[A1].
 * out: 4096 int32. */
void cs_channel_pure_phase_a1_4d(
    const int16_t sig[CS_N_SQUARES_4D],
    int32_t out[CS_N_SQUARES_4D]);

/* Channels 1-4: STD4 coord-residual channels (int).
 *   out_d[s] = COORD_RESID_INT8[d][s] × sig[s]   (d in 0..3)
 * out: 4×4096 int32. */
void cs_channels_pure_phase_std4_4d(
    const int16_t sig[CS_N_SQUARES_4D],
    int32_t out[CS_N_DIMS * CS_N_SQUARES_4D]);

/* Channels 5-7: fiber-symmetric (int, 3 channels via loop-swap +
 * broadcast). For each occupied non-pawn square s:
 *   gradient = sum over t in adj(s) of sig[t]
 *   for d in 0..2: out[d, adj(s)] += gradient × FIBER_LOCAL_INT16[p, s, d]
 * out: 3×4096 int32. */
void cs_channels_pure_phase_fiber_sym_4d(
    const cs_position_4d_t *pos,
    const int16_t sig[CS_N_SQUARES_4D],
    int32_t out[CS_N_SYM_FIBER_4D * CS_N_SQUARES_4D]);

/* Channel 8: FA_PAWN_W (W-axis pawn antisymmetric, int).
 *   For each W-axis pawn at s = (sx, sy, sz, sw):
 *     out[(sx, sy, sz, *)] += sign × W_ANTI_DCT_INT16[sw, *]
 * out: 4096 int32. */
void cs_channel_pure_phase_fa_pawn_w_4d(
    const cs_position_4d_t *pos,
    int32_t out[CS_N_SQUARES_4D]);

/* Channel 9: FA_PAWN_Y (Y-axis pawn antisymmetric, int).
 *   For each Y-axis pawn at s = (sx, sy, sz, sw):
 *     out[(sx, *, sz, sw)] += sign × Y_ANTI_DCT_INT16[sy, *]   (stride 64)
 * out: 4096 int32. */
void cs_channel_pure_phase_fa_pawn_y_4d(
    const cs_position_4d_t *pos,
    int32_t out[CS_N_SQUARES_4D]);

/* Channel 10: FD_DIAG diagonal deviation (int, group-by-piece-type).
 *   coef[piece_row] = sum over occupied s of piece_row(s)==row of sig[s]
 *   out[k] = sum over piece_row of coef[piece_row] × DIAG_DEV_INT16_4D[row, k]
 * out: 4096 int32. */
void cs_channel_pure_phase_diag_4d(
    const cs_position_4d_t *pos,
    const int16_t sig[CS_N_SQUARES_4D],
    int32_t out[CS_N_SQUARES_4D]);

/* Full 11-channel × 45 056-int32 pure-phase encoder.
 * Bit-exact parity target (post-dequant) for Python's
 * encode_4d_pure_phase. */
void cs_encode_pure_phase_4d(
    const cs_position_4d_t *pos,
    cs_pure_phase_encoding_4d_t *enc);

#ifdef __cplusplus
}
#endif

#endif /* CS_ENCODER_PURE_PHASE_4D_H */
