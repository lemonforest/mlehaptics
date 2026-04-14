/* cs_frame.c — binary .spectral frame I/O (minimal implementation).
 * The header is written/read as a raw block; frames are appended sequentially.
 */
#include <string.h>
#include <stdio.h>
#include "cs_frame.h"

int cs_file_write_header(FILE *fp, const cs_file_header_t *hdr)
{
    if (!fp || !hdr) return -1;
    if (fseek(fp, 0, SEEK_SET) != 0) return -2;
    if (fwrite(hdr, sizeof(*hdr), 1, fp) != 1) return -3;
    return 0;
}

int cs_file_read_header(FILE *fp, cs_file_header_t *hdr)
{
    if (!fp || !hdr) return -1;
    if (fseek(fp, 0, SEEK_SET) != 0) return -2;
    if (fread(hdr, sizeof(*hdr), 1, fp) != 1) return -3;
    if (hdr->magic != CS_FILE_MAGIC) return -4;
    if (hdr->version != CS_FILE_VERSION) return -5;
    if (hdr->encoding_dim != CS_ENCODING_DIM) return -6;
    return 0;
}

int cs_file_write_frame(FILE *fp, const cs_spectral_frame_t *frame)
{
    if (!fp || !frame) return -1;
    if (fwrite(frame, sizeof(*frame), 1, fp) != 1) return -2;
    return 0;
}

int cs_file_read_frame(FILE *fp, cs_spectral_frame_t *frame)
{
    if (!fp || !frame) return -1;
    if (fread(frame, sizeof(*frame), 1, fp) != 1) return -2;
    return 0;
}

int cs_file_seek_frame(FILE *fp, uint32_t ply, const cs_file_header_t *hdr)
{
    if (!fp || !hdr) return -1;
    if (ply >= hdr->n_plies) return -2;
    long pos = (long)sizeof(cs_file_header_t) + (long)ply * (long)sizeof(cs_spectral_frame_t);
    if (fseek(fp, pos, SEEK_SET) != 0) return -3;
    return 0;
}
