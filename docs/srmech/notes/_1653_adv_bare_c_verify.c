/*
 * _1653_adv_bare_c_verify.c — ADVERSARIAL cross-check driver for gh #1653.
 *
 * Reproduces the census script's C verdicts with NEITHER ctypes NOR CPython
 * anywhere in the path: links the STATIC c/build/libsrmech.a directly and
 * calls srmech_chain_spec_parse / srmech_dsl_chain_run on JSON read from a
 * file.  If the bare-C status differs from the ctypes status, the census
 * harness was the cause and its rejection figures are artefacts.
 *
 * JPL Power-of-Ten discipline: no recursion, no malloc/free, every buffer a
 * file-scope caller arena, every function <= 60 lines with >= 2 asserts.
 *
 * Build (from docs/srmech/c):
 *   cc -std=c17 -O2 -Wall -Wextra -Iinclude \
 *      -o <scratch>/adv_verify ../notes/_1653_adv_bare_c_verify.c \
 *      build/libsrmech.a
 *
 * Usage:
 *   adv_verify spec <chain.json>
 *   adv_verify dsl  <chain.json> <input.json>
 */

#include <assert.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>

#include "srmech.h"

#define SRC_CAP   (1u << 20)   /* 1 MiB source buffer per file */
#define ARENA_CAP (48u << 20)  /* 48 MiB caller arena          */
#define OUT_CAP   (1u << 20)   /* 1 MiB canonical-JSON output  */

static char g_chain[SRC_CAP];
static char g_input[SRC_CAP];
static char g_arena[ARENA_CAP];
static char g_out[OUT_CAP];

/* Read a whole file into buf; 1 on success, 0 on any failure. */
static int slurp(const char *path, char *buf, size_t cap, size_t *out_len)
{
    assert(path != NULL);
    assert(buf != NULL && out_len != NULL);
    FILE *fh = fopen(path, "rb");
    if (fh == NULL) { return 0; }
    size_t n = fread(buf, 1u, cap, fh);
    int bad = ferror(fh);
    (void)fclose(fh);
    if (bad != 0 || n == 0u || n >= cap) { return 0; }
    *out_len = n;
    return 1;
}

/* Print a status line plus at most 96 bytes of the canonical output. */
static void report(const char *tag, const char *path, int rc, size_t olen)
{
    assert(tag != NULL);
    assert(path != NULL);
    size_t show = (olen < 96u) ? olen : 96u;
    printf("%-4s rc=%d  %-46s out[%zu]=", tag, rc, path, olen);
    for (size_t i = 0u; i < show; i++) {
        int c = (unsigned char)g_out[i];
        (void)putchar((c >= 32 && c < 127) ? c : '.');
    }
    (void)putchar('\n');
}

/* srmech_chain_spec_parse on one file. Returns the srmech status, or -1. */
static int do_spec(const char *path)
{
    assert(path != NULL);
    assert(sizeof g_arena > 0u);
    size_t clen = 0u;
    if (!slurp(path, g_chain, SRC_CAP, &clen)) {
        printf("SPEC SLURP-FAIL %s\n", path);
        return -1;
    }
    size_t need = srmech_chain_spec_parse_arena_bytes(clen);
    if (need > ARENA_CAP) {
        printf("SPEC ARENA-SHORT need=%zu cap=%u %s\n", need,
               (unsigned)ARENA_CAP, path);
        return -1;
    }
    size_t olen = 0u;
    srmech_status_t st = srmech_chain_spec_parse(g_chain, clen, g_arena, need,
                                                g_out, OUT_CAP, &olen);
    report("SPEC", path, (int)st, olen);
    return (int)st;
}

/* srmech_dsl_chain_run on one chain file + one F1 input-descriptor file. */
static int do_dsl(const char *cpath, const char *ipath)
{
    assert(cpath != NULL);
    assert(ipath != NULL);
    size_t clen = 0u;
    size_t ilen = 0u;
    if (!slurp(cpath, g_chain, SRC_CAP, &clen) ||
        !slurp(ipath, g_input, SRC_CAP, &ilen)) {
        printf("DSL  SLURP-FAIL %s / %s\n", cpath, ipath);
        return -1;
    }
    size_t need = srmech_dsl_chain_run_arena_bytes(clen, ilen);
    if (need > ARENA_CAP) {
        printf("DSL  ARENA-SHORT need=%zu cap=%u %s\n", need,
               (unsigned)ARENA_CAP, cpath);
        return -1;
    }
    size_t olen = 0u;
    srmech_status_t st = srmech_dsl_chain_run(g_chain, clen, g_input, ilen,
                                             g_arena, need, g_out, OUT_CAP,
                                             &olen);
    report("DSL", cpath, (int)st, olen);
    return (int)st;
}

/* srmech_chain_run on one chain file + one ctx file. The SURFACE-A run loop:
 * tests directly whether the C runner declines a C-PARSE-ACCEPTED chain, so the
 * "0 of 20 C-run" figure cannot be a Python-side-gate artefact. */
static int do_run(const char *cpath, const char *xpath)
{
    assert(cpath != NULL);
    assert(xpath != NULL);
    size_t clen = 0u;
    size_t xlen = 0u;
    if (!slurp(cpath, g_chain, SRC_CAP, &clen) ||
        !slurp(xpath, g_input, SRC_CAP, &xlen)) {
        printf("RUN  SLURP-FAIL %s / %s\n", cpath, xpath);
        return -1;
    }
    size_t need = srmech_chain_run_arena_bytes(clen, xlen);
    if (need > ARENA_CAP) {
        printf("RUN  ARENA-SHORT need=%zu cap=%u %s\n", need,
               (unsigned)ARENA_CAP, cpath);
        return -1;
    }
    size_t olen = 0u;
    srmech_status_t st = srmech_chain_run(g_chain, clen, g_input, xlen,
                                         g_arena, need, g_out, OUT_CAP, &olen);
    report("RUN", cpath, (int)st, olen);
    return (int)st;
}

int main(int argc, char **argv)
{
    assert(argv != NULL);
    assert(argc >= 0);
    if (argc >= 2 && strcmp(argv[1], "version") == 0) {
        printf("libsrmech %s abi=%d\n", srmech_version(), srmech_abi_version());
        return 0;
    }
    if (argc == 4 && strcmp(argv[1], "run") == 0) {
        return (do_run(argv[2], argv[3]) == 0) ? 0 : 1;
    }
    if (argc == 3 && strcmp(argv[1], "spec") == 0) {
        return (do_spec(argv[2]) == 0) ? 0 : 1;
    }
    if (argc == 4 && strcmp(argv[1], "dsl") == 0) {
        return (do_dsl(argv[2], argv[3]) == 0) ? 0 : 1;
    }
    printf("usage: adv_verify {version|spec <chain.json>"
           "|dsl <chain.json> <input.json>}\n");
    return 2;
}
