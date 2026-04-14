/* test_temporal.c — coprime roll binding invariants. */
#include <stdio.h>
#include <math.h>
#include <string.h>
#include "cs_temporal.h"

static int test_roll_self_inverse(void)
{
    double x[CS_ENCODING_DIM];
    for (int i = 0; i < CS_ENCODING_DIM; i++) x[i] = (double)(i * 17 % 101) - 50.0;

    double y[CS_ENCODING_DIM], z[CS_ENCODING_DIM];
    int offs[] = {1, 7, 67, 131, 313, 639, -1, -131};
    for (size_t j = 0; j < sizeof(offs) / sizeof(offs[0]); j++) {
        cs_roll_640(x, offs[j], y);
        cs_roll_640(y, -offs[j], z);
        for (int i = 0; i < CS_ENCODING_DIM; i++) {
            if (x[i] != z[i]) {
                printf("    [FAIL] roll(roll(x,%d),-%d) != x at i=%d\n",
                       offs[j], offs[j], i);
                return 1;
            }
        }
    }
    return 0;
}

static int test_spatial_offsets_distinct(void)
{
    int seen[CS_ENCODING_DIM] = {0};
    for (int r = 0; r < 8; r++) {
        for (int c = 0; c < 8; c++) {
            int o = cs_spatial_offset(r, c) % CS_ENCODING_DIM;
            if (o < 0) o += CS_ENCODING_DIM;
            if (seen[o]) {
                printf("    [FAIL] spatial offset collision at (r=%d,c=%d) o=%d\n", r, c, o);
                return 1;
            }
            seen[o] = 1;
        }
    }
    return 0;
}

static int test_temporal_offsets_distinct_over_horizon(void)
{
    /* Expect distinct offsets for t=0..N-1 where N·131 < 640·gcd-cycle.
     * Since gcd(131, 640)=1, 131 generates all of Z_640, so the orbit
     * period is 640. Check all 640 are distinct. */
    int seen[CS_ENCODING_DIM] = {0};
    for (int t = 0; t < CS_ENCODING_DIM; t++) {
        int o = cs_temporal_offset(t) % CS_ENCODING_DIM;
        if (o < 0) o += CS_ENCODING_DIM;
        if (seen[o]) {
            printf("    [FAIL] temporal offset collision at t=%d, o=%d\n", t, o);
            return 1;
        }
        seen[o] = 1;
    }
    return 0;
}

int test_temporal(void)
{
    int f = 0;
    f += test_roll_self_inverse();
    f += test_spatial_offsets_distinct();
    f += test_temporal_offsets_distinct_over_horizon();
    return f;
}
