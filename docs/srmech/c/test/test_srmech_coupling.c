/*
 * test_srmech_coupling.c — standalone C-HOST proof for the resonant-spectrum
 * closure (srmech_coupling.c, §75 / F928).
 *
 * THE POINT (the C-host-only mandate): a C-ONLY host — no Python — reads a
 * coupling Laplacian as a stored resonant object via srmech_resonant_spectrum,
 * orchestrating the existing eigensolve + best_rational + factor kernels. The
 * anchor is the F928 Jupiter+Galilean-moon gravity Laplacian (n=5): L^2
 * concentrates on the Jupiter<->Io pair ~20x+ vs the outer Callisto coupling.
 *
 * Build + run (Linux gcc / macOS clang), pedantic, warnings = errors:
 *   cc -std=c17 -Wall -Wextra -Wpedantic -Werror -I../include \
 *      test_srmech_coupling.c ../src/srmech_coupling.c ../src/srmech_laplacian.c \
 *      ../src/srmech_config.c ../src/srmech_rational.c ../src/srmech_cyclic.c \
 *      ../src/srmech_primes.c -o /tmp/coupling && /tmp/coupling
 *
 * Mirrors the assert+count house style of test_srmech_qi.c (no framework;
 * exits 0 on all-pass, non-zero on first fail).
 */

#include "srmech.h"

#include <stdint.h>
#include <stdio.h>

static int g_passed = 0;
static int g_failed = 0;

static void check_true(int cond, const char *desc)
{
    if (cond) {
        g_passed++;
    } else {
        g_failed++;
        printf("FAIL %s\n", desc);
    }
}

/* |x| via x*x compare (no libm / abs in the test either). */
static double mag(double x)
{
    return (x < 0.0) ? -x : x;
}

/* Build the F928 Jupiter+Galilean gravity Laplacian L = D - A (n=5) into the
 * caller's row-major buffer. weights w_ij = m_i*m_j / r_ij^2 (central body 0
 * at origin: r is the outer body's axis; moon-moon: the axis gap). */
static void build_jupiter_laplacian(double *L)
{
    const double a[5] = {0.0, 421.7, 671.0, 1070.4, 1882.7};
    const double m[5] = {189800.0, 8.93, 4.80, 14.82, 10.76};
    for (int e = 0; e < 25; e++) {
        L[e] = 0.0;
    }
    for (int i = 0; i < 5; i++) {
        for (int j = i + 1; j < 5; j++) {
            double r = (i == 0) ? a[j] : (a[j] - a[i]);
            if (r > 0.0) {
                double w = m[i] * m[j] / (r * r);
                L[i * 5 + j] -= w;
                L[j * 5 + i] -= w;
                L[i * 5 + i] += w;
                L[j * 5 + j] += w;
            }
        }
    }
}

int main(void)
{
    const uint32_t n = 5;
    double L[25];
    build_jupiter_laplacian(L);

    double tensions[5];
    double modes[25];
    double force_orders[2 * 25];    /* orders = 2 */
    int32_t res_pairs[4 * 2];       /* up to n-1 = 4 resonances */
    uint64_t res_ratio[4 * 2];
    int32_t res_locked[4];
    uint32_t res_count = 0;

    size_t ws_bytes = srmech_resonant_spectrum_arena_bytes(n);
    double ws[256];                 /* > arena need for n=5 (175 doubles) */
    check_true(ws_bytes <= sizeof(ws), "arena fits the static ws");

    srmech_status_t st = srmech_resonant_spectrum(
        n, L, 2u, 64u, tensions, modes, force_orders,
        res_pairs, res_ratio, res_locked, &res_count, ws, sizeof(ws));
    check_true(st == SRMECH_OK, "resonant_spectrum returns OK");

    /* Tensions ascending; one near-zero free mode (connected graph). */
    int ascending = 1;
    for (uint32_t i = 1; i < n; i++) {
        if (tensions[i] < tensions[i - 1]) {
            ascending = 0;
        }
    }
    check_true(ascending, "tensions ascending");
    check_true(mag(tensions[0]) < tensions[n - 1] * 1e-6, "one ~zero free mode");

    /* THE ANCHOR: L^2 (force_orders[1]) concentrates on Jupiter<->Io (0,1)
     * vs the outer Jupiter<->Callisto (0,4) — ratio > 15x (~26x in practice). */
    const double *L2 = force_orders + 25;
    double io = mag(L2[0 * 5 + 1]);
    double callisto = mag(L2[0 * 5 + 4]);
    check_true(io > 15.0 * callisto, "L^2 Jupiter<->Io concentration > 15x");

    /* force_orders[0] == L (the first order is L itself). */
    int l1_ok = 1;
    const double *L1 = force_orders;
    for (uint32_t e = 0; e < 25; e++) {
        if (mag(L1[e] - L[e]) > 1e-6) {
            l1_ok = 0;
        }
    }
    check_true(l1_ok, "force_orders[0] == L");

    /* Resonances were read; at least one adjacent pair, each ratio den >= 1. */
    check_true(res_count >= 1u && res_count <= 4u, "resonance count in range");
    int ratios_ok = 1;
    for (uint32_t i = 0; i < res_count; i++) {
        if (res_ratio[i * 2 + 1] < 1u || res_locked[i] < 0) {
            ratios_ok = 0;
        }
    }
    check_true(ratios_ok, "every resonance has den >= 1 + a lock flag");

    /* A 2x2 identity → eigenvalues {1,1}, ratio 1/1 (locked). */
    double I2[4] = {1.0, 0.0, 0.0, 1.0};
    double t2[2], m2[4], f2[2 * 4];
    int32_t p2[1 * 2];
    uint64_t r2[1 * 2];
    int32_t lk2[1];
    uint32_t c2 = 0;
    double ws2[64];
    srmech_status_t st2 = srmech_resonant_spectrum(
        2u, I2, 2u, 64u, t2, m2, f2, p2, r2, lk2, &c2, ws2, sizeof(ws2));
    check_true(st2 == SRMECH_OK, "identity 2x2 OK");
    check_true(c2 == 1u && r2[0] == 1u && r2[1] == 1u, "identity ratio 1/1");

    /* Bad input: orders < 1. */
    srmech_status_t stb = srmech_resonant_spectrum(
        2u, I2, 0u, 64u, t2, m2, f2, p2, r2, lk2, &c2, ws2, sizeof(ws2));
    check_true(stb == SRMECH_ERR_BAD_INPUT, "orders<1 is BAD_INPUT");

    printf("test_srmech_coupling: %d passed, %d failed\n", g_passed, g_failed);
    return (g_failed == 0) ? 0 : 1;
}
