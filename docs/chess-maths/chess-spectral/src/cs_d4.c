/* cs_d4.c — D4 irrep projection via Serre's character formula.
 *
 * For irrep μ with character chars[g] over D4 group elements g=0..7,
 *   projected[k] = (dim_μ / 8) · Σ_g chars[g] · sig[D4_PERMS[g][k]]
 * Here dim_μ = 2 for E, 1 for A1,A2,B1,B2. The permutation interpretation
 * matches encoder_512.py: sig[perm] gathers values according to perm.
 */
#include <string.h>
#include "cs_encoder.h"

void cs_project_irrep(const double sig[64], int irrep_idx, double out[64])
{
    const int dim_mu = (irrep_idx == 4) ? 2 : 1;  /* E is 2-dim */
    const double scale = (double)dim_mu / 8.0;

    double acc[64];
    memset(acc, 0, sizeof(acc));

    for (int g = 0; g < 8; g++) {
        int chi = CHARS[irrep_idx][g];
        if (chi == 0) continue;
        const uint8_t *perm = D4_PERMS[g];
        /* acc[k] += chi · sig[perm[k]] */
        if (chi == 1) {
            for (int k = 0; k < 64; k++) acc[k] += sig[perm[k]];
        } else if (chi == -1) {
            for (int k = 0; k < 64; k++) acc[k] -= sig[perm[k]];
        } else {
            for (int k = 0; k < 64; k++) acc[k] += (double)chi * sig[perm[k]];
        }
    }

    for (int k = 0; k < 64; k++) out[k] = scale * acc[k];
}
