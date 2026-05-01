/* cs_fen_4d.c — FEN4 v1 parser. See docs/FEN4_FORMAT.md for the grammar.
 *
 * Style mirrors cs_fen.c: small, allocation-free, byte-by-byte walk
 * over the input. Errors are reported as small negative integers (see
 * include/cs_fen_4d.h). The parser writes a fully-populated
 * cs_position_4d_t on success; the caller does not need to memset.
 *
 * Parity contract: the Python parser in chess_spectral/fen_4d.py must
 * accept exactly the same set of inputs (and reject the same set), and
 * produce a position dict that round-trips to the same encoding bytes
 * as this parser via cs_encode_4d / encode_4d. Verified by
 * python/tests/test_fen4_parity.py.
 */
#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include "cs_fen_4d.h"

#define FEN4_PREFIX "4d-fen v1:"

static int is_ws(char c) {
    return c == ' ' || c == '\t' || c == '\n' || c == '\r';
}

static const char *skip_ws(const char *p) {
    while (*p && is_ws(*p)) p++;
    return p;
}

/* Parse a single "x,y,z,w" coord starting at *pp. On success, advances
 * *pp past the last digit and writes the four coords into out[0..3].
 * Returns 0 on success, -4 on any malformed coord (non-digit, wrong
 * separator count, value out of [0,7]).
 */
static int parse_coord(const char **pp, int out[4])
{
    const char *p = *pp;
    for (int i = 0; i < 4; i++) {
        if (*p < '0' || *p > '7') return -4;
        out[i] = *p - '0';
        p++;
        if (i < 3) {
            if (*p != ',') return -4;
            p++;
        }
    }
    *pp = p;
    return 0;
}

/* Parse a single piece spec starting at *pp. On success, advances *pp
 * past the spec and writes the piece char into *piece_out and the pawn
 * axis into *axis_out (CS_PAWN_AXIS_W for non-pawns; meaningful only
 * for pawns). Returns 0 on success, -3 on malformed spec.
 *
 * 1.7.1+: accepts an optional '/' separator between the pawn color
 * char and its axis letter — both "Pw@..." (canonical) and
 * "P/w@..." (slash-separated) parse to the same value. The Python
 * parser in chess_spectral/fen_4d.py mirrors this tolerance.
 */
static int parse_piece_spec(const char **pp,
                            int8_t *piece_out, uint8_t *axis_out)
{
    const char *p = *pp;
    char c = *p;
    *axis_out = CS_PAWN_AXIS_W;

    /* White / black pawns: must carry an axis suffix, optionally
     * preceded by '/'. */
    if (c == 'P' || c == 'p') {
        const char *axis_p = p + 1;
        if (*axis_p == '/') axis_p++;   /* tolerate "P/w" */
        char a = *axis_p;
        if (a == 'w') *axis_out = CS_PAWN_AXIS_W;
        else if (a == 'y') *axis_out = CS_PAWN_AXIS_Y;
        else return -3;
        *piece_out = (int8_t)c;
        *pp = axis_p + 1;
        return 0;
    }

    /* Non-pawn pieces: one char, must be NBRQK / nbrqk. */
    switch (c) {
        case 'N': case 'B': case 'R': case 'Q': case 'K':
        case 'n': case 'b': case 'r': case 'q': case 'k':
            *piece_out = (int8_t)c;
            *pp = p + 1;
            return 0;
        default:
            return -3;
    }
}

int cs_fen_4d_parse(const char *fen4, cs_position_4d_t *pos)
{
    if (!fen4 || !pos) return -1;

    /* Zero the whole struct; this gives an empty board with all
     * pawn_axis bytes set to CS_PAWN_AXIS_W (0). */
    memset(pos, 0, sizeof(*pos));

    /* Match "4d-fen v1:" — case-sensitive, exact. */
    const size_t pref_len = sizeof(FEN4_PREFIX) - 1;
    /* Allow leading whitespace. */
    const char *p = skip_ws(fen4);
    if (strncmp(p, FEN4_PREFIX, pref_len) != 0) return -2;
    p += pref_len;

    /* Empty body → empty board. Walk past trailing whitespace and
     * confirm we hit the end of input. */
    p = skip_ws(p);
    if (*p == '\0') return 0;

    /* Loop over piece records. Each record:
     *   <piece-spec> '@' <coord>
     * separated by ';' (with optional surrounding whitespace).
     */
    for (;;) {
        int8_t piece;
        uint8_t axis;
        int rc = parse_piece_spec(&p, &piece, &axis);
        if (rc != 0) return rc;

        /* '@' separator (whitespace allowed on both sides). */
        p = skip_ws(p);
        if (*p != '@') return -3;
        p++;
        p = skip_ws(p);

        int xyzw[4];
        rc = parse_coord(&p, xyzw);
        if (rc != 0) return rc;

        long s = (((long)xyzw[0] * 8 + xyzw[1]) * 8 + xyzw[2]) * 8 + xyzw[3];
        if (s < 0 || s >= CS_N_SQUARES_4D) return -4;
        if (pos->sq[s] != 0) return -5;  /* duplicate */
        pos->sq[s] = piece;
        pos->pawn_axis[s] = axis;

        /* End of input or ';' separator. */
        p = skip_ws(p);
        if (*p == '\0') return 0;
        if (*p != ';') return -6;
        p++;
        p = skip_ws(p);
        if (*p == '\0') return 0;  /* trailing ';' is fine */
    }
}
