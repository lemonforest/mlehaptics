/*
 * test_srmech_genome.c — standalone C smoke tests for §41 genome
 * persistence (srmech_genome_save / catalog / load / window / append).
 *
 * No Python, no test framework — assert + count, like test_srmech_json.c.
 * Exits 0 on all-pass, non-zero on first fail.
 *
 * Builds a tiny synthetic genome in memory (leaf_dim = 4, 2 chromosomes),
 * saves it to a temp dir, then exercises:
 *   - catalog : manifest parses, body_sha256 present.
 *   - load    : bytes == body + whole-body bounding OK.
 *   - bounding: corrupt one byte of turns.bin -> load returns the error.
 *   - window  : one chromosome's region bytes match (cap bounding OK).
 *   - append  : n_turns grows + a prior chromosome entry is unchanged.
 */

#include "srmech.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int g_passed = 0;
static int g_failed = 0;

/* 8 MiB workspace arena — matches the json smoke + parity harness. */
static unsigned char g_ws[8u * 1024u * 1024u];

/* rc338 (#956): a SECOND, disjoint arena. The lifetime check below holds two
 * derived manifest trees alive at once, and they must not share storage — with
 * one arena the second call would overwrite the first tree's json nodes
 * outright, which is a different (and uninteresting) failure than the
 * use-after-scope this checks for. Disjoint arenas leave the STACK as the only
 * thing the two calls share. */
static unsigned char g_ws2[8u * 1024u * 1024u];

static void check_true(int cond, const char *desc)
{
    if (cond) {
        g_passed++;
        printf("  PASS  %s\n", desc);
    } else {
        g_failed++;
        printf("  FAIL  %s\n", desc);
    }
}

/* Pick a writable temp directory (TMPDIR / TMP, else /tmp). Returns a
 * pointer into a static buffer holding "<base>/srmech_genome_smoke". */
static const char *temp_dir(void)
{
    static char dir[1024];
    const char *base = getenv("TMPDIR");
    if (base == NULL) { base = getenv("TMP"); }
    if (base == NULL) { base = "/tmp"; }
    snprintf(dir, sizeof(dir), "%s/srmech_genome_smoke", base);
    return dir;
}

/* rc338 (#956): a SECOND store, so the lifetime check has a genome whose digests
 * are distinguishable from the first's. */
static const char *temp_dir2(void)
{
    static char dir[1024];
    const char *base = getenv("TMPDIR");
    if (base == NULL) { base = getenv("TMP"); }
    if (base == NULL) { base = "/tmp"; }
    snprintf(dir, sizeof(dir), "%s/srmech_genome_smoke2", base);
    return dir;
}

/* Best-effort mkdir of `dir` (POSIX `mkdir -p` analogue for one level).
 * The genome save itself assumes the directory exists, so we create it
 * here via a tiny system-portable shim: try to write a probe file, and
 * if that fails, mkdir via the C runtime. We keep it minimal — the WSL2
 * harness runs under Linux where the parent /tmp always exists. */
static int ensure_dir(const char *dir)
{
#if defined(_WIN32)
    (void)dir;
    return system(NULL) ? 0 : 0;   /* the parity harness runs on Linux */
#else
    char cmd[1200];
    /* Fresh dir each run (drop stale turns.bin / manifest.json so the
     * append 'label already present' check is exercised cleanly). */
    snprintf(cmd, sizeof(cmd), "rm -rf '%s' && mkdir -p '%s'", dir, dir);
    return system(cmd);
#endif
}

/* rc280 §101 tick: CANCEL once `done` reaches *(size_t *)user. Records the last
 * event seen so the test can assert the heartbeat's exact (done, total, phase). */
static uint64_t g_sc_last_done = 0u;
static uint64_t g_sc_last_total = 0u;
static uint32_t g_sc_last_phase = 0u;
static int g_sc_ticks = 0;

static int sc_cancel_at(const srmech_progress_ev_t *ev, void *user)
{
    const uint64_t at = *(const uint64_t *)user;
    g_sc_last_done = ev->done;
    g_sc_last_total = ev->total;
    g_sc_last_phase = ev->phase;
    g_sc_ticks++;
    return (ev->done >= at) ? 1 : 0;
}

int main(void)
{
    printf("== srmech_genome smoke tests ==\n");

    const uint32_t leaf_dim = 4u;
    /* coupling: one 4-byte Klein-4 block (values 0..3). */
    unsigned char coupling[4] = { 1u, 2u, 3u, 0u };

    /* §44 self-describing body (leaf_dim=4, so labels are <= 3 bytes). Two
     * chromosomes; the save SCANS the inline caps (no caller layout).
     *   chrom "A": CHROM cap + a GENE cap "g" + 2 data turns  (4 blocks)
     *   chrom "B": CHROM cap + 1 data turn                     (2 blocks)
     * The GENE cap is in the region (byte_len) but NOT a data turn
     * (leaf_count) — so A.leaf_count == 2. 6 blocks * 4 = 24 bytes. */
    const unsigned char CC = (unsigned char)SRMECH_GENOME_CHROM_CAP_MARKER;
    const unsigned char GC = (unsigned char)SRMECH_GENOME_GENE_CAP_MARKER;
    unsigned char body[24] = {
        /* A CHROM cap */ CC, (unsigned char)'A', 0u, 0u,
        /* A GENE cap  */ GC, (unsigned char)'g', 0u, 0u,
        /* A turn0     */ 0u, 1u, 2u, 3u,
        /* A turn1     */ 2u, 2u, 1u, 1u,
        /* B CHROM cap */ CC, (unsigned char)'B', 0u, 0u,
        /* B turn0     */ 3u, 0u, 2u, 1u,
    };

    const char *dir = temp_dir();
    ensure_dir(dir);

    srmech_status_t st = srmech_genome_save(
        dir, body, sizeof(body), leaf_dim, coupling, sizeof(coupling),
        g_ws, sizeof(g_ws));
    check_true(st == SRMECH_OK, "genome_save OK (scans inline caps)");

    /* CATALOG: manifest parses, data.body_sha256 present. */
    {
        srmech_json_value_t *man = NULL;
        st = srmech_genome_catalog(dir, NULL, 0u, g_ws, sizeof(g_ws), &man);
        check_true(st == SRMECH_OK && man != NULL, "genome_catalog parses");
        const srmech_json_value_t *data =
            srmech_json_object_get(man, "data");
        check_true(data != NULL && data->type == SRMECH_JSON_OBJECT,
                   "manifest has data object");
        const srmech_json_value_t *bsha =
            srmech_json_object_get(data, "body_sha256");
        check_true(bsha != NULL && bsha->type == SRMECH_JSON_STRING &&
                   bsha->u.str.len == 64u, "data.body_sha256 is 64-hex");
        const srmech_json_value_t *nt =
            srmech_json_object_get(data, "n_turns");
        check_true(nt != NULL && nt->type == SRMECH_JSON_INT && nt->u.i == 6,
                   "data.n_turns == 6 (blocks: 4 + 2)");
        const srmech_json_value_t *ld =
            srmech_json_object_get(data, "leaf_dim");
        check_true(ld != NULL && ld->type == SRMECH_JSON_INT && ld->u.i == 4,
                   "data.leaf_dim == 4");
    }

    /* LOAD: bytes == body + whole-body bounding OK. */
    {
        unsigned char out[64];
        size_t olen = 0u;
        st = srmech_genome_load(dir, out, sizeof(out), &olen,
                                NULL, 0u, g_ws, sizeof(g_ws));
        check_true(st == SRMECH_OK, "genome_load OK (bounding passes)");
        check_true(olen == sizeof(body) &&
                   memcmp(out, body, sizeof(body)) == 0,
                   "loaded body == saved body");
    }

    /* WINDOW: chromosome 'A' region bytes (CHROM cap + GENE cap + 2 turns =
     * 4 blocks = 16 bytes). The region includes the caps (caller flattens). */
    {
        unsigned char out[64];
        size_t olen = 0u;
        st = srmech_genome_window(dir, "A", out, sizeof(out), &olen,
                                  NULL, 0u, g_ws, sizeof(g_ws));
        check_true(st == SRMECH_OK, "genome_window('A') OK");
        check_true(olen == 16u && memcmp(out, body, 16u) == 0,
                   "window('A') == first 16 body bytes");
        /* WINDOW on a missing label is rejected. */
        st = srmech_genome_window(dir, "nope", out, sizeof(out), &olen,
                                  NULL, 0u, g_ws, sizeof(g_ws));
        check_true(st != SRMECH_OK, "genome_window('nope') rejected");
    }

    /* APPEND: add chromosome 'C' (CHROM cap + 1 turn = 2 blocks = 8 bytes). */
    {
        unsigned char region[8] = {
            /* C CHROM cap */ CC, (unsigned char)'C', 0u, 0u,
            /* C turn0     */ 1u, 1u, 0u, 3u,
        };
        st = srmech_genome_append(dir, "C", region, sizeof(region),
                                  leaf_dim, coupling, sizeof(coupling),
                                  g_ws, sizeof(g_ws));
        check_true(st == SRMECH_OK, "genome_append('C') OK");

        srmech_json_value_t *man = NULL;
        st = srmech_genome_catalog(dir, NULL, 0u, g_ws, sizeof(g_ws), &man);
        const srmech_json_value_t *data =
            srmech_json_object_get(man, "data");
        const srmech_json_value_t *nt =
            srmech_json_object_get(data, "n_turns");
        check_true(nt != NULL && nt->u.i == 8, "n_turns grew 6 -> 8");
        const srmech_json_value_t *chr =
            srmech_json_object_get(data, "chromosomes");
        check_true(chr != NULL && chr->type == SRMECH_JSON_ARRAY &&
                   chr->u.arr.n == 3u, "chromosomes now 3");
        /* Prior entry 'A' (index 0) byte_offset/leaf_count unchanged (the GENE
         * cap is in the region but excluded from leaf_count). */
        const srmech_json_value_t *a0 = chr->u.arr.items[0];
        const srmech_json_value_t *a_off =
            srmech_json_object_get(a0, "byte_offset");
        const srmech_json_value_t *a_lc =
            srmech_json_object_get(a0, "leaf_count");
        check_true(a_off != NULL && a_off->u.i == 0 &&
                   a_lc != NULL && a_lc->u.i == 2,
                   "prior 'A' entry unchanged (offset 0, leaf_count 2)");
        /* New 'C' entry at index 2, offset 24 (the prior 24-byte body). */
        const srmech_json_value_t *g2 = chr->u.arr.items[2];
        const srmech_json_value_t *g_lbl =
            srmech_json_object_get(g2, "label");
        const srmech_json_value_t *g_off =
            srmech_json_object_get(g2, "byte_offset");
        check_true(g_lbl != NULL && g_lbl->u.str.len == 1u &&
                   memcmp(g_lbl->u.str.ptr, "C", 1) == 0 &&
                   g_off != NULL && g_off->u.i == 24,
                   "new 'C' entry at offset 24");
    }

    /* §97 C-host parity: srmech_genome_append_arena_bytes sizes the v12 append arena
     * from the MANIFEST (O(1) tail-extend), never the body — a bare-C host sizes right
     * with no Python. The genome here is A+B+C (a v12 HEAD-ONLY manifest carrying the
     * scalar n_chromosomes = 3). Prove: (1) it returns OK + a usable size; (2) that
     * size EQUALS the manifest-scaled arithmetic, NOT the body-scaled one; (3) the
     * size actually SUFFICES for a real append (run one bounded to exactly `sz`). */
    {
        size_t msz = 0u, body = 0u;
        char mp[1200], bp[1200];
        snprintf(mp, sizeof(mp), "%s/manifest.json", dir);
        snprintf(bp, sizeof(bp), "%s/turns.bin", dir);
        FILE *mf = fopen(mp, "rb");
        check_true(mf != NULL, "open manifest.json for arena-size check");
        if (mf != NULL) { fseek(mf, 0L, SEEK_END); msz = (size_t)ftell(mf); fclose(mf); }
        FILE *bf = fopen(bp, "rb");
        check_true(bf != NULL, "open turns.bin for arena-size check");
        if (bf != NULL) { fseek(bf, 0L, SEEK_END); body = (size_t)ftell(bf); fclose(bf); }

        size_t sz = 0u;
        srmech_status_t as = srmech_genome_append_arena_bytes(dir, 8u, g_ws,
                                                              sizeof(g_ws), &sz);
        check_true(as == SRMECH_OK && sz > 0u, "append_arena_bytes(v12) OK");
        /* MANIFEST-scaled with n_chroms = 1: the O(1) v4 head path stages ONE region
         * slot + a head-only (1-entry) manifest, so the arena is INDEPENDENT of the
         * chromosome count (the §97 O(1) guarantee) — never `n_chromosomes` * per_chrom. */
        size_t manifest_scaled = srmech_genome_arena_bytes(msz * 6u + 300000u, 1u, 8u);
        check_true(sz == manifest_scaled,
                   "append arena is MANIFEST-scaled, n_chroms=1 (O(1) v4 path)");
        /* NOT the whole-body migration size (guards against a v12 misroute). */
        size_t body_scaled = srmech_genome_arena_bytes(body + 8u, 1u, 8u);
        check_true(sz != body_scaled || body + 8u == msz * 6u + 300000u,
                   "append arena is NOT body-scaled for v12");
        /* The size actually SUFFICES: a real append bounded to EXACTLY `sz` bytes of
         * the arena succeeds — a bare-C host would size its arena from this, no more.
         * (This mutates the genome to A+B+C+D; the BOUNDING/§44 sections below re-save
         * a fresh body, so the extra chromosome does not perturb them.) */
        {
            unsigned char dregion[8] = {
                /* D CHROM cap */ CC, (unsigned char)'D', 0u, 0u,
                /* D turn0     */ 1u, 1u, 0u, 3u,
            };
            srmech_status_t ds = srmech_genome_append(dir, "D", dregion,
                sizeof(dregion), leaf_dim, coupling, sizeof(coupling), g_ws, sz);
            check_true(ds == SRMECH_OK, "append fits in append_arena_bytes size");
        }
    }

    /* BOUNDING: corrupt one byte of turns.bin -> load returns the error. */
    {
        char body_path[1200];
        snprintf(body_path, sizeof(body_path), "%s/turns.bin", dir);
        FILE *fp = fopen(body_path, "r+b");
        check_true(fp != NULL, "reopen turns.bin to corrupt a byte");
        if (fp != NULL) {
            fseek(fp, 0, SEEK_SET);
            unsigned char b = 0;
            size_t r = fread(&b, 1u, 1u, fp);
            (void)r;
            fseek(fp, 0, SEEK_SET);
            unsigned char flipped = (unsigned char)(b ^ 0x01u);
            fwrite(&flipped, 1u, 1u, fp);
            fclose(fp);
        }
        unsigned char out[64];
        size_t olen = 0u;
        st = srmech_genome_load(dir, out, sizeof(out), &olen,
                                NULL, 0u, g_ws, sizeof(g_ws));
        check_true(st == SRMECH_ERR_BAD_INPUT,
                   "corrupted body -> load bounding error");
    }

    /* §44 (rc145): manifest.json is the OPTIONAL .fai cache — the loaders
     * reconstruct from turns.bin ALONE (scan), given coupling for the leaf
     * width. So a genome can be shipped as turns.bin only (the §43 goal). */
    {
        /* Re-save a clean genome (the BOUNDING test corrupted turns.bin). */
        st = srmech_genome_save(dir, body, sizeof(body), leaf_dim,
                                coupling, sizeof(coupling), g_ws, sizeof(g_ws));
        check_true(st == SRMECH_OK, "re-save clean genome for the §44 section");
        /* Delete manifest.json — the strand is now the sole source of truth. */
        char man_path[1200];
        snprintf(man_path, sizeof(man_path), "%s/manifest.json", dir);
        check_true(remove(man_path) == 0, "delete manifest.json");

        /* CATALOG rebuilt by scanning turns.bin (needs coupling for the width). */
        srmech_json_value_t *man = NULL;
        st = srmech_genome_catalog(dir, coupling, sizeof(coupling),
                                   g_ws, sizeof(g_ws), &man);
        check_true(st == SRMECH_OK && man != NULL,
                   "catalog rebuilt manifest-less (coupling)");
        const srmech_json_value_t *data = srmech_json_object_get(man, "data");
        const srmech_json_value_t *nt = srmech_json_object_get(data, "n_turns");
        check_true(nt != NULL && nt->u.i == 6,
                   "rebuilt n_turns == 6 (the original 2-chrom body)");

        /* LOAD manifest-less -> body bytes match the saved body. */
        unsigned char out[64];
        size_t olen = 0u;
        st = srmech_genome_load(dir, out, sizeof(out), &olen,
                                coupling, sizeof(coupling), g_ws, sizeof(g_ws));
        check_true(st == SRMECH_OK && olen == sizeof(body) &&
                   memcmp(out, body, sizeof(body)) == 0,
                   "load manifest-less == saved body");

        /* WINDOW manifest-less -> chromosome 'A' region (first 16 bytes). */
        st = srmech_genome_window(dir, "A", out, sizeof(out), &olen,
                                  coupling, sizeof(coupling), g_ws, sizeof(g_ws));
        check_true(st == SRMECH_OK && olen == 16u &&
                   memcmp(out, body, 16u) == 0,
                   "window('A') manifest-less == first 16 bytes");

        /* HELPFUL error: no manifest AND no coupling -> BAD_INPUT (not IO). */
        st = srmech_genome_catalog(dir, NULL, 0u, g_ws, sizeof(g_ws), &man);
        check_true(st == SRMECH_ERR_BAD_INPUT,
                   "no manifest + no coupling -> BAD_INPUT (helpful, not IO)");

        /* APPEND manifest-less -> rebuilds, appends, re-writes the .fai cache. */
        unsigned char region[8] = {
            /* Z CHROM cap */ CC, (unsigned char)'Z', 0u, 0u,
            /* Z turn0     */ 1u, 1u, 0u, 3u,
        };
        st = srmech_genome_append(dir, "Z", region, sizeof(region), leaf_dim,
                                  coupling, sizeof(coupling), g_ws, sizeof(g_ws));
        check_true(st == SRMECH_OK, "append manifest-less OK (rebuild + grow)");
        st = srmech_genome_catalog(dir, NULL, 0u, g_ws, sizeof(g_ws), &man);
        data = srmech_json_object_get(man, "data");
        nt = srmech_json_object_get(data, "n_turns");
        check_true(st == SRMECH_OK && nt != NULL && nt->u.i == 8,
                   "append re-wrote the .fai cache (n_turns 6 -> 8)");
    }

    /* §45 (rc147): IN-PLACE EDIT — biology excises, it does not re-synthesize.
     * An edit is a pure BYTE splice on the self-describing body; the survivors'
     * coupled bytes stay byte-identical (only relocated). */
    {
        /* clean 2-chromosome body (A + B). */
        st = srmech_genome_save(dir, body, sizeof(body), leaf_dim,
                                coupling, sizeof(coupling), g_ws, sizeof(g_ws));
        check_true(st == SRMECH_OK, "re-save clean A+B for the §45 section");

        /* REMOVE the FIRST chromosome 'A' (16 bytes) — B slides to the front. */
        st = srmech_genome_remove(dir, "A", coupling, sizeof(coupling),
                                  g_ws, sizeof(g_ws));
        check_true(st == SRMECH_OK, "genome_remove('A') OK");
        {
            unsigned char out[64];
            size_t olen = 0u;
            st = srmech_genome_load(dir, out, sizeof(out), &olen,
                                    NULL, 0u, g_ws, sizeof(g_ws));
            /* the new body == the original B region (last 8 bytes), VERBATIM. */
            check_true(st == SRMECH_OK && olen == 8u &&
                       memcmp(out, body + 16, 8u) == 0,
                       "remove('A') is a pure byte splice (B verbatim, relocated)");
            st = srmech_genome_window(dir, "B", out, sizeof(out), &olen,
                                      NULL, 0u, g_ws, sizeof(g_ws));
            check_true(st == SRMECH_OK && olen == 8u, "window('B') after remove OK");
            st = srmech_genome_window(dir, "A", out, sizeof(out), &olen,
                                      NULL, 0u, g_ws, sizeof(g_ws));
            check_true(st != SRMECH_OK, "window('A') gone after remove");
        }

        /* REMOVE the only chromosome -> BAD_INPUT (a genome keeps >= 1). */
        st = srmech_genome_remove(dir, "B", coupling, sizeof(coupling),
                                  g_ws, sizeof(g_ws));
        check_true(st == SRMECH_ERR_BAD_INPUT, "remove the only chromosome rejected");
        /* REMOVE a missing label -> BAD_INPUT. */
        st = srmech_genome_remove(dir, "nope", coupling, sizeof(coupling),
                                  g_ws, sizeof(g_ws));
        check_true(st == SRMECH_ERR_BAD_INPUT, "remove('nope') rejected");

        /* REPLACE: re-save A+B, then replace 'B' (8 bytes) with a fresh region
         * (CHROM cap 'B' + 2 turns = 3 blocks = 12 bytes). A stays byte-identical. */
        st = srmech_genome_save(dir, body, sizeof(body), leaf_dim,
                                coupling, sizeof(coupling), g_ws, sizeof(g_ws));
        check_true(st == SRMECH_OK, "re-save A+B for the replace case");
        {
            unsigned char nregion[12] = {
                /* B CHROM cap */ CC, (unsigned char)'B', 0u, 0u,
                /* B turn0     */ 2u, 0u, 1u, 3u,
                /* B turn1     */ 1u, 3u, 2u, 0u,
            };
            unsigned char out[64];
            size_t olen = 0u;
            st = srmech_genome_replace(dir, "B", nregion, sizeof(nregion),
                                       leaf_dim, coupling, sizeof(coupling),
                                       g_ws, sizeof(g_ws));
            check_true(st == SRMECH_OK, "genome_replace('B') OK");
            st = srmech_genome_load(dir, out, sizeof(out), &olen,
                                    NULL, 0u, g_ws, sizeof(g_ws));
            /* new body == A's original 16 bytes (untouched) + the 12-byte region. */
            check_true(st == SRMECH_OK && olen == 28u &&
                       memcmp(out, body, 16u) == 0 &&
                       memcmp(out + 16, nregion, 12u) == 0,
                       "replace('B') splices in place (A verbatim + new B)");
            st = srmech_genome_window(dir, "B", out, sizeof(out), &olen,
                                      NULL, 0u, g_ws, sizeof(g_ws));
            check_true(st == SRMECH_OK && olen == 12u, "window('B') == new region");
        }

        /* CORRUPT-body integrity bound fires BEFORE an in-place edit. */
        {
            char body_path[1200];
            snprintf(body_path, sizeof(body_path), "%s/turns.bin", dir);
            FILE *f = fopen(body_path, "r+b");
            check_true(f != NULL, "open turns.bin to flip a byte");
            if (f != NULL) {
                int c = fgetc(f);
                if (fseek(f, 0L, SEEK_SET) == 0) { fputc(c ^ 0x01, f); }
                fclose(f);
            }
            st = srmech_genome_remove(dir, "A", coupling, sizeof(coupling),
                                      g_ws, sizeof(g_ws));
            check_true(st == SRMECH_ERR_BAD_INPUT,
                       "remove on a corrupt body -> BAD_INPUT (bound fires)");
        }
    }

    /* §43 (rc149): FILE-MANAGEMENT — the chromosome as a bundleable .chr file.
     * Export one chromosome to a self-contained MPR-attested .chr, then import
     * it (SEED a fresh genome / APPEND byte-for-byte) self-verifying. */
    {
        /* clean 2-chromosome body (A + B) to export from (the §45 section left
         * turns.bin corrupt after its last remove-on-corrupt-body test). */
        st = srmech_genome_save(dir, body, sizeof(body), leaf_dim,
                                coupling, sizeof(coupling), g_ws, sizeof(g_ws));
        check_true(st == SRMECH_OK, "re-save clean A+B for the §43 section");

        const char *tbase = getenv("TMPDIR");
        if (tbase == NULL) { tbase = getenv("TMP"); }
        if (tbase == NULL) { tbase = "/tmp"; }
        char chr_path[1024], seed_dir[1024], app_dir[1024], mism_dir[1024];
        snprintf(chr_path, sizeof(chr_path), "%s/srmech_genome_A.chr", tbase);
        snprintf(seed_dir, sizeof(seed_dir), "%s/srmech_genome_seed", tbase);
        snprintf(app_dir, sizeof(app_dir), "%s/srmech_genome_app", tbase);
        snprintf(mism_dir, sizeof(mism_dir), "%s/srmech_genome_mism", tbase);

        /* EXPORT 'A' to A.chr; a missing label is rejected. */
        st = srmech_genome_export(dir, "A", chr_path, NULL, 0u, g_ws, sizeof(g_ws));
        check_true(st == SRMECH_OK, "genome_export('A') OK");
        st = srmech_genome_export(dir, "nope", chr_path, NULL, 0u, g_ws, sizeof(g_ws));
        check_true(st == SRMECH_ERR_BAD_INPUT, "export('nope') rejected");
        st = srmech_genome_export(dir, "A", chr_path, NULL, 0u, g_ws, sizeof(g_ws));
        check_true(st == SRMECH_OK, "re-export('A') OK");

        /* the .chr is a valid MPR-v1 record tagged as a chromosome bundle. */
        {
            unsigned char txt[8192];
            size_t tn = 0u;
            FILE *cf = fopen(chr_path, "rb");
            check_true(cf != NULL, "open A.chr");
            if (cf != NULL) { tn = fread(txt, 1u, sizeof(txt) - 1u, cf); fclose(cf); }
            while (tn > 0u && (txt[tn - 1u] == '\n' || txt[tn - 1u] == '\r')) { tn--; }
            srmech_json_value_t *rec = NULL;
            st = srmech_json_parse((const char *)txt, tn, g_ws, sizeof(g_ws), &rec);
            check_true(st == SRMECH_OK && rec != NULL, "A.chr parses as JSON");
            const char *chr_sid = "srmech://schema/genome_chromosome/v1";
            const srmech_json_value_t *sid =
                (rec != NULL) ? srmech_json_object_get(rec, "data_schema_id") : NULL;
            check_true(sid != NULL && sid->type == SRMECH_JSON_STRING &&
                       sid->u.str.len == (uint32_t)strlen(chr_sid) &&
                       memcmp(sid->u.str.ptr, chr_sid, sid->u.str.len) == 0,
                       "A.chr data_schema_id == chromosome bundle");
            const srmech_json_value_t *d =
                (rec != NULL) ? srmech_json_object_get(rec, "data") : NULL;
            const srmech_json_value_t *reg =
                (d != NULL) ? srmech_json_object_get(d, "region") : NULL;
            check_true(reg != NULL && reg->type == SRMECH_JSON_OBJECT,
                       "A.chr data.region present");
        }

        /* IMPORT SEED: into a fresh empty dest -> turns.bin == A's region (16 B). */
        ensure_dir(seed_dir);
        st = srmech_genome_import(chr_path, seed_dir, NULL, 0u, g_ws, sizeof(g_ws));
        check_true(st == SRMECH_OK, "genome_import SEED OK");
        {
            unsigned char out[64];
            size_t olen = 0u;
            st = srmech_genome_load(seed_dir, out, sizeof(out), &olen,
                                    NULL, 0u, g_ws, sizeof(g_ws));
            check_true(st == SRMECH_OK && olen == 16u &&
                       memcmp(out, body, 16u) == 0,
                       "seeded body == A's region verbatim (16 B)");
            st = srmech_genome_window(seed_dir, "A", out, sizeof(out), &olen,
                                      NULL, 0u, g_ws, sizeof(g_ws));
            check_true(st == SRMECH_OK, "window('A') on the seeded genome OK");
        }

        /* IMPORT APPEND: a dest coupled to the SAME coupling with a different
         * 1-chromosome body -> A is appended byte-for-byte; a dup label fails. */
        ensure_dir(app_dir);
        {
            unsigned char solo[8] = { CC, (unsigned char)'S', 0u, 0u, 3u, 2u, 1u, 0u };
            unsigned char out[64];
            size_t olen = 0u;
            st = srmech_genome_save(app_dir, solo, sizeof(solo), leaf_dim,
                                    coupling, sizeof(coupling), g_ws, sizeof(g_ws));
            check_true(st == SRMECH_OK, "save solo dest for the APPEND case");
            st = srmech_genome_import(chr_path, app_dir, NULL, 0u, g_ws, sizeof(g_ws));
            check_true(st == SRMECH_OK, "genome_import APPEND OK");
            st = srmech_genome_load(app_dir, out, sizeof(out), &olen,
                                    NULL, 0u, g_ws, sizeof(g_ws));
            check_true(st == SRMECH_OK && olen == 24u &&
                       memcmp(out, solo, 8u) == 0 &&
                       memcmp(out + 8, body, 16u) == 0,
                       "appended body == solo + A's region (byte-for-byte)");
            st = srmech_genome_import(chr_path, app_dir, NULL, 0u, g_ws, sizeof(g_ws));
            check_true(st == SRMECH_ERR_BAD_INPUT, "import dup label rejected");
        }

        /* IMPORT into a dest coupled to a DIFFERENT coupling -> BAD_INPUT. */
        ensure_dir(mism_dir);
        {
            unsigned char one_b[4] = { 2u, 1u, 0u, 3u };
            unsigned char solo[8] = { CC, (unsigned char)'S', 0u, 0u, 1u, 0u, 3u, 2u };
            st = srmech_genome_save(mism_dir, solo, sizeof(solo), leaf_dim,
                                    one_b, sizeof(one_b), g_ws, sizeof(g_ws));
            check_true(st == SRMECH_OK, "save coupling-mismatch dest");
            st = srmech_genome_import(chr_path, mism_dir, NULL, 0u, g_ws, sizeof(g_ws));
            check_true(st == SRMECH_ERR_BAD_INPUT, "import coupling-mismatch rejected");
        }

        /* SELF-VERIFY: flip the first region hex digit in A.chr -> import fails. */
        {
            unsigned char txt[8192];
            size_t tn = 0u;
            FILE *cf = fopen(chr_path, "rb");
            if (cf != NULL) { tn = fread(txt, 1u, sizeof(txt) - 1u, cf); fclose(cf); }
            txt[tn] = '\0';
            char *p = strstr((char *)txt, "\"hex\"");   /* region's hex (sorted first) */
            check_true(p != NULL, "locate region hex in A.chr");
            if (p != NULL) {
                p += 5;
                while (*p != '"' && *p != '\0') { p++; }
                if (*p == '"') { p++; *p = (*p == '0') ? '1' : '0'; }
                cf = fopen(chr_path, "wb");
                if (cf != NULL) { fwrite(txt, 1u, tn, cf); fclose(cf); }
            }
            ensure_dir(seed_dir);
            st = srmech_genome_import(chr_path, seed_dir, NULL, 0u, g_ws, sizeof(g_ws));
            check_true(st == SRMECH_ERR_BAD_INPUT,
                       "tampered region -> import self-verify BAD_INPUT");
        }
    }

    /* §43 (rc151): LOOSE<->PACKED — explode the packed genome to a dir of
     * <label>.chr bundles, then pack them back (canonical sorted-label order)
     * into a fresh genome whose turns.bin is byte-identical to the source. */
    {
        /* re-save clean A+B (the §43 section above tampered A.chr, not dir). */
        st = srmech_genome_save(dir, body, sizeof(body), leaf_dim,
                                coupling, sizeof(coupling), g_ws, sizeof(g_ws));
        check_true(st == SRMECH_OK, "re-save clean A+B for the loose<->packed section");

        const char *tbase = getenv("TMPDIR");
        if (tbase == NULL) { tbase = getenv("TMP"); }
        if (tbase == NULL) { tbase = "/tmp"; }
        char loose_dir[1024], packed_dir[1024], a_chr[1100], b_chr[1100];
        snprintf(loose_dir, sizeof(loose_dir), "%s/srmech_genome_loose", tbase);
        snprintf(packed_dir, sizeof(packed_dir), "%s/srmech_genome_packed", tbase);
        snprintf(a_chr, sizeof(a_chr), "%s/A.chr", loose_dir);
        snprintf(b_chr, sizeof(b_chr), "%s/B.chr", loose_dir);

        /* EXPLODE: dir -> loose_dir/{A.chr, B.chr}. */
        ensure_dir(loose_dir);
        st = srmech_genome_explode(dir, loose_dir, NULL, 0u, g_ws, sizeof(g_ws));
        check_true(st == SRMECH_OK, "genome_explode OK");
        {
            FILE *fa = fopen(a_chr, "rb");
            FILE *fb = fopen(b_chr, "rb");
            check_true(fa != NULL && fb != NULL, "explode wrote A.chr + B.chr");
            if (fa != NULL) { fclose(fa); }
            if (fb != NULL) { fclose(fb); }
        }

        /* PACK: loose_dir -> packed_dir; turns.bin == the original body
         * (canonical A<B order seeds with A then appends B = source layout). */
        ensure_dir(packed_dir);
        st = srmech_genome_pack(loose_dir, packed_dir, NULL, 0u, g_ws, sizeof(g_ws));
        check_true(st == SRMECH_OK, "genome_pack OK");
        {
            unsigned char out[64];
            size_t olen = 0u;
            st = srmech_genome_load(packed_dir, out, sizeof(out), &olen,
                                    NULL, 0u, g_ws, sizeof(g_ws));
            check_true(st == SRMECH_OK && olen == sizeof(body) &&
                       memcmp(out, body, sizeof(body)) == 0,
                       "packed body == source body (byte-for-byte, A<B order)");
            st = srmech_genome_window(packed_dir, "A", out, sizeof(out), &olen,
                                      NULL, 0u, g_ws, sizeof(g_ws));
            check_true(st == SRMECH_OK && olen == 16u, "packed window('A') OK (16 B)");
            st = srmech_genome_window(packed_dir, "B", out, sizeof(out), &olen,
                                      NULL, 0u, g_ws, sizeof(g_ws));
            check_true(st == SRMECH_OK && olen == 8u, "packed window('B') OK (8 B)");
        }

        /* PACK of an empty dir (no .chr files) -> BAD_INPUT (not IO). */
        {
            char empty_dir[1024], dst[1024];
            snprintf(empty_dir, sizeof(empty_dir), "%s/srmech_genome_empty", tbase);
            snprintf(dst, sizeof(dst), "%s/srmech_genome_packed_empty", tbase);
            ensure_dir(empty_dir);
            ensure_dir(dst);
            st = srmech_genome_pack(empty_dir, dst, NULL, 0u, g_ws, sizeof(g_ws));
            check_true(st == SRMECH_ERR_BAD_INPUT, "pack of empty dir -> BAD_INPUT");
        }
    }

    /* rc154: >256 chromosomes — the OLD static SRMECH_GENOME_MAX_CHROMS=256
     * struct-of-arrays could NOT hold this; the caller-arena scratch is bounded
     * only by g_ws. 300 chromosomes (leaf_dim 4, 2-char labels), each = 1 CHROM
     * cap + 1 data turn = 8 bytes; the whole body is 2400 bytes. */
    {
        static unsigned char big[300u * 8u];
        static char lbl[300][3];
        const char *alpha =
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
        for (uint32_t i = 0u; i < 300u; i++) {
            lbl[i][0] = alpha[i / 62u];
            lbl[i][1] = alpha[i % 62u];
            lbl[i][2] = '\0';
            unsigned char *leaf = big + (size_t)i * 8u;
            leaf[0] = CC;
            leaf[1] = (unsigned char)lbl[i][0];
            leaf[2] = (unsigned char)lbl[i][1];
            leaf[3] = 0u;
            leaf[4] = 0u; leaf[5] = 1u; leaf[6] = 2u; leaf[7] = 3u;  /* data turn */
        }
        const char *tb = getenv("TMPDIR");
        if (tb == NULL) { tb = getenv("TMP"); }
        if (tb == NULL) { tb = "/tmp"; }
        char big_dir[1024];
        snprintf(big_dir, sizeof(big_dir), "%s/srmech_genome_big", tb);
        ensure_dir(big_dir);
        st = srmech_genome_save(big_dir, big, sizeof(big), leaf_dim,
                                coupling, sizeof(coupling), g_ws, sizeof(g_ws));
        check_true(st == SRMECH_OK, "save 300-chromosome genome (>256, arena-bound)");
        {
            srmech_json_value_t *bm = NULL;
            st = srmech_genome_catalog(big_dir, NULL, 0u, g_ws, sizeof(g_ws), &bm);
            const srmech_json_value_t *bdata =
                (st == SRMECH_OK) ? srmech_json_object_get(bm, "data") : NULL;
            const srmech_json_value_t *arr =
                (bdata != NULL) ? srmech_json_object_get(bdata, "chromosomes") : NULL;
            check_true(arr != NULL && arr->type == SRMECH_JSON_ARRAY &&
                       arr->u.arr.n == 300u, "catalog has 300 chromosomes");
        }
        {
            unsigned char wout[16];
            size_t wlen = 0u;
            st = srmech_genome_window(big_dir, lbl[299], wout, sizeof(wout),
                                      &wlen, NULL, 0u, g_ws, sizeof(g_ws));
            check_true(st == SRMECH_OK && wlen == 8u &&
                       memcmp(wout, big + 299u * 8u, 8u) == 0,
                       "window(300th label) on >256-chrom genome OK (8 B)");
        }
    }

    /* §55/rc114 (issue #1245): format v3 — BIT-PACKED data turns + MIXED
     * bodies. A packed turn is [0x51 'Q'] + ceil(leaf_dim/4) payload bytes
     * (4 Klein-4 symbols per byte, first symbol in the HIGH lanes); caps stay
     * leaf_dim-wide; legacy v2 byte-per-symbol turns remain readable in the
     * SAME walk (back-compat is structural). */
    {
        const unsigned char PQ = (unsigned char)SRMECH_GENOME_PACKED_TURN_MARKER;
        /* leaf_dim=4 -> packed turn = 1 + 1 = 2 bytes. Chrom 'P': cap + a
         * packed turn (symbols 0,1,2,3 -> 0b00011011 = 0x1B); chrom 'L': cap
         * + a LEGACY v2 turn (3,0,2,1). Mixed body: 4+2+4+4 = 14 B, 4 blocks. */
        unsigned char mixed[14] = {
            CC, (unsigned char)'P', 0u, 0u,
            PQ, 0x1Bu,
            CC, (unsigned char)'L', 0u, 0u,
            3u, 0u, 2u, 1u,
        };
        const char *tb = getenv("TMPDIR");
        if (tb == NULL) { tb = getenv("TMP"); }
        if (tb == NULL) { tb = "/tmp"; }
        char mix_dir[1024];
        snprintf(mix_dir, sizeof(mix_dir), "%s/srmech_genome_v3mix", tb);
        ensure_dir(mix_dir);
        st = srmech_genome_save(mix_dir, mixed, sizeof(mixed), leaf_dim,
                                coupling, sizeof(coupling), g_ws, sizeof(g_ws));
        check_true(st == SRMECH_OK, "v3 save of a MIXED packed+legacy body OK");
        {
            srmech_json_value_t *man = NULL;
            st = srmech_genome_catalog(mix_dir, NULL, 0u, g_ws, sizeof(g_ws), &man);
            const srmech_json_value_t *data =
                (st == SRMECH_OK) ? srmech_json_object_get(man, "data") : NULL;
            const srmech_json_value_t *fv =
                (data != NULL) ? srmech_json_object_get(data, "format_version") : NULL;
            check_true(fv != NULL && fv->type == SRMECH_JSON_INT &&
                       fv->u.i == SRMECH_GENOME_FORMAT_VERSION,
                       "mixed-body manifest format_version == the current writer");
            const srmech_json_value_t *nt =
                (data != NULL) ? srmech_json_object_get(data, "n_turns") : NULL;
            check_true(nt != NULL && nt->type == SRMECH_JSON_INT && nt->u.i == 4,
                       "mixed-body n_turns == 4 BLOCKS (variable-width walk)");
            const srmech_json_value_t *chr =
                (data != NULL) ? srmech_json_object_get(data, "chromosomes") : NULL;
            check_true(chr != NULL && chr->type == SRMECH_JSON_ARRAY &&
                       chr->u.arr.n == 2u, "mixed-body has 2 chromosomes");
            if (chr != NULL && chr->u.arr.n == 2u) {
                const srmech_json_value_t *p0 = chr->u.arr.items[0];
                const srmech_json_value_t *p_bl =
                    srmech_json_object_get(p0, "byte_len");
                const srmech_json_value_t *p_lc =
                    srmech_json_object_get(p0, "leaf_count");
                check_true(p_bl != NULL && p_bl->u.i == 6 &&
                           p_lc != NULL && p_lc->u.i == 1,
                           "packed chrom 'P': byte_len 6 (cap 4 + turn 2), leaf_count 1");
                const srmech_json_value_t *l1 = chr->u.arr.items[1];
                const srmech_json_value_t *l_bl =
                    srmech_json_object_get(l1, "byte_len");
                const srmech_json_value_t *l_off =
                    srmech_json_object_get(l1, "byte_offset");
                check_true(l_bl != NULL && l_bl->u.i == 8 &&
                           l_off != NULL && l_off->u.i == 6,
                           "legacy chrom 'L': byte_len 8 at offset 6");
            }
        }
        {
            unsigned char out[64];
            size_t olen = 0u;
            st = srmech_genome_load(mix_dir, out, sizeof(out), &olen,
                                    NULL, 0u, g_ws, sizeof(g_ws));
            check_true(st == SRMECH_OK && olen == sizeof(mixed) &&
                       memcmp(out, mixed, sizeof(mixed)) == 0,
                       "mixed body loads verbatim (bounding passes)");
            st = srmech_genome_window(mix_dir, "P", out, sizeof(out), &olen,
                                      NULL, 0u, g_ws, sizeof(g_ws));
            check_true(st == SRMECH_OK && olen == 6u &&
                       memcmp(out, mixed, 6u) == 0,
                       "window('P') == the 6-byte packed region");
        }
        {
            /* §44 held across the bump: manifest-less rebuild scans the MIXED
             * body (coupling gives the width) — same n_turns/chromosomes. */
            char man_path[1200];
            snprintf(man_path, sizeof(man_path), "%s/manifest.json", mix_dir);
            check_true(remove(man_path) == 0, "delete mixed manifest.json");
            srmech_json_value_t *man = NULL;
            st = srmech_genome_catalog(mix_dir, coupling, sizeof(coupling),
                                       g_ws, sizeof(g_ws), &man);
            const srmech_json_value_t *data =
                (st == SRMECH_OK) ? srmech_json_object_get(man, "data") : NULL;
            const srmech_json_value_t *nt =
                (data != NULL) ? srmech_json_object_get(data, "n_turns") : NULL;
            check_true(st == SRMECH_OK && nt != NULL && nt->u.i == 4,
                       "manifest-less rebuild walks the mixed body (n_turns 4)");
        }
        {
            /* An unrecognised block kind byte is rejected (a packed-format
             * body with a corrupt kind byte cannot silently mis-parse). */
            unsigned char bad[6] = { CC, (unsigned char)'X', 0u, 0u, 0x7Fu, 0u };
            char bad_dir[1024];
            snprintf(bad_dir, sizeof(bad_dir), "%s/srmech_genome_v3bad", tb);
            ensure_dir(bad_dir);
            st = srmech_genome_save(bad_dir, bad, sizeof(bad), leaf_dim,
                                    coupling, sizeof(coupling), g_ws, sizeof(g_ws));
            check_true(st == SRMECH_ERR_BAD_INPUT,
                       "unrecognised block kind byte -> BAD_INPUT");
        }
    }

    /* §96/rc267: per-chromosome cap_kind in the catalog + genome_census +
     * genome_registry. A mixed genome: plasmid 'S' (cap + turn), nuclear 'M' (cap +
     * turn + interior centromere + turn), diploid 'D' (diploid-telomere cap +
     * turn). leaf_dim=4, so labels <= 3 bytes; 8 blocks * 4 = 32 bytes. */
    {
        const unsigned char XC = (unsigned char)SRMECH_GENOME_CENTROMERE_CAP_MARKER;
        const unsigned char DC = (unsigned char)SRMECH_GENOME_DIPLOID_TELOMERE_MARKER;
        unsigned char cbody[32] = {
            CC, (unsigned char)'S', 0u, 0u,  0u, 1u, 2u, 3u,            /* S: 2 blocks */
            CC, (unsigned char)'M', 0u, 0u,  1u, 1u, 1u, 1u,
            XC, 0u, 0u, 0u,  2u, 2u, 2u, 2u,                            /* M: 4 blocks */
            DC, (unsigned char)'D', 0u, 0u,  3u, 0u, 3u, 0u,            /* D: 2 blocks */
        };
        const char *tb = getenv("TMPDIR");
        if (tb == NULL) { tb = getenv("TMP"); }
        if (tb == NULL) { tb = "/tmp"; }
        char cdir[1024];
        snprintf(cdir, sizeof(cdir), "%s/srmech_genome_census", tb);
        ensure_dir(cdir);
        st = srmech_genome_save(cdir, cbody, sizeof(cbody), leaf_dim,
                                coupling, sizeof(coupling), g_ws, sizeof(g_ws));
        check_true(st == SRMECH_OK, "save mixed plasmid+nuclear+diploid genome");

        /* CATALOG carries §96 cap_kind per chromosome (plasmid / nuclear / diploid). */
        {
            srmech_json_value_t *man = NULL;
            st = srmech_genome_catalog(cdir, NULL, 0u, g_ws, sizeof(g_ws), &man);
            const srmech_json_value_t *data =
                (st == SRMECH_OK) ? srmech_json_object_get(man, "data") : NULL;
            const srmech_json_value_t *chr =
                (data != NULL) ? srmech_json_object_get(data, "chromosomes") : NULL;
            check_true(chr != NULL && chr->type == SRMECH_JSON_ARRAY &&
                       chr->u.arr.n == 3u, "cap_kind catalog has 3 chromosomes");
            if (chr != NULL && chr->u.arr.n == 3u) {
                const srmech_json_value_t *k0 =
                    srmech_json_object_get(chr->u.arr.items[0], "cap_kind");
                const srmech_json_value_t *k1 =
                    srmech_json_object_get(chr->u.arr.items[1], "cap_kind");
                const srmech_json_value_t *k2 =
                    srmech_json_object_get(chr->u.arr.items[2], "cap_kind");
                check_true(k0 != NULL && k0->type == SRMECH_JSON_STRING &&
                           k0->u.str.len == 7u &&
                           memcmp(k0->u.str.ptr, "plasmid", 7) == 0,
                           "chrom S cap_kind == plasmid");
                check_true(k1 != NULL && k1->u.str.len == 7u &&
                           memcmp(k1->u.str.ptr, "nuclear", 7) == 0,
                           "chrom M cap_kind == nuclear (interior centromere)");
                check_true(k2 != NULL && k2->u.str.len == 7u &&
                           memcmp(k2->u.str.ptr, "diploid", 7) == 0,
                           "chrom D cap_kind == diploid (0x44 opener)");
            }
        }

        /* CENSUS: types {1,1,1}, total_leaves 4, topology nuclear-like. */
        {
            srmech_json_value_t *cen = NULL;
            st = srmech_genome_census(cdir, NULL, 0u, g_ws, sizeof(g_ws), &cen);
            check_true(st == SRMECH_OK && cen != NULL, "genome_census OK");
            const srmech_json_value_t *nc =
                (cen != NULL) ? srmech_json_object_get(cen, "n_chromosomes") : NULL;
            check_true(nc != NULL && nc->u.i == 3, "census n_chromosomes == 3");
            const srmech_json_value_t *types =
                (cen != NULL) ? srmech_json_object_get(cen, "types") : NULL;
            const srmech_json_value_t *ts =
                (types != NULL) ? srmech_json_object_get(types, "plasmid") : NULL;
            const srmech_json_value_t *tm =
                (types != NULL) ? srmech_json_object_get(types, "nuclear") : NULL;
            const srmech_json_value_t *td =
                (types != NULL) ? srmech_json_object_get(types, "diploid") : NULL;
            check_true(ts != NULL && ts->u.i == 1 && tm != NULL && tm->u.i == 1 &&
                       td != NULL && td->u.i == 1, "census types {plasmid,nuclear,diploid}=1,1,1");
            const srmech_json_value_t *tl =
                (cen != NULL) ? srmech_json_object_get(cen, "total_leaves") : NULL;
            check_true(tl != NULL && tl->u.i == 4, "census total_leaves == 4");
            const srmech_json_value_t *topo =
                (cen != NULL) ? srmech_json_object_get(cen, "topology") : NULL;
            check_true(topo != NULL && topo->type == SRMECH_JSON_STRING &&
                       topo->u.str.len == 12u &&
                       memcmp(topo->u.str.ptr, "nuclear-like", 12) == 0,
                       "census topology == nuclear-like");
        }

        /* CENSUS of a small all-plasmid genome -> organelle-like. */
        {
            unsigned char pbody[16] = {
                CC, (unsigned char)'a', 0u, 0u,  0u, 1u, 2u, 3u,
                CC, (unsigned char)'b', 0u, 0u,  1u, 0u, 3u, 2u,
            };
            char pdir[1024];
            snprintf(pdir, sizeof(pdir), "%s/srmech_genome_organelle", tb);
            ensure_dir(pdir);
            st = srmech_genome_save(pdir, pbody, sizeof(pbody), leaf_dim,
                                    coupling, sizeof(coupling), g_ws, sizeof(g_ws));
            check_true(st == SRMECH_OK, "save small all-plasmid (organelle) genome");
            srmech_json_value_t *cen = NULL;
            st = srmech_genome_census(pdir, NULL, 0u, g_ws, sizeof(g_ws), &cen);
            const srmech_json_value_t *topo =
                (st == SRMECH_OK) ? srmech_json_object_get(cen, "topology") : NULL;
            check_true(topo != NULL && topo->u.str.len == 14u &&
                       memcmp(topo->u.str.ptr, "organelle-like", 14) == 0,
                       "small all-plasmid census -> organelle-like");
        }

        /* REGISTRY: a root of 2 genome dirs (+ a non-genome dir, ignored). */
        {
            char rroot[1024], sub[1200];
            snprintf(rroot, sizeof(rroot), "%s/srmech_genome_cell", tb);
            ensure_dir(rroot);
            snprintf(sub, sizeof(sub), "%s/aaa", rroot);
            ensure_dir(sub);
            st = srmech_genome_save(sub, cbody, sizeof(cbody), leaf_dim,
                                    coupling, sizeof(coupling), g_ws, sizeof(g_ws));
            check_true(st == SRMECH_OK, "registry: save genome 'aaa' (nucleus)");
            unsigned char pbody[16] = {
                CC, (unsigned char)'a', 0u, 0u,  0u, 1u, 2u, 3u,
                CC, (unsigned char)'b', 0u, 0u,  1u, 0u, 3u, 2u,
            };
            snprintf(sub, sizeof(sub), "%s/bbb", rroot);
            ensure_dir(sub);
            st = srmech_genome_save(sub, pbody, sizeof(pbody), leaf_dim,
                                    coupling, sizeof(coupling), g_ws, sizeof(g_ws));
            check_true(st == SRMECH_OK, "registry: save genome 'bbb' (organelle)");
            snprintf(sub, sizeof(sub), "%s/notgenome", rroot);
            ensure_dir(sub);                        /* no turns.bin -> ignored */

            srmech_json_value_t *reg = NULL;
            st = srmech_genome_registry(rroot, NULL, 0u, g_ws, sizeof(g_ws), &reg);
            check_true(st == SRMECH_OK && reg != NULL, "genome_registry OK");
            const srmech_json_value_t *ng =
                (reg != NULL) ? srmech_json_object_get(reg, "n_genomes") : NULL;
            check_true(ng != NULL && ng->u.i == 2,
                       "registry n_genomes == 2 (non-genome dir ignored)");
            const srmech_json_value_t *gs =
                (reg != NULL) ? srmech_json_object_get(reg, "genomes") : NULL;
            check_true(gs != NULL && gs->type == SRMECH_JSON_ARRAY &&
                       gs->u.arr.n == 2u, "registry genomes array has 2");
            if (gs != NULL && gs->u.arr.n == 2u) {  /* sorted by name: aaa, bbb */
                const srmech_json_value_t *t0 =
                    srmech_json_object_get(gs->u.arr.items[0], "topology");
                const srmech_json_value_t *t1 =
                    srmech_json_object_get(gs->u.arr.items[1], "topology");
                check_true(t0 != NULL && t0->u.str.len == 12u &&
                           memcmp(t0->u.str.ptr, "nuclear-like", 12) == 0,
                           "registry[0] 'aaa' -> nuclear-like");
                check_true(t1 != NULL && t1->u.str.len == 14u &&
                           memcmp(t1->u.str.ptr, "organelle-like", 14) == 0,
                           "registry[1] 'bbb' -> organelle-like");
            }
        }
    }

    /* §98/rc268: the CHROMATIN access cap writer (srmech_genome_chromatin) + strand read
     * (srmech_genome_chromatin_of). leaf_dim2 = 32 (a chromatin cap's [marker + handle + NUL +
     * type + num(8) + den(8)] needs >= 19 bytes, so the leaf_dim=4 body above is too narrow). */
    {
        const uint32_t ld2 = 32u;
        unsigned char strand[4u * 32u];
        unsigned char tmp[32];
        unsigned char ctype;
        uint64_t num, den;
        size_t at;
        int found;

        /* HEAD scope: [CHROM cap, CHROMATIN(binary condensed 0/1), turn, turn] -> at == 0. */
        memset(strand, 0, sizeof(strand));
        strand[0] = CC; strand[1] = (unsigned char)'c';           /* block 0: a CHROM boundary cap */
        st = srmech_genome_chromatin(SRMECH_GENOME_CHROMATIN_TYPE_BINARY, 0u, 1u,
                                     (const unsigned char *)"chr", 3u, ld2,
                                     strand + ld2, ld2);          /* block 1: the chromatin cap */
        check_true(st == SRMECH_OK, "chromatin cap writer OK (binary condensed)");
        check_true(strand[ld2] == (unsigned char)SRMECH_GENOME_CHROMATIN_MARKER,
                   "chromatin cap first byte == 0x48");
        strand[2u * ld2] = 1u; strand[2u * ld2 + 1u] = 2u;        /* block 2: a Klein-4 data turn */
        strand[3u * ld2] = 3u;                                    /* block 3: a Klein-4 data turn */
        ctype = 9u; num = 9u; den = 9u; at = 99u; found = -1;
        st = srmech_genome_chromatin_of(strand, 4u, ld2, &ctype, &num, &den, &at, &found);
        check_true(st == SRMECH_OK && found == 1, "chromatin_of finds the head marker");
        check_true(ctype == SRMECH_GENOME_CHROMATIN_TYPE_BINARY && num == 0u && den == 1u,
                   "chromatin_of reads binary condensed (0/1)");
        check_true(at == 0u, "chromatin_of at == 0 (head / whole-chromosome scope)");

        /* INTERIOR STRETCH: [CHROM cap, turn, CHROMATIN(graded 1/3), turn] -> at == 1. */
        memset(strand, 0, sizeof(strand));
        strand[0] = CC; strand[1] = (unsigned char)'c';
        strand[ld2] = 1u; strand[ld2 + 1u] = 2u;                 /* block 1: a data turn */
        st = srmech_genome_chromatin(SRMECH_GENOME_CHROMATIN_TYPE_GRADED, 1u, 3u,
                                     (const unsigned char *)"chr", 3u, ld2,
                                     strand + 2u * ld2, ld2);     /* block 2: the chromatin cap */
        check_true(st == SRMECH_OK, "chromatin cap writer OK (graded 1/3)");
        strand[3u * ld2] = 3u;                                    /* block 3: a data turn */
        ctype = 9u; num = 9u; den = 9u; at = 99u; found = -1;
        st = srmech_genome_chromatin_of(strand, 4u, ld2, &ctype, &num, &den, &at, &found);
        check_true(st == SRMECH_OK && found == 1 &&
                   ctype == SRMECH_GENOME_CHROMATIN_TYPE_GRADED && num == 1u && den == 3u,
                   "chromatin_of reads graded 1/3");
        check_true(at == 1u, "chromatin_of at == 1 (interior stretch scope)");

        /* a chromatin-FREE strand -> found == 0 (all-euchromatin default). */
        memset(strand, 0, sizeof(strand));
        strand[0] = CC; strand[ld2] = 1u;
        found = -1;
        st = srmech_genome_chromatin_of(strand, 2u, ld2, NULL, NULL, NULL, NULL, &found);
        check_true(st == SRMECH_OK && found == 0, "chromatin_of: chromatin-free -> not found");

        /* the writer rejects a bad level (num > den) and a too-small dim. */
        st = srmech_genome_chromatin(SRMECH_GENOME_CHROMATIN_TYPE_BINARY, 5u, 1u,
                                     NULL, 0u, ld2, tmp, ld2);
        check_true(st == SRMECH_ERR_BAD_INPUT, "chromatin writer rejects num > den");
        st = srmech_genome_chromatin(SRMECH_GENOME_CHROMATIN_TYPE_BINARY, 0u, 1u,
                                     NULL, 0u, 4u, tmp, 4u);
        check_true(st == SRMECH_ERR_BAD_INPUT, "chromatin writer rejects dim too small");
    }

    /* §98/rc269: the DEMAND-LOAD PATH plan (srmech_genome_gene_express_plan) respects the HEAD
     * chromatin cap — a CONDENSED region is SKIPPED reading ONLY its chromatin cap (its gene
     * gate cap is NEVER touched). Layout (leaf_dim2 = 32); each community is a plain always-on
     * GENE gate, so at cell_state 0 the HEAD chromatin cap alone decides inclusion:
     *   "op": [CHROM, CHROMATIN open(1,1),      GENE, turn] -> INCLUDED (euchromatin)
     *   "cn": [CHROM, CHROMATIN condensed(0,1), GENE, turn] -> SKIPPED  (heterochromatin)
     *   "fr": [CHROM,                           GENE, turn] -> INCLUDED (chromatin-free) */
    {
        const uint32_t ld2 = 32u;
        unsigned char one32[32];
        for (size_t k = 0u; k < 32u; k++) { one32[k] = (unsigned char)(k & 3u); }
        unsigned char pbody[11u * 32u];
        memset(pbody, 0, sizeof(pbody));
        pbody[0u * ld2] = CC; pbody[0u * ld2 + 1u] = (unsigned char)'o';
        pbody[0u * ld2 + 2u] = (unsigned char)'p';
        st = srmech_genome_chromatin(SRMECH_GENOME_CHROMATIN_TYPE_BINARY, 1u, 1u,
                                     (const unsigned char *)"chr", 3u, ld2,
                                     pbody + 1u * ld2, ld2);           /* OPEN (1,1) */
        check_true(st == SRMECH_OK, "plan: op chromatin OPEN cap written");
        pbody[2u * ld2] = GC; pbody[2u * ld2 + 1u] = (unsigned char)'o';
        pbody[2u * ld2 + 2u] = (unsigned char)'p';
        pbody[3u * ld2] = 1u;                                         /* a data turn */
        pbody[4u * ld2] = CC; pbody[4u * ld2 + 1u] = (unsigned char)'c';
        pbody[4u * ld2 + 2u] = (unsigned char)'n';
        st = srmech_genome_chromatin(SRMECH_GENOME_CHROMATIN_TYPE_BINARY, 0u, 1u,
                                     (const unsigned char *)"chr", 3u, ld2,
                                     pbody + 5u * ld2, ld2);           /* CONDENSED (0,1) */
        check_true(st == SRMECH_OK, "plan: cn chromatin CONDENSED cap written");
        pbody[6u * ld2] = GC; pbody[6u * ld2 + 1u] = (unsigned char)'c';
        pbody[6u * ld2 + 2u] = (unsigned char)'n';
        pbody[7u * ld2] = 1u;
        pbody[8u * ld2] = CC; pbody[8u * ld2 + 1u] = (unsigned char)'f';
        pbody[8u * ld2 + 2u] = (unsigned char)'r';
        pbody[9u * ld2] = GC; pbody[9u * ld2 + 1u] = (unsigned char)'f';
        pbody[9u * ld2 + 2u] = (unsigned char)'r';
        pbody[10u * ld2] = 1u;

        char plan_dir[1200];
        snprintf(plan_dir, sizeof(plan_dir), "%s_plan", dir);
        ensure_dir(plan_dir);
        st = srmech_genome_save(plan_dir, pbody, sizeof(pbody), ld2,
                                one32, sizeof(one32), g_ws, sizeof(g_ws));
        check_true(st == SRMECH_OK, "plan: genome_save OK (op/cn/fr)");

        unsigned char pout[512];
        size_t plen = 0u;
        st = srmech_genome_gene_express_plan(plan_dir, 0u, one32, sizeof(one32),
                                             pout, sizeof(pout), &plen,
                                             g_ws, sizeof(g_ws));
        check_true(st == SRMECH_OK, "plan: gene_express_plan OK");
        /* parse [u32 n]{ (u32 label_len)(label)(u64 off)(u64 len) }* (all big-endian). */
        int saw_op = 0, saw_cn = 0, saw_fr = 0;
        uint32_t n = ((uint32_t)pout[0] << 24) | ((uint32_t)pout[1] << 16) |
                     ((uint32_t)pout[2] << 8) | (uint32_t)pout[3];
        size_t p = 4u;
        for (uint32_t r = 0u; r < n && p + 4u <= plen; r++) {
            uint32_t ll = ((uint32_t)pout[p] << 24) | ((uint32_t)pout[p + 1u] << 16) |
                          ((uint32_t)pout[p + 2u] << 8) | (uint32_t)pout[p + 3u];
            p += 4u;
            if (p + ll + 16u > plen) { break; }
            if (ll == 2u && pout[p] == (unsigned char)'o' &&
                pout[p + 1u] == (unsigned char)'p') { saw_op = 1; }
            if (ll == 2u && pout[p] == (unsigned char)'c' &&
                pout[p + 1u] == (unsigned char)'n') { saw_cn = 1; }
            if (ll == 2u && pout[p] == (unsigned char)'f' &&
                pout[p + 1u] == (unsigned char)'r') { saw_fr = 1; }
            p += ll + 16u;                                   /* label + off(8) + len(8) */
        }
        check_true(n == 2u, "plan: exactly 2 communities expressed (op + fr)");
        check_true(saw_op == 1, "plan: 'op' (euchromatin) INCLUDED");
        check_true(saw_fr == 1, "plan: 'fr' (chromatin-free) INCLUDED");
        check_true(saw_cn == 0, "plan: 'cn' (heterochromatin) SKIPPED");
    }

    /* rc270 §100 GAP 1: MINT a GRAPH strand. mint_strand splices a §95a interior
     * centromere (0x58) into an ALREADY-PACKED strand — a PURE composition over the
     * srmech_genome_centromere cap-writer + a strand splice (NO new C symbol). The
     * C-host story proven here: encode a directed graph, lay its Klein-4 syms across
     * content leaves, SPLICE a real centromere cap between them, save -> census NUCLEAR,
     * and recover the graph BYTE-EXACT after the splice (recall skips the cap). */
    {
        const uint32_t ldg = 32u;                     /* the C genome coupling caps at 32 bytes */
        uint64_t ei[6] = {0u, 1u, 2u, 3u, 4u, 0u};
        uint64_t ej[6] = {1u, 2u, 0u, 4u, 3u, 2u};
        uint64_t gw[6] = {5u, 7u, 2u, 9u, 3u, 8u};
        int64_t  gc[6] = {1, -1, 1, -1, 0, 1};
        uint64_t gnid[3] = {100u, 200u, 300u};
        uint64_t gex[2] = {42u, 7u};
        uint8_t syms[256];
        size_t nsy = 0u;
        srmech_status_t gs = srmech_graph_kernel_encode(
            5u, ei, ej, gw, gc, 6u, gnid, 3u, gex, 2u, syms, sizeof(syms), &nsy);
        check_true(gs == SRMECH_OK && nsy > 0u && nsy <= 256u,
                   "rc270: graph_kernel_encode OK");

        /* baseline: decode the raw syms (the un-minted graph). */
        uint64_t bvs = 0u, bei[16], bej[16], bw[16], bnid[16], bex[16];
        int64_t  bch[16];
        size_t bne = 0u, bnn = 0u, bnx = 0u;
        gs = srmech_graph_kernel_decode(syms, nsy, &bvs, bei, bej, bw, bch, 16u,
                                        &bne, bnid, 16u, &bnn, bex, 16u, &bnx);
        check_true(gs == SRMECH_OK && bvs == 5u && bne == 6u && bch[1] == -1 &&
                   bnn == 3u && bnx == 2u, "rc270: graph_kernel_decode baseline OK");

        /* lay the syms across content leaves (zero-padded); force >= 2 so the mint
         * splits at a genuinely INTERIOR point (the metacentric midpoint). */
        size_t n_leaves = (nsy + ldg - 1u) / ldg;
        if (n_leaves < 2u) { n_leaves = 2u; }
        size_t split = n_leaves / 2u;                 /* content turns before the cap */
        unsigned char gbody[8u * 64u];
        memset(gbody, 0, sizeof(gbody));
        /* block 0: a CHROM boundary cap 'G'. */
        gbody[0] = CC; gbody[1] = (unsigned char)'G';
        /* content leaves, with a centromere cap spliced after `split` of them. */
        size_t blk = 1u;
        for (size_t L = 0u; L < n_leaves; L++) {
            if (L == split) {
                st = srmech_genome_centromere(
                    2u, 15u, (const unsigned char *)"cen", 3u, ldg,
                    gbody + blk * ldg, ldg);          /* the real cap mint_strand splices */
                check_true(st == SRMECH_OK, "rc270: centromere cap writer OK");
                check_true(gbody[blk * ldg] ==
                           (unsigned char)SRMECH_GENOME_CENTROMERE_CAP_MARKER,
                           "rc270: spliced cap first byte == 0x58");
                blk++;
            }
            for (uint32_t k = 0u; k < ldg; k++) {
                size_t si = L * (size_t)ldg + k;
                gbody[blk * ldg + k] = (si < nsy) ? syms[si] : 0u;
            }
            blk++;
        }
        size_t n_blocks = blk;                        /* split = n_leaves/2 < n_leaves */

        /* SAVE -> CENSUS: the graph chromosome now reads NUCLEAR (interior 0x58). */
        unsigned char one_g[32];
        for (uint32_t i = 0u; i < 32u; i++) { one_g[i] = (unsigned char)(i & 3u); }
        const char *tbg = getenv("TMPDIR");
        if (tbg == NULL) { tbg = getenv("TMP"); }
        if (tbg == NULL) { tbg = "/tmp"; }
        char gdir[1024];
        snprintf(gdir, sizeof(gdir), "%s/srmech_genome_mintgraph", tbg);
        ensure_dir(gdir);
        st = srmech_genome_save(gdir, gbody, n_blocks * (size_t)ldg, ldg,
                                one_g, sizeof(one_g), g_ws, sizeof(g_ws));
        check_true(st == SRMECH_OK, "rc270: save minted graph strand");
        {
            srmech_json_value_t *cen = NULL;
            st = srmech_genome_census(gdir, NULL, 0u, g_ws, sizeof(g_ws), &cen);
            const srmech_json_value_t *types =
                (st == SRMECH_OK && cen != NULL)
                    ? srmech_json_object_get(cen, "types") : NULL;
            const srmech_json_value_t *tm =
                (types != NULL) ? srmech_json_object_get(types, "nuclear") : NULL;
            const srmech_json_value_t *ts =
                (types != NULL) ? srmech_json_object_get(types, "plasmid") : NULL;
            check_true(tm != NULL && tm->u.i == 1 && ts != NULL && ts->u.i == 0,
                       "rc270: minted graph chromosome censuses as nuclear");
        }

        /* RECOVER: skip every cap (recall), concatenate the content leaves, take the
         * first nsy syms, decode -> BYTE-EXACT vs the un-minted baseline. */
        uint8_t rsyms[256];
        size_t rn = 0u;
        for (size_t b = 0u; b < n_blocks; b++) {
            if (gbody[b * (size_t)ldg] > 3u) { continue; }   /* a cap — skip */
            for (uint32_t k = 0u; k < ldg && rn < nsy; k++) {
                rsyms[rn++] = gbody[b * (size_t)ldg + k];
            }
        }
        check_true(rn == nsy, "rc270: recovered syms count == nsy (cap skipped)");
        uint64_t mvs = 0u, mei[16], mej[16], mw[16], mnid[16], mex[16];
        int64_t  mch[16];
        size_t mne = 0u, mnn = 0u, mnx = 0u;
        gs = srmech_graph_kernel_decode(rsyms, rn, &mvs, mei, mej, mw, mch, 16u,
                                        &mne, mnid, 16u, &mnn, mex, 16u, &mnx);
        check_true(gs == SRMECH_OK && mvs == bvs && mne == bne && mnn == bnn &&
                   mnx == bnx, "rc270: minted graph decode dims match baseline");
        int same = (mch[0] == bch[0]) && (mch[1] == bch[1]) && (mw[3] == bw[3]) &&
                   (mnid[2] == bnid[2]) && (mex[0] == bex[0]) && (mei[5] == bei[5]);
        check_true(same == 1,
                   "rc270: kernel_to_graph BYTE-EXACT after minting (cap transparent)");
    }

    /* §135/rc273 (F1251) — GENE COPY-NUMBER forward-compat: a plain GENE cap (0x47)
     * carrying a copy-number field (a non-zero uint64 BE RIGHT AFTER the label's NUL,
     * in what was NUL padding) still reads as ALWAYS-EXPRESSED via srmech_genome_gene_
     * express (the C wire-format back/forward-compat: the count is TRANSPARENT to the C
     * reader, which returns on the 0x47 marker BEFORE reading any field — the same
     * discipline the Python _gene_expresses uses). This is the C proof that amplify's
     * additive field needs no format bump (v15 stays).
     *
     * ⚠️ rc281 CORRECTION: this block used to conclude "and no C change" — it does NOT
     * show that. Transparency proves an existing C READER is not BROKEN by the field; it
     * says nothing about whether a C host can USE it. Until rc281 there was no C path to
     * WRITE the count or READ its value, so a bare-C host could only ignore the axis. The
     * rc281 block below covers the two peers that actually close that gap. */
    {
        const uint32_t ld = 16u;
        unsigned char cap[16];
        memset(cap, 0, sizeof(cap));
        cap[0] = (unsigned char)SRMECH_GENOME_GENE_CAP_MARKER;  /* 0x47 plain gene */
        cap[1] = (unsigned char)'r';                            /* label "r" */
        cap[2] = 0u;                                            /* label NUL terminator */
        /* copy_number = 7 as uint64 big-endian in cap[3..10] (was NUL padding). */
        cap[3] = 0u; cap[4] = 0u; cap[5] = 0u; cap[6] = 0u;
        cap[7] = 0u; cap[8] = 0u; cap[9] = 0u; cap[10] = 7u;
        int expressed = -1;
        uint64_t mask = 0xDEADu;
        srmech_status_t cst = srmech_genome_gene_express(cap, ld, 0u, &expressed, &mask);
        check_true(cst == SRMECH_OK && expressed == 1 && mask == 0u,
                   "rc273: plain gene w/ copy-number field reads always-express (count transparent)");
        /* A gene with NO field (all-NUL padding, the pre-rc273 / copy-number-1 form)
         * reads identically — same always-express verdict. */
        unsigned char plain[16];
        memset(plain, 0, sizeof(plain));
        plain[0] = (unsigned char)SRMECH_GENOME_GENE_CAP_MARKER;
        plain[1] = (unsigned char)'r';
        int expressed2 = -1;
        uint64_t mask2 = 0xBEEFu;
        srmech_status_t cst2 = srmech_genome_gene_express(plain, ld, 0u, &expressed2, &mask2);
        check_true(cst2 == SRMECH_OK && expressed2 == 1 && mask2 == 0u,
                   "rc273: plain gene (no copy-number, copy_number 1) reads always-express");
    }

    /* §95.1d/rc276 (F1244 / G4) — srmech_genome_integrate SPLICE + gate. Host has TWO
     * chromosomes A (blocks 0..1) + B (blocks 2..4); provirus P is ONE chromosome
     * (blocks 0..1). Boundary caps at host blocks 0 (A) and 2 (B) => 2 chromosomes.
     * Verify every `at` locus + the honest-decline gate against a hand-built oracle. */
    {
        const uint32_t ld = 4u;
        unsigned char H[20] = {
            CC,'A',0,0,   0,1,2,3,      /* chrom A: cap + 1 turn   (blocks 0,1) */
            CC,'B',0,0,   2,2,1,1,  3,0,2,1,  /* chrom B: cap + 2 turns (blocks 2,3,4) */
        };
        unsigned char P[8] = { CC,'P',0,0,   1,1,2,2 };   /* provirus: cap + 1 turn */
        unsigned char got[64];
        unsigned char exp[64];
        /* (a) at locus-block combos: -1(None)->5, 0->0, 1->2, 2(==nchrom)->5. */
        long ats[4]   = { -1L, 0L, 1L, 2L };
        size_t locs[4] = { 5u, 0u, 2u, 5u };            /* expected locus, in blocks */
        const char *tags[4] = { "at=None (append last)", "at=0 (before A)",
                                "at=1 (before B)", "at=2 (== nchrom, append last)" };
        for (int c = 0; c < 4; c++) {
            size_t loc = locs[c];
            size_t nbo = 0u; int integ = -1;
            srmech_status_t ist = srmech_genome_integrate(
                H, 5u, ld, P, 2u, ld, ats[c], got, sizeof(got), &nbo, &integ);
            /* oracle: H[:loc] + P + H[loc:] */
            memcpy(exp, H, loc * ld);
            memcpy(exp + loc * ld, P, sizeof(P));
            memcpy(exp + loc * ld + sizeof(P), H + loc * ld, sizeof(H) - loc * ld);
            check_true(ist == SRMECH_OK && integ == 1 && nbo == 7u &&
                       memcmp(got, exp, sizeof(H) + sizeof(P)) == 0, tags[c]);
        }
        /* (b) empty host coheres -> out == provirus. */
        {
            size_t nbo = 0u; int integ = -1;
            srmech_status_t ist = srmech_genome_integrate(
                NULL, 0u, ld, P, 2u, ld, -1L, got, sizeof(got), &nbo, &integ);
            check_true(ist == SRMECH_OK && integ == 1 && nbo == 2u &&
                       memcmp(got, P, sizeof(P)) == 0, "rc276: empty host -> provirus");
        }
        /* (c) width incoherence -> HONEST-DECLINE (integrated 0, nothing written). */
        {
            unsigned char P8[16] = { CC,'Q',0,0,0,0,0,0,  1,1,2,2,0,0,0,0 };
            size_t nbo = 99u; int integ = -1;
            srmech_status_t ist = srmech_genome_integrate(
                H, 5u, ld, P8, 2u, 8u, -1L, got, sizeof(got), &nbo, &integ);
            check_true(ist == SRMECH_OK && integ == 0,
                       "rc276: width mismatch -> honest-decline (integrated 0)");
        }
        /* (d) at out of range -> BAD_INPUT (2 chromosomes, at=3 > 2). */
        {
            size_t nbo = 0u; int integ = -1;
            srmech_status_t ist = srmech_genome_integrate(
                H, 5u, ld, P, 2u, ld, 3L, got, sizeof(got), &nbo, &integ);
            check_true(ist == SRMECH_ERR_BAD_INPUT, "rc276: at out of range -> BAD_INPUT");
        }
        /* (e) provirus not opening with a boundary cap -> BAD_INPUT. */
        {
            unsigned char bad[8] = { 0,1,2,3,  1,1,1,1 };   /* first block is a data turn */
            size_t nbo = 0u; int integ = -1;
            srmech_status_t ist = srmech_genome_integrate(
                H, 5u, ld, bad, 2u, ld, -1L, got, sizeof(got), &nbo, &integ);
            check_true(ist == SRMECH_ERR_BAD_INPUT, "rc276: provirus no boundary cap -> BAD_INPUT");
        }
        /* (f) out_cap too small -> OVERFLOW. */
        {
            unsigned char tiny[8];
            size_t nbo = 0u; int integ = -1;
            srmech_status_t ist = srmech_genome_integrate(
                H, 5u, ld, P, 2u, ld, -1L, tiny, sizeof(tiny), &nbo, &integ);
            check_true(ist == SRMECH_ERR_OVERFLOW, "rc276: out_cap too small -> OVERFLOW");
        }
    }

    /* §100 GAP 1/rc277 (F1249 / G5) — srmech_genome_mint_strand PROMOTE + splice. Build a
     * packed strand (CHROM boundary cap + 6 Klein-4 data turns), MINT it (splice a §95a
     * 0x58 centromere at the metacentric midpoint), and verify: n_blocks+1 out; the cap
     * lands after 3 data turns (6//2) and decodes to the given orientation + p:q = 3:3;
     * recall is byte-exact after minting (the cap is transparent, §44); the content-address
     * orientation is a valid 0..3 sector; and the error paths. leaf_dim 24 fits the
     * 21-byte cap payload (marker + "cen" + NUL + R=15 + 15 votes). */
    {
        const uint32_t ld = 24u;
        unsigned char one_m[24];
        for (uint32_t i = 0u; i < ld; i++) { one_m[i] = (unsigned char)(i & 3u); }
        unsigned char S[7u * 24u];            /* 1 cap + 6 turns = 7 blocks */
        memset(S, 0, sizeof(S));
        S[0] = CC; S[1] = (unsigned char)'M';                 /* CHROM boundary cap */
        for (size_t t = 0u; t < 6u; t++) {                    /* 6 data turns, bytes 0..3 */
            for (uint32_t k = 0u; k < ld; k++) {
                S[(1u + t) * ld + k] = (unsigned char)((t + k) & 3u);
            }
        }
        unsigned char M[8u * 24u];
        size_t mnb = 0u;
        /* (a) explicit orientation 2, midpoint (centromere_at = -1). */
        srmech_status_t ms = srmech_genome_mint_strand(
            S, 7u, ld, one_m, -1L, 2u, 0, 15u, (const unsigned char *)"cen", 3u,
            M, sizeof(M), &mnb);
        check_true(ms == SRMECH_OK && mnb == 8u, "rc277: mint_strand OK, n_blocks+1");
        check_true(M[4u * ld] == (unsigned char)SRMECH_GENOME_CENTROMERE_CAP_MARKER,
                   "rc277: centromere spliced at the metacentric midpoint (block 4)");
        {   /* centromere_of the minted strand -> orientation 2, p:q = 3:3. */
            unsigned char o = 9u; size_t p = 0u, q = 0u; int found = 0;
            srmech_status_t cs = srmech_genome_centromere_of(M, mnb, ld, &o, &p, &q,
                                                             &found);
            check_true(cs == SRMECH_OK && found == 1 && o == 2u && p == 3u && q == 3u,
                       "rc277: minted cap decodes orientation 2, p:q = 3:3");
        }
        {   /* recall the minted strand == recall the original (the cap is transparent). */
            unsigned char r0[6u * 24u], r1[6u * 24u]; size_t n0 = 0u, n1 = 0u;
            srmech_status_t a = srmech_genome_recall(S, 7u, ld, one_m, r0, sizeof(r0),
                                                     &n0);
            srmech_status_t b = srmech_genome_recall(M, mnb, ld, one_m, r1, sizeof(r1),
                                                     &n1);
            check_true(a == SRMECH_OK && b == SRMECH_OK && n0 == 6u && n1 == 6u &&
                       memcmp(r0, r1, n0 * ld) == 0,
                       "rc277: recall byte-exact after minting (cap transparent)");
        }
        /* (b) content-address orientation (orientation_auto=1) -> a valid 0..3 sector. */
        {
            size_t nb2 = 0u;
            srmech_status_t ms2 = srmech_genome_mint_strand(
                S, 7u, ld, one_m, -1L, 0u, 1, 15u, (const unsigned char *)"cen", 3u,
                M, sizeof(M), &nb2);
            unsigned char o = 9u; size_t p = 0u, q = 0u; int found = 0;
            (void)srmech_genome_centromere_of(M, nb2, ld, &o, &p, &q, &found);
            check_true(ms2 == SRMECH_OK && nb2 == 8u && found == 1 && o <= 3u,
                       "rc277: content-address orientation mints a valid 0..3 sector");
        }
        /* (c) already-minted (a 0x58 present) -> BAD_INPUT (M carries a centromere from b). */
        {
            size_t nb3 = 0u;
            srmech_status_t ms3 = srmech_genome_mint_strand(
                M, 8u, ld, one_m, -1L, 0u, 1, 15u, (const unsigned char *)"cen", 3u,
                M, sizeof(M), &nb3);
            check_true(ms3 == SRMECH_ERR_BAD_INPUT, "rc277: already-minted -> BAD_INPUT");
        }
        /* (d) not opening with a boundary cap -> BAD_INPUT (first block is a data turn). */
        {
            unsigned char bad[2u * 24u]; size_t nb4 = 0u;
            memset(bad, 0, sizeof(bad));
            bad[0] = 1u;                                       /* a Klein-4 turn, not a cap */
            srmech_status_t ms4 = srmech_genome_mint_strand(
                bad, 2u, ld, one_m, -1L, 2u, 0, 15u, (const unsigned char *)"cen", 3u,
                M, sizeof(M), &nb4);
            check_true(ms4 == SRMECH_ERR_BAD_INPUT, "rc277: no boundary cap -> BAD_INPUT");
        }
        /* (e) out_cap too small -> OVERFLOW. */
        {
            unsigned char tiny[24]; size_t nb5 = 0u;
            srmech_status_t ms5 = srmech_genome_mint_strand(
                S, 7u, ld, one_m, -1L, 2u, 0, 15u, (const unsigned char *)"cen", 3u,
                tiny, sizeof(tiny), &nb5);
            check_true(ms5 == SRMECH_ERR_OVERFLOW, "rc277: out_cap too small -> OVERFLOW");
        }
    }

    /* §102 / rc278 (F1252 STAGE 1 — EXTRACT) — srmech_genome_plasmid_extract:
     * compose graph_kernel_encode -> the §89 KERNEL-region build -> genome_append
     * into a seeded store; the appended section round-trips (window -> recall ->
     * graph_kernel_decode) to the ORIGINAL graph with its GLOBAL node_ids. */
    {
        const uint32_t ld = 64u;                 /* >= 52 for the §89 header leaf */
        unsigned char one_p[64];
        char pdir[1100];
        unsigned char seed[64];
        uint64_t ei[2] = { 0u, 1u }, ej[2] = { 1u, 2u }, ww[2] = { 2u, 1u };
        uint64_t nid[3] = { 10u, 20u, 30u };
        size_t nsy = 0u, nsy1 = 0u;
        srmech_status_t ss, pe, pe1;
        for (uint32_t i = 0; i < ld; i++) { one_p[i] = 1u; }
        snprintf(pdir, sizeof(pdir), "%s_plasmid", temp_dir());
        (void)ensure_dir(pdir);
        /* seed the store with a CHROM cap-only chromosome (0 data turns) so the
         * append hot path (which requires an existing genome) can run. */
        memset(seed, 0, sizeof(seed));
        seed[0] = SRMECH_GENOME_CHROM_CAP_MARKER;
        memcpy(seed + 1, "seed", 4u);
        ss = srmech_genome_save(pdir, seed, sizeof(seed), ld, one_p,
                                sizeof(one_p), g_ws, sizeof(g_ws));
        check_true(ss == SRMECH_OK, "rc278: seed store saved");
        pe = srmech_genome_plasmid_extract(
            3u, ei, ej, ww, NULL, 2u, nid, 3u, NULL, 0u, pdir, "sec0", ld,
            one_p, g_ws, sizeof(g_ws), &nsy);
        check_true(pe == SRMECH_OK && nsy > 0u,
                   "rc278: plasmid_extract appends section 0");
        pe1 = srmech_genome_plasmid_extract(
            3u, ei, ej, ww, NULL, 2u, nid, 3u, NULL, 0u, pdir, "sec1", ld,
            one_p, g_ws, sizeof(g_ws), &nsy1);
        check_true(pe1 == SRMECH_OK && nsy1 == nsy,
                   "rc278: plasmid_extract appends section 1 (streaming, same D)");
        {
            /* both appended sections are present + cap-verified (append-only
             * accumulation). window returns the RAW §55/v3 region (cap +
             * bit-packed turns); the FULL graph round-trip (kernel_unpack ->
             * graph_kernel_decode) + the C<->Python byte-parity are proven in the
             * Python rc278 test where kernel_unpack lives. Here: the section reads
             * back with its cap intact + is longer than the lone telomere. */
            unsigned char wbuf[8192];
            size_t wlen0 = 0u, wlen1 = 0u;
            srmech_status_t ws0 = srmech_genome_window(
                pdir, "sec0", wbuf, sizeof(wbuf), &wlen0, one_p, sizeof(one_p),
                g_ws, sizeof(g_ws));
            check_true(ws0 == SRMECH_OK && wlen0 > (size_t)ld,
                       "rc278: section 0 pages back (cap-verified, > 1 block)");
            srmech_status_t ws1 = srmech_genome_window(
                pdir, "sec1", wbuf, sizeof(wbuf), &wlen1, one_p, sizeof(one_p),
                g_ws, sizeof(g_ws));
            check_true(ws1 == SRMECH_OK && wlen1 == wlen0,
                       "rc278: section 1 pages back, same region length");
        }
        {
            size_t ne = 0u;
            srmech_status_t en = srmech_genome_plasmid_extract(
                3u, ei, ej, ww, NULL, 2u, nid, 3u, NULL, 0u, pdir, "e", ld,
                one_p, g_ws, sizeof(g_ws), NULL);
            srmech_status_t eb = srmech_genome_plasmid_extract(
                3u, ei, ej, ww, NULL, 2u, nid, 3u, NULL, 0u, pdir, "e", 4u,
                one_p, g_ws, sizeof(g_ws), &ne);
            check_true(en == SRMECH_ERR_NULL_ARG,
                       "rc278: NULL out_n_syms -> NULL_ARG");
            check_true(eb == SRMECH_ERR_BAD_INPUT,
                       "rc278: leaf_dim < 52 -> BAD_INPUT");
        }
    }

    /* §102 / rc280 (F1253) — srmech_genome_section_counts: scan a PLASMID section
     * store and derive {global_id -> n_sections}. Three sections with OVERLAPPING
     * node_ids over a store whose vocab karyotype chromosome must be EXCLUDED; each
     * section carries EDGES after its node_ids table (the bytes the targeted prefix
     * read must never touch). Covers the exact counts, the within-section dedupe,
     * the SRMECH_ERR_OVERFLOW capacity-retry contract, and the §101 cancel. */
    {
        const uint32_t ld = 64u;
        unsigned char one_p[64];
        unsigned char seed[64];
        char scdir[1100];
        /* edges sit AFTER node_ids in the §89 stream — deliberately present. */
        uint64_t ei[3] = { 0u, 1u, 2u }, ej[3] = { 1u, 2u, 0u };
        uint64_t ww[3] = { 5u, 4u, 3u };
        uint64_t nidA[3] = { 10u, 20u, 30u };
        uint64_t nidB[3] = { 20u, 30u, 40u };
        uint64_t nidC[3] = { 30u, 50u, 30u };   /* a REPEAT — counts ONCE per section */
        uint64_t ids[16], cnts[16];
        size_t n_out = 0u, n_done = 0u, nsy = 0u;
        srmech_status_t ss, st;
        uint64_t cancel_at;
        for (uint32_t i = 0; i < ld; i++) { one_p[i] = 1u; }
        snprintf(scdir, sizeof(scdir), "%s_sc280", temp_dir());
        (void)ensure_dir(scdir);
        /* Seed with the VOCAB karyotype chromosome — the scan must SKIP it, so the
         * section total is 3, not 4. */
        memset(seed, 0, sizeof(seed));
        seed[0] = SRMECH_GENOME_CHROM_CAP_MARKER;
        memcpy(seed + 1, "__vocab__", 9u);
        ss = srmech_genome_save(scdir, seed, sizeof(seed), ld, one_p,
                                sizeof(one_p), g_ws, sizeof(g_ws));
        check_true(ss == SRMECH_OK, "rc280: section store seeded (vocab chromosome)");
        ss = srmech_genome_plasmid_extract(64u, ei, ej, ww, NULL, 3u, nidA, 3u,
                                           NULL, 0u, scdir, "s0", ld, one_p,
                                           g_ws, sizeof(g_ws), &nsy);
        check_true(ss == SRMECH_OK, "rc280: section s0 extracted {10,20,30}");
        ss = srmech_genome_plasmid_extract(64u, ei, ej, ww, NULL, 3u, nidB, 3u,
                                           NULL, 0u, scdir, "s1", ld, one_p,
                                           g_ws, sizeof(g_ws), &nsy);
        check_true(ss == SRMECH_OK, "rc280: section s1 extracted {20,30,40}");
        ss = srmech_genome_plasmid_extract(64u, ei, ej, ww, NULL, 3u, nidC, 3u,
                                           NULL, 0u, scdir, "s2", ld, one_p,
                                           g_ws, sizeof(g_ws), &nsy);
        check_true(ss == SRMECH_OK, "rc280: section s2 extracted {30,50,30}");
        /* the counts themselves: ASCENDING ids, one count per DISTINCT section. */
        st = srmech_genome_section_counts(scdir, one_p, ld, NULL, NULL,
                                          g_ws, sizeof(g_ws),
                                          ids, cnts, 16u, &n_out, &n_done);
        check_true(st == SRMECH_OK, "rc280: section_counts derives OK");
        check_true(n_out == 5u, "rc280: 5 distinct global ids");
        check_true(n_done == 3u, "rc280: 3 sections scanned (vocab EXCLUDED)");
        check_true(ids[0] == 10u && ids[1] == 20u && ids[2] == 30u &&
                   ids[3] == 40u && ids[4] == 50u,
                   "rc280: ids ASCENDING 10,20,30,40,50");
        check_true(cnts[0] == 1u && cnts[1] == 2u && cnts[2] == 3u &&
                   cnts[3] == 1u && cnts[4] == 1u,
                   "rc280: counts 1,2,3,1,1 (30 in all three; the s2 repeat once)");
        {   /* OVERFLOW reports the TRUE need, and the retry at that size succeeds. */
            uint64_t tid[2], tct[2];
            size_t tn = 0u, td = 0u;
            srmech_status_t so = srmech_genome_section_counts(
                scdir, one_p, ld, NULL, NULL, g_ws, sizeof(g_ws),
                tid, tct, 2u, &tn, &td);
            check_true(so == SRMECH_ERR_OVERFLOW,
                       "rc280: out_cap 2 < 5 -> SRMECH_ERR_OVERFLOW");
            check_true(tn == 5u, "rc280: OVERFLOW reports the TRUE n_out (5)");
            memset(ids, 0, sizeof(ids));
            so = srmech_genome_section_counts(scdir, one_p, ld, NULL, NULL,
                                              g_ws, sizeof(g_ws),
                                              ids, cnts, tn, &n_out, &n_done);
            check_true(so == SRMECH_OK && n_out == 5u && ids[4] == 50u,
                       "rc280: retry at the reported cap succeeds");
        }
        {   /* CANCEL between whole SECTIONS: the partial counts still come back. */
            g_sc_ticks = 0;
            cancel_at = 1u;
            memset(ids, 0, sizeof(ids));
            memset(cnts, 0, sizeof(cnts));
            st = srmech_genome_section_counts(scdir, one_p, ld, sc_cancel_at,
                                              &cancel_at, g_ws, sizeof(g_ws),
                                              ids, cnts, 16u,
                                              &n_out, &n_done);
            check_true(st == SRMECH_CANCELLED, "rc280: tick cancel -> SRMECH_CANCELLED");
            check_true(n_done == 1u, "rc280: cancelled after 1 whole section");
            check_true(g_sc_last_phase == (uint32_t)SRMECH_PHASE_EXTRACTING &&
                       g_sc_last_total == 3u && g_sc_last_done == 1u,
                       "rc280: tick carries EXTRACTING, done=1, total=3");
            check_true(g_sc_ticks == 2, "rc280: ticks fired at done=0 then done=1");
            check_true(n_out == 3u && ids[0] == 10u && ids[1] == 20u &&
                       ids[2] == 30u && cnts[0] == 1u && cnts[1] == 1u &&
                       cnts[2] == 1u,
                       "rc280: the PARTIAL counts (s0 only) are still written");
        }
        {   /* a NULL tick runs exactly as the plain call; bad args are rejected. */
            size_t bn = 0u, bd = 0u;
            srmech_status_t b1 = srmech_genome_section_counts(
                NULL, one_p, ld, NULL, NULL, g_ws, sizeof(g_ws),
                ids, cnts, 16u, &bn, &bd);
            srmech_status_t b2 = srmech_genome_section_counts(
                scdir, one_p, 4u, NULL, NULL, g_ws, sizeof(g_ws),
                ids, cnts, 16u, &bn, &bd);
            srmech_status_t b3 = srmech_genome_section_counts(
                scdir, one_p, ld, NULL, NULL, g_ws, sizeof(g_ws),
                ids, cnts, 16u, NULL, &bd);
            check_true(b1 == SRMECH_ERR_NULL_ARG, "rc280: NULL dir -> NULL_ARG");
            check_true(b2 == SRMECH_ERR_BAD_INPUT, "rc280: leaf_dim < 52 -> BAD_INPUT");
            check_true(b3 == SRMECH_ERR_NULL_ARG, "rc280: NULL n_out -> NULL_ARG");
        }
    }

    /* §135/rc281 (F1251 / G6) — the COPY-NUMBER pair: srmech_genome_amplify (WRITE) +
     * srmech_genome_copy_number (READ). A bare-C host now SETS and GETS the axis, not
     * merely tolerates it. Strand: [CHROM cap "c"][gene "resA"][turn][gene "resB"][turn]. */
    {
        const uint32_t ld = 16u;
        unsigned char strand[5u * 16u];
        unsigned char out[5u * 16u];
        memset(strand, 0, sizeof(strand));
        strand[0] = (unsigned char)SRMECH_GENOME_CHROM_CAP_MARKER;   /* chromosome cap */
        strand[1] = (unsigned char)'c';
        strand[16] = (unsigned char)SRMECH_GENOME_GENE_CAP_MARKER;   /* gene "resA" */
        memcpy(strand + 17, "resA", 4u);
        strand[32] = 2u;                                             /* a Klein-4 turn */
        strand[48] = (unsigned char)SRMECH_GENOME_GENE_CAP_MARKER;   /* gene "resB" */
        memcpy(strand + 49, "resB", 4u);
        strand[64] = 1u;                                             /* a Klein-4 turn */

        /* a never-amplified gene reads 1 (all-NUL padding == stored 0 == present-once) */
        uint64_t got = 0u;
        srmech_status_t r = srmech_genome_copy_number(
            strand, 5u, ld, (const unsigned char *)"resA", 4u, &got);
        check_true(r == SRMECH_OK && got == 1u,
                   "rc281: a plain (never-amplified) gene reads copy-number 1");

        /* WRITE 7 -> the field lands right after the label's NUL, uint64 big-endian */
        srmech_status_t w = srmech_genome_amplify(
            strand, 5u, ld, (const unsigned char *)"resA", 4u, 7u, out, sizeof(out));
        check_true(w == SRMECH_OK, "rc281: amplify returns OK");
        check_true(out[48 + 0] == (unsigned char)SRMECH_GENOME_GENE_CAP_MARKER &&
                   memcmp(out + 49, "resB", 4u) == 0 &&
                   out[32] == 2u && out[64] == 1u && out[0] == strand[0],
                   "rc281: every other block is byte-copied unchanged");
        check_true(out[16] == (unsigned char)SRMECH_GENOME_GENE_CAP_MARKER &&
                   memcmp(out + 17, "resA", 4u) == 0 && out[21] == 0u &&
                   out[22] == 0u && out[23] == 0u && out[24] == 0u && out[25] == 0u &&
                   out[26] == 0u && out[27] == 0u && out[28] == 0u && out[29] == 7u,
                   "rc281: the count is uint64 BE right after the label NUL");

        /* READ it back, and confirm the sibling gene is untouched */
        uint64_t back = 0u, sib = 0u;
        srmech_status_t r2 = srmech_genome_copy_number(
            out, 5u, ld, (const unsigned char *)"resA", 4u, &back);
        srmech_status_t r3 = srmech_genome_copy_number(
            out, 5u, ld, (const unsigned char *)"resB", 4u, &sib);
        check_true(r2 == SRMECH_OK && back == 7u, "rc281: copy_number reads 7 back");
        check_true(r3 == SRMECH_OK && sib == 1u, "rc281: the sibling gene still reads 1");

        /* the amplified cap is STILL an always-expressed plain gene (transparency holds) */
        int expressed = -1;
        uint64_t m = 0xDEADu;
        srmech_status_t e = srmech_genome_gene_express(out + 16, ld, 0u, &expressed, &m);
        check_true(e == SRMECH_OK && expressed == 1 && m == 0u,
                   "rc281: an amplified cap still reads always-express");

        /* a large count round-trips exactly (no float, no truncation) */
        unsigned char big[5u * 16u];
        uint64_t bigv = 0u;
        srmech_status_t wb = srmech_genome_amplify(
            strand, 5u, ld, (const unsigned char *)"resB", 4u,
            (uint64_t)1u << 40, big, sizeof(big));
        srmech_status_t rb = srmech_genome_copy_number(
            big, 5u, ld, (const unsigned char *)"resB", 4u, &bigv);
        check_true(wb == SRMECH_OK && rb == SRMECH_OK && bigv == ((uint64_t)1u << 40),
                   "rc281: a 2^40 count round-trips exactly");

        /* n == 1 is the DEFAULT: byte-identical to the plain strand, no field spent */
        unsigned char one_out[5u * 16u];
        srmech_status_t w1 = srmech_genome_amplify(
            strand, 5u, ld, (const unsigned char *)"resA", 4u, 1u,
            one_out, sizeof(one_out));
        check_true(w1 == SRMECH_OK && memcmp(one_out, strand, sizeof(strand)) == 0,
                   "rc281: amplify to 1 is byte-identical to the plain strand");

        /* error contract: n == 0, an absent gene, NULL args, a short out buffer */
        srmech_status_t b1 = srmech_genome_amplify(
            strand, 5u, ld, (const unsigned char *)"resA", 4u, 0u, out, sizeof(out));
        srmech_status_t b2 = srmech_genome_amplify(
            strand, 5u, ld, (const unsigned char *)"nope", 4u, 3u, out, sizeof(out));
        srmech_status_t b3 = srmech_genome_amplify(
            NULL, 5u, ld, (const unsigned char *)"resA", 4u, 3u, out, sizeof(out));
        srmech_status_t b4 = srmech_genome_amplify(
            strand, 5u, ld, (const unsigned char *)"resA", 4u, 3u, out, 8u);
        srmech_status_t b5 = srmech_genome_copy_number(
            strand, 5u, ld, (const unsigned char *)"nope", 4u, &got);
        check_true(b1 == SRMECH_ERR_BAD_INPUT, "rc281: n == 0 -> BAD_INPUT");
        check_true(b2 == SRMECH_ERR_BAD_INPUT, "rc281: absent gene -> BAD_INPUT");
        check_true(b3 == SRMECH_ERR_NULL_ARG, "rc281: NULL strand -> NULL_ARG");
        check_true(b4 == SRMECH_ERR_OVERFLOW, "rc281: short out buffer -> OVERFLOW");
        check_true(b5 == SRMECH_ERR_BAD_INPUT,
                   "rc281: copy_number of an absent gene -> BAD_INPUT");

        /* a leaf too narrow for label + field is refused, not silently truncated */
        unsigned char tiny[2u * 8u];
        unsigned char tiny_out[2u * 8u];
        memset(tiny, 0, sizeof(tiny));
        tiny[0] = (unsigned char)SRMECH_GENOME_GENE_CAP_MARKER;
        memcpy(tiny + 1, "resA", 4u);
        srmech_status_t nt = srmech_genome_amplify(
            tiny, 2u, 8u, (const unsigned char *)"resA", 4u, 5u,
            tiny_out, sizeof(tiny_out));
        check_true(nt == SRMECH_ERR_BAD_INPUT,
                   "rc281: label + field wider than leaf_dim -> BAD_INPUT");
        /* ...and READING such a leaf falls back to the present-once default, not a crash */
        uint64_t tv = 0u;
        srmech_status_t tr = srmech_genome_copy_number(
            tiny, 2u, 8u, (const unsigned char *)"resA", 4u, &tv);
        check_true(tr == SRMECH_OK && tv == 1u,
                   "rc281: a leaf too narrow for the field reads 1 (absent == default)");
    }

    /* rc337 (#952): srmech_genome_catalog BINDS the re-derived region chain against
     * the manifest head's COMMITTED body_sha256.
     *
     * Every corruption test ABOVE flips byte 0 — the CHROM cap's KIND byte — which
     * the structural walk rejects on its own (genome_block_len: unrecognised kind).
     * So the C host had never exercised a body that walks PERFECTLY but carries a
     * changed PAYLOAD. Here byte 2 is inside chromosome A's label field: the walk
     * still sees a valid CC cap and 6 well-formed blocks, only the label (and hence
     * the region digest) changed. Pre-rc337 that was accepted silently and the
     * catalog reported the MANGLED label; now the chain mismatch is BAD_INPUT.
     *
     * SCOPE: the CATALOG READ only. srmech_genome_census / _registry run a second,
     * parallel derive that rc337 does not reach, and srmech_genome_load's own
     * genome_verify_body is a tautology on a v12 head-only store (the tree it
     * compares against was derived from the body being verified). Both are asserted
     * BELOW as still-permissive, so the #955 follow-up has a from-C baseline and so
     * this block cannot be read as claiming more than it does. Binding them means
     * reaching genome_obtain_manifest, whose fifteen callers include every mutation
     * — that is what turned windows-latest red with 22 mutation-path failures. */
    {
        st = srmech_genome_save(dir, body, sizeof(body), leaf_dim,
                                coupling, sizeof(coupling), g_ws, sizeof(g_ws));
        check_true(st == SRMECH_OK, "rc337: re-save a clean genome for the bound test");

        /* CONTROL FIRST — the clean store still reads on every surface, so the
         * assertions below cannot pass by having degenerated into reject-everything. */
        srmech_json_value_t *cman = NULL;
        srmech_json_value_t *ccen = NULL;
        unsigned char cout[64];
        size_t colen = 0u;
        srmech_status_t c1 = srmech_genome_catalog(dir, NULL, 0u, g_ws,
                                                   sizeof(g_ws), &cman);
        srmech_status_t c2 = srmech_genome_census(dir, NULL, 0u, g_ws,
                                                  sizeof(g_ws), &ccen);
        srmech_status_t c3 = srmech_genome_load(dir, cout, sizeof(cout), &colen,
                                                NULL, 0u, g_ws, sizeof(g_ws));
        check_true(c1 == SRMECH_OK && cman != NULL, "rc337: clean store -> catalog OK");
        check_true(c2 == SRMECH_OK && ccen != NULL, "rc337: clean store -> census OK");
        check_true(c3 == SRMECH_OK && colen == sizeof(body),
                   "rc337: clean store -> load OK");

        char bpath[1200];
        snprintf(bpath, sizeof(bpath), "%s/turns.bin", dir);
        FILE *bf = fopen(bpath, "r+b");
        check_true(bf != NULL, "rc337: reopen turns.bin to perturb a PAYLOAD byte");
        if (bf != NULL) {
            /* chromosome A is at byte_offset 0; +2 lands in its label field. */
            if (fseek(bf, 2L, SEEK_SET) == 0) {
                int c = fgetc(bf);
                if (fseek(bf, 2L, SEEK_SET) == 0) {
                    fputc((c + 1) % 4, bf);        /* still a legal Klein-4 symbol */
                }
            }
            fclose(bf);
        }

        srmech_json_value_t *man2 = NULL;
        srmech_json_value_t *cen2 = NULL;
        unsigned char out2[64];
        size_t olen2 = 0u;
        srmech_status_t k1 = srmech_genome_catalog(dir, NULL, 0u, g_ws,
                                                   sizeof(g_ws), &man2);
        srmech_status_t k2 = srmech_genome_census(dir, NULL, 0u, g_ws,
                                                  sizeof(g_ws), &cen2);
        srmech_status_t k3 = srmech_genome_load(dir, out2, sizeof(out2), &olen2,
                                                NULL, 0u, g_ws, sizeof(g_ws));
        check_true(k1 == SRMECH_ERR_BAD_INPUT,
                   "rc337: well-formed body + corrupt payload -> catalog BAD_INPUT");
        check_true(k2 == SRMECH_OK,
                   "rc337 scope: census is NOT bound (its own derive) — #955");
        check_true(k3 == SRMECH_OK,
                   "rc337 scope: load is NOT bound (verify_body tautology) — #955");

        /* And the store is UNDAMAGED by the rejection: repair the payload byte and
         * the same catalog read succeeds again. A bound that left the genome
         * permanently unreadable would satisfy every assertion above. */
        bf = fopen(bpath, "r+b");
        check_true(bf != NULL, "rc337: reopen turns.bin to REPAIR the payload byte");
        if (bf != NULL) {
            if (fseek(bf, 2L, SEEK_SET) == 0) { fputc((int)body[2], bf); }
            fclose(bf);
        }
        srmech_json_value_t *man3 = NULL;
        srmech_status_t k5 = srmech_genome_catalog(dir, NULL, 0u, g_ws,
                                                   sizeof(g_ws), &man3);
        check_true(k5 == SRMECH_OK && man3 != NULL,
                   "rc337: repairing the payload byte makes the catalog read again");
    }

    /* rc338 (#956) LIFETIME — a derived manifest tree must not point into the
     * dead frame of the function that built it.
     *
     * `genome_obtain_manifest` used to scan into a STACK-local genome_strings_t
     * and hand back a tree whose body_sha256 / coupling.* / attestation.* string
     * nodes pointed at it (srmech_json_new_string does not copy). The bytes were
     * usually still lying undisturbed in the abandoned frame, so it shipped.
     *
     * Make the reuse deterministic with the most faithful scribbler there is: a
     * SECOND catalog call. It re-enters genome_obtain_manifest at the identical
     * stack depth, so its strings block lands on exactly the bytes the first
     * call's did — and fills them with the SECOND genome's digests. The two
     * calls use disjoint arenas, so the stack is all they share.
     *
     * This is the bare-C-HOST projection of
     * python/tests/test_genome_manifest_tree_lifetime_rc338.py: a C-only host
     * with no Python reaches the identical defect through the identical symbol,
     * which is exactly what ADR-0009 means by co-equal projections. */
    {
        const char *dir2 = temp_dir2();
        ensure_dir(dir2);
        /* A distinguishable second genome: a different coupling (so coupling.hex
         * and coupling.sha256 differ) over different content (so body_sha256
         * differs) — three chromosomes rather than two. */
        unsigned char coupling2[4] = { 3u, 1u, 0u, 2u };
        unsigned char body2[24] = {
            /* C CHROM cap */ CC, (unsigned char)'C', 0u, 0u,
            /* C turn0     */ 1u, 1u, 3u, 2u,
            /* D CHROM cap */ CC, (unsigned char)'D', 0u, 0u,
            /* D turn0     */ 2u, 3u, 0u, 1u,
            /* E CHROM cap */ CC, (unsigned char)'E', 0u, 0u,
            /* E turn0     */ 0u, 3u, 3u, 2u,
        };
        srmech_status_t s2 = srmech_genome_save(
            dir2, body2, sizeof(body2), leaf_dim, coupling2, sizeof(coupling2),
            g_ws2, sizeof(g_ws2));
        check_true(s2 == SRMECH_OK, "rc338: second store saves");

        srmech_json_value_t *ta = NULL;
        srmech_status_t la = srmech_genome_catalog(dir, NULL, 0u, g_ws,
                                                   sizeof(g_ws), &ta);
        check_true(la == SRMECH_OK && ta != NULL, "rc338: catalog A (arena 1)");

        /* Snapshot A's answers BEFORE anything else runs on that stack region. */
        char ref_body[65] = { 0 };
        char ref_hex[65] = { 0 };
        const srmech_json_value_t *da = (ta != NULL)
            ? srmech_json_object_get(ta, "data") : NULL;
        const srmech_json_value_t *ba = (da != NULL)
            ? srmech_json_object_get(da, "body_sha256") : NULL;
        const srmech_json_value_t *ca = (da != NULL)
            ? srmech_json_object_get(da, "coupling") : NULL;
        const srmech_json_value_t *ha = (ca != NULL)
            ? srmech_json_object_get(ca, "hex") : NULL;
        check_true(ba != NULL && ba->type == SRMECH_JSON_STRING &&
                   ba->u.str.len == 64u, "rc338: tree A has a 64-hex body_sha256");
        check_true(ha != NULL && ha->type == SRMECH_JSON_STRING &&
                   ha->u.str.len == 2u * leaf_dim, "rc338: tree A has coupling.hex");
        if (ba != NULL && ba->u.str.len == 64u) { memcpy(ref_body, ba->u.str.ptr, 64u); }
        if (ha != NULL && ha->u.str.len <= 64u) {
            memcpy(ref_hex, ha->u.str.ptr, ha->u.str.len);
        }

        /* THE SCRIBBLER — same symbol, same depth, disjoint arena. */
        srmech_json_value_t *tb = NULL;
        srmech_status_t lb = srmech_genome_catalog(dir2, NULL, 0u, g_ws2,
                                                   sizeof(g_ws2), &tb);
        check_true(lb == SRMECH_OK && tb != NULL, "rc338: catalog B (arena 2)");

        const srmech_json_value_t *db = (tb != NULL)
            ? srmech_json_object_get(tb, "data") : NULL;
        const srmech_json_value_t *bb = (db != NULL)
            ? srmech_json_object_get(db, "body_sha256") : NULL;
        check_true(bb != NULL && bb->type == SRMECH_JSON_STRING &&
                   bb->u.str.len == 64u && memcmp(bb->u.str.ptr, ref_body, 64u) != 0,
                   "rc338: the two genomes ARE distinguishable (fixture)");

        /* Pre-fix these two read back as genome B's digest and coupling: a
         * well-formed manifest, a success status, and the WRONG genome. */
        check_true(ba != NULL && memcmp(ba->u.str.ptr, ref_body, 64u) == 0,
                   "rc338/#956: tree A still reports A's body_sha256 after call B");
        check_true(ha != NULL &&
                   memcmp(ha->u.str.ptr, ref_hex, ha->u.str.len) == 0,
                   "rc338/#956: tree A still reports A's coupling.hex after call B");

        /* And the LAST writer of that frame must be right too — a "fix" that only
         * swapped which of the two trees gets corrupted would pass the above. */
        const srmech_json_value_t *ab = (tb != NULL)
            ? srmech_json_object_get(tb, "attestation") : NULL;
        const srmech_json_value_t *rb = (ab != NULL)
            ? srmech_json_object_get(ab, "response_sha256") : NULL;
        check_true(rb != NULL && rb->type == SRMECH_JSON_STRING &&
                   bb != NULL && rb->u.str.len == 64u &&
                   memcmp(rb->u.str.ptr, bb->u.str.ptr, 64u) == 0,
                   "rc338: tree B's attestation.response_sha256 == its body_sha256");
    }

    printf("== %d passed, %d failed ==\n", g_passed, g_failed);
    return (g_failed == 0) ? 0 : 1;
}
