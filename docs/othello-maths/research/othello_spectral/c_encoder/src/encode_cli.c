/* encode_cli.c — minimal CLI driver around othello_spectral_encode_768.
 *
 * Reads 64 bytes of state from stdin (each byte in {0xFF=-1, 0, 1})
 * or from an OBF string argument, encodes, and writes 768 float32
 * little-endian values to stdout.  Used by the Python/C parity
 * regression test.
 *
 * Usage:
 *   (a) --obf '<66-char OBF string>' : parse then encode
 *   (b) --stdin                      : read 64 bytes of signed state
 *                                       from stdin, encode to stdout
 *
 * Build:
 *   cc -std=c17 -Wall -Wextra -O2 -I include \
 *      src/othello_spectral.c src/encode_cli.c -o encode_cli
 *
 * Output layout: 768 little-endian IEEE 754 float32 values (3072
 * bytes total), suitable for byte-for-byte comparison against the
 * float32-cast output of the Python encoder.
 */

#include "othello_spectral.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int obf_to_state(const char *obf, int8_t state[64])
{
    /* OBF format: 64 chars for board + ' ' + 'X'|'O' + ';' */
    size_t n = strlen(obf);
    if (n < 66 || obf[64] != ' ' || (obf[65] != 'X' && obf[65] != 'O')) {
        fprintf(stderr, "bad OBF string length=%zu\n", n);
        return -1;
    }
    for (size_t i = 0; i < 64; ++i) {
        char c = obf[i];
        if (c == '-') {
            state[i] = 0;
        } else if (c == 'X') {
            state[i] = 1;
        } else if (c == 'O') {
            state[i] = -1;
        } else {
            fprintf(stderr, "bad OBF char '%c' at %zu\n", c, i);
            return -1;
        }
    }
    return 0;
}

static int read_state_stdin(int8_t state[64])
{
    /* Read 64 bytes, interpret as int8_t.  Little-endian machines
     * can memcpy; portability-minded code should read one byte at
     * a time. */
    unsigned char buf[64];
    size_t got = fread(buf, 1, 64, stdin);
    if (got != 64) {
        fprintf(stderr, "read_state_stdin: got %zu bytes, wanted 64\n", got);
        return -1;
    }
    for (size_t i = 0; i < 64; ++i) {
        state[i] = (int8_t)buf[i];
    }
    return 0;
}

static void write_f32_little_endian(double value)
{
    float f = (float)value;
    unsigned char bytes[4];
    memcpy(bytes, &f, 4);
    /* Assume host is little-endian.  If building on a big-endian
     * target, byte-swap explicitly; tests will catch the mismatch.
     */
    fwrite(bytes, 1, 4, stdout);
}

int main(int argc, char **argv)
{
    int8_t state[64];
    int input_mode = 0;  /* 0 = stdin, 1 = obf */
    const char *obf = NULL;

    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--stdin") == 0) {
            input_mode = 0;
        } else if (strcmp(argv[i], "--obf") == 0 && i + 1 < argc) {
            input_mode = 1;
            obf = argv[++i];
        } else if (strcmp(argv[i], "--version") == 0) {
            printf("%s\n", OTHELLO_SPECTRAL_VERSION);
            return 0;
        } else {
            fprintf(stderr, "usage: %s [--stdin | --obf <OBF>]\n", argv[0]);
            return 2;
        }
    }

    if (input_mode == 1) {
        if (obf_to_state(obf, state) != 0) return 3;
    } else {
        if (read_state_stdin(state) != 0) return 3;
    }

    double out[OTHELLO_SPECTRAL_ENCODING_DIM];
    int rc = othello_spectral_encode_768(state, out);
    if (rc != 0) {
        fprintf(stderr, "encode_768 returned %d\n", rc);
        return 4;
    }

    for (size_t i = 0; i < OTHELLO_SPECTRAL_ENCODING_DIM; ++i) {
        write_f32_little_endian(out[i]);
    }
    fflush(stdout);
    return 0;
}
