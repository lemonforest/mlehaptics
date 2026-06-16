/*
 * test_srmech_fiedler.c — C smoke for the §51 sparse normalized-cut Fiedler
 * (srmech_laplacian_fiedler_sparse, issue #1097; rc166).
 *
 * A two-community graph (block A = {0,1,2}, block B = {3,4,5}, each a triangle,
 * joined by ONE weak bridge 2—3) has a clean Fiedler cut: the sign of the
 * converged vector must separate A from B (up to a global flip). We check that,
 * plus the n<2 / too-small-arena / out-of-range-edge guards.
 *
 * License: GPL-3.0-or-later.
 */

#include "srmech.h"

#include <stdint.h>
#include <stddef.h>
#include <stdio.h>

static int g_pass = 0;
static int g_fail = 0;

static void check(int cond, const char *msg)
{
    if (cond) { g_pass++; printf("  PASS  %s\n", msg); }
    else      { g_fail++; printf("  FAIL  %s\n", msg); }
}

int main(void)
{
    printf("== srmech_fiedler smoke tests (rc166 §51 sparse Fiedler) ==\n");

    /* Two triangles {0,1,2} and {3,4,5} + a weak bridge 2—3. */
    uint32_t eu[] = { 0u, 0u, 1u, 3u, 3u, 4u, 2u };
    uint32_t ev[] = { 1u, 2u, 2u, 4u, 5u, 5u, 3u };
    double   w[]  = { 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.05 };
    uint32_t n_edges = 7u;
    uint32_t n = 6u;

    double out[6];
    double ws[8 * 6];   /* caller arena: 8*n doubles */
    srmech_status_t st = srmech_laplacian_fiedler_sparse(
        n, n_edges, eu, ev, w, 250u, out, ws, (size_t)(8 * 6));
    check(st == SRMECH_OK, "fiedler returns SRMECH_OK");

    /* Sign partition must split A = {0,1,2} from B = {3,4,5} (up to a flip). */
    int sa = (out[0] >= 0.0);
    int a_uniform = (sa == (out[1] >= 0.0)) && (sa == (out[2] >= 0.0));
    int sb = (out[3] >= 0.0);
    int b_uniform = (sb == (out[4] >= 0.0)) && (sb == (out[5] >= 0.0));
    check(a_uniform, "block A {0,1,2} has one sign");
    check(b_uniform, "block B {3,4,5} has one sign");
    check(sa != sb, "the two blocks have OPPOSITE signs (clean cut)");

    /* n < 2 -> zero vector, OK. */
    double out1[1] = { 9.0 };
    double ws1[8];
    st = srmech_laplacian_fiedler_sparse(1u, 0u, NULL, NULL, NULL, 250u,
                                         out1, ws1, (size_t)8);
    check(st == SRMECH_OK && out1[0] == 0.0, "n<2 -> zero vector, OK");

    /* ws too small -> BAD_INPUT. */
    st = srmech_laplacian_fiedler_sparse(n, n_edges, eu, ev, w, 250u, out, ws,
                                         (size_t)(8 * 6 - 1));
    check(st == SRMECH_ERR_BAD_INPUT, "ws_len < 8*n -> BAD_INPUT");

    /* out-of-range edge endpoint -> BAD_INPUT. */
    uint32_t bad_ev[] = { 1u, 99u, 2u, 4u, 5u, 5u, 3u };   /* 99 >= n */
    st = srmech_laplacian_fiedler_sparse(n, n_edges, eu, bad_ev, w, 250u, out,
                                         ws, (size_t)(8 * 6));
    check(st == SRMECH_ERR_BAD_INPUT, "out-of-range edge -> BAD_INPUT");

    /* NOTE: the NULL-arg runtime guard (returns SRMECH_ERR_NULL_ARG in a
     * release build) is NOT exercised here — asserts are active in this build
     * and trip first, by design (the JPL precondition-assert convention). */

    printf("== %d passed, %d failed ==\n", g_pass, g_fail);
    return g_fail == 0 ? 0 : 1;
}
