/* test_gzip.c — round-trip a synthetic .spectral through gzip compression
 * and transparent decompression, verifying byte equality and that the
 * uncompressed path still works.
 */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#include "cs_frame.h"
#include "cs_gzip.h"

#define N_TEST_PLIES 7

static int write_synthetic_blob(FILE *fp)
{
    cs_file_header_t hdr = {0};
    hdr.magic        = CS_FILE_MAGIC;
    hdr.version      = CS_FILE_VERSION;
    hdr.encoding_dim = CS_ENCODING_DIM;
    hdr.frame_bytes  = (uint32_t)sizeof(cs_spectral_frame_t);
    hdr.n_plies      = N_TEST_PLIES;
    if (cs_file_write_header(fp, &hdr) != 0) return -1;

    for (uint32_t p = 0; p < N_TEST_PLIES; p++) {
        cs_spectral_frame_t fr;
        memset(&fr, 0, sizeof(fr));
        for (int i = 0; i < CS_ENCODING_DIM; i++) {
            /* Deterministic pseudo-random-ish content that exercises the
             * compressor (mix of zeros and varied floats). */
            fr.encoding[i] = (i % 13 == 0) ? 0.0f
                           : (float)((int)p * 1000 + i) * 1.5e-3f;
        }
        fr.ply = p;
        fr.move_from = (uint8_t)(p & 0x3F);
        fr.move_to   = (uint8_t)((p + 16) & 0x3F);
        fr.move_promo = 0;
        fr.move_flags = 0;
        if (cs_file_write_frame(fp, &fr) != 0) return -2;
    }
    return 0;
}

static int read_and_verify_blob(FILE *fp)
{
    cs_file_header_t hdr;
    if (cs_file_read_header(fp, &hdr) != 0) {
        fprintf(stderr, "  read_header failed\n"); return -1;
    }
    if (hdr.magic != CS_FILE_MAGIC)           return -2;
    if (hdr.version != CS_FILE_VERSION)       return -3;
    if (hdr.encoding_dim != CS_ENCODING_DIM)  return -4;
    if (hdr.frame_bytes != sizeof(cs_spectral_frame_t)) return -5;
    if (hdr.n_plies != N_TEST_PLIES)          return -6;

    for (uint32_t p = 0; p < N_TEST_PLIES; p++) {
        cs_spectral_frame_t fr;
        if (cs_file_read_frame(fp, &fr) != 0) return -7;
        if (fr.ply != p) return -8;
        if (fr.move_from != (uint8_t)(p & 0x3F))        return -9;
        if (fr.move_to   != (uint8_t)((p + 16) & 0x3F)) return -10;
        for (int i = 0; i < CS_ENCODING_DIM; i++) {
            float expect = (i % 13 == 0) ? 0.0f
                         : (float)((int)p * 1000 + i) * 1.5e-3f;
            if (fr.encoding[i] != expect) return -11;
        }
    }
    return 0;
}

static int write_synthetic_plain_file(const char *path)
{
    FILE *fp = fopen(path, "wb");
    if (!fp) return -1;
    int rc = write_synthetic_blob(fp);
    fclose(fp);
    return rc;
}

int test_gzip(void)
{
    /* 1. Write a plain .spectral and a .spectralz referring to the same
     *    underlying data, then round-trip both through
     *    cs_open_read_transparent and compare. */
    const char *plain_path = "test_gz_plain.spectral";
    const char *gz_path    = "test_gz_compressed.spectralz";

    if (write_synthetic_plain_file(plain_path) != 0) {
        fprintf(stderr, "  failed to write plain file\n"); return 1;
    }

    /* Compress the plain file to gz_path via cs_file_write_gzip. */
    FILE *src = fopen(plain_path, "rb");
    if (!src) return 2;
    int rc = cs_file_write_gzip(gz_path, src);
    fclose(src);
    if (rc != 0) {
        fprintf(stderr, "  cs_file_write_gzip rc=%d\n", rc);
        return 3;
    }

    /* 2. Verify gzip magic in the output. */
    FILE *gz = fopen(gz_path, "rb");
    if (!gz) return 4;
    unsigned char magic[2];
    if (fread(magic, 1, 2, gz) != 2) { fclose(gz); return 5; }
    fclose(gz);
    if (magic[0] != 0x1F || magic[1] != 0x8B) {
        fprintf(stderr, "  output lacks gzip magic: got %02x %02x\n",
                magic[0], magic[1]);
        return 6;
    }

    /* 3. Transparent open + read the .spectralz — should decompress
     *    and return a rewound tmpfile we can read frames from. */
    FILE *fp = NULL;
    if (cs_open_read_transparent(gz_path, &fp) != 0 || !fp) {
        fprintf(stderr, "  cs_open_read_transparent failed on gz\n");
        return 7;
    }
    rc = read_and_verify_blob(fp);
    fclose(fp);
    if (rc != 0) {
        fprintf(stderr, "  gz read-verify rc=%d\n", rc);
        return 8;
    }

    /* 4. Transparent open on a plain file must pass through unchanged. */
    if (cs_open_read_transparent(plain_path, &fp) != 0 || !fp) {
        fprintf(stderr, "  cs_open_read_transparent failed on plain\n");
        return 9;
    }
    rc = read_and_verify_blob(fp);
    fclose(fp);
    if (rc != 0) {
        fprintf(stderr, "  plain read-verify rc=%d\n", rc);
        return 10;
    }

    /* Cleanup. tmpfile()s already auto-deleted; nuke the two disk files. */
    remove(plain_path);
    remove(gz_path);
    return 0;
}
