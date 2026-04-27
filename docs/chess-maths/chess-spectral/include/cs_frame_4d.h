#ifndef CS_FRAME_4D_H
#define CS_FRAME_4D_H

#include <stdio.h>
#include <stdint.h>
#include "cs_types_4d.h"

#ifdef __cplusplus
extern "C" {
#endif

/* spectralz v3 / v4 file format for the 4D encoder. Layout mirrors
 * python/chess_spectral/frame_4d.py byte-for-byte; the parity contract
 * requires that a Python writer and this C writer produce identical
 * bytes for identical encodings.
 *
 * Header (256 B, little-endian):
 *   uint64 magic           "LARTPSEC" (= CS_FILE_4D_MAGIC)
 *   uint32 version         CS_FILE_4D_VERSION (4 for v1.1.1)
 *   uint32 encoding_dim    CS_ENCODING_DIM_4D (45056 for v4)
 *   uint32 frame_bytes     encoding_dim * 4 + 14
 *   uint32 n_plies         number of frames that follow
 *   uint32 board_dim_side  8
 *   uint32 n_dimensions    4
 *   uint8  pad[224]        zero
 *
 * Frame (encoding_dim*4 + 14 B):
 *   float32 encoding[encoding_dim]
 *   uint32 ply
 *   uint8  from_x, from_y, from_z, from_w
 *   uint8  to_x,   to_y,   to_z,   to_w
 *   uint8  promo, flags
 */

#define CS_FILE_4D_MAGIC     0x434553505452414CULL /* "LARTPSEC" LE */
#define CS_FILE_4D_VERSION   4u                    /* v1.1.1 (current) */
#define CS_FILE_4D_VERSION_V3 3u                   /* v1.0 (legacy) */
#define CS_FRAME_4D_TAIL_BYTES 14u                 /* ply(4)+from(4)+to(4)+promo(1)+flags(1) */

typedef struct {
    uint64_t magic;             /* CS_FILE_4D_MAGIC */
    uint32_t version;           /* CS_FILE_4D_VERSION */
    uint32_t encoding_dim;      /* CS_ENCODING_DIM_4D */
    uint32_t frame_bytes;       /* encoding_dim*4 + 14 */
    uint32_t n_plies;           /* set by writer; backfilled in bulk encode */
    uint32_t board_dim_side;    /* 8 */
    uint32_t n_dimensions;      /* 4 */
    uint8_t  _pad[224];         /* reserved; pads header to 256 B */
} cs_file_header_4d_t;

_Static_assert(sizeof(cs_file_header_4d_t) == 256,
               "cs_file_header_4d_t must be 256 B");

/* The frame struct uses #pragma pack to defeat any compiler-inserted
 * padding between the encoding array and the trailing metadata bytes
 * (45056 * 4 = 180224 is 4-aligned, so on most ABIs there'd be no
 * padding anyway, but we make this explicit for correctness across
 * MSVC / GCC / Clang). */
#pragma pack(push, 1)
typedef struct {
    float    encoding[CS_ENCODING_DIM_4D]; /* 180 224 B */
    uint32_t ply;                          /* 4 B */
    uint8_t  from_x, from_y, from_z, from_w;
    uint8_t  to_x,   to_y,   to_z,   to_w;
    uint8_t  promo;
    uint8_t  flags;
} cs_spectral_frame_4d_t;
#pragma pack(pop)

_Static_assert(sizeof(cs_spectral_frame_4d_t)
               == CS_ENCODING_DIM_4D * 4 + 14,
               "cs_spectral_frame_4d_t must be encoding_dim*4 + 14 bytes");

/* File I/O — all return 0 on success, non-zero on error. */
int cs_file_4d_write_header(FILE *fp, const cs_file_header_4d_t *hdr);
int cs_file_4d_read_header (FILE *fp, cs_file_header_4d_t *hdr);
int cs_file_4d_write_frame (FILE *fp, const cs_spectral_frame_4d_t *frame);
int cs_file_4d_read_frame  (FILE *fp, cs_spectral_frame_4d_t *frame);

/* Initialize a header struct with all standard v4 fields populated.
 * `n_plies` is set to 0; the caller backfills after writing all frames. */
void cs_file_4d_header_init(cs_file_header_4d_t *hdr);

#ifdef __cplusplus
}
#endif

#endif /* CS_FRAME_4D_H */
