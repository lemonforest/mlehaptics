#ifndef CS_ENCODER_H
#define CS_ENCODER_H

#include "cs_types.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Core primitives (exposed for unit tests). */

/* sig[64] = vals[type_of_square] * color_of_square, zero elsewhere. */
void cs_board_signal(const cs_position_t *pos,
                     const double vals[6],
                     double sig[64]);

/* Project signal onto D4 irrep μ via Serre's character formula.
 * irrep_idx: 0=A1, 1=A2, 2=B1, 3=B2, 4=E. out[64]. */
void cs_project_irrep(const double sig[64], int irrep_idx, double out[64]);

/* Channels 5-7 (symmetric 3D fiber), one channel-dim at a time (d=0..2). */
void cs_fiber_symmetric_channel(const cs_position_t *pos,
                                const double sig[64],
                                int d,
                                double out[64]);

/* Channel 8 (antisymmetric pawn fiber in eigenbasis). Only pawns contribute.
 * Sign: white pawn → +val_P * PAWN_ANTI_FIBER[s]; black pawn → −val_P * .. */
void cs_fiber_antisymmetric(const cs_position_t *pos, double out[64]);

/* Channel 9 (diagonal-deviation / rook's shadow). Every piece contributes;
 * weight = sig[s] (already color-signed). */
void cs_fiber_diagonal(const cs_position_t *pos,
                       const double sig[64],
                       double out[64]);

/* Full 640-dim encoder. vals = SPECTRAL_VALS for standard usage. */
void cs_encode_640(const cs_position_t *pos,
                   const double vals[6],
                   cs_encoding_t *enc);

#ifdef __cplusplus
}
#endif

#endif /* CS_ENCODER_H */
