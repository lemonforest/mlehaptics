/* othello_spectral.c — ANSI C17 reference encoder (stub).
 *
 * Bit-identical target for othello_spectral.encoder.encode_768.
 *
 * This file is a STUB.  It compiles but does not yet produce correct
 * output.  The implementation intentionally mirrors the Python
 * encoder's math step by step so a future build can diff-test the
 * intermediate signals against Python at every block boundary.
 *
 * TODO list (bring-up order):
 *   1. Run `python -m othello_spectral.codegen.emit_c_tables` to
 *      materialise include/othello_spectral_tables.h.
 *   2. Implement encode_768 using the generated projector tables
 *      and L_ortho / L_diag matrices.  Apply as
 *        out[k*64..(k+1)*64) = PROJECTORS[k] @ signal
 *      where signal = state (int8 cast to double) for channels 0..4
 *      and signal = state * state for channels 5..9; fiber blocks
 *      are L_ortho/L_diag @ state respectively.
 *   3. Verify bit-identical output against Python on the Barcelona
 *      fixture (35 games, 2184 frames; 6.72 MB .spectralz).
 *   4. Add frame write routine that matches frame.py's little-
 *      endian float32 layout exactly.
 *
 * Compilation (when ready):
 *   cc -std=c17 -Wall -Wextra -O2 -I include \
 *      src/othello_spectral.c -o othello_spectral
 *
 * Current behaviour: encode_768 zeroes the output and returns 1
 * (not implemented).  Channel energies return a consistent all-zero
 * result for that output.  Callers can compile-test the API but
 * MUST NOT rely on the output until stub bodies are filled in.
 *
 * License: GPL-3.0-or-later (parent project).
 */

#include "othello_spectral.h"

#include <string.h>

/* Public version / dim constants duplicated here for linkage. */
const size_t othello_spectral_encoding_dim  = OTHELLO_SPECTRAL_ENCODING_DIM;
const size_t othello_spectral_n_channels    = OTHELLO_SPECTRAL_N_CHANNELS;
const char *const othello_spectral_version  = OTHELLO_SPECTRAL_VERSION;

int othello_spectral_encode_768(
    const int8_t state[64],
    double out[OTHELLO_SPECTRAL_ENCODING_DIM])
{
    if (state == NULL || out == NULL) {
        return -1;
    }

    /* Validate input and cast to double.  The encoder operates on
     * float64 throughout; state values must be in {-1, 0, +1}. */
    double sig[64];
    double occ[64];
    for (size_t i = 0; i < 64; ++i) {
        int8_t v = state[i];
        if (v != -1 && v != 0 && v != 1) {
            return -2;
        }
        sig[i] = (double)v;
        occ[i] = sig[i] * sig[i];
    }

    /* Zero the output block. */
    memset(out, 0, sizeof(double) * OTHELLO_SPECTRAL_ENCODING_DIM);

    /* Channels 0..4: five D4xZ2 '-' irreps applied to magnetisation.
     * Channels 5..9: five D4   irreps applied to occupation s^2.
     * Both are stored in PROJECTORS[10][64][64] in encoder-channel
     * order.  For each channel, the output block is PROJ @ signal. */
    for (size_t ch = 0; ch < 10; ++ch) {
        const double *signal = (ch < 5) ? sig : occ;
        double *block = &out[ch * 64];
        for (size_t i = 0; i < 64; ++i) {
            double s = 0.0;
            for (size_t j = 0; j < 64; ++j) {
                s += OTHELLO_SPECTRAL_PROJECTORS[ch][i][j] * signal[j];
            }
            block[i] = s;
        }
    }

    /* Channel 10: L_ortho @ sig. */
    for (size_t i = 0; i < 64; ++i) {
        double s = 0.0;
        for (size_t j = 0; j < 64; ++j) {
            s += OTHELLO_SPECTRAL_L_ORTHO[i][j] * sig[j];
        }
        out[640 + i] = s;
    }

    /* Channel 11: L_diag @ sig. */
    for (size_t i = 0; i < 64; ++i) {
        double s = 0.0;
        for (size_t j = 0; j < 64; ++j) {
            s += OTHELLO_SPECTRAL_L_DIAG[i][j] * sig[j];
        }
        out[704 + i] = s;
    }

    return 0;
}

int othello_spectral_channel_energies(
    const double enc[OTHELLO_SPECTRAL_ENCODING_DIM],
    double out[OTHELLO_SPECTRAL_N_CHANNELS])
{
    if (enc == NULL || out == NULL) {
        return -1;
    }
    /* For each of the N_CHANNELS blocks, compute ||block||^2. */
    for (size_t ch = 0; ch < OTHELLO_SPECTRAL_N_CHANNELS; ++ch) {
        double sum = 0.0;
        for (size_t j = 0; j < 64; ++j) {
            double v = enc[ch * 64 + j];
            sum += v * v;
        }
        out[ch] = sum;
    }
    return 0;
}
