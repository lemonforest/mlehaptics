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
#define TIME_SYNC_MSG_SIZE          (16U)

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
} time_sync_state_t;

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
 */
typedef struct {
    uint32_t samples_collected;             /**< Number of sync samples */
    int32_t  avg_offset_us;                 /**< Average clock offset (μs) */
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
    /* Timing References */
    uint64_t local_ref_time_us;      /**< Local reference timestamp (esp_timer) */
    uint64_t server_ref_time_us;     /**< SERVER's reference timestamp */
    int32_t  clock_offset_us;        /**< Calculated offset (CLIENT - SERVER) */
    uint32_t last_sync_ms;           /**< When last sync occurred (milliseconds since boot) */

    /* Sync Protocol State */
    time_sync_state_t state;         /**< Current sync state */
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

    /* JPL Rule 2: Bounded operation tracking */
    uint32_t total_syncs;            /**< Total sync operations (diagnostic) */
    uint32_t session_start_ms;       /**< Session start time for drift calculation */
} time_sync_state_t;

/**
 * @brief Time sync beacon message structure
 *
 * Transmitted by SERVER to CLIENT for periodic synchronization.
 * Fixed 16-byte size for efficient BLE notification.
 *
 * JPL Rule 1: Fixed size, no dynamic allocation.
 */
typedef struct __attribute__((packed)) {
    uint64_t timestamp_us;           /**< SERVER's current time (microseconds) */
    uint32_t session_ref_ms;         /**< Session reference time (milliseconds) */
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
 * Records the connection event timestamp as common reference.
 *
 * For SERVER: Records local timestamp and prepares to send initial beacon.
 * For CLIENT: Records local timestamp and waits for SERVER beacon.
 *
 * JPL Rule 5: Explicit error checking required.
 *
 * @param connection_time_us Timestamp of connection event (from esp_timer)
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_STATE if not in INIT state
 * @return ESP_ERR_INVALID_ARG if connection_time_us is 0
 */
esp_err_t time_sync_on_connection(uint64_t connection_time_us);

/**
 * @brief Handle disconnection event
 *
 * Transitions to SYNC_STATE_DISCONNECTED and freezes current sync state
 * for continued operation using last known offset.
 *
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_STATE if not in synchronized state
 */
esp_err_t time_sync_on_disconnection(void);

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
time_sync_state_t time_sync_get_state(void);

/**
 * @brief Get device role
 *
 * Returns the assigned device role for time synchronization.
 *
 * @return Current role (TIME_SYNC_ROLE_*)
 */
time_sync_role_t time_sync_get_role(void);

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
