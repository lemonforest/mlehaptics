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
#define SRMECH_VERSION_PRE   "rc419"
#define SRMECH_VERSION       "0.9.0rc419"

/* ABI version. Bumped in lockstep with the Python shim's
 * EXPECTED_ABI_VERSION whenever the wire format of any exported
 * function changes. Adding a NEW symbol does not bump ABI; changing
 * an existing signature does; and — stated explicitly since rc287,
 * because its absence here is what let a removal ship unbumped through
 * a first review pass — REMOVING an exported symbol ALWAYS bumps.
 *
 * The reason is not that the removed op misbehaves. It is that a
 * removal produces NO OTHER SYMPTOM. The ctypes shim binds optional
 * peers by `hasattr`, so against a stale lib the absent symbol raises
 * nothing and the wrapper simply runs its pure body — which is the
 * CORRECT result for that one op. Meanwhile the ABI check has passed,
 * HAS_NATIVE stays true, and EVERY OTHER op keeps dispatching into a
 * library built from different source. The ABI version is the only
 * mechanism that can catch that pairing, and a removal is precisely
 * the change that leaves it nothing else to catch.
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
 * v4 — v0.9.0rc180: the srmech.bus pub/sub C peer (ANNEX Batch A pt2b —
 *      BUS FULLY C). Adds the new function-pointer typedef
 *      srmech_bus_subscriber_callback_t (the pub/sub client's
 *      broadcast-delivery callback) alongside the broadcast /
 *      subscribe / pubsub_accept / subscriber_count / pipe symbols.
 *      Per the v2→v3 precedent, adding a callback typedef carries a
 *      CFUNCTYPE wire-format implication, so ABI bumps (the plain
 *      additive functions alone would not).
 * v5 — v0.9.0rc242: the C progress / introspection callback (#840 —
 *      Class-H self-introspection projected to a bare-C host, completing
 *      the everything-to-C surface). Adds the new function-pointer typedef
 *      srmech_progress_cb_t (the dispatch-observer callback) alongside the
 *      srmech_set_progress_cb registration symbol. Per the v2→v3 / v3→v4
 *      precedent, adding a callback typedef carries a CFUNCTYPE wire-format
 *      implication for the Python ctypes shim, so ABI bumps (the plain
 *      srmech_set_progress_cb function alone would not).
 * v6 — v0.9.0rc275: the C encode-progress + graceful-abort primitive (§101 /
 *      PR#687 / F1252). Adds the new function-pointer typedef
 *      srmech_progress_tick_cb_t (the PER-CALL, PER-ITERATION heartbeat WITH a
 *      nonzero-return-to-CANCEL channel) + the versioned srmech_progress_ev_t
 *      event struct + the SRMECH_CANCELLED status, alongside the two
 *      *_progress overload symbols (srmech_laplacian_fiedler_sparse_file_progress,
 *      srmech_genome_mint_progress). Distinct from the v5 srmech_progress_cb_t
 *      dispatch-observer (the libcurl/SQLite separate trace-vs-progress pattern).
 *      Per the v2→v5 precedent, adding a callback typedef carries a CFUNCTYPE
 *      wire-format implication for the Python ctypes shim, so ABI bumps (the
 *      additive *_progress functions alone would not). Later APPEND-only growth
 *      of srmech_progress_ev_t via its struct_size gate does NOT re-bump.
 * v7 — v0.9.0rc287: the glyph-stream tokenizer (BREAKING). REMOVES the
 *      exported srmech_text_tokenize and adds srmech_text_glyph_stream +
 *      srmech_text_default_gb_table. The FIRST bump driven by a REMOVAL
 *      rather than a callback typedef, and the removal alone is sufficient
 *      per the policy note above. Verified rather than assumed: with the lib
 *      loaded but srmech_text_glyph_stream absent, glyph_stream() returns a
 *      CORRECT grapheme-cluster stream from its pure body (conformance still
 *      1093/1093) — so the removal is not caught by wrong output, and it is
 *      not caught by a load error either. Nothing catches it except this
 *      version, while HAS_NATIVE stays true and the rest of the library
 *      dispatches into a mismatched build. (The added symbols alone would
 *      not have bumped.)
 *
 *      rc286 also claimed 7, but is NOT shipping: rc287 supersedes it
 *      completely (it parameterised the `_MIN_LEN` machinery this rc
 *      deletes outright), so 7 belongs to rc287. The rc286 branch and its
 *      findings are retained; the numbering gap is deliberate.
 * v8 — v0.9.0rc290: the Klein-4 mint split by REGIME (§102 / F1259 / F1260,
 *      BREAKING). REMOVES the exported srmech_klein4_random and adds
 *      srmech_klein4_expand (the same MT19937 stream under the name that
 *      describes it), srmech_klein4_address, srmech_klein4_role,
 *      srmech_klein4_sector_frame and srmech_klein4_from_one. The SECOND
 *      bump driven by a removal; the five added symbols alone would not
 *      have bumped.
 *
 *      The removal is deliberate rather than incidental. srmech_klein4_random
 *      was never random — with a `key` supplied it is a pure deterministic
 *      expansion — and leaving the wrong name on the C symbol while fixing the
 *      Python one would have re-created exactly the Python-rooted taxonomy
 *      ADR-0009 names: a bare-C host reading "random" gets the SHARPER form of
 *      the lie, because C has no other regime to fall back on. Per the policy
 *      note above the removal alone is sufficient to bump, and the rc287
 *      reasoning applies unchanged: nothing but this version can catch a lib
 *      built from pre-rc290 source, since the ctypes shim binds by hasattr and
 *      the wrapper would silently run its pure body while every OTHER op kept
 *      dispatching into the mismatched build.
 * v9 — v0.9.0rc306: srmech_genome_section_counts caller-arena conversion (§102 /
 *      task #899). ADDS two params (void *ws, size_t ws_len) to the EXISTING
 *      exported srmech_genome_section_counts signature — an existing-signature
 *      change, so this is the FIRST bump of the ordinary kind (not a callback
 *      typedef, not a removal). The op used three file-scope static scratch
 *      buffers (a 32 MiB catalog arena, a 2^18-slot count table, a 64 KiB window)
 *      + a static id counter; those made it BOTH corpus-capped (the 32 MiB arena
 *      admitted ~11,000 chromosomes) AND non-reentrant. It now carves the count
 *      table + window off the caller `ws` and hands the untouched tail to
 *      genome_obtain_manifest as the catalog arena — no static state remains, so
 *      the op is reentrant and the corpus bound is whatever `ws` the caller sizes
 *      (via the new srmech_genome_section_counts_arena_bytes helper). The paired
 *      Python ctypes argtypes gain the two params in lockstep; a stale ABI-8 lib
 *      would push the OLD 10-arg wire shape at the NEW 12-arg binding, which the
 *      version check is the only thing that catches (HAS_NATIVE would otherwise
 *      stay true). GENOME_FORMAT_VERSION stays 15 — no on-disk format change.
 * v10 — v0.9.0rc307: the fiedler_sparse family ws_len UNIT unified to BYTES (§51 /
 *      task #903). No signature changed shape; the CONTRACT of an existing param
 *      changed: srmech_laplacian_fiedler_sparse / _file / _file_progress guarded
 *      ws_len as a COUNT OF DOUBLES (`ws_len < 8u*n`), while the rest of the
 *      caller-arena surface (k_extreme_modes, recursive_cut, every *_arena_bytes
 *      peer) counts BYTES. That three-way split was a latent unit hazard for an
 *      EXTERNAL bare-C host sizing by the wrong convention (fail-safe in-tree only
 *      because the Python sizer happened to over-size). rc307 adds
 *      srmech_laplacian_fiedler_sparse_arena_bytes(n) = 8*n*sizeof(double) and
 *      flips the three fiedler guards to it, so ws_len is BYTES uniformly across
 *      the whole laplacian surface. Reinterpreting an exported function's ws_len
 *      unit is a breaking wire-contract change for external callers: a caller
 *      passing the old doubles count now under-sizes the arena 8x and is correctly
 *      declined (SRMECH_ERR_BAD_INPUT) rather than silently reading OOB — the
 *      version bump is what tells an out-of-tree caller to re-read the contract.
 *      The paired Python ctypes dispatch sites pass BYTES in lockstep. The added
 *      *_arena_bytes symbol alone would NOT have bumped; the unit reinterpretation
 *      is what does. GENOME_FORMAT_VERSION stays 15 — no on-disk format change.
 *  (rc334, v0.9.0rc334, task #887) — srmech_genome_add_plasmid + its
 *      srmech_genome_add_plasmid_scratch_bytes sizer close the LAST genome wire-glue
 *      parity gap (add_plasmid; CEIL_WIRE_GLUE_GAPS 1 -> 0). Two ADDITIVE plain
 *      symbols reusing the existing srmech_progress_tick_cb_t typedef (NO new
 *      callback typedef, no existing signature changed), so SRMECH_ABI_VERSION STAYS
 *      10 and GENOME_FORMAT_VERSION STAYS 19 — the organized strand is plain v15-era
 *      KERNEL chromosomes over existing caps + blocks.
 *  (rc395, v0.9.0rc395, task #T1000) — REMOVED the dedicated dim-16 brute-force export
 *      srmech_cd_zero_divisor_witness (and its static helper cd_pair_product_is_zero).
 *      It predated the GF(2) route and is subsumed by the dim-general Python ops
 *      cd_zero_divisor_witness / cd_zero_divisor_witnesses, which are composition_of_c
 *      over the already-C gf_rref + cd_basis_product (no dedicated C symbol). A removed
 *      export produces no symptom other than a version mismatch, so by standing policy
 *      it bumps SRMECH_ABI_VERSION 10 -> 11. GENOME_FORMAT_VERSION stays 19 — no on-disk
 *      format change.
 * v12 — v0.9.0rc404 (`#T1069`): SRMECH_ERR_LIMIT = 8 splits the retryable half of
 *      SRMECH_ERR_OVERFLOW away from the structural half, and srmech_json_parse /
 *      srmech_toml_parse now RETURN THE NEW VALUE for a class of input that
 *      returned 4 through rc403. NO signature changed shape; the CONTRACT of an
 *      existing export's RETURN VALUE changed — the same KIND of bump as v10's
 *      ws_len unit reinterpretation, and for the same reason: the version is the
 *      only thing that tells an out-of-tree caller to re-read the contract. The
 *      status block below states outright that non-zero values "form part of the
 *      wire contract with the Python ctypes binding", so reinterpreting one IS a
 *      wire-contract change.
 *
 *      WHAT THE BUMP ACTUALLY BUYS, measured. rc404 also deletes the rc401
 *      Python-side pre-scan, which existed ONLY because the two conditions shared
 *      status 4. A stale rc403 .so reports ABI 11 and would otherwise LOAD into
 *      rc404 Python; with the pre-scan gone and the C sites un-migrated, an
 *      out-of-int64 literal costs 13 native calls and ~512 MiB of arena instead of
 *      1 call and ~0.1 MiB — reintroducing the exact defect rc404 exists to
 *      remove, and doing it SILENTLY, because the answer stays correct. Rejecting
 *      the stale lib (clean fall-back to the pure path) is strictly better than a
 *      correct answer bought at 512 MiB. GENOME_FORMAT_VERSION stays 19 — no
 *      on-disk format change.
 *
 *   v13 (v0.9.0rc418, task `#T1108`) — the ATTESTATION LIFECYCLE bump, and the
 *      second of the ORDINARY kind after v9. Eleven existing exported signatures
 *      changed: the ten genome WRITE entry points
 *        srmech_genome_save / _append / _remove / _replace / _export / _import /
 *        _pack / _from_graph / _plasmid_extract / _add_plasmid
 *      each gained `(const char *attestation, size_t attestation_len)` — the
 *      caller MPR SOURCE-attestation channel the compiled projection previously
 *      did not have AT ALL, and
 *        srmech_catalog_attestation_audit
 *      gained `(const char *descriptor, size_t descriptor_len)` so it can
 *      SYNTHESISE a literature_curated row's attestation instead of projecting a
 *      raw envelope's. The paired ctypes argtypes move in lockstep, exactly as
 *      v9's precedent requires — quoted from docs/srmech/CLAUDE.md: "v9
 *      (v0.9.0rc306, task #899) is the first bump of the ORDINARY kind — an
 *      existing exported signature changed: srmech_genome_section_counts gained
 *      (void *ws, size_t ws_len) caller-arena params ... with the paired ctypes
 *      argtypes updated in lockstep."
 *
 *      WHAT THE BUMP BUYS. Before rc418 the ten write entry points had no channel
 *      for a caller attestation, so `genome_save(attestation=...)` had to branch
 *      to the scripting projection — an ADR-0009 capability gap dressed up as a
 *      fast-path skip. A stale rc417 .so reports ABI 12 and would otherwise load
 *      into rc418 Python, where the carry-forward the rc adds lives in the C
 *      builders: the stale lib would keep OVERWRITING a caller's real attestation
 *      with srmech's defaults and the result would still validate as a well-formed
 *      MPR. That is the silent-wrong-answer class, so rejecting the stale lib is
 *      the only safe read. GENOME_FORMAT_VERSION stays 19 — the attestation block
 *      is free-form MPR content, gains no key, and turns.bin is untouched.
 */
#define SRMECH_ABI_VERSION 13

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
    SRMECH_ERR_INTERNAL   = 6,  /* invariant violation; report it */
    SRMECH_CANCELLED      = 7,  /* §101: a progress tick returned nonzero — a
                                 * CLEAN abort, NOT an error. The out-count
                                 * reflects the COMPLETE units already written
                                 * (a valid partial); the C mirror of the
                                 * telomere_tick honest-decline. */
    SRMECH_ERR_LIMIT      = 8   /* rc404 (`#T1069`): a bound that GROWING THE
                                 * CALLER'S BUFFERS CANNOT RELIEVE — a value
                                 * outside the representable range, a
                                 * compiled-in structural cap, or a
                                 * non-convergent iteration. Retrying is futile
                                 * BY CONSTRUCTION, which is exactly what
                                 * distinguishes it from SRMECH_ERR_OVERFLOW.
                                 *
                                 * WHY THE SPLIT. Until rc404 both conditions
                                 * shared status 4, so a caller's grow-loop
                                 * could not tell "your arena was too small"
                                 * from "this integer does not fit in int64".
                                 * The loop therefore doubled its arena up to
                                 * the cap and re-parsed at every step before
                                 * declining — measured at 13 native calls and
                                 * ~512 MiB of allocation for a document whose
                                 * verdict was fixed at the first byte. The
                                 * answer was always CORRECT; it was the COST
                                 * that was wrong.
                                 *
                                 * DIRECTION IS FORCED, NOT CHOSEN. Status 4
                                 * KEEPS the retryable/buffer meaning, so every
                                 * existing `rc == SRMECH_ERR_OVERFLOW -> grow`
                                 * loop stays correct with ZERO edits and the
                                 * new value falls through to its decline
                                 * branch. Assigning 8 to the buffer case
                                 * instead would silently stop every retry loop
                                 * growing on genuine arena exhaustion.
                                 *
                                 * MIGRATION IS PARTIAL AND DELIBERATE. rc404
                                 * re-statuses ONE MEASURED SLICE —
                                 * srmech_json.c and srmech_toml.c — and leaves
                                 * the rest of the tree conflating the two under
                                 * status 4. The remaining sites are visible and
                                 * monotone via the down-only line ratchet in
                                 * python/tests/test_status_conflation_ratchet_rc404.py.
                                 * Do NOT read a status-4 return elsewhere in
                                 * the tree as "therefore retryable" yet. */
} srmech_status_t;

/* ------------------------------------------------------------------ *
 * ENCODE PROGRESS + GRACEFUL ABORT (v0.9.0rc275, §101 / PR#687 / F1252)
 *
 * The caller HEARTBEAT + nonzero-return-to-CANCEL primitive threaded into the
 * long encode ops. DISTINCT from the v5 srmech_progress_cb_t dispatch-OBSERVER
 * (void return, once-per-tool, process-global): this is a PER-CALL,
 * PER-ITERATION heartbeat WITH a cancel channel, passed as a parameter to a long
 * encode op (the libcurl XFERINFOFUNCTION / SQLite progress_handler / libgit2
 * transfer_progress pattern — a separate progress handler kept orthogonal to the
 * trace/verbose observer). Fires INLINE on the encode thread — zero concurrency,
 * MCU-safe, JPL-deterministic (no task registry, no RTOS threads).
 *
 * VERSIONED STRUCT (statx stx_mask / Vulkan sType / Win32 cbSize): the first
 * field is struct_size. rc276+ fields APPEND after the current tail; the emitter
 * sets struct_size to what IT knows, the callback reads a field only if
 * struct_size covers it. So the struct extends WITHOUT an ABI bump — only this
 * first introduction bumps (the new callback typedef -> CFUNCTYPE implication).
 *
 * OFF BY DEFAULT: a NULL tick pointer means the op runs exactly as before (one
 * pointer test per unit — the hot path pays ~nothing).
 *
 * done / total are EXACT integer cardinalities (Class-N; node / kernel / group /
 * iteration counts). The library NEVER divides and NEVER accumulates a float; a
 * %-fraction is the observer's own done/total. They are non-negative by
 * construction (there is no sign to strip — not a Class-K pin-slot site; no abs).
 * ------------------------------------------------------------------ */
typedef enum srmech_encode_phase {
    SRMECH_PHASE_NONE         = 0,  /* unknown / unspecified                    */
    SRMECH_PHASE_EXTRACTING   = 1,  /* stage-1 co-occurrence extract (F1252)    */
    SRMECH_PHASE_INTEGRATING  = 2,  /* stage-2 plasmid integrate  (F1252)       */
    SRMECH_PHASE_MINTING      = 3,  /* mint / mint_strand / centromere splice   */
    SRMECH_PHASE_PARTITIONING = 4   /* recursive_cut / fiedler bisection        */
    /* rc276+ phases APPEND HERE (forward-extensible; older readers see the int) */
} srmech_encode_phase_t;

typedef struct srmech_progress_ev {
    uint32_t struct_size;   /* == sizeof(srmech_progress_ev_t); the cbSize gate  */
    uint32_t phase;         /* an srmech_encode_phase_t value                    */
    uint64_t done;          /* EXACT numerator   (cardinality; always >= 0)      */
    uint64_t total;         /* EXACT denominator (0 == indeterminate; else > 0)  */
    /* rc276+ APPEND-ONLY fields go HERE. Older callbacks (struct_size-gated) skip. */
} srmech_progress_ev_t;

/* Return 0 to CONTINUE, nonzero to CANCEL. Fires inline on the encode thread;
 * MUST be cheap and MUST NOT re-enter srmech_* (it runs inside the encode). The
 * new typedef bumps SRMECH_ABI_VERSION 5 -> 6 (the CFUNCTYPE wire implication). */
typedef int (*srmech_progress_tick_cb_t)(const srmech_progress_ev_t *ev,
                                         void *user_data);

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

/* rc178 (ANNEX Batch A): standard RFC 2104 HMAC-SHA-256 over the srmech
 * SHA-256 compression. Writes the RAW 32-byte MAC of `msg[0..msg_len)` under
 * `key[0..key_len)` into `out32` (must be 32 bytes, must NOT alias inputs).
 * Byte-exact with Python hmac.new(key, msg, "sha256").digest() and the RFC
 * 4231 vectors; block size 64, ipad/opad 0x36/0x5c, over-length key reduced
 * with SHA-256 per the spec. A general primitive — the bus Bio-TOTP keystream
 * composes it. Bounded stack only (no malloc); arbitrary key_len / msg_len. A
 * NULL key/msg is allowed only with the matching length 0. New symbol only —
 * SRMECH_ABI_VERSION stays 3. */
srmech_status_t srmech_hmac_sha256(const uint8_t *key, size_t key_len,
                                   const uint8_t *msg, size_t msg_len,
                                   uint8_t       *out32);

/* rc200 (make_class -> C, leaf-batch 6/8; #887): the deterministic RBS-HDC
 * VECTOR MINTER — the Class-A content-addressed hypervector the sedenion
 * HDC-storage leaves (sed_write / materialize / read / clean) compose in C.
 * Mirror of Python srmech.signal_processing.mint_vector, byte-for-byte: writes
 * `n_bytes` of the SHA-256 chain
 *     out = ( SHA256(name || u64_be(0)) || SHA256(name || u64_be(1)) || ... )
 *           [0 : n_bytes]
 * where each counter is an 8-byte BIG-ENDIAN unsigned integer concatenated AFTER
 * the raw UTF-8 `name` bytes, chained (counter 0,1,2,...) until n_bytes are
 * filled and truncated to n_bytes. `name` may be NULL iff name_len == 0. `out`
 * is a caller buffer of at least n_bytes; the mint uses bounded stack only (no
 * malloc). n_bytes >= 1. Errors: SRMECH_ERR_NULL_ARG (out NULL, or name NULL
 * with name_len != 0); SRMECH_ERR_BAD_INPUT (n_bytes == 0). Routes through the
 * srmech SHA-256 core (Merkle-Damgard midstate over the name's full 64-byte
 * blocks, re-finalised per counter). Byte-identical to the pure chain, attested
 * by tests/test_sed_storage_c_rc200.py. ABI-additive: a new symbol, no callback
 * typedef, so SRMECH_ABI_VERSION stays 4. See srmech_sha256.c. */
srmech_status_t srmech_mint_vector(const uint8_t *name, size_t name_len,
                                   uint32_t n_bytes, uint8_t *out);

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
 * descriptors under srmech/cascade/catalogs/cascade_catalog/ for
 * declarative composition. (That path was srmech/amsc/_research/
 * cascade_catalog/ until v0.9.0rc364, when ADR-0010's first execution
 * slice moved the built-in catalogs to the composition layer.)
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
 * srmech.math.cyclic.gcd which itself enforces non-negative uint64
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
 * Rounding: the magnitude * fine_scale product is rounded to int64 by
 * a LIBM-FREE round-half-to-even (banker's rounding) Class-K/N branch
 * (v0.9.0rc211; formerly llrint(), the last libm import in libsrmech —
 * a bare-C-host executable needed -lm for it). The branch is byte-
 * identical to llrint() under the default IEEE-754 FE_TONEAREST mode
 * across the full 0 <= v < 2^63 range this cascade feeds it, and so
 * matches Python's built-in round() at the .5 boundary bit-exactly.
 * C99 round() is round-half-AWAY-from-zero and would diverge from
 * Python at the boundary.
 *
 * Error returns:
 *   SRMECH_OK              — success
 *   SRMECH_ERR_NULL_ARG    — out_num or out_den is NULL
 *   SRMECH_ERR_BAD_INPUT   — max_denominator < 1 or fine_scale < 1, or
 *                            magnitude * fine_scale >= 2^63 (int64 ABI
 *                            overflow; previously an unspecified
 *                            llrint() domain-error result — the Python
 *                            dispatch falls back to its Python
 *                            reference path on this status)
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
 * C parity for srmech.math.hdc's dim-8 octonion (Cayley-Dickson)
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
 * NUMERIC JPEG-like block-DCT compression pipeline (0.9.0rc214, #753) —
 * the float-DCT numeric op deferred out of the rc144/B6b exact coder
 * batch, now `closed_form_ops.jpeg`'s dedicated C peer.
 *
 * encode: per bs×bs block of the h×w row-major image —
 *   Z = (2·B₂·X)·(2·B₂ᵀ)           separable 2-D DCT-II (cols then rows)
 *   out = round_half_even(Z ⊘ QT)  Class-K quantise (banker's rounding,
 *                                  the exact C twin of Python round();
 *                                  no libm rint(), no fabs()/abs())
 * decode: per block — D = Q ⊙ QT; DCT-III (with the weight-1 j==0
 * correction) cols then rows; scale by 1/(2·bs)² into the (bh·bs)×(bw·bs)
 * row-major image.
 *
 * The cosine bases basis2/basis3 (bs×bs row-major DCT-II / DCT-III
 * matrices, B₂[k][j] = cos(π·k·(2j+1)/(2bs)), B₃[k][j] =
 * cos(π·(2k+1)·j/(2bs))) and the bs×bs quant table qt are CALLER inputs
 * (the Python side builds them once through the byte-exact Class-N
 * rational.cos cascade — the SAME basis the pure path uses; a bare-C host
 * builds them from the libm-free srmech_cos) — the rc149 iir precedent
 * (taps are caller data; the kernel is the loop). WHY A NEW SYMBOL: the
 * pipeline is BLOCKED + FUSED (strided block extract → two basis
 * multiplies → quantise, per block); routed through the generic dense
 * matmul it costs 4 dispatches per block and rebuilds the basis per call
 * — this kernel is ONE crossing for the whole image. NUMERIC (FPU-tol),
 * NOT byte-exact: within-tol (reldiff ≤ 1e-9) vs the pure-Python cascade,
 * the F1-FFT / F2-SVD / B4 contract. All scratch is bump-carved from the
 * CALLER arena ws (>= srmech_jpeg_ws_bound(bs) bytes = 2·bs² doubles; no
 * malloc; under-sized -> SRMECH_ERR_OVERFLOW). `out` MUST NOT alias the
 * input. Encode truncates to whole blocks (bh = h/bs, bw = w/bs; zero
 * blocks writes nothing); out is bh·bw·bs² doubles in block order, each
 * an exact integer value. qt entries must be nonzero (else
 * SRMECH_ERR_BAD_INPUT); a quantise quotient at or past 2^62 returns
 * SRMECH_ERR_OVERFLOW (OVERFLOW-not-wrap). The pure-Python cascade is the
 * COMPLETE alternative for no-C hosts. ABI-additive — SRMECH_ABI_VERSION
 * stays 4 (the Python ctypes shim hasattr-guards the symbols).
 * ------------------------------------------------------------------ */
size_t srmech_jpeg_ws_bound(size_t bs);

srmech_status_t srmech_jpeg_encode_f64(
    const double *image, size_t h, size_t w,
    const double *basis2, const double *qt, size_t bs,
    double *out, double *ws, size_t ws_len);

srmech_status_t srmech_jpeg_decode_f64(
    const double *qblocks, size_t bh, size_t bw,
    const double *basis3, const double *qt, size_t bs,
    double *out, double *ws, size_t ws_len);

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

/* Class I ∘ K ∘ C — the smallest INTEGER vector on the same ray as the
 * rational vector nums[i]/dens[i] (0.9.0rc378, task T1049; the keystone the
 * chemistry stoichiometry domain consumes). Clears denominators by their LCM
 * (Class I), strips the content = gcd of the entry magnitudes (Class I / K),
 * then pins the FIRST NONZERO entry positive (Class K pin-slot ∘ Class C
 * reorient — never abs()). Writes the primitive vector to out[0..n-1] and the
 * signed content to *out_content, with content * primitive == the cleared
 * integer vector L*v (the reduction is reversible). The all-zero vector maps
 * to all zeros with *out_content = 0.
 *
 * Signed int64 FAST PATH: nums / dens are int64 and out is a caller-owned
 * int64[n] (used as scratch, no malloc). Any entry == INT64_MIN, or any int64
 * intermediate overflow, returns SRMECH_ERR_OVERFLOW so the caller can fall
 * back to an arbitrary-precision path (the pure-Python body is byte-identical).
 * n == 0 -> *out_content = 0, no writes. den == 0 -> SRMECH_ERR_BAD_INPUT.
 * ABI-additive: a new symbol, so SRMECH_ABI_VERSION stays 10. */
srmech_status_t srmech_primitive_integer_vector(const int64_t *nums,
                                                const int64_t *dens, size_t n,
                                                int64_t *out,
                                                int64_t *out_content);

/* ------------------------------------------------------------------ *
 * The CHEMISTRY domain (0.9.0rc379, task T1050) — reaction networks as
 * exact-integer linear algebra. The three math ops (balance_reaction /
 * conservation_laws / deficiency) COMPOSE the already-C-backed QMat / graph
 * Laplacian / srmech_primitive_integer_vector surface (no new kernel).
 * srmech_parse_formula is the one genuinely new capability: a Class F/G
 * chemical-formula tokenizer. ABI-additive — SRMECH_ABI_VERSION stays 10.
 * ------------------------------------------------------------------ */

/* Max element-symbol bytes INCLUDING the NUL terminator (real symbols are
 * <= 3 chars); the fixed stride of the parse_formula output symbol buffer. */
#define SRMECH_ELEM_SYM_CAP 8u

/* Minimum ws_len BYTES for srmech_parse_formula given a formula of `len` bytes
 * (raw tokens + a group-start index stack; len+1 entries each). */
size_t srmech_parse_formula_ws_bound(size_t len);

/* Parse a chemical formula string into DISTINCT element counts (Class F/G; the
 * C twin of srmech.chemistry.formula.parse_formula). Handles multi-letter
 * symbols ([A-Z][a-z]*), implicit/explicit ASCII-digit counts, and NESTED '('
 * ... ')' groups with a trailing multiplier ("Ca3(PO4)2" -> Ca:3, P:2, O:8).
 * out_syms is out_cap * SRMECH_ELEM_SYM_CAP bytes (NUL-terminated symbols at
 * that stride); out_counts is int64[out_cap]; *out_n is the distinct-element
 * count. out_cap = len+1 is always sufficient. Returns SRMECH_OK,
 * SRMECH_ERR_BAD_INPUT (malformed / empty / unexpected byte / unbalanced
 * parens), or SRMECH_ERR_OVERFLOW (ws/out capacity or count overflow -> the
 * caller falls to the byte-identical pure-Python body). */
srmech_status_t srmech_parse_formula(const char *s, size_t len, void *ws,
                                     size_t ws_len, char *out_syms,
                                     int64_t *out_counts, size_t out_cap,
                                     size_t *out_n);

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

/* The 2π seam-fold DIVMOD with the quotient KEPT (0.9.0rc207; gh#1276 —
 * the #741 mod-should-be-divmod audit's first concrete instance):
 * theta = 2π·(*w_out) + (*theta_out), *w_out = round(theta/2π)
 * (round-half-toward-+inf, the Python _eph_round_div convention),
 * |*theta_out| <= π. Computed on the SAME integer 2/π quarter-turn
 * machinery srmech_cos / srmech_sin already fold with (no forked 2π
 * constant), so the (w, theta) pair IS the fold's own divmod — the
 * quotient (the METACYCLE winding) retained instead of discarded, the
 * remainder the EPICYCLE residue. Same domain as srmech_cos: returns
 * SRMECH_ERR_BAD_INPUT for Inf / |theta| >= 2^55 (*theta_out NaN); a
 * quiet-NaN input propagates as NaN with SRMECH_OK (the srmech_cos
 * convention); SRMECH_ERR_NULL_ARG for a NULL out pointer. */
srmech_status_t srmech_winding_fold(double theta, int64_t *w_out,
                                    double *theta_out);

/* rc313 — srmech_genome_discrete_writhe: the EXACT-integer DIRECTIONAL
 * discrete writhe of a polygonal backbone (the physical-topology peer of
 * the intrinsic mod-2 center-parity holonomy srmech_quaternion_cycle_holonomy,
 * rc309). Each vertex is an EXACT RATIONAL: xn[k]/xd[k], yn[k]/yd[k],
 * zn[k]/zd[k] (den != 0; sign folded into the numerator internally). The
 * writhe is the DISCRETE Gauss double-sum over non-adjacent segment PAIRS
 * in the z-drop projection,
 *   Wr = Σ ε_ij, ε_ij = sign((B−A)·((D−C)×(C−A))) when segments i,j cross
 *   in the xy-projection (four 2D orientation determinants decide the
 *   crossing), else 0; A=P_i,B=P_{i+1},C=P_j,D=P_{j+1}.
 * Every crossing decision and every ε is the SIGN of an INTEGER
 * determinant over srmech_bigint (the 4 pair-vertices are scaled to a
 * common positive integer denominator per axis) — no float can flip a
 * near-degenerate sign. This is the exact-INTEGER directional writhe (the
 * signed crossing number), NOT the transcendental smooth solid-angle
 * Gauss writhe; the mod-2 CWF check uses only its PARITY.
 *   closed != 0  → the wrap segment P_{n-1}→P_0 is included (a loop).
 *   out_num, out_den = the writhe as a reduced rational (den is always 1
 *      — the directional writhe is integer-valued; the pair form honors
 *      srmech's exact-rational contract).
 * Returns SRMECH_ERR_BAD_INPUT on a non-generic projection (an orientation
 *   determinant that decides a crossing vanishes) or a vanishing triple
 *   product at a proper crossing (the strands meet in 3D — not an
 *   embedding); SRMECH_ERR_NULL_ARG on a NULL array / out pointer;
 *   SRMECH_ERR_OVERFLOW on a too-small ws.
 *   ws / ws_len : caller workspace; size with
 *      srmech_genome_discrete_writhe_arena_bytes(n_points). All scratch is
 *      per-pair and rewound each pair, so the arena is O(1) in n_points.
 * Integer/exact (Class-N over the bigint surface); no float, no libm, no
 * malloc, no goto, no recursion. ABI additive → SRMECH_ABI_VERSION stays 10. */
size_t srmech_genome_discrete_writhe_arena_bytes(uint32_t n_points);

srmech_status_t srmech_genome_discrete_writhe(
    const int64_t *xn, const int64_t *xd,
    const int64_t *yn, const int64_t *yd,
    const int64_t *zn, const int64_t *zd,
    uint32_t n_points, int32_t closed,
    void *ws, size_t ws_len,
    int64_t *out_num, int64_t *out_den);

/* rc313 — srmech_genome_cwf_consistency_mod2: the mod-2 Călugăreanu–White–
 * Fuller check as a WHOLE-OP C peer (genome-fully-in-C). ORCHESTRATES the
 * existing C ops: Lk = the single fundamental cycle's center parity via
 * srmech_quaternion_cycle_holonomy over the Q₈ gains (edges_u/edges_v the
 * endpoints, gains 4·n_edges doubles or NULL = identity); Tw = the Q₈
 * negative-coset SIGN-accumulation parity (the sign of each gain's first
 * component past 1e-9); Wr = the directional writhe of the supplied embedding
 * (srmech_genome_discrete_writhe) when has_embedding != 0; verdict
 * (Tw + Wr) mod 2 == Lk mod 2. Outputs (all int32):
 *   *out_lk_center_parity   +1/-1/0 (the {1}/{−1}/pure-imaginary class)
 *   *out_lk_mod2            0/1, or -1 when the holonomy is NON-central (0)
 *   *out_tw_mod2            0/1
 *   *out_wr_mod2            0/1, or -1 when has_embedding == 0
 *   *out_consistent         0/1, or -1 when Lk is undefined OR no embedding
 * Byte-identical to the pure Python (same center parity + writhe integer).
 * SRMECH_ERR_BAD_INPUT unless there is exactly one fundamental cycle, or on a
 * degenerate/non-embedded writhe; SRMECH_ERR_NULL_ARG on a NULL edge/out
 * pointer; SRMECH_ERR_OVERFLOW on a too-small ws (size it with
 * srmech_genome_cwf_consistency_mod2_arena_bytes(n_nodes, n_edges, n_points)).
 * No malloc, no goto, no recursion. ABI additive → SRMECH_ABI_VERSION stays 10. */
size_t srmech_genome_cwf_consistency_mod2_arena_bytes(uint32_t n_nodes,
                                                      uint32_t n_edges,
                                                      uint32_t n_points);

srmech_status_t srmech_genome_cwf_consistency_mod2(
    const uint32_t *edges_u, const uint32_t *edges_v, const double *gains,
    uint32_t n_edges, uint32_t n_nodes, int32_t has_embedding,
    const int64_t *xn, const int64_t *xd, const int64_t *yn, const int64_t *yd,
    const int64_t *zn, const int64_t *zd, uint32_t n_points, int32_t closed,
    void *ws, size_t ws_len,
    int32_t *out_lk_mod2, int32_t *out_lk_center_parity, int32_t *out_tw_mod2,
    int32_t *out_wr_mod2, int32_t *out_consistent);

/* rc314 — the CODON READ-LAYER whole-op C peers (genome-fully-in-C). Biology
 * reads the genome in CODONS (triplets); the ribosome IMPOSES that reading over
 * the stored strand. Both are PURE READS: they store nothing and change no
 * on-disk format (GENOME_FORMAT_VERSION stays 16). No float, no libm, no abs().
 * ABI additive → SRMECH_ABI_VERSION stays 10.
 *
 * srmech_genome_codon_read: read `strand` (n Q8 base symbols) as codons in
 * reading frame `phase` in {0,1,2}, writing one amino-acid byte per codon into
 * `out`. Each symbol is projected (& 3) FIRST so the Q8 CENTER SIGN BIT never
 * touches identity (biology reads 4 bases, not 8 signed states: coset 0->U/T,
 * 1->C, 2->A, 3->G). A 3-slot window slides from `phase`; the base-4 index
 * i = 16*b0 + 4*b1 + b2 in [0,64) indexes `ncbieaa` (the 64-byte NCBI
 * transl_table=1 amino-acid string — attested reference data passed IN, never
 * baked). `out` MUST hold >= n/3 bytes; `*out_len` receives the codon count.
 * Class-I (project + Z3 frame) o Class-E (dense catalog). Byte-identical to the
 * pure Python. Errors: SRMECH_ERR_NULL_ARG (any pointer NULL),
 * SRMECH_ERR_BAD_INPUT (phase > 2). */
srmech_status_t srmech_genome_codon_read(const uint8_t *strand, uint32_t n,
                                         uint32_t phase, const uint8_t *ncbieaa,
                                         uint8_t *out, uint32_t *out_len);

/* srmech_genome_codon_frame_monodromy: the Z3 reading-frame monodromy of a
 * CIRCULAR strand of `n` base symbols — going once around shifts the frame
 * phi -> phi + n (mod 3), so `*out` = n mod 3 in {0,1,2}. A pure Class-I cyclic
 * read (V4 projection preserves length, so only the symbol count matters); the
 * winding Lk lives in the sign bit, NOT here. Errors: SRMECH_ERR_NULL_ARG (out
 * NULL). */
srmech_status_t srmech_genome_codon_frame_monodromy(uint32_t n, uint32_t *out);

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

/* ------------------------------------------------------------------
 * 0.9.0rc328 (task #893 / #888 rec (c)): the Laplace–Beltrami α-family —
 * two closed-form Class-L constructors that expose the discrete LB
 * operator as a WEIGHTING/NORMALIZATION of the shipped weighted Laplacian
 * (NOT a PDE / mesh-FEA solve; see docs/srmech/notes/laplace_beltrami_scoping.md).
 *
 * srmech_graph_mass_normalized_laplacian — the α-family / mass-normalized
 * Laplacian.  Builds L = D − W (the weighted combinatorial Laplacian) and
 * applies a diagonal mass normalization:
 *   kind == 0  symmetric   L̂ = M^(−1/2) (D − W) M^(−1/2)
 *   kind == 1  random-walk L̂ = M^(−1)   (D − W)
 * `masses` (n doubles) is the diagonal mass; NULL → the degree D (the
 * α = 0 connectivity case, which recovers srmech_graph_normalized_laplacian
 * up to the exact-1 diagonal convention).  A supplied mass (e.g. Voronoi
 * areas) is the α = 1 metric case — the discrete Laplace–Beltrami spectrum.
 * m_i <= 0 → scale 0 (isolated / massless vertex, mirroring normalized_lap).
 * `scale_ws` is a CALLER workspace of >= n doubles (holds the per-node
 * scale s_i; caller-arena, no malloc/static — reentrant on disjoint ws).
 * The one algebraic step is the D^(−1/2) sqrt (srmech_rational_sqrt, NOT
 * libm); byte-exact with the pure-Python Class-N cascade. No node cap.
 * ABI-additive: a new symbol, so SRMECH_ABI_VERSION stays 10. */
srmech_status_t srmech_graph_mass_normalized_laplacian(uint32_t        n,
                                                       uint32_t        n_edges,
                                                       const uint32_t *edges_u,
                                                       const uint32_t *edges_v,
                                                       const double   *weights,
                                                       const double   *masses,
                                                       uint32_t        kind,
                                                       double         *scale_ws,
                                                       double         *out_matrix);

/* srmech_graph_cotangent_weights — the cotangent-weight Laplacian weight
 * constructor (the discrete Laplace–Beltrami weights on a triangulated
 * manifold; Pinkall & Polthier 1993).  Takes the triangle geometry as
 * given NUMBERS (positions as data — algebra/spectral only, NOT CAD
 * mesh-contact) and emits, per triangle, the THREE per-corner contributions
 * `½·cot(θ)` for the edge opposite each vertex.  For the apex `k` opposite
 * edge (i, j), with u = p_i − p_k, v = p_j − p_k:
 *   cot θ = (u·v) / |u×v|,   |u×v| = sqrt(|u|²|v|² − (u·v)²)   (Lagrange)
 * — the Lagrange cross magnitude is ≥ 0 in 2-D and 3-D alike (NO abs; the
 * signed area is a Class-K pin-slot the magnitude does not need).  NO trig
 * (no cos/sin/atan): the only irrationality is one algebraic sqrt per corner
 * (srmech_rational_sqrt).  The 3·n_tri (edge, weight) contributions FEED
 * srmech_graph_dense_laplacian, whose parallel-edge accumulation sums the
 * two triangles sharing an edge into the standard ½(cot α + cot β).
 *   tri        : 3·n_tri vertex indices (i, j, k per triangle).
 *   positions  : n_vert·dim doubles, row-major; dim ∈ {2, 3}.
 *   out_edges_u / out_edges_v / out_weights : 3·n_tri each (caller-alloc).
 * Degenerate (collinear) triangle → SRMECH_ERR_BAD_INPUT.  No node cap.
 * ABI-additive: a new symbol, so SRMECH_ABI_VERSION stays 10. */
srmech_status_t srmech_graph_cotangent_weights(uint32_t        n_tri,
                                               const uint32_t *tri,
                                               const double   *positions,
                                               uint32_t        dim,
                                               uint32_t        n_vert,
                                               uint32_t       *out_edges_u,
                                               uint32_t       *out_edges_v,
                                               double         *out_weights);

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
 *
 * Attested SSoT (the flux/magnetic-Laplacian construction): E. H. Lieb &
 * M. Loss, "Fluxes, Laplacians, and Kasteleyn's Theorem", Duke Math. J.
 * 71 (1993) 337-363; OA preprint arXiv:cond-mat/9209031. (The complex-
 * unit-gain-graph spectral framing: N. Reff, "Spectral Properties of
 * Complex Unit Gain Graphs", Linear Algebra Appl. 436 (2012) 3165-3176;
 * arXiv:1110.4554.)
 * ABI-additive: a new symbol, so SRMECH_ABI_VERSION stays 3. */
srmech_status_t srmech_graph_magnetic_laplacian(uint32_t        n,
                                                uint32_t        n_edges,
                                                const uint32_t *edges_u,
                                                const uint32_t *edges_v,
                                                const double   *weights,
                                                double          q,
                                                const double   *charges,
                                                double         *out_matrix);

/* 0.9.0rc229 (#687): the V4-gain (Klein-4-sector) Laplacian — the EVEN-
 * channel fuller partner of srmech_graph_magnetic_laplacian. Each edge
 * carries a V4 = Z2 x Z2 gain g = (g0, g1) as TWO sign bits packed low..
 * high in a uint8 `gains[e]` in {0,1,2,3} (NULL -> all identity 0). V4
 * has FOUR real characters chi_ab(g) = (-1)^(a*g0 + b*g1), so the object
 * decomposes into FOUR real signed Laplacians L_chi = D_bar - chi(g_e)*A
 * (the two-bit generalization of the one-bit signed Laplacian). The two
 * gain bits are SYMMETRIC — neither is privileged. `out_matrix` is
 * 4*n*n doubles, SECTOR-major: sector k in {0,1,2,3} = (a = k>>1, b = k&1)
 * fills out[k*n*n ...], so k=0 -> chi00 (trivial; == dense_laplacian for
 * unit gains), 1 -> chi01, 2 -> chi10, 3 -> chi11 (each real row-major
 * n*n). The signed degree D_bar_ii = sum|A_ij| is the Class-K magnitude
 * (no abs()) and is character-independent. The four-sector Laplacian
 * spectrum equals the ordinary Laplacian spectrum of the V4 abelian COVER
 * (4n nodes) — the abelian-cover character decomposition (Bilu & Linial,
 * "Lifts, Discrepancy and Nearly Optimal Spectral Gap", Combinatorica 26
 * (2006) 495-519; arXiv:math/0312022; generalized from the Z2 2-lift to
 * V4). No node cap, NO scratch (staged in-place in `out_matrix`); an
 * out-of-range endpoint or gain > 3 -> SRMECH_ERR_BAD_INPUT. ABI-additive:
 * a new symbol, so SRMECH_ABI_VERSION stays 4. */
srmech_status_t srmech_graph_klein4_gain_laplacian(uint32_t        n,
                                                   uint32_t        n_edges,
                                                   const uint32_t *edges_u,
                                                   const uint32_t *edges_v,
                                                   const double   *weights,
                                                   const uint8_t  *gains,
                                                   double         *out_matrix);

/* 0.9.0rc229 (#687): cycle_holonomy — the ODD channel the (Hermitian /
 * signed) spectrum provably cannot carry (a conjugated Hermitian matrix
 * has the same eigenvalues, so no eigenvalue read carries the which-way
 * sign). A gain graph is determined up to switching by its cycle gains
 * (Zaslavsky, "Signed graphs", Discrete Appl. Math. 4 (1982) 47-74). This
 * builds a spanning forest (union-find; first-encountered edge = tree
 * edge), then for each co-tree edge computes the fundamental cycle's NET
 * charge: per-edge charges in TURNS as reduced rationals
 * charge_num[e]/charge_den[e] (NULL -> 0), summed exactly around the cycle
 * and reduced mod 1 (Class I mod-1 cyclic o Class L graph; NO eigensolve).
 * The holonomy is invariant under node re-gauging (a coboundary
 * telescopes) and is 0 for every cycle IFF the gain graph is balanced
 * (Zaslavsky); it distinguishes +c from -c (1/4 vs 3/4 mod 1) — the
 * chirality the sector spectra cannot. Denominators must be > 0 and both
 * |num| and den <= 1e9 so the exact int64 arithmetic cannot overflow; a
 * larger magnitude / a reduced intermediate past the limit / an
 * undersized arena -> SRMECH_ERR_OVERFLOW (the pure-Python Fraction path
 * is the exact complete alternative). Outputs (each length >= n_edges):
 * out_num/out_den = reduced holonomy in [0,1) per cycle; out_cycle_u/v =
 * the co-tree edge per cycle; *out_n_cycles = the cyclomatic number.
 * `ws` is a caller arena of >= srmech_graph_cycle_holonomy_arena_bytes
 * bytes (no malloc). ABI-additive: new symbols, SRMECH_ABI_VERSION stays
 * 4. */
size_t srmech_graph_cycle_holonomy_arena_bytes(uint32_t n, uint32_t n_edges);
srmech_status_t srmech_graph_cycle_holonomy(uint32_t        n,
                                            uint32_t        n_edges,
                                            const uint32_t *edges_u,
                                            const uint32_t *edges_v,
                                            const int64_t  *charge_num,
                                            const int64_t  *charge_den,
                                            int64_t        *out_num,
                                            int64_t        *out_den,
                                            uint32_t       *out_cycle_u,
                                            uint32_t       *out_cycle_v,
                                            uint32_t       *out_n_cycles,
                                            void           *ws,
                                            size_t          ws_len);

/* 0.9.0rc309 (#944 follow-on): the NON-ABELIAN generalization of
 * srmech_graph_cycle_holonomy — the k=2 discrete holonomy channel over the
 * quaternion units Q8 = {+-1, +-i, +-j, +-k} (H "which-way" / Lk-analog
 * reader). Same union-find spanning-forest base-point scaffolding (first-
 * encountered edge = tree edge), but edge gains are UNIT QUATERNIONS (4
 * doubles each; NULL -> identity). Per fundamental cycle the holonomy is the
 * ordered quaternion PRODUCT walked around the cycle,
 *     H = P_u . g_uv . conj(P_v),
 * where P_x = the ordered product of edge gains along the tree path root->x
 * (a reversed edge contributes conj(gain) = its inverse). Under a node-wise
 * re-gauge g_uv -> s_u . g_uv . conj(s_v) the intermediate factors telescope
 * and H -> s_root . H . conj(s_root): H is CONJUGATED by the base-point gauge,
 * so its CONJUGACY CLASS is gauge-invariant.
 *
 * THE GAUGE-INVARIANT READ. For unit quaternions (SU(2)) the conjugacy class
 * is a level set of the SCALAR part w = Re(H) (a conjugation invariant:
 * Re(s.H.conj(s)) = Re(H) exactly). For a Q8-derived connection w in
 * {+1, 0, -1}, giving THREE frame-free classes (out_class_index):
 *   w ~ +1 -> 0 = {1}          center_parity +1
 *   w ~ -1 -> 1 = {-1}         center_parity -1   (the spinor / Lk half-twist)
 *   w ~  0 -> 2 = {+-i,+-j,+-k} center_parity  0  (pure-imaginary)
 * NOTE (measured, not assumed): the finer 5-class Q8 split {+-i}/{+-j}/{+-k}
 * is invariant only under DISCRETE Q8 re-gauge; under CONTINUOUS unit-
 * quaternion re-gauge SU(2) merges the three imaginary axes (i and j are
 * SU(2)-conjugate), so only the scalar-part class above is frame-free. That is
 * the sound keystone this op ships. out_center_parity is the {1}-vs-{-1}
 * central sign (a class function, hence also invariant). A holonomy whose
 * scalar is far from {-1, 0, 1} means the gains were not Q8/unit-consistent ->
 * SRMECH_ERR_BAD_INPUT (tolerance 1e-9).
 *
 * Outputs (each length >= n_edges except out_holonomy): out_class_index +
 * out_center_parity per fundamental cycle; out_cycle_u/v = the co-tree edge;
 * out_holonomy (NULLABLE; length >= 4*n_edges) = the raw H quaternion per
 * cycle; *out_n_cycles = the cyclomatic number. `ws` is a caller arena of >=
 * srmech_quaternion_cycle_holonomy_arena_bytes(n, n_edges) BYTES (no malloc;
 * ws_len guarded in BYTES per the rc307 discipline). Additive symbols ->
 * SRMECH_ABI_VERSION stays 10. See srmech_laplacian.c. */
size_t srmech_quaternion_cycle_holonomy_arena_bytes(uint32_t n,
                                                    uint32_t n_edges);
srmech_status_t srmech_quaternion_cycle_holonomy(
    uint32_t        n,
    uint32_t        n_edges,
    const uint32_t *edges_u,
    const uint32_t *edges_v,
    const double   *gains,
    uint32_t       *out_class_index,
    int32_t        *out_center_parity,
    uint32_t       *out_cycle_u,
    uint32_t       *out_cycle_v,
    double         *out_holonomy,
    uint32_t       *out_n_cycles,
    void           *ws,
    size_t          ws_len);

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
 * power iteration.
 *
 * `ws` is a caller arena of >= srmech_laplacian_fiedler_sparse_arena_bytes(n)
 * BYTES (rc307: BYTES, like the rest of the caller-arena surface — the pre-rc307
 * DOUBLES-count contract was the odd one out and is gone; see the v10 ABI note).
 * ABI: the *_arena_bytes helper is a new additive symbol, but rc307 also flips
 * this guard's ws_len UNIT to BYTES, which is a breaking wire-contract change ->
 * SRMECH_ABI_VERSION 9 -> 10. */
size_t srmech_laplacian_fiedler_sparse_arena_bytes(uint32_t n);

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
 * vectors live in RAM (the caller `ws` arena, >= srmech_laplacian_fiedler_sparse_arena_bytes(n)
 * BYTES — rc307: BYTES, no compiled-in node cap), so a low-RAM target can PARTITION
 * a graph whose edge list does not fit RAM: the low-RAM ENCODE for graph partition
 * (composes §52.1 cooccurrence_topk for the bounded edge SET). `out_vec` (length n)
 * receives the sign-bearing Fiedler vector; n < 2 -> the zero vector. A read that is
 * not a whole number of records (truncated file) -> SRMECH_ERR_BAD_INPUT; an
 * out-of-range endpoint -> SRMECH_ERR_BAD_INPUT. rc307 flips this guard's ws_len
 * UNIT to BYTES -> SRMECH_ABI_VERSION 9 -> 10 (see the v10 note). */
srmech_status_t srmech_laplacian_fiedler_sparse_file(uint32_t      n,
                                                     const char   *path,
                                                     uint32_t      max_iters,
                                                     double       *out_vec,
                                                     double       *ws,
                                                     size_t        ws_len);

/* §101 (v0.9.0rc275): the ENCODE-PROGRESS overload of the out-of-core Fiedler.
 * Byte-identical to srmech_laplacian_fiedler_sparse_file (which forwards here with
 * tick == NULL), but fires the caller `tick` heartbeat once per power-iteration
 * (phase SRMECH_PHASE_PARTITIONING, done = it+1, total = max_iters). A nonzero
 * tick return CANCELS: the loop returns SRMECH_CANCELLED with `out_vec` left as
 * the zeroed init (a valid "no cut" vector, byte-indistinguishable from an
 * edgeless graph). `tick` may be NULL (runs exactly as the plain symbol).
 * `ws` is a caller arena of >= srmech_laplacian_fiedler_sparse_arena_bytes(n)
 * BYTES (rc307). The srmech_progress_tick_cb_t typedef is what bumped
 * SRMECH_ABI_VERSION 5 -> 6; rc307's ws_len BYTES unification bumps 9 -> 10.
 * See the srmech_progress_ev_t block above. */
srmech_status_t srmech_laplacian_fiedler_sparse_file_progress(
    uint32_t                   n,
    const char                *path,
    uint32_t                   max_iters,
    double                    *out_vec,
    double                    *ws,
    size_t                     ws_len,
    srmech_progress_tick_cb_t  tick,
    void                      *tick_user);

/* §100 G1 (v0.9.0rc284): the OUT-OF-CORE RECURSIVE SPECTRAL BISECTION driver
 * — the `while pending` recursion around srmech_laplacian_fiedler_sparse_file
 * that, until rc284, existed ONLY in Python. That is what made §100 G1 the
 * deepest C-host parity gap: the Fiedler ENGINE has been native since rc168,
 * but a bare-C host could bisect ONCE and no further, so it could not build a
 * partition at all. With this symbol the whole op runs standalone.
 *
 * Partitions the graph in `edges_path` (the packed 16-byte-record file
 * srmech_laplacian_fiedler_sparse_file reads, written by write_packed_graph)
 * into community TOMES under `work_dir`. Every pending sub-graph and every
 * finished tome lives ON DISK — peak RAM is the caller arena alone, so the
 * structure may exceed RAM. A set of <= max_tome nodes (or < 2, or at
 * max_depth) becomes a leaf tome; otherwise it is sign-split by the streaming
 * Fiedler and both halves are re-queued.
 *
 * NOT recursive in C (JPL Rule 1): an explicit arena-backed LIFO stack carries
 * (serial, depth), in the Python driver's exact pop/append order, so both
 * coherency projections emit byte-identical tome files in byte-identical
 * order. Node sets are ASCENDING by construction, so the original->local
 * relabel is a binary search over the set — no map, no allocation.
 *
 * `work_dir` is created if absent (as are work_dir/queue + work_dir/tomes);
 * an existing one is REUSED. `tome_paths_out` is a caller array of
 * `paths_cap` fixed-width 512-byte path slots (NUL-terminated); a partition
 * needing more tomes than that returns SRMECH_ERR_OVERFLOW. `tome_sizes_out`
 * (>= paths_cap entries) receives each tome's node count. *n_tomes_out gets
 * the count written. n == 0 yields exactly ONE empty tome — matching the
 * Python projection, which seeds the queue with the empty root set and retires
 * it like any other leaf (an early-out here would be a parity divergence).
 *
 * `ws` is a caller arena of >= srmech_laplacian_recursive_cut_arena_bytes(n)
 * BYTES — so there is no compiled-in node cap; the bound is the caller's RAM.
 * (rc307: the whole laplacian caller-arena surface, fiedler_sparse family
 * included, now counts ws_len in BYTES — the DOUBLES odd-one-out is gone.)
 *
 * §101: `tick` fires once per queue pop (phase SRMECH_PHASE_PARTITIONING,
 * done = Σ finalized-tome sizes so far — EXACT and monotone, total = n). A
 * nonzero return CANCELS and returns SRMECH_CANCELLED after promoting every
 * still-pending set to a coarse, uncut tome: the outputs then still partition
 * ALL n nodes (a valid COARSER partition), never a torn result. `tick` may be
 * NULL. Reuses the existing srmech_progress_tick_cb_t typedef, so this is a
 * purely ABI-ADDITIVE pair of symbols -> SRMECH_ABI_VERSION stays 6. */
size_t srmech_laplacian_recursive_cut_arena_bytes(uint32_t n);

srmech_status_t srmech_laplacian_recursive_cut(uint32_t                  n,
                                               const char               *edges_path,
                                               const char               *work_dir,
                                               uint32_t                  max_tome,
                                               uint32_t                  max_iters,
                                               uint32_t                  max_depth,
                                               uint32_t                 *tome_sizes_out,
                                               char                     *tome_paths_out,
                                               size_t                    paths_cap,
                                               uint32_t                 *n_tomes_out,
                                               double                   *ws,
                                               size_t                    ws_len,
                                               srmech_progress_tick_cb_t tick,
                                               void                     *tick_user);

/* The fixed width of one `tome_paths_out` slot, in bytes. */
#define SRMECH_RECURSIVE_CUT_PATH_MAX 512u

/* §100 G3 (rc321, task #904) — the WHOLE-OP C peer of the GRAPH partition
 * srmech.biology.genome.genome_partition. NOT the strand-recovery op that shares the
 * C name srmech_genome_partition: this reads a directed relational GRAPH into a
 * nuclear-core vs plasmid-periphery split BY ITS OWN TOPOLOGY. It composes
 * srmech_laplacian_recursive_cut (the out-of-core community assignment) with an
 * exact-integer participation read + the antimode histogram DECISION + a per-node
 * classify + group assembly — all in C, so a bare-C host builds the partition with
 * NO Python present (closes the deepest half of the §100 G-series parity ladder).
 *
 * The result STRUCT carries the scalar read-out (the histogram DECISION + the
 * one-DNA-type + node counts); the caller-arena OUT arrays carry the per-node and
 * per-group vectors. `struct_size` is the cbSize forward-compat gate (a later
 * APPEND-only growth is size-gated, never a re-bump). `threshold_bin` /
 * `peak_low_bin` / `peak_high_bin` / `one_dna_type` / `valley_count` use -1 as the
 * Python `None` sentinel (unimodal). ADDITIVE — a new struct + two symbols reusing
 * the existing srmech_progress_tick_cb_t typedef (NO new callback typedef), so
 * SRMECH_ABI_VERSION stays 10, SRMECH_GENOME_FORMAT_VERSION stays 16 (this op reads
 * a packed GRAPH edge file + writes recursive_cut tomes — it never touches the genome
 * strand format). */
typedef struct srmech_genome_graph_partition_result {
    uint32_t struct_size;    /* == sizeof(srmech_genome_graph_partition_result_t) */
    uint32_t n_communities;  /* the recursive_cut tome count                       */
    uint32_t n_groups;       /* emitted (community, type) slices (<= 2*n_comm)      */
    uint32_t cancelled;      /* 0/1 — §101: recursive_cut returned a clean partial  */
    uint32_t bimodal;        /* 0/1 — a clean antimode valley was found             */
    uint32_t mode_bin;       /* the single dominant mode (fixes one_dna_type)       */
    int32_t  threshold_bin;  /* the low occupied bin at the split; -1 == None       */
    int32_t  peak_low_bin;   /* -1 == None (unimodal)                               */
    int32_t  peak_high_bin;  /* -1 == None (unimodal)                               */
    int32_t  one_dna_type;   /* -1 None, 0 nuclear, 1 plasmid                        */
    int64_t  valley_count;   /* the in-gap antimode; -1 == None                      */
    uint64_t gap;            /* smaller_mode - valley (both non-negative; no abs)   */
    uint64_t node_nuclear;   /* count of nuclear-classified nodes                    */
    uint64_t node_plasmid;   /* count of plasmid-classified nodes                    */
} srmech_genome_graph_partition_result_t;

/* Arena size (BYTES) for srmech_genome_graph_partition: the recursive_cut
 * sub-arena + cross/tot/counts accumulators + the tome-path/size buffers + the
 * node-bin + tome-read scratch. `n_edges` is accepted for signature symmetry but
 * the participation read STREAMS the edge file (never resident), so it is unused.
 * `n_bins` must be >= 2; pass `paths_cap = n + 1` (the op uses that internally). */
size_t srmech_genome_graph_partition_arena_bytes(uint32_t n, uint32_t n_edges,
                                                 uint32_t n_bins, size_t paths_cap);

/* Run the whole GRAPH partition. `edges_path` is a packed 16-byte-record edge file
 * (write_packed_graph format: uint32 u | uint32 v | double w, integer weights); the
 * op writes the recursive_cut tomes under `work_dir`. Per-node OUT arrays
 * (>= n): community_out (tome index), part_num_out / part_den_out (the exact reduced
 * participation rational). counts_out (>= n_bins) receives the participation
 * histogram. The group OUT arrays (>= groups_cap, with groups_cap >= 2*(n+1)) receive
 * each slice's community / type (0 nuclear, 1 plasmid) / size / reduced participation;
 * group_members_out (>= n) is the flat member list in group-emission order (per group
 * ascending). *result_out carries the scalar read-out. `tick` (may be NULL) threads
 * the §101 partition heartbeat into recursive_cut; a nonzero return CANCELS -> the op
 * returns SRMECH_CANCELLED with the community assignment still a valid COARSER
 * partition (participation / groups are then not computed — the Python projection
 * emits the same clean partial). `ws` is a caller arena of >=
 * srmech_genome_graph_partition_arena_bytes(n, 0, n_bins, n + 1) BYTES (no malloc).
 * NEVER abs (all values are non-negative). ADDITIVE — SRMECH_ABI_VERSION stays 10. */
srmech_status_t srmech_genome_graph_partition(
    uint32_t n, const char *edges_path, const char *work_dir,
    uint32_t max_tome, uint32_t n_bins, uint32_t max_iters, uint32_t max_depth,
    uint32_t *community_out, uint64_t *part_num_out, uint64_t *part_den_out,
    uint64_t *counts_out,
    uint32_t *group_comm_out, uint32_t *group_type_out, uint32_t *group_size_out,
    uint64_t *group_num_out, uint64_t *group_den_out,
    uint32_t *group_members_out, uint32_t groups_cap,
    srmech_genome_graph_partition_result_t *result_out,
    void *ws, size_t ws_len,
    srmech_progress_tick_cb_t tick, void *tick_ctx);

/* §75-sparse (issue #698): the STREAMING k-extreme resonant read — the
 * n-unbounded C twin of srmech.biology.coupling.resonant_spectrum_sparse. Reads the
 * bottom-k + top-k modes of the COMBINATORIAL Laplacian L = D - W by power
 * iteration + Gram-Schmidt deflation, STREAMING the packed edge file (the same
 * 16-byte-record format srmech_laplacian_fiedler_sparse_file reads) via the PAL
 * — only the O(n) `ws` arena + the caller `out_modes` (O(k*n)) are resident, so a
 * low-RAM target reads the F172 storage signature at unbounded n (past the n<=256
 * dense-eigensolver wall). Bottom modes ride the shift sigma*I - L (sigma =
 * 2*max_deg + 1, a Gershgorin lambda_max bound); top modes ride L. Each new mode
 * deflates against every found mode, so bottom/top never collide and 2k >= n
 * yields the full spectrum. `k` modes per extreme SIDE; the caller pre-sizes
 * out_tensions[2k] + out_modes[2k*n] (row m = mode m, row-major); *out_count
 * receives the number of DISTINCT modes written (<= min(2k, n)), in found order
 * (bottom ascending, then top descending — the caller sorts). `ws` (ws_len BYTES)
 * sized from srmech_laplacian_k_extreme_modes_arena_bytes. n == 0 writes nothing
 * + *out_count = 0. Returns SRMECH_ERR_NULL_ARG for a NULL pointer,
 * SRMECH_ERR_BAD_INPUT for a too-small arena / a truncated or out-of-range edge
 * file. ABI-additive (new symbols) -> SRMECH_ABI_VERSION stays 4. */
size_t srmech_laplacian_k_extreme_modes_arena_bytes(uint32_t n);

srmech_status_t srmech_laplacian_k_extreme_modes_file(uint32_t   n,
                                                      const char *path,
                                                      uint32_t    k,
                                                      uint32_t    max_iters,
                                                      double     *out_tensions,
                                                      double     *out_modes,
                                                      uint32_t   *out_count,
                                                      double     *ws,
                                                      size_t      ws_len);

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

/* ── the GENERAL (non-Hermitian) eigenvalue solver (v0.9.0rc299, `#918`) ──
 *
 * The whole-op C peer of `srmech.math.laplacian.mat_eigvals`. Until rc299 the
 * C surface had three eigen-paths and none was general — srmech_jacobi_eigvals
 * (real symmetric), srmech_hermitian_eigendecompose_ws (complex Hermitian) and
 * the exact integer srmech_eigvec_exact / srmech_complex_isolate — while
 * `mat_eigvals` was classified `composition_of_c`, a bucket annotated
 * "standalone-ready". It was not: balancing, the Hessenberg reduction, the
 * deflation loop, the Wilkinson shift ladder and {QR} were Python-only, and
 * `mat_eigvals` has no Hermitian fast path, so a bare-C host could not run it
 * for ANY input. rc285 filed that gap; this closes it.
 *
 * `a_interleaved` is n*n interleaved (re, im) pairs, row-major, and may be a
 * general complex or real matrix (a real matrix is passed with zero imaginary
 * parts). `out_eigvals` receives n interleaved (re, im) eigenvalues in
 * DEFLATION order — the multiset is the contract; the ORDER is not, exactly as
 * on the Python side (an eigenvalue multiset is unique only as a set).
 *
 * `max_sweeps` bounds the shifted-QR iteration at max_sweeps*n steps; 500
 * mirrors the Python default. Non-convergence returns SRMECH_ERR_OVERFLOW
 * rather than the raw diagonal of an un-converged block — for a companion
 * matrix that diagonal is all zeros, which is the historic all-zero bug.
 *
 * `workspace` is caller-supplied (no malloc), ws_len >= the _ws_size below.
 *
 * PARITY: NUMERIC (FPU-tol), not byte-exact. Both projections run the same
 * operation sequence in IEEE double and share srmech_rational_sqrt bit-for-bit;
 * the one divergence is the complex MODULUS, which on the Python side roots an
 * EXACT rational sum-of-squares (arbitrary-precision Class-N) and here is the
 * scaled float form. That is a ~1 ulp difference feeding a shift estimate and
 * a reflector phase, far below the deflation tolerance.
 *
 * No libm, no <complex.h>, no malloc, no recursion. Additive symbols ->
 * SRMECH_ABI_VERSION unchanged. */
size_t srmech_mat_eigvals_ws_size(uint32_t n);

srmech_status_t srmech_mat_eigvals_ws(
    uint32_t       n,
    const double  *a_interleaved,
    uint32_t       max_sweeps,
    double        *out_eigvals,
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
 * srmech.cascade.exact_dft. A power-of-two-length integer / Gaussian-
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
 * numeric twin of srmech.cascade.spectral_cascades.fft/ifft that the
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
 * srmech.biology.coupling.resonant_spectrum. Reads a real-symmetric coupling
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
 * srmech.math.laplacian.heat_trace / .ground_state_flux_response.
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
 * The spectral SPINE (0.9.0rc204; gh#1324 / F1167–F1169) — a Class-L
 * COMPOSITE over the existing kernels (srmech_graph_dense_adjacency +
 * srmech_hermitian_eigendecompose_ws), the C twin of
 * srmech.math.laplacian.spectral_spine. It completes the community/spine
 * PAIR srmech already ships: srmech_laplacian_fiedler_sparse /
 * srmech_three_fold_bands read the LOW modes (2-/3-way community split),
 * this reads the DOMINANT mode. The largest-eigenvalue eigenvector of a
 * (signed) graph Laplacian concentrates on the structurally CENTRAL
 * items; its top-|component| nodes ARE the spine. Domain-free (edges =
 * any relational graph).
 *
 * Build → decompose → select: the signed Laplacian L = D̄ − A (signed
 * degree D̄_ii = Σ|A_ij|, the Class-K magnitude — a sign branch, NOT
 * fabs) is built from the edge list (srmech_graph_dense_adjacency then
 * the in-arena D̄ − A pass), embedded real → interleaved-complex, and
 * ONE srmech_hermitian_eigendecompose_ws gives the ascending spectrum +
 * unitary eigenvectors. The DOMINANT eigenvector is the LAST column
 * (largest λ); the top-k nodes by |component|² (re²+im², a Class-K
 * magnitude-square — NO fabs, NO sqrt) are the spine, ordered by
 * descending magnitude, ties broken by ascending index (bit-matching the
 * Python op's sort key). NUMERIC (FPU-tol): the eigenvector basis is
 * non-unique, so native == pure agrees WITHIN-TOL (the selected index
 * SET / order is stable for a non-degenerate dominant eigenvalue), NOT
 * byte-for-byte — contrast the exact-integer ops. Standalone-complete:
 * all scratch is bump-carved from the CALLER arena `ws` (no malloc). The
 * Python op is the COMPLETE alternative for a no-C host. ABI-additive:
 * new symbols, so SRMECH_ABI_VERSION stays 4.
 * ------------------------------------------------------------------ */

/* The caller arena size IN BYTES srmech_spectral_spine needs for an n×n
 * signed Laplacian (the real adjacency + the interleaved-H copy + the
 * eigenvector staging + the eigensolve workspace + eigvals + the
 * magnitude-square scratch). Size `ws_len` ≥ this. */
size_t srmech_spectral_spine_arena_bytes(uint32_t n);

/* The spectral spine of the relational graph on `n` nodes with `n_edges`
 * undirected edges (edges_u/edges_v parallel uint32 arrays; `weights`
 * NULL → unit weights, may be negative for a signed graph). Writes the
 * top-min(k, n) central node indices (descending |component| of the
 * dominant eigenvector, ties by ascending index) into `out_spine` (caller
 * sizes it ≥ min(k, n)) and their count into `*out_count`. n == 0 (empty
 * graph) writes *out_count = 0 and nothing else. `ws` (ws_len bytes) sized
 * from srmech_spectral_spine_arena_bytes. Returns SRMECH_ERR_NULL_ARG for
 * a NULL required pointer, SRMECH_ERR_BAD_INPUT for an out-of-range edge
 * endpoint, SRMECH_ERR_OVERFLOW for a too-small arena or a non-convergent
 * eigensolve. */
srmech_status_t srmech_spectral_spine(
    uint32_t        n,
    uint32_t        n_edges,
    const uint32_t *edges_u,
    const uint32_t *edges_v,
    const double   *weights,
    uint32_t        k,
    uint32_t       *out_spine,
    uint32_t       *out_count,
    double         *ws,
    size_t          ws_len);

/* ------------------------------------------------------------------ *
 * EPH — the complex-time Wick-rotation propagator (0.9.0rc136; siona
 * gh#1274) — a Class-L COMPOSITE over the existing kernels
 * (srmech_hermitian_eigendecompose_ws + srmech_exp + srmech_cos +
 * srmech_sin), the C twin of srmech.math.laplacian.propagate.
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
 * EPH SPARSE — the sparse-scaled propagator (0.9.0rc206; siona
 * gh#1274 item 1c, the corpus-scale residual) — the SAME harvest
 * e^{-zL}·u0 as srmech_eph_propagate (same complex-z convention, same
 * arg(z) coherence dial, same seam-folded Wick factor) computed by a
 * CHEBYSHEV polynomial of the operator applied with MATRIX-VECTOR
 * PRODUCTS ONLY — no eigendecomposition, no dense e^{-zL} — so it runs
 * on a corpus-scale L past the n<=256 dense-eigensolve cap.
 *
 * The operator is the SIGNED graph Laplacian read off the edge list
 * (the signed_laplacian convention): (L v)[i] = deg[i]·v[i] −
 * Σ_{(i,j)} w_ij·v[j], deg[i] = Σ_incident |w| (Class-K sign branch,
 * never fabs; self-loops skipped; duplicate edges read PER-EDGE).
 * Spectral interval by Gershgorin ([0, 2·max deg] — deterministic, an
 * overestimate only widens the interval), affine-mapped to [-1, 1];
 * Chebyshev interpolation coefficients of e^{-z·lambda(s)} from the
 * Chebyshev nodes (srmech_exp + srmech_cos / srmech_sin per node — the
 * Q61 octant reduction IS the 2π seam-fold), node count adaptively
 * DOUBLED from 64 up to the HARD CAP max_degree+1, accepted when the
 * coefficient tail (top eighth) falls below tol·max|e^{-z·lambda}|;
 * then the forward T_{k+1} = 2·L~·T_k − T_{k-1} vector recurrence
 * (m matvecs, O(m·n_edges) time, O(n) memory). Not converged at the
 * cap → honest SRMECH_ERR_OVERFLOW (raise max_degree or shrink |z|).
 * Standalone-complete: all scratch is bump-carved from the CALLER
 * arena `ws` (no malloc). ABI-additive: new symbols, ABI stays 4.
 * ------------------------------------------------------------------ */

/* The caller arena size IN BYTES srmech_eph_propagate_sparse needs for
 * n nodes / n_edges edges / a max_degree cap: the signed degrees + three
 * interleaved-complex recurrence vectors (the harvest accumulates into
 * the caller's output buffer) + the Chebyshev node/coefficient staging
 * (5·(max_degree+1) doubles). Size `ws_len` >= this. */
size_t srmech_eph_propagate_sparse_arena_bytes(uint32_t n, uint32_t n_edges,
                                               uint32_t max_degree);

/* harvest = e^{-zL}·u0 on the SPARSE signed Laplacian of the edge list
 * (edges_u/edges_v parallel uint32 arrays; `weights` NULL → unit, may
 * be negative for a signed graph). `u0_interleaved` / `out_harvest_
 * interleaved` are each n INTERLEAVED-complex (re, im) pairs (a real
 * excitation rides as (re, 0)). z = z_re + i·z_im is the complex time
 * (the arg(z) coherence dial, as srmech_eph_propagate). `tol` (> 0) is
 * the RELATIVE coefficient-tail tolerance (relative to the max
 * propagator magnitude over the spectral interval); `max_degree`
 * (1..2^28) is the HARD Chebyshev degree cap. Writes the Chebyshev
 * degree actually used to *out_degree_used when non-NULL. n == 0
 * writes nothing. `ws` (ws_len bytes) sized from
 * srmech_eph_propagate_sparse_arena_bytes. Returns SRMECH_ERR_NULL_ARG
 * for a NULL required pointer, SRMECH_ERR_BAD_INPUT for an out-of-range
 * edge endpoint / non-finite weight / tol <= 0 / max_degree out of
 * range / a non-finite propagator value (exp overflow on a backward
 * z), SRMECH_ERR_OVERFLOW for a too-small arena or a coefficient tail
 * not below tol within the max_degree cap. */
srmech_status_t srmech_eph_propagate_sparse(
    uint32_t        n,
    uint32_t        n_edges,
    const uint32_t *edges_u,
    const uint32_t *edges_v,
    const double   *weights,
    const double   *u0_interleaved,
    double          z_re,
    double          z_im,
    double          tol,
    uint32_t        max_degree,
    double         *out_harvest_interleaved,
    uint32_t       *out_degree_used,
    double         *ws,
    size_t          ws_len);

/* ------------------------------------------------------------------ *
 * EPH WOUND — the wound propagator (0.9.0rc207; siona gh#1276) — the
 * SAME harvest e^{-zL}·u0 as srmech_eph_propagate with the 2π
 * seam-fold's DIVMOD QUOTIENT KEPT (the #741 mod-should-be-divmod
 * audit's first concrete instance). srmech_eph_propagate's per-mode
 * fold discards the whole-turn winding w_k of the oscillation
 * argument Im(z)·λ_k (the mod-collapse); this peer keeps the grading —
 * BOTH harvests at the seam: the EPICYCLE harvest (byte-identical to
 * srmech_eph_propagate — same statics, same order; carrying w does
 * not perturb it) PLUS the per-mode METACYCLE readout, wired in the
 * One's (σ, θ, w) crank vocabulary:
 *   w_k     = round(Im(z)·λ_k / 2π)  — the metacycle winding, the
 *             quotient of the SAME divmod the fold performs
 *             (srmech_winding_fold — no forked 2π constant);
 *   θ_k     = the folded epicycle residue, |θ| <= π,
 *             2π·w_k + θ_k == Im(z)·λ_k on the fold's grid (lossless —
 *             the One.unwrapped_phase reconstruction per mode);
 *   σ_eff_k = the tower-graded chirality dial via the winding's
 *             binary tower on the mode triad (w_k, 0, 0) — the
 *             EXISTING srmech_sigma_effective readout (NOT the
 *             melding bare `w mod 2`);
 *   spin_k  = the double-cover sign (-1)^{w_k} — the EXISTING
 *             srmech_spinor_sign readout.
 * Standalone-complete: all scratch is bump-carved from the CALLER
 * arena `ws` (no malloc). ABI-additive: new symbols, ABI stays 4.
 * ------------------------------------------------------------------ */

/* The caller arena size IN BYTES srmech_eph_propagate_wound needs for
 * an n*n L — the srmech_eph_propagate carve minus the eigvals row
 * (λ writes straight to the caller's out_eigvals). Size ws_len >= this. */
size_t srmech_eph_propagate_wound_arena_bytes(uint32_t n, int is_complex);

/* harvest = e^{-zL}·u0 with the per-mode winding KEPT. The first seven
 * parameters follow srmech_eph_propagate exactly (same conventions,
 * byte-identical harvest). The five readout arrays are each length n,
 * in the eigensolve's mode order: out_eigvals (λ_k), out_winding
 * (w_k, int64), out_theta (θ_k, |θ| <= π), out_sigma_effective /
 * out_spinor_sign (±1 each, int32). n == 0 writes nothing. `ws`
 * (ws_len bytes) sized from srmech_eph_propagate_wound_arena_bytes.
 * Returns SRMECH_ERR_NULL_ARG for a NULL required pointer,
 * SRMECH_ERR_OVERFLOW for a too-small arena / a non-convergent
 * eigensolve, SRMECH_ERR_BAD_INPUT if an oscillation argument
 * |Im(z)·λ_k| exceeds the fold's reduction bound (~2^55, the
 * srmech_cos domain). */
srmech_status_t srmech_eph_propagate_wound(
    uint32_t       n,
    int            is_complex,
    const double  *L,
    const double  *u0_interleaved,
    double         z_re,
    double         z_im,
    double        *out_harvest_interleaved,
    double        *out_eigvals,
    int64_t       *out_winding,
    double        *out_theta,
    int32_t       *out_sigma_effective,
    int32_t       *out_spinor_sign,
    double        *ws,
    size_t         ws_len);

/* ------------------------------------------------------------------ *
 * RESPONSION — the response-function family of a generator L acting
 * on an excitation u0 (0.9.0rc208; F1186 — the op(x)operand(x)responsion
 * k=3 completion: the stored relationship itself, the answering-
 * correspondence between successive op-on-operand applications). The
 * family has TWO canonical continuous-form members that are LAPLACE-
 * TRANSFORM DUALS of one another:
 *
 *   kind == 0 (PROPAGATOR, time domain):   e^{-zL}·u0
 *     — delegates to the shipped srmech_eph_propagate cascade (rc136;
 *       same complex-z convention, same arg(z) coherence dial, same
 *       mandatory 2-pi seam-fold).
 *   kind == 1 (RESOLVENT, frequency/energy domain, the Green's
 *              function): (zI - L)^{-1}·u0
 *     — the Laplace transform of the (semigroup) propagator:
 *       (zI - L)^{-1} = integral_0^inf e^{-zt}·e^{tL} dt for
 *       Re(z) > max Re(lambda(L)); per eigenmode the pair is
 *       e^{-z·lambda}  <->  1/(z - lambda). Realised as the REAL
 *       2n x 2n block embedding [[Ar, -Ai], [Ai, Ar]]·[u; v] =
 *       [br; bi] of the complex system A = zI - L over the shipped
 *       srmech_dense_solve_f64_ws Gauss-Jordan kernel (the SAME
 *       embedding the Python mat_solve complex path rides) — a
 *       composition of existing C, no forked solve.
 *
 * A singular A (z EXACTLY in the spectrum of L — a resolvent POLE)
 * returns SRMECH_ERR_BAD_INPUT (the honest pole signal, not a number).
 * Standalone-complete: all scratch is bump-carved from the CALLER
 * arena `ws` (no malloc). ABI-additive: new symbols, ABI stays 4.
 * ------------------------------------------------------------------ */

/* The caller arena size IN BYTES srmech_responsion needs for an n*n L
 * and the given kind: kind == 0 -> the srmech_eph_propagate carve
 * (identical, pass-through); kind == 1 -> the 2n x 2n real block
 * embedding + the stacked RHS/solution columns + the inner
 * srmech_dense_solve_arena_bytes(2n, 1) solve arena. Size ws_len >=
 * this. An unknown kind returns 0. */
size_t srmech_responsion_arena_bytes(uint32_t n, int is_complex, int kind);

/* response = R(z)·u0 for the selected kind (0 = propagator e^{-zL}·u0,
 * 1 = resolvent (zI - L)^{-1}·u0). is_complex == 0: `L` is n*n
 * row-major REAL symmetric; is_complex != 0: `L` is n*n row-major
 * INTERLEAVED-complex (re, im) Hermitian. `u0_interleaved` and
 * `out_response_interleaved` are each n INTERLEAVED-complex (re, im)
 * pairs (a real excitation rides as (re, 0)). z = z_re + i·z_im.
 * n == 0 writes nothing. `ws` (ws_len bytes) sized from
 * srmech_responsion_arena_bytes for the SAME kind. Returns
 * SRMECH_ERR_NULL_ARG for a NULL required pointer, SRMECH_ERR_BAD_INPUT
 * for an unknown kind or a resolvent pole (z in spec(L)) or a
 * propagator fold-domain overflow, SRMECH_ERR_OVERFLOW for a too-small
 * arena / a non-convergent eigensolve (propagator kind). */
srmech_status_t srmech_responsion(
    uint32_t       n,
    int            is_complex,
    int            kind,
    const double  *L,
    const double  *u0_interleaved,
    double         z_re,
    double         z_im,
    double        *out_response_interleaved,
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
 * entry lies in [0, p). Requires p a prime with 2 <= p < 2**31 (so a*b fits
 * uint64); returns SRMECH_ERR_BAD_INPUT otherwise. Writes the pivot column of
 * each pivot row into `out_pivots` (caller buffer of >= min(n_rows, n_cols)
 * uint32) and the rank into `*out_rank`. Primality of p is the caller's
 * contract (the arithmetic domain bound is the only thing guarded here).
 *
 * rc350 (task #T1003): the lower bound was 2 < p through rc349 because the rc44
 * kernel inverted a pivot by FERMAT (a**(p-2) mod p); rc49 replaced that with
 * the extended-Euclidean srmech_mod_inv and the bound was never revisited. Only
 * the CEILING was ever an arithmetic-domain fact. GF(2) is now in domain and
 * matches the Python peer exactly -- char 2 needs no division (1^-1 = 1) and the
 * row op is XOR. Signature UNCHANGED, so no ABI bump; this widens the accepted
 * input set only (every p that was accepted before is accepted now). */
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
 * Catalog REGISTRY / KERNEL-STATE / AUDIT logic (0.9.0rc172; the
 * ORCHESTRATION→C spine, batch 2). A bare-C host (no Python) runs the
 * catalog registry/kernel/audit surface with these peers, each COMPOSING
 * the existing kernels — the srmech_json parser / canonical writer /
 * builder + srmech_sha256_hex (Class A) — and NO new parser, NO new hash.
 * They back the Python ops
 *   srmech.amsc.catalog.list_registered_roots  -> srmech_catalog_registered_roots
 *   srmech.amsc.catalog.get_local_kernel_state  -> srmech_catalog_local_kernel_state
 *   srmech.amsc.catalog.use_local_kernel        -> srmech_catalog_use_local_kernel
 *     (clear_local_kernel dispatches through use_local_kernel(None))
 *   srmech.amsc.catalog.attestation_audit       -> srmech_catalog_attestation_audit
 *
 * STATE MODEL (option a — caller-owned): the registry / kernel state is
 * OWNED BY THE HOST and passed in per call (Python passes its module
 * globals; a bare-C host passes its own struct's contents). No global
 * mutable C state, no long-lived handle. All scratch is bump-carved from
 * the caller arena `ws` (size it with the matching *_arena_bytes). Each
 * peer writes canonical JSON (byte-identical to CPython json.dumps(obj,
 * sort_keys=True, ensure_ascii=False)) into `out` (NO trailing NUL) and
 * sets *out_len. Output is float-free by construction; a per-line NDJSON
 * parse failure returns non-OK so the Python caller runs the COMPLETE
 * pure path (value-parity, never a rescue). ABI-additive: new symbols,
 * so SRMECH_ABI_VERSION stays 3.
 * ------------------------------------------------------------------ */

/* list_registered_roots: [{"path":<root>,"source":<root_source>}, ...] with
 * the host's own attested root FIRST, then every external (path, source)
 * pair from `ext_json` (a JSON array of two-string [path, source] arrays). */
size_t srmech_catalog_registered_roots_arena_bytes(size_t root_len,
                                                   size_t source_len,
                                                   size_t ext_len);
srmech_status_t srmech_catalog_registered_roots(
    const char *root_path, size_t root_len,
    const char *root_source, size_t root_source_len,
    const char *ext_json, size_t ext_len,
    void *ws, size_t ws_len,
    char *out, size_t out_cap, size_t *out_len);

/* get_local_kernel_state: {ok, active, path, adapter_class, n_overlay_sources,
 * per_source, cache_hash} where cache_hash = sha256( "\n".join(
 * f"{source_key}\t{overlay_sha256}") ) over the caller-provided per_source
 * array (each entry an object with source_key/table/overlay_path/
 * overlay_sha256 string fields — the FS-derived overlay set). `path` /
 * `adapter_class` NULL -> JSON null. */
size_t srmech_catalog_local_kernel_state_arena_bytes(size_t path_len,
                                                     size_t ac_len,
                                                     size_t per_source_len);
srmech_status_t srmech_catalog_local_kernel_state(
    int active, const char *path, size_t path_len,
    const char *adapter_class, size_t ac_len,
    const char *per_source_json, size_t per_source_len,
    void *ws, size_t ws_len, char *out, size_t out_cap, size_t *out_len);

/* use_local_kernel / clear_local_kernel HAPPY-PATH response. `clear != 0`
 * -> the T2-cleared response; else the success response for a validated,
 * existing overlay dir (the caller does adapter_class validation + FS
 * existence/dir checks + the Python-repr error responses). `path` is the
 * resolved overlay path (success only); `adapter_class` NULL -> no scope. */
size_t srmech_catalog_use_local_kernel_arena_bytes(size_t path_len,
                                                   size_t ac_len);
srmech_status_t srmech_catalog_use_local_kernel(
    int clear, const char *path, size_t path_len,
    const char *adapter_class, size_t ac_len,
    void *ws, size_t ws_len, char *out, size_t out_cap, size_t *out_len);

/* attestation_audit: {ok, source_key, n_rows, rows:[...]}. Iterates the
 * NDJSON file bytes (lstrip each line; skip empty / '#' comment lines),
 * parses each row as JSON, and projects data_schema_id + the EIGHT
 * attestation fields {source_doi, source_url, license, response_sha256,
 * retrieved_at, parser_version, parser_rule_hash, collector_descriptor_hash}
 * (each "" when absent). A per-line parse failure returns non-OK -> the caller
 * runs the pure path.
 *
 * `#T1108` (ABI 13) — THE DESCRIPTOR PAIR IS NEW, and it is what makes the
 * answer honest rather than merely consistent. The projection above is only
 * legitimate when the committed line IS an MPR envelope. A data-only
 * `literature_curated` catalogue commits rows with no attestation key at all,
 * so through rc417 this op returned empty strings for every field of every row
 * of eight of the nine registered sources — and so did its Python peer, which
 * is why eleven releases of differential testing never saw it.
 *
 * With the descriptor in hand the op reads `[fetch].adapter` and DECIDES:
 *   - a verbatim adapter (live fetchers, `mpr_committed`)   -> project.
 *   - `literature_curated`                                  -> SRMECH_ERR_NOT_IMPL.
 * The decline is a NAMED CAPABILITY GAP, not a bug and not a fallback:
 * synthesising the curated block needs canonical-TOML `descriptor_hash` /
 * `parser_rule_hash` peers that the C surface does not export today, and
 * SRMECH_ERR_NOT_IMPL (never SRMECH_ERR_OVERFLOW) says so — no arena relieves
 * it. The Python host services the call completely; a bare-C host does not get
 * this one source class yet. Declining loudly is the only alternative to
 * answering wrongly, which is the state this replaces.
 *
 * A NULL / unparseable descriptor is SRMECH_ERR_BAD_INPUT rather than an
 * assumed-verbatim projection: guessing is how the blank answer happened. */
size_t srmech_catalog_attestation_audit_arena_bytes(size_t ndjson_len,
                                                    size_t descriptor_len,
                                                    size_t source_key_len);
srmech_status_t srmech_catalog_attestation_audit(
    const char *source_key, size_t source_key_len,
    const char *descriptor, size_t descriptor_len,
    const char *ndjson, size_t ndjson_len,
    void *ws, size_t ws_len, char *out, size_t out_cap, size_t *out_len);

/* ------------------------------------------------------------------ *
 * cascade.compose LINEAR CHAIN-RUNNER — PARSE + VALIDATE (0.9.0rc173; the
 * ORCHESTRATION→C spine, batch 3). A bare-C host parses + validates an
 * operator-chain descriptor's `[[catalog.operator_chain]]` blocks with
 * these peers, each COMPOSING the srmech_json parser / builder / canonical
 * writer — NO new parser, NO new math. They back the Python ops
 *   srmech.cascade.compose.parse_chain_spec     -> srmech_chain_spec_parse
 *   srmech.cascade.compose.parse_catalog_chains -> srmech_chain_catalog_parse
 *
 * SCOPE (honest split): PARSE + VALIDATE only. The RUN loop (resolve_chain /
 * run_chain) is NOT here — it dispatches ARBITRARY srmech ops (heterogeneous
 * kwargs signatures) over the LIVE Python object graph (importlib + getattr +
 * reference resolution against runtime step outputs) → it needs a bounded-op
 * FFI + a uniform value carrier, scoped rc174. (Confirmed rc173: run_chain
 * invokes ANY of the 14 class modules by name — sha256_bytes / mod_add /
 * pi_cascade_digits / *_series_truncate — NOT the bounded cascade atoms.)
 *
 * CONTRACT: input is JSON (the Python dict, json.dumps'd). On success each
 * peer writes the normalized spec(s) as canonical JSON (byte-identical to
 * json.dumps(obj, sort_keys=True, ensure_ascii=False); NO trailing NUL) into
 * `out` and sets *out_len. `args` are OMITTED — the Python caller re-attaches
 * them from the ORIGINAL dict so arg object identity/type is preserved. On
 * ANY validation failure or non-JSON input the peer returns non-OK so the
 * caller runs the COMPLETE pure path (the ChainSpecError message is raised
 * there). All scratch is caller-arena `ws` (size it with *_arena_bytes).
 * ABI-additive: new symbols, so SRMECH_ABI_VERSION stays 3.
 * ------------------------------------------------------------------ */

/* parse_chain_spec: validate one chain block (JSON object with name / summary
 * / returns / steps[{class,op,args,on_error?}] / on_error?) and emit the
 * normalized {name, on_error, returns, steps:[{class_id, on_error, op}],
 * summary}. Class ids A..N; on_error in {raise, warn_return_none, skip};
 * every @<row|input|step|catalog>.<path> reference is grammar-checked and
 * @step[N] is bounded to N < the step index. */
size_t srmech_chain_spec_parse_arena_bytes(size_t chain_len);
srmech_status_t srmech_chain_spec_parse(
    const char *chain_json, size_t chain_len,
    void *ws, size_t ws_len, char *out, size_t out_cap, size_t *out_len);

/* parse_catalog_chains: validate {chain_schema_version:1, operator_chain:[
 * chain, ...]} and emit [spec, ...]. chain_schema_version MUST be int 1;
 * each chain is validated as in srmech_chain_spec_parse. */
size_t srmech_chain_catalog_parse_arena_bytes(size_t cat_len);
srmech_status_t srmech_chain_catalog_parse(
    const char *cat_json, size_t cat_len,
    void *ws, size_t ws_len, char *out, size_t out_cap, size_t *out_len);

/* ------------------------------------------------------------------ *
 * cascade.compose LINEAR CHAIN-RUNNER — the RUN LOOP (0.9.0rc174; the
 * ORCHESTRATION→C spine, batch 4; srmech_compose_run.c).
 *
 * srmech_chain_run RUNS a validated `[[catalog.operator_chain]]` end-to-end in
 * C to BYTE-IDENTICAL OUTPUT, backing srmech.cascade.compose.run_chain /
 * resolve_chain (whose Python closure over the live object graph is NOT
 * mirrored — parity is on the final VALUE, not the closure).
 *
 *   chain_json : the FULL chain object {name,summary,returns,on_error?,steps:
 *                [{class,op,args,on_error?}]} (json.dumps of the ChainSpec).
 *   ctx_json   : {"row": <obj|null>, "inputs": <obj>} — the @row / @input
 *                binding tables (may be NULL / "" if the chain refs neither).
 *
 * Each step's args are resolved (@row.<path> / @input.<path> /
 * @step[N].output; @catalog is NOT supported here) and dispatched to a BOUNDED
 * Class-N op set — pi_cascade_digits, {exp,sin,cos,log1p,atan}_series_truncate,
 * rational_{add,mul,div,pow_uint} — over the EXISTING C kernels
 * (srmech_pi_archimedes / srmech_*_series_truncate_big / srmech_rational_pow_
 * uint_big + a bignum-ℚ add/mul/div composed from srmech_bigint). The final
 * value is marshaled back as a canonical-JSON VALUE DESCRIPTOR
 * ({"k":"s","v":"3.14"} | {"k":"q","n":"..","d":".."} | {"k":"i","v":".."} |
 * {"k":"n"}; bignums as decimal strings) which the Python caller reconstructs.
 *
 * rc103 inform-don't-limit: ANY op outside the table, any @catalog ref, any
 * non-"raise" error policy, any float / unsupported arg, or any domain error /
 * overflow → non-OK, and the Python caller runs the COMPLETE pure path (never a
 * wrong answer; the pure path raises the exact ChainSpecError / ValueError).
 * ONE caller arena `ws`, bump-allocated forward (size it with
 * srmech_chain_run_arena_bytes); ABI-additive → SRMECH_ABI_VERSION stays 3. */
size_t srmech_chain_run_arena_bytes(size_t chain_len, size_t ctx_len);
srmech_status_t srmech_chain_run(
    const char *chain_json, size_t chain_len,
    const char *ctx_json, size_t ctx_len,
    void *ws, size_t ws_len, char *out, size_t out_cap, size_t *out_len);

/* ------------------------------------------------------------------ *
 * amsc.catalog CHAIN ORCHESTRATION — list + run a catalog's named chains
 * (0.9.0rc175; the ORCHESTRATION→C spine, batch 5). These COMPOSE the rc173
 * chain parse (srmech_compose.c) + the rc174 chain-runner (srmech_compose_run.c)
 * — NO new parser, NO new math. They back the Python ops
 *   srmech.amsc.catalog.list_catalog_chains -> srmech_catalog_list_chains
 *   srmech.amsc.catalog.run_catalog_chain   -> srmech_catalog_run_chain
 *
 * CONTRACT: input is JSON (the Python descriptor's [catalog] table, json.dumps'd
 * as {chain_schema_version:1, operator_chain:[chain, ...]}). Any validation
 * failure / unknown chain name / non-JSON input / out-of-table op → non-OK so
 * the Python caller runs the COMPLETE pure path. Caller-arena `ws` (size with
 * the matching *_arena_bytes). ABI-additive → SRMECH_ABI_VERSION stays 3.
 *
 * srmech_catalog_list_chains: emit the chain-summary array
 *   [{classes:[class_id,...], n_steps, name, on_error, returns, summary}, ...]
 * (canonical JSON, byte-identical to CPython
 * json.dumps(obj, sort_keys=True, ensure_ascii=False) — the exact kwarg
 * combination srmech_json_write_ws implements; this line omitted
 * ensure_ascii until rc403); each chain is validated as in
 * srmech_chain_spec_parse. */
size_t srmech_catalog_list_chains_arena_bytes(size_t cat_len);
srmech_status_t srmech_catalog_list_chains(
    const char *cat_json, size_t cat_len,
    void *ws, size_t ws_len, char *out, size_t out_cap, size_t *out_len);

/* srmech_catalog_run_chain: find the chain named [chain_name, name_len) in
 * operator_chain and RUN it end-to-end (same bounded Class-N op set + value-
 * descriptor OUTPUT contract as srmech_chain_run). ctx_json = {"row":.., "inputs"
 * :..}. A chain not found / a non-table op / a non-i64 input / overflow → non-OK
 * → the Python pure path (the not-found KeyError / the live-object-graph run). */
size_t srmech_catalog_run_chain_arena_bytes(size_t cat_len, size_t ctx_len);
srmech_status_t srmech_catalog_run_chain(
    const char *cat_json, size_t cat_len,
    const char *chain_name, size_t name_len,
    const char *ctx_json, size_t ctx_len,
    void *ws, size_t ws_len, char *out, size_t out_cap, size_t *out_len);

/* ------------------------------------------------------------------ *
 * srmech.dsl Chain LINEAR RUN-LOOP — the F1 carrier-FFI FOUNDATION (0.9.0rc181;
 * ANNEX Batch B pt1; srmech_dsl_chain_run.c). The C peer of srmech.dsl.Chain.run
 * — a SIBLING interpreter to srmech_chain_run: it VALUE-THREADS (each stage's
 * output feeds the next stage's input, NO @row/@input/@step refs) over the LEAN
 * cascade ATOMS on f64/i64 carriers. Backs the DSL rows lookup_cascade_op (the
 * leaf-dispatch table) + build_chain_from_dict (the stage-IR discriminator parse).
 *
 *   chain_json  : {"chain":{"name":..},"stage":[{"op":..,<kwargs>..},...]} — the
 *                 build_chain_from_dict grammar. Only `op` (LINEAR) stages run
 *                 here; a loop/fold/reduce/parallel discriminator → non-OK → the
 *                 pure path (rc182 adds the combinators + the TOML front-ends).
 *   input_json  : an F1 VALUE DESCRIPTOR for the seed value.
 *   out         : the F1 VALUE DESCRIPTOR for the final value.
 *
 * THE F1 CARRIER (the shared carrier-FFI bedrock #796's F2/F3/F4 extend). Tagged
 * union {NONE, INT (i64), FLOAT (f64), STR, LIST}; LIST carries an is_tuple bit
 * (Python list vs tuple) + BOUNDED-depth children (JPL Rule 1 — the nesting
 * recursion is depth-guarded + asserted, never unbounded). Marshalled as:
 *   {"k":"n"} | {"k":"i","v":<int>} | {"k":"f","v":<num>} | {"k":"s","v":<str>} |
 *   {"k":"l","v":[..]} (list) | {"k":"t","v":[..]} (tuple). FLOAT is emitted by
 *   srmech_json_write_ws, so as of rc403 (`#T1071`) the numeric atoms are
 *   BYTE-IDENTICAL to repr(float), not merely within-tolerance. This line read
 *   "round-trips at %.17g -> WITHIN-TOL, not byte-identical" until then.
 *
 * THE LEAF-DISPATCH TABLE: magnitude / reorient / pin_slot_at_zero /
 * best_rational_signed / chiral_flip / net_chirality / autocorrelation — the
 * C-backed unary value→value atoms. Any other unary op (chiral_dual;
 * kuramoto_step / quaternion_dft / octonion_dft — heavier multi-array carriers)
 * → non-OK → the COMPLETE pure path (rc103 inform-don't-limit; never a wrong
 * answer). ONE caller arena `ws` (size with srmech_dsl_chain_run_arena_bytes).
 *
 * THE COMBINATORS (0.9.0rc182; ANNEX Batch B pt2 — completes the interpreter).
 * The build_chain_from_dict discriminator grammar now RUNS in C:
 *   * loop   {"loop_n":N,"sub_chain":[stage,..]} — value-thread the sub-chain
 *            N times (recurse into the stage-runner; N + nesting depth BOUNDED
 *            + asserted, JPL Rule 1/2 — a too-large N or too-deep nesting → pure).
 *   * fold   {"fold_init":<scalar>,"fold_op":<op>} — acc = fold_init; for each
 *            element of the input LIST, acc = fold_op(acc, elem) (a C-backed
 *            BINARY op: cyclic_gcd). Empty list → acc = fold_init.
 *   * reduce {"reduce_op":<op>} — acc = list[0]; fold the BINARY op over the
 *            remaining elements. Empty list → non-OK (pure raises ValueError).
 *   * map_indexed {"map_op":<op>} (0.9.0rc420, the SIXTH combinator — the
 *            general indexed map, the dominant missing recursion scheme the
 *            census under local task `#T1114` measured) — out[k] =
 *            body(input, k) for k in 0..len(input)-1, n FIXED AT ENTRY
 *            (data-SIZED, never data-DEPENDENT; the same totality class as
 *            fold). C map-body table: seq_get (data-first identity access);
 *            any other body → non-OK → pure. Widened CONSCIOUSLY with the
 *            Python dispatcher + tests/test_combinator_kernel_closure.py in
 *            the same change (the closure ratchet now cross-reads this
 *            file's discriminator array, so the two sides cannot drift).
 * `parallel_body` (the Klein-4 fan-out over host threads) still DEFERS to pure.
 * A combinator whose body op is not a C leaf / binary kernel → non-OK → pure.
 * ABI-additive → SRMECH_ABI_VERSION stays 4 (and the rc420 map form adds no
 * symbol, changes no signature and adds no callback typedef → ABI unchanged). */
size_t srmech_dsl_chain_run_arena_bytes(size_t chain_len, size_t input_len);
srmech_status_t srmech_dsl_chain_run(
    const char *chain_json, size_t chain_len,
    const char *input_json, size_t input_len,
    void *ws, size_t ws_len, char *out, size_t out_cap, size_t *out_len);

/* srmech_dsl_toml_chain_to_json — the TOML front-end bridge (0.9.0rc182). Parse
 * a TOML chain-spec document via srmech_toml_parse, then serialise the parsed
 * table tree as canonical JSON (byte-identical to CPython
 * json.dumps(obj, sort_keys=True, ensure_ascii=False) — this line omitted both
 * `obj` and ensure_ascii until rc403. DOUBLE values are byte-identical too as of
 * rc403; the old "%.17g, WITHIN-TOL" caveat is retired, and a non-finite double
 * now DECLINES rather than emitting an unparseable token). The output is the
 * build_chain_from_dict IR
 * the Python `build_chain_from_toml_str` feeds straight into the chain builder —
 * so a C-only / MCU host reads a `[chain]` + `[[stage]]` TOML descriptor with no
 * Python TOML hop. A syntax error / unsupported construct / arena overflow →
 * non-OK, and the Python caller falls back to the stdlib tomllib parse (rc103
 * inform-don't-limit — same value, same error). ONE caller arena `ws` (size with
 * srmech_dsl_toml_chain_to_json_arena_bytes). ABI-additive → stays 4. */
size_t srmech_dsl_toml_chain_to_json_arena_bytes(size_t toml_len);
srmech_status_t srmech_dsl_toml_chain_to_json(
    const char *toml_src, size_t toml_len,
    void *ws, size_t ws_len, char *out, size_t out_cap, size_t *out_len);

/* ------------------------------------------------------------------ *
 * srmech_infer — the F929 OPEN/infer ROUTER (0.9.0rc176; the ORCHESTRATION->C
 * spine, batch 6; the CARRIER-FFI foundation). The C peer of
 * srmech.math.dispatch.infer — the META-dispatcher over srmech's shipped
 * closed-form reduction-theory rows. Given a STORED RELATIONSHIP marshalled as
 * JSON, DETECT which row its operand structure matches, DISPATCH the matching C
 * reducer, VERIFY the reducer's OWN contract, and emit the DECISION as a small
 * JSON descriptor the Python caller reconstructs (the closed_form OBJECT is
 * rebuilt from the SAME reducer this op verified, so native == the pure infer).
 *
 * rc176 handles the two EXACT-SYMBOLIC bignum-carrier rows that share ONE
 * carrier-FFI marshal (JSON with bignum-decimal-string coefficients):
 *   * cyclic       (sigma / theta_num / theta_den)      -> srmech_the_one; the
 *                  n1_is_sigma_only invariant (flat[1] == (sigma, 1)) is the
 *                  reducer's own verification.
 *   * sigma-gosper (term_ratio_num / term_ratio_den as ascending [num, den]
 *                  rational coefficient lists) -> srmech_gosper; has == 1 is the
 *                  verification (a hypergeometric antidifference exists).
 *
 * rc192 (#796 payoff) ADDS the SIGMA-DEFINITE (wz_certificate) exact-Q row over
 * the rc191 srmech_carrier_read_bipoly reader:
 *   * sigma-wz      (rn_num / rn_den / rk_num / rk_den as the four (n,k) BiPoly
 *                  term-ratios) -> FIND srmech_zeilberger @order-1 (accept only
 *                  the WZ shape a0(n)+a1(n)=0, nonzero constants) + PROVE
 *                  srmech_wz_verify on the 1/a1-rescaled certificate; reducible
 *                  iff the WZ equation VERIFIES (the genuine identity proof — not
 *                  the FIND alone). The reducer name is "wz_certificate".
 *
 * Output JSON (Python json.loads-able):
 *   reducible: {"reducer":"the_one"|"gosper"|"wz_certificate"|
 *               "apagodu_zeilberger"|"q_wz_certificate"|"q_gosper"|
 *               "elliptic_wz_certificate","reducible":true,
 *               "row":..,"verified":true}
 *   open     : {"reducible":false,"row":"cyclic"|"sigma"|"sigma_q"}   (Python
 *               builds the candidate-next-theory hint from the row; the rows
 *               whose C reducer declines non-definitively NEVER emit false —
 *               they return non-OK so the pure infer decides)
 *
 * rc223 (#796) ADDS the three remaining EXACT-Q rows over the rc223 public
 * carrier readers (srmech_carrier_read_{tripoly,qbipoly,ellratio}):
 *   * sigma_multivar (rn_* / rj_* / rk_* as the six (n,j,k) TriPoly term-
 *                  ratios) -> srmech_apagodu_zeilberger @max_order=1; a has=1
 *                  minimal-order recurrence IS the verification (the same
 *                  non-None-is-the-proof contract as gosper). A has=0 is NOT
 *                  definitive (the C peer declines above order 1) -> non-OK ->
 *                  the pure path decides. Reducer name "apagodu_zeilberger".
 *   * sigma_q      DEFINITE (qrn_* / qrk_* as the four (X,Y)=(q^n,q^k) QBiPoly
 *                  q-term-ratios) -> FIND srmech_q_zeilberger @order-1 (accept
 *                  only the q-WZ shape a0+a1=0, nonzero rational scalars) +
 *                  PROVE srmech_q_wz_verify on the 1/a1-rescaled certificate
 *                  (the COMPLETE degree-bounded q-WZ-equation check). Reducer
 *                  name "q_wz_certificate". A FIND decline (the C q-Zeilberger
 *                  completes only the k-free q-geometric class) -> non-OK ->
 *                  pure; a FIND success whose shape/verify fails -> reducible:
 *                  false (definitive: the k-free class is byte-identical to
 *                  the pure FIND, and the verify is a complete mirror).
 *                  INDEFINITE (q_term_ratio_* as a single-Y-cell QBiPoly wire
 *                  of the QPoly q-term-ratio) -> srmech_q_gosper; has == 1 is
 *                  the verification. Reducer name "q_gosper". A has=0 is NOT
 *                  definitive (constant-ratio native scope) -> non-OK -> pure.
 *   * sigma_elliptic (elliptic_term_ratio as the PRE-INTERNED EllRatio wire
 *                  object) -> srmech_elliptic_wz_certificate; has == 1 (the
 *                  8w7 recognized AND the connection-coefficient certificate
 *                  decides exactly zero) is the verification. Reducer name
 *                  "elliptic_wz_certificate". A has=0 -> non-OK -> pure (the
 *                  conservative fall; never a possibly-divergent false).
 *
 * rc224 (#796 CLOSE — the LAST row) ADDS the SPECTRAL row with the EXACT
 * operator-level verdict:
 *   * spectral     (matrix {"n","bits"} / adjacency {"n","bits"} / edges
 *                  [[u,v]...] + n + optional weights) — every f64 leaf rides
 *                  the wire as its IEEE-754 BIT PATTERN (a signed int64; the
 *                  bit-EXACT float wire — no decimal float parse in the
 *                  decision path). Build L in C (edges -> the Class-L
 *                  srmech_graph_dense_laplacian kernel, the SAME builder the
 *                  pure path dispatches to; matrix -> the raw grid;
 *                  adjacency -> the in-place D-A transform in the pure
 *                  _build_laplacian's exact float-op order) and decide:
 *                  reducible iff L is BIT-EXACT real-symmetric (IEEE == over
 *                  all mirrored pairs — the spectral theorem's own
 *                  hypothesis). NO eigensolve, NO resonant_spectrum, NO float
 *                  tolerance in the C decision path; the eigenvalue payload
 *                  is the OPERAND, re-derived pure-side on a reducible
 *                  verdict. Reducer name "resonant_spectrum". BOTH verdicts
 *                  are definitive here (the C-built L is entry-for-entry the
 *                  pure build), so the native and pure decisions are
 *                  identical on EVERY platform by construction.
 *
 * rc103 inform-don't-limit: any OTHER row (the elliptic multivariate Cn
 * Jackson row — whose verify is carrier-symbolic), any
 * malformed operand, or any arena overflow -> non-OK, and the Python caller
 * runs the COMPLETE pure infer (NEVER a false reducible; the honest OPEN
 * residue is the no-hallucination discipline in C). ONE caller arena `ws`. The
 * cyclic / gosper rows size with srmech_infer_arena_bytes(rel_len, max_terms)
 * (max_terms = the largest operand's coefficient count — the gosper degree, 1
 * for cyclic — since the gosper ws grows super-linearly in the degree, not in
 * rel_len). The sigma-wz row sizes with
 * srmech_infer_sigma_definite_arena_bytes; the rc223 rows each size with their
 * OWN sizer below (max_terms = the row's shape envelope: the TriPoly
 * jdeg/kdeg/nlen max; the QBiPoly ycells/xcells/qlen max; the EllRatio
 * n_syms + monomial count. coeff_limbs = the max significant 32-bit limbs per
 * coefficient) so the cheap rows never pay the MB floor. The rc224 spectral
 * row sizes with srmech_infer_spectral_arena_bytes(rel_len, n) (n = the
 * Laplacian dimension; parse + ONE n*n double grid + the edge arrays — no
 * eigensolve scratch). All are ABI-additive -> SRMECH_ABI_VERSION stays 4. */
size_t srmech_infer_arena_bytes(size_t rel_len, size_t max_terms);
size_t srmech_infer_sigma_definite_arena_bytes(size_t rel_len, size_t max_terms,
                                               size_t coeff_limbs);
size_t srmech_infer_sigma_multivar_arena_bytes(size_t rel_len, size_t max_terms,
                                               size_t coeff_limbs);
size_t srmech_infer_sigma_q_arena_bytes(size_t rel_len, size_t max_terms,
                                        size_t coeff_limbs);
size_t srmech_infer_sigma_elliptic_arena_bytes(size_t rel_len, size_t max_terms,
                                               size_t coeff_limbs);
size_t srmech_infer_spectral_arena_bytes(size_t rel_len, size_t n);
srmech_status_t srmech_infer(const char *rel_json, size_t rel_len,
                             void *ws, size_t ws_len,
                             char *out, size_t out_cap, size_t *out_len);

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

/* best_rational's Stern-Brocot / continued-fraction path made explicit
 * (rc336). Identical bounded convergent walk to srmech_best_rational, but
 * ALSO emits the partial quotients a_0, a_1, ... of the ACCEPTED convergents
 * into caller-allocated `terms` (the compact CF = the run-length encoding of
 * the Stern-Brocot L/R mediant path = the Class-N approximation holonomy).
 * *out_p / *out_q are the landing convergent, byte-identical to
 * srmech_best_rational. Bounded by SRMECH_RATIONAL_EUCLID_CAP.
 * Returns SRMECH_ERR_BAD_INPUT for denominator == 0 or max_denominator == 0;
 * SRMECH_ERR_NULL_ARG for a null out-param / terms; SRMECH_ERR_OVERFLOW if
 * max_terms is exceeded. */
srmech_status_t srmech_best_rational_path(uint64_t  numerator,
                                          uint64_t  denominator,
                                          uint64_t  max_denominator,
                                          uint64_t *terms,
                                          uint32_t  max_terms,
                                          uint32_t *out_count,
                                          uint64_t *out_p,
                                          uint64_t *out_q);

/* Class N rc8: exp Taylor partial sum as exact rational.
 *
 * Computes S_N(p/q) = sum_{k=0..N} (p/q)^k / k! and returns the result
 * reduced to lowest terms in (*out_num, *out_den). Pure integer
 * arithmetic; bounded num_terms ≤ 20 to keep N! within u64 (Python
 * fallback srmech.math.rational.exp_series_truncate handles larger N
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
 * range. Python wrappers (srmech.math.rational.rational_{add,mul,pow_uint})
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
 * srmech.math.rational.continued_fraction_convergents falls back to
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

/* ------------------------------------------------------------------ *
 * §102 / F1259 / F1260 (v0.9.0rc290): the Klein-4 mint SPLIT BY REGIME.
 *
 * Until rc290 one symbol — srmech_klein4_random — served every
 * deterministic Klein-4 mint, and the four regimes it was asked to cover
 * have DIFFERENT CORRECTNESS CRITERIA:
 *
 *   EXPAND     srmech_klein4_expand(key, …)     reproducibility
 *   ADDRESSED  srmech_klein4_address(content,…) identity + structurelessness
 *   ROLE       (compose _expand over a token hash) near-orthogonality
 *   STOCHASTIC (host entropy; no C peer — see below) non-reproducibility
 *
 * A caller who cannot see which regime a call is in cannot see that a
 * magic-number seed (DRAWN, an undeclared ensemble) is not a content
 * address (DERIVED). Separate symbols make the wrong choice hard to
 * WRITE rather than merely explicit.
 *
 * NOTE ON THE STOCHASTIC REGIME: it has no C peer, and that is a
 * REGIME property, not an ADR-0009 parity gap. Two implementations of
 * "unpredictable" cannot be differentially tested for byte-identity, and
 * a C host needing an unpredictable Klein-4 vector draws from its own
 * entropy source. The CAPABILITY every cascade actually consumes —
 * DETERMINISTIC Klein-4 minting — is fully covered in both projections.
 * ------------------------------------------------------------------ */

/* klein4_expand(key, key_length, D): D draws of CPython random.Random(seed)
 * .randrange(4), BYTE-IDENTICAL. `key` is the seed's little-endian uint32 words
 * (the Python wrapper splits the seed int; a C-only / MCU host passes its own
 * entropy words). Fills `out` with D codes in {0,1,2,3} via MT19937 +
 * getrandbits(3) rejection. Standalone-complete: the 624-word state is
 * stack-resident — no malloc, no compiled-in cap (bound is the caller's `out`).
 *
 * rc290 RENAME of srmech_klein4_random. The stream is unchanged byte-for-byte;
 * the NAME was the defect — the op is deterministic, so a C host reading
 * "random" got the sharper form of the lie the Python name told. The REMOVAL
 * of srmech_klein4_random is what bumps SRMECH_ABI_VERSION 7 -> 8. */
srmech_status_t srmech_klein4_expand(const uint32_t *key,
                                     size_t          key_length,
                                     uint32_t        D,
                                     uint8_t        *out);

/* klein4_address(content, content_len, D): the ADDRESSED regime — the Class-A
 * content address of `content` as D Klein-4 codes. Counter-mode SHA-256:
 * sha256(content || '|' || decimal(i)) for i = 0, 1, 2, …, each digest byte
 * contributing four crumbs (bit-pairs, LSB-first) until D symbols are filled.
 * `content` may be NULL iff content_len == 0 (the empty address is defined).
 *
 * CORRECTNESS CRITERION: identity + structurelessness. Equal content -> equal
 * vector; unequal content -> vectors at the 0.25 Klein-4 orthogonality floor
 * with no residual similarity. The output is SUPPOSED to be incompressible and
 * SUPPOSED to sit at the floor; that is the target, not a defect.
 *
 * NEVER use it to represent content you intend to COMPARE. SHA-256 avalanche
 * flips ~48.8 % of output bits per one-character edit, so at D=8192 "cat" vs
 * "cats" scores 0.2589 against a 0.2454 "cat"/"dog" control — the edit is invisible.
 * srmech_klein4_compose (the byte/glyph encoder) scores 0.6597 on the same pair
 * because it composes position-bound per-byte vectors. High diffusion is
 * exactly what makes a good ADDRESS and exactly what disqualifies it as a
 * REPRESENTATION (F1260): one property, two opposite requirements.
 *
 * Standalone-complete: no malloc, no compiled-in cap (bound is `out`).
 * Additive symbol. */
srmech_status_t srmech_klein4_address(const uint8_t *content,
                                      size_t         content_len,
                                      uint32_t       D,
                                      uint8_t       *out);

/* klein4_role(role, role_len, base, D): the ROLE regime — the binding key for a
 * NAMED SLOT (the role half of a role-filler bind). `role` is the slot name's
 * UTF-8 bytes, folded to a 32-bit seed by FNV-1a (offset basis 0x811C9DC5,
 * prime 0x01000193) XOR `base`, then expanded via srmech_klein4_expand. Bit-
 * exact with the Python _cooc_token_seed, which is the SAME derivation the
 * co-occurrence fold and the HRR role/value codebook already use.
 *
 * CORRECTNESS CRITERION: near-orthogonality between DISTINCT roles. Two
 * different names must land at the 0.25 Klein-4 floor so that binding by one
 * role cannot be read out by another. Unlike the ADDRESSED regime, near-
 * orthogonality here is not merely acceptable — it IS the whole functional
 * requirement, because it is what stops slots leaking into each other.
 *
 * Use it when the vector names a POSITION IN A STRUCTURE (a field name, a slot
 * label, a co-occurrence role) rather than a piece of data. It is NOT a content
 * address: `base` deliberately re-namespaces the same role name to a different
 * vector, which is correct for a codebook and wrong for an identity.
 * Additive symbol. */
srmech_status_t srmech_klein4_role(const uint8_t *role,
                                   size_t         role_len,
                                   uint32_t       base,
                                   uint32_t       D,
                                   uint8_t       *out);

/* klein4_sector_frame(D): the substrate's own period-14 (1,3,7,3) Klein-4
 * position structure. out[j] is the Class-C sector flip of the Cayley-Dickson
 * block that slot (j mod 14) belongs to: C -> i*omega7 (1), H -> gamma5 (2),
 * O -> CPT (3). Blocks tile as C = 2 slots, H = 4, O = 8.
 *
 * The partition enters as a MASK because it is not vector structure: the One's
 * 14-D adjoint carries only TWO independent transcendental values plus a sign
 * (ten slots theta-constant; slots 3 and 7 both cos, 4 and 12 both +/-sin), so
 * (1,3,7,3) is OPERATOR structure — how G(sigma,theta) ACTS — while any
 * projection target is an operand. As a period-14 mask it is well-defined at
 * EVERY D, which is why nothing here needs D divisible by 14 (and measurement
 * across 56/64, 112/128, 224/256, 448/512, 896/1024 found no gain from it).
 *
 * HONEST DISCLOSURE: the frame is STATISTICALLY INERT. XOR-by-constant is a
 * Hamming isometry, so masking changes no pairwise statistic at all. It is
 * carried for structural legibility and attestation, and it gives a falsifiable
 * invariant: XOR the frame back off and the raw Class-A expansion reappears.
 * Additive symbol. */
srmech_status_t srmech_klein4_sector_frame(uint32_t D, uint8_t *out);

/* klein4_from_one(sigma, theta_num, theta_den, terms, D): ONE-A14 — the One's
 * Klein-4 COUPLING projection. Builds the One's canonical serialisation
 * {"sigma":S,"terms":T,"theta":[N,D]} (sorted keys, no whitespace — byte-
 * identical to the Python json.dumps of One._to_jsonable()), takes its
 * klein4_address, and XORs the klein4_sector_frame. Derivable from the three
 * constructor integers alone: no stored bytes, no seed table, no label.
 *
 * WHAT THIS IS FOR: it is a ROLE, not a representation. The genome's coupling
 * slot is consumed by quad_turn, which applies it as a uniform klein4_bind —
 * and XOR-by-constant is a Hamming isometry, so sim(t1^c, t2^c) == sim(t1, t2)
 * for ANY coupling c. A coupling therefore MATHEMATICALLY CANNOT transmit
 * structure into stored content. The 0.25 floor and incompressibility are the
 * CORRECT targets; a "structure-preserving" coupling is a LEAK (the naive slot
 * projection scores 0.82 mutual similarity and reads one genome with another's
 * key at 64/64). Do not "improve" this toward structure-bearing.
 *
 * WHAT IT BUYS IS PROVENANCE, NOT STATISTICS. At D=64 over 120 distinct theta
 * (7140 pairs): mean pairwise similarity 0.2501, ZERO identical pairs —
 * statistically indistinguishable from the magic-integer draw it replaces
 * (0.2498) and from the design-note prototype (0.2491). The gain is a DECLARED FUNCTION of substrate parameters replacing
 * an undeclared draw. It is not a quality improvement and is not offered as one.
 *
 * The int64 parameters are the wire; the Python shim declines to the pure path
 * rather than truncate an arbitrary-precision theta. Standalone-complete: no
 * malloc, no compiled-in cap (bound is `out`). Additive symbol. */
srmech_status_t srmech_klein4_from_one(int64_t   sigma,
                                       int64_t   theta_num,
                                       int64_t   theta_den,
                                       int64_t   terms,
                                       uint32_t  D,
                                       uint8_t  *out);

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

/* klein4_bundle_sector_scores(acc, out, dim) (§102 / F1265; rc295): the
 * NON-COLLAPSING read of the same (1 + 2*dim) accumulator _resolve collapses.
 * _resolve emits ONE symbol per coordinate and throws the margins away; this
 * emits ALL FOUR sector scores per coordinate, so a caller RANKS instead of
 * matching. out is 4*dim uint64, row-major: out[4*i + s] is coordinate i's
 * score for sector s, s in {0,1,2,3} with bit0 = s & 1 and bit1 = (s >> 1) & 1.
 *
 * The score is the agreement PRODUCT a0(s) * a1(s), where a0 = c0 if bit0 else
 * n - c0 and a1 = c1 if bit1 else n - c1 — i.e. n^2 * P(sector s) under
 * per-coordinate bit independence, which is the maximum-likelihood estimate of
 * the joint cell the marginals can support. Ranking is invariant to the
 * 1/n^2, so the estimate is kept in EXACT INTEGERS and never divided.
 *
 * uint64 out (not uint32) is load-bearing: a0 * a1 reaches n^2, which overflows
 * uint32 at n > 65535 folded vectors, and the accumulator itself has no such
 * cap. A malformed accumulator (a bit count exceeding n) -> SRMECH_ERR_BAD_INPUT
 * rather than a silent wrap. Additive symbol — no ABI bump. */
srmech_status_t srmech_klein4_bundle_sector_scores(const uint32_t *acc,
                                                   uint64_t       *out,
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

/* Bio-TOTP ENCRYPTED server (rc179; ANNEX Batch A part 2). Same as
 * srmech_bus_serve but every request/response payload is wrapped in the
 * rc178 UTLP Bio-TOTP wire cipher (DEFAULT stdlib HMAC-SHA-256 counter-mode
 * path — the AES-128-CTR `[crypto]` extra stays Python). So a bare-C host
 * speaks the ENCRYPTED wire, not plaintext. Wire body = [nonce:16][ciphertext],
 * TLV-framed; key rolls on the PAL wall clock over `window_ns` (a large
 * window pins one key). `dna` (dna_len bytes, capped at 256; NULL iff
 * dna_len == 0) is the shared secret; `sender_id`/`channel_id` seed the
 * server's response nonces (each accepted connection gets a fresh packet_seq).
 * ENCRYPT composes srmech_bio_totp_derive_key + _keystream_xor; DECRYPT
 * composes srmech_bio_totp_decode_splice (permissive binding over the OPAQUE
 * payload). Additive symbol → SRMECH_ABI_VERSION stays 3.
 *
 * Error returns: as srmech_bus_serve, plus SRMECH_ERR_BAD_INPUT (window_ns
 * <= 0) / SRMECH_ERR_OVERFLOW (dna_len > 256) / SRMECH_ERR_IO (no wall
 * clock). */
srmech_status_t srmech_bus_serve_encrypted(
    const char                       *name,
    srmech_bus_handler_callback_t     handler,
    void                             *user_data,
    const uint8_t                    *dna,
    size_t                            dna_len,
    uint64_t                          sender_id,
    uint32_t                          channel_id,
    int64_t                           window_ns,
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

/* Bio-TOTP ENCRYPTED client (rc179). Same as srmech_bus_connect but the
 * returned handle encrypts on srmech_bus_send_recv and decrypts the reply
 * (see srmech_bus_serve_encrypted). `dna` + `window_ns` must match the
 * server's; `sender_id`/`channel_id` seed this client's request nonces.
 * srmech_bus_send_recv / srmech_bus_client_close are shared (they read the
 * cipher state from the handle). Additive symbol → SRMECH_ABI_VERSION stays 3.
 *
 * Error returns: as srmech_bus_connect, plus SRMECH_ERR_BAD_INPUT (window_ns
 * <= 0) / SRMECH_ERR_OVERFLOW (dna_len > 256). */
srmech_status_t srmech_bus_connect_encrypted(
    const char                       *name,
    const uint8_t                    *dna,
    size_t                            dna_len,
    uint64_t                          sender_id,
    uint32_t                          channel_id,
    int64_t                           window_ns,
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

/* ------------------------------------------------------------------ *
 * srmech.bus — pub/sub broadcast fan-out C peer (0.9.0rc180; ANNEX
 * Batch A part 2b — BUS FULLY C). The last owed bus row (`pipe`) → C.
 *
 * Model (mirrors srmech.bus._server.Endpoint.broadcast + _client.Channel.
 * subscribe + _pipe.pipe): a server handle (from srmech_bus_serve /
 * _serve_encrypted — the SAME handle; every server now carries a ready PAL
 * mutex + an empty subscriber registry) can act as a publisher. Every
 * connection accepted via srmech_bus_pubsub_accept is REGISTERED as a
 * subscriber in a BOUNDED registry (≤ SRMECH_BUS_MAX_SUBSCRIBERS), guarded
 * by the PAL mutex. srmech_bus_broadcast fans one frame out to every active
 * subscriber under the lock (serialised → per-subscriber frame order is
 * preserved). On the encrypted path each subscriber has its OWN send cipher
 * (independent packet_seq — mirrors the Python per-subscriber send_bio). A
 * failed write DROPS that subscriber (peer closed = unsubscribe). The OS
 * socket send buffer IS the bounded per-subscriber queue (no heap growth).
 *
 * Concurrency: srmech_bus_pubsub_accept (spin one per thread, JOIN before
 * srmech_bus_server_stop — the rc179 accept model) + srmech_bus_broadcast +
 * srmech_bus_subscriber_count all take the mutex; the registry is race-free.
 * Teardown (srmech_bus_server_stop) closes every subscriber conn + destroys
 * the mutex under the lock. On POSIX the fan-out + teardown are ASAN/UBSAN +
 * ThreadSanitizer clean; closing a subscriber's server-side fd wakes its
 * blocking read deterministically.
 *
 * PLATFORM SCOPE — POSIX-first (Windows is a follow-up). The Windows PAL
 * transport is a NAMED PIPE whose instance is created lazily inside accept
 * (POSIX listen pre-binds), and a synchronous ConnectNamedPipe is not reliably
 * woken by CloseHandle from another thread — so a Windows pubsub_accept with no
 * connected client can block indefinitely and teardown cannot deterministically
 * wake it. The symbols BUILD on Windows, but a correct Windows pub/sub server
 * (overlapped ConnectNamedPipe + a stop-event, or pre-created instances +
 * a self-connect wake) needs Windows-CI verification and is a follow-up rc.
 * The req/rep + encrypted transport (rc2 / rc179) are unaffected.
 *
 * ABI v4 (this rc): the new srmech_bus_subscriber_callback_t typedef carries
 * a CFUNCTYPE wire-format implication (the v2→v3 handler-callback precedent),
 * so ABI bumps; the broadcast / accept / count / pipe functions are additive.
 * ------------------------------------------------------------------ */

/* Pub/sub subscriber-delivery callback. srmech_bus_subscribe reads each
 * broadcast frame (decrypting on the encrypted path) into the caller buffer,
 * then invokes this callback with the plaintext event bytes. Returning
 * SRMECH_OK keeps streaming; any non-OK return UNSUBSCRIBES (srmech_bus_
 * subscribe returns cleanly). `user_data` is the opaque context pointer. */
typedef srmech_status_t (*srmech_bus_subscriber_callback_t)(
    const uint8_t *event,
    size_t         event_len,
    void          *user_data);

/* Max concurrently-registered subscribers per server (bounded registry). */
#define SRMECH_BUS_MAX_SUBSCRIBERS 64u

/* Accept ONE client and register it as a subscriber (BLOCKING). Caller
 * spins this in a thread loop (join before srmech_bus_server_stop). The
 * accepted connection is retained in the registry (NOT closed on return);
 * srmech_bus_broadcast writes to it; srmech_bus_server_stop closes it.
 *
 * Error returns:
 *   SRMECH_ERR_NULL_ARG — h is NULL.
 *   SRMECH_ERR_OVERFLOW — the registry is full (SRMECH_BUS_MAX_SUBSCRIBERS).
 *   SRMECH_ERR_IO       — accept failed (server stopped). */
srmech_status_t srmech_bus_pubsub_accept(srmech_bus_server_handle_t *h);

/* Broadcast `body` (length `body_len`) to every currently-registered
 * subscriber, under the registry mutex. Per-subscriber write failure drops
 * that subscriber (best-effort fan-out); returns SRMECH_OK after the pass.
 * On an encrypted server the body is encrypted per-subscriber.
 *
 * Error returns:
 *   SRMECH_ERR_NULL_ARG — h is NULL (or body NULL with body_len != 0).
 *   SRMECH_ERR_OVERFLOW — body_len > UINT32_MAX. */
srmech_status_t srmech_bus_broadcast(
    srmech_bus_server_handle_t *h,
    const uint8_t              *body,
    size_t                      body_len);

/* Current registered-subscriber count into *out_count (mutex-guarded read —
 * a subscribe/broadcast sync point for callers). */
srmech_status_t srmech_bus_subscriber_count(
    srmech_bus_server_handle_t *h,
    size_t                     *out_count);

/* Subscribe: stream broadcasts from a connected client handle (from
 * srmech_bus_connect / _connect_encrypted). Loops reading frames (decrypting
 * on the encrypted path) into the caller-owned `buf` (capacity `buf_cap`) and
 * invoking `cb(event, event_len, user_data)` per frame. Returns SRMECH_OK on
 * clean end (server closed the stream, or `cb` returned non-OK to unsubscribe).
 *
 * Error returns:
 *   SRMECH_ERR_NULL_ARG — h, buf, or cb is NULL. */
srmech_status_t srmech_bus_subscribe(
    srmech_bus_client_handle_t       *h,
    uint8_t                          *buf,
    size_t                            buf_cap,
    srmech_bus_subscriber_callback_t  cb,
    void                             *user_data);

/* Pipe: subscribe to `source` and forward every broadcast (fire-and-forget)
 * to `sink` — the C composition mirroring srmech.bus._pipe.pipe (identity
 * forward; the Python transform= / asyncio wrappers are Python-side
 * affordances). Composes srmech_bus_connect (×2) + srmech_bus_subscribe +
 * the frame writer. `buf` (capacity `buf_cap`) is the caller-owned per-event
 * staging buffer. Blocks until `source` closes; returns SRMECH_OK on clean
 * end.
 *
 * Error returns:
 *   SRMECH_ERR_NULL_ARG — source, sink, or buf is NULL.
 *   plus any srmech_bus_connect error (source / sink not reachable). */
srmech_status_t srmech_bus_pipe(
    const char *source,
    const char *sink,
    uint8_t    *buf,
    size_t      buf_cap);

/* ------------------------------------------------------------------ *
 * srmech.bus — UTLP Bio-TOTP wire cipher C peer (0.9.0rc178; ANNEX
 * Batch A part 1). A FAITHFUL BYTE-EXACT mirror of the already-shipped
 * Python cipher `srmech/bus/_bio_totp.py` — the DEFAULT stdlib
 * HMAC-SHA-256 counter-mode path only (the optional AES-128-CTR
 * `[crypto]` extra stays Python, out of the bare-C-host default).
 *
 * Each op COMPOSES existing kernels (no new hash, no new parser):
 * srmech_sha256_hex (key derive), srmech_hmac_sha256 (keystream),
 * srmech_json_parse / srmech_json_object_get (binding check). The Python
 * ops dispatch to these under HAS_NATIVE (ctypes, hasattr-guarded) and
 * keep the COMPLETE pure path for a stale / no-C host (value-parity).
 * Caller-arena / bounded-stack only (JPL Rule 3). New symbols only, so
 * SRMECH_ABI_VERSION stays 3.
 * ------------------------------------------------------------------ */

/* Derive the 16-byte Bio-TOTP key for one time window:
 *   out16 = sha256(dna || quantized_time_be8_signed)[0:16]
 * where quantized_time = floor(time_ns / window_ns) (Python //, so a
 * negative time_ns floors toward -inf) serialised as 8 big-endian
 * two's-complement bytes. window_ns must be > 0. `dna` (dna_len bytes;
 * NULL iff dna_len == 0) is capped at 256 bytes on the bounded stack —
 * a longer dna returns SRMECH_ERR_OVERFLOW (the Python wrapper's pure
 * path handles any length). Byte-exact with _bio_totp.derive_key. */
srmech_status_t srmech_bio_totp_derive_key(const uint8_t *dna, size_t dna_len,
                                           int64_t time_ns, int64_t window_ns,
                                           uint8_t *out16);

/* XOR `data[0..data_len)` with the HMAC-SHA-256 counter-mode keystream
 * derived from (key16, nonce16), writing `data_len` bytes to `out`
 * (encrypt and decrypt are the same operation). Keystream block i =
 * HMAC(key16, nonce16 || i_be4), i = 0, 1, ...; the 32-byte blocks are
 * concatenated and truncated to data_len. data_len == 0 is a no-op
 * (`out` / `data` may be NULL then). Byte-exact with the stdlib
 * HMAC-CTR branch of _bio_totp._stream_cipher. */
srmech_status_t srmech_bio_totp_keystream_xor(const uint8_t *key16,
                                              const uint8_t *nonce16,
                                              const uint8_t *data,
                                              size_t         data_len,
                                              uint8_t       *out);

/* Bytes of caller workspace srmech_bio_totp_decode_splice needs for the
 * binding-check srmech_json parse of the recovered plaintext (bounded by
 * the ciphertext length; a proven over-approximation). */
size_t srmech_bio_totp_decode_splice_arena_bytes(size_t framed_len);

/* Pure-function decode (mirrors _bio_totp.decode_splice): given a wire
 * body `framed` = [nonce:16][ciphertext] and the `dna` secret, try the
 * current time window then ±1 (deltas 0, -1, 1 in that order) for
 * clock-skew tolerance; on the FIRST window whose decryption binds to the
 * nonce under PERMISSIVE mode, write the plaintext to `out_plaintext`
 * (capacity `out_cap` >= ciphertext length), set *out_len, *out_used_time
 * = the candidate time that decoded, and *out_found = 1. If no window
 * binds, *out_found = 0 (the Python caller raises BioTotpDecryptError).
 * `now_ns` is the resolved current time (the Python side calls
 * time.time_ns()); `window_ns` must be > 0. A frame shorter than 16 bytes
 * returns SRMECH_ERR_BAD_INPUT (the format error). `ws` (size it with
 * srmech_bio_totp_decode_splice_arena_bytes) backs the binding parse.
 * Byte-exact plaintext + verdict with the pure decode_splice. */
srmech_status_t srmech_bio_totp_decode_splice(
    const uint8_t *framed, size_t framed_len,
    const uint8_t *dna, size_t dna_len,
    int64_t window_ns, int64_t now_ns,
    void *ws, size_t ws_len,
    uint8_t *out_plaintext, size_t out_cap, size_t *out_len,
    int64_t *out_used_time, int *out_found);

/* --------------------------------------------------------------------
 * Hamming / GF(2) linear block-code family (#910 / §30; F442/F449).
 *
 * The CARRY/EC half of the sedenion front-loader: a 2^n-1 single-error-
 * correcting Hamming code, lean-ALU XOR-native (GF(2) add = parity = XOR;
 * no float, no libm, no malloc). Canonical 1-indexed construction: codeword
 * length N = 2^n - 1, parity bits at the power-of-two positions; the syndrome
 * IS the 1-indexed position of the single flipped bit (0 = clean). Distance 3
 * => corrects any single-bit error. Hamming(7,4) is the octonion's own Fano
 * plane (F441). Rosetta peer of srmech.cascade.hamming_* — attested
 * bit-exact by tests/test_cascade_hamming_parity.py.
 *
 * ABI-additive: new symbols + one macro, so SRMECH_ABI_VERSION stays 3.
 * ------------------------------------------------------------------ */

/* Upper bound on the parity-bit count n (codeword 2^n - 1 <= 65535). Shared
 * with the Python surface (srmech.cascade.hamming.HAMMING_MAX_N). */
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
 * Rosetta peer of srmech.cascade.cayley_dickson.cd_basis_product —
 * attested bit-exact by tests/test_cascade_cayley_dickson_parity.py.
 *
 * ABI-additive: a new symbol + two macros, so SRMECH_ABI_VERSION stays 3.
 * ------------------------------------------------------------------ */

/* Hard ceiling on the algebra dimension (a power of two). Shared with the
 * Python surface (srmech.cascade.cayley_dickson.CD_MAX_DIM).
 *
 * rc298 (`#933`): 64 -> 256. The old 64 was a TOOLING bound that stopped the
 * rung sweep four doublings past the Hurwitz wall; PR #687 named it as the
 * thing blocking the research, not the mathematics.
 *
 * WHY 256 IS CHEAP. Every scratch buffer reached by the ADDRESSING path is
 * LINEAR in this cap:
 *   srmech_cayley_dickson.c  seen[2*MAX] (121, 204), es[]/ei[] (251-252),
 *                            units[]/subset[]/sub_gens[] (295, 301-302),
 *                            acc[] (331)
 *   srmech_cd_register.c     seen[MAX] (168)
 *   srmech_qmat.c            arena ws-bounds (linear in dim)
 * At 256 the largest of those is 2*256*sizeof(int) = 2 KB. The whole
 * addressing surface fits in a few KB of stack at any rung this cap admits.
 *
 * The one QUADRATIC buffer in the tree — srmech_sedenion.c's dim x dim
 * modular-rank matrix — is NOT on the addressing path and does NOT follow this
 * cap. It has its own, deliberately smaller ceiling: see
 * SRMECH_CD_DENSE_MAX_DIM below. Raising THIS macro does not enlarge any
 * quadratic allocation anywhere.
 *
 * The remaining ceiling above 256 is VERIFICATION TIME, not memory: proving
 * srmech_cd_navmap_is_signed_permutation at a rung costs O(dim^2) basis
 * products, and the Python cross-path check against a full cd_mult costs
 * O(dim^4) rational multiplies. The linear buffers would tolerate 1024
 * (16 KB); we cap where we can still PROVE the rung rather than assert it. */
#define SRMECH_CD_MAX_DIM 256
/* log2(SRMECH_CD_MAX_DIM) — the doubling-loop over-bound (JPL Rule 2). */
#define SRMECH_CD_MAX_LEVELS 8

/* Ceiling on the DENSE dim x dim path — srmech_sedenion_is_navigable's
 * modular-rank matrix (srmech_sedenion.c). This is a SEPARATE capability from
 * addressing and carries a separate bound because its cost profile is
 * quadratic, not linear:
 *
 *     dim  |  int64_t mat[dim*dim]
 *      64  |   32 KB      <- here
 *     128  |  131 KB
 *     256  |  524 KB
 *     512  |    2 MB      <- exceeds MSVC's 1 MB default thread stack
 *
 * gcc/clang default to ~8 MB of thread stack; MSVC defaults to 1 MB. Sizing
 * this buffer off SRMECH_CD_MAX_DIM would put a 524 KB frame on every
 * is_navigable call — over half the Windows budget — for a function that never
 * participates in addressing. So the two caps are decoupled.
 *
 * Beyond this bound srmech_sedenion_is_navigable returns SRMECH_ERR_BAD_INPUT.
 * That is a PERFORMANCE-projection boundary, not a capability one: the Python
 * peer's _native_is_invertible already treats a non-OK return as "route to the
 * exact-rational oracle" (the same path it uses beyond int64 magnitude), so
 * left_mult_is_invertible stays CORRECT at every dim <= SRMECH_CD_MAX_DIM —
 * just slower past this cap. ADR-0009: the capability is the invariant; which
 * projection answers is not. */
#define SRMECH_CD_DENSE_MAX_DIM 64

/* ---- the OTHER two carrier ceilings (rc339, `#T967`) ---------------------
 *
 * SRMECH_CD_MAX_DIM and SRMECH_CD_DENSE_MAX_DIM above are BOTH ADDRESSING
 * bounds. Publishing only those answers "how big can this go?" with 256 and
 * stays silent on the two ceilings that actually bind, so a caller — or an LLM
 * driving the MCP surface — can read 256 and try to TURN there, where
 * non-commuting turn composition died at dim 8. A permissive ceiling reported
 * without its capability implies a capability that does not exist. These two
 * macros are the missing halves; the Python peers are
 * srmech.cascade.cayley_dickson.CD_COMPOSE_MAX_DIM / CD_TURN_MAX_DIM and
 * tests/test_carrier_capability_rc339.py pins the four in lockstep (ADR-0009:
 * the capability is the invariant, so a bare-C host reads the same ceilings).
 *
 * Macros, not exported symbols: SRMECH_ABI_VERSION is untouched. */

/* COMPOSE ceiling: the largest dim whose product has NO ZERO DIVISORS (a
 * normed composition algebra). Hurwitz (1898): 1, 2, 4, 8 and nothing else.
 * Past it (dim 16, the sedenions) there exist x != 0, y != 0 with x*y == 0 —
 * which is the whole reason srmech_sedenion_is_navigable has a question to
 * answer. Strictly below SRMECH_CD_MAX_DIM: addressing outruns composition. */
#define SRMECH_CD_COMPOSE_MAX_DIM 8

/* TURN ceiling: the largest dim at which NON-COMMUTING turn composition
 * survives ON THIS LADDER. A turn composes iff left multiplication is a
 * representation — L_x o L_y == L_(x*y), i.e. x*(y*z) == (x*y)*z for every z.
 *
 * SCOPE (rc343, `#T972`): this is a CAYLEY-DICKSON ceiling, NOT a universal
 * one. The earlier wording here — "this is associativity read as a statement
 * about turns, and it stops at H" — was the GENERAL form of a ladder-specific
 * fact, and it is false for any associative carrier at dimension. srmech's own
 * Mat (product mat_matmul, associative at every dim) was MEASURED over the
 * matrix units of M_n(R): 81/81 turn-composing pairs at n=3 (algebra dim 9),
 * 42 of them NON-commuting, and 256/256 at n=4 (dim 16), 108 non-commuting.
 * The ceiling is PER-CARRIER — every carrier row in srmech_carrier_registry
 * publishes its own max_dim / bounded_by — and
 * describe()["limits"]["capabilities"]["turn"] carries `family` =
 * "cayley_dickson" plus a DERIVED `exceeded_by` naming what outruns it.
 *
 * WHY it stops here, on THIS ladder. Not "associativity": turn composition IS
 * associativity, so that reason merely restates the definition and no carrier
 * row could ever contradict it. The Cayley-Dickson product FACTORS into an XOR
 * on the INDEX and a COCYCLE on the SIGN, and the halves behave differently
 * (measured over srmech_cd_basis_product):
 *
 *     dim | index == a XOR b | negative signs (C(d,2)) | SIGN COCYCLE assoc
 *       2 |       4/4        |        1  (1)           |     8/8      100%
 *       4 |      16/16       |        6  (6)           |    64/64     100%
 *       8 |      64/64       |       28  (28)          |   344/512     67%
 *      16 |     256/256      |      120  (120)         |  2248/4096    55%
 *      32 |    1024/1024     |      496  (496)         | 16808/32768   51%
 *
 * The index lane is exact at EVERY rung; the SIGN is what stops being
 * associative, abruptly, at dim 8. So addressing is unbounded because XOR is
 * associative forever, and turns/composition break because the sign cocycle is
 * not — which is also why rc298 could lift SRMECH_CD_MAX_DIM 64 -> 256 by
 * DECOUPLING the caps. (`index == XOR` is close to definitional for a CD
 * basis, so that column is a CHECK; the READING it supports — a free index
 * and a load-bearing sign — is the part that is not.)
 *
 * MEASURED over the basis of each rung (generating code + NDJSON:
 * docs/srmech/notes/carrier_capability_ontology_rc339.py):
 *
 *     dim  1: 1/1     dim  2: 4/4     dim  4: 16/16
 *     dim  8: 22/64   dim 16: 46/256  dim 32: 94/1024
 *
 * The largest power-of-two SUB-rung all of whose turns compose is 4 at dim 8
 * AND at dim 16 AND at dim 32 — it saturates and never grows again.
 *
 * The precise statement is NOT "turns stop at H". Turns DEGRADE TO
 * ABELIAN-ONLY at O: measured as SETS (not merely as equal counts), the
 * turn-composing basis pairs and the commuting basis pairs are THE SAME SET at
 * dim 8, 16 and 32 — both set differences empty. At dim 4 they are not (16
 * compose, 10 commute: 6 non-commuting pairs still compose). What dies at the
 * octonion rung is specifically NON-COMMUTING turn composition. */
#define SRMECH_CD_TURN_MAX_DIM 4

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
 * srmech_algebra_table — the GAMMA-PARAMETERISED Cayley-Dickson doubling,
 * materialised as a rank-3 structure-constant table (rc352, `#T997`).
 *
 * The generalised doubling carries one parameter per rung:
 *     (a1, a2)(b1, b2) = (a1 b1 + gamma * b2~ a2,  b2 a1 + a2 b1~)
 * gamma == -1 at every level IS the definite ladder R -> C -> H -> O -> S ...
 * that srmech_cd_basis_product / srmech_cd_mult compute; a +1 anywhere makes
 * the algebra SPLIT. Both are served by ONE cocycle engine in
 * src/srmech_cayley_dickson.c, so `gammas == NULL` reproduces
 * srmech_cd_basis_product bit-for-bit rather than paralleling it.
 *
 * WHY IT EXISTS: CONTROLS. Every negative control the split-algebra work needs
 * -- split-O, split-C, split-H, arbitrary hand-built tables -- had to be
 * hand-rolled because no constructor shipped. It is NOT a capability claim:
 * the whole 8-member gamma family at dim 8 is sign-cocycle-degenerate in the
 * same 344/512 way (see SRMECH_CD_TURN_MAX_DIM above), and every associative
 * twist is a matrix algebra the Mat carrier already publishes. See
 * `[[feedback_negative_controls_for_carrier_claims_split_octonion_and_random_anticommutative]]`.
 *
 * Rosetta peers of srmech.cascade.{algebra_table, table_product}.
 * Additive symbols -> SRMECH_ABI_VERSION unchanged (stays 10).
 * ------------------------------------------------------------------ */

/* Largest dim srmech_algebra_table will MATERIALISE. Lower than
 * SRMECH_CD_MAX_DIM (256) and than SRMECH_ALGEBRA_INERTIA_MAX_DIM (256)
 * because the table itself is dim*dim*dim int64 -- 2 MiB at 64, 128 MiB at
 * 256. A THIRD ceiling with a THIRD name, so none of them can stand in for
 * another: this one bounds MATERIALISATION, not addressing and not the
 * elimination. The cocycle underneath is exact at every dim
 * srmech_cd_basis_product accepts. */
#define SRMECH_ALGEBRA_TABLE_MAX_DIM 64u

/* Fill `out_table` (caller-sized, dim*dim*dim int64) with the structure
 * constants of the generalised Cayley-Dickson algebra:
 * out_table[(i*dim + j)*dim + k] is the coefficient of e_k in e_i * e_j --
 * the SAME layout srmech_algebra_inertia_signature reads.
 *
 *   dim      : power of two in [1, SRMECH_ALGEBRA_TABLE_MAX_DIM].
 *   gammas   : n_gammas entries, each +1 or -1, in LADDER ORDER (gammas[0] is
 *              the R->C doubling, gammas[1] is C->H, ...). NULL (with
 *              n_gammas == 0) means -1 at every level -- the definite ladder.
 *   n_gammas : must be log2(dim) when gammas != NULL.
 *
 * The result is MONOMIAL: e_i * e_j = sign * e_{i XOR j}, so exactly dim*dim
 * of the dim*dim*dim cells are nonzero. Integer-only: no float, no libm, no
 * malloc, no recursion. Errors: SRMECH_ERR_NULL_ARG; SRMECH_ERR_BAD_INPUT
 * (dim out of range or not a power of two; n_gammas mismatched; a gamma
 * outside {+1, -1}). */
srmech_status_t srmech_algebra_table(int dim, const int *gammas,
                                     size_t n_gammas, int64_t *out_table);

/* ------------------------------------------------------------------
 * Cayley-Dickson loop NAVIGATION (v0.9.0rc158; Qalg TAIL Batch 2) — the
 * combinatorial layer over the srmech_cd_basis_product cocycle, INTEGER-only
 * (signed basis units +-e_i; no float, no bignum, no libm, no malloc). A
 * "signed unit" is (sign, index) with sign in {+1,-1}, index in [0, dim); the
 * full Moufang loop has 2*dim of them. These give a C-only host the loop
 * analogues of the cyclic-group orbit machinery: the sub-loop a generator set
 * spans, one left-multiplication cycle, and the minimum spanning cardinality.
 * Each COMPOSES srmech_cd_basis_product (it does NOT re-implement the cocycle).
 * Rosetta peers of
 * srmech.cascade.cayley_dickson.{closure,left_orbit,min_generating_set},
 * attested BYTE-IDENTICAL by tests/test_qalg_cdnav_c_rc158.py.
 * (rc395 `#T1000`: the fourth peer srmech_cd_zero_divisor_witness was REMOVED —
 * subsumed by the composition_of_c cd_zero_divisor_witness over gf_rref +
 * cd_basis_product; ABI 10 -> 11.)
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

/* (rc395, task #T1000) srmech_cd_zero_divisor_witness was REMOVED here: the
 * dedicated dim-16 brute-force export is subsumed by the dim-general Python
 * cd_zero_divisor_witness / cd_zero_divisor_witnesses, a composition_of_c over
 * the GF(2) gf_rref + cd_basis_product. Its removal bumped SRMECH_ABI_VERSION to
 * 11 (see the ABI history above). */

/* ------------------------------------------------------------------
 * Qi — the EXACT-complex (Gaussian-rational) carrier C-host peer (0.9.0rc15;
 * Python srmech.math.qi.Qi). A Qi value is FOUR int64 limbs
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
 * F468; Python srmech.cascade.sedenion_register). The navigation +
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
 * vector of power-of-two length n in [1, SRMECH_CD_DENSE_MAX_DIM]) a bijection?
 * Sets *out_invertible to 1 (invertible / navigable) or 0 (a left zero
 * divisor). Exact (modular rank; bit-identical bool to the Python
 * Fraction-nullspace oracle). Errors: SRMECH_ERR_NULL_ARG; SRMECH_ERR_BAD_INPUT
 * (n not a power of two in range, magnitude overflow, or coefficients beyond
 * the certainty prime table).
 *
 * NOTE THE CAP: this is the DENSE bound (rc298, `#933`), deliberately smaller
 * than SRMECH_CD_MAX_DIM because the dim x dim modular-rank matrix is the only
 * quadratic buffer in the library. A caller wanting invertibility past it uses
 * the exact-rational nullspace (srmech_qmat_nullspace over the left-mult
 * matrix), which is caller-arena-backed and carries no compiled-in cap — that
 * is exactly what the Python peer does. */
srmech_status_t srmech_sedenion_is_navigable(const int64_t *direction,
                                             size_t n, int *out_invertible);

/* rc199 (make_class → C, leaf-batch 5/8; #887): the `slots` accessor's
 * canonical numeric reshape. Validate + copy the register's occupied
 * (slot, sign) skeleton — slot in [0,16), sign in {+1,-1} — into
 * out_slots / out_signs (the make_class `slots` leaf's numeric core; the
 * key strings pass through in the Python caller, and the slot int-keys
 * ride the srmech_mval_t DICT as STR "0".."15" one layer up). count == 0
 * is a no-op. Errors: SRMECH_ERR_NULL_ARG; SRMECH_ERR_BAD_INPUT (slot out
 * of range or sign not +-1 -> the Python caller runs the un-validated pure
 * reshape; inform-don't-limit). ABI-additive: a new symbol, no callback
 * typedef, so SRMECH_ABI_VERSION stays 4. See srmech_sedenion.c. */
srmech_status_t srmech_sed_slots(const int *in_slots, const int *in_signs,
                                 size_t count, int *out_slots, int *out_signs);

/* ------------------------------------------------------------------
 * rc297 (#934): the GENERAL N-slot Cayley-Dickson address layer — the same
 * navigation surface as the srmech_sedenion_* peers above, generalised from
 * the hard-coded 16 slots to any power-of-two dim in [1, SRMECH_CD_MAX_DIM].
 * The Python peer is srmech.cascade.cd_register (CDRegister).
 *
 * WHY THIS IS SOUND ABOVE THE HURWITZ WALL (F1274 / F1275). Addressing does
 * not need the division property; it needs only that a basis product be a
 * SIGNED PERMUTATION (e_i * e_j = +- e_k). Zero divisors are built from SUMS
 * of basis elements, never from a single basis pair, so the boundary that
 * destroys composition at dim >= 16 leaves addressing untouched. The two
 * properties are disjoint. srmech_cd_navmap_is_signed_permutation makes that
 * premise checkable at runtime instead of assumed.
 *
 * The slot bound is the ONLY generalisation: every sign and index rule is
 * shared verbatim with the 16-slot peers through srmech_cd_basis_product.
 * Nothing here scales quadratically in dim, so this layer imposes no new
 * ceiling on SRMECH_CD_MAX_DIM.
 *
 * ABI-additive: new symbols only, no callback typedef and no wire-format
 * change to any existing export, so SRMECH_ABI_VERSION stays 8.
 * See srmech_cd_register.c.
 * ------------------------------------------------------------------ */

/* The signed pointer-advance permutation for right-multiply-by-e_j over `dim`
 * slots: for each slot i in [0,dim), out_dest[i] = k and out_sign[i] = s where
 * e_i * e_j = s * e_k. out_dest / out_sign are caller arrays of length >= dim.
 * dim is a power of two in [1, SRMECH_CD_MAX_DIM]; j in [0,dim). At dim == 16
 * this is bit-identical to srmech_sedenion_navmap. Errors:
 * SRMECH_ERR_NULL_ARG; SRMECH_ERR_BAD_INPUT (bad dim, or j out of range). */
srmech_status_t srmech_cd_navmap(int dim, int j, int *out_dest, int *out_sign);

/* Route `count` occupied (slot, sign) records through the x e_j permutation at
 * `dim` slots, composing the Class-C signs: out_slots[m] = k and out_signs[m] =
 * in_signs[m] * s where e_{in_slots[m]} * e_j = s * e_k. in_signs entries must
 * be +1/-1 and in_slots in [0,dim). count == 0 is a no-op. At dim == 16 this is
 * bit-identical to srmech_sedenion_navigate. Errors: SRMECH_ERR_NULL_ARG;
 * SRMECH_ERR_BAD_INPUT (bad dim, j / slot out of range, or sign not +-1). */
srmech_status_t srmech_cd_navigate(int dim, int j, const int *in_slots,
                                   const int *in_signs, size_t count,
                                   int *out_slots, int *out_signs);

/* The STRUCTURAL INVARIANT addressing rides on, checked rather than assumed:
 * for EVERY direction j in [0,dim), is i -> (dest, sign) a bijection on
 * [0,dim) with every sign in {+1,-1}?  Sets *out_ok to 1 (the premise holds at
 * this rung) or 0 (it fails). SCOPE: this verifies the bijection + sign-domain
 * property of the navmap as computed by the srmech_cd_basis_product cocycle;
 * it does NOT independently re-derive e_i * e_j from a full Cayley-Dickson
 * multiplication. That cross-path check lives in the Python suite, which has an
 * exact-rational cd_mult to check the cocycle shortcut against. Errors:
 * SRMECH_ERR_NULL_ARG; SRMECH_ERR_BAD_INPUT (bad dim). */
srmech_status_t srmech_cd_navmap_is_signed_permutation(int dim, int *out_ok);

/* ------------------------------------------------------------------
 * srmech_algebra_inertia — is an algebra ORDERABLE? Read off its
 * multiplication table, exactly (rc349; the R->C rung of the Hurwitz loss
 * ladder, the one rung that had no instrument).
 *
 * x -> Re(x*x) is a QUADRATIC FORM, so its complete invariant is the Sylvester
 * inertia signature (n_plus, n_minus, n_zero). This op computes that from the
 * table and returns a concrete negative direction with it -- an instrument,
 * not a lookup. It measures THE INERTIA OF ONE QUADRATIC FORM AND NOTHING
 * ELSE; n_minus == 0 does NOT mean "orderable" (see the per-op comment).
 *
 * IT READS THE TABLE, NEVER A DECLARED DIMENSION, and never the coordinate
 * form a^2 - |v|^2: nothing here consults SRMECH_CD_MAX_DIM or any imaginary-
 * dimension constant, and Re(x*x) is summed from the structure constants. That
 * coordinate substitution is input-blind -- it agrees with the real read
 * 4000/4000 on O but only 854/4000 on split-O, and stays wrong at infinite
 * precision. Measured here: R (1,0,0) / C (1,1,0) / H (1,3,0) / O (1,7,0) /
 * S16 (1,15,0), and split-O (5,3,0) -- NOT the (1,7,0) of O, which is the
 * control that proves the read is of the algebra rather than of the ladder.
 *
 * Rosetta peer of srmech.cascade.cayley_dickson.inertia_signature.
 * Additive symbols -> SRMECH_ABI_VERSION unchanged.
 * ------------------------------------------------------------------ */

/* The largest dimension the exact int64 elimination accepts. Not a memory cap
 * (the working state is caller-arena backed): it bounds the dim*dim*dim table
 * index and the ws-bound arithmetic. */
#define SRMECH_ALGEBRA_INERTIA_MAX_DIM 256u

/* Minimum `ws_len` BYTES for srmech_algebra_inertia_signature at this dim.
 * Returns 0 for a dim outside [1, SRMECH_ALGEBRA_INERTIA_MAX_DIM]. */
size_t srmech_algebra_inertia_ws_bound(size_t dim);

/* Sylvester inertia signature of a quadratic form read off the algebra whose
 * rank-3 structure-constant tensor is `table`: table[(i*dim + j)*dim + k] is
 * the coefficient of e_k in e_i * e_j. Basis element 0 is the real direction.
 *
 * `form` selects the read, and NAMING IT IS LOAD-BEARING -- the two are
 * different forms with complementary signatures:
 *   0  TRACE  q(x) = Re(x*x)   -- the SQUARES read. split-O -> (5,3,0)
 *   1  NORM   N(x) = Re(x*x~)  -- x~ = x_0 e_0 - sum_{i>0} x_i e_i, a NAMED
 *                                 convention a bare tensor does not determine.
 *                                 split-O -> (4,4,0), which is what the
 *                                 literature quotes.
 *
 * *out_n_plus / *out_n_minus / *out_n_zero <- the signature (they sum to dim).
 * *out_has_witness <- 1 iff n_minus > 0, in which case out_witness (caller-
 * sized `dim`) receives the primitive integer negative pivot direction w, with
 * the chosen form negative at w. *out_has_witness <- 0 means NO NEGATIVE
 * DIRECTION IN THIS FORM -- it does NOT mean the algebra is orderable
 * (split-C answers 0 here and has zero divisors, so it is provably not
 * orderable). A witness-finder that can never return "none" is not measuring
 * anything, so R must and does land there.
 *
 * SCOPE: this reads the inertia of one quadratic form and nothing else. It
 * cannot certify composition, alternativity, associativity or division -- a
 * table with the diagonal pinned and the off-diagonal scrambled answers
 * exactly as O does. Use srmech_loop_associator_f64 / srmech_g2_three_form_f64
 * / srmech_sedenion_is_navigable for the off-diagonal structure.
 *
 * `ws` >= srmech_algebra_inertia_ws_bound(dim). Exact integers throughout: no
 * float, no epsilon, no division except an inertia-invariant positive-gcd
 * strip. Errors: SRMECH_ERR_NULL_ARG; SRMECH_ERR_BAD_INPUT (dim outside
 * [1, SRMECH_ALGEBRA_INERTIA_MAX_DIM], or form outside {0, 1});
 * SRMECH_ERR_OVERFLOW (ws too small, or an exact intermediate leaves int64 --
 * never a silent wrap; the Python peer then routes to its ceiling-free bignum
 * path). */
srmech_status_t srmech_algebra_inertia_signature(const int64_t *table,
                                                 size_t dim, int form,
                                                 void *ws, size_t ws_len,
                                                 int *out_n_plus,
                                                 int *out_n_minus,
                                                 int *out_n_zero,
                                                 int *out_has_witness,
                                                 int64_t *out_witness);

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
 * float-free) — AND, as of rc403 (`#T1071`), for FINITE doubles too,
 * via the integer-only Ryu converter behind srmech_double_repr. A
 * non-finite double DECLINES the write. See the byte-parity rules at
 * srmech_json_write below for the exact domain.
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
 * rc404 (`#T1069`) — SRMECH_ERR_LIMIT, and why the distinction is the point.
 * SRMECH_ERR_OVERFLOW now means EXACTLY "your arena was too small; GROW IT AND
 * RETRY and this call may succeed". Conditions no arena can relieve return
 * SRMECH_ERR_LIMIT instead, and a caller must NOT retry them:
 *   - an integer outside int64 (`99999999999999999999`)
 *   - a numeric literal >= 63 bytes (the internal staging bound)
 *   - nesting past SRMECH_JSON_MAX_DEPTH (64)
 *   - uint32 saturation of a container's child count
 * All four returned SRMECH_ERR_OVERFLOW through rc403, so a grow-loop could not
 * tell them from exhaustion and doubled its arena to the cap before declining —
 * measured at 13 calls and ~512 MiB for a verdict fixed at the first byte. The
 * ANSWER was always correct; only the cost was wrong.
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
 * json.dumps(obj, sort_keys=True, ensure_ascii=False) — the FULL kwarg
 * combination, no other. DOUBLE values are byte-identical too as of
 * rc403 (`#T1071`): each rides srmech_double_repr, an integer-only Ryu
 * conversion, so the digits are a function of the input bits alone.
 * Before rc403 this was snprintf("%.17g"), which was platform-dependent
 * (Windows spells 1e17 as `1e+017`, Linux as `1e+17`) — for a canonical
 * writer whose bytes go behind a sha256 that meant the same tree hashed
 * differently per host.
 *
 * TWO domain limits, both exact and both deliberate:
 *
 *  - NON-FINITE DOUBLE -> SRMECH_ERR_BAD_INPUT for the whole write. RFC
 *    8259 has no NaN / Infinity literal and srmech_json_parse (this
 *    module's other half) declines those tokens by the rc402
 *    adjudication, so emitting them would produce a document this
 *    library cannot read back — fatal for an attestation chain. The
 *    write DECLINES instead, visibly. (srmech_mcp_serialise_result makes
 *    the OPPOSITE call for its own contract; see the note there.)
 *
 *  - OBJECT KEYS ARE STRINGS. CPython's sort_keys=True sorts the original
 *    key OBJECTS and only then coerces them to strings, so a dict with
 *    INTEGER keys orders numerically ({1:..,2:..,10:..} -> "1","2","10")
 *    while this writer, whose tree holds keys already as strings, orders
 *    bytewise ("1","10","2"). That is not a bug to fix here — bytewise IS
 *    correct for the string keys the tree can represent, and a
 *    numeric-aware comparator would then be wrong for the genuine string
 *    keys "1"/"2"/"10". It is a limit on what may be handed to a future
 *    C-backed dumps: coerce non-string keys, and sort, on the Python
 *    side. */
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
 * Tool-schema registry (0.9.0rc184; the C MCP-server FOUNDATION GATE).
 *
 * The ~403-entry srmech.introspect.tool_schema `_REGISTRY` (every public
 * callable surface: name / owner / category / summary / typed params /
 * returns / mcp_callable) crystallised as a `const` data table so a
 * bare-C host (no Python) can produce the tool registry DATA + the
 * canonical `tool_schema_sha256` attestation with no interpreter.
 *
 * The table itself lives in the GENERATED translation unit
 * `srmech_tool_registry.c` (regenerate with c/tools/gen_tool_registry.py);
 * the accessors + the canonical serialiser live in srmech_tool_schema.c.
 *
 * srmech_tool_schema_to_json emits bytes BYTE-IDENTICAL to CPython
 *   json.dumps(get_tool_schema().to_jsonable(),
 *              sort_keys=True, separators=(",", ":"))
 * (the DEFAULT ensure_ascii=True form the `_mcpb` tool_schema hash is
 * taken over — non-ASCII escaped \uXXXX, astral as a UTF-16 surrogate
 * pair, keys emitted in sorted order, compact separators). The
 * documentation-hint fields `example` / `smoke_test_hint` carry an
 * arbitrary-schema payload; the generator bakes each as its already-
 * canonical compact JSON fragment (spliced raw), while the structured
 * core is rebuilt field-by-field here. This byte-identity IS the
 * hash-ratchet's contract: sha256(this) == the Python tool_schema_sha256.
 *
 * ABI-additive: new symbols + two structs, so SRMECH_ABI_VERSION stays 4.
 * ------------------------------------------------------------------ */

/* One typed parameter of a tool entry's call signature. All string
 * pointers are NUL-terminated decoded UTF-8 (never escaped). */
typedef struct {
    const char *name;       /* parameter name                         */
    const char *type;       /* free-form srmech type-string           */
    int         required;   /* 0/1                                    */
    const char *summary;    /* human hint ("" allowed, never NULL)    */
} srmech_tool_param_t;

/* One callable surface in the tool schema. Optional fields are NULL
 * when absent (mirroring ToolEntry.to_jsonable's key omission). */
typedef struct {
    const char               *name;      /* full dotted identifier     */
    const char               *owner;     /* "srmech" or a profile name */
    const char               *category;
    const char               *summary;
    const srmech_tool_param_t *params;   /* NULL iff param_count == 0  */
    uint32_t                  param_count;
    const char               *returns_type;   /* NULL iff no `returns` */
    const char               *returns_shape;  /* "" allowed; unused when returns_type==NULL */
    int                       mcp_callable;    /* 0/1                  */
    const char               *mcp_unavailable_reason; /* NULL when callable */
    const char               *example_json;    /* pre-canonical compact-ASCII JSON fragment, or NULL */
    const char               *smoke_json;      /* pre-canonical compact-ASCII JSON fragment, or NULL */
    const char               *explanation;     /* NUL-terminated decoded UTF-8 hint, or NULL (rc240 #838) */
    /* rc305 (#943): the compose/preserve cascade layer. Ordered sub-op names
     * (`composes`) + maintained-invariant strings (`preserves`); each element
     * is NUL-terminated decoded UTF-8. NULL iff the matching *_count is 0 (a
     * leaf op) — mirroring ToolEntry.to_jsonable's key omission. */
    const char *const        *composes;        /* NULL iff composes_count == 0  */
    uint32_t                  composes_count;
    const char *const        *preserves;       /* NULL iff preserves_count == 0 */
    uint32_t                  preserves_count;
    /* rc347 (#T985): the LANE axis — which lane of its input this op's output
     * DEPENDS ON. `reads_lane` is one of "index" / "sign" / "both", or NULL
     * when the op declares no lane (the correct default for most of the
     * surface: an op whose input carries only ONE of the two lanes cannot
     * declare, because no measurement could contradict it). `reads_input` is
     * what the lane is read OF — "algebra" and/or "geometry" — because two ops
     * can share a LANE while reading different INPUTS, which is exactly the
     * Tw-vs-Wr contrast. Both are declared together or not at all:
     * reads_lane == NULL  iff  reads_input_count == 0. Mirrors
     * ToolEntry.reads_lane / .reads_input and its key omission, so the
     * byte-identity contract holds; both JSON keys sort between "preserves"
     * and "returns". ABI-additive by the rc305 precedent (the composes /
     * preserves fields appended to this same struct without a bump): callers
     * receive a POINTER from srmech_tool_registry_get and never allocate the
     * struct, so appending leaves every existing field offset unchanged.
     * SRMECH_ABI_VERSION STAYS 10. */
    const char               *reads_lane;      /* NULL iff no lane declared     */
    const char *const        *reads_input;     /* NULL iff reads_input_count==0 */
    uint32_t                  reads_input_count;
} srmech_tool_entry_t;

/* Number of registered tool entries in the const table. */
size_t srmech_tool_registry_count(void);

/* The entry at `index`, or NULL if `index` is out of range. */
const srmech_tool_entry_t *srmech_tool_registry_get(size_t index);

/* The entry whose `name` equals `name` (bounded linear scan), or NULL
 * if there is no such entry. `name` must be NUL-terminated. */
const srmech_tool_entry_t *srmech_tool_registry_find(const char *name);

/* Serialise the whole registry as canonical JSON (see byte-identity
 * contract above) into `buf` (capacity `buf_len`; NO trailing NUL) and
 * set *out_len to the byte count. If `buf` is NULL this is a SIZE-QUERY
 * (nothing written; *out_len receives the exact full length). A
 * too-small non-NULL `buf` returns SRMECH_ERR_OVERFLOW. The srmech
 * version field is injected from srmech_version() at call time (so a
 * pure version bump needs no table regeneration). */
srmech_status_t srmech_tool_schema_to_json(char *buf, size_t buf_len,
                                           size_t *out_len);

/* ------------------------------------------------------------------
 * Tool-schema PROJECTION ops (0.9.0rc185; the HOST-GLUE tier over the
 * rc184 const registry table). The C peers of
 *   srmech.introspect.tool_schema.get_tool_schema  / .tool_schema_view
 *   srmech.mcp.tool_entries_to_mcp_defs
 * so a bare-C host produces the SAME projections a Python host does.
 *
 * All three share the two-pass buffer contract of
 * srmech_tool_schema_to_json: `buf == NULL` is a SIZE-QUERY (nothing
 * written; *out_len ← the exact full byte count), a too-small non-NULL
 * `buf` returns SRMECH_ERR_OVERFLOW (never writes past the buffer),
 * NO trailing NUL is emitted, and `out_len == NULL` → SRMECH_ERR_NULL_ARG.
 * JPL-clean (no malloc, no goto, no libm, no abs). ABI-additive
 * (SRMECH_ABI_VERSION stays 4).
 *
 * srmech_get_tool_schema / srmech_tool_schema_view emit the WHOLE schema as
 * the canonical (sorted-key) JSON — the SAME bytes as srmech_tool_schema_to_json
 * (reused per the rc185 brief). Python get_tool_schema() takes no filter and
 * tool_schema_view() IS get_tool_schema().to_jsonable(), so both project the
 * whole schema; the output json-parses back EQUAL to
 * get_tool_schema().to_jsonable() (STRUCTURAL identity — dict equality is
 * order-insensitive). Byte-identity is to the SORTED canonical form (the rc184
 * hash pre-image), which is the only byte-stable whole-schema JSON the const
 * table can produce: the opaque example/smoke_test_hint payloads are baked as
 * sorted-canonical fragments in the table, so the insertion-order to_jsonable
 * bytes are not reconstructible from it. All three names are provided for the
 * 1:1 host surface.
 */
srmech_status_t srmech_get_tool_schema(char *buf, size_t buf_len,
                                       size_t *out_len);
srmech_status_t srmech_tool_schema_view(char *buf, size_t buf_len,
                                        size_t *out_len);

/* Emit the ADVERTISED MCP tool-definitions as a JSON array
 *   [ {"name":..,"description":..,"inputSchema":{"type":"object",
 *      "properties":{<param>:{"type":<json-type>,"description":..}, ...},
 *      "required":[..]}}, ... ]
 * — one object per registry entry with mcp_callable != 0, in table order,
 * byte-identical to
 *   json.dumps(list(srmech.mcp.tool_entries_to_mcp_defs()),
 *              separators=(",", ":"))
 * (insertion-order keys, default ensure_ascii=True). The srmech param
 * type-string → JSON-schema type mapping + the per-type wire-encoding
 * hint (appended to each property description) are a bounded static
 * lexicon mirroring srmech.mcp._tools._TYPE_LEXICON / _ENCODING_HINT;
 * an unknown type degrades to "string" with no hint (the Python SSoT
 * default). Property keys are sanitised to the Anthropic/MCP grammar
 * ^[a-zA-Z0-9_.-]{1,64}$ (mirroring _sanitise_property_key). */
srmech_status_t srmech_tool_entries_to_mcp_defs(char *buf, size_t buf_len,
                                                size_t *out_len);

/* ------------------------------------------------------------------
 * MCP server CONTROL SPINE (0.9.0rc186; the HOST-GLUE JSON-RPC protocol +
 * stdio read-loop). The C peers of srmech.mcp._server.MCPServer.handle +
 * srmech.mcp._stdio.serve_stdio + srmech.mcp._server.build_attestation, so a
 * bare-C host (no Python) serves the MCP lifecycle + discovery surfaces —
 * initialize / notifications/initialized / tools/list / ping / shutdown —
 * natively over stdin/stdout, with the MPR attestation preimage.
 *
 * The tools/call DISPATCH (invoke_tool: dotted-name resolution + the ~403-tool
 * typed-argument marshalling) is the SEPARATE next arc (rc187+). srmech_mcp_handle
 * routes tools/call to a "defer" signal (SRMECH_MCP_DEFER_CALL) when
 * `defer_calls != 0` (the Python host then runs pure invoke_tool), OR — when
 * `defer_calls == 0` (the bare-C serve_stdio loop, no Python) — emits an honest
 * JSON-RPC error (inform-don't-limit). ABI-additive: SRMECH_ABI_VERSION stays 4.
 * ------------------------------------------------------------------ */

/* Advertised protocol version + default server name (mirror
 * srmech.mcp._server.MCP_PROTOCOL_VERSION / MCP_SERVER_NAME). */
#define SRMECH_MCP_PROTOCOL_VERSION "2024-11-05"
#define SRMECH_MCP_SERVER_NAME      "srmech-mcp"

/* srmech_mcp_handle out_kind: what the caller must do with the request. */
#define SRMECH_MCP_RESPONSE     0   /* a JSON-RPC response was written to buf   */
#define SRMECH_MCP_NO_RESPONSE  1   /* a notification — nothing to write        */
#define SRMECH_MCP_DEFER_CALL   2   /* tools/call — caller runs invoke_tool     */
#define SRMECH_MCP_CALL_RESULT  3   /* tools/call — the C invoke_tool spine RAN */
                                    /*  the tool in C; buf holds the result     */
                                    /*  TEXT (== serialise_result). The caller  */
                                    /*  wraps it in the content + attestation   */
                                    /*  envelope (its own clock). (rc188)        */

/* Dispatch ONE JSON-RPC request (`req[0..req_len)`), writing the response into
 * `buf` (capacity `buf_len`; NO trailing NUL) and setting *out_len + *out_kind.
 * The request is parsed into the caller-supplied arena `ws` (length `ws_len`;
 * the srmech_json bump-allocator convention). Two-pass: `buf == NULL` is a
 * SIZE-QUERY (nothing written; *out_len ← the exact full byte count; *out_kind
 * still set); a too-small non-NULL `buf` returns SRMECH_ERR_OVERFLOW.
 *
 * The response is BYTE-IDENTICAL to CPython
 *   json.dumps(MCPServer(name="srmech-mcp").handle(req), separators=(",", ":"))
 * for initialize / tools/list / ping / shutdown (insertion-order keys, default
 * ensure_ascii=True escaping). tools/list embeds srmech_tool_entries_to_mcp_defs.
 *
 * out_kind:
 *   SRMECH_MCP_RESPONSE    — *out_len bytes written (initialize / tools/list /
 *                            ping / shutdown / a JSON-RPC error envelope).
 *   SRMECH_MCP_NO_RESPONSE — a notification (notifications/initialized or an
 *                            unknown notification); *out_len == 0, write nothing.
 *   SRMECH_MCP_DEFER_CALL  — tools/call with `defer_calls != 0`; *out_len == 0,
 *                            the caller runs invoke_tool + attaches attestation.
 *
 * `defer_calls == 0` makes tools/call an honest JSON-RPC error inline (the
 * bare-C loop path, no Python fallback). Errors: SRMECH_ERR_NULL_ARG (out_len /
 * out_kind NULL); SRMECH_ERR_OVERFLOW (buf too small / ws too small). A malformed
 * request → a -32700 parse-error response with a null id (kind RESPONSE). */
srmech_status_t srmech_mcp_handle(const char *req, size_t req_len,
                                  void *ws, size_t ws_len,
                                  char *buf, size_t buf_len,
                                  size_t *out_len, int *out_kind,
                                  int defer_calls);

/* Build the MPR attestation object for one tools/call response into `buf`
 * (two-pass: `buf == NULL` is a size-query). The `response_sha256` is
 * srmech_sha256_hex over the exact preimage
 *   tool_name "\x1f" "srmech <version>" "\x1f" result_text "\x1f" retrieved_at
 * (byte-exact with srmech.mcp._server.build_attestation). The preimage is
 * assembled in the caller arena `ws` (length `ws_len`; size it to
 * len(tool_name)+len("srmech ")+len(version)+len(result_text)+len(retrieved_at)+3).
 * On the size-query pass ws may be NULL (the digest is not needed to size the
 * fixed-shape object). Emits, in insertion order,
 *   {"mpr_version":"1.0","tool_name":..,"parser_version":"srmech <v>",
 *    "retrieved_at":..,"response_sha256":"<64 hex>"}
 * NUL-terminated arguments; NO trailing NUL on the output. */
srmech_status_t srmech_mcp_build_attestation(const char *tool_name,
        const char *result_text, const char *retrieved_at,
        void *ws, size_t ws_len, char *buf, size_t buf_len, size_t *out_len);

/* Run the stdio JSON-RPC read-frame → handle → write-frame loop (the bare-C
 * host's `serve_stdio`): newline-delimited requests from stdin, newline-
 * delimited responses to stdout, both via the PAL. Blocks until stdin EOF (a
 * closed pipe), then returns SRMECH_OK — the deterministic terminator; it never
 * hangs. tools/call is served with the honest bare-C error (defer_calls == 0,
 * no Python invoke_tool). All three buffers are CALLER-supplied (no malloc):
 * `line_buf` (capacity `line_cap`) assembles one request line, `ws` (`ws_len`)
 * is srmech_mcp_handle's parse arena, `resp_buf` (`resp_cap`) holds one response
 * (size it for the largest — tools/list is the whole advertised catalog). A
 * response exceeding resp_cap is dropped (no partial write); an over-long
 * request line is skipped. Returns SRMECH_ERR_IO on a stdio-less target. */
srmech_status_t srmech_mcp_serve_stdio(char *line_buf, size_t line_cap,
                                       void *ws, size_t ws_len,
                                       char *resp_buf, size_t resp_cap);

/* ------------------------------------------------------------------
 * MCP HTTP+SSE TRANSPORT (0.9.0rc194; the HOST-GLUE cross-terminal server).
 *
 * The C peer of srmech.mcp._sse.serve_http_sse: a bare-C host serves MCP over
 * HTTP+Server-Sent-Events on a localhost TCP port. Composes srmech_mcp_handle
 * (JSON-RPC dispatch, defer_calls==0 — like serve_stdio) + the rc194 TCP PAL.
 * A background accept thread routes GET /sse (emit an `endpoint` event, then
 * push JSON-RPC responses as `message` events) + POST /message?session=<id>
 * (202 + the response rides the matching SSE stream) + GET /healthz; a second
 * thread emits a 15s keepalive on idle sessions. See c/src/srmech_mcp_sse.c.
 *
 * NO-HANG teardown (the rc180 socket-teardown discipline): srmech_mcp_sse_stop
 * sets the stop flag + closes the poll-gated TCP listener; both threads return
 * within one tick + join. POSIX-FIRST — on a host where srmech_plat_has_tcp()
 * is 0 (Windows Winsock follow-up / bare-metal) serve returns
 * SRMECH_ERR_BAD_INPUT and a Python host runs the pure http.server.
 *
 * ABI-additive: new symbols, and the server dispatches in C (NO Python
 * callback typedef), so SRMECH_ABI_VERSION stays 4. */

/* Opaque handle to a running MCP HTTP+SSE server. */
typedef struct srmech_mcp_sse_server srmech_mcp_sse_server_t;

/* Bind `host`:`port` (host a dotted-quad, e.g. "127.0.0.1"; port 0 = kernel-
 * assigned) + serve MCP over HTTP+SSE on a background accept thread. Returns
 * immediately with *out_handle; read the bound port with srmech_mcp_sse_port.
 * SRMECH_ERR_BAD_INPUT on a no-TCP host (POSIX-first). */
srmech_status_t srmech_mcp_sse_serve(const char *host, uint16_t port,
                                     srmech_mcp_sse_server_t **out_handle);

/* The bound TCP port of a running server (0 on a NULL handle). */
uint16_t srmech_mcp_sse_port(const srmech_mcp_sse_server_t *h);

/* Stop the server: set the stop flag, close the listener (unblocks the accept
 * poll), join both threads, close all sessions, free the handle. No hang. */
srmech_status_t srmech_mcp_sse_stop(srmech_mcp_sse_server_t *h);

/* Blocking "serve forever" (a bare-C host main / the Python background=False
 * path): serve + join the accept thread. Returns only when the listener stops
 * (e.g. a signalled process). Sole owner of the handle → no concurrent stop. */
srmech_status_t srmech_mcp_serve_http_sse(const char *host, uint16_t port);

/* ------------------------------------------------------------------
 * MCP tool-call MARSHALLING FOUNDATION (0.9.0rc187; the HOST-GLUE
 * JSON-args↔typed-C-args value carrier). The shared bedrock the rc188+
 * invoke_tool DISPATCH + the #796 nested-carrier marshal build on: it
 * generalises the rc181 dsl_chain_run dv_value_t tagged union into a
 * uniform marshalling carrier (`srmech_mval_t`) and mirrors the private
 * Python srmech.mcp._coercion coerce_param / serialise_native for the
 * bucket-(a) CLEAN families (scalar / str / list / bytes / complex).
 *
 * TWO-STAGE marshal (the MCP wire form is NOT self-describing — the param
 * TYPE comes from the rc184 registry, not the value):
 *   (1) srmech_mval_from_json : parse a JSON value tree -> a tagged carrier.
 *   (2) srmech_mcp_marshal_arg : typed-lower keyed on the registry type
 *       string (the INVERSE of rc185's MCP_TYPE_LEXICON) — base64 str ->
 *       BYTES, [re,im] -> COMPLEX, list-of-those recursively, etc.
 * srmech_mcp_serialise_result is the OUTBOUND inverse (typed carrier ->
 * canonical JSON, BYTE-IDENTICAL to CPython json.dumps(x, separators=
 * (",", ":")) — insertion-order keys, default ensure_ascii=True escaping,
 * bytes -> base64, complex -> [re,im]).
 *
 * A type OUTSIDE bucket-(a) (Mat/Vec/HV/np.ndarray float carriers = rc190
 * (c); the by-reference handle / operator_name = later; any unknown) ->
 * srmech_mcp_marshal_arg returns SRMECH_ERR_NOT_IMPL and the caller DEFERS
 * to the pure Python coerce_param (rc103 inform-don't-limit). A JSON null
 * ALWAYS passes through (coerce_param's null-first rule) for any type.
 *
 * JPL-clean: caller-arena only (no malloc), depth-bounded recursion
 * (SRMECH_MVAL_MAX_DEPTH), no goto/abs/libm. ABI-additive (new symbols +
 * types, no wire change to an existing function) -> SRMECH_ABI_VERSION
 * stays 4. NO Python dispatch is wired THIS rc (foundation only — the
 * rc188 invoke_tool spine wires srmech_mcp.c tools/call to it).
 * ------------------------------------------------------------------ */

#define SRMECH_MVAL_MAX_DEPTH 6   /* bounded nesting (mirrors rc181 DV_MAX_DEPTH) */

/* Discriminant of the uniform marshalling value carrier. NONE/INT/FLOAT/
 * STR/LIST mirror the rc181 dv_value_t; BYTES (decoded byte buffer, base64
 * on the wire) + COMPLEX (re,im f64 pair, [re,im] on the wire) are the new
 * typed leaves; BOOL + DICT complete faithful JSON coverage (a bool arg, a
 * dict/object result, the Mapping[bytes,bytes] object family). */
typedef enum {
    SRMECH_MVAL_NONE = 0,   /* JSON null                                 */
    SRMECH_MVAL_BOOL,       /* JSON true / false  (i = 0/1)              */
    SRMECH_MVAL_INT,        /* int64  (i)                                */
    SRMECH_MVAL_FLOAT,      /* f64  (re)                                 */
    SRMECH_MVAL_STR,        /* UTF-8 string  (s, slen) — length-delimited */
    SRMECH_MVAL_BYTES,      /* decoded bytes  (b, blen) — base64 on wire */
    SRMECH_MVAL_COMPLEX,    /* (re, im) f64 pair — [re,im] on wire       */
    SRMECH_MVAL_LIST,       /* ordered children (items, n; is_tuple bit) */
    SRMECH_MVAL_DICT,       /* ordered key/value pairs (keys, items, n)  */
    SRMECH_MVAL_MAT,        /* rc190 real f64 Mat carrier — n=n_rows,     */
                            /* i=n_cols, b=row-major double buffer, blen= */
                            /* n_rows*n_cols doubles (is_tuple=0, real).  */
                            /* Matches coerce_param("Mat")=Mat.from_rows( */
                            /* is_complex=False); a genuine-complex Mat    */
                            /* rides the by-reference handle path.        */
    SRMECH_MVAL_BIGINT      /* rc335 (#948/#887) arbitrary-precision INT   */
                            /* carrier — a PRE-FORMATTED decimal string in */
                            /* (s, slen), REUSING those fields (NO struct- */
                            /* layout change). mm_serialise emits it       */
                            /* RAW/UNQUOTED (like an int64, not a string), */
                            /* so a bignum that OVERFLOWS int64 serialises */
                            /* BYTE-for-BYTE with json.dumps(int) / CPython */
                            /* str(int). The One.flat / One.scalar make_   */
                            /* class thunks build it via srmech_bigint_to_ */
                            /* dec (leading '-', "0" for zero, no leading  */
                            /* zeros). ABI-additive (a new enum value, no  */
                            /* wire change) -> SRMECH_ABI_VERSION stays 10. */
} srmech_mval_kind_t;

/* The uniform JSON-args<->typed-C-args value carrier. All pointer members
 * alias a caller arena (see srmech_marshal_arena_t). LIST/DICT hold up to
 * SRMECH_MVAL_MAX_DEPTH nesting. A DICT key node is a STR (an ordinary
 * object key) or a BYTES (a Mapping[bytes,bytes] base64 key). */
typedef struct srmech_mval srmech_mval_t;
struct srmech_mval {
    srmech_mval_kind_t   kind;
    int64_t              i;         /* INT value; BOOL 0/1                */
    double               re;        /* FLOAT value; COMPLEX real part     */
    double               im;        /* COMPLEX imaginary part             */
    const char          *s;         /* STR bytes (NOT NUL-guaranteed)     */
    uint32_t             slen;      /* STR length                         */
    const unsigned char *b;         /* BYTES buffer                       */
    uint32_t             blen;      /* BYTES length                       */
    srmech_mval_t      **items;     /* LIST children / DICT values        */
    srmech_mval_t      **keys;      /* DICT keys (n of them)              */
    uint32_t             n;         /* LIST / DICT length                 */
    int                  is_tuple;  /* LIST: 1 => tuple, 0 => list        */
};

/* Forward-only bump arena backing every carrier node + decoded byte buffer.
 * Caller stack-allocates it over a workspace, then hands it to the marshal
 * ops; a request that does not fit yields SRMECH_ERR_OVERFLOW. */
typedef struct { unsigned char *cur; unsigned char *end; } srmech_marshal_arena_t;

/* Initialise `a` over the workspace `ws` (length `ws_len`). */
void srmech_marshal_arena_init(srmech_marshal_arena_t *a,
                               void *ws, size_t ws_len);

/* STAGE 1 — mirror a parsed srmech_json value tree into a carrier tree
 * (null->NONE, bool->BOOL, int->INT, double->FLOAT, string->STR,
 * array->LIST(list), object->DICT with STR keys). Depth-bounded. NULL args
 * -> SRMECH_ERR_NULL_ARG; over-deep / arena-exhausted -> the matching
 * error; else *out is the root carrier. */
srmech_status_t srmech_mval_from_json(const srmech_json_value_t *j,
                                      srmech_marshal_arena_t *a,
                                      srmech_mval_t **out);

/* STAGE 2 — typed-lower one argument carrier `v` per the registry
 * `type_string`. Bucket-(a) CLEAN: identity (int/float/bool/str/number/
 * dict/list + Optional/nested/ChainSpec/callable/array-acc), bytes (base64
 * str -> BYTES), complex (number|[re,im] -> COMPLEX), tuple[int,int],
 * Sequence[bytes]/list[bytes], list[complex], list[list[complex]],
 * Mapping[bytes,bytes], list[tuple[bytes,int]], list[tuple[bytes,bytes]].
 * A JSON null passes through for ANY type. A type outside bucket-(a) ->
 * SRMECH_ERR_NOT_IMPL (the caller defers to the pure coerce_param) — this
 * INCLUDES pathlib.Path, whose str(Path) round-trip is OS-dependent ('/'
 * vs Windows '\\') and so NOT a portable data marshal; a malformed wire
 * value for the type (bad base64, a non-[re,im] complex) ->
 * SRMECH_ERR_BAD_INPUT. On SRMECH_OK *out is the typed carrier (it MAY
 * alias `v` for the identity families). */
srmech_status_t srmech_mcp_marshal_arg(const char *type_string,
                                       const srmech_mval_t *v,
                                       srmech_marshal_arena_t *a,
                                       srmech_mval_t **out);

/* OUTBOUND — serialise a (typed) carrier as canonical JSON into `buf`
 * (capacity `buf_len`; NO trailing NUL) and set *out_len. Two-pass:
 * `buf == NULL` is a SIZE-QUERY (nothing written; *out_len <- exact byte
 * count); a too-small non-NULL `buf` returns SRMECH_ERR_OVERFLOW (never
 * writes past the buffer). BYTE-IDENTICAL to CPython
 *   json.dumps(x, separators=(",", ":"))
 * and no other kwarg combination — insertion-order keys (NOT sorted; that is
 * srmech_json_write_ws's contract, not this one) and the DEFAULT
 * ensure_ascii=True and allow_nan=True: bytes -> base64 string, complex ->
 * [re,im], NONE -> null, BOOL -> true/false, tuple -> array; a MAT -> a nested
 * [[...]] float array (compact).
 *
 * FLOAT/COMPLEX/MAT doubles go through srmech_double_repr, the shortest
 * round-trip decimal. rc403 (`#T1071`) replaced that function's printf search
 * with an integer-only Ryu conversion; before rc403 it emitted the wrong digits
 * for 92 of the 4196 signed powers of two, so THIS surface shipped bytes that
 * were not json.dumps's at SRMECH_OK.
 *
 * NON-FINITE (rc403): emits CPython's own "NaN" / "Infinity" / "-Infinity",
 * which is what allow_nan=True produces, replacing the platform-spelled %.17g
 * fallback ("nan"/"inf" under glibc). This is the OPPOSITE call from
 * srmech_json_write_ws, which DECLINES a non-finite double — deliberately, and
 * for a reason specific to each: this surface's consumer is a CPython
 * json.loads, which accepts all three tokens, so the round trip closes; the
 * canonical writer's consumer is srmech_json_parse, which is strict RFC 8259
 * and does not. */
srmech_status_t srmech_mcp_serialise_result(const srmech_mval_t *v,
                                            char *buf, size_t buf_len,
                                            size_t *out_len);

/* Format a FINITE double exactly as CPython repr(float) / json.dumps(float) do:
 * the SHORTEST decimal that round-trips, rendered fixed OR scientific per
 * CPython's rule (scientific iff decpt <= -4 or decpt > 16), with the
 * integer-valued fixed form carrying a trailing ".0" (repr(5.0) == "5.0") and
 * the exponent padded to a MINIMUM of two digits ("5e-08", never "5e-8").
 * Writes a NUL-terminated string into `out` (cap >= 32) and sets *out_len
 * (length excluding the NUL). Returns SRMECH_OK; SRMECH_ERR_NULL_ARG for a
 * NULL / too-small buffer; SRMECH_ERR_BAD_INPUT for a non-finite v (NaN / Inf —
 * the caller decides the spelling, and the two callers decide differently; see
 * srmech_mcp_serialise_result and srmech_json_write_ws above).
 *
 * rc403 (`#T1071`) — WHAT CHANGED, AND A CORRECTION TO THIS PROSE. From rc190
 * to rc402 the implementation searched for the shortest snprintf("%.*e") that
 * strtod round-trips, and THIS COMMENT CALLED THAT "David Gay 'r' mode". It was
 * not. It is the shortest PRINTF-REACHABLE round-tripper: at an exact decimal
 * tie glibc rounds to-even, that candidate then fails round-trip, and the tie's
 * other neighbour — which does round-trip at the same length — was never
 * offered, so the search returned one digit too many. 92 of the 4196 signed
 * powers of two were wrong, including 2**-24 (emitted as the 17-digit
 * 5.9604644775390625e-08 where CPython gives 5.960464477539063e-08).
 *
 * It is now an integer-only, table-driven Ryu conversion (Ulf Adams, PLDI 2018)
 * in src/srmech_ryu.c. NO printf and NO strtod in the digit path, and no
 * floating-point arithmetic either — so the output depends on the input bits
 * alone and is identical on gcc / clang / MSVC and Linux / macOS / Windows by
 * construction, where "%.17g" was not (Windows spells 1e17 as `1e+017`).
 * Still libm-FREE. Gated by c/test/test_srmech_ryu_repr_rc403.c (in the ctest
 * foreach, all three OSes) and tests/test_ryu_double_repr_rc403.py. */
srmech_status_t srmech_double_repr(double v, char *out, size_t cap,
                                   size_t *out_len);

/* Workspace bytes srmech_mcp_marshal_roundtrip needs for a `value_len`-byte
 * argument JSON (parse tree + carrier tree + decoded buffers). */
size_t srmech_mcp_marshal_roundtrip_arena_bytes(size_t value_len);

/* FOUNDATION ROUND-TRIP PROVER (the rc187 DoD surface, JSON in / JSON out —
 * ctypes-drivable). Parse `value_json` (a single argument value, `value_len`
 * bytes) into the caller arena `ws` (length `ws_len`; size with
 * srmech_mcp_marshal_roundtrip_arena_bytes), STAGE-1 mirror it, STAGE-2
 * marshal_arg it per `type_string`, then serialise the typed carrier into
 * `out` (capacity `out_cap`; NO trailing NUL) and set *out_len. `out == NULL`
 * is NOT a size-query here (pass a real buffer). A non-bucket-(a) type ->
 * SRMECH_ERR_NOT_IMPL; a malformed value -> SRMECH_ERR_BAD_INPUT. This proves
 * marshal_arg -> serialise_result round-trips to the SAME canonical JSON as
 * the Python coerce_param -> serialise_native path. */
srmech_status_t srmech_mcp_marshal_roundtrip(const char *type_string,
                                             const char *value_json,
                                             size_t value_len,
                                             void *ws, size_t ws_len,
                                             char *out, size_t out_cap,
                                             size_t *out_len);

/* ------------------------------------------------------------------
 * MCP tools/call DISPATCH SPINE (0.9.0rc188; the HOST-GLUE invoke_tool that
 * makes MCP `tools/call` genuinely RUN in C). The C peer of the compute half
 * of srmech.mcp._tools.invoke_tool: registry_find (rc184) -> per-arg
 * srmech_mcp_marshal_arg (rc187) -> a SIGNATURE-SHAPE-batched thunk table
 * (tool name -> the bespoke C kernel) -> srmech_mcp_serialise_result (rc187).
 *
 * srmech_invoke_tool takes a dotted tool `name` + the tools/call `arguments`
 * OBJECT as JSON (`params_json[0..params_len)`) and, for a CLEAN BATCH of
 * c_dispatched tools, computes the result IN C and writes the result TEXT
 * (byte-identical to the pure `serialise_result(invoke_tool(name, args))` —
 * json.dumps(serialise_native(result)) with the json.dumps DEFAULT separators)
 * into `buf`, setting *out_kind = SRMECH_INVOKE_DISPATCHED. The still-wide
 * surface (383 tools with no single C kernel — nested / float-carrier / Mat /
 * handle / any tool NOT in the thunk table, an unregistered name, an extra
 * or malformed argument) sets *out_kind = SRMECH_INVOKE_DEFER (with *out_len
 * = 0) and the caller runs the pure Python invoke_tool + attests (rc103
 * inform-don't-limit — never a wrong answer).
 *
 * `ws` (length `ws_len`; size with srmech_invoke_tool_arena_bytes) is the
 * caller arena for the argument PARSE tree + the marshalled carrier tree +
 * decoded byte buffers + the result carrier. `buf` (capacity `buf_len`; NO
 * trailing NUL) receives the result text; a too-small `buf` returns
 * SRMECH_ERR_OVERFLOW (the caller then defers to pure). NULL `name` /
 * `params_json` / `ws` / `buf` / `out_len` / `out_kind` -> SRMECH_ERR_NULL_ARG.
 * JPL-clean (caller-arena, no malloc/goto/abs/libm, bounded). ABI-additive
 * (SRMECH_ABI_VERSION stays 4). */

/* srmech_invoke_tool out_kind: whether the C spine ran the tool. */
#define SRMECH_INVOKE_DISPATCHED 0  /* buf holds the result text (native==pure) */
#define SRMECH_INVOKE_DEFER      1  /* caller runs the pure invoke_tool + attest */

srmech_status_t srmech_invoke_tool(const char *name,
                                   const char *params_json, size_t params_len,
                                   void *ws, size_t ws_len,
                                   char *buf, size_t buf_len,
                                   size_t *out_len, int *out_kind);

/* The PARSED-args sibling — dispatch over an ALREADY-parsed `arguments` value
 * node (the in-process srmech_mcp.c tools/call path: no re-serialise / double
 * parse). `arguments` NULL or non-object -> SRMECH_INVOKE_DEFER. `ws` (length
 * `ws_len`) backs the marshalled carriers + result; same out_kind / buf / error
 * contract as srmech_invoke_tool. */
srmech_status_t srmech_invoke_tool_json(const char *name,
                                        const srmech_json_value_t *arguments,
                                        void *ws, size_t ws_len,
                                        char *buf, size_t buf_len,
                                        size_t *out_len, int *out_kind);

/* Workspace bytes srmech_invoke_tool needs for a `params_len`-byte argument
 * object (the parse tree + carrier tree + decoded byte buffers + result). */
size_t srmech_invoke_tool_arena_bytes(size_t params_len);

/* ------------------------------------------------------------------
 * PROGRESS / INTROSPECTION CALLBACK (0.9.0rc242, #840) — Class-H (self-
 * introspection) projected across the BARE-C HOST boundary.
 *
 * srmech's introspection stream (~/.srmech/run-*.ndjson) is otherwise written
 * ONLY by the Python srmech.introspect.Writer at Python op boundaries — the C
 * library itself emits nothing, so a no-Python host cannot observe which op ran.
 * This callback completes the everything-to-C surface: a host registers a
 * callback with srmech_set_progress_cb, and the central invoke spine
 * (srmech_invoke_tool / _json -> iv_dispatch) fires it ONCE per successfully-
 * dispatched tool (on the real materialisation pass; a NULL-buf size-query does
 * not emit) with a compact canonical-JSON event describing the op:
 *
 *   {"category": <category>, "mpr_version": "1.0", "op_name": <dotted name>}
 *
 * The event is built through srmech_json_write_ws (the keystone), so it is
 * BYTE-IDENTICAL to CPython
 *   json.dumps({"category": ..., "mpr_version": "1.0", "op_name": ...},
 *              sort_keys=True, ensure_ascii=False)
 * — the SAME shape (and ", " / ": " separators) the Python
 * srmech.introspect._event.serialize emits. A host may append the line straight
 * to its own NDJSON stream, enriching it with a timestamp / pid the way the
 * Python Writer does: the C library reports WHAT ran, not WHEN (the clock is the
 * host's), keeping the emit a pure function of the dispatch — deterministic,
 * byte-exact-testable, and libm/time-free.
 *
 * OFF BY DEFAULT: with no callback registered the emit path returns after a
 * single NULL-pointer test, so the hot dispatch path pays nothing.
 *
 * ABI v5 (this rc): the new srmech_progress_cb_t typedef carries a CFUNCTYPE
 * wire-format implication (the v2→v3 / v3→v4 callback-typedef precedent), so
 * ABI bumps; srmech_set_progress_cb itself is an additive symbol.
 * ------------------------------------------------------------------ */

/* Progress / introspection callback. The C library invokes it once per
 * successfully-dispatched tool with `event_json` (a NUL-terminated compact
 * canonical-JSON object, valid for the lifetime of the call only — copy it to
 * retain) and the opaque `user_data` registered alongside the callback. The
 * callback MUST be cheap and MUST NOT re-enter srmech_invoke_* (it fires inside
 * dispatch). */
typedef void (*srmech_progress_cb_t)(const char *event_json, void *user_data);

/* Register (or clear, `cb` == NULL) the PROCESS-GLOBAL progress callback and its
 * opaque `user_data`. Returns the PREVIOUS callback (NULL if none) so a host can
 * chain or restore. The observer is process-wide (mirroring the Python single-
 * global srmech.introspect writer); set it before spinning worker threads. */
srmech_progress_cb_t srmech_set_progress_cb(srmech_progress_cb_t cb,
                                            void *user_data);

/* ------------------------------------------------------------------
 * make_class OBJECT-MODEL ENGINE (0.9.0rc201; the make_class -> C arc, #887).
 * The C peer of the compute half of srmech.dsl._class_catalog.CatalogClass: a
 * bare-C host constructs a DSL [class] instance from its packaged TOML descriptor
 * + a field-state map and RUNS its declared methods natively (rc194-200 made all
 * 31 leaf ops C-realizable; this builds the descriptor->field-state->dispatch->
 * route ENGINE on top, with a leaf VTABLE that returns LIVE srmech_mval_t carriers
 * so the routes compose — distinct from the rc188 invoke_tool text vtable).
 *
 * srmech_make_class_run takes the [class] descriptor TOML (`class_toml`[0..
 * `toml_len`)), a `method` name, the instance FIELD-STATE as a JSON object
 * (`fields_json`[0..`fields_len`)), and the call ARGS as a JSON object
 * (`args_json`[0..`args_len`)); for a method in the rc201 PROVEN BATCH it runs
 * the method IN C and writes {"result": <value>, "fields": <post-self-state>} as
 * canonical JSON — it emits through srmech_mcp_serialise_result, so the exact
 * claim is byte-identity with
 *   json.dumps(serialise_native(...), separators=(",", ":"))
 * (insertion-order keys, default ensure_ascii=True). This line carried a BARE
 * `json.dumps(serialise_native(...))` until rc403, which names the DEFAULT
 * ", " / ": " separators — the opposite of what this surface emits — into `out`
 * (cap `out_cap`; NO trailing NUL), setting *out_len + *out_kind =
 * SRMECH_MAKE_CLASS_DISPATCHED. For a returns="self" method "result" is the NEW
 * instance's field-state DICT (self untouched).
 *
 * rc201 BATCH: One's 5 inline-constant accessors (dim/imag_dims/partition/
 * plane_counts/grammar_slots) + the sedenion ADDRESS-ALGEBRA methods
 * navmap/slots/is_navigable (plain) + navigate (returns="self"). Any OTHER method
 * — a chain, an appends/sets/mutates route, an op outside the batch (the One
 * bignum + genome byte/disk + sed HDC leaves = rc201b), an unknown method/class,
 * or an unparseable descriptor — sets *out_kind = SRMECH_MAKE_CLASS_DEFER and the
 * caller runs the COMPLETE pure CatalogClass (rc103 inform-don't-limit; never a
 * wrong answer). A user register_class_dir class DEFERS the same way (no host
 * op-resolver callback -> SRMECH_ABI_VERSION stays 4).
 *
 * JPL-clean: caller-arena only (no malloc), <=60-line functions, >=2 asserts, no
 * goto/abs/libm. Additive symbols -> SRMECH_ABI_VERSION stays 4.
 * ------------------------------------------------------------------ */

/* srmech_make_class_run out_kind: whether the C engine ran the method. */
#define SRMECH_MAKE_CLASS_DISPATCHED 0  /* out holds {"result",...} (native==pure) */
#define SRMECH_MAKE_CLASS_DEFER      1  /* caller runs the pure CatalogClass       */

/* Workspace bytes srmech_make_class_run needs for the given input sizes (the
 * TOML tree + two JSON trees + two mval trees + the result carriers). */
size_t srmech_make_class_run_arena_bytes(size_t toml_len, size_t fields_len,
                                         size_t args_len);

srmech_status_t srmech_make_class_run(const char *class_toml, size_t toml_len,
                                      const char *method,
                                      const char *fields_json, size_t fields_len,
                                      const char *args_json, size_t args_len,
                                      void *ws, size_t ws_len,
                                      char *out, size_t out_cap, size_t *out_len,
                                      int *out_kind);

/* ------------------------------------------------------------------
 * run_class_method — the STATELESS one-shot class-method run (0.9.0rc203; the
 * make_class -> C arc, #887; the FINAL owed_orchestration row). The C peer of
 * srmech.dsl._class_surface.run_class_method: it RESOLVES a class NAME to its
 * packaged [class] descriptor (the compiled-in srmech_class_registry_table — a
 * bare-C host needs NO Python + NO filesystem), runs one method through the
 * rc201 srmech_make_class_run engine, and WRAPS the result as
 * {"class": name, "method": method, "result": <value>, "fields": <post-state>}
 * (byte-identical to the pure run_class_method). Any name the registry does not
 * hold (a register_class_dir USER class) or any method the engine defers sets
 * *out_kind = SRMECH_MAKE_CLASS_DEFER and the caller runs the pure
 * run_class_method (rc103 inform-don't-limit; never a wrong answer).
 *
 * The NAME->DESCRIPTOR registry: the four shipped descriptors as a const DATA
 * table (GENERATED by c/tools/gen_class_registry.py into srmech_class_registry.c
 * — the rc184 tool-registry codegen model), resolved by srmech_class_descriptor_
 * lookup. Additive symbols -> SRMECH_ABI_VERSION stays 4. JPL-clean.
 * ------------------------------------------------------------------ */

/* A packaged DSL [class] descriptor: its NAME (the resolve key) + the UTF-8
 * descriptor bytes (LF, NUL-terminated; `toml_len` EXCLUDES the NUL). */
typedef struct {
    const char *name;
    const char *toml;
    size_t      toml_len;
} srmech_class_descriptor_t;

/* The compiled-in registry table + count (defined in the generated
 * srmech_class_registry.c). */
extern const srmech_class_descriptor_t srmech_class_registry_table[];
extern const size_t srmech_class_registry_len;

/* Resolve a class NAME to its packaged descriptor bytes; returns the UTF-8 TOML
 * (writing its length EXCLUDING the NUL to *out_len) or NULL for an unknown /
 * user class. `out_len` may be NULL. */
const char *srmech_class_descriptor_lookup(const char *name, size_t *out_len);

/* rc359 (`#T1009`) — ENUMERATE the compiled-in class registry: the peers of
 * srmech_carrier_registry_count / _get. srmech_class_descriptor_lookup resolves
 * a name the caller must already hold, so it cannot answer "what does C
 * actually carry?" — which is the question a parity ratchet has to ask. These
 * two let a caller walk the table and read every descriptor BODY, so a stale
 * .so (source regenerated, library not rebuilt) is DETECTABLE rather than
 * silently trusted. `_get` returns NULL for an out-of-range index.
 * Additive -> SRMECH_ABI_VERSION stays 10. */
size_t srmech_class_registry_count(void);
const srmech_class_descriptor_t *srmech_class_registry_get(size_t index);

/* Workspace bytes srmech_run_class_method needs for a given class + input sizes
 * (resolves `class_name`'s descriptor length internally; a safe over-bound for
 * an unknown name). */
size_t srmech_run_class_method_arena_bytes(const char *class_name,
                                           size_t fields_len, size_t args_len);

srmech_status_t srmech_run_class_method(const char *class_name,
                                        const char *method,
                                        const char *fields_json, size_t fields_len,
                                        const char *args_json, size_t args_len,
                                        void *ws, size_t ws_len,
                                        char *out, size_t out_cap, size_t *out_len,
                                        int *out_kind);

/* ------------------------------------------------------------------
 * CLI arg-grammar + dispatch (0.9.0rc193; the HOST-GLUE console-script
 * parser). The C peer of srmech.cli.main.{build_parser, main} + the five
 * subcommand srmech.cli.{status,bus,dsl,mcp,klass}.add_arguments — a bare-C
 * host (no Python) parses the `srmech` console-script grammar + routes each
 * subcommand to its (C) run body (bus → srmech_bus_*, dsl → srmech_dsl_chain_run,
 * mcp → srmech_mcp_*, class → the DSL class surface, status → host FS).
 *
 * GRAMMAR (mirrors build_parser + the five add_arguments EXACTLY):
 *   status                       [--pid INT] [-f/--follow] [--json] [--poll-interval FLOAT]
 *   bus {list,tap,pipe,send,serve}
 *     list                       [--json] [--all]
 *     tap NAME                    [--seed HEX] [--format {json,pretty}] [--filter TYPE] [--limit N]
 *     pipe SRC DST                [--seed-src HEX] [--seed-dst HEX] [--transform PY]
 *     send NAME [EVENT_JSON]      [--seed HEX] [--timeout FLOAT] [--stdin]
 *     serve NAME                  [--echo] [--seed HEX] [--seed-mint] [--handler-module M:f]
 *   dsl {run,ops,visualize}
 *     run CHAIN.toml              [--input J] [--input-file P] [--output-file P]
 *                                 [--ndjson-input] [--json]
 *     ops                         [--json]
 *     visualize CHAIN.toml        [--json]
 *   mcp {emit-mcpb}
 *     emit-mcpb                   [--out DIR] [--type {uv,python}] [--name N]
 *                                 [--manifest-only] [--filter GLOB]
 *   class {list,describe}
 *     list
 *     describe NAME
 *
 * BEHAVIOR-PARITY (NOT byte-identical help text — the documented split). For a
 * VALID subcommand invocation srmech_cli_parse emits the parsed argparse
 * namespace as canonical JSON (dest keys, defaults filled) into `out` and sets
 * *out_action = SRMECH_CLI_ACTION_RUN; the caller reconstructs the Namespace +
 * routes via srmech_cli_dispatch. -h/--help → SRMECH_CLI_ACTION_HELP (*out_exit
 * 0); --version → SRMECH_CLI_ACTION_VERSION (0); a structural error (unknown
 * subcommand, bad --choice, missing/extra positional, missing option value) →
 * SRMECH_CLI_ACTION_ERROR (*out_exit 2). A grammar the bounded parser will not
 * risk mis-handling (an option abbreviation, an inline `--`, an unusual numeric
 * token, a value that itself looks like an option) → SRMECH_ERR_NOT_IMPL so a
 * Python host DEFERS to pure argparse (inform-don't-limit; help/version/error
 * text stays byte-identical because pure argparse emits it). numeric option
 * tokens are validated: --pid/--limit lex as int64 (emitted as a JSON number);
 * --poll-interval/--timeout lex as a float token (emitted as a JSON string the
 * consumer float()s). Bounded: fixed subcommand table + fixed per-subcommand
 * option table (JPL Rule 2). No workspace arena needed (argv is parsed in place;
 * the canonical JSON is written straight to `out`).
 *
 * Returns:
 *   SRMECH_OK            — *out_action set (RUN/HELP/VERSION/ERROR); on RUN the
 *                          canonical JSON is `out[0..*out_len)`.
 *   SRMECH_ERR_NULL_ARG  — out / out_action / out_exit / out_len NULL, or argv
 *                          NULL with argc > 0.
 *   SRMECH_ERR_OVERFLOW  — the canonical JSON exceeds out_cap (*out_len holds the
 *                          needed length).
 *   SRMECH_ERR_NOT_IMPL  — the bounded parser defers this grammar to pure argparse.
 * ABI-additive: new symbols only, so SRMECH_ABI_VERSION stays 4. */
#define SRMECH_CLI_ACTION_RUN     0  /* valid invocation; `out` = namespace JSON  */
#define SRMECH_CLI_ACTION_HELP    1  /* -h/--help; defer to pure help (exit 0)     */
#define SRMECH_CLI_ACTION_VERSION 2  /* --version; defer to pure version (exit 0)  */
#define SRMECH_CLI_ACTION_ERROR   3  /* an argparse arg error (exit 2)             */

srmech_status_t srmech_cli_parse(int argc, const char *const *argv,
                                 char *out, size_t out_cap, size_t *out_len,
                                 int *out_action, int *out_exit);

/* Route a parsed CLI namespace (the canonical JSON srmech_cli_parse emitted on
 * ACTION_RUN) to its run-body target: read the top-level "command" and set
 * *out_route to the run body a bare-C main() invokes. A null / absent command
 * (a bare `srmech`) → SRMECH_CLI_ROUTE_HELP (print top help). The subcommand run
 * bodies are the composes_c cli.*.run over the already-C bus / dsl / mcp — this
 * is the ROUTING, not a re-run of them. Returns SRMECH_ERR_NULL_ARG on a NULL
 * arg, SRMECH_ERR_BAD_INPUT on JSON with no recognizable "command". */
#define SRMECH_CLI_ROUTE_STATUS 0
#define SRMECH_CLI_ROUTE_BUS    1
#define SRMECH_CLI_ROUTE_DSL    2
#define SRMECH_CLI_ROUTE_MCP    3
#define SRMECH_CLI_ROUTE_CLASS  4
#define SRMECH_CLI_ROUTE_HELP   5  /* command == null → print top help          */

srmech_status_t srmech_cli_dispatch(const char *parsed_json, size_t len,
                                    int *out_route);

/* ------------------------------------------------------------------
 * Op-provenance canonical record hasher (0.9.0rc117; the op-carrying
 * carrier, dives #718/#719) — the C peer of
 * srmech.introspect.op_provenance.op_provenance_hash.
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
 * SRMECH_ERR_BAD_INPUT. (The Python wrapper enforces the same rejection;
 * the mirror agrees on the domain, not just the values.)
 *
 * The REASON given here until rc403 was "C's %.17g double rendering is not
 * byte-identical to Python repr(float)" — true then, no longer true now that
 * srmech_json_write_ws rides the Ryu converter. The rejection STANDS anyway,
 * on the stronger of the two original grounds: `float.hex()` is exact and
 * `repr(float)` is merely shortest-round-trip, so the hex tag is the right
 * pre-image for a hash regardless of how well the decimal writer performs.
 * Keeping the rejection also keeps this op's domain independent of the
 * writer, which is what a self-hash should be.
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
 * Op-provenance VERDICT / RECORD / RE-VERIFY logic (0.9.0rc171; the
 * ORCHESTRATION→C spine, batch 1) — the C peers of the five
 * srmech.introspect.op_provenance verdict/carry ops, so a bare-C host (no
 * Python) builds + compares op-provenance records with no json.dumps.
 * Each COMPOSES the existing kernels: the srmech_json parser / canonical
 * writer / builder, srmech_sha256_hex (Class A), and
 * srmech_op_provenance_hash (the rc117 canonical chain hasher) — no new
 * parser, no new hash. The Python ops dispatch to these under HAS_NATIVE
 * (hasattr-guarded; a stale lib falls back to the COMPLETE pure path).
 *
 * All records are FLOAT-FREE canonical JSON (floats ride as
 * {"__float64__": "<hex>"} tags); a raw JSON float in any input is
 * REJECTED with SRMECH_ERR_BAD_INPUT (same rejection as
 * srmech_op_provenance_hash — the mirror agrees on the domain).
 *
 * ABI-additive: new symbols only, so SRMECH_ABI_VERSION stays 3.
 * ------------------------------------------------------------------ */

/* op_verdict: *out_equal = 1 ("EQUAL") iff the two records' rc117 canonical
 * chain hashes agree (recomputed, never the cached field), else 0 ("UNKNOWN")
 * — the honest one-sided verdict (never a false UNEQUAL). `ws` is scratch for
 * hashing each record (reused); size it with srmech_op_verdict_arena_bytes.
 * SRMECH_ERR_BAD_INPUT on a malformed record / a raw float. */
srmech_status_t srmech_op_verdict(const char *r1_json, size_t r1_len,
                                  const char *r2_json, size_t r2_len,
                                  void *ws, size_t ws_len, int *out_equal);
size_t srmech_op_verdict_arena_bytes(size_t r1_len, size_t r2_len);

/* family_verdict: *out_same = 1 ("SAME_TARGET") iff BOTH records carry a
 * "family" object with equal NON-EMPTY "target_id" AND equal "tower_kind"
 * (both-absent tower_kind counts as equal), else 0 ("UNKNOWN"). Composes the
 * srmech_json parser. Size `ws` with srmech_family_verdict_arena_bytes. */
srmech_status_t srmech_family_verdict(const char *r1_json, size_t r1_len,
                                      const char *r2_json, size_t r2_len,
                                      void *ws, size_t ws_len, int *out_same);
size_t srmech_family_verdict_arena_bytes(size_t r1_len, size_t r2_len);

/* op_carry: build the CARRIED-op provenance RECORD (the provenance face of
 * carry(); the numeric value is the runner's job) from the canonical inputs /
 * params / family / rung JSON. Hashes the inputs into input_sha256 (sorted-key
 * order), derives leaves_exact (no __float64__/__complex128__ tag), and
 * appends chain_sha256 (== srmech_op_provenance_hash of the chain-less image).
 * `family_json` is "null" or the family object JSON; `params_json` / `rung_json`
 * are canonical objects. Writes canonical record JSON into out_json (out_cap
 * bytes; *out_len set); a too-small out_json returns SRMECH_ERR_OVERFLOW.
 * Size `ws` (and out_cap) with srmech_op_carry_arena_bytes. */
srmech_status_t srmech_op_carry(const char *op, size_t op_len,
                                const char *inputs_json, size_t inputs_len,
                                const char *params_json, size_t params_len,
                                const char *family_json, size_t family_len,
                                const char *rung_json, size_t rung_len,
                                void *ws, size_t ws_len,
                                char *out_json, size_t out_cap,
                                size_t *out_len);
size_t srmech_op_carry_arena_bytes(size_t inputs_len, size_t params_len,
                                   size_t family_len, size_t rung_len);

/* lossy_projection_record: build the exact-in/exact-out LOSSY-PROJECTION
 * record (rc125) from the canonical inputs — family=null, params={}, rung={},
 * the given projection_kind string, the derived leaves_exact + chain hash.
 * Writes canonical record JSON into out_json. Size `ws` (and out_cap) with
 * srmech_lossy_projection_record_arena_bytes. */
srmech_status_t srmech_lossy_projection_record(
    const char *op, size_t op_len,
    const char *inputs_json, size_t inputs_len,
    const char *projection_kind, size_t pk_len,
    void *ws, size_t ws_len,
    char *out_json, size_t out_cap, size_t *out_len);
size_t srmech_lossy_projection_record_arena_bytes(size_t inputs_len);

/* op_reproject: the MPM re-verification — *out_ok = 1 iff the supplied
 * canonical inputs re-hash (sorted-key order) to the record's input_sha256
 * array element-for-element (and the counts match), else 0 (a provenance that
 * can't be re-verified, or different inputs). Composes the srmech_json parser
 * + srmech_sha256_hex. Size `ws` with srmech_op_reproject_arena_bytes. */
srmech_status_t srmech_op_reproject(const char *record_json, size_t record_len,
                                    const char *inputs_json, size_t inputs_len,
                                    void *ws, size_t ws_len, int *out_ok);
size_t srmech_op_reproject_arena_bytes(size_t record_len, size_t inputs_len);

/* ------------------------------------------------------------------
 * §41 genome persistence — the C mirror of srmech.biology.genome's
 * disk save / load / catalog / append / window. A genome directory is
 *
 *   <dir>/manifest.json   an MPRRecord (MPR v1) catalogue of the
 *                         chromosome set (leaf_dim, per-chromosome
 *                         cap_sha256 / leaf_count / byte_offset /
 *                         byte_len, body_sha256, coupling hash+hex).
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
 * GENOME_FORMAT_VERSION in srmech.biology.genome. */
/* v15 (§98/rc268, #1422 / F1246-F1247): the CHROMATIN ACCESS LAYER. An interior
 * SRMECH_GENOME_CHROMATIN_MARKER (0x48) cap carries a per-region ACCESSIBILITY state
 * inline — biology's epigenetic packaging gate ABOVE the coupled-turn content
 * (euchromatin = accessible / heterochromatin = silenced), the modify-WITHOUT-changing-
 * the-DNA layer. It is an INTERIOR cap (like the §95a centromere 0x58; it never OPENS a
 * chromosome) whose PLACEMENT is its scope: right after the opening telomere → whole-
 * chromosome (the X-inactivation / master case), deeper interior → a sub-region STRETCH.
 * A NEW marker byte = a new block KIND, so it bumps v14 -> v15 (the walker gains ONE
 * branch; v2..v14 bodies read UNCHANGED; a chromatin-FREE genome saved by the v15 writer
 * is byte-identical to v14 EXCEPT the format_version field, and reads all-euchromatin by
 * default). Mirrors GENOME_FORMAT_VERSION in srmech.biology.genome. */
/* v7 (§127/rc127, #726): the ACTIVE TELOMERE. A chromosome MAY open with a
 * SRMECH_GENOME_ACTIVE_TELOMERE_MARKER (0x74) cap carrying an exact non-negative
 * Hayflick COUNT inline (a descending replicative counter that srmech_genome_telomere_tick
 * reads to gate a divide — the op-carries-operand cap making the chromosome a genuine
 * op(x)operand). The 0x74 cap is one more self-describing kind in the SAME walk (first
 * byte keys it, label read UNIFORMLY up to the first NUL, count in the 8 bytes after
 * that NUL), so v2..v6 bodies read UNCHANGED (dual-read): back-compat is STRUCTURAL,
 * never a converter. A plain-telomere (no 0x74) genome saved by the v7 writer is
 * byte-identical to v6 EXCEPT the format_version field. Mirrors GENOME_FORMAT_VERSION
 * in srmech.biology.genome. */
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
 * field). Mirrors GENOME_FORMAT_VERSION in srmech.biology.genome. §v12 (O(1) genome-native
 * append): the on-disk manifest is HEAD-ONLY — the per-chromosome ``chromosomes`` /
 * ``regions`` arrays (a plaintext table-of-contents) are DROPPED from disk and DERIVED by
 * scanning the self-describing body on read, so ``srmech_genome_append`` rewrites only the
 * tiny head (O(1)) instead of the whole array (the O(N^2) wall). The BODY format is
 * UNCHANGED (v2..v11 bodies read identically); a v≤11 manifest with the arrays reads
 * verbatim, and the first v12 append migrates it head-only. Mirrors GENOME_FORMAT_VERSION.
 * §v16 (§55/§Q8/rc312, the Q₈ on-disk migration): the wire gains a SECOND data-turn packing
 * — a Q₈ (element_type=q8) data turn 3-bit-packs under SRMECH_GENOME_Q8_PACKED_TURN_MARKER
 * (0x38) instead of the klein4 2-bit SRMECH_GENOME_PACKED_TURN_MARKER (0x51) — plus a manifest
 * "carrier" field naming the element type ("klein4"/"q8"). klein4 keeps its 2-bit packer, so a
 * klein4 body is BYTE-IDENTICAL to v15 (only the manifest format_version + carrier move); a v15
 * klein4 turn (bytes 0..3, sign bit 0) is the winding-0 slice of a v16 Q₈ turn. One more
 * self-describing marker in the SAME walk, so v2..v15 bodies read UNCHANGED. A v16 writer
 * stamps 16. Mirrors GENOME_FORMAT_VERSION.
 *
 * v16->v17 (rc322, §Q8-FIBER, F-HOLO-MISLOCATED): adds the TOPOLOGY / FIBER cap marker
 * SRMECH_GENOME_FIBER_CAP_MARKER (0x46) — an INTERIOR cap holding the strand's ORDERED
 * accumulated Q8 holonomy (the fiber / gauge the winding-invariant per-turn store cannot
 * carry). A body with NO 0x46 cap is BYTE-IDENTICAL to v16 (klein4/Q8 turns pack
 * unchanged); only the manifest format_version moves. The fiber cap is OPT-IN (genome_add_
 * fiber), so a default save is winding-INVARIANT base bytes exactly as before. A v17 writer
 * stamps 17; v2..v16 bodies read UNCHANGED (one more self-describing cap in the SAME walk).
 *
 * v17->v18 (rc325, §𝕆-FIBER): adds the 𝕆 (octonion) analog of the v17 ℍ (Q8) fiber cap —
 * the TOPOLOGY / FIBER cap marker SRMECH_GENOME_OCT_FIBER_CAP_MARKER (0x4F) holding the
 * strand's ORDERED accumulated OCTONION holonomy (the fiber the winding-invariant per-turn
 * octonion store cannot carry), ONE Cayley-Dickson rung up from the Q8 fiber. A body with NO
 * 0x4F cap is BYTE-IDENTICAL to v17 (klein4/Q8/octonion turns pack unchanged); only the
 * manifest format_version moves. The octonion fiber cap is OPT-IN (genome_add_octonion_fiber),
 * so a default save is base bytes exactly as before. A v18 writer stamps 18; v2..v17 bodies
 * read UNCHANGED (one more self-describing cap in the SAME walk).
 *
 * v18->v19 (rc326, §𝕆-TURN): the on-disk WIRE gains a THIRD data-turn packing — an octonion
 * (element_type=octonion) DATA turn 4-bit-packs under SRMECH_GENOME_OCTONION_PACKED_TURN_MARKER
 * (0x39) instead of the klein4 2-bit 0x51 or the Q8 3-bit 0x38 — plus the manifest "carrier"
 * field gains the "octonion" value. rc324 shipped the 𝕆 carrier + 4-bit codec and rc325 the 𝕆
 * fiber CAP, but the on-disk wire still packed only klein4/Q8 DATA turns; v19 closes that gap so
 * an octonion turn (INCLUDING the non-quaternionic indices 4..7) persists to turns.bin and
 * round-trips through a genome file. A body with NO 0x39 turn is BYTE-IDENTICAL to v18
 * (klein4/Q8 turns pack unchanged); only the manifest format_version moves. A v19 writer stamps
 * 19; v2..v18 bodies read UNCHANGED (one more self-describing marker in the SAME walk). The
 * mirror of the v15->v16 Q8 on-disk migration, ONE Cayley-Dickson rung up. */
#define SRMECH_GENOME_FORMAT_VERSION 19

/* §44 inline cap markers — the FIRST byte of a fixed-width cap leaf. Both are
 * > 3 so a cap is told apart from a Klein-4 data turn (bytes 0..3) by its
 * first byte alone; the label follows, NUL-padded to leaf_dim. Mirror
 * CHROM_CAP_MARKER / GENE_CAP_MARKER in srmech.biology.genome. */
#define SRMECH_GENOME_CHROM_CAP_MARKER 0x43u   /* 'C' — opens a chromosome */
#define SRMECH_GENOME_GENE_CAP_MARKER  0x47u   /* 'G' — opens a gene */

/* §55/v3 bit-packed data-turn marker — the FIRST byte of a packed turn block
 * ([marker] + ceil(leaf_dim/4) payload bytes; symbol i lives in payload byte
 * i/4 at bit shift 6 - 2*(i%4), first symbol in the HIGH lanes; a partial
 * final byte's unused low lanes are zero). > 3 and distinct from both cap
 * markers, so the strand stays self-describing. Mirrors PACKED_TURN_MARKER
 * in srmech.biology.genome. */
#define SRMECH_GENOME_PACKED_TURN_MARKER 0x51u /* 'Q' — a quad-packed turn */

/* §55/§Q8/v16 (rc312) 3-BIT Q₈ packed data-turn marker — the FIRST byte of a Q₈
 * packed turn block ([marker] + ceil(leaf_dim*3/8) payload bytes). MSB-FIRST
 * CONTIGUOUS: symbol i occupies bits [3i, 3i+3) of a big-endian bitstream (symbol 0
 * in the highest bits, the sign/high bit of each 3-bit symbol first); the unused LOW
 * bits of a partial final byte are zero (canonical). > 3 and distinct from the 2-bit
 * PACKED marker (0x51) and every cap marker, so a block's first byte keys BOTH its
 * kind and its width — a v16 body is walked in the SAME self-describing scan as a v3
 * klein4 body, klein4 turns keep 0x51 and Q₈ turns use this. Mirrors
 * Q8_PACKED_TURN_MARKER in srmech.biology.genome. */
#define SRMECH_GENOME_Q8_PACKED_TURN_MARKER 0x38u /* '8' — a 3-bit Q₈ octet turn */

/* §55/§𝕆-TURN/v19 (rc326) 4-BIT octonion packed data-turn marker — the FIRST byte of an
 * octonion packed turn block ([marker] + ceil(leaf_dim*4/8) = ceil(leaf_dim/2) payload bytes,
 * two 4-bit symbols per byte). MSB-FIRST CONTIGUOUS: symbol i occupies bits [4i, 4i+4) of a
 * big-endian bitstream (symbol 0 in the high nibble of payload byte 0, each symbol's high bit
 * first); the unused LOW bits of a partial final byte are zero (canonical). > 3 and distinct
 * from the 2-bit PACKED marker (0x51), the 3-bit Q8 marker (0x38), and every cap marker, so a
 * block's first byte keys BOTH its kind and its width — a v19 body is walked in the SAME
 * self-describing scan as a v3/v16 body: klein4 turns keep 0x51, Q8 turns use 0x38, octonion
 * turns use this. Mirrors OCTONION_PACKED_TURN_MARKER in srmech.biology.genome. */
#define SRMECH_GENOME_OCTONION_PACKED_TURN_MARKER 0x39u /* '9' — a 4-bit octonion turn */

/* §60/v5 SIZE-AGNOSTIC KERNEL HEADER marker — the FIRST byte of a fixed-width
 * leaf_dim-byte inline block written by kernel_pack right after a kernel
 * chromosome's telomere. It self-records the kernel's TRUE length D (bytes [1:9],
 * uint64 big-endian), leaf_dim (bytes [9:13], uint32 big-endian) and element_type
 * (byte [13], uint8 enum; 0 = klein4). > 3 and distinct from every other marker,
 * so the strand stays self-describing; stored VERBATIM (never bit-packed) and NOT
 * counted as a data turn. Mirrors KERNEL_HEADER_MARKER in srmech.biology.genome.
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
 * walker gains ONE branch. Mirrors KERNEL_TELOMERE_MARKER in srmech.biology.genome. */
#define SRMECH_GENOME_KERNEL_TELOMERE_MARKER 0x6Bu /* 'k' — a §89 kernel telomere */

/* §127/v7 ACTIVE TELOMERE marker (rc127, #726) — the FIRST byte of a fixed-width
 * leaf_dim-byte cap leaf that opens a chromosome (like the CHROM cap) AND carries an
 * exact non-negative COUNT inline. Layout: [0x74] + utf-8 label + NUL + count (uint64
 * big-endian) + NUL-pad to leaf_dim. The label decode is UNIFORM (bytes [1:] up to the
 * first NUL — the same as every cap); the count is read at the 8 bytes RIGHT AFTER that
 * NUL. > 3 and distinct from every other marker (CHROM 0x43 / GENE 0x47 / v5 KERNEL 0x4B
 * / PACKED 0x51 / KERNEL-telomere 0x6B), so v2..v6 bodies read UNCHANGED — the walker
 * gains ONE branch. Mirrors ACTIVE_TELOMERE_MARKER in srmech.biology.genome. */
#define SRMECH_GENOME_ACTIVE_TELOMERE_MARKER 0x74u /* 't' — a §127 active telomere */

/* §127/v7 active-telomere COUNT field width — a uint64 (8 bytes, big-endian), read at
 * the byte right after the inline label's NUL terminator. Mirrors
 * _ACTIVE_TELOMERE_COUNT_BYTES in srmech.biology.genome. */
#define SRMECH_GENOME_ACTIVE_TELOMERE_COUNT_BYTES 8u

/* §135/rc273 gene COPY-NUMBER field width — a uint64 (8 bytes, big-endian) carried in what
 * was a PLAIN GENE cap's (0x47) NUL padding, at the bytes RIGHT AFTER the inline label's NUL
 * terminator (the SAME placement discipline as the §127 active-telomere count and the §129
 * regulatory masks, so the label decode stays UNIFORM). A stored 0 — the all-NUL padding a
 * plain / pre-rc273 gene carries — reads as copy-number 1 (present-once, the DEFAULT), and a
 * copy-number of 1 is written as the plain cap, so an n == 1 amplify is BYTE-IDENTICAL to a
 * plain gene and no wire change is spent. Additive field in EXISTING padding, not a new
 * marker or block kind: SRMECH_GENOME_FORMAT_VERSION stays 15. Mirrors
 * _GENE_COPY_NUMBER_BYTES in srmech.biology.genome. */
#define SRMECH_GENOME_GENE_COPY_NUMBER_BYTES 8u

/* §128/v8 REGULATORY GENE marker (rc128, #728) — the FIRST byte of a fixed-width
 * leaf_dim-byte cap leaf that opens an INTRA-chromosome gene (like the plain GENE cap) AND
 * carries an exact non-negative regulatory MASK inline. Layout: [0x67] + utf-8 label + NUL +
 * mask (uint64 big-endian) + NUL-pad to leaf_dim (the SAME field shape as the §127 active
 * telomere, mask replacing count). The label decode is UNIFORM (bytes [1:] up to the first
 * NUL — the same as every cap); the mask is read at the 8 bytes RIGHT AFTER that NUL. > 3 and
 * distinct from every other marker (CHROM 0x43 / GENE 0x47 / v5 KERNEL 0x4B / PACKED 0x51 /
 * KERNEL-telomere 0x6B / ACTIVE-telomere 0x74), so v2..v7 bodies read UNCHANGED — the walker
 * gains ONE branch. srmech_genome_gene_express reads the mask to gate expression under a
 * cell_state. Mirrors REGULATORY_GENE_MARKER in srmech.biology.genome. */
#define SRMECH_GENOME_REGULATORY_GENE_MARKER 0x67u /* 'g' — a §128 regulatory gene */

/* §128/v8 regulatory-gene MASK field width — a uint64 (8 bytes, big-endian), read at the byte
 * right after the inline label's NUL terminator (the SAME field shape as the §127 active
 * telomere's count). §129 (#729): a regulatory gene carries TWO consecutive such fields — the
 * KLEIN-4 bit-planes (activator then repressor); rc128's single-mask cap is dual-read as
 * activator=mask, repressor=0 (the repressor plane occupies what was NUL padding). Mirrors
 * _REGULATORY_GENE_MASK_BYTES in srmech.biology.genome. */
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
 * under a cell_state. Mirrors BOOLEAN_GENE_MARKER in srmech.biology.genome. */
#define SRMECH_GENOME_BOOLEAN_GENE_MARKER 0x62u /* 'b' — a §130 boolean gene */

/* §130/v9 REGULATORY GATE-TYPE enum (rc130, #730). A regulatory gene declares a gate_type;
 * srmech_genome_gene_express dispatches on it. KLEIN4_MASK (0) = the §129 activator/repressor
 * two-mask (the fast common case, carried by a 0x47/0x67 cap); BOOLEAN_DNF (1) = the §130 DNF
 * (the general case, carried by a 0x62 cap). The gate_type is IMPLIED by the cap marker AND —
 * for a 0x62 gene — stored EXPLICITLY as a uint8 in the cap so the bare strand self-describes it
 * and the family stays extensible. Mirrors GATE_TYPE_* in srmech.biology.genome. */
#define SRMECH_GENOME_GATE_TYPE_KLEIN4_MASK 0u
#define SRMECH_GENOME_GATE_TYPE_BOOLEAN_DNF 1u

/* §130/v9 BOOLEAN GENE DNF wire widths (rc130, #730). The DNF term COUNT is a uint16 big-endian
 * (2 bytes). Each DNF TERM is TWO consecutive uint64 big-endian masks — the (activator,
 * repressor) AND-clause (16 bytes), the SAME (require-present, require-absent) pair the §129
 * klein4-mask carries as its ONE clause. Mirror _BOOLEAN_GENE_* in srmech.biology.genome. */
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
 * THRESHOLD_GENE_MARKER in srmech.biology.genome. */
#define SRMECH_GENOME_THRESHOLD_GENE_MARKER 0x77u /* 'w' — a §131 threshold gene */

/* §131/v10 REGULATORY GATE-TYPE enum extension (rc131, #731). THRESHOLD (2) = the §131 linear-
 * threshold / perceptron gate (a SIGNED integer weight vector + a threshold, carried by a 0x77
 * cap); srmech_genome_gene_express dispatches on the cap marker. Mirrors GATE_TYPE_THRESHOLD in
 * srmech.biology.genome. */
#define SRMECH_GENOME_GATE_TYPE_THRESHOLD 2u

/* §131/v10 THRESHOLD GENE wire widths (rc131, #731). The weight-vector LENGTH is a uint16
 * big-endian (2 bytes; weight i gates condition bit i of the cell_state). The THRESHOLD and each
 * WEIGHT are int64 big-endian SIGNED two's-complement (8 bytes each; SIGNED so an inhibitory /
 * repressive input is a NEGATIVE weight). Mirror _THRESHOLD_GENE_* in srmech.biology.genome. */
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
 * GRADED_GENE_MARKER in srmech.biology.genome. */
#define SRMECH_GENOME_GRADED_GENE_MARKER 0x64u /* 'd' — a §132 graded (dose) gene */

/* §132/v11 GRADED GATE-TYPE (rc132, #732). GRADED (3) = the §132 analog dose-response LEVEL axis
 * (a SIGNED integer level-weight vector + a POSITIVE denominator, carried by a 0x64 cap). NOT a
 * binary gate-type in the E1/E2/E4 IF-family — the ORTHOGONAL HOW-MUCH axis; the gate_type is
 * stored in the cap for self-description / extensibility. Mirrors GATE_TYPE_GRADED in
 * srmech.biology.genome. */
#define SRMECH_GENOME_GATE_TYPE_GRADED 3u

/* §132/v11 GRADED GENE wire widths (rc132, #732). The level-weight-vector LENGTH is a uint16
 * big-endian (2 bytes; weight i doses condition bit i). The DENOMINATOR is a uint64 big-endian
 * POSITIVE integer (8 bytes; the full-expression dose — a divisor is never negative, so UNSIGNED,
 * never abs). Each LEVEL-WEIGHT is int64 big-endian SIGNED two's-complement (8 bytes; SIGNED so an
 * inhibitory input REDUCES the dose). Mirror _GRADED_GENE_* in srmech.biology.genome. */
#define SRMECH_GENOME_GRADED_NWEIGHTS_BYTES 2u
#define SRMECH_GENOME_GRADED_DENOM_BYTES 8u
#define SRMECH_GENOME_GRADED_WEIGHT_BYTES 8u

/* §95a/v13 CENTROMERE marker (rc262, #1407 / F1243) — the FIRST byte of a fixed-width
 * leaf_dim-byte cap leaf that sits INTERIOR to a NUCLEAR chromosome (between its two arms),
 * NOT a chromosome-boundary cap. It carries the chromosome's GLOBAL 4-way orientation as an
 * α-satellite REPEAT-ARRAY. Layout: [0x58] + utf-8 handle + NUL + R (uint8) + R orientation
 * votes (each a byte in {0,1,2,3}) + NUL-pad to leaf_dim. The handle decode is UNIFORM (bytes
 * [1:] up to the first NUL — the same as every cap); R + votes are read AFTER that NUL. > 3
 * and distinct from every other marker (CHROM 0x43 / GENE 0x47 / v5 KERNEL 0x4B / PACKED 0x51
 * / KERNEL-telomere 0x6B / ACTIVE-telomere 0x74 / regulatory 0x67 / boolean 0x62 / threshold
 * 0x77 / graded 0x64), so v2..v12 bodies read UNCHANGED — the walker gains ONE branch (it is
 * an interior cap, so genome_cap_kind recognises it and every cap-skip walk flattens past it;
 * it is NOT a chromosome-opening boundary). Mirrors CENTROMERE_CAP_MARKER in
 * srmech.biology.genome. 0x58 = 'X' — the centromere is the cross-point of the X-shaped
 * chromosome. */
#define SRMECH_GENOME_CENTROMERE_CAP_MARKER 0x58u /* 'X' — a §95a interior centromere */

/* §95a/v13 default centromere α-satellite repeat-array size R (rc262). Mirrors
 * CENTROMERE_DEFAULT_REPEATS in srmech.biology.genome. */
#define SRMECH_GENOME_CENTROMERE_DEFAULT_REPEATS 15u

/* §95b/v14 DIPLOID chromosome-boundary marker (rc262, #1407 / F1244) — the FIRST byte of a
 * fixed-width leaf_dim-byte cap that OPENS a chromosome (like the CHROM cap, but flags it as
 * DIPLOID: its two arms, split by an interior SRMECH_GENOME_CENTROMERE_CAP_MARKER, are
 * HOMOLOGOUS FULL COPIES of the content — [diploid_telomere, copyA…, centromere(mark), copyB…],
 * copyA == copyB). The erasure/break specialist: srmech_genome_recover_diploid fills an erased
 * leaf from the intact homolog (2× not 3×), the centromere orientation is the which-template
 * mark (2 copies + 1 mark = 3 = k=3). > 3 and distinct from every prior marker, so v2..v13
 * bodies read UNCHANGED — the walker gains ONE branch (it OPENS a chromosome everywhere CHROM
 * does). Mirrors DIPLOID_TELOMERE_MARKER in srmech.biology.genome. 0x44 = 'D' (Diploid). */
#define SRMECH_GENOME_DIPLOID_TELOMERE_MARKER 0x44u /* 'D' — a §95b diploid chromosome */

/* §98/v15 CHROMATIN marker (rc268, #1422 / F1246-F1247) — the FIRST byte of a fixed-width
 * leaf_dim-byte cap leaf that sits INTERIOR to a chromosome (like the §95a centromere 0x58;
 * it NEVER opens a chromosome), carrying a per-region ACCESSIBILITY state inline: biology's
 * epigenetic packaging gate ABOVE the coupled-turn content (euchromatin = accessible /
 * heterochromatin = silenced). Layout: [0x48] + utf-8 handle + NUL + chromatin_type(uint8) +
 * num(uint64 BE) + den(uint64 BE POSITIVE), NUL-padded to leaf_dim. The handle decode is
 * UNIFORM (bytes [1:] up to the first NUL — the same as every cap); the type + num + den sit
 * AFTER that NUL (the §127 active-telomere inline-field pattern). The accessibility LEVEL is
 * the exact reduced rational num/den in [0, 1] (Class-N; NO float; NEVER abs — a level is a
 * non-negative fraction): BINARY (type 0) carries (1,1) OPEN or (0,1) CONDENSED; GRADED
 * (type 1) an arbitrary reduced rational. PLACEMENT is scope: at a region HEAD (right after
 * the opening telomere, 0 data turns before it) → whole-chromosome; deeper INTERIOR → a
 * sub-region STRETCH. > 3 and distinct from every prior marker (CHROM 0x43 / GENE 0x47 / v5
 * KERNEL 0x4B / PACKED 0x51 / KERNEL-telomere 0x6B / ACTIVE-telomere 0x74 / regulatory 0x67 /
 * boolean 0x62 / threshold 0x77 / graded 0x64 / centromere 0x58 / diploid 0x44), so v2..v14
 * bodies read UNCHANGED — genome_cap_kind recognises it as an interior cap and every cap-skip
 * walk flattens past it (it is NOT a data turn, NOT a chromosome-opener). Mirrors
 * CHROMATIN_MARKER in srmech.biology.genome. 0x48 = 'H' — histone / heterochromatin. */
#define SRMECH_GENOME_CHROMATIN_MARKER 0x48u /* 'H' — a §98 interior chromatin cap */

/* §Q8-FIBER/v17 FIBER (topology/gauge) cap marker (rc322, F-HOLO-MISLOCATED) — the FIRST
 * byte of a fixed-width leaf holding the strand's ORDERED accumulated Q8 holonomy (the
 * fiber / gauge). Layout (the §127 active-telomere inline-field pattern): [0x46] + utf-8
 * label + NUL, then n_holo (uint16 big-endian, the holonomy length in Q8 symbols == leaf_dim)
 * right after the label NUL, then ceil(n_holo*3/8) bytes of the 3-bit-packed Q8 holonomy
 * (the SAME MSB-first packing as a Q8 data turn payload), NUL-padded to leaf_dim. Like the
 * §95a centromere / §98 chromatin caps it is an INTERIOR cap (genome_cap_kind recognises it,
 * every cap-skip walk flattens past it — it is NOT a data turn, NOT a chromosome-opener), so
 * a codon / sequence read is byte-IDENTICAL with or without it (the fiber is OPT-IN). > 3 and
 * distinct from every prior marker (CHROM 0x43 / diploid 0x44 / GENE 0x47 / chromatin 0x48 /
 * Q8-turn 0x38 / KERNEL 0x4B / PACKED 0x51 / KERNEL-telomere 0x6B / ACTIVE 0x74 / regulatory
 * 0x67 / boolean 0x62 / threshold 0x77 / graded 0x64 / centromere 0x58), so v2..v16 bodies
 * read UNCHANGED. Mirrors FIBER_CAP_MARKER in srmech.biology.genome. 0x46 = 'F' — Fiber. */
#define SRMECH_GENOME_FIBER_CAP_MARKER 0x46u /* 'F' — a §Q8-FIBER interior fiber/gauge cap */

/* §𝕆-FIBER/v18 OCTONION FIBER (topology/gauge) cap marker (rc325) — the 𝕆 analog of the
 * v17 Q8 fiber cap, ONE Cayley-Dickson rung up. The FIRST byte of a fixed-width leaf holding
 * the strand's ORDERED accumulated OCTONION holonomy (the non-associativity-carrying fiber).
 * Layout (the §127 active-telomere inline-field pattern): [0x4F] + utf-8 label + NUL, then
 * n_holo (uint16 big-endian, the holonomy length in octonion symbols == leaf_dim) right after
 * the label NUL, then ceil(n_holo*4/8) = ceil(n_holo/2) bytes of the 4-bit-packed octonion
 * holonomy (the SAME MSB-first packing as an octonion data turn payload), NUL-padded to
 * leaf_dim. Like the §95a centromere / §98 chromatin / §Q8-FIBER caps it is an INTERIOR cap
 * (genome_cap_kind recognises it, every cap-skip walk flattens past it — NOT a data turn, NOT
 * a chromosome-opener), so a codon / sequence read is byte-IDENTICAL with or without it (the
 * fiber is OPT-IN). > 3 and distinct from every prior marker (CHROM 0x43 / diploid 0x44 / GENE
 * 0x47 / chromatin 0x48 / Q8-turn 0x38 / octonion-turn 0x39 / KERNEL 0x4B / Q8-fiber 0x46 /
 * PACKED 0x51 / KERNEL-telomere 0x6B / ACTIVE 0x74 / regulatory 0x67 / boolean 0x62 / threshold
 * 0x77 / graded 0x64 / centromere 0x58), so v2..v17 bodies read UNCHANGED. Mirrors
 * OCT_FIBER_CAP_MARKER in srmech.biology.genome. 0x4F = 'O' — Octonion fiber. */
#define SRMECH_GENOME_OCT_FIBER_CAP_MARKER 0x4Fu /* 'O' — a §𝕆-FIBER interior octonion fiber cap */

/* §98/v15 chromatin TYPE enum (rc268). BINARY (0) = open (1,1) / condensed (0,1); GRADED (1) =
 * an arbitrary reduced-rational accessibility level in [0,1]. Single-line #defines (JPL Rule 8). */
#define SRMECH_GENOME_CHROMATIN_TYPE_BINARY 0u
#define SRMECH_GENOME_CHROMATIN_TYPE_GRADED 1u

/* §98/v15 chromatin LEVEL field width — the num + den are each a uint64 (8 bytes, big-endian),
 * read at the two 8-byte fields right after the chromatin_type byte. Mirrors
 * _CHROMATIN_LEVEL_BYTES in srmech.biology.genome. */
#define SRMECH_GENOME_CHROMATIN_LEVEL_BYTES 8u

/* §98.1/v15 (§98.1/G1 / rc274) chromatin ACCESS-GATE type — an additive uint8 field in the cap's
 * existing NUL padding RIGHT AFTER den (the same dual-read discipline as the §129 repressor / §135
 * copy-number: pre-rc274 NUL padding reads back as NONE). It makes the 0x48 access layer CELL-
 * STATE-CONDITIONAL (facultative heterochromatin — Barr body / X-inactivation): NONE (0) =
 * CONSTITUTIVE (accessibility is the STATIC stored num/den, constant in cell_state — the pre-rc274
 * read); KLEIN4/BOOLEAN/THRESHOLD (1/2/3) = FACULTATIVE — the stored num/den is the WHEN-OPEN level,
 * returned iff the gate FIRES under cell_state (the SAME §129/§130/§131 gene-gate evaluators applied
 * to the chromatin cap), else (0,1) (silenced). Same 0x48 marker → no new marker / block kind, so
 * SRMECH_GENOME_FORMAT_VERSION STAYS 15 and a constitutive cap is BYTE-IDENTICAL to a v15 cap.
 * Single-line #defines (JPL Rule 8). Mirrors CHROMATIN_GATE_* in srmech.biology.genome. */
#define SRMECH_GENOME_CHROMATIN_GATE_NONE 0u
#define SRMECH_GENOME_CHROMATIN_GATE_KLEIN4 1u
#define SRMECH_GENOME_CHROMATIN_GATE_BOOLEAN 2u
#define SRMECH_GENOME_CHROMATIN_GATE_THRESHOLD 3u

/* Max label byte length (NUL-terminated) for one chromosome. This is a FORMAT
 * width (a label lives inline in a leaf_dim-byte cap block, like PATH_MAX), NOT
 * a count cap — the number of chromosomes is bounded only by the caller arena. */
#define SRMECH_GENOME_MAX_LABEL 256

/* §44/F708 one dense block ("tome") = 256 = 2**8 (one byte of address). The
 * encode-shape leaf capacity; mirrors LEAF_CAP in srmech.biology.genome. */
#define SRMECH_GENOME_LEAF_CAP 256u

/* rc196 (#887) make_class → C leaf-batch 2 (the genome CAP FOUNDATION). The two
 * smallest in-memory leaf ops of the genome [class] descriptor get their C peers
 * so a bare-C host (and the rc201 object-model engine) runs them natively; the
 * shared cap byte-TLV pack / kind / unpack helpers they rest on are the reusable
 * foundation rc197 (chromosome/recall) + rc198 (genome/partition) build on.
 * Additive symbols only → SRMECH_ABI_VERSION stays 4. */

/* ENCODE_SHAPE — the pure-INTEGER genome shape planner (Class-I/N, no float). For
 * a kernel of `n` elements it computes:
 *   leaves = ceil(n / SRMECH_GENOME_LEAF_CAP)        (dense blocks; overflow-safe)
 *   depth  = ceil(log4(leaves))                      (base-4 quad levels)
 * BYTE-IDENTICAL to srmech.biology.genome.encode_shape (which maps depth → shape
 * "tome"/"mobius"/"quad_strand" and assembles the dict — that trivial labeling
 * stays in the caller; the arithmetic is here). No arena, malloc-free, no abs.
 *   n          : the kernel size (> 0). Fits a uint64; the Python wrapper routes
 *                n == 0 / n >= 2**64 to the pure path (byte-identical).
 *   leaves_out : out — ceil(n / 256) dense blocks (>= 1).
 *   depth_out  : out — ceil(log4(leaves)) (0 → tome, 1 → mobius, >= 2 → strand).
 * Error returns:
 *   SRMECH_ERR_NULL_ARG  — leaves_out or depth_out is NULL.
 *   SRMECH_ERR_BAD_INPUT  — n == 0 (a size is a positive int). */
srmech_status_t srmech_genome_encode_shape(
    uint64_t n, uint64_t *leaves_out, uint32_t *depth_out);

/* TELOMERE — the chromosome boundary cap WRITER: a fixed-width `dim`-byte §44
 * cap leaf `[SRMECH_GENOME_CHROM_CAP_MARKER] + label, NUL-padded to dim`. This is
 * the first C cap-WRITER (the genome C surface until now only READ/scanned caps),
 * so it also exposes the shared cap-pack framing rc197/rc198 reuse to build every
 * chromosome / gene / kernel cap. BYTE-IDENTICAL to the bytes behind
 * srmech.biology.genome.telomere (which wraps them in an HV(sectors=256)). The label
 * is raw bytes (the caller passes the already-UTF-8-encoded label); it must fit
 * dim - 1 bytes (§44 inline: one marker byte + label + NUL padding). Caller-arena
 * output (no malloc), no abs.
 *   label / label_len : the cap label bytes (label may be NULL iff label_len 0).
 *   dim               : the leaf width in bytes (> 0); the cap is exactly dim bytes.
 *   out / out_cap     : caller buffer (out_cap >= dim) — receives the dim cap bytes.
 * Error returns:
 *   SRMECH_ERR_NULL_ARG  — out is NULL, or label is NULL with label_len > 0.
 *   SRMECH_ERR_BAD_INPUT  — dim == 0, out_cap < dim, or label_len > dim - 1. */
srmech_status_t srmech_genome_telomere(
    const unsigned char *label, size_t label_len, uint32_t dim,
    unsigned char *out, size_t out_cap);

/* rc197 (#887) make_class → C leaf-batch 3 — the genome [class]'s CHROMOSOME +
 * RECALL in-memory leaf ops (the plain single-kernel path the `add_chromosome` /
 * `recall` methods bind). Both COMPOSE the rc196 cap foundation (genome_pack_cap /
 * genome_cap_kind) + the Class-M srmech_klein4_bind (the reversible Klein-4 XOR
 * `quad_turn`) — so a bare-C host (and the rc201 object-model engine) builds /
 * reverses a chromosome strand natively, BYTE-IDENTICAL to the Python. The
 * gene / kernel / active-telomere chromosome forms stay in the pure Python (they
 * open their own boundary caps); rc197 covers exactly the plain path.
 * Additive symbols only → SRMECH_ABI_VERSION stays 4. */

/* CHROMOSOME — the plain single-kernel strand builder: a leading CHROM telomere
 * cap over `label`, then each of the `n_leaves` leaves coupled through `coupling`.
 * Every block is leaf_dim bytes; the output strand is (1 + n_leaves) * leaf_dim
 * bytes. BYTE-IDENTICAL to srmech.biology.genome.chromosome(leaves, coupling,
 * label=…) for the plain path (recovered by srmech_genome_recall).
 *   label / label_len : the CHROM cap label bytes (label may be NULL iff len 0);
 *                       must fit leaf_dim - 1 bytes (§44 inline cap encoding).
 *   coupling           : the shared Klein-4 invariant (leaf_dim bytes, {0,1,2,3}).
 *   leaf_dim          : the block width in bytes (> 0, <= 256) == len(coupling).
 *   leaves / n_leaves : the n_leaves leaves, each leaf_dim bytes, contiguous
 *                       (leaves may be NULL iff n_leaves 0).
 *   out / out_cap     : caller buffer; out_cap >= (1 + n_leaves) * leaf_dim.
 * Error returns:
 *   SRMECH_ERR_NULL_ARG  — out or coupling NULL, or a NULL buffer with a nonzero len.
 *   SRMECH_ERR_BAD_INPUT  — leaf_dim 0 / > 256, over-long label, or a leaf byte > 3.
 *   SRMECH_ERR_OVERFLOW   — out_cap too small for the strand. */
srmech_status_t srmech_genome_chromosome(
    const unsigned char *label, size_t label_len,
    const unsigned char *coupling, uint32_t leaf_dim,
    const unsigned char *leaves, size_t n_leaves,
    unsigned char *out, size_t out_cap);

/* RECALL — recover a plain chromosome's leaves: walk the strand's `n_blocks`
 * fixed-width leaf_dim-byte blocks, SKIP every cap (genome_cap_kind >= 0), and
 * re-bind each data turn through `coupling` (the reversible Klein-4 bind is its
 * own inverse) to recover the original leaf. BYTE-IDENTICAL to
 * srmech.biology.genome.recall (gate-agnostic — it flattens across any cap marker).
 *   strand / n_blocks : the strand's n_blocks blocks, each leaf_dim bytes, contiguous.
 *   leaf_dim          : the block width in bytes (> 0, <= 256) == len(coupling).
 *   coupling           : the shared Klein-4 invariant (leaf_dim bytes, {0,1,2,3}).
 *   out / out_cap     : caller buffer for the recovered leaves; out_cap >=
 *                       (data-turn count) * leaf_dim (n_blocks * leaf_dim always fits).
 *   n_leaves_out      : out — the recovered data-turn (leaf) count.
 * Error returns:
 *   SRMECH_ERR_NULL_ARG  — strand / coupling / out / n_leaves_out NULL.
 *   SRMECH_ERR_BAD_INPUT  — leaf_dim 0 / > 256, or a data-turn byte > 3.
 *   SRMECH_ERR_OVERFLOW   — out_cap too small for the recovered leaves. */
srmech_status_t srmech_genome_recall(
    const unsigned char *strand, size_t n_blocks, uint32_t leaf_dim,
    const unsigned char *coupling,
    unsigned char *out, size_t out_cap, size_t *n_leaves_out);

/* rc198 (#887) make_class → C leaf-batch 4 — the genome [class]'s MULTI-KERNEL +
 * PARTITION in-memory leaf ops, COMPLETING the genome leaf-family in C (all 10
 * leaves C-realizable for the rc201 object-model engine). Both LOOP the rc197
 * in-memory leaves (srmech_genome_chromosome to assemble, the recall re-bind to
 * recover) and reuse the rc196 cap foundation (genome_pack_cap / genome_cap_kind /
 * genome_decode_label) verbatim, so a bare-C host builds / splits a multi-kernel
 * genome strand natively, BYTE-IDENTICAL to the Python. The §44 chromosomes=
 * multi-gene assembly form opens its own gene caps and stays pure.
 * Additive symbols only → SRMECH_ABI_VERSION stays 4. */

/* GENOME — assemble `n_kernels` labelled kernels into ONE strand: each kernel
 * becomes a CHROM-capped chromosome (srmech_genome_chromosome), concatenated in
 * kernel order. BYTE-IDENTICAL to srmech.biology.genome.genome(kernels, coupling) for
 * the plain single-gene-per-chromosome path.
 *   labels / label_lens : the n_kernels raw UTF-8 labels CONCATENATED, label_lens[k]
 *                         the k-th label's byte length (its slice into `labels`).
 *   coupling             : the shared Klein-4 invariant (leaf_dim bytes, {0,1,2,3}).
 *   leaf_dim            : the block width in bytes (> 0, <= 256) == len(coupling).
 *   leaves / leaf_counts: the kernels' leaves CONCATENATED (each leaf_dim bytes),
 *                         leaf_counts[k] the k-th kernel's leaf count.
 *   n_kernels           : the kernel count (labels/label_lens/leaf_counts may be
 *                         NULL iff n_kernels 0).
 *   out / out_cap       : caller buffer; out_cap >= (n_kernels + Σ leaf_counts)*leaf_dim.
 *   n_blocks_out        : out — the total strand block count written.
 * Error returns:
 *   SRMECH_ERR_NULL_ARG  — out / coupling / n_blocks_out NULL, or a NULL kernel array
 *                          with n_kernels > 0, or a kernel with a NULL leaf run.
 *   SRMECH_ERR_BAD_INPUT  — leaf_dim 0 / > 256, an over-long label, or a leaf byte > 3.
 *   SRMECH_ERR_OVERFLOW   — out_cap too small for the strand. */
srmech_status_t srmech_genome_genome(
    const unsigned char *labels, const size_t *label_lens,
    const unsigned char *coupling, uint32_t leaf_dim,
    const unsigned char *leaves, const size_t *leaf_counts, size_t n_kernels,
    unsigned char *out, size_t out_cap, size_t *n_blocks_out);

/* §95a/v13 CENTROMERE cap writer (rc262, #1407) — mirror srmech.biology.genome._pack_centromere:
 * `[0x58] + handle + NUL + R + R orientation votes, NUL-padded to dim`. `orientation` is a
 * Klein-4 sector (0..3); `repeats` R in [1, 255]; the votes are R copies of `orientation` (the
 * α-satellite array, majority-decoded on read). Byte-identical to the bytes behind the Python
 * centromere cap. Caller-arena (no malloc), no abs, no float.
 *   SRMECH_ERR_NULL_ARG  — out NULL, or handle NULL with handle_len > 0.
 *   SRMECH_ERR_BAD_INPUT  — dim 0 / > out_cap, orientation > 3, repeats out of [1,255], or the
 *                          [marker+handle+NUL+R+votes] payload does not fit dim. */
srmech_status_t srmech_genome_centromere(
    unsigned char orientation, uint32_t repeats, const unsigned char *handle,
    size_t handle_len, uint32_t dim, unsigned char *out, size_t out_cap);

/* §95a/v13 MINT — build a genome letting the tooling PICK each chromosome's shape by modeling
 * biology (mirror srmech.biology.genome.mint / #1407 / F1244). Same args + return as
 * srmech_genome_genome, but per kernel the ATTESTED encode_shape criterion decides: tome/mobius
 * (depth < 2, ≤ 4 leaves) → a Tier-1 PLASMID chromosome (no centromere, byte-identical to the
 * genome() chromosome); quad_strand (depth >= 2, ≥ 5 leaves) → a Tier-2 NUCLEAR chromosome with
 * an INTERIOR centromere at the metacentric split carrying the kernel's global orientation
 * (sha256(raw leaves)[0] & 3). BYTE-IDENTICAL to the Python mint(). Same error returns as
 * srmech_genome_genome; out_cap >= (n_kernels + Σ leaf_counts + n_nuclear)*leaf_dim. */
srmech_status_t srmech_genome_mint(
    const unsigned char *labels, const size_t *label_lens,
    const unsigned char *coupling, uint32_t leaf_dim,
    const unsigned char *leaves, const size_t *leaf_counts, size_t n_kernels,
    unsigned char *out, size_t out_cap, size_t *n_blocks_out);

/* §101 (v0.9.0rc275): the ENCODE-PROGRESS overload of MINT. Byte-identical to
 * srmech_genome_mint (which forwards here with tick == NULL), but fires the caller
 * `tick` heartbeat at the TOP of each kernel (phase SRMECH_PHASE_MINTING,
 * done = k [complete chromosomes so far], total = n_kernels). A nonzero tick
 * return CANCELS: *n_blocks_out is set to the COMPLETE blocks already written (a
 * valid PARTIAL genome of k chromosomes — never a half-written chromosome) and
 * SRMECH_CANCELLED is returned. `tick` may be NULL (runs exactly as the plain
 * symbol). ABI-additive symbol; the srmech_progress_tick_cb_t typedef is what
 * bumps SRMECH_ABI_VERSION 5 -> 6. */
srmech_status_t srmech_genome_mint_progress(
    const unsigned char *labels, const size_t *label_lens,
    const unsigned char *coupling, uint32_t leaf_dim,
    const unsigned char *leaves, const size_t *leaf_counts, size_t n_kernels,
    unsigned char *out, size_t out_cap, size_t *n_blocks_out,
    srmech_progress_tick_cb_t tick, void *tick_user);

/* §95a/v13 CENTROMERE READ (rc262) — recover a NUCLEAR chromosome's global orientation +
 * arm-ratio (mirror srmech.biology.genome.centromere_of). Walks the strand's n_blocks leaf_dim-byte
 * blocks, majority-decodes the orientation from the interior 0x58 cap's α-satellite votes
 * (klein4_triality_correct's 2-of-3 generalised to R — a Class-K sector count + argmax, no abs),
 * and reads the p:q arm-ratio from the cap's POSITION (data turns before : after). Sets
 * *found_out = 1 and fills orientation/p/q iff a centromere is present, else *found_out = 0.
 *   SRMECH_ERR_NULL_ARG  — strand / found_out NULL (orientation/p/q may be NULL to skip).
 *   SRMECH_ERR_BAD_INPUT  — leaf_dim 0 / > 256, or a malformed centromere cap. */
srmech_status_t srmech_genome_centromere_of(
    const unsigned char *strand, size_t n_blocks, uint32_t leaf_dim,
    unsigned char *orientation_out, size_t *p_out, size_t *q_out,
    int *found_out);

/* §95b/v14 DIPLOID builder (rc262, #1407 / F1244) — mirror srmech.biology.genome.diploid: a
 * chromosome storing TWO homologous copies of the kernel split by an interior centromere
 * (the which-template mark): [diploid_telomere(label), copyA turns…, centromere(orientation),
 * copyB turns…], copyA == copyB. `orientation` is the mark + global orientation (0..3);
 * `repeats` the centromere α-satellite size. Writes (2*n_leaves + 2) leaf_dim-byte blocks.
 * BYTE-IDENTICAL to the Python diploid(). Caller-arena; no malloc/goto/abs/float.
 *   SRMECH_ERR_NULL_ARG  — out / coupling / n_blocks_out NULL, or NULL leaves with n_leaves>0.
 *   SRMECH_ERR_BAD_INPUT  — leaf_dim 0 / > 256, orientation > 3, an over-long label, a leaf
 *                          byte > 3, or the centromere repeats out of [1,255].
 *   SRMECH_ERR_OVERFLOW   — out_cap too small for the strand. */
srmech_status_t srmech_genome_diploid(
    const unsigned char *label, size_t label_len, const unsigned char *coupling,
    uint32_t leaf_dim, const unsigned char *leaves, size_t n_leaves,
    unsigned char orientation, uint32_t repeats,
    unsigned char *out, size_t out_cap, size_t *n_blocks_out);

/* §95b/v14 DIPLOID recover (rc262) — mirror srmech.biology.genome.recover_diploid: split the
 * strand at its interior centromere into copyA | copyB (homologs) and error-correct per leaf
 * (agree → use; one ERASED (all-zero leaf) → the intact homolog; disagree → the centromere
 * which-template mark). Re-binds each surviving turn through `coupling`. Writes the recovered
 * leaves (n_leaves of them). BYTE-IDENTICAL to the Python recover_diploid.
 *   SRMECH_ERR_NULL_ARG  — any pointer arg NULL.
 *   SRMECH_ERR_BAD_INPUT  — leaf_dim 0 / > 256, not a diploid strand (no leading 0x44), or a
 *                          malformed diploid (missing centromere / unequal homolog arms).
 *   SRMECH_ERR_OVERFLOW   — out too small for the recovered leaves. */
srmech_status_t srmech_genome_recover_diploid(
    const unsigned char *strand, size_t n_blocks, uint32_t leaf_dim,
    const unsigned char *coupling, unsigned char *out, size_t out_cap,
    size_t *n_out);

/* §Q8/rc311 — the Q8 element-type peers of recall / recover_diploid. IDENTICAL signatures to
 * their klein4 twins (srmech_genome_recall / srmech_genome_recover_diploid); they differ ONLY
 * in the per-turn op: the DECOUPLE is the Q₈ group INVERSE
 *   out[i] = srmech_q8_mult(stored[i], srmech_q8_conjugate(one[i]))
 * instead of the reversible klein4 XOR (Q₈ is NON-abelian, so decouple != couple — this is a
 * genuine inverse, resting on srmech_q8_mult(a, srmech_q8_conjugate(a)) == 0). The RIGHT-coupling
 * SIDE is a HARD ASSERTION in the C decouple (re-coupling the result recovers the stored turn),
 * mirroring the Python _q8_side_ok guard. BYTE-IDENTICAL to recall / recover_diploid with
 * element_type=ELEMENT_TYPE_Q8. NEW symbols reusing the existing q8 ops (no new typedef) →
 * SRMECH_ABI_VERSION stays 10, GENOME_FORMAT_VERSION stays 15. No malloc/goto/abs/float; a
 * non-Q8 data byte (>= 8) returns SRMECH_ERR_BAD_INPUT (the caller falls back to the pure walk).
 *   SRMECH_ERR_NULL_ARG  — any pointer arg NULL.
 *   SRMECH_ERR_BAD_INPUT — leaf_dim 0 / > 256, a data-turn byte >= 8, or (recover) not a
 *                          diploid strand / malformed diploid.
 *   SRMECH_ERR_OVERFLOW  — out too small for the recovered leaves. */
srmech_status_t srmech_genome_recall_q8(
    const unsigned char *strand, size_t n_blocks, uint32_t leaf_dim,
    const unsigned char *coupling, unsigned char *out, size_t out_cap,
    size_t *n_leaves_out);
srmech_status_t srmech_genome_recover_diploid_q8(
    const unsigned char *strand, size_t n_blocks, uint32_t leaf_dim,
    const unsigned char *coupling, unsigned char *out, size_t out_cap,
    size_t *n_out);

/* §55/§Q8/v16 (rc312) — the 3-BIT Q₈ packed-turn CODEC primitives (the genome-fully-in-C
 * mirror of _pack_turn_block_q8 / _unpack_turn_payload_q8). A Q₈ data turn carries a 3-bit
 * symbol (2-bit V4 coset + 1-bit winding sign), so it 3-bit-packs where the klein4 turn packs
 * 2. Layout is MSB-FIRST CONTIGUOUS: symbol i -> bits [3i, 3i+3) of a big-endian bitstream
 * (symbol 0 highest, each symbol's high bit first); the unused LOW bits of a partial final byte
 * are zero (canonical). BYTE-IDENTICAL to the Python codec (the parity gate re-verifies over
 * odd/partial leaf_dims). ADDITIVE symbols reusing NO callback typedef -> SRMECH_ABI_VERSION
 * stays 10. No malloc/goto/abs/float (integer bit-arithmetic).
 *
 * pack:  `leaf` = leaf_dim Q₈ bytes (0..7); `out` gets [SRMECH_GENOME_Q8_PACKED_TURN_MARKER]
 *        + ceil(leaf_dim*3/8) payload bytes; *out_len = 1 + ceil(leaf_dim*3/8). `out` must hold
 *        that many bytes. A byte >= 8 -> SRMECH_ERR_BAD_INPUT.
 * unpack: `payload` = ceil(leaf_dim*3/8) bytes (NOT the marker); `out` gets leaf_dim Q₈ bytes.
 *   SRMECH_ERR_NULL_ARG  — any pointer arg NULL.
 *   SRMECH_ERR_BAD_INPUT — leaf_dim 0 / > 256, or (pack) a symbol >= 8. */
srmech_status_t srmech_genome_q8_pack_turn(
    const unsigned char *leaf, uint32_t leaf_dim,
    unsigned char *out, size_t *out_len);
srmech_status_t srmech_genome_q8_unpack_turn(
    const unsigned char *payload, uint32_t leaf_dim, unsigned char *out);

/* §55/§𝕆-TURN/v19 (rc326) — the 4-BIT octonion packed-turn CODEC primitives (the
 * genome-fully-in-C mirror of _pack_turn_block_octonion / _unpack_turn_payload_octonion). An
 * octonion data turn carries a 4-bit symbol (the ±e₀..±e₇ index), so it 4-bit-packs where the
 * Q8 turn packs 3 and the klein4 turn 2. Layout is MSB-FIRST CONTIGUOUS: symbol i -> bits
 * [4i, 4i+4) of a big-endian bitstream (symbol 0 in the high nibble, each symbol's high bit
 * first); the unused LOW bits of a partial final byte are zero (canonical). BYTE-IDENTICAL to
 * the Python codec (the parity gate re-verifies over odd/partial leaf_dims). ADDITIVE symbols
 * reusing NO callback typedef -> SRMECH_ABI_VERSION stays 10. No malloc/goto/abs/float (integer
 * bit-arithmetic).
 *
 * pack:  `leaf` = leaf_dim octonion bytes (0..15); `out` gets
 *        [SRMECH_GENOME_OCTONION_PACKED_TURN_MARKER] + ceil(leaf_dim*4/8) payload bytes;
 *        *out_len = 1 + ceil(leaf_dim*4/8). `out` must hold that many bytes. A byte >= 16 ->
 *        SRMECH_ERR_BAD_INPUT.
 * unpack: `payload` = ceil(leaf_dim*4/8) bytes (NOT the marker); `out` gets leaf_dim octonion
 *        bytes.
 *   SRMECH_ERR_NULL_ARG  — any pointer arg NULL.
 *   SRMECH_ERR_BAD_INPUT — leaf_dim 0 / > 256, or (pack) a symbol >= 16. */
srmech_status_t srmech_genome_octonion_pack_turn(
    const unsigned char *leaf, uint32_t leaf_dim,
    unsigned char *out, size_t *out_len);
srmech_status_t srmech_genome_octonion_unpack_turn(
    const unsigned char *payload, uint32_t leaf_dim, unsigned char *out);

/* §95.1d/v15 INTEGRATE (rc276, #891 / F1244 / G4) — the stage-2 SPLICE primitive:
 * insert a PROVIRUS chromosome strand INTO a host genome strand at a chromosome
 * boundary (mirror srmech.biology.genome.integrate). Scans the host's leaf_dim-byte
 * blocks for boundary caps (CHROM / kernel-telomere / active-telomere / diploid),
 * resolves the insert LOCUS from `at` (the host chromosome index to insert BEFORE),
 * and concatenates host[:locus] + provirus + host[locus:] BYTE-IDENTICALLY — whole
 * self-describing blocks, no re-coupling (the provirus turns are already coupled).
 * A bare-C host integrates end-to-end via this ONE call (closes the rc262/rc273
 * "a C-only host integrates identically" claim, which previously had no C peer).
 *   host / host_blocks / host_leaf_dim : the host strand (host may be NULL iff 0
 *                       blocks); host_leaf_dim is read only when host_blocks > 0.
 *   provirus / prov_blocks / prov_leaf_dim : the provirus strand (>= 1 block,
 *                       opening with a boundary cap); prov_leaf_dim == the output width.
 *   at                : host chromosome index to insert BEFORE (0-based); < 0 = after
 *                       the last chromosome (the Python `at=None` default).
 *   out / out_cap     : caller buffer; out_cap >= (host_blocks + prov_blocks)*prov_leaf_dim.
 *   n_blocks_out      : out — the spliced block count (host_blocks + prov_blocks) on a
 *                       compatible integration; untouched on an honest-decline.
 *   integrated_out    : out — 1 on a compatible splice, 0 on an honest-decline.
 * The DEFAULT COMPATIBILITY GATE (§135/F1251): an empty host coheres with any
 * provirus; else host_leaf_dim == prov_leaf_dim (a Class-K coupling-WIDTH EQUALITY
 * read, NEVER abs — different widths were coupled through different `coupling`
 * invariants: the CG258 incompatible-replicon analog). On incompatibility this
 * HONEST-DECLINES (*integrated_out = 0, nothing written, SRMECH_OK — the C analog of
 * the Python None; mirrors centromere_of's *found_out = 0). The `compatible=` caller
 * predicate stays a Python-layer affordance (a callable cannot cross the C wire).
 * Error returns:
 *   SRMECH_ERR_NULL_ARG  — out / n_blocks_out / integrated_out NULL, provirus NULL with
 *                          prov_blocks > 0, or host NULL with host_blocks > 0.
 *   SRMECH_ERR_BAD_INPUT  — a leaf_dim 0 / > 256, an empty provirus, a provirus / host
 *                          not opening with a boundary cap, or `at` out of range.
 *   SRMECH_ERR_OVERFLOW   — out_cap too small for the spliced strand.
 * Additive symbol (no new typedef) -> SRMECH_ABI_VERSION stays 6, GENOME_FORMAT_VERSION
 * stays 15. Caller-arena; no malloc/goto/abs/float. */
srmech_status_t srmech_genome_integrate(
    const unsigned char *host, size_t host_blocks, uint32_t host_leaf_dim,
    const unsigned char *provirus, size_t prov_blocks, uint32_t prov_leaf_dim,
    long at, unsigned char *out, size_t out_cap,
    size_t *n_blocks_out, int *integrated_out);

/* §100 GAP 1/v15 MINT-STRAND (rc277, #891-peer / F1249 / G5) — the stage-2 PROMOTE
 * primitive of the F1252 two-stage encode: splice a §95a interior CENTROMERE (0x58) into
 * an ALREADY-PACKED strand at the p:q arm-split, PROMOTING a Tier-1 PLASMID to a Tier-2
 * NUCLEAR chromosome (mirror srmech.biology.genome.mint_strand). The cap-writer
 * (srmech_genome_centromere) already had a C peer; before rc277 the GLUE — data-turn
 * scan -> metacentric midpoint -> single-block centromere insert — was Python-only. This
 * closes that GAP so a bare-C host promotes a strand end-to-end via ONE call.
 *   strand / n_blocks / leaf_dim : the already-packed input strand (>= 1 block, opening
 *                       with a CHROM / kernel / active / diploid boundary cap); leaf_dim
 *                       is the block width AND coupling's width AND the output width.
 *   coupling           : the shared Klein-4 invariant (leaf_dim bytes); read ONLY when
 *                       orientation_auto != 0 (recall's un-couple), else may be NULL.
 *   centromere_at     : the arm-split in DATA TURNS (the cap goes AFTER that many data
 *                       turns); < 0 = the metacentric midpoint n_turns/2 (Python
 *                       centromere_at=None). Must be in [0, n_turns] when >= 0.
 *   orientation       : the global 4-way which-way (0..3), used only when
 *                       orientation_auto == 0.
 *   orientation_auto  : 1 = content-address the orientation from the strand's OWN
 *                       recovered leaves (recall -> sha256(leaves)[0] & 3, the SAME
 *                       _mint_orientation rule mint() uses — the Python orientation=None
 *                       default); 0 = use `orientation` verbatim.
 *   repeats           : the centromere α-satellite repeat-array size R in [1, 255].
 *   handle / handle_len : the CENP-A inline epigenetic address (may be NULL iff 0; no NUL
 *                       byte inside — the pack rule of srmech_genome_centromere).
 *   out / out_cap     : caller buffer; out_cap >= (n_blocks + 1)*leaf_dim. When
 *                       orientation_auto, `out` doubles as the recall scratch arena (the
 *                       recalled leaves are fully consumed BEFORE the splice writes out).
 *   n_blocks_out      : out — the minted block count (n_blocks + 1).
 * BYTE-IDENTICAL to the Python mint_strand (same content-address orientation, the same
 * centromere cap bytes, the same block splice). The interior centromere is TRANSPARENT to
 * recall / kernel_to_graph (they skip caps, §44), so the recovered payload is unchanged.
 * Error returns:
 *   SRMECH_ERR_NULL_ARG  — out / n_blocks_out / strand NULL, coupling NULL with
 *                          orientation_auto, or handle NULL with handle_len > 0.
 *   SRMECH_ERR_BAD_INPUT  — leaf_dim 0 / > 256, an empty strand, a strand not opening with
 *                          a boundary cap, a strand ALREADY carrying a centromere,
 *                          centromere_at out of [0, n_turns], or a bad orientation /
 *                          repeats / over-long handle (from the cap writer).
 *   SRMECH_ERR_OVERFLOW   — out_cap too small for the +1-block minted strand.
 * The §101 progress= gate is a Python-only affordance (a splice has no meaningful partial;
 * a callable cannot cross the C wire). Additive symbol (no new typedef) ->
 * SRMECH_ABI_VERSION stays 6, GENOME_FORMAT_VERSION stays 15. Caller-arena; no
 * malloc/goto/abs/float. */
srmech_status_t srmech_genome_mint_strand(
    const unsigned char *strand, size_t n_blocks, uint32_t leaf_dim,
    const unsigned char *coupling, long centromere_at,
    unsigned char orientation, int orientation_auto,
    uint32_t repeats, const unsigned char *handle, size_t handle_len,
    unsigned char *out, size_t out_cap, size_t *n_blocks_out);

/* §98/v15 CHROMATIN cap writer (rc268, #1422) — mirror srmech.biology.genome._pack_chromatin:
 * `[0x48] + handle + NUL + chromatin_type + num(uint64 BE) + den(uint64 BE), NUL-padded to dim`.
 * `chromatin_type` is 0 (binary) or 1 (graded); the accessibility level `num/den` is a reduced
 * non-negative rational in [0, 1] (den >= 1, num <= den). Byte-identical to the bytes behind the
 * Python chromatin cap. Caller-arena (no malloc), no abs, no float.
 *   SRMECH_ERR_NULL_ARG  — out NULL, or handle NULL with handle_len > 0.
 *   SRMECH_ERR_BAD_INPUT  — dim 0 / > out_cap, chromatin_type > 1, den 0, num > den, or the
 *                          [marker+handle+NUL+type+num+den] payload does not fit dim. */
srmech_status_t srmech_genome_chromatin(
    unsigned char chromatin_type, uint64_t num, uint64_t den,
    const unsigned char *handle, size_t handle_len, uint32_t dim,
    unsigned char *out, size_t out_cap);

/* §98/v15 CHROMATIN READ (rc268) — recover a chromosome's FIRST chromatin access state (mirror
 * srmech.biology.genome.chromatin_of). Walks the strand's n_blocks leaf_dim-byte blocks; on the
 * FIRST interior 0x48 cap sets *found_out = 1 and fills chromatin_type / num / den, plus *at_out
 * = the number of DATA TURNS before it (0 → whole-chromosome scope, >0 → a stretch). *found_out
 * = 0 (a chromatin-free / all-euchromatin chromosome) leaves the outs untouched.
 *   SRMECH_ERR_NULL_ARG  — strand / found_out NULL (type/num/den/at may be NULL to skip).
 *   SRMECH_ERR_BAD_INPUT  — leaf_dim 0 / > 256, or a malformed chromatin cap. */
srmech_status_t srmech_genome_chromatin_of(
    const unsigned char *strand, size_t n_blocks, uint32_t leaf_dim,
    unsigned char *type_out, uint64_t *num_out, uint64_t *den_out,
    size_t *at_out, int *found_out);

/* §98.1/v15 (§98.1/G1 / rc274) — the COMPUTED accessibility level of ONE chromatin cap under
 * cell_state (mirror srmech.biology.genome._chromatin_access). Decode the static (chromatin_type, num,
 * den); read the §98.1 access_gate_type at den_end (guard den_end < leaf_dim, else NONE): NONE →
 * (num, den) (constitutive, constant in cell_state); a facultative KLEIN4/BOOLEAN/THRESHOLD gate →
 * (num, den) if the gate FIRES under cell_state (the SAME §129/§130/§131 evaluators), else (0, 1)
 * (silenced). `cap` is ONE leaf_dim-byte 0x48 cap. Byte-identical to the pure Python. Additive
 * symbol → SRMECH_ABI_VERSION stays 5. Caller-arena (no malloc), no abs, no float; a READ.
 *   SRMECH_ERR_NULL_ARG  — cap / num_out / den_out NULL.
 *   SRMECH_ERR_BAD_INPUT  — leaf_dim 0 / > 256, cap[0] != 0x48, a malformed cap / gate, or an
 *                          unsupported access_gate_type.
 *   SRMECH_ERR_OVERFLOW   — an int64 threshold-accumulate overflow (caller falls to the exact
 *                          pure/bignum Python path — the native result, when produced, is exact). */
srmech_status_t srmech_genome_chromatin_access(
    const unsigned char *cap, uint32_t leaf_dim, uint64_t cell_state,
    uint64_t *num_out, uint64_t *den_out);

/* §98.1/v15 (§98.1/G1 / rc274) — the FACULTATIVE chromatin cap writer (mirror the bytes behind
 * srmech.biology.genome._pack_chromatin with a gate): srmech_genome_chromatin, then append
 * `gate_blob = [access_gate_type(u8)] + payload` VERBATIM after den, NUL-padded to dim. The Python
 * _chromatin_gate_blob serialisation is the oracle; this appends its bytes. A NONE (constitutive)
 * cap passes gate_blob_len 0 → byte-identical to srmech_genome_chromatin. Additive symbol →
 * SRMECH_ABI_VERSION stays 5. Caller-arena (no malloc), no abs, no float.
 *   SRMECH_ERR_NULL_ARG  — out NULL, handle NULL with handle_len > 0, or gate_blob NULL with
 *                          gate_blob_len > 0.
 *   SRMECH_ERR_BAD_INPUT  — the constitutive cap does not build (see srmech_genome_chromatin), or
 *                          [marker+handle+NUL+type+num+den+gate_blob] does not fit dim. */
srmech_status_t srmech_genome_chromatin_gated(
    unsigned char chromatin_type, uint64_t num, uint64_t den,
    const unsigned char *gate_blob, size_t gate_blob_len,
    const unsigned char *handle, size_t handle_len, uint32_t dim,
    unsigned char *out, size_t out_cap);

/* §98/v15 (rc332 §102 G7, #887) CONDENSE — the WHOLE placement decision of
 * srmech.biology.genome.condense: resolve the target chromosome's block range (the shared
 * label -> chromatin-range find, mirroring _chrom_range) and, WITHIN it, the BLOCK index at
 * which the already-built chromatin cap (srmech_genome_chromatin, an existing C peer) is spliced.
 * `*insert_out` is that index; a bare-C host then lays out strand[:insert] + cap + strand[insert:]
 * (the trivial byte mechanics). The Python-only _chrom_range(label) lookup + region resolution
 * this rc lifts into C (the "reaching a C primitive is not a whole-op entry" gap). PLACEMENT is
 * scope, mirroring the pure body EXACTLY:
 *   region_kind 0 (None)  -> insert = start + 1 (HEAD scope: right after the opening telomere).
 *   region_kind 1 (int)   -> `region_turn` selects the region_turn-th DATA turn in (start, end);
 *                            == the turn count appends at `end`; > it DECLINES.
 *   region_kind 2 (label) -> the FIRST gene in (start, end) whose inline label equals
 *                            (region_label, region_label_len); no match DECLINES.
 * `label`/`label_is_none` pick the chromosome (label_is_none requires a single-chromosome strand,
 * mirroring label=None). BYTE-IDENTICAL to the pure insert index; a turn count is a non-negative
 * cardinality (no abs, NOT a Class-K pin-slot site). Additive plain symbol (no new typedef) ->
 * SRMECH_ABI_VERSION stays 10, SRMECH_GENOME_FORMAT_VERSION stays 19. Caller-arena; no
 * malloc/goto/recursion/abs/float.
 *   SRMECH_ERR_NULL_ARG  — strand / insert_out NULL, or a label pointer NULL with a nonzero length.
 *   SRMECH_ERR_BAD_INPUT  — leaf_dim 0 / > 256, a range-find decline (strand does not open with a
 *                          boundary cap / ambiguous label=None / no chromosome by that label), a
 *                          region_turn past the data-turn count, or a gene label with no match. */
srmech_status_t srmech_genome_condense(
    const unsigned char *strand, size_t n_blocks, uint32_t leaf_dim,
    const unsigned char *label, size_t label_len, int label_is_none,
    int region_kind, uint64_t region_turn,
    const unsigned char *region_label, size_t region_label_len,
    size_t *insert_out);

/* §98/v15 (rc332 §102 G7, #887) DECONDENSE — the inverse: the WHOLE cap-clear decision of
 * srmech.biology.genome.decondense. Writes a KEEP-MASK — `keep_out[i]` is 1 iff block i SURVIVES the
 * clear, 0 iff it is dropped — one byte per block (caller buffer >= n_blocks bytes); a bare-C host
 * then filters the strand by the mask. Mirrors the pure body EXACTLY:
 *   label_is_none (whole strand) -> drop EVERY 0x48 chromatin cap; never declines (a pure filter).
 *   else (label scope)          -> drop only the 0x48 caps inside the target chromosome's block
 *                                  range [start, end) (the SAME range-find as condense).
 * BYTE-IDENTICAL to the pure kept-block set. Additive plain symbol (no new typedef) ->
 * SRMECH_ABI_VERSION stays 10, SRMECH_GENOME_FORMAT_VERSION stays 19. Caller-arena; no
 * malloc/goto/recursion/abs/float.
 *   SRMECH_ERR_NULL_ARG  — strand / keep_out NULL, or label NULL with label_len > 0 (label scope).
 *   SRMECH_ERR_BAD_INPUT  — leaf_dim 0 / > 256, or a label-scope range-find decline. */
srmech_status_t srmech_genome_decondense(
    const unsigned char *strand, size_t n_blocks, uint32_t leaf_dim,
    const unsigned char *label, size_t label_len, int label_is_none,
    unsigned char *keep_out);

/* §98/v15 (rc333 §102 G7, #887) — the GENES-FAMILY whole-op C peers: the per-gene
 * (label, leaves) BOUNDARY-PRESERVING read that srmech_genome_recall FLATTENS and
 * srmech_genome_gene_express_plan returns as SPANS. All three emit ONE shared big-endian
 * structure a bare-C host parses without Python:
 *   [u32 n_genes] then per gene [u32 label_len][label bytes][u32 n_leaves][n_leaves*leaf_dim],
 * each leaf the DECOUPLED (recovered) byte-per-symbol leaf. Additive plain symbols (no new
 * typedef) -> SRMECH_ABI_VERSION stays 10, SRMECH_GENOME_FORMAT_VERSION stays 19.
 *
 * GENES — the IN-MEMORY per-gene split of srmech.biology.genome.genes (the KLEIN4 default; a
 * DECODED Q8/octonion strand carries no on-disk carrier marker, so those take the pure oracle).
 * `strand` is `n_blocks` fixed-width `leaf_dim`-byte blocks; the peer walks them (a GENE cap
 * opens a gene whose inline label is read back; the 4 chromosome-boundary caps + any leading
 * block are skipped; every other started block is decoupled into the gene's leaves) and emits the
 * shared structure. BYTE-IDENTICAL to the pure genes. Caller-arena; no malloc/goto/recursion/abs.
 *   SRMECH_ERR_NULL_ARG  — strand / coupling / out / out_len NULL.
 *   SRMECH_ERR_BAD_INPUT  — leaf_dim 0 / > 256, a malformed gene cap (no label NUL).
 *   SRMECH_ERR_OVERFLOW   — `out` (out_cap) too small for the emitted structure. */
srmech_status_t srmech_genome_genes(
    const unsigned char *strand, size_t n_blocks, uint32_t leaf_dim,
    const unsigned char *coupling, unsigned char *out, size_t out_cap, size_t *out_len);

/* GENOME_GENES — the ON-DISK sibling: obtain the manifest (parse or §44 rebuild-by-scan),
 * resolve (leaf_dim, coupling) from the head, find `label`'s chromosome, PAGE its region
 * (RAM-bounded, §45 cap-integrity checked), and run the SAME per-gene split over the raw region
 * (each carrier decoupled from its on-disk turn marker). BYTE-IDENTICAL to the pure genome_genes.
 * `ws` (>= srmech_genome_arena_bytes(body_len, n_chroms, body_len)) holds the manifest tree and is
 * REUSED as the region-staging buffer after the label/offsets/cap-hash are copied out.
 * Caller-arena; no malloc/goto/recursion/abs.
 *   SRMECH_ERR_NULL_ARG  — dir / label / out / out_len / ws NULL, or coupling NULL w/ a nonzero len.
 *   SRMECH_ERR_BAD_INPUT  — no manifest+coupling, a malformed head, no chromosome by that label,
 *                          a cap-integrity mismatch, or a malformed gene cap.
 *
 * BOUND (rc342, #T969): a READ - it holds the derive against the head's
 * committed body_sha256 and is SRMECH_ERR_BAD_INPUT on a mismatch. See THE
 * READ-SIDE INTEGRITY BOUND note above srmech_genome_catalog.
 *   SRMECH_ERR_OVERFLOW   — `out` or the region-staging arena too small. */
srmech_status_t srmech_genome_genome_genes(
    const char *dir, const char *label,
    const unsigned char *coupling, size_t coupling_len,
    unsigned char *out, size_t out_cap, size_t *out_len, void *ws, size_t ws_len);

/* GENOME_GENES_EXPRESSED — the ON-DISK gene-express ORCHESTRATION whole-op peer: the plan-walk +
 * region-page + collect loop that srmech_genome_gene_express_plan (per-community head-gate) and
 * srmech_genome_gene_express (per-gene decision) did NOT compose. Walks every chromosome, pages
 * ONLY the expressed communities' regions, filters each by gene_express (the §98 chromatin outer
 * gate over the §128-132 promoter, carrier-aware decouple), and emits the shared genes structure.
 * BYTE-IDENTICAL to the pure genome_genes_expressed. `ws` holds the manifest tree; `region_ws`
 * (SEPARATE, >= body_len) stages one region at a time (the manifest tree must persist across the
 * chromosome loop, so the region cannot reuse `ws`). Caller-arena; no malloc/goto/recursion/abs.
 *   SRMECH_ERR_NULL_ARG  — dir / out / out_len / ws / region_ws NULL, or coupling NULL w/ nonzero len.
 *   SRMECH_ERR_BAD_INPUT  — no manifest+coupling, a malformed head/entry, or a cap-integrity mismatch.
 *
 * BOUND (rc342, #T969): a READ - it holds the derive against the head's
 * committed body_sha256 and is SRMECH_ERR_BAD_INPUT on a mismatch. See THE
 * READ-SIDE INTEGRITY BOUND note above srmech_genome_catalog.
 *   SRMECH_ERR_OVERFLOW   — `out` or the region-staging arena too small. */
srmech_status_t srmech_genome_genes_expressed(
    const char *dir, uint64_t cell_state,
    const unsigned char *coupling, size_t coupling_len,
    unsigned char *out, size_t out_cap, size_t *out_len,
    void *ws, size_t ws_len, void *region_ws, size_t region_ws_len);

/* PARTITION — recover every kernel from a multi-kernel strand (the inverse of
 * srmech_genome_genome): a CHROM / kernel-telomere / active-telomere cap opens a
 * partition (label read INLINE); a gene / header cap is SKIPPED (the partition
 * flattens across genes); each data turn until the next opening cap is re-bound
 * through `coupling` as that partition's leaf. BYTE-IDENTICAL to
 * srmech.biology.genome.partition; the caller applies the dict overwrite-on-duplicate-
 * label + `labels=` filter semantics over these ORDERED partitions.
 *   strand / n_blocks : the strand's n_blocks blocks, each leaf_dim bytes, contiguous.
 *   leaf_dim          : the block width in bytes (> 0, <= 256) == len(coupling).
 *   coupling           : the shared Klein-4 invariant (leaf_dim bytes).
 *   out_leaves        : caller buffer for the recovered leaves (leaf_dim bytes each,
 *                       partition order); out_leaves_cap >= (data-turn count)*leaf_dim.
 *   out_labels        : caller buffer for the partition labels, one leaf_dim-byte
 *                       NUL-terminated slot each; out_labels_cap >= n_parts*leaf_dim.
 *   part_leaf_counts  : caller buffer [counts_cap] — the per-partition leaf count.
 *   n_parts_out       : out — the partition (opening-cap) count.
 *   n_leaves_out      : out — the total recovered-leaf count.
 * Error returns:
 *   SRMECH_ERR_NULL_ARG  — any pointer arg is NULL.
 *   SRMECH_ERR_BAD_INPUT  — leaf_dim 0 / > 256, an over-long label, or a data byte > 3.
 *   SRMECH_ERR_OVERFLOW   — out_leaves / out_labels / part_leaf_counts too small. */
srmech_status_t srmech_genome_partition(
    const unsigned char *strand, size_t n_blocks, uint32_t leaf_dim,
    const unsigned char *coupling,
    unsigned char *out_leaves, size_t out_leaves_cap,
    unsigned char *out_labels, size_t out_labels_cap,
    uint32_t *part_leaf_counts, size_t counts_cap,
    size_t *n_parts_out, size_t *n_leaves_out);

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
 *   coupling / coupling_len : coupling's single leaf_dim-byte block
 *                     (coupling_len MUST equal leaf_dim).
 *   ws / ws_len     : the caller arena for ALL scratch (the per-chromosome
 *                     scan arrays + the manifest buffer + the JSON tree) — the
 *                     bound is the caller's RAM, NOT a compiled-in cap. Size it
 *                     to the genome (a host sizes it large, an MCU small);
 *                     SRMECH_ERR_OVERFLOW if too small for this genome.
 *
 * Error returns:
 *   SRMECH_ERR_NULL_ARG   — dir / body(when body_len>0) / coupling / ws NULL.
 *   SRMECH_ERR_BAD_INPUT   — leaf_dim == 0 / > 256, coupling_len != leaf_dim,
 *                           a truncated / unrecognised block, a turn before
 *                           the first CHROM cap, or a label too long.
 *   SRMECH_ERR_IO          — fopen / fwrite failed.
 *   SRMECH_ERR_OVERFLOW    — the caller arena ws is too small for this genome.
 */
srmech_status_t srmech_genome_save(
    const char *dir,
    const unsigned char *body, size_t body_len,
    uint32_t leaf_dim,
    const unsigned char *coupling, size_t coupling_len,
    /* `#T1108` (ABI 13): the caller MPR SOURCE attestation — a JSON object
     * carrying any of source_doi / source_url / license / retrieved_at. NULL
     * (len 0) = none, in which case the block already in <dir>/manifest.json
     * is CARRIED FORWARD and srmech's default is written only when there is
     * nothing to inherit. A given block that DISAGREES with a non-default one
     * already on disk is SRMECH_ERR_BAD_INPUT: overwriting an attestation of
     * record is allowed, it is never silent. response_sha256 and the four
     * encoder-identity fields are ALWAYS re-synthesised and are not readable
     * through this channel. */
    const char *attestation, size_t attestation_len,
    void *ws, size_t ws_len);

/* The arena byte count any genome op needs for a body of `body_len` bytes with
 * `n_chroms` chromosomes when it also stages a `region_len`-byte region (a .chr
 * region, or an append/replace region; 0 otherwise). Capacity is DEFINED by the
 * C layout — the caller sizes its `ws` arena from THIS rather than guessing. Pure
 * arithmetic (no I/O); each term traces to a real allocation (two body copies +
 * the .chr region/hex/io + per-chromosome strings/manifest/json + a fixed slop).
 * Adding this symbol does NOT bump SRMECH_ABI_VERSION. */
size_t srmech_genome_arena_bytes(size_t body_len, uint32_t n_chroms,
                                 size_t region_len, size_t attestation_len);

/* The exact working-arena size (bytes) srmech_genome_append needs for the genome at
 * `dir` when it stages a `region_len`-byte region. Reads manifest.json into `ws`
 * (needs manifest_size + 1 bytes; a few KB for a v12 head-only genome) and classifies
 * EXACTLY as srmech_genome_append (same byte-substring probe): a v12 head
 * ("n_chromosomes") or a v4..v11 full manifest ("regions") takes the O(1) tail-extend →
 * a MANIFEST-scaled arena; a legacy v2/v3 (neither key) migrates once → a whole-body
 * arena. The tail-extend fast path stages ONE region slot + a head-only (1-entry)
 * manifest, so its arena is O(1) in the chromosome count (does NOT grow with the body).
 * A bare-C host sizes its `ws` arena for an append from THIS — the v12/legacy
 * classification lives ONCE, in C, not reimplemented per host. On success *out_bytes
 * gets the size.
 *
 * Error returns:
 *   SRMECH_ERR_NULL_ARG   — dir / out_bytes is NULL (or ws is NULL with ws_len != 0).
 *   SRMECH_ERR_OVERFLOW   — ws is too small to hold manifest.json (needs msz + 1).
 *   SRMECH_ERR_IO         — the body turns.bin is missing / unstattable.
 * Adding this symbol does NOT bump SRMECH_ABI_VERSION. */
srmech_status_t srmech_genome_append_arena_bytes(const char *dir, size_t region_len,
                                                 size_t attestation_len,
                                                 void *ws, size_t ws_len,
                                                 size_t *out_bytes);

/* ------------------------------------------------------------------ *
 * THE READ-SIDE INTEGRITY BOUND (rc342, #T969) - the genome READ contract
 *
 * EVERY read entry point below holds what it derived from turns.bin against the
 * COMMITTED body_sha256 in <dir>/manifest.json, and returns SRMECH_ERR_BAD_INPUT
 * (the GenomeBoundingError analogue) when the two disagree. "Every" IS the
 * contract: srmech_genome_catalog / _census / _registry / _load / _window /
 * _export / _explode / _genome_genes / _genes_expressed / _gene_express_plan /
 * _section_counts. A caller may treat any one of them as an integrity gate.
 *
 * WHY THE CONTRACT IS "EVERY READ" AND NOT A LIST. rc337 bound exactly ONE read,
 * srmech_genome_catalog. That made the answer to "does a read reject a corrupt
 * body?" a fact about plumbing rather than about policy, and the measured answer
 * was a patchwork: with ONE byte flipped in a chromosome label, _census /
 * _registry / _load / _explode / _genome_genes / _gene_express_plan all returned a
 * plausible result with a SUCCESS status, while _window / _export rejected it only
 * when the flipped byte happened to land inside the FIRST chromosome (a per-region
 * cap check, not a whole-body one - flip a byte in the LAST chromosome and they
 * accepted it too). _gene_express_plan was the sharpest case: it handed back the
 * mangled label "g\x02ography" with a success status, which is the exact symptom
 * rc337 was written to remove. A per-surface allow-list cannot be audited;
 * "every read bounds" can.
 *
 * WHAT IS UNBOUND, BY DECLARATION. The MUTATION entry points -
 * srmech_genome_append / _remove / _replace / _import / _add_plasmid - obtain the
 * manifest while the store is MID-EDIT, where a derive-vs-committed compare
 * polices a TRANSIENT window rather than settled state. rc337 measured that
 * directly: binding the shared derive turned Windows CI red with 22 mutation-path
 * failures, on stores an instrumented probe proved byte-identical to a green Linux
 * one. Those surfaces are bound one layer up, in the scripting projection, which
 * reads the catalog before dispatching. Their C entry points are NOT integrity
 * gates and a bare-C host must not use them as one. Closing that gap needs the
 * mid-edit window characterised first and is tracked separately.
 *
 * WHAT IS UNBOUND BECAUSE THERE IS NOTHING TO BIND AGAINST. Two cases pass through
 * every read unbound, in BOTH projections, on purpose:
 *   - a manifest-LESS genome (S44: the strand IS the SSoT - no committed value
 *     exists, so the bytes on disk are by definition the truth);
 *   - a v<=11 FULL manifest, whose body_sha256 may be a plain WHOLE-BODY digest
 *     rather than the v4+ region CHAIN a body scan re-derives; comparing those
 *     would hard-fail every legacy store.
 *
 * COST: none measured. The committed digest is copied out of the manifest parse
 * the derive ALREADY performs, so no read gained an open, a parse, or a hash, and
 * the comparison is a 64-byte memcmp. This is load-bearing rather than incidental:
 * plumbed the obvious way - a second open+parse of manifest.json, which is how
 * rc337 reached the value - the rc282 DOWN-ONLY open-count ratchet measured
 * srmech_genome_section_counts going 5 -> 7 opens per scan.
 *
 * ABI: unchanged at 10. Every function rc342 added or re-shaped is static; no
 * exported signature moved and no symbol was added or removed. The rejection
 * reuses SRMECH_ERR_BAD_INPUT, already in each of these functions' documented
 * error sets.
 * ------------------------------------------------------------------ */

/* CATALOG: obtain the manifest catalog as a JSON value tree from the caller
 * arena `ws`.
 *
 * WHAT THIS COSTS (rc337 — the previous wording here was false). This block used
 * to claim the catalog "never opens turns.bin" when manifest.json is present. That
 * holds only for a v≤11 FULL manifest, which stored the per-chromosome array
 * verbatim. Since v12 the on-disk manifest is HEAD-ONLY — the array is a plaintext
 * table-of-contents and ADR-0003 forbids storing one — so it is DERIVED by scanning
 * the self-describing body. EVERY store written today is head-only, so this call
 * reads turns.bin end to end. (The Python docstring was corrected in rc282; this
 * one was not.)
 *
 * §44: when manifest.json is ABSENT the catalog is likewise REBUILT by scanning
 * turns.bin (the strand is the SSoT, the manifest an optional .fai cache); that
 * rebuild needs `coupling` (coupling_len IS the leaf width). On success
 * *out_manifest points at the root object (the full MPRRecord; its "data" child is
 * the catalog). Pass coupling=NULL,coupling_len=0 when a manifest is present.
 *
 * INTEGRITY (rc337): on the head-only path the re-derived region chain is held
 * against the head's COMMITTED body_sha256, so a body modified out of band is
 * SRMECH_ERR_BAD_INPUT rather than a catalog built from the corrupt bytes. A
 * manifest-LESS genome has no committed value and is therefore unbound (the strand
 * IS the truth), and a v≤11 FULL manifest is returned as parsed — there
 * body_sha256 can be a WHOLE-BODY digest rather than the v4+ region CHAIN a scan
 * re-derives, so an unconditional compare would hard-fail every legacy store.
 *
 * The bound is applied in the READ entry points and NOT in the shared derive
 * they call: that derive also serves every MUTATION, where it would police a
 * transient mid-edit window. See THE READ-SIDE INTEGRITY BOUND note above -
 * rc342 made the bound GLOBAL across reads. (The rc337 text here said census /
 * registry / load were 'NOT bound yet'. They now are.)
 *
 * Error returns:
 *   SRMECH_ERR_NULL_ARG   — dir / ws / out_manifest is NULL.
 *   SRMECH_ERR_IO          — turns.bin could not be opened / read on rebuild.
 *   SRMECH_ERR_OVERFLOW    — the manifest or its tree exceeds ws / turns.bin
 *                           exceeds the rebuild scratch.
 *   SRMECH_ERR_BAD_INPUT   — manifest.json is malformed JSON; OR it is absent
 *                           and no coupling was supplied (cannot scan); OR (rc337)
 *                           the body's derived region chain does not match the
 *                           head's committed body_sha256 (modified out of band),
 *                           or that head field is missing / not 64 hex chars.
 */
srmech_status_t srmech_genome_catalog(
    const char *dir, const unsigned char *coupling, size_t coupling_len,
    void *ws, size_t ws_len, srmech_json_value_t **out_manifest);

/* §96 CENSUS: the biology-native per-genome roll-up. Scans the body ONCE (the
 * per-chromosome cap_kind rides the §44 scan — no O(n) per-chromosome loads)
 * and returns a JSON value tree in the caller arena `ws`:
 *   {path, n_chromosomes, types:{plasmid,nuclear,diploid},
 *    chromosomes:[{label,type,leaf_count}], total_leaves, topology}
 * `type`/`cap_kind` is plasmid / nuclear (an interior §95a centromere) / diploid (a
 * §95b diploid-telomere opener with no centromere; nuclear > diploid > plasmid).
 * rc271 (F1251): the field's own names — plasmid (was "stick") / nuclear (was
 * "minted"). `topology` is a STRUCTURAL integer read (no libm): "nuclear-like"
 * (any nuclear / diploid), else "organelle-like" (n>0 and total_leaves <= 8*n),
 * else "plasmid/prokaryote-like" (n>0, all plasmid), else "empty". Same manifest-present
 * / manifest-less rules as srmech_genome_catalog (pass coupling when absent).
 *
 * BOUND (rc342, #T969): the census runs its OWN derive (genome_scan_params ->
 * genome_load_strings), never the one srmech_genome_catalog binds, so it needed
 * its own. It now holds the re-derived region chain against the head's committed
 * body_sha256 and returns SRMECH_ERR_BAD_INPUT on a mismatch. Through rc341 it
 * returned a census OF THE CORRUPT BYTES with a success status while the
 * scripting projection raised - a live ADR-0009 split, and the worst surface to
 * have one on: the census is the CHEAP INVENTORY read, so a caller who censuses
 * and never windows was told the object was fine and never learned otherwise.
 *
 * Error returns: SRMECH_ERR_NULL_ARG (dir/ws/out NULL); SRMECH_ERR_IO
 * (turns.bin unreadable); SRMECH_ERR_OVERFLOW (ws too small);
 * SRMECH_ERR_BAD_INPUT (malformed manifest, or absent + no coupling).
 */
srmech_status_t srmech_genome_census(
    const char *dir, const unsigned char *coupling, size_t coupling_len,
    void *ws, size_t ws_len, srmech_json_value_t **out_census);

/* Arena bytes srmech_genome_census needs for a body of `body_len` bytes /
 * `n_chroms` chromosomes (== the catalog budget; a census subtree is smaller). */
size_t srmech_genome_census_arena_bytes(size_t body_len, uint32_t n_chroms);

/* rc345 (task T964) CONTENT: the count that survives REPARTITIONING. Scans the body
 * and returns a JSON value tree in the caller arena `ws`:
 *   {path, n_turns, n_chromosomes, n_content}
 * with n_content = n_turns - n_chromosomes.
 *
 * WHY THE SUBTRACTION IS EXACT. Every chromosome opens with exactly ONE boundary
 * (telomere) cap, and a cap is a leaf_dim-wide BLOCK — i.e. a turn — like any other
 * strand element, so the boundary caps are IN n_turns. Subtracting the chromosome count
 * removes the container overhead with NO residual. Cut fixed content into chromosomes N
 * different ways and n_chromosomes changes (it IS the cut), n_turns changes (one turn
 * per added boundary) and body_sha256 changes (the caps are in the bytes) — n_content
 * does not. MEASURED over 8 partitionings of 24 leaves: n_turns 25/26/27/28/30/32/36/48,
 * n_content 24 in all eight, 8 distinct body_sha256.
 *
 * READ IT AS "NOT A CONTAINER", NOT AS "LEAVES". n_content counts every NON-BOUNDARY
 * block, INCLUDING inline §44 GENE caps and §95a centromeres. It equals the census's
 * total_leaves (which excludes ALL caps) only when the chromosomes carry no inline caps;
 * the same 24 leaves as 4 genes of one chromosome give n_content 28, total_leaves 24.
 *
 * DERIVED, NEVER STORED. n_content is not a manifest field and
 * SRMECH_GENOME_FORMAT_VERSION does not move for it — the strand determines it, and a
 * stored copy of an exactly-derivable value is a second encoding that can go stale.
 * This reads the counts the §44 way, by SCANNING the self-describing body rather than
 * trusting the head's cached scalars, and therefore carries the rc342 READ-SIDE
 * INTEGRITY BOUND for free: the scan re-derives the region chain anyway, so holding it
 * against the head's committed body_sha256 costs no extra open, parse, or hash. Same
 * manifest-present / manifest-less rules as srmech_genome_catalog (pass coupling when
 * absent); a manifest-LESS genome or a v<=11 FULL manifest passes through UNBOUND.
 *
 * Error returns: SRMECH_ERR_NULL_ARG (dir/ws/out NULL); SRMECH_ERR_IO (turns.bin
 * unreadable); SRMECH_ERR_OVERFLOW (ws too small); SRMECH_ERR_BAD_INPUT (malformed
 * manifest, absent + no coupling, or a body/committed-digest mismatch).
 */
srmech_status_t srmech_genome_content(
    const char *dir, const unsigned char *coupling, size_t coupling_len,
    void *ws, size_t ws_len, srmech_json_value_t **out_content);

/* Arena bytes srmech_genome_content needs (== the census budget; the derive is the
 * census's derive and only the emitted subtree is smaller). */
size_t srmech_genome_content_arena_bytes(size_t body_len, uint32_t n_chroms);

/* §96 REGISTRY: the cell/melange census over a ROOT of genomes. Scans `root`
 * for genome dirs (a subdir holding BOTH turns.bin and manifest.json) via the
 * PAL directory surface (no #ifdef), censuses each (sorted by basename), and
 * returns a JSON value tree in `ws`:
 *   {root, n_genomes, genomes:[<census per genome>]}
 * `ws` must fit the SUM of the per-genome census arenas
 * (srmech_genome_census_arena_bytes) plus a small registry-root reserve; a
 * root that OPENS but holds no genome dirs yields n_genomes 0 (not an error).
 *
 * rc294: a root that CANNOT BE OPENED — absent, permission denied, or not a
 * directory — is SRMECH_ERR_IO, NOT "n_genomes 0, success". Through rc292 every
 * dir-open failure was reported as an empty registry with a success status, so
 * a typo'd corpus path answered "your corpus is empty" authoritatively while
 * the scripting projection raised on the same input (ADR-0009: the SPLIT was
 * the defect). The n_genomes-0 contract has always been about an EMPTY dir and
 * is unchanged. No new status enumerator: SRMECH_ERR_IO was already in this
 * function's documented error set, so the ctypes wire format is untouched and
 * SRMECH_ABI_VERSION does not move.
 *
 * BOUND (rc342, #T969): each per-genome census inherits srmech_genome_census's
 * bound, so a corrupt genome under `root` fails the registry read instead of
 * contributing a census of its corrupt bytes. See THE READ-SIDE INTEGRITY BOUND.
 *
 * Error returns: SRMECH_ERR_NULL_ARG (root/ws/out NULL); SRMECH_ERR_IO
 * (`root` cannot be opened, or a genome's turns.bin unreadable);
 * SRMECH_ERR_OVERFLOW (ws too small); SRMECH_ERR_BAD_INPUT (a genome's
 * manifest malformed, or absent + no coupling).
 */
srmech_status_t srmech_genome_registry(
    const char *root, const unsigned char *coupling, size_t coupling_len,
    void *ws, size_t ws_len, srmech_json_value_t **out_registry);

/* LOAD: read <dir>/turns.bin into `out` (capacity out_cap bytes), re-hash
 * the whole body and compare its hex against the manifest's
 * data.body_sha256. On a mismatch returns SRMECH_ERR_BAD_INPUT (the
 * GenomeBoundingError analogue). *out_len receives the body length. §44: when
 * manifest.json is absent the catalog is rebuilt by scanning turns.bin, which
 * needs `coupling` (coupling_len IS the leaf width); pass coupling=NULL,0 when a
 * manifest is present.
 *
 * WHY THE TRAILING RE-HASH IS NOT THE BOUND. On a v12 HEAD-ONLY store - which is
 * every store written today - that re-hash is a TAUTOLOGY: the manifest tree it
 * compares against was itself derived from the body being verified, so its
 * body_sha256 and its regions both come out of that one scan and the comparison
 * cannot fail, whatever the body says. It stays operative on a v<=11 FULL
 * manifest, whose arrays are an independent committed record parsed off disk.
 * rc342 (#T969) added the REAL bound one layer up, against the head's committed
 * body_sha256, so this call IS now an integrity gate on a head-only store; the
 * rc337 advice to 'read srmech_genome_catalog first' is obsolete.
 *
 * Error returns:
 *   SRMECH_ERR_NULL_ARG   — dir / out / out_len / ws is NULL.
 *   SRMECH_ERR_IO          — turns.bin I/O failed.
 *   SRMECH_ERR_OVERFLOW    — out_cap < body length, or ws too small.
 *   SRMECH_ERR_BAD_INPUT   — body hash != manifest body_sha256 (bound
 *                           failed), a malformed manifest, OR no manifest and
 *                           no coupling.
 */
srmech_status_t srmech_genome_load(
    const char *dir, unsigned char *out, size_t out_cap, size_t *out_len,
    const unsigned char *coupling, size_t coupling_len,
    void *ws, size_t ws_len);

/* WINDOW: seek to one chromosome's byte_offset, read its byte_len bytes
 * into `out` (capacity out_cap), re-hash the leading cap block and compare
 * its hex against that chromosome's cap_sha256. On a mismatch returns
 * SRMECH_ERR_BAD_INPUT (the bounding error). *out_len receives byte_len.
 * The returned bytes include the leading cap block (the whole region). §44:
 * when manifest.json is absent the offsets are rebuilt by scanning turns.bin,
 * which needs `coupling` (coupling_len IS the leaf width); pass coupling=NULL,0
 * when a manifest is present.
 *
 * Error returns:
 *   SRMECH_ERR_NULL_ARG   — dir / label / out / out_len / ws is NULL.
 *   SRMECH_ERR_IO          — turns.bin I/O failed.
 *   SRMECH_ERR_OVERFLOW    — out_cap < byte_len, or ws too small.
 *   SRMECH_ERR_BAD_INPUT   — label absent, cap hash != cap_sha256, a
 *                           malformed manifest, OR no manifest and no coupling.
 *
 * BOUND (rc342, #T969): a READ - it holds the derive against the head's
 * committed body_sha256 and is SRMECH_ERR_BAD_INPUT on a mismatch. See THE
 * READ-SIDE INTEGRITY BOUND note above srmech_genome_catalog.
 */
srmech_status_t srmech_genome_window(
    const char *dir, const char *label,
    unsigned char *out, size_t out_cap, size_t *out_len,
    const unsigned char *coupling, size_t coupling_len,
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
 * rebuilt by scanning turns.bin, which needs `coupling` (coupling_len IS the leaf
 * width); pass coupling=NULL,0 when a manifest is present. ABI-additive: a new
 * symbol, so SRMECH_ABI_VERSION stays 3.
 *
 * Error returns:
 *   SRMECH_ERR_NULL_ARG   — dir / out / out_len / ws is NULL.
 *   SRMECH_ERR_IO          — turns.bin I/O failed.
 *   SRMECH_ERR_OVERFLOW    — ws too small for the manifest parse.
 *   SRMECH_ERR_BAD_INPUT   — out too small for the plan, a malformed manifest,
 *                           OR no manifest and no coupling.
 *
 * BOUND (rc342, #T969): a READ - it holds the derive against the head's
 * committed body_sha256 and is SRMECH_ERR_BAD_INPUT on a mismatch. See THE
 * READ-SIDE INTEGRITY BOUND note above srmech_genome_catalog.
 */
srmech_status_t srmech_genome_gene_express_plan(
    const char *dir, uint64_t cell_state,
    const unsigned char *coupling, size_t coupling_len,
    unsigned char *out, size_t out_cap, size_t *out_len,
    void *ws, size_t ws_len);

/* APPEND: append one chromosome's region (`region`, region_len bytes = the
 * cap block + its data turns, all leaf_dim-byte blocks) to the END of
 * <dir>/turns.bin (append-only; prior body bytes are never rewritten), then
 * rewrite manifest.json with the new chromosome entry + recomputed n_turns /
 * body_sha256. Every EXISTING chromosome entry (cap_sha256 / byte_offset /
 * leaf_count / byte_len) is carried through byte-identically.
 *   coupling / coupling_len : coupling block (coupling_len == leaf_dim), re-used
 *                     for the manifest coupling hash+hex (must match the stored
 *                     leaf_dim; the prior body is bound-checked before growth).
 *
 * Error returns:
 *   SRMECH_ERR_NULL_ARG   — dir / label / region(when region_len>0) /
 *                           coupling / ws is NULL.
 *   SRMECH_ERR_IO          — turns.bin / manifest.json I/O failed.
 *   SRMECH_ERR_OVERFLOW    — ws too small, or too many chromosomes.
 *   SRMECH_ERR_BAD_INPUT   — leaf_dim mismatch, label already present, a
 *                           truncated / unrecognised region block (§55/v3:
 *                           blocks are variable-width, validated by the scan),
 *                           prior body bound failed, or malformed manifest.
 *
 * NOT AN INTEGRITY GATE (rc342, #T969): a MUTATION - it obtains the manifest
 * MID-EDIT, so it is deliberately NOT bound against the committed body_sha256
 * (that would police a transient window; rc337 measured 22 Windows failures).
 * Bound one layer up in the scripting projection. See THE READ-SIDE INTEGRITY
 * BOUND note above srmech_genome_catalog.
 */
srmech_status_t srmech_genome_append(
    const char *dir, const char *label,
    const unsigned char *region, size_t region_len, uint32_t leaf_dim,
    const unsigned char *coupling, size_t coupling_len,
    const char *attestation, size_t attestation_len,
    void *ws, size_t ws_len);

/* §45 IN-PLACE EDIT — biology excises, it does not re-synthesize. With the §44
 * self-describing body an edit is a pure BYTE splice on turns.bin (no kernel is
 * decoded / re-coupled — the surviving chromosomes' coupled bytes stay
 * byte-identical, only relocated). The spliced body is committed via
 * srmech_genome_save, which re-derives the manifest by scanning it, so the
 * on-disk turns.bin + manifest.json are byte-identical to the Python
 * genome_remove / genome_replace output. Like APPEND (a write op), `coupling` is
 * REQUIRED (srmech_genome_save needs it for the manifest coupling hash+hex) and
 * coupling_len IS leaf_dim. The whole body is re-hashed against the committed
 * body_sha256 BEFORE the edit (the GenomeBoundingError analogue). */

/* REMOVE: excise chromosome `label` IN PLACE — find its region in the
 * self-describing body, splice the [byte_offset, byte_offset+byte_len) span out
 * of turns.bin, and rewrite manifest.json (DERIVED by scanning the spliced
 * body). Mirrors the Python genome_remove. coupling_len MUST equal the stored
 * leaf_dim.
 *
 * Error returns:
 *   SRMECH_ERR_NULL_ARG   — dir / label / coupling / ws is NULL.
 *   SRMECH_ERR_IO          — turns.bin / manifest.json I/O failed.
 *   SRMECH_ERR_OVERFLOW    — ws too small, or body exceeds the scratch.
 *   SRMECH_ERR_BAD_INPUT   — coupling_len 0 / > 256 or != stored leaf_dim, label
 *                           absent, `label` is the genome's ONLY chromosome,
 *                           prior body bound failed, or malformed manifest.
 *
 * NOT AN INTEGRITY GATE (rc342, #T969): a MUTATION - it obtains the manifest
 * MID-EDIT, so it is deliberately NOT bound against the committed body_sha256
 * (that would police a transient window; rc337 measured 22 Windows failures).
 * Bound one layer up in the scripting projection. See THE READ-SIDE INTEGRITY
 * BOUND note above srmech_genome_catalog.
 */
srmech_status_t srmech_genome_remove(
    const char *dir, const char *label,
    const unsigned char *coupling, size_t coupling_len,
    const char *attestation, size_t attestation_len,
    void *ws, size_t ws_len);

/* REPLACE: swap chromosome `label`'s content IN PLACE — splice its old span out
 * of turns.bin and `region` (region_len bytes = a fresh telomere-capped
 * chromosome's cap block + data turns, all leaf_dim-byte blocks) IN at the same
 * position, then rewrite manifest.json (DERIVED by scanning the new body). Every
 * OTHER chromosome's body bytes stay byte-identical. Mirrors the Python
 * genome_replace (whose `leaves` are coupled into the region by the caller).
 *
 * Error returns:
 *   SRMECH_ERR_NULL_ARG   — dir / label / region(when region_len>0) / coupling /
 *                           ws is NULL.
 *   SRMECH_ERR_IO          — turns.bin / manifest.json I/O failed.
 *   SRMECH_ERR_OVERFLOW    — ws too small, or the new body exceeds the scratch.
 *   SRMECH_ERR_BAD_INPUT   — leaf_dim 0 / coupling_len != leaf_dim / != stored
 *                           leaf_dim, region_len not a whole multiple of
 *                           leaf_dim, label absent, prior body bound failed, or
 *                           malformed manifest.
 *
 * NOT AN INTEGRITY GATE (rc342, #T969): a MUTATION - it obtains the manifest
 * MID-EDIT, so it is deliberately NOT bound against the committed body_sha256
 * (that would police a transient window; rc337 measured 22 Windows failures).
 * Bound one layer up in the scripting projection. See THE READ-SIDE INTEGRITY
 * BOUND note above srmech_genome_catalog.
 */
srmech_status_t srmech_genome_replace(
    const char *dir, const char *label,
    const unsigned char *region, size_t region_len, uint32_t leaf_dim,
    const unsigned char *coupling, size_t coupling_len,
    const char *attestation, size_t attestation_len,
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
 * parallel attestation. Mirrors srmech.biology.genome genome_export / genome_import.
 *
 * The .chr region / hex / file-text scratch is carved from the caller arena
 * (sized to the chromosome / the .chr file), so a chromosome of any size the
 * caller's arena fits can be bundled — no compiled-in cap. */

/* EXPORT: write chromosome `label`'s region (CHROM cap + coupled turns; the
 * leading cap re-hashed against the manifest cap_sha256) + coupling to `out_path`
 * as ONE MPR-attested .chr record. `coupling` is OPTIONAL — pass it (length ==
 * leaf_dim) to export from a MANIFEST-LESS source (§44; the catalog is rebuilt
 * by scanning turns.bin), else NULL when manifest.json is present. The .chr
 * round-trips byte-identically.
 *
 * Error returns:
 *   SRMECH_ERR_NULL_ARG   — dir / label / out_path / ws is NULL.
 *   SRMECH_ERR_IO          — turns.bin / the .chr I/O failed.
 *   SRMECH_ERR_OVERFLOW    — the caller arena ws is too small for this
 *                           chromosome (its region / hex / .chr text).
 *   SRMECH_ERR_BAD_INPUT   — coupling_len 0 / > 256, label absent, cap integrity
 *
 * BOUND (rc342, #T969): a READ - it holds the derive against the head's
 * committed body_sha256 and is SRMECH_ERR_BAD_INPUT on a mismatch. See THE
 * READ-SIDE INTEGRITY BOUND note above srmech_genome_catalog.
 *                           bound failed, or a malformed manifest. */
srmech_status_t srmech_genome_export(
    const char *dir, const char *label, const char *out_path,
    const unsigned char *coupling, size_t coupling_len,
    const char *attestation, size_t attestation_len,
    void *ws, size_t ws_len);

/* IMPORT: read a .chr bundle (genome_export's output), RE-HASH its region and
 * its coupling against the bundle's own attestation (self-verifying — a flipped
 * byte is SRMECH_ERR_BAD_INPUT), then either SEED a fresh genome at `dest` when
 * it has no turns.bin yet (the region becomes turns.bin VERBATIM) or APPEND the
 * chromosome byte-for-byte into the existing dest (which REQUIRES the same
 * coupling invariant — dest coupling.sha256 == the .chr's — and a fresh label).
 * `coupling` is only consulted as the rebuild width for a manifest-less existing
 * dest (§44); the bundle carries its own coupling. The dest directory must exist
 * (the C surface does not mkdir — turns.bin is written into an existing dir,
 * like save / append). Mirrors the Python genome_import.
 *
 * Error returns:
 *   SRMECH_ERR_NULL_ARG   — chr_path / dest / ws is NULL.
 *   SRMECH_ERR_IO          — the .chr / turns.bin / manifest.json I/O failed.
 *   SRMECH_ERR_OVERFLOW    — the caller arena ws is too small for this .chr
 *                           (its text / decoded region / the dest body grow).
 *   SRMECH_ERR_BAD_INPUT   — not a chromosome bundle (wrong data_schema_id),
 *                           a region / coupling integrity bound failed, the dest
 *                           leaf_dim / coupling mismatches, the label already
 *
 * NOT AN INTEGRITY GATE (rc342, #T969): a MUTATION - it obtains the manifest
 * MID-EDIT, so it is deliberately NOT bound against the committed body_sha256
 * (that would police a transient window; rc337 measured 22 Windows failures).
 * Bound one layer up in the scripting projection. See THE READ-SIDE INTEGRITY
 * BOUND note above srmech_genome_catalog.
 *                           exists in dest, or a malformed bundle / manifest. */
srmech_status_t srmech_genome_import(
    const char *chr_path, const char *dest,
    const unsigned char *coupling, size_t coupling_len,
    const char *attestation, size_t attestation_len,
    void *ws, size_t ws_len);

/* §43 LOOSE<->PACKED — git's object model for genomes.
 *
 * EXPLODE: write one loose <label>.chr bundle per chromosome of the packed
 * genome at `dir` into `out_dir` (which must exist; the C surface does not
 * mkdir), each via srmech_genome_export (so each .chr self-verifies). Like
 * `git unpack-objects`. `coupling` is only consulted as the rebuild width
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
 *   SRMECH_ERR_BAD_INPUT   — coupling_len 0 / > 256, an unsafe label, a cap
 *
 * BOUND (rc342, #T969): a READ - it holds the derive against the head's
 * committed body_sha256 and is SRMECH_ERR_BAD_INPUT on a mismatch. See THE
 * READ-SIDE INTEGRITY BOUND note above srmech_genome_catalog.
 *                           integrity bound failed, or a malformed manifest. */
srmech_status_t srmech_genome_explode(
    const char *dir, const char *out_dir,
    const unsigned char *coupling, size_t coupling_len,
    void *ws, size_t ws_len);

/* PACK: read every <label>.chr in `loose_dir` (a *.chr directory scan), sort
 * them by their inner data.label (CANONICAL order — content-preserving, not
 * byte-order-preserving: it re-canonicalises), and srmech_genome_import each
 * in order into `dest` (the first SEEDS dest, the rest APPEND — so they must
 * share one coupling). Like `git repack`. `dest` must exist (no mkdir); an
 * empty `loose_dir` (or no *.chr files) is SRMECH_ERR_BAD_INPUT. `coupling` is
 * only the rebuild width for a manifest-less existing dest (§44). Mirrors the
 * Python genome_pack.
 *
 * Error returns:
 *   SRMECH_ERR_NULL_ARG   — loose_dir / dest / ws is NULL.
 *   SRMECH_ERR_IO          — a .chr / turns.bin / manifest.json I/O failed.
 *   SRMECH_ERR_OVERFLOW    — the caller arena ws is too small for this pack
 *                           (the .chr names / labels / a bundle / the body), or
 *                           a path too long.
 *   SRMECH_ERR_BAD_INPUT   — coupling_len 0 / > 256, no .chr files, a bundle is
 *                           not a chromosome / fails its integrity bound, or
 *                           the dest leaf_dim / coupling / label invariant. */
srmech_status_t srmech_genome_pack(
    const char *loose_dir, const char *dest,
    const unsigned char *coupling, size_t coupling_len,
    const char *attestation, size_t attestation_len,
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

/* §127/v7 (#726, rc329 §102 G7) ACTIVE-TELOMERE PACKER — build ONE §127 active telomere
 * cap (mirror srmech.biology.genome._pack_active_telomere / active_telomere), the PACK
 * counterpart of srmech_genome_telomere_tick above. Layout: [0x74 marker] + label + NUL
 * + count(uint64 BIG-ENDIAN), NUL-padded to leaf_dim. A telomere that opens+governs a
 * chromosome (the op) carrying the exact non-negative Hayflick counter `count` INLINE
 * (the operand), the count right AFTER the label's NUL so the label decodes UNIFORMLY.
 * The tick op above reads+decrements this cap to mint a DAUGHTER; this entry packs ONE
 * active cap with NO daughter-minting, so a bare-C host builds it standalone (the
 * c_host_parity_audit_rc273 §2 G7 exhibit). `count` is a uint64 — a Hayflick counter is
 * never signed, so nothing to strip (NOT a Class-K pin-slot site). BYTE-IDENTICAL to the
 * bytes behind the Python cap.
 *   label / label_len : the chromosome label (may be NULL iff label_len 0; no NUL inside).
 *   count             : the exact non-negative Hayflick counter.
 *   leaf_dim          : the leaf width (match the turns it caps).
 *   out / out_cap     : caller buffer >= leaf_dim bytes — the packed cap leaf.
 * Error returns:
 *   SRMECH_ERR_NULL_ARG  — out NULL, or label NULL with label_len > 0.
 *   SRMECH_ERR_BAD_INPUT  — leaf_dim 0 / > out_cap, a NUL byte inside label, or the
 *                          [marker+label+NUL+count] payload does not fit leaf_dim.
 * Additive plain symbol (no new typedef) → SRMECH_ABI_VERSION stays 10,
 * GENOME_FORMAT_VERSION stays 19. Caller-arena; no malloc/goto/recursion/abs/float. */
srmech_status_t srmech_genome_active_telomere(
    const unsigned char *label, size_t label_len, uint64_t count,
    uint32_t leaf_dim, unsigned char *out, size_t out_cap);

/* rc329 (§102 G7) MINT PLAN — the read-only introspection loop of
 * srmech.biology.genome.mint_plan in C: for each kernel decide its chromosome SHAPE
 * (plasmid vs nuclear) and, for a nuclear kernel, its content-addressed global
 * orientation, so a bare-C host assembles the plan with no Python present (the
 * c_host_parity_audit_rc273 §2 G7 exhibit: the per-step primitive srmech_genome_encode_shape
 * was native but the assembling loop was not). BUILDS NOTHING. Per kernel i:
 *   is_nuclear_out[i] = 1 iff srmech_genome_encode_shape(max(1, leaf_counts[i]) *
 *                       SRMECH_GENOME_LEAF_CAP) yields a quad_strand (depth >= 2) — the
 *                       F715 attested criterion (mirror genome._mint_shape); else 0 (a
 *                       Tier-1 plasmid).
 *   orient_out[i]     = sha256(content_i)[0] & 3 (Class A content-address → Class C
 *                       sector) — WRITTEN only for a nuclear kernel; 0 for a plasmid
 *                       (the Python projection maps a plasmid's orientation to None).
 *   content / content_lens : the flat concatenation of every kernel's content preimage
 *                       (the SAME bytes genome._kernel_content_bytes serialises: its
 *                       leaves as fixed-width blocks); content_lens[i] is kernel i's slice.
 *   leaf_counts / n_kernels : the per-kernel leaf count (the plan's n_leaves) and count.
 *   is_nuclear_out / orient_out : caller arrays of n_kernels bytes each.
 * BYTE-IDENTICAL to the pure mint_plan's (shape, orientation) per kernel. A leaf count is
 * a non-negative cardinality — no abs (NOT a Class-K pin-slot site).
 * Error returns:
 *   SRMECH_ERR_NULL_ARG  — is_nuclear_out / orient_out NULL, or leaf_counts /
 *                          content_lens NULL with n_kernels > 0.
 *   SRMECH_ERR_BAD_INPUT  — a leaf count whose *256 would overflow uint64.
 * Additive plain symbol (no new typedef) → SRMECH_ABI_VERSION stays 10,
 * GENOME_FORMAT_VERSION stays 19. Caller-arena; no malloc/goto/recursion/abs/float. */
srmech_status_t srmech_genome_mint_plan(
    const unsigned char *content, const size_t *content_lens,
    const size_t *leaf_counts, size_t n_kernels,
    unsigned char *is_nuclear_out, unsigned char *orient_out);

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
 * Byte-identical to the pure Python decision in srmech.biology.genome._gene_expresses. The
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
 * decision in srmech.biology.genome._gene_level. If the exact int64 dose accumulate would OVERFLOW,
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
 * srmech.biology.genome._modulator_recover_pure. No arena; malloc-free; no abs; a READ.
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
 * srmech.biology.genome._serialize_bool_constraint(_modulator_constraint_bool_pure).
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
 * to the pure Python srmech.biology.genome._satisfies_bool. Malloc-free; no abs; READ.
 * Error returns:
 *   SRMECH_ERR_NULL_ARG  — buf(when buf_len>0) / satisfied is NULL.
 *   SRMECH_ERR_BAD_INPUT  — a truncated / malformed buffer. */
srmech_status_t srmech_genome_modulator_constraint_satisfies(
    const unsigned char *buf, size_t buf_len,
    uint64_t candidate_cell_state, int *satisfied);

/* srmech_graph_kernel_encode / _decode — the #1390 item 2 codec: a sparse
 * SIGNED integer graph (vocab_size + edges + int weights[metric] + signed
 * charges + optional node_ids label table + extras) <-> a flat Klein-4
 * symbol stream {0,1,2,3}, base-4 digits behind a 2-symbol length header
 * (<= 15 digits = 30 bits; Class-K zig-zag charge). Byte-identical to the
 * pure genome._graph_ints_to_syms / _graph_syms_to_ints. On decode the
 * caller sizes edge_cap / nid_cap / ex_cap (a count over-cap =>
 * SRMECH_ERR_BAD_INPUT). ADDITIVE — SRMECH_ABI_VERSION stays 5. */
srmech_status_t srmech_graph_kernel_encode(
    uint64_t vocab_size,
    const uint64_t *edge_i, const uint64_t *edge_j,
    const uint64_t *weights, const int64_t *charges, size_t n_edges,
    const uint64_t *node_ids, size_t n_nid,
    const uint64_t *extras, size_t n_ex,
    uint8_t *out_syms, size_t syms_cap, size_t *out_n_syms);

srmech_status_t srmech_graph_kernel_decode(
    const uint8_t *syms, size_t n_syms,
    uint64_t *out_vocab_size,
    uint64_t *out_edge_i, uint64_t *out_edge_j,
    uint64_t *out_weights, int64_t *out_charges, size_t edge_cap,
    size_t *out_n_edges,
    uint64_t *out_node_ids, size_t nid_cap, size_t *out_n_nid,
    uint64_t *out_extras, size_t ex_cap, size_t *out_n_ex);

/* rc327 (§100 GAP 2 / G2, task #905) — GENOME FROM GRAPH: the C-native orchestrator
 * that builds a multi-chromosome genome from a directed SIGNED graph PARTITIONED BY
 * ITS OWN STRUCTURE, so a bare-C host runs the §100 GAP-2 builder end-to-end (the
 * LAST §100 G-series parity gap G2; the G2 SIBLING of G3 srmech_genome_graph_partition).
 * It COMPOSES srmech_genome_graph_partition (the groups) -> per group an in-RAM
 * induced-subgraph relabel (keep every edge with BOTH endpoints in the group,
 * ORIGINAL edge order) -> srmech_graph_kernel_encode -> the HV kernel BLOCK build
 * (byte-identical to kernel_pack's leaves, the mint-strand block form) -> a NUCLEAR
 * community is MINTED via srmech_genome_mint_strand (a 0x58 centromere), a PLASMID
 * community is kept -> CONCATENATE into one strand. BYTE-IDENTICAL to the pure Python
 * srmech.biology.genome.genome_from_graph strand.
 *
 * The PARTITION READ-OUT arrays are the SAME shape srmech_genome_graph_partition
 * writes (community_out / part_*_out / counts_out / group_*_out / group_members_out /
 * result_out) and are CALLER-OWNED — so ONE call yields BOTH the assembled strand AND
 * the data the Python projection rebuilds the partition dict from (no double partition).
 * groups_cap >= 2*(n+1). The STRAND is written to `out` as uniform leaf_dim-byte HV
 * blocks (out_cap >= the assembled block count * leaf_dim); *out_nblocks the block
 * count, *out_nchroms the chromosome (== group) count, chrom_nsyms_out[gi] the group's
 * true Klein-4 symbol count D (kernel_unpack recovers it from the §89 header, but it is
 * surfaced for the chromosome record). `edges_path` is the write_packed_graph edge file
 * srmech_genome_graph_partition streams; `edge_i/edge_j/weights/charges` (n_edges; the
 * charges may be NULL = all 0) are the SAME edges IN MEMORY for the induced-subgraph
 * rebuild (write_packed_graph does not carry charges). `centromere_at < 0` = the
 * metacentric midpoint; repeats/handle -> mint_strand. `tick` threads the §101
 * PARTITIONING heartbeat into the partition AND fires a MINTING heartbeat per group; a
 * nonzero return CANCELS -> *out_cancelled = 1 with a CLEAN partial (the partition
 * cancel builds no strand; a mint-loop cancel keeps whole chromosomes so far). `ws` is a
 * caller arena of >= srmech_genome_from_graph_arena_bytes(n, n_edges, n_bins, leaf_dim)
 * BYTES (no malloc). NEVER abs (participations/counts/relabels are non-negative).
 * ADDITIVE — a plain symbol reusing the existing srmech_progress_tick_cb_t typedef (NO
 * new callback typedef): SRMECH_ABI_VERSION stays 10, GENOME_FORMAT_VERSION stays 19
 * (the strand is plain v15-era KERNEL chromosomes over existing caps + blocks). */
size_t srmech_genome_from_graph_arena_bytes(uint32_t n, uint32_t n_edges,
                                            uint32_t n_bins, uint32_t leaf_dim);

srmech_status_t srmech_genome_from_graph(
    uint32_t n, const char *edges_path, const char *work_dir,
    const uint64_t *edge_i, const uint64_t *edge_j,
    const uint64_t *weights, const int64_t *charges, size_t n_edges,
    uint32_t leaf_dim, const unsigned char *coupling,
    uint32_t max_tome, uint32_t n_bins, uint32_t max_iters, uint32_t max_depth,
    long centromere_at, uint32_t repeats,
    const unsigned char *handle, size_t handle_len,
    uint32_t *community_out, uint64_t *part_num_out, uint64_t *part_den_out,
    uint64_t *counts_out,
    uint32_t *group_comm_out, uint32_t *group_type_out, uint32_t *group_size_out,
    uint64_t *group_num_out, uint64_t *group_den_out,
    uint32_t *group_members_out, uint32_t groups_cap,
    srmech_genome_graph_partition_result_t *result_out,
    unsigned char *out, size_t out_cap, size_t *out_nblocks,
    uint64_t *chrom_nsyms_out, size_t *out_nchroms, uint32_t *out_cancelled,
    void *ws, size_t ws_len, srmech_progress_tick_cb_t tick, void *tick_ctx);

/* rc278 (§102 / F1252 STAGE 1 — EXTRACT) — PLASMID EXTRACT: the C-native
 * orchestrator that COMPOSES the stage-1 C peers so a bare-C host extracts ONE
 * document into ONE appended PLASMID section end-to-end (genome-must-exist-in-C).
 * It chains srmech_graph_kernel_encode (a doc's local co-occurrence graph -> a
 * flat Klein-4 symbol stream) -> a §89/v6 KERNEL-chromosome region build (the
 * missing syms->on-disk-region glue: a KERNEL telomere 0x6B cap + the coupled +
 * §55/v3 bit-packed uniformly-Klein-4 header + content leaves, BYTE-IDENTICAL to
 * kernel_pack + _disk_block) -> srmech_genome_append (§v12 O(1) HEAD-only tail-
 * extend). The co-occurrence peer (srmech_text_cooccurrence_topk / _extract) is
 * the other standalone stage-1 C peer a host composes upstream to produce the
 * (edges, weights) — so `cooccurrence_topk` -> `plasmid_extract` is the whole
 * stage-1 stack in C, zero Python. Append-only: prior sections stay byte-
 * untouched. Store the node_ids GLOBAL-id label table so a word shared across
 * sections carries the SAME id (the precondition stage-2 conservation reads).
 *   vocab_size / edge_i / edge_j / weights / charges / n_edges / node_ids /
 *   n_nid / extras / n_ex : EXACTLY srmech_graph_kernel_encode's inputs (the
 *                       doc's LOCAL co-occurrence graph; node_ids = the local ->
 *                       GLOBAL id table; charges may be NULL = all 0).
 *   dir / label         : the sections store (a genome dir that MUST already
 *                       exist — the append hot path) + this section's label.
 *   leaf_dim / coupling  : the store's leaf width + the shared Klein-4 invariant
 *                       (coupling is leaf_dim bytes); leaf_dim >= 52 (the §89
 *                       uniformly-Klein-4 header fits one leaf).
 *   ws / ws_len         : ONE caller working arena (the encode syms buffer, the
 *                       region buffer, AND srmech_genome_append's own arena are
 *                       carved from it; size generously — SRMECH_ERR_OVERFLOW if
 *                       too small).
 *   out_n_syms          : out — the section's true Klein-4 symbol count D (the
 *                       §89 header self-records it; no external length needed to
 *                       recover the graph via kernel_unpack / kernel_to_graph).
 * BYTE-IDENTICAL to the pure Python plasmid_extract's genome_append_kernel
 * section (same syms, same coupled + v3-packed region, same O(1) append).
 * Error returns:
 *   SRMECH_ERR_NULL_ARG  — dir / label / coupling / ws / out_n_syms NULL (or an
 *                          edge/nid/ex pointer NULL with a nonzero count).
 *   SRMECH_ERR_BAD_INPUT — leaf_dim 0 / > 256 / < 52, or a bad graph (from the
 *                          encoder: a 30-bit-overflowing datum, a bad charge).
 *   SRMECH_ERR_OVERFLOW  — ws too small for the syms / region / append stages.
 *   (plus srmech_genome_append's IO / bound returns unchanged.)
 * ADDITIVE — a new plain symbol reusing NO callback typedef: SRMECH_ABI_VERSION
 * stays 6. The on-disk GENOME_FORMAT_VERSION stays 15 (the sections store is a
 * plain genome dir of KERNEL chromosomes over existing v15 caps + blocks). */
srmech_status_t srmech_genome_plasmid_extract(
    uint64_t vocab_size,
    const uint64_t *edge_i, const uint64_t *edge_j,
    const uint64_t *weights, const int64_t *charges, size_t n_edges,
    const uint64_t *node_ids, size_t n_nid,
    const uint64_t *extras, size_t n_ex,
    const char *dir, const char *label,
    uint32_t leaf_dim, const unsigned char *coupling,
    const char *attestation, size_t attestation_len,
    void *ws, size_t ws_len, size_t *out_n_syms);

/* rc279 (§102 / F1252 STAGE 2 — ORGANIZE, the CONSERVE step) — read the
 * SECTION-COUNT distribution and return the CONSERVED CORE node set + the
 * threshold k. `counts[i]` is how many distinct plasmid sections node
 * `node_ids[i]` appears in (stage-1's O(1)-per-node integer accumulator). A node
 * is CONSERVED iff `counts[i] >= k` -> it joins the NUCLEAR core; the rest stay
 * accessory PLASMID (expect the ~16/84 asymmetric minority, F1251).
 *
 * `k` IS DERIVED FROM THE DATA, NOT TUNED. With `k_in < 0` this MEASURES the
 * ANTIMODE of the section-count histogram — the same walk, qualifying predicate
 * and widest-gap tie-break as the rc272 participation antimode
 * (genome._partition_antimode), applied in the count domain: the widest gap
 * between consecutive OCCUPIED count-bins whose two flanking modes are both real
 * (>= 2 nodes) splits conserved from accessory, and k = lo + 1. Note the
 * INVERSION vs participation: there HIGH = a bridging PLASMID, here HIGH
 * section-count = shared across many plasmids = the conserved NUCLEAR core.
 * UNIMODAL (no qualifying gap) -> ONE-DNA-TYPE: *out_bimodal = 0, *out_k = 0 and
 * *out_n_core = 0 — the split is NOT forced (the F1250 discipline). `k_in >= 0`
 * forces a caller-supplied k (a verification / replay affordance, NOT the derived
 * path; *out_bimodal is then 1).
 *   node_ids / counts / n_nodes : the parallel node-id + section-count arrays.
 *   k_in              : < 0 = DERIVE k from the distribution; >= 0 = force k.
 *   out_core_ids / core_cap / out_n_core : caller buffer + the conserved count;
 *                       core_cap >= n_nodes is always sufficient.
 *   out_k             : out — the threshold actually used (0 on one-DNA-type).
 *   out_bimodal       : out — 1 iff a real antimode split was found (or forced).
 *   hist / hist_cap   : caller arena for the count histogram AND the two
 *                       flanking-mode tables the O(max_count) antimode walk
 *                       needs; hist_cap must be >= 3 * (max_count + 1). (The
 *                       real corpus histogram is HEAVY-TAILED — a max count in
 *                       the hundreds of thousands over ~1.7k occupied bins,
 *                       F1253 — so re-scanning a side per gap would be
 *                       O(gaps * max_count); the prefix tables make it linear.)
 * Error returns:
 *   SRMECH_ERR_NULL_ARG  — out_n_core / out_k / out_bimodal / hist NULL, out_core_ids
 *                          NULL with core_cap > 0, or node_ids / counts NULL with
 *                          n_nodes > 0.
 *   SRMECH_ERR_OVERFLOW  — hist_cap < 3*(max_count+1), or core_cap too small.
 * Pure integer CARDINALITIES (Class-N): no float, no division, and no abs (a count
 * has no sign to strip — not a Class-K pin-slot site). ADDITIVE plain symbol
 * reusing NO callback typedef -> SRMECH_ABI_VERSION stays 6, GENOME_FORMAT_VERSION
 * stays 15. Caller-arena; no malloc/goto. */
srmech_status_t srmech_genome_conserved_core(
    const uint64_t *node_ids, const uint64_t *counts, size_t n_nodes,
    long k_in, uint64_t *out_core_ids, size_t core_cap, size_t *out_n_core,
    uint64_t *out_k, int *out_bimodal, uint64_t *hist, size_t hist_cap);

/* rc280 (§102 / F1253) — SECTION COUNTS: scan a PLASMID section store and derive
 * {global_id -> n_sections}, the section-occurrence histogram
 * srmech_genome_conserved_core reads. A bare-C host derives it END-TO-END (no
 * Python anywhere in the loop); the pure srmech.biology.plasmid.section_counts body
 * is the byte-parity oracle. The VOCAB karyotype chromosome ("__vocab__") is
 * EXCLUDED, and a node counts ONCE per section (deduped within the section).
 *
 * WHAT MAKES IT FAST (the two rc280 costs, both structural):
 *   1. the store CATALOG is derived ONCE for the whole scan. On a v12 HEAD-ONLY
 *      manifest, deriving it re-reads and re-Merkle-folds the WHOLE body, so
 *      doing it per section — as a per-label window read does — is O(P * body),
 *      quadratic in corpus size, and it dominated everything else measured.
 *   2. per section ONLY the node_ids PREFIX of the region is paged, never the
 *      EDGE bytes (the bulk of a co-occurrence section). NO format change was
 *      needed: the §89 payload int stream is
 *        [vocab_size, n_node_ids] + node_ids + [n_extras] + ... + [n_edges] + ...
 *      so node_ids is a strict PREFIX; quad_turn is a per-leaf REVERSIBLE
 *      Klein-4 XOR (leaf k uncouples from leaf k ALONE, no chaining) so a prefix
 *      of coupled leaves uncouples to exactly the prefix of the symbol stream;
 *      and the region's integrity bound is its LEADING cap, so a prefix of >= 1
 *      block re-hashes the SAME cap_sha256 a whole-region read does. A prefix
 *      read is not a weaker read — it is the same bound over fewer bytes.
 *   Together: O(P^2 * body) -> O(P * node_ids).
 *   dir            : the plasmid section store (a genome dir).
 *   coupling        : the store's shared Klein-4 invariant, leaf_dim bytes.
 *   leaf_dim       : the store's leaf width; >= 52 (the §89 header fits one leaf).
 *   tick/tick_ctx  : §101 heartbeat, fired BETWEEN whole SECTIONS with phase
 *                    SRMECH_PHASE_EXTRACTING, done = sections scanned so far,
 *                    total = P. A NONZERO return CANCELS: SRMECH_CANCELLED is
 *                    returned with the PARTIAL counts still written and *n_done
 *                    set. (A partial count is not a smaller valid count, it is a
 *                    WRONG one — it would shift every downstream conservation
 *                    threshold — so the Python caller RAISES rather than
 *                    returning it. The partial rides out for inspection/resume.)
 *                    NULL = off.
 *   out_ids/out_counts/out_cap : caller arrays; out_ids ASCENDING, out_counts[i]
 *                    the number of DISTINCT sections carrying out_ids[i].
 *   n_out          : out — the distinct-id count. ALWAYS the TRUE required count,
 *                    INCLUDING on SRMECH_ERR_OVERFLOW, so a caller retries at
 *                    exactly the size it needs (a short table would silently
 *                    UNDER-count, and nothing downstream would reveal it).
 *   n_done         : out — sections scanned.
 * Error returns:
 *   SRMECH_ERR_NULL_ARG  — dir / coupling / n_out / n_done NULL, or an out array
 *                          NULL with out_cap > 0.
 *   SRMECH_ERR_BAD_INPUT — leaf_dim < 52 or > 256; a leaf_dim/manifest mismatch;
 *                          a malformed catalog entry; a cap integrity failure; a
 *                          section whose region cannot satisfy its own declared
 *                          n_node_ids.
 *   SRMECH_ERR_OVERFLOW  — out_cap < *n_out (retry at *n_out), OR `ws` was too
 *                          small for the store's catalog / count table (then
 *                          *n_out is 0, which the Python binding reads as a
 *                          DECLINE and runs the pure body — correct, just not
 *                          native).
 *   SRMECH_CANCELLED     — a tick asked to stop (a clean section-boundary partial).
 *
 * REENTRANT (rc306 / task #899 — v9). This call carries NO file-scope static
 * scratch: the count table + the region window are carved off the caller `ws`,
 * and its untouched TAIL is the catalog arena genome_obtain_manifest parses the
 * manifest into. Two threads with DISJOINT `ws` buffers may run it concurrently.
 * (Before rc306 the scratch was three process-global statics — a 32 MiB catalog
 * arena, a 2^18-slot count table, a 64 KiB window — which capped the corpus at
 * ~11,000 chromosomes AND made the call non-reentrant.)
 *   ws / ws_len    : caller workspace. Size it with
 *                    srmech_genome_section_counts_arena_bytes(body_len, n_chroms,
 *                    out_cap): the count table is sized to hold out_cap distinct
 *                    ids (so the table and the out arrays overflow on the SAME
 *                    knob — grow out_cap and re-size ws), and the catalog term
 *                    scales with n_chroms, so there is no compiled-in corpus cap.
 *                    The region window is a fixed SRMECH_GENOME_SC_WINDOW_BYTES
 *                    (64 KiB, must exceed one block, leaf_dim <= 256). A short ws
 *                    leaves *n_out == 0 (the DECLINE above).
 * GENOME_FORMAT_VERSION stays 15 (no on-disk format change). Adding the ws / ws_len
 * params to this EXISTING signature changes its wire format, so SRMECH_ABI_VERSION
 * bumps 8 -> 9 (see the ABI history above). Integer/exact (Class-N); no float, no
 * abs (a count and an id have no sign to strip — not a Class-K pin-slot site); no
 *
 * BOUND (rc342, #T969): a READ - it holds the derive against the head's
 * committed body_sha256 and is SRMECH_ERR_BAD_INPUT on a mismatch. See THE
 * READ-SIDE INTEGRITY BOUND note above srmech_genome_catalog.
 * malloc, no goto, no recursion. */
srmech_status_t srmech_genome_section_counts(
    const char *dir,
    const unsigned char *coupling, uint32_t leaf_dim,
    srmech_progress_tick_cb_t tick, void *tick_ctx,
    void *ws, size_t ws_len,
    uint64_t *out_ids, uint64_t *out_counts, size_t out_cap,
    size_t *n_out, size_t *n_done);

/* rc306 (task #899) — the caller-arena sizing helper for
 * srmech_genome_section_counts, mirroring the other *_arena_bytes helpers.
 * Returns the minimum `ws_len` a scan needs:
 *   body_len : the store's turns.bin byte length (the catalog arena copies it).
 *   n_chroms : the manifest's chromosome count (INCLUDING the vocab karyotype).
 *   out_cap  : the distinct-id capacity the caller sizes its out arrays to; the
 *              internal count table is sized to hold at least this many ids under
 *              the 3/4 open-addressing load bound (floored so a tiny store still
 *              gets real headroom). Grow out_cap (and re-size ws) to census a
 *              corpus with more distinct ids than the default ceiling.
 * The total is: count-table + region-window + the srmech_genome_arena_bytes
 * catalog term + per-carve alignment slop. Pure integer arithmetic. */
size_t srmech_genome_section_counts_arena_bytes(size_t body_len, uint32_t n_chroms,
                                                size_t out_cap);

/* rc279 (§102 / F1252 STAGE 2 — ORGANIZE) — the C-native ORGANIZE orchestrator:
 * PROMOTE the conserved core then MERGE the retained plasmid sections into ONE
 * organized genome (nuclear core + plasmids), so a bare-C host runs stage 2
 * end-to-end (genome-must-exist-in-C). It composes the two stage-2 primitives:
 *   PROMOTE -> srmech_genome_mint_strand (rc277 / G5): the already-packed
 *              conserved-core strand gains a §95a interior CENTROMERE (0x58) at the
 *              metacentric p:q split with a content-addressed orientation, becoming
 *              a Tier-2 NUCLEAR chromosome. It is placed at the HEAD.
 *   MERGE   -> srmech_genome_integrate (rc276 / G4): each retained plasmid section
 *              is spliced in at the chromosome boundary, in order.
 * Because `at < 0` makes integrate a pure TAIL-APPEND, folding it over the P
 * sections is exactly their CONCATENATION (associativity) — so the orchestrator
 * calls the peer at the running write offset and the whole fold is O(total), not
 * the O(P * total) a literal re-splice of the growing host would cost. The
 * width-coherence gate (Class-K equality, NEVER abs) is applied per section.
 *
 * THE INCREMENTAL PATH. This is the op that removes the monolithic from-scratch
 * partition from the encode: stage 2 NEVER calls srmech_laplacian_recursive_cut and
 * never re-extracts. Adding one document = a stage-1 append + an O(section) count
 * bump + a re-mint of the small conserved core; every plasmid section stays
 * byte-untouched.
 *   core / core_blocks : the already-packed conserved-core strand (from
 *                       srmech_graph_kernel_encode over the induced core subgraph +
 *                       the §89 kernel region build). core_blocks == 0 = ONE-DNA-TYPE
 *                       (no core promoted — the plasmids are folded as-is).
 *   plasmids / plasmid_blocks / n_plasmids : the retained sections, CONCATENATED
 *                       block-wise, with the per-section block counts.
 *   leaf_dim / coupling : the coupling width + the shared Klein-4 invariant
 *                       (coupling is leaf_dim bytes; required when core_blocks > 0).
 *   centromere_at / repeats / handle / handle_len : passed through to mint_strand
 *                       (centromere_at < 0 = the metacentric midpoint).
 *   tick / tick_user  : the §101 heartbeat, fired BETWEEN whole chromosomes —
 *                       phase SRMECH_PHASE_MINTING (done 0, total 1) for the core
 *                       promote, then SRMECH_PHASE_INTEGRATING (done = sections
 *                       merged so far, total = n_plasmids) per section. A nonzero
 *                       return CANCELS: *n_blocks_out holds the COMPLETE blocks
 *                       written (a valid, readable partial organized genome — never
 *                       a half-written chromosome), *n_integrated_out the sections
 *                       merged, and SRMECH_CANCELLED is returned. NULL = off.
 *   out / out_cap     : caller buffer; out_cap >= (core_blocks + 1 + sum
 *                       plasmid_blocks) * leaf_dim.
 *   n_blocks_out      : out — the organized block count.
 *   n_integrated_out  : out — the sections merged (== n_plasmids unless cancelled).
 *   ws / ws_len       : the mint scratch; ws_len >= (core_blocks + 1) * leaf_dim
 *                       (read only when core_blocks > 0).
 * BYTE-IDENTICAL to the pure Python genome_integrate_plasmids (same derived core,
 * same minted centromere bytes, same section order).
 * Error returns:
 *   SRMECH_ERR_NULL_ARG  — out / n_blocks_out / n_integrated_out NULL, plasmids or
 *                          plasmid_blocks NULL with n_plasmids > 0, or core / ws /
 *                          coupling NULL with core_blocks > 0.
 *   SRMECH_ERR_BAD_INPUT — leaf_dim 0 / > 256, or a section not opening with a
 *                          chromosome-boundary cap (from the integrate peer).
 *   SRMECH_ERR_OVERFLOW  — out_cap or ws_len too small.
 *   SRMECH_CANCELLED     — the tick asked to stop (a clean chromosome-boundary partial).
 * ADDITIVE plain symbol REUSING the existing srmech_progress_tick_cb_t typedef (no
 * NEW typedef) -> SRMECH_ABI_VERSION stays 6, GENOME_FORMAT_VERSION stays 15.
 * Caller-arena; no malloc/goto/abs/float. */
srmech_status_t srmech_genome_integrate_plasmids(
    const unsigned char *core, size_t core_blocks,
    const unsigned char *plasmids, const size_t *plasmid_blocks, size_t n_plasmids,
    uint32_t leaf_dim, const unsigned char *coupling,
    long centromere_at, uint32_t repeats,
    const unsigned char *handle, size_t handle_len,
    srmech_progress_tick_cb_t tick, void *tick_user,
    unsigned char *out, size_t out_cap, size_t *n_blocks_out,
    size_t *n_integrated_out, unsigned char *ws, size_t ws_len);

/* rc334 (§102 / F1252 — INCREMENTAL STAGE 1+2, task #887) — ADD PLASMID: the
 * whole-op C peer of srmech.biology.plasmid.add_plasmid and the LAST genome wire-glue
 * parity gap. It CLOSES the ADR-0003 "genome must exist fully in C" commitment — the
 * enumerated wire-glue gap list (CEIL_WIRE_GLUE_GAPS) drops 1 -> 0.
 *
 * The Python projection owns the stage-1 APPEND (srmech_genome_plasmid_extract, which
 * seeds a fresh store + refreshes the "__vocab__" karyotype index — the seed + vocab
 * bookkeeping is not this op's job), then hands this peer the store (new section
 * ALREADY appended), the PRIOR section-count accumulator, the NEW section's GLOBAL
 * node_ids, and k. This peer runs the CONSERVE + ORGANIZE half END-TO-END:
 *   (1) MERGE   — prior {id:count} + the new section ids (+1 each; a node counts ONCE
 *                 per section) -> the ascending merged counts. Byte-identical to the
 *                 pure O(section) dict bump.
 *   (2) CONSERVE— srmech_genome_conserved_core over the merged counts (k_in < 0 DERIVES
 *                 k from the antimode; >= 0 forces it). *out_core the ASCENDING
 *                 conserved node ids, *out_k / *out_bimodal the threshold + its shape.
 *   (3) HARVEST + PROMOTE — page every plasmid section off disk, decode its GLOBAL
 *                 edges (srmech_graph_kernel_decode), keep the induced CORE subgraph
 *                 (both endpoints conserved), SUM the per-(u,v) multiplicities in
 *                 canonical sorted order (ORDER-FREE), and pack it
 *                 (srmech_graph_kernel_encode -> the kernel BLOCK form) into a core
 *                 strand — byte-identical to the pure _core_packed.
 *   (4) MERGE the strand — MINT the core (0x58 centromere) at the head, then FOLD each
 *                 retained plasmid section's strand (paged + unpacked off disk) onto
 *                 the running TAIL, the srmech_genome_integrate_plasmids discipline
 *                 (mint_strand promote + integrate merge).
 * A global recursive_cut is NEVER run and no document is re-extracted. BYTE-IDENTICAL
 * to the pure add_plasmid `strand` + `state` (the section_count map, the core, k).
 *   dir / coupling / leaf_dim : the section store + its shared Klein-4 invariant
 *                       (coupling is leaf_dim bytes; leaf_dim in [52, 256]).
 *   k_in                : < 0 DERIVE the conservation threshold; >= 0 force it.
 *   prior_ids/prior_counts/n_prior : the PRIOR ascending section-count accumulator.
 *   new_nid / n_new     : the new section's UNIQUE GLOBAL node_ids (+1 each).
 *   prior_core/n_prior_core : the PRIOR conserved core (for *out_core_changed).
 *   centromere_at/repeats/handle/handle_len : mint_strand params for the core promote
 *                       (centromere_at < 0 = the metacentric midpoint; the defaults
 *                       MUST match the pure mint_strand, i.e. repeats=15, handle="cen").
 *   tick/tick_ctx       : §101 heartbeat — MINTING once for the core, then INTEGRATING
 *                       per section; a nonzero return CANCELS at a chromosome boundary
 *                       (*out_cancelled = 1, SRMECH_CANCELLED, *out_nblocks a clean
 *                       partial). NULL = off.
 *   out_ids/out_counts/counts_cap/n_counts : the NEW ascending merged counts
 *                       (counts_cap >= n_prior + n_new is always sufficient).
 *   out_core/core_cap/n_core_out : the NEW conserved core (core_cap >= n_counts).
 *   out_k/out_bimodal/out_core_changed : the derived threshold, its shape, and 1 iff
 *                       the core membership moved from prior_core.
 *   out/out_cap/out_nblocks : the organized strand as leaf_dim-byte HV blocks.
 *   n_integrated        : the plasmid sections merged (== the section count unless
 *                       cancelled).
 *   ws/ws_len           : the MANIFEST arena (>= srmech_genome_arena_bytes(body_len,
 *                       n_chroms, 0); the tree persists across the section passes).
 *   scratch/scratch_len : the ORGANIZE scratch (>= srmech_genome_add_plasmid_scratch_bytes;
 *                       SRMECH_ERR_OVERFLOW when short — the op appends NOTHING, so a
 *                       larger re-run is idempotent).
 * Error returns: SRMECH_ERR_NULL_ARG (a required pointer NULL), SRMECH_ERR_BAD_INPUT
 * (leaf_dim out of range / a manifest-mismatch / a malformed section), SRMECH_ERR_OVERFLOW
 * (an out buffer or arena too small), SRMECH_CANCELLED (a tick asked to stop).
 * ADDITIVE — two new plain symbols REUSING the existing srmech_progress_tick_cb_t
 * typedef (NO new callback typedef): SRMECH_ABI_VERSION stays 10, GENOME_FORMAT_VERSION
 * stays 19 (no on-disk format change — plain v15-era KERNEL chromosomes). Caller-arena;
 *
 * NOT AN INTEGRITY GATE (rc342, #T969): a MUTATION - it obtains the manifest
 * MID-EDIT, so it is deliberately NOT bound against the committed body_sha256
 * (that would police a transient window; rc337 measured 22 Windows failures).
 * Bound one layer up in the scripting projection. See THE READ-SIDE INTEGRITY
 * BOUND note above srmech_genome_catalog.
 * no malloc/goto/recursion/abs/float. */
srmech_status_t srmech_genome_add_plasmid(
    const char *dir, const unsigned char *coupling, uint32_t leaf_dim, long k_in,
    const uint64_t *prior_ids, const uint64_t *prior_counts, size_t n_prior,
    const uint64_t *new_nid, size_t n_new,
    const uint64_t *prior_core, size_t n_prior_core,
    long centromere_at, uint32_t repeats,
    const unsigned char *handle, size_t handle_len,
    srmech_progress_tick_cb_t tick, void *tick_ctx,
    uint64_t *out_ids, uint64_t *out_counts, size_t counts_cap, size_t *n_counts,
    uint64_t *out_core, size_t core_cap, size_t *n_core_out,
    uint64_t *out_k, int *out_bimodal, int *out_core_changed,
    unsigned char *out, size_t out_cap, size_t *out_nblocks,
    size_t *n_integrated, uint32_t *out_cancelled,
    void *ws, size_t ws_len, void *scratch, size_t scratch_len);

size_t srmech_genome_add_plasmid_scratch_bytes(size_t body_len, size_t n_new,
                                               uint32_t leaf_dim);

/* rc281 (§135 / F1251 — the GENE COPY-NUMBER pair) — WRITE a gene's copy number.
 *
 * rc273 shipped `amplify` / `copy_number_of` in Python only, on the reasoning that the
 * copy-number field is TRANSPARENT to every existing C reader (srmech_genome_gene_express
 * returns on the 0x47 marker before reading any field, so no C change was needed to keep
 * reading an amplified genome). That is true and it is NOT parity: transparent-to-readers
 * is not the same as C-host-standalone. Without these two symbols a bare-C host can neither
 * SET nor GET the copy-number axis — it can only ignore it. This pair closes that gap
 * (the c_host_parity_audit_rc273 G6 exhibit), so ADR-0003 holds for the whole §135 surface.
 *
 * Walk `strand` (`n_blocks` fixed-width `leaf_dim`-byte blocks), find the FIRST PLAIN GENE
 * cap (0x47) whose inline label equals `label`, and write to `out` a strand of the SAME
 * n_blocks in which ONLY that cap is rewritten to carry `n` — every other block, and the
 * matched gene's own data turns, are byte-copied unchanged. The strand LENGTH is unchanged:
 * `n` is a MULTIPLICITY (an annotation on the ONE gene), never N duplicated strands.
 *
 * `n == 1` (the default present-once) writes the PLAIN cap — byte-identical to a gene that
 * was never amplified — so amplifying to 1 is an identity-shaped rewrite that spends no
 * wire. Only `n >= 2` spends the 8-byte field. Byte-identical to the Python
 * srmech.biology.genome.amplify for every (label, n, leaf_dim).
 *
 * `out_cap` must be >= n_blocks * leaf_dim. Returns SRMECH_ERR_BAD_INPUT if `n` is 0 (a
 * gene is present at least once — a multiplicity is never signed, so there is nothing to
 * strip and this is NOT a Class-K pin-slot site: it is a domain gate), if no plain gene
 * named `label` is in the strand, or if the label + field would not fit `leaf_dim`.
 * ADDITIVE plain symbol (no new typedef) — SRMECH_ABI_VERSION stays 6,
 * SRMECH_GENOME_FORMAT_VERSION stays 15 (rc273's field is already in the format).
 * Integer/exact (Class-I/N); no float, no abs, no malloc, no goto, no recursion. */
srmech_status_t srmech_genome_amplify(
    const unsigned char *strand, size_t n_blocks, uint32_t leaf_dim,
    const unsigned char *label, size_t label_len, uint64_t n,
    unsigned char *out, size_t out_cap);

/* rc281 (§135 / F1251) — READ a gene's copy number: the inverse of srmech_genome_amplify
 * and the C peer of srmech.biology.genome.copy_number_of.
 *
 * Walk `strand`, find the FIRST PLAIN GENE cap (0x47) whose inline label equals `label`,
 * and write its exact copy number to *count_out: the uint64 big-endian value carried right
 * after the label's NUL, or 1 when the field is absent. ABSENT means any of: all-NUL
 * padding (a plain, never-amplified gene), a pre-rc273 genome, no label NUL inside the
 * leaf, or a leaf too narrow to hold the field — every one of those reads as 1
 * (present-once, the DEFAULT), which is what makes the field back-compatible.
 *
 * A pure READ — `strand` is untouched. Returns SRMECH_ERR_BAD_INPUT if no plain gene named
 * `label` is in the strand (a caller distinguishes "absent gene" from "gene present once",
 * exactly as the Python raises rather than returning 0). ADDITIVE plain symbol —
 * SRMECH_ABI_VERSION stays 6, SRMECH_GENOME_FORMAT_VERSION stays 15. Integer/exact
 * (Class-I/N); no float, no abs, no malloc, no goto, no recursion. */
srmech_status_t srmech_genome_copy_number(
    const unsigned char *strand, size_t n_blocks, uint32_t leaf_dim,
    const unsigned char *label, size_t label_len, uint64_t *count_out);

/* srmech_eulerian_walk — #1390 item 3: the Hierholzer Eulerian trail /
 * circuit over a DIRECTED integer-node edge multiset [0, n_nodes). start < 0
 * = auto (min out-bearing node for a circuit; the unique out=in+1 node for a
 * path); circuit_only rejects a non-circuit. On out_feasible == 1, out_walk
 * holds *out_walk_len == n_edges+1 nodes; out_feasible == 0 is the pure `None`
 * (degree-infeasible / disconnected). Caller arenas: outdeg/indeg/cur are
 * n_nodes, adj_start is n_nodes+1, adj is n_edges, stack/out_walk are
 * n_edges+1. Byte-identical to the pure eulerian_path/eulerian_circuit (same
 * order: adjacency filled in edge order, consumed from the END). ADDITIVE —
 * SRMECH_ABI_VERSION stays 5. */
srmech_status_t srmech_eulerian_walk(
    const uint64_t *edge_u, const uint64_t *edge_v, size_t n_edges,
    uint64_t n_nodes, int64_t start, int circuit_only,
    uint64_t *outdeg, uint64_t *indeg, size_t *adj_start, size_t *cur,
    uint64_t *adj, uint64_t *stack, uint64_t *out_walk, size_t *out_walk_len,
    int *out_feasible);

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

/* srmech_toml_parse_arena_bytes (0.9.0rc391) — return a SAFE upper bound, in
 * bytes, for the `ws` arena srmech_toml_parse needs to parse a `src_len`-byte
 * document. Both the transient builder tree (arena-linked tables + per-key
 * entries + NUL-terminated key/string copies) and the finalised right-sized
 * value tree coexist in `ws`, so the bound is linear in the source length plus
 * a fixed floor for a tiny document. This is exactly the parse-only budget
 * srmech_dsl_toml_chain_to_json already carves for its internal
 * srmech_toml_parse call, so the figure is proven-safe in production. A caller
 * that still meets SRMECH_ERR_OVERFLOW on a pathological many-tiny-keys doc may
 * grow and retry. ABI-additive: a new symbol, so SRMECH_ABI_VERSION stays 10. */
size_t srmech_toml_parse_arena_bytes(size_t src_len);

/* Parse src[0..len) into a TOML tree built ENTIRELY inside the caller's
 * arena `ws` (ws_len bytes, used as an 8-byte-aligned bump allocator).
 * On success *out is the root TABLE value (which lives in ws). No malloc.
 *
 * Returns:
 *   SRMECH_OK             — success (*out set)
 *   SRMECH_ERR_NULL_ARG   — src (with len > 0), ws, or out is NULL
 *   SRMECH_ERR_OVERFLOW   — caller arena `ws` too small for this document.
 *                           GROW IT AND RETRY; this call may then succeed.
 *   SRMECH_ERR_LIMIT      — rc404 (`#T1069`): a bound no arena relieves —
 *                           nesting past SRMECH_TOML_MAX_DEPTH, an integer
 *                           outside int64, a saturated size computation, or a
 *                           fixed digit/key-segment capacity. DO NOT RETRY.
 *                           These returned SRMECH_ERR_OVERFLOW through rc403,
 *                           so a grow-loop burned every doubling to the cap
 *                           first — measured 13 calls / ~537 MiB on an
 *                           out-of-int64 literal, for a correct answer.
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

/* q = floor(a / d), *rem = a - q*d in [0, d) — the SINGLE-LIMB-DIVISOR peer of
 * srmech_bigint_divmod (SAME Python-FLOOR convention), for a small (uint32_t)
 * divisor. Computes the quotient one limb at a time, so it needs NO `ws` and no
 * per-divisor bigint allocation — the fast path for trial-division / factor-out /
 * radix conversion. d != 0 else SRMECH_ERR_BAD_INPUT; q->cap must hold a->n (+1
 * for the negative-dividend floor carry) else OVERFLOW. ABI-additive: a new
 * symbol, so SRMECH_ABI_VERSION stays 5. */
srmech_status_t srmech_bigint_divmod_small(srmech_bigint_t *q, uint32_t *rem,
                                           const srmech_bigint_t *a, uint32_t d);

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
 * srmech_carrier_marshal — the NESTED exact-ℚ carrier OPERAND marshal
 * (0.9.0rc191; the #796 LINCHPIN foundation). The bignum-safe reader that
 * lowers the MCP nested-ℚ wire form of the §76 "telescope" reducer operands
 * (the exact-ℚ carriers Poly / BiPoly) into arena-backed srmech_bigint
 * coefficient arrays — extending the rc176 srmech_infer.c `inf_read_poly`
 * pattern ONE nesting level per carrier, in a REUSABLE form the rc192
 * srmech_infer.c wiring calls to dispatch the deferred exact #796 infer rows
 * (sigma-definite / q / elliptic) for a bare-C host.
 *
 * NOT the rc188 invoke_tool VTABLE: the §76 reducer kernels need MB–GB caller
 * workspaces (srmech_gosper ~9 MB, srmech_wz_verify ~32 MB, srmech_zeilberger
 * ~470 MB), sized by srmech_infer_arena_bytes (~41 MB); the vtable arena
 * (256*params_len + 65536 ~ 114 KB, JPL Rule 3 no-malloc) cannot host them, so
 * a reducer's home is the srmech_infer.c DECISION path, not the vtable.
 *
 * WIRE FORM: a COEFFICIENT is a bare integer c (den 1) OR a [num,den] 2-list;
 * each scalar is a JSON int64 OR a decimal STRING (the bignum transport, since
 * srmech_json's strtoll clamps a >int64 literal). A Poly is an ascending-degree
 * LIST of coefficients; a BiPoly is a k-ascending LIST of Poly-in-n, lowered to
 * FLAT (k-then-n) num/den arrays + klen[] + the k-degree slot count kdeg. The
 * reader lands the operand VERBATIM (no reduce/normalise); a malformed node ->
 * SRMECH_ERR_BAD_INPUT (the Python caller runs the COMPLETE pure path).
 * Additive symbols -> SRMECH_ABI_VERSION stays 4. ------- */

/* Carrier kinds for srmech_carrier_marshal_roundtrip. */
#define SRMECH_CARRIER_POLY     0  /* ascending-degree coefficient list        */
#define SRMECH_CARRIER_BIPOLY   1  /* k-ascending list of Poly-in-n (flat+klen) */
#define SRMECH_CARRIER_SCALAR   2  /* a single coefficient (EllRatio scalar)   */
#define SRMECH_CARRIER_TRIPOLY  3  /* j-list of k-lists of n-coeff lists (rc223) */
#define SRMECH_CARRIER_QBIPOLY  4  /* Y-list of [x_low, [q-run, ...]] (rc223)   */
#define SRMECH_CARRIER_ELLRATIO 5  /* the pre-interned EllRatio wire (rc223)    */

/* Minimum caller-arena BYTES for a `json_len`-byte carrier relationship. No
 * malloc; the caller owns the arena. Too small -> SRMECH_ERR_OVERFLOW. */
size_t srmech_carrier_marshal_arena_bytes(size_t json_len);

/* Read a Poly wire node (an ascending-degree coefficient ARRAY) into parallel
 * numerator / denominator bigint arrays of `cap` limbs each (carved off `a`).
 * *out_len is the coefficient count. A non-array node / malformed coefficient
 * -> SRMECH_ERR_BAD_INPUT; arena exhaustion -> SRMECH_ERR_OVERFLOW; a NULL
 * param -> SRMECH_ERR_NULL_ARG. (Public: rc192 srmech_infer.c reuse.) */
srmech_status_t srmech_carrier_read_poly(const srmech_json_value_t *node,
                                         srmech_marshal_arena_t *a, uint32_t cap,
                                         srmech_bigint_t **out_num,
                                         srmech_bigint_t **out_den,
                                         size_t *out_len);

/* Read a BiPoly wire node (a k-ascending ARRAY of Poly-in-n coefficient
 * arrays) into FLAT (k-then-n) numerator / denominator bigint arrays + the
 * per-k length array *out_klen (length *out_kdeg). The flat length is the sum
 * of the klen entries. Same error contract as srmech_carrier_read_poly. The
 * exact encoding srmech_zeilberger / srmech_wz_verify consume. (Public.) */
srmech_status_t srmech_carrier_read_bipoly(const srmech_json_value_t *node,
                                           srmech_marshal_arena_t *a, uint32_t cap,
                                           srmech_bigint_t **out_num,
                                           srmech_bigint_t **out_den,
                                           size_t **out_klen, size_t *out_kdeg);

/* Read a TriPoly wire node (a j-ascending ARRAY of k-ascending ARRAYs of
 * ascending-n coefficient arrays — the apagodu_zeilberger._tri_pairs bridge
 * form, rc223) into FLAT (j-major, then k, then n) numerator / denominator
 * bigint arrays + the per-(j,k)-cell length array *out_nlen (length
 * (*out_jdeg) * (*out_kdeg); a ragged j-block is padded with empty runs to the
 * max k-count, mirroring the Python _az_tri_flatten rectangularisation). The
 * exact encoding srmech_apagodu_zeilberger consumes. Same error contract as
 * srmech_carrier_read_poly. (Public: rc223 srmech_infer.c reuse.) */
srmech_status_t srmech_carrier_read_tripoly(const srmech_json_value_t *node,
                                            srmech_marshal_arena_t *a, uint32_t cap,
                                            srmech_bigint_t **out_num,
                                            srmech_bigint_t **out_den,
                                            size_t **out_nlen, size_t *out_jdeg,
                                            size_t *out_kdeg);

/* Read a QBiPoly wire node (a Y-ascending ARRAY of [x_low, rows] pairs — the
 * qbipoly._qb_pairs bridge form lowered to JSON, rc223: x_low a JSON int, rows
 * an x-ascending ARRAY of ascending-q coefficient arrays) into the flat
 * (Y-major then X-major) q-run bigint arrays + the per-(Y,X)-cell *out_qlen +
 * the per-Y-cell *out_xlow / *out_xcells + the Y-cell count *out_ycells — the
 * exact bridge encoding srmech_q_zeilberger / srmech_q_wz_verify /
 * srmech_q_gosper consume (a QPoly rides as ONE Y-cell). Same error contract
 * as srmech_carrier_read_poly. (Public: rc223 srmech_infer.c reuse.) */
srmech_status_t srmech_carrier_read_qbipoly(const srmech_json_value_t *node,
                                            srmech_marshal_arena_t *a, uint32_t cap,
                                            srmech_bigint_t **out_num,
                                            srmech_bigint_t **out_den,
                                            size_t **out_qlen, int64_t **out_xlow,
                                            size_t **out_xcells,
                                            size_t *out_ycells);

/* The PRE-INTERNED EllRatio wire (rc223) — the srmech_elliptic_* wire form
 * lifted to a struct: the interned symbol-table dimension n_syms; the
 * x/p/q/y/N/K interned indices (-1 if absent); the num / den theta counts; the
 * flat exact-Q monomial coefficient arrays (1 + n_num + n_den entries, in the
 * order prefactor, num0.., den0..); the flat int32 exponent rows (int32[n_syms]
 * per monomial, same order). */
typedef struct srmech_ellratio_wire {
    size_t n_syms;
    int xsym; int psym; int qsym; int ysym; int nsym; int ksym;
    size_t n_num; size_t n_den;
    srmech_bigint_t *coeff_num;      /* 1 + n_num + n_den                      */
    srmech_bigint_t *coeff_den;
    int32_t *exps_flat;              /* (1 + n_num + n_den) * n_syms           */
} srmech_ellratio_wire_t;

/* Read an EllRatio wire node (a JSON OBJECT with n_syms / xsym / psym / qsym /
 * ysym / nsym / ksym / n_num / n_den int fields + coeff_num / coeff_den scalar
 * arrays (int64 or decimal string — the bignum transport) + exps int rows —
 * the interning done Python-side, sorted-symbol order, so the reader is a pure
 * array lowering) into arena-backed bigint coefficient arrays + the flat int32
 * exponent rows. Same error contract as srmech_carrier_read_poly. (Public:
 * rc223 srmech_infer.c reuse.) */
srmech_status_t srmech_carrier_read_ellratio(const srmech_json_value_t *node,
                                             srmech_marshal_arena_t *a,
                                             uint32_t cap,
                                             srmech_ellratio_wire_t *out);

/* The round-trip PROVER: parse `json`, marshal the `kind` carrier, and
 * re-serialise it to CANONICAL nested-ℚ JSON (each coefficient as [num,den]
 * decimal, compact separators) into `out` (capacity `out_cap`; NO trailing
 * NUL) with *out_len set. Proves the reader landed every (bignum) coefficient
 * value + the nesting, byte-identical to the Python carrier's coefficient
 * view, with a SMALL arena (srmech_carrier_marshal_arena_bytes). A malformed
 * node / too-small out -> the matching error (the caller defers to pure). */
srmech_status_t srmech_carrier_marshal_roundtrip(int kind, const char *json,
                                                 size_t json_len,
                                                 void *ws, size_t ws_len,
                                                 char *out, size_t out_cap,
                                                 size_t *out_len);

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
 * srmech.math.rational.{exp,sin,cos,log1p,atan}_series_truncate /
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
/* ------------------------------------------------------------------ *
 * srmech_bessel_j_fixed_big — FIXED-POINT Bessel J_k (v0.9.0rc362).
 *
 * The C peer of srmech.music.bessel_j_fixed: the DLMF 10.2.2 / Watson (1922)
 * Sec 3.1 ascending series J_k(x) = SUM_m (-1)^m (x/2)^(2m+k) / (m!(m+k)!),
 * summed by an exact integer recurrence on a DECLARED 2^-scale_bits grid.
 * `out_num` is the value over the IMPLICIT denominator 2^scale_bits.
 *
 * Unlike its *_series_truncate_big siblings (which return an exact REDUCED
 * rational), this returns a fixed-point value — the contract the membrane
 * spectrum needs and the one the Python computes. Bit-identical to Python by
 * construction: the running term is a NON-NEGATIVE magnitude and the series
 * alternation is an explicit orientation applied at the accumulation, so no
 * shift or divide ever sees a negative operand and C truncation and Python
 * floor cannot diverge.
 *
 * Domain: order <= 64, x_num->sign >= 0 (the real-axis half-line; use
 * J_k(-x) = (-1)^k J_k(x) for the other), x_den->sign > 0, scale_bits in
 * [8, 4096]. Out-of-domain -> SRMECH_ERR_BAD_INPUT, matching the Python
 * ValueError domain so C and Python accept the SAME inputs. NO transcendence
 * claim is made about any Bessel zero.
 *
 * Carrier-internal (like srmech_pi): NOT a Rosetta ledger op. Additive
 * symbols -> SRMECH_ABI_VERSION unchanged.
 * ------------------------------------------------------------------ */

/* Minimum `ws_len` BYTES for srmech_bessel_j_fixed_big at the given input
 * limb sizes, scale and order. 8-byte-aligned uint32 bump arena. */
size_t srmech_bessel_j_fixed_ws_bound(size_t num_limbs, size_t den_limbs,
                                      uint32_t scale_bits, uint32_t order);

srmech_status_t srmech_bessel_j_fixed_big(uint32_t order,
                                          const srmech_bigint_t *x_num,
                                          const srmech_bigint_t *x_den,
                                          uint32_t scale_bits,
                                          srmech_bigint_t *out_num,
                                          void *ws, size_t ws_len);

srmech_status_t srmech_rational_pow_uint_big(const srmech_bigint_t *base_num,
                                             const srmech_bigint_t *base_den,
                                             uint32_t exp_val,
                                             srmech_bigint_t *out_num,
                                             srmech_bigint_t *out_den,
                                             void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_the_one — the S(sigma, theta) ADJOINT generator (rc138; #743).
 *
 * The C peer for srmech.cascade.one.the_one's exact-rational ADJOINT
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
 * srmech_one_scalar / srmech_one_matrix — the One-family COMPUTE leaf ops
 * (0.9.0rc195; the make_class -> C arc, #887). C peers of the one.toml [class]
 * One accessor ops srmech.cascade.to_scalar / one_matrix: they COMPOSE
 * srmech_the_one (regenerate the 14 exact adjoint rationals) then assemble
 * exactly like One.to_scalar / One.to_matrix, so a bare-C host runs the object
 * model's scalar / matrix methods with no per-method Python shell-out.
 *
 * sigma in {+1,-1} (Class-K/C chirality; a sign is applied by negating the
 * sign-magnitude numerator, never abs()). theta_den->sign must be > 0. num_terms
 * <= 50. Additive symbols -> SRMECH_ABI_VERSION stays 4. See c/src/srmech_one.c.
 * ------------------------------------------------------------------ */

/* Minimum ws_len BYTES for srmech_one_scalar with theta rationals of the given
 * limb sizes + N terms (8-byte-aligned uint32 bump arena: the 14 flat carriers +
 * the scalar-accumulation scratch + the srmech_the_one series scratch). */
size_t srmech_one_scalar_ws_bound(size_t num_limbs, size_t den_limbs,
                                  uint32_t num_terms);

/* The scalar projection of S(sigma, theta_num/theta_den) to N terms:
 *   mode 0 (trace)     Tr G = 3 + 3*sigma + 8*sigma*cos(theta), EXACT (num,den)
 *   mode 1 (sqnorm)    Sum (num/den)^2 over the 14 state rationals, EXACT
 *   mode 2 (component) the `index`-th (0..13) of the 14 exact rationals
 * out_num/out_den receive the reduced exact rational (positive denominator) —
 * BYTE-IDENTICAL to the pure Python One.to_scalar (the as_float terminal cast
 * stays in the caller). Bad sigma / theta_den <= 0 / num_terms > 50 / mode / index
 * -> SRMECH_ERR_BAD_INPUT; too-small out cap or ws -> SRMECH_ERR_OVERFLOW. */
srmech_status_t srmech_one_scalar(int32_t sigma,
                                  const srmech_bigint_t *theta_num,
                                  const srmech_bigint_t *theta_den,
                                  uint32_t num_terms, int32_t mode, int32_t index,
                                  srmech_bigint_t *out_num,
                                  srmech_bigint_t *out_den,
                                  void *ws, size_t ws_len);

/* Minimum ws_len BYTES for srmech_one_matrix (the 14 flat carriers + the
 * bignum-rational->double scratch + the srmech_the_one series scratch). */
size_t srmech_one_matrix_ws_bound(size_t num_limbs, size_t den_limbs,
                                  uint32_t num_terms);

/* The 14x14 block-diagonal float operator G(sigma,theta) = (+)_n (1 (+) sigma
 * R_n(theta)) written into `out` as ONE_DIM*ONE_DIM = 196 row-major doubles
 * (out_count must be >= 196). cos/sin are the exact flat rationals CORRECTLY-
 * ROUNDED to double (round-half-to-even — the SAME nearest binary64 CPython
 * int/int returns), then the +-1 / +-cos / +-sin tile is placed with NO float
 * accumulation (FMA-safe). BYTE-IDENTICAL to the pure Python One.to_matrix
 * (rc331; #948) — each cell is the bit-exact double the pure cn/cd division
 * yields; the rounding is a dynamic-shift bignum divmod + round-half-even + an
 * exact power-of-two IEEE assembly (libm-free, deterministic cross-platform).
 * Bad sigma / theta_den <= 0 / num_terms > 50 -> SRMECH_ERR_BAD_INPUT; out_count
 * < 196 or too-small ws -> SRMECH_ERR_OVERFLOW. */
srmech_status_t srmech_one_matrix(int32_t sigma,
                                  const srmech_bigint_t *theta_num,
                                  const srmech_bigint_t *theta_den,
                                  uint32_t num_terms, double *out, size_t out_count,
                                  void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_jacobi — BIGNUM-EXACT Jacobi elliptic sn/cn/dn Maclaurin truncation
 * (the C peer of srmech.math.rational.jacobi_sncndn_series_truncate).
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
 * (the C peer of srmech.math.poly.Poly; the §76 telescope Sigma-row prover's
 * foundation carrier).
 *
 * A polynomial is two parallel caller-owned srmech_bigint arrays in ASCENDING
 * degree: nums[i] / dens[i] is the exact-rational coefficient of x^i (dens[i] >
 * 0, gcd(|nums[i]|, dens[i]) == 1; zero coefficient = 0/1). `n` is the
 * coefficient count; the CANONICAL form trims trailing-zero (high-degree)
 * coefficients, so the zero polynomial has n == 0. Each op computes the SAME
 * exact rational coefficients srmech.math.poly.Poly computes (Class-N rational
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
 * srmech.cascade.matrix_cascades.factor_integer_poly (Qalg TAIL Batch 8).
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
 * srmech_lll_reduce — EXACT-ℚ LLL lattice-basis reduction (the C peer of
 * srmech.cascade.matrix_cascades.lll_reduce; the foundation for a future
 * van Hoeij polynomial-factorization knapsack). Classic Lenstra–Lenstra–Lovász
 * (1982): Gram–Schmidt orthogonalization in EXACT ℚ over srmech_bigint (μ_{i,j},
 * ‖b*_i‖² as num/den pairs), size reduction by exact nearest-integer rounding of
 * μ (round(a/b) = floor((2a+b)/(2b)); the |μ| ≤ 1/2 guard a Class-K sign branch
 * on 2·|num| vs den — never an ALU abs), and the Lovász swap on the exact ℚ
 * condition ‖b*_k‖² ≥ (δ − μ²_{k,k−1})·‖b*_{k−1}‖². Integer-in, integer-out;
 * NO float, NO libm. The GSO is recomputed from the current integer basis each
 * outer step (a pure function of the basis → byte-identical to the Python pure
 * body, which is the parity oracle + the no-native fallback).
 *
 * `basis`  : m*n input row-major integer matrix (m rows × n cols; the lattice
 *            basis — an INDEPENDENT basis). Each srmech_bigint an exact integer.
 * m, n     : rows / cols (m >= 0, n >= 0). m <= 1 copies the input to `out`.
 * delta_*  : the Lovász parameter δ = delta_num/delta_den, an exact rational in
 *            (1/4, 1] (delta_num*4 > delta_den && delta_num <= delta_den &&
 *            delta_den > 0), else SRMECH_ERR_BAD_INPUT.
 * out      : m*n row-major integer matrix (caller-owned; each srmech_bigint
 *            pre-bound to >= srmech_lll_reduce_entry_cap limbs) — the reduced
 *            basis, same lattice (unimodular; det = ±1).
 * ws,ws_len: caller arena (>= srmech_lll_reduce_ws_bound BYTES; 8-byte-aligned).
 *
 * Errors: SRMECH_ERR_NULL_ARG (a required pointer NULL with m*n > 0);
 * SRMECH_ERR_BAD_INPUT (δ out of range, or a linearly dependent / degenerate
 * basis — a vanishing ‖b*_j‖²); SRMECH_ERR_OVERFLOW (arena / out slot too small
 * → the Python falls back to its byte-identical pure body). Additive symbols ->
 * SRMECH_ABI_VERSION unchanged (stays 4).
 * ------------------------------------------------------------------ */

/* Per-entry limb cap the caller must give each srmech_bigint in the `out`
 * matrix (and internally each working carrier). `maxbits` = the max bit length
 * of any input entry. Generous determinant-Hadamard envelope; overflow is a
 * clean SRMECH_ERR_OVERFLOW, never a silent wrap. */
size_t srmech_lll_reduce_entry_cap(int m, int n, int maxbits);

/* Minimum `ws_len` BYTES: the working integer basis (m*n) + the μ matrix (m*m,
 * num+den) + the ‖b*‖² vector (m, num+den) + the scalar Q carriers + the
 * gcd/divmod scratch tail, each at the entry cap. 8-byte-aligned uint32 arena. */
size_t srmech_lll_reduce_ws_bound(int m, int n, int maxbits);

/* The reduction. See the block comment above. */
srmech_status_t srmech_lll_reduce(
    const srmech_bigint_t *basis, int m, int n,
    int32_t delta_num, int32_t delta_den,
    srmech_bigint_t *out, void *ws, size_t ws_len);

/* rc222 — EXACT Gram–Schmidt squared norms ‖b*_i‖² of the integer basis
 * `basis` (m rows × n cols, row-major), written as reduced num/den pairs into
 * out_num/out_den (m slots each, pre-bound to >= srmech_lll_reduce_entry_cap
 * limbs; den > 0). The van Hoeij knapsack recombination's |V*_k| > M cutoff
 * (LLL-paper (1.11)) reads these. `ws` sized by srmech_lll_reduce_ws_bound
 * (a superset of the GSO-only need). Errors: SRMECH_ERR_NULL_ARG /
 * SRMECH_ERR_BAD_INPUT (linearly dependent basis) / SRMECH_ERR_OVERFLOW.
 * Additive symbol -> SRMECH_ABI_VERSION unchanged (stays 4). */
srmech_status_t srmech_lll_gso_normsq(
    const srmech_bigint_t *basis, int m, int n,
    srmech_bigint_t *out_num, srmech_bigint_t *out_den,
    void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_unary_theta — the EXACT-INTEGER q-series of a UNARY THETA SERIES (the
 * C peer of srmech.apokatastasis.unary_theta.UnaryTheta; the first WEIGHT-GRADED operand
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
 * (the C peer of srmech.apokatastasis.eta_quotient.EtaQuotient; a WEIGHT-axis operand
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
 * SERIES E_k (the C peer of srmech.apokatastasis.eisenstein.Eisenstein; the SECOND rung
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
 * srmech.apokatastasis.quasimodular_forms_ring). SRMECH_ERR_BAD_INPUT on n_terms<1 / k<2 /
 * k odd / a NULL pointer; SRMECH_ERR_OVERFLOW if a coefficient or the arena is too
 * small. */
srmech_status_t srmech_eisenstein_qseries(
    size_t k, size_t n_terms, srmech_bigint_t *out_num, srmech_bigint_t *out_den,
    size_t *out_len, void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_modular_forms_ring_represent — the EXACT-rational level-1 C[E4,E6]
 * MODULAR-FORMS-RING MEMBERSHIP DECISION (the C peer of
 * srmech.apokatastasis.modular_forms_ring.ModularFormsRing.represent; the THIRD rung of the
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
 * srmech.apokatastasis.quasimodular_forms_ring.QuasiModularFormsRing.represent; the FOURTH
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
 * srmech.apokatastasis.harmonic_maass.HarmonicMaass / MockQSeries; the PAIR carrier that
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
 * srmech.apokatastasis.riemann_theta.RiemannTheta; the FIRST RUNG of the GENUS axis). The
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
 * reusing the rc29 exact-DFT cyclotomic power basis (srmech.cascade.exact_dft) --
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
 * of srmech.apokatastasis.riemann_theta.RiemannThetaG3, the genus-3 analog of the rc72
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
 * LATTICE — the C peer of srmech.apokatastasis.riemann_theta.RiemannThetaG4, the genus-4 analog
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
 * LATTICE -- the C peer of srmech.apokatastasis.riemann_theta.RiemannThetaG5, the genus-5 analog
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
 * srmech.apokatastasis.riemann_theta.SchottkyFormG4._count_gram_py.
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
 * The C peer of srmech.apokatastasis.riemann_theta.RiemannThetaG3.chi18_leading_part.
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
 * srmech.apokatastasis.riemann_theta.RiemannThetaG3.{transform,addition_*}.
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
 * srmech.apokatastasis.riemann_theta.RiemannThetaG3.goepel_holds.
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
 * srmech.apokatastasis.riemann_theta.RiemannThetaG4.{transform, addition_*, goepel_holds}.
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
 * srmech.apokatastasis.riemann_theta.{RiemannTheta, RiemannThetaG3, RiemannThetaG4,
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
 * rc226: srmech_riemann_theta_fay_certificate — the C peer of the genus-2
 * Fay/KP RE-INDEXING CERTIFICATE
 * (srmech.apokatastasis.riemann_theta.RiemannTheta.fay_reindexing_certificate), which
 * upgrades the rc73 addition_holds SAFE-REGION boolean into an explicit,
 * EVERY-ORDER witness for the genus-2 theta addition / Fay-Hirota-shadow
 * bilinear identity (DLMF 21.6.8, z=0) via the re-indexing bijection
 * phi: (m,m') -> (m+m', m-m') on Z^2 x Z^2 (the mod-2 parity class IS the
 * RHS r-sum). Verifies the certificate's exact structural facts: (1) the
 * PARALLELOGRAM quadratic-form identity 2u^2+2u'^2 = (u+u')^2+(u-u')^2 (per
 * coordinate + the polarized cross form) as an exact CLOSED-FORM polynomial
 * identity in canonical monomial form over Z[u1,u2,u1',u2'] (index-independent
 * = the every-order content; never sampled) -> *out_par_ok; (2) the bijection
 * key-equality + mod-4 sector congruences + phi-inverse round-trip over the
 * bounded ILLUSTRATION window |n_i|,|n'_i| <= box -> *out_window_ok /
 * *out_tuples (the illustration, NOT the proof); (3) the BEYOND-SAFE-REGION
 * witness monomial (witness_a, witness_b, witness_c): its FULL exact
 * coefficient on both sides (complete — the non-negative diagonal exponents
 * bound every contributing index) -> *out_witness_lhs / *out_witness_rhs.
 * The pure-Python bodies are the complete alternative + the parity oracle.
 * SRMECH_ERR_BAD_INPUT on a non-bit characteristic, box > 2047 (the derived
 * int64 window bound), or a witness key outside the box-derived bounds
 * (diagonals in [0, 4*(2*box+1)^2], 2|C| <= A+B). Additive symbol -> ABI
 * unchanged (stays 4). It does NOT decide is-Jacobian / the curve-specific
 * Fay trisecant (the Schottky problem, genuinely open for genus >= 5). */
srmech_status_t srmech_riemann_theta_fay_certificate(
    int a1, int a2, int b1, int b2, uint32_t box,
    int64_t witness_a, int64_t witness_b, int64_t witness_c,
    int *out_par_ok, int *out_window_ok, int64_t *out_tuples,
    int64_t *out_witness_lhs, int64_t *out_witness_rhs);

/* ------------------------------------------------------------------ *
 * srmech_tripoly — EXACT-RATIONAL TRIVARIATE polynomial over srmech_bigint (the
 * C peer of srmech.math.tripoly.TriPoly; the multivariate "sums of sums"
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
 * Each op computes the SAME exact rational coefficients srmech.math.tripoly.
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
 * srmech.math.qpoly.QPoly; the q-hypergeometric F929 reduction-row foundation,
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
 * Each op computes the SAME exact rational coefficients srmech.math.qpoly.QPoly
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
 * srmech.apokatastasis.q_gosper.q_gosper.
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
 * C peer of srmech.apokatastasis.elliptic_gosper.elliptic_gosper.
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
 * carrier's is_zero (srmech.apokatastasis.thetasum.ThetaSum.is_zero), the load-bearing
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
 * srmech_thetasum_is_zero_interpolation — the C peer of the ThetaSum SOUND
 * structural CERTIFICATE recursion (REBUILT in rc210 — the is_zero soundness
 * stop-the-line fix). A 1:1 mirror of the consumer BOOL of the pure-Python
 * srmech.apokatastasis.thetasum._decide_struct (ThetaSum._is_zero_interpolation):
 * *out_is_zero = 1 IFF the cleared numerator is CERTIFICATE-PROVEN identically
 * zero; 0 = "not proven" (a proven-nonzero object or an honest decline — the
 * sound contract is True-only, so a 0 is never a nonzero CLAIM).
 *
 * The pre-rc210 decision here claimed COMPLETENESS via a single-variable
 * p-order band + a mixed-character node count; both were UNSOUND (they
 * certified provably-NONZERO objects as zero) and were REPLACED, not repaired.
 * The certificates (Rosengren arXiv:1608.06161v3): Z1 exact combine-
 * cancellation + theta(1)=0; Z3s the exact per-symbol joint-CHARACTER split
 * (degree D_v = sum e^2 + the full Eq. 1.6 multiplier mu_v — different
 * characters are linearly independent, so all components proven zero => zero);
 * Z2 the Weierstrass three-term +/- -pair reduction (Eq. 1.12) to the EMPTY
 * normal form, generalized over a component's ACTUAL live symbols; Z4
 * per-character elliptic interpolation at D_v+1 nodes PAIRWISE DISTINCT mod
 * p^Z (Cor. 1.3.5), the nodes = theta-factor zeros + DEDUPLICATED globally-
 * distinct augment primes. NO numeric band anywhere on the proving side.
 * Recursion -> an EXPLICIT arena-mark DFS (JPL Rule 1). A too-small caller
 * arena / coefficient cap -> SRMECH_ERR_OVERFLOW and the caller falls to the
 * sound pure oracle.
 *
 * Wire form + args are IDENTICAL to srmech_thetasum_is_zero. rc210 is an
 * internal rebuild (same symbols, same wire) -> ABI unchanged (stays 4).
 * License: MIT. ------- */

/* Minimum `ws_len` BYTES srmech_thetasum_is_zero_interpolation needs for the given
 * shape (rc210 certificate-recursion sizer; signature unchanged from rc102).
 * `max_theta_sq_sum` (the max per-term/per-variable sum of squared THETA-argument
 * exponents) bounds the per-frame Z4 node count D+1; the old base-case series grid
 * is GONE, so the arena is the DFS path + the transient character table + the
 * transient Z2 pair-reduce work buffers. `max_abs_exp` rides only as slack. */
size_t srmech_thetasum_is_zero_interpolation_ws_bound2(size_t n_syms, size_t n_terms,
                                                       size_t max_thetas,
                                                       size_t coeff_limbs,
                                                       size_t max_abs_exp,
                                                       size_t max_theta_sq_sum);

/* Legacy 5-arg entry (pre-rc102). Passes max_abs_exp^2 as the degree bound so a
 * stale caller still links + gets a valid (conservative) sizing; new callers use
 * srmech_thetasum_is_zero_interpolation_ws_bound2. */
size_t srmech_thetasum_is_zero_interpolation_ws_bound(size_t n_syms, size_t n_terms,
                                                      size_t max_thetas,
                                                      size_t coeff_limbs,
                                                      size_t max_abs_exp);

/* Decide whether the cleared ThetaSum numerator is CERTIFICATE-PROVEN identically
 * zero (the rc210 sound recursion — see the block comment above). *out_is_zero =
 * 1 iff proven == 0; 0 = not proven. Caller arena `ws`. n_terms == 0 -> == 0. A
 * required NULL pointer -> SRMECH_ERR_NULL_ARG; a too-small arena ->
 * SRMECH_ERR_OVERFLOW (the Python dispatch then falls to the pure oracle). */
srmech_status_t srmech_thetasum_is_zero_interpolation(
    size_t n_syms, int xsym, int ysym, int psym, size_t n_terms,
    const size_t *term_nthetas, const srmech_bigint_t *coeff_num,
    const srmech_bigint_t *coeff_den, const int32_t *exps_flat,
    uint32_t coeff_cap, int *out_is_zero, void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_thetasum_is_zero_interpolation_parallel — the rc103 CHIRALITY-
 * PRESERVING native PARALLEL fan-out, retargeted in rc210 onto the SOUND
 * certificate tree (a branch's children are its joint-character components OR
 * its interpolation nodes). Peels the top branching levels into independent
 * sub-problems, runs the sequential certificate DFS on each over a PAL worker
 * pool (deeper recursion stays serial), AND-folds with a best-effort cancel
 * flag (first not-proven short-circuits, preserving the serial early-exit);
 * bit-identical serial fallback when the PAL has no threads OR n_workers <= 1.
 *
 * TWO first-class CONTRACTS: (1) CARRIER — the verdict is BYTE-FOR-BYTE the
 * srmech_thetasum_is_zero_interpolation verdict (exact-Q, no float); (2)
 * CHIRALITY — the fan-out is ORDER-FREE: the verdict is invariant to the task
 * enumeration/scheduling order, neither chirality privileged. `task_order`
 * (0 forward / 1 reverse) exists to make the order-invariance contract
 * testable. rc210 rebuild: same symbols, same wire -> ABI stays 4. ---- */

/* Minimum `ws_len` BYTES the parallel entry needs for the given shape + width:
 * a fixed control band (the task frontier) + a parse-sized shared-root region +
 * n_workers disjoint arena slices (each the ws_bound2 sizing). See the
 * ws_bound2 doc for the sizing args. */
size_t srmech_thetasum_is_zero_interpolation_parallel_ws_bound(
    size_t n_syms, size_t n_terms, size_t max_thetas, size_t coeff_limbs,
    size_t max_abs_exp, size_t max_theta_sq_sum, size_t n_workers);

/* Decide the cleared ThetaSum numerator's certificate-proven is_zero by the
 * CHIRALITY-PRESERVING PARALLEL fan-out. Wire form + verdict IDENTICAL to
 * srmech_thetasum_is_zero_interpolation. `n_workers` = the parallel width (clamped
 * to [1, 32]); `task_order` = 0 (forward) / 1 (reverse) task enumeration — the
 * verdict is invariant either way. *out_is_zero = 1 iff proven == 0. Caller arena
 * `ws` (size via ..._parallel_ws_bound). A too-small arena -> SRMECH_ERR_OVERFLOW. */
srmech_status_t srmech_thetasum_is_zero_interpolation_parallel(
    size_t n_syms, int xsym, int ysym, int psym, size_t n_terms,
    const size_t *term_nthetas, const srmech_bigint_t *coeff_num,
    const srmech_bigint_t *coeff_den, const int32_t *exps_flat,
    uint32_t coeff_cap, uint32_t n_workers, uint32_t task_order,
    int *out_is_zero, void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_ellratio_is_elliptic — the C peer of the EllRatio carrier's is_elliptic
 * (srmech.apokatastasis.ellbase.EllRatio.is_elliptic), the load-bearing BALANCING / very-
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
 * srmech.apokatastasis.ellbase.half_shift_response (rc119; the #712 Dzhanibekov reader). A
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
 * srmech.apokatastasis.ellbase.elliptic_lagrange_basis (rc66, shipped Python-only; its C
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
 * srmech.apokatastasis.elliptic_determinant.elliptic_cauchy_determinant (rc94), the
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
 * srmech.apokatastasis.elliptic_partial_fraction.elliptic_partial_fraction (rc95), the
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
 * srmech.apokatastasis.elliptic_jackson.multivariate_elliptic_jackson (rc96),
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
 * srmech_cn_vwp_multisum_lhs — the C peer of the ThetaSum-returning op
 * srmech.apokatastasis.elliptic_jackson.cn_vwp_multisum_lhs (rc216), the SYMBOLIC Cn
 * very-well-poised (VWP) elliptic multisum LHS builder: the exact per-partition
 * theta-quotient TERMS of the LEFT-hand side of the Cn elliptic Jackson
 * summation (Hjalmar Rosengren, "A proof of a multivariable elliptic summation
 * formula conjectured by Warnaar", arXiv:math/0101073v1 [math.CA] (9 Jan 2001),
 * Theorem 2.1, Eq. 5), over the partitions
 * Lambda_{nN} = {N >= lambda_1 >= ... >= lambda_n >= 0} with the balancing
 * b*c*d*e*x^{n-1} = a^2*q^{N+1} (e fixed by construction). A C-MIRROR PARITY
 * build (NOT a new algorithm): it constructs the EXACT per-partition EllRatio
 * TERMS the pure-Python builder (the rc96 test oracle -> rc101 symbolic verify
 * engine, promoted public at rc216) builds, byte-for-byte; the Python side SUMS
 * them into the ThetaSum (there is NO ThetaSum-CONSTRUCTION C surface, so the
 * peer returns the terms as a row stream, exactly like
 * srmech_elliptic_partial_fraction).
 *
 * Each partition's summand is one EllRatio: the monomial prefactor
 * PROD_i q^{li} x^{2(i-1)li}, the diagonal num/den theta args
 * E(a x^{2(1-i)} q^{2li}) / E(a x^{2(1-i)}), the off-diagonal (i<j) coupling
 * E(x^{j-i} q^{li-lj})/E(x^{j-i}) * E(a x^{2-i-j} q^{li+lj})/E(a x^{2-i-j})
 * * (a x^{3-i-j};q)_{li+lj} (x^{j-i+1};q)_{li-lj}
 *   / ((aq x^{1-i-j};q)_{li+lj} (q x^{j-i-1};q)_{li-lj}),
 * and the six num / six den VECTOR theta-Pochhammer bases
 * (a x^{1-n}, b, c, d, e, q^{-N}; q, x)_lambda /
 * (q x^{n-1}, aq/b, aq/c, aq/d, aq/e, a q^{N+1}; q, x)_lambda. er_build folds
 * each theta's canonicalize prefactor, cancels matching thetas, sorts the
 * survivors. Pure composition of the shared srmech_ellbase_* monomial algebra
 * + er_build.
 *
 * Wire form: the interned symbol-table dimension `n_syms`; `psym` the interned
 * index of the nome p (-1 if absent); the positive ints `N` (partition ceiling)
 * + `n` (rank) + `n_terms` (the partition count C(N+n, n), computed by the
 * caller); each of the 6 parameter monomials a/b/c/d/x/q as a (num, den)
 * srmech_bigint pair + its flat int32[n_syms] exponent row. `coeff_cap` is the
 * per-bigint limb cap.
 *
 * Output: the n_terms TERM EllRatios written out flat in the LEXICOGRAPHIC
 * partition order (all-zeros first; the exact order the Python oracle's
 * filtered itertools.product enumerates) -- per term t, `out_n_num[t]` /
 * `out_n_den[t]` the survivor theta counts, and the canonical rows appended
 * (per term: its prefactor row, then its num rows, then its den rows; each row
 * carries its exact-Q coeff AND its dense int32[n_syms] exponent row).
 * `out_exps_cap_rows` is the row capacity; too small -> SRMECH_ERR_OVERFLOW.
 * N == 0, n == 0 or n_terms == 0 -> SRMECH_ERR_NULL_ARG (Python raises
 * ValueError); a wrong n_terms (not C(N+n, n)) -> SRMECH_ERR_BAD_INPUT; a
 * required NULL pointer -> SRMECH_ERR_NULL_ARG; a too-small arena ->
 * SRMECH_ERR_OVERFLOW.
 *
 * Sign travels in the Class-K coeff branch, never abs()/fabs(). Malloc-free
 * (JPL Rule 3): caller arena `ws` only, sized to (N, n, n_syms) -- no
 * compiled-in cap. Additive symbol -> ABI unchanged (stays 4). License: MIT. ---- */

/* Minimum `ws_len` BYTES srmech_cn_vwp_multisum_lhs needs for the given shape
 * (n_syms symbols, N the partition ceiling, n the rank, coeff_limbs the
 * per-coefficient significant-limb estimate). */
size_t srmech_cn_vwp_multisum_lhs_ws_bound(size_t n_syms, size_t N, size_t n,
                                           size_t coeff_limbs);

/* Build the n_terms per-partition Cn VWP multisum LHS TERM EllRatios (see
 * above); the Python side sums them into the returned ThetaSum. */
srmech_status_t srmech_cn_vwp_multisum_lhs(size_t n_syms, int psym, size_t N,
                                           size_t n, size_t n_terms,
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
 * srmech_multivariate_elliptic_jackson_an — the C peer of the EllRatio-carrier
 * op srmech.apokatastasis.elliptic_jackson_an.multivariate_elliptic_jackson_an (rc227),
 * the eq-6 An elliptic Jackson summation reducer: the type-A member of the
 * multivariable (root-system) elliptic reduction row. A C-MIRROR PARITY build
 * (NOT a new algorithm): it constructs the EXACT closed form the pure-Python op
 * builds, byte-for-byte.
 *
 * For the variables z_1..z_n, the parameters a_1..a_{n+1}, the base q and the
 * COMPUTED balancing w = z_1..z_n * a_1..a_{n+1} (Hjalmar Rosengren, "New
 * transformations for elliptic hypergeometric series on the root system An",
 * arXiv:math/0305379v1 [math.CA] (27 May 2003), Eq. 6 -- the elliptic analogue
 * of Milne's An Jackson summation), the An elliptic Jackson summation over the
 * SIMPLEX y_1+..+y_n = N reduces to the theta-quotient
 *   PROD_{j=1}^{n+1} (w/a_j)_N / [ PROD_{j=1}^n (w*z_j)_N * (q)_N ],
 * with (u)_k = PROD_{i=0}^{k-1} theta(u*q^i). This op CONSTRUCTS the right-hand
 * side as an exact EllRatio: the unit prefactor, the (n+1)*N numerator thetas
 * (w/a_j * q^i) and the (n+1)*N denominator thetas (w*z_j * q^i + the (q)_N
 * block q*q^i); er_build folds each theta's canonicalize prefactor, cancels
 * matching thetas, sorts the survivors. Pure composition of the shared
 * srmech_ellbase_* monomial algebra + er_build.
 *
 * Wire form: the interned symbol-table dimension `n_syms`; `psym` the interned
 * index of the nome p (-1 if absent); the positive ints `N` (simplex ceiling) +
 * `n` (rank); the VARIABLE-ARITY vectors as parallel arrays (the
 * srmech_elliptic_cauchy_determinant convention): `zs_num`/`zs_den` n bigints +
 * `zs_exps_flat` int32[n*n_syms]; `as_num`/`as_den` n+1 bigints +
 * `as_exps_flat` int32[(n+1)*n_syms]; q as a (num, den) pair + its
 * int32[n_syms] exponent row. `coeff_cap` is the per-bigint limb cap.
 *
 * Output: the single closed-form EllRatio written flat as a ROW stream (the
 * srmech_multivariate_elliptic_jackson wire form): the prefactor row, then
 * *out_n_num num-theta rows, then *out_n_den den-theta rows (each row its
 * exact-Q coeff + its dense int32[n_syms] exponent row). `out_exps_cap_rows` is
 * the row capacity; too small -> SRMECH_ERR_OVERFLOW. N == 0 or n == 0 ->
 * SRMECH_ERR_NULL_ARG (Python raises ValueError); a required NULL pointer ->
 * SRMECH_ERR_NULL_ARG; a too-small arena -> SRMECH_ERR_OVERFLOW.
 *
 * Sign travels in the Class-K coeff branch, never abs()/fabs(). Malloc-free
 * (JPL Rule 3): caller arena `ws` only, sized to (N, n, n_syms) -- no
 * compiled-in cap. Additive symbol -> ABI unchanged (stays 4). License: MIT. ---- */

/* Minimum `ws_len` BYTES srmech_multivariate_elliptic_jackson_an needs for the
 * given shape (n_syms symbols, N the simplex ceiling, n the rank, coeff_limbs
 * the per-coefficient significant-limb estimate). */
size_t srmech_multivariate_elliptic_jackson_an_ws_bound(size_t n_syms, size_t N,
                                                        size_t n, size_t coeff_limbs);

/* Build the single An elliptic Jackson closed-form EllRatio (see above). */
srmech_status_t srmech_multivariate_elliptic_jackson_an(
    size_t n_syms, int psym, size_t N, size_t n,
    const srmech_bigint_t *zs_num, const srmech_bigint_t *zs_den,
    const int32_t *zs_exps_flat,
    const srmech_bigint_t *as_num, const srmech_bigint_t *as_den,
    const int32_t *as_exps_flat,
    const srmech_bigint_t *q_num, const srmech_bigint_t *q_den,
    const int32_t *q_exps, uint32_t coeff_cap,
    srmech_bigint_t *out_coeff_num, srmech_bigint_t *out_coeff_den,
    int32_t *out_exps_flat, size_t out_exps_cap_rows,
    size_t *out_n_num, size_t *out_n_den, void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_an_vwp_multisum_lhs — the C peer of the ThetaSum-returning op
 * srmech.apokatastasis.elliptic_jackson_an.an_vwp_multisum_lhs (rc227), the SYMBOLIC An
 * elliptic multisum LHS builder: the exact per-composition theta-quotient
 * TERMS of the LEFT-hand side of the An (type-A / Milne) elliptic Jackson
 * summation (Rosengren arXiv:math/0305379v1, Eq. 6), over the SIMPLEX
 * y_1..y_n >= 0 with y_1+..+y_n = N, with the COMPUTED balancing
 * w = z_1..z_n * a_1..a_{n+1}. A C-MIRROR PARITY build (NOT a new algorithm):
 * it constructs the EXACT per-composition EllRatio TERMS the pure-Python
 * builder builds, byte-for-byte; the Python side SUMS them into the ThetaSum
 * (there is NO ThetaSum-CONSTRUCTION C surface -- the
 * srmech_cn_vwp_multisum_lhs row-stream pattern).
 *
 * Each composition's summand is one EllRatio: the monomial prefactor
 * PROD_{j<k} q^{y_j} (the type-A Vandermonde ratio's monomial part), the
 * Vandermonde theta args E(z_k q^{y_k - y_j}/z_j) / E(z_k/z_j) for j < k, the
 * (n+1) num theta-Pochhammers (a_j z_k)_{y_k} per k, and the den
 * theta-Pochhammers (w z_k)_{y_k} * PROD_j (q z_k/z_j)_{y_k} per k. er_build
 * folds each theta's canonicalize prefactor, cancels matching thetas, sorts
 * the survivors. Pure composition of the shared srmech_ellbase_* monomial
 * algebra + er_build.
 *
 * Wire form: the interned symbol-table dimension `n_syms`; `psym` the interned
 * index of the nome p (-1 if absent); the positive ints `N` (simplex ceiling)
 * + `n` (rank) + `n_terms` (the composition count C(N+n-1, n-1), computed by
 * the caller); the VARIABLE-ARITY vectors as parallel arrays: `zs_num`/`zs_den`
 * n bigints + `zs_exps_flat` int32[n*n_syms]; `as_num`/`as_den` n+1 bigints +
 * `as_exps_flat` int32[(n+1)*n_syms]; q as a (num, den) pair + its
 * int32[n_syms] row. `coeff_cap` is the per-bigint limb cap.
 *
 * Output: the n_terms TERM EllRatios written out flat in the ASCENDING
 * LEXICOGRAPHIC composition order ((0,..,0,N) first, (N,0,..,0) last; the
 * exact order the Python builder's filtered itertools.product enumerates) --
 * per term t, `out_n_num[t]` / `out_n_den[t]` the survivor theta counts, and
 * the canonical rows appended (per term: its prefactor row, then its num rows,
 * then its den rows; each row carries its exact-Q coeff AND its dense
 * int32[n_syms] exponent row). `out_exps_cap_rows` is the row capacity; too
 * small -> SRMECH_ERR_OVERFLOW. N == 0, n == 0 or n_terms == 0 ->
 * SRMECH_ERR_NULL_ARG (Python raises ValueError); a wrong n_terms (not
 * C(N+n-1, n-1)) -> SRMECH_ERR_BAD_INPUT; a required NULL pointer ->
 * SRMECH_ERR_NULL_ARG; a too-small arena -> SRMECH_ERR_OVERFLOW.
 *
 * Sign travels in the Class-K coeff branch, never abs()/fabs(). Malloc-free
 * (JPL Rule 3): caller arena `ws` only, sized to (N, n, n_syms) -- no
 * compiled-in cap. Additive symbol -> ABI unchanged (stays 4). License: MIT. ---- */

/* Minimum `ws_len` BYTES srmech_an_vwp_multisum_lhs needs for the given shape
 * (n_syms symbols, N the simplex ceiling, n the rank, coeff_limbs the
 * per-coefficient significant-limb estimate). */
size_t srmech_an_vwp_multisum_lhs_ws_bound(size_t n_syms, size_t N, size_t n,
                                           size_t coeff_limbs);

/* Build the n_terms per-composition An multisum LHS TERM EllRatios (see
 * above); the Python side sums them into the returned ThetaSum. */
srmech_status_t srmech_an_vwp_multisum_lhs(
    size_t n_syms, int psym, size_t N, size_t n, size_t n_terms,
    const srmech_bigint_t *zs_num, const srmech_bigint_t *zs_den,
    const int32_t *zs_exps_flat,
    const srmech_bigint_t *as_num, const srmech_bigint_t *as_den,
    const int32_t *as_exps_flat,
    const srmech_bigint_t *q_num, const srmech_bigint_t *q_den,
    const int32_t *q_exps, uint32_t coeff_cap,
    srmech_bigint_t *out_coeff_num, srmech_bigint_t *out_coeff_den,
    int32_t *out_exps_flat, size_t out_exps_cap_rows,
    size_t *out_n_num, size_t *out_n_den, void *ws, size_t ws_len);

/* ------------------------------------------------------------------ *
 * srmech_riemann_theta_multisum — the C peer of the ThetaBracketSum-returning
 * ops srmech.apokatastasis.riemann_theta_multisum.{riemann_theta_multisum_lhs,
 * multivariate_riemann_theta_sum} (rc232): the HIGHER-GENUS (genus-g Riemann
 * theta) multisum reduction-row builders. It constructs, byte-for-byte, the
 * bracket-product MONOMIALS of the LEFT-hand side (the n+1-term multisum, side 0)
 * and the closed-form RIGHT-hand side (PROD g_k - PROD h_k, side 1) of
 * Spiridonov's multiparameter summation formula (arXiv:math/0408366, the Theorem,
 * Eq. sum; extracted-source PDF sha256
 * 8478af7407d26d0b0504d381cbe3c32a00f950c3b0c6ab8001a023b7e0c4c319). The Python
 * side folds the emitted monomials into the ThetaBracketSum.
 *
 * A self-contained int32/int64 wire (no srmech_bigint / ellbase dependency): the
 * coeffs are +-1 and the genus-g odd-theta arguments are small integer exponent
 * rows over the interned symbol table (Python sorted-symbol-NAME order). Additive
 * '+' of arguments is row addition, v(a,b) = -P_a + P_b is row axpy, and the odd
 * antisymmetry [-u] = -[u] is canonicalized by orienting each argument row so its
 * FIRST NONZERO entry is NEGATIVE, folding a Class-K +-1 sign into the monomial
 * coeff (never abs()); an all-zero argument is the zero bracket [0]=0 and drops
 * the whole monomial.
 *
 * Inputs: `n_syms` the interned symbol dimension (>= 1); `n` the summation ceiling
 * (n+1 point-tuples); `side` 0 = LHS / 1 = RHS; `z_exps_flat` = int32[(n+1)*n_syms]
 * (the z-vector rows); `pt_exps_flat` = int32[(n+1)*4*n_syms] (per k the four rows
 * a,b,c,d). Outputs: `out_coeff[m]` the m-th monomial coeff (+-1 before the Python
 * combine); `out_args_flat` its nb = 4*(n+1) canonical argument rows appended flat
 * (nb*n_syms int32 per monomial, build order); `*out_n_monos` the monomials
 * emitted (a zero-bracket monomial is skipped: LHS <= n+1, RHS <= 2); `*out_nb` =
 * nb. `max_monos` the caller's monomial capacity; too small -> SRMECH_ERR_OVERFLOW.
 * n_syms == 0 or a NULL required pointer -> SRMECH_ERR_NULL_ARG; side not in {0,1}
 * -> SRMECH_ERR_BAD_INPUT. Malloc-free (builds in the output buffer in place, no
 * scratch arena). Additive symbol -> SRMECH_ABI_VERSION stays 4. */
srmech_status_t srmech_riemann_theta_multisum(
    size_t n_syms, size_t n, int side,
    const int32_t *z_exps_flat, const int32_t *pt_exps_flat,
    int64_t *out_coeff, int32_t *out_args_flat, size_t max_monos,
    size_t *out_n_monos, size_t *out_nb);

/* ------------------------------------------------------------------ *
 * srmech_elliptic_recurrence_8w7 — the ELLIPTIC Sigma-row ORDER-1 RECURRENCE op for the
 * Frenkel–Turaev ₈ω₇ summation. The C peer of
 * srmech.apokatastasis.elliptic_recurrence.elliptic_recurrence_8w7 — a 1:1 STRUCTURAL MIRROR of
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
 * srmech.apokatastasis.elliptic_zeilberger.elliptic_zeilberger). The order-1 recurrence
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
 * srmech.apokatastasis.elliptic_wz_certificate.elliptic_wz_certificate). Where
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
 * srmech.math.carrier_spectrum.carrier_spectrum). A 1:1 STRUCTURAL MIRROR of the
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
 * srmech_zeilberger). The C peer of srmech.apokatastasis.q_zeilberger.q_zeilberger.
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
 * CLOSER). The C peer of the VERIFY half of srmech.apokatastasis.q_wz_certificate.
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
 * srmech.math.qmat.QMat; the exact-ℚ linear-algebra carrier the §76 gosper
 * undetermined-coefficient solve needs in C).
 *
 * A matrix is two parallel caller-owned srmech_bigint arrays, ROW-MAJOR:
 * nums[r*ncols + c] / dens[r*ncols + c] is the exact-rational entry at (r, c)
 * (dens > 0, gcd(|nums|, dens) == 1; zero entry = 0/1). Each op computes the
 * SAME exact rational entries srmech.math.qmat.QMat computes — exact Gauss-Jordan
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
 * pure-Python srmech.math.qmat.QMat.rref_crt: descending odd primes from 2**31-2,
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
 * srmech.cascade.cayley_dickson.{cd_basis, cd_conjugate, cd_add,
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
 * srmech.cascade.cayley_dickson.cd_mult; attested by
 * tests/test_qalg_cdmult_c_rc160.py. Additive symbol -> ABI unchanged (3). */
srmech_status_t srmech_cd_mult(const srmech_bigint_t *x_n,
                               const srmech_bigint_t *x_d,
                               const srmech_bigint_t *y_n,
                               const srmech_bigint_t *y_d, int dim,
                               srmech_bigint_t *out_n, srmech_bigint_t *out_d,
                               void *ws, size_t ws_len);

/* The TABLE-DRIVEN exact-Q product (v0.9.0rc353, `#T997`) — srmech_cd_mult's
 * sibling, reading a caller-supplied rank-3 structure-constant table instead
 * of the hard-wired Cayley-Dickson cocycle:
 *
 *     (x*y)_k = sum_{i,j} table[(i*dim + j)*dim + k] * x_i * y_j
 *
 * `table` is dim*dim*dim int64 in the SAME layout srmech_algebra_table writes
 * and srmech_algebra_inertia_signature reads. x, y, out are each `dim`
 * exact-Q (num, den) components; out may not alias x or y. Feeding it
 * srmech_algebra_table(dim, NULL, 0, ...) reproduces srmech_cd_mult exactly --
 * the same bilinear form by two routes, which is the differential the split
 * and control tables are checked against.
 *
 * The structure constants are INTEGER by contract; the ELEMENTS are arbitrary
 * exact rationals, so the domain is exactly srmech_cd_mult's -- there is no
 * int64 element ceiling and no decline. `ws` >=
 * srmech_algebra_table_product_ws_bound(coeff_limbs, dim); each output entry
 * needs srmech_algebra_table_product_entry_cap limbs (both sized for a DENSE
 * table, which can steer all dim*dim products into one slot). Errors:
 * SRMECH_ERR_NULL_ARG; SRMECH_ERR_BAD_INPUT (dim outside
 * [1, SRMECH_ALGEBRA_TABLE_MAX_DIM]); SRMECH_ERR_OVERFLOW (arena or entry
 * too small -- never a silent wrap; the Python peer then routes to its
 * ceiling-free bignum path). Rosetta peer of
 * srmech.cascade.cayley_dickson.table_product. Additive symbols ->
 * SRMECH_ABI_VERSION unchanged (stays 10). */
size_t srmech_algebra_table_product_ws_bound(size_t coeff_limbs, size_t dim);
size_t srmech_algebra_table_product_entry_cap(size_t coeff_limbs, size_t dim);
srmech_status_t srmech_algebra_table_product(const int64_t *table, int dim,
                                             const srmech_bigint_t *x_n,
                                             const srmech_bigint_t *x_d,
                                             const srmech_bigint_t *y_n,
                                             const srmech_bigint_t *y_d,
                                             srmech_bigint_t *out_n,
                                             srmech_bigint_t *out_d,
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
 * of srmech.cascade.matrix_cascades.char_poly (integer path); attested by
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
 * srmech.cascade.matrix_cascades.eigvals_exact (real-root path); attested by
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
 * F929). The C peer of srmech.apokatastasis.zeilberger.zeilberger.
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
 * srmech.apokatastasis.wz_certificate.wz_certificate.
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
 * srmech.apokatastasis.apagodu_zeilberger.apagodu_zeilberger.
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
 * re-raise of #863 BX-5/6/7). C peers of srmech.physics.qm.quaternion — the
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

/* The quaternion conjugate conj(x) = (x0, -x1, -x2, -x3): the scalar axis is
 * fixed, the three imaginary axes flip sign (a plain Class-C orientation flip;
 * no abs()). For a UNIT quaternion conj IS the inverse (x . conj(x) = |x|^2 = 1),
 * so conj(exp(mu*theta)) = exp(-mu*theta) — the inverse-QDFT twiddle, and the
 * reversed-edge gain in the cycle-holonomy walk. `n` must be 4; `out` MAY alias
 * `x` (in-place negation is safe). C peer of srmech.physics.qm.quaternion.quaternion_conjugate
 * (byte-exact). Errors: SRMECH_ERR_NULL_ARG; SRMECH_ERR_BAD_INPUT (n != 4).
 * Additive symbol -> SRMECH_ABI_VERSION stays 10. */
srmech_status_t srmech_quaternion_conjugate(
    const double *x, size_t n, double *out);

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

/* 0.9.0rc385 (#T1048) — the INVERSE of srmech_quaternion_exp for a UNIT
 * quaternion q = [w, v]: out = [0, theta * v/‖v‖] with ‖v‖ the Class-K
 * magnitude of the imaginary part and theta = atan2(‖v‖, w) in [0, pi]. The
 * pure-real branch (‖v‖ == 0) is the Class-K pin-slot: the zero tangent. ‖v‖
 * rides the Class-N srmech_rational_sqrt of a sum-of-squares (no abs()); theta
 * rides srmech_atan_q61 with the quadrant shift in Q61 INTEGER space (by
 * SRMECH_Q61_HALF_PI, exactly as Python rational.atan2), projected to double
 * ONCE — byte-exact with srmech.physics.qm.quaternion.quaternion_log. `n` must
 * be 4; `out` MAY alias `q`. Errors: SRMECH_ERR_NULL_ARG; SRMECH_ERR_BAD_INPUT
 * (n != 4) or an srmech_rational_sqrt / srmech_atan_q61 error. Additive symbol
 * -> SRMECH_ABI_VERSION stays 10. */
srmech_status_t srmech_quaternion_log(
    const double *q, size_t n, double *out);

/* 0.9.0rc385 (#T1048) — shortest-arc geodesic interpolation on the unit-
 * quaternion S^3: slerp(q0, q1, t) = q0 . exp(t . log(conj(q0) . q1)). A pure
 * composition of the shipped ops (Class-C conjugate, Class-M Hamilton product,
 * the rc385 log, the exp twiddle); t = 0 -> q0, t = 1 -> q1 for unit q0/q1. `n`
 * must be 4; `out` MUST NOT alias q0/q1. Byte-exact with
 * srmech.physics.qm.quaternion.quaternion_slerp. Errors: SRMECH_ERR_NULL_ARG;
 * SRMECH_ERR_BAD_INPUT (n != 4) or a sub-op error. Additive symbol ->
 * SRMECH_ABI_VERSION stays 10. */
srmech_status_t srmech_quaternion_slerp(
    const double *q0, const double *q1, double t, size_t n, double *out);

/* ------------------------------------------------------------------ *
 * srmech_q8 — the DISCRETE quaternion group Q8 = {+-1, +-i, +-j, +-k}
 * as 3-bit bytes (0.9.0rc310): the discrete peer of the CONTINUOUS H
 * surface above. A byte q in {0..7} is q = (sign_bit << 2) | v4_coset
 * with v4_coset = q & 3 in {1,i,j,k} and sign_bit = q >> 2 in {+,-}, so
 * 0=+1 1=+i 2=+j 3=+k 4=-1 5=-i 6=-j 7=-k. Pure INTEGER bit-arithmetic:
 * no floats, so no FMA / FP-contraction concern. Q8 is the central
 * extension 1 -> Z2 -> Q8 -> V4 -> 1; the product's sign is the cocycle
 * F (= the dim-4 restriction of the srmech_cd_basis_product sign,
 * verified from Python) xored with the two center bits. The abelian
 * projection V4 = q & 3 is the EXACT F380 / in-repo R21 homomorphism
 * pi: Q8 -> V4 (pi(a.b) = pi(a) xor pi(b) for all a,b). Additive
 * INTEGER symbols (no callback typedef) -> SRMECH_ABI_VERSION stays 10.
 * See srmech_q8.c.
 * ------------------------------------------------------------------ */

/* The Q8 group product: (sa . e_xa)(sb . e_xb) = (sa xor sb xor
 * F[xa][xb]) . e_(xa xor xb), with xa=a&3, xb=b&3, sa=a>>2, sb=b>>2 and
 * F the central-extension cocycle sign table. NON-abelian (q8_mult(1,2)=3
 * but q8_mult(2,1)=7), i^2 = j^2 = k^2 = 4 (-1), associative over all
 * 8x8x8. Class-M group bind o Class-I Z2 sign xor (no abs()). Contract:
 * a < 8 and b < 8 (asserted). */
uint8_t srmech_q8_mult(uint8_t a, uint8_t b);

/* The Q8 conjugate / group inverse: conj(a) = a for the center (coset 0,
 * self-inverse), else a xor 4 (flip an imaginary coset's sign bit).
 * srmech_q8_mult(a, srmech_q8_conjugate(a)) == 0 for every a. Class-C
 * orientation flip (no abs()). Contract: a < 8 (asserted). */
uint8_t srmech_q8_conjugate(uint8_t a);

/* Elementwise Q8 bind over n-length uint8 buffers: out[i] =
 * srmech_q8_mult(turn[i], one[i]). `out` MAY alias `turn` and/or `one`
 * (each slot i is read then written before slot i+1 is touched, so an
 * in-place bind is well defined). n == 0 is a no-op. Every input byte
 * MUST be a valid Q8 element (< 8). Class-M bind. Errors:
 * SRMECH_ERR_NULL_ARG (any pointer NULL). */
srmech_status_t srmech_q8_bind(const uint8_t *turn, const uint8_t *one,
                               uint32_t n, uint8_t *out);

/* The abelian projection pi: Q8 -> V4 elementwise: out[i] = q[i] & 3
 * (drop the center sign bit, keeping the {1,i,j,k} coset). `out` MAY
 * alias `q`. n == 0 is a no-op. Class-I abelian coset read. Errors:
 * SRMECH_ERR_NULL_ARG (any pointer NULL). */
srmech_status_t srmech_q8_project_v4(const uint8_t *q, uint32_t n,
                                     uint8_t *out);

/* ------------------------------------------------------------------ *
 * srmech_oct — the DISCRETE octonion Moufang loop {+-e0, +-e1, ...,
 * +-e7} as 4-bit bytes (0.9.0rc324): the Cayley-Dickson rung ABOVE the
 * Q8 group above. A byte o in {0..15} is o = (sign_bit << 3) | index
 * with index = o & 7 in {e0..e7} and sign_bit = o >> 3 in {+,-}, so
 * 0=+e0(=+1) ... 7=+e7, 8=-e0(=-1) ... 15=-e7 (the FULL octonion —
 * indices 4..7 are the non-quaternionic units the Q8 sub-block 0..3
 * cannot reach). Pure INTEGER bit-arithmetic: no floats. The product's
 * sign is the Cayley-Dickson cocycle F at dim 8 (computed by calling
 * srmech_cd_basis_product, of which Q8's F is the dim-4 restriction)
 * xored with the two center bits; the result index is ALWAYS xa xor xb.
 * NON-associative for >= 3 independent units, but the per-slot Moufang
 * loop has the inverse property so the right-conjugate decouple round-
 * trips byte-exact. Additive INTEGER symbols (no callback typedef) ->
 * SRMECH_ABI_VERSION stays 10. See srmech_octonion_carrier.c. */

/* The octonion loop product: (sa . e_xa)(sb . e_xb) = (sa xor sb xor
 * F[xa][xb]) . e_(xa xor xb), with xa=a&7, xb=b&7, sa=a>>3, sb=b>>3 and
 * F the dim-8 Cayley-Dickson cocycle sign (via srmech_cd_basis_product).
 * 0 (+e0) is the identity; e_i^2 = -1 (byte 8) for i != 0. Class-M loop
 * bind o Class-I Z2 sign xor (no abs()). Contract: a < 16 and b < 16
 * (asserted). */
uint8_t srmech_oct_mult(uint8_t a, uint8_t b);

/* The octonion conjugate / loop inverse: conj(a) = a for the real center
 * (index 0, self-inverse), else a xor 8 (flip an imaginary unit's sign
 * bit). srmech_oct_mult(a, srmech_oct_conjugate(a)) == 0 for every a.
 * Class-C orientation flip (no abs()). Contract: a < 16 (asserted). */
uint8_t srmech_oct_conjugate(uint8_t a);

/* Elementwise octonion bind over n-length uint8 buffers: out[i] =
 * srmech_oct_mult(turn[i], one[i]). `out` MAY alias `turn` and/or `one`
 * (each slot i is read then written before slot i+1 is touched, so an
 * in-place bind is well defined). n == 0 is a no-op. Every input byte
 * MUST be a valid octonion element (< 16). Class-M bind. Errors:
 * SRMECH_ERR_NULL_ARG (any pointer NULL). */
srmech_status_t srmech_oct_bind(const uint8_t *turn, const uint8_t *one,
                                uint32_t n, uint8_t *out);

/* §Q8-FIBER/v17 (rc322, F-HOLO-MISLOCATED) — the strand's TOPOLOGY / FIBER
 * channel: the ORDERED (order-carried) accumulated Q8 holonomy of the coupled
 * turns along a strand. `turns` is a flat n_turns x leaf_dim buffer of Q8 bytes
 * (row t = the t-th stored/coupled data turn, one Q8 element per slot); `out` is
 * leaf_dim Q8 bytes. Per slot s, out[s] = q8_mult(...q8_mult(q8_mult(0, turns[0]
 * [s]), turns[1][s])..., turns[n_turns-1][s]) — the ordered left-to-right fold
 * (identity +1 == byte 0). Q8 is NON-abelian (i.j=+k but j.i=-k), so REORDERING
 * the turns CHANGES the fold: this is the fiber/gauge the per-turn coupled STORE
 * cannot carry (that store re-stamps q8_mult(turn, one) per turn — winding-
 * INVARIANT). The accumulated sign bit (out[s] >> 2) IS the per-slot Lk mod 2
 * (the accumulated Lk = Tw + Wr; no abs()). Writes `out` directly — no scratch,
 * no malloc; additive INTEGER symbol, SRMECH_ABI_VERSION stays 10. n_turns == 0
 * yields the identity. `out` MUST NOT alias `turns`. Every input byte MUST be a
 * valid Q8 element (< 8). Errors: SRMECH_ERR_NULL_ARG (turns or out NULL). */
srmech_status_t srmech_genome_fiber_holonomy(const uint8_t *turns,
                                             uint32_t n_turns,
                                             uint32_t leaf_dim,
                                             uint8_t *out);

/* §𝕆-FIBER/v18 (rc325) — the strand's OCTONION TOPOLOGY / FIBER channel, the 𝕆
 * analog of srmech_genome_fiber_holonomy ONE Cayley-Dickson rung up (Q8 -> 𝕆).
 * The ORDERED accumulated octonion holonomy of the coupled turns along a strand.
 * `turns` is a flat n_turns x leaf_dim buffer of octonion bytes (row t = the t-th
 * stored/coupled data turn, one octonion element per slot); `out` is leaf_dim
 * octonion bytes. Per slot s, out[s] = oct_mult(...oct_mult(oct_mult(0, turns[0]
 * [s]), turns[1][s])..., turns[n_turns-1][s]) — the ordered LEFT-to-right fold
 * (identity +e0 == byte 0), REUSING srmech_oct_mult (NOT a reimplemented product).
 * 𝕆 is non-commutative AND non-associative, so REORDERING the turns CHANGES the
 * fold: this is the fiber the per-turn coupled octonion STORE cannot carry (that
 * store re-stamps oct_mult(turn, one) per turn). Writes `out` directly — no scratch,
 * no malloc; additive INTEGER symbol, SRMECH_ABI_VERSION stays 10. n_turns == 0
 * yields the identity. `out` MUST NOT alias `turns`. Every input byte MUST be a
 * valid octonion element (< 16). Errors: SRMECH_ERR_NULL_ARG (turns or out NULL). */
srmech_status_t srmech_genome_octonion_holonomy(const uint8_t *turns,
                                                uint32_t n_turns,
                                                uint32_t leaf_dim,
                                                uint8_t *out);

/* THE ORDER-CARRYING OCTONION ASSOCIATIVITY READ — split_defect (rc390). The
 * ORDER-carrying complement of srmech_genome_octonion_associator (order-BLIND:
 * L-vs-R fold, permutation-invariant). For a `word` of n octonion basis letters
 * (each byte < 16) and a split index k (0 < k < n), it reads the sign bit of the
 * fully-LEFT fold of the whole word against the sign bit of (fold(word[:k]) .
 * fold(word[k:])) — the SAME letters, RE-BRACKETED at k:
 *   *out_bit = (fold(word) >> 3) ^ (oct_mult(fold(word[:k]), fold(word[k:])) >> 3)
 * The octonion index lane is ⊕-associative so both bracketings share the index and
 * differ ONLY in the center sign bit — the returned 0/1. It CAN fire only when BOTH
 * split sides have length >= 2 (a length-1 side folds trivially), so a middle split
 * needs n >= 4 (the 𝕆 census is 1008/2401 at n=4). Folds via srmech_oct_mult (NOT a
 * reimplemented product); Class-M (the two folds) ∘ Class-K (the sign reads) ∘
 * Class-C (the XOR); no abs(). No malloc, no goto, no recursion. ADDITIVE plain
 * symbol reusing NO callback typedef -> SRMECH_ABI_VERSION stays 10. Contract:
 * word/out_bit non-NULL, n >= 2, 0 < k < n, every byte < 16. Errors:
 * SRMECH_ERR_NULL_ARG (word or out_bit NULL), SRMECH_ERR_BAD_INPUT (bad k/n/byte). */
srmech_status_t srmech_split_defect(const uint8_t *word, uint32_t n, uint32_t k,
                                    uint8_t *out_bit);

/* ------------------------------------------------------------------ *
 * srmech_octonion — the ODFT twiddle family + the whole-transform
 * OCTONION DFT (0.9.0rc111; issue #1234 Item 1c, re-raise of #863).
 * C peers of srmech.physics.qm.octonion's rc111 twiddle family and the
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
 * F1002 refinement). C peer of srmech.cascade.phase_coherent_peak.
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

/* ------------------------------------------------------------------
 * Carrier (operand) introspection registry (0.9.0rc205; gh #1293).
 *
 * The noun-side DUAL of the rc184 tool-schema registry: where the tool
 * table exposes the OPS (the A-N operator verbs), this table exposes the
 * CARRIER TYPES (the operand nouns — Poly/BiPoly/TriPoly/QPoly/QBiPoly,
 * the Cayley-Dickson rungs float/complex/quaternion/octonion/sedenion,
 * Mat/Vec/HV, the exact scalars int/Fraction/Q, the elliptic
 * EllMonomial/EllRatio/ThetaSum, the weight-axis UnaryTheta/MockQSeries/
 * HarmonicMaass, and the HDC objects One/SedenionRegister) with, per
 * carrier: a one-line human-readable description, its promote/project
 * ladder + rung (NULL/0 off-ladder), its shift variables, the rc339 (`#T967`)
 * CAPABILITY block, and the DERIVED ops back-index (which registered tools
 * consume / produce it) — so a bare-C host (no Python) discovers BOTH the
 * verbs and the nouns (the Siona / RBS-LM self-hosting ask).
 *
 * CAPABILITY (rc339, extended rc343 `#T972`) — what the carrier can DO, not
 * only what it is: {product, address, compose, turn, commutative, varies_with,
 * max_dim, bounded_by}. The last two are the PER-CARRIER ceiling: `max_dim` is
 * the largest algebra dim (real dimension) at which the row's verdicts hold,
 * NULL/absent meaning UNBOUNDED in dim, and `bounded_by` names the mechanism.
 * They exist because rc339 published ONE turn ceiling of 4, globally, and rows
 * in this very table beat it — Mat's mat_matmul is associative at every dim.
 * It reports the
 * WORST case over everything the carrier admits (CDRegister publishes the
 * dim-256 answer, not the dim-4 one), so a permissive number elsewhere can
 * never be read as a capability the carrier does not have; `varies_with` names
 * the knob that can improve it. `turn` == "abelian_only" is read together with
 * `commutative`: vacuous on a commutative carrier, a DEGRADATION on a
 * non-commutative one — which is exactly the octonion rung, where the
 * turn-composing set and the commuting set were measured to be the same set.
 * The dimension ceilings are SRMECH_CD_COMPOSE_MAX_DIM / SRMECH_CD_TURN_MAX_DIM
 * above; the measured ontology is
 * docs/srmech/notes/carrier_capability_ontology_rc339.py.
 *
 * The table lives in the GENERATED translation unit
 * `srmech_carrier_registry.c` (regenerate with
 * c/tools/gen_carrier_registry.py); the accessors + the whole-schema
 * assembler live in srmech_carrier_schema.c.
 *
 * srmech_carrier_schema emits bytes BYTE-IDENTICAL to CPython
 *   json.dumps(srmech.introspect.carrier_schema._pure_carrier_schema(),
 *              sort_keys=True, separators=(",", ":"))
 * (each per-carrier entry payload is baked pre-canonical; rows are in
 * byte-sorted name order == the sort_keys key order, so the assembler is
 * plain concatenation). This byte-identity IS the hash-ratchet contract
 * locking the C table to the Python SSoT.
 *
 * ABI-additive: new symbols + one struct, so SRMECH_ABI_VERSION stays 4.
 * ------------------------------------------------------------------ */

/* One carrier (operand) type in the registry. All string pointers are
 * NUL-terminated decoded UTF-8; `entry_json` is the per-carrier payload
 * {"capability","description","ladder","name","ops","rung","variables"} as its
 * pre-canonical compact-ASCII JSON fragment (`entry_len` bytes, excluding
 * the NUL). */
typedef struct {
    const char *name;        /* carrier name (the registry key)          */
    const char *description; /* one-line human-readable description      */
    const char *ladder;      /* promote/project ladder, NULL off-ladder  */
    int         rung;        /* rung on the ladder, 0 off-ladder         */
    const char *entry_json;  /* pre-canonical compact JSON entry payload */
    size_t      entry_len;   /* bytes in entry_json (excluding the NUL)  */
} srmech_carrier_entry_t;

/* The compiled-in registry table + count (defined in the generated
 * srmech_carrier_registry.c). */
extern const srmech_carrier_entry_t srmech_carrier_registry_table[];
extern const size_t srmech_carrier_registry_len;

/* Number of registered carrier entries in the const table. */
size_t srmech_carrier_registry_count(void);

/* The entry at `index`, or NULL if `index` is out of range. */
const srmech_carrier_entry_t *srmech_carrier_registry_get(size_t index);

/* The entry whose `name` equals `name` (bounded linear scan), or NULL
 * for an unknown name / a NULL `name`. `name` must be NUL-terminated. */
const srmech_carrier_entry_t *srmech_carrier_registry_find(const char *name);

/* Assemble the whole carrier schema as canonical JSON (see byte-identity
 * contract above) into `buf` (capacity `buf_len`; NO trailing NUL) and
 * set *out_len to the byte count. If `buf` is NULL this is a SIZE-QUERY
 * (nothing written; *out_len receives the exact full length). A
 * too-small non-NULL `buf` returns SRMECH_ERR_OVERFLOW; `out_len == NULL`
 * returns SRMECH_ERR_NULL_ARG. */
srmech_status_t srmech_carrier_schema(char *buf, size_t buf_len,
                                      size_t *out_len);

/* ------------------------------------------------------------------ *
 * RESPONSION (stored-relationship) introspection registry (0.9.0rc225)
 *
 * The k=3 completion of the introspection triad (user design
 * 2026-07-12): the rc184 tool registry exposes the OPS (the A-N
 * operator verbs) and the rc205 carrier registry exposes the OPERANDS
 * (the carrier nouns) — the k=2 pair of NODES. This table exposes the
 * RESPONSIONS: the EDGES binding them — "this op, on this operand,
 * answers THIS way" (op (x) operand (x) responsion; srmech =
 * Stored-RELATIONSHIP Mechanism). Each entry is keyed by the
 * "<operator>|<carrier>" edge (operator = a tool-registry name,
 * carrier = a carrier-registry name — never a bare-name flat list) and
 * carries one-or-more responsions: the kind (propagator / resolvent /
 * closed_form / open_sustain / trace / response_curve), the regime
 * (continuous_spectral / discrete_algebraic — the two faces of ONE
 * responsion), the response form, and the honest verified-or-OPEN
 * status (the OPEN rows are the F929 dispatch _OPEN_HINTS residues,
 * verbatim).
 *
 * The table lives in the GENERATED translation unit
 * `srmech_responsion_registry.c` (regenerate with
 * c/tools/gen_responsion_registry.py); the accessors + the
 * whole-schema assembler live in srmech_responsion_schema.c.
 *
 * srmech_responsion_schema emits bytes BYTE-IDENTICAL to CPython
 *   json.dumps(srmech.introspect.responsion_schema._pure_responsion_schema(),
 *              sort_keys=True, separators=(",", ":"))
 * (each per-edge payload is baked pre-canonical; rows are in
 * byte-sorted key order == the sort_keys key order, so the assembler is
 * plain concatenation). This byte-identity IS the hash-ratchet contract
 * locking the C table to the Python SSoT.
 *
 * ABI-additive: new symbols + one struct, so SRMECH_ABI_VERSION stays 4.
 * ------------------------------------------------------------------ */

/* One responsion EDGE in the registry. All string pointers are
 * NUL-terminated ASCII (edge keys are dotted identifiers); `entry_json`
 * is the per-edge payload — a JSON ARRAY of responsion objects
 * {"answers_with","carrier","curvature","kind","operator","regime",
 * "status"} — as its pre-canonical compact-ASCII fragment (`entry_len`
 * bytes, excluding the NUL). ("curvature" = the rc237 F3 flat/curved
 * frame-independence class, sorted between "carrier" and "kind".) */
typedef struct {
    const char *key;           /* "<operator>|<carrier>" (the edge key) */
    const char *op_name;       /* the operator ref (a tool-registry name) */
    const char *carrier;       /* the carrier ref (a carrier-registry name) */
    size_t      n_responsions; /* responsions riding this edge           */
    const char *entry_json;    /* pre-canonical compact JSON array       */
    size_t      entry_len;     /* bytes in entry_json (excluding the NUL) */
} srmech_responsion_entry_t;

/* The compiled-in registry table + count (defined in the generated
 * srmech_responsion_registry.c). */
extern const srmech_responsion_entry_t srmech_responsion_registry_table[];
extern const size_t srmech_responsion_registry_len;

/* Number of registered responsion edges in the const table. */
size_t srmech_responsion_registry_count(void);

/* The entry at `index`, or NULL if `index` is out of range. */
const srmech_responsion_entry_t *srmech_responsion_registry_get(size_t index);

/* The entry whose edge `key` equals `key` (bounded linear scan), or
 * NULL for an unknown key / a NULL `key`. `key` must be NUL-terminated. */
const srmech_responsion_entry_t *srmech_responsion_registry_find(
    const char *key);

/* Assemble the whole responsion schema as canonical JSON (see
 * byte-identity contract above) into `buf` (capacity `buf_len`; NO
 * trailing NUL) and set *out_len to the byte count. If `buf` is NULL
 * this is a SIZE-QUERY (nothing written; *out_len receives the exact
 * full length). A too-small non-NULL `buf` returns SRMECH_ERR_OVERFLOW;
 * `out_len == NULL` returns SRMECH_ERR_NULL_ARG. */
srmech_status_t srmech_responsion_schema(char *buf, size_t buf_len,
                                         size_t *out_len);

/* ------------------------------------------------------------------ *
 * qm CONSTANT-matrix builders (0.9.0rc213, #755)
 *
 * The base qm constant matrices were Python LITERALS with no C source —
 * classified `composition_of_c`, yet a bare-C host could not produce the
 * constant DATA (a real python-free gap). These builders EMIT the
 * canonical constant data BYTE-IDENTICAL to the (rc212-canonicalized)
 * Python constants: every mathematically-zero slot is +0.0 (the Python
 * literals' -0.0 slots from `-1j` / `-1.0 · Mat` were canonicalized in
 * the same rc), integer entries are exact, and the two irrational
 * values (the λ⁸ 1/√3 normaliser; the SU(3) f^{458} = f^{678} = √3/2)
 * route through srmech's own libm-free srmech_rational_sqrt so the
 * double projection matches Python's float(rational.sqrt(3.0)) path
 * bit-for-bit.
 *
 * Layout: complex matrices are row-major interleaved (re,im) doubles
 * (the Mat carrier layout); the Minkowski metric is row-major REAL
 * doubles; structure constants are flat rank-3 row-major f[a][b][c].
 *
 * Errors: SRMECH_ERR_NULL_ARG (out NULL); SRMECH_ERR_BAD_INPUT
 * (selector out of range).
 *
 * ABI-additive: new symbols, no callback typedef — SRMECH_ABI_VERSION
 * stays 4. See srmech_qm_constants.c; parity attested by
 * tests/test_qm_constants_c_rc212.py.
 * ------------------------------------------------------------------ */

/* Pauli 2×2: which = 0 (σ_x), 1 (σ_y), 2 (σ_z), 3 (I₂). out = 8 doubles. */
srmech_status_t srmech_qm_pauli(int32_t which, double *out);

/* Dirac γ^mu 4×4 (Dirac/standard basis, Peskin-Schroeder eq 3.25):
 * mu in 0..3. out = 32 doubles. */
srmech_status_t srmech_qm_dirac_gamma(int32_t mu, double *out);

/* Mostly-minus Minkowski metric η = diag(+1,-1,-1,-1). out = 16 REAL
 * doubles (row-major, no interleaving — the real-Mat layout). */
srmech_status_t srmech_qm_minkowski_metric(double *out);

/* Gell-Mann λ^a 3×3 (Gell-Mann 1962 eq 16): a in 1..8. out = 18 doubles.
 * λ⁸ carries the 1/√3 normaliser via srmech_rational_sqrt. */
srmech_status_t srmech_qm_gell_mann(int32_t a, double *out);

/* SU(2) structure constants ε^{abc}. out = 27 doubles (f[a][b][c]). */
srmech_status_t srmech_qm_su2_structure(double *out);

/* SU(3) structure constants f^{abc} (Peskin-Schroeder eq 17.34), filled
 * by total antisymmetry; f^{458} = f^{678} = √3/2 via
 * srmech_rational_sqrt. out = 512 doubles (f[a][b][c]). */
srmech_status_t srmech_qm_su3_structure(double *out);

/* ------------------------------------------------------------------ *
 * srmech_text — text → tokens → co-occurrence ingestion peers
 * (v0.9.0rc217; gh #1360)
 *
 * The C mirror of `srmech.math.text` — the §40/§52 text→graph leaves of
 * the K1 presence-kernel chain `text → glyph_stream → cooccurrence_edges →
 * dense_laplacian`, plus the §52 streaming bounded top-K peer. The
 * corpus-linear hot loops (per-codepoint segmentation; windowed pair-count
 * accumulation; bounded chunk merge) run fully in C; the vocab-scale
 * string→id mapping stays host-side (the srmech_klein4_cooccurrence_fold
 * split precedent).
 *
 * BYTE-IDENTICAL parity contract: each op reproduces the pure-Python
 * `srmech.math.text` result EXACTLY (token stream, integer pair counts,
 * (-weight, index) tie-breaks, first-seen edge weights, lexicographic
 * edge order) — the correctness gate for the downstream Laplacian.
 *
 * rc287 replaced the word with the GLYPH CLUSTER as the unit. The
 * retired tokenizer's word decision carried a length floor, a casefold,
 * an English stoplist and an apostrophe special case — all of which were
 * Latin-shaped assumptions that mis-segmented most of the world's
 * scripts (scriptio continua fell into single 45-96 char "words"; ~89%
 * of resulting types were singletons). A UAX #29 extended grapheme
 * cluster is well-defined in EVERY script, so no per-language decision
 * is made at the front door.
 *
 * The break table stays CALLER-PROVIDED data (caller-arena discipline),
 * but unlike the retired tokenizer's tables it cannot be built from a
 * host interpreter: unicodedata exposes no grapheme-break property, no
 * Extended_Pictographic and no InCB. srmech vendors one attested default
 * (srmech_unicode_gb_tables.h) that both projections load and that
 * srmech_text_default_gb_table() hands to a bare-C host.
 *
 * All workspaces are caller arenas (JPL Rule 3); a too-small hash /
 * scratch arena returns SRMECH_ERR_OVERFLOW (grow + retry — the
 * OVERFLOW-not-wrap discipline; results are identical at any sufficient
 * capacity). ABI-additive: new symbols, no callback typedef —
 * SRMECH_ABI_VERSION stays 4. See srmech_text.c; parity attested by
 * tests/test_text_c_rc217.py.
 * ------------------------------------------------------------------ */

/* Expose the srmech-shipped DEFAULT UAX #29 break-property table
 * (srmech_unicode_gb_tables.h; UCD 16.0.0, attested + re-derivable via
 * c/tools/gen_unicode_gb_tables.py --verify). This is the entry point that
 * lets a BARE-C HOST WITH NO PYTHON PRESENT segment the full Unicode
 * domain (ADR-0003): call this, then pass the four values straight to
 * srmech_text_glyph_stream. A host with its own table skips this and
 * passes that table instead — the table is an INPUT, never a hidden
 * global, so the op stays reentrant and arena-safe. */
void srmech_text_default_gb_table(
    const uint32_t **out_lo, const uint32_t **out_hi,
    const uint8_t **out_prop, size_t *out_n_ranges);

/* Segment NFC-normalized UTF-8 `text` into UAX #29 EXTENDED GRAPHEME
 * CLUSTERS — the glyph stream (rc287). Writes *out_n + 1 ascending byte
 * offsets into `out_off`, so cluster i spans [out_off[i], out_off[i+1]);
 * the trailing sentinel is text_len. out_cap >= text_len + 1 always
 * suffices (one cluster per byte is the worst case).
 *
 * The break table (lo/hi/prop/n_ranges, ascending non-overlapping ranges;
 * packed byte = gbp in bits 0-3, Extended_Pictographic in bit 4, InCB in
 * bits 5-6) is a CALLER-PROVIDED input — see srmech_text_default_gb_table.
 * Hangul LV/LVT are recovered by the UAX #29 §3 syllable algebra and are
 * deliberately absent from the table; jamo L/V/T are present as rows.
 *
 * Implements GB1..GB999 including GB9c (Indic conjuncts, Unicode 15.1)
 * and GB11 (emoji ZWJ sequences); scores 1093/1093 on the official
 * GraphemeBreakTest.txt (tests/test_glyph_stream_conformance_rc287.py).
 * Malformed UTF-8 → SRMECH_ERR_BAD_INPUT; too-small out_cap →
 * SRMECH_ERR_OVERFLOW (grow + retry; results identical at any sufficient
 * capacity). */
srmech_status_t srmech_text_glyph_stream(
    const uint8_t *text, size_t text_len,
    const uint32_t *lo, const uint32_t *hi, const uint8_t *prop,
    size_t n_ranges, uint32_t *out_off, size_t out_cap, size_t *out_n);

/* Expose the srmech-shipped DEFAULT combining-mark fold table
 * (srmech_unicode_fold_tables.h; UCD 16.0.0, attested + re-derivable via
 * c/tools/gen_unicode_fold_tables.py --verify). This is the entry point
 * that lets a BARE-C HOST WITH NO PYTHON PRESENT fold marks over the full
 * Unicode domain (ADR-0003) - there is no `unicodedata` to ask, which is
 * why the table is vendored at all. Call this, then pass the four values
 * straight to srmech_text_fold_marks. A host with its own table skips this
 * and passes that table instead - the table is an INPUT, never a hidden
 * global, so the op stays reentrant and arena-safe. */
void srmech_text_default_fold_table(
    const uint32_t **out_lo, const uint32_t **out_hi,
    const uint32_t **out_rep, size_t *out_n_ranges);

/* Drop combining marks from UTF-8 `text` by Unicode General_Category
 * (Mn / Mc / Me) - the language-agnostic fold (rc293). Writes the folded
 * UTF-8 bytes to `out` and the byte length to *out_len.
 *
 * The NAME is the contract: a VIRAMA is a mark, not an accent, so this is
 * fold_marks and never fold_accents - the Latin-shaped name would be wrong
 * in exactly the Indic cases that matter most.
 *
 * Category ONLY: no case change, no locale tailoring, no NFKD/compatibility
 * folding, no ligature expansion. So U+00F8 is unchanged (a stroke is part
 * of the letter, not a mark), and Hangul is unchanged in either
 * normalization form (it decomposes to jamo, which are starters).
 *
 * The fold table (lo/hi/rep/n_ranges, ascending non-overlapping ranges) is a
 * CALLER-PROVIDED input - see srmech_text_default_fold_table. A row payload
 * of SRMECH_FOLD_DROP (0) deletes the codepoint; any other value REPLACES
 * it. Replacements are transitively resolved in the table, so ONE pass is
 * sufficient and no decomposition buffer or recursion is needed.
 *
 * Needs no normalizer: precomposed characters are handled by the map rows
 * and decomposed sequences by the drop rows, so the same marks fall out
 * whichever form the caller supplies (verified over the whole codepoint
 * domain: NFC(fold(NFC(s))) == NFC(fold(NFD(s)))).
 *
 * Folding never GROWS the UTF-8 byte length (asserted by the generator), so
 * out_cap >= text_len always suffices. Malformed UTF-8 ->
 * SRMECH_ERR_BAD_INPUT; too-small out_cap -> SRMECH_ERR_OVERFLOW (grow +
 * retry; results identical at any sufficient capacity). */
srmech_status_t srmech_text_fold_marks(
    const uint8_t *text, size_t text_len,
    const uint32_t *lo, const uint32_t *hi, const uint32_t *rep,
    size_t n_ranges, uint8_t *out, size_t out_cap, size_t *out_len);

/* Windowed unordered co-occurrence pair counts over per-document vocab-id
 * streams (doc d = tok_ids[doc_off[d] .. doc_off[d+1]); the window resets
 * at every document boundary), aggregated in the caller hash arena
 * (ht_keys/ht_vals; power-of-two ht_cap; load kept <= 1/2 else
 * SRMECH_ERR_OVERFLOW). On success the *out_n_edges distinct pairs sit
 * compacted + sorted at the FRONT of ht_keys (key = (u<<32)|v, u < v —
 * lexicographic edge order) with parallel integer counts in ht_vals. */
srmech_status_t srmech_text_cooccurrence_edges(
    const uint32_t *tok_ids, size_t n_tok,
    const size_t *doc_off, size_t n_docs, uint32_t window, uint32_t n_vocab,
    uint64_t *ht_keys, uint64_t *ht_vals, size_t ht_cap, size_t *out_n_edges);

/* srmech_text_cooccurrence_edges_directed — the directed=True SUPERSET
 * (#1390 item 1). Same arena discipline, but on the canonical unordered
 * key it fills two output columns: ht_metric (== the undirected weight,
 * fwd+bwd) and ht_charge (signed, fwd-bwd — +1 when the earlier-position
 * token has the smaller id, else -1). On success out_n_edges canonical
 * edges sit at the front of ht_keys with parallel ht_metric / ht_charge.
 * ADDITIVE symbol — SRMECH_ABI_VERSION stays 5. */
srmech_status_t srmech_text_cooccurrence_edges_directed(
    const uint32_t *tok_ids, size_t n_tok,
    const size_t *doc_off, size_t n_docs, uint32_t window, uint32_t n_vocab,
    uint64_t *ht_keys, uint64_t *ht_metric, int64_t *ht_charge, size_t ht_cap,
    size_t *out_n_edges);

/* One §52 bounded top-K chunk FLUSH: accumulate the chunk's windowed pair
 * counts (same loop as cooccurrence_edges), then merge each touched
 * node's directed neighbours into its bounded store row — full
 * within-chunk weights sum BEFORE any truncation; a row exceeding `cap`
 * truncates to the cap best by (-weight, neighbour). store_nbr/store_w
 * are n_vocab × cap row-major (neighbour-ascending rows); store_len[u]
 * counts row u's live entries. `dir` (2·distinct-pairs records) and
 * `scr` (one node's merge: up to cap + its chunk-degree records) are
 * uint64-PAIR record scratch arenas. */
srmech_status_t srmech_text_cooccurrence_topk(
    const uint32_t *tok_ids, size_t n_tok,
    const size_t *doc_off, size_t n_docs, uint32_t window, uint32_t cap,
    uint32_t n_vocab, uint32_t *store_nbr, uint64_t *store_w,
    uint32_t *store_len, uint64_t *ht_keys, uint64_t *ht_vals, size_t ht_cap,
    uint64_t *dir, size_t dir_cap_recs, uint64_t *scr, size_t scr_cap_recs);

/* The §52 final read-out of the bounded store: per node u (ascending),
 * rank its row by (-weight, neighbour) and keep the top k into
 * topk_nbr/topk_w (n_vocab × k row-major; topk_len[u] live, in ranked
 * order — the per-token `topk` view), and union those entries into the
 * deduplicated sparse edge list with the FIRST-SEEN weight, sorted by
 * (min, max) key. edge_recs needs Σ_u min(store_len[u], k) 3-uint64
 * records of scratch and returns *out_n_edges 2-uint64 (key, weight)
 * records compacted at its front; node_scr holds `cap` 2-uint64 records. */
srmech_status_t srmech_text_cooccurrence_topk_extract(
    const uint32_t *store_nbr, const uint64_t *store_w,
    const uint32_t *store_len, uint32_t n_vocab, uint32_t cap, uint32_t k,
    uint32_t *topk_nbr, uint64_t *topk_w, uint32_t *topk_len,
    uint64_t *edge_recs, size_t edge_cap_recs, size_t *out_n_edges,
    uint64_t *node_scr, size_t node_scr_cap_recs);

/* ------------------------------------------------------------------ *
 * rc219 (gh #827): the encode-pipeline's other half — batched C peers.
 *
 * srmech_rbs_lm_* mirrors the `srmech.rbs_lm.substrate` Klein-4 encode
 * kernels (srmech_rbs_lm.c): the per-token word encode and the WHOLE
 * last-k-token context-window encode in ONE call (profile: ~90%+ of the
 * measured 127 ms/window at D=4096, k=16 was Python per-token
 * orchestration + k FFI hops around a few ms of C work). EXACT
 * byte-identical parity — every leaf is integer/byte (sha256 seeds,
 * the CPython-replicating MT19937 mint, XOR bind, strict majority
 * bundle).
 *
 * srmech_spectral_* mirrors the per-state half of `srmech.spectral`
 * decompose/recompose over the CACHED eigenbasis
 * (srmech_spectral_codec.c): marshal + matvec + complex128 pack + sha
 * in one crossing, through the SAME srmech_dense_matmul_complex kernel
 * the carrier route uses. NUMERIC float-eig-derived parity: same-machine
 * byte-identity by construction; cross-platform/arm within-tol only
 * (the rc218 macOS lesson — never a hardcoded cross-platform SHA).
 *
 * All workspaces are caller arenas (JPL Rule 3). ABI-additive: new
 * symbols, no callback typedef — SRMECH_ABI_VERSION stays 4.
 * Parity attested by tests/test_rbs_lm_encode_context_rc219.py +
 * tests/test_spectral_c_peer_rc219.py.
 * ------------------------------------------------------------------ */

/* One token → its Klein-4 word vector, byte-identical to
 * substrate.encode_word_byteglyph (enc_mode 0) / encode_word_k4 (enc_mode 1):
 *   byteglyph — klein4_encode_bytes over the token's UTF-8 bytes (an empty
 *               token routes to the seed-0 neutral atom), then the sector
 *               XOR bind;
 *   wordhash  — klein4_random seeded by token_seed(tok, hex_chars) (the
 *               sha256 hex prefix as a CPython init_by_array key), then the
 *               sector XOR bind.
 * `acc` is a (1 + 2*D) uint32 caller accumulator; `scratch` is 3*D caller
 * bytes; `out` is D bytes. sector <= 3; enc_mode wordhash needs hex_chars in
 * 1..64 (byteglyph ignores it). tok may be NULL iff tok_len == 0. */
srmech_status_t srmech_rbs_lm_encode_word(
    const uint8_t *tok, size_t tok_len, uint32_t D, uint8_t sector,
    uint32_t hex_chars, uint32_t enc_mode, uint32_t *acc, uint8_t *scratch,
    uint8_t *out);

/* The WHOLE last-k-token context window → ONE Klein-4 state, byte-identical
 * to ContextSubstrate.encode_context: per token p, klein4_bind(pos_key(p),
 * enc(token_p)) (pos_key = the wordhash atom of "__ctx_pos_{p}__", enc_mode-
 * independent), majority-bundled with the even-count odd-pad (an even window
 * — including the empty one — APPENDS the fixed neutral pad
 * enc("__bundle_pad__"); never drops a real token). Tokens ride as
 * concatenated UTF-8 `tok_bytes` + n_tokens+1 `tok_off` offsets. `pad` may be
 * the caller's precomputed D-byte pad vector (the substrate caches it) or
 * NULL to compute it here.
 *
 * mint_cache / mint_flags (BOTH non-NULL or both NULL) are an optional
 * caller-owned WINDOW-INVARIANT mint cache — the dominant residual cost of
 * the collapsed call is the MT19937 mints (~85 µs each at D=4096; ~260 per
 * byteglyph window), and the byte vocab, byteglyph position keys and window
 * position keys are the same on every call. Layout: (256 + n_bytepos +
 * n_ctxpos) D-byte rows — [0,256) the byte vocab (seed = byte value),
 * [256, 256+n_bytepos) the byteglyph position keys (seed 0x10000+i),
 * [256+n_bytepos, ...) the RAW (pre-sector-bind) window position-key mints —
 * with one occupancy flag byte per row (mint_flags, zero-initialised by the
 * caller ONCE; rows fill lazily and persist across calls). A cached mint is
 * byte-identical to a fresh one by construction; byte positions ≥ n_bytepos /
 * window positions ≥ n_ctxpos simply mint uncached. The caller must never
 * mutate the arenas and must pass the SAME pair while D / sector / hex_chars
 * stay fixed (the Python ContextSubstrate owns one pair per instance, exactly
 * like its pure-path _poskey dict).
 *
 * acc_outer / acc_inner are (1 + 2*D) uint32 caller accumulators; `scratch`
 * is 4*D caller bytes; `out` is D bytes. */
srmech_status_t srmech_rbs_lm_encode_context(
    const uint8_t *tok_bytes, const uint32_t *tok_off, uint32_t n_tokens,
    uint32_t D, uint8_t sector, uint32_t hex_chars, uint32_t enc_mode,
    const uint8_t *pad, uint8_t *mint_cache, uint8_t *mint_flags,
    uint32_t n_bytepos, uint32_t n_ctxpos, uint32_t *acc_outer,
    uint32_t *acc_inner, uint8_t *scratch, uint8_t *out);

/* coeffs = Vᴴ·state over the CACHED eigenbasis + the complex128 pack + the
 * Class-A content sha, in one call. `v_interleaved` is the n×n eigenvector
 * Mat buffer (row-major interleaved (re, im); columns = eigenvectors), read
 * zero-copy; `state_interleaved` is n interleaved pairs; `scratch_vh` is a
 * 2*n*n-double caller arena (the Vᴴ staging — exact transpose + imag
 * sign-flip, then the SAME srmech_dense_matmul_complex kernel the carrier
 * mat_matvec route dispatches to); `out_coeffs` is 2*n doubles whose raw
 * bytes ARE the SpectralHandle coefficients_bytes; `out_sha_hex` is 65 bytes
 * (their lowercase content sha). No aliasing between scratch/out and the
 * inputs. NUMERIC parity: same-machine byte-identity by construction;
 * cross-platform within-tol only. */
srmech_status_t srmech_spectral_decompose(
    uint32_t n, const double *v_interleaved, const double *state_interleaved,
    double *scratch_vh, double *out_coeffs, char *out_sha_hex);

/* state = V·coeffs — the inverse projection back to the node domain, through
 * the same public matmul kernel (n×n · n×1). `coeffs_interleaved` is the
 * handle's coefficients_bytes viewed as 2*n doubles; `out_state` is 2*n
 * doubles (must not alias the inputs). */
srmech_status_t srmech_spectral_recompose(
    uint32_t n, const double *v_interleaved, const double *coeffs_interleaved,
    double *out_state);

#ifdef __cplusplus
}
#endif

#endif /* SRMECH_H */
