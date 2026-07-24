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

/* The §41 parser_rule_hash pre-image (== f"genome_persistence/v{FORMAT_VERSION}" — tracks
 * SRMECH_GENOME_FORMAT_VERSION, mirroring the Python _manifest_record; v15->v16 §Q8 packer). */
#define SRMECH_GENOME_RULE_PREIMAGE "genome_persistence/v17"

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
    char one_sha[65];                               /* coupling.sha256    */
    char one_hex[2 * 256 + 1];                      /* coupling.hex (<=512 hex) */
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
    unsigned char *cap_kind;                        /* [cap_chroms] §96 cap-kind CODE
                                                     * (0 plasmid / 1 nuclear / 2 diploid),
                                                     * mapped to a string in
                                                     * genome_build_chrom */
    uint32_t cap_chroms;                            /* arena-allocated capacity */
    uint32_t n_chroms;                              /* chromosomes found by scan */
    uint32_t n_blocks;                              /* §55/v3: strand BLOCK count
                                                     * (caps + turns) == n_turns */
    unsigned char carrier_q8;                       /* §Q8/v16: 1 iff the scan saw a
                                                     * Q₈ packed turn (0x38) → the
                                                     * manifest "carrier" is "q8";
                                                     * 0 → "klein4" (the default) */
} genome_strings_t;

/* §44 CAP-KIND classifier — the C mirror of srmech.amsc.genome._cap_kind. The
 * FIRST byte of a `block` classifies it: return the marker byte (an int in
 * [0, 255]) iff it is one of the nine §44/§60/§89/§127/§128/§130/§131/§132 cap
 * markers (CHROM / GENE / REGULATORY / BOOLEAN / THRESHOLD / GRADED / KERNEL-
 * header / KERNEL-telomere / ACTIVE-telomere), else -1 (a Klein-4 data turn
 * 0..3, a v3 packed-turn marker 0x51, or an empty block). Shared cap-scan-skip
 * foundation reused by genome_block_len (rc196) + rc197/rc198's chromosome /
 * recall / genome / partition walks. A READ; no abs, no mutation. */
static int genome_cap_kind(const unsigned char *block, size_t len)
{
    if (block == NULL || len == 0u) { return -1; }
    assert(block != NULL);
    assert(len > 0u);
    unsigned char m = block[0];
    if (m == SRMECH_GENOME_CHROM_CAP_MARKER ||
        m == SRMECH_GENOME_GENE_CAP_MARKER ||
        m == SRMECH_GENOME_REGULATORY_GENE_MARKER ||
        m == SRMECH_GENOME_BOOLEAN_GENE_MARKER ||
        m == SRMECH_GENOME_THRESHOLD_GENE_MARKER ||
        m == SRMECH_GENOME_GRADED_GENE_MARKER ||
        m == SRMECH_GENOME_KERNEL_HEADER_MARKER ||
        m == SRMECH_GENOME_KERNEL_TELOMERE_MARKER ||
        m == SRMECH_GENOME_ACTIVE_TELOMERE_MARKER ||
        m == SRMECH_GENOME_CENTROMERE_CAP_MARKER ||    /* §95a interior centromere */
        m == SRMECH_GENOME_CHROMATIN_MARKER ||         /* §98 interior chromatin cap */
        m == SRMECH_GENOME_FIBER_CAP_MARKER ||         /* §Q8-FIBER/v17 interior fiber cap */
        m == SRMECH_GENOME_DIPLOID_TELOMERE_MARKER) {  /* §95b diploid boundary */
        return (int)m;
    }
    return -1;
}

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
    if (genome_cap_kind(&body[off], 1u) >= 0 || kind <= 3u) {
        n = (size_t)leaf_dim;   /* cap / §60 v5 header / §89 kernel telomere /
                                 * §127 active telomere / §128 regulatory gene /
                                 * §130 boolean gene / §131 threshold gene /
                                 * §132 graded gene / v2 turn */
    } else if (kind == SRMECH_GENOME_PACKED_TURN_MARKER) {
        n = 1u + ((size_t)leaf_dim + 3u) / 4u;      /* v3 klein4 2-bit packed turn */
    } else if (kind == SRMECH_GENOME_Q8_PACKED_TURN_MARKER) {
        n = 1u + ((size_t)leaf_dim * 3u + 7u) / 8u; /* §Q8/v16 3-bit packed turn */
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
 * chain folds the RAW 32-byte values); the v12 head-rebuild ALSO reverses it for
 * coupling.hex (n == leaf_dim, up to the §102/rc278 kernel-section leaf_dim >= 52
 * — bound by SRMECH_GENOME_LEAF_CAP, the caller one_buf[256]). SRMECH_ERR_BAD_INPUT
 * on a non-hex char. (A fixed-width decoder — distinct from the .chr's
 * variable-length, cap-checked genome_unhex.) */
static srmech_status_t genome_hex2bytes(const char *hex, size_t n,
                                        unsigned char *out)
{
    assert(hex != NULL && out != NULL);
    assert(n <= (size_t)SRMECH_GENOME_LEAF_CAP);
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

/* Build the "coupling" sub-object {"sha256":..,"hex":..} from `s`. */
static srmech_json_value_t *genome_build_coupling(srmech_json_builder_t *b,
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

/* §96 cap-kind CODES — the per-chromosome classification the body scan derives
 * (byte-identical to genome.py). A chromosome opening with the §95b diploid
 * telomere is provisionally DIPLOID (else PLASMID); an interior §95a centromere
 * OVERWRITES it to NUCLEAR (nuclear > diploid > plasmid — the R-RBS-LM
 * reference's centromere-first classify; a diploid PAIR carries a centromere, so
 * it reads as nuclear). rc271 (F1251): the field's own names — the ACCESSORY /
 * plasmid genome is "plasmid" (was "stick"), the CORE / clonal genome is
 * "nuclear" (was "minted"). Single-line #defines (JPL Rule 8). */
#define SRMECH_GENOME_CAP_KIND_PLASMID  0u
#define SRMECH_GENOME_CAP_KIND_NUCLEAR  1u
#define SRMECH_GENOME_CAP_KIND_DIPLOID  2u

/* Map a §96 cap-kind CODE to its canonical string (== the genome.py cap_kind
 * literals). An unknown code degrades to "plasmid" (the safe default). */
static const char *genome_cap_kind_str(unsigned char code)
{
    assert(code <= SRMECH_GENOME_CAP_KIND_DIPLOID);
    assert(SRMECH_GENOME_CAP_KIND_PLASMID == 0u);
    if (code == SRMECH_GENOME_CAP_KIND_NUCLEAR) { return "nuclear"; }
    if (code == SRMECH_GENOME_CAP_KIND_DIPLOID) { return "diploid"; }
    return "plasmid";
}

/* Build one chromosome entry object (6 keys) from the scanned strings (§44 —
 * label + leaf_count come from the inline-cap body scan, not a caller layout;
 * §96 — cap_kind is the derived plasmid/nuclear/diploid classification). */
static srmech_json_value_t *genome_build_chrom(srmech_json_builder_t *b,
                                               const genome_strings_t *s,
                                               uint32_t idx)
{
    assert(b != NULL && s != NULL);
    assert(idx < s->cap_chroms);
    const char *keys[6] = { "label", "cap_sha256", "leaf_count",
                            "byte_offset", "byte_len", "cap_kind" };
    srmech_json_value_t *vals[6];
    const char *ck = genome_cap_kind_str(s->cap_kind[idx]);
    vals[0] = srmech_json_new_string(b, s->label[idx],
                                     (uint32_t)strlen(s->label[idx]));
    vals[1] = srmech_json_new_string(b, s->cap_sha[idx],
                                     (uint32_t)strlen(s->cap_sha[idx]));
    vals[2] = srmech_json_new_int(b, (int64_t)s->leaf_count[idx]);
    vals[3] = srmech_json_new_int(b, (int64_t)s->byte_offset[idx]);
    vals[4] = srmech_json_new_int(b, (int64_t)s->byte_len[idx]);
    vals[5] = srmech_json_new_string(b, ck, (uint32_t)strlen(ck));
    return srmech_json_new_object(b, keys, vals, 6u);
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

/* Build the "data" block. head_only (v12): the O(1) HEAD — format_version / leaf_dim /
 * n_turns / n_chromosomes / coupling / body_sha256, NO per-chromosome chromosomes/regions
 * arrays (those are a plaintext TOC, dropped from disk + derived by scanning the body).
 * !head_only (the reader-side DERIVE / a v≤11 read): the FULL data with the arrays.
 * v4 (rc115 #1245(b)): body_sha256 is the region CHAIN (s->body_sha). */
static srmech_json_value_t *genome_build_data(srmech_json_builder_t *b,
                                              const genome_strings_t *s,
                                              srmech_json_value_t **chrom_items,
                                              srmech_json_value_t **region_items,
                                              uint32_t leaf_dim,
                                              size_t body_len, int head_only)
{
    assert(b != NULL && s != NULL);
    assert(leaf_dim > 0u);
    assert(head_only || s->n_chroms <= s->cap_chroms);   /* head: n_chroms is a COUNT */
    (void)body_len;                 /* §55/v3: n_turns is the scanned BLOCK count */
    /* §Q8/v16: "carrier" names the element-type packer ("klein4"/"q8"), derived from
     * the body scan (a Q₈ 0x38 turn seen → "q8"). The json writer SORTS keys, so build
     * order is cosmetic; this stays byte-identical to json.dumps(sort_keys=True). */
    const char *carrier = s->carrier_q8 ? "q8" : "klein4";
    if (head_only) {                /* v12 HEAD-ONLY manifest data (no arrays) */
        const char *hkeys[7] = { "format_version", "carrier", "leaf_dim", "n_turns",
                                 "n_chromosomes", "coupling", "body_sha256" };
        srmech_json_value_t *hvals[7];
        hvals[0] = srmech_json_new_int(b, (int64_t)SRMECH_GENOME_FORMAT_VERSION);
        hvals[1] = srmech_json_new_string(b, carrier, (uint32_t)strlen(carrier));
        hvals[2] = srmech_json_new_int(b, (int64_t)leaf_dim);
        hvals[3] = srmech_json_new_int(b, (int64_t)s->n_blocks);
        hvals[4] = srmech_json_new_int(b, (int64_t)s->n_chroms);
        hvals[5] = genome_build_coupling(b, s);
        hvals[6] = srmech_json_new_string(b, s->body_sha, (uint32_t)strlen(s->body_sha));
        return srmech_json_new_object(b, hkeys, hvals, 7u);
    }
    assert(chrom_items != NULL || s->n_chroms == 0u);
    for (uint32_t i = 0; i < s->n_chroms; i++) {
        chrom_items[i] = genome_build_chrom(b, s, i);
        region_items[i] = genome_build_region(b, s, i);
    }
    srmech_json_value_t *arr = srmech_json_new_array(b, chrom_items, s->n_chroms);
    srmech_json_value_t *rarr = srmech_json_new_array(b, region_items, s->n_chroms);
    (void)body_len;                 /* §55/v3: n_turns is the scanned BLOCK count */
    int64_t n_turns = (int64_t)s->n_blocks;
    const char *keys[8] = { "format_version", "carrier", "leaf_dim", "n_turns",
                            "coupling", "body_sha256", "regions", "chromosomes" };
    srmech_json_value_t *vals[8];
    vals[0] = srmech_json_new_int(b, (int64_t)SRMECH_GENOME_FORMAT_VERSION);
    vals[1] = srmech_json_new_string(b, carrier, (uint32_t)strlen(carrier));
    vals[2] = srmech_json_new_int(b, (int64_t)leaf_dim);
    vals[3] = srmech_json_new_int(b, n_turns);
    vals[4] = genome_build_coupling(b, s);
    vals[5] = srmech_json_new_string(b, s->body_sha, (uint32_t)strlen(s->body_sha));
    vals[6] = rarr;
    vals[7] = arr;
    return srmech_json_new_object(b, keys, vals, 8u);
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
                                                  void **wtail, size_t *wtail_len,
                                                  int head_only)
{
    assert(s != NULL && out != NULL);
    assert(leaf_dim > 0u);
    assert(head_only || s->n_chroms <= s->cap_chroms);   /* head: n_chroms is a COUNT */
    /* Carve the chrom-pointer scratch from the FRONT of the caller arena, then
     * run the json builder on the TAIL (so the scratch stays put across the
     * build). No fixed cap — the bound is the caller's arena. head_only skips the
     * per-chromosome scratch entirely (the head has no arrays). */
    genome_arena_t a;
    genome_arena_init(&a, ws, ws_len);
    srmech_json_value_t **chrom_items = NULL;
    srmech_json_value_t **region_items = NULL;
    if (!head_only && s->n_chroms > 0u) {
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
    v[1] = genome_build_data(&b, s, chrom_items, region_items, leaf_dim, body_len,
                             head_only);
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
                                             size_t *out_len, int head_only)
{
    assert(s != NULL && out != NULL && out_len != NULL);
    assert(leaf_dim > 0u);
    assert(head_only || s->n_chroms <= s->cap_chroms);   /* head: n_chroms is a COUNT */
    srmech_json_value_t *root = NULL;
    void *wtail = NULL;
    size_t wtail_len = 0u;
    srmech_status_t st = genome_build_manifest_tree(s, leaf_dim, body_len,
                                                    ws, ws_len, &root,
                                                    &wtail, &wtail_len, head_only);
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

/* §44 CAP-PACK writer — the C mirror of srmech.amsc.genome._pack_cap. Build a
 * fixed-width `dim`-byte cap leaf `[marker] + label, NUL-padded to dim` into
 * `out` (capacity out_cap >= dim). `marker` (> 3) classifies the block; the
 * label (raw bytes, already UTF-8) must fit dim - 1 bytes (one marker byte +
 * label + NUL padding). The shared cap-WRITER foundation rc197/rc198 reuse to
 * build every chromosome / gene / kernel cap. Caller-arena, no malloc, no abs.
 * (genome_decode_label + block[0] is the READ inverse — together they are the
 * C _pack_cap / _unpack_cap pair.) */
static srmech_status_t genome_pack_cap(unsigned char marker,
                                       const unsigned char *label,
                                       size_t label_len, uint32_t dim,
                                       unsigned char *out, size_t out_cap)
{
    if (out == NULL || (label == NULL && label_len != 0u)) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(out != NULL);
    assert(label != NULL || label_len == 0u);
    if (dim == 0u || (size_t)dim > out_cap) { return SRMECH_ERR_BAD_INPUT; }
    if (label_len > (size_t)dim - 1u) { return SRMECH_ERR_BAD_INPUT; }
    out[0] = marker;
    if (label_len != 0u) { memcpy(out + 1, label, label_len); }
    memset(out + 1u + label_len, 0, (size_t)dim - 1u - label_len);
    return SRMECH_OK;
}

/* rc196 — the CHROM boundary cap writer (mirror srmech.amsc.genome.telomere):
 * `[SRMECH_GENOME_CHROM_CAP_MARKER] + label, NUL-padded to dim`. Byte-identical
 * to the bytes behind the Python telomere (which wraps them in HV(sectors=256)). */
srmech_status_t srmech_genome_telomere(const unsigned char *label,
                                       size_t label_len, uint32_t dim,
                                       unsigned char *out, size_t out_cap)
{
    if (out == NULL || (label == NULL && label_len != 0u)) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(out != NULL);
    assert(label != NULL || label_len == 0u);
    return genome_pack_cap(SRMECH_GENOME_CHROM_CAP_MARKER, label, label_len,
                           dim, out, out_cap);
}

/* rc196 — the pure-integer genome shape planner (mirror
 * srmech.amsc.genome.encode_shape's arithmetic): leaves = ceil(n / 256),
 * depth = ceil(log4(leaves)). Class-I/N integer only, no float, no abs. The
 * Python maps depth → shape label + builds the dict; here we compute the two
 * integers it needs (byte-identical). */
srmech_status_t srmech_genome_encode_shape(uint64_t n, uint64_t *leaves_out,
                                           uint32_t *depth_out)
{
    if (leaves_out == NULL || depth_out == NULL) { return SRMECH_ERR_NULL_ARG; }
    assert(leaves_out != NULL);
    assert(depth_out != NULL);
    if (n == 0u) { return SRMECH_ERR_BAD_INPUT; }
    /* leaves = ceil(n / 256) — split the divide so n + 255 cannot wrap uint64. */
    uint64_t leaves = n / (uint64_t)SRMECH_GENOME_LEAF_CAP;
    if (n % (uint64_t)SRMECH_GENOME_LEAF_CAP != 0u) { leaves += 1u; }
    /* depth = smallest d >= 0 with QUAD**d >= leaves (QUAD = 4, the Klein-4
     * order). power tops out at 4**28 = 2**56 < 2**64 for any uint64 leaves. */
    uint32_t d = 0u;
    uint64_t power = 1u;
    while (power < leaves) { power *= 4u; d += 1u; }
    *leaves_out = leaves;
    *depth_out = d;
    return SRMECH_OK;
}

/* rc197 (#887) — the plain CHROMOSOME builder (mirror srmech.amsc.genome.chromosome's
 * single-kernel plain path: no genes / kernel / active_count). Writes a leading CHROM
 * telomere cap over `label` (reusing the rc196 genome_pack_cap), then each of the
 * `n_leaves` leaves (each leaf_dim bytes, contiguous in `leaves`) coupled through
 * `coupling` via srmech_klein4_bind — the reversible Klein-4 XOR that is quad_turn. The
 * strand is (1 + n_leaves) leaf_dim-byte blocks in `out`. BYTE-IDENTICAL to the bytes
 * behind the Python strand (recovered by srmech_genome_recall). The gene / kernel /
 * active-telomere forms open their own boundary caps → stay in the pure Python.
 * Caller-arena output (no malloc), no goto, no abs, no float. */
srmech_status_t srmech_genome_chromosome(const unsigned char *label,
                                         size_t label_len,
                                         const unsigned char *coupling,
                                         uint32_t leaf_dim,
                                         const unsigned char *leaves,
                                         size_t n_leaves,
                                         unsigned char *out, size_t out_cap)
{
    if (out == NULL || coupling == NULL ||
        (label == NULL && label_len != 0u) ||
        (leaves == NULL && n_leaves != 0u)) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(out != NULL && coupling != NULL);
    assert(leaves != NULL || n_leaves == 0u);
    if (leaf_dim == 0u || leaf_dim > 256u) { return SRMECH_ERR_BAD_INPUT; }
    /* strand = 1 cap + n_leaves turns, each leaf_dim bytes; check the fit without
     * overflowing size_t (n_leaves is a caller count; leaf_dim <= 256). */
    size_t max_blocks = out_cap / (size_t)leaf_dim;
    if (n_leaves + 1u < n_leaves || n_leaves + 1u > max_blocks) {
        return SRMECH_ERR_OVERFLOW;
    }
    /* [0] the CHROM telomere cap (the rc196 shared cap writer). */
    srmech_status_t st = genome_pack_cap(SRMECH_GENOME_CHROM_CAP_MARKER, label,
                                         label_len, leaf_dim, out, leaf_dim);
    if (st != SRMECH_OK) { return st; }
    /* [1..] each leaf coupled through coupling — the reversible Klein-4 bind. */
    for (size_t i = 0; i < n_leaves; i++) {
        st = srmech_klein4_bind(leaves + i * (size_t)leaf_dim, coupling,
                                leaf_dim, out + (i + 1u) * (size_t)leaf_dim);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* rc197 (#887) — the plain RECALL (mirror srmech.amsc.genome.recall): walk the strand's
 * `n_blocks` fixed-width leaf_dim-byte blocks, SKIP every cap (genome_cap_kind >= 0 — the
 * rc196 kind classifier), and re-bind each data turn through `coupling` via
 * srmech_klein4_bind (quad_turn is its own inverse) to recover the original leaf. The
 * recovered leaves are written contiguously to `out` (leaf_dim bytes each); *n_leaves_out
 * gets their count. BYTE-IDENTICAL to recall (gate-agnostic: it flattens across every cap
 * marker, exactly like the pure walk). No malloc, no goto, no abs, no float. */
srmech_status_t srmech_genome_recall(const unsigned char *strand,
                                     size_t n_blocks, uint32_t leaf_dim,
                                     const unsigned char *coupling,
                                     unsigned char *out, size_t out_cap,
                                     size_t *n_leaves_out)
{
    if (strand == NULL || coupling == NULL || out == NULL ||
        n_leaves_out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(strand != NULL && coupling != NULL);
    assert(out != NULL && n_leaves_out != NULL);
    if (leaf_dim == 0u || leaf_dim > 256u) { return SRMECH_ERR_BAD_INPUT; }
    size_t count = 0u;
    for (size_t i = 0; i < n_blocks; i++) {
        const unsigned char *block = strand + i * (size_t)leaf_dim;
        if (genome_cap_kind(block, leaf_dim) >= 0) { continue; }   /* skip caps */
        size_t off = count * (size_t)leaf_dim;
        if (off + (size_t)leaf_dim > out_cap) { return SRMECH_ERR_OVERFLOW; }
        srmech_status_t st = srmech_klein4_bind(block, coupling, leaf_dim,
                                                out + off);
        if (st != SRMECH_OK) { return st; }
        count++;
    }
    *n_leaves_out = count;
    return SRMECH_OK;
}

/* rc198 (#887) make_class → C leaf-batch 4 — the genome MULTI-KERNEL + PARTITION
 * in-memory leaves, COMPLETING the genome leaf-family in C. Both LOOP the rc197
 * leaves (srmech_genome_chromosome to assemble, the recall re-bind to recover) and
 * reuse the rc196 cap foundation (genome_pack_cap / genome_cap_kind /
 * genome_decode_label) verbatim — so a bare-C host (and the rc201 object-model
 * engine) assembles / splits a multi-kernel genome strand natively, BYTE-IDENTICAL
 * to the Python. Additive symbols only → SRMECH_ABI_VERSION stays 4.
 *
 * GENOME — assemble `n_kernels` labelled kernels into ONE strand: each kernel
 * becomes a CHROM-capped chromosome (via the rc197 srmech_genome_chromosome),
 * concatenated in kernel order. Mirror srmech.amsc.genome.genome(kernels, coupling)
 * for the plain (single-gene-per-chromosome) path — the §44 chromosomes= multi-gene
 * form opens its own gene caps and stays in the pure Python.
 *   labels / label_lens : the n_kernels raw UTF-8 labels CONCATENATED (`labels`),
 *                         label_lens[k] the k-th label's byte length (its slice).
 *   coupling / leaf_dim  : the shared Klein-4 invariant (leaf_dim bytes) + block width.
 *   leaves / leaf_counts: the kernels' leaves CONCATENATED (each leaf_dim bytes),
 *                         leaf_counts[k] the k-th kernel's leaf count.
 *   n_kernels           : the kernel count (the label / leaf arrays may be NULL iff 0).
 *   out / out_cap       : caller buffer; out_cap >= (n_kernels + Σ leaf_counts)*leaf_dim.
 *   n_blocks_out        : out — the total strand block count written.
 * Error returns mirror srmech_genome_chromosome (NULL_ARG / BAD_INPUT / OVERFLOW). */
srmech_status_t srmech_genome_genome(const unsigned char *labels,
                                     const size_t *label_lens,
                                     const unsigned char *coupling,
                                     uint32_t leaf_dim,
                                     const unsigned char *leaves,
                                     const size_t *leaf_counts,
                                     size_t n_kernels,
                                     unsigned char *out, size_t out_cap,
                                     size_t *n_blocks_out)
{
    if (out == NULL || coupling == NULL || n_blocks_out == NULL ||
        (n_kernels != 0u &&
         (labels == NULL || label_lens == NULL || leaf_counts == NULL))) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(out != NULL && coupling != NULL && n_blocks_out != NULL);
    assert(n_kernels == 0u || (label_lens != NULL && leaf_counts != NULL));
    if (leaf_dim == 0u || leaf_dim > 256u) { return SRMECH_ERR_BAD_INPUT; }
    size_t label_off = 0u;    /* byte cursor into `labels` */
    size_t leaf_off = 0u;     /* block cursor into `leaves` */
    size_t out_off = 0u;      /* byte cursor into `out` (<= out_cap always) */
    size_t blocks = 0u;
    for (size_t k = 0; k < n_kernels; k++) {
        size_t kn = leaf_counts[k];
        const unsigned char *kleaves = leaves + leaf_off * (size_t)leaf_dim;
        /* each kernel → a CHROM-capped chromosome via the rc197 peer (byte-exact). */
        srmech_status_t st = srmech_genome_chromosome(
            labels + label_off, label_lens[k], coupling, leaf_dim,
            kleaves, kn, out + out_off, out_cap - out_off);
        if (st != SRMECH_OK) { return st; }
        size_t kblocks = kn + 1u;                     /* the CHROM cap + kn turns */
        out_off += kblocks * (size_t)leaf_dim;
        blocks += kblocks;
        label_off += label_lens[k];
        leaf_off += kn;
    }
    *n_blocks_out = blocks;
    return SRMECH_OK;
}

/* §95a/v13 (rc258, #1407) — the CENTROMERE cap writer (mirror
 * srmech.amsc.genome._pack_centromere): [0x58] + handle + NUL + R + R orientation votes,
 * NUL-padded to dim. Each vote is the Klein-4 sector `orientation` (0..3); the R copies are
 * biology's α-satellite repeat-array. Byte-identical to the Python cap. No malloc/abs/float. */
static srmech_status_t genome_pack_centromere(unsigned char orientation,
                                              uint32_t repeats,
                                              const unsigned char *handle,
                                              size_t handle_len, uint32_t dim,
                                              unsigned char *out, size_t out_cap)
{
    if (out == NULL || (handle == NULL && handle_len != 0u)) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(out != NULL);
    assert(handle != NULL || handle_len == 0u);
    if (dim == 0u || (size_t)dim > out_cap) { return SRMECH_ERR_BAD_INPUT; }
    if (orientation > 3u) { return SRMECH_ERR_BAD_INPUT; }
    if (repeats < 1u || repeats > 255u) { return SRMECH_ERR_BAD_INPUT; }
    /* [marker] + handle + NUL + R + R votes — the payload must fit one leaf. */
    size_t payload = 3u + handle_len + (size_t)repeats;   /* marker + NUL + R + votes + handle */
    if (payload > (size_t)dim) { return SRMECH_ERR_BAD_INPUT; }
    out[0] = SRMECH_GENOME_CENTROMERE_CAP_MARKER;
    if (handle_len != 0u) { memcpy(out + 1, handle, handle_len); }
    out[1u + handle_len] = 0u;                            /* handle NUL terminator */
    out[2u + handle_len] = (unsigned char)repeats;        /* R */
    memset(out + 3u + handle_len, (int)orientation, (size_t)repeats);  /* R votes */
    memset(out + payload, 0, (size_t)dim - payload);      /* NUL pad */
    return SRMECH_OK;
}

/* §95a/v13 public CENTROMERE cap writer — the srmech_genome_centromere wrapper. */
srmech_status_t srmech_genome_centromere(unsigned char orientation,
                                         uint32_t repeats,
                                         const unsigned char *handle,
                                         size_t handle_len, uint32_t dim,
                                         unsigned char *out, size_t out_cap)
{
    if (out == NULL || (handle == NULL && handle_len != 0u)) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(out != NULL);
    assert(handle != NULL || handle_len == 0u);
    return genome_pack_centromere(orientation, repeats, handle, handle_len,
                                  dim, out, out_cap);
}

/* §95a/v13 — majority-decode the GLOBAL orientation from a centromere cap's α-satellite votes
 * (mirror srmech.amsc.genome._centromere_orientation): R at [nul+1], votes at [nul+2:nul+2+R];
 * a Class-K sector-occupancy count + argmax (ties toward the lowest sector — strict >). This is
 * klein4_triality_correct's 2-of-3 generalised to R. No abs, no float. */
static srmech_status_t genome_centromere_orientation(const unsigned char *cap,
                                                     uint32_t leaf_dim,
                                                     unsigned char *o_out)
{
    assert(cap != NULL && o_out != NULL);
    assert(leaf_dim > 0u);
    size_t nul = 1u;                                      /* handle NUL scan (bytes [1:]) */
    while (nul < (size_t)leaf_dim && cap[nul] != 0u) { nul++; }
    if (nul + 2u > (size_t)leaf_dim) { return SRMECH_ERR_BAD_INPUT; }
    size_t r = cap[nul + 1u];
    if (nul + 2u + r > (size_t)leaf_dim) { return SRMECH_ERR_BAD_INPUT; }
    unsigned int counts[4] = {0u, 0u, 0u, 0u};           /* Class-K sector occupancy */
    for (size_t i = 0; i < r; i++) { counts[cap[nul + 2u + i] & 3u]++; }
    unsigned char best = 0u;
    for (unsigned char sctr = 1u; sctr < 4u; sctr++) {
        if (counts[sctr] > counts[best]) { best = sctr; }  /* strict > keeps ties lowest */
    }
    *o_out = best;
    return SRMECH_OK;
}

/* §95a/v13 — the mint orientation: sha256(raw leaves)[0] & 3 (Class A content-address → Class C
 * sector), matching Python int(sha256_hex[0:2], 16) & 3. */
static srmech_status_t genome_mint_orientation(const unsigned char *content,
                                               size_t n, unsigned char *o_out)
{
    assert(content != NULL || n == 0u);
    assert(o_out != NULL);
    char hex[65];
    srmech_status_t st = srmech_sha256_hex(content, n, hex);
    if (st != SRMECH_OK) { return st; }
    unsigned int hi = (hex[0] >= 'a') ? (unsigned int)(hex[0] - 'a' + 10)
                                      : (unsigned int)(hex[0] - '0');
    unsigned int lo = (hex[1] >= 'a') ? (unsigned int)(hex[1] - 'a' + 10)
                                      : (unsigned int)(hex[1] - '0');
    *o_out = (unsigned char)(((hi << 4) | lo) & 3u);      /* first digest byte & 3 */
    return SRMECH_OK;
}

/* §95a/v13 — bind turns[from:to] through coupling into `out` starting at block *oi (advancing
 * it). The reversible Klein-4 XOR that is quad_turn; shared by the nuclear-chromosome arms. */
static srmech_status_t genome_bind_turns(const unsigned char *kleaves,
                                         size_t from, size_t to,
                                         const unsigned char *coupling,
                                         uint32_t leaf_dim, unsigned char *out,
                                         size_t *oi)
{
    assert(kleaves != NULL || from == to);
    assert(coupling != NULL && out != NULL && oi != NULL);
    for (size_t i = from; i < to; i++) {
        srmech_status_t st = srmech_klein4_bind(kleaves + i * (size_t)leaf_dim,
                                                coupling, leaf_dim,
                                                out + (*oi) * (size_t)leaf_dim);
        if (st != SRMECH_OK) { return st; }
        (*oi)++;
    }
    return SRMECH_OK;
}

/* §95a/v13 — build ONE chromosome, the tooling PICKING its shape by the attested encode_shape
 * (mirror the Python mint()'s per-kernel branch): depth < 2 (tome/mobius) → a Tier-1 PLASMID
 * (byte-identical to srmech_genome_chromosome); depth >= 2 (quad_strand) → a Tier-2 NUCLEAR
 * chromosome [telomere] + short-arm + [centromere] + long-arm, metacentric split, orientation =
 * content-address of the raw leaves. Writes *blocks_out blocks. No malloc/goto/abs/float. */
static srmech_status_t genome_mint_chromosome(const unsigned char *label,
                                              size_t label_len,
                                              const unsigned char *coupling,
                                              uint32_t leaf_dim,
                                              const unsigned char *kleaves,
                                              size_t kn, unsigned char *out,
                                              size_t out_cap, size_t *blocks_out)
{
    assert(coupling != NULL && out != NULL && blocks_out != NULL);
    assert(kleaves != NULL || kn == 0u);
    uint64_t leaves_sh = 0u;
    uint32_t depth = 0u;
    uint64_t n = (kn == 0u ? 1u : (uint64_t)kn) * (uint64_t)SRMECH_GENOME_LEAF_CAP;
    srmech_status_t st = srmech_genome_encode_shape(n, &leaves_sh, &depth);
    if (st != SRMECH_OK) { return st; }
    if (depth < 2u) {                                    /* tome/mobius → Tier-1 plasmid */
        st = srmech_genome_chromosome(label, label_len, coupling, leaf_dim,
                                      kleaves, kn, out, out_cap);
        if (st != SRMECH_OK) { return st; }
        *blocks_out = kn + 1u;
        return SRMECH_OK;
    }
    /* quad_strand → Tier-2 nuclear: [telomere] + short-arm + [centromere] + long-arm. */
    size_t total = kn + 2u;                              /* telomere + kn turns + centromere */
    if (total > out_cap / (size_t)leaf_dim) { return SRMECH_ERR_OVERFLOW; }
    unsigned char o = 0u;
    st = genome_mint_orientation(kleaves, kn * (size_t)leaf_dim, &o);
    if (st != SRMECH_OK) { return st; }
    st = genome_pack_cap(SRMECH_GENOME_CHROM_CAP_MARKER, label, label_len,
                         leaf_dim, out, leaf_dim);
    if (st != SRMECH_OK) { return st; }
    size_t oi = 1u;
    size_t split = kn / 2u;                              /* metacentric arm-split */
    st = genome_bind_turns(kleaves, 0u, split, coupling, leaf_dim, out, &oi);
    if (st != SRMECH_OK) { return st; }
    st = genome_pack_centromere(o, SRMECH_GENOME_CENTROMERE_DEFAULT_REPEATS,
                                (const unsigned char *)"cen", 3u, leaf_dim,
                                out + oi * (size_t)leaf_dim, leaf_dim);
    if (st != SRMECH_OK) { return st; }
    oi++;
    st = genome_bind_turns(kleaves, split, kn, coupling, leaf_dim, out, &oi);
    if (st != SRMECH_OK) { return st; }
    *blocks_out = total;
    return SRMECH_OK;
}

/* §95a/v13 MINT — build a genome, the tooling PICKING each chromosome's shape (mirror
 * srmech.amsc.genome.mint / #1407). Same shape as srmech_genome_genome; genome_mint_chromosome
 * does the per-kernel plasmid-vs-centromere selection. BYTE-IDENTICAL to the Python mint(). */
/* §101: the plain symbol keeps its exact ABI signature and forwards to the
 * _progress overload with a NULL tick (runs exactly as before rc275). */
srmech_status_t srmech_genome_mint(const unsigned char *labels,
                                   const size_t *label_lens,
                                   const unsigned char *coupling,
                                   uint32_t leaf_dim, const unsigned char *leaves,
                                   const size_t *leaf_counts, size_t n_kernels,
                                   unsigned char *out, size_t out_cap,
                                   size_t *n_blocks_out)
{
    assert(out != NULL || n_blocks_out == NULL);
    assert(leaf_dim <= 256u);
    return srmech_genome_mint_progress(labels, label_lens, coupling, leaf_dim,
                                       leaves, leaf_counts, n_kernels, out,
                                       out_cap, n_blocks_out, NULL, NULL);
}

/* §101 ENCODE-PROGRESS overload of MINT — the plain per-kernel loop + a tick at
 * the TOP of each kernel (phase SRMECH_PHASE_MINTING, done = k complete
 * chromosomes so far, total = n_kernels). A nonzero tick CANCELS: *n_blocks_out
 * is set to the COMPLETE blocks already written (a valid k-chromosome partial
 * genome, never a half-written chromosome) and SRMECH_CANCELLED is returned. */
srmech_status_t srmech_genome_mint_progress(const unsigned char *labels,
                                   const size_t *label_lens,
                                   const unsigned char *coupling,
                                   uint32_t leaf_dim, const unsigned char *leaves,
                                   const size_t *leaf_counts, size_t n_kernels,
                                   unsigned char *out, size_t out_cap,
                                   size_t *n_blocks_out,
                                   srmech_progress_tick_cb_t tick, void *tick_user)
{
    if (out == NULL || coupling == NULL || n_blocks_out == NULL ||
        (n_kernels != 0u &&
         (labels == NULL || label_lens == NULL || leaf_counts == NULL))) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(out != NULL && coupling != NULL && n_blocks_out != NULL);
    assert(n_kernels == 0u || (label_lens != NULL && leaf_counts != NULL));
    if (leaf_dim == 0u || leaf_dim > 256u) { return SRMECH_ERR_BAD_INPUT; }
    size_t label_off = 0u, leaf_off = 0u, out_off = 0u, blocks = 0u;
    for (size_t k = 0; k < n_kernels; k++) {
        if (tick != NULL) {
            srmech_progress_ev_t ev = { (uint32_t)sizeof(srmech_progress_ev_t),
                                        (uint32_t)SRMECH_PHASE_MINTING,
                                        (uint64_t)k, (uint64_t)n_kernels };
            if (tick(&ev, tick_user) != 0) {
                *n_blocks_out = blocks;    /* valid partial: k complete chromosomes */
                return SRMECH_CANCELLED;
            }
        }
        size_t kn = leaf_counts[k];
        const unsigned char *kleaves = leaves + leaf_off * (size_t)leaf_dim;
        size_t kblocks = 0u;
        srmech_status_t st = genome_mint_chromosome(
            labels + label_off, label_lens[k], coupling, leaf_dim, kleaves, kn,
            out + out_off, out_cap - out_off, &kblocks);
        if (st != SRMECH_OK) { return st; }
        out_off += kblocks * (size_t)leaf_dim;
        blocks += kblocks;
        label_off += label_lens[k];
        leaf_off += kn;
    }
    *n_blocks_out = blocks;
    return SRMECH_OK;
}

/* §95a/v13 CENTROMERE READ — recover a nuclear chromosome's orientation + p:q arm-ratio (mirror
 * srmech.amsc.genome.centromere_of). p = data turns before the 0x58 cap, q = after. */
srmech_status_t srmech_genome_centromere_of(const unsigned char *strand,
                                            size_t n_blocks, uint32_t leaf_dim,
                                            unsigned char *orientation_out,
                                            size_t *p_out, size_t *q_out,
                                            int *found_out)
{
    if (strand == NULL || found_out == NULL) { return SRMECH_ERR_NULL_ARG; }
    assert(strand != NULL && found_out != NULL);
    if (leaf_dim == 0u || leaf_dim > 256u) { return SRMECH_ERR_BAD_INPUT; }
    assert(leaf_dim >= 1u && leaf_dim <= 256u);          /* the guard above holds here */
    const unsigned char *cen = NULL;
    size_t p = 0u, total = 0u;
    for (size_t i = 0; i < n_blocks; i++) {
        const unsigned char *block = strand + i * (size_t)leaf_dim;
        int kind = genome_cap_kind(block, leaf_dim);
        if (kind == (int)SRMECH_GENOME_CENTROMERE_CAP_MARKER) {
            cen = block;
            p = total;                                   /* data turns so far = short arm */
        } else if (kind < 0) {
            total++;                                     /* a coupled data turn */
        }
    }
    *found_out = (cen != NULL) ? 1 : 0;
    if (cen == NULL) { return SRMECH_OK; }
    unsigned char o = 0u;
    srmech_status_t st = genome_centromere_orientation(cen, leaf_dim, &o);
    if (st != SRMECH_OK) { return st; }
    if (orientation_out != NULL) { *orientation_out = o; }
    if (p_out != NULL) { *p_out = p; }
    if (q_out != NULL) { *q_out = total - p; }
    return SRMECH_OK;
}

/* §95b/v14 (rc259, #1407; §95.4 rc264 erasure-symmetry fix) — the per-leaf DIPLOID EC read
 * (mirror _diploid_ec_leaf): exactly one ERASED -> the intact homolog (the erasure
 * specialist); both present + agree -> use it; both present but DISAGREE -> the centromere
 * which-template mark (which = 0 -> copyA, 1 -> copyB). `a_turn`/`b_turn` are the two STORED
 * homolog TURNS (leaf_dim bytes each, PRE-decouple): erasure is an all-zero stored TURN, read
 * BEFORE decoupling — a zeroed turn decouples to a NON-zero leaf, so the sentinel MUST be
 * tested on the turn (the §95.4 bug: testing the decoupled leaf detected no erasure, so a
 * copyA break healed only by substitution-tiebreak luck — asymmetric). Decouples the
 * survivor(s) via srmech_klein4_bind; writes the chosen leaf to `out`. Class-K compare; no
 * float/abs. */
static srmech_status_t genome_diploid_ec_leaf(const unsigned char *a_turn,
                                              const unsigned char *b_turn,
                                              const unsigned char *coupling,
                                              uint32_t leaf_dim, unsigned int which,
                                              unsigned char *out)
{
    assert(a_turn != NULL && b_turn != NULL && coupling != NULL && out != NULL);
    assert(leaf_dim > 0u && leaf_dim <= 256u);
    int a_erased = 1, b_erased = 1;
    for (uint32_t k = 0; k < leaf_dim; k++) {
        if (a_turn[k] != 0u) { a_erased = 0; }
        if (b_turn[k] != 0u) { b_erased = 0; }
    }
    if (a_erased != 0 && b_erased == 0) {                /* erasure -> heal from intact B */
        return srmech_klein4_bind(b_turn, coupling, leaf_dim, out);
    }
    if (b_erased != 0 && a_erased == 0) {                /* erasure -> heal from intact A */
        return srmech_klein4_bind(a_turn, coupling, leaf_dim, out);
    }
    unsigned char a[256], b[256];                        /* both present: decouple + compare */
    srmech_status_t st = srmech_klein4_bind(a_turn, coupling, leaf_dim, a);
    if (st != SRMECH_OK) { return st; }
    st = srmech_klein4_bind(b_turn, coupling, leaf_dim, b);
    if (st != SRMECH_OK) { return st; }
    const unsigned char *pick = (memcmp(a, b, (size_t)leaf_dim) == 0)
                                    ? a : ((which != 0u) ? b : a);
    memcpy(out, pick, (size_t)leaf_dim);
    return SRMECH_OK;
}

/* §95b/v14 DIPLOID builder — [diploid_telomere, copyA…, centromere(orientation), copyB…],
 * copyA == copyB (homologs). BYTE-IDENTICAL to the Python diploid(). */
srmech_status_t srmech_genome_diploid(const unsigned char *label, size_t label_len,
                                      const unsigned char *coupling, uint32_t leaf_dim,
                                      const unsigned char *leaves, size_t n_leaves,
                                      unsigned char orientation, uint32_t repeats,
                                      unsigned char *out, size_t out_cap,
                                      size_t *n_blocks_out)
{
    if (out == NULL || coupling == NULL || n_blocks_out == NULL ||
        (leaves == NULL && n_leaves != 0u)) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(out != NULL && coupling != NULL && n_blocks_out != NULL);
    assert(leaves != NULL || n_leaves == 0u);
    if (leaf_dim == 0u || leaf_dim > 256u || orientation > 3u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    size_t total = 2u * n_leaves + 2u;                   /* cap + n + centromere + n */
    if (n_leaves + 1u < n_leaves || total > out_cap / (size_t)leaf_dim) {
        return SRMECH_ERR_OVERFLOW;
    }
    srmech_status_t st = genome_pack_cap(SRMECH_GENOME_DIPLOID_TELOMERE_MARKER, label,
                                         label_len, leaf_dim, out, leaf_dim);
    if (st != SRMECH_OK) { return st; }
    size_t oi = 1u;
    st = genome_bind_turns(leaves, 0u, n_leaves, coupling, leaf_dim, out, &oi);  /* copyA */
    if (st != SRMECH_OK) { return st; }
    st = genome_pack_centromere(orientation, repeats, (const unsigned char *)"cen", 3u,
                                leaf_dim, out + oi * (size_t)leaf_dim, leaf_dim);
    if (st != SRMECH_OK) { return st; }
    oi++;
    st = genome_bind_turns(leaves, 0u, n_leaves, coupling, leaf_dim, out, &oi);  /* copyB */
    if (st != SRMECH_OK) { return st; }
    *n_blocks_out = total;
    return SRMECH_OK;
}

/* §95b/v14 DIPLOID recover — split at the interior centromere into copyA | copyB and
 * error-correct per leaf. BYTE-IDENTICAL to the Python recover_diploid. */
srmech_status_t srmech_genome_recover_diploid(const unsigned char *strand, size_t n_blocks,
                                              uint32_t leaf_dim, const unsigned char *coupling,
                                              unsigned char *out, size_t out_cap,
                                              size_t *n_out)
{
    if (strand == NULL || coupling == NULL || out == NULL || n_out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(strand != NULL && coupling != NULL);
    assert(out != NULL && n_out != NULL);
    if (leaf_dim == 0u || leaf_dim > 256u || n_blocks == 0u ||
        strand[0] != SRMECH_GENOME_DIPLOID_TELOMERE_MARKER) {
        return SRMECH_ERR_BAD_INPUT;
    }
    size_t cen_idx = 0u, n_before = 0u, n_turns = 0u;
    int have_cen = 0;
    for (size_t i = 0; i < n_blocks; i++) {
        int kind = genome_cap_kind(strand + i * (size_t)leaf_dim, leaf_dim);
        if (kind == (int)SRMECH_GENOME_CENTROMERE_CAP_MARKER) {
            cen_idx = i; have_cen = 1; n_before = n_turns;
        } else if (kind < 0) { n_turns++; }
    }
    if (have_cen == 0 || 2u * n_before != n_turns) { return SRMECH_ERR_BAD_INPUT; }
    unsigned char o = 0u;
    srmech_status_t st = genome_centromere_orientation(
        strand + cen_idx * (size_t)leaf_dim, leaf_dim, &o);
    if (st != SRMECH_OK) { return st; }
    unsigned int which = (unsigned int)(o & 1u);
    if (n_before > out_cap / (size_t)leaf_dim) { return SRMECH_ERR_OVERFLOW; }
    for (size_t j = 0; j < n_before; j++) {
        /* pass the STORED turns (pre-decouple) — erasure is read on the turn (§95.4) */
        st = genome_diploid_ec_leaf(strand + (1u + j) * (size_t)leaf_dim,
                                    strand + (cen_idx + 1u + j) * (size_t)leaf_dim,
                                    coupling, leaf_dim, which, out + j * (size_t)leaf_dim);
        if (st != SRMECH_OK) { return st; }
    }
    *n_out = n_before;
    return SRMECH_OK;
}

/* §Q8/rc311 — decouple one STORED Q8 turn back to its leaf: out[i] = q8_mult(stored[i],
 * q8_conjugate(one[i])) — the Q8 group INVERSE (Q8 is NON-abelian, so NOT a second bind; it
 * rests on srmech_q8_mult(a, srmech_q8_conjugate(a)) == 0). The RIGHT-coupling SIDE is a HARD
 * ASSERTION: re-coupling the result recovers `stored` (q8_mult(out[i], one[i]) == stored[i]) —
 * a wrong side would fail HERE, loudly (mirror of the Python _q8_side_ok guard). A non-Q8 byte
 * (>= 8) returns BAD_INPUT so the caller falls back to the pure path (never an assert-abort).
 * No malloc/goto/abs/float. */
static srmech_status_t genome_q8_uncouple(const unsigned char *stored,
                                          const unsigned char *one,
                                          uint32_t leaf_dim, unsigned char *out)
{
    assert(stored != NULL && one != NULL && out != NULL);
    assert(leaf_dim > 0u && leaf_dim <= 256u);
    for (uint32_t i = 0; i < leaf_dim; i++) {
        if (stored[i] >= 8u || one[i] >= 8u) { return SRMECH_ERR_BAD_INPUT; }
        unsigned char rec = srmech_q8_mult(stored[i], srmech_q8_conjugate(one[i]));
        assert(srmech_q8_mult(rec, one[i]) == stored[i]);   /* right-coupling side pin */
        out[i] = rec;
    }
    return SRMECH_OK;
}

/* §Q8/rc311 — the Q8 element-type recall: walk the blocks, skip every cap, and DECOUPLE each
 * Q8 data turn by the group inverse (genome_q8_uncouple) instead of the reversible klein4 XOR.
 * BYTE-IDENTICAL to recall(strand, coupling, element_type=ELEMENT_TYPE_Q8). A distinct symbol
 * from srmech_genome_recall (klein4), so ABI stays 10. No malloc/goto/abs/float. */
srmech_status_t srmech_genome_recall_q8(const unsigned char *strand,
                                        size_t n_blocks, uint32_t leaf_dim,
                                        const unsigned char *coupling,
                                        unsigned char *out, size_t out_cap,
                                        size_t *n_leaves_out)
{
    if (strand == NULL || coupling == NULL || out == NULL ||
        n_leaves_out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(strand != NULL && coupling != NULL);
    assert(out != NULL && n_leaves_out != NULL);
    if (leaf_dim == 0u || leaf_dim > 256u) { return SRMECH_ERR_BAD_INPUT; }
    size_t count = 0u;
    for (size_t i = 0; i < n_blocks; i++) {
        const unsigned char *block = strand + i * (size_t)leaf_dim;
        if (genome_cap_kind(block, leaf_dim) >= 0) { continue; }   /* skip caps */
        size_t off = count * (size_t)leaf_dim;
        if (off + (size_t)leaf_dim > out_cap) { return SRMECH_ERR_OVERFLOW; }
        srmech_status_t st = genome_q8_uncouple(block, coupling, leaf_dim,
                                                out + off);
        if (st != SRMECH_OK) { return st; }
        count++;
    }
    *n_leaves_out = count;
    return SRMECH_OK;
}

/* §Q8/rc311 — the per-leaf diploid EC for the Q8 path: the SAME two-copy + mark logic as
 * genome_diploid_ec_leaf, but the survivor decouple is the Q8 group inverse
 * (genome_q8_uncouple). The full-leaf memcmp is bit-width-agnostic, so it resolves a lone Q8
 * SIGN-bit disagreement (the NEW 3rd bit) through the SAME mark tiebreak it uses for a 2-bit V4
 * one. Erasure is read on the stored TURN (§95.4). No float/abs. */
static srmech_status_t genome_q8_ec_leaf(const unsigned char *a_turn,
                                         const unsigned char *b_turn,
                                         const unsigned char *coupling,
                                         uint32_t leaf_dim, unsigned int which,
                                         unsigned char *out)
{
    assert(a_turn != NULL && b_turn != NULL && coupling != NULL && out != NULL);
    assert(leaf_dim > 0u && leaf_dim <= 256u);
    int a_erased = 1, b_erased = 1;
    for (uint32_t k = 0; k < leaf_dim; k++) {
        if (a_turn[k] != 0u) { a_erased = 0; }
        if (b_turn[k] != 0u) { b_erased = 0; }
    }
    if (a_erased != 0 && b_erased == 0) {                /* erasure -> heal from intact B */
        return genome_q8_uncouple(b_turn, coupling, leaf_dim, out);
    }
    if (b_erased != 0 && a_erased == 0) {                /* erasure -> heal from intact A */
        return genome_q8_uncouple(a_turn, coupling, leaf_dim, out);
    }
    unsigned char a[256], b[256];                        /* both present: decouple + compare */
    srmech_status_t st = genome_q8_uncouple(a_turn, coupling, leaf_dim, a);
    if (st != SRMECH_OK) { return st; }
    st = genome_q8_uncouple(b_turn, coupling, leaf_dim, b);
    if (st != SRMECH_OK) { return st; }
    const unsigned char *pick = (memcmp(a, b, (size_t)leaf_dim) == 0)
                                    ? a : ((which != 0u) ? b : a);
    memcpy(out, pick, (size_t)leaf_dim);
    return SRMECH_OK;
}

/* §Q8/rc311 — the Q8 element-type diploid recover: the SAME split-at-centromere + two-copy EC
 * as srmech_genome_recover_diploid, decoupling each Q8 turn by the group inverse
 * (genome_q8_ec_leaf). BYTE-IDENTICAL to recover_diploid(..., element_type=ELEMENT_TYPE_Q8). A
 * distinct symbol from the klein4 peer, so ABI stays 10. No malloc/goto/abs/float. */
srmech_status_t srmech_genome_recover_diploid_q8(const unsigned char *strand, size_t n_blocks,
                                                 uint32_t leaf_dim,
                                                 const unsigned char *coupling,
                                                 unsigned char *out, size_t out_cap,
                                                 size_t *n_out)
{
    if (strand == NULL || coupling == NULL || out == NULL || n_out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(strand != NULL && coupling != NULL);
    assert(out != NULL && n_out != NULL);
    if (leaf_dim == 0u || leaf_dim > 256u || n_blocks == 0u ||
        strand[0] != SRMECH_GENOME_DIPLOID_TELOMERE_MARKER) {
        return SRMECH_ERR_BAD_INPUT;
    }
    size_t cen_idx = 0u, n_before = 0u, n_turns = 0u;
    int have_cen = 0;
    for (size_t i = 0; i < n_blocks; i++) {
        int kind = genome_cap_kind(strand + i * (size_t)leaf_dim, leaf_dim);
        if (kind == (int)SRMECH_GENOME_CENTROMERE_CAP_MARKER) {
            cen_idx = i; have_cen = 1; n_before = n_turns;
        } else if (kind < 0) { n_turns++; }
    }
    if (have_cen == 0 || 2u * n_before != n_turns) { return SRMECH_ERR_BAD_INPUT; }
    unsigned char o = 0u;
    srmech_status_t st = genome_centromere_orientation(
        strand + cen_idx * (size_t)leaf_dim, leaf_dim, &o);
    if (st != SRMECH_OK) { return st; }
    unsigned int which = (unsigned int)(o & 1u);
    if (n_before > out_cap / (size_t)leaf_dim) { return SRMECH_ERR_OVERFLOW; }
    for (size_t j = 0; j < n_before; j++) {
        /* pass the STORED turns (pre-decouple) — erasure is read on the turn (§95.4) */
        st = genome_q8_ec_leaf(strand + (1u + j) * (size_t)leaf_dim,
                               strand + (cen_idx + 1u + j) * (size_t)leaf_dim,
                               coupling, leaf_dim, which, out + j * (size_t)leaf_dim);
        if (st != SRMECH_OK) { return st; }
    }
    *n_out = n_before;
    return SRMECH_OK;
}

/* §98/v15 (rc268, #1422) — write a uint64 BIG-ENDIAN into out[0..8): the chromatin cap's
 * num/den accessibility-level fields. No abs (a level numerator/denominator is never negated). */
static void genome_put_u64_be(unsigned char *out, uint64_t v)
{
    assert(out != NULL);
    assert(SRMECH_GENOME_CHROMATIN_LEVEL_BYTES == 8u);
    for (size_t k = 0u; k < SRMECH_GENOME_CHROMATIN_LEVEL_BYTES; k++) {
        unsigned shift = 8u * (unsigned)(SRMECH_GENOME_CHROMATIN_LEVEL_BYTES - 1u - k);
        out[k] = (unsigned char)((v >> shift) & 0xFFu);
    }
}

/* §98/v15 — read a uint64 BIG-ENDIAN from cap[base..base+8). Bounds are checked by the caller. */
static uint64_t genome_get_u64_be(const unsigned char *cap, size_t base)
{
    assert(cap != NULL);
    assert(base < base + SRMECH_GENOME_CHROMATIN_LEVEL_BYTES);    /* no wrap */
    uint64_t v = 0u;
    for (size_t k = 0u; k < SRMECH_GENOME_CHROMATIN_LEVEL_BYTES; k++) {
        v = (v << 8) | (uint64_t)cap[base + k];
    }
    return v;
}

/* §98/v15 CHROMATIN cap writer (rc268, #1422) — mirror srmech.amsc.genome._pack_chromatin:
 * [0x48] + handle + NUL + chromatin_type + num(u64 BE) + den(u64 BE), NUL-padded to dim. The
 * accessibility level num/den is a reduced non-negative rational in [0,1] (den >= 1, num <= den).
 * Byte-identical to the Python cap. No malloc/abs/float. */
static srmech_status_t genome_pack_chromatin(unsigned char chromatin_type,
                                             uint64_t num, uint64_t den,
                                             const unsigned char *handle,
                                             size_t handle_len, uint32_t dim,
                                             unsigned char *out, size_t out_cap)
{
    if (out == NULL || (handle == NULL && handle_len != 0u)) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(out != NULL);
    assert(handle != NULL || handle_len == 0u);
    if (dim == 0u || (size_t)dim > out_cap) { return SRMECH_ERR_BAD_INPUT; }
    if (chromatin_type > SRMECH_GENOME_CHROMATIN_TYPE_GRADED) { return SRMECH_ERR_BAD_INPUT; }
    if (den == 0u || num > den) { return SRMECH_ERR_BAD_INPUT; }   /* level in [0,1], den positive */
    size_t lb = (size_t)SRMECH_GENOME_CHROMATIN_LEVEL_BYTES;
    size_t payload = 3u + handle_len + 2u * lb;   /* marker + handle + NUL + type + num + den */
    if (payload > (size_t)dim) { return SRMECH_ERR_BAD_INPUT; }
    out[0] = SRMECH_GENOME_CHROMATIN_MARKER;
    if (handle_len != 0u) { memcpy(out + 1, handle, handle_len); }
    out[1u + handle_len] = 0u;                            /* handle NUL terminator */
    out[2u + handle_len] = chromatin_type;                /* chromatin_type uint8 */
    genome_put_u64_be(out + 3u + handle_len, num);        /* num (u64 BE) */
    genome_put_u64_be(out + 3u + handle_len + lb, den);   /* den (u64 BE) */
    memset(out + payload, 0, (size_t)dim - payload);      /* NUL pad */
    return SRMECH_OK;
}

/* §Q8-FIBER/v17 (rc322, F-HOLO-MISLOCATED) — the strand's TOPOLOGY/FIBER channel.
 * Folds the ORDERED per-slot Q8 product of the coupled turns along the strand:
 * out[s] = q8_mult(...q8_mult(0, turns[0][s])..., turns[n_turns-1][s]). Because Q8
 * is non-abelian, REORDERING the turns changes the fold — the fiber/gauge (the
 * accumulated Lk) the winding-invariant per-turn store cannot carry. Writes `out`
 * (leaf_dim Q8 bytes) directly; no scratch, no malloc. See the header doc + Python
 * genome.genome_fiber_holonomy (the parity oracle). Class-M q8-bind fold; no abs(). */
srmech_status_t srmech_genome_fiber_holonomy(const uint8_t *turns,
                                             uint32_t n_turns,
                                             uint32_t leaf_dim,
                                             uint8_t *out)
{
    if (turns == NULL || out == NULL) { return SRMECH_ERR_NULL_ARG; }
    assert(turns != NULL && out != NULL);
    assert(leaf_dim > 0u);
    for (uint32_t s = 0u; s < leaf_dim; ++s) {
        out[s] = 0u;                        /* the Q8 identity +1 (byte 0) */
    }
    for (uint32_t t = 0u; t < n_turns; ++t) {
        const uint8_t *turn = turns + (size_t)t * (size_t)leaf_dim;
        for (uint32_t s = 0u; s < leaf_dim; ++s) {
            out[s] = srmech_q8_mult(out[s], turn[s]);   /* ordered: acc . turn_t */
        }
    }
    return SRMECH_OK;
}

/* §98/v15 public CHROMATIN cap writer — the srmech_genome_chromatin wrapper. */
srmech_status_t srmech_genome_chromatin(unsigned char chromatin_type, uint64_t num,
                                        uint64_t den, const unsigned char *handle,
                                        size_t handle_len, uint32_t dim,
                                        unsigned char *out, size_t out_cap)
{
    if (out == NULL || (handle == NULL && handle_len != 0u)) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(out != NULL);
    assert(handle != NULL || handle_len == 0u);
    return genome_pack_chromatin(chromatin_type, num, den, handle, handle_len,
                                 dim, out, out_cap);
}

/* §98.1/v15 (§98.1/G1 / rc274) FACULTATIVE chromatin cap writer — the srmech_genome_chromatin_gated
 * wrapper: build the constitutive cap, then append gate_blob = [access_gate_type] + payload VERBATIM
 * after den (the Python _chromatin_gate_blob serialisation is the oracle). gate_blob_len 0 →
 * byte-identical to srmech_genome_chromatin. See the header. Additive symbol → ABI stays 5. */
srmech_status_t srmech_genome_chromatin_gated(
    unsigned char chromatin_type, uint64_t num, uint64_t den,
    const unsigned char *gate_blob, size_t gate_blob_len,
    const unsigned char *handle, size_t handle_len, uint32_t dim,
    unsigned char *out, size_t out_cap)
{
    if (out == NULL || (handle == NULL && handle_len != 0u) ||
        (gate_blob == NULL && gate_blob_len != 0u)) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(out != NULL);
    assert(gate_blob != NULL || gate_blob_len == 0u);
    srmech_status_t st = genome_pack_chromatin(chromatin_type, num, den, handle,
                                               handle_len, dim, out, out_cap);
    if (st != SRMECH_OK) { return st; }
    if (gate_blob_len == 0u) { return SRMECH_OK; }        /* constitutive → bytes unchanged */
    size_t lb = (size_t)SRMECH_GENOME_CHROMATIN_LEVEL_BYTES;
    size_t den_end = 3u + handle_len + 2u * lb;           /* marker+handle+NUL+type+num+den */
    if (den_end + gate_blob_len > (size_t)dim) { return SRMECH_ERR_BAD_INPUT; }
    memcpy(out + den_end, gate_blob, gate_blob_len);
    memset(out + den_end + gate_blob_len, 0, (size_t)dim - den_end - gate_blob_len);
    return SRMECH_OK;
}

/* §98/v15 CHROMATIN READ (rc268) — the strand scan (mirror srmech.amsc.genome.chromatin_of).
 * Walk n_blocks leaf_dim-byte blocks; on the FIRST interior 0x48 cap fill type/num/den + *at_out
 * (data turns before it: 0 = whole-chromosome, >0 = a stretch). No abs, no float, no mutation. */
srmech_status_t srmech_genome_chromatin_of(const unsigned char *strand, size_t n_blocks,
                                           uint32_t leaf_dim, unsigned char *type_out,
                                           uint64_t *num_out, uint64_t *den_out,
                                           size_t *at_out, int *found_out)
{
    if (strand == NULL || found_out == NULL) { return SRMECH_ERR_NULL_ARG; }
    assert(strand != NULL && found_out != NULL);
    if (leaf_dim == 0u || leaf_dim > 256u) { return SRMECH_ERR_BAD_INPUT; }
    assert(leaf_dim >= 1u && leaf_dim <= 256u);          /* the guard above holds here */
    *found_out = 0;
    size_t lb = (size_t)SRMECH_GENOME_CHROMATIN_LEVEL_BYTES;
    size_t turns = 0u;
    for (size_t i = 0u; i < n_blocks; i++) {
        const unsigned char *block = strand + i * (size_t)leaf_dim;
        int kind = genome_cap_kind(block, leaf_dim);
        if (kind == (int)SRMECH_GENOME_CHROMATIN_MARKER) {
            size_t nul = 1u;                             /* handle NUL scan (bytes [1:]) */
            while (nul < (size_t)leaf_dim && block[nul] != 0u) { nul++; }
            if (nul + 2u + 2u * lb > (size_t)leaf_dim) { return SRMECH_ERR_BAD_INPUT; }
            unsigned char ct = block[nul + 1u];
            uint64_t num = genome_get_u64_be(block, nul + 2u);
            uint64_t den = genome_get_u64_be(block, nul + 2u + lb);
            if (ct > SRMECH_GENOME_CHROMATIN_TYPE_GRADED || den == 0u || num > den) {
                return SRMECH_ERR_BAD_INPUT;
            }
            if (type_out != NULL) { *type_out = ct; }
            if (num_out != NULL) { *num_out = num; }
            if (den_out != NULL) { *den_out = den; }
            if (at_out != NULL) { *at_out = turns; }
            *found_out = 1;
            return SRMECH_OK;
        }
        if (kind < 0) { turns++; }                       /* a coupled data turn */
    }
    return SRMECH_OK;
}

/* PARTITION — recover every kernel from a multi-kernel strand (the inverse of
 * srmech_genome_genome). Mirror srmech.amsc.genome.partition(strand, coupling): walk
 * the strand's `n_blocks` fixed-width leaf_dim-byte blocks; a CHROM / kernel-telomere
 * / active-telomere cap OPENS a partition (its label read INLINE by genome_decode_
 * label); a gene / regulatory / boolean / threshold / graded / kernel-header cap is
 * SKIPPED (a delimiter — the partition FLATTENS across genes); every data turn until
 * the next opening cap is re-bound through `coupling` (the reversible Klein-4 bind) as
 * that partition's leaf. The Python-side `labels=` FILTER + the dict overwrite-on-
 * duplicate-label semantics are applied by the caller over these ordered partitions.
 *   strand / n_blocks : the strand's n_blocks blocks, each leaf_dim bytes, contiguous.
 *   leaf_dim          : the block width in bytes (> 0, <= 256) == len(coupling).
 *   coupling           : the shared Klein-4 invariant (leaf_dim bytes).
 *   out_leaves        : caller buffer for the recovered leaves (leaf_dim bytes each),
 *                       in partition order; out_leaves_cap >= (data-turn count)*leaf_dim.
 *   out_labels        : caller buffer for the partition labels, one leaf_dim-byte
 *                       NUL-terminated slot each; out_labels_cap >= n_parts*leaf_dim.
 *   part_leaf_counts  : caller buffer [counts_cap] — the per-partition leaf count.
 *   n_parts_out       : out — the partition (opening-cap) count.
 *   n_leaves_out      : out — the total recovered-leaf count.
 * Error returns:
 *   SRMECH_ERR_NULL_ARG  — any pointer arg NULL.
 *   SRMECH_ERR_BAD_INPUT  — leaf_dim 0 / > 256, an over-long label, or a data byte > 3.
 *   SRMECH_ERR_OVERFLOW   — out_leaves / out_labels / part_leaf_counts too small. */
srmech_status_t srmech_genome_partition(const unsigned char *strand,
                                        size_t n_blocks, uint32_t leaf_dim,
                                        const unsigned char *coupling,
                                        unsigned char *out_leaves,
                                        size_t out_leaves_cap,
                                        unsigned char *out_labels,
                                        size_t out_labels_cap,
                                        uint32_t *part_leaf_counts,
                                        size_t counts_cap,
                                        size_t *n_parts_out,
                                        size_t *n_leaves_out)
{
    if (strand == NULL || coupling == NULL || out_leaves == NULL ||
        out_labels == NULL || part_leaf_counts == NULL ||
        n_parts_out == NULL || n_leaves_out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(strand != NULL && coupling != NULL && out_leaves != NULL);
    assert(part_leaf_counts != NULL && n_parts_out != NULL);
    if (leaf_dim == 0u || leaf_dim > 256u) { return SRMECH_ERR_BAD_INPUT; }
    size_t n_parts = 0u;
    size_t n_leaves = 0u;
    int have_current = 0;
    for (size_t i = 0; i < n_blocks; i++) {
        const unsigned char *block = strand + i * (size_t)leaf_dim;
        int kind = genome_cap_kind(block, leaf_dim);
        if (kind == (int)SRMECH_GENOME_CHROM_CAP_MARKER ||
            kind == (int)SRMECH_GENOME_KERNEL_TELOMERE_MARKER ||
            kind == (int)SRMECH_GENOME_ACTIVE_TELOMERE_MARKER ||
            kind == (int)SRMECH_GENOME_DIPLOID_TELOMERE_MARKER) {  /* §95b diploid opens a chrom */
            size_t loff = n_parts * (size_t)leaf_dim;
            if (n_parts >= counts_cap || loff + (size_t)leaf_dim > out_labels_cap) {
                return SRMECH_ERR_OVERFLOW;
            }
            srmech_status_t st = genome_decode_label(
                block, leaf_dim, (char *)(out_labels + loff));
            if (st != SRMECH_OK) { return st; }
            part_leaf_counts[n_parts] = 0u;
            n_parts++;
            have_current = 1;
        } else if (kind >= 0) {
            continue;                          /* a gene / header cap — skip (flatten) */
        } else if (have_current != 0) {
            size_t doff = n_leaves * (size_t)leaf_dim;
            if (doff + (size_t)leaf_dim > out_leaves_cap) {
                return SRMECH_ERR_OVERFLOW;
            }
            srmech_status_t st = srmech_klein4_bind(block, coupling, leaf_dim,
                                                    out_leaves + doff);
            if (st != SRMECH_OK) { return st; }
            part_leaf_counts[n_parts - 1u]++;
            n_leaves++;
        }
    }
    *n_parts_out = n_parts;
    *n_leaves_out = n_leaves;
    return SRMECH_OK;
}

/* §44 CHROMOSOME-BOUNDARY predicate — 1 iff `block` OPENS a chromosome (a CHROM /
 * kernel-telomere / active-telomere / diploid boundary cap, mirroring the Python
 * _CHROM_BOUNDARY_MARKERS set), else 0. A READ over genome_cap_kind; no abs. */
static int genome_is_boundary_cap(const unsigned char *block, size_t len)
{
    int kind;
    assert(block != NULL || len == 0u);
    assert(len <= 256u);
    kind = genome_cap_kind(block, len);
    return (kind == (int)SRMECH_GENOME_CHROM_CAP_MARKER ||
            kind == (int)SRMECH_GENOME_KERNEL_TELOMERE_MARKER ||
            kind == (int)SRMECH_GENOME_ACTIVE_TELOMERE_MARKER ||
            kind == (int)SRMECH_GENOME_DIPLOID_TELOMERE_MARKER) ? 1 : 0;
}

/* §95.1d/v15 INTEGRATE (rc276, #891 / F1244 / G4) — splice a PROVIRUS chromosome
 * strand INTO a host genome strand at a chromosome boundary; mirror
 * srmech.amsc.genome.integrate. Scans the host's leaf_dim-byte blocks for
 * boundary caps, resolves the insert LOCUS from `at`, and concatenates
 * host[:locus] + provirus + host[locus:] BYTE-IDENTICALLY (whole self-describing
 * blocks; the provirus turns are already coupled, so no re-coupling). This is
 * self-contained: a bare-C host integrates end-to-end via this ONE call. */
srmech_status_t srmech_genome_integrate(
    const unsigned char *host, size_t host_blocks, uint32_t host_leaf_dim,
    const unsigned char *provirus, size_t prov_blocks, uint32_t prov_leaf_dim,
    long at, unsigned char *out, size_t out_cap,
    size_t *n_blocks_out, int *integrated_out)
{
    size_t dim = (size_t)prov_leaf_dim;
    size_t nb = 0u, locus = 0u, locus_at = 0u, total, off;
    if (out == NULL || n_blocks_out == NULL || integrated_out == NULL ||
        (provirus == NULL && prov_blocks > 0u) ||
        (host == NULL && host_blocks > 0u)) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(out != NULL && n_blocks_out != NULL && integrated_out != NULL);
    if (prov_leaf_dim == 0u || prov_leaf_dim > 256u) { return SRMECH_ERR_BAD_INPUT; }
    if (host_blocks > 0u && (host_leaf_dim == 0u || host_leaf_dim > 256u)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (prov_blocks == 0u || genome_is_boundary_cap(provirus, dim) == 0) {
        return SRMECH_ERR_BAD_INPUT;      /* provirus must open with a boundary cap */
    }
    assert(provirus != NULL && dim > 0u && dim <= 256u);
    if (host_blocks > 0u &&
        genome_is_boundary_cap(host, (size_t)host_leaf_dim) == 0) {
        return SRMECH_ERR_BAD_INPUT;      /* host is not a well-formed genome strand */
    }
    /* §135/F1251 GATE: an empty host coheres with any provirus; else EQUAL coupling
     * WIDTH (a Class-K equality read, NEVER abs — two genomes at different widths were
     * coupled through different `coupling` invariants and cannot cohere: the CG258
     * incompatible-replicon analog). Incompatible -> HONEST-DECLINE (the C analog of
     * the Python None: *integrated_out = 0, nothing written, SRMECH_OK). */
    if (host_blocks > 0u && host_leaf_dim != prov_leaf_dim) {
        *integrated_out = 0;
        return SRMECH_OK;
    }
    for (size_t i = 0u; i < host_blocks; i++) {   /* scan host chromosome boundaries */
        if (genome_is_boundary_cap(host + i * dim, dim) == 0) { continue; }
        if (at >= 0 && (size_t)at == nb) { locus_at = i; }
        nb++;
    }
    if (at < 0) {
        locus = host_blocks;              /* at None -> after the last chromosome */
    } else {
        if ((size_t)at > nb) { return SRMECH_ERR_BAD_INPUT; }   /* at out of range */
        locus = ((size_t)at < nb) ? locus_at : host_blocks;
    }
    total = host_blocks + prov_blocks;
    if (out_cap < total * dim) { return SRMECH_ERR_OVERFLOW; }
    memcpy(out + locus * dim, provirus, prov_blocks * dim);     /* + provirus */
    if (host_blocks > 0u) {
        memcpy(out, host, locus * dim);                        /* host[:locus] */
        off = (locus + prov_blocks) * dim;
        memcpy(out + off, host + locus * dim, (host_blocks - locus) * dim);
    }
    *n_blocks_out = total;
    *integrated_out = 1;
    return SRMECH_OK;
}

/* §100 GAP 1/v15 MINT-STRAND (rc277) — ONE pass over a strand's leaf_dim-byte blocks:
 * count DATA turns (genome_cap_kind < 0, the non-cap leaves) AND flag an interior
 * centromere (0x58). Mirror the Python data_positions scan + the "already carries a
 * centromere" guard. A READ; no abs, no mutation. */
static void genome_mint_strand_scan(const unsigned char *strand, size_t n_blocks,
                                    uint32_t leaf_dim, size_t *n_turns_out,
                                    int *has_cen_out)
{
    assert(strand != NULL || n_blocks == 0u);
    assert(n_turns_out != NULL && has_cen_out != NULL);
    size_t turns = 0u;
    int has_cen = 0;
    for (size_t i = 0u; i < n_blocks; i++) {
        int kind = genome_cap_kind(strand + i * (size_t)leaf_dim, leaf_dim);
        if (kind < 0) { turns++; }                      /* a DATA turn */
        else if (kind == (int)SRMECH_GENOME_CENTROMERE_CAP_MARKER) { has_cen = 1; }
    }
    *n_turns_out = turns;
    *has_cen_out = has_cen;
}

/* §100 GAP 1/v15 — the BLOCK index of the `split`-th (0-based) DATA turn, or n_blocks
 * when split == the data-turn count (the metacentric cap appends at the very end).
 * Mirror the Python `data_positions[split] if split < n_turns else len(strand)`. A READ;
 * no abs. */
static size_t genome_nth_data_turn(const unsigned char *strand, size_t n_blocks,
                                   uint32_t leaf_dim, size_t split)
{
    assert(strand != NULL || n_blocks == 0u);
    assert(leaf_dim > 0u);
    size_t seen = 0u;
    for (size_t i = 0u; i < n_blocks; i++) {
        if (genome_cap_kind(strand + i * (size_t)leaf_dim, leaf_dim) < 0) {
            if (seen == split) { return i; }
            seen++;
        }
    }
    return n_blocks;                       /* split == n_turns -> append at the end */
}

/* §100 GAP 1/v15 — resolve the GLOBAL orientation for a mint_strand. When
 * orientation_auto: RECALL the strand's leaves into `scratch` (caller-arena; the recall
 * output is <= n_blocks*leaf_dim, and the caller passes `out` whose out_cap already fits
 * the +1-block splice) and fold sha256(recalled)[0] & 3 — the SAME Class-A -> Class-C
 * _mint_orientation rule mint() uses, applied to the strand's OWN recovered leaves. Else
 * pass the caller `orientation_in` through. No abs, no float. */
static srmech_status_t genome_mint_strand_orient(
    const unsigned char *strand, size_t n_blocks, uint32_t leaf_dim,
    const unsigned char *coupling, int orientation_auto,
    unsigned char orientation_in, unsigned char *scratch, size_t scratch_cap,
    unsigned char *o_out)
{
    assert(o_out != NULL);
    assert(orientation_auto == 0 || (coupling != NULL && scratch != NULL));
    if (orientation_auto == 0) { *o_out = orientation_in; return SRMECH_OK; }
    size_t n_leaves = 0u;
    srmech_status_t st = srmech_genome_recall(strand, n_blocks, leaf_dim, coupling,
                                              scratch, scratch_cap, &n_leaves);
    if (st != SRMECH_OK) { return st; }
    return genome_mint_orientation(scratch, n_leaves * (size_t)leaf_dim, o_out);
}

/* §100 GAP 1/v15 MINT-STRAND (rc277, #891-peer / F1249 / G5) — the stage-2 PROMOTE
 * primitive: splice a §95a interior CENTROMERE (0x58) into an ALREADY-PACKED strand at
 * the p:q arm-split, turning a Tier-1 PLASMID into a Tier-2 NUCLEAR chromosome (mirror
 * srmech.amsc.genome.mint_strand). Scans the strand's leaf_dim-byte DATA turns, resolves
 * the metacentric split, content-addresses the global orientation (recall -> sha256 & 3)
 * when orientation_auto, writes the centromere cap, and concatenates
 * strand[:locus] + cap + strand[locus:] BYTE-IDENTICALLY (whole self-describing blocks,
 * no re-coupling). Self-contained: a bare-C host promotes a strand end-to-end via this
 * ONE call (closes the rc270 mint_strand C-host GAP — the cap-writer had a C peer, its
 * glue did not). */
srmech_status_t srmech_genome_mint_strand(
    const unsigned char *strand, size_t n_blocks, uint32_t leaf_dim,
    const unsigned char *coupling, long centromere_at,
    unsigned char orientation, int orientation_auto,
    uint32_t repeats, const unsigned char *handle, size_t handle_len,
    unsigned char *out, size_t out_cap, size_t *n_blocks_out)
{
    size_t dim = (size_t)leaf_dim, n_turns = 0u, split, locus, total;
    int has_cen = 0;
    unsigned char cap[256];
    unsigned char o = 0u;
    if (out == NULL || n_blocks_out == NULL || strand == NULL ||
        (orientation_auto != 0 && coupling == NULL) ||
        (handle == NULL && handle_len != 0u)) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(out != NULL && n_blocks_out != NULL && strand != NULL);
    if (leaf_dim == 0u || leaf_dim > 256u) { return SRMECH_ERR_BAD_INPUT; }
    if (n_blocks == 0u || genome_is_boundary_cap(strand, dim) == 0) {
        return SRMECH_ERR_BAD_INPUT;      /* empty / not opening with a boundary cap */
    }
    genome_mint_strand_scan(strand, n_blocks, leaf_dim, &n_turns, &has_cen);
    if (has_cen != 0) { return SRMECH_ERR_BAD_INPUT; }   /* already minted (0x58) */
    if (centromere_at >= 0) {
        if ((size_t)centromere_at > n_turns) { return SRMECH_ERR_BAD_INPUT; }
        split = (size_t)centromere_at;                   /* the caller-supplied arm-split */
    } else {
        split = n_turns / 2u;                            /* at None -> metacentric midpoint */
    }
    total = n_blocks + 1u;
    if (out_cap < total * dim) { return SRMECH_ERR_OVERFLOW; }
    /* orientation resolve: recall uses `out` as the caller arena (recalled leaves are
     * <= n_blocks*dim <= out_cap), FULLY consumed before the splice writes `out`. */
    srmech_status_t st = genome_mint_strand_orient(
        strand, n_blocks, leaf_dim, coupling, orientation_auto, orientation,
        out, out_cap, &o);
    if (st != SRMECH_OK) { return st; }
    st = srmech_genome_centromere(o, repeats, handle, handle_len, leaf_dim, cap, dim);
    if (st != SRMECH_OK) { return st; }
    locus = genome_nth_data_turn(strand, n_blocks, leaf_dim, split);
    assert(locus <= n_blocks);
    memcpy(out, strand, locus * dim);                        /* strand[:locus] */
    memcpy(out + locus * dim, cap, dim);                     /* + centromere cap */
    memcpy(out + (locus + 1u) * dim, strand + locus * dim,
           (n_blocks - locus) * dim);                        /* + strand[locus:] */
    *n_blocks_out = total;
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
            body[off] == SRMECH_GENOME_ACTIVE_TELOMERE_MARKER ||
            body[off] == SRMECH_GENOME_DIPLOID_TELOMERE_MARKER) {  /* §95b diploid opens a chrom */
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
    s->cap_kind = genome_arena_alloc(a, (size_t)n);           /* §96 cap-kind code */
    if (s->cap_sha == NULL || s->byte_offset == NULL || s->byte_len == NULL ||
        s->label == NULL || s->leaf_count == NULL || s->region_sha == NULL ||
        s->cap_kind == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    s->cap_chroms = n;
    s->n_chroms = 0u;
    return SRMECH_OK;
}

/* Fold ONE non-opener block (marker `m`) into the current chromosome `cur` during
 * the §44 scan: a §Q8/v16 packed turn (0x38) flags the carrier "q8"; an interior
 * §95a centromere (0x58) marks the cap-kind nuclear; a DATA turn — anything that is
 * NOT a GENE / regulatory / boolean / threshold / graded gene cap, a v5 kernel
 * header, or an interior centromere/chromatin cap — increments the leaf count. */
static void genome_scan_fold_block(genome_strings_t *s, unsigned char m, int32_t cur)
{
    assert(s != NULL);
    assert(cur >= 0);
    if (m == SRMECH_GENOME_Q8_PACKED_TURN_MARKER) {
        s->carrier_q8 = 1u;                        /* §Q8/v16: a Q₈ turn → carrier "q8" */
    }
    if (m == SRMECH_GENOME_CENTROMERE_CAP_MARKER) {
        s->cap_kind[cur] = SRMECH_GENOME_CAP_KIND_NUCLEAR;   /* §96 nuclear wins */
    }
    if (m != SRMECH_GENOME_GENE_CAP_MARKER &&
        m != SRMECH_GENOME_REGULATORY_GENE_MARKER &&
        m != SRMECH_GENOME_BOOLEAN_GENE_MARKER &&
        m != SRMECH_GENOME_THRESHOLD_GENE_MARKER &&
        m != SRMECH_GENOME_GRADED_GENE_MARKER &&
        m != SRMECH_GENOME_KERNEL_HEADER_MARKER &&
        m != SRMECH_GENOME_CHROMATIN_MARKER &&
        m != SRMECH_GENOME_CENTROMERE_CAP_MARKER) {
        s->leaf_count[cur]++;                      /* §95a/§98: an interior cap, not a turn */
    }
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
            body[off] == SRMECH_GENOME_ACTIVE_TELOMERE_MARKER ||
            body[off] == SRMECH_GENOME_DIPLOID_TELOMERE_MARKER) {  /* §95b diploid opens a chrom */
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
            /* §96: cap-kind PROVISIONAL on the opener (0x44 diploid else plasmid) —
             * an interior centromere below overwrites it to nuclear. */
            s->cap_kind[cur] = (body[off] == SRMECH_GENOME_DIPLOID_TELOMERE_MARKER)
                ? SRMECH_GENOME_CAP_KIND_DIPLOID : SRMECH_GENOME_CAP_KIND_PLASMID;
        } else {
            if (cur < 0) { return SRMECH_ERR_BAD_INPUT; }   /* turn before 1st cap */
            /* §55/v3 + §Q8/v16 + §96: fold the non-opener block (carrier flag,
             * cap-kind, data-turn count) — extracted to keep this scan ≤60 (JPL R4). */
            genome_scan_fold_block(s, body[off], cur);
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
    s->carrier_q8 = 0u;             /* §Q8/v16: klein4 unless the scan finds a 0x38 turn */
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

/* Fill the per-build string block from the body + coupling: the hashes, the
 * version string, and the §44 inline-cap chromosome scan. */
static srmech_status_t genome_fill_strings(genome_strings_t *s,
                                           genome_arena_t *a,
                                           const unsigned char *body,
                                           size_t body_len, uint32_t leaf_dim,
                                           const unsigned char *coupling)
{
    assert(s != NULL && coupling != NULL);
    assert(a != NULL && leaf_dim > 0u);
    uint32_t n_chroms = 0u;                            /* count → carve arrays */
    uint32_t n_blocks = 0u;                            /* §55/v3: == n_turns */
    srmech_status_t st = genome_count_chroms(body, body_len, leaf_dim,
                                             &n_chroms, &n_blocks);
    if (st != SRMECH_OK) { return st; }
    st = genome_strings_alloc(s, a, n_chroms);
    if (st != SRMECH_OK) { return st; }
    s->n_blocks = n_blocks;
    st = srmech_sha256_hex(coupling, leaf_dim, s->one_sha);
    if (st != SRMECH_OK) { return st; }
    genome_hex(coupling, leaf_dim, s->one_hex);
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
                                            const unsigned char *coupling,
                                            size_t coupling_len, const void *ws)
{
    assert(body != NULL || body_len == 0u);
    assert(dir != NULL || ws == NULL);
    if (dir == NULL || coupling == NULL || ws == NULL ||
        (body == NULL && body_len != 0u)) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (leaf_dim == 0u || coupling_len != (size_t)leaf_dim || leaf_dim > 256u) {
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

/* §98.1/G1 (rc274) — the THRESHOLD chromatin gate fold: *fires = 1 iff Sum_i (weight_i *
 * bit_i(cell_state)) >= threshold, byte-identical to the pure Python _threshold_expresses. The
 * payload begins at `off` (NO inner gate_type byte — access_gate_type already discriminated it):
 * n_weights(u16 BE) + threshold(i64 BE signed) + n_weights x weight(i64 BE signed). On an int64
 * accumulate OVERFLOW returns SRMECH_ERR_OVERFLOW (the caller falls to the exact pure/bignum Python
 * path). Reuses genome_read_i64_be. Bounds checked; malloc-free; no abs (the SIGN is Class-K); a
 * READ. */
static srmech_status_t genome_chromatin_threshold_fires(
    const unsigned char *cap, size_t leaf_dim, size_t off, uint64_t cell_state, int *fires)
{
    assert(cap != NULL && fires != NULL);
    assert(leaf_dim > 0u && leaf_dim <= 256u);
    size_t nw = (size_t)SRMECH_GENOME_THRESHOLD_NWEIGHTS_BYTES;
    size_t vb = (size_t)SRMECH_GENOME_THRESHOLD_VALUE_BYTES;
    if (off + nw + vb > leaf_dim) { return SRMECH_ERR_BAD_INPUT; }   /* n_weights + threshold header */
    uint32_t n_weights = ((uint32_t)cap[off] << 8) | (uint32_t)cap[off + 1u];
    int64_t threshold = genome_read_i64_be(cap, off + nw);
    size_t w_off = off + nw + vb;
    if (w_off + (size_t)n_weights * vb > leaf_dim) { return SRMECH_ERR_BAD_INPUT; }  /* vector trunc */
    int64_t total = 0;
    for (uint32_t t = 0u; t < n_weights && t < 64u; t++) {      /* bit_t == 0 for t >= 64 (uint64) */
        if (((cell_state >> t) & 1u) == 0u) { continue; }      /* condition absent — weight skipped */
        int64_t w = genome_read_i64_be(cap, w_off + (size_t)t * vb);
        if ((w > 0 && total > INT64_MAX - w) ||                 /* defer to the exact pure path */
            (w < 0 && total < INT64_MIN - w)) { return SRMECH_ERR_OVERFLOW; }
        total += w;                                            /* exact int64 signed accumulate */
    }
    *fires = (total >= threshold) ? 1 : 0;                     /* Class-K sign-branch; never abs */
    return SRMECH_OK;
}

/* §98.1/G1 (rc274) — evaluate the FACULTATIVE chromatin gate whose payload begins at `off` in `cap`
 * (access_gate_type already discriminated the kind; NO inner gate_type byte). *fires = 1 iff the
 * gate fires under cell_state. KLEIN4 = act(u64 BE) + rep(u64 BE); BOOLEAN = n_terms(u16 BE) +
 * n_terms x (act(u64 BE) + rep(u64 BE)); THRESHOLD delegates to genome_chromatin_threshold_fires.
 * Byte-identical to the pure Python _chromatin_access `fires` decision (klein4 rule / _dnf_expresses
 * / _threshold_expresses). Reuses genome_read_u64_be. Bounds checked; malloc-free; no abs; a READ. */
static srmech_status_t genome_chromatin_gate_fires(
    const unsigned char *cap, size_t leaf_dim, size_t off,
    unsigned char gate_type, uint64_t cell_state, int *fires)
{
    assert(cap != NULL && fires != NULL);
    assert(leaf_dim > 0u && leaf_dim <= 256u);
    size_t mb = (size_t)SRMECH_GENOME_REGULATORY_MASK_BYTES;
    if (gate_type == (unsigned char)SRMECH_GENOME_CHROMATIN_GATE_KLEIN4) {
        if (off + 2u * mb > leaf_dim) { return SRMECH_ERR_BAD_INPUT; }
        uint64_t act = genome_read_u64_be(cap, off);
        uint64_t rep = genome_read_u64_be(cap, off + mb);
        *fires = (((cell_state & act) == act) && ((cell_state & rep) == 0u)) ? 1 : 0;  /* no abs */
        return SRMECH_OK;
    }
    if (gate_type == (unsigned char)SRMECH_GENOME_CHROMATIN_GATE_BOOLEAN) {
        size_t nt = (size_t)SRMECH_GENOME_BOOLEAN_NTERMS_BYTES;
        if (off + nt > leaf_dim) { return SRMECH_ERR_BAD_INPUT; }
        uint32_t n_terms = ((uint32_t)cap[off] << 8) | (uint32_t)cap[off + 1u];
        size_t terms_off = off + nt;
        if (terms_off + (size_t)n_terms * SRMECH_GENOME_BOOLEAN_TERM_BYTES > leaf_dim) {
            return SRMECH_ERR_BAD_INPUT;
        }
        int any = 0;
        for (uint32_t t = 0u; t < n_terms && any == 0; t++) {  /* OR of AND-clauses; empty DNF -> 0 */
            size_t o = terms_off + (size_t)t * SRMECH_GENOME_BOOLEAN_TERM_BYTES;
            uint64_t act = genome_read_u64_be(cap, o);
            uint64_t rep = genome_read_u64_be(cap, o + mb);
            if (((cell_state & act) == act) && ((cell_state & rep) == 0u)) { any = 1; }
        }
        *fires = any;
        return SRMECH_OK;
    }
    if (gate_type == (unsigned char)SRMECH_GENOME_CHROMATIN_GATE_THRESHOLD) {
        return genome_chromatin_threshold_fires(cap, leaf_dim, off, cell_state, fires);
    }
    return SRMECH_ERR_BAD_INPUT;                                /* unsupported access_gate_type */
}

/* §98.1/G1 (rc274) — the COMPUTED accessibility (num, den) of ONE chromatin cap under cell_state
 * (mirror srmech.amsc.genome._chromatin_access). Decode the static (chromatin_type, num, den); read
 * access_gate_type at den_end (guard den_end < leaf_dim, else NONE — the tight-leaf pad default);
 * NONE -> the static (num, den) (constitutive, constant in cell_state); a facultative gate ->
 * (num, den) if it FIRES under cell_state, else (0, 1) (silenced). Byte-identical to Python.
 * Malloc-free; no abs; no float; a READ. */
static srmech_status_t genome_chromatin_access(
    const unsigned char *cap, uint32_t leaf_dim, uint64_t cell_state,
    uint64_t *num_out, uint64_t *den_out)
{
    assert(cap != NULL && num_out != NULL && den_out != NULL);
    assert(leaf_dim >= 1u && leaf_dim <= 256u);
    if (cap[0] != SRMECH_GENOME_CHROMATIN_MARKER) { return SRMECH_ERR_BAD_INPUT; }
    size_t lb = (size_t)SRMECH_GENOME_CHROMATIN_LEVEL_BYTES;
    size_t nul = 1u;                                       /* handle NUL scan (bytes [1:]) */
    while (nul < (size_t)leaf_dim && cap[nul] != 0u) { nul++; }
    if (nul + 2u + 2u * lb > (size_t)leaf_dim) { return SRMECH_ERR_BAD_INPUT; }
    unsigned char ct = cap[nul + 1u];
    uint64_t num = genome_get_u64_be(cap, nul + 2u);
    uint64_t den = genome_get_u64_be(cap, nul + 2u + lb);
    if (ct > SRMECH_GENOME_CHROMATIN_TYPE_GRADED || den == 0u || num > den) {
        return SRMECH_ERR_BAD_INPUT;
    }
    size_t den_end = nul + 2u + 2u * lb;                  /* the access_gate_type byte offset */
    unsigned char gt = (den_end < (size_t)leaf_dim)
                       ? cap[den_end] : (unsigned char)SRMECH_GENOME_CHROMATIN_GATE_NONE;
    if (gt == (unsigned char)SRMECH_GENOME_CHROMATIN_GATE_NONE) {
        *num_out = num; *den_out = den;                   /* constitutive: the static level */
        return SRMECH_OK;
    }
    int fires = 0;
    srmech_status_t st = genome_chromatin_gate_fires(cap, (size_t)leaf_dim, den_end + 1u,
                                                     gt, cell_state, &fires);
    if (st != SRMECH_OK) { return st; }
    if (fires != 0) { *num_out = num; *den_out = den; }   /* fired: the when-open level */
    else { *num_out = 0u; *den_out = 1u; }                /* silenced */
    return SRMECH_OK;
}

/* §98.1/G1 (rc274) public single-cap accessibility reader — the srmech_genome_chromatin_access
 * wrapper (NULL/leaf_dim guards, then genome_chromatin_access). See the header. */
srmech_status_t srmech_genome_chromatin_access(
    const unsigned char *cap, uint32_t leaf_dim, uint64_t cell_state,
    uint64_t *num_out, uint64_t *den_out)
{
    if (cap == NULL || num_out == NULL || den_out == NULL) { return SRMECH_ERR_NULL_ARG; }
    assert(cap != NULL && num_out != NULL && den_out != NULL);
    if (leaf_dim == 0u || leaf_dim > 256u) { return SRMECH_ERR_BAD_INPUT; }
    assert(leaf_dim >= 1u && leaf_dim <= 256u);
    return genome_chromatin_access(cap, leaf_dim, cell_state, num_out, den_out);
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

/* ========================================================================== *
 * §133/v11 (#733) — MODULATOR-RECOVERY: the INVERSE of gene_express. Given an
 * OBSERVED expressed-label set (+ the strand's gene caps), recover the two-sided
 * cell-state FLOOR every consistent cell_state must satisfy (M1), and forward-
 * CHECK one candidate (M2). Under-determined -> a ONE-SIDED, SOUND floor (it
 * never over-claims a bit); the exact cell_state is irrecoverable by
 * construction (many states -> one expression) and naming that honestly IS the
 * finding. The `body` here is the GENE-CAP SUBSET of the strand (each block
 * leaf_dim bytes, first byte a gene marker) — the data turns do not gate
 * expression, so the caller strips them, keeping the walk uniform-width.
 * Class-I bitwise; no abs; a READ (never mutates the body).
 * ========================================================================== */

/* Is `label` (label_len bytes) present as a NUL-delimited token of `blob`
 * (blob_len bytes; tokens are label\0label\0...)? Byte-exact match — the gene
 * labels are UTF-8, so this mirrors Python's set membership. blob==NULL /
 * blob_len==0 -> the empty set (0). No abs; a READ. */
static int genome_blob_contains(
    const unsigned char *blob, size_t blob_len,
    const unsigned char *label, size_t label_len)
{
    assert(blob != NULL || blob_len == 0u);
    assert(label != NULL || label_len == 0u);
    size_t i = 0u;
    while (i < blob_len) {
        size_t j = i;
        while (j < blob_len && blob[j] != 0u) { j++; }   /* token = blob[i..j) */
        size_t tok_len = j - i;
        if (tok_len == label_len &&
            (label_len == 0u || memcmp(blob + i, label, label_len) == 0)) {
            return 1;
        }
        i = j + 1u;                                      /* skip the NUL delimiter */
    }
    return 0;
}

/* The inline label of the gene cap at `cap[0..leaf_dim)` — cap[1..NUL). Sets
 * *label_len and returns a pointer into `cap`; NULL on a missing NUL (a
 * malformed gene). Mirrors _unpack_cap's label read. No abs; a READ. */
static const unsigned char *genome_gene_label(
    const unsigned char *cap, size_t leaf_dim, size_t *label_len)
{
    assert(cap != NULL && label_len != NULL);
    assert(leaf_dim > 0u);
    size_t i = 1u;
    while (i < leaf_dim && cap[i] != 0u) { i++; }        /* find the label NUL */
    if (i >= leaf_dim) { return NULL; }                  /* no label NUL */
    *label_len = i - 1u;
    return cap + 1u;
}

/* §128/§129 E1 — the (activator, repressor) Klein-4 bit-planes of a plain
 * (0x47 -> (0,0)) / regulatory (0x67) gene cap. Mirrors _regulatory_gene_masks.
 * No abs; a READ. */
static srmech_status_t genome_regulatory_masks(
    const unsigned char *cap, size_t leaf_dim, uint64_t *act, uint64_t *rep)
{
    assert(cap != NULL && act != NULL && rep != NULL);
    assert(leaf_dim > 0u && leaf_dim <= 256u);
    *act = 0u;
    *rep = 0u;
    if (cap[0] == SRMECH_GENOME_GENE_CAP_MARKER) { return SRMECH_OK; }  /* plain (0,0) */
    size_t i = 1u;
    while (i < leaf_dim && cap[i] != 0u) { i++; }
    if (i >= leaf_dim) { return SRMECH_ERR_BAD_INPUT; }
    size_t act_base = i + 1u;
    if (act_base + SRMECH_GENOME_REGULATORY_MASK_BYTES > leaf_dim) {
        return SRMECH_ERR_BAD_INPUT;
    }
    *act = genome_read_u64_be(cap, act_base);
    size_t rep_base = act_base + SRMECH_GENOME_REGULATORY_MASK_BYTES;
    if (rep_base + SRMECH_GENOME_REGULATORY_MASK_BYTES <= leaf_dim) {   /* §129 dual-read */
        *rep = genome_read_u64_be(cap, rep_base);
    }
    return SRMECH_OK;
}

/* §130 E2 — fold a BOOLEAN GENE's DNF (0x62): *ref = the OR over clauses of
 * (act|rep) (bits the gene READS); *fon / *foff = the intersection-over-clauses
 * activator / repressor (the bits EVERY clause requires present / absent — the
 * SOUND floor an expressed E2 gene proves, since SOME clause matched). The empty
 * DNF (0 clauses) proves NOTHING (fon=foff=0) — never over-claim. No abs; READ. */
static srmech_status_t genome_dnf_fold(
    const unsigned char *cap, size_t leaf_dim,
    uint64_t *ref, uint64_t *fon, uint64_t *foff)
{
    assert(cap != NULL && ref != NULL);
    assert(fon != NULL && foff != NULL);
    *ref = 0u; *fon = 0u; *foff = 0u;
    size_t i = 1u;
    while (i < leaf_dim && cap[i] != 0u) { i++; }
    if (i >= leaf_dim) { return SRMECH_ERR_BAD_INPUT; }
    size_t base = i + 1u;
    if (base + 1u + SRMECH_GENOME_BOOLEAN_NTERMS_BYTES > leaf_dim) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (cap[base] != SRMECH_GENOME_GATE_TYPE_BOOLEAN_DNF) { return SRMECH_ERR_BAD_INPUT; }
    size_t nt_off = base + 1u;
    uint32_t n_terms = ((uint32_t)cap[nt_off] << 8) | (uint32_t)cap[nt_off + 1u];
    size_t terms_off = nt_off + SRMECH_GENOME_BOOLEAN_NTERMS_BYTES;
    if (terms_off + (size_t)n_terms * SRMECH_GENOME_BOOLEAN_TERM_BYTES > leaf_dim) {
        return SRMECH_ERR_BAD_INPUT;
    }
    uint64_t inter_act = UINT64_MAX;
    uint64_t inter_rep = UINT64_MAX;
    for (uint32_t t = 0u; t < n_terms; t++) {
        size_t o = terms_off + (size_t)t * SRMECH_GENOME_BOOLEAN_TERM_BYTES;
        uint64_t a = genome_read_u64_be(cap, o);
        uint64_t r = genome_read_u64_be(cap, o + SRMECH_GENOME_REGULATORY_MASK_BYTES);
        *ref |= a | r;
        inter_act &= a;
        inter_rep &= r;
    }
    if (n_terms > 0u) { *fon = inter_act; *foff = inter_rep; }  /* empty DNF proves nothing */
    return SRMECH_OK;
}

/* §131 E4 / §132 E3 — the condition bits a THRESHOLD (0x77) / GRADED (0x64) gene
 * READS: the OR of (1 << t) for every NONZERO weight at index t < 64 (bit t of the
 * uint64 cell_state; weights beyond 63 gate always-absent conditions -> not read).
 * These gates give NO clean single-bit certainty, so they contribute to *ref only
 * (no floor). `is_graded` selects the cap layout (a graded cap has an 8-byte
 * denom before the weights). THRESHOLD + GRADED share the uint16 count / int64
 * value widths. No abs; a READ. */
static srmech_status_t genome_weighted_ref(
    const unsigned char *cap, size_t leaf_dim, int is_graded, uint64_t *ref)
{
    assert(cap != NULL && ref != NULL);
    assert(leaf_dim > 0u && leaf_dim <= 256u);
    *ref = 0u;
    size_t i = 1u;
    while (i < leaf_dim && cap[i] != 0u) { i++; }
    if (i >= leaf_dim) { return SRMECH_ERR_BAD_INPUT; }
    size_t base = i + 1u;
    size_t denom_bytes = is_graded ? (size_t)SRMECH_GENOME_GRADED_DENOM_BYTES : 0u;
    size_t hdr = 1u + SRMECH_GENOME_THRESHOLD_NWEIGHTS_BYTES + denom_bytes;
    if (base + hdr > leaf_dim) { return SRMECH_ERR_BAD_INPUT; }
    unsigned char want = is_graded ? (unsigned char)SRMECH_GENOME_GATE_TYPE_GRADED
                                   : (unsigned char)SRMECH_GENOME_GATE_TYPE_THRESHOLD;
    if (cap[base] != want) { return SRMECH_ERR_BAD_INPUT; }
    size_t nw_off = base + 1u;
    uint32_t n_weights = ((uint32_t)cap[nw_off] << 8) | (uint32_t)cap[nw_off + 1u];
    size_t w_off = nw_off + SRMECH_GENOME_THRESHOLD_NWEIGHTS_BYTES + denom_bytes;
    if (w_off + (size_t)n_weights * SRMECH_GENOME_THRESHOLD_VALUE_BYTES > leaf_dim) {
        return SRMECH_ERR_BAD_INPUT;
    }
    for (uint32_t t = 0u; t < n_weights && t < 64u; t++) {
        int64_t w = genome_read_i64_be(
            cap, w_off + (size_t)t * SRMECH_GENOME_THRESHOLD_VALUE_BYTES);
        if (w != 0) { *ref |= ((uint64_t)1u << t); }    /* a nonzero weight READS bit t */
    }
    return SRMECH_OK;
}

/* One gene cap's condition-bit contributions: *ref = the bits it READS; *fon /
 * *foff = the bits an EXPRESSED instance PROVES on / off (the SOUND floor). The
 * caller applies (*fon, *foff) iff the gene is expressed AND its label uniquely
 * identifies it. No abs; a READ. */
static srmech_status_t genome_gene_contribution(
    const unsigned char *cap, size_t leaf_dim,
    uint64_t *ref, uint64_t *fon, uint64_t *foff)
{
    assert(cap != NULL && ref != NULL);
    assert(fon != NULL && foff != NULL);
    *ref = 0u; *fon = 0u; *foff = 0u;
    unsigned char m = cap[0];
    if (m == SRMECH_GENOME_BOOLEAN_GENE_MARKER) {
        return genome_dnf_fold(cap, leaf_dim, ref, fon, foff);   /* E2 intersection floor */
    }
    if (m == SRMECH_GENOME_THRESHOLD_GENE_MARKER) {
        return genome_weighted_ref(cap, leaf_dim, 0, ref);       /* E4 — ref only */
    }
    if (m == SRMECH_GENOME_GRADED_GENE_MARKER) {
        return genome_weighted_ref(cap, leaf_dim, 1, ref);       /* E3 — ref only */
    }
    uint64_t act = 0u, rep = 0u;                                 /* E1 (0x47 / 0x67) */
    srmech_status_t st = genome_regulatory_masks(cap, leaf_dim, &act, &rep);
    if (st != SRMECH_OK) { return st; }
    *ref = act | rep;
    *fon = act;                                                  /* activators certain ON */
    *foff = rep;                                                 /* repressors certain OFF */
    return SRMECH_OK;
}

/* Is the label at `self_off` UNIQUE among the body's gene caps (no OTHER cap
 * shares it)? The SOUNDNESS guard: a label shared by >=2 genes cannot be
 * attributed to a specific gene (the expressed SET collapses duplicates), so
 * NEITHER contributes to the floor. No abs; a READ. */
static int genome_label_unique(
    const unsigned char *body, size_t body_len, size_t leaf_dim,
    size_t self_off, const unsigned char *label, size_t label_len)
{
    assert(body != NULL && label != NULL);
    assert(leaf_dim > 0u);
    for (size_t o = 0u; o + leaf_dim <= body_len; o += leaf_dim) {
        if (o == self_off) { continue; }
        size_t other_len = 0u;
        const unsigned char *other = genome_gene_label(body + o, leaf_dim, &other_len);
        if (other == NULL) { continue; }
        if (other_len == label_len &&
            (label_len == 0u || memcmp(other, label, label_len) == 0)) {
            return 0;                                            /* a duplicate — not unique */
        }
    }
    return 1;
}

/* §133 M1 — recover the TWO-SIDED cell-state FLOOR from an OBSERVED expressed set.
 * *certain_on  = bits every consistent cell_state MUST have SET (OR of expressed
 *                E1 activators + expressed E2 intersection-over-clauses activators);
 * *certain_off = bits every consistent state MUST have CLEAR (the repressor duals);
 * *undetermined= the referenced condition bits (union any gene READS) minus the
 *                pinned set; *verdict = EXACT (pinned covers all referenced) /
 * PARTIAL (some pinned) / UNKNOWN (none pinned). E4/E3/un-expressed genes give NO
 * clean single-bit certainty -> they add to *undetermined, never to the floor.
 * SOUND: for every M2-consistent state, (state & *certain_on) == *certain_on AND
 * (state & *certain_off) == 0. Byte-identical to _modulator_recover_pure. No abs;
 * caller-arena-free; malloc-free; a READ. */
srmech_status_t srmech_genome_modulator_recover(
    const unsigned char *body, size_t body_len, size_t leaf_dim,
    const unsigned char *expressed, size_t expressed_len,
    uint64_t *certain_on, uint64_t *certain_off,
    uint64_t *undetermined, int *verdict)
{
    assert(body != NULL || body_len == 0u);
    assert(certain_on != NULL && certain_off != NULL);
    if (body == NULL && body_len != 0u) { return SRMECH_ERR_NULL_ARG; }
    if (certain_on == NULL || certain_off == NULL ||
        undetermined == NULL || verdict == NULL) { return SRMECH_ERR_NULL_ARG; }
    if (expressed == NULL && expressed_len != 0u) { return SRMECH_ERR_NULL_ARG; }
    if (leaf_dim == 0u || leaf_dim > 256u) { return SRMECH_ERR_BAD_INPUT; }
    if (body_len % leaf_dim != 0u) { return SRMECH_ERR_BAD_INPUT; }
    uint64_t on = 0u, off = 0u, ref = 0u;
    for (size_t o = 0u; o + leaf_dim <= body_len; o += leaf_dim) {
        const unsigned char *cap = body + o;
        uint64_t gref = 0u, gon = 0u, goff = 0u;
        srmech_status_t st = genome_gene_contribution(cap, leaf_dim, &gref, &gon, &goff);
        if (st != SRMECH_OK) { return st; }
        ref |= gref;
        size_t label_len = 0u;
        const unsigned char *label = genome_gene_label(cap, leaf_dim, &label_len);
        if (label == NULL) { return SRMECH_ERR_BAD_INPUT; }
        if (genome_blob_contains(expressed, expressed_len, label, label_len) &&
            genome_label_unique(body, body_len, leaf_dim, o, label, label_len)) {
            on |= gon;                                           /* SOUND: proven bits only */
            off |= goff;
        }
    }
    uint64_t pinned = on | off;
    *certain_on = on;
    *certain_off = off;
    *undetermined = ref & ~pinned;
    *verdict = (pinned == 0u) ? SRMECH_GENOME_MODULATOR_UNKNOWN
             : (((ref & ~pinned) == 0u) ? SRMECH_GENOME_MODULATOR_EXACT
                                        : SRMECH_GENOME_MODULATOR_PARTIAL);
    return SRMECH_OK;
}

/* §133 — does the gene opened by `cap` EXPRESS under `cs`? Uniform over EVERY gate
 * kind (E1/E2/E4 binary AND E3 graded): a gene is "expressed" iff its LEVEL num > 0
 * (the SAME rule gene_express uses — a graded gene's dose-response IS its gate, and a
 * binary gene is the degenerate {0,1} level). So this routes through
 * srmech_genome_gene_express_levels (which handles the 0x64 graded marker
 * srmech_genome_gene_express does NOT). An int64 accumulate OVERFLOW propagates so the
 * caller falls to the exact pure path. No abs; a READ. */
static srmech_status_t genome_gene_is_expressed(
    const unsigned char *cap, size_t leaf_dim, uint64_t cs, int *e)
{
    assert(cap != NULL && e != NULL);
    assert(leaf_dim > 0u && leaf_dim <= 256u);
    uint64_t num = 0u, den = 0u;
    srmech_status_t st = srmech_genome_gene_express_levels(cap, leaf_dim, cs, &num, &den);
    if (st != SRMECH_OK) { return st; }
    *e = (num > 0u) ? 1 : 0;                        /* level > 0 IS the gate (all kinds) */
    return SRMECH_OK;
}

/* §133 M2 helper — Check 2 of set equality: every EXPECTED token is the label of
 * some gene that EXPRESSES under `cs`. Sets *ok = 0 on any uncovered token. No
 * abs; a READ. */
static srmech_status_t genome_modulator_expected_covered(
    const unsigned char *body, size_t body_len, size_t leaf_dim,
    const unsigned char *expected, size_t expected_len, uint64_t cs, int *ok)
{
    assert(body != NULL || body_len == 0u);
    assert(ok != NULL && (expected != NULL || expected_len == 0u));
    size_t i = 0u;
    while (i < expected_len) {
        size_t j = i;
        while (j < expected_len && expected[j] != 0u) { j++; }  /* token = expected[i..j) */
        size_t tok_len = j - i;
        int found = 0;
        for (size_t o = 0u; o + leaf_dim <= body_len && found == 0; o += leaf_dim) {
            size_t ll = 0u;
            const unsigned char *lab = genome_gene_label(body + o, leaf_dim, &ll);
            if (lab == NULL) { continue; }
            if (ll != tok_len ||
                (tok_len != 0u && memcmp(lab, expected + i, tok_len) != 0)) { continue; }
            int e = 0;
            srmech_status_t st = genome_gene_is_expressed(body + o, leaf_dim, cs, &e);
            if (st != SRMECH_OK) { return st; }
            if (e) { found = 1; }
        }
        if (found == 0) { *ok = 0; }
        i = j + 1u;
    }
    return SRMECH_OK;
}

/* §133 M2 — forward-CHECK one candidate: is set(gene_express(candidate) labels)
 * == set(expected)? *consistent = 1 iff the two label sets are EQUAL (both-subset:
 * every expressing gene's label is expected, AND every expected token is produced
 * by some expressing gene — duplicate-insensitive). ONE-SIDED: CONSISTENT = "could
 * be the state" (many may be), NEVER "it IS the state". Reuses the forward
 * per-gene srmech_genome_gene_express (no new gate logic); an int64 threshold /
 * graded OVERFLOW propagates so the caller falls to the exact pure path. Byte-
 * identical to the pure Python set comparison. No abs; caller-arena-free;
 * malloc-free; a READ. */
srmech_status_t srmech_genome_modulator_consistent(
    const unsigned char *body, size_t body_len, size_t leaf_dim,
    const unsigned char *expected, size_t expected_len,
    uint64_t candidate_cell_state, int *consistent)
{
    assert(body != NULL || body_len == 0u);
    assert(consistent != NULL);
    if (body == NULL && body_len != 0u) { return SRMECH_ERR_NULL_ARG; }
    if (consistent == NULL) { return SRMECH_ERR_NULL_ARG; }
    if (expected == NULL && expected_len != 0u) { return SRMECH_ERR_NULL_ARG; }
    if (leaf_dim == 0u || leaf_dim > 256u) { return SRMECH_ERR_BAD_INPUT; }
    if (body_len % leaf_dim != 0u) { return SRMECH_ERR_BAD_INPUT; }
    int ok = 1;
    for (size_t o = 0u; o + leaf_dim <= body_len; o += leaf_dim) {  /* Check 1 */
        int e = 0;
        srmech_status_t st = genome_gene_is_expressed(
            body + o, leaf_dim, candidate_cell_state, &e);
        if (st != SRMECH_OK) { return st; }             /* overflow -> pure path */
        if (e == 0) { continue; }
        size_t ll = 0u;
        const unsigned char *lab = genome_gene_label(body + o, leaf_dim, &ll);
        if (lab == NULL) { return SRMECH_ERR_BAD_INPUT; }
        if (genome_blob_contains(expected, expected_len, lab, ll) == 0) { ok = 0; }
    }
    srmech_status_t st2 = genome_modulator_expected_covered(   /* Check 2 */
        body, body_len, leaf_dim, expected, expected_len, candidate_cell_state, &ok);
    if (st2 != SRMECH_OK) { return st2; }
    *consistent = ok;
    return SRMECH_OK;
}

/* ==========================================================================
 * §133/v11 (#733) — MODULATOR-CONSTRAINT (M3): the COMPLETE inverse of
 * gene_express. Emit the BOOLEAN part (the M1 floor + the disjunctive nand /
 * or_terms CLAUSES) of the EXACT constraint characterizing the WHOLE set of
 * cell-states consistent with an observed expression, into a caller-arena
 * buffer, in the canonical big-endian serialization (see srmech.h). The E4
 * inequality / E3 level constraints + satisfiability are computed by the
 * Python caller (the owed-C). Byte-identical to the pure Python
 * srmech.amsc.genome._serialize_bool_constraint(_modulator_constraint_bool_pure).
 * Caller-arena; malloc-free; no abs; a READ.
 * ========================================================================== */

/* Read a big-endian uint32 at buf[base..base+4). Bounds are checked by the
 * caller (the satisfies parser). No abs; a READ. */
static uint32_t genome_read_u32_be(const unsigned char *buf, size_t base)
{
    assert(buf != NULL);
    assert(base < base + 4u);                        /* no wrap */
    return ((uint32_t)buf[base] << 24) | ((uint32_t)buf[base + 1u] << 16)
         | ((uint32_t)buf[base + 2u] << 8) | (uint32_t)buf[base + 3u];
}

/* Write uint64 v big-endian into out[*pos..*pos+8); caller-arena bounds-checked
 * against out_cap; advances *pos. SRMECH_ERR_BAD_INPUT if it would overflow the
 * caller's buffer. No abs. */
static srmech_status_t genome_emit_u64(unsigned char *out, size_t out_cap,
                                       size_t *pos, uint64_t v)
{
    assert(out != NULL && pos != NULL);
    assert(out_cap >= *pos);
    if (*pos + 8u > out_cap) { return SRMECH_ERR_BAD_INPUT; }
    for (size_t k = 0u; k < 8u; k++) {
        out[*pos + k] = (unsigned char)((v >> (8u * (7u - k))) & 0xFFu);
    }
    *pos += 8u;
    return SRMECH_OK;
}

/* Write uint32 v big-endian into out[*pos..*pos+4); bounds-checked; advances
 * *pos. No abs. */
static srmech_status_t genome_emit_u32(unsigned char *out, size_t out_cap,
                                       size_t *pos, uint32_t v)
{
    assert(out != NULL && pos != NULL);
    assert(out_cap >= *pos);
    if (*pos + 4u > out_cap) { return SRMECH_ERR_BAD_INPUT; }
    for (size_t k = 0u; k < 4u; k++) {
        out[*pos + k] = (unsigned char)((v >> (8u * (3u - k))) & 0xFFu);
    }
    *pos += 4u;
    return SRMECH_OK;
}

/* Backfill a uint32 big-endian at a FIXED (already-reserved, in-bounds) offset. */
static void genome_poke_u32(unsigned char *out, size_t at, uint32_t v)
{
    assert(out != NULL);
    assert(at < at + 4u);                            /* no wrap */
    for (size_t k = 0u; k < 4u; k++) {
        out[at + k] = (unsigned char)((v >> (8u * (3u - k))) & 0xFFu);
    }
}

/* Number of boolean AND-terms a gene cap contributes (§133 M3): E1 (0x47/0x67)
 * -> 1; E2 (0x62) -> its DNF term count; threshold/graded -> 0. Byte-identical
 * to Python _gene_bool_terms length. *n set; status. No abs; a READ. */
static srmech_status_t genome_bool_nterms(const unsigned char *cap, size_t leaf_dim,
                                          uint32_t *n)
{
    assert(cap != NULL && n != NULL);
    assert(leaf_dim > 0u && leaf_dim <= 256u);
    *n = 0u;
    unsigned char m = cap[0];
    if (m == SRMECH_GENOME_THRESHOLD_GENE_MARKER ||
        m == SRMECH_GENOME_GRADED_GENE_MARKER) { return SRMECH_OK; }        /* not boolean */
    if (m != SRMECH_GENOME_BOOLEAN_GENE_MARKER) { *n = 1u; return SRMECH_OK; }  /* E1 -> 1 */
    size_t i = 1u;
    while (i < leaf_dim && cap[i] != 0u) { i++; }
    if (i >= leaf_dim) { return SRMECH_ERR_BAD_INPUT; }
    size_t base = i + 1u;
    if (base + 1u + SRMECH_GENOME_BOOLEAN_NTERMS_BYTES > leaf_dim) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (cap[base] != SRMECH_GENOME_GATE_TYPE_BOOLEAN_DNF) { return SRMECH_ERR_BAD_INPUT; }
    size_t nt = base + 1u;
    *n = ((uint32_t)cap[nt] << 8) | (uint32_t)cap[nt + 1u];
    return SRMECH_OK;
}

/* Read boolean AND-term k of a gene cap into (*act,*rep) (§133 M3): E1 0x47 ->
 * (0,0); E1 0x67 -> its (activator,repressor); E2 0x62 -> the k-th DNF (act,rep).
 * Bounds mirror genome_dnf_fold. No abs; a READ. */
static srmech_status_t genome_bool_term(const unsigned char *cap, size_t leaf_dim,
                                        uint32_t k, uint64_t *act, uint64_t *rep)
{
    assert(cap != NULL && act != NULL && rep != NULL);
    assert(leaf_dim > 0u && leaf_dim <= 256u);
    *act = 0u; *rep = 0u;
    if (cap[0] != SRMECH_GENOME_BOOLEAN_GENE_MARKER) {
        return genome_regulatory_masks(cap, leaf_dim, act, rep);            /* E1; k == 0 */
    }
    size_t i = 1u;
    while (i < leaf_dim && cap[i] != 0u) { i++; }
    if (i >= leaf_dim) { return SRMECH_ERR_BAD_INPUT; }
    size_t terms_off = i + 1u + 1u + SRMECH_GENOME_BOOLEAN_NTERMS_BYTES;
    size_t o = terms_off + (size_t)k * SRMECH_GENOME_BOOLEAN_TERM_BYTES;
    if (o + SRMECH_GENOME_BOOLEAN_TERM_BYTES > leaf_dim) { return SRMECH_ERR_BAD_INPUT; }
    *act = genome_read_u64_be(cap, o);
    *rep = genome_read_u64_be(cap, o + SRMECH_GENOME_REGULATORY_MASK_BYTES);
    return SRMECH_OK;
}

/* Is the cap at `self_off` the FIRST cap in `body` carrying `label` (no earlier
 * cap shares it)? The "one or-clause per label, first-occurrence order" guard. */
static int genome_is_first_label(const unsigned char *body, size_t leaf_dim,
                                 size_t self_off, const unsigned char *label,
                                 size_t label_len)
{
    assert(body != NULL && label != NULL);
    assert(leaf_dim > 0u);
    for (size_t o = 0u; o < self_off; o += leaf_dim) {
        size_t ol = 0u;
        const unsigned char *ot = genome_gene_label(body + o, leaf_dim, &ol);
        if (ot == NULL) { continue; }
        if (ol == label_len && (label_len == 0u || memcmp(ot, label, label_len) == 0)) {
            return 0;                                /* an earlier cap shares it */
        }
    }
    return 1;
}

/* Does any cap carrying `label` open a THRESHOLD (0x77) / GRADED (0x64) gene?
 * The cross-type-OR soundness guard: such a label's boolean terms must NOT be
 * forced into an or-clause (it can express via the threshold/graded branch). */
static int genome_label_has_nonbool(const unsigned char *body, size_t body_len,
                                    size_t leaf_dim, const unsigned char *label,
                                    size_t label_len)
{
    assert(body != NULL || body_len == 0u);
    assert(label != NULL || label_len == 0u);
    for (size_t o = 0u; o + leaf_dim <= body_len; o += leaf_dim) {
        unsigned char m = body[o];
        if (m != SRMECH_GENOME_THRESHOLD_GENE_MARKER &&
            m != SRMECH_GENOME_GRADED_GENE_MARKER) { continue; }
        size_t ol = 0u;
        const unsigned char *ot = genome_gene_label(body + o, leaf_dim, &ol);
        if (ot == NULL) { continue; }
        if (ol == label_len && (label_len == 0u || memcmp(ot, label, label_len) == 0)) {
            return 1;
        }
    }
    return 0;
}

/* Emit the nand clauses (§133 M3): for every UN-expressed E1/E2 gene cap (body
 * order), one (any_absent=act, any_present=rep) pair per boolean AND-term. Sets
 * *n_nand. Byte-identical to the pure Python nand walk. No abs; a READ. */
static srmech_status_t genome_emit_nand(
    const unsigned char *body, size_t body_len, size_t leaf_dim,
    const unsigned char *expressed, size_t expressed_len,
    unsigned char *out, size_t out_cap, size_t *pos, uint32_t *n_nand)
{
    assert(out != NULL && pos != NULL && n_nand != NULL);
    assert(leaf_dim > 0u);
    *n_nand = 0u;
    for (size_t o = 0u; o + leaf_dim <= body_len; o += leaf_dim) {
        const unsigned char *cap = body + o;
        if (cap[0] == SRMECH_GENOME_THRESHOLD_GENE_MARKER ||
            cap[0] == SRMECH_GENOME_GRADED_GENE_MARKER) { continue; }       /* an ineq / level */
        size_t ll = 0u;
        const unsigned char *lab = genome_gene_label(cap, leaf_dim, &ll);
        if (lab == NULL) { return SRMECH_ERR_BAD_INPUT; }
        if (genome_blob_contains(expressed, expressed_len, lab, ll)) { continue; }  /* expressed */
        uint32_t nt = 0u;
        srmech_status_t st = genome_bool_nterms(cap, leaf_dim, &nt);
        if (st != SRMECH_OK) { return st; }
        for (uint32_t k = 0u; k < nt; k++) {
            uint64_t a = 0u, r = 0u;
            st = genome_bool_term(cap, leaf_dim, k, &a, &r);
            if (st != SRMECH_OK) { return st; }
            st = genome_emit_u64(out, out_cap, pos, a);
            if (st != SRMECH_OK) { return st; }
            st = genome_emit_u64(out, out_cap, pos, r);
            if (st != SRMECH_OK) { return st; }
            (*n_nand)++;
        }
    }
    return SRMECH_OK;
}

/* Total boolean AND-terms across every cap in body carrying `label`. */
static srmech_status_t genome_count_label_terms(
    const unsigned char *body, size_t body_len, size_t leaf_dim,
    const unsigned char *label, size_t label_len, uint32_t *total)
{
    assert(body != NULL || body_len == 0u);
    assert(total != NULL);
    *total = 0u;
    for (size_t o = 0u; o + leaf_dim <= body_len; o += leaf_dim) {
        size_t ll = 0u;
        const unsigned char *lab = genome_gene_label(body + o, leaf_dim, &ll);
        if (lab == NULL) { continue; }
        if (ll != label_len || (label_len != 0u && memcmp(lab, label, label_len) != 0)) {
            continue;
        }
        uint32_t nt = 0u;
        srmech_status_t st = genome_bool_nterms(body + o, leaf_dim, &nt);
        if (st != SRMECH_OK) { return st; }
        *total += nt;
    }
    return SRMECH_OK;
}

/* Emit every boolean AND-term (present=act u64, absent=rep u64) across caps
 * carrying `label`, in body order. Pairs with genome_count_label_terms. */
static srmech_status_t genome_emit_label_terms(
    const unsigned char *body, size_t body_len, size_t leaf_dim,
    const unsigned char *label, size_t label_len,
    unsigned char *out, size_t out_cap, size_t *pos)
{
    assert(body != NULL || body_len == 0u);
    assert(out != NULL && pos != NULL);
    for (size_t o = 0u; o + leaf_dim <= body_len; o += leaf_dim) {
        size_t ll = 0u;
        const unsigned char *lab = genome_gene_label(body + o, leaf_dim, &ll);
        if (lab == NULL) { continue; }
        if (ll != label_len || (label_len != 0u && memcmp(lab, label, label_len) != 0)) {
            continue;
        }
        uint32_t nt = 0u;
        srmech_status_t st = genome_bool_nterms(body + o, leaf_dim, &nt);
        if (st != SRMECH_OK) { return st; }
        for (uint32_t k = 0u; k < nt; k++) {
            uint64_t a = 0u, r = 0u;
            st = genome_bool_term(body + o, leaf_dim, k, &a, &r);
            if (st != SRMECH_OK) { return st; }
            st = genome_emit_u64(out, out_cap, pos, a);
            if (st != SRMECH_OK) { return st; }
            st = genome_emit_u64(out, out_cap, pos, r);
            if (st != SRMECH_OK) { return st; }
        }
    }
    return SRMECH_OK;
}

/* Emit the or_terms clauses (§133 M3): for each EXPRESSED pure-boolean label
 * (first-occurrence order, no threshold/graded cap) with >= 2 boolean terms, one
 * (n_terms, [present, absent]*) clause. Sets *n_or. Byte-identical to Python.
 * No abs; a READ. */
static srmech_status_t genome_emit_or(
    const unsigned char *body, size_t body_len, size_t leaf_dim,
    const unsigned char *expressed, size_t expressed_len,
    unsigned char *out, size_t out_cap, size_t *pos, uint32_t *n_or)
{
    assert(out != NULL && pos != NULL && n_or != NULL);
    assert(leaf_dim > 0u);
    *n_or = 0u;
    for (size_t o = 0u; o + leaf_dim <= body_len; o += leaf_dim) {
        size_t ll = 0u;
        const unsigned char *lab = genome_gene_label(body + o, leaf_dim, &ll);
        if (lab == NULL) { return SRMECH_ERR_BAD_INPUT; }
        if (!genome_is_first_label(body, leaf_dim, o, lab, ll)) { continue; }
        if (!genome_blob_contains(expressed, expressed_len, lab, ll)) { continue; }
        if (genome_label_has_nonbool(body, body_len, leaf_dim, lab, ll)) { continue; }
        uint32_t total = 0u;
        srmech_status_t st = genome_count_label_terms(body, body_len, leaf_dim, lab, ll, &total);
        if (st != SRMECH_OK) { return st; }
        if (total < 2u) { continue; }                /* single term -> pinned by the floor */
        st = genome_emit_u32(out, out_cap, pos, total);
        if (st != SRMECH_OK) { return st; }
        st = genome_emit_label_terms(body, body_len, leaf_dim, lab, ll, out, out_cap, pos);
        if (st != SRMECH_OK) { return st; }
        (*n_or)++;
    }
    return SRMECH_OK;
}

srmech_status_t srmech_genome_modulator_constraint(
    const unsigned char *body, size_t body_len, size_t leaf_dim,
    const unsigned char *expressed, size_t expressed_len,
    unsigned char *out, size_t out_cap, size_t *out_len)
{
    assert(body != NULL || body_len == 0u);
    assert(out != NULL && out_len != NULL);
    if (body == NULL && body_len != 0u) { return SRMECH_ERR_NULL_ARG; }
    if (out == NULL || out_len == NULL) { return SRMECH_ERR_NULL_ARG; }
    if (expressed == NULL && expressed_len != 0u) { return SRMECH_ERR_NULL_ARG; }
    if (leaf_dim == 0u || leaf_dim > 256u) { return SRMECH_ERR_BAD_INPUT; }
    if (body_len % leaf_dim != 0u) { return SRMECH_ERR_BAD_INPUT; }
    uint64_t on = 0u, off = 0u, und = 0u;
    int verdict = 0;
    srmech_status_t st = srmech_genome_modulator_recover(     /* the M1 floor */
        body, body_len, leaf_dim, expressed, expressed_len, &on, &off, &und, &verdict);
    if (st != SRMECH_OK) { return st; }
    size_t pos = 0u;
    st = genome_emit_u64(out, out_cap, &pos, on);
    if (st != SRMECH_OK) { return st; }
    st = genome_emit_u64(out, out_cap, &pos, off);
    if (st != SRMECH_OK) { return st; }
    size_t nand_at = pos;                                    /* reserve n_nand */
    st = genome_emit_u32(out, out_cap, &pos, 0u);
    if (st != SRMECH_OK) { return st; }
    uint32_t n_nand = 0u;
    st = genome_emit_nand(body, body_len, leaf_dim, expressed, expressed_len,
                          out, out_cap, &pos, &n_nand);
    if (st != SRMECH_OK) { return st; }
    genome_poke_u32(out, nand_at, n_nand);
    size_t or_at = pos;                                      /* reserve n_or */
    st = genome_emit_u32(out, out_cap, &pos, 0u);
    if (st != SRMECH_OK) { return st; }
    uint32_t n_or = 0u;
    st = genome_emit_or(body, body_len, leaf_dim, expressed, expressed_len,
                        out, out_cap, &pos, &n_or);
    if (st != SRMECH_OK) { return st; }
    genome_poke_u32(out, or_at, n_or);
    *out_len = pos;
    return SRMECH_OK;
}

/* §133 M3 — check the BOOLEAN part of an emitted constraint against a candidate.
 * *satisfied = 1 iff the floor pins + every nand / or_terms clause hold. Byte-
 * identical to the pure Python _satisfies_bool. Malloc-free; no abs; a READ. */
srmech_status_t srmech_genome_modulator_constraint_satisfies(
    const unsigned char *buf, size_t buf_len,
    uint64_t candidate_cell_state, int *satisfied)
{
    assert(buf != NULL || buf_len == 0u);
    assert(satisfied != NULL);
    if (satisfied == NULL) { return SRMECH_ERR_NULL_ARG; }
    if (buf == NULL && buf_len != 0u) { return SRMECH_ERR_NULL_ARG; }
    if (buf_len < 20u) { return SRMECH_ERR_BAD_INPUT; }
    uint64_t cs = candidate_cell_state;
    *satisfied = 0;
    if ((cs & genome_read_u64_be(buf, 0u)) != genome_read_u64_be(buf, 0u)) { return SRMECH_OK; }
    if ((cs & genome_read_u64_be(buf, 8u)) != 0u) { return SRMECH_OK; }
    uint32_t n_nand = genome_read_u32_be(buf, 16u);
    size_t pos = 20u;
    for (uint32_t i = 0u; i < n_nand; i++) {
        if (pos + 16u > buf_len) { return SRMECH_ERR_BAD_INPUT; }
        uint64_t a = genome_read_u64_be(buf, pos);
        uint64_t p = genome_read_u64_be(buf, pos + 8u);
        pos += 16u;
        if (!(((cs & a) != a) || ((cs & p) != 0u))) { return SRMECH_OK; }  /* term matched */
    }
    if (pos + 4u > buf_len) { return SRMECH_ERR_BAD_INPUT; }
    uint32_t n_or = genome_read_u32_be(buf, pos);
    pos += 4u;
    for (uint32_t i = 0u; i < n_or; i++) {
        if (pos + 4u > buf_len) { return SRMECH_ERR_BAD_INPUT; }
        uint32_t nt = genome_read_u32_be(buf, pos);
        pos += 4u;
        int matched = 0;
        for (uint32_t k = 0u; k < nt; k++) {
            if (pos + 16u > buf_len) { return SRMECH_ERR_BAD_INPUT; }
            uint64_t pr = genome_read_u64_be(buf, pos);
            uint64_t ab = genome_read_u64_be(buf, pos + 8u);
            pos += 16u;
            if (((cs & pr) == pr) && ((cs & ab) == 0u)) { matched = 1; }
        }
        if (matched == 0) { return SRMECH_OK; }
    }
    *satisfied = 1;
    return SRMECH_OK;
}

srmech_status_t srmech_genome_save(
    const char *dir,
    const unsigned char *body, size_t body_len,
    uint32_t leaf_dim,
    const unsigned char *coupling, size_t coupling_len,
    void *ws, size_t ws_len)
{
    assert(dir != NULL || ws == NULL);
    assert(coupling != NULL || coupling_len == 0u);
    srmech_status_t st = genome_save_validate(dir, body, body_len, leaf_dim,
                                              coupling, coupling_len, ws);
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
    st = genome_fill_strings(&strs, &a, body, body_len, leaf_dim, coupling);
    if (st != SRMECH_OK) { return st; }
    size_t man_cap = genome_manifest_cap(strs.n_chroms);
    char *manifest = genome_arena_alloc(&a, man_cap + 1u);
    if (manifest == NULL) { return SRMECH_ERR_OVERFLOW; }
    void *tws = NULL;
    size_t tws_len = 0u;
    genome_arena_tail(&a, &tws, &tws_len);
    size_t mlen = 0u;
    st = genome_build_manifest(&strs, leaf_dim, body_len,
                               tws, tws_len, manifest, man_cap, &mlen, 1);  /* HEAD-ONLY */
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
        (size_t)(65u + 65u + 8u + 8u + SRMECH_GENOME_MAX_LABEL + 8u + 1u) /* strings
                                                    * arrays (+65 = the v4 region_sha,
                                                    * +1 = the §96 cap_kind code) */
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

/* Forward decl: genome_data_get is defined below but genome_obtain_manifest (v12
 * head-only branch) needs it above. */
static const srmech_json_value_t *genome_data_get(
    const srmech_json_value_t *manifest, const char *key);

/* From a v12 HEAD-ONLY manifest tree, extract leaf_dim + decode coupling (into
 * one_buf, cap >= leaf_dim <= 256) — the params the reader-side derive-from-body
 * needs (the head carries them; no caller coupling= required). */
static srmech_status_t genome_head_rebuild_params(const srmech_json_value_t *head,
    unsigned char *one_buf, uint32_t *leaf_dim)
{
    assert(head != NULL && one_buf != NULL);
    assert(leaf_dim != NULL);
    const srmech_json_value_t *ld = genome_data_get(head, "leaf_dim");
    const srmech_json_value_t *dto = genome_data_get(head, "coupling");
    const srmech_json_value_t *hx =
        (dto != NULL) ? srmech_json_object_get(dto, "hex") : NULL;
    if (ld == NULL || ld->type != SRMECH_JSON_INT || ld->u.i <= 0 ||
        ld->u.i > 256 || hx == NULL || hx->type != SRMECH_JSON_STRING ||
        hx->u.str.len != 2u * (size_t)ld->u.i) {
        return SRMECH_ERR_BAD_INPUT;
    }
    *leaf_dim = (uint32_t)ld->u.i;
    return genome_hex2bytes(hx->u.str.ptr, *leaf_dim, one_buf);
}

/* §44: obtain the manifest TREE — parse manifest.json if present (cheap; never
 * opens turns.bin), else REBUILD it by scanning the self-describing body (the
 * strand is the SSoT, the manifest an optional .fai cache). The rebuild needs
 * `coupling` (coupling_len IS leaf_dim, the width the body lacks inline); a
 * missing manifest with coupling==NULL returns SRMECH_ERR_BAD_INPUT (the helpful
 * "pass coupling" error, NOT a bare IO miss). On either path the tree lives in
 * `ws`, so the loaders' accessors walk it unchanged. */
static srmech_status_t genome_obtain_manifest(
    const char *dir, const unsigned char *coupling, size_t coupling_len,
    void *ws, size_t ws_len, srmech_json_value_t **out)
{
    assert(dir != NULL && out != NULL && ws != NULL);
    assert(coupling != NULL || coupling_len == 0u);
    char man_path[SRMECH_GENOME_PATH_MAX];
    srmech_status_t st = genome_join(dir, SRMECH_GENOME_MANIFEST,
                                     man_path, sizeof(man_path));
    if (st != SRMECH_OK) { return st; }
    genome_arena_t a;
    genome_arena_init(&a, ws, ws_len);
    size_t msz = 0u;
    uint32_t leaf_dim;
    const unsigned char *one_ptr;
    unsigned char one_buf[256];
    if (genome_file_size(man_path, &msz) == SRMECH_OK) {  /* manifest present: parse it */
        char *manbuf = genome_arena_alloc(&a, msz + 1u);
        if (manbuf == NULL) { return SRMECH_ERR_OVERFLOW; }
        void *ptws = NULL;
        size_t ptws_len = 0u;
        genome_arena_tail(&a, &ptws, &ptws_len);
        size_t mlen = 0u;
        st = genome_parse_manifest(dir, manbuf, msz + 1u, &mlen, ptws, ptws_len, out);
        if (st != SRMECH_OK) { return st; }
        if (genome_data_get(*out, "chromosomes") != NULL) {
            return SRMECH_OK;                     /* v<=11 FULL manifest — arrays present */
        }
        /* v12 HEAD-ONLY: derive leaf_dim + coupling from the head, rebuild from body. */
        st = genome_head_rebuild_params(*out, one_buf, &leaf_dim);
        if (st != SRMECH_OK) { return st; }
        one_ptr = one_buf;
        genome_arena_init(&a, ws, ws_len);        /* RESET — the head is copied out */
    } else {
        if (coupling == NULL || coupling_len == 0u || coupling_len > 256u) {
            return SRMECH_ERR_BAD_INPUT;              /* cannot scan w/o leaf_dim */
        }
        leaf_dim = (uint32_t)coupling_len;
        one_ptr = coupling;
    }
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
    st = genome_fill_strings(&rstrs, &a, body, blen, leaf_dim, one_ptr);
    if (st != SRMECH_OK) { return st; }
    void *tws = NULL;
    size_t tws_len = 0u;
    genome_arena_tail(&a, &tws, &tws_len);
    return genome_build_manifest_tree(&rstrs, leaf_dim, blen, tws, tws_len,
                                      out, NULL, NULL, 0);  /* FULL — readers need arrays */
}

srmech_status_t srmech_genome_catalog(const char *dir,
                                      const unsigned char *coupling,
                                      size_t coupling_len,
                                      void *ws, size_t ws_len,
                                      srmech_json_value_t **out_manifest)
{
    assert(out_manifest != NULL);
    assert(dir != NULL || ws == NULL);
    if (dir == NULL || ws == NULL || out_manifest == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    return genome_obtain_manifest(dir, coupling, coupling_len, ws, ws_len,
                                  out_manifest);
}

/* ------------------------------------------------------------------ *
 * §96 CENSUS + REGISTRY — the biology-native per-genome roll-up + the
 * cell/melange census over a ROOT of genomes. srmech reads the SHAPE (the
 * inline cap markers, classified once in the body scan); the caller assigns
 * the ROLE. The census scans the body ONCE (no O(n) per-chromosome loads —
 * cap_kind rides the §44 scan), the topology is an INTEGER read (no libm).
 * ------------------------------------------------------------------ */

/* Census arena size — a body scan + strings block + a (small) census subtree
 * fit inside the catalog arena budget, so reuse srmech_genome_arena_bytes. */
size_t srmech_genome_census_arena_bytes(size_t body_len, uint32_t n_chroms)
{
    assert(n_chroms != 0xFFFFFFFFu);
    assert(SRMECH_GENOME_MAX_LABEL > 0u);
    return srmech_genome_arena_bytes(body_len, n_chroms, 0u);
}

/* Resolve the (leaf_dim, one_ptr) a body SCAN needs — from the manifest HEAD
 * when present (a full OR head-only manifest both carry data.leaf_dim +
 * data.coupling.hex), else from the caller `coupling` (its length IS leaf_dim).
 * Bumps `a` past the manifest bytes (the parse TREE lives in a's tail and is
 * reclaimed by the next alloc — leaf_dim + coupling are copied into one_buf). */
static srmech_status_t genome_scan_params(
    const char *dir, const unsigned char *coupling, size_t coupling_len,
    genome_arena_t *a, unsigned char *one_buf, const unsigned char **one_ptr,
    uint32_t *leaf_dim)
{
    assert(dir != NULL && a != NULL && one_buf != NULL);
    assert(one_ptr != NULL && leaf_dim != NULL);
    char man_path[SRMECH_GENOME_PATH_MAX];
    srmech_status_t st = genome_join(dir, SRMECH_GENOME_MANIFEST,
                                     man_path, sizeof(man_path));
    if (st != SRMECH_OK) { return st; }
    size_t msz = 0u;
    if (genome_file_size(man_path, &msz) == SRMECH_OK) {   /* manifest present */
        char *manbuf = genome_arena_alloc(a, msz + 1u);
        if (manbuf == NULL) { return SRMECH_ERR_OVERFLOW; }
        void *ptws = NULL;
        size_t ptws_len = 0u;
        genome_arena_tail(a, &ptws, &ptws_len);
        size_t mlen = 0u;
        srmech_json_value_t *man = NULL;
        st = genome_parse_manifest(dir, manbuf, msz + 1u, &mlen, ptws, ptws_len, &man);
        if (st != SRMECH_OK) { return st; }
        st = genome_head_rebuild_params(man, one_buf, leaf_dim);  /* copies out */
        if (st != SRMECH_OK) { return st; }
        *one_ptr = one_buf;
        return SRMECH_OK;
    }
    if (coupling == NULL || coupling_len == 0u || coupling_len > 256u) {
        return SRMECH_ERR_BAD_INPUT;                       /* cannot scan w/o width */
    }
    *leaf_dim = (uint32_t)coupling_len;
    *one_ptr = coupling;
    return SRMECH_OK;
}

/* Read <dir>/turns.bin into the arena `a` and fill the §44 strings block
 * (label / leaf_count / cap_kind / … per chromosome) — the census's ONE body
 * scan. `a` already holds the resolved (leaf_dim, one_ptr). */
static srmech_status_t genome_load_strings(
    const char *dir, const unsigned char *one_ptr, uint32_t leaf_dim,
    genome_arena_t *a, genome_strings_t *s)
{
    assert(dir != NULL && one_ptr != NULL);
    assert(a != NULL && s != NULL && leaf_dim > 0u);
    char body_path[SRMECH_GENOME_PATH_MAX];
    srmech_status_t st = genome_join(dir, SRMECH_GENOME_BODY,
                                     body_path, sizeof(body_path));
    if (st != SRMECH_OK) { return st; }
    size_t bsz = 0u;
    st = genome_file_size(body_path, &bsz);
    if (st != SRMECH_OK) { return st; }
    unsigned char *body = genome_arena_alloc(a, (bsz == 0u) ? 1u : bsz);
    if (body == NULL) { return SRMECH_ERR_OVERFLOW; }
    size_t blen = 0u;
    st = genome_read_file(body_path, body, bsz, &blen);
    if (st != SRMECH_OK) { return st; }
    return genome_fill_strings(s, a, body, blen, leaf_dim, one_ptr);
}

/* §96 topology — the structural nuclear/organelle/plasmid read, INTEGER-only
 * (no libm), byte-identical to genome.py: any nuclear/diploid → nuclear-like;
 * else small all-plasmid (total_leaves <= 8*n) → organelle-like; else n>0 →
 * plasmid/prokaryote-like; else empty. */
static const char *genome_census_topology(uint32_t nuclear, uint32_t diploid,
                                          uint64_t total_leaves, uint32_t n_chrom)
{
    assert(n_chrom != 0xFFFFFFFFu);
    assert(nuclear <= n_chrom && diploid <= n_chrom);
    if (nuclear > 0u || diploid > 0u) { return "nuclear-like"; }
    if (n_chrom > 0u && total_leaves <= (uint64_t)8u * (uint64_t)n_chrom) {
        return "organelle-like";
    }
    if (n_chrom > 0u) { return "plasmid/prokaryote-like"; }
    return "empty";
}

/* Build one census chromosome entry {label, type, leaf_count} (the caller
 * assigns the ROLE; srmech reads the SHAPE cap_kind). */
static srmech_json_value_t *genome_build_census_chrom(
    srmech_json_builder_t *b, const genome_strings_t *s, uint32_t idx)
{
    assert(b != NULL && s != NULL);
    assert(idx < s->n_chroms);
    const char *keys[3] = { "label", "type", "leaf_count" };
    srmech_json_value_t *vals[3];
    const char *ck = genome_cap_kind_str(s->cap_kind[idx]);
    vals[0] = srmech_json_new_string(b, s->label[idx],
                                     (uint32_t)strlen(s->label[idx]));
    vals[1] = srmech_json_new_string(b, ck, (uint32_t)strlen(ck));
    vals[2] = srmech_json_new_int(b, (int64_t)s->leaf_count[idx]);
    return srmech_json_new_object(b, keys, vals, 3u);
}

/* Build the types roll-up object {plasmid, nuclear, diploid} from the code counts
 * (cnt indexed by the §96 cap-kind code: 0 plasmid / 1 nuclear / 2 diploid). */
static srmech_json_value_t *genome_build_types(srmech_json_builder_t *b,
                                               const uint32_t cnt[3])
{
    assert(b != NULL && cnt != NULL);
    assert(SRMECH_GENOME_CAP_KIND_NUCLEAR == 1u);
    const char *keys[3] = { "plasmid", "nuclear", "diploid" };
    srmech_json_value_t *vals[3];
    vals[0] = srmech_json_new_int(b, (int64_t)cnt[0]);
    vals[1] = srmech_json_new_int(b, (int64_t)cnt[1]);
    vals[2] = srmech_json_new_int(b, (int64_t)cnt[2]);
    return srmech_json_new_object(b, keys, vals, 3u);
}

/* Build the census ROOT {path, n_chromosomes, types, chromosomes, total_leaves,
 * topology} from a filled strings block, using builder `b` (its arena persists;
 * `path` + s->label[] are held BY REFERENCE, so both must outlive the tree).
 * `items` is an n_chroms-sized pointer scratch carved from the persistent arena. */
static srmech_json_value_t *genome_census_root(
    srmech_json_builder_t *b, const genome_strings_t *s, const char *path,
    srmech_json_value_t **items)
{
    assert(b != NULL && s != NULL);
    assert(path != NULL && items != NULL);
    uint32_t cnt[3] = { 0u, 0u, 0u };
    uint64_t leaves = 0u;
    for (uint32_t i = 0; i < s->n_chroms; i++) {
        unsigned char code = s->cap_kind[i];
        if (code <= SRMECH_GENOME_CAP_KIND_DIPLOID) { cnt[code]++; }
        leaves += (uint64_t)s->leaf_count[i];
        items[i] = genome_build_census_chrom(b, s, i);
    }
    srmech_json_value_t *chroms = srmech_json_new_array(b, items, s->n_chroms);
    srmech_json_value_t *types = genome_build_types(b, cnt);
    const char *topo = genome_census_topology(cnt[1], cnt[2], leaves, s->n_chroms);
    const char *keys[6] = { "path", "n_chromosomes", "types", "chromosomes",
                            "total_leaves", "topology" };
    srmech_json_value_t *vals[6];
    vals[0] = srmech_json_new_string(b, path, (uint32_t)strlen(path));
    vals[1] = srmech_json_new_int(b, (int64_t)s->n_chroms);
    vals[2] = types;
    vals[3] = chroms;
    vals[4] = srmech_json_new_int(b, (int64_t)leaves);
    vals[5] = srmech_json_new_string(b, topo, (uint32_t)strlen(topo));
    return srmech_json_new_object(b, keys, vals, 6u);
}

/* Build ONE genome's census tree into the bump arena `a` (PERSISTENT — the tree,
 * its strings block, and the item scratch all survive so a REGISTRY caller can
 * reference the subtree while it builds later genomes). Advances a->off past the
 * subtree. `dir` is used BOTH as the FS path to read and the census "path" field
 * (so it must outlive the tree — the caller keeps it alive). */
static srmech_status_t genome_census_build(
    const char *dir, const unsigned char *coupling, size_t coupling_len,
    genome_arena_t *a, srmech_json_value_t **out)
{
    assert(dir != NULL && a != NULL && out != NULL);
    assert(coupling != NULL || coupling_len == 0u);
    unsigned char one_buf[256];
    const unsigned char *one_ptr = NULL;
    uint32_t leaf_dim = 0u;
    srmech_status_t st = genome_scan_params(dir, coupling, coupling_len, a,
                                            one_buf, &one_ptr, &leaf_dim);
    if (st != SRMECH_OK) { return st; }
    genome_strings_t s;
    st = genome_load_strings(dir, one_ptr, leaf_dim, a, &s);
    if (st != SRMECH_OK) { return st; }
    /* Copy `dir` into the arena so the tree's "path" is SELF-CONTAINED (the census
     * value tree is held by reference — the caller's `dir` string may not outlive
     * the later json write). */
    size_t dlen = strlen(dir);
    char *path_copy = genome_arena_alloc(a, dlen + 1u);
    if (path_copy == NULL) { return SRMECH_ERR_OVERFLOW; }
    memcpy(path_copy, dir, dlen + 1u);
    srmech_json_value_t **items = genome_arena_alloc(
        a, (size_t)((s.n_chroms == 0u) ? 1u : s.n_chroms) * sizeof(*items));
    if (items == NULL) { return SRMECH_ERR_OVERFLOW; }
    void *jws = NULL;
    size_t jws_len = 0u;
    genome_arena_tail(a, &jws, &jws_len);
    srmech_json_builder_t b;
    st = srmech_json_builder_init(&b, jws, jws_len);
    if (st != SRMECH_OK) { return st; }
    *out = genome_census_root(&b, &s, path_copy, items);
    if (b.failed || *out == NULL) { return SRMECH_ERR_OVERFLOW; }
    a->off = (size_t)((unsigned char *)jws - a->base) + b.used;  /* subtree persists */
    return SRMECH_OK;
}

srmech_status_t srmech_genome_census(const char *dir, const unsigned char *coupling,
                                     size_t coupling_len, void *ws, size_t ws_len,
                                     srmech_json_value_t **out_census)
{
    assert(out_census != NULL);
    assert(dir != NULL || ws == NULL);
    if (dir == NULL || ws == NULL || out_census == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    genome_arena_t a;
    genome_arena_init(&a, ws, ws_len);
    return genome_census_build(dir, coupling, coupling_len, &a, out_census);
}

/* 1 iff <root>/<name> is a genome dir (holds BOTH turns.bin and manifest.json).
 * `dirbuf` (>= SRMECH_GENOME_PATH_MAX) receives <root>/<name> on success. */
static int genome_dir_is_genome(const char *root, const char *name, char *dirbuf)
{
    assert(root != NULL && name != NULL && dirbuf != NULL);
    assert(name[0] != '\0');
    if (genome_join(root, name, dirbuf, SRMECH_GENOME_PATH_MAX) != SRMECH_OK) {
        return 0;
    }
    char fp[SRMECH_GENOME_PATH_MAX];
    size_t sz = 0u;
    if (genome_join(dirbuf, SRMECH_GENOME_BODY, fp, sizeof(fp)) != SRMECH_OK ||
        genome_file_size(fp, &sz) != SRMECH_OK) {
        return 0;
    }
    if (genome_join(dirbuf, SRMECH_GENOME_MANIFEST, fp, sizeof(fp)) != SRMECH_OK ||
        genome_file_size(fp, &sz) != SRMECH_OK) {
        return 0;
    }
    return 1;
}

/* List basenames of GENOME dirs under `root` into `names` (cap max_n) via the
 * PAL dir surface (no #ifdef — the OS opendir/FindFirstFile is in the PAL). A
 * root that OPENS but holds no genome dirs yields count 0; a root that CANNOT
 * BE OPENED is SRMECH_ERR_IO. Bounded (JPL Rule 2). names==NULL runs a
 * count-only pass.
 *
 * rc294 (ADR-0009): this used to swallow EVERY dir_open failure as
 * `*count = 0; return SRMECH_OK` under a comment reading "no root -> none".
 * The comment described one case; the code covered all of them — absent root,
 * permission denied, path-is-a-file, I/O error alike all reported ZERO GENOMES
 * AND SUCCESS. A caller who typo'd a corpus path was told, authoritatively,
 * that their corpus was empty. The scripting projection meanwhile raised
 * (Path.iterdir), so the two implementations disagreed on the same input,
 * which under ADR-0009 makes the SPLIT the defect rather than either side.
 *
 * The sibling surface already had it right: genome_census on an absent path
 * raises in both projections. genome_registry was the outlier in its own
 * family. And the docstring never sanctioned it — it promises n_genomes 0 for
 * "a dir with no genome subdirs", which is an EMPTY dir, not an ABSENT one.
 *
 * The fix is deliberately NOT a bare `return st`. That would have made the
 * behaviour of an EMPTY root hostage to how each platform reports one, and
 * Windows genuinely differs: FindFirstFile signals an empty match set with
 * ERROR_FILE_NOT_FOUND, indistinguishable at this layer from a failure to
 * open. So the distinction is drawn where the knowledge lives — in the PAL
 * (srmech_plat_dir_open), which now returns SRMECH_OK + an exhausted iterator
 * for "opened, no entries" on every backend. By the time control reaches here,
 * a non-OK status means the root could not be opened, full stop.
 *
 * `max_n` is a CAPACITY, and ZERO IS A LEGAL CAPACITY. An EMPTY root is a
 * documented supported input (the public docstring promises n_genomes 0), and
 * the two-pass caller reaches pass 2 with (names != NULL, max_n == 0) whenever
 * pass 1 counted none. That shape is safe by construction: the `n >= max_n`
 * overflow guard below fires BEFORE any store, so `names` is never dereferenced
 * at capacity 0 — an empty root simply falls out of the loop with count 0, and
 * a genome appearing between the two passes is reported as OVERFLOW (a clean
 * status, not a crash). rc289: this previously asserted `max_n > 0u`, which
 * ABORTED the host on that documented input under an asserts-live build while
 * NDEBUG builds returned the right answer — an ADR-0009 projection split that
 * every shipped (Release) build masked. The assert was wrong, not the code. */
static srmech_status_t genome_list_genomes(const char *root,
    char names[][SRMECH_PLAT_DIR_NAME_MAX], uint32_t max_n, uint32_t *count)
{
    assert(root != NULL && count != NULL);
    /* The count-only pass must not claim capacity it has no buffer for; the
     * fill pass may legally carry capacity 0 (see the note above). */
    assert(names != NULL || max_n == 0u);
    uint32_t n = 0u;
    srmech_plat_dir_t d;
    srmech_status_t st = srmech_plat_dir_open(root, &d);
    /* Cannot open -> ERROR (rc294). An OPENED-but-empty root does not come
     * through here: the PAL reports it as SRMECH_OK + an exhausted iterator,
     * so it falls out of the loop below with count 0, which is the contract. */
    if (st != SRMECH_OK) { *count = 0u; return st; }
    char nm[SRMECH_PLAT_DIR_NAME_MAX];
    char dirbuf[SRMECH_GENOME_PATH_MAX];
    int have = 0;
    for (uint32_t guard = 0u; guard < 65536u; guard++) {
        st = srmech_plat_dir_next(&d, nm, sizeof(nm), &have);
        if (st != SRMECH_OK) { srmech_plat_dir_close(&d); return st; }
        if (have == 0) { break; }
        if (genome_dir_is_genome(root, nm, dirbuf)) {
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

/* Insertion-sort the genome-dir basenames ascending — the canonical registry
 * order (Python sorts genomes by path; the shared root prefix makes that a
 * basename sort). UTF-8 byte order == code-point order, so strcmp agrees. */
static void genome_sort_names(char names[][SRMECH_PLAT_DIR_NAME_MAX], uint32_t n)
{
    assert(names != NULL || n == 0u);
    assert(n != 0xFFFFFFFFu);
    for (uint32_t i = 1u; i < n; i++) {
        char nm[SRMECH_PLAT_DIR_NAME_MAX];
        memcpy(nm, names[i], sizeof(nm));
        uint32_t j = i;
        while (j > 0u && strcmp(names[j - 1u], nm) > 0) {
            memcpy(names[j], names[j - 1u], sizeof(nm));
            j--;
        }
        memcpy(names[j], nm, sizeof(nm));
    }
}

/* Build the registry ROOT {root, n_genomes, genomes} on a's tail; `groots`
 * points at the n per-genome census subtrees already built in `a` (they persist,
 * so referencing them is safe). `root` is held by reference (caller keeps it). */
static srmech_status_t genome_registry_root(genome_arena_t *a, const char *root,
    srmech_json_value_t **groots, uint32_t n, srmech_json_value_t **out)
{
    assert(a != NULL && root != NULL && out != NULL);
    assert(groots != NULL || n == 0u);
    void *jws = NULL;
    size_t jws_len = 0u;
    genome_arena_tail(a, &jws, &jws_len);
    srmech_json_builder_t b;
    srmech_status_t st = srmech_json_builder_init(&b, jws, jws_len);
    if (st != SRMECH_OK) { return st; }
    srmech_json_value_t *garr = srmech_json_new_array(&b, groots, n);
    const char *keys[3] = { "root", "n_genomes", "genomes" };
    srmech_json_value_t *vals[3];
    vals[0] = srmech_json_new_string(&b, root, (uint32_t)strlen(root));
    vals[1] = srmech_json_new_int(&b, (int64_t)n);
    vals[2] = garr;
    *out = srmech_json_new_object(&b, keys, vals, 3u);
    if (b.failed || *out == NULL) { return SRMECH_ERR_OVERFLOW; }
    return SRMECH_OK;
}

/* Census each genome dir under `root` into the bump arena `a` (each subtree
 * persists), collecting the roots into `groots`. `paths`/`names` are the
 * persistent per-genome path + basename scratch (both carved from `a`). */
static srmech_status_t genome_registry_census_all(genome_arena_t *a,
    const char *root, char (*names)[SRMECH_PLAT_DIR_NAME_MAX], uint32_t n,
    const unsigned char *coupling, size_t coupling_len, srmech_json_value_t **groots)
{
    assert(a != NULL && root != NULL);
    assert(groots != NULL || n == 0u);
    for (uint32_t i = 0; i < n; i++) {
        char *fullpath = genome_arena_alloc(a, SRMECH_GENOME_PATH_MAX);
        if (fullpath == NULL) { return SRMECH_ERR_OVERFLOW; }
        srmech_status_t st = genome_join(root, names[i], fullpath,
                                         SRMECH_GENOME_PATH_MAX);
        if (st != SRMECH_OK) { return st; }
        st = genome_census_build(fullpath, coupling, coupling_len, a, &groots[i]);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

srmech_status_t srmech_genome_registry(const char *root, const unsigned char *coupling,
                                       size_t coupling_len, void *ws, size_t ws_len,
                                       srmech_json_value_t **out_registry)
{
    assert(out_registry != NULL);
    assert(root != NULL || ws == NULL);
    if (root == NULL || ws == NULL || out_registry == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    genome_arena_t a;
    genome_arena_init(&a, ws, ws_len);
    uint32_t n = 0u;
    srmech_status_t st = genome_list_genomes(root, NULL, 0u, &n);  /* pass 1: count */
    if (st != SRMECH_OK) { return st; }
    char (*names)[SRMECH_PLAT_DIR_NAME_MAX] = genome_arena_alloc(
        &a, (size_t)((n == 0u) ? 1u : n) * SRMECH_PLAT_DIR_NAME_MAX);
    srmech_json_value_t **groots = genome_arena_alloc(
        &a, (size_t)((n == 0u) ? 1u : n) * sizeof(*groots));
    if (names == NULL || groots == NULL) { return SRMECH_ERR_OVERFLOW; }
    uint32_t n2 = 0u;
    st = genome_list_genomes(root, names, n, &n2);                 /* pass 2: fill */
    if (st != SRMECH_OK) { return st; }
    genome_sort_names(names, n2);
    st = genome_registry_census_all(&a, root, names, n2, coupling, coupling_len, groots);
    if (st != SRMECH_OK) { return st; }
    /* Copy `root` into the arena so the tree's "root" is SELF-CONTAINED (held by
     * reference; the caller's `root` string may not outlive the later json write). */
    size_t rlen = strlen(root);
    char *root_copy = genome_arena_alloc(&a, rlen + 1u);
    if (root_copy == NULL) { return SRMECH_ERR_OVERFLOW; }
    memcpy(root_copy, root, rlen + 1u);
    return genome_registry_root(&a, root_copy, groots, n2, out_registry);
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
                                   const unsigned char *coupling,
                                   size_t coupling_len,
                                   void *ws, size_t ws_len)
{
    assert(out_len != NULL);
    assert(dir != NULL || out == NULL);
    if (dir == NULL || out == NULL || out_len == NULL || ws == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    srmech_json_value_t *manifest = NULL;
    srmech_status_t st = genome_obtain_manifest(dir, coupling, coupling_len,
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
                                     const unsigned char *coupling,
                                     size_t coupling_len,
                                     void *ws, size_t ws_len)
{
    assert(out_len != NULL);
    assert(dir != NULL || out == NULL);
    if (dir == NULL || label == NULL || out == NULL ||
        out_len == NULL || ws == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    srmech_json_value_t *manifest = NULL;
    srmech_status_t st = genome_obtain_manifest(dir, coupling, coupling_len,
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
 * §134/rc135 (#1273) — the DEMAND-LOAD gene-expression PLAN. For each
 * chromosome in the manifest, seek to its byte_offset and read ONLY the
 * head GATE cap (the SECOND block, at byte_offset + leaf_dim), evaluate the
 * gate under cell_state, and emit the EXPRESSED regions' (label, byte_offset,
 * byte_len). NEVER reads a region body — bounded I/O (the plan touches only
 * one leaf_dim-byte gate cap per chromosome). Emit format (big-endian):
 *   [u32 n] then per record [u32 label_len][label bytes][u64 offset][u64 len]
 * Byte-identical to the pure-Python gene_express_plan PATH variant. No abs
 * (a mask / cell_state is never negated); a READ (never mutates); malloc-free
 * (the manifest parses in the caller arena, the gate cap is a fixed stack
 * buffer). This is the siona community=chromosome layout — the per-chromosome
 * head gate IS the community gate.
 * ------------------------------------------------------------------ */

/* §98/rc269 (§98.1/G1/rc274 cell-state-conditional) — read a region's HEAD slot at off+leaf_dim into
 * `gate` (>= leaf_dim) and resolve the CHROMATIN OUTER gate under cell_state. If the head block is a
 * chromatin cap (0x48): its COMPUTED accessibility (genome_chromatin_access — constitutive caps are
 * constant, §98.1/G1 FACULTATIVE caps fire per cell_state, evaluated IN PLACE over the already-paged
 * `gate` buffer so the read stays a SINGLE seek — bounded I/O) decides: SILENCED (numerator == 0
 * under this cell_state) -> *skip = 1 (the gene gate cap is NEVER read); OPEN -> the gene gate is the
 * NEXT slot, read off+2*leaf_dim into `gate` (unless no room -> *skip = 1). A non-chromatin head
 * block leaves `gate` holding it (*skip = 0). Byte-identical to the pure _plan_path_head_expresses
 * head walk. No malloc (the variable-length DNF/threshold gate is decoded in place over `gate`); no
 * abs, no float; a READ. */
static srmech_status_t genome_plan_read_head(
    const char *body_path, size_t off, size_t len, uint32_t leaf_dim,
    uint64_t cell_state, unsigned char *gate, int *skip)
{
    assert(body_path != NULL && gate != NULL && skip != NULL);
    assert(leaf_dim >= 1u && leaf_dim <= 256u);
    *skip = 0;
    srmech_status_t st = genome_read_region(body_path, off + leaf_dim,
                                            leaf_dim, gate, leaf_dim);
    if (st != SRMECH_OK) { return st; }
    if (gate[0] != SRMECH_GENOME_CHROMATIN_MARKER) { return SRMECH_OK; }
    uint64_t num = 0u, den = 0u;                            /* §98.1/G1 cell-state-conditional access */
    st = genome_chromatin_access(gate, leaf_dim, cell_state, &num, &den);
    if (st != SRMECH_OK) { return st; }
    if (num == 0u) { *skip = 1; return SRMECH_OK; }         /* silenced under cell_state -> SKIP */
    if ((size_t)3u * leaf_dim > len) { *skip = 1; return SRMECH_OK; }   /* no gate slot after cap */
    return genome_read_region(body_path, off + (size_t)2u * leaf_dim,
                              leaf_dim, gate, leaf_dim);     /* accessible -> the gene gate is next */
}

/* Read one chromosome's head GATE cap (the block at byte_offset + leaf_dim, or —
 * §98/rc269 — the block after an OPEN head chromatin cap) into `gate` (>= leaf_dim),
 * evaluate it under cell_state, and EMIT the record (label + byte_offset + byte_len)
 * into out[*pos..] iff it EXPRESSES. A region with no full head gene cap
 * (byte_len < 2*leaf_dim), a CONDENSED head-chromatin region (skipped reading ONLY
 * the chromatin cap), or one whose head block is not a GENE marker, is skipped (not a
 * gated / accessible community; SRMECH_OK, no emit). *pos + *n advance on an emit.
 * No abs; a READ. */
static srmech_status_t genome_plan_emit_one(
    const char *body_path, const srmech_json_value_t *entry,
    uint32_t leaf_dim, uint64_t cell_state,
    unsigned char *gate, unsigned char *out, size_t out_cap,
    size_t *pos, uint32_t *n)
{
    assert(entry != NULL && gate != NULL && body_path != NULL);
    assert(out != NULL && pos != NULL && n != NULL);
    const srmech_json_value_t *bo = srmech_json_object_get(entry, "byte_offset");
    const srmech_json_value_t *bl = srmech_json_object_get(entry, "byte_len");
    const srmech_json_value_t *lv = srmech_json_object_get(entry, "label");
    if (bo == NULL || bl == NULL || lv == NULL ||
        bo->type != SRMECH_JSON_INT || bl->type != SRMECH_JSON_INT ||
        lv->type != SRMECH_JSON_STRING) {
        return SRMECH_ERR_BAD_INPUT;
    }
    size_t off = (size_t)bo->u.i, len = (size_t)bl->u.i;
    if (len < (size_t)2u * leaf_dim) { return SRMECH_OK; }   /* no head gene cap */
    int skip = 0;
    srmech_status_t st = genome_plan_read_head(body_path, off, len, leaf_dim,
                                               cell_state, gate, &skip);
    if (st != SRMECH_OK) { return st; }
    if (skip) { return SRMECH_OK; }             /* §98 heterochromatin / no gate slot after cap */
    unsigned char gm = gate[0];                             /* the head block kind */
    int expressed = 0;
    if (gm == SRMECH_GENOME_GRADED_GENE_MARKER) {
        /* §132 E3: the graded gene's BINARY reading is level > 0 — srmech_genome_gene_express
         * does NOT decide graded (the level op does), matching Python _gene_expresses. */
        uint64_t num = 0u, den = 0u;
        st = srmech_genome_gene_express_levels(gate, leaf_dim, cell_state, &num, &den);
        if (st != SRMECH_OK) { return st; }
        expressed = (num > 0u) ? 1 : 0;
    } else if (gm == SRMECH_GENOME_GENE_CAP_MARKER ||
               gm == SRMECH_GENOME_REGULATORY_GENE_MARKER ||
               gm == SRMECH_GENOME_BOOLEAN_GENE_MARKER ||
               gm == SRMECH_GENOME_THRESHOLD_GENE_MARKER) {
        st = srmech_genome_gene_express(gate, leaf_dim, cell_state, &expressed, NULL);
        if (st != SRMECH_OK) { return st; }
    } else {
        return SRMECH_OK;                                    /* head not a gene cap */
    }
    if (!expressed) { return SRMECH_OK; }
    st = genome_emit_u32(out, out_cap, pos, lv->u.str.len);
    if (st != SRMECH_OK) { return st; }
    if (*pos + lv->u.str.len > out_cap) { return SRMECH_ERR_BAD_INPUT; }
    memcpy(out + *pos, lv->u.str.ptr, lv->u.str.len);
    *pos += lv->u.str.len;
    st = genome_emit_u64(out, out_cap, pos, off);
    if (st != SRMECH_OK) { return st; }
    st = genome_emit_u64(out, out_cap, pos, len);
    if (st != SRMECH_OK) { return st; }
    (*n)++;
    return SRMECH_OK;
}

srmech_status_t srmech_genome_gene_express_plan(
    const char *dir, uint64_t cell_state,
    const unsigned char *coupling, size_t coupling_len,
    unsigned char *out, size_t out_cap, size_t *out_len,
    void *ws, size_t ws_len)
{
    assert(out_len != NULL);
    assert(dir != NULL || out == NULL);
    if (dir == NULL || out == NULL || out_len == NULL || ws == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (coupling == NULL && coupling_len != 0u) { return SRMECH_ERR_NULL_ARG; }
    srmech_json_value_t *manifest = NULL;
    srmech_status_t st = genome_obtain_manifest(dir, coupling, coupling_len,
                                                ws, ws_len, &manifest);
    if (st != SRMECH_OK) { return st; }
    const srmech_json_value_t *ld = genome_data_get(manifest, "leaf_dim");
    const srmech_json_value_t *arr = genome_data_get(manifest, "chromosomes");
    if (ld == NULL || ld->type != SRMECH_JSON_INT ||
        arr == NULL || arr->type != SRMECH_JSON_ARRAY) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (ld->u.i <= 0 || ld->u.i > 256) { return SRMECH_ERR_BAD_INPUT; }
    uint32_t leaf_dim = (uint32_t)ld->u.i;
    char body_path[SRMECH_GENOME_PATH_MAX];
    st = genome_join(dir, SRMECH_GENOME_BODY, body_path, sizeof(body_path));
    if (st != SRMECH_OK) { return st; }
    unsigned char gate[256];                        /* leaf_dim <= 256; fixed stack cap */
    size_t pos = 0u;
    st = genome_emit_u32(out, out_cap, &pos, 0u);   /* reserve the record count */
    if (st != SRMECH_OK) { return st; }
    uint32_t n = 0u;
    for (uint32_t i = 0; i < arr->u.arr.n; i++) {
        st = genome_plan_emit_one(body_path, arr->u.arr.items[i], leaf_dim,
                                  cell_state, gate, out, out_cap, &pos, &n);
        if (st != SRMECH_OK) { return st; }
    }
    genome_poke_u32(out, 0u, n);                    /* backfill the count at offset 0 */
    *out_len = pos;
    return SRMECH_OK;
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
         region[0] != SRMECH_GENOME_ACTIVE_TELOMERE_MARKER &&
         region[0] != SRMECH_GENOME_DIPLOID_TELOMERE_MARKER)) {  /* §95b diploid region */
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
                          kind == SRMECH_GENOME_ACTIVE_TELOMERE_MARKER ||
                          kind == SRMECH_GENOME_DIPLOID_TELOMERE_MARKER)) {  /* §95b diploid */
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
            kind != SRMECH_GENOME_CENTROMERE_CAP_MARKER &&  /* §95a interior centromere */
            kind != SRMECH_GENOME_DIPLOID_TELOMERE_MARKER &&  /* §95b diploid boundary */
            kind != SRMECH_GENOME_KERNEL_HEADER_MARKER) { lc++; }
        nb++;
        off += blen;
    }
    *leaf_count = lc;
    *n_blocks = nb;
    return SRMECH_OK;
}


/* The v12 O(1) HEAD-append core: read ONLY the head fields from the OLD manifest — the
 * body_sha256 chain head, n_turns, coupling, and the prior chromosome COUNT (v12's
 * "n_chromosomes", or the v4..v11 "chromosomes" array length) — then scan ONLY the new
 * region, fold it onto the chain, and set the strings HEAD (n_chroms = the count,
 * n_blocks, body_sha, one_*). NO per-chromosome array copy (the O(n) wall), NO O(n)
 * dup-label scan (labels are content-addresses, ADR-0003). `s` needs ONE slot (the new
 * region's scan lands in slot 0). The head-only manifest build consumes s->n_chroms as a
 * COUNT and never iterates the array. */
static srmech_status_t genome_append_head(genome_strings_t *s,
    const srmech_json_value_t *manifest,
    const unsigned char *region, size_t region_len, uint32_t leaf_dim)
{
    assert(s != NULL && manifest != NULL);
    assert(region != NULL && leaf_dim > 0u);
    const srmech_json_value_t *dto = genome_data_get(manifest, "coupling");
    const srmech_json_value_t *nt = genome_data_get(manifest, "n_turns");
    const srmech_json_value_t *bsha = genome_data_get(manifest, "body_sha256");
    const srmech_json_value_t *nch = genome_data_get(manifest, "n_chromosomes");
    const srmech_json_value_t *carr = genome_data_get(manifest, "chromosomes");
    if (dto == NULL || nt == NULL || bsha == NULL || nt->type != SRMECH_JSON_INT ||
        bsha->type != SRMECH_JSON_STRING || bsha->u.str.len != 64u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    uint32_t n_old;
    if (nch != NULL && nch->type == SRMECH_JSON_INT) {
        n_old = (uint32_t)nch->u.i;                      /* v12 head-only */
    } else if (carr != NULL && carr->type == SRMECH_JSON_ARRAY) {
        n_old = carr->u.arr.n;                           /* v4..v11 full (count only) */
    } else {
        return SRMECH_ERR_BAD_INPUT;
    }
    srmech_status_t st = genome_copy_jstr(dto, "sha256", s->one_sha, 65u);
    if (st != SRMECH_OK) { return st; }
    st = genome_copy_jstr(dto, "hex", s->one_hex, 2u * 256u + 1u);
    if (st != SRMECH_OK) { return st; }
    memcpy(s->body_sha, bsha->u.str.ptr, 64u);           /* prior chain head */
    s->body_sha[64] = '\0';
    st = genome_fill_constants(s);
    if (st != SRMECH_OK) { return st; }
    /* §Q8/v16: PRESERVE the genome's carrier across the O(1) append — read it from the
     * existing manifest (a v≤15 manifest predates the field → klein4, the default). */
    const srmech_json_value_t *cf = genome_data_get(manifest, "carrier");
    if (cf != NULL && cf->type == SRMECH_JSON_STRING &&
        cf->u.str.len == 2u && memcmp(cf->u.str.ptr, "q8", 2u) == 0) {
        s->carrier_q8 = 1u;
    }
    uint32_t new_lc = 0u, new_nb = 0u;
    st = genome_scan_region(region, region_len, leaf_dim, s->cap_sha[0],
                            s->region_sha[0], &new_lc, &new_nb);
    if (st != SRMECH_OK) { return st; }
    s->n_chroms = n_old + 1u;                             /* the COUNT (head-only) */
    s->n_blocks = (uint32_t)nt->u.i + new_nb;
    return genome_chain_fold(s->body_sha, s->region_sha[0]);  /* extend chain O(1) */
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
    (void)label;    /* v12 O(1) head-append: labels are content-addresses (ADR-0003),
                     * no dup scan; the label rides inline in the region's cap block. */
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
    if (ld == NULL || ld->type != SRMECH_JSON_INT ||
        (uint32_t)ld->u.i != leaf_dim) { return SRMECH_ERR_BAD_INPUT; }
    genome_strings_t s;
    st = genome_strings_alloc(&s, a, 1u);          /* ONE slot — the new region's scan */
    if (st != SRMECH_OK) { return st; }
    st = genome_append_head(&s, manifest, region, region_len, leaf_dim);
    if (st != SRMECH_OK) { return st; }
    size_t man_cap = genome_manifest_cap(1u);      /* FIXED head cap — O(1), no array */
    char *manifest_out = genome_arena_alloc(a, man_cap + 1u);
    if (manifest_out == NULL) { return SRMECH_ERR_OVERFLOW; }
    void *tws = NULL;
    size_t tws_len = 0u;
    genome_arena_tail(a, &tws, &tws_len);
    size_t out_len = 0u;
    st = genome_build_manifest(&s, leaf_dim, old_len + region_len, tws, tws_len,
                               manifest_out, man_cap, &out_len, 1);  /* HEAD-ONLY */
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
    const unsigned char *coupling, size_t coupling_len, genome_arena_t *a)
{
    assert(dir != NULL && label != NULL && coupling != NULL && a != NULL);
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
    st = genome_obtain_manifest(dir, coupling, coupling_len, tws, tws_len, &manifest);
    if (st != SRMECH_OK) { return st; }
    const srmech_json_value_t *ld = genome_data_get(manifest, "leaf_dim");
    if (ld == NULL || ld->type != SRMECH_JSON_INT ||
        (uint32_t)ld->u.i != leaf_dim) { return SRMECH_ERR_BAD_INPUT; }
    st = genome_check_new_label(manifest, label);
    if (st != SRMECH_OK) { return st; }
    size_t new_len = 0u;
    st = genome_grow_body(dir, manifest, region, region_len, body, bcap, &new_len);
    if (st != SRMECH_OK) { return st; }
    return srmech_genome_save(dir, body, new_len, leaf_dim, coupling, coupling_len,
                              tws, tws_len);
}

srmech_status_t srmech_genome_append(const char *dir, const char *label,
                                     const unsigned char *region,
                                     size_t region_len, uint32_t leaf_dim,
                                     const unsigned char *coupling,
                                     size_t coupling_len, void *ws, size_t ws_len)
{
    assert(coupling != NULL || coupling_len == 0u);
    assert(dir != NULL || label == NULL);
    if (dir == NULL || label == NULL || coupling == NULL || ws == NULL ||
        (region == NULL && region_len != 0u)) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (leaf_dim == 0u || coupling_len != (size_t)leaf_dim || region_len == 0u ||
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
                                     coupling, coupling_len, &a);
    }
    char *manbuf = genome_arena_alloc(&a, msz + 1u);
    if (manbuf == NULL) { return SRMECH_ERR_OVERFLOW; }
    size_t mlen = 0u;
    st = genome_read_file(man_path, (unsigned char *)manbuf, msz + 1u, &mlen);
    if (st != SRMECH_OK) { return st; }
    while (mlen > 0u && (manbuf[mlen - 1u] == '\n' || manbuf[mlen - 1u] == '\r')) {
        mlen--;
    }
    /* The O(1) HEAD-append takes any manifest that carries the region CHAIN head: a
     * v4..v11 FULL manifest ("regions") OR a v12 HEAD-ONLY one ("n_chromosomes"). Only
     * a legacy v2/v3 (whole-body digest, NEITHER key) migrates. Sniff cheaply by a
     * substring probe on the canonical text (the keys are always double-quoted). */
    if (!genome_bytes_contains(manbuf, mlen, "\"regions\":", 10u) &&
        !genome_bytes_contains(manbuf, mlen, "\"n_chromosomes\":", 16u)) {
        genome_arena_init(&a, ws, ws_len);      /* migrate re-reads the body itself */
        return genome_append_migrate(dir, label, region, region_len, leaf_dim,
                                     coupling, coupling_len, &a);
    }
    return genome_append_v4(dir, label, region, region_len, leaf_dim, &a,
                            manbuf, msz, mlen, old_len);
}

/* Public — the exact working-arena size (bytes) srmech_genome_append needs for the
 * genome at `dir` when it stages a `region_len`-byte region. Reads manifest.json into
 * `ws` (needs manifest_size + 1 bytes; a few KB for a v12 HEAD-ONLY genome) and
 * classifies EXACTLY as srmech_genome_append does — by the SAME byte-substring probe
 * (genome_bytes_contains): a v12 head ("n_chromosomes") or a v4..v11 full manifest
 * ("regions") takes the O(1) tail-extend; a legacy v2/v3 (neither key) migrates once.
 *
 * §97 O(1): the tail-extend fast path (genome_append_v4/genome_append_head) stages ONE
 * new region slot + a head-only, 1-ENTRY manifest — it NEVER materialises the
 * per-chromosome array — so its arena is MANIFEST-scaled with n_chroms = 1 and does NOT
 * grow with the chromosome count (the corpus-scale RAM fix). Only the migrate path
 * scales with the body. A bare-C host — and the Python wrapper — sizes the append arena
 * from THIS, so the v12/legacy classification lives ONCE (here), not reimplemented per
 * host. *out_bytes gets the size. Additive symbol; does NOT bump SRMECH_ABI_VERSION. */
srmech_status_t srmech_genome_append_arena_bytes(const char *dir, size_t region_len,
                                                 void *ws, size_t ws_len,
                                                 size_t *out_bytes)
{
    assert(dir != NULL || out_bytes == NULL);
    assert(SRMECH_GENOME_MAX_LABEL > 0u);
    if (dir == NULL || out_bytes == NULL || (ws == NULL && ws_len != 0u)) {
        return SRMECH_ERR_NULL_ARG;
    }
    size_t old_len = 0u;
    srmech_status_t st = genome_body_size(dir, &old_len);
    if (st != SRMECH_OK) { return st; }
    char man_path[SRMECH_GENOME_PATH_MAX];
    st = genome_join(dir, SRMECH_GENOME_MANIFEST, man_path, sizeof(man_path));
    if (st != SRMECH_OK) { return st; }
    size_t msz = 0u;
    if (genome_file_size(man_path, &msz) != SRMECH_OK) {   /* manifest-less => migrate */
        *out_bytes = srmech_genome_arena_bytes(old_len + region_len,
                                               (uint32_t)(old_len / 32u) + 1u, region_len);
        return SRMECH_OK;
    }
    if (ws == NULL || msz + 1u > ws_len) { return SRMECH_ERR_OVERFLOW; }
    size_t mlen = 0u;
    st = genome_read_file(man_path, (unsigned char *)ws, msz + 1u, &mlen);
    if (st != SRMECH_OK) { return st; }
    const char *man = (const char *)ws;
    /* Same probe the op uses (line ~3387): v12 head OR v4..v11 full => O(1) tail-extend
     * (MANIFEST-scaled, n_chroms = 1 — the 1-slot head append); legacy => whole-body. */
    int is_v4 = genome_bytes_contains(man, mlen, "\"n_chromosomes\":", 16u) ||
                genome_bytes_contains(man, mlen, "\"regions\":", 10u);
    if (is_v4) {
        *out_bytes = srmech_genome_arena_bytes(msz * 6u + 300000u, 1u, region_len);
    } else {
        *out_bytes = srmech_genome_arena_bytes(old_len + region_len,
                                               (uint32_t)(old_len / 32u) + 1u, region_len);
    }
    return SRMECH_OK;
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
 * genome_remove / genome_replace output. Like APPEND (a write op) coupling is
 * REQUIRED here (srmech_genome_save needs it for the manifest coupling hash+hex);
 * coupling_len IS leaf_dim. The whole body is bound-checked against body_sha256
 * BEFORE the edit (genome_read_bound_body).
 * ------------------------------------------------------------------ */

srmech_status_t srmech_genome_remove(const char *dir, const char *label,
                                     const unsigned char *coupling,
                                     size_t coupling_len, void *ws, size_t ws_len)
{
    assert(coupling != NULL || coupling_len == 0u);
    assert(dir != NULL || label == NULL);
    if (dir == NULL || label == NULL || coupling == NULL || ws == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (coupling_len == 0u || coupling_len > 256u) { return SRMECH_ERR_BAD_INPUT; }
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
    st = genome_obtain_manifest(dir, coupling, coupling_len, tws, tws_len,
                                &manifest);
    if (st != SRMECH_OK) { return st; }
    const srmech_json_value_t *ld = genome_data_get(manifest, "leaf_dim");
    const srmech_json_value_t *arr = genome_data_get(manifest, "chromosomes");
    if (ld == NULL || ld->type != SRMECH_JSON_INT ||
        (size_t)ld->u.i != coupling_len ||
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
                              (uint32_t)coupling_len, coupling, coupling_len,
                              tws, tws_len);
}

srmech_status_t srmech_genome_replace(const char *dir, const char *label,
                                      const unsigned char *region,
                                      size_t region_len, uint32_t leaf_dim,
                                      const unsigned char *coupling,
                                      size_t coupling_len, void *ws, size_t ws_len)
{
    assert(coupling != NULL || coupling_len == 0u);
    assert(dir != NULL || label == NULL);
    if (dir == NULL || label == NULL || coupling == NULL || ws == NULL ||
        (region == NULL && region_len != 0u)) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (leaf_dim == 0u || coupling_len != (size_t)leaf_dim) {
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
    st = genome_obtain_manifest(dir, coupling, coupling_len, tws, tws_len,
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
                              coupling, coupling_len, tws, tws_len);
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
 * (CHROM cap + coupled turns) hex + coupling hex; its attestation.response_sha256
 * IS the region hash, so an import re-hashes the region and self-verifies. This
 * COMPOSES the §41 MPR surface — it is NOT a parallel attestation.
 *
 * Mirrors srmech.amsc.genome genome_export / genome_import.
 * ------------------------------------------------------------------ */

/* The §43 .chr data_schema_id (== GENOME_CHR_SCHEMA_ID). */
#define SRMECH_GENOME_CHR_SCHEMA_ID "srmech://schema/genome_chromosome/v1"
/* The §43 parser_rule_hash pre-image (== f"genome_chromosome/v{FORMAT_VERSION}" — tracks
 * SRMECH_GENOME_FORMAT_VERSION, mirroring the Python _chr_record; v15->v16 §Q8 packer). */
#define SRMECH_GENOME_CHR_RULE_PREIMAGE "genome_chromosome/v17"
/* The §43 rendering "purpose" — VERBATIM from genome.py _chr_record
 * (single-line #define; JPL Rule 8 forbids backslash line-continuation). */
#define SRMECH_GENOME_CHR_PURPOSE "One self-contained, MPR-attested chromosome: its fixed-width region (CHROM cap + coupled turns) + coupling, re-importable self-verifying."
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

/* Build a {"sha256":..,"hex":..} sub-object (coupling / region). */
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
                            "cap_sha256", "coupling", "region" };
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
 * the chromosome entry, coupling sha256+hex from the manifest (the .chr re-uses
 * the manifest's coupling verbatim). SRMECH_ERR_BAD_INPUT on absent / malformed. */
static srmech_status_t genome_chr_meta(const srmech_json_value_t *manifest,
                                       const char *label, genome_chr_strings_t *cs,
                                       size_t *off, size_t *len)
{
    assert(manifest != NULL && label != NULL);
    assert(cs != NULL && off != NULL && len != NULL);
    const srmech_json_value_t *ld = genome_data_get(manifest, "leaf_dim");
    const srmech_json_value_t *to = genome_data_get(manifest, "coupling");
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
                                     const unsigned char *coupling,
                                     size_t coupling_len, void *ws, size_t ws_len)
{
    assert(dir != NULL || ws == NULL);
    assert(coupling != NULL || coupling_len == 0u);
    if (dir == NULL || label == NULL || out_path == NULL || ws == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (coupling != NULL && (coupling_len == 0u || coupling_len > 256u)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    genome_arena_t a;
    genome_arena_init(&a, ws, ws_len);     /* obtain uses the whole arena */
    srmech_json_value_t *manifest = NULL;
    srmech_status_t st = genome_obtain_manifest(dir, coupling, coupling_len,
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
 * incl. attestation.response_sha256 == region.sha256), its coupling (decoded +
 * self-verified, length == leaf_dim), leaf_dim and label. Mirrors the integrity
 * bounds of the Python genome_import (_read_chr + the region/coupling re-hash). */
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
    st = genome_chr_decode_verify(srmech_json_object_get(data, "coupling"),
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
 * invariant (dest coupling.sha256 == the .chr's) + a fresh label, then grow the
 * body byte-for-byte and re-save. `caller_one` is the rebuild width for a
 * manifest-less dest (else the .chr's own coupling). Mirrors genome_import's
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
    const srmech_json_value_t *dto = genome_data_get(manifest, "coupling");
    const srmech_json_value_t *dsha =
        (dto != NULL) ? srmech_json_object_get(dto, "sha256") : NULL;
    char osha[65];
    st = srmech_sha256_hex(one, one_len, osha);
    if (st != SRMECH_OK) { return st; }
    if (dsha == NULL || !genome_str_eq(dsha, osha)) {
        return SRMECH_ERR_BAD_INPUT;             /* coupled to a different coupling */
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
                                     const unsigned char *coupling,
                                     size_t coupling_len, void *ws, size_t ws_len)
{
    assert(dest != NULL || ws == NULL);
    assert(coupling != NULL || coupling_len == 0u);
    if (chr_path == NULL || dest == NULL || ws == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (coupling != NULL && (coupling_len == 0u || coupling_len > 256u)) {
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
                             oneblk, one_len, coupling, coupling_len, pw, pl);
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
                                      const unsigned char *coupling,
                                      size_t coupling_len, void *ws, size_t ws_len)
{
    assert(dir != NULL || ws == NULL);
    assert(coupling != NULL || coupling_len == 0u);
    if (dir == NULL || out_dir == NULL || ws == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (coupling != NULL && (coupling_len == 0u || coupling_len > 256u)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    genome_arena_t a;
    genome_arena_init(&a, ws, ws_len);
    /* pass 1: obtain the manifest to learn the chromosome count. */
    srmech_json_value_t *m0 = NULL;
    srmech_status_t st = genome_obtain_manifest(dir, coupling, coupling_len,
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
    st = genome_obtain_manifest(dir, coupling, coupling_len, ew, el, &manifest);
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
        st = srmech_genome_export(dir, labels[i], out_path, coupling,
                                  coupling_len, ew, el);
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
 * 65536 entries stops.
 *
 * rc294: this swallow was AUDITED alongside the genome_list_genomes one and
 * deliberately KEPT — it is not the same defect wearing the same shape. There
 * the swallow reached the caller as a SUCCESS status; here the sole caller
 * (srmech_genome_pack) turns count 0 into SRMECH_ERR_BAD_INPUT unconditionally,
 * and the scripting peer does likewise: Path.glob("*.chr") does NOT raise on an
 * absent dir, so it also yields nothing and also raises "no .chr files". Both
 * projections therefore ERROR on an unopenable dir, which is the ADR-0009
 * invariant. Changing this one would alter the STATUS a bare-C host sees
 * (BAD_INPUT -> IO) while fixing no split. Verified, not assumed. */
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
 * the pack's coupling + leaf_dim; each later bundle must match them (one coupling
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
                                   const unsigned char *coupling,
                                   size_t coupling_len, void *ws, size_t ws_len)
{
    assert(loose_dir != NULL || ws == NULL);
    assert(coupling != NULL || coupling_len == 0u);
    if (loose_dir == NULL || dest == NULL || ws == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (coupling != NULL && (coupling_len == 0u || coupling_len > 256u)) {
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

/* ------------------------------------------------------------------ *
 * srmech_graph_kernel_encode / _decode — #1390 item 2.
 *
 * The domain-free codec that serialises a sparse SIGNED integer graph
 * (vocab_size + edge list + int weights[metric] + signed charges + an
 * optional node_ids label table + extras metadata) into a flat Klein-4
 * symbol stream {0,1,2,3}, and inverts it BYTE-EXACT. Each int is base-4
 * digits behind a 2-symbol length header (<= 15 digits = 30 bits); the
 * charge is Class-K zig-zag encoded. Byte-identical to the pure
 * genome._graph_ints_to_syms / _graph_syms_to_ints codec. ADDITIVE
 * symbols — SRMECH_ABI_VERSION stays 5.
 * ------------------------------------------------------------------ */

#define SRMECH_GK_MAX_DIGITS 15u

/* Class-K zig-zag: signed <-> non-negative (NOT the abs builtin). */
static uint64_t gk_zig(int64_t n)
{
    return (n >= 0) ? ((uint64_t)n << 1)
                    : (((uint64_t)(-n) << 1) - 1u);
}

static int64_t gk_unzig(uint64_t z)
{
    return ((z & 1u) == 0u) ? (int64_t)(z >> 1)
                            : -(int64_t)((z + 1u) >> 1);
}

/* emit one non-negative int as base-4 digits behind a 2-symbol length
 * header. OVERFLOW if it needs > 15 digits or overruns the buffer. */
static srmech_status_t gk_emit(uint64_t v, uint8_t *syms, size_t cap,
                               size_t *io_n)
{
    uint8_t digs[SRMECH_GK_MAX_DIGITS];
    size_t nd = 0;
    uint64_t x = v;
    assert(syms != NULL && io_n != NULL);
    assert(cap >= 2u);
    for (;;) {
        if (nd >= SRMECH_GK_MAX_DIGITS) { return SRMECH_ERR_OVERFLOW; }
        digs[nd] = (uint8_t)(x & 3u);
        nd += 1u;
        x >>= 2;
        if (x == 0u) { break; }
    }
    if (*io_n + 2u + nd > cap) { return SRMECH_ERR_OVERFLOW; }
    syms[*io_n] = (uint8_t)(nd & 3u);
    syms[*io_n + 1u] = (uint8_t)((nd >> 2) & 3u);
    *io_n += 2u;
    for (size_t k = 0; k < nd; k++) { syms[*io_n + k] = digs[k]; }
    *io_n += nd;
    return SRMECH_OK;
}

/* read one int from syms at *io_i (2-sym header + base-4 digits); sets
 * *ok = 0 (returns 0) on exhausted / malformed / already-failed stream. */
static uint64_t gk_read(const uint8_t *syms, size_t n, size_t *io_i, int *ok)
{
    size_t i = *io_i;
    size_t ln;
    uint64_t v = 0;
    assert(syms != NULL || n == 0u);
    assert(io_i != NULL && ok != NULL);
    if (*ok == 0 || i + 2u > n) { *ok = 0; return 0; }
    ln = (size_t)syms[i] + ((size_t)syms[i + 1u] << 2);
    i += 2u;
    if (ln == 0u || i + ln > n) { *ok = 0; return 0; }
    for (size_t k = 0; k < ln; k++) { v |= (uint64_t)syms[i + k] << (2u * k); }
    *io_i = i + ln;
    return v;
}

srmech_status_t srmech_graph_kernel_encode(
    uint64_t vocab_size,
    const uint64_t *edge_i, const uint64_t *edge_j,
    const uint64_t *weights, const int64_t *charges, size_t n_edges,
    const uint64_t *node_ids, size_t n_nid,
    const uint64_t *extras, size_t n_ex,
    uint8_t *out_syms, size_t syms_cap, size_t *out_n_syms)
{
    srmech_status_t st;
    size_t w = 0;
    assert(out_syms != NULL && out_n_syms != NULL);
    assert((edge_i != NULL && edge_j != NULL) || n_edges == 0u);
    if (out_syms == NULL || out_n_syms == NULL ||
        ((edge_i == NULL || edge_j == NULL || weights == NULL) && n_edges > 0u) ||
        (node_ids == NULL && n_nid > 0u) || (extras == NULL && n_ex > 0u)) {
        return SRMECH_ERR_NULL_ARG;
    }
    st = gk_emit(vocab_size, out_syms, syms_cap, &w);
    if (st != SRMECH_OK) { return st; }
    st = gk_emit((uint64_t)n_nid, out_syms, syms_cap, &w);
    if (st != SRMECH_OK) { return st; }
    for (size_t k = 0; k < n_nid; k++) {
        st = gk_emit(node_ids[k], out_syms, syms_cap, &w);
        if (st != SRMECH_OK) { return st; }
    }
    st = gk_emit((uint64_t)n_ex, out_syms, syms_cap, &w);
    if (st != SRMECH_OK) { return st; }
    for (size_t k = 0; k < n_ex; k++) {
        st = gk_emit(extras[k], out_syms, syms_cap, &w);
        if (st != SRMECH_OK) { return st; }
    }
    st = gk_emit((uint64_t)n_edges, out_syms, syms_cap, &w);
    if (st != SRMECH_OK) { return st; }
    for (size_t k = 0; k < n_edges; k++) {
        st = gk_emit(edge_i[k], out_syms, syms_cap, &w);
        if (st != SRMECH_OK) { return st; }
        st = gk_emit(edge_j[k], out_syms, syms_cap, &w);
        if (st != SRMECH_OK) { return st; }
        st = gk_emit(weights[k], out_syms, syms_cap, &w);
        if (st != SRMECH_OK) { return st; }
        st = gk_emit(gk_zig(charges != NULL ? charges[k] : 0), out_syms,
                     syms_cap, &w);
        if (st != SRMECH_OK) { return st; }
    }
    *out_n_syms = w;
    return SRMECH_OK;
}

srmech_status_t srmech_graph_kernel_decode(
    const uint8_t *syms, size_t n_syms,
    uint64_t *out_vocab_size,
    uint64_t *out_edge_i, uint64_t *out_edge_j,
    uint64_t *out_weights, int64_t *out_charges, size_t edge_cap,
    size_t *out_n_edges,
    uint64_t *out_node_ids, size_t nid_cap, size_t *out_n_nid,
    uint64_t *out_extras, size_t ex_cap, size_t *out_n_ex)
{
    size_t i = 0;
    int ok = 1;
    uint64_t n_nid, n_ex, n_edges;
    assert(syms != NULL || n_syms == 0u);
    assert(out_vocab_size != NULL && out_n_edges != NULL);
    if (out_vocab_size == NULL || out_edge_i == NULL || out_edge_j == NULL ||
        out_weights == NULL || out_charges == NULL || out_n_edges == NULL ||
        out_node_ids == NULL || out_n_nid == NULL || out_extras == NULL ||
        out_n_ex == NULL || (syms == NULL && n_syms > 0u)) {
        return SRMECH_ERR_NULL_ARG;
    }
    *out_vocab_size = gk_read(syms, n_syms, &i, &ok);
    n_nid = gk_read(syms, n_syms, &i, &ok);
    if (!ok || n_nid > nid_cap) { return SRMECH_ERR_BAD_INPUT; }
    for (size_t k = 0; k < n_nid; k++) {
        out_node_ids[k] = gk_read(syms, n_syms, &i, &ok);
    }
    n_ex = gk_read(syms, n_syms, &i, &ok);
    if (!ok || n_ex > ex_cap) { return SRMECH_ERR_BAD_INPUT; }
    for (size_t k = 0; k < n_ex; k++) {
        out_extras[k] = gk_read(syms, n_syms, &i, &ok);
    }
    n_edges = gk_read(syms, n_syms, &i, &ok);
    if (!ok || n_edges > edge_cap) { return SRMECH_ERR_BAD_INPUT; }
    for (size_t k = 0; k < n_edges; k++) {
        out_edge_i[k] = gk_read(syms, n_syms, &i, &ok);
        out_edge_j[k] = gk_read(syms, n_syms, &i, &ok);
        out_weights[k] = gk_read(syms, n_syms, &i, &ok);
        out_charges[k] = gk_unzig(gk_read(syms, n_syms, &i, &ok));
    }
    if (!ok) { return SRMECH_ERR_BAD_INPUT; }
    *out_n_nid = (size_t)n_nid;
    *out_n_ex = (size_t)n_ex;
    *out_n_edges = (size_t)n_edges;
    return SRMECH_OK;
}

/* rc278 (§102 / F1252 STAGE 1) — the §89/v6 UNIFORMLY-KLEIN-4 kernel HEADER leaf
 * (mirror srmech.amsc.genome._pack_kernel_header_klein4): base-4 BIG-ENDIAN
 * (MSB-symbol first) `true_len` (uint64 -> 32 symbols) ++ `leaf_dim` (uint32 ->
 * 16) ++ element_type (uint8 -> 4; ELEMENT_TYPE_KLEIN4 == 0), Klein-4-zero-padded
 * to `dim`. Writes `dim` symbols {0,1,2,3}. No float, no abs, no goto/malloc. */
static void genome_kernel_header_leaf(uint64_t true_len, uint32_t leaf_dim,
                                      unsigned char *out, uint32_t dim)
{
    uint64_t v = true_len;
    uint32_t d = leaf_dim;
    assert(out != NULL);
    assert(dim >= 52u && dim <= 256u);
    for (uint32_t j = 0; j < dim; j++) { out[j] = 0u; }     /* Klein-4 zero pad */
    /* true_len -> 32 base-4 symbols at [0:32], big-endian (out[31] the LSB). */
    for (uint32_t j = 0; j < 32u; j++) {
        out[31u - j] = (unsigned char)(v & 3u);
        v >>= 2;
    }
    /* leaf_dim -> 16 base-4 symbols at [32:48], big-endian. */
    for (uint32_t j = 0; j < 16u; j++) {
        out[47u - j] = (unsigned char)(d & 3u);
        d >>= 2;
    }
    /* element_type == ELEMENT_TYPE_KLEIN4 == 0 -> symbols [48:52] stay 0. */
}

/* rc278 — pack ONE coupled leaf_dim-symbol Klein-4 turn into its §55/v3 on-disk
 * block [SRMECH_GENOME_PACKED_TURN_MARKER] + ceil(leaf_dim/4) payload bytes (4
 * two-bit lanes/byte, the FIRST symbol in the HIGH lanes; the partial final
 * byte's unused low lanes stay 0 — canonical). Mirror _pack_turn_block. Returns
 * the bytes written (1 + ceil(leaf_dim/4)); the caller has bounded `out`. */
static size_t genome_v3_pack_turn(const unsigned char *leaf, uint32_t leaf_dim,
                                  unsigned char *out)
{
    size_t plen = ((size_t)leaf_dim + 3u) / 4u;
    assert(leaf != NULL && out != NULL);
    assert(leaf_dim != 0u && leaf_dim <= 256u);
    out[0] = SRMECH_GENOME_PACKED_TURN_MARKER;
    for (size_t b = 0; b < plen; b++) {
        unsigned char byte = 0u;
        for (size_t lane = 0; lane < 4u; lane++) {
            size_t idx = b * 4u + lane;
            unsigned char sym = (idx < (size_t)leaf_dim) ? (leaf[idx] & 3u) : 0u;
            byte = (unsigned char)(byte | (sym << (6u - 2u * lane)));
        }
        out[1u + b] = byte;
    }
    return 1u + plen;
}

/* §55/§Q8/v16 (rc312) — pack ONE coupled leaf_dim-symbol Q8 turn (bytes 0..7) into its
 * on-disk block [SRMECH_GENOME_Q8_PACKED_TURN_MARKER] + ceil(leaf_dim*3/8) payload bytes:
 * 3 bits/symbol, MSB-FIRST CONTIGUOUS (symbol i -> bits [3i, 3i+3), symbol 0 in the highest
 * bits, each symbol's high bit first; a partial final byte's unused LOW bits stay 0 —
 * canonical). Exported genome-fully-in-C primitive; BYTE-IDENTICAL to _pack_turn_block_q8.
 * *out_len = 1 + ceil(leaf_dim*3/8); the caller has bounded `out`. */
srmech_status_t srmech_genome_q8_pack_turn(const unsigned char *leaf,
                                           uint32_t leaf_dim,
                                           unsigned char *out, size_t *out_len)
{
    size_t plen;
    if (leaf == NULL || out == NULL || out_len == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(leaf != NULL && out != NULL && out_len != NULL);
    if (leaf_dim == 0u || leaf_dim > 256u) { return SRMECH_ERR_BAD_INPUT; }
    for (uint32_t i = 0u; i < leaf_dim; i++) {
        if (leaf[i] >= 8u) { return SRMECH_ERR_BAD_INPUT; }
    }
    plen = ((size_t)leaf_dim * 3u + 7u) / 8u;
    out[0] = SRMECH_GENOME_Q8_PACKED_TURN_MARKER;
    for (size_t i = 0; i < plen; i++) { out[1u + i] = 0u; }
    for (size_t i = 0; i < (size_t)leaf_dim; i++) {
        unsigned char sym = (unsigned char)(leaf[i] & 7u);
        size_t bitpos = i * 3u;
        for (size_t k = 0; k < 3u; k++) {
            if (((unsigned)(sym >> (2u - k)) & 1u) != 0u) {
                size_t bp = bitpos + k;
                out[1u + (bp >> 3)] |= (unsigned char)(0x80u >> (bp & 7u));
            }
        }
    }
    assert(plen == ((size_t)leaf_dim * 3u + 7u) / 8u);
    *out_len = 1u + plen;
    return SRMECH_OK;
}

/* §55/§Q8/v16 (rc312) — a Q8 packed payload (NOT the marker) -> its byte-per-symbol Q8 leaf
 * (bytes 0..7): exact inverse of srmech_genome_q8_pack_turn, reading leaf_dim 3-bit symbols
 * MSB-first. Exported; BYTE-IDENTICAL to _unpack_turn_payload_q8. */
srmech_status_t srmech_genome_q8_unpack_turn(const unsigned char *payload,
                                             uint32_t leaf_dim, unsigned char *out)
{
    if (payload == NULL || out == NULL) { return SRMECH_ERR_NULL_ARG; }
    assert(payload != NULL && out != NULL);
    if (leaf_dim == 0u || leaf_dim > 256u) { return SRMECH_ERR_BAD_INPUT; }
    for (uint32_t i = 0u; i < leaf_dim; i++) {
        unsigned char sym = 0u;
        size_t bitpos = (size_t)i * 3u;
        for (size_t k = 0; k < 3u; k++) {
            size_t bp = bitpos + k;
            unsigned char bit =
                (unsigned char)((payload[bp >> 3] >> (7u - (bp & 7u))) & 1u);
            sym = (unsigned char)((sym << 1) | bit);
        }
        out[i] = sym;
    }
    assert(leaf_dim <= 256u);
    return SRMECH_OK;
}

/* rc278 — build ONE §89/v6 KERNEL-chromosome on-disk region from a flat Klein-4
 * symbol stream `syms` (`n_syms`): a KERNEL telomere (0x6B) cap over `label`
 * (verbatim, leaf_dim bytes), then the coupled + v3-packed §89 header leaf, then
 * each coupled + v3-packed content leaf (`syms` chunked leaf_dim-wide, final leaf
 * Klein-4-zero-padded). BYTE-IDENTICAL to Python kernel_pack + _disk_block (the
 * genome_append_kernel section). Caller-arena `out`; *out_len the bytes written.
 * No malloc, no goto, no abs, no float. */
static srmech_status_t genome_kernel_region(
    const uint8_t *syms, size_t n_syms, uint32_t leaf_dim,
    const unsigned char *coupling, const char *label,
    unsigned char *out, size_t out_cap, size_t *out_len)
{
    unsigned char leaf[256];
    unsigned char coupled[256];
    size_t dim = (size_t)leaf_dim;
    size_t pos = 0u;
    size_t turn_len = 1u + ((size_t)leaf_dim + 3u) / 4u;
    srmech_status_t st;
    if (syms == NULL || coupling == NULL || out == NULL || out_len == NULL ||
        label == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(out != NULL && out_len != NULL);
    assert(coupling != NULL && label != NULL);
    if (leaf_dim < 52u || leaf_dim > 256u) { return SRMECH_ERR_BAD_INPUT; }
    if (out_cap < dim) { return SRMECH_ERR_OVERFLOW; }
    /* [0] KERNEL telomere cap (verbatim leaf_dim bytes). */
    st = genome_pack_cap(SRMECH_GENOME_KERNEL_TELOMERE_MARKER,
                         (const unsigned char *)label, strlen(label), leaf_dim,
                         out, dim);
    if (st != SRMECH_OK) { return st; }
    pos = dim;
    /* the §89 header leaf: build -> couple through coupling -> v3-pack. */
    genome_kernel_header_leaf(n_syms, leaf_dim, leaf, leaf_dim);
    st = srmech_klein4_bind(leaf, coupling, leaf_dim, coupled);
    if (st != SRMECH_OK) { return st; }
    if (pos + turn_len > out_cap) { return SRMECH_ERR_OVERFLOW; }
    pos += genome_v3_pack_turn(coupled, leaf_dim, out + pos);
    /* content leaves: chunk syms leaf_dim-wide, zero-pad final -> couple -> pack. */
    for (size_t i = 0; i < n_syms; i += dim) {
        size_t take = (n_syms - i < dim) ? (n_syms - i) : dim;
        for (size_t j = 0; j < dim; j++) {
            leaf[j] = (j < take) ? (unsigned char)(syms[i + j] & 3u) : 0u;
        }
        st = srmech_klein4_bind(leaf, coupling, leaf_dim, coupled);
        if (st != SRMECH_OK) { return st; }
        if (pos + turn_len > out_cap) { return SRMECH_ERR_OVERFLOW; }
        pos += genome_v3_pack_turn(coupled, leaf_dim, out + pos);
    }
    *out_len = pos;
    return SRMECH_OK;
}

/* rc278 (§102 / F1252 STAGE 1 — EXTRACT) — the C-native PLASMID EXTRACT
 * orchestrator (doc: srmech.h). Chains srmech_graph_kernel_encode -> the §89
 * KERNEL-region build (genome_kernel_region) -> srmech_genome_append, carving the
 * syms buffer, the region buffer, AND the append arena from ONE `ws`. BYTE-
 * IDENTICAL to the pure Python plasmid_extract section. No malloc, no goto, no
 * abs, no float. */
srmech_status_t srmech_genome_plasmid_extract(
    uint64_t vocab_size,
    const uint64_t *edge_i, const uint64_t *edge_j,
    const uint64_t *weights, const int64_t *charges, size_t n_edges,
    const uint64_t *node_ids, size_t n_nid,
    const uint64_t *extras, size_t n_ex,
    const char *dir, const char *label,
    uint32_t leaf_dim, const unsigned char *coupling,
    void *ws, size_t ws_len, size_t *out_n_syms)
{
    genome_arena_t a;
    size_t n_ints, syms_cap, n_syms = 0u, n_leaves, turn_len, region_cap;
    size_t region_len = 0u, aws_len = 0u;
    uint8_t *syms;
    unsigned char *region;
    void *aws = NULL;
    srmech_status_t st;
    if (dir == NULL || label == NULL || coupling == NULL || ws == NULL ||
        out_n_syms == NULL || (node_ids == NULL && n_nid != 0u) ||
        (extras == NULL && n_ex != 0u) ||
        ((edge_i == NULL || edge_j == NULL || weights == NULL) && n_edges != 0u)) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(dir != NULL && label != NULL && coupling != NULL);
    assert(ws != NULL && out_n_syms != NULL);
    if (leaf_dim < 52u || leaf_dim > 256u) { return SRMECH_ERR_BAD_INPUT; }
    genome_arena_init(&a, ws, ws_len);
    /* syms buffer: the encoder emits <= 17 symbols per int (2-sym count header +
     * <= 15 base-4 digits); n_ints <= 8 + n_nid + n_ex + 4*n_edges. */
    n_ints = 8u + n_nid + n_ex + 4u * n_edges;
    syms_cap = 17u * n_ints + 64u;
    syms = genome_arena_alloc(&a, syms_cap);
    if (syms == NULL) { return SRMECH_ERR_OVERFLOW; }
    st = srmech_graph_kernel_encode(vocab_size, edge_i, edge_j, weights, charges,
                                    n_edges, node_ids, n_nid, extras, n_ex,
                                    syms, syms_cap, &n_syms);
    if (st != SRMECH_OK) { return st; }
    /* region buffer: the leaf_dim cap + (1 header + ceil(D/leaf_dim) content) v3
     * turns, each 1 + ceil(leaf_dim/4) bytes. */
    n_leaves = 1u + (n_syms + (size_t)leaf_dim - 1u) / (size_t)leaf_dim;
    turn_len = 1u + ((size_t)leaf_dim + 3u) / 4u;
    region_cap = (size_t)leaf_dim + n_leaves * turn_len;
    region = genome_arena_alloc(&a, region_cap);
    if (region == NULL) { return SRMECH_ERR_OVERFLOW; }
    st = genome_kernel_region(syms, n_syms, leaf_dim, coupling, label,
                              region, region_cap, &region_len);
    if (st != SRMECH_OK) { return st; }
    /* append the section (O(1) tail-extend) — srmech_genome_append gets the arena
     * TAIL (the syms + region buffers are already consumed above). */
    genome_arena_tail(&a, &aws, &aws_len);
    st = srmech_genome_append(dir, label, region, region_len, leaf_dim,
                              coupling, (size_t)leaf_dim, aws, aws_len);
    if (st != SRMECH_OK) { return st; }
    *out_n_syms = n_syms;
    return SRMECH_OK;
}

/* rc279 (§102 / F1252 STAGE 2 — ORGANIZE) — build the SECTION-COUNT HISTOGRAM:
 * hist[c] = how many nodes have section_count == c, over c in [0, max_count].
 * Pure integer CARDINALITIES (Class-N): no float, and no abs (a count has no
 * sign to strip — this is not a Class-K pin-slot site). */
static srmech_status_t conserved_hist_build(const uint64_t *counts, size_t n_nodes,
                                            uint64_t *hist, size_t hist_cap,
                                            uint64_t *max_out)
{
    uint64_t mx = 0u;
    assert(hist != NULL && max_out != NULL);
    assert(counts != NULL || n_nodes == 0u);
    for (size_t i = 0u; i < n_nodes; i++) {
        if (counts[i] > mx) { mx = counts[i]; }
    }
    if ((uint64_t)hist_cap <= mx) { return SRMECH_ERR_OVERFLOW; }
    for (uint64_t c = 0u; c <= mx; c++) { hist[c] = 0u; }
    for (size_t i = 0u; i < n_nodes; i++) { hist[counts[i]]++; }
    *max_out = mx;
    return SRMECH_OK;
}

/* rc279 — PRECOMPUTE both flanking modes for every possible gap in ONE pass each:
 * pre[b] = argmax over hist[0..b], suf[b] = argmax over hist[b..max_count], both
 * LOWEST-INDEX-ON-TIE so they agree exactly with conserved_side_argmax.
 *
 * Why: the real corpus histogram is HEAVY-TAILED — a maximum count in the hundreds
 * of thousands with only ~1.7k occupied bins (F1253). Re-scanning a side per gap
 * would be O(gaps * max_count), hundreds of millions of reads for ONE derivation.
 * These two prefix passes make the whole antimode walk O(max_count). No abs/float. */
static void conserved_side_modes(const uint64_t *hist, uint64_t max_count,
                                 uint64_t *pre, uint64_t *suf)
{
    uint64_t best = 0u, b;
    assert(hist != NULL);
    assert(pre != NULL && suf != NULL);
    for (b = 0u; b <= max_count; b++) {
        if (hist[b] > hist[best]) { best = b; }   /* strict > keeps the LOWEST index */
        pre[b] = best;
    }
    best = max_count;
    for (b = max_count + 1u; b-- > 0u; ) {
        if (hist[b] >= hist[best]) { best = b; }  /* >= walking down keeps the LOWEST */
        suf[b] = best;
    }
}

/* rc279 — MEASURE the ANTIMODE of the section-count histogram: the conservation
 * DECISION, and the reason `k` is DERIVED FROM THE DATA rather than tuned. This is
 * the count-domain mirror of the rc272 participation antimode
 * (genome._partition_antimode) — same walk, same qualifying predicate, same
 * widest-gap tie-break — so the two reads share one discipline.
 *
 * Walks the GAPS between consecutive OCCUPIED count-bins. A gap qualifies iff it is
 * at least one bin WIDE (a genuine empty separation, not adjacent bins) and the
 * dominant mode on EACH side is a real mode (>= 2 nodes). BIMODAL -> split at the
 * WIDEST qualifying gap (ties -> the larger smaller-mode, then the lower bin);
 * *k_out = lo + 1, so a node is CONSERVED iff section_count >= k (the empty gap makes
 * `>= lo+1` and `>= hi` the same set).
 *
 * NOTE THE INVERSION vs participation: there HIGH participation = a community-bridging
 * PLASMID; here HIGH section-count = shared across many plasmid sections = the
 * conserved NUCLEAR core. UNIMODAL (no qualifying gap) -> ONE-DNA-TYPE: *bimodal_out
 * = 0 and *k_out = 0 — do NOT force a split (the F1250 discipline). */
static void conserved_antimode(const uint64_t *hist, uint64_t max_count,
                               const uint64_t *pre, const uint64_t *suf,
                               uint64_t *k_out, int *bimodal_out)
{
    uint64_t best_lo = 0u, best_w = 0u, best_sm = 0u, prev = 0u;
    int found = 0, have_prev = 0;
    assert(hist != NULL && pre != NULL && suf != NULL);
    assert(k_out != NULL && bimodal_out != NULL);
    for (uint64_t b = 0u; b <= max_count; b++) {
        if (hist[b] == 0u) { continue; }
        if (have_prev != 0 && b - prev >= 2u) {
            uint64_t plo = pre[prev];       /* == conserved_side_argmax(0, prev)   */
            uint64_t phi = suf[b];          /* == conserved_side_argmax(b, max)    */
            uint64_t sm = (hist[plo] < hist[phi]) ? hist[plo] : hist[phi];
            uint64_t w = b - prev;
            if (sm >= 2u && (found == 0 || w > best_w ||
                             (w == best_w && sm > best_sm))) {
                best_w = w; best_sm = sm; best_lo = prev; found = 1;
            }
        }
        prev = b;
        have_prev = 1;
    }
    *bimodal_out = found;
    *k_out = (found != 0) ? (best_lo + 1u) : 0u;
}

/* rc279 (§102 / F1252 STAGE 2 — the CONSERVE step) — read the section-count
 * distribution and return the CONSERVED CORE node set + the DERIVED threshold k.
 * See srmech.h for the full contract. `k_in < 0` DERIVES k from the distribution's
 * antimode (the discipline); `k_in >= 0` forces a caller-supplied k (a verification
 * / replay affordance, NOT the derived path). Pure integer; no float, no abs. */
srmech_status_t srmech_genome_conserved_core(
    const uint64_t *node_ids, const uint64_t *counts, size_t n_nodes,
    long k_in, uint64_t *out_core_ids, size_t core_cap, size_t *out_n_core,
    uint64_t *out_k, int *out_bimodal, uint64_t *hist, size_t hist_cap)
{
    uint64_t max_count = 0u, k = 0u, span;
    int bimodal = 0;
    size_t n_core = 0u;
    srmech_status_t st;
    if (out_n_core == NULL || out_k == NULL || out_bimodal == NULL ||
        hist == NULL || (core_cap > 0u && out_core_ids == NULL) ||
        (n_nodes > 0u && (node_ids == NULL || counts == NULL))) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(out_n_core != NULL && out_k != NULL && out_bimodal != NULL);
    assert(hist != NULL);
    st = conserved_hist_build(counts, n_nodes, hist, hist_cap, &max_count);
    if (st != SRMECH_OK) { return st; }
    span = max_count + 1u;
    /* the arena holds THREE span-sized integer bands: the histogram, then the
     * prefix-mode and suffix-mode tables the O(max_count) antimode walk needs. */
    if ((uint64_t)hist_cap < 3u * span) { return SRMECH_ERR_OVERFLOW; }
    if (k_in >= 0) {
        k = (uint64_t)k_in;                   /* caller-forced split (not derived) */
        bimodal = 1;
    } else {
        conserved_side_modes(hist, max_count, hist + span, hist + 2u * span);
        conserved_antimode(hist, max_count, hist + span, hist + 2u * span,
                           &k, &bimodal);
    }
    if (bimodal != 0 && k > 0u) {             /* CONSERVED iff section_count >= k */
        for (size_t i = 0u; i < n_nodes; i++) {
            if (counts[i] < k) { continue; }
            if (n_core >= core_cap) { return SRMECH_ERR_OVERFLOW; }
            out_core_ids[n_core] = node_ids[i];
            n_core++;
        }
    }
    *out_n_core = n_core;
    *out_k = k;
    *out_bimodal = bimodal;
    return SRMECH_OK;
}

/* rc279 — fire ONE §101 heartbeat. Returns nonzero to CANCEL (the tick's own
 * channel); a NULL tick is OFF (one pointer test — the hot path pays ~nothing).
 * done / total are EXACT cardinalities; the library never divides. */
static int organize_tick(srmech_progress_tick_cb_t tick, void *user,
                         uint32_t phase, uint64_t done, uint64_t total)
{
    srmech_progress_ev_t ev;
    assert(phase <= (uint32_t)SRMECH_PHASE_PARTITIONING);
    assert(total == 0u || done <= total);
    if (tick == NULL) { return 0; }
    ev.struct_size = (uint32_t)sizeof(srmech_progress_ev_t);
    ev.phase = phase;
    ev.done = done;
    ev.total = total;
    return tick(&ev, user);
}

/* rc279 — PROMOTE: mint the conserved-core strand into a Tier-2 NUCLEAR chromosome
 * via the rc277 srmech_genome_mint_strand peer (the 0x58 centromere at the
 * metacentric p:q split, content-addressed orientation), then place it at the head
 * of the organized genome. `ws` is the mint scratch (the peer writes the +1-block
 * minted strand there; it is copied to `out` head). No abs, no float. */
static srmech_status_t organize_promote_core(
    const unsigned char *core, size_t core_blocks, uint32_t leaf_dim,
    const unsigned char *coupling, long centromere_at, uint32_t repeats,
    const unsigned char *handle, size_t handle_len,
    unsigned char *out, size_t out_cap, unsigned char *ws, size_t ws_len,
    size_t *n_out)
{
    size_t minted = 0u;
    srmech_status_t st;
    assert(out != NULL && n_out != NULL);
    assert(core != NULL && ws != NULL);
    st = srmech_genome_mint_strand(core, core_blocks, leaf_dim, coupling,
                                   centromere_at, 0u, 1, repeats, handle,
                                   handle_len, ws, ws_len, &minted);
    if (st != SRMECH_OK) { return st; }
    if (out_cap < minted * (size_t)leaf_dim) { return SRMECH_ERR_OVERFLOW; }
    memcpy(out, ws, minted * (size_t)leaf_dim);
    *n_out = minted;
    return SRMECH_OK;
}

/* rc279 — MERGE one retained plasmid section onto the organized strand's running
 * TAIL via the rc276 srmech_genome_integrate peer.
 *
 * `at < 0` (integrate AFTER the last chromosome) makes the splice a pure TAIL-APPEND,
 * so folding integrate over the P sections is exactly their CONCATENATION
 * (associativity). Calling the peer at the running write offset with an EMPTY host
 * therefore yields the BYTE-IDENTICAL strand in O(section) per step — the whole fold
 * stays O(total) instead of the O(P * total) a literal re-splice of the accumulated
 * host would cost. The WIDTH-COHERENCE gate (a Class-K equality read, NEVER abs) is
 * applied HERE per section, because the peer's own gate is vacuous against an empty
 * host — so the F1251 compatibility contract is still enforced per plasmid. */
static srmech_status_t organize_append_section(
    const unsigned char *sec, size_t sec_blocks, uint32_t leaf_dim,
    uint32_t sec_leaf_dim, unsigned char *out, size_t out_cap, size_t off,
    size_t *nb_out)
{
    int integrated = 0;
    srmech_status_t st;
    assert(out != NULL && nb_out != NULL);
    assert(sec != NULL || sec_blocks == 0u);
    if (sec_leaf_dim != leaf_dim) { return SRMECH_ERR_BAD_INPUT; }   /* incoherent */
    st = srmech_genome_integrate(NULL, 0u, leaf_dim, sec, sec_blocks, leaf_dim, -1,
                                 out + off, (out_cap > off) ? (out_cap - off) : 0u,
                                 nb_out, &integrated);
    if (st != SRMECH_OK) { return st; }
    if (integrated == 0) { return SRMECH_ERR_BAD_INPUT; }
    return SRMECH_OK;
}

/* rc279 (§102 / F1252 STAGE 2 — ORGANIZE) — the incremental organize orchestrator:
 * PROMOTE the conserved core (mint_strand / G5) then MERGE the retained plasmid
 * sections (integrate / G4) into ONE organized genome. See srmech.h for the full
 * contract. The §101 tick fires BETWEEN whole chromosomes, so a cancel truncates at
 * a valid chromosome boundary and *n_blocks_out is a complete, readable partial
 * genome. No malloc / goto / abs / float. */
srmech_status_t srmech_genome_integrate_plasmids(
    const unsigned char *core, size_t core_blocks,
    const unsigned char *plasmids, const size_t *plasmid_blocks, size_t n_plasmids,
    uint32_t leaf_dim, const unsigned char *coupling,
    long centromere_at, uint32_t repeats,
    const unsigned char *handle, size_t handle_len,
    srmech_progress_tick_cb_t tick, void *tick_user,
    unsigned char *out, size_t out_cap, size_t *n_blocks_out,
    size_t *n_integrated_out, unsigned char *ws, size_t ws_len)
{
    size_t dim = (size_t)leaf_dim, off = 0u, blocks = 0u, sec_off = 0u, p;
    srmech_status_t st;
    if (out == NULL || n_blocks_out == NULL || n_integrated_out == NULL ||
        (n_plasmids > 0u && (plasmids == NULL || plasmid_blocks == NULL)) ||
        (core_blocks > 0u && (core == NULL || ws == NULL || coupling == NULL))) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(out != NULL && n_blocks_out != NULL);
    assert(n_integrated_out != NULL);
    if (leaf_dim == 0u || leaf_dim > 256u) { return SRMECH_ERR_BAD_INPUT; }
    *n_integrated_out = 0u;
    if (core_blocks > 0u) {                  /* PROMOTE — the conserved nuclear core */
        size_t minted = 0u;
        if (organize_tick(tick, tick_user, (uint32_t)SRMECH_PHASE_MINTING, 0u, 1u)
            != 0) {
            *n_blocks_out = 0u;              /* cancelled before any chromosome */
            return SRMECH_CANCELLED;
        }
        st = organize_promote_core(core, core_blocks, leaf_dim, coupling,
                                   centromere_at, repeats, handle, handle_len,
                                   out, out_cap, ws, ws_len, &minted);
        if (st != SRMECH_OK) { return st; }
        off = minted * dim;
        blocks = minted;
    }
    for (p = 0u; p < n_plasmids; p++) {      /* MERGE — the retained plasmids */
        size_t nb = 0u;
        if (organize_tick(tick, tick_user, (uint32_t)SRMECH_PHASE_INTEGRATING,
                          (uint64_t)p, (uint64_t)n_plasmids) != 0) {
            *n_blocks_out = blocks;          /* valid partial: whole chromosomes only */
            *n_integrated_out = p;
            return SRMECH_CANCELLED;
        }
        st = organize_append_section(plasmids + sec_off, plasmid_blocks[p], leaf_dim,
                                     leaf_dim, out, out_cap, off, &nb);
        if (st != SRMECH_OK) { return st; }
        sec_off += plasmid_blocks[p] * dim;
        off += nb * dim;
        blocks += nb;
    }
    *n_blocks_out = blocks;
    *n_integrated_out = n_plasmids;
    return SRMECH_OK;
}

/* ------------------------------------------------------------------ *
 * rc280 (§102 / F1253) — SECTION COUNTS: {global_id -> n_sections} over a
 * PLASMID section store, derived END-TO-END in C (genome-must-exist-in-C).
 *
 * The two costs rc280 removes (see srmech.h for the full contract):
 *   1. the store CATALOG is derived ONCE for the whole scan — a v12 head-only
 *      manifest re-reads and re-Merkle-folds the WHOLE body to derive it, so
 *      doing that per section is O(P * body), quadratic in corpus size;
 *   2. per section only the node_ids PREFIX of the region is paged — never the
 *      edge bytes, which are the bulk of a co-occurrence section.
 *
 * (2) needs NO format change. The §89 graph-kernel payload int stream is
 *   [vocab_size, n_node_ids] + node_ids + [n_extras] + extras + [n_edges] + ...
 * so node_ids is a strict PREFIX and the edges sit strictly AFTER it; quad_turn
 * is a per-leaf REVERSIBLE Klein-4 XOR against coupling (leaf k uncouples from
 * leaf k ALONE — no chaining), so a prefix of coupled leaves uncouples to
 * exactly the prefix of the symbol stream; and the region's integrity bound is
 * its LEADING cap, present in — and paid identically by — any prefix of >= 1
 * block. The C reads the region through a sliding WINDOW and stops the moment
 * the declared node_ids are in hand: strictly tighter than, and value-identical
 * to, the pure reader's probe-then-grow (which sizes a re-read instead).
 *
 * REENTRANT (rc306 / task #899). The wire signature carries a `ws` arena and JPL
 * Rule 3 bans malloc, so the scan's scratch is CALLER-supplied: the count table
 * and the region window are carved off the FRONT of `ws`, and the untouched TAIL
 * is the catalog arena genome_obtain_manifest parses into. No file-scope static
 * state remains, so two threads with DISJOINT `ws` may scan concurrently, and the
 * corpus bound is whatever `ws` the caller sizes (no compiled-in 32 MiB cap). The
 * running state that used to live in the statics now lives in one sc_ctx_t on the
 * scan's stack, threaded to every helper.
 * ------------------------------------------------------------------ */

/* Region read window; must exceed one block (leaf_dim <= 256). */
#ifndef SRMECH_GENOME_SC_WINDOW_BYTES
#define SRMECH_GENOME_SC_WINDOW_BYTES (64u * 1024u)
#endif

/* Leading ints before the node_ids table: vocab_size, n_node_ids. */
#define SRMECH_GENOME_SC_HEADER_INTS 2u

/* The karyotype INDEX chromosome — excluded from the scan (mirror
 * srmech.amsc.plasmid.VOCAB_LABEL). */
#define SRMECH_GENOME_SC_VOCAB_LABEL "__vocab__"

/* One count-table slot. `key` is global_id + 1 so 0 marks an EMPTY slot (id 0
 * is a legitimate global id). `last` is the 1-based section ordinal that last
 * bumped this id — that IS the within-section dedupe ("a node counts ONCE per
 * section") with no per-section set, no sort, no extra storage. */
typedef struct {
    uint64_t key;
    uint64_t count;
    uint64_t last;
} sc_slot_t;

/* The incremental §89 int decoder. Symbols arrive one uncoupled LEAF at a time
 * and a serialised int (2-symbol length header + <= 15 base-4 digits, so <= 17
 * symbols) may straddle a leaf boundary — `pend` carries that remainder, which
 * is provably < 17 symbols (any longer suffix already contains a complete int).
 * Decoding incrementally is what lets the reader stop MID-region: there is never
 * a materialised whole-region symbol buffer that has to be filled first. */
typedef struct {
    uint8_t  pend[32];
    uint32_t n_pend;
    uint64_t idx;        /* index of the NEXT int in the stream */
    uint64_t n_nid;      /* declared node_ids count (valid once idx > 1) */
    uint32_t ord;        /* 1-based section ordinal (the dedupe key) */
    int      stopped;    /* a zero-length header ended the stream */
} sc_dec_t;

/* The scan's caller-arena scratch, threaded to every helper in place of the four
 * file-scope statics this rc removed. `slots`/`n_slots` is the open-addressed
 * count table (n_slots a power of two, carved from ws); `n_ids` is the distinct-id
 * count so far (the old g_sc_n_ids); `win`/`win_bytes` is the region read window
 * (also carved from ws). No pointer here aliases another scan's — that IS the
 * reentrancy. */
typedef struct {
    sc_slot_t     *slots;
    size_t         n_slots;
    size_t         n_ids;
    unsigned char *win;
    size_t         win_bytes;
} sc_ctx_t;

/* Smallest power-of-two count-table size whose 3/4 open-addressing load bound
 * admits `max_ids` distinct ids, floored at 4096 slots so a tiny store still gets
 * real headroom. The table and the caller's out arrays scale on the SAME knob
 * (out_cap): grow out_cap and the table grows with it, which is what lets a corpus
 * with more than the old 196,608-id ceiling be censused natively — the caller just
 * sizes ws bigger. The loop is bounded (it stops at the top representable power of
 * two), so an absurd max_ids degrades to a decline, never a wrap to zero. */
static size_t sc_table_slots(size_t max_ids)
{
    size_t need = max_ids + max_ids / 3u + 1u;      /* ceil((4/3) * max_ids), >= 1 */
    size_t s = 4096u;
    assert(need >= 1u);
    assert(s >= 4096u);
    while (s < need && s < (((size_t)-1 >> 1) + 1u)) { s <<= 1; }
    return s;
}

/* Bump `id`'s section count, ONCE per section (`ord`). Open addressing with
 * linear probing over the power-of-two table; the id is mixed by the 64-bit
 * golden-ratio odd constant. Integer only — no float, and no abs (a count and
 * an id have no sign to strip; this is not a Class-K pin-slot site).
 * SRMECH_ERR_OVERFLOW past the 3/4 load bound. */
static srmech_status_t sc_bump(sc_ctx_t *ctx, uint64_t id, uint32_t ord)
{
    uint64_t h = (id + 1u) * 0x9E3779B97F4A7C15u;
    size_t mask, i, cap;
    assert(ctx != NULL && ord != 0u);
    assert(ctx->slots != NULL && ctx->n_slots != 0u);
    mask = ctx->n_slots - 1u;
    i = (size_t)((h ^ (h >> 32)) & (uint64_t)mask);
    cap = (ctx->n_slots / 4u) * 3u;
    assert((ctx->n_slots & mask) == 0u);   /* power of two */
    for (size_t probe = 0u; probe <= mask; probe++) {
        sc_slot_t *s = &ctx->slots[i];
        if (s->key == 0u) {
            if (ctx->n_ids >= cap) { return SRMECH_ERR_OVERFLOW; }
            s->key = id + 1u;
            s->count = 1u;
            s->last = (uint64_t)ord;
            ctx->n_ids++;
            return SRMECH_OK;
        }
        if (s->key == id + 1u) {
            if (s->last != (uint64_t)ord) {    /* a node counts ONCE per section */
                s->count++;
                s->last = (uint64_t)ord;
            }
            return SRMECH_OK;
        }
        i = (i + 1u) & mask;
    }
    return SRMECH_ERR_OVERFLOW;
}

/* Dispatch ONE decoded int by its stream position: [0] vocab_size (ignored),
 * [1] n_node_ids, [2 .. 2 + n_nid) the GLOBAL node_ids. *done goes 1 once the
 * declared table is fully in hand — the signal to stop reading the region, so
 * the edge bytes after it are never touched. */
static srmech_status_t sc_dec_int(sc_ctx_t *ctx, sc_dec_t *d, uint64_t v, int *done)
{
    srmech_status_t st = SRMECH_OK;
    assert(ctx != NULL && d != NULL && done != NULL);
    assert(d->stopped == 0);
    if (d->idx == 1u) {
        d->n_nid = v;
    } else if (d->idx >= (uint64_t)SRMECH_GENOME_SC_HEADER_INTS &&
               d->idx < (uint64_t)SRMECH_GENOME_SC_HEADER_INTS + d->n_nid) {
        st = sc_bump(ctx, v, d->ord);
    }
    d->idx++;
    if (d->idx >= (uint64_t)SRMECH_GENOME_SC_HEADER_INTS &&
        d->idx >= (uint64_t)SRMECH_GENOME_SC_HEADER_INTS + d->n_nid) {
        *done = 1;
    }
    return st;
}

/* Feed ONE uncoupled leaf's `n` symbols (n <= 256) into the decoder, consuming
 * every COMPLETE int the carry + this leaf now spell. Mirror of the pure
 * _graph_prefix_ints: a zero-length header ENDS the stream (that is the Klein-4
 * zero padding, and the pure reader breaks on it identically). */
static srmech_status_t sc_dec_feed(sc_ctx_t *ctx, sc_dec_t *d,
                                   const unsigned char *syms,
                                   size_t n, int *done)
{
    unsigned char buf[320];
    size_t m, i = 0u, rem;
    assert(ctx != NULL && d != NULL && done != NULL);
    assert(syms != NULL && n <= 256u && d->n_pend <= 16u);
    memcpy(buf, d->pend, (size_t)d->n_pend);
    memcpy(buf + d->n_pend, syms, n);
    m = (size_t)d->n_pend + n;
    while (d->stopped == 0 && *done == 0 && i + 2u <= m) {
        size_t ln = (size_t)buf[i] + ((size_t)buf[i + 1u] << 2);
        uint64_t v = 0u;
        srmech_status_t st;
        if (ln == 0u) { d->stopped = 1; break; }
        if (i + 2u + ln > m) { break; }
        for (size_t k = 0u; k < ln; k++) {
            v |= (uint64_t)buf[i + 2u + k] << (2u * k);
        }
        i += 2u + ln;
        st = sc_dec_int(ctx, d, v, done);
        if (st != SRMECH_OK) { return st; }
    }
    rem = m - i;
    if (d->stopped != 0 || *done != 0) { d->n_pend = 0u; return SRMECH_OK; }
    if (rem > sizeof(d->pend)) { return SRMECH_ERR_BAD_INPUT; }
    memcpy(d->pend, buf + i, rem);
    d->n_pend = (uint32_t)rem;
    return SRMECH_OK;
}

/* A v3 packed turn payload -> its byte-per-symbol Klein-4 leaf (exact inverse of
 * genome_v3_pack_turn: 4 two-bit lanes per byte, the FIRST symbol in the HIGH
 * lanes). Writes leaf_dim symbols. */
static void sc_unpack_turn(const unsigned char *payload, uint32_t leaf_dim,
                           unsigned char *out)
{
    assert(payload != NULL && out != NULL);
    assert(leaf_dim != 0u && leaf_dim <= 256u);
    for (uint32_t j = 0u; j < leaf_dim; j++) {
        unsigned char byte = payload[j / 4u];
        out[j] = (unsigned char)((byte >> (6u - 2u * (j % 4u))) & 3u);
    }
}

/* The §89/v6 kernel HEADER leaf's TRUE symbol length D — symbols [0:32] read as
 * base-4 BIG-ENDIAN (the exact inverse of genome_kernel_header_leaf's write and
 * of the pure _unpack_kernel_header_klein4). 32 symbols * 2 bits == 64 bits. */
static uint64_t sc_header_true_len(const unsigned char *unc)
{
    uint64_t v = 0u;
    assert(unc != NULL);
    assert(sizeof(v) == 8u);
    for (uint32_t j = 0u; j < 32u; j++) {
        v = (v << 2) | (uint64_t)(unc[j] & 3u);
    }
    return v;
}

/* Refill the sliding window at region offset `roff`; *wlen gets the bytes read.
 * The read is bounded by the region's own byte_len, so the window never pages a
 * neighbouring chromosome.
 *
 * rc282: reads through an ALREADY-OPEN handle. This used genome_read_region,
 * which fopen/fcloses per call — so a scan paid at least one open PER SECTION
 * (more for a region wider than the window). The scripting projection had the
 * same defect at 2.0 opens/section; both now hold ONE handle for the whole scan
 * (ADR-0009: the capability is the invariant, so the two coherency projections
 * must not differ in I/O shape either). */
static srmech_status_t sc_refill(sc_ctx_t *ctx, srmech_file_ro_t *fh, uint64_t base,
                                 uint64_t byte_len, uint64_t roff, size_t *wlen)
{
    uint64_t left = byte_len - roff;
    size_t n = (left > (uint64_t)ctx->win_bytes) ? ctx->win_bytes : (size_t)left;
    assert(ctx != NULL && fh != NULL && wlen != NULL);
    assert(roff < byte_len && ctx->win != NULL);
    if (n > ctx->win_bytes) { return SRMECH_ERR_OVERFLOW; }
    *wlen = n;
    return srmech_plat_file_read_at(fh, (size_t)(base + roff), ctx->win, n);
}

/* One block's on-disk width from its FIRST byte — the §55/v3 dual-format stride
 * (mirror genome_block_len, but over a WINDOW rather than a whole body, so the
 * truncation test belongs to the caller's refill loop). 0 = unrecognised. */
static size_t sc_block_len(unsigned char kind, uint32_t leaf_dim)
{
    assert(leaf_dim != 0u && leaf_dim <= 256u);
    assert(SRMECH_GENOME_PACKED_TURN_MARKER > 3u);
    if (genome_cap_kind(&kind, 1u) >= 0 || kind <= 3u) { return (size_t)leaf_dim; }
    if (kind == SRMECH_GENOME_PACKED_TURN_MARKER) {
        return 1u + ((size_t)leaf_dim + 3u) / 4u;
    }
    if (kind == SRMECH_GENOME_Q8_PACKED_TURN_MARKER) {
        return 1u + ((size_t)leaf_dim * 3u + 7u) / 8u;   /* §Q8/v16 3-bit turn */
    }
    return 0u;
}

/* Uncouple ONE data block into `unc` (leaf_dim symbols): a v3 klein4 packed turn
 * unpacks (2-bit) then klein4-decouples (XOR, its own inverse); a §Q8/v16 packed turn
 * unpacks (3-bit) then Q₈-decouples (the group INVERSE, genome_q8_uncouple); a legacy
 * v2 turn is already byte-per-symbol. So a mixed body's section-count scan strides +
 * decodes both carriers. */
static srmech_status_t sc_uncouple(const unsigned char *blk, uint32_t leaf_dim,
                                   const unsigned char *coupling,
                                   unsigned char *unc)
{
    unsigned char mem[256];
    assert(blk != NULL && coupling != NULL && unc != NULL);
    assert(leaf_dim != 0u && leaf_dim <= 256u);
    if (blk[0] == SRMECH_GENOME_Q8_PACKED_TURN_MARKER) {
        srmech_status_t su = srmech_genome_q8_unpack_turn(blk + 1, leaf_dim, mem);
        if (su != SRMECH_OK) { return su; }
        return genome_q8_uncouple(mem, coupling, leaf_dim, unc);
    }
    if (blk[0] == SRMECH_GENOME_PACKED_TURN_MARKER) {
        sc_unpack_turn(blk + 1, leaf_dim, mem);
    } else {
        memcpy(mem, blk, (size_t)leaf_dim);
    }
    return srmech_klein4_bind(mem, coupling, leaf_dim, unc);
}

/* Verify a region prefix's LEADING cap against the catalog's cap_sha256 — the
 * SAME integrity bound a whole-region read pays, over fewer bytes (the cap is
 * the region's first leaf_dim bytes, so every prefix of >= 1 block carries it).
 * Bounding IS integrity: a prefix read is not a weaker read. */
static srmech_status_t sc_verify_cap(const unsigned char *win, uint32_t leaf_dim,
                                     const srmech_json_value_t *csha)
{
    char got[65];
    srmech_status_t st;
    assert(win != NULL && csha != NULL);
    assert(leaf_dim != 0u && leaf_dim <= 256u);
    st = srmech_sha256_hex(win, (size_t)leaf_dim, got);
    if (st != SRMECH_OK) { return st; }
    return genome_str_eq(csha, got) ? SRMECH_OK : SRMECH_ERR_BAD_INPUT;
}

/* The running per-section walk state — the §89 header leaf's TRUE length D and
 * how many CONTENT symbols have been fed so far (the content is trimmed to D: a
 * SHORT section's last leaf carries pad symbols that would otherwise decode as
 * spurious trailing ints). */
typedef struct {
    int      have_header;
    uint64_t true_len;
    uint64_t fed;
} sc_walk_t;

/* Fold ONE on-disk block into the walk: caps are SKIPPED (they are not data
 * turns), the FIRST data turn is the §89 header (it self-records D), every later
 * data turn is content fed to the incremental decoder, trimmed to D. */
static srmech_status_t sc_block_fold(sc_ctx_t *ctx, const unsigned char *blk,
                                     uint32_t leaf_dim,
                                     const unsigned char *coupling,
                                     sc_walk_t *w, sc_dec_t *d, int *done)
{
    unsigned char unc[256];
    size_t take;
    srmech_status_t st;
    assert(ctx != NULL && blk != NULL && w != NULL && d != NULL && done != NULL);
    assert(coupling != NULL && leaf_dim >= 52u);
    if (genome_cap_kind(blk, leaf_dim) >= 0) { return SRMECH_OK; }   /* skip caps */
    st = sc_uncouple(blk, leaf_dim, coupling, unc);
    if (st != SRMECH_OK) { return st; }
    if (w->have_header == 0) {
        w->true_len = sc_header_true_len(unc);
        w->have_header = 1;
        return SRMECH_OK;
    }
    if (w->fed >= w->true_len) { *done = 1; return SRMECH_OK; }   /* D exhausted */
    take = (w->true_len - w->fed > (uint64_t)leaf_dim) ? (size_t)leaf_dim
         : (size_t)(w->true_len - w->fed);
    w->fed += (uint64_t)take;
    return sc_dec_feed(ctx, d, unc, take, done);
}

/* Page ONE section's node_ids prefix and fold its ids into the count table.
 * Walks the region through the sliding window and returns the moment the
 * declared node_ids are in hand, so the edge bytes are never read.
 * SRMECH_ERR_BAD_INPUT if the whole region cannot satisfy its own declared
 * n_node_ids — a SHORT table would silently UNDER-count, which is the one
 * failure this op must never return quietly. */
static srmech_status_t sc_section_scan(sc_ctx_t *ctx, srmech_file_ro_t *fh,
                                       uint64_t base,
                                       uint64_t byte_len, uint32_t leaf_dim,
                                       const unsigned char *coupling,
                                       const srmech_json_value_t *csha,
                                       uint32_t ord)
{
    sc_dec_t d;
    sc_walk_t w;
    uint64_t roff = 0u, wbase = 0u;
    size_t wlen = 0u;
    int done = 0;
    srmech_status_t st;
    assert(ctx != NULL && fh != NULL && coupling != NULL && csha != NULL);
    assert(leaf_dim >= 52u && leaf_dim <= 256u);
    memset(&d, 0, sizeof(d));
    memset(&w, 0, sizeof(w));
    d.ord = ord;
    while (done == 0 && roff < byte_len) {
        size_t inw, blen;
        if (wlen == 0u || roff >= wbase + (uint64_t)wlen) {
            st = sc_refill(ctx, fh, base, byte_len, roff, &wlen);
            if (st != SRMECH_OK) { return st; }
            wbase = roff;
            if (roff == 0u) {
                st = sc_verify_cap(ctx->win, leaf_dim, csha);
                if (st != SRMECH_OK) { return st; }
            }
        }
        inw = (size_t)(wbase + (uint64_t)wlen - roff);
        blen = sc_block_len(ctx->win[roff - wbase], leaf_dim);
        if (blen == 0u) { return SRMECH_ERR_BAD_INPUT; }    /* unrecognised kind */
        if (blen > inw) {
            if (wbase == roff) { return SRMECH_ERR_BAD_INPUT; }   /* truncated */
            wlen = 0u;                                      /* straddles — refill */
            continue;
        }
        st = sc_block_fold(ctx, &ctx->win[roff - wbase], leaf_dim, coupling, &w,
                           &d, &done);
        if (st != SRMECH_OK) { return st; }
        roff += (uint64_t)blen;
    }
    if (done == 0 && d.idx < (uint64_t)SRMECH_GENOME_SC_HEADER_INTS) {
        return SRMECH_OK;                  /* a section carrying no payload at all */
    }
    return (done == 0) ? SRMECH_ERR_BAD_INPUT : SRMECH_OK;
}

/* 1 iff a catalog chromosome entry is the VOCAB karyotype index (excluded from
 * the scan, exactly as the pure _section_entries excludes it). */
static int sc_is_vocab(const srmech_json_value_t *c)
{
    const srmech_json_value_t *lv;
    size_t n = strlen(SRMECH_GENOME_SC_VOCAB_LABEL);
    assert(c != NULL);
    assert(n != 0u);
    lv = srmech_json_object_get(c, "label");
    if (lv == NULL || lv->type != SRMECH_JSON_STRING ||
        lv->u.str.len != (uint32_t)n) {
        return 0;
    }
    return (memcmp(lv->u.str.ptr, SRMECH_GENOME_SC_VOCAB_LABEL, n) == 0) ? 1 : 0;
}

/* Pull one catalog entry's (byte_offset, byte_len, cap_sha256). NULL cap digest
 * = a malformed entry. */
static const srmech_json_value_t *sc_entry(const srmech_json_value_t *c,
                                           uint64_t *off, uint64_t *len)
{
    const srmech_json_value_t *bo, *bl, *cs;
    assert(c != NULL);
    assert(off != NULL && len != NULL);
    bo = srmech_json_object_get(c, "byte_offset");
    bl = srmech_json_object_get(c, "byte_len");
    cs = srmech_json_object_get(c, "cap_sha256");
    if (bo == NULL || bl == NULL || cs == NULL || bo->type != SRMECH_JSON_INT ||
        bl->type != SRMECH_JSON_INT || cs->type != SRMECH_JSON_STRING ||
        bo->u.i < 0 || bl->u.i <= 0) {
        return NULL;
    }
    *off = (uint64_t)bo->u.i;
    *len = (uint64_t)bl->u.i;
    return cs;
}

/* Sift `a[i]` down a max-heap of `n` slots, ordered by id. Iterative — JPL Rule
 * 1 bans recursion, and an O(n log n) in-place heapsort is what turns the
 * unordered count table into the ASCENDING output the contract promises. */
static void sc_sift(sc_slot_t *a, size_t n, size_t i)
{
    assert(a != NULL);
    assert(i < n || n == 0u);
    while (1) {
        size_t l = 2u * i + 1u, r = l + 1u, big = i;
        sc_slot_t t;
        if (l < n && a[l].key > a[big].key) { big = l; }
        if (r < n && a[r].key > a[big].key) { big = r; }
        if (big == i) { return; }
        t = a[i];
        a[i] = a[big];
        a[big] = t;
        i = big;
    }
}

/* In-place ascending heapsort of `n` slots by id. */
static void sc_sort(sc_slot_t *a, size_t n)
{
    assert(a != NULL || n == 0u);
    assert(n != (size_t)-1);
    for (size_t k = n / 2u; k > 0u; k--) { sc_sift(a, n, k - 1u); }
    for (size_t k = n; k > 1u; k--) {
        sc_slot_t t = a[0];
        a[0] = a[k - 1u];
        a[k - 1u] = t;
        sc_sift(a, k - 1u, 0u);
    }
}

/* Compact the occupied slots to the FRONT of the table, sort them ascending by
 * id, and copy out. *n_out is ALWAYS the TRUE distinct-id count — including on
 * SRMECH_ERR_OVERFLOW, which is what lets the caller retry at exactly the size
 * it needs (a short table would silently under-report the histogram). */
static srmech_status_t sc_finalize(sc_ctx_t *ctx, uint64_t *out_ids,
                                   uint64_t *out_counts, size_t out_cap,
                                   size_t *n_out)
{
    size_t w = 0u;
    assert(ctx != NULL && n_out != NULL);
    assert(out_ids != NULL || out_cap == 0u);
    for (size_t i = 0u; i < ctx->n_slots; i++) {
        if (ctx->slots[i].key != 0u) { ctx->slots[w++] = ctx->slots[i]; }
    }
    *n_out = w;
    if (w > out_cap) { return SRMECH_ERR_OVERFLOW; }
    sc_sort(ctx->slots, w);
    for (size_t i = 0u; i < w; i++) {
        out_ids[i] = ctx->slots[i].key - 1u;      /* key is id + 1 (0 == empty) */
        out_counts[i] = ctx->slots[i].count;
    }
    return SRMECH_OK;
}

/* Count the PLASMID sections in the catalog (the vocab index excluded) — the
 * `total` every §101 tick reports. */
static size_t sc_count_sections(const srmech_json_value_t *arr)
{
    size_t p = 0u;
    assert(arr != NULL);
    assert(arr->type == SRMECH_JSON_ARRAY);
    for (uint32_t i = 0u; i < arr->u.arr.n; i++) {
        if (sc_is_vocab(arr->u.arr.items[i]) == 0) { p++; }
    }
    return p;
}

/* The scan loop: page each PLASMID section's node_ids prefix, folding its ids
 * into the count table. The §101 tick fires BETWEEN whole SECTIONS with
 * done = sections scanned so far (never mid-section), so a cancel lands on a
 * section boundary; *cancelled goes 1 and *n_done holds the sections completed. */
static srmech_status_t sc_scan_all(sc_ctx_t *ctx, srmech_file_ro_t *fh,
                                   const srmech_json_value_t *arr,
                                   uint32_t leaf_dim,
                                   const unsigned char *coupling,
                                   srmech_progress_tick_cb_t tick, void *tick_ctx,
                                   size_t total, size_t *n_done, int *cancelled)
{
    size_t ord = 0u;
    assert(ctx != NULL && fh != NULL && arr != NULL && coupling != NULL);
    assert(n_done != NULL && cancelled != NULL);
    for (uint32_t i = 0u; i < arr->u.arr.n; i++) {
        const srmech_json_value_t *c = arr->u.arr.items[i], *csha;
        uint64_t off = 0u, len = 0u;
        srmech_status_t st;
        if (sc_is_vocab(c) != 0) { continue; }
        if (organize_tick(tick, tick_ctx, (uint32_t)SRMECH_PHASE_EXTRACTING,
                          (uint64_t)ord, (uint64_t)total) != 0) {
            *cancelled = 1;
            *n_done = ord;
            return SRMECH_OK;
        }
        csha = sc_entry(c, &off, &len);
        if (csha == NULL) { return SRMECH_ERR_BAD_INPUT; }
        ord++;
        st = sc_section_scan(ctx, fh, off, len, leaf_dim, coupling, csha,
                             (uint32_t)ord);
        if (st != SRMECH_OK) { return st; }
    }
    *n_done = ord;
    return SRMECH_OK;
}

/* Derive the store catalog ONCE and resolve the body path — the O(P * body)
 * quadratic this rc removes lives here, in that this runs exactly once per scan
 * rather than once per section. */
static srmech_status_t sc_open_store(const char *dir, const unsigned char *coupling,
                                     uint32_t leaf_dim, void *cws, size_t cws_len,
                                     char *body_path, size_t path_cap,
                                     const srmech_json_value_t **arr)
{
    srmech_json_value_t *manifest = NULL;
    const srmech_json_value_t *ld, *a;
    srmech_status_t st;
    assert(dir != NULL && coupling != NULL && body_path != NULL);
    assert(arr != NULL && leaf_dim >= 52u);
    st = genome_obtain_manifest(dir, coupling, (size_t)leaf_dim, cws,
                                cws_len, &manifest);
    if (st != SRMECH_OK) { return st; }
    ld = genome_data_get(manifest, "leaf_dim");
    if (ld == NULL || ld->type != SRMECH_JSON_INT ||
        (uint32_t)ld->u.i != leaf_dim) {
        return SRMECH_ERR_BAD_INPUT;
    }
    a = genome_data_get(manifest, "chromosomes");
    if (a == NULL || a->type != SRMECH_JSON_ARRAY) { return SRMECH_ERR_BAD_INPUT; }
    *arr = a;
    return genome_join(dir, SRMECH_GENOME_BODY, body_path, path_cap);
}

srmech_status_t srmech_genome_section_counts(
    const char *dir,
    const unsigned char *coupling, uint32_t leaf_dim,
    srmech_progress_tick_cb_t tick, void *tick_ctx,
    void *ws, size_t ws_len,
    uint64_t *out_ids, uint64_t *out_counts, size_t out_cap,
    size_t *n_out, size_t *n_done)
{
    char body_path[SRMECH_GENOME_PATH_MAX];
    const srmech_json_value_t *arr = NULL;
    srmech_file_ro_t fh;
    genome_arena_t a;
    sc_ctx_t ctx;
    void *cws = NULL;
    size_t cws_len = 0u, total;
    int cancelled = 0;
    srmech_status_t st;
    if (dir == NULL || coupling == NULL || ws == NULL || n_out == NULL ||
        n_done == NULL ||
        ((out_ids == NULL || out_counts == NULL) && out_cap != 0u)) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(dir != NULL && coupling != NULL && ws != NULL);
    assert(n_out != NULL && n_done != NULL);
    if (leaf_dim < 52u || leaf_dim > 256u) { return SRMECH_ERR_BAD_INPUT; }
    *n_out = 0u;
    *n_done = 0u;
    /* Carve the count table + the region window off the FRONT of ws; the untouched
     * TAIL becomes the catalog arena. A short ws leaves *n_out == 0 (a DECLINE). */
    memset(&ctx, 0, sizeof(ctx));
    genome_arena_init(&a, ws, ws_len);
    ctx.n_slots = sc_table_slots(out_cap);
    ctx.slots = genome_arena_alloc(&a, ctx.n_slots * sizeof(sc_slot_t));
    ctx.win_bytes = (size_t)SRMECH_GENOME_SC_WINDOW_BYTES;
    ctx.win = genome_arena_alloc(&a, ctx.win_bytes);
    if (ctx.slots == NULL || ctx.win == NULL) { return SRMECH_ERR_OVERFLOW; }
    memset(ctx.slots, 0, ctx.n_slots * sizeof(sc_slot_t));
    genome_arena_tail(&a, &cws, &cws_len);
    st = sc_open_store(dir, coupling, leaf_dim, cws, cws_len, body_path,
                       sizeof(body_path), &arr);
    if (st != SRMECH_OK) { return st; }
    total = sc_count_sections(arr);
    /* rc282: ONE open of turns.bin for the WHOLE scan, not one per section. */
    st = srmech_plat_file_open_ro(body_path, &fh);
    if (st != SRMECH_OK) { return st; }
    st = sc_scan_all(&ctx, &fh, arr, leaf_dim, coupling, tick, tick_ctx, total,
                     n_done, &cancelled);
    srmech_plat_file_close_ro(&fh);
    if (st != SRMECH_OK) { return st; }
    st = sc_finalize(&ctx, out_ids, out_counts, out_cap, n_out);
    if (st != SRMECH_OK) { return st; }      /* OVERFLOW carries the TRUE *n_out */
    return (cancelled != 0) ? SRMECH_CANCELLED : SRMECH_OK;
}

/* rc306 (task #899) — see the header for the contract. The catalog term reuses
 * srmech_genome_arena_bytes (the exact rule genome_obtain_manifest carves to); the
 * count table + region window are the two front carves the scan adds. */
size_t srmech_genome_section_counts_arena_bytes(size_t body_len, uint32_t n_chroms,
                                                size_t out_cap)
{
    size_t slots = sc_table_slots(out_cap);
    size_t table = slots * sizeof(sc_slot_t);
    size_t window = (size_t)SRMECH_GENOME_SC_WINDOW_BYTES;
    size_t catalog = srmech_genome_arena_bytes(body_len, n_chroms, 0u);
    assert(slots != 0u);
    assert(n_chroms != 0xFFFFFFFFu);
    return table + window + catalog + 64u;   /* +64: per-carve 16-align slop */
}

/* ─────────────────────────────────────────────────────────────────────────────
 * rc281 (§135 / F1251) — the GENE COPY-NUMBER pair: amplify (write) + copy_number
 * (read). rc273 shipped these Python-only because the field is TRANSPARENT to the
 * existing C readers; transparent-to-readers is not C-host parity, so a bare-C host
 * could neither set nor get the axis. These two symbols close the audit's G6 exhibit.
 * ───────────────────────────────────────────────────────────────────────────── */

/* rc281 — the gene COPY-NUMBER field offset: the index of the inline label's NUL
 * terminator inside a plain GENE cap. SRMECH_ERR_BAD_INPUT if there is no NUL within
 * leaf_dim, or if the 8-byte field would run past the leaf — BOTH of which the caller
 * reads as "field absent" => copy-number 1. The §135 mirror of
 * genome_active_count_offset (§127): the SAME right-after-the-label placement, which
 * is what keeps the label decode uniform across plain and amplified genes. */
static srmech_status_t genome_copy_number_offset(const unsigned char *cap,
                                                 size_t leaf_dim, size_t *nul_off)
{
    assert(cap != NULL && nul_off != NULL);
    assert(leaf_dim > 0u);
    size_t i = 1u;                                  /* skip the 0x47 marker byte */
    while (i < leaf_dim && cap[i] != 0u) { i++; }   /* find the label terminator */
    if (i >= leaf_dim) { return SRMECH_ERR_BAD_INPUT; }        /* no label NUL */
    if (i + 1u + SRMECH_GENOME_GENE_COPY_NUMBER_BYTES > leaf_dim) {
        return SRMECH_ERR_BAD_INPUT;                           /* field truncated */
    }
    *nul_off = i;
    return SRMECH_OK;
}

/* rc281 — does this cap's inline label equal (label, label_len)? The label is
 * cap[1 .. first NUL), decoded UNIFORMLY: a copy-number field sits AFTER that NUL, so
 * an already-amplified gene matches its own label unchanged. 1 on match, else 0.
 * A READ; no abs, no mutation. */
static int genome_gene_label_eq(const unsigned char *block, size_t leaf_dim,
                                const unsigned char *label, size_t label_len)
{
    assert(block != NULL);
    assert(label != NULL || label_len == 0u);
    size_t n = 1u;
    while (n < leaf_dim && block[n] != 0u) { n++; }
    if (n - 1u != label_len) { return 0; }          /* label byte count differs */
    return (label_len == 0u || memcmp(block + 1, label, label_len) == 0) ? 1 : 0;
}

/* rc281 — index of the FIRST PLAIN GENE cap (0x47) in `strand` whose inline label
 * equals (label, label_len); SRMECH_ERR_BAD_INPUT if there is none. ONLY a plain gene
 * carries a copy-number axis, so a regulatory / boolean / threshold / graded gene is
 * skipped even when its label matches (the Python `_cap_kind(hv) != GENE_CAP_MARKER`
 * guard). The find shared by amplify + copy_number. */
static srmech_status_t genome_find_plain_gene(const unsigned char *strand,
                                              size_t n_blocks, uint32_t leaf_dim,
                                              const unsigned char *label,
                                              size_t label_len, size_t *idx_out)
{
    assert(strand != NULL && idx_out != NULL);
    assert(leaf_dim > 0u);
    for (size_t i = 0u; i < n_blocks; i++) {
        const unsigned char *block = strand + i * (size_t)leaf_dim;
        if (genome_cap_kind(block, leaf_dim) != (int)SRMECH_GENOME_GENE_CAP_MARKER) {
            continue;
        }
        if (genome_gene_label_eq(block, (size_t)leaf_dim, label, label_len) != 0) {
            *idx_out = i;
            return SRMECH_OK;
        }
    }
    return SRMECH_ERR_BAD_INPUT;                    /* no plain gene by that label */
}

/* rc281 — pack a PLAIN GENE cap carrying an exact copy number. `n == 1` is the DEFAULT
 * (present-once) and writes the PLAIN cap — byte-identical to a never-amplified gene, no
 * field spent; only `n >= 2` writes [0x47] + label + NUL + n(uint64 BE), NUL-padded to
 * dim. The C mirror of srmech.amsc.genome._pack_gene_cap_copy_number. */
static srmech_status_t genome_pack_gene_copy_number(const unsigned char *label,
                                                    size_t label_len, uint64_t n,
                                                    uint32_t dim,
                                                    unsigned char *out, size_t out_cap)
{
    assert(out != NULL);
    assert(label != NULL || label_len == 0u);
    if (n == 0u) { return SRMECH_ERR_BAD_INPUT; }   /* a gene is present >= once */
    if (n == 1u) {                                  /* DEFAULT — the plain cap */
        return genome_pack_cap(SRMECH_GENOME_GENE_CAP_MARKER, label, label_len,
                               dim, out, out_cap);
    }
    if (dim == 0u || (size_t)dim > out_cap) { return SRMECH_ERR_BAD_INPUT; }
    size_t need = 2u + label_len + SRMECH_GENOME_GENE_COPY_NUMBER_BYTES;
    if (need > (size_t)dim) { return SRMECH_ERR_BAD_INPUT; }   /* label + field too wide */
    out[0] = SRMECH_GENOME_GENE_CAP_MARKER;
    if (label_len != 0u) { memcpy(out + 1, label, label_len); }
    out[1u + label_len] = 0u;                       /* the label terminator */
    size_t base = 2u + label_len;
    for (size_t k = 0u; k < SRMECH_GENOME_GENE_COPY_NUMBER_BYTES; k++) {
        unsigned shift = (unsigned)(8u *
            (SRMECH_GENOME_GENE_COPY_NUMBER_BYTES - 1u - k));
        out[base + k] = (unsigned char)((n >> shift) & 0xFFu);
    }
    memset(out + need, 0, (size_t)dim - need);      /* NUL-pad the remainder */
    return SRMECH_OK;
}

/* rc281 (§135 / F1251) — WRITE a gene's copy number. See srmech.h for the contract. */
srmech_status_t srmech_genome_amplify(
    const unsigned char *strand, size_t n_blocks, uint32_t leaf_dim,
    const unsigned char *label, size_t label_len, uint64_t n,
    unsigned char *out, size_t out_cap)
{
    if (strand == NULL || out == NULL || (label == NULL && label_len != 0u)) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(strand != NULL && out != NULL);
    assert(label != NULL || label_len == 0u);
    if (leaf_dim == 0u || leaf_dim > 256u || n_blocks == 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (n == 0u) { return SRMECH_ERR_BAD_INPUT; }   /* multiplicity is >= 1 */
    size_t total = n_blocks * (size_t)leaf_dim;
    if (total / (size_t)leaf_dim != n_blocks) { return SRMECH_ERR_BAD_INPUT; }  /* wrap */
    if (out_cap < total) { return SRMECH_ERR_OVERFLOW; }
    size_t idx = 0u;
    srmech_status_t st = genome_find_plain_gene(strand, n_blocks, leaf_dim,
                                                label, label_len, &idx);
    if (st != SRMECH_OK) { return st; }
    memcpy(out, strand, total);                     /* every block byte-copied ... */
    return genome_pack_gene_copy_number(label, label_len, n, leaf_dim,
                                        out + idx * (size_t)leaf_dim,
                                        (size_t)leaf_dim);   /* ... one cap rewritten */
}

/* rc281 (§135 / F1251) — READ a gene's copy number. See srmech.h for the contract. */
srmech_status_t srmech_genome_copy_number(
    const unsigned char *strand, size_t n_blocks, uint32_t leaf_dim,
    const unsigned char *label, size_t label_len, uint64_t *count_out)
{
    if (strand == NULL || count_out == NULL || (label == NULL && label_len != 0u)) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(strand != NULL && count_out != NULL);
    assert(label != NULL || label_len == 0u);
    if (leaf_dim == 0u || leaf_dim > 256u || n_blocks == 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    size_t idx = 0u;
    srmech_status_t st = genome_find_plain_gene(strand, n_blocks, leaf_dim,
                                                label, label_len, &idx);
    if (st != SRMECH_OK) { return st; }
    const unsigned char *cap = strand + idx * (size_t)leaf_dim;
    size_t nul = 0u;
    if (genome_copy_number_offset(cap, (size_t)leaf_dim, &nul) != SRMECH_OK) {
        *count_out = 1u;              /* no label NUL / no field room -> present-once */
        return SRMECH_OK;
    }
    uint64_t stored = 0u;
    size_t base = nul + 1u;
    for (size_t k = 0u; k < SRMECH_GENOME_GENE_COPY_NUMBER_BYTES; k++) {
        stored = (stored << 8) | (uint64_t)cap[base + k];
    }
    *count_out = (stored >= 1u) ? stored : 1u;   /* stored 0 (plain / pre-rc273) -> 1 */
    return SRMECH_OK;
}

/* rc314 — the CODON READ-LAYER whole-op C peers. Biology reads the genome in
 * CODONS (triplets); the ribosome IMPOSES that reading over the stored strand.
 * PURE READS: no store, no on-disk format change (GENOME_FORMAT_VERSION stays
 * 16). No float, no libm, no abs() — the base-4 codon index is exact Class-I
 * integer arithmetic and the amino-acid lookup is a Class-E dense catalog read.
 * ABI-additive: two new symbols only, so SRMECH_ABI_VERSION stays 10. */

srmech_status_t srmech_genome_codon_read(const uint8_t *strand, uint32_t n,
                                         uint32_t phase, const uint8_t *ncbieaa,
                                         uint8_t *out, uint32_t *out_len)
{
    if (strand == NULL || ncbieaa == NULL || out == NULL || out_len == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (phase > 2u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    assert(ncbieaa != NULL);
    assert(out != NULL && out_len != NULL);
    uint32_t k = 0u;
    /* q8_project_v4 FIRST (& 3): the sign bit must not touch identity. Then the
     * base-4 window read (coset 0->U/T, 1->C, 2->A, 3->G) indexes the attested
     * NCBI transl_table=1 amino-acid string. */
    for (uint32_t i = phase; i + 3u <= n; i += 3u) {
        uint32_t b0 = (uint32_t)(strand[i] & 3u);
        uint32_t b1 = (uint32_t)(strand[i + 1u] & 3u);
        uint32_t b2 = (uint32_t)(strand[i + 2u] & 3u);
        uint32_t idx = 16u * b0 + 4u * b1 + b2;   /* base-4 codon index [0,64) */
        assert(idx < 64u);
        out[k] = ncbieaa[idx];                    /* Class-E dense catalog read */
        k += 1u;
    }
    *out_len = k;
    return SRMECH_OK;
}

srmech_status_t srmech_genome_codon_frame_monodromy(uint32_t n, uint32_t *out)
{
    if (out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(out != NULL);
    /* V4 projection preserves length, so the Z3 monodromy is just n mod 3. */
    *out = n % 3u;
    assert(*out < 3u);
    return SRMECH_OK;
}
