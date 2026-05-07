/*
 * ephemerides-spectral — C BIP encoder
 *
 * ALU-native integer-only port of the Phase 9 breathing Laplacian /
 * BIP encode_state path from the Python `ephemerides-spectral` package.
 * Source compiles cleanly under -std=c11 / c17; the Makefile defaults
 * to c17, drops to c11 for older toolchains.
 *
 * Targets: ESP32 / Cortex-M / RISC-V — anywhere with int64 arithmetic
 * and no FPU. No libm, no malloc, no Skyfield, no Python at runtime.
 *
 * Algebra
 * -------
 *   Phase composition lives in Z_{2^32}. (a + b) mod 2^32 is implicit
 *   uint32 overflow. One full revolution = MODULO = 2^32 residues.
 *
 *   Frequencies (omega_diag, scaled couplings) are stored as int64
 *   residues/day in Q-format. Conversion from continuous omega
 *   (rad/day) is omega_int = round(omega / (2*pi) * 2^32).
 *
 * Phase 9 breathing
 * -----------------
 *   Off-diagonal weights modulate as W_ij(phi) = W_ij^(0) *
 *   (1 + alpha * cos(n_a*phi_a - m_b*phi_b)). The cos() is evaluated
 *   through a precomputed int32 cosine LUT (1024 entries, Q1.14
 *   amplitude, 4 KB). No FPU calls in the hot path.
 *
 *   Mathematical positioning: state-dependent (non-autonomous) graph
 *   Laplacian / adaptive Kuramoto-family network with phase-difference-
 *   dependent (PDDP) coupling. See ../docs/antikythera-maths/
 *   ephemerides_spectral_research_notebook.md §1.4.
 *
 * Bounds
 * ------
 *   delta_t_days must satisfy |delta_t| <= ES_DELTA_DAYS_LIMIT
 *   (~6.8e8 days = ~1.86 Myr). Outside this envelope, omega * delta_t
 *   would saturate int64 and corrupt the result.
 *
 * License: GPL-3.0-or-later (parent project: mlehaptics).
 */

#ifndef EPHEMERIDES_SPECTRAL_H
#define EPHEMERIDES_SPECTRAL_H

#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ------------------------------------------------------------------ *
 * Compile-time constants
 * ------------------------------------------------------------------ */

/* Number of bodies in the Sol Star System Laplacian.
 *
 *   v0.1.0 baseline (26):  sun + 9 planets + 12 major moons + 4 asteroids
 *   v0.5.0 expansion (+12): Jupiter inner regulars (Metis, Adrastea,
 *                           Amalthea, Thebe) + classical Saturnians
 *                           (Mimas, Tethys, Dione, Hyperion, Iapetus,
 *                           Phoebe) + Saturn co-orbitals (Janus,
 *                           Epimetheus). Total: 38.
 *
 * Pinned by the codegen-emitted body table in es_bodies.c via
 * _Static_assert. Name field is 16 bytes including NUL.
 */
#define ES_N_BODIES        52u

/* Phase-residue cyclic group: Z_{2^32}. Power-of-2 modulus = free
 * uint32 overflow.
 */
#define ES_K_BITS          32u
#define ES_MODULO_MASK     0xFFFFFFFFu

/* Reference Julian Date (J2000.0). All phases are calibrated against
 * this epoch and integrated forward/backward from it.
 */
#define ES_REFERENCE_JD    2451545.0

/* Pre-flight bounds limit: |jd_tdb - REFERENCE_JD| in days.
 * 6.8e8 days = ~1.86 Myr; outside this, omega * delta_t saturates int64.
 */
#define ES_DELTA_DAYS_LIMIT 6.8e8

/* Phase 9 breathing chunk size (days per integration step).
 * 30-day chunks balance LUT-lookup overhead against breathing fidelity.
 */
#define ES_CHUNK_DAYS      30

/* Phase 9 breathing modulation depth (alpha = NUM/DEN = 0.1 = 1/10).
 * Phenomenological per Phase 9; v0.3.x will derive from a Hamilton/
 * Delaunay-variable Lagrangian.
 */
#define ES_BREATHING_NUM   1
#define ES_BREATHING_DEN   10

/* Off-diagonal coupling LUT (1024 x int32, Q1.14, 4 KB). */
#define ES_COSINE_LUT_BITS 10u
#define ES_COSINE_LUT_SIZE (1u << ES_COSINE_LUT_BITS)
#define ES_COSINE_LUT_AMP  (1 << 14)        /* +/- 16384, Q1.14       */

/* ------------------------------------------------------------------ *
 * Status / error codes
 * ------------------------------------------------------------------ */

typedef enum {
    ES_OK                       = 0,
    ES_ERR_DELTA_OUT_OF_RANGE   = 1, /* |delta_t_days| > ES_DELTA_DAYS_LIMIT */
    ES_ERR_NULL_OUTPUT          = 2, /* phases_out == NULL                  */
    ES_ERR_NON_FINITE_INPUT     = 3, /* delta_t_days is NaN or +/-inf       */
    ES_ERR_INVALID_INDEX        = 4, /* body index >= ES_N_BODIES (v0.6.0) */
    ES_ERR_INVALID_KIND         = 5, /* syzygy kind not in {0,1,2} (v0.6.0) */
    ES_ERR_INVALID_THRESHOLD    = 6, /* threshold not in (0, 0.5] (v0.6.0)  */
} es_status_t;

/* Body category enum (mirrors the Python `Body.category` field). */
typedef enum {
    ES_CATEGORY_STAR     = 0,
    ES_CATEGORY_PLANET   = 1,
    ES_CATEGORY_MOON     = 2,
    ES_CATEGORY_ASTEROID = 3,
} es_category_t;

/* ------------------------------------------------------------------ *
 * Body metadata (codegen-emitted in es_bodies.c)
 * ------------------------------------------------------------------ */

typedef struct {
    /* ASCII body name, NUL-terminated. Up to 16 chars including NUL. */
    char            name[16];
    /* Sidereal period in days; 0.0 for the Sun. */
    double          period_days;
    /* Mass relative to Earth. */
    double          mass_earth;
    es_category_t   category;
} es_body_t;

extern const es_body_t  es_bodies[ES_N_BODIES];

/* Body name lookup. Returns ES_N_BODIES (sentinel) if not found.
 * Linear scan; with N=26 this is cheap and avoids a hash-table dep.
 */
size_t es_body_index(const char *name);

/* ------------------------------------------------------------------ *
 * Laplacian table (codegen-emitted)
 * ------------------------------------------------------------------ */

/* Per-body diagonal frequency (residues/day, signed int64).
 * Sum of L_trunk + L_pn (mean motion + Mercury PN correction).
 *
 * Q-format: omega_int = round(omega_rad_per_day / (2*pi) * 2^32).
 * Range examples:
 *   - Earth:  ~11.76e6 residues/day
 *   - Phobos: ~13.5e9 residues/day (smallest period, largest omega)
 *   - Sun:    0
 */
extern const int64_t es_omega_diag[ES_N_BODIES];

/* Per-body initial phase residue at REFERENCE_JD = J2000.0 (uint32,
 * Z_{2^32}). Calibrated from JPL DE441 ground truth at codegen time.
 */
extern const uint32_t es_initial_phases[ES_N_BODIES];

/* Off-diagonal coupling entry for the Phase 9 breathing path. */
typedef struct {
    /* Indices into es_bodies (es_omega_diag, es_initial_phases). */
    uint8_t  idx_a;
    uint8_t  idx_b;
    /* Resonance multipliers: cos(n_a * phi_a - m_b * phi_b). */
    uint8_t  n_a;
    uint8_t  m_b;
    /* Static coupling weight in residues/day (signed int64). */
    int64_t  weight_rpd;
} es_coupling_t;

/* Number of off-diagonal couplings in the Phase 9 path. */
extern const size_t es_n_couplings;

/* The coupling table itself. v0.1.0 wires only the Jupiter-Saturn 5:2
 * entry; future revisions will extend (Neptune-Pluto 3:2, Io-Europa
 * 1:2, etc. — see the ROADMAP).
 */
extern const es_coupling_t es_couplings[];

/* ------------------------------------------------------------------ *
 * Cosine LUT (built at startup; no libm dependency)
 * ------------------------------------------------------------------ */

/* Pre-built integer cosine LUT. Initialised in es_cosine_lut.c by
 * a startup routine that uses ONLY integer arithmetic + a small
 * constant table — no calls to libm's cos().
 *
 * Index k -> round(cos(2*pi * k / ES_COSINE_LUT_SIZE) * ES_COSINE_LUT_AMP).
 */
extern const int32_t es_cosine_lut[ES_COSINE_LUT_SIZE];

/* Look up cos(n_lobes * phase_residue * 2*pi / 2^32) as a Q1.14
 * integer in [-ES_COSINE_LUT_AMP, +ES_COSINE_LUT_AMP].
 */
int32_t es_cos_lut(uint32_t phase_residue, uint32_t n_lobes);

/* ------------------------------------------------------------------ *
 * Encode-state API
 * ------------------------------------------------------------------ */

/* Encode the Sol Star System state at a given JD relative to
 * REFERENCE_JD. Returns ES_N_BODIES uint32 phase residues in
 * phases_out[0..ES_N_BODIES-1].
 *
 * Strict pre-flight bounds check: rejects |delta_t_days| >
 * ES_DELTA_DAYS_LIMIT or non-finite inputs before any math runs.
 * Per the Phase 9 design, the only float input is delta_t_days; all
 * arithmetic from there is integer (int64 / uint64 / uint32).
 *
 * Returns ES_OK on success, an es_status_t error code otherwise.
 *
 * Thread-safety: this function is reentrant; the only shared state
 * is the const tables (es_bodies, es_omega_diag, es_initial_phases,
 * es_couplings, es_cosine_lut).
 */
es_status_t es_encode_state(double delta_t_days,
                            uint32_t phases_out[ES_N_BODIES]);

/* Convenience: encode at an absolute JD (TDB). Equivalent to
 * es_encode_state(jd_tdb - ES_REFERENCE_JD, phases_out).
 */
es_status_t es_encode_at_jd(double jd_tdb,
                            uint32_t phases_out[ES_N_BODIES]);

/* ------------------------------------------------------------------ *
 * Helpers (cyclic-group binding)
 * ------------------------------------------------------------------ */

/* Modular addition in Z_{2^32} — the BIP "bind" operator. Implicit
 * uint32 overflow is the cyclic-group reduction.
 */
static inline uint32_t es_bind(uint32_t a, uint32_t b) {
    return (uint32_t)(a + b);
}

/* Convert a uint32 phase residue to radians (only float touchpoint;
 * provided as a courtesy for callers that need to cross back to
 * continuous angles). The encode path itself never calls this.
 */
double es_residue_to_radians(uint32_t residue);

/* ------------------------------------------------------------------ *
 * Diagnosed-fiber runtime overlay (v0.4.1, ABI v2)
 * ------------------------------------------------------------------ *
 *
 * Patches are an additive layer on top of the published spectral
 * kernel — DATA, not code edits. The encode path consults the
 * registry AFTER the base loop has finished and contributes per-body
 * residue deltas BEFORE the final cyclic-group reduction. The base
 * encoder bytes never change.
 *
 * Two patch kinds, mirroring the Python `diagnosed_fibers` module:
 *
 *   ES_PATCH_KIND_SINUSOID:
 *      diagonal — adds A * sin(2*pi * dt / period + phi) to one body
 *      (`body_idx_a`). `body_idx_b` and `correlation` are ignored.
 *
 *   ES_PATCH_KIND_COUPLED_SINUSOID:
 *      off-diagonal — adds A * sin(...) to body_a, and
 *      `correlation` * A * sin(...) to body_b.
 *      `correlation` must be +1 or -1.
 *
 * Capacity: ES_MAX_PATCHES (32). `es_apply_patch` returns
 * ES_ERR_PATCH_FULL when the registry is at capacity.
 *
 * Threading: NOT thread-safe. The registry is a process-global state
 * shared by all callers; serialise apply/clear/encode from the caller
 * side if you have multiple threads. Encoding alone IS reentrant
 * (no mutation), but a concurrent apply/clear from another thread
 * could split a patch's contribution mid-encode.
 *
 * Floating-point note: the patch evaluation calls libm `sin()` via
 * the standard <math.h>. This is the ONLY libm dependency in the
 * encode path; it only fires when patches are active. If you've
 * compiled in a libm-free environment, leave the patch registry
 * empty (the default) and the libm reference is not pulled in.
 */

#define ES_MAX_PATCHES      32
#define ES_PATCH_NAME_MAX   64

typedef enum {
    ES_PATCH_KIND_SINUSOID         = 0,
    ES_PATCH_KIND_COUPLED_SINUSOID = 1,
} es_patch_kind_t;

typedef struct {
    int32_t  kind;                          /* es_patch_kind_t */
    char     name[ES_PATCH_NAME_MAX];
    int32_t  body_idx_a;                    /* [0, ES_N_BODIES); -1 = unused */
    int32_t  body_idx_b;                    /* coupled only; -1 for sinusoid */
    double   amplitude_deg;
    double   period_days;
    double   phase_rad;
    int32_t  correlation;                   /* +1 or -1; coupled only        */
} es_patch_t;

/* Status codes specific to the patch registry. Returned by
 * es_apply_patch / es_get_patch_at. Values disjoint from
 * es_status_t so callers can distinguish patch errors at the API
 * boundary without losing the original status enum.
 */
#define ES_ERR_PATCH_FULL           100  /* registry at capacity            */
#define ES_ERR_PATCH_DUPLICATE_NAME 101  /* same name already active        */
#define ES_ERR_PATCH_BAD_KIND       102  /* unknown kind value              */
#define ES_ERR_PATCH_BAD_INDEX      103  /* body_idx out of [0, N_BODIES)   */
#define ES_ERR_PATCH_BAD_PARAM      104  /* period <= 0, |correlation| != 1 */
#define ES_ERR_PATCH_OUT_OF_RANGE   105  /* es_get_patch_at: idx >= count   */

/* Apply a patch into the registry. Validates kind, body indices, and
 * that the period_days > 0; for coupled-sinusoid kind, also checks
 * correlation in {-1, +1}.
 *
 * Returns ES_OK on success, or one of the ES_ERR_PATCH_* codes.
 * The patch is COPIED — the caller can free its argument after the
 * call returns.
 */
int es_apply_patch(const es_patch_t *patch);

/* Clear every active patch. Returns the count of patches that were
 * cleared (always >= 0). Idempotent: calling on an empty registry
 * returns 0 with no side effects.
 */
size_t es_clear_patches(void);

/* Number of patches currently in the registry. */
size_t es_n_active_patches(void);

/* Read-back accessor: copies the patch at `idx` into `*out`.
 * Returns ES_OK on success, ES_ERR_PATCH_OUT_OF_RANGE if idx is past
 * the end, ES_ERR_NULL_OUTPUT if `out` is NULL.
 */
int es_get_patch_at(size_t idx, es_patch_t *out);

/* ------------------------------------------------------------------ *
 * C/Python parity Tier 1 (v0.6.0, ABI v3)
 * ------------------------------------------------------------------ *
 *
 * Two new entry points so the bridge's Python-only methods get a C
 * twin. The byte-identical-or-ULP-matching parity discipline is
 * pinned by tests/test_parity_smoke.py — every encoder-touching
 * bridge method has a paired (Python, C) test that compares output.
 *
 * es_breathing_modulation: exposes the resonant-pair phase residue +
 *   integer-cosine-LUT modulation that lives inside es_encode_state's
 *   inner off-diagonal loop. Same arithmetic, evaluated at one JD
 *   without running the full encode.
 *
 * es_find_syzygies: enumerates new-moon / full-moon syzygies in a
 *   JD window via fixed-period synodic + draconic month arithmetic.
 *   No encoder calls; pure modular reduction. Mirrors the Python
 *   `_research/syzygy_window.py` algorithm 1:1.
 */

/* Resonant-pair breathing modulation at a single JD.
 *
 *   delta_t_days     = jd_tdb - ES_REFERENCE_JD
 *   body_idx_a/b     = indices into es_bodies (e.g. via es_body_index)
 *   n_a / n_b        = resonance multiplicities (e.g. (5, 2) for J-S)
 *   *out_phase       = (n_a * phi_a - n_b * phi_b) mod 2^32
 *   *out_cos_q14     = es_cos_lut(*out_phase, 1) — the integer LUT value
 *   *out_modulation  = 1 + 0.1 * (cos_q14 / ES_COSINE_LUT_AMP) — the
 *                      breathing factor multiplying the static off-
 *                      diagonal coupling weight at this JD
 *
 * Returns ES_OK on success; ES_ERR_NULL_OUTPUT on null pointer args;
 * ES_ERR_INVALID_INDEX on out-of-bounds body indices;
 * ES_ERR_NON_FINITE_INPUT on NaN/inf delta_t_days.
 */
es_status_t es_breathing_modulation(double delta_t_days,
                                    size_t body_idx_a,
                                    size_t body_idx_b,
                                    int n_a,
                                    int n_b,
                                    uint32_t *out_phase,
                                    int32_t *out_cos_q14,
                                    double *out_modulation);

/* Syzygy candidate (one entry per detected event). Mirrors the Python
 * SyzygyCandidate dataclass:
 *   jd_tdb            = candidate JD (TDB)
 *   kind              = 0 for solar (new moon), 1 for lunar (full moon)
 *   synodic_phase_resid = always 0 by enumeration construction
 *   draconic_phase_resid = how close to a node-crossing (0 = exact)
 *   score             = sqrt(syn^2 + drc^2); lower is stronger
 */
#define ES_SYZYGY_KIND_SOLAR  0
#define ES_SYZYGY_KIND_LUNAR  1

typedef struct {
    double  jd_tdb;
    int32_t kind;
    double  synodic_phase_resid;
    double  draconic_phase_resid;
    double  score;
} es_syzygy_t;

/* Enumerate syzygies in [jd_lo, jd_hi] (TDB).
 *
 *   kind:           0 = solar only, 1 = lunar only, 2 = both ("all")
 *   threshold:      score cutoff in (0, 0.5]
 *   max_candidates: hard cap; enumeration stops at this many
 *   out_buf:        caller-provided buffer of capacity `out_capacity`
 *                   es_syzygy_t entries
 *   *out_count:     number written (may be < out_capacity OR
 *                   max_candidates)
 *
 * Returns ES_OK on success. Truncates silently if more candidates
 * exist than out_capacity (caller can detect this via `*out_count
 * == out_capacity`).
 */
#define ES_SYZYGY_KIND_FILTER_SOLAR  0
#define ES_SYZYGY_KIND_FILTER_LUNAR  1
#define ES_SYZYGY_KIND_FILTER_ALL    2

es_status_t es_find_syzygies(double jd_lo,
                             double jd_hi,
                             int kind,
                             double threshold,
                             size_t max_candidates,
                             es_syzygy_t *out_buf,
                             size_t out_capacity,
                             size_t *out_count);

/* ------------------------------------------------------------------ *
 * C/Python parity Tier 2a (v0.6.1, ABI v4) — channel basis foundation
 * ------------------------------------------------------------------ *
 *
 * Tier 2 brings the FPU-side hyperdimensional state into C so
 * `bridge.get_local_view` and `bridge.get_eclipse_probability` get
 * matching backend="c" paths. Phase 2a is the foundation:
 *
 *   - `es_complex64_t`: shared complex-pair representation. Two
 *     contiguous `float` (real, imag); 8 bytes per element. Matches
 *     numpy's `complex64` so callers can read the result directly.
 *
 *   - `es_channel_basis(seed, out, D)`: fills `out[D]` with the
 *     deterministic random unit-magnitude complex hypervector
 *     constructed from `seed` via splitmix64.
 *
 * Why complex64 not complex128: a D=65536 hypervector is 1 MB at
 * complex128 vs 512 KB at complex64. The basis-byte values are
 * generated from a uniform-2π PRNG — float32 precision is ample for
 * the basis itself; the consumer can promote to complex128 if any
 * downstream op needs the extra precision. Phase 2b (the actual HD
 * encode / observer-bind / eclipse projection) will pick complex64
 * for in-C state and complex128 for the boundary with Python's
 * scipy-bound paths.
 *
 * The `es_channel_basis` function does NOT divide by sqrt(D). The
 * Python ref instrument's `_initialize_bases` divides by sqrt(D) at
 * basis construction; that scaling is applied by the caller in C
 * when needed (typically by the HD-encode pipeline or the observer-
 * bind path) to keep the C-side basis primitive minimal.
 */

typedef struct {
    float real;
    float imag;
} es_complex64_t;

/* Fill `out[D]` with the unit-magnitude complex hypervector
 * `exp(1j * uniform(0, 2π))` for each element, seeded from `seed`.
 *
 * `seed` is the 64-bit splitmix64 seed; the Python side uses
 * `seed = 2026 + body_index` for the body channel bases, `seed = 9999`
 * for the topocentric coord basis, `seed = 777` for the syzygy node
 * basis. (The integer constants are SSOT in the Python ref instrument
 * and mirrored at the call site, not here.)
 *
 * Returns ES_OK on success; ES_ERR_NULL_OUTPUT if `out == NULL`.
 *
 * Bit-parity: matches `_research/portable_prng.splitmix64_phases(seed, D)`
 * followed by `[exp(1j * φ) for φ in phases]` byte-for-byte (modulo
 * complex64 vs complex128 casting; the float32 truncation is
 * deterministic).
 */
es_status_t es_channel_basis(uint64_t seed,
                             es_complex64_t *out,
                             size_t D);

/* ------------------------------------------------------------------ *
 * C/Python parity Tier 2b (v0.7.0, ABI v5) — HD encode + observer-bind
 * + eclipse projection
 * ------------------------------------------------------------------ *
 *
 * Three new entry points so the FPU-side hyperdimensional surface gets
 * a `backend="c"` path. The Python-and-C agreement is the BIP-and-lift
 * pipeline:
 *
 *   1. Encode 38 × uint32 phase residues via the existing
 *      `es_encode_state` (BIP integer encoder).
 *   2. For each body, lift its phase to the D-dim hypervector by
 *      rolling the deterministic channel basis (from `es_channel_basis`
 *      with seed = ES_BODY_BASIS_SEED_BASE + body_idx).
 *   3. Sum the rolled bases, normalise.
 *
 * Observer-bind and eclipse projection are pure HDC algebra (no SPICE,
 * no skyfield) — same code on both sides modulo language conventions.
 *
 * The Python BIP-and-lift path lives in
 * `_research/bip_hd_lift.py`; the parity smoke test pins the two
 * paths to within float-ULP. The original FPU matrix-expm path
 * (`EphemerisHDCInstrument.encode_state`) is kept as `backend=
 * "fpu-ref"` for backwards compat — it produces a different state
 * vector (different propagation algorithm) and is NOT C-twinned.
 */

/* SSOT seeds — mirror `_research/bip_hd_lift` constants. The Python
 * side uses these same integer values so the channel bases agree
 * byte-for-byte across both runtimes.
 */
#define ES_BODY_BASIS_SEED_BASE        ((uint64_t)2026)
#define ES_OBSERVER_COORD_BASIS_SEED   ((uint64_t)9999)
#define ES_SYZYGY_NODE_BASIS_SEED      ((uint64_t)777)

/* Coprime weights for the observer-bind roll. Same as
 * `ephemeris_reference_instrument.COPRIME_LAT/LON`.
 */
#define ES_COPRIME_LAT 67
#define ES_COPRIME_LON 7

/* Encode the system at delta_t and lift to a D-dim hypervector.
 *
 * Calls `es_encode_state` for the 38 × uint32 phase residues, then for
 * each body rolls its channel basis (seed = ES_BODY_BASIS_SEED_BASE +
 * body_idx) by `round((phi/2^32) * D) mod D`, divides by sqrt(D), and
 * sums into `out_state`. Final state is normalised to unit norm.
 *
 * `out_state`, `scratch_basis`, and `scratch_rolled` must each have
 * capacity for D `es_complex64_t` entries. `scratch_*` buffers are
 * caller-supplied to keep the C library JPL-Power-of-Ten Rule 3 clean
 * (no dynamic allocation after init); contents on entry are ignored
 * and on return are unspecified.
 *
 * Returns ES_OK on success; ES_ERR_NULL_OUTPUT if any required
 * pointer is NULL; propagates failure from `es_encode_state`.
 */
es_status_t es_encode_state_hd(double delta_t_days,
                               es_complex64_t *out_state,
                               es_complex64_t *scratch_basis,
                               es_complex64_t *scratch_rolled,
                               size_t D);

/* Bind a topocentric observer at (lat_deg, lon_deg) on body_idx into
 * the HD state.
 *
 *   lat_res = int((lat + 90)/180 * D) mod D
 *   lon_res = int((lon + 180)/360 * D) mod D
 *   coord_op = roll(channel_basis(ES_OBSERVER_COORD_BASIS_SEED, D),
 *                   (lat_res * ES_COPRIME_LAT + lon_res * ES_COPRIME_LON) mod D)
 *   observer_op = (body_basis / sqrt(D)) * coord_op
 *   out[k] = state[k] * observer_op[k] * sqrt(D)
 *
 * Pure HDC algebra. No SPICE, no skyfield.
 *
 * `out_state` may overlap with `state_in` (in-place is supported).
 * `scratch_body_basis`, `scratch_coord_basis`, and `scratch_coord_op`
 * are caller-supplied buffers of D `es_complex64_t` entries each (Rule 3).
 *
 * Returns ES_OK on success; ES_ERR_NULL_OUTPUT on NULL ptrs;
 * ES_ERR_INVALID_INDEX if body_idx >= ES_N_BODIES;
 * ES_ERR_NON_FINITE_INPUT for NaN/inf lat/lon.
 */
es_status_t es_bind_observer(const es_complex64_t *state_in,
                             size_t body_idx,
                             double lat_deg,
                             double lon_deg,
                             es_complex64_t *out_state,
                             es_complex64_t *scratch_body_basis,
                             es_complex64_t *scratch_coord_basis,
                             es_complex64_t *scratch_coord_op,
                             size_t D);

/* Eclipse probability via the syzygy operator.
 *
 *   sun_b   = channel_basis(ES_BODY_BASIS_SEED_BASE + sun_body_idx, D)
 *   moon_b  = channel_basis(ES_BODY_BASIS_SEED_BASE + moon_body_idx, D)
 *   node_b  = channel_basis(ES_SYZYGY_NODE_BASIS_SEED, D) / sqrt(D)
 *   s_op    = (sun_b + moon_b) / sqrt(D) + node_b
 *   s_op   /= |s_op|
 *   *out_prob = | <state, s_op> |   (sum-of-conj-product magnitude)
 *
 * Body-index resolution (which body is "sun", which is "moon") happens
 * at the call site — the function doesn't parse names. The Python
 * bridge resolves them via `es_body_index("sun")` / `("moon")`.
 *
 * `scratch_sun_b`, `scratch_moon_b`, `scratch_node_b`, and
 * `scratch_s_op` are caller-supplied buffers of D `es_complex64_t`
 * entries each (Rule 3).
 *
 * Returns ES_OK on success; usual error codes for null/oob/non-finite.
 */
es_status_t es_get_eclipse_probability(const es_complex64_t *state,
                                       size_t D,
                                       size_t sun_body_idx,
                                       size_t moon_body_idx,
                                       es_complex64_t *scratch_sun_b,
                                       es_complex64_t *scratch_moon_b,
                                       es_complex64_t *scratch_node_b,
                                       es_complex64_t *scratch_s_op,
                                       double *out_prob);

/* ------------------------------------------------------------------ *
 * Version
 * ------------------------------------------------------------------ */

/* Version: MUST match python/pyproject.toml's [project].version. The
 * manifest.json emitted by codegen reads from pyproject.toml as SSOT
 * (see codegen/emit_c_tables.py); this header is hand-written so the
 * two need to be bumped together at release time.
 */
#define ES_VERSION_MAJOR 0
#define ES_VERSION_MINOR 24
#define ES_VERSION_PATCH 4
#define ES_VERSION_STRING "0.24.4"

const char *es_version(void);

/* ABI version. Increment whenever the wire format of any exported
 * function changes (struct field added/removed, parameter type
 * changed, semantics altered). The Python ctypes shim verifies
 * this at load time and refuses to load a mismatched binary.
 *
 * v1: initial v0.3.1 release. es_encode_state, es_encode_at_jd,
 *     es_body_index, es_cos_lut, es_residue_to_radians, es_version.
 *     ES_N_BODIES = 26.
 *
 * v2: v0.4.1 — diagnosed-fiber runtime overlay.
 *     Added: es_patch_t struct, es_apply_patch, es_clear_patches,
 *     es_n_active_patches, es_get_patch_at. The encode-state path
 *     consults the patch registry AFTER the base loop and BEFORE
 *     the final cyclic-group reduction, mirroring the Python BIP
 *     encoder's overlay step. With no patches active the encode is
 *     byte-identical to v0.4.0 (and to the Python BIP encoder).
 *
 * v3: v0.6.0 — C/Python parity Tier 1.
 *     Added: es_breathing_modulation, es_syzygy_t struct, es_find_syzygies,
 *     ES_SYZYGY_KIND_* + ES_SYZYGY_KIND_FILTER_* constants. Encoder
 *     hot path is unchanged — these are net-new entry points. With
 *     no patches active the encode-state output is byte-identical
 *     to v2 (and to the Python BIP encoder).
 *
 * v4: v0.6.1 — C/Python parity Tier 2a foundation (channel bases).
 *     Added: es_complex64_t struct, es_channel_basis. Splitmix64
 *     PRNG plumbing (es_prng.h, internal). Encoder hot path is
 *     unchanged. Tier 2b (the actual HD encode + observer-bind +
 *     eclipse projection) bumps to ABI v5 in v0.7.0.
 *
 * v5: v0.7.0 — C/Python parity Tier 2b (HD pipeline).
 *     Added: es_encode_state_hd, es_bind_observer,
 *     es_get_eclipse_probability + ES_BODY_BASIS_SEED_BASE /
 *     ES_OBSERVER_COORD_BASIS_SEED / ES_SYZYGY_NODE_BASIS_SEED /
 *     ES_COPRIME_LAT / ES_COPRIME_LON constants. Encoder hot path
 *     unchanged. Parity smoke flips both Tier 2 entries from
 *     `tier2_skip` to `parity` -- every encoder-touching bridge
 *     method now has a paired C path.
 *
 * v6: v0.13.4 — JPL Power-of-Ten Rule 1 + Rule 3 fixes.
 *     The three HD-pipeline entries gain caller-supplied scratch
 *     buffer parameters so the C library no longer calls malloc/free
 *     after init (Rule 3) and no longer needs the goto-cleanup
 *     pattern (Rule 1). Encoder math is byte-identical to v5; only
 *     the wire format changed (extra pointer params).
 *
 *       es_encode_state_hd:        +scratch_basis, +scratch_rolled
 *       es_bind_observer:          +scratch_body_basis,
 *                                  +scratch_coord_basis,
 *                                  +scratch_coord_op
 *       es_get_eclipse_probability:+scratch_sun_b, +scratch_moon_b,
 *                                  +scratch_node_b, +scratch_s_op
 *
 *     Each scratch buffer must have capacity for D es_complex64_t
 *     entries; contents on entry ignored, on return unspecified.
 *     The Python ctypes shim allocates these once per call alongside
 *     the existing `out_state` buffer, so the user-facing bridge API
 *     is unchanged.
 */
#define ES_ABI_VERSION 8
int es_abi_version(void);

/* Compile-time body count, exposed as a function for the Python
 * loader so the ctypes shim can size buffers without parsing the
 * header.
 */
int es_n_bodies(void);

#ifdef __cplusplus
}
#endif

#endif /* EPHEMERIDES_SPECTRAL_H */
