#ifndef CS_ENCODER_4D_H
#define CS_ENCODER_4D_H

#include "cs_types_4d.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Build the 4096-square signed-value signal from a position.
 *
 * sig[s] = +PIECE_VALUES_4D[type]  if sq[s] is a white piece char
 *          -PIECE_VALUES_4D[type]  if sq[s] is a black piece char
 *          0                       if sq[s] == 0 (empty)
 *
 * Output is double (not float) because the reference Python carries
 * the signal in float64 all the way up to the final float32 cast at
 * channel-write time.
 */
void cs_board_signal_4d(const cs_position_4d_t *pos,
                        double sig[CS_N_SQUARES_4D]);

/* Channel 0: A_1 orbit averaging.
 *   out[s] = (1/|orbit(s)|) * sum over t in orbit(s) of sig[t]
 * Implemented in P2b via ORBIT_OF / ORBIT_MEMBERS / ORBIT_INV_SIZE.
 */
void cs_channel_a1_4d(const double sig[CS_N_SQUARES_4D],
                      float out[CS_N_SQUARES_4D]);

/* Channels 1-4: std-4D coordinate residual channels.
 *   out_d[s] = COORD_RESID[d][s] * sig[s]    (d in 0..3)
 * `out` points to the channel-1 start; four consecutive 4096-blocks are
 * written. Implemented in P2b.
 */
void cs_channels_std4_4d(const double sig[CS_N_SQUARES_4D],
                         float out[CS_N_DIMS * CS_N_SQUARES_4D]);

/* Channel 9: diagonal-deviation (rook shadow), DCT-mode space.
 *   out[k] = sum over occupied s of sig[s] * DIAG_DEV_4D[piece_row(s), k]
 * Implemented in P2b.
 */
void cs_channel_diag_4d(const cs_position_4d_t *pos,
                        const double sig[CS_N_SQUARES_4D],
                        float out[CS_N_SQUARES_4D]);

/* Channel 8: FA_PAWN_W -- pawn antisymmetric fiber along the w-axis.
 *   For each W-axis pawn at s = (sx,sy,sz,sw), write
 *     sign * W_ANTI_DCT[sw, 0..7] into the 8 modes sharing (sx,sy,sz)
 *   along w. Pawns with pawn_axis[s] != CS_PAWN_AXIS_W are skipped.
 */
void cs_channel_fa_pawn_w_4d(const cs_position_4d_t *pos,
                             float out[CS_N_SQUARES_4D]);

/* Channel 9 (v1.1.1): FA_PAWN_Y -- pawn antisymmetric fiber along the
 * y-axis. Symmetric structure to FA_PAWN_W but with the 8x8 factor
 * sitting on the y-tensor leg:
 *   out[(sx, ty, sz, sw)] += sign * Y_ANTI_DCT[sy, ty]   for ty in 0..7
 * Pawns with pawn_axis[s] != CS_PAWN_AXIS_Y are skipped.
 */
void cs_channel_fa_pawn_y_4d(const cs_position_4d_t *pos,
                             float out[CS_N_SQUARES_4D]);

/* Legacy alias: equivalent to cs_channel_fa_pawn_w_4d. Retained for
 * incremental migration; new code should call the axis-specific
 * entrypoints directly. */
static inline void cs_channel_pawn_antisym_4d(const cs_position_4d_t *pos,
                                              float out[CS_N_SQUARES_4D]) {
    cs_channel_fa_pawn_w_4d(pos, out);
}

/* Channels 5-7: cross-piece fiber-sym (P4).
 *   For each direction d in 0..2 and sorted-ascending occupied non-pawn
 *   square s: gradient = sig[adj(s)].sum();  fc[adj(s)] += grad * fib_d(p,s).
 *   `out` points to the channel-5 start; three consecutive 4096-blocks
 *   are written.
 */
void cs_channels_fiber_sym_4d(const cs_position_4d_t *pos,
                              const double sig[CS_N_SQUARES_4D],
                              float out[CS_N_SYM_FIBER_4D * CS_N_SQUARES_4D]);

/* Full 11-channel, 45 056-float32 encoder (v1.1.1). Byte-for-byte
 * parity target for Python's encode_4d (tolerance 1e-10 absolute
 * max-delta). */
void cs_encode_4d(const cs_position_4d_t *pos,
                  cs_encoding_4d_t *enc);

#ifdef __cplusplus
}
#endif

#endif /* CS_ENCODER_4D_H */
