/* main_4d.c — `spectral_4d` CLI entry point.
 *
 * Mirrors the 2D `spectral` binary's manual argv strcmp dispatch style
 * (see src/main.c). Subcommands:
 *   version         — print encoder dims + channel layout
 *   help            — usage banner
 *   encode-fixture  — ingest positions_4d.jsonl, emit 40960 float32 LE on stdout
 *   encode-fen4     — [stub] single-position parity entry; needs FEN4 parser
 *   encode          — [P5] NDJSON4 → .spectralz4 bulk encoding
 *   csv             — [P5] per-ply channel energies
 *
 * The JSONL record schema (produced by codegen/emit_test_vectors_4d.py):
 *   {"name": "<fixture>", "pieces": {"<sq>": "<char>", ...}}
 * where <sq> is the decimal square index (0..4095) and <char> is one of
 * {P,N,B,R,Q,K,p,n,b,r,q,k}. encode-fixture is the parity-test surface;
 * Python shells out to it and compares 40960 float32 against fixtures_4d.npz.
 */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "cs_encoder_4d.h"

#ifdef _WIN32
#  include <io.h>
#  include <fcntl.h>
#endif

/* ─── help / usage ─────────────────────────────────────────────────────── */

static void print_usage(FILE *fp)
{
    fprintf(fp,
        "spectral_4d — 40 960-dim 4D spectral chess encoder (C17)\n"
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
        "                     Emits 40960 little-endian float32 (163 840 bytes)\n"
        "                     on stdout. Parity-test entry point.\n"
        "    encode-fen4      [stub — requires FEN4 parser]\n"
        "    encode           [stub — P5]  NDJSON4 → .spectralz4 bulk encoding\n"
        "    csv              [stub — P5]  Per-ply channel energies (CSV)\n"
        "\n"
        "ENCODING DIMENSIONS:\n"
        "    10 channels × 4096 board eigenmodes = 40 960 floats per position.\n"
        "        Ch 0     : A_1 orbit-mean                               (dims     0..4095 )\n"
        "        Ch 1-4   : std-4D coord residuals                       (dims  4096..20479)\n"
        "        Ch 5-7   : symmetric 3D cross-piece fiber               (dims 20480..32767)\n"
        "        Ch 8     : antisymmetric pawn fiber (Z_2-breaking, w)   (dims 32768..36863)\n"
        "        Ch 9     : diagonal deviation (rook shadow)             (dims 36864..40959)\n"
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

static int cmd_todo(const char *name)
{
    fprintf(stderr,
        "spectral_4d %s: not yet implemented.\n"
        "  See the v1.1 port plan (when-we-need-to-spicy-seahorse.md).\n",
        name);
    return 4;
}

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

/* Parse {"<square>":"<char>", ...} into pos->sq. Square keys are decimal
 * strings 0..4095; chars are single ASCII letters. Tolerates whitespace
 * (json.dumps default inserts one space after each `:` and `,`). */
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
        pos->sq[s] = (int8_t)(*obj);
        obj++;  /* past the single piece char */
        if (*obj != '"') return -1;
        obj++;  /* past closing quote of value */
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
    if (strcmp(argv[1], "encode-fen4") == 0) return cmd_todo("encode-fen4");
    if (strcmp(argv[1], "encode")      == 0) return cmd_todo("encode");
    if (strcmp(argv[1], "csv")         == 0) return cmd_todo("csv");

    fprintf(stderr, "spectral_4d: unknown command '%s'\n\n", argv[1]);
    print_usage(stderr);
    return 1;
}
