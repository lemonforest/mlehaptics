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
#define SRMECH_VERSION_PRE   "rc52"
#define SRMECH_VERSION       "0.9.0rc52"

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
 * §41 genome persistence — the C mirror of srmech.amsc.genome's
 * disk save / load / catalog / append / window. A genome directory is
 *
 *   <dir>/manifest.json   an MPRRecord (MPR v1) catalogue of the
 *                         chromosome set (leaf_dim, per-chromosome
 *                         cap_sha256 / leaf_count / byte_offset /
 *                         byte_len, body_sha256, the_one hash+hex).
 *   <dir>/turns.bin       the append-only flat body: every strand
 *                         element (a telomere cap or a coupled turn)
 *                         is a FIXED-WIDTH leaf_dim-byte block. No
 *                         length prefixes — chromosome boundaries live
 *                         in the manifest as byte_offset / byte_len.
 *
 * The manifest is built with the JSON builder above and serialised with
 * srmech_json_write, so it is BYTE-IDENTICAL to the Python genome_save's
 * json.dumps(payload, sort_keys=True, ensure_ascii=False). turns.bin is
 * the body bytes verbatim (no transformation). All hashing routes through
 * srmech_sha256_hex (Class A); bounding == integrity (every read re-hashes
 * the bytes it touched and compares the hex against the manifest — no abs,
 * no float). The §41 format version is 1.
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
 * field rebuildable by scanning the body). Mirrors GENOME_FORMAT_VERSION. */
#define SRMECH_GENOME_FORMAT_VERSION 2

/* §44 inline cap markers — the FIRST byte of a fixed-width cap leaf. Both are
 * > 3 so a cap is told apart from a Klein-4 data turn (bytes 0..3) by its
 * first byte alone; the label follows, NUL-padded to leaf_dim. Mirror
 * CHROM_CAP_MARKER / GENE_CAP_MARKER in srmech.amsc.genome. */
#define SRMECH_GENOME_CHROM_CAP_MARKER 0x43u   /* 'C' — opens a chromosome */
#define SRMECH_GENOME_GENE_CAP_MARKER  0x47u   /* 'G' — opens a gene */

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
 *   body / body_len : the self-describing fixed-width body (CHROM/GENE caps +
 *                     coupled turns; n_turns = body_len / leaf_dim).
 *   leaf_dim        : the fixed block width in bytes (> 0, <= 256).
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
 *                           body_len not a whole multiple of leaf_dim, a turn
 *                           before the first CHROM cap, or a label too long.
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
 *   SRMECH_ERR_BAD_INPUT   — leaf_dim mismatch, label already present,
 *                           region_len not a whole multiple of leaf_dim,
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

/* out = a * b (schoolbook). OVERFLOW if out->cap < mul_bound(a->n, b->n). */
srmech_status_t srmech_bigint_mul(srmech_bigint_t *out, const srmech_bigint_t *a,
                                  const srmech_bigint_t *b);

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
 * skip that output. Uses Knuth Algorithm D in the caller arena `ws`. */
srmech_status_t srmech_bigint_divmod(srmech_bigint_t *q, srmech_bigint_t *r,
                                     const srmech_bigint_t *a,
                                     const srmech_bigint_t *b,
                                     void *ws, size_t ws_len);

/* out = floor(sqrt(a)). a >= 0 else SRMECH_ERR_BAD_INPUT. Integer Newton
 * iteration over the caller arena `ws`. OVERFLOW if out->cap too small. */
srmech_status_t srmech_bigint_isqrt(srmech_bigint_t *out, const srmech_bigint_t *a,
                                    void *ws, size_t ws_len);

/* out = gcd(|a|, |b|) >= 0 (Euclid). Caller arena `ws`. */
srmech_status_t srmech_bigint_gcd(srmech_bigint_t *out, const srmech_bigint_t *a,
                                  const srmech_bigint_t *b,
                                  void *ws, size_t ws_len);

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

#ifdef __cplusplus
}
#endif

#endif /* SRMECH_H */
