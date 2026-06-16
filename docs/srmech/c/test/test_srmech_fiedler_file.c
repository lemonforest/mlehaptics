/*
 * test_srmech_fiedler_file.c — C smoke for the §52 Part 2 OUT-OF-CORE streaming
 * Fiedler (srmech_laplacian_fiedler_sparse_file, F793; rc168).
 *
 * Same two-community graph as the in-core smoke (block A = {0,1,2}, block B =
 * {3,4,5}, each a triangle, joined by ONE weak bridge 2—3), but the adjacency is
 * written to a packed 16-byte-record file (uint32 u | uint32 v | double w) and
 * STREAMED through the PAL — no edge ever resident. The streamed cut must match
 * the in-core Fiedler's cut byte-for-byte (same algorithm, same init), and the
 * truncated-file / too-small-arena guards must fire.
 *
 * License: GPL-3.0-or-later.
 */

#include "srmech.h"

#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>

static int g_pass = 0;
static int g_fail = 0;

static void check(int cond, const char *msg)
{
    if (cond) { g_pass++; printf("  PASS  %s\n", msg); }
    else      { g_fail++; printf("  FAIL  %s\n", msg); }
}

/* Write one 16-byte edge record: u (4) | v (4) | w (8), host byte order. */
static int write_rec(FILE *f, uint32_t u, uint32_t v, double w)
{
    unsigned char rec[16];
    memcpy(rec, &u, sizeof(uint32_t));
    memcpy(rec + 4, &v, sizeof(uint32_t));
    memcpy(rec + 8, &w, sizeof(double));
    return fwrite(rec, 1u, sizeof(rec), f) == sizeof(rec) ? 0 : -1;
}

int main(void)
{
    printf("== srmech_fiedler_file smoke tests (rc168 §52 Part 2 streaming) ==\n");

    uint32_t eu[] = { 0u, 0u, 1u, 3u, 3u, 4u, 2u };
    uint32_t ev[] = { 1u, 2u, 2u, 4u, 5u, 5u, 3u };
    double   w[]  = { 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.05 };
    uint32_t n_edges = 7u;
    uint32_t n = 6u;

    const char *path = "fiedler_file_smoke.bin";
    FILE *f = fopen(path, "wb");
    check(f != NULL, "open packed graph file for write");
    int wrote_ok = 1;
    for (uint32_t i = 0; i < n_edges; i++) {
        if (write_rec(f, eu[i], ev[i], w[i]) != 0) { wrote_ok = 0; }
    }
    fclose(f);
    check(wrote_ok == 1, "wrote all 7 edge records");

    /* In-core reference cut (same graph, same algorithm). */
    double ref[6];
    double ws_ref[8 * 6];
    srmech_status_t st = srmech_laplacian_fiedler_sparse(
        n, n_edges, eu, ev, w, 250u, ref, ws_ref, (size_t)(8 * 6));
    check(st == SRMECH_OK, "in-core fiedler returns SRMECH_OK");

    /* Streamed cut from the file. */
    double out[6];
    double ws[8 * 6];
    st = srmech_laplacian_fiedler_sparse_file(
        n, path, 250u, out, ws, (size_t)(8 * 6));
    check(st == SRMECH_OK, "streaming fiedler returns SRMECH_OK");

    /* Block-uniform, opposite-sign partition (the clean cut). */
    int sa = (out[0] >= 0.0);
    int a_uniform = (sa == (out[1] >= 0.0)) && (sa == (out[2] >= 0.0));
    int sb = (out[3] >= 0.0);
    int b_uniform = (sb == (out[4] >= 0.0)) && (sb == (out[5] >= 0.0));
    check(a_uniform, "block A {0,1,2} has one sign");
    check(b_uniform, "block B {3,4,5} has one sign");
    check(sa != sb, "the two blocks have OPPOSITE signs (clean cut)");

    /* Streamed == in-core, bit-for-bit (same init, same matvec arithmetic). */
    int identical = 1;
    for (uint32_t i = 0; i < n; i++) {
        if (out[i] != ref[i]) { identical = 0; }
    }
    check(identical == 1, "streamed vector == in-core vector, bit-for-bit");

    /* n < 2 -> zero vector, OK (no file read needed). */
    double out1[1] = { 9.0 };
    double ws1[8];
    st = srmech_laplacian_fiedler_sparse_file(1u, path, 250u, out1, ws1,
                                              (size_t)8);
    check(st == SRMECH_OK && out1[0] == 0.0, "n<2 -> zero vector, OK");

    /* ws too small -> BAD_INPUT. */
    st = srmech_laplacian_fiedler_sparse_file(n, path, 250u, out, ws,
                                              (size_t)(8 * 6 - 1));
    check(st == SRMECH_ERR_BAD_INPUT, "ws_len < 8*n -> BAD_INPUT");

    /* Truncated file (not a whole number of records) -> BAD_INPUT. */
    const char *bad = "fiedler_file_trunc.bin";
    FILE *bf = fopen(bad, "wb");
    if (bf != NULL) {
        unsigned char junk[20] = { 0 };   /* 20 bytes != k*16 */
        fwrite(junk, 1u, sizeof(junk), bf);
        fclose(bf);
    }
    st = srmech_laplacian_fiedler_sparse_file(n, bad, 250u, out, ws,
                                              (size_t)(8 * 6));
    check(st == SRMECH_ERR_BAD_INPUT, "truncated file -> BAD_INPUT");

    /* Missing file -> IO error (path opens fail). */
    st = srmech_laplacian_fiedler_sparse_file(n, "does_not_exist.bin", 250u,
                                              out, ws, (size_t)(8 * 6));
    check(st != SRMECH_OK, "missing file -> non-OK");

    remove(path);
    remove(bad);

    printf("== %d passed, %d failed ==\n", g_pass, g_fail);
    return g_fail == 0 ? 0 : 1;
}
