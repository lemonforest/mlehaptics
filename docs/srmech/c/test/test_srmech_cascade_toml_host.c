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
static unsigned char g_run_ws[32u << 20];   /* chain-run arena (measured:    */
                                            /* best_rational_signed ~4.3 MiB;*/
                                            /* octonion_dft's ~2.9 KiB chain */
                                            /* JSON sizes to ~13.4 MiB, and  */
                                            /* klein4's ~4.4 KiB chain to    */
                                            /* ~19.4 MiB — the arena sizer   */
                                            /* scales with document LENGTH)  */
static char g_file[262144];                 /* biggest descriptor is ~23 KiB */
static char g_chain[16384];
static char g_ctx[8192];
static char g_out[65536];

/* ── TOML -> JSON transcode of a FINITE subtree ──────────────────────────
 * Depth-capped recursion (a test file is outside the JPL src audit; the cap
 * makes the recursion bounded the same way the library's own toml_to_json
 * bounds its). Child fan-out is capped at 72 — klein4_from_one's bind block
 * carries a 64-entry quotient table and a 55-entry hexval table, the widest
 * subtrees this host transcodes (24 sufficed until that chain closed) — and
 * the cap FAILS the row rather than truncating: a truncating walker would
 * return a well-formed descriptor holding less than the file said, which is
 * a silent wrong answer of exactly the class this arc exists to close. */
#define T2J_MAX_DEPTH 12u
#define T2J_MAX_KIDS  72u

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

/* The merged @input binding table for one proof case — rc452 (gh #1653,
 * finding (a)). The descriptor's OWN `optional_inputs` (each name defaults
 * to null — Python None) and `input_defaults` (TOML-spellable values) merge
 * UNDER the case's inputs, exactly as srmech.dsl._cascade_chain.
 * chain_input_defaults does. Before this the host built {"inputs": <case>}
 * bare, so it was STRUCTURALLY unable to drive kuramoto_step/general — the
 * very variant whose defaults moved INTO the descriptor at rc452 (`#T1171`)
 * so that shipped configuration would suffice — and no shipped C gate drove
 * that variant from its file at all. NULL on builder failure or more than 16
 * merged keys (the widest shipped case is kuramoto/general's 8). */
static srmech_json_value_t *build_ctx(srmech_json_builder_t *bd,
                                      const srmech_toml_value_t *entry,
                                      const srmech_toml_value_t *inputs)
{
    const srmech_toml_value_t *opt = srmech_toml_table_get(entry, "optional_inputs");
    const srmech_toml_value_t *dfl = srmech_toml_table_get(entry, "input_defaults");
    const char *keys[16]; srmech_json_value_t *vals[16];
    const char *okeys[1]; srmech_json_value_t *ovals[1];
    uint32_t nk = 0u, i, j;

    for (i = 0u; inputs != NULL && i < inputs->u.tbl.n; i++) {
        if (nk >= 16u) { return NULL; }
        keys[nk] = inputs->u.tbl.keys[i];
        vals[nk] = t2j(bd, inputs->u.tbl.vals[i], 0u);
        if (vals[nk] == NULL) { return NULL; }
        nk++;
    }
    for (i = 0u; opt != NULL && opt->type == SRMECH_TOML_ARRAY &&
                 i < opt->u.arr.n; i++) {
        const srmech_toml_value_t *nm = opt->u.arr.items[i];
        int have = 0;
        if (nm == NULL || nm->type != SRMECH_TOML_STRING) { return NULL; }
        for (j = 0u; j < nk; j++) {
            if (strcmp(keys[j], nm->u.str.ptr) == 0) { have = 1; break; }
        }
        if (have) { continue; }
        if (nk >= 16u) { return NULL; }
        keys[nk] = nm->u.str.ptr;
        vals[nk] = srmech_json_new_null(bd);
        if (vals[nk] == NULL) { return NULL; }
        nk++;
    }
    for (i = 0u; dfl != NULL && dfl->type == SRMECH_TOML_TABLE &&
                 i < dfl->u.tbl.n; i++) {
        int have = 0;
        for (j = 0u; j < nk; j++) {
            if (strcmp(keys[j], dfl->u.tbl.keys[i]) == 0) { have = 1; break; }
        }
        if (have) { continue; }
        if (nk >= 16u) { return NULL; }
        keys[nk] = dfl->u.tbl.keys[i];
        vals[nk] = t2j(bd, dfl->u.tbl.vals[i], 0u);
        if (vals[nk] == NULL) { return NULL; }
        nk++;
    }
    okeys[0] = "inputs";
    ovals[0] = srmech_json_new_object(bd, keys, vals, nk);
    if (ovals[0] == NULL) { return NULL; }
    return srmech_json_new_object(bd, okeys, ovals, 1u);
}

/* One row: open the descriptor, parse, extract, transcode, run, compare.
 * `chain_idx` selects WHICH [[cascade.chain]] entry drives — 0 until rc452's
 * registry-ripple phase, which added the first rows over SECOND variants
 * (klein4's wound pipeline is entry 1's twin; kuramoto's general variant IS
 * entry 1 and had no config-driven C gate at all, finding (a)).
 * Distinct return codes so the negative controls can pin WHICH stage refused:
 *   0 = wire bytes match          4 = builder / writer failure
 *   1 = file / parse failure      5 = srmech_chain_run non-OK
 *   2 = navigation failure        6 = wire bytes MISMATCH (printed)
 *   3 = step-count mismatch                                               */
static int run_row(const char *fname, uint32_t chain_idx, uint32_t case_idx,
                   uint32_t n_steps, const char *expect)
{
    const srmech_toml_value_t *root, *cascade, *chain, *entry, *steps;
    const srmech_toml_value_t *cases, *pcase, *inputs, *cname;
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
    entry   = arr_item(chain, chain_idx);   /* the selected [[cascade.chain]] */
    cname   = srmech_toml_table_get(cascade, "name");
    steps   = srmech_toml_table_get(entry, "steps");
    cases   = srmech_toml_table_get(entry, "proof_cases");
    pcase   = arr_item(cases, case_idx);
    inputs  = srmech_toml_table_get(pcase, "inputs");
    if (steps == NULL || steps->type != SRMECH_TOML_ARRAY ||
        inputs == NULL || inputs->type != SRMECH_TOML_TABLE ||
        cname == NULL || cname->type != SRMECH_TOML_STRING) { return 2; }
    /* The DECLARED step count, read from the FILE — pins that the file
     * content (not an embedded literal) supplied the chain shape. */
    if (steps->u.arr.n != n_steps) { return 3; }

    /* chain JSON: the entry's runner keys PLUS the required header (rc452,
     * gh #1653 finding (b)): srmech_chain_run now refuses a chain missing
     * name/summary/returns, and the raw [[cascade.chain]] entry carries
     * summary/returns but NO name — so the [cascade].name from the same file
     * supplies it, the way cascade_chain_specs synthesizes its `op.variant`
     * spelling. Through rc452 Phase 3 this host fed HEADERLESS chains and
     * the runner accepted them — the (b) divergence, live in this file. */
    if (srmech_json_builder_init(&bd, g_build_ws,
                                 sizeof(g_build_ws)) != SRMECH_OK) { return 4; }
    nkeys = 0u;
    if (entry != NULL && entry->type == SRMECH_TOML_TABLE) {
        for (i = 0u; i < entry->u.tbl.n && nkeys < 7u; i++) {
            const char *k = entry->u.tbl.keys[i];
            if (strcmp(k, "chain_schema_version") == 0 ||
                strcmp(k, "summary") == 0 || strcmp(k, "returns") == 0 ||
                strcmp(k, "on_error") == 0 || strcmp(k, "steps") == 0) {
                keys[nkeys] = k;
                vals[nkeys] = t2j(&bd, entry->u.tbl.vals[i], 0u);
                if (vals[nkeys] == NULL) { return 4; }
                nkeys++;
            }
        }
    }
    keys[nkeys] = "name";
    vals[nkeys] = srmech_json_new_string(&bd, cname->u.str.ptr,
                                         cname->u.str.len);
    if (vals[nkeys] == NULL) { return 4; }
    nkeys++;
    jchain = srmech_json_new_object(&bd, keys, vals, nkeys);
    if (jchain == NULL || bd.failed) { return 4; }
    if (write_json(jchain, g_chain, sizeof(g_chain), &clen) != 0) { return 4; }

    /* ctx JSON: the case inputs over the DESCRIPTOR'S OWN defaults —
     * finding (a); see build_ctx. */
    jctx = build_ctx(&bd, entry, inputs);
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
        printf("  (wire mismatch for %s chain %u case %u\n"
               "   expect %s\n   got    %s)\n",
               fname, (unsigned)chain_idx, (unsigned)case_idx, expect, g_out);
        return 6;
    }
    return 0;
}

/* The 18 config-driven rows at rc452 — every chain that runs in C, driven
 * FROM ITS SHIPPED DESCRIPTOR FILE, one hand-derived proof case each (plus
 * the first SECOND-VARIANT rows — see `chain_idx`). `n_steps` is the
 * declared top-level [[cascade.chain.steps]] count the file must yield. */
typedef struct {
    const char *fname;
    uint32_t    chain_idx;
    uint32_t    case_idx;
    uint32_t    n_steps;
    const char *expect;
    const char *why;
} row_t;

static const row_t ROWS[] = {
    { "cyclic_gcd.toml", 0u, 0u, 1u, "{\"k\": \"i\", \"v\": \"6\"}",
      "gcd(12, 18) = 6 (Euclid)" },
    { "cyclic_mod_add.toml", 0u, 0u, 1u, "{\"k\": \"i\", \"v\": \"3\"}",
      "(7 + 8) mod 12 = 15 mod 12 = 3" },
    { "cyclic_mod_mul.toml", 0u, 0u, 1u, "{\"k\": \"i\", \"v\": \"8\"}",
      "(7 * 8) mod 12 = 56 mod 12 = 8" },
    { "cyclic_mod_mul_wide.toml", 0u, 1u, 1u, "{\"k\": \"i\", \"v\": \"2\"}",
      "with n = 2^63-1: (n-1)(n-2) === (-1)(-2) = 2 (mod n) — the WIDE path, "
      "unreachable through a 64-bit product" },
    { "cyclic_mod_inv.toml", 0u, 0u, 1u, "{\"k\": \"i\", \"v\": \"5\"}",
      "3 * 5 = 15 === 1 (mod 7), so mod_inv(3, 7) = 5" },
    { "cyclic_mod_pow.toml", 0u, 0u, 1u, "{\"k\": \"i\", \"v\": \"7\"}",
      "3^7 = 2187, 2187 mod 10 = 7" },
    { "magnitude.toml", 0u, 0u, 2u, "{\"k\": \"f\", \"v\": 3.5}",
      "pin_slot_at_zero(-3.5) = (-1, 3.5); reorient(3.5, +1) = 3.5 — the "
      "Class-K/Class-C decomposition, never an ALU abs" },
    { "net_chirality.toml", 0u, 5u, 1u, "{\"k\": \"i\", \"v\": \"-1\"}",
      "fold orientation_compose over [1, -1, 1] from seed +1: product -1" },
    { "chiral_dual.toml", 0u, 0u, 3u,
      "{\"k\": \"l\", \"v\": [{\"k\": \"f\", \"v\": 11.0}, "
      "{\"k\": \"f\", \"v\": 11.0}, {\"k\": \"f\", \"v\": 14.0}]}",
      "flip([1,2,3]) = [3,2,1]; circular autocorr = [14, 11, 11] "
      "(9+4+1; 6+2+3; 3+6+2); flip back = [11, 11, 14]" },
    { "best_rational_signed.toml", 0u, 0u, 6u,
      "{\"k\": \"t\", \"v\": [{\"k\": \"i\", \"v\": \"22\"}, "
      "{\"k\": \"i\", \"v\": \"7\"}]}",
      "pi -> (22, 7): the six-step K/K/N/N/C/B cascade, integer-carried "
      "through the Class-C tail, crossing as the rc451 TUPLE kind" },
    { "autocorrelation.toml", 0u, 2u, 2u,
      "{\"k\": \"l\", \"v\": [{\"k\": \"f\", \"v\": 14.25}, "
      "{\"k\": \"f\", \"v\": -6.0}, {\"k\": \"f\", \"v\": 4.0}, "
      "{\"k\": \"f\", \"v\": -6.0}]}",
      "circular autocorr of [1, -2, 3, 0.5]: r0 = 1+4+9+0.25 = 14.25; "
      "r1 = -2-6+1.5+0.5 = -6; r2 = 3-1+3-1 = 4; r3 = 0.5-2-6+1.5 = -6 "
      "(all products exactly representable, so the Neumaier compensation "
      "contributes nothing and the values are exact). Runs the NESTED map "
      "bodies — [[cascade.chain.steps.body.body]] — from the file" },
    /* ── rc452 Phase 3: the three chains this phase unblocked ─────────────
     * Each expected wire is hand-derived on a proof case whose float
     * arithmetic is EXACT, so the derivation needs no trusted oracle:
     * identity twiddles (theta = 0) for the DFTs, sin(0) = 0 for kuramoto,
     * with the one rounding collapse computed as an exact dyadic sum. */
    { "kuramoto_step.toml", 0u, 2u, 3u,
      "{\"k\": \"l\", \"v\": [{\"k\": \"f\", \"v\": 0.713}]}",
      "n_one is PURE DRIFT: the only coupling term is sin(theta_0 - theta_0) "
      "= sin(0), whose Q61 rational is exactly 0. The combine is then the "
      "exact dyadic sum 0.7 + 0.01*(1.3 + 1.0*0): with 0.7 = "
      "3152519739159347/2^52, 0.01 = 5764607523034235/2^59 and 1.3 = "
      "5854679515581645/2^52, the sum rounds (half-even) to the double "
      "spelled 0.713 — one float() collapse, as the op declares" },
    { "quaternion_dft.toml", 0u, 5u, 6u,
      "{\"k\": \"l\", \"v\": [{\"k\": \"l\", \"v\": [{\"k\": \"f\", \"v\": 1.0}, "
      "{\"k\": \"f\", \"v\": 2.0}, {\"k\": \"f\", \"v\": 3.0}, "
      "{\"k\": \"f\", \"v\": 4.0}]}]}",
      "the 'single' case: N = 1, so the only twiddle angle is "
      "sigma*2*pi*(0*0 mod 1)/1 = 0 and W = exp(0) = [1,0,0,0], whose "
      "left-mult operator is the identity (e0*ek = ek). Summand = x[0]; "
      "vec_add from the zero seed and vec_scale by 1.0 are exact; the "
      "spectrum is [[1, 2, 3, 4]] verbatim — crossing as a NESTED l, the "
      "kind the rc452 depth-bounded marshaller added" },
    { "octonion_dft.toml", 0u, 6u, 7u,
      "{\"k\": \"l\", \"v\": [{\"k\": \"l\", \"v\": [{\"k\": \"f\", \"v\": 1.0}, "
      "{\"k\": \"f\", \"v\": 2.0}, {\"k\": \"f\", \"v\": 3.0}, "
      "{\"k\": \"f\", \"v\": 4.0}, {\"k\": \"f\", \"v\": 0.0}, "
      "{\"k\": \"f\", \"v\": 0.0}, {\"k\": \"f\", \"v\": 0.0}, "
      "{\"k\": \"f\", \"v\": 0.0}]}]}",
      "the 'quat_embed' case: as_oct8 zero-extends [1,2,3,4] into H c O; "
      "N = 1 makes the e4-axis twiddle exp(0) = identity, so the one-sided "
      "left product returns the embedded sample and the spectrum is "
      "[[1, 2, 3, 4, 0, 0, 0, 0]] exactly" },
    /* ── rc452 registry-ripple phase (gh #1653): the two rows this phase
     * adds. klein4's expect is derived from the FIPS 180-4 contract via an
     * INDEPENDENT implementation (coreutils sha256sum — not srmech's C, not
     * CPython's hashlib) plus base-4 crumb arithmetic by hand; the kuramoto
     * general row is the FIRST config-driven C gate over that variant, and
     * the first row whose ctx depends on the descriptor's own
     * input_defaults / optional_inputs (finding (a) — pin_strength = 1.0
     * and pin_anchor = null come from the FILE, not the case). */
    { "klein4_from_one.toml", 0u, 0u, 10u,
      "{\"k\": \"l\", \"v\": [{\"k\": \"i\", \"v\": \"3\"}, {\"k\": \"i"
      "\", \"v\": \"0\"}, {\"k\": \"i\", \"v\": \"0\"}, {\"k\": \"i\", "
      "\"v\": \"0\"}, {\"k\": \"i\", \"v\": \"2\"}, {\"k\": \"i\", \"v"
      "\": \"0\"}, {\"k\": \"i\", \"v\": \"1\"}, {\"k\": \"i\", \"v\": "
      "\"1\"}, {\"k\": \"i\", \"v\": \"1\"}, {\"k\": \"i\", \"v\": \"3"
      "\"}, {\"k\": \"i\", \"v\": \"1\"}, {\"k\": \"i\", \"v\": \"0\"},"
      " {\"k\": \"i\", \"v\": \"2\"}, {\"k\": \"i\", \"v\": \"2\"}, {\""
      "k\": \"i\", \"v\": \"3\"}, {\"k\": \"i\", \"v\": \"0\"}, {\"k\":"
      " \"i\", \"v\": \"2\"}, {\"k\": \"i\", \"v\": \"0\"}, {\"k\": \"i"
      "\", \"v\": \"0\"}, {\"k\": \"i\", \"v\": \"3\"}, {\"k\": \"i\", "
      "\"v\": \"1\"}, {\"k\": \"i\", \"v\": \"1\"}, {\"k\": \"i\", \"v"
      "\": \"3\"}, {\"k\": \"i\", \"v\": \"0\"}, {\"k\": \"i\", \"v\": "
      "\"0\"}, {\"k\": \"i\", \"v\": \"2\"}, {\"k\": \"i\", \"v\": \"3"
      "\"}, {\"k\": \"i\", \"v\": \"1\"}, {\"k\": \"i\", \"v\": \"3\"},"
      " {\"k\": \"i\", \"v\": \"0\"}, {\"k\": \"i\", \"v\": \"0\"}, {\""
      "k\": \"i\", \"v\": \"2\"}, {\"k\": \"i\", \"v\": \"2\"}, {\"k\":"
      " \"i\", \"v\": \"2\"}, {\"k\": \"i\", \"v\": \"0\"}, {\"k\": \"i"
      "\", \"v\": \"2\"}, {\"k\": \"i\", \"v\": \"3\"}, {\"k\": \"i\", "
      "\"v\": \"2\"}, {\"k\": \"i\", \"v\": \"2\"}, {\"k\": \"i\", \"v"
      "\": \"0\"}, {\"k\": \"i\", \"v\": \"0\"}, {\"k\": \"i\", \"v\": "
      "\"0\"}, {\"k\": \"i\", \"v\": \"0\"}, {\"k\": \"i\", \"v\": \"3"
      "\"}, {\"k\": \"i\", \"v\": \"3\"}, {\"k\": \"i\", \"v\": \"3\"},"
      " {\"k\": \"i\", \"v\": \"1\"}, {\"k\": \"i\", \"v\": \"3\"}, {\""
      "k\": \"i\", \"v\": \"1\"}, {\"k\": \"i\", \"v\": \"1\"}, {\"k\":"
      " \"i\", \"v\": \"3\"}, {\"k\": \"i\", \"v\": \"0\"}, {\"k\": \"i"
      "\", \"v\": \"0\"}, {\"k\": \"i\", \"v\": \"1\"}, {\"k\": \"i\", "
      "\"v\": \"1\"}, {\"k\": \"i\", \"v\": \"0\"}, {\"k\": \"i\", \"v"
      "\": \"1\"}, {\"k\": \"i\", \"v\": \"1\"}, {\"k\": \"i\", \"v\": "
      "\"0\"}, {\"k\": \"i\", \"v\": \"3\"}, {\"k\": \"i\", \"v\": \"3"
      "\"}, {\"k\": \"i\", \"v\": \"1\"}, {\"k\": \"i\", \"v\": \"1\"},"
      " {\"k\": \"i\", \"v\": \"0\"}]}",
      "ONE-A14 at rest, case 0 ({sigma:1, terms:24, theta:[1,1]}): render "
      "the preimage {\"sigma\":1,\"terms\":24,\"theta\":[1,1]}, sha256sum "
      "(independent coreutils run) gives 5ee9cb25...6dc6514e; counter block "
      "h||'|0' gives a6a8e265...10b2c9; each hex byte yields crumbs "
      "(lo%4, lo/4, hi%4, hi/4) XOR the (1,3,7,3) period-14 mask "
      "[1,1,2,2,2,2,3,3,3,3,3,3,3,3] — 64 masked crumbs, all derived by "
      "hand from FIPS 180-4 + base-4 arithmetic before being frozen here" },
    { "kuramoto_step.toml", 1u, 4u, 3u,
      "{\"k\": \"l\", \"v\": [{\"k\": \"f\", \"v\": 1.0}, "
      "{\"k\": \"f\", \"v\": -1.0}]}",
      "the GENERAL variant (chain 1), zero-coupling adjacency case: K = 0 "
      "with adjacency present makes every term weight K*A_ij = 0, so each "
      "coupling sum is exactly 0.0; omega = [0, 0] and dt*0 = 0.0, so "
      "theta' = theta = [1.0, -1.0] EXACTLY. pin_anchor rides as null and "
      "pin_strength as 1.0 from the descriptor's OWN optional_inputs / "
      "input_defaults tables — the case supplies neither, which is what "
      "makes this row the finding-(a) gate: a host ignoring the defaults "
      "cannot resolve @bind.psi and declines instead of answering" },
    /* -- rc452 Phase 2 (`#T1166`, the K1 slice): the FIRST row whose final
     * value crosses as the `b` (BYTES) kind. Its expected hex is derived
     * INDEPENDENTLY of srmech and of CPython: the three SHA-256 digests come
     * from coreutils sha256sum over the three exact preimages, and the
     * stride / rotate / XOR arithmetic over those hex strings is plain
     * integer arithmetic with no library involved. Case 2 is chosen over
     * case 0 because D = 256 makes the whole fingerprint 32 bytes -- a
     * 64-char expectation a reader can re-derive in a shell, where the
     * D = 8192 sweep case would be 2048 chars nobody would check. */
    { "encode_loe_content.toml", 0u, 2u, 11u,
      "{\"k\": \"b\", \"v\": \"63322bf3973f4ed9a3891f3bc481b781"
      "b69f941937d09aa0d32ace8c2e46b5bd\"}",
      "the 'substrate_anchor' case (content 'hello', D 256, substrate "
      "'audio'). sha256sum('LoE.content.hello' || u64_be(0)) = a9d325d3... "
      "is the Class-A mint; sha256sum('hello') = 2cf24dba..., whose first 8 "
      "bytes little-endian are 1054880662928880172, reduced mod D = 256 by "
      "the Class-I mod_add to a stride of 44; the Class-C permute rotates "
      "the mint by 44 bit positions (LSB-first within each byte); "
      "sha256sum('LoE.substrate.audio' || u64_be(0)) = 2b9e13c4... is the "
      "substrate anchor, and the Class-M bind XORs the two -- 64 hex chars "
      "derived from FIPS 180-4 via coreutils plus integer arithmetic, "
      "before being frozen here" },
    /* -- rc452 Phase 2 (`#T1166`, the K3 slice): the FIRST row whose final
     * value crosses as the `x` (MATRIX) kind, and the first driven by a C arm
     * with no pre-existing C symbol behind it at any granularity. Its
     * expectation is derived by hand and is EXACTLY representable, so no
     * oracle of any kind is involved. */
    { "schur_complement.toml", 0u, 0u, 1u,
      "{\"k\": \"x\", \"v\": [{\"k\": \"l\", \"v\": [{\"k\": \"f\", \"v\": 1.5}, "
      "{\"k\": \"f\", \"v\": -0.5}]}, {\"k\": \"l\", \"v\": [{\"k\": \"f\", "
      "\"v\": -0.5}, {\"k\": \"f\", \"v\": 1.5}]}]}",
      "the 3-path Laplacian [[2,-1,0],[-1,2,-1],[0,-1,2]] reduced onto the "
      "boundary {0, 2}. The interior is the single node 1, so L_ii = [[2]], "
      "L_id = [[-1, -1]] and the interior solve is the scalar division "
      "X = [[-0.5, -0.5]] -- exact in binary. Then S = L_dd - L_di X gives "
      "S[0][0] = 2 - (-1)(-0.5) = 1.5, S[0][1] = 0 - (-1)(-0.5) = -0.5, and "
      "the transpose by symmetry: [[1.5, -0.5], [-0.5, 1.5]]. Every value is "
      "a dyadic rational, so this row needs no oracle at all -- it is the "
      "textbook Schur complement done by hand" },
};

int main(void)
{
    size_t r;
    int rc;
    srmech_toml_value_t *parsed = NULL;

    printf("== Surface-A cascade-catalog TOML -> bare-C chain run "
           "(gh #1653, rc452 `#T1166`) ==\n");

    /* ── the 18 config-driven rows ──────────────────────────────────────── */
    for (r = 0u; r < sizeof(ROWS) / sizeof(ROWS[0]); r++) {
        char desc[512];
        rc = run_row(ROWS[r].fname, ROWS[r].chain_idx, ROWS[r].case_idx,
                     ROWS[r].n_steps, ROWS[r].expect);
        snprintf(desc, sizeof(desc),
                 "%s chain %u case %u from the FILE -> rc %d — %s",
                 ROWS[r].fname, (unsigned)ROWS[r].chain_idx,
                 (unsigned)ROWS[r].case_idx, rc, ROWS[r].why);
        check(rc == 0, desc);
    }

    /* ── negative controls: every refusal stage can actually refuse ─────── */

    /* The comparator can fail: a deliberately-wrong expected wire must be
     * reported as a MISMATCH (6), not swallowed. Without this, 16 green rows
     * are indistinguishable from a strcmp that cannot return nonzero. */
    rc = run_row("cyclic_gcd.toml", 0u, 0u, 1u, "{\"k\": \"i\", \"v\": \"7\"}");
    check(rc == 6, "a WRONG expected wire is refused as a mismatch (control)");

    /* The step-count pin can fail: claiming cyclic_gcd declares 2 steps must
     * be refused at stage 3 — proof the count is read from the file. */
    rc = run_row("cyclic_gcd.toml", 0u, 0u, 2u, "{\"k\": \"i\", \"v\": \"6\"}");
    check(rc == 3, "a WRONG declared step count is refused (control)");

    /* A proof case the descriptor does not declare must be a navigation
     * refusal, not an invented run. */
    rc = run_row("cyclic_gcd.toml", 0u, 99u, 1u, "{\"k\": \"i\", \"v\": \"6\"}");
    check(rc == 2, "an absent proof-case index is refused (control)");

    /* A chain VARIANT the descriptor does not declare must refuse the same
     * way — the chain_idx column is new (rc452) and must be provably read. */
    rc = run_row("cyclic_gcd.toml", 9u, 0u, 1u, "{\"k\": \"i\", \"v\": \"6\"}");
    check(rc == 2, "an absent [[cascade.chain]] index is refused (control)");

    /* The parser can fail: malformed TOML declines, never guesses. */
    check(srmech_toml_parse("= not toml", 10u, g_toml_ws,
                            srmech_toml_parse_arena_bytes(10u),
                            &parsed) != SRMECH_OK,
          "malformed TOML is refused by srmech_toml_parse (control)");

    printf("== cascade-toml host: %d passed, %d failed ==\n", g_pass, g_fail);
    return (g_fail == 0) ? 0 : 1;
}
