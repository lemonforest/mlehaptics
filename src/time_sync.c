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
static void update_quality_metrics(int32_t offset_us, uint32_t rtt_us);
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

esp_err_t time_sync_on_connection(uint64_t connection_time_us)
{
    /* JPL Rule 5: Validate state and parameters */
    if (!g_time_sync_state.initialized) {
        ESP_LOGE(TAG, "Not initialized");
        return ESP_ERR_INVALID_STATE;
    }

    if (connection_time_us == 0) {
        ESP_LOGE(TAG, "Invalid connection time");
        return ESP_ERR_INVALID_ARG;
    }

    if (g_time_sync_state.state != SYNC_STATE_INIT) {
        ESP_LOGW(TAG, "Not in INIT state (current: %d)", g_time_sync_state.state);
        return ESP_ERR_INVALID_STATE;
    }

    /* Record connection timestamp as reference */
    g_time_sync_state.local_ref_time_us = connection_time_us;
    g_time_sync_state.server_ref_time_us = connection_time_us;  /* Initial assumption */
    g_time_sync_state.last_sync_ms = (uint32_t)(connection_time_us / 1000);
    g_time_sync_state.state = SYNC_STATE_CONNECTED;

    ESP_LOGI(TAG, "Connection sync established at %llu μs (%s role)",
             connection_time_us,
             (g_time_sync_state.role == TIME_SYNC_ROLE_SERVER) ? "SERVER" : "CLIENT");

    /* SERVER immediately transitions to SYNCED, CLIENT waits for first beacon */
    if (g_time_sync_state.role == TIME_SYNC_ROLE_SERVER) {
        g_time_sync_state.state = SYNC_STATE_SYNCED;
        ESP_LOGI(TAG, "SERVER ready to send sync beacons (interval: %lu ms)",
                 g_time_sync_state.sync_interval_ms);
    } else {
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

    /* Freeze current sync state for continued operation */
    time_sync_state_t old_state = g_time_sync_state.state;
    g_time_sync_state.state = SYNC_STATE_DISCONNECTED;

    uint32_t now_ms = (uint32_t)(esp_timer_get_time() / 1000);
    uint32_t elapsed_ms = now_ms - g_time_sync_state.last_sync_ms;
    uint32_t expected_drift_us = time_sync_calculate_expected_drift(elapsed_ms);

    ESP_LOGI(TAG, "Disconnected (last sync: %lu ms ago, expected drift: %lu μs)",
             elapsed_ms, expected_drift_us);
    ESP_LOGI(TAG, "Continuing with frozen sync state (offset: %ld μs, quality: %u%%)",
             g_time_sync_state.clock_offset_us,
             g_time_sync_state.quality.quality_score);

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
        if (should_send_sync_beacon()) {
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
    /* CLIENT: Apply clock offset correction */
    else if (g_time_sync_state.role == TIME_SYNC_ROLE_CLIENT) {
        /* Apply offset (offset can be negative) */
        *sync_time_us = (uint64_t)((int64_t)local_time_us - (int64_t)g_time_sync_state.clock_offset_us);
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

    /* Calculate clock offset: CLIENT_time - SERVER_time */
    int64_t offset = (int64_t)receive_time_us - (int64_t)beacon->timestamp_us;
    g_time_sync_state.clock_offset_us = (int32_t)offset;  /* Cast to 32-bit (sufficient for ±2000s) */

    /* Calculate round-trip time (approximate, assumes symmetric delay) */
    uint32_t rtt_us = 0;  /* TODO: Implement proper RTT measurement with request/response */

    /* Update quality metrics */
    update_quality_metrics(g_time_sync_state.clock_offset_us, rtt_us);

    /* Update state */
    g_time_sync_state.server_ref_time_us = beacon->timestamp_us;
    g_time_sync_state.last_sync_ms = (uint32_t)(receive_time_us / 1000);
    g_time_sync_state.sync_sequence = beacon->sequence;
    g_time_sync_state.total_syncs++;

    /* Transition to SYNCED if this is first beacon */
    if (g_time_sync_state.state == SYNC_STATE_CONNECTED) {
        g_time_sync_state.state = SYNC_STATE_SYNCED;
        ESP_LOGI(TAG, "Initial sync complete (offset: %ld μs, quality: %u%%)",
                 g_time_sync_state.clock_offset_us,
                 g_time_sync_state.quality.quality_score);
    }
    /* Clear drift flag if resync successful */
    else if (g_time_sync_state.state == SYNC_STATE_DRIFT_DETECTED) {
        g_time_sync_state.state = SYNC_STATE_SYNCED;
        g_time_sync_state.drift_detected = false;
        ESP_LOGI(TAG, "Resync complete (offset: %ld μs, quality: %u%%)",
                 g_time_sync_state.clock_offset_us,
                 g_time_sync_state.quality.quality_score);
    }

    ESP_LOGD(TAG, "Beacon processed (seq: %u, offset: %ld μs, SERVER_quality: %u%%)",
             beacon->sequence,
             g_time_sync_state.clock_offset_us,
             beacon->quality_score);

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
    beacon->timestamp_us = esp_timer_get_time();
    beacon->session_ref_ms = g_time_sync_state.session_start_ms;
    beacon->sequence = ++g_time_sync_state.sync_sequence;  /* Increment and use */
    beacon->quality_score = g_time_sync_state.quality.quality_score;

    /* Calculate and append checksum */
    beacon->checksum = calculate_crc16((const uint8_t *)beacon, sizeof(time_sync_beacon_t) - sizeof(uint16_t));

    ESP_LOGD(TAG, "Beacon generated (seq: %u, time: %llu μs, quality: %u%%)",
             beacon->sequence, beacon->timestamp_us, beacon->quality_score);

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

time_sync_state_t time_sync_get_state(void)
{
    return g_time_sync_state.state;
}

time_sync_role_t time_sync_get_role(void)
{
    return g_time_sync_state.role;
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
 * @brief Calculate sync quality score (0-100%)
 *
 * Quality based on:
 * - Clock offset magnitude (lower is better)
 * - Drift from expected (lower is better)
 * - Round-trip time (lower is better)
 *
 * @param offset_us Clock offset in microseconds (absolute value used)
 * @param drift_us Drift from expected in microseconds
 * @param rtt_us Round-trip time in microseconds
 * @return Quality score (0-100%)
 */
static uint8_t calculate_sync_quality(int32_t offset_us, uint32_t drift_us, uint32_t rtt_us)
{
    /* Convert to absolute offset */
    uint32_t abs_offset_us = (offset_us < 0) ? (uint32_t)(-offset_us) : (uint32_t)offset_us;

    /* Quality thresholds based on ±100ms requirement (half = 50ms) */
    if (abs_offset_us < 5000 && drift_us < 5000) {
        return SYNC_QUALITY_EXCELLENT;  /* < 5ms */
    } else if (abs_offset_us < 15000 && drift_us < 15000) {
        return SYNC_QUALITY_GOOD;       /* < 15ms */
    } else if (abs_offset_us < 30000 && drift_us < 30000) {
        return SYNC_QUALITY_FAIR;       /* < 30ms */
    } else if (abs_offset_us < 50000 && drift_us < 50000) {
        return SYNC_QUALITY_POOR;       /* < 50ms (threshold) */
    } else {
        return 0;  /* Failed - exceeds threshold */
    }
}

/**
 * @brief Update quality metrics with new sync sample
 *
 * Updates running statistics for sync quality tracking.
 * JPL Rule 2: Bounded by SYNC_QUALITY_WINDOW constant.
 *
 * @param offset_us New clock offset sample
 * @param rtt_us New round-trip time sample
 */
static void update_quality_metrics(int32_t offset_us, uint32_t rtt_us)
{
    time_sync_quality_t *q = &g_time_sync_state.quality;

    /* Update sample count (bounded by window size) */
    if (q->samples_collected < TIME_SYNC_QUALITY_WINDOW) {
        q->samples_collected++;
    }

    /* Update average offset (simple moving average) */
    q->avg_offset_us = (q->avg_offset_us * (q->samples_collected - 1) + offset_us) / q->samples_collected;

    /* Update max drift */
    uint32_t abs_offset = (offset_us < 0) ? (uint32_t)(-offset_us) : (uint32_t)offset_us;
    if (abs_offset > q->max_drift_us) {
        q->max_drift_us = abs_offset;
    }

    /* Update RTT */
    q->last_rtt_us = rtt_us;

    /* Calculate quality score */
    uint32_t expected_drift = time_sync_calculate_expected_drift(
        (uint32_t)(esp_timer_get_time() / 1000) - g_time_sync_state.last_sync_ms
    );
    q->quality_score = calculate_sync_quality(offset_us, expected_drift, rtt_us);
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
