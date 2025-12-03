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
static void update_quality_metrics(int32_t offset_change_us, uint32_t rtt_us, int32_t drift_rate_us_per_s);
static esp_err_t adjust_sync_interval(void);
static int64_t update_time_filter(int64_t raw_offset_us, uint64_t timestamp_us, uint8_t sequence);

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

    /* PRESERVE drift rate data (CLIENT can extrapolate offset during disconnect) */
    /* drift_rate_us_per_s, drift_rate_valid - NOT cleared */
    /* last_beacon_offset_us, last_beacon_valid, last_beacon_time_us - NOT cleared */

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
            ESP_LOGW(TAG, "time_sync_get_time: Underflow prevented (local=%" PRIu64 " μs, offset=%" PRId64 " μs, would be %" PRId64 " μs)",
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

    /* Phase 6r Step 2: Apply EMA filter with outlier detection (AD043) */
    int64_t filtered_offset = update_time_filter(raw_offset, receive_time_us, beacon->sequence);
    g_time_sync_state.clock_offset_us = filtered_offset;

    g_time_sync_state.server_ref_time_us = beacon->server_time_us;
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
            ESP_LOGI(TAG, "Quality metrics initialized from beacon (raw offset, filter pending)");
        }
        g_time_sync_state.state = SYNC_STATE_SYNCED;
        ESP_LOGI(TAG, "Initial sync beacon processed (one-way timestamp)");
    }

    ESP_LOGD(TAG, "Beacon processed (seq: %u, raw_offset: %" PRId64 " μs, motor_epoch: %" PRIu64 ", cycle: %lu)",
             beacon->sequence, raw_offset, beacon->motor_epoch_us, beacon->motor_cycle_ms);

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

    /* Populate beacon fields (Phase 6r: Simplified for filtered time sync)
     * AD043: One-way timestamp approach (no RTT measurement in beacon)
     * CLIENT will capture receive time immediately and apply EMA filter
     */
    beacon->server_time_us = esp_timer_get_time();  /* Absolute boot time */
    beacon->sequence = ++g_time_sync_state.sync_sequence;  /* Increment and use */

    /* Phase 3: Include motor epoch for bilateral coordination */
    beacon->motor_epoch_us = g_time_sync_state.motor_epoch_us;
    beacon->motor_cycle_ms = g_time_sync_state.motor_cycle_ms;

    /* Calculate and append checksum */
    beacon->checksum = calculate_crc16((const uint8_t *)beacon, sizeof(time_sync_beacon_t) - sizeof(uint16_t));

    ESP_LOGD(TAG, "Beacon generated (seq: %u, server_time: %" PRIu64 " μs, motor_epoch: %" PRIu64 " μs, cycle: %lu ms)",
             beacon->sequence, beacon->server_time_us,
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
 * @brief Update EMA filter with new time offset sample (Phase 6r Step 2 - AD043)
 *
 * Implements exponential moving average filter with outlier rejection:
 * 1. Check if sample deviates >200ms from filtered value (outlier detection)
 * 2. If outlier, log and return previous filtered value (reject)
 * 3. If valid, apply EMA: filtered = (alpha * raw) + ((1-alpha) * filtered)
 * 4. Store sample in ring buffer for debugging
 * 5. Log filter statistics every 10 samples
 *
 * JPL Rule 1: Fixed-size ring buffer (no dynamic allocation)
 * JPL Rule 2: Bounded loops (ring buffer size = 8)
 *
 * @param raw_offset_us Raw offset measurement (rx_time - server_time)
 * @param timestamp_us When this sample was taken
 * @param sequence Beacon sequence number
 * @return Filtered offset value (microseconds)
 */
static int64_t update_time_filter(int64_t raw_offset_us, uint64_t timestamp_us, uint8_t sequence)
{
    time_filter_t *filter = &g_time_sync_state.filter;

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
        filter->samples[0].sequence = sequence;
        filter->samples[0].outlier = false;

        ESP_LOGI(TAG, "Filter initialized: raw=%" PRId64 " μs (seq=%u, fast-attack active)", raw_offset_us, sequence);
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

        ESP_LOGW(TAG, "Outlier rejected: raw=%" PRId64 " μs, filtered=%" PRId64 " μs, deviation=%+" PRId64 " μs (seq=%u)",
                 raw_offset_us, filter->filtered_offset_us, deviation, sequence);

        /* Store outlier in ring buffer but don't update filter */
        filter->samples[filter->head].raw_offset_us = raw_offset_us;
        filter->samples[filter->head].timestamp_us = timestamp_us;
        filter->samples[filter->head].sequence = sequence;
        filter->samples[filter->head].outlier = true;

        filter->head = (filter->head + 1) % TIME_FILTER_RING_SIZE;
        filter->sample_count++;

        /* Return previous filtered value (reject outlier) */
        return filter->filtered_offset_us;
    }

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
     * Formula: filtered = (alpha/100 * raw) + ((100-alpha)/100 * filtered)
     *
     * Dual-alpha fast-attack:
     * - Fast alpha (30%) until N=12 or early convergence detected
     * - Slow alpha (10%) for long-term stability after convergence
     */
    uint8_t alpha = filter->fast_attack_active ? TIME_FILTER_ALPHA_FAST_PCT : TIME_FILTER_ALPHA_PCT;
    int64_t alpha_term = (raw_offset_us * alpha) / 100;
    int64_t history_term = (filter->filtered_offset_us * (100 - alpha)) / 100;
    filter->filtered_offset_us = alpha_term + history_term;

    /* Store in ring buffer */
    filter->samples[filter->head].raw_offset_us = raw_offset_us;
    filter->samples[filter->head].timestamp_us = timestamp_us;
    filter->samples[filter->head].sequence = sequence;
    filter->samples[filter->head].outlier = false;

    filter->head = (filter->head + 1) % TIME_FILTER_RING_SIZE;
    filter->sample_count++;
    filter->valid_beacon_count++;  /* Increment valid beacon counter */

    /* Log filter statistics every 10 samples (avoid log spam) */
    if (filter->sample_count % 10 == 0) {
        uint32_t outlier_pct = (filter->outlier_count * 100) / filter->sample_count;
        ESP_LOGI(TAG, "Filter stats: samples=%lu, outliers=%lu (%lu%%), filtered=%" PRId64 " μs, last_raw=%" PRId64 " μs",
                 filter->sample_count, filter->outlier_count, outlier_pct,
                 filter->filtered_offset_us, raw_offset_us);
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

    /* Check for forced beacon mode (mode change fast convergence) */
    if (g_time_sync_state.forced_beacon_count > 0) {
        if (now_ms >= g_time_sync_state.forced_beacon_next_ms) {
            /* Time for next forced beacon */
            g_time_sync_state.forced_beacon_count--;

            if (g_time_sync_state.forced_beacon_count > 0) {
                /* Phase 6t: Schedule next forced beacon in 200ms (5 total for fast lock) */
                g_time_sync_state.forced_beacon_next_ms = now_ms + 200;
                ESP_LOGI(TAG, "Forced beacon %d/5 sent, next in 200ms",
                         5 - g_time_sync_state.forced_beacon_count);
            } else {
                /* Last forced beacon - return to adaptive interval */
                ESP_LOGI(TAG, "Forced beacon 5/5 sent, returning to adaptive interval (%lu ms)",
                         (unsigned long)g_time_sync_state.sync_interval_ms);
            }

            return true;
        }
        /* Not time for forced beacon yet */
        return false;
    }

    /* Normal adaptive interval check */
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

/**
 * @brief Trigger forced beacons for fast convergence (SERVER only)
 *
 * Forces 3 immediate beacons at 500ms intervals to help CLIENT filter
 * adapt quickly after mode changes. After 3 beacons, returns to adaptive interval.
 *
 * This is only valid for SERVER role (beacon sender).
 *
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_STATE if not initialized or not SERVER role
 */
esp_err_t time_sync_trigger_forced_beacons(void)
{
    if (!g_time_sync_state.initialized) {
        ESP_LOGE(TAG, "Not initialized");
        return ESP_ERR_INVALID_STATE;
    }

    if (g_time_sync_state.role != TIME_SYNC_ROLE_SERVER) {
        ESP_LOGW(TAG, "Forced beacons only valid for SERVER role");
        return ESP_ERR_INVALID_STATE;
    }

    /* Phase 6t: Set up fast lock beacon burst
     * - 5 beacons total (vs 3 in Phase 6r)
     * - First beacon sent immediately (next_ms = 0)
     * - Subsequent beacons at 200ms intervals (vs 500ms in Phase 6r)
     * - Total lock time: ~1 second (vs 2-3 seconds in Phase 6r)
     *
     * Research basis: IEEE/Bluetooth SIG papers show 50-100ms lock achievable
     * for biomedical BLE sensors with rapid beacon bursts handling 16-50ppm
     * crystal drift (ESP32-C6 is ~16ppm).
     */
    g_time_sync_state.forced_beacon_count = 5;
    g_time_sync_state.forced_beacon_next_ms = 0;  // Send first beacon immediately

    ESP_LOGI(TAG, "Forcing 5 beacons at 200ms intervals for fast lock (Phase 6t)");

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
    if (!g_time_sync_state.drift_rate_valid || g_time_sync_state.last_beacon_time_us == 0) {
        /* Phase 6r: Log first fallback only (avoid spam) */
        static bool fallback_logged = false;
        if (!fallback_logged) {
            ESP_LOGI(TAG, "Prediction: Using RAW offset (drift_rate_valid=%d, no beacon updates yet)",
                     g_time_sync_state.drift_rate_valid ? 1 : 0);
            fallback_logged = true;
        }
        *predicted_offset_us = g_time_sync_state.clock_offset_us;
        return ESP_ERR_NOT_FOUND;
    }

    /* Calculate time since last beacon update */
    uint64_t now_us = esp_timer_get_time();
    uint32_t elapsed_ms = (uint32_t)((now_us - g_time_sync_state.last_beacon_time_us) / 1000);

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
        ESP_LOGI(TAG, "Prediction: Using DRIFT RATE (%d μs/s, elapsed=%lu ms, correction=%" PRId64 " μs)",
                 g_time_sync_state.drift_rate_us_per_s, elapsed_ms, drift_correction_us);
        prediction_logged = true;
    }

    return ESP_OK;
}

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

    /* 4. Beacon must not be stale (recent update within 2× adaptive interval)
     * Stale beacons indicate connection issues or SERVER stopped sending.
     * Use 2× interval for safety margin during adaptive backoff.
     */
    uint32_t now_ms = (uint32_t)(esp_timer_get_time() / 1000);
    uint32_t elapsed_ms = now_ms - g_time_sync_state.last_sync_ms;
    uint32_t staleness_threshold_ms = g_time_sync_state.sync_interval_ms * 2;

    if (elapsed_ms > staleness_threshold_ms) {
        return false;  /* Beacon too old */
    }

    /* All criteria met - phase lock achieved */
    return true;
}
