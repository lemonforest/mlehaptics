/* test_frame_v5.c — unit tests for cs_frame_v5.c (v1.6.x Track 2 PR-1).
 *
 * Validates:
 *   - cs_v5_header_pack rejects malformed inputs
 *   - cs_v5_header_pack/unpack round-trip preserves all fields
 *   - 256-byte buffer is correctly populated (header + zero padding)
 *   - cs_v5_peek_version returns the right version on a packed buffer
 *   - cs_v5_header_read pulls the correct fields from a stream
 *   - byte-for-byte parity with the Python frame_v5.py output
 *     (the Python writer's 256-byte header is hex-encoded into a
 *     fixture below; this is the load-bearing parity check)
 */
#include "cs_frame_v5.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int g_fails = 0;
static int g_assertions = 0;

#define ASSERT_EQ_U32(actual, expected, label) do { \
    g_assertions++; \
    if ((uint32_t)(actual) != (uint32_t)(expected)) { \
        fprintf(stderr, "  FAIL %s: got %u expected %u\n", \
                (label), (uint32_t)(actual), (uint32_t)(expected)); \
        g_fails++; \
    } \
} while (0)

#define ASSERT_EQ_U64(actual, expected, label) do { \
    g_assertions++; \
    if ((uint64_t)(actual) != (uint64_t)(expected)) { \
        fprintf(stderr, "  FAIL %s: got 0x%llx expected 0x%llx\n", \
                (label), (unsigned long long)(actual), \
                (unsigned long long)(expected)); \
        g_fails++; \
    } \
} while (0)

#define ASSERT_EQ_INT(actual, expected, label) do { \
    g_assertions++; \
    if ((int)(actual) != (int)(expected)) { \
        fprintf(stderr, "  FAIL %s: got %d expected %d\n", \
                (label), (int)(actual), (int)(expected)); \
        g_fails++; \
    } \
} while (0)


/* ---- Pack / unpack round-trip ----------------------------------- */

static void test_pack_unpack_2d_dense(void) {
    cs_v5_header_t hdr = {
        .magic = CS_V5_MAGIC,
        .version = CS_V5_VERSION,
        .encoding_dim = CS_V5_ENCODING_DIM_2D,
        .frame_bytes = CS_V5_FRAME_BYTES_2D,
        .n_plies = 42u,
        .board_dim_side = CS_V5_BOARD_SIDE,
        .n_dimensions = 2u,
        .encoding_mode = CS_V5_MODE_DENSE,
    };
    uint8_t buf[CS_V5_HEADER_SIZE];
    int rc = cs_v5_header_pack(&hdr, buf);
    ASSERT_EQ_INT(rc, 0, "pack 2D-dense rc");

    cs_v5_header_t got;
    memset(&got, 0xAA, sizeof(got));  /* poison */
    rc = cs_v5_header_unpack(buf, &got);
    ASSERT_EQ_INT(rc, 0, "unpack 2D-dense rc");
    ASSERT_EQ_U64(got.magic, CS_V5_MAGIC, "magic round-trip");
    ASSERT_EQ_U32(got.version, CS_V5_VERSION, "version round-trip");
    ASSERT_EQ_U32(got.encoding_dim, CS_V5_ENCODING_DIM_2D, "encoding_dim round-trip");
    ASSERT_EQ_U32(got.frame_bytes, CS_V5_FRAME_BYTES_2D, "frame_bytes round-trip");
    ASSERT_EQ_U32(got.n_plies, 42u, "n_plies round-trip");
    ASSERT_EQ_U32(got.board_dim_side, 8u, "board_dim_side round-trip");
    ASSERT_EQ_U32(got.n_dimensions, 2u, "n_dimensions round-trip");
    ASSERT_EQ_INT(got.encoding_mode, CS_V5_MODE_DENSE, "encoding_mode round-trip");
}

static void test_pack_unpack_4d_xor(void) {
    cs_v5_header_t hdr = {
        .magic = CS_V5_MAGIC,
        .version = CS_V5_VERSION,
        .encoding_dim = CS_V5_ENCODING_DIM_4D,
        .frame_bytes = CS_V5_FRAME_BYTES_4D,
        .n_plies = 88u,
        .board_dim_side = CS_V5_BOARD_SIDE,
        .n_dimensions = 4u,
        .encoding_mode = CS_V5_MODE_XOR_STREAM,
    };
    uint8_t buf[CS_V5_HEADER_SIZE];
    int rc = cs_v5_header_pack(&hdr, buf);
    ASSERT_EQ_INT(rc, 0, "pack 4D-xor rc");

    cs_v5_header_t got;
    rc = cs_v5_header_unpack(buf, &got);
    ASSERT_EQ_INT(rc, 0, "unpack 4D-xor rc");
    ASSERT_EQ_U32(got.encoding_dim, CS_V5_ENCODING_DIM_4D, "4D encoding_dim");
    ASSERT_EQ_U32(got.n_dimensions, 4u, "4D n_dimensions");
    ASSERT_EQ_INT(got.encoding_mode, CS_V5_MODE_XOR_STREAM, "xor encoding_mode");
}


/* ---- Padding zero-fill ------------------------------------------ */

static void test_padding_is_zero(void) {
    cs_v5_header_t hdr = {
        .magic = CS_V5_MAGIC,
        .version = CS_V5_VERSION,
        .encoding_dim = CS_V5_ENCODING_DIM_2D,
        .frame_bytes = CS_V5_FRAME_BYTES_2D,
        .n_plies = 0u,
        .board_dim_side = CS_V5_BOARD_SIDE,
        .n_dimensions = 2u,
        .encoding_mode = CS_V5_MODE_DENSE,
    };
    uint8_t buf[CS_V5_HEADER_SIZE];
    /* Poison the buffer first to verify pack zeroes it. */
    memset(buf, 0xCC, sizeof(buf));
    int rc = cs_v5_header_pack(&hdr, buf);
    ASSERT_EQ_INT(rc, 0, "pack rc");
    /* Bytes 33..255 must be zero (the reserved[223] padding). */
    int padding_clean = 1;
    for (int i = 33; i < CS_V5_HEADER_SIZE; ++i) {
        if (buf[i] != 0u) { padding_clean = 0; break; }
    }
    g_assertions++;
    if (!padding_clean) {
        fprintf(stderr, "  FAIL padding not zero-filled\n");
        g_fails++;
    }
}


/* ---- Validation rejects malformed inputs ----------------------- */

static void test_pack_rejects_bad_n_dimensions(void) {
    cs_v5_header_t hdr = {
        .magic = CS_V5_MAGIC, .version = CS_V5_VERSION,
        .encoding_dim = CS_V5_ENCODING_DIM_2D,
        .frame_bytes = CS_V5_FRAME_BYTES_2D, .n_plies = 0u,
        .board_dim_side = CS_V5_BOARD_SIDE,
        .n_dimensions = 3u,  /* invalid */
        .encoding_mode = CS_V5_MODE_DENSE,
    };
    uint8_t buf[CS_V5_HEADER_SIZE];
    int rc = cs_v5_header_pack(&hdr, buf);
    ASSERT_EQ_INT(rc, -4, "reject n_dimensions=3");
}

static void test_pack_rejects_bad_encoding_mode(void) {
    cs_v5_header_t hdr = {
        .magic = CS_V5_MAGIC, .version = CS_V5_VERSION,
        .encoding_dim = CS_V5_ENCODING_DIM_2D,
        .frame_bytes = CS_V5_FRAME_BYTES_2D, .n_plies = 0u,
        .board_dim_side = CS_V5_BOARD_SIDE, .n_dimensions = 2u,
        .encoding_mode = 99u,  /* invalid */
    };
    uint8_t buf[CS_V5_HEADER_SIZE];
    int rc = cs_v5_header_pack(&hdr, buf);
    ASSERT_EQ_INT(rc, -5, "reject encoding_mode=99");
}

static void test_pack_rejects_dim_mismatch(void) {
    cs_v5_header_t hdr = {
        .magic = CS_V5_MAGIC, .version = CS_V5_VERSION,
        .encoding_dim = CS_V5_ENCODING_DIM_4D,  /* 4D dim with 2D n_dimensions */
        .frame_bytes = CS_V5_FRAME_BYTES_2D, .n_plies = 0u,
        .board_dim_side = CS_V5_BOARD_SIDE, .n_dimensions = 2u,
        .encoding_mode = CS_V5_MODE_DENSE,
    };
    uint8_t buf[CS_V5_HEADER_SIZE];
    int rc = cs_v5_header_pack(&hdr, buf);
    ASSERT_EQ_INT(rc, -6, "reject 2D with 45056 dim");
}

static void test_unpack_rejects_bad_magic(void) {
    uint8_t buf[CS_V5_HEADER_SIZE];
    memset(buf, 0, sizeof(buf));
    /* Write a deliberately-wrong magic. */
    const char wrong[] = "BADMAGIC";
    memcpy(buf, wrong, 8);
    /* Set valid-looking other fields so the magic-check is the actual fail. */
    buf[8] = 5;  /* version=5 little-endian byte 0 */
    cs_v5_header_t hdr;
    int rc = cs_v5_header_unpack(buf, &hdr);
    ASSERT_EQ_INT(rc, -2, "reject bad magic");
}


/* ---- File I/O round-trip ---------------------------------------- */

static void test_file_round_trip(void) {
    cs_v5_header_t hdr = {
        .magic = CS_V5_MAGIC, .version = CS_V5_VERSION,
        .encoding_dim = CS_V5_ENCODING_DIM_4D,
        .frame_bytes = CS_V5_FRAME_BYTES_4D,
        .n_plies = 17u, .board_dim_side = 8u,
        .n_dimensions = 4u, .encoding_mode = CS_V5_MODE_PER_CHANNEL,
    };

    /* Use tmpfile() — auto-cleanup, no name collisions. */
    FILE *fp = tmpfile();
    g_assertions++;
    if (!fp) {
        fprintf(stderr, "  FAIL tmpfile()\n");
        g_fails++;
        return;
    }

    int rc = cs_v5_header_write(fp, &hdr);
    ASSERT_EQ_INT(rc, 0, "header_write rc");

    /* Rewind and peek. */
    rewind(fp);
    int v = cs_v5_peek_version(fp);
    ASSERT_EQ_INT(v, (int)CS_V5_VERSION, "peek version");

    /* Verify peek restored fp position (we should still be at 0). */
    long pos = ftell(fp);
    ASSERT_EQ_INT((int)pos, 0, "peek restored fp");

    /* Read back. */
    cs_v5_header_t got;
    rc = cs_v5_header_read(fp, &got);
    ASSERT_EQ_INT(rc, 0, "header_read rc");
    ASSERT_EQ_U32(got.encoding_dim, CS_V5_ENCODING_DIM_4D, "round-trip encoding_dim");
    ASSERT_EQ_U32(got.n_plies, 17u, "round-trip n_plies");
    ASSERT_EQ_INT(got.encoding_mode, CS_V5_MODE_PER_CHANNEL, "round-trip mode");

    fclose(fp);
}


/* ---- Byte-for-byte parity with the Python reference -------------
 *
 * frame_v5.py produces this exact byte sequence for a 2D-dense
 * header with n_plies=42. Captured via:
 *
 *   from chess_spectral.frame_v5 import HeaderV5, MODE_DENSE
 *   h = HeaderV5(encoding_dim=640, n_plies=42, n_dimensions=2,
 *                encoding_mode=MODE_DENSE)
 *   print(h.pack().hex())
 *
 * Captured 2026-04-30. The first 33 bytes encode the fields; the
 * remaining 223 bytes are zero padding (verified by the
 * test_padding_is_zero case above so we don't list them all here).
 */
static const uint8_t PYTHON_REFERENCE_HEADER_2D_DENSE[33] = {
    /* magic "LARTPSEC" */
    0x4c, 0x41, 0x52, 0x54, 0x50, 0x53, 0x45, 0x43,
    /* version=5  (uint32 LE) */
    0x05, 0x00, 0x00, 0x00,
    /* encoding_dim=640 = 0x00000280  (uint32 LE) */
    0x80, 0x02, 0x00, 0x00,
    /* frame_bytes=2568 = 0x00000a08  (uint32 LE) */
    0x08, 0x0a, 0x00, 0x00,
    /* n_plies=42 = 0x0000002a  (uint32 LE) */
    0x2a, 0x00, 0x00, 0x00,
    /* board_dim_side=8  (uint32 LE) */
    0x08, 0x00, 0x00, 0x00,
    /* n_dimensions=2  (uint32 LE) */
    0x02, 0x00, 0x00, 0x00,
    /* encoding_mode=0  (uint8) */
    0x00,
};

static void test_byte_parity_with_python(void) {
    cs_v5_header_t hdr = {
        .magic = CS_V5_MAGIC, .version = CS_V5_VERSION,
        .encoding_dim = CS_V5_ENCODING_DIM_2D,
        .frame_bytes = CS_V5_FRAME_BYTES_2D,
        .n_plies = 42u, .board_dim_side = CS_V5_BOARD_SIDE,
        .n_dimensions = 2u, .encoding_mode = CS_V5_MODE_DENSE,
    };
    uint8_t buf[CS_V5_HEADER_SIZE];
    int rc = cs_v5_header_pack(&hdr, buf);
    ASSERT_EQ_INT(rc, 0, "pack rc");

    /* Compare the first 33 bytes (the actual fields) to Python's
     * output. The remaining 223 bytes are zero in both cases, already
     * verified by test_padding_is_zero. */
    int bytewise_ok = 1;
    for (int i = 0; i < 33; ++i) {
        if (buf[i] != PYTHON_REFERENCE_HEADER_2D_DENSE[i]) {
            fprintf(stderr,
                    "  FAIL byte %d: C=0x%02x Python=0x%02x\n",
                    i, buf[i], PYTHON_REFERENCE_HEADER_2D_DENSE[i]);
            bytewise_ok = 0;
            g_fails++;
        }
    }
    g_assertions++;
    if (!bytewise_ok) {
        fprintf(stderr,
                "  C-side v5 header does NOT match Python frame_v5.py byte-for-byte\n");
    }
}


/* ---- Dense-mode (mode 0) full-file I/O round-trips -------------- */

static void test_dense_2d_full_file_round_trip(void) {
    /* Synthesize 3 frames worth of bytes (3 * 2568 = 7704 bytes total)
     * and write them to a tmpfile under a v5 dense 2D header. Then
     * read back and verify byte-for-byte equality. */
    const uint32_t N = 3u;
    const size_t fs = (size_t)CS_V5_FRAME_BYTES_2D;
    const size_t total = fs * (size_t)N;
    uint8_t *src = (uint8_t *)malloc(total);
    g_assertions++;
    if (!src) { fprintf(stderr, "  FAIL malloc\n"); g_fails++; return; }
    for (size_t i = 0; i < total; ++i) src[i] = (uint8_t)((i * 37u) & 0xFFu);

    FILE *fp = tmpfile();
    g_assertions++;
    if (!fp) { fprintf(stderr, "  FAIL tmpfile\n"); g_fails++; free(src); return; }

    int rc = cs_v5_write_dense_2d_file(fp, src, N);
    ASSERT_EQ_INT(rc, 0, "write_dense_2d rc");

    rewind(fp);
    uint8_t *dst = (uint8_t *)malloc(total);
    g_assertions++;
    if (!dst) { g_fails++; free(src); fclose(fp); return; }
    cs_v5_header_t hdr;
    uint32_t got_n = 0;
    rc = cs_v5_read_dense_2d_file(fp, &hdr, dst, N, &got_n);
    ASSERT_EQ_INT(rc, 0, "read_dense_2d rc");
    ASSERT_EQ_U32(got_n, N, "n_plies_out");
    ASSERT_EQ_U32(hdr.encoding_dim, CS_V5_ENCODING_DIM_2D, "header encoding_dim");
    ASSERT_EQ_U32(hdr.n_dimensions, 2u, "header n_dimensions");
    ASSERT_EQ_INT(hdr.encoding_mode, CS_V5_MODE_DENSE, "header encoding_mode");

    g_assertions++;
    if (memcmp(src, dst, total) != 0) {
        fprintf(stderr, "  FAIL frame body bytes mismatch\n");
        g_fails++;
    }

    free(src); free(dst); fclose(fp);
}

static void test_dense_2d_truncates_to_max_plies(void) {
    /* Write 5 frames; read with max_plies=2. Bytes for frames 0..1
     * should match the source. */
    const uint32_t N_WRITE = 5u, N_READ = 2u;
    const size_t fs = (size_t)CS_V5_FRAME_BYTES_2D;
    const size_t total = fs * (size_t)N_WRITE;
    uint8_t *src = (uint8_t *)malloc(total);
    if (!src) { g_assertions++; g_fails++; return; }
    for (size_t i = 0; i < total; ++i) src[i] = (uint8_t)((i * 13u) & 0xFFu);

    FILE *fp = tmpfile();
    if (!fp) { g_assertions++; g_fails++; free(src); return; }
    int rc = cs_v5_write_dense_2d_file(fp, src, N_WRITE);
    ASSERT_EQ_INT(rc, 0, "write 5-frame rc");
    rewind(fp);

    uint8_t *dst = (uint8_t *)malloc(fs * (size_t)N_READ);
    if (!dst) { g_assertions++; g_fails++; free(src); fclose(fp); return; }
    uint32_t got_n = 0;
    rc = cs_v5_read_dense_2d_file(fp, NULL, dst, N_READ, &got_n);
    ASSERT_EQ_INT(rc, 0, "read truncated rc");
    ASSERT_EQ_U32(got_n, N_READ, "got_n clamped to max_plies");
    g_assertions++;
    if (memcmp(src, dst, fs * (size_t)N_READ) != 0) {
        fprintf(stderr, "  FAIL truncated read bytes mismatch\n");
        g_fails++;
    }
    free(src); free(dst); fclose(fp);
}

static void test_dense_4d_full_file_round_trip(void) {
    const uint32_t N = 1u;
    const size_t fs = (size_t)CS_V5_FRAME_BYTES_4D;
    uint8_t *src = (uint8_t *)malloc(fs);
    if (!src) { g_assertions++; g_fails++; return; }
    for (size_t i = 0; i < fs; ++i) src[i] = (uint8_t)((i * 7u) & 0xFFu);

    FILE *fp = tmpfile();
    if (!fp) { g_assertions++; g_fails++; free(src); return; }
    int rc = cs_v5_write_dense_4d_file(fp, src, N);
    ASSERT_EQ_INT(rc, 0, "write_dense_4d rc");
    rewind(fp);

    uint8_t *dst = (uint8_t *)malloc(fs);
    if (!dst) { g_assertions++; g_fails++; free(src); fclose(fp); return; }
    cs_v5_header_t hdr;
    uint32_t got_n = 0;
    rc = cs_v5_read_dense_4d_file(fp, &hdr, dst, N, &got_n);
    ASSERT_EQ_INT(rc, 0, "read_dense_4d rc");
    ASSERT_EQ_U32(hdr.encoding_dim, CS_V5_ENCODING_DIM_4D, "4D encoding_dim");
    ASSERT_EQ_U32(hdr.n_dimensions, 4u, "4D n_dimensions");
    g_assertions++;
    if (memcmp(src, dst, fs) != 0) {
        fprintf(stderr, "  FAIL 4D frame bytes mismatch\n");
        g_fails++;
    }
    free(src); free(dst); fclose(fp);
}

static void test_dense_2d_reader_rejects_4d_file(void) {
    FILE *fp = tmpfile();
    if (!fp) { g_assertions++; g_fails++; return; }
    int rc = cs_v5_write_dense_4d_file(fp, NULL, 0u);
    ASSERT_EQ_INT(rc, 0, "write 4D-empty rc");
    rewind(fp);

    cs_v5_header_t hdr;
    uint32_t got_n = 0;
    rc = cs_v5_read_dense_2d_file(fp, &hdr, NULL, 0u, &got_n);
    ASSERT_EQ_INT(rc, -8, "2D reader rejects 4D file");
    fclose(fp);
}


int test_frame_v5(void) {
    g_fails = 0;
    g_assertions = 0;

    test_pack_unpack_2d_dense();
    test_pack_unpack_4d_xor();
    test_padding_is_zero();
    test_pack_rejects_bad_n_dimensions();
    test_pack_rejects_bad_encoding_mode();
    test_pack_rejects_dim_mismatch();
    test_unpack_rejects_bad_magic();
    test_file_round_trip();
    test_byte_parity_with_python();
    test_dense_2d_full_file_round_trip();
    test_dense_2d_truncates_to_max_plies();
    test_dense_4d_full_file_round_trip();
    test_dense_2d_reader_rejects_4d_file();

    printf("  %d/%d assertions passed\n",
           g_assertions - g_fails, g_assertions);
    return g_fails == 0 ? 0 : 1;
}
