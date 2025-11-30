/**
 * @file time_sync.c
 * @brief Hybrid time synchronization implementation for bilateral coordination
 *
 * Implements hybrid time sync protocol combining:
 * - Initial connection sync (< 1ms accuracy)
 * - Periodic sync beacons (10-60s adaptive intervals)
 * - Quality metrics and drift detection
 *
 * JPL Power of Ten Compliance:
 * - Rule 1: Static allocation only (g_time_sync_state)
 * - Rule 2: All loops bounded by constants
 * - Rule 3: vTaskDelay() for all timing
 * - Rule 5: Explicit error checking
 * - Rule 7: Pointer validation
 * - Rule 8: Watchdog integration points
 *
 * @version 0.3.0
 * @date 2025-11-19
 */

#include "time_sync.h"
#include "esp_timer.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include <string.h>
#include <math.h>

/*******************************************************************************
 * CONSTANTS
 ******************************************************************************/

static const char *TAG = "TIME_SYNC";

/** @brief CRC-16 polynomial for message integrity */
#define CRC16_POLY 0x1021

/** @brief Sync quality thresholds */
#define SYNC_QUALITY_EXCELLENT (95U)  /**< < 5ms drift */
#define SYNC_QUALITY_GOOD (85U)       /**< < 15ms drift */
#define SYNC_QUALITY_FAIR (70U)       /**< < 30ms drift */
#define SYNC_QUALITY_POOR (50U)       /**< < 50ms drift */

/*******************************************************************************
 * STATIC STATE (JPL Rule 1: No dynamic allocation)
 ******************************************************************************/

/** @brief Global time sync state - statically allocated */
static time_sync_state_t g_time_sync_state = {
    .state = SYNC_STATE_INIT,
    .role = TIME_SYNC_ROLE_NONE,
    .initialized = false
};

/*******************************************************************************
 * FORWARD DECLARATIONS
 ******************************************************************************/

static uint16_t calculate_crc16(const uint8_t *data, size_t length);
static uint8_t calculate_sync_quality(int32_t offset_us, uint32_t drift_us, uint32_t rtt_us);
static void update_quality_metrics(int32_t offset_change_us, uint32_t rtt_us, int32_t drift_rate_us_per_s);
static esp_err_t adjust_sync_interval(void);

/*******************************************************************************
 * PUBLIC API IMPLEMENTATION
 ******************************************************************************/

esp_err_t time_sync_init(time_sync_role_t role)
{
    /* JPL Rule 5: Validate parameters */
    if (role >= TIME_SYNC_ROLE_MAX || role == TIME_SYNC_ROLE_NONE) {
        ESP_LOGE(TAG, "Invalid role: %d", role);
        return ESP_ERR_INVALID_ARG;
    }

    if (g_time_sync_state.initialized) {
        ESP_LOGW(TAG, "Already initialized");
        return ESP_ERR_INVALID_STATE;
    }

    /* Initialize state structure */
    memset(&g_time_sync_state, 0, sizeof(time_sync_state_t));

    g_time_sync_state.state = SYNC_STATE_INIT;
    g_time_sync_state.role = role;
    g_time_sync_state.sync_interval_ms = TIME_SYNC_INTERVAL_MIN_MS;  /* Start aggressive */
    g_time_sync_state.initialized = true;
    g_time_sync_state.session_start_ms = (uint32_t)(esp_timer_get_time() / 1000);

    ESP_LOGI(TAG, "Initialized as %s (interval: %lu ms)",
             (role == TIME_SYNC_ROLE_SERVER) ? "SERVER" : "CLIENT",
             g_time_sync_state.sync_interval_ms);

    return ESP_OK;
}

esp_err_t time_sync_deinit(void)
{
    if (!g_time_sync_state.initialized) {
        ESP_LOGW(TAG, "Not initialized");
        return ESP_ERR_INVALID_STATE;
    }

    ESP_LOGI(TAG, "Deinitializing (total syncs: %lu)", g_time_sync_state.total_syncs);

    /* Reset to initial state */
    memset(&g_time_sync_state, 0, sizeof(time_sync_state_t));
    g_time_sync_state.state = SYNC_STATE_INIT;
    g_time_sync_state.role = TIME_SYNC_ROLE_NONE;
    g_time_sync_state.initialized = false;

    return ESP_OK;
}

esp_err_t time_sync_on_connection(void)
{
    /* JPL Rule 5: Validate state */
    if (!g_time_sync_state.initialized) {
        ESP_LOGE(TAG, "Not initialized");
        return ESP_ERR_INVALID_STATE;
    }

    if (g_time_sync_state.state != SYNC_STATE_INIT) {
        ESP_LOGW(TAG, "Not in INIT state (current: %d)", g_time_sync_state.state);
        return ESP_ERR_INVALID_STATE;
    }

    /* NTP-style: No common reference needed - each device uses absolute boot time */
    uint64_t now_us = esp_timer_get_time();
    g_time_sync_state.state = SYNC_STATE_CONNECTED;

    ESP_LOGI(TAG, "Connection sync established (%s role, NTP-style)",
             (g_time_sync_state.role == TIME_SYNC_ROLE_SERVER) ? "SERVER" : "CLIENT");

    /* SERVER immediately transitions to SYNCED, CLIENT waits for first beacon */
    if (g_time_sync_state.role == TIME_SYNC_ROLE_SERVER) {
        g_time_sync_state.state = SYNC_STATE_SYNCED;

        /* SERVER is authoritative reference - initialize quality to 100% (excellent) */
        g_time_sync_state.quality.quality_score = 100;
        g_time_sync_state.quality.samples_collected = 1;

        /* FIX: Set last_sync_ms far enough in the past to trigger immediate first beacon
         * elapsed_ms = now - last_sync = now - (now - interval - 1) = interval + 1 >= interval
         * This ensures CLIENT receives motor epoch promptly after pairing */
        uint32_t now_ms = (uint32_t)(now_us / 1000);
        g_time_sync_state.last_sync_ms = now_ms - g_time_sync_state.sync_interval_ms - 1;

        ESP_LOGI(TAG, "SERVER ready to send sync beacons (first beacon IMMEDIATE, then every %lu ms)",
                 g_time_sync_state.sync_interval_ms);
    } else {
        /* CLIENT: Initialize to current time (only used for drift monitoring) */
        g_time_sync_state.last_sync_ms = (uint32_t)(now_us / 1000);
        ESP_LOGI(TAG, "CLIENT waiting for initial beacon from SERVER");
    }

    return ESP_OK;
}

esp_err_t time_sync_on_disconnection(void)
{
    if (!g_time_sync_state.initialized) {
        ESP_LOGE(TAG, "Not initialized");
        return ESP_ERR_INVALID_STATE;
    }

    if (g_time_sync_state.state != SYNC_STATE_SYNCED &&
        g_time_sync_state.state != SYNC_STATE_DRIFT_DETECTED) {
        ESP_LOGW(TAG, "Not in synchronized state");
        return ESP_ERR_INVALID_STATE;
    }

    /* PHASE 6r FIX: Preserve motor epoch and drift rate for continuation during disconnect
     *
     * Root cause analysis (original Phase 6 bug):
     * - The original bug was about ROLE SWAP corruption during RECONNECTION
     * - Device carried over motor_epoch from previous session when role changed
     * - Example: CLIENT in session 1 → reconnect as SERVER → used old CLIENT epoch
     * - Result: 2466ms phase skip (Boot #3 in serial logs)
     *
     * Separate question: Can CLIENT continue during DISCONNECT (no role swap)?
     * - Drift rate proven stable (±30 μs over 90 minutes from Phase 2 testing)
     * - For 20-minute therapy: ±2.4ms worst-case drift (well within ±100ms spec)
     * - Technical conclusion: YES, continuation is valid and therapeutically beneficial
     *
     * Phase 6r solution: Preserve sync state for continuation, clear only on role swap
     * - Motor coordination continues during brief disconnects using frozen drift rate
     * - Role swap detection on reconnection prevents original corruption bug
     * - Safety timeout (2 min) expires motor epoch for long disconnects
     * - Phase 6n already ensures roles are preserved on reconnection (should never swap)
     */
    g_time_sync_state.state = SYNC_STATE_DISCONNECTED;

    /* PRESERVE motor epoch data (CLIENT can continue bilateral alternation) */
    /* motor_epoch_us, motor_cycle_ms, motor_epoch_valid - NOT cleared */

    /* PRESERVE drift rate data (CLIENT can extrapolate offset during disconnect) */
    /* drift_rate_us_per_s, drift_rate_valid - NOT cleared */
    /* last_beacon_offset_us, last_beacon_valid, last_beacon_time_us - NOT cleared */

    /* Clear RTT measurement state (no fresh measurements possible while disconnected) */
    g_time_sync_state.measured_rtt_us = 0;
    g_time_sync_state.measured_rtt_valid = false;
    g_time_sync_state.last_beacon_t1_valid = false;

    /* Clear handshake state (forces fresh handshake on reconnection) */
    g_time_sync_state.handshake_complete = false;
    g_time_sync_state.handshake_t1_us = 0;

    ESP_LOGI(TAG, "Disconnected - motor coordination continues using frozen drift rate");
    ESP_LOGI(TAG, "Drift rate: %ld μs/s | Motor epoch preserved for continuation",
             (long)g_time_sync_state.drift_rate_us_per_s);
    ESP_LOGI(TAG, "Safety timeout: Motor epoch expires after 2 minutes if disconnected");

    return ESP_OK;
}

/**
 * @brief Handle reconnection event with role swap detection
 *
 * Called when BLE peer connection is re-established. Conditionally clears
 * motor epoch data if role changed between connections to prevent Phase 6
 * corruption bug.
 *
 * PHASE 6r: Role swap detection for conditional clearing
 *
 * Phase 6n ensures roles are preserved on reconnection, so role swap should
 * NOT occur during normal operation. If it does, that indicates a bug in
 * role preservation logic.
 *
 * @param new_role Device role after reconnection (SERVER or CLIENT)
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_STATE if not initialized or not disconnected
 */
esp_err_t time_sync_on_reconnection(time_sync_role_t new_role)
{
    if (!g_time_sync_state.initialized) {
        ESP_LOGE(TAG, "Not initialized");
        return ESP_ERR_INVALID_STATE;
    }

    if (g_time_sync_state.state != SYNC_STATE_DISCONNECTED &&
        g_time_sync_state.state != SYNC_STATE_INIT) {
        ESP_LOGW(TAG, "Not in disconnected state (current: %d)", g_time_sync_state.state);
        /* Not an error - may be called during initial connection */
    }

    time_sync_role_t prev_role = g_time_sync_state.role;

    /* CRITICAL: Detect role swap (should NOT happen per Phase 6n) */
    if (prev_role != TIME_SYNC_ROLE_NONE && prev_role != new_role) {
        /* This should NOT occur - Phase 6n preserves roles on reconnection */
        ESP_LOGW(TAG, "⚠️  WARNING: Role swap detected - THIS SHOULD NOT HAPPEN!");
        ESP_LOGW(TAG, "⚠️  Previous role: %s | New role: %s",
                 prev_role == TIME_SYNC_ROLE_SERVER ? "SERVER" : "CLIENT",
                 new_role == TIME_SYNC_ROLE_SERVER ? "SERVER" : "CLIENT");
        ESP_LOGW(TAG, "⚠️  This indicates a bug in role preservation logic (Phase 6n)");
        ESP_LOGW(TAG, "⚠️  Clearing motor epoch to prevent corruption (Phase 6 bug mitigation)");

        /* Clear motor epoch to prevent Phase 6 corruption bug */
        g_time_sync_state.motor_epoch_us = 0;
        g_time_sync_state.motor_cycle_ms = 0;
        g_time_sync_state.motor_epoch_valid = false;
    } else {
        /* Normal case: Role unchanged (or initial connection) */
        if (prev_role != TIME_SYNC_ROLE_NONE) {
            ESP_LOGI(TAG, "✓ Role preserved on reconnection: %s",
                     new_role == TIME_SYNC_ROLE_SERVER ? "SERVER" : "CLIENT");
            ESP_LOGI(TAG, "✓ Motor epoch still valid - bilateral coordination can resume");
        } else {
            ESP_LOGI(TAG, "Initial connection - role assigned: %s",
                     new_role == TIME_SYNC_ROLE_SERVER ? "SERVER" : "CLIENT");
        }
    }

    return ESP_OK;
}

esp_err_t time_sync_update(void)
{
    if (!g_time_sync_state.initialized) {
        return ESP_ERR_INVALID_STATE;
    }

    /* Skip updates if not in active sync states */
    if (g_time_sync_state.state != SYNC_STATE_SYNCED &&
        g_time_sync_state.state != SYNC_STATE_DRIFT_DETECTED &&
        g_time_sync_state.state != SYNC_STATE_CONNECTED) {
        return ESP_OK;
    }

    uint32_t now_ms = (uint32_t)(esp_timer_get_time() / 1000);

    /* SERVER: Check if time to send sync beacon */
    if (g_time_sync_state.role == TIME_SYNC_ROLE_SERVER) {
        if (time_sync_should_send_beacon()) {
            /* Note: Actual beacon sending handled by BLE manager via time_sync_generate_beacon() */
            g_time_sync_state.last_sync_ms = now_ms;
            g_time_sync_state.total_syncs++;

            /* Adjust interval based on quality */
            esp_err_t err = adjust_sync_interval();
            if (err != ESP_OK) {
                ESP_LOGW(TAG, "Failed to adjust sync interval: %d", err);
            }

            ESP_LOGI(TAG, "Sync beacon interval elapsed (next in %lu ms, quality: %u%%)",
                     g_time_sync_state.sync_interval_ms,
                     g_time_sync_state.quality.quality_score);
        }
    }
    /* CLIENT: Monitor drift and request resync if needed */
    else if (g_time_sync_state.role == TIME_SYNC_ROLE_CLIENT) {
        uint32_t elapsed_ms = now_ms - g_time_sync_state.last_sync_ms;
        uint32_t expected_drift_us = time_sync_calculate_expected_drift(elapsed_ms);

        /* Check if drift exceeds threshold */
        if (expected_drift_us > TIME_SYNC_DRIFT_THRESHOLD_US) {
            if (g_time_sync_state.state != SYNC_STATE_DRIFT_DETECTED) {
                ESP_LOGW(TAG, "Drift threshold exceeded (%lu μs > %lu μs after %lu ms)",
                         expected_drift_us, TIME_SYNC_DRIFT_THRESHOLD_US, elapsed_ms);
                g_time_sync_state.state = SYNC_STATE_DRIFT_DETECTED;
                g_time_sync_state.drift_detected = true;
            }
        }

        /* Log quality periodically (every 60 seconds) */
        if ((elapsed_ms % 60000) == 0 && elapsed_ms > 0) {
            ESP_LOGI(TAG, "Sync status: offset=%ld μs, drift=%lu μs, quality=%u%%, last_sync=%lu ms ago",
                     g_time_sync_state.clock_offset_us,
                     expected_drift_us,
                     g_time_sync_state.quality.quality_score,
                     elapsed_ms);
        }
    }

    return ESP_OK;
}

esp_err_t time_sync_get_time(uint64_t *sync_time_us)
{
    /* JPL Rule 7: Validate pointer */
    if (sync_time_us == NULL) {
        ESP_LOGE(TAG, "NULL pointer");
        return ESP_ERR_INVALID_ARG;
    }

    if (!g_time_sync_state.initialized) {
        ESP_LOGE(TAG, "Not initialized");
        return ESP_ERR_INVALID_STATE;
    }

    /* Get current local time */
    uint64_t local_time_us = esp_timer_get_time();

    /* SERVER: Return local time directly */
    if (g_time_sync_state.role == TIME_SYNC_ROLE_SERVER) {
        *sync_time_us = local_time_us;
    }
    /* CLIENT: Apply clock offset correction (Phase 6k: use predicted offset for smoother coordination) */
    else if (g_time_sync_state.role == TIME_SYNC_ROLE_CLIENT) {
        /* Try to use predicted offset for smoother bilateral coordination
         * Falls back to raw offset if drift rate not yet calculated */
        int64_t offset_us = 0;
        esp_err_t ret = time_sync_get_predicted_offset(&offset_us);

        if (ret != ESP_OK) {
            /* Fallback to raw offset (first ~20s after boot) */
            offset_us = g_time_sync_state.clock_offset_us;
        }

        /* Apply offset (offset can be negative)
         * Phase 6o: Clamp to zero if result would underflow (early boot edge case)
         * If CLIENT hasn't run long enough for local_time > offset, return 0 instead of underflowing */
        int64_t sync_time_signed = (int64_t)local_time_us - offset_us;
        if (sync_time_signed < 0) {
            ESP_LOGW(TAG, "time_sync_get_time: Underflow prevented (local=%llu μs, offset=%lld μs, would be %lld μs)",
                     local_time_us, offset_us, sync_time_signed);
            *sync_time_us = 0;  // Clamp to zero
        } else {
            *sync_time_us = (uint64_t)sync_time_signed;
        }
    }
    else {
        ESP_LOGE(TAG, "Invalid role: %d", g_time_sync_state.role);
        return ESP_ERR_INVALID_STATE;
    }

    return ESP_OK;
}

esp_err_t time_sync_process_beacon(const time_sync_beacon_t *beacon, uint64_t receive_time_us)
{
    /* JPL Rule 7: Validate pointers */
    if (beacon == NULL) {
        ESP_LOGE(TAG, "NULL beacon pointer");
        return ESP_ERR_INVALID_ARG;
    }

    if (!g_time_sync_state.initialized) {
        ESP_LOGE(TAG, "Not initialized");
        return ESP_ERR_INVALID_STATE;
    }

    if (g_time_sync_state.role != TIME_SYNC_ROLE_CLIENT) {
        ESP_LOGE(TAG, "Not CLIENT role (role: %d)", g_time_sync_state.role);
        return ESP_ERR_INVALID_STATE;
    }

    /* Validate checksum */
    uint16_t calc_crc = calculate_crc16((const uint8_t *)beacon, sizeof(time_sync_beacon_t) - sizeof(uint16_t));
    if (calc_crc != beacon->checksum) {
        ESP_LOGE(TAG, "CRC mismatch (calc: 0x%04X, recv: 0x%04X)", calc_crc, beacon->checksum);
        g_time_sync_state.quality.sync_failures++;
        return ESP_ERR_INVALID_CRC;
    }

    /* The primary purpose of the beacon is now to deliver the motor epoch.
     * The drift rate and offset are calculated from the more precise RTT updates.
     * We still update some secondary state here.
     */
    g_time_sync_state.server_ref_time_us = beacon->timestamp_us;
    g_time_sync_state.last_sync_ms = (uint32_t)(receive_time_us / 1000);
    g_time_sync_state.sync_sequence = beacon->sequence;
    g_time_sync_state.total_syncs++;

    /* Phase 3: Extract motor epoch for bilateral coordination */
    g_time_sync_state.motor_epoch_us = beacon->motor_epoch_us;
    g_time_sync_state.motor_cycle_ms = beacon->motor_cycle_ms;
    g_time_sync_state.motor_epoch_valid = (beacon->motor_epoch_us > 0 && beacon->motor_cycle_ms > 0);

    /* Transition to SYNCED if this is first beacon */
    if (g_time_sync_state.state == SYNC_STATE_CONNECTED) {
        if (g_time_sync_state.quality.samples_collected == 0) {
            g_time_sync_state.quality.samples_collected = 1;
            g_time_sync_state.quality.quality_score = 50;
            ESP_LOGI(TAG, "Quality metrics initialized from beacon (handshake not completed)");
        }
        g_time_sync_state.state = SYNC_STATE_SYNCED;
        ESP_LOGI(TAG, "Initial sync beacon processed");
    }

    ESP_LOGD(TAG, "Beacon processed (seq: %u, motor_epoch: %llu, cycle: %lu)",
             beacon->sequence, beacon->motor_epoch_us, beacon->motor_cycle_ms);

    return ESP_OK;
}

esp_err_t time_sync_generate_beacon(time_sync_beacon_t *beacon)
{
    /* JPL Rule 7: Validate pointer */
    if (beacon == NULL) {
        ESP_LOGE(TAG, "NULL beacon pointer");
        return ESP_ERR_INVALID_ARG;
    }

    if (!g_time_sync_state.initialized) {
        ESP_LOGE(TAG, "Not initialized");
        return ESP_ERR_INVALID_STATE;
    }

    if (g_time_sync_state.role != TIME_SYNC_ROLE_SERVER) {
        ESP_LOGE(TAG, "Not SERVER role (role: %d)", g_time_sync_state.role);
        return ESP_ERR_INVALID_STATE;
    }

    /* Populate beacon fields */
    /* NTP-STYLE: Send ABSOLUTE timestamp (boot time in microseconds)
     * CLIENT will calculate offset directly: offset = receive_time - beacon_time
     * Offset magnitude doesn't matter - only stability (drift) matters
     */
    beacon->timestamp_us = esp_timer_get_time();  /* Absolute boot time */
    beacon->session_ref_ms = g_time_sync_state.session_start_ms;
    beacon->sequence = ++g_time_sync_state.sync_sequence;  /* Increment and use */
    beacon->quality_score = g_time_sync_state.quality.quality_score;

    /* Phase 3: Include motor epoch for bilateral coordination */
    beacon->motor_epoch_us = g_time_sync_state.motor_epoch_us;
    beacon->motor_cycle_ms = g_time_sync_state.motor_cycle_ms;

    /* Calculate and append checksum */
    beacon->checksum = calculate_crc16((const uint8_t *)beacon, sizeof(time_sync_beacon_t) - sizeof(uint16_t));

    ESP_LOGD(TAG, "Beacon generated (seq: %u, time: %llu μs, quality: %u%%, motor_epoch: %llu μs, cycle: %lu ms)",
             beacon->sequence, beacon->timestamp_us, beacon->quality_score,
             beacon->motor_epoch_us, beacon->motor_cycle_ms);

    return ESP_OK;
}

esp_err_t time_sync_get_quality(time_sync_quality_t *quality)
{
    /* JPL Rule 7: Validate pointer */
    if (quality == NULL) {
        ESP_LOGE(TAG, "NULL quality pointer");
        return ESP_ERR_INVALID_ARG;
    }

    if (!g_time_sync_state.initialized) {
        ESP_LOGE(TAG, "Not initialized");
        return ESP_ERR_INVALID_STATE;
    }

    /* Copy quality metrics */
    memcpy(quality, &g_time_sync_state.quality, sizeof(time_sync_quality_t));

    return ESP_OK;
}

sync_state_t time_sync_get_state(void)
{
    return g_time_sync_state.state;
}

time_sync_role_t time_sync_get_role(void)
{
    return g_time_sync_state.role;
}

esp_err_t time_sync_get_clock_offset(int64_t *offset_us)
{
    /* JPL Rule 7: Validate pointer */
    if (offset_us == NULL) {
        ESP_LOGE(TAG, "NULL offset pointer");
        return ESP_ERR_INVALID_ARG;
    }

    if (!g_time_sync_state.initialized) {
        ESP_LOGE(TAG, "Not initialized");
        return ESP_ERR_INVALID_STATE;
    }

    /* Return calculated clock offset (CLIENT - SERVER) */
    *offset_us = g_time_sync_state.clock_offset_us;
    return ESP_OK;
}

uint32_t time_sync_calculate_expected_drift(uint32_t elapsed_ms)
{
    /* ESP32-C6 crystal: ±10 PPM
     * Drift (μs) = (elapsed_ms × 1000 μs/ms) × (drift_ppm / 1,000,000)
     *             = elapsed_ms × drift_ppm / 1000
     */
    uint32_t drift_us = (elapsed_ms * TIME_SYNC_CRYSTAL_DRIFT_PPM) / 1000;
    return drift_us;
}

esp_err_t time_sync_force_resync(void)
{
    if (!g_time_sync_state.initialized) {
        ESP_LOGE(TAG, "Not initialized");
        return ESP_ERR_INVALID_STATE;
    }

    if (g_time_sync_state.state != SYNC_STATE_SYNCED &&
        g_time_sync_state.state != SYNC_STATE_DRIFT_DETECTED) {
        ESP_LOGW(TAG, "Not in synchronized state");
        return ESP_ERR_INVALID_STATE;
    }

    /* Reset to minimum interval for aggressive resync */
    g_time_sync_state.sync_interval_ms = TIME_SYNC_INTERVAL_MIN_MS;
    g_time_sync_state.last_sync_ms = 0;  /* Force immediate sync */

    ESP_LOGI(TAG, "Forced resync triggered (interval reset to %lu ms)", TIME_SYNC_INTERVAL_MIN_MS);

    return ESP_OK;
}

/*******************************************************************************
 * PRIVATE HELPER FUNCTIONS
 ******************************************************************************/

/**
 * @brief Calculate CRC-16 checksum for message integrity
 *
 * Uses CRC-16-CCITT polynomial for message validation.
 * JPL Rule 2: Bounded loop (iterates over data length).
 *
 * @param data Pointer to data buffer
 * @param length Number of bytes to process
 * @return CRC-16 checksum value
 */
static uint16_t calculate_crc16(const uint8_t *data, size_t length)
{
    uint16_t crc = 0xFFFF;

    /* JPL Rule 2: Loop bounded by length parameter */
    for (size_t i = 0; i < length && i < TIME_SYNC_MSG_SIZE; i++) {
        crc ^= (uint16_t)data[i] << 8;

        /* Process 8 bits */
        for (uint8_t bit = 0; bit < 8; bit++) {
            if (crc & 0x8000) {
                crc = (crc << 1) ^ CRC16_POLY;
            } else {
                crc <<= 1;
            }
        }
    }

    return crc;
}

/**
 * @brief Calculate sync quality score (0-100%) based on drift prediction accuracy
 *
 * PHASE 6q (Nov 29, 2025): Fixed to measure DRIFT PREDICTION ACCURACY, not magnitude.
 * Aligns with AD041 Predictive Bilateral Synchronization protocol.
 *
 * Quality measures how well drift-rate compensation predicts actual drift.
 * This determines adaptive beacon interval (10-60s):
 * - High quality (predictable drift) → Extend beacons to 60s
 * - Low quality (unpredictable drift) → Keep beacons at 10s
 *
 * Quality based on prediction error:
 * - |actual_drift - expected_drift| < 1ms → EXCELLENT (95%) → 60s beacons
 * - |actual_drift - expected_drift| < 5ms → GOOD (75%) → 30-40s beacons
 * - |actual_drift - expected_drift| < 15ms → FAIR (50%) → 10-20s beacons
 * - |actual_drift - expected_drift| > 30ms → FAILED (0%) → 10s minimum
 *
 * @param actual_drift_us Actual measured drift since last beacon (stable_drift_us)
 * @param expected_drift_us Predicted drift from drift-rate extrapolation
 * @param rtt_us Round-trip time (for future RTT variance penalty, not currently used)
 * @return Quality score (0-100%): EXCELLENT=95, GOOD=75, FAIR=50, POOR=25, FAILED=0
 */
static uint8_t calculate_sync_quality(int32_t actual_drift_us, uint32_t expected_drift_us, uint32_t rtt_us)
{
    /* PHASE 6q (Nov 29, 2025): Fixed to measure DRIFT PREDICTION ACCURACY, not magnitude.
     * Aligns with AD041 Predictive Bilateral Synchronization philosophy.
     *
     * Quality measures how well we can PREDICT drift using drift-rate compensation.
     * High quality → drift is predictable → beacons can extend to 60s.
     * Low quality → drift is unpredictable → beacons stay at 10s.
     */

    /* Calculate prediction error: How well did our drift-rate model predict actual drift?
     * This is the KEY metric for adaptive beacon intervals (AD041).
     */
    int32_t prediction_error_us = actual_drift_us - (int32_t)expected_drift_us;
    uint32_t abs_prediction_error = (prediction_error_us < 0)
                                    ? (uint32_t)(-prediction_error_us)
                                    : (uint32_t)prediction_error_us;

    /* Quality thresholds based on prediction accuracy (AD041 adaptive intervals):
     *
     * EXCELLENT (95%): Prediction within 1ms → Drift is highly predictable
     *   - Beacons can safely extend to 60s
     *   - Example: Actual=-50ms, Expected=-48ms → Error=2ms → 95% quality ✅
     *
     * GOOD (75%): Prediction within 5ms → Drift is predictable
     *   - Beacons can extend to 30-40s
     *
     * FAIR (50%): Prediction within 15ms → Drift moderately predictable
     *   - Beacons should stay at 10-20s
     *
     * POOR (25%): Prediction within 30ms → Drift poorly predictable
     *   - Beacons must stay at 10s minimum
     *
     * FAILED (0%): Prediction error > 30ms → Drift unpredictable
     *   - Cannot safely extend beacon intervals
     */
    if (abs_prediction_error < 1000) {
        return SYNC_QUALITY_EXCELLENT;  /* < 1ms prediction error */
    } else if (abs_prediction_error < 5000) {
        return SYNC_QUALITY_GOOD;       /* < 5ms prediction error */
    } else if (abs_prediction_error < 15000) {
        return SYNC_QUALITY_FAIR;       /* < 15ms prediction error */
    } else if (abs_prediction_error < 30000) {
        return SYNC_QUALITY_POOR;       /* < 30ms prediction error */
    } else {
        return 0;  /* > 30ms prediction error - model failure */
    }

    /* Note: RTT passed for future enhancement (penalize high RTT variance)
     * but not currently used. AD041 focuses on prediction accuracy.
     */
}

/**
 * @brief Update quality metrics with new sync sample
 *
 * NTP-STYLE: Tracks offset DRIFT (change between samples), not absolute offset magnitude.
 * A stable offset (even if large) is excellent quality.
 * A changing offset (even if small) indicates clock drift.
 *
 * JPL Rule 2: Bounded by SYNC_QUALITY_WINDOW constant.
 *
 * @param offset_change_us Change in offset since last beacon (drift)
 * @param rtt_us New round-trip time sample
 */
static void update_quality_metrics(int32_t offset_change_us, uint32_t rtt_us, int32_t drift_rate_us_per_s)
{
    time_sync_quality_t *q = &g_time_sync_state.quality;

    /* JPL Rule 5: Defensive bounds checking to prevent division by zero
     * Note: With Issue #2 fix, this should never trigger, but guard anyway
     */
    if (q->samples_collected == 0) {
        ESP_LOGW(TAG, "update_quality_metrics() called with samples_collected=0, ignoring");
        return;
    }

    /* Calculate time since last sync to convert drift rate to absolute drift
     * Drift rate is μs/s, so over interval_ms milliseconds:
     * stable_drift_us = drift_rate_us_per_s * (interval_ms / 1000)
     */
    uint32_t interval_ms = (uint32_t)(esp_timer_get_time() / 1000) - g_time_sync_state.last_sync_ms;
    int32_t stable_drift_us = (drift_rate_us_per_s * (int32_t)interval_ms) / 1000;

    /* Track DRIFT using stable drift rate (not noisy RTT-based offset change)
     * This filters out BLE latency variation that makes drift appear unstable.
     *
     * CRITICAL: samples_collected is uint32_t, so (samples_collected - 1) causes
     * unsigned promotion of the entire expression. When drift is negative
     * (e.g., -69 μs), it wraps to UINT32_MAX - 69 + 1, producing garbage values like
     * 2147483613 μs instead of -34 μs. Fix: Cast to signed and calculate before increment.
     */
    if (q->samples_collected < TIME_SYNC_QUALITY_WINDOW) {
        /* Calculate new average using current count, then increment */
        int32_t count = (int32_t)q->samples_collected;  /* Cast to prevent unsigned promotion */
        q->avg_drift_us = (q->avg_drift_us * count + stable_drift_us) / (count + 1);
        q->samples_collected++;
    } else {
        /* Window full - use simple moving average with fixed window size */
        int32_t window = (int32_t)TIME_SYNC_QUALITY_WINDOW;  /* Cast to prevent unsigned promotion */
        q->avg_drift_us = (q->avg_drift_us * (window - 1) + stable_drift_us) / window;
    }

    /* Update max drift using stable value */
    uint32_t abs_stable_drift = (stable_drift_us < 0) ? (uint32_t)(-stable_drift_us) : (uint32_t)stable_drift_us;
    if (abs_stable_drift > q->max_drift_us) {
        q->max_drift_us = abs_stable_drift;
    }

    /* Update RTT */
    q->last_rtt_us = rtt_us;

    /* Calculate quality score using stable drift (filters out RTT variation)
     * The stable_drift_us represents real clock drift based on filtered drift rate,
     * not RTT-induced offset changes (which can be ±30ms when RTT varies ±60ms).
     */
    uint32_t expected_drift = time_sync_calculate_expected_drift(interval_ms);
    q->quality_score = calculate_sync_quality(stable_drift_us, expected_drift, rtt_us);
}

/**
 * @brief Adjust sync interval based on quality (exponential backoff)
 *
 * Implements adaptive sync interval:
 * - Start at 10s (aggressive)
 * - Increase to 20s, 40s, 60s (max) if quality remains good
 * - Reset to 10s if quality degrades
 *
 * JPL Rule 2: Bounded interval adjustment (max = 60s).
 *
 * @return ESP_OK on success
 */
static esp_err_t adjust_sync_interval(void)
{
    time_sync_quality_t *q = &g_time_sync_state.quality;

    /* If quality excellent and we have enough samples, increase interval */
    if (q->quality_score >= SYNC_QUALITY_GOOD && q->samples_collected >= 3) {
        /* Double interval up to max */
        if (g_time_sync_state.sync_interval_ms < TIME_SYNC_INTERVAL_MAX_MS) {
            g_time_sync_state.sync_interval_ms = g_time_sync_state.sync_interval_ms * 2;

            /* Clamp to max */
            if (g_time_sync_state.sync_interval_ms > TIME_SYNC_INTERVAL_MAX_MS) {
                g_time_sync_state.sync_interval_ms = TIME_SYNC_INTERVAL_MAX_MS;
            }

            ESP_LOGI(TAG, "Sync interval increased to %lu ms (quality: %u%%)",
                     g_time_sync_state.sync_interval_ms, q->quality_score);
        }
    }
    /* If quality poor, reset to minimum interval */
    else if (q->quality_score < SYNC_QUALITY_FAIR) {
        if (g_time_sync_state.sync_interval_ms > TIME_SYNC_INTERVAL_MIN_MS) {
            g_time_sync_state.sync_interval_ms = TIME_SYNC_INTERVAL_MIN_MS;
            ESP_LOGW(TAG, "Sync interval reset to %lu ms (quality degraded: %u%%)",
                     g_time_sync_state.sync_interval_ms, q->quality_score);
        }
    }

    return ESP_OK;
}

/*******************************************************************************
 * PUBLIC API IMPLEMENTATION (CONTINUED)
 ******************************************************************************/

/**
 * @brief Check if sync beacon should be sent (SERVER only)
 *
 * Public function for motor task to determine when to send sync beacons.
 * Determines if enough time has elapsed since last sync based on
 * adaptive interval.
 *
 * @return true if beacon should be sent, false otherwise
 */
bool time_sync_should_send_beacon(void)
{
    uint32_t now_ms = (uint32_t)(esp_timer_get_time() / 1000);
    uint32_t elapsed_ms = now_ms - g_time_sync_state.last_sync_ms;

    return (elapsed_ms >= g_time_sync_state.sync_interval_ms);
}

/**
 * @brief Get current adaptive sync interval
 *
 * Returns the current sync interval in milliseconds, which is adaptively
 * adjusted based on sync quality (10-60s range).
 *
 * @return Current sync interval in milliseconds
 */
uint32_t time_sync_get_interval_ms(void)
{
    return g_time_sync_state.sync_interval_ms;
}

/*******************************************************************************
 * MOTOR EPOCH SYNCHRONIZATION (Phase 3)
 ******************************************************************************/

/**
 * @brief Set motor epoch timestamp (SERVER only)
 *
 * Called by SERVER's motor task when it starts motor cycles. This establishes
 * the timing reference that CLIENT will use for bilateral synchronization.
 *
 * Phase 3: Bilateral motor coordination via synchronized epoch
 *
 * @param epoch_us Motor cycle start time in microseconds (synchronized time)
 * @param cycle_ms Motor cycle period in milliseconds (e.g., 2000ms for Mode 0)
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_ARG if cycle_ms is zero or unreasonably large
 * @return ESP_ERR_INVALID_STATE if not initialized or invalid role (must be SERVER or CLIENT)
 */
esp_err_t time_sync_set_motor_epoch(uint64_t epoch_us, uint32_t cycle_ms)
{
    /* JPL Rule 5: Validate parameters */
    if (cycle_ms == 0 || cycle_ms > 10000) {  /* Max 10s cycle */
        ESP_LOGE(TAG, "Invalid cycle_ms: %lu (must be 1-10000ms)", cycle_ms);
        return ESP_ERR_INVALID_ARG;
    }

    if (!g_time_sync_state.initialized) {
        ESP_LOGE(TAG, "Not initialized");
        return ESP_ERR_INVALID_STATE;
    }

    /* Phase 6: Allow both SERVER and CLIENT to set motor epoch
     * - SERVER: Sets its own motor epoch when motors start
     * - CLIENT: Sets motor epoch when receiving MOTOR_STARTED notification from SERVER
     * - STANDALONE: Rejected (doesn't participate in bilateral coordination)
     */
    if (g_time_sync_state.role != TIME_SYNC_ROLE_SERVER &&
        g_time_sync_state.role != TIME_SYNC_ROLE_CLIENT) {
        ESP_LOGE(TAG, "Invalid role for motor epoch (role=%d, must be SERVER or CLIENT)",
                 g_time_sync_state.role);
        return ESP_ERR_INVALID_STATE;
    }

    /* Store motor epoch reference */
    g_time_sync_state.motor_epoch_us = epoch_us;
    g_time_sync_state.motor_cycle_ms = cycle_ms;
    g_time_sync_state.motor_epoch_valid = true;

    ESP_LOGI(TAG, "Motor epoch set: %llu us, cycle: %lu ms", epoch_us, cycle_ms);

    return ESP_OK;
}

/**
 * @brief Get motor epoch timestamp (CLIENT only)
 *
 * Called by CLIENT's motor task to retrieve SERVER's motor cycle timing reference.
 * CLIENT uses this to calculate when to activate its own motors for proper
 * bilateral alternation.
 *
 * Phase 3: Bilateral motor coordination via synchronized epoch
 *
 * @param epoch_us [out] Pointer to store motor epoch timestamp (microseconds)
 * @param cycle_ms [out] Pointer to store motor cycle period (milliseconds)
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_ARG if pointers are NULL
 * @return ESP_ERR_INVALID_STATE if motor epoch not yet set
 */
esp_err_t time_sync_get_motor_epoch(uint64_t *epoch_us, uint32_t *cycle_ms)
{
    /* JPL Rule 7: Validate pointers */
    if (epoch_us == NULL || cycle_ms == NULL) {
        ESP_LOGE(TAG, "NULL pointer(s) passed to time_sync_get_motor_epoch");
        return ESP_ERR_INVALID_ARG;
    }

    if (!g_time_sync_state.initialized) {
        ESP_LOGE(TAG, "Not initialized");
        return ESP_ERR_INVALID_STATE;
    }

    if (!g_time_sync_state.motor_epoch_valid) {
        ESP_LOGW(TAG, "Motor epoch not yet set");
        return ESP_ERR_INVALID_STATE;
    }

    /* PHASE 6r: Safety timeout - expire motor epoch if disconnected > 2 minutes
     *
     * Rationale: During disconnect, CLIENT uses frozen drift rate to continue
     * bilateral alternation. However, unbounded drift accumulation is unsafe:
     * - Expected drift: ±2.4ms over 20 minutes (acceptable)
     * - Long disconnect: ±72ms over 60 minutes (approaching ±100ms spec limit)
     *
     * Solution: Automatically invalidate motor epoch after 2-minute disconnect
     * to prevent unbounded drift. Motor coordination stops gracefully.
     */
    if (g_time_sync_state.state == SYNC_STATE_DISCONNECTED) {
        uint64_t now_us = esp_timer_get_time();
        uint32_t now_ms = (uint32_t)(now_us / 1000);
        uint32_t disconnect_duration_ms = now_ms - g_time_sync_state.last_sync_ms;

        /* 2-minute safety timeout */
        if (disconnect_duration_ms > 120000) {
            ESP_LOGW(TAG, "Motor epoch expired (disconnect > 2 min, duration: %lu ms)",
                     (unsigned long)disconnect_duration_ms);
            ESP_LOGW(TAG, "Stopping motor coordination until reconnection");
            g_time_sync_state.motor_epoch_valid = false;
            return ESP_ERR_TIMEOUT;
        }
    }

    /* Return motor epoch reference */
    *epoch_us = g_time_sync_state.motor_epoch_us;
    *cycle_ms = g_time_sync_state.motor_cycle_ms;

    return ESP_OK;
}

/*******************************************************************************
 * NTP-STYLE HANDSHAKE IMPLEMENTATION (Phase 6k - Precision Bootstrap)
 ******************************************************************************/

/**
 * @brief Check if initial NTP handshake is complete
 */
bool time_sync_is_handshake_complete(void)
{
    return g_time_sync_state.handshake_complete;
}

/**
 * @brief Initiate NTP-style handshake (CLIENT only)
 *
 * CLIENT calls this to start the 3-way handshake. Stores T1 internally
 * and returns it for the caller to include in the TIME_REQUEST message.
 */
esp_err_t time_sync_initiate_handshake(uint64_t *t1_out)
{
    /* JPL Rule 7: Validate pointer */
    if (t1_out == NULL) {
        ESP_LOGE(TAG, "NULL pointer passed to time_sync_initiate_handshake");
        return ESP_ERR_INVALID_ARG;
    }

    if (!g_time_sync_state.initialized) {
        ESP_LOGE(TAG, "Not initialized");
        return ESP_ERR_INVALID_STATE;
    }

    if (g_time_sync_state.role != TIME_SYNC_ROLE_CLIENT) {
        ESP_LOGE(TAG, "Not CLIENT role (current role: %d)", g_time_sync_state.role);
        return ESP_ERR_INVALID_STATE;
    }

    if (g_time_sync_state.handshake_complete) {
        ESP_LOGW(TAG, "Handshake already complete");
        return ESP_ERR_INVALID_STATE;
    }

    /* Record T1 (CLIENT send time) */
    uint64_t t1 = esp_timer_get_time();
    g_time_sync_state.handshake_t1_us = t1;
    *t1_out = t1;

    ESP_LOGI(TAG, "Handshake initiated: T1=%llu μs", t1);

    return ESP_OK;
}

/**
 * @brief Process handshake request (SERVER only)
 *
 * SERVER receives TIME_REQUEST, records T2, and returns T3 for the response.
 * The caller constructs the TIME_RESPONSE message with T1, T2, T3.
 */
esp_err_t time_sync_process_handshake_request(uint64_t t1_client_send_us,
                                               uint64_t t2_server_recv_us,
                                               uint64_t *t3_server_send_out)
{
    /* JPL Rule 7: Validate pointer */
    if (t3_server_send_out == NULL) {
        ESP_LOGE(TAG, "NULL pointer passed to time_sync_process_handshake_request");
        return ESP_ERR_INVALID_ARG;
    }

    if (!g_time_sync_state.initialized) {
        ESP_LOGE(TAG, "Not initialized");
        return ESP_ERR_INVALID_STATE;
    }

    if (g_time_sync_state.role != TIME_SYNC_ROLE_SERVER) {
        ESP_LOGE(TAG, "Not SERVER role (current role: %d)", g_time_sync_state.role);
        return ESP_ERR_INVALID_STATE;
    }

    /* T3 = SERVER send time (now, just before sending response) */
    *t3_server_send_out = esp_timer_get_time();

    ESP_LOGI(TAG, "Handshake request processed: T1=%llu, T2=%llu, T3=%llu μs",
             t1_client_send_us, t2_server_recv_us, *t3_server_send_out);

    return ESP_OK;
}

/**
 * @brief Process handshake response (CLIENT only)
 *
 * CLIENT receives TIME_RESPONSE with T1, T2, T3 and records T4.
 * Calculates precise offset using NTP formula:
 *   offset = ((T2-T1) + (T3-T4)) / 2
 *   RTT = (T4-T1) - (T3-T2)
 *
 * This becomes the EWMA filter's initial value (precise bootstrap).
 */
esp_err_t time_sync_process_handshake_response(uint64_t t1_us, uint64_t t2_us,
                                                uint64_t t3_us, uint64_t t4_us)
{
    if (!g_time_sync_state.initialized) {
        ESP_LOGE(TAG, "Not initialized");
        return ESP_ERR_INVALID_STATE;
    }

    if (g_time_sync_state.role != TIME_SYNC_ROLE_CLIENT) {
        ESP_LOGE(TAG, "Not CLIENT role (current role: %d)", g_time_sync_state.role);
        return ESP_ERR_INVALID_STATE;
    }

    if (g_time_sync_state.handshake_complete) {
        ESP_LOGW(TAG, "Handshake already complete, ignoring response");
        return ESP_ERR_INVALID_STATE;
    }

    /* Verify T1 matches what we sent (sanity check) */
    if (t1_us != g_time_sync_state.handshake_t1_us) {
        ESP_LOGW(TAG, "T1 mismatch: sent=%llu, received=%llu (possible stale response)",
                 g_time_sync_state.handshake_t1_us, t1_us);
        /* Continue anyway - the offset calculation is still valid */
    }

    /* NTP offset formula: offset = ((T2-T1) + (T3-T4)) / 2
     *
     * Interpretation:
     *   (T2-T1) = One-way delay + clock offset (client→server)
     *   (T3-T4) = -(One-way delay + clock offset) (server→client, negated)
     *   Average = clock offset (delays cancel if symmetric)
     *
     * Sign convention: offset > 0 means CLIENT is ahead of SERVER
     */
    int64_t d1 = (int64_t)t2_us - (int64_t)t1_us;  /* T2 - T1 */
    int64_t d2 = (int64_t)t3_us - (int64_t)t4_us;  /* T3 - T4 */
    int64_t offset = (d1 + d2) / 2;

    /* RTT formula: RTT = (T4-T1) - (T3-T2)
     *
     * Interpretation:
     *   (T4-T1) = Total elapsed time on CLIENT
     *   (T3-T2) = Processing time on SERVER
     *   RTT = Network round-trip time (excludes SERVER processing)
     */
    int64_t rtt = ((int64_t)t4_us - (int64_t)t1_us) - ((int64_t)t3_us - (int64_t)t2_us);

    /* Bootstrap EWMA filter with precise offset */
    g_time_sync_state.clock_offset_us = offset;
    g_time_sync_state.handshake_complete = true;

    /* Update quality metrics with measured RTT */
    g_time_sync_state.quality.last_rtt_us = (uint32_t)(rtt > 0 ? rtt : 0);
    g_time_sync_state.quality.samples_collected = 1;
    g_time_sync_state.quality.quality_score = 95;  /* Start high (precise measurement) */

    /* Transition to SYNCED state */
    g_time_sync_state.state = SYNC_STATE_SYNCED;
    g_time_sync_state.last_sync_ms = (uint32_t)(t4_us / 1000);

    ESP_LOGI(TAG, "Handshake complete: offset=%lld μs, RTT=%lld μs (T1=%llu, T2=%llu, T3=%llu, T4=%llu)",
             offset, rtt, t1_us, t2_us, t3_us, t4_us);

    return ESP_OK;
}

/**
 * @brief Set motor epoch from handshake response (CLIENT only)
 *
 * Called by CLIENT when receiving motor_epoch in TIME_RESPONSE.
 * This avoids waiting 10s for next beacon to get motor epoch.
 */
esp_err_t time_sync_set_motor_epoch_from_handshake(uint64_t epoch_us, uint32_t cycle_ms)
{
    if (epoch_us == 0 || cycle_ms == 0) {
        return ESP_ERR_INVALID_ARG;
    }

    if (!g_time_sync_state.initialized) {
        ESP_LOGE(TAG, "Not initialized");
        return ESP_ERR_INVALID_STATE;
    }

    /* Store motor epoch (same as beacon processing does) */
    g_time_sync_state.motor_epoch_us = epoch_us;
    g_time_sync_state.motor_cycle_ms = cycle_ms;
    g_time_sync_state.motor_epoch_valid = true;

    ESP_LOGI(TAG, "Motor epoch set from handshake: %llu μs, cycle: %lu ms", epoch_us, cycle_ms);

    return ESP_OK;
}

/*******************************************************************************
 * BUG #27 FIX: TWO-WAY RTT MEASUREMENT PER BEACON
 ******************************************************************************/

/**
 * @brief Record beacon T1 timestamp (SERVER only)
 */
esp_err_t time_sync_record_beacon_t1(uint64_t t1_us, uint8_t sequence)
{
    if (!g_time_sync_state.initialized) {
        return ESP_ERR_INVALID_STATE;
    }

    if (g_time_sync_state.role != TIME_SYNC_ROLE_SERVER) {
        return ESP_ERR_INVALID_STATE;
    }

    g_time_sync_state.last_beacon_t1_us = t1_us;
    g_time_sync_state.last_beacon_seq = sequence;
    g_time_sync_state.last_beacon_t1_valid = true;

    return ESP_OK;
}

/**
 * @brief Process beacon response (SERVER only)
 *
 * Calculates RTT and precise offset using NTP formula.
 * Also implements Fix #2: Update clock_offset_us from measured two-way data
 * instead of preserving stale handshake offset.
 */
esp_err_t time_sync_process_beacon_response(uint8_t sequence, uint64_t t2_us,
                                            uint64_t t3_us, uint64_t t4_us)
{
    if (!g_time_sync_state.initialized) {
        ESP_LOGE(TAG, "Beacon response: Not initialized");
        return ESP_ERR_INVALID_STATE;
    }

    if (g_time_sync_state.role != TIME_SYNC_ROLE_SERVER) {
        ESP_LOGE(TAG, "Beacon response: Not SERVER role");
        return ESP_ERR_INVALID_STATE;
    }

    if (!g_time_sync_state.last_beacon_t1_valid) {
        ESP_LOGW(TAG, "Beacon response: No T1 stored for matching");
        return ESP_ERR_NOT_FOUND;
    }

    if (sequence != g_time_sync_state.last_beacon_seq) {
        ESP_LOGW(TAG, "Beacon response: Sequence mismatch (got %u, expected %u)",
                 sequence, g_time_sync_state.last_beacon_seq);
        return ESP_ERR_INVALID_RESPONSE;
    }

    uint64_t t1_us = g_time_sync_state.last_beacon_t1_us;

    /* NTP formula:
     * offset = ((T2-T1) + (T3-T4)) / 2
     * RTT = (T4-T1) - (T3-T2)
     *
     * Note: offset is CLIENT_time - SERVER_time
     * Positive offset = CLIENT clock ahead of SERVER
     */
    int64_t t2_minus_t1 = (int64_t)t2_us - (int64_t)t1_us;
    int64_t t3_minus_t4 = (int64_t)t3_us - (int64_t)t4_us;
    int64_t offset = (t2_minus_t1 + t3_minus_t4) / 2;

    /* CRITICAL FIX (Phase 6): Calculate RTT using signed arithmetic to prevent overflow
     *
     * Root cause: The subtraction (t4_us - t1_us) can produce huge positive values when
     * t4_us < t1_us due to unsigned wraparound. This creates astronomically large RTT
     * values (4.6×10^15 μs ≈ 147,000 years!) that corrupt drift calculations.
     *
     * Evidence: All RTT measurements in logs show RTT=4648207396655XXXXXX μs pattern
     *
     * Solution: Use signed arithmetic throughout to detect negative results
     */
    int64_t t4_minus_t1 = (int64_t)t4_us - (int64_t)t1_us;
    int64_t t3_minus_t2 = (int64_t)t3_us - (int64_t)t2_us;
    int64_t rtt = t4_minus_t1 - t3_minus_t2;

    /* Sanity check RTT - should be positive and reasonable (< 10 seconds) */
    if (rtt < 0) {
        ESP_LOGW(TAG, "Beacon response: Negative RTT (%lld μs) - time sync not stable yet, ignoring", rtt);
        return ESP_ERR_INVALID_RESPONSE;
    }

    if (rtt > 10000000) {  /* > 10 seconds = corrupt/overflow */
        ESP_LOGW(TAG, "Beacon response: RTT too large (%lld μs) - likely overflow, ignoring", rtt);
        return ESP_ERR_INVALID_RESPONSE;
    }

    if (rtt > 500000) {  /* > 500ms = suspect but not fatal */
        ESP_LOGW(TAG, "Beacon response: RTT unusually high (%lld μs) - possible BLE congestion", rtt);
        /* Continue anyway - might be real BLE latency spike */
    }

    /* Store measured RTT */
    g_time_sync_state.measured_rtt_us = (int32_t)rtt;
    g_time_sync_state.measured_rtt_valid = true;

    /* Track drift for diagnostics */
    int64_t old_offset = g_time_sync_state.clock_offset_us;
    int64_t drift_us = offset - old_offset;

    /* Fix #2: Update clock_offset_us with fresh two-way measurement
     * The handshake offset becomes stale as crystals drift.
     * Two-way measurement gives us accurate, current offset.
     */
    g_time_sync_state.clock_offset_us = offset;
    g_time_sync_state.quality.last_rtt_us = (uint32_t)rtt;

    /* Clear T1 to prevent reuse */
    g_time_sync_state.last_beacon_t1_valid = false;

    ESP_LOGI(TAG, "Beacon RTT measured: %ld μs, offset: %lld μs (drift: %+lld μs)",
             (long)rtt, offset, drift_us);

    return ESP_OK;
}

/**
 * @brief Get last measured RTT
 */
esp_err_t time_sync_get_measured_rtt(int32_t *rtt_us)
{
    if (rtt_us == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    if (g_time_sync_state.measured_rtt_valid) {
        *rtt_us = g_time_sync_state.measured_rtt_us;
        return ESP_OK;
    } else {
        /* Return default estimate */
        *rtt_us = 20000;  /* 20ms default */
        return ESP_ERR_NOT_FOUND;
    }
}

/**
 * @brief Update clock offset from two-way RTT measurement (CLIENT only)
 *
 * Bug #27 Fix: Called when CLIENT receives RTT_RESULT from SERVER.
 * SERVER calculated offset using proper NTP 4-timestamp formula,
 * so CLIENT can directly use this value instead of one-way estimate.
 */
esp_err_t time_sync_update_offset_from_rtt(int64_t offset_us, int32_t rtt_us, uint8_t sequence)
{
    if (!g_time_sync_state.initialized) {
        ESP_LOGE(TAG, "RTT offset update: Not initialized");
        return ESP_ERR_INVALID_STATE;
    }

    if (g_time_sync_state.role != TIME_SYNC_ROLE_CLIENT) {
        ESP_LOGE(TAG, "RTT offset update: Not CLIENT role");
        return ESP_ERR_INVALID_STATE;
    }

    /* CRITICAL FIX (Phase 6): Validate RTT and offset before accepting */
    if (rtt_us < 0 || rtt_us > 10000000) { /* <0 or >10s */
        ESP_LOGW(TAG, "RTT offset update: RTT out of range (%ld μs), rejecting", (long)rtt_us);
        return ESP_ERR_INVALID_ARG;
    }
    if (offset_us > 50000000 || offset_us < -50000000) { /* >50s or <-50s */
        ESP_LOGW(TAG, "RTT offset update: Offset too large (%lld μs), rejecting", offset_us);
        return ESP_ERR_INVALID_ARG;
    }

    /* Store the old offset before updating, for drift calculation */
    int64_t old_offset = g_time_sync_state.clock_offset_us;
    int64_t drift_us = offset_us - old_offset;

    /* Update clock offset with the new, precise two-way measurement */
    g_time_sync_state.clock_offset_us = offset_us;

    /* DRIFT RATE CALCULATION (Gemini Improvement - November 30, 2025)
     *
     * Historical Context:
     * - Original implementation calculated drift from one-way beacon timestamps
     * - Beacons used static 20ms RTT estimate when actual RTT varies (50-100ms typical)
     * - This introduced significant timing noise into drift calculations
     *
     * Current Approach (Post-Gemini Refactor):
     * - Calculate drift from change in RTT-compensated offset (two-way NTP protocol)
     * - Uses measured RTT from beacon response round-trip
     * - Precision improvement: ~50-100ms beacon noise → ~10-20ms RTT measurement accuracy
     * - Same EWMA filtering algorithm (70/30 alpha) applied to filtered data
     *
     * Benefits:
     * - More accurate drift rate for predictive synchronization (Phase 6k)
     * - Better quality metrics (based on stable drift tracking)
     * - Aligns with Phase 6r drift freeze on disconnect (RTT stops → drift freezes)
     *
     * Formula: drift_rate = (offset_change_us * 1000) / interval_ms
     * Units: μs/s (microseconds per second)
     */
    uint64_t now_us = esp_timer_get_time();
    if (g_time_sync_state.last_rtt_update_ms > 0) {
        uint32_t interval_ms = (uint32_t)(now_us / 1000) - g_time_sync_state.last_rtt_update_ms;
        if (interval_ms > 100 && interval_ms < 120000) { /* 100ms to 2 minutes */
            int32_t instant_drift_rate = (int32_t)((drift_us * 1000) / (int64_t)interval_ms);

            if (!g_time_sync_state.drift_rate_valid) {
                g_time_sync_state.drift_rate_us_per_s = instant_drift_rate;
                g_time_sync_state.drift_rate_valid = true;
            } else {
                int32_t alpha = TIME_SYNC_EWMA_ALPHA_PCT;
                int32_t prev_rate = g_time_sync_state.drift_rate_us_per_s;
                g_time_sync_state.drift_rate_us_per_s = (alpha * instant_drift_rate + (100 - alpha) * prev_rate) / 100;
            }
        }
    }

    /* Update timestamps and quality metrics */
    g_time_sync_state.last_rtt_update_ms = (uint32_t)(now_us / 1000);
    g_time_sync_state.measured_rtt_us = rtt_us;
    g_time_sync_state.measured_rtt_valid = true;
    g_time_sync_state.quality.last_rtt_us = (uint32_t)(rtt_us > 0 ? rtt_us : 0);

    int32_t drift_rate = g_time_sync_state.drift_rate_valid ? g_time_sync_state.drift_rate_us_per_s : 0;
    if (g_time_sync_state.quality.samples_collected > 0) {
        update_quality_metrics((int32_t)drift_us, (uint32_t)rtt_us, drift_rate);
    }

    /* Fix Option 2: Clear DRIFT_DETECTED state on successful RTT update
     * Since RTT updates now calculate drift (post-Gemini refactor), they should
     * also handle drift detection recovery. Successful RTT update with filtered
     * drift rate indicates sync is working properly again.
     */
    if (g_time_sync_state.state == SYNC_STATE_DRIFT_DETECTED) {
        g_time_sync_state.state = SYNC_STATE_SYNCED;
        g_time_sync_state.drift_detected = false;
        ESP_LOGI(TAG, "Resync complete (RTT update after drift detection, drift_rate=%ld μs/s)",
                 (long)drift_rate);
    }

    ESP_LOGI(TAG, "RTT offset updated: seq=%u, offset=%lld μs (raw_drift=%+lld μs), drift_rate=%+ld μs/s, rtt=%ld μs, quality=%u%%",
             sequence, offset_us, drift_us, (long)drift_rate, (long)rtt_us, g_time_sync_state.quality.quality_score);

    return ESP_OK;
}

/**
 * @brief Get filtered drift rate (Fix #2)
 */
esp_err_t time_sync_get_drift_rate(int32_t *drift_rate_us_per_s)
{
    if (drift_rate_us_per_s == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    if (!g_time_sync_state.initialized) {
        return ESP_ERR_INVALID_STATE;
    }

    if (g_time_sync_state.drift_rate_valid) {
        *drift_rate_us_per_s = g_time_sync_state.drift_rate_us_per_s;
        return ESP_OK;
    } else {
        /* No drift rate calculated yet - return 0 */
        *drift_rate_us_per_s = 0;
        return ESP_ERR_NOT_FOUND;
    }
}

/**
 * @brief Get predicted clock offset using drift rate (Phase 6k)
 *
 * Provides smoother offset estimation between RTT measurements by extrapolating
 * based on filtered drift rate. Reduces RTT asymmetry noise for bilateral coordination.
 */
esp_err_t time_sync_get_predicted_offset(int64_t *predicted_offset_us)
{
    if (predicted_offset_us == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    if (!g_time_sync_state.initialized) {
        return ESP_ERR_INVALID_STATE;
    }

    /* Fall back to raw offset if drift rate not yet calculated */
    if (!g_time_sync_state.drift_rate_valid || g_time_sync_state.last_rtt_update_ms == 0) {
        /* Phase 6l: Log first fallback only (avoid spam) */
        static bool fallback_logged = false;
        if (!fallback_logged) {
            ESP_LOGI(TAG, "Prediction: Using RAW offset (drift_rate_valid=%d, no RTT updates yet)",
                     g_time_sync_state.drift_rate_valid ? 1 : 0);
            fallback_logged = true;
        }
        *predicted_offset_us = g_time_sync_state.clock_offset_us;
        return ESP_ERR_NOT_FOUND;
    }

    /* Calculate time since last RTT update */
    uint32_t now_ms = (uint32_t)(esp_timer_get_time() / 1000);
    uint32_t elapsed_ms = now_ms - g_time_sync_state.last_rtt_update_ms;

    /* Extrapolate offset using drift rate
     * predicted_offset = last_offset + (drift_rate_us_per_s * elapsed_seconds)
     * drift_rate is μs/s, elapsed is ms, so:
     * predicted_offset = last_offset + (drift_rate * elapsed_ms / 1000)
     */
    int64_t drift_correction_us = ((int64_t)g_time_sync_state.drift_rate_us_per_s * (int64_t)elapsed_ms) / 1000;
    *predicted_offset_us = g_time_sync_state.clock_offset_us + drift_correction_us;

    /* Phase 6l: Log first prediction only (avoid spam) */
    static bool prediction_logged = false;
    if (!prediction_logged) {
        ESP_LOGI(TAG, "Prediction: Using DRIFT RATE (%d μs/s, elapsed=%lu ms, correction=%lld μs)",
                 g_time_sync_state.drift_rate_us_per_s, elapsed_ms, drift_correction_us);
        prediction_logged = true;
    }

    return ESP_OK;
}
