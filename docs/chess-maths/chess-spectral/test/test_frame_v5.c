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


/* ---- Per-channel (mode 1) full-file I/O round-trips ------------- *
 *
 * We synthesize "dense-equivalent" inputs in the 2568-byte 2D layout:
 *   bytes 0..2559 = float32 encoding[640]  (10 channels × 64 dim)
 *   bytes 2560..2567 = move tail (ply u32 + 4 u8)
 * The writer computes per-channel deltas and emits the variable-size
 * mode-1 body; the reader reconstructs the dense layout and we check
 * byte-for-byte equality. */

static void _set_channel(uint8_t *frame, uint32_t channel_idx, uint8_t value) {
    /* Set all 64 floats (256 bytes) of one channel in a 2D dense
     * frame to the same byte pattern. Channel layout: channel i
     * occupies bytes [i*256 .. (i+1)*256). */
    memset(frame + channel_idx * 256u, value, 256u);
}

static void _set_2d_move_tail(uint8_t *frame, uint32_t ply,
                               uint8_t mfrom, uint8_t mto,
                               uint8_t mpromo, uint8_t mflags) {
    uint8_t *t = frame + (size_t)CS_V5_ENCODING_DIM_2D * 4u;
    t[0] = (uint8_t)(ply & 0xFFu);
    t[1] = (uint8_t)((ply >> 8) & 0xFFu);
    t[2] = (uint8_t)((ply >> 16) & 0xFFu);
    t[3] = (uint8_t)((ply >> 24) & 0xFFu);
    t[4] = mfrom; t[5] = mto; t[6] = mpromo; t[7] = mflags;
}

static void test_pc_2d_round_trip_progressive_deltas(void) {
    /* 4 frames: frame 0 has channel 0 = 0xAA, all others 0. Then each
     * subsequent frame mutates one additional channel. The reader must
     * reconstruct each frame to its full dense form. */
    const uint32_t N = 4u;
    const size_t fs = (size_t)CS_V5_FRAME_BYTES_2D;
    const size_t total = fs * (size_t)N;
    uint8_t *src = (uint8_t *)calloc(total, 1);
    g_assertions++;
    if (!src) { g_fails++; return; }

    /* Build the source frames. */
    for (uint32_t k = 0; k < N; ++k) {
        uint8_t *f = src + (size_t)k * fs;
        /* Carry forward all previously-set channels by mutating: each
         * frame inherits all channel values from the previous frame
         * (since calloc'd, frame 0 starts at zero everywhere). */
        if (k > 0) memcpy(f, src + (size_t)(k - 1) * fs, fs);
        _set_channel(f, k, (uint8_t)(0xA0u + k));
        _set_2d_move_tail(f, /*ply=*/k, (uint8_t)k, (uint8_t)(k + 1), 0u, 0u);
    }

    FILE *fp = tmpfile();
    if (!fp) { g_assertions++; g_fails++; free(src); return; }
    int rc = cs_v5_write_per_channel_2d_file(fp, src, N);
    ASSERT_EQ_INT(rc, 0, "pc write 2D rc");

    rewind(fp);
    uint8_t *dst = (uint8_t *)calloc(total, 1);
    if (!dst) { g_assertions++; g_fails++; free(src); fclose(fp); return; }
    cs_v5_header_t hdr;
    uint32_t got_n = 0;
    rc = cs_v5_read_per_channel_2d_file(fp, &hdr, dst, N, &got_n);
    ASSERT_EQ_INT(rc, 0, "pc read 2D rc");
    ASSERT_EQ_U32(got_n, N, "pc 2D n_plies_out");
    ASSERT_EQ_INT(hdr.encoding_mode, CS_V5_MODE_PER_CHANNEL, "pc 2D mode");
    ASSERT_EQ_U32(hdr.n_dimensions, 2u, "pc 2D n_dimensions");

    g_assertions++;
    if (memcmp(src, dst, total) != 0) {
        fprintf(stderr, "  FAIL pc 2D frame bytes mismatch\n");
        g_fails++;
    }

    free(src); free(dst); fclose(fp);
}

static void test_pc_2d_zero_delta_frames(void) {
    /* 3 frames, all identical encoding. Frame 0 is FULL; frames 1+2
     * should encode 0 channels. Round-trip must reconstruct all frames
     * byte-exact. */
    const uint32_t N = 3u;
    const size_t fs = (size_t)CS_V5_FRAME_BYTES_2D;
    const size_t total = fs * (size_t)N;
    uint8_t *src = (uint8_t *)calloc(total, 1);
    g_assertions++;
    if (!src) { g_fails++; return; }

    for (uint32_t k = 0; k < N; ++k) {
        uint8_t *f = src + (size_t)k * fs;
        for (uint32_t c = 0; c < CS_V5_N_CHANNELS_2D; ++c) {
            _set_channel(f, c, (uint8_t)(0x10u + c));
        }
        /* Move tails differ — those don't participate in delta logic. */
        _set_2d_move_tail(f, k, (uint8_t)k, (uint8_t)(k + 16u), 0u, 0u);
    }

    FILE *fp = tmpfile();
    if (!fp) { g_assertions++; g_fails++; free(src); return; }
    int rc = cs_v5_write_per_channel_2d_file(fp, src, N);
    ASSERT_EQ_INT(rc, 0, "pc zero-delta write rc");

    rewind(fp);
    uint8_t *dst = (uint8_t *)calloc(total, 1);
    cs_v5_header_t hdr;
    uint32_t got_n = 0;
    rc = cs_v5_read_per_channel_2d_file(fp, &hdr, dst, N, &got_n);
    ASSERT_EQ_INT(rc, 0, "pc zero-delta read rc");
    ASSERT_EQ_U32(got_n, N, "pc zero-delta n_plies");
    g_assertions++;
    if (memcmp(src, dst, total) != 0) {
        fprintf(stderr, "  FAIL pc zero-delta bytes mismatch\n");
        g_fails++;
    }
    free(src); free(dst); fclose(fp);
}

static void test_pc_2d_all_channels_change(void) {
    /* 2 frames, every channel changed in frame 1. n_present should be
     * CS_V5_N_CHANNELS_2D for both frames (frame 0 = FULL, frame 1 =
     * full delta). Round-trip must still be byte-exact. */
    const uint32_t N = 2u;
    const size_t fs = (size_t)CS_V5_FRAME_BYTES_2D;
    const size_t total = fs * (size_t)N;
    uint8_t *src = (uint8_t *)calloc(total, 1);
    g_assertions++;
    if (!src) { g_fails++; return; }

    /* Frame 0 = all 0xAA. Frame 1 = all 0xBB. */
    memset(src, 0xAA, fs - 8u);
    _set_2d_move_tail(src, 0u, 0u, 0u, 0u, 0u);
    memset(src + fs, 0xBB, fs - 8u);
    _set_2d_move_tail(src + fs, 1u, 1u, 1u, 0u, 0u);

    FILE *fp = tmpfile();
    if (!fp) { g_assertions++; g_fails++; free(src); return; }
    int rc = cs_v5_write_per_channel_2d_file(fp, src, N);
    ASSERT_EQ_INT(rc, 0, "pc all-change write rc");
    rewind(fp);

    uint8_t *dst = (uint8_t *)calloc(total, 1);
    cs_v5_header_t hdr;
    uint32_t got_n = 0;
    rc = cs_v5_read_per_channel_2d_file(fp, &hdr, dst, N, &got_n);
    ASSERT_EQ_INT(rc, 0, "pc all-change read rc");
    ASSERT_EQ_U32(got_n, N, "pc all-change n_plies");
    g_assertions++;
    if (memcmp(src, dst, total) != 0) {
        fprintf(stderr, "  FAIL pc all-change bytes mismatch\n");
        g_fails++;
    }
    free(src); free(dst); fclose(fp);
}

static void test_pc_4d_single_frame(void) {
    /* 1 frame for 4D: full block with 11 channels × 4096 dim float32 +
     * 14-byte move tail. Just check the round-trip works at 4D
     * dimensions. */
    const uint32_t N = 1u;
    const size_t fs = (size_t)CS_V5_FRAME_BYTES_4D;
    uint8_t *src = (uint8_t *)malloc(fs);
    g_assertions++;
    if (!src) { g_fails++; return; }
    /* Distinct deterministic pattern in each byte. */
    for (size_t i = 0; i < fs; ++i) src[i] = (uint8_t)((i * 19u + 3u) & 0xFFu);

    FILE *fp = tmpfile();
    if (!fp) { g_assertions++; g_fails++; free(src); return; }
    int rc = cs_v5_write_per_channel_4d_file(fp, src, N);
    ASSERT_EQ_INT(rc, 0, "pc 4D write rc");
    rewind(fp);

    uint8_t *dst = (uint8_t *)malloc(fs);
    cs_v5_header_t hdr;
    uint32_t got_n = 0;
    rc = cs_v5_read_per_channel_4d_file(fp, &hdr, dst, N, &got_n);
    ASSERT_EQ_INT(rc, 0, "pc 4D read rc");
    ASSERT_EQ_U32(got_n, N, "pc 4D n_plies");
    ASSERT_EQ_U32(hdr.encoding_dim, CS_V5_ENCODING_DIM_4D, "pc 4D encoding_dim");
    ASSERT_EQ_U32(hdr.n_dimensions, 4u, "pc 4D n_dimensions");
    ASSERT_EQ_INT(hdr.encoding_mode, CS_V5_MODE_PER_CHANNEL, "pc 4D mode");
    g_assertions++;
    if (memcmp(src, dst, fs) != 0) {
        fprintf(stderr, "  FAIL pc 4D bytes mismatch\n");
        g_fails++;
    }
    free(src); free(dst); fclose(fp);
}

static void test_pc_2d_reader_rejects_dense_file(void) {
    /* A mode-0 (dense) 2D file should be rejected by the mode-1
     * reader with -8 (mode mismatch). */
    FILE *fp = tmpfile();
    if (!fp) { g_assertions++; g_fails++; return; }
    int rc = cs_v5_write_dense_2d_file(fp, NULL, 0u);
    ASSERT_EQ_INT(rc, 0, "write dense-empty rc");
    rewind(fp);

    cs_v5_header_t hdr;
    uint32_t got_n = 0;
    rc = cs_v5_read_per_channel_2d_file(fp, &hdr, NULL, 0u, &got_n);
    ASSERT_EQ_INT(rc, -8, "pc 2D reader rejects dense");
    fclose(fp);
}

/* ---- XOR-stream (mode 2) full-file I/O round-trips -------------- *
 *
 * Mode 2 is fixed-frame-size (same layout as dense). The transform is
 * applied at write/read time: frame 0 stored verbatim, frame N>0
 * stored bytes = real[N].encoding XOR real[N-1].encoding (move tail
 * unchanged). Round-trip must be byte-exact even for adversarial
 * inputs (e.g. NaN bit patterns produced by XOR).
 */

static void test_xor_2d_round_trip_progressive(void) {
    /* 4 frames: each frame's encoding equals the previous + a known
     * delta in some bytes. XOR transform compresses well in real life;
     * here we just verify byte-exact reconstruction. */
    const uint32_t N = 4u;
    const size_t fs = (size_t)CS_V5_FRAME_BYTES_2D;
    const size_t total = fs * (size_t)N;
    uint8_t *src = (uint8_t *)calloc(total, 1);
    g_assertions++;
    if (!src) { g_fails++; return; }

    /* Frame 0: encoding = repeating 0x55, tail = 0. */
    memset(src, 0x55, fs - 8u);
    _set_2d_move_tail(src, 0u, 0u, 0u, 0u, 0u);
    /* Frames 1..3: clone previous, mutate first 16 bytes of encoding. */
    for (uint32_t k = 1; k < N; ++k) {
        uint8_t *f = src + (size_t)k * fs;
        memcpy(f, src + (size_t)(k - 1) * fs, fs);
        for (uint32_t b = 0; b < 16u; ++b) f[b] = (uint8_t)(0x10u * k + b);
        _set_2d_move_tail(f, k, (uint8_t)k, (uint8_t)(k + 8u), 0u, 0u);
    }

    FILE *fp = tmpfile();
    if (!fp) { g_assertions++; g_fails++; free(src); return; }
    int rc = cs_v5_write_xor_stream_2d_file(fp, src, N);
    ASSERT_EQ_INT(rc, 0, "xor 2D write rc");
    rewind(fp);

    uint8_t *dst = (uint8_t *)calloc(total, 1);
    if (!dst) { g_assertions++; g_fails++; free(src); fclose(fp); return; }
    cs_v5_header_t hdr;
    uint32_t got_n = 0;
    rc = cs_v5_read_xor_stream_2d_file(fp, &hdr, dst, N, &got_n);
    ASSERT_EQ_INT(rc, 0, "xor 2D read rc");
    ASSERT_EQ_U32(got_n, N, "xor 2D got_n");
    ASSERT_EQ_INT(hdr.encoding_mode, CS_V5_MODE_XOR_STREAM, "xor 2D mode");
    ASSERT_EQ_U32(hdr.n_dimensions, 2u, "xor 2D n_dimensions");
    g_assertions++;
    if (memcmp(src, dst, total) != 0) {
        fprintf(stderr, "  FAIL xor 2D bytes mismatch\n");
        g_fails++;
    }
    free(src); free(dst); fclose(fp);
}

static void test_xor_2d_zero_delta_compression_invariant(void) {
    /* 3 IDENTICAL frames (only ply differs). After XOR, frames 1+2
     * should have all-zero encoding bytes on disk. We don't directly
     * peek at the on-disk bytes here, but we verify the round-trip
     * produces the original input — combined with the dense-frame test
     * above, that establishes XOR + un-XOR == identity. */
    const uint32_t N = 3u;
    const size_t fs = (size_t)CS_V5_FRAME_BYTES_2D;
    const size_t total = fs * (size_t)N;
    uint8_t *src = (uint8_t *)calloc(total, 1);
    g_assertions++;
    if (!src) { g_fails++; return; }

    for (uint32_t k = 0; k < N; ++k) {
        uint8_t *f = src + (size_t)k * fs;
        for (size_t b = 0; b < fs - 8u; ++b) f[b] = (uint8_t)(b & 0xFFu);
        _set_2d_move_tail(f, k, (uint8_t)k, (uint8_t)(k + 1u), 0u, 0u);
    }

    FILE *fp = tmpfile();
    if (!fp) { g_assertions++; g_fails++; free(src); return; }
    int rc = cs_v5_write_xor_stream_2d_file(fp, src, N);
    ASSERT_EQ_INT(rc, 0, "xor zero-delta write rc");
    rewind(fp);

    uint8_t *dst = (uint8_t *)calloc(total, 1);
    cs_v5_header_t hdr;
    uint32_t got_n = 0;
    rc = cs_v5_read_xor_stream_2d_file(fp, &hdr, dst, N, &got_n);
    ASSERT_EQ_INT(rc, 0, "xor zero-delta read rc");
    g_assertions++;
    if (memcmp(src, dst, total) != 0) {
        fprintf(stderr, "  FAIL xor zero-delta bytes mismatch\n");
        g_fails++;
    }
    free(src); free(dst); fclose(fp);
}

static void test_xor_2d_disk_layout_for_zero_delta(void) {
    /* Direct on-disk inspection: for two identical frames, the second
     * frame's stored ENCODING bytes (offset 256 + frame_bytes ..
     * 256 + frame_bytes + enc_bytes) must be all zero. Move tail bytes
     * are unaffected by XOR and remain whatever the writer received. */
    const uint32_t N = 2u;
    const size_t fs = (size_t)CS_V5_FRAME_BYTES_2D;
    const size_t total = fs * (size_t)N;
    const size_t enc_bytes = (size_t)CS_V5_ENCODING_DIM_2D * 4u;
    uint8_t *src = (uint8_t *)calloc(total, 1);
    g_assertions++;
    if (!src) { g_fails++; return; }

    /* Frame 0 and frame 1 have identical encoding portions, distinct
     * move tails. */
    for (size_t b = 0; b < enc_bytes; ++b) src[b] = (uint8_t)((b * 11) & 0xFFu);
    memcpy(src + fs, src, enc_bytes);  /* frame 1 encoding = frame 0 */
    _set_2d_move_tail(src, 0u, 1u, 2u, 0u, 0u);
    _set_2d_move_tail(src + fs, 1u, 3u, 4u, 0u, 0u);

    FILE *fp = tmpfile();
    if (!fp) { g_assertions++; g_fails++; free(src); return; }
    int rc = cs_v5_write_xor_stream_2d_file(fp, src, N);
    ASSERT_EQ_INT(rc, 0, "xor disk-layout write rc");

    /* Read raw bytes back from disk for inspection. */
    rewind(fp);
    uint8_t *raw = (uint8_t *)calloc((size_t)CS_V5_HEADER_SIZE + total, 1);
    if (!raw) { g_assertions++; g_fails++; free(src); fclose(fp); return; }
    size_t r = fread(raw, 1, (size_t)CS_V5_HEADER_SIZE + total, fp);
    ASSERT_EQ_INT((int)r, (int)((size_t)CS_V5_HEADER_SIZE + total),
                  "xor disk-layout read raw bytes");

    /* Frame 1 stored encoding starts at offset CS_V5_HEADER_SIZE + fs. */
    const uint8_t *f1_enc = raw + CS_V5_HEADER_SIZE + fs;
    int all_zero = 1;
    for (size_t b = 0; b < enc_bytes; ++b) {
        if (f1_enc[b] != 0u) { all_zero = 0; break; }
    }
    g_assertions++;
    if (!all_zero) {
        fprintf(stderr, "  FAIL xor zero-delta did not produce zero bytes on disk\n");
        g_fails++;
    }

    free(src); free(raw); fclose(fp);
}

static void test_xor_4d_single_frame(void) {
    /* 1 frame for 4D: stored verbatim (XOR with zero). Round-trip
     * should produce byte-exact equality. */
    const uint32_t N = 1u;
    const size_t fs = (size_t)CS_V5_FRAME_BYTES_4D;
    uint8_t *src = (uint8_t *)malloc(fs);
    g_assertions++;
    if (!src) { g_fails++; return; }
    for (size_t i = 0; i < fs; ++i) src[i] = (uint8_t)((i * 23u + 5u) & 0xFFu);

    FILE *fp = tmpfile();
    if (!fp) { g_assertions++; g_fails++; free(src); return; }
    int rc = cs_v5_write_xor_stream_4d_file(fp, src, N);
    ASSERT_EQ_INT(rc, 0, "xor 4D write rc");
    rewind(fp);

    uint8_t *dst = (uint8_t *)malloc(fs);
    cs_v5_header_t hdr;
    uint32_t got_n = 0;
    rc = cs_v5_read_xor_stream_4d_file(fp, &hdr, dst, N, &got_n);
    ASSERT_EQ_INT(rc, 0, "xor 4D read rc");
    ASSERT_EQ_U32(got_n, N, "xor 4D got_n");
    ASSERT_EQ_U32(hdr.encoding_dim, CS_V5_ENCODING_DIM_4D, "xor 4D encoding_dim");
    ASSERT_EQ_U32(hdr.n_dimensions, 4u, "xor 4D n_dimensions");
    ASSERT_EQ_INT(hdr.encoding_mode, CS_V5_MODE_XOR_STREAM, "xor 4D mode");
    g_assertions++;
    if (memcmp(src, dst, fs) != 0) {
        fprintf(stderr, "  FAIL xor 4D bytes mismatch\n");
        g_fails++;
    }
    free(src); free(dst); fclose(fp);
}

static void test_xor_2d_reader_rejects_dense_file(void) {
    FILE *fp = tmpfile();
    if (!fp) { g_assertions++; g_fails++; return; }
    int rc = cs_v5_write_dense_2d_file(fp, NULL, 0u);
    ASSERT_EQ_INT(rc, 0, "write dense-empty rc");
    rewind(fp);

    cs_v5_header_t hdr;
    uint32_t got_n = 0;
    rc = cs_v5_read_xor_stream_2d_file(fp, &hdr, NULL, 0u, &got_n);
    ASSERT_EQ_INT(rc, -8, "xor 2D reader rejects dense");
    fclose(fp);
}


static void test_pc_2d_truncates_to_max_plies(void) {
    /* Write 4 plies with progressive single-channel deltas; read with
     * max_plies=2. The reader must reconstruct frames 0..1 correctly
     * (and stop, leaving the rest of the stream unconsumed). */
    const uint32_t N_WRITE = 4u, N_READ = 2u;
    const size_t fs = (size_t)CS_V5_FRAME_BYTES_2D;
    const size_t total_write = fs * (size_t)N_WRITE;
    const size_t total_read = fs * (size_t)N_READ;
    uint8_t *src = (uint8_t *)calloc(total_write, 1);
    g_assertions++;
    if (!src) { g_fails++; return; }

    for (uint32_t k = 0; k < N_WRITE; ++k) {
        uint8_t *f = src + (size_t)k * fs;
        if (k > 0) memcpy(f, src + (size_t)(k - 1) * fs, fs);
        _set_channel(f, k, (uint8_t)(0x50u + k));
        _set_2d_move_tail(f, k, (uint8_t)k, (uint8_t)(k + 1), 0u, 0u);
    }

    FILE *fp = tmpfile();
    if (!fp) { g_assertions++; g_fails++; free(src); return; }
    int rc = cs_v5_write_per_channel_2d_file(fp, src, N_WRITE);
    ASSERT_EQ_INT(rc, 0, "pc trunc write rc");
    rewind(fp);

    uint8_t *dst = (uint8_t *)calloc(total_read, 1);
    cs_v5_header_t hdr;
    uint32_t got_n = 0;
    rc = cs_v5_read_per_channel_2d_file(fp, &hdr, dst, N_READ, &got_n);
    ASSERT_EQ_INT(rc, 0, "pc trunc read rc");
    ASSERT_EQ_U32(got_n, N_READ, "pc trunc got_n");
    /* hdr.n_plies should still report the full file count (4), not 2. */
    ASSERT_EQ_U32(hdr.n_plies, N_WRITE, "pc trunc hdr.n_plies");
    g_assertions++;
    if (memcmp(src, dst, total_read) != 0) {
        fprintf(stderr, "  FAIL pc truncated read bytes mismatch\n");
        g_fails++;
    }
    free(src); free(dst); fclose(fp);
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
    test_pc_2d_round_trip_progressive_deltas();
    test_pc_2d_zero_delta_frames();
    test_pc_2d_all_channels_change();
    test_pc_4d_single_frame();
    test_pc_2d_reader_rejects_dense_file();
    test_pc_2d_truncates_to_max_plies();
    test_xor_2d_round_trip_progressive();
    test_xor_2d_zero_delta_compression_invariant();
    test_xor_2d_disk_layout_for_zero_delta();
    test_xor_4d_single_frame();
    test_xor_2d_reader_rejects_dense_file();

    printf("  %d/%d assertions passed\n",
           g_assertions - g_fails, g_assertions);
    return g_fails == 0 ? 0 : 1;
}
