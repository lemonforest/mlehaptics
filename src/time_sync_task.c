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
#include "firmware_version.h"  // AD040: Firmware version logging
#include "motor_task.h"        // Phase 2: Beacon-triggered back-EMF logging
#include "button_task.h"       // Phase 3: Queue externs for coordination forwarding

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

/** @brief Flag set when CLIENT_READY message received (Phase 6 handshake) */
static volatile bool client_ready_received = false;

/** @brief Bug #11 fix: Buffer CLIENT_READY if received before time_sync initialized */
static volatile bool client_ready_buffered = false;

/** @brief Bug #28 fix: Buffer TIME_REQUEST if received before time_sync initialized */
static volatile bool time_request_buffered = false;
static volatile uint64_t buffered_t1_us = 0;
static volatile uint64_t buffered_t2_us = 0;

/*******************************************************************************
 * PRIVATE FUNCTION DECLARATIONS
 ******************************************************************************/

static void time_sync_task(void *arg);
static void handle_init_message(const time_sync_message_t *msg);
static void handle_disconnection_message(void);
static void handle_beacon_message(const time_sync_message_t *msg);
static void handle_coordination_message(const time_sync_message_t *msg);
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

esp_err_t time_sync_task_send_coordination(const coordination_message_t *msg)
{
    if (msg == NULL) {
        ESP_LOGE(TAG, "Coordination message pointer is NULL");
        return ESP_ERR_INVALID_ARG;
    }

    if (time_sync_queue == NULL) {
        ESP_LOGE(TAG, "Time sync queue not initialized");
        return ESP_FAIL;
    }

    time_sync_message_t task_msg = {
        .type = TIME_SYNC_MSG_COORDINATION,
        .data.coordination = {
            .msg = *msg
        }
    };

    if (xQueueSend(time_sync_queue, &task_msg, pdMS_TO_TICKS(100)) != pdTRUE) {
        ESP_LOGE(TAG, "Failed to send coordination message");
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

                case TIME_SYNC_MSG_COORDINATION:
                    handle_coordination_message(&msg);
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

    // Bug #11 fix: Process buffered CLIENT_READY if received before initialization
    if (client_ready_buffered && msg->data.init.role == TIME_SYNC_ROLE_SERVER) {
        client_ready_received = true;
        client_ready_buffered = false;  // Clear buffer flag
        ESP_LOGI(TAG, "Processing buffered CLIENT_READY (received before init)");
    }

    // Bug #28 fix: Process buffered TIME_REQUEST if received before initialization
    if (time_request_buffered && msg->data.init.role == TIME_SYNC_ROLE_SERVER) {
        uint64_t t3_server_send = 0;
        err = time_sync_process_handshake_request(buffered_t1_us, buffered_t2_us, &t3_server_send);
        if (err == ESP_OK) {
            // Get motor epoch to include in response
            uint64_t motor_epoch = 0;
            uint32_t motor_cycle = 0;
            time_sync_get_motor_epoch(&motor_epoch, &motor_cycle);

            // Send TIME_RESPONSE back to CLIENT
            coordination_message_t response = {
                .type = SYNC_MSG_TIME_RESPONSE,
                .timestamp_ms = (uint32_t)(esp_timer_get_time() / 1000),
                .payload.time_response = {
                    .t1_client_send_us = buffered_t1_us,
                    .t2_server_recv_us = buffered_t2_us,
                    .t3_server_send_us = t3_server_send,
                    .motor_epoch_us = motor_epoch,
                    .motor_cycle_ms = motor_cycle
                }
            };

            err = ble_send_coordination_message(&response);
            if (err == ESP_OK) {
                ESP_LOGI(TAG, "TIME_RESPONSE sent (buffered): T1=%llu, T2=%llu, T3=%llu, epoch=%llu, cycle=%lu",
                         buffered_t1_us, buffered_t2_us, t3_server_send, motor_epoch, motor_cycle);
            } else {
                ESP_LOGW(TAG, "Failed to send TIME_RESPONSE (buffered): %s", esp_err_to_name(err));
            }
        } else {
            ESP_LOGW(TAG, "Failed to process buffered TIME_REQUEST: %s", esp_err_to_name(err));
        }

        // Clear buffer flag
        time_request_buffered = false;
        ESP_LOGI(TAG, "Processing buffered TIME_REQUEST (received before init)");
    }

    // CLIENT: Initiate NTP-style 3-way handshake for precise initial offset
    // This bootstraps the EWMA filter with a measured (not estimated) RTT
    if (msg->data.init.role == TIME_SYNC_ROLE_CLIENT) {
        uint64_t t1 = 0;
        err = time_sync_initiate_handshake(&t1);
        if (err == ESP_OK) {
            // Send TIME_REQUEST to SERVER
            coordination_message_t request = {
                .type = SYNC_MSG_TIME_REQUEST,
                .timestamp_ms = (uint32_t)(esp_timer_get_time() / 1000),
                .payload.time_request = {
                    .t1_client_send_us = t1
                }
            };

            err = ble_send_coordination_message(&request);
            if (err == ESP_OK) {
                ESP_LOGI(TAG, "TIME_REQUEST sent: T1=%llu μs (awaiting SERVER response)", t1);
            } else {
                ESP_LOGW(TAG, "Failed to send TIME_REQUEST: %s (will use beacon bootstrap)", esp_err_to_name(err));
            }
        } else {
            ESP_LOGW(TAG, "Failed to initiate handshake: %s (will use beacon bootstrap)", esp_err_to_name(err));
        }
    }

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
    /* Phase 6r (AD043): Simplified beacon processing - no response sent
     *
     * CLIENT receives one-way timestamp from SERVER and applies EMA filter.
     * No need to send T2/T3 back to SERVER (eliminates RTT measurement overhead).
     */

    // Process beacon (CLIENT only)
    esp_err_t err = time_sync_process_beacon(&msg->data.beacon.beacon,
                                              msg->data.beacon.receive_time_us);

    if (err == ESP_OK) {
        // Get actual clock offset and sync quality for heartbeat logging
        int64_t clock_offset_us = 0;
        time_sync_quality_t quality;

        if (time_sync_get_clock_offset(&clock_offset_us) == ESP_OK &&
            time_sync_get_quality(&quality) == ESP_OK) {
            ESP_LOGI(TAG, "Sync beacon received: seq=%u, offset=%lld μs, drift=%ld μs, quality=%u%%",
                     msg->data.beacon.beacon.sequence,
                     clock_offset_us,         // Actual offset (CLIENT - SERVER)
                     quality.avg_drift_us,    // Drift (average offset change)
                     quality.quality_score);
        }

        // Phase 2: Trigger back-EMF logging to verify bilateral timing after sync
        motor_trigger_beacon_bemf_logging();
    } else {
        ESP_LOGW(TAG, "Failed to process beacon: %s", esp_err_to_name(err));
    }
}

/**
 * @brief Handle coordination message from peer (Phase 3)
 *
 * Processes coordination messages that were previously handled by motor_task.
 * Moving this here prevents BLE processing from blocking motor timing.
 *
 * Message types:
 * - SYNC_MSG_MODE_CHANGE: Forward to motor task queue
 * - SYNC_MSG_SETTINGS: Call individual ble_update_* functions
 * - SYNC_MSG_SHUTDOWN: Forward to button task queue
 * - SYNC_MSG_START_ADVERTISING: Start BLE advertising
 */
static void handle_coordination_message(const time_sync_message_t *msg)
{
    const coordination_message_t *coord = &msg->data.coordination.msg;

    ESP_LOGI(TAG, "Coordination message received: type=%d timestamp=%lu",
             coord->type, (unsigned long)coord->timestamp_ms);

    switch (coord->type) {
        case SYNC_MSG_MODE_CHANGE: {
            // Forward mode change to motor task queue
            task_message_t task_msg = {
                .type = MSG_MODE_CHANGE,
                .data = {.new_mode = coord->payload.mode}
            };

            if (button_to_motor_queue != NULL) {
                if (xQueueSend(button_to_motor_queue, &task_msg, pdMS_TO_TICKS(100)) == pdTRUE) {
                    ESP_LOGI(TAG, "Peer triggered mode change → %d", coord->payload.mode);
                } else {
                    ESP_LOGW(TAG, "Peer mode change failed: queue full");
                }
            } else {
                ESP_LOGW(TAG, "Peer mode change ignored: queue not initialized");
            }
            break;
        }

        case SYNC_MSG_SETTINGS: {
            // Process settings update using individual ble_update_* functions
            // This keeps power efficiency (only updates changed values) while
            // moving processing out of motor task (no timing disruption)
            const coordination_settings_t *settings = &coord->payload.settings;
            esp_err_t err;

            // Bug fix: Only notify motor task if motor-timing params (freq/duty) changed
            // Previously, ANY settings sync (e.g., session duration) triggered motor phase reset
            // causing bilateral timing to break during rapid PWA parameter adjustments
            // Note: Intensity changes handled per-mode via ble_update_modeX_intensity()
            uint16_t old_freq = ble_get_custom_frequency_hz();
            uint8_t old_duty = ble_get_custom_duty_percent();

            err = ble_update_custom_freq(settings->frequency_cHz);
            if (err != ESP_OK) {
                ESP_LOGW(TAG, "Failed to update frequency from peer: %s", esp_err_to_name(err));
            }

            err = ble_update_custom_duty(settings->duty_pct);
            if (err != ESP_OK) {
                ESP_LOGW(TAG, "Failed to update duty from peer: %s", esp_err_to_name(err));
            }

            // Update all 5 mode intensities
            err = ble_update_mode0_intensity(settings->mode0_intensity_pct);
            if (err != ESP_OK) {
                ESP_LOGW(TAG, "Failed to update mode 0 intensity from peer: %s", esp_err_to_name(err));
            }

            err = ble_update_mode1_intensity(settings->mode1_intensity_pct);
            if (err != ESP_OK) {
                ESP_LOGW(TAG, "Failed to update mode 1 intensity from peer: %s", esp_err_to_name(err));
            }

            err = ble_update_mode2_intensity(settings->mode2_intensity_pct);
            if (err != ESP_OK) {
                ESP_LOGW(TAG, "Failed to update mode 2 intensity from peer: %s", esp_err_to_name(err));
            }

            err = ble_update_mode3_intensity(settings->mode3_intensity_pct);
            if (err != ESP_OK) {
                ESP_LOGW(TAG, "Failed to update mode 3 intensity from peer: %s", esp_err_to_name(err));
            }

            err = ble_update_mode4_intensity(settings->mode4_intensity_pct);
            if (err != ESP_OK) {
                ESP_LOGW(TAG, "Failed to update mode 4 intensity from peer: %s", esp_err_to_name(err));
            }

            err = ble_update_led_palette(settings->led_color_idx);
            if (err != ESP_OK) {
                ESP_LOGW(TAG, "Failed to update LED color from peer: %s", esp_err_to_name(err));
            }

            err = ble_update_led_brightness(settings->led_brightness_pct);
            if (err != ESP_OK) {
                ESP_LOGW(TAG, "Failed to update LED brightness from peer: %s", esp_err_to_name(err));
            }

            err = ble_update_led_enable(settings->led_enable != 0);
            if (err != ESP_OK) {
                ESP_LOGW(TAG, "Failed to update LED enable from peer: %s", esp_err_to_name(err));
            }

            err = ble_update_led_color_mode(settings->led_color_mode);
            if (err != ESP_OK) {
                ESP_LOGW(TAG, "Failed to update LED color mode from peer: %s", esp_err_to_name(err));
            }

            err = ble_update_led_custom_rgb(settings->led_custom_r, settings->led_custom_g, settings->led_custom_b);
            if (err != ESP_OK) {
                ESP_LOGW(TAG, "Failed to update LED custom RGB from peer: %s", esp_err_to_name(err));
            }

            err = ble_update_session_duration(settings->session_duration_sec);
            if (err != ESP_OK) {
                ESP_LOGW(TAG, "Failed to update session duration from peer: %s", esp_err_to_name(err));
            }

            // Only notify motor task if motor-timing params actually changed
            // This prevents phase resets from session duration or LED changes
            // Note: Intensity changes handled per-mode, not checked here
            bool motor_timing_changed = (old_freq != settings->frequency_cHz) ||
                                        (old_duty != settings->duty_pct);
            if (motor_timing_changed) {
                ble_callback_params_updated();
                ESP_LOGI(TAG, "Settings synced from peer: freq=%.2fHz duty=%u%% LED=%s (MOTOR UPDATE + per-mode intensities)",
                         settings->frequency_cHz / 100.0f, settings->duty_pct,
                         settings->led_enable ? "ON" : "OFF");
            } else {
                ESP_LOGI(TAG, "Settings synced from peer: freq=%.2fHz duty=%u%% LED=%s (intensities updated)",
                         settings->frequency_cHz / 100.0f, settings->duty_pct,
                         settings->led_enable ? "ON" : "OFF");
            }
            break;
        }

        case SYNC_MSG_SHUTDOWN: {
            // Forward shutdown request to button_task
            ESP_LOGI(TAG, "Peer requested shutdown - forwarding to button_task");

            task_message_t shutdown_msg = {
                .type = MSG_EMERGENCY_SHUTDOWN,
                .data = {.new_mode = 0}
            };

            if (motor_to_button_queue != NULL) {
                if (xQueueSend(motor_to_button_queue, &shutdown_msg, pdMS_TO_TICKS(100)) == pdTRUE) {
                    ESP_LOGI(TAG, "Shutdown request forwarded to button_task");
                } else {
                    ESP_LOGW(TAG, "Failed to forward shutdown to button_task");
                }
            }
            break;
        }

        case SYNC_MSG_START_ADVERTISING: {
            // CLIENT requested SERVER to start advertising for PWA connection
            ble_start_advertising();
            ESP_LOGI(TAG, "Advertising restarted (CLIENT request)");
            break;
        }

        case SYNC_MSG_CLIENT_BATTERY: {
            // CLIENT sent its battery level to SERVER (Phase 6 - dual-device mode)
            // SERVER updates its client_battery characteristic for PWA access
            uint8_t client_batt = coord->payload.battery_level;
            ble_update_client_battery_level(client_batt);
            ESP_LOGI(TAG, "Client battery received: %u%%", client_batt);
            break;
        }

        case SYNC_MSG_CLIENT_READY: {
            // CLIENT received beacon and calculated phase - ready to start
            // SERVER can now start its motor cycle knowing CLIENT is synchronized

            // Bug #11 fix: Buffer CLIENT_READY if time_sync not yet initialized
            if (!TIME_SYNC_IS_INITIALIZED()) {
                client_ready_buffered = true;
                ESP_LOGI(TAG, "CLIENT_READY received early (buffered until time_sync initialized)");
                break;
            }

            client_ready_received = true;
            ESP_LOGI(TAG, "CLIENT_READY received - both devices synchronized");
            break;
        }

        case SYNC_MSG_TIME_REQUEST: {
            // SERVER receives TIME_REQUEST from CLIENT (NTP handshake step 1)
            // Record T2 (receive time) and generate T3 for response
            uint64_t t2_server_recv = esp_timer_get_time();
            uint64_t t1_client_send = coord->payload.time_request.t1_client_send_us;

            // Bug #28 fix: Buffer TIME_REQUEST if time_sync not yet initialized
            if (!TIME_SYNC_IS_INITIALIZED()) {
                time_request_buffered = true;
                buffered_t1_us = t1_client_send;
                buffered_t2_us = t2_server_recv;
                ESP_LOGI(TAG, "TIME_REQUEST received early (buffered until time_sync initialized)");
                break;
            }

            uint64_t t3_server_send = 0;

            esp_err_t err = time_sync_process_handshake_request(t1_client_send, t2_server_recv, &t3_server_send);
            if (err != ESP_OK) {
                ESP_LOGW(TAG, "Failed to process handshake request: %s", esp_err_to_name(err));
                break;
            }

            // Get motor epoch to include in response (so CLIENT doesn't wait for next beacon)
            uint64_t motor_epoch = 0;
            uint32_t motor_cycle = 0;
            time_sync_get_motor_epoch(&motor_epoch, &motor_cycle);  // OK if not set yet (returns 0)

            // Send TIME_RESPONSE back to CLIENT
            coordination_message_t response = {
                .type = SYNC_MSG_TIME_RESPONSE,
                .timestamp_ms = (uint32_t)(esp_timer_get_time() / 1000),
                .payload.time_response = {
                    .t1_client_send_us = t1_client_send,
                    .t2_server_recv_us = t2_server_recv,
                    .t3_server_send_us = t3_server_send,
                    .motor_epoch_us = motor_epoch,
                    .motor_cycle_ms = motor_cycle
                }
            };

            err = ble_send_coordination_message(&response);
            if (err == ESP_OK) {
                ESP_LOGI(TAG, "TIME_RESPONSE sent: T1=%llu, T2=%llu, T3=%llu, epoch=%llu, cycle=%lu",
                         t1_client_send, t2_server_recv, t3_server_send, motor_epoch, motor_cycle);

                /* Phase 6r: Send immediate beacon to bootstrap CLIENT's EMA filter
                 * Reduces first sample delay from ~4.35s to ~2s (2.35s faster convergence)
                 * Then 1s interval kicks in for fast startup tracking
                 */
                esp_err_t beacon_err = ble_send_time_sync_beacon();
                if (beacon_err == ESP_OK) {
                    ESP_LOGI(TAG, "Bootstrap beacon sent immediately after handshake (Phase 6r)");
                } else {
                    ESP_LOGW(TAG, "Failed to send bootstrap beacon: %s", esp_err_to_name(beacon_err));
                }
            } else {
                ESP_LOGW(TAG, "Failed to send TIME_RESPONSE: %s", esp_err_to_name(err));
            }
            break;
        }

        case SYNC_MSG_TIME_RESPONSE: {
            // CLIENT receives TIME_RESPONSE from SERVER (NTP handshake step 2)
            // Record T4 (receive time) and calculate precise offset
            uint64_t t4_client_recv = esp_timer_get_time();
            uint64_t t1 = coord->payload.time_response.t1_client_send_us;
            uint64_t t2 = coord->payload.time_response.t2_server_recv_us;
            uint64_t t3 = coord->payload.time_response.t3_server_send_us;
            uint64_t motor_epoch = coord->payload.time_response.motor_epoch_us;
            uint32_t motor_cycle = coord->payload.time_response.motor_cycle_ms;

            esp_err_t err = time_sync_process_handshake_response(t1, t2, t3, t4_client_recv);
            if (err == ESP_OK) {
                ESP_LOGI(TAG, "NTP handshake complete - EWMA filter bootstrapped with precise offset");

                // Extract motor epoch from handshake response (avoids 10s wait for next beacon)
                if (motor_epoch > 0 && motor_cycle > 0) {
                    err = time_sync_set_motor_epoch_from_handshake(motor_epoch, motor_cycle);
                    if (err == ESP_OK) {
                        ESP_LOGI(TAG, "Motor epoch from handshake: %llu μs, cycle=%lu ms", motor_epoch, motor_cycle);
                    }
                } else {
                    ESP_LOGD(TAG, "No motor epoch in handshake (SERVER not started yet)");
                }
            } else {
                ESP_LOGW(TAG, "Failed to process handshake response: %s", esp_err_to_name(err));
            }
            break;
        }

        case SYNC_MSG_MOTOR_STARTED: {
            /* Phase 6: CLIENT receives immediate motor epoch notification from SERVER
             * This eliminates the 9.5s delay waiting for periodic beacons.
             * CLIENT can calculate antiphase and start motors within 100-200ms.
             */
            uint64_t motor_epoch_us = coord->payload.motor_started.motor_epoch_us;
            uint32_t motor_cycle_ms = coord->payload.motor_started.motor_cycle_ms;

            esp_err_t err = time_sync_set_motor_epoch(motor_epoch_us, motor_cycle_ms);
            if (err == ESP_OK) {
                ESP_LOGI(TAG, "CLIENT: MOTOR_STARTED received (epoch=%llu, cycle=%lu) - can start motors immediately",
                         motor_epoch_us, motor_cycle_ms);

                // Issue #3 fix: Notify motor_task to abort coordinated start wait loop
                // This fixes the case where handshake and MOTOR_STARTED have same epoch value
                motor_task_notify_motor_started();
            } else {
                ESP_LOGW(TAG, "CLIENT: Failed to set motor epoch from MOTOR_STARTED: %s", esp_err_to_name(err));
            }
            break;
        }

        default:
            ESP_LOGW(TAG, "Unknown coordination message type: %d", coord->type);
            break;
    }
}

static void perform_periodic_update(void)
{
    // Periodic firmware version logging (AD040 - every 60 seconds)
    static uint32_t version_log_counter = 0;
    static firmware_version_t fw_version = {0};  // Cache version to avoid repeated calls

    if (version_log_counter == 0) {
        // Initialize cached version on first call
        fw_version = firmware_get_version();
    }

    version_log_counter++;
    if (version_log_counter >= 60) {  // Every 60 seconds (1-second periodic updates)
        ESP_LOGI(TAG, "[FW: v%d.%d.%d %s %s]",
                 fw_version.major, fw_version.minor, fw_version.patch,
                 fw_version.build_date, fw_version.build_time);
        version_log_counter = 0;
    }

    if (!TIME_SYNC_IS_INITIALIZED()) {
        return;
    }

    // SERVER: Send sync beacon if interval elapsed
    // CRITICAL: Check and send BEFORE time_sync_update() resets the timestamp
    // Bug fix: time_sync_update() updates last_sync_ms, which invalidates
    // the interval check if done afterwards
    bool beacon_sent = false;
    if (TIME_SYNC_IS_SERVER() && time_sync_should_send_beacon()) {
        esp_err_t err = ble_send_time_sync_beacon();
        if (err == ESP_OK) {
            beacon_sent = true;
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

    // Log beacon sent with UPDATED adaptive interval (after time_sync_update() adjusts it)
    // Bug fix: Nov 23, 2025 - shows actual next interval, not previous interval
    if (beacon_sent) {
        time_sync_quality_t quality;
        time_sync_get_quality(&quality);
        ESP_LOGI(TAG, "Sync beacon sent: quality=%u%%, next_interval=%lu ms, drift=%lu μs",
                 quality.quality_score,
                 time_sync_get_interval_ms(),  // Now shows ADJUSTED interval
                 quality.max_drift_us);

        // Phase 2: Log BLE diagnostics with each sync beacon (Nov 29, 2025)
        // Monitors RX queue depth, HCI buffers, connection stats to identify notification buffering issues
        ble_log_diagnostics();

        // SERVER: Trigger back-EMF logging to verify bilateral timing (mirror CLIENT behavior)
        // This allows comparing motor timings on both devices simultaneously
        motor_trigger_beacon_bemf_logging();
    }
}

/*******************************************************************************
 * CLIENT_READY HANDSHAKE (Phase 6 - Synchronized Session Start)
 ******************************************************************************/

/**
 * @brief Check if CLIENT_READY message has been received
 * @return true if CLIENT is ready, false otherwise
 *
 * Used by SERVER motor_task to wait for CLIENT synchronization before starting
 */
bool time_sync_client_ready_received(void)
{
    return client_ready_received;
}

/**
 * @brief Reset CLIENT_READY flag for next session
 *
 * Called at start of pairing to clear stale state from previous session
 */
void time_sync_reset_client_ready(void)
{
    client_ready_received = false;
    client_ready_buffered = false;  // Bug #11 fix: Also clear buffer flag
    time_request_buffered = false;  // Bug #28 fix: Also clear TIME_REQUEST buffer flag
}
