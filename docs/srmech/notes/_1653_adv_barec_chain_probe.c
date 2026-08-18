/*
 * _1653_adv_barec_chain_probe.c — ADVERSARIAL independent re-derivation of the
 * gh #1653 chain-census rejections, by a route that shares NOTHING with the
 * census harness: static libsrmech.a, no Python, no ctypes, no _compose.
 *
 * WHY THIS EXISTS
 * ---------------
 * The census concluded "srmech_chain_run rejects 18/18 cascade-catalog chains".
 * The single biggest way that conclusion could be WRONG is a HARNESS artifact:
 * an under-sized caller arena, an under-sized out buffer, or a wrong entry
 * point, mis-read as the C grammar declining the chain.  The census guarded it
 * with two synthetic positive controls at ONE arena size (the shipped
 * convention).  This driver hardens the guard two ways it did not:
 *
 *   1. IT IS A DIFFERENT ROUTE.  ctypes, srmech.cascade.compose and the whole
 *      Python layer are absent.  If the rc reproduces here, no Python-side
 *      marshalling bug can be producing it.
 *   2. IT SWEEPS THE ARENA.  Each chain is run at 1x / 4x / 16x the arena the
 *      shipped srmech_chain_run_arena_bytes() recommends, and at a 1 MiB out
 *      buffer.  An OVERFLOW-shaped harness fault MUST move when the arena
 *      grows.  A grammar verdict CANNOT.  rc invariant across the sweep is
 *      therefore positive evidence that the verdict is the grammar's.
 *
 * EXPECTED (predicted by hand-reading c/src/srmech_compose_run.c):
 *   CONTROL rational_add       -> srmech_chain_run rc=0  (SRMECH_OK)
 *   cyclic_gcd.default         -> run rc=5  NOT_IMPL   :616 cr_dispatch
 *                                 parse rc=0 (all-plain steps pass co_build_step)
 *   net_chirality.default      -> run rc=2  BAD_INPUT  :723 (fold step, no "op")
 *                                 parse rc=2
 *   octonion_dft.default       -> run rc=5  NOT_IMPL   :616
 *                                 parse rc=2 (map/fold + @idx/@bind)
 *
 * Build (from c/):
 *   cc -std=c17 -Wall -Wextra -Wpedantic -O2 -Iinclude \
 *      ../notes/_1653_adv_barec_chain_probe.c build/libsrmech.a -o build/adv1653
 * Run (from notes/):
 *   ../c/build/adv1653
 *
 * JPL Power-of-Ten discipline:
 *   Rule 1  no goto, no recursion (every function is a leaf or calls only
 *           libsrmech / helpers below it; the call graph is a DAG of depth 3).
 *   Rule 2  every loop has a compile-time bound.
 *   Rule 3  no malloc / free — the arena and the file buffers are file-scope
 *           static storage, carved by the caller and handed to libsrmech
 *           (caller-arena contract).
 *   Rule 4  every function <= 60 lines.
 *   Rule 5  >= 2 asserts per function.
 *   Rule 8  no multi-line macros.
 */

#include <assert.h>
#include <stdio.h>
#include <stddef.h>
#include <string.h>

#include "srmech.h"

#define ADV_FILE_CAP   (size_t)65536
#define ADV_ARENA_CAP  (size_t)33554432      /* 32 MiB, static BSS */
#define ADV_OUT_CAP    (size_t)1048576       /* 1 MiB */
#define ADV_N_MULT     3

static char adv_chain[ADV_FILE_CAP];
static char adv_ctx[ADV_FILE_CAP];
static unsigned char adv_arena[ADV_ARENA_CAP];
static char adv_out[ADV_OUT_CAP];

static const size_t adv_mult[ADV_N_MULT] = { 1u, 4u, 16u };

/* Read a whole file into `buf`. Returns 1 on success, 0 on failure. */
static int adv_read(const char *path, char *buf, size_t cap, size_t *len)
{
    FILE *fh;
    size_t n;
    assert(path != NULL && buf != NULL && len != NULL);
    assert(cap > 0u);
    *len = 0u;
    fh = fopen(path, "rb");
    if (fh == NULL) { return 0; }
    n = fread(buf, 1u, cap, fh);
    (void)fclose(fh);
    if (n == 0u || n >= cap) { return 0; }
    *len = n;
    return 1;
}

/* One srmech_chain_run call at a given arena multiple. Prints the rc row. */
static void adv_run_at(const char *label, size_t mult,
                       const char *cj, size_t cl, const char *xj, size_t xl)
{
    size_t base, ws, out_len = 0u;
    srmech_status_t rc;
    assert(label != NULL && cj != NULL);
    assert(mult > 0u && cl > 0u);
    base = srmech_chain_run_arena_bytes(cl, xl);
    ws = base * mult;
    if (ws > ADV_ARENA_CAP) { ws = ADV_ARENA_CAP; }
    memset(adv_arena, 0, ws);
    rc = srmech_chain_run(cj, cl, xj, xl, adv_arena, ws,
                          adv_out, ADV_OUT_CAP, &out_len);
    printf("  run   %-30s arena=%2zux (%9zu B) out_cap=%7zu -> rc=%d out_len=%zu\n",
           label, mult, ws, ADV_OUT_CAP, (int)rc, out_len);
}

/* srmech_chain_spec_parse at the shipped arena, then at 16x. */
static void adv_parse(const char *label, const char *cj, size_t cl)
{
    size_t base, ws, out_len;
    size_t i;
    srmech_status_t rc;
    assert(label != NULL && cj != NULL);
    assert(cl > 0u);
    base = srmech_chain_spec_parse_arena_bytes(cl);
    for (i = 0u; i < ADV_N_MULT; i++) {
        ws = base * adv_mult[i];
        if (ws > ADV_ARENA_CAP) { ws = ADV_ARENA_CAP; }
        out_len = 0u;
        memset(adv_arena, 0, ws);
        rc = srmech_chain_spec_parse(cj, cl, adv_arena, ws,
                                     adv_out, ADV_OUT_CAP, &out_len);
        printf("  parse %-30s arena=%2zux (%9zu B) -> rc=%d out_len=%zu\n",
               label, adv_mult[i], ws, (int)rc, out_len);
    }
}

/* The POSITIVE CONTROL: a chain the C run loop must accept, driven through the
 * exact same buffers.  If this is rc=0 and the real chains are not, the
 * difference is the chain, not the driver. */
static void adv_control(void)
{
    static const char cj[] =
        "{\"name\":\"ctl.literal\",\"summary\":\"positive control\","
        "\"returns\":\"tuple[int, int]\",\"on_error\":\"raise\","
        "\"steps\":[{\"class\":\"N\",\"op\":\"rational_add\","
        "\"args\":{\"a\":[1,2],\"b\":[1,3]}}]}";
    static const char xj[] = "{\"row\":null,\"inputs\":{}}";
    size_t cl = sizeof(cj) - 1u, xl = sizeof(xj) - 1u;
    size_t i;
    assert(cl > 0u);
    assert(xl > 0u);
    printf("CONTROL rational_add (literal args) -- MUST be rc=0\n");
    for (i = 0u; i < ADV_N_MULT; i++) {
        adv_run_at("ctl.literal", adv_mult[i], cj, cl, xj, xl);
    }
    adv_parse("ctl.literal", cj, cl);
    { size_t out_len = 0u;
      srmech_status_t rc;
      memset(adv_arena, 0, ADV_ARENA_CAP);
      rc = srmech_chain_run(cj, cl, xj, xl, adv_arena, ADV_ARENA_CAP,
                            adv_out, ADV_OUT_CAP, &out_len);
      printf("  CONTROL out (32 MiB arena, rc=%d): %.*s\n",
             (int)rc, (int)out_len, adv_out); }
}

/* One real descriptor chain: sweep the arena on run (with proof-case ctx AND
 * with the empty structure-probe ctx), then parse. */
static int adv_chain_case(const char *base_dir, const char *base_name,
                          const char *ctx_suffix)
{
    char p_chain[512], p_ctx[512];
    size_t cl = 0u, xl = 0u, i;
    assert(base_dir != NULL && base_name != NULL);
    assert(ctx_suffix != NULL);
    (void)snprintf(p_chain, sizeof(p_chain), "%s/%s.chain.json",
                   base_dir, base_name);
    (void)snprintf(p_ctx, sizeof(p_ctx), "%s/%s.%s.json",
                   base_dir, base_name, ctx_suffix);
    if (!adv_read(p_chain, adv_chain, ADV_FILE_CAP, &cl)) {
        printf("  UNREADABLE %s\n", p_chain);
        return 0;
    }
    if (!adv_read(p_ctx, adv_ctx, ADV_FILE_CAP, &xl)) {
        printf("  UNREADABLE %s\n", p_ctx);
        return 0;
    }
    printf("%s  [ctx=%s]  chain_len=%zu ctx_len=%zu\n",
           base_name, ctx_suffix, cl, xl);
    for (i = 0u; i < ADV_N_MULT; i++) {
        adv_run_at(base_name, adv_mult[i], adv_chain, cl, adv_ctx, xl);
    }
    return 1;
}

/* Drive one base name: run (proof ctx + probe ctx) then parse. */
static void adv_one(const char *dir, const char *name)
{
    size_t cl = 0u;
    char p[512];
    assert(dir != NULL);
    assert(name != NULL);
    printf("\n");
    (void)adv_chain_case(dir, name, "ctx");
    (void)adv_chain_case(dir, name, "probe");
    (void)snprintf(p, sizeof(p), "%s/%s.chain.json", dir, name);
    if (adv_read(p, adv_chain, ADV_FILE_CAP, &cl)) {
        adv_parse(name, adv_chain, cl);
    }
}

int main(int argc, char **argv)
{
    static const char *names[3] = { "cyclic_gcd__default",
                                    "net_chirality__default",
                                    "octonion_dft__default" };
    const char *dir = "_1653_adv_barec";
    int i;
    size_t k;
    assert(argc >= 1);
    assert(argv != NULL);
    if (argc > 1) { dir = argv[1]; }
    printf("srmech C library version=%s ABI=%d\n",
           srmech_version(), (int)srmech_abi_version());
    printf("STATUS: 0=OK 1=NULL_ARG 2=BAD_INPUT 3=IO 4=OVERFLOW "
           "5=NOT_IMPL 6=INTERNAL 8=LIMIT\n\n");
    adv_control();
    if (argc > 2) {
        printf("\nSTEP-FORM PROBES (bare C, arena swept 1x/4x/16x)\n");
        for (i = 2; i < argc; i++) { adv_one(dir, argv[i]); }
        return 0;
    }
    printf("\nREAL cascade-catalog chains (bare C, arena swept 1x/4x/16x)\n");
    for (k = 0u; k < 3u; k++) { adv_one(dir, names[k]); }
    return 0;
}
