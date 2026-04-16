/* cs_fen.c — minimal FEN piece-placement parser.
 * Convention: row 0 = rank 8 (matching encoder_512.py).
 * Only the placement field is parsed; castling/en-passant/clocks are ignored.
 */
#include <string.h>
#include <stdio.h>
#include "cs_types.h"

/* Returns 0 on success, nonzero on error. */
int cs_fen_parse(const char *fen, cs_position_t *pos)
{
    memset(pos, 0, sizeof(*pos));
    if (!fen || !pos) return -1;

    int row = 0, col = 0, count = 0;
    const char *p = fen;
    while (*p && *p != ' ') {
        char c = *p++;
        if (c == '/') {
            if (col != 8) return -2;
            row++;
            col = 0;
            if (row > 7) break;
            continue;
        }
        if (c >= '1' && c <= '8') {
            col += (c - '0');
            if (col > 8) return -3;
            continue;
        }
        /* Piece char. */
        int color = (c >= 'A' && c <= 'Z') ? +1 : -1;
        char u = (color > 0) ? c : (char)(c - 32);
        int type;
        switch (u) {
            case 'P': type = CS_PAWN;   break;
            case 'N': type = CS_KNIGHT; break;
            case 'B': type = CS_BISHOP; break;
            case 'R': type = CS_ROOK;   break;
            case 'Q': type = CS_QUEEN;  break;
            case 'K': type = CS_KING;   break;
            default:  return -4;
        }
        if (count >= CS_MAX_PIECES) return -5;
        pos->square[count] = (uint8_t)(row * 8 + col);
        pos->type[count]   = (uint8_t)type;
        pos->color[count]  = (int8_t)color;
        count++;
        col++;
        if (col > 8) return -6;
    }
    if (row != 7 || col != 8) return -7;
    pos->count = count;
    return 0;
}
