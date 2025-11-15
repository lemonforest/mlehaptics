/**
 * @file ble_task.c
 * @brief BLE Task Implementation - 4-state advertising lifecycle manager
 *
 * Implements BLE advertising timeout enforcement and message queue handling.
 * Extracted from single_device_ble_gatt_test.c reference implementation.
 *
 * @date November 11, 2025
 * @author Claude Code (Anthropic)
 */

#include "ble_task.h"
#include "ble_manager.h"
#include "status_led.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "host/ble_gap.h"
#include "host/ble_hs.h"

static const char *TAG = "BLE_TASK";

// ============================================================================
// BLE TASK IMPLEMENTATION
// ============================================================================

void ble_task(void *pvParameters) {
    task_message_t msg;
    ble_state_t state = BLE_STATE_IDLE;
    uint32_t idle_log_counter = 0;  // For periodic state logging

    ESP_LOGI(TAG, "BLE task started");
    ESP_LOGI(TAG, "Initial state: IDLE, advertising=%s, connected=%s",
             ble_is_advertising() ? "YES" : "NO",
             ble_is_connected() ? "YES" : "NO");

    while (state != BLE_STATE_SHUTDOWN) {
        switch (state) {
            case BLE_STATE_IDLE: {
                // Check if advertising was auto-started by ble_on_sync() callback
                // This happens when NimBLE synchronizes during initialization
                // Don't auto-detect if already connected to peer (Phase 1b)
                if (ble_is_advertising() && !ble_is_peer_connected()) {
                    ble_start_scanning();
                    ESP_LOGI(TAG, "State: IDLE → ADVERTISING (auto-detected, scanning started)");
                    state = BLE_STATE_ADVERTISING;
                    break;
                }

                // Check for messages (1s timeout for responsiveness)
                if (xQueueReceive(button_to_ble_queue, &msg, pdMS_TO_TICKS(1000)) == pdTRUE) {
                    if (msg.type == MSG_BLE_REENABLE) {
                        ESP_LOGI(TAG, "BLE re-enable requested (button hold 1-2s)");
                        ble_start_advertising();

                        // Transition based on result
                        if (ble_is_advertising()) {
                            // Phase 1a: Start scanning for peer devices
                            ble_start_scanning();
                            ESP_LOGI(TAG, "State: IDLE → ADVERTISING (scanning for peer)");
                            state = BLE_STATE_ADVERTISING;
                        } else {
                            ESP_LOGW(TAG, "Failed to start advertising, staying in IDLE");
                        }
                    } else if (msg.type == MSG_EMERGENCY_SHUTDOWN) {
                        ESP_LOGI(TAG, "Emergency shutdown requested (button hold 5s)");
                        ESP_LOGI(TAG, "State: IDLE → SHUTDOWN");
                        state = BLE_STATE_SHUTDOWN;
                        break;
                    }
                }

                // Check if connection established (possible if advertising was ongoing)
                if (ble_is_connected()) {
                    ESP_LOGI(TAG, "Client connected (from IDLE)");
                    status_led_pattern(STATUS_PATTERN_BLE_CONNECTED);  // 5× blink for connection
                    ESP_LOGI(TAG, "State: IDLE → CONNECTED");
                    state = BLE_STATE_CONNECTED;
                }

                // Periodic state logging (every 30 seconds)
                idle_log_counter++;
                if (idle_log_counter >= 30) {
                    ESP_LOGI(TAG, "State: IDLE (advertising=%s, connected=%s)",
                             ble_is_advertising() ? "YES" : "NO",
                             ble_is_connected() ? "YES" : "NO");
                    idle_log_counter = 0;
                }
                break;
            }

            case BLE_STATE_ADVERTISING: {
                // Check for messages (100ms timeout for fast response)
                if (xQueueReceive(button_to_ble_queue, &msg, pdMS_TO_TICKS(100)) == pdTRUE) {
                    if (msg.type == MSG_EMERGENCY_SHUTDOWN) {
                        ESP_LOGI(TAG, "Emergency shutdown during advertising");
                        ble_stop_scanning();  // Phase 1a: Stop scanning
                        ble_stop_advertising();
                        ESP_LOGI(TAG, "State: ADVERTISING → SHUTDOWN");
                        state = BLE_STATE_SHUTDOWN;
                        break;
                    } else if (msg.type == MSG_BLE_REENABLE) {
                        // Restart advertising from 0 (reset timeout)
                        ESP_LOGI(TAG, "BLE re-enable requested while advertising, restarting");
                        ble_stop_scanning();  // Phase 1a: Stop scanning before restart
                        ble_stop_advertising();
                        vTaskDelay(pdMS_TO_TICKS(100));  // Brief delay
                        ble_start_advertising();
                        ble_start_scanning();  // Phase 1a: Restart scanning
                        ESP_LOGI(TAG, "Advertising restarted (timeout reset, scanning resumed)");
                    }
                }

                // Check for client connection (set by GAP event handler)
                if (ble_is_connected()) {
                    ESP_LOGI(TAG, "Client connected");
                    ble_stop_scanning();  // Phase 1a: Stop scanning when connected
                    status_led_pattern(STATUS_PATTERN_BLE_CONNECTED);  // 5× blink for connection
                    ESP_LOGI(TAG, "State: ADVERTISING → CONNECTED");
                    state = BLE_STATE_CONNECTED;
                    break;
                }

                // Check advertising timeout (5 minutes = 300000ms)
                // Skip timeout if mobile app is connected (Configuration Service active)
                if (ble_is_advertising()) {
                    // Don't timeout if mobile app is using Configuration Service
                    if (ble_is_connected()) {
                        // Mobile app connected, no timeout needed
                        // (Advertising should have been stopped when app connected,
                        //  but if it's still running, don't timeout it)
                        vTaskDelay(pdMS_TO_TICKS(100));
                    } else {
                        uint32_t elapsed = ble_get_advertising_elapsed_ms();

                        if (elapsed >= BLE_ADV_TIMEOUT_MS) {
                            ESP_LOGI(TAG, "Advertising timeout (5 minutes)");
                            ble_stop_scanning();  // Phase 1a: Stop scanning on timeout
                            ble_stop_advertising();
                            ESP_LOGI(TAG, "State: ADVERTISING → IDLE");
                            state = BLE_STATE_IDLE;
                        }

                        // Log progress every minute
                        if ((elapsed % 60000) < 200) {  // Within 200ms of minute boundary
                            ESP_LOGI(TAG, "Advertising for %u seconds (timeout at %u sec)",
                                     elapsed / 1000, BLE_ADV_TIMEOUT_MS / 1000);
                        }
                    }
                } else {
                    // Advertising stopped externally, return to idle
                    ESP_LOGW(TAG, "Advertising stopped externally");
                    ESP_LOGI(TAG, "State: ADVERTISING → IDLE");
                    state = BLE_STATE_IDLE;
                }
                break;
            }

            case BLE_STATE_CONNECTED: {
                // Check for messages (100ms timeout for fast response)
                if (xQueueReceive(button_to_ble_queue, &msg, pdMS_TO_TICKS(100)) == pdTRUE) {
                    if (msg.type == MSG_EMERGENCY_SHUTDOWN) {
                        ESP_LOGI(TAG, "Emergency shutdown during connection");

                        // CRITICAL FIX (Bug #15): Gracefully disconnect BLE connections before shutdown
                        // Check which connections are active and terminate them
                        if (ble_is_peer_connected()) {
                            uint16_t peer_handle = ble_get_peer_conn_handle();
                            if (peer_handle != 0xFFFF) {  // BLE_HS_CONN_HANDLE_NONE
                                ESP_LOGI(TAG, "Disconnecting peer connection (handle=%d)", peer_handle);
                                ble_gap_terminate(peer_handle, BLE_ERR_REM_USER_CONN_TERM);
                            }
                        }

                        if (ble_is_connected()) {
                            uint16_t app_handle = ble_get_app_conn_handle();
                            if (app_handle != 0xFFFF) {  // BLE_HS_CONN_HANDLE_NONE
                                ESP_LOGI(TAG, "Disconnecting mobile app connection (handle=%d)", app_handle);
                                ble_gap_terminate(app_handle, BLE_ERR_REM_USER_CONN_TERM);
                            }
                        }

                        // Small delay to allow disconnect events to process
                        vTaskDelay(pdMS_TO_TICKS(100));

                        ESP_LOGI(TAG, "State: CONNECTED → SHUTDOWN");
                        state = BLE_STATE_SHUTDOWN;
                        break;
                    } else if (msg.type == MSG_BLE_REENABLE) {
                        // Already connected, no action needed
                        ESP_LOGI(TAG, "BLE re-enable requested while connected (ignored, already active)");
                    }
                }

                // Check if client disconnected (set by GAP event handler)
                if (!ble_is_connected()) {
                    ESP_LOGI(TAG, "Client disconnected");

                    // JPL compliance: Wait for disconnect handler to complete advertising restart
                    // Measured disconnect handler advertising restart time: ~80ms
                    // Use 150ms delay for safety margin (deterministic wait)
                    vTaskDelay(pdMS_TO_TICKS(150));

                    // GAP event handler automatically restarts advertising
                    if (ble_is_advertising()) {
                        // Phase 1a: Resume scanning for peer after disconnect
                        ble_start_scanning();
                        ESP_LOGI(TAG, "Advertising restarted after disconnect (scanning for peer)");
                        ESP_LOGI(TAG, "State: CONNECTED → ADVERTISING");
                        state = BLE_STATE_ADVERTISING;
                    } else {
                        ESP_LOGW(TAG, "Advertising did not restart after disconnect");
                        ESP_LOGI(TAG, "State: CONNECTED → IDLE");
                        state = BLE_STATE_IDLE;
                    }
                }
                break;
            }

            case BLE_STATE_SHUTDOWN: {
                // Loop exit handled by while condition
                ESP_LOGI(TAG, "BLE task shutting down");
                break;
            }
        }
    }

    ESP_LOGI(TAG, "BLE task stopping");
    vTaskDelete(NULL);
}
