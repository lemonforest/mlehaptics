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
#include "time_sync_task.h"  /* Bug #57: For time_sync_task_trigger_beacons() */
#include "motor_task.h"      /* AD045: Pattern-broadcast - motor_get_duty_percent(), motor_get_current_mode() */
#include "esp_timer.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include <string.h>
#include <math.h>
#include <inttypes.h>  /* For portable PRId64/PRIu64 format specifiers */

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
static esp_err_t adjust_sync_interval(void);
static int64_t update_time_filter(int64_t raw_offset_us, uint64_t timestamp_us, uint8_t sequence, uint32_t rtt_us);

/* UTLP Phase 1: MDPS (Minimum Delay Packet Selection) */
static void mdps_add_sample(mdps_state_t *mdps, uint32_t rtt_us, int64_t offset_us);
static uint32_t mdps_get_percentile_rtt(mdps_state_t *mdps);
static bool mdps_is_min_delay_sample(mdps_state_t *mdps, uint32_t rtt_us);

/* UTLP Phase 1: Two-State Kalman Filter (offset + drift) */
static void kalman_init(kalman_state_t *kf, int64_t initial_offset_us, uint64_t timestamp_us);
static void kalman_predict(kalman_state_t *kf, uint64_t current_time_us);
static void kalman_update(kalman_state_t *kf, int64_t measured_offset_us, uint32_t rtt_us, uint64_t timestamp_us);

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

    /* Phase 6r: Initialize EMA filter (AD043) */
    memset(&g_time_sync_state.filter, 0, sizeof(time_filter_t));
    g_time_sync_state.filter.initialized = false;  /* Will be set true on first sample */

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
    /* EMA-filtered clock_offset_us also preserved for continued operation */

    /* Clear handshake state (forces fresh handshake on reconnection) */
    g_time_sync_state.handshake_complete = false;
    g_time_sync_state.handshake_t1_us = 0;

    ESP_LOGI(TAG, "Disconnected - motor coordination continues using EMA offset");
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

            /* Bug #36: Increment SERVER's sample counter to allow interval backoff
             * SERVER assumes 100% quality (authoritative), but needs sample history
             * to trust that quality is sustained over time before increasing interval */
            if (g_time_sync_state.quality.samples_collected < TIME_SYNC_QUALITY_WINDOW) {
                g_time_sync_state.quality.samples_collected++;
            }

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
    /* CLIENT: Apply EMA-filtered clock offset (AD045 simplified)
     * Emergency vehicle pattern: EMA filter provides ±30μs accuracy,
     * no need for drift rate extrapolation between beacons. */
    else if (g_time_sync_state.role == TIME_SYNC_ROLE_CLIENT) {
        int64_t offset_us = g_time_sync_state.clock_offset_us;

        /* IEEE 1588 bidirectional path asymmetry correction (v0.6.97)
         *
         * Problem: Forward offset (from beacons) is biased by path asymmetry.
         * Solution: Use bidirectional measurements to detect and correct bias.
         *
         * asymmetry = forward_offset + reverse_offset
         * - If symmetric: asymmetry ≈ 0 (fwd and rev cancel out)
         * - If asymmetric: asymmetry ≠ 0 (path difference biases offset)
         *
         * Correction: Subtract half the asymmetry from offset
         * - If asymmetry = +18ms, offset is biased by +9ms, so subtract 9ms
         */
        if (g_time_sync_state.asymmetry_valid) {
            int64_t correction_us = g_time_sync_state.asymmetry_us / 2;
            offset_us -= correction_us;
        }

        /* Apply offset (offset can be negative)
         * Clamp to zero if result would underflow (early boot edge case) */
        int64_t sync_time_signed = (int64_t)local_time_us - offset_us;
        if (sync_time_signed < 0) {
            ESP_LOGW(TAG, "time_sync_get_time: Underflow prevented (local=%" PRIu64 " μs, offset=%" PRId64 " μs)",
                     local_time_us, offset_us);
            *sync_time_us = 0;
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

    /* Phase 6r (AD043): Calculate one-way offset from beacon timestamp
     *
     * One-way delay estimation (simplified from NTP):
     *   raw_offset = client_rx_time - server_tx_time
     *
     * This includes both:
     * - Clock offset (what we want)
     * - BLE transmission delay (~10-50ms, varies with RTT)
     *
     * EMA filter (Step 2) smooths out the BLE delay variation.
     */
    int64_t raw_offset = (int64_t)receive_time_us - (int64_t)beacon->server_time_us;

    /* Phase 6r Step 2: Apply EMA filter with outlier detection (AD043)
     * Note: RTT=0 for one-way beacon (RTT only available after paired exchange)
     * UTLP Phase 1: MDPS uses RTT for minimum delay packet selection */
    int64_t filtered_offset = update_time_filter(raw_offset, receive_time_us, beacon->sequence, 0);
    g_time_sync_state.clock_offset_us = filtered_offset;

    g_time_sync_state.server_ref_time_us = beacon->server_time_us;
    g_time_sync_state.last_beacon_time_us = receive_time_us;  /* AD043: Store T2 for paired timestamps */
    g_time_sync_state.last_sync_ms = (uint32_t)(receive_time_us / 1000);
    g_time_sync_state.sync_sequence = beacon->sequence;
    g_time_sync_state.total_syncs++;

    /* Phase 3: Extract motor epoch for bilateral coordination */
    g_time_sync_state.motor_epoch_us = beacon->motor_epoch_us;
    g_time_sync_state.motor_cycle_ms = beacon->motor_cycle_ms;
    g_time_sync_state.motor_epoch_valid = (beacon->motor_epoch_us > 0 && beacon->motor_cycle_ms > 0);

    /* AD045: Pattern-broadcast validation - warn if mode mismatch
     * Both devices should be in same mode for proper bilateral coordination
     * Mode mismatch indicates button press or BLE command didn't propagate
     */
    mode_t client_mode = motor_get_current_mode();
    if (beacon->mode_id != (uint8_t)client_mode) {
        ESP_LOGW(TAG, "Mode mismatch! SERVER mode=%u, CLIENT mode=%u - timing may be incorrect",
                 beacon->mode_id, (uint8_t)client_mode);
    }

    /* Transition to SYNCED if this is first beacon */
    if (g_time_sync_state.state == SYNC_STATE_CONNECTED) {
        if (g_time_sync_state.quality.samples_collected == 0) {
            g_time_sync_state.quality.samples_collected = 1;
            g_time_sync_state.quality.quality_score = 50;
            ESP_LOGI(TAG, "Quality metrics initialized from beacon (raw offset, filter pending)");
        }
        g_time_sync_state.state = SYNC_STATE_SYNCED;
        ESP_LOGI(TAG, "Initial sync beacon processed (one-way timestamp)");
    }

    ESP_LOGD(TAG, "Beacon (seq: %u, epoch: %" PRIu64 ", cycle: %lu, duty: %u%%, mode: %u)",
             beacon->sequence, beacon->motor_epoch_us, beacon->motor_cycle_ms,
             beacon->duty_percent, beacon->mode_id);

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

    /* Populate beacon fields (AD045: Pattern-broadcast architecture)
     * - One-way timestamp for filtered time sync (AD043)
     * - Pattern info (epoch, period, duty, mode) for independent calculation
     * - CLIENT receives pattern once, calculates timing independently
     */
    beacon->server_time_us = esp_timer_get_time();  /* Absolute boot time */
    beacon->sequence = ++g_time_sync_state.sync_sequence;  /* Increment and use */

    /* Phase 3: Include motor epoch for bilateral coordination */
    beacon->motor_epoch_us = g_time_sync_state.motor_epoch_us;
    beacon->motor_cycle_ms = g_time_sync_state.motor_cycle_ms;

    /* AD045: Pattern-broadcast - include duty and mode for CLIENT validation */
    beacon->duty_percent = motor_get_duty_percent();
    beacon->mode_id = (uint8_t)motor_get_current_mode();

    /* Calculate and append checksum */
    beacon->checksum = calculate_crc16((const uint8_t *)beacon, sizeof(time_sync_beacon_t) - sizeof(uint16_t));

    ESP_LOGD(TAG, "Beacon generated (seq: %u, epoch: %" PRIu64 " μs, cycle: %lu ms, duty: %u%%, mode: %u)",
             beacon->sequence, beacon->motor_epoch_us,
             beacon->motor_cycle_ms, beacon->duty_percent, beacon->mode_id);

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

esp_err_t time_sync_update_asymmetry(int64_t asymmetry_us, int64_t rtt_us)
{
    if (!g_time_sync_state.initialized) {
        return ESP_ERR_INVALID_STATE;
    }

    /* Reject samples with high RTT (BLE congestion causes unreliable measurements) */
    if (rtt_us > (int64_t)TIME_SYNC_ASYMMETRY_RTT_MAX_US) {
        ESP_LOGD(TAG, "[ASYM] Rejected sample: RTT=%lld us > %lu us threshold",
                 (long long)rtt_us, (unsigned long)TIME_SYNC_ASYMMETRY_RTT_MAX_US);
        return ESP_ERR_INVALID_STATE;
    }

    /* EMA filter for asymmetry (alpha = 0.3 for moderate smoothing)
     * Use 30% weight for new samples to track changes while filtering noise
     */
    #define ASYMMETRY_EMA_ALPHA_PCT 30

    if (g_time_sync_state.asymmetry_sample_count == 0) {
        /* First sample - initialize directly */
        g_time_sync_state.asymmetry_us = asymmetry_us;
    } else {
        /* EMA update: new = (1-alpha)*old + alpha*sample */
        int64_t old = g_time_sync_state.asymmetry_us;
        g_time_sync_state.asymmetry_us =
            ((100 - ASYMMETRY_EMA_ALPHA_PCT) * old + ASYMMETRY_EMA_ALPHA_PCT * asymmetry_us) / 100;
    }

    g_time_sync_state.asymmetry_sample_count++;

    /* Mark valid once we have enough samples */
    if (g_time_sync_state.asymmetry_sample_count >= TIME_SYNC_MIN_ASYMMETRY_SAMPLES) {
        if (!g_time_sync_state.asymmetry_valid) {
            ESP_LOGI(TAG, "[ASYM] Correction enabled: %lld us (correction=%lld us)",
                     (long long)g_time_sync_state.asymmetry_us,
                     (long long)(g_time_sync_state.asymmetry_us / 2));
            g_time_sync_state.asymmetry_valid = true;
        }
    }

    ESP_LOGD(TAG, "[ASYM] Updated: %lld us (samples=%lu, valid=%d)",
             (long long)g_time_sync_state.asymmetry_us,
             (unsigned long)g_time_sync_state.asymmetry_sample_count,
             g_time_sync_state.asymmetry_valid);

    return ESP_OK;
}

esp_err_t time_sync_get_asymmetry(int64_t *asymmetry_us, bool *valid)
{
    if (asymmetry_us == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    *asymmetry_us = g_time_sync_state.asymmetry_us;
    if (valid != NULL) {
        *valid = g_time_sync_state.asymmetry_valid;
    }

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

/*******************************************************************************
 * UTLP PHASE 1: MDPS + KALMAN FILTER IMPLEMENTATION
 ******************************************************************************/

/**
 * @brief Add sample to MDPS ring buffer
 *
 * Stores RTT and offset for minimum delay packet selection.
 * JPL Rule 1: Fixed-size ring buffer (no dynamic allocation)
 *
 * @param mdps MDPS state structure
 * @param rtt_us Round-trip time in microseconds
 * @param offset_us Measured offset in microseconds
 */
static void mdps_add_sample(mdps_state_t *mdps, uint32_t rtt_us, int64_t offset_us)
{
    /* Store in ring buffer */
    mdps->rtt_history[mdps->head] = rtt_us;
    mdps->offset_history[mdps->head] = offset_us;

    /* Advance head and update count */
    mdps->head = (mdps->head + 1) % MDPS_RING_SIZE;
    if (mdps->count < MDPS_RING_SIZE) {
        mdps->count++;
    }
}

/**
 * @brief Get 10th percentile RTT from MDPS history
 *
 * Finds the N-th lowest RTT value where N = MDPS_PERCENTILE_IDX.
 * JPL Rule 2: Bounded loop (MDPS_RING_SIZE iterations max)
 *
 * @param mdps MDPS state structure
 * @return 10th percentile RTT value, or UINT32_MAX if insufficient samples
 */
static uint32_t mdps_get_percentile_rtt(mdps_state_t *mdps)
{
    if (mdps->count < MDPS_MIN_SAMPLES) {
        return UINT32_MAX;  /* Not enough samples */
    }

    /* Simple selection: find (MDPS_PERCENTILE_IDX+1)-th smallest RTT
     * For 16 samples and index 1, this gives us 2nd lowest (10th percentile)
     * JPL Rule 2: Bounded loop - max MDPS_RING_SIZE * MDPS_PERCENTILE_IDX iterations
     */
    uint32_t selected_rtts[MDPS_PERCENTILE_IDX + 1];
    for (uint8_t i = 0; i <= MDPS_PERCENTILE_IDX; i++) {
        selected_rtts[i] = UINT32_MAX;
    }

    /* Find lowest (MDPS_PERCENTILE_IDX+1) RTT values */
    for (uint8_t i = 0; i < mdps->count; i++) {
        uint32_t rtt = mdps->rtt_history[i];
        if (rtt == 0) continue;  /* Skip invalid samples */

        /* Insert into sorted selection array */
        for (uint8_t j = 0; j <= MDPS_PERCENTILE_IDX; j++) {
            if (rtt < selected_rtts[j]) {
                /* Shift larger values down */
                for (uint8_t k = MDPS_PERCENTILE_IDX; k > j; k--) {
                    selected_rtts[k] = selected_rtts[k - 1];
                }
                selected_rtts[j] = rtt;
                break;
            }
        }
    }

    mdps->min_rtt_us = selected_rtts[MDPS_PERCENTILE_IDX];
    return mdps->min_rtt_us;
}

/**
 * @brief Check if sample is within minimum delay threshold
 *
 * @param mdps MDPS state structure
 * @param rtt_us Sample RTT to check
 * @return true if RTT is within 10% of minimum, false otherwise
 */
static bool mdps_is_min_delay_sample(mdps_state_t *mdps, uint32_t rtt_us)
{
    if (rtt_us == 0 || mdps->min_rtt_us == 0 || mdps->min_rtt_us == UINT32_MAX) {
        return true;  /* Accept sample if RTT not available */
    }

    /* Accept samples within 10% of minimum RTT */
    uint32_t threshold = mdps->min_rtt_us + (mdps->min_rtt_us / 10);
    return (rtt_us <= threshold);
}

/**
 * @brief Initialize Kalman filter state
 *
 * @param kf Kalman filter state
 * @param initial_offset_us First offset measurement
 * @param timestamp_us Current timestamp
 */
static void kalman_init(kalman_state_t *kf, int64_t initial_offset_us, uint64_t timestamp_us)
{
    kf->offset_us = (float)initial_offset_us;
    kf->drift_ppm = 0.0f;  /* Assume no initial drift */

    /* Initialize covariance matrix (diagonal) */
    kf->P[0][0] = KALMAN_P_OFFSET_INIT;
    kf->P[0][1] = 0.0f;
    kf->P[1][0] = 0.0f;
    kf->P[1][1] = KALMAN_P_DRIFT_INIT;

    kf->R = KALMAN_R_INITIAL;
    kf->last_update_us = timestamp_us;
    kf->initialized = true;

    ESP_LOGI(TAG, "Kalman filter initialized: offset=%.0f µs, drift=%.3f ppm",
             kf->offset_us, kf->drift_ppm);
}

/**
 * @brief Kalman filter prediction step
 *
 * Propagates state estimate forward in time using drift rate.
 * State transition: offset += drift * dt
 *
 * @param kf Kalman filter state
 * @param current_time_us Current timestamp
 */
static void kalman_predict(kalman_state_t *kf, uint64_t current_time_us)
{
    if (!kf->initialized || current_time_us <= kf->last_update_us) {
        return;
    }

    /* Calculate time delta in seconds */
    float dt_s = (float)(current_time_us - kf->last_update_us) / 1000000.0f;

    /* State prediction: offset += drift_ppm * dt_s (drift is µs per second) */
    kf->offset_us += kf->drift_ppm * dt_s;

    /* Covariance prediction: P = F*P*F' + Q
     * F = [1, dt; 0, 1]
     * Q = [Q_offset*dt, 0; 0, Q_drift*dt]
     */
    float P00_new = kf->P[0][0] + 2.0f * dt_s * kf->P[0][1] + dt_s * dt_s * kf->P[1][1] + KALMAN_Q_OFFSET * dt_s;
    float P01_new = kf->P[0][1] + dt_s * kf->P[1][1];
    float P11_new = kf->P[1][1] + KALMAN_Q_DRIFT * dt_s;

    kf->P[0][0] = P00_new;
    kf->P[0][1] = P01_new;
    kf->P[1][0] = P01_new;  /* Symmetric */
    kf->P[1][1] = P11_new;
}

/**
 * @brief Kalman filter update step
 *
 * Incorporates new measurement to update state estimate.
 * Measurement noise R is adapted based on RTT (higher RTT = more noise).
 *
 * @param kf Kalman filter state
 * @param measured_offset_us New offset measurement
 * @param rtt_us Round-trip time (for adaptive noise estimation)
 * @param timestamp_us Measurement timestamp
 */
static void kalman_update(kalman_state_t *kf, int64_t measured_offset_us, uint32_t rtt_us, uint64_t timestamp_us)
{
    if (!kf->initialized) {
        kalman_init(kf, measured_offset_us, timestamp_us);
        return;
    }

    /* Run prediction step */
    kalman_predict(kf, timestamp_us);

    /* Adaptive measurement noise based on RTT
     * Higher RTT indicates more queueing delay uncertainty
     */
    if (rtt_us > 0) {
        /* R scales with RTT: base + (RTT/1000)^2 µs² */
        float rtt_factor = (float)rtt_us / 1000.0f;
        kf->R = KALMAN_R_MIN + rtt_factor * rtt_factor;
    }

    /* Kalman gain: K = P * H' * (H * P * H' + R)^-1
     * H = [1, 0] (we only measure offset, not drift)
     */
    float S = kf->P[0][0] + kf->R;  /* Innovation covariance */
    if (S < 1e-6f) S = 1e-6f;       /* Prevent division by zero */

    float K0 = kf->P[0][0] / S;     /* Kalman gain for offset */
    float K1 = kf->P[1][0] / S;     /* Kalman gain for drift */

    /* State update: x = x + K * (z - H*x) */
    float innovation = (float)measured_offset_us - kf->offset_us;
    kf->offset_us += K0 * innovation;
    kf->drift_ppm += K1 * innovation;

    /* Covariance update: P = (I - K*H) * P */
    float P00_new = (1.0f - K0) * kf->P[0][0];
    float P01_new = (1.0f - K0) * kf->P[0][1];
    float P10_new = -K1 * kf->P[0][0] + kf->P[1][0];
    float P11_new = -K1 * kf->P[0][1] + kf->P[1][1];

    kf->P[0][0] = P00_new;
    kf->P[0][1] = P01_new;
    kf->P[1][0] = P10_new;
    kf->P[1][1] = P11_new;

    kf->last_update_us = timestamp_us;
}

/*******************************************************************************
 * EMA FILTER WITH MDPS + KALMAN INTEGRATION
 ******************************************************************************/

/**
 * @brief Update EMA filter with new time offset sample (Phase 6r Step 2 - AD043)
 *
 * UTLP Phase 1: Implements hybrid EMA + MDPS + Kalman filtering:
 * 1. MDPS tracks RTT history to identify minimum-delay samples
 * 2. EMA provides primary filtering with outlier rejection
 * 3. Kalman filter tracks drift rate for prediction
 * 4. MDPS-weighted alpha gives more weight to low-RTT samples
 *
 * Retains original EMA behavior for backward compatibility.
 * MDPS and Kalman provide enhanced accuracy when RTT is available.
 *
 * JPL Rule 1: Fixed-size ring buffers (no dynamic allocation)
 * JPL Rule 2: Bounded loops (ring buffer sizes are constants)
 *
 * @param raw_offset_us Raw offset measurement (rx_time - server_time)
 * @param timestamp_us When this sample was taken
 * @param sequence Beacon sequence number
 * @param rtt_us Round-trip time (0 if not available, e.g., one-way beacon)
 * @return Filtered offset value (microseconds)
 */
static int64_t update_time_filter(int64_t raw_offset_us, uint64_t timestamp_us, uint8_t sequence, uint32_t rtt_us)
{
    time_filter_t *filter = &g_time_sync_state.filter;
    mdps_state_t *mdps = &g_time_sync_state.mdps;
    kalman_state_t *kalman = &g_time_sync_state.kalman;

    /* UTLP Phase 1: Add sample to MDPS if RTT available */
    if (rtt_us > 0) {
        mdps_add_sample(mdps, rtt_us, raw_offset_us);
        mdps_get_percentile_rtt(mdps);  /* Update min RTT threshold */
    }

    /* First sample: Initialize filter with raw value (no history to compare) */
    if (!filter->initialized) {
        filter->filtered_offset_us = raw_offset_us;
        filter->initialized = true;
        filter->sample_count = 1;
        filter->outlier_count = 0;
        filter->head = 0;
        filter->fast_attack_active = true;   /* Start in fast-attack mode */
        filter->valid_beacon_count = 1;      /* First valid beacon */

        /* Store in ring buffer */
        filter->samples[0].raw_offset_us = raw_offset_us;
        filter->samples[0].timestamp_us = timestamp_us;
        filter->samples[0].rtt_us = rtt_us;  /* UTLP Phase 1: Store RTT */
        filter->samples[0].sequence = sequence;
        filter->samples[0].outlier = false;

        /* UTLP Phase 1: Initialize Kalman filter */
        kalman_init(kalman, raw_offset_us, timestamp_us);

        ESP_LOGI(TAG, "Filter initialized: raw=%" PRId64 " µs, RTT=%lu µs (seq=%u, fast-attack active)",
                 raw_offset_us, (unsigned long)rtt_us, sequence);
        return raw_offset_us;
    }

    /* Outlier detection: Dynamic threshold based on filter mode
     * - Fast-attack mode: 50ms threshold (aggressive during mode changes)
     * - Steady-state mode: 100ms threshold (normal operation)
     */
    uint32_t outlier_threshold = filter->fast_attack_active ?
                                 TIME_FILTER_OUTLIER_THRESHOLD_FAST_US :
                                 TIME_FILTER_OUTLIER_THRESHOLD_US;

    int64_t deviation = raw_offset_us - filter->filtered_offset_us;
    int64_t abs_deviation = (deviation >= 0) ? deviation : -deviation;

    if (abs_deviation > (int64_t)outlier_threshold) {
        filter->outlier_count++;

        ESP_LOGW(TAG, "Outlier rejected: raw=%" PRId64 " µs, filtered=%" PRId64 " µs, deviation=%+" PRId64 " µs (seq=%u, RTT=%lu)",
                 raw_offset_us, filter->filtered_offset_us, deviation, sequence, (unsigned long)rtt_us);

        /* Store outlier in ring buffer but don't update filter */
        filter->samples[filter->head].raw_offset_us = raw_offset_us;
        filter->samples[filter->head].timestamp_us = timestamp_us;
        filter->samples[filter->head].rtt_us = rtt_us;  /* UTLP Phase 1: Store RTT */
        filter->samples[filter->head].sequence = sequence;
        filter->samples[filter->head].outlier = true;

        filter->head = (filter->head + 1) % TIME_FILTER_RING_SIZE;
        filter->sample_count++;

        /* Return previous filtered value (reject outlier) */
        return filter->filtered_offset_us;
    }

    /* UTLP Phase 1: MDPS quality weighting
     * Samples with RTT near minimum get full weight, higher RTT get reduced weight
     */
    bool is_min_delay = mdps_is_min_delay_sample(mdps, rtt_us);

    /* Dual-alpha fast-attack: Check if we should switch from fast to slow alpha */
    if (filter->fast_attack_active) {
        /* Condition 1: N=12 valid beacons received */
        if (filter->valid_beacon_count >= 12) {
            filter->fast_attack_active = false;
            ESP_LOGI(TAG, "Fast-attack filter ended after %u beacons, switching to slow alpha",
                     filter->valid_beacon_count);
        }
        /* Condition 2: Early convergence - offset changed by <50µs over last 4 beacons */
        else if (filter->valid_beacon_count >= 4) {
            /* Scan last 4 valid (non-outlier) samples in ring buffer */
            int64_t min_offset = INT64_MAX;
            int64_t max_offset = INT64_MIN;
            uint8_t samples_checked = 0;

            /* Walk backwards through ring buffer to find last 4 valid samples */
            for (uint8_t i = 0; i < TIME_FILTER_RING_SIZE && samples_checked < 4; i++) {
                /* Calculate index walking backwards from current head */
                uint8_t idx = (filter->head + TIME_FILTER_RING_SIZE - 1 - i) % TIME_FILTER_RING_SIZE;

                if (!filter->samples[idx].outlier) {
                    int64_t offset = filter->samples[idx].raw_offset_us;
                    if (offset < min_offset) min_offset = offset;
                    if (offset > max_offset) max_offset = offset;
                    samples_checked++;
                }
            }

            /* Check convergence: max deviation < 50µs */
            if (samples_checked == 4 && (max_offset - min_offset) < TIME_FILTER_CONVERGENCE_THRESHOLD_US) {
                filter->fast_attack_active = false;
                ESP_LOGI(TAG, "Fast-attack filter ended after %u beacons (early convergence: %lld µs stability), switching to slow alpha",
                         filter->valid_beacon_count, (max_offset - min_offset));
            }
        }
    }

    /* Valid sample: Apply EMA filter with selected alpha
     * UTLP Phase 1: Minimum-delay samples get higher alpha (more weight)
     * Formula: filtered = (alpha/100 * raw) + ((100-alpha)/100 * filtered)
     *
     * Dual-alpha fast-attack:
     * - Fast alpha (30%) until N=12 or early convergence detected
     * - Slow alpha (10%) for long-term stability after convergence
     */
    uint8_t base_alpha = filter->fast_attack_active ? TIME_FILTER_ALPHA_FAST_PCT : TIME_FILTER_ALPHA_PCT;
    uint8_t alpha = base_alpha;

    /* MDPS bonus: Give minimum-delay samples 50% more weight */
    if (is_min_delay && rtt_us > 0) {
        alpha = (base_alpha * 3) / 2;  /* 1.5x weight */
        if (alpha > 50) alpha = 50;    /* Cap at 50% */
    }

    int64_t alpha_term = (raw_offset_us * alpha) / 100;
    int64_t history_term = (filter->filtered_offset_us * (100 - alpha)) / 100;
    filter->filtered_offset_us = alpha_term + history_term;

    /* UTLP Phase 1: Update Kalman filter for drift tracking */
    kalman_update(kalman, raw_offset_us, rtt_us, timestamp_us);

    /* Store in ring buffer */
    filter->samples[filter->head].raw_offset_us = raw_offset_us;
    filter->samples[filter->head].timestamp_us = timestamp_us;
    filter->samples[filter->head].rtt_us = rtt_us;  /* UTLP Phase 1: Store RTT */
    filter->samples[filter->head].sequence = sequence;
    filter->samples[filter->head].outlier = false;

    filter->head = (filter->head + 1) % TIME_FILTER_RING_SIZE;
    filter->sample_count++;
    filter->valid_beacon_count++;  /* Increment valid beacon counter */

    /* Log filter statistics every 10 samples (avoid log spam) */
    if (filter->sample_count % 10 == 0) {
        uint32_t outlier_pct = (filter->outlier_count * 100) / filter->sample_count;
        ESP_LOGI(TAG, "Filter stats: samples=%lu, outliers=%lu (%lu%%), EMA=%" PRId64 " µs, Kalman=%.0f µs, drift=%.2f µs/s",
                 filter->sample_count, filter->outlier_count, outlier_pct,
                 filter->filtered_offset_us, kalman->offset_us, kalman->drift_ppm);

        /* Log MDPS stats if active */
        if (mdps->count >= MDPS_MIN_SAMPLES) {
            ESP_LOGI(TAG, "MDPS: min_RTT=%lu µs, samples=%u, is_min_delay=%s",
                     (unsigned long)mdps->min_rtt_us, mdps->count, is_min_delay ? "yes" : "no");
        }
    }

    return filter->filtered_offset_us;
}

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
 * @brief Finalize beacon timestamp just before BLE transmission
 *
 * Bug #76 (PTP Hardening): Records T1 as late as possible to minimize
 * timestamp-to-transmission asymmetry. The original T1 was recorded in
 * time_sync_generate_beacon() ~1-50ms before actual RF transmission.
 *
 * Call this right before ble_hs_mbuf_from_flat() to minimize the gap.
 *
 * @param beacon Pointer to beacon struct to update
 */
void time_sync_finalize_beacon_timestamp(time_sync_beacon_t *beacon)
{
    if (beacon == NULL) {
        return;
    }

    /* Update T1 to current time (as close to transmission as possible) */
    beacon->server_time_us = esp_timer_get_time();

    /* Recalculate CRC with updated timestamp */
    beacon->checksum = calculate_crc16((const uint8_t *)beacon,
                                       sizeof(time_sync_beacon_t) - sizeof(uint16_t));
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

/* REMOVED: update_quality_metrics() - AD045 simplification
 * This function was never called. Quality metrics are now updated
 * directly where needed without drift rate dependency. */

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
#if TDM_TECH_SPIKE_ENABLED
    /* TDM Tech Spike: Fixed 1s interval for jitter analysis.
     * Results: ~74ms consistent bias, outliers inflate stddev.
     * See time_sync.h for full analysis and next steps. */
    g_time_sync_state.sync_interval_ms = TDM_INTERVAL_MS;
    return ESP_OK;
#endif

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
    /* Bug #62 fix: Removed forced_beacon_count mechanism
     *
     * Previous approach tried to send 5 beacons at 200ms intervals after
     * mode change. This was flawed because:
     * 1. EMA convergence depends on time between samples, not rapid fire
     * 2. The continuous beacon check loop didn't update last_sync_ms,
     *    causing beacon spam (100+ beacons)
     *
     * New approach: Send ONE beacon on mode change (via TRIGGER_BEACONS msg),
     * then rely on normal adaptive interval for subsequent syncs.
     */
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

    ESP_LOGI(TAG, "Motor epoch set: %" PRIu64 " us, cycle: %lu ms", epoch_us, cycle_ms);

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
 * PWA TIME INJECTION IMPLEMENTATION (AD047 - UTLP Integration)
 ******************************************************************************/

/* UTLP stratum state - defaults to peer-only */
static uint8_t g_utlp_stratum = UTLP_STRATUM_PEER_ONLY;

/**
 * @brief Inject external time reference from PWA
 *
 * ALWAYS adopts the injected time (no stratum comparison).
 * Rationale: We need bilateral sync, not wall-clock accuracy.
 */
esp_err_t time_sync_inject_pwa_time(const pwa_time_inject_t *inject)
{
    /* JPL Rule 7: Validate pointer */
    if (inject == NULL) {
        ESP_LOGE(TAG, "NULL pointer passed to time_sync_inject_pwa_time");
        return ESP_ERR_INVALID_ARG;
    }

    if (!g_time_sync_state.initialized) {
        ESP_LOGE(TAG, "Not initialized");
        return ESP_ERR_INVALID_STATE;
    }

    /* Update stratum from injected source */
    g_utlp_stratum = inject->stratum;

    ESP_LOGI(TAG, "PWA time adopted: stratum=%d, quality=%d, time=%llu us, uncertainty=±%ld us",
             inject->stratum, inject->quality,
             (unsigned long long)inject->utc_time_us,
             (long)inject->uncertainty_us);

    /* TODO: Actually apply the time offset when full UTLP integration is done.
     * For now, just update the stratum. The time value would be used to:
     * 1. Calculate offset from local time
     * 2. Apply to synchronized time calculations
     * 3. Propagate to peer if we're SERVER
     */

    /* Propagate to peer if we're SERVER */
    if (g_time_sync_state.role == TIME_SYNC_ROLE_SERVER) {
        ESP_LOGI(TAG, "SERVER: Will propagate new stratum to CLIENT in next beacon");
        /* The stratum will be included in the next beacon generation */
    }

    return ESP_OK;
}

/**
 * @brief Get current UTLP stratum level
 */
uint8_t time_sync_get_stratum(void)
{
    return g_utlp_stratum;
}

/**
 * @brief Get current UTLP quality value (battery percentage)
 */
uint8_t time_sync_get_utlp_quality(void)
{
    /* Import battery percentage from battery_monitor module */
    extern uint8_t battery_get_percentage(void);
    return battery_get_percentage();
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

    ESP_LOGI(TAG, "Handshake initiated: T1=%" PRIu64 " μs", t1);

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

    ESP_LOGI(TAG, "Handshake request processed: T1=%" PRIu64 ", T2=%" PRIu64 ", T3=%" PRIu64 " μs",
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
        ESP_LOGW(TAG, "T1 mismatch: sent=%" PRIu64 ", received=%" PRIu64 " (possible stale response)",
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
     * Raw NTP convention: offset > 0 means SERVER is ahead of CLIENT
     * Our convention: offset > 0 means CLIENT is ahead of SERVER
     *
     * We NEGATE to match our beacon convention (client_rx - server_tx)
     * so time_sync_get_time can use consistent subtraction.
     */
    int64_t d1 = (int64_t)t2_us - (int64_t)t1_us;  /* T2 - T1 */
    int64_t d2 = (int64_t)t3_us - (int64_t)t4_us;  /* T3 - T4 */
    int64_t offset = -((d1 + d2) / 2);  /* NEGATE to match CLIENT-SERVER convention */

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

    ESP_LOGI(TAG, "Handshake complete: offset=%" PRId64 " μs, RTT=%" PRId64 " μs (T1=%" PRIu64 ", T2=%" PRIu64 ", T3=%" PRIu64 ", T4=%" PRIu64 ")",
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

    ESP_LOGI(TAG, "Motor epoch set from handshake: %" PRIu64 " μs, cycle: %lu ms", epoch_us, cycle_ms);

    return ESP_OK;
}

/**
 * @brief Reset EMA filter to fast-attack mode (for mode changes)
 *
 * Resets the filter to fast-attack mode for rapid convergence after mode changes.
 * This prevents jerky motor corrections during the first 10-40 seconds after
 * frequency/duty/cycle changes.
 *
 * Changes:
 * - Sets fast_attack_active = true (enables 30% alpha)
 * - Resets valid_beacon_count = 0 (forces 12 samples or early convergence)
 * - Resets sample_count = 0 (restart filter statistics)
 * - Uses 50ms outlier threshold (vs 100ms in steady-state)
 * - Preserves filtered_offset_us (doesn't reset to zero)
 */
esp_err_t time_sync_reset_filter_fast_attack(void)
{
    if (!g_time_sync_state.initialized) {
        ESP_LOGE(TAG, "Not initialized");
        return ESP_ERR_INVALID_STATE;
    }

    time_filter_t *filter = &g_time_sync_state.filter;

    /* Reset filter to fast-attack mode */
    filter->fast_attack_active = true;
    filter->valid_beacon_count = 0;
    filter->sample_count = 0;
    filter->outlier_count = 0;

    /* Keep filtered_offset_us unchanged - we don't want to reset to zero,
     * just want to adapt quickly to the new motor epoch timing */

    ESP_LOGI(TAG, "Mode change detected - resetting to fast-attack filter (alpha=30%%, threshold=50ms, preserving offset=%" PRId64 " μs)",
             filter->filtered_offset_us);

    return ESP_OK;
}

/* REMOVED: time_sync_trigger_forced_beacons() - UTLP Refactor
 *
 * Mode-change beacons eliminated. Epoch delivery now handled by
 * SYNC_MSG_MOTOR_STARTED message. Time layer handles beacons on
 * fixed schedule, not triggered by application events.
 *
 * See: UTLP architecture - time handles time, application handles application.
 */

/* REMOVED: time_sync_get_drift_rate() - AD045 simplification
 * Never called externally. Drift rate calculation was only used for
 * time_sync_get_predicted_offset() which is also removed. */

/* REMOVED: time_sync_get_predicted_offset() - AD045 simplification
 * Emergency vehicle pattern: Both devices know the time (EMA filter ±30μs),
 * no need for drift rate extrapolation between beacons. */

/**
 * @brief Check if antiphase lock is achieved (stable synchronization)
 *
 * Determines if time synchronization has converged to a stable state suitable
 * for starting motors. This prevents startup jitter from filter convergence.
 *
 * Lock criteria:
 * - Handshake complete (precise NTP-style bootstrap)
 * - Minimum 3 beacons received (filter has data)
 * - Filter in steady-state mode (sample_count >= 10, not fast-attack)
 * - Recent beacon within 2× adaptive interval (not stale)
 *
 * Expected lock time: 2-3 seconds from connection
 *
 * @return true if locked and stable, false otherwise
 *
 * @note This function is called by CLIENT motor task before starting motors
 *       and periodically during operation for lock maintenance
 */
bool time_sync_is_antiphase_locked(void)
{
    /* Not initialized - definitely not locked */
    if (!g_time_sync_state.initialized) {
        return false;
    }

    /* Only CLIENT devices need phase lock (SERVER is authoritative) */
    if (g_time_sync_state.role != TIME_SYNC_ROLE_CLIENT) {
        /* SERVER always reports "locked" (no phase lock needed) */
        return true;
    }

    /* 1. Handshake must be complete (precise NTP-style offset calculated) */
    if (!g_time_sync_state.handshake_complete) {
        return false;
    }

    /* 2. Minimum beacon history (filter needs data to be reliable) */
    if (g_time_sync_state.filter.sample_count < 3) {
        return false;
    }

    /* 3. Phase 6t: Early lock detection during fast-attack mode
     * Allow lock if offset variance is low (< ±2ms) even during fast-attack.
     * This enables ~1s lock time vs 2-3s waiting for steady-state.
     *
     * Check variance of last 5 valid samples in ring buffer.
     */
    if (g_time_sync_state.filter.fast_attack_active) {
        /* Need at least 5 valid beacons for variance calculation */
        if (g_time_sync_state.filter.valid_beacon_count < 5) {
            return false;  /* Not enough samples yet */
        }

        /* Scan last 5 valid (non-outlier) samples to calculate variance */
        int64_t min_offset = INT64_MAX;
        int64_t max_offset = INT64_MIN;
        uint8_t samples_checked = 0;

        /* Walk backwards through ring buffer to find last 5 valid samples */
        for (uint8_t i = 0; i < TIME_FILTER_RING_SIZE && samples_checked < 5; i++) {
            uint8_t idx = (g_time_sync_state.filter.head + TIME_FILTER_RING_SIZE - 1 - i) % TIME_FILTER_RING_SIZE;

            if (!g_time_sync_state.filter.samples[idx].outlier) {
                int64_t offset = g_time_sync_state.filter.samples[idx].raw_offset_us;
                if (offset < min_offset) min_offset = offset;
                if (offset > max_offset) max_offset = offset;
                samples_checked++;
            }
        }

        /* Check if variance is low enough for stable lock */
        const int64_t FAST_LOCK_VARIANCE_THRESHOLD_US = 2000;  /* ±2ms */
        if (samples_checked == 5 && (max_offset - min_offset) < FAST_LOCK_VARIANCE_THRESHOLD_US) {
            /* Variance is low - safe to lock even during fast-attack */
            static bool fast_lock_logged = false;
            if (!fast_lock_logged) {
                ESP_LOGI(TAG, "Phase 6t: Fast lock achieved (variance=%lld µs < 2ms threshold, %u beacons)",
                         (max_offset - min_offset), g_time_sync_state.filter.valid_beacon_count);
                fast_lock_logged = true;
            }
            return true;
        }

        /* Variance too high - need to wait for more samples */
        return false;
    }

    /* 4. Beacon must not be stale (recent update within 2× max interval)
     *
     * Bug #63 fix: CLIENT's sync_interval_ms stays at 1s (TIME_SYNC_INTERVAL_MIN_MS)
     * but SERVER backs off to 60s (TIME_SYNC_INTERVAL_MAX_MS). Using CLIENT's
     * interval caused false "lock LOST" warnings after 2s when beacons arrive
     * every 60s.
     *
     * Fix: Use 2× max interval (120s) as the staleness threshold. This accounts
     * for SERVER's adaptive backoff while still detecting true connection loss.
     */
    uint32_t now_ms = (uint32_t)(esp_timer_get_time() / 1000);
    uint32_t elapsed_ms = now_ms - g_time_sync_state.last_sync_ms;
    uint32_t staleness_threshold_ms = TIME_SYNC_INTERVAL_MAX_MS * 2;  /* 120s */

    if (elapsed_ms > staleness_threshold_ms) {
        return false;  /* Beacon too old - likely connection loss */
    }

    /* All criteria met - phase lock achieved */
    return true;
}

/**
 * @brief Get last beacon timestamps for paired offset calculation (AD043)
 *
 * CLIENT uses this to populate SYNC_FB with T1/T2 timestamps.
 * SERVER can then calculate bias-corrected offset using NTP formula.
 */
esp_err_t time_sync_get_last_beacon_timestamps(uint64_t *server_time_us, uint64_t *local_rx_time_us)
{
    /* JPL Rule 7: Validate pointers */
    if (server_time_us == NULL || local_rx_time_us == NULL) {
        ESP_LOGE(TAG, "NULL pointer in time_sync_get_last_beacon_timestamps");
        return ESP_ERR_INVALID_ARG;
    }

    if (!g_time_sync_state.initialized) {
        return ESP_ERR_INVALID_STATE;
    }

    /* Check if we have received at least one beacon */
    if (g_time_sync_state.last_beacon_time_us == 0 || g_time_sync_state.server_ref_time_us == 0) {
        return ESP_ERR_INVALID_STATE;
    }

    *server_time_us = g_time_sync_state.server_ref_time_us;     /* T1 */
    *local_rx_time_us = g_time_sync_state.last_beacon_time_us;  /* T2 */

    return ESP_OK;
}

/**
 * @brief Update offset using paired timestamps from SYNC_FB (AD043)
 *
 * SERVER calls this when receiving SYNC_FB with paired timestamps.
 * Calculates bias-corrected offset using NTP formula and feeds it into EMA filter.
 *
 * NTP formula: offset = ((T2-T1) + (T3-T4)) / 2
 *   - (T2-T1) includes: clock_offset + one_way_delay_to_client
 *   - (T3-T4) includes: clock_offset - one_way_delay_to_server
 *   - Sum cancels the delays: 2 * clock_offset
 *   - Divide by 2: clock_offset (bias-corrected)
 *
 * This corrects the systematic one-way delay bias in beacon-only synchronization.
 */
esp_err_t time_sync_update_from_paired_timestamps(
    uint64_t t1_server_beacon_time_us,
    uint64_t t2_client_rx_time_us,
    uint64_t t3_client_tx_time_us,
    uint64_t t4_server_rx_time_us)
{
    if (!g_time_sync_state.initialized) {
        return ESP_ERR_INVALID_STATE;
    }

    /* Only SERVER processes paired timestamps (CLIENT sends them) */
    if (g_time_sync_state.role != TIME_SYNC_ROLE_SERVER) {
        ESP_LOGW(TAG, "Paired timestamps only processed by SERVER");
        return ESP_ERR_INVALID_STATE;
    }

    /* Sanity check: T4 should be after T1 (basic causality) */
    if (t4_server_rx_time_us < t1_server_beacon_time_us) {
        ESP_LOGW(TAG, "Invalid timestamps: T4 < T1 (T1=%" PRIu64 ", T4=%" PRIu64 ")",
                 t1_server_beacon_time_us, t4_server_rx_time_us);
        return ESP_ERR_INVALID_ARG;
    }

    /* NTP offset formula: offset = ((T2-T1) + (T3-T4)) / 2
     *
     * Sign convention (same as AD039/AD043):
     * - Positive offset = CLIENT clock ahead of SERVER
     * - Negative offset = CLIENT clock behind SERVER
     *
     * Formula derivation:
     *   (T2-T1) = client_local - server_local = offset + delay_to_client
     *   (T3-T4) = client_local - server_local = offset - delay_to_server
     *   Sum = 2*offset + (delay_to_client - delay_to_server)
     *   If delays are symmetric: Sum ≈ 2*offset
     */
    int64_t d1 = (int64_t)t2_client_rx_time_us - (int64_t)t1_server_beacon_time_us;
    int64_t d2 = (int64_t)t3_client_tx_time_us - (int64_t)t4_server_rx_time_us;
    int64_t paired_offset = (d1 + d2) / 2;

    /* Calculate RTT for diagnostics: RTT = (T4-T1) - (T3-T2) */
    int64_t rtt = ((int64_t)t4_server_rx_time_us - (int64_t)t1_server_beacon_time_us) -
                  ((int64_t)t3_client_tx_time_us - (int64_t)t2_client_rx_time_us);

    /* Log the paired offset calculation */
    ESP_LOGI(TAG, "[PAIRED] offset=%" PRId64 " µs, RTT=%" PRId64 " µs (T1=%" PRIu64 ", T2=%" PRIu64 ", T3=%" PRIu64 ", T4=%" PRIu64 ")",
             paired_offset, rtt, t1_server_beacon_time_us, t2_client_rx_time_us,
             t3_client_tx_time_us, t4_server_rx_time_us);

    /* Feed paired offset into EMA filter for smoothing
     * This overwrites the one-way offset with the bias-corrected value.
     * Using the same filter ensures consistency and outlier rejection.
     * UTLP Phase 1: Pass RTT for MDPS minimum delay selection.
     */
    uint32_t rtt_u32 = (rtt > 0 && rtt < UINT32_MAX) ? (uint32_t)rtt : 0;
    int64_t filtered_offset = update_time_filter(paired_offset, t4_server_rx_time_us,
                                                  g_time_sync_state.sync_sequence, rtt_u32);
    g_time_sync_state.clock_offset_us = filtered_offset;

    /* Update quality metrics with RTT */
    if (rtt > 0 && rtt < 2000000) {  /* Sanity: RTT < 2 seconds */
        g_time_sync_state.quality.last_rtt_us = (uint32_t)rtt;
    }

    return ESP_OK;
}
