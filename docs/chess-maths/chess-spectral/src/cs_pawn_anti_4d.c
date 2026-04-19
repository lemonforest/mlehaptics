/* Channels 8-9 (v1.1.1): pawn antisymmetric fibers, per axis.
 *
 * v1.0 layout had a single channel 8 (FA_PAWN) carrying the w-axis
 * antisymmetric fiber. v1.1.1 splits this into two sub-channels per
 * Oana & Chiru Def. 11:
 *
 *   FA_PAWN_W (slot 8, legacy)   Kronecker form: I (x) I (x) I (x) A_w
 *     For each pawn with pawn_axis[s] == CS_PAWN_AXIS_W at
 *     s = (sx,sy,sz,sw):
 *       out[(sx,sy,sz,tw)] += sign * W_ANTI_DCT[sw, tw]   (tw in 0..7)
 *     Scatter pattern: 8 contiguous stride-1 writes.
 *
 *   FA_PAWN_Y (slot 9, new)      Kronecker form: I (x) A_y (x) I (x) I
 *     For each pawn with pawn_axis[s] == CS_PAWN_AXIS_Y at
 *     s = (sx,sy,sz,sw):
 *       out[(sx,ty,sz,sw)] += sign * Y_ANTI_DCT[sy, ty]   (ty in 0..7)
 *     Scatter pattern: 8 stride-64 writes at base | (ty << 6),
 *     where base clears the y-bits (6..8) of the pawn's square.
 *
 * Both routines skip pawns that don't match the channel's axis, so
 * v1.0 fixtures (where every pawn defaults to CS_PAWN_AXIS_W via the
 * struct zero-init) feed only FA_PAWN_W and leave FA_PAWN_Y all-zero;
 * this preserves byte-for-byte parity with the v1.0 W-only encoding
 * on the legacy fixture subset.
 *
 * Sign convention: 'P' -> +1, 'p' -> -1; non-pawn squares are skipped
 * unconditionally. Square-index layout (matches tables_4d.sq4):
 *   s = ((sx*8 + sy)*8 + sz)*8 + sw
 *   sw = s & 7  sz = (s>>3)&7  sy = (s>>6)&7  sx = (s>>9)&7
 */
#include <string.h>
#include "cs_encoder_4d.h"
#include "cs_fiber_tables_4d.h"
#include "cs_tables_4d.h"
#include "cs_types_4d.h"

void cs_channel_fa_pawn_w_4d(const cs_position_4d_t *pos,
                             float out[CS_N_SQUARES_4D]) {
    double pawn_ch[CS_N_SQUARES_4D];
    memset(pawn_ch, 0, sizeof(pawn_ch));

    for (int s = 0; s < CS_N_SQUARES_4D; s++) {
        int8_t pc = pos->sq[s];
        if (pc != 'P' && pc != 'p') continue;
        /* v1.1.1: route only W-axis pawns into this channel. Non-W
         * pawns (Y-axis per Def. 11) are handled by cs_channel_fa_pawn_y_4d.
         * pos->pawn_axis[s] defaults to CS_PAWN_AXIS_W (0) via the struct
         * zero-init, so v1.0 callers with no axis wiring still route all
         * pawns here, preserving exact v1.0 numerics. */
        if (pos->pawn_axis[s] != CS_PAWN_AXIS_W) continue;

        double sign = (pc == 'P') ? 1.0 : -1.0;
        int sw   = s & 7;
        int base = s & ~7;  /* zero the low 3 bits -- (sx,sy,sz,0) */
        const double *row = W_ANTI_DCT[sw];
        for (int tw = 0; tw < 8; tw++) {
            pawn_ch[base + tw] += sign * row[tw];
        }
    }

    for (int k = 0; k < CS_N_SQUARES_4D; k++) {
        out[k] = (float)pawn_ch[k];
    }
}

void cs_channel_fa_pawn_y_4d(const cs_position_4d_t *pos,
                             float out[CS_N_SQUARES_4D]) {
    double pawn_ch[CS_N_SQUARES_4D];
    memset(pawn_ch, 0, sizeof(pawn_ch));

    /* y-axis mask covers bits 6..8 of the square index (see header
     * comment above for the sq4 layout). */
    const int Y_MASK = 7 << 6;  /* 0x1C0 */

    for (int s = 0; s < CS_N_SQUARES_4D; s++) {
        int8_t pc = pos->sq[s];
        if (pc != 'P' && pc != 'p') continue;
        if (pos->pawn_axis[s] != CS_PAWN_AXIS_Y) continue;

        double sign = (pc == 'P') ? 1.0 : -1.0;
        int sy   = (s >> 6) & 7;
        int base = s & ~Y_MASK;  /* (sx, 0, sz, sw) */
        const double *row = Y_ANTI_DCT[sy];
        for (int ty = 0; ty < 8; ty++) {
            pawn_ch[base | (ty << 6)] += sign * row[ty];
        }
    }

    for (int k = 0; k < CS_N_SQUARES_4D; k++) {
        out[k] = (float)pawn_ch[k];
    }
}
