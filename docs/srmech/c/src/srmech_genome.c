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
 *                         element (a telomere cap or a coupled turn) is
 *                         one SELF-DESCRIBING block whose FIRST byte keys
 *                         its kind + width: a leaf_dim-byte cap, a §55/v3
 *                         BIT-PACKED data turn (1 + ceil(leaf_dim/4)
 *                         bytes, 4 Klein-4 symbols per byte), or a legacy
 *                         v2 leaf_dim-byte byte-per-symbol turn — verbatim
 *                         (no transformation, no length prefix).
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
 *                                    (a caller-arena count) or a caller
 *                                    size_t.
 *   - Rule 3 (no malloc)           : OK — ALL scratch (body / manifest / the
 *                                    chromosome arrays / the .chr buffers) is
 *                                    carved from the caller arena (a bump
 *                                    pointer, not malloc); stdio for files;
 *                                    fixed stack buffers for paths + digests.
 *   - Rule 4 (<= 60 lines/fn)      : OK — split along natural seams.
 *   - Rule 5 (>= 2 asserts/fn)     : OK — pointer + bound asserts per fn.
 *   - Rule 8 (no multiline macros) : OK — single-token object-like macros.
 *
 * License: MIT.
 */

#include "srmech.h"
#include "srmech_platform.h"   /* PAL FILE surface (rc162) — the OS file TU */

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

/* The §41 parser_rule_hash pre-image (== f"genome_persistence/v11" — tracks
 * SRMECH_GENOME_FORMAT_VERSION, mirroring the Python _manifest_record; §132/rc132 v10->v11). */
#define SRMECH_GENOME_RULE_PREIMAGE "genome_persistence/v11"

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
 * or "ab" append). Returns SRMECH_OK / SRMECH_ERR_IO. (rc162: the OS write
 * goes through the PAL — `srmech_plat_file_write` — so no raw stdio lives in
 * the genome; the mode string maps to the PAL's `append` flag.) */
static srmech_status_t genome_write_file(const char *path, const char *mode,
                                         const unsigned char *data, size_t len)
{
    assert(path != NULL && mode != NULL);
    assert(data != NULL || len == 0u);
    return srmech_plat_file_write(path, (mode[0] == 'a') ? 1 : 0, data, len);
}

/* Read up to `cap` bytes of file `path` into `out`; *out_len gets the byte
 * count. SRMECH_ERR_OVERFLOW if the file is larger than `cap`. (rc162: through
 * the PAL `srmech_plat_file_read` — identical whole-file semantics.) */
static srmech_status_t genome_read_file(const char *path, unsigned char *out,
                                        size_t cap, size_t *out_len)
{
    assert(path != NULL && out_len != NULL);
    assert(out != NULL || cap == 0u);
    return srmech_plat_file_read(path, out, cap, out_len);
}

/* Read a chromosome region: seek to `offset`, read `len` bytes into `out`
 * (capacity `cap`). SRMECH_ERR_OVERFLOW if len > cap; SRMECH_ERR_IO on a
 * short read (a truncated body). (rc162: the genome keeps the cap guard, the
 * seek+read goes through the PAL `srmech_plat_file_read_region`.) */
static srmech_status_t genome_read_region(const char *path, size_t offset,
                                          size_t len, unsigned char *out,
                                          size_t cap)
{
    assert(path != NULL);
    assert(out != NULL || len == 0u);
    if (len > cap) {
        return SRMECH_ERR_OVERFLOW;
    }
    return srmech_plat_file_read_region(path, offset, out, len);
}

/* Byte length of file `path` (for arena-sizing a body / manifest read).
 * SRMECH_ERR_IO on a missing / unstattable file; *size gets the length.
 * (rc162: through the PAL `srmech_plat_file_size`.) */
static srmech_status_t genome_file_size(const char *path, size_t *size)
{
    assert(path != NULL);
    assert(size != NULL);
    return srmech_plat_file_size(path, size);
}

/* ------------------------------------------------------------------ *
 * Caller-arena bump allocator — the size-AGNOSTIC scaffolding.
 *
 * ALL genome scratch (the body bytes read off disk, the per-chromosome
 * string arrays, the manifest serialise buffer, the .chr region) is carved
 * from the caller's `ws` arena, so the ONLY bound is the CALLER'S RAM — a
 * host sizes the arena large, a microcontroller small — never a compiled-in
 * cap. The C is therefore standalone-complete: it handles any genome the
 * caller's arena fits, with no assumption that a Python fallback exists.
 * JPL Rule 3 bans malloc, NOT a bump-pointer over a caller buffer (the
 * caller owns the allocation). The srmech_json builder/parser then runs on
 * the arena's untouched TAIL.
 * ------------------------------------------------------------------ */
typedef struct {
    unsigned char *base;   /* caller workspace base        */
    size_t         cap;    /* caller workspace capacity    */
    size_t         off;    /* bump offset                  */
} genome_arena_t;

/* Bind an arena over the caller's [ws, ws + ws_len). */
static void genome_arena_init(genome_arena_t *a, void *ws, size_t ws_len)
{
    assert(a != NULL);
    assert(ws != NULL || ws_len == 0u);
    a->base = (unsigned char *)ws;
    a->cap = ws_len;
    a->off = 0u;
}

/* Carve `n` bytes (16-byte aligned) off the front; NULL on overflow. */
static void *genome_arena_alloc(genome_arena_t *a, size_t n)
{
    assert(a != NULL);
    assert(a->off <= a->cap);
    size_t off = (a->off + 15u) & ~(size_t)15u;        /* align up to 16 */
    if (off > a->cap || n > a->cap - off) { return NULL; }
    void *p = a->base + off;
    a->off = off + n;
    return p;
}

/* The arena's untouched (16-aligned) tail — handed to the srmech_json
 * builder/parser, which manages it independently from here on. */
static void genome_arena_tail(const genome_arena_t *a, void **ws, size_t *ws_len)
{
    assert(a != NULL);
    assert(ws != NULL && ws_len != NULL);
    size_t off = (a->off + 15u) & ~(size_t)15u;
    if (off > a->cap) { off = a->cap; }
    *ws = a->base + off;
    *ws_len = a->cap - off;
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
    /* §44: per-chromosome arrays — derived by SCANNING the body's inline CHROM
     * caps (the manifest is a derived cache; these fields ARE that derivation).
     * Carved from the caller arena, sized to the scanned chromosome count, so a
     * genome may hold ANY number of chromosomes the arena fits (no compiled-in
     * cap). A consumer indexes `s->cap_sha[i]` etc. exactly as before. */
    char (*cap_sha)[65];                            /* [cap_chroms] cap_sha256 */
    uint32_t *byte_offset;                          /* [cap_chroms] */
    uint32_t *byte_len;                             /* [cap_chroms] */
    char (*label)[SRMECH_GENOME_MAX_LABEL];         /* [cap_chroms] inline label */
    uint32_t *leaf_count;                           /* [cap_chroms] DATA turns */
    char (*region_sha)[65];                         /* [cap_chroms] full-region
                                                     * digest (v4 regions[] +
                                                     * the body_sha256 chain) */
    uint32_t cap_chroms;                            /* arena-allocated capacity */
    uint32_t n_chroms;                              /* chromosomes found by scan */
    uint32_t n_blocks;                              /* §55/v3: strand BLOCK count
                                                     * (caps + turns) == n_turns */
} genome_strings_t;

/* §55/v3: byte length of the block starting at body[off], keyed by its FIRST
 * byte — a leaf_dim-byte cap or legacy v2 turn, or a 1 + ceil(leaf_dim/4)-byte
 * bit-packed turn. SRMECH_ERR_BAD_INPUT on an unrecognised kind byte or a block
 * running past body_len (a truncated body). This is THE dual-format walker
 * step (v2 | v3 | mixed bodies read in the same walk — back-compat). */
static srmech_status_t genome_block_len(const unsigned char *body,
                                        size_t body_len, size_t off,
                                        uint32_t leaf_dim, size_t *blen)
{
    assert(body != NULL && blen != NULL);
    assert(off < body_len && leaf_dim > 0u);
    unsigned char kind = body[off];
    size_t n;
    if (kind == SRMECH_GENOME_CHROM_CAP_MARKER ||
        kind == SRMECH_GENOME_GENE_CAP_MARKER ||
        kind == SRMECH_GENOME_REGULATORY_GENE_MARKER ||
        kind == SRMECH_GENOME_BOOLEAN_GENE_MARKER ||
        kind == SRMECH_GENOME_THRESHOLD_GENE_MARKER ||
        kind == SRMECH_GENOME_GRADED_GENE_MARKER ||
        kind == SRMECH_GENOME_KERNEL_HEADER_MARKER ||
        kind == SRMECH_GENOME_KERNEL_TELOMERE_MARKER ||
        kind == SRMECH_GENOME_ACTIVE_TELOMERE_MARKER || kind <= 3u) {
        n = (size_t)leaf_dim;   /* cap / §60 v5 header / §89 kernel telomere /
                                 * §127 active telomere / §128 regulatory gene /
                                 * §130 boolean gene / §131 threshold gene /
                                 * §132 graded gene / v2 turn */
    } else if (kind == SRMECH_GENOME_PACKED_TURN_MARKER) {
        n = 1u + ((size_t)leaf_dim + 3u) / 4u;      /* v3 bit-packed turn */
    } else {
        return SRMECH_ERR_BAD_INPUT;                /* unrecognised kind byte */
    }
    if (n > body_len - off) { return SRMECH_ERR_BAD_INPUT; }   /* truncated */
    *blen = n;
    return SRMECH_OK;
}

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

/* Decode `n` bytes from the 2*n lowercase-hex chars at `hex` into `out`. The v4
 * region-chain reverses genome_hex (the stored region/chain digests are hex; the
 * chain folds the RAW 32-byte values). SRMECH_ERR_BAD_INPUT on a non-hex char.
 * (A fixed-width digest decoder — distinct from the .chr's variable-length,
 * cap-checked genome_unhex.) */
static srmech_status_t genome_hex2bytes(const char *hex, size_t n,
                                        unsigned char *out)
{
    assert(hex != NULL && out != NULL);
    assert(n <= 32u);
    for (size_t i = 0; i < 2u * n; i++) {
        char c = hex[i];
        int nib = (c >= '0' && c <= '9') ? (c - '0')
                : (c >= 'a' && c <= 'f') ? (c - 'a' + 10) : -1;
        if (nib < 0) { return SRMECH_ERR_BAD_INPUT; }
        out[i >> 1] = (unsigned char)((i & 1u) ? (out[i >> 1] | nib)
                                              : (nib << 4));
    }
    return SRMECH_OK;
}

/* One region-chain fold step Hk = sha256(Hk-1 || region_k): `chain_hex` (both in
 * and out, >= 65 bytes) and `region_hex` are 64-char digests; the RAW 32-byte
 * values are concatenated and re-hashed (== genome.py _chain_step). */
static srmech_status_t genome_chain_fold(char *chain_hex, const char *region_hex)
{
    assert(chain_hex != NULL && region_hex != NULL);
    assert(region_hex[0] != '\0');
    unsigned char buf[64];
    srmech_status_t st = genome_hex2bytes(chain_hex, 32u, buf);    /* Hk-1 raw */
    if (st != SRMECH_OK) { return st; }
    st = genome_hex2bytes(region_hex, 32u, buf + 32u);             /* region_k raw */
    if (st != SRMECH_OK) { return st; }
    return srmech_sha256_hex(buf, 64u, chain_hex);                 /* Hk */
}

/* v4 (rc115 #1245(b)): fold `n` per-chromosome region digests (hex, body order)
 * into the whole-body body_sha256 CHAIN, seeded by H0 = sha256("") — O(1)-
 * extendable, re-verifiable, §44-derivable. `chain_hex` (>= 65 bytes) receives
 * the final head. Byte-identical to genome.py _region_chain. */
static srmech_status_t genome_chain_regions(char (*region_sha)[65],
                                            uint32_t n, char *chain_hex)
{
    assert(region_sha != NULL || n == 0u);
    assert(chain_hex != NULL);
    srmech_status_t st = srmech_sha256_hex((const uint8_t *)"", 0u, chain_hex);
    if (st != SRMECH_OK) { return st; }
    for (uint32_t i = 0; i < n; i++) {
        st = genome_chain_fold(chain_hex, region_sha[i]);
        if (st != SRMECH_OK) { return st; }
    }
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
    assert(idx < s->cap_chroms);
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

/* Build one region entry object (3 keys) from the scanned strings — v4
 * (rc115 #1245(b)): {byte_offset, byte_len, sha256} where sha256 is the FULL
 * region digest (the chromosome's .chr / AMSC provenance unit). */
static srmech_json_value_t *genome_build_region(srmech_json_builder_t *b,
                                                const genome_strings_t *s,
                                                uint32_t idx)
{
    assert(b != NULL && s != NULL);
    assert(idx < s->cap_chroms);
    const char *keys[3] = { "byte_offset", "byte_len", "sha256" };
    srmech_json_value_t *vals[3];
    vals[0] = srmech_json_new_int(b, (int64_t)s->byte_offset[idx]);
    vals[1] = srmech_json_new_int(b, (int64_t)s->byte_len[idx]);
    vals[2] = srmech_json_new_string(b, s->region_sha[idx],
                                     (uint32_t)strlen(s->region_sha[idx]));
    return srmech_json_new_object(b, keys, vals, 3u);
}

/* Build the "data" block (format_version / leaf_dim / n_turns / the_one /
 * body_sha256 / regions / chromosomes). v4 (rc115 #1245(b)): body_sha256 is the
 * region CHAIN (s->body_sha, folded in genome_fill_regions_chain) and `regions`
 * is the per-chromosome integrity partition. */
static srmech_json_value_t *genome_build_data(srmech_json_builder_t *b,
                                              const genome_strings_t *s,
                                              srmech_json_value_t **chrom_items,
                                              srmech_json_value_t **region_items,
                                              uint32_t leaf_dim,
                                              size_t body_len)
{
    assert(b != NULL && s != NULL);
    assert(leaf_dim > 0u && s->n_chroms <= s->cap_chroms);
    assert(chrom_items != NULL || s->n_chroms == 0u);
    for (uint32_t i = 0; i < s->n_chroms; i++) {
        chrom_items[i] = genome_build_chrom(b, s, i);
        region_items[i] = genome_build_region(b, s, i);
    }
    srmech_json_value_t *arr = srmech_json_new_array(b, chrom_items, s->n_chroms);
    srmech_json_value_t *rarr = srmech_json_new_array(b, region_items, s->n_chroms);
    (void)body_len;                 /* §55/v3: n_turns is the scanned BLOCK count */
    int64_t n_turns = (int64_t)s->n_blocks;
    const char *keys[7] = { "format_version", "leaf_dim", "n_turns",
                            "the_one", "body_sha256", "regions", "chromosomes" };
    srmech_json_value_t *vals[7];
    vals[0] = srmech_json_new_int(b, (int64_t)SRMECH_GENOME_FORMAT_VERSION);
    vals[1] = srmech_json_new_int(b, (int64_t)leaf_dim);
    vals[2] = srmech_json_new_int(b, n_turns);
    vals[3] = genome_build_the_one(b, s);
    vals[4] = srmech_json_new_string(b, s->body_sha, (uint32_t)strlen(s->body_sha));
    vals[5] = rarr;
    vals[6] = arr;
    return srmech_json_new_object(b, keys, vals, 7u);
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
/* `wtail`/`wtail_len` (both NULL-able) receive the builder's untouched arena
 * tail after the tree is built — the SAVE caller hands it to the json writer
 * as its key-sort scratch (so the writer needs no arena of its own). */
static srmech_status_t genome_build_manifest_tree(const genome_strings_t *s,
                                                  uint32_t leaf_dim,
                                                  size_t body_len,
                                                  void *ws, size_t ws_len,
                                                  srmech_json_value_t **out,
                                                  void **wtail, size_t *wtail_len)
{
    assert(s != NULL && out != NULL);
    assert(leaf_dim > 0u && s->n_chroms <= s->cap_chroms);
    /* Carve the chrom-pointer scratch from the FRONT of the caller arena, then
     * run the json builder on the TAIL (so the scratch stays put across the
     * build). No fixed cap — the bound is the caller's arena. */
    genome_arena_t a;
    genome_arena_init(&a, ws, ws_len);
    srmech_json_value_t **chrom_items = NULL;
    srmech_json_value_t **region_items = NULL;
    if (s->n_chroms > 0u) {
        chrom_items = genome_arena_alloc(&a,
                                         (size_t)s->n_chroms * sizeof(*chrom_items));
        region_items = genome_arena_alloc(&a,
                                          (size_t)s->n_chroms * sizeof(*region_items));
        if (chrom_items == NULL || region_items == NULL) {
            return SRMECH_ERR_OVERFLOW;
        }
    }
    void *jws = NULL;
    size_t jws_len = 0u;
    genome_arena_tail(&a, &jws, &jws_len);
    srmech_json_builder_t b;
    srmech_status_t st = srmech_json_builder_init(&b, jws, jws_len);
    if (st != SRMECH_OK) { return st; }
    const char *keys[5] = { "mpr_version", "data", "data_schema_id",
                            "attestation", "rendering" };
    srmech_json_value_t *v[5];
    v[0] = srmech_json_new_string(&b, "1.0", 3u);
    v[1] = genome_build_data(&b, s, chrom_items, region_items, leaf_dim, body_len);
    v[2] = srmech_json_new_string(&b, SRMECH_GENOME_SCHEMA_ID,
                                  (uint32_t)strlen(SRMECH_GENOME_SCHEMA_ID));
    v[3] = genome_build_attest(&b, s);
    v[4] = genome_build_render(&b);
    srmech_json_value_t *root = srmech_json_new_object(&b, keys, v, 5u);
    if (b.failed || root == NULL) { return SRMECH_ERR_OVERFLOW; }
    *out = root;
    if (wtail != NULL) { *wtail = (unsigned char *)jws + b.used; }
    if (wtail_len != NULL) { *wtail_len = jws_len - b.used; }
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
    assert(leaf_dim > 0u && s->n_chroms <= s->cap_chroms);
    srmech_json_value_t *root = NULL;
    void *wtail = NULL;
    size_t wtail_len = 0u;
    srmech_status_t st = genome_build_manifest_tree(s, leaf_dim, body_len,
                                                    ws, ws_len, &root,
                                                    &wtail, &wtail_len);
    if (st != SRMECH_OK) { return st; }
    /* Writer key-sort scratch = the builder's untouched arena tail. */
    return srmech_json_write_ws(root, out, out_cap, out_len, wtail, wtail_len);
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

/* §44 COUNT: walk the body's self-describing blocks (§55/v3 dual-format) and
 * count its CHROM caps AND its total blocks (a pre-scan, so the per-chromosome
 * arrays can be carved to EXACTLY that many — no compiled-in chromosome cap;
 * the block count IS n_turns). Validates every block parses and fits. */
static srmech_status_t genome_count_chroms(const unsigned char *body,
                                           size_t body_len, uint32_t leaf_dim,
                                           uint32_t *out_n, uint32_t *out_blocks)
{
    assert(out_n != NULL && out_blocks != NULL);
    assert(body != NULL || body_len == 0u);
    if (leaf_dim == 0u) { return SRMECH_ERR_BAD_INPUT; }
    uint32_t n = 0u;
    uint32_t blocks = 0u;
    for (size_t off = 0u; off < body_len; ) {
        size_t blen = 0u;
        srmech_status_t st = genome_block_len(body, body_len, off, leaf_dim,
                                              &blen);
        if (st != SRMECH_OK) { return st; }
        /* §89/§127: a CHROM cap, a §89 kernel telomere, OR a §127 active telomere
         * opens a chromosome. */
        if (body[off] == SRMECH_GENOME_CHROM_CAP_MARKER ||
            body[off] == SRMECH_GENOME_KERNEL_TELOMERE_MARKER ||
            body[off] == SRMECH_GENOME_ACTIVE_TELOMERE_MARKER) {
            if (n == 0xFFFFFFFFu) { return SRMECH_ERR_OVERFLOW; }
            n++;
        }
        if (blocks == 0xFFFFFFFFu) { return SRMECH_ERR_OVERFLOW; }
        blocks++;
        off += blen;
    }
    *out_n = n;
    *out_blocks = blocks;
    return SRMECH_OK;
}

/* Carve the per-chromosome string arrays (sized to `n`) off the arena `a` —
 * the bound is the caller's arena, not a constant. SRMECH_ERR_OVERFLOW when the
 * arena cannot fit them. */
static srmech_status_t genome_strings_alloc(genome_strings_t *s,
                                            genome_arena_t *a, uint32_t n)
{
    assert(s != NULL && a != NULL);
    assert(n != 0xFFFFFFFFu);
    s->cap_sha = genome_arena_alloc(a, (size_t)n * 65u);
    s->byte_offset = genome_arena_alloc(a, (size_t)n * sizeof(uint32_t));
    s->byte_len = genome_arena_alloc(a, (size_t)n * sizeof(uint32_t));
    s->label = genome_arena_alloc(a, (size_t)n * SRMECH_GENOME_MAX_LABEL);
    s->leaf_count = genome_arena_alloc(a, (size_t)n * sizeof(uint32_t));
    s->region_sha = genome_arena_alloc(a, (size_t)n * 65u);   /* v4 region digest */
    if (s->cap_sha == NULL || s->byte_offset == NULL || s->byte_len == NULL ||
        s->label == NULL || s->leaf_count == NULL || s->region_sha == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    s->cap_chroms = n;
    s->n_chroms = 0u;
    return SRMECH_OK;
}

/* §44 SCAN: walk the self-describing body block-by-block (§55/v3 dual-format
 * walker — caps and legacy turns are leaf_dim bytes, packed turns 1 +
 * ceil(leaf_dim/4)) and derive every chromosome's (label, cap_sha256,
 * leaf_count, byte_offset, byte_len) into the string block — this IS the
 * "manifest is a derived cache" claim in C. A CHROM cap opens a chromosome
 * (label read inline); each non-cap block is a data turn (leaf_count++); GENE
 * caps stay in the region (byte_len) but are not turns. */
static srmech_status_t genome_scan_chroms(genome_strings_t *s,
                                          const unsigned char *body,
                                          size_t body_len, uint32_t leaf_dim)
{
    assert(s != NULL);
    assert(body != NULL || body_len == 0u);
    s->n_chroms = 0u;
    int32_t cur = -1;
    for (size_t off = 0u; off < body_len; ) {
        size_t blen = 0u;
        srmech_status_t st = genome_block_len(body, body_len, off, leaf_dim,
                                              &blen);
        if (st != SRMECH_OK) { return st; }
        /* §89/§127: a CHROM cap, a §89 kernel telomere (0x6B), OR a §127 active
         * telomere (0x74) opens a chromosome. The label decode is UNIFORM (bytes [1:]
         * up to the first NUL) — the active telomere's count sits AFTER that NUL. */
        if (body[off] == SRMECH_GENOME_CHROM_CAP_MARKER ||
            body[off] == SRMECH_GENOME_KERNEL_TELOMERE_MARKER ||
            body[off] == SRMECH_GENOME_ACTIVE_TELOMERE_MARKER) {
            if (s->n_chroms >= s->cap_chroms) { return SRMECH_ERR_OVERFLOW; }
            cur = (int32_t)s->n_chroms;
            s->n_chroms++;
            st = srmech_sha256_hex(body + off, leaf_dim, s->cap_sha[cur]);
            if (st != SRMECH_OK) { return st; }
            st = genome_decode_label(body + off, leaf_dim, s->label[cur]);
            if (st != SRMECH_OK) { return st; }
            s->byte_offset[cur] = (uint32_t)off;
            s->byte_len[cur] = 0u;                /* accumulated below */
            s->leaf_count[cur] = 0u;
        } else {
            if (cur < 0) { return SRMECH_ERR_BAD_INPUT; }   /* turn before 1st cap */
            /* §60/§128/§130/§131/§132: a GENE cap (plain 0x47 / regulatory 0x67 / boolean 0x62 /
             * threshold 0x77 / graded 0x64) or a v5 KERNEL HEADER (0x4B) is not a data turn. The
             * §89 v6 Klein-4 header IS a coupled turn (counted). */
            if (body[off] != SRMECH_GENOME_GENE_CAP_MARKER &&
                body[off] != SRMECH_GENOME_REGULATORY_GENE_MARKER &&
                body[off] != SRMECH_GENOME_BOOLEAN_GENE_MARKER &&
                body[off] != SRMECH_GENOME_THRESHOLD_GENE_MARKER &&
                body[off] != SRMECH_GENOME_GRADED_GENE_MARKER &&
                body[off] != SRMECH_GENOME_KERNEL_HEADER_MARKER) {
                s->leaf_count[cur]++;
            }
        }
        s->byte_len[cur] += (uint32_t)blen;
        off += blen;
    }
    return SRMECH_OK;
}

/* Fill the strings block's version + rule + descriptor constants (shared by
 * genome_fill_strings and the O(1) append's rebuild-from-manifest). */
static srmech_status_t genome_fill_constants(genome_strings_t *s)
{
    assert(s != NULL);
    assert(sizeof(SRMECH_VERSION) > 0u);
    srmech_status_t st = srmech_sha256_hex(
        (const uint8_t *)SRMECH_GENOME_RULE_PREIMAGE,
        strlen(SRMECH_GENOME_RULE_PREIMAGE), s->rule_hash);
    if (st != SRMECH_OK) { return st; }
    st = srmech_sha256_hex((const uint8_t *)SRMECH_GENOME_SCHEMA_ID,
                           strlen(SRMECH_GENOME_SCHEMA_ID), s->descr_hash);
    if (st != SRMECH_OK) { return st; }
    memcpy(s->parser_version, "srmech ", 7u);
    memcpy(s->parser_version + 7u, SRMECH_VERSION, sizeof(SRMECH_VERSION));
    return SRMECH_OK;
}

/* v4 (rc115 #1245(b)): after the scan set every chromosome's byte span, hash
 * each FULL region [byte_offset, byte_offset+byte_len) into s->region_sha[i]
 * and fold them into the body_sha256 chain. The regions tile the body in order,
 * so this is the §44-derivable whole-body integrity value. */
static srmech_status_t genome_fill_regions_chain(genome_strings_t *s,
                                                 const unsigned char *body)
{
    assert(s != NULL);
    assert(body != NULL || s->n_chroms == 0u);
    for (uint32_t i = 0; i < s->n_chroms; i++) {
        srmech_status_t st = srmech_sha256_hex(body + s->byte_offset[i],
                                               s->byte_len[i], s->region_sha[i]);
        if (st != SRMECH_OK) { return st; }
    }
    return genome_chain_regions(s->region_sha, s->n_chroms, s->body_sha);
}

/* Fill the per-build string block from the body + the_one: the hashes, the
 * version string, and the §44 inline-cap chromosome scan. */
static srmech_status_t genome_fill_strings(genome_strings_t *s,
                                           genome_arena_t *a,
                                           const unsigned char *body,
                                           size_t body_len, uint32_t leaf_dim,
                                           const unsigned char *the_one)
{
    assert(s != NULL && the_one != NULL);
    assert(a != NULL && leaf_dim > 0u);
    uint32_t n_chroms = 0u;                            /* count → carve arrays */
    uint32_t n_blocks = 0u;                            /* §55/v3: == n_turns */
    srmech_status_t st = genome_count_chroms(body, body_len, leaf_dim,
                                             &n_chroms, &n_blocks);
    if (st != SRMECH_OK) { return st; }
    st = genome_strings_alloc(s, a, n_chroms);
    if (st != SRMECH_OK) { return st; }
    s->n_blocks = n_blocks;
    st = srmech_sha256_hex(the_one, leaf_dim, s->one_sha);
    if (st != SRMECH_OK) { return st; }
    genome_hex(the_one, leaf_dim, s->one_hex);
    st = genome_fill_constants(s);                         /* rule/descr/version */
    if (st != SRMECH_OK) { return st; }
    st = genome_scan_chroms(s, body, body_len, leaf_dim);  /* byte spans first */
    if (st != SRMECH_OK) { return st; }
    return genome_fill_regions_chain(s, body);             /* v4 regions + chain */
}

/* ------------------------------------------------------------------ *
 * Manifest write buffer — the serialised manifest bytes + trailing LF, carved
 * from the caller arena (NO fixed cap). The size is bounded by the chromosome
 * count: a fixed preamble + a per-chromosome JSON entry (label + 4 hashes/ints
 * + keys, < SRMECH_GENOME_MAX_LABEL + 600). The caller (Python) sizes the arena
 * to the genome.
 * ------------------------------------------------------------------ */
static size_t genome_manifest_cap(uint32_t n_chroms)
{
    assert(n_chroms != 0xFFFFFFFFu);
    assert(SRMECH_GENOME_MAX_LABEL > 0u);
    /* per chrom: the chromosome entry (label + 4 hashes/ints) AND the v4 region
     * entry ({byte_offset, byte_len, sha256}) — the 800 slop covers both. */
    return (size_t)4096u + (size_t)n_chroms * (size_t)(SRMECH_GENOME_MAX_LABEL + 800u);
}

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

/* §127/v7 (#726) — the active-telomere COUNT field offset: the byte right after the
 * inline label's NUL terminator. Returns the NUL index in *nul_off (BAD_INPUT if there
 * is no label NUL within leaf_dim, or the 8-byte count would run past leaf_dim). This
 * is the operand-read shared by srmech_genome_telomere_tick. */
static srmech_status_t genome_active_count_offset(const unsigned char *cap,
                                                  size_t leaf_dim, size_t *nul_off)
{
    assert(cap != NULL && nul_off != NULL);
    assert(leaf_dim > 0u);
    size_t i = 1u;                                  /* skip the 0x74 marker byte */
    while (i < leaf_dim && cap[i] != 0u) { i++; }   /* find the label terminator */
    if (i >= leaf_dim) { return SRMECH_ERR_BAD_INPUT; }        /* no label NUL */
    if (i + 1u + SRMECH_GENOME_ACTIVE_TELOMERE_COUNT_BYTES > leaf_dim) {
        return SRMECH_ERR_BAD_INPUT;                           /* count truncated */
    }
    *nul_off = i;
    return SRMECH_OK;
}

/* §127/v7 (#726) — the divide/gate op: the OPERAND (count) selects the OPERATOR. */
srmech_status_t srmech_genome_telomere_tick(
    const unsigned char *cap, size_t leaf_dim,
    unsigned char *out_cap, int *senescent, uint64_t *count_after)
{
    assert(cap != NULL || out_cap == NULL);
    assert(leaf_dim <= 256u);
    if (cap == NULL || out_cap == NULL || senescent == NULL || count_after == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (leaf_dim == 0u || cap[0] != SRMECH_GENOME_ACTIVE_TELOMERE_MARKER) {
        return SRMECH_ERR_BAD_INPUT;
    }
    size_t nul = 0u;
    srmech_status_t st = genome_active_count_offset(cap, leaf_dim, &nul);
    if (st != SRMECH_OK) { return st; }
    /* read the uint64 big-endian count (the operand) at the bytes after the NUL */
    uint64_t count = 0u;
    size_t base = nul + 1u;
    for (size_t k = 0u; k < SRMECH_GENOME_ACTIVE_TELOMERE_COUNT_BYTES; k++) {
        count = (count << 8) | (uint64_t)cap[base + k];
    }
    memcpy(out_cap, cap, leaf_dim);                 /* daughter starts as a copy */
    if (count == 0u) {
        *senescent = 1;                             /* Hayflick senescence — refuse */
        *count_after = 0u;                          /* count stays 0 (never negated) */
        return SRMECH_OK;
    }
    uint64_t after = count - 1u;                    /* DIVIDE: decrement by exactly 1 */
    for (size_t k = 0u; k < SRMECH_GENOME_ACTIVE_TELOMERE_COUNT_BYTES; k++) {
        unsigned shift = (unsigned)(8u *
            (SRMECH_GENOME_ACTIVE_TELOMERE_COUNT_BYTES - 1u - k));
        out_cap[base + k] = (unsigned char)((after >> shift) & 0xFFu);
    }
    *senescent = 0;
    *count_after = after;
    return SRMECH_OK;
}

/* §130/v9 (#730) — read one uint64 BIG-ENDIAN mask at cap[base..base+8). Bounds are checked by
 * the caller (genome_dnf_expresses). No abs (a mask is never negated). */
static uint64_t genome_read_u64_be(const unsigned char *cap, size_t base)
{
    assert(cap != NULL);
    assert(base < base + SRMECH_GENOME_REGULATORY_MASK_BYTES);   /* no wrap */
    uint64_t v = 0u;
    for (size_t k = 0u; k < SRMECH_GENOME_REGULATORY_MASK_BYTES; k++) {
        v = (v << 8) | (uint64_t)cap[base + k];
    }
    return v;
}

/* §130/v9 (#730) — evaluate a BOOLEAN GENE (cap[0] == 0x62): an arbitrary boolean function over
 * the conditions in DNF (an OR of (activator, repressor) AND-clauses). *expressed = 1 iff ANY
 * clause matches (cell_state & act) == act AND (cell_state & rep) == 0 (the empty DNF -> 0 =
 * never). Layout after the label NUL: gate_type(uint8) + n_terms(uint16 BE) + n_terms x
 * (activator(u64 BE) + repressor(u64 BE)). Byte-identical to the pure Python _dnf_expresses. No
 * arena; malloc-free; no abs; NEVER mutates cap (a READ). */
static srmech_status_t genome_dnf_expresses(
    const unsigned char *cap, size_t leaf_dim, uint64_t cell_state, int *expressed)
{
    assert(cap != NULL && expressed != NULL);
    assert(leaf_dim > 0u && leaf_dim <= 256u);
    size_t i = 1u;                                  /* skip the 0x62 marker byte */
    while (i < leaf_dim && cap[i] != 0u) { i++; }   /* find the label terminator */
    if (i >= leaf_dim) { return SRMECH_ERR_BAD_INPUT; }         /* no label NUL */
    size_t base = i + 1u;                           /* gate_type + n_terms header */
    if (base + 1u + SRMECH_GENOME_BOOLEAN_NTERMS_BYTES > leaf_dim) {
        return SRMECH_ERR_BAD_INPUT;                            /* header truncated */
    }
    if (cap[base] != SRMECH_GENOME_GATE_TYPE_BOOLEAN_DNF) {
        return SRMECH_ERR_BAD_INPUT;                            /* unsupported gate_type */
    }
    size_t nt_off = base + 1u;
    uint32_t n_terms = ((uint32_t)cap[nt_off] << 8) | (uint32_t)cap[nt_off + 1u];
    size_t terms_off = nt_off + SRMECH_GENOME_BOOLEAN_NTERMS_BYTES;
    if (terms_off + (size_t)n_terms * SRMECH_GENOME_BOOLEAN_TERM_BYTES > leaf_dim) {
        return SRMECH_ERR_BAD_INPUT;                            /* term list truncated */
    }
    int any = 0;
    for (uint32_t t = 0u; t < n_terms && any == 0; t++) {
        size_t o = terms_off + (size_t)t * SRMECH_GENOME_BOOLEAN_TERM_BYTES;
        uint64_t act = genome_read_u64_be(cap, o);
        uint64_t rep = genome_read_u64_be(cap, o + SRMECH_GENOME_REGULATORY_MASK_BYTES);
        if (((cell_state & act) == act) && ((cell_state & rep) == 0u)) { any = 1; }
    }
    *expressed = any;
    return SRMECH_OK;
}

/* §131/v10 (#731) — read one int64 BIG-ENDIAN SIGNED (two's-complement) value at
 * cap[base..base+8). Bounds are checked by the caller (genome_threshold_expresses). The signed
 * reconstruction is PORTABLE (no impl-defined uint->int narrowing): the high half is rebuilt via
 * ~v (whose top bit is clear, so the int64 cast is defined). No abs (the sign is meaningful). */
static int64_t genome_read_i64_be(const unsigned char *cap, size_t base)
{
    assert(cap != NULL);
    assert(base < base + SRMECH_GENOME_THRESHOLD_VALUE_BYTES);   /* no wrap */
    uint64_t v = 0u;
    for (size_t k = 0u; k < SRMECH_GENOME_THRESHOLD_VALUE_BYTES; k++) {
        v = (v << 8) | (uint64_t)cap[base + k];
    }
    if (v <= (uint64_t)INT64_MAX) { return (int64_t)v; }
    return -(int64_t)(~v) - 1;                       /* two's-complement, portable */
}

/* §131/v10 (#731) — evaluate a THRESHOLD GENE (cap[0] == 0x77): a LINEAR-THRESHOLD (perceptron)
 * gate over the condition bits — a per-condition SIGNED int64 WEIGHT vector + an int64 THRESHOLD.
 * *expressed = 1 iff Sum_i (weight_i * bit_i(cell_state)) >= threshold — the exact int64 signed sum
 * of the weights of the PRESENT conditions; the decision is the SIGN of (sum - threshold) compared
 * DIRECTLY (total >= threshold, so the compare cannot overflow) — Class-K, never abs. SIGNED
 * weights (an inhibitory input is negative). Layout after the label NUL: gate_type(uint8) +
 * n_weights(uint16 BE) + threshold(int64 BE signed) + n_weights x weight(int64 BE signed). On an
 * int64 accumulate OVERFLOW this returns SRMECH_ERR_OVERFLOW so the caller falls to the exact pure
 * (bignum) Python path — the native result, when produced, is byte-identical to Python. No arena;
 * malloc-free; no abs; NEVER mutates cap (a READ). */
static srmech_status_t genome_threshold_expresses(
    const unsigned char *cap, size_t leaf_dim, uint64_t cell_state, int *expressed)
{
    assert(cap != NULL && expressed != NULL);
    assert(leaf_dim > 0u && leaf_dim <= 256u);
    size_t i = 1u;                                  /* skip the 0x77 marker byte */
    while (i < leaf_dim && cap[i] != 0u) { i++; }   /* find the label terminator */
    if (i >= leaf_dim) { return SRMECH_ERR_BAD_INPUT; }         /* no label NUL */
    size_t base = i + 1u;                           /* gate_type + n_weights + threshold header */
    size_t hdr = 1u + SRMECH_GENOME_THRESHOLD_NWEIGHTS_BYTES + SRMECH_GENOME_THRESHOLD_VALUE_BYTES;
    if (base + hdr > leaf_dim) { return SRMECH_ERR_BAD_INPUT; }  /* header truncated */
    if (cap[base] != SRMECH_GENOME_GATE_TYPE_THRESHOLD) {
        return SRMECH_ERR_BAD_INPUT;                            /* unsupported gate_type */
    }
    size_t nw_off = base + 1u;
    uint32_t n_weights = ((uint32_t)cap[nw_off] << 8) | (uint32_t)cap[nw_off + 1u];
    size_t th_off = nw_off + SRMECH_GENOME_THRESHOLD_NWEIGHTS_BYTES;
    int64_t threshold = genome_read_i64_be(cap, th_off);
    size_t w_off = th_off + SRMECH_GENOME_THRESHOLD_VALUE_BYTES;
    if (w_off + (size_t)n_weights * SRMECH_GENOME_THRESHOLD_VALUE_BYTES > leaf_dim) {
        return SRMECH_ERR_BAD_INPUT;                            /* weight vector truncated */
    }
    int64_t total = 0;
    for (uint32_t t = 0u; t < n_weights && t < 64u; t++) {      /* bit_t == 0 for t >= 64 (uint64) */
        if (((cell_state >> t) & 1u) == 0u) { continue; }      /* condition absent — weight skipped */
        int64_t w = genome_read_i64_be(cap, w_off + (size_t)t * SRMECH_GENOME_THRESHOLD_VALUE_BYTES);
        if ((w > 0 && total > INT64_MAX - w) ||                 /* defer to the exact pure path */
            (w < 0 && total < INT64_MIN - w)) { return SRMECH_ERR_OVERFLOW; }
        total += w;                                            /* exact int64 accumulate */
    }
    *expressed = (total >= threshold) ? 1 : 0;                 /* Class-K sign-branch; never abs */
    return SRMECH_OK;
}

/* §128/v8 (#728) + §129 (#729) — the per-gene EXPRESSION read-filter: the OPERAND (cell_state)
 * selects the OPERATOR (express or not). A plain GENE cap (0x47) always expresses (masks 0); a
 * REGULATORY GENE cap (0x67) carries the TWO KLEIN-4 bit-planes (activator then repressor) and
 * expresses iff (cell_state & activator) == activator (ALL activators PRESENT) AND
 * (cell_state & repressor) == 0 (NO repressor PRESENT). Per condition (act_bit, rep_bit) is a
 * Klein-4 role: (0,0) don't-care / (1,0) activator / (0,1) repressor / (1,1) never (present AND
 * absent = contradiction -> auto-silenced). §129 DUAL-READ: the repressor field lives in what
 * was NUL padding, so a rc128 single-mask cap / a short leaf carries NO repressor field ->
 * repressor 0 (activator=mask, identical rc128 behaviour). mask_out reports the ACTIVATOR (the
 * first plane). §130/v9 (#730): a BOOLEAN GENE cap (0x62) carries the GENERAL gate-type — an
 * arbitrary boolean function over the conditions in DNF; *expressed = 1 iff ANY clause matches
 * (delegated to genome_dnf_expresses; E1 subset E2). mask_out is 0 for a boolean gene. NEVER
 * mutates cap (a READ). No abs (a mask / cell_state is never negated). */
srmech_status_t srmech_genome_gene_express(
    const unsigned char *cap, size_t leaf_dim, uint64_t cell_state,
    int *expressed, uint64_t *mask_out)
{
    assert(cap != NULL || expressed == NULL);
    assert(leaf_dim <= 256u);
    if (cap == NULL || expressed == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (leaf_dim == 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    unsigned char marker = cap[0];
    if (marker == SRMECH_GENOME_GENE_CAP_MARKER) {
        if (mask_out != NULL) { *mask_out = 0u; }
        *expressed = 1;             /* unregulated gene == masks 0; (cell_state & 0) == 0 */
        return SRMECH_OK;
    }
    if (marker == SRMECH_GENOME_BOOLEAN_GENE_MARKER) {
        /* §130 the GENERAL gate-type: evaluate the DNF (express iff ANY clause matches). No
         * single activator plane, so mask_out is 0. */
        if (mask_out != NULL) { *mask_out = 0u; }
        return genome_dnf_expresses(cap, leaf_dim, cell_state, expressed);
    }
    if (marker == SRMECH_GENOME_THRESHOLD_GENE_MARKER) {
        /* §131 the LINEAR-THRESHOLD gate-type: evaluate the perceptron (express iff the SIGNED
         * weighted sum >= threshold). No single activator plane, so mask_out is 0. */
        if (mask_out != NULL) { *mask_out = 0u; }
        return genome_threshold_expresses(cap, leaf_dim, cell_state, expressed);
    }
    if (marker != SRMECH_GENOME_REGULATORY_GENE_MARKER) {
        return SRMECH_ERR_BAD_INPUT;          /* not 0x47 / 0x62 / 0x67 / 0x77 — not a gene */
    }
    /* a regulatory gene — read the uint64 big-endian mask(s) after the label's NUL terminator */
    size_t i = 1u;                                  /* skip the 0x67 marker byte */
    while (i < leaf_dim && cap[i] != 0u) { i++; }   /* find the label terminator */
    if (i >= leaf_dim) { return SRMECH_ERR_BAD_INPUT; }        /* no label NUL */
    size_t act_base = i + 1u;
    if (act_base + SRMECH_GENOME_REGULATORY_MASK_BYTES > leaf_dim) {
        return SRMECH_ERR_BAD_INPUT;                           /* activator field truncated */
    }
    uint64_t activator = 0u;
    for (size_t k = 0u; k < SRMECH_GENOME_REGULATORY_MASK_BYTES; k++) {
        activator = (activator << 8) | (uint64_t)cap[act_base + k];
    }
    /* §129: the repressor plane sits in what was NUL padding — present iff the leaf has room;
     * absent (rc128 single-mask / short leaf) => repressor 0 (no repression). */
    uint64_t repressor = 0u;
    size_t rep_base = act_base + SRMECH_GENOME_REGULATORY_MASK_BYTES;
    if (rep_base + SRMECH_GENOME_REGULATORY_MASK_BYTES <= leaf_dim) {
        for (size_t k = 0u; k < SRMECH_GENOME_REGULATORY_MASK_BYTES; k++) {
            repressor = (repressor << 8) | (uint64_t)cap[rep_base + k];
        }
    }
    if (mask_out != NULL) { *mask_out = activator; }
    *expressed = (((cell_state & activator) == activator)     /* ALL activators PRESENT */
                 && ((cell_state & repressor) == 0u)) ? 1 : 0; /* NO repressor PRESENT; no abs */
    return SRMECH_OK;
}

/* §132/v11 (#732) — CLAMP the raw dose `raw_num / denom` to [0, 1] and REDUCE, returning the
 * exact-rational LEVEL as (num_out, den_out). `denom` is POSITIVE. The clamp is a Class-K
 * sign-branch, NEVER abs: raw_num <= 0 -> (0, 1) (off); raw_num >= denom -> (1, 1) (full); else the
 * in-range fraction reduced by the Class-I gcd (srmech_gcd; both parts positive, no abs). No arena;
 * malloc-free. Byte-identical to genome._clamp_reduce_level in Python. */
static srmech_status_t genome_clamp_reduce_level(
    int64_t raw_num, uint64_t denom, uint64_t *num_out, uint64_t *den_out)
{
    assert(num_out != NULL && den_out != NULL);
    assert(denom > 0u);
    if (raw_num <= 0) {                              /* Class-K: sign of raw_num — off */
        *num_out = 0u; *den_out = 1u;
        return SRMECH_OK;
    }
    uint64_t num = (uint64_t)raw_num;               /* raw_num > 0, so the cast is defined */
    if (num >= denom) {                             /* Class-K: sign of (raw_num - denom) — full */
        *num_out = 1u; *den_out = 1u;
        return SRMECH_OK;
    }
    uint64_t g = 0u;
    srmech_status_t st = srmech_gcd(num, denom, &g); /* Class-I gcd (both positive; no abs) */
    if (st != SRMECH_OK) { return st; }
    assert(g > 0u);                                 /* 0 < num < denom, so gcd >= 1 */
    *num_out = num / g;
    *den_out = denom / g;
    return SRMECH_OK;
}

/* §132/v11 (#732) — evaluate a GRADED GENE (cap[0] == 0x64): the ANALOG dose-response LEVEL. Read
 * the SIGNED int64 LEVEL-WEIGHT vector + the POSITIVE uint64 DENOMINATOR after the label NUL; the
 * level is Sum_i (level_weight_i * bit_i(cell_state)) / denom clamped to [0, 1] and gcd-reduced ->
 * (num_out, den_out). Layout after the label NUL: gate_type(uint8) + n_weights(uint16 BE) +
 * denom(uint64 BE POSITIVE) + n_weights x level_weight(int64 BE SIGNED). On an int64 dose
 * accumulate OVERFLOW this returns SRMECH_ERR_OVERFLOW so the caller falls to the exact pure
 * (bignum) Python path. No arena; malloc-free; no abs; NEVER mutates cap (a READ). */
static srmech_status_t genome_graded_level(
    const unsigned char *cap, size_t leaf_dim, uint64_t cell_state,
    uint64_t *num_out, uint64_t *den_out)
{
    assert(cap != NULL && num_out != NULL && den_out != NULL);
    assert(leaf_dim > 0u && leaf_dim <= 256u);
    size_t i = 1u;                                  /* skip the 0x64 marker byte */
    while (i < leaf_dim && cap[i] != 0u) { i++; }   /* find the label terminator */
    if (i >= leaf_dim) { return SRMECH_ERR_BAD_INPUT; }        /* no label NUL */
    size_t base = i + 1u;                           /* gate_type + n_weights + denom header */
    size_t hdr = 1u + SRMECH_GENOME_GRADED_NWEIGHTS_BYTES + SRMECH_GENOME_GRADED_DENOM_BYTES;
    if (base + hdr > leaf_dim) { return SRMECH_ERR_BAD_INPUT; }  /* header truncated */
    if (cap[base] != SRMECH_GENOME_GATE_TYPE_GRADED) {
        return SRMECH_ERR_BAD_INPUT;                            /* unsupported gate_type */
    }
    size_t nw_off = base + 1u;
    uint32_t n_weights = ((uint32_t)cap[nw_off] << 8) | (uint32_t)cap[nw_off + 1u];
    size_t dn_off = nw_off + SRMECH_GENOME_GRADED_NWEIGHTS_BYTES;
    uint64_t denom = genome_read_u64_be(cap, dn_off);
    if (denom == 0u) { return SRMECH_ERR_BAD_INPUT; }           /* a divisor is never zero */
    size_t w_off = dn_off + SRMECH_GENOME_GRADED_DENOM_BYTES;
    if (w_off + (size_t)n_weights * SRMECH_GENOME_GRADED_WEIGHT_BYTES > leaf_dim) {
        return SRMECH_ERR_BAD_INPUT;                            /* weight vector truncated */
    }
    int64_t total = 0;
    for (uint32_t t = 0u; t < n_weights && t < 64u; t++) {      /* bit_t == 0 for t >= 64 (uint64) */
        if (((cell_state >> t) & 1u) == 0u) { continue; }      /* condition absent — weight skipped */
        int64_t w = genome_read_i64_be(cap, w_off + (size_t)t * SRMECH_GENOME_GRADED_WEIGHT_BYTES);
        if ((w > 0 && total > INT64_MAX - w) ||                 /* defer to the exact pure path */
            (w < 0 && total < INT64_MIN - w)) { return SRMECH_ERR_OVERFLOW; }
        total += w;                                            /* exact int64 signed dose accumulate */
    }
    return genome_clamp_reduce_level(total, denom, num_out, den_out);
}

srmech_status_t srmech_genome_gene_express_levels(
    const unsigned char *cap, size_t leaf_dim, uint64_t cell_state,
    uint64_t *num_out, uint64_t *den_out)
{
    assert(cap != NULL || num_out == NULL);
    assert(leaf_dim <= 256u);
    if (cap == NULL || num_out == NULL || den_out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (leaf_dim == 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (cap[0] == SRMECH_GENOME_GRADED_GENE_MARKER) {
        /* §132 the ORTHOGONAL analog LEVEL axis: the exact-rational dose-response. */
        return genome_graded_level(cap, leaf_dim, cell_state, num_out, den_out);
    }
    /* a BINARY gene — the degenerate {0, 1} case: level 1 iff its E1/E2/E4 gate passes (the SAME
     * decision as srmech_genome_gene_express), else 0. */
    int expressed = 0;
    srmech_status_t st = srmech_genome_gene_express(cap, leaf_dim, cell_state, &expressed, NULL);
    if (st != SRMECH_OK) { return st; }
    *num_out = expressed ? 1u : 0u;
    *den_out = 1u;
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
    /* Write turns.bin first (verbatim body), then hash + scan + build manifest.
     * The chromosome arrays, the manifest buffer, and the json tree are all
     * carved from the caller arena — bound = caller RAM, no compiled-in cap. */
    st = genome_write_file(body_path, "wb", body, body_len);
    if (st != SRMECH_OK) { return st; }
    genome_arena_t a;
    genome_arena_init(&a, ws, ws_len);
    genome_strings_t strs;
    st = genome_fill_strings(&strs, &a, body, body_len, leaf_dim, the_one);
    if (st != SRMECH_OK) { return st; }
    size_t man_cap = genome_manifest_cap(strs.n_chroms);
    char *manifest = genome_arena_alloc(&a, man_cap + 1u);
    if (manifest == NULL) { return SRMECH_ERR_OVERFLOW; }
    void *tws = NULL;
    size_t tws_len = 0u;
    genome_arena_tail(&a, &tws, &tws_len);
    size_t mlen = 0u;
    st = genome_build_manifest(&strs, leaf_dim, body_len,
                               tws, tws_len, manifest, man_cap, &mlen);
    if (st != SRMECH_OK) { return st; }
    manifest[mlen] = '\n';                 /* trailing LF, like _write_manifest */
    return genome_write_file(man_path, "wb",
                             (const unsigned char *)manifest, mlen + 1u);
}

/* The arena byte count the genome ops need for a body of `body_len` bytes with
 * `n_chroms` chromosomes when an op also stages a `region_len`-byte region (a
 * .chr export/import region, or an append/replace region; 0 otherwise). The C
 * carves ALL scratch from the caller arena, so the caller sizes the arena from
 * THIS — capacity is defined by the layout, not a guess. Every term traces to a
 * real allocation: two body copies (the grown/spliced body + the §44 rebuild
 * scan copy), the .chr region+hex+io (region + 2*hex + 2*io ≈ 5*region), the
 * per-chromosome strings arrays + manifest entry + json subtree (+ alignment),
 * the manifest header, and a fixed slop for the top-level json + the ~20 arena
 * 16-byte alignment pads. Pure arithmetic, no I/O. */
size_t srmech_genome_arena_bytes(size_t body_len, uint32_t n_chroms,
                                 size_t region_len)
{
    assert(n_chroms != 0xFFFFFFFFu);
    assert(SRMECH_GENOME_MAX_LABEL > 0u);
    size_t per_chrom =
        (size_t)(65u + 65u + 8u + 8u + SRMECH_GENOME_MAX_LABEL + 8u) /* strings arrays
                                                    * (+65 = the v4 region_sha) */
      + (size_t)(SRMECH_GENOME_MAX_LABEL + 800u)                /* manifest chrom + region entry */
      + 1152u                                                   /* json nodes+ptrs+decoded
                                                    * (chrom subtree + v4 region subtree) */
      + 64u;                                                    /* per-chrom align pads */
    size_t bodies = 2u * body_len + region_len;     /* spliced/grown body + rebuild copy */
    size_t chr = 5u * region_len + 8192u;           /* region + 2*hex + 2*io + slop */
    size_t fixed = 64u * 1024u + 4096u;             /* top-level json + manifest header */
    return bodies + chr + (size_t)n_chroms * per_chrom + fixed;
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

/* Byte length of <dir>/turns.bin — the APPEND grow / §45 splice callers use it
 * to arena-size the body buffer (carved from the caller arena, no compiled-in
 * cap). SRMECH_ERR_IO if turns.bin is missing / unstattable. */
static srmech_status_t genome_body_size(const char *dir, size_t *out)
{
    assert(dir != NULL);
    assert(out != NULL);
    char body_path[SRMECH_GENOME_PATH_MAX];
    srmech_status_t st = genome_join(dir, SRMECH_GENOME_BODY,
                                     body_path, sizeof(body_path));
    if (st != SRMECH_OK) { return st; }
    return genome_file_size(body_path, out);
}

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
    genome_arena_t a;
    genome_arena_init(&a, ws, ws_len);
    size_t msz = 0u;
    if (genome_file_size(man_path, &msz) == SRMECH_OK) {  /* fast path: parse it */
        char *manbuf = genome_arena_alloc(&a, msz + 1u);
        if (manbuf == NULL) { return SRMECH_ERR_OVERFLOW; }
        void *ptws = NULL;
        size_t ptws_len = 0u;
        genome_arena_tail(&a, &ptws, &ptws_len);
        size_t mlen = 0u;
        return genome_parse_manifest(dir, manbuf, msz + 1u, &mlen,
                                     ptws, ptws_len, out);
    }
    if (the_one == NULL || the_one_len == 0u || the_one_len > 256u) {
        return SRMECH_ERR_BAD_INPUT;                  /* cannot scan w/o leaf_dim */
    }
    uint32_t leaf_dim = (uint32_t)the_one_len;
    char body_path[SRMECH_GENOME_PATH_MAX];
    st = genome_join(dir, SRMECH_GENOME_BODY, body_path, sizeof(body_path));
    if (st != SRMECH_OK) { return st; }
    size_t bsz = 0u;
    st = genome_file_size(body_path, &bsz);
    if (st != SRMECH_OK) { return st; }
    unsigned char *body = genome_arena_alloc(&a, (bsz == 0u) ? 1u : bsz);
    if (body == NULL) { return SRMECH_ERR_OVERFLOW; }
    size_t blen = 0u;
    st = genome_read_file(body_path, body, bsz, &blen);
    if (st != SRMECH_OK) { return st; }
    genome_strings_t rstrs;
    st = genome_fill_strings(&rstrs, &a, body, blen, leaf_dim, the_one);
    if (st != SRMECH_OK) { return st; }
    void *tws = NULL;
    size_t tws_len = 0u;
    genome_arena_tail(&a, &tws, &tws_len);
    return genome_build_manifest_tree(&rstrs, leaf_dim, blen, tws, tws_len,
                                      out, NULL, NULL);
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

/* v4 (rc115 #1245(b)): re-fold the body_sha256 CHAIN from the manifest's
 * chromosome byte spans (== the region partition) and compare to body_sha256 —
 * the regions must tile [0, body_len) in order. `chain` (>= 65) is scratch. */
static srmech_status_t genome_verify_body_chain(const unsigned char *body,
    size_t body_len, const srmech_json_value_t *arr,
    const srmech_json_value_t *bsha, char *chain)
{
    assert(body != NULL || body_len == 0u);
    assert(arr != NULL && bsha != NULL && chain != NULL);
    srmech_status_t st = srmech_sha256_hex((const uint8_t *)"", 0u, chain);
    if (st != SRMECH_OK) { return st; }
    size_t expect_off = 0u;
    for (uint32_t i = 0; i < arr->u.arr.n; i++) {
        const srmech_json_value_t *c = arr->u.arr.items[i];
        const srmech_json_value_t *bo = srmech_json_object_get(c, "byte_offset");
        const srmech_json_value_t *bl = srmech_json_object_get(c, "byte_len");
        if (bo == NULL || bl == NULL || bo->type != SRMECH_JSON_INT ||
            bl->type != SRMECH_JSON_INT) { return SRMECH_ERR_BAD_INPUT; }
        size_t off = (size_t)bo->u.i, len = (size_t)bl->u.i;
        if (off != expect_off || len > body_len - off) { return SRMECH_ERR_BAD_INPUT; }
        char rh[65];
        st = srmech_sha256_hex(body + off, len, rh);
        if (st != SRMECH_OK) { return st; }
        st = genome_chain_fold(chain, rh);
        if (st != SRMECH_OK) { return st; }
        expect_off = off + len;
    }
    if (expect_off != body_len) { return SRMECH_ERR_BAD_INPUT; }
    return genome_str_eq(bsha, chain) ? SRMECH_OK : SRMECH_ERR_BAD_INPUT;
}

/* Whole-body integrity bound, format-aware (rc115 #1245(b)): v4 (a `regions`
 * array present) re-folds the region chain from the chromosome byte spans; v2/v3
 * (no `regions`) checks sha256(body) == body_sha256. The GenomeBoundingError
 * analogue — SRMECH_ERR_BAD_INPUT on any mismatch. */
static srmech_status_t genome_verify_body(const unsigned char *body,
                                          size_t body_len,
                                          const srmech_json_value_t *manifest)
{
    assert(body != NULL || body_len == 0u);
    assert(manifest != NULL);
    const srmech_json_value_t *bsha = genome_data_get(manifest, "body_sha256");
    if (bsha == NULL || bsha->type != SRMECH_JSON_STRING) {
        return SRMECH_ERR_BAD_INPUT;
    }
    const srmech_json_value_t *regions = genome_data_get(manifest, "regions");
    if (regions == NULL) {                          /* v2/v3 whole-body digest */
        char got[65];
        srmech_status_t st = srmech_sha256_hex(body, body_len, got);
        if (st != SRMECH_OK) { return st; }
        return genome_str_eq(bsha, got) ? SRMECH_OK : SRMECH_ERR_BAD_INPUT;
    }
    const srmech_json_value_t *arr = genome_data_get(manifest, "chromosomes");
    if (arr == NULL || arr->type != SRMECH_JSON_ARRAY) {
        return SRMECH_ERR_BAD_INPUT;
    }
    char chain[65];
    return genome_verify_body_chain(body, body_len, arr, bsha, chain);
}

/* ------------------------------------------------------------------ *
 * LOAD — read turns.bin, re-verify the whole body vs manifest body_sha256.
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
    char body_path[SRMECH_GENOME_PATH_MAX];
    st = genome_join(dir, SRMECH_GENOME_BODY, body_path, sizeof(body_path));
    if (st != SRMECH_OK) { return st; }
    st = genome_read_file(body_path, out, out_cap, out_len);
    if (st != SRMECH_OK) { return st; }
    /* rc115 (#1245(b)): re-verify the whole body against body_sha256 — the v4
     * region chain (or the v2/v3 whole-body digest for a legacy genome). */
    return genome_verify_body(out, *out_len, manifest);
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

/* §44/§45: read <dir>/turns.bin into `out` (cap out_cap) and bound-check the
 * whole body against the manifest's body_sha256 — the GenomeBoundingError
 * analogue (never grow OR splice a corrupt body). *len gets the body length.
 * Shared by APPEND (grow) and the §45 in-place edits (remove / replace). */
static srmech_status_t genome_read_bound_body(const char *dir,
                                              const srmech_json_value_t *manifest,
                                              unsigned char *out, size_t out_cap,
                                              size_t *len)
{
    assert(dir != NULL && manifest != NULL);
    assert(out != NULL && len != NULL);
    char body_path[SRMECH_GENOME_PATH_MAX];
    srmech_status_t st = genome_join(dir, SRMECH_GENOME_BODY,
                                     body_path, sizeof(body_path));
    if (st != SRMECH_OK) { return st; }
    st = genome_read_file(body_path, out, out_cap, len);
    if (st != SRMECH_OK) { return st; }
    /* rc115 (#1245(b)): format-aware whole-body bound (v4 chain | v2/v3 digest) —
     * never grow OR splice a corrupt body. */
    return genome_verify_body(out, *len, manifest);
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
    size_t old_len = 0u;
    srmech_status_t st = genome_read_bound_body(dir, manifest, out, out_cap,
                                                &old_len);
    if (st != SRMECH_OK) { return st; }
    if (old_len + region_len > out_cap) { return SRMECH_ERR_OVERFLOW; }
    if (region_len != 0u) { memcpy(out + old_len, region, region_len); }
    *new_len = old_len + region_len;
    return SRMECH_OK;
}

/* Copy obj[key]'s string value into `out` (NUL-terminated; cap includes the
 * NUL). SRMECH_ERR_BAD_INPUT if absent / not a string / too long. */
static srmech_status_t genome_copy_jstr(const srmech_json_value_t *obj,
                                        const char *key, char *out, size_t cap)
{
    assert(obj != NULL && key != NULL);
    assert(out != NULL && cap > 0u);
    const srmech_json_value_t *v = srmech_json_object_get(obj, key);
    if (v == NULL || v->type != SRMECH_JSON_STRING ||
        (size_t)v->u.str.len + 1u > cap) { return SRMECH_ERR_BAD_INPUT; }
    memcpy(out, v->u.str.ptr, v->u.str.len);
    out[v->u.str.len] = '\0';
    return SRMECH_OK;
}

/* Read obj[key]'s non-negative int value into *out. */
static srmech_status_t genome_read_ju32(const srmech_json_value_t *obj,
                                        const char *key, uint32_t *out)
{
    assert(obj != NULL && key != NULL);
    assert(out != NULL);
    const srmech_json_value_t *v = srmech_json_object_get(obj, key);
    if (v == NULL || v->type != SRMECH_JSON_INT || v->u.i < 0) {
        return SRMECH_ERR_BAD_INPUT;
    }
    *out = (uint32_t)v->u.i;
    return SRMECH_OK;
}

/* Scan the ONE-chromosome append region (O(region_len)): require its first block
 * to be a CHROM cap, hash the cap (first leaf_dim bytes) into `cap_sha` and the
 * whole region into `region_sha`, and count DATA turns + total blocks. A second
 * CHROM cap (a multi-chromosome region) is rejected. */
static srmech_status_t genome_scan_region(const unsigned char *region,
    size_t region_len, uint32_t leaf_dim, char *cap_sha, char *region_sha,
    uint32_t *leaf_count, uint32_t *n_blocks)
{
    assert(region != NULL && cap_sha != NULL);
    assert(region_sha != NULL && leaf_count != NULL && n_blocks != NULL);
    /* §89/§127: an append region opens with a CHROM cap, a §89 kernel telomere, OR a
     * §127 active telomere (an appended active-telomere chromosome). */
    if (region_len < (size_t)leaf_dim ||
        (region[0] != SRMECH_GENOME_CHROM_CAP_MARKER &&
         region[0] != SRMECH_GENOME_KERNEL_TELOMERE_MARKER &&
         region[0] != SRMECH_GENOME_ACTIVE_TELOMERE_MARKER)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    srmech_status_t st = srmech_sha256_hex(region, leaf_dim, cap_sha);
    if (st != SRMECH_OK) { return st; }
    st = srmech_sha256_hex(region, region_len, region_sha);
    if (st != SRMECH_OK) { return st; }
    uint32_t lc = 0u, nb = 0u;
    for (size_t off = 0u; off < region_len; ) {
        size_t blen = 0u;
        st = genome_block_len(region, region_len, off, leaf_dim, &blen);
        if (st != SRMECH_OK) { return st; }
        unsigned char kind = region[off];
        if (off != 0u && (kind == SRMECH_GENOME_CHROM_CAP_MARKER ||
                          kind == SRMECH_GENOME_KERNEL_TELOMERE_MARKER ||
                          kind == SRMECH_GENOME_ACTIVE_TELOMERE_MARKER)) {
            return SRMECH_ERR_BAD_INPUT;  /* one append == ONE chromosome */
        }
        /* §60/§127/§128/§130/§131/§132: a GENE cap (plain 0x47 / regulatory 0x67 / boolean 0x62 /
         * threshold 0x77 / graded 0x64) or a v5 KERNEL HEADER (0x4B) is not a data turn; the §89
         * kernel telomere / §127 active telomere opens the region (off==0). The §89 Klein-4 header
         * IS a coupled turn. */
        if (kind != SRMECH_GENOME_CHROM_CAP_MARKER &&
            kind != SRMECH_GENOME_KERNEL_TELOMERE_MARKER &&
            kind != SRMECH_GENOME_ACTIVE_TELOMERE_MARKER &&
            kind != SRMECH_GENOME_GENE_CAP_MARKER &&
            kind != SRMECH_GENOME_REGULATORY_GENE_MARKER &&
            kind != SRMECH_GENOME_BOOLEAN_GENE_MARKER &&
            kind != SRMECH_GENOME_THRESHOLD_GENE_MARKER &&
            kind != SRMECH_GENOME_GRADED_GENE_MARKER &&
            kind != SRMECH_GENOME_KERNEL_HEADER_MARKER) { lc++; }
        nb++;
        off += blen;
    }
    *leaf_count = lc;
    *n_blocks = nb;
    return SRMECH_OK;
}

/* Copy the i-th existing chromosome (manifest chromosomes[i] + regions[i]) into
 * the strings block — the O(1) append reuses the OLD entries verbatim. */
static srmech_status_t genome_copy_chrom(genome_strings_t *s, uint32_t i,
    const srmech_json_value_t *carr, const srmech_json_value_t *rarr)
{
    assert(s != NULL && carr != NULL && rarr != NULL);
    assert(i < s->cap_chroms);
    const srmech_json_value_t *c = carr->u.arr.items[i];
    const srmech_json_value_t *r = rarr->u.arr.items[i];
    srmech_status_t st = genome_copy_jstr(c, "label", s->label[i],
                                          SRMECH_GENOME_MAX_LABEL);
    if (st != SRMECH_OK) { return st; }
    st = genome_copy_jstr(c, "cap_sha256", s->cap_sha[i], 65u);
    if (st != SRMECH_OK) { return st; }
    st = genome_copy_jstr(r, "sha256", s->region_sha[i], 65u);
    if (st != SRMECH_OK) { return st; }
    st = genome_read_ju32(c, "leaf_count", &s->leaf_count[i]);
    if (st != SRMECH_OK) { return st; }
    st = genome_read_ju32(c, "byte_offset", &s->byte_offset[i]);
    if (st != SRMECH_OK) { return st; }
    return genome_read_ju32(c, "byte_len", &s->byte_len[i]);
}

/* Fill the strings block from the OLD manifest tree + the new region — the O(1)
 * append core (no whole-body read/hash/scan). `s`'s arrays are already carved to
 * n_old+1. Sets every EXISTING entry (verbatim from the manifest), the NEW
 * chromosome (index n_old, scanned from `region`), n_blocks, and EXTENDS the
 * body_sha256 chain from its prior head. Returns the new label's dup status via
 * genome_check_new_label. */
static srmech_status_t genome_append_fill(genome_strings_t *s,
    const srmech_json_value_t *manifest, uint32_t n_old, const char *label,
    const unsigned char *region, size_t region_len, uint32_t leaf_dim,
    size_t old_len)
{
    assert(s != NULL && manifest != NULL && label != NULL);
    assert(region != NULL && strlen(label) + 1u <= SRMECH_GENOME_MAX_LABEL);
    const srmech_json_value_t *carr = genome_data_get(manifest, "chromosomes");
    const srmech_json_value_t *rarr = genome_data_get(manifest, "regions");
    const srmech_json_value_t *dto = genome_data_get(manifest, "the_one");
    const srmech_json_value_t *nt = genome_data_get(manifest, "n_turns");
    const srmech_json_value_t *bsha = genome_data_get(manifest, "body_sha256");
    if (carr == NULL || rarr == NULL || dto == NULL || nt == NULL ||
        bsha == NULL || carr->type != SRMECH_JSON_ARRAY ||
        rarr->type != SRMECH_JSON_ARRAY || nt->type != SRMECH_JSON_INT ||
        bsha->type != SRMECH_JSON_STRING || carr->u.arr.n != n_old ||
        rarr->u.arr.n != n_old) { return SRMECH_ERR_BAD_INPUT; }
    srmech_status_t st = genome_copy_jstr(dto, "sha256", s->one_sha, 65u);
    if (st != SRMECH_OK) { return st; }
    st = genome_copy_jstr(dto, "hex", s->one_hex, 2u * 256u + 1u);
    if (st != SRMECH_OK) { return st; }
    if (bsha->u.str.len != 64u) { return SRMECH_ERR_BAD_INPUT; }
    memcpy(s->body_sha, bsha->u.str.ptr, 64u);     /* prior chain head */
    s->body_sha[64] = '\0';
    st = genome_fill_constants(s);
    if (st != SRMECH_OK) { return st; }
    for (uint32_t i = 0; i < n_old; i++) {
        const srmech_json_value_t *lv =
            srmech_json_object_get(carr->u.arr.items[i], "label");
        if (genome_str_eq(lv, label)) { return SRMECH_ERR_BAD_INPUT; }  /* dup */
        st = genome_copy_chrom(s, i, carr, rarr);
        if (st != SRMECH_OK) { return st; }
    }
    uint32_t new_lc = 0u, new_nb = 0u;
    st = genome_scan_region(region, region_len, leaf_dim, s->cap_sha[n_old],
                            s->region_sha[n_old], &new_lc, &new_nb);
    if (st != SRMECH_OK) { return st; }
    memcpy(s->label[n_old], label, strlen(label) + 1u);
    s->leaf_count[n_old] = new_lc;
    s->byte_offset[n_old] = (uint32_t)old_len;
    s->byte_len[n_old] = (uint32_t)region_len;
    s->n_chroms = n_old + 1u;
    s->n_blocks = (uint32_t)nt->u.i + new_nb;
    return genome_chain_fold(s->body_sha, s->region_sha[n_old]);  /* extend chain */
}

/* Portable byte-substring probe (MSVC has no memmem): 1 iff `needle` occurs in
 * `hay`. Used only to sniff the v4 "regions" key in the manifest text. */
static int genome_bytes_contains(const char *hay, size_t hay_len,
                                 const char *needle, size_t needle_len)
{
    assert(hay != NULL || hay_len == 0u);
    assert(needle != NULL && needle_len > 0u);
    if (needle_len > hay_len) { return 0; }
    for (size_t i = 0; i + needle_len <= hay_len; i++) {
        if (memcmp(hay + i, needle, needle_len) == 0) { return 1; }
    }
    return 0;
}

/* The O(1) v4 fast path: parse the manifest ONCE, rebuild the manifest from its
 * entries + the new region, tail-extend turns.bin, write the manifest. No
 * whole-body read/hash/scan — bounded by the manifest + the new region. */
static srmech_status_t genome_append_v4(const char *dir, const char *label,
    const unsigned char *region, size_t region_len, uint32_t leaf_dim,
    genome_arena_t *a, char *manbuf, size_t msz, size_t mlen, size_t old_len)
{
    assert(dir != NULL && label != NULL && a != NULL && manbuf != NULL);
    assert(region != NULL && leaf_dim > 0u);
    /* Parse workspace bound: the tree of a manifest of `msz` bytes sits in a few
     * multiples of the source + a fixed base (the caller sizes the whole arena
     * from srmech_genome_arena_bytes, generously). */
    size_t pws_len = 4u * msz + 262144u;
    void *pws = genome_arena_alloc(a, pws_len);
    if (pws == NULL) { return SRMECH_ERR_OVERFLOW; }
    srmech_json_value_t *manifest = NULL;
    srmech_status_t st = srmech_json_parse(manbuf, mlen, pws, pws_len, &manifest);
    if (st != SRMECH_OK) { return st; }
    const srmech_json_value_t *ld = genome_data_get(manifest, "leaf_dim");
    const srmech_json_value_t *carr = genome_data_get(manifest, "chromosomes");
    if (ld == NULL || ld->type != SRMECH_JSON_INT ||
        (uint32_t)ld->u.i != leaf_dim || carr == NULL ||
        carr->type != SRMECH_JSON_ARRAY) { return SRMECH_ERR_BAD_INPUT; }
    uint32_t n_old = carr->u.arr.n;
    genome_strings_t s;
    st = genome_strings_alloc(&s, a, n_old + 1u);
    if (st != SRMECH_OK) { return st; }
    st = genome_append_fill(&s, manifest, n_old, label, region, region_len,
                            leaf_dim, old_len);
    if (st != SRMECH_OK) { return st; }
    size_t man_cap = genome_manifest_cap(s.n_chroms);
    char *manifest_out = genome_arena_alloc(a, man_cap + 1u);
    if (manifest_out == NULL) { return SRMECH_ERR_OVERFLOW; }
    void *tws = NULL;
    size_t tws_len = 0u;
    genome_arena_tail(a, &tws, &tws_len);
    size_t out_len = 0u;
    st = genome_build_manifest(&s, leaf_dim, old_len + region_len, tws, tws_len,
                               manifest_out, man_cap, &out_len);
    if (st != SRMECH_OK) { return st; }
    manifest_out[out_len] = '\n';
    char body_path[SRMECH_GENOME_PATH_MAX];
    char man_path[SRMECH_GENOME_PATH_MAX];
    st = genome_join(dir, SRMECH_GENOME_BODY, body_path, sizeof(body_path));
    if (st != SRMECH_OK) { return st; }
    st = genome_join(dir, SRMECH_GENOME_MANIFEST, man_path, sizeof(man_path));
    if (st != SRMECH_OK) { return st; }
    st = genome_write_file(body_path, "ab", region, region_len);   /* tail-extend */
    if (st != SRMECH_OK) { return st; }
    return genome_write_file(man_path, "wb",
                             (const unsigned char *)manifest_out, out_len + 1u);
}

/* v2/v3 (or manifest-less) MIGRATION: read the old body, append the region, and
 * SAVE the grown body (a full rebuild → v4, once). The one-time cost of moving a
 * legacy genome to the region-partitioned v4 format; subsequent appends are O(1).*/
static srmech_status_t genome_append_migrate(const char *dir, const char *label,
    const unsigned char *region, size_t region_len, uint32_t leaf_dim,
    const unsigned char *the_one, size_t the_one_len, genome_arena_t *a)
{
    assert(dir != NULL && label != NULL && the_one != NULL && a != NULL);
    assert(region != NULL || region_len == 0u);
    size_t bcap = 0u;
    srmech_status_t st = genome_body_size(dir, &bcap);
    if (st != SRMECH_OK) { return st; }
    bcap += region_len;
    unsigned char *body = genome_arena_alloc(a, (bcap == 0u) ? 1u : bcap);
    if (body == NULL) { return SRMECH_ERR_OVERFLOW; }
    void *tws = NULL;
    size_t tws_len = 0u;
    genome_arena_tail(a, &tws, &tws_len);
    srmech_json_value_t *manifest = NULL;
    st = genome_obtain_manifest(dir, the_one, the_one_len, tws, tws_len, &manifest);
    if (st != SRMECH_OK) { return st; }
    const srmech_json_value_t *ld = genome_data_get(manifest, "leaf_dim");
    if (ld == NULL || ld->type != SRMECH_JSON_INT ||
        (uint32_t)ld->u.i != leaf_dim) { return SRMECH_ERR_BAD_INPUT; }
    st = genome_check_new_label(manifest, label);
    if (st != SRMECH_OK) { return st; }
    size_t new_len = 0u;
    st = genome_grow_body(dir, manifest, region, region_len, body, bcap, &new_len);
    if (st != SRMECH_OK) { return st; }
    return srmech_genome_save(dir, body, new_len, leaf_dim, the_one, the_one_len,
                              tws, tws_len);
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
    if (leaf_dim == 0u || the_one_len != (size_t)leaf_dim || region_len == 0u ||
        strlen(label) + 1u > SRMECH_GENOME_MAX_LABEL) {
        return SRMECH_ERR_BAD_INPUT;
    }
    genome_arena_t a;
    genome_arena_init(&a, ws, ws_len);
    /* §56 (rc115 #1245(b)): read the OLD body size (cheap stat — we never read
     * the body) + the manifest.json bytes. A v4 manifest (regions present) takes
     * the O(1) tail-extend path; a legacy v2/v3 (or manifest-less) genome migrates
     * once via a full rebuild. */
    size_t old_len = 0u;
    srmech_status_t st = genome_body_size(dir, &old_len);
    if (st != SRMECH_OK) { return st; }
    char man_path[SRMECH_GENOME_PATH_MAX];
    st = genome_join(dir, SRMECH_GENOME_MANIFEST, man_path, sizeof(man_path));
    if (st != SRMECH_OK) { return st; }
    size_t msz = 0u;
    if (genome_file_size(man_path, &msz) != SRMECH_OK) {   /* manifest-less */
        return genome_append_migrate(dir, label, region, region_len, leaf_dim,
                                     the_one, the_one_len, &a);
    }
    char *manbuf = genome_arena_alloc(&a, msz + 1u);
    if (manbuf == NULL) { return SRMECH_ERR_OVERFLOW; }
    size_t mlen = 0u;
    st = genome_read_file(man_path, (unsigned char *)manbuf, msz + 1u, &mlen);
    if (st != SRMECH_OK) { return st; }
    while (mlen > 0u && (manbuf[mlen - 1u] == '\n' || manbuf[mlen - 1u] == '\r')) {
        mlen--;
    }
    /* A v4 manifest carries "regions"; a legacy one does not. Sniff cheaply by a
     * substring probe on the canonical text (the key is always double-quoted). */
    if (!genome_bytes_contains(manbuf, mlen, "\"regions\":", 10u)) {
        genome_arena_init(&a, ws, ws_len);      /* migrate re-reads the body itself */
        return genome_append_migrate(dir, label, region, region_len, leaf_dim,
                                     the_one, the_one_len, &a);
    }
    return genome_append_v4(dir, label, region, region_len, leaf_dim, &a,
                            manbuf, msz, mlen, old_len);
}

/* ------------------------------------------------------------------ *
 * §45 IN-PLACE EDIT — remove / replace one chromosome by a BYTE splice.
 *
 * Biology excises; it does not re-synthesize. With the §44 self-describing
 * body an edit is a pure byte-level splice on turns.bin — no kernel is decoded
 * or re-coupled, so the surviving chromosomes' coupled bytes stay byte-identical
 * (only relocated). The spliced body is committed via srmech_genome_save, which
 * re-derives the manifest by scanning it (the strand is the SSoT), so the
 * on-disk turns.bin + manifest.json are byte-identical to the Python
 * genome_remove / genome_replace output. Like APPEND (a write op) the_one is
 * REQUIRED here (srmech_genome_save needs it for the manifest the_one hash+hex);
 * the_one_len IS leaf_dim. The whole body is bound-checked against body_sha256
 * BEFORE the edit (genome_read_bound_body).
 * ------------------------------------------------------------------ */

srmech_status_t srmech_genome_remove(const char *dir, const char *label,
                                     const unsigned char *the_one,
                                     size_t the_one_len, void *ws, size_t ws_len)
{
    assert(the_one != NULL || the_one_len == 0u);
    assert(dir != NULL || label == NULL);
    if (dir == NULL || label == NULL || the_one == NULL || ws == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (the_one_len == 0u || the_one_len > 256u) { return SRMECH_ERR_BAD_INPUT; }
    genome_arena_t a;
    genome_arena_init(&a, ws, ws_len);
    size_t bcap = 0u;
    srmech_status_t st = genome_body_size(dir, &bcap);
    if (st != SRMECH_OK) { return st; }
    unsigned char *body = genome_arena_alloc(&a, (bcap == 0u) ? 1u : bcap);
    if (body == NULL) { return SRMECH_ERR_OVERFLOW; }
    void *tws = NULL;
    size_t tws_len = 0u;
    genome_arena_tail(&a, &tws, &tws_len);
    srmech_json_value_t *manifest = NULL;
    st = genome_obtain_manifest(dir, the_one, the_one_len, tws, tws_len,
                                &manifest);
    if (st != SRMECH_OK) { return st; }
    const srmech_json_value_t *ld = genome_data_get(manifest, "leaf_dim");
    const srmech_json_value_t *arr = genome_data_get(manifest, "chromosomes");
    if (ld == NULL || ld->type != SRMECH_JSON_INT ||
        (size_t)ld->u.i != the_one_len ||
        arr == NULL || arr->type != SRMECH_JSON_ARRAY) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (arr->u.arr.n <= 1u) { return SRMECH_ERR_BAD_INPUT; }   /* the only chrom */
    size_t off = 0u, len = 0u;
    if (genome_find_chrom(manifest, label, &off, &len) == NULL) {
        return SRMECH_ERR_BAD_INPUT;                           /* label absent */
    }
    size_t body_len = 0u;
    st = genome_read_bound_body(dir, manifest, body, bcap, &body_len);
    if (st != SRMECH_OK) { return st; }
    /* splice [off, off+len) out IN PLACE: slide the tail down over the span. */
    memmove(body + off, body + off + len, body_len - off - len);
    return srmech_genome_save(dir, body, body_len - len,
                              (uint32_t)the_one_len, the_one, the_one_len,
                              tws, tws_len);
}

srmech_status_t srmech_genome_replace(const char *dir, const char *label,
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
    if (leaf_dim == 0u || the_one_len != (size_t)leaf_dim) {
        return SRMECH_ERR_BAD_INPUT;   /* §55/v3: blocks are variable-width —
                                        * the save's scan validates the region */
    }
    genome_arena_t a;
    genome_arena_init(&a, ws, ws_len);
    size_t bcap = 0u;
    srmech_status_t st = genome_body_size(dir, &bcap);
    if (st != SRMECH_OK) { return st; }
    bcap += region_len;                       /* new region may exceed the old */
    unsigned char *body = genome_arena_alloc(&a, (bcap == 0u) ? 1u : bcap);
    if (body == NULL) { return SRMECH_ERR_OVERFLOW; }
    void *tws = NULL;
    size_t tws_len = 0u;
    genome_arena_tail(&a, &tws, &tws_len);
    srmech_json_value_t *manifest = NULL;
    st = genome_obtain_manifest(dir, the_one, the_one_len, tws, tws_len,
                                &manifest);
    if (st != SRMECH_OK) { return st; }
    const srmech_json_value_t *ld = genome_data_get(manifest, "leaf_dim");
    if (ld == NULL || ld->type != SRMECH_JSON_INT ||
        (uint32_t)ld->u.i != leaf_dim) { return SRMECH_ERR_BAD_INPUT; }
    size_t off = 0u, len = 0u;
    if (genome_find_chrom(manifest, label, &off, &len) == NULL) {
        return SRMECH_ERR_BAD_INPUT;                           /* label absent */
    }
    size_t body_len = 0u;
    st = genome_read_bound_body(dir, manifest, body, bcap, &body_len);
    if (st != SRMECH_OK) { return st; }
    size_t tail = body_len - off - len;
    size_t new_len = body_len - len + region_len;
    /* splice old span out + new region in, IN PLACE: shift the tail to its new
     * home, then write the (external) region into the gap. */
    memmove(body + off + region_len, body + off + len, tail);
    if (region_len != 0u) { memcpy(body + off, region, region_len); }
    return srmech_genome_save(dir, body, new_len, leaf_dim,
                              the_one, the_one_len, tws, tws_len);
}

/* ------------------------------------------------------------------ *
 * §43 FILE-MANAGEMENT — the chromosome as a bundleable .chr file.
 *
 * Now that §44 made the strand self-describing and §45 made it editable in
 * place, a chromosome can be EXPORTED as ONE self-contained, content-addressed
 * file (genome_export -> .chr), shipped, and re-IMPORTED into a genome
 * (genome_import) self-verifying — the "tar one chromosome, ship it" goal.
 *
 * A .chr is ONE MPR record (the SAME json builder + writer the manifest uses,
 * so it is BYTE-IDENTICAL to the Python genome_export's json.dumps(sort_keys=
 * True, ensure_ascii=False) + LF): its `data` carries the chromosome's region
 * (CHROM cap + coupled turns) hex + the_one hex; its attestation.response_sha256
 * IS the region hash, so an import re-hashes the region and self-verifies. This
 * COMPOSES the §41 MPR surface — it is NOT a parallel attestation.
 *
 * Mirrors srmech.amsc.genome genome_export / genome_import.
 * ------------------------------------------------------------------ */

/* The §43 .chr data_schema_id (== GENOME_CHR_SCHEMA_ID). */
#define SRMECH_GENOME_CHR_SCHEMA_ID "srmech://schema/genome_chromosome/v1"
/* The §43 parser_rule_hash pre-image (== f"genome_chromosome/v11" — tracks
 * SRMECH_GENOME_FORMAT_VERSION, mirroring the Python _chr_record; §132/rc132 v10->v11). */
#define SRMECH_GENOME_CHR_RULE_PREIMAGE "genome_chromosome/v11"
/* The §43 rendering "purpose" — VERBATIM from genome.py _chr_record
 * (single-line #define; JPL Rule 8 forbids backslash line-continuation). */
#define SRMECH_GENOME_CHR_PURPOSE "One self-contained, MPR-attested chromosome: its fixed-width region (CHROM cap + coupled turns) + the_one, re-importable self-verifying."
/* The §43 rendering "cite_as" (the U+00A7 § is the 2-byte UTF-8 0xC2 0xA7,
 * emitted ensure_ascii=False; the "" breaks the \x hex escape before "43"). */
#define SRMECH_GENOME_CHR_CITE_AS "srmech genome chromosome bundle (UPSTREAM \xc2\xa7""43)"

/* §43 .chr scratch — the region bytes, the region hex, and the .chr file text —
 * are all carved from the caller arena (sized to the chromosome / .chr file), so
 * the only bound is the caller's RAM (no compiled-in 1 MiB cap). The region buf
 * is carved SEPARATE from the body buf so an import APPEND can grow the dest body
 * without a collision; the hex is held BY REFERENCE during srmech_json_write. */

/* Stable string storage for one .chr build (held BY REFERENCE by the JSON
 * builder; must outlive srmech_json_write). The region hex is arena-carved. */
typedef struct {
    char     label[SRMECH_GENOME_MAX_LABEL];
    char     cap_sha[65];
    char     one_sha[65];
    char     one_hex[2 * 256 + 1];
    char     region_sha[65];
    char     parser_version[16 + sizeof(SRMECH_VERSION)];
    char     rule_hash[65];
    char     descr_hash[65];
    char     name[40 + SRMECH_GENOME_MAX_LABEL]; /* "srmech chromosome bundle (" + label + ")" */
    uint32_t leaf_dim;
    int64_t  leaf_count;
} genome_chr_strings_t;

/* new_string from a NUL-terminated C string (strlen length). */
static srmech_json_value_t *genome_jstr(srmech_json_builder_t *b, const char *s)
{
    assert(b != NULL);
    assert(s != NULL);
    return srmech_json_new_string(b, s, (uint32_t)strlen(s));
}

/* Find the chromosome OBJECT node with `label` (NULL if absent / malformed). */
static const srmech_json_value_t *genome_find_chrom_obj(
    const srmech_json_value_t *manifest, const char *label)
{
    assert(manifest != NULL && label != NULL);
    assert(label[0] != '\0');
    const srmech_json_value_t *arr = genome_data_get(manifest, "chromosomes");
    if (arr == NULL || arr->type != SRMECH_JSON_ARRAY) { return NULL; }
    size_t ll = strlen(label);
    for (uint32_t i = 0; i < arr->u.arr.n; i++) {
        const srmech_json_value_t *c = arr->u.arr.items[i];
        const srmech_json_value_t *lv = srmech_json_object_get(c, "label");
        if (lv != NULL && lv->type == SRMECH_JSON_STRING &&
            lv->u.str.len == (uint32_t)ll &&
            memcmp(lv->u.str.ptr, label, ll) == 0) {
            return c;
        }
    }
    return NULL;
}

/* Build a {"sha256":..,"hex":..} sub-object (the_one / region). */
static srmech_json_value_t *genome_chr_subobj(srmech_json_builder_t *b,
                                              const char *sha, const char *hex)
{
    assert(b != NULL && sha != NULL && hex != NULL);
    assert(sha[0] != '\0');
    const char *keys[2] = { "sha256", "hex" };
    srmech_json_value_t *v[2];
    v[0] = genome_jstr(b, sha);
    v[1] = genome_jstr(b, hex);
    return srmech_json_new_object(b, keys, v, 2u);
}

/* Build the .chr "data" block (7 keys; key order matches genome.py _chr_data —
 * the writer sorts, so order is cosmetic). */
static srmech_json_value_t *genome_chr_build_data(srmech_json_builder_t *b,
                                                  const genome_chr_strings_t *cs,
                                                  const char *region_hex)
{
    assert(b != NULL && cs != NULL && region_hex != NULL);
    assert(cs->cap_sha[0] != '\0');
    const char *keys[7] = { "format_version", "leaf_dim", "label", "leaf_count",
                            "cap_sha256", "the_one", "region" };
    srmech_json_value_t *v[7];
    v[0] = srmech_json_new_int(b, (int64_t)SRMECH_GENOME_FORMAT_VERSION);
    v[1] = srmech_json_new_int(b, (int64_t)cs->leaf_dim);
    v[2] = genome_jstr(b, cs->label);
    v[3] = srmech_json_new_int(b, cs->leaf_count);
    v[4] = genome_jstr(b, cs->cap_sha);
    v[5] = genome_chr_subobj(b, cs->one_sha, cs->one_hex);
    v[6] = genome_chr_subobj(b, cs->region_sha, region_hex);
    return srmech_json_new_object(b, keys, v, 7u);
}

/* Build the .chr "attestation" block (9 fields; constants VERBATIM from
 * genome.py _chr_record). response_sha256 IS the region hash. */
static srmech_json_value_t *genome_chr_build_attest(srmech_json_builder_t *b,
                                                    const genome_chr_strings_t *cs)
{
    assert(b != NULL && cs != NULL);
    assert(cs->region_sha[0] != '\0');
    const char *keys[9] = {
        "source_doi", "source_url", "license", "retrieved_at",
        "response_sha256", "parser_version", "parser_rule_hash",
        "collector_descriptor_path", "collector_descriptor_hash" };
    srmech_json_value_t *v[9];
    v[0] = genome_jstr(b, "10.0/srmech.genome.chromosome");
    v[1] = genome_jstr(b, "https://srmech.net/genome/chromosome");
    v[2] = genome_jstr(b, "CC0");
    v[3] = genome_jstr(b, "1970-01-01T00:00:00Z");
    v[4] = genome_jstr(b, cs->region_sha);
    v[5] = genome_jstr(b, cs->parser_version);
    v[6] = genome_jstr(b, cs->rule_hash);
    v[7] = genome_jstr(b, "srmech/amsc/genome.py");
    v[8] = genome_jstr(b, cs->descr_hash);
    return srmech_json_new_object(b, keys, v, 9u);
}

/* Build the .chr "rendering" block (human_readable_name / cite_as / purpose). */
static srmech_json_value_t *genome_chr_build_render(srmech_json_builder_t *b,
                                                    const genome_chr_strings_t *cs)
{
    assert(b != NULL && cs != NULL);
    assert(cs->name[0] != '\0');
    const char *keys[3] = { "human_readable_name", "cite_as", "purpose" };
    srmech_json_value_t *v[3];
    v[0] = genome_jstr(b, cs->name);
    v[1] = genome_jstr(b, SRMECH_GENOME_CHR_CITE_AS);
    v[2] = genome_jstr(b, SRMECH_GENOME_CHR_PURPOSE);
    return srmech_json_new_object(b, keys, v, 3u);
}

/* Build the whole .chr MPRRecord tree in `ws` and serialise it into `out`
 * (capacity out_cap); *out_len gets the byte count (no trailing LF — the
 * caller appends it, like genome_build_manifest). */
static srmech_status_t genome_chr_build_file(const genome_chr_strings_t *cs,
                                             const char *region_hex,
                                             void *ws, size_t ws_len,
                                             char *out, size_t out_cap,
                                             size_t *out_len)
{
    assert(cs != NULL && region_hex != NULL);
    assert(out != NULL && out_len != NULL && ws != NULL);
    srmech_json_builder_t b;
    srmech_status_t st = srmech_json_builder_init(&b, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    const char *keys[5] = { "mpr_version", "data", "data_schema_id",
                            "attestation", "rendering" };
    srmech_json_value_t *v[5];
    v[0] = genome_jstr(&b, "1.0");
    v[1] = genome_chr_build_data(&b, cs, region_hex);
    v[2] = genome_jstr(&b, SRMECH_GENOME_CHR_SCHEMA_ID);
    v[3] = genome_chr_build_attest(&b, cs);
    v[4] = genome_chr_build_render(&b, cs);
    srmech_json_value_t *root = srmech_json_new_object(&b, keys, v, 5u);
    if (b.failed || root == NULL) { return SRMECH_ERR_OVERFLOW; }
    /* The writer's key-sort scratch comes from the builder's untouched
     * arena tail (no compiled-in object-width cap). */
    return srmech_json_write_ws(root, out, out_cap, out_len,
                                b.base + b.used, b.len - b.used);
}

/* Pull one chromosome's export metadata out of the manifest into `cs` and set
 * its byte span (*off, *len) — leaf_dim / label / leaf_count / cap_sha256 from
 * the chromosome entry, the_one sha256+hex from the manifest (the .chr re-uses
 * the manifest's the_one verbatim). SRMECH_ERR_BAD_INPUT on absent / malformed. */
static srmech_status_t genome_chr_meta(const srmech_json_value_t *manifest,
                                       const char *label, genome_chr_strings_t *cs,
                                       size_t *off, size_t *len)
{
    assert(manifest != NULL && label != NULL);
    assert(cs != NULL && off != NULL && len != NULL);
    const srmech_json_value_t *ld = genome_data_get(manifest, "leaf_dim");
    const srmech_json_value_t *to = genome_data_get(manifest, "the_one");
    if (ld == NULL || ld->type != SRMECH_JSON_INT || ld->u.i <= 0 ||
        ld->u.i > 256 || to == NULL || to->type != SRMECH_JSON_OBJECT) {
        return SRMECH_ERR_BAD_INPUT;
    }
    const srmech_json_value_t *c = genome_find_chrom_obj(manifest, label);
    if (c == NULL) { return SRMECH_ERR_BAD_INPUT; }       /* label not present */
    const srmech_json_value_t *bo = srmech_json_object_get(c, "byte_offset");
    const srmech_json_value_t *bl = srmech_json_object_get(c, "byte_len");
    const srmech_json_value_t *cap = srmech_json_object_get(c, "cap_sha256");
    const srmech_json_value_t *lc = srmech_json_object_get(c, "leaf_count");
    const srmech_json_value_t *ts = srmech_json_object_get(to, "sha256");
    const srmech_json_value_t *th = srmech_json_object_get(to, "hex");
    if (bo == NULL || bo->type != SRMECH_JSON_INT ||
        bl == NULL || bl->type != SRMECH_JSON_INT ||
        cap == NULL || cap->type != SRMECH_JSON_STRING || cap->u.str.len != 64u ||
        lc == NULL || lc->type != SRMECH_JSON_INT ||
        ts == NULL || ts->type != SRMECH_JSON_STRING || ts->u.str.len != 64u ||
        th == NULL || th->type != SRMECH_JSON_STRING || th->u.str.len > 512u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    size_t ll = strlen(label);
    *off = (size_t)bo->u.i;
    *len = (size_t)bl->u.i;
    cs->leaf_dim = (uint32_t)ld->u.i;
    cs->leaf_count = lc->u.i;
    memcpy(cs->cap_sha, cap->u.str.ptr, 64u);  cs->cap_sha[64] = '\0';
    memcpy(cs->label, label, ll);              cs->label[ll] = '\0';
    memcpy(cs->one_sha, ts->u.str.ptr, 64u);   cs->one_sha[64] = '\0';
    memcpy(cs->one_hex, th->u.str.ptr, th->u.str.len);
    cs->one_hex[th->u.str.len] = '\0';
    return SRMECH_OK;
}

/* Fill the .chr's derived constant strings: parser_rule_hash, the descriptor
 * hash, the parser_version, and the human_readable_name (label-substituted). */
static srmech_status_t genome_chr_consts(genome_chr_strings_t *cs)
{
    assert(cs != NULL);
    assert(cs->cap_sha[0] != '\0');
    srmech_status_t st = srmech_sha256_hex(
        (const uint8_t *)SRMECH_GENOME_CHR_RULE_PREIMAGE,
        strlen(SRMECH_GENOME_CHR_RULE_PREIMAGE), cs->rule_hash);
    if (st != SRMECH_OK) { return st; }
    st = srmech_sha256_hex((const uint8_t *)SRMECH_GENOME_CHR_SCHEMA_ID,
                           strlen(SRMECH_GENOME_CHR_SCHEMA_ID), cs->descr_hash);
    if (st != SRMECH_OK) { return st; }
    memcpy(cs->parser_version, "srmech ", 7u);
    memcpy(cs->parser_version + 7u, SRMECH_VERSION, sizeof(SRMECH_VERSION));
    const char *pfx = "srmech chromosome bundle (";
    size_t pl = strlen(pfx), ll = strlen(cs->label);
    memcpy(cs->name, pfx, pl);
    memcpy(cs->name + pl, cs->label, ll);
    cs->name[pl + ll] = ')';
    cs->name[pl + ll + 1u] = '\0';
    return SRMECH_OK;
}

/* Read the chromosome region [off,off+len) from <dir>/turns.bin into `region`
 * (cap == max(len,1)), verify its leading leaf_dim-byte cap block hashes to
 * cs->cap_sha (the _read_region cap-integrity check), fill cs->region_sha, and
 * hex-encode the region bytes into `hex` (cap >= 2*len+1). */
static srmech_status_t genome_chr_read_region(const char *dir,
    genome_chr_strings_t *cs, size_t off, size_t len,
    unsigned char *region, char *hex)
{
    assert(dir != NULL && cs != NULL);
    assert(region != NULL && hex != NULL);
    char body_path[SRMECH_GENOME_PATH_MAX];
    srmech_status_t st = genome_join(dir, SRMECH_GENOME_BODY,
                                     body_path, sizeof(body_path));
    if (st != SRMECH_OK) { return st; }
    st = genome_read_region(body_path, off, len, region, (len == 0u) ? 1u : len);
    if (st != SRMECH_OK) { return st; }
    char capgot[65];
    st = srmech_sha256_hex(region, cs->leaf_dim, capgot);
    if (st != SRMECH_OK) { return st; }
    if (memcmp(capgot, cs->cap_sha, 64u) != 0) { return SRMECH_ERR_BAD_INPUT; }
    st = srmech_sha256_hex(region, len, cs->region_sha);
    if (st != SRMECH_OK) { return st; }
    genome_hex(region, len, hex);
    return SRMECH_OK;
}

srmech_status_t srmech_genome_export(const char *dir, const char *label,
                                     const char *out_path,
                                     const unsigned char *the_one,
                                     size_t the_one_len, void *ws, size_t ws_len)
{
    assert(dir != NULL || ws == NULL);
    assert(the_one != NULL || the_one_len == 0u);
    if (dir == NULL || label == NULL || out_path == NULL || ws == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (the_one != NULL && (the_one_len == 0u || the_one_len > 256u)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    genome_arena_t a;
    genome_arena_init(&a, ws, ws_len);     /* obtain uses the whole arena */
    srmech_json_value_t *manifest = NULL;
    srmech_status_t st = genome_obtain_manifest(dir, the_one, the_one_len,
                                                ws, ws_len, &manifest);
    if (st != SRMECH_OK) { return st; }
    genome_chr_strings_t cs;
    size_t off = 0u, len = 0u;
    st = genome_chr_meta(manifest, label, &cs, &off, &len);   /* copies out tree */
    if (st != SRMECH_OK) { return st; }
    genome_arena_init(&a, ws, ws_len);     /* manifest consumed → reuse arena */
    unsigned char *region = genome_arena_alloc(&a, (len == 0u) ? 1u : len);
    char *hex = genome_arena_alloc(&a, 2u * len + 1u);
    size_t io_cap = 2u * len + 4096u;
    char *io = genome_arena_alloc(&a, io_cap);
    if (region == NULL || hex == NULL || io == NULL) { return SRMECH_ERR_OVERFLOW; }
    st = genome_chr_read_region(dir, &cs, off, len, region, hex);
    if (st != SRMECH_OK) { return st; }
    st = genome_chr_consts(&cs);
    if (st != SRMECH_OK) { return st; }
    void *tw = NULL;
    size_t tl = 0u;
    genome_arena_tail(&a, &tw, &tl);       /* tail for the .chr json tree */
    size_t flen = 0u;
    st = genome_chr_build_file(&cs, hex, tw, tl, io, io_cap - 1u, &flen);
    if (st != SRMECH_OK) { return st; }
    io[flen] = '\n';                       /* trailing LF, like _write_mpr_file */
    return genome_write_file(out_path, "wb",
                             (const unsigned char *)io, flen + 1u);
}

/* Decode `hexlen` lowercase/uppercase hex chars at `hex` into `out` (cap
 * out_cap); *out_len gets the byte count. SRMECH_ERR_BAD_INPUT on an odd length /
 * a non-hex char; OVERFLOW if the decoded bytes exceed out_cap. The per-nibble
 * decode is inlined (a tiny pure-arithmetic step — no separate accessor).
 * Mirrors Python bytes.fromhex. */
static srmech_status_t genome_unhex(const char *hex, size_t hexlen,
                                    unsigned char *out, size_t out_cap,
                                    size_t *out_len)
{
    assert(hex != NULL || hexlen == 0u);
    assert(out != NULL && out_len != NULL);
    if (hexlen % 2u != 0u) { return SRMECH_ERR_BAD_INPUT; }
    size_t n = hexlen / 2u;
    if (n > out_cap) { return SRMECH_ERR_OVERFLOW; }
    for (size_t i = 0; i < n; i++) {
        int v[2];
        for (int k = 0; k < 2; k++) {
            char c = hex[2u * i + (size_t)k];
            if (c >= '0' && c <= '9') { v[k] = c - '0'; }
            else if (c >= 'a' && c <= 'f') { v[k] = c - 'a' + 10; }
            else if (c >= 'A' && c <= 'F') { v[k] = c - 'A' + 10; }
            else { return SRMECH_ERR_BAD_INPUT; }
        }
        out[i] = (unsigned char)((v[0] << 4) | v[1]);
    }
    *out_len = n;
    return SRMECH_OK;
}

/* Decode a .chr {"sha256":..,"hex":..} sub-object's hex into `out`, re-hash the
 * bytes, and SELF-VERIFY the digest against the stored sha256 (a flipped byte is
 * SRMECH_ERR_BAD_INPUT). *out_len gets the byte count; sha_out (>= 65) the hex. */
static srmech_status_t genome_chr_decode_verify(const srmech_json_value_t *sub,
                                                unsigned char *out, size_t out_cap,
                                                size_t *out_len, char *sha_out)
{
    assert(sub != NULL && out != NULL);
    assert(out_len != NULL && sha_out != NULL);
    if (sub->type != SRMECH_JSON_OBJECT) { return SRMECH_ERR_BAD_INPUT; }
    const srmech_json_value_t *hex = srmech_json_object_get(sub, "hex");
    const srmech_json_value_t *sha = srmech_json_object_get(sub, "sha256");
    if (hex == NULL || hex->type != SRMECH_JSON_STRING ||
        sha == NULL || sha->type != SRMECH_JSON_STRING) {
        return SRMECH_ERR_BAD_INPUT;
    }
    srmech_status_t st = genome_unhex(hex->u.str.ptr, hex->u.str.len,
                                      out, out_cap, out_len);
    if (st != SRMECH_OK) { return st; }
    st = srmech_sha256_hex(out, *out_len, sha_out);
    if (st != SRMECH_OK) { return st; }
    return genome_str_eq(sha, sha_out) ? SRMECH_OK : SRMECH_ERR_BAD_INPUT;
}

/* Validate a parsed .chr record and extract its region (decoded + self-verified,
 * incl. attestation.response_sha256 == region.sha256), its the_one (decoded +
 * self-verified, length == leaf_dim), leaf_dim and label. Mirrors the integrity
 * bounds of the Python genome_import (_read_chr + the region/the_one re-hash). */
static srmech_status_t genome_chr_verify_extract(const srmech_json_value_t *rec,
    unsigned char *region, size_t region_cap, size_t *region_len,
    unsigned char *oneblk, size_t *one_len, uint32_t *leaf_dim,
    char *label, size_t label_cap)
{
    assert(rec != NULL && region != NULL && region_len != NULL);
    assert(oneblk != NULL && leaf_dim != NULL && label != NULL);
    const srmech_json_value_t *sid = srmech_json_object_get(rec, "data_schema_id");
    if (sid == NULL || !genome_str_eq(sid, SRMECH_GENOME_CHR_SCHEMA_ID)) {
        return SRMECH_ERR_BAD_INPUT;                  /* not a chromosome bundle */
    }
    const srmech_json_value_t *data = srmech_json_object_get(rec, "data");
    const srmech_json_value_t *att = srmech_json_object_get(rec, "attestation");
    if (data == NULL || data->type != SRMECH_JSON_OBJECT ||
        att == NULL || att->type != SRMECH_JSON_OBJECT) {
        return SRMECH_ERR_BAD_INPUT;
    }
    const srmech_json_value_t *ld = srmech_json_object_get(data, "leaf_dim");
    const srmech_json_value_t *lbl = srmech_json_object_get(data, "label");
    if (ld == NULL || ld->type != SRMECH_JSON_INT || ld->u.i <= 0 || ld->u.i > 256 ||
        lbl == NULL || lbl->type != SRMECH_JSON_STRING ||
        (size_t)lbl->u.str.len + 1u > label_cap) {
        return SRMECH_ERR_BAD_INPUT;
    }
    *leaf_dim = (uint32_t)ld->u.i;
    memcpy(label, lbl->u.str.ptr, lbl->u.str.len);
    label[lbl->u.str.len] = '\0';
    char rsha[65];
    srmech_status_t st = genome_chr_decode_verify(
        srmech_json_object_get(data, "region"), region, region_cap, region_len, rsha);
    if (st != SRMECH_OK) { return st; }
    const srmech_json_value_t *resp = srmech_json_object_get(att, "response_sha256");
    if (resp == NULL || !genome_str_eq(resp, rsha)) { return SRMECH_ERR_BAD_INPUT; }
    char osha[65];
    st = genome_chr_decode_verify(srmech_json_object_get(data, "the_one"),
                                  oneblk, 256u, one_len, osha);
    if (st != SRMECH_OK) { return st; }
    return (*one_len == (size_t)*leaf_dim) ? SRMECH_OK : SRMECH_ERR_BAD_INPUT;
}

/* Does <dir>/turns.bin exist? (the SEED-vs-APPEND discriminator). */
static int genome_body_exists(const char *dir)
{
    assert(dir != NULL);
    char body_path[SRMECH_GENOME_PATH_MAX];
    srmech_status_t st = genome_join(dir, SRMECH_GENOME_BODY,
                                     body_path, sizeof(body_path));
    assert(st == SRMECH_OK || st == SRMECH_ERR_OVERFLOW);
    if (st != SRMECH_OK) { return 0; }
    size_t sz = 0u;   /* rc162: existence probe through the PAL, no raw fopen */
    return (srmech_plat_file_size(body_path, &sz) == SRMECH_OK) ? 1 : 0;
}

/* APPEND a verified .chr region into an existing dest genome: same coupling
 * invariant (dest the_one.sha256 == the .chr's) + a fresh label, then grow the
 * body byte-for-byte and re-save. `caller_one` is the rebuild width for a
 * manifest-less dest (else the .chr's own the_one). Mirrors genome_import's
 * APPEND branch. */
static srmech_status_t genome_chr_append(const char *dest, const char *label,
    const unsigned char *region, size_t region_len, uint32_t leaf_dim,
    const unsigned char *one, size_t one_len,
    const unsigned char *caller_one, size_t caller_one_len,
    void *ws, size_t ws_len)
{
    assert(dest != NULL && label != NULL && one != NULL);
    assert(region != NULL || region_len == 0u);
    const unsigned char *rb = (caller_one != NULL) ? caller_one : one;
    size_t rb_len = (caller_one != NULL) ? caller_one_len : one_len;
    genome_arena_t a;
    genome_arena_init(&a, ws, ws_len);
    size_t bcap = 0u;
    srmech_status_t st = genome_body_size(dest, &bcap);
    if (st != SRMECH_OK) { return st; }
    bcap += region_len;
    unsigned char *body = genome_arena_alloc(&a, (bcap == 0u) ? 1u : bcap);
    if (body == NULL) { return SRMECH_ERR_OVERFLOW; }
    void *tws = NULL;
    size_t tws_len = 0u;
    genome_arena_tail(&a, &tws, &tws_len);
    srmech_json_value_t *manifest = NULL;
    st = genome_obtain_manifest(dest, rb, rb_len, tws, tws_len, &manifest);
    if (st != SRMECH_OK) { return st; }
    const srmech_json_value_t *ld = genome_data_get(manifest, "leaf_dim");
    if (ld == NULL || ld->type != SRMECH_JSON_INT ||
        (uint32_t)ld->u.i != leaf_dim) { return SRMECH_ERR_BAD_INPUT; }
    const srmech_json_value_t *dto = genome_data_get(manifest, "the_one");
    const srmech_json_value_t *dsha =
        (dto != NULL) ? srmech_json_object_get(dto, "sha256") : NULL;
    char osha[65];
    st = srmech_sha256_hex(one, one_len, osha);
    if (st != SRMECH_OK) { return st; }
    if (dsha == NULL || !genome_str_eq(dsha, osha)) {
        return SRMECH_ERR_BAD_INPUT;             /* coupled to a different the_one */
    }
    st = genome_check_new_label(manifest, label);          /* no dup labels */
    if (st != SRMECH_OK) { return st; }
    size_t new_len = 0u;
    st = genome_grow_body(dest, manifest, region, region_len, body, bcap, &new_len);
    if (st != SRMECH_OK) { return st; }
    return srmech_genome_save(dest, body, new_len, leaf_dim,
                              one, one_len, tws, tws_len);
}

srmech_status_t srmech_genome_import(const char *chr_path, const char *dest,
                                     const unsigned char *the_one,
                                     size_t the_one_len, void *ws, size_t ws_len)
{
    assert(dest != NULL || ws == NULL);
    assert(the_one != NULL || the_one_len == 0u);
    if (chr_path == NULL || dest == NULL || ws == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (the_one != NULL && (the_one_len == 0u || the_one_len > 256u)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    genome_arena_t a;
    genome_arena_init(&a, ws, ws_len);
    size_t fsz = 0u;
    srmech_status_t st = genome_file_size(chr_path, &fsz);
    if (st != SRMECH_OK) { return st; }
    char *io = genome_arena_alloc(&a, fsz + 1u);
    unsigned char *region = genome_arena_alloc(&a, fsz + 1u);  /* region <= file */
    if (io == NULL || region == NULL) { return SRMECH_ERR_OVERFLOW; }
    size_t tlen = 0u;
    st = genome_read_file(chr_path, (unsigned char *)io, fsz + 1u, &tlen);
    if (st != SRMECH_OK) { return st; }
    while (tlen > 0u && (io[tlen - 1u] == '\n' || io[tlen - 1u] == '\r')) { tlen--; }
    void *pw = NULL;
    size_t pl = 0u;
    genome_arena_tail(&a, &pw, &pl);       /* tail for the parse tree + save */
    srmech_json_value_t *rec = NULL;
    st = srmech_json_parse(io, tlen, pw, pl, &rec);
    if (st != SRMECH_OK) { return st; }
    unsigned char oneblk[256];
    size_t region_len = 0u, one_len = 0u;
    uint32_t leaf_dim = 0u;
    char label[SRMECH_GENOME_MAX_LABEL];
    st = genome_chr_verify_extract(rec, region, fsz + 1u,
                                   &region_len, oneblk, &one_len, &leaf_dim,
                                   label, sizeof(label));
    if (st != SRMECH_OK) { return st; }
    if (!genome_body_exists(dest)) {           /* SEED — region IS the body */
        return srmech_genome_save(dest, region, region_len, leaf_dim,
                                  oneblk, one_len, pw, pl);
    }
    return genome_chr_append(dest, label, region, region_len, leaf_dim,
                             oneblk, one_len, the_one, the_one_len, pw, pl);
}

/* ================================================================== *
 * §43 LOOSE<->PACKED — git's object model for genomes.
 *
 *   explode: packed turns.bin  ->  dir of loose <label>.chr bundles
 *            (like `git unpack-objects`).
 *   pack:    dir of <label>.chr -> one packed genome in CANONICAL
 *            sorted-label order (like `git repack`; content-preserving,
 *            re-canonicalises byte order). Mirrors the Python
 *            genome_explode / genome_pack.
 * ================================================================== */

/* A loose-bundle basename "<label>.chr" needs room for the label + ".chr"
 * + NUL on top of the longest label. */
#define SRMECH_GENOME_CHR_NAME_MAX (SRMECH_GENOME_MAX_LABEL + 8u)

/* Is `label` filename-safe to become "<label>.chr"? (no path separator,
 * not "" / "." / ".."). Mirrors the Python genome_explode guard. */
static int genome_label_filename_safe(const char *label)
{
    assert(label != NULL);
    size_t n = strlen(label);
    assert(n < SRMECH_GENOME_MAX_LABEL);
    if (n == 0u) { return 0; }
    if (strcmp(label, ".") == 0 || strcmp(label, "..") == 0) { return 0; }
    for (size_t i = 0; i < n; i++) {
        if (label[i] == '/' || label[i] == '\\') { return 0; }
    }
    return 1;
}

/* Copy every chromosome label out of a parsed manifest into the stable
 * `labels` array (each must be filename-safe — explode turns it into
 * "<label>.chr"). Done BEFORE any export, because srmech_genome_export
 * REUSES ws (re-obtains the manifest, clobbering this tree). */
static srmech_status_t genome_collect_labels(const srmech_json_value_t *manifest,
    char labels[][SRMECH_GENOME_MAX_LABEL], uint32_t *count)
{
    assert(manifest != NULL && labels != NULL);
    assert(count != NULL);
    const srmech_json_value_t *arr = genome_data_get(manifest, "chromosomes");
    if (arr == NULL || arr->type != SRMECH_JSON_ARRAY) {
        return SRMECH_ERR_BAD_INPUT;
    }
    for (uint32_t i = 0; i < arr->u.arr.n; i++) {
        const srmech_json_value_t *lv =
            srmech_json_object_get(arr->u.arr.items[i], "label");
        if (lv == NULL || lv->type != SRMECH_JSON_STRING ||
            (size_t)lv->u.str.len + 1u > SRMECH_GENOME_MAX_LABEL) {
            return SRMECH_ERR_BAD_INPUT;
        }
        memcpy(labels[i], lv->u.str.ptr, lv->u.str.len);
        labels[i][lv->u.str.len] = '\0';
        if (!genome_label_filename_safe(labels[i])) {
            return SRMECH_ERR_BAD_INPUT;
        }
    }
    *count = arr->u.arr.n;
    return SRMECH_OK;
}

srmech_status_t srmech_genome_explode(const char *dir, const char *out_dir,
                                      const unsigned char *the_one,
                                      size_t the_one_len, void *ws, size_t ws_len)
{
    assert(dir != NULL || ws == NULL);
    assert(the_one != NULL || the_one_len == 0u);
    if (dir == NULL || out_dir == NULL || ws == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (the_one != NULL && (the_one_len == 0u || the_one_len > 256u)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    genome_arena_t a;
    genome_arena_init(&a, ws, ws_len);
    /* pass 1: obtain the manifest to learn the chromosome count. */
    srmech_json_value_t *m0 = NULL;
    srmech_status_t st = genome_obtain_manifest(dir, the_one, the_one_len,
                                                ws, ws_len, &m0);
    if (st != SRMECH_OK) { return st; }
    const srmech_json_value_t *arr = genome_data_get(m0, "chromosomes");
    if (arr == NULL || arr->type != SRMECH_JSON_ARRAY) {
        return SRMECH_ERR_BAD_INPUT;
    }
    uint32_t nch = arr->u.arr.n;
    /* carve the stable labels array (arena FRONT); the re-obtain + the export
     * loop run on the tail past it (export REUSES its ws each iteration). */
    genome_arena_init(&a, ws, ws_len);
    char (*labels)[SRMECH_GENOME_MAX_LABEL] = genome_arena_alloc(
        &a, (size_t)((nch == 0u) ? 1u : nch) * SRMECH_GENOME_MAX_LABEL);
    if (labels == NULL) { return SRMECH_ERR_OVERFLOW; }
    void *ew = NULL;
    size_t el = 0u;
    genome_arena_tail(&a, &ew, &el);
    srmech_json_value_t *manifest = NULL;
    st = genome_obtain_manifest(dir, the_one, the_one_len, ew, el, &manifest);
    if (st != SRMECH_OK) { return st; }
    uint32_t n = 0u;
    st = genome_collect_labels(manifest, labels, &n);    /* before any export */
    if (st != SRMECH_OK) { return st; }
    for (uint32_t i = 0; i < n; i++) {                   /* export reuses ew */
        char name[SRMECH_GENOME_CHR_NAME_MAX];
        size_t ll = strlen(labels[i]);
        memcpy(name, labels[i], ll);
        memcpy(name + ll, ".chr", 5u);                   /* incl NUL */
        char out_path[SRMECH_GENOME_PATH_MAX];
        st = genome_join(out_dir, name, out_path, sizeof(out_path));
        if (st != SRMECH_OK) { return st; }
        st = srmech_genome_export(dir, labels[i], out_path, the_one,
                                  the_one_len, ew, el);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* Does `name` end in ".chr" (with a non-empty label) and fit a loose-bundle
 * basename slot? (the *.chr filter for pack's directory scan). */
static int genome_chr_name_ok(const char *name)
{
    assert(name != NULL);
    size_t len = strlen(name);
    assert(len < SRMECH_GENOME_PATH_MAX);
    if (len < 5u || len + 1u > SRMECH_GENOME_CHR_NAME_MAX) { return 0; }
    return strcmp(name + len - 4u, ".chr") == 0 ? 1 : 0;
}

/* List "*.chr" basenames in `dir` into `names` (cap max_n). Iterates via the
 * PAL directory surface (`srmech_plat_dir_*`) so this file carries no #ifdef
 * — the OS-specific opendir/FindFirstFile lives in srmech_platform.c. A
 * missing/empty dir yields count 0 (not an error — the Python glob simply
 * finds nothing; the caller turns 0 into the "no .chr files" error). The
 * scan is bounded (JPL Rule 2): >max_n matches is OVERFLOW, and a flood of
 * 65536 entries stops. */
static srmech_status_t genome_list_chr(const char *dir,
    char names[][SRMECH_GENOME_CHR_NAME_MAX], uint32_t max_n, uint32_t *count)
{
    assert(dir != NULL && count != NULL);
    assert(names == NULL || max_n > 0u);             /* names==NULL: count-only */
    uint32_t n = 0u;
    srmech_plat_dir_t d;
    srmech_status_t st = srmech_plat_dir_open(dir, &d);
    if (st != SRMECH_OK) { *count = 0u; return SRMECH_OK; }  /* no dir -> none */
    char nm[SRMECH_GENOME_CHR_NAME_MAX];
    int have = 0;
    for (uint32_t guard = 0u; guard < 65536u; guard++) {
        st = srmech_plat_dir_next(&d, nm, sizeof(nm), &have);
        if (st != SRMECH_OK) { srmech_plat_dir_close(&d); return st; }
        if (have == 0) { break; }
        if (genome_chr_name_ok(nm)) {
            if (names != NULL && n >= max_n) {
                srmech_plat_dir_close(&d); return SRMECH_ERR_OVERFLOW;
            }
            if (names != NULL) { memcpy(names[n], nm, strlen(nm) + 1u); }
            n++;
        }
    }
    srmech_plat_dir_close(&d);
    *count = n;
    return SRMECH_OK;
}

/* Read+parse a .chr bundle at `chr_path` and copy its inner data.label out
 * to `label_out` (the canonical-sort key for pack). Carves its read+parse
 * scratch from the caller arena `ws` (sized to the .chr file). */
static srmech_status_t genome_chr_peek_label(const char *chr_path,
    void *ws, size_t ws_len, char *label_out)
{
    assert(chr_path != NULL && label_out != NULL);
    assert(ws != NULL);
    genome_arena_t a;
    genome_arena_init(&a, ws, ws_len);
    size_t fsz = 0u;
    srmech_status_t st = genome_file_size(chr_path, &fsz);
    if (st != SRMECH_OK) { return st; }
    char *io = genome_arena_alloc(&a, fsz + 1u);
    if (io == NULL) { return SRMECH_ERR_OVERFLOW; }
    size_t tlen = 0u;
    st = genome_read_file(chr_path, (unsigned char *)io, fsz + 1u, &tlen);
    if (st != SRMECH_OK) { return st; }
    while (tlen > 0u && (io[tlen - 1u] == '\n' || io[tlen - 1u] == '\r')) { tlen--; }
    void *pw = NULL;
    size_t pl = 0u;
    genome_arena_tail(&a, &pw, &pl);
    srmech_json_value_t *rec = NULL;
    st = srmech_json_parse(io, tlen, pw, pl, &rec);
    if (st != SRMECH_OK) { return st; }
    const srmech_json_value_t *sid =
        srmech_json_object_get(rec, "data_schema_id");
    if (sid == NULL || !genome_str_eq(sid, SRMECH_GENOME_CHR_SCHEMA_ID)) {
        return SRMECH_ERR_BAD_INPUT;                  /* not a chromosome bundle */
    }
    const srmech_json_value_t *data = srmech_json_object_get(rec, "data");
    const srmech_json_value_t *lbl =
        (data != NULL) ? srmech_json_object_get(data, "label") : NULL;
    if (lbl == NULL || lbl->type != SRMECH_JSON_STRING ||
        (size_t)lbl->u.str.len + 1u > SRMECH_GENOME_MAX_LABEL) {
        return SRMECH_ERR_BAD_INPUT;
    }
    memcpy(label_out, lbl->u.str.ptr, lbl->u.str.len);
    label_out[lbl->u.str.len] = '\0';
    return SRMECH_OK;
}

/* Insertion-sort the (label, basename) pairs by label, ascending — the
 * canonical pack order (Python sorts by data.label; labels are unique, so
 * the secondary key never engages). UTF-8 byte order == code-point order,
 * so strcmp agrees with Python's str sort. Bounded by n. */
static void genome_sort_by_label(char labels[][SRMECH_GENOME_MAX_LABEL],
    char names[][SRMECH_GENOME_CHR_NAME_MAX], uint32_t n)
{
    assert(labels != NULL && names != NULL);
    assert(n != 0xFFFFFFFFu);
    for (uint32_t i = 1u; i < n; i++) {
        char lbl[SRMECH_GENOME_MAX_LABEL];
        char nm[SRMECH_GENOME_CHR_NAME_MAX];
        memcpy(lbl, labels[i], sizeof(lbl));
        memcpy(nm, names[i], sizeof(nm));
        uint32_t j = i;
        while (j > 0u && strcmp(labels[j - 1u], lbl) > 0) {
            memcpy(labels[j], labels[j - 1u], sizeof(lbl));
            memcpy(names[j], names[j - 1u], sizeof(nm));
            j--;
        }
        memcpy(labels[j], lbl, sizeof(lbl));
        memcpy(names[j], nm, sizeof(nm));
    }
}

/* Read + verify one loose .chr and copy its region into `body` at *offset —
 * the single-pass concat step (rc115 #1245(b)). The first bundle (is_first) sets
 * the pack's the_one + leaf_dim; each later bundle must match them (one coupling
 * invariant). *offset advances by the region length. */
static srmech_status_t genome_pack_read_chr(const char *loose_dir,
    const char *name, void *ws, size_t ws_len, unsigned char *body,
    size_t body_cap, size_t *offset, unsigned char *pack_one,
    size_t *pack_one_len, uint32_t *leaf_dim, int is_first)
{
    assert(loose_dir != NULL && name != NULL && body != NULL);
    assert(offset != NULL && pack_one != NULL && leaf_dim != NULL);
    char chr_path[SRMECH_GENOME_PATH_MAX];
    srmech_status_t st = genome_join(loose_dir, name, chr_path, sizeof(chr_path));
    if (st != SRMECH_OK) { return st; }
    genome_arena_t a;
    genome_arena_init(&a, ws, ws_len);
    size_t fsz = 0u;
    st = genome_file_size(chr_path, &fsz);
    if (st != SRMECH_OK) { return st; }
    char *io = genome_arena_alloc(&a, fsz + 1u);
    if (io == NULL) { return SRMECH_ERR_OVERFLOW; }
    size_t tlen = 0u;
    st = genome_read_file(chr_path, (unsigned char *)io, fsz + 1u, &tlen);
    if (st != SRMECH_OK) { return st; }
    while (tlen > 0u && (io[tlen - 1u] == '\n' || io[tlen - 1u] == '\r')) { tlen--; }
    void *pw = NULL;
    size_t pl = 0u;
    genome_arena_tail(&a, &pw, &pl);
    srmech_json_value_t *rec = NULL;
    st = srmech_json_parse(io, tlen, pw, pl, &rec);
    if (st != SRMECH_OK) { return st; }
    unsigned char oneblk[256];
    size_t one_len = 0u, rlen = 0u;
    uint32_t ld = 0u;
    char label[SRMECH_GENOME_MAX_LABEL];
    st = genome_chr_verify_extract(rec, body + *offset, body_cap - *offset, &rlen,
                                   oneblk, &one_len, &ld, label, sizeof(label));
    if (st != SRMECH_OK) { return st; }
    if (is_first) {
        *leaf_dim = ld;
        *pack_one_len = one_len;
        memcpy(pack_one, oneblk, one_len);
    } else if (ld != *leaf_dim || one_len != *pack_one_len ||
               memcmp(oneblk, pack_one, one_len) != 0) {
        return SRMECH_ERR_BAD_INPUT;              /* different coupling invariant */
    }
    *offset += rlen;
    return SRMECH_OK;
}

/* Sum the byte sizes of the `n` named .chr files (the concat body upper bound —
 * every region is <= its .chr file). */
static srmech_status_t genome_pack_total(const char *loose_dir,
    char names[][SRMECH_GENOME_CHR_NAME_MAX], uint32_t n, size_t *out)
{
    assert(loose_dir != NULL && names != NULL);
    assert(out != NULL && n != 0xFFFFFFFFu);
    size_t total = 0u;
    for (uint32_t i = 0; i < n; i++) {
        char cp[SRMECH_GENOME_PATH_MAX];
        srmech_status_t st = genome_join(loose_dir, names[i], cp, sizeof(cp));
        if (st != SRMECH_OK) { return st; }
        size_t fsz = 0u;
        st = genome_file_size(cp, &fsz);
        if (st != SRMECH_OK) { return st; }
        total += fsz;
    }
    *out = total;
    return SRMECH_OK;
}

/* Concat every sorted .chr region into ONE body buffer (canonical order) and
 * SAVE the packed genome once — the single-pass compaction core (rc115 #1245(b)).
 * `names` is already sorted by inner label + dedup-checked. */
static srmech_status_t genome_pack_concat_save(const char *loose_dir,
    const char *dest, char names[][SRMECH_GENOME_CHR_NAME_MAX], uint32_t n,
    void *tw, size_t tl)
{
    assert(loose_dir != NULL && dest != NULL && names != NULL);
    assert(tw != NULL && n != 0u);
    size_t total = 0u;
    srmech_status_t st = genome_pack_total(loose_dir, names, n, &total);
    if (st != SRMECH_OK) { return st; }
    genome_arena_t a2;
    genome_arena_init(&a2, tw, tl);
    unsigned char *body = genome_arena_alloc(&a2, (total == 0u) ? 1u : total);
    if (body == NULL) { return SRMECH_ERR_OVERFLOW; }
    void *scr = NULL;
    size_t scrl = 0u;
    genome_arena_tail(&a2, &scr, &scrl);      /* per-.chr scratch + the save */
    unsigned char pack_one[256];
    size_t pack_one_len = 0u, offset = 0u;
    uint32_t leaf_dim = 0u;
    for (uint32_t i = 0; i < n; i++) {
        st = genome_pack_read_chr(loose_dir, names[i], scr, scrl, body, total,
                                  &offset, pack_one, &pack_one_len, &leaf_dim,
                                  (i == 0u));
        if (st != SRMECH_OK) { return st; }
    }
    return srmech_genome_save(dest, body, offset, leaf_dim, pack_one,
                              pack_one_len, scr, scrl);
}

srmech_status_t srmech_genome_pack(const char *loose_dir, const char *dest,
                                   const unsigned char *the_one,
                                   size_t the_one_len, void *ws, size_t ws_len)
{
    assert(loose_dir != NULL || ws == NULL);
    assert(the_one != NULL || the_one_len == 0u);
    if (loose_dir == NULL || dest == NULL || ws == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (the_one != NULL && (the_one_len == 0u || the_one_len > 256u)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    uint32_t nfiles = 0u;
    srmech_status_t st = genome_list_chr(loose_dir, NULL, 0u, &nfiles); /* count */
    if (st != SRMECH_OK) { return st; }
    if (nfiles == 0u) { return SRMECH_ERR_BAD_INPUT; }   /* no .chr files */
    genome_arena_t a;
    genome_arena_init(&a, ws, ws_len);
    char (*names)[SRMECH_GENOME_CHR_NAME_MAX] = genome_arena_alloc(
        &a, (size_t)nfiles * SRMECH_GENOME_CHR_NAME_MAX);
    char (*labels)[SRMECH_GENOME_MAX_LABEL] = genome_arena_alloc(
        &a, (size_t)nfiles * SRMECH_GENOME_MAX_LABEL);
    if (names == NULL || labels == NULL) { return SRMECH_ERR_OVERFLOW; }
    void *tw = NULL;
    size_t tl = 0u;
    genome_arena_tail(&a, &tw, &tl);          /* tail for peek + concat + save */
    uint32_t n = 0u;
    st = genome_list_chr(loose_dir, names, nfiles, &n);  /* fill names */
    if (st != SRMECH_OK) { return st; }
    if (n == 0u) { return SRMECH_ERR_BAD_INPUT; }
    for (uint32_t i = 0; i < n; i++) {                   /* peek inner labels */
        char chr_path[SRMECH_GENOME_PATH_MAX];
        st = genome_join(loose_dir, names[i], chr_path, sizeof(chr_path));
        if (st != SRMECH_OK) { return st; }
        st = genome_chr_peek_label(chr_path, tw, tl, labels[i]);
        if (st != SRMECH_OK) { return st; }
    }
    genome_sort_by_label(labels, names, n);              /* canonical order */
    for (uint32_t i = 1u; i < n; i++) {                  /* reject duplicate labels */
        if (strcmp(labels[i], labels[i - 1u]) == 0) { return SRMECH_ERR_BAD_INPUT; }
    }
    return genome_pack_concat_save(loose_dir, dest, names, n, tw, tl);
}
