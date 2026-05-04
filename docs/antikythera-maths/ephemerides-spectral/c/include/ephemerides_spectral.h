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

/* Number of bodies in the Sol Star System Laplacian (sun + 9 planets +
 * 12 major moons + 4 main-belt asteroids). Pinned by the codegen-
 * emitted body table in es_bodies.c.
 */
#define ES_N_BODIES        26u

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
 * Version
 * ------------------------------------------------------------------ */

#define ES_VERSION_MAJOR 0
#define ES_VERSION_MINOR 1
#define ES_VERSION_PATCH 0
#define ES_VERSION_STRING "0.1.0"

const char *es_version(void);

#ifdef __cplusplus
}
#endif

#endif /* EPHEMERIDES_SPECTRAL_H */
