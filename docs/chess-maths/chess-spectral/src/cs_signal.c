/* cs_signal.c — 64-dim board signal from piece list. */
#include <string.h>
#include "cs_encoder.h"

void cs_board_signal(const cs_position_t *pos,
                     const double vals[6],
                     double sig[64])
{
    memset(sig, 0, 64 * sizeof(double));
    for (int i = 0; i < pos->count; i++) {
        int s = pos->square[i];
        int t = pos->type[i];
        int c = pos->color[i];
        sig[s] = vals[t] * (double)c;
    }
}
