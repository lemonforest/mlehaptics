/*
 * srmech_genome.c — §41 genome persistence, the C mirror of
 * srmech.amsc.genome's disk save / load / catalog / append / window.
 *
 * A genome directory holds two files:
 *   <dir>/manifest.json   an MPRRecord (MPR v1) catalogue of the
 *                         chromosome set, built with the srmech_json
 *                         BUILDER + serialised with srmech_json_write so
 *                         it is BYTE-IDENTICAL to the Python genome_save's
 *                         json.dumps(payload, sort_keys=True,
 *                         ensure_ascii=False).
 *   <dir>/turns.bin       the append-only flat body — every strand
 *                         element (a telomere cap or a coupled turn) is a
 *                         FIXED-WIDTH leaf_dim-byte block, verbatim (no
 *                         transformation, no length prefix).
 *
 * Bounding == integrity: every read re-hashes (via srmech_sha256_hex) the
 * bytes it touched and compares the lowercase-hex digest against the
 * manifest's stored hex (whole-body body_sha256, a windowed chromosome's
 * cap_sha256). A mismatch is SRMECH_ERR_BAD_INPUT — the GenomeBoundingError
 * analogue. No abs(), no float, no libm.
 *
 * The strings the manifest builder references (hex digests, the version
 * string, the parser/descriptor hashes, the chromosome labels) are held BY
 * REFERENCE by srmech_json_new_string — so they live in caller-or-this-frame
 * buffers that stay alive until after srmech_json_write. The §41 rendering /
 * attestation constants are copied VERBATIM from srmech/amsc/genome.py
 * (_manifest_record).
 *
 * JPL Power-of-Ten compliance (held to the tests/test_jpl_audit.py ratchet):
 *   - Rule 1 (no goto / recursion) : OK — straight-line; the JSON tree is
 *                                    built/walked by the non-recursive
 *                                    srmech_json builder/writer/parser.
 *   - Rule 2 (bounded loops)       : OK — every loop bounded by n_chroms
 *                                    (<= SRMECH_GENOME_MAX_CHROMS) or a
 *                                    caller size_t.
 *   - Rule 3 (no malloc)           : OK — caller arena for the JSON tree;
 *                                    stdio for files; fixed stack/static
 *                                    buffers for paths + digests.
 *   - Rule 4 (<= 60 lines/fn)      : OK — split along natural seams.
 *   - Rule 5 (>= 2 asserts/fn)     : OK — pointer + bound asserts per fn.
 *   - Rule 8 (no multiline macros) : OK — single-token object-like macros.
 *
 * License: GPL-3.0-or-later.
 */

#include "srmech.h"

#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

/* On-disk filenames (mirror genome.py _MANIFEST_NAME / _BODY_NAME). */
#define SRMECH_GENOME_MANIFEST "manifest.json"
#define SRMECH_GENOME_BODY     "turns.bin"

/* Max bytes for a built directory-path string (dir + '/' + filename). */
#define SRMECH_GENOME_PATH_MAX 4096u

/* The §41 manifest data_schema_id (== GENOME_MANIFEST_SCHEMA_ID). */
#define SRMECH_GENOME_SCHEMA_ID "srmech://schema/genome_manifest/v1"

/* The §41 parser_rule_hash pre-image (== f"genome_persistence/v1"). */
#define SRMECH_GENOME_RULE_PREIMAGE "genome_persistence/v2"

/* ------------------------------------------------------------------ *
 * Path + file helpers (stdio — Rule 3 allows file I/O, bans malloc).
 * ------------------------------------------------------------------ */

/* Build "<dir>/<name>" into `out` (capacity out_cap). Returns SRMECH_OK
 * or SRMECH_ERR_OVERFLOW when the joined path does not fit. */
static srmech_status_t genome_join(const char *dir, const char *name,
                                   char *out, size_t out_cap)
{
    assert(dir != NULL && name != NULL);
    assert(out != NULL && out_cap > 0u);
    size_t dl = strlen(dir);
    size_t nl = strlen(name);
    if (dl + 1u + nl + 1u > out_cap) {
        return SRMECH_ERR_OVERFLOW;
    }
    memcpy(out, dir, dl);
    out[dl] = '/';
    memcpy(out + dl + 1u, name, nl);
    out[dl + 1u + nl] = '\0';
    return SRMECH_OK;
}

/* Write `len` bytes from `data` to file `path` (mode `mode`: "wb" truncate
 * or "ab" append). Returns SRMECH_OK / SRMECH_ERR_IO. */
static srmech_status_t genome_write_file(const char *path, const char *mode,
                                         const unsigned char *data, size_t len)
{
    assert(path != NULL && mode != NULL);
    assert(data != NULL || len == 0u);
    FILE *fp = fopen(path, mode);
    if (fp == NULL) {
        return SRMECH_ERR_IO;
    }
    size_t wrote = (len == 0u) ? 0u : fwrite(data, 1u, len, fp);
    int closed = fclose(fp);
    if (wrote != len || closed != 0) {
        return SRMECH_ERR_IO;
    }
    return SRMECH_OK;
}

/* Read up to `cap` bytes of file `path` into `out`; *out_len gets the byte
 * count. SRMECH_ERR_OVERFLOW if the file is larger than `cap`. */
static srmech_status_t genome_read_file(const char *path, unsigned char *out,
                                        size_t cap, size_t *out_len)
{
    assert(path != NULL && out_len != NULL);
    assert(out != NULL || cap == 0u);
    FILE *fp = fopen(path, "rb");
    if (fp == NULL) {
        return SRMECH_ERR_IO;
    }
    size_t total = 0u;
    int over = 0;
    int done = 0;
    /* Bounded loop (Rule 2): at most cap+1 passes — each non-final pass
     * advances `total` by >= 1, or `got == 0` ends it. */
    for (size_t pass = 0; pass <= cap && !done; pass++) {
        if (total >= cap) {
            unsigned char probe;            /* probe one byte past `cap` */
            if (fread(&probe, 1u, 1u, fp) != 0u) { over = 1; }
            done = 1;
        } else {
            size_t got = fread(out + total, 1u, cap - total, fp);
            if (got == 0u) { done = 1; } else { total += got; }
        }
    }
    int err = ferror(fp);
    fclose(fp);
    if (err) { return SRMECH_ERR_IO; }
    if (over) { return SRMECH_ERR_OVERFLOW; }
    *out_len = total;
    return SRMECH_OK;
}

/* Read a chromosome region: seek to `offset`, read `len` bytes into `out`
 * (capacity `cap`). SRMECH_ERR_OVERFLOW if len > cap; SRMECH_ERR_IO on a
 * short read (a truncated body). */
static srmech_status_t genome_read_region(const char *path, size_t offset,
                                          size_t len, unsigned char *out,
                                          size_t cap)
{
    assert(path != NULL);
    assert(out != NULL || len == 0u);
    if (len > cap) {
        return SRMECH_ERR_OVERFLOW;
    }
    FILE *fp = fopen(path, "rb");
    if (fp == NULL) {
        return SRMECH_ERR_IO;
    }
    if (fseek(fp, (long)offset, SEEK_SET) != 0) {
        fclose(fp);
        return SRMECH_ERR_IO;
    }
    size_t got = (len == 0u) ? 0u : fread(out, 1u, len, fp);
    fclose(fp);
    return (got == len) ? SRMECH_OK : SRMECH_ERR_IO;
}

/* ------------------------------------------------------------------ *
 * Manifest builder — assembles the MPRRecord tree (byte-identical to
 * genome.py _manifest_record after the json writer's key-sort).
 *
 * All per-build mutable strings (hex digests, the version string, the
 * parser/descriptor hashes) live in the caller-supplied buffer block
 * `genome_strings_t`, which stays alive across srmech_json_write.
 * ------------------------------------------------------------------ */

/* Stable string storage for one manifest build (held BY REFERENCE by
 * srmech_json_new_string; must outlive srmech_json_write). */
typedef struct {
    char body_sha[65];                              /* body_sha256 + NUL */
    char one_sha[65];                               /* the_one.sha256    */
    char one_hex[2 * 256 + 1];                      /* the_one.hex (<=512 hex) */
    char rule_hash[65];                             /* parser_rule_hash  */
    char descr_hash[65];                            /* collector_descriptor_hash */
    char parser_version[16 + sizeof(SRMECH_VERSION)]; /* "srmech " + ver */
    char cap_sha[SRMECH_GENOME_MAX_CHROMS][65];     /* per-chromosome cap_sha256 */
    uint32_t byte_offset[SRMECH_GENOME_MAX_CHROMS];
    uint32_t byte_len[SRMECH_GENOME_MAX_CHROMS];
    /* §44: derived by SCANNING the body's inline CHROM caps (the manifest is a
     * derived cache — these fields ARE that derivation). */
    char label[SRMECH_GENOME_MAX_CHROMS][SRMECH_GENOME_MAX_LABEL]; /* inline cap label */
    uint32_t leaf_count[SRMECH_GENOME_MAX_CHROMS];  /* DATA turns (caps excluded) */
    uint32_t n_chroms;                              /* chromosomes found by scan */
} genome_strings_t;

/* Lowercase-hex of leaf_dim bytes into `out` (>= 2*n + 1). No libm. */
static srmech_status_t genome_hex(const unsigned char *data, size_t n,
                                  char *out)
{
    static const char H[17] = "0123456789abcdef";
    assert(data != NULL || n == 0u);
    assert(out != NULL);
    for (size_t i = 0; i < n; i++) {
        out[2u * i] = H[(data[i] >> 4) & 0x0Fu];
        out[2u * i + 1u] = H[data[i] & 0x0Fu];
    }
    out[2u * n] = '\0';
    return SRMECH_OK;
}

/* Build the "the_one" sub-object {"sha256":..,"hex":..} from `s`. */
static srmech_json_value_t *genome_build_the_one(srmech_json_builder_t *b,
                                                 const genome_strings_t *s)
{
    assert(b != NULL && s != NULL);
    assert(s->one_sha[0] != '\0');
    const char *keys[2] = { "sha256", "hex" };
    srmech_json_value_t *vals[2];
    vals[0] = srmech_json_new_string(b, s->one_sha, (uint32_t)strlen(s->one_sha));
    vals[1] = srmech_json_new_string(b, s->one_hex, (uint32_t)strlen(s->one_hex));
    return srmech_json_new_object(b, keys, vals, 2u);
}

/* Build one chromosome entry object (5 keys) from the scanned strings (§44 —
 * label + leaf_count come from the inline-cap body scan, not a caller layout). */
static srmech_json_value_t *genome_build_chrom(srmech_json_builder_t *b,
                                               const genome_strings_t *s,
                                               uint32_t idx)
{
    assert(b != NULL && s != NULL);
    assert(idx < SRMECH_GENOME_MAX_CHROMS);
    const char *keys[5] = { "label", "cap_sha256", "leaf_count",
                            "byte_offset", "byte_len" };
    srmech_json_value_t *vals[5];
    vals[0] = srmech_json_new_string(b, s->label[idx],
                                     (uint32_t)strlen(s->label[idx]));
    vals[1] = srmech_json_new_string(b, s->cap_sha[idx],
                                     (uint32_t)strlen(s->cap_sha[idx]));
    vals[2] = srmech_json_new_int(b, (int64_t)s->leaf_count[idx]);
    vals[3] = srmech_json_new_int(b, (int64_t)s->byte_offset[idx]);
    vals[4] = srmech_json_new_int(b, (int64_t)s->byte_len[idx]);
    return srmech_json_new_object(b, keys, vals, 5u);
}

/* Build the "data" block (format_version / leaf_dim / n_turns / the_one /
 * body_sha256 / chromosomes). */
static srmech_json_value_t *genome_build_data(srmech_json_builder_t *b,
                                              const genome_strings_t *s,
                                              uint32_t leaf_dim,
                                              size_t body_len)
{
    assert(b != NULL && s != NULL);
    assert(leaf_dim > 0u && s->n_chroms <= SRMECH_GENOME_MAX_CHROMS);
    srmech_json_value_t *chrom_items[SRMECH_GENOME_MAX_CHROMS];
    for (uint32_t i = 0; i < s->n_chroms; i++) {
        chrom_items[i] = genome_build_chrom(b, s, i);
    }
    srmech_json_value_t *arr = srmech_json_new_array(b, chrom_items, s->n_chroms);
    int64_t n_turns = (int64_t)(body_len / (size_t)leaf_dim);
    const char *keys[6] = { "format_version", "leaf_dim", "n_turns",
                            "the_one", "body_sha256", "chromosomes" };
    srmech_json_value_t *vals[6];
    vals[0] = srmech_json_new_int(b, (int64_t)SRMECH_GENOME_FORMAT_VERSION);
    vals[1] = srmech_json_new_int(b, (int64_t)leaf_dim);
    vals[2] = srmech_json_new_int(b, n_turns);
    vals[3] = genome_build_the_one(b, s);
    vals[4] = srmech_json_new_string(b, s->body_sha, (uint32_t)strlen(s->body_sha));
    vals[5] = arr;
    return srmech_json_new_object(b, keys, vals, 6u);
}

/* Build the "attestation" block (9 fields; constants VERBATIM from
 * genome.py _manifest_record). response_sha256 IS the body hash. */
static srmech_json_value_t *genome_build_attest(srmech_json_builder_t *b,
                                                const genome_strings_t *s)
{
    assert(b != NULL && s != NULL);
    assert(s->body_sha[0] != '\0');
    const char *keys[9] = {
        "source_doi", "source_url", "license", "retrieved_at",
        "response_sha256", "parser_version", "parser_rule_hash",
        "collector_descriptor_path", "collector_descriptor_hash" };
    srmech_json_value_t *v[9];
    v[0] = srmech_json_new_string(b, "10.0/srmech.genome.persistence", 30u);
    v[1] = srmech_json_new_string(b, "https://srmech.net/genome/persistence", 37u);
    v[2] = srmech_json_new_string(b, "CC0", 3u);
    v[3] = srmech_json_new_string(b, "1970-01-01T00:00:00Z", 20u);
    v[4] = srmech_json_new_string(b, s->body_sha, (uint32_t)strlen(s->body_sha));
    v[5] = srmech_json_new_string(b, s->parser_version,
                                  (uint32_t)strlen(s->parser_version));
    v[6] = srmech_json_new_string(b, s->rule_hash, (uint32_t)strlen(s->rule_hash));
    v[7] = srmech_json_new_string(b, "srmech/amsc/genome.py", 21u);
    v[8] = srmech_json_new_string(b, s->descr_hash, (uint32_t)strlen(s->descr_hash));
    return srmech_json_new_object(b, keys, v, 9u);
}

/* The §41 rendering "purpose" — VERBATIM from genome.py _manifest_record
 * (single-line #define; JPL Rule 8 forbids the backslash line-continuation). */
#define SRMECH_GENOME_PURPOSE "A telomere-partitioned genome persisted as a fixed-width body (turns.bin) + an MPR-attested manifest catalog."

/* The §41 rendering "cite_as" — VERBATIM from genome.py (the U+00A7 § is
 * the 2-byte UTF-8 sequence 0xC2 0xA7, emitted ensure_ascii=False). */
#define SRMECH_GENOME_CITE_AS "srmech genome persistence (UPSTREAM \xc2\xa7""41)"

/* Build the "rendering" block (human_readable_name / cite_as / purpose). */
static srmech_json_value_t *genome_build_render(srmech_json_builder_t *b)
{
    assert(b != NULL);
    assert(b->base != NULL || b->len == 0u);
    const char *name = "srmech genome (on-disk chromosome set)";
    const char *cite = SRMECH_GENOME_CITE_AS;
    const char *purpose = SRMECH_GENOME_PURPOSE;
    const char *keys[3] = { "human_readable_name", "cite_as", "purpose" };
    srmech_json_value_t *v[3];
    v[0] = srmech_json_new_string(b, name, (uint32_t)strlen(name));
    v[1] = srmech_json_new_string(b, cite, (uint32_t)strlen(cite));
    v[2] = srmech_json_new_string(b, purpose, (uint32_t)strlen(purpose));
    return srmech_json_new_object(b, keys, v, 3u);
}

/* Build the whole MPRRecord root (5 keys) and serialise it into `out`
 * (capacity out_cap); *out_len gets the byte count. */
/* Build the manifest MPRRecord TREE in the arena `ws` and return its root in
 * *out — the shared core of SAVE (serialised below) and the §44 manifest-less
 * REBUILD (handed straight to the loaders' accessors, exactly like a parsed
 * tree). The key order matches genome.py _manifest_record. */
static srmech_status_t genome_build_manifest_tree(const genome_strings_t *s,
                                                  uint32_t leaf_dim,
                                                  size_t body_len,
                                                  void *ws, size_t ws_len,
                                                  srmech_json_value_t **out)
{
    assert(s != NULL && out != NULL);
    assert(leaf_dim > 0u && s->n_chroms <= SRMECH_GENOME_MAX_CHROMS);
    srmech_json_builder_t b;
    srmech_status_t st = srmech_json_builder_init(&b, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    const char *keys[5] = { "mpr_version", "data", "data_schema_id",
                            "attestation", "rendering" };
    srmech_json_value_t *v[5];
    v[0] = srmech_json_new_string(&b, "1.0", 3u);
    v[1] = genome_build_data(&b, s, leaf_dim, body_len);
    v[2] = srmech_json_new_string(&b, SRMECH_GENOME_SCHEMA_ID,
                                  (uint32_t)strlen(SRMECH_GENOME_SCHEMA_ID));
    v[3] = genome_build_attest(&b, s);
    v[4] = genome_build_render(&b);
    srmech_json_value_t *root = srmech_json_new_object(&b, keys, v, 5u);
    if (b.failed || root == NULL) { return SRMECH_ERR_OVERFLOW; }
    *out = root;
    return SRMECH_OK;
}

/* Serialise the manifest tree to bytes (SAVE). Byte-identical to genome.py
 * _write_manifest after the json writer's key-sort. */
static srmech_status_t genome_build_manifest(const genome_strings_t *s,
                                             uint32_t leaf_dim, size_t body_len,
                                             void *ws, size_t ws_len,
                                             char *out, size_t out_cap,
                                             size_t *out_len)
{
    assert(s != NULL && out != NULL && out_len != NULL);
    assert(leaf_dim > 0u && s->n_chroms <= SRMECH_GENOME_MAX_CHROMS);
    srmech_json_value_t *root = NULL;
    srmech_status_t st = genome_build_manifest_tree(s, leaf_dim, body_len,
                                                    ws, ws_len, &root);
    if (st != SRMECH_OK) { return st; }
    return srmech_json_write(root, out, out_cap, out_len);
}

/* Decode a §44 cap leaf's INLINE label (bytes [1 .. first NUL]) into `out`
 * (NUL-terminated). The cap is `[marker] + label, NUL-padded to leaf_dim`. */
static srmech_status_t genome_decode_label(const unsigned char *cap,
                                           uint32_t leaf_dim, char *out)
{
    assert(cap != NULL && out != NULL);
    assert(leaf_dim > 0u);
    uint32_t n = 0u;
    while (n + 1u < leaf_dim && cap[1u + n] != 0u) { n++; }   /* up to first NUL */
    if (n + 1u > SRMECH_GENOME_MAX_LABEL) { return SRMECH_ERR_BAD_INPUT; }
    memcpy(out, cap + 1, n);
    out[n] = '\0';
    return SRMECH_OK;
}

/* §44 SCAN: walk the self-describing body block-by-block and derive every
 * chromosome's (label, cap_sha256, leaf_count, byte_offset, byte_len) into the
 * string block — this IS the "manifest is a derived cache" claim in C. A CHROM
 * cap opens a chromosome (label read inline); each non-cap block is a data turn
 * (leaf_count++); GENE caps stay in the region (byte_len) but are not turns. */
static srmech_status_t genome_scan_chroms(genome_strings_t *s,
                                          const unsigned char *body,
                                          size_t body_len, uint32_t leaf_dim)
{
    assert(s != NULL);
    assert(body != NULL || body_len == 0u);
    if (body_len % (size_t)leaf_dim != 0u) { return SRMECH_ERR_BAD_INPUT; }
    s->n_chroms = 0u;
    int32_t cur = -1;
    for (size_t off = 0u; off < body_len; off += leaf_dim) {
        if (body[off] == SRMECH_GENOME_CHROM_CAP_MARKER) {
            if (s->n_chroms >= SRMECH_GENOME_MAX_CHROMS) { return SRMECH_ERR_OVERFLOW; }
            cur = (int32_t)s->n_chroms;
            s->n_chroms++;
            srmech_status_t st = srmech_sha256_hex(body + off, leaf_dim, s->cap_sha[cur]);
            if (st != SRMECH_OK) { return st; }
            st = genome_decode_label(body + off, leaf_dim, s->label[cur]);
            if (st != SRMECH_OK) { return st; }
            s->byte_offset[cur] = (uint32_t)off;
            s->byte_len[cur] = leaf_dim;
            s->leaf_count[cur] = 0u;
        } else {
            if (cur < 0) { return SRMECH_ERR_BAD_INPUT; }   /* turn before 1st cap */
            s->byte_len[cur] += leaf_dim;
            if (body[off] != SRMECH_GENOME_GENE_CAP_MARKER) { s->leaf_count[cur]++; }
        }
    }
    return SRMECH_OK;
}

/* Fill the per-build string block from the body + the_one: the hashes, the
 * version string, and the §44 inline-cap chromosome scan. */
static srmech_status_t genome_fill_strings(genome_strings_t *s,
                                           const unsigned char *body,
                                           size_t body_len, uint32_t leaf_dim,
                                           const unsigned char *the_one)
{
    assert(s != NULL && the_one != NULL);
    assert(leaf_dim > 0u);
    srmech_status_t st = srmech_sha256_hex(body, body_len, s->body_sha);
    if (st != SRMECH_OK) { return st; }
    st = srmech_sha256_hex(the_one, leaf_dim, s->one_sha);
    if (st != SRMECH_OK) { return st; }
    genome_hex(the_one, leaf_dim, s->one_hex);
    st = srmech_sha256_hex((const uint8_t *)SRMECH_GENOME_RULE_PREIMAGE,
                           strlen(SRMECH_GENOME_RULE_PREIMAGE), s->rule_hash);
    if (st != SRMECH_OK) { return st; }
    st = srmech_sha256_hex((const uint8_t *)SRMECH_GENOME_SCHEMA_ID,
                           strlen(SRMECH_GENOME_SCHEMA_ID), s->descr_hash);
    if (st != SRMECH_OK) { return st; }
    memcpy(s->parser_version, "srmech ", 7u);
    memcpy(s->parser_version + 7u, SRMECH_VERSION, sizeof(SRMECH_VERSION));
    return genome_scan_chroms(s, body, body_len, leaf_dim);
}

/* ------------------------------------------------------------------ *
 * Manifest write buffer — the serialised manifest bytes + trailing LF.
 * Static thread-local (Rule-3-clean; per-thread reentrant; 256 KiB is
 * ample for the §41 manifest of a SRMECH_GENOME_MAX_CHROMS genome).
 * ------------------------------------------------------------------ */
#define SRMECH_GENOME_MANIFEST_MAX (256u * 1024u)

/* Validate the SAVE args; returns SRMECH_OK or the matching error. §44: there
 * is no caller chromosome layout — the body self-describes. */
static srmech_status_t genome_save_validate(const char *dir,
                                            const unsigned char *body,
                                            size_t body_len, uint32_t leaf_dim,
                                            const unsigned char *the_one,
                                            size_t the_one_len, const void *ws)
{
    assert(body != NULL || body_len == 0u);
    assert(dir != NULL || ws == NULL);
    if (dir == NULL || the_one == NULL || ws == NULL ||
        (body == NULL && body_len != 0u)) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (leaf_dim == 0u || the_one_len != (size_t)leaf_dim || leaf_dim > 256u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    return SRMECH_OK;
}

srmech_status_t srmech_genome_save(
    const char *dir,
    const unsigned char *body, size_t body_len,
    uint32_t leaf_dim,
    const unsigned char *the_one, size_t the_one_len,
    void *ws, size_t ws_len)
{
    assert(dir != NULL || ws == NULL);
    assert(the_one != NULL || the_one_len == 0u);
    srmech_status_t st = genome_save_validate(dir, body, body_len, leaf_dim,
                                              the_one, the_one_len, ws);
    if (st != SRMECH_OK) { return st; }
    char body_path[SRMECH_GENOME_PATH_MAX];
    char man_path[SRMECH_GENOME_PATH_MAX];
    st = genome_join(dir, SRMECH_GENOME_BODY, body_path, sizeof(body_path));
    if (st != SRMECH_OK) { return st; }
    st = genome_join(dir, SRMECH_GENOME_MANIFEST, man_path, sizeof(man_path));
    if (st != SRMECH_OK) { return st; }
    /* Write turns.bin first (verbatim body), then hash + scan + build manifest. */
    st = genome_write_file(body_path, "wb", body, body_len);
    if (st != SRMECH_OK) { return st; }
    static SRMECH_THREAD_LOCAL genome_strings_t strs;
    st = genome_fill_strings(&strs, body, body_len, leaf_dim, the_one);
    if (st != SRMECH_OK) { return st; }
    static SRMECH_THREAD_LOCAL char manifest[SRMECH_GENOME_MANIFEST_MAX];
    size_t mlen = 0u;
    st = genome_build_manifest(&strs, leaf_dim, body_len,
                               ws, ws_len, manifest, sizeof(manifest) - 1u, &mlen);
    if (st != SRMECH_OK) { return st; }
    manifest[mlen] = '\n';                 /* trailing LF, like _write_manifest */
    return genome_write_file(man_path, "wb",
                             (const unsigned char *)manifest, mlen + 1u);
}

/* ------------------------------------------------------------------ *
 * CATALOG — parse manifest.json into a JSON tree (never opens turns.bin).
 * ------------------------------------------------------------------ */

/* Read manifest.json bytes into `buf` (cap), parse into a JSON tree from
 * the arena `ws`. The manifest bytes buffer must outlive the parse (the
 * tree's decoded strings live in the arena, but the parser reads `buf`). */
static srmech_status_t genome_parse_manifest(const char *dir, char *buf,
                                             size_t buf_cap, size_t *buf_len,
                                             void *ws, size_t ws_len,
                                             srmech_json_value_t **out)
{
    assert(dir != NULL && buf != NULL && buf_len != NULL);
    assert(out != NULL && ws != NULL);
    char man_path[SRMECH_GENOME_PATH_MAX];
    srmech_status_t st = genome_join(dir, SRMECH_GENOME_MANIFEST,
                                     man_path, sizeof(man_path));
    if (st != SRMECH_OK) { return st; }
    st = genome_read_file(man_path, (unsigned char *)buf, buf_cap, buf_len);
    if (st != SRMECH_OK) { return st; }
    size_t n = *buf_len;
    while (n > 0u && (buf[n - 1u] == '\n' || buf[n - 1u] == '\r')) { n--; }
    return srmech_json_parse(buf, n, ws, ws_len, out);
}

/* Static body scratch — the whole body, read for the §44 manifest-less REBUILD
 * scan AND for the APPEND grow (Rule-3-clean thread-local). 16 MiB covers a
 * large genome; SRMECH_ERR_OVERFLOW past it. The two uses are SEQUENTIAL (an
 * append's obtain finishes before its grow), so one shared buffer is safe. */
#define SRMECH_GENOME_BODY_MAX (16u * 1024u * 1024u)
static SRMECH_THREAD_LOCAL unsigned char genome_body_scratch[SRMECH_GENOME_BODY_MAX];

/* §44: obtain the manifest TREE — parse manifest.json if present (cheap; never
 * opens turns.bin), else REBUILD it by scanning the self-describing body (the
 * strand is the SSoT, the manifest an optional .fai cache). The rebuild needs
 * `the_one` (the_one_len IS leaf_dim, the width the body lacks inline); a
 * missing manifest with the_one==NULL returns SRMECH_ERR_BAD_INPUT (the helpful
 * "pass the_one" error, NOT a bare IO miss). On either path the tree lives in
 * `ws`, so the loaders' accessors walk it unchanged. */
static srmech_status_t genome_obtain_manifest(
    const char *dir, const unsigned char *the_one, size_t the_one_len,
    void *ws, size_t ws_len, srmech_json_value_t **out)
{
    assert(dir != NULL && out != NULL && ws != NULL);
    assert(the_one != NULL || the_one_len == 0u);
    char man_path[SRMECH_GENOME_PATH_MAX];
    srmech_status_t st = genome_join(dir, SRMECH_GENOME_MANIFEST,
                                     man_path, sizeof(man_path));
    if (st != SRMECH_OK) { return st; }
    FILE *probe = fopen(man_path, "rb");
    if (probe != NULL) {                              /* fast path: parse it */
        fclose(probe);
        static SRMECH_THREAD_LOCAL char manbuf[SRMECH_GENOME_MANIFEST_MAX];
        size_t mlen = 0u;
        return genome_parse_manifest(dir, manbuf, sizeof(manbuf), &mlen,
                                     ws, ws_len, out);
    }
    if (the_one == NULL || the_one_len == 0u || the_one_len > 256u) {
        return SRMECH_ERR_BAD_INPUT;                  /* cannot scan w/o leaf_dim */
    }
    uint32_t leaf_dim = (uint32_t)the_one_len;
    char body_path[SRMECH_GENOME_PATH_MAX];
    st = genome_join(dir, SRMECH_GENOME_BODY, body_path, sizeof(body_path));
    if (st != SRMECH_OK) { return st; }
    size_t blen = 0u;
    st = genome_read_file(body_path, genome_body_scratch,
                          sizeof(genome_body_scratch), &blen);
    if (st != SRMECH_OK) { return st; }
    static SRMECH_THREAD_LOCAL genome_strings_t rstrs;
    st = genome_fill_strings(&rstrs, genome_body_scratch, blen, leaf_dim, the_one);
    if (st != SRMECH_OK) { return st; }
    return genome_build_manifest_tree(&rstrs, leaf_dim, blen, ws, ws_len, out);
}

srmech_status_t srmech_genome_catalog(const char *dir,
                                      const unsigned char *the_one,
                                      size_t the_one_len,
                                      void *ws, size_t ws_len,
                                      srmech_json_value_t **out_manifest)
{
    assert(out_manifest != NULL);
    assert(dir != NULL || ws == NULL);
    if (dir == NULL || ws == NULL || out_manifest == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    return genome_obtain_manifest(dir, the_one, the_one_len, ws, ws_len,
                                  out_manifest);
}

/* ------------------------------------------------------------------ *
 * Manifest accessors — pull a string / int out of the parsed data block.
 * ------------------------------------------------------------------ */

/* Get manifest.data.<key> as a string value (NULL on absence / type). */
static const srmech_json_value_t *genome_data_get(
    const srmech_json_value_t *manifest, const char *key)
{
    assert(manifest != NULL && key != NULL);
    assert(key[0] != '\0');
    const srmech_json_value_t *data = srmech_json_object_get(manifest, "data");
    if (data == NULL) { return NULL; }
    return srmech_json_object_get(data, key);
}

/* Compare a parsed JSON string value against a NUL-terminated digest. */
static int genome_str_eq(const srmech_json_value_t *v, const char *hex)
{
    assert(hex != NULL);
    assert(hex[0] != '\0');
    if (v == NULL || v->type != SRMECH_JSON_STRING) { return 0; }
    size_t hl = strlen(hex);
    return (v->u.str.len == (uint32_t)hl &&
            memcmp(v->u.str.ptr, hex, hl) == 0) ? 1 : 0;
}

/* ------------------------------------------------------------------ *
 * LOAD — read turns.bin, re-hash whole body vs manifest body_sha256.
 * ------------------------------------------------------------------ */
srmech_status_t srmech_genome_load(const char *dir, unsigned char *out,
                                   size_t out_cap, size_t *out_len,
                                   const unsigned char *the_one,
                                   size_t the_one_len,
                                   void *ws, size_t ws_len)
{
    assert(out_len != NULL);
    assert(dir != NULL || out == NULL);
    if (dir == NULL || out == NULL || out_len == NULL || ws == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    srmech_json_value_t *manifest = NULL;
    srmech_status_t st = genome_obtain_manifest(dir, the_one, the_one_len,
                                                ws, ws_len, &manifest);
    if (st != SRMECH_OK) { return st; }
    const srmech_json_value_t *bsha = genome_data_get(manifest, "body_sha256");
    if (bsha == NULL || bsha->type != SRMECH_JSON_STRING) {
        return SRMECH_ERR_BAD_INPUT;
    }
    char body_path[SRMECH_GENOME_PATH_MAX];
    st = genome_join(dir, SRMECH_GENOME_BODY, body_path, sizeof(body_path));
    if (st != SRMECH_OK) { return st; }
    st = genome_read_file(body_path, out, out_cap, out_len);
    if (st != SRMECH_OK) { return st; }
    char got[65];
    st = srmech_sha256_hex(out, *out_len, got);
    if (st != SRMECH_OK) { return st; }
    return genome_str_eq(bsha, got) ? SRMECH_OK : SRMECH_ERR_BAD_INPUT;
}

/* ------------------------------------------------------------------ *
 * WINDOW — page one chromosome's region, re-hash its cap vs cap_sha256.
 * ------------------------------------------------------------------ */

/* Find the chromosome entry with `label`; on success copies its
 * byte_offset / byte_len and a pointer to its cap_sha256 value. */
static const srmech_json_value_t *genome_find_chrom(
    const srmech_json_value_t *manifest, const char *label,
    size_t *offset, size_t *len)
{
    assert(manifest != NULL && label != NULL);
    assert(offset != NULL && len != NULL);
    const srmech_json_value_t *arr = genome_data_get(manifest, "chromosomes");
    if (arr == NULL || arr->type != SRMECH_JSON_ARRAY) { return NULL; }
    size_t ll = strlen(label);
    for (uint32_t i = 0; i < arr->u.arr.n; i++) {
        const srmech_json_value_t *c = arr->u.arr.items[i];
        const srmech_json_value_t *lv = srmech_json_object_get(c, "label");
        if (lv == NULL || lv->type != SRMECH_JSON_STRING ||
            lv->u.str.len != (uint32_t)ll ||
            memcmp(lv->u.str.ptr, label, ll) != 0) { continue; }
        const srmech_json_value_t *bo = srmech_json_object_get(c, "byte_offset");
        const srmech_json_value_t *bl = srmech_json_object_get(c, "byte_len");
        if (bo == NULL || bl == NULL) { return NULL; }
        *offset = (size_t)bo->u.i;
        *len = (size_t)bl->u.i;
        return srmech_json_object_get(c, "cap_sha256");
    }
    return NULL;
}

srmech_status_t srmech_genome_window(const char *dir, const char *label,
                                     unsigned char *out, size_t out_cap,
                                     size_t *out_len,
                                     const unsigned char *the_one,
                                     size_t the_one_len,
                                     void *ws, size_t ws_len)
{
    assert(out_len != NULL);
    assert(dir != NULL || out == NULL);
    if (dir == NULL || label == NULL || out == NULL ||
        out_len == NULL || ws == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    srmech_json_value_t *manifest = NULL;
    srmech_status_t st = genome_obtain_manifest(dir, the_one, the_one_len,
                                                ws, ws_len, &manifest);
    if (st != SRMECH_OK) { return st; }
    size_t off = 0u, len = 0u;
    const srmech_json_value_t *csha =
        genome_find_chrom(manifest, label, &off, &len);
    if (csha == NULL || csha->type != SRMECH_JSON_STRING) {
        return SRMECH_ERR_BAD_INPUT;
    }
    const srmech_json_value_t *ld = genome_data_get(manifest, "leaf_dim");
    if (ld == NULL || ld->type != SRMECH_JSON_INT) { return SRMECH_ERR_BAD_INPUT; }
    char body_path[SRMECH_GENOME_PATH_MAX];
    st = genome_join(dir, SRMECH_GENOME_BODY, body_path, sizeof(body_path));
    if (st != SRMECH_OK) { return st; }
    st = genome_read_region(body_path, off, len, out, out_cap);
    if (st != SRMECH_OK) { return st; }
    *out_len = len;
    char got[65];
    st = srmech_sha256_hex(out, (size_t)ld->u.i, got);
    if (st != SRMECH_OK) { return st; }
    return genome_str_eq(csha, got) ? SRMECH_OK : SRMECH_ERR_BAD_INPUT;
}

/* ------------------------------------------------------------------ *
 * APPEND — append one chromosome region to turns.bin, rewrite manifest.
 *
 * The manifest is rebuilt from the WHOLE new body the same way SAVE
 * builds it — re-deriving every chromosome's cap_sha256 / byte_offset /
 * byte_len + the new body_sha256 / n_turns — but the existing chromosome
 * entries come out byte-identical because the body bytes they hash are
 * untouched (append-only) and the layout walk is order-stable.
 * ------------------------------------------------------------------ */

/* §44: guard against appending a chromosome whose label already exists (the
 * Python genome_append's `if label in existing_labels: raise`). Returns
 * SRMECH_ERR_BAD_INPUT if `new_label` is already a chromosome of the manifest;
 * SRMECH_OK otherwise. (The rebuilt manifest is DERIVED from the grown body by
 * srmech_genome_save's scan, so no layout list is collected here.) */
static srmech_status_t genome_check_new_label(
    const srmech_json_value_t *manifest, const char *new_label)
{
    assert(manifest != NULL);
    assert(new_label != NULL);
    const srmech_json_value_t *arr = genome_data_get(manifest, "chromosomes");
    if (arr == NULL || arr->type != SRMECH_JSON_ARRAY) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if ((size_t)arr->u.arr.n + 1u > SRMECH_GENOME_MAX_CHROMS) {
        return SRMECH_ERR_OVERFLOW;
    }
    size_t nl = strlen(new_label);
    for (uint32_t i = 0; i < arr->u.arr.n; i++) {
        const srmech_json_value_t *lv =
            srmech_json_object_get(arr->u.arr.items[i], "label");
        if (lv == NULL || lv->type != SRMECH_JSON_STRING) {
            return SRMECH_ERR_BAD_INPUT;
        }
        if (lv->u.str.len == (uint32_t)nl &&
            memcmp(lv->u.str.ptr, new_label, nl) == 0) {
            return SRMECH_ERR_BAD_INPUT;          /* label already present */
        }
    }
    return SRMECH_OK;
}

/* Read the existing body, bound-check it against the manifest body_sha256,
 * then append `region` into `out`; *new_len gets the grown length. */
static srmech_status_t genome_grow_body(const char *dir,
                                        const srmech_json_value_t *manifest,
                                        const unsigned char *region,
                                        size_t region_len, unsigned char *out,
                                        size_t out_cap, size_t *new_len)
{
    assert(dir != NULL && manifest != NULL && out != NULL && new_len != NULL);
    assert(region != NULL || region_len == 0u);
    char body_path[SRMECH_GENOME_PATH_MAX];
    srmech_status_t st = genome_join(dir, SRMECH_GENOME_BODY,
                                     body_path, sizeof(body_path));
    if (st != SRMECH_OK) { return st; }
    size_t old_len = 0u;
    st = genome_read_file(body_path, out, out_cap, &old_len);
    if (st != SRMECH_OK) { return st; }
    const srmech_json_value_t *bsha = genome_data_get(manifest, "body_sha256");
    char got[65];
    st = srmech_sha256_hex(out, old_len, got);
    if (st != SRMECH_OK) { return st; }
    if (!genome_str_eq(bsha, got)) { return SRMECH_ERR_BAD_INPUT; }
    if (old_len + region_len > out_cap) { return SRMECH_ERR_OVERFLOW; }
    if (region_len != 0u) { memcpy(out + old_len, region, region_len); }
    *new_len = old_len + region_len;
    return SRMECH_OK;
}

srmech_status_t srmech_genome_append(const char *dir, const char *label,
                                     const unsigned char *region,
                                     size_t region_len, uint32_t leaf_dim,
                                     const unsigned char *the_one,
                                     size_t the_one_len, void *ws, size_t ws_len)
{
    assert(the_one != NULL || the_one_len == 0u);
    assert(dir != NULL || label == NULL);
    if (dir == NULL || label == NULL || the_one == NULL || ws == NULL ||
        (region == NULL && region_len != 0u)) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (leaf_dim == 0u || the_one_len != (size_t)leaf_dim ||
        region_len == 0u || region_len % (size_t)leaf_dim != 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    /* §44: obtain the manifest — parsed if present, else rebuilt by scanning
     * (the_one carries the leaf width), so an append works manifest-less too. */
    srmech_json_value_t *manifest = NULL;
    srmech_status_t st = genome_obtain_manifest(dir, the_one, the_one_len,
                                                ws, ws_len, &manifest);
    if (st != SRMECH_OK) { return st; }
    const srmech_json_value_t *ld = genome_data_get(manifest, "leaf_dim");
    if (ld == NULL || ld->type != SRMECH_JSON_INT ||
        (uint32_t)ld->u.i != leaf_dim) { return SRMECH_ERR_BAD_INPUT; }
    st = genome_check_new_label(manifest, label);          /* no dup labels */
    if (st != SRMECH_OK) { return st; }
    size_t new_len = 0u;
    /* genome_body_scratch is reused here (obtain's scan has finished). */
    st = genome_grow_body(dir, manifest, region, region_len,
                          genome_body_scratch, sizeof(genome_body_scratch),
                          &new_len);
    if (st != SRMECH_OK) { return st; }
    /* §44: rewrite turns.bin (verbatim grown body) + a manifest DERIVED by
     * scanning the grown body. The grown body is the prior bytes UNCHANGED +
     * the appended region, so turns.bin is byte-identical to a true append and
     * every prior chromosome entry re-derives byte-identically (same body
     * bytes, order-stable inline-cap scan). */
    return srmech_genome_save(dir, genome_body_scratch, new_len, leaf_dim,
                              the_one, the_one_len, ws, ws_len);
}
