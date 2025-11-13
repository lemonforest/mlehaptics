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
                // Check for messages (1s timeout for responsiveness)
                if (xQueueReceive(button_to_ble_queue, &msg, pdMS_TO_TICKS(1000)) == pdTRUE) {
                    if (msg.type == MSG_BLE_REENABLE) {
                        ESP_LOGI(TAG, "BLE re-enable requested (button hold 1-2s)");
                        ble_start_advertising();

                        // Transition based on result
                        if (ble_is_advertising()) {
                            ESP_LOGI(TAG, "State: IDLE → ADVERTISING");
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
                // Check for shutdown message (100ms timeout for fast response)
                if (xQueueReceive(button_to_ble_queue, &msg, pdMS_TO_TICKS(100)) == pdTRUE) {
                    if (msg.type == MSG_EMERGENCY_SHUTDOWN) {
                        ESP_LOGI(TAG, "Emergency shutdown during advertising");
                        ble_stop_advertising();
                        ESP_LOGI(TAG, "State: ADVERTISING → SHUTDOWN");
                        state = BLE_STATE_SHUTDOWN;
                        break;
                    }
                }

                // Check for client connection (set by GAP event handler)
                if (ble_is_connected()) {
                    ESP_LOGI(TAG, "Client connected");
                    status_led_pattern(STATUS_PATTERN_BLE_CONNECTED);  // 5× blink for connection
                    ESP_LOGI(TAG, "State: ADVERTISING → CONNECTED");
                    state = BLE_STATE_CONNECTED;
                    break;
                }

                // Check advertising timeout (5 minutes = 300000ms)
                if (ble_is_advertising()) {
                    uint32_t elapsed = ble_get_advertising_elapsed_ms();

                    if (elapsed >= BLE_ADV_TIMEOUT_MS) {
                        ESP_LOGI(TAG, "Advertising timeout (5 minutes)");
                        ble_stop_advertising();
                        ESP_LOGI(TAG, "State: ADVERTISING → IDLE");
                        state = BLE_STATE_IDLE;
                    }

                    // Log progress every minute
                    if ((elapsed % 60000) < 200) {  // Within 200ms of minute boundary
                        ESP_LOGI(TAG, "Advertising for %u seconds (timeout at %u sec)",
                                 elapsed / 1000, BLE_ADV_TIMEOUT_MS / 1000);
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
                // Check for shutdown message (100ms timeout for fast response)
                if (xQueueReceive(button_to_ble_queue, &msg, pdMS_TO_TICKS(100)) == pdTRUE) {
                    if (msg.type == MSG_EMERGENCY_SHUTDOWN) {
                        ESP_LOGI(TAG, "Emergency shutdown during connection");
                        // Client disconnect is handled by GAP event handler
                        ESP_LOGI(TAG, "State: CONNECTED → SHUTDOWN");
                        state = BLE_STATE_SHUTDOWN;
                        break;
                    }
                }

                // Check if client disconnected (set by GAP event handler)
                if (!ble_is_connected()) {
                    ESP_LOGI(TAG, "Client disconnected");

                    // GAP event handler automatically restarts advertising
                    if (ble_is_advertising()) {
                        ESP_LOGI(TAG, "Auto-restarting advertising after disconnect");
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
