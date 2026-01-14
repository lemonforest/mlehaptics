/**
 * @file utlp.c
 * @brief UTLP v4 - Phase 2 First Contact (N=2 Epoch Resolution)
 *
 * PHASE 2 FIRST CONTACT: Two devices discover each other and resolve epochs.
 *
 * "N=1 is VALID LIFE. A single device is living its own timeline
 * with full authority." - Biological governance model
 *
 * "Time is a chord, not a number." - Vector time is FOUNDATIONAL
 *
 * Phase 2 implements:
 * - Stem cell depth model (fresh=128, Time Lord=255, exhausted=0)
 * - Beacon broadcasting and reception
 * - Contact type detection (new, known, rebooted peers)
 * - Epoch resolution using stem cell rules:
 *   1. Higher depth (more vitality) wins
 *   2. Equal depth → older origin_time wins
 *   3. True tie → lower MAC adopts from higher MAC
 * - Defense Layer 1: Chord-origin verification
 * - Telomere shortening on adoption (depth--)
 *
 * Still from Phase 1:
 * - epoch_state_t initialization (7 bytes packed)
 * - Cold boot with unique session_salt from hardware RNG
 * - Vector time via HPLC phase engine (phase chord is NATIVE)
 * - 1Hz LED heartbeat proving life
 * - ILC (Interrupt Latency Compensation) learning
 *
 * @version 2.0.0 (Phase 2 First Contact - N=2 Epoch Resolution)
 * @date 2026-01-11
 *
 * @copyright
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#include "utlp_config.h"
#include "utlp_hal.h"
#include "utlp_phase.h"
#include "utlp_transport.h"
#include "utlp_arbor.h"
#include "utlp_security.h"  /* utlp_wire_packet_t, utlp_exon_t, utlp_intron_t */
#include "utlp_smsp.h"

#include <string.h>

#ifdef ESP_PLATFORM
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#endif

static const char *TAG = "UTLP_PHASE2";

/*============================================================================
 * EPOCH STATE (Phase 1 - N=1 Genesis)
 *
 * The epoch represents the "lineage" of time in the swarm. Each device
 * starts as an originator (depth=0) and may adopt a peer's epoch if that
 * peer has been validated by external life (depth>0).
 *
 * Wire format: 7 bytes exactly for peer exchange
 *==========================================================================*/

/**
 * @brief Epoch state - packed for wire transmission
 *
 * Principle: "N=1 is VALID LIFE. A single device is living its own
 * timeline with full authority."
 *
 * Stem Cell Model:
 * - Fresh boot: depth = UTLP_DEPTH_FRESH (128) - somatic cell, half vitality
 * - Time Lord: depth = UTLP_DEPTH_TIME_LORD (255) - telomerase regeneration
 * - Exhausted: depth = UTLP_DEPTH_EXHAUSTED (0) - cannot propagate
 *
 * See utlp_config.h for full stem cell depth model documentation.
 */
typedef struct __attribute__((packed)) {
    uint32_t origin_time;      /**< When epoch lineage began (boot moment) */
    uint8_t  depth;            /**< Stem cell model: 128=fresh, 255=Time Lord, 0=exhausted */
    uint8_t  session_salt[2];  /**< Per-boot random (anti-replay) */
} epoch_state_t;

/* Compile-time validation of epoch structure */
_Static_assert(sizeof(epoch_state_t) == 7, "epoch_state_t must be exactly 7 bytes");

/*============================================================================
 * PHASE 2: SEISMIC CHIRP BEACON (3-Burst @ 2ms Spacing)
 *
 * "Every beacon is a seismic chirp - 3 packets spaced 2ms apart,
 * all carrying the SAME timestamp (the chirp epoch)."
 *
 * Uses the 32-byte utlp_wire_packet_t format from utlp_security.h:
 * - EXON (24 bytes cleartext): SequenceID, Timestamp, NTP, Salt, Stratum, Version
 * - INTRON (8 bytes): TX_Power, Battery, Drift, Opcode, Payload[3]
 *
 * The burst index is carried in intron.payload[2] for heartbeat opcodes.
 *
 * WHAT THE 3-BURST PATTERN REVEALS (not just jitter!):
 * 1. TIME OFFSET: Burst 0 timestamp vs local time = clock offset
 * 2. RECEIVER JITTER: Deviation from expected 2ms inter-burst spacing
 * 3. PROPAGATION CHANGE: Consistent drift in inter-burst timing = device movement
 *    - Delay increasing → devices moving apart
 *    - Delay decreasing → devices moving closer
 * 4. TDOA RANGING: With multiple receivers, position triangulation is possible
 *
 * WHY SAME TIMESTAMP FOR ALL BURSTS:
 * The 2ms spacing is a KNOWN REFERENCE SIGNAL. Deviations reveal
 * receiver-side effects (jitter, motion), not sender drift.
 *
 * @see UTLP_Technical_Supplement_S1.md Section 1.4 - Seismic Chirp
 * @see utlp_security.h - utlp_wire_packet_t definition
 *==========================================================================*/

/** @brief Protocol version for Phase 2 (Vector Time) */
#define UTLP_PROTOCOL_VERSION_N2    0x02

/*============================================================================
 * PHASE 2: PEER TRACKING (First Contact Detection)
 *
 * Track known peers to detect:
 * - CONTACT_NEW_PEER: Never seen this MAC before
 * - CONTACT_KNOWN_PEER: Known MAC, same session salt
 * - CONTACT_REBOOTED_PEER: Known MAC, different salt (peer rebooted)
 *==========================================================================*/

/** @brief Maximum peers to track (memory budget) */
#define UTLP_MAX_PEERS              8

/**
 * @brief Contact type classification for first contact handling
 */
typedef enum {
    CONTACT_NEW_PEER = 0,       /**< Never seen this MAC before */
    CONTACT_KNOWN_PEER,         /**< Known MAC, same session salt */
    CONTACT_REBOOTED_PEER       /**< Known MAC, different salt */
} contact_type_t;

/*============================================================================
 * GENESIS PATTERN SCRIPT (SMSP-Style Playback Definition)
 *
 * The genesis pulse follows a predictable ramp pattern - like a heartbeat
 * or fingerprint that identifies a newborn device. This is a "script" that
 * can be encoded, played back, and compared against observed behavior.
 *
 * PATTERN TEXTURE:
 * - Phase 1 (0-1s):   100ms intervals  → Rapid pulse (seeking peers)
 * - Phase 2 (1-5s):   500ms intervals  → Fast convergence
 * - Phase 3 (5-10s):  1000ms intervals → Settling
 * - Phase 4 (10-60s): 10000ms intervals → Stabilizing
 * - Phase 5 (60s+):   60000ms intervals → Steady state
 *
 * WHY THIS MATTERS:
 * An established device broadcasting at 60s intervals has a DIFFERENT TEXTURE
 * than a newborn device ramping through genesis. By comparing observed intervals
 * against this script, we can detect genesis vs established without trusting
 * the peer's claimed timestamps.
 *
 * SMSP ANALOGY:
 * Just as SMSP patterns define expected motor/LED behavior over time, this
 * defines expected beacon behavior. Deviation from script = anomaly.
 *==========================================================================*/

/**
 * @brief Genesis pattern step definition (SMSP-style)
 *
 * Each step defines: "From time T1 to T2, expect interval I (±tolerance)"
 */
typedef struct {
    uint32_t    start_ms;       /**< Step start time (ms since boot) */
    uint32_t    end_ms;         /**< Step end time (ms since boot) */
    uint32_t    interval_ms;    /**< Expected beacon interval */
    uint32_t    tolerance_ms;   /**< Acceptable deviation (±) */
} genesis_step_t;

/**
 * @brief The Genesis Pattern Script
 *
 * 5 phases of genesis, encoded as playable/comparable steps.
 * Use genesis_pattern_match() to compare observed intervals against this script.
 */
#define GENESIS_PATTERN_STEPS  5
static const genesis_step_t GENESIS_SCRIPT[GENESIS_PATTERN_STEPS] = {
    /* Phase 1: Rapid pulse (0-1s) - seeking peers */
    { .start_ms = 0,     .end_ms = 1000,   .interval_ms = 100,   .tolerance_ms = 50 },
    /* Phase 2: Fast convergence (1-5s) */
    { .start_ms = 1000,  .end_ms = 5000,   .interval_ms = 500,   .tolerance_ms = 200 },
    /* Phase 3: Settling (5-10s) */
    { .start_ms = 5000,  .end_ms = 10000,  .interval_ms = 1000,  .tolerance_ms = 300 },
    /* Phase 4: Stabilizing (10-60s) */
    { .start_ms = 10000, .end_ms = 60000,  .interval_ms = 10000, .tolerance_ms = 2000 },
    /* Phase 5: Steady state (60s+) */
    { .start_ms = 60000, .end_ms = UINT32_MAX, .interval_ms = 60000, .tolerance_ms = 5000 },
};

/**
 * @brief Genesis pattern detection thresholds
 *
 * These are derived from the script but provide quick classification.
 */
#define GENESIS_RAPID_INTERVAL_MS     200   /**< < 200ms = Phase 1 (rapid) */
#define GENESIS_FAST_INTERVAL_MS     1000   /**< < 1s = Phase 1-2 (genesis) */
#define GENESIS_SETTLING_INTERVAL_MS 2000   /**< < 2s = Phase 1-3 (young) */
#define STEADY_STATE_INTERVAL_MS    50000   /**< > 50s = Phase 5 (established) */

/*============================================================================
 * SEISMIC CHIRP STATE - Per-Peer Burst Tracking
 *
 * Track the 3-burst seismic chirp from each peer to extract:
 * - Time offset (burst 0)
 * - Jitter rate (burst 0→1 timing)
 * - Motion hint (burst 1→2 timing drift)
 *==========================================================================*/

/**
 * @defgroup vector_metrics Vector Peer Metrics (HDC-Ready)
 * @{
 *
 * "Scalar values show a moment; vectors show meaning over time."
 *
 * These history buffers enable:
 * 1. Outlier rejection via median filtering
 * 2. Trend detection (drift direction, jitter patterns)
 * 3. Future HDC encoding (each history becomes a hypervector dimension)
 * 4. Quality scoring based on distribution shape
 *
 * LEGACY SCALAR: Kept for human-readable logging (us/ms/s are intuitive).
 * PROTOCOL USE: Vector representations are primary for decision-making.
 */

/** @brief History depth for offset/jitter vectors */
#define UTLP_METRIC_HISTORY_SIZE    8

/**
 * @brief Offset history vector - tracks clock offset evolution
 *
 * Each element is a signed offset (our_time - peer_time) in microseconds.
 * Positive = we're ahead, Negative = we're behind.
 *
 * HDC Encoding (future): Encode as sparse binary vector where set bits
 * represent offset buckets. Similar offsets → similar hypervectors.
 */
typedef struct {
    int64_t     samples[UTLP_METRIC_HISTORY_SIZE];  /**< Ring buffer of offsets */
    uint8_t     write_idx;                          /**< Next write position */
    uint8_t     count;                              /**< Valid samples (0-8) */
    int64_t     median_us;                          /**< Median of samples (filtered) */
    int64_t     trend_us_per_s;                     /**< Drift rate (positive = diverging) */
} offset_history_t;

/**
 * @brief Jitter distribution vector - tracks timing variability
 *
 * Stores absolute jitter values (always positive).
 * Low variance = stable connection, high variance = unreliable.
 *
 * HDC Encoding (future): Thermometer encoding where jitter magnitude
 * sets bit count. Higher jitter → more bits set → orthogonal to low jitter.
 */
typedef struct {
    uint32_t    samples[UTLP_METRIC_HISTORY_SIZE];  /**< Ring buffer of |jitter| */
    uint8_t     write_idx;                          /**< Next write position */
    uint8_t     count;                              /**< Valid samples (0-8) */
    uint32_t    p50_us;                             /**< Median jitter */
    uint32_t    p90_us;                             /**< 90th percentile (worst-case) */
} jitter_distribution_t;

/**
 * @brief Beacon interval history vector - SWARM STATE SNAPSHOT
 *
 * "The interval between heartbeats tells you if a creature is calm or panicked."
 *
 * Tracks time between consecutive beacons from a peer. This vector is the
 * foundation of swarm state awareness - each peer's interval pattern reveals:
 *
 * GENESIS SIGNATURE (characteristic ramp):
 *   - Phase 1: ~100ms intervals (burst)
 *   - Phase 2: ~500ms intervals
 *   - Phase 3: ~1000ms intervals
 *   - Phase 4: ~10s intervals
 *   - Phase 5: ~60s intervals (steady state)
 *
 * ESTABLISHED SIGNATURE:
 *   - Consistent ~60s intervals (±jitter)
 *
 * DISTURBED SIGNATURE:
 *   - Erratic intervals (network issues, interference, motion)
 *
 * HDC Encoding (future): The interval vector can be encoded as a binary
 * hypervector where each interval maps to thermometer encoding. Similar
 * behavioral patterns → similar hypervectors → detectable via HD similarity.
 *
 * This enables:
 * - Genesis pulse detection (newcomer vs established)
 * - Swarm stability assessment (all peers steady?)
 * - Anomaly detection (sudden pattern change)
 * - Quality scoring (interval variance)
 */
typedef struct {
    /* === 8-byte aligned fields first === */
    uint64_t    last_beacon_us;                     /**< When last beacon received */

    /* === 4-byte aligned fields === */
    uint32_t    intervals_ms[UTLP_METRIC_HISTORY_SIZE]; /**< Ring buffer of intervals (ms) */
    uint32_t    median_ms;                          /**< Typical interval */
    uint32_t    min_ms;                             /**< Shortest recent interval */
    uint32_t    max_ms;                             /**< Longest recent interval */
    uint32_t    variance_ms;                        /**< Spread (stability indicator) */

    /* === 1-byte fields grouped (box truck packed) === */
    uint8_t     write_idx;                          /**< Next write position */
    uint8_t     count;                              /**< Valid intervals (0-8) */
    uint8_t     is_genesis_pattern;                 /**< True if intervals match genesis ramp */
    uint8_t     is_steady_pattern;                  /**< True if intervals are consistent ~60s */
    /* 4 bytes: no padding needed, naturally aligned to next 4-byte boundary */
} beacon_interval_history_t;

/**
 * @brief Chord history vector - tracks peer's time evolution
 *
 * Records peer's phase chord at each observation. Enables:
 * - Chord drift detection (are dimensions evolving consistently?)
 * - Spoofing detection (chord should evolve predictably)
 * - Partition recovery (find common chord subsequence)
 */
typedef struct {
    utlp_phase_chord_t  chords[UTLP_METRIC_HISTORY_SIZE]; /**< Ring buffer of chords */
    uint64_t            timestamps[UTLP_METRIC_HISTORY_SIZE]; /**< When observed (local) */
    uint8_t             write_idx;                  /**< Next write position */
    uint8_t             count;                      /**< Valid entries (0-8) */
} chord_history_t;

/** @} */ /* vector_metrics */

/**
 * @brief Chirp burst tracking for a single peer
 *
 * Tracks arrival times of the 3-burst seismic chirp to extract
 * offset, jitter, and motion information.
 *
 * SCALAR vs VECTOR:
 * - offset_us, jitter_*_us, motion_hint_us: Scalar (current measurement)
 * - offset_history, jitter_dist: Vector (trend over time)
 *
 * Control loops use the FILTERED (vector-derived) values.
 * Logging shows BOTH for debugging.
 */
typedef struct {
    uint64_t    chirp_epoch_us;         /**< Sender's timestamp (same for all 3 bursts) */
    uint64_t    rx_time_us[UTLP_CHIRP_BURST_COUNT]; /**< Local RX times for each burst */
    uint8_t     bursts_received;        /**< Bitmask of received bursts (0x01, 0x02, 0x04) */
    bool        chirp_complete;         /**< All 3 bursts received */

    /* === SCALAR: Current Measurement (for logging) === */
    int64_t     offset_us;              /**< Clock offset (our time - their time) */
    int64_t     jitter_01_us;           /**< Jitter: (rx1-rx0) - 2ms expected */
    int64_t     jitter_12_us;           /**< Jitter: (rx2-rx1) - 2ms expected */
    int64_t     motion_hint_us;         /**< Motion: jitter_12 - jitter_01 (acceleration) */

    /* === VECTOR: History for Filtering/HDC (for control) === */
    offset_history_t     offset_history;    /**< Offset trend over time */
    jitter_distribution_t jitter_dist;      /**< Jitter quality distribution */
} chirp_state_t;

/**
 * @brief Peer record for tracking known peers
 *
 * IDENTITY MODEL:
 * ---------------
 * A peer's identity for trust purposes is (MAC, session_salt), not MAC alone.
 *
 * - MAC alone: Hardware identity (same physical device)
 * - MAC + Salt: Session identity (same boot instance)
 *
 * When salt changes (peer rebooted):
 * 1. CONTACT_REBOOTED_PEER is returned by classify_contact()
 * 2. The peer is treated as NEW LIFE
 * 3. ALL accumulated state is wiped (chirp, welcome, future trust)
 * 4. Epoch resolution runs fresh (no inherited authority)
 *
 * This prevents:
 * - Stale measurements affecting new sessions
 * - Trust metrics persisting across reboots
 * - Old offset/jitter data corrupting new sync
 */
typedef struct {
    /* === Hardware Identity (MAC) - Stable Across Reboots === */
    uint8_t       mac[6];           /**< Peer's MAC address */

    /* === Session Identity (Salt) - Changes on Reboot === */
    uint8_t       session_salt[2];  /**< Last known session salt */

    /* === Epoch State (from beacon) === */
    uint32_t      origin_time;      /**< Last known origin_time */
    uint8_t       depth;            /**< Last known depth */
    uint64_t      last_seen_us;     /**< When last heard from peer */
    bool          is_known;         /**< Slot in use */

    /* === Per-Session Accumulated State (WIPED on salt change) === */
    chirp_state_t chirp;            /**< Seismic chirp burst tracking */

    /* Welcome Response tracking (genesis burst detection) */
    uint64_t      first_beacon_us;  /**< When we first heard from this peer */
    uint8_t       beacon_count;     /**< Beacons received in detection window */
    uint64_t      welcome_sent_us;  /**< When we last sent welcome (cooldown) */

    /* === VECTOR METRICS: Swarm State Snapshot === */
    chord_history_t           chord_history;     /**< Peer's chord over time */
    beacon_interval_history_t interval_history;  /**< Beacon timing pattern (SWARM STATE) */

    /* === Epoch Resolution State === */
    bool          epoch_resolved;   /**< True after epoch resolution complete */

    /* Future: trust metrics, reputation, arbor-specific RSSI, etc. */
} peer_record_t;

/*============================================================================
 * MODULE STATE
 *==========================================================================*/

static struct {
    uint8_t       local_mac[6];
    epoch_state_t epoch;            /**< Our epoch state */
    peer_record_t peers[UTLP_MAX_PEERS]; /**< Peer table */
    uint8_t       peer_count;       /**< Number of known peers */
    uint64_t      boot_time_us;     /**< Timestamp at boot (for genesis pulse calc) */
    uint8_t       current_genesis_phase; /**< 1-5 for logging, 5 = steady state */
    bool          initialized;

    /* Time synchronization state */
    int64_t       time_offset_us;   /**< Our time - peer time (positive = we're ahead) */
    bool          time_synced;      /**< True if we have a valid time offset */
    bool          we_adopted_epoch; /**< True if WE adopted peer's epoch (we adjust time) */
    uint32_t      sequence_id;      /**< TX sequence counter for beacons */

    /* === SELF-OBSERVATION: Our Own Beacon Texture ===
     *
     * Track our own beacon intervals for:
     * 1. Self-awareness: Know what texture we're broadcasting
     * 2. Pattern verification: Ensure we follow genesis script
     * 3. Debug visibility: Log our texture alongside peer textures
     * 4. Symmetry: Same analysis on self as on peers
     */
    beacon_interval_history_t self_interval;  /**< Our beacon timing pattern */
    uint64_t      last_tx_us;       /**< When we last transmitted (for self-interval calc) */
} s_utlp = {0};

/*============================================================================
 * VECTOR METRIC HELPERS - Update History Buffers
 *
 * "Scalar values show a moment; vectors show meaning over time."
 *
 * These functions update the ring buffers and compute derived statistics.
 * Integer-only math (no floats) for embedded efficiency.
 *==========================================================================*/

/**
 * @brief Simple integer median for small arrays (insertion sort approach)
 *
 * Works in-place on a copy. For 8 elements, O(n²) is acceptable.
 *
 * @param arr Array to find median of
 * @param count Number of valid elements (1-8)
 * @return Median value
 */
static int64_t compute_median_i64(const int64_t *arr, uint8_t count)
{
    if (count == 0) return 0;
    if (count == 1) return arr[0];

    /* Copy to temp array for sorting */
    int64_t temp[UTLP_METRIC_HISTORY_SIZE];
    for (uint8_t i = 0; i < count; i++) {
        temp[i] = arr[i];
    }

    /* Insertion sort (small array, O(n²) is fine) */
    for (uint8_t i = 1; i < count; i++) {
        int64_t key = temp[i];
        int8_t j = i - 1;
        while (j >= 0 && temp[j] > key) {
            temp[j + 1] = temp[j];
            j--;
        }
        temp[j + 1] = key;
    }

    /* Return median */
    if (count % 2 == 1) {
        return temp[count / 2];
    } else {
        return (temp[count / 2 - 1] + temp[count / 2]) / 2;
    }
}

/**
 * @brief Update offset history vector with new sample
 *
 * Adds new offset to ring buffer and updates derived statistics:
 * - median_us: Filtered offset (robust to outliers)
 * - trend_us_per_s: Rate of change (future: for drift compensation)
 *
 * @param history Offset history to update
 * @param offset_us New offset sample
 */
static void offset_history_update(offset_history_t *history, int64_t offset_us)
{
    if (!history) return;

    /* Add to ring buffer */
    history->samples[history->write_idx] = offset_us;
    history->write_idx = (history->write_idx + 1) % UTLP_METRIC_HISTORY_SIZE;
    if (history->count < UTLP_METRIC_HISTORY_SIZE) {
        history->count++;
    }

    /* Update median */
    history->median_us = compute_median_i64(history->samples, history->count);

    /* Compute trend (simple: newest - oldest, scaled to per-second)
     * More sophisticated: linear regression (future enhancement)
     */
    if (history->count >= 2) {
        /* Approximate: assume ~1 second between samples (adjustable) */
        uint8_t oldest_idx = (history->write_idx + UTLP_METRIC_HISTORY_SIZE - history->count)
                             % UTLP_METRIC_HISTORY_SIZE;
        uint8_t newest_idx = (history->write_idx + UTLP_METRIC_HISTORY_SIZE - 1)
                             % UTLP_METRIC_HISTORY_SIZE;
        history->trend_us_per_s = (history->samples[newest_idx] - history->samples[oldest_idx])
                                  / (int64_t)history->count;
    }
}

/**
 * @brief Update jitter distribution with new sample
 *
 * Tracks jitter magnitude (absolute value) to build quality picture:
 * - p50_us: Typical jitter (median)
 * - p90_us: Worst-case jitter (for timeout calculations)
 *
 * @param dist Jitter distribution to update
 * @param jitter_us Raw jitter (can be negative)
 */
static void jitter_dist_update(jitter_distribution_t *dist, int64_t jitter_us)
{
    if (!dist) return;

    /* Store absolute value */
    uint32_t abs_jitter = (jitter_us >= 0) ? (uint32_t)jitter_us
                                           : (uint32_t)(-jitter_us);

    /* Add to ring buffer */
    dist->samples[dist->write_idx] = abs_jitter;
    dist->write_idx = (dist->write_idx + 1) % UTLP_METRIC_HISTORY_SIZE;
    if (dist->count < UTLP_METRIC_HISTORY_SIZE) {
        dist->count++;
    }

    /* Sort samples to find percentiles */
    uint32_t sorted[UTLP_METRIC_HISTORY_SIZE];
    for (uint8_t i = 0; i < dist->count; i++) {
        sorted[i] = dist->samples[i];
    }

    /* Insertion sort */
    for (uint8_t i = 1; i < dist->count; i++) {
        uint32_t key = sorted[i];
        int8_t j = i - 1;
        while (j >= 0 && sorted[j] > key) {
            sorted[j + 1] = sorted[j];
            j--;
        }
        sorted[j + 1] = key;
    }

    /* p50 = median */
    dist->p50_us = sorted[dist->count / 2];

    /* p90 = 90th percentile (index = count * 0.9) */
    uint8_t p90_idx = (dist->count * 9) / 10;
    if (p90_idx >= dist->count) p90_idx = dist->count - 1;
    dist->p90_us = sorted[p90_idx];
}

/**
 * @brief Record peer's chord observation
 *
 * Adds chord to history for:
 * - Spoofing detection (chord should evolve predictably)
 * - Partition recovery (find common subsequence)
 * - Future HDC encoding
 *
 * @param history Chord history to update
 * @param chord Peer's current phase chord
 * @param timestamp_us Local time of observation
 */
static void chord_history_record(chord_history_t *history,
                                  const utlp_phase_chord_t chord,
                                  uint64_t timestamp_us)
{
    if (!history || !chord) return;

    /* Copy chord to ring buffer */
    memcpy(history->chords[history->write_idx], chord, sizeof(utlp_phase_chord_t));
    history->timestamps[history->write_idx] = timestamp_us;

    history->write_idx = (history->write_idx + 1) % UTLP_METRIC_HISTORY_SIZE;
    if (history->count < UTLP_METRIC_HISTORY_SIZE) {
        history->count++;
    }
}

/**
 * @brief Update beacon interval history - SWARM STATE TRACKING
 *
 * "The heartbeat between messages reveals if a peer is calm or panicked."
 *
 * Records the interval since the last beacon from this peer and classifies
 * the pattern. This is the foundation of swarm state awareness.
 *
 * GENESIS DETECTION THRESHOLDS:
 *   - Any interval < 2000ms = genesis pulsing (steady state is 60s)
 *   - Ramp pattern: intervals INCREASING = genesis chirp signature
 *   - Steady pattern: intervals ~60s ± small variance
 *
 * @param history Interval history to update
 * @param rx_time_us Current beacon reception time
 */
static void beacon_interval_update(beacon_interval_history_t *history, uint64_t rx_time_us)
{
    if (!history) return;

    /* First beacon - just record time, no interval yet */
    if (history->last_beacon_us == 0) {
        history->last_beacon_us = rx_time_us;
        return;
    }

    /* Calculate interval since last beacon (in ms for reasonable storage) */
    uint64_t interval_us = rx_time_us - history->last_beacon_us;
    uint32_t interval_ms = (uint32_t)(interval_us / 1000);
    history->last_beacon_us = rx_time_us;

    /* Add to ring buffer */
    history->intervals_ms[history->write_idx] = interval_ms;
    history->write_idx = (history->write_idx + 1) % UTLP_METRIC_HISTORY_SIZE;
    if (history->count < UTLP_METRIC_HISTORY_SIZE) {
        history->count++;
    }

    /* Sort samples for statistics */
    uint32_t sorted[UTLP_METRIC_HISTORY_SIZE];
    for (uint8_t i = 0; i < history->count; i++) {
        sorted[i] = history->intervals_ms[i];
    }

    /* Insertion sort */
    for (uint8_t i = 1; i < history->count; i++) {
        uint32_t key = sorted[i];
        int8_t j = i - 1;
        while (j >= 0 && sorted[j] > key) {
            sorted[j + 1] = sorted[j];
            j--;
        }
        sorted[j + 1] = key;
    }

    /* Compute statistics */
    history->min_ms = sorted[0];
    history->max_ms = sorted[history->count - 1];
    history->median_ms = sorted[history->count / 2];
    history->variance_ms = history->max_ms - history->min_ms;

    /*
     * PATTERN CLASSIFICATION (using constants from GENESIS_SCRIPT)
     *
     * Genesis signature: ANY interval < 2s (matches Phase 1-3)
     * Steady signature: ALL intervals > 50s with low variance (matches Phase 5)
     *
     * See GENESIS_SCRIPT for the full pattern definition.
     */
    #define STEADY_VARIANCE_MAX_MS         10000   /* < 10s variance = stable */

    /* Check for genesis pattern (any short interval) */
    history->is_genesis_pattern = (history->min_ms < GENESIS_SETTLING_INTERVAL_MS);

    /* Check for steady pattern (all long intervals, low variance) */
    history->is_steady_pattern = (history->min_ms > STEADY_STATE_INTERVAL_MS) &&
                                  (history->variance_ms < STEADY_VARIANCE_MAX_MS);
}

/**
 * @brief Match observed interval against GENESIS_SCRIPT pattern
 *
 * SMSP-style pattern matching: Given an observed interval, determine which
 * phase of the genesis script it matches (or if it doesn't match any).
 *
 * This enables:
 * - "Where in genesis is this peer?" (not just "is it genesis pulsing?")
 * - Anomaly detection (interval doesn't match any expected phase)
 * - Age estimation (phase → approximate uptime)
 *
 * @param interval_ms Observed beacon interval in milliseconds
 * @return Phase number (1-5) if interval matches, 0 if no match (anomaly)
 */
static uint8_t genesis_pattern_match(uint32_t interval_ms)
{
    for (uint8_t phase = 0; phase < GENESIS_PATTERN_STEPS; phase++) {
        const genesis_step_t *step = &GENESIS_SCRIPT[phase];

        /* Check if interval is within expected range for this phase */
        int32_t deviation = (int32_t)interval_ms - (int32_t)step->interval_ms;
        if (deviation < 0) deviation = -deviation;  /* abs() */

        if ((uint32_t)deviation <= step->tolerance_ms) {
            return phase + 1;  /* 1-indexed phase number */
        }
    }

    /* No match - interval doesn't fit any expected pattern */
    return 0;
}

/**
 * @brief Estimate peer age from genesis pattern phase
 *
 * Given a phase match from genesis_pattern_match(), estimate the peer's
 * approximate uptime range.
 *
 * @param phase Phase number from genesis_pattern_match() (1-5)
 * @param out_min_ms Output: minimum estimated age in ms
 * @param out_max_ms Output: maximum estimated age in ms
 */
static void genesis_phase_to_age(uint8_t phase, uint32_t *out_min_ms, uint32_t *out_max_ms)
{
    if (phase == 0 || phase > GENESIS_PATTERN_STEPS) {
        /* Invalid phase - unknown age */
        if (out_min_ms) *out_min_ms = 0;
        if (out_max_ms) *out_max_ms = UINT32_MAX;
        return;
    }

    const genesis_step_t *step = &GENESIS_SCRIPT[phase - 1];  /* 0-indexed */
    if (out_min_ms) *out_min_ms = step->start_ms;
    if (out_max_ms) *out_max_ms = step->end_ms;
}

/*============================================================================
 * GENESIS CHIRP - Mathematically Identifiable Birth Signal
 *
 * "Like the Cosmic Microwave Background reveals the Big Bang's age,
 * the Genesis Chirp pattern reveals how recently a device booted."
 *
 * PATTERN: Linear Frequency Sweep
 *   interval(t) = CHIRP_BASE_US + (t_seconds × CHIRP_SLOPE_US)
 *
 * Timeline (with default constants):
 *   t=0.0s: interval = 50ms    (20 beacons/sec)
 *   t=1.0s: interval = 150ms   (6.7 beacons/sec)
 *   t=5.0s: interval = 550ms   (1.8 beacons/sec)
 *   t=10s:  interval = 1050ms  → switch to 60s steady state
 *
 * Detection: Any observer can identify a genesis chirp by measuring
 * the slope of interval changes. If slope ≈ CHIRP_SLOPE_US, it's a
 * newborn device.
 *==========================================================================*/

/**
 * @brief Calculate current beacon interval using linear chirp formula
 *
 * Formula: interval = CHIRP_BASE_US + (uptime_seconds × CHIRP_SLOPE_US)
 *
 * This creates a mathematically identifiable "birth signature" that any
 * observer can detect by measuring the slope of interval changes.
 *
 * @param uptime_us Microseconds since boot
 * @param[out] out_is_chirping true if still in chirp phase, false if steady
 * @return Beacon interval in microseconds
 */
static uint64_t get_genesis_chirp_interval_us(uint64_t uptime_us, bool *out_is_chirping)
{
    if (uptime_us < UTLP_CHIRP_DURATION_US) {
        /* Still in genesis chirp phase - use linear formula */
        uint32_t uptime_s = (uint32_t)(uptime_us / 1000000ULL);
        uint64_t interval = UTLP_CHIRP_BASE_US + (uptime_s * UTLP_CHIRP_SLOPE_US);

        if (out_is_chirping) *out_is_chirping = true;
        return interval;
    }
    else {
        /* Chirp complete - steady state */
        if (out_is_chirping) *out_is_chirping = false;
        return UTLP_BEACON_STEADY_US;
    }
}

/**
 * @brief Estimate peer's age from observed beacon interval
 *
 * Inverse of the chirp formula:
 *   age_seconds = (observed_interval - CHIRP_BASE_US) / CHIRP_SLOPE_US
 *
 * @param observed_interval_us Peer's beacon interval in microseconds
 * @return Estimated age in seconds (0 if interval below base)
 */
static uint32_t estimate_peer_age_from_interval(uint64_t observed_interval_us)
{
    if (observed_interval_us <= UTLP_CHIRP_BASE_US) {
        return 0;
    }

    /* Invert the chirp formula: t = (interval - base) / slope */
    return (uint32_t)((observed_interval_us - UTLP_CHIRP_BASE_US) / UTLP_CHIRP_SLOPE_US);
}

/**
 * @brief Check if observed interval slope matches genesis chirp signature
 *
 * Genesis chirp detection algorithm:
 *   1. Need at least 2 beacon observations
 *   2. Measure interval between consecutive beacons
 *   3. Compute slope = (interval_2 - interval_1) / time_delta
 *   4. If slope ≈ CHIRP_SLOPE_US (within tolerance), it's a genesis chirp
 *
 * @param interval_1_us First observed beacon interval
 * @param interval_2_us Second observed beacon interval
 * @param time_delta_us Time between the two observations
 * @return true if slope matches genesis chirp signature
 */
static bool detect_genesis_chirp(uint64_t interval_1_us, uint64_t interval_2_us,
                                  uint64_t time_delta_us)
{
    if (time_delta_us < 100000) {  /* Need at least 100ms between observations */
        return false;
    }

    /* Calculate observed slope (us increase per second) */
    int64_t interval_delta = (int64_t)interval_2_us - (int64_t)interval_1_us;
    int64_t time_delta_s = (int64_t)(time_delta_us / 1000000ULL);
    if (time_delta_s == 0) time_delta_s = 1;  /* Avoid division by zero */

    int64_t observed_slope = (interval_delta * 1000000LL) / (int64_t)time_delta_us;

    /* Expected slope from constants */
    int64_t expected_slope = UTLP_CHIRP_SLOPE_US;
    int64_t tolerance = (expected_slope * UTLP_CHIRP_SLOPE_TOLERANCE_PCT) / 100;

    /* Check if observed slope matches expected (within tolerance) */
    bool matches = (observed_slope >= (expected_slope - tolerance)) &&
                   (observed_slope <= (expected_slope + tolerance));

    return matches;
}

/**
 * @brief Check if a peer is in genesis chirp phase (simple age check)
 *
 * Quick check based on peer's atomic time from beacon.
 * For more sophisticated detection, use detect_genesis_chirp() with
 * multiple beacon observations.
 *
 * @param peer_atomic_time_us Peer's atomic time from beacon
 * @return true if peer is likely in genesis chirp phase
 */
static bool is_genesis_chirping(uint64_t peer_atomic_time_us)
{
    /* Peer running less than CHIRP_DURATION = still in genesis chirp */
    return (peer_atomic_time_us < UTLP_CHIRP_DURATION_US);
}

/*============================================================================
 * PHASE 2: PEER TABLE OPERATIONS
 *==========================================================================*/

/**
 * @brief Find peer record by MAC address
 *
 * @param mac 6-byte MAC address to find
 * @return Pointer to peer record, or NULL if not found
 */
static peer_record_t* find_peer_by_mac(const uint8_t *mac)
{
    if (!mac) {
        return NULL;
    }

    for (int i = 0; i < UTLP_MAX_PEERS; i++) {
        if (s_utlp.peers[i].is_known &&
            memcmp(s_utlp.peers[i].mac, mac, 6) == 0) {
            return &s_utlp.peers[i];
        }
    }
    return NULL;
}

/**
 * @brief Classify contact type based on MAC and session salt
 *
 * Uses the (MAC, session_salt) tuple to determine peer identity:
 *
 * | MAC Known? | Salt Match? | Result             | Action                    |
 * |------------|-------------|--------------------| --------------------------|
 * | No         | N/A         | CONTACT_NEW_PEER   | First contact, resolve    |
 * | Yes        | Yes         | CONTACT_KNOWN_PEER | Same session, update time |
 * | Yes        | No          | CONTACT_REBOOTED   | New session, wipe & reset |
 *
 * CONTACT_REBOOTED_PEER triggers full state reset because the peer lost
 * all volatile state. Trust, measurements, and sync data must NOT persist.
 *
 * @param mac Peer's MAC address (hardware identity)
 * @param salt Peer's session salt (2 bytes, session identity)
 * @return Contact type classification
 */
static contact_type_t classify_contact(const uint8_t *mac, const uint8_t *salt)
{
    peer_record_t *peer = find_peer_by_mac(mac);

    if (peer == NULL) {
        return CONTACT_NEW_PEER;
    }

    if (memcmp(peer->session_salt, salt, 2) == 0) {
        return CONTACT_KNOWN_PEER;
    }

    return CONTACT_REBOOTED_PEER;
}

/**
 * @brief Register or update a peer in the peer table
 *
 * IDENTITY MODEL - MAC vs MAC+Salt:
 *
 * - **MAC alone**: Used to find the hardware device's slot in memory.
 *   The physical device keeps the same slot even across reboots.
 *
 * - **MAC + Salt**: The LOGICAL identity for trust purposes. A change
 *   in salt indicates reboot - the device lost all volatile state and
 *   must NOT inherit trust metrics from its previous incarnation.
 *
 * When a peer reboots (same MAC, different salt):
 * 1. CONTACT_REBOOTED_PEER is detected via classify_contact()
 * 2. invalidate_peer() marks the slot empty
 * 3. This function is called with the new epoch
 * 4. We MUST zero ALL accumulated state before populating
 *
 * This ensures chirp measurements, welcome tracking, and future trust
 * metrics are NEVER inherited across reboots.
 *
 * @param mac Peer's MAC address (hardware identity)
 * @param epoch Peer's epoch state (includes session_salt)
 * @return Pointer to peer record, or NULL if table full
 */
static peer_record_t* register_peer(const uint8_t *mac, const epoch_state_t *epoch)
{
    if (!mac || !epoch) {
        return NULL;
    }

    /* Find existing or empty slot */
    peer_record_t *slot = find_peer_by_mac(mac);
    if (slot == NULL) {
        /* Find empty slot */
        for (int i = 0; i < UTLP_MAX_PEERS; i++) {
            if (!s_utlp.peers[i].is_known) {
                slot = &s_utlp.peers[i];
                s_utlp.peer_count++;
                break;
            }
        }
    }

    if (slot == NULL) {
        utlp_hal_log_warn(TAG, "Peer table full!");
        return NULL;
    }

    /*
     * CRITICAL: Zero the ENTIRE slot before populating!
     *
     * This ensures NO state is inherited from previous sessions:
     * - chirp: offset_us, jitter, motion_hint, bursts_received
     * - welcome: first_beacon_us, beacon_count, welcome_sent_us
     * - future: trust metrics, reputation scores
     *
     * A rebooted peer is NEW LIFE - treat it as such.
     */
    memset(slot, 0, sizeof(peer_record_t));

    /* Populate with new session data */
    memcpy(slot->mac, mac, 6);
    memcpy(slot->session_salt, epoch->session_salt, 2);
    slot->origin_time = epoch->origin_time;
    slot->depth = epoch->depth;
    slot->last_seen_us = utlp_hal_get_micros();
    slot->is_known = true;

    return slot;
}

/**
 * @brief Invalidate a peer record (e.g., after reboot detection)
 *
 * @param mac Peer's MAC address
 */
static void invalidate_peer(const uint8_t *mac)
{
    peer_record_t *peer = find_peer_by_mac(mac);
    if (peer) {
        peer->is_known = false;
        s_utlp.peer_count--;
        utlp_hal_log_info(TAG, "Peer invalidated: %02X:%02X:%02X:%02X:%02X:%02X",
                          mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
    }
}

/*============================================================================
 * PHASE 2: EPOCH RESOLUTION (Stem Cell Model)
 *
 * "Higher depth (more vitality) wins."
 *
 * Resolution Rules:
 * 1. Higher depth wins (stem cell model - more telomeres = more vitality)
 * 2. Equal depth → older origin_time wins (temporal precedence)
 * 3. True tie → lower MAC adopts from higher MAC
 *
 * On adoption, depth DECREMENTS (telomere shortening).
 *==========================================================================*/

/**
 * @brief Adopt epoch from a peer (telomere shortening)
 *
 * @param source Epoch to adopt from
 */
static void adopt_epoch(const epoch_state_t *source)
{
    uint32_t old_origin = s_utlp.epoch.origin_time;
    uint8_t old_depth = s_utlp.epoch.depth;

    /* Adopt origin time */
    s_utlp.epoch.origin_time = source->origin_time;

    /* Decrement depth (telomere shortening) with saturation */
    if (source->depth > UTLP_DEPTH_EXHAUSTED) {
        s_utlp.epoch.depth = source->depth - 1;
    } else {
        s_utlp.epoch.depth = UTLP_DEPTH_EXHAUSTED;
    }

    /* Note: session_salt unchanged - we did not reboot */

    utlp_hal_log_info(TAG, "ADOPT: origin %lu→%lu, depth %u→%u",
                      (unsigned long)old_origin,
                      (unsigned long)s_utlp.epoch.origin_time,
                      old_depth, s_utlp.epoch.depth);
}

/*============================================================================
 * PHASE 2: WELCOME RESPONSE (Genesis Burst Detection)
 *
 * "When an established device hears a genesis pulse, it says 'Hello!'"
 *
 * When we receive a beacon from a NEW peer (genesis pulsing), and we are
 * an ESTABLISHED device (past our own genesis chirp), we send an immediate
 * out-of-schedule beacon so the newborn doesn't wait for our 60s steady rate.
 *==========================================================================*/

/* Forward declaration - send_beacon is defined later but needed for welcome response */
static void send_beacon(void);

/**
 * @brief Check if we should send a welcome response to a new peer
 *
 * Conditions:
 * 1. WE are established (past our own genesis chirp phase)
 * 2. PEER is genesis pulsing (rapid beacons within detection window)
 * 3. Cooldown has expired (prevent spam)
 *
 * @param peer Peer record to check
 * @param rx_time_us Current reception timestamp
 * @return true if we should send welcome response
 */
static bool should_send_welcome_response(peer_record_t *peer, uint64_t rx_time_us)
{
    /* Condition 1: Are WE established? (past genesis chirp) */
    uint64_t our_uptime_us = rx_time_us - s_utlp.boot_time_us;
    if (our_uptime_us < UTLP_WELCOME_MIN_UPTIME_US) {
        /* We're still genesis pulsing ourselves - don't send welcome */
        return false;
    }

    /* Condition 2: Is this peer genesis pulsing? (rapid beacon rate) */
    if (peer->first_beacon_us == 0) {
        /* First beacon from this peer - start tracking */
        peer->first_beacon_us = rx_time_us;
        peer->beacon_count = 1;
        return false;  /* Need at least THRESHOLD_BEACONS to detect pattern */
    }

    uint64_t window_elapsed = rx_time_us - peer->first_beacon_us;

    if (window_elapsed <= UTLP_WELCOME_THRESHOLD_WINDOW_US) {
        /* Still within detection window - count beacon */
        peer->beacon_count++;

        if (peer->beacon_count >= UTLP_WELCOME_THRESHOLD_BEACONS) {
            /* Detected genesis burst pattern! Check cooldown. */

            /* Condition 3: Cooldown expired? */
            if (peer->welcome_sent_us > 0) {
                uint64_t since_welcome = rx_time_us - peer->welcome_sent_us;
                if (since_welcome < UTLP_WELCOME_COOLDOWN_US) {
                    /* Recently sent welcome - skip (rate limiting) */
                    return false;
                }
            }

            /* All conditions met - send welcome! */
            return true;
        }
    } else {
        /* Window expired - reset detection */
        peer->first_beacon_us = rx_time_us;
        peer->beacon_count = 1;
    }

    return false;
}

/**
 * @brief Send welcome response to a new peer
 *
 * Sends an immediate out-of-schedule beacon after a small jitter delay.
 * Uses MAC-based jitter to prevent synchronized floods from multiple devices.
 *
 * @param peer Peer record to update
 * @param rx_time_us Current reception timestamp
 */
static void send_welcome_response(peer_record_t *peer, uint64_t rx_time_us)
{
    /* Add MAC-based jitter to prevent synchronized welcome floods */
    uint32_t jitter_us = UTLP_WELCOME_RESPONSE_DELAY_US;
    jitter_us += (s_utlp.local_mac[5] & 0x0F) * 1000;  /* 0-15ms extra jitter */

    utlp_hal_log_info(TAG, "WELCOME RESPONSE: Sending beacon to new peer (jitter=%lu us)",
                      (unsigned long)jitter_us);

    /* Small delay before responding */
    utlp_hal_delay_us(jitter_us);

    /* Send our beacon (full seismic chirp) */
    send_beacon();

    /* Mark welcome sent for cooldown */
    peer->welcome_sent_us = rx_time_us;

    /* Reset detection counters */
    peer->beacon_count = 0;
    peer->first_beacon_us = 0;
}

/**
 * @brief Handle first contact with a peer (new or rebooted)
 *
 * Implements stem cell epoch resolution:
 * 1. Higher depth (more vitality) wins
 * 2. Equal depth → oldest origin_time wins
 * 3. True tie → lower MAC adopts from higher MAC
 *
 * @param peer_mac Peer's MAC address
 * @param peer_epoch Peer's epoch state
 * @param peer_chord Peer's phase chord (for verification)
 */
static void handle_first_contact(const uint8_t *peer_mac,
                                  const epoch_state_t *peer_epoch,
                                  const utlp_phase_chord_t peer_chord)
{
    utlp_hal_log_info(TAG, "First contact: MAC=%02X:%02X:%02X:%02X:%02X:%02X",
                      peer_mac[0], peer_mac[1], peer_mac[2],
                      peer_mac[3], peer_mac[4], peer_mac[5]);
    utlp_hal_log_info(TAG, "  Peer: origin=%lu, depth=%u, salt=%02X%02X",
                      (unsigned long)peer_epoch->origin_time,
                      peer_epoch->depth,
                      peer_epoch->session_salt[1], peer_epoch->session_salt[0]);
    utlp_hal_log_info(TAG, "  Self: origin=%lu, depth=%u, salt=%02X%02X",
                      (unsigned long)s_utlp.epoch.origin_time,
                      s_utlp.epoch.depth,
                      s_utlp.epoch.session_salt[1], s_utlp.epoch.session_salt[0]);

    /* Defense Layer 1: Chord-Origin Verification */
    if (!utlp_phase_chord_origin_verify(peer_chord,
                                        peer_epoch->origin_time,
                                        s_utlp.epoch.origin_time)) {
        utlp_hal_log_warn(TAG, "REJECT: Chord-origin verification failed");
        return;
    }

    /*
     * EPOCH RESOLUTION DEFERRED
     *
     * We used to resolve epoch here using origin_time comparison, but that
     * was comparing values in different clock domains (my uptime vs peer's
     * uptime). A fresh device with origin=0 would incorrectly beat older
     * devices with higher origin values.
     *
     * Now we defer resolution until after the seismic chirp completes,
     * giving us a valid clock offset. The offset tells us who booted first:
     * - offset > 0: Our clock is ahead → we're older
     * - offset < 0: Peer's clock is ahead → peer is older
     *
     * See resolve_epoch_with_offset() called from process_chirp_burst().
     */

    /* Register peer - epoch resolution happens after chirp complete */
    peer_record_t *peer = register_peer(peer_mac, peer_epoch);
    if (peer) {
        peer->epoch_resolved = false;  /* Will resolve when we have offset */
        utlp_hal_log_info(TAG, "Peer registered - awaiting chirp for epoch resolution");
    }
}

/**
 * @brief Resolve epoch using clock offset (called after chirp complete)
 *
 * Uses the offset from seismic chirp to determine who is older:
 * - offset > 0: Our clock is ahead → we started first → we're older
 * - offset < 0: Peer's clock is ahead → peer started first → peer is older
 *
 * This replaces the broken origin_time comparison which compared values
 * from different clock domains.
 *
 * @param peer Peer record with valid chirp offset
 */
static void resolve_epoch_with_offset(peer_record_t *peer)
{
    if (!peer || peer->epoch_resolved) {
        return;  /* Already resolved or invalid */
    }

    bool i_should_adopt = false;
    int64_t offset_us = peer->chirp.offset_us;

    utlp_hal_log_info(TAG, "Epoch resolution using offset: %lld us",
                      (long long)offset_us);
    utlp_hal_log_info(TAG, "  Peer depth=%u, Self depth=%u",
                      peer->depth, s_utlp.epoch.depth);

    /* Build epoch for logging */
    epoch_state_t peer_epoch;
    peer_epoch.origin_time = peer->origin_time;
    peer_epoch.depth = peer->depth;
    memcpy(peer_epoch.session_salt, peer->session_salt, 2);

    /*
     * === N=2 EPOCH RESOLUTION (GENESIS-PROTECTED, OFFSET-FIRST MODEL) ===
     *
     * For N=2 without Byzantine detection, we CANNOT trust depth claims.
     * A rebooted device claims depth=128 (fresh) but that doesn't mean
     * it should dominate an established device running for hours.
     *
     * Resolution Rules (in order):
     * 0. GENESIS PROTECTION: Established device NEVER adopts from genesis-pulsing peer
     * 1. TIME LORD (255) always wins - earned through service
     * 2. NON-TIME-LORDS: Use OFFSET to determine who is older
     * 3. DEPTH tiebreaker if offset inconclusive (devices born same second)
     * 4. MAC tiebreaker as last resort
     *
     * User requirement: "We should know better to blindly accept a Genesis
     * Pulse as a real value unless both devices are born within the same second."
     *
     * Genesis protection ensures that when device C joins established A+B swarm,
     * C is PULLED INTO SYNC with A+B rather than disrupting their sync.
     */

    /* OFFSET THRESHOLD for determining "same second" */
    #define EPOCH_OFFSET_THRESHOLD_US  1000000  /* 1 second */

    /*
     * === RULE 0: GENESIS PULSE PROTECTION (INNATE IMMUNITY) ===
     *
     * "An established swarm recognizes and absorbs newcomers, not vice versa."
     *
     * If WE are established AND peer is genesis pulsing, we NEVER adopt.
     * The newborn must sync to the established swarm.
     *
     * DETECTION STRATEGY (VECTOR-BASED SWARM STATE):
     *
     * PRIMARY: Use interval_history.is_genesis_pattern (observed beacon intervals)
     *   - Requires multiple beacons → more reliable
     *   - Detects genesis ramp signature (100ms → 500ms → 1s intervals)
     *   - Cannot be faked by manipulating TX timestamp
     *
     * FALLBACK: Use is_genesis_chirping(TX timestamp) for early/sparse observations
     *   - Works on first contact (before interval history builds)
     *   - Peer claims "I've been running X microseconds"
     *   - Can be spoofed but combined with interval pattern is robust
     *
     * BOTH MUST AGREE for established detection (conservative approach):
     *   - We consider ourselves established ONLY if uptime > 5s
     *   - We consider peer genesis pulsing if EITHER vector OR timestamp indicates
     */
    uint64_t our_uptime_us = utlp_hal_get_micros() - s_utlp.boot_time_us;
    bool we_are_established = (our_uptime_us >= UTLP_CHIRP_DURATION_US);

    /* Vector-based detection (observed behavior - cannot be faked) */
    bool peer_genesis_by_vector = peer->interval_history.is_genesis_pattern;

    /* Timestamp-based detection (peer's claim - can be faked but useful early) */
    bool peer_genesis_by_timestamp = is_genesis_chirping(peer->chirp.chirp_epoch_us);

    /* EITHER method indicates genesis = protective (conservative) */
    bool peer_is_genesis_pulsing = peer_genesis_by_vector || peer_genesis_by_timestamp;

    utlp_hal_log_info(TAG, "  We established=%s (uptime=%llu us)",
                      we_are_established ? "YES" : "NO",
                      (unsigned long long)our_uptime_us);

    /* Use SMSP-style pattern matching to identify peer's genesis phase */
    uint8_t peer_phase = genesis_pattern_match(peer->interval_history.median_ms);
    uint32_t peer_age_min_ms, peer_age_max_ms;
    genesis_phase_to_age(peer_phase, &peer_age_min_ms, &peer_age_max_ms);

    utlp_hal_log_info(TAG, "  Peer genesis: vector=%s (min=%lu ms, median=%lu ms)",
                      peer_genesis_by_vector ? "YES" : "NO",
                      (unsigned long)peer->interval_history.min_ms,
                      (unsigned long)peer->interval_history.median_ms);
    utlp_hal_log_info(TAG, "  Peer pattern: phase=%u (%lu-%lu ms uptime), timestamp=%s (tx=%llu us)",
                      peer_phase,
                      (unsigned long)peer_age_min_ms,
                      (unsigned long)peer_age_max_ms,
                      peer_genesis_by_timestamp ? "YES" : "NO",
                      (unsigned long long)peer->chirp.chirp_epoch_us);

    if (we_are_established && peer_is_genesis_pulsing) {
        /*
         * GENESIS PROTECTION TRIGGERED
         *
         * We are established, peer just booted (detected via interval vector
         * and/or TX timestamp). We keep our epoch.
         *
         * This protects existing N=2 sync when a 3rd device joins:
         * - A & B are synced (established)
         * - C boots (genesis pulsing)
         * - A meets C: A is established, C is genesis → A keeps epoch
         * - B meets C: B is established, C is genesis → B keeps epoch
         * - C adopts from both A and B → swarm stable
         */
        utlp_hal_log_info(TAG, "RESOLUTION: GENESIS PROTECTION - we are established, peer is newborn");
        utlp_hal_log_info(TAG, "  → We keep epoch, peer must sync to us");
        s_utlp.we_adopted_epoch = false;
        peer->epoch_resolved = true;
        return;  /* Early exit - no further checks needed */
    }

    /* Rule 1: Time Lord check - only Time Lords get special treatment */
    bool peer_is_time_lord = (peer->depth == UTLP_DEPTH_TIME_LORD);
    bool we_are_time_lord = (s_utlp.epoch.depth == UTLP_DEPTH_TIME_LORD);

    if (peer_is_time_lord && !we_are_time_lord) {
        /* Peer is Time Lord, we are not → adopt */
        i_should_adopt = true;
        utlp_hal_log_info(TAG, "RESOLUTION: Peer is Time Lord (255), we adopt");
    }
    else if (we_are_time_lord && !peer_is_time_lord) {
        /* We are Time Lord, peer is not → keep ours */
        utlp_hal_log_info(TAG, "RESOLUTION: We are Time Lord (255), we keep epoch");
    }
    else {
        /*
         * Rule 2: Both Time Lords OR both non-Time-Lords
         * Use OFFSET to determine who is older (who booted first).
         *
         * offset = my_rx_time - peer_tx_time
         *
         * If offset > 0: My clock is ahead → I've been running longer → I'm older
         * If offset < 0: Peer's clock is ahead → Peer booted first → Peer is older
         */
        if (offset_us < -EPOCH_OFFSET_THRESHOLD_US) {
            /* Peer is significantly older - their clock is ahead */
            i_should_adopt = true;
            utlp_hal_log_info(TAG, "RESOLUTION: Peer is older (offset=%lld us, older wins)",
                              (long long)offset_us);
        }
        else if (offset_us > EPOCH_OFFSET_THRESHOLD_US) {
            /* We are significantly older - our clock is ahead */
            utlp_hal_log_info(TAG, "RESOLUTION: We are older (offset=%lld us, we keep epoch)",
                              (long long)offset_us);
        }
        else {
            /*
             * Rule 3: Both devices born within ~1 second (genesis race)
             * Only NOW do we consider depth as tiebreaker.
             *
             * This prevents fresh reboots (128) from beating established
             * devices (127) unless they JUST booted together.
             */
            utlp_hal_log_info(TAG, "RESOLUTION: Devices born same second (offset=%lld us)",
                              (long long)offset_us);

            if (peer->depth > s_utlp.epoch.depth) {
                i_should_adopt = true;
                utlp_hal_log_info(TAG, "  Depth tiebreaker: peer wins (%u > %u)",
                                  peer->depth, s_utlp.epoch.depth);
            }
            else if (peer->depth < s_utlp.epoch.depth) {
                utlp_hal_log_info(TAG, "  Depth tiebreaker: we win (%u > %u)",
                                  s_utlp.epoch.depth, peer->depth);
            }
            else {
                /* Rule 4: MAC tiebreaker as absolute last resort */
                if (memcmp(s_utlp.local_mac, peer->mac, 6) < 0) {
                    i_should_adopt = true;
                    utlp_hal_log_info(TAG, "  MAC tiebreaker: lower MAC adopts");
                } else {
                    utlp_hal_log_info(TAG, "  MAC tiebreaker: higher MAC keeps epoch");
                }
            }
        }
    }

    /* Execute adoption if needed */
    if (i_should_adopt) {
        adopt_epoch(&peer_epoch);
        s_utlp.we_adopted_epoch = true;  /* We adjust our time to match peer */
        utlp_hal_log_info(TAG, "We adopted → will sync our LED to peer's time");
    } else {
        s_utlp.we_adopted_epoch = false;  /* We keep our time, peer adjusts */
        utlp_hal_log_info(TAG, "We kept epoch → peer will sync to our time");
    }

    peer->epoch_resolved = true;
}

/**
 * @brief Process a single burst from a seismic chirp
 *
 * Tracks burst arrivals and calculates time offset/jitter when complete.
 *
 * @param peer Peer record to update
 * @param wire_pkt The received wire packet
 * @param rx_time_us Local time when packet was received
 */
static void process_chirp_burst(peer_record_t *peer,
                                 const utlp_wire_packet_t *wire_pkt,
                                 uint64_t rx_time_us)
{
    uint8_t burst_idx = wire_pkt->intron.field.payload[2];
    uint64_t chirp_epoch = wire_pkt->exon.utlp_timestamp_us;

    /* Validate burst index */
    if (burst_idx >= UTLP_CHIRP_BURST_COUNT) {
        utlp_hal_log_warn(TAG, "Invalid burst index: %u", burst_idx);
        return;
    }

    /*
     * Check if this is a NEW chirp or continuation of current chirp.
     * A new chirp has a different chirp_epoch (timestamp).
     */
    if (chirp_epoch != peer->chirp.chirp_epoch_us) {
        /* New chirp starting - reset state */
        peer->chirp.chirp_epoch_us = chirp_epoch;
        peer->chirp.bursts_received = 0;
        peer->chirp.chirp_complete = false;
    }

    /* Record this burst's arrival time */
    peer->chirp.rx_time_us[burst_idx] = rx_time_us;
    peer->chirp.bursts_received |= (1 << burst_idx);

    /*
     * Check if all 3 bursts received - calculate self-adjusted offset
     */
    if (peer->chirp.bursts_received == 0x07) {  /* 0b111 = all 3 bursts */
        peer->chirp.chirp_complete = true;

        /*
         * === 3-BURST SELF-ADJUSTMENT (No 4-Way Handshake Needed!) ===
         *
         * "Individual device resolves its own protocol/arbor stack jitter."
         *
         * Each burst gives an independent offset measurement:
         *   offset_i = rx[i] - (tx + i*spacing)
         *
         * Our ISR jitter varies per burst, but by averaging all 3:
         *   avg_offset = (offset_0 + offset_1 + offset_2) / 3
         *
         * The random variation in our receive timing CANCELS OUT,
         * leaving only the true clock offset + systematic bias.
         *
         * This is "self-adjustment" - we correct our own jitter without
         * any explicit feedback from the peer.
         */
        int64_t offset_0 = (int64_t)peer->chirp.rx_time_us[0] - (int64_t)chirp_epoch;
        int64_t offset_1 = (int64_t)peer->chirp.rx_time_us[1] -
                           ((int64_t)chirp_epoch + UTLP_CHIRP_BURST_SPACING_US);
        int64_t offset_2 = (int64_t)peer->chirp.rx_time_us[2] -
                           ((int64_t)chirp_epoch + 2 * UTLP_CHIRP_BURST_SPACING_US);

        /* Average cancels ISR jitter - self-adjustment! */
        peer->chirp.offset_us = (offset_0 + offset_1 + offset_2) / 3;

        utlp_hal_log_info(TAG, "3-burst offset: [%lld, %lld, %lld] → avg=%lld us",
                          (long long)offset_0, (long long)offset_1, (long long)offset_2,
                          (long long)peer->chirp.offset_us);

        /* Calculate inter-burst timing (expected: 2ms each) */
        int64_t delta_01 = (int64_t)(peer->chirp.rx_time_us[1] - peer->chirp.rx_time_us[0]);
        int64_t delta_12 = (int64_t)(peer->chirp.rx_time_us[2] - peer->chirp.rx_time_us[1]);

        /* Jitter = deviation from expected 2ms */
        peer->chirp.jitter_01_us = delta_01 - UTLP_CHIRP_BURST_SPACING_US;
        peer->chirp.jitter_12_us = delta_12 - UTLP_CHIRP_BURST_SPACING_US;

        /*
         * Motion hint: difference in jitter between intervals
         *
         * If propagation delay is changing (device moving):
         * - Positive motion_hint = delay increasing = devices moving apart
         * - Negative motion_hint = delay decreasing = devices moving closer
         * - Zero motion_hint = stable distance
         *
         * Note: This is noisy! Use for research/observation, not control.
         */
        peer->chirp.motion_hint_us = peer->chirp.jitter_12_us - peer->chirp.jitter_01_us;

        /*
         * === UPDATE VECTOR METRICS ===
         *
         * "Scalar values show a moment; vectors show meaning over time."
         *
         * These history buffers enable outlier rejection, trend detection,
         * and future HDC encoding. Control loops should use the FILTERED
         * (median) values rather than raw scalars.
         */
        offset_history_update(&peer->chirp.offset_history, peer->chirp.offset_us);
        jitter_dist_update(&peer->chirp.jitter_dist, peer->chirp.jitter_01_us);
        jitter_dist_update(&peer->chirp.jitter_dist, peer->chirp.jitter_12_us);

        /* Log BOTH scalar (human-readable) and vector (filtered) */
        utlp_hal_log_info(TAG, "Chirp: offset=%lld us (median=%lld, trend=%lld us/s)",
                          (long long)peer->chirp.offset_us,
                          (long long)peer->chirp.offset_history.median_us,
                          (long long)peer->chirp.offset_history.trend_us_per_s);
        utlp_hal_log_info(TAG, "  jitter: raw=[%lld,%lld] p50=%lu p90=%lu us | motion=%lld",
                          (long long)peer->chirp.jitter_01_us,
                          (long long)peer->chirp.jitter_12_us,
                          (unsigned long)peer->chirp.jitter_dist.p50_us,
                          (unsigned long)peer->chirp.jitter_dist.p90_us,
                          (long long)peer->chirp.motion_hint_us);

        /*
         * === UPDATE TIME SYNC STATE ===
         *
         * Use the FILTERED (median) offset once history has built up.
         * The median naturally rejects outliers and provides stability.
         * First sync uses raw offset; subsequent updates use median.
         */
        if (!s_utlp.time_synced) {
            /* First sync: use raw averaged offset */
            s_utlp.time_offset_us = peer->chirp.offset_us;
            s_utlp.time_synced = true;
            utlp_hal_log_info(TAG, "TIME SYNCED! Adopted offset=%lld us (3-burst avg)",
                              (long long)s_utlp.time_offset_us);
        } else if (peer->chirp.offset_history.count >= 4) {
            /* Ongoing sync: use median-filtered offset for stability */
            s_utlp.time_offset_us = peer->chirp.offset_history.median_us;
            utlp_hal_log_info(TAG, "TIME UPDATE: median_offset=%lld us (from %u samples)",
                              (long long)s_utlp.time_offset_us,
                              peer->chirp.offset_history.count);
        }

        /*
         * EPOCH RESOLUTION - Now that we have a valid offset!
         *
         * This is the key fix for the "youngest device wins" bug.
         * We defer epoch resolution until here because we need the clock
         * offset to determine who actually booted first.
         */
        if (!peer->epoch_resolved) {
            resolve_epoch_with_offset(peer);

            /*
             * === APPLY OFFSET TO PHASE ENGINE FOR GLOBAL TIME ===
             *
             * After epoch resolution, we know WHO should apply the offset:
             * - Device that ADOPTED: Apply offset to convert local → global time
             * - Device that KEPT epoch: Their local time IS the reference (offset=0)
             *
             * This ensures both devices show the SAME scalar time in logs.
             */
            if (s_utlp.we_adopted_epoch) {
                /*
                 * We adopted the peer's epoch.
                 * Our local time + offset = peer's time = GLOBAL time
                 *
                 * offset = rx_time - tx_time
                 * If offset > 0: Our clock is ahead, we need to SUBTRACT to match peer
                 * If offset < 0: Our clock is behind, offset is already negative
                 *
                 * Phase engine: scalar = cycles*period + ticks + epoch_offset
                 * We set epoch_offset = -time_offset_us to align with peer
                 */
                utlp_phase_set_epoch_offset(-s_utlp.time_offset_us);
                utlp_hal_log_info(TAG, "PHASE ENGINE: Offset applied=%lld us (we adopted)",
                                  (long long)(-s_utlp.time_offset_us));
            } else {
                /* We won - keep offset at 0, our time is the reference */
                utlp_phase_set_epoch_offset(0);
                utlp_hal_log_info(TAG, "PHASE ENGINE: We are time reference (offset=0)");
            }
        }
    }
}

/**
 * @brief Process received beacon (seismic chirp burst)
 *
 * Handles 32-byte wire packet format with 3-burst seismic chirp.
 *
 * @param pkt Received packet from HAL
 */
static void on_beacon_received(const utlp_packet_t *pkt)
{
    if (!pkt || pkt->len < sizeof(utlp_wire_packet_t)) {
        return;
    }

    uint64_t rx_time_us = utlp_hal_get_micros();
    const utlp_wire_packet_t *wire_pkt = (const utlp_wire_packet_t *)pkt->payload;

    /* Verify protocol version */
    if (wire_pkt->exon.protocol_version != UTLP_PROTOCOL_VERSION_N2) {
        utlp_hal_log_warn(TAG, "Ignoring beacon: unsupported version 0x%02X",
                          wire_pkt->exon.protocol_version);
        return;
    }

    /* Extract session salt for contact classification */
    uint8_t salt[2];
    salt[0] = (uint8_t)(wire_pkt->exon.session_salt & 0xFF);
    salt[1] = (uint8_t)((wire_pkt->exon.session_salt >> 8) & 0xFF);

    /* Classify contact type */
    contact_type_t contact = classify_contact(pkt->mac, salt);

    /* Build epoch_state from wire packet for first contact handling */
    epoch_state_t peer_epoch;
    peer_epoch.origin_time = (uint32_t)(wire_pkt->exon.utlp_timestamp_us / 1000000ULL);
    peer_epoch.depth = UTLP_DEPTH_FRESH;  /* Phase 2: assume fresh for now */
    peer_epoch.session_salt[0] = salt[0];
    peer_epoch.session_salt[1] = salt[1];

    /* Get phase chord from current time (Phase 2: placeholder) */
    utlp_phase_chord_t peer_chord;
    utlp_phase_get_chord(peer_chord);  /* Use our chord as placeholder */

    peer_record_t *peer = NULL;

    switch (contact) {
        case CONTACT_NEW_PEER:
            utlp_hal_log_info(TAG, "New peer discovered");
            handle_first_contact(pkt->mac, &peer_epoch, peer_chord);
            peer = find_peer_by_mac(pkt->mac);
            break;

        case CONTACT_REBOOTED_PEER:
            utlp_hal_log_info(TAG, "Peer reboot detected - re-evaluating");
            invalidate_peer(pkt->mac);
            handle_first_contact(pkt->mac, &peer_epoch, peer_chord);
            peer = find_peer_by_mac(pkt->mac);
            break;

        case CONTACT_KNOWN_PEER:
            peer = find_peer_by_mac(pkt->mac);
            if (peer) {
                peer->last_seen_us = rx_time_us;
            }
            break;
    }

    /*
     * === UPDATE SWARM STATE VECTOR ===
     *
     * Track beacon intervals for genesis/steady pattern detection.
     * This is the foundation of swarm state awareness.
     */
    if (peer) {
        beacon_interval_update(&peer->interval_history, rx_time_us);
    }

    /*
     * Process seismic chirp burst for time synchronization
     */
    if (peer) {
        process_chirp_burst(peer, wire_pkt, rx_time_us);
    }

    /*
     * WELCOME RESPONSE: If we're established and peer is genesis pulsing,
     * send immediate out-of-schedule beacon to accelerate convergence.
     *
     * "When an established device hears a genesis pulse, it says 'Hello!'"
     *
     * This solves the critical gap where newborn (50ms interval) waits up to
     * 60 seconds to hear from established device (60s interval).
     */
    if (peer && (contact == CONTACT_NEW_PEER || contact == CONTACT_REBOOTED_PEER)) {
        if (should_send_welcome_response(peer, rx_time_us)) {
            send_welcome_response(peer, rx_time_us);
        }
    }
}

/**
 * @brief Send seismic chirp beacon (3 bursts @ 2ms spacing)
 *
 * "Every beacon is a seismic chirp - 3 packets spaced 2ms apart,
 * all carrying the SAME timestamp (the chirp epoch)."
 *
 * The 3-burst pattern with SAME timestamp allows receivers to extract:
 * 1. Time offset (burst 0 timestamp vs local time)
 * 2. Receiver jitter (deviation from expected 2ms spacing)
 * 3. Motion hint (propagation delay drift between bursts)
 *
 * Uses 32-byte utlp_wire_packet_t format:
 * - EXON (24 bytes): SequenceID, Timestamp, NTP, Salt, Stratum, Version
 * - INTRON (8 bytes): TX_Power, Battery, Drift, Opcode, Payload[burst_index]
 */
static void send_beacon(void)
{
    utlp_wire_packet_t pkt;

    /*
     * Capture chirp epoch ONCE - same timestamp for all 3 bursts!
     * This is the "known reference signal" - deviations reveal receiver jitter.
     */
    uint64_t chirp_epoch_us = utlp_hal_get_micros();

    /*
     * SELF-OBSERVATION: Track our own beacon interval texture
     *
     * Same analysis we apply to peers, applied to ourselves.
     * This provides: self-awareness, pattern verification, debug symmetry.
     */
    if (s_utlp.last_tx_us != 0) {
        beacon_interval_update(&s_utlp.self_interval, chirp_epoch_us);
    }
    s_utlp.last_tx_us = chirp_epoch_us;

    /*
     * Build EXON (cleartext header) - same for all bursts
     */
    pkt.exon.sequence_id = s_utlp.sequence_id++;
    pkt.exon.utlp_timestamp_us = chirp_epoch_us;
    pkt.exon.ntp_timestamp_utc = 0;  /* No NTP in Phase 2 */
    pkt.exon.session_salt = (uint16_t)(s_utlp.epoch.session_salt[0] |
                                        (s_utlp.epoch.session_salt[1] << 8));
    pkt.exon.stratum = 1;  /* Genesis stratum */
    pkt.exon.protocol_version = UTLP_PROTOCOL_VERSION_N2;

    /*
     * Build INTRON (encrypted payload) - burst_index varies
     */
    pkt.intron.field.tx_power_dbm = 0;  /* Default TX power */
    pkt.intron.field.battery_level = 255;  /* No battery monitoring in Phase 2 */
    pkt.intron.field.drift_ppm = 0;  /* No drift estimate yet */
    pkt.intron.field.opcode = UTLP_CMD_NONE;  /* Heartbeat */

    /* Payload[0] = CPU load (unused), Payload[1] = Role, Payload[2] = Burst index */
    pkt.intron.field.payload[0] = 0;  /* CPU load */
    pkt.intron.field.payload[1] = 0;  /* Role: GENESIS */

    /*
     * Send 3 bursts with 2ms spacing - the seismic chirp!
     *
     * Burst 0: Offset measurement (control)
     * Burst 1: Jitter rate (control)
     * Burst 2: Jitter acceleration (observation only)
     */
    for (uint8_t burst = 0; burst < UTLP_CHIRP_BURST_COUNT; burst++) {
        pkt.intron.field.payload[2] = burst;  /* Burst index */

        /* TX the packet (no encryption in Phase 2) */
        utlp_transport_tx((const uint8_t *)&pkt, sizeof(pkt));

        /* Wait 2ms between bursts (except after last burst) */
        if (burst < UTLP_CHIRP_BURST_COUNT - 1) {
            utlp_hal_delay_us(UTLP_CHIRP_BURST_SPACING_US);
        }
    }
}

/*============================================================================
 * UTILITY FUNCTIONS
 *==========================================================================*/

/**
 * @brief Run physics heartbeat - 1Hz LED blink using SYNCHRONIZED time
 *
 * LED phase is computed from synchronized time so both devices blink together:
 * - If we WON epoch resolution: use our local time (peer adjusts to us)
 * - If we ADOPTED peer's epoch: adjust our time by offset to match peer
 *
 * Time synchronization formula:
 *   synced_time = local_time - offset
 *
 * Where offset = (our_rx_time - peer_tx_time):
 *   - Positive offset: we're ahead of peer → subtract to slow down
 *   - Negative offset: we're behind peer → subtracting negative = speed up
 */
static void run_heartbeat(void)
{
    uint64_t now_us = utlp_hal_get_micros();

    /*
     * Apply time sync offset ONLY if we adopted (lost epoch resolution).
     * The epoch winner keeps their time; the loser adjusts.
     *
     * This ensures both devices compute the SAME phase value at the SAME
     * wall-clock moment, resulting in synchronized LED blinking.
     */
    if (s_utlp.time_synced && s_utlp.we_adopted_epoch) {
        now_us = (uint64_t)((int64_t)now_us - s_utlp.time_offset_us);
    }

    uint32_t phase_ms = (now_us / 1000) % 1000;

    /* 1Hz blink: ON for 500ms, OFF for 500ms */
    uint8_t duty = (phase_ms < 500) ? 100 : 0;

    utlp_hal_set_actuator_phase(UTLP_ACTUATOR_MAIN, 1000, 0, duty);
}

/*============================================================================
 * PUBLIC API STUBS (for compilation compatibility)
 *==========================================================================*/

/**
 * @brief Get current stratum (always Genesis for Phase 0)
 */
uint8_t utlp_get_stratum(void)
{
    return 1;  /* Genesis stratum */
}

/**
 * @brief Set stratum for arbor (stub)
 */
void utlp_set_stratum_for_arbor(utlp_arbor_id_t arbor, uint8_t stratum)
{
    (void)arbor;
    (void)stratum;
}

/**
 * @brief Set primary time source (stub)
 */
void utlp_set_primary_time_source(utlp_arbor_id_t arbor)
{
    (void)arbor;
}

/**
 * @brief Set swarm DNA (stub)
 */
void utlp_set_swarm_dna(const uint8_t dna[UTLP_DNA_SIZE])
{
    (void)dna;
}

/*============================================================================
 * APPLICATION ENTRY POINT
 *==========================================================================*/

/**
 * @brief Main UTLP application entry point
 *
 * Phase 1 Genesis implementation:
 * - Initialize HAL layer
 * - Initialize epoch state (origin_time, depth=0, session_salt)
 * - Initialize phase engine (HPLAC)
 * - Run LED heartbeat loop (proves life)
 *
 * This is called from app_main() after platform setup.
 */
void utlp_app_run(void)
{
    utlp_hal_log_info(TAG, "========================================");
    utlp_hal_log_info(TAG, "UTLP Phase 2 - First Contact (N=2)");
    utlp_hal_log_info(TAG, "\"Time is a chord, not a number\"");
    utlp_hal_log_info(TAG, "========================================");

    /*
     * Step 1: Initialize HAL
     *
     * The HAL provides:
     * - Radio TX/RX (802.15.4 or ESP-NOW)
     * - Timer access (esp_timer)
     * - Actuator control (LED/motor)
     * - Random number generation
     */
    utlp_hal_init();

    /*
     * Step 2: Get our MAC address
     */
    utlp_hal_get_mac(s_utlp.local_mac);
    utlp_hal_log_info(TAG, "MAC: %02X:%02X:%02X:%02X:%02X:%02X",
                      s_utlp.local_mac[0], s_utlp.local_mac[1],
                      s_utlp.local_mac[2], s_utlp.local_mac[3],
                      s_utlp.local_mac[4], s_utlp.local_mac[5]);

    /*
     * Step 3: Initialize Epoch State (Phase 1 - Genesis)
     *
     * Stem Cell Model: Every device starts as a "somatic cell" (depth=128)
     * with half vitality. Only Time Lords earn depth=255 through service.
     * This prevents reboot attacks where a fresh device claims authority.
     *
     * origin_time = boot moment (truncated to seconds for wire efficiency)
     * depth = UTLP_DEPTH_FRESH (128) - somatic cell, half vitality
     * session_salt = per-boot random (anti-replay, peer identification)
     *
     * On Phase 2 first contact, epoch resolution uses:
     * 1. Higher depth (more vitality) wins
     * 2. Equal depth → oldest origin_time wins
     * 3. True tie → lower MAC adopts from higher MAC
     */
    uint16_t salt = utlp_security_generate_session_salt();

    /* Capture boot moment as origin time (seconds, for wire format) */
    uint64_t boot_us = utlp_hal_get_micros();
    uint32_t origin_time_s = (uint32_t)(boot_us / 1000000ULL);

    /* Initialize epoch state */
    s_utlp.epoch.origin_time = origin_time_s;
    s_utlp.epoch.depth = UTLP_DEPTH_FRESH;  /* Fresh boot - somatic cell (stem cell model) */
    s_utlp.epoch.session_salt[0] = (uint8_t)(salt & 0xFF);
    s_utlp.epoch.session_salt[1] = (uint8_t)((salt >> 8) & 0xFF);

    utlp_hal_log_info(TAG, "Epoch State (Genesis):");
    utlp_hal_log_info(TAG, "  origin_time: %lu s", (unsigned long)s_utlp.epoch.origin_time);
    utlp_hal_log_info(TAG, "  depth: %u (fresh boot - somatic cell)", s_utlp.epoch.depth);
    utlp_hal_log_info(TAG, "  session_salt: 0x%04X", salt);

    /*
     * Step 4: Initialize phase engine (HPLC - Vector Time)
     *
     * "Time is a chord, not a number."
     *
     * Phase 1 uses the full 10 MHz MCPWM-based Hardware Phase Locked
     * Coherency engine via the timer HAL. Time is represented as a
     * phase chord (8 residues modulo coprime primes) - scalar time
     * is DERIVED via CRT when needed.
     */
    esp_err_t phase_ret = utlp_phase_init();
    if (phase_ret != ESP_OK) {
        utlp_hal_log_error(TAG, "Phase engine init failed!");
    }

    /*
     * Step 5: Initialize arbor subsystem (stub)
     */
    utlp_arbor_init();

    /*
     * Step 6: Initialize transport layer (stub)
     */
    utlp_transport_init(NULL);

    /*
     * Step 7: Initialize SMSP (stub)
     */
    smsp_init();

    /*
     * Step 8: Record boot time for genesis pulse calculation
     */
    s_utlp.boot_time_us = utlp_hal_get_micros();
    s_utlp.current_genesis_phase = 1;  /* Start in genesis burst phase */

    /*
     * Mark as initialized
     */
    s_utlp.initialized = true;
    utlp_hal_log_info(TAG, "Phase 2 initialization complete");
    utlp_hal_log_info(TAG, "Seismic Chirp: 3-burst @ %lu ms spacing",
                      (unsigned long)(UTLP_CHIRP_BURST_SPACING_US / 1000));
    utlp_hal_log_info(TAG, "Beacon format: 32-byte wire packet (EXON+INTRON)");
    utlp_hal_log_info(TAG, "Starting beacon TX/RX - searching for peers!");

    /*
     * Phase 2 Main Loop: First Contact
     *
     * "Time is a chord, not a number."
     *
     * This loop:
     * - Runs LED heartbeat (physics proof)
     * - Sends periodic beacons
     * - Receives and processes peer beacons
     * - Performs epoch resolution on first contact
     *
     * Phase 2 Validation Gates:
     * - [x] Single device boots, generates unique session_salt
     * - [x] LED blinks at 1Hz using phase engine
     * - [x] origin_time = boot moment, depth = 128 (fresh)
     * - [ ] Two devices discover each other via beacons
     * - [ ] Higher depth (more vital) wins resolution
     * - [ ] Depth DECREMENTS on adoption (telomere shortening)
     * - [ ] Session_salt unchanged after adoption
     * - [ ] Reboot detection works (same MAC, new salt)
     * - [ ] Chord-origin verification rejects implausible peers
     */
    uint64_t last_log_us = 0;
    uint64_t last_beacon_us = 0;
    uint64_t last_chirp_log_us = 0;
    uint32_t heartbeat_count = 0;
    bool was_chirping = true;
    utlp_phase_chord_t chord;
    utlp_packet_t rx_pkt;

    /* Log genesis chirp start */
    utlp_hal_log_info(TAG, "Genesis Chirp: interval=%lu ms (LINEAR: base=%lu + slope=%lu×t)",
                      (unsigned long)(UTLP_CHIRP_BASE_US / 1000),
                      (unsigned long)(UTLP_CHIRP_BASE_US / 1000),
                      (unsigned long)(UTLP_CHIRP_SLOPE_US / 1000));

    while (1) {
        uint64_t now_us = utlp_hal_get_micros();
        uint64_t uptime_us = now_us - s_utlp.boot_time_us;

        /* Run physics heartbeat (LED blink) */
        run_heartbeat();

        /* Poll for received beacons */
        if (utlp_transport_rx_poll(&rx_pkt)) {
            on_beacon_received(&rx_pkt);
        }

        /*
         * Genesis Chirp: Linear frequency sweep beacon interval
         *
         * "Like the Cosmic Microwave Background reveals the Big Bang's age,
         * the Genesis Chirp pattern reveals how recently a device booted."
         *
         * Formula: interval = BASE + (uptime_seconds × SLOPE)
         *
         * Any observer can detect a genesis chirp by measuring the slope
         * of interval changes. If slope ≈ CHIRP_SLOPE_US, it's a newborn.
         */
        bool is_chirping;
        uint64_t beacon_interval_us = get_genesis_chirp_interval_us(uptime_us, &is_chirping);

        /* Log chirp progress every second during chirp phase */
        if (is_chirping && (now_us - last_chirp_log_us >= 1000000ULL)) {
            uint32_t uptime_s = (uint32_t)(uptime_us / 1000000ULL);
            utlp_hal_log_info(TAG, "Chirp: t=%lus → interval=%lu ms",
                              (unsigned long)uptime_s,
                              (unsigned long)(beacon_interval_us / 1000));
            last_chirp_log_us = now_us;
        }

        /* Log transition from chirp to steady state */
        if (was_chirping && !is_chirping) {
            utlp_hal_log_info(TAG, "Genesis Chirp COMPLETE → Steady state: %lu s interval",
                              (unsigned long)(UTLP_BEACON_STEADY_US / 1000000));
            was_chirping = false;
        }

        /* Send beacon periodically */
        if (now_us - last_beacon_us >= beacon_interval_us) {
            send_beacon();
            last_beacon_us = now_us;
        }

        /* Periodic logging (every 10 seconds) */
        if (now_us - last_log_us >= 10000000ULL) {
            heartbeat_count++;

            /* Get ISR latency from phase engine (ILC learning) */
            uint32_t isr_latency_us = utlp_phase_get_isr_latency_us();

            /* Get current phase chord (vector time) */
            utlp_phase_get_chord(chord);

            utlp_hal_log_info(TAG, "Heartbeat #%lu | depth=%u | salt=0x%02X%02X | peers=%u | ILC=%lu us",
                              (unsigned long)heartbeat_count,
                              s_utlp.epoch.depth,
                              s_utlp.epoch.session_salt[1],
                              s_utlp.epoch.session_salt[0],
                              s_utlp.peer_count,
                              (unsigned long)isr_latency_us);

            /*
             * Log BOTH representations:
             * - VECTOR (protocol-native): phase chord [8 residues]
             * - SCALAR (human-readable): CRT-derived microseconds
             *
             * "Time is a chord, not a number" - but scalars help humans debug.
             */
            uint64_t scalar_us = utlp_phase_get_scalar_us();
            utlp_hal_log_info(TAG, "  VECTOR: chord=[%u,%u,%u,%u,%u,%u,%u,%u]",
                              chord[0], chord[1], chord[2], chord[3],
                              chord[4], chord[5], chord[6], chord[7]);
            utlp_hal_log_info(TAG, "  SCALAR: %llu us (CRT-derived, for logging only)",
                              (unsigned long long)scalar_us);

            /* Log time sync status with vector metrics if available */
            if (s_utlp.time_synced) {
                /* Find first peer to show vector metrics */
                peer_record_t *first_peer = NULL;
                for (int i = 0; i < UTLP_MAX_PEERS && !first_peer; i++) {
                    if (s_utlp.peers[i].is_known) {
                        first_peer = &s_utlp.peers[i];
                    }
                }

                if (s_utlp.we_adopted_epoch) {
                    utlp_hal_log_info(TAG, "  SYNC: offset=%lld us (APPLYING - we adopted)",
                                      (long long)s_utlp.time_offset_us);
                } else {
                    utlp_hal_log_info(TAG, "  SYNC: offset=%lld us (NOT applying - we won)",
                                      (long long)s_utlp.time_offset_us);
                }

                /* Show filtered metrics if history has built up */
                if (first_peer && first_peer->chirp.offset_history.count >= 2) {
                    utlp_hal_log_info(TAG, "  VECTOR METRICS: median=%lld us, trend=%lld us/s, jitter p50=%lu p90=%lu us",
                                      (long long)first_peer->chirp.offset_history.median_us,
                                      (long long)first_peer->chirp.offset_history.trend_us_per_s,
                                      (unsigned long)first_peer->chirp.jitter_dist.p50_us,
                                      (unsigned long)first_peer->chirp.jitter_dist.p90_us);
                }
            } else {
                utlp_hal_log_info(TAG, "  SYNC: searching for peer...");
            }

            last_log_us = now_us;
        }

        /* Yield to other tasks */
        utlp_hal_yield();
    }
}
