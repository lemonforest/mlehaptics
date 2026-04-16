#ifndef CS_TEMPORAL_H
#define CS_TEMPORAL_H

#include "cs_tables.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Coprime roll in 640-space. For offset o, out[(i+o) mod 640] = in[i].
 * Negative offsets supported; the effective offset is taken mod 640. */
void cs_roll_640(const double in[CS_ENCODING_DIM],
                 int offset,
                 double out[CS_ENCODING_DIM]);

/* Spatial binding offset for a (row, col) location: row*67 + col*7. */
static inline int cs_spatial_offset(int row, int col) {
    return (row * CS_COPRIME_ROW + col * CS_COPRIME_COL);
}

/* Temporal binding offset for ply t: t*131. */
static inline int cs_temporal_offset(int ply) {
    return ply * CS_COPRIME_TIME;
}

#ifdef __cplusplus
}
#endif

#endif /* CS_TEMPORAL_H */
