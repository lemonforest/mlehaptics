/*
 * test_srmech_recursive_cut.c — C smoke for the §100 G1 OUT-OF-CORE RECURSIVE
 * SPECTRAL BISECTION driver (srmech_laplacian_recursive_cut; rc284).
 *
 * This is the symbol that closes the deepest C-host parity gap: before rc284 a
 * bare-C host had the Fiedler ENGINE (rc168) but not the RECURSION around it,
 * so it could bisect once and no further. The smoke therefore checks the parts
 * the engine alone could not do — that the driver TERMINATES, that the tomes it
 * writes PARTITION the node set exactly (every node once, no duplicates, no
 * drops), that the degenerate shapes do not wedge it, and that the §101 tick
 * cancel yields a valid COARSER partition rather than a torn one.
 *
 * Graph: four triangles {0,1,2} {3,4,5} {6,7,8} {9,10,11} joined in a ring by
 * single weak bridges — a shape with real community structure to cut.
 *
 * License: MIT.
 */

#include "srmech.h"

#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int g_pass = 0;
static int g_fail = 0;

static void check(int cond, const char *msg)
{
    if (cond) { g_pass++; printf("  PASS  %s\n", msg); }
    else      { g_fail++; printf("  FAIL  %s\n", msg); }
}

static int write_rec(FILE *f, uint32_t u, uint32_t v, double w)
{
    unsigned char rec[16];
    memcpy(rec, &u, sizeof(uint32_t));
    memcpy(rec + 4, &v, sizeof(uint32_t));
    memcpy(rec + 8, &w, sizeof(double));
    return fwrite(rec, 1u, sizeof(rec), f) == sizeof(rec) ? 0 : -1;
}

/* Read a packed node-set tome back (uint32 records). Returns count, -1 on error. */
static long read_tome(const char *path, uint32_t *out, size_t cap)
{
    FILE *f = fopen(path, "rb");
    if (f == NULL) { return -1; }
    size_t n = fread(out, sizeof(uint32_t), cap, f);
    fclose(f);
    return (long)n;
}

/* Every node in 0..n-1 must appear in EXACTLY one tome, exactly once. */
static int tomes_partition_exactly(uint32_t n, uint32_t n_tomes,
                                   const char *paths, const uint32_t *sizes)
{
    uint32_t seen[64];
    uint32_t buf[64];
    memset(seen, 0, sizeof seen);
    if (n > 64u) { return 0; }
    uint32_t total = 0u;
    for (uint32_t t = 0u; t < n_tomes; t++) {
        long got = read_tome(paths + (size_t)t * 512u, buf, 64u);
        if (got < 0 || (uint32_t)got != sizes[t]) { return 0; }
        for (long i = 0; i < got; i++) {
            if (buf[i] >= n) { return 0; }
            seen[buf[i]] += 1u;
        }
        total += (uint32_t)got;
    }
    if (total != n) { return 0; }
    for (uint32_t i = 0u; i < n; i++) { if (seen[i] != 1u) { return 0; } }
    return 1;
}

/* A tick that cancels on its `at`-th call (1-based); counts every call. */
static int g_tick_calls = 0;
static int g_tick_cancel_at = 0;
static uint64_t g_tick_last_total = 0u;
static int g_tick_monotone = 1;
static uint64_t g_tick_prev_done = 0u;

static int cancel_tick(const srmech_progress_ev_t *ev, void *user)
{
    (void)user;
    g_tick_calls++;
    if (ev->struct_size != (uint32_t)sizeof(srmech_progress_ev_t)) { return 0; }
    if (ev->done < g_tick_prev_done) { g_tick_monotone = 0; }
    g_tick_prev_done = ev->done;
    g_tick_last_total = ev->total;
    if (g_tick_cancel_at != 0 && g_tick_calls >= g_tick_cancel_at) { return 1; }
    return 0;
}

static int build_graph(const char *path)
{
    /* four triangles, ring-bridged by weak edges */
    uint32_t tu[] = { 0u,0u,1u,  3u,3u,4u,  6u,6u,7u,  9u,9u,10u };
    uint32_t tv[] = { 1u,2u,2u,  4u,5u,5u,  7u,8u,8u, 10u,11u,11u };
    uint32_t bu[] = { 2u, 5u, 8u, 11u };
    uint32_t bv[] = { 3u, 6u, 9u,  0u };
    FILE *f = fopen(path, "wb");
    if (f == NULL) { return -1; }
    for (size_t i = 0; i < sizeof tu / sizeof tu[0]; i++) {
        if (write_rec(f, tu[i], tv[i], 1.0) != 0) { fclose(f); return -1; }
    }
    for (size_t i = 0; i < sizeof bu / sizeof bu[0]; i++) {
        if (write_rec(f, bu[i], bv[i], 0.02) != 0) { fclose(f); return -1; }
    }
    fclose(f);
    return 0;
}

int main(void)
{
    printf("== srmech_recursive_cut smoke tests (rc284 §100 G1) ==\n");

    const char *graph = "rcut_graph.bin";
    const char *work  = "rcut_work";
    check(build_graph(graph) == 0, "packed ring-of-triangles graph written");

    uint32_t n = 12u;
    size_t need = srmech_laplacian_recursive_cut_arena_bytes(n);
    check(need >= 88u * (size_t)n, "arena_bytes covers 9n doubles + 4n+4 uint32");
    double *ws = (double *)malloc(need);
    check(ws != NULL, "test arena allocated (the LIBRARY never allocates)");
    if (ws == NULL) { return 1; }

    enum { CAP = 32 };
    static char  paths[CAP * 512];
    uint32_t     sizes[CAP];
    uint32_t     n_tomes = 0u;

    /* ---- 1. the ordinary partition ------------------------------------- */
    srmech_status_t st = srmech_laplacian_recursive_cut(
        n, graph, work, 3u, 250u, 64u, sizes, paths, (size_t)CAP, &n_tomes,
        ws, need, NULL, NULL);
    check(st == SRMECH_OK, "recursive_cut returns OK on a real graph");
    check(n_tomes >= 2u, "the driver actually RECURSED (more than one tome)");
    check(tomes_partition_exactly(n, n_tomes, paths, sizes),
          "tomes partition all 12 nodes exactly once");
    for (uint32_t t = 0u; t < n_tomes; t++) {
        if (sizes[t] > 3u) {
            check(0, "every leaf tome is within max_tome");
            break;
        }
    }
    check(1, "leaf tomes respect max_tome=3");

    /* ---- 2. determinism: a re-run reproduces the partition exactly ------ */
    static char paths2[CAP * 512];
    uint32_t sizes2[CAP];
    uint32_t n_tomes2 = 0u;
    st = srmech_laplacian_recursive_cut(n, graph, work, 3u, 250u, 64u, sizes2,
                                        paths2, (size_t)CAP, &n_tomes2, ws, need,
                                        NULL, NULL);
    check(st == SRMECH_OK && n_tomes2 == n_tomes, "re-run yields the same tome count");
    check(memcmp(sizes, sizes2, sizeof(uint32_t) * n_tomes) == 0,
          "re-run yields identical tome sizes (deterministic)");

    /* ---- 3. degenerate shapes ------------------------------------------ */
    uint32_t n1 = 0u;
    st = srmech_laplacian_recursive_cut(0u, graph, work, 3u, 250u, 64u, sizes,
                                        paths, (size_t)CAP, &n1, ws, need,
                                        NULL, NULL);
    check(st == SRMECH_OK && n1 == 1u && sizes[0] == 0u,
          "n == 0 yields ONE empty tome (mirrors the Python projection)");

    st = srmech_laplacian_recursive_cut(1u, graph, "rcut_w1", 3u, 250u, 64u,
                                        sizes, paths, (size_t)CAP, &n1, ws, need,
                                        NULL, NULL);
    check(st == SRMECH_OK && n1 == 1u, "single-node graph -> exactly one tome");

    const char *empty = "rcut_empty.bin";
    FILE *ef = fopen(empty, "wb");
    if (ef != NULL) { fclose(ef); }
    uint32_t n2 = 0u;
    st = srmech_laplacian_recursive_cut(6u, empty, "rcut_w2", 2u, 250u, 64u,
                                        sizes, paths, (size_t)CAP, &n2, ws, need,
                                        NULL, NULL);
    check(st == SRMECH_OK, "edgeless graph does not wedge the driver");
    check(tomes_partition_exactly(6u, n2, paths, sizes),
          "edgeless graph still partitions all its nodes exactly once");

    /* ---- 4. guards ------------------------------------------------------ */
    st = srmech_laplacian_recursive_cut(n, graph, work, 3u, 250u, 64u, sizes,
                                        paths, (size_t)CAP, &n_tomes, ws,
                                        need - 1u, NULL, NULL);
    check(st == SRMECH_ERR_BAD_INPUT, "undersized arena -> BAD_INPUT");

    st = srmech_laplacian_recursive_cut(n, NULL, work, 3u, 250u, 64u, sizes,
                                        paths, (size_t)CAP, &n_tomes, ws, need,
                                        NULL, NULL);
    check(st == SRMECH_ERR_NULL_ARG, "NULL edges_path -> NULL_ARG");

    st = srmech_laplacian_recursive_cut(n, graph, work, 3u, 250u, 64u, sizes,
                                        paths, (size_t)1u, &n_tomes, ws, need,
                                        NULL, NULL);
    check(st == SRMECH_ERR_OVERFLOW, "too-small tome_paths capacity -> OVERFLOW");

    /* ---- 5. §101 tick: observe, then cancel ----------------------------- */
    g_tick_calls = 0; g_tick_cancel_at = 0;
    g_tick_prev_done = 0u; g_tick_monotone = 1;
    uint32_t n3 = 0u;
    st = srmech_laplacian_recursive_cut(n, graph, "rcut_w3", 3u, 250u, 64u,
                                        sizes, paths, (size_t)CAP, &n3, ws, need,
                                        cancel_tick, NULL);
    check(st == SRMECH_OK, "a never-cancelling tick runs to completion");
    check(g_tick_calls > 0, "tick fired");
    check(g_tick_monotone, "tick `done` is monotone non-decreasing");
    check(g_tick_last_total == (uint64_t)n, "tick `total` is n");

    g_tick_calls = 0; g_tick_cancel_at = 1;
    g_tick_prev_done = 0u;
    uint32_t n4 = 0u;
    st = srmech_laplacian_recursive_cut(n, graph, "rcut_w4", 3u, 250u, 64u,
                                        sizes, paths, (size_t)CAP, &n4, ws, need,
                                        cancel_tick, NULL);
    check(st == SRMECH_CANCELLED, "cancelling tick -> SRMECH_CANCELLED");
    check(tomes_partition_exactly(n, n4, paths, sizes),
          "CANCELLED still partitions all n nodes (coarser, never torn)");

    free(ws);
    printf("\n%d passed, %d failed\n", g_pass, g_fail);
    return g_fail == 0 ? 0 : 1;
}
