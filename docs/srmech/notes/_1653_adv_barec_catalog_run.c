/*
 * _1653_adv_barec_catalog_run.c — close the ONE axis the census admits it did
 * not measure: srmech_catalog_run_chain (srmech.h:3384), the C peer of
 * srmech.amsc.catalog.run_catalog_chain.
 *
 * The census measured srmech_chain_catalog_parse with a
 * {"chain_schema_version":1,"operator_chain":[chain]} wrapper, then declined to
 * measure srmech_catalog_run_chain on the grounds that the wrapper "would have
 * been my invention".  But the wrapper it declined to reuse is the wrapper it
 * had ALREADY built for the parse axis — so the gap is closable at zero
 * invention cost.  This driver closes it, in bare C.
 *
 * The point is falsification: if srmech_catalog_run_chain ACCEPTED chains that
 * srmech_chain_run rejects, "the C projection runs 0 of 18" would be FALSE —
 * there would exist a shipped C entry point that runs them.
 *
 * Expected (both entry points share cr_run_and_write / cr_run_steps, so the
 * verdicts must agree):
 *   CONTROL rational_add  -> rc=0
 *   cyclic_gcd            -> rc=5   NOT_IMPL  :616
 *   net_chirality         -> rc=2   BAD_INPUT :723
 *   octonion_dft          -> rc=5   NOT_IMPL  :616
 *
 * Build (from c/):
 *   cc -std=c17 -Wall -Wextra -Wpedantic -O2 -Iinclude \
 *      ../notes/_1653_adv_barec_catalog_run.c build/libsrmech.a -o build/adv1653cat
 *
 * JPL Power-of-Ten: no goto, no recursion, no malloc (file-scope static
 * caller-arena), every function <= 60 lines and >= 2 asserts, no multi-line
 * macros, every loop compile-time bounded.
 */

#include <assert.h>
#include <stdio.h>
#include <stddef.h>
#include <string.h>

#include "srmech.h"

#define CAT_FILE_CAP   (size_t)65536
#define CAT_ARENA_CAP  (size_t)33554432
#define CAT_OUT_CAP    (size_t)1048576
#define CAT_N_MULT     3

static char cat_buf[CAT_FILE_CAP];
static char cat_ctx[CAT_FILE_CAP];
static unsigned char cat_arena[CAT_ARENA_CAP];
static char cat_out[CAT_OUT_CAP];

static const size_t cat_mult[CAT_N_MULT] = { 1u, 4u, 16u };

/* Read a whole file into `buf`. 1 on success, 0 on failure. */
static int cat_read(const char *path, char *buf, size_t cap, size_t *len)
{
    FILE *fh;
    size_t n;
    assert(path != NULL && buf != NULL);
    assert(len != NULL && cap > 0u);
    *len = 0u;
    fh = fopen(path, "rb");
    if (fh == NULL) { return 0; }
    n = fread(buf, 1u, cap, fh);
    (void)fclose(fh);
    if (n == 0u || n >= cap) { return 0; }
    *len = n;
    return 1;
}

/* srmech_catalog_run_chain at one arena multiple. */
static void cat_run_at(const char *chain_name, size_t mult,
                       size_t cl, size_t xl)
{
    size_t base, ws, out_len = 0u, nl;
    srmech_status_t rc;
    assert(chain_name != NULL);
    assert(mult > 0u && cl > 0u);
    nl = strlen(chain_name);
    base = srmech_catalog_run_chain_arena_bytes(cl, xl);
    ws = base * mult;
    if (ws > CAT_ARENA_CAP) { ws = CAT_ARENA_CAP; }
    memset(cat_arena, 0, ws);
    rc = srmech_catalog_run_chain(cat_buf, cl, chain_name, nl,
                                 cat_ctx, xl, cat_arena, ws,
                                 cat_out, CAT_OUT_CAP, &out_len);
    printf("  catalog_run %-26s arena=%2zux (%9zu B) -> rc=%d out_len=%zu",
           chain_name, mult, ws, (int)rc, out_len);
    if (rc == 0) { printf("  out=%.*s", (int)out_len, cat_out); }
    printf("\n");
}

/* One catalog wrapper file + its ctx, swept over the arena multiples. */
static void cat_one(const char *dir, const char *base, const char *chain_name)
{
    char p_cat[512], p_ctx[512];
    size_t cl = 0u, xl = 0u, i;
    assert(dir != NULL && base != NULL);
    assert(chain_name != NULL);
    (void)snprintf(p_cat, sizeof(p_cat), "%s/%s.catalog.json", dir, base);
    (void)snprintf(p_ctx, sizeof(p_ctx), "%s/%s.ctx.json", dir, base);
    if (!cat_read(p_cat, cat_buf, CAT_FILE_CAP, &cl)) {
        printf("  UNREADABLE %s\n", p_cat);
        return;
    }
    if (!cat_read(p_ctx, cat_ctx, CAT_FILE_CAP, &xl)) {
        printf("  UNREADABLE %s\n", p_ctx);
        return;
    }
    printf("%s  cat_len=%zu ctx_len=%zu  chain_name=%s\n",
           base, cl, xl, chain_name);
    for (i = 0u; i < CAT_N_MULT; i++) {
        cat_run_at(chain_name, cat_mult[i], cl, xl);
    }
}

int main(int argc, char **argv)
{
    static const char *bases[4] = { "ctl_catalog", "cyclic_gcd__default",
                                    "net_chirality__default",
                                    "octonion_dft__default" };
    static const char *cnames[4] = { "ctl.literal", "cyclic_gcd.default",
                                     "net_chirality.default",
                                     "octonion_dft.default" };
    const char *dir = "_1653_adv_barec";
    size_t i;
    assert(argc >= 1);
    assert(argv != NULL);
    if (argc > 1) { dir = argv[1]; }
    printf("srmech C library version=%s ABI=%d\n",
           srmech_version(), (int)srmech_abi_version());
    printf("srmech_catalog_run_chain -- the axis the census skipped\n");
    printf("STATUS: 0=OK 2=BAD_INPUT 4=OVERFLOW 5=NOT_IMPL\n\n");
    for (i = 0u; i < 4u; i++) {
        cat_one(dir, bases[i], cnames[i]);
        printf("\n");
    }
    return 0;
}
