/* cs_gzip.c — transparent gzip read/write for .spectral(z) files.
 *
 * Wraps miniz's raw-deflate streaming API (windowBits = -15) and hand-rolls
 * the gzip header/trailer per RFC 1952. No dependency on the host's zlib.
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "cs_gzip.h"
#include "miniz.h"

/* gzip magic and header-flag bits (RFC 1952 §2.3) */
#define GZ_ID1      0x1Fu
#define GZ_ID2      0x8Bu
#define GZ_CM_DEFLATE 0x08u
#define GZ_FHCRC    0x02u
#define GZ_FEXTRA   0x04u
#define GZ_FNAME    0x08u
#define GZ_FCOMMENT 0x10u

#define CS_GZ_BUF   (64u * 1024u)

static int skip_cstring(FILE *fp)
{
    int c;
    do {
        c = fgetc(fp);
        if (c == EOF) return -1;
    } while (c != 0);
    return 0;
}

/* Read and discard a gzip member header, leaving fp at the first byte of
 * the raw-deflate payload. Returns 0 on success. */
static int gz_parse_header(FILE *fp)
{
    unsigned char h[10];
    if (fread(h, 1, 10, fp) != 10) return -1;
    if (h[0] != GZ_ID1 || h[1] != GZ_ID2) return -2;
    if (h[2] != GZ_CM_DEFLATE)           return -3;

    unsigned flg = h[3];
    if (flg & GZ_FEXTRA) {
        unsigned char lb[2];
        if (fread(lb, 1, 2, fp) != 2) return -4;
        unsigned long xlen = (unsigned long)lb[0] | ((unsigned long)lb[1] << 8);
        if (fseek(fp, (long)xlen, SEEK_CUR) != 0) return -4;
    }
    if (flg & GZ_FNAME)    { if (skip_cstring(fp) != 0) return -5; }
    if (flg & GZ_FCOMMENT) { if (skip_cstring(fp) != 0) return -6; }
    if (flg & GZ_FHCRC)    { if (fseek(fp, 2, SEEK_CUR) != 0) return -7; }
    return 0;
}

/* Decompress raw-deflate bytes from src (already past the gzip header) into
 * dst. Returns 0 on success. */
static int gz_inflate_to_file(FILE *src, FILE *dst)
{
    mz_stream zs;
    memset(&zs, 0, sizeof(zs));
    if (mz_inflateInit2(&zs, -MZ_DEFAULT_WINDOW_BITS) != MZ_OK) return -1;

    unsigned char *in  = (unsigned char *)malloc(CS_GZ_BUF);
    unsigned char *out = (unsigned char *)malloc(CS_GZ_BUF);
    if (!in || !out) { free(in); free(out); mz_inflateEnd(&zs); return -2; }

    int rc = 0;
    for (;;) {
        if (zs.avail_in == 0 && !feof(src)) {
            size_t n = fread(in, 1, CS_GZ_BUF, src);
            if (n == 0 && ferror(src)) { rc = -3; break; }
            zs.next_in  = in;
            zs.avail_in = (unsigned)n;
        }
        zs.next_out  = out;
        zs.avail_out = CS_GZ_BUF;
        int r = mz_inflate(&zs, MZ_NO_FLUSH);
        size_t produced = CS_GZ_BUF - zs.avail_out;
        if (produced > 0) {
            if (fwrite(out, 1, produced, dst) != produced) { rc = -4; break; }
        }
        if (r == MZ_STREAM_END) { rc = 0; break; }
        if (r != MZ_OK)         { rc = -5; break; }
        if (zs.avail_in == 0 && feof(src) && produced == 0) { rc = -6; break; }
    }
    mz_inflateEnd(&zs);
    free(in);
    free(out);
    return rc;
}

int cs_open_read_transparent(const char *path, FILE **out)
{
    if (!path || !out) return -1;
    *out = NULL;

    FILE *fp = fopen(path, "rb");
    if (!fp) return -2;

    int c0 = fgetc(fp);
    int c1 = fgetc(fp);
    int is_gzip = (c0 == GZ_ID1 && c1 == GZ_ID2);

    if (fseek(fp, 0, SEEK_SET) != 0) { fclose(fp); return -3; }

    if (!is_gzip) {
        *out = fp;
        return 0;
    }

    /* gzip member: decompress entirely into a tmpfile and return that. */
    if (gz_parse_header(fp) != 0) { fclose(fp); return -4; }

    FILE *tmp = tmpfile();
    if (!tmp) { fclose(fp); return -5; }

    int r = gz_inflate_to_file(fp, tmp);
    fclose(fp);
    if (r != 0) { fclose(tmp); return -6; }

    if (fseek(tmp, 0, SEEK_SET) != 0) { fclose(tmp); return -7; }
    *out = tmp;
    return 0;
}

int cs_file_write_gzip(const char *dst_path, FILE *src_plain)
{
    if (!dst_path || !src_plain) return -1;
    if (fseek(src_plain, 0, SEEK_SET) != 0) return -2;

    FILE *dst = fopen(dst_path, "wb");
    if (!dst) return -3;

    /* RFC 1952 fixed header: ID1 ID2 CM FLG MTIME(4) XFL OS.
     * MTIME=0 (no time), XFL=0, OS=0xFF (unknown). */
    static const unsigned char gz_hdr[10] = {
        GZ_ID1, GZ_ID2, GZ_CM_DEFLATE, 0x00,
        0x00, 0x00, 0x00, 0x00,
        0x00, 0xFF
    };
    if (fwrite(gz_hdr, 1, 10, dst) != 10) { fclose(dst); return -4; }

    mz_stream zs;
    memset(&zs, 0, sizeof(zs));
    if (mz_deflateInit2(&zs, MZ_DEFAULT_LEVEL, MZ_DEFLATED,
                        -MZ_DEFAULT_WINDOW_BITS, 9,
                        MZ_DEFAULT_STRATEGY) != MZ_OK) {
        fclose(dst);
        return -5;
    }

    unsigned char *in  = (unsigned char *)malloc(CS_GZ_BUF);
    unsigned char *out = (unsigned char *)malloc(CS_GZ_BUF);
    if (!in || !out) {
        free(in); free(out);
        mz_deflateEnd(&zs); fclose(dst);
        return -6;
    }

    mz_ulong crc = MZ_CRC32_INIT;
    uint64_t total_in = 0;
    int rc = 0;
    int input_eof = 0;

    while (rc == 0) {
        size_t n = 0;
        if (!input_eof) {
            n = fread(in, 1, CS_GZ_BUF, src_plain);
            if (n == 0) {
                if (ferror(src_plain)) { rc = -7; break; }
                input_eof = 1;
            } else {
                crc = mz_crc32(crc, in, n);
                total_in += n;
            }
        }
        zs.next_in  = in;
        zs.avail_in = (unsigned)n;

        int flush = input_eof ? MZ_FINISH : MZ_NO_FLUSH;
        int done  = 0;
        while (!done) {
            zs.next_out  = out;
            zs.avail_out = CS_GZ_BUF;
            int r = mz_deflate(&zs, flush);
            size_t produced = CS_GZ_BUF - zs.avail_out;
            if (produced > 0) {
                if (fwrite(out, 1, produced, dst) != produced) {
                    rc = -8; done = 1; break;
                }
            }
            if (r == MZ_STREAM_END) { done = 1; input_eof = 1; break; }
            if (r != MZ_OK)         { rc = -9; done = 1; break; }
            if (zs.avail_in == 0 && zs.avail_out > 0) done = 1;  /* need more input */
        }
        if (input_eof && zs.avail_in == 0 && flush == MZ_FINISH) break;
    }
    mz_deflateEnd(&zs);
    free(in);
    free(out);

    if (rc == 0) {
        /* Trailer: CRC32 + ISIZE (mod 2^32), little-endian. */
        uint32_t c32 = (uint32_t)crc;
        uint32_t isize = (uint32_t)(total_in & 0xFFFFFFFFu);
        unsigned char tail[8] = {
            (unsigned char)( c32        & 0xFFu),
            (unsigned char)((c32 >>  8) & 0xFFu),
            (unsigned char)((c32 >> 16) & 0xFFu),
            (unsigned char)((c32 >> 24) & 0xFFu),
            (unsigned char)( isize       & 0xFFu),
            (unsigned char)((isize >> 8) & 0xFFu),
            (unsigned char)((isize >> 16) & 0xFFu),
            (unsigned char)((isize >> 24) & 0xFFu),
        };
        if (fwrite(tail, 1, 8, dst) != 8) rc = -10;
    }

    fclose(dst);
    return rc;
}
