#ifndef CS_FRAME_H
#define CS_FRAME_H

#include <stdio.h>
#include <stdint.h>
#include "cs_types.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Binary .spectral file format v2 — encoding-only.
 * Layout: [cs_file_header_t][cs_spectral_frame_t × N_plies]
 * All fields are little-endian (native on x86_64).
 *
 * v2 rationale: v1 redundantly stored bitboards, delta[640], 8 scalar
 * energies, and a per-file history[640] that readers always recomputed
 * anyway. v2 keeps only the encoding + identifying ply/move metadata;
 * deltas, energies, and piece placement are derived on the fly.
 *
 * Header : 8 + 4 + 4 + 4 + 4 + 232 pad  = 256 B
 * Frame  : 640*4 encoding + 4 ply + 4 move-metadata = 2568 B
 */

#define CS_FILE_MAGIC        0x434553505452414CULL /* "LARTPSEC" reversed endian */
#define CS_FILE_VERSION      2u

typedef struct {
    uint64_t magic;             /* CS_FILE_MAGIC */
    uint32_t version;           /* CS_FILE_VERSION */
    uint32_t encoding_dim;      /* 640 */
    uint32_t frame_bytes;       /* sizeof(cs_spectral_frame_t) == 2568 */
    uint32_t n_plies;           /* number of frames that follow */
    uint8_t  _pad[232];         /* reserved; pads header to 256 B */
} cs_file_header_t;

typedef struct {
    float    encoding[CS_ENCODING_DIM]; /* 2560 B */
    uint32_t ply;                       /* 4 B */
    uint8_t  move_from;                 /* 0..63, 0xFF if unset */
    uint8_t  move_to;                   /* 0..63, 0xFF if unset */
    uint8_t  move_promo;                /* piece enum or 0 */
    uint8_t  move_flags;                /* reserved for castling/ep/check */
} cs_spectral_frame_t;

_Static_assert(sizeof(cs_file_header_t)    == 256,  "cs_file_header_t must be 256 B");
_Static_assert(sizeof(cs_spectral_frame_t) == 2568, "cs_spectral_frame_t must be 2568 B");

/* File I/O. All functions return 0 on success, non-zero on error. */
int  cs_file_write_header(FILE *fp, const cs_file_header_t *hdr);
int  cs_file_read_header (FILE *fp, cs_file_header_t *hdr);
int  cs_file_write_frame (FILE *fp, const cs_spectral_frame_t *frame);
int  cs_file_read_frame  (FILE *fp, cs_spectral_frame_t *frame);
int  cs_file_seek_frame  (FILE *fp, uint32_t ply, const cs_file_header_t *hdr);

#ifdef __cplusplus
}
#endif

#endif /* CS_FRAME_H */
