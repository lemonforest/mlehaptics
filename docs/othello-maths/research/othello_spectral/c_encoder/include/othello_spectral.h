/* othello_spectral.h — ANSI C17 reference encoder API (stub).
 *
 * Goal: bit-identical output to othello_spectral.encoder.encode_768
 * in Python.  This header declares the public API; the Python side
 * owns the source of truth for the tables (see codegen/emit_c_tables.py).
 *
 * Status: scaffold.  The encode_768 function is a stub; the table
 * header is generated on demand by the Python codegen.  See
 * ../../c_encoder/README.md for the bring-up plan.
 *
 * License: GPL-3.0-or-later (parent project).
 */
#ifndef OTHELLO_SPECTRAL_H
#define OTHELLO_SPECTRAL_H

#include <stdint.h>
#include <stddef.h>

#include "othello_spectral_tables.h"

/* Export annotation for Windows DLL builds.  On non-Windows or
 * static builds the macro is a no-op.  clang on Windows builds a
 * DLL when -shared is passed; in that case we must explicitly
 * tag the public symbols as exported, otherwise they are not in
 * the DLL's export table and ctypes can't find them. */
#if defined(_WIN32)
#  if defined(OTHELLO_SPECTRAL_STATIC)
#    define OTHELLO_API
#  else
#    define OTHELLO_API __declspec(dllexport)
#  endif
#else
#  define OTHELLO_API __attribute__((visibility("default")))
#endif

#ifdef __cplusplus
extern "C" {
#endif

/* ---------------------------------------------------------------------
 * Public constants (also available as #define from the tables header).
 * --------------------------------------------------------------------- */

/* Encoding dimension in float64 units.  Always 768 at v0.2.0. */
extern const size_t othello_spectral_encoding_dim;

/* Number of named channels (12 at v0.2.0). */
extern const size_t othello_spectral_n_channels;

/* Encoder semver string; matches Python __version__. */
extern const char *const othello_spectral_version;

/* ---------------------------------------------------------------------
 * Encoder
 * --------------------------------------------------------------------- */

/* Encode a 64-cell Blume-Capel state (row-major, values in {-1, 0, +1})
 * into a 768-dim float64 vector.
 *
 * Parameters:
 *   state  : length-64 array of int8_t in {-1, 0, +1}
 *   out    : length-768 array of double, caller-allocated
 *
 * Return:
 *   0      on success
 *   nonzero on invalid input (e.g. state value outside {-1, 0, +1})
 *
 * Bit-identical parity with Python encode_768 is the correctness
 * invariant.  See tests/test_c_py_parity (to be added) for the
 * fixture-based regression.
 */
OTHELLO_API int othello_spectral_encode_768(
    const int8_t state[64],
    double out[OTHELLO_SPECTRAL_ENCODING_DIM]);

/* Compute per-channel squared-norm energies (||channel_block||^2).
 * Caller allocates ``out`` with n_channels entries in encoder order. */
OTHELLO_API int othello_spectral_channel_energies(
    const double enc[OTHELLO_SPECTRAL_ENCODING_DIM],
    double out[OTHELLO_SPECTRAL_N_CHANNELS]);

/* ---------------------------------------------------------------------
 * Binary frame I/O (.spectralz format)
 *
 * Write a single frame to a pre-opened FILE* in the little-endian
 * float32 format described in frame.py (772 bytes per frame).
 * The caller owns the file handle and header bookkeeping.
 * --------------------------------------------------------------------- */

struct othello_spectral_frame {
    double data[OTHELLO_SPECTRAL_ENCODING_DIM];  /* encoder output */
    uint32_t ply;                                 /* frame index */
};

#ifdef __cplusplus
}
#endif

#endif /* OTHELLO_SPECTRAL_H */
