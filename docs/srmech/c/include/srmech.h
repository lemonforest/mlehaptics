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
#define SRMECH_VERSION_MINOR 7
#define SRMECH_VERSION_PATCH 3
#define SRMECH_VERSION_PRE   ""
#define SRMECH_VERSION       "0.7.3"

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
 * v3 — v0.5.0rc2: srmech_bus_* C peer for srmech.bus cross-process
 *      IPC, including the new function-pointer typedef
 *      srmech_bus_handler_callback_t. Adding a typedef carries a
 *      wire-format implication for the Python ctypes shim
 *      (CFUNCTYPE construction), so ABI bumps even though no
 *      existing function signature changed.
 */
#define SRMECH_ABI_VERSION 3

/* ------------------------------------------------------------------ *
 * Thread-local storage qualifier (reentrancy support; #772)
 *
 * SRMECH_THREAD_LOCAL expands to the platform's thread-local-storage
 * keyword. C11 `_Thread_local` on conforming compilers; MSVC's
 * `__declspec(thread)` on Microsoft toolchains that predate full C11
 * TLS support. Each is Rule-3-clean (static-duration, no malloc) and
 * gives every thread its own copy of the qualified object, so a
 * thread-local-static scratch buffer is reentrant ACROSS threads —
 * exactly what the #771 multi-threaded plugin needs without risking a
 * stack overflow from a large per-call frame.
 *
 * This is a single-token object-like macro (JPL Rule 8 clean: no
 * token-paste, no varargs, no line continuation).
 * ------------------------------------------------------------------ */
#if defined(_MSC_VER)
#define SRMECH_THREAD_LOCAL __declspec(thread)
#elif defined(__STDC_VERSION__) && (__STDC_VERSION__ >= 201112L)
#define SRMECH_THREAD_LOCAL _Thread_local
#elif defined(__GNUC__)
#define SRMECH_THREAD_LOCAL __thread
#else
#define SRMECH_THREAD_LOCAL
#endif

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

/* F292 graft #1 (v0.7.0rc10): N-way SIMD SHA-256 BATCH. Hashes `n`
 * independent messages — msgs[i] points to lens[i] bytes (msgs[i] may be
 * NULL iff lens[i]==0); writes the raw 32-byte digest of message i into
 * out_digests[i*32 ..]. out_digests must be n*32 bytes and must NOT alias
 * any input. Bit-exact with srmech_sha256_hex / hashlib per message; on
 * x86 it dispatches at runtime to AVX2 8-way / SSE2 4-way and falls back
 * to the scalar path (remainder, non-x86, Pyodide). The
 * SRMECH_SHA256_FORCE_TIER env-var ({0,1,2}) overrides the dispatch (test
 * hook). New symbol only — ABI stays 3. */
srmech_status_t srmech_sha256_batch(const uint8_t *const *msgs,
                                    const size_t         *lens,
                                    size_t                n,
                                    uint8_t              *out_digests);

/* F292 graft #3 (v0.7.0rc19): SHA-NI SINGLE-STREAM SHA-256. Hashes ONE
 * message — `data` points to `len` bytes (data may be NULL iff len==0) —
 * and writes the RAW 32-byte digest into out_digest[0..31] (out_digest must
 * be 32 bytes and must NOT alias data). Bit-exact with srmech_sha256_hex /
 * hashlib. On x86 with the Intel SHA Extensions present it runs the SHA-NI
 * rnds2/msg1/msg2 kernel; hosts without the feature (and non-x86 / Pyodide)
 * take the scalar path. The kernel is NEVER entered unless cpuid confirms
 * SHA-NI, so the SRMECH_SHANI_FORCE_TIER env-var ({0,1}) test hook can only
 * select scalar-or-(SHA-NI-if-present) — it can never SIGILL. New symbol
 * only — ABI stays 3. */
srmech_status_t srmech_sha256_shani(const uint8_t *data,
                                    size_t         len,
                                    uint8_t       *out_digest);

/* B4: NDJSON streaming line iterator. Caller provides a file path
 *     and a per-line callback; srmech_ndjson_iter walks the file
 *     line by line and invokes the callback for every non-empty
 *     line. Empty lines (zero-length after CR-stripping) are
 *     skipped silently — they don't trigger the callback but the
 *     lineno counter still advances, so callback-side error
 *     messages line up byte-exactly with the file.
 *
 *     `line` points into srmech's per-thread line-assembly buffer
 *     and is valid only for the duration of the callback. `line_len`
 *     excludes the terminating LF and any trailing CR (mirrors
 *     Python's `raw.rstrip("\r\n")`).
 *
 *     `lineno` is 1-indexed over ALL lines in the file (including
 *     the skipped empties); callers can use it directly in error
 *     messages.
 *
 *     REENTRANCY (#772): the 1 MiB line-assembly buffer is a
 *     function-local `static SRMECH_THREAD_LOCAL` buffer, so
 *     srmech_ndjson_iter is safe to call from multiple threads
 *     concurrently — each thread owns its own buffer. (Recursive
 *     re-entry on the SAME thread, e.g. calling srmech_ndjson_iter
 *     from inside its own callback, would still reuse that thread's
 *     buffer — not a supported usage.)
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

/* ------------------------------------------------------------------ *
 * Cascade catalog — cross-domain named cascades
 *
 * Each cascade op composes the existing 14-class A–N primitive
 * vocabulary into a recurring named pattern (per the cascade-catalog
 * discipline: a named cascade is the default, a math-library call the
 * exception). Cascades carry their own C symbols for full C/Python
 * parity per the project's full-coverage discipline, AND ship as TOML
 * descriptors under srmech/amsc/_research/cascade_catalog/ for
 * declarative composition.
 *
 * v0.4.5rc1: chiral_flip — Class C orientation reversal.
 * v0.4.5rc2: pin_slot_at_zero — Class K pin-slot at zero (sign-strip).
 * v0.4.5rc3: magnitude — Class K pin-slot magnitude-only projection.
 * v0.4.5rc4: reorient — Class C cascade-orientation re-application.
 * v0.4.5rc5: net_chirality — Class C net handedness invariant.
 * v0.4.5rc6: cyclic_gcd — Class I cyclic-group gcd (cascade-namespace
 *            wrapper; delegates to the Class I primitive srmech_gcd).
 *            FIRST of the delegating cascade ops.
 * v0.4.5rc7: best_rational_signed — Class K ∘ Class N ∘ Class C.
 *            Multi-class cascade combining Class K pin-slot (sign-strip)
 *            + Class N best-rational anchor (delegates to srmech_best_rational)
 *            + Class C re-orientation (sign re-apply on the numerator).
 * v0.4.5rc8: chiral_dual — HIGHER-ORDER Class C ∘ op ∘ Class C
 *            conjugation. Takes a function-pointer callback for the
 *            inner op (the cascade catalog accepts arbitrary callables
 *            for op per the project discipline — Class-ID enum dispatch
 *            would have broken the public API contract). Wraps the
 *            existing rc1 chiral_flip C peer on both sides. CLOSES the
 *            cascade-catalog C-parity arc (8 of 8); after this all 8
 *            cascade ops have full C/Python parity + TOML descriptors.
 * ------------------------------------------------------------------ */

/* chiral_flip: Class C orientation reversal of a sequence (the value-
 * level Class C cascade-orientation operator; reverses traversal order).
 * Reversing a real signal is the FFT-level chirality operator: same
 * magnitude spectrum, orientation-flipped phase (MFO §VIII.31.11 §(5b)).
 *
 * Two typed variants — cascade inputs are heterogeneous (int sequences
 * from cyclic-group land, float sequences from spectral land); each
 * caller picks the matching ABI. `in` and `out` may alias (the impl
 * supports in-place reversal); `n == 0` is allowed and is a no-op.
 *
 * Error returns:
 *   SRMECH_OK              — success
 *   SRMECH_ERR_NULL_ARG    — in or out is NULL with n > 0
 */
srmech_status_t srmech_cascade_chiral_flip_i64(const int64_t *in,
                                                size_t         n,
                                                int64_t       *out);

srmech_status_t srmech_cascade_chiral_flip_f64(const double *in,
                                                size_t        n,
                                                double       *out);

/* pin_slot_at_zero: Class K pin-slot at zero — split a real value into
 * (orientation, magnitude). orientation in {-1, 0, +1}; magnitude >= 0.0.
 * The sign-flip IS the canonical Class K phase-boundary; expressing this
 * as a named cascade (rather than C99 fabs()) keeps the cascade-count
 * claimed in line with the cascade-count executed.
 *
 * f64-only — scalar floats are the cascade-hot path (best_rational_signed,
 * magnitude). Integer pin-slot is trivial and not catalogued.
 *
 * NaN handling: a NaN input fails both `x > 0.0` and `x < 0.0`, so it
 * falls through to the dead-band branch and maps to (0, 0.0). This
 * preserves bit-parity with the Python reference impl where
 * `NaN > 0.0` and `NaN < 0.0` both evaluate False. +/-Inf map to
 * (+/-1, +Inf) — the comparison branches do the right thing.
 *
 * Error returns:
 *   SRMECH_OK              — success
 *   SRMECH_ERR_NULL_ARG    — orientation_out or magnitude_out is NULL
 */
srmech_status_t srmech_cascade_pin_slot_at_zero_f64(double  x,
                                                     int8_t *orientation_out,
                                                     double *magnitude_out);

/* magnitude: Class K pin-slot magnitude-only projection — |x| but
 * cascade-honest (composes pin_slot_at_zero, discards orientation).
 * The replacement for C99 fabs() inside cascade code: keeps the
 * cascade-count claimed in line with the cascade-count executed.
 *
 * NaN maps to the dead-band 0.0 (parity with the Python reference:
 * pin_slot_at_zero(nan) -> (0, 0.0), so magnitude(nan) -> 0.0).
 * +/-Inf preserve magnitude: magnitude(+inf) = magnitude(-inf) = +inf.
 *
 * Error returns:
 *   SRMECH_OK              — success
 *   SRMECH_ERR_NULL_ARG    — magnitude_out is NULL
 */
srmech_status_t srmech_cascade_magnitude_f64(double  x,
                                              double *magnitude_out);

/* reorient: Class C cascade-orientation — re-apply a captured
 * orientation to a value. orientation must be in {-1, 0, +1}; the
 * value is negated iff orientation < 0 (zero and positive orientation
 * both return the value unchanged — only the SIGN of orientation
 * matters, mirroring the Python reference).
 *
 * Two typed variants — reorient is type-preserving (Python preserves
 * int vs float through the operation), so the caller picks the matching
 * ABI for whichever scalar type the cascade is carrying.
 *
 * NaN/Inf handling (f64): NaN and +/-Inf pass through unchanged when
 * orientation >= 0; NaN is negated to NaN (still NaN — sign bit irrelevant
 * for NaN equality) and +/-Inf flip to mp/+Inf when orientation < 0,
 * matching IEEE-754 negation semantics and Python's -nan / -inf behaviour.
 *
 * Error returns:
 *   SRMECH_OK              — success
 *   SRMECH_ERR_NULL_ARG    — out is NULL
 */
srmech_status_t srmech_cascade_reorient_i64(int8_t   orientation,
                                             int64_t  value,
                                             int64_t *out);

srmech_status_t srmech_cascade_reorient_f64(int8_t   orientation,
                                             double   value,
                                             double  *out);

/* net_chirality: Class C net handedness invariant — multiplicative
 * product of per-op orientations in {-1, 0, +1}.
 *
 * Empty input (n == 0) returns +1 (the multiplicative identity, matching
 * Python where the loop doesn't execute). Any orientation of 0 in the
 * sequence short-circuits the result to 0 (a zero-crossing collapses
 * net handedness). Otherwise the result is +1 (even count of -1s) or
 * -1 (odd count). Orientations are int8; any value not in {-1, 0, +1}
 * is normalised by sign (negative -> -1, positive -> +1, zero -> 0),
 * matching the Python ref where only the sign of each o matters.
 *
 * Error returns:
 *   SRMECH_OK              — success
 *   SRMECH_ERR_NULL_ARG    — orientations is NULL with n > 0, or out is NULL
 */
srmech_status_t srmech_cascade_net_chirality_i8(const int8_t *orientations,
                                                  size_t        n,
                                                  int8_t       *out);

/* cyclic_gcd: Class I cyclic-group gcd, cascade-namespace wrapper.
 *
 * The cascade-catalog entry for cyclic_gcd IS the Class I primitive
 * gcd (Euclidean algorithm). This wrapper exists to maintain the
 * srmech_cascade_* namespace invariant: every cascade-catalog entry
 * ships a srmech_cascade_* C symbol, even when the math lives at
 * the Class I primitive level. Internally delegates to the existing
 * srmech_gcd primitive (Task #217 Phase C1 rc1; declared below).
 *
 * Signature mirrors the Class I primitive exactly: uint64 inputs,
 * uint64 output via pointer, srmech_status_t returned. The cascade
 * Python ref (cascade.py:cyclic_gcd) is a thin pass-through to
 * srmech.amsc.cyclic.gcd which itself enforces non-negative uint64
 * range — so the cascade C wrapper is intentionally uint64 too;
 * negative / out-of-range inputs are rejected at the Python dispatch
 * layer and never reach the C wrapper.
 *
 * Conventional gcd(0, 0) = 0; gcd(a, 0) = a (matches srmech_gcd).
 *
 * Error returns:
 *   SRMECH_OK              — success
 *   SRMECH_ERR_NULL_ARG    — out is NULL
 *   (any other status propagated from the underlying srmech_gcd)
 */
srmech_status_t srmech_cascade_cyclic_gcd_u64(uint64_t  a,
                                                uint64_t  b,
                                                uint64_t *out);

/* best_rational_signed: Class K ∘ Class N ∘ Class C — float to signed
 * small-denominator rational. Cascade-namespace wrapper around the
 * existing Class N best_rational primitive with the Class K pin-slot
 * strip + Class C orientation-re-apply on the numerator.
 *
 * Stages:
 *   Class K: (orientation, magnitude) <- pin_slot_at_zero(x)
 *   Class N: (num_pos, den) <- best_rational(round(magnitude * fine_scale),
 *                                              fine_scale, max_denominator)
 *   Class C: out_num <- (orientation < 0) ? -num_pos : num_pos
 *
 * Output: (out_num, out_den) where out_den >= 1 and out_num has the
 * sign of x. Origin and sub-dead-band magnitudes (< 1e-12) map to
 * (0, 1). NaN maps to (0, 1) via the Class K dead-band (both `x > 0`
 * and `x < 0` evaluate false for NaN under IEEE-754).
 *
 * Rounding: the magnitude * fine_scale product is rounded to int64 via
 * llrint() under the default IEEE-754 FE_TONEAREST mode (round-half-to-
 * even / banker's rounding) — this matches Python's built-in round() at
 * the .5 boundary bit-exactly. C99 round() is round-half-AWAY-from-zero
 * and would diverge from Python at the boundary; llrint() with default
 * fenv is the canonical match.
 *
 * Error returns:
 *   SRMECH_OK              — success
 *   SRMECH_ERR_NULL_ARG    — out_num or out_den is NULL
 *   SRMECH_ERR_BAD_INPUT   — max_denominator < 1 or fine_scale < 1
 *   (any other status propagated from the underlying srmech_best_rational)
 */
srmech_status_t srmech_cascade_best_rational_signed_f64(
    double    x,
    int64_t   max_denominator,
    int64_t   fine_scale,
    int64_t  *out_num,
    int64_t  *out_den);

/* ------------------------------------------------------------------ *
 * chiral_dual — HIGHER-ORDER Class C ∘ op ∘ Class C conjugation
 *
 * Closes the cascade-catalog C-parity arc (v0.4.5rc8; op 8 of 8).
 * Higher-order: takes a function-pointer callback for the inner op.
 * Wraps the existing rc1 chiral_flip C peer on both sides.
 *
 * Algorithm:
 *   workspace = chiral_flip(in)
 *   out       = op(workspace, user_data)
 *   out       = chiral_flip(out)            // in-place via rc1
 *
 * The cascade preserves spectral magnitude and inverts phase
 * orientation (verified across 14 A–N operators in
 * docs/srmech/notes/spike_chiral_an_spectral_shape.py; MFO §VIII.31.11
 * §(5b)/(5c)).
 *
 * Memory: workspace MUST be caller-allocated with capacity >= n
 * doubles. No malloc inside libsrmech (JPL Rule 3).
 *
 * Why a function-pointer callback (Option A) and NOT a Class-ID enum
 * dispatch (Option B): the cascade catalog accepts arbitrary callables
 * for op per the public API contract; restricting chiral_dual to known
 * A–N srmech ops via an enum would break that contract. Option A
 * preserves the contract; the only Python ↔ C boundary is the callback
 * (wrapped via ctypes.CFUNCTYPE on the Python side).
 *
 * Error returns:
 *   SRMECH_OK              — success
 *   SRMECH_ERR_NULL_ARG    — op or out is NULL, or in/workspace is NULL
 *                            while n > 0
 *   (any other status propagated from the op callback or from the
 *   underlying srmech_cascade_chiral_flip_f64)
 * ------------------------------------------------------------------ */

/* Callback signature: unary op on f64 sequences. user_data is opaque
 * caller-supplied context (typically used by the Python ctypes layer
 * to identify which Python callable to invoke; the Python ref captures
 * the Python op via closure and passes NULL here). */
typedef srmech_status_t (*srmech_cascade_op_callback_f64_t)(
    const double *in,
    size_t        n,
    double       *out,
    void         *user_data);

srmech_status_t srmech_cascade_chiral_dual_f64(
    srmech_cascade_op_callback_f64_t op,
    void                              *user_data,
    const double                     *in,
    size_t                            n,
    double                           *out,
    double                           *workspace);

/* ------------------------------------------------------------------ *
 * Klein-4 four-sector PARALLEL cascade dispatch — C-orchestration
 * parity for the rc6 Python parallel_sector_dispatch (#771; MS#20 rc7).
 *
 * Runs ONE caller-supplied cascade `body` across its ≤4 Klein-4
 * chirality sectors and writes the four sector duals. This is the
 * native four-sector dispatch so srmech does NOT need a host Python to
 * run the four-sector cascade — a thread-less microcontroller still
 * gets all four sectors (serially; see THREADING below).
 *
 * THE FOUR SECTORS (mirror rc6 §1). Each sector `s` runs the SAME
 * `body` conjugated by its Klein-4 stream-transform T_s (the sector
 * dual T_s(body(T_s(in))), each T_s an involution so inv_T_s == T_s):
 *   s0 (+,+) identity;  s1 (+,−) iω₇-flip (per-element reorient(-1, .));
 *   s2 (−,+) γ₅-flip (chiral_flip) — its dual IS
 *      srmech_cascade_chiral_dual_f64;  s3 (−,−) both / CPT mirror.
 * Composes the EXISTING C atoms (srmech_cascade_chiral_flip_f64 +
 * srmech_cascade_reorient_f64) — no atom is reimplemented.
 *
 * BUFFER LAYOUT (caller-supplied; NO malloc, JPL Rule 3):
 *   - out_sectors : n_sectors * n doubles. Sector s occupies the
 *                   disjoint slice [s*n .. s*n + n).
 *   - scratch     : n_sectors * n doubles. Sector s uses ONLY its own
 *                   disjoint slice [s*n .. s*n + n) for the T_s(in)
 *                   intermediate. `scratch_len` (in doubles) must be
 *                   >= n_sectors * n (validated; SRMECH_ERR_OVERFLOW
 *                   otherwise).
 * Each sector writes ONLY its own out + scratch slice and reads only
 * the shared read-only `in` — 0 cross-thread writes (the F233 4-way
 * independence). That disjointness is what makes the threaded path
 * correct: the sectors are order-free, so the SERIAL result equals the
 * THREADED result BIT-FOR-BIT.
 *
 * THREADING (portable shim, guarded like srmech_bus.c):
 *   POSIX   -> pthread_create / pthread_join;
 *   Windows -> CreateThread / WaitForMultipleObjects;
 *   else    -> SERIAL fallback (compute the ≤4 sectors in a loop).
 * The serial fallback PRESERVES the capability (all 4 sectors computed,
 * bit-identical). Concurrency is platform-gated; thread handles are a
 * fixed-size [4] stack array (no malloc).
 *
 * CAP AT 4 (F220): n_sectors must be in 1..4. Klein-4 = Z₂ × Z₂ has no
 * order-4+ element; past 4 needs the order-3 triality (F220) — not
 * here. n_sectors > 4 returns SRMECH_ERR_BAD_INPUT.
 *
 * Error returns:
 *   SRMECH_OK              — success
 *   SRMECH_ERR_NULL_ARG    — body / out_sectors / scratch is NULL, or
 *                            in is NULL while n > 0
 *   SRMECH_ERR_BAD_INPUT   — n_sectors < 1 or n_sectors > 4
 *   SRMECH_ERR_OVERFLOW    — scratch_len < n_sectors * n
 *   (any other status propagated from the `body` callback)
 *
 * ABI-additive: a new symbol + typedef + macro, so SRMECH_ABI_VERSION
 * stays 3.
 * ------------------------------------------------------------------ */

/* Klein-4 has order 4 — the dispatch is hard-capped at 4 sectors
 * (single-token object-like macro; JPL Rule 8 clean). */
#define SRMECH_PARALLEL_SECTOR_CAP 4

/* Cascade `body` callback: a unary op on an f64 sequence. `out` (n
 * doubles, caller-allocated) receives body(in). `user` is opaque
 * caller-supplied context. Returns SRMECH_OK on success. Same shape as
 * srmech_cascade_op_callback_f64_t but named for the dispatch role. */
typedef srmech_status_t (*srmech_cascade_body_f64)(
    const double *in, size_t n, double *out, void *user);

srmech_status_t srmech_cascade_parallel_sector_dispatch(
    srmech_cascade_body_f64 body, void *user,
    const double *in, size_t n,
    uint32_t n_sectors,            /* 1..4 */
    double  *out_sectors,          /* n_sectors * n doubles; sector s at [s*n ..) */
    double  *scratch, size_t scratch_len); /* per-sector scratch; NO malloc */

/* ------------------------------------------------------------------ *
 * Kuramoto coupled-oscillator forward-Euler step (#778 follow-on).
 *
 * One forward-Euler step of the canonical Kuramoto model (Kuramoto
 * 1975; Acebrón et al. 2005, Rev. Mod. Phys. 77:137):
 *
 *     out[i] = theta[i] + dt * ( omega[i]
 *                                + (coupling_k / n) * Σ_j sin(theta[j] - theta[i]) )
 *
 * Closes a C/Python parity gap — the dispatch-clock Euler integration
 * the spectral-research arc hand-rolled in Python (F141 / F231 / R-95 /
 * F234) now has a native step. Composes existing class operations
 * (Class I cyclic phase + sin coupling + sum-reduce + Class-C Euler
 * add); NOT a new privileged primitive. Uses libm sin (as
 * srmech_kepler.c does). No abs().
 *
 * Buffers: reads `theta`/`omega` (n doubles each), writes `out` (n
 * doubles, caller-allocated). `out` MUST NOT alias `theta` or `omega`.
 * Pure / reentrant (no shared static state).
 *
 * n == 0 is a no-op returning SRMECH_OK. n == 1 has an empty coupling
 * sum (Σ sin(0) over the self-term cancels), so out[0] = theta[0] +
 * dt*omega[0] — pure drift, as expected.
 *
 * Returns:
 *   SRMECH_OK              — success
 *   SRMECH_ERR_NULL_ARG    — out is NULL, or theta/omega is NULL while n > 0
 *
 * ABI-additive: a new symbol, so SRMECH_ABI_VERSION stays 3.
 * ------------------------------------------------------------------ */
srmech_status_t srmech_cascade_kuramoto_step_f64(
    const double *theta, const double *omega, size_t n,
    double coupling_k, double dt,
    double *out);                  /* n doubles; MUST NOT alias theta/omega */

/* ------------------------------------------------------------------ *
 * GENERALISED Kuramoto-Sakaguchi forward-Euler step (v0.6.0rc14; §11.1).
 *
 *   dθ_i/dt = ω_i + Σ_j A_ij·sin(θ_j − θ_i − α) [ + p_i·sin(ψ_i − θ_i) ]
 *   θ_i(t+dt) = θ_i(t) + dt·[ above ]
 *
 * `adjacency` is ROW-MAJOR n×n (A_ij = weight of oscillator j on i): a
 * non-symmetric matrix expresses DIRECTED / one-way coupling, a graph
 * Laplacian expresses graph-structured coupling. `adjacency == NULL` ⇒
 * every weight is the uniform mean-field K/N (so NULL adjacency + α=0 +
 * NULL pin_anchor reproduces srmech_cascade_kuramoto_step_f64 exactly).
 * `alpha` is the Sakaguchi phase frustration. `pin_anchor` (NULL ⇒ no
 * pinning) is n anchor phases ψ; `pin_strength` (NULL ⇒ unit) is n
 * per-oscillator strengths p. No abs().
 *
 * Returns:
 *   SRMECH_OK              — success
 *   SRMECH_ERR_NULL_ARG    — out NULL, or theta/omega NULL while n > 0
 *
 * ABI-additive: a new symbol, so SRMECH_ABI_VERSION stays 3.
 * `out` MUST NOT alias theta / omega / adjacency / pin_anchor / pin_strength.
 * ------------------------------------------------------------------ */
srmech_status_t srmech_cascade_kuramoto_step_general_f64(
    const double *theta, const double *omega, size_t n,
    const double *adjacency, double coupling_k, double alpha,
    const double *pin_anchor, const double *pin_strength,
    double dt, double *out);

/* ------------------------------------------------------------------ *
 * Octonion "loop-bind" Moufang family (MS#21 v0.7.0rc7)
 *
 * C parity for srmech.amsc.hdc's dim-8 octonion (Cayley-Dickson)
 * product loop_bind and companions. The carrier is the OCTONION: every
 * `n` argument MUST equal 8 (the dim where division still holds); other
 * dimensions return SRMECH_ERR_BAD_INPUT and the Python keeps its
 * recursive fallback. The product matches hdc._loop_bind_raw exactly:
 *   (a, b)(c, d) = (a c - conj(d) b,  d a + b conj(c))
 * unrolled real -> complex -> quaternion -> octonion (no recursion).
 *
 * The HD block variants each have a native whole-array C peer too —
 * srmech_loop_bind_hd_f64 (below; N-way SIMD) plus the rc20 family
 * srmech_loop_{conj,inv,unbind,runbind}_hd_f64 (srmech_loophd_family.c) —
 * so EVERY Python loop op has a C-source transpile (the "C = transpiled
 * Python" Rosetta discipline; notebook §3.29.4). The Python wrappers
 * dispatch to those peers and keep a per-8-block pure-Python fallback for
 * Pyodide / WASM, looping the per-block loop_bind / loop_conj here.
 *
 * Returns:
 *   SRMECH_OK              — success
 *   SRMECH_ERR_NULL_ARG    — a required pointer was NULL
 *   SRMECH_ERR_BAD_INPUT   — n != 8, or (loop_inv) a zero vector
 *
 * ABI-additive: new symbols only, so SRMECH_ABI_VERSION stays 3.
 * `out` MUST NOT alias the inputs. No abs() (Class-K sign = conj flip).
 * ------------------------------------------------------------------ */

/* The octonion product x·y (Class M ∘ Class-C ordering). 8 doubles. */
srmech_status_t srmech_loop_bind_f64(
    const double *x, const double *y, size_t n, double *out);

/* Octonion conjugate x̄ — keep x[0], negate the imaginary part (Class C). */
srmech_status_t srmech_loop_conj_f64(
    const double *x, size_t n, double *out);

/* Moufang inverse x⁻¹ = x̄ / <x,x> (Class-K clean; the norm² gate). */
srmech_status_t srmech_loop_inv_f64(
    const double *x, size_t n, double *out);

/* 7-D cross product x×y = Im(loop_bind(x, y)) (drop the e0 anchor). */
srmech_status_t srmech_cross7_f64(
    const double *x, const double *y, size_t n, double *out);

/* G2 associative calibration 3-form φ(x,y,z) = <x, cross7(y, z)>. The
 * scalar result is written to *out (a single double). */
srmech_status_t srmech_g2_three_form_f64(
    const double *x, const double *y, const double *z, size_t n,
    double *out);

/* Class-K associator residue (a·b)·c − a·(b·c) (8 doubles out; the (4:3)|
 * (3:4) non-associativity). MS#21 v0.7.0rc21 — completes the #814 op-spec
 * C/Python parity (left_op/right_op/associator were pure-Python composites). */
srmech_status_t srmech_loop_associator_f64(
    const double *a, const double *b, const double *c, size_t n, double *out);

/* Left/right multiplication operator matrices L_a (col k = a·e_k) and R_a
 * (col k = e_k·a). `out` is n*n doubles, row-major (out[i*n+k]), byte-matching
 * numpy column_stack of the per-basis binds. ABI-additive — stays 3. */
srmech_status_t srmech_loop_left_op_f64(
    const double *a, size_t n, double *out);
srmech_status_t srmech_loop_right_op_f64(
    const double *a, size_t n, double *out);

/* ------------------------------------------------------------------ *
 * Block-diagonal HD loop-bind, N-way SIMD (MS#21 v0.7.0rc17; F292 #2)
 *
 * out[k] = loop_bind(x[k], y[k]) over nb INDEPENDENT 8-blocks (the
 * block-diagonal ⊕ F289 verified err 0.0). x, y, out are each nb*8
 * doubles; LOOP_DIM is fixed at 8. This is the data-parallel shape the
 * cpuminer N-way-SIMD mindset exploits — nb independent octonion units
 * advanced across SIMD lanes in ONE C call (was a Python per-block loop).
 * Runtime-dispatched AVX (256-bit double, W=4 blocks/pass; note: AVX, not
 * AVX2) / SSE2 (W=2) / scalar remainder reusing srmech_loop_bind_f64 (so
 * the scalar tier is bit-exact with the single-block product). The SIMD
 * tiers mirror the same Cayley-Dickson op-DAG per lane, so each lane is
 * bit-exact modulo a possible FMA-contraction 1-ULP (parity at ~1e-12).
 * SRMECH_LOOP_HD_FORCE_TIER={0,1,2} overrides dispatch (test hook).
 *
 * Returns:
 *   SRMECH_OK              — success (nb == 0 is a no-op)
 *   SRMECH_ERR_NULL_ARG    — x, y, or out is NULL with nb > 0
 *
 * `out` MUST NOT alias x or y. ABI-additive — SRMECH_ABI_VERSION stays 3.
 * No abs() (Class-K sign = conj flip, same as the per-block product).
 * ------------------------------------------------------------------ */
srmech_status_t srmech_loop_bind_hd_f64(
    const double *x, const double *y, size_t nb, double *out);

/* ------------------------------------------------------------------ *
 * The rest of the HD loop family — whole-array C peers (MS#21 v0.7.0rc20)
 *
 * The faithful transpile of the Python per-block wrappers (hdc.py
 * loop_{conj,inv,unbind,runbind}_hd): the SHIPPED per-block symbol applied
 * over nb INDEPENDENT dim-8 blocks (the block-diagonal ⊕, #811/F289),
 * collapsing the Python per-block loop into ONE native call. Completes the
 * "C = transpiled Python" Rosetta parity (notebook §3.29.4) — no HD loop op
 * is Python-only. Scalar (no N-way SIMD; the bind owns that, above); the
 * heavy step where present is the per-block product, already native.
 *
 * Each is nb*8 doubles per buffer; LOOP_DIM is fixed at 8; `out` MUST NOT
 * alias the inputs; nb == 0 is a no-op. conj/unbind/runbind = Class C ∘
 * Class M; inv = Class-K clean (norm² gate, never abs()). NO new class.
 *
 * Returns:
 *   SRMECH_OK              — success
 *   SRMECH_ERR_NULL_ARG    — a required pointer was NULL with nb > 0
 *   SRMECH_ERR_BAD_INPUT   — (loop_inv_hd) a zero block has no inverse
 *
 * ABI-additive: new symbols only, so SRMECH_ABI_VERSION stays 3.
 * ------------------------------------------------------------------ */

/* Per-block HD conjugate: out[k] = conj(x[k]) over nb dim-8 blocks. */
srmech_status_t srmech_loop_conj_hd_f64(
    const double *x, size_t nb, double *out);

/* Per-block HD Moufang inverse: out[k] = conj(x[k]) / <x[k],x[k]>. */
srmech_status_t srmech_loop_inv_hd_f64(
    const double *x, size_t nb, double *out);

/* Per-block HD LEFT-unbind (left-division): out[k] = conj(a[k])·b[k]. */
srmech_status_t srmech_loop_unbind_hd_f64(
    const double *a, const double *b, size_t nb, double *out);

/* Per-block HD RIGHT-unbind (right-division): out[k] = b[k]·conj(a[k]). */
srmech_status_t srmech_loop_runbind_hd_f64(
    const double *a, const double *b, size_t nb, double *out);

/* ------------------------------------------------------------------ *
 * Class L — autocorrelation (MS#21 v0.7.0rc8; the F290 §C primitive)
 *
 * The circular autocorrelation r[k] = Σ_i x[i]·x[(i+k) mod n] (r[0] = Σx² =
 * energy). This is the Wiener-Khinchin spectral object r = Re(IFFT(|FFT|²))
 * — that identity is WHY it is Class L (autocorrelation ↔ power spectrum) —
 * but the C peer computes the DIRECT O(n²) sum, which is the same object and
 * needs NO FFT (so no recursion, no transcendentals; JPL-clean). The Python
 * wrapper uses the fast numpy FFT route + dispatches here for the embedded /
 * full-parity path. Parity to FFT roundoff (~1e-12). `out` (n doubles) MUST
 * NOT alias `x`. n == 0 -> no-op. ABI-additive — SRMECH_ABI_VERSION stays 3.
 * ------------------------------------------------------------------ */
srmech_status_t srmech_autocorrelation_f64(
    const double *x, size_t n, double *out);

/* ------------------------------------------------------------------ *
 * Class I — cyclic-group / modular arithmetic (Task #217 Phase C1)
 *
 * Six load-bearing modular-arithmetic primitives on uint64_t. These
 * are the foundation for cyclic-cascade composition (Task #218
 * Phase C2's MFO/SM/QM operations layer). Every cyclic factor C_n in
 * a cascade exposes order, mode-index arithmetic, and period
 * operations that ultimately reduce to the six primitives here.
 *
 * Range: all functions operate on uint64_t inputs. `srmech_mod_inv`
 * additionally requires `n <= INT64_MAX` because the extended-
 * Euclidean coefficients use int64 intermediates (returns
 * SRMECH_ERR_OVERFLOW for larger n).
 *
 * No ABI bump: all symbols below are new additions to ABI v2; adding
 * a new symbol does not bump ABI per the Phase B4 convention.
 * ------------------------------------------------------------------ */

/* gcd(a, b) = greatest common divisor. Conventional gcd(0,0) = 0;
 * gcd(a, 0) = a. */
srmech_status_t srmech_gcd(uint64_t a, uint64_t b, uint64_t *out);

/* lcm(a, b) = least common multiple. Returns 0 when a == 0 or b == 0.
 * Returns SRMECH_ERR_OVERFLOW when `a / gcd(a, b) * b` exceeds
 * UINT64_MAX. */
srmech_status_t srmech_lcm(uint64_t a, uint64_t b, uint64_t *out);

/* (a + b) mod n. Overflow-safe (handles a, b > UINT64_MAX/2).
 * Returns SRMECH_ERR_BAD_INPUT for n == 0. */
srmech_status_t srmech_mod_add(uint64_t a, uint64_t b, uint64_t n,
                               uint64_t *out);

/* (a * b) mod n. Overflow-safe via russian-peasant doubling (portable
 * to platforms without __int128 / _umul128).
 * Returns SRMECH_ERR_BAD_INPUT for n == 0. */
srmech_status_t srmech_mod_mul(uint64_t a, uint64_t b, uint64_t n,
                               uint64_t *out);

/* (a^k) mod n via square-and-multiply. Returns 0 for n == 1.
 * Returns SRMECH_ERR_BAD_INPUT for n == 0. */
srmech_status_t srmech_mod_pow(uint64_t a, uint64_t k, uint64_t n,
                               uint64_t *out);

/* Modular inverse of a in Z/nZ via extended Euclidean. Requires
 * `gcd(a, n) == 1` (returns SRMECH_ERR_BAD_INPUT otherwise) and
 * `n <= INT64_MAX` (returns SRMECH_ERR_OVERFLOW otherwise).
 * Returns SRMECH_ERR_BAD_INPUT for n in {0, 1}. */
srmech_status_t srmech_mod_inv(uint64_t a, uint64_t n, uint64_t *out);

/* Harmonic-3 Z/3 generator (F150): *out = (value + 1) mod 3, read on
 * the residue class of value. Result is always in {0, 1, 2}; applying
 * it three times is the identity on each residue (period 3). */
srmech_status_t srmech_three_cycle(uint64_t value, uint64_t *out);

/* ------------------------------------------------------------------ *
 * Class L — graph Laplacian (Task #217 Phase C1)
 *
 * Four load-bearing graph-Laplacian primitives on row-major dense
 * double matrices. Class L is Spike #24's structural workhorse
 * (instantiated at six of six bonus substrates). Pi-free implementation
 * per `[[user_stance_pi_as_projection]]`: cyclic-graph closed-form
 * spectra (the pi-bearing `2(1-cos(2πk/n))` shortcut) are NOT shipped
 * on the C surface — those are downstream projections of Class I's
 * integer-cyclic upstream.
 *
 * Conventions:
 *   - Matrices: row-major n×n doubles, caller-allocated.
 *   - Edge lists: parallel uint32 arrays edges_u / edges_v + optional
 *     double weights (NULL = unit weights).
 *   - N bound: srmech_graph_dense_laplacian / normalized_laplacian /
 *     jacobi_eigvals stack-allocate degree/scaling buffers; n is
 *     bounded by SRMECH_LAPLACIAN_MAX_NODES (256, embedded-safe).
 *     Larger graphs return SRMECH_ERR_OVERFLOW; Python falls back to
 *     numpy.linalg.eigvalsh.
 *
 * No ABI bump: pure additions to ABI v2 per the Phase B4 convention.
 * ------------------------------------------------------------------ */

#define SRMECH_LAPLACIAN_MAX_NODES 256

/* A from edge list. A[u,v] = A[v,u] = sum of weights of edges between u
 * and v. Self-loops add 2*w to the diagonal (standard convention).
 * out_matrix is n*n doubles, row-major. */
srmech_status_t srmech_graph_dense_adjacency(uint32_t        n,
                                             uint32_t        n_edges,
                                             const uint32_t *edges_u,
                                             const uint32_t *edges_v,
                                             const double   *weights,
                                             double         *out_matrix);

/* L = D - A. Same edge-list inputs; n bounded by
 * SRMECH_LAPLACIAN_MAX_NODES for the stack-allocated degree buffer. */
srmech_status_t srmech_graph_dense_laplacian(uint32_t        n,
                                             uint32_t        n_edges,
                                             const uint32_t *edges_u,
                                             const uint32_t *edges_v,
                                             const double   *weights,
                                             double         *out_matrix);

/* L_sym = I - D^(-1/2) A D^(-1/2). Isolated vertices (degree 0) have
 * diagonal entry 0. n bounded by SRMECH_LAPLACIAN_MAX_NODES. */
srmech_status_t srmech_graph_normalized_laplacian(uint32_t        n,
                                                  uint32_t        n_edges,
                                                  const uint32_t *edges_u,
                                                  const uint32_t *edges_v,
                                                  const double   *weights,
                                                  double         *out_matrix);

/* Symmetric Jacobi eigendecomposition. In-place: `matrix` becomes
 * approximately diagonal at exit (caller-owned working buffer). The
 * `out_eigvals` array receives the n diagonal entries (unsorted).
 * max_sweeps = 0 selects SRMECH_LAPLACIAN_JACOBI_MAX_SWEEPS (100).
 * tolerance is the off-diagonal Frobenius norm threshold relative to
 * the initial off-diagonal norm. Pi-free: c, s computed algebraically
 * from matrix entries (no trig calls). */
srmech_status_t srmech_jacobi_eigvals(uint32_t  n,
                                      double   *matrix,
                                      uint32_t  max_sweeps,
                                      double    tolerance,
                                      double   *out_eigvals);

/* Harmonic-3 three-fold band split (F150): partition n eigenvectors into
 * contiguous low/mid/high bands. base = n/3; the remainder (n mod 3) rows go
 * to the later bands so *out_low <= *out_mid <= *out_high and the three sum
 * to n. Bit-exact with the Python three_fold_eigvec_groups band sizing.
 * ABI-additive: a new symbol, so SRMECH_ABI_VERSION stays 3. */
srmech_status_t srmech_three_fold_bands(uint32_t n, uint32_t *out_low,
                                        uint32_t *out_mid, uint32_t *out_high);

/* ------------------------------------------------------------------ *
 * Class L broadening — ADR-0002 Phase 2 (Task #225, srmech v0.4.1rc5).
 *
 * Per the ADR-0002 Phase 1 spike finding (TDSE evolution
 * `ψ(t) = V·diag(exp(-iλt))·V^H·ψ(0)` from Sakurai §2.1.5 eq 2.1.40),
 * Class L's identity broadens from "graph Laplacian" to "dense-matrix
 * linear algebra including eigendecomposition + matrix-vector
 * multiplication + elementwise operations". The four ops below extend
 * the Class L C surface to accommodate complex Hermitian eigen-
 * decomposition + dense complex matvec + elementwise complex multiply
 * + array-vectorised transcendentals. Per
 * [[feedback_no_privileged_primitive_classes]]: dissolve-before-promote;
 * no Class P promoted. Vocabulary stays at 14 classes A–N.
 *
 * Complex numbers travel as interleaved-double pairs (re, im, re, im, ...)
 * to keep the ctypes surface and embedded-target portability simple
 * (no <complex.h> across the FFI boundary). Length n complex vector =
 * 2n doubles; n×n complex matrix = 2*n*n doubles row-major.
 *
 * Canonical SSoT per [[feedback_science_is_ssot_not_project]]:
 *   - Hermitian eigendecomposition: Golub & Van Loan, *Matrix
 *     Computations* (4th ed., Johns Hopkins, 2013) §8.4 (Jacobi)
 *     and §8.5 (Hermitian-specific via unitary rotations).
 *   - Matrix-vector multiplication: Golub & Van Loan §1.1.
 *   - Elementwise transcendentals: ANSI C99 §7.12 (libm `exp`, `cos`,
 *     `sin`, `log`).
 *
 * No ABI bump: pure additions to ABI v2 per the Phase B4 convention.
 * ------------------------------------------------------------------ */

/* Transcendental op-id enum for srmech_elementwise_transcendental. */
#define SRMECH_TRANS_EXP 0
#define SRMECH_TRANS_COS 1
#define SRMECH_TRANS_SIN 2
#define SRMECH_TRANS_LOG 3

/* Hermitian eigendecomposition via complex-Jacobi rotations.
 * Input: H_interleaved is n*n interleaved-doubles (re, im pairs),
 *   row-major; MUST be Hermitian (caller's responsibility — checked
 *   only via assert in debug builds).
 * Output: out_eigvals = n real ascending-sorted eigenvalues;
 *   out_eigvecs_interleaved = n*n complex unitary matrix V (columns
 *   are eigenvectors). H = V * diag(eigvals) * V^H.
 * n is bounded by SRMECH_LAPLACIAN_MAX_NODES (256). Iteration count
 * bounded by SRMECH_LAPLACIAN_JACOBI_MAX_SWEEPS (100); returns
 * SRMECH_ERR_OVERFLOW on non-convergence.
 * Pi-free: phase factor for complex-Jacobi computed algebraically
 * from matrix entries (atan2-free).
 */
srmech_status_t srmech_hermitian_eigendecompose(
    uint32_t       n,
    const double  *H_interleaved,
    double        *out_eigvals,
    double        *out_eigvecs_interleaved);

/* Required workspace length (in doubles) for srmech_hermitian_
 * eigendecompose_ws at a given node count `n`: a working copy of the
 * n×n complex Hermitian matrix in interleaved-double form = 2*n*n
 * doubles. Use SRMECH_HERMITIAN_WS_MAX to size a worst-case
 * (n == SRMECH_LAPLACIAN_MAX_NODES) buffer. */
#define SRMECH_HERMITIAN_WS_LEN(n) ((size_t)(n) * (size_t)(n) * 2u)
#define SRMECH_HERMITIAN_WS_MAX SRMECH_HERMITIAN_WS_LEN(SRMECH_LAPLACIAN_MAX_NODES)

/* Reentrant variant of srmech_hermitian_eigendecompose (#772).
 *
 * Identical numerics + output contract, but takes a CALLER-SUPPLIED
 * working buffer `workspace` (length `ws_len` doubles) instead of an
 * internal shared-static scratch matrix. This makes the eigendecomp
 * safe to drive concurrently from many threads (the #771 plugin),
 * each passing its own workspace, with no malloc (JPL Rule 3) and no
 * large per-call stack frame.
 *
 * `workspace` must be non-NULL with `ws_len >= SRMECH_HERMITIAN_WS_LEN(n)`
 * = 2*n*n doubles; returns SRMECH_ERR_OVERFLOW if too small or n
 * exceeds SRMECH_LAPLACIAN_MAX_NODES, SRMECH_ERR_NULL_ARG if any
 * required pointer is NULL.
 *
 * ABI-additive: a new symbol, so SRMECH_ABI_VERSION is unchanged. The
 * original srmech_hermitian_eigendecompose remains and now routes
 * through this core using a thread-local workspace. */
srmech_status_t srmech_hermitian_eigendecompose_ws(
    uint32_t       n,
    const double  *H_interleaved,
    double        *out_eigvals,
    double        *out_eigvecs_interleaved,
    double        *workspace,
    size_t         ws_len);

/* Dense complex matrix-vector multiplication: out = M @ v.
 * M_interleaved is rows*cols interleaved-double pairs (row-major).
 * v_interleaved is cols interleaved-double pairs.
 * out_interleaved is rows interleaved-double pairs (caller-allocated).
 * rows and cols are bounded by SRMECH_LAPLACIAN_MAX_NODES (256).
 */
srmech_status_t srmech_dense_matvec_complex(
    uint32_t       rows,
    uint32_t       cols,
    const double  *M_interleaved,
    const double  *v_interleaved,
    double        *out_interleaved);

/* Elementwise complex multiply: out[i] = a[i] * b[i].
 * a, b, out are n interleaved-double pairs each. Bounded n only by
 * uint32_t — no stack allocation, so the SRMECH_LAPLACIAN_MAX_NODES
 * bound does NOT apply.
 */
srmech_status_t srmech_elementwise_multiply_complex(
    uint32_t       n,
    const double  *a_interleaved,
    const double  *b_interleaved,
    double        *out_interleaved);

/* Array-vectorised real transcendental. op_id from
 * {SRMECH_TRANS_EXP, SRMECH_TRANS_COS, SRMECH_TRANS_SIN, SRMECH_TRANS_LOG}.
 * Complex exponential `exp_i(x) = exp(i*x)` is NOT shipped in C —
 * lives in the Python wrapper as two C calls (cos + i*sin over the
 * real argument). Domain checks: SRMECH_TRANS_LOG returns
 * SRMECH_ERR_BAD_INPUT if any arr[i] <= 0.0.
 */
srmech_status_t srmech_elementwise_transcendental(
    uint32_t       n,
    const double  *arr,
    int            op_id,
    double        *out);

/* Dense linear solve A·X = B (v0.7.1rc3, #897 §26). A is n×n, B and the
 * output X are n×nrhs, all row-major doubles (caller-allocated). Gauss–
 * Jordan with partial pivoting; the reusable Class-L float primitive the
 * Schur-complement / DtN float path composes over for its interior solve.
 * A singular A (a wholly-zero pivot column at/below the diagonal) returns
 * SRMECH_ERR_BAD_INPUT. Bounded n, nrhs ≤ 256 (a thread-local augmented
 * workspace); larger systems return SRMECH_ERR_OVERFLOW (Python falls back
 * to numpy.linalg.solve). No libm: a solve is + − × ÷ only.
 * ABI-additive: a new symbol, so SRMECH_ABI_VERSION stays 3.
 */
srmech_status_t srmech_dense_solve_f64(
    uint32_t       n,
    uint32_t       nrhs,
    const double  *A,
    const double  *B,
    double        *out_X);

/* ------------------------------------------------------------------ *
 * Class J — prime-factorisation / period (Task #217 Phase C1 rc3)
 *
 * Integer-structure primitives complementing Class I (modular
 * arithmetic). Pi-free, no LAPACK, no malloc, no goto.
 *

 * No ABI bump (pure additions per Phase B4 convention).
 * `bool` comes from <stdbool.h> already included at top of header.
 * ------------------------------------------------------------------ */

/* Trial-division primality test. False for n < 2; true for 2, 3.
 * Loop bounded by sqrt(n) via the d <= n/d terminator. */
srmech_status_t srmech_is_prime(uint64_t n, bool *out);

/* Prime factorisation by trial division.
 *   primes[i]    = i-th distinct prime factor (ascending)
 *   exponents[i] = exponent of primes[i]
 *   max_count    = caller-allocated buffer size (≥ 15 covers uint64)
 *   *out_count   = number of distinct primes written
 * For n < 2: writes nothing, sets *out_count = 0.
 * Returns SRMECH_ERR_OVERFLOW if distinct-prime count exceeds
 * max_count. */
srmech_status_t srmech_factor(uint64_t  n,
                              uint64_t *primes,
                              uint8_t  *exponents,
                              uint32_t  max_count,
                              uint32_t *out_count);

/* Multiplicative order of a in (Z/nZ)*: smallest k > 0 with
 * a^k ≡ 1 (mod n). Requires n >= 2, gcd(a mod n, n) == 1, max_k >= 1.
 * Returns SRMECH_ERR_BAD_INPUT for invalid n, gcd != 1 (detected as
 * a mod n == 0), or max_k == 0.
 * Returns SRMECH_ERR_OVERFLOW if no period found within max_k. */
srmech_status_t srmech_cyclic_period(uint64_t  a,
                                     uint64_t  n,
                                     uint64_t  max_k,
                                     uint64_t *out_period);

/* ------------------------------------------------------------------ *
 * Class B — tagged-tuple TLV byte-canonical form (Task #217 Phase
 * C1 rc4 lightweight trio).
 *
 * Single operation: TLV pack. JSON-record parsing stays Python-side
 * per srmech CLAUDE.md operational-scope-clarification.
 * ------------------------------------------------------------------ */

/* Pack (tag, value) into a [u8 tag][u32 length BE][value] byte sequence.
 * `out_buffer` must have capacity ≥ 5 + value_len bytes; returns
 * SRMECH_ERR_OVERFLOW otherwise. `*out_written` = 5 + value_len on OK.
 * Big-endian length avoids platform-specific byte-order ambiguity.
 * Per [[feedback_struct_field_ordering_big_first]] this is a wire-
 * format-sensitive layout (the documented exception). */
srmech_status_t srmech_tlv_pack(uint8_t        tag,
                                const uint8_t *value,
                                uint32_t       value_len,
                                uint8_t       *out_buffer,
                                uint32_t       out_capacity,
                                uint32_t      *out_written);

/* ------------------------------------------------------------------ *
 * Class G — discovery / search (Task #217 Phase C1 rc4 lightweight trio).
 *
 * Single operation: byte-pattern search. Catalog discovery (Python-
 * side dictionary lookups) stays in srmech.amsc.catalog per the
 * operational-scope-clarification.
 * ------------------------------------------------------------------ */

/* Find the first occurrence of `needle` (needle_len bytes) in
 * `haystack` (haystack_len bytes). Naive O(n*m); fast for the small
 * haystacks srmech encounters. On match: *out_offset = first index
 * in haystack where needle appears. On miss: *out_offset =
 * UINT32_MAX (SRMECH_SEARCH_NOT_FOUND). Empty needle matches at 0
 * (matches Python's `bytes.find(b'')` convention). */
srmech_status_t srmech_byte_search(const uint8_t *haystack,
                                   uint32_t       haystack_len,
                                   const uint8_t *needle,
                                   uint32_t       needle_len,
                                   uint32_t      *out_offset);

/* Harmonic-2 chiral mirror of srmech_byte_search (F150): find the LAST
 * occurrence of `needle` in `haystack`. On match: *out_offset = highest
 * index where needle appears. On miss: *out_offset = UINT32_MAX
 * (SRMECH_SEARCH_NOT_FOUND). Empty needle returns *out_offset =
 * haystack_len (matches Python's `bytes.rfind(b'')` convention). */
srmech_status_t srmech_byte_search_backward(const uint8_t *haystack,
                                            uint32_t       haystack_len,
                                            const uint8_t *needle,
                                            uint32_t       needle_len,
                                            uint32_t      *out_offset);

/* ------------------------------------------------------------------ *
 * Class H — self-introspection (Task #217 Phase C1 rc4 acknowledgment).
 *
 * Already shipped in `srmech_meta.c` since Phase B2 — `srmech_version`
 * and `srmech_abi_version` are the Class H primitives. Documenting
 * the mapping here for the cross-substrate-audit roster.
 * ------------------------------------------------------------------ */

/* ------------------------------------------------------------------ *
 * Class D — late-binding / dispatch (Task #217 Phase C1 rc5)
 *
 * Given an input byte sequence and an array of (pattern, tag) rules,
 * find the first rule whose pattern occurs in the input and return its
 * tag. Multi-needle byte-pattern dispatcher; builds on Class G's
 * srmech_byte_search internally.
 *
 * On match: *out_matched = true, *out_tag = tags[matched_index].
 * On no match: *out_matched = false, *out_tag = 0.
 * Rules with pattern_lengths[i] == 0 (empty pattern) match at offset 0
 * by Class G's convention.
 * ------------------------------------------------------------------ */
srmech_status_t srmech_dispatch_match(const uint8_t  *input,
                                      uint32_t        input_len,
                                      const uint8_t  *patterns_buffer,
                                      const uint32_t *pattern_offsets,
                                      const uint32_t *pattern_lengths,
                                      const uint32_t *tags,
                                      uint32_t        n_rules,
                                      bool           *out_matched,
                                      uint32_t       *out_tag);

/* Harmonic-2 chiral mirror of a dispatch pattern (F150): write the
 * `pattern_len` bytes of `pattern` reversed into `out`
 * (out[i] = pattern[pattern_len - 1 - i]). `out` is caller-owned and
 * must NOT alias `pattern`. Empty pattern writes nothing. Applying it
 * twice is the identity (period 2). */
srmech_status_t srmech_mirror_pattern(const uint8_t *pattern,
                                      uint32_t       pattern_len,
                                      uint8_t       *out);

/* ------------------------------------------------------------------ *
 * Class E — catalog / naming (Task #217 Phase C1 rc5)
 *
 * Binary search over a sorted (key, value) catalog. Keys MUST be
 * pre-sorted ascending lexicographic (caller responsibility). On
 * match: *out_found = true, *out_value_offset / *out_value_length
 * describe the value's slice within values_buffer.
 *
 * Comparison is byte-level lex with length tiebreak (shorter is less
 * when prefix-equal). Use srmech_catalog_lookup to build higher-level
 * registry operations (e.g., the attested-sources catalog in
 * srmech.amsc.catalog uses this primitive on canonicalised keys).
 * ------------------------------------------------------------------ */
srmech_status_t srmech_catalog_lookup(const uint8_t  *key,
                                      uint32_t        key_len,
                                      const uint8_t  *keys_buffer,
                                      const uint32_t *key_offsets,
                                      const uint32_t *key_lengths,
                                      const uint32_t *value_offsets,
                                      const uint32_t *value_lengths,
                                      uint32_t        n_entries,
                                      bool           *out_found,
                                      uint32_t       *out_value_offset,
                                      uint32_t       *out_value_length);

/* Harmonic-2 chiral mirror of a sorted catalog (F150): write the reversed
 * index permutation out_order[i] = n - 1 - i. The Python wrapper applies this
 * to the (key, value) pairs to produce a descending-key view of an ascending
 * catalog; applying it twice is the identity (period 2). `out_order` is
 * caller-owned with room for n uint32 entries; empty n writes nothing.
 * ABI-additive: a new symbol, so SRMECH_ABI_VERSION stays 3. */
srmech_status_t srmech_reverse_order(uint32_t n, uint32_t *out_order);

/* ------------------------------------------------------------------ *
 * Class F — substitution / templating (Task #217 Phase C1 rc5)
 *
 * Render a template containing `{key}` placeholders into out_buf,
 * substituting each `{key}` with the value looked up in a sorted
 * (key, value) catalog (uses srmech_catalog_lookup internally).
 *
 * Format:
 *   - Plain bytes pass through verbatim.
 *   - `{key}` substitutes with the looked-up value bytes.
 *   - Unterminated `{...` or unknown key: SRMECH_ERR_BAD_INPUT.
 *   - Insufficient out_capacity: SRMECH_ERR_OVERFLOW.
 *
 * No escape sequences for `{` and `}` (caller can substitute a key
 * whose value is the literal brace if needed). Keep simple per JPL
 * discipline.
 * ------------------------------------------------------------------ */
srmech_status_t srmech_template_render(const uint8_t  *tmpl,
                                       uint32_t        tmpl_len,
                                       const uint8_t  *keys_buffer,
                                       const uint32_t *key_offsets,
                                       const uint32_t *key_lengths,
                                       const uint8_t  *values_buffer,
                                       const uint32_t *value_offsets,
                                       const uint32_t *value_lengths,
                                       uint32_t        n_pairs,
                                       uint8_t        *out_buf,
                                       uint32_t        out_capacity,
                                       uint32_t       *out_written);

/* ------------------------------------------------------------------ *
 * Class N — rational-approximation (Task #217 Phase C1 rc6)
 *
 * Two operations: simple continued-fraction expansion (Euclidean
 * recurrence) and best-rational-under-denominator-bound (continued-
 * fraction convergents). Pure integer arithmetic on uint64_t.
 * ------------------------------------------------------------------ */

/* Simple continued-fraction expansion of numerator / denominator.
 * Writes integer terms a_0, a_1, a_2, ... into caller-allocated
 * `terms`. Bounded by Fibonacci-worst-case for uint64 (~91 iter);
 * SRMECH_RATIONAL_EUCLID_CAP = 128 is the safe ceiling.
 * Returns SRMECH_ERR_BAD_INPUT for denominator == 0.
 * Returns SRMECH_ERR_OVERFLOW if max_terms is exceeded. */
srmech_status_t srmech_continued_fraction(uint64_t  numerator,
                                          uint64_t  denominator,
                                          uint64_t *terms,
                                          uint32_t  max_terms,
                                          uint32_t *out_count);

/* Best rational p'/q' with q' <= max_denominator approximating
 * numerator/denominator. Walks continued-fraction convergents
 * (Stern-Brocot path through the mediant tree); returns (0, 1) if
 * no non-trivial convergent fits. Overflow-guarded.
 * Returns SRMECH_ERR_BAD_INPUT for denominator == 0 or
 * max_denominator == 0. */
srmech_status_t srmech_best_rational(uint64_t  numerator,
                                     uint64_t  denominator,
                                     uint64_t  max_denominator,
                                     uint64_t *out_p,
                                     uint64_t *out_q);

/* Class N rc8: exp Taylor partial sum as exact rational.
 *
 * Computes S_N(p/q) = sum_{k=0..N} (p/q)^k / k! and returns the result
 * reduced to lowest terms in (*out_num, *out_den). Pure integer
 * arithmetic; bounded num_terms ≤ 20 to keep N! within u64 (Python
 * fallback srmech.amsc.rational.exp_series_truncate handles larger N
 * via arbitrary-precision int). Returns SRMECH_ERR_OVERFLOW if any
 * intermediate product (|p|^k, q^(N-k), N!/k!, their products, the sum
 * itself) would exceed range; the wrapper falls through to bignum
 * Python in that case.
 *
 * The C surface is usable STANDALONE — link libsrmech, call this from
 * a C-only program (no Python required) for catalog-row-shaped inputs.
 * Anchored to [[feedback_no_binding_layer_carveout]] discipline:
 * every primitive class earns a real C surface.
 *
 * Canonical SSoT: Apostol *Mathematical Analysis* 2nd ed. Thm 12.20
 * (Lagrange remainder) for the convergence claim; Bishop *Foundations
 * of Constructive Analysis* §2 for the asymptotic-rate framing.
 */
srmech_status_t srmech_exp_series_truncate(int64_t   x_num,
                                           uint64_t  x_den,
                                           uint32_t  num_terms,
                                           int64_t  *out_num,
                                           uint64_t *out_den);

/* Class N rc10: rational arithmetic primitives.
 *
 * Three load-bearing operations for the `cosmos_validation` catalog's
 * Friedmann dark-fraction chain composition under Phase 2 v1 chain DSL:
 *
 *   - srmech_rational_add:      (a_num/a_den) + (b_num/b_den) reduced
 *   - srmech_rational_mul:      (a_num/a_den) * (b_num/b_den) reduced
 *   - srmech_rational_pow_uint: (base_num/base_den)^exp reduced; exp ≤ 64
 *
 * Each returns SRMECH_ERR_OVERFLOW when any intermediate exceeds u64
 * range. Python wrappers (srmech.amsc.rational.rational_{add,mul,pow_uint})
 * fall through to bignum on overflow. C library is usable standalone
 * for inputs that fit u64 per [[feedback_no_binding_layer_carveout]].
 */
srmech_status_t srmech_rational_add(int64_t   a_num,
                                    uint64_t  a_den,
                                    int64_t   b_num,
                                    uint64_t  b_den,
                                    int64_t  *out_num,
                                    uint64_t *out_den);

srmech_status_t srmech_rational_mul(int64_t   a_num,
                                    uint64_t  a_den,
                                    int64_t   b_num,
                                    uint64_t  b_den,
                                    int64_t  *out_num,
                                    uint64_t *out_den);

srmech_status_t srmech_rational_div(int64_t   a_num,
                                    uint64_t  a_den,
                                    int64_t   b_num,
                                    uint64_t  b_den,
                                    int64_t  *out_num,
                                    uint64_t *out_den);

srmech_status_t srmech_rational_pow_uint(int64_t   base_num,
                                         uint64_t  base_den,
                                         uint32_t  exp_val,
                                         int64_t  *out_num,
                                         uint64_t *out_den);

/* Class N Milestone #4: π geometric-cascade primitives.
 *
 * srmech_cf_convergents_int64 — convergent ladder for a continued-
 * fraction coefficient list. Given coefs = [a_0, a_1, ..., a_{n-1}]
 * (the simple CF of some real number), produces convergents
 *
 *   h_k = a_k * h_{k-1} + h_{k-2},  h_{-1} = 1, h_{-2} = 0
 *   k_k = a_k * k_{k-1} + k_{k-2},  k_{-1} = 0, k_{-2} = 1
 *
 * in out_nums[i] / out_dens[i] for i = 0..n-1.
 *
 * The canonical π convergent ladder drops out when coefs is the
 * canonical π CF [3, 7, 15, 1, 292, 1, 1, 1, 2, 1, 3, 1, 14, ...]:
 * (3, 1), (22, 7), (333, 106), (355, 113), (103993, 33102), ...
 *
 * Bounded loop n ≤ SRMECH_CF_CONVERGENTS_MAX_N (256). Returns
 * SRMECH_ERR_OVERFLOW if any convergent exceeds int64; Python
 * srmech.amsc.rational.continued_fraction_convergents falls back to
 * bignum at that point.
 *
 * Anchored to [[user_stance_pi_spectral_shape_scalar_invariant]] —
 * the convergent ladder IS π's substrate-level identity (Spike #32
 * PR #460 confirmed across 3 substrates with AST-verified zero
 * math.pi invocations).
 */
srmech_status_t srmech_cf_convergents_int64(const int64_t *coefs,
                                            size_t         n,
                                            int64_t       *out_nums,
                                            int64_t       *out_dens);

/* ------------------------------------------------------------------ *
 * Class K — equation-of-centre / pin-slot (Task #217 Phase C1 rc7)
 *
 * Three continuous-projection operations. Per [[user_stance_kepler_shape_universal]]
 * + PR #416 F2/F15/F17: Kepler-equation algebra IS pin-slot composition.
 * This file ships the continuous projection-shadow of the integer-cyclic
 * upstream (Class I cyclic groups + Class J prime-period). Uses libm
 * (sin / cos / atan2 / fabs); double precision throughout.
 *
 * Canonical SSoT per [[feedback_science_is_ssot_not_project]]:
 *   - Pin-slot transform        : Freeth (2021) Nature Sci Rep, Supp S9.
 *   - Kepler equation           : Kepler (1609) Astronomia Nova.
 *   - Newton-Raphson starter    : Smith (1979) Celestial Mech 19, 163.
 *   - Equation-of-centre series : Brouwer & Clemence (1961) §3.2;
 *                                 Murray & Dermott (1999) §2.5.
 *
 * No ABI bump: pure additions to ABI v2 per the Phase B4 convention.
 * ------------------------------------------------------------------ */

#define SRMECH_KEPLER_EOC_MAX_TERMS 6

/* Antikythera-era pin-and-slot transform. Pin at radial offset pin_offset
 * on input gear; rocker axis at distance pin_distance from input gear
 * center; rocker tracks the pin via a radial slot. As input rotates by
 * theta (radians), rocker turns by phi = atan2(i*sin(theta), d + i*cos(theta)).
 * Returns SRMECH_ERR_BAD_INPUT only for the degenerate case pin_offset == 0
 * AND pin_distance == 0 (atan2(0,0) is implementation-defined). */
srmech_status_t srmech_pin_slot(double  theta,
                                double  pin_offset,
                                double  pin_distance,
                                double *out_phi);

/* Newton-Raphson on Kepler's equation M = E - e*sin(E). Inputs in radians.
 * 0 <= e < 1 required (returns SRMECH_ERR_BAD_INPUT otherwise). Initial
 * guess via Smith (1979): E_0 = M + e*sin(M). Converges in 4-6 iter for
 * e < 0.5; e >= 0.95 may need >30. Tolerance is |delta E| < tolerance.
 * Returns SRMECH_ERR_OVERFLOW if not converged within max_iter (caller
 * gets best-effort E in out_E_rad). */
srmech_status_t srmech_kepler_solve(double    M_rad,
                                    double    e,
                                    double    tolerance,
                                    uint32_t  max_iter,
                                    double   *out_E_rad);

/* Fourier-series equation of centre nu - M (true anomaly minus mean
 * anomaly), principal-term-per-harmonic up to n_terms in eccentricity:
 *   nu - M = sum_{k=1..n} c_k * e^k * sin(k*M)
 * with c_k = [2, 5/4, 13/12, 103/96, 1097/960, 1223/960] for k = 1..6
 * (Brouwer & Clemence 1961 §3.2). Returns SRMECH_ERR_BAD_INPUT for
 * e < 0 or e >= 1, n_terms == 0, or n_terms > SRMECH_KEPLER_EOC_MAX_TERMS. */
srmech_status_t srmech_equation_of_centre(double    M_rad,
                                          double    e,
                                          uint32_t  n_terms,
                                          double   *out_delta_rad);

/* ------------------------------------------------------------------ *
 * Class N — native rational trig cascade (v0.7.0rc43; C-transpile
 * triality coherence). sin/cos/atan/atan2 computed as the Class-N
 * Taylor cascade in Q61 fixed-point, with the CYCLIC range-reduction
 * (mod pi/2) done in pure INTEGER arithmetic (pi from the Archimedes
 * pi-cascade; no libm sin/cos/atan2, no abs()). float appears only at
 * the final rational->double projection. These are the native peers the
 * kepler / kuramoto ops route through so the executable runs the cascade,
 * not libm. Matches libm to machine epsilon for |x| < 2^55; returns
 * SRMECH_ERR_BAD_INPUT for non-finite x (out set to NaN). Additive ->
 * ABI unchanged.
 * ------------------------------------------------------------------ */
srmech_status_t srmech_sin(double x, double *out);
srmech_status_t srmech_cos(double x, double *out);
srmech_status_t srmech_atan(double x, double *out);
srmech_status_t srmech_atan2(double y, double x, double *out);

/* Class-N rational sqrt cascade (v0.7.0rc45). sqrt(x) (x >= 0) via an INTEGER
 * floor-isqrt on a scaled radicand (portable two-limb 128-bit isqrt; no libm,
 * no float sqrt, no __int128) + IEEE-exponent-field power-of-two scaling.
 * srmech_laplacian.c's cyclic-Jacobi eigensolver routes through this so the
 * executable runs the cascade. Machine-epsilon vs libm; negative x ->
 * SRMECH_ERR_BAD_INPUT (out = NaN). Additive -> ABI unchanged. */
srmech_status_t srmech_rational_sqrt(double x, double *out);

/* Class-N rational exp/log cascade (v0.7.0rc46; the C-transpile closeout).
 * exp(x) = 2^n * exp(r) with the Q61 integer Taylor for exp(r) (|r| <= ln2/2)
 * and the 2^n scale built into the IEEE exponent field; log(x) reads
 * x = m*2^e from the bit pattern (integer) and runs the Q61 integer atanh
 * series log(m) = 2*atanh((m-1)/(m+1)). No libm, no float exp/log/pow.
 * srmech_laplacian.c's elementwise transcendental op routes through these so
 * the executable runs the cascade (the last two libm calls in libsrmech).
 * Machine-epsilon vs libm; exp overflow -> +Inf, underflow -> 0; log of a
 * non-positive x -> SRMECH_ERR_BAD_INPUT. Additive -> ABI unchanged. */
srmech_status_t srmech_exp(double x, double *out);
srmech_status_t srmech_log(double x, double *out);

/* ------------------------------------------------------------------ *
 * Class M — HDC binary spatter codes (Task #217 Phase C1 rc8)
 *
 * Final primitive class — closes the 14-class C parity roster. BSC
 * operations on byte-buffer hyperdimensional vectors (D bits = 8 * n_bytes;
 * standard canonical D = 1024 bits, n_bytes = 128). Per
 * [[user_stance_1d_collapse_to_loe_identity_not_action]]: Class M is the
 * binding operation that uncompresses LoE-content along its compression
 * axis. Class C ∘ Class M composes the full LoE-uncompression kernel
 * (Class C iteration drives Class M binding).
 *
 * Canonical SSoT per [[feedback_science_is_ssot_not_project]]:
 *   - Kanerva (2009) Cognitive Computation 1, 139-159
 *   - Plate (1995) IEEE Trans Neural Networks 6, 623-641
 *   - Rachkovskij (2001) Neural Comput Appl 9, 322-345
 *
 * No ABI bump: pure additions to ABI v2 per the Phase B4 convention.
 * ------------------------------------------------------------------ */

#define SRMECH_HDC_MAX_BUNDLE_N 257  /* safety cap for bundle n_vectors */

/* bind(a, b): component-wise XOR. out[i] = a[i] ^ b[i]. Commutative,
 * associative, self-inverse: bind(a, bind(a, b)) = b. */
srmech_status_t srmech_hdc_bind(const uint8_t *a,
                                const uint8_t *b,
                                uint32_t       n_bytes,
                                uint8_t       *out);

/* bundle(vectors, n_vectors): majority across n_vectors at each bit position.
 * Returns SRMECH_ERR_BAD_INPUT for even n_vectors (BSC convention requires
 * odd-count for clean majority; caller can pad with tie-breaker vector).
 * Returns SRMECH_ERR_OVERFLOW for n_vectors > SRMECH_HDC_MAX_BUNDLE_N. */
srmech_status_t srmech_hdc_bundle(const uint8_t * const *vectors,
                                  uint32_t                n_vectors,
                                  uint32_t                n_bytes,
                                  uint8_t                *out);

/* permute(a, rotate_bits): cyclic bit-rotation of a by rotate_bits positions.
 * Negative rotate_bits rotates the other direction. Result is a re-ordered
 * vector of the same n_bytes; preserves popcount(a). */
srmech_status_t srmech_hdc_permute(const uint8_t *a,
                                   uint32_t       n_bytes,
                                   int32_t        rotate_bits,
                                   uint8_t       *out);

/* similarity(a, b): 1 - 2 * hamming(a, b) / D in [-1, 1]. +1 = identical,
 * 0 = orthogonal (Hamming(a,b) = D/2), -1 = bit-complementary. */
srmech_status_t srmech_hdc_similarity(const uint8_t *a,
                                      const uint8_t *b,
                                      uint32_t       n_bytes,
                                      double        *out);

/* ------------------------------------------------------------------ *
 * Class M — polar {-1, 0, +1} variant (v0.4.3rc1)
 *
 * Rank-1 Class M with an *absorbing* zero (Class M ∘ Class K). Unlike the
 * bipolar BSC surface above (bit-packed bytes), a polar hypervector is an
 * int8 array of D elements, each in {-1, 0, +1}; 0 is the asymptotic-DOF
 * "dead-band / uncertain" state the Class-K pin-slot rejects. Bind is the
 * multiplicative sign-product (0 absorbing); bundle is the sticky majority
 * (ties resolve to 0). No ABI bump — pure additions to ABI v2.
 *
 * Class M variant ladder: bipolar {-1,+1} → polar {-1,0,+1} → Klein-4 (Z₂)².
 * ------------------------------------------------------------------ */

/* polar_bind(a, b): element-wise sign-product, 0 absorbing.
 * out[i] = a[i] * b[i]. Also serves unbind (self-inverse on ±1; 0
 * destructive). Inputs must hold values in {-1, 0, +1}; returns
 * SRMECH_ERR_BAD_INPUT otherwise. */
srmech_status_t srmech_polar_bind(const int8_t *a,
                                  const int8_t *b,
                                  uint32_t      n,
                                  int8_t       *out);

/* polar_bundle(vectors, n_vectors): per-position sticky majority.
 * out[i] = sign(sum_v vectors[v][i]); exact ties (sum == 0) → 0. No
 * odd-count restriction (the 0 state absorbs ties). Returns
 * SRMECH_ERR_OVERFLOW for n_vectors > SRMECH_HDC_MAX_BUNDLE_N. */
srmech_status_t srmech_polar_bundle(const int8_t * const *vectors,
                                    uint32_t              n_vectors,
                                    uint32_t              n,
                                    int8_t               *out);

/* polar_similarity(a, b, skip_zero): match-fraction in [0, 1].
 * skip_zero != 0 → fraction over positions where both a[i] != 0 and
 * b[i] != 0 (0.0 if none); skip_zero == 0 → fraction over all positions
 * (0 == 0 counts as a match). */
srmech_status_t srmech_polar_similarity(const int8_t *a,
                                        const int8_t *b,
                                        uint32_t      n,
                                        int32_t       skip_zero,
                                        double       *out);

/* polar_density(v): fraction of non-zero (informative) positions in [0, 1].
 * 1.0 = fully bipolar (no dead-band); lower = more dead-band positions. */
srmech_status_t srmech_polar_density(const int8_t *v,
                                     uint32_t      n,
                                     double       *out);

/* ------------------------------------------------------------------ *
 * Class M — Klein-4 {0,1,2,3} variant (v0.4.3rc2)
 *
 * Rank-2 abelian Class M over (F₂)² = Z₂×Z₂. uint8 hypervectors with
 * elements in {0,1,2,3} (state = γ₅_bit·2 + iω₇_bit). bind = component-
 * wise (F₂)²-XOR (self-inverse, abelian, identity 0); bundle = per-bit
 * majority (ties → 0). Inputs out of {0,1,2,3} → SRMECH_ERR_BAD_INPUT.
 * No ABI bump. Ladder: bipolar → polar → KLEIN-4.
 * ------------------------------------------------------------------ */

/* klein4_bind(a, b): component-wise XOR over (F₂)². out[i] = a[i] ^ b[i]. */
srmech_status_t srmech_klein4_bind(const uint8_t *a,
                                   const uint8_t *b,
                                   uint32_t       n,
                                   uint8_t       *out);

/* klein4_bundle(vectors, n_vectors): per-bit majority on each of the 2
 * bits independently; exact ties (count == n_vectors/2) → 0 for that bit.
 * Returns SRMECH_ERR_OVERFLOW for n_vectors > SRMECH_HDC_MAX_BUNDLE_N. */
srmech_status_t srmech_klein4_bundle(const uint8_t * const *vectors,
                                     uint32_t               n_vectors,
                                     uint32_t               n,
                                     uint8_t               *out);

/* klein4_similarity(a, b): fraction of positions where a[i] == b[i] in
 * [0, 1] (1 identical, 0 orthogonal). */
srmech_status_t srmech_klein4_similarity(const uint8_t *a,
                                         const uint8_t *b,
                                         uint32_t       n,
                                         double        *out);

/* klein4_triality_cycle(in, n, inverse, out): the order-3 S3 = Aut(V4)
 * cycle of the three involutions (iw7 1 -> g5 2 -> CPT 3, identity 0
 * fixed); the V4-carrier image of the so(8) 8v->8s->8c triality. inverse
 * != 0 applies the reverse 3-cycle (T^2 = T^-1). Out of {0,1,2,3} ->
 * SRMECH_ERR_BAD_INPUT. Additive symbol — no ABI bump. */
srmech_status_t srmech_klein4_triality_cycle(const uint8_t *in,
                                             uint32_t       n,
                                             int            inverse,
                                             uint8_t       *out);

/* ------------------------------------------------------------------ *
 * srmech.bus — cross-process IPC C peer (v0.5.0rc2)
 *
 * Five public symbols + one function-pointer typedef. POSIX uses
 * AF_UNIX sockets at ~/.srmech/bus-<name>.sock; Windows uses named
 * pipes at \\.\pipe\srmech-<name>. Framing is 4-byte big-endian
 * length prefix + payload bytes (same as the Python skeleton).
 *
 * Handler dispatch is via the caller-provided function-pointer
 * callback typedef below — same pattern as v0.4.5rc8's
 * srmech_cascade_op_callback_f64_t. The Python ctypes layer
 * wraps this typedef via ctypes.CFUNCTYPE to marshal arbitrary
 * Python callables to the C surface.
 *
 * Memory: no malloc inside the hot path (JPL Rule 3). The per-server
 * workspace + response buffer are allocated once at srmech_bus_serve
 * entry and freed at srmech_bus_server_stop; the accept loop reuses
 * them across all accepted connections. Caller-supplied response
 * buffers in srmech_bus_send_recv are caller-owned (no copy through
 * the library).
 *
 * Threading: thread-per-connection is the documented model on the
 * Python side; the C surface ships srmech_bus_server_accept_one for
 * single-threaded harnesses (each call accepts one client, services
 * its requests until peer-close, then returns — the caller spins
 * this in a thread).
 *
 * ABI v3 (this rc). Pure additions to v2 — but the new callback
 * typedef carries a wire-format implication, so ABI bumps per the
 * `[[reference_srmech_abi_compatibility]]` convention.
 * ------------------------------------------------------------------ */

/* Handler callback: per-request dispatch. The C library reads one
 * length-prefixed request into a workspace, then invokes this
 * callback. The callback writes its response into the caller-supplied
 * `response` buffer (capacity in `*response_len_inout` on entry) and
 * sets `*response_len_inout` to the actual response byte length.
 * Returns SRMECH_OK on success; any non-OK return is treated as a
 * handler error and propagated to the worker loop (which closes the
 * connection). `user_data` is the opaque context pointer passed at
 * srmech_bus_serve entry. */
typedef srmech_status_t (*srmech_bus_handler_callback_t)(
    const uint8_t *request,
    size_t         request_len,
    uint8_t       *response,
    size_t        *response_len_inout,
    void          *user_data);

/* Opaque handle types. Definitions live in srmech_bus.c. */
typedef struct srmech_bus_server_handle srmech_bus_server_handle_t;
typedef struct srmech_bus_client_handle srmech_bus_client_handle_t;

/* Create a bus server. Builds the on-disk registration
 * (~/.srmech/bus-<name>.sock on POSIX; \\.\pipe\srmech-<name> on
 * Windows), allocates the per-server workspace, and returns the
 * handle in *out_handle. Does NOT start an accept loop — call
 * srmech_bus_server_accept_one in a thread loop to service
 * connections.
 *
 * Error returns:
 *   SRMECH_ERR_NULL_ARG    — name, handler, or out_handle is NULL.
 *   SRMECH_ERR_BAD_INPUT   — name produces an invalid on-disk path.
 *   SRMECH_ERR_OVERFLOW    — name + path-prefix exceeds buffer.
 *   SRMECH_ERR_IO          — socket/bind/listen failed.
 *   SRMECH_ERR_INTERNAL    — calloc failed. */
srmech_status_t srmech_bus_serve(
    const char                       *name,
    srmech_bus_handler_callback_t     handler,
    void                             *user_data,
    srmech_bus_server_handle_t      **out_handle);

/* Accept one client + service its requests until peer-close.
 * BLOCKING. Caller-spinnable in a thread loop. Returns SRMECH_OK
 * after the client disconnects cleanly; SRMECH_ERR_IO on accept
 * failure. */
srmech_status_t srmech_bus_server_accept_one(
    srmech_bus_server_handle_t *h);

/* Stop the server: signal shutdown, close the listen handle,
 * unlink the on-disk registration, free the workspace + the
 * handle itself. After return, h is invalid. */
srmech_status_t srmech_bus_server_stop(srmech_bus_server_handle_t *h);

/* Connect a bus client to the named endpoint. Returns the handle
 * in *out_handle on success.
 *
 * Error returns:
 *   SRMECH_ERR_NULL_ARG    — name or out_handle is NULL.
 *   SRMECH_ERR_IO          — socket/connect failed (server not
 *                            running, permission, etc.). */
srmech_status_t srmech_bus_connect(
    const char                       *name,
    srmech_bus_client_handle_t      **out_handle);

/* Send one request + read its reply.
 *   request: caller-owned bytes (length request_len).
 *   response: caller-allocated buffer; *response_len_inout is the
 *     capacity on entry, the actual response length on success.
 *
 * Error returns:
 *   SRMECH_ERR_NULL_ARG    — any of the four pointers is NULL.
 *   SRMECH_ERR_OVERFLOW    — request_len > UINT32_MAX, or response
 *                            buffer too small for the server's reply.
 *   SRMECH_ERR_IO          — peer closed mid-frame, network error. */
srmech_status_t srmech_bus_send_recv(
    srmech_bus_client_handle_t       *h,
    const uint8_t                    *request,
    size_t                            request_len,
    uint8_t                          *response,
    size_t                           *response_len_inout);

/* Close the client + free its handle. After return, h is invalid. */
srmech_status_t srmech_bus_client_close(srmech_bus_client_handle_t *h);

/* --------------------------------------------------------------------
 * Hamming / GF(2) linear block-code family (#910 / §30; F442/F449).
 *
 * The CARRY/EC half of the sedenion front-loader: a 2^n-1 single-error-
 * correcting Hamming code, lean-ALU XOR-native (GF(2) add = parity = XOR;
 * no float, no libm, no malloc). Canonical 1-indexed construction: codeword
 * length N = 2^n - 1, parity bits at the power-of-two positions; the syndrome
 * IS the 1-indexed position of the single flipped bit (0 = clean). Distance 3
 * => corrects any single-bit error. Hamming(7,4) is the octonion's own Fano
 * plane (F441). Rosetta peer of srmech.amsc.cascade.hamming_* — attested
 * bit-exact by tests/test_cascade_hamming_parity.py.
 *
 * ABI-additive: new symbols + one macro, so SRMECH_ABI_VERSION stays 3.
 * ------------------------------------------------------------------ */

/* Upper bound on the parity-bit count n (codeword 2^n - 1 <= 65535). Shared
 * with the Python surface (srmech.amsc.cascade.hamming.HAMMING_MAX_N). */
#define SRMECH_HAMMING_MAX_N 16

/* Encode k = (2^n - 1) - n data bits (each 0/1) into a 2^n-1-bit codeword.
 *   data         : k input bits (0/1), caller-owned.
 *   k            : MUST equal (2^n - 1) - n.
 *   n            : parity-bit count, 2 <= n <= SRMECH_HAMMING_MAX_N.
 *   out_codeword : caller-owned, length 2^n - 1; receives the codeword.
 * Errors: SRMECH_ERR_NULL_ARG (null ptr); SRMECH_ERR_BAD_INPUT (n out of
 * range, k mismatch, or a non-0/1 data bit). */
srmech_status_t srmech_hamming_encode(const uint8_t *data, size_t k, int n,
                                      uint8_t *out_codeword);

/* Compute the syndrome (1-indexed flipped-bit position; 0 = clean).
 *   codeword : len bits (0/1); len MUST be of the form 2^n - 1.
 *   len      : codeword length.
 *   out_pos  : receives the 1-indexed error position (0 if clean).
 * Errors: SRMECH_ERR_NULL_ARG; SRMECH_ERR_BAD_INPUT (len not 2^n-1 in range,
 * or a non-0/1 bit). */
srmech_status_t srmech_hamming_syndrome(const uint8_t *codeword, size_t len,
                                        int *out_pos);

/* Locate + correct any single-bit error and recover the data payload.
 *   codeword : len bits (0/1), len = 2^n - 1.
 *   len      : codeword length.
 *   out_data : caller-owned, length len - n; receives the k corrected data bits.
 *   out_pos  : receives the 1-indexed error position (0 if clean).
 * Single-error-correcting (distance 3). Errors as srmech_hamming_syndrome. */
srmech_status_t srmech_hamming_decode_correct(const uint8_t *codeword, size_t len,
                                              uint8_t *out_data, int *out_pos);

/* ------------------------------------------------------------------
 * Cayley-Dickson basis-unit cocycle (v0.7.3rc1; #915 / MFO §VII.6.23) — the
 * integer structural core of the open-exterior demonstrator. The product of
 * two unit basis elements e_i * e_j = sign * e_index in the dim-D
 * Cayley-Dickson algebra (the result index is i XOR j; the sign carries the
 * Fano/orientation structure). Computed by the same iterative doubling-step the
 * Python recursion uses, unrolled to a bounded loop (no recursion; JPL Rule 1).
 * Rosetta peer of srmech.amsc.cascade.cayley_dickson.cd_basis_product —
 * attested bit-exact by tests/test_cascade_cayley_dickson_parity.py.
 *
 * ABI-additive: a new symbol + two macros, so SRMECH_ABI_VERSION stays 3.
 * ------------------------------------------------------------------ */

/* Hard ceiling on the algebra dimension (a power of two). Shared with the
 * Python surface (srmech.amsc.cascade.cayley_dickson.CD_MAX_DIM). */
#define SRMECH_CD_MAX_DIM 64
/* log2(SRMECH_CD_MAX_DIM) — the doubling-loop over-bound (JPL Rule 2). */
#define SRMECH_CD_MAX_LEVELS 6

/* Product of two unit basis elements: e_i * e_j = sign * e_index.
 *   dim        : algebra dimension, a power of two in [1, SRMECH_CD_MAX_DIM].
 *   i, j       : basis indices in [0, dim).
 *   out_index  : receives the result basis index in [0, dim) (== i XOR j).
 *   out_sign   : receives the sign, +1 or -1.
 * Errors: SRMECH_ERR_NULL_ARG (null ptr); SRMECH_ERR_BAD_INPUT (dim not a
 * power of two in range, or i/j out of range). */
srmech_status_t srmech_cd_basis_product(int dim, int i, int j,
                                        int *out_index, int *out_sign);

#ifdef __cplusplus
}
#endif

#endif /* SRMECH_H */
