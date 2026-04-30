/* cs_frame_v5.c — v5 unified wire format, C-side header reader/writer.
 *
 * v1.6.x Track 2 PR-1: header struct + peek + read + write. Frame-
 * body reader/writer ships in subsequent v1.6.x PRs.
 *
 * The byte layout is fully specified by python/chess_spectral/
 * frame_v5.py and docs/WIRE_FORMAT.md. This C side is the "from-
 * scratch" mirror that proves byte-for-byte compatibility (an
 * upcoming integration test will read a Python-written v5 header in
 * C and a C-written v5 header in Python, checking exact equality).
 *
 * All multi-byte fields are little-endian, the same convention used
 * by the existing v2 / v3 / v4 readers in cs_frame.c / cs_frame_4d.c.
 * On x86_64 (the only supported platform today) these are native
 * stores; the explicit byte-level pack/unpack here is for
 * portability + clarity rather than wire-format conversion.
 */
#include "cs_frame_v5.h"

#include <string.h>

/* ----- Helpers: little-endian byte-level read/write --------------- */

static void _put_u64_le(uint8_t *p, uint64_t v) {
    for (int i = 0; i < 8; ++i) p[i] = (uint8_t)((v >> (8 * i)) & 0xFFu);
}
static void _put_u32_le(uint8_t *p, uint32_t v) {
    for (int i = 0; i < 4; ++i) p[i] = (uint8_t)((v >> (8 * i)) & 0xFFu);
}
static uint64_t _get_u64_le(const uint8_t *p) {
    uint64_t v = 0;
    for (int i = 0; i < 8; ++i) v |= ((uint64_t)p[i]) << (8 * i);
    return v;
}
static uint32_t _get_u32_le(const uint8_t *p) {
    uint32_t v = 0;
    for (int i = 0; i < 4; ++i) v |= ((uint32_t)p[i]) << (8 * i);
    return v;
}

/* ----- Field-validation helper ----------------------------------- */

static int _validate_v5_fields(const cs_v5_header_t *hdr) {
    if (hdr == NULL) return -1;
    if (hdr->magic != CS_V5_MAGIC) return -2;
    if (hdr->version != CS_V5_VERSION) return -3;
    if (hdr->n_dimensions != 2u && hdr->n_dimensions != 4u) return -4;
    if (hdr->encoding_mode > CS_V5_MODE_XOR_STREAM) return -5;
    /* encoding_dim must match n_dimensions. */
    uint32_t expected_dim = (hdr->n_dimensions == 2u)
        ? CS_V5_ENCODING_DIM_2D : CS_V5_ENCODING_DIM_4D;
    if (hdr->encoding_dim != expected_dim) return -6;
    return 0;
}

/* ----- Public: pack / unpack ------------------------------------- */

int cs_v5_header_pack(const cs_v5_header_t *hdr, uint8_t out[CS_V5_HEADER_SIZE]) {
    if (hdr == NULL || out == NULL) return -1;
    int rc = _validate_v5_fields(hdr);
    if (rc != 0) return rc;

    /* Zero the entire 256-byte buffer first; the reserved[223] tail
     * stays zero, and any leakage from caller stack stays out of the
     * file. */
    memset(out, 0, CS_V5_HEADER_SIZE);

    _put_u64_le(out + 0,  hdr->magic);
    _put_u32_le(out + 8,  hdr->version);
    _put_u32_le(out + 12, hdr->encoding_dim);
    _put_u32_le(out + 16, hdr->frame_bytes);
    _put_u32_le(out + 20, hdr->n_plies);
    _put_u32_le(out + 24, hdr->board_dim_side);
    _put_u32_le(out + 28, hdr->n_dimensions);
    out[32] = hdr->encoding_mode;
    /* out[33..255] already zero from memset above. */
    return 0;
}

int cs_v5_header_unpack(const uint8_t in[CS_V5_HEADER_SIZE], cs_v5_header_t *hdr) {
    if (in == NULL || hdr == NULL) return -1;

    hdr->magic          = _get_u64_le(in + 0);
    hdr->version        = _get_u32_le(in + 8);
    hdr->encoding_dim   = _get_u32_le(in + 12);
    hdr->frame_bytes    = _get_u32_le(in + 16);
    hdr->n_plies        = _get_u32_le(in + 20);
    hdr->board_dim_side = _get_u32_le(in + 24);
    hdr->n_dimensions   = _get_u32_le(in + 28);
    hdr->encoding_mode  = in[32];

    return _validate_v5_fields(hdr);
}

/* ----- Public: peek / read / write ------------------------------- */

int cs_v5_peek_version(FILE *fp) {
    if (fp == NULL) return -1;
    long pos = ftell(fp);
    if (pos < 0) return -1;

    uint8_t head[12];
    size_t n = fread(head, 1, 12, fp);
    /* Restore position regardless of read outcome. */
    if (fseek(fp, pos, SEEK_SET) != 0) return -1;
    if (n != 12) return -1;

    uint64_t magic = _get_u64_le(head + 0);
    if (magic != CS_V5_MAGIC) return -2;
    uint32_t v = _get_u32_le(head + 8);
    return (int)v;
}

int cs_v5_header_read(FILE *fp, cs_v5_header_t *hdr) {
    if (fp == NULL || hdr == NULL) return -1;
    uint8_t buf[CS_V5_HEADER_SIZE];
    size_t n = fread(buf, 1, CS_V5_HEADER_SIZE, fp);
    if (n != CS_V5_HEADER_SIZE) return -7;
    return cs_v5_header_unpack(buf, hdr);
}

int cs_v5_header_write(FILE *fp, const cs_v5_header_t *hdr) {
    if (fp == NULL || hdr == NULL) return -1;
    uint8_t buf[CS_V5_HEADER_SIZE];
    int rc = cs_v5_header_pack(hdr, buf);
    if (rc != 0) return rc;
    size_t n = fwrite(buf, 1, CS_V5_HEADER_SIZE, fp);
    if (n != CS_V5_HEADER_SIZE) return -7;
    return 0;
}


/* ----- Dense-mode (mode 0) full-file I/O ----------------------- */

static int _v5_write_dense_file(FILE *fp,
                                 uint32_t n_dimensions,
                                 uint32_t encoding_dim,
                                 uint32_t frame_bytes,
                                 const void *frame_blob,
                                 uint32_t n_plies) {
    if (fp == NULL || (frame_blob == NULL && n_plies > 0)) return -1;

    cs_v5_header_t hdr = {
        .magic          = CS_V5_MAGIC,
        .version        = CS_V5_VERSION,
        .encoding_dim   = encoding_dim,
        .frame_bytes    = frame_bytes,
        .n_plies        = n_plies,
        .board_dim_side = CS_V5_BOARD_SIDE,
        .n_dimensions   = n_dimensions,
        .encoding_mode  = CS_V5_MODE_DENSE,
    };
    int rc = cs_v5_header_write(fp, &hdr);
    if (rc != 0) return rc;

    if (n_plies > 0) {
        size_t total = (size_t)frame_bytes * (size_t)n_plies;
        size_t w = fwrite(frame_blob, 1, total, fp);
        if (w != total) return -7;
    }
    return 0;
}

int cs_v5_write_dense_2d_file(FILE *fp,
                              const void *frame_bytes,
                              uint32_t n_plies) {
    return _v5_write_dense_file(
        fp, /*n_dimensions=*/2u,
        CS_V5_ENCODING_DIM_2D, CS_V5_FRAME_BYTES_2D,
        frame_bytes, n_plies);
}

int cs_v5_write_dense_4d_file(FILE *fp,
                              const void *frame_bytes,
                              uint32_t n_plies) {
    return _v5_write_dense_file(
        fp, /*n_dimensions=*/4u,
        CS_V5_ENCODING_DIM_4D, CS_V5_FRAME_BYTES_4D,
        frame_bytes, n_plies);
}

static int _v5_read_dense_file(FILE *fp,
                                cs_v5_header_t *hdr_out,
                                void *frame_buf,
                                uint32_t max_plies,
                                uint32_t *n_plies_out,
                                uint32_t expect_n_dim,
                                uint32_t expect_encoding_dim,
                                uint32_t frame_bytes) {
    if (fp == NULL) return -1;
    cs_v5_header_t hdr;
    int rc = cs_v5_header_read(fp, &hdr);
    if (rc != 0) return rc;

    if (hdr.n_dimensions != expect_n_dim
        || hdr.encoding_dim != expect_encoding_dim
        || hdr.encoding_mode != CS_V5_MODE_DENSE) {
        return -8;
    }
    if (hdr_out != NULL) *hdr_out = hdr;

    uint32_t n_to_read = hdr.n_plies < max_plies ? hdr.n_plies : max_plies;
    if (n_plies_out != NULL) *n_plies_out = n_to_read;

    if (n_to_read > 0 && frame_buf != NULL) {
        size_t total = (size_t)frame_bytes * (size_t)n_to_read;
        size_t r = fread(frame_buf, 1, total, fp);
        if (r != total) return -7;
    }
    return 0;
}

int cs_v5_read_dense_2d_file(FILE *fp,
                             cs_v5_header_t *hdr_out,
                             void *frame_buf,
                             uint32_t max_plies,
                             uint32_t *n_plies_out) {
    return _v5_read_dense_file(
        fp, hdr_out, frame_buf, max_plies, n_plies_out,
        /*expect_n_dim=*/2u,
        CS_V5_ENCODING_DIM_2D, CS_V5_FRAME_BYTES_2D);
}

int cs_v5_read_dense_4d_file(FILE *fp,
                             cs_v5_header_t *hdr_out,
                             void *frame_buf,
                             uint32_t max_plies,
                             uint32_t *n_plies_out) {
    return _v5_read_dense_file(
        fp, hdr_out, frame_buf, max_plies, n_plies_out,
        /*expect_n_dim=*/4u,
        CS_V5_ENCODING_DIM_4D, CS_V5_FRAME_BYTES_4D);
}
