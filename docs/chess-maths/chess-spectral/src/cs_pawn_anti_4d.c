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
 *     8 fp ops per pawn; zero contribution off the (sx,sy,sz,*) fiber.
 *
 *   FA_PAWN_Y (slot 9, new)      Kronecker form: I (x) A_y (x) I (x) I
 *     For each pawn with pawn_axis[s] == CS_PAWN_AXIS_Y at
 *     s = (sx,sy,sz,sw):
 *       out[(sx,ty,sz,sw)] += sign * Y_ANTI_DCT[sy, ty]   (ty in 0..7)
 *     Full impl lands in P6 -- this TU currently emits a zero-fill
 *     for FA_PAWN_Y so the header split compiles and cs_encode_4d
 *     writes well-defined bytes.
 *
 * Sign convention: 'P' -> +1, 'p' -> -1; non-pawn squares are skipped
 * unconditionally.
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
    /* P4 stub: zero-fill. Full Y-axis factored scatter lands in P6
     * along with Y_ANTI_DCT regeneration in P5. */
    (void)pos;
    memset(out, 0, CS_N_SQUARES_4D * sizeof(float));
}
