/*
 * srmech — Stored-Relationship Mechanism C library
 *
 * C parity surface for the srmech package's AMSC framework. Ports
 * the three load-bearing primitives from `srmech.amsc.*` to native
 * code so srmech can take the same Python/C parity discipline that
 * ephemerides-spectral uses (Tasks #79, #80, #105–#110).
 *
 * What lives here (planned, per Task #201 Phase B3–B5):
 *   - srmech_sha256_bytes   (B3) — SHA-256 attestation hash.
 *   - srmech_ndjson_iter    (B4) — streaming NDJSON line reader.
 *   - srmech_toml_canonical (B5) — canonical-serialised TOML for
 *                                  descriptor_hash() byte-stable
 *                                  across whitespace edits.
 *
 * Targets: same cross-platform matrix as ephemerides-spectral —
 * Linux / macOS / Windows × x86_64 / arm64 × Py 3.10–3.14. Pure
 * Python fallback retained for Pyodide / WASM via the
 * `pyproject-pure.toml` build path (Phase B2).
 *
 * Phase B1 (this file) is a SCAFFOLD ONLY: header guards, version
 * macros, status enum, and forward-declared API. No symbols are
 * defined yet. Linking against this header at Phase B1 will not
 * resolve any function. The build infrastructure is wired in
 * Phase B2 (scikit-build-core + CMake); the first real symbol
 * lands in Phase B3 (sha256).
 *
 * Why C
 * -----
 * srmech is data-pipeline tooling, NOT embedded firmware. The C
 * port exists for:
 *   1. Parity discipline with ephemerides-spectral (which needs C
 *      for its ESP32 / Cortex-M targets) so the monorepo's two
 *      spectral-research packages share one quality bar.
 *   2. Performance on hot paths — every catalog read goes through
 *      NDJSON streaming; every descriptor edit recomputes the
 *      canonical-serialised TOML hash; SHA-256 is called per row
 *      at codegen time. The Python paths stay correct; C is the
 *      fast path runtime can opt into.
 *   3. JPL Power-of-Ten discipline (Phase B6) as a structural
 *      quality ratchet, mirroring Tasks #105–#110.
 *
 * License: GPL-3.0-or-later (parent project: mlehaptics).
 */

#ifndef SRMECH_H
#define SRMECH_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ------------------------------------------------------------------ *
 * Version
 *
 * Mirrors srmech.version.__version__ in the Python tree. The publish
 * workflow asserts agreement between this constant and the Python
 * version at tag time; mismatch fails the publish.
 * ------------------------------------------------------------------ */
#define SRMECH_VERSION_MAJOR 0
#define SRMECH_VERSION_MINOR 1
#define SRMECH_VERSION_PATCH 1
#define SRMECH_VERSION_PRE   "rc8"
#define SRMECH_VERSION       "0.1.1rc8"

/* ABI version. Bumped in lockstep with the Python shim's
 * EXPECTED_ABI_VERSION whenever the wire format of any exported
 * function changes. Adding a NEW symbol does not bump ABI; changing
 * an existing signature does.
 *
 * v1 — Phase B3 baseline: srmech_sha256_hex.
 * v2 — Phase B4: srmech_ndjson_iter callback signature gained
 *      `size_t lineno` param so callback-side errors can report
 *      file-relative line numbers without a side channel. Pure
 *      addition; srmech_sha256_hex unchanged. ABI bumped because
 *      the callback typedef wire-format changed.
 */
#define SRMECH_ABI_VERSION 2

/* ------------------------------------------------------------------ *
 * Status codes
 *
 * Every srmech_* API returns srmech_status_t. SRMECH_OK is zero so
 * `if (st)` reads as error-handling. Non-zero values are stable
 * across patch releases and form part of the wire contract with the
 * Python ctypes binding.
 * ------------------------------------------------------------------ */
typedef enum srmech_status {
    SRMECH_OK             = 0,
    SRMECH_ERR_NULL_ARG   = 1,  /* a required pointer was NULL    */
    SRMECH_ERR_BAD_INPUT  = 2,  /* malformed input bytes / state  */
    SRMECH_ERR_IO         = 3,  /* file / stream I/O failed       */
    SRMECH_ERR_OVERFLOW   = 4,  /* bounded buffer overflow guard  */
    SRMECH_ERR_NOT_IMPL   = 5,  /* not yet implemented (Phase B1) */
    SRMECH_ERR_INTERNAL   = 6   /* invariant violation; report it */
} srmech_status_t;

/* ------------------------------------------------------------------ *
 * Metadata accessors (defined in src/srmech_meta.c)
 *
 * Called by the Python ctypes shim at load time to verify version +
 * ABI agreement before binding the rest of the API.
 * ------------------------------------------------------------------ */
const char *srmech_version(void);
int         srmech_abi_version(void);

/* ------------------------------------------------------------------ *
 * Public API (Phase B3+)
 * ------------------------------------------------------------------ */

/* B3: SHA-256 over an arbitrary byte buffer. Writes 64 lowercase hex
 *     chars + NUL into `out_hex`. `out_hex` must point to at least
 *     65 bytes. Byte-exact with hashlib.sha256(data).hexdigest(). */
srmech_status_t srmech_sha256_hex(const uint8_t *data,
                                  size_t         data_len,
                                  char          *out_hex);

/* B4: NDJSON streaming line iterator. Caller provides a file path
 *     and a per-line callback; srmech_ndjson_iter walks the file
 *     line by line and invokes the callback for every non-empty
 *     line. Empty lines (zero-length after CR-stripping) are
 *     skipped silently — they don't trigger the callback but the
 *     lineno counter still advances, so callback-side error
 *     messages line up byte-exactly with the file.
 *
 *     `line` points into srmech's static line-assembly buffer and
 *     is valid only for the duration of the callback. `line_len`
 *     excludes the terminating LF and any trailing CR (mirrors
 *     Python's `raw.rstrip("\r\n")`).
 *
 *     `lineno` is 1-indexed over ALL lines in the file (including
 *     the skipped empties); callers can use it directly in error
 *     messages.
 *
 *     SINGLE-THREAD CONTRACT: srmech_ndjson_iter uses a static
 *     1 MiB line-assembly buffer, so it is not safe to call from
 *     two threads concurrently. (The two callsites in srmech today
 *     — Python format.read_ndjson + the C-side parity test —
 *     are both serial.)
 *
 *     Error returns:
 *       SRMECH_ERR_NULL_ARG     — path or cb is NULL
 *       SRMECH_ERR_IO           — fopen / fread failed
 *       SRMECH_ERR_OVERFLOW     — line exceeds SRMECH_NDJSON_MAX_LINE_BYTES
 *       <cb return value>       — propagated if cb returns non-OK
 */
typedef srmech_status_t (*srmech_ndjson_line_cb)(const char *line,
                                                 size_t      line_len,
                                                 size_t      lineno,
                                                 void       *user);
srmech_status_t srmech_ndjson_iter(const char            *path,
                                   srmech_ndjson_line_cb  cb,
                                   void                  *user);

/* B5 (planned): Canonical-serialised TOML hash. Re-emits the parsed
 *     TOML with sorted keys + normalised whitespace, then SHA-256s
 *     the result. Output is 64 lowercase hex chars + NUL into
 *     `out_hex`. */
srmech_status_t srmech_toml_canonical_hash(const char *toml_path,
                                           char       *out_hex);

#ifdef __cplusplus
}
#endif

#endif /* SRMECH_H */
