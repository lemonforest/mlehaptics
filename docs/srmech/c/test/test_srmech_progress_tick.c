/*
 * test_srmech_progress_tick.c — bare-C-HOST smoke for the §101 (0.9.0rc275)
 * ENCODE-PROGRESS + graceful-abort primitive: the srmech_progress_tick_cb_t
 * per-iteration heartbeat WITH a nonzero-return-to-CANCEL channel. Distinct from
 * the rc242 srmech_progress_cb_t dispatch-OBSERVER (test_srmech_progress.c).
 *
 * Checks, via runtime if-guards (NOT assert — Release/NDEBUG in the pedantic CI
 * strips assert, so this doubles as the -Werror/-WX compile gate AND a real value
 * check when run):
 *   1. FIEDLER cancel — srmech_laplacian_fiedler_sparse_file_progress on a 4-cycle
 *      with a tick that CANCELS at iteration 3 returns SRMECH_CANCELLED and leaves
 *      out_vec ZEROED (a valid "no cut" vector). The events seen are the exact
 *      PARTITIONING phase, monotone done = 1,2,3, total = max_iters.
 *   2. MINT cancel — srmech_genome_mint_progress with a tick that CANCELS at
 *      kernel 1 returns SRMECH_CANCELLED with *n_blocks_out = the COMPLETE blocks
 *      of kernel 0 (a valid PARTIAL), and those bytes are a byte-PREFIX of the
 *      full (uncancelled) mint. The events are the MINTING phase, done = 0,1.
 *   3. NULL tick — the _progress overloads with tick == NULL behave exactly as
 *      the plain symbols (no cancel, full result).
 *
 * Run it (exit 0 = all pass):
 *   ./build/test_srmech_progress_tick
 */
#include "srmech.h"

#include <stdint.h>
#include <stdio.h>
#include <string.h>

/* ------------------------------------------------------------------ *
 * Shared event-shape validator: every tick must carry the versioned
 * struct_size gate, a nonzero total, and a monotone-nondecreasing done.
 * ------------------------------------------------------------------ */
static int      g_ev_bad;      /* set nonzero if any event is malformed        */
static uint64_t g_last_done;   /* monotonicity tracker (per test, reset first)  */
static uint32_t g_want_phase;  /* the phase the current op should report        */

static void check_ev(const srmech_progress_ev_t *ev)
{
    if (ev == NULL) { g_ev_bad = 1; return; }
    if (ev->struct_size != (uint32_t)sizeof(srmech_progress_ev_t)) { g_ev_bad = 1; }
    if (ev->phase != g_want_phase) { g_ev_bad = 1; }
    if (ev->total == 0u) { g_ev_bad = 1; }
    if (ev->done < g_last_done) { g_ev_bad = 1; }   /* monotone nondecreasing */
    g_last_done = ev->done;
}

/* Cancel the fiedler power loop at iteration 3 (done == 3). */
static int fiedler_tick(const srmech_progress_ev_t *ev, void *user_data)
{
    (void)user_data;
    check_ev(ev);
    return (ev->done >= 3u) ? 1 : 0;
}

/* Cancel the mint per-kernel loop at kernel 1 (done == 1). */
static int mint_tick(const srmech_progress_ev_t *ev, void *user_data)
{
    (void)user_data;
    check_ev(ev);
    return (ev->done >= 1u) ? 1 : 0;
}

/* Write a packed 16-byte-record edge file (u@0, v@4, w@8; host byte order). */
static int write_graph(const char *path, const uint32_t *eu, const uint32_t *ev,
                       const double *ew, size_t n_edges)
{
    FILE *fh = fopen(path, "wb");
    if (fh == NULL) { return -1; }
    for (size_t i = 0; i < n_edges; i++) {
        unsigned char rec[16];
        memcpy(rec, &eu[i], 4);
        memcpy(rec + 4, &ev[i], 4);
        memcpy(rec + 8, &ew[i], 8);
        if (fwrite(rec, 1u, sizeof rec, fh) != sizeof rec) { fclose(fh); return -1; }
    }
    return fclose(fh);
}

/* Test 1 — fiedler cancel at iteration 3 -> SRMECH_CANCELLED + zeroed out_vec. */
static int test_fiedler_cancel(void)
{
    const char *path = "srmech_progress_tick_graph.bin";
    uint32_t eu[4] = { 0u, 1u, 2u, 3u };
    uint32_t ev[4] = { 1u, 2u, 3u, 0u };            /* a 4-node cycle */
    double   ew[4] = { 1.0, 1.0, 1.0, 1.0 };
    if (write_graph(path, eu, ev, ew, 4u) != 0) {
        fprintf(stderr, "test_fiedler_cancel: cannot write graph file\n");
        return 1;
    }
    double out[4] = { 9.0, 9.0, 9.0, 9.0 };
    double ws[36];
    g_ev_bad = 0; g_last_done = 0u; g_want_phase = (uint32_t)SRMECH_PHASE_PARTITIONING;
    srmech_status_t st = srmech_laplacian_fiedler_sparse_file_progress(
        4u, path, 250u, out, ws, 36u, fiedler_tick, NULL);
    remove(path);
    if (st != SRMECH_CANCELLED) {
        fprintf(stderr, "test_fiedler_cancel: status=%d (want SRMECH_CANCELLED=%d)\n",
                (int)st, (int)SRMECH_CANCELLED);
        return 1;
    }
    for (int i = 0; i < 4; i++) {
        if (out[i] != 0.0) {
            fprintf(stderr, "test_fiedler_cancel: out[%d]=%g (want 0)\n", i, out[i]);
            return 1;
        }
    }
    if (g_ev_bad != 0 || g_last_done != 3u) {
        fprintf(stderr, "test_fiedler_cancel: bad event stream (bad=%d last_done=%llu)\n",
                g_ev_bad, (unsigned long long)g_last_done);
        return 1;
    }
    return 0;
}

/* Build minimal valid mint inputs: 3 single-leaf klein-4 kernels, leaf_dim 4. */
static int test_mint_cancel(void)
{
    const unsigned char labels[3] = { 'a', 'b', 'c' };
    const size_t label_lens[3] = { 1u, 1u, 1u };
    const unsigned char coupling[4] = { 1u, 2u, 3u, 0u };
    const unsigned char leaves[12] = { 0u, 1u, 2u, 3u, 3u, 2u, 1u, 0u, 1u, 1u, 2u, 2u };
    const size_t leaf_counts[3] = { 1u, 1u, 1u };
    unsigned char out_full[64];
    unsigned char out_part[64];
    size_t n_full = 0u, n_part = 0u;

    srmech_status_t st = srmech_genome_mint(labels, label_lens, coupling, 4u,
                                            leaves, leaf_counts, 3u,
                                            out_full, sizeof out_full, &n_full);
    if (st != SRMECH_OK || n_full == 0u) {
        fprintf(stderr, "test_mint_cancel: full mint status=%d n=%zu\n", (int)st, n_full);
        return 1;
    }
    g_ev_bad = 0; g_last_done = 0u; g_want_phase = (uint32_t)SRMECH_PHASE_MINTING;
    st = srmech_genome_mint_progress(labels, label_lens, coupling, 4u,
                                     leaves, leaf_counts, 3u,
                                     out_part, sizeof out_part, &n_part,
                                     mint_tick, NULL);
    if (st != SRMECH_CANCELLED) {
        fprintf(stderr, "test_mint_cancel: status=%d (want SRMECH_CANCELLED)\n", (int)st);
        return 1;
    }
    if (n_part == 0u || n_part >= n_full) {
        fprintf(stderr, "test_mint_cancel: n_part=%zu not a strict partial of n_full=%zu\n",
                n_part, n_full);
        return 1;
    }
    if (memcmp(out_full, out_part, n_part * 4u) != 0) {
        fprintf(stderr, "test_mint_cancel: partial is not a byte-prefix of the full mint\n");
        return 1;
    }
    if (g_ev_bad != 0 || g_last_done != 1u) {
        fprintf(stderr, "test_mint_cancel: bad event stream (bad=%d last_done=%llu)\n",
                g_ev_bad, (unsigned long long)g_last_done);
        return 1;
    }
    return 0;
}

/* Test 3 — NULL tick behaves as the plain symbol (no cancel, full mint). */
static int test_null_tick(void)
{
    const unsigned char labels[2] = { 'x', 'y' };
    const size_t label_lens[2] = { 1u, 1u };
    const unsigned char coupling[4] = { 1u, 2u, 3u, 0u };
    const unsigned char leaves[8] = { 0u, 1u, 2u, 3u, 2u, 2u, 1u, 1u };
    const size_t leaf_counts[2] = { 1u, 1u };
    unsigned char out_a[64], out_b[64];
    size_t n_a = 0u, n_b = 0u;
    srmech_status_t sa = srmech_genome_mint(labels, label_lens, coupling, 4u,
                                            leaves, leaf_counts, 2u,
                                            out_a, sizeof out_a, &n_a);
    srmech_status_t sb = srmech_genome_mint_progress(labels, label_lens, coupling, 4u,
                                                     leaves, leaf_counts, 2u,
                                                     out_b, sizeof out_b, &n_b,
                                                     NULL, NULL);
    if (sa != SRMECH_OK || sb != SRMECH_OK || n_a != n_b || n_a == 0u) {
        fprintf(stderr, "test_null_tick: status a=%d b=%d n_a=%zu n_b=%zu\n",
                (int)sa, (int)sb, n_a, n_b);
        return 1;
    }
    if (memcmp(out_a, out_b, n_a * 4u) != 0) {
        fprintf(stderr, "test_null_tick: NULL-tick mint differs from plain mint\n");
        return 1;
    }
    return 0;
}

int main(void)
{
    int fails = 0;
    fails += test_fiedler_cancel();
    fails += test_mint_cancel();
    fails += test_null_tick();
    if (fails == 0) {
        printf("test_srmech_progress_tick: all pass\n");
        return 0;
    }
    fprintf(stderr, "test_srmech_progress_tick: %d test(s) FAILED\n", fails);
    return 1;
}
