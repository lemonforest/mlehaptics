/* Pure-phase int16 board-signal builder for 2D (1.19.0+).
 *
 * Mirror of the Python _board_signal_int helper: emit int16 with the
 * piece-value table pre-scaled by CS_VALS_INT_SCALE_2D=2 so the
 * half-integer bishop value (3.5 in VALS) survives as integer 7.
 * King value 100 becomes 200; well within int16 range.
 *
 * JPL discipline:
 *   - Single fixed-bound loop over 64 squares.
 *   - Two pre-condition assertions on pointer args + invariant.
 *   - All variable scope minimized.
 *   - No dynamic allocation.
 */
#include <assert.h>
#include "cs_encoder_pure_phase_2d.h"

/* Map piece char ('P','N','B','R','Q','K','p','n','b','r','q','k')
 * to the SIGNED_VALS_INT_2D index (0..11). Returns -1 for empty
 * squares or unknown chars. The packed table layout matches the
 * codegen-emitted SIGNED_VALS_INT_2D[12]. */
static int piece_char_to_idx(int8_t pc)
{
    switch (pc) {
        case 'P': return 0;
        case 'N': return 1;
        case 'B': return 2;
        case 'R': return 3;
        case 'Q': return 4;
        case 'K': return 5;
        case 'p': return 6;
        case 'n': return 7;
        case 'b': return 8;
        case 'r': return 9;
        case 'q': return 10;
        case 'k': return 11;
        default:  return -1;
    }
}

void cs_board_signal_pure_phase_2d(
    const cs_pure_phase_position_2d_t *pos,
    int16_t sig[CS_BOARD_DIM])
{
    assert(pos != NULL);
    assert(sig != NULL);
    assert(CS_BOARD_DIM == 64);

    for (int s = 0; s < CS_BOARD_DIM; s++) {
        const int idx = piece_char_to_idx(pos->sq[s]);
        if (idx < 0) {
            sig[s] = 0;
        } else {
            sig[s] = SIGNED_VALS_INT_2D[idx];
        }
    }
}
