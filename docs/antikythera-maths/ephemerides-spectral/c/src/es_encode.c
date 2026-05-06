/*
 * es_encode.c — Phase 9 BIP encode_state, integer ALU.
 *
 * Direct port of EphemerisBIPInstrument._encode_state_impl from the
 * Python `ephemerides-spectral` package. See
 * ../include/ephemerides_spectral.h for the API contract and the
 * Q-format / overflow / breathing-coupling design notes.
 *
 * Hot-path arithmetic: int64 (omega multiplies), uint64 (phase
 * accumulator), uint32 (final reduction). NO floats inside the loop.
 * The single float input — delta_t_days — is consumed once at the top
 * of the function for the chunk-count math and the sub-day remainder.
 */

#include <math.h>      /* isfinite, fabs, round — all called <= 4 times,
                          ALL outside the chunk loop                     */
#include <string.h>    /* strncmp                                         */

#include "ephemerides_spectral.h"

/* ------------------------------------------------------------------ */
/*  Internal helpers                                                  */
/* ------------------------------------------------------------------ */

/* Saturated-bounds check. Returns true if delta_t_days is finite AND
 * inside the int64 envelope; false otherwise.
 */
static bool es_delta_in_range(double delta_t_days) {
    if (!isfinite(delta_t_days)) {
        return false;
    }
    if (fabs(delta_t_days) > ES_DELTA_DAYS_LIMIT) {
        return false;
    }
    return true;
}

/* Floor division with int64 operands.
 *
 * C's `/` truncates toward zero; Python's `//` floors toward negative
 * infinity. The Phase 9 breathing path divides a possibly-negative
 * numerator by a positive denominator, and every chunk's result feeds
 * the cyclic accumulator, so the rounding mode propagates: byte-exact
 * parity with the Python reference encoder requires floor division.
 *
 * Returns floor(a / b). Branch only fires on a/b sign mismatch with
 * non-zero remainder, so the truncating fast path covers > 50% of
 * chunks (cos_q14 >= 0 half the time on average).
 */
static inline int64_t es_floor_div(int64_t a, int64_t b) {
    int64_t q = a / b;
    int64_t r = a % b;
    if ((r != 0) && ((r < 0) != (b < 0))) {
        q -= 1;
    }
    return q;
}

/* Banker's rounding (round-half-to-even) for double -> int64.
 *
 * C's `round()` is round-half-away-from-zero; numpy's `np.round`
 * is banker's (half-to-even). The sub-day remainder step in
 * encode_state hits exact half-integer results often enough for
 * this difference to break byte-exact parity by 1 ULP on specific
 * JDs (verified at ±1 yr in the v0.3.1 native parity tests).
 *
 * Implementation: add 0.5 with truncation toward zero only when
 * the half-tie would land on an even integer; otherwise round up
 * the absolute value as `round()` would. Keeps integer arithmetic
 * once the rounding decision is made — no floating-point comparison
 * after the fact.
 */
/* External linkage so es_patches.c can call this for the overlay
 * delta-rounding (must match the BIP encoder's banker's rounding
 * for byte-exact patch parity with the Python overlay).
 */
int64_t es_banker_round(double x) {
    /* Truncation toward zero gives us the integer below |x|. */
    double sign = (x >= 0.0) ? 1.0 : -1.0;
    double abs_x = sign * x;
    int64_t truncated = (int64_t)abs_x;
    double frac = abs_x - (double)truncated;

    /* Strict less-than / greater-than first; only the exact half
     * needs banker's-rounding tie-break.
     */
    int64_t rounded;
    if (frac < 0.5) {
        rounded = truncated;
    } else if (frac > 0.5) {
        rounded = truncated + 1;
    } else {
        /* Exact half: round to the nearest even integer. */
        rounded = (truncated % 2 == 0) ? truncated : truncated + 1;
    }
    return (sign > 0.0) ? rounded : -rounded;
}

/* Forward declaration of the overlay hook implemented in es_patches.c.
 * Internal to the library; not exposed in the public header. The
 * encoder calls this after the base loop to sum any active
 * diagnosed-fiber patch contributions into the phase accumulator
 * before the final cyclic-group reduction.
 */
void es_apply_overlay_to_phases(double delta_t_days,
                                uint64_t curr_phases[ES_N_BODIES]);

/* Body-name lookup: O(N) but N=26. Returns ES_N_BODIES on miss. */
size_t es_body_index(const char *name) {
    if (name == NULL) {
        return ES_N_BODIES;
    }
    for (size_t i = 0; i < ES_N_BODIES; ++i) {
        /* Names are NUL-terminated within name[16]. */
        if (strncmp(es_bodies[i].name, name, sizeof es_bodies[i].name) == 0) {
            return i;
        }
    }
    return ES_N_BODIES;
}

/* ------------------------------------------------------------------ */
/*  Cosine LUT runtime accessor                                       */
/* ------------------------------------------------------------------ */

int32_t es_cos_lut(uint32_t phase_residue, uint32_t n_lobes) {
    /* fold n_lobes * phase into Z_{2^32} (free uint32 overflow) */
    uint32_t folded = phase_residue * n_lobes;
    /* top ES_COSINE_LUT_BITS bits index the table */
    uint32_t idx = folded >> (ES_K_BITS - ES_COSINE_LUT_BITS);
    return es_cosine_lut[idx];
}

double es_residue_to_radians(uint32_t residue) {
    /* Convert phase residue to radians. Only float touchpoint outside
     * the encode hot path; provided for callers that need continuous
     * angles. Uses 2*pi expressed to ~1e-15 precision.
     */
    static const double TWO_PI = 6.283185307179586476925286766559;
    return ((double)residue / 4294967296.0) * TWO_PI;
}

/* ------------------------------------------------------------------ */
/*  encode_state                                                      */
/* ------------------------------------------------------------------ */

/* Apply one chunk's worth of phase evolution to `curr_phases`:
 *   1. Diagonal evolution (cyclic addition by trunk_step in Z_{2^64}).
 *   2. Phase 9 breathing-couplings perturbation.
 * `step` is the signed chunk size in days (used inside the breathing
 * inner term `cp->weight_rpd * step`); `trunk_step` is its O(N)
 * pre-multiply.
 *
 * All integer ops; uint64 wraparound is the cyclic-group reduction by
 * design. The final reduction to Z_{2^32} happens once, at the end of
 * `es_encode_state`.
 */
static void apply_one_chunk(uint64_t curr_phases[ES_N_BODIES],
                            const int64_t trunk_step[ES_N_BODIES],
                            int64_t step)
{
    /* Diagonal evolution. */
    for (size_t i = 0; i < ES_N_BODIES; ++i) {
        curr_phases[i] += (uint64_t)trunk_step[i];
    }

    /* Phase 9 breathing-couplings perturbation. For each coupling
     * (a, b, n_a, m_b, weight_rpd):
     *   cos_q14 = cos_lut(n_a * phi_a - m_b * phi_b)
     *   breath  = (NUM * base_nudge * cos_q14) / (DEN * AMP)
     *   nudge   = base_nudge + breath
     *   phi_a, phi_b += nudge
     */
    for (size_t k = 0; k < es_n_couplings; ++k) {
        const es_coupling_t *cp = &es_couplings[k];
        const uint32_t phi_a = (uint32_t)(curr_phases[cp->idx_a] & ES_MODULO_MASK);
        const uint32_t phi_b = (uint32_t)(curr_phases[cp->idx_b] & ES_MODULO_MASK);
        /* res_phase = (n_a * phi_a) - (m_b * phi_b), mod 2^32.
         * uint32 arithmetic gives free overflow.
         */
        const uint32_t res_phase = (uint32_t)(cp->n_a) * phi_a
                                 - (uint32_t)(cp->m_b) * phi_b;
        const int32_t  cos_q14   = es_cos_lut(res_phase, 1u);
        const int64_t  base_nudge = cp->weight_rpd * step;
        const int64_t  breath = es_floor_div(
            (int64_t)ES_BREATHING_NUM * base_nudge * (int64_t)cos_q14,
            (int64_t)ES_BREATHING_DEN * (int64_t)ES_COSINE_LUT_AMP);
        const int64_t  nudge = base_nudge + breath;

        curr_phases[cp->idx_a] += (uint64_t)nudge;
        curr_phases[cp->idx_b] += (uint64_t)nudge;
    }
}

/* Apply the leftover sub-chunk remainder (single fractional-day step).
 * Banker's rounding (half-to-even) matches numpy's np.round; called
 * O(N) times outside the hot loop. Necessary for byte-exact parity
 * with the Python BIP encoder when the multiplication produces an
 * exact half-integer (verified at the v0.3.1 +/- 1 yr parity tests).
 */
static void apply_subchunk_remainder(uint64_t curr_phases[ES_N_BODIES],
                                     double remainder_signed)
{
    for (size_t i = 0; i < ES_N_BODIES; ++i) {
        const int64_t rem_step = es_banker_round(
            (double)es_omega_diag[i] * remainder_signed);
        curr_phases[i] += (uint64_t)rem_step;
    }
}

es_status_t es_encode_state(double delta_t_days,
                            uint32_t phases_out[ES_N_BODIES])
{
    if (phases_out == NULL) {
        return ES_ERR_NULL_OUTPUT;
    }
    if (!isfinite(delta_t_days)) {
        return ES_ERR_NON_FINITE_INPUT;
    }
    if (!es_delta_in_range(delta_t_days)) {
        return ES_ERR_DELTA_OUT_OF_RANGE;
    }

    /* Chunk decomposition. The chunk loop only ever multiplies by an
     * integer step (+/- ES_CHUNK_DAYS); the leftover sub-chunk
     * remainder is handled once at the end.
     */
    const int sign = (delta_t_days >= 0.0) ? 1 : -1;
    const double abs_days = (delta_t_days >= 0.0) ? delta_t_days : -delta_t_days;
    const int64_t step = (int64_t)(sign * (int)ES_CHUNK_DAYS);
    const uint64_t num_steps = (uint64_t)(abs_days / (double)ES_CHUNK_DAYS);
    const double remainder_days = abs_days - (double)num_steps * (double)ES_CHUNK_DAYS;

    /* Phase accumulator (uint64; final reduction = & ES_MODULO_MASK). */
    uint64_t curr_phases[ES_N_BODIES];
    for (size_t i = 0; i < ES_N_BODIES; ++i) {
        curr_phases[i] = (uint64_t)es_initial_phases[i];
    }

    /* Pre-multiply: trunk_step[i] = omega_diag[i] * step (residues/chunk). */
    int64_t trunk_step[ES_N_BODIES];
    for (size_t i = 0; i < ES_N_BODIES; ++i) {
        trunk_step[i] = es_omega_diag[i] * step;
    }

    for (uint64_t s = 0; s < num_steps; ++s) {
        apply_one_chunk(curr_phases, trunk_step, step);
    }

    if (remainder_days > 0.0) {
        apply_subchunk_remainder(curr_phases, (double)sign * remainder_days);
    }

    /* v0.4.1 diagnosed-fiber runtime overlay. With no patches active
     * this is a single early-return; with patches active the per-body
     * deltas are summed onto the accumulator before final reduction.
     */
    es_apply_overlay_to_phases(delta_t_days, curr_phases);

    /* Final reduction to Z_{2^32}. */
    for (size_t i = 0; i < ES_N_BODIES; ++i) {
        phases_out[i] = (uint32_t)(curr_phases[i] & ES_MODULO_MASK);
    }
    return ES_OK;
}

es_status_t es_encode_at_jd(double jd_tdb,
                            uint32_t phases_out[ES_N_BODIES])
{
    if (!isfinite(jd_tdb)) {
        return ES_ERR_NON_FINITE_INPUT;
    }
    return es_encode_state(jd_tdb - ES_REFERENCE_JD, phases_out);
}

const char *es_version(void) {
    return ES_VERSION_STRING;
}

int es_abi_version(void) {
    return ES_ABI_VERSION;
}

int es_n_bodies(void) {
    return (int)ES_N_BODIES;
}
