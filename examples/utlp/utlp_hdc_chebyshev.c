/**
 * @file utlp_hdc_chebyshev.c
 * @brief Chebyshev Harmonic HDC Implementation
 *
 * The mathematical orrery brought to life.
 *
 * @see utlp_hdc_chebyshev.h for detailed documentation
 *
 * @copyright SPDX-License-Identifier: GPL-3.0-or-later
 */

#include "utlp_hdc_chebyshev.h"

/*============================================================================
 * MODULE STATE
 *==========================================================================*/

/** Chebyshev basis LUT - populated at boot */
int8_t utlp_cheb_basis_lut[UTLP_CHEB_NUM_HARMONICS][UTLP_CHEB_LUT_SAMPLES];

/** Initialization flag */
bool utlp_cheb_initialized = false;

/** Primes array for local use */
static const uint8_t s_primes[UTLP_CHORD_SIZE] = UTLP_PRIMES_INIT;

/*============================================================================
 * INITIALIZATION
 *==========================================================================*/

bool utlp_cheb_init(void)
{
    if (utlp_cheb_initialized) {
        return true;  /* Already initialized */
    }

    /*
     * Populate the basis LUT using the identity T_n(cos θ) = cos(nθ).
     *
     * For each harmonic n and sample k:
     *   θ_k = k * (2π/256)
     *   T_n(cos θ_k) = cos(n * θ_k)
     *
     * The cosine LUT is already precomputed, so this is just index arithmetic.
     */
    for (uint8_t n = 0; n < UTLP_CHEB_NUM_HARMONICS; n++) {
        for (uint16_t k = 0; k < UTLP_CHEB_LUT_SAMPLES; k++) {
            /*
             * cos(n * k * 2π/256) = cos_lut[(n * k) mod 256]
             *
             * The cosine LUT is in Q15 [-32767, +32767].
             * We convert to Q7 [-127, +127] for HDC bipolar representation.
             */
            uint8_t lut_idx = (uint8_t)((n * k) & 0xFF);
            int16_t cos_q15 = utlp_cheb_cos_lut[lut_idx];

            /* Convert Q15 to Q7 with rounding */
            int8_t basis_val = (int8_t)((cos_q15 + 128) >> 8);

            /* Clamp to valid range */
            if (basis_val > 127) basis_val = 127;
            if (basis_val < -127) basis_val = -127;

            utlp_cheb_basis_lut[n][k] = basis_val;
        }
    }

    utlp_cheb_initialized = true;
    return true;
}

/*============================================================================
 * DETAILED SIMILARITY
 *==========================================================================*/

void utlp_cheb_detailed_similarity(
    const uint8_t chord_a[UTLP_CHORD_SIZE],
    const uint8_t chord_b[UTLP_CHORD_SIZE],
    utlp_cheb_similarity_t *result,
    uint16_t dims)
{
    if (!result) return;

    /* Initialize result */
    memset(result, 0, sizeof(utlp_cheb_similarity_t));

    int32_t total_agreement = 0;
    int32_t harmonic_sums[UTLP_CHEB_NUM_HARMONICS] = {0};
    uint32_t texture_distance_sq = 0;

    for (uint16_t d = 0; d < dims; d++) {
        int16_t sum_a = 0;
        int16_t sum_b = 0;

        for (uint8_t h = 0; h < UTLP_CHEB_NUM_HARMONICS; h++) {
            uint8_t phase_offset = (uint8_t)((d * (h + 1)) & 0xFF);

            uint8_t lut_a = utlp_cheb_phase_to_lut_idx(chord_a[h], s_primes[h]);
            uint8_t lut_b = utlp_cheb_phase_to_lut_idx(chord_b[h], s_primes[h]);

            lut_a = (lut_a + phase_offset) & 0xFF;
            lut_b = (lut_b + phase_offset) & 0xFF;

            int16_t val_a = utlp_cheb_fast_eval(lut_a, h);
            int16_t val_b = utlp_cheb_fast_eval(lut_b, h);

            sum_a += val_a;
            sum_b += val_b;

            /* Track per-harmonic agreement */
            if ((val_a >= 0) == (val_b >= 0)) {
                harmonic_sums[h]++;
            } else {
                harmonic_sums[h]--;
            }

            /* Track texture distance */
            int16_t diff = val_a - val_b;
            texture_distance_sq += (uint32_t)(diff * diff);
        }

        /* Overall agreement */
        if ((sum_a >= 0) == (sum_b >= 0)) {
            total_agreement++;
        } else {
            total_agreement--;
        }
    }

    /* Compute overall similarity */
    int32_t scaled = ((total_agreement + (int32_t)dims) * 255) / (2 * (int32_t)dims);
    if (scaled < 0) scaled = 0;
    if (scaled > 255) scaled = 255;
    result->similarity = (uint8_t)scaled;

    /* Compute per-harmonic agreement (normalize to [-127, +127]) */
    for (uint8_t h = 0; h < UTLP_CHEB_NUM_HARMONICS; h++) {
        int32_t norm = (harmonic_sums[h] * 127) / (int32_t)dims;
        if (norm > 127) norm = 127;
        if (norm < -127) norm = -127;
        result->harmonic_agreement[h] = (int8_t)norm;
    }

    /* Texture distance (sqrt approximation) */
    /* Use integer sqrt: find x such that x*x <= texture_distance_sq */
    uint32_t x = 1;
    while (x * x < texture_distance_sq / (dims * UTLP_CHEB_NUM_HARMONICS)) {
        x++;
    }
    result->texture_distance = (uint16_t)x;

    /* Same epoch window check (similarity > 200 suggests same window) */
    result->same_epoch_window = (result->similarity > 200);
}

/*============================================================================
 * SPECTRAL AGE COMPUTATION
 *==========================================================================*/

utlp_spectral_age_t utlp_cheb_spectral_age(
    const uint8_t chord[UTLP_CHORD_SIZE],
    uint64_t tick_us)
{
    utlp_spectral_age_t age;
    memset(&age, 0, sizeof(age));

    /* Get compound gear positions */
    age.slow_phase = utlp_cheb_slow_gear(tick_us);
    age.medium_phase = utlp_cheb_medium_gear(tick_us);

    /*
     * Compute harmonic energy from chord.
     *
     * The energy in each harmonic indicates how much that frequency
     * contributes to the current chord configuration.
     *
     * Low harmonics cycle slowly → stable over time → coarse age
     * High harmonics cycle fast → change rapidly → fine age
     */
    int32_t total_energy = 0;
    int32_t weighted_sum = 0;

    for (uint8_t h = 0; h < UTLP_CHEB_NUM_HARMONICS; h++) {
        int32_t energy = 0;

        /* Sum energy across all primes for this harmonic */
        for (uint8_t p = 0; p < UTLP_CHORD_SIZE; p++) {
            uint8_t lut_idx = utlp_cheb_phase_to_lut_idx(chord[p], s_primes[p]);
            int16_t val = utlp_cheb_fast_eval(lut_idx, h);
            energy += (val >= 0) ? val : -val;  /* Absolute value */
        }

        age.harmonic_energy[h] = (int16_t)(energy / UTLP_CHORD_SIZE);
        total_energy += age.harmonic_energy[h];

        /*
         * Weight higher harmonics more heavily for fine age resolution.
         * This creates a monotonic age value that increases with time.
         *
         * The weighting uses harmonic index as proxy for frequency:
         * - h=0 (DC) contributes least (stable)
         * - h=7 (highest harmonic) contributes most (changes rapidly)
         */
        weighted_sum += age.harmonic_energy[h] * (h + 1);
    }

    /*
     * Combine slow gear position with harmonic energy for monotonic age.
     *
     * The slow gear provides the "coarse" component (14.5s period).
     * The harmonic energy provides the "fine" component.
     *
     * Scale so that slow_phase dominates over harmonic energy.
     */
    int32_t slow_contribution = (int32_t)(age.slow_phase >> 8);  /* Scale down */
    int32_t harmonic_contribution = weighted_sum >> 4;  /* Much smaller scale */

    age.monotonic_age = slow_contribution + harmonic_contribution;

    /* Confidence based on energy distribution */
    /* High total energy with balanced distribution = high confidence */
    if (total_energy > 0) {
        age.confidence = (uint8_t)((total_energy * 255) / (32767 * UTLP_CHEB_NUM_HARMONICS));
    } else {
        age.confidence = 0;
    }

    return age;
}

/*============================================================================
 * LAYER 0: ORBITAL SKELETON
 *==========================================================================*/

void utlp_cheb_get_skeleton(
    const uint8_t chord[UTLP_CHORD_SIZE],
    int8_t *skeleton,
    uint16_t dims)
{
    if (!skeleton) return;

    /*
     * The skeleton is the smooth Chebyshev harmonic representation.
     *
     * For each dimension d:
     *   1. Sum contributions from all 8 harmonics
     *   2. Apply dimension-dependent rotation for variation
     *   3. Binarize to [-1, +1] for HDC compatibility
     */
    for (uint16_t d = 0; d < dims; d++) {
        int16_t sum = 0;

        for (uint8_t h = 0; h < UTLP_CHEB_NUM_HARMONICS; h++) {
            /* Dimension-dependent rotation */
            uint8_t phase_offset = (uint8_t)((d * (h + 1)) & 0xFF);

            /* Get LUT index for this chord dimension */
            uint8_t lut_idx = utlp_cheb_phase_to_lut_idx(chord[h], s_primes[h]);
            lut_idx = (lut_idx + phase_offset) & 0xFF;

            /* Add harmonic contribution */
            sum += utlp_cheb_fast_eval(lut_idx, h);
        }

        /* Binarize: positive sum → +1, negative → -1, zero → sign of d */
        if (sum > 0) {
            skeleton[d] = 1;
        } else if (sum < 0) {
            skeleton[d] = -1;
        } else {
            skeleton[d] = (d & 1) ? 1 : -1;  /* Tie-breaker */
        }
    }
}

/*============================================================================
 * LAYER 1: TEMPORAL BINDING
 *==========================================================================*/

void utlp_cheb_bind_epoch(
    const int8_t *skeleton,
    uint32_t slow_phase,
    int8_t *epoch_vector,
    uint16_t dims)
{
    if (!skeleton || !epoch_vector) return;

    /*
     * Temporal binding uses fractional power encoding.
     *
     * In FHRR terms, this is B^t where:
     *   - B is the base vector (the skeleton)
     *   - t is the temporal phase (slow gear position)
     *
     * For practical implementation, we use a simplified rotation:
     * Each harmonic component is rotated by (slow_phase * harmonic_freq).
     *
     * The rotation amount varies by dimension to preserve the
     * hypervector structure while encoding temporal information.
     */
    uint32_t normalized_phase = (slow_phase * 256) / UTLP_SLOW_GEAR_PERIOD_US;

    for (uint16_t d = 0; d < dims; d++) {
        /*
         * Compute rotation for this dimension.
         * Different dimensions rotate at different "frequencies"
         * based on their position, creating a spectral spread.
         */
        uint32_t rotation = (normalized_phase * (d + 1)) & 0xFF;

        /*
         * Apply rotation via XOR with a pseudo-rotation pattern.
         * For bipolar {-1, +1} vectors, rotation is approximated
         * by conditional sign flip based on rotation angle.
         *
         * If rotation > 128, flip the sign (half-period rotation).
         */
        if (rotation > 128) {
            epoch_vector[d] = -skeleton[d];
        } else {
            epoch_vector[d] = skeleton[d];
        }
    }
}

/*============================================================================
 * LAYER 2: PERTURBATION BINDING
 *==========================================================================*/

void utlp_cheb_bind_perturbation(
    const int8_t *epoch_vector,
    const int8_t *perturbation,
    int8_t *perturbed_vector,
    uint16_t dims)
{
    if (!epoch_vector || !perturbation || !perturbed_vector) return;

    /*
     * Perturbation binding uses element-wise multiplication.
     *
     * In HDC bipolar representation: {-1, +1} × {-1, +1}
     *   (+1) × (+1) = +1
     *   (+1) × (-1) = -1
     *   (-1) × (+1) = -1
     *   (-1) × (-1) = +1
     *
     * This is equivalent to XOR on the sign bits.
     *
     * The Chebyshev product identity T_m · T_n = ½[T_{m+n} + T_{|m-n|}]
     * governs the frequency mixing that occurs, pushing spectral
     * energy to higher harmonics with each binding operation.
     */
    for (uint16_t d = 0; d < dims; d++) {
        /* Bipolar multiplication: same signs → +1, different → -1 */
        if ((epoch_vector[d] > 0) == (perturbation[d] > 0)) {
            perturbed_vector[d] = 1;
        } else {
            perturbed_vector[d] = -1;
        }
    }
}

/*============================================================================
 * SELF-DESCRIBING VERIFICATION
 *==========================================================================*/

void utlp_cheb_decompose(
    const int8_t *vector,
    int16_t coefficients[UTLP_CHEB_NUM_HARMONICS],
    uint16_t dims)
{
    if (!vector || !coefficients) return;

    /*
     * DCT-II decomposition: project vector onto each Chebyshev basis.
     *
     * For each harmonic h:
     *   coefficient[h] = Σ_d vector[d] · T_h(d)
     *
     * This extracts the "strength" of each harmonic in the vector,
     * revealing the underlying orbital structure.
     */
    for (uint8_t h = 0; h < UTLP_CHEB_NUM_HARMONICS; h++) {
        int32_t projection = 0;

        for (uint16_t d = 0; d < dims; d++) {
            /*
             * Compute T_h at normalized position d/dims.
             * Map d ∈ [0, dims) to θ ∈ [0, 2π).
             */
            uint8_t theta_256 = (uint8_t)((d * 256) / dims);
            int16_t basis_val = utlp_cheb_fast_eval(theta_256, h);

            /* Project: vector[d] × basis_val */
            projection += (int32_t)vector[d] * basis_val;
        }

        /* Normalize by dimensionality */
        coefficients[h] = (int16_t)(projection / (int32_t)dims);
    }
}

bool utlp_cheb_verify_consistency(
    const int8_t *vector,
    uint16_t dims)
{
    if (!vector) return false;

    /*
     * Verify that the vector has valid Chebyshev structure.
     *
     * A properly encoded vector should have:
     * 1. Non-zero energy in at least some harmonics
     * 2. Reasonable energy distribution (not all in one harmonic)
     * 3. Reconstructible from its DCT coefficients
     *
     * Byzantine detection: forged vectors will typically fail these checks.
     */
    int16_t coefficients[UTLP_CHEB_NUM_HARMONICS];
    utlp_cheb_decompose(vector, coefficients, dims);

    /* Check 1: Total energy must be non-zero */
    int32_t total_energy = 0;
    for (uint8_t h = 0; h < UTLP_CHEB_NUM_HARMONICS; h++) {
        int16_t val = coefficients[h];
        total_energy += (val >= 0) ? val : -val;
    }

    if (total_energy < 100) {  /* Threshold for minimum energy */
        return false;  /* Too little structure - likely corrupted */
    }

    /* Check 2: Energy distribution - no single harmonic should dominate completely */
    for (uint8_t h = 0; h < UTLP_CHEB_NUM_HARMONICS; h++) {
        int16_t val = coefficients[h];
        int32_t abs_val = (val >= 0) ? val : -val;

        /* If one harmonic has >90% of total energy, suspicious */
        if (abs_val > (total_energy * 9) / 10) {
            return false;
        }
    }

    /* Check 3: Reconstruction error should be small */
    /* (Simplified check: just verify bipolar structure) */
    int32_t bipolar_count = 0;
    for (uint16_t d = 0; d < dims; d++) {
        if (vector[d] == 1 || vector[d] == -1) {
            bipolar_count++;
        }
    }

    /* At least 90% of values should be exactly ±1 */
    if (bipolar_count < (dims * 9) / 10) {
        return false;
    }

    return true;
}
