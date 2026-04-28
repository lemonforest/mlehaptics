/* main_4d.c — `spectral_4d` CLI entry point.
 *
 * Mirrors the 2D `spectral` binary's manual argv strcmp dispatch style
 * (see src/main.c). Subcommands:
 *   version         — print encoder dims + channel layout
 *   help            — usage banner
 *   encode-fixture  — ingest positions_4d.jsonl, emit 45056 float32 LE on stdout
 *   encode-fen4     — encode a FEN4 v1 literal to a single-frame .spectralz4
 *   encode          — [P5] NDJSON4 → .spectralz4 bulk encoding
 *   csv             — [P5] per-ply channel energies
 *
 * The JSONL record schema (produced by codegen/emit_test_vectors_4d.py):
 *   {"name": "<fixture>", "pieces": {"<sq>": "<char>", ...}}
 * where <sq> is the decimal square index (0..4095) and <char> is one of
 * {P,N,B,R,Q,K,p,n,b,r,q,k}. encode-fixture is the parity-test surface;
 * Python shells out to it and compares 45056 float32 against fixtures_4d.npz.
 *
 * encode-fen4 is the v1.2.4 entry point for single-position .spectralz4
 * generation: parse a FEN4 v1 literal (docs/FEN4_FORMAT.md), encode it,
 * and write a one-frame v4 .spectralz4 (optionally gzip-compressed). The
 * Python CLI's encode-fen4 produces byte-identical output.
 */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>
#include "cs_encoder_4d.h"
#include "cs_fen_4d.h"
#include "cs_frame_4d.h"
#include "cs_gzip.h"

#ifdef _WIN32
#  include <io.h>
#  include <fcntl.h>
#endif

/* ─── help / usage ─────────────────────────────────────────────────────── */

static void print_usage(FILE *fp)
{
    fprintf(fp,
        "spectral_4d — 45 056-dim 4D spectral chess encoder (C17, v1.1.1)\n"
        "\n"
        "USAGE:\n"
        "    spectral_4d <command> [options]\n"
        "    spectral_4d --help | -h | -? | /? | help\n"
        "\n"
        "COMMANDS:\n"
        "    version          Print encoder version and dimensions\n"
        "    help             Print this message\n"
        "    encode-fixture   Encode a named fixture from positions_4d.jsonl\n"
        "                         --positions-jsonl <path>   JSONL fixture file\n"
        "                         --name <fixture>           fixture name to encode\n"
        "                     Emits 45056 little-endian float32 (180 224 bytes)\n"
        "                     on stdout. Parity-test entry point.\n"
        "    encode-fen4      Encode a FEN4 v1 literal to a single-frame v4 .spectralz4\n"
        "                         --fen4 <literal>           FEN4 v1 string (see docs/FEN4_FORMAT.md)\n"
        "                         -o, --output <path>        output path (.spectralz4 if -z, else .spectral4)\n"
        "                         -z, --compress             gzip the output (RFC 1952)\n"
        "                     Use '-' as the output path to stream raw bytes to stdout.\n"
        "    encode           NDJSON4 ply-log → v4 .spectralz4 bulk encoder\n"
        "                         -i, --input <path>         NDJSON4 path or '-' for stdin\n"
        "                         -o, --output <path>        output .spectral4 / .spectralz4\n"
        "                         -z, --compress             gzip the output\n"
        "                     Schema: docs/NDJSON4_FORMAT.md\n"
        "    csv              .spectralz4 → per-ply 11-channel energies + dist/cos/dA1 (CSV)\n"
        "                         <input>                    plain or gzipped .spectral4 file\n"
        "                         -o, --output <path>        CSV path (omit for stdout)\n"
        "\n"
        "ENCODING DIMENSIONS (v1.1.1, Oana-Chiru Def. 11 pawn axis split):\n"
        "    11 channels × 4096 board eigenmodes = 45 056 floats per position.\n"
        "        Ch 0     : A_1 orbit-mean                                (dims     0..4095 )\n"
        "        Ch 1-4   : std-4D coord residuals                        (dims  4096..20479)\n"
        "        Ch 5-7   : symmetric 3D cross-piece fiber                (dims 20480..32767)\n"
        "        Ch 8     : antisymmetric pawn fiber, W-axis              (dims 32768..36863)\n"
        "        Ch 9     : antisymmetric pawn fiber, Y-axis (NEW v1.1.1) (dims 36864..40959)\n"
        "        Ch 10    : diagonal deviation (rook shadow)              (dims 40960..45055)\n"
        "\n"
        "EXIT CODES:\n"
        "    0  success\n"
        "    1  usage error / unknown command\n"
        "    2  missing / invalid arguments\n"
        "    3  I/O or parse error during processing\n"
        "    4  command is not yet implemented\n"
    );
}

static int cmd_help(void)    { print_usage(stdout); return 0; }

static int cmd_version(void)
{
    printf("spectral_4d 0.1.0 — encoding_dim=%d channels=%d n_squares=%d\n",
           CS_ENCODING_DIM_4D, CS_N_CHANNELS_4D, CS_N_SQUARES_4D);
    printf("board_side=%d n_dims=%d b4_order=%d n_orbits=%d\n",
           CS_BOARD_SIDE_4D, CS_N_DIMS, CS_B4_ORDER, CS_N_ORBITS_4D);
    return 0;
}

/* (cmd_todo was deleted in v1.2.4 — all advertised commands are now
 * wired. If a new stub is needed in the future, restore this helper
 * from git history; the 2D src/main.c retains the same pattern.) */

/* ─── encode-fixture (parity-test surface) ─────────────────────────────── */

/* Extract the value of a "key":"..." field from a JSON line. Writes into
 * `dst` (dst_size including the NUL). Returns 0 on success, -1 if not
 * found. Tolerates whitespace between ':' and '"' since json.dumps'
 * default output is `"key": "value"` (one space).
 */
static int json_str_field(const char *line, const char *key,
                          char *dst, size_t dst_size)
{
    char needle[64];
    int nk = snprintf(needle, sizeof(needle), "\"%s\":", key);
    if (nk < 0 || (size_t)nk >= sizeof(needle)) return -1;
    const char *p = strstr(line, needle);
    if (!p) return -1;
    p += nk;
    while (*p == ' ' || *p == '\t') p++;
    if (*p != '"') return -1;
    p++;  /* past opening quote */
    const char *q = strchr(p, '"');
    if (!q) return -1;
    size_t n = (size_t)(q - p);
    if (n + 1 > dst_size) n = dst_size - 1;
    memcpy(dst, p, n);
    dst[n] = '\0';
    return 0;
}

/* Find the value of a nested object field — returns pointer to the
 * opening '{' of {"pieces": {...}}, or NULL if not present. Tolerates
 * whitespace between the colon and the '{' (json.dumps' default
 * separator is ", " / ": " which inserts one). */
static const char *json_object_field(const char *line, const char *key)
{
    char needle[64];
    int nk = snprintf(needle, sizeof(needle), "\"%s\":", key);
    if (nk < 0 || (size_t)nk >= sizeof(needle)) return NULL;
    const char *p = strstr(line, needle);
    if (!p) return NULL;
    p += nk;
    while (*p == ' ' || *p == '\t') p++;
    if (*p != '{') return NULL;
    return p;
}

/* Parse {"<square>":"<val>", ...} into pos->sq + pos->pawn_axis.
 *
 * Square keys are decimal strings 0..4095. Values are either:
 *   - 1-char: a single piece letter (NBRQKnbrqk) OR a legacy pawn
 *             ('P'/'p') which defaults to W-axis (matches v1.0 JSONL).
 *   - 2-char: a pawn color + axis, e.g. "Pw", "Py", "pw", "py"
 *             (v1.1.1 per Oana-Chiru Def. 11).
 *
 * Tolerates whitespace (json.dumps' default inserts one space after
 * each `:` and `,`). Returns 0 on success, -1 on any malformed input
 * including an unknown pawn axis letter. Non-pawn chars MUST be
 * 1-char; a 2-char non-pawn value is rejected.
 */
static int parse_pieces_object(const char *obj, cs_position_4d_t *pos)
{
    if (*obj != '{') return -1;
    obj++;  /* past '{' */
    memset(pos->sq, 0, sizeof(pos->sq));
    memset(pos->pawn_axis, CS_PAWN_AXIS_W, sizeof(pos->pawn_axis));

    while (*obj && *obj != '}') {
        while (*obj == ' ' || *obj == '\t' || *obj == ',') obj++;
        if (*obj == '}') break;
        if (*obj != '"') return -1;
        obj++;  /* past opening quote of key */

        long s = 0;
        while (*obj >= '0' && *obj <= '9') { s = s * 10 + (*obj - '0'); obj++; }
        if (*obj != '"') return -1;
        obj++;  /* past closing quote of key */
        while (*obj == ' ' || *obj == '\t') obj++;
        if (*obj != ':') return -1;
        obj++;  /* past ':' */
        while (*obj == ' ' || *obj == '\t') obj++;
        if (*obj != '"') return -1;
        obj++;  /* past opening quote of value */

        if (s < 0 || s >= CS_N_SQUARES_4D) return -1;

        char color = *obj;
        if (color == '\0' || color == '"') return -1;
        obj++;  /* past color char */
        pos->sq[s] = (int8_t)color;

        if (*obj == '"') {
            /* 1-char value: either a non-pawn piece or a legacy pawn
             * (W-axis default, already set by the memset above). */
            obj++;  /* past closing quote */
        } else {
            /* 2-char value: must be a pawn with an explicit axis. */
            if (color != 'P' && color != 'p') return -1;
            char axis = *obj;
            obj++;  /* past axis char */
            if (*obj != '"') return -1;
            obj++;  /* past closing quote */
            if (axis == 'w') {
                pos->pawn_axis[s] = CS_PAWN_AXIS_W;
            } else if (axis == 'y') {
                pos->pawn_axis[s] = CS_PAWN_AXIS_Y;
            } else {
                /* Oana-Chiru Def. 11 forbids z-axis pawns; reject
                 * anything that isn't 'w' or 'y' rather than silently
                 * falling back to W. */
                return -1;
            }
        }
    }
    return 0;
}

static int cmd_encode_fixture(int argc, char **argv)
{
    const char *jsonl_path = NULL;
    const char *name       = NULL;
    int repeat             = 1;
    for (int i = 0; i < argc; i++) {
        if (strcmp(argv[i], "--positions-jsonl") == 0 && i + 1 < argc) {
            jsonl_path = argv[++i];
        } else if (strcmp(argv[i], "--name") == 0 && i + 1 < argc) {
            name = argv[++i];
        } else if (strcmp(argv[i], "--repeat") == 0 && i + 1 < argc) {
            /* Benchmark-only: run cs_encode_4d N times, emit only the
             * last result. Lets callers amortize subprocess startup over
             * many encodes without writing N * 163 840 bytes to stdout. */
            repeat = atoi(argv[++i]);
            if (repeat < 1) repeat = 1;
        }
    }
    if (!jsonl_path) {
        fprintf(stderr, "encode-fixture: missing --positions-jsonl <path>\n");
        return 2;
    }
    if (!name) {
        fprintf(stderr, "encode-fixture: missing --name <fixture>\n");
        return 2;
    }

    FILE *fin = fopen(jsonl_path, "r");
    if (!fin) {
        fprintf(stderr, "encode-fixture: cannot open %s\n", jsonl_path);
        return 3;
    }

    /* JSONL lines: find the one with matching "name". Lines can be long
     * (the 12-piece fixture is ~300 bytes); 4 KiB is ample for v1.1.   */
    char line[4096];
    cs_position_4d_t pos = {0};  /* defaults pawn_axis[] to CS_PAWN_AXIS_W */
    int found = 0;
    while (fgets(line, sizeof(line), fin)) {
        char got[64];
        if (json_str_field(line, "name", got, sizeof(got)) != 0) continue;
        if (strcmp(got, name) != 0) continue;
        const char *obj = json_object_field(line, "pieces");
        if (!obj) {
            fprintf(stderr, "encode-fixture: %s has no \"pieces\" object\n", name);
            fclose(fin);
            return 3;
        }
        if (parse_pieces_object(obj, &pos) != 0) {
            fprintf(stderr, "encode-fixture: malformed pieces object for %s\n", name);
            fclose(fin);
            return 3;
        }
        found = 1;
        break;
    }
    fclose(fin);

    if (!found) {
        fprintf(stderr, "encode-fixture: fixture '%s' not found in %s\n",
                name, jsonl_path);
        return 3;
    }

    cs_encoding_4d_t enc;
    for (int r = 0; r < repeat; r++) {
        cs_encode_4d(&pos, &enc);
    }

#ifdef _WIN32
    /* Switch stdout to binary so \n doesn't mangle 0x0A bytes in the
     * float32 stream. POSIX is binary-by-default, so this is a no-op
     * elsewhere. */
    _setmode(_fileno(stdout), _O_BINARY);
#endif

    size_t nfloats = CS_ENCODING_DIM_4D;
    size_t written = fwrite(enc.v, sizeof(float), nfloats, stdout);
    fflush(stdout);
    if (written != nfloats) {
        fprintf(stderr, "encode-fixture: short write (%zu of %zu floats)\n",
                written, nfloats);
        return 3;
    }
    return 0;
}

/* ─── JSON field helpers (NDJSON4 ply-log) ─────────────────────────────── */

/* Find "key": and return a pointer to the byte after the colon (and
 * any whitespace). NULL if not found. */
static const char *json_find_field(const char *line, const char *key)
{
    char needle[64];
    int nk = snprintf(needle, sizeof(needle), "\"%s\":", key);
    if (nk < 0 || (size_t)nk >= sizeof(needle)) return NULL;
    const char *p = strstr(line, needle);
    if (!p) return NULL;
    p += nk;
    while (*p == ' ' || *p == '\t') p++;
    return p;
}

/* Extract "key":"<value>" into dst. dst_size includes NUL. Returns:
 *    0  success
 *   -1  key not found, or value isn't a string
 *   -2  value would overflow dst (length excluding NUL >= dst_size)
 *
 * Pre-1.3.2 the overflow case silently truncated and returned 0,
 * which converted "FEN4 too long" failures into "FEN4 has bad
 * coordinate" errors downstream — the user spent time bisecting
 * coord values for what was really a buffer-size issue. The new
 * -2 return makes the failure mode explicit. */
static int json_str_field4(const char *line, const char *key,
                           char *dst, size_t dst_size)
{
    const char *p = json_find_field(line, key);
    if (!p || *p != '"') return -1;
    p++;  /* past opening quote */
    /* Walk until unescaped closing quote. FEN4 strings contain no
     * backslashes, so a simple scan suffices. */
    const char *q = p;
    while (*q && *q != '"') q++;
    if (*q != '"') return -1;
    size_t n = (size_t)(q - p);
    if (n + 1 > dst_size) return -2;  /* explicit overflow signal */
    memcpy(dst, p, n);
    dst[n] = '\0';
    return 0;
}

/* Extract "key":N where N is a non-negative integer. Returns 0 on
 * success, -1 if not found or value isn't an integer literal. */
static int json_int_field4(const char *line, const char *key, int *out)
{
    const char *p = json_find_field(line, key);
    if (!p) return -1;
    if (*p == '"') return -1;
    if (*p == '-' || (*p >= '0' && *p <= '9')) {
        *out = atoi(p);
        return 0;
    }
    return -1;
}

/* Extract "key":[a,b,c,d] as 4 ints. Returns 0 on success, -1
 * otherwise. Tolerates whitespace inside the brackets. */
static int json_int_array4_field(const char *line, const char *key,
                                 int out[4])
{
    const char *p = json_find_field(line, key);
    if (!p || *p != '[') return -1;
    p++;
    for (int i = 0; i < 4; i++) {
        while (*p == ' ' || *p == '\t') p++;
        if (*p != '-' && (*p < '0' || *p > '9')) return -1;
        out[i] = atoi(p);
        while (*p == '-' || (*p >= '0' && *p <= '9')) p++;
        while (*p == ' ' || *p == '\t') p++;
        if (i < 3) {
            if (*p != ',') return -1;
            p++;
        }
    }
    if (*p != ']') return -1;
    return 0;
}

/* ─── encode-fen4 (single-position .spectralz4 writer) ─────────────────── */

static int write_one_frame(FILE *fp, const cs_encoding_4d_t *enc)
{
    cs_spectral_frame_4d_t fr;
    memset(&fr, 0, sizeof(fr));
    /* Encoding is a fixed-size float32 array; copy in. */
    memcpy(fr.encoding, enc->v, sizeof(enc->v));
    /* ply / from / to / promo / flags all zero for a single-position
     * write — there's no move history to record. */
    return cs_file_4d_write_frame(fp, &fr);
}

static int cmd_encode_fen4(int argc, char **argv)
{
    const char *fen4   = NULL;
    const char *output = NULL;
    int compress = 0;

    for (int i = 0; i < argc; i++) {
        if ((strcmp(argv[i], "--fen4") == 0
             || strcmp(argv[i], "--fen") == 0) && i + 1 < argc) {
            fen4 = argv[++i];
        } else if ((strcmp(argv[i], "-o") == 0
                    || strcmp(argv[i], "--output") == 0) && i + 1 < argc) {
            output = argv[++i];
        } else if (strcmp(argv[i], "-z") == 0
                   || strcmp(argv[i], "--compress") == 0) {
            compress = 1;
        }
    }

    if (!fen4) {
        fprintf(stderr, "encode-fen4: missing --fen4 <literal>\n");
        return 2;
    }

    cs_position_4d_t pos;
    int rc = cs_fen_4d_parse(fen4, &pos);
    if (rc != 0) {
        fprintf(stderr, "encode-fen4: FEN4 parse error %d\n", rc);
        return 3;
    }

    cs_encoding_4d_t enc;
    cs_encode_4d(&pos, &enc);

    cs_file_header_4d_t hdr;
    cs_file_4d_header_init(&hdr);
    hdr.n_plies = 1u;

    /* Writing strategy:
     *   - If !compress and output is "-" or NULL: raw bytes to stdout
     *     (binary mode on Windows).
     *   - If !compress and output is a path: write directly.
     *   - If compress: write to a tmpfile, then gzip-compress to the
     *     target path. Stdout output with -z is rejected (would need a
     *     stream-gzip path that cs_gzip doesn't currently expose).
     */
    if (compress) {
        if (!output || strcmp(output, "-") == 0) {
            fprintf(stderr, "encode-fen4: -z requires --output <path>; "
                    "cannot gzip-stream to stdout\n");
            return 2;
        }
        FILE *tmp = tmpfile();
        if (!tmp) {
            fprintf(stderr, "encode-fen4: tmpfile() failed\n");
            return 3;
        }
        if (cs_file_4d_write_header(tmp, &hdr) != 0
            || write_one_frame(tmp, &enc) != 0) {
            fprintf(stderr, "encode-fen4: write to tmpfile failed\n");
            fclose(tmp);
            return 3;
        }
        if (cs_file_write_gzip(output, tmp) != 0) {
            fprintf(stderr, "encode-fen4: gzip to %s failed\n", output);
            fclose(tmp);
            return 3;
        }
        fclose(tmp);
    } else {
        FILE *fp = NULL;
        int close_fp = 0;
        if (!output || strcmp(output, "-") == 0) {
#ifdef _WIN32
            _setmode(_fileno(stdout), _O_BINARY);
#endif
            fp = stdout;
        } else {
            fp = fopen(output, "wb");
            if (!fp) {
                fprintf(stderr, "encode-fen4: cannot open %s for write\n",
                        output);
                return 3;
            }
            close_fp = 1;
        }
        if (cs_file_4d_write_header(fp, &hdr) != 0
            || write_one_frame(fp, &enc) != 0) {
            fprintf(stderr, "encode-fen4: write failed\n");
            if (close_fp) fclose(fp);
            return 3;
        }
        fflush(fp);
        if (close_fp) fclose(fp);
    }
    return 0;
}

/* ─── encode (NDJSON4 → .spectralz4 bulk) ──────────────────────────────── */

/* Per [AUDIT_2026-04.md F-11], the cs_encoding_4d_t and
 * cs_spectral_frame_4d_t are hoisted outside the per-ply loop to avoid
 * the 180 KiB stack-frame churn at -O0. */
static int cmd_encode(int argc, char **argv)
{
    const char *input  = NULL;
    const char *output = NULL;
    int compress = 0;

    for (int i = 0; i < argc; i++) {
        if ((strcmp(argv[i], "-i") == 0
             || strcmp(argv[i], "--input") == 0) && i + 1 < argc) {
            input = argv[++i];
        } else if ((strcmp(argv[i], "-o") == 0
                    || strcmp(argv[i], "--output") == 0) && i + 1 < argc) {
            output = argv[++i];
        } else if (strcmp(argv[i], "-z") == 0
                   || strcmp(argv[i], "--compress") == 0) {
            compress = 1;
        } else if (argv[i][0] != '-' && !input) {
            /* Positional input path (matches 2D `spectral encode FILE` style). */
            input = argv[i];
        }
    }

    if (!input) {
        fprintf(stderr, "encode: missing input NDJSON4 path "
                "(use -i <path> or positional)\n");
        return 2;
    }
    if (!output) {
        fprintf(stderr, "encode: missing -o <output>\n");
        return 2;
    }

    FILE *fin = (strcmp(input, "-") == 0) ? stdin : fopen(input, "rb");
    if (!fin) {
        fprintf(stderr, "encode: cannot open %s\n", input);
        return 3;
    }

    /* When compressing, write plain frames to a tmpfile (so header
     * backfill via fseek still works), then deflate to the user's
     * output path. Mirrors the 2D pattern at src/main.c:427-432. */
    FILE *fout = compress ? tmpfile() : fopen(output, "wb");
    if (!fout) {
        if (fin != stdin) fclose(fin);
        fprintf(stderr, "encode: cannot create %s\n",
                compress ? "tmpfile" : output);
        return 3;
    }

    cs_file_header_4d_t hdr;
    cs_file_4d_header_init(&hdr);
    if (cs_file_4d_write_header(fout, &hdr) != 0) {
        if (fin != stdin) fclose(fin);
        fclose(fout);
        fprintf(stderr, "encode: header write failed\n");
        return 3;
    }

    /* Hoisted per F-11. cs_spectral_frame_4d_t is ~180 KiB; allocate
     * once. cs_position_4d_t is fully overwritten each iteration by
     * cs_fen_4d_parse(). */
    cs_position_4d_t pos;
    cs_encoding_4d_t enc;
    cs_spectral_frame_4d_t fr;

    /* Heap-allocated line buffer + FEN4 buffer. Both have to be
     * large enough to hold the worst-case full-board 4D position:
     *
     *   FEN4 string for 4096 occupied squares with short piece
     *   records (e.g. "R@7,7,7,7", 9 chars) plus separators ≈ 45 KiB;
     *   with longer pawn records ("Pw@7,7,7,7", 11 chars) ≈ 55 KiB.
     *
     *   The wrapping NDJSON line is the FEN4 plus JSON envelope:
     *   {"ply":N,"fen4":"<...>","move_from":[...],...}
     *   ≈ FEN4 size + ~200 bytes of metadata.
     *
     * Sizes chosen with ~10 KiB headroom each for future format
     * additions (extra piece flags, longer piece-axis names, etc.).
     *
     * Pre-1.3.2 these were 8 KiB and 2 KiB stack buffers; the FEN4
     * buffer's silent truncation produced misleading "bad coord"
     * errors on real chess4d corpora. Heap-allocated so we don't
     * push the function's stack frame past Windows' default
     * thread-stack limit (cs_spectral_frame_4d_t is already
     * ~180 KiB on the stack for `fr`).
     *
     * IMPORTANT: every `return` after this point MUST free both
     * buffers or they leak. There are exactly two: the gzip-failure
     * path and the normal success path; both are inline below. If
     * you add a new return between the malloc and the function's
     * end, free both buffers first. */
    enum { LINE_BUF_SIZE = 80 * 1024, FEN4_BUF_SIZE = 64 * 1024 };
    char *buf  = (char *)malloc(LINE_BUF_SIZE);
    char *fen4 = (char *)malloc(FEN4_BUF_SIZE);
    if (!buf || !fen4) {
        free(buf);
        free(fen4);
        if (fin != stdin) fclose(fin);
        fclose(fout);
        fprintf(stderr, "encode: out of memory allocating line/FEN4 "
                        "buffers (need %d + %d KiB)\n",
                LINE_BUF_SIZE / 1024, FEN4_BUF_SIZE / 1024);
        return 3;
    }

    uint32_t n_plies = 0;
    uint32_t line_no = 0;

    while (fgets(buf, LINE_BUF_SIZE, fin)) {
        line_no++;
        if (strstr(buf, "bridge_version")) continue;

        int rc = json_str_field4(buf, "fen4", fen4, FEN4_BUF_SIZE);
        if (rc == -2) {
            /* Buffer overflow — surface a clearer error than the
             * downstream FEN4 parser's "bad coord" we'd otherwise
             * get from a half-truncated string. */
            fprintf(stderr,
                "encode: line %u: FEN4 string longer than %d KiB; "
                "rebuild with a larger FEN4_BUF_SIZE in cmd_encode "
                "(src/main_4d.c) if your corpus genuinely needs it\n",
                line_no, FEN4_BUF_SIZE / 1024);
            continue;
        }
        if (rc != 0) continue;  /* key not found, line is metadata */

        rc = cs_fen_4d_parse(fen4, &pos);
        if (rc != 0) {
            fprintf(stderr, "encode: FEN4 parse error %d at line %u\n",
                    rc, line_no);
            continue;
        }

        cs_encode_4d(&pos, &enc);

        /* Frame layout: zero metadata fields, copy encoding, then
         * overlay any move metadata from the JSON line. */
        memset(&fr, 0, sizeof(fr));
        memcpy(fr.encoding, enc.v, sizeof(enc.v));

        int ply = -1;
        (void)json_int_field4(buf, "ply", &ply);
        fr.ply = (uint32_t)(ply >= 0 ? ply : (int)n_plies);

        int from4[4] = {0,0,0,0};
        if (json_int_array4_field(buf, "move_from", from4) == 0) {
            fr.from_x = (uint8_t)(from4[0] & 0xFF);
            fr.from_y = (uint8_t)(from4[1] & 0xFF);
            fr.from_z = (uint8_t)(from4[2] & 0xFF);
            fr.from_w = (uint8_t)(from4[3] & 0xFF);
        }
        int to4[4] = {0,0,0,0};
        if (json_int_array4_field(buf, "move_to", to4) == 0) {
            fr.to_x = (uint8_t)(to4[0] & 0xFF);
            fr.to_y = (uint8_t)(to4[1] & 0xFF);
            fr.to_z = (uint8_t)(to4[2] & 0xFF);
            fr.to_w = (uint8_t)(to4[3] & 0xFF);
        }
        int promo = 0, flags = 0;
        (void)json_int_field4(buf, "promo", &promo);
        (void)json_int_field4(buf, "flags", &flags);
        fr.promo = (uint8_t)(promo & 0xFF);
        fr.flags = (uint8_t)(flags & 0xFF);

        if (cs_file_4d_write_frame(fout, &fr) != 0) {
            fprintf(stderr, "encode: frame write failed at ply %u\n",
                    fr.ply);
            break;
        }
        n_plies++;
    }

    /* Backfill n_plies in the header. */
    hdr.n_plies = n_plies;
    if (cs_file_4d_write_header(fout, &hdr) != 0) {
        fprintf(stderr, "encode: header backfill failed\n");
    }

    if (fin != stdin) fclose(fin);

    if (compress) {
        if (cs_file_write_gzip(output, fout) != 0) {
            fprintf(stderr, "encode: gzip to %s failed\n", output);
            fclose(fout);
            free(fen4);
            free(buf);
            return 3;
        }
    }
    fclose(fout);

    if (n_plies == 0) {
        fprintf(stderr, "encode: warning — no plies written "
                "(empty input or all FEN4 parse errors)\n");
    }
    free(fen4);
    free(buf);
    return 0;
}

/* ─── csv (per-ply 11-channel energies) ────────────────────────────────── */

/* Channel layout (matches help text and frame_4d.py):
 *   0       : A1            (dims 0       .. 4095)
 *   1-4     : STD4_X..W     (dims 4096    .. 20479)
 *   5-7     : FIB_SYM_1..3  (dims 20480   .. 32767)
 *   8       : FA_PAWN_W     (dims 32768   .. 36863)
 *   9       : FA_PAWN_Y     (dims 36864   .. 40959)
 *   10      : FD_DIAG       (dims 40960   .. 45055)
 */
#define CS_N_CSV_CHANNELS_4D 11
static const char *const CSV_CHAN_NAMES_4D[CS_N_CSV_CHANNELS_4D] = {
    "A1", "STD4_X", "STD4_Y", "STD4_Z", "STD4_W",
    "FIB_SYM_1", "FIB_SYM_2", "FIB_SYM_3",
    "FA_PAWN_W", "FA_PAWN_Y", "FD_DIAG",
};
#define CS_BLOCK_4D 4096

static double sum_sq_f4(const float *v, int n)
{
    double s = 0.0;
    for (int i = 0; i < n; i++) { double x = (double)v[i]; s += x * x; }
    return s;
}

/* Same chat-friendly formatter as 2D's fmt_csv_num — see
 * src/main.c:565-584 for the rationale. */
static void fmt_csv_num4(FILE *fp, double x)
{
    double ax = x < 0 ? -x : x;
    if (ax < 1e-6)      { fputc('0', fp); return; }
    if (ax >= 100.0)    { fprintf(fp, "%.0f", x); return; }
    if (ax >= 1.0)      { fprintf(fp, "%.2f", x); return; }
    if (ax >= 0.01)     { fprintf(fp, "%.3f", x); return; }
    fprintf(fp, "%.2e", x);
}

static void fmt_csv_cos4(FILE *fp, double x)
{
    fprintf(fp, "%.4f", x);
}

static int cmd_csv(int argc, char **argv)
{
    const char *input  = NULL;
    const char *output = NULL;
    for (int i = 0; i < argc; i++) {
        if ((strcmp(argv[i], "-o") == 0
             || strcmp(argv[i], "--output") == 0) && i + 1 < argc) {
            output = argv[++i];
        } else if (argv[i][0] != '-' && !input) {
            input = argv[i];
        }
    }
    if (!input) {
        fprintf(stderr,
            "csv: missing input file.\n"
            "    spectral_4d csv <game.spectralz4> [-o out.csv]\n"
            "    (omit -o or pass -o - to write CSV to stdout)\n");
        return 2;
    }

    FILE *fin = NULL;
    if (cs_open_read_transparent(input, &fin) != 0 || !fin) {
        fprintf(stderr, "csv: cannot open %s (or bad gzip)\n", input);
        return 3;
    }

    cs_file_header_4d_t hdr;
    if (cs_file_4d_read_header(fin, &hdr) != 0) {
        fprintf(stderr,
            "csv: %s is not a valid v3/v4 .spectralz4 file\n", input);
        fclose(fin);
        return 3;
    }

    FILE *fout = stdout;
    int close_fout = 0;
    if (output && strcmp(output, "-") != 0) {
        fout = fopen(output, "w");
        if (!fout) {
            fprintf(stderr, "csv: cannot create %s\n", output);
            fclose(fin);
            return 3;
        }
        close_fout = 1;
    }

    /* Header row. Move coords are 4 ints per square; we emit 8 columns
     * (from_x,from_y,from_z,from_w,to_x,to_y,to_z,to_w) plus standard
     * cosine/distance/dA1 + 11 channel energies + total. */
    fprintf(fout,
            "ply,from_x,from_y,from_z,from_w,to_x,to_y,to_z,to_w,"
            "dist_prev,cos_prev,dA1,"
            "E_A1,E_STD4_X,E_STD4_Y,E_STD4_Z,E_STD4_W,"
            "E_FIB_SYM_1,E_FIB_SYM_2,E_FIB_SYM_3,"
            "E_FA_PAWN_W,E_FA_PAWN_Y,E_FD_DIAG,"
            "E_total\n");
    /* Suppress -Wunused-variable warnings on names that we intentionally
     * spell out in the header but don't read at runtime. */
    (void)CSV_CHAN_NAMES_4D;

    /* Reused frame buffer; cs_spectral_frame_4d_t is ~180 KiB. */
    static cs_spectral_frame_4d_t fr;
    /* prev_enc holds the previous ply's encoding for dist/cos/dA1. */
    static float prev_enc[CS_ENCODING_DIM_4D];
    int have_prev = 0;

    for (uint32_t p = 0; p < hdr.n_plies; p++) {
        if (cs_file_4d_read_frame(fin, &fr) != 0) {
            fprintf(stderr, "csv: frame read failed at ply %u\n", p);
            break;
        }

        double E[CS_N_CSV_CHANNELS_4D];
        double total = 0.0;
        for (int c = 0; c < CS_N_CSV_CHANNELS_4D; c++) {
            E[c] = sum_sq_f4(&fr.encoding[c * CS_BLOCK_4D], CS_BLOCK_4D);
            total += E[c];
        }

        double dist_prev = 0.0;
        double cos_prev  = 0.0;
        double dA1       = 0.0;
        if (have_prev) {
            double dot = 0.0, n_cur = 0.0, n_prev = 0.0, ssq = 0.0;
            for (int i = 0; i < CS_ENCODING_DIM_4D; i++) {
                double a = (double)fr.encoding[i];
                double b = (double)prev_enc[i];
                double d = a - b;
                dot    += a * b;
                n_cur  += a * a;
                n_prev += b * b;
                ssq    += d * d;
            }
            dist_prev = sqrt(ssq);
            double denom = sqrt(n_cur) * sqrt(n_prev);
            cos_prev = (denom > 0.0) ? (dot / denom) : 0.0;
            /* dA1 = L2 of A1 channel difference */
            double a1ssq = 0.0;
            for (int i = 0; i < CS_BLOCK_4D; i++) {
                double d = (double)fr.encoding[i] - (double)prev_enc[i];
                a1ssq += d * d;
            }
            dA1 = sqrt(a1ssq);
        }

        fprintf(fout,
                "%u,%u,%u,%u,%u,%u,%u,%u,%u,",
                fr.ply,
                (unsigned)fr.from_x, (unsigned)fr.from_y,
                (unsigned)fr.from_z, (unsigned)fr.from_w,
                (unsigned)fr.to_x,   (unsigned)fr.to_y,
                (unsigned)fr.to_z,   (unsigned)fr.to_w);
        fmt_csv_num4(fout, dist_prev); fputc(',', fout);
        fmt_csv_cos4(fout, cos_prev);  fputc(',', fout);
        fmt_csv_num4(fout, dA1);       fputc(',', fout);
        for (int c = 0; c < CS_N_CSV_CHANNELS_4D; c++) {
            fmt_csv_num4(fout, E[c]); fputc(',', fout);
        }
        fmt_csv_num4(fout, total);
        fputc('\n', fout);

        memcpy(prev_enc, fr.encoding, sizeof(prev_enc));
        have_prev = 1;
    }

    fclose(fin);
    if (close_fout) fclose(fout);
    return 0;
}

/* ─── dispatch ─────────────────────────────────────────────────────────── */

static int is_help_flag(const char *s)
{
    return strcmp(s, "--help") == 0
        || strcmp(s, "-h") == 0
        || strcmp(s, "-?") == 0
        || strcmp(s, "/?") == 0
        || strcmp(s, "help") == 0;
}

int main(int argc, char **argv)
{
    if (argc < 2) { print_usage(stderr); return 1; }
    if (is_help_flag(argv[1])) return cmd_help();
    if (strcmp(argv[1], "version") == 0 || strcmp(argv[1], "--version") == 0)
        return cmd_version();
    if (strcmp(argv[1], "encode-fixture") == 0)
        return cmd_encode_fixture(argc - 2, argv + 2);
    if (strcmp(argv[1], "encode-fen4") == 0)
        return cmd_encode_fen4(argc - 2, argv + 2);
    if (strcmp(argv[1], "encode")      == 0)
        return cmd_encode(argc - 2, argv + 2);
    if (strcmp(argv[1], "csv")         == 0)
        return cmd_csv(argc - 2, argv + 2);

    fprintf(stderr, "spectral_4d: unknown command '%s'\n\n", argv[1]);
    print_usage(stderr);
    return 1;
}
