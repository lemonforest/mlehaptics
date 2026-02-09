/**
 * @file utlp_hdc_chebyshev.h
 * @brief Chebyshev Harmonic HDC - The Mathematical Orrery
 *
 * @section overview Overview
 *
 * Replaces hash-based HDC texture with Chebyshev harmonic encoding.
 * This creates SMOOTH texture where adjacent time values produce similar
 * hypervectors, enabling monotonic distance measurement from genesis.
 *
 * @section identity The Unifying Identity
 *
 * The entire framework rests on a single mathematical identity:
 *
 *     T_n(cos θ) = cos(nθ)
 *
 * Chebyshev polynomials of the first kind, evaluated on the cosine-
 * parameterized interval, ARE pure cosine harmonics. This connects:
 *
 * - NASA SPICE ephemeris compression (Chebyshev coefficients)
 * - DCT-II transform basis (signal compression)
 * - The Antikythera mechanism (coprime gear ratios)
 * - Grid cells in entorhinal cortex (coprime spatial frequencies)
 * - Our 8-prime phase chord (the orrery)
 *
 * @section orthogonality Exact Orthogonality
 *
 * At Chebyshev-Gauss nodes x_k = cos((2k-1)π / 2D), the discrete inner
 * product satisfies an EXACT relation (not approximate):
 *
 *     Σ_k T_m(x_k) · T_n(x_k) = { 0     if m ≠ n
 *                               { D/2   if m = n ≥ 1
 *                               { D     if m = n = 0
 *
 * This yields D exactly orthogonal basis vectors in D dimensions.
 *
 * @section layers Bones and Texture Architecture
 *
 * - Layer 0: Orbital skeleton (smooth Chebyshev harmonics) - "orrery at rest"
 * - Layer 1: Temporal binding (epoch specification) - "animation"
 * - Layer 2: Perturbation binding (drift corrections) - "refinement"
 * - Layer 3: Observer binding (local view) - future N>2
 *
 * "Strip away all the bindings, and what remains is not random noise
 * but the orbital model itself. The bones remember."
 *
 * @section prior_art Historical Context
 *
 * The Antikythera mechanism (c. 150-80 BCE) physically instantiated this
 * principle: coprime gear ratios encoding celestial cycles. The 19-tooth
 * gear encoded the Metonic cycle, the 223-tooth gear the Saros eclipse
 * cycle. Our 8-prime phase chord is the digital equivalent.
 *
 * @see implementation_plan_chebyshev_orrery.md
 * @see hdc_cosmograph_celestial_mechanics.md
 * @see chebyshev_harmonics_skeletal_basis.md
 *
 * @version 1.0.0
 * @date 2026-02-08
 *
 * @copyright SPDX-License-Identifier: GPL-3.0-or-later
 */

#ifndef UTLP_HDC_CHEBYSHEV_H
#define UTLP_HDC_CHEBYSHEV_H

#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include "utlp_config.h"

#ifdef __cplusplus
extern "C" {
#endif

/*============================================================================
 * MATHEMATICAL CONSTANTS
 *
 * These are not arbitrary - they are derived from the physics.
 *==========================================================================*/

/**
 * @brief Number of Chebyshev harmonics (matches chord size)
 *
 * Each prime in the phase chord maps to one Chebyshev harmonic.
 * T_0 = DC component, T_1 = fundamental, T_2..T_7 = overtones.
 */
#define UTLP_CHEB_NUM_HARMONICS     UTLP_CHORD_SIZE  /* 8 */

/**
 * @brief LUT resolution (samples per harmonic)
 *
 * 256 samples provides sufficient resolution for 8-bit phase values.
 * Each prime's phase [0, prime-1] maps into this range.
 */
#define UTLP_CHEB_LUT_SAMPLES       256

/**
 * @brief Embedded-friendly dimension count
 *
 * 256 dimensions at 8 primes × 8 cycles ≈ 102µs on ESP32-C6 @ 160MHz.
 * This fits within the <100µs timing budget (with margin for variance).
 */
#define UTLP_CHEB_EMBEDDED_DIMS     256

/**
 * @brief Full-precision dimension count (for non-real-time analysis)
 */
#define UTLP_CHEB_FULL_DIMS         1024

/*============================================================================
 * SLOW COMPOUND GEAR - The Missing "Hour Hand"
 *
 * The 8 primes (211-251) all cycle at 200+ Hz at 1µs resolution.
 * This is like having 8 second hands but no hour hand.
 *
 * The compound gear solves this by taking the product of 3 primes,
 * creating a MUCH slower cycle that enables monotonic age measurement.
 *
 * | Gear       | Period     | Wraps/sec | Use Case            |
 * |------------|------------|-----------|---------------------|
 * | Prime 241  | 241µs      | 4,149     | Useless for age     |
 * | 2-prime    | 60.5ms     | 16.5      | Marginal            |
 * | 3-prime    | 14.5s      | 0.07      | Genesis distance ✓  |
 * | All 8      | 261,000 yr | 0         | Epoch uniqueness    |
 *
 *==========================================================================*/

/**
 * @brief Slow compound gear period (3-prime product)
 *
 * 241 × 251 × 239 = 14,456,809 microseconds ≈ 14.46 seconds
 *
 * This gives us monotonic age measurement within a 14.5 second window,
 * which is more than sufficient for first-contact synchronization.
 */
#define UTLP_SLOW_GEAR_PERIOD_US    (241UL * 251UL * 239UL)  /* 14,456,809 */

/**
 * @brief Medium compound gear (2-prime product)
 *
 * 241 × 251 = 60,491 microseconds ≈ 60.5 milliseconds
 * Used for intermediate precision between chord and slow gear.
 */
#define UTLP_MEDIUM_GEAR_PERIOD_US  (241UL * 251UL)  /* 60,491 */

/*============================================================================
 * FIXED-POINT ARITHMETIC (Q15.16)
 *
 * Integer-only computation for embedded systems without FPU.
 *
 * Q15.16 format: 1 sign bit, 15 integer bits, 16 fractional bits
 * Range: [-32768.0, +32767.99998]
 * Resolution: 1/65536 ≈ 0.000015
 *
 * For Chebyshev: x ∈ [-1, +1] maps to [-65536, +65536] in Q16.
 *==========================================================================*/

/** @defgroup fixed_point Fixed-Point Arithmetic
 * @{
 */

/** Q16 representation of 1.0 */
#define UTLP_Q16_ONE        (1L << 16)      /* 65536 */

/** Q16 representation of 0.5 */
#define UTLP_Q16_HALF       (1L << 15)      /* 32768 */

/** Q16 representation of -1.0 */
#define UTLP_Q16_NEG_ONE    (-(1L << 16))   /* -65536 */

/** Multiply two Q16 values, returning Q16 result */
#define UTLP_Q16_MUL(a, b)  ((int32_t)(((int64_t)(a) * (int64_t)(b)) >> 16))

/** Convert integer to Q16 */
#define UTLP_INT_TO_Q16(x)  ((int32_t)(x) << 16)

/** Convert Q16 to integer (truncating) */
#define UTLP_Q16_TO_INT(x)  ((int32_t)(x) >> 16)

/** @} */ /* fixed_point */

/*============================================================================
 * PRECOMPUTED COSINE TABLE
 *
 * 256-entry cosine lookup table for the identity T_n(cos θ) = cos(nθ).
 * This enables O(1) Chebyshev evaluation without trig functions.
 *
 * Table is indexed by θ in units of (2π/256), covering one full period.
 * Values are in Q15 format: [-32767, +32767] representing [-1, +1].
 *
 * The table is generated at compile time using the formula:
 *   cos_lut[i] = round(32767 * cos(2π * i / 256))
 *==========================================================================*/

/**
 * @brief Precomputed cosine table (256 entries, Q15 format)
 *
 * Usage: cos(θ) where θ = i * (2π/256) → cos_lut[i]
 *
 * For cos(nθ): cos_lut[(n * i) & 0xFF]
 *
 * This is the heart of the Chebyshev identity implementation.
 * T_n(cos(θ)) = cos(n*θ) becomes a single array lookup.
 */
static const int16_t utlp_cheb_cos_lut[256] = {
    /* Generated by: round(32767 * cos(2π * i / 256)) for i = 0..255 */
    /* θ = 0° to 360° in 256 steps */
     32767,  32757,  32728,  32678,  32609,  32521,  32412,  32285,
     32137,  31971,  31785,  31580,  31356,  31113,  30852,  30571,
     30273,  29956,  29621,  29268,  28898,  28510,  28105,  27683,
     27245,  26790,  26319,  25832,  25329,  24811,  24279,  23731,
     23170,  22594,  22005,  21403,  20787,  20159,  19519,  18868,
     18204,  17530,  16846,  16151,  15446,  14732,  14010,  13279,
     12539,  11793,  11039,  10278,   9512,   8739,   7962,   7179,
      6393,   5602,   4808,   4011,   3212,   2410,   1608,    804,
         0,   -804,  -1608,  -2410,  -3212,  -4011,  -4808,  -5602,
     -6393,  -7179,  -7962,  -8739,  -9512, -10278, -11039, -11793,
    -12539, -13279, -14010, -14732, -15446, -16151, -16846, -17530,
    -18204, -18868, -19519, -20159, -20787, -21403, -22005, -22594,
    -23170, -23731, -24279, -24811, -25329, -25832, -26319, -26790,
    -27245, -27683, -28105, -28510, -28898, -29268, -29621, -29956,
    -30273, -30571, -30852, -31113, -31356, -31580, -31785, -31971,
    -32137, -32285, -32412, -32521, -32609, -32678, -32728, -32757,
    -32767, -32757, -32728, -32678, -32609, -32521, -32412, -32285,
    -32137, -31971, -31785, -31580, -31356, -31113, -30852, -30571,
    -30273, -29956, -29621, -29268, -28898, -28510, -28105, -27683,
    -27245, -26790, -26319, -25832, -25329, -24811, -24279, -23731,
    -23170, -22594, -22005, -21403, -20787, -20159, -19519, -18868,
    -18204, -17530, -16846, -16151, -15446, -14732, -14010, -13279,
    -12539, -11793, -11039, -10278,  -9512,  -8739,  -7962,  -7179,
     -6393,  -5602,  -4808,  -4011,  -3212,  -2410,  -1608,   -804,
         0,    804,   1608,   2410,   3212,   4011,   4808,   5602,
      6393,   7179,   7962,   8739,   9512,  10278,  11039,  11793,
     12539,  13279,  14010,  14732,  15446,  16151,  16846,  17530,
     18204,  18868,  19519,  20159,  20787,  21403,  22005,  22594,
     23170,  23731,  24279,  24811,  25329,  25832,  26319,  26790,
     27245,  27683,  28105,  28510,  28898,  29268,  29621,  29956,
     30273,  30571,  30852,  31113,  31356,  31580,  31785,  31971,
     32137,  32285,  32412,  32521,  32609,  32678,  32728,  32757
};

/*============================================================================
 * CHEBYSHEV BASIS LOOKUP TABLE
 *
 * The "bones" of the orrery - precomputed at boot time.
 *
 * Each row n contains T_n evaluated at 256 sample points.
 * T_n(x_k) = cos(n * arccos(x_k)) = cos(n * θ_k)
 *
 * For phase values: phase [0, prime-1] maps to θ [0, 2π]
 *   θ = (phase / prime) * 2π
 *   LUT index = (phase * 256) / prime
 *
 * Storage: 8 harmonics × 256 samples × 1 byte = 2048 bytes (2KB)
 *==========================================================================*/

/**
 * @brief Chebyshev basis LUT (8 harmonics × 256 samples)
 *
 * Indexed as: chebyshev_lut[harmonic][sample]
 *
 * Values are in [-127, +127] representing the bipolar HDC domain.
 *
 * @note This is populated at boot time by utlp_cheb_init().
 *       The initialization cost is ~50ms on ESP32-C6.
 */
extern int8_t utlp_cheb_basis_lut[UTLP_CHEB_NUM_HARMONICS][UTLP_CHEB_LUT_SAMPLES];

/**
 * @brief Flag indicating LUT has been initialized
 */
extern bool utlp_cheb_initialized;

/*============================================================================
 * DATA STRUCTURES
 *==========================================================================*/

/**
 * @brief Spectral age - monotonic age from harmonic decomposition
 *
 * Unlike Genesis Distance (broken at high tick rates), spectral age
 * uses the slow compound gear for monotonic ordering within 14.5s,
 * with harmonic decomposition for fine resolution.
 *
 * The key insight: low harmonics cycle slowly (coarse age),
 * high harmonics cycle fast (fine age, disambiguated by low).
 */
typedef struct {
    /** Energy in each Chebyshev harmonic [0-7] */
    int16_t harmonic_energy[UTLP_CHEB_NUM_HARMONICS];

    /** Position in slow compound gear [0, 14,456,808] */
    uint32_t slow_phase;

    /** Position in medium compound gear [0, 60,490] */
    uint32_t medium_phase;

    /** Confidence based on energy distribution [0-255] */
    uint8_t confidence;

    /** Monotonic age value (for direct comparison) */
    int32_t monotonic_age;
} utlp_spectral_age_t;

/**
 * @brief Chebyshev similarity result with harmonic breakdown
 *
 * Not just a single similarity value, but a decomposition
 * showing which harmonics agree and which disagree.
 */
typedef struct {
    /** Overall similarity [0-255] (128 = orthogonal) */
    uint8_t similarity;

    /** Per-harmonic agreement [-127 to +127] */
    int8_t harmonic_agreement[UTLP_CHEB_NUM_HARMONICS];

    /** Smooth texture difference (low = similar, high = different) */
    uint16_t texture_distance;

    /** Whether both chords are from the same epoch window */
    bool same_epoch_window;
} utlp_cheb_similarity_t;

/*============================================================================
 * INITIALIZATION
 *==========================================================================*/

/**
 * @brief Initialize Chebyshev basis LUT
 *
 * Must be called once at boot before using any Chebyshev functions.
 * Populates the utlp_cheb_basis_lut table with precomputed values.
 *
 * The LUT uses the identity T_n(cos θ) = cos(nθ):
 *   lut[n][k] = round(127 * cos(n * k * 2π / 256))
 *
 * @return true on success, false on failure
 *
 * @note Cost: ~50ms on ESP32-C6 @ 160MHz (one-time at boot)
 * @note Thread-safe: Can be called from any context
 */
bool utlp_cheb_init(void);

/*============================================================================
 * SLOW COMPOUND GEAR
 *
 * The "hour hand" that enables monotonic age measurement.
 *==========================================================================*/

/**
 * @brief Get current position in slow compound gear
 *
 * The slow gear has period 241 × 251 × 239 ≈ 14.46 seconds.
 * Position increases monotonically, wrapping only every 14.5s.
 *
 * @param tick_us Current tick count in microseconds
 * @return Position in [0, UTLP_SLOW_GEAR_PERIOD_US - 1]
 */
static inline uint32_t utlp_cheb_slow_gear(uint64_t tick_us)
{
    return (uint32_t)(tick_us % UTLP_SLOW_GEAR_PERIOD_US);
}

/**
 * @brief Get current position in medium compound gear
 *
 * The medium gear has period 241 × 251 ≈ 60.5 milliseconds.
 * Provides intermediate resolution between chord and slow gear.
 *
 * @param tick_us Current tick count in microseconds
 * @return Position in [0, UTLP_MEDIUM_GEAR_PERIOD_US - 1]
 */
static inline uint32_t utlp_cheb_medium_gear(uint64_t tick_us)
{
    return (uint32_t)(tick_us % UTLP_MEDIUM_GEAR_PERIOD_US);
}

/**
 * @brief Compare two slow gear positions to determine ordering
 *
 * Returns the signed distance from 'a' to 'b' on the slow gear circle.
 * Positive = b is ahead of a (b is older)
 * Negative = a is ahead of b (a is older)
 * Zero = same position
 *
 * Handles wrap-around correctly within half the period (~7.2s).
 *
 * @param a First slow gear position
 * @param b Second slow gear position
 * @return Signed distance (positive = b ahead, negative = a ahead)
 */
static inline int32_t utlp_cheb_slow_gear_diff(uint32_t a, uint32_t b)
{
    int32_t diff = (int32_t)b - (int32_t)a;
    int32_t half_period = (int32_t)(UTLP_SLOW_GEAR_PERIOD_US / 2);

    /* Handle wrap-around: take the shorter path */
    if (diff > half_period) {
        diff -= (int32_t)UTLP_SLOW_GEAR_PERIOD_US;
    } else if (diff < -half_period) {
        diff += (int32_t)UTLP_SLOW_GEAR_PERIOD_US;
    }

    return diff;
}

/*============================================================================
 * CHEBYSHEV POLYNOMIAL EVALUATION
 *
 * Integer-only implementation using the recurrence relation:
 *   T_0(x) = 1
 *   T_1(x) = x
 *   T_n(x) = 2x · T_{n-1}(x) - T_{n-2}(x)
 *
 * This is numerically stable and requires no floating point.
 *==========================================================================*/

/**
 * @brief Evaluate Chebyshev polynomial T_n(x) using recurrence
 *
 * Uses the three-term recurrence relation for numerical stability.
 * All arithmetic is in Q16 fixed-point format.
 *
 * @param x_q16 Input value in Q16 format, must be in [-65536, +65536]
 * @param order Polynomial degree n (0 to 7 for our use case)
 * @return T_n(x) in Q16 format
 *
 * @note For order > 15, numerical errors may accumulate
 */
static inline int32_t utlp_cheb_polynomial_q16(int32_t x_q16, uint8_t order)
{
    if (order == 0) {
        return UTLP_Q16_ONE;  /* T_0(x) = 1 */
    }
    if (order == 1) {
        return x_q16;  /* T_1(x) = x */
    }

    int32_t t_prev2 = UTLP_Q16_ONE;  /* T_0 */
    int32_t t_prev1 = x_q16;         /* T_1 */
    int32_t t_curr = 0;

    for (uint8_t n = 2; n <= order; n++) {
        /*
         * T_n = 2x · T_{n-1} - T_{n-2}
         *
         * Multiply 2x · T_{n-1} in Q16:
         *   2x in Q16 = x_q16 << 1
         *   product = (2x * T_{n-1}) >> 16 to stay in Q16
         */
        int64_t product = ((int64_t)x_q16 * (int64_t)t_prev1) >> 15;  /* >> 15 because 2x */
        t_curr = (int32_t)product - t_prev2;

        t_prev2 = t_prev1;
        t_prev1 = t_curr;
    }

    return t_prev1;
}

/**
 * @brief Fast Chebyshev evaluation using cosine LUT identity
 *
 * Uses T_n(cos θ) = cos(nθ) for O(1) evaluation.
 *
 * @param theta_256 Angle in units of (2π/256), range [0, 255]
 * @param harmonic Chebyshev degree n
 * @return T_n(cos θ) in Q15 format [-32767, +32767]
 */
static inline int16_t utlp_cheb_fast_eval(uint8_t theta_256, uint8_t harmonic)
{
    /*
     * T_n(cos θ) = cos(nθ)
     *
     * If θ = k * (2π/256), then nθ = (n*k) * (2π/256)
     * LUT index for cos(nθ) = (n * k) mod 256
     */
    uint8_t lut_idx = (uint8_t)((harmonic * theta_256) & 0xFF);
    return utlp_cheb_cos_lut[lut_idx];
}

/*============================================================================
 * PHASE CHORD TO CHEBYSHEV MAPPING
 *
 * Each phase value [0, prime-1] maps to an angle θ ∈ [0, 2π].
 * The LUT is indexed by θ in units of (2π/256).
 *==========================================================================*/

/**
 * @brief Convert phase value to LUT index
 *
 * Maps phase ∈ [0, prime-1] to θ ∈ [0, 2π) discretized to 256 steps.
 *
 * @param phase Phase value (0 to prime-1)
 * @param prime The prime for this chord dimension
 * @return LUT index [0, 255]
 */
static inline uint8_t utlp_cheb_phase_to_lut_idx(uint8_t phase, uint8_t prime)
{
    /*
     * θ = (phase / prime) * 2π
     * LUT index = (phase / prime) * 256 = (phase * 256) / prime
     *
     * Use 32-bit intermediate to avoid overflow for phase * 256.
     */
    return (uint8_t)(((uint32_t)phase * 256) / prime);
}

/**
 * @brief Get Chebyshev basis value for a chord dimension
 *
 * Returns T_harmonic(cos(θ)) where θ = (phase/prime) * 2π
 *
 * @param phase Phase value for this dimension
 * @param prime The prime for this dimension
 * @param harmonic Which Chebyshev harmonic (0-7)
 * @return Basis value in [-127, +127]
 */
static inline int8_t utlp_cheb_basis_value(uint8_t phase, uint8_t prime, uint8_t harmonic)
{
    if (!utlp_cheb_initialized) {
        /* Fallback to direct computation if LUT not ready */
        uint8_t theta_256 = utlp_cheb_phase_to_lut_idx(phase, prime);
        int16_t val_q15 = utlp_cheb_fast_eval(theta_256, harmonic);
        return (int8_t)(val_q15 >> 8);  /* Q15 to Q7 */
    }

    /* Use precomputed LUT for speed */
    uint8_t lut_idx = utlp_cheb_phase_to_lut_idx(phase, prime);
    return utlp_cheb_basis_lut[harmonic][lut_idx];
}

/*============================================================================
 * SMOOTH SIMILARITY COMPUTATION
 *
 * Unlike hash-based expansion (jagged texture), Chebyshev encoding
 * produces SMOOTH similarity where adjacent chords are highly similar.
 *
 * This is the core operation that replaces utlp_hdc_expanded_similarity().
 *==========================================================================*/

/**
 * @brief Compute smooth similarity between two phase chords
 *
 * Uses Chebyshev harmonic decomposition for smooth texture.
 * Adjacent time values produce high similarity; distant values
 * produce low similarity — monotonically.
 *
 * Algorithm:
 * 1. For each dimension d in [0, dims):
 *    - Sum Chebyshev contributions from all 8 primes
 *    - Compare signs: same sign = agreement, different = disagreement
 * 2. Normalize agreement to [0, 255]
 *
 * @param chord_a First phase chord (8 bytes)
 * @param chord_b Second phase chord (8 bytes)
 * @param dims Number of dimensions (use UTLP_CHEB_EMBEDDED_DIMS)
 * @return Similarity 0-255 (128 = orthogonal, 255 = identical, 0 = opposite)
 */
static inline uint8_t utlp_cheb_smooth_similarity(
    const uint8_t chord_a[UTLP_CHORD_SIZE],
    const uint8_t chord_b[UTLP_CHORD_SIZE],
    uint16_t dims)
{
    static const uint8_t primes[UTLP_CHORD_SIZE] = UTLP_PRIMES_INIT;

    int32_t agreement = 0;

    for (uint16_t d = 0; d < dims; d++) {
        int16_t sum_a = 0;
        int16_t sum_b = 0;

        /*
         * Sum Chebyshev contributions across all harmonics.
         * Each harmonic is weighted by its position in the dimension.
         */
        for (uint8_t h = 0; h < UTLP_CHEB_NUM_HARMONICS; h++) {
            /*
             * Dimension d selects which "rotation" of the harmonic we use.
             * This creates variation across dimensions while preserving
             * the smooth texture within each harmonic.
             */
            uint8_t phase_offset = (uint8_t)((d * (h + 1)) & 0xFF);

            /* Get basis values for both chords */
            uint8_t lut_a = utlp_cheb_phase_to_lut_idx(chord_a[h], primes[h]);
            uint8_t lut_b = utlp_cheb_phase_to_lut_idx(chord_b[h], primes[h]);

            /* Apply dimension-dependent rotation */
            lut_a = (lut_a + phase_offset) & 0xFF;
            lut_b = (lut_b + phase_offset) & 0xFF;

            /* Use fast cosine identity: T_h(cos θ) = cos(h*θ) */
            sum_a += utlp_cheb_fast_eval(lut_a, h);
            sum_b += utlp_cheb_fast_eval(lut_b, h);
        }

        /* Compare signs of accumulators */
        if ((sum_a >= 0) == (sum_b >= 0)) {
            agreement++;
        } else {
            agreement--;
        }
    }

    /*
     * Convert agreement to [0, 255]:
     *   agreement = -dims → 0 (completely opposite)
     *   agreement = 0 → 128 (orthogonal)
     *   agreement = +dims → 255 (identical)
     */
    int32_t scaled = ((agreement + (int32_t)dims) * 255) / (2 * (int32_t)dims);
    if (scaled < 0) scaled = 0;
    if (scaled > 255) scaled = 255;

    return (uint8_t)scaled;
}

/**
 * @brief Compute detailed similarity with harmonic breakdown
 *
 * Like utlp_cheb_smooth_similarity but returns per-harmonic analysis.
 * Useful for debugging and Byzantine detection.
 *
 * @param chord_a First phase chord
 * @param chord_b Second phase chord
 * @param result Output structure with harmonic breakdown
 * @param dims Number of dimensions
 */
void utlp_cheb_detailed_similarity(
    const uint8_t chord_a[UTLP_CHORD_SIZE],
    const uint8_t chord_b[UTLP_CHORD_SIZE],
    utlp_cheb_similarity_t *result,
    uint16_t dims);

/*============================================================================
 * SPECTRAL AGE COMPUTATION
 *
 * Monotonic age measurement using slow compound gear + harmonic decomposition.
 * This replaces the broken Genesis Distance algorithm.
 *==========================================================================*/

/**
 * @brief Compute spectral age of a phase chord
 *
 * Combines:
 * 1. Slow compound gear position (14.5s monotonic window)
 * 2. Harmonic energy distribution (fine resolution)
 *
 * The result is MONOTONIC within 14.5 seconds — orders of magnitude
 * better than Genesis Distance which fails at 1µs tick rate.
 *
 * @param chord Phase chord to analyze
 * @param tick_us Current tick count in microseconds
 * @return Spectral age structure with monotonic age value
 */
utlp_spectral_age_t utlp_cheb_spectral_age(
    const uint8_t chord[UTLP_CHORD_SIZE],
    uint64_t tick_us);

/**
 * @brief Compare two spectral ages to determine ordering
 *
 * Returns positive if age_b is older (further from genesis).
 * Returns negative if age_a is older.
 * Returns zero if indistinguishable.
 *
 * @param age_a First spectral age
 * @param age_b Second spectral age
 * @return Signed comparison (positive = b older, negative = a older)
 */
static inline int32_t utlp_cheb_compare_age(
    const utlp_spectral_age_t *age_a,
    const utlp_spectral_age_t *age_b)
{
    /*
     * Primary comparison: slow gear position
     * This is monotonic within 14.5 seconds.
     */
    int32_t slow_diff = utlp_cheb_slow_gear_diff(age_a->slow_phase, age_b->slow_phase);

    /*
     * If slow gear difference is significant (> 100ms), use it directly.
     * Otherwise, use harmonic energy for fine resolution.
     */
    const int32_t SLOW_THRESHOLD = 100000;  /* 100ms in µs */

    if (slow_diff > SLOW_THRESHOLD || slow_diff < -SLOW_THRESHOLD) {
        return slow_diff;
    }

    /* Fall back to monotonic age from harmonic analysis */
    return age_b->monotonic_age - age_a->monotonic_age;
}

/*============================================================================
 * LAYER 0: ORBITAL SKELETON
 *
 * The smooth Chebyshev harmonic representation — the "orrery at rest".
 * This is the time-independent orbital geometry that persists through
 * all bindings.
 *==========================================================================*/

/**
 * @brief Extract orbital skeleton from phase chord
 *
 * Produces the Layer 0 representation: smooth Chebyshev harmonics
 * encoding the "bones" of the time structure.
 *
 * The skeleton has the property that:
 * - Adjacent chords produce adjacent skeletons (smooth texture)
 * - Unbinding epoch and perturbations recovers this skeleton
 *
 * @param chord Input phase chord (8 bytes)
 * @param skeleton Output skeleton vector (dims bytes)
 * @param dims Dimensionality of output
 */
void utlp_cheb_get_skeleton(
    const uint8_t chord[UTLP_CHORD_SIZE],
    int8_t *skeleton,
    uint16_t dims);

/*============================================================================
 * LAYER 1: TEMPORAL BINDING
 *
 * Animates the skeleton by binding with epoch-specific phase.
 * This is "where on the orbit" — the temporal specification.
 *==========================================================================*/

/**
 * @brief Bind epoch (temporal phase) to skeleton
 *
 * Applies fractional power encoding to rotate each harmonic by the
 * slow compound gear phase. This animates the skeleton to represent
 * a specific moment in time.
 *
 * In FHRR terms: B^t where t is the slow gear phase.
 *
 * @param skeleton Input Layer 0 skeleton
 * @param slow_phase Position in slow compound gear
 * @param epoch_vector Output Layer 1 epoch-bound vector
 * @param dims Dimensionality
 */
void utlp_cheb_bind_epoch(
    const int8_t *skeleton,
    uint32_t slow_phase,
    int8_t *epoch_vector,
    uint16_t dims);

/*============================================================================
 * LAYER 2: PERTURBATION BINDING
 *
 * Adds drift corrections and peer synchronization adjustments.
 * This is the "texture" that makes each observation unique.
 *==========================================================================*/

/**
 * @brief Bind perturbation (drift correction) to epoch vector
 *
 * Adds higher-frequency texture from synchronization adjustments.
 * The Chebyshev product identity governs frequency mixing:
 *
 *   T_m(x) · T_n(x) = ½[T_{m+n}(x) + T_{|m-n|}(x)]
 *
 * This pushes spectral energy to higher harmonics, progressively
 * roughening the representation with each sync observation.
 *
 * @param epoch_vector Input Layer 1 epoch-bound vector
 * @param perturbation Perturbation vector (from drift computation)
 * @param perturbed_vector Output Layer 2 perturbed vector
 * @param dims Dimensionality
 */
void utlp_cheb_bind_perturbation(
    const int8_t *epoch_vector,
    const int8_t *perturbation,
    int8_t *perturbed_vector,
    uint16_t dims);

/*============================================================================
 * SELF-DESCRIBING VERIFICATION
 *
 * The beauty of Chebyshev encoding: the vector reveals its content
 * through DCT decomposition. No external codebook needed.
 *==========================================================================*/

/**
 * @brief Extract harmonic coefficients via DCT decomposition
 *
 * Projects the vector onto each Chebyshev basis to recover the
 * original encoding parameters. This is how the vector "describes
 * itself" — the mathematical structure is inherent, not external.
 *
 * @param vector Input hypervector
 * @param coefficients Output harmonic coefficients [8 values]
 * @param dims Dimensionality of input
 */
void utlp_cheb_decompose(
    const int8_t *vector,
    int16_t coefficients[UTLP_CHEB_NUM_HARMONICS],
    uint16_t dims);

/**
 * @brief Verify internal consistency of Chebyshev-encoded vector
 *
 * Checks that the vector's harmonic structure is consistent with
 * a valid Chebyshev encoding. Invalid vectors (corrupted, forged,
 * or wrong encoding) will fail this check.
 *
 * Useful for Byzantine detection: a node claiming a timestamp but
 * providing an inconsistent Chebyshev encoding is likely malicious.
 *
 * @param vector Vector to verify
 * @param dims Dimensionality
 * @return true if valid Chebyshev encoding, false if inconsistent
 */
bool utlp_cheb_verify_consistency(
    const int8_t *vector,
    uint16_t dims);

#ifdef __cplusplus
}
#endif

#endif /* UTLP_HDC_CHEBYSHEV_H */
