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

#ifdef __cplusplus
}
#endif

#endif /* CS_FRAME_V5_H */
