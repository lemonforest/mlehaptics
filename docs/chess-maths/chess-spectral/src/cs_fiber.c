/* cs_fiber.c — Three fiber channels:
 *   (1) symmetric 3D fiber (channels 5-7)       — LOCAL_FIBER_3D / LOCAL_ADJ_ROWS
 *   (2) antisymmetric pawn fiber (channel 8)    — PAWN_ANTI_FIBER
 *   (3) diagonal deviation (channel 9)          — DIAG_DEV
 *
 * Channels 5-7 skip pawns (no movement Laplacian in the 3D fiber basis).
 * Channel 8 only pawns contribute (all other pieces have symmetric A).
 * Channel 9 every piece contributes, weighted by signed piece value.
 */
#include <string.h>
#include "cs_encoder.h"
#include "cs_fiber_tables.h"

/* Map cs_piece_t to fiber_idx (0..4) for N,B,R,Q,K. Pawn returns -1. */
static inline int fiber_index(int type) {
    return (type >= 1 && type <= 5) ? (type - 1) : -1;
}

void cs_fiber_symmetric_channel(const cs_position_t *pos,
                                const double sig[64],
                                int d,
                                double out[64])
{
    memset(out, 0, 64 * sizeof(double));
    for (int i = 0; i < pos->count; i++) {
        int fi = fiber_index(pos->type[i]);
        if (fi < 0) continue;         /* skip pawns */
        int s = pos->square[i];
        double fib_d = LOCAL_FIBER_3D[fi][s][d];
        const double *adj_row = LOCAL_ADJ_ROWS[fi][s];

        /* gradient = adj_row · sig  (total material on reachable squares) */
        double gradient = 0.0;
        for (int k = 0; k < 64; k++) gradient += adj_row[k] * sig[k];

        double w = gradient * fib_d;
        for (int k = 0; k < 64; k++) out[k] += w * adj_row[k];
    }
}

void cs_fiber_antisymmetric(const cs_position_t *pos, double out[64])
{
    memset(out, 0, 64 * sizeof(double));
    const double val_P = SPECTRAL_VALS[CS_PAWN];
    for (int i = 0; i < pos->count; i++) {
        if (pos->type[i] != CS_PAWN) continue;
        int s = pos->square[i];
        double w = (double)pos->color[i] * val_P;   /* +val_P white, -val_P black */
        const double *row = PAWN_ANTI_FIBER[s];     /* in eigenbasis */
        for (int k = 0; k < 64; k++) out[k] += w * row[k];
    }
}

void cs_fiber_diagonal(const cs_position_t *pos,
                       const double sig[64],
                       double out[64])
{
    memset(out, 0, 64 * sizeof(double));
    for (int i = 0; i < pos->count; i++) {
        int s = pos->square[i];
        int t = pos->type[i];
        double w = sig[s];  /* already signed */
        const double *row = DIAG_DEV[t];
        for (int k = 0; k < 64; k++) out[k] += w * row[k];
    }
}
