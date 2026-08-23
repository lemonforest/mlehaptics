/* test_srmech_cascade_toml_host.c — rc452 (`#T1166`), gh #1653: the Surface-A
 * CONFIG-DRIVEN bare-C host proof — the descriptor FILE drives, not a
 * transcription of it.
 *
 * WHY THIS FILE EXISTS WHEN test_srmech_chain_run.c ALREADY SAYS "bare-C host
 * proof". That file's chains are hand-transcribed JSON string literals: it
 * contains no fopen and no TOML, so it proves the INTERPRETER computes with no
 * Python present — a real claim, and not the config-driven one. gh #1653
 * mandate clause 1 says a host without Python can drive a cascade FROM A
 * DESCRIPTOR; through this rc no shipped C entry point ever ingested a
 * Surface-A cascade-catalog TOML — every catalog/chain C API took JSON that
 * Python produced. So the config-driven half of the mandate was unproven even
 * for the chains that pass. This file is that proof:
 *
 *   fopen(the SHIPPED cascade_catalog/<name>.toml)
 *     -> srmech_toml_parse            (srmech's own C TOML parser)
 *     -> navigate to [[cascade.chain]] / [[cascade.chain.proof_cases]]
 *     -> transcode the chain + the case inputs to the chain-run JSON grammar
 *        (srmech_json builder + canonical writer — all shipped C symbols)
 *     -> srmech_chain_run
 *     -> strcmp against hand-derived expected wire bytes.
 *
 * NO PYTHON anywhere in the acceptance path — not even to generate the
 * expected bytes: every `expect` literal below is derived by hand from the
 * op contracts in the row's `why` string, and the derivations were
 * cross-checked against a live C run before being frozen here.
 *
 * ⚠️ THE EXPECTED BYTES ARE LITERALS, NOT AN ORACLE CALL, on purpose. The
 * shared-reader lesson of this arc: `resolve_chain` runs the native path first
 * and returns `_reconstruct_value`'s output, so a C-vs-Python comparison
 * cannot detect anything both projections route through. A hand-written
 * descriptor can. (Same stance as the rc452 depth-spine checks in
 * test_srmech_chain_run.c.)
 *
 * The C TOML parser's fitness for this corpus is not assumed either: parse
 * parity with the tomllib oracle over EVERY shipped descriptor is proven by
 * tests/test_toml_dedup_parity_rc400.py; the rc420 special-float arm exists
 * precisely because magnitude.toml carries `x = nan` / `x = inf` proof cases
 * (this host parses that whole file, then drives its finite case 0).
 *
 * NO malloc (JPL Rule 3 spirit — every buffer is static or stack); runtime
 * if-guards, never assert (Release/NDEBUG strips assert, and this joins the
 * -Werror / /WX pedantic matrix). License: MIT.
 */
#include "srmech.h"

#include <stdio.h>
#include <string.h>

#ifndef SRMECH_CASCADE_CATALOG_DIR
#error "SRMECH_CASCADE_CATALOG_DIR must be defined (CMakeLists.txt passes it)"
#endif

static int g_pass = 0;
static int g_fail = 0;

static void check(int cond, const char *desc)
{
    if (cond) { g_pass++; printf("  PASS  %s\n", desc); }
    else      { g_fail++; printf("  FAIL  %s\n", desc); }
}

/* ── static arenas — a bare-C host has no allocator, which is the point ─── */
static unsigned char g_toml_ws[8u << 20];   /* TOML parse tree               */
static unsigned char g_build_ws[1u << 20];  /* JSON builder tree             */
static unsigned char g_write_ws[1u << 20];  /* canonical-writer sort scratch */
static unsigned char g_run_ws[8u << 20];    /* chain-run arena (measured:    */
                                            /* best_rational_signed ~4.3 MiB)*/
static char g_file[262144];                 /* biggest descriptor is ~23 KiB */
static char g_chain[16384];
static char g_ctx[8192];
static char g_out[65536];

/* ── TOML -> JSON transcode of a FINITE subtree ──────────────────────────
 * Depth-capped recursion (a test file is outside the JPL src audit; the cap
 * makes the recursion bounded the same way the library's own toml_to_json
 * bounds its). Child fan-out is capped at 24 — the widest subtree this host
 * transcodes is a 6-element steps array / a 4-key inputs table — and the cap
 * FAILS the row rather than truncating: a truncating walker would return a
 * well-formed descriptor holding less than the file said, which is a silent
 * wrong answer of exactly the class this arc exists to close. */
#define T2J_MAX_DEPTH 12u
#define T2J_MAX_KIDS  24u

static srmech_json_value_t *t2j(srmech_json_builder_t *bd,
                                const srmech_toml_value_t *tv,
                                unsigned depth)
{
    srmech_json_value_t *kids[T2J_MAX_KIDS];
    const char *keys[T2J_MAX_KIDS];
    uint32_t i, n;

    if (tv == NULL || depth > T2J_MAX_DEPTH) { return NULL; }
    switch (tv->type) {
    case SRMECH_TOML_STRING:
        return srmech_json_new_string(bd, tv->u.str.ptr, tv->u.str.len);
    case SRMECH_TOML_INT:
        return srmech_json_new_int(bd, tv->u.i);
    case SRMECH_TOML_FLOAT:
        return srmech_json_new_double(bd, tv->u.f);
    case SRMECH_TOML_BOOL:
        return srmech_json_new_bool(bd, tv->u.b);
    case SRMECH_TOML_ARRAY:
        n = tv->u.arr.n;
        if (n > T2J_MAX_KIDS) { return NULL; }
        for (i = 0u; i < n; i++) {
            kids[i] = t2j(bd, tv->u.arr.items[i], depth + 1u);
            if (kids[i] == NULL) { return NULL; }
        }
        return srmech_json_new_array(bd, kids, n);
    case SRMECH_TOML_TABLE:
        n = tv->u.tbl.n;
        if (n > T2J_MAX_KIDS) { return NULL; }
        for (i = 0u; i < n; i++) {
            keys[i] = tv->u.tbl.keys[i];
            kids[i] = t2j(bd, tv->u.tbl.vals[i], depth + 1u);
            if (kids[i] == NULL) { return NULL; }
        }
        return srmech_json_new_object(bd, keys, kids, n);
    }
    return NULL;
}

/* Serialise a built tree to canonical JSON in dst; 0 on success. */
static int write_json(const srmech_json_value_t *root,
                      char *dst, size_t dst_cap, size_t *out_len)
{
    size_t need = srmech_json_write_arena_bytes(root);
    if (need > sizeof(g_write_ws)) { return -1; }
    if (srmech_json_write_ws(root, dst, dst_cap - 1u, out_len,
                             g_write_ws, need) != SRMECH_OK) { return -1; }
    dst[*out_len] = '\0';
    return 0;
}

static const srmech_toml_value_t *arr_item(const srmech_toml_value_t *v,
                                           uint32_t i)
{
    if (v == NULL || v->type != SRMECH_TOML_ARRAY || i >= v->u.arr.n) {
        return NULL;
    }
    return v->u.arr.items[i];
}

static long read_file(const char *fname, char *dst, size_t cap)
{
    char path[1024];
    FILE *f;
    size_t got;
    int n = snprintf(path, sizeof(path), "%s/%s",
                     SRMECH_CASCADE_CATALOG_DIR, fname);
    if (n <= 0 || (size_t)n >= sizeof(path)) { return -1L; }
    f = fopen(path, "rb");
    if (f == NULL) { printf("  (cannot open %s)\n", path); return -1L; }
    got = fread(dst, 1u, cap, f);
    fclose(f);
    if (got == 0u || got >= cap) { return -1L; }
    return (long)got;
}

/* One row: open the descriptor, parse, extract, transcode, run, compare.
 * Distinct return codes so the negative controls can pin WHICH stage refused:
 *   0 = wire bytes match          4 = builder / writer failure
 *   1 = file / parse failure      5 = srmech_chain_run non-OK
 *   2 = navigation failure        6 = wire bytes MISMATCH (printed)
 *   3 = step-count mismatch                                               */
static int run_row(const char *fname, uint32_t case_idx, uint32_t n_steps,
                   const char *expect)
{
    const srmech_toml_value_t *root, *cascade, *chain, *entry, *steps;
    const srmech_toml_value_t *cases, *pcase, *inputs;
    srmech_json_builder_t bd;
    srmech_json_value_t *jchain, *jctx, *vals[8];
    const char *keys[8];
    srmech_toml_value_t *parsed = NULL;
    size_t clen = 0u, xlen = 0u, olen = 0u, need;
    uint32_t i, nkeys;
    long flen = read_file(fname, g_file, sizeof(g_file));

    if (flen <= 0L) { return 1; }
    need = srmech_toml_parse_arena_bytes((size_t)flen);
    if (need > sizeof(g_toml_ws)) { return 1; }
    if (srmech_toml_parse(g_file, (size_t)flen, g_toml_ws, need,
                          &parsed) != SRMECH_OK) { return 1; }
    root = parsed;

    cascade = srmech_toml_table_get(root, "cascade");
    chain   = srmech_toml_table_get(cascade, "chain");
    entry   = arr_item(chain, 0u);      /* the single [[cascade.chain]]     */
    steps   = srmech_toml_table_get(entry, "steps");
    cases   = srmech_toml_table_get(entry, "proof_cases");
    pcase   = arr_item(cases, case_idx);
    inputs  = srmech_toml_table_get(pcase, "inputs");
    if (steps == NULL || steps->type != SRMECH_TOML_ARRAY ||
        inputs == NULL || inputs->type != SRMECH_TOML_TABLE) { return 2; }
    /* The DECLARED step count, read from the FILE — pins that the file
     * content (not an embedded literal) supplied the chain shape. */
    if (steps->u.arr.n != n_steps) { return 3; }

    /* chain JSON: the entry FILTERED to the runner's keys — the same
     * projection srmech.dsl._cascade_chain applies (`_chain_only`). */
    if (srmech_json_builder_init(&bd, g_build_ws,
                                 sizeof(g_build_ws)) != SRMECH_OK) { return 4; }
    nkeys = 0u;
    if (entry != NULL && entry->type == SRMECH_TOML_TABLE) {
        for (i = 0u; i < entry->u.tbl.n && nkeys < 8u; i++) {
            const char *k = entry->u.tbl.keys[i];
            if (strcmp(k, "chain_schema_version") == 0 ||
                strcmp(k, "name") == 0 || strcmp(k, "on_error") == 0 ||
                strcmp(k, "steps") == 0) {
                keys[nkeys] = k;
                vals[nkeys] = t2j(&bd, entry->u.tbl.vals[i], 0u);
                if (vals[nkeys] == NULL) { return 4; }
                nkeys++;
            }
        }
    }
    jchain = srmech_json_new_object(&bd, keys, vals, nkeys);
    if (jchain == NULL || bd.failed) { return 4; }
    if (write_json(jchain, g_chain, sizeof(g_chain), &clen) != 0) { return 4; }

    /* ctx JSON: {"inputs": <the proof case's inputs table>} */
    keys[0] = "inputs";
    vals[0] = t2j(&bd, inputs, 0u);
    if (vals[0] == NULL) { return 4; }
    jctx = srmech_json_new_object(&bd, keys, vals, 1u);
    if (jctx == NULL || bd.failed) { return 4; }
    if (write_json(jctx, g_ctx, sizeof(g_ctx), &xlen) != 0) { return 4; }

    need = srmech_chain_run_arena_bytes(clen, xlen);
    if (need > sizeof(g_run_ws)) { return 5; }
    if (srmech_chain_run(g_chain, clen, g_ctx, xlen, g_run_ws, need,
                         g_out, sizeof(g_out) - 1u, &olen) != SRMECH_OK) {
        return 5;
    }
    g_out[olen] = '\0';
    if (strcmp(g_out, expect) != 0) {
        printf("  (wire mismatch for %s case %u\n   expect %s\n   got    %s)\n",
               fname, (unsigned)case_idx, expect, g_out);
        return 6;
    }
    return 0;
}

/* The 11 chains that run in C at rc452 — every one driven FROM ITS SHIPPED
 * DESCRIPTOR FILE, one hand-derived proof case each. `n_steps` is the
 * declared top-level [[cascade.chain.steps]] count the file must yield. */
typedef struct {
    const char *fname;
    uint32_t    case_idx;
    uint32_t    n_steps;
    const char *expect;
    const char *why;
} row_t;

static const row_t ROWS[] = {
    { "cyclic_gcd.toml", 0u, 1u, "{\"k\": \"i\", \"v\": \"6\"}",
      "gcd(12, 18) = 6 (Euclid)" },
    { "cyclic_mod_add.toml", 0u, 1u, "{\"k\": \"i\", \"v\": \"3\"}",
      "(7 + 8) mod 12 = 15 mod 12 = 3" },
    { "cyclic_mod_mul.toml", 0u, 1u, "{\"k\": \"i\", \"v\": \"8\"}",
      "(7 * 8) mod 12 = 56 mod 12 = 8" },
    { "cyclic_mod_mul_wide.toml", 1u, 1u, "{\"k\": \"i\", \"v\": \"2\"}",
      "with n = 2^63-1: (n-1)(n-2) === (-1)(-2) = 2 (mod n) — the WIDE path, "
      "unreachable through a 64-bit product" },
    { "cyclic_mod_inv.toml", 0u, 1u, "{\"k\": \"i\", \"v\": \"5\"}",
      "3 * 5 = 15 === 1 (mod 7), so mod_inv(3, 7) = 5" },
    { "cyclic_mod_pow.toml", 0u, 1u, "{\"k\": \"i\", \"v\": \"7\"}",
      "3^7 = 2187, 2187 mod 10 = 7" },
    { "magnitude.toml", 0u, 2u, "{\"k\": \"f\", \"v\": 3.5}",
      "pin_slot_at_zero(-3.5) = (-1, 3.5); reorient(3.5, +1) = 3.5 — the "
      "Class-K/Class-C decomposition, never an ALU abs" },
    { "net_chirality.toml", 5u, 1u, "{\"k\": \"i\", \"v\": \"-1\"}",
      "fold orientation_compose over [1, -1, 1] from seed +1: product -1" },
    { "chiral_dual.toml", 0u, 3u,
      "{\"k\": \"l\", \"v\": [{\"k\": \"f\", \"v\": 11.0}, "
      "{\"k\": \"f\", \"v\": 11.0}, {\"k\": \"f\", \"v\": 14.0}]}",
      "flip([1,2,3]) = [3,2,1]; circular autocorr = [14, 11, 11] "
      "(9+4+1; 6+2+3; 3+6+2); flip back = [11, 11, 14]" },
    { "best_rational_signed.toml", 0u, 6u,
      "{\"k\": \"t\", \"v\": [{\"k\": \"i\", \"v\": \"22\"}, "
      "{\"k\": \"i\", \"v\": \"7\"}]}",
      "pi -> (22, 7): the six-step K/K/N/N/C/B cascade, integer-carried "
      "through the Class-C tail, crossing as the rc451 TUPLE kind" },
    { "autocorrelation.toml", 2u, 2u,
      "{\"k\": \"l\", \"v\": [{\"k\": \"f\", \"v\": 14.25}, "
      "{\"k\": \"f\", \"v\": -6.0}, {\"k\": \"f\", \"v\": 4.0}, "
      "{\"k\": \"f\", \"v\": -6.0}]}",
      "circular autocorr of [1, -2, 3, 0.5]: r0 = 1+4+9+0.25 = 14.25; "
      "r1 = -2-6+1.5+0.5 = -6; r2 = 3-1+3-1 = 4; r3 = 0.5-2-6+1.5 = -6 "
      "(all products exactly representable, so the Neumaier compensation "
      "contributes nothing and the values are exact). Runs the NESTED map "
      "bodies — [[cascade.chain.steps.body.body]] — from the file" },
};

int main(void)
{
    size_t r;
    int rc;
    srmech_toml_value_t *parsed = NULL;

    printf("== Surface-A cascade-catalog TOML -> bare-C chain run "
           "(gh #1653, rc452 `#T1166`) ==\n");

    /* ── the 11 config-driven rows ──────────────────────────────────────── */
    for (r = 0u; r < sizeof(ROWS) / sizeof(ROWS[0]); r++) {
        char desc[512];
        rc = run_row(ROWS[r].fname, ROWS[r].case_idx, ROWS[r].n_steps,
                     ROWS[r].expect);
        snprintf(desc, sizeof(desc), "%s case %u from the FILE -> rc %d — %s",
                 ROWS[r].fname, (unsigned)ROWS[r].case_idx, rc, ROWS[r].why);
        check(rc == 0, desc);
    }

    /* ── negative controls: every refusal stage can actually refuse ─────── */

    /* The comparator can fail: a deliberately-wrong expected wire must be
     * reported as a MISMATCH (6), not swallowed. Without this, 11 green rows
     * are indistinguishable from a strcmp that cannot return nonzero. */
    rc = run_row("cyclic_gcd.toml", 0u, 1u, "{\"k\": \"i\", \"v\": \"7\"}");
    check(rc == 6, "a WRONG expected wire is refused as a mismatch (control)");

    /* The step-count pin can fail: claiming cyclic_gcd declares 2 steps must
     * be refused at stage 3 — proof the count is read from the file. */
    rc = run_row("cyclic_gcd.toml", 0u, 2u, "{\"k\": \"i\", \"v\": \"6\"}");
    check(rc == 3, "a WRONG declared step count is refused (control)");

    /* A proof case the descriptor does not declare must be a navigation
     * refusal, not an invented run. */
    rc = run_row("cyclic_gcd.toml", 99u, 1u, "{\"k\": \"i\", \"v\": \"6\"}");
    check(rc == 2, "an absent proof-case index is refused (control)");

    /* The parser can fail: malformed TOML declines, never guesses. */
    check(srmech_toml_parse("= not toml", 10u, g_toml_ws,
                            srmech_toml_parse_arena_bytes(10u),
                            &parsed) != SRMECH_OK,
          "malformed TOML is refused by srmech_toml_parse (control)");

    printf("== cascade-toml host: %d passed, %d failed ==\n", g_pass, g_fail);
    return (g_fail == 0) ? 0 : 1;
}
