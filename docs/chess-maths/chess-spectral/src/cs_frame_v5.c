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


/* ----- Per-channel (mode 1) full-file I/O --------------------- *
 *
 * The dense-equivalent input/output buffer layout is:
 *   per ply: encoding_bytes (encoding_dim * 4) + move_tail_bytes
 *   total: n_plies * frame_bytes
 *
 * The wire layout per ply (variable size) is:
 *   u32 body_size            // bytes following body_size itself
 *   u8  flags                // bit 0 = PC_FLAG_FULL
 *   u8  n_channels_present
 *   [u8 channel_idx, u8 reserved, float32 buffer[channel_dim]]
 *       * n_channels_present
 *   <move-metadata tail>
 *
 * body_size = 1(flags) + 1(n_chan) + n_chan*(2 + channel_dim*4) +
 *             move_tail_bytes
 *
 * Channel comparison is bit-exact via memcmp on the float32 byte
 * representation; this preserves NaN bit patterns (cf. the comment in
 * frame_v5.py). The first frame is always written as a FULL block.
 */

/* Compare two channel buffers byte-exact. Returns 1 if equal, 0 if
 * different. Bytes are float32; memcmp on the raw bytes is the
 * uint32-view bit-exact comparison Python's _channels_diff does. */
static int _v5_pc_channels_equal(const uint8_t *a, const uint8_t *b,
                                  uint32_t channel_bytes) {
    return memcmp(a, b, channel_bytes) == 0;
}

static int _v5_pc_write_frame(FILE *fp,
                               const uint8_t *curr_frame,
                               const uint8_t *prev_frame_or_NULL,
                               uint32_t n_channels,
                               uint32_t channel_dim,
                               uint32_t move_tail_bytes) {
    uint32_t channel_bytes = channel_dim * 4u;
    uint32_t enc_bytes = n_channels * channel_bytes;

    /* First, decide which channels to emit. */
    uint8_t flags;
    uint8_t channel_present[CS_V5_N_CHANNELS_4D];   /* 11 fits 2D and 4D */
    uint32_t n_present = 0u;
    if (prev_frame_or_NULL == NULL) {
        flags = CS_V5_PC_FLAG_FULL;
        for (uint32_t i = 0; i < n_channels; ++i) channel_present[i] = 1u;
        n_present = n_channels;
    } else {
        flags = 0u;
        for (uint32_t i = 0; i < n_channels; ++i) {
            const uint8_t *cc = curr_frame + i * channel_bytes;
            const uint8_t *pc = prev_frame_or_NULL + i * channel_bytes;
            if (_v5_pc_channels_equal(cc, pc, channel_bytes)) {
                channel_present[i] = 0u;
            } else {
                channel_present[i] = 1u;
                n_present++;
            }
        }
    }

    /* body_size = flags(1) + n_chan(1) + present*(2 + channel_bytes) +
     *             move_tail_bytes */
    uint32_t body_size = 1u + 1u
                       + n_present * (CS_V5_PC_BLOCK_PREFIX + channel_bytes)
                       + move_tail_bytes;

    /* Write [u32 body_size][u8 flags][u8 n_chan]. */
    uint8_t hdr[CS_V5_PC_HEADER_SIZE];
    _put_u32_le(hdr + 0, body_size);
    hdr[4] = flags;
    hdr[5] = (uint8_t)(n_present & 0xFFu);
    if (fwrite(hdr, 1, CS_V5_PC_HEADER_SIZE, fp) != CS_V5_PC_HEADER_SIZE) {
        return -7;
    }

    /* Per-channel blocks: u8 idx + u8 reserved + float32 buffer. */
    for (uint32_t i = 0; i < n_channels; ++i) {
        if (!channel_present[i]) continue;
        uint8_t prefix[CS_V5_PC_BLOCK_PREFIX];
        prefix[0] = (uint8_t)(i & 0xFFu);
        prefix[1] = 0u;  /* reserved */
        if (fwrite(prefix, 1, CS_V5_PC_BLOCK_PREFIX, fp) != CS_V5_PC_BLOCK_PREFIX) {
            return -7;
        }
        const uint8_t *cc = curr_frame + i * channel_bytes;
        if (fwrite(cc, 1, channel_bytes, fp) != channel_bytes) {
            return -7;
        }
    }

    /* Move tail: bytes immediately after the encoding portion of the
     * dense frame layout. */
    const uint8_t *tail = curr_frame + enc_bytes;
    if (fwrite(tail, 1, move_tail_bytes, fp) != move_tail_bytes) {
        return -7;
    }

    return 0;
}

static int _v5_write_per_channel_file(FILE *fp,
                                       uint32_t n_dimensions,
                                       uint32_t encoding_dim,
                                       uint32_t frame_bytes,
                                       uint32_t n_channels,
                                       uint32_t channel_dim,
                                       uint32_t move_tail_bytes,
                                       const void *dense_encodings,
                                       uint32_t n_plies) {
    if (fp == NULL || (dense_encodings == NULL && n_plies > 0)) return -1;

    cs_v5_header_t hdr = {
        .magic          = CS_V5_MAGIC,
        .version        = CS_V5_VERSION,
        .encoding_dim   = encoding_dim,
        .frame_bytes    = frame_bytes,
        .n_plies        = n_plies,
        .board_dim_side = CS_V5_BOARD_SIDE,
        .n_dimensions   = n_dimensions,
        .encoding_mode  = CS_V5_MODE_PER_CHANNEL,
    };
    int rc = cs_v5_header_write(fp, &hdr);
    if (rc != 0) return rc;

    const uint8_t *base = (const uint8_t *)dense_encodings;
    for (uint32_t i = 0; i < n_plies; ++i) {
        const uint8_t *curr = base + (size_t)i * (size_t)frame_bytes;
        const uint8_t *prev = (i == 0) ? NULL
                              : base + (size_t)(i - 1u) * (size_t)frame_bytes;
        rc = _v5_pc_write_frame(fp, curr, prev,
                                 n_channels, channel_dim, move_tail_bytes);
        if (rc != 0) return rc;
    }
    return 0;
}

int cs_v5_write_per_channel_2d_file(FILE *fp,
                                     const void *dense_encodings,
                                     uint32_t n_plies) {
    return _v5_write_per_channel_file(
        fp, /*n_dimensions=*/2u,
        CS_V5_ENCODING_DIM_2D, CS_V5_FRAME_BYTES_2D,
        CS_V5_N_CHANNELS_2D, CS_V5_CHANNEL_DIM_2D, CS_V5_MOVE_TAIL_2D,
        dense_encodings, n_plies);
}

int cs_v5_write_per_channel_4d_file(FILE *fp,
                                     const void *dense_encodings,
                                     uint32_t n_plies) {
    return _v5_write_per_channel_file(
        fp, /*n_dimensions=*/4u,
        CS_V5_ENCODING_DIM_4D, CS_V5_FRAME_BYTES_4D,
        CS_V5_N_CHANNELS_4D, CS_V5_CHANNEL_DIM_4D, CS_V5_MOVE_TAIL_4D,
        dense_encodings, n_plies);
}

static int _v5_pc_read_frame(FILE *fp,
                              const uint8_t *prev_full_enc_or_NULL,
                              uint8_t *out_full_enc,
                              uint8_t *out_move_tail,
                              uint32_t n_channels,
                              uint32_t channel_dim,
                              uint32_t move_tail_bytes,
                              int *out_was_full) {
    /* Read the 6-byte body header. */
    uint8_t head[CS_V5_PC_HEADER_SIZE];
    if (fread(head, 1, CS_V5_PC_HEADER_SIZE, fp) != CS_V5_PC_HEADER_SIZE) {
        return -7;
    }
    uint32_t body_size = _get_u32_le(head + 0);
    uint8_t flags = head[4];
    uint8_t n_present = head[5];
    int is_full = (flags & CS_V5_PC_FLAG_FULL) != 0;
    if (out_was_full) *out_was_full = is_full;

    /* The remaining body bytes after [flags + n_chan]. */
    if (body_size < 2u) return -9;
    uint32_t remaining = body_size - 2u;

    /* Sanity-check the body geometry: must hold n_present blocks +
     * the move-metadata tail exactly. */
    uint32_t channel_bytes = channel_dim * 4u;
    uint32_t expect_blocks = (uint32_t)n_present
                              * (CS_V5_PC_BLOCK_PREFIX + channel_bytes);
    if (remaining != expect_blocks + move_tail_bytes) return -9;
    if (is_full && n_present != n_channels) return -9;
    if (!is_full && prev_full_enc_or_NULL == NULL) return -9;

    /* Seed the output: full → zeros, delta → copy of prev. */
    if (is_full) {
        memset(out_full_enc, 0, (size_t)n_channels * (size_t)channel_bytes);
    } else {
        memcpy(out_full_enc, prev_full_enc_or_NULL,
               (size_t)n_channels * (size_t)channel_bytes);
    }

    /* Read each present channel block in order and write into the
     * matching slot of out_full_enc. */
    for (uint32_t k = 0; k < n_present; ++k) {
        uint8_t prefix[CS_V5_PC_BLOCK_PREFIX];
        if (fread(prefix, 1, CS_V5_PC_BLOCK_PREFIX, fp)
            != CS_V5_PC_BLOCK_PREFIX) {
            return -7;
        }
        uint32_t idx = prefix[0];
        if (idx >= n_channels) return -9;
        uint8_t *slot = out_full_enc + idx * channel_bytes;
        if (fread(slot, 1, channel_bytes, fp) != channel_bytes) {
            return -7;
        }
    }

    /* Move tail. */
    if (fread(out_move_tail, 1, move_tail_bytes, fp) != move_tail_bytes) {
        return -7;
    }
    return 0;
}

static int _v5_read_per_channel_file(FILE *fp,
                                      cs_v5_header_t *hdr_out,
                                      void *dense_encodings_buf,
                                      uint32_t max_plies,
                                      uint32_t *n_plies_out,
                                      uint32_t expect_n_dim,
                                      uint32_t expect_encoding_dim,
                                      uint32_t frame_bytes,
                                      uint32_t n_channels,
                                      uint32_t channel_dim,
                                      uint32_t move_tail_bytes) {
    if (fp == NULL) return -1;
    cs_v5_header_t hdr;
    int rc = cs_v5_header_read(fp, &hdr);
    if (rc != 0) return rc;

    if (hdr.n_dimensions != expect_n_dim
        || hdr.encoding_dim != expect_encoding_dim
        || hdr.encoding_mode != CS_V5_MODE_PER_CHANNEL) {
        return -8;
    }
    if (hdr_out != NULL) *hdr_out = hdr;

    uint32_t n_to_read = hdr.n_plies < max_plies ? hdr.n_plies : max_plies;
    if (n_plies_out != NULL) *n_plies_out = n_to_read;
    if (n_to_read == 0u || dense_encodings_buf == NULL) {
        /* Caller asked for zero plies (or only wants the header) — done. */
        if (n_to_read == 0u) return 0;
        return -1;
    }

    /* Reconstruct n_to_read frames in place. The previous reconstructed
     * frame's encoding lives at base + (i-1)*frame_bytes, which has the
     * same n_channels*channel_bytes layout for the encoding portion. */
    uint8_t *base = (uint8_t *)dense_encodings_buf;
    uint32_t enc_bytes = n_channels * channel_dim * 4u;
    for (uint32_t i = 0; i < n_to_read; ++i) {
        uint8_t *curr = base + (size_t)i * (size_t)frame_bytes;
        const uint8_t *prev = (i == 0u) ? NULL
                              : base + (size_t)(i - 1u) * (size_t)frame_bytes;
        int was_full = 0;
        rc = _v5_pc_read_frame(fp, prev, curr, curr + enc_bytes,
                                n_channels, channel_dim, move_tail_bytes,
                                &was_full);
        if (rc != 0) return rc;
        if (i == 0u && !was_full) return -9;  /* first frame must be full */
    }
    return 0;
}

int cs_v5_read_per_channel_2d_file(FILE *fp,
                                    cs_v5_header_t *hdr_out,
                                    void *dense_encodings_buf,
                                    uint32_t max_plies,
                                    uint32_t *n_plies_out) {
    return _v5_read_per_channel_file(
        fp, hdr_out, dense_encodings_buf, max_plies, n_plies_out,
        /*expect_n_dim=*/2u, CS_V5_ENCODING_DIM_2D, CS_V5_FRAME_BYTES_2D,
        CS_V5_N_CHANNELS_2D, CS_V5_CHANNEL_DIM_2D, CS_V5_MOVE_TAIL_2D);
}

int cs_v5_read_per_channel_4d_file(FILE *fp,
                                    cs_v5_header_t *hdr_out,
                                    void *dense_encodings_buf,
                                    uint32_t max_plies,
                                    uint32_t *n_plies_out) {
    return _v5_read_per_channel_file(
        fp, hdr_out, dense_encodings_buf, max_plies, n_plies_out,
        /*expect_n_dim=*/4u, CS_V5_ENCODING_DIM_4D, CS_V5_FRAME_BYTES_4D,
        CS_V5_N_CHANNELS_4D, CS_V5_CHANNEL_DIM_4D, CS_V5_MOVE_TAIL_4D);
}
