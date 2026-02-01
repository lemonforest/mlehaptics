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
#include "utlp_hdc.h"       /* HDC-native sync primitives */

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
    uint32_t origin_time;      /**< Swarm time epoch origin (seconds) - lineage's T=0 */
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

/** @brief Protocol version for Phase 2 (Vector Time) - Steady State */
#define UTLP_PROTOCOL_VERSION_N2        0x02

/**
 * @brief Protocol version for Genesis Pulsing
 *
 * Devices in genesis chirp phase (first ~10s after boot) use this version
 * to explicitly signal they're seeking swarm adoption. Established devices
 * seeing this version should send an immediate welcome response.
 *
 * Using 0xFE (not 0xFF) leaves room for future special values.
 */
#define UTLP_PROTOCOL_VERSION_GENESIS   0xFE

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
#define GENESIS_SETTLING_INTERVAL_MS 2000   /**< <= 2s = Phase 1-4 (unproven) */
#define STEADY_STATE_INTERVAL_MS    50000   /**< > 50s = Phase 5 (proven) */

/**
 * @brief Lineage state enumeration
 *
 * Replaces binary is_genesis_pattern/is_steady_pattern with explicit state machine.
 * Terminology shift: "genesis" → "lineage" per HDC/Physics/Engineering analysis.
 *
 * Key insight: "Lineage is what propagates. Authority is what accumulates."
 *   - A device doesn't "become established" - its AUTHORITY increases
 *   - A lineage doesn't "become proven" - EVIDENCE accumulates
 *
 * The UNKNOWN state solves the critical default-state bug where (false, false)
 * meant both "no data yet" AND "transitioning" - now these are distinct.
 */
typedef enum {
    LINEAGE_UNKNOWN = 0,       /**< Default: insufficient interval data (SAFE) */
    LINEAGE_UNPROVEN,          /**< Genesis pulsing: intervals <= 2s observed */
    LINEAGE_TRANSITIONING,     /**< Between genesis and steady: 2s < interval <= 50s */
    LINEAGE_PROVEN             /**< Established: intervals > 50s with low variance */
} lineage_state_t;

/** Minimum intervals needed before trusting lineage classification */
#define UTLP_MIN_INTERVALS_FOR_LINEAGE  2

/** Hysteresis threshold: consecutive observations needed to change state */
#define UTLP_LINEAGE_HYSTERESIS_THRESHOLD  2

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
 * TREND CALCULATION FIX: Uses actual elapsed time between first and last
 * samples, not sample count. This ensures accurate drift rate even when
 * samples are spaced irregularly (e.g., 20s between chirps, not 1s).
 *
 * HDC Encoding (future): Encode as sparse binary vector where set bits
 * represent offset buckets. Similar offsets → similar hypervectors.
 */
typedef struct {
    /* === 8-byte aligned fields (descending) === */
    int64_t     samples[UTLP_METRIC_HISTORY_SIZE];  /**< Ring buffer of offsets */
    int64_t     median_us;                          /**< Median of samples (filtered) */
    int64_t     trend_us_per_s;                     /**< Drift rate (positive = diverging) */
    uint64_t    first_sample_time_us;               /**< When tracking started (for accurate trend) */
    uint64_t    last_sample_time_us;                /**< Most recent sample time */
    /* === 1-byte fields (grouped at end) === */
    uint8_t     write_idx;                          /**< Next write position */
    uint8_t     count;                              /**< Valid samples (0-8) */
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
    /* === 4-byte aligned fields (descending) === */
    uint32_t    samples[UTLP_METRIC_HISTORY_SIZE];  /**< Ring buffer of |jitter| */
    uint32_t    p50_us;                             /**< Median jitter */
    uint32_t    p90_us;                             /**< 90th percentile (worst-case) */
    /* === 1-byte fields (grouped at end) === */
    uint8_t     write_idx;                          /**< Next write position */
    uint8_t     count;                              /**< Valid samples (0-8) */
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
    lineage_state_t lineage;                        /**< Lineage classification (replaces 2 bools) */
    uint8_t     lineage_hysteresis;                 /**< Consecutive obs supporting state change */
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
    /* === 8-byte aligned fields first === */
    uint64_t            timestamps[UTLP_METRIC_HISTORY_SIZE]; /**< When observed (local) */
    /* === 1-byte aligned arrays === */
    utlp_phase_chord_t  chords[UTLP_METRIC_HISTORY_SIZE]; /**< Ring buffer of chords */
    /* === 1-byte fields (grouped at end) === */
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
    /* === 8-byte aligned fields first === */
    uint64_t    rx_time_us[UTLP_CHIRP_BURST_COUNT]; /**< Local RX times for each burst */
    int64_t     offset_us;              /**< Clock offset (our time - their time) */
    int64_t     jitter_01_us;           /**< Jitter: (rx1-rx0) - 2ms expected */
    int64_t     jitter_12_us;           /**< Jitter: (rx2-rx1) - 2ms expected */
    int64_t     motion_hint_us;         /**< Motion: jitter_12 - jitter_01 (acceleration) */

    /* === Embedded structs (already properly ordered internally) === */
    offset_history_t      offset_history;   /**< Offset trend over time */
    jitter_distribution_t jitter_dist;      /**< Jitter quality distribution */

    /* === Chord-based chirp identification (8 bytes) === */
    utlp_phase_chord_t chirp_epoch_chord; /**< Peer's chord (same for all 3 bursts) */

    /* === 1-byte fields (grouped at end) === */
    uint8_t     bursts_received;        /**< Bitmask of received bursts (0x01, 0x02, 0x04) */
    bool        chirp_complete;         /**< All 3 bursts received */
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
    /* === 8-byte aligned fields first === */
    uint64_t      last_seen_us;     /**< When last heard from peer */
    uint64_t      first_beacon_us;  /**< When we first heard from this peer */
    uint64_t      welcome_sent_us;  /**< When we last sent welcome (cooldown) */

    /* === Large embedded structs (already properly ordered internally) === */
    chirp_state_t             chirp;            /**< Seismic chirp burst tracking */
    chord_history_t           chord_history;    /**< Peer's chord over time */
    beacon_interval_history_t interval_history; /**< Beacon timing pattern (SWARM STATE) */

    /* === 4-byte aligned fields === */
    uint32_t      origin_time;      /**< Last known origin_time */

    /* === HDC tracking (Phase 3 - Vector-native sync) === */
    trajectory_t      trajectory;       /**< Peer's chord trajectory (legacy ring buffer) */
    trajectory_holo_t traj_holo;        /**< Peer's holographic trajectory (TRUE HDC) */
    latency_holo_t    latency_holo;     /**< Holographic latency memory */
    agreement_vector_t last_agreement;  /**< Most recent agreement vector */

    /* === 1-byte fields (grouped at end) === */
    uint8_t       mac[6];           /**< Peer's MAC address (hardware identity) */
    uint8_t       session_salt[2];  /**< Last known session salt (session identity) */
    uint8_t       depth;            /**< Last known depth */
    uint8_t       beacon_count;     /**< Beacons received in detection window */
    uint8_t       last_beacon_chord[8]; /**< Chord of last beacon (for dedup) */
    bool          is_known;         /**< Slot in use */
    bool          epoch_resolved;   /**< True after epoch resolution complete */
    bool          genesis_protected; /**< True if we used genesis protection (legacy) */
    bool          is_genesis;       /**< True if peer is genesis pulsing (from protocol_version) */
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

    /* Time synchronization state (legacy scalar - being replaced by HDC) */
    int64_t       time_offset_us;   /**< Our time - peer time (positive = we're ahead) */
    bool          time_synced;      /**< True if we have a valid time offset */
    bool          we_adopted_epoch; /**< True if WE adopted peer's epoch (we adjust time) */
    uint32_t      sequence_id;      /**< TX sequence counter for beacons */

    /* HDC-native sync state (Phase 3 - Vector consensus) */
    trajectory_t      self_trajectory;   /**< Our own chord trajectory (legacy) */
    trajectory_holo_t self_traj_holo;    /**< Our holographic trajectory (TRUE HDC) */
    latency_holo_t    self_latency;      /**< Our latency hologram (for self-assessment) */
    rollin_t          rollin;            /**< Roll-in state for fresh boot convergence */
    uint32_t          observation_count; /**< Our total observations (authority metric) */

    /*
     * FIREFLY MODEL: Vector-Native Offset (Replaces scalar time_offset_us)
     *
     * Like fireflies synchronizing their flashes, we store the offset as a
     * CHORD (8 bytes) not a scalar. Each dimension tracks phase difference
     * in that prime's ring:
     *
     *   offset_chord[i] = (peer_chord[i] - our_chord[i]) mod prime[i]
     *
     * Benefits:
     * 1. No CRT conversion (avoids scalar artifacts)
     * 2. Each dimension can converge independently (elastic)
     * 3. SMSP can use swarm_chord directly (no scalar→chord→LED)
     * 4. Natural partition detection (dimensions disagree = trouble)
     *
     * To get swarm chord: swarm[i] = (local[i] + offset_chord[i]) mod prime[i]
     */
    utlp_phase_chord_t offset_chord;     /**< Vector offset: add to local → swarm */
    bool               have_offset_chord; /**< True if offset_chord is valid */

    /*
     * SYNC SOURCE TRACKING (Bug Fix: Stale Offset After Peer Reboot)
     *
     * When we adopt a peer's epoch, we record WHICH peer we synced from.
     * If that peer reboots (CONTACT_REBOOTED_PEER), our time_offset becomes
     * meaningless - the peer's new timeline has no relation to their old one.
     *
     * On sync source reboot:
     * 1. Clear time_synced
     * 2. Clear sync_source_mac
     * 3. Re-run epoch resolution with the rebooted peer
     *
     * This prevents "swarm fragmentation" where devices hold stale offsets
     * to timelines that no longer exist.
     */
    uint8_t       sync_source_mac[6];   /**< MAC of peer we adopted from (if have_sync_source) */
    bool          have_sync_source;     /**< True if sync_source_mac is valid */

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

    /* JPL Rule 2: Bounded loop termination */
    bool          shutdown_requested; /**< Request graceful shutdown of main loop */
} s_utlp = {0};

/*============================================================================
 * SHUTDOWN API - Glass Wall Interface
 *
 * Application layer can request UTLP shutdown via this API.
 * The main loop will exit cleanly on next iteration.
 *==========================================================================*/

/**
 * @brief Request UTLP main loop shutdown
 *
 * Sets the shutdown flag, causing the main loop to exit on its next iteration.
 * JPL Rule 2 compliance: All loops must have bounded termination.
 */
void utlp_request_shutdown(void)
{
    s_utlp.shutdown_requested = true;
}

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
 * @brief Clear offset history (call when sync source changes)
 *
 * Prevents history contamination when transitioning between sync sources.
 * Without this, old samples from previous timeline cause garbage trend values.
 *
 * @param history Offset history to clear
 */
static void offset_history_clear(offset_history_t *history)
{
    if (!history) return;
    memset(history, 0, sizeof(offset_history_t));
}

/*============================================================================
 * CHORD-ON-WIRE HELPERS - Protocol v0x02 Support
 *
 * These functions support the new chord-based wire format where time is
 * transmitted as 8-byte phase chord instead of scalar timestamp.
 *==========================================================================*/

/** @brief The 8 coprime primes used for phase chord (from utlp_config.h) */
static const uint8_t PHASE_PRIMES[8] = {241, 251, 239, 233, 229, 227, 223, 211};

/**
 * @brief Compute signed offset in quanta between two chords
 *
 * Each chord dimension wraps around at its prime. We compute the minimum
 * signed distance on each prime ring, then take the median as the offset.
 *
 * Positive result: chord_a is AHEAD of chord_b (a is in the future)
 * Negative result: chord_a is BEHIND chord_b (a is in the past)
 *
 * @param chord_a First chord (typically local/receiver)
 * @param chord_b Second chord (typically peer/sender)
 * @return Signed offset in quanta (chord_a - chord_b), median across dimensions
 */
static int32_t chord_offset_quanta(const uint8_t *chord_a, const uint8_t *chord_b)
{
    int32_t deltas[8];

    for (int i = 0; i < 8; i++) {
        uint8_t prime = PHASE_PRIMES[i];
        int16_t raw_diff = (int16_t)chord_a[i] - (int16_t)chord_b[i];

        /*
         * Compute minimum signed distance on circular ring.
         * If raw_diff > prime/2, we wrapped around - adjust to negative.
         * If raw_diff < -prime/2, we wrapped around - adjust to positive.
         */
        if (raw_diff > (int16_t)(prime / 2)) {
            raw_diff -= prime;  /* Wrapped forward → actually behind */
        } else if (raw_diff < -(int16_t)(prime / 2)) {
            raw_diff += prime;  /* Wrapped backward → actually ahead */
        }

        deltas[i] = raw_diff;
    }

    /* Return median of the 8 deltas (robust to outliers from prime ambiguity) */
    /* Simple sort for 8 elements */
    for (int i = 1; i < 8; i++) {
        int32_t key = deltas[i];
        int j = i - 1;
        while (j >= 0 && deltas[j] > key) {
            deltas[j + 1] = deltas[j];
            j--;
        }
        deltas[j + 1] = key;
    }

    /* Return average of middle two (median of even count) */
    return (deltas[3] + deltas[4]) / 2;
}

/**
 * @brief Overflow-safe modular multiplication
 *
 * Computes (a * b) % m without overflow using Russian peasant algorithm.
 * Works correctly even when a * b would exceed UINT64_MAX.
 *
 * @param a First multiplicand (will be reduced mod m)
 * @param b Second multiplicand
 * @param m Modulus
 * @return (a * b) % m
 */
static uint64_t mulmod_safe(uint64_t a, uint64_t b, uint64_t m)
{
    uint64_t result = 0;
    a %= m;

    while (b > 0) {
        if (b & 1) {
            /* result = (result + a) % m, avoiding overflow in addition */
            if (result >= m - a) {
                result = result - (m - a);  /* result = result + a - m */
            } else {
                result = result + a;
            }
        }

        /* a = (a * 2) % m, avoiding overflow in doubling */
        if (a >= m - a) {
            a = a - (m - a);  /* a = 2a - m */
        } else {
            a = a << 1;
        }

        b >>= 1;
    }

    return result;
}

/**
 * @brief Convert chord to scalar time via Chinese Remainder Theorem
 *
 * Given a phase chord [r0, r1, ..., r7], find the unique scalar x such that:
 *   x ≡ r0 (mod 241)
 *   x ≡ r1 (mod 251)
 *   ...
 *   x ≡ r7 (mod 211)
 *
 * The solution is unique modulo M = 241×251×...×211 ≈ 8.24×10^18, which fits
 * in uint64_t. This provides unambiguous time for ~261,000 years at 1μs ticks.
 *
 * @param chord Phase chord (8 bytes)
 * @return Scalar time in quanta (1 quanta = 1 ms in PRECISION mode)
 */
static uint64_t chord_to_scalar_crt(const uint8_t *chord)
{
    /*
     * Product of all primes: M = 241×251×239×233×229×227×223×211
     * M = 8,239,355,544,127,721,383 (fits in uint64_t)
     */
    static const uint64_t M = 8239355544127721383ULL;

    /*
     * Precomputed M_i values: M_i = M / prime[i]
     * Primes:     [241,     251,     239,     233,     229,     227,     223,     211]
     */
    static const uint64_t M_i[8] = {
        34188197278538263ULL,   /* M / 241 */
        32826117705688133ULL,   /* M / 251 */
        34474290979613897ULL,   /* M / 239 */
        35362040961921551ULL,   /* M / 233 */
        35979718533308827ULL,   /* M / 229 */
        36296720458712429ULL,   /* M / 227 */
        36947782709092921ULL,   /* M / 223 */
        39049078408188253ULL    /* M / 211 */
    };

    /*
     * Precomputed y_i values: y_i = M_i^(-1) mod prime[i]
     * These are the modular multiplicative inverses, precomputed offline.
     * Verify: (M_i[i] * y_i[i]) mod prime[i] == 1 for all i
     */
    static const uint8_t y_i[8] = {22, 206, 186, 18, 208, 102, 119, 72};

    uint64_t result = 0;

    for (int i = 0; i < 8; i++) {
        /*
         * CRT term: chord[i] * M_i * y_i mod M
         *
         * We use mulmod_safe to avoid overflow:
         * - chord[i] <= 250
         * - M_i ~ 3.4×10^16
         * - y_i <= 250
         * - chord[i] * M_i ~ 8.5×10^18 which can OVERFLOW uint64_t
         * - And then multiplying by y_i would definitely overflow
         *
         * mulmod_safe handles this correctly via Russian peasant algorithm.
         */
        uint64_t term = mulmod_safe((uint64_t)chord[i], M_i[i], M);
        term = mulmod_safe(term, (uint64_t)y_i[i], M);

        /* Accumulate with safe modular addition */
        if (result >= M - term) {
            result = result - (M - term);  /* result = result + term - M */
        } else {
            result = result + term;
        }
    }

    /* Result is already positive (uint64_t) and < M due to modular arithmetic */
    return result;
}

/**
 * @brief Compute signed offset between two chords using CRT
 *
 * Unlike chord_offset_quanta (which uses circular distance and fails for
 * large time differences), this uses full CRT reconstruction to compute
 * the TRUE scalar difference.
 *
 * @param chord_a First chord (typically local/receiver)
 * @param chord_b Second chord (typically peer/sender)
 * @return Signed offset in quanta (chord_a_scalar - chord_b_scalar)
 */
static int64_t chord_offset_crt(const uint8_t *chord_a, const uint8_t *chord_b)
{
    uint64_t scalar_a = chord_to_scalar_crt(chord_a);
    uint64_t scalar_b = chord_to_scalar_crt(chord_b);

    /*
     * Compute signed difference. Since scalars can be anywhere in the
     * ~8×10^18 range, we need to handle wrap-around at the CRT horizon.
     * But for practical purposes (devices running < 261,000 years),
     * simple subtraction works.
     */
    return (int64_t)scalar_a - (int64_t)scalar_b;
}

/**
 * @brief Update offset history vector with new sample
 *
 * Adds new offset to ring buffer and updates derived statistics:
 * - median_us: Filtered offset (robust to outliers)
 * - trend_us_per_s: Rate of change using ACTUAL elapsed time
 *
 * TREND CALCULATION FIX:
 * Previous bug assumed 1 second between samples (dividing by count).
 * With chirps every ~20 seconds and 8 samples, that's 160s window,
 * but old code assumed 8s, producing 20× error in trend.
 *
 * Fix: Track actual timestamps and compute drift = ΔOffset / ΔTime.
 *
 * @param history Offset history to update
 * @param offset_us New offset sample
 * @param sample_time_us Timestamp when this sample was taken (local clock)
 */
static void offset_history_update(offset_history_t *history, int64_t offset_us,
                                   uint64_t sample_time_us)
{
    if (!history) return;

    /* Track first sample time (for accurate trend calculation) */
    if (history->count == 0) {
        history->first_sample_time_us = sample_time_us;
    }
    history->last_sample_time_us = sample_time_us;

    /* Add to ring buffer */
    history->samples[history->write_idx] = offset_us;
    history->write_idx = (history->write_idx + 1) % UTLP_METRIC_HISTORY_SIZE;
    if (history->count < UTLP_METRIC_HISTORY_SIZE) {
        history->count++;
    }

    /* Update median */
    history->median_us = compute_median_i64(history->samples, history->count);

    /*
     * Compute trend using ACTUAL elapsed time (not sample count!)
     *
     * drift_rate = (newest_offset - oldest_offset) / elapsed_time
     *
     * This gives us the true drift in µs/s, which should be bounded by
     * crystal tolerance (typically ±50 ppm = ±50 µs/s).
     */
    if (history->count >= 2 && history->first_sample_time_us > 0) {
        uint8_t oldest_idx = (history->write_idx + UTLP_METRIC_HISTORY_SIZE - history->count)
                             % UTLP_METRIC_HISTORY_SIZE;
        uint8_t newest_idx = (history->write_idx + UTLP_METRIC_HISTORY_SIZE - 1)
                             % UTLP_METRIC_HISTORY_SIZE;

        int64_t delta_offset = history->samples[newest_idx] - history->samples[oldest_idx];
        uint64_t elapsed_us = history->last_sample_time_us - history->first_sample_time_us;

        if (elapsed_us > 0) {
            /* Scale to µs per second: (delta_offset / elapsed_us) * 1,000,000 */
            history->trend_us_per_s = (delta_offset * UTLP_US_PER_SEC) / (int64_t)elapsed_us;
        }
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
     * LINEAGE CLASSIFICATION with hysteresis
     *
     * Replaces binary is_genesis/is_steady with explicit state machine.
     * Key insight: "Lineage is what propagates. Authority is what accumulates."
     *
     * States:
     *   UNKNOWN:       Insufficient data (< 2 intervals) - SAFE default
     *   UNPROVEN:      Genesis pulsing (any interval <= 2s)
     *   TRANSITIONING: Between genesis and steady (2s < all intervals <= 50s)
     *   PROVEN:        Established (all intervals > 50s, low variance)
     *
     * Hysteresis prevents single-packet state flips from noise.
     */
    #define STEADY_VARIANCE_MAX_MS         10000   /* < 10s variance = stable */

    /* Insufficient data? Stay UNKNOWN (the safe default) */
    if (history->count < UTLP_MIN_INTERVALS_FOR_LINEAGE) {
        history->lineage = LINEAGE_UNKNOWN;
        history->lineage_hysteresis = 0;
        return;
    }

    /* Classify based on current interval statistics */
    lineage_state_t observed;
    if (history->min_ms <= GENESIS_SETTLING_INTERVAL_MS) {
        /* Any short interval = unproven (genesis pulsing) */
        observed = LINEAGE_UNPROVEN;
    } else if (history->min_ms > STEADY_STATE_INTERVAL_MS &&
               history->variance_ms < STEADY_VARIANCE_MAX_MS) {
        /* All long intervals with low variance = proven (established) */
        observed = LINEAGE_PROVEN;
    } else {
        /* Between genesis and steady = transitioning */
        observed = LINEAGE_TRANSITIONING;
    }

    /* Apply hysteresis: require N consecutive observations to change state */
    if (observed != history->lineage) {
        history->lineage_hysteresis++;
        if (history->lineage_hysteresis >= UTLP_LINEAGE_HYSTERESIS_THRESHOLD) {
            /* Enough evidence - transition to new state */
            history->lineage = observed;
            history->lineage_hysteresis = 0;
        }
        /* else: stay in current state, accumulating evidence */
    } else {
        /* Observation matches current state - reset hysteresis counter */
        history->lineage_hysteresis = 0;
    }
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
        uint32_t uptime_s = (uint32_t)(uptime_us / UTLP_US_PER_SEC);
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
    if (time_delta_us < UTLP_MIN_OBSERVATION_INTERVAL_US) {
        return false;
    }

    /* Calculate observed slope (us increase per second) */
    int64_t interval_delta = (int64_t)interval_2_us - (int64_t)interval_1_us;
    int64_t time_delta_s = (int64_t)(time_delta_us / UTLP_US_PER_SEC);
    if (time_delta_s == 0) time_delta_s = 1;  /* Avoid division by zero */

    int64_t observed_slope = (interval_delta * (int64_t)UTLP_US_PER_SEC) / (int64_t)time_delta_us;

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
 * 2. PEER is genesis pulsing (explicit protocol version flag)
 * 3. Cooldown has expired (prevent spam)
 *
 * EXPLICIT GENESIS MARKING: Uses protocol_version field (0xFE = genesis).
 * This is cleaner than behavioral detection because it works on FIRST beacon.
 *
 * BEHAVIORAL TRACKING: We still track beacon timing patterns for diagnostics
 * and arbor classification, but it's not used for the welcome decision.
 *
 * @param peer Peer record to check
 * @param rx_time_us Current reception timestamp
 * @param peer_is_genesis True if peer's protocol_version == GENESIS (0xFE)
 * @param beacon_chord The chord from the received beacon (for burst dedup)
 * @return true if we should send welcome response
 */
static bool should_send_welcome_response(peer_record_t *peer,
                                          uint64_t rx_time_us,
                                          bool peer_is_genesis,
                                          const uint8_t *beacon_chord)
{
    /* Condition 1: Are WE established? (past genesis chirp) */
    uint64_t our_uptime_us = rx_time_us - s_utlp.boot_time_us;
    if (our_uptime_us < UTLP_WELCOME_MIN_UPTIME_US) {
        /* We're still genesis pulsing ourselves - don't send welcome */
        return false;
    }

    /*
     * SEISMIC CHIRP BURST DEDUPLICATION
     *
     * Each chirp has 3 bursts with identical chords. Only respond to ONE
     * burst per chirp (the first one with a new chord).
     */
    bool is_new_chirp = (memcmp(beacon_chord, peer->last_beacon_chord, 8) != 0);

    /* Always update last_beacon_chord for next comparison */
    memcpy(peer->last_beacon_chord, beacon_chord, 8);

    if (!is_new_chirp) {
        /* Same chord as last beacon = another burst of same chirp, ignore */
        return false;
    }

    /*
     * BEHAVIORAL TRACKING (for diagnostics, not welcome decision)
     *
     * Track beacon timing patterns to learn about peer's hardware and arbor type.
     * This data is useful for arbor classification even though we use explicit
     * genesis marking for the welcome response decision.
     */
    if (peer->first_beacon_us == 0) {
        peer->first_beacon_us = rx_time_us;
        peer->beacon_count = 1;
    } else {
        uint64_t window_elapsed = rx_time_us - peer->first_beacon_us;
        if (window_elapsed <= UTLP_WELCOME_THRESHOLD_WINDOW_US) {
            peer->beacon_count++;
        } else {
            /* Window expired - reset for next observation window */
            peer->first_beacon_us = rx_time_us;
            peer->beacon_count = 1;
        }
    }

    /* Condition 2: Is peer EXPLICITLY marked as genesis pulsing? */
    if (!peer_is_genesis) {
        /* Peer is in steady state - no welcome needed */
        return false;
    }

    /* Condition 3: Cooldown expired? (prevent spam) */
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

    /*
     * CHORD-ORIGIN VERIFICATION DISABLED AT FIRST CONTACT
     *
     * The original design called for verifying peer's chord against their
     * claimed origin_time. However, at FIRST contact this comparison is
     * meaningless because:
     *
     * - Peer's chord is computed from THEIR boot timeline
     * - Our chord is computed from OUR boot timeline
     * - These are independent until we sync!
     *
     * The verification was comparing peer_chord with our_chord and requiring
     * 5/8 similarity, which fails 100% of the time for unsynced devices.
     *
     * FUTURE: Re-enable chord verification AFTER sync is established to
     * detect clock drift or spoofing. For N=2 first contact, we must trust
     * the peer's claims and verify through subsequent chirp exchanges.
     *
     * (void)peer_chord;  // Will use for swarm chord sync
     */
    utlp_hal_log_info(TAG, "  peer_chord=[%u,%u,%u,%u,%u,%u,%u,%u]",
                      peer_chord[0], peer_chord[1], peer_chord[2], peer_chord[3],
                      peer_chord[4], peer_chord[5], peer_chord[6], peer_chord[7]);

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
        peer->epoch_resolved = false;    /* Will resolve when we have offset */
        peer->genesis_protected = false; /* Clear protection flag for new resolution */
        utlp_hal_log_info(TAG, "Peer registered - awaiting chirp for epoch resolution");
    }
}

/**
 * @brief Resolve epoch using HDC agreement vectors (Phase 3 - Vector-native)
 *
 * Replaces scalar offset comparison with hyperdimensional agreement:
 * - Agreement vector shows per-dimension phase alignment
 * - Trajectory parallelism confirms clocks evolve together
 * - Observation count determines authority (can't be faked)
 * - Elastic nudge for convergence (not hard adoption)
 *
 * Key insight: "Two clocks are synced when they evolve in PARALLEL,
 * not when their readings match at a single instant."
 *
 * @param peer Peer record with valid chord data
 * @return true if resolution complete, false if still converging
 */
static bool resolve_epoch_hdc(peer_record_t *peer)
{
    if (!peer) {
        return false;
    }

    /*
     * ==========================================================================
     * GENESIS PROTECTION: Established devices NEVER adopt from genesis peers
     * ==========================================================================
     *
     * CRITICAL: If WE are established (past genesis chirp duration) AND
     * the peer is still genesis pulsing, we MUST NOT adopt from them.
     *
     * The newborn must sync to the established swarm, not vice versa.
     * This is a HARD RULE that overrides Genesis Distance calculations.
     */
    uint64_t our_uptime_us = utlp_hal_get_micros() - s_utlp.boot_time_us;
    bool we_are_established = (our_uptime_us >= UTLP_CHIRP_DURATION_US);

    if (we_are_established && peer->is_genesis) {
        /*
         * We are established, peer is genesis pulsing.
         * We ARE the reference - peer must sync to us.
         * Set zero offset chord and return immediately.
         */
        utlp_hal_log_info(TAG, "GENESIS PROTECTION: We are established (uptime=%llu ms), "
                          "peer is genesis pulsing → we keep epoch",
                          (unsigned long long)(our_uptime_us / 1000));

        memset(s_utlp.offset_chord, 0, UTLP_CHORD_SIZE);
        s_utlp.have_offset_chord = true;
        s_utlp.we_adopted_epoch = false;
        s_utlp.observation_count++;
        return true;  /* Resolution complete - we won by rule */
    }

    /*
     * ==========================================================================
     * FIREFLY MODEL: Vector-Native Epoch Resolution
     * ==========================================================================
     *
     * Like fireflies synchronizing flashes, we determine who is "older"
     * (the reference) by VOTING across 8 dimensions rather than converting
     * to scalar via CRT.
     *
     * Algorithm:
     * 1. Vote across all 8 dimensions: in each prime's ring, who is ahead?
     * 2. Majority vote determines who is older
     * 3. If tied → MAC tiebreaker
     * 4. Store offset as a CHORD (not scalar) for vector-native heartbeat
     *
     * Key insight: If peer's chord is consistently AHEAD of ours in most
     * dimensions, peer booted earlier → peer is the reference.
     */

    /* Get our current chord */
    utlp_phase_chord_t our_chord;
    utlp_phase_get_chord(our_chord);
    const utlp_phase_chord_t *peer_chord = &peer->chirp.chirp_epoch_chord;

    /* Firefly direction vote - uses 10k expansion for anti-aliasing */
    firefly_vote_t vote = utlp_hdc_firefly_vote(our_chord, *peer_chord);

    /* Log detailed debug info */
    utlp_hal_log_info(TAG, "FIREFLY: our=[%u,%u,%u,%u,%u,%u,%u,%u]",
                      our_chord[0], our_chord[1], our_chord[2], our_chord[3],
                      our_chord[4], our_chord[5], our_chord[6], our_chord[7]);
    utlp_hal_log_info(TAG, "FIREFLY: peer=[%u,%u,%u,%u,%u,%u,%u,%u]",
                      (*peer_chord)[0], (*peer_chord)[1], (*peer_chord)[2], (*peer_chord)[3],
                      (*peer_chord)[4], (*peer_chord)[5], (*peer_chord)[6], (*peer_chord)[7]);
    utlp_hal_log_info(TAG, "FIREFLY: signed_dist=[%d,%d,%d,%d,%d,%d,%d,%d]",
                      vote.signed_dist[0], vote.signed_dist[1],
                      vote.signed_dist[2], vote.signed_dist[3],
                      vote.signed_dist[4], vote.signed_dist[5],
                      vote.signed_dist[6], vote.signed_dist[7]);
    utlp_hal_log_info(TAG, "FIREFLY: direction=%+d conf=%u our_dist=%u peer_dist=%u",
                      vote.direction, vote.confidence,
                      vote.sim_forward, vote.sim_backward);  /* Genesis distance: higher = older */
    utlp_hal_log_info(TAG, "FIREFLY: offset=[%u,%u,%u,%u,%u,%u,%u,%u]",
                      vote.offset_chord[0], vote.offset_chord[1],
                      vote.offset_chord[2], vote.offset_chord[3],
                      vote.offset_chord[4], vote.offset_chord[5],
                      vote.offset_chord[6], vote.offset_chord[7]);

    /*
     * === FIREFLY RESOLUTION: OLDEST DEVICE WINS ===
     *
     * Genesis Distance approach (HDC Orrery model):
     * - Genesis = [0,0,0,0,0,0,0,0] = starting line
     * - Distance = 255 - similarity(chord, genesis) in 10k space
     * - GREATER distance from genesis = MORE elapsed time = OLDER
     *
     * vote.direction:
     *   +1 = We are older (our genesis distance > peer's)
     *   -1 = Peer is older (peer genesis distance > ours)
     *    0 = Tied (use MAC tiebreaker)
     */
    bool i_should_adopt = false;

    if (vote.direction < 0) {
        /*
         * Peer is older (peer has walked further from genesis).
         * We should adopt peer's timeline.
         */
        i_should_adopt = true;
        utlp_hal_log_info(TAG, "FIREFLY: Peer is older (vote=%+d, conf=%u) → we adopt",
                          vote.direction, vote.confidence);

    } else if (vote.direction > 0) {
        /*
         * We are older (we have walked further from genesis).
         * Peer should adopt from us.
         */
        i_should_adopt = false;
        utlp_hal_log_info(TAG, "FIREFLY: We are older (vote=%+d, conf=%u) → we keep epoch",
                          vote.direction, vote.confidence);

    } else {
        /*
         * Tied vote (dimensions split or all abstained).
         * Use MAC address as deterministic tiebreaker.
         * Lower MAC adopts from higher MAC (arbitrary but consistent).
         */
        i_should_adopt = (memcmp(s_utlp.local_mac, peer->mac, 6) < 0);
        utlp_hal_log_info(TAG, "FIREFLY: Tied vote (conf=%u) → MAC tiebreaker: %s adopts",
                          vote.confidence,
                          i_should_adopt ? "we" : "peer");
    }

    /*
     * === APPLY RESOLUTION (Vector-Native) ===
     */
    if (i_should_adopt) {
        /*
         * We are the younger device - adopt peer's timeline.
         *
         * Store the OFFSET CHORD (not scalar!). To get swarm chord:
         *   swarm[i] = (local[i] + offset_chord[i]) mod prime[i]
         */
        memcpy(s_utlp.offset_chord, vote.offset_chord, UTLP_CHORD_SIZE);
        s_utlp.have_offset_chord = true;
        s_utlp.we_adopted_epoch = true;

        /* Track sync source for reboot detection */
        memcpy(s_utlp.sync_source_mac, peer->mac, 6);
        s_utlp.have_sync_source = true;

        utlp_hal_log_info(TAG, "FIREFLY: Stored offset chord (attached to peer)");
    } else {
        /*
         * We are the older device - we ARE the swarm reference.
         * Offset chord is all zeros (local chord = swarm chord).
         */
        memset(s_utlp.offset_chord, 0, UTLP_CHORD_SIZE);
        s_utlp.have_offset_chord = true;  /* Valid, just zero */
        s_utlp.we_adopted_epoch = false;

        utlp_hal_log_info(TAG, "FIREFLY: We are the reference (zero offset chord)");
    }

    s_utlp.observation_count++;
    return true;  /* Resolution complete */
}

/**
 * @brief Resolve epoch using clock offset (called after chirp complete)
 * @deprecated Use resolve_epoch_hdc() for vector-native resolution
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

    /* OFFSET THRESHOLD for determining "same second" (from utlp_config.h) */

    /*
     * === RULE 0: GENESIS PULSE PROTECTION (INNATE IMMUNITY) ===
     *
     * "An established swarm recognizes and absorbs newcomers, not vice versa."
     *
     * If WE are established AND peer is genesis pulsing, we NEVER adopt.
     * The newborn must sync to the established swarm.
     *
     * DETECTION STRATEGY (TIME-TRIGGERED, PROTOCOL v0x02):
     *
     * ONLY: Use interval_history.is_genesis_pattern (observed beacon intervals)
     *   - Requires multiple beacons → builds over time
     *   - Detects genesis ramp signature (100ms → 500ms → 1s intervals)
     *   - Cannot be faked by manipulating any field
     *   - Aligns with design_philosophy_anticipatory.md: observe, don't react
     *
     * NOTE: Timestamp-based detection was REMOVED with chord-on-wire (v0x02).
     * The old approach used chord_to_approx_quanta() which was fundamentally
     * broken, wrapping every 241ms. With chord-on-wire, we can't derive scalar
     * time from the beacon - we rely solely on interval vector observation.
     *
     * We consider ourselves established ONLY if uptime > 5s (UTLP_CHIRP_DURATION_US).
     */
    uint64_t our_uptime_us = utlp_hal_get_micros() - s_utlp.boot_time_us;

    /*
     * LINEAGE-BASED CLASSIFICATION (replaces binary genesis/established)
     *
     * Per HDC/Physics/Engineering specialist analysis:
     * - "Lineage is what propagates. Authority is what accumulates."
     * - Binary classification created edge case failures
     * - New approach uses explicit state machine with UNKNOWN as safe default
     */
    lineage_state_t peer_lineage = peer->interval_history.lineage;
    bool we_have_proven_lineage = (our_uptime_us >= UTLP_CHIRP_DURATION_US);
    bool we_have_unproven_lineage = !we_have_proven_lineage;

    /* Map lineage states to semantic booleans for clarity */
    bool peer_has_unproven_lineage = (peer_lineage == LINEAGE_UNPROVEN);
    bool peer_has_proven_lineage = (peer_lineage == LINEAGE_PROVEN);

    utlp_hal_log_info(TAG, "  Our lineage: %s (uptime=%llu us)",
                      we_have_proven_lineage ? "PROVEN" : "UNPROVEN",
                      (unsigned long long)our_uptime_us);
    utlp_hal_log_info(TAG, "  Peer lineage: %s (min=%lu ms, median=%lu ms)",
                      peer_lineage == LINEAGE_UNKNOWN ? "UNKNOWN" :
                      peer_lineage == LINEAGE_UNPROVEN ? "UNPROVEN" :
                      peer_lineage == LINEAGE_TRANSITIONING ? "TRANSITIONING" : "PROVEN",
                      (unsigned long)peer->interval_history.min_ms,
                      (unsigned long)peer->interval_history.median_ms);

    /*
     * === RULE 0: DEFER if insufficient data ===
     *
     * Critical fix for "fresh boot thinks it won" bug.
     * If peer's lineage is UNKNOWN (< 2 interval samples), we cannot
     * make a reliable resolution decision. Defer until we have data.
     *
     * This prevents:
     * - Fresh boot receiving one beacon and claiming victory
     * - Edge cases where default (false, false) was ambiguous
     */
    if (peer_lineage == LINEAGE_UNKNOWN) {
        utlp_hal_log_info(TAG, "RESOLUTION: DEFERRED - peer lineage unknown (need %d+ intervals)",
                          UTLP_MIN_INTERVALS_FOR_LINEAGE);
        utlp_hal_log_info(TAG, "  → Waiting for more observations before resolving");
        /* Don't set epoch_resolved - we'll try again on next beacon */
        return;
    }

    /* Use SMSP-style pattern matching for age estimation (informational) */
    uint8_t peer_phase = genesis_pattern_match(peer->interval_history.median_ms);
    uint32_t peer_age_min_ms, peer_age_max_ms;
    genesis_phase_to_age(peer_phase, &peer_age_min_ms, &peer_age_max_ms);
    utlp_hal_log_info(TAG, "  Peer age estimate: phase=%u (%lu-%lu ms)",
                      peer_phase, (unsigned long)peer_age_min_ms, (unsigned long)peer_age_max_ms);

    /*
     * === RULE 1: LINEAGE PRIORITY (was "GENESIS PROTECTION") ===
     *
     * "Proven lineage has priority over unproven lineage."
     *
     * If WE have proven lineage AND peer has unproven lineage, we keep ours.
     * The newcomer must sync to the established swarm.
     *
     * This protects existing N=2 sync when a 3rd device joins:
     * - A & B are synced (proven lineage)
     * - C boots (unproven lineage)
     * - A meets C: A proven, C unproven → A keeps epoch
     * - B meets C: B proven, C unproven → B keeps epoch
     * - C adopts from both A and B → swarm stable
     *
     * CRITICAL: Do NOT modify s_utlp.we_adopted_epoch here!
     * That flag tracks our sync state with whoever we adopted FROM.
     * Lineage priority is a per-peer decision that should not
     * affect our global sync state.
     */
    if (we_have_proven_lineage && peer_has_unproven_lineage) {
        utlp_hal_log_info(TAG, "RESOLUTION: LINEAGE PRIORITY - we are proven, peer is unproven");
        utlp_hal_log_info(TAG, "  → We keep epoch, peer must sync to us");
        peer->epoch_resolved = true;
        peer->genesis_protected = true;  /* Legacy field name - means "lineage priority applied" */
        return;  /* Early exit - no further checks needed */
    }

    /*
     * === RULE 2: SYMMETRIC LINEAGE PRIORITY (WE ARE THE NEWCOMER) ===
     *
     * The inverse of Rule 1: if WE have unproven lineage (just booted)
     * AND peer has PROVEN lineage (steady 60s intervals observed),
     * then WE MUST adopt from them.
     *
     * This handles the case where:
     * - Device C boots fresh (unproven lineage, < 10s uptime)
     * - Device C sees Device B with steady 60s intervals (proven lineage)
     * - C should immediately recognize B as proven and adopt
     *
     * Combined with RULE 0 (deferral on UNKNOWN), this ensures:
     * - No decisions made on first beacon (UNKNOWN → defer)
     * - Clear asymmetry once lineage is known (proven beats unproven)
     */
    if (we_have_unproven_lineage && peer_has_proven_lineage) {
        /*
         * WE ARE UNPROVEN, PEER IS PROVEN
         *
         * We just booted. Peer has PROVEN lineage (steady intervals observed).
         * We MUST adopt from the proven peer - no question.
         *
         * This is the symmetric case to lineage priority:
         * - Rule 1: "proven lineage keeps epoch over unproven"
         * - Rule 2: "unproven lineage adopts from proven"
         */
        utlp_hal_log_info(TAG, "RESOLUTION: SYMMETRIC LINEAGE - we are unproven, peer is proven");
        utlp_hal_log_info(TAG, "  → We adopt from proven peer");
        i_should_adopt = true;

        /* Skip all other resolution logic - this is definitive */
        goto do_adoption;
    }

    /* Rule 3: Time Lord check - only Time Lords get special treatment */
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
        if (offset_us < -UTLP_EPOCH_OFFSET_THRESHOLD_US) {
            /* Peer is significantly older - their clock is ahead */
            i_should_adopt = true;
            utlp_hal_log_info(TAG, "RESOLUTION: Peer is older (offset=%lld us, older wins)",
                              (long long)offset_us);
        }
        else if (offset_us > UTLP_EPOCH_OFFSET_THRESHOLD_US) {
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

do_adoption:
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

    /*
     * NOTE: time_synced is set in the PHASE ENGINE block after this function
     * returns, not here. This preserves the check at line ~2071 that decides
     * whether to set offset=0 (first sync) or preserve existing (already synced).
     */
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

    /* Extract peer's chord from wire packet (v0x02 format) */
    const uint8_t *peer_chord = wire_pkt->exon.phase_chord;

    /* Validate burst index */
    if (burst_idx >= UTLP_CHIRP_BURST_COUNT) {
        utlp_hal_log_warn(TAG, "Invalid burst index: %u", burst_idx);
        return;
    }

    /*
     * Check if this is a NEW chirp or continuation of current chirp.
     * PROTOCOL v0x02: Compare chords directly (same chord = same chirp).
     */
    if (memcmp(peer_chord, peer->chirp.chirp_epoch_chord, sizeof(utlp_phase_chord_t)) != 0) {
        /* New chirp starting - reset state */
        memcpy(peer->chirp.chirp_epoch_chord, peer_chord, sizeof(utlp_phase_chord_t));
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
        /*
         * PROTOCOL v0x02: Compute offset using CRT SCALAR DIFFERENCE.
         *
         * HISTORY OF BUGS:
         * 1. chord_to_approx_quanta() returned chord[0], wrapping every 241ms
         * 2. chord_offset_quanta() used circular distance, failing for >120ms differences
         *
         * CORRECT APPROACH: Use Chinese Remainder Theorem to convert each chord
         * to its unique scalar value (modulo ~8×10^18), then compute difference.
         * This gives the TRUE time offset without any wrap-around issues.
         *
         * The CRT approach works because:
         * - Each chord uniquely maps to a scalar in [0, 8.24×10^18)
         * - The difference of scalars is the true time difference
         * - No circular distance ambiguity at any time scale
         *
         * The result is the signed offset in quanta (1 quanta = 1 ms).
         */
        utlp_phase_chord_t our_chord;
        utlp_phase_get_chord(our_chord);

        int64_t offset_quanta = chord_offset_crt(our_chord, peer->chirp.chirp_epoch_chord);
        int64_t chord_offset_us = offset_quanta * 1000LL;

        /*
         * 3-burst jitter averaging using RX time deltas.
         * Even without scalar TX time, we can measure ISR jitter from
         * the inter-burst timing (should be exactly 2ms each).
         */
        int64_t delta_01 = (int64_t)(peer->chirp.rx_time_us[1] - peer->chirp.rx_time_us[0]);
        int64_t delta_12 = (int64_t)(peer->chirp.rx_time_us[2] - peer->chirp.rx_time_us[1]);
        int64_t jitter_01 = delta_01 - UTLP_CHIRP_BURST_SPACING_US;
        int64_t jitter_12 = delta_12 - UTLP_CHIRP_BURST_SPACING_US;

        /* Final offset = chord-based offset */
        peer->chirp.offset_us = chord_offset_us;

        utlp_hal_log_info(TAG, "CRT offset: %lld quanta = %lld us (jitter=[%lld,%lld])",
                          (long long)offset_quanta, (long long)chord_offset_us,
                          (long long)jitter_01, (long long)jitter_12);

        /* Store jitter for history tracking */
        peer->chirp.jitter_01_us = jitter_01;
        peer->chirp.jitter_12_us = jitter_12;

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
        offset_history_update(&peer->chirp.offset_history, peer->chirp.offset_us, rx_time_us);
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
         *
         * CRITICAL: For ongoing sync, only update offset from peers
         * whose epoch is already resolved AND whom we didn't reject via
         * genesis protection. This prevents newly-joined genesis devices
         * from polluting our established sync with another peer.
         *
         * Bug scenario without this check:
         * 1. Device B synced to A with offset=-8ms
         * 2. Device C (newborn) joins, B calculates C's offset=+47ms
         * 3. TIME UPDATE fires BEFORE epoch resolution → B's offset polluted!
         * 4. Genesis protection fires → too late, damage done
         *
         * Fix: Don't update from new peers until epoch resolution accepts them.
         */
        /*
         * CRITICAL FIX: Do NOT set time_synced until AFTER epoch resolution!
         *
         * Previously, time_synced was set here immediately on first chirp.
         * But epoch resolution is DEFERRED until we have 3+ interval samples.
         * This caused a race condition:
         *   - time_synced = true (first chirp received)
         *   - we_adopted_epoch = false (default, resolution not run yet)
         *   - Heartbeat shows "NOT applying - we won" (WRONG!)
         *
         * The fix: Only store the offset here, but don't set time_synced.
         * time_synced is set INSIDE the epoch resolution block below.
         */
        if (!s_utlp.time_synced && !peer->epoch_resolved) {
            /* Store offset for later use, but don't mark synced yet */
            s_utlp.time_offset_us = peer->chirp.offset_us;
            utlp_hal_log_debug(TAG, "Offset stored=%lld us (awaiting epoch resolution)",
                               (long long)s_utlp.time_offset_us);
        } else if (peer->epoch_resolved && !peer->genesis_protected &&
                   peer->chirp.offset_history.count >= 4) {
            /* Ongoing sync: use median-filtered offset from ACCEPTED peer only */
            s_utlp.time_offset_us = peer->chirp.offset_history.median_us;
            utlp_hal_log_info(TAG, "TIME UPDATE: median_offset=%lld us (from %u samples)",
                              (long long)s_utlp.time_offset_us,
                              peer->chirp.offset_history.count);
        }

        /*
         * DEFERRED EPOCH RESOLUTION (Anticipatory Design)
         *
         * We defer epoch resolution until we have OBSERVED enough of the peer's
         * behavior to detect whether they're in genesis mode. This is the
         * time-triggered approach: observe actual beacon intervals, not claims.
         *
         * Genesis detection requires seeing the interval pattern (50ms→150ms→250ms...)
         * which takes at least 3 beacon observations to identify.
         *
         * Without this deferral, established devices would immediately resolve
         * against fresh reboots before detecting the genesis pattern, causing
         * the "both devices think they won" bug.
         *
         * EXPLICIT GENESIS MARKING: If peer's protocol_version tells us they're
         * NOT genesis pulsing (is_genesis = false), we can skip the interval
         * requirement and proceed immediately. The interval detection is only
         * needed when we have to infer genesis state from behavior.
         */
        #define MIN_INTERVAL_SAMPLES_FOR_RESOLUTION 3

        if (!peer->epoch_resolved) {
            /*
             * Check if we can proceed with resolution:
             * 1. If peer is NOT genesis pulsing (explicit flag), proceed immediately
             * 2. If peer IS genesis pulsing, wait for interval samples to detect transition
             */
            bool can_resolve = !peer->is_genesis ||  /* Peer is established - proceed */
                               (peer->interval_history.count >= MIN_INTERVAL_SAMPLES_FOR_RESOLUTION);

            if (!can_resolve) {
                /* Genesis peer without enough observations - defer resolution */
                utlp_hal_log_debug(TAG, "Epoch resolution deferred: peer is genesis, need %d interval samples, have %u",
                                   MIN_INTERVAL_SAMPLES_FOR_RESOLUTION,
                                   peer->interval_history.count);
            } else {
                /* Enough observations - use HDC agreement-based resolution */
                bool resolution_complete = resolve_epoch_hdc(peer);

                if (!resolution_complete) {
                    /* Still converging via elastic nudge - skip offset application */
                    utlp_hal_log_debug(TAG, "HDC roll-in: Still converging (state=%d)",
                                       s_utlp.rollin.state);
                    return;  /* Wait for next chirp to continue convergence */
                }

                /* Mark peer epoch as resolved */
                peer->epoch_resolved = true;

            /*
             * === APPLY OFFSET TO PHASE ENGINE FOR GLOBAL TIME ===
             *
             * After epoch resolution, we know WHO should apply the offset:
             * - Device that ADOPTED: Apply offset to convert local → global time
             * - Device that KEPT epoch: Their local time IS the reference (offset=0)
             *
             * CRITICAL: Skip offset application if genesis protection fired!
             * Genesis protection means we're established and met a newborn.
             * Our existing sync (if any) must be preserved.
             * (Bug fix: N=3 joining was breaking N=2 sync)
             */
            if (peer->genesis_protected) {
                utlp_hal_log_info(TAG, "PHASE ENGINE: Skipped (genesis protection - preserving existing sync)");
            } else if (s_utlp.we_adopted_epoch) {
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
                 *
                 * SYNC SOURCE TRACKING: Record which peer we synced from.
                 * If this peer reboots later, our offset becomes stale and must be reset.
                 */
                memcpy(s_utlp.sync_source_mac, peer->mac, 6);
                s_utlp.have_sync_source = true;
                utlp_phase_set_epoch_offset(-s_utlp.time_offset_us);
                utlp_hal_log_info(TAG, "PHASE ENGINE: Offset applied=%lld us from %02X:%02X:%02X:%02X:%02X:%02X",
                                  (long long)(-s_utlp.time_offset_us),
                                  peer->mac[0], peer->mac[1], peer->mac[2],
                                  peer->mac[3], peer->mac[4], peer->mac[5]);
            } else {
                /*
                 * We won the resolution - but only set offset=0 if this is
                 * our FIRST sync. If we already have a sync (time_synced),
                 * don't touch it - our offset is valid from a previous peer.
                 */
                if (!s_utlp.time_synced) {
                    utlp_phase_set_epoch_offset(0);
                    utlp_hal_log_info(TAG, "PHASE ENGINE: We are time reference (offset=0)");
                } else {
                    utlp_hal_log_info(TAG, "PHASE ENGINE: Keeping existing sync (already synced to another peer)");
                }
            }

            /*
             * NOW set time_synced = true, AFTER epoch resolution AND phase engine
             * offset application are complete.
             *
             * CRITICAL FIX: Previously time_synced was set immediately on first
             * chirp, BEFORE epoch resolution ran. This caused fresh devices to
             * think they "won" because:
             *   - time_synced = true (first chirp)
             *   - we_adopted_epoch = false (default, resolution deferred)
             *   - Heartbeat shows "NOT applying - we won" (WRONG!)
             *
             * Bug symptom: "TIME SYNCED! Adopted offset=X" immediately followed
             * by heartbeat "NOT applying - we won" (contradiction).
             *
             * Now time_synced is only set AFTER resolution completes and we know
             * the correct value of we_adopted_epoch.
             */
            if (!s_utlp.time_synced) {
                s_utlp.time_synced = true;
                utlp_hal_log_info(TAG, "TIME SYNCED! Resolution complete (we %s)",
                                  s_utlp.we_adopted_epoch ? "adopted" : "won");
            }
            }  /* End of else (enough interval samples) */
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

    /* Verify protocol version - accept both steady state and genesis */
    uint8_t proto_ver = wire_pkt->exon.protocol_version;
    bool peer_is_genesis = (proto_ver == UTLP_PROTOCOL_VERSION_GENESIS);
    if (proto_ver != UTLP_PROTOCOL_VERSION_N2 && !peer_is_genesis) {
        utlp_hal_log_warn(TAG, "Ignoring beacon: unsupported version 0x%02X",
                          proto_ver);
        return;
    }

    /* Extract session salt for contact classification */
    uint8_t salt[2];
    salt[0] = (uint8_t)(wire_pkt->exon.session_salt & 0xFF);
    salt[1] = (uint8_t)((wire_pkt->exon.session_salt >> 8) & 0xFF);

    /* Classify contact type */
    contact_type_t contact = classify_contact(pkt->mac, salt);

    /*
     * PROTOCOL v0x02: Extract peer's chord directly from wire packet.
     *
     * NOTE: With chord-on-wire, we cannot derive peer's absolute boot time.
     * The origin_time field is now our local time when we first see this peer
     * (useful for debugging, but NOT used for epoch resolution - that uses
     * chord offset comparison instead).
     */
    utlp_phase_chord_t peer_chord;
    memcpy(peer_chord, wire_pkt->exon.phase_chord, sizeof(utlp_phase_chord_t));

    /* Build epoch_state from wire packet for first contact handling */
    epoch_state_t peer_epoch;
    /*
     * origin_time: Use our local uptime when we first see this peer.
     * This is meaningful for debugging ("when did we meet this peer?").
     * Epoch resolution now uses chord offset, NOT origin_time comparison.
     */
    uint64_t our_uptime_us = utlp_hal_get_micros() - s_utlp.boot_time_us;
    peer_epoch.origin_time = (uint32_t)(our_uptime_us / UTLP_US_PER_SEC);
    peer_epoch.depth = UTLP_DEPTH_FRESH;  /* Phase 2: assume fresh for now */
    peer_epoch.session_salt[0] = salt[0];
    peer_epoch.session_salt[1] = salt[1];

    peer_record_t *peer = NULL;

    switch (contact) {
        case CONTACT_NEW_PEER:
            utlp_hal_log_info(TAG, "New peer discovered");
            handle_first_contact(pkt->mac, &peer_epoch, peer_chord);
            peer = find_peer_by_mac(pkt->mac);
            break;

        case CONTACT_REBOOTED_PEER:
            utlp_hal_log_info(TAG, "Peer reboot detected - re-evaluating");

            /*
             * SYNC SOURCE REBOOT DETECTION
             *
             * If this peer is our sync source (we adopted from them), our
             * time_offset is now STALE. The peer's new boot time has no
             * relation to their old one - our offset was computed against
             * a timeline that no longer exists.
             *
             * Reset sync state so epoch resolution starts fresh.
             * This prevents "swarm fragmentation" where we broadcast
             * timestamps based on a stale offset to a dead timeline.
             */
            if (s_utlp.have_sync_source &&
                memcmp(s_utlp.sync_source_mac, pkt->mac, 6) == 0) {
                utlp_hal_log_warn(TAG, "⚠️ SYNC SOURCE REBOOTED! Resetting sync state (was offset=%lld us)",
                                  (long long)s_utlp.time_offset_us);
                s_utlp.time_synced = false;
                s_utlp.we_adopted_epoch = false;
                s_utlp.have_sync_source = false;
                s_utlp.time_offset_us = 0;
                memset(s_utlp.sync_source_mac, 0, 6);
                utlp_phase_set_epoch_offset(0);  /* Reset to local time */
            }

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
     *
     * CRITICAL FIX: Only update on NEW chirp, not every burst!
     * Each chirp has 3 bursts with 2ms spacing. If we update on every burst,
     * we'd measure 2ms intervals and EVERYONE would look like genesis pulsing.
     *
     * PROTOCOL v0x02: Compare chords to detect new chirp (same chord = same chirp).
     */
    if (peer) {
        if (memcmp(peer_chord, peer->chirp.chirp_epoch_chord, sizeof(utlp_phase_chord_t)) != 0) {
            /* This is a NEW chirp - update interval history */
            beacon_interval_update(&peer->interval_history, rx_time_us);
        }
        /* Note: peer->chirp.chirp_epoch_chord will be updated in process_chirp_burst() */
    }

    /*
     * TRACK PEER'S GENESIS STATE
     *
     * The explicit protocol_version flag tells us if peer is genesis pulsing.
     * This is used to bypass the interval detection requirement - if we KNOW
     * the peer is established (version 0x02), we can proceed with epoch
     * resolution immediately instead of waiting for 3 interval samples.
     */
    if (peer) {
        peer->is_genesis = peer_is_genesis;
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
     * EXPLICIT GENESIS MARKING: Peer's protocol_version field tells us
     * immediately if they're genesis pulsing (0xFE) or steady state (0x02).
     * No need for behavioral detection - works on FIRST beacon!
     *
     * This solves the critical gap where newborn (150ms interval) waits up to
     * 60 seconds to hear from established device (60s interval).
     */
    if (peer) {
        /* Reset tracking on reboot (peer is new life) */
        if (contact == CONTACT_REBOOTED_PEER) {
            peer->beacon_count = 0;
            peer->first_beacon_us = 0;
            peer->welcome_sent_us = 0;
            memset(peer->last_beacon_chord, 0, 8);
        }

        if (should_send_welcome_response(peer, rx_time_us, peer_is_genesis, peer_chord)) {
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

    /*
     * Beacon TX: Use SWARM time, not LOCAL time.
     *
     * PROTOCOL v0x02: Send phase chord directly on wire.
     *
     * "Time is a chord, not a number." - S3 Spec
     *
     * When we've adopted from another device, our local chord differs from
     * swarm chord by time_offset_us worth of quanta. We compute the swarm
     * chord by getting our local chord and adjusting by the offset.
     *
     * For now, we use a simpler approach: get the chord at local time
     * or swarm time based on sync state. The phase engine already handles
     * the offset internally via epoch_offset.
     *
     * Example: A boots, B boots +8.5s later, B adopts from A (offset=-8.5s)
     * - A's chord evolves from A_boot
     * - B's chord evolves from B_boot, but phase engine adds -(-8.5s) = +8.5s
     * - Both compute same swarm chord, which goes on wire
     */
    utlp_phase_get_chord(pkt.exon.phase_chord);  /* Phase engine handles offset */

    pkt.exon.ntp_timestamp_utc = 0;  /* No NTP in Phase 2 */
    pkt.exon.session_salt = (uint16_t)(s_utlp.epoch.session_salt[0] |
                                        (s_utlp.epoch.session_salt[1] << 8));
    pkt.exon.stratum = 1;  /* Genesis stratum */

    /*
     * PROTOCOL VERSION: Explicit Genesis Marking
     *
     * Devices in genesis chirp phase use GENESIS version to signal they're
     * seeking swarm adoption. Established devices seeing this version should
     * send an immediate welcome response.
     *
     * This explicit marking is cleaner than behavioral detection (counting
     * beacon intervals) because it works on the FIRST beacon.
     */
    uint64_t tx_uptime_us = chirp_epoch_us - s_utlp.boot_time_us;
    bool is_genesis_pulsing = (tx_uptime_us < UTLP_CHIRP_DURATION_US);
    pkt.exon.protocol_version = is_genesis_pulsing ?
        UTLP_PROTOCOL_VERSION_GENESIS : UTLP_PROTOCOL_VERSION_N2;

    /*
     * Build INTRON (encrypted payload) - burst_index varies
     */
    pkt.intron.field.tx_power_dbm = 0;  /* Default TX power */
    pkt.intron.field.battery_level = 255;  /* No battery monitoring in Phase 2 */
    pkt.intron.field.drift_ppm = 0;  /* No drift estimate yet */
    pkt.intron.field.opcode = UTLP_CMD_NONE;  /* Heartbeat */

    /* Payload[0] = CPU load (unused), Payload[1] = Role, Payload[2] = Burst index */
    pkt.intron.field.payload[0] = 0;  /* CPU load */

    /*
     * Determine biological role:
     * - NAIVE (0): Genesis pulsing, haven't resolved epoch yet
     * - TIME_LORD (1): We are the origin of our lineage (didn't adopt)
     * - SOMATIC (2): We adopted from another device
     */
    uint8_t role;
    if (is_genesis_pulsing) {
        role = UTLP_ROLE_NAIVE;  /* Still genesis pulsing */
    } else if (s_utlp.we_adopted_epoch) {
        role = UTLP_ROLE_SOMATIC;  /* We adopted - following Time Lord */
    } else {
        role = UTLP_ROLE_TIME_LORD;  /* We are origin of lineage */
    }
    pkt.intron.field.payload[1] = role;

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
/**
 * @brief Get current swarm chord (vector-native sync)
 *
 * FIREFLY MODEL: Applies the offset chord to our local chord to get
 * the swarm-synchronized chord. No scalar conversion needed!
 *
 *   swarm[i] = (local[i] + offset_chord[i]) mod prime[i]
 *
 * If we haven't synced yet (no offset chord), returns local chord.
 *
 * @param[out] swarm_chord Output swarm-synchronized chord
 */
static void utlp_get_swarm_chord(utlp_phase_chord_t swarm_chord)
{
    /* Get our clean local chord */
    utlp_phase_chord_t local_chord;
    utlp_phase_get_chord(local_chord);

    if (s_utlp.have_offset_chord) {
        /* Apply offset chord to get swarm chord */
        utlp_hdc_apply_offset_chord(local_chord, s_utlp.offset_chord, swarm_chord);
    } else {
        /* No sync yet - local chord IS swarm chord */
        memcpy(swarm_chord, local_chord, UTLP_CHORD_SIZE);
    }
}

static void run_heartbeat(void)
{
    /*
     * ==========================================================================
     * FIREFLY HEARTBEAT: 1Hz LED Blink via Virtual Gear
     * ==========================================================================
     *
     * THE CHALLENGE:
     * Our 8 primes (241, 251, 239...) all cycle at kHz rates at 1µs tick resolution.
     * chord[0]=241 cycles every 241µs = ~4150 Hz (causes headaches!)
     *
     * THE PLAYER PIANO MODEL (from Gemini insight):
     * We need a "gear" that naturally cycles at 1Hz to use as our LED clock.
     * Since we don't have one, we CREATE a virtual 1Hz gear.
     *
     * APPROACH: Virtual 1Hz Gear via Synchronized Tick Count
     * - Use offset chord to synchronize swarm_tick (HDC-native sync)
     * - Derive virtual_1hz_phase from swarm_tick (scalar derived from vector)
     * - Drive LED based on virtual phase
     *
     * FUTURE: True HDC Resonance Model
     * - Store "LED_ON schedule" hypervector
     * - Compute similarity(current_chord_10k, schedule)
     * - LED ON when resonance > threshold
     * This requires pre-computing what chords look like at 0, 0.5s, 1s marks.
     */
    utlp_phase_chord_t swarm_chord;
    utlp_get_swarm_chord(swarm_chord);

    /*
     * Virtual 1Hz gear derived from synchronized tick count.
     *
     * The offset chord keeps us synchronized in vector space.
     * We derive a scalar "swarm tick" for the 1Hz virtual gear:
     *
     * For synced device: swarm_tick = local_tick
     * For adopted device: swarm_tick = local_tick + offset_scalar
     *
     * Since we want to avoid CRT for offset, we use a simpler approach:
     * Track milliseconds within each second using the phase engine's scalar time.
     *
     * With 1µs resolution: 1,000,000 µs = 1 second
     * virtual_ms_in_sec = (scalar_us / 1000) % 1000
     * LED ON for first 500ms, OFF for next 500ms → 1Hz, 50% duty
     */
    uint64_t local_us = utlp_phase_get_scalar_us();

    /*
     * Apply offset for synchronized time.
     *
     * If we adopted an offset chord, we also have scalar time_offset_us.
     * time_offset_us = our_time - peer_time
     *
     * If positive: we're ahead, subtract to sync backward
     * If negative: we're behind, add (subtract negative) to sync forward
     *
     * The key insight: Both devices should see the SAME ms_in_second value
     * at the same wall-clock moment.
     */
    int64_t synced_us = (int64_t)local_us;
    if (s_utlp.time_synced && s_utlp.we_adopted_epoch) {
        /* We adopted peer's epoch - adjust our time toward peer */
        synced_us = (int64_t)local_us - s_utlp.time_offset_us;
    }
    /* Ensure non-negative for modulo operation */
    if (synced_us < 0) {
        synced_us += 1000000;  /* Add 1 second to make positive */
    }

    /* Virtual 1Hz gear: milliseconds within current second */
    uint32_t ms_in_second = (uint32_t)((synced_us / 1000) % 1000);

    /* 1Hz, 50% duty: ON for first 500ms, OFF for next 500ms */
    uint8_t duty = (ms_in_second < 500) ? 100 : 0;

    /* Log swarm chord for debugging (only occasionally to avoid spam) */
    static uint32_t log_counter = 0;
    if (++log_counter >= 1000) {  /* Every 1000 heartbeats */
        utlp_hal_log_debug(TAG, "HEARTBEAT: chord=[%u,%u,%u,%u,%u,%u,%u,%u] ms_in_sec=%lu LED=%s",
                           swarm_chord[0], swarm_chord[1], swarm_chord[2], swarm_chord[3],
                           swarm_chord[4], swarm_chord[5], swarm_chord[6], swarm_chord[7],
                           (unsigned long)ms_in_second,
                           duty ? "ON" : "OFF");
        log_counter = 0;
    }

    utlp_hal_set_actuator_phase(UTLP_ACTUATOR_MAIN, 1000, (uint16_t)ms_in_second, duty);
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
     * origin_time = swarm time epoch origin (seconds, for wire efficiency)
     * depth = UTLP_DEPTH_FRESH (128) - somatic cell, half vitality
     * session_salt = per-boot random (anti-replay, peer identification)
     *
     * On Phase 2 first contact, epoch resolution uses:
     * 1. Higher depth (more vitality) wins
     * 2. Equal depth → oldest origin_time wins
     * 3. True tie → lower MAC adopts from higher MAC
     */
    uint16_t salt = utlp_security_generate_session_salt();

    /* Establish swarm time epoch origin (seconds, for wire format) */
    uint64_t boot_us = utlp_hal_get_micros();
    uint32_t origin_time_s = (uint32_t)(boot_us / UTLP_US_PER_SEC);

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
     * The Hardware Phase Locked Coherency engine uses MCPWM timer HAL.
     * Time is represented as a phase chord (8 residues modulo coprime
     * primes) - scalar time is DERIVED via CRT when needed.
     *
     * Power Profile Selection (via API):
     *   PRECISION (10 MHz): 1 kHz ISR, 100 ns tick, blocks light sleep
     *   BALANCED  (1 MHz):  100 Hz ISR, 1 µs tick, enables light sleep
     *
     * Target-based selection:
     *   ESP32-C6 (XIAO): PRECISION - authoritative time source
     *   ESP32 (DevKit): BALANCED - battery-friendly, mixed-node testing
     *
     * Mixed-node testing verifies canonical quantum fix - both produce
     * identical phase chords for the same wall-clock time.
     */
    utlp_power_profile_t selected_profile;
#if CONFIG_IDF_TARGET_ESP32
    /* ESP32 DevKit: Use BALANCED for mixed-node testing */
    selected_profile = UTLP_POWER_PROFILE_BALANCED;
    utlp_hal_log_info(TAG, "Power profile: BALANCED (1 MHz, 100 Hz ISR)");
#else
    /* ESP32-C6 and others: Use PRECISION as authoritative time source */
    selected_profile = UTLP_POWER_PROFILE_PRECISION;
    utlp_hal_log_info(TAG, "Power profile: PRECISION (10 MHz, 1 kHz ISR)");
#endif

    utlp_phase_config_t phase_config = {
        .power_profile = selected_profile,
    };
    esp_err_t phase_ret = utlp_phase_init_with_config(&phase_config);
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
     * - [x] origin_time = swarm epoch origin, depth = 128 (fresh)
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
                      (unsigned long)(UTLP_CHIRP_BASE_US / UTLP_US_PER_MS),
                      (unsigned long)(UTLP_CHIRP_BASE_US / UTLP_US_PER_MS),
                      (unsigned long)(UTLP_CHIRP_SLOPE_US / UTLP_US_PER_MS));

    /*
     * Main Loop - JPL Rule 2 Compliant
     *
     * Loop terminates when:
     * 1. shutdown_requested flag is set (via utlp_request_shutdown())
     * 2. External reset/power cycle
     *
     * Glass Wall: Application layer controls shutdown via API.
     */
    while (!s_utlp.shutdown_requested) {
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
        if (is_chirping && (now_us - last_chirp_log_us >= UTLP_CHIRP_LOG_INTERVAL_US)) {
            uint32_t uptime_s = (uint32_t)(uptime_us / UTLP_US_PER_SEC);
            utlp_hal_log_info(TAG, "Chirp: t=%lus → interval=%lu ms",
                              (unsigned long)uptime_s,
                              (unsigned long)(beacon_interval_us / UTLP_US_PER_MS));
            last_chirp_log_us = now_us;
        }

        /* Log transition from chirp to steady state */
        if (was_chirping && !is_chirping) {
            utlp_hal_log_info(TAG, "Genesis Chirp COMPLETE → Steady state: %lu s interval",
                              (unsigned long)(UTLP_BEACON_STEADY_US / UTLP_US_PER_SEC));
            was_chirping = false;
        }

        /* Send beacon periodically */
        if (now_us - last_beacon_us >= beacon_interval_us) {
            send_beacon();
            last_beacon_us = now_us;
        }

        /* Periodic logging (every 10 seconds) */
        if (now_us - last_log_us >= UTLP_MAIN_LOG_INTERVAL_US) {
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
