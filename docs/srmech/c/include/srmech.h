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
 * License: MIT (parent project: mlehaptics).
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
#define SRMECH_VERSION_MINOR 9
#define SRMECH_VERSION_PATCH 0
#define SRMECH_VERSION_PRE   "rc169"
#define SRMECH_VERSION       "0.9.0rc169"

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
 *   dθ_i/dt = ω_i + Σ_j K·A_ij·sin(θ_j − θ_i − α) [ + p_i·sin(ψ_i − θ_i) ]
 *   θ_i(t+dt) = θ_i(t) + dt·[ above ]
 *
 * `adjacency` is ROW-MAJOR n×n (A_ij = weight of oscillator j on i): a
 * non-symmetric matrix expresses DIRECTED / one-way coupling, a graph
 * Laplacian expresses graph-structured coupling. The effective weight is
 * `coupling_k·A_ij` — the global K SCALES the matrix (so K=0 zeroes the
 * coupling), matching the all-to-all branch's K/N (§32 fix, v0.7.5rc15;
 * prior to rc15 K was ignored when adjacency was provided).
 * `adjacency == NULL` ⇒ every weight is the uniform mean-field K/N (so NULL
 * adjacency + α=0 + NULL pin_anchor reproduces
 * srmech_cascade_kuramoto_step_f64 exactly).
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
 * NUMERIC IIR / recursive filter (BATCH B4b, 0.9.0rc149) — the sp_transform
 * filter family's one genuinely-new numeric kernel.
 *
 * The direct-form-I difference equation
 *   y[i] = ( Σ_{j} b[j]·x[i-j] − Σ_{k>=1} a[k]·y[i-k] ) / a[0]
 * (x[i-j] / y[i-k] = 0 for negative index; zero initial rest). This is
 * y = lfilter(b, a, x): the recursive IIR filter that backs both
 * `closed_form_ops.iir` (biquad cascade = per-section) and
 * `closed_form_ops.allpass` (mirrored (b,a)). An FIR filter is the a=[1] case.
 *
 * WHY A NEW SYMBOL: the feedback term reads y[i-k] — the output still being
 * produced — so the recursion is inherently SEQUENTIAL and does NOT decompose
 * into a matmul/FFT (contrast a feed-forward-only convolution, which the filter
 * family routes through mat_matmul). NUMERIC (FPU-tol), NOT byte-exact — the
 * Python parity contract is within-tol (reldiff ≤ 1e-9), matching the F1-FFT /
 * F2-SVD numeric foundations. No libm, no abs. `out` (n doubles) MUST NOT alias
 * `x`. Empty b/a -> SRMECH_ERR_NULL_ARG; a[0]==0 -> SRMECH_ERR_BAD_INPUT; n==0
 * writes nothing. The pure-Python difference-equation reference is the COMPLETE
 * alternative for no-C hosts. ABI-additive — SRMECH_ABI_VERSION stays 3.
 * ------------------------------------------------------------------ */
srmech_status_t srmech_iir_lfilter_f64(
    const double *b, size_t nb,
    const double *a, size_t na,
    const double *x, size_t n,
    double *out);

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
 * The One's WINDING surface (siona gh#1276; rc137) — exact INTEGER
 * readouts of the winding triad the SO->Spin double cover carries.
 * Independent of the S(sigma,theta) adjoint generator; every op is
 * exact-integer -> BYTE-IDENTICAL to the Python (no float). ABI stays 3.
 * ------------------------------------------------------------------ */

/* The divmod-recursive binary TOWER of a WHOLE winding w — the (Z/2)^d
 * hypercube / Cayley-Dickson doubling coordinate. Fills bits_out with the
 * LSB-first bits of |w| (the Class-K magnitude; a retrograde winding negates,
 * never abs()) and writes the count to *n_bits_out. This KEEPS the Z/2 grading
 * (the anti-collapse of `w mod 2`: winding_tower(5)={1,0,1} is DISTINGUISHED
 * from winding_tower(7)={1,1,1}). w == 0 -> empty tower (*n_bits_out = 0).
 * Returns SRMECH_ERR_NULL_ARG (bits_out / n_bits_out NULL), SRMECH_ERR_BAD_INPUT
 * (bits_cap < 0), SRMECH_ERR_OVERFLOW (bits_cap too small; |w| needs up to 64). */
srmech_status_t srmech_winding_tower(int64_t w, uint8_t *bits_out,
                                     int32_t bits_cap, int32_t *n_bits_out);

/* The chirality READOUT via the winding's binary tower — sigma modulated by the
 * parity of the FULL popcount over the triad's towers (every graded bit counts;
 * NOT the bare low bit `w mod 2`). *out = sigma if the total popcount is even,
 * -sigma if odd (so w=5/popcount-2 and w=7/popcount-3 are DISTINGUISHED). No
 * abs(); *out in {+1,-1}. Returns SRMECH_ERR_NULL_ARG (out NULL),
 * SRMECH_ERR_BAD_INPUT (sigma not in {+1,-1}). */
srmech_status_t srmech_sigma_effective(int32_t sigma, int64_t w0, int64_t w1,
                                       int64_t w2, int32_t *out);

/* The double-cover sign (-1)^(w0+w1+w2) — the genuine Spin->SO 2:1 lift (ONE
 * winding flips, TWO restore). *out in {+1,-1} = the parity of the winding sum.
 * Returns SRMECH_ERR_NULL_ARG for out NULL. */
srmech_status_t srmech_spinor_sign(int64_t w0, int64_t w1, int64_t w2,
                                   int32_t *out);

/* The per-metacycle-scale unwrapped-phase TURNS (2*pi*w_k + theta): the full
 * integer turns a theta-only object folds away. Writes the winding triad to
 * turns_out[0..2] (theta is a caller-carried pass-through rational).
 * Returns SRMECH_ERR_NULL_ARG for turns_out NULL. */
srmech_status_t srmech_unwrapped_phase(int64_t w0, int64_t w1, int64_t w2,
                                       int64_t *turns_out);

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
 *   - No N cap: srmech_graph_dense_laplacian / normalized_laplacian /
 *     jacobi_eigvals / dense_matmul_complex write only into the caller's
 *     matrix (degree per-row, d^(−1/2) stashed in the diagonal, Jacobi
 *     rotates in place), so the bound is the caller's RAM, not a compiled
 *     limit (standalone-complete honor).
 *
 * No ABI bump: pure additions to ABI v2 per the Phase B4 convention.
 * ------------------------------------------------------------------ */

/* A from edge list. A[u,v] = A[v,u] = sum of weights of edges between u
 * and v. Self-loops add 2*w to the diagonal (standard convention).
 * out_matrix is n*n doubles, row-major. */
srmech_status_t srmech_graph_dense_adjacency(uint32_t        n,
                                             uint32_t        n_edges,
                                             const uint32_t *edges_u,
                                             const uint32_t *edges_v,
                                             const double   *weights,
                                             double         *out_matrix);

/* L = D - A. Same edge-list inputs. No node cap — degree is computed
 * per-row into the caller's matrix (no scratch). */
srmech_status_t srmech_graph_dense_laplacian(uint32_t        n,
                                             uint32_t        n_edges,
                                             const uint32_t *edges_u,
                                             const uint32_t *edges_v,
                                             const double   *weights,
                                             double         *out_matrix);

/* L_sym = I - D^(-1/2) A D^(-1/2). Isolated vertices (degree 0) have
 * diagonal entry 0. No node cap — d^(-1/2) is stashed in the diagonal
 * (no scratch). */
srmech_status_t srmech_graph_normalized_laplacian(uint32_t        n,
                                                  uint32_t        n_edges,
                                                  const uint32_t *edges_u,
                                                  const uint32_t *edges_v,
                                                  const double   *weights,
                                                  double         *out_matrix);

/* 0.9.0rc105 (issue #1234 Item 3 / F1006 / F1007): magnetic (Hermitian)
 * Laplacian of a DIRECTED graph — the standalone-C builder peer of the
 * Python `laplacian.magnetic_laplacian` (the "tracked next voxel" of the
 * rc26 directed/signed leg). Direction is encoded as a complex phase so
 * the matrix stays Hermitian; the phase comes from the srmech Q61 trig
 * cascade (srmech_cos_q61 / srmech_sin_q61 — NOT libm), byte-exact with
 * the pure-Python Class-N cascade, and pi enters as 4*atan_q61(1) (the
 * same derivation the Python module uses; no libm M_PI).
 *
 * out_matrix is 2*n*n doubles, row-major INTERLEAVED complex (re, im)
 * pairs — the module's complex wire convention.
 *
 * TWO modes, selected by `charges`:
 *   charges == NULL — scalar-q mode (the rc26 construction):
 *       W[u,v] += w (directed);  A_s = (W + W^T)/2;
 *       L[r,c] = -A_s[r,c] * exp(i * 2*pi*q * (W[r,c] - W[c,r])), r != c;
 *       L[r,r] = sum_c A_s[r,c].
 *     `q` is the flux in TURNS per unit net flow (q = 0.25 = quarter
 *     turn per unit imbalance).
 *   charges != NULL — per-edge CHIRAL mode (length n_edges, TURNS): the
 *     dual-sense knowledge-graph encoding (F1007) — a real signed edge
 *     pair (+w, -w) ANNIHILATES in the signed Laplacian, while the two
 *     phase senses e^{+i 2*pi*c} / e^{-i 2*pi*c} are conjugate partners
 *     that SURVIVE. Each edge k = (u, v, w, c) accumulates
 *       L[u,v] += -(w/2) * exp(+i * 2*pi*c)
 *       L[v,u] += -(w/2) * exp(-i * 2*pi*c)      (Hermitian by construction)
 *       deg[u] += w/2;  deg[v] += w/2;  L[r,r] = deg[r]  (real diagonal).
 *     The w/2 matches the scalar mode's (W + W^T)/2 magnitude scale;
 *     (u, v, c) is equivalent to (v, u, -c). `q` is IGNORED in this mode
 *     (the Python surface rejects passing both).
 *
 * No node cap and NO scratch: scalar mode stages W in the imaginary
 * slots of the caller's own out_matrix (the imag half is rewritten by
 * the final pass), so the bound is the caller's RAM (standalone-
 * complete honor). An out-of-range edge endpoint -> SRMECH_ERR_BAD_INPUT;
 * a phase angle with no Q61 form (non-finite / |ang| >= 2^55) ->
 * SRMECH_ERR_BAD_INPUT (the Python peer raises identically).
 * ABI-additive: a new symbol, so SRMECH_ABI_VERSION stays 3. */
srmech_status_t srmech_graph_magnetic_laplacian(uint32_t        n,
                                                uint32_t        n_edges,
                                                const uint32_t *edges_u,
                                                const uint32_t *edges_v,
                                                const double   *weights,
                                                double          q,
                                                const double   *charges,
                                                double         *out_matrix);

/* §51 (issue #1097): the SPARSE / iterative normalized-cut Fiedler — the
 * n-unbounded peer of the dense eigensolver path. Power iteration on the
 * normalized operator B = I + D^(-1/2) W D^(-1/2) (= 2I - L_sym; eigenvalues in
 * [0,2], well-conditioned), deflating the sqrt(deg) (lambda0) mode each step;
 * the converged direction's SIGN is the normalized-cut bisection. Matvec-only
 * (by edge, no CSR) -> O(edges), n unbounded -> breaks the n<=256 dense-
 * eigensolver wall for graph partitioning at corpus scale. `ws` is a CALLER-
 * supplied scratch arena of at least 8*n doubles (so there is NO compiled-in
 * node cap — the bound is the caller's RAM). `out_vec` (length n) receives the
 * sign-bearing Fiedler vector; n < 2 -> the zero vector. Stops early on sign-
 * stability (5 stable-sign steps past a 20-iteration warmup). max_iters caps the
 * power iteration. ABI-additive (a new symbol) -> SRMECH_ABI_VERSION stays 3. */
srmech_status_t srmech_laplacian_fiedler_sparse(uint32_t        n,
                                                uint32_t        n_edges,
                                                const uint32_t *edge_u,
                                                const uint32_t *edge_v,
                                                const double   *weights,
                                                uint32_t        max_iters,
                                                double         *out_vec,
                                                double         *ws,
                                                size_t          ws_len);

/* §52 Part 2 (F793): the OUT-OF-CORE streaming Fiedler. Identical normalized-cut
 * power iteration to srmech_laplacian_fiedler_sparse, but the adjacency is NEVER
 * resident — each edge pass STREAMS a packed edge file via the PAL streaming-read.
 * `path` is a packed binary file of 16-byte records (uint32 u | uint32 v | double w,
 * host byte order; records never straddle a read chunk). Only the O(n) working
 * vectors live in RAM (the caller `ws` arena, >= 8*n doubles — no compiled-in node
 * cap), so a low-RAM target can PARTITION a graph whose edge list does not fit RAM:
 * the low-RAM ENCODE for graph partition (composes §52.1 cooccurrence_topk for the
 * bounded edge SET). `out_vec` (length n) receives the sign-bearing Fiedler vector;
 * n < 2 -> the zero vector. A read that is not a whole number of records (truncated
 * file) -> SRMECH_ERR_BAD_INPUT; an out-of-range endpoint -> SRMECH_ERR_BAD_INPUT.
 * ABI-additive (a new symbol) -> SRMECH_ABI_VERSION stays 3. */
srmech_status_t srmech_laplacian_fiedler_sparse_file(uint32_t      n,
                                                     const char   *path,
                                                     uint32_t      max_iters,
                                                     double       *out_vec,
                                                     double       *ws,
                                                     size_t        ws_len);

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

/* Required workspace length (in doubles) for srmech_hermitian_
 * eigendecompose_ws at a given node count `n`: a working copy of the
 * n×n complex Hermitian matrix in interleaved-double form = 2*n*n
 * doubles. */
#define SRMECH_HERMITIAN_WS_LEN(n) ((size_t)(n) * (size_t)(n) * 2u)

/* DEFAULT compute-guard ceiling for the Hermitian eigendecomposition's
 * node count — a reasonableness limit on the O(n³) dense complex Jacobi,
 * NOT a scratch-buffer cap (the caller owns the 2*n*n workspace). As of
 * rc161 this is the *built-in default* of a CONFIG-DRIVEN value: read the
 * live ceiling with srmech_config_hermitian_max_nodes() (settable via
 * srmech_config_load_toml/_file, key `[hermitian] max_nodes`), not from a
 * compiled-in cap. The real architectural bound is still `ws_len >= 2*n*n`.
 * (rc161 removed the no-`_ws` convenience wrapper + its 1 MiB thread-local
 * static; callers use srmech_hermitian_eigendecompose_ws with a sized
 * workspace, the Python `mat_hermitian_eigendecompose` being one.) */
#define SRMECH_HERMITIAN_DEFAULT_MAX_NODES 2048u

/* ------------------------------------------------------------------ *
 * Runtime config (rc161) — config-FILE-driven library limits, so a
 * compute-guard ceiling tunes per-deployment with NO recompile (the
 * "config-driven, not hard-coded" direction). Defined in srmech_config.c.
 *
 * Set ONCE at startup (before concurrent use); read-only thereafter.
 * Un-set / missing keys keep the built-in default, so behaviour is
 * unchanged until a config overrides it. ABI-additive — new symbols, so
 * SRMECH_ABI_VERSION stays 3.
 * ------------------------------------------------------------------ */

/* Parse a caller-held TOML blob (MCU-safe — a flash image, no filesystem
 * needed) into the live config, using the caller arena `ws` (ws_len bytes;
 * no malloc). Recognised today: `[hermitian] max_nodes`. Unknown keys are
 * ignored. SRMECH_ERR_BAD_INPUT on a syntax error, OVERFLOW if `ws` is too
 * small for the document. */
srmech_status_t srmech_config_load_toml(const char *toml, size_t len,
                                        void *ws, size_t ws_len);

/* Read `path` THROUGH THE PAL (the single OS file surface) into a buffer
 * carved from `ws`, then srmech_config_load_toml it. On a no-filesystem
 * target the PAL returns SRMECH_ERR_IO; use the bytes form instead. */
srmech_status_t srmech_config_load_file(const char *path,
                                        void *ws, size_t ws_len);

/* The live Hermitian-eig node ceiling (default SRMECH_HERMITIAN_DEFAULT_
 * MAX_NODES; overridden by a loaded config). Always > 0. */
uint32_t srmech_config_hermitian_max_nodes(void);

/* Reset every config value to its built-in default (mainly for tests). */
void srmech_config_reset_defaults(void);

/* Hermitian eigendecomposition via complex-Jacobi rotations (caller-
 * workspace entry — the only entry as of rc161; the no-`_ws` convenience
 * overload was removed). Identical numerics + output contract regardless
 * of who owns the workspace; safe to drive concurrently from many threads
 * (the #771 plugin), each passing its own workspace, with no malloc (JPL
 * Rule 3) and no large per-call stack frame.
 * Input: H_interleaved is n*n interleaved-doubles (re, im pairs),
 *   row-major; MUST be Hermitian (caller's responsibility — asserted in
 *   debug builds).
 * Output: out_eigvals = n real ascending-sorted eigenvalues;
 *   out_eigvecs_interleaved = n*n complex unitary matrix V (columns are
 *   eigenvectors). H = V * diag(eigvals) * V^H.
 * `workspace` must be non-NULL with `ws_len >= SRMECH_HERMITIAN_WS_LEN(n)`
 * = 2*n*n doubles (the real architectural bound). `n` is additionally
 * compute-guarded by srmech_config_hermitian_max_nodes() (config-driven,
 * default 2048). Returns SRMECH_ERR_OVERFLOW if `ws_len` is too small, n
 * exceeds the configured ceiling, or the Jacobi sweep
 * (SRMECH_LAPLACIAN_JACOBI_MAX_SWEEPS) does not converge; SRMECH_ERR_NULL_
 * ARG if any required pointer is NULL. Pi-free (atan2-free phase factor).
 *
 * ABI-additive: SRMECH_ABI_VERSION unchanged. */
srmech_status_t srmech_hermitian_eigendecompose_ws(
    uint32_t       n,
    const double  *H_interleaved,
    double        *out_eigvals,
    double        *out_eigvecs_interleaved,
    double        *workspace,
    size_t         ws_len);

/* Dense complex matrix-matrix multiplication: out = A @ B.
 * A_interleaved is m*k interleaved-double pairs (row-major).
 * B_interleaved is k*n interleaved-double pairs (row-major).
 * out_interleaved is m*n interleaved-double pairs (caller-allocated).
 * No m/k/n cap — the product writes only the caller's buffer (no scratch).
 */
srmech_status_t srmech_dense_matmul_complex(
    uint32_t       m,
    uint32_t       k,
    uint32_t       n,
    const double  *A_interleaved,
    const double  *B_interleaved,
    double        *out_interleaved);

/* Elementwise complex multiply: out[i] = a[i] * b[i].
 * a, b, out are n interleaved-double pairs each. No node cap — bounded
 * only by uint32_t / the caller's buffers (no scratch).
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

/* Dense linear solve A·X = B (v0.7.1rc3, #897 §26; v0.7.5rc158 caller-arena).
 * A is n×n, B and the output X are n×nrhs, all row-major doubles (caller-
 * allocated). Gauss–Jordan with partial pivoting; the reusable Class-L float
 * primitive the Schur-complement / DtN float path composes over for its
 * interior solve. A singular A (a wholly-zero pivot column at/below the
 * diagonal) returns SRMECH_ERR_BAD_INPUT. No libm: a solve is + − × ÷ only.
 *
 * NO compiled-in size cap (rc158 standalone-complete honor, the genome rc154
 * precedent / [[feedback_c_must_be_standalone_complete_no_python_fallback]]):
 * the augmented [A | B] working matrix is bump-carved from the CALLER arena
 * `ws` (ws_len bytes), so the bound is the caller's RAM — a host sizes it
 * large, a microcontroller small. Size `ws` from srmech_dense_solve_arena_bytes;
 * an under-sized arena returns SRMECH_ERR_OVERFLOW. The pure-Python exact-
 * rational solve is the COMPLETE alternative implementation for no-C hosts,
 * not a rescue path. ABI: this RENAMES the old capped srmech_dense_solve_f64 to
 * the arena form; the Python ctypes shim hasattr-guards the new name (a stale
 * lib lacking it falls to pure-Python), so SRMECH_ABI_VERSION stays 3.
 */
size_t srmech_dense_solve_arena_bytes(uint32_t n, uint32_t nrhs);

srmech_status_t srmech_dense_solve_f64_ws(
    uint32_t       n,
    uint32_t       nrhs,
    const double  *A,
    const double  *B,
    double        *out_X,
    void          *ws,
    size_t         ws_len);

/* Exact cyclotomic-integer DFT (v0.7.5rc29, #928) — the native twin of
 * srmech.amsc.cascade.exact_dft. A power-of-two-length integer / Gaussian-
 * integer signal transforms to the exact ℤ[ζ_N] spectrum by PURE INTEGER
 * add/subtract (ζ^{N/2} = -1 is a Class-K sign-flip, never abs/fabs); the
 * single FPU lift ζ → e^{-2πi/N} is on the Python side. re/im are length-N
 * int64 component arrays; out_re/out_im are length N·(N/2) int64 (row k holds
 * the N/2 cyclotomic coefficients of X[k] at [k·N/2, (k+1)·N/2)). inverse != 0
 * uses ζ^{-nk}. N must be a power of two ≥ 2 (else SRMECH_ERR_BAD_INPUT) — NO
 * compiled-in size cap (rc156 standalone-complete honor: the kernel writes only
 * the caller's out_re/out_im, no scratch to bound). The genuine domain limit is
 * the int64 element magnitude: keep N·max|signal| int64-safe (the Python wrapper
 * enforces this and routes larger magnitudes to its arbitrary-precision bignum
 * path). No libm: an exact DFT is integer + − only. ABI-additive: new symbol,
 * SRMECH_ABI_VERSION stays 3.
 */
srmech_status_t srmech_exact_dft_i64(
    uint32_t        n,
    int             inverse,
    const int64_t  *re,
    const int64_t  *im,
    int64_t        *out_re,
    int64_t        *out_im);

/* Numeric complex128 FFT / IFFT (0.9.0rc139, #743/#747 Foundation F1) — the
 * numeric twin of srmech.amsc.cascade.spectral_cascades.fft/ifft that the
 * whole signal_processing fft-family dispatches to. In/out are INTERLEAVED
 * (re, im) length-2n double buffers (the Complex128 / Vec carrier layout, so
 * the dispatch is zero-copy). inverse != 0 applies the single 1/N scale
 * (matching NumPy ifft + the pure-Python cascade addend-for-addend). n is
 * arbitrary: a power-of-two n runs the iterative radix-2 Cooley-Tukey
 * butterfly; any other (incl. PRIME) n runs Bluestein's chirp-z, so this is
 * NOT power-of-2-only. NUMERIC (FPU-tol), not byte-exact — contrast the
 * exact-integer srmech_exact_dft_i64. No libm: twiddle / chirp trig is the
 * libm-free srmech_cos / srmech_sin. No abs (the FFT reads no magnitude).
 * `out` MUST NOT alias `in` (else SRMECH_ERR_BAD_INPUT). All scratch is
 * bump-carved from the CALLER arena `ws` (ws_len bytes; no malloc) — size it
 * from srmech_fft_c128_ws_bound(n); an under-sized arena returns
 * SRMECH_ERR_OVERFLOW. n == 0 writes nothing. The pure-Python cascade is the
 * COMPLETE alternative for no-C hosts. ABI-additive: new symbols, so
 * SRMECH_ABI_VERSION stays 3 (the Python ctypes shim hasattr-guards them). */
size_t srmech_fft_c128_ws_bound(size_t n);

srmech_status_t srmech_fft_c128(
    const double  *in_interleaved,
    size_t         n,
    int            inverse,
    double        *out_interleaved,
    double        *ws,
    size_t         ws_len);

/* Numeric f64 QR + SVD (0.9.0rc140, Foundation F2) — the numeric-LA twins the
 * subspace / MIMO / LA family (matrix_cascades.{qr,svd,lstsq} + the
 * signal_processing subspace ops) dispatches its REAL path to (the complex
 * path keeps its Gram-eigen / list-Householder pure route). NUMERIC (FPU-tol),
 * NOT byte-exact. No libm (the only root is the Class-N srmech_rational_sqrt);
 * no abs()/fabs() (every magnitude is a Class-K sign-branch). ABI-additive:
 * new symbols, so SRMECH_ABI_VERSION stays 3 (the Python ctypes shim
 * hasattr-guards them).
 *
 * srmech_qr_f64 — Householder QR A = Q*R, A m*n row-major, Q m*m orthogonal,
 * R m*n upper-trapezoidal (both caller-allocated). DIRECT (no iteration): the
 * product of min(m,n) reflectors H = I - beta*v*v^T; the phase
 * alpha = -sign(x0)*||x|| is a Class-K pin-slot (a sign-BRANCH). The reflector
 * vector v is bump-carved from the CALLER arena `ws` (>= srmech_qr_f64_ws_bound
 * BYTES = m doubles); an under-sized arena returns SRMECH_ERR_OVERFLOW. m==0 or
 * n==0 writes nothing. The pure-Python list-Householder is the COMPLETE
 * alternative for no-C hosts. */
size_t srmech_qr_f64_ws_bound(uint32_t m, uint32_t n);

srmech_status_t srmech_qr_f64(uint32_t       m,
                              uint32_t       n,
                              const double  *A_rowmajor,
                              double        *Q_out,
                              double        *R_out,
                              double        *ws,
                              size_t         ws_len);

/* srmech_svd_f64 — A = U*diag(S)*V^T (A m*n row-major, m>=n), via ONE-SIDED
 * JACOBI (Hestenes): orthogonalise the columns of a working copy by column
 * Jacobi rotations accumulated into V; the converged column norms are the
 * singular values, U = W*diag(1/S). Outputs (all caller-allocated): U_out m*n
 * (thin left singular vectors; a zero-singular-value column is left zero for
 * the caller's orthonormal completion), S_out n (DESCENDING, >= 0), V_out n*n
 * (right singular vectors as COLUMNS, descending). m<n returns
 * SRMECH_ERR_BAD_INPUT — the Python peer transposes and swaps U/V.
 *
 * ITERATIVE -> the CONVERGENCE CONTRACT: an EXPLICIT sweep cap (JPL Rule 2
 * bounded loop). A sweep that rotates NO pair (every off-diagonal below tol) is
 * converged -> SRMECH_OK; hitting the cap with a rotation still pending returns
 * SRMECH_ERR_OVERFLOW (a NOT-CONVERGED status, NEVER a silent wrong answer), so
 * the Python dispatch falls back to the pure Gram-eigen SVD. The working copy
 * W (m*n) + rotation accumulator V (n*n) are bump-carved from the CALLER arena
 * `ws` (>= srmech_svd_f64_ws_bound BYTES); an under-sized arena returns
 * SRMECH_ERR_OVERFLOW. The pure-Python Gram-eigen SVD is the COMPLETE
 * alternative for no-C hosts. */
size_t srmech_svd_f64_ws_bound(uint32_t m, uint32_t n);

srmech_status_t srmech_svd_f64(uint32_t       m,
                               uint32_t       n,
                               const double  *A_rowmajor,
                               double        *U_out,
                               double        *S_out,
                               double        *V_out,
                               double        *ws,
                               size_t         ws_len);

/* srmech_jade_jointdiag — the JADE (Cardoso-Souloumiac 1993) Givens joint-
 * diagonalisation sweep, the iterative kernel at the heart of ICA-JADE
 * (0.9.0rc155, BATCH B-residue: the FINAL compute op -> python_only_debt=0).
 * Given the fourth-order cumulant tensor `cum` (k*k*k*k row-major, MUTATED as
 * the working buffer), drive its (i,j) slices toward joint diagonality by a
 * data-dependent sequence of Givens rotations, accumulating them into the
 * un-mixing rotation `v_out` (k*k row-major, initialised to I here). The
 * per-(i,j) angle is theta = 0.25*atan2(2*C[i][j][i][j],
 * C[i][i][i][i]-C[j][j][j][j]) (the simplified-JADE update), applied when
 * |theta| >= tol; the first-axis tensor rotation is applied TWICE per Givens
 * step (a preserved quirk of the reference). ITERATIVE -> an EXPLICIT sweep
 * cap `max_iter` (JPL Rule 2 bounded loop); a sweep whose Σ|theta| < tol is
 * converged and stops early (matching the Python reference, which never
 * errors on non-convergence — it returns the current rotation).
 *
 * NUMERIC (FPU-tol), NOT byte-exact: the angle/twiddle are the libm-free
 * Class-N cascades srmech_atan2 / srmech_cos / srmech_sin (the same the
 * Python rational.{atan2,cos,sin} dispatch to); JADE's basis is
 * permutation/sign/scale-ambiguous, so native and pure recover the same
 * sources WITHIN-TOL, not byte-for-byte. No abs()/fabs() (Class-K sign
 * branch). Scratch (G + V·G accumulator + rotated-cumulant ping-pong) is
 * bump-carved from the CALLER arena `ws` (>= srmech_jade_jointdiag_ws_bound
 * BYTES = (2*k² + k⁴) doubles); an under-sized arena returns
 * SRMECH_ERR_OVERFLOW. The pure-Python sweep is the COMPLETE alternative for
 * no-C hosts (and the parity oracle). Additive -> ABI stays 3. */
size_t srmech_jade_jointdiag_ws_bound(uint32_t k);

srmech_status_t srmech_jade_jointdiag(double   *cum,
                                      uint32_t  k,
                                      uint32_t  max_iter,
                                      double    tol,
                                      double   *v_out,
                                      double   *ws,
                                      size_t    ws_len);

/* ------------------------------------------------------------------ *
 * The resonant-spectrum closure (§75 / F928) — a Class-L coupling
 * COMPOSITE over the existing kernels (srmech_hermitian_eigendecompose_ws
 * + srmech_best_rational + srmech_factor), the C twin of
 * srmech.amsc.coupling.resonant_spectrum. Reads a real-symmetric coupling
 * Laplacian L as a stored (excitation-free) object: the eigenvalue
 * "tensions" (ascending), the eigenvector "modes" (columns), the force-
 * orders L^k = V·diag(Λ^k)·Vᵀ from the ONE eigensolve, and the adjacent-
 * tension resonance ratios + lock (smooth-den) vs libration (large-prime-
 * den) verdicts. Standalone-complete: all scratch is bump-carved from the
 * CALLER arena `ws` (no malloc). ABI-additive: new symbols, ABI stays 3.
 * ------------------------------------------------------------------ */

/* The caller arena size IN BYTES srmech_resonant_spectrum needs for an
 * n×n Laplacian (the interleaved-H input + eigensolve workspace + the
 * complex/real eigenvector copies). Size `ws_len` ≥ this. */
size_t srmech_resonant_spectrum_arena_bytes(uint32_t n);

/* Read the real-symmetric coupling Laplacian L (n×n row-major real,
 * `L_rowmajor`) as a resonant object. `orders` ≥ 1 force-orders, `max_den`
 * ≥ 1 the best_rational ceiling. Caller pre-sizes every output:
 *   out_tensions[n]              — eigenvalues ASCENDING (real)
 *   out_modes[n*n]               — eigenvectors, row-major, columns = modes
 *                                  (real; sign-pinned like the Python op)
 *   out_force_orders[orders*n*n] — [L, L^2, …, L^orders] row-major real,
 *                                  contiguous per order
 *   out_res_pairs[(n-1)*2]       — (i, j) adjacent-tension pair indices
 *   out_res_ratio[(n-1)*2]       — (num, den) of each tension ratio
 *   out_res_locked[n-1]          — 1 = LOCK (smooth/2-adic den), 0 = libration
 *   *out_res_count               — number of resonance rows actually written
 * `ws` (ws_len bytes) sized from srmech_resonant_spectrum_arena_bytes.
 * Returns SRMECH_ERR_BAD_INPUT for orders<1 / max_den<1, SRMECH_ERR_NULL_ARG
 * for a NULL pointer (n>0), SRMECH_ERR_OVERFLOW for a too-small arena or a
 * non-convergent eigensolve. n==0 writes nothing + *out_res_count=0. */
srmech_status_t srmech_resonant_spectrum(
    uint32_t       n,
    const double  *L_rowmajor,
    uint32_t       orders,
    uint64_t       max_den,
    double        *out_tensions,
    double        *out_modes,
    double        *out_force_orders,
    int32_t       *out_res_pairs,
    uint64_t      *out_res_ratio,
    int32_t       *out_res_locked,
    uint32_t      *out_res_count,
    double        *ws,
    size_t         ws_len);

/* ------------------------------------------------------------------ *
 * The spectral theta / heat trace (0.9.0rc108; issue #1234 Item 2 /
 * F1007) — a Class-L COMPOSITE over the existing kernels
 * (srmech_jacobi_eigvals / srmech_hermitian_eigendecompose_ws +
 * srmech_exp + srmech_graph_magnetic_laplacian), the C twin of
 * srmech.amsc.laplacian.heat_trace / .ground_state_flux_response.
 * Theta(t) = Tr(e^{-tL}) = sum_k exp(-t*lambda_k) IS a theta function of
 * the Laplacian (on a cycle, the Jacobi-theta family) — the
 * read-independent spectral summary. F1007: under magnetic flux the FULL
 * trace is flux-invariant (Poisson -> the modular/holomorphic part) while
 * the flux shadow lives only in the ground state lambda_min(flux) — the
 * companion srmech_ground_state_flux_response is that shadow reader. The
 * exp is srmech_exp (the Q61 libm-free Class-N cascade) at the
 * spectral-summary boundary — Theta is a float summary, never an exact
 * decision. Standalone-complete: all scratch is bump-carved from the
 * CALLER arena `ws` (no malloc). ABI-additive: new symbols, ABI stays 3.
 * ------------------------------------------------------------------ */

/* The caller arena size IN BYTES srmech_heat_trace needs for an n*n L —
 * real (is_complex == 0): the in-place Jacobi work copy + eigvals;
 * complex (is_complex != 0): the Hermitian eigensolve staging + eigvals.
 * Size `ws_len` >= this. */
size_t srmech_heat_trace_arena_bytes(uint32_t n, int is_complex);

/* Theta(t_i) = sum_k exp(-t_i * lambda_k) for each of the n_t t-values,
 * from ONE eigensolve of L. is_complex == 0: `L` is n*n row-major REAL
 * symmetric (spectrum via srmech_jacobi_eigvals, sorted ascending);
 * is_complex != 0: `L` is n*n row-major INTERLEAVED-complex (re, im)
 * Hermitian (spectrum via srmech_hermitian_eigendecompose_ws, ascending;
 * subject to the config-driven Hermitian node ceiling). Symmetry /
 * Hermiticity is the caller's responsibility (the eigensolve ops'
 * contract). out_theta receives n_t values. n == 0 writes Theta = 0 (the
 * empty spectrum); n_t == 0 writes nothing. `ws` (ws_len bytes) sized
 * from srmech_heat_trace_arena_bytes. Returns SRMECH_ERR_NULL_ARG for a
 * NULL required pointer, SRMECH_ERR_OVERFLOW for a too-small arena / a
 * non-convergent eigensolve. */
srmech_status_t srmech_heat_trace(
    uint32_t       n,
    int            is_complex,
    const double  *L,
    uint32_t       n_t,
    const double  *t_values,
    double        *out_theta,
    double        *ws,
    size_t         ws_len);

/* The caller arena size IN BYTES srmech_ground_state_flux_response needs
 * for an n-node / n_edges-edge graph. Size `ws_len` >= this. */
size_t srmech_ground_state_flux_response_arena_bytes(uint32_t n,
                                                     uint32_t n_edges);

/* lambda_min(flux_i) — the magnetic ground state as a function of flux
 * (the F1007 shadow reader). For each of the n_flux flux values (in
 * TURNS, the rc105 charge unit): every edge k gets charge
 * flux * charge_pattern[k] (charge_pattern NULL -> the uniform 1/n_edges
 * default, so a single cycle's total holonomy is `flux` turns), the
 * magnetic Laplacian is built via srmech_graph_magnetic_laplacian
 * (per-edge chiral mode; weights NULL -> 1.0 each), and
 * out_lambda_min[i] receives its smallest eigenvalue. Integer flux is
 * gauge-equivalent to flux = 0 (holonomy e^{i*2*pi*flux} = 1), so
 * lambda_min is periodic in integer flux. n >= 1 (an empty graph has no
 * ground state -> SRMECH_ERR_BAD_INPUT); n_flux == 0 writes nothing.
 * `ws` (ws_len bytes) sized from
 * srmech_ground_state_flux_response_arena_bytes. Returns
 * SRMECH_ERR_NULL_ARG for a NULL required pointer, SRMECH_ERR_BAD_INPUT
 * for an out-of-range edge endpoint / a phase with no Q61 form,
 * SRMECH_ERR_OVERFLOW for a too-small arena / a non-convergent
 * eigensolve. */
srmech_status_t srmech_ground_state_flux_response(
    uint32_t        n,
    uint32_t        n_edges,
    const uint32_t *edges_u,
    const uint32_t *edges_v,
    const double   *weights,
    const double   *charge_pattern,
    uint32_t        n_flux,
    const double   *fluxes,
    double         *out_lambda_min,
    double         *ws,
    size_t          ws_len);

/* ------------------------------------------------------------------ *
 * EPH — the complex-time Wick-rotation propagator (0.9.0rc136; siona
 * gh#1274) — a Class-L COMPOSITE over the existing kernels
 * (srmech_hermitian_eigendecompose_ws + srmech_exp + srmech_cos +
 * srmech_sin), the C twin of srmech.amsc.laplacian.propagate.
 *
 * EPH = harvest = Propagate · excite: a propagator P = e^{-zL}
 * (operator) applied to an excitation u0 (operand) → the harvest H.
 * The thermal e^{-tL} and the coherent e^{-itL} are NOT two ops — they
 * are the ONE complex-time propagator e^{-zL} with z COMPLEX, the `i`
 * being the WICK-ROTATION PHASE. arg(z) is the coherence dial:
 * z REAL → thermal diffusion (decoherent, damping), z IMAGINARY →
 * coherent unitary quantum walk (norm-preserving), arg(z) BETWEEN →
 * partial coherence (the regime only the unified form can name). The
 * neuron is one propagator choice (RBS-SNN = EPH-with-a-synaptic-
 * propagator P = connectome/weight matrix); no privileged instance.
 * Composes the framework's Class-L Wick rotation (the signed-metric /
 * Wick op = a Class-L signed-Laplacian variant).
 *
 * harvest = e^{-zL}·u0 = V·diag(e^{-z·λ_k})·V^H·u0 from ONE
 * eigensolve: the per-mode scalar e^{-zλ_k} = e^{-Re(z)·λ_k}·
 * (cos(Im(z)·λ_k) − i·sin(Im(z)·λ_k)) uses srmech_exp (real damping,
 * the Q61 libm-free Class-N cascade) + srmech_cos / srmech_sin
 * (oscillation; their internal octant reduction IS the 2π argument
 * fold in the Q61 basis — the algebraic twin of the Python op's
 * explicit Machin-2π Class-N-series seam-fold, so both are correct at
 * any t·λ). The harvest is basis-invariant (each eigenvector appears
 * in both V and V^H), so it agrees with the Python op to the
 * eigensolve tolerance regardless of the eigenvector sign / degenerate-
 * subspace basis convention. Standalone-complete: all scratch is
 * bump-carved from the CALLER arena `ws` (no malloc). ABI-additive:
 * new symbols, so SRMECH_ABI_VERSION stays 3.
 * ------------------------------------------------------------------ */

/* The caller arena size IN BYTES srmech_eph_propagate needs for an n*n
 * L (the interleaved Hermitian input + eigensolve workspace + the
 * complex eigenvectors + the projected mode vector). Same arena for
 * real and complex input (real L is lifted to interleaved (re, 0)).
 * Size `ws_len` >= this. */
size_t srmech_eph_propagate_arena_bytes(uint32_t n, int is_complex);

/* harvest = e^{-zL}·u0 via the eigenbasis, from ONE eigensolve of L.
 * is_complex == 0: `L` is n*n row-major REAL symmetric; is_complex != 0:
 * `L` is n*n row-major INTERLEAVED-complex (re, im) Hermitian (subject
 * to the config-driven Hermitian node ceiling). `u0` and `out_harvest`
 * are each n INTERLEAVED-complex (re, im) pairs (a real excitation
 * rides as (re, 0)). z = z_re + i·z_im is the complex time. n == 0
 * writes nothing. `ws` (ws_len bytes) sized from
 * srmech_eph_propagate_arena_bytes. Returns SRMECH_ERR_NULL_ARG for a
 * NULL required pointer, SRMECH_ERR_OVERFLOW for a too-small arena / a
 * non-convergent eigensolve, SRMECH_ERR_BAD_INPUT if an oscillation
 * argument |Im(z)·λ_k| exceeds the srmech_cos/sin reduction bound
 * (~2^55, far beyond any physical t·λ). */
srmech_status_t srmech_eph_propagate(
    uint32_t       n,
    int            is_complex,
    const double  *L,
    const double  *u0_interleaved,
    double         z_re,
    double         z_im,
    double        *out_harvest_interleaved,
    double        *ws,
    size_t         ws_len);

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

/* Smallest prime strictly greater than n (the prime successor). Composes the
 * trial-division srmech_is_prime over the odd candidates above n. 0 and 1 step
 * to 2; 2 steps to 3. Returns SRMECH_ERR_OVERFLOW only if no prime exists below
 * the uint64 wrap (unreachable for any real n -- the largest prime gap under
 * 2^64 is ~1500). srmech 0.9.0rc44, additive symbol (no ABI bump). */
srmech_status_t srmech_next_prime(uint64_t n, uint64_t *out);

/* ------------------------------------------------------------------ *
 * Class I -- modular linear algebra: GF(p) RREF (srmech 0.9.0rc44).
 *
 * Rung 1 of the CRT-QMat re-fibration arc: the swell-free GF(p) Gauss-
 * Jordan that the later CRT solve composes (solve mod several machine-
 * int primes -> CRT-combine -> rational-reconstruct once). Bounded
 * machine-int arithmetic only -- NO fraction growth, NO bignum. The
 * matrix + pivot buffers are caller-owned (no malloc).
 *
 * Additive symbol -- no ABI bump.
 * ------------------------------------------------------------------ */

/* Reduce `matrix` (an n_rows x n_cols int64 matrix, ROW-MAJOR, caller-owned)
 * to reduced row-echelon form over the field GF(p), IN PLACE. Entries may be
 * negative on input; they are canonicalised into [0, p) first and every output
 * entry lies in [0, p). Requires p an odd prime with 2 < p < 2**31 (so a*b fits
 * uint64); returns SRMECH_ERR_BAD_INPUT otherwise. Writes the pivot column of
 * each pivot row into `out_pivots` (caller buffer of >= min(n_rows, n_cols)
 * uint32) and the rank into `*out_rank`. Primality of p is the caller's
 * contract (the arithmetic domain bound is the only thing guarded here). */
srmech_status_t srmech_gf_rref(int64_t  *matrix,
                               uint32_t  n_rows,
                               uint32_t  n_cols,
                               uint64_t  p,
                               uint32_t *out_pivots,
                               uint32_t *out_rank);

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

/* 0.9.0rc8 Q61 model constants (F868) — the fixed-point scale + the two
 * transcendental recombine anchors a C-ONLY host needs to reassemble the EXACT
 * rational that Python's rational.{sin,cos,tan,atan,atan2,exp,log,sqrt,hypot}
 * return, with NO Python present. The *_q61 peers below hand back the int64 Q61
 * pieces; these three constants close the assembly so the full transcendental
 * surface is computable standalone:
 *   sin/cos/atan : value = out_q61 / SRMECH_Q61_ONE                  (exact int64)
 *   exp          : value = (out_core / SRMECH_Q61_ONE) * 2^out_n     (ldexp scale)
 *   log          : value = (out_logm + out_e * SRMECH_Q61_LN2) / SRMECH_Q61_ONE
 *                  — out_e * ln2 exceeds int64; recombine in int128 / a bignum
 *                  for the EXACT rational (Python uses arbitrary-precision ints),
 *                  or in double for the libm-faithful float projection.
 *   sqrt         : value = out_root * 2^out_p                        (no constant)
 *   tan          : sin-peer / cos-peer                               (exact Q/Q)
 *   atan2        : atan-peer + quadrant shift by SRMECH_Q61_HALF_PI (+-pi/2) and
 *                  2*SRMECH_Q61_HALF_PI (+-pi), per sign(x), sign(y)
 *   hypot        : sqrt-peer of (a*a + b*b)
 * Values are round(c * 2^61). Single-line #defines (JPL Rule 8 clean). */
#define SRMECH_Q61_FBITS    61
#define SRMECH_Q61_ONE      (INT64_C(1) << SRMECH_Q61_FBITS)   /* 1.0 in Q61 = 2^61 */
#define SRMECH_Q61_LN2      INT64_C(1598288580650331957)       /* round(ln2  * 2^61) */
#define SRMECH_Q61_HALF_PI  INT64_C(3622009729038561421)       /* round(pi/2 * 2^61) */

/* 0.9.0rc7 stay-rational Q61 peers (F868). These return the EXACT int64 Q61
 * cascade value (denominator 2^61) BEFORE the float projection, so the Python
 * rational.{sin,cos,atan} dispatch to native AND keep the full 61-bit rational
 * (Q(*out_q61, 2^61)) instead of a double promoted back to Q. Same cores. A
 * non-finite (or |x| >= 2^55) argument has no Q61 form -> SRMECH_ERR_BAD_INPUT.
 * A C-only host reassembles the rational via the SRMECH_Q61_* constants above.
 * Additive -> ABI unchanged. */
srmech_status_t srmech_sin_q61(double x, int64_t *out_q61);
srmech_status_t srmech_cos_q61(double x, int64_t *out_q61);
srmech_status_t srmech_atan_q61(double x, int64_t *out_q61);

/* Class-N rational sqrt cascade (v0.7.0rc45). sqrt(x) (x >= 0) via an INTEGER
 * floor-isqrt on a scaled radicand (portable two-limb 128-bit isqrt; no libm,
 * no float sqrt, no __int128) + IEEE-exponent-field power-of-two scaling.
 * srmech_laplacian.c's cyclic-Jacobi eigensolver routes through this so the
 * executable runs the cascade. Machine-epsilon vs libm; negative x ->
 * SRMECH_ERR_BAD_INPUT (out = NaN). Additive -> ABI unchanged. */
srmech_status_t srmech_rational_sqrt(double x, double *out);

/* 0.9.0rc7 stay-rational Q61 peer (F868). sqrt(x) = root * 2^(e/2 - K) EXACTLY
 * (root = isqrt(M << 2K), K = 27). Returns the integer pieces (*out_root,
 * *out_p) so the Python rational.sqrt forms Q(root << p, 1) for p >= 0 else
 * Q(root, 1 << -p). sqrt(0) -> (0, 0); negative / non-finite -> BAD_INPUT.
 * Additive -> ABI unchanged. */
srmech_status_t srmech_sqrt_q61(double x, int64_t *out_root, int64_t *out_p);

/* 0.9.0rc13 public integer floor-sqrt — floor(sqrt((nhi:nlo))) for a 128-bit
 * unsigned radicand, written to *out_root. Exposes the two-limb isqrt the
 * sqrt cascade already uses as a standalone-C symbol so a C-only host (and the
 * Python rational._integer_sqrt dispatch) needs NO stdlib math.isqrt. The
 * Python peer falls back to arbitrary-precision integer-Newton beyond 128 bits.
 * Additive -> ABI unchanged. */
srmech_status_t srmech_isqrt(uint64_t nhi, uint64_t nlo, uint64_t *out_root);

/* 0.9.0rc10 hypercomplex exp(mu*theta) twiddle (F882, srmech #205). Fills out8
 * (an 8-element int64 array) with the unit exponential q = cos(theta) +
 * mu*sin(theta) in Q61 (denominator 2^61): out8[0] = cos(theta), out8[1..k] =
 * sin(theta)/sqrt(k), out8[k+1..7] = 0. mu = the equal-weight UNIT pure-imaginary
 * over the first k_axes octonion axes, k_axes in {1,3,7} -> C/H/O. The eight
 * components feed a Cayley-Dickson multiply (the literal QDFT/ODFT twiddle), then
 * one projection. Byte-exact with the Python pure-Q61 cascade.hypercomplex_exp.
 * Non-finite / |theta| >= 2^55, or k_axes not in {1,3,7} -> SRMECH_ERR_BAD_INPUT.
 * Additive -> ABI unchanged. */
srmech_status_t srmech_hypercomplex_exp_q61(double theta, int k_axes,
                                            int64_t *out8);

/* 0.9.0rc16 exact-Q61 (sigma,theta,mu) octonion coupler — the C-host peer of
 * cascade.hypercomplex_dft.hypercomplex_couple (closes the rc12 sed_couple /
 * sed_uncouple transitive-ratchet allowlist). T = exp(eff*mu) = cos(eff) +
 * sin(eff)*mu, with `eff = sigma*(-1 if inverse)*theta` and `mu` a caller-
 * provided UNIT pure-imaginary Q61 8-vector (denominator 2^61); out8 = T*streams8
 * (form_is_left != 0) or streams8*T (the non-commutative left/right forms), via
 * the Q61 trig cascade + srmech_cd_basis_product structure constants + the Q61
 * fixed-point multiply. Byte-exact with the pure-Q61 Python mirror. Non-finite /
 * |eff| >= 2^55 -> SRMECH_ERR_BAD_INPUT (the cos/sin peers gate it). Additive ->
 * ABI unchanged. */
srmech_status_t srmech_hypercomplex_couple_q61(double eff, const int64_t streams8[8],
                                               const int64_t mu8[8], int form_is_left,
                                               int64_t out8[8]);

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

/* 0.9.0rc7 stay-rational Q61 peers (F868). Return the EXACT rational pieces so
 * the Python rational.{exp,log} dispatch to native AND keep full Q61 provenance:
 *   srmech_exp_q61: exp(x) = (core / 2^61) * 2^n -> (*out_core, *out_n); Python
 *     forms Q(core << n, 2^61) (n>=0) or Q(core, 2^61 << -n). NaN / impractical
 *     |x| (n past int64) -> BAD_INPUT (no DBL_MAX gate — the rational has none).
 *   srmech_log_q61: log(x) = (logm + e*ln2) / 2^61 -> (*out_logm = log(mantissa)
 *     in Q61, *out_e); Python forms Q(logm + e*_Q61_LN2, 2^61) with the cascade-
 *     derived Q61 ln2. x <= 0 / non-finite -> BAD_INPUT.
 * Additive -> ABI unchanged. */
srmech_status_t srmech_exp_q61(double x, int64_t *out_core, int64_t *out_n);
srmech_status_t srmech_log_q61(double x, int64_t *out_logm, int64_t *out_e);

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

/* bind(a, b): component-wise XOR. out[i] = a[i] ^ b[i]. Commutative,
 * associative, self-inverse: bind(a, bind(a, b)) = b. */
srmech_status_t srmech_hdc_bind(const uint8_t *a,
                                const uint8_t *b,
                                uint32_t       n_bytes,
                                uint8_t       *out);

/* bundle(vectors, n_vectors): majority across n_vectors at each bit position.
 * Returns SRMECH_ERR_BAD_INPUT for even n_vectors (BSC convention requires
 * odd-count for clean majority; caller can pad with tie-breaker vector).
 * No n_vectors cap — bound is the caller's RAM (the bit-count is uint32). */
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

/* hdc_hamming(a, b): EXACT integer bit-Hamming distance (count of differing
 * bits = popcount of the XOR), the F868 stay-rational recall key before the
 * float divide (similarity = 1 - 2*hamming/D). Additive symbol — no ABI bump. */
srmech_status_t srmech_hdc_hamming(const uint8_t *a,
                                   const uint8_t *b,
                                   uint32_t       n_bytes,
                                   uint32_t      *out);

/* similarity(a, b): 1 - 2 * hamming(a, b) / D in [-1, 1]. +1 = identical,
 * 0 = orthogonal (Hamming(a,b) = D/2), -1 = bit-complementary — the
 * display-boundary collapse of srmech_hdc_hamming. */
srmech_status_t srmech_hdc_similarity(const uint8_t *a,
                                      const uint8_t *b,
                                      uint32_t       n_bytes,
                                      double        *out);

/* bundle_with_ties(vectors, n_vectors, n_bytes): bitwise majority across ANY
 * number of BSC vectors, with the tie state surfaced. Unlike srmech_hdc_bundle
 * (odd-count only), accepts any n_vectors: out_majority bit = 1 where strictly
 * more than half the inputs are set (a tie -> 0; odd n_vectors == srmech_hdc_bundle
 * exactly); out_ties bit = 1 where set / unset counts are exactly equal (even
 * n_vectors only). A tie is a Class-K event; counts only, no abs. No n_vectors
 * cap. Additive symbol — no ABI bump. */
srmech_status_t srmech_hdc_bundle_with_ties(const uint8_t * const *vectors,
                                            uint32_t                n_vectors,
                                            uint32_t                n_bytes,
                                            uint8_t                *out_majority,
                                            uint8_t                *out_ties);

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
 * odd-count restriction (the 0 state absorbs ties). No n_vectors cap —
 * bound is the caller's RAM (the sum accumulator is int32). */
srmech_status_t srmech_polar_bundle(const int8_t * const *vectors,
                                    uint32_t              n_vectors,
                                    uint32_t              n,
                                    int8_t               *out);

/* polar_random(key, key_length, D): D draws of CPython random.Random(seed)
 * .randrange(-1, 2), BYTE-IDENTICAL. `key` is the seed's little-endian uint32
 * words (the Python wrapper splits the seed int; a C-only / MCU host passes its
 * own entropy words). Fills `out` (int8) with D values in {-1, 0, +1} via
 * MT19937 + getrandbits(2) rejection (_randbelow(3) — a DIFFERENT stream from
 * klein4_random's _randbelow(4)). Standalone-complete: the 624-word state is
 * stack-resident — no malloc, no compiled-in cap (bound is the caller's `out`).
 * Additive symbol — no ABI bump. */
srmech_status_t srmech_polar_random(const uint32_t *key,
                                    size_t          key_length,
                                    uint32_t        D,
                                    int8_t         *out);

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
 * No n_vectors cap — bound is the caller's RAM (the 1-counts are uint32). */
srmech_status_t srmech_klein4_bundle(const uint8_t * const *vectors,
                                     uint32_t               n_vectors,
                                     uint32_t               n,
                                     uint8_t               *out);

/* klein4_phase_key(D, start, width, elem): the V4 code `elem` on the circular
 * slot-window [start, start+width) mod D, identity (0) elsewhere — the §59 /
 * F861 population-code CONTINUOUS-PHASE key (the chirality-native analogue of
 * HRR / polar phase). Caller picks start = round(frac*D) mod D and width (the
 * half-window D/2 gives the 1 − 2·circ_dist similarity law). Additive symbol —
 * no ABI bump; no compiled-in cap (bound is the caller's `out` of length D). */
srmech_status_t srmech_klein4_phase_key(uint32_t  D,
                                        uint32_t  start,
                                        uint32_t  width,
                                        uint8_t   elem,
                                        uint8_t  *out);

/* klein4_chunk_resolve(chunks, n_chunks, key, D, candidates, n_candidates):
 * §58 / F837 max-resonance read over a CAPACITY-BOUNDED chunk-set. `chunks` is
 * n_chunks*D, `candidates` is n_candidates*D (row-major, codes {0,1,2,3}). For
 * each candidate, out_counts[j] = MAX over chunks of the integer match-count
 * between (chunk XOR key) and that candidate — the F868 stay-rational recall
 * key before the /D divide (Python wraps Q(count, D)). Additive symbol — no ABI
 * bump; no compiled-in cap (bound is the caller's arrays). */
srmech_status_t srmech_klein4_chunk_resolve(const uint8_t *chunks,
                                            uint32_t       n_chunks,
                                            const uint8_t *key,
                                            uint32_t       D,
                                            const uint8_t *candidates,
                                            uint32_t       n_candidates,
                                            uint32_t      *out_counts);

/* klein4_random(key, key_length, D): D draws of CPython random.Random(seed)
 * .randrange(4), BYTE-IDENTICAL. `key` is the seed's little-endian uint32 words
 * (the Python wrapper splits the seed int; a C-only / MCU host passes its own
 * entropy words). Fills `out` with D codes in {0,1,2,3} via MT19937 +
 * getrandbits(3) rejection. Standalone-complete: the 624-word state is
 * stack-resident — no malloc, no compiled-in cap (bound is the caller's `out`).
 * Additive symbol — no ABI bump. */
srmech_status_t srmech_klein4_random(const uint32_t *key,
                                     size_t          key_length,
                                     uint32_t        D,
                                     uint8_t        *out);

/* klein4_match_count(a, b): EXACT integer count of positions where a[i] ==
 * b[i] (the F868 stay-rational recall-ranking key before the float divide;
 * similarity = count / n). Additive symbol — no ABI bump. */
srmech_status_t srmech_klein4_match_count(const uint8_t *a,
                                          const uint8_t *b,
                                          uint32_t       n,
                                          uint32_t      *out);

/* klein4_similarity(a, b): fraction of positions where a[i] == b[i] in
 * [0, 1] (1 identical, 0 orthogonal) — the display-boundary collapse of
 * srmech_klein4_match_count. */
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

/* klein4_bundle_accumulate / _resolve (UPSTREAM §50): the STREAMING form of
 * srmech_klein4_bundle. acc is a caller-owned (1 + 2*dim) uint32 accumulator
 * (acc[0] = n folded; acc[1..dim] / acc[1+dim..2*dim] = per-coordinate bit-0 /
 * bit-1 1-counts). _accumulate folds one Klein-4 vector; _resolve reads the
 * argmax-per-coordinate bundle (bit-identical to srmech_klein4_bundle). The
 * accumulator width is the architecture (caller's RAM) — no compiled-in cap.
 * Adding these symbols does NOT bump SRMECH_ABI_VERSION. */
srmech_status_t srmech_klein4_bundle_accumulate(uint32_t      *acc,
                                                const uint8_t *v,
                                                size_t         dim);

srmech_status_t srmech_klein4_bundle_resolve(const uint32_t *acc,
                                             uint8_t        *out,
                                             size_t          dim);

/* klein4_compose(parts, n, D, acc, scratch, out): the scale-invariant role-
 * filler compositor (UPSTREAM §60 / F900; rc18) —
 * bundle_i( klein4_bind(part_i, klein4_pos_key(D, i)) ) over n pre-composed
 * D-byte Klein-4 `parts` (row-major). pos_key(i) = klein4_random over seed
 * 0x10000 + i (byte-identical to the Python _klein4_pos_key). The native peer of
 * hdc.klein4_compose, the RECURSIVE rung above klein4_encode_bytes; one C call
 * folds the whole bundle (a single part resolves to its position-bound self).
 * `acc` is caller-owned (1 + 2*D) uint32; `scratch` is 2*D caller-owned bytes
 * (pos-key + bound). No compiled-in cap, no malloc. Additive — no ABI bump. */
srmech_status_t srmech_klein4_compose(const uint8_t *parts,
                                      uint32_t       n,
                                      uint32_t       D,
                                      uint32_t      *acc,
                                      uint8_t       *scratch,
                                      uint8_t       *out);

/* klein4_cooccurrence_fold (UPSTREAM §50; rc165): the §50 holographic
 * co-occurrence fold with the corpus-linear inner loop fully in C — the per-token
 * windowed accumulation, no Python callback. `codes` is n_codes fixed-width
 * (dim-byte) Klein-4 atomic codes (each byte in {0..3}); `tok_idx[i]` is the
 * code index (0..n_codes-1) carried by corpus position i. For every position i in
 * [0, n_tokens), each neighbour within ±window (excluding i) folds into the
 * accumulator of the token at i. `out_accs` is n_codes * (1 + 2*dim) uint32,
 * CALLER-allocated; this zeroes it then folds, so each accumulator is the SAME
 * 2-bit tally as srmech_klein4_bundle_accumulate (resolving out_accs[t] is
 * bit-identical to the streamed fold). Width is the architecture (caller's RAM) —
 * no compiled-in cap. Class M; no abs. window >= 1; bad code byte / out-of-range
 * index -> SRMECH_ERR_BAD_INPUT. Additive symbol — no ABI bump. */
srmech_status_t srmech_klein4_cooccurrence_fold(const uint8_t  *codes,
                                                uint32_t        n_codes,
                                                const uint32_t *tok_idx,
                                                uint32_t        n_tokens,
                                                uint32_t        window,
                                                size_t          dim,
                                                uint32_t       *out_accs);

/* ------------------------------------------------------------------ *
 * Class M — Klein-4 EXACT sector ops (v0.9.0rc142; BATCH B1)
 *
 * Six byte-exact ops over the (F2)^2 Klein-4 carrier that compose / extend the
 * srmech_klein4 foundation above. Integer / sector only — no float, no abs.
 * Byte-identical to the pure-Python hdc.klein4_* ops. Additive symbols, so
 * SRMECH_ABI_VERSION stays 3.
 * ------------------------------------------------------------------ */

/* klein4_sector_flip(in, n, mask): XOR every element with a constant sector mask
 * in {0,1,2,3} — the chirality flips (gamma5 = mask 2, iomega7 = mask 1, CPT =
 * mask 3). out[i] = in[i] ^ mask. Out of {0,1,2,3} -> SRMECH_ERR_BAD_INPUT. */
srmech_status_t srmech_klein4_sector_flip(const uint8_t *in,
                                          uint32_t       n,
                                          uint8_t        mask,
                                          uint8_t       *out);

/* klein4_sector_count(in, n): per-sector occupancy [n0,n1,n2,n3] into the
 * caller-owned 4-uint32 out_counts. Out of {0,1,2,3} -> SRMECH_ERR_BAD_INPUT. */
srmech_status_t srmech_klein4_sector_count(const uint8_t *in,
                                           uint32_t       n,
                                           uint32_t      *out_counts);

/* klein4_holographic_encode(in, n, replicas): replica-major replication — out is
 * n*replicas bytes = the input repeated `replicas` times (#797 op (a2); F353).
 * replicas >= 2. Out of {0,1,2,3} -> SRMECH_ERR_BAD_INPUT. */
srmech_status_t srmech_klein4_holographic_encode(const uint8_t *in,
                                                 uint32_t       n,
                                                 uint32_t       replicas,
                                                 uint8_t       *out);

/* klein4_holographic_decode(store, n, replicas, erased): D = n/replicas. erased
 * == NULL -> blind per-position majority (ties -> lowest sector); erased != NULL
 * (length-n mask, nonzero = erased) -> first surviving replica per position
 * (all-erased -> SRMECH_ERR_BAD_INPUT). out is D bytes. n % replicas == 0. */
srmech_status_t srmech_klein4_holographic_decode(const uint8_t *store,
                                                 uint32_t       n,
                                                 uint32_t       replicas,
                                                 const uint8_t *erased,
                                                 uint8_t       *out);

/* klein4_triality_encode(in, n): the order-3 triality orbit [v, T(v), T^2(v)]
 * (orbit-major) — out is 3*n bytes (#797 op (a1); F359). Composes
 * srmech_klein4_triality_cycle. Out of {0,1,2,3} -> SRMECH_ERR_BAD_INPUT. */
srmech_status_t srmech_klein4_triality_encode(const uint8_t *in,
                                              uint32_t       n,
                                              uint8_t       *out);

/* klein4_triality_correct(store, n, scratch): D = n/3; the 2-of-3 triality
 * majority over [b0, T^-1(b1), T(b2)] (ties -> lowest sector), correcting one
 * error (#797 op (a1)). Composes srmech_klein4_triality_cycle; `scratch` is 2*D
 * caller-owned bytes. out is D bytes. n % 3 == 0. */
srmech_status_t srmech_klein4_triality_correct(const uint8_t *store,
                                               uint32_t       n,
                                               uint8_t       *scratch,
                                               uint8_t       *out);

/* ------------------------------------------------------------------ *
 * EXACT signal-processing coder / quantizer ops (v0.9.0rc143; BATCH B6a)
 *
 * Four byte-exact C twins for the five simpler sp_coder_dp ops (the two
 * sign_quantise paths share srmech_sign_quantise). Integer / exact coders —
 * no float tolerance, no libm, no abs (Class-K sign is a pin-slot boundary).
 * Byte-identical to the pure-Python signal_processing kernels. Additive
 * symbols, so SRMECH_ABI_VERSION stays 3. See c/src/srmech_coder.c.
 * ------------------------------------------------------------------ */

/* sign_quantise(in, n, threshold, dead_band): Class-K {-1,0,+1} threshold
 * projection. dead_band <= 0 -> two-level (in >= threshold ? +1 : -1); dead_band
 * > 0 -> three-level (+1 above threshold+dead_band, -1 below threshold-dead_band,
 * 0 in the acceptance band). out is n int8 entries. No abs. */
srmech_status_t srmech_sign_quantise(const double *in,
                                     uint32_t      n,
                                     double        threshold,
                                     double        dead_band,
                                     int8_t       *out);

/* vector_quantise_encode(vectors[n_vec*dim], codebook[n_codes*dim], dim): for
 * each input row, the index of the nearest codebook entry by SQUARED Euclidean
 * distance (accumulated left-to-right -> bit-identical to the pure fold; ties
 * -> lowest index via strict `<`). out_idx receives n_vec indices. No abs. */
srmech_status_t srmech_vector_quantise_encode(const double *vectors,
                                              uint32_t      n_vec,
                                              const double *codebook,
                                              uint32_t      n_codes,
                                              uint32_t      dim,
                                              uint32_t     *out_idx);

/* rle_encode(data, n, max_run): run-length encode to (symbol, count) records;
 * a run stops at a symbol change or at max_run. out_sym / out_count are caller
 * arenas of >= n entries; out_npairs receives the record count. */
srmech_status_t srmech_rle_encode(const uint8_t *data,
                                  uint32_t       n,
                                  uint32_t       max_run,
                                  uint8_t       *out_sym,
                                  uint32_t      *out_count,
                                  uint32_t      *out_npairs);

/* huffman_build_codes(data, n): build the canonical Huffman code table via the
 * SAME deterministic (freq, counter) node ordering as the Python heapq tree.
 * out_code_len[256] = per-symbol code length (0 = absent); out_code_str[256*256]
 * holds each present symbol's '0'/'1' code at [sym*256 ..]; out_order[256] lists
 * present symbols in the Python code-dict order (out_order_count of them). */
srmech_status_t srmech_huffman_build_codes(const uint8_t *data,
                                           uint32_t       n,
                                           uint32_t      *out_code_len,
                                           char          *out_code_str,
                                           uint8_t       *out_order,
                                           uint32_t      *out_order_count);

/* ------------------------------------------------------------------ *
 * sp_coder_dp part 2 — LZ77 / Viterbi / MLSE / arithmetic coder
 * (v0.9.0rc144; BATCH B6b)
 *
 * The four harder sp_coder_dp ops. LZ77 + arithmetic-encode are exact integer /
 * exact-rational (byte-identical); Viterbi + MLSE are float trellis DP made
 * byte-identical by reproducing the EXACT float accumulation order + first-
 * maximal argmax tie-break (deterministic double, no libm). jpeg is DEFERRED
 * (its DCT basis is a float rational.cos cascade -> a numeric batch). Additive
 * symbols, so SRMECH_ABI_VERSION stays 3. See c/src/srmech_coder.c.
 * ------------------------------------------------------------------ */

/* lz77_encode(data, n, window_size, lookahead_size): emit (offset, length,
 * literal) tokens; longest match, ties keep the first ws (largest offset).
 * out_literal[t] == -1 marks the Python `None` literal (match to end-of-input).
 * out_* are caller arenas of >= n entries; *out_ntokens receives the count. */
srmech_status_t srmech_lz77_encode(const uint8_t *data,
                                   uint32_t       n,
                                   uint32_t       window_size,
                                   uint32_t       lookahead_size,
                                   uint32_t      *out_offset,
                                   uint32_t      *out_length,
                                   int32_t       *out_literal,
                                   uint32_t      *out_ntokens);

/* viterbi(obs[T], A[n_states*n_states] row-major, B[n_states*n_obs], pi[
 * n_states]): the log-domain trellis DP; ws_delta / ws_psi are caller scratch
 * of T*n_states each; out_path receives the T-state Viterbi path (first-maximal
 * argmax tie-break). Deterministic double, no libm, no abs. */
srmech_status_t srmech_viterbi(const int32_t *obs,
                               uint32_t       T,
                               const double  *A,
                               const double  *B,
                               const double  *pi,
                               uint32_t       n_states,
                               uint32_t       n_obs,
                               double        *ws_delta,
                               int32_t       *ws_psi,
                               int32_t       *out_path);

/* mlse(obs(re,im)[T], taps(re,im)[L], alpha(re,im)[A]): MLSE over an ISI
 * channel. L = memory+1 (tap count); n_states = A^memory (caller-computed);
 * log_a / log_nstates are the Class-N rational-log constants (computed in
 * Python, passed exact). dscratch carves A_log(n^2) | B_log(n*T) | pi(n) |
 * delta(T*n); iscratch carves psi(T*n) | obs_idx(T); uscratch carves
 * tup(memory) | ntup(memory). out_path receives the T input-symbol indices. */
srmech_status_t srmech_mlse(const double  *obs_re,
                            const double  *obs_im,
                            uint32_t       T,
                            const double  *taps_re,
                            const double  *taps_im,
                            uint32_t       L,
                            const double  *alpha_re,
                            const double  *alpha_im,
                            uint32_t       A,
                            uint32_t       n_states,
                            double         log_a,
                            double         log_nstates,
                            double        *dscratch,
                            int32_t       *iscratch,
                            uint32_t      *uscratch,
                            int32_t       *out_path);

/* arithmetic_encode(clo[k], chi[k], n, total): exact-rational range-coder
 * encode. clo[k] and chi[k] are the k-th symbol's cumulative bounds; total is
 * the frequency sum. Carries a common denominator (total^k) so the whole loop
 * is exact srmech_bigint integer + a single terminal gcd; the lo and hi num/den
 * buffers receive the reduced-fraction decimals (NUL-terminated, each buffer
 * of >= str_cap); ws is the caller uint32 arena. n >= 1. Byte-identical to the
 * Python fractions.Fraction encode. */
srmech_status_t srmech_arithmetic_encode(const uint32_t *clo,
                                         const uint32_t *chi,
                                         uint32_t        n,
                                         uint64_t        total,
                                         char           *lo_num,
                                         char           *lo_den,
                                         char           *hi_num,
                                         char           *hi_den,
                                         size_t          str_cap,
                                         size_t         *lo_num_len,
                                         size_t         *lo_den_len,
                                         size_t         *hi_num_len,
                                         size_t         *hi_den_len,
                                         void           *ws,
                                         size_t          ws_len);

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

/* ------------------------------------------------------------------
 * Cayley-Dickson loop NAVIGATION (v0.9.0rc158; Qalg TAIL Batch 2) — the
 * combinatorial layer over the srmech_cd_basis_product cocycle, INTEGER-only
 * (signed basis units +-e_i; no float, no bignum, no libm, no malloc). A
 * "signed unit" is (sign, index) with sign in {+1,-1}, index in [0, dim); the
 * full Moufang loop has 2*dim of them. These give a C-only host the loop
 * analogues of the cyclic-group orbit machinery: the sub-loop a generator set
 * spans, one left-multiplication cycle, the minimum spanning cardinality, and
 * the sedenion zero-divisor witness. Each COMPOSES srmech_cd_basis_product (it
 * does NOT re-implement the cocycle). Rosetta peers of
 * srmech.amsc.cascade.cayley_dickson.{closure,left_orbit,min_generating_set,
 * sedenion_zero_divisor_witness}, attested BYTE-IDENTICAL by
 * tests/test_qalg_cdnav_c_rc158.py.
 *
 * ABI-additive: new symbols + two macros, so SRMECH_ABI_VERSION stays 3.
 * ------------------------------------------------------------------ */

/* min_generating_set search bounds (JPL Rule 2 explicit caps). A unit set
 * larger than MAX_UNITS, or a combinatorial search exceeding MAX_SUBSETS,
 * returns SRMECH_ERR_OVERFLOW so the caller falls to the complete pure oracle
 * (never a wrong answer). The realistic domain (<= sedenion, 15 units) is far
 * under both. */
#define SRMECH_CD_MGS_MAX_UNITS   20
#define SRMECH_CD_MGS_MAX_SUBSETS 1000000L

/* The sub-loop generated by {e_g : g in gen_idxs}: the fixpoint over signed
 * basis units seeded with the identity (+1, e0) and each generator (+1, e_g),
 * closed under all pairwise products. out_signs[m]/out_indices[m] receive the
 * m-th spanned signed unit; *out_count its cardinality (<= 2*dim). out_cap is
 * the length of the caller arrays (>= 2*dim to hold the full loop). dim a power
 * of two in [1, SRMECH_CD_MAX_DIM]; each gen index in [0, dim). Errors:
 * SRMECH_ERR_NULL_ARG; SRMECH_ERR_BAD_INPUT (bad dim / gen index);
 * SRMECH_ERR_OVERFLOW (out_cap too small). */
srmech_status_t srmech_cd_closure(int dim, const int *gen_idxs, size_t n_gens,
                                  int *out_signs, int *out_indices,
                                  size_t out_cap, size_t *out_count);

/* The left-multiplication orbit of e_{start_idx} under repeated left-multiply
 * by e_{gen_idx}: [e_s, e_g*e_s, e_g*(e_g*e_s), ...] in cycle order, closing
 * repeat excluded. out_signs[m]/out_indices[m] receive the m-th signed unit;
 * *out_count the cycle length (<= 2*dim). out_cap the caller-array length.
 * Same dim / index domain + errors as srmech_cd_closure. */
srmech_status_t srmech_cd_left_orbit(int dim, int start_idx, int gen_idx,
                                     int *out_signs, int *out_indices,
                                     size_t out_cap, size_t *out_count);

/* The smallest k such that some k-subset of {e_u : u in unit_idxs} has a
 * srmech_cd_closure equal to the FULL loop (2*dim signed units). *out_k = k on
 * success, or 0 when NO subset spans (the caller raises the ValueError). Units
 * are de-duplicated preserving order; each in [0, dim). Composes
 * srmech_cd_closure over each combination. Errors: SRMECH_ERR_NULL_ARG;
 * SRMECH_ERR_BAD_INPUT (bad dim / unit index); SRMECH_ERR_OVERFLOW (unit count
 * or subset search past the caps -> caller uses the pure oracle). */
srmech_status_t srmech_cd_min_generating_set(int dim, const int *unit_idxs,
                                             size_t n_units, int *out_k);

/* The first sedenion (dim 16) basis-pair zero divisor: (e_i + e_j)(e_k + s*e_l)
 * = 0 with both factors nonzero, found by searching basis-unit pairs in the
 * SAME nested order (i<j, k<l, s in {+1,-1}) as the Python oracle so the witness
 * is identical. *out_i/j/k/l receive the imaginary-unit indices (1..15);
 * *out_s the second-factor sign (+1/-1). Errors: SRMECH_ERR_NULL_ARG. (The
 * sedenions always have such a witness; a not-found return would be a broken
 * convention -> SRMECH_ERR_BAD_INPUT.) */
srmech_status_t srmech_cd_zero_divisor_witness(int *out_i, int *out_j,
                                               int *out_k, int *out_l,
                                               int *out_s);

/* ------------------------------------------------------------------
 * Qi — the EXACT-complex (Gaussian-rational) carrier C-host peer (0.9.0rc15;
 * Python srmech.amsc.qi.Qi). A Qi value is FOUR int64 limbs
 * {re_num, re_den, im_num, im_den} (denominators positive, fit int64). Lets a
 * C-only host do exact `re + im·i` arithmetic over ℚ in one call per op, the
 * named A–N cascade composed from the Class-N srmech_rational_* ops:
 *   add/sub/mul  : Class M bilinear bind ∘ Class C cross-term order
 *                  (mul = (ac−bd) + (ad+bc)i)
 *   conjugate    : Class K — the im sign-flip (never abs())
 *   quadrant     : Class C orientation → Klein-4 sector (bit0=re<0, bit1=im<0)
 *   norm_sq      : Class N anchor — re²+im² (exact ℚ; out[2] = {num, den})
 *
 * NO BIGNUM (fixed-limb mandate): any intermediate escaping the int64/uint64
 * limb domain returns SRMECH_ERR_OVERFLOW; the Python Qi falls through to its
 * exact-Fraction path (the unbounded oracle), as the rc13 isqrt does past
 * 2^128. Carrier-internal like the Mat/Vec dense kernels: NOT a Rosetta op.
 * ABI-additive — SRMECH_ABI_VERSION stays 3. See srmech_qi.c.
 * Errors: SRMECH_ERR_NULL_ARG; SRMECH_ERR_BAD_INPUT (denominator ≤ 0);
 * SRMECH_ERR_OVERFLOW (int64 limb domain exceeded). out arrays are caller-owned
 * (out[4] for add/sub/mul/conjugate; out[2] for norm_sq). ------------------ */
srmech_status_t srmech_qi_add(const int64_t a[4], const int64_t b[4],
                              int64_t out[4]);
srmech_status_t srmech_qi_sub(const int64_t a[4], const int64_t b[4],
                              int64_t out[4]);
srmech_status_t srmech_qi_mul(const int64_t a[4], const int64_t b[4],
                              int64_t out[4]);
srmech_status_t srmech_qi_conjugate(const int64_t a[4], int64_t out[4]);
srmech_status_t srmech_qi_quadrant(const int64_t a[4], int *out_quadrant);
srmech_status_t srmech_qi_norm_sq(const int64_t a[4], int64_t out[2]);

/* ------------------------------------------------------------------
 * Sedenion-addressable hyper-loop ADDRESS LAYER (UPSTREAM §31 / F465 +
 * F468; Python srmech.amsc.cascade.sedenion_register). The navigation +
 * reversibility-gate ops a C-only host needs to run "Siona's address
 * layer." The carry/correct EC half is the §30 srmech_hamming_* family.
 * Rosetta peer of SedenionRegister.{navmap,navigate,is_navigable},
 * attested by tests/test_cascade_sedenion_parity.py.
 *
 * NO BIGNUM: is_navigable decides invertibility of the signed
 * XOR-circulant L(x)[r][c] = sign(r^c,c) * x_{r^c} by MODULAR rank over
 * word-size primes (every product < 2^62, no multi-precision limb), made
 * certain for the singular verdict by exceeding the Hadamard determinant
 * bound. See srmech_sedenion.c.
 *
 * ABI-additive: new symbols + a macro, so SRMECH_ABI_VERSION stays 3.
 * ------------------------------------------------------------------ */

/* The sedenion address space is 16 named slots e0..e15. */
#define SRMECH_SEDENION_NUM_SLOTS 16

/* The signed pointer-advance permutation for right-multiply-by-e_j: for each
 * slot i in [0,16), out_dest[i] = k and out_sign[i] = s where e_i * e_j =
 * s * e_k. out_dest / out_sign are caller arrays of length 16. j in [0,16).
 * Errors: SRMECH_ERR_NULL_ARG; SRMECH_ERR_BAD_INPUT (j out of range). */
srmech_status_t srmech_sedenion_navmap(int j, int *out_dest, int *out_sign);

/* Route `count` occupied (slot, sign) records through the ×e_j permutation,
 * composing the Class-C signs: out_slots[m] = k, out_signs[m] = in_signs[m]*s
 * where e_{in_slots[m]} * e_j = s * e_k. in_signs entries must be +1/-1 and
 * in_slots in [0,16). count == 0 is a no-op. Errors: SRMECH_ERR_NULL_ARG;
 * SRMECH_ERR_BAD_INPUT (j / slot out of range, or sign not +-1). */
srmech_status_t srmech_sedenion_navigate(int j, const int *in_slots,
                                         const int *in_signs, size_t count,
                                         int *out_slots, int *out_signs);

/* Reversibility gate: is left-multiplication by `direction` (an integer
 * vector of power-of-two length n in [1, SRMECH_CD_MAX_DIM]) a bijection?
 * Sets *out_invertible to 1 (invertible / navigable) or 0 (a left zero
 * divisor). Exact (modular rank; bit-identical bool to the Python
 * Fraction-nullspace oracle). Errors: SRMECH_ERR_NULL_ARG; SRMECH_ERR_BAD_INPUT
 * (n not a power of two in range, magnitude overflow, or coefficients beyond
 * the certainty prime table). */
srmech_status_t srmech_sedenion_is_navigable(const int64_t *direction,
                                             size_t n, int *out_invertible);

/* ------------------------------------------------------------------
 * JSON value-tree — parser + canonical writer (§41 genome-persistence
 * C mirror; the wider AMSC provenance C surface).
 *
 * A malloc-free JSON module: the parser builds a value tree from a
 * caller-supplied arena/workspace (bump allocator — the same
 * `void *ws, size_t ws_len` convention the TOML parser uses), and the
 * writer emits bytes BYTE-IDENTICAL to CPython's
 *   json.dumps(obj, sort_keys=True, ensure_ascii=False)
 * for any tree of null / bool / int / string / object / array — which
 * is exactly what an MPR manifest / a genome catalog is (they are
 * float-free). See the byte-parity rules at srmech_json_write below.
 *
 * Strings (and object keys) in the value tree are stored DECODED (the
 * raw UTF-8 bytes, escapes already resolved) and are NOT NUL-
 * terminated — each carries an explicit length. The writer re-escapes
 * them on output.
 *
 * No recursion: both the parser and the writer use an explicit depth-
 * bounded stack (<= SRMECH_JSON_MAX_DEPTH), so JPL Rule 1 (no direct
 * or indirect recursion) holds.
 *
 * ABI-additive: new symbols + a struct + macros, so SRMECH_ABI_VERSION
 * stays 3.
 * ------------------------------------------------------------------ */

/* Recursion-depth guard for the explicit parse/emit stacks (single-token
 * object-like macro; JPL Rule 8 clean). There is NO object/array child
 * cap: parse grows children arena-backed, and the writer's key-sort
 * scratch is carved from a caller arena (srmech_json_write_ws), so a
 * container is bounded only by the caller's RAM. */
#define SRMECH_JSON_MAX_DEPTH    64

typedef enum {
    SRMECH_JSON_NULL = 0,
    SRMECH_JSON_BOOL,
    SRMECH_JSON_INT,      /* int64 */
    SRMECH_JSON_DOUBLE,
    SRMECH_JSON_STRING,
    SRMECH_JSON_ARRAY,
    SRMECH_JSON_OBJECT
} srmech_json_type_t;

typedef struct srmech_json_value srmech_json_value_t;
struct srmech_json_value {
    srmech_json_type_t type;
    union {
        struct { const char *ptr; uint32_t len; } str;   /* UTF-8, decoded (NOT escaped); keys + string values */
        int64_t i;
        double  f;
        int     b;                                       /* 0/1 */
        struct { srmech_json_value_t **items; uint32_t n; } arr;
        struct { const char **keys; srmech_json_value_t **vals; uint32_t n; } obj;
    } u;
};

/* Parse `len` JSON bytes at `src` into a value tree allocated from the
 * caller-supplied workspace `ws` (length `ws_len` bytes). On success
 * *out points at the root node (inside the workspace) and SRMECH_OK is
 * returned. Trailing non-whitespace after the top-level value is an
 * error. Arena exhaustion → SRMECH_ERR_OVERFLOW; malformed input →
 * SRMECH_ERR_BAD_INPUT; a NULL required pointer → SRMECH_ERR_NULL_ARG.
 *
 * String decoding handles \" \\ \/ \b \f \n \r \t and \uXXXX
 * (including UTF-16 surrogate pairs → UTF-8 bytes). Numbers with a
 * '.', 'e', or 'E' parse to SRMECH_JSON_DOUBLE; otherwise to
 * SRMECH_JSON_INT (int64). */
srmech_status_t srmech_json_parse(const char *src, size_t len,
                                  void *ws, size_t ws_len,
                                  srmech_json_value_t **out);

/* Bytes of caller workspace srmech_json_write_ws needs to serialise `v`:
 * the emit-frame stack plus the key-order sort scratch, sized to the
 * ACTUAL tree (deepest nesting × widest object) — no compiled-in
 * object-width cap. Pure tree walk, no I/O. */
size_t srmech_json_write_arena_bytes(const srmech_json_value_t *v);

/* Write `v` as canonical JSON into `buf` (capacity `buf_len` bytes,
 * NO trailing NUL written) and set *out_len to the byte count, using the
 * caller-supplied scratch `ws` (length `ws_len`; size it with
 * srmech_json_write_arena_bytes). The key-sort permutation arrays live in
 * `ws`, so an object is bounded only by the arena, not a compiled-in cap.
 * A `ws` too small for the tree returns SRMECH_ERR_BAD_INPUT.
 *
 * If `buf` is NULL this is a SIZE-QUERY: nothing is written and *out_len
 * receives the exact length a full write would produce (callers can
 * two-pass: query, allocate, fill). When writing, a too-small buffer
 * returns SRMECH_ERR_OVERFLOW (never overflows). *out_len is always
 * set on SRMECH_OK.
 *
 * The output is byte-identical to CPython
 * json.dumps(obj, sort_keys=True, ensure_ascii=False) for null / bool
 * / int / string / object / array trees. DOUBLE values are best-effort
 * (%.17g shortest-ish) and are NOT guaranteed byte-identical to
 * Python's repr(float) — float parity is explicitly out of scope (MPR
 * / genome manifests are float-free). */
srmech_status_t srmech_json_write_ws(const srmech_json_value_t *v,
                                     char *buf, size_t buf_len,
                                     size_t *out_len,
                                     void *ws, size_t ws_len);

/* Look up `key` (NUL-terminated) in an OBJECT value; returns the value
 * node or NULL if `obj` is not an object or the key is absent. */
const srmech_json_value_t *srmech_json_object_get(
    const srmech_json_value_t *obj, const char *key);

/* ------------------------------------------------------------------
 * JSON builder — construct a value tree in the SAME arena, for the
 * §41 genome-manifest C mirror (nested objects / arrays / strings /
 * int64s). Init a builder over a workspace, then allocate nodes from
 * it; the resulting root can be handed straight to srmech_json_write.
 *
 * Strings passed to srmech_json_new_string are NOT copied — the caller
 * must keep the bytes alive for the lifetime of the tree (the manifest
 * builder holds its key/value byte buffers across the build → write).
 * The keys/vals/items arrays passed to new_object / new_array ARE
 * copied into the arena, so the caller's temporary arrays may be
 * reused after the call.
 * ------------------------------------------------------------------ */
typedef struct {
    unsigned char *base;   /* workspace base                         */
    size_t         len;    /* workspace capacity (bytes)             */
    size_t         used;   /* bump offset                            */
    int            failed; /* 1 once any allocation overflowed       */
} srmech_json_builder_t;

/* Initialise a builder over `ws` (length `ws_len`). */
srmech_status_t srmech_json_builder_init(srmech_json_builder_t *b,
                                         void *ws, size_t ws_len);

/* Node constructors. Each returns a node allocated from the builder's
 * arena, or NULL on arena exhaustion / NULL builder (the builder's
 * `failed` flag latches so a caller can check once at the end). */
srmech_json_value_t *srmech_json_new_null(srmech_json_builder_t *b);
srmech_json_value_t *srmech_json_new_bool(srmech_json_builder_t *b, int truth);
srmech_json_value_t *srmech_json_new_int(srmech_json_builder_t *b, int64_t i);
srmech_json_value_t *srmech_json_new_double(srmech_json_builder_t *b, double f);
srmech_json_value_t *srmech_json_new_string(srmech_json_builder_t *b,
                                            const char *ptr, uint32_t len);
srmech_json_value_t *srmech_json_new_array(srmech_json_builder_t *b,
                                           srmech_json_value_t **items,
                                           uint32_t n);
srmech_json_value_t *srmech_json_new_object(srmech_json_builder_t *b,
                                            const char **keys,
                                            srmech_json_value_t **vals,
                                            uint32_t n);

/* ------------------------------------------------------------------
 * Op-provenance canonical record hasher (0.9.0rc117; the op-carrying
 * carrier, dives #718/#719) — the C peer of
 * srmech.amsc.op_provenance.op_provenance_hash.
 *
 * digest = sha256( canonical_json( record MINUS "chain_sha256" ) )
 *
 * A Class-A composite over the JSON module above + srmech_sha256_hex:
 * parse `record_len` JSON bytes at `record_json` (ANY formatting / key
 * order), drop the top-level "chain_sha256" member (the record's cached
 * self-hash — the pre-image never contains it), re-emit CANONICALLY
 * (byte-identical to CPython json.dumps(obj, sort_keys=True,
 * ensure_ascii=False)), and write the 64-hex SHA-256 (+ NUL) of those
 * canonical bytes into `out_hex` (>= 65 bytes).
 *
 * FLOAT-FREE BY CONSTRUCTION: the op-provenance canonical image carries
 * floats only as {"__float64__": "<float.hex>"} string tags. A raw JSON
 * float (any number token containing '.', 'e', or 'E') is REJECTED with
 * SRMECH_ERR_BAD_INPUT — C's %.17g double rendering is not byte-identical
 * to Python repr(float), and a silent fork of the hash is exactly what
 * this op exists to prevent. (The Python wrapper enforces the same
 * rejection; the mirror agrees on the domain, not just the values.)
 *
 * `ws` is the caller arena for ALL scratch (parse tree + writer key-sort
 * scratch + the canonical byte buffer) — bound by the caller's RAM, no
 * compiled-in cap; size it with srmech_op_provenance_hash_arena_bytes.
 * ABI-additive: new symbols only, SRMECH_ABI_VERSION stays 3.
 *
 * Error returns:
 *   SRMECH_ERR_NULL_ARG  — record_json / ws / out_hex is NULL.
 *   SRMECH_ERR_BAD_INPUT — empty / malformed JSON, a raw float token,
 *                          or a ws too small to seat the writer scratch.
 *   SRMECH_ERR_OVERFLOW  — the arena cannot hold this record's tree /
 *                          canonical bytes (size ws up and retry).
 * ------------------------------------------------------------------ */
srmech_status_t srmech_op_provenance_hash(const char *record_json,
                                          size_t record_len,
                                          void *ws, size_t ws_len,
                                          char *out_hex);

/* The arena byte count srmech_op_provenance_hash needs for a record of
 * `record_len` JSON bytes — a static over-approximation of the parse
 * tree + writer scratch + canonical output (each term traces to a real
 * allocation; see srmech_op_provenance.c). Pure arithmetic (no I/O).
 * Adding this symbol does NOT bump SRMECH_ABI_VERSION. */
size_t srmech_op_provenance_hash_arena_bytes(size_t record_len);

/* ------------------------------------------------------------------
 * §41 genome persistence — the C mirror of srmech.amsc.genome's
 * disk save / load / catalog / append / window. A genome directory is
 *
 *   <dir>/manifest.json   an MPRRecord (MPR v1) catalogue of the
 *                         chromosome set (leaf_dim, per-chromosome
 *                         cap_sha256 / leaf_count / byte_offset /
 *                         byte_len, body_sha256, the_one hash+hex).
 *   <dir>/turns.bin       the append-only flat body: every strand
 *                         element (a telomere cap or a coupled turn)
 *                         is one SELF-DESCRIBING block whose FIRST byte
 *                         keys its kind + width — a leaf_dim-byte cap,
 *                         a §55/v3 BIT-PACKED data turn (1 +
 *                         ceil(leaf_dim/4) bytes, 4 Klein-4 symbols per
 *                         byte), or a legacy v2 leaf_dim-byte turn. No
 *                         length prefixes — chromosome boundaries live
 *                         in the manifest as byte_offset / byte_len.
 *
 * The manifest is built with the JSON builder above and serialised with
 * srmech_json_write, so it is BYTE-IDENTICAL to the Python genome_save's
 * json.dumps(payload, sort_keys=True, ensure_ascii=False). turns.bin is
 * the body bytes verbatim (no transformation). All hashing routes through
 * srmech_sha256_hex (Class A); bounding == integrity (every read re-hashes
 * the bytes it touched and compares the hex against the manifest — no abs,
 * no float). The on-disk format version is SRMECH_GENOME_FORMAT_VERSION.
 *
 * File I/O is stdio (fopen / fread / fwrite / fseek); JPL Rule 3 bans
 * malloc, not file I/O. The caller arena `ws` backs ALL scratch (the body
 * read, the manifest, the per-chromosome arrays, the .chr buffers, the JSON
 * tree) via a bump pointer — the bound is the caller's RAM, never a
 * compiled-in cap; directory-path strings are built into bounded stack
 * buffers.
 *
 * ABI-additive: new symbols + a struct + macros, so SRMECH_ABI_VERSION
 * stays 3.
 * ------------------------------------------------------------------ */

/* §41/§44 on-disk format version. 1 == content-address telomere caps +
 * manifest-described boundaries; 2 (§44) == SELF-DESCRIBING fixed-width
 * strand: chromosome + gene boundaries are INLINE packed caps scanned-for in
 * the body (the strand is the SSoT; the manifest is a derived cache, every
 * field rebuildable by scanning the body); 3 (§55/rc114, issue #1245) ==
 * BIT-PACKED data turns: a data turn is [SRMECH_GENOME_PACKED_TURN_MARKER] +
 * ceil(leaf_dim/4) payload bytes (4 Klein-4 symbols per byte — the measured
 * 4.03x byte-per-symbol bloat removed), while cap blocks keep their v2
 * leaf_dim-byte inline layout. A block's FIRST byte keys its kind AND its
 * width, so v2 / v3 / MIXED bodies read in the SAME walk (back-compat is
 * structural, not a converter). n_turns counts strand BLOCKS.
 *
 * v4 (rc115, #1245 ask (b)): the manifest carries a `regions` array — one
 * {byte_offset, byte_len, sha256} entry per chromosome (the full-region digest,
 * == the chromosome's .chr / AMSC provenance unit) — and body_sha256 becomes the
 * REGION CHAIN Hn = sha256(Hn-1 || region_n_sha256) seeded by H0 = sha256("").
 * The chain is O(1)-maintainable on append (extend the head) yet re-verifiable
 * from the file (re-hash each region, re-fold) and body-derivable by a §44 scan
 * (so a rebuild reproduces it byte-identically). v2/v3 manifests (no `regions`,
 * whole-body body_sha256) stay READ-compatible. Mirrors GENOME_FORMAT_VERSION. */
/* v5 (§60/rc121, issue #1245 REOPENED): a kernel chromosome may carry a
 * SRMECH_GENOME_KERNEL_HEADER_MARKER (0x4B) block SELF-RECORDING an
 * arbitrary-dimension Klein-4 kernel's TRUE length + element_type + leaf_dim, so
 * kernel_unpack reconstructs it EXACTLY with no caller length. The header is one
 * more self-describing block kind in the SAME walk (first byte keys it), so v2 /
 * v3 / v4 bodies — and any v5 body with NO header — read UNCHANGED (a header-less
 * body defaults to element_type=klein4, D = leaf_count * leaf_dim): back-compat
 * is STRUCTURAL, not a converter. */
/* v6 (§89/rc126, issue #1261): the UNIFORMLY-KLEIN-4 kernel header. A kernel
 * chromosome now opens with a SRMECH_GENOME_KERNEL_TELOMERE_MARKER (0x6B) cap and
 * carries its header as a 100%-Klein-4 coupled LEAF (base-4-encoded D +
 * element_type + leaf_dim) — the 0x4B byte-TLV residue is GONE, so the store is
 * uniformly Klein-4 and the O(1) genome_append_kernel rides the plain coupled-turn
 * append. The 0x6B cap is one more self-describing kind in the SAME walk (first byte
 * keys it), so v2 / v3 / v4 bodies — AND any v5 0x4B byte-TLV header — read
 * UNCHANGED (dual-read): back-compat is STRUCTURAL, never a converter. Mirrors
 * GENOME_FORMAT_VERSION in srmech.amsc.genome. */
/* v7 (§127/rc127, #726): the ACTIVE TELOMERE. A chromosome MAY open with a
 * SRMECH_GENOME_ACTIVE_TELOMERE_MARKER (0x74) cap carrying an exact non-negative
 * Hayflick COUNT inline (a descending replicative counter that srmech_genome_telomere_tick
 * reads to gate a divide — the op-carries-operand cap making the chromosome a genuine
 * op(x)operand). The 0x74 cap is one more self-describing kind in the SAME walk (first
 * byte keys it, label read UNIFORMLY up to the first NUL, count in the 8 bytes after
 * that NUL), so v2..v6 bodies read UNCHANGED (dual-read): back-compat is STRUCTURAL,
 * never a converter. A plain-telomere (no 0x74) genome saved by the v7 writer is
 * byte-identical to v6 EXCEPT the format_version field. Mirrors GENOME_FORMAT_VERSION
 * in srmech.amsc.genome. */
/* v8 (§128/rc128, #728): the REGULATORY GENE. An intra-chromosome gene MAY be opened by a
 * SRMECH_GENOME_REGULATORY_GENE_MARKER (0x67) cap carrying an exact regulatory MASK inline
 * (the gene's "regulatory region / promoter" that srmech_genome_gene_express reads to gate
 * which genes express under an applied cell_state — the op-carries-operand theorem one scale
 * up from the v7 active telomere: the cell-state operand modulates the expression operator
 * over MANY genes, #728). Unlike the v6/v7 chromosome-boundary caps, the 0x67 cap is an
 * INTRA-chromosome gene delimiter (a gene-analog of the plain GENE cap 0x47); it is one more
 * self-describing kind in the SAME walk (first byte keys it, label read UNIFORMLY, mask in
 * the 8 bytes after the label NUL), so v2..v7 bodies read UNCHANGED (dual-read): back-compat
 * is STRUCTURAL, never a converter. A plain-gene (no 0x67) genome saved by the v8 writer is
 * byte-identical to v7 EXCEPT the format_version field, and every plain gene ALWAYS EXPRESSES
 * (an unregulated gene == a regulatory gene with mask 0). §130/v9 (#730): the BOOLEAN GENE
 * (marker 0x62) carrying arbitrary boolean logic (a DNF) is a NEW block KIND, so it bumps v8 ->
 * v9 (the walker gains ONE branch; v2..v8 bodies read UNCHANGED; a plain/klein4-mask genome
 * saved by the v9 writer is byte-identical to v8 EXCEPT the format_version field). §131/v10
 * (#731): the THRESHOLD GENE (marker 0x77) carrying a linear-threshold / perceptron gate (a
 * SIGNED integer weight vector + a threshold) is a NEW block KIND, so it bumps v9 -> v10 (the
 * walker gains ONE branch; v2..v9 bodies read UNCHANGED; a plain/klein4-mask/boolean genome saved
 * by the v10 writer is byte-identical to v9 EXCEPT the format_version field). §132/v11 (#732):
 * the GRADED (dose-response) GENE (marker 0x64) carrying an ANALOG expression LEVEL (a SIGNED
 * integer level-weight vector + a POSITIVE denominator) is a NEW block KIND, so it bumps v10 ->
 * v11 (the walker gains ONE branch; v2..v10 bodies read UNCHANGED; a plain/klein4-mask/boolean/
 * threshold genome saved by the v11 writer is byte-identical to v10 EXCEPT the format_version
 * field). Mirrors GENOME_FORMAT_VERSION in srmech.amsc.genome. */
#define SRMECH_GENOME_FORMAT_VERSION 11

/* §44 inline cap markers — the FIRST byte of a fixed-width cap leaf. Both are
 * > 3 so a cap is told apart from a Klein-4 data turn (bytes 0..3) by its
 * first byte alone; the label follows, NUL-padded to leaf_dim. Mirror
 * CHROM_CAP_MARKER / GENE_CAP_MARKER in srmech.amsc.genome. */
#define SRMECH_GENOME_CHROM_CAP_MARKER 0x43u   /* 'C' — opens a chromosome */
#define SRMECH_GENOME_GENE_CAP_MARKER  0x47u   /* 'G' — opens a gene */

/* §55/v3 bit-packed data-turn marker — the FIRST byte of a packed turn block
 * ([marker] + ceil(leaf_dim/4) payload bytes; symbol i lives in payload byte
 * i/4 at bit shift 6 - 2*(i%4), first symbol in the HIGH lanes; a partial
 * final byte's unused low lanes are zero). > 3 and distinct from both cap
 * markers, so the strand stays self-describing. Mirrors PACKED_TURN_MARKER
 * in srmech.amsc.genome. */
#define SRMECH_GENOME_PACKED_TURN_MARKER 0x51u /* 'Q' — a quad-packed turn */

/* §60/v5 SIZE-AGNOSTIC KERNEL HEADER marker — the FIRST byte of a fixed-width
 * leaf_dim-byte inline block written by kernel_pack right after a kernel
 * chromosome's telomere. It self-records the kernel's TRUE length D (bytes [1:9],
 * uint64 big-endian), leaf_dim (bytes [9:13], uint32 big-endian) and element_type
 * (byte [13], uint8 enum; 0 = klein4). > 3 and distinct from every other marker,
 * so the strand stays self-describing; stored VERBATIM (never bit-packed) and NOT
 * counted as a data turn. Mirrors KERNEL_HEADER_MARKER in srmech.amsc.genome.
 * §89/v6: READ-ONLY back-compat — kernel_pack no longer WRITES it. */
#define SRMECH_GENOME_KERNEL_HEADER_MARKER 0x4Bu /* 'K' — a v5 kernel header */

/* §89/v6 KERNEL TELOMERE marker (rc126, issue #1261) — the FIRST byte of a
 * fixed-width leaf_dim-byte cap leaf that opens a KERNEL chromosome (like the CHROM
 * cap, but flags the chromosome as a kernel: the coupled turn IMMEDIATELY after it
 * is the uniformly-Klein-4 §89 header LEAF — base-4 D + element_type + leaf_dim). A
 * reader recovers the true D by scanning for 0x6B and reading the next turn (the
 * collision-FREE distinguisher — a framing marker, not in-band magic). > 3 and
 * distinct from every other marker (CHROM 0x43 / GENE 0x47 / v5 KERNEL 0x4B / PACKED
 * 0x51), so the strand stays self-describing and v2..v5 bodies read UNCHANGED — the
 * walker gains ONE branch. Mirrors KERNEL_TELOMERE_MARKER in srmech.amsc.genome. */
#define SRMECH_GENOME_KERNEL_TELOMERE_MARKER 0x6Bu /* 'k' — a §89 kernel telomere */

/* §127/v7 ACTIVE TELOMERE marker (rc127, #726) — the FIRST byte of a fixed-width
 * leaf_dim-byte cap leaf that opens a chromosome (like the CHROM cap) AND carries an
 * exact non-negative COUNT inline. Layout: [0x74] + utf-8 label + NUL + count (uint64
 * big-endian) + NUL-pad to leaf_dim. The label decode is UNIFORM (bytes [1:] up to the
 * first NUL — the same as every cap); the count is read at the 8 bytes RIGHT AFTER that
 * NUL. > 3 and distinct from every other marker (CHROM 0x43 / GENE 0x47 / v5 KERNEL 0x4B
 * / PACKED 0x51 / KERNEL-telomere 0x6B), so v2..v6 bodies read UNCHANGED — the walker
 * gains ONE branch. Mirrors ACTIVE_TELOMERE_MARKER in srmech.amsc.genome. */
#define SRMECH_GENOME_ACTIVE_TELOMERE_MARKER 0x74u /* 't' — a §127 active telomere */

/* §127/v7 active-telomere COUNT field width — a uint64 (8 bytes, big-endian), read at
 * the byte right after the inline label's NUL terminator. Mirrors
 * _ACTIVE_TELOMERE_COUNT_BYTES in srmech.amsc.genome. */
#define SRMECH_GENOME_ACTIVE_TELOMERE_COUNT_BYTES 8u

/* §128/v8 REGULATORY GENE marker (rc128, #728) — the FIRST byte of a fixed-width
 * leaf_dim-byte cap leaf that opens an INTRA-chromosome gene (like the plain GENE cap) AND
 * carries an exact non-negative regulatory MASK inline. Layout: [0x67] + utf-8 label + NUL +
 * mask (uint64 big-endian) + NUL-pad to leaf_dim (the SAME field shape as the §127 active
 * telomere, mask replacing count). The label decode is UNIFORM (bytes [1:] up to the first
 * NUL — the same as every cap); the mask is read at the 8 bytes RIGHT AFTER that NUL. > 3 and
 * distinct from every other marker (CHROM 0x43 / GENE 0x47 / v5 KERNEL 0x4B / PACKED 0x51 /
 * KERNEL-telomere 0x6B / ACTIVE-telomere 0x74), so v2..v7 bodies read UNCHANGED — the walker
 * gains ONE branch. srmech_genome_gene_express reads the mask to gate expression under a
 * cell_state. Mirrors REGULATORY_GENE_MARKER in srmech.amsc.genome. */
#define SRMECH_GENOME_REGULATORY_GENE_MARKER 0x67u /* 'g' — a §128 regulatory gene */

/* §128/v8 regulatory-gene MASK field width — a uint64 (8 bytes, big-endian), read at the byte
 * right after the inline label's NUL terminator (the SAME field shape as the §127 active
 * telomere's count). §129 (#729): a regulatory gene carries TWO consecutive such fields — the
 * KLEIN-4 bit-planes (activator then repressor); rc128's single-mask cap is dual-read as
 * activator=mask, repressor=0 (the repressor plane occupies what was NUL padding). Mirrors
 * _REGULATORY_GENE_MASK_BYTES in srmech.amsc.genome. */
#define SRMECH_GENOME_REGULATORY_MASK_BYTES 8u

/* §130/v9 BOOLEAN GENE marker (rc130, #730) — the FIRST byte of a fixed-width leaf_dim-byte cap
 * leaf that opens an INTRA-chromosome gene (like the plain GENE cap / the §128 regulatory gene)
 * AND carries ARBITRARY boolean regulatory logic inline as a DNF (disjunctive normal form). The
 * GENERAL gate-type in the rc129 dispatch family: the §128/§129 klein4-mask gene (0x67) stays
 * the fast common case; this 0x62 gene is the general escape hatch (E1 subset E2 — the
 * klein4-mask (activator, repressor) two-mask IS a 1-term DNF). Layout: [0x62] + utf-8 label +
 * NUL + gate_type(uint8) + n_terms(uint16 big-endian) + n_terms x (activator(uint64 BE) +
 * repressor(uint64 BE)) + NUL-pad to leaf_dim. The label decode is UNIFORM (bytes [1:] up to the
 * first NUL — the same as every cap); the gate_type + DNF are read at the bytes RIGHT AFTER that
 * NUL. > 3 and distinct from every other marker (CHROM 0x43 / GENE 0x47 / v5 KERNEL 0x4B /
 * PACKED 0x51 / KERNEL-telomere 0x6B / ACTIVE-telomere 0x74 / REGULATORY-gene 0x67), so v2..v8
 * bodies read UNCHANGED — the walker gains ONE branch. A NEW marker byte = a new block KIND, so
 * it bumps the genome format v8 -> v9 (like the 0x74 v6->v7 and 0x67 v7->v8 bumps; the read path
 * is version-independent, so every pre-rc130 genome still reads identically).
 * srmech_genome_gene_express evaluates the DNF (express iff ANY term matches) to gate expression
 * under a cell_state. Mirrors BOOLEAN_GENE_MARKER in srmech.amsc.genome. */
#define SRMECH_GENOME_BOOLEAN_GENE_MARKER 0x62u /* 'b' — a §130 boolean gene */

/* §130/v9 REGULATORY GATE-TYPE enum (rc130, #730). A regulatory gene declares a gate_type;
 * srmech_genome_gene_express dispatches on it. KLEIN4_MASK (0) = the §129 activator/repressor
 * two-mask (the fast common case, carried by a 0x47/0x67 cap); BOOLEAN_DNF (1) = the §130 DNF
 * (the general case, carried by a 0x62 cap). The gate_type is IMPLIED by the cap marker AND —
 * for a 0x62 gene — stored EXPLICITLY as a uint8 in the cap so the bare strand self-describes it
 * and the family stays extensible. Mirrors GATE_TYPE_* in srmech.amsc.genome. */
#define SRMECH_GENOME_GATE_TYPE_KLEIN4_MASK 0u
#define SRMECH_GENOME_GATE_TYPE_BOOLEAN_DNF 1u

/* §130/v9 BOOLEAN GENE DNF wire widths (rc130, #730). The DNF term COUNT is a uint16 big-endian
 * (2 bytes). Each DNF TERM is TWO consecutive uint64 big-endian masks — the (activator,
 * repressor) AND-clause (16 bytes), the SAME (require-present, require-absent) pair the §129
 * klein4-mask carries as its ONE clause. Mirror _BOOLEAN_GENE_* in srmech.amsc.genome. */
#define SRMECH_GENOME_BOOLEAN_NTERMS_BYTES 2u
#define SRMECH_GENOME_BOOLEAN_TERM_BYTES (2u * SRMECH_GENOME_REGULATORY_MASK_BYTES)

/* §131/v10 THRESHOLD GENE marker (rc131, #731) — the FIRST byte of a fixed-width leaf_dim-byte cap
 * leaf that opens an INTRA-chromosome gene (like the plain GENE cap / the §128 regulatory gene /
 * the §130 boolean gene) AND carries a LINEAR-THRESHOLD (perceptron) gate inline: a per-condition
 * SIGNED integer WEIGHT vector + an integer THRESHOLD. The THIRD gate-type in the rc129 dispatch
 * family (E1 klein4_mask 0x67 / E2 boolean_dnf 0x62 / E4 threshold 0x77). GENUINELY DISTINCT from
 * E2: a linear-threshold function (MAJORITY-of-n, a weighted dose-sum) needs an EXPONENTIALLY-large
 * DNF, so E4 captures COMPACTLY what E2 cannot (linear-threshold subset-not small-DNF). Layout:
 * [0x77] + utf-8 label + NUL + gate_type(uint8) + n_weights(uint16 big-endian) +
 * threshold(int64 BE SIGNED two's-complement) + n_weights x (weight(int64 BE SIGNED)) + NUL-pad to
 * leaf_dim. The label decode is UNIFORM (bytes [1:] up to the first NUL); the gate_type + weights +
 * threshold are read at the bytes RIGHT AFTER that NUL. > 3 and distinct from every other marker
 * (CHROM 0x43 / GENE 0x47 / v5 KERNEL 0x4B / PACKED 0x51 / KERNEL-telomere 0x6B / ACTIVE-telomere
 * 0x74 / REGULATORY-gene 0x67 / BOOLEAN-gene 0x62), so v2..v9 bodies read UNCHANGED — the walker
 * gains ONE branch. A NEW marker byte = a new block KIND, so it bumps the genome format v9 -> v10.
 * srmech_genome_gene_express evaluates the perceptron (express iff Sum weight_i * bit_i(cell_state)
 * >= threshold; the decision is the SIGN of the sum minus threshold — Class-K, never abs). Mirrors
 * THRESHOLD_GENE_MARKER in srmech.amsc.genome. */
#define SRMECH_GENOME_THRESHOLD_GENE_MARKER 0x77u /* 'w' — a §131 threshold gene */

/* §131/v10 REGULATORY GATE-TYPE enum extension (rc131, #731). THRESHOLD (2) = the §131 linear-
 * threshold / perceptron gate (a SIGNED integer weight vector + a threshold, carried by a 0x77
 * cap); srmech_genome_gene_express dispatches on the cap marker. Mirrors GATE_TYPE_THRESHOLD in
 * srmech.amsc.genome. */
#define SRMECH_GENOME_GATE_TYPE_THRESHOLD 2u

/* §131/v10 THRESHOLD GENE wire widths (rc131, #731). The weight-vector LENGTH is a uint16
 * big-endian (2 bytes; weight i gates condition bit i of the cell_state). The THRESHOLD and each
 * WEIGHT are int64 big-endian SIGNED two's-complement (8 bytes each; SIGNED so an inhibitory /
 * repressive input is a NEGATIVE weight). Mirror _THRESHOLD_GENE_* in srmech.amsc.genome. */
#define SRMECH_GENOME_THRESHOLD_NWEIGHTS_BYTES 2u
#define SRMECH_GENOME_THRESHOLD_VALUE_BYTES 8u

/* §132/v11 GRADED (dose-response) GENE marker (rc132, #732) — the FIRST byte of a fixed-width
 * leaf_dim-byte cap leaf that opens an INTRA-chromosome gene (like the plain GENE cap / the §128
 * regulatory / §130 boolean / §131 threshold gene) AND carries an ANALOG (dose-response)
 * EXPRESSION LEVEL inline: a per-condition SIGNED integer LEVEL-WEIGHT vector + a POSITIVE integer
 * DENOMINATOR. It is the E3 GRADED LEVEL rung — an ORTHOGONAL AXIS on top of the E1/E2/E4 gate-type
 * family: the gate-types decide IF a gene expresses (binary); E3 decides HOW MUCH (analog output,
 * real biology). srmech_genome_gene_express_levels reports the LEVEL as the reduced exact rational
 * Sum_i (level_weight_i * bit_i(cell_state)) / denom clamped to [0, 1] (a Class-K sign-branch,
 * never abs; the fraction reduced by the Class-I gcd). Layout: [0x64] + utf-8 label + NUL +
 * gate_type(uint8=3) + n_weights(uint16 big-endian) + denom(uint64 BE POSITIVE) + n_weights x
 * (level_weight(int64 BE SIGNED)) + NUL-pad to leaf_dim. The label decode is UNIFORM (bytes [1:]
 * up to the first NUL); the gate_type + n_weights + denom + weights are read at the bytes RIGHT
 * AFTER that NUL. > 3 and distinct from every other marker (CHROM 0x43 / GENE 0x47 / v5 KERNEL
 * 0x4B / PACKED 0x51 / KERNEL-telomere 0x6B / ACTIVE-telomere 0x74 / REGULATORY-gene 0x67 /
 * BOOLEAN-gene 0x62 / THRESHOLD-gene 0x77), so v2..v10 bodies read UNCHANGED — the walker gains ONE
 * branch. A NEW marker byte = a new block KIND, so it bumps the genome format v10 -> v11. Mirrors
 * GRADED_GENE_MARKER in srmech.amsc.genome. */
#define SRMECH_GENOME_GRADED_GENE_MARKER 0x64u /* 'd' — a §132 graded (dose) gene */

/* §132/v11 GRADED GATE-TYPE (rc132, #732). GRADED (3) = the §132 analog dose-response LEVEL axis
 * (a SIGNED integer level-weight vector + a POSITIVE denominator, carried by a 0x64 cap). NOT a
 * binary gate-type in the E1/E2/E4 IF-family — the ORTHOGONAL HOW-MUCH axis; the gate_type is
 * stored in the cap for self-description / extensibility. Mirrors GATE_TYPE_GRADED in
 * srmech.amsc.genome. */
#define SRMECH_GENOME_GATE_TYPE_GRADED 3u

/* §132/v11 GRADED GENE wire widths (rc132, #732). The level-weight-vector LENGTH is a uint16
 * big-endian (2 bytes; weight i doses condition bit i). The DENOMINATOR is a uint64 big-endian
 * POSITIVE integer (8 bytes; the full-expression dose — a divisor is never negative, so UNSIGNED,
 * never abs). Each LEVEL-WEIGHT is int64 big-endian SIGNED two's-complement (8 bytes; SIGNED so an
 * inhibitory input REDUCES the dose). Mirror _GRADED_GENE_* in srmech.amsc.genome. */
#define SRMECH_GENOME_GRADED_NWEIGHTS_BYTES 2u
#define SRMECH_GENOME_GRADED_DENOM_BYTES 8u
#define SRMECH_GENOME_GRADED_WEIGHT_BYTES 8u

/* Max label byte length (NUL-terminated) for one chromosome. This is a FORMAT
 * width (a label lives inline in a leaf_dim-byte cap block, like PATH_MAX), NOT
 * a count cap — the number of chromosomes is bounded only by the caller arena. */
#define SRMECH_GENOME_MAX_LABEL 256

/* SAVE: write <dir>/turns.bin (= `body` verbatim, body_len bytes) and
 * <dir>/manifest.json (byte-identical to the Python genome_save manifest).
 *
 * §44: the chromosome layout is DERIVED by SCANNING the self-describing body
 * — there is no caller-supplied layout. Every CHROM cap (first byte
 * SRMECH_GENOME_CHROM_CAP_MARKER) opens a chromosome whose label is read INLINE
 * from the cap, whose leaf_count is the DATA-turn count (blocks that are NOT a
 * CHROM/GENE cap), and whose byte_offset/byte_len span up to the next CHROM cap
 * (or EOF). The derived manifest is byte-identical to the Python genome_save's
 * (the strand is the SSoT; the manifest is a derived cache).
 *   body / body_len : the self-describing body (CHROM/GENE caps + coupled
 *                     turns — §55/v3: blocks are variable-width, keyed by
 *                     their first byte; n_turns = the scanned BLOCK count).
 *   leaf_dim        : the cap / in-memory leaf width in bytes (> 0, <= 256).
 *   the_one / the_one_len : the_one's single leaf_dim-byte block
 *                     (the_one_len MUST equal leaf_dim).
 *   ws / ws_len     : the caller arena for ALL scratch (the per-chromosome
 *                     scan arrays + the manifest buffer + the JSON tree) — the
 *                     bound is the caller's RAM, NOT a compiled-in cap. Size it
 *                     to the genome (a host sizes it large, an MCU small);
 *                     SRMECH_ERR_OVERFLOW if too small for this genome.
 *
 * Error returns:
 *   SRMECH_ERR_NULL_ARG   — dir / body(when body_len>0) / the_one / ws NULL.
 *   SRMECH_ERR_BAD_INPUT   — leaf_dim == 0 / > 256, the_one_len != leaf_dim,
 *                           a truncated / unrecognised block, a turn before
 *                           the first CHROM cap, or a label too long.
 *   SRMECH_ERR_IO          — fopen / fwrite failed.
 *   SRMECH_ERR_OVERFLOW    — the caller arena ws is too small for this genome.
 */
srmech_status_t srmech_genome_save(
    const char *dir,
    const unsigned char *body, size_t body_len,
    uint32_t leaf_dim,
    const unsigned char *the_one, size_t the_one_len,
    void *ws, size_t ws_len);

/* The arena byte count any genome op needs for a body of `body_len` bytes with
 * `n_chroms` chromosomes when it also stages a `region_len`-byte region (a .chr
 * region, or an append/replace region; 0 otherwise). Capacity is DEFINED by the
 * C layout — the caller sizes its `ws` arena from THIS rather than guessing. Pure
 * arithmetic (no I/O); each term traces to a real allocation (two body copies +
 * the .chr region/hex/io + per-chromosome strings/manifest/json + a fixed slop).
 * Adding this symbol does NOT bump SRMECH_ABI_VERSION. */
size_t srmech_genome_arena_bytes(size_t body_len, uint32_t n_chroms,
                                 size_t region_len);

/* CATALOG: obtain the manifest catalog as a JSON value tree from the caller
 * arena `ws`. When <dir>/manifest.json is PRESENT this parses it ONLY (never
 * opens turns.bin) — the cheap catalog read. §44: when it is ABSENT the catalog
 * is REBUILT by scanning the self-describing turns.bin (the strand is the SSoT,
 * the manifest an optional .fai cache); that rebuild needs `the_one`
 * (the_one_len IS the leaf width). On success *out_manifest points at the root
 * object (the full MPRRecord; its "data" child is the catalog).
 * Pass the_one=NULL,the_one_len=0 when a manifest is known to be present.
 *
 * Error returns:
 *   SRMECH_ERR_NULL_ARG   — dir / ws / out_manifest is NULL.
 *   SRMECH_ERR_IO          — turns.bin could not be opened / read on rebuild.
 *   SRMECH_ERR_OVERFLOW    — the manifest or its tree exceeds ws / turns.bin
 *                           exceeds the rebuild scratch.
 *   SRMECH_ERR_BAD_INPUT   — manifest.json is malformed JSON, OR it is absent
 *                           and no the_one was supplied (cannot scan).
 */
srmech_status_t srmech_genome_catalog(
    const char *dir, const unsigned char *the_one, size_t the_one_len,
    void *ws, size_t ws_len, srmech_json_value_t **out_manifest);

/* LOAD: read <dir>/turns.bin into `out` (capacity out_cap bytes), re-hash
 * the whole body and compare its hex against the manifest's
 * data.body_sha256. On a mismatch returns SRMECH_ERR_BAD_INPUT (the
 * GenomeBoundingError analogue). *out_len receives the body length. §44: when
 * manifest.json is absent the catalog is rebuilt by scanning turns.bin, which
 * needs `the_one` (the_one_len IS the leaf width); pass the_one=NULL,0 when a
 * manifest is present.
 *
 * Error returns:
 *   SRMECH_ERR_NULL_ARG   — dir / out / out_len / ws is NULL.
 *   SRMECH_ERR_IO          — turns.bin I/O failed.
 *   SRMECH_ERR_OVERFLOW    — out_cap < body length, or ws too small.
 *   SRMECH_ERR_BAD_INPUT   — body hash != manifest body_sha256 (bound
 *                           failed), a malformed manifest, OR no manifest and
 *                           no the_one.
 */
srmech_status_t srmech_genome_load(
    const char *dir, unsigned char *out, size_t out_cap, size_t *out_len,
    const unsigned char *the_one, size_t the_one_len,
    void *ws, size_t ws_len);

/* WINDOW: seek to one chromosome's byte_offset, read its byte_len bytes
 * into `out` (capacity out_cap), re-hash the leading cap block and compare
 * its hex against that chromosome's cap_sha256. On a mismatch returns
 * SRMECH_ERR_BAD_INPUT (the bounding error). *out_len receives byte_len.
 * The returned bytes include the leading cap block (the whole region). §44:
 * when manifest.json is absent the offsets are rebuilt by scanning turns.bin,
 * which needs `the_one` (the_one_len IS the leaf width); pass the_one=NULL,0
 * when a manifest is present.
 *
 * Error returns:
 *   SRMECH_ERR_NULL_ARG   — dir / label / out / out_len / ws is NULL.
 *   SRMECH_ERR_IO          — turns.bin I/O failed.
 *   SRMECH_ERR_OVERFLOW    — out_cap < byte_len, or ws too small.
 *   SRMECH_ERR_BAD_INPUT   — label absent, cap hash != cap_sha256, a
 *                           malformed manifest, OR no manifest and no the_one.
 */
srmech_status_t srmech_genome_window(
    const char *dir, const char *label,
    unsigned char *out, size_t out_cap, size_t *out_len,
    const unsigned char *the_one, size_t the_one_len,
    void *ws, size_t ws_len);

/* §134/rc135 (#1273) GENE-EXPRESSION PLAN: the DEMAND-LOAD, offset-only load
 * plan. For each chromosome in <dir>'s manifest, seek to its byte_offset and
 * read ONLY the head GATE cap (the second block, at byte_offset + leaf_dim),
 * evaluate its inline gate (E1 0x67 / E2 0x62 / E4 0x77 / E3 0x64) under
 * cell_state, and emit the EXPRESSED regions into `out` (capacity out_cap
 * bytes). NEVER reads a region body — bounded I/O (one leaf_dim-byte gate cap
 * per chromosome). *out_len receives the emitted byte count. Emit format
 * (big-endian): [u32 n] then per record [u32 label_len][label bytes]
 * [u64 byte_offset][u64 byte_len]. Byte-identical to the pure-Python
 * gene_express_plan PATH variant (the siona community=chromosome layout — the
 * per-chromosome head gate IS the community gate). A READ (never mutates);
 * malloc-free (the manifest parses in the caller arena `ws`; the gate cap is a
 * fixed stack buffer). §44: when manifest.json is absent the offsets are
 * rebuilt by scanning turns.bin, which needs `the_one` (the_one_len IS the leaf
 * width); pass the_one=NULL,0 when a manifest is present. ABI-additive: a new
 * symbol, so SRMECH_ABI_VERSION stays 3.
 *
 * Error returns:
 *   SRMECH_ERR_NULL_ARG   — dir / out / out_len / ws is NULL.
 *   SRMECH_ERR_IO          — turns.bin I/O failed.
 *   SRMECH_ERR_OVERFLOW    — ws too small for the manifest parse.
 *   SRMECH_ERR_BAD_INPUT   — out too small for the plan, a malformed manifest,
 *                           OR no manifest and no the_one.
 */
srmech_status_t srmech_genome_gene_express_plan(
    const char *dir, uint64_t cell_state,
    const unsigned char *the_one, size_t the_one_len,
    unsigned char *out, size_t out_cap, size_t *out_len,
    void *ws, size_t ws_len);

/* APPEND: append one chromosome's region (`region`, region_len bytes = the
 * cap block + its data turns, all leaf_dim-byte blocks) to the END of
 * <dir>/turns.bin (append-only; prior body bytes are never rewritten), then
 * rewrite manifest.json with the new chromosome entry + recomputed n_turns /
 * body_sha256. Every EXISTING chromosome entry (cap_sha256 / byte_offset /
 * leaf_count / byte_len) is carried through byte-identically.
 *   the_one / the_one_len : the_one block (the_one_len == leaf_dim), re-used
 *                     for the manifest the_one hash+hex (must match the stored
 *                     leaf_dim; the prior body is bound-checked before growth).
 *
 * Error returns:
 *   SRMECH_ERR_NULL_ARG   — dir / label / region(when region_len>0) /
 *                           the_one / ws is NULL.
 *   SRMECH_ERR_IO          — turns.bin / manifest.json I/O failed.
 *   SRMECH_ERR_OVERFLOW    — ws too small, or too many chromosomes.
 *   SRMECH_ERR_BAD_INPUT   — leaf_dim mismatch, label already present, a
 *                           truncated / unrecognised region block (§55/v3:
 *                           blocks are variable-width, validated by the scan),
 *                           prior body bound failed, or malformed manifest.
 */
srmech_status_t srmech_genome_append(
    const char *dir, const char *label,
    const unsigned char *region, size_t region_len, uint32_t leaf_dim,
    const unsigned char *the_one, size_t the_one_len,
    void *ws, size_t ws_len);

/* §45 IN-PLACE EDIT — biology excises, it does not re-synthesize. With the §44
 * self-describing body an edit is a pure BYTE splice on turns.bin (no kernel is
 * decoded / re-coupled — the surviving chromosomes' coupled bytes stay
 * byte-identical, only relocated). The spliced body is committed via
 * srmech_genome_save, which re-derives the manifest by scanning it, so the
 * on-disk turns.bin + manifest.json are byte-identical to the Python
 * genome_remove / genome_replace output. Like APPEND (a write op), `the_one` is
 * REQUIRED (srmech_genome_save needs it for the manifest the_one hash+hex) and
 * the_one_len IS leaf_dim. The whole body is re-hashed against the committed
 * body_sha256 BEFORE the edit (the GenomeBoundingError analogue). */

/* REMOVE: excise chromosome `label` IN PLACE — find its region in the
 * self-describing body, splice the [byte_offset, byte_offset+byte_len) span out
 * of turns.bin, and rewrite manifest.json (DERIVED by scanning the spliced
 * body). Mirrors the Python genome_remove. the_one_len MUST equal the stored
 * leaf_dim.
 *
 * Error returns:
 *   SRMECH_ERR_NULL_ARG   — dir / label / the_one / ws is NULL.
 *   SRMECH_ERR_IO          — turns.bin / manifest.json I/O failed.
 *   SRMECH_ERR_OVERFLOW    — ws too small, or body exceeds the scratch.
 *   SRMECH_ERR_BAD_INPUT   — the_one_len 0 / > 256 or != stored leaf_dim, label
 *                           absent, `label` is the genome's ONLY chromosome,
 *                           prior body bound failed, or malformed manifest.
 */
srmech_status_t srmech_genome_remove(
    const char *dir, const char *label,
    const unsigned char *the_one, size_t the_one_len,
    void *ws, size_t ws_len);

/* REPLACE: swap chromosome `label`'s content IN PLACE — splice its old span out
 * of turns.bin and `region` (region_len bytes = a fresh telomere-capped
 * chromosome's cap block + data turns, all leaf_dim-byte blocks) IN at the same
 * position, then rewrite manifest.json (DERIVED by scanning the new body). Every
 * OTHER chromosome's body bytes stay byte-identical. Mirrors the Python
 * genome_replace (whose `leaves` are coupled into the region by the caller).
 *
 * Error returns:
 *   SRMECH_ERR_NULL_ARG   — dir / label / region(when region_len>0) / the_one /
 *                           ws is NULL.
 *   SRMECH_ERR_IO          — turns.bin / manifest.json I/O failed.
 *   SRMECH_ERR_OVERFLOW    — ws too small, or the new body exceeds the scratch.
 *   SRMECH_ERR_BAD_INPUT   — leaf_dim 0 / the_one_len != leaf_dim / != stored
 *                           leaf_dim, region_len not a whole multiple of
 *                           leaf_dim, label absent, prior body bound failed, or
 *                           malformed manifest.
 */
srmech_status_t srmech_genome_replace(
    const char *dir, const char *label,
    const unsigned char *region, size_t region_len, uint32_t leaf_dim,
    const unsigned char *the_one, size_t the_one_len,
    void *ws, size_t ws_len);

/* §43 FILE-MANAGEMENT — the chromosome as a bundleable .chr file. Now that §44
 * made the strand self-describing and §45 made it editable in place, a
 * chromosome can be EXPORTED as ONE self-contained, content-addressed file
 * (.chr), shipped, and re-IMPORTED into a genome self-verifying — the "tar one
 * chromosome, ship it" goal. A .chr is ONE MPR record built with the SAME json
 * builder + writer the manifest uses, so it is BYTE-IDENTICAL to the Python
 * genome_export's json.dumps(sort_keys=True, ensure_ascii=False) + LF; its
 * attestation.response_sha256 IS the region hash, so an import re-hashes the
 * region and self-verifies. This COMPOSES the §41 MPR surface — it is NOT a
 * parallel attestation. Mirrors srmech.amsc.genome genome_export / genome_import.
 *
 * The .chr region / hex / file-text scratch is carved from the caller arena
 * (sized to the chromosome / the .chr file), so a chromosome of any size the
 * caller's arena fits can be bundled — no compiled-in cap. */

/* EXPORT: write chromosome `label`'s region (CHROM cap + coupled turns; the
 * leading cap re-hashed against the manifest cap_sha256) + the_one to `out_path`
 * as ONE MPR-attested .chr record. `the_one` is OPTIONAL — pass it (length ==
 * leaf_dim) to export from a MANIFEST-LESS source (§44; the catalog is rebuilt
 * by scanning turns.bin), else NULL when manifest.json is present. The .chr
 * round-trips byte-identically.
 *
 * Error returns:
 *   SRMECH_ERR_NULL_ARG   — dir / label / out_path / ws is NULL.
 *   SRMECH_ERR_IO          — turns.bin / the .chr I/O failed.
 *   SRMECH_ERR_OVERFLOW    — the caller arena ws is too small for this
 *                           chromosome (its region / hex / .chr text).
 *   SRMECH_ERR_BAD_INPUT   — the_one_len 0 / > 256, label absent, cap integrity
 *                           bound failed, or a malformed manifest. */
srmech_status_t srmech_genome_export(
    const char *dir, const char *label, const char *out_path,
    const unsigned char *the_one, size_t the_one_len,
    void *ws, size_t ws_len);

/* IMPORT: read a .chr bundle (genome_export's output), RE-HASH its region and
 * its the_one against the bundle's own attestation (self-verifying — a flipped
 * byte is SRMECH_ERR_BAD_INPUT), then either SEED a fresh genome at `dest` when
 * it has no turns.bin yet (the region becomes turns.bin VERBATIM) or APPEND the
 * chromosome byte-for-byte into the existing dest (which REQUIRES the same
 * coupling invariant — dest the_one.sha256 == the .chr's — and a fresh label).
 * `the_one` is only consulted as the rebuild width for a manifest-less existing
 * dest (§44); the bundle carries its own the_one. The dest directory must exist
 * (the C surface does not mkdir — turns.bin is written into an existing dir,
 * like save / append). Mirrors the Python genome_import.
 *
 * Error returns:
 *   SRMECH_ERR_NULL_ARG   — chr_path / dest / ws is NULL.
 *   SRMECH_ERR_IO          — the .chr / turns.bin / manifest.json I/O failed.
 *   SRMECH_ERR_OVERFLOW    — the caller arena ws is too small for this .chr
 *                           (its text / decoded region / the dest body grow).
 *   SRMECH_ERR_BAD_INPUT   — not a chromosome bundle (wrong data_schema_id),
 *                           a region / the_one integrity bound failed, the dest
 *                           leaf_dim / the_one mismatches, the label already
 *                           exists in dest, or a malformed bundle / manifest. */
srmech_status_t srmech_genome_import(
    const char *chr_path, const char *dest,
    const unsigned char *the_one, size_t the_one_len,
    void *ws, size_t ws_len);

/* §43 LOOSE<->PACKED — git's object model for genomes.
 *
 * EXPLODE: write one loose <label>.chr bundle per chromosome of the packed
 * genome at `dir` into `out_dir` (which must exist; the C surface does not
 * mkdir), each via srmech_genome_export (so each .chr self-verifies). Like
 * `git unpack-objects`. `the_one` is only consulted as the rebuild width
 * for a manifest-less source (§44); when the source has a manifest.json it
 * may be NULL. Every chromosome label must be filename-safe (no '/' / '\\',
 * not "" / "." / "..") — else SRMECH_ERR_BAD_INPUT. Mirrors the Python
 * genome_explode.
 *
 * Error returns:
 *   SRMECH_ERR_NULL_ARG   — dir / out_dir / ws is NULL.
 *   SRMECH_ERR_IO          — turns.bin / a .chr write failed.
 *   SRMECH_ERR_OVERFLOW    — the caller arena ws is too small for this explode
 *                           (the labels array / a chromosome), or a path too long.
 *   SRMECH_ERR_BAD_INPUT   — the_one_len 0 / > 256, an unsafe label, a cap
 *                           integrity bound failed, or a malformed manifest. */
srmech_status_t srmech_genome_explode(
    const char *dir, const char *out_dir,
    const unsigned char *the_one, size_t the_one_len,
    void *ws, size_t ws_len);

/* PACK: read every <label>.chr in `loose_dir` (a *.chr directory scan), sort
 * them by their inner data.label (CANONICAL order — content-preserving, not
 * byte-order-preserving: it re-canonicalises), and srmech_genome_import each
 * in order into `dest` (the first SEEDS dest, the rest APPEND — so they must
 * share one the_one). Like `git repack`. `dest` must exist (no mkdir); an
 * empty `loose_dir` (or no *.chr files) is SRMECH_ERR_BAD_INPUT. `the_one` is
 * only the rebuild width for a manifest-less existing dest (§44). Mirrors the
 * Python genome_pack.
 *
 * Error returns:
 *   SRMECH_ERR_NULL_ARG   — loose_dir / dest / ws is NULL.
 *   SRMECH_ERR_IO          — a .chr / turns.bin / manifest.json I/O failed.
 *   SRMECH_ERR_OVERFLOW    — the caller arena ws is too small for this pack
 *                           (the .chr names / labels / a bundle / the body), or
 *                           a path too long.
 *   SRMECH_ERR_BAD_INPUT   — the_one_len 0 / > 256, no .chr files, a bundle is
 *                           not a chromosome / fails its integrity bound, or
 *                           the dest leaf_dim / the_one / label invariant. */
srmech_status_t srmech_genome_pack(
    const char *loose_dir, const char *dest,
    const unsigned char *the_one, size_t the_one_len,
    void *ws, size_t ws_len);

/* §127/v7 (#726) ACTIVE-TELOMERE TICK — the divide/gate op whose OPERATOR behaviour
 * is SELECTED by its OPERAND (the count). Read the exact non-negative COUNT carried
 * inline in an active-telomere cap (`cap`, the first leaf_dim bytes; marker 0x74) and
 * decide:
 *   count == 0 -> SENESCENCE: *senescent = 1, *count_after = 0, out_cap = cap verbatim
 *                 (the honest refuse — no divide).
 *   count  > 0 -> DIVIDE:     *senescent = 0, *count_after = count - 1, out_cap = cap
 *                 with the count field decremented by exactly 1 (the daughter cap; the
 *                 telomere shortens). Byte-identical to the Python telomere_tick.
 * The count lives at the SRMECH_GENOME_ACTIVE_TELOMERE_COUNT_BYTES (8) bytes right
 * after the label's NUL terminator, big-endian. No arena (out_cap is caller-provided,
 * leaf_dim bytes); malloc-free; no abs (a count is never negated).
 *   cap / leaf_dim : the active-telomere cap leaf (leaf_dim bytes; cap[0] == 0x74).
 *   out_cap        : caller buffer >= leaf_dim bytes — the daughter (or verbatim) cap.
 *   senescent      : out — 1 iff count was 0 (refuse), else 0.
 *   count_after    : out — the decremented count (0 on senescence).
 * Error returns:
 *   SRMECH_ERR_NULL_ARG  — cap / out_cap / senescent / count_after is NULL.
 *   SRMECH_ERR_BAD_INPUT  — leaf_dim 0, cap[0] != 0x74, no label NUL, or a truncated
 *                          count field. */
srmech_status_t srmech_genome_telomere_tick(
    const unsigned char *cap, size_t leaf_dim,
    unsigned char *out_cap, int *senescent, uint64_t *count_after);

/* §128/v8 (#728) + §129 (#729) GENE EXPRESSION — the per-gene read-time FILTER whose OPERATOR
 * behaviour (express or not) is SELECTED by its OPERAND (the cell_state). Read the regulatory
 * MASK(s) carried inline in a gene cap (`cap`, the first leaf_dim bytes) and decide:
 *   plain GENE cap (cap[0] == 0x47, no masks) -> masks 0, *expressed = 1 (ALWAYS expresses;
 *                    an unregulated gene == masks 0 — back-compat).
 *   REGULATORY GENE cap (cap[0] == 0x67) -> read the TWO KLEIN-4 bit-planes (activator then
 *                    repressor), *expressed = 1 iff (cell_state & activator) == activator (ALL
 *                    activators PRESENT) AND (cell_state & repressor) == 0 (NO repressor
 *                    PRESENT), else 0. Per condition (act_bit, rep_bit) is a Klein-4 role:
 *                    (0,0) don't-care / (1,0) activator / (0,1) repressor / (1,1) never (a bit
 *                    set in BOTH masks = present AND absent = contradiction -> auto-silenced).
 * Byte-identical to the pure Python decision in srmech.amsc.genome._gene_expresses. The
 * activator lives at the SRMECH_GENOME_REGULATORY_MASK_BYTES (8) bytes right after the label's
 * NUL terminator (big-endian, always present); the repressor at the NEXT 8 bytes IF the leaf
 * has room, else 0. §129 DUAL-READ: the repressor plane sits in what was NUL padding, so a
 * rc128 single-mask cap / a short leaf carries NO repressor field -> repressor 0 (identical
 * rc128 behaviour). §130/v9 (#730): a BOOLEAN GENE cap (cap[0] == 0x62) carries the GENERAL
 * gate-type — an arbitrary boolean function over the conditions in DNF (an OR of (activator,
 * repressor) AND-clauses); *expressed = 1 iff ANY clause matches (E1 subset E2 — the klein4-mask
 * two-mask is a 1-clause DNF; the empty DNF is FALSE = never). mask_out is 0 for a boolean gene
 * (no single activator plane). §131/v10 (#731): a THRESHOLD GENE cap (cap[0] == 0x77) carries a
 * LINEAR-THRESHOLD / perceptron gate — a per-condition SIGNED int64 WEIGHT vector + an int64
 * THRESHOLD; *expressed = 1 iff Sum_i (weight_i * bit_i(cell_state)) >= threshold (the decision is
 * the SIGN of the exact signed sum minus threshold — Class-K, never abs; SIGNED weights allow an
 * inhibitory input). mask_out is 0 for a threshold gene. If the exact int64 accumulate would
 * OVERFLOW, this returns SRMECH_ERR_OVERFLOW so the caller falls to the pure (arbitrary-precision)
 * Python path — the native result, when produced, is byte-identical to Python. No arena (a per-cap
 * decision); malloc-free; no abs. NEVER MUTATES cap (a READ — biology does not rewrite DNA).
 *   cap / leaf_dim : the gene cap leaf (leaf_dim bytes; cap[0] == 0x47, 0x67, 0x62 or 0x77).
 *   cell_state     : the exact non-negative cell-state bitmask (each set bit a condition).
 *   expressed      : out — 1 iff the gene expresses under cell_state, else 0.
 *   mask_out       : out — the gene's ACTIVATOR mask (0 for a plain / boolean / threshold gene);
 *                    may be NULL.
 * Error returns:
 *   SRMECH_ERR_NULL_ARG  — cap / expressed is NULL.
 *   SRMECH_ERR_BAD_INPUT  — leaf_dim 0, cap[0] is not 0x47 / 0x67 / 0x62 / 0x77, no label NUL, a
 *                          truncated activator field (regulatory gene), a truncated /
 *                          unsupported-gate_type DNF header / term list (boolean gene), or a
 *                          truncated / unsupported-gate_type threshold header / weight vector.
 *   SRMECH_ERR_OVERFLOW  — the int64 weighted-sum accumulate would overflow (threshold gene) ->
 *                          the caller uses the exact pure Python path. */
srmech_status_t srmech_genome_gene_express(
    const unsigned char *cap, size_t leaf_dim, uint64_t cell_state,
    int *expressed, uint64_t *mask_out);

/* §132/v11 (#732) GRADED / ANALOG gene expression LEVEL — the ORTHOGONAL companion to
 * srmech_genome_gene_express. Where gene_express decides IF each gene expresses (binary), this
 * reports the exact-rational LEVEL — HOW MUCH — of the gene opened by `cap` under `cell_state`,
 * as a reduced (num_out, den_out) pair (den_out >= 1). Dispatches on the cap marker:
 *   GRADED GENE cap (cap[0] == 0x64) -> the ANALOG dose-response: read the SIGNED int64
 *       LEVEL-WEIGHT vector + the POSITIVE uint64 DENOMINATOR after the label NUL; the level is
 *       Sum_i (level_weight_i * bit_i(cell_state)) / denom CLAMPED to [0, 1] (Class-K sign-branch,
 *       never abs) and reduced by the Class-I gcd (srmech_gcd). raw dose <= 0 -> (0, 1) (off);
 *       raw dose >= denom -> (1, 1) (fully on); else the reduced in-range fraction.
 *   a BINARY gene cap (cap[0] == 0x47 / 0x67 / 0x62 / 0x77) is the DEGENERATE {0, 1} case:
 *       (1, 1) if its E1/E2/E4 gate PASSES (the SAME decision as srmech_genome_gene_express) else
 *       (0, 1). So the level axis composes with EVERY gate-type.
 * A gene is "expressed" iff num_out > 0 (the caller filters). Byte-identical to the pure Python
 * decision in srmech.amsc.genome._gene_level. If the exact int64 dose accumulate would OVERFLOW,
 * this returns SRMECH_ERR_OVERFLOW so the caller falls to the pure (arbitrary-precision) Python
 * path. No arena (a per-cap decision); malloc-free; no abs. NEVER MUTATES cap (a READ).
 *   cap / leaf_dim : the gene cap leaf (leaf_dim bytes; cap[0] in {0x47,0x67,0x62,0x77,0x64}).
 *   cell_state     : the exact non-negative cell-state bitmask (each set bit a present condition).
 *   num_out        : out — the reduced level numerator (>= 0).
 *   den_out        : out — the reduced level denominator (>= 1).
 * Error returns:
 *   SRMECH_ERR_NULL_ARG  — cap / num_out / den_out is NULL.
 *   SRMECH_ERR_BAD_INPUT  — leaf_dim 0, cap[0] not a gene marker, no label NUL, a truncated /
 *                          unsupported-gate_type / zero-denom graded header or weight vector, or a
 *                          malformed binary gene (propagated from srmech_genome_gene_express).
 *   SRMECH_ERR_OVERFLOW  — the int64 graded-dose accumulate would overflow -> the caller uses the
 *                          exact pure Python path. */
srmech_status_t srmech_genome_gene_express_levels(
    const unsigned char *cap, size_t leaf_dim, uint64_t cell_state,
    uint64_t *num_out, uint64_t *den_out);

/* §133/v11 (#733) MODULATOR-RECOVERY verdict codes — the *verdict out of
 * srmech_genome_modulator_recover. Mirrors the one-sided op_verdict (rc117)
 * EQUAL/UNKNOWN contract: UNKNOWN (none pinned) / PARTIAL (some pinned) / EXACT
 * (the floor pins every referenced condition bit). */
#define SRMECH_GENOME_MODULATOR_UNKNOWN 0
#define SRMECH_GENOME_MODULATOR_PARTIAL 1
#define SRMECH_GENOME_MODULATOR_EXACT   2

/* §133/v11 (#733) M1 — the INVERSE of gene_express: recover the TWO-SIDED cell-
 * state FLOOR from an OBSERVED expressed-label set. `body` is the GENE-CAP subset
 * of the strand (each block leaf_dim bytes, first byte a gene marker
 * 0x47/0x67/0x62/0x77/0x64 — the data turns do NOT gate expression, so the caller
 * strips them). `expressed` is the observed labels as NUL-delimited UTF-8 tokens
 * (label\0label\0...; expressed_len bytes; NULL,0 = the empty set). Outputs:
 *   *certain_on  — bits every consistent cell_state MUST have SET (OR of each
 *                  EXPRESSED E1 gene's activator mask + each EXPRESSED E2 gene's
 *                  intersection-over-clauses activator).
 *   *certain_off — bits every consistent state MUST have CLEAR (the repressor duals).
 *   *undetermined— the referenced condition bits (union of bits ANY gene reads)
 *                  minus (certain_on | certain_off).
 *   *verdict     — SRMECH_GENOME_MODULATOR_{EXACT,PARTIAL,UNKNOWN}.
 * E4 threshold / E3 graded / un-expressed genes give NO clean single-bit certainty
 * -> they contribute to *undetermined, NEVER to the floor (SOUND, not over-claiming).
 * A gene's floor is applied only when its label is expressed AND UNIQUE among the
 * body's gene caps (a duplicated label cannot be attributed). SOUND: for every
 * candidate the companion op reports CONSISTENT, (state & *certain_on) == *certain_on
 * AND (state & *certain_off) == 0. Byte-identical to the pure Python
 * srmech.amsc.genome._modulator_recover_pure. No arena; malloc-free; no abs; a READ.
 * Error returns:
 *   SRMECH_ERR_NULL_ARG  — body(when body_len>0) / expressed(when expressed_len>0) /
 *                          any out pointer is NULL.
 *   SRMECH_ERR_BAD_INPUT  — leaf_dim 0 / > 256, body_len not a multiple of leaf_dim,
 *                          or a malformed / truncated gene cap. */
srmech_status_t srmech_genome_modulator_recover(
    const unsigned char *body, size_t body_len, size_t leaf_dim,
    const unsigned char *expressed, size_t expressed_len,
    uint64_t *certain_on, uint64_t *certain_off,
    uint64_t *undetermined, int *verdict);

/* §133/v11 (#733) M2 — forward-CHECK one candidate cell_state: is
 * set(gene_express(candidate) labels) == set(expected)? `body` is the GENE-CAP
 * subset (as for srmech_genome_modulator_recover); `expected` is the observed
 * labels as NUL-delimited UTF-8 tokens. *consistent = 1 iff the two label sets are
 * EQUAL (both-subset: every EXPRESSING gene's label is expected AND every expected
 * token is produced by some EXPRESSING gene). ONE-SIDED: CONSISTENT means "could be
 * the state" (many candidates may be), NEVER "it IS the state". Reuses the forward
 * per-gene srmech_genome_gene_express (no new gate logic). Byte-identical to the
 * pure Python set comparison. No arena; malloc-free; no abs; a READ.
 * Error returns:
 *   SRMECH_ERR_NULL_ARG  — body(when body_len>0) / expected(when expected_len>0) /
 *                          consistent is NULL.
 *   SRMECH_ERR_BAD_INPUT  — leaf_dim 0 / > 256, body_len not a multiple of leaf_dim,
 *                          or a malformed gene cap.
 *   SRMECH_ERR_OVERFLOW  — an int64 threshold / graded accumulate would overflow ->
 *                          the caller uses the exact pure Python path. */
srmech_status_t srmech_genome_modulator_consistent(
    const unsigned char *body, size_t body_len, size_t leaf_dim,
    const unsigned char *expected, size_t expected_len,
    uint64_t candidate_cell_state, int *consistent);

/* §133/v11 (#733) M3 — the COMPLETE inverse of gene_express: emit the BOOLEAN
 * part (the M1 floor + the disjunctive CLAUSES) of the EXACT constraint
 * characterizing the WHOLE set of cell-states consistent with an observed
 * expression. `body` is the GENE-CAP subset (as for srmech_genome_modulator_
 * recover); `expressed` is the observed labels as NUL-delimited UTF-8 tokens.
 * The emitted `out` buffer (caller-arena; `out_cap` bytes; *out_len set to the
 * used length) is the canonical big-endian serialization:
 *   certain_on(u64) certain_off(u64)
 *   n_nand(u32) [any_absent(u64) any_present(u64)]*n_nand
 *   n_or(u32)   [n_terms(u32) [present(u64) absent(u64)]*n_terms]*n_or
 * where certain_on/off is the M1 floor; each nand pair is one boolean AND-term
 * of an UN-expressed E1/E2 gene (in body order, term order — "some activator
 * absent OR some repressor present" = the gene NOT expressing, all ANDed); each
 * or-clause is one EXPRESSED pure-boolean label with >= 2 boolean terms (in
 * first-occurrence label order; a label that ALSO opens a threshold/graded cap is
 * a CROSS-TYPE OR and emits NO or-clause). This is the BOOLEAN scope only — the
 * E4 inequality / E3 level constraints + satisfiability are computed by the
 * Python caller (the owed-C). Byte-identical to the pure Python
 * srmech.amsc.genome._serialize_bool_constraint(_modulator_constraint_bool_pure).
 * Caller-arena; malloc-free; no abs; a READ (never mutates the body).
 * Error returns:
 *   SRMECH_ERR_NULL_ARG  — body(when body_len>0) / expressed(when expressed_len>0)
 *                          / out / out_len is NULL.
 *   SRMECH_ERR_BAD_INPUT  — leaf_dim 0 / > 256, body_len not a multiple of
 *                          leaf_dim, a malformed gene cap, or out_cap too small. */
srmech_status_t srmech_genome_modulator_constraint(
    const unsigned char *body, size_t body_len, size_t leaf_dim,
    const unsigned char *expressed, size_t expressed_len,
    unsigned char *out, size_t out_cap, size_t *out_len);

/* §133/v11 (#733) M3 — does `candidate` satisfy the BOOLEAN part of an emitted M3
 * constraint? `buf` (buf_len bytes) is the canonical serialization
 * srmech_genome_modulator_constraint emits. *satisfied = 1 iff
 * (candidate & certain_on) == certain_on AND (candidate & certain_off) == 0 AND
 * every nand pair holds ((candidate & any_absent) != any_absent OR
 * (candidate & any_present) != 0) AND every or-clause has >= 1 term fully matching
 * ((candidate & present) == present AND (candidate & absent) == 0). The BOOLEAN
 * scope only — the caller ANDs the exact E4/E3 checks (the owed-C). Byte-identical
 * to the pure Python srmech.amsc.genome._satisfies_bool. Malloc-free; no abs; READ.
 * Error returns:
 *   SRMECH_ERR_NULL_ARG  — buf(when buf_len>0) / satisfied is NULL.
 *   SRMECH_ERR_BAD_INPUT  — a truncated / malformed buffer. */
srmech_status_t srmech_genome_modulator_constraint_satisfies(
    const unsigned char *buf, size_t buf_len,
    uint64_t candidate_cell_state, int *satisfied);

/* ------------------------------------------------------------------ *
 * TOML parser (malloc-free; caller arena)
 *
 * A self-contained reader for the TOML subset srmech's descriptor /
 * cascade-catalog files actually use. NOT a full TOML 1.0 parser: it
 * implements exactly the grammar the corpus exercises and rejects the
 * rest with SRMECH_ERR_BAD_INPUT so a silent mis-parse can never slip
 * through (no datetimes — they do not appear in the corpus).
 *
 * Supported grammar:
 *   - tables [a], [a.b.c] (dotted -> nested; reopening a path allowed);
 *   - arrays of tables [[a]], [[a.b]] (each appends a new table);
 *   - key/value: bare or dotted bare keys ([A-Za-z0-9_-]); the value is
 *       basic "..." (escapes \" \\ \n \t \r \uXXXX -> UTF-8),
 *       literal '...', multiline """...""" / '''...''' (leading newline
 *       after the opener trimmed), integer (+/-, underscores), float
 *       (decimal point and/or e/E exponent, underscores), bool
 *       true/false, array [ ... ] (multi-line, trailing comma, nested),
 *       inline table { k = v, ... };
 *   - comments: '#' to end of line, outside strings.
 *
 * Memory model: the WHOLE parse tree (values, key strings, child
 * pointer arrays) is built inside the caller-supplied arena `ws`
 * (ws_len bytes), used as an 8-byte-aligned bump allocator. There is
 * NO malloc and no global state — the parser is reentrant. Strings are
 * copied into the arena NUL-terminated, so srmech_toml_value_t::u.str.ptr
 * is always a C string (the `len` field is the byte length, excluding
 * the NUL). The arena content must outlive any use of *out.
 *
 * NO per-table / per-array element cap (rc159 standalone-complete honor):
 * children are collected into arena linked lists (no fixed staging array),
 * so a single table or array may hold any number of entries the caller arena
 * fits — a C-only / MCU host parses a descriptor bounded only by its RAM.
 * Nesting depth is still bounded by SRMECH_TOML_MAX_DEPTH (a recursion-depth
 * guard, not a problem-size cap) -> SRMECH_ERR_OVERFLOW.
 *
 * ABI-additive: new symbols + types + macros only, so
 * SRMECH_ABI_VERSION stays 3. No libm, no <complex.h>, no malloc.
 * ------------------------------------------------------------------ */

/* Maximum table/array/inline-table nesting depth (recursion guard for
 * the value parser; JPL Rule 2 bound). Exceeding it -> SRMECH_ERR_OVERFLOW. */
#define SRMECH_TOML_MAX_DEPTH 64

/* The dynamic type of a parsed TOML value. */
typedef enum srmech_toml_type {
    SRMECH_TOML_STRING = 0,
    SRMECH_TOML_INT,
    SRMECH_TOML_FLOAT,
    SRMECH_TOML_BOOL,
    SRMECH_TOML_ARRAY,
    SRMECH_TOML_TABLE
} srmech_toml_type_t;

typedef struct srmech_toml_value srmech_toml_value_t;

/* A parsed TOML value. All pointers refer into the caller's arena. For
 * a STRING, `str.ptr` is NUL-terminated and `str.len` is its byte
 * length. For ARRAY / TABLE, the child pointer arrays (`arr.items`,
 * `tbl.keys`, `tbl.vals`) also live in the arena. */
struct srmech_toml_value {
    srmech_toml_type_t type;
    union {
        struct { const char *ptr; uint32_t len; } str;
        int64_t i;
        double  f;
        int     b;
        struct { srmech_toml_value_t **items; uint32_t n; } arr;
        struct {
            const char           **keys;
            srmech_toml_value_t  **vals;
            uint32_t               n;
        } tbl;
    } u;
};

/* Parse src[0..len) into a TOML tree built ENTIRELY inside the caller's
 * arena `ws` (ws_len bytes, used as an 8-byte-aligned bump allocator).
 * On success *out is the root TABLE value (which lives in ws). No malloc.
 *
 * Returns:
 *   SRMECH_OK             — success (*out set)
 *   SRMECH_ERR_NULL_ARG   — src (with len > 0), ws, or out is NULL
 *   SRMECH_ERR_OVERFLOW   — caller arena `ws` too small for this document,
 *                           or nesting exceeds SRMECH_TOML_MAX_DEPTH
 *   SRMECH_ERR_BAD_INPUT  — a syntax error / unsupported construct
 */
srmech_status_t srmech_toml_parse(const char *src, size_t len,
                                  void *ws, size_t ws_len,
                                  srmech_toml_value_t **out);

/* Look up `key` in a TABLE value; returns the matching child value, or
 * NULL if `table`/`key` is NULL, `table` is not a TABLE, or the key is
 * absent. The returned pointer aliases into the same arena as `table`. */
const srmech_toml_value_t *srmech_toml_table_get(
    const srmech_toml_value_t *table, const char *key);

/* ------------------------------------------------------------------ *
 * srmech_bigint — caller-arena arbitrary-precision integer
 *
 * The unbounded-integer foundation that removes the "overflow → fall
 * back to CPython int" gap so the C library is standalone-complete
 * (no GMP, no external bignum, no malloc — JPL Rule 3). A value is
 * carried base-2^32, little-endian, sign-magnitude, over CALLER-OWNED
 * limb storage:
 *
 *   sign  ∈ {-1, 0, +1}   (0 iff the value is zero)
 *   n                       significant limb count, NO leading-zero limbs
 *   cap                     capacity of limbs[] the caller provided
 *   limbs[0]                least-significant 32-bit limb
 *
 * Every op writes into a caller-provided `out` whose limbs[]/cap the
 * caller pre-sizes via the `_bound` helpers (limb counts). If out->cap
 * is too small the op returns SRMECH_ERR_OVERFLOW and never writes past
 * cap. Ops needing scratch take a `void *ws, size_t ws_len` caller arena
 * (an 8-byte-aligned uint32 bump region); too-small → SRMECH_ERR_OVERFLOW.
 *
 * Division / shift use PYTHON FLOOR semantics: q = floor(a / b),
 * r = a − q·b, so 0 <= r < |b| when b > 0 (matches Python divmod and >>).
 * ------------------------------------------------------------------ */
typedef struct srmech_bigint {
    int32_t   sign;    /* -1, 0, or +1 (0 iff n == 0)            */
    uint32_t  n;       /* significant limb count; no leading zero */
    uint32_t  cap;     /* capacity of limbs[] the caller provided */
    uint32_t *limbs;   /* caller-owned; limbs[0] = least sig.     */
} srmech_bigint_t;

/* Bound helpers — the minimum limb count the caller must allocate for
 * each operation's `out`. Each clamps/guards size_t overflow. */
size_t srmech_bigint_add_bound(size_t a_n, size_t b_n);     /* max(a,b)+1     */
size_t srmech_bigint_mul_bound(size_t a_n, size_t b_n);     /* a_n + b_n      */
size_t srmech_bigint_mul_ws_bound(size_t a_n, size_t b_n);  /* Karatsuba BYTES*/
size_t srmech_bigint_shl_bound(size_t a_n, uint32_t bits);  /* a + bits/32 +1 */
size_t srmech_bigint_pow_bound(size_t base_n, uint32_t exp);/* base_n*exp + 1 */
size_t srmech_bigint_pow_ws_bound(size_t base_n, uint32_t exp);/* pow ws BYTES */
size_t srmech_bigint_from_dec_bound(size_t n_digits);       /* n_digits/9 + 2 */
size_t srmech_bigint_to_dec_bound(size_t a_n);              /* a_n*10 + 2     */

/* out = v (a signed 64-bit value). INT64_MIN handled (no negation trap). */
srmech_status_t srmech_bigint_set_i64(srmech_bigint_t *out, int64_t v);

/* out = a (deep limb copy). OVERFLOW if out->cap < a->n. */
srmech_status_t srmech_bigint_copy(srmech_bigint_t *out, const srmech_bigint_t *a);

/* Signed three-way compare: -1 if a < b, 0 if a == b, +1 if a > b. */
int srmech_bigint_cmp(const srmech_bigint_t *a, const srmech_bigint_t *b);

/* 1 iff a is zero, else 0. */
int srmech_bigint_is_zero(const srmech_bigint_t *a);

/* out = a + b (signed). OVERFLOW if out->cap < add_bound(a->n, b->n). */
srmech_status_t srmech_bigint_add(srmech_bigint_t *out, const srmech_bigint_t *a,
                                  const srmech_bigint_t *b);

/* out = a - b (signed). OVERFLOW if out->cap < add_bound(a->n, b->n). */
srmech_status_t srmech_bigint_sub(srmech_bigint_t *out, const srmech_bigint_t *a,
                                  const srmech_bigint_t *b);

/* out = a * b. OVERFLOW if out->cap < mul_bound(a->n, b->n). Since
 * 0.9.0rc168 the multiply is KARATSUBA above a measured limb crossover
 * (schoolbook below): this no-arena entry runs the split over a bounded
 * internal scratch region, degrading gracefully (fewer split levels →
 * ultimately schoolbook) for very large operands. The product is
 * byte-identical to schoolbook for every input — only the speed changes.
 * out must NOT alias a or b (the multiply zeros/rebuilds out's limbs). */
srmech_status_t srmech_bigint_mul(srmech_bigint_t *out, const srmech_bigint_t *a,
                                  const srmech_bigint_t *b);

/* out = a * b over a CALLER scratch arena (the unbounded Karatsuba entry).
 * Size ws via srmech_bigint_mul_ws_bound(a->n, b->n) — BYTES — for the
 * full O(n^log2(3)) split at any operand size (the explicit split-frame
 * stack + every level's sum/middle-term scratch live in ws; JPL Rule 1:
 * no recursion — the schedule is an iterative frame machine; Rule 3: no
 * malloc). A smaller/NULL ws is VALID and still returns the identical
 * product (each split level that does not fit falls back to schoolbook,
 * so ws only tunes speed, never the result). ws should be 8-byte aligned
 * (the shared arena contract); a misaligned ws routes to schoolbook.
 * OVERFLOW iff out->cap < mul_bound(a->n, b->n). out must NOT alias
 * a, b, or ws. */
srmech_status_t srmech_bigint_mul_ws(srmech_bigint_t *out,
                                     const srmech_bigint_t *a,
                                     const srmech_bigint_t *b,
                                     void *ws, size_t ws_len);

/* out = a << bits. OVERFLOW if out->cap < shl_bound(a->n, bits). */
srmech_status_t srmech_bigint_shl_bits(srmech_bigint_t *out,
                                       const srmech_bigint_t *a, uint32_t bits);

/* out = a >> bits, FLOOR (toward -inf) to match Python >>; for a >= 0
 * this is a plain truncating shift. For a < 0 the floor can carry one
 * extra limb, so size out->cap >= a->n + 1 (OVERFLOW otherwise). */
srmech_status_t srmech_bigint_shr_bits(srmech_bigint_t *out,
                                       const srmech_bigint_t *a, uint32_t bits);

/* q = floor(a / b), r = a - q*b (Python FLOOR semantics: 0 <= r < |b|
 * when b > 0). b != 0 else SRMECH_ERR_BAD_INPUT. q or r may be NULL to
 * skip that output — the skipped output's throwaway storage is carved off
 * the front of `ws` (a->n + 2 limbs for q; max(a->n, b->n) + 2 for r), so
 * the NULL contract holds for EVERY input including the negative-dividend
 * floor fixup (pre-fix a cap-0 sink spuriously returned OVERFLOW there).
 * Uses Knuth Algorithm D in the caller arena `ws`. */
srmech_status_t srmech_bigint_divmod(srmech_bigint_t *q, srmech_bigint_t *r,
                                     const srmech_bigint_t *a,
                                     const srmech_bigint_t *b,
                                     void *ws, size_t ws_len);

/* out = floor(sqrt(a)). a >= 0 else SRMECH_ERR_BAD_INPUT. Integer Newton
 * iteration over the caller arena `ws`. OVERFLOW if out->cap too small. */
srmech_status_t srmech_bigint_isqrt(srmech_bigint_t *out, const srmech_bigint_t *a,
                                    void *ws, size_t ws_len);

/* out = gcd(|a|, |b|) >= 0. Caller arena `ws`. 0.9.0rc169: LEHMER'S
 * algorithm (Knuth TAOCP Vol 2 §4.5.2 Algorithm L) when `ws` meets
 * srmech_bigint_gcd_ws_bound — the leading-30-bit-digit cofactor matrix
 * batches ~30 bits of Euclid steps into 4 single-limb multiply-adds, a
 * large constant-factor win over the per-step full-precision divmod; a
 * tighter arena transparently falls back to lean Euclid. The gcd VALUE
 * is unique, so byte-identical either way. */
srmech_status_t srmech_bigint_gcd(srmech_bigint_t *out, const srmech_bigint_t *a,
                                  const srmech_bigint_t *b,
                                  void *ws, size_t ws_len);

/* Workspace BYTES that engage the Lehmer fast path of srmech_bigint_gcd
 * for `a_n`/`b_n`-limb inputs (a smaller arena still returns the identical
 * gcd via the lean-Euclid fallback). 8-byte-aligned uint32 bump arena. */
size_t srmech_bigint_gcd_ws_bound(size_t a_n, size_t b_n);

/* out = base^exp (exp >= 0; exp == 0 -> 1). Binary exponentiation over
 * the caller arena `ws` (>= pow_ws_bound(base->n, exp) BYTES). OVERFLOW if
 * out->cap < pow_bound(base->n, exp) or ws is too small for the running
 * square + raw mul-temp (both sized from base^exp, not a fixed cap). */
srmech_status_t srmech_bigint_pow_u32(srmech_bigint_t *out,
                                      const srmech_bigint_t *base, uint32_t exp,
                                      void *ws, size_t ws_len);

/* out = decimal s[0..len). Optional leading '-'; remaining chars 0-9.
 * OVERFLOW if out->cap < from_dec_bound(len). */
srmech_status_t srmech_bigint_from_dec(srmech_bigint_t *out, const char *s,
                                       size_t len);

/* Write a's decimal expansion (with leading '-' if negative) into buf as a
 * NUL-terminated string; *out_len = strlen (excludes the NUL). Caller arena
 * `ws`. OVERFLOW if buf cap or ws is too small (need to_dec_bound limbs). */
srmech_status_t srmech_bigint_to_dec(const srmech_bigint_t *a, char *buf,
                                     size_t cap, size_t *out_len,
                                     void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_pi — ROTATION-LAST Chudnovsky π (built on srmech_bigint)
 *
 * The canonical srmech cascade shape: keep the body BIT-EXACT (integer
 * add / sub / mul / floor-divmod on the exact bigint substrate) and do
 * the SINGLE continuous/frame projection ONCE, terminally. The body is
 * the Chudnovsky linear series accumulated as exact bigints; the lone
 * terminal rotation is the final isqrt(10005·one²) + one division + a
 * base-10 render. NO float, NO libm, NO per-term square root.
 *
 * Byte-identical to the pure-Python pi_chudnovsky_digits oracle (same
 * fixed-point algorithm, same floor semantics). All limb buffers + the
 * divmod/isqrt scratch are carved from the caller arena `ws`; size it
 * via srmech_pi_chudnovsky_ws_bound(num_digits). Linear term accumulation
 * (NO binary splitting) — JPL Rule 1 no-recursion clean.
 * ------------------------------------------------------------------ */

/* Minimum `ws_len` BYTES the caller must hand srmech_pi_chudnovsky for the
 * requested digit count (covers every bigint limb buffer + the deepest
 * divmod/isqrt scratch). 8-byte-aligned uint32 bump arena. */
size_t srmech_pi_chudnovsky_ws_bound(uint32_t num_digits);

/* Write π to `num_digits` fractional digits as "3." + digits into `out`
 * (NUL-terminated; *out_len = strlen, excludes the NUL). num_digits == 0
 * → "3.". `out_cap` must be >= num_digits + 4. Carves all scratch from the
 * caller arena `ws` (>= srmech_pi_chudnovsky_ws_bound); too-small out_cap
 * or ws → SRMECH_ERR_OVERFLOW. */
srmech_status_t srmech_pi_chudnovsky(uint32_t num_digits, char *out,
                                     size_t out_cap, size_t *out_len,
                                     void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_pi_archimedes — the projects-EVERY-step Pfaff-Archimedes pi
 *
 * The COMPLEMENT of srmech_pi_chudnovsky (rotation-last): Pfaff's 1800
 * reformulation of Archimedes' polygon method as a two-mean chiral pair that
 * brackets pi over a fixed-point unit M = 1 << precision_bits, projecting at
 * EVERY step (one integer isqrt per iteration = the geometric mean):
 *
 *   b0 = 3*M ; a0 = isqrt(12*M*M) ;
 *   a' = (2*a*b)//(a+b) [harmonic, dn] ; b' = isqrt(a'*b) [geometric, up] ;
 *   pi ~ (a+b)//2 -> pi_int = (pi_scaled*10^D)//M -> "3." + D digits.
 *
 * The WHOLE loop runs in C (NO per-step decimal round-trip), so a bare C host
 * computes pi with no Python. Byte-identical to the pure-Python
 * pi_cascade_digits oracle (same fixed-point integers, same Python-FLOOR
 * divmod/shr, same depth/precision). Early-exits at the exact a==b fixed point
 * (a pure speedup, not a result change). All limb buffers + the divmod/isqrt
 * scratch are carved from the caller arena `ws` (no malloc). num_digits == 0
 * -> "3."; out_cap must be >= num_digits + 4. Too-small out_cap or ws, or a
 * zero depth/precision, -> SRMECH_ERR_OVERFLOW / SRMECH_ERR_BAD_INPUT.
 *
 * Carrier-internal (like srmech_pi_chudnovsky): NOT a Rosetta ledger op.
 * ABI-additive: a new symbol, so SRMECH_ABI_VERSION stays 3. */
srmech_status_t srmech_pi_archimedes(uint32_t num_digits,
                                     uint32_t max_cascade_depth,
                                     uint32_t precision_bits,
                                     char *out, size_t out_cap, size_t *out_len,
                                     void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_bigexp — BIGNUM-EXACT Class-N transcendental Taylor truncations
 * (built on srmech_bigint; the standalone-honor closure for the exact-
 * rational series).
 *
 * The int64/Q61 peers in srmech_rational.c (srmech_exp_series_truncate,
 * srmech_rational_pow_uint) cap at int64 and return SRMECH_ERR_OVERFLOW past
 * it, so a C-only host hit a magnitude ceiling the Python bignum path does
 * not. These *_big variants compute the SAME exact rational the Python
 * srmech.amsc.rational.{exp,sin,cos,log1p,atan}_series_truncate /
 * rational_pow_uint compute, over caller-arena srmech_bigint (NO malloc), and
 * return it REDUCED to lowest terms with positive denominator — byte-identical
 * to Python's (num, den) at ANY magnitude.
 *
 * The operand and result rationals are passed as srmech_bigint pairs
 * (x_num / x_den in, out_num / out_den out). out_den is always > 0 and
 * gcd(|out_num|, out_den) == 1. den (x_den / base_den) must be > 0. Each op
 * carves all working carriers + divmod/gcd scratch from the caller arena
 * `ws` (>= srmech_bigexp_ws_bound(num_limbs, den_limbs, num_terms)); too-small
 * `ws` or an `out` whose cap is too small → SRMECH_ERR_OVERFLOW. Out-of-domain
 * arguments (x_den <= 0, num_terms past the per-op cap, |x| > 1 for atan, or
 * x outside (-1, 1] for log1p) → SRMECH_ERR_BAD_INPUT, matching the Python
 * ValueError-domain so C and Python accept the SAME inputs.
 *
 * Carrier-internal (like srmech_pi): NOT a Rosetta ledger op. Additive
 * symbols → SRMECH_ABI_VERSION unchanged.
 * ------------------------------------------------------------------ */

/* Minimum `ws_len` BYTES the caller must hand any *_big op below, for input
 * rationals of `num_limbs` / `den_limbs` significant limbs and the given
 * `num_terms`. Covers every working carrier + the deepest divmod/gcd scratch.
 * 8-byte-aligned uint32 bump arena. */
size_t srmech_bigexp_ws_bound(size_t num_limbs, size_t den_limbs,
                              uint32_t num_terms);

/* exp partial sum S_N(p/q) = Σ_{k=0..N} (p/q)^k / k!. num_terms <= 512. */
srmech_status_t srmech_exp_series_truncate_big(const srmech_bigint_t *x_num,
                                               const srmech_bigint_t *x_den,
                                               uint32_t num_terms,
                                               srmech_bigint_t *out_num,
                                               srmech_bigint_t *out_den,
                                               void *ws, size_t ws_len);

/* sin partial sum Σ_{k=0..N} (-1)^k (p/q)^(2k+1) / (2k+1)!. num_terms <= 50. */
srmech_status_t srmech_sin_series_truncate_big(const srmech_bigint_t *x_num,
                                               const srmech_bigint_t *x_den,
                                               uint32_t num_terms,
                                               srmech_bigint_t *out_num,
                                               srmech_bigint_t *out_den,
                                               void *ws, size_t ws_len);

/* cos partial sum Σ_{k=0..N} (-1)^k (p/q)^(2k) / (2k)!. num_terms <= 50. */
srmech_status_t srmech_cos_series_truncate_big(const srmech_bigint_t *x_num,
                                               const srmech_bigint_t *x_den,
                                               uint32_t num_terms,
                                               srmech_bigint_t *out_num,
                                               srmech_bigint_t *out_den,
                                               void *ws, size_t ws_len);

/* log1p partial sum Σ_{k=1..N} (-1)^(k+1) (p/q)^k / k. Domain -1 < p/q <= 1.
 * num_terms <= 64. */
srmech_status_t srmech_log1p_series_truncate_big(const srmech_bigint_t *x_num,
                                                 const srmech_bigint_t *x_den,
                                                 uint32_t num_terms,
                                                 srmech_bigint_t *out_num,
                                                 srmech_bigint_t *out_den,
                                                 void *ws, size_t ws_len);

/* atan partial sum Σ_{k=0..N} (-1)^k (p/q)^(2k+1) / (2k+1). Domain |p/q| <= 1.
 * num_terms <= 64. */
srmech_status_t srmech_atan_series_truncate_big(const srmech_bigint_t *x_num,
                                                const srmech_bigint_t *x_den,
                                                uint32_t num_terms,
                                                srmech_bigint_t *out_num,
                                                srmech_bigint_t *out_den,
                                                void *ws, size_t ws_len);

/* (p/q)^n = p^n / q^n, reduced. exp_val <= 65535. */
srmech_status_t srmech_rational_pow_uint_big(const srmech_bigint_t *base_num,
                                             const srmech_bigint_t *base_den,
                                             uint32_t exp_val,
                                             srmech_bigint_t *out_num,
                                             srmech_bigint_t *out_den,
                                             void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_the_one — the S(sigma, theta) ADJOINT generator (rc138; #743).
 *
 * The C peer for srmech.amsc.cascade.one.the_one's exact-rational ADJOINT
 * (One.to_flat_rational — the w-INVARIANT 2pi-periodic base). COMPOSES the
 * exact-rational bignum series srmech_cos/sin_series_truncate_big with the fixed
 * Fano-plane block-tiling of the 1+3+7+3 = 14 Hurwitz ladder, producing the SAME
 * 14 exact adjoint rationals (num, den) the Python builds — BYTE-IDENTICAL at ANY
 * magnitude, over caller-arena srmech_bigint (NO float, NO libm, NO malloc). It
 * is w-BLIND (the winding folds away in the adjoint base), the same as Python.
 *
 * sigma in {+1, -1} (the Class-K/C chirality; a sign is applied by negating the
 * sign-magnitude numerator, never abs()). theta_den->sign must be > 0. num_terms
 * <= 50 (the trig-series cap; matches the Python ValueError domain). out_num /
 * out_den are caller-provided arrays of EXACTLY 14 srmech_bigint (order: [R.1, Im]
 * per block, C then H then O). Each out is reduced with positive denominator.
 * Bad sigma / theta_den <= 0 / num_terms > 50 -> SRMECH_ERR_BAD_INPUT; too-small
 * out cap or arena ws (>= srmech_the_one_ws_bound) -> SRMECH_ERR_OVERFLOW.
 *
 * Carrier-internal (like srmech_bigexp): NOT a Rosetta ledger op of its own —
 * it BACKS the existing the_one / one_matrix / to_scalar Python ops. Additive
 * symbol -> SRMECH_ABI_VERSION stays 3.
 * ------------------------------------------------------------------ */

/* Minimum `ws_len` BYTES for theta rationals of the given limb sizes + N.
 * 8-byte-aligned uint32 bump arena (4 cos/sin carriers + the series scratch). */
size_t srmech_the_one_ws_bound(size_t num_limbs, size_t den_limbs,
                               uint32_t num_terms);

/* The 14 exact adjoint rationals of S(sigma, theta_num/theta_den) to N terms. */
srmech_status_t srmech_the_one(int32_t sigma,
                               const srmech_bigint_t *theta_num,
                               const srmech_bigint_t *theta_den,
                               uint32_t num_terms,
                               srmech_bigint_t *out_num,
                               srmech_bigint_t *out_den,
                               void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_jacobi — BIGNUM-EXACT Jacobi elliptic sn/cn/dn Maclaurin truncation
 * (the C peer of srmech.amsc.rational.jacobi_sncndn_series_truncate).
 *
 * The "rotation-last" exact-ℚ sibling of srmech_sin/cos_series_truncate_big:
 * builds the Maclaurin coefficient sequences of the three Jacobi elliptic
 * functions sn/cn/dn from the coupled power-series ODE
 *   sn' = cn·dn, cn' = -sn·dn, dn' = -m·sn·cn ; sn(0)=0, cn(0)=dn(0)=1
 * (Abramowitz & Stegun §16.4), evaluates each at u = u_num/u_den with modulus
 * parameter m = m_num/m_den, and returns the three reduced exact rationals
 * (sn, cn, dn) — byte-identical to the Python triple at ANY magnitude, over
 * caller-arena srmech_bigint (NO malloc). u_den / m_den must be > 0;
 * num_terms <= 50 (else SRMECH_ERR_BAD_INPUT, matching the Python domain).
 * Every out carrier's cap and the arena `ws` (>= srmech_jacobi_sncndn_ws_bound)
 * too small → SRMECH_ERR_OVERFLOW. Additive symbol → ABI unchanged.
 * ------------------------------------------------------------------ */

/* Minimum `ws_len` BYTES for an op with input rationals of the given limb
 * sizes + num_terms. 8-byte-aligned uint32 bump arena. */
size_t srmech_jacobi_sncndn_ws_bound(size_t num_limbs, size_t den_limbs,
                                     size_t m_num_limbs, size_t m_den_limbs,
                                     uint32_t num_terms);

/* sn/cn/dn N-term Maclaurin truncation at u = u_num/u_den, m = m_num/m_den.
 * Each (out_num, out_den) is reduced, gcd == 1, out_den > 0. num_terms <= 50. */
srmech_status_t srmech_jacobi_sncndn(const srmech_bigint_t *u_num,
                                     const srmech_bigint_t *u_den,
                                     const srmech_bigint_t *m_num,
                                     const srmech_bigint_t *m_den,
                                     uint32_t num_terms,
                                     srmech_bigint_t *sn_num,
                                     srmech_bigint_t *sn_den,
                                     srmech_bigint_t *cn_num,
                                     srmech_bigint_t *cn_den,
                                     srmech_bigint_t *dn_num,
                                     srmech_bigint_t *dn_den,
                                     void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_crt_combine / srmech_rational_reconstruct — the CRT closers
 * (srmech 0.9.0rc45, rung 2 of the CRT-QMat re-fibration arc).
 *
 * After the swell-free GF(p) elimination (srmech_gf_rref, rung 1) has produced
 * one residue per reduction prime, these two turn the per-prime residues back
 * into the EXACT rational answer: CRT-combine the residues into one residue
 * modulo the product of the primes, then rational-reconstruct that residue back
 * to a bounded p/q. Both run over the caller-arena srmech_bigint — the combined
 * modulus + the reconstructed numerator/denominator are bignum.
 *
 * Additive symbols — ABI unchanged (stays 3).
 * ------------------------------------------------------------------ */

/* Minimum `ws_len` BYTES for srmech_crt_combine over `k` congruences. The Garner
 * fold's scratch is a few partial-product bigints sized from the running
 * modulus; this is a generous envelope (the actual modulus limb count is data-
 * dependent, so the marshaller pads further). */
size_t srmech_crt_combine_ws_bound(size_t k);

/* CRT-combine `k` congruences r_i (mod m_i) into one residue mod ∏ m_i.
 * `residues` / `moduli` are caller-owned uint64 arrays of length `k` (each
 * residue + modulus fits uint64 — the ~31-bit reduction primes). The moduli
 * must be pairwise coprime (distinct primes; the caller's contract). Writes the
 * combined residue (in [0, modulus)) into *out_residue and ∏ m_i into
 * *out_modulus, both bignum (size their limb cap from the total bit-width).
 * Iterative Garner CRT; the per-step inverse is taken modulo a single uint64
 * prime. SRMECH_ERR_BAD_INPUT if k == 0 or any modulus < 2; SRMECH_ERR_OVERFLOW
 * if an out cap or `ws` is too small. */
srmech_status_t srmech_crt_combine(const uint64_t *residues,
                                   const uint64_t *moduli,
                                   uint32_t k,
                                   srmech_bigint_t *out_residue,
                                   srmech_bigint_t *out_modulus,
                                   void *ws, size_t ws_len);

/* Minimum `ws_len` BYTES for srmech_rational_reconstruct on a modulus of
 * `modulus_limbs` 32-bit limbs. Covers the half-GCD recurrence carriers + the
 * divmod/gcd arena tail. */
size_t srmech_rational_reconstruct_ws_bound(size_t modulus_limbs);

/* Reconstruct the rational p/q congruent to `residue` modulo `modulus`, with
 * |p| <= num_bound, 0 < q <= den_bound, gcd(q, modulus) == 1 and gcd(|p|, q)
 * == 1. residue/modulus/num_bound/den_bound are caller-owned bigints (modulus
 * >= 2; bounds >= 0/1). On success *out_found = 1 and out_num/out_den carry the
 * reduced SIGNED p/q (out_den > 0; the sign is Class-K, an explicit sign-branch,
 * never abs()). If no rational exists in the bounds, *out_found = 0 (out_num/
 * out_den unspecified). Half-GCD / Wang reconstruction over the caller arena
 * `ws`. SRMECH_ERR_BAD_INPUT if modulus < 2; SRMECH_ERR_OVERFLOW on a too-small
 * out cap or `ws`. */
srmech_status_t srmech_rational_reconstruct(const srmech_bigint_t *residue,
                                            const srmech_bigint_t *modulus,
                                            const srmech_bigint_t *num_bound,
                                            const srmech_bigint_t *den_bound,
                                            srmech_bigint_t *out_num,
                                            srmech_bigint_t *out_den,
                                            int32_t *out_found,
                                            void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_poly — EXACT-RATIONAL univariate polynomial over srmech_bigint
 * (the C peer of srmech.amsc.poly.Poly; the §76 telescope Sigma-row prover's
 * foundation carrier).
 *
 * A polynomial is two parallel caller-owned srmech_bigint arrays in ASCENDING
 * degree: nums[i] / dens[i] is the exact-rational coefficient of x^i (dens[i] >
 * 0, gcd(|nums[i]|, dens[i]) == 1; zero coefficient = 0/1). `n` is the
 * coefficient count; the CANONICAL form trims trailing-zero (high-degree)
 * coefficients, so the zero polynomial has n == 0. Each op computes the SAME
 * exact rational coefficients srmech.amsc.poly.Poly computes (Class-N rational
 * arithmetic over Class-J reduction), over caller-arena srmech_bigint (NO
 * malloc), reduced to lowest terms — byte-identical to Python at ANY magnitude
 * (full bignum; no int64/Q61 ceiling).
 *
 * STANDALONE-COMPLETE: every working carrier + the divmod/reduce scratch is
 * carved from the caller arena `ws` (>= the matching srmech_poly_ws_bound), so
 * the bound is the caller's RAM. Out coefficient arrays are caller-owned + must
 * be pre-sized (add/sub: max(na,nb); mul: na+nb-1; divmod: q -> na-nb+1, r ->
 * na; shift: n); each srmech_bigint in those arrays must carry enough limb
 * capacity for the result coefficient (size with srmech_bigint cap >= the
 * per-coeff product bound). Out-of-domain (nb == 0 for divmod) ->
 * SRMECH_ERR_BAD_INPUT; too-small ws or an out coefficient cap ->
 * SRMECH_ERR_OVERFLOW (matching Python's ZeroDivisionError / unbounded-int
 * domains).
 *
 * The single-call polynomial GCD (srmech_poly_gcd, rc39) takes a SEPARATE
 * ws-bound (srmech_poly_gcd_ws_bound) because the Euclidean GCD over Q has the
 * classic intermediate-coefficient growth, so its caller-arena bound scales with
 * the Euclidean-chain length. The soundness lever is MONIC NORMALIZATION after
 * every chain step: the GCD is defined up to a unit, so scaling each remainder
 * to a leading 1 leaves the final monic GCD identical (verified over 4000 random
 * integer+rational trials) while taming the coefficient growth from ~92x input
 * bits (no-norm) to ~23x (monic-norm); poly_gcd_cap_for then sizes each carrier
 * with degree-squared headroom, provably past that linear-in-degree growth. Any
 * residual overflow still returns SRMECH_ERR_OVERFLOW (never a silent wrap), and
 * the Python Poly.gcd falls back to its ceiling-free pure-bigint path.
 *
 * Carrier-internal (like srmech_bigexp): NOT a Rosetta ledger op. Additive
 * symbols -> SRMECH_ABI_VERSION unchanged.
 * ------------------------------------------------------------------ */

/* Minimum `ws_len` BYTES the caller hands any srmech_poly_* op below, for input
 * coefficients of `coeff_limbs` significant limbs and a polynomial of `n_terms`
 * coefficients. Covers every working carrier + the deepest divmod scratch.
 * 8-byte-aligned uint32 bump arena. */
size_t srmech_poly_ws_bound(size_t coeff_limbs, size_t n_terms);

/* out = a + b, coefficientwise exact-Q, trimmed. out arrays hold max(na, nb)
 * coefficients; *out_len <- the trimmed length. */
srmech_status_t srmech_poly_add(const srmech_bigint_t *a_n,
                                const srmech_bigint_t *a_d, size_t na,
                                const srmech_bigint_t *b_n,
                                const srmech_bigint_t *b_d, size_t nb,
                                srmech_bigint_t *out_n, srmech_bigint_t *out_d,
                                size_t *out_len, void *ws, size_t ws_len);

/* out = a - b, coefficientwise exact-Q, trimmed. Same shapes as add. */
srmech_status_t srmech_poly_sub(const srmech_bigint_t *a_n,
                                const srmech_bigint_t *a_d, size_t na,
                                const srmech_bigint_t *b_n,
                                const srmech_bigint_t *b_d, size_t nb,
                                srmech_bigint_t *out_n, srmech_bigint_t *out_d,
                                size_t *out_len, void *ws, size_t ws_len);

/* out = a * b (coefficient convolution), exact-Q, trimmed. out arrays hold
 * na + nb - 1 coefficients (0 when either is the zero polynomial). */
srmech_status_t srmech_poly_mul(const srmech_bigint_t *a_n,
                                const srmech_bigint_t *a_d, size_t na,
                                const srmech_bigint_t *b_n,
                                const srmech_bigint_t *b_d, size_t nb,
                                srmech_bigint_t *out_n, srmech_bigint_t *out_d,
                                size_t *out_len, void *ws, size_t ws_len);

/* (quotient, remainder) of a / b over Q: a == q*b + r, deg r < deg b (or r ==
 * 0). nb == 0 -> SRMECH_ERR_BAD_INPUT. out_q arrays hold na-nb+1 coefficients
 * (0 when na < nb); out_r arrays hold na (the working remainder width).
 * *out_qn / *out_rn <- the trimmed lengths. */
srmech_status_t srmech_poly_divmod(const srmech_bigint_t *a_n,
                                   const srmech_bigint_t *a_d, size_t na,
                                   const srmech_bigint_t *b_n,
                                   const srmech_bigint_t *b_d, size_t nb,
                                   srmech_bigint_t *out_q_n,
                                   srmech_bigint_t *out_q_d, size_t *out_qn,
                                   srmech_bigint_t *out_r_n,
                                   srmech_bigint_t *out_r_d, size_t *out_rn,
                                   void *ws, size_t ws_len);

/* Minimum `ws_len` BYTES for srmech_poly_gcd (a SEPARATE, larger bound than
 * srmech_poly_ws_bound — covers the chain-scaled carriers + three working poly
 * buffers + the divmod scratch). 8-byte-aligned uint32 bump arena. */
size_t srmech_poly_gcd_ws_bound(size_t coeff_limbs, size_t n_terms);

/* gcd = the MONIC Euclidean GCD of a and b over Q (leading coefficient 1, so
 * canonical). out arrays hold max(na, nb) coefficients (the GCD degree never
 * exceeds min(deg a, deg b)); *out_len <- the trimmed monic-GCD length.
 * gcd(0, 0) -> the zero polynomial (out_len 0); gcd(p, 0) -> monic(p). Exact
 * over Q, bignum; OVERFLOW if ws or an out coefficient cap is too small. */
srmech_status_t srmech_poly_gcd(const srmech_bigint_t *a_n,
                                const srmech_bigint_t *a_d, size_t na,
                                const srmech_bigint_t *b_n,
                                const srmech_bigint_t *b_d, size_t nb,
                                srmech_bigint_t *out_n, srmech_bigint_t *out_d,
                                size_t *out_len, void *ws, size_t ws_len);

/* p(x) at x = x_n/x_d by exact Horner -> one reduced rational out_num/out_den. */
srmech_status_t srmech_poly_eval(const srmech_bigint_t *p_n,
                                 const srmech_bigint_t *p_d, size_t n,
                                 const srmech_bigint_t *x_n,
                                 const srmech_bigint_t *x_d,
                                 srmech_bigint_t *out_num,
                                 srmech_bigint_t *out_den,
                                 void *ws, size_t ws_len);

/* p(x + h) (the dispersion shift) by exact synthetic Horner on (x + h). acc
 * arrays hold n coefficients; *acc_len <- the trimmed length. */
srmech_status_t srmech_poly_shift(const srmech_bigint_t *p_n,
                                  const srmech_bigint_t *p_d, size_t n,
                                  const srmech_bigint_t *h_n,
                                  const srmech_bigint_t *h_d,
                                  srmech_bigint_t *acc_n,
                                  srmech_bigint_t *acc_d, size_t *acc_len,
                                  void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_factor_squarefree_primitive — EXACT integer-polynomial factorization
 * (Zassenhaus): the C peer of the Zassenhaus core of
 * srmech.amsc.cascade.matrix_cascades.factor_integer_poly (Qalg TAIL Batch 8).
 *
 * Factors a SQUARE-FREE PRIMITIVE integer polynomial (coeffs low->high, content
 * 1, POSITIVE leading coefficient, deg >= 1) into its irreducible ℤ factors:
 * choose a prime p ∤ lead with the input square-free mod p; factor mod p in
 * 𝔽_p[x] (distinct-degree then Cantor–Zassenhaus equal-degree, over a
 * DETERMINISTIC xorshift64 rng that reproduces the Python rng stream
 * byte-for-byte); Hensel-lift to mod p^k >= 2·B+1 (B the Mignotte bound); then
 * recombine over increasing subset sizes (exact ℤ trial-division), guarded by a
 * subset-size cap. Byte/structurally-identical to the pure
 * _factor_square_free_primitive (the factorization is unique).
 *
 * coeffs / ncoeff : the input integer coefficients low->high (denominator 1).
 * out_coeffs      : the irreducible factors' coefficients CONCATENATED low->high
 *                   (>= 2*deg srmech_bigint slots, each cap >= the out_cap).
 * out_degs        : out_degs[j] = degree of factor j (>= deg int slots).
 * out_nfac        : *out_nfac <- the factor count.
 * out_hit_cap     : *out_hit_cap <- 1 if the recombination subset cap was hit.
 * ws, ws_len      : caller arena (>= srmech_factor_squarefree_primitive_ws_bound).
 *
 * Returns SRMECH_OK; SRMECH_ERR_OVERFLOW on arena/degree overflow (caller falls
 * back to the pure path); SRMECH_ERR_BAD_INPUT on the zero polynomial or no good
 * reduction prime below 100000.
 *
 * All exact srmech_bigint (NO malloc, JPL Rule 3). Additive symbols -> ABI 3. */
size_t srmech_factor_squarefree_primitive_out_cap(size_t coeff_limbs, int deg);
size_t srmech_factor_squarefree_primitive_ws_bound(size_t coeff_limbs, int deg);
srmech_status_t srmech_factor_squarefree_primitive(
    const srmech_bigint_t *coeffs, int ncoeff, srmech_bigint_t *out_coeffs,
    int *out_degs, int *out_nfac, int *out_hit_cap, void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_factor_integer_poly — the FULL factor_integer_poly composite (the
 * everything-mirrors completion of the rc165 Zassenhaus core): content +
 * primitive part, Yun square-free decomposition over exact ℚ (composed from
 * srmech_poly_gcd / srmech_poly_divmod / srmech_poly_sub + an exact-ℚ
 * derivative), per square-free part the Zassenhaus core
 * srmech_factor_squarefree_primitive, merge-identical factors, and the
 * (len, coeffs) sort — so a bare-C host factors an integer polynomial into
 * its irreducible (factor, multiplicity) list with ONE call, byte-identical
 * to the Python factor_integer_poly (same factors, multiplicities, ORDER).
 *
 * coeffs / ncoeff : the input integer coefficients low->high (denominator 1).
 * out_coeffs      : the sorted factors' coefficients CONCATENATED low->high
 *                   (>= 2*deg + 2 srmech_bigint slots, each cap >= the out_cap).
 * out_degs        : out_degs[j] = degree of factor j (>= deg int slots).
 * out_mults       : out_mults[j] = multiplicity of factor j (>= deg int slots).
 * out_nfac        : *out_nfac <- the factor count (0 for a nonzero constant).
 * out_capped      : *out_capped <- 1 if any part hit the recombination cap.
 * ws, ws_len      : caller arena (>= srmech_factor_integer_poly_ws_bound).
 *
 * Returns SRMECH_OK; SRMECH_ERR_BAD_INPUT on the zero polynomial;
 * SRMECH_ERR_OVERFLOW on arena/degree overflow OR an internal multiply-back
 * self-check mismatch (the Python wrapper then falls back to the
 * byte-identical pure path — never a silently wrong answer).
 *
 * All exact srmech_bigint (NO malloc, JPL Rule 3). Additive symbols -> ABI 3. */
size_t srmech_factor_integer_poly_out_cap(size_t coeff_limbs, int deg);
size_t srmech_factor_integer_poly_ws_bound(size_t coeff_limbs, int deg);
srmech_status_t srmech_factor_integer_poly(
    const srmech_bigint_t *coeffs, int ncoeff, srmech_bigint_t *out_coeffs,
    int *out_degs, int *out_mults, int *out_nfac, int *out_capped,
    void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_unary_theta — the EXACT-INTEGER q-series of a UNARY THETA SERIES (the
 * C peer of srmech.amsc.unary_theta.UnaryTheta; the first WEIGHT-GRADED operand
 * carrier). A unary theta is g(tau) = SUM_{n in support} chi(n)*n^j*q^{(a*n^2+
 * b*n)/D}; its WEIGHT is 1/2 + j (that rational lives in the Python Q carrier —
 * the C computes only the integer q-series). This op returns the EXACT INTEGER
 * coefficients out[e] = SUM_{n:E(n)=e} chi(n)*n^j (e = 0..N) after factoring out
 * the leading (minimal) q-power over the support — byte-identical to the Python
 * carrier (n^j is full srmech_bigint, no int64 ceiling). chi(n) in {-1,0,1} via
 * the length-`modulus` chi_table (Class-K sign, never abs). support: 0=all
 * (n in Z), 1=positive (n>=1), 2=nonneg (n>=0).
 *
 * Carrier-internal (like srmech_poly): NOT a Rosetta ledger op; additive symbols
 * -> ABI unchanged (stays 3). The working n^j carriers + pow scratch are carved
 * from the caller arena `ws` (>= srmech_unary_theta_ws_bound). The out[] array
 * is caller-owned (N+1 srmech_bigint, each pre-bound to >= coeff_limbs limbs).
 * ------------------------------------------------------------------ */

/* Minimum `ws_len` BYTES for srmech_unary_theta_q_series (the nj/nbase carriers
 * at `coeff_limbs` width + the bigint pow scratch for |n|^j). */
size_t srmech_unary_theta_ws_bound(uint32_t j, size_t coeff_limbs);

/* The exact integer q-series: out[e] (e=0..N) <- SUM_{n:E(n)=e} chi(n)*n^j,
 * *out_len <- N+1. SRMECH_ERR_BAD_INPUT on modulus<1 / a<=0 / D<1 / empty
 * support; SRMECH_ERR_OVERFLOW if a coefficient or the arena is too small. */
srmech_status_t srmech_unary_theta_q_series(
    uint32_t modulus, const int32_t *chi_table, uint32_t j,
    int64_t a, int64_t b, uint32_t D, int support, size_t N,
    srmech_bigint_t *out, size_t *out_len, void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_eta_quotient — the EXACT-INTEGER q-series of a DEDEKIND-ETA QUOTIENT
 * (the C peer of srmech.amsc.eta_quotient.EtaQuotient; a WEIGHT-axis operand
 * carrier). Q(tau) = PROD_{d|N} eta(d tau)^{r_d} = q^{(SUM_d d r_d)/24} *
 * PROD_d PROD_{m>=1}(1 - q^{dm})^{r_d}. This op returns the EXACT INTEGER
 * coefficients out[e] (e = 0..n_terms-1) of the power series AFTER the leading
 * fractional q-power factor-out — byte-identical to the Python carrier (the
 * coefficients GROW, e.g. the Ramanujan tau, so out[e] is full srmech_bigint,
 * no int64 ceiling). The product is built factor by factor: r_d>0 multiplies by
 * (1-q^{dm}) (a backward subtract-shift), r_d<0 divides (a forward add-shift, the
 * geometric expansion) — the Class-K sign branch chooses, never an ALU abs().
 *
 * Carrier-internal (like srmech_poly / srmech_unary_theta): NOT a Rosetta ledger
 * op; additive symbols -> ABI unchanged (stays 3). The ONE scratch bigint is
 * carved from the caller arena `ws` (>= srmech_eta_quotient_ws_bound); the out[]
 * array is caller-owned (n_terms srmech_bigint, each pre-bound to >= coeff_limbs
 * limbs). The Ligozat / order-at-cusp DECISION logic stays Python-only.
 * ------------------------------------------------------------------ */

/* Minimum `ws_len` BYTES for srmech_eta_quotient_qseries (ONE scratch bigint at
 * `coeff_limbs` width + slack; every step is a bigint add/sub on a copy). */
size_t srmech_eta_quotient_ws_bound(size_t coeff_limbs);

/* The exact integer q-series of PROD_d PROD_{m>=1}(1 - q^{dm})^{r_d}: out[e]
 * (e = 0..n_terms-1) <- the coefficient of q^e, *out_len <- n_terms. ds[i]>=1 /
 * rs[i]!=0 are the n_factors factors. SRMECH_ERR_BAD_INPUT on n_terms<1 /
 * n_factors<1 / a bad d or r; SRMECH_ERR_OVERFLOW if a coefficient or the arena
 * is too small. */
srmech_status_t srmech_eta_quotient_qseries(
    const int64_t *ds, const int64_t *rs, size_t n_factors, size_t n_terms,
    srmech_bigint_t *out, size_t *out_len, void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_eisenstein — the EXACT-RATIONAL q-series of a normalized EISENSTEIN
 * SERIES E_k (the C peer of srmech.amsc.eisenstein.Eisenstein; the SECOND rung
 * of the WEIGHT axis, after the rc82 eta-quotient). For even weight k >= 4,
 *     E_k(tau) = 1 - (2k / B_k) * SUM_{n>=1} sigma_{k-1}(n) q^n,
 * with B_k the k-th Bernoulli number (an EXACT RATIONAL: B_4=-1/30, B_6=1/42,
 * B_12=-691/2730) and sigma_{k-1}(n) = SUM_{d|n} d^{k-1}. This op returns each
 * coefficient as a REDUCED (num, den) pair of full srmech_bigint — byte-identical
 * to the Python carrier (NO int64 ceiling; the genuine rational case k=12 ->
 * 65520/691 IS covered, not just integer-coeff k). B_k is computed exact-Q by the
 * standard recurrence over a caller-arena Bernoulli rational roster; sigma is
 * exact-integer; the coefficient is pref*sigma reduced to lowest terms (the
 * Class-N rational arithmetic of srmech_poly / srmech_rational). Only bigint
 * add/sub/mul/divmod/gcd/pow — the sign is the Class-K pin-slot, never ALU abs().
 *
 * Carrier-internal (like srmech_poly / srmech_eta_quotient): NOT a Rosetta ledger
 * op; additive symbols -> ABI unchanged (stays 3). The working carriers + the
 * Bernoulli roster + the divmod/gcd/pow scratch are carved from the caller arena
 * `ws` (>= srmech_eisenstein_ws_bound); the out_num[]/out_den[] arrays are
 * caller-owned (n_terms srmech_bigint each, >= coeff_limbs limbs). The
 * is_modular / quasimodular-boundary DECISION logic stays Python-only.
 * ------------------------------------------------------------------ */

/* Minimum `ws_len` BYTES for srmech_eisenstein_qseries (the working carriers + the
 * (k+1) Bernoulli rational roster headers+limbs + a divmod/gcd/pow scratch tail,
 * all at `coeff_limbs` width). */
size_t srmech_eisenstein_ws_bound(size_t coeff_limbs, size_t k);

/* The exact-rational q-series of E_k = 1 - (2k/B_k) SUM sigma_{k-1}(n) q^n:
 * out_num[e]/out_den[e] (e = 0..n_terms-1) <- the REDUCED coefficient of q^e
 * (out_num[0]/out_den[0] = 1/1), *out_len <- n_terms. k must be EVEN >= 2: k>=4 is
 * the modular E_k; k=2 is the QUASIMODULAR E_2 branch (E_2 = 1 - 24 SUM sigma_1(n)
 * q^n; same formula at k=2, pref -4/B_2 = -24 — the modularity DECISION stays
 * Python-side: the Eisenstein(k) carrier still rejects k=2, E_2 enters only via
 * srmech.amsc.quasimodular_forms_ring). SRMECH_ERR_BAD_INPUT on n_terms<1 / k<2 /
 * k odd / a NULL pointer; SRMECH_ERR_OVERFLOW if a coefficient or the arena is too
 * small. */
srmech_status_t srmech_eisenstein_qseries(
    size_t k, size_t n_terms, srmech_bigint_t *out_num, srmech_bigint_t *out_den,
    size_t *out_len, void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_modular_forms_ring_represent — the EXACT-rational level-1 C[E4,E6]
 * MODULAR-FORMS-RING MEMBERSHIP DECISION (the C peer of
 * srmech.amsc.modular_forms_ring.ModularFormsRing.represent; the THIRD rung of the
 * WEIGHT axis, after the rc82 eta-quotient + rc83 Eisenstein). The structure
 * theorem M_*(SL2(Z)) = C[E4,E6] made executable: every level-1 weight-k modular
 * form is a UNIQUE exact-Q polynomial in E4,E6. Given a claimed weight-k q-series
 * f, this op enumerates the weight-k monomial basis {(a,b): 4a+6b=k}, builds each
 * column E4^a E6^b (the rc83 srmech_eisenstein_qseries for E4/E6 + an exact-Q
 * truncated convolution), solves the square leading-d-rows subsystem A x = b by
 * dispatching to the PUBLIC srmech_qmat_solve (exact Gauss-Jordan over bignum-Q —
 * reuse, not reimplement), VERIFIES the candidate reproduces EVERY provided term,
 * and returns the reduced (num, den) rep coefficients with *out_has = 1, or
 * *out_has = 0 (a non-modular series, or the honest LEVEL-axis OPEN of a
 * higher-level form). REDUCER (unlike the carrier q-series peers): a Rosetta ledger
 * op (c_dispatched). Additive symbols -> ABI unchanged (stays 3). The working
 * carriers + the E4/E6 q-series + the monomial columns + the qmat marshalling are
 * carved from the caller arena `ws` (>= srmech_modular_forms_ring_represent_ws_
 * bound); out_num[]/out_den[] are caller-owned (>= mfr_dim(k) srmech_bigint each,
 * >= srmech_modular_forms_ring_entry_cap limbs). Sign is the Class-K pin-slot,
 * never ALU abs().
 * ------------------------------------------------------------------ */

/* Minimum `ws_len` BYTES for srmech_modular_forms_ring_represent (the working
 * carriers + the E4/E6 q-series rosters + the d monomial columns + the qmat
 * marshalling + the qmat working arena, at `coeff_limbs` width over n_terms terms
 * and a weight-k basis). */
size_t srmech_modular_forms_ring_represent_ws_bound(size_t coeff_limbs,
                                                    size_t n_terms, size_t k);

/* The per-entry limb cap the caller must give each srmech_bigint in the OUTPUT rep
 * arrays (so a reduced result entry never overflows its slot before the op's guard
 * fires). */
size_t srmech_modular_forms_ring_entry_cap(size_t coeff_limbs, size_t n_terms,
                                           size_t k);

/* The level-1 modular-forms-ring membership decision. k is the (even >= 0) claimed
 * weight; f_n[i]/f_d[i] (i = 0..n_terms-1) the reduced claimed q-series. On a
 * representable form: *out_has = 1 and out_num[j]/out_den[j] (j = 0..mfr_dim(k)-1)
 * are the reduced rep coefficients of E4^a E6^b (monomial order, ascending a). On a
 * non-form / higher-level form: *out_has = 0 (out_* unspecified).
 * SRMECH_ERR_BAD_INPUT on n_terms < mfr_dim(k)+2 / a NULL pointer / mfr_dim(k) >
 * the internal MFR_MAX_DIM; SRMECH_ERR_OVERFLOW on an arena shortfall. */
srmech_status_t srmech_modular_forms_ring_represent(
    size_t k, const srmech_bigint_t *f_n, const srmech_bigint_t *f_d,
    size_t n_terms, srmech_bigint_t *out_num, srmech_bigint_t *out_den,
    size_t *out_has, void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_quasimodular_forms_ring_represent — the EXACT-rational level-1 C[E2,E4,E6]
 * QUASIMODULAR-forms-ring MEMBERSHIP DECISION (the C peer of
 * srmech.amsc.quasimodular_forms_ring.QuasiModularFormsRing.represent; the FOURTH
 * rung of the WEIGHT axis, after the rc82 eta-quotient + rc83 Eisenstein + rc84
 * ModularFormsRing). Kaneko-Zagier M~_*(SL2(Z)) = C[E2,E4,E6] made executable:
 * every level-1 weight-k quasimodular form is a UNIQUE exact-Q polynomial in
 * E2,E4,E6. Given a claimed weight-k q-series f, this op enumerates the weight-k
 * monomial basis {(a,b,c): 2a+4b+6c=k}, builds each column E2^a E4^b E6^c (the rc83
 * srmech_eisenstein_qseries — k=2 for E2 via its quasimodular branch, k=4/6 for
 * E4/E6 — + an exact-Q truncated convolution), solves the square leading-d-rows
 * subsystem A x = b by dispatching to the PUBLIC srmech_qmat_solve (exact
 * Gauss-Jordan over bignum-Q — reuse, not reimplement), VERIFIES the candidate
 * reproduces EVERY provided term, and returns the reduced (num, den) rep
 * coefficients with *out_has = 1, or *out_has = 0 (a non-quasimodular series). The
 * rc84 modular ring C[E4,E6] is the a=0 subring; this ring genuinely EXTENDS it
 * (E2^2 @4 -> {(2,0,0):1}, NOT in C[E4,E6]). REDUCER (like
 * srmech_modular_forms_ring_represent): a Rosetta ledger op (c_dispatched).
 * Additive symbols -> ABI unchanged (stays 3). The working carriers + the E2/E4/E6
 * q-series + the monomial columns + the qmat marshalling are carved from the caller
 * arena `ws` (>= srmech_quasimodular_forms_ring_represent_ws_bound); out_num[]/
 * out_den[] are caller-owned (>= qmfr_dim(k) srmech_bigint each, >=
 * srmech_quasimodular_forms_ring_entry_cap limbs). Sign is the Class-K pin-slot,
 * never ALU abs().
 * ------------------------------------------------------------------ */

/* Minimum `ws_len` BYTES for srmech_quasimodular_forms_ring_represent (the working
 * carriers + the E2/E4/E6 q-series rosters + the d monomial columns + the qmat
 * marshalling + the qmat working arena, at `coeff_limbs` width over n_terms terms
 * and a weight-k basis). */
size_t srmech_quasimodular_forms_ring_represent_ws_bound(size_t coeff_limbs,
                                                         size_t n_terms, size_t k);

/* The per-entry limb cap the caller must give each srmech_bigint in the OUTPUT rep
 * arrays (so a reduced result entry never overflows its slot before the op's guard
 * fires). */
size_t srmech_quasimodular_forms_ring_entry_cap(size_t coeff_limbs, size_t n_terms,
                                                size_t k);

/* The level-1 quasimodular-forms-ring membership decision. k is the (even >= 0)
 * claimed weight; f_n[i]/f_d[i] (i = 0..n_terms-1) the reduced claimed q-series. On
 * a representable form: *out_has = 1 and out_num[j]/out_den[j] (j = 0..qmfr_dim(k)-1)
 * are the reduced rep coefficients of E2^a E4^b E6^c (monomial order, ascending a
 * then b). On a non-form: *out_has = 0 (out_* unspecified). SRMECH_ERR_BAD_INPUT on
 * n_terms < qmfr_dim(k)+2 / a NULL pointer / qmfr_dim(k) > the internal
 * QMFR_MAX_DIM; SRMECH_ERR_OVERFLOW on an arena shortfall. */
srmech_status_t srmech_quasimodular_forms_ring_represent(
    size_t k, const srmech_bigint_t *f_n, const srmech_bigint_t *f_d,
    size_t n_terms, srmech_bigint_t *out_num, srmech_bigint_t *out_den,
    size_t *out_has, void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_harmonic_maass — the EXACT-INTEGER q-series of the HOLOMORPHIC mock part
 * of a HARMONIC (weak) MAASS form (the C peer of
 * srmech.amsc.harmonic_maass.HarmonicMaass / MockQSeries; the PAIR carrier that
 * makes research item #9 a finite exact object). A harmonic Maass form f of
 * weight k is determined by the pair (f+ holomorphic mock part, g = xi_k(f)
 * shadow); the non-holomorphic completion f- is the Eichler integral of the
 * shadow, recoverable not stored (Bruinier-Funke, arXiv:math/0212286v4, Prop.
 * 3.2). The shadow q-series rides the EXISTING srmech_unary_theta peer; this op
 * mirrors the genuinely-new HOLOMORPHIC computation — Ramanujan's order-3 mock
 * theta (Zagier, Asterisque 326 (2009), p. 145, Eulerian series)
 *     f(q) = SUM_{n>=0} q^{n^2} / PROD_{j=1}^n (1+q^j)^2 .
 * Returns the EXACT INTEGER coefficients out[e] (e=0..N) of f(q) to depth N
 * (leading power 0), byte-identical to the Python carrier (each out[e] a full
 * srmech_bigint, no int64 ceiling). Built over exact integer power-series algebra
 * (truncated product + integer-series reciprocal + q^{n^2} shift); the sign is
 * the Class-K pin-slot (the reciprocal recurrence's subtraction), never abs().
 *
 * Carrier-internal (like srmech_poly / srmech_unary_theta): NOT a Rosetta ledger
 * op; additive symbols -> ABI unchanged (stays 3). The working power-series cell
 * banks + temps are carved from the caller arena `ws` (>=
 * srmech_harmonic_maass_ws_bound). The out[] array is caller-owned (N+1
 * srmech_bigint, each pre-bound to >= coeff_limbs limbs).
 * ------------------------------------------------------------------ */

/* Minimum `ws_len` BYTES for srmech_harmonic_maass_hol_q_series (the prod/invp/
 * factor power-series cell banks at `coeff_limbs` width + the mul/accumulate
 * temps). */
size_t srmech_harmonic_maass_ws_bound(size_t N, size_t coeff_limbs);

/* The exact integer q-series of f(q) (the order-3 mock theta holomorphic part):
 * out[e] (e=0..N) <- the coefficient of q^e, *out_len <- N+1.
 * SRMECH_ERR_OVERFLOW if a coefficient or the arena is too small. */
srmech_status_t srmech_harmonic_maass_hol_q_series(
    size_t N, srmech_bigint_t *out, size_t *out_len, void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_riemann_theta — the EXACT-INTEGER (A, B, C) EXPONENT LATTICE of a
 * GENUS-2 RIEMANN THETA-CONSTANT (the C peer of
 * srmech.amsc.riemann_theta.RiemannTheta; the FIRST RUNG of the GENUS axis). The
 * genus-2 theta-constant theta[ep'; e](0|Omega) (Grushevsky arXiv:1009.0369 eq.1;
 * Eilers arXiv:1707.08855 eq.1.2; binary characteristic [ep1,ep2; e1,e2], bits in
 * {0,1}) is a lattice sum over n in Z^2 of (-1)^{e.n} q1^{m1^2} q2^{m2^2}
 * q12^{m1 m2}, m_i = n_i + ep'_i/2. Cleared to the quarter-nome base
 * (Q1,Q2,Q12)=(q1,q2,q12)^{1/4} a term is Q1^A Q2^B Q12^C * (-1)^{e.n} with EXACT
 * INTEGER exponents A=(2n1+ep1)^2, B=(2n2+ep2)^2, C=(2n1+ep1)(2n2+ep2) (C = the
 * cross-term, the genus-2 denominator-4 clearing the genus-1 unary-theta never
 * saw). The lower characteristic e gives the per-term sign (-1)^{e.n} (Class-K
 * pin-slot, never abs). This op emits the lattice as a flat caller-owned int64
 * array of [A,B,C,sign] QUADRUPLES (one per lattice point |n_i| <= box, row-major
 * (n1,n2)); the genus-2 theta-CONSTANT coefficients are small +-1 lattice counts
 * (int64-exact, no bignum), and the caller accumulates the quadruples into the
 * canonical {(A,B,C):coeff} lattice (byte-identical to the Python carrier).
 *
 * Caller-owned out[] (like srmech_poly / srmech_unary_theta); no malloc. Additive
 * symbols -> ABI unchanged (stays 3).
 * ------------------------------------------------------------------ */

/* The number of int64 a box needs: (2*box+1)^2 lattice points * 4 (A,B,C,sign). */
size_t srmech_riemann_theta_count(uint32_t box);

/* Emit the [A,B,C,sign] quadruple lattice for characteristic [ep1,ep2; e1,e2]
 * (bits in {0,1}) over |n_i| <= box, into the caller out[] (out_cap int64);
 * *out_len <- the number of int64 written (= srmech_riemann_theta_count).
 * SRMECH_ERR_BAD_INPUT if any bit is not in {0,1}; SRMECH_ERR_OVERFLOW if out[]
 * is too small. */
srmech_status_t srmech_riemann_theta_lattice(
    int ep1, int ep2, int e1, int e2, uint32_t box,
    int64_t *out, size_t out_cap, size_t *out_len);

/* ------------------------------------------------------------------ *
 * rc87: EXACT theta evaluation at a RATIONAL argument (the genus-axis
 * Fay-trisecant / KP-Hirota verifier FOUNDATION). C peers of
 * RiemannTheta.theta_at (g2) + RiemannThetaG3.theta_at (g3).
 *
 * theta at a RATIONAL argument z = z_num/z_den (z_den even = 2N) is exactly
 * representable: the extra Fourier factor exp(2 pi i (n+ep'/2).z) of each lattice
 * point is a ROOT OF UNITY zeta_m^{e}, m = 2*z_den, e = SUM_i (2n_i+ep'_i) z_num_i --
 * an exact element of the cyclotomic ring Z[zeta_m] (NO transcendental eval). These
 * peers emit, per lattice point |n_i| <= box, the SAME (A,B,C[...]) quarter-nome
 * exponents as the lattice peer PLUS the phase exponent e_mod = e mod m (in [0,m), a
 * Class-I cyclic reduction) PLUS the Class-K sign (-1)^{e.n}: a [A,B,C,e_mod,sign]
 * QUINTUPLE (g2) / [A1,A2,A3,C12,C13,C23,e_mod,sign] OCTUPLE (g3). The Python
 * marshaller accumulates sign*zeta_m^{e_mod} into the canonical cyclotomic lattice by
 * reusing the rc29 exact-DFT cyclotomic power basis (srmech.amsc.cascade.exact_dft) --
 * byte-identical to the pure-Python theta_at. Caller-owned out[] (no malloc), like the
 * lattice peer; all exact integer, no float, no abs(). Additive symbols -> ABI
 * unchanged (stays 3).
 * ------------------------------------------------------------------ */

/* The number of int64 a box needs for the genus-2 theta_at lattice: (2*box+1)^2
 * points * 5 [A,B,C,e_mod,sign]. */
size_t srmech_riemann_theta_at_count(uint32_t box);

/* Emit the genus-2 theta_at [A,B,C,e_mod,sign] quintuple lattice for characteristic
 * [ep1,ep2; e1,e2] (bits in {0,1}) at rational z=(z1,z2)/z_den, m = 2*z_den (>= 2),
 * over |n_i| <= box, into the caller out[] (out_cap int64); *out_len <- the number of
 * int64 written (= srmech_riemann_theta_at_count). SRMECH_ERR_BAD_INPUT if a bit is
 * not in {0,1} or m < 2; SRMECH_ERR_OVERFLOW if out[] is too small. */
srmech_status_t srmech_riemann_theta_at(
    int ep1, int ep2, int e1, int e2,
    int64_t z1, int64_t z2, int64_t m, uint32_t box,
    int64_t *out, size_t out_cap, size_t *out_len);

/* The number of int64 a box needs for the genus-3 theta_at lattice: (2*box+1)^3
 * points * 8 [A1,A2,A3,C12,C13,C23,e_mod,sign]. */
size_t srmech_riemann_theta_g3_at_count(uint32_t box);

/* Emit the genus-3 theta_at [A1,A2,A3,C12,C13,C23,e_mod,sign] octuple lattice for
 * characteristic [ep1,ep2,ep3; e1,e2,e3] (bits in {0,1}) at rational
 * z=(z1,z2,z3)/z_den, m = 2*z_den (>= 2), over |n_i| <= box. SRMECH_ERR_BAD_INPUT if a
 * bit is not in {0,1} or m < 2; SRMECH_ERR_OVERFLOW if out[] is too small. */
srmech_status_t srmech_riemann_theta_g3_at(
    int ep1, int ep2, int ep3, int e1, int e2, int e3,
    int64_t z1, int64_t z2, int64_t z3, int64_t m, uint32_t box,
    int64_t *out, size_t out_cap, size_t *out_len);

/* ------------------------------------------------------------------ *
 * rc88: srmech_riemann_theta_cyc_mul -- the EXACT Z[zeta_m] power-basis MULTIPLY, the
 * genuinely-new exact-integer kernel behind the genus-axis Fay / Hirota bilinear
 * VERIFIER (RiemannTheta.addition_holds_at / RiemannThetaG3.addition_holds_at: Riemann's
 * theta ADDITION FORMULA in second-order theta functions -- Igusa, Theta Functions
 * (1972) Ch. IV; Mumford, Tata Lectures on Theta I (1983) Ch. II). The rc87 theta_at
 * gives theta at a rational argument as a {key: Z[zeta_m] coeff} lattice; the verifier's
 * bilinear product multiplies the cyclotomic COEFFICIENTS (this kernel) and convolves the
 * integer exponent keys (caller bookkeeping -- the rc73 addition / rc74 Goepel gate
 * precedent). out[deg] <- a[deg]*b[deg] in Z[zeta_m]: (sum_i a_i z^i)(sum_j b_j z^j) =
 * sum_ij a_i b_j z^{i+j}, each z^{i+j} reduced to the power basis via the REUSED rc29
 * exact-DFT reduction table (table[j*deg + k] = coeff k of zeta_m^j, j in [0,m),
 * deg = phi(m)); byte-identical to the pure-Python _cyc_mul_py. Pure integer (no float,
 * no abs, no malloc, no goto); int64 fast path GUARDS per-coefficient magnitude (a
 * Class-K sign-branch range read) -> SRMECH_ERR_OVERFLOW makes the caller run the pure
 * bignum path. out[] MUST NOT alias a or b. SRMECH_ERR_BAD_INPUT on NULL / deg == 0 /
 * deg > 16 / m < 2. Additive symbol -> SRMECH_ABI_VERSION unchanged (stays 3).
 * ------------------------------------------------------------------ */
srmech_status_t srmech_riemann_theta_cyc_mul(
    const int64_t *a, const int64_t *b, uint32_t deg,
    const int64_t *table, uint32_t m, int64_t *out);

/* ------------------------------------------------------------------ *
 * rc73 (SECOND GENUS RUNG): the Sp(4,Z) characteristic TRANSFORMATION + the
 * EIGHTH-nome lattice (the addition gate). C peers of
 * RiemannTheta.transform / .addition_holds.
 *
 * The genus-2 modular group Sp(2g,Z)=Sp(4,Z) acts on the binary characteristic
 * m=[ep'; ep] by the EXACT affine-linear map (Igusa, Theta Functions (1972) V.1;
 * DLMF 21.5.9): ep' |-> D ep' - C ep + diag(C D^T); ep |-> -B ep' + A ep +
 * diag(A B^T) (mod 2 for the bit; parity even<->even/odd<->odd preserved). The
 * theta-constant gains an 8th-root multiplier zeta_8^k carried as the EXACT integer
 * exponent k in Z/8 from the Igusa phase phi_m (8*phi_m integer). The TRANSCENDENTAL
 * det(C Omega+D)^{1/2} is NOT computed (off the decision path). All exact
 * integer / mod-2; no float, no abs(). Additive symbols -> ABI unchanged (stays 3).
 * ------------------------------------------------------------------ */

/* Transform characteristic [ep1,ep2; e1,e2] (bits in {0,1}) under gamma[16] (the
 * A,B,C,D 2x2 blocks, row-major). out_char[4] <- (ep1',ep2',e1',e2') bits;
 * *kexp <- the multiplier exponent k in {0..7} (multiplier = zeta_8^k).
 * SRMECH_ERR_BAD_INPUT if a bit is invalid or gamma is not symplectic. */
srmech_status_t srmech_riemann_theta_sp4_char(
    const int64_t *gamma, int ep1, int ep2, int e1, int e2,
    int *out_char, int *kexp);

/* The number of int64 a box needs for the eighth-nome lattice (same shape as the
 * quarter-nome count: (2*box+1)^2 points * 4 [A,B,C,sign]). */
size_t srmech_riemann_theta_eighth_count(uint32_t box);

/* Emit the eighth-nome [A,B,C,sign] quadruple lattice over |n_i| <= box: the
 * common base Q8=q^{1/8} so theta at Omega (at_two_omega=0: A=2(2n+s)^2 ...) and
 * at 2*Omega (at_two_omega=1: A=(4n+s)^2 ...) share ONE integer lattice (the
 * addition identity is a lattice equality). s1,s2 = DOUBLED upper characteristic
 * (any int); e1,e2 in {0,1} the lower sign characteristic. SRMECH_ERR_BAD_INPUT if
 * e-bit invalid; SRMECH_ERR_OVERFLOW if out[] too small. */
srmech_status_t srmech_riemann_theta_eighth_lattice(
    int s1, int s2, int e1, int e2, int at_two_omega, uint32_t box,
    int64_t *out, size_t out_cap, size_t *out_len);

/* rc74: the GENUS-AXIS CAPSTONE — the Thomae / Rosenhain bridge. The genuinely-new
 * exact-integer content is the Eilers genus-2 ETA-MAP (arXiv:1707.08855, eq 4.4):
 * the (mod-2) characteristic [eps(I)] = SUM_{k in I} [A_k] - [K_inf] of a
 * branch-point index set I (subset of {1..6}, e6 = inf), where [A_k] are the Eilers
 * eq.(4.2) Abelian-image characteristics and [K_inf] = [A_2]+[A_4]+[A_6] (eq 4.3,
 * the vector of Riemann constants). This is the characteristic ASSIGNMENT behind
 * BOTH the symbolic Rosenhain lambda-map (the moduli as theta-null ratios, Cor 2.4)
 * AND the Frobenius/Goepel even-null syzygy. Pure GF(2) linear algebra: exact
 * integer / mod-2, no float, no abs() (subtraction == addition in (Z/2)^4). The
 * Goepel relation gate itself convolves srmech_riemann_theta_lattice outputs
 * (caller bookkeeping, already C-backed), so the eta-map is rc74's new C kernel.
 * Additive symbol -> SRMECH_ABI_VERSION unchanged (stays 3).
 * ------------------------------------------------------------------ */

/* The Eilers genus-2 eta-map: branch-point index set -> characteristic. indices[]
 * holds n_idx branch-point indices (each in {1..6}); out_char[4] <- (ep1,ep2,e1,e2)
 * the (mod-2) characteristic bits of [eps(I)]. SRMECH_ERR_BAD_INPUT if any index is
 * out of {1..6} or out_char/indices is NULL. */
srmech_status_t srmech_riemann_theta_eta_char(
    const int *indices, size_t n_idx, int *out_char);

/* ------------------------------------------------------------------ *
 * rc75 (NEXT GENUS RUNG): the GENUS-3 EXACT-INTEGER EXPONENT LATTICE — the C peer
 * of srmech.amsc.riemann_theta.RiemannThetaG3, the genus-3 analog of the rc72
 * genus-2 peer. The genus-3 theta-constant theta[ep'; e](0|Omega) (Grushevsky
 * arXiv:1009.0369 eq.1, the g=3 specialization; binary characteristic
 * [ep1,ep2,ep3; e1,e2,e3], six bits in {0,1}) is a lattice sum over n in Z^3 of
 * (-1)^{e.n} q1^{m1^2} q2^{m2^2} q3^{m3^2} q12^{m1 m2} q13^{m1 m3} q23^{m2 m3},
 * m_i = n_i + ep'_i/2. Cleared to the quarter-nome base (Q_i,Q_ij)=(q_i,q_ij)^{1/4}
 * a term is Q1^A1 Q2^A2 Q3^A3 Q12^C12 Q13^C13 Q23^C23 * (-1)^{e.n} with EXACT INTEGER
 * exponents A_i=(2n_i+ep_i)^2 and the THREE cross-terms C_ij=(2n_i+ep_i)(2n_j+ep_j)
 * (genus 2 had ONE cross-term; genus 3 has THREE -- the hardest part). The lower
 * characteristic e gives the per-term sign (-1)^{e.n} (Class-K pin-slot, never abs).
 * This op emits the lattice as a flat caller-owned int64 array of
 * [A1,A2,A3,C12,C13,C23,sign] SEPTUPLES (one per lattice point |n_i| <= box, row-major
 * (n1,n2,n3)); the genus-3 theta-CONSTANT coefficients are small +-1 lattice counts
 * (int64-exact, no bignum), and the caller accumulates the septuples into the
 * canonical {(A1,A2,A3,C12,C13,C23):coeff} lattice (byte-identical to the Python
 * carrier). Caller-owned out[]; no malloc. Additive symbol -> ABI unchanged (stays 3).
 * ------------------------------------------------------------------ */

/* The number of int64 a box needs: (2*box+1)^3 lattice points * 7
 * (A1,A2,A3,C12,C13,C23,sign). */
size_t srmech_riemann_theta_g3_count(uint32_t box);

/* Emit the genus-3 [A1,A2,A3,C12,C13,C23,sign] septuple lattice for characteristic
 * [ep1,ep2,ep3; e1,e2,e3] (bits in {0,1}) over |n_i| <= box, into the caller out[]
 * (out_cap int64); *out_len <- the number of int64 written (= the g3 count).
 * SRMECH_ERR_BAD_INPUT if any bit is not in {0,1}; SRMECH_ERR_OVERFLOW if out[] is
 * too small. */
srmech_status_t srmech_riemann_theta_g3_lattice(
    int ep1, int ep2, int ep3, int e1, int e2, int e3, uint32_t box,
    int64_t *out, size_t out_cap, size_t *out_len);

/* ------------------------------------------------------------------ *
 * rc80 (NEXT GENUS RUNG, the SCHOTTKY FRONTIER): the GENUS-4 EXACT-INTEGER EXPONENT
 * LATTICE — the C peer of srmech.amsc.riemann_theta.RiemannThetaG4, the genus-4 analog
 * of the rc75 genus-3 peer. The genus-4 theta-constant theta[ep'; e](0|Omega)
 * (Grushevsky arXiv:1009.0369 eq.1, the g=4 specialization; binary characteristic
 * [ep1,ep2,ep3,ep4; e1,e2,e3,e4], eight bits in {0,1}) is a lattice sum over n in Z^4 of
 * (-1)^{e.n} prod_i q_i^{m_i^2} prod_{i<j} q_ij^{m_i m_j}, m_i = n_i + ep'_i/2. Cleared
 * to the quarter-nome base (Q_i,Q_ij)=(q_i,q_ij)^{1/4} a term is
 *  Q1^A1 Q2^A2 Q3^A3 Q4^A4 Q12^C12 Q13^C13 Q14^C14 Q23^C23 Q24^C24 Q34^C34 *(-1)^{e.n}
 * with EXACT INTEGER exponents A_i=(2n_i+ep_i)^2 and the SIX cross-terms
 * C_ij=(2n_i+ep_i)(2n_j+ep_j) for the 6 pairs {12,13,14,23,24,34} (genus 2 had ONE,
 * genus 3 THREE, genus 4 SIX -- the scaling difficulty). The lower characteristic e
 * gives the per-term sign (-1)^{e.n} (Class-K pin-slot, never abs). This op emits the
 * lattice as a flat caller-owned int64 array of
 * [A1,A2,A3,A4,C12,C13,C14,C23,C24,C34,sign] 11-TUPLES (one per lattice point
 * |n_i| <= box, row-major (n1,n2,n3,n4)); the genus-4 theta-CONSTANT coefficients are
 * small +-1 lattice counts (int64-exact, no bignum), and the caller accumulates the
 * 11-tuples into the canonical {(A1..A4,C12,C13,C14,C23,C24,C34):coeff} lattice
 * (byte-identical to the Python carrier). Caller-owned out[]; no malloc. Additive symbol
 * -> ABI unchanged (stays 3). NOTE: (2*box+1)^4 grows fast -- keep box small (2 or 3);
 * the formal relations are box-stable. The Schottky-frontier OPEN (the numerical
 * Jacobian decision) is DOCUMENTED in the Python carrier, NOT built here.
 * ------------------------------------------------------------------ */

/* The number of int64 a box needs: (2*box+1)^4 lattice points * 11
 * (A1,A2,A3,A4,C12,C13,C14,C23,C24,C34,sign). */
size_t srmech_riemann_theta_g4_count(uint32_t box);

/* Emit the genus-4 [A1,A2,A3,A4,C12,C13,C14,C23,C24,C34,sign] 11-tuple lattice for
 * characteristic [ep1,ep2,ep3,ep4; e1,e2,e3,e4] (bits in {0,1}) over |n_i| <= box, into
 * the caller out[] (out_cap int64); *out_len <- the number of int64 written (= the g4
 * count). SRMECH_ERR_BAD_INPUT if any bit is not in {0,1}; SRMECH_ERR_OVERFLOW if out[]
 * is too small. */
srmech_status_t srmech_riemann_theta_g4_lattice(
    int ep1, int ep2, int ep3, int ep4, int e1, int e2, int e3, int e4, uint32_t box,
    int64_t *out, size_t out_cap, size_t *out_len);

/* ------------------------------------------------------------------ *
 * rc86 (NEXT GENUS RUNG, PAST the SCHOTTKY FRONTIER): the GENUS-5 EXACT-INTEGER EXPONENT
 * LATTICE -- the C peer of srmech.amsc.riemann_theta.RiemannThetaG5, the genus-5 analog
 * of the rc80 genus-4 peer. The genus-5 theta-constant theta[ep'; e](0|Omega) (binary
 * characteristic [ep1..ep5; e1..e5], ten bits in {0,1}) is a lattice sum over n in Z^5;
 * cleared to the quarter-nome base a term is prod_i Q_i^{A_i} prod_{i<j} Q_ij^{C_ij}
 * *(-1)^{e.n} with A_i=(2n_i+ep_i)^2 and the TEN cross-terms C_ij=(2n_i+ep_i)(2n_j+ep_j)
 * over the 10 pairs {12,13,14,15,23,24,25,34,35,45} (genus 4 had SIX -- the scaling
 * difficulty). Emits the lattice as a flat caller-owned int64 array of
 * [A1..A5,C12,C13,C14,C15,C23,C24,C25,C34,C35,C45,sign] 16-TUPLES (one per lattice point
 * |n_i| <= box, row-major (n1,n2,n3,n4,n5)); the genus-5 theta-CONSTANT coefficients are
 * small +-1 lattice counts (int64-exact, no bignum), and the caller accumulates the
 * 16-tuples into the canonical {(A1..A5,C12..C45):coeff} lattice (byte-identical to the
 * Python carrier). Caller-owned out[]; no malloc. Additive symbol -> ABI unchanged
 * (stays 3). NOTE: (2*box+1)^5 grows FAST -- keep box small (1 or 2; box >= 3 is
 * catastrophic); the formal relations are box-stable. The genuinely-OPEN genus-5 Schottky
 * decision (NO single modular form cuts J_5: dim A_5 = 15, dim J_5 = 12, codim 3 -- NOT a
 * hypersurface) is DOCUMENTED in the Python carrier, NOT built here.
 * ------------------------------------------------------------------ */

/* The number of int64 a box needs: (2*box+1)^5 lattice points * 16
 * (A1..A5,C12,C13,C14,C15,C23,C24,C25,C34,C35,C45,sign). */
size_t srmech_riemann_theta_g5_count(uint32_t box);

/* Emit the genus-5 [A1..A5,C12,C13,C14,C15,C23,C24,C25,C34,C35,C45,sign] 16-tuple lattice
 * for characteristic [ep1..ep5; e1..e5] (bits in {0,1}) over |n_i| <= box, into the caller
 * out[] (out_cap int64); *out_len <- the number of int64 written (= the g5 count).
 * SRMECH_ERR_BAD_INPUT if any bit is not in {0,1}; SRMECH_ERR_OVERFLOW if out[] is too
 * small. */
srmech_status_t srmech_riemann_theta_g5_lattice(
    int ep1, int ep2, int ep3, int ep4, int ep5,
    int e1, int e2, int e3, int e4, int e5, uint32_t box,
    int64_t *out, size_t out_cap, size_t *out_len);

/* ------------------------------------------------------------------ *
 * rc81 (the GENUS-4 CAPSTONE): the SCHOTTKY FORM J = theta^4(E8+E8) - theta^4(E16)
 * representation-number COUNTER -- the C peer of
 * srmech.amsc.riemann_theta.SchottkyFormG4._count_gram_py.
 *
 * The Schottky form J (weight-8 degree-4 level-1 Siegel CUSP form whose vanishing cuts
 * the genus-4 Jacobian locus = the Schottky problem's g=4 solution; Schottky 1888, Igusa
 * 1981, Poor-Yuen 1996) is the difference of the genus-4 theta-SERIES of the two rank-16
 * even-unimodular lattices E8+E8 and E16=D16+. Organized by the Gram matrix T of a g-tuple
 * of lattice vectors, J's coefficient at T is the EXACT INTEGER representation-number
 * difference r_{E8+E8}(T) - r_{E16}(T) (by Witt 1941 these EQUAL for g<=3 and FIRST DIFFER
 * at g=4, so the difference is the nonzero Schottky cusp form). This op COUNTS r_L(T) over
 * the MINIMAL shell (norm-2 vectors; the leading part of J) for one lattice. The vectors
 * are passed DOUBLED (real coords *2 -> half-integer coords are exact odd ints, no float),
 * so the doubled inner <2u,2v> = 4<u,v> IS the q_ij quarter-nome exponent (diagonal 8 =
 * norm 2; off-diagonal in {-8,-4,0,4,8}). The count is a pure NON-NEGATIVE integer tally
 * (no sign, NO abs()), walking the inner-value BITSET table (Class-L adjacency-by-inner-
 * value). Caller arena (no malloc): srmech_riemann_theta_g4_schottky_arena(n) uint64.
 * Additive symbols -> ABI stays 3.
 * ------------------------------------------------------------------ */

/* The uint64 the count op's caller arena needs: bitset table (n*5*ceil(n/64)) + one
 * scratch bitset (ceil(n/64)). The Python marshaller sizes the arena from this. */
size_t srmech_riemann_theta_g4_schottky_arena(size_t n);

/* Count ordered g-tuples of minimal (doubled) vectors vecs[n*dim] whose OFF-DIAGONAL
 * doubled Gram is gram_off[k], k = genus*(genus-1)/2 (genus in {1,2,3,4}; the diagonal is
 * 8 = norm 2). *out_count <- the exact non-negative count. arena (arena_cap uint64) >=
 * srmech_riemann_theta_g4_schottky_arena(n). SRMECH_ERR_BAD_INPUT: unsupported genus,
 * n=0/dim=0, n > 1024, or an off-Gram value outside {-8,-4,0,4,8}; SRMECH_ERR_OVERFLOW:
 * arena too small; SRMECH_ERR_NULL_ARG: NULL pointers. */
srmech_status_t srmech_riemann_theta_g4_schottky_count(
    const int64_t *vecs, size_t n, size_t dim, int genus,
    const int64_t *gram_off, uint64_t *arena, size_t arena_cap,
    int64_t *out_count);

/* The int64 the shell op's out[] needs: at most 5^(genus*(genus-1)/2) rows, each
 * (genus*(genus-1)/2 off-values + 1 count). genus in {1,2,3,4}. */
size_t srmech_riemann_theta_g4_schottky_shell_count(int genus);

/* The FULL minimal-shell off-Gram HISTOGRAM for one lattice: for every off-Gram pattern
 * with a NONZERO count, emit the row [off_1..off_noff, count] (noff = genus*(genus-1)/2;
 * off values the doubled inners in {-8,-4,0,4,8}) into out[] (out_cap int64); *out_len <-
 * the number of int64 written. The bitset table is built ONCE; the patterns are walked
 * mixed-radix over the 5 classes. arena per srmech_riemann_theta_g4_schottky_arena(n).
 * Mirrors SchottkyFormG4._full_shell_grams_py. SRMECH_ERR_OVERFLOW if out[] (size via
 * srmech_riemann_theta_g4_schottky_shell_count) is too small. */
srmech_status_t srmech_riemann_theta_g4_schottky_shell(
    const int64_t *vecs, size_t n, size_t dim, int genus,
    uint64_t *arena, size_t arena_cap, int64_t *out, size_t out_cap,
    size_t *out_len);

/* ------------------------------------------------------------------ *
 * rc76: IGUSA'S chi_18 — the EXACT product of the 36 even genus-3 theta-nulls (the
 * genus-3 hyperelliptic / vanishing-theta-null structure as an exact formal q-series).
 * The C peer of srmech.amsc.riemann_theta.RiemannThetaG3.chi18_leading_part.
 *
 * chi_18 in S_18(Gamma_3) is the weight-18 degree-3 Siegel cusp form DEFINED AS THE
 * PRODUCT OF ALL 36 EVEN THETA-CONSTANTS (each theta-null weight 1/2 -> 36*1/2 = 18;
 * Bernatska-Kopeliovich arXiv:2306.14889 p.1; van der Geer SMF Degree 2&3 + Invariant
 * Theory). Divisor = H_3 + 2D -> vanishes exactly on the genus-3 hyperelliptic locus.
 * This op emits the EXACT LEADING-ORDER HOMOGENEOUS PART (the cusp-vanishing structure)
 * as a flat int64 array of [A1,A2,A3,C12,C13,C23,coeff] septuples — NONZERO, at
 * diagonal quarter-order 48 (= 12 in q_i). Caller-arena (one int64 work[] sized via
 * the count helper) ping-ponged; no malloc. Additive symbols -> ABI stays 3. */

/* The number of int64 the work arena needs (THREE buffers, box-independent). */
size_t srmech_riemann_theta_g3_chi18_count(uint32_t box);

/* Emit Igusa's chi_18 leading-part [A1,A2,A3,C12,C13,C23,coeff] septuples into out[]
 * (out_cap int64); work[] is the caller arena (work_cap int64, >= the count helper);
 * *out_len <- int64 written. box is for signature parity (must be >= 1).
 * SRMECH_ERR_BAD_INPUT on box==0 / undersized work; SRMECH_ERR_OVERFLOW on undersized
 * out[] or an over-cap accumulator. */
srmech_status_t srmech_riemann_theta_g3_chi18(
    uint32_t box, int64_t *work, size_t work_cap,
    int64_t *out, size_t out_cap, size_t *out_len);

/* ------------------------------------------------------------------ *
 * rc77: the genus-3 Sp(6,Z) modular TRANSFORMATION on the characteristics + the
 * genus-3 two-argument ADDITION theorem (the g=2->g=3 parametric extension of the
 * rc73 Sp(4,Z) transform + addition). The C peers of
 * srmech.amsc.riemann_theta.RiemannThetaG3.{transform,addition_*}.
 *
 * (A) srmech_riemann_theta_g3_sp6_char -- the EXACT integer Sp(6,Z) characteristic
 *     action ep' |-> D ep' - C ep + diag(C D^T), ep |-> -B ep' + A ep + diag(A B^T)
 *     (DLMF 21.5.9, general genus g; here 3x3 blocks, gamma is 36 int64 A,B,C,D
 *     row-major) + the EXACT 8th-root multiplier exponent k in Z/8 (the Igusa phase
 *     8*phi_m; the transcendental det(C Om + D)^{1/2} is OFF the decision path).
 * (B) srmech_riemann_theta_g3_eighth_lattice -- the COMMON eighth-nome genus-3
 *     lattice at Omega / 2Omega that the addition gate (DLMF 21.6.8, g=3, sum over
 *     nu in (Z/2)^3) convolves; [A1,A2,A3,C12,C13,C23,sign] septuples.
 * Caller-owned out[]; no malloc. Additive symbols -> ABI unchanged (stays 3). */

/* Emit the genus-3 Sp(6,Z) transformed characteristic + kappa exponent. gamma[36] =
 * A,B,C,D 3x3 blocks (row-major); out_char[6] <- (ep1',ep2',ep3',e1',e2',e3') bits;
 * *kexp <- k in {0..7} (multiplier = zeta_8^k). SRMECH_ERR_BAD_INPUT if a bit is
 * invalid or gamma is not symplectic. */
srmech_status_t srmech_riemann_theta_g3_sp6_char(
    const int64_t *gamma, int ep1, int ep2, int ep3, int e1, int e2, int e3,
    int *out_char, int *kexp);

/* The number of int64 a box needs for the genus-3 eighth-nome lattice: (2*box+1)^3
 * lattice points * 7 (A1,A2,A3,C12,C13,C23,sign). */
size_t srmech_riemann_theta_g3_eighth_count(uint32_t box);

/* Emit the genus-3 eighth-nome [A1,A2,A3,C12,C13,C23,sign] septuple lattice for the
 * DOUBLED upper characteristic s=(s1,s2,s3) + lower char (e1,e2,e3), at Omega
 * (at_two_omega=0: A=2(2n+s)^2 ...) or 2Omega (at_two_omega=1: A=(4n+s)^2 ...) over
 * |n_i|<=box, row-major; *out_len <- int64 written. SRMECH_ERR_BAD_INPUT if a
 * lower-char bit is invalid; SRMECH_ERR_OVERFLOW if out[] is too small. */
srmech_status_t srmech_riemann_theta_g3_eighth_lattice(
    int s1, int s2, int s3, int e1, int e2, int e3, int at_two_omega, uint32_t box,
    int64_t *out, size_t out_cap, size_t *out_len);

/* ------------------------------------------------------------------ *
 * rc78: the genus-3 GÖPEL / FROBENIUS quadratic theta-null SYZYGY gate — the C peer of
 * srmech.amsc.riemann_theta.RiemannThetaG3.goepel_holds.
 *
 * The genus-3 GÖPEL/FROBENIUS quadratic relation among the even theta-NULLS (the
 * genus-3 analog of the genus-2 rc74 Göpel syzygy) — a 4-PAIR / 8-NULL same-Omega
 * relation `theta^2[a]theta^2[b] = theta^2[c]theta^2[d] + theta^2[e]theta^2[f]
 * - theta^2[g]theta^2[h]` among the eight even nulls a=[000;001] b=[111;110]
 * c=[000;010] d=[111;101] e=[001;000] f=[110;111] g=[010;000] h=[101;111], all summing
 * to [1,1,1;1,1,1] (a genus-3 Goepel/azygetic system). The genus-2-style 6-null lift
 * does NOT hold for g=3 (exhaustively checked) — the 4-term form is the genuine minimal
 * genus-3 syzygy. Glass, Compositio Math 40 (1980) §3 (products-of-squares, coeffs +-1);
 * Fiorentino-Salvati Manni SIGMA 16 (2020) 057; Igusa Theta Functions (1972) §IV/V; van
 * der Geer SMF Degree 2&3. Holds for ALL Omega; decided EXACTLY on the box-stable safe
 * inner region (each A_i, |C_ij| <= box^2). Caller-arena (one int64 work[] sized via the
 * count helper); no malloc. Additive symbols -> ABI stays 3. */

/* The number of int64 the caller work arena needs (THREE buffers, box-independent). */
size_t srmech_riemann_theta_g3_goepel_count(uint32_t box);

/* Decide the genus-3 Goepel syzygy gate over the box-stable safe region. work[] is the
 * caller arena (work_cap int64, >= the count helper); *out_holds <- 1 iff LHS == RHS
 * (residual empty), *out_has_cross <- 1 iff a genuine genus-3 cross-term (C13 or C23
 * != 0) populates the LHS safe region. SRMECH_ERR_BAD_INPUT on box<3 / undersized work;
 * SRMECH_ERR_OVERFLOW on an over-cap accumulator. */
srmech_status_t srmech_riemann_theta_g3_goepel(
    uint32_t box, int64_t *work, size_t work_cap,
    int *out_holds, int *out_has_cross);

/* ------------------------------------------------------------------ *
 * rc85: the genus-4 Sp(8,Z) modular TRANSFORMATION on the characteristics + the
 * genus-4 two-argument ADDITION theorem + the genus-4 universal GOEPEL relation gate
 * (the g=3->g=4 parametric extension of the rc77/rc78 genus-3 peers — closes the
 * genus-ladder modular-action gap so the g1->g4 ladder is uniform). The C peers of
 * srmech.amsc.riemann_theta.RiemannThetaG4.{transform, addition_*, goepel_holds}.
 * DLMF 21.5.9 / 21.6.8 hold for general genus g; here 4x4 blocks / 4-vectors over an
 * 8x8 symplectic gamma (64 int64 A,B,C,D row-major). Caller-owned out[] / caller arena;
 * no malloc. Additive symbols -> ABI unchanged (stays 3). */

/* Emit the genus-4 Sp(8,Z) transformed characteristic + kappa exponent. gamma[64] =
 * A,B,C,D 4x4 blocks (row-major); out_char[8] <- (ep1'..ep4',e1'..e4') bits; *kexp <- k
 * in {0..7} (multiplier = zeta_8^k). SRMECH_ERR_BAD_INPUT if a bit is invalid or gamma
 * is not symplectic. */
srmech_status_t srmech_riemann_theta_g4_sp8_char(
    const int64_t *gamma, int ep1, int ep2, int ep3, int ep4,
    int e1, int e2, int e3, int e4, int *out_char, int *kexp);

/* The number of int64 a box needs for the genus-4 eighth-nome lattice: (2*box+1)^4
 * lattice points * 11 (A1..A4,C12,C13,C14,C23,C24,C34,sign). */
size_t srmech_riemann_theta_g4_eighth_count(uint32_t box);

/* Emit the genus-4 eighth-nome [A1..A4,C12,C13,C14,C23,C24,C34,sign] 11-tuple lattice
 * for the DOUBLED upper characteristic s=(s1..s4) + lower char (e1..e4), at Omega
 * (at_two_omega=0: A=2(2n+s)^2 ...) or 2Omega (at_two_omega=1: A=(4n+s)^2 ...) over
 * |n_i|<=box, row-major; *out_len <- int64 written. SRMECH_ERR_BAD_INPUT if a
 * lower-char bit is invalid; SRMECH_ERR_OVERFLOW if out[] is too small. */
srmech_status_t srmech_riemann_theta_g4_eighth_lattice(
    int s1, int s2, int s3, int s4, int e1, int e2, int e3, int e4,
    int at_two_omega, uint32_t box, int64_t *out, size_t out_cap, size_t *out_len);

/* The number of int64 the caller work arena needs for the genus-4 Goepel gate (THREE
 * buffers, box-independent / capped). */
size_t srmech_riemann_theta_g4_goepel_count(uint32_t box);

/* Decide the genus-4 universal Goepel relation gate over the box-stable safe region. An
 * 8-PAIR / 16-NULL same-Omega relation Sum sign*theta^2[a]theta^2[b] == 0 among even
 * theta-nulls all summing to [1,1,1,1;1,1,1,1] (the genus-4 instance of the goepel_holds
 * surface g2/g3 expose; Glass Compositio Math 40 (1980); Fiorentino-Salvati Manni SIGMA
 * 16 (2020) 057; Igusa Theta Functions (1972) SS IV/V). work[] is the caller arena
 * (work_cap int64, >= the count helper); *out_holds <- 1 iff the relation holds (residual
 * empty), *out_has_cross <- 1 iff a genuine genus-4 cross-term (C14, C24 or C34 != 0)
 * populates the LHS safe region. SRMECH_ERR_BAD_INPUT on box<2 / undersized work;
 * SRMECH_ERR_OVERFLOW on an over-cap accumulator. */
srmech_status_t srmech_riemann_theta_g4_goepel(
    uint32_t box, int64_t *work, size_t work_cap,
    int *out_holds, int *out_has_cross);

/* ------------------------------------------------------------------ *
 * rc107: the generic SPARSE SAFE-SUPPORT GATE DECISION kernel — the ONE C peer of
 * ALL the genus-axis theta identity/distinctness gates (g in {2..5}: the
 * duplication / addition / Goepel *_holds gates and the *_is_distinct_* gates of
 * srmech.amsc.riemann_theta.{RiemannTheta, RiemannThetaG3, RiemannThetaG4,
 * RiemannThetaG5} — the #707 dive's SAFE-REGION PUSH-DOWN, Deliverable B1).
 *
 * Every gate compares two signed sums of theta-lattice PRODUCTS only on the safe
 * inner region {A_i <= safe, |C_ij| <= safe}. The diagonal exponents A_i are
 * non-negative and ADD under the lattice convolution, so a product monomial inside
 * the safe region can only come from factor monomials each with A_i <= safe — each
 * factor is therefore enumerated DIRECTLY on its safe support {u : dc*u^2 <= safe}
 * (the exact safe region of the INFINITE theta series; box-parameter-free) and the
 * convolutions carry a diagonal-additivity guard. Bit-identical to the dense
 * box-enumerate-then-restrict path on the compared region (measured x48..x6900).
 *
 * The gate ships its comparison list as an int32 SPEC (built by the Python side —
 * the single SSOT of the pair/syzygy data), parsed sequentially:
 *   per comparison: [n_lhs, n_rhs] then (n_lhs + n_rhs) products;
 *   per product:    [sign(+-1), n_factors(2 or 4)] then n_factors factor specs;
 *   per factor:     [dc, step, a[0..g-1], e[0..g-1]]   (2 + 2g int32)
 * where a factor's terms are u_i = step*n_i + a_i with diagonal dc*u_i^2, cross
 * dc*u_i*u_j and Class-K sign (-1)^{e.n}. Per comparison the kernel accumulates
 * the LHS products into a hash-table residual (out_cross[c] <- 1 iff a surviving
 * LHS monomial carries a genus-g cross-term C_{i,g} != 0), then subtracts the RHS
 * products; out_equal[c] <- 1 iff the residual vanishes (LHS == RHS on the safe
 * region). restrict_crosses=1 applies the full safe cut (A_i AND |C_ij| <= safe);
 * 0 is the diagonal-only mode of the _diag_restrict-shaped distinctness gates.
 *
 * ONE call decides a WHOLE gate (no per-lattice marshaling — the rc106 finding
 * that round-tripping the eighth-nome lattices through ctypes was a net slowdown).
 * Caller-arena (one int64 work[] sized via the count helper — a main hash table +
 * four aux tables, per-genus compiled caps); no malloc. Overflowing a cap returns
 * SRMECH_ERR_OVERFLOW and the Python side falls to the pure sparse body. Additive
 * symbols -> ABI unchanged (stays 3). */

/* The number of int64 the caller work arena needs for genus g (2..5) — the main
 * accumulator hash table + 2 factor + 2 intermediate aux tables, each slot
 * [used, key(g + g(g-1)/2), coeff]. Box/safe-independent (per-genus compiled
 * caps). Returns 0 for an out-of-range genus. */
size_t srmech_riemann_theta_gate_count(uint32_t g);

/* Decide n_comparisons gate comparisons over the safe region (see the block
 * comment above for the spec wire format). out_equal[] / out_cross[] are
 * caller-owned int32[n_comparisons]. SRMECH_ERR_BAD_INPUT on a malformed spec /
 * out-of-range genus / negative safe / undersized work; SRMECH_ERR_OVERFLOW when
 * a table cap is exceeded (the caller falls to the pure path). */
srmech_status_t srmech_riemann_theta_gate_decide(
    uint32_t g, int64_t safe, uint32_t restrict_crosses,
    const int32_t *spec, size_t spec_len, uint32_t n_comparisons,
    int64_t *work, size_t work_cap,
    int32_t *out_equal, int32_t *out_cross);

/* ------------------------------------------------------------------ *
 * srmech_tripoly — EXACT-RATIONAL TRIVARIATE polynomial over srmech_bigint (the
 * C peer of srmech.amsc.tripoly.TriPoly; the multivariate "sums of sums"
 * creative-telescoping foundation, the 3-variable sibling of BiPoly).
 *
 * A TriPoly is an exact-Q polynomial in the free variable n and two summation
 * variables j, k, carried as a ROW-MAJOR (j, k) GRID of n-polynomials: the grid
 * has aj = (j-degree + 1) rows and ak = (k-degree + 1) columns; the cell
 * (dj, dk) at flat index dj*ak + dk is an n-polynomial — a run of exact-rational
 * coefficients in ASCENDING n-degree. The cell n-runs are CONCATENATED in a
 * single pair of caller-owned srmech_bigint arrays (nums[] / dens[], ascending n
 * within each cell, cells in row-major (j,k) order), with a parallel nlen[]
 * array (length aj*ak) giving each cell's n-run length. A cell coefficient
 * nums[..]/dens[..] is the exact rational of n^dn (dens > 0, gcd(|nums|, dens)
 * == 1; zero coefficient = 0/1).
 *
 * Each op computes the SAME exact rational coefficients srmech.amsc.tripoly.
 * TriPoly computes (Class-N rational arithmetic over Class-J reduction), over
 * caller-arena srmech_bigint (NO malloc), reduced to lowest terms with positive
 * denominator. Byte-identical to Python at ANY magnitude (full bignum; no
 * int64/Q61 ceiling).
 *
 * add/sub require the two grids to share the SAME (aj, ak) shape: the caller
 * pre-pads the smaller grid's missing cells to empty n-runs and the smaller j/k
 * extent to the max (mirroring how Python TriPoly aligns block(d) over the max
 * j-degree and each BiPoly over the max k-degree). mul is the 2-D (j,k)
 * convolution: the product grid is (aj+bj-1) x (ak+bk-1); the caller passes the
 * product column count `ocols`, a per-output-cell base offset array out_off[]
 * (into the concatenated out arrays — the caller-sized cell stride), the
 * worst-case n-run convolution depth `accum_terms`, and pre-zeros out_nlen[] to
 * 0; the op multiply-accumulates each cell and writes the trimmed n-run length
 * back into out_nlen[cell].
 *
 * STANDALONE-COMPLETE: every working carrier is carved from the caller arena `ws`
 * (>= the matching srmech_tripoly_ws_bound), so the bound is the caller's RAM. A
 * too-small ws or an out coefficient cap -> SRMECH_ERR_OVERFLOW (never a silent
 * wrap), and the Python TriPoly falls back to its ceiling-free pure-Python path.
 *
 * Carrier-internal (like srmech_poly): NOT a Rosetta ledger op. Additive symbols
 * -> SRMECH_ABI_VERSION unchanged.
 * ------------------------------------------------------------------ */

/* Minimum `ws_len` BYTES the caller hands any srmech_tripoly_* op below, for
 * input coefficients of `coeff_limbs` significant limbs and a worst-case output
 * n-run of `n_terms` coefficients. 8-byte-aligned uint32 bump arena. */
size_t srmech_tripoly_ws_bound(size_t coeff_limbs, size_t n_terms);

/* out = a + b, cellwise (j,k)-aligned, coefficientwise exact-Q over each cell's
 * n-run, trimmed. Both grids are `cells` cells (the SAME aj*ak shape); a_nlen /
 * b_nlen give each cell's n-run length; out arrays hold, per cell,
 * max(a_nlen[cell], b_nlen[cell]) coefficients (the pre-trim stride);
 * out_nlen[cell] <- the trimmed length. */
srmech_status_t srmech_tripoly_add(const srmech_bigint_t *a_n,
                                   const srmech_bigint_t *a_d,
                                   const size_t *a_nlen, size_t cells,
                                   const srmech_bigint_t *b_n,
                                   const srmech_bigint_t *b_d,
                                   const size_t *b_nlen,
                                   srmech_bigint_t *out_n,
                                   srmech_bigint_t *out_d, size_t *out_nlen,
                                   void *ws, size_t ws_len);

/* out = a - b, cellwise exact-Q. Same shapes as add. */
srmech_status_t srmech_tripoly_sub(const srmech_bigint_t *a_n,
                                   const srmech_bigint_t *a_d,
                                   const size_t *a_nlen, size_t cells,
                                   const srmech_bigint_t *b_n,
                                   const srmech_bigint_t *b_d,
                                   const size_t *b_nlen,
                                   srmech_bigint_t *out_n,
                                   srmech_bigint_t *out_d, size_t *out_nlen,
                                   void *ws, size_t ws_len);

/* out = a * b (2-D (j,k) convolution; each cell an n-run convolution). A is
 * (aj x ak), B is (bj x bk); the product grid is (aj+bj-1) x (ak+bk-1) with
 * `ocols` = ak+bk-1 columns. out_off[] (length (aj+bj-1)*ocols) is each output
 * cell's base offset into the concatenated out arrays; `accum_terms` is the
 * worst-case output n-run length. The caller pre-zeros out_nlen[] to 0; the op
 * multiply-accumulates + writes the trimmed n-run length per cell. */
srmech_status_t srmech_tripoly_mul(const srmech_bigint_t *a_n,
                                   const srmech_bigint_t *a_d,
                                   const size_t *a_nlen, size_t aj, size_t ak,
                                   const srmech_bigint_t *b_n,
                                   const srmech_bigint_t *b_d,
                                   const size_t *b_nlen, size_t bj, size_t bk,
                                   srmech_bigint_t *out_n,
                                   srmech_bigint_t *out_d, size_t *out_nlen,
                                   const size_t *out_off, size_t ocols,
                                   size_t accum_terms, void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_qpoly — EXACT q-shift CARRIER over srmech_bigint (the C peer of
 * srmech.amsc.qpoly.QPoly; the q-hypergeometric F929 reduction-row foundation,
 * the q-analog of srmech_poly).
 *
 * A QPoly is a LAURENT polynomial in x = q^n whose coefficients are exact
 * polynomials in q (the ground ring Q[q]). It is carried as a ROW of q-polynomial
 * CELLS over an x-exponent window [x_low, x_low+cells): cell i is the Q[q]
 * coefficient of x^(x_low+i), itself a run of exact-rational coefficients in
 * ASCENDING q-degree. The cell q-runs are stored CONCATENATED in a single pair of
 * caller-owned srmech_bigint arrays (nums[] / dens[], ascending q within each
 * cell, cells in ascending-x order), with a parallel `qlen[]` array (length
 * `cells`) giving each cell's q-run length. A cell coefficient is the exact
 * rational of q^dq (dens > 0, gcd(|nums|, dens) == 1; zero = 0/1). The x_low
 * offset is the caller's bookkeeping (these ops align by INDEX). (Mirrors
 * srmech_tripoly's concatenated-cell + nlen[] layout, one dimension lighter — a
 * single x-row, not a (j,k) grid.)
 *
 * Each op computes the SAME exact rational coefficients srmech.amsc.qpoly.QPoly
 * computes (Class-N rational arithmetic over Class-J reduction), over caller-arena
 * srmech_bigint (NO malloc), reduced to lowest terms — byte-identical to Python at
 * ANY magnitude (full bignum; no int64/Q61 ceiling).
 *
 *   add/sub : cellwise (x-index-aligned) coefficientwise exact-Q add/sub of the
 *             two cells' q-runs, then trim. The caller pre-aligns both inputs to
 *             the SAME x-window (cells count), padding missing cells to empty
 *             q-runs (mirroring the Python QPoly._addsub union span).
 *   mul     : 1-D x-convolution; each output x-cell accumulates the exact-Q q-run
 *             convolution (a Q[q] multiply) of the input cells.
 *   qshift  : the q-shift sigma^s : x -> q^s * x. Cell i (x-exponent x_low+i)
 *             becomes c_i(q) * q^(s*(x_low+i)) — each cell's q-run shifted up by
 *             s*(x_low+i) q-degrees. The caller guarantees every s*(x_low+i) >= 0
 *             (the Q[q] ground ring; q-Gosper feeds only non-negative shifts) — a
 *             negative shift -> SRMECH_ERR_BAD_INPUT (a Laurent-in-q result needs
 *             the future Q(q) carrier, never asked of this op).
 *
 * STANDALONE-COMPLETE: every working carrier is carved from the caller arena `ws`
 * (>= the matching srmech_qpoly_ws_bound), so the bound is the caller's RAM. Out
 * coefficient arrays are caller-owned + must be pre-sized (add/sub: each cell
 * max(na,nb); mul: each output cell na+nb-1; qshift: each cell in_qlen + s*e), and
 * pre-zeroed for mul (the multiply-accumulate seed). A too-small ws or out cap ->
 * SRMECH_ERR_OVERFLOW (never a silent wrap), and the Python QPoly falls back to
 * its ceiling-free pure path.
 *
 * Carrier-internal (like srmech_poly / srmech_tripoly): NOT a Rosetta ledger op.
 * Additive symbols -> SRMECH_ABI_VERSION unchanged.
 * ------------------------------------------------------------------ */

/* Minimum `ws_len` BYTES the caller hands any srmech_qpoly_* op below, for input
 * coefficients of `coeff_limbs` significant limbs and a worst-case output q-run of
 * `n_terms` coefficients. 8-byte-aligned uint32 bump arena. */
size_t srmech_qpoly_ws_bound(size_t coeff_limbs, size_t n_terms);

/* out = a + b, cellwise (x-index-aligned) coefficientwise exact-Q, trimmed. Both
 * inputs share `cells` x-cells (caller pre-aligns to the union x-window, padding
 * missing cells to empty q-runs). out arrays hold, per cell, max(na, nb)
 * coefficients (concatenated, ascending q); out_qlen[cell] <- the trimmed q-len. */
srmech_status_t srmech_qpoly_add(const srmech_bigint_t *a_n,
                                 const srmech_bigint_t *a_d,
                                 const size_t *a_qlen, size_t cells,
                                 const srmech_bigint_t *b_n,
                                 const srmech_bigint_t *b_d,
                                 const size_t *b_qlen,
                                 srmech_bigint_t *out_n, srmech_bigint_t *out_d,
                                 size_t *out_qlen, void *ws, size_t ws_len);

/* out = a - b, cellwise exact-Q, trimmed. Same shapes as srmech_qpoly_add. */
srmech_status_t srmech_qpoly_sub(const srmech_bigint_t *a_n,
                                 const srmech_bigint_t *a_d,
                                 const size_t *a_qlen, size_t cells,
                                 const srmech_bigint_t *b_n,
                                 const srmech_bigint_t *b_d,
                                 const size_t *b_qlen,
                                 srmech_bigint_t *out_n, srmech_bigint_t *out_d,
                                 size_t *out_qlen, void *ws, size_t ws_len);

/* out = a * b (1-D x-convolution; each output cell a q-run convolution), exact-Q.
 * A is `acells` x-cells, B is `bcells`; the product is acells+bcells-1 cells. The
 * caller pre-zeros the output (total slots) and passes each output cell's q-run
 * CAPACITY in out_qlen[cell] on entry (the stride); the op fills + trims, writing
 * the final trimmed q-len back. out_off[cell] is the flat output offset of cell
 * `cell`. `accum_terms` is the worst-case output q-run length (sizes the arena). */
srmech_status_t srmech_qpoly_mul(const srmech_bigint_t *a_n,
                                 const srmech_bigint_t *a_d,
                                 const size_t *a_qlen, size_t acells,
                                 const srmech_bigint_t *b_n,
                                 const srmech_bigint_t *b_d,
                                 const size_t *b_qlen, size_t bcells,
                                 srmech_bigint_t *out_n, srmech_bigint_t *out_d,
                                 size_t *out_qlen, const size_t *out_off,
                                 size_t accum_terms, void *ws, size_t ws_len);

/* The q-shift sigma^s : x -> q^s * x, i.e. f(q^n) -> f(q^(n+s)). Cell i
 * (x-exponent x_low+i, coefficient c_i(q)) -> c_i(q) * q^(s*(x_low+i)): each
 * cell's q-run is shifted up by s*(x_low+i) q-degrees. The x-window is UNCHANGED
 * (`cells` cells). Every s*(x_low+i) must be >= 0 (the Q[q] ground ring); a
 * negative shift -> SRMECH_ERR_BAD_INPUT. The caller pre-zeros the output + passes
 * each cell's output q-run CAPACITY (>= in_qlen + s*e) via out_off[cell] strides;
 * out_qlen[cell] <- the trimmed q-len. */
srmech_status_t srmech_qpoly_qshift(const srmech_bigint_t *a_n,
                                    const srmech_bigint_t *a_d,
                                    const size_t *a_qlen, size_t cells,
                                    int64_t s, int64_t x_low,
                                    srmech_bigint_t *out_n,
                                    srmech_bigint_t *out_d, size_t *out_qlen,
                                    const size_t *out_off, void *ws,
                                    size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_q_gosper — the q-analog of Gosper's indefinite hypergeometric
 * summation (the FIRST public op of the q-hypergeometric F929 reduction row,
 * the q-analog of the §76 srmech_gosper). The C peer of
 * srmech.amsc.q_gosper.q_gosper.
 *
 * Input: a q-hypergeometric term given by its TERM RATIO t(k+1)/t(k) = r(x) =
 * num(x)/den(x) as two Laurent polynomials in x = q^k over Q[q] (two QPoly),
 * each in the bridge wire form (concatenated ascending-q (num, den) runs +
 * a per-x-cell qlen[] array + the x_low offset). Output: when Sum t(k) HAS a
 * q-hypergeometric antidifference T(k) = R(q^k)*t(k) (so T(k+1)-T(k)=t(k)), the
 * rational CERTIFICATE R(x) = r_num(x)/r_den(x) (two QPoly, same bridge form);
 * else *out_has = 0.
 *
 * The algorithm is exact over the FIELD Q(q) (Koornwinder 1993): the
 * q-Gosper-Petkovsek normal form + the q-Gosper equation a(x)y(qx)-b(x/q)y(x)=
 * c(x), the rational leaf solve riding the PUBLIC srmech_qmat_rref over
 * caller-arena srmech_bigint (NO malloc, JPL Rule 3). Byte-identical to the
 * Python certificate at ANY magnitude.
 *
 * STANDALONE-COMPLETE + BOUNDED native scope: this rc55 peer COMPLETES the
 * canonical constant-ratio q-geometric case natively (r = num0(q)/den0(q),
 * x-degree 0; R = den0 / (num0 - den0)); for every other input it DECLINES
 * (*out_has = 0), and the Python op re-runs its COMPLETE pure-Q(q) path -- so a
 * has=0 is NEVER a definitive "no certificate" (the dispatch trusts only has=1),
 * mirroring the srmech_zeilberger / srmech_apagodu_zeilberger order-cap precedent.
 * The full higher-x-degree Q(q)[x] RREF is the owed everything-mirrors backlog.
 * Any residual overflow returns SRMECH_ERR_OVERFLOW (never a wrap).
 *
 * Additive symbol -> ABI unchanged (stays 3). License: MIT. ------- */

/* Minimum `ws_len` BYTES srmech_q_gosper needs for inputs of `coeff_limbs`
 * significant limbs per q-coefficient and a higher q-degree of `qdeg`. */
size_t srmech_q_gosper_ws_bound(size_t coeff_limbs, size_t qdeg);

/* The per-coefficient limb cap for each srmech_bigint in the rn / rd OUTPUT
 * q-run arrays, so a reduced certificate q-coefficient never overflows its slot. */
size_t srmech_q_gosper_out_cap(size_t coeff_limbs, size_t qdeg);

/* Compute the q-Gosper certificate for r = num/den.
 *   num_n/num_d (qlen num_qlen[], num_cells x-cells, x_low num_xlow): the term
 *     ratio NUMERATOR num(x) -- a QPoly bridge form (concatenated ascending-q runs)
 *   den_n/den_d ...: the term ratio DENOMINATOR den(x) (same form; den_cells > 0)
 * On success *out_has is set: 1 when a q-hypergeometric antidifference exists (then
 * rn and rd carry the reduced certificate R(x) = r_num(x) over r_den(x) as two
 * QPoly, with rn_qlen[]/out_rn_cells/out_rn_xlow + the rd peers), 0 when the peer
 * declines (the caller re-decides on the pure path). The caller sizes each output
 * q-run array to srmech_q_gosper_out_cap limbs; rn and rd hold one x-cell each in
 * the native (constant-ratio) scope. den_cells == 0 -> SRMECH_ERR_BAD_INPUT. */
srmech_status_t srmech_q_gosper(const srmech_bigint_t *num_n,
                                const srmech_bigint_t *num_d,
                                const size_t *num_qlen, size_t num_cells,
                                int64_t num_xlow,
                                const srmech_bigint_t *den_n,
                                const srmech_bigint_t *den_d,
                                const size_t *den_qlen, size_t den_cells,
                                int64_t den_xlow,
                                int *out_has,
                                srmech_bigint_t *rn_n, srmech_bigint_t *rn_d,
                                size_t *rn_qlen, size_t *out_rn_cells,
                                int64_t *out_rn_xlow,
                                srmech_bigint_t *rd_n, srmech_bigint_t *rd_d,
                                size_t *rd_qlen, size_t *out_rd_cells,
                                int64_t *out_rd_xlow,
                                void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_elliptic_gosper — the ELLIPTIC analog of Gosper's indefinite
 * hypergeometric summation (the FIRST engine op of the ELLIPTIC F929 reduction
 * row, the top of the base-axis degeneration tower elliptic -> q -> ordinary). The
 * C peer of srmech.amsc.elliptic_gosper.elliptic_gosper.
 *
 * Input: an elliptic-hypergeometric term given by its TERM RATIO t(n+1)/t(n) = r(x)
 * (x = q^n) as a FULL EllRatio -- a theta-quotient prod theta(a x;p)/prod theta(b x;p)
 * over an exact-Q monomial prefactor. The wire form mirrors srmech_ellratio_is_elliptic:
 * the interned symbol-table dimension `n_syms` (distinct symbols in the Python sorted
 * order so the dense exponent vector reproduces EllMonomial._sort_key); the x / p / q
 * interned indices (`xsym` / `psym` / `qsym`, -1 if absent); the num / den theta counts
 * (`n_num` / `n_den`); the flat exact-Q monomial coeff arrays `coeff_num` / `coeff_den`
 * (in order prefactor, num0..K-1, den0..L-1) + the flat int32 exponent rows `exps_flat`
 * (int32[n_syms] per monomial, same order). `coeff_cap` is the per-bigint limb cap.
 *
 * Output: when t(n) HAS an elliptic-hypergeometric antidifference T(n) = R(x)*t(n)
 * (so T(n+1) - T(n) = t(n)), the CERTIFICATE R(x) (a full EllRatio) satisfying the
 * elliptic Gosper equation R(qx)*r(x) - R(x) = 1, written out as `out_pref_num` /
 * `out_pref_den` (the prefactor exact-Q coeff) + `out_exps_flat` (the prefactor row,
 * then the *out_n_num num rows, then the *out_n_den den rows; each int32[n_syms]) +
 * the counts `*out_n_num` / `*out_n_den`. Else *out_has = 0.
 *
 * Reference (MPM-verified at build): George Gasper & Michael Schlosser, "Summation,
 * transformation, and expansion formulas for multibasic theta hypergeometric
 * series," Adv. Stud. Contemp. Math. (Kyungshang) 11, no. 1 (2005), 67-84
 * (arXiv:math/0505215) -- derived "using indefinite summation"; the key equation is
 * the Weierstrass three-term relation, Rosengren arXiv:1608.06161 Sec.1.4 Eq.1.12.
 *
 * GENUINE structural pipeline (a 1:1 mirror of _elliptic_gosper_pure, NOT the rc61
 * geometric-constant shell): (0) the elliptic-GEOMETRIC core (a constant scalar ratio
 * r = z -> R = z_den/(z_num - z_den); z == 1 declines); (1) PEEL the q-shift coboundary
 * to the theta-GP normal form r = (A/B)*(sigma C / C); (2) SOLVE the elliptic Gosper
 * key equation via the Weierstrass three-term relation, the <=8 chiral endianness
 * resolved against the EXACT residual ThetaSum is_zero verifier (srmech_thetasum_is_zero
 * -- the same no-hallucination standard). For an input outside the structurally-
 * decidable class it DECLINES (*out_has = 0), and the Python op re-runs its COMPLETE
 * pure-Python path + re-verifies any has=1 result in exact Q -- a has=0 is NEVER a
 * definitive "no certificate" (the dispatch trusts only has=1). Malloc-free (JPL Rule
 * 3): caller arena `ws` only; byte-identical to the Python certificate at ANY
 * magnitude. Any residual overflow / too-small arena -> SRMECH_ERR_OVERFLOW.
 *
 * Additive symbol -> ABI unchanged (stays 3). License: MIT. ------- */

/* Minimum `ws_len` BYTES srmech_elliptic_gosper needs for the given shape (n_syms
 * symbols, n_num + n_den input theta factors, coeff_limbs the per-coefficient
 * significant-limb estimate). */
size_t srmech_elliptic_gosper_ws_bound(size_t n_syms, size_t n_num, size_t n_den,
                                       size_t coeff_limbs);

/* The per-coefficient limb cap for each srmech_bigint in the OUTPUT (the cert prefactor
 * coeff), so the reduced certificate coefficient never overflows its slot. */
size_t srmech_elliptic_gosper_out_cap(size_t coeff_limbs);

/* Compute the GENUINE elliptic-Gosper certificate for the term ratio r (the full
 * EllRatio wire form). On success *out_has is set: 1 when t(n) has an antidifference
 * (then out_pref_num/out_pref_den + out_exps_flat + out_n_num/out_n_den carry the
 * certificate EllRatio), 0 when the peer declines (out of the structurally-decidable
 * class -> the caller re-decides on the pure path). `out_exps_cap_rows` is the row
 * capacity of the caller's out_exps_flat buffer (1 + max_num + max_den rows); too small
 * -> SRMECH_ERR_OVERFLOW. A required NULL pointer -> SRMECH_ERR_NULL_ARG. */
srmech_status_t srmech_elliptic_gosper(size_t n_syms, int xsym, int psym, int qsym,
                                       size_t n_num, size_t n_den,
                                       const srmech_bigint_t *coeff_num,
                                       const srmech_bigint_t *coeff_den,
                                       const int32_t *exps_flat, uint32_t coeff_cap,
                                       int *out_has, srmech_bigint_t *out_pref_num,
                                       srmech_bigint_t *out_pref_den,
                                       int32_t *out_exps_flat, size_t out_exps_cap_rows,
                                       size_t *out_n_num, size_t *out_n_den,
                                       void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_thetasum_is_zero — the C peer of the ThetaSum ADDITIVE theta-function
 * carrier's is_zero (srmech.amsc.thetasum.ThetaSum.is_zero), the load-bearing
 * EXACT decision under GENUINE elliptic creative telescoping. A 1:1 STRUCTURAL
 * MIRROR of the pure-Python Weierstrass three-term reduction partitioned by
 * quasi-periodicity class (Rosengren arXiv:1608.06161v3 §1.4 Eq. 1.12 + §1.3
 * Lemma 1.3.2) -- NOT a bounded shell: the C verdict equals the Python verdict
 * byte-for-byte, including the honest NOT-zero on a shape outside the clean +/-
 * -pair form the carrier reduces (sound, never false-accept; never a converging
 * eval). The whole peer is malloc-free (JPL Rule 3): every working monomial /
 * theta / term / rterm + bigint scratch is carved from the caller arena `ws`,
 * sized to the input (n_terms, n_thetas, n_syms) -- no compiled-in math cap.
 *
 * The cleared numerator is the only input is_zero inspects (self == 0 <=>
 * numerator == 0). The wire form: the interned symbol-table dimension `n_syms`
 * (the distinct symbols, in the Python sorted order so the dense exponent vector
 * reproduces the EllMonomial._sort_key tuple compare); the p / x / y interned
 * indices (`psym` / `xsym` / `ysym`, -1 if absent); the per-term theta counts
 * `term_nthetas[n_terms]`; the flat monomial coeff arrays `coeff_num` / `coeff_den`
 * (each monomial an exact-Q num/den as a srmech_bigint, in the order term0.pref,
 * term0.theta0..K, term1.pref, ...) + the flat exponent rows `exps_flat`
 * (int32[n_syms] per monomial, same order). `coeff_cap` is the per-bigint limb cap.
 * *out_is_zero = 1 iff the numerator is identically zero.
 *
 * Additive symbol -> ABI unchanged (stays 3). License: MIT. ------- */

/* Minimum `ws_len` BYTES srmech_thetasum_is_zero needs for the given shape
 * (n_syms symbols, n_terms numerator terms, max_thetas the largest per-term theta
 * count, coeff_limbs the per-coefficient significant-limb estimate). */
size_t srmech_thetasum_ws_bound(size_t n_syms, size_t n_terms, size_t max_thetas,
                                size_t coeff_limbs);

/* Decide whether the cleared ThetaSum numerator (the `n_terms` terms) is
 * identically zero. *out_is_zero = 1 iff == 0. Caller arena `ws`. n_terms == 0 ->
 * == 0 (the empty numerator). A required NULL pointer -> SRMECH_ERR_NULL_ARG; a
 * too-small arena -> SRMECH_ERR_OVERFLOW. */
srmech_status_t srmech_thetasum_is_zero(size_t n_syms, int xsym, int ysym, int psym,
                                        size_t n_terms, const size_t *term_nthetas,
                                        const srmech_bigint_t *coeff_num,
                                        const srmech_bigint_t *coeff_den,
                                        const int32_t *exps_flat,
                                        uint32_t coeff_cap, int *out_is_zero,
                                        void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_thetasum_is_zero_interpolation — the C peer of the ThetaSum
 * STRUCTURAL ELLIPTIC-INTERPOLATION is_zero completion (the pure-Python
 * srmech.amsc.thetasum._structural_is_zero / ThetaSum._is_zero_interpolation,
 * rc98). Where srmech_thetasum_is_zero is the SOUND +/- -pair fast path
 * (complete only for the single-variable class), THIS is the COMPLETE
 * multi-variable elliptic decision: a 1:1 STRUCTURAL MIRROR whose verdict
 * EQUALS the pure-Python _is_zero_interpolation verdict — True AND False —
 * so the Python dispatch trusts it directly.
 *
 * The algorithm (Rosengren arXiv:1608.06161v3 Prop 1.6.1 / eq 1.22 + Cor
 * 1.3.5): interpolate in ONE variable v at D_v+1 distinct points (a degree-D
 * theta vanishing at D+1 points is == 0) — a lower-variable is_zero RECURSES,
 * base = the single-variable degree-bound q-expansion. Nodes = the theta-FACTOR
 * ZEROS (killing terms via theta(1)=0) augmented with GLOBALLY-DISTINCT PRIMES
 * threaded through the recursion (so no two variables collide to a spurious
 * theta(1) — load-bearing for soundness). Recursion -> an EXPLICIT arena-mark
 * DFS (JPL Rule 1: no recursion). A too-small caller arena / coefficient cap ->
 * SRMECH_ERR_OVERFLOW and the caller falls to the COMPLETE pure oracle.
 *
 * Wire form + args are IDENTICAL to srmech_thetasum_is_zero. Additive symbol ->
 * ABI unchanged (stays 3). License: MIT. ------- */

/* Minimum `ws_len` BYTES srmech_thetasum_is_zero_interpolation needs for the given
 * shape. rc102 degree-aware sizer: `max_theta_sq_sum` is the base case's TRUE p-order
 * band degree — `ti_deg` = the max over terms of SUM of squared THETA-argument
 * exponents in a base variable (what ti_one_var actually consumes, k = max(deg-1,0) +
 * MARGIN), NOT `max_abs_exp` squared. A leaf with >=2 same-variable thetas has
 * SUM(e^2) >> max(e^2), so the pre-rc102 max_abs_exp^2 UNDER-sized k and the peer
 * false-declined (SRMECH_ERR_OVERFLOW); `max_abs_exp` (largest |exponent| across ALL
 * monomials incl. the prefactor) still bounds the w-band span + prefactor offset.
 * Additive symbol -> SRMECH_ABI_VERSION stays 3. */
size_t srmech_thetasum_is_zero_interpolation_ws_bound2(size_t n_syms, size_t n_terms,
                                                       size_t max_thetas,
                                                       size_t coeff_limbs,
                                                       size_t max_abs_exp,
                                                       size_t max_theta_sq_sum);

/* Legacy 5-arg entry (pre-rc102). Reproduces the old sizing byte-for-byte (passes
 * max_abs_exp^2 as the degree) so a stale ABI-3 caller / lib still links + behaves as
 * before; new callers use srmech_thetasum_is_zero_interpolation_ws_bound2. */
size_t srmech_thetasum_is_zero_interpolation_ws_bound(size_t n_syms, size_t n_terms,
                                                      size_t max_thetas,
                                                      size_t coeff_limbs,
                                                      size_t max_abs_exp);

/* Decide whether the cleared ThetaSum numerator is identically zero by the exact
 * structural elliptic interpolation (the COMPLETE multi-variable mirror).
 * *out_is_zero = 1 iff == 0. Caller arena `ws`. n_terms == 0 -> == 0. A required
 * NULL pointer -> SRMECH_ERR_NULL_ARG; a too-small arena -> SRMECH_ERR_OVERFLOW. */
srmech_status_t srmech_thetasum_is_zero_interpolation(
    size_t n_syms, int xsym, int ysym, int psym, size_t n_terms,
    const size_t *term_nthetas, const srmech_bigint_t *coeff_num,
    const srmech_bigint_t *coeff_den, const int32_t *exps_flat,
    uint32_t coeff_cap, int *out_is_zero, void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_thetasum_is_zero_interpolation_parallel — the rc103 CHIRALITY-
 * PRESERVING native PARALLEL fan-out for the structural elliptic-interpolation
 * is_zero (the FIRST realization of the general parallel_independent_dispatch
 * pattern). Peels the top branching levels of the interpolation tree into
 * independent sub-problems, runs the EXISTING sequential ti_decide DFS on each
 * over a PAL worker pool (deeper recursion stays serial), AND-folds with a
 * best-effort cancel flag (first False short-circuits, preserving the serial
 * early-exit); bit-identical serial fallback when the PAL has no threads OR
 * n_workers <= 1.
 *
 * TWO first-class CONTRACTS: (1) CARRIER — the verdict is BYTE-FOR-BYTE the
 * srmech_thetasum_is_zero_interpolation verdict (exact-Q, no float); (2)
 * CHIRALITY — the fan-out is ORDER-FREE (the interpolation +/- -pairs are the two
 * chiral halves): the verdict is invariant to the task enumeration/scheduling
 * order, neither chirality privileged. `task_order` (0 forward / 1 reverse) exists
 * to make the order-invariance contract testable. Does NOT lift the fundamental
 * n=2/N=2 wall (the documented frontier). Additive symbol -> ABI stays 3. ---- */

/* Minimum `ws_len` BYTES the parallel entry needs for the given shape + width:
 * a fixed control band (the task frontier) + n_workers disjoint arena slices
 * (each the ws_bound2 sizing + a replay margin). See the ws_bound2 doc for the
 * degree-aware sizing args. Additive symbol -> SRMECH_ABI_VERSION stays 3. */
size_t srmech_thetasum_is_zero_interpolation_parallel_ws_bound(
    size_t n_syms, size_t n_terms, size_t max_thetas, size_t coeff_limbs,
    size_t max_abs_exp, size_t max_theta_sq_sum, size_t n_workers);

/* Decide the cleared ThetaSum numerator's is_zero by the CHIRALITY-PRESERVING
 * PARALLEL structural elliptic interpolation. Wire form + verdict IDENTICAL to
 * srmech_thetasum_is_zero_interpolation. `n_workers` = the parallel width (clamped
 * to [1, 32]); `task_order` = 0 (forward) / 1 (reverse) task enumeration — the
 * verdict is invariant either way. *out_is_zero = 1 iff == 0. Caller arena `ws`
 * (size via ..._parallel_ws_bound). A too-small arena -> SRMECH_ERR_OVERFLOW. */
srmech_status_t srmech_thetasum_is_zero_interpolation_parallel(
    size_t n_syms, int xsym, int ysym, int psym, size_t n_terms,
    const size_t *term_nthetas, const srmech_bigint_t *coeff_num,
    const srmech_bigint_t *coeff_den, const int32_t *exps_flat,
    uint32_t coeff_cap, uint32_t n_workers, uint32_t task_order,
    int *out_is_zero, void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_ellratio_is_elliptic — the C peer of the EllRatio carrier's is_elliptic
 * (srmech.amsc.ellbase.EllRatio.is_elliptic), the load-bearing BALANCING / very-
 * well-poised predicate the elliptic reducers consult before attempting a closed
 * form. A 1:1 STRUCTURAL MIRROR of the pure-Python decision
 *
 *     is_elliptic() == (pshift() == self)
 *
 * — the term-ratio is a genuine elliptic function (a function on the elliptic curve
 * C-star / <p>) IFF it is invariant under the period shift x -> p*x. The C reproduces
 * the
 * Python decision byte-for-byte: it period-shifts the prefactor + every theta
 * argument (x -> p*x: a monomial gains p^{its x-exponent}), RE-CANONICALIZES (the
 * Theta.canonicalize quasi-periodicity + inversion rewrites fold each prefactor),
 * cancels matching canonical thetas between numerator and denominator, sorts the
 * survivors, and compares the canonical (prefactor, num-multiset, den-multiset) to
 * self's. NOT a bounded/numeric shell -- no convergence threshold on any decision
 * path. The shared exact-Q monomial + theta-canon kernels are the same single copy
 * srmech_thetasum_is_zero rides (promoted to srmech_ellbase.c). Malloc-free (JPL
 * Rule 3): every working monomial + bigint scratch is carved from the caller arena
 * `ws`, sized to the input (n_num, n_den, n_syms) -- no compiled-in math cap.
 *
 * Wire form: the interned symbol-table dimension `n_syms` (the distinct symbols, in
 * the Python sorted order so the dense exponent vector reproduces the
 * EllMonomial._sort_key tuple compare); the x / p interned indices (`xsym` / `psym`,
 * -1 if absent); the numerator / denominator theta-factor counts (`n_num` / `n_den`);
 * the flat monomial coeff arrays `coeff_num` / `coeff_den` (each an exact-Q num/den
 * as a srmech_bigint, in order prefactor, num0..K-1, den0..L-1) + the flat exponent
 * rows `exps_flat` (int32[n_syms] per monomial, same order). `coeff_cap` is the
 * per-bigint limb cap. *out_is_elliptic = 1 iff genuinely elliptic.
 *
 * Additive symbol -> ABI unchanged (stays 3). License: MIT. ------- */

/* Minimum `ws_len` BYTES srmech_ellratio_is_elliptic needs for the given shape
 * (n_syms symbols, n_num numerator + n_den denominator theta factors, coeff_limbs
 * the per-coefficient significant-limb estimate). */
size_t srmech_ellratio_ws_bound(size_t n_syms, size_t n_num, size_t n_den,
                                size_t coeff_limbs);

/* Decide whether the EllRatio (prefactor + the `n_num` numerator + `n_den`
 * denominator canonical theta arguments) is a genuine ELLIPTIC function (invariant
 * under x -> p*x). *out_is_elliptic = 1 iff elliptic. Caller arena `ws`. A required
 * NULL pointer -> SRMECH_ERR_NULL_ARG; a too-small arena -> SRMECH_ERR_OVERFLOW. */
srmech_status_t srmech_ellratio_is_elliptic(size_t n_syms, int xsym, int psym,
                                            size_t n_num, size_t n_den,
                                            const srmech_bigint_t *coeff_num,
                                            const srmech_bigint_t *coeff_den,
                                            const int32_t *exps_flat,
                                            uint32_t coeff_cap, int *out_is_elliptic,
                                            void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_ellratio_half_shift_response — the C peer of the EllRatio-carrier op
 * srmech.amsc.ellbase.half_shift_response (rc119; the #712 Dzhanibekov reader). A
 * C-MIRROR PARITY build: the multiplier EQUALS the pure-Python EllMonomial byte-
 * for-byte. Reads the EXACT monomial multiplier the carrier acquires under a HALF-
 * period translation of the torque-free torus (the harmonic⊗subharmonic cascade,
 * DLMF 22.4). Two axes: `axis` = 0 is the REAL 2K half-beat (the double-cover deck
 * transformation var -> -var: each canonical monomial's Class-K coeff picks up
 * (-1)^{var-exponent} -- a pure sign, bare iff every theta arg is EVEN in var);
 * `axis` = 1 is the NOME 2iK' half-beat (the carrier period shift var -> p*var, the
 * -x^-1-type Theta.canonicalize quasi-periodicity prefactor). The multiplier is
 * (shift(self) * self.inv()).prefactor; it is a BARE monomial iff the shifted
 * theta-parts equal self's (they cancel against self.inv()) -- *out_is_bare reports
 * it (0 -> the ratio is not half-shift-covariant along this axis/var, the boundary-
 * blind #712 finding for a chirality-EVEN reader is *out_is_bare=1 with a +1 sign).
 *
 * Wire form (mirrors srmech_ellratio_is_elliptic): the interned symbol-table
 * dimension `n_syms`; `varsym` / `psym` the interned indices of the shift variable
 * (the subharmonic half-var w for the real axis; the summation var x for the nome
 * axis) and the nome p (-1 if absent); `axis` the half-beat selector; the num / den
 * theta counts; the flat monomial coeff arrays `coeff_num` / `coeff_den` (exact-Q
 * num/den srmech_bigint, order prefactor, num0..K-1, den0..L-1) + the flat int32
 * exponent rows `exps_flat`. `coeff_cap` the per-bigint limb cap. Output: the
 * multiplier monomial's exact-Q coeff into `out_coeff_num` / `out_coeff_den` + its
 * dense int32[n_syms] exps row into `out_exps`; *out_is_bare the covariance flag.
 * Caller arena `ws` (size via srmech_ellratio_ws_bound, same shape).
 *
 * Additive symbol -> ABI unchanged (stays 3). License: MIT. ------- */
srmech_status_t srmech_ellratio_half_shift_response(
    size_t n_syms, int varsym, int psym, int axis, size_t n_num, size_t n_den,
    const srmech_bigint_t *coeff_num, const srmech_bigint_t *coeff_den,
    const int32_t *exps_flat, uint32_t coeff_cap, int *out_is_bare,
    srmech_bigint_t *out_coeff_num, srmech_bigint_t *out_coeff_den,
    int32_t *out_exps, void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_elliptic_lagrange_basis — the C peer of the EllRatio-carrier op
 * srmech.amsc.ellbase.elliptic_lagrange_basis (rc66, shipped Python-only; its C
 * mirror is owed by the everything-mirrors same-rc discipline -> rc67). A
 * C-MIRROR PARITY build (NOT a new algorithm): it reproduces the EXISTING,
 * already-shipped pure-Python carrier byte-for-byte.
 *
 * Returns the k = `k` elliptic Lagrange interpolation basis EllRatios of the
 * k-dimensional space V_t = { f analytic on C* : f(p*z) = t*z^{-k}*f(z) } at the
 * k nodes (Rosengren arXiv:1608.06161v3 Sec.1.3 Corollary 1.3.5). For each i,
 * with others = { points[j] : j != i } and prod = PROD others, the i-th element
 * places its k theta zeros at { z/u_j : j != i } plus the BALANCING point
 * v_i = (-1)^k * t / prod (so the product of the k zeros equals (-1)^k * t):
 *   L_i = EllRatio( num = [ theta(z * u_j^{-1}) : j != i ] + [ theta(z * v_i^{-1}) ] )
 * with the default unit prefactor; the EllRatio construction folds each theta's
 * canonicalize prefactor, cancels matching thetas, and sorts the survivors. Pure
 * composition of the shared srmech_ellbase_* monomial algebra + er_build.
 *
 * Wire form (mirrors srmech_ellratio_is_elliptic): the interned symbol-table
 * dimension `n_syms` (distinct symbols in the Python sorted-symbol-NAME order so
 * the dense exponent vector reproduces EllMonomial._sort_key); `varsym` / `psym`
 * the interned indices of the interpolation variable `var` and the nome `p`
 * (-1 if absent); the node count `k`; the flat point-monomial coeff arrays
 * `pt_coeff_num` / `pt_coeff_den` (point0..k-1) + the flat int32 exponent rows
 * `pt_exps_flat` (int32[n_syms] per point); the multiplier monomial `mult_num`
 * / `mult_den` / `mult_exps`. `coeff_cap` is the per-bigint limb cap.
 *
 * Output: the k basis EllRatios written flat as a single ROW stream. Each emitted
 * monomial (a prefactor or a theta argument) contributes ONE row: its exact-Q coeff
 * into `out_coeff_num` / `out_coeff_den`[row] AND its dense int32[n_syms] exponent
 * row into `out_exps_flat`, in the order, per element i: its prefactor row, then
 * out_n_num[i] num-theta rows, then out_n_den[i] den-theta rows. The per-element
 * theta counts come back in `out_n_num[i]` / `out_n_den[i]`. (The coeff travels with
 * EVERY row -- a theta ARGUMENT can carry a non-unit Class-K coeff, e.g. the
 * balancing arg z*v_i^{-1} with v_i = (-1)^k*t/PROD others -- so the coeff is NOT
 * assumed 1.) `out_exps_cap_rows` is the row capacity of the caller's out_exps_flat
 * / out_coeff buffers; too small -> SRMECH_ERR_OVERFLOW. k == 0 -> SRMECH_ERR_NULL_ARG
 * (Python raises ValueError). A required NULL pointer -> SRMECH_ERR_NULL_ARG; a
 * too-small arena -> SRMECH_ERR_OVERFLOW.
 *
 * The (-1)^k sign is a Class-K parity branch (an int +/-1), never abs()/fabs().
 * Malloc-free (JPL Rule 3): caller arena `ws` only, sized to (k, n_syms) -- no
 * compiled-in cap. Additive symbol -> ABI unchanged (stays 3). License: MIT. ---- */

/* Minimum `ws_len` BYTES srmech_elliptic_lagrange_basis needs for the given shape
 * (n_syms symbols, k interpolation nodes, coeff_limbs the per-coefficient
 * significant-limb estimate). */
size_t srmech_elliptic_lagrange_basis_ws_bound(size_t n_syms, size_t k,
                                               size_t coeff_limbs);

/* Build the k elliptic Lagrange basis EllRatios at the k nodes (see above). */
srmech_status_t srmech_elliptic_lagrange_basis(size_t n_syms, int varsym, int psym,
                                               size_t k,
                                               const srmech_bigint_t *pt_coeff_num,
                                               const srmech_bigint_t *pt_coeff_den,
                                               const int32_t *pt_exps_flat,
                                               const srmech_bigint_t *mult_num,
                                               const srmech_bigint_t *mult_den,
                                               const int32_t *mult_exps,
                                               uint32_t coeff_cap,
                                               srmech_bigint_t *out_coeff_num,
                                               srmech_bigint_t *out_coeff_den,
                                               int32_t *out_exps_flat,
                                               size_t out_exps_cap_rows,
                                               size_t *out_n_num, size_t *out_n_den,
                                               void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_elliptic_cauchy_determinant — the C peer of the EllRatio-carrier op
 * srmech.amsc.elliptic_determinant.elliptic_cauchy_determinant (rc94), the
 * ELLIPTIC-DETERMINANT primitive (foundation of the multivariable Cn elliptic
 * reduction row). A C-MIRROR PARITY build (NOT a new algorithm): it constructs
 * the EXACT closed form the pure-Python op builds, byte-for-byte.
 *
 * For distinct x_1..x_n, y_1..y_n and a parameter t (Rosengren,
 * arXiv:1608.06161v3, Exercise 1.6.6; classically Frobenius 1882):
 *   det_{1<=i,j<=n}[theta(t*x_i*y_j;p)/theta(x_i*y_j;p)]
 *     = theta(t;p)^{n-1} * theta(t*PRODx*PRODy;p)
 *       * PROD_{i<j}[x_j*y_j*theta(x_i/x_j;p)*theta(y_i/y_j;p)]
 *       / PROD_{i,j}theta(x_i*y_j;p).
 * This op CONSTRUCTS the right-hand side as one EllRatio: the EllMonomial
 * prefactor PROD_{i<j} x_j*y_j, the numerator thetas (theta(t) x (n-1),
 * theta(t*PRODx*PRODy), theta(x_i/x_j) + theta(y_i/y_j) for i<j) and the
 * denominator thetas theta(x_i*y_j) for all i,j; er_build (the EllRatio.__init__
 * mirror) folds each theta's canonicalize prefactor, cancels matching thetas,
 * sorts the survivors. Pure composition of the shared srmech_ellbase_* monomial
 * algebra + er_build.
 *
 * Wire form (mirrors srmech_elliptic_lagrange_basis): the interned symbol-table
 * dimension `n_syms`; `psym` the interned index of the nome p (-1 if absent);
 * `n` the matrix dimension; the parameter monomial `t_num` / `t_den` / `t_exps`;
 * the flat x-monomial coeff arrays `xs_num` / `xs_den` (x0..x_{n-1}) + the flat
 * int32 exponent rows `xs_exps_flat` (int32[n_syms] per x); likewise the y's.
 * `coeff_cap` is the per-bigint limb cap.
 *
 * Output: the single closed-form EllRatio written flat as a ROW stream. Each
 * emitted monomial (the prefactor or a theta argument) contributes ONE row: its
 * exact-Q coeff into `out_coeff_num` / `out_coeff_den`[row] AND its dense
 * int32[n_syms] exponent row into `out_exps_flat`, in the order: the prefactor
 * row, then `*out_n_num` num-theta rows, then `*out_n_den` den-theta rows. The
 * survivor theta counts come back in `*out_n_num` / `*out_n_den`. (The coeff
 * travels with EVERY row -- a canonicalized theta argument can carry a non-unit
 * Class-K coeff.) `out_exps_cap_rows` is the row capacity; too small ->
 * SRMECH_ERR_OVERFLOW. n == 0 -> SRMECH_ERR_NULL_ARG (Python raises ValueError);
 * a required NULL pointer -> SRMECH_ERR_NULL_ARG; a too-small arena ->
 * SRMECH_ERR_OVERFLOW.
 *
 * Sign travels in the Class-K coeff branch, never abs()/fabs(). Malloc-free
 * (JPL Rule 3): caller arena `ws` only, sized to (n, n_syms) -- no compiled-in
 * cap. Additive symbol -> ABI unchanged (stays 3). License: MIT. ---- */

/* Minimum `ws_len` BYTES srmech_elliptic_cauchy_determinant needs for the given
 * shape (n_syms symbols, n the matrix dimension, coeff_limbs the per-coefficient
 * significant-limb estimate). */
size_t srmech_elliptic_cauchy_determinant_ws_bound(size_t n_syms, size_t n,
                                                   size_t coeff_limbs);

/* Build the single Frobenius elliptic Cauchy determinant EllRatio (see above). */
srmech_status_t srmech_elliptic_cauchy_determinant(size_t n_syms, int psym, size_t n,
                                                   const srmech_bigint_t *t_num,
                                                   const srmech_bigint_t *t_den,
                                                   const int32_t *t_exps,
                                                   const srmech_bigint_t *xs_num,
                                                   const srmech_bigint_t *xs_den,
                                                   const int32_t *xs_exps_flat,
                                                   const srmech_bigint_t *ys_num,
                                                   const srmech_bigint_t *ys_den,
                                                   const int32_t *ys_exps_flat,
                                                   uint32_t coeff_cap,
                                                   srmech_bigint_t *out_coeff_num,
                                                   srmech_bigint_t *out_coeff_den,
                                                   int32_t *out_exps_flat,
                                                   size_t out_exps_cap_rows,
                                                   size_t *out_n_num, size_t *out_n_den,
                                                   void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_elliptic_partial_fraction — the C peer of the ThetaSum-returning op
 * srmech.amsc.elliptic_partial_fraction.elliptic_partial_fraction (rc95), the
 * ELLIPTIC PARTIAL-FRACTION expansion (the reduction ENGINE of the multivariable
 * Cn elliptic reduction row). A C-MIRROR PARITY build (NOT a new algorithm): it
 * constructs the EXACT n theta-quotient TERMS the pure-Python op builds, byte-for-
 * byte; the Python side SUMS them into the ThetaSum (there is NO ThetaSum-
 * CONSTRUCTION C surface, so the peer returns the n EllRatio TERMS, exactly like
 * srmech_elliptic_lagrange_basis returns its k basis EllRatios).
 *
 * For distinct z_1..z_n, y_1..y_n and the variable x (Rosengren,
 * arXiv:1608.06161v3, Proposition 1.6.1 + Eq. 1.22):
 *   PROD_{k=1}^n theta(x/z_k;p)/theta(x/y_k;p)
 *     = 1/theta(Y/Z;p) * SUM_{j=1}^n
 *         [PROD_k theta(y_j/z_k;p) / PROD_{k!=j} theta(y_j/y_k;p)]
 *         * [theta(x*Y/(y_j*Z);p) / theta(x/y_j;p)],   Y=PROD y, Z=PROD z.
 * Each summand j is an EllRatio (unit prefactor): num thetas theta(y_j/z_k) all k
 * + theta(x*Y/(y_j*Z)) (n+1); den thetas theta(y_j/y_k) k!=j + theta(x/y_j) +
 * theta(Y/Z) (n+1). er_build folds each theta's canonicalize prefactor, cancels
 * matching thetas, sorts the survivors. Pure composition of the shared
 * srmech_ellbase_* monomial algebra + er_build.
 *
 * Wire form (mirrors srmech_elliptic_lagrange_basis): the interned symbol-table
 * dimension `n_syms`; `psym` the interned index of the nome p (-1 if absent);
 * `n` the term count; the variable monomial `x_num` / `x_den` / `x_exps`; the
 * flat z-monomial coeff arrays `zs_num` / `zs_den` (z0..z_{n-1}) + the flat int32
 * exponent rows `zs_exps_flat` (int32[n_syms] per z); likewise the y's.
 * `coeff_cap` is the per-bigint limb cap.
 *
 * Output: the n TERM EllRatios written out flat -- per term j, `out_n_num[j]` /
 * `out_n_den[j]` the survivor theta counts, and the canonical rows appended (per
 * term: its prefactor row, then its out_n_num[j] num rows, then its out_n_den[j]
 * den rows; each row carries its exact-Q coeff AND its dense int32[n_syms]
 * exponent row). `out_exps_cap_rows` is the row capacity; too small ->
 * SRMECH_ERR_OVERFLOW. n == 0 -> SRMECH_ERR_NULL_ARG (Python raises ValueError);
 * a required NULL pointer -> SRMECH_ERR_NULL_ARG; a too-small arena ->
 * SRMECH_ERR_OVERFLOW.
 *
 * Sign travels in the Class-K coeff branch, never abs()/fabs(). Malloc-free
 * (JPL Rule 3): caller arena `ws` only, sized to (n, n_syms) -- no compiled-in
 * cap. Additive symbol -> ABI unchanged (stays 3). License: MIT. ---- */

/* Minimum `ws_len` BYTES srmech_elliptic_partial_fraction needs for the given
 * shape (n_syms symbols, n the term count, coeff_limbs the per-coefficient
 * significant-limb estimate). */
size_t srmech_elliptic_partial_fraction_ws_bound(size_t n_syms, size_t n,
                                                 size_t coeff_limbs);

/* Build the n Frobenius/Rosengren elliptic partial-fraction TERM EllRatios
 * (see above); the Python side sums them into the returned ThetaSum. */
srmech_status_t srmech_elliptic_partial_fraction(size_t n_syms, int psym, size_t n,
                                                 const srmech_bigint_t *x_num,
                                                 const srmech_bigint_t *x_den,
                                                 const int32_t *x_exps,
                                                 const srmech_bigint_t *zs_num,
                                                 const srmech_bigint_t *zs_den,
                                                 const int32_t *zs_exps_flat,
                                                 const srmech_bigint_t *ys_num,
                                                 const srmech_bigint_t *ys_den,
                                                 const int32_t *ys_exps_flat,
                                                 uint32_t coeff_cap,
                                                 srmech_bigint_t *out_coeff_num,
                                                 srmech_bigint_t *out_coeff_den,
                                                 int32_t *out_exps_flat,
                                                 size_t out_exps_cap_rows,
                                                 size_t *out_n_num, size_t *out_n_den,
                                                 void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_multivariate_elliptic_jackson — the C peer of the EllRatio-carrier op
 * srmech.amsc.multivariate_elliptic_jackson.multivariate_elliptic_jackson (rc96),
 * the eq-5 Cn elliptic Jackson summation reducer (the CAPSTONE of the
 * multivariable (root-system Cn) elliptic reduction row). A C-MIRROR PARITY
 * build (NOT a new algorithm): it constructs the EXACT closed form the pure-
 * Python op builds, byte-for-byte.
 *
 * For the parameters a, b, c, d and the base variables x, q (Rosengren, A
 * multivariable elliptic summation formula, arXiv:math/0101073, Theorem 2.1,
 * Eq. 5), the balanced Cn very-well-poised elliptic Jackson summation reduces
 * to the theta-quotient product
 *   (aq, aq/bc, aq/bd, aq/cd; q, x)_{N^n} / (aq/b, aq/c, aq/d, aq/bcd; q, x)_{N^n},
 * with the vector elliptic Pochhammer
 *   (u; q, x)_{N^n} = PROD_{j=1}^n PROD_{i=0}^{N-1} theta(u*x^{1-j}*q^i; p).
 * This op CONSTRUCTS the right-hand side as one EllRatio: the unit prefactor,
 * the numerator thetas (the vector Pochhammer of each of aq, aq/bc, aq/bd,
 * aq/cd) and the denominator thetas (the vector Pochhammer of each of aq/b,
 * aq/c, aq/d, aq/bcd); er_build (the EllRatio.__init__ mirror) folds each
 * theta's canonicalize prefactor, cancels matching thetas, sorts the survivors.
 * Pure composition of the shared srmech_ellbase_* monomial algebra + er_build.
 *
 * Wire form: the interned symbol-table dimension `n_syms`; `psym` the interned
 * index of the nome p (-1 if absent); the positive ints `N` (partition ceiling)
 * + `n` (rank); each of the 6 parameter monomials a/b/c/d/x/q as a
 * (num, den) srmech_bigint pair + its flat int32[n_syms] exponent row.
 * `coeff_cap` is the per-bigint limb cap.
 *
 * Output: the single closed-form EllRatio written flat as a ROW stream (the
 * prefactor row, then `*out_n_num` num-theta rows, then `*out_n_den` den-theta
 * rows), each row carrying its exact-Q coeff (out_coeff_num / out_coeff_den) AND
 * its dense int32[n_syms] exponent row (out_exps_flat). `out_exps_cap_rows` is
 * the row capacity; too small -> SRMECH_ERR_OVERFLOW. N == 0 or n == 0 ->
 * SRMECH_ERR_NULL_ARG (Python raises ValueError); a required NULL pointer ->
 * SRMECH_ERR_NULL_ARG; a too-small arena -> SRMECH_ERR_OVERFLOW.
 *
 * Sign travels in the Class-K coeff branch, never abs()/fabs(). Malloc-free
 * (JPL Rule 3): caller arena `ws` only, sized to (N, n, n_syms) -- no compiled-in
 * cap. Additive symbol -> ABI unchanged (stays 3). License: MIT. ---- */

/* Minimum `ws_len` BYTES srmech_multivariate_elliptic_jackson needs for the given
 * shape (n_syms symbols, N the partition ceiling, n the rank, coeff_limbs the
 * per-coefficient significant-limb estimate). */
size_t srmech_multivariate_elliptic_jackson_ws_bound(size_t n_syms, size_t N, size_t n,
                                                     size_t coeff_limbs);

/* Build the single balanced Cn elliptic Jackson summation EllRatio (see above). */
srmech_status_t srmech_multivariate_elliptic_jackson(size_t n_syms, int psym, size_t N,
                                                     size_t n,
                                                     const srmech_bigint_t *a_num,
                                                     const srmech_bigint_t *a_den,
                                                     const int32_t *a_exps,
                                                     const srmech_bigint_t *b_num,
                                                     const srmech_bigint_t *b_den,
                                                     const int32_t *b_exps,
                                                     const srmech_bigint_t *c_num,
                                                     const srmech_bigint_t *c_den,
                                                     const int32_t *c_exps,
                                                     const srmech_bigint_t *d_num,
                                                     const srmech_bigint_t *d_den,
                                                     const int32_t *d_exps,
                                                     const srmech_bigint_t *x_num,
                                                     const srmech_bigint_t *x_den,
                                                     const int32_t *x_exps,
                                                     const srmech_bigint_t *q_num,
                                                     const srmech_bigint_t *q_den,
                                                     const int32_t *q_exps,
                                                     uint32_t coeff_cap,
                                                     srmech_bigint_t *out_coeff_num,
                                                     srmech_bigint_t *out_coeff_den,
                                                     int32_t *out_exps_flat,
                                                     size_t out_exps_cap_rows,
                                                     size_t *out_n_num, size_t *out_n_den,
                                                     void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_elliptic_recurrence_8w7 — the ELLIPTIC Sigma-row ORDER-1 RECURRENCE op for the
 * Frenkel–Turaev ₈ω₇ summation. The C peer of
 * srmech.amsc.elliptic_recurrence.elliptic_recurrence_8w7 — a 1:1 STRUCTURAL MIRROR of
 * the pure-Python recognize-decompose-construct pipeline (NOT a coefficient nullspace
 * solve, which is provably dead for the elliptic case; the anti-brute-force discipline).
 *
 * Input: the ₈ω₇ summand's TERM RATIO t(n+1)/t(n) = r(x) (x = q^n) as a full EllRatio (a
 * theta-quotient prod theta(a x;p)/prod theta(b x;p) over an exact-Q monomial prefactor).
 * The wire form mirrors srmech_elliptic_gosper but ADDS the y interned index (the
 * recurrence axis y = q^n): the interned symbol-table dimension `n_syms` + the x/p/q/y
 * interned indices (-1 if absent) + the num/den theta counts + the flat exact-Q coeff
 * arrays + the flat int32 exponent rows (in the order prefactor, num0..K-1, den0..L-1).
 * `coeff_cap` is the per-bigint limb cap.
 *
 * Output: when r is a canonical ₈ω₇, the order-1 recurrence COEFFICIENT rho (a full
 * EllRatio in y = q^n: its prefactor exact-Q coeff into out_pref_num/out_pref_den + its
 * exponent row, then the num/den canonical theta-argument exponent rows into
 * out_exps_flat, per-side counts in out_n_num/out_n_den) such that f(n+1) = rho(n)*f(n);
 * else *out_has = 0.
 *
 * The GENUINE pipeline (mirrors _elliptic_recurrence_8w7_pure):
 *   (1) RECOGNIZE + DECOMPOSE the very-well-poised ₈ω₇: the unique den factor
 *       theta(a x^2) (x-exponent magnitude 2) gives the base a; the linear den factors
 *       theta(a q x u^-1) (x-exponent magnitude 1) give aq*real_base^-1 = u; drop the
 *       (q)-factor (u == a) + the y-carrying (n-dependent) params, leaving the three FREE
 *       params [b, c, d]. Out of class (no unique quadratic core / != 3 free) -> *out_has=0.
 *   (2) CONSTRUCT rho from the elementary symmetric functions s2 = {bc, bd, cd}, s3 = bcd
 *       (Warnaar, Constr. Approx. 18 (2002) 479-502, Cor 2.2): num endpoints
 *       {aq} U {aq/bc, aq/bd, aq/cd}; den {aq/b, aq/c, aq/d} U {aq/bcd}; rho =
 *       prod theta(end*y;p) over num / prod theta(end*y;p) over den. The construction IS
 *       the answer (decompose-and-compute, no undetermined-coefficient solve).
 *
 * The VERIFICATION GATE (rho(n) == f(n+1)/f(n) for the ₈ω₇ sum) is on the PYTHON side (it
 * needs the truncated-theta eval oracle); the C peer constructs the EXACT rho and the
 * Python trusts it ONLY after rebuilding it byte-for-byte AND re-running the gate in exact
 * Q. A *out_has = 0 is NEVER a definitive "no recurrence" (the Python re-decides on its
 * COMPLETE pure path); on any overflow / too-small arena the peer returns
 * SRMECH_ERR_OVERFLOW and the Python re-runs the pure path. A required NULL pointer ->
 * SRMECH_ERR_NULL_ARG.
 *
 * Reference (MPM-verified at build): S. Ole Warnaar, "Summation and transformation
 * formulas for elliptic hypergeometric series," Constr. Approx. 18 (2002) 479-502
 * (arXiv:math/0001006), Corollary 2.2.
 *
 * PURE COMPOSITION of the shared srmech_ellbase_* exact-Q monomial algebra + er_build
 * (the same single copy srmech_elliptic_gosper / srmech_ellratio_is_elliptic ride).
 * Malloc-free (JPL Rule 3): caller arena `ws` only. The "magnitude 2 / magnitude 1"
 * x-power test is a Class-K parity branch (e == mag || e == -mag), never abs()/fabs().
 * Additive symbol -> ABI unchanged (stays 3). License: MIT. ---- */

/* Minimum `ws_len` BYTES srmech_elliptic_recurrence_8w7 needs for the given shape (n_syms
 * symbols, n_num + n_den input theta factors, coeff_limbs the per-coefficient
 * significant-limb estimate). */
size_t srmech_elliptic_recurrence_8w7_ws_bound(size_t n_syms, size_t n_num, size_t n_den,
                                               size_t coeff_cap);

/* The per-coefficient limb cap for each srmech_bigint in the OUTPUT (the rho prefactor). */
size_t srmech_elliptic_recurrence_8w7_out_cap(size_t coeff_limbs);

/* Find the order-1 ₈ω₇ recurrence coefficient rho (see above). */
srmech_status_t srmech_elliptic_recurrence_8w7(size_t n_syms, int xsym, int psym,
                                               int qsym, int ysym,
                                               size_t n_num, size_t n_den,
                                               const srmech_bigint_t *coeff_num,
                                               const srmech_bigint_t *coeff_den,
                                               const int32_t *exps_flat,
                                               uint32_t coeff_cap, int *out_has,
                                               srmech_bigint_t *out_pref_num,
                                               srmech_bigint_t *out_pref_den,
                                               int32_t *out_exps_flat,
                                               size_t out_exps_cap_rows,
                                               size_t *out_n_num, size_t *out_n_den,
                                               void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_elliptic_zeilberger — the ELLIPTIC Sigma-row CREATIVE-TELESCOPING op for the
 * Frenkel-Turaev 8w7 summation (the C peer of
 * srmech.amsc.elliptic_zeilberger.elliptic_zeilberger). The order-1 recurrence
 * f(n+1) = rho(n)*f(n) PLUS an EXACT connection-coefficient certificate that PROVES it
 * (the ThetaSum.is_zero decision, NOT rc68's 1e-9 numerical convergence gate).
 *
 * Input: the 8w7 term ratio r(x) = t(n+1)/t(n) (x = q^n) as the SAME full EllRatio wire
 * form srmech_elliptic_recurrence_8w7 parses (n_syms + the x/p/q/y interned indices + the
 * num/den theta counts + the flat exact-Q coeff arrays + the flat int32 exponent rows),
 * PLUS the two extra interned indices nsym/ksym for the recurrence index symbols N = q^n,
 * K = q^k the connection-coefficient certificate carries (force-interned by the caller;
 * the input ratio's own monomials are zero in those two columns).
 *
 * Output: *out_has = 1 iff r is a canonical 8w7 (the SAME recognize-decompose pipeline
 * srmech_elliptic_recurrence_8w7 runs) AND the connection-coefficient inductive-step
 * certificate (Rosengren arXiv:1608.06161 Eq.(2.12)-(2.14) -> Eq.(1.12), the cleared
 * +/- pair split) decides EXACTLY ZERO via the shared srmech_thetasum_is_zero kernel;
 * else *out_has = 0 (out of class / cert did not close -> the Python re-decides on its
 * complete pure path AND builds + re-verifies rho there). The C peer does NOT emit rho
 * (the Python builds it; the peer's novelty is the EXACT certificate decision).
 *
 * PURE COMPOSITION of the shared srmech_ellbase_* exact-Q monomial algebra + er_build +
 * srmech_thetasum_is_zero (the same single copies srmech_elliptic_recurrence /
 * srmech_elliptic_gosper ride). Malloc-free (JPL Rule 3): caller arena `ws` only. The
 * "magnitude 2 / magnitude 1" x-power test + the +/-1 prefactor sign are Class-K parity
 * branches, never abs()/fabs(). Additive symbol -> ABI unchanged (stays 3). License: MIT. */

/* Minimum `ws_len` BYTES srmech_elliptic_zeilberger needs for the given shape (n_syms
 * symbols, n_num + n_den input theta factors, coeff_cap the per-coefficient significant-
 * limb estimate). */
size_t srmech_elliptic_zeilberger_ws_bound(size_t n_syms, size_t n_num, size_t n_den,
                                           size_t coeff_cap);

/* Decide the order-1 ₈ω₇ recurrence + its EXACT connection-coefficient certificate (see
 * above). *out_has = 1 iff recognized AND the certificate is exactly zero. */
srmech_status_t srmech_elliptic_zeilberger(size_t n_syms, int xsym, int psym, int qsym,
                                           int ysym, int nsym, int ksym,
                                           size_t n_num, size_t n_den,
                                           const srmech_bigint_t *coeff_num,
                                           const srmech_bigint_t *coeff_den,
                                           const int32_t *exps_flat, uint32_t coeff_cap,
                                           int *out_has, void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_elliptic_wz_certificate — the ELLIPTIC Sigma-row IDENTITY-PROOF op for the
 * Frenkel-Turaev 8w7 SUMMATION (the C peer of
 * srmech.amsc.elliptic_wz_certificate.elliptic_wz_certificate). Where
 * srmech_elliptic_zeilberger proves the order-1 RECURRENCE f(n+1) = rho(n)*f(n), this op
 * proves the full SUMMATION IDENTITY sum_{k=0}^n F(n,k) = cf(n) -- the elliptic analogue
 * of srmech_wz_certificate (the Sec.76 ordinary/q identity-proof rung). The DISTINCT
 * OUTPUT is the closed form cf(n) = (aq, aq/bc, aq/bd, aq/cd; q,p)_n /
 * (aq/b, aq/c, aq/d, aq/bcd; q,p)_n (Warnaar Cor 2.2 / Rosengren Thm 2.3.1); the Python
 * builds those Pochhammer endpoints on its side (the analogue of "the Python builds rho"),
 * so this C peer -- exactly as srmech_elliptic_zeilberger -- returns ONLY the verdict.
 *
 * Input: identical to srmech_elliptic_zeilberger (the 8w7 term ratio r(x) = t(n+1)/t(n)
 * as the full EllRatio wire form + the nsym/ksym certificate index symbols N = q^n,
 * K = q^k).
 *
 * Output: *out_has = 1 iff r is a canonical 8w7 (the SAME recognize-decompose pipeline)
 * AND the connection-coefficient inductive-step certificate (Rosengren arXiv:1608.06161
 * Eq.(2.12)-(2.14) -> Eq.(1.12), the cleared +/- pair split) decides EXACTLY ZERO via the
 * shared srmech_thetasum_is_zero kernel; else *out_has = 0 (out of class / cert did not
 * close -> the Python re-decides on its complete pure path AND builds + re-verifies the
 * closed form there). The inductive step (the certificate) + the terminating base case
 * C^0_0 = 1 are the complete exact proof of the summation identity.
 *
 * PURE COMPOSITION of the shared srmech_ellbase_* exact-Q monomial algebra + er_build +
 * srmech_thetasum_is_zero (the same single copies srmech_elliptic_zeilberger /
 * srmech_elliptic_gosper ride). Malloc-free (JPL Rule 3): caller arena `ws` only. The
 * "magnitude 2 / magnitude 1" x-power test + the +/-1 prefactor sign are Class-K parity
 * branches, never abs()/fabs(). Additive symbol -> ABI unchanged (stays 3). License: MIT. */

/* Minimum `ws_len` BYTES srmech_elliptic_wz_certificate needs for the given shape (n_syms
 * symbols, n_num + n_den input theta factors, coeff_cap the per-coefficient significant-
 * limb estimate). */
size_t srmech_elliptic_wz_certificate_ws_bound(size_t n_syms, size_t n_num, size_t n_den,
                                               size_t coeff_cap);

/* Decide the 8w7 SUMMATION identity via its EXACT connection-coefficient certificate (see
 * above). *out_has = 1 iff recognized AND the certificate is exactly zero. */
srmech_status_t srmech_elliptic_wz_certificate(size_t n_syms, int xsym, int psym, int qsym,
                                               int ysym, int nsym, int ksym,
                                               size_t n_num, size_t n_den,
                                               const srmech_bigint_t *coeff_num,
                                               const srmech_bigint_t *coeff_den,
                                               const int32_t *exps_flat, uint32_t coeff_cap,
                                               int *out_has, void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_carrier_spectrum — the OPERAND-side dual of the_one (the C peer of
 * srmech.amsc.carrier_spectrum.carrier_spectrum). A 1:1 STRUCTURAL MIRROR of the
 * pure-Python CHANNEL READ: the harmonic occupancy of a carrier element under the
 * shift-Laplacian, in two orthogonal channels.
 *
 * Input: the carrier element as a full EllRatio wire form (the SAME wire form
 * srmech_elliptic_recurrence_8w7 parses: the interned symbol-table dimension `n_syms`
 * + the x/p/q/y interned indices (-1 if absent) + the num/den theta counts + the flat
 * exact-Q coeff arrays + the flat int32 exponent rows, in the order prefactor,
 * num0..K-1, den0..L-1). `coeff_cap` is the per-bigint limb cap.
 *
 * Output:
 *   - Channel 1 (Class-I) the cyclic sigma-EIGENSPECTRUM: the distinct x-exponents k
 *     (sigma(x^k) = q^k x^k; k = 0 the shift-Laplacian L = sigma-1 kernel) into
 *     out_cyclic[0..*out_n_cyclic-1] (cyclic_cap the slot cap);
 *   - Channel 2 (Class-L) the quasi-periodic p-CHARACTER BLOCK of each theta-factor:
 *     the net period-multiplier exponent row (under x -> p x AND y -> p y, Rosengren
 *     Eq. 1.6 via the shared theta-canon), q-coordinate STRIPPED (sigma-invariant),
 *     one length-n_syms int32 row per num-then-den theta into out_block_flat
 *     (block_cap_rows the row cap); *out_n_thetas the live theta count.
 * *out_has = 1 on a successful read; *out_has = 0 (p absent / over native scope) ->
 * the Python re-decides on its COMPLETE pure path. On overflow / too-small arena the
 * peer returns SRMECH_ERR_OVERFLOW; a required NULL pointer -> SRMECH_ERR_NULL_ARG.
 *
 * The Python side rebuilds the cyclic dict + groups the thetas by the block rows, and
 * trusts the native result ONLY after the pure rebuild reproduces the same spectrum
 * byte-for-byte (the channels are a pure exponent-lattice read). The block-DECOMPOSED
 * key-equation SOLVE (CarrierSpectrum.solve_key_equation) is Python-side (it rides the
 * additive ThetaSum carrier whose full-arithmetic C peer is OWED); the public op
 * returns the channel READ, which this peer mirrors completely.
 *
 * Reference (the harmonic-shape framing; MPM-verified at build): Hjalmar Rosengren,
 * "Elliptic Hypergeometric Functions" (arXiv:1608.06161v3 [math.CA]), Sec. 1.3
 * Lemma 1.3.2 + Sec. 1.4 Eq. (1.12).
 *
 * PURE COMPOSITION of the shared srmech_ellbase_* exact-Q monomial algebra +
 * theta_canon_full + er_build (the same single copy srmech_elliptic_gosper /
 * srmech_elliptic_recurrence ride). Malloc-free (JPL Rule 3): caller arena `ws` only.
 * No abs() (Class-K sign), no libm, no <complex.h>. Additive symbol -> ABI unchanged
 * (stays 3). License: MIT. ---- */

/* Minimum `ws_len` BYTES srmech_carrier_spectrum needs for the given shape (n_syms
 * symbols, n_num + n_den input theta factors, coeff_cap the per-coefficient limb cap). */
size_t srmech_carrier_spectrum_ws_bound(size_t n_syms, size_t n_num, size_t n_den,
                                        size_t coeff_cap);

/* Read both harmonic channels of a carrier element (see above). */
srmech_status_t srmech_carrier_spectrum(size_t n_syms, int xsym, int psym,
                                        int qsym, int ysym, size_t n_num, size_t n_den,
                                        const srmech_bigint_t *coeff_num,
                                        const srmech_bigint_t *coeff_den,
                                        const int32_t *exps_flat, uint32_t coeff_cap,
                                        int *out_has, int32_t *out_cyclic,
                                        size_t cyclic_cap, size_t *out_n_cyclic,
                                        int32_t *out_block_flat, size_t block_cap_rows,
                                        size_t *out_n_thetas, void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_q_zeilberger — the q-analog of Zeilberger's creative telescoping (the
 * SECOND public op of the q-hypergeometric F929 reduction row, the q-analog of
 * srmech_zeilberger). The C peer of srmech.amsc.q_zeilberger.q_zeilberger.
 *
 * Input: a proper q-hypergeometric term F(n,k) by its TWO bivariate-q term ratios
 * over (X, Y) = (q^n, q^k):
 *   r_n(X,Y) = F(n+1,k)/F(n,k) = rn_num/rn_den
 *   r_k(X,Y) = F(n,k+1)/F(n,k) = rk_num/rk_den
 * each a QBiPoly (a Y-ascending list of QPoly-in-X cells; each QPoly a Laurent-in-X
 * run of Q[q] coefficients). The bridge wire form per QBiPoly: the concatenated
 * q-runs (Y-major then X-major), a per-(Y,X)-cell qlen[], a per-Y-cell x_low[] and
 * x_cells[], and the Y-cell count.
 *
 * Output: when f(n)=Sum_k F(n,k) satisfies a q-recurrence of order <= max_order,
 * *out_has = 1, *out_order = L, and coeff_* (with coeff_qlen[]/coeff_xlow[]/
 * coeff_xcells[] and *out_coeff_count = L+1) carry the recurrence coefficients
 * a_j(X) (QPoly-in-X) so Sum_j a_j(q^n) f(n+j) = 0; cert_* (with *out_cert_ycells)
 * carry the q-Gosper certificate numerator x(X,Y) (R = x/D_P) when emitted. Else
 * *out_has = 0.
 *
 * STANDALONE-COMPLETE + BOUNDED native scope (the srmech_q_gosper precedent): this
 * rc56 peer COMPLETES the canonical k-FREE q-GEOMETRIC class (r_n a single Y^0
 * QPoly cell, r_k == 1) -- the order-1 recurrence rn_den f(n+1) - rn_num f(n) = 0
 * (a_0 = -rn_num, a_1 = rn_den), exact + byte-identical. For every other input it
 * DECLINES (*out_has = 0), and the Python op re-runs its COMPLETE pure-Q(q) path
 * (a has=0 is NEVER a definitive "no recurrence" -- the dispatch trusts only has=1).
 * The full higher-order Q(q)[X,Y] RREF is the owed everything-mirrors backlog. Any
 * residual overflow returns SRMECH_ERR_OVERFLOW (never a wrap).
 *
 * Additive symbol -> ABI unchanged (stays 3). License: MIT. ------- */

/* Minimum `ws_len` BYTES for input ratios of `coeff_limbs` significant limbs per
 * q-coefficient, a max ansatz `order`, and a max q-degree `qdeg`. 8-byte-aligned. */
size_t srmech_q_zeilberger_ws_bound(size_t coeff_limbs, size_t order, size_t qdeg);

/* The per-coefficient limb cap for each srmech_bigint in the coeff_* / cert_* OUTPUT
 * arrays, so a result q-coefficient never overflows its slot. */
size_t srmech_q_zeilberger_out_cap(size_t coeff_limbs, size_t order, size_t qdeg);

/* Compute the q-Zeilberger recurrence for F(n,k) given by its two bivariate-q
 * ratios. The caller sizes coeff_* to (max_order+1) output QPoly cells (each a q-run
 * of srmech_q_zeilberger_out_cap limbs) and cert_* likewise. rn_den / rk_den must
 * have ycells > 0. */
srmech_status_t srmech_q_zeilberger(
        const srmech_bigint_t *rn_num_n, const srmech_bigint_t *rn_num_d,
        const size_t *rn_num_qlen, const int64_t *rn_num_xlow,
        const size_t *rn_num_xcells, size_t rn_num_ycells,
        const srmech_bigint_t *rn_den_n, const srmech_bigint_t *rn_den_d,
        const size_t *rn_den_qlen, const int64_t *rn_den_xlow,
        const size_t *rn_den_xcells, size_t rn_den_ycells,
        const srmech_bigint_t *rk_num_n, const srmech_bigint_t *rk_num_d,
        const size_t *rk_num_qlen, const int64_t *rk_num_xlow,
        const size_t *rk_num_xcells, size_t rk_num_ycells,
        const srmech_bigint_t *rk_den_n, const srmech_bigint_t *rk_den_d,
        const size_t *rk_den_qlen, const int64_t *rk_den_xlow,
        const size_t *rk_den_xcells, size_t rk_den_ycells,
        size_t max_order,
        int *out_has, size_t *out_order,
        srmech_bigint_t *coeff_n, srmech_bigint_t *coeff_d,
        size_t *coeff_qlen, int64_t *coeff_xlow, size_t *coeff_xcells,
        size_t *out_coeff_count,
        srmech_bigint_t *cert_n, srmech_bigint_t *cert_d,
        size_t *cert_qlen, int64_t *cert_xlow, size_t *cert_xcells,
        size_t *out_cert_ycells,
        void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_q_wz_verify — the q-analog of the Wilf-Zeilberger VERIFY primitive (the
 * THIRD and FINAL public op of the q-hypergeometric F929 reduction row, the q-row
 * CLOSER). The C peer of the VERIFY half of srmech.amsc.q_wz_certificate.
 *
 * CHECKS that a candidate q-WZ certificate R(X,Y) = Xn/Xd satisfies the q-WZ equation
 * for the proper q-hypergeometric term F(n,k) given by its two bivariate-q term
 * ratios r_n = An/Ad, r_k = Bn/Bd (each an exact bivariate-Q[q] QBiPoly over
 * (X,Y) = (q^n, q^k), the SAME bridge wire form srmech_q_zeilberger consumes -- the
 * concatenated q-runs (Y-major then X-major), a per-(Y,X)-cell qlen[], a per-Y-cell
 * xlow[]/xcells[], and the Y-cell count):
 *
 *   F(n+1,k) - F(n,k) = G(n,k+1) - G(n,k),   G(n,k) = R(X,Y) * F(n,k),
 * with G(n,k+1) = (sigma_y R)*(sigma_y F) and sigma_y : Y -> q*Y the k-direction
 * q-shift (a Q[q] monomial multiply per Y-cell: the Y^d cell picks up q^d).
 *
 * Dividing by F(n,k) gives the rational identity
 *   r_n - 1 = R(X,qY) * r_k - R(X,Y),
 * and clearing denominators turns it into the single bivariate POLYNOMIAL identity
 *   (An - Ad) * (sigma_y(Xd) * Bd * Xd) ==
 *       (sigma_y(Xn) * Bn * Xd - Xn * sigma_y(Xd) * Bd) * Ad.
 * This is a COMPLETE verification -- bounded only by the input DEGREES, NOT by any
 * order (unlike the rc56 srmech_q_zeilberger order-<=1 native cap). So
 * srmech_q_wz_verify is a FULL C mirror of the Python verify.
 *
 * Method (exact over Q[q], no float): build both sides as exact bivariate-Q[q]
 * QBiPoly (a Y-ascending list of Q[q] QPoly-in-X cells, over caller-arena
 * srmech_bigint) and compare them coefficient-by-coefficient. NO solve, NO order loop,
 * NO qmat. *out_equal = 1 iff the identity holds. No malloc (JPL Rule 3): every
 * working carrier is carved from the caller arena `ws`. Any residual overflow returns
 * SRMECH_ERR_OVERFLOW (never a wrap); the Python op then runs its ceiling-free pure-Q
 * compare (standalone-honor). rn_den / rk_den / cert_den must have ycells > 0.
 *
 * Additive symbol -> ABI unchanged (stays 3). License: MIT. ------- */

/* Minimum `ws_len` BYTES for inputs of `coeff_limbs` significant limbs per
 * q-coefficient and a max bivariate `degree` (max over the X- + Y- + q-extents).
 * 8-byte-aligned. */
size_t srmech_q_wz_verify_ws_bound(size_t coeff_limbs, size_t degree);

/* The per-coefficient limb cap each srmech_bigint working carrier needs so a cleared-
 * identity q-coefficient never overflows its slot (a degree hint). */
size_t srmech_q_wz_verify_out_cap(size_t coeff_limbs, size_t degree);

/* Verify the q-WZ certificate for the term F(n,k). The six bivariate-q operands ride
 * the SAME QBiPoly bridge as srmech_q_zeilberger (n/d flat q-runs + qlen[] + xlow[] +
 * xcells[] + ycells). rn_den / rk_den / cert_den must have ycells > 0 (nonzero).
 * Returns SRMECH_OK + *out_equal set on a clean check; SRMECH_ERR_OVERFLOW (arena too
 * small for a huge input) routes the Python op to its pure-Q compare. */
srmech_status_t srmech_q_wz_verify(
        const srmech_bigint_t *rn_num_n, const srmech_bigint_t *rn_num_d,
        const size_t *rn_num_qlen, const int64_t *rn_num_xlow,
        const size_t *rn_num_xcells, size_t rn_num_ycells,
        const srmech_bigint_t *rn_den_n, const srmech_bigint_t *rn_den_d,
        const size_t *rn_den_qlen, const int64_t *rn_den_xlow,
        const size_t *rn_den_xcells, size_t rn_den_ycells,
        const srmech_bigint_t *rk_num_n, const srmech_bigint_t *rk_num_d,
        const size_t *rk_num_qlen, const int64_t *rk_num_xlow,
        const size_t *rk_num_xcells, size_t rk_num_ycells,
        const srmech_bigint_t *rk_den_n, const srmech_bigint_t *rk_den_d,
        const size_t *rk_den_qlen, const int64_t *rk_den_xlow,
        const size_t *rk_den_xcells, size_t rk_den_ycells,
        const srmech_bigint_t *cert_num_n, const srmech_bigint_t *cert_num_d,
        const size_t *cert_num_qlen, const int64_t *cert_num_xlow,
        const size_t *cert_num_xcells, size_t cert_num_ycells,
        const srmech_bigint_t *cert_den_n, const srmech_bigint_t *cert_den_d,
        const size_t *cert_den_qlen, const int64_t *cert_den_xlow,
        const size_t *cert_den_xcells, size_t cert_den_ycells,
        int *out_equal, void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_qmat — EXACT-RATIONAL dense matrix over srmech_bigint (the C peer of
 * srmech.amsc.qmat.QMat; the exact-ℚ linear-algebra carrier the §76 gosper
 * undetermined-coefficient solve needs in C).
 *
 * A matrix is two parallel caller-owned srmech_bigint arrays, ROW-MAJOR:
 * nums[r*ncols + c] / dens[r*ncols + c] is the exact-rational entry at (r, c)
 * (dens > 0, gcd(|nums|, dens) == 1; zero entry = 0/1). Each op computes the
 * SAME exact rational entries srmech.amsc.qmat.QMat computes — exact Gauss-Jordan
 * over ℚ on the shared _rref_augmented kernel — over caller-arena srmech_bigint
 * (NO malloc), reduced to lowest terms with positive denominator. Byte-identical
 * to Python's (num, den) at ANY magnitude (full bignum; no int64/Q61 ceiling).
 *
 * STANDALONE-COMPLETE: the working matrix entry storage + every scalar carrier +
 * the divmod/reduce scratch are carved from the caller arena `ws` (>= the matching
 * srmech_qmat_ws_bound), so the bound is the caller's RAM. Out entry arrays are
 * caller-owned + must be pre-sized: rref n_rows*n_cols, det a single rational,
 * inverse/solve the answer block, nullspace n_cols*n_cols (column-major basis).
 * Each srmech_bigint in those arrays must carry >= srmech_qmat_entry_cap limbs.
 * A singular inverse/solve sets *out_singular = 1 (mirroring QMat's ValueError);
 * a too-small ws or an out entry cap -> SRMECH_ERR_OVERFLOW (never a silent wrap),
 * and the Python QMat falls back to its ceiling-free pure-Gauss-Jordan path.
 *
 * ARENA SOUNDNESS: every reduced RREF entry is a ratio of input MINORS (Cramer);
 * a k x k minor Hadamard-bounds at k^(k/2) * M^k (k <= n_rows + total_cols).
 * qmat_cap_for sizes each carrier with coeff_limbs * (n_rows + total_cols) + a
 * log-headroom slack (dominating that minor bit-length) and x2 for the unreduced
 * cross-product — so a benign input never spuriously overflows; a genuinely huge
 * one reports OVERFLOW, never wraps.
 *
 * Carrier-internal (like srmech_poly): NOT a Rosetta ledger op. Additive symbols
 * -> SRMECH_ABI_VERSION unchanged (stays 3).
 * ------------------------------------------------------------------ */

/* The largest square dimension / column count the fixed-size pivot bookkeeping
 * (the on-stack pivot_cols + col->pivot-row arrays) supports. Past this an op
 * returns SRMECH_ERR_BAD_INPUT and the Python QMat keeps its pure path. */
#define SRMECH_QMAT_MAX_DIM 256u

/* Minimum `ws_len` BYTES the caller hands every srmech_qmat_* op below, for input
 * entries of `coeff_limbs` significant limbs and a row-reduction spanning `n_rows`
 * rows by `total_cols` columns (total_cols = the augmented width: n_cols for
 * rref/rank/nullspace, 2*n for inverse, n+b_cols for solve). Covers the working
 * matrix entry storage + every scalar carrier + the deepest gcd/divmod scratch.
 * 8-byte-aligned uint32 bump arena. */
size_t srmech_qmat_ws_bound(size_t coeff_limbs, size_t n_rows,
                            size_t total_cols);

/* The per-entry limb cap the caller must give each srmech_bigint in the OUTPUT
 * nums/dens arrays (so a reduced result entry never overflows its slot before the
 * op's guard fires). Use the SAME total_cols as the op's ws-bound. */
size_t srmech_qmat_entry_cap(size_t coeff_limbs, size_t n_rows,
                             size_t total_cols);

/* Reduced row echelon form of A (n_rows x n_cols) over ℚ. out_n/out_d receive the
 * n_rows*n_cols reduced matrix (row-major); *out_rank <- the pivot count;
 * pivot_cols[0..*out_rank) <- the pivot columns (increasing; caller sizes it
 * n_cols). n_cols > SRMECH_QMAT_MAX_DIM -> SRMECH_ERR_BAD_INPUT. */
srmech_status_t srmech_qmat_rref(const srmech_bigint_t *a_n,
                                 const srmech_bigint_t *a_d, size_t n_rows,
                                 size_t n_cols, srmech_bigint_t *out_n,
                                 srmech_bigint_t *out_d, size_t *out_rank,
                                 size_t *pivot_cols, void *ws, size_t ws_len);

/* The exact rank of A (the RREF pivot count). */
srmech_status_t srmech_qmat_rank(const srmech_bigint_t *a_n,
                                 const srmech_bigint_t *a_d, size_t n_rows,
                                 size_t n_cols, size_t *out_rank,
                                 void *ws, size_t ws_len);

/* The exact determinant of A (n x n) as one reduced rational out_num/out_den.
 * Forward Gauss elimination with explicit pivoting; the swap sign is a Class-K
 * int ±1 pin-slot (never an ALU abs). A zero pivot column -> det 0/1. */
srmech_status_t srmech_qmat_det(const srmech_bigint_t *a_n,
                                const srmech_bigint_t *a_d, size_t n,
                                srmech_bigint_t *out_num,
                                srmech_bigint_t *out_den, void *ws,
                                size_t ws_len);

/* The exact inverse of A (n x n) via [A|I] Gauss-Jordan. out_n/out_d receive the
 * n*n inverse (row-major) iff A is invertible; *out_singular set 1 (and out left
 * unspecified) when A is singular — mirroring QMat.inverse's ValueError. */
srmech_status_t srmech_qmat_inverse(const srmech_bigint_t *a_n,
                                    const srmech_bigint_t *a_d, size_t n,
                                    srmech_bigint_t *out_n,
                                    srmech_bigint_t *out_d, int *out_singular,
                                    void *ws, size_t ws_len);

/* Solve A x = b EXACTLY (A is n x n, b is n x b_cols) via [A|b] Gauss-Jordan.
 * out_n/out_d receive x (n x b_cols, row-major) iff A is full-rank-square;
 * *out_singular set 1 when A is singular (no unique solution) — mirroring
 * QMat.solve's ValueError. */
srmech_status_t srmech_qmat_solve(const srmech_bigint_t *a_n,
                                  const srmech_bigint_t *a_d, size_t n,
                                  const srmech_bigint_t *b_n,
                                  const srmech_bigint_t *b_d, size_t b_cols,
                                  srmech_bigint_t *out_n, srmech_bigint_t *out_d,
                                  int *out_singular, void *ws, size_t ws_len);

/* An exact basis of ker(A) (A is n_rows x n_cols) — the classical free-variable
 * construction (mirrors QMat.nullspace element-for-element). out_n/out_d receive
 * an (n_cols x *out_nfree) COLUMN-MAJOR-by-store matrix: out[i*n_cols + j] is
 * entry i of basis column j (caller sizes out n_cols*n_cols; *out_nfree <= n_cols
 * is the free-column count). *out_nfree == 0 iff A has full column rank. */
srmech_status_t srmech_qmat_nullspace(const srmech_bigint_t *a_n,
                                      const srmech_bigint_t *a_d, size_t n_rows,
                                      size_t n_cols, srmech_bigint_t *out_n,
                                      srmech_bigint_t *out_d, size_t *out_nfree,
                                      void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_qmat_rref_crt — the CRT re-fibration of the exact-Q RREF as ONE
 * standalone C symbol (srmech 0.9.0rc48, the CLOSER of the CRT-QMat arc).
 *
 * Orchestrates the four already-C-backed rungs (srmech_gf_rref / srmech_crt_combine
 * / srmech_rational_reconstruct / srmech_is_prime) into the full bounded-memory
 * exact-Q solve a bare-C host can call with ONE call. BYTE-IDENTICAL to the
 * pure-Python srmech.amsc.qmat.QMat.rref_crt: descending odd primes from 2**31-2,
 * skip a prime dividing any denominator, gf_rref per prime over GF(p), unlucky-
 * prime rank-consensus (max (rank, pivots) dominates; a strictly higher-rank prime
 * RESTARTS the CRT), crt_combine per cell, rational_reconstruct with the default
 * Wang bound isqrt(modulus // 2), stabilization early-termination (reconstructed
 * matrix identical across two consecutive good primes).
 *
 * THE ARENA BOUND (the crux). Unlike the dense srmech_qmat_rref (whose malloc-free
 * arena must reserve the Hadamard fraction ENVELOPE OF THE ELIMINATION, GB-scale),
 * the CRT arena is bounded by the ANSWER size: each per-prime solve is int64
 * (n_rows*n_cols*8 bytes), and the only bignum is the final per-cell crt_combine
 * product + rational_reconstruct, whose size is bounded by the NUMBER OF GOOD
 * PRIMES -- itself bounded a priori by the answer-Hadamard envelope (every reduced
 * entry is a ratio of input MINORS; a span x span minor of magnitude-M entries
 * bounds at span^(span/2)*M^span = H, and Wang succeeds once the good-prime product
 * exceeds 2*H^2, so n_primes <= ceil((2*log2 H + 2)/30) + slack). That bound is
 * derived from the input entries' magnitudes + the dimension, NOT the elimination
 * swell -- so the working RAM is answer-sized (MB-scale on the Franel system),
 * never the ~2.3 GB dense envelope. The caller sizes the arena from
 * srmech_qmat_rref_crt_ws_bound.
 *
 * Returns the same wire shape as srmech_qmat_rref (the exact-Q RREF row-major in
 * out_n/out_d, the pivot count in *out_rank, the pivot columns in pivot_cols).
 * STANDALONE-COMPLETE: every working table + bignum carrier + sub-op scratch is
 * carved from the caller arena `ws` (>= srmech_qmat_rref_crt_ws_bound). A too-small
 * arena or an exhausted prime field -> SRMECH_ERR_OVERFLOW (never a silent wrap);
 * the Python QMat.rref_crt then keeps its ceiling-free pure CRT path.
 * n_rows / n_cols > SRMECH_QMAT_MAX_DIM -> SRMECH_ERR_BAD_INPUT.
 *
 * Carrier-internal (like srmech_qmat): NOT a Rosetta ledger op. Additive symbols
 * -> SRMECH_ABI_VERSION unchanged (stays 3).
 * ------------------------------------------------------------------ */

/* Minimum `ws_len` BYTES for srmech_qmat_rref_crt on an n_rows x n_cols input of
 * `coeff_limbs` significant limbs per entry. Sizes the roster from the ANSWER-
 * Hadamard good-prime bound (NOT the dense elimination swell). 8-byte-aligned. */
size_t srmech_qmat_rref_crt_ws_bound(size_t coeff_limbs, size_t n_rows,
                                     size_t n_cols);

/* The per-entry limb cap the caller must give each srmech_bigint in the OUTPUT
 * nums/dens arrays -- sized from the ANSWER-Hadamard good-prime bound (NOT the
 * dense Cramer-minor srmech_qmat_entry_cap, which would re-reserve the GB-scale
 * output the CRT row escapes). */
size_t srmech_qmat_rref_crt_entry_cap(size_t coeff_limbs, size_t n_rows,
                                      size_t n_cols);

/* The exact-Q RREF of A (n_rows x n_cols) via the bounded-memory CRT re-fibration.
 * out_n/out_d receive the n_rows*n_cols reduced matrix (row-major); *out_rank <-
 * the pivot count; pivot_cols[0..*out_rank) <- the pivot columns (increasing;
 * caller sizes it n_cols). Byte-identical to srmech_qmat_rref's result at bounded
 * memory. */
srmech_status_t srmech_qmat_rref_crt(const srmech_bigint_t *a_n,
                                     const srmech_bigint_t *a_d, size_t n_rows,
                                     size_t n_cols, srmech_bigint_t *out_n,
                                     srmech_bigint_t *out_d, size_t *out_rank,
                                     size_t *pivot_cols, void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_cd_qvec — the Cayley-Dickson EXACT-ℚ VECTOR carrier, the 1-D sibling
 * of srmech_qmat (v0.9.0rc159; Qalg TAIL Batch 3). A dim-2^k Cayley-Dickson
 * element is a ℚ-vector of `dim` components; each component is one exact
 * rational num/den srmech_bigint pair (dens > 0, gcd(|num|, den) == 1; the
 * zero component is 0/1) — the SAME reduced canonical form as Python's
 * fractions.Fraction. A bare-C host CONSTRUCTS + HOLDS + MANIPULATES a CD
 * ℚ-vector through these four kernels with no Python (the everything-mirrors
 * discipline — the carrier is owed C too, not only the primitive kernels).
 *
 * They REUSE the qmat exact-ℚ scalar machinery (qmat_q_add / qmat_q_mul /
 * qmat_q_reduce over srmech_bigint) in the SAME translation unit — the 1-D
 * vector is a degenerate matrix, so the rational-limb arithmetic is not
 * duplicated (the 1:1-mirror discipline forbids two copies of the same
 * algebra). BYTE-IDENTICAL to Python's Fraction (num, den) at ANY magnitude
 * (full bignum; no int64/Q61 ceiling). Rosetta peers of
 * srmech.amsc.cascade.cayley_dickson.{cd_basis, cd_conjugate, cd_add,
 * cd_norm_sq}, attested BYTE-IDENTICAL by tests/test_qalg_qvec_c_rc159.py.
 *
 *   cd_qbasis    : the unit vector e_i (1/1 at i, 0/1 elsewhere) — Class-A
 *                  attested basis convention; no arithmetic.
 *   cd_qconjugate: negate the IMAGINARY half (components 1..dim-1), keep
 *                  component 0 — the Class-K sign-flip (never an ALU abs).
 *   cd_qadd      : component-wise exact-ℚ sum (Class-M bilinear over ℚ).
 *   cd_qnorm_sq  : Σ_i x_i² as one exact-ℚ scalar (Class-N rational anchor;
 *                  x·x̄ = N(x)·1).
 *
 * STANDALONE-COMPLETE: the qadd / qnorm_sq working carriers + reduce scratch
 * are carved from the caller arena `ws` (>= srmech_cd_qvec_ws_bound), so the
 * bound is the caller's RAM; any residual overflow returns SRMECH_ERR_OVERFLOW
 * (never a silent wrap), and the Python cd_* op falls back to its ceiling-free
 * pure-Fraction oracle. qbasis / qconjugate need NO arena (bignum copy / set +
 * a Class-K sign flip only). Out entry arrays are caller-owned + pre-sized:
 * each srmech_bigint must carry >= srmech_cd_qvec_entry_cap limbs.
 *
 * Carrier-internal like srmech_qmat / srmech_poly (no ToolEntry of its own —
 * the Python cd_* ops are the ledger surface). Additive symbols -> ABI
 * unchanged (stays 3). See srmech_qmat.c. dim a power of two in
 * [1, SRMECH_CD_MAX_DIM]; a bad dim / index -> SRMECH_ERR_BAD_INPUT.
 * ------------------------------------------------------------------ */

/* Minimum `ws_len` BYTES the caller hands srmech_cd_qadd / srmech_cd_qnorm_sq
 * for `dim` components of `coeff_limbs` significant limbs each. Covers the
 * exact-ℚ scalar accumulator + reduce scratch (the norm_sq accumulator's
 * denominator can grow to ~dim*coeff_limbs limbs; this dominates it). */
size_t srmech_cd_qvec_ws_bound(size_t coeff_limbs, size_t dim);

/* The per-entry limb cap the caller must give each srmech_bigint in the OUTPUT
 * nums/dens arrays so a reduced result never overflows its slot before the op's
 * guard fires. Use the SAME dim as the op's ws-bound. */
size_t srmech_cd_qvec_entry_cap(size_t coeff_limbs, size_t dim);

/* The unit basis element e_i of the dim-D algebra: out_n[c]/out_d[c] receive
 * 1/1 at c == i and 0/1 elsewhere (caller sizes out arrays `dim` long). No
 * arena. Errors: SRMECH_ERR_NULL_ARG; SRMECH_ERR_BAD_INPUT (bad dim / i). */
srmech_status_t srmech_cd_qbasis(int dim, int i,
                                 srmech_bigint_t *out_n, srmech_bigint_t *out_d);

/* Cayley-Dickson conjugation: copy x, then negate the numerator sign of the
 * imaginary components 1..dim-1 (Class-K; component 0 kept). out may not alias
 * x. Reduced form is preserved (negation keeps gcd == 1). No arena. */
srmech_status_t srmech_cd_qconjugate(const srmech_bigint_t *x_n,
                                     const srmech_bigint_t *x_d, int dim,
                                     srmech_bigint_t *out_n,
                                     srmech_bigint_t *out_d);

/* Component-wise exact-ℚ sum: out[c] = x[c] + y[c] (reduced). x, y, out are
 * each `dim` components; out may not alias x or y. Uses the caller arena `ws`
 * (>= srmech_cd_qvec_ws_bound). */
srmech_status_t srmech_cd_qadd(const srmech_bigint_t *x_n,
                               const srmech_bigint_t *x_d,
                               const srmech_bigint_t *y_n,
                               const srmech_bigint_t *y_d, int dim,
                               srmech_bigint_t *out_n, srmech_bigint_t *out_d,
                               void *ws, size_t ws_len);

/* The squared norm N(x) = Σ_i x_i² as one reduced exact-ℚ scalar
 * out_num/out_den. `dim` components; uses the caller arena `ws`
 * (>= srmech_cd_qvec_ws_bound). */
srmech_status_t srmech_cd_qnorm_sq(const srmech_bigint_t *x_n,
                                   const srmech_bigint_t *x_d, int dim,
                                   srmech_bigint_t *out_num,
                                   srmech_bigint_t *out_den,
                                   void *ws, size_t ws_len);

/* The arbitrary-rational Cayley-Dickson PRODUCT x·y (v0.9.0rc160; Qalg TAIL
 * Batch 4). Composes the integer cocycle srmech_cd_basis_product with the same
 * qmat exact-ℚ scalar arithmetic the Qvec kernels use: out[i⊕j] += x_i·y_j·
 * sign(i,j) over all i, j (the bilinear form of the recursive doubling). x, y,
 * out are each `dim` components; out may not alias x or y. Uses the caller arena
 * `ws` (>= srmech_cd_qvec_ws_bound; each slot sums `dim` products — the same
 * accumulation profile as srmech_cd_qnorm_sq). BYTE-IDENTICAL reduced (num, den)
 * to Python's recursive cd_mult at any magnitude. Rosetta peer of
 * srmech.amsc.cascade.cayley_dickson.cd_mult; attested by
 * tests/test_qalg_cdmult_c_rc160.py. Additive symbol -> ABI unchanged (3). */
srmech_status_t srmech_cd_mult(const srmech_bigint_t *x_n,
                               const srmech_bigint_t *x_d,
                               const srmech_bigint_t *y_n,
                               const srmech_bigint_t *y_d, int dim,
                               srmech_bigint_t *out_n, srmech_bigint_t *out_d,
                               void *ws, size_t ws_len);

/* srmech_faddeev_leverrier — the exact-INTEGER characteristic polynomial of an
 * n×n integer matrix via the Faddeev–LeVerrier recursion (v0.9.0rc161; Qalg TAIL
 * Batch 5). It is the FOUNDATION of the exact-LA tail (eigvals_exact / eig_exact
 * / jordan all reduce to the roots of this polynomial). Pure srmech_bigint
 * INTEGER arithmetic (NOT ℚ — an integer matrix has integer char-poly coeffs):
 *   M_1 = I ; c_1 = -tr(A) ;  for k in 1..n:  AM = A·M ;  c_k = -tr(AM)/k
 *   (the /k is EXACT — tr(A·M_k) is divisible by k, the FL integer theorem) ;
 *   M <- AM + c_k·I .
 * Composes srmech_bigint mul/add (the A·M matmul + trace accumulate) with the
 * exact srmech_bigint divmod (the /k step; floor == exact since k | tr). `a` is
 * the row-major n×n input matrix (n·n integer bigints; dens implied 1). `coeffs`
 * receives the n+1 monic coefficients HIGH→LOW: coeffs[0]=1, coeffs[k]=c_k, so
 * det(xI−A)=Σ coeffs[k]·x^(n−k). Uses the caller arena `ws`
 * (>= srmech_faddeev_leverrier_ws_bound); each `coeffs` entry must carry
 * >= srmech_faddeev_leverrier_entry_cap limbs. A too-small arena / entry cap ->
 * SRMECH_ERR_OVERFLOW (caller falls back to the byte-identical pure Python).
 * n in [1, SRMECH_FL_MAX_DIM]; n<1 or n>max -> SRMECH_ERR_BAD_INPUT. Rosetta peer
 * of srmech.amsc.cascade.matrix_cascades.char_poly (integer path); attested by
 * tests/test_qalg_charpoly_c_rc161.py. Additive symbol -> ABI unchanged (3). */
#define SRMECH_FL_MAX_DIM 256u
size_t srmech_faddeev_leverrier_entry_cap(size_t coeff_limbs, size_t n);
size_t srmech_faddeev_leverrier_ws_bound(size_t coeff_limbs, size_t n);
srmech_status_t srmech_faddeev_leverrier(const srmech_bigint_t *a, int n,
                                         srmech_bigint_t *coeffs,
                                         void *ws, size_t ws_len);

/* srmech_sturm_isolate — EXACT REAL-EIGENVALUE isolation (v0.9.0rc162; Qalg TAIL
 * Batch 6). The exact ROOTS of the characteristic polynomial: eigenvalues are
 * ALGEBRAIC numbers, so — kept in exact integer/rational arithmetic — they come
 * out as exact isolating rational intervals with NO Wilkinson ill-conditioning.
 * `cp` is the n+1 monic INTEGER char-poly coefficients HIGH->LOW (the
 * srmech_faddeev_leverrier output; dens implied 1). The op composes the exact-Q
 * srmech_poly_* kernels (gcd / divmod / eval) with scalar exact-Q srmech_bigint
 * arithmetic:
 *   char_poly -> Yun square-free factorisation (exact multiplicities) -> STURM
 *   sign-sequence isolation (sign-variation count at rational boundaries) ->
 *   rational BISECTION to width < 2^-bits.
 * out_lo_n/out_lo_d, out_hi_n/out_hi_d receive the reduced-fraction (num, den)
 * endpoints of the isolating intervals WITH multiplicity (each caller-owned,
 * >= srmech_sturm_isolate_entry_cap limbs, >= n slots); *out_count <- the number
 * of real eigenvalues (with multiplicity). The caller SORTS by lo+hi and projects
 * to float (the single terminal rotation) exactly as the pure path does. Uses the
 * caller arena `ws` (>= srmech_sturm_isolate_ws_bound); a too-small arena / entry
 * cap / a subdivision beyond the bounded stack -> SRMECH_ERR_OVERFLOW (the caller
 * falls back to the byte-identical pure Python — the parity oracle). n in
 * [1, SRMECH_STURM_MAX_DIM]; n<1 or n>max -> SRMECH_ERR_BAD_INPUT. Rosetta peer of
 * srmech.amsc.cascade.matrix_cascades.eigvals_exact (real-root path); attested by
 * tests/test_qalg_eigvals_c_rc162.py. Additive symbol -> ABI unchanged (3). */
#define SRMECH_STURM_MAX_DIM 256
size_t srmech_sturm_isolate_entry_cap(size_t coeff_limbs, size_t n,
                                      uint32_t bits);
size_t srmech_sturm_isolate_ws_bound(size_t coeff_limbs, size_t n, uint32_t bits);
srmech_status_t srmech_sturm_isolate(const srmech_bigint_t *cp, int n,
                                     uint32_t bits,
                                     srmech_bigint_t *out_lo_n,
                                     srmech_bigint_t *out_lo_d,
                                     srmech_bigint_t *out_hi_n,
                                     srmech_bigint_t *out_hi_d,
                                     size_t *out_count, void *ws, size_t ws_len);

/* srmech_poly_root_box_certify — the exact ARGUMENT-PRINCIPLE root count of a
 * polynomial `p` (np coefficients, low->high, over Q as num/den srmech_bigint
 * pairs) STRICTLY inside the open rational box (x0,x1) x (y0,y1). The winding
 * number of p around the box boundary (traversed CCW) = the enclosed root count,
 * computed in EXACT Fraction arithmetic (Cauchy-index sum of the per-edge V/U
 * sign-variation sequences — the same generalised-Sturm machinery as the real
 * isolation). *out_count <- the count; *out_degenerate <- 1 when a corner/edge
 * hits a root (winding half-integer / p vanishes on an edge — the caller nudges
 * the corners), mirroring _count_roots_in_box's ValueError. Composes srmech_poly_*
 * (edge substitution + generalised Sturm seq) + srmech_poly_eval over the caller
 * arena `ws` (>= srmech_poly_root_box_certify_ws_bound). The certifier the complex
 * eigenvalue isolation (eigvals_exact include_complex) composes. Additive symbol
 * -> ABI unchanged (3). */
size_t srmech_poly_root_box_certify_ws_bound(size_t coeff_limbs, size_t np);
srmech_status_t srmech_poly_root_box_certify(
        const srmech_bigint_t *p_num, const srmech_bigint_t *p_den, size_t np,
        const srmech_bigint_t *x0n, const srmech_bigint_t *x0d,
        const srmech_bigint_t *x1n, const srmech_bigint_t *x1d,
        const srmech_bigint_t *y0n, const srmech_bigint_t *y0d,
        const srmech_bigint_t *y1n, const srmech_bigint_t *y1d,
        int *out_count, int *out_degenerate, void *ws, size_t ws_len);

/* srmech_complex_isolate — the exact COMPLEX eigenvalues of the integer matrix
 * whose monic INTEGER char-poly is `cp` (HIGH->LOW, n+1 coeffs). Composes the Yun
 * square-free factorisation with PURE rational-box subdivision over the upper
 * half-plane, each box CERTIFIED by srmech_poly_root_box_certify (the exact
 * argument principle — no float in the count), refined to 2^-bits. out_re_n/out_re_d,
 * out_im_n/out_im_d receive the reduced-fraction (re, im) box centers WITH
 * multiplicity — each certified upper-half center AND its conjugate (im<0), in
 * per-square-free-factor emit order (the caller sorts by (re, im) + projects to
 * complex, exactly as the pure include_complex path does). *out_count <- the number
 * of complex eigenvalues (= n - #real). Byte/structurally-identical to the pure
 * _isolate_complex_roots_upper. Caller arena `ws` (>= srmech_complex_isolate_ws_bound);
 * each output >= srmech_complex_isolate_entry_cap limbs, >= n slots. A too-small
 * arena / a certifier degeneracy the jitter cannot escape -> SRMECH_ERR_OVERFLOW
 * (the caller falls back to the byte-identical pure path). Additive symbol -> ABI 3. */
size_t srmech_complex_isolate_entry_cap(size_t coeff_limbs, size_t n, uint32_t bits);
size_t srmech_complex_isolate_ws_bound(size_t coeff_limbs, size_t n, uint32_t bits);
srmech_status_t srmech_complex_isolate(const srmech_bigint_t *cp, int n,
                                       uint32_t bits,
                                       srmech_bigint_t *out_re_n,
                                       srmech_bigint_t *out_re_d,
                                       srmech_bigint_t *out_im_n,
                                       srmech_bigint_t *out_im_d,
                                       size_t *out_count, void *ws, size_t ws_len);

/* srmech_eigvec_exact — EXACT EIGENVECTORS over the number field ℚ(λ) = ℚ[x]/(m)
 * (v0.9.0rc163; Qalg TAIL Batch 7a). An algebraic eigenvalue λ is a root of a
 * monic IRREDUCIBLE integer polynomial m of degree deg, so ℚ(λ) is a FIELD; the
 * eigenvector is the null space of M = A − λI over that field, read off the exact
 * REDUCED ROW ECHELON form. The Qalg field arithmetic composes the exact-ℚ
 * srmech_poly_* kernels: add/sub coefficientwise, mul = convolution then REDUCE
 * mod m (srmech_poly_divmod remainder — the monic relation αⁿ = −Σ m[i]αⁱ),
 * inverse = the extended Euclidean algorithm on b(x), m(x) in ℚ[x] (b⁻¹ = u/g mod
 * m). Byte/structurally-identical to the pure _eigvec_exact_qalg (the RREF is
 * canonical). Rosetta peer of matrix_cascades.eigvec_exact / eigvec_exact_float;
 * attested by tests/test_qalg_eigvec_c_rc163.py.
 *
 * `a_n`/`a_d` are the n·n rational matrix entries (row-major, num/den, dens > 0
 * reduced); `m` is the deg+1 monic INTEGER coefficients low->high (denominators
 * implied 1); `lam_n`/`lam_d` are λ's deg ℚ(α) coordinates. out_n/out_d receive
 * *out_k null-space basis vectors, each n components of deg coordinates, at
 * out[((v·n + comp)·deg + coeff)] (the caller sizes them n·n·deg slots, each >=
 * srmech_eigvec_exact_entry_cap limbs); *out_k is the null-space dimension (0 iff
 * λ is not an eigenvalue — the caller then raises the same ValueError). Uses the
 * caller arena `ws` (>= srmech_eigvec_exact_ws_bound). n/deg in [1,
 * SRMECH_EIGVEC_MAX_DIM]; a non-monic / out-of-range / REDUCIBLE m (a zero-divisor
 * pivot with no inverse) -> SRMECH_ERR_BAD_INPUT; a too-small arena / coordinate
 * cap -> SRMECH_ERR_OVERFLOW (the caller falls back to the byte-identical pure
 * path — the parity oracle). Additive symbols -> ABI unchanged (3). */
#define SRMECH_EIGVEC_MAX_DIM 256
size_t srmech_eigvec_exact_entry_cap(size_t coeff_limbs, int n, int deg);
size_t srmech_eigvec_exact_ws_bound(size_t coeff_limbs, int n, int deg);
srmech_status_t srmech_eigvec_exact(
        const srmech_bigint_t *a_n, const srmech_bigint_t *a_d, int n,
        const srmech_bigint_t *m, int deg,
        const srmech_bigint_t *lam_n, const srmech_bigint_t *lam_d,
        srmech_bigint_t *out_n, srmech_bigint_t *out_d, int *out_k,
        void *ws, size_t ws_len);

/* srmech_jordan_chains — the exact JORDAN CHAINS (generalized eigenvectors) of
 * an integer/rational matrix A for the algebraic eigenvalue λ over ℚ(λ) =
 * ℚ[x]/(m) (v0.9.0rc164; Qalg TAIL Batch 7b). With N = A − λI (Qalg entries),
 * the generalized eigenspace null(Nᵘ) has dim μ and N is nilpotent on it; the
 * Jordan structure is read off the exact Qalg-RREF ranks r_k = rank(Nᵏ)
 * (# blocks of size exactly k = r_{k-1} − 2·r_k + r_{k+1}) and the chains are
 * built TOP-DOWN. COMPOSES the rc163 Qalg field (srmech_eigvec_exact's field
 * arithmetic) plus the Qalg matrix MATMUL / RANK / nested NULLSPACE added here.
 * Rosetta peer of matrix_cascades.jordan_chains_exact; attested by
 * tests/test_qalg_jordan_c_rc164.py.
 *
 * `a_n`/`a_d` are the n·n rational matrix entries (row-major, num/den); `m` is
 * the deg+1 monic INTEGER coefficients low->high; `lam_n`/`lam_d` are λ's deg
 * ℚ(α) coordinates. out_n/out_d receive *out_total generalized eigenvectors
 * (≤ n), each n components of deg coordinates, at out[((v·n + comp)·deg + coeff)]
 * — the chains CONCATENATED in build order (block size p down to 1; each chain
 * BOTTOM→TOP). out_block_sizes[0..*out_nchains) receive the chain lengths in the
 * same order (Σ = *out_total). The caller sizes out_n/out_d n·n·deg slots (each
 * >= srmech_jordan_chains_entry_cap limbs) and out_block_sizes n ints. Uses the
 * caller arena `ws` (>= srmech_jordan_chains_ws_bound). n/deg in
 * [1, SRMECH_JORDAN_MAX_DIM]; a non-monic / out-of-range / REDUCIBLE m ->
 * SRMECH_ERR_BAD_INPUT; a too-small arena / cap -> SRMECH_ERR_OVERFLOW (the
 * caller falls back to the byte-identical pure path). Additive symbols -> ABI
 * unchanged (3). */
#define SRMECH_JORDAN_MAX_DIM 64
size_t srmech_jordan_chains_entry_cap(size_t coeff_limbs, int n, int deg);
size_t srmech_jordan_chains_ws_bound(size_t coeff_limbs, int n, int deg);
srmech_status_t srmech_jordan_chains(
        const srmech_bigint_t *a_n, const srmech_bigint_t *a_d, int n,
        const srmech_bigint_t *m, int deg,
        const srmech_bigint_t *lam_n, const srmech_bigint_t *lam_d,
        srmech_bigint_t *out_n, srmech_bigint_t *out_d, int *out_total,
        int *out_block_sizes, int *out_nchains, void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_gosper — Gosper's indefinite hypergeometric summation (the
 * FIRST public op of the §76 "telescope" Σ-row closed-form prover,
 * F929). Built on srmech_bigint + the exact-ℚ poly/qmat machinery.
 *
 * Input: a hypergeometric term given by its TERM RATIO
 *   t(k+1)/t(k) = num(k)/den(k)
 * as two exact-rational polynomials in ℚ[k], each a parallel pair of
 * srmech_bigint coefficient arrays (ascending degree; nums[i]/dens[i] =
 * coeff of k^i, dens > 0, reduced). Output: when Σ t(k) HAS a
 * hypergeometric antidifference T(k) = R(k)·t(k) (so T(k+1)−T(k)=t(k)),
 * the rational CERTIFICATE R(k) = r_num(k)/r_den(k); else "no solution".
 *
 * The algorithm composes the same exact-ℚ kernels the Python op uses —
 * polynomial GCD / long division / dispersion shift (the srmech_poly_*
 * family's algebra) + the exact Gauss-Jordan RREF over ℚ
 * (srmech_qmat_rref) for the undetermined-coefficient Gosper equation —
 * over caller-arena srmech_bigint (NO malloc, JPL Rule 3). Byte-identical
 * to the Python certificate at ANY magnitude (full bignum; no ceiling).
 *
 * STANDALONE-COMPLETE: every working carrier + the poly/qmat/divmod
 * scratch is carved from the caller arena `ws` (>= srmech_gosper_ws_bound),
 * so the bound is the caller's RAM, not a compiled-in cap. Any residual
 * overflow returns SRMECH_ERR_OVERFLOW (never a silent wrap), and the
 * Python gosper falls back to its ceiling-free pure-ℚ path.
 *
 * Additive symbol -> ABI unchanged (stays 3). License: MIT. ------- */

/* Minimum `ws_len` BYTES the caller hands srmech_gosper for input term-ratio
 * polynomials of `coeff_limbs` significant limbs per coefficient and a higher
 * degree of `degree` (max(deg num, deg den)). Sized for the dispersion /
 * GP-normal-form / degree-bounded linear-solve chain (the heaviest stage is the
 * exact-ℚ RREF over an (deg²+1)×(deg+1) augmented matrix). 8-byte-aligned. */
size_t srmech_gosper_ws_bound(size_t coeff_limbs, size_t degree);

/* The per-coefficient limb cap a caller must give each srmech_bigint in the
 * r_num / r_den output arrays, so a reduced certificate coefficient never
 * overflows its slot before the op's own guard fires. */
size_t srmech_gosper_out_cap(size_t coeff_limbs, size_t degree);

/* Compute Gosper's certificate for the term ratio num/den.
 *   num_n/num_d (length n_num) : the term-ratio numerator   num(k) over ℚ[k]
 *   den_n/den_d (length n_den) : the term-ratio denominator den(k) over ℚ[k]
 * On success *out_has_solution is set: 1 when a hypergeometric antidifference
 * exists (then r_num_n/r_num_d (length *out_rnum) and r_den_n/r_den_d (length
 * *out_rden) carry the reduced certificate R(k) = r_num(k)/r_den(k)), 0 when
 * none exists (the r_* arrays are then unspecified). The caller sizes each r_*
 * array to (degree + 2) coefficients of srmech_gosper_out_cap limbs. den must be
 * a NONZERO polynomial (n_den > 0) else SRMECH_ERR_BAD_INPUT. */
srmech_status_t srmech_gosper(const srmech_bigint_t *num_n,
                              const srmech_bigint_t *num_d, size_t n_num,
                              const srmech_bigint_t *den_n,
                              const srmech_bigint_t *den_d, size_t n_den,
                              int *out_has_solution,
                              srmech_bigint_t *r_num_n, srmech_bigint_t *r_num_d,
                              size_t *out_rnum,
                              srmech_bigint_t *r_den_n, srmech_bigint_t *r_den_d,
                              size_t *out_rden,
                              void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_zeilberger -- Zeilberger's creative telescoping (the SECOND
 * public op of the section 76 "telescope" Sigma-row closed-form prover,
 * F929). The C peer of srmech.amsc.zeilberger.zeilberger.
 *
 * Input: a proper hypergeometric term F(n,k) given by its TWO term ratios
 *   r_n(n,k) = F(n+1,k)/F(n,k) = rn_num(n,k)/rn_den(n,k)
 *   r_k(n,k) = F(n,k+1)/F(n,k) = rk_num(n,k)/rk_den(n,k)
 * each an exact-rational BIVARIATE polynomial over Q[n,k]. A bivariate
 * polynomial is encoded FLAT as a k-ascending list of Poly-in-n coefficients:
 * the (num_n, num_d) arrays carry every coefficient in order (k-degree dk's
 * Poly-in-n occupies the next klen[dk] entries, ascending n-degree), and
 * klen[dk] is that Poly-in-n's coefficient count; kdeg is the number of
 * k-degree slots. Each srmech_bigint pair (num, den) is a reduced exact rational.
 *
 * Output: when a recurrence of order <= max_order exists, *out_has = 1, *out_order
 * = L, and coeff_n/coeff_d (with coeff_nlen[j] the per-j length, j = 0..L) carry
 * the recurrence coefficient polynomials a_j(n) so Sum_j a_j(n) f(n+j) = 0
 * (f(n) = Sum_k F(n,k)); cert_n/cert_d (with cert_klen + *out_cert_kdeg) carry the
 * rational certificate numerator x(n,k) (R = x / D_P). Else *out_has = 0.
 *
 * The algorithm composes the SAME exact-Q kernels the Python op uses -- the
 * srmech_poly_* algebra (the bivariate handling rides Poly-in-n mul/add/shift) +
 * the exact Gauss-Jordan RREF over Q (srmech_qmat_rref) for the parametrized
 * creative-telescoping linear system -- over caller-arena srmech_bigint (NO
 * malloc, JPL Rule 3). Byte-identical to the Python recurrence at ANY magnitude.
 *
 * STANDALONE-COMPLETE: every working carrier + the bipoly/qmat scratch is carved
 * from the caller arena `ws` (>= srmech_zeilberger_ws_bound). Any residual
 * overflow returns SRMECH_ERR_OVERFLOW (never a wrap), and the Python zeilberger
 * falls back to its ceiling-free pure-Q path.
 *
 * Additive symbol -> ABI unchanged (stays 3). License: MIT. ------- */

/* Minimum `ws_len` BYTES for input ratios of `coeff_limbs` significant limbs per
 * coefficient, a max ansatz `order`, and a max bivariate `degree`. 8-byte-aligned. */
size_t srmech_zeilberger_ws_bound(size_t coeff_limbs, size_t order, size_t degree);

/* The per-coefficient limb cap for each srmech_bigint in the coeff_* / cert_*
 * OUTPUT arrays, so a result coefficient never overflows its slot. */
size_t srmech_zeilberger_out_cap(size_t coeff_limbs, size_t order, size_t degree);

/* Compute Zeilberger's recurrence for the term F(n,k) given by its two ratios.
 * n_stride is the largest n-shift in the inputs (a degree hint; 1 is safe). The
 * caller sizes coeff_* to (max_order+1) * (out n-degree bound) entries and cert_*
 * to (out k-degree bound) * (out n-degree bound) entries, each of
 * srmech_zeilberger_out_cap limbs. rn_den / rk_den must have kdeg > 0. */
srmech_status_t srmech_zeilberger(
        const srmech_bigint_t *rn_num_n, const srmech_bigint_t *rn_num_d,
        const size_t *rn_num_klen, size_t rn_num_kdeg,
        const srmech_bigint_t *rn_den_n, const srmech_bigint_t *rn_den_d,
        const size_t *rn_den_klen, size_t rn_den_kdeg,
        const srmech_bigint_t *rk_num_n, const srmech_bigint_t *rk_num_d,
        const size_t *rk_num_klen, size_t rk_num_kdeg,
        const srmech_bigint_t *rk_den_n, const srmech_bigint_t *rk_den_d,
        const size_t *rk_den_klen, size_t rk_den_kdeg,
        size_t max_order, size_t n_stride,
        int *out_has, size_t *out_order,
        srmech_bigint_t *coeff_n, srmech_bigint_t *coeff_d, size_t *coeff_nlen,
        srmech_bigint_t *cert_n, srmech_bigint_t *cert_d, size_t *cert_klen,
        size_t *out_cert_kdeg,
        void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_wz_verify -- the Wilf-Zeilberger VERIFY primitive (the THIRD
 * and FINAL public op of the section 76 "telescope" Sigma-row closed-form
 * prover, F929). The COMPLETE C mirror of the VERIFY half of
 * srmech.amsc.wz_certificate.wz_certificate.
 *
 * Given a proper hypergeometric term F(n,k) by its two term ratios
 *   r_n(n,k) = An/Ad = rn_num/rn_den
 *   r_k(n,k) = Bn/Bd = rk_num/rk_den
 * and a candidate WZ certificate R(n,k) = Xn/Xd = cert_num/cert_den (each an
 * exact-rational BIVARIATE polynomial over Q[n,k], the same flat k-ascending
 * Poly-in-n encoding the srmech_zeilberger peer uses), this CHECKS the WZ equation
 *   F(n+1,k) - F(n,k) = G(n,k+1) - G(n,k),   G = R * F,
 * as an EXACT bivariate rational-function identity. Dividing through by F(n,k) and
 * clearing denominators it is the single bivariate POLYNOMIAL identity
 *   (An - Ad) * (Xd1 * Bd * Xd)  ==  (Xn1 * Bn * Xd - Xn * Xd1 * Bd) * Ad,
 * where Xn1/Xd1 are the k->k+1 shifts of Xn/Xd.
 *
 * *out_equal = 1 iff the identity holds (the WZ certificate is valid), else 0.
 *
 * This is a COMPLETE verification -- bounded only by the input DEGREES, NOT by any
 * order (unlike the rc42 srmech_zeilberger peer's order<=1 cap). Method: build both
 * sides as exact-Q bivariate polynomials (a 2-D grid of Q over caller-arena
 * srmech_bigint) and compare them coefficient-by-coefficient. NO solve, NO order
 * loop, NO qmat. No malloc (JPL Rule 3): every working bipoly is carved from the
 * caller arena `ws` (>= srmech_wz_verify_ws_bound). Any residual overflow returns
 * SRMECH_ERR_OVERFLOW (never a wrap), and the Python wz_certificate falls back to
 * its ceiling-free pure-Q compare (the standalone-complete honor).
 *
 * Additive symbol -> ABI unchanged (stays 3). License: MIT. ------- */

/* Minimum `ws_len` BYTES for inputs of `coeff_limbs` significant limbs per
 * coefficient and a max bivariate `degree`. 8-byte-aligned. */
size_t srmech_wz_verify_ws_bound(size_t coeff_limbs, size_t degree);

/* The per-coefficient limb cap each srmech_bigint working carrier needs so a
 * cleared-identity coefficient never overflows its slot (a degree hint). */
size_t srmech_wz_verify_out_cap(size_t coeff_limbs, size_t degree);

/* Verify the WZ certificate for the term F(n,k). rn_den / rk_den / cert_den must
 * have kdeg > 0 (nonzero). Returns SRMECH_OK + *out_equal set on a clean check;
 * SRMECH_ERR_OVERFLOW (arena too small for a huge input) routes the Python op to
 * its pure-Q compare. */
srmech_status_t srmech_wz_verify(
        const srmech_bigint_t *rn_num_n, const srmech_bigint_t *rn_num_d,
        const size_t *rn_num_klen, size_t rn_num_kdeg,
        const srmech_bigint_t *rn_den_n, const srmech_bigint_t *rn_den_d,
        const size_t *rn_den_klen, size_t rn_den_kdeg,
        const srmech_bigint_t *rk_num_n, const srmech_bigint_t *rk_num_d,
        const size_t *rk_num_klen, size_t rk_num_kdeg,
        const srmech_bigint_t *rk_den_n, const srmech_bigint_t *rk_den_d,
        const size_t *rk_den_klen, size_t rk_den_kdeg,
        const srmech_bigint_t *cert_num_n, const srmech_bigint_t *cert_num_d,
        const size_t *cert_num_klen, size_t cert_num_kdeg,
        const srmech_bigint_t *cert_den_n, const srmech_bigint_t *cert_den_d,
        const size_t *cert_den_klen, size_t cert_den_kdeg,
        int *out_equal, void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_apagodu_zeilberger -- the Apagodu-Zeilberger multivariate "sums
 * of sums" creative-telescoping recurrence-finder (the rc53 op that CLOSES
 * the multivariate F929 reduction row). The C peer of
 * srmech.amsc.apagodu_zeilberger.apagodu_zeilberger.
 *
 * Input: a proper hypergeometric term F(n,j,k) given by its THREE term ratios
 *   r_n(n,j,k) = F(n+1,j,k)/F(n,j,k) = rn_num/rn_den
 *   r_j(n,j,k) = F(n,j+1,k)/F(n,j,k) = rj_num/rj_den
 *   r_k(n,j,k) = F(n,j,k+1)/F(n,j,k) = rk_num/rk_den
 * each an exact-rational TRIVARIATE polynomial over Q[n,j,k]. A trivariate poly
 * is encoded FLAT as a j-major then k-then-n stream of (num, den) bigint pairs:
 * for the (jdeg x kdeg) (j,k) grid, *_nlen[dj*kdeg + dk] is the n-run length of
 * cell (dj, dk) and those n-coefficients occupy the next *_nlen entries (ascending
 * n-degree); *_jdeg / *_kdeg are the block shape. Each (num, den) is reduced.
 *
 * Output: when a recurrence of order <= max_order exists, *out_has = 1, *out_order
 * = L, and coeff_n/coeff_d (coeff_nlen[i] the per-i length, i = 0..L) carry the
 * recurrence coefficient polynomials a_i(n) so Sum_i a_i(n) f(n+i) = 0
 * (f(n) = Sum_{j,k} F(n,j,k)); cert_j_* and cert_k_* carry the two rational
 * certificate numerators x_j(n,j,k) / x_k(n,j,k) (R_j = x_j/D_P, R_k = x_k/D_P) as
 * the SAME (j,k)-cell grid encoding (cert_*_nlen + *out_cert_*_jdeg/kdeg). Else
 * *out_has = 0.
 *
 * The algorithm (Apagodu & Zeilberger 2006, Adv. Appl. Math. 37:139-152), exact
 * over Q[n,j,k]: for L = 0..max_order, the two-certificate ansatz
 *   Sum_i a_i(n) rho_i = [R_j(j+1) r_j - R_j] + [R_k(k+1) r_k - R_k]
 * (rho_i = prod_{t<i} r_n(n+t), D_P = prod_i rho_den_i) cleared to one common
 * denominator is a polynomial identity in (n,j,k) LINEAR in {a_i coeffs} U
 * {x_j coeffs} U {x_k coeffs}; matching (n,j,k)-powers gives a HOMOGENEOUS exact-Q
 * system. A kernel vector with a NONZERO a-block (read off srmech_qmat_rref) gives
 * the recurrence + certificates; the first such L is the minimal order.
 *
 * The C peer ACCELERATES the common low-order case (order <= 1, the textbook
 * double-sum identities, e.g. Sum_{j,k} C(n,j)C(j,k) -> 3^n); a genuinely-2D
 * higher-order term (the Apery-like sums) falls to the COMPLETE pure-Python path
 * -- the C never returns a false "no recurrence", it just declines (the Python
 * dispatch trusts only a has=1 C result). Composes the srmech_qmat_rref kernel + a
 * compact internal exact-Q TRIVARIATE poly toolkit over caller-arena srmech_bigint
 * (NO malloc, JPL Rule 3). Byte-identical to the Python recurrence at ANY
 * magnitude. Any residual overflow returns SRMECH_ERR_OVERFLOW (never a wrap), and
 * the Python op then runs its ceiling-free pure-Q path.
 *
 * Additive symbol -> ABI unchanged (stays 3). License: MIT. ------- */

/* Minimum `ws_len` BYTES for inputs of `coeff_limbs` significant limbs per
 * coefficient, a max ansatz `order`, and a max trivariate `degree`. 8-byte-aligned. */
size_t srmech_apagodu_zeilberger_ws_bound(size_t coeff_limbs, size_t order,
                                          size_t degree);

/* The per-coefficient limb cap for each srmech_bigint in the coeff_* / cert_*
 * OUTPUT arrays, so a result coefficient never overflows its slot. */
size_t srmech_apagodu_zeilberger_out_cap(size_t coeff_limbs, size_t order,
                                         size_t degree);

/* Compute the Apagodu-Zeilberger recurrence for the double sum f(n)=Sum_{j,k}
 * F(n,j,k) given F's three term ratios. degree_hint is a degree hint (1 is safe).
 * The caller sizes coeff_* to (max_order+1) * (out n-degree bound) entries and each
 * cert_* to (out jdeg)*(out kdeg)*(out n-degree bound) entries, each of
 * srmech_apagodu_zeilberger_out_cap limbs. rn_den / rj_den / rk_den must have
 * jdeg > 0. */
srmech_status_t srmech_apagodu_zeilberger(
        const srmech_bigint_t *rn_num_n, const srmech_bigint_t *rn_num_d,
        const size_t *rn_num_nlen, size_t rn_num_jdeg, size_t rn_num_kdeg,
        const srmech_bigint_t *rn_den_n, const srmech_bigint_t *rn_den_d,
        const size_t *rn_den_nlen, size_t rn_den_jdeg, size_t rn_den_kdeg,
        const srmech_bigint_t *rj_num_n, const srmech_bigint_t *rj_num_d,
        const size_t *rj_num_nlen, size_t rj_num_jdeg, size_t rj_num_kdeg,
        const srmech_bigint_t *rj_den_n, const srmech_bigint_t *rj_den_d,
        const size_t *rj_den_nlen, size_t rj_den_jdeg, size_t rj_den_kdeg,
        const srmech_bigint_t *rk_num_n, const srmech_bigint_t *rk_num_d,
        const size_t *rk_num_nlen, size_t rk_num_jdeg, size_t rk_num_kdeg,
        const srmech_bigint_t *rk_den_n, const srmech_bigint_t *rk_den_d,
        const size_t *rk_den_nlen, size_t rk_den_jdeg, size_t rk_den_kdeg,
        size_t max_order, size_t degree_hint,
        int *out_has, size_t *out_order,
        srmech_bigint_t *coeff_n, srmech_bigint_t *coeff_d, size_t *coeff_nlen,
        srmech_bigint_t *cert_j_n, srmech_bigint_t *cert_j_d, size_t *cert_j_nlen,
        size_t *out_cert_j_jdeg, size_t *out_cert_j_kdeg,
        srmech_bigint_t *cert_k_n, srmech_bigint_t *cert_k_d, size_t *cert_k_nlen,
        size_t *out_cert_k_jdeg, size_t *out_cert_k_kdeg,
        void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_quaternion — the 4x4 quaternion multiplication operators + the
 * hypercomplex exp(mu*theta) twiddle (0.9.0rc109; issue #1234 Item 1a,
 * re-raise of #863 BX-5/6/7). C peers of srmech.qm.quaternion — the
 * QDFT/ODFT foundation. WHY: Q8/{+-1} ~= Z2xZ2 = Klein-4 (F380 / the
 * in-repo R21 proof), so a quaternion FT's coefficient algebra (H)
 * matches a Klein-4 object's value algebra; these peers let a C-only
 * host build the 4x4 operator matrices + DFT twiddles without slicing
 * the 8x8 octonion operators (srmech_loop_{left,right}_op_f64).
 *
 * Same fixed Cayley-Dickson convention as srmech_loopbind.c (H = the
 * dim-4 rung of the same ladder, i.e. the octonion product restricted
 * to the first 4 basis elements). No libm: the twiddle's cos/sin ride
 * the Q61 cascade (srmech_{cos,sin}_q61) projected to double once, and
 * pi enters as 4*atan_q61(1). No malloc; caller buffers; JPL-clean.
 * Additive symbols -> SRMECH_ABI_VERSION stays 3. See srmech_quaternion.c.
 * ------------------------------------------------------------------ */

/* Left-multiplication operator matrix L_q: column k = q . e_k. `q` is 4
 * doubles; `n` must be 4; `out` is 4*4 = 16 doubles, row-major,
 * out[i*4 + k] = (q . e_k)_i. For a basis unit e_i (i >= 1) the matrix is
 * antisymmetric. L is a homomorphism: L(pq) = L(p)L(q); it commutes with
 * every right multiplication (the associativity witness H has, O lacks).
 * Errors: SRMECH_ERR_NULL_ARG; SRMECH_ERR_BAD_INPUT (n != 4). */
srmech_status_t srmech_quaternion_left_mult(
    const double *q, size_t n, double *out);

/* Right-multiplication operator matrix R_q: column k = e_k . q (the mirror
 * ordering; R(pq) = R(q)R(p), the anti-homomorphism — H is non-commutative
 * so L_q != R_q for generic q). Same buffer contract as left_mult. */
srmech_status_t srmech_quaternion_right_mult(
    const double *q, size_t n, double *out);

/* The quaternion Euler twiddle exp(mu*theta) = cos(theta)*1 + sin(theta)*mu.
 * `mu` is a caller-provided UNIT pure-imaginary 4-vector (mu[0] == 0.0;
 * the same caller-normalises-mu contract as srmech_hypercomplex_couple_q61;
 * normalise via srmech_rational_sqrt / srmech_sqrt_q61 on a C-only host).
 * `n` must be 4; `out` receives [cos t, sin t * mu1, sin t * mu2,
 * sin t * mu3] — a UNIT quaternion in the commutative subalgebra R[mu].
 * cos/sin are the exact Q61 cascade projected to double ONCE (byte-exact
 * with the pure-Python mirror). Errors: SRMECH_ERR_NULL_ARG;
 * SRMECH_ERR_BAD_INPUT (n != 4, mu[0] != 0, zero axis, or theta with no
 * Q61 form — non-finite / |theta| >= 2^55). */
srmech_status_t srmech_quaternion_exp(
    double theta, const double *mu, size_t n, double *out);

/* The QDFT twiddle factor exp(sigma * mu * 2*pi*j*k/N): theta =
 * sigma * 2*pi * ((j*k) mod n_points) / n_points with the index reduced
 * exactly in uint64 (Class I) and pi = 4*atan_q61(1) (Class N; no libm
 * M_PI), then srmech_quaternion_exp. sigma = -1 is the forward-DFT
 * orientation, +1 the inverse. Same unit-mu contract as
 * srmech_quaternion_exp. Errors: SRMECH_ERR_NULL_ARG;
 * SRMECH_ERR_BAD_INPUT (n_points == 0, sigma not +-1, or exp errors). */
srmech_status_t srmech_quaternion_twiddle(
    uint32_t j, uint32_t k, uint32_t n_points, int32_t sigma,
    const double *mu, size_t n, double *out);

/* The QUATERNION DISCRETE FOURIER TRANSFORM (0.9.0rc110; issue #1234
 * Item 1b, re-raise of #863) — the whole O(N^2) exact-reference transform
 * over the rc109 foundation (srmech_quaternion_twiddle + the left/right
 * mult operators). WHY: Q8/{+-1} ~= Z2xZ2 = Klein-4 (F380), so the H
 * coefficient algebra preserves BOTH Z2 chirality axes a complex FFT's
 * C-projection collapses. THE CONVENTION (forward sign sigma = -1):
 *   left  form (left == 1): X[k] = sum_m W(sigma*2*pi*k*m/N) . x[m]
 *   right form (left == 0): X[k] = sum_m x[m] . W(sigma*2*pi*k*m/N)
 * with W(theta) = exp(mu*theta); the INVERSE (inverse == 1) flips sigma
 * to +1 and scales by 1/N on the SAME side — each form round-trips
 * exactly. `x` is n_points*4 doubles (row-major quaternion samples);
 * `mu` is a caller-provided UNIT pure-imaginary 4-vector (`n` must be 4;
 * the srmech_quaternion_exp contract); `out` is n_points*4 doubles and
 * MUST NOT alias `x`. This is the SPREAD-SPECTRUM ENCODING / analysis
 * transform (the read path is the separate lightweight phase-coherent
 * peak op — a later voxel); an FFT factorisation is future work.
 * Errors: SRMECH_ERR_NULL_ARG; SRMECH_ERR_BAD_INPUT (n != 4,
 * n_points == 0, left/inverse not 0/1, or twiddle errors). */
srmech_status_t srmech_quaternion_dft(
    const double *x, uint32_t n_points, int32_t left, int32_t inverse,
    const double *mu, size_t n, double *out);

/* ------------------------------------------------------------------ *
 * srmech_octonion — the ODFT twiddle family + the whole-transform
 * OCTONION DFT (0.9.0rc111; issue #1234 Item 1c, re-raise of #863).
 * C peers of srmech.qm.octonion's rc111 twiddle family and the
 * graduated cascade.octonion_dft. WHY THE BRACKETING IS AN ARGUMENT
 * (F378): octonion multiplication is NON-ASSOCIATIVE, so "the ODFT" is
 * not unique until its bracketing convention is DECLARED — a different
 * bracketing is a DIFFERENT (also-declarable) transform. Declared
 * convention (attested in octonion_dft.toml [cascade.bracketing]):
 * per-summand-single-product; the inverse applies the conjugate twiddle
 * (sigma flip) on the SAME declared side; the two-sided 3-factor
 * association order is the explicit `bracketing` argument. O is
 * ALTERNATIVE (Artin: 2-generated subalgebras associate), so the
 * one-sided same-axis round-trip is EXACT; non-associativity bites at
 * >= 3 independent generators only (two_sided with distinct axes; a
 * twiddle associated through a product of samples) — verified from
 * Python over the fixed table. No libm (Q61 trig; pi = 4*atan_q61(1));
 * no malloc; caller buffers; JPL-clean. Additive symbols ->
 * SRMECH_ABI_VERSION stays 3. See srmech_octonion.c.
 * ------------------------------------------------------------------ */

/* The octonion Euler twiddle exp(mu*theta) = cos(theta)*1 + sin(theta)*mu.
 * `mu` is a caller-provided UNIT pure-imaginary 8-vector (mu[0] == 0.0;
 * the same caller-normalises-mu contract as srmech_quaternion_exp).
 * `n` must be 8; `out` receives [cos t, sin t * mu1, ..., sin t * mu7] —
 * a UNIT octonion in the commutative subalgebra R[mu] (which is WHY the
 * one-sided ODFT inverts). cos/sin are the exact Q61 cascade projected to
 * double ONCE (byte-exact with the pure-Python mirror). Errors:
 * SRMECH_ERR_NULL_ARG; SRMECH_ERR_BAD_INPUT (n != 8, mu[0] != 0, zero
 * axis, or theta with no Q61 form — non-finite / |theta| >= 2^55). */
srmech_status_t srmech_octonion_exp(
    double theta, const double *mu, size_t n, double *out);

/* The ODFT twiddle factor exp(sigma * mu * 2*pi*j*k/N): theta =
 * sigma * 2*pi * ((j*k) mod n_points) / n_points with the index reduced
 * exactly in uint64 (Class I) and pi = 4*atan_q61(1) (Class N; no libm
 * M_PI), then srmech_octonion_exp. sigma = -1 is the forward-DFT
 * orientation, +1 the inverse. Same unit-mu contract as
 * srmech_octonion_exp. Errors: SRMECH_ERR_NULL_ARG;
 * SRMECH_ERR_BAD_INPUT (n_points == 0, sigma not +-1, or exp errors). */
srmech_status_t srmech_octonion_twiddle(
    uint32_t j, uint32_t k, uint32_t n_points, int32_t sigma,
    const double *mu, size_t n, double *out);

/* The OCTONION DISCRETE FOURIER TRANSFORM (0.9.0rc111; issue #1234
 * Item 1c, re-raise of #863) — the whole O(N^2) exact-reference ODFT
 * over srmech_octonion_twiddle + the octonion loop operators
 * (srmech_loop_{left,right}_op_f64), ALL THREE forms in one peer.
 * THE DECLARED CONVENTION (forward sign sigma = -1; W = exp(mu*theta)):
 *   form == 0 (left):      X[k] = sum_m W . x[m]        (ONE product)
 *   form == 1 (right):     X[k] = sum_m x[m] . W        (ONE product)
 *   form == 2 (two_sided): X[k] = sum_m bracket(W_l, x[m], W_r)
 * with bracket keyed by `bracketing`: 0 = (W_l . x) . W_r
 * (left_associated), 1 = W_l . (x . W_r) (right_associated) — the F378
 * non-associativity made an explicit argument (the bracketings DIFFER
 * for distinct axes; a different bracketing is a different transform).
 * The INVERSE (inverse == 1; one-sided forms ONLY — two_sided is
 * forward-only) flips sigma to +1 and scales by 1/N on the SAME side;
 * the round-trip is EXACT by alternativity/Artin (see srmech_octonion.c).
 * `x` is n_points*8 doubles (row-major octonion samples); `mu` (and
 * `mu_r` for form == 2; ignored otherwise, may be NULL for one-sided)
 * are caller-provided UNIT pure-imaginary 8-vectors (`n` must be 8);
 * `out` is n_points*8 doubles and MUST NOT alias `x`. An FFT
 * factorisation is future work. Errors: SRMECH_ERR_NULL_ARG (incl.
 * mu_r == NULL with form == 2); SRMECH_ERR_BAD_INPUT (n != 8,
 * n_points == 0, form/bracketing/inverse out of range, two_sided with
 * inverse == 1, or twiddle errors). */
srmech_status_t srmech_octonion_dft(
    const double *x, uint32_t n_points, int32_t form, int32_t bracketing,
    int32_t inverse, const double *mu, const double *mu_r, size_t n,
    double *out);

/* ------------------------------------------------------------------ *
 * srmech_phase_coherent — the LIGHTWEIGHT matched-filter PEAK READ over a
 * rung/mode ladder (0.9.0rc112; issue #1234 Item 1d, the F1000->F1001->
 * F1002 refinement). C peer of srmech.amsc.cascade.phase_coherent_peak.
 * This is the READ counterpart to the full srmech_quaternion_dft /
 * srmech_octonion_dft ENCODING transforms — kept API-DISTINCT from them.
 *
 * WHY A SEPARATE OP (F1001): for the RBS-LM single-rung fold the target's
 * cross-rung response is a SPIKE, so the PEAK (max phase-coherent energy
 * over the rung ladder) is the MATCHED FILTER (it rejects off-rung noise),
 * whereas the full complex QDFT coherently combines ALL rungs — including
 * the off-rung noise — and measured WORSE (a spike's spectrum is flat, so
 * coherent combination gains nothing and forfeits the max's noise-
 * rejection). F1002 settled it read-independently (the elliptic code's
 * value is GENERATIVE encoding, not read-amplification). So the READ path
 * wants ONLY this peak reduction, NOT the full transform. There is NO
 * twiddle here — its absence IS what distinguishes the read from the
 * transform. See srmech_phase_coherent.c.
 * ------------------------------------------------------------------ */

/* The matched-filter PEAK over a rung ladder. `ladder` is n_rungs*dim
 * doubles (row-major: n_rungs per-rung samples, each a dim-component real
 * vector — dim 1 for a scalar response, dim 2 for a complex (re,im) sample,
 * dim 4/8 for a quaternion/octonion sample). Per-rung phase-coherent
 * energy: with `keys` == NULL the identity filter E_r = sum_i ladder[r][i]^2
 * (the sample's squared magnitude — the F1001 read); with `keys` != NULL
 * (also n_rungs*dim) the explicit matched filter E_r = (sum_i keys[r][i]*
 * ladder[r][i])^2. `*out_index` receives argmax_r E_r (ties -> lowest
 * index), `*out_score` the peak energy E, and `out_scores` (if non-NULL,
 * n_rungs doubles, MUST NOT alias the inputs) every E_r. A Class-K
 * squared-magnitude / comparison cascade — no abs(), no libm, no malloc.
 * Byte-exact with the pure-Python mirror (identical float-op order).
 * Errors: SRMECH_ERR_NULL_ARG (ladder/out_index/out_score NULL);
 * SRMECH_ERR_BAD_INPUT (n_rungs == 0 or dim == 0). */
srmech_status_t srmech_phase_coherent_peak(
    const double *ladder, const double *keys, uint32_t n_rungs, size_t dim,
    uint32_t *out_index, double *out_score, double *out_scores);

/* ------------------------------------------------------------------ *
 * Carriers-C (0.9.0rc141; Foundation F0) — the Mat/Vec CARRIER struct +
 * ctor / accessor / elementwise / lifecycle API so a BARE C HOST can
 * CONSTRUCT + HOLD + MANIPULATE a carrier with NO Python and feed its
 * buffer straight to the compute kernels (srmech_dense_matmul_complex /
 * srmech_svd_f64 / srmech_fft_c128 …) ZERO-COPY. The LAST C:Python
 * parity-backfill foundation (everything-mirrors capstone).
 *
 * The struct is a VIEW over a CALLER-OWNED buffer (JPL Rule 3: no malloc,
 * the same caller-arena discipline as srmech_bigint_t's `limbs`). Layout
 * mirrors the Python Mat/Vec exactly: row-major, one double per real
 * element / interleaved (re,im) per complex element (= C99
 * `double _Complex`), so `buf` is byte-identical to the Python carrier's
 * `array('d')` and feeds the interleaved-complex kernels no-copy.
 *
 * BYTE-IDENTICAL value ops: complex multiply is the naive CPython
 * `_Py_c_prod` (ac-bd, ad+bc); add/sub componentwise. (Complex `/` is NOT
 * in the C surface — CPython's Smith-scaled algorithm stays the pure-
 * Python path.) NO abs(): conj/neg are Class-K sign flips. ABI-additive:
 * new symbols only, SRMECH_ABI_VERSION stays 3.
 * ------------------------------------------------------------------ */

typedef struct srmech_mat {
    double  *buf;        /* caller-owned; row-major; interleaved (re,im) if
                            is_complex (2*rows*cols doubles) else rows*cols */
    uint32_t rows;
    uint32_t cols;
    int      is_complex; /* 0 = real, 1 = complex (any nonzero -> complex) */
} srmech_mat_t;

typedef struct srmech_vec {
    double  *buf;        /* caller-owned; interleaved (re,im) if is_complex
                            (2*n doubles) else n */
    uint32_t n;
    int      is_complex; /* 0 = real, 1 = complex (any nonzero -> complex) */
} srmech_vec_t;

/* Backing-buffer length (in doubles) a caller must provide for the given
 * shape + dtype: rows*cols (real) / 2*rows*cols (complex); n / 2*n. */
size_t srmech_mat_buf_len(uint32_t rows, uint32_t cols, int is_complex);
size_t srmech_vec_buf_len(uint32_t n, int is_complex);

/* Construction. init: point the struct at `buf` (a view; is_complex is
 * normalised to 0/1). zeros: init + clear the whole buffer to 0.
 * SRMECH_ERR_NULL_ARG if the struct or buf pointer is NULL. */
srmech_status_t srmech_mat_init(srmech_mat_t *m, double *buf,
                                uint32_t rows, uint32_t cols, int is_complex);
srmech_status_t srmech_vec_init(srmech_vec_t *v, double *buf,
                                uint32_t n, int is_complex);
srmech_status_t srmech_mat_zeros(srmech_mat_t *m, double *buf,
                                 uint32_t rows, uint32_t cols, int is_complex);
srmech_status_t srmech_vec_zeros(srmech_vec_t *v, double *buf,
                                 uint32_t n, int is_complex);

/* Element accessors. get writes *re_out (+ *im_out if non-NULL; 0 for a
 * real carrier). set stores (re[, im]); a real carrier stores only re (as
 * the Python carrier stores float(x.real)). SRMECH_ERR_BAD_INPUT on an
 * out-of-range index. */
srmech_status_t srmech_mat_get(const srmech_mat_t *m, uint32_t i, uint32_t j,
                               double *re_out, double *im_out);
srmech_status_t srmech_mat_set(srmech_mat_t *m, uint32_t i, uint32_t j,
                               double re, double im);
srmech_status_t srmech_vec_get(const srmech_vec_t *v, uint32_t i,
                               double *re_out, double *im_out);
srmech_status_t srmech_vec_set(srmech_vec_t *v, uint32_t i, double re, double im);

/* Row / column views: copy row i / column j of `m` into `out` (a caller-
 * provided Vec of length cols / rows and matching dtype). Mirrors the
 * Python m[i] / m[:, j] -> Vec. */
srmech_status_t srmech_mat_row(const srmech_mat_t *m, uint32_t i,
                               srmech_vec_t *out);
srmech_status_t srmech_mat_col(const srmech_mat_t *m, uint32_t j,
                               srmech_vec_t *out);

/* Elementwise binary (carrier op carrier; * is Hadamard, like the Python
 * carrier). Same shape required; out->is_complex MUST equal a|b (the
 * format-preserving rule) or SRMECH_ERR_BAD_INPUT. */
srmech_status_t srmech_mat_add(const srmech_mat_t *a, const srmech_mat_t *b,
                               srmech_mat_t *out);
srmech_status_t srmech_mat_sub(const srmech_mat_t *a, const srmech_mat_t *b,
                               srmech_mat_t *out);
srmech_status_t srmech_mat_mul(const srmech_mat_t *a, const srmech_mat_t *b,
                               srmech_mat_t *out);
srmech_status_t srmech_vec_add(const srmech_vec_t *a, const srmech_vec_t *b,
                               srmech_vec_t *out);
srmech_status_t srmech_vec_sub(const srmech_vec_t *a, const srmech_vec_t *b,
                               srmech_vec_t *out);
srmech_status_t srmech_vec_mul(const srmech_vec_t *a, const srmech_vec_t *b,
                               srmech_vec_t *out);

/* Scalar broadcast (scale = elementwise * scalar; add_scalar = + scalar).
 * out->is_complex MUST equal a|(s_im != 0) — a scalar with a nonzero
 * imaginary part promotes, matching the Python rule. */
srmech_status_t srmech_mat_scale(const srmech_mat_t *a, double s_re,
                                 double s_im, srmech_mat_t *out);
srmech_status_t srmech_mat_add_scalar(const srmech_mat_t *a, double s_re,
                                      double s_im, srmech_mat_t *out);
srmech_status_t srmech_vec_scale(const srmech_vec_t *a, double s_re,
                                 double s_im, srmech_vec_t *out);
srmech_status_t srmech_vec_add_scalar(const srmech_vec_t *a, double s_re,
                                      double s_im, srmech_vec_t *out);

/* Unary (dtype preserved). conj = Class-K sign flip on the imaginary slot
 * (real -> copy); neg = sign flip on every slot; transpose swaps axes
 * (out shape = cols x rows). */
srmech_status_t srmech_mat_conj(const srmech_mat_t *a, srmech_mat_t *out);
srmech_status_t srmech_mat_neg(const srmech_mat_t *a, srmech_mat_t *out);
srmech_status_t srmech_mat_transpose(const srmech_mat_t *a, srmech_mat_t *out);
srmech_status_t srmech_vec_conj(const srmech_vec_t *a, srmech_vec_t *out);
srmech_status_t srmech_vec_neg(const srmech_vec_t *a, srmech_vec_t *out);

/* Zero-copy kernel BRIDGE: complex carrier matmul out = a @ b, feeding the
 * three carrier buffers straight to srmech_dense_matmul_complex (no copy).
 * All three must be complex; a->cols == b->rows; out is a->rows x b->cols.
 * (Real / SVD / FFT need no wrapper — the carrier buf IS the argument those
 * kernels already take.) */
srmech_status_t srmech_mat_matmul_c128(const srmech_mat_t *a,
                                       const srmech_mat_t *b, srmech_mat_t *out);

#ifdef __cplusplus
}
#endif

#endif /* SRMECH_H */
