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

    /* ---- the chunk loop ---- */
    for (uint64_t s = 0; s < num_steps; ++s) {
        /* 1. Diagonal evolution: cyclic addition in Z_{2^64}. The final
         *    reduction to Z_{2^32} happens once, at the bottom of this
         *    function. uint64 wraparound here is the modular reduction
         *    by design.
         */
        for (size_t i = 0; i < ES_N_BODIES; ++i) {
            curr_phases[i] += (uint64_t)trunk_step[i];
        }

        /* 2. Phase 9 breathing: state-dependent coupling perturbation.
         *    For each (a, b, n_a, m_b, weight_rpd) entry, compute
         *
         *       cos_q14 = cos_lut(n_a * phi_a - m_b * phi_b)
         *       breath  = (NUM * base_nudge * cos_q14) / (DEN * AMP)
         *       nudge   = base_nudge + breath
         *       phi_a, phi_b += nudge
         *
         *    All integer ops; LUT lookup is O(1).
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

    /* ---- sub-chunk remainder (single fractional-day step) ---- */
    if (remainder_days > 0.0) {
        const double remainder_signed = (double)sign * remainder_days;
        for (size_t i = 0; i < ES_N_BODIES; ++i) {
            /* round() is libm; called O(N) times outside the hot loop.
             * Embedded targets without libm can replace with their own
             * nearest-integer rounding; the result fits in int64 by
             * the bounds check above.
             */
            const int64_t rem_step = (int64_t)round(
                (double)es_omega_diag[i] * remainder_signed);
            curr_phases[i] += (uint64_t)rem_step;
        }
    }

    /* ---- final reduction to Z_{2^32} ---- */
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
