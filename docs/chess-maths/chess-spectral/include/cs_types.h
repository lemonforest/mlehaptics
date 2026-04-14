#ifndef CS_TYPES_H
#define CS_TYPES_H

#include <stdint.h>
#include <stddef.h>
#include "cs_tables.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    CS_PAWN   = 0,
    CS_KNIGHT = 1,
    CS_BISHOP = 2,
    CS_ROOK   = 3,
    CS_QUEEN  = 4,
    CS_KING   = 5
} cs_piece_t;

#define CS_MAX_PIECES 32

/* Chess position as a piece list. Color: +1 white, -1 black. */
typedef struct {
    uint8_t    square[CS_MAX_PIECES];   /* 0..63 */
    uint8_t    type  [CS_MAX_PIECES];   /* cs_piece_t */
    int8_t     color[CS_MAX_PIECES];    /* +1 / -1 */
    int        count;                   /* 0..CS_MAX_PIECES */
} cs_position_t;

/* Flat 640-dim encoding. */
typedef struct {
    double v[CS_ENCODING_DIM];
} cs_encoding_t;

#ifdef __cplusplus
}
#endif

#endif /* CS_TYPES_H */
