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

int main(void)
{
    printf("== srmech_genome smoke tests ==\n");

    const uint32_t leaf_dim = 4u;
    /* the_one: one 4-byte Klein-4 block (values 0..3). */
    unsigned char the_one[4] = { 1u, 2u, 3u, 0u };

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
        dir, body, sizeof(body), leaf_dim, the_one, sizeof(the_one),
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
                                  leaf_dim, the_one, sizeof(the_one),
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
     * reconstruct from turns.bin ALONE (scan), given the_one for the leaf
     * width. So a genome can be shipped as turns.bin only (the §43 goal). */
    {
        /* Re-save a clean genome (the BOUNDING test corrupted turns.bin). */
        st = srmech_genome_save(dir, body, sizeof(body), leaf_dim,
                                the_one, sizeof(the_one), g_ws, sizeof(g_ws));
        check_true(st == SRMECH_OK, "re-save clean genome for the §44 section");
        /* Delete manifest.json — the strand is now the sole source of truth. */
        char man_path[1200];
        snprintf(man_path, sizeof(man_path), "%s/manifest.json", dir);
        check_true(remove(man_path) == 0, "delete manifest.json");

        /* CATALOG rebuilt by scanning turns.bin (needs the_one for the width). */
        srmech_json_value_t *man = NULL;
        st = srmech_genome_catalog(dir, the_one, sizeof(the_one),
                                   g_ws, sizeof(g_ws), &man);
        check_true(st == SRMECH_OK && man != NULL,
                   "catalog rebuilt manifest-less (the_one)");
        const srmech_json_value_t *data = srmech_json_object_get(man, "data");
        const srmech_json_value_t *nt = srmech_json_object_get(data, "n_turns");
        check_true(nt != NULL && nt->u.i == 6,
                   "rebuilt n_turns == 6 (the original 2-chrom body)");

        /* LOAD manifest-less -> body bytes match the saved body. */
        unsigned char out[64];
        size_t olen = 0u;
        st = srmech_genome_load(dir, out, sizeof(out), &olen,
                                the_one, sizeof(the_one), g_ws, sizeof(g_ws));
        check_true(st == SRMECH_OK && olen == sizeof(body) &&
                   memcmp(out, body, sizeof(body)) == 0,
                   "load manifest-less == saved body");

        /* WINDOW manifest-less -> chromosome 'A' region (first 16 bytes). */
        st = srmech_genome_window(dir, "A", out, sizeof(out), &olen,
                                  the_one, sizeof(the_one), g_ws, sizeof(g_ws));
        check_true(st == SRMECH_OK && olen == 16u &&
                   memcmp(out, body, 16u) == 0,
                   "window('A') manifest-less == first 16 bytes");

        /* HELPFUL error: no manifest AND no the_one -> BAD_INPUT (not IO). */
        st = srmech_genome_catalog(dir, NULL, 0u, g_ws, sizeof(g_ws), &man);
        check_true(st == SRMECH_ERR_BAD_INPUT,
                   "no manifest + no the_one -> BAD_INPUT (helpful, not IO)");

        /* APPEND manifest-less -> rebuilds, appends, re-writes the .fai cache. */
        unsigned char region[8] = {
            /* Z CHROM cap */ CC, (unsigned char)'Z', 0u, 0u,
            /* Z turn0     */ 1u, 1u, 0u, 3u,
        };
        st = srmech_genome_append(dir, "Z", region, sizeof(region), leaf_dim,
                                  the_one, sizeof(the_one), g_ws, sizeof(g_ws));
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
                                the_one, sizeof(the_one), g_ws, sizeof(g_ws));
        check_true(st == SRMECH_OK, "re-save clean A+B for the §45 section");

        /* REMOVE the FIRST chromosome 'A' (16 bytes) — B slides to the front. */
        st = srmech_genome_remove(dir, "A", the_one, sizeof(the_one),
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
        st = srmech_genome_remove(dir, "B", the_one, sizeof(the_one),
                                  g_ws, sizeof(g_ws));
        check_true(st == SRMECH_ERR_BAD_INPUT, "remove the only chromosome rejected");
        /* REMOVE a missing label -> BAD_INPUT. */
        st = srmech_genome_remove(dir, "nope", the_one, sizeof(the_one),
                                  g_ws, sizeof(g_ws));
        check_true(st == SRMECH_ERR_BAD_INPUT, "remove('nope') rejected");

        /* REPLACE: re-save A+B, then replace 'B' (8 bytes) with a fresh region
         * (CHROM cap 'B' + 2 turns = 3 blocks = 12 bytes). A stays byte-identical. */
        st = srmech_genome_save(dir, body, sizeof(body), leaf_dim,
                                the_one, sizeof(the_one), g_ws, sizeof(g_ws));
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
                                       leaf_dim, the_one, sizeof(the_one),
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
            st = srmech_genome_remove(dir, "A", the_one, sizeof(the_one),
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
                                the_one, sizeof(the_one), g_ws, sizeof(g_ws));
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

        /* IMPORT APPEND: a dest coupled to the SAME the_one with a different
         * 1-chromosome body -> A is appended byte-for-byte; a dup label fails. */
        ensure_dir(app_dir);
        {
            unsigned char solo[8] = { CC, (unsigned char)'S', 0u, 0u, 3u, 2u, 1u, 0u };
            unsigned char out[64];
            size_t olen = 0u;
            st = srmech_genome_save(app_dir, solo, sizeof(solo), leaf_dim,
                                    the_one, sizeof(the_one), g_ws, sizeof(g_ws));
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

        /* IMPORT into a dest coupled to a DIFFERENT the_one -> BAD_INPUT. */
        ensure_dir(mism_dir);
        {
            unsigned char one_b[4] = { 2u, 1u, 0u, 3u };
            unsigned char solo[8] = { CC, (unsigned char)'S', 0u, 0u, 1u, 0u, 3u, 2u };
            st = srmech_genome_save(mism_dir, solo, sizeof(solo), leaf_dim,
                                    one_b, sizeof(one_b), g_ws, sizeof(g_ws));
            check_true(st == SRMECH_OK, "save the_one-mismatch dest");
            st = srmech_genome_import(chr_path, mism_dir, NULL, 0u, g_ws, sizeof(g_ws));
            check_true(st == SRMECH_ERR_BAD_INPUT, "import the_one-mismatch rejected");
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
                                the_one, sizeof(the_one), g_ws, sizeof(g_ws));
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

    printf("== %d passed, %d failed ==\n", g_passed, g_failed);
    return (g_failed == 0) ? 0 : 1;
}
