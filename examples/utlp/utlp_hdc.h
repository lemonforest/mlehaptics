/**
 * @file utlp_hdc.h
 * @brief UTLP Hyperdimensional Computing Primitives
 *
 * HDC-native time synchronization for UTLP. Replaces scalar offset comparison
 * with vector-based agreement, trajectory tracking, and elastic convergence.
 *
 * CORE PRINCIPLES:
 * 1. Time is a SHAPE (8D phase chord), not a scalar
 * 2. Agreement is a VECTOR (8 signed dimensions), not a scalar offset
 * 3. Sync is ELASTIC (nudge toward consensus), not hard adoption
 * 4. Authority comes from OBSERVATION COUNT, not claimed depth
 *
 * KEY INSIGHT: "Two clocks are synced when they evolve in PARALLEL,
 * not when their readings match."
 *
 * @see design_philosophy_anticipatory.md
 * @see UTLP_Technical_Supplement_S3.md (Vector Time)
 */

#ifndef UTLP_HDC_H
#define UTLP_HDC_H

#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include "utlp_config.h"

#ifdef __cplusplus
extern "C" {
#endif

/*============================================================================
 * CONFIGURATION CONSTANTS
 *==========================================================================*/

/** Trajectory history depth (observations) */
#define UTLP_HDC_TRAJECTORY_DEPTH       8

/** Minimum observations before trusting trajectory */
#define UTLP_HDC_MIN_OBSERVATIONS       3

/** Agreement threshold for "parallel trajectories" (out of 8) */
#define UTLP_HDC_PARALLEL_THRESHOLD     7

/** Agreement threshold for "converging" (out of 8) */
#define UTLP_HDC_CONVERGING_THRESHOLD   4

/** Roll-in nudge rate (quanta per 10ms tick) */
#define UTLP_HDC_ROLLIN_RATE            1

/** Roll-in timeout (ticks at 100Hz = 10ms each) */
#define UTLP_HDC_ROLLIN_TIMEOUT_TICKS   500  /* 5 seconds */

/** EMA alpha values (scaled by 256 for integer math) */
#define UTLP_HDC_ALPHA_FAST_X256        64   /* 25% - responds in ~4 obs */
#define UTLP_HDC_ALPHA_MEDIUM_X256      8    /* 3.1% - responds in ~32 obs */
#define UTLP_HDC_ALPHA_SLOW_X256        1    /* 0.4% - responds in ~256 obs */

/*============================================================================
 * 10,000-DIMENSION HYPERVECTOR EXPANSION
 *
 * TRUE HDC: The 8-byte phase chord is a COMPRESSED representation.
 * Each device expands it to a 10,000-dimension hypervector for similarity.
 *
 * GENERATIVE COMPRESSION:
 * - Wire format: 8 bytes (chord)
 * - Expanded: 10,000 bits (1,250 bytes)
 * - Ratio: 156:1 compression!
 *
 * Both devices generate IDENTICAL base vectors from the same seed (Swarm DNA),
 * so they independently expand any chord to the same 10,000D hypervector.
 *
 * STREAMING COMPUTATION:
 * For embedded, we DON'T store 10,000 bits. We compute similarity
 * on-the-fly using a deterministic PRNG to regenerate base vectors.
 *==========================================================================*/

/** Full hypervector dimensions (per spec) */
#define UTLP_HDC_FULL_DIMS          10000

/** Embedded-friendly dimension count (faster, still effective) */
#define UTLP_HDC_EMBEDDED_DIMS      512

/** Default seed for base vector generation (derive from Swarm DNA in production) */
#define UTLP_HDC_DEFAULT_SEED       0x55AA55AA

/**
 * @brief Fast 32-bit xorshift PRNG for streaming base vector generation
 *
 * Deterministic: same seed → same sequence on all devices.
 * Much faster than hardware RNG, suitable for real-time expansion.
 */
static inline uint32_t utlp_hdc_xorshift32(uint32_t *state)
{
    uint32_t x = *state;
    x ^= x << 13;
    x ^= x >> 17;
    x ^= x << 5;
    *state = x;
    return x;
}

/**
 * @brief Compute 10K-expanded similarity between two chords (streaming)
 *
 * THE KEY HDC OPERATION: Expand both chords to 10,000-D hypervectors
 * and compute their cosine similarity, WITHOUT storing full vectors.
 *
 * Algorithm:
 * 1. For each dimension d in [0, dims):
 *    - Generate base vector bits for all 8 primes using PRNG
 *    - Rotate by respective phase values
 *    - Sum to get accumulator_a and accumulator_b
 *    - Compare signs: same sign = +1, different = -1
 * 2. Return normalized similarity [-1.0, +1.0] as integer [0, 255]
 *
 * @param chord_a First phase chord (8 bytes)
 * @param chord_b Second phase chord (8 bytes)
 * @param seed Shared seed for base vector generation (Swarm DNA)
 * @param dims Number of dimensions (use UTLP_HDC_EMBEDDED_DIMS for speed)
 * @return Similarity 0-255 (128 = orthogonal, 255 = identical, 0 = opposite)
 */
static inline uint8_t utlp_hdc_expanded_similarity(
    const utlp_phase_chord_t chord_a,
    const utlp_phase_chord_t chord_b,
    uint32_t seed,
    uint16_t dims)
{
    static const uint8_t primes[UTLP_CHORD_SIZE] = UTLP_PRIMES_INIT;

    int32_t agreement = 0;  /* Sum of +1 (agree) or -1 (disagree) per dimension */

    /*
     * For each dimension, we need to:
     * 1. Generate 8 random bits (one per prime's base vector)
     * 2. Rotate each by the chord's phase value
     * 3. Sum to get accumulators for chord_a and chord_b
     * 4. Compare signs
     *
     * Optimization: Process 32 dimensions at a time using 32-bit words.
     */
    uint32_t rng_state = seed;

    for (uint16_t d = 0; d < dims; d++) {
        int8_t acc_a = 0;
        int8_t acc_b = 0;

        /* Generate base vector bits for this dimension */
        if ((d & 31) == 0) {
            /* Refresh random bits every 32 dimensions */
            rng_state = utlp_hdc_xorshift32(&rng_state);
        }

        for (uint8_t p = 0; p < UTLP_CHORD_SIZE; p++) {
            /* Get deterministic "random" bit for this (dimension, prime) */
            /* Use a hash of (seed, dimension, prime) for better distribution */
            uint32_t hash = seed ^ (d * 31337) ^ (p * 65537);
            hash = utlp_hdc_xorshift32(&hash);
            int8_t base_bit = (hash & (1 << p)) ? +1 : -1;

            /*
             * "Rotate" by phase value:
             * In true HDC, we'd rotate a vector. Here we simulate by
             * combining the base bit with a phase-dependent modifier.
             *
             * The key property: same phase = same modifier = same result.
             * Different phases = different modifiers = decorrelated results.
             */
            uint8_t phase_a = chord_a[p];
            uint8_t phase_b = chord_b[p];

            /* Phase affects which "version" of the base vector we see */
            uint32_t mod_a = seed ^ (d * 7919) ^ (p * 104729) ^ (phase_a * 1000003);
            uint32_t mod_b = seed ^ (d * 7919) ^ (p * 104729) ^ (phase_b * 1000003);

            int8_t bit_a = ((utlp_hdc_xorshift32(&mod_a) & 1) ^ (base_bit > 0)) ? +1 : -1;
            int8_t bit_b = ((utlp_hdc_xorshift32(&mod_b) & 1) ^ (base_bit > 0)) ? +1 : -1;

            acc_a += bit_a;
            acc_b += bit_b;
        }

        /* Compare signs of accumulators */
        int8_t sign_a = (acc_a >= 0) ? +1 : -1;
        int8_t sign_b = (acc_b >= 0) ? +1 : -1;

        agreement += (sign_a == sign_b) ? +1 : -1;
    }

    /*
     * Convert agreement to 0-255 range:
     * - agreement = -dims → 0 (completely opposite)
     * - agreement = 0 → 128 (orthogonal)
     * - agreement = +dims → 255 (identical)
     */
    int32_t scaled = ((agreement + (int32_t)dims) * 255) / (2 * (int32_t)dims);
    if (scaled < 0) scaled = 0;
    if (scaled > 255) scaled = 255;

    return (uint8_t)scaled;
}

/**
 * @brief Fast 8D chord similarity (original, for comparison)
 *
 * This is the "compressed" similarity - works directly on 8-byte chords
 * without expansion. Less accurate but much faster.
 *
 * Use for: Quick filtering before expensive 10K expansion.
 */
static inline uint8_t utlp_hdc_chord_similarity_fast(
    const utlp_phase_chord_t chord_a,
    const utlp_phase_chord_t chord_b)
{
    static const uint8_t primes[UTLP_CHORD_SIZE] = UTLP_PRIMES_INIT;
    uint8_t matches = 0;

    for (uint8_t i = 0; i < UTLP_CHORD_SIZE; i++) {
        int16_t diff = (int16_t)chord_a[i] - (int16_t)chord_b[i];
        if (diff < 0) diff = -diff;
        if (diff > primes[i] / 2) diff = primes[i] - diff;

        /* 10% tolerance */
        if (diff <= primes[i] / 10) {
            matches++;
        }
    }

    /* Scale 0-8 to 0-255: matches * 32 (clamp at 255) */
    return (matches >= 8) ? 255 : (matches * 32);
}

/*============================================================================
 * AGREEMENT VECTOR
 *
 * Replaces scalar offset with 8-dimensional signed agreement.
 * Each dimension tells us: "In this prime's ring, who is ahead?"
 *
 * When all 8 dimensions agree on direction → high confidence
 * When dimensions disagree → low confidence (noise, partition, or spoof)
 *==========================================================================*/

/**
 * @brief Agreement vector - replaces scalar offset
 *
 * Instead of "offset = 347us", we have 8 signed offsets that should agree.
 * The PATTERN of agreement carries information that a scalar discards.
 */
typedef struct {
    /** Per-dimension signed offset: [-127, +127] */
    int8_t dimension[UTLP_CHORD_SIZE];

    /** Confidence: how many dimensions point same direction (0-8) */
    uint8_t confidence;

    /** Quality: consistency across dimensions (0-255, higher = more consistent) */
    uint8_t quality;

    /** Dominant direction: +1 = we're ahead, -1 = peer ahead, 0 = tied */
    int8_t direction;

    /** Reserved for alignment */
    uint8_t _reserved;
} agreement_vector_t;

/**
 * @brief Compute agreement vector between two phase chords
 *
 * This is the HDC replacement for scalar offset calculation.
 * Returns rich information about the relationship between two time states.
 *
 * @param our_chord Our current phase chord
 * @param peer_chord Peer's phase chord (from beacon)
 * @return Agreement vector with per-dimension analysis
 */
static inline agreement_vector_t utlp_hdc_compute_agreement(
    const utlp_phase_chord_t our_chord,
    const utlp_phase_chord_t peer_chord)
{
    agreement_vector_t result = {0};
    int positive_count = 0;
    int negative_count = 0;
    int32_t total_magnitude = 0;

    static const uint8_t primes[UTLP_CHORD_SIZE] = UTLP_PRIMES_INIT;

    for (uint8_t i = 0; i < UTLP_CHORD_SIZE; i++) {
        int16_t raw_diff = (int16_t)our_chord[i] - (int16_t)peer_chord[i];
        uint8_t prime = primes[i];

        /* Circular distance (wrap around the ring) */
        if (raw_diff > (int16_t)(prime / 2)) {
            raw_diff -= prime;
        } else if (raw_diff < -(int16_t)(prime / 2)) {
            raw_diff += prime;
        }

        /* Clamp to int8 range */
        if (raw_diff > 127) raw_diff = 127;
        if (raw_diff < -127) raw_diff = -127;

        result.dimension[i] = (int8_t)raw_diff;

        /* Count direction consensus */
        if (raw_diff > 0) positive_count++;
        else if (raw_diff < 0) negative_count++;

        /* Accumulate magnitude for quality calc */
        total_magnitude += (raw_diff >= 0) ? raw_diff : -raw_diff;
    }

    /* Confidence = how many dimensions point same direction */
    result.confidence = (positive_count > negative_count)
                       ? (uint8_t)positive_count
                       : (uint8_t)negative_count;

    /* Direction = which way is the majority pointing */
    if (positive_count > negative_count) {
        result.direction = 1;   /* We're ahead */
    } else if (negative_count > positive_count) {
        result.direction = -1;  /* Peer is ahead */
    } else {
        result.direction = 0;   /* Tied */
    }

    /* Quality = inverse of variance (all same magnitude = high quality) */
    /* Simple approximation: 255 - (max_dev from mean) */
    int32_t mean_mag = total_magnitude / UTLP_CHORD_SIZE;
    int32_t max_deviation = 0;
    for (uint8_t i = 0; i < UTLP_CHORD_SIZE; i++) {
        int32_t mag = (result.dimension[i] >= 0) ? result.dimension[i] : -result.dimension[i];
        int32_t dev = (mag > mean_mag) ? (mag - mean_mag) : (mean_mag - mag);
        if (dev > max_deviation) max_deviation = dev;
    }
    result.quality = (max_deviation < 255) ? (uint8_t)(255 - max_deviation) : 0;

    return result;
}

/*============================================================================
 * HOLOGRAPHIC TRAJECTORY MEMORY
 *
 * TRUE HDC: Instead of storing raw chords (which limits us to N observations),
 * we BUNDLE chord-time pairs into a holographic memory that can represent
 * an unlimited observation window in fixed memory.
 *
 * KEY HDC OPERATIONS:
 * - BIND (XOR): chord ⊗ time_offset_chord → creates association
 * - BUNDLE (ADD): sum of bound pairs → holographic superposition
 * - PROBE: similarity(memory, probe ⊗ hypothesis) → find best offset
 *
 * ANTICIPATORY PRINCIPLE:
 * "The memory doesn't store what happened - it encodes a MODEL that
 * PREDICTS what offset would make observations align."
 *
 * CAPACITY: Holographic memory reliably holds 10-20 items in 8D space.
 * We use multi-timescale EMA like latency_holo_t to handle more.
 *==========================================================================*/

/**
 * @brief Holographic trajectory memory (96 bytes)
 *
 * Multi-timescale holographic encoding of (chord, time_offset) pairs.
 * Instead of storing 8 raw chords, we bundle them holographically,
 * enabling probing for ANY offset hypothesis.
 *
 * The memory answers: "If I try offset H, how well do my observations align?"
 */
typedef struct {
    /* === Holographic accumulators (64 bytes) ===
     * Each stores BUNDLED (chord ⊗ offset) pairs at different timescales.
     * Fast responds to recent observations, slow to long-term patterns.
     */
    int16_t fast_acc[UTLP_CHORD_SIZE];      /**< Fast: ~2s response, captures jitter */
    int16_t medium_acc[UTLP_CHORD_SIZE];    /**< Medium: ~30s response, captures drift */
    int16_t slow_acc[UTLP_CHORD_SIZE];      /**< Slow: ~5min response, captures stability */
    int16_t bundled[UTLP_CHORD_SIZE];       /**< Blended holographic memory */

    /* === Reference state (16 bytes) ===
     * Tracks our "origin" so we know what offsets mean.
     */
    uint64_t origin_us;                     /**< When we started observing (local time) */
    uint64_t last_observation_us;           /**< Most recent observation timestamp */

    /* === Statistics (12 bytes) === */
    uint32_t observation_count;             /**< Total observations bundled */
    int32_t  estimated_offset_us;           /**< Current best offset estimate */

    /* === Quality metrics (8 bytes) === */
    uint8_t  confidence;                    /**< 0-255: how certain is our estimate? */
    uint8_t  stability;                     /**< 0-255: how stable is the offset? */
    uint8_t  parallelism;                   /**< 0-8: velocity agreement with peer */
    uint8_t  window_coverage;               /**< How much time span we've observed */
    int8_t   velocity[UTLP_CHORD_SIZE / 2]; /**< Estimated drift rate (4 dims) */
} trajectory_holo_t;

/**
 * @brief Legacy trajectory for backward compatibility
 *
 * DEPRECATED: Use trajectory_holo_t for new code.
 * Kept for gradual migration and trajectory_parallelism() function.
 */
typedef struct {
    /** Ring buffer of observed chords */
    utlp_phase_chord_t chords[UTLP_HDC_TRAJECTORY_DEPTH];

    /** Timestamps of observations (local time, microseconds) */
    uint64_t timestamps[UTLP_HDC_TRAJECTORY_DEPTH];

    /** Write index into ring buffer */
    uint8_t write_idx;

    /** Number of valid observations (0 to DEPTH) */
    uint8_t count;

    /** Computed: is trajectory stable? (low variance in deltas) */
    uint8_t stability;  /* 0-255 */

    /** Computed: average delta per observation (velocity) */
    int8_t velocity[UTLP_CHORD_SIZE];
} trajectory_t;

/*============================================================================
 * HOLOGRAPHIC TRAJECTORY OPERATIONS
 *
 * TRUE HDC: Bundle observations into holographic memory instead of
 * storing raw values. This enables probing for ANY offset hypothesis,
 * not just the ones we have stored samples for.
 *
 * The key insight: Instead of "did I see this exact chord at time T?",
 * we ask "if the offset is H, how well do ALL my observations align?"
 *==========================================================================*/

/**
 * @brief Initialize holographic trajectory
 *
 * @param holo Holographic trajectory state
 * @param origin_us Starting timestamp (local time)
 */
static inline void utlp_hdc_traj_holo_init(trajectory_holo_t *holo, uint64_t origin_us)
{
    if (!holo) return;
    memset(holo, 0, sizeof(trajectory_holo_t));
    holo->origin_us = origin_us;
    holo->last_observation_us = origin_us;
}

/**
 * @brief XOR-bind a chord with a time offset chord
 *
 * HDC BINDING: Associates the observed chord with WHEN it was observed.
 * binding = observation ⊗ time_offset
 *
 * @param chord Observed chord
 * @param offset_quanta Time offset in quanta (ms from origin)
 * @param[out] bound Output bound vector
 */
static inline void utlp_hdc_bind_chord_time(
    const utlp_phase_chord_t chord,
    int64_t offset_quanta,
    int16_t bound[UTLP_CHORD_SIZE])
{
    static const uint8_t primes[UTLP_CHORD_SIZE] = UTLP_PRIMES_INIT;

    for (uint8_t i = 0; i < UTLP_CHORD_SIZE; i++) {
        /* Compute time offset's phase in this dimension */
        int64_t offset_phase = offset_quanta % (int64_t)primes[i];
        if (offset_phase < 0) offset_phase += primes[i];

        /* XOR-like binding: rotate chord by offset phase */
        int16_t rotated = (int16_t)chord[i] - (int16_t)offset_phase;
        if (rotated < 0) rotated += primes[i];

        /* Center around zero for accumulator */
        bound[i] = rotated - (primes[i] / 2);
    }
}

/**
 * @brief Bundle an observation into holographic trajectory
 *
 * HDC BUNDLING: Adds the bound (chord ⊗ time) pair to the holographic
 * memory using multi-timescale EMA (same as latency_holo_t).
 *
 * ANTICIPATORY DESIGN: Each observation STRENGTHENS the holographic
 * representation of "this is when chords like this appear."
 *
 * @param holo Holographic trajectory state
 * @param chord Observed chord (peer's swarm chord from beacon)
 * @param timestamp_us When we received it (local time)
 */
static inline void utlp_hdc_traj_holo_observe(
    trajectory_holo_t *holo,
    const utlp_phase_chord_t chord,
    uint64_t timestamp_us)
{
    if (!holo) return;

    /* Compute time offset from our origin (in quanta = ms) */
    int64_t offset_quanta = (int64_t)(timestamp_us - holo->origin_us) / 1000;

    /* Bind chord to its time offset */
    int16_t bound[UTLP_CHORD_SIZE];
    utlp_hdc_bind_chord_time(chord, offset_quanta, bound);

    /* Bundle into multi-timescale accumulators (EMA update) */
    for (uint8_t i = 0; i < UTLP_CHORD_SIZE; i++) {
        /* Fast timescale: α ≈ 25% (responds in ~4 observations) */
        holo->fast_acc[i] += (bound[i] - holo->fast_acc[i]) * UTLP_HDC_ALPHA_FAST_X256 / 256;

        /* Medium timescale: α ≈ 3% (responds in ~32 observations) */
        holo->medium_acc[i] += (bound[i] - holo->medium_acc[i]) * UTLP_HDC_ALPHA_MEDIUM_X256 / 256;

        /* Slow timescale: α ≈ 0.4% (responds in ~256 observations) */
        holo->slow_acc[i] += (bound[i] - holo->slow_acc[i]) * UTLP_HDC_ALPHA_SLOW_X256 / 256;

        /* Blend timescales based on stability (higher stability = favor slow) */
        uint8_t w_fast = (holo->stability < 128) ? 128 : 64;
        uint8_t w_medium = 64;
        uint8_t w_slow = 256 - w_fast - w_medium;

        holo->bundled[i] = (int16_t)(
            (holo->fast_acc[i] * w_fast +
             holo->medium_acc[i] * w_medium +
             holo->slow_acc[i] * w_slow) / 256);
    }

    /* Update statistics */
    holo->observation_count++;
    holo->last_observation_us = timestamp_us;

    /* Update window coverage (how much time span we've observed) */
    uint64_t span_us = timestamp_us - holo->origin_us;
    if (span_us > 60000000ULL) {  /* > 60s */
        holo->window_coverage = 255;
    } else {
        holo->window_coverage = (uint8_t)(span_us / 235294ULL);  /* Scale to 0-255 */
    }
}

/**
 * @brief Probe holographic memory with an offset hypothesis
 *
 * THE HUMMING SEARCH (HDC-native):
 * "If the true offset is H, how well does my memory predict the probe chord?"
 *
 * Instead of scanning raw samples, we probe the HOLOGRAPHIC SUPERPOSITION.
 * This works even for offsets we never directly observed!
 *
 * @param holo Holographic trajectory state
 * @param probe_chord Chord to probe with (current peer chord)
 * @param hypothesis_quanta Offset hypothesis to test (in ms/quanta)
 * @return Similarity score 0-255 (255 = perfect match)
 */
static inline uint8_t utlp_hdc_traj_holo_probe(
    const trajectory_holo_t *holo,
    const utlp_phase_chord_t probe_chord,
    int64_t hypothesis_quanta)
{
    if (!holo || holo->observation_count < 3) return 0;

    /* Bind probe chord with hypothesized offset */
    int16_t bound_probe[UTLP_CHORD_SIZE];
    utlp_hdc_bind_chord_time(probe_chord, hypothesis_quanta, bound_probe);

    /* Compute similarity between bound probe and bundled memory */
    static const uint8_t primes[UTLP_CHORD_SIZE] = UTLP_PRIMES_INIT;
    uint16_t similarity = 0;

    for (uint8_t i = 0; i < UTLP_CHORD_SIZE; i++) {
        int16_t diff = bound_probe[i] - holo->bundled[i];
        if (diff < 0) diff = -diff;

        /* Threshold: 10% of prime's range (centered, so max = prime/2) */
        uint8_t threshold = primes[i] / 5;  /* Generous for holographic noise */

        if (diff <= threshold) {
            similarity += 32;  /* Each matching dimension contributes 32 */
        } else if (diff <= threshold * 2) {
            similarity += 16;  /* Partial match */
        }
    }

    return (similarity > 255) ? 255 : (uint8_t)similarity;
}

/**
 * @brief Find best offset by probing holographic memory
 *
 * ANTICIPATORY OFFSET DISCOVERY:
 * Instead of comparing raw samples (reactive), we probe multiple
 * offset HYPOTHESES against our holographic model (anticipatory).
 *
 * The memory PREDICTS which offset would make observations align,
 * rather than just remembering what offsets we've seen.
 *
 * @param holo Holographic trajectory state
 * @param probe_chord Current peer chord to locate
 * @param search_range_ms Maximum offset to search (±ms from now)
 * @param[out] best_offset_us Best offset found (in microseconds)
 * @return Confidence in result (0-255)
 */
static inline uint8_t utlp_hdc_traj_holo_find_offset(
    const trajectory_holo_t *holo,
    const utlp_phase_chord_t probe_chord,
    uint32_t search_range_ms,
    int64_t *best_offset_us)
{
    if (!holo || !best_offset_us || holo->observation_count < 3) {
        if (best_offset_us) *best_offset_us = 0;
        return 0;
    }

    uint8_t best_similarity = 0;
    int64_t best_quanta = 0;

    /* Golden ratio search for efficiency */
    int64_t range = (int64_t)search_range_ms;
    int64_t step = (range > 100) ? range / 20 : 5;  /* Coarse then fine */

    /* Two-phase search: coarse then fine */
    for (int phase = 0; phase < 2; phase++) {
        int64_t start = (phase == 0) ? -range : (best_quanta - step * 5);
        int64_t end = (phase == 0) ? range : (best_quanta + step * 5);

        for (int64_t h = start; h <= end; h += step) {
            uint8_t sim = utlp_hdc_traj_holo_probe(holo, probe_chord, h);
            if (sim > best_similarity) {
                best_similarity = sim;
                best_quanta = h;
            }
        }

        /* Refine step for second phase */
        step = (step > 5) ? step / 5 : 1;
        if (phase == 0 && best_similarity < 64) {
            /* Poor coarse result - skip fine search */
            break;
        }
    }

    *best_offset_us = best_quanta * 1000;  /* quanta (ms) → microseconds */

    /* Update confidence based on similarity and observation count */
    uint8_t obs_factor = (holo->observation_count > 10) ? 255 :
                         (uint8_t)(holo->observation_count * 25);
    uint8_t confidence = (uint8_t)((uint16_t)best_similarity * obs_factor / 256);

    return confidence;
}

/*============================================================================
 * LEGACY TRAJECTORY (Ring Buffer) - For Backward Compatibility
 *
 * DEPRECATED: New code should use trajectory_holo_t.
 * Kept for gradual migration.
 *==========================================================================*/

/**
 * @brief Record a chord observation into trajectory history (LEGACY)
 *
 * @param traj Trajectory state
 * @param chord Observed chord
 * @param timestamp_us Local timestamp when observed
 */
static inline void utlp_hdc_trajectory_record(
    trajectory_t *traj,
    const utlp_phase_chord_t chord,
    uint64_t timestamp_us)
{
    if (!traj) return;

    /* Store in ring buffer */
    memcpy(traj->chords[traj->write_idx], chord, UTLP_CHORD_SIZE);
    traj->timestamps[traj->write_idx] = timestamp_us;

    traj->write_idx = (traj->write_idx + 1) % UTLP_HDC_TRAJECTORY_DEPTH;
    if (traj->count < UTLP_HDC_TRAJECTORY_DEPTH) {
        traj->count++;
    }

    /* Recompute velocity if we have enough observations */
    if (traj->count >= 2) {
        /* Get oldest and newest */
        uint8_t oldest_idx = (traj->write_idx + UTLP_HDC_TRAJECTORY_DEPTH - traj->count)
                            % UTLP_HDC_TRAJECTORY_DEPTH;
        uint8_t newest_idx = (traj->write_idx + UTLP_HDC_TRAJECTORY_DEPTH - 1)
                            % UTLP_HDC_TRAJECTORY_DEPTH;

        /* Compute delta per observation */
        static const uint8_t primes[UTLP_CHORD_SIZE] = UTLP_PRIMES_INIT;
        for (uint8_t i = 0; i < UTLP_CHORD_SIZE; i++) {
            int16_t diff = (int16_t)traj->chords[newest_idx][i]
                         - (int16_t)traj->chords[oldest_idx][i];
            uint8_t prime = primes[i];

            /* Circular wrap */
            if (diff > (int16_t)(prime / 2)) diff -= prime;
            if (diff < -(int16_t)(prime / 2)) diff += prime;

            /* Average over observations */
            traj->velocity[i] = (int8_t)(diff / (int16_t)(traj->count - 1));
        }
    }
}

/**
 * @brief Check if two trajectories are parallel (same reference frame)
 *
 * Parallel trajectories = devices are synced (evolving in lockstep).
 * This is the HDC-native definition of "time sync".
 *
 * @param ours Our trajectory
 * @param theirs Peer's trajectory (reconstructed from beacon history)
 * @return Parallelism score 0-8 (8 = perfectly parallel)
 */
static inline uint8_t utlp_hdc_trajectory_parallelism(
    const trajectory_t *ours,
    const trajectory_t *theirs)
{
    if (!ours || !theirs) return 0;
    if (ours->count < UTLP_HDC_MIN_OBSERVATIONS) return 0;
    if (theirs->count < UTLP_HDC_MIN_OBSERVATIONS) return 0;

    /* Compare velocities - parallel means same velocity vector */
    uint8_t matches = 0;
    for (uint8_t i = 0; i < UTLP_CHORD_SIZE; i++) {
        int8_t diff = ours->velocity[i] - theirs->velocity[i];
        if (diff < 0) diff = -diff;

        /* Tolerance: ±2 quanta per observation */
        if (diff <= 2) {
            matches++;
        }
    }

    return matches;
}

/*============================================================================
 * SLIDING WINDOW SCANNER (THE HUMMING SEARCH)
 *
 * Given a peer's chord (the "Shard"), slide it along our trajectory history
 * (the "Master Tape") to find where it resonates. The resonance point tells
 * us the TIME OFFSET between our timeline and peer's timeline.
 *
 * This is the core HDC operation for N=2 convergence:
 * - We don't compare single snapshots (that never converges)
 * - We scan the peer's chord along our history
 * - The point of maximum similarity = the offset
 *==========================================================================*/

/**
 * @brief Compute chord similarity (0-8 dimensions matching)
 *
 * @param chord_a First chord
 * @param chord_b Second chord
 * @return Number of dimensions within tolerance (0-8)
 */
static inline uint8_t utlp_hdc_chord_similarity(
    const utlp_phase_chord_t chord_a,
    const utlp_phase_chord_t chord_b)
{
    static const uint8_t primes[UTLP_CHORD_SIZE] = UTLP_PRIMES_INIT;
    uint8_t matches = 0;

    for (uint8_t i = 0; i < UTLP_CHORD_SIZE; i++) {
        int16_t diff = (int16_t)chord_a[i] - (int16_t)chord_b[i];

        /* Circular distance on the ring */
        if (diff < 0) diff = -diff;
        if (diff > primes[i] / 2) diff = primes[i] - diff;

        /* Tolerance: 10% of prime value (~24 for prime 241) */
        uint8_t threshold = primes[i] / 10;
        if (diff <= threshold) {
            matches++;
        }
    }

    return matches;
}

/**
 * @brief Scan trajectory to find where peer's chord resonates
 *
 * The "humming search" - slide the Shard along the Master Tape.
 * Returns the time offset where maximum similarity is found.
 *
 * KEY INSIGHT: This finds WHEN on our timeline the peer's chord
 * would have matched, telling us the offset between timelines.
 *
 * @param our_trajectory Our chord history (Master Tape)
 * @param peer_chord The received chord (Shard)
 * @param[out] offset_us Computed offset in microseconds (negative = peer is ahead)
 * @return Confidence of match (0-8, 8 = perfect resonance)
 */
static inline uint8_t utlp_hdc_scan_for_offset(
    const trajectory_t *our_trajectory,
    const utlp_phase_chord_t peer_chord,
    int64_t *offset_us)
{
    if (!our_trajectory || !offset_us) {
        if (offset_us) *offset_us = 0;
        return 0;
    }

    if (our_trajectory->count < 2) {
        /* Not enough history to scan */
        *offset_us = 0;
        return 0;
    }

    uint8_t best_similarity = 0;
    int64_t best_offset_us = 0;
    uint8_t best_idx = 0;

    /* Get the newest timestamp as our reference point */
    uint8_t newest_idx = (our_trajectory->write_idx + UTLP_HDC_TRAJECTORY_DEPTH - 1)
                        % UTLP_HDC_TRAJECTORY_DEPTH;
    uint64_t now_us = our_trajectory->timestamps[newest_idx];

    /* Slide peer's chord along our trajectory history */
    for (uint8_t i = 0; i < our_trajectory->count; i++) {
        uint8_t idx = (our_trajectory->write_idx + UTLP_HDC_TRAJECTORY_DEPTH - our_trajectory->count + i)
                     % UTLP_HDC_TRAJECTORY_DEPTH;

        /* Compare peer's chord to this point in our history */
        uint8_t similarity = utlp_hdc_chord_similarity(
            our_trajectory->chords[idx], peer_chord);

        if (similarity > best_similarity) {
            best_similarity = similarity;
            best_idx = idx;

            /* Compute time offset: how old is this match point?
             * Negative offset = peer's chord matched an OLDER point in our history
             *                 = peer is BEHIND us (their clock is slower)
             * Positive offset = peer's chord matched a NEWER point
             *                 = peer is AHEAD of us (shouldn't happen with proper history)
             */
            int64_t match_age_us = (int64_t)(now_us - our_trajectory->timestamps[idx]);
            best_offset_us = -match_age_us;  /* Peer is this much behind */
        }
    }

    *offset_us = best_offset_us;

    /* Log for debugging */
    #if 0  /* Enable for debugging */
    if (best_similarity >= 6) {
        /* Good match found */
    }
    #endif

    return best_similarity;
}

/**
 * @brief Evolve a chord forward by applying an offset
 *
 * This is how we "rotate" the time object - apply the computed offset
 * to get the swarm-synchronized chord without polluting our local clock.
 *
 * GLASS WALL: The local phase engine stays clean. This function creates
 * a NEW chord that represents swarm time = local time + offset.
 *
 * @param local_chord Our clean local chord (read-only, THE RULER)
 * @param offset_us The offset to apply (from scanning)
 * @param[out] swarm_chord Output swarm-synchronized chord
 */
static inline void utlp_hdc_apply_offset_to_chord(
    const utlp_phase_chord_t local_chord,
    int64_t offset_us,
    utlp_phase_chord_t swarm_chord)
{
    static const uint8_t primes[UTLP_CHORD_SIZE] = UTLP_PRIMES_INIT;

    /* Convert offset from microseconds to ticks (assuming 100µs per tick) */
    int32_t offset_ticks = (int32_t)(offset_us / 100);

    for (uint8_t i = 0; i < UTLP_CHORD_SIZE; i++) {
        /* Apply offset with modular arithmetic on the ring */
        int32_t adjusted = (int32_t)local_chord[i] + offset_ticks;

        /* Wrap to [0, prime-1] */
        while (adjusted < 0) adjusted += primes[i];
        while (adjusted >= primes[i]) adjusted -= primes[i];

        swarm_chord[i] = (uint8_t)adjusted;
    }
}

/*============================================================================
 * HOLOGRAPHIC LATENCY MEMORY
 *
 * Encodes latency "shape" rather than scalar value. Similar latencies
 * (same causal sources) produce similar hypervectors, enabling prediction
 * and anomaly detection.
 *==========================================================================*/

/**
 * @brief Holographic latency memory (96 bytes)
 *
 * Multi-timescale EMA accumulators separate fast (radio/ISR jitter),
 * medium (task scheduling), and slow (thermal/crystal drift) components
 * WITHOUT explicit labeling - the timescales self-separate.
 */
typedef struct {
    /* === 8-byte aligned: Hypervector accumulators (64 bytes) === */
    int16_t fast_acc[UTLP_CHORD_SIZE];      /**< Fast: ~1s response */
    int16_t medium_acc[UTLP_CHORD_SIZE];    /**< Medium: ~30s response */
    int16_t slow_acc[UTLP_CHORD_SIZE];      /**< Slow: ~5min response */
    int16_t predicted[UTLP_CHORD_SIZE];     /**< Blended prediction */

    /* === 4-byte aligned: Scalar statistics (20 bytes) === */
    uint32_t observation_count;             /**< Total observations */
    int32_t  last_error_us;                 /**< Last prediction error */
    int32_t  anomaly_threshold_x256;        /**< Scaled threshold */
    uint32_t last_update_ms;                /**< Timestamp for decay */
    uint32_t anomaly_count;                 /**< Surprise counter */

    /* === 1-byte aligned: Control (12 bytes) === */
    uint8_t  confidence;                    /**< 0-255: prediction confidence */
    uint8_t  stability;                     /**< 0-255: latency stability */
    uint8_t  timescale_hint;                /**< Dominant timescale (0=fast, 2=slow) */
    uint8_t  flags;                         /**< State flags */
    uint8_t  last_chord[UTLP_CHORD_SIZE];   /**< Last observed chord */
} latency_holo_t;

/**
 * @brief Encode latency as chord (distributed representation)
 *
 * @param latency_us Observed latency in microseconds
 * @param[out] chord Output chord (8 bytes)
 */
static inline void utlp_hdc_latency_to_chord(int32_t latency_us, uint8_t chord[UTLP_CHORD_SIZE])
{
    uint32_t abs_lat = (latency_us >= 0) ? (uint32_t)latency_us : (uint32_t)(-latency_us);

    /* Compute residues mod each prime */
    chord[0] = (uint8_t)(abs_lat % UTLP_PRIME_0);
    chord[1] = (uint8_t)(abs_lat % UTLP_PRIME_1);
    chord[2] = (uint8_t)(abs_lat % UTLP_PRIME_2);
    chord[3] = (uint8_t)(abs_lat % UTLP_PRIME_3);
    chord[4] = (uint8_t)(abs_lat % UTLP_PRIME_4);
    chord[5] = (uint8_t)(abs_lat % UTLP_PRIME_5);
    chord[6] = (uint8_t)(abs_lat % UTLP_PRIME_6);
    chord[7] = (uint8_t)(abs_lat % UTLP_PRIME_7);
}

/**
 * @brief Update holographic latency memory with new observation
 *
 * @param holo Holographic state
 * @param latency_us Observed latency
 * @param now_ms Current time in milliseconds
 */
static inline void utlp_hdc_latency_update(latency_holo_t *holo, int32_t latency_us, uint32_t now_ms)
{
    if (!holo) return;

    uint8_t obs_chord[UTLP_CHORD_SIZE];
    utlp_hdc_latency_to_chord(latency_us, obs_chord);

    /* Multi-timescale EMA update */
    for (uint8_t i = 0; i < UTLP_CHORD_SIZE; i++) {
        int16_t obs = (int16_t)obs_chord[i];

        /* Fast: alpha = 64/256 = 25% */
        holo->fast_acc[i] += (int16_t)(((obs - holo->fast_acc[i])
                                        * UTLP_HDC_ALPHA_FAST_X256) >> 8);

        /* Medium: alpha = 8/256 = 3.1% */
        holo->medium_acc[i] += (int16_t)(((obs - holo->medium_acc[i])
                                          * UTLP_HDC_ALPHA_MEDIUM_X256) >> 8);

        /* Slow: alpha = 1/256 = 0.4% */
        holo->slow_acc[i] += (int16_t)(((obs - holo->slow_acc[i])
                                        * UTLP_HDC_ALPHA_SLOW_X256) >> 8);
    }

    memcpy(holo->last_chord, obs_chord, UTLP_CHORD_SIZE);
    holo->observation_count++;
    holo->last_update_ms = now_ms;
}

/**
 * @brief Generate prediction from holographic memory
 *
 * @param holo Holographic state
 * @param[out] predicted_chord Output predicted chord
 */
static inline void utlp_hdc_latency_predict(const latency_holo_t *holo, uint8_t predicted_chord[UTLP_CHORD_SIZE])
{
    if (!holo || !predicted_chord) return;

    /* Weight selection based on stability */
    uint8_t w_fast, w_medium, w_slow;
    if (holo->stability < 86) {
        w_fast = 192; w_medium = 48; w_slow = 16;   /* Volatile */
    } else if (holo->stability < 171) {
        w_fast = 64; w_medium = 128; w_slow = 64;   /* Normal */
    } else {
        w_fast = 16; w_medium = 48; w_slow = 192;   /* Stable */
    }

    static const uint8_t primes[UTLP_CHORD_SIZE] = UTLP_PRIMES_INIT;
    for (uint8_t i = 0; i < UTLP_CHORD_SIZE; i++) {
        int32_t blended = (holo->fast_acc[i] * w_fast +
                          holo->medium_acc[i] * w_medium +
                          holo->slow_acc[i] * w_slow) >> 8;

        if (blended < 0) blended = 0;
        if (blended >= primes[i]) blended = primes[i] - 1;

        predicted_chord[i] = (uint8_t)blended;
    }
}

/**
 * @brief Check similarity between observed and predicted latency
 *
 * @param holo Holographic state
 * @param latency_us Observed latency
 * @return Similarity 0-8 (8 = perfect match)
 */
static inline uint8_t utlp_hdc_latency_similarity(const latency_holo_t *holo, int32_t latency_us)
{
    uint8_t obs_chord[UTLP_CHORD_SIZE];
    utlp_hdc_latency_to_chord(latency_us, obs_chord);

    static const uint8_t primes[UTLP_CHORD_SIZE] = UTLP_PRIMES_INIT;
    uint8_t matches = 0;

    for (uint8_t i = 0; i < UTLP_CHORD_SIZE; i++) {
        uint8_t threshold = primes[i] / 10;
        if (threshold < 2) threshold = 2;

        int16_t diff = (int16_t)obs_chord[i] - (int16_t)(holo->predicted[i] & 0xFF);
        if (diff < 0) diff = -diff;
        if (diff > primes[i] / 2) diff = primes[i] - diff;

        if (diff <= threshold) matches++;
    }

    return matches;
}

/*============================================================================
 * ROLL-IN STATE MACHINE
 *
 * When a device boots fresh, it must "roll into" phase coherence with
 * an established peer. This is elastic nudging, not hard adoption.
 *==========================================================================*/

/** Roll-in state */
typedef enum {
    ROLLIN_IDLE = 0,        /**< Not rolling in (established or no peer) */
    ROLLIN_SEEKING,         /**< Looking for authoritative peer */
    ROLLIN_CONVERGING,      /**< Nudging toward peer's phase */
    ROLLIN_COHERENT,        /**< Achieved coherence, accumulating history */
    ROLLIN_TIMEOUT          /**< Failed to achieve coherence */
} rollin_state_t;

/** Number of consecutive coherent observations needed to confirm roll-in complete */
#define UTLP_HDC_ROLLIN_COHERENT_COUNT  5

/**
 * @brief Roll-in state tracking
 */
typedef struct {
    rollin_state_t state;

    /** Target peer MAC we're rolling toward */
    uint8_t target_mac[6];

    /** Peer's observation count (their authority) */
    uint32_t peer_authority;

    /** Ticks spent in current state */
    uint16_t ticks_in_state;

    /** Total tick count since roll-in started */
    uint16_t tick_count;

    /** Consecutive coherent observations (all dims aligned) */
    uint8_t convergence_count;

    /** Our accumulated offset from lineage (for CRT audit) */
    int8_t lineage_offset[UTLP_CHORD_SIZE];

    /** How many dimensions are coherent */
    uint8_t coherent_dimensions;

    /** Reserved */
    uint8_t _reserved;
} rollin_t;

/**
 * @brief Initialize roll-in state for fresh boot
 *
 * @param rollin Roll-in state
 */
static inline void utlp_hdc_rollin_init(rollin_t *rollin)
{
    if (!rollin) return;
    memset(rollin, 0, sizeof(rollin_t));
    rollin->state = ROLLIN_SEEKING;
}

/**
 * @brief Compute elastic nudge toward peer's chord
 *
 * Called every 10ms tick during roll-in. Returns per-dimension nudge values.
 *
 * @param agreement Current agreement with target peer
 * @param[out] nudge Output nudge values (±1 per dimension, or 0 if coherent)
 * @return Number of dimensions that need nudging (0 = fully coherent)
 */
static inline uint8_t utlp_hdc_compute_nudge(
    const agreement_vector_t *agreement,
    int8_t nudge[UTLP_CHORD_SIZE])
{
    if (!agreement || !nudge) return UTLP_CHORD_SIZE;

    uint8_t dimensions_needing_nudge = 0;

    for (uint8_t i = 0; i < UTLP_CHORD_SIZE; i++) {
        int8_t dim_offset = agreement->dimension[i];

        /* Threshold for "close enough" - within 2 quanta */
        if (dim_offset > 2) {
            nudge[i] = -UTLP_HDC_ROLLIN_RATE;  /* We're ahead, slow down */
            dimensions_needing_nudge++;
        } else if (dim_offset < -2) {
            nudge[i] = +UTLP_HDC_ROLLIN_RATE;  /* We're behind, speed up */
            dimensions_needing_nudge++;
        } else {
            nudge[i] = 0;  /* Close enough, no nudge needed */
        }
    }

    return dimensions_needing_nudge;
}

/*============================================================================
 * AUTHORITY MODEL
 *
 * Authority = observation count. This is the HDC-native trust anchor.
 * A device with 1000 observations cannot be overridden by a device with 0.
 *==========================================================================*/

/**
 * @brief Compute authority weight from observation count
 *
 * Uses logarithmic scaling so early observations matter more,
 * but established devices have overwhelming authority.
 *
 * @param observation_count Number of chord observations
 * @return Authority weight 0-255
 */
static inline uint8_t utlp_hdc_authority_weight(uint32_t observation_count)
{
    if (observation_count == 0) return 0;
    if (observation_count >= 1024) return 255;

    /* Approximate log2 using bit position */
    uint8_t log2 = 0;
    uint32_t temp = observation_count;
    while (temp > 1) {
        temp >>= 1;
        log2++;
    }

    /* Scale: log2(1024) = 10 → 255 */
    return (uint8_t)((log2 * 255) / 10);
}

/**
 * @brief Determine if we should trust peer over ourselves
 *
 * @param our_observations Our observation count
 * @param peer_observations Peer's observation count
 * @param agreement Current agreement vector
 * @return true if peer has authority and we should follow
 */
static inline bool utlp_hdc_peer_has_authority(
    uint32_t our_observations,
    uint32_t peer_observations,
    const agreement_vector_t *agreement)
{
    /* Fresh boot always follows anyone with observations */
    if (our_observations < UTLP_HDC_MIN_OBSERVATIONS) {
        return peer_observations >= UTLP_HDC_MIN_OBSERVATIONS;
    }

    /* Neither has authority - use agreement quality to decide */
    if (peer_observations < UTLP_HDC_MIN_OBSERVATIONS) {
        return false;  /* We have more authority */
    }

    /* Both have observations - peer needs significantly more to override */
    /* Ratio: peer needs 4x our observations to have authority */
    return peer_observations > (our_observations * 4);
}

/*============================================================================
 * PATTERN MEMORY (THE SIDECAR / APP LAYER)
 *
 * This implements the "Glass Wall" architecture from Gemini:
 * - UTLP provides the clean clock (THE RULER) - read-only
 * - App layer has its own memory (THE PENCIL) - uses time as key
 *
 * The pattern memory is pre-bundled with actions bound to time keys:
 *   PatternMemory = Σ(action_vector ⊗ time_key)
 *
 * At runtime, we probe: action = Similarity(PatternMemory, current_time)
 *
 * CRITICAL: The app NEVER writes back to UTLP. It only READS the time key.
 * This prevents "polluting the clock" with dirty data.
 *
 * Capacity: With 8D vectors, we can reliably distinguish ~8-16 actions.
 * For LED ON/OFF patterns, this is plenty.
 *==========================================================================*/

/** Maximum number of distinct actions in a pattern */
#define UTLP_PATTERN_MAX_ACTIONS  8

/** Action codes (what the app should do) */
typedef enum {
    UTLP_ACTION_NONE = 0,
    UTLP_ACTION_LED_OFF,
    UTLP_ACTION_LED_ON,
    UTLP_ACTION_LED_BREATHE,
    UTLP_ACTION_MOTOR_LEFT,
    UTLP_ACTION_MOTOR_RIGHT,
    UTLP_ACTION_MOTOR_BOTH,
    UTLP_ACTION_CUSTOM
} utlp_action_t;

/**
 * @brief A single action binding (action ⊗ time_key)
 *
 * Represents: "At phase range [start, end), do this action"
 */
typedef struct {
    uint8_t phase_start;   /**< Start phase (0-240 for prime 241) */
    uint8_t phase_end;     /**< End phase (exclusive) */
    uint8_t prime_idx;     /**< Which prime dimension to check (0-7) */
    uint8_t action;        /**< Action code (utlp_action_t) */
} pattern_binding_t;

/**
 * @brief Pattern memory - holds bundled action bindings
 *
 * This is the "Sidecar" - the app's own memory that uses
 * UTLP time as a key to look up what action to perform.
 */
typedef struct {
    pattern_binding_t bindings[UTLP_PATTERN_MAX_ACTIONS];
    uint8_t binding_count;
    uint8_t default_action;  /**< Action when no binding matches */
} pattern_memory_t;

/**
 * @brief Initialize pattern memory with default (LED blink at 1Hz)
 *
 * Creates a simple ON/OFF pattern using prime[0]=241:
 * - Phase 0-120: LED ON (50% duty)
 * - Phase 121-240: LED OFF
 *
 * @param pattern Pattern memory to initialize
 */
static inline void utlp_pattern_init_led_blink(pattern_memory_t *pattern)
{
    if (!pattern) return;

    memset(pattern, 0, sizeof(pattern_memory_t));

    /* LED ON for first half of cycle */
    pattern->bindings[0].phase_start = 0;
    pattern->bindings[0].phase_end = 121;  /* 121/241 ≈ 50% */
    pattern->bindings[0].prime_idx = 0;    /* Use prime[0]=241 */
    pattern->bindings[0].action = UTLP_ACTION_LED_ON;

    /* LED OFF for second half */
    pattern->bindings[1].phase_start = 121;
    pattern->bindings[1].phase_end = 241;
    pattern->bindings[1].prime_idx = 0;
    pattern->bindings[1].action = UTLP_ACTION_LED_OFF;

    pattern->binding_count = 2;
    pattern->default_action = UTLP_ACTION_LED_OFF;
}

/**
 * @brief Probe pattern memory with current time to get action
 *
 * This is the runtime "similarity check" - we use the UTLP time chord
 * as a KEY to look up what action the app should perform.
 *
 * GLASS WALL: We READ the chord from UTLP (the ruler) but NEVER write
 * back to it. The pattern memory is completely separate from the clock.
 *
 * @param pattern The pattern memory (app's sidecar)
 * @param swarm_chord Current swarm-synchronized chord (from UTLP)
 * @return Action code to perform
 */
static inline utlp_action_t utlp_pattern_probe(
    const pattern_memory_t *pattern,
    const utlp_phase_chord_t swarm_chord)
{
    if (!pattern || pattern->binding_count == 0) {
        return UTLP_ACTION_NONE;
    }

    /* Check each binding to find matching phase range */
    for (uint8_t i = 0; i < pattern->binding_count; i++) {
        const pattern_binding_t *b = &pattern->bindings[i];

        /* Get the relevant phase dimension */
        uint8_t phase = swarm_chord[b->prime_idx];

        /* Check if phase is in range [start, end) */
        if (phase >= b->phase_start && phase < b->phase_end) {
            return (utlp_action_t)b->action;
        }
    }

    return (utlp_action_t)pattern->default_action;
}

/**
 * @brief Add a custom binding to pattern memory
 *
 * @param pattern Pattern memory
 * @param prime_idx Which prime dimension (0-7)
 * @param phase_start Start of phase range
 * @param phase_end End of phase range (exclusive)
 * @param action Action code
 * @return true if added, false if memory full
 */
static inline bool utlp_pattern_add_binding(
    pattern_memory_t *pattern,
    uint8_t prime_idx,
    uint8_t phase_start,
    uint8_t phase_end,
    utlp_action_t action)
{
    if (!pattern || pattern->binding_count >= UTLP_PATTERN_MAX_ACTIONS) {
        return false;
    }

    pattern_binding_t *b = &pattern->bindings[pattern->binding_count];
    b->prime_idx = prime_idx;
    b->phase_start = phase_start;
    b->phase_end = phase_end;
    b->action = (uint8_t)action;

    pattern->binding_count++;
    return true;
}

#ifdef __cplusplus
}
#endif

#endif /* UTLP_HDC_H */
