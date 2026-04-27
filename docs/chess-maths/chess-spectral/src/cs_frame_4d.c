/* cs_frame_4d.c — binary .spectralz4 (v3 / v4) frame I/O.
 *
 * Mirrors python/chess_spectral/frame_4d.py exactly. The Python writer
 * and this C writer must produce byte-identical output for identical
 * encodings — that is the parity contract for Phase B's end-to-end
 * .spectralz4 test.
 */
#include <string.h>
#include <stdio.h>
#include "cs_frame_4d.h"

void cs_file_4d_header_init(cs_file_header_4d_t *hdr)
{
    if (!hdr) return;
    memset(hdr, 0, sizeof(*hdr));
    hdr->magic          = CS_FILE_4D_MAGIC;
    hdr->version        = CS_FILE_4D_VERSION;
    hdr->encoding_dim   = CS_ENCODING_DIM_4D;
    hdr->frame_bytes    = CS_ENCODING_DIM_4D * 4u + CS_FRAME_4D_TAIL_BYTES;
    hdr->n_plies        = 0u;  /* caller backfills */
    hdr->board_dim_side = 8u;
    hdr->n_dimensions   = 4u;
    /* _pad already zeroed by memset */
}

int cs_file_4d_write_header(FILE *fp, const cs_file_header_4d_t *hdr)
{
    if (!fp || !hdr) return -1;
    if (fseek(fp, 0, SEEK_SET) != 0) return -2;
    if (fwrite(hdr, sizeof(*hdr), 1, fp) != 1) return -3;
    return 0;
}

int cs_file_4d_read_header(FILE *fp, cs_file_header_4d_t *hdr)
{
    if (!fp || !hdr) return -1;
    if (fseek(fp, 0, SEEK_SET) != 0) return -2;
    if (fread(hdr, sizeof(*hdr), 1, fp) != 1) return -3;
    if (hdr->magic != CS_FILE_4D_MAGIC) return -4;
    if (hdr->version != CS_FILE_4D_VERSION
        && hdr->version != CS_FILE_4D_VERSION_V3) return -5;
    /* encoding_dim / frame_bytes consistency */
    if (hdr->frame_bytes != hdr->encoding_dim * 4u + CS_FRAME_4D_TAIL_BYTES)
        return -6;
    return 0;
}

int cs_file_4d_write_frame(FILE *fp, const cs_spectral_frame_4d_t *frame)
{
    if (!fp || !frame) return -1;
    if (fwrite(frame, sizeof(*frame), 1, fp) != 1) return -2;
    return 0;
}

int cs_file_4d_read_frame(FILE *fp, cs_spectral_frame_4d_t *frame)
{
    if (!fp || !frame) return -1;
    if (fread(frame, sizeof(*frame), 1, fp) != 1) return -2;
    return 0;
}
