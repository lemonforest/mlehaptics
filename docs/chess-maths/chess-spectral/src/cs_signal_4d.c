/* 4D board-signal construction.
 *
 * Mirrors encoder_4d.board_signal_4d (Python) — walks the 4096-entry
 * sq[] array, looks up the signed piece value, and writes it to sig[s].
 * Empty squares zero. Identical iteration order to Python (ascending s).
 */
#include <string.h>
#include "cs_encoder_4d.h"

void cs_board_signal_4d(const cs_position_4d_t *pos,
                        double sig[CS_N_SQUARES_4D]) {
    /* Zero-fill first; most squares will be empty in any realistic
     * 4D position (even the 12-piece starting_like_mini fixture leaves
     * 4084 of 4096 untouched). */
    memset(sig, 0, sizeof(double) * CS_N_SQUARES_4D);
    for (int s = 0; s < CS_N_SQUARES_4D; s++) {
        int8_t pc = pos->sq[s];
        if (pc == 0) continue;
        sig[s] = cs_piece_value_4d(pc);
    }
}
