#ifndef CS_FEN_4D_H
#define CS_FEN_4D_H

#include "cs_types_4d.h"

#ifdef __cplusplus
extern "C" {
#endif

/* FEN4 v1 parser — see docs/FEN4_FORMAT.md for the full grammar.
 *
 * Format summary:
 *   "4d-fen v1: <piece-spec>@<x>,<y>,<z>,<w>; <piece-spec>@... ;"
 * where <piece-spec> is one of {N,B,R,Q,K, n,b,r,q,k, Pw,Py, pw,py}
 * and (x,y,z,w) are integers in [0,7]. Whitespace between tokens is
 * permitted; whitespace inside coords or piece specs is not.
 *
 * Returns 0 on success, nonzero on parse error. On error, *pos has
 * undefined contents. The parser fully zeros pos before populating it,
 * so an empty FEN4 string ("4d-fen v1:") yields an empty board.
 *
 * Error codes (negative; magnitudes carry no semantic meaning beyond
 * "this kind of error occurred", but are stable across versions for
 * test assertions):
 *
 *   -1  null argument
 *   -2  missing or wrong "4d-fen v1:" prefix
 *   -3  malformed piece spec (unknown letter, missing axis on pawn,
 *       missing '@', etc.)
 *   -4  malformed coord (non-digit, wrong separator count, out of [0,7])
 *   -5  duplicate square (two pieces declared at the same (x,y,z,w))
 *   -6  trailing garbage after the piece list
 */
int cs_fen_4d_parse(const char *fen4, cs_position_4d_t *pos);

#ifdef __cplusplus
}
#endif

#endif /* CS_FEN_4D_H */
