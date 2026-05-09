/* Pure-phase int16 board-signal builder (1.18.0+).
 *
 * Mirror of cs_board_signal_4d but emitting int16 with the
 * piece-value table pre-scaled by CS_VALS_INT_SCALE_4D=4. The bishop
 * value 3.25 thus becomes integer 13 (scaled), and all other piece
 * values fit comfortably in int16 with margin (max |value| = K = 48).
 *
 * JPL discipline:
 *   - Single fixed-bound loop over 4096 squares.
 *   - Two pre-condition assertions on pointer args.
 *   - All variable scope minimized.
 *   - No dynamic allocation.
 */
#include <assert.h>
#include "cs_encoder_pure_phase_4d.h"

void cs_board_signal_pure_phase_4d(
    const cs_position_4d_t *pos,
    int16_t sig[CS_N_SQUARES_4D])
{
    assert(pos != NULL);
    assert(sig != NULL);

    for (int s = 0; s < CS_N_SQUARES_4D; s++) {
        const int8_t pc = pos->sq[s];
        const int row = cs_piece_row_4d(pc);
        if (row < 0) {
            sig[s] = 0;
        } else {
            const int16_t mag = SIGNED_VALS_INT_4D[row];
            sig[s] = (pc >= 'a') ? (int16_t)(-mag) : mag;
        }
    }
}
