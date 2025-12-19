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
#include "esp_random.h"        // AD048: Hardware RNG for nonce generation
#include "ble_manager.h"
#include "firmware_version.h"  // AD040: Firmware version checking
#include "status_led.h"        // AD040: Version mismatch LED pattern
#include "motor_task.h"        // Phase 2: Beacon-triggered back-EMF logging
#include "button_task.h"       // Phase 3: Queue externs for coordination forwarding
#include "pattern_playback.h"  // AD047: Pattern sync between devices
#include "espnow_transport.h"  // AD048: ESP-NOW transport for low-latency beacons
#include <string.h>            // AD048: memcpy, memset for MAC/key handling

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

/** @brief AD048: Last processed beacon sequence for deduplication (ESP-NOW + BLE) */
static uint8_t last_processed_beacon_seq = 255;  // Init to unlikely value

#if TDM_TECH_SPIKE_ENABLED
/*******************************************************************************
 * TDM TECH SPIKE - Results (December 2025)
 *
 * KEY FINDING: ~74ms consistent latency bias, outliers inflate stddev to ~150ms.
 * Mean converges as sample count increases - this is useful!
 * Next step: Add histogram to measure % of packets within ±30ms of mean.
 * See time_sync.h for full analysis.
 ******************************************************************************/

/** @brief Last beacon receive timestamp (microseconds) */
static int64_t tdm_last_receive_us = 0;

/** @brief Jitter measurement sample count */
static uint32_t tdm_jitter_count = 0;

/** @brief Sum of jitter values (for mean calculation) */
static int64_t tdm_jitter_sum_us = 0;

/** @brief Sum of squared jitter values (for stddev calculation) */
static int64_t tdm_jitter_sum_sq = 0;

/** @brief Minimum jitter observed (microseconds) */
static int64_t tdm_jitter_min_us = INT64_MAX;

/** @brief Maximum jitter observed (microseconds) */
static int64_t tdm_jitter_max_us = INT64_MIN;

/** @brief Log stats every N samples */
#define TDM_JITTER_LOG_INTERVAL  10
#endif /* TDM_TECH_SPIKE_ENABLED */

/** @brief Bug #28 fix: Buffer TIME_REQUEST if received before time_sync initialized */
static volatile bool time_request_buffered = false;
static volatile uint64_t buffered_t1_us = 0;
static volatile uint64_t buffered_t2_us = 0;

/*******************************************************************************
 * AD048: ESP-NOW KEY EXCHANGE STATE
 *
 * Storage for peer WiFi MAC and nonce during key derivation.
 * Flow:
 * 1. Both devices exchange WIFI_MAC messages
 * 2. SERVER generates nonce, sends KEY_EXCHANGE to CLIENT
 * 3. Both derive LMK using HKDF(server_mac || client_mac || nonce)
 * 4. Both configure encrypted ESP-NOW peer
 ******************************************************************************/

/** @brief Stored peer WiFi MAC for key derivation */
static uint8_t peer_wifi_mac[6] = {0};

/** @brief Flag indicating peer MAC has been received */
static bool peer_wifi_mac_received = false;

/** @brief Server-generated nonce for key derivation (only valid on SERVER) */
static uint8_t session_nonce[8] = {0};

/** @brief Flag indicating key exchange is complete (encrypted ESP-NOW ready) */
static bool espnow_key_exchange_complete = false;

/*******************************************************************************
 * PRIVATE FUNCTION DECLARATIONS
 ******************************************************************************/

static void time_sync_task(void *arg);
static void handle_init_message(const time_sync_message_t *msg);
static void handle_disconnection_message(void);
static void handle_beacon_message(const time_sync_message_t *msg);
static void handle_coordination_message(const time_sync_message_t *msg);
static void perform_periodic_update(void);
static void espnow_beacon_recv_callback(const time_sync_beacon_t *beacon, uint64_t rx_time_us);

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

    // AD048: Register ESP-NOW beacon callback for low-latency beacon delivery
    // The callback runs in WiFi task context and queues beacons to time_sync_task
    espnow_transport_register_callback(espnow_beacon_recv_callback);
    ESP_LOGI(TAG, "AD048: ESP-NOW beacon callback registered");

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

esp_err_t time_sync_task_send_beacon(const time_sync_beacon_t *beacon, uint64_t receive_time_us, uint8_t transport)
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
            .receive_time_us = receive_time_us,
            .transport = transport
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

esp_err_t time_sync_task_trigger_beacons(void)
{
    if (time_sync_queue == NULL) {
        ESP_LOGE(TAG, "Time sync queue not initialized");
        return ESP_FAIL;
    }

    time_sync_message_t msg = {
        .type = TIME_SYNC_MSG_TRIGGER_BEACONS
    };

    if (xQueueSend(time_sync_queue, &msg, pdMS_TO_TICKS(100)) != pdTRUE) {
        ESP_LOGE(TAG, "Failed to send trigger beacons message");
        return ESP_FAIL;
    }

    return ESP_OK;
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
        /* Bug #58 fix: Drain ALL messages from queue each iteration
         *
         * Previous bug: Task processed only ONE message per iteration with 1-second
         * timeout. When multiple messages arrived rapidly (mode change + ACK + SYNC_FB),
         * the queue would fill up and never recover.
         *
         * Fix: Use a short timeout (100ms) and drain all pending messages each iteration.
         * This ensures queue stays responsive even during burst traffic.
         */
        TickType_t wait_time = pdMS_TO_TICKS(100);  // Short wait to stay responsive

        while (xQueueReceive(time_sync_queue, &msg, wait_time) == pdTRUE) {
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

                case TIME_SYNC_MSG_TRIGGER_BEACONS:
                    /* UTLP Refactor: Mode-change beacons REMOVED
                     *
                     * Mode changes use SYNC_MSG_MOTOR_STARTED for epoch delivery.
                     * Beacons are now handled by the time layer on a fixed schedule,
                     * not triggered by application events.
                     *
                     * See: UTLP architecture - time handles time, application handles application.
                     */
                    ESP_LOGD(TAG, "TRIGGER_BEACONS ignored (UTLP refactor - use MOTOR_STARTED for epoch)");
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

            /* After processing each message, check for more with zero wait */
            wait_time = 0;  // Don't block on subsequent checks
        }

        /* Bug #62 fix: REMOVED continuous beacon check
         *
         * Previous Bug #57/58: Tried to send forced beacons every 100ms to help
         * CLIENT converge after mode changes.
         *
         * Problem: time_sync_should_send_beacon() doesn't update last_sync_ms,
         * so it returned true continuously, causing beacon spam (100+ beacons).
         *
         * Root cause: Beacon blasting doesn't help EMA convergence anyway.
         * EMA converges based on sample COUNT over TIME, not rapid-fire samples.
         *
         * Fix: Send ONE beacon on mode change (for epoch delivery), then let
         * perform_periodic_update() handle normal interval beacons.
         */

        // Bug #95: Debounced frequency change triggers coordinated mode change
        // When PWA user drags frequency slider, we debounce 300ms then trigger
        // AD045 two-phase commit mode change to resynchronize both devices.
        // Only SERVER initiates mode changes (button press equivalent).
        if (TIME_SYNC_IS_SERVER() && ble_check_and_clear_freq_change_pending(300)) {
            ESP_LOGI(TAG, "Bug #95: Frequency change settled - triggering coordinated mode change");

            // Send MSG_MODE_CHANGE to motor_task (same as button press)
            // Motor task will execute AD045 protocol to sync with CLIENT
            task_message_t msg = {
                .type = MSG_MODE_CHANGE,
                .data.new_mode = MODE_CUSTOM  // Re-arm Mode 4 with new frequency
            };

            if (xQueueSend(button_to_motor_queue, &msg, 0) != pdTRUE) {
                ESP_LOGW(TAG, "Failed to queue frequency change mode update");
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

    // AD048: Reset deduplication state so we don't skip first beacon after reconnect
    last_processed_beacon_seq = 255;

    // AD048: Reset key exchange state for new session on reconnect
    peer_wifi_mac_received = false;
    espnow_key_exchange_complete = false;
    memset(peer_wifi_mac, 0, sizeof(peer_wifi_mac));
    memset(session_nonce, 0, sizeof(session_nonce));

    // Clear ESP-NOW peer (will be reconfigured on reconnect)
    espnow_transport_clear_peer();

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

    /* AD048: Deduplicate - ESP-NOW arrives first (~100μs latency), BLE arrives
     * ~50-70ms later with same sequence number. Skip duplicates to prevent
     * BLE's higher latency from polluting the EMA filter. First-wins strategy. */
    uint8_t seq = msg->data.beacon.beacon.sequence;
    if (seq == last_processed_beacon_seq) {
        const char *transport_str = (msg->data.beacon.transport == BEACON_TRANSPORT_ESPNOW) ? "ESP-NOW" : "BLE";
        ESP_LOGD(TAG, "AD048: Skipping duplicate seq=%u [%s] (already processed)", seq, transport_str);
        return;
    }
    last_processed_beacon_seq = seq;

    // Process beacon (CLIENT only)
    esp_err_t err = time_sync_process_beacon(&msg->data.beacon.beacon,
                                              msg->data.beacon.receive_time_us);

    if (err == ESP_OK) {
        // Get actual clock offset and sync quality for heartbeat logging
        int64_t clock_offset_us = 0;
        time_sync_quality_t quality;

        if (time_sync_get_clock_offset(&clock_offset_us) == ESP_OK &&
            time_sync_get_quality(&quality) == ESP_OK) {
            const char *transport_str = (msg->data.beacon.transport == BEACON_TRANSPORT_ESPNOW) ? "ESP-NOW" : "BLE";
            ESP_LOGI(TAG, "Sync beacon received [%s]: seq=%u, offset=%lld μs, drift=%ld μs, quality=%u%%",
                     transport_str,
                     msg->data.beacon.beacon.sequence,
                     clock_offset_us,         // Actual offset (CLIENT - SERVER)
                     quality.avg_drift_us,    // Drift (average offset change)
                     quality.quality_score);
        }

#if TDM_TECH_SPIKE_ENABLED
        /* TDM jitter measurement: ~74ms consistent bias, outliers inflate stddev.
         * TODO: Add histogram buckets to measure distribution. */
        {
            int64_t receive_us = msg->data.beacon.receive_time_us;

            if (tdm_last_receive_us != 0) {
                /* Calculate inter-beacon interval and jitter */
                int64_t actual_interval_us = receive_us - tdm_last_receive_us;
                int64_t expected_interval_us = (int64_t)TDM_INTERVAL_MS * 1000;
                int64_t jitter_us = actual_interval_us - expected_interval_us;

                /* Update running statistics */
                tdm_jitter_count++;
                tdm_jitter_sum_us += jitter_us;
                tdm_jitter_sum_sq += (jitter_us * jitter_us);

                if (jitter_us < tdm_jitter_min_us) {
                    tdm_jitter_min_us = jitter_us;
                }
                if (jitter_us > tdm_jitter_max_us) {
                    tdm_jitter_max_us = jitter_us;
                }

                /* Log statistics every N samples */
                if (tdm_jitter_count % TDM_JITTER_LOG_INTERVAL == 0) {
                    int64_t mean_us = tdm_jitter_sum_us / (int64_t)tdm_jitter_count;
                    /* Variance = E[X²] - E[X]² */
                    int64_t mean_sq = tdm_jitter_sum_sq / (int64_t)tdm_jitter_count;
                    int64_t variance = mean_sq - (mean_us * mean_us);
                    /* Approximate sqrt for stddev (integer math) */
                    int64_t stddev_us = 0;
                    if (variance > 0) {
                        /* Newton-Raphson integer sqrt approximation */
                        stddev_us = variance;
                        int64_t x = variance;
                        while (x > stddev_us / x) {
                            x = (x + variance / x) / 2;
                        }
                        stddev_us = x;
                    }

                    ESP_LOGI(TAG, "TDM Jitter [n=%lu]: mean=%lld μs, stddev=%lld μs, min=%lld, max=%lld",
                             (unsigned long)tdm_jitter_count,
                             mean_us, stddev_us,
                             tdm_jitter_min_us, tdm_jitter_max_us);
                }
            }

            tdm_last_receive_us = receive_us;
        }
#endif /* TDM_TECH_SPIKE_ENABLED */

        // Note: BEMF logging now uses independent 60s timer in motor_task (not beacon-triggered)
    } else {
        ESP_LOGW(TAG, "Failed to process beacon: %s", esp_err_to_name(err));
    }
}

/**
 * @brief ESP-NOW beacon receive callback (AD048)
 *
 * This callback runs in WiFi task context when an ESP-NOW beacon is received.
 * It queues the beacon to time_sync_task for processing (same path as BLE beacons).
 *
 * Benefits of ESP-NOW:
 * - Sub-millisecond latency (~100μs jitter vs BLE's ~50ms)
 * - Connectionless, fires-and-forgets (no ACK overhead)
 * - Runs alongside BLE for redundancy
 *
 * @param beacon   Pointer to received beacon data
 * @param rx_time_us  Hardware timestamp when beacon was received
 */
static void espnow_beacon_recv_callback(const time_sync_beacon_t *beacon, uint64_t rx_time_us)
{
    // Queue beacon to time_sync_task with ESP-NOW transport marker
    esp_err_t err = time_sync_task_send_beacon(beacon, rx_time_us, BEACON_TRANSPORT_ESPNOW);

    if (err == ESP_OK) {
        ESP_LOGD(TAG, "AD048: ESP-NOW beacon queued (seq=%u, rx=%llu μs)",
                 beacon->sequence, rx_time_us);
    } else {
        // Queue full or other error - beacon dropped (not critical, next one will arrive)
        ESP_LOGW(TAG, "AD048: Failed to queue ESP-NOW beacon: %s", esp_err_to_name(err));
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

            /* Reset time sync filter to fast-attack mode for quick convergence
             * Mode changes reset the motor epoch, so filter needs to adapt quickly
             * to avoid jerky motor corrections during the first 10-40 seconds */
            esp_err_t reset_err = time_sync_reset_filter_fast_attack();
            if (reset_err != ESP_OK) {
                ESP_LOGW(TAG, "Failed to reset filter to fast-attack mode: %s",
                         esp_err_to_name(reset_err));
            }

            /* UTLP Refactor: Mode-change beacons REMOVED
             *
             * Mode changes deliver epoch via SYNC_MSG_MOTOR_STARTED message,
             * not via forced beacons. Time layer handles timing on fixed schedule.
             *
             * See: UTLP architecture - time handles time, application handles application.
             */
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
                /* UTLP Refactor: Beacon burst REMOVED
                 * Time sync now relies on fixed-interval beacons, not event-triggered bursts.
                 * Handshake provides epoch via TIME_RESPONSE.motor_epoch_us field.
                 */
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

        case SYNC_MSG_MODE_CHANGE_PROPOSAL: {
            // AD045: CLIENT receives mode change proposal from SERVER
            // Bug #69: Validate epoch-relative consistency (both devices can verify)
            const mode_change_proposal_t *proposal = &coord->payload.mode_proposal;

            ESP_LOGI(TAG, "CLIENT: Mode change proposal received (mode=%s, server_epoch=%llu, client_epoch=%llu)",
                     modes[proposal->new_mode].name, proposal->server_epoch_us, proposal->client_epoch_us);

            // Validate that epochs are in the future
            uint64_t current_time_us;
            if (time_sync_get_time(&current_time_us) != ESP_OK) {
                ESP_LOGW(TAG, "CLIENT: Cannot validate proposal - time sync not available");
                break;
            }

            if (proposal->client_epoch_us <= current_time_us) {
                ESP_LOGW(TAG, "CLIENT: Proposal rejected - epoch already passed (current=%llu, client_epoch=%llu)",
                         current_time_us, proposal->client_epoch_us);
                break;
            }

            // Bug #69: Verify epoch-relative consistency
            // CLIENT can independently check that server_epoch aligns with known motor epoch
            uint64_t motor_epoch_us;
            uint32_t motor_cycle_ms;
            if (time_sync_get_motor_epoch(&motor_epoch_us, &motor_cycle_ms) == ESP_OK &&
                motor_epoch_us > 0 && motor_cycle_ms > 0) {
                // Server's transition epoch should be: motor_epoch + (N * period)
                uint64_t period_us = (uint64_t)motor_cycle_ms * 1000ULL;
                uint64_t offset_from_epoch = (proposal->server_epoch_us > motor_epoch_us) ?
                                             (proposal->server_epoch_us - motor_epoch_us) : 0;
                uint64_t cycles_to_transition = offset_from_epoch / period_us;
                uint64_t remainder_us = offset_from_epoch % period_us;

                // Log verification (remainder should be ~0 if epoch-aligned)
                if (remainder_us > 1000) {  // >1ms remainder = not cycle-aligned
                    ESP_LOGW(TAG, "CLIENT: Proposal not epoch-aligned (remainder=%lluus)", remainder_us);
                } else {
                    ESP_LOGI(TAG, "CLIENT: Proposal verified (transition at cycle %llu)", cycles_to_transition);
                }
            }

            // Send acknowledgment to SERVER
            coordination_message_t ack = {
                .type = SYNC_MSG_MODE_CHANGE_ACK,
                .timestamp_ms = (uint32_t)(esp_timer_get_time() / 1000),
                .payload = {0}  // No payload for ACK
            };

            esp_err_t err = ble_send_coordination_message(&ack);
            if (err == ESP_OK) {
                ESP_LOGI(TAG, "CLIENT: Mode change ACK sent to SERVER");

                // Arm mode change for CLIENT epoch
                // motor_task will check mode_change_armed and execute when epoch reached
                mode_change_armed = true;
                armed_new_mode = proposal->new_mode;
                armed_epoch_us = proposal->client_epoch_us;
                armed_cycle_ms = proposal->new_cycle_ms;
                armed_active_ms = proposal->new_active_ms;
                // Bug #82 fix: Store SERVER's epoch for CLIENT antiphase calculation
                armed_server_epoch_us = proposal->server_epoch_us;

                ESP_LOGI(TAG, "CLIENT: Mode change armed for epoch %llu", armed_epoch_us);
            } else {
                ESP_LOGW(TAG, "CLIENT: Failed to send mode change ACK: %s", esp_err_to_name(err));
            }
            break;
        }

        case SYNC_MSG_MODE_CHANGE_ACK: {
            // AD045: SERVER receives acknowledgment from CLIENT
            ESP_LOGI(TAG, "SERVER: Mode change ACK received from CLIENT - proposal accepted");
            // No action needed - both devices will execute at their respective epochs
            break;
        }

        case SYNC_MSG_ACTIVATION_REPORT: {
            // PTP-style synchronization error feedback (IEEE 1588 Delay_Req pattern)
            // CLIENT reports its activation timing for SERVER's independent drift verification
            const activation_report_t *report = &coord->payload.activation_report;

            // AD043: Record T4 = SERVER's local time when SYNC_FB received
            uint64_t t4_server_rx_time_us = esp_timer_get_time();

            // PTP hardening: Log raw timestamps and path asymmetry for systematic error analysis
            // T1 = SERVER send beacon, T2 = CLIENT receive beacon
            // T3 = CLIENT send report, T4 = SERVER receive report
            if (report->beacon_server_time_us > 0 && report->beacon_rx_time_us > 0) {
                int64_t t1 = (int64_t)report->beacon_server_time_us;
                int64_t t2 = (int64_t)report->beacon_rx_time_us;
                int64_t t3 = (int64_t)report->report_tx_time_us;
                int64_t t4 = (int64_t)t4_server_rx_time_us;

                // NTP offset formula: offset = [(T2-T1) - (T4-T3)] / 2
                // delay = [(T2-T1) + (T4-T3)] / 2  (this cancels clock offset, shows REAL delay)
                int64_t raw_fwd_us = t2 - t1;         // Contaminated by clock offset
                int64_t raw_rev_us = t4 - t3;         // Contaminated by clock offset
                int64_t ntp_offset_us = (raw_fwd_us - raw_rev_us) / 2;  // Clock offset
                int64_t one_way_delay_us = (raw_fwd_us + raw_rev_us) / 2;  // TRUE one-way delay

                // REAL path asymmetry (offset-corrected):
                // real_fwd = raw_fwd + offset = (raw_fwd + raw_rev)/2 = delay (same for both!)
                // If NTP assumptions hold (symmetric paths), asymmetry should be ~0
                // Non-zero asymmetry here indicates our 25ms bug source!
                //
                // Derivation: If real delays are D+A and D-A (asymmetric by 2A):
                //   raw_fwd = D+A - X, raw_rev = D-A + X
                //   delay = D (correct), offset_ntp = A - X (WRONG by A!)
                // So we CANNOT detect asymmetry from a single exchange - it's baked into offset.
                // But we can compare offset_ntp with EMA offset to detect asymmetry.
                int64_t ema_offset_us = 0;
                time_sync_get_clock_offset(&ema_offset_us);
                int64_t offset_diff_us = ntp_offset_us - ema_offset_us;

                // Log: delay_ms is the actual BLE latency, offset_diff shows if this sample differs from EMA
                ESP_LOGI(TAG, "[PTP] delay=%lldms offset_ntp=%lldms ema=%lldms diff=%lldms",
                         one_way_delay_us / 1000, ntp_offset_us / 1000,
                         ema_offset_us / 1000, offset_diff_us / 1000);

                // Process paired timestamps for offset update
                esp_err_t paired_err = time_sync_update_from_paired_timestamps(t1, t2, t3, t4);
                if (paired_err != ESP_OK) {
                    ESP_LOGW(TAG, "[SYNC_FB] Paired timestamp update failed: %d", paired_err);
                }
            }

            // Get SERVER's motor epoch for independent calculation
            uint64_t server_epoch_us;
            uint32_t server_cycle_ms;
            esp_err_t err = time_sync_get_motor_epoch(&server_epoch_us, &server_cycle_ms);

            if (err == ESP_OK && server_cycle_ms > 0) {
                // AD045: Pattern-broadcast SYNC_FB - derive cycles from SERVER's time domain
                //
                // IMPORTANT: CLIENT's actual_time_us is already converted to SERVER's time domain
                // via time_sync_get_time() which does: CLIENT_local - clock_offset
                // So we can directly compare with server_epoch_us (SERVER's local time)
                //
                // CLIENT activates at: epoch + (N * cycle_period) + half_cycle
                // Where N is the cycle number in SERVER's time domain
                uint64_t half_cycle_us = ((uint64_t)server_cycle_ms * 1000ULL) / 2;
                uint64_t cycle_period_us = (uint64_t)server_cycle_ms * 1000ULL;

                // Derive which cycle this activation belongs to from timestamp
                // Both actual_time_us and server_epoch_us should be in SERVER's time domain
                int64_t time_since_epoch_us = (int64_t)report->actual_time_us - (int64_t)server_epoch_us;
                int64_t time_adjusted_us = time_since_epoch_us - (int64_t)half_cycle_us;

                // Calculate cycle number (round to nearest cycle)
                int64_t cycles_elapsed = (time_adjusted_us + (int64_t)(cycle_period_us / 2)) / (int64_t)cycle_period_us;
                if (cycles_elapsed < 0) cycles_elapsed = 0;  // Safety: no negative cycles

                // Calculate expected activation for this cycle
                uint64_t expected_client_us = server_epoch_us +
                                              ((uint64_t)cycles_elapsed * cycle_period_us) +
                                              half_cycle_us;

                // SERVER's independent drift measurement (in SERVER time domain)
                int64_t server_measured_drift_us = (int64_t)report->actual_time_us - (int64_t)expected_client_us;
                int32_t server_measured_drift_ms = (int32_t)(server_measured_drift_us / 1000);

                // Calculate elapsed time from epoch for diagnostics
                int64_t elapsed_since_epoch_ms = time_since_epoch_us / 1000;

                // Enhanced diagnostic format:
                // [SYNC_FB] cycle=N/M err=Xms elapsed=Yms
                // N = CLIENT's counter, M = derived from timestamp, err = timing error, elapsed = time since epoch
                ESP_LOGI(TAG, "[SYNC_FB] cycle=%lu/%ld err=%ldms elapsed=%ldms",
                         (unsigned long)report->cycle_number,
                         (long)cycles_elapsed,
                         (long)server_measured_drift_ms,
                         (long)elapsed_since_epoch_ms);

                // Warn if cycle counter diverges significantly (indicates epoch or time domain issue)
                int32_t cycle_divergence = (int32_t)report->cycle_number - (int32_t)cycles_elapsed;
                if (cycle_divergence > 5 || cycle_divergence < -5) {
                    ESP_LOGW(TAG, "[SYNC_FB] Cycle divergence=%ld (epoch may be stale or time domain mismatch)",
                             (long)cycle_divergence);
                }

                // Warn if significant timing error
                if (server_measured_drift_ms > 50 || server_measured_drift_ms < -50) {
                    ESP_LOGW(TAG, "[SYNC_FB] ALERT: Timing error > 50ms!");
                }
            } else {
                // Fallback: Just log CLIENT's self-reported error
                ESP_LOGI(TAG, "[SYNC_FB] cycle=%lu client_err=%ldms (no server epoch)",
                         (unsigned long)report->cycle_number,
                         (long)report->client_error_ms);
            }
            break;
        }

        case SYNC_MSG_REVERSE_PROBE: {
            // IEEE 1588 bidirectional path measurement: SERVER handles CLIENT-initiated probe
            // This enables detection of path asymmetry between SERVER→CLIENT and CLIENT→SERVER
            //
            // Flow (reverse direction from normal beacon):
            // 1. CLIENT sends REVERSE_PROBE with T1' (client send time)
            // 2. SERVER receives here, records T2' immediately
            // 3. SERVER sends REVERSE_PROBE_RESPONSE with T2', T3' just before BLE send
            // 4. CLIENT receives, records T4', calculates reverse offset
            //
            // By comparing forward offset (from beacons) with reverse offset (from probes),
            // we can detect systematic BLE path asymmetry causing the ~36ms systematic error
            const reverse_probe_t *probe = &coord->payload.reverse_probe;

            // T2': SERVER's local time when probe received - record IMMEDIATELY
            uint64_t t2_prime_us = esp_timer_get_time();

            ESP_LOGI(TAG, "[REV_PROBE] seq=%lu T1'=%llu T2'=%llu",
                     (unsigned long)probe->probe_sequence,
                     (unsigned long long)probe->client_send_time_us,
                     (unsigned long long)t2_prime_us);

            // Send response with T2', T3' - T3' recorded right before BLE send
            uint64_t t3_prime_us = esp_timer_get_time();  // T3': As close to BLE send as possible

            coordination_message_t response = {
                .type = SYNC_MSG_REVERSE_PROBE_RESPONSE,
                .timestamp_ms = (uint32_t)(t3_prime_us / 1000),
                .payload.reverse_probe_response = {
                    .client_send_time_us = probe->client_send_time_us,  // Echo T1'
                    .server_recv_time_us = t2_prime_us,                 // T2'
                    .server_send_time_us = t3_prime_us,                 // T3'
                    .probe_sequence = probe->probe_sequence             // Echo sequence
                }
            };

            esp_err_t err = ble_send_coordination_message(&response);
            if (err != ESP_OK) {
                ESP_LOGW(TAG, "[REV_PROBE] Failed to send response: %s", esp_err_to_name(err));
            }
            break;
        }

        case SYNC_MSG_REVERSE_PROBE_RESPONSE: {
            // CLIENT receives SERVER's response to reverse probe
            // Calculate reverse offset and compare with forward offset
            const reverse_probe_response_t *resp = &coord->payload.reverse_probe_response;

            // T4': CLIENT's local time when response received - record IMMEDIATELY
            uint64_t t4_prime_us = esp_timer_get_time();

            int64_t t1 = (int64_t)resp->client_send_time_us;   // T1': CLIENT send
            int64_t t2 = (int64_t)resp->server_recv_time_us;   // T2': SERVER recv
            int64_t t3 = (int64_t)resp->server_send_time_us;   // T3': SERVER send
            int64_t t4 = (int64_t)t4_prime_us;                 // T4': CLIENT recv

            // NTP offset formula (reverse direction):
            // reverse_offset = [(T2'-T1') - (T4'-T3')] / 2
            //
            // BUG FIX: This gives SERVER_clock - CLIENT_clock (OPPOSITE of forward!)
            // Proof: T2'-T1' = (SERVER+d) - CLIENT = SERVER-CLIENT+d
            //        T4'-T3' = CLIENT - (SERVER+d) = CLIENT-SERVER-d
            //        reverse = [(S-C+d) - (C-S-d)]/2 = [2(S-C)+2d]/2 ≈ SERVER-CLIENT
            //
            // Forward offset (EMA) = CLIENT_clock - SERVER_clock
            // Reverse offset = SERVER_clock - CLIENT_clock (opposite sign convention!)
            int64_t raw_fwd_prime_us = t2 - t1;  // T2' - T1' (contaminated by offset)
            int64_t raw_rev_prime_us = t4 - t3;  // T4' - T3' (contaminated by offset)
            int64_t reverse_offset_us = (raw_fwd_prime_us - raw_rev_prime_us) / 2;
            int64_t reverse_delay_us = (raw_fwd_prime_us + raw_rev_prime_us) / 2;

            // Get current forward offset (from EMA filter)
            // Convention: forward_offset = CLIENT_clock - SERVER_clock
            int64_t forward_offset_us = 0;
            time_sync_get_clock_offset(&forward_offset_us);

            // Path asymmetry = forward_offset + reverse_offset (NOT minus!)
            // Since they have opposite sign conventions, they should sum to ~0 if symmetric.
            // forward = C-S, reverse = S-C, so: (C-S) + (S-C) = 0 if no asymmetry
            // Non-zero sum indicates systematic BLE path difference (asymmetric delays)
            int64_t asymmetry_us = forward_offset_us + reverse_offset_us;

            // Calculate RTT for quality filtering
            int64_t rtt_us = reverse_delay_us * 2;

            ESP_LOGI(TAG, "[REV_PROBE_RESP] seq=%lu fwd=%lldms rev=%lldms asym=%lldms RTT=%lldms",
                     (unsigned long)resp->probe_sequence,
                     forward_offset_us / 1000,
                     reverse_offset_us / 1000,
                     asymmetry_us / 1000,
                     rtt_us / 1000);

            // Update asymmetry correction (v0.6.97)
            // This applies to time_sync_get_time() for CLIENT motor timing
            esp_err_t asym_err = time_sync_update_asymmetry(asymmetry_us, rtt_us);
            if (asym_err == ESP_OK) {
                // Get updated asymmetry for logging
                int64_t filtered_asym_us = 0;
                bool asym_valid = false;
                time_sync_get_asymmetry(&filtered_asym_us, &asym_valid);
                ESP_LOGI(TAG, "[ASYM] Updated EMA=%lldms correction=%lldms valid=%d",
                         filtered_asym_us / 1000,
                         filtered_asym_us / 2000,
                         asym_valid);
            }

            // Large asymmetry indicates systematic BLE path difference
            // ~50ms asymmetry at 0.5Hz = 2.5% phase error
            if (asymmetry_us > 30000 || asymmetry_us < -30000) {  // > 30ms
                ESP_LOGW(TAG, "[REV_PROBE] PATH ASYMMETRY: %lldms!", asymmetry_us / 1000);
            }
            break;
        }

        case SYNC_MSG_FIRMWARE_VERSION: {
            // AD040: Peer sent their firmware version - compare and respond
            const firmware_version_t *peer_version = &coord->payload.firmware_version;
            firmware_version_t local_version = firmware_get_version();

            // Build peer version string for BLE characteristic (AD032)
            char version_str[32];
            snprintf(version_str, sizeof(version_str), "v%d.%d.%d (%s)",
                     peer_version->major, peer_version->minor, peer_version->patch,
                     peer_version->build_date);

            // Store for BLE characteristic reads
            ble_set_peer_firmware_version(version_str);

            // Compare versions using firmware_version.h helper
            bool match = firmware_versions_match(local_version, *peer_version);
            ble_set_firmware_version_match(match);

            if (match) {
                ESP_LOGI(TAG, "AD040: Peer firmware: %s %s (MATCH)",
                         version_str, peer_version->build_time);
                // Show green success pattern (same as pairing success)
                status_led_pattern(STATUS_PATTERN_PAIRING_SUCCESS);
            } else {
                // Show full timestamps so user can see WHY it's a mismatch
                // (version numbers may match but build timestamps differ)
                ESP_LOGW(TAG, "AD040: FIRMWARE MISMATCH!");
                ESP_LOGW(TAG, "  Peer:  v%d.%d.%d built %s %s",
                         peer_version->major, peer_version->minor, peer_version->patch,
                         peer_version->build_date, peer_version->build_time);
                ESP_LOGW(TAG, "  Local: v%d.%d.%d built %s %s",
                         local_version.major, local_version.minor, local_version.patch,
                         local_version.build_date, local_version.build_time);
                // Show yellow warning pattern - connection allowed but versions differ
                status_led_pattern(STATUS_PATTERN_VERSION_MISMATCH);
            }
            // Note: Do NOT respond here - both sides send once after GATT discovery.
            // Responding would cause an infinite ping-pong loop.
            break;
        }

        case SYNC_MSG_HARDWARE_INFO: {
            // AD048: Peer sent their hardware info (silicon revision, FTM capability)
            const hardware_info_t *peer_hw = &coord->payload.hardware_info;

            // Store for BLE characteristic reads
            ble_set_peer_hardware_info(peer_hw->info_str);

            ESP_LOGI(TAG, "AD048: Peer hardware: %s", peer_hw->info_str);

            // Note: Do NOT respond here - both sides send once after GATT discovery.
            break;
        }

        case SYNC_MSG_WIFI_MAC: {
            // AD048: Peer sent their WiFi MAC for ESP-NOW transport
            const wifi_mac_payload_t *wifi_mac = &coord->payload.wifi_mac;

            ESP_LOGI(TAG, "AD048: Received peer WiFi MAC: %02X:%02X:%02X:%02X:%02X:%02X",
                     wifi_mac->mac[0], wifi_mac->mac[1], wifi_mac->mac[2],
                     wifi_mac->mac[3], wifi_mac->mac[4], wifi_mac->mac[5]);

            // Store peer MAC for key derivation
            memcpy(peer_wifi_mac, wifi_mac->mac, 6);
            peer_wifi_mac_received = true;

            // SERVER: Initiate key exchange after receiving CLIENT's MAC
            // CLIENT: Just store MAC; key exchange message will follow
            if (TIME_SYNC_IS_SERVER()) {
                ESP_LOGI(TAG, "AD048: SERVER initiating key exchange");

                // Get our own WiFi MAC
                uint8_t server_mac[6];
                esp_err_t err = espnow_transport_get_local_mac(server_mac);
                if (err != ESP_OK) {
                    ESP_LOGE(TAG, "AD048: Failed to get local WiFi MAC: %s", esp_err_to_name(err));
                    break;
                }

                // Generate random nonce using hardware RNG
                esp_fill_random(session_nonce, sizeof(session_nonce));

                // Derive LMK using HKDF: server_mac || client_mac || nonce
                uint8_t lmk[ESPNOW_KEY_SIZE];
                err = espnow_transport_derive_session_key(
                    server_mac,           // SERVER MAC (initiator)
                    peer_wifi_mac,        // CLIENT MAC (responder)
                    session_nonce,
                    lmk
                );
                if (err != ESP_OK) {
                    ESP_LOGE(TAG, "AD048: HKDF key derivation failed: %s", esp_err_to_name(err));
                    break;
                }

                // Configure encrypted ESP-NOW peer
                err = espnow_transport_set_peer_encrypted(peer_wifi_mac, lmk);
                if (err == ESP_OK) {
                    ESP_LOGI(TAG, "AD048: SERVER configured encrypted ESP-NOW peer");
                    espnow_key_exchange_complete = true;
                } else {
                    ESP_LOGE(TAG, "AD048: Failed to configure encrypted peer: %s", esp_err_to_name(err));
                    break;
                }

                // Send key exchange to CLIENT
                err = ble_send_espnow_key_exchange(session_nonce, server_mac);
                if (err == ESP_OK) {
                    ESP_LOGI(TAG, "AD048: Key exchange sent to CLIENT");
                } else {
                    ESP_LOGE(TAG, "AD048: Failed to send key exchange: %s", esp_err_to_name(err));
                }

                // Clear sensitive data
                memset(lmk, 0, sizeof(lmk));
            } else {
                // CLIENT: Configure unencrypted peer for now, will upgrade after key exchange
                // (This allows BLE fallback if key exchange fails)
                esp_err_t err = espnow_transport_set_peer(wifi_mac->mac);
                if (err == ESP_OK) {
                    ESP_LOGI(TAG, "AD048: CLIENT configured ESP-NOW peer (awaiting key exchange)");
                } else {
                    ESP_LOGE(TAG, "AD048: Failed to configure ESP-NOW peer: %s", esp_err_to_name(err));
                }
            }
            break;
        }

        case SYNC_MSG_ESPNOW_KEY_EXCHANGE: {
            // AD048: CLIENT receives key exchange from SERVER
            // Derive LMK using same inputs as SERVER (HKDF is deterministic)
            const espnow_key_exchange_payload_t *key_ex = &coord->payload.espnow_key;

            ESP_LOGI(TAG, "AD048: Received ESP-NOW key exchange from SERVER");
            ESP_LOGI(TAG, "  Nonce: %02X%02X%02X%02X%02X%02X%02X%02X",
                     key_ex->nonce[0], key_ex->nonce[1], key_ex->nonce[2], key_ex->nonce[3],
                     key_ex->nonce[4], key_ex->nonce[5], key_ex->nonce[6], key_ex->nonce[7]);
            ESP_LOGI(TAG, "  Server MAC: %02X:%02X:%02X:%02X:%02X:%02X",
                     key_ex->server_mac[0], key_ex->server_mac[1], key_ex->server_mac[2],
                     key_ex->server_mac[3], key_ex->server_mac[4], key_ex->server_mac[5]);

            // Get our own WiFi MAC (CLIENT MAC)
            uint8_t client_mac[6];
            esp_err_t err = espnow_transport_get_local_mac(client_mac);
            if (err != ESP_OK) {
                ESP_LOGE(TAG, "AD048: Failed to get local WiFi MAC: %s", esp_err_to_name(err));
                break;
            }

            // Derive LMK using HKDF: server_mac || client_mac || nonce
            // Must use SAME order as SERVER for identical keys!
            uint8_t lmk[ESPNOW_KEY_SIZE];
            err = espnow_transport_derive_session_key(
                key_ex->server_mac,   // SERVER MAC (initiator) - from message
                client_mac,           // CLIENT MAC (responder) - local
                key_ex->nonce,        // Nonce - from message
                lmk
            );
            if (err != ESP_OK) {
                ESP_LOGE(TAG, "AD048: HKDF key derivation failed: %s", esp_err_to_name(err));
                break;
            }

            // Verify server MAC matches what we received earlier via WIFI_MAC message
            if (peer_wifi_mac_received) {
                if (memcmp(key_ex->server_mac, peer_wifi_mac, 6) != 0) {
                    ESP_LOGW(TAG, "AD048: Server MAC mismatch (possible MITM attempt)");
                    // Continue anyway - peer_wifi_mac was from same connection
                }
            }

            // Upgrade ESP-NOW peer to encrypted
            err = espnow_transport_set_peer_encrypted(key_ex->server_mac, lmk);
            if (err == ESP_OK) {
                ESP_LOGI(TAG, "AD048: CLIENT configured encrypted ESP-NOW peer");
                espnow_key_exchange_complete = true;
            } else {
                ESP_LOGE(TAG, "AD048: Failed to configure encrypted peer: %s", esp_err_to_name(err));
            }

            // Clear sensitive data
            memset(lmk, 0, sizeof(lmk));
            break;
        }

        case SYNC_MSG_PHASE_QUERY: {
            // Phase Query: Peer is asking "how long until your next ACTIVE state?"
            // Calculate our time to next active and respond
            uint64_t epoch_us = 0;
            uint32_t cycle_ms = 0;
            esp_err_t err = time_sync_get_motor_epoch(&epoch_us, &cycle_ms);

            if (err != ESP_OK || epoch_us == 0 || cycle_ms == 0) {
                ESP_LOGW(TAG, "Phase Query: Phase query received but motor epoch not set");
                break;
            }

            uint64_t now_us = esp_timer_get_time();
            uint64_t elapsed_us = now_us - epoch_us;
            uint32_t cycle_us = cycle_ms * 1000;

            // Position within current cycle (0 to cycle_us)
            uint32_t pos_in_cycle_us = (uint32_t)(elapsed_us % cycle_us);
            uint32_t pos_in_cycle_ms = pos_in_cycle_us / 1000;

            // For phase query, we report time until OUR next ACTIVE
            // SERVER (phase 0): ACTIVE at cycle start (pos=0)
            // CLIENT (phase 180): ACTIVE at half-cycle (pos=cycle/2)
            uint32_t half_cycle_ms = cycle_ms / 2;
            uint32_t ms_to_active = 0;
            uint8_t current_state = 0;  // 0=INACTIVE, 1=ACTIVE
            uint32_t current_cycle = (uint32_t)(elapsed_us / cycle_us);

            // Simplified: Assume we're ACTIVE for first 25% of our phase
            // SERVER: ACTIVE 0-25%, INACTIVE 25-100%
            // CLIENT: INACTIVE 0-50%, ACTIVE 50-75%, INACTIVE 75-100%
            uint32_t duty_ms = cycle_ms / 4;  // 25% duty cycle assumption

            if (ble_get_peer_role() == PEER_ROLE_CLIENT) {
                // We are SERVER (peer is CLIENT) - our ACTIVE is at cycle start
                if (pos_in_cycle_ms < duty_ms) {
                    current_state = 1;  // ACTIVE now
                    ms_to_active = 0;
                } else {
                    current_state = 0;  // INACTIVE
                    ms_to_active = cycle_ms - pos_in_cycle_ms;
                }
            } else {
                // We are CLIENT (peer is SERVER) - our ACTIVE is at half-cycle
                if (pos_in_cycle_ms >= half_cycle_ms && pos_in_cycle_ms < half_cycle_ms + duty_ms) {
                    current_state = 1;  // ACTIVE now
                    ms_to_active = 0;
                } else if (pos_in_cycle_ms < half_cycle_ms) {
                    current_state = 0;  // INACTIVE, waiting for half-cycle
                    ms_to_active = half_cycle_ms - pos_in_cycle_ms;
                } else {
                    current_state = 0;  // INACTIVE, waiting for next cycle
                    ms_to_active = cycle_ms - pos_in_cycle_ms + half_cycle_ms;
                }
            }

            // Send response
            coordination_message_t response = {
                .type = SYNC_MSG_PHASE_RESPONSE,
                .timestamp_ms = (uint32_t)(now_us / 1000),
            };
            response.payload.phase_response.ms_to_active = ms_to_active;
            response.payload.phase_response.pos_in_cycle_ms = pos_in_cycle_ms;  // Direct position for comparison
            response.payload.phase_response.current_cycle = current_cycle;
            response.payload.phase_response.current_state = current_state;

            ble_send_coordination_message(&response);
            ESP_LOGD(TAG, "Phase Query: Response: pos=%lu ms, ms_to_active=%lu, state=%s",
                     (unsigned long)pos_in_cycle_ms, (unsigned long)ms_to_active,
                     current_state ? "ACTIVE" : "INACTIVE");
            break;
        }

        case SYNC_MSG_PHASE_RESPONSE: {
            // Phase Query: Peer responded with their time-to-active
            // LOGGING ONLY - compare to our time-to-inactive for phase error detection
            const phase_response_t *pr = &coord->payload.phase_response;

            uint64_t epoch_us = 0;
            uint32_t cycle_ms = 0;
            esp_err_t err = time_sync_get_motor_epoch(&epoch_us, &cycle_ms);

            if (err != ESP_OK || epoch_us == 0 || cycle_ms == 0) {
                ESP_LOGW(TAG, "Phase Query: Phase response received but motor epoch not set");
                break;
            }

            uint64_t now_us = esp_timer_get_time();
            uint64_t elapsed_us = now_us - epoch_us;
            uint32_t cycle_us = cycle_ms * 1000;
            uint32_t pos_in_cycle_us = (uint32_t)(elapsed_us % cycle_us);
            uint32_t pos_in_cycle_ms = pos_in_cycle_us / 1000;
            uint32_t half_cycle_ms = cycle_ms / 2;

            // Phase error calculation using direct position comparison
            // For perfect antiphase: peer_pos should be (my_pos + half_cycle) % cycle
            //
            // Protocol now includes pos_in_cycle_ms directly - no more deriving from ms_to_active!
            // This eliminates the semantic confusion that caused ±1500ms "errors".
            uint32_t peer_pos_ms = pr->pos_in_cycle_ms;

            // Expected peer position for perfect antiphase
            uint32_t expected_peer_pos = (pos_in_cycle_ms + half_cycle_ms) % cycle_ms;

            // Phase error (normalize to ±half_cycle range)
            int32_t phase_error_ms = (int32_t)peer_pos_ms - (int32_t)expected_peer_pos;
            if (phase_error_ms > (int32_t)half_cycle_ms) {
                phase_error_ms -= (int32_t)cycle_ms;
            }
            if (phase_error_ms < -(int32_t)half_cycle_ms) {
                phase_error_ms += (int32_t)cycle_ms;
            }

            // Log for diagnostic purposes (no correction applied yet)
            // Note: BLE latency (~50-70ms) will always show some error
            if (abs(phase_error_ms) > 100) {
                ESP_LOGW(TAG, "Phase Query: PHASE ERROR: my_pos=%lu ms, peer_pos=%lu ms (expected %lu), error=%+ld ms",
                         (unsigned long)pos_in_cycle_ms, (unsigned long)peer_pos_ms,
                         (unsigned long)expected_peer_pos, (long)phase_error_ms);
            } else {
                ESP_LOGI(TAG, "Phase Query: Phase OK: my_pos=%lu ms, peer_pos=%lu ms, error=%+ld ms (BLE latency)",
                         (unsigned long)pos_in_cycle_ms, (unsigned long)peer_pos_ms, (long)phase_error_ms);
            }

            ESP_LOGD(TAG, "Phase Query: Peer state=%s, ms_to_active=%lu",
                     pr->current_state ? "ACTIVE" : "INACTIVE",
                     (unsigned long)pr->ms_to_active);
            break;
        }

        case SYNC_MSG_PATTERN_CHANGE: {
            // AD047: Handle pattern selection sync from SERVER (peer relay)
            const pattern_sync_t *ps = &coord->payload.pattern_sync;

            ESP_LOGI(TAG, "Pattern sync received: cmd=%d, start_time=%llu",
                     ps->control_cmd, (unsigned long long)ps->start_time_us);

            // Execute pattern command (same logic as BLE Pattern Control)
            if (ps->control_cmd == 0) {
                // Stop pattern
                pattern_stop();
                ESP_LOGI(TAG, "Pattern stopped via sync");
            } else if (ps->control_cmd == 1) {
                // Start current pattern
                pattern_start(ps->start_time_us);
                ESP_LOGI(TAG, "Pattern started via sync");
            } else if (ps->control_cmd >= 2 && ps->control_cmd <= 4) {
                // Load and start builtin pattern (BLE cmd 2→enum 1, cmd 3→enum 2, etc.)
                builtin_pattern_id_t pattern_id = (builtin_pattern_id_t)(ps->control_cmd - 1);
                if (pattern_id < BUILTIN_PATTERN_COUNT) {
                    pattern_load_builtin(pattern_id);
                    pattern_start(ps->start_time_us);
                    ESP_LOGI(TAG, "Pattern %d loaded and started via sync", pattern_id);
                } else {
                    ESP_LOGW(TAG, "Invalid pattern ID: %d", pattern_id);
                }
            } else {
                ESP_LOGW(TAG, "Unknown pattern control command: %d", ps->control_cmd);
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

        // Note: BEMF logging now uses independent 60s timer in motor_task (not beacon-triggered)
    }

    // Phase Query: CLIENT sends periodic phase queries for diagnostic logging
    // Send every 10 seconds when motor is running (motor_epoch_valid)
    static uint32_t phase_query_counter = 0;
    phase_query_counter++;

    if (phase_query_counter >= 10) {  // Every 10 seconds
        phase_query_counter = 0;

        // Only send if we're CLIENT, peer is connected, and motor is running
        if (!TIME_SYNC_IS_SERVER() && ble_is_peer_connected()) {
            uint64_t epoch_us = 0;
            uint32_t cycle_ms = 0;
            if (time_sync_get_motor_epoch(&epoch_us, &cycle_ms) == ESP_OK && epoch_us != 0) {
                // Send phase query to SERVER
                coordination_message_t query = {
                    .type = SYNC_MSG_PHASE_QUERY,
                    .timestamp_ms = (uint32_t)(esp_timer_get_time() / 1000),
                };
                esp_err_t qerr = ble_send_coordination_message(&query);
                if (qerr == ESP_OK) {
                    ESP_LOGD(TAG, "Phase Query: Phase query sent to SERVER");
                }
            }
        }
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
