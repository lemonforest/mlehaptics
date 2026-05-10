/* Pure-phase 2D spectral encoder public API (1.19.0+).
 *
 * C port of chess_spectral.encoder_pure_phase.encode_2d_pure_phase.
 * Computes the 10-channel × 64-cell encoding using integer arithmetic
 * throughout (int8 / int16 / int32 / int64 accumulators; no float in
 * the hot path).
 *
 * JPL coding standards (Power of Ten):
 *   - All loops bounded (CS_BOARD_DIM = 64, etc.).
 *   - No dynamic memory allocation (caller-provided buffer).
 *   - Functions <= 60 lines.
 *   - >= 2 assertions per function.
 *   - Restricted variable scope.
 *   - Return values checked.
 *   - No goto, no recursion, no function pointers.
 *   - Preprocessor limited to header guards + table dimensions.
 *
 * Output layout matches CHANNELS in chess_spectral.encoder:
 *   [  0: 64]  A_1                                   int32
 *   [ 64:128]  A_2                                   int32
 *   [128:192]  B_1                                   int32
 *   [192:256]  B_2                                   int32
 *   [256:320]  E                                     int32
 *   [320:384]  F1 symmetric fiber d=0                int32
 *   [384:448]  F2 symmetric fiber d=1                int32
 *   [448:512]  F3 symmetric fiber d=2                int32
 *   [512:576]  FA antisymmetric pawn fiber           int32
 *   [576:640]  FD diagonal deviation                 int32
 *
 * Each channel block carries its own dequantization scale in
 * CHANNEL_DEQUANT_SCALES_2D (see cs_pure_phase_tables_2d.h). Multiply
 * an int32 channel value by its scale to recover the float64 result
 * comparable to encode_640(pos, vals=VALS).
 */
#ifndef CS_ENCODER_PURE_PHASE_2D_H
#define CS_ENCODER_PURE_PHASE_2D_H

#include <stdint.h>
#include "cs_types.h"
#include "cs_tables.h"
#include "cs_pure_phase_tables_2d.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Pure-phase 2D encoding: 10 channels × 64 cells = 640 int32. */
typedef struct {
    int32_t v[CS_PURE_PHASE_DIM_2D];
} cs_pure_phase_encoding_2d_t;

_Static_assert(sizeof(((cs_pure_phase_encoding_2d_t *)0)->v)
               == CS_PURE_PHASE_DIM_2D * sizeof(int32_t),
               "pure-phase 2D encoding must be 640 int32s");

/* Position dict for the 2D pure-phase encoder. ``sq[s]`` is the
 * piece char ('P','N','B','R','Q','K' white; 'p','n','b','r','q','k'
 * black) at square s, or 0 (NUL) for an empty square. Mirrors the
 * cs_position_4d_t shape for marshalling consistency, but the 2D
 * encoder does not need a pawn-axis array. */
typedef struct {
    int8_t sq[CS_BOARD_DIM];
} cs_pure_phase_position_2d_t;

/* Build the 64-square scaled-integer signal from a position.
 *
 * sig[s] = +SIGNED_VALS_INT_2D[piece_idx]   if sq[s] is a white piece char
 *          -SIGNED_VALS_INT_2D[piece_idx]   if sq[s] is a black piece char
 *          0                                 if sq[s] == 0 (empty)
 *
 * Output is int16: piece values scaled by CS_VALS_INT_SCALE_2D=2,
 * so K becomes 200; well within int16 range. */
void cs_board_signal_pure_phase_2d(
    const cs_pure_phase_position_2d_t *pos,
    int16_t sig[CS_BOARD_DIM]);

/* Channels 0-4: pure-integer D₄ irrep projections.
 *
 * For each irrep mu (A1, A2, B1, B2, E):
 *   out[s] = sum_g CHARS[mu][g] * sig[D4_PERMS[g][s]]
 *
 * The dim_mu/8/_VALS_INT_SCALE factor is absorbed in
 * CHANNEL_DEQUANT_SCALES_2D[*]. CHARS values are ±1, ±2, 0 — already
 * integer — so no scale-by-LCM trick is needed (unlike 4D's A1 orbit
 * sum which requires 384/orbit_size). out: 5 × 64 int32. */
void cs_channels_pure_phase_d4_irreps_2d(
    const int16_t sig[CS_BOARD_DIM],
    int32_t out[CS_NUM_IRREPS * CS_BOARD_DIM]);

/* Channels 5-7: fiber-symmetric (int, 3 channels via loop-swap +
 * broadcast). For each occupied non-pawn square s with fiber-piece p:
 *   gradient = sum_t LOCAL_ADJ_ROWS_INT8[p][s][t] * sig[t]
 *   for d in 0..2:
 *     out[d, t] += gradient * LOCAL_FIBER_3D_INT16[p, s, d]
 *                                  * LOCAL_ADJ_ROWS_INT8[p][s][t]
 * out: 3 × 64 int32. */
void cs_channels_pure_phase_fiber_sym_2d(
    const cs_pure_phase_position_2d_t *pos,
    const int16_t sig[CS_BOARD_DIM],
    int32_t out[CS_NUM_SYM_FIBER * CS_BOARD_DIM]);

/* Channel 8: FA pawn antisymmetric (int).
 *   For each pawn at s (any color):
 *     out[k] += sign * SIGNED_VALS_INT_2D[P or p] / sign-only
 *               * PAWN_ANTI_FIBER_INT16[s, k]
 * (Implementation uses signed pawn weight directly; the
 * _VALS_INT_SCALE factor is absorbed in CHANNEL_DEQUANT_SCALES_2D[FA].)
 * out: 64 int32. */
void cs_channel_pure_phase_fa_2d(
    const cs_pure_phase_position_2d_t *pos,
    int32_t out[CS_BOARD_DIM]);

/* Channel 9: FD diagonal deviation (int, group-by-piece-type).
 *   coef[piece_row] = sum over occupied s with piece_row(s)==row of sig[s]
 *   out[k] = sum over piece_row of coef[piece_row] * DIAG_DEV_INT16_2D[row][k]
 * out: 64 int32. */
void cs_channel_pure_phase_diag_2d(
    const cs_pure_phase_position_2d_t *pos,
    const int16_t sig[CS_BOARD_DIM],
    int32_t out[CS_BOARD_DIM]);

/* Full 10-channel × 640-int32 pure-phase 2D encoder.
 * Bit-exact parity target (post-dequant) for Python's
 * encode_2d_pure_phase. */
void cs_encode_pure_phase_2d(
    const cs_pure_phase_position_2d_t *pos,
    cs_pure_phase_encoding_2d_t *enc);

#ifdef __cplusplus
}
#endif

#endif /* CS_ENCODER_PURE_PHASE_2D_H */
