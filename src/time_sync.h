/**
 * @file time_sync.h
 * @brief Hybrid time synchronization for bilateral motor coordination
 *
 * This module implements a hybrid time synchronization protocol for coordinating
 * bilateral motor activation between two peer devices. The approach combines:
 *
 * 1. Initial connection sync - Capture common timestamp reference at connection
 * 2. Periodic sync beacons - SERVER sends time updates every 10-60s
 * 3. Timestamped commands - All motor commands include timing verification
 *
 * Design Goals:
 * - ±100ms timing accuracy (AD029 revised specification)
 * - Battery-efficient sync intervals with exponential backoff
 * - Graceful degradation during BLE disconnects
 * - Full JPL Power of Ten compliance
 *
 * JPL Compliance:
 * - Rule 1: Static allocation only (no malloc)
 * - Rule 2: Bounded loops (max iterations defined)
 * - Rule 3: vTaskDelay() for all timing (no busy-wait)
 * - Rule 5: Explicit error checking (all return codes checked)
 * - Rule 8: Watchdog integration for sync task
 *
 * @version 0.3.0
 * @date 2025-11-19
 * @author Phase 2 Implementation
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

/** @brief Time sync beacon message size (bytes) */
#define TIME_SYNC_MSG_SIZE          (28U)

/** @brief Minimum sync interval (milliseconds) - aggressive sync */
#define TIME_SYNC_INTERVAL_MIN_MS   (10000U)    // 10 seconds

/** @brief Maximum sync interval (milliseconds) - steady state */
#define TIME_SYNC_INTERVAL_MAX_MS   (60000U)    // 60 seconds

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

/*******************************************************************************
 * TYPE DEFINITIONS
 ******************************************************************************/

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

    /* Quality Metrics */
    time_sync_quality_t quality;     /**< Sync quality tracking */

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

    /* Bug #27 Fix: Two-way RTT measurement per beacon */
    uint64_t last_beacon_t1_us;      /**< SERVER: T1 of last sent beacon (for RTT calc) */
    uint8_t  last_beacon_seq;        /**< SERVER: Sequence of last sent beacon */
    bool     last_beacon_t1_valid;   /**< SERVER: T1 available for matching response */
    int32_t  measured_rtt_us;        /**< Last measured RTT (μs) from two-way exchange */
    bool     measured_rtt_valid;     /**< Whether measured_rtt_us is valid */

    /* Fix #2: Drift rate filtering (NTP best practice) */
    uint64_t last_beacon_time_us;    /**< CLIENT: Time when last beacon was received */
    int32_t  drift_rate_us_per_s;    /**< Filtered drift rate (μs/s) - positive = CLIENT faster */
    bool     drift_rate_valid;       /**< Whether drift_rate_us_per_s has been calculated */

    /* Phase 6k: Drift-rate-based offset prediction for faster bilateral convergence */
    uint32_t last_rtt_update_ms;     /**< When clock_offset_us was last updated (for prediction) */
} time_sync_state_t;

/**
 * @brief Time sync beacon message structure
 *
 * Transmitted by SERVER to CLIENT for periodic synchronization.
 * Fixed 28-byte size for efficient BLE notification.
 *
 * JPL Rule 1: Fixed size, no dynamic allocation.
 *
 * Phase 3: Extended to include motor epoch for bilateral coordination.
 */
typedef struct __attribute__((packed)) {
    uint64_t timestamp_us;           /**< SERVER's current time (microseconds) */
    uint32_t session_ref_ms;         /**< Session reference time (milliseconds) */
    uint64_t motor_epoch_us;         /**< Motor cycle start time (Phase 3) */
    uint32_t motor_cycle_ms;         /**< Motor cycle period (Phase 3) */
    uint8_t  sequence;               /**< Sequence number (for ordering) */
    uint8_t  quality_score;          /**< SERVER's sync quality (0-100) */
    uint16_t checksum;               /**< CRC-16 for integrity */
} time_sync_beacon_t;

/*******************************************************************************
 * PUBLIC API FUNCTIONS
 ******************************************************************************/

/**
 * @brief Initialize time synchronization module
 *
 * Prepares the time sync module for operation. Must be called before any
 * other time sync functions. Initializes state to SYNC_STATE_INIT.
 *
 * JPL Rule 5: Returns error code for explicit checking.
 *
 * @param role Device role (SERVER or CLIENT)
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_ARG if role is invalid
 * @return ESP_ERR_INVALID_STATE if already initialized
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
 * @param epoch_us Motor cycle start time in microseconds (synchronized time)
 * @param cycle_ms Motor cycle period in milliseconds (e.g., 2000ms for Mode 0)
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_ARG if parameters are invalid
 * @return ESP_ERR_INVALID_STATE if not initialized or not SERVER role
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

/*******************************************************************************
 * BUG #27 FIX: TWO-WAY RTT MEASUREMENT PER BEACON
 ******************************************************************************/

/**
 * @brief Record beacon T1 timestamp (SERVER only)
 *
 * Called by SERVER when generating a beacon, before sending.
 * Stores T1 and sequence for matching with CLIENT's response.
 *
 * @param t1_us SERVER's local time when beacon generated
 * @param sequence Beacon sequence number
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_STATE if not SERVER role
 */
esp_err_t time_sync_record_beacon_t1(uint64_t t1_us, uint8_t sequence);

/**
 * @brief Process beacon response (SERVER only)
 *
 * Called by SERVER when receiving SYNC_MSG_BEACON_RESPONSE from CLIENT.
 * Calculates RTT and precise offset using NTP formula:
 *   offset = ((T2-T1) + (T3-T4)) / 2
 *   RTT = (T4-T1) - (T3-T2)
 *
 * Updates clock_offset_us with measured value (more accurate than one-way).
 *
 * @param sequence Beacon sequence (to match with stored T1)
 * @param t2_us CLIENT's receive time
 * @param t3_us CLIENT's response send time
 * @param t4_us SERVER's receive time (when response arrived)
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_STATE if not SERVER role or sequence mismatch
 */
esp_err_t time_sync_process_beacon_response(uint8_t sequence, uint64_t t2_us,
                                            uint64_t t3_us, uint64_t t4_us);

/**
 * @brief Get last measured RTT
 *
 * Returns the RTT from the most recent two-way exchange.
 * If no valid measurement, returns default estimate (20ms).
 *
 * @param rtt_us [out] Pointer to store RTT in microseconds
 * @return ESP_OK if valid measurement available
 * @return ESP_ERR_NOT_FOUND if using default estimate
 */
esp_err_t time_sync_get_measured_rtt(int32_t *rtt_us);

/**
 * @brief Update clock offset from two-way RTT measurement (CLIENT only)
 *
 * Bug #27 Fix: Called when CLIENT receives RTT_RESULT from SERVER.
 * SERVER calculated offset using proper NTP 4-timestamp formula,
 * so CLIENT can directly use this value instead of one-way estimate.
 *
 * @param offset_us Calculated clock offset (CLIENT - SERVER) in μs
 * @param rtt_us Measured round-trip time in μs
 * @param sequence Beacon sequence for correlation
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_STATE if not CLIENT role
 */
esp_err_t time_sync_update_offset_from_rtt(int64_t offset_us, int32_t rtt_us, uint8_t sequence);

/**
 * @brief Get filtered drift rate (Fix #2)
 *
 * Returns the EWMA-filtered drift rate in μs/s.
 * Positive value means CLIENT clock is running faster than SERVER.
 *
 * @param drift_rate_us_per_s [out] Pointer to store drift rate
 * @return ESP_OK if valid drift rate available
 * @return ESP_ERR_NOT_FOUND if drift rate not yet calculated
 */
esp_err_t time_sync_get_drift_rate(int32_t *drift_rate_us_per_s);

/**
 * @brief Get predicted clock offset using drift rate (Phase 6k)
 *
 * Provides smoother offset estimation between RTT measurements by extrapolating
 * based on filtered drift rate. Reduces RTT asymmetry noise (±10-30ms) for
 * bilateral motor coordination, enabling faster antiphase convergence (2-5s vs 10-20s).
 *
 * Formula: predicted_offset = last_offset + (drift_rate * elapsed_time)
 *
 * @param predicted_offset_us [out] Pointer to store predicted offset in μs
 * @return ESP_OK if prediction available (drift rate valid)
 * @return ESP_ERR_NOT_FOUND if using raw offset (first ~20s after boot)
 */
esp_err_t time_sync_get_predicted_offset(int64_t *predicted_offset_us);

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

#ifdef __cplusplus
}
#endif

#endif /* TIME_SYNC_H */
