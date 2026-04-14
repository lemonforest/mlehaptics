/* cs_encoder.c — orchestrator for the 640-dim spectral chess encoder. */
#include "cs_encoder.h"

void cs_encode_640(const cs_position_t *pos,
                   const double vals[6],
                   cs_encoding_t *enc)
{
    double sig[64];
    cs_board_signal(pos, vals, sig);

    /* Dims 0..319: D4 irrep projections (A1, A2, B1, B2, E) */
    for (int ch = 0; ch < CS_NUM_IRREPS; ch++) {
        cs_project_irrep(sig, ch, &enc->v[ch * CS_BOARD_DIM]);
    }

    /* Dims 320..511: symmetric 3D fiber channels */
    for (int d = 0; d < CS_NUM_SYM_FIBER; d++) {
        cs_fiber_symmetric_channel(pos, sig, d,
                                   &enc->v[CS_NUM_IRREPS * CS_BOARD_DIM
                                           + d * CS_BOARD_DIM]);
    }

    /* Dims 512..575: antisymmetric pawn fiber */
    cs_fiber_antisymmetric(pos, &enc->v[512]);

    /* Dims 576..639: diagonal deviation */
    cs_fiber_diagonal(pos, sig, &enc->v[576]);
}
