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

/* ========================================================================
 * Faithful-sheaf bracket classifier + per-cell pending counts
 *
 * Ports faithful_sheaf.classify_ray + the pending-count extraction
 * used in encode_768(fiber_mode="sheaf").  Bit-identical to the
 * Python reference: identical control flow, identical integer
 * arithmetic, identical per-cell increments.
 * ======================================================================== */

/* 8 ray directions in (dr, dc) form.  Order matches Python's
 * othello_utils.RAY_OFFSETS dict iteration order:
 *   N, NE, E, SE, S, SW, W, NW                                          */
static const int RAY_DR[8] = { -1, -1,  0,  1,  1,  1,  0, -1 };
static const int RAY_DC[8] = {  0,  1,  1,  1,  0, -1, -1, -1 };

/* Bracket-classification codes.  Match Python faithful_sheaf module. */
#define R1_NONE      0
#define R2_COMPLETE  1
#define R3_PENDING   2
#define R4_OPEN      3

/* Classify the ray starting at (v_row, v_col) stepping by (dr, dc).
 *
 * Returns the R{1..4} classification code.  On R2_COMPLETE and
 * R3_PENDING, writes the opponent-run cell linear indices into
 * opp_out[] and the count into *n_opp_out.  Max ray length on an
 * 8x8 board from any cell is 7, so opp_out has capacity 7.
 *
 * Direct port of faithful_sheaf.classify_ray — same control flow,
 * same early-exit conditions. */
static int classify_ray(
    const int8_t state[64],
    int v_idx,
    int dr, int dc,
    int opp_out[7],
    int *n_opp_out)
{
    int v_row = v_idx / 8;
    int v_col = v_idx % 8;
    int v_val = (int)state[v_idx];
    *n_opp_out = 0;
    if (v_val == 0) {
        return R1_NONE;
    }
    int r = v_row + dr;
    int c = v_col + dc;
    while (r >= 0 && r < 8 && c >= 0 && c < 8) {
        int w_idx = r * 8 + c;
        int w_val = (int)state[w_idx];
        if (w_val == 0) {
            /* opp run + empty => pending, if run is non-empty */
            return (*n_opp_out > 0) ? R3_PENDING : R1_NONE;
        }
        if (w_val == v_val) {
            /* opp run + friendly close => complete */
            return (*n_opp_out > 0) ? R2_COMPLETE : R1_NONE;
        }
        /* w is opposite-colour: append to opp run, continue walk */
        opp_out[*n_opp_out] = w_idx;
        *n_opp_out += 1;
        r += dr;
        c += dc;
    }
    /* Ran off the board with (possibly) an opp run => open */
    return R4_OPEN;
}

/* Compute per-cell R3_PENDING bracket counts for both owners.
 *
 * pending_black[i] = number of R3_PENDING brackets cell i
 *                     participates in (as origin or opp-run member)
 *                     from the black owner's perspective.
 * pending_white[i] = same, white owner.
 *
 * Direct port of the loop body in encoder._sheaf_fiber_channels.
 * Iterates (cell, direction) for every non-empty cell. */
static void sheaf_pending_counts(
    const int8_t state[64],
    double pending_black[64],
    double pending_white[64])
{
    memset(pending_black, 0, sizeof(double) * 64);
    memset(pending_white, 0, sizeof(double) * 64);
    int opp_buf[7];
    int n_opp = 0;
    for (int v = 0; v < 64; ++v) {
        int s_v = (int)state[v];
        if (s_v == 0) {
            continue;
        }
        for (int d = 0; d < 8; ++d) {
            int cls = classify_ray(
                state, v, RAY_DR[d], RAY_DC[d], opp_buf, &n_opp
            );
            if (cls != R3_PENDING) {
                continue;
            }
            double *target = (s_v == 1) ? pending_black : pending_white;
            target[v] += 1.0;
            for (int k = 0; k < n_opp; ++k) {
                target[opp_buf[k]] += 1.0;
            }
        }
    }
}


int othello_spectral_encode_768_v2(
    const int8_t state[64],
    int fiber_mode,
    double out[OTHELLO_SPECTRAL_ENCODING_DIM])
{
    if (state == NULL || out == NULL) {
        return -1;
    }
    if (fiber_mode != OTHELLO_SPECTRAL_FIBER_RANK2 &&
        fiber_mode != OTHELLO_SPECTRAL_FIBER_SHEAF) {
        return -3;
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
     * Channels 5..9: five D4   irreps applied to occupation s^2. */
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

    /* Channels 10-11: fiber, mode-dependent. */
    if (fiber_mode == OTHELLO_SPECTRAL_FIBER_RANK2) {
        /* v0.2.0: L_ortho @ sig, L_diag @ sig. */
        for (size_t i = 0; i < 64; ++i) {
            double so = 0.0, sd = 0.0;
            for (size_t j = 0; j < 64; ++j) {
                so += OTHELLO_SPECTRAL_L_ORTHO[i][j] * sig[j];
                sd += OTHELLO_SPECTRAL_L_DIAG[i][j]  * sig[j];
            }
            out[640 + i] = so;
            out[704 + i] = sd;
        }
    } else {
        /* v0.3.0: per-cell R3_PENDING counts from faithful sheaf. */
        double pend_b[64], pend_w[64];
        sheaf_pending_counts(state, pend_b, pend_w);
        for (size_t i = 0; i < 64; ++i) {
            out[640 + i] = pend_b[i];
            out[704 + i] = pend_w[i];
        }
    }

    return 0;
}

int othello_spectral_encode_768(
    const int8_t state[64],
    double out[OTHELLO_SPECTRAL_ENCODING_DIM])
{
    /* Legacy alias: rank-2 fiber (v0.2.0 semantics). */
    return othello_spectral_encode_768_v2(
        state, OTHELLO_SPECTRAL_FIBER_RANK2, out
    );
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
