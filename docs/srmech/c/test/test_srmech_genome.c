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

    printf("== %d passed, %d failed ==\n", g_passed, g_failed);
    return (g_failed == 0) ? 0 : 1;
}
