/* cs_temporal.c — coprime roll binding for 640-dim HDC.
 *
 * COPRIME_ROW=67, COPRIME_COL=7, COPRIME_TIME=131 are all coprime to
 * 640 = 2^7 * 5, so each is a generator of Z_640 under addition.
 */
#include "cs_temporal.h"

_Static_assert(CS_ENCODING_DIM == 640, "CS_ENCODING_DIM must be 640");
_Static_assert((CS_COPRIME_ROW  % 2 != 0) && (CS_COPRIME_ROW  % 5 != 0),
               "COPRIME_ROW must be coprime to 640");
_Static_assert((CS_COPRIME_COL  % 2 != 0) && (CS_COPRIME_COL  % 5 != 0),
               "COPRIME_COL must be coprime to 640");
_Static_assert((CS_COPRIME_TIME % 2 != 0) && (CS_COPRIME_TIME % 5 != 0),
               "COPRIME_TIME must be coprime to 640");

void cs_roll_640(const double in[CS_ENCODING_DIM],
                 int offset,
                 double out[CS_ENCODING_DIM])
{
    /* Normalize offset to [0, CS_ENCODING_DIM). C's % preserves sign for
     * negative operands, so we add the dim once to get a non-negative mod. */
    int o = offset % CS_ENCODING_DIM;
    if (o < 0) o += CS_ENCODING_DIM;

    /* out[(i+o) mod N] = in[i]   (left-rotation semantics matching numpy.roll
     * with shift = -offset; our convention: out rotates FORWARD by offset). */
    for (int i = 0; i < CS_ENCODING_DIM; i++) {
        int dst = (i + o);
        if (dst >= CS_ENCODING_DIM) dst -= CS_ENCODING_DIM;
        out[dst] = in[i];
    }
}
