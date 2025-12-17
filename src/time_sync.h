/**
 * @file time_sync.h
 * @brief Hybrid time synchronization for bilateral motor coordination
 *
 * @defgroup time_sync Time Synchronization Module
 * @{
 *
 * @section ts_overview Overview
 *
 * This module implements a PTP-inspired (IEEE 1588) time synchronization protocol
 * for coordinating bilateral motor activation between two ESP32-C6 peer devices.
 * Achieves ±30 microseconds drift over 90-minute sessions using only BLE.
 *
 * @section ts_arduino Arduino Developers: Key Differences
 *
 * | Arduino Way | ESP-IDF Way (This Code) |
 * |-------------|-------------------------|
 * | `millis()` | `esp_timer_get_time()` (microseconds, 64-bit) |
 * | `delay()` | `vTaskDelay(pdMS_TO_TICKS(ms))` (FreeRTOS, non-blocking) |
 * | Global variables | Structured state with mutex protection |
 * | Single loop() | Multiple FreeRTOS tasks running concurrently |
 * | BLE libraries | NimBLE stack with GATT services |
 *
 * @section ts_architecture Architecture
 *
 * The protocol uses a "pattern broadcast" approach inspired by emergency vehicle
 * light bars (Feniex, Whelen). Instead of sending "activate NOW" commands:
 *
 * @code{.unparsed}
 *   SERVER broadcasts: "Pattern epoch = T, period = 2000ms"
 *   CLIENT calculates:  "I activate at T + 1000ms (antiphase)"
 *   Both execute independently from shared reference
 * @endcode
 *
 * This eliminates feedback oscillation and tolerates BLE dropouts gracefully.
 *
 * @section ts_protocol Protocol Layers
 *
 * 1. **Initial Handshake** - NTP-style 4-timestamp exchange for precise bootstrap
 * 2. **Periodic Beacons** - SERVER sends one-way timestamps every 10-60s
 * 3. **EMA Filter** - Smooths BLE jitter (30% fast-attack, 10% steady-state)
 * 4. **Motor Epoch** - Shared timing reference for bilateral alternation
 *
 * @section ts_jpl JPL Coding Standard Compliance
 *
 * - **Rule 1:** Static allocation only (no malloc/free at runtime)
 * - **Rule 2:** All loops have bounded iteration counts
 * - **Rule 3:** All timing uses vTaskDelay() (no busy-wait spin loops)
 * - **Rule 5:** Every function returns esp_err_t, caller must check
 * - **Rule 8:** Task subscribes to watchdog, feeds regularly
 *
 * @see docs/adr/0043-filtered-time-synchronization.md
 * @see docs/Bilateral_Time_Sync_Protocol_Technical_Report.md
 *
 * @version 0.6.122
 * @date 2025-12-14
 * @author Claude Code (Anthropic) - Sonnet 4, Sonnet 4.5, Opus 4.5
 */

#ifndef TIME_SYNC_H
#define TIME_SYNC_H

#include <stdint.h>
#include <stdbool.h>
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/*******************************************************************************
 * CONSTANTS AND CONFIGURATION
 ******************************************************************************/

/** @brief Time sync beacon message size (bytes) - Pattern-broadcast (AD045) expanded from 23 to 25 */
#define TIME_SYNC_MSG_SIZE          (25U)

/** @brief Minimum sync interval (milliseconds) - fast startup (Phase 6r) */
#define TIME_SYNC_INTERVAL_MIN_MS   (1000U)     // 1 second (10× faster convergence)

/** @brief Maximum sync interval (milliseconds) - steady state */
#define TIME_SYNC_INTERVAL_MAX_MS   (60000U)    // 60 seconds

/** @brief Minimum asymmetry samples before applying correction (v0.6.97) */
#define TIME_SYNC_MIN_ASYMMETRY_SAMPLES (3U)    // Need 3 valid samples for reliable EMA

/** @brief Maximum RTT for asymmetry sample to be valid (microseconds) */
#define TIME_SYNC_ASYMMETRY_RTT_MAX_US  (80000U) // 80ms - reject congested samples

/** @brief Sync interval step size for exponential backoff */
#define TIME_SYNC_INTERVAL_STEP_MS  (10000U)    // 10 second increments

/** @brief Drift threshold for resync (microseconds) */
#define TIME_SYNC_DRIFT_THRESHOLD_US (50000U)   // 50ms (half of ±100ms spec)

/** @brief Maximum sync retry attempts (JPL Rule 2: bounded loops) */
#define TIME_SYNC_MAX_RETRIES       (3U)

/** @brief Sync timeout per attempt (milliseconds) */
#define TIME_SYNC_TIMEOUT_MS        (1000U)     // 1 second

/** @brief Sync quality evaluation window (number of samples) */
#define TIME_SYNC_QUALITY_WINDOW    (10U)

/** @brief EWMA smoothing factor for clock offset (percentage, 0-100)
 *
 * EWMA (Exponentially Weighted Moving Average) reduces oscillation from BLE jitter:
 *   new_offset = (alpha/100)*sample + (1 - alpha/100)*old_offset
 *
 * Values:
 *   100 = No smoothing (raw samples)
 *   50  = Equal weight (responsive but some smoothing)
 *   25  = Heavy smoothing (stable but slower to track drift)
 *
 * Recommended: 25-35% for BLE time sync (balances stability vs responsiveness)
 */
#define TIME_SYNC_EWMA_ALPHA_PCT    (30U)       // 30% weight on new sample

/** @brief ESP32-C6 crystal drift specification (parts per million) */
#define TIME_SYNC_CRYSTAL_DRIFT_PPM (10U)       // ±10 PPM from datasheet

/** @brief Phase 6r: EMA filter alpha - fast attack (percentage, 0-100) */
#define TIME_FILTER_ALPHA_FAST_PCT  (30U)       // 30% weight for first N samples (fast convergence)

/** @brief Phase 6r: EMA filter alpha - slow/steady (percentage, 0-100) - heavy smoothing */
#define TIME_FILTER_ALPHA_PCT       (10U)       // 10% weight on new sample (90% on history)

/** @brief Phase 6r: Ring buffer size for outlier detection */
#define TIME_FILTER_RING_SIZE       (8U)        // Last 8 samples

/** @brief Phase 6r: Outlier threshold (microseconds) - reject samples >100ms deviation */
#define TIME_FILTER_OUTLIER_THRESHOLD_US (100000U)  // 100ms (steady-state mode)

/** @brief Phase 6r: Fast-mode outlier threshold (microseconds) - more aggressive during mode changes */
#define TIME_FILTER_OUTLIER_THRESHOLD_FAST_US (50000U)  // 50ms (fast-attack mode)

/** @brief Phase 6r: Early convergence detection threshold (microseconds) */
#define TIME_FILTER_CONVERGENCE_THRESHOLD_US (50U)  // 50µs stability over 4 beacons

/*******************************************************************************
 * TYPE DEFINITIONS
 ******************************************************************************/

/**
 * @brief Phase 6r: Time sample for ring buffer (AD043)
 *
 * Stores individual beacon measurements for debugging and outlier detection.
 */
typedef struct {
    int64_t  raw_offset_us;      /**< Raw offset measurement (rx_time - server_time) */
    uint64_t timestamp_us;       /**< When this sample was taken */
    uint8_t  sequence;           /**< Beacon sequence number */
    bool     outlier;            /**< True if rejected as outlier (>200ms deviation) */
} time_sample_t;

/**
 * @brief Phase 6r: EMA filter state (AD043 - Filtered Time Sync)
 *
 * Implements exponential moving average filter with ring buffer for
 * outlier detection. Smooths out BLE transmission delay variation
 * (±10-30ms typical) while rejecting extreme outliers (>100ms).
 *
 * Dual-alpha fast-attack:
 * - Fast alpha (30%) for first N valid beacons (N=12 or early convergence)
 * - Slow alpha (10%) for long-term stability after convergence
 *
 * JPL Rule 1: Fixed size ring buffer, no dynamic allocation.
 */
typedef struct {
    time_sample_t samples[TIME_FILTER_RING_SIZE];  /**< Ring buffer of recent samples */
    uint8_t       head;                             /**< Next write index (0-7) */
    int64_t       filtered_offset_us;               /**< Smoothed offset estimate */
    uint32_t      sample_count;                     /**< Total samples processed */
    uint32_t      outlier_count;                    /**< Samples rejected as outliers */
    bool          initialized;                      /**< Filter has first sample */
    bool          fast_attack_active;               /**< True until switched to slow alpha */
    uint8_t       valid_beacon_count;               /**< Count of non-outlier beacons (for N=12 check) */
} time_filter_t;

/**
 * @brief Time synchronization states
 *
 * State machine for sync protocol lifecycle. Designed per JPL Rule 2
 * to prevent unbounded operation.
 */
typedef enum {
    SYNC_STATE_INIT = 0,        /**< Waiting for connection */
    SYNC_STATE_CONNECTED,        /**< Initial sync pending */
    SYNC_STATE_SYNCED,          /**< Normal operation, periodic sync active */
    SYNC_STATE_DRIFT_DETECTED,  /**< Excessive drift, resync needed */
    SYNC_STATE_DISCONNECTED,    /**< Using last sync reference */
    SYNC_STATE_ERROR,           /**< Sync failed, fallback mode */
    SYNC_STATE_MAX              /**< Sentinel for bounds checking */
} sync_state_t;

/**
 * @brief Device role for time synchronization
 */
typedef enum {
    TIME_SYNC_ROLE_NONE = 0,    /**< No role assigned yet */
    TIME_SYNC_ROLE_SERVER,      /**< Sends sync beacons (higher battery device) */
    TIME_SYNC_ROLE_CLIENT,      /**< Receives sync beacons (lower battery device) */
    TIME_SYNC_ROLE_MAX          /**< Sentinel for bounds checking */
} time_sync_role_t;

/**
 * @brief Sync quality metrics
 *
 * Tracks synchronization accuracy over time for adaptive interval
 * adjustment and diagnostic logging.
 *
 * NTP-style: Tracks offset DRIFT (stability), not absolute offset magnitude.
 */
typedef struct {
    uint32_t samples_collected;             /**< Number of sync samples */
    int32_t  avg_drift_us;                  /**< Average drift (offset change between beacons, μs) */
    uint32_t std_deviation_us;              /**< Standard deviation (μs) */
    uint32_t max_drift_us;                  /**< Maximum observed drift (μs) */
    uint32_t sync_failures;                 /**< Count of failed sync attempts */
    uint32_t last_rtt_us;                   /**< Last round-trip time (μs) */
    uint8_t  quality_score;                 /**< 0-100% quality metric */
} time_sync_quality_t;

/**
 * @brief Time synchronization state structure
 *
 * JPL Rule 1: All fields statically allocated, no pointers to heap.
 * This structure maintains the complete state for hybrid time sync.
 */
typedef struct {
    /* Timing References (NTP-style: absolute timestamps) */
    uint64_t server_ref_time_us;     /**< SERVER's reference timestamp */
    int64_t  clock_offset_us;        /**< Calculated offset (CLIENT - SERVER) */
    uint32_t last_sync_ms;           /**< When last sync occurred (milliseconds since boot) */

    /* Sync Protocol State */
    sync_state_t state;              /**< Current sync state */
    time_sync_role_t  role;          /**< Device role (SERVER or CLIENT) */
    uint32_t sync_interval_ms;       /**< Current sync interval (adaptive) */
    uint8_t  sync_sequence;          /**< Message sequence number (wraps at 255) */
    uint8_t  retry_count;            /**< Current retry attempt (bounded by MAX_RETRIES) */

    /* Bug #62: Removed forced_beacon_count and forced_beacon_next_ms
     * Beacon blasting doesn't help EMA convergence, single beacon suffices.
     */

    /* Quality Metrics */
    time_sync_quality_t quality;     /**< Sync quality tracking */

    /* Phase 6r: EMA filter for one-way timestamp smoothing (AD043) */
    time_filter_t filter;            /**< Exponential moving average filter */

    /* Flags */
    bool     initialized;            /**< Module initialization complete */
    bool     sync_in_progress;       /**< Sync operation active */
    bool     drift_detected;         /**< Excessive drift flag */
    bool     handshake_complete;     /**< Initial NTP-style handshake done (precise bootstrap) */
    uint64_t handshake_t1_us;        /**< CLIENT: Stored T1 for RTT calculation */

    /* Beacon-to-beacon drift tracking (separate from handshake offset) */
    int64_t  last_beacon_offset_us;  /**< Last beacon's raw offset for drift calculation */
    bool     last_beacon_valid;      /**< Whether last_beacon_offset_us is valid */

    /* JPL Rule 2: Bounded operation tracking */
    uint32_t total_syncs;            /**< Total sync operations (diagnostic) */
    uint32_t session_start_ms;       /**< Session start time for drift calculation */

    /* Bilateral Motor Coordination (Phase 2) */
    uint64_t motor_epoch_us;         /**< When SERVER started motor cycles (synchronized time) */
    uint32_t motor_cycle_ms;         /**< Current motor cycle period (e.g., 2000ms for Mode 0) */
    bool     motor_epoch_valid;      /**< Whether motor epoch has been set by SERVER */

    /* Beacon timestamp for NTP-style pairing */
    uint64_t last_beacon_time_us;    /**< CLIENT: Time when last beacon was received (T2) */
    /* AD045: drift_rate fields removed - EMA filter provides ±30μs accuracy */

    /* IEEE 1588 Bidirectional Path Asymmetry Correction (v0.6.97) */
    int64_t  asymmetry_us;           /**< EMA-filtered path asymmetry (fwd + rev offset) */
    uint32_t asymmetry_sample_count; /**< Number of valid asymmetry samples received */
    bool     asymmetry_valid;        /**< True after MIN_ASYMMETRY_SAMPLES collected */
} time_sync_state_t;

/**
 * @brief Time sync beacon message structure (AD045 - Pattern-Broadcast Architecture)
 *
 * Transmitted by SERVER to CLIENT for periodic synchronization.
 * Fixed 25-byte size for efficient BLE notification.
 *
 * JPL Rule 1: Fixed size, no dynamic allocation.
 *
 * Pattern-broadcast (Emergency Vehicle architecture adaptation):
 * - SERVER broadcasts pattern once: epoch, period, duty, mode_id
 * - Both devices calculate independently from shared pattern
 * - CLIENT applies half-cycle antiphase offset
 * - No cycle-by-cycle corrections needed
 *
 * Benefits over correction-based approaches:
 * - Eliminates correction death spirals
 * - Both ends know what time it is, both know the pattern
 * - Execute independently in perfect sync (Feniex philosophy)
 */
typedef struct __attribute__((packed)) {
    uint64_t server_time_us;         /**< SERVER's current time (microseconds) - one-way timestamp */
    uint64_t motor_epoch_us;         /**< Pattern start time (Phase 3) */
    uint32_t motor_cycle_ms;         /**< Pattern period (Phase 3) */
    uint8_t  duty_percent;           /**< Motor ON time as % of half-cycle (25-50% typical) */
    uint8_t  mode_id;                /**< Mode identifier (0-4) for validation */
    uint8_t  sequence;               /**< Sequence number (for ordering) */
    uint16_t checksum;               /**< CRC-16 for integrity */
} time_sync_beacon_t;

/*******************************************************************************
 * UTLP INTEGRATION STRUCTURES (AD047)
 ******************************************************************************/

/** @brief UTLP magic bytes for beacon v2 detection */
#define UTLP_MAGIC_BYTE_0       (0xFEU)
#define UTLP_MAGIC_BYTE_1       (0xFEU)

/** @brief UTLP stratum values */
#define UTLP_STRATUM_GPS        (0U)    /**< GPS/atomic time source */
#define UTLP_STRATUM_PHONE      (1U)    /**< Phone network time (cellular/NTP) */
#define UTLP_STRATUM_PEER_1     (2U)    /**< One hop from phone */
#define UTLP_STRATUM_PEER_ONLY  (255U)  /**< No external time source */

/**
 * @brief UTLP-enhanced time sync beacon (v2)
 *
 * Extends time_sync_beacon_t with UTLP stratum and quality fields for:
 * - Time source hierarchy (GPS > phone > peer)
 * - Battery-based quality metric (Swarm Rule for leader election)
 *
 * Backward compatibility: v1 beacons start with server_time_us (8 bytes).
 * v2 beacons start with magic bytes 0xFE, 0xFE - detect by checking first 2 bytes.
 *
 * @see docs/UTLP_Specification.md
 */
typedef struct __attribute__((packed)) {
    uint8_t  magic[2];               /**< UTLP identifier: 0xFE, 0xFE */
    uint8_t  stratum;                /**< Time source stratum (0=GPS, 1=phone, 255=peer-only) */
    uint8_t  quality;                /**< Battery level 0-100 (Swarm Rule) */
    uint64_t server_time_us;         /**< SERVER's current time (microseconds) */
    uint64_t motor_epoch_us;         /**< Pattern start time */
    uint32_t motor_cycle_ms;         /**< Pattern period */
    uint8_t  mode_id;                /**< Mode identifier (0-6) */
    uint8_t  sequence;               /**< Sequence number (for ordering) */
    uint16_t checksum;               /**< CRC-16 for integrity */
} time_sync_beacon_v2_t;             /**< 29 bytes total */

/**
 * @brief PWA time injection structure
 *
 * Allows PWA to inject GPS/cellular time into devices for improved sync accuracy.
 * The device ALWAYS adopts this time (no stratum comparison) because we only need
 * devices to agree on "when seconds change", not absolute UTC correctness.
 *
 * @see docs/bilateral_pattern_playback_architecture.md
 */
typedef struct __attribute__((packed)) {
    uint8_t  stratum;                /**< Source stratum: 0=GPS, 1=network time */
    uint8_t  quality;                /**< Signal quality 0-100 (GPS accuracy indicator) */
    uint64_t utc_time_us;            /**< Microseconds since Unix epoch (1970-01-01) */
    int32_t  uncertainty_us;         /**< Estimated uncertainty (± microseconds) */
} pwa_time_inject_t;                 /**< 14 bytes total */

/*******************************************************************************
 * PUBLIC API FUNCTIONS
 ******************************************************************************/

/**
 * @brief Initialize time synchronization module
 *
 * Prepares the time sync module for operation. Must be called before any
 * other time sync functions. Initializes state to SYNC_STATE_INIT.
 *
 * @par Arduino Equivalent
 * This is like calling `BLE.begin()` in Arduino BLE libraries, but for our
 * custom time sync protocol. ESP-IDF separates initialization from operation.
 *
 * @par Example Usage
 * @code{.c}
 * // In main.c after BLE role is determined
 * peer_role_t role = ble_get_peer_role();
 * time_sync_role_t ts_role = (role == PEER_ROLE_SERVER)
 *                            ? TIME_SYNC_ROLE_SERVER
 *                            : TIME_SYNC_ROLE_CLIENT;
 *
 * esp_err_t err = time_sync_init(ts_role);
 * if (err != ESP_OK) {
 *     ESP_LOGE(TAG, "Time sync init failed: %s", esp_err_to_name(err));
 *     // Handle error - cannot proceed without time sync
 * }
 * @endcode
 *
 * @pre BLE connection established and peer role determined
 * @post Module ready for time_sync_on_connection() call
 *
 * @param[in] role Device role (TIME_SYNC_ROLE_SERVER or TIME_SYNC_ROLE_CLIENT)
 *
 * @return
 * - ESP_OK: Success
 * - ESP_ERR_INVALID_ARG: Role is TIME_SYNC_ROLE_NONE or invalid
 * - ESP_ERR_INVALID_STATE: Already initialized (call time_sync_deinit() first)
 *
 * @note JPL Rule 5: Always check return value
 * @see time_sync_deinit() to reset module state
 * @see ble_get_peer_role() to determine device role
 */
esp_err_t time_sync_init(time_sync_role_t role);

/**
 * @brief Deinitialize time synchronization module
 *
 * Cleans up time sync resources and resets state.
 *
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_STATE if not initialized
 */
esp_err_t time_sync_deinit(void);

/**
 * @brief Establish initial time sync on connection
 *
 * Called by both devices immediately after peer BLE connection.
 * Initializes NTP-style synchronization (no common reference needed).
 *
 * For SERVER: Prepares to send sync beacons with absolute timestamps.
 * For CLIENT: Waits for SERVER beacon to establish initial offset.
 *
 * JPL Rule 5: Explicit error checking required.
 *
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_STATE if not in INIT state
 */
esp_err_t time_sync_on_connection(void);

/**
 * @brief Handle disconnection event
 *
 * Transitions to SYNC_STATE_DISCONNECTED. Phase 6r: Preserves motor epoch
 * and drift rate for continuation during brief disconnects.
 *
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_STATE if not in synchronized state
 */
esp_err_t time_sync_on_disconnection(void);

/**
 * @brief Handle reconnection event with role swap detection
 *
 * Called when BLE peer connection is re-established. Conditionally clears
 * motor epoch data if role changed between connections (Phase 6r).
 *
 * Phase 6n ensures roles are preserved on reconnection, so role swap should
 * NOT occur. If detected, logs warning and clears epoch to prevent corruption.
 *
 * @param new_role Device role after reconnection (SERVER or CLIENT)
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_STATE if not initialized
 */
esp_err_t time_sync_on_reconnection(time_sync_role_t new_role);

/**
 * @brief Update time synchronization (periodic call)
 *
 * Called periodically by SERVER to send sync beacons and by CLIENT to
 * monitor drift. Implements exponential backoff for sync intervals.
 *
 * JPL Rule 3: Uses vTaskDelay() internally, never busy-waits.
 * JPL Rule 5: Returns error code for checking.
 *
 * For SERVER:
 * - Checks if sync interval elapsed
 * - Sends sync beacon to CLIENT
 * - Updates quality metrics
 *
 * For CLIENT:
 * - Monitors clock drift
 * - Requests resync if drift exceeds threshold
 * - Updates quality metrics
 *
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_STATE if not initialized
 * @return ESP_ERR_TIMEOUT if sync operation timed out
 * @return ESP_FAIL if sync send/receive failed
 */
esp_err_t time_sync_update(void);

/**
 * @brief Get synchronized time
 *
 * Returns the current synchronized time in microseconds. For SERVER, this
 * is simply the local esp_timer value. For CLIENT, this is local time
 * adjusted by the calculated clock offset.
 *
 * JPL Rule 5: Returns error code, time via pointer parameter.
 * JPL Rule 7: Pointer parameter checked for NULL.
 *
 * @param sync_time_us [out] Pointer to store synchronized time
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_ARG if sync_time_us is NULL
 * @return ESP_ERR_INVALID_STATE if not synchronized
 */
esp_err_t time_sync_get_time(uint64_t *sync_time_us);

/**
 * @brief Process received sync beacon (CLIENT only)
 *
 * Called by CLIENT when sync beacon received from SERVER via BLE.
 * Updates clock offset calculation and quality metrics.
 *
 * JPL Rule 5: Returns error code for checking.
 * JPL Rule 7: Validates beacon pointer.
 *
 * @param beacon Pointer to received beacon message
 * @param receive_time_us Local timestamp when beacon received
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_ARG if beacon is NULL
 * @return ESP_ERR_INVALID_STATE if not CLIENT role
 * @return ESP_ERR_INVALID_CRC if beacon checksum fails
 */
esp_err_t time_sync_process_beacon(const time_sync_beacon_t *beacon, uint64_t receive_time_us);

/**
 * @brief Generate sync beacon (SERVER only)
 *
 * Creates a sync beacon message for transmission to CLIENT.
 *
 * JPL Rule 5: Returns error code for checking.
 * JPL Rule 7: Validates beacon pointer.
 *
 * @param beacon [out] Pointer to beacon structure to populate
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_ARG if beacon is NULL
 * @return ESP_ERR_INVALID_STATE if not SERVER role
 */
esp_err_t time_sync_generate_beacon(time_sync_beacon_t *beacon);

/**
 * @brief Finalize beacon timestamp just before BLE transmission
 *
 * Bug #76 (PTP Hardening): Updates server_time_us (T1) and recalculates CRC
 * as late as possible to minimize timestamp-to-transmission asymmetry.
 *
 * Call this right before ble_hs_mbuf_from_flat() in ble_send_time_sync_beacon().
 *
 * @param beacon Pointer to beacon struct to update
 */
void time_sync_finalize_beacon_timestamp(time_sync_beacon_t *beacon);

/**
 * @brief Get current sync quality metrics
 *
 * Returns quality metrics for diagnostic logging and adaptive sync interval
 * adjustment.
 *
 * @param quality [out] Pointer to quality structure to populate
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_ARG if quality is NULL
 * @return ESP_ERR_INVALID_STATE if not initialized
 */
esp_err_t time_sync_get_quality(time_sync_quality_t *quality);

/**
 * @brief Get current synchronization state
 *
 * Returns the current state of the time sync state machine.
 *
 * @return Current sync state (SYNC_STATE_*)
 */
sync_state_t time_sync_get_state(void);

/**
 * @brief Get device role
 *
 * Returns the assigned device role for time synchronization.
 *
 * @return Current role (TIME_SYNC_ROLE_*)
 */
time_sync_role_t time_sync_get_role(void);

/**
 * @brief Get current clock offset
 *
 * Returns the calculated clock offset between CLIENT and SERVER.
 * For CLIENT: offset = CLIENT_time - SERVER_time
 * For SERVER: offset is always 0 (self-reference)
 *
 * NTP-style: Offset magnitude can be large (seconds) - this is normal.
 * What matters is offset stability (drift), not magnitude.
 *
 * @param offset_us [out] Pointer to store clock offset in microseconds (int64_t for unlimited range)
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_ARG if offset_us is NULL
 * @return ESP_ERR_INVALID_STATE if not synchronized
 */
esp_err_t time_sync_get_clock_offset(int64_t *offset_us);

/**
 * @brief Update path asymmetry correction from bidirectional measurement (v0.6.97)
 *
 * Called when CLIENT receives REVERSE_PROBE_RESPONSE. Updates EMA-filtered
 * asymmetry value used to correct systematic offset bias.
 *
 * IEEE 1588 bidirectional path measurement:
 * - Forward offset (from beacons): CLIENT - SERVER, biased by path difference
 * - Reverse offset (from probes): SERVER - CLIENT, biased opposite direction
 * - Asymmetry = forward + reverse (should be 0 if symmetric)
 * - Correction = asymmetry / 2 (applied to offset)
 *
 * @param asymmetry_us Measured asymmetry (forward_offset + reverse_offset)
 * @param rtt_us Round-trip time of the measurement (for quality filtering)
 * @return ESP_OK if sample accepted
 * @return ESP_ERR_INVALID_STATE if RTT too high (congested sample rejected)
 */
esp_err_t time_sync_update_asymmetry(int64_t asymmetry_us, int64_t rtt_us);

/**
 * @brief Get current asymmetry correction value
 *
 * @param asymmetry_us [out] Pointer to store asymmetry in microseconds
 * @param valid [out] Pointer to store validity flag (optional, can be NULL)
 * @return ESP_OK on success
 */
esp_err_t time_sync_get_asymmetry(int64_t *asymmetry_us, bool *valid);

/**
 * @brief Calculate expected drift over time
 *
 * Calculates maximum expected clock drift based on ESP32-C6 crystal
 * specification (±10 PPM) and elapsed time.
 *
 * Useful for determining when resync is needed during disconnection.
 *
 * @param elapsed_ms Time elapsed since last sync (milliseconds)
 * @return Expected drift in microseconds
 */
uint32_t time_sync_calculate_expected_drift(uint32_t elapsed_ms);

/**
 * @brief Check if sync beacon should be sent (SERVER only)
 *
 * Determines if enough time has elapsed since last sync based on
 * adaptive interval. Used by motor task to trigger beacon transmission.
 *
 * @return true if beacon should be sent, false otherwise
 */
bool time_sync_should_send_beacon(void);

/**
 * @brief Force immediate resynchronization
 *
 * Resets sync interval to minimum and triggers immediate sync beacon
 * (SERVER) or requests resync (CLIENT). Used when drift detected or
 * for diagnostic purposes.
 *
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_STATE if not in synchronized state
 */
esp_err_t time_sync_force_resync(void);

/**
 * @brief Get current adaptive sync interval
 *
 * Returns the current sync interval in milliseconds, which is adaptively
 * adjusted based on sync quality (10-60s range).
 *
 * @return Current sync interval in milliseconds
 */
uint32_t time_sync_get_interval_ms(void);

/**
 * @brief Set motor epoch timestamp (SERVER only)
 *
 * Called by SERVER's motor task when it starts motor cycles. This establishes
 * the timing reference that CLIENT will use for bilateral synchronization.
 *
 * @par Why This Matters
 * The motor epoch is the foundation of bilateral coordination. Both devices
 * calculate their activation times from this single reference point. If the
 * epoch is wrong, motors will overlap or have gaps instead of alternating.
 *
 * @par Arduino Equivalent
 * Similar to setting `startTime = millis()` at the beginning of a pattern,
 * but with microsecond precision and synchronized across two devices.
 *
 * @warning This function should only be called once per session start or mode
 *          change. Calling it repeatedly during a session will cause CLIENT
 *          to recalculate its phase offset, potentially causing motor overlap.
 *
 * @pre time_sync_init() called with TIME_SYNC_ROLE_SERVER
 * @pre BLE peer connected
 * @post Epoch will be broadcast to CLIENT in next beacon
 *
 * @param[in] epoch_us Motor cycle start time in microseconds (from esp_timer_get_time())
 * @param[in] cycle_ms Motor cycle period in milliseconds (500-4000ms for 0.25-2Hz)
 *
 * @return
 * - ESP_OK: Success, epoch set and will be sent to CLIENT
 * - ESP_ERR_INVALID_ARG: cycle_ms outside valid range (500-4000ms)
 * - ESP_ERR_INVALID_STATE: Not SERVER role, or module not initialized
 *
 * @see time_sync_get_motor_epoch() for CLIENT retrieval
 * @see docs/adr/0045-synchronized-independent-bilateral-operation.md
 */
esp_err_t time_sync_set_motor_epoch(uint64_t epoch_us, uint32_t cycle_ms);

/**
 * @brief Get motor epoch timestamp (CLIENT only)
 *
 * Called by CLIENT's motor task to retrieve SERVER's motor cycle timing reference.
 * CLIENT uses this to calculate when to activate its own motors for proper
 * bilateral alternation.
 *
 * @param epoch_us [out] Pointer to store motor epoch timestamp (microseconds)
 * @param cycle_ms [out] Pointer to store motor cycle period (milliseconds)
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_ARG if pointers are NULL
 * @return ESP_ERR_INVALID_STATE if motor epoch not yet set
 */
esp_err_t time_sync_get_motor_epoch(uint64_t *epoch_us, uint32_t *cycle_ms);

/*******************************************************************************
 * PWA TIME INJECTION API (AD047 - UTLP Integration)
 ******************************************************************************/

/**
 * @brief Inject external time reference from PWA
 *
 * Allows PWA to provide GPS or cellular network time to improve device sync.
 * The device ALWAYS adopts this time regardless of current stratum - we don't
 * care about absolute UTC correctness, only that devices agree on "when seconds
 * change".
 *
 * @par Time Adoption Philosophy
 * Traditional NTP rejects time jumps to prevent security issues. Our use case
 * is different:
 * - We need bilateral sync, not wall-clock accuracy
 * - Rejecting "worse" time could lock us to spoofed high timestamps
 * - Always accepting allows recovery from any state
 *
 * @par When to Call
 * PWA should inject time:
 * - At session start (before pattern playback begins)
 * - After GPS fix obtained on mobile device
 * - Periodically if high-precision sync is required
 *
 * @param[in] inject Pointer to time injection structure
 * @return ESP_OK on success, time adopted
 * @return ESP_ERR_INVALID_ARG if inject is NULL
 * @return ESP_ERR_INVALID_STATE if module not initialized
 *
 * @see pwa_time_inject_t for structure details
 * @see docs/bilateral_pattern_playback_architecture.md
 */
esp_err_t time_sync_inject_pwa_time(const pwa_time_inject_t *inject);

/**
 * @brief Get current UTLP stratum level
 *
 * Returns the current time source stratum:
 * - 0: GPS time (highest quality)
 * - 1: Phone/cellular time (from PWA injection)
 * - 2+: Peer-derived time (each hop increments)
 * - 255: No external time source (peer-only sync)
 *
 * @return Current stratum value
 */
uint8_t time_sync_get_stratum(void);

/**
 * @brief Get current UTLP quality value
 *
 * Returns battery percentage as quality metric (Swarm Rule).
 * Higher quality devices are preferred as time sources.
 *
 * @note Named `utlp_quality` to avoid conflict with existing
 *       `time_sync_get_quality(time_sync_quality_t*)` which returns
 *       sync accuracy metrics.
 *
 * @return Quality value 0-100 (battery percentage)
 */
uint8_t time_sync_get_utlp_quality(void);

/*******************************************************************************
 * NTP-STYLE HANDSHAKE API (Phase 6k - Precision Bootstrap)
 ******************************************************************************/

/**
 * @brief Check if initial NTP handshake is complete
 *
 * The 3-way handshake provides a precise initial offset measurement with
 * measured RTT (vs estimated). After handshake, one-way beacons with EWMA
 * filtering maintain sync.
 *
 * @return true if handshake complete, false if pending or not started
 */
bool time_sync_is_handshake_complete(void);

/**
 * @brief Initiate NTP-style handshake (CLIENT only)
 *
 * CLIENT calls this to start the 3-way handshake:
 * 1. CLIENT sends TIME_REQUEST with T1 (client send time)
 * 2. SERVER receives, responds with T1, T2, T3
 * 3. CLIENT processes response to calculate precise offset
 *
 * @param t1_out [out] Pointer to store T1 timestamp for message payload
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_STATE if not CLIENT role or already complete
 * @return ESP_ERR_INVALID_ARG if t1_out is NULL
 */
esp_err_t time_sync_initiate_handshake(uint64_t *t1_out);

/**
 * @brief Process handshake request (SERVER only)
 *
 * SERVER calls this when receiving TIME_REQUEST from CLIENT.
 * Returns timestamps for TIME_RESPONSE: T1 (echoed), T2 (receive time), T3 (send time).
 *
 * @param t1_client_send_us T1 from CLIENT's request
 * @param t2_server_recv_us SERVER's local time when request received
 * @param t3_server_send_out [out] Pointer to store T3 (SERVER send time)
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_STATE if not SERVER role
 * @return ESP_ERR_INVALID_ARG if t3_server_send_out is NULL
 */
esp_err_t time_sync_process_handshake_request(uint64_t t1_client_send_us,
                                               uint64_t t2_server_recv_us,
                                               uint64_t *t3_server_send_out);

/**
 * @brief Process handshake response (CLIENT only)
 *
 * CLIENT calls this when receiving TIME_RESPONSE from SERVER.
 * Calculates precise offset using NTP formula:
 *   offset = ((T2-T1) + (T3-T4)) / 2
 *   RTT = (T4-T1) - (T3-T2)
 *
 * This offset becomes the EWMA filter's initial value (precise bootstrap).
 *
 * @param t1_us T1 from original request (echoed in response)
 * @param t2_us T2 SERVER receive time
 * @param t3_us T3 SERVER send time
 * @param t4_us T4 CLIENT receive time (caller's local time when response received)
 * @return ESP_OK on success (handshake complete, offset set)
 * @return ESP_ERR_INVALID_STATE if not CLIENT role or handshake already complete
 */
esp_err_t time_sync_process_handshake_response(uint64_t t1_us, uint64_t t2_us,
                                                uint64_t t3_us, uint64_t t4_us);

/**
 * @brief Set motor epoch from handshake response (CLIENT only)
 *
 * Called by CLIENT when receiving motor_epoch in TIME_RESPONSE.
 * This avoids waiting 10s for next beacon to get motor epoch.
 *
 * @param epoch_us Motor epoch timestamp from SERVER
 * @param cycle_ms Motor cycle period from SERVER
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_ARG if parameters are invalid
 */
esp_err_t time_sync_set_motor_epoch_from_handshake(uint64_t epoch_us, uint32_t cycle_ms);

/**
 * @brief Trigger forced beacons for fast convergence (SERVER only)
 *
 * Forces 3 immediate beacons at 500ms intervals for fast time sync convergence
 * after mode changes. After 3 beacons, returns to adaptive interval.
 *
 * Call this on SERVER when mode changes to help CLIENT filter adapt quickly.
 *
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_STATE if not initialized or not SERVER role
 */
esp_err_t time_sync_trigger_forced_beacons(void);

/**
 * @brief Reset EMA filter to fast-attack mode (for mode changes)
 *
 * Resets the filter to fast-attack mode with aggressive convergence:
 * - Sets fast_attack_active = true
 * - Resets valid_beacon_count = 0 (forces 12 samples or early convergence)
 * - Clears sample_count = 0
 * - Uses 50ms outlier threshold (vs 100ms in steady-state)
 * - Keeps current filtered_offset_us (doesn't reset to zero)
 *
 * Call this when mode changes (frequency/duty/cycle) to quickly adapt
 * to the new motor epoch without jerky corrections.
 *
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_STATE if not initialized
 */
esp_err_t time_sync_reset_filter_fast_attack(void);

/* AD045: time_sync_get_drift_rate() and time_sync_get_predicted_offset() removed.
 * EMA filter provides ±30μs accuracy - no drift rate extrapolation needed. */

/**
 * @brief Check if antiphase lock is achieved (Phase 6s)
 *
 * Determines if time synchronization has converged to a stable state suitable
 * for starting motors. This prevents startup jitter from EWMA filter convergence.
 *
 * Lock criteria:
 * - Handshake complete (precise NTP-style bootstrap)
 * - Minimum 3 beacons received (filter has data)
 * - Filter in steady-state mode (sample_count >= 10, not fast-attack)
 * - Recent beacon within 2× adaptive interval (not stale)
 *
 * Expected lock time: 2-3 seconds from connection
 *
 * Usage:
 * - CLIENT motor task waits for lock before starting motors (5s timeout)
 * - Periodically check during operation for lock maintenance (every 10 cycles)
 * - Request forced beacons if lock lost during session
 *
 * @return true if locked and stable, false otherwise
 * @note SERVER always returns true (no phase lock needed, it's authoritative)
 */
bool time_sync_is_antiphase_locked(void);

/**
 * @brief Get last beacon timestamps for paired offset calculation (AD043)
 *
 * CLIENT uses this to populate SYNC_FB with T1/T2 timestamps for NTP-style
 * offset calculation on SERVER. This enables bias correction for the one-way
 * delay inherent in beacon-based synchronization.
 *
 * @param server_time_us [out] T1: server_time_us from last beacon
 * @param local_rx_time_us [out] T2: CLIENT's local time when beacon received
 * @return ESP_OK if timestamps available
 * @return ESP_ERR_INVALID_STATE if no beacon received yet
 */
esp_err_t time_sync_get_last_beacon_timestamps(uint64_t *server_time_us, uint64_t *local_rx_time_us);

/**
 * @brief Update offset using paired timestamps from SYNC_FB (AD043)
 *
 * SERVER calls this when receiving SYNC_FB with paired timestamps.
 * Calculates bias-corrected offset using NTP formula:
 *   offset = ((T2-T1) + (T3-T4)) / 2
 *
 * The calculated offset is fed into the EMA filter, correcting the
 * systematic one-way delay bias from beacon-only synchronization.
 *
 * @param t1_server_beacon_time_us T1: SERVER's beacon timestamp (from SYNC_FB)
 * @param t2_client_rx_time_us T2: CLIENT's beacon receive time (from SYNC_FB)
 * @param t3_client_tx_time_us T3: CLIENT's SYNC_FB send time (from SYNC_FB)
 * @param t4_server_rx_time_us T4: SERVER's local time when SYNC_FB received
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_ARG if timestamps are invalid (e.g., t4 < t1)
 */
esp_err_t time_sync_update_from_paired_timestamps(
    uint64_t t1_server_beacon_time_us,
    uint64_t t2_client_rx_time_us,
    uint64_t t3_client_tx_time_us,
    uint64_t t4_server_rx_time_us);

/*******************************************************************************
 * UTILITY MACROS
 ******************************************************************************/

/** @brief Check if time sync is initialized */
#define TIME_SYNC_IS_INITIALIZED() (time_sync_get_state() != SYNC_STATE_INIT)

/** @brief Check if time sync is active (connected and synced) */
#define TIME_SYNC_IS_ACTIVE() ((time_sync_get_state() == SYNC_STATE_SYNCED) || \
                                (time_sync_get_state() == SYNC_STATE_DRIFT_DETECTED))

/** @brief Check if device is SERVER */
#define TIME_SYNC_IS_SERVER() (time_sync_get_role() == TIME_SYNC_ROLE_SERVER)

/** @brief Check if device is CLIENT */
#define TIME_SYNC_IS_CLIENT() (time_sync_get_role() == TIME_SYNC_ROLE_CLIENT)

/** @} */ // end of time_sync group

#ifdef __cplusplus
}
#endif

#endif /* TIME_SYNC_H */
