/**
 * @file time_sync_task.c
 * @brief Time Synchronization Task Module - Implementation
 *
 * Dedicated FreeRTOS task for managing time synchronization between peer devices.
 *
 * Phase 2 (AD039): Hybrid time synchronization protocol
 *
 * Task Responsibilities:
 * - Initialize time sync module with assigned role
 * - Periodic sync updates (adaptive 10-60s intervals)
 * - SERVER: Send sync beacons via BLE notifications
 * - CLIENT: Process received beacons, update clock offset
 * - Handle peer disconnection (freeze sync state)
 * - Log sync quality metrics (heartbeat logging)
 *
 * @date 2025-11-19
 * @author Claude Code (Anthropic)
 */

#include "time_sync_task.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "esp_task_wdt.h"
#include "ble_manager.h"

static const char *TAG = "TIME_SYNC_TASK";

/*******************************************************************************
 * PRIVATE VARIABLES
 ******************************************************************************/

/** @brief Time sync task handle */
static TaskHandle_t time_sync_task_handle = NULL;

/** @brief Message queue for time sync task */
static QueueHandle_t time_sync_queue = NULL;

/** @brief Next periodic update time (ticks) */
static TickType_t next_update_time = 0;

/*******************************************************************************
 * PRIVATE FUNCTION DECLARATIONS
 ******************************************************************************/

static void time_sync_task(void *arg);
static void handle_init_message(const time_sync_message_t *msg);
static void handle_disconnection_message(void);
static void handle_beacon_message(const time_sync_message_t *msg);
static void perform_periodic_update(void);

/*******************************************************************************
 * PUBLIC API IMPLEMENTATION
 ******************************************************************************/

esp_err_t time_sync_task_init(void)
{
    // Create message queue
    time_sync_queue = xQueueCreate(TIME_SYNC_QUEUE_DEPTH, sizeof(time_sync_message_t));
    if (time_sync_queue == NULL) {
        ESP_LOGE(TAG, "Failed to create time sync queue");
        return ESP_ERR_NO_MEM;
    }

    // Create task
    BaseType_t result = xTaskCreate(
        time_sync_task,
        "time_sync",
        TIME_SYNC_TASK_STACK_SIZE,
        NULL,
        TIME_SYNC_TASK_PRIORITY,
        &time_sync_task_handle
    );

    if (result != pdPASS) {
        ESP_LOGE(TAG, "Failed to create time sync task");
        vQueueDelete(time_sync_queue);
        time_sync_queue = NULL;
        return ESP_ERR_NO_MEM;
    }

    ESP_LOGI(TAG, "Time sync task created (priority=%d, stack=%d bytes)",
             TIME_SYNC_TASK_PRIORITY, TIME_SYNC_TASK_STACK_SIZE);

    return ESP_OK;
}

esp_err_t time_sync_task_send_init(time_sync_role_t role)
{
    if (time_sync_queue == NULL) {
        ESP_LOGE(TAG, "Time sync queue not initialized");
        return ESP_FAIL;
    }

    time_sync_message_t msg = {
        .type = TIME_SYNC_MSG_INIT,
        .data.init = {
            .role = role
        }
    };

    if (xQueueSend(time_sync_queue, &msg, pdMS_TO_TICKS(100)) != pdTRUE) {
        ESP_LOGE(TAG, "Failed to send init message to time sync task");
        return ESP_FAIL;
    }

    return ESP_OK;
}

esp_err_t time_sync_task_send_disconnection(void)
{
    if (time_sync_queue == NULL) {
        ESP_LOGE(TAG, "Time sync queue not initialized");
        return ESP_FAIL;
    }

    time_sync_message_t msg = {
        .type = TIME_SYNC_MSG_DISCONNECTION
    };

    if (xQueueSend(time_sync_queue, &msg, pdMS_TO_TICKS(100)) != pdTRUE) {
        ESP_LOGE(TAG, "Failed to send disconnection message");
        return ESP_FAIL;
    }

    return ESP_OK;
}

esp_err_t time_sync_task_send_beacon(const time_sync_beacon_t *beacon, uint64_t receive_time_us)
{
    if (beacon == NULL) {
        ESP_LOGE(TAG, "Beacon pointer is NULL");
        return ESP_ERR_INVALID_ARG;
    }

    if (time_sync_queue == NULL) {
        ESP_LOGE(TAG, "Time sync queue not initialized");
        return ESP_FAIL;
    }

    time_sync_message_t msg = {
        .type = TIME_SYNC_MSG_BEACON_RECEIVED,
        .data.beacon = {
            .beacon = *beacon,
            .receive_time_us = receive_time_us
        }
    };

    if (xQueueSend(time_sync_queue, &msg, pdMS_TO_TICKS(100)) != pdTRUE) {
        ESP_LOGE(TAG, "Failed to send beacon message");
        return ESP_FAIL;
    }

    return ESP_OK;
}

QueueHandle_t time_sync_task_get_queue(void)
{
    return time_sync_queue;
}

/*******************************************************************************
 * TASK IMPLEMENTATION
 ******************************************************************************/

static void time_sync_task(void *arg)
{
    ESP_LOGI(TAG, "Time sync task started");

    // Subscribe to watchdog (JPL compliance)
    ESP_ERROR_CHECK(esp_task_wdt_add(NULL));

    time_sync_message_t msg;
    next_update_time = xTaskGetTickCount() + pdMS_TO_TICKS(time_sync_get_interval_ms());

    while (1) {
        // Wait for message or timeout for periodic update
        TickType_t wait_time = pdMS_TO_TICKS(1000);  // Check every 1 second

        if (xQueueReceive(time_sync_queue, &msg, wait_time) == pdTRUE) {
            // Handle received message
            switch (msg.type) {
                case TIME_SYNC_MSG_INIT:
                    handle_init_message(&msg);
                    break;

                case TIME_SYNC_MSG_DISCONNECTION:
                    handle_disconnection_message();
                    break;

                case TIME_SYNC_MSG_BEACON_RECEIVED:
                    handle_beacon_message(&msg);
                    break;

                case TIME_SYNC_MSG_SHUTDOWN:
                    ESP_LOGI(TAG, "Shutdown requested");
                    esp_task_wdt_delete(NULL);
                    vTaskDelete(NULL);
                    return;

                default:
                    ESP_LOGW(TAG, "Unknown message type: %d", msg.type);
                    break;
            }
        }

        // Periodic update check
        TickType_t now = xTaskGetTickCount();
        if ((int32_t)(now - next_update_time) >= 0) {
            perform_periodic_update();

            // Schedule next update (time_sync_update() adjusts interval internally)
            next_update_time = now + pdMS_TO_TICKS(time_sync_get_interval_ms());
        }

        // Feed watchdog
        esp_task_wdt_reset();
    }
}

/*******************************************************************************
 * PRIVATE FUNCTIONS
 ******************************************************************************/

static void handle_init_message(const time_sync_message_t *msg)
{
    ESP_LOGI(TAG, "Initializing time sync: role=%s (NTP-style)",
             msg->data.init.role == TIME_SYNC_ROLE_SERVER ? "SERVER" : "CLIENT");

    // Initialize time sync module
    esp_err_t err = time_sync_init(msg->data.init.role);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Failed to initialize time sync: %s", esp_err_to_name(err));
        return;
    }

    // Establish initial connection sync (no parameters needed for NTP-style)
    err = time_sync_on_connection();
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Failed to establish connection sync: %s", esp_err_to_name(err));
        return;
    }

    ESP_LOGI(TAG, "Time sync initialized successfully (%s role)",
             msg->data.init.role == TIME_SYNC_ROLE_SERVER ? "SERVER" : "CLIENT");

    // Schedule next update (time_sync module handles interval initialization)
    next_update_time = xTaskGetTickCount() + pdMS_TO_TICKS(time_sync_get_interval_ms());
}

static void handle_disconnection_message(void)
{
    ESP_LOGI(TAG, "Peer disconnected, freezing time sync state");

    esp_err_t err = time_sync_on_disconnection();
    if (err == ESP_OK) {
        time_sync_quality_t quality;
        if (time_sync_get_quality(&quality) == ESP_OK) {
            ESP_LOGI(TAG, "Time sync frozen: avg_drift=%ld μs, quality=%u%%",
                     quality.avg_drift_us, quality.quality_score);
        }
    } else if (err != ESP_ERR_INVALID_STATE) {
        ESP_LOGW(TAG, "Failed to handle disconnection: %s", esp_err_to_name(err));
    }
}

static void handle_beacon_message(const time_sync_message_t *msg)
{
    // Process beacon (CLIENT only)
    esp_err_t err = time_sync_process_beacon(&msg->data.beacon.beacon,
                                              msg->data.beacon.receive_time_us);

    if (err == ESP_OK) {
        // Get actual clock offset and sync quality for heartbeat logging
        int64_t clock_offset_us = 0;
        time_sync_quality_t quality;

        if (time_sync_get_clock_offset(&clock_offset_us) == ESP_OK &&
            time_sync_get_quality(&quality) == ESP_OK) {
            ESP_LOGI(TAG, "Sync beacon received: seq=%u, offset=%lld μs, drift=%ld μs, quality=%u%%, rtt=%lu μs",
                     msg->data.beacon.beacon.sequence,
                     clock_offset_us,         // Actual offset (CLIENT - SERVER)
                     quality.avg_drift_us,    // Drift (average offset change)
                     quality.quality_score,
                     quality.last_rtt_us);
        }
    } else {
        ESP_LOGW(TAG, "Failed to process beacon: %s", esp_err_to_name(err));
    }
}

static void perform_periodic_update(void)
{
    if (!TIME_SYNC_IS_INITIALIZED()) {
        return;
    }

    // SERVER: Send sync beacon if interval elapsed
    // CRITICAL: Check and send BEFORE time_sync_update() resets the timestamp
    // Bug fix: time_sync_update() updates last_sync_ms, which invalidates
    // the interval check if done afterwards
    if (TIME_SYNC_IS_SERVER() && time_sync_should_send_beacon()) {
        time_sync_quality_t quality;
        time_sync_get_quality(&quality);

        esp_err_t err = ble_send_time_sync_beacon();
        if (err == ESP_OK) {
            ESP_LOGI(TAG, "Sync beacon sent: quality=%u%%, interval=%lu ms, drift=%lu μs",
                     quality.quality_score,
                     time_sync_get_interval_ms(),
                     quality.max_drift_us);
        } else if (err == ESP_ERR_INVALID_STATE) {
            // INFO log for ESP_ERR_INVALID_STATE (peer not connected or handle not initialized)
            // This helps diagnose why beacons aren't being sent
            ESP_LOGI(TAG, "Cannot send sync beacon: invalid state (peer disconnected or handle not initialized)");
        } else {
            ESP_LOGW(TAG, "Failed to send sync beacon: %s", esp_err_to_name(err));
        }
    }

    // Call time sync update (updates timestamp, adjusts interval, logs status)
    esp_err_t err = time_sync_update();
    if (err != ESP_OK && err != ESP_ERR_INVALID_STATE) {
        ESP_LOGW(TAG, "Time sync update failed: %s", esp_err_to_name(err));
    }
}
