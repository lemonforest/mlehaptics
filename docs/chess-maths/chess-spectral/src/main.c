/* main.c — `spectral` CLI entry point.
 *
 * Commands are listed by `spectral --help`. Only a subset is implemented today;
 * unimplemented commands (none at v1.2.4) print a clear TODO message and exit non-zero so shell
 * pipelines fail loudly instead of silently producing empty output.
 *
 * PGN ingestion flow (three equivalent entry paths):
 *   spectral encode game.pgn       -o out.spectral   # auto-pipes via pgn_bridge.py
 *   spectral encode --url <URL>    -o out.spectral   # auto-fetch + pipe
 *   spectral encode game.ndjson    -o out.spectral   # pre-produced NDJSON
 *
 * The bridge is a ~130-line Python script (bridge/pgn_bridge.py) that uses
 * python-chess to handle SAN parsing, legality, and move generation. The C
 * side only consumes NDJSON with {"fen": "..."} records.
 *
 * Future: when interactive ply-by-ply lands, we'll port the move parser into
 * C so the binary is fully self-contained. Until then the bridge is the
 * single Python seam in the pipeline.
 */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>
#include "cs_encoder.h"
#include "cs_frame.h"
#include "cs_gzip.h"

#ifdef _WIN32
#  define CS_POPEN  _popen
#  define CS_PCLOSE _pclose
#else
#  define CS_POPEN  popen
#  define CS_PCLOSE pclose
#endif

int cs_fen_parse(const char *fen, cs_position_t *pos);

/* ─── help / usage ─────────────────────────────────────────────────────── */

static void print_usage(FILE *fp)
{
    fprintf(fp,
        "spectral — 640-dim spectral chess encoder (C17)\n"
        "\n"
        "USAGE:\n"
        "    spectral <command> [options]\n"
        "    spectral --help | -h | -? | /? | help\n"
        "\n"
        "COMMANDS:\n"
        "    encode      Encode a PGN / NDJSON / URL stream into a .spectral file\n"
        "    encode-fen  Encode a single FEN and print 640 floats to stdout\n"
        "    csv         Export per-ply channel energies to CSV (LLM-friendly)\n"
        "    query       Print spectral decomposition at ply N\n"
        "    analyze     Per-game summary (A1 peak, drop, crisis ply; JSON)\n"
        "    compare     Cosine-compare two .spectral files\n"
        "    heatmap     ANSI 8x8 heatmap of a single channel at ply N\n"
        "    play        Ply-by-ply viewer (--ply N for detail; default lists all)\n"
        "    export      Export a .spectral file to JSON for the web viewer\n"
        "    version     Print encoder version and dimensions\n"
        "    help        Print this message\n"
        "\n"
        "COMMAND DETAILS:\n"
        "    encode <input> [--pgn] [--url URL] [-z] -o <output.spectral[z]>\n"
        "        Encode every ply of one or more games into a .spectral file\n"
        "        (header + one 2568-byte frame per ply: encoding[640] + ply + move).\n"
        "        Input forms:\n"
        "            *.pgn            PGN file (auto-piped through pgn_bridge.py)\n"
        "            *.ndjson         NDJSON with a \"fen\" field per line\n"
        "            -                read NDJSON from stdin\n"
        "            --pgn -          read PGN from stdin (forces the bridge)\n"
        "            --pgn FILE       treat FILE as PGN regardless of extension\n"
        "            --url <URL>      fetch PGN from the web (lichess, chess.com)\n"
        "            -z, --compress   gzip-compress output (file becomes *.spectralz,\n"
        "                             ~5-6x smaller; readers detect 1F 8B transparently)\n"
        "            --pgn-start N    skip to game N (0-indexed) in a multi-game PGN\n"
        "            --pgn-count K    emit at most K games starting at --pgn-start\n"
        "                             (both forwarded to pgn_bridge.py)\n"
        "        PGN handling requires Python + 'pip install python-chess'.\n"
        "        Override interpreter with CS_PYTHON, bridge path with CS_PGN_BRIDGE.\n"
        "        Examples:\n"
        "            spectral encode game.pgn     -o game.spectral\n"
        "            spectral encode game.pgn -z  -o game.spectralz\n"
        "            spectral encode game.ndjson  -o game.spectral\n"
        "            python pgn_fetcher.py fetch --source hf --n 10 --format pgn \\\n"
        "                 | spectral encode --pgn - -z -o games.spectralz\n"
        "            spectral encode --url https://lichess.org/game/export/ABCD1234.pgn \\\n"
        "                            -o game.spectral\n"
        "\n"
        "    encode-fen --fen \"<placement>\"\n"
        "        Encode one position. Emits 640 space-separated doubles on\n"
        "        stdout. Handy for smoke-testing and diff'ing against Python.\n"
        "\n"
        "    csv <file.spectral[z]> [-o out.csv]\n"
        "        Export per-ply channel energies as CSV — one row per ply,\n"
        "        one column per channel. Designed for downstream analysis\n"
        "        in Python/R/spreadsheets or LLMs that can't parse our binary.\n"
        "        Columns: ply, move_from, move_to,\n"
        "                 E_A1, E_A2, E_B1, E_B2, E_E,\n"
        "                 E_F1, E_F2, E_F3, E_FA, E_FD,\n"
        "                 E_total, dA1\n"
        "        where E_X = ||channel X||^2 (64-dim block energy) and\n"
        "        dA1 = ||A1(ply) - A1(ply-1)||^2 (Nagle's 'crisis' signal).\n"
        "        Input may be plain .spectral or gzip-compressed .spectralz.\n"
        "        Omit -o or pass -o - to write CSV to stdout.\n"
        "\n"
        "    query <file.spectral> --ply <N>\n"
        "        Print full spectral decomposition at ply N: channel energies,\n"
        "        delta breakdown, fiber coordinates.\n"
        "\n"
        "    heatmap <file.spectral> --ply <N> --channel <A1|A2|B1|B2|E|F1|F2|F3|FA|FD>\n"
        "        Render an ANSI-colored 8x8 projection of the selected channel\n"
        "        at the given ply. FA = antisymmetric pawn channel (dims 512-575).\n"
        "        FD = diagonal deviation (dims 576-639).\n"
        "\n"
        "    analyze <file.spectral>\n"
        "        Per-game summary: A1 peak ply, fiber peak, max |delta_a1|\n"
        "        (crisis detection), overall complexity arc.\n"
        "\n"
        "    compare <a.spectral> <b.spectral>\n"
        "        Cosine similarity of temporal history vectors; per-ply\n"
        "        alignment of A1 trajectories.\n"
        "\n"
        "    export <file.spectral> -o <out.json>\n"
        "        Dump frames as JSON for the web viewer.\n"
        "\n"
        "EXIT CODES:\n"
        "    0  success\n"
        "    1  usage error / unknown command\n"
        "    2  missing / invalid arguments\n"
        "    3  I/O or parse error during processing\n"
        "    4  command is not yet implemented\n"
        "\n"
        "ENCODING DIMENSIONS:\n"
        "    10 channels × 64 board eigenmodes = 640 dims per position.\n"
        "        Ch 0-4 : D4 irreps    A1, A2, B1, B2, E              (dims 0..319)\n"
        "        Ch 5-7 : symmetric 3D fiber                          (dims 320..511)\n"
        "        Ch 8   : antisymmetric pawn fiber (Z2-breaking)      (dims 512..575)\n"
        "        Ch 9   : diagonal deviation (rook's shadow)          (dims 576..639)\n"
    );
}

static int cmd_help(void) { print_usage(stdout); return 0; }

static int cmd_version(void)
{
    printf("spectral 0.1.0 — encoding_dim=%d channels=%d board_dim=%d\n",
           CS_ENCODING_DIM, CS_NUM_CHANNELS, CS_BOARD_DIM);
    printf("coprime: row=%d col=%d time=%d\n",
           CS_COPRIME_ROW, CS_COPRIME_COL, CS_COPRIME_TIME);
    return 0;
}

/* ─── encode-fen (single position) ─────────────────────────────────────── */

static int cmd_encode_fen(int argc, char **argv)
{
    const char *fen = NULL;
    for (int i = 0; i < argc; i++) {
        if (strcmp(argv[i], "--fen") == 0 && i + 1 < argc) fen = argv[++i];
    }
    if (!fen) {
        fprintf(stderr, "encode-fen: missing --fen \"<placement>\"\n");
        return 2;
    }
    cs_position_t pos;
    int rc = cs_fen_parse(fen, &pos);
    if (rc != 0) { fprintf(stderr, "FEN parse error %d\n", rc); return 3; }

    cs_encoding_t enc;
    cs_encode_640(&pos, SPECTRAL_VALS, &enc);
    for (int i = 0; i < CS_ENCODING_DIM; i++) {
        printf("%.6g%c", enc.v[i], (i + 1 == CS_ENCODING_DIM) ? '\n' : ' ');
    }
    return 0;
}

/* ─── NDJSON → .spectral encoding ──────────────────────────────────────── */

/* Extract the value of a "key":"..." field from a JSON line. Writes into
 * `dst` (dst_size including the NUL). Returns 0 on success, -1 if not found.
 * FEN never contains quotes or backslashes, so a straight substring scan is
 * sufficient for the pgn_bridge format. */
static int json_str_field(const char *line, const char *key,
                          char *dst, size_t dst_size)
{
    char needle[64];
    int nk = snprintf(needle, sizeof(needle), "\"%s\":\"", key);
    if (nk < 0 || (size_t)nk >= sizeof(needle)) return -1;
    const char *p = strstr(line, needle);
    if (!p) return -1;
    p += nk;
    const char *q = strchr(p, '"');
    if (!q) return -1;
    size_t n = (size_t)(q - p);
    if (n + 1 > dst_size) n = dst_size - 1;
    memcpy(dst, p, n);
    dst[n] = '\0';
    return 0;
}

/* Extract an integer field (plain "key":N) from a JSON line.
 * Returns 0 on success, -1 if not found. */
static int json_int_field(const char *line, const char *key, int *out)
{
    char needle[64];
    int nk = snprintf(needle, sizeof(needle), "\"%s\":", key);
    if (nk < 0 || (size_t)nk >= sizeof(needle)) return -1;
    const char *p = strstr(line, needle);
    if (!p) return -1;
    p += nk;
    while (*p == ' ') p++;
    if (*p == '"') return -1;  /* string, not int */
    *out = atoi(p);
    return 0;
}

/* ─── PGN bridge subprocess plumbing ───────────────────────────────────── */

static const char *bridge_python(void)
{
    const char *p = getenv("CS_PYTHON");
    if (p && *p) return p;
#ifdef _WIN32
    return "python";     /* py-launcher is also common; user can override. */
#else
    return "python3";
#endif
}

static const char *bridge_script(void)
{
    const char *p = getenv("CS_PGN_BRIDGE");
    if (p && *p) return p;
#ifdef CS_BRIDGE_SCRIPT_PATH
    return CS_BRIDGE_SCRIPT_PATH;
#else
    return "bridge/pgn_bridge.py";
#endif
}

/* Case-insensitive suffix match. */
static int has_suffix_ci(const char *s, const char *suf)
{
    size_t ls = strlen(s), lf = strlen(suf);
    if (lf > ls) return 0;
    const char *p = s + (ls - lf);
    for (size_t i = 0; i < lf; i++) {
        char a = p[i], b = suf[i];
        if (a >= 'A' && a <= 'Z') a = (char)(a + 32);
        if (b >= 'A' && b <= 'Z') b = (char)(b + 32);
        if (a != b) return 0;
    }
    return 1;
}

/* Open an NDJSON-producing stream. On return, *is_pipe is 1 if the caller
 * must use CS_PCLOSE, 0 if plain fclose. Sets *fp, returns 0 on success.
 *
 * Routing:
 *   url != NULL           → bridge --url <URL>
 *   force_pgn             → bridge --input <path-or-stdin>  (treat any input as PGN)
 *   input_path ends .pgn  → bridge --input <path>
 *   input_path == "-"     → plain stdin (assumed NDJSON)
 *   otherwise             → fopen(input_path) (assumed NDJSON)
 */
static int open_ndjson_stream(const char *input_path, const char *url,
                              int force_pgn, int pgn_start, int pgn_count,
                              FILE **fp, int *is_pipe)
{
    *fp = NULL;
    *is_pipe = 0;

    int use_bridge = (url != NULL)
        || force_pgn
        || (input_path && has_suffix_ci(input_path, ".pgn"));

    if (!use_bridge) {
        if (input_path && strcmp(input_path, "-") == 0) {
            *fp = stdin;
            return 0;
        }
        FILE *f = fopen(input_path, "r");
        if (!f) { fprintf(stderr, "encode: cannot open %s\n", input_path); return -1; }
        *fp = f;
        return 0;
    }

    /* PGN / URL path — shell out to pgn_bridge.py and read NDJSON from
     * its stdout. We rely on the OS shell to re-quote the tokens.
     *
     * Windows cmd.exe quoting gotcha: when the command line starts with
     * `"` and contains >2 quote chars, cmd strips the outermost pair
     * (documented in `cmd /?`). We work around it by wrapping the entire
     * line in one extra pair of quotes so cmd's outer-strip leaves the
     * inner quoting intact. POSIX `/bin/sh -c` doesn't need this dance. */
    char cmd[8192];
    const char *py = bridge_python();
    const char *br = bridge_script();
    int n;
#ifdef _WIN32
    const char *open_wrap = "\"";
    const char *close_wrap = "\"";
#else
    const char *open_wrap = "";
    const char *close_wrap = "";
#endif
    /* When the caller passes "-" or leaves input_path NULL under --pgn,
     * we want the bridge to consume its own stdin (inheriting ours). */
    const char *bridge_input = (input_path && strcmp(input_path, "-") != 0)
                               ? input_path : "-";
    /* Optional slice flags — only emitted when the user passed non-default
     * values on the spectral CLI. Defaults (0) match pgn_bridge's own
     * defaults so omission is semantically identical. */
    char slice[128] = {0};
    if (pgn_start > 0 || pgn_count > 0) {
        int sn = snprintf(slice, sizeof(slice),
                          " --start-game %d --max-games %d",
                          pgn_start > 0 ? pgn_start : 0,
                          pgn_count > 0 ? pgn_count : 0);
        if (sn < 0 || (size_t)sn >= sizeof(slice)) {
            fprintf(stderr, "encode: slice flags overflow\n");
            return -1;
        }
    }

    if (url) {
        n = snprintf(cmd, sizeof(cmd),
                     "%s\"%s\" \"%s\" --url \"%s\"%s%s",
                     open_wrap, py, br, url, slice, close_wrap);
    } else {
        n = snprintf(cmd, sizeof(cmd),
                     "%s\"%s\" \"%s\" --input \"%s\"%s%s",
                     open_wrap, py, br, bridge_input, slice, close_wrap);
    }
    if (n < 0 || (size_t)n >= sizeof(cmd)) {
        fprintf(stderr, "encode: bridge command too long\n");
        return -1;
    }

    fprintf(stderr, "encode: piping through bridge: %s\n", cmd);
    FILE *pipe = CS_POPEN(cmd, "r");
    if (!pipe) {
        fprintf(stderr,
            "encode: failed to launch pgn_bridge.py.\n"
            "        Checked interpreter:  %s  (override via CS_PYTHON)\n"
            "        Checked script path:  %s  (override via CS_PGN_BRIDGE)\n"
            "        Ensure python is on PATH and run: pip install python-chess\n",
            py, br);
        return -1;
    }
    *fp = pipe;
    *is_pipe = 1;
    return 0;
}

static int cmd_encode(int argc, char **argv)
{
    const char *input = NULL;
    const char *output = NULL;
    const char *url = NULL;
    int force_pgn = 0;
    int compress = 0;
    int pgn_start = 0;
    int pgn_count = 0;
    for (int i = 0; i < argc; i++) {
        if ((strcmp(argv[i], "-o") == 0 || strcmp(argv[i], "--output") == 0)
            && i + 1 < argc) {
            output = argv[++i];
        } else if ((strcmp(argv[i], "--url") == 0 || strcmp(argv[i], "-u") == 0)
                   && i + 1 < argc) {
            url = argv[++i];
        } else if (strcmp(argv[i], "--pgn") == 0) {
            force_pgn = 1;
        } else if (strcmp(argv[i], "--pgn-start") == 0 && i + 1 < argc) {
            pgn_start = atoi(argv[++i]);
        } else if (strcmp(argv[i], "--pgn-count") == 0 && i + 1 < argc) {
            pgn_count = atoi(argv[++i]);
        } else if (strcmp(argv[i], "--compress") == 0 || strcmp(argv[i], "-z") == 0) {
            compress = 1;
        } else if (strcmp(argv[i], "-") == 0 && !input) {
            input = "-";  /* explicit stdin */
        } else if (argv[i][0] != '-' && !input) {
            input = argv[i];
        }
    }
    if (!input && !url && !force_pgn) {
        fprintf(stderr,
            "encode: missing input. Provide one of:\n"
            "    spectral encode game.pgn         -o out.spectral\n"
            "    spectral encode game.ndjson      -o out.spectral\n"
            "    spectral encode -                -o out.spectral   (NDJSON on stdin)\n"
            "    spectral encode --pgn -          -o out.spectral   (PGN on stdin)\n"
            "    spectral encode --url <URL>      -o out.spectral\n"
            "    spectral encode game.pgn -z      -o out.spectralz  (gzip-compressed)\n"
            "  Multi-game PGN slicing:\n"
            "    spectral encode corpus.pgn --pgn-start 0 --pgn-count 100 -o head100.spectral\n"
            "    spectral encode corpus.pgn --pgn-start 2527 --pgn-count 100 -o mid100.spectral\n");
        return 2;
    }
    if (!output) {
        fprintf(stderr, "encode: missing -o <output.spectral[z]>\n");
        return 2;
    }
    /* --pgn with no input implies stdin. */
    if (force_pgn && !input && !url) input = "-";

    if (pgn_start < 0 || pgn_count < 0) {
        fprintf(stderr, "encode: --pgn-start/--pgn-count must be >= 0\n");
        return 2;
    }
    if ((pgn_start > 0 || pgn_count > 0) && !url && !force_pgn
        && !(input && has_suffix_ci(input, ".pgn"))) {
        fprintf(stderr,
            "encode: --pgn-start/--pgn-count only apply when ingesting PGN "
            "(use --pgn, --url, or a .pgn file)\n");
        return 2;
    }

    FILE *fin = NULL;
    int is_pipe = 0;
    if (open_ndjson_stream(input, url, force_pgn, pgn_start, pgn_count,
                           &fin, &is_pipe) != 0) return 3;

    /* When compressing, write plain frames to an anonymous tmpfile first
     * (so header backfill via fseek still works), then deflate the whole
     * thing to the user's output path at the end. */
    FILE *fout = compress ? tmpfile() : fopen(output, "wb");
    if (!fout) {
        if (is_pipe) CS_PCLOSE(fin); else if (fin != stdin) fclose(fin);
        fprintf(stderr, "encode: cannot create %s\n",
                compress ? "temporary staging file" : output);
        return 3;
    }

    /* Placeholder header; n_plies is backfilled after processing. */
    cs_file_header_t hdr = {0};
    hdr.magic = CS_FILE_MAGIC;
    hdr.version = CS_FILE_VERSION;
    hdr.encoding_dim = CS_ENCODING_DIM;
    hdr.frame_bytes = (uint32_t)sizeof(cs_spectral_frame_t);
    hdr.n_plies = 0;
    if (cs_file_write_header(fout, &hdr) != 0) {
        fclose(fin); fclose(fout);
        fprintf(stderr, "encode: header write failed\n");
        return 3;
    }

    uint32_t n_plies = 0;
    uint32_t line_no = 0;

    /* Portable getline loop — on MSVC, roll our own. */
    char buf[8192];
    while (fgets(buf, sizeof(buf), fin)) {
        line_no++;

        /* Skip bridge header (first non-empty line may contain "bridge_version"). */
        if (strstr(buf, "bridge_version")) continue;

        char fen[128];
        if (json_str_field(buf, "fen", fen, sizeof(fen)) != 0) continue;

        int ply = -1;
        (void)json_int_field(buf, "ply", &ply);

        char move_san[32] = {0};
        (void)json_str_field(buf, "move", move_san, sizeof(move_san));

        cs_position_t pos;
        int rc = cs_fen_parse(fen, &pos);
        if (rc != 0) {
            fprintf(stderr, "encode: FEN parse error %d at line %u: %s\n",
                    rc, line_no, fen);
            continue;
        }

        cs_encoding_t enc;
        cs_encode_640(&pos, SPECTRAL_VALS, &enc);

        cs_spectral_frame_t fr;
        memset(&fr, 0, sizeof(fr));

        for (int i = 0; i < CS_ENCODING_DIM; i++) {
            fr.encoding[i] = (float)enc.v[i];
        }
        fr.ply = (uint32_t)(ply >= 0 ? ply : (int)n_plies);

        /* NDJSON v2 carries move_from/move_to/move_promo/move_flags per
         * ply. Fall back to 0xFF/0 sentinels if a legacy producer omits
         * them (matches the Python reference encoder's behaviour). */
        int mv_from = 0xFF, mv_to = 0xFF, mv_promo = 0, mv_flags = 0;
        (void)json_int_field(buf, "move_from",  &mv_from);
        (void)json_int_field(buf, "move_to",    &mv_to);
        (void)json_int_field(buf, "move_promo", &mv_promo);
        (void)json_int_field(buf, "move_flags", &mv_flags);
        fr.move_from  = (uint8_t)(mv_from  & 0xFF);
        fr.move_to    = (uint8_t)(mv_to    & 0xFF);
        fr.move_promo = (uint8_t)(mv_promo & 0xFF);
        fr.move_flags = (uint8_t)(mv_flags & 0xFF);

        if (cs_file_write_frame(fout, &fr) != 0) {
            fprintf(stderr, "encode: frame write failed at ply %u\n", fr.ply);
            break;
        }
        n_plies++;
    }

    /* Backfill n_plies in the header. */
    hdr.n_plies = n_plies;
    if (cs_file_write_header(fout, &hdr) != 0) {
        fprintf(stderr, "encode: header backfill failed\n");
    }

    if (is_pipe) {
        int rc = CS_PCLOSE(fin);
        if (rc != 0) {
            fprintf(stderr, "encode: pgn_bridge.py exited with status %d\n", rc);
        }
    } else if (fin != stdin) {
        fclose(fin);
    }

    int exit_code = 0;
    if (compress) {
        /* fout is an anonymous tmpfile holding the fully-written plain blob.
         * Flush miniz through it into the user's target path. */
        if (fflush(fout) != 0) {
            fprintf(stderr, "encode: staging flush failed\n");
            exit_code = 3;
        } else {
            int rc = cs_file_write_gzip(output, fout);
            if (rc != 0) {
                fprintf(stderr, "encode: gzip write to %s failed (rc=%d)\n",
                        output, rc);
                exit_code = 3;
            }
        }
    }
    fclose(fout);  /* closes tmpfile (auto-deletes) or the plain .spectral */

    if (exit_code == 0) {
        fprintf(stderr, "encode: wrote %u frames to %s%s\n",
                n_plies, output, compress ? " (gzip)" : "");
    }
    return exit_code;
}

/* ─── csv export (per-ply channel energies) ────────────────────────────── */

/* Channel layout (10 × 64 = 640). Order + names mirror heatmap --channel. */
static const struct {
    const char *name;
    int         start;  /* inclusive */
} CS_CHANNELS[10] = {
    {"A1", 0}, {"A2", 64}, {"B1", 128}, {"B2", 192}, {"E", 256},
    {"F1", 320}, {"F2", 384}, {"F3", 448}, {"FA", 512}, {"FD", 576},
};

static double sum_sq_f(const float *v, int n)
{
    double s = 0.0;
    for (int i = 0; i < n; i++) { double x = v[i]; s += x * x; }
    return s;
}

/* Chat-friendly number formatter. Goal: minimize token count in the CSV
 * without dropping useful precision. Scheme:
 *   |x| < 1e-6           → "0"           (floating-point noise)
 *   |x| >= 100           → "%.0f"        (integer; 4 sig figs is noise)
 *   |x| >= 1             → "%.2f"        (two decimals)
 *   |x| >= 0.01          → "%.3f"        (three decimals)
 *   else                 → "%.2e"        (compact exponential)
 * Dimensionless quantities in [-1,1] (cos) always use 4 decimals so the
 * caller has enough resolution to distinguish near-orthogonal (≈0) from
 * near-identical (≈1) positions.
 */
static void fmt_csv_num(FILE *fp, double x)
{
    double ax = fabs(x);
    if (ax < 1e-6)      { fputc('0', fp); return; }
    if (ax >= 100.0)    { fprintf(fp, "%.0f", x); return; }
    if (ax >= 1.0)      { fprintf(fp, "%.2f", x); return; }
    if (ax >= 0.01)     { fprintf(fp, "%.3f", x); return; }
    fprintf(fp, "%.2e", x);
}

static void fmt_csv_cos(FILE *fp, double x)
{
    /* Cosine similarity: keep 4 decimals always. This is the signal we
     * rely on to distinguish 0.998 (spectrally invisible blunder) from
     * 0.017 (near-orthogonal queen trade). %g with 4 sig figs would
     * collapse both extremes. */
    fprintf(fp, "%.4f", x);
}

static int cmd_csv(int argc, char **argv)
{
    const char *input  = NULL;
    const char *output = NULL;
    for (int i = 0; i < argc; i++) {
        if ((strcmp(argv[i], "-o") == 0 || strcmp(argv[i], "--output") == 0)
            && i + 1 < argc) {
            output = argv[++i];
        } else if (argv[i][0] != '-' && !input) {
            input = argv[i];
        }
    }
    if (!input) {
        fprintf(stderr,
            "csv: missing input file.\n"
            "    spectral csv <game.spectral[z]> [-o out.csv]\n"
            "    (omit -o or pass -o - to write to stdout)\n");
        return 2;
    }

    FILE *fin = NULL;
    if (cs_open_read_transparent(input, &fin) != 0 || !fin) {
        fprintf(stderr, "csv: cannot open %s (or bad gzip)\n", input);
        return 3;
    }

    cs_file_header_t hdr;
    if (cs_file_read_header(fin, &hdr) != 0) {
        fprintf(stderr, "csv: %s is not a valid .spectral file\n", input);
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

    /* Header row.
     *   dist_prev,cos_prev — L2 distance and cosine similarity between
     *     this ply's full 640-dim encoding and the previous ply's. These
     *     are the primary chat-analysis signals: spectrally invisible
     *     moves have cos_prev ≈ 1, structural earthquakes have large
     *     dist_prev, near-orthogonal trades have cos_prev ≈ 0.
     *   dA1 — L2 of the A1 channel change alone (dims 0-63). Catches
     *     totally-symmetric shifts even when the rest of the position is
     *     unchanged.
     *   E_xx — ||channel||² per channel (10 cols).
     *   E_total — Σ E_xx (redundant but useful as a sanity check).
     *
     * First row has dist_prev=cos_prev=dA1=0 (no predecessor). */
    fprintf(fout,
            "ply,move_from,move_to,"
            "dist_prev,cos_prev,dA1,"
            "E_A1,E_A2,E_B1,E_B2,E_E,E_F1,E_F2,E_F3,E_FA,E_FD,"
            "E_total\n");

    float prev_enc[CS_ENCODING_DIM];
    int have_prev = 0;

    for (uint32_t p = 0; p < hdr.n_plies; p++) {
        cs_spectral_frame_t fr;
        if (cs_file_read_frame(fin, &fr) != 0) {
            fprintf(stderr, "csv: frame read failed at ply %u\n", p);
            break;
        }

        double E[10];
        double total = 0.0;
        for (int c = 0; c < 10; c++) {
            E[c] = sum_sq_f(&fr.encoding[CS_CHANNELS[c].start], CS_BOARD_DIM);
            total += E[c];
        }

        double dist_prev = 0.0;
        double cos_prev  = 0.0;
        double dA1       = 0.0;
        if (have_prev) {
            double dot = 0.0, n_cur = 0.0, n_prev = 0.0, ssq = 0.0;
            for (int i = 0; i < CS_ENCODING_DIM; i++) {
                double a = (double)fr.encoding[i];
                double b = (double)prev_enc[i];
                double d = a - b;
                ssq    += d * d;
                dot    += a * b;
                n_cur  += a * a;
                n_prev += b * b;
            }
            dist_prev = sqrt(ssq);
            /* Guard against a zero-norm encoding (empty-board edge case). */
            double denom = sqrt(n_cur) * sqrt(n_prev);
            cos_prev = (denom > 0.0) ? (dot / denom) : 0.0;

            double a1sq = 0.0;
            for (int i = 0; i < CS_BOARD_DIM; i++) {
                double d = (double)fr.encoding[i] - (double)prev_enc[i];
                a1sq += d * d;
            }
            dA1 = sqrt(a1sq);
        }
        memcpy(prev_enc, fr.encoding, sizeof(prev_enc));
        have_prev = 1;

        /* move_from/to are 0xFF when unset (v2 writer hasn't wired SAN yet). */
        fprintf(fout, "%u,%u,%u,",
                fr.ply,
                (unsigned)fr.move_from, (unsigned)fr.move_to);
        fmt_csv_num(fout, dist_prev);  fputc(',', fout);
        fmt_csv_cos(fout, cos_prev);   fputc(',', fout);
        fmt_csv_num(fout, dA1);        fputc(',', fout);
        for (int c = 0; c < 10; c++) { fmt_csv_num(fout, E[c]); fputc(',', fout); }
        fmt_csv_num(fout, total);
        fputc('\n', fout);
    }

    if (close_fout) fclose(fout);
    fclose(fin);

    fprintf(stderr, "csv: wrote %u rows from %s%s%s\n",
            hdr.n_plies, input,
            (output && strcmp(output, "-") != 0) ? " to "      : "",
            (output && strcmp(output, "-") != 0) ? output       : "");
    return 0;
}

/* ─── compare (cosine similarity between two .spectral files) ──────────── */

static int read_all_encodings(const char *path, float **out_buf,
                              uint32_t *out_n_plies)
{
    FILE *fp = NULL;
    if (cs_open_read_transparent(path, &fp) != 0 || !fp) return -1;
    cs_file_header_t hdr;
    if (cs_file_read_header(fp, &hdr) != 0) { fclose(fp); return -2; }
    float *buf = (float *)malloc((size_t)hdr.n_plies
                                 * CS_ENCODING_DIM * sizeof(float));
    if (!buf) { fclose(fp); return -3; }
    cs_spectral_frame_t fr;
    for (uint32_t p = 0; p < hdr.n_plies; p++) {
        if (cs_file_read_frame(fp, &fr) != 0) {
            free(buf); fclose(fp); return -4;
        }
        memcpy(&buf[(size_t)p * CS_ENCODING_DIM], fr.encoding,
               sizeof(fr.encoding));
    }
    fclose(fp);
    *out_buf = buf;
    *out_n_plies = hdr.n_plies;
    return 0;
}

static int cmd_compare(int argc, char **argv)
{
    const char *a = NULL, *b = NULL;
    for (int i = 0; i < argc; i++) {
        if (argv[i][0] == '-') continue;
        if (!a) a = argv[i];
        else if (!b) b = argv[i];
    }
    if (!a || !b) {
        fprintf(stderr, "compare: usage: spectral compare A.spectral[z] B.spectral[z]\n");
        return 2;
    }
    float *ea = NULL, *eb = NULL;
    uint32_t na = 0, nb = 0;
    if (read_all_encodings(a, &ea, &na) != 0) {
        fprintf(stderr, "compare: cannot read %s\n", a); return 3;
    }
    if (read_all_encodings(b, &eb, &nb) != 0) {
        fprintf(stderr, "compare: cannot read %s\n", b); free(ea); return 3;
    }
    if (na != nb) {
        fprintf(stderr, "compare: ply counts differ (%u vs %u); "
                "comparing first %u plies\n", na, nb, na < nb ? na : nb);
    }
    uint32_t n = na < nb ? na : nb;

    /* Aggregate stats: min, mean, max cosine + ply with min cosine. */
    double cmin = 2.0, cmax = -2.0, csum = 0.0;
    uint32_t cmin_ply = 0;
    for (uint32_t p = 0; p < n; p++) {
        double dot = 0.0, na2 = 0.0, nb2 = 0.0;
        const float *fa = &ea[(size_t)p * CS_ENCODING_DIM];
        const float *fb = &eb[(size_t)p * CS_ENCODING_DIM];
        for (int i = 0; i < CS_ENCODING_DIM; i++) {
            double x = (double)fa[i], y = (double)fb[i];
            dot += x * y; na2 += x * x; nb2 += y * y;
        }
        double denom = sqrt(na2) * sqrt(nb2);
        double cos = (denom > 0.0) ? (dot / denom) : 1.0;
        if (cos < cmin) { cmin = cos; cmin_ply = p; }
        if (cos > cmax) cmax = cos;
        csum += cos;
    }

    if (n > 0) {
        double cmean = csum / (double)n;
        printf("compare: n_plies=%u  cos_min=%.4f (ply=%u)  "
               "cos_mean=%.4f  cos_max=%.4f\n",
               n, cmin, cmin_ply, cmean, cmax);
    } else {
        printf("compare: n_plies=0 (nothing to compare)\n");
    }

    free(ea); free(eb);
    return 0;
}

/* ─── query (frame at ply N — channel breakdown) ───────────────────────── */

static int cmd_query(int argc, char **argv)
{
    const char *input = NULL;
    int ply = -1;
    for (int i = 0; i < argc; i++) {
        if (strcmp(argv[i], "--ply") == 0 && i + 1 < argc) {
            ply = atoi(argv[++i]);
        } else if (argv[i][0] != '-' && !input) {
            input = argv[i];
        }
    }
    if (!input || ply < 0) {
        fprintf(stderr, "query: usage: spectral query <file.spectral[z]> --ply N\n");
        return 2;
    }
    FILE *fp = NULL;
    if (cs_open_read_transparent(input, &fp) != 0 || !fp) {
        fprintf(stderr, "query: cannot open %s\n", input); return 3;
    }
    cs_file_header_t hdr;
    if (cs_file_read_header(fp, &hdr) != 0) {
        fclose(fp); fprintf(stderr, "query: bad header\n"); return 3;
    }
    if ((uint32_t)ply >= hdr.n_plies) {
        fclose(fp);
        fprintf(stderr, "query: ply %d out of range (n_plies=%u)\n",
                ply, hdr.n_plies);
        return 3;
    }
    if (cs_file_seek_frame(fp, (uint32_t)ply, &hdr) != 0) {
        fclose(fp); fprintf(stderr, "query: seek failed\n"); return 3;
    }
    cs_spectral_frame_t fr;
    if (cs_file_read_frame(fp, &fr) != 0) {
        fclose(fp); fprintf(stderr, "query: read failed\n"); return 3;
    }
    fclose(fp);

    printf("ply %u  move_from=%u  move_to=%u  promo=%u  flags=%u\n",
           fr.ply, fr.move_from, fr.move_to, fr.move_promo, fr.move_flags);
    double total = 0.0;
    for (int c = 0; c < 10; c++) {
        double E = sum_sq_f(&fr.encoding[CS_CHANNELS[c].start], CS_BOARD_DIM);
        total += E;
        printf("  E_%-3s = %12.4f   dims %3d..%3d\n",
               CS_CHANNELS[c].name, E,
               CS_CHANNELS[c].start,
               CS_CHANNELS[c].start + CS_BOARD_DIM - 1);
    }
    printf("  E_total= %12.4f\n", total);
    return 0;
}

/* ─── heatmap (ANSI 8x8 of one channel at ply N) ───────────────────────── */

static int cmd_heatmap(int argc, char **argv)
{
    const char *input = NULL;
    const char *channel = "A1";
    int ply = -1;
    for (int i = 0; i < argc; i++) {
        if (strcmp(argv[i], "--ply") == 0 && i + 1 < argc) {
            ply = atoi(argv[++i]);
        } else if (strcmp(argv[i], "--channel") == 0 && i + 1 < argc) {
            channel = argv[++i];
        } else if (argv[i][0] != '-' && !input) {
            input = argv[i];
        }
    }
    if (!input || ply < 0) {
        fprintf(stderr, "heatmap: usage: spectral heatmap <file> --ply N --channel A1\n");
        return 2;
    }
    int chan_idx = -1;
    for (int c = 0; c < 10; c++) {
        if (strcmp(channel, CS_CHANNELS[c].name) == 0) { chan_idx = c; break; }
    }
    if (chan_idx < 0) {
        fprintf(stderr, "heatmap: unknown channel '%s' (valid: A1,A2,B1,B2,E,F1,F2,F3,FA,FD)\n",
                channel);
        return 2;
    }

    FILE *fp = NULL;
    if (cs_open_read_transparent(input, &fp) != 0 || !fp) {
        fprintf(stderr, "heatmap: cannot open %s\n", input); return 3;
    }
    cs_file_header_t hdr;
    if (cs_file_read_header(fp, &hdr) != 0) {
        fclose(fp); fprintf(stderr, "heatmap: bad header\n"); return 3;
    }
    if ((uint32_t)ply >= hdr.n_plies) {
        fclose(fp);
        fprintf(stderr, "heatmap: ply %d out of range (n_plies=%u)\n",
                ply, hdr.n_plies);
        return 3;
    }
    if (cs_file_seek_frame(fp, (uint32_t)ply, &hdr) != 0) {
        fclose(fp); return 3;
    }
    cs_spectral_frame_t fr;
    if (cs_file_read_frame(fp, &fr) != 0) {
        fclose(fp); return 3;
    }
    fclose(fp);

    const float *block = &fr.encoding[CS_CHANNELS[chan_idx].start];
    double absmax = 0.0;
    for (int i = 0; i < 64; i++) {
        double a = fabs((double)block[i]);
        if (a > absmax) absmax = a;
    }
    if (absmax == 0.0) absmax = 1.0;  /* avoid division by zero */

    /* Map |value| / absmax → ANSI 256-color gradient (16..51 = blue->cyan->green->yellow->red).
     * Sign indicated by background color: + bright, - dim.
     * Convention: row 0 = rank 8 (matches encoder_512.py / cs_fen_parse). */
    printf("heatmap: %s ply=%u channel=%s absmax=%.4f\n",
           input, fr.ply, channel, absmax);
    for (int r = 0; r < 8; r++) {
        printf("  %d  ", 8 - r);
        for (int c = 0; c < 8; c++) {
            double v = (double)block[r * 8 + c];
            double a = fabs(v) / absmax;
            int bucket = (int)(a * 8.0);  /* 0..8 */
            if (bucket > 8) bucket = 8;
            const char *glyph = " .,:-=+*#@"[bucket] ? &" .,:-=+*#@"[bucket] : "@";
            char ch = glyph[0];
            int col = (v >= 0) ? 36 : 31;  /* cyan for +, red for - */
            printf("\x1b[%dm%c\x1b[0m ", col, ch);
        }
        printf("\n");
    }
    printf("     a b c d e f g h\n");
    return 0;
}

/* ─── analyze (per-game peaks/crises/complexity arc) ───────────────────── */

/* Per the chess_spectral_research_notebook.md §p.1636-1648 ("ΔA₁ derivative
 * analysis"), the canonical signals are:
 *   - A₁ peak ply: ply with max E_A1 (positions of highest complexity)
 *   - A₁ drop ply: ply with most-negative ΔA₁ (the simplification event,
 *     "complexity *break*"). The notebook table at p.1640-1646 is the
 *     reference output format.
 *   - Crisis ply: |drop_ply| with the largest magnitude ΔA₁.
 */
static int cmd_analyze(int argc, char **argv)
{
    const char *input = NULL;
    for (int i = 0; i < argc; i++) {
        if (argv[i][0] != '-' && !input) input = argv[i];
    }
    if (!input) {
        fprintf(stderr, "analyze: usage: spectral analyze <file.spectral[z]>\n");
        return 2;
    }
    FILE *fp = NULL;
    if (cs_open_read_transparent(input, &fp) != 0 || !fp) {
        fprintf(stderr, "analyze: cannot open %s\n", input); return 3;
    }
    cs_file_header_t hdr;
    if (cs_file_read_header(fp, &hdr) != 0) {
        fclose(fp); fprintf(stderr, "analyze: bad header\n"); return 3;
    }
    if (hdr.n_plies == 0) {
        fclose(fp); printf("{\"n_plies\":0}\n"); return 0;
    }

    double e_a1_peak = -1.0;
    uint32_t a1_peak_ply = 0;
    double dA1_drop = 0.0;       /* most-negative ΔA₁ */
    uint32_t dA1_drop_ply = 0;
    double abs_dA1_max = 0.0;     /* largest |ΔA₁| → "crisis" */
    uint32_t crisis_ply = 0;
    double e_total_max = 0.0;
    uint32_t e_total_max_ply = 0;

    cs_spectral_frame_t fr;
    float prev_a1[CS_BOARD_DIM];
    int have_prev = 0;

    for (uint32_t p = 0; p < hdr.n_plies; p++) {
        if (cs_file_read_frame(fp, &fr) != 0) break;
        double E_A1 = sum_sq_f(&fr.encoding[0], CS_BOARD_DIM);
        if (E_A1 > e_a1_peak) { e_a1_peak = E_A1; a1_peak_ply = fr.ply; }

        double E_total = 0.0;
        for (int c = 0; c < 10; c++) {
            E_total += sum_sq_f(&fr.encoding[CS_CHANNELS[c].start],
                                CS_BOARD_DIM);
        }
        if (E_total > e_total_max) {
            e_total_max = E_total; e_total_max_ply = fr.ply;
        }

        if (have_prev) {
            double ssq = 0.0;
            for (int i = 0; i < CS_BOARD_DIM; i++) {
                double d = (double)fr.encoding[i] - (double)prev_a1[i];
                ssq += d * d;
            }
            double dA1_signed = sqrt(ssq);
            /* sign: did the A₁ energy drop or rise? */
            double prev_E_A1 = sum_sq_f(prev_a1, CS_BOARD_DIM);
            if (E_A1 < prev_E_A1) dA1_signed = -dA1_signed;
            if (dA1_signed < dA1_drop) {
                dA1_drop = dA1_signed; dA1_drop_ply = fr.ply;
            }
            double abs_d = dA1_signed < 0 ? -dA1_signed : dA1_signed;
            if (abs_d > abs_dA1_max) {
                abs_dA1_max = abs_d; crisis_ply = fr.ply;
            }
        }
        memcpy(prev_a1, &fr.encoding[0], sizeof(prev_a1));
        have_prev = 1;
    }
    fclose(fp);

    /* Output as compact JSON for downstream tooling.
     * peak_ply + drop_ply + crisis_ply mirror the notebook §p.1640-1646
     * table columns; e_total_max_ply is added as a useful general signal. */
    printf("{\n");
    printf("  \"n_plies\":         %u,\n", hdr.n_plies);
    printf("  \"a1_peak_ply\":     %u,\n", a1_peak_ply);
    printf("  \"a1_peak_value\":   %.6f,\n", e_a1_peak);
    printf("  \"a1_drop_ply\":     %u,\n", dA1_drop_ply);
    printf("  \"a1_drop_value\":   %.6f,\n", dA1_drop);
    printf("  \"crisis_ply\":      %u,\n", crisis_ply);
    printf("  \"abs_dA1_max\":     %.6f,\n", abs_dA1_max);
    printf("  \"e_total_max_ply\": %u,\n", e_total_max_ply);
    printf("  \"e_total_max\":     %.6f\n", e_total_max);
    printf("}\n");
    return 0;
}

/* ─── export (.spectral → JSON for web viewer) ─────────────────────────── */

static int cmd_export(int argc, char **argv)
{
    const char *input = NULL;
    const char *output = NULL;
    for (int i = 0; i < argc; i++) {
        if ((strcmp(argv[i], "-o") == 0 || strcmp(argv[i], "--output") == 0)
            && i + 1 < argc) {
            output = argv[++i];
        } else if (argv[i][0] != '-' && !input) {
            input = argv[i];
        }
    }
    if (!input) {
        fprintf(stderr, "export: usage: spectral export <file.spectral[z]> [-o out.json]\n");
        return 2;
    }
    FILE *fp = NULL;
    if (cs_open_read_transparent(input, &fp) != 0 || !fp) {
        fprintf(stderr, "export: cannot open %s\n", input); return 3;
    }
    cs_file_header_t hdr;
    if (cs_file_read_header(fp, &hdr) != 0) {
        fclose(fp); fprintf(stderr, "export: bad header\n"); return 3;
    }
    FILE *fout = stdout;
    int close_fout = 0;
    if (output && strcmp(output, "-") != 0) {
        fout = fopen(output, "w");
        if (!fout) {
            fclose(fp); fprintf(stderr, "export: cannot create %s\n", output);
            return 3;
        }
        close_fout = 1;
    }

    /* JSON schema (for the web viewer at lemonforest.github.io/chess-maths-viewer):
     *   {"version": 2, "encoding_dim": 640, "n_plies": N,
     *    "channels": [{"name":"A1","start":0,"end":63}, ...],
     *    "frames": [{"ply":N, "move_from":0xFF, "move_to":0xFF,
     *                "channel_energies": {"A1": x, ...}, "encoding": [...]}, ...]}
     */
    fprintf(fout, "{\n");
    fprintf(fout, "  \"version\": %u,\n", hdr.version);
    fprintf(fout, "  \"encoding_dim\": %u,\n", hdr.encoding_dim);
    fprintf(fout, "  \"n_plies\": %u,\n", hdr.n_plies);
    fprintf(fout, "  \"channels\": [");
    for (int c = 0; c < 10; c++) {
        fprintf(fout, "%s{\"name\":\"%s\",\"start\":%d,\"end\":%d}",
                c == 0 ? "" : ",",
                CS_CHANNELS[c].name, CS_CHANNELS[c].start,
                CS_CHANNELS[c].start + CS_BOARD_DIM - 1);
    }
    fprintf(fout, "],\n  \"frames\": [");

    cs_spectral_frame_t fr;
    for (uint32_t p = 0; p < hdr.n_plies; p++) {
        if (cs_file_read_frame(fp, &fr) != 0) break;
        fprintf(fout, "%s\n    {", p == 0 ? "" : ",");
        fprintf(fout, "\"ply\":%u,\"move_from\":%u,\"move_to\":%u,",
                fr.ply, fr.move_from, fr.move_to);
        fprintf(fout, "\"promo\":%u,\"flags\":%u,",
                fr.move_promo, fr.move_flags);
        fprintf(fout, "\"channel_energies\":{");
        for (int c = 0; c < 10; c++) {
            double E = sum_sq_f(&fr.encoding[CS_CHANNELS[c].start],
                                CS_BOARD_DIM);
            fprintf(fout, "%s\"%s\":%.6f",
                    c == 0 ? "" : ",", CS_CHANNELS[c].name, E);
        }
        fprintf(fout, "},\"encoding\":[");
        for (int i = 0; i < CS_ENCODING_DIM; i++) {
            fprintf(fout, "%s%.6g",
                    i == 0 ? "" : ",", (double)fr.encoding[i]);
        }
        fprintf(fout, "]}");
    }
    fprintf(fout, "\n  ]\n}\n");

    fclose(fp);
    if (close_fout) fclose(fout);
    return 0;
}

/* ─── play (non-interactive ply-by-ply viewer) ─────────────────────────── */

/* Per the plan ("consider trimming to a non-interactive --ply N --next/--prev
 * style"), the v1.2.4 implementation is non-interactive: it lists all
 * plies with one-line summaries by default, or shows a single ply with
 * --ply N (delegates to query). Interactive mode is deferred. */
static int cmd_play(int argc, char **argv)
{
    const char *input = NULL;
    int ply = -1;
    for (int i = 0; i < argc; i++) {
        if (strcmp(argv[i], "--ply") == 0 && i + 1 < argc) {
            ply = atoi(argv[++i]);
        } else if (argv[i][0] != '-' && !input) {
            input = argv[i];
        }
    }
    if (!input) {
        fprintf(stderr, "play: usage: spectral play <file.spectral[z]> [--ply N]\n");
        return 2;
    }
    if (ply >= 0) {
        /* Single-ply mode delegates to query for the detailed breakdown. */
        char ply_str[32];
        snprintf(ply_str, sizeof(ply_str), "%d", ply);
        char *q_argv[] = { (char *)input, "--ply", ply_str, NULL };
        return cmd_query(3, q_argv);
    }

    /* List mode: one line per ply with E_total + dist_prev + cos_prev. */
    FILE *fp = NULL;
    if (cs_open_read_transparent(input, &fp) != 0 || !fp) {
        fprintf(stderr, "play: cannot open %s\n", input); return 3;
    }
    cs_file_header_t hdr;
    if (cs_file_read_header(fp, &hdr) != 0) {
        fclose(fp); fprintf(stderr, "play: bad header\n"); return 3;
    }
    printf("%-6s %-8s %-8s %-8s %-12s\n",
           "ply", "from", "to", "cos_prev", "E_total");
    cs_spectral_frame_t fr;
    float prev[CS_ENCODING_DIM];
    int have_prev = 0;
    for (uint32_t p = 0; p < hdr.n_plies; p++) {
        if (cs_file_read_frame(fp, &fr) != 0) break;
        double E = 0.0;
        for (int c = 0; c < 10; c++) {
            E += sum_sq_f(&fr.encoding[CS_CHANNELS[c].start], CS_BOARD_DIM);
        }
        double cos = 1.0;
        if (have_prev) {
            double dot = 0.0, n_a = 0.0, n_b = 0.0;
            for (int i = 0; i < CS_ENCODING_DIM; i++) {
                double a = (double)fr.encoding[i], b = (double)prev[i];
                dot += a * b; n_a += a * a; n_b += b * b;
            }
            double denom = sqrt(n_a) * sqrt(n_b);
            cos = denom > 0.0 ? dot / denom : 1.0;
        }
        printf("%-6u %-8u %-8u %-8.4f %-12.4f\n",
               fr.ply, fr.move_from, fr.move_to, cos, E);
        memcpy(prev, fr.encoding, sizeof(prev));
        have_prev = 1;
    }
    fclose(fp);
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
    if (strcmp(argv[1], "encode-fen") == 0) return cmd_encode_fen(argc - 2, argv + 2);
    if (strcmp(argv[1], "encode")     == 0) return cmd_encode    (argc - 2, argv + 2);
    if (strcmp(argv[1], "csv")        == 0) return cmd_csv       (argc - 2, argv + 2);
    if (strcmp(argv[1], "query")      == 0) return cmd_query  (argc - 2, argv + 2);
    if (strcmp(argv[1], "analyze")    == 0) return cmd_analyze (argc - 2, argv + 2);
    if (strcmp(argv[1], "compare")    == 0) return cmd_compare (argc - 2, argv + 2);
    if (strcmp(argv[1], "heatmap")    == 0) return cmd_heatmap (argc - 2, argv + 2);
    if (strcmp(argv[1], "play")       == 0) return cmd_play    (argc - 2, argv + 2);
    if (strcmp(argv[1], "export")     == 0) return cmd_export  (argc - 2, argv + 2);

    fprintf(stderr, "spectral: unknown command '%s'\n\n", argv[1]);
    print_usage(stderr);
    return 1;
}
