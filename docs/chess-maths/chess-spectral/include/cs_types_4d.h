#ifndef CS_TYPES_4D_H
#define CS_TYPES_4D_H

#include <stdint.h>
#include <stddef.h>
#include "cs_tables_4d.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Pawn axis labels (v1.1.1, Oana & Chiru Def. 11).
 *   CS_PAWN_AXIS_W = 0 -- pawn advances along the w-axis (v1.0 default)
 *   CS_PAWN_AXIS_Y = 1 -- pawn advances along the y-axis
 * Non-pawn squares carry CS_PAWN_AXIS_W (0) by convention and are
 * ignored when the pawn-axis channels walk the position. */
#define CS_PAWN_AXIS_W 0
#define CS_PAWN_AXIS_Y 1

/* 4D chess position.
 *
 * Square index s encodes (x,y,z,w) as ((x*8+y)*8+z)*8+w, i.e.
 *   s = (x<<9) | (y<<6) | (z<<3) | w    (0 <= x,y,z,w < 8)
 * matching tables_4d.sq4 / rc4 in the Python reference.
 *
 * sq[s] stores the piece ASCII char at square s, or 0 for empty.
 * Uppercase = white {P,N,B,R,Q,K}; lowercase = black {p,n,b,r,q,k}.
 * int8_t is ample: all piece chars fit in 7 bits.
 *
 * pawn_axis[s] carries the v1.1.1 axis label per Oana & Chiru Def. 11:
 *   CS_PAWN_AXIS_W (0)  -- w-axis pawn  (legacy default; safe for
 *                                        non-pawn squares too)
 *   CS_PAWN_AXIS_Y (1)  -- y-axis pawn
 * Only meaningful when sq[s] is 'P' or 'p'. Because memset-to-zero
 * produces a valid W-axis default for every square, callers that are
 * still on the v1.0 single-axis schema remain correct without code
 * changes.
 */
typedef struct {
    int8_t  sq[CS_N_SQUARES_4D];
    uint8_t pawn_axis[CS_N_SQUARES_4D];
} cs_position_4d_t;

/* Flat 45 056-dim float32 encoding (v1.1.1; up from 40 960 in v1.0).
 *
 * Float32 (not double) because:
 *   (a) the Python reference explicitly stores encoder output as
 *       np.float32 -- parity target is float32;
 *   (b) the spectralz v4 frame format stores each ply as 45 056 float32
 *       (180 224 B/ply), matching the on-disk representation.
 */
typedef struct {
    float v[CS_ENCODING_DIM_4D];
} cs_encoding_4d_t;

_Static_assert(sizeof(((cs_position_4d_t*)0)->pawn_axis)
               == CS_N_SQUARES_4D,
               "pawn_axis[] must cover every square");

/* Map a piece ASCII char to the 6-piece cs_piece_4d_t enum row used by
 * DIAG_DEV_4D. Returns -1 for 0 / empty / unknown chars.
 *
 * Defined here (header-inline) rather than as a function to avoid a
 * cross-TU branch for what is effectively a tiny switch.
 */
static inline int cs_piece_row_4d(int8_t pc) {
    switch (pc) {
        case 'P': case 'p': return CS_PIECE_4D_P;
        case 'N': case 'n': return CS_PIECE_4D_N;
        case 'B': case 'b': return CS_PIECE_4D_B;
        case 'R': case 'r': return CS_PIECE_4D_R;
        case 'Q': case 'q': return CS_PIECE_4D_Q;
        case 'K': case 'k': return CS_PIECE_4D_K;
        default:            return -1;
    }
}

/* Map a piece ASCII char to the 5-piece cs_fiber_piece_4d_t enum row
 * used by FIBER_LOCAL_4D (wired in P4). Pawns return -1 since they are
 * handled in the antisymmetric channel (8), not the fiber-sym channels.
 */
static inline int cs_fiber_row_4d(int8_t pc) {
    switch (pc) {
        case 'N': case 'n': return CS_FIBER_PIECE_4D_N;
        case 'B': case 'b': return CS_FIBER_PIECE_4D_B;
        case 'R': case 'r': return CS_FIBER_PIECE_4D_R;
        case 'Q': case 'q': return CS_FIBER_PIECE_4D_Q;
        case 'K': case 'k': return CS_FIBER_PIECE_4D_K;
        default:            return -1;
    }
}

/* Signed piece-value lookup for board_signal. Uppercase -> +PIECE_VALUES_4D,
 * lowercase -> -PIECE_VALUES_4D. Empty squares / unknown chars -> 0. */
static inline double cs_piece_value_4d(int8_t pc) {
    int row = cs_piece_row_4d(pc);
    if (row < 0) return 0.0;
    double v = PIECE_VALUES_4D[row];
    return (pc >= 'a') ? -v : v;
}

#ifdef __cplusplus
}
#endif

#endif /* CS_TYPES_4D_H */
