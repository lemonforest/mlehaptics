#ifndef CS_FRAME_V5_H
#define CS_FRAME_V5_H

/* v5 unified .spectral[z] / .spectralz4 wire format.
 *
 * Mirrors python/chess_spectral/frame_v5.py's layout exactly. v5
 * supersedes v2 (2D, encoding_dim=640) and v3/v4 (4D, encoding_dim=
 * 40960/45056) for new writes; legacy v2/v3/v4 readers in cs_frame.h
 * / cs_frame_4d.h continue to work unchanged so files already on disk
 * keep loading.
 *
 * Header (256 bytes total, little-endian):
 *
 *     char     magic[8];       // "LARTPSEC" (unchanged from v2/v4)
 *     uint32_t version;        // 5
 *     uint32_t encoding_dim;   // 640 (2D) | 45056 (4D)
 *     uint32_t frame_bytes;    // dense-equivalent frame body size
 *     uint32_t n_plies;
 *     uint32_t board_dim_side; // 8 (always)
 *     uint32_t n_dimensions;   // 2 or 4
 *     uint8_t  encoding_mode;  // 0=dense, 1=per-channel, 2=XOR-stream
 *     uint8_t  reserved[223];  // zero-filled
 *
 * Total = 8 + 6*4 + 1 + 223 = 256 B
 *
 * Reference: docs/adr/wire_format/ADR-001-v5-unified-encoding-modes.md
 *            docs/WIRE_FORMAT.md (user-facing spec)
 */

#include <stdio.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif


#define CS_V5_MAGIC          0x434553505452414CULL /* "LARTPSEC" reversed endian */
#define CS_V5_VERSION        5u
#define CS_V5_HEADER_SIZE    256
#define CS_V5_BOARD_SIDE     8u

/* Encoding modes (header byte at offset 32). */
#define CS_V5_MODE_DENSE          0u  /* current v2/v4 frame body */
#define CS_V5_MODE_PER_CHANNEL    1u  /* variable-size frames; only changed channels */
#define CS_V5_MODE_XOR_STREAM     2u  /* frame_N = stored[N] XOR frame_{N-1} */

/* Per-dimension dense encoding sizes (parity with frame_v5.py). */
#define CS_V5_ENCODING_DIM_2D     640u
#define CS_V5_ENCODING_DIM_4D     45056u
#define CS_V5_FRAME_BYTES_2D      (CS_V5_ENCODING_DIM_2D * 4u + 8u)   /* 2568 */
#define CS_V5_FRAME_BYTES_4D      (CS_V5_ENCODING_DIM_4D * 4u + 14u)  /* 180238 */
#define CS_V5_MOVE_TAIL_2D        8u    /* ply(u32) + 4*u8 (from/to/promo/flags) */
#define CS_V5_MOVE_TAIL_4D        14u   /* ply(u32) + 8*u8 + promo(u8) + flags(u8) */

/* Per-dimension channel layout for mode 1 (per-channel replacement).
 * Mirrors qm_2d._H_CHANNELS / encoder_4d._CHANNEL_NAMES. */
#define CS_V5_N_CHANNELS_2D       10u
#define CS_V5_N_CHANNELS_4D       11u
#define CS_V5_CHANNEL_DIM_2D      (CS_V5_ENCODING_DIM_2D / CS_V5_N_CHANNELS_2D)   /* 64 */
#define CS_V5_CHANNEL_DIM_4D      (CS_V5_ENCODING_DIM_4D / CS_V5_N_CHANNELS_4D)   /* 4096 */

/* Per-channel frame body (mode 1) layout:
 *   u32 body_size              // bytes following the body_size field itself
 *   u8  flags                  // bit 0 = CS_V5_PC_FLAG_FULL (independent frame)
 *   u8  n_channels_present     // 0..N_channels
 *   [u8 channel_idx, u8 reserved, float32 buffer[channel_dim]] * n_present
 *   <move-metadata tail>       // 8 B (2D) or 14 B (4D); same as mode 0
 */
#define CS_V5_PC_FLAG_FULL        0x01u
#define CS_V5_PC_HEADER_SIZE      6u   /* u32 body_size + u8 flags + u8 n_chan */
#define CS_V5_PC_BLOCK_PREFIX     2u   /* u8 channel_idx + u8 reserved */

/* The v5 header lives in 256 bytes total. The first 33 bytes carry
 * the actual fields; the remaining 223 are reserved padding. We use
 * an explicit-size struct (33 packed bytes) under the covers, then
 * pad to 256 on read/write. The packed representation is what the
 * file format defines; the in-memory C struct mirrors it for
 * convenience but should not be assumed to round-trip via fwrite()
 * without explicit padding.
 */
typedef struct {
    uint64_t magic;          /* CS_V5_MAGIC */
    uint32_t version;        /* CS_V5_VERSION = 5 */
    uint32_t encoding_dim;   /* 640 or 45056 */
    uint32_t frame_bytes;    /* dense-equivalent frame body size */
    uint32_t n_plies;
    uint32_t board_dim_side; /* 8 */
    uint32_t n_dimensions;   /* 2 or 4 */
    uint8_t  encoding_mode;  /* 0/1/2 */
} cs_v5_header_t;

/* Pack a v5 header into a 256-byte buffer (`out`). Byte order is
 * little-endian (native on x86_64; the function does explicit byte-
 * level writes so it's portable). The 223 trailing padding bytes are
 * zero-filled. Returns 0 on success, non-zero if any field is invalid
 * (n_dimensions not in {2,4}; encoding_mode not in {0,1,2}; or magic
 * != CS_V5_MAGIC). */
int cs_v5_header_pack(const cs_v5_header_t *hdr, uint8_t out[CS_V5_HEADER_SIZE]);

/* Parse a v5 header from a 256-byte buffer. Validates magic, version,
 * dimension, and encoding mode. Returns 0 on success; non-zero on:
 *   -1: NULL pointer
 *   -2: bad magic (not LARTPSEC)
 *   -3: bad version (not 5)
 *   -4: bad n_dimensions (not 2 or 4)
 *   -5: bad encoding_mode (not 0/1/2)
 *   -6: encoding_dim doesn't match n_dimensions (640 for 2D, 45056 for 4D)
 */
int cs_v5_header_unpack(const uint8_t in[CS_V5_HEADER_SIZE], cs_v5_header_t *hdr);

/* Read the first 12 bytes of fp (after any gzip transparent
 * decompression — the caller is responsible for that) and return the
 * version field. Used by readers to dispatch between v2 / v4 / v5
 * without reading the full header. The fp position is restored.
 *
 * Returns the version on success (a non-negative uint32), or -1 on
 * I/O error / -2 on bad magic. */
int cs_v5_peek_version(FILE *fp);

/* Read a v5 header from fp. fp must be positioned at the start of
 * the header (offset 0 of the file/stream). Returns 0 on success and
 * fills *hdr; same negative error codes as cs_v5_header_unpack on
 * structural validation failure, plus -7 on short read. */
int cs_v5_header_read(FILE *fp, cs_v5_header_t *hdr);

/* Write a packed v5 header (256 bytes) to fp at fp's current
 * position. Returns 0 on success or non-zero on I/O failure. The
 * caller is responsible for positioning fp; this routine writes
 * exactly 256 bytes and does not seek. */
int cs_v5_header_write(FILE *fp, const cs_v5_header_t *hdr);


/* ----- Dense-mode (mode 0) full-file I/O ----------------------- */

/* Write a complete v5 dense (mode 0) 2D file: header + n_plies *
 * frame bodies. Each frame body is a contiguous 2568-byte block:
 * 2560 bytes of float32 encoding + 8 bytes of move metadata
 * (ply u32, move_from u8, move_to u8, move_promo u8, move_flags u8),
 * matching the layout of cs_spectral_frame_t in cs_frame.h.
 *
 * The header is built from CS_V5_* constants + the n_plies argument
 * — caller doesn't need to fill cs_v5_header_t. Returns 0 on success
 * or -7 on I/O error. */
int cs_v5_write_dense_2d_file(FILE *fp,
                              const void *frame_bytes,
                              uint32_t n_plies);

/* Read a complete v5 dense (mode 0) 2D file. fp must be at start.
 * Reads the header, validates dimension and mode, then reads up to
 * `max_plies` frame bodies into `frame_buf` (must be at least
 * `max_plies * CS_V5_FRAME_BYTES_2D` bytes). Sets *n_plies_out to
 * the actual count read (clamped to the file's n_plies). Optional
 * hdr_out receives the parsed header. Returns 0 on success; same
 * negative codes as cs_v5_header_read for header errors, plus
 * -8 if the header's n_dimensions / encoding_mode / encoding_dim
 * don't match a 2D dense file. */
int cs_v5_read_dense_2d_file(FILE *fp,
                             cs_v5_header_t *hdr_out,
                             void *frame_buf,
                             uint32_t max_plies,
                             uint32_t *n_plies_out);

/* Write a complete v5 dense (mode 0) 4D file: header + n_plies *
 * frame bodies. Each frame body is 180238 bytes (45056 * 4 + 14),
 * matching cs_spectral_frame_4d_t in cs_frame_4d.h. */
int cs_v5_write_dense_4d_file(FILE *fp,
                              const void *frame_bytes,
                              uint32_t n_plies);

/* Read a complete v5 dense (mode 0) 4D file. Same shape as
 * cs_v5_read_dense_2d_file but with 4D field expectations
 * (encoding_dim=45056, n_dimensions=4). frame_buf >=
 * max_plies * CS_V5_FRAME_BYTES_4D bytes. */
int cs_v5_read_dense_4d_file(FILE *fp,
                             cs_v5_header_t *hdr_out,
                             void *frame_buf,
                             uint32_t max_plies,
                             uint32_t *n_plies_out);


/* ----- Per-channel mode (mode 1) full-file I/O ---------------- */

/* Write a complete v5 per-channel (mode 1) 2D file: header + n_plies *
 * variable-length bodies. The caller passes a contiguous buffer of
 * dense-equivalent 2D frames (CS_V5_FRAME_BYTES_2D each = 2568 bytes:
 * float32 encoding[640] + 8-byte move tail), the same layout used by
 * cs_v5_write_dense_2d_file. The writer:
 *   - emits frame 0 as a FULL block (flags & PC_FLAG_FULL = 1, all
 *     CS_V5_N_CHANNELS_2D channels written)
 *   - for frames 1..n-1, compares against the previous dense frame
 *     channel-by-channel (bit-exact float32 via uint32 view) and emits
 *     only the channels that differ
 *   - appends the 8-byte move-metadata tail after each body's
 *     channels block
 *
 * Returns 0 on success or -7 on I/O error. */
int cs_v5_write_per_channel_2d_file(FILE *fp,
                                     const void *dense_encodings,
                                     uint32_t n_plies);

/* Write a complete v5 per-channel (mode 1) 4D file. Same shape as
 * cs_v5_write_per_channel_2d_file but with 4D layout:
 * CS_V5_N_CHANNELS_4D=11 channels, CS_V5_CHANNEL_DIM_4D=4096 dim each,
 * CS_V5_FRAME_BYTES_4D=180238 input frame size, 14-byte move tail. */
int cs_v5_write_per_channel_4d_file(FILE *fp,
                                     const void *dense_encodings,
                                     uint32_t n_plies);

/* Read a complete v5 per-channel (mode 1) 2D file. Reconstructs each
 * frame's full dense encoding from per-channel deltas and writes the
 * dense frame body (encoding + move tail = 2568 bytes) into
 * dense_encodings_buf. Same usage pattern as cs_v5_read_dense_2d_file
 * but consuming a mode-1 file.
 *
 * Returns 0 on success; -8 if file isn't 2D mode-1; -7 on truncation;
 * -9 on malformed body (bad channel index, body_size mismatch, or a
 * non-leading delta frame missing prev_encoding state). */
int cs_v5_read_per_channel_2d_file(FILE *fp,
                                    cs_v5_header_t *hdr_out,
                                    void *dense_encodings_buf,
                                    uint32_t max_plies,
                                    uint32_t *n_plies_out);

/* Read a complete v5 per-channel (mode 1) 4D file. Same shape as
 * cs_v5_read_per_channel_2d_file but with 4D layout. dense_encodings_buf
 * must be at least max_plies * CS_V5_FRAME_BYTES_4D bytes. */
int cs_v5_read_per_channel_4d_file(FILE *fp,
                                    cs_v5_header_t *hdr_out,
                                    void *dense_encodings_buf,
                                    uint32_t max_plies,
                                    uint32_t *n_plies_out);


/* ----- XOR-stream mode (mode 2) full-file I/O ---------------- *
 *
 * Mode 2 is fixed-frame-size like dense (mode 0). The DIFFERENCE is
 * what the bytes contain: each frame's float32 encoding portion is
 * the bit-XOR (uint32-view) of the real frame's encoding with the
 * previous *reconstructed* frame's encoding. Frame 0 is XOR'd with
 * zero (i.e. stored verbatim). The move-metadata tail is unchanged.
 *
 * Reconstruction: real[N] = stored[N] XOR real[N-1] (uint32 view);
 * real[0] = stored[0]. Bit-exact, lossless. Wins because chess
 * encoder hypervectors are largely stable per ply — XOR produces
 * long runs of zero bytes where nothing changed, and gzip eats
 * those for free. Empirical 4D spike: 7.23x compression on a
 * 50-ply knight-tour fixture.
 */

/* Write a complete v5 XOR-stream (mode 2) 2D file. Caller passes a
 * contiguous buffer of dense-equivalent frames (CS_V5_FRAME_BYTES_2D
 * each, identical layout to cs_v5_write_dense_2d_file). The writer
 * applies the XOR transform in-flight: frame 0 is written verbatim;
 * subsequent frames have their encoding bytes XOR'd with the prior
 * REAL frame's encoding bytes before write. The move tail is appended
 * unchanged. Returns 0 on success or -7 on I/O. */
int cs_v5_write_xor_stream_2d_file(FILE *fp,
                                    const void *dense_encodings,
                                    uint32_t n_plies);

/* Write a complete v5 XOR-stream (mode 2) 4D file. */
int cs_v5_write_xor_stream_4d_file(FILE *fp,
                                    const void *dense_encodings,
                                    uint32_t n_plies);

/* Read a complete v5 XOR-stream (mode 2) 2D file. Reconstructs each
 * frame's full dense layout (encoding + move tail) into
 * dense_encodings_buf via cumulative XOR application. Returns 0 on
 * success; -8 on header mode/dimension mismatch; -7 on truncation.
 * dense_encodings_buf must be at least max_plies * CS_V5_FRAME_BYTES_2D
 * bytes. */
int cs_v5_read_xor_stream_2d_file(FILE *fp,
                                   cs_v5_header_t *hdr_out,
                                   void *dense_encodings_buf,
                                   uint32_t max_plies,
                                   uint32_t *n_plies_out);

/* Read a complete v5 XOR-stream (mode 2) 4D file. dense_encodings_buf
 * must be at least max_plies * CS_V5_FRAME_BYTES_4D bytes. */
int cs_v5_read_xor_stream_4d_file(FILE *fp,
                                   cs_v5_header_t *hdr_out,
                                   void *dense_encodings_buf,
                                   uint32_t max_plies,
                                   uint32_t *n_plies_out);

#ifdef __cplusplus
}
#endif

#endif /* CS_FRAME_V5_H */
