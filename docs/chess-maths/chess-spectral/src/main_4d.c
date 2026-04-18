/* main_4d.c — `spectral_4d` CLI entry point.
 *
 * Mirrors the 2D `spectral` binary's manual argv strcmp dispatch style
 * (see src/main.c). Subcommands:
 *   version     — print encoder dims + channel layout
 *   help        — usage banner
 *   encode-fen4 — [P2a stub] parity smoke-test entry
 *   encode      — [P5]      NDJSON4 → .spectralz4 bulk encoding
 *   csv         — [P5]      per-ply channel energies
 *
 * P2a scope: only `version` and `help` actually do work. `encode-fen4`
 * prints a clear TODO and exits 4 (matches 2D stub contract) until the
 * P2b JSONL-fixture ingestion path lands and/or a FEN4 grammar is defined.
 */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "cs_encoder_4d.h"

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
        "    version      Print encoder version and dimensions\n"
        "    help         Print this message\n"
        "    encode-fen4  [stub — see plan, requires FEN4 parser]\n"
        "    encode       [stub — P5]  NDJSON4 → .spectralz4 bulk encoding\n"
        "    csv          [stub — P5]  Per-ply channel energies (CSV)\n"
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
    if (strcmp(argv[1], "encode-fen4") == 0) return cmd_todo("encode-fen4");
    if (strcmp(argv[1], "encode")      == 0) return cmd_todo("encode");
    if (strcmp(argv[1], "csv")         == 0) return cmd_todo("csv");

    fprintf(stderr, "spectral_4d: unknown command '%s'\n\n", argv[1]);
    print_usage(stderr);
    return 1;
}
