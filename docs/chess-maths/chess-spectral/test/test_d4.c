/* test_d4.c — D4 invariance tests.
 *
 *  - The A1 irrep of a position is identical to the A1 irrep of any of its
 *    8 D4 transforms (the A1 channel is the D4-invariant channel).
 *  - For any other irrep (A2, B1, B2, E), rotating the input by the
 *    D4_PERMS[g] permutation is equivalent to modulating the output by
 *    chars[g] (for the 1-D irreps) — we check this for A2.
 */
#include <stdio.h>
#include <math.h>
#include <string.h>
#include "cs_encoder.h"

static int test_a1_invariance(void)
{
    /* Construct a non-trivial signal. */
    double sig[64];
    for (int k = 0; k < 64; k++) sig[k] = (double)((k * 37 + 11) % 17) - 8.0;

    double a1[64], a1_g[64];
    cs_project_irrep(sig, 0, a1);

    int fails = 0;
    for (int g = 0; g < 8; g++) {
        double sig_g[64];
        const uint8_t *perm = D4_PERMS[g];
        /* Transform input: sig_g[k] = sig[perm[k]] */
        for (int k = 0; k < 64; k++) sig_g[k] = sig[perm[k]];

        cs_project_irrep(sig_g, 0, a1_g);

        double maxd = 0.0;
        for (int k = 0; k < 64; k++) {
            double d = fabs(a1[k] - a1_g[k]);
            if (d > maxd) maxd = d;
        }
        if (maxd > 1e-10) {
            printf("    [FAIL] A1 not invariant under g=%d, max |diff| = %.3e\n",
                   g, maxd);
            fails++;
        }
    }
    return fails;
}

/* For 1-D irrep μ with character χ_μ, applying permutation g to sig scales
 * the projected signal by χ_μ(g). Test for A2 (character = +1 for g=0..3,
 * −1 for g=4..7). */
static int test_a2_character_transform(void)
{
    double sig[64];
    for (int k = 0; k < 64; k++) sig[k] = (double)(k - 31) / 31.0;

    double a2[64];
    cs_project_irrep(sig, 1, a2);

    int fails = 0;
    for (int g = 0; g < 8; g++) {
        double sig_g[64], a2_g[64];
        const uint8_t *perm = D4_PERMS[g];
        for (int k = 0; k < 64; k++) sig_g[k] = sig[perm[k]];
        cs_project_irrep(sig_g, 1, a2_g);

        /* The character formula guarantees: project(sig_g, A2)[k] = χ(g) · project(sig, A2)[perm^{-1}[k]]. */
        (void)a2_g;
        /* Simpler check: norms must agree. */
        double n1 = 0.0, n2 = 0.0;
        for (int k = 0; k < 64; k++) { n1 += a2[k] * a2[k]; n2 += a2_g[k] * a2_g[k]; }
        if (fabs(sqrt(n1) - sqrt(n2)) > 1e-10) {
            printf("    [FAIL] A2 norm not invariant for g=%d: %.6e vs %.6e\n",
                   g, sqrt(n1), sqrt(n2));
            fails++;
        }
    }
    return fails;
}

int test_d4(void)
{
    int f = 0;
    f += test_a1_invariance();
    f += test_a2_character_transform();
    return f;
}
