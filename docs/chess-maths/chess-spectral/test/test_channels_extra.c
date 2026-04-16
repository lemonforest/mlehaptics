/* test_channels_extra.c — channel 8/9 specific invariants. */
#include <stdio.h>
#include <math.h>
#include <string.h>
#include "cs_encoder.h"
#include "cs_fiber_tables.h"

static double vnorm(const double *v, int n) {
    double s = 0.0;
    for (int i = 0; i < n; i++) s += v[i] * v[i];
    return sqrt(s);
}

/* Test: a no-pawn position has antisymmetric channel exactly zero. */
static int test_antisym_zero_without_pawns(void)
{
    cs_position_t pos;
    pos.count = 2;
    pos.square[0] = 27; pos.type[0] = CS_KNIGHT; pos.color[0] = +1;
    pos.square[1] = 36; pos.type[1] = CS_ROOK;   pos.color[1] = -1;

    double anti[64];
    cs_fiber_antisymmetric(&pos, anti);
    double n = vnorm(anti, 64);
    if (n != 0.0) {
        printf("    [FAIL] no-pawn antisym norm = %.3e, expected 0\n", n);
        return 1;
    }
    return 0;
}

/* Test: a single rook contributes ||diag|| ≈ val_R · ||DIAG_DEV[R]|| ≈ 5.4 · 88.05 ≈ 475.5. */
static int test_rook_diag_magnitude(void)
{
    cs_position_t pos;
    pos.count = 1;
    pos.square[0] = 28; pos.type[0] = CS_ROOK; pos.color[0] = +1;

    double sig[64], diag[64];
    cs_board_signal(&pos, SPECTRAL_VALS, sig);
    cs_fiber_diagonal(&pos, sig, diag);

    double got = vnorm(diag, 64);
    double val_R = SPECTRAL_VALS[CS_ROOK];
    double expected = val_R * vnorm(DIAG_DEV[CS_ROOK], 64);

    if (fabs(got - expected) > 1e-9) {
        printf("    [FAIL] rook diag norm = %.6f, expected %.6f\n",
               got, expected);
        return 1;
    }
    return 0;
}

/* Test: a single rook has negligible symmetric-fiber content (||F3|| ~ 0). */
static int test_rook_symfiber_near_zero(void)
{
    cs_position_t pos;
    pos.count = 1;
    pos.square[0] = 28; pos.type[0] = CS_ROOK; pos.color[0] = +1;

    double sig[64], f[64];
    cs_board_signal(&pos, SPECTRAL_VALS, sig);

    /* Symmetric fiber gradient = adj · sig = 0 (only rook itself is placed,
     * and the rook's own square is NOT in its adjacency row). */
    for (int d = 0; d < 3; d++) {
        cs_fiber_symmetric_channel(&pos, sig, d, f);
        double n = vnorm(f, 64);
        if (n > 1e-12) {
            printf("    [FAIL] single-rook sym fiber[%d] norm = %.3e, expected ~0\n",
                   d, n);
            return 1;
        }
    }
    return 0;
}

/* Test: a single white pawn produces a non-trivial antisymmetric contribution. */
static int test_single_pawn_antisym_nonzero(void)
{
    cs_position_t pos;
    pos.count = 1;
    pos.square[0] = 52; /* e.g. (6, 4) = e2 */
    pos.type[0] = CS_PAWN; pos.color[0] = +1;

    double anti[64];
    cs_fiber_antisymmetric(&pos, anti);

    double n = vnorm(anti, 64);
    if (n < 1e-6) {
        printf("    [FAIL] single pawn antisym norm = %.3e, expected > 0\n", n);
        return 1;
    }
    return 0;
}

/* Test: black pawn antisym is exactly negated version of white pawn antisym. */
static int test_pawn_antisym_color_symmetry(void)
{
    cs_position_t pos_w, pos_b;
    pos_w.count = 1;
    pos_w.square[0] = 52; pos_w.type[0] = CS_PAWN; pos_w.color[0] = +1;
    pos_b = pos_w;
    pos_b.color[0] = -1;

    double a_w[64], a_b[64];
    cs_fiber_antisymmetric(&pos_w, a_w);
    cs_fiber_antisymmetric(&pos_b, a_b);

    double maxd = 0.0;
    for (int k = 0; k < 64; k++) {
        double d = fabs(a_w[k] + a_b[k]);
        if (d > maxd) maxd = d;
    }
    if (maxd > 1e-12) {
        printf("    [FAIL] w + b antisym should = 0, max |diff| = %.3e\n", maxd);
        return 1;
    }
    return 0;
}

int test_channels_extra(void)
{
    int f = 0;
    f += test_antisym_zero_without_pawns();
    f += test_rook_diag_magnitude();
    f += test_rook_symfiber_near_zero();
    f += test_single_pawn_antisym_nonzero();
    f += test_pawn_antisym_color_symmetry();
    return f;
}
