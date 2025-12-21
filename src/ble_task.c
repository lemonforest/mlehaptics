/**
 * @file ble_task.c
 * @brief BLE Task Implementation - 5-state advertising lifecycle manager
 *
 * Implements BLE advertising timeout enforcement, pairing lifecycle management,
 * and message queue handling.
 * Extracted from single_device_ble_gatt_test.c reference implementation.
 *
 * @date November 15, 2025 (Phase 1b.3: Added pairing state)
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

                        // Purpose: Restart advertising for mobile app connection after 5-min timeout
                        // DO NOT reset pairing window or roles - preserves session continuity with peer
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

                // Bug #34 fix: Handle peer connection that occurred before ble_task reached PAIRING state
                // This happens when CLIENT receives incoming connection during startup (before IDLE→ADVERTISING)
                // CLIENT's ble_manager handles connection in GAP callback, but ble_task misses MSG_PAIRING_COMPLETE
                static bool idle_peer_handled = false;
                if (!idle_peer_handled && ble_is_peer_connected()) {
                    // Peer already connected - check if pairing workflow complete
                    if (ble_firmware_version_exchanged() && ble_firmware_versions_match()) {
                        ESP_LOGI(TAG, "Peer already connected during IDLE (late ble_task start)");

                        // Send MSG_PAIRING_COMPLETE to motor_task
                        extern QueueHandle_t ble_to_motor_queue;
                        if (ble_to_motor_queue != NULL) {
                            task_message_t success_msg = {
                                .type = MSG_PAIRING_COMPLETE,
                                .data = {.new_mode = 0}
                            };
                            if (xQueueSend(ble_to_motor_queue, &success_msg, pdMS_TO_TICKS(100)) == pdTRUE) {
                                ESP_LOGI(TAG, "Pairing complete message sent to motor_task (from IDLE)");
                                idle_peer_handled = true;

                                // Stop advertising if still active (peer pairing complete)
                                if (ble_is_advertising()) {
                                    // Only SERVER should continue advertising for mobile app access
                                    if (ble_get_peer_role() != PEER_ROLE_SERVER) {
                                        ble_stop_advertising();
                                        ESP_LOGI(TAG, "CLIENT: Advertising stopped (peer connected from IDLE)");
                                    }
                                }

                                // Transition to ADVERTISING state (handles app connections, timeouts)
                                ESP_LOGI(TAG, "State: IDLE → ADVERTISING (peer already paired)");
                                state = BLE_STATE_ADVERTISING;
                            } else {
                                ESP_LOGW(TAG, "Failed to send pairing complete (from IDLE)");
                            }
                        }
                    } else {
                        // Peer connected but firmware version not yet exchanged
                        // This is normal during startup - wait for time_sync_task to exchange versions
                        ESP_LOGD(TAG, "Peer connected but waiting for firmware version exchange...");
                    }
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

                // Check for pairing started (Phase 1b.3)
                // CRITICAL FIX: Check NVS for bonded peers before starting pairing window
                // If bonded peer exists, skip pairing window for silent reconnection
                static bool pairing_window_started = false;
                if (!pairing_window_started) {
                    // Check if bonded peer exists in NVS storage
                    bool bonded_peer_exists = ble_check_bonded_peer_exists();

                    if (bonded_peer_exists) {
                        // Bonded peer found - skip pairing window and allow silent reconnection
                        ESP_LOGI(TAG, "Bonded peer found in NVS, skipping pairing window (silent reconnection)");
                        pairing_window_started = true;  // Prevent repeated checks

                        // Send immediate MSG_PAIRING_COMPLETE to motor_task (bonded reconnection mode)
                        extern QueueHandle_t ble_to_motor_queue;
                        if (ble_to_motor_queue != NULL) {
                            task_message_t msg = {
                                .type = MSG_PAIRING_COMPLETE,
                                .data = {.new_mode = 0}
                            };
                            if (xQueueSend(ble_to_motor_queue, &msg, pdMS_TO_TICKS(100)) == pdTRUE) {
                                ESP_LOGI(TAG, "Motor task notified: can continue session (bonded peer mode)");
                            } else {
                                ESP_LOGW(TAG, "Failed to send MSG_PAIRING_COMPLETE for bonded peer");
                            }
                        }

                        // Stay in ADVERTISING state, wait for bonded peer reconnection
                        // NO status LED patterns, NO 30-second countdown
                        break;
                    }

                    // No bonded peer found - proceed with first-time pairing
                    pairing_window_started = true;
                    ESP_LOGI(TAG, "Starting 30-second peer pairing window (first-time pairing)");
                    status_led_pattern(STATUS_PATTERN_PAIRING_WAIT);  // Solid ON during pairing window
                    ESP_LOGI(TAG, "State: ADVERTISING → PAIRING (window started)");
                    state = BLE_STATE_PAIRING;
                    break;
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
                        } else {
                            // Log progress every minute (only if NOT timing out)
                            if ((elapsed % 60000) < 200) {  // Within 200ms of minute boundary
                                ESP_LOGI(TAG, "Advertising for %u seconds (timeout at %u sec)",
                                         elapsed / 1000, BLE_ADV_TIMEOUT_MS / 1000);
                            }
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

            case BLE_STATE_PAIRING: {
                // Phase 1b.3: Wait for pairing to complete with 30-second timeout
                static int64_t pairing_start_time = 0;
                const uint32_t PAIRING_TIMEOUT_MS = 30000;  // 30 seconds (JPL compliant)

                // Initialize pairing start time on first entry
                if (pairing_start_time == 0) {
                    pairing_start_time = esp_timer_get_time() / 1000;  // Convert to milliseconds
                    ESP_LOGI(TAG, "Pairing started, 30-second timeout active");
                }

                // Check for messages (500ms timeout for LED pattern pulsing)
                if (xQueueReceive(button_to_ble_queue, &msg, pdMS_TO_TICKS(500)) == pdTRUE) {
                    if (msg.type == MSG_EMERGENCY_SHUTDOWN) {
                        ESP_LOGI(TAG, "Emergency shutdown during pairing");
                        pairing_start_time = 0;  // Reset timer
                        ESP_LOGI(TAG, "State: PAIRING → SHUTDOWN");
                        state = BLE_STATE_SHUTDOWN;
                        break;
                    }
                }

                // Display pairing progress pattern (pulsing 1Hz)
                // Pattern: 500ms ON, 500ms OFF (implemented in status_led.c)
                status_led_pattern(STATUS_PATTERN_PAIRING_PROGRESS);

                // Check if PEER pairing completed successfully
                // Pairing is complete when peer is connected AND encryption finished
                // AND firmware version exchange completed with matching versions (AD040)
                if (ble_is_peer_connected() && !ble_is_pairing() &&
                    ble_firmware_version_exchanged() && ble_firmware_versions_match()) {
                    pairing_start_time = 0;  // Reset timer
                    ESP_LOGI(TAG, "Peer pairing completed successfully (versions match)");
                    status_led_pattern(STATUS_PATTERN_PAIRING_SUCCESS);  // Green 3× blink
                    vTaskDelay(pdMS_TO_TICKS(1500));  // Wait for LED pattern to complete

                    // BUG FIX: Explicitly turn off GPIO15 before motor takes WS2812B ownership
                    // Ensures status LED is not left ON when motor_task disables status_led patterns
                    status_led_off();
                    ESP_LOGI(TAG, "GPIO15 (status LED) turned OFF before motor ownership transfer");

                    // Send success message to motor_task (BUG FIX: was missing)
                    extern QueueHandle_t ble_to_motor_queue;
                    if (ble_to_motor_queue != NULL) {
                        task_message_t success_msg = {
                            .type = MSG_PAIRING_COMPLETE,
                            .data = {.new_mode = 0}
                        };
                        if (xQueueSend(ble_to_motor_queue, &success_msg, pdMS_TO_TICKS(100)) == pdTRUE) {
                            ESP_LOGI(TAG, "Pairing complete message sent to motor_task");
                        } else {
                            ESP_LOGW(TAG, "Failed to send pairing complete message");
                        }
                    }

                    // BUG FIX: Stop scanning for additional peers (peer connection complete)
                    ESP_LOGI(TAG, "Stopping peer discovery scan (peer connected)");
                    ble_stop_scanning();

                    // BUG #26 FIX: Restart advertising for SERVER device (mobile app access)
                    // This gives ~4s between peer connection and advertising restart
                    // (prevents timing race with NimBLE controller that caused BLE_HS_ECONTROLLER errors)
                    // Only SERVER devices advertise after peer pairing (CLIENT does not)
                    if (ble_get_peer_role() == PEER_ROLE_SERVER) {
                        if (!ble_is_advertising()) {
                            ble_start_advertising();
                            ESP_LOGI(TAG, "SERVER: Advertising restarted for mobile app access (5 min timeout)");
                        }
                    } else {
                        ESP_LOGI(TAG, "CLIENT: No advertising (peer connection only)");
                    }

                    ESP_LOGI(TAG, "State: PAIRING → ADVERTISING");
                    state = BLE_STATE_ADVERTISING;
                    break;
                }

                // Check pairing timeout (30 seconds JPL compliant)
                int64_t current_time = esp_timer_get_time() / 1000;
                uint32_t elapsed = (uint32_t)(current_time - pairing_start_time);

                if (elapsed >= PAIRING_TIMEOUT_MS) {
                    ESP_LOGW(TAG, "Pairing timeout after %u seconds", PAIRING_TIMEOUT_MS / 1000);
                    pairing_start_time = 0;  // Reset timer

                    // Bug #45: Close pairing window to prevent late peer connections
                    // This ensures devices powered on >30s apart do NOT pair
                    ble_close_pairing_window();

                    status_led_pattern(STATUS_PATTERN_PAIRING_FAILED);  // Red 3× blink
                    vTaskDelay(pdMS_TO_TICKS(1500));  // Wait for LED pattern to complete

                    // BUG FIX: Explicitly turn off GPIO15 before motor takes WS2812B ownership
                    status_led_off();
                    ESP_LOGI(TAG, "GPIO15 (status LED) turned OFF after pairing timeout");

                    // Send timeout failure message to motor_task (Phase 1b.3)
                    extern QueueHandle_t ble_to_motor_queue;
                    if (ble_to_motor_queue != NULL) {
                        task_message_t timeout_msg = {
                            .type = MSG_PAIRING_FAILED,
                            .data = {.new_mode = 0}
                        };
                        if (xQueueSend(ble_to_motor_queue, &timeout_msg, pdMS_TO_TICKS(100)) == pdTRUE) {
                            ESP_LOGI(TAG, "Pairing timeout message sent to motor_task");
                        } else {
                            ESP_LOGW(TAG, "Failed to send pairing timeout message");
                        }
                    }

                    // Disconnect if still connected
                    if (ble_is_connected()) {
                        uint16_t conn_handle = ble_get_pairing_conn_handle();
                        if (conn_handle != 0xFFFF) {  // BLE_HS_CONN_HANDLE_NONE
                            ESP_LOGI(TAG, "Disconnecting pairing connection (handle=%d)", conn_handle);
                            ble_gap_terminate(conn_handle, BLE_ERR_REM_USER_CONN_TERM);
                            vTaskDelay(pdMS_TO_TICKS(100));  // Wait for disconnect
                        }
                    }

                    // BUG FIX: Stop scanning for peers and restart advertising with Config UUID
                    // Single-device mode: advertise Config UUID for PWA/mobile app discovery
                    ESP_LOGI(TAG, "Single-device mode: stopping peer scan, advertising Config UUID for apps");
                    ble_stop_scanning();  // Stop peer discovery scanning
                    ble_stop_advertising();  // Stop Bilateral UUID advertising
                    vTaskDelay(pdMS_TO_TICKS(100));  // Brief delay for cleanup
                    ble_start_advertising();  // Restart with Config UUID (30s elapsed)
                    ESP_LOGI(TAG, "State: PAIRING → ADVERTISING (Config UUID for PWA/app)");
                    state = BLE_STATE_ADVERTISING;
                    break;
                }

                // Log progress every 5 seconds
                if ((elapsed % 5000) < 600) {  // Within 600ms of 5-second boundary
                    ESP_LOGI(TAG, "Pairing in progress: %u/%u seconds",
                             elapsed / 1000, PAIRING_TIMEOUT_MS / 1000);
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

                // Check if ALL connections lost (both mobile app AND peer)
                // BUG FIX: ble_is_connected() only checks mobile app, not peer!
                // Must stay in CONNECTED state if peer is connected (even without mobile app)
                if (!ble_is_connected() && !ble_is_peer_connected()) {
                    ESP_LOGI(TAG, "All connections lost (app and peer)");

                    // JPL compliance: Wait for disconnect handler to complete advertising restart
                    // Measured disconnect handler advertising restart time: ~80ms
                    // Use 150ms delay for safety margin (deterministic wait)
                    vTaskDelay(pdMS_TO_TICKS(150));

                    // GAP event handler automatically restarts advertising
                    if (ble_is_advertising()) {
                        // Phase 1b.3: Only scan for peers during initial pairing window
                        // Don't scan if:
                        // - Past 30s (single-device mode)
                        // - Peer already connected (dual-device mode)
                        // - Peer already bonded (no need to re-pair)
                        uint32_t elapsed_ms = (uint32_t)(esp_timer_get_time() / 1000);
                        bool should_scan = (elapsed_ms < 30000) &&
                                          !ble_is_peer_connected() &&
                                          !ble_check_bonded_peer_exists();

                        if (should_scan) {
                            ble_start_scanning();
                            ESP_LOGI(TAG, "Advertising restarted after app disconnect (within 30s - scanning for peer)");
                        } else {
                            if (ble_is_peer_connected()) {
                                ESP_LOGI(TAG, "Advertising restarted after app disconnect (peer connected - no scanning)");
                            } else {
                                ESP_LOGI(TAG, "Advertising restarted after app disconnect (single-device mode - no scanning)");
                            }
                        }
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
