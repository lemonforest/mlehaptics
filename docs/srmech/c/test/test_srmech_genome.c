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

    /* Body: 2 chromosomes. chrom A = cap + 2 turns (3 blocks); chrom B =
     * cap + 1 turn (2 blocks). 5 blocks * 4 bytes = 20 bytes. */
    unsigned char body[20] = {
        /* A cap   */ 3u, 1u, 0u, 2u,
        /* A turn0 */ 0u, 1u, 2u, 3u,
        /* A turn1 */ 2u, 2u, 1u, 1u,
        /* B cap   */ 1u, 3u, 3u, 0u,
        /* B turn0 */ 3u, 0u, 2u, 1u,
    };
    srmech_genome_chrom_t chroms[2];
    chroms[0].label = "alpha";
    chroms[0].leaf_count = 2u;     /* region = 3 blocks */
    chroms[1].label = "beta";
    chroms[1].leaf_count = 1u;     /* region = 2 blocks */

    const char *dir = temp_dir();
    ensure_dir(dir);

    srmech_status_t st = srmech_genome_save(
        dir, body, sizeof(body), leaf_dim, the_one, sizeof(the_one),
        chroms, 2u, g_ws, sizeof(g_ws));
    check_true(st == SRMECH_OK, "genome_save OK");

    /* CATALOG: manifest parses, data.body_sha256 present. */
    {
        srmech_json_value_t *man = NULL;
        st = srmech_genome_catalog(dir, g_ws, sizeof(g_ws), &man);
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
        check_true(nt != NULL && nt->type == SRMECH_JSON_INT && nt->u.i == 5,
                   "data.n_turns == 5");
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
                                g_ws, sizeof(g_ws));
        check_true(st == SRMECH_OK, "genome_load OK (bounding passes)");
        check_true(olen == sizeof(body) &&
                   memcmp(out, body, sizeof(body)) == 0,
                   "loaded body == saved body");
    }

    /* WINDOW: chromosome 'alpha' region bytes (cap + 2 turns = 12 bytes). */
    {
        unsigned char out[64];
        size_t olen = 0u;
        st = srmech_genome_window(dir, "alpha", out, sizeof(out), &olen,
                                  g_ws, sizeof(g_ws));
        check_true(st == SRMECH_OK, "genome_window('alpha') OK");
        check_true(olen == 12u && memcmp(out, body, 12u) == 0,
                   "window('alpha') == first 12 body bytes");
        /* WINDOW on a missing label is rejected. */
        st = srmech_genome_window(dir, "nope", out, sizeof(out), &olen,
                                  g_ws, sizeof(g_ws));
        check_true(st != SRMECH_OK, "genome_window('nope') rejected");
    }

    /* APPEND: add chromosome 'gamma' (cap + 1 turn). */
    {
        unsigned char region[8] = {
            /* gamma cap   */ 2u, 0u, 3u, 1u,
            /* gamma turn0 */ 1u, 1u, 0u, 3u,
        };
        st = srmech_genome_append(dir, "gamma", region, sizeof(region),
                                  leaf_dim, the_one, sizeof(the_one),
                                  g_ws, sizeof(g_ws));
        check_true(st == SRMECH_OK, "genome_append('gamma') OK");

        srmech_json_value_t *man = NULL;
        st = srmech_genome_catalog(dir, g_ws, sizeof(g_ws), &man);
        const srmech_json_value_t *data =
            srmech_json_object_get(man, "data");
        const srmech_json_value_t *nt =
            srmech_json_object_get(data, "n_turns");
        check_true(nt != NULL && nt->u.i == 7, "n_turns grew 5 -> 7");
        const srmech_json_value_t *chr =
            srmech_json_object_get(data, "chromosomes");
        check_true(chr != NULL && chr->type == SRMECH_JSON_ARRAY &&
                   chr->u.arr.n == 3u, "chromosomes now 3");
        /* Prior entry 'alpha' (index 0) byte_offset/leaf_count unchanged. */
        const srmech_json_value_t *a0 = chr->u.arr.items[0];
        const srmech_json_value_t *a_off =
            srmech_json_object_get(a0, "byte_offset");
        const srmech_json_value_t *a_lc =
            srmech_json_object_get(a0, "leaf_count");
        check_true(a_off != NULL && a_off->u.i == 0 &&
                   a_lc != NULL && a_lc->u.i == 2,
                   "prior 'alpha' entry unchanged (offset 0, leaf_count 2)");
        /* New 'gamma' entry at index 2, offset 20, leaf_count 1. */
        const srmech_json_value_t *g2 = chr->u.arr.items[2];
        const srmech_json_value_t *g_lbl =
            srmech_json_object_get(g2, "label");
        const srmech_json_value_t *g_off =
            srmech_json_object_get(g2, "byte_offset");
        check_true(g_lbl != NULL && g_lbl->u.str.len == 5u &&
                   memcmp(g_lbl->u.str.ptr, "gamma", 5) == 0 &&
                   g_off != NULL && g_off->u.i == 20,
                   "new 'gamma' entry at offset 20");
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
                                g_ws, sizeof(g_ws));
        check_true(st == SRMECH_ERR_BAD_INPUT,
                   "corrupted body -> load bounding error");
    }

    printf("== %d passed, %d failed ==\n", g_passed, g_failed);
    return (g_failed == 0) ? 0 : 1;
}
