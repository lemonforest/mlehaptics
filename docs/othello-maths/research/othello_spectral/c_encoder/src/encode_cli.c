/* encode_cli.c — minimal CLI driver around othello_spectral_encode_768.
 *
 * Reads 64 bytes of state from stdin (each byte in {0xFF=-1, 0, 1})
 * or from an OBF string argument, encodes, and writes 768 float32
 * little-endian values to stdout.  Used by the Python/C parity
 * regression test.
 *
 * Usage:
 *   (a) --obf '<66-char OBF string>' : parse, encode, emit one frame
 *   (b) --stdin                      : read exactly 64 bytes of
 *                                       state from stdin, emit one
 *                                       frame of 3072 bytes
 *   (c) --stdin-stream               : read 64-byte states in a
 *                                       loop until EOF, emit one
 *                                       frame per input state.
 *                                       Used by the Python engine
 *                                       dispatcher to amortise
 *                                       subprocess startup over a
 *                                       whole corpus.
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

static int read_one_state(int8_t state[64])
{
    unsigned char buf[64];
    size_t got = fread(buf, 1, 64, stdin);
    if (got == 0) return 1;  /* EOF */
    if (got != 64) {
        fprintf(stderr, "short read: got %zu bytes\n", got);
        return -1;
    }
    for (size_t i = 0; i < 64; ++i) state[i] = (int8_t)buf[i];
    return 0;
}

int main(int argc, char **argv)
{
    int8_t state[64];
    enum { MODE_STDIN_ONE, MODE_STDIN_STREAM, MODE_OBF } mode = MODE_STDIN_ONE;
    const char *obf = NULL;
    int fiber_mode = OTHELLO_SPECTRAL_FIBER_RANK2;  /* rank2 default */

    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--stdin") == 0) {
            mode = MODE_STDIN_ONE;
        } else if (strcmp(argv[i], "--stdin-stream") == 0) {
            mode = MODE_STDIN_STREAM;
        } else if (strcmp(argv[i], "--obf") == 0 && i + 1 < argc) {
            mode = MODE_OBF;
            obf = argv[++i];
        } else if (strcmp(argv[i], "--fiber") == 0 && i + 1 < argc) {
            const char *f = argv[++i];
            if (strcmp(f, "rank2") == 0) {
                fiber_mode = OTHELLO_SPECTRAL_FIBER_RANK2;
            } else if (strcmp(f, "sheaf") == 0) {
                fiber_mode = OTHELLO_SPECTRAL_FIBER_SHEAF;
            } else {
                fprintf(stderr, "unknown --fiber %s\n", f);
                return 2;
            }
        } else if (strcmp(argv[i], "--version") == 0) {
            printf("%s\n", OTHELLO_SPECTRAL_VERSION);
            return 0;
        } else {
            fprintf(
                stderr,
                "usage: %s [--stdin | --stdin-stream | --obf <OBF>]"
                " [--fiber rank2|sheaf]\n",
                argv[0]);
            return 2;
        }
    }

    if (mode == MODE_STDIN_STREAM) {
        /* Streaming: read 64 bytes, encode, emit 3072 bytes; repeat
         * until EOF.  Used by the Python engine dispatcher to encode
         * many states through a single subprocess. */
#if defined(_WIN32)
        /* Windows: flip stdin/stdout to binary so CRLF translation
         * does not corrupt the state bytes or float32 output. */
        extern int _setmode(int, int);
        _setmode(0 /*stdin*/, 0x8000 /* _O_BINARY */);
        _setmode(1 /*stdout*/, 0x8000);
#endif
        for (;;) {
            int r = read_one_state(state);
            if (r == 1) break;      /* clean EOF */
            if (r != 0) return 3;
            double out[OTHELLO_SPECTRAL_ENCODING_DIM];
            int rc = othello_spectral_encode_768_v2(state, fiber_mode, out);
            if (rc != 0) {
                fprintf(stderr, "encode_768_v2 returned %d\n", rc);
                return 4;
            }
            for (size_t i = 0; i < OTHELLO_SPECTRAL_ENCODING_DIM; ++i) {
                write_f32_little_endian(out[i]);
            }
            fflush(stdout);
        }
        return 0;
    }

    if (mode == MODE_OBF) {
        if (obf_to_state(obf, state) != 0) return 3;
    } else {
        if (read_one_state(state) != 0) return 3;
    }

    double out[OTHELLO_SPECTRAL_ENCODING_DIM];
    int rc = othello_spectral_encode_768_v2(state, fiber_mode, out);
    if (rc != 0) {
        fprintf(stderr, "encode_768_v2 returned %d\n", rc);
        return 4;
    }

    for (size_t i = 0; i < OTHELLO_SPECTRAL_ENCODING_DIM; ++i) {
        write_f32_little_endian(out[i]);
    }
    fflush(stdout);
    return 0;
}
