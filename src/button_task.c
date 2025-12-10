/**
 * @file button_task.c
 * @brief Button Task Implementation - 8-state button handler with hold detection
 *
 * Implements button state machine with debouncing, mode cycling, BLE re-enable,
 * emergency shutdown with purple countdown, and optional NVS factory reset.
 * Extracted from single_device_ble_gatt_test.c reference implementation.
 *
 * @date November 11, 2025
 * @author Claude Code (Anthropic)
 */

#include "button_task.h"
#include "motor_task.h"
#include "ble_manager.h"
#include "battery_monitor.h"
#include "nvs_manager.h"
#include "led_control.h"
#include "status_led.h"
#include "power_manager.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "esp_sleep.h"
#include "esp_task_wdt.h"
#include "driver/gpio.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "BTN_TASK";

// ============================================================================
// MODE CYCLING
// ============================================================================

/**
 * @brief Get next mode in cycle
 * @param current Current mode
 * @return Next mode in sequence
 *
 * Cycle: MODE_05HZ_25 → MODE_1HZ_25 → MODE_15HZ_25 → MODE_2HZ_25 → MODE_CUSTOM → [repeat]
 */
static mode_t get_next_mode(mode_t current) {
    switch (current) {
        case MODE_05HZ_25:  return MODE_1HZ_25;
        case MODE_1HZ_25:   return MODE_15HZ_25;
        case MODE_15HZ_25:  return MODE_2HZ_25;
        case MODE_2HZ_25:   return MODE_CUSTOM;
        case MODE_CUSTOM:   return MODE_05HZ_25;
        default:            return MODE_05HZ_25;
    }
}

// ============================================================================
// BUTTON TASK IMPLEMENTATION
// ============================================================================

void button_task(void *pvParameters) {
    button_state_t state = BTN_STATE_IDLE;
    uint32_t press_start_time = 0;
    uint32_t boot_time = (uint32_t)(esp_timer_get_time() / 1000);  // Boot time in ms
    bool watchdog_subscribed = false;

    ESP_LOGI(TAG, "Button task started");

    // Configure button GPIO (input with pull-up)
    gpio_config_t btn_cfg = {
        .pin_bit_mask = (1ULL << GPIO_BUTTON),
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_ENABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE
    };
    esp_err_t ret = gpio_config(&btn_cfg);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to configure GPIO_BUTTON: %s", esp_err_to_name(ret));
        vTaskDelete(NULL);
        return;
    }

    // Initialize status LED module
    ret = status_led_init();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to initialize status LED: %s", esp_err_to_name(ret));
        vTaskDelete(NULL);
        return;
    }

    while (state != BTN_STATE_SHUTDOWN_SENT) {
        uint32_t now = (uint32_t)(esp_timer_get_time() / 1000);  // Current time in ms
        int button_level = gpio_get_level(GPIO_BUTTON);  // 0 = pressed, 1 = released

        switch (state) {
            case BTN_STATE_IDLE: {
                // Check for messages from motor task (non-blocking)
                task_message_t motor_msg;
                if (xQueueReceive(motor_to_button_queue, &motor_msg, 0) == pdTRUE) {
                    if (motor_msg.type == MSG_SESSION_TIMEOUT) {
                        ESP_LOGI(TAG, "Session timeout received from motor_task");
                        ESP_LOGI(TAG, "State: IDLE → SHUTDOWN (non-abortable session timeout)");

                        // Issue #4 Fix: Send shutdown messages to local tasks
                        // (Session timeout originated from motor_task, so it already knows)
                        task_message_t ble_msg = {
                            .type = MSG_EMERGENCY_SHUTDOWN,
                            .data = {.new_mode = 0}
                        };
                        if (xQueueSend(button_to_ble_queue, &ble_msg, pdMS_TO_TICKS(100)) == pdTRUE) {
                            ESP_LOGI(TAG, "Shutdown message sent to ble_task");
                        } else {
                            ESP_LOGW(TAG, "Failed to send shutdown message to ble_task");
                        }

                        // Skip countdown for session timeout - go directly to shutdown
                        state = BTN_STATE_SHUTDOWN;
                        break;  // Exit IDLE state immediately

                    } else if (motor_msg.type == MSG_EMERGENCY_SHUTDOWN) {
                        ESP_LOGI(TAG, "Peer-initiated shutdown received from motor_task");
                        ESP_LOGI(TAG, "State: IDLE → SHUTDOWN (peer requested shutdown)");

                        // Issue #4 Fix: Send shutdown messages to local tasks
                        // Peer shutdown goes through time_sync_task → button_task, so local tasks don't know yet
                        task_message_t local_motor_msg = {
                            .type = MSG_EMERGENCY_SHUTDOWN,
                            .data = {.new_mode = 0}
                        };
                        if (xQueueSend(button_to_motor_queue, &local_motor_msg, pdMS_TO_TICKS(100)) == pdTRUE) {
                            ESP_LOGI(TAG, "Shutdown message sent to motor_task");
                        } else {
                            ESP_LOGW(TAG, "Failed to send shutdown message to motor_task");
                        }

                        task_message_t ble_msg = {
                            .type = MSG_EMERGENCY_SHUTDOWN,
                            .data = {.new_mode = 0}
                        };
                        if (xQueueSend(button_to_ble_queue, &ble_msg, pdMS_TO_TICKS(100)) == pdTRUE) {
                            ESP_LOGI(TAG, "Shutdown message sent to ble_task");
                        } else {
                            ESP_LOGW(TAG, "Failed to send shutdown message to ble_task");
                        }

                        // Skip countdown for peer shutdown - go directly to shutdown
                        state = BTN_STATE_SHUTDOWN;
                        break;  // Exit IDLE state immediately
                    }
                }

                // Wait for button press (GPIO low)
                if (button_level == 0) {
                    ESP_LOGI(TAG, "Button pressed");
                    press_start_time = now;
                    ESP_LOGI(TAG, "State: IDLE → DEBOUNCE");
                    state = BTN_STATE_DEBOUNCE;
                }
                break;
            }

            case BTN_STATE_DEBOUNCE: {
                uint32_t elapsed = now - press_start_time;

                if (button_level == 1) {
                    // Button released during debounce
                    ESP_LOGI(TAG, "Button released during debounce (false trigger)");
                    ESP_LOGI(TAG, "State: DEBOUNCE → IDLE");
                    state = BTN_STATE_IDLE;
                } else if (elapsed >= BUTTON_DEBOUNCE_MS) {
                    // Debounce complete and still pressed
                    ESP_LOGI(TAG, "Button press confirmed (debounced)");
                    ESP_LOGI(TAG, "State: DEBOUNCE → PRESSED");
                    state = BTN_STATE_PRESSED;
                }
                break;
            }

            case BTN_STATE_PRESSED: {
                uint32_t elapsed = now - press_start_time;

                if (button_level == 1) {
                    // Button released before 1s hold threshold
                    ESP_LOGI(TAG, "Button released after %u ms (short press)", elapsed);

                    // AD045: Calculate next mode based on armed mode (if present) to allow rapid cycling
                    // If mode change already armed, use that as base; otherwise use current mode
                    // This allows: Press 1: 0→1, Press 2: 1→2, Press 3: 2→3 (rapid queue)
                    mode_t base_mode = mode_change_armed ? armed_new_mode : motor_get_current_mode();
                    mode_t next_mode = get_next_mode(base_mode);

                    ESP_LOGI(TAG, "Mode change: %d → %d%s", base_mode, next_mode,
                             mode_change_armed ? " (override armed)" : "");

                    // Quick blink for mode change feedback
                    status_led_on();

                    task_message_t msg = {
                        .type = MSG_MODE_CHANGE,
                        .data = {.new_mode = next_mode}
                    };

                    if (xQueueSend(button_to_motor_queue, &msg, 0) != pdTRUE) {
                        ESP_LOGW(TAG, "Failed to send mode change message (queue full)");
                    }

                    // Notify BLE clients of mode change (mobile app sync)
                    ble_update_mode(next_mode);

                    // Phase 3: Sync mode change to peer device
                    if (ble_is_peer_connected()) {
                        coordination_message_t coord_msg = {
                            .type = SYNC_MSG_MODE_CHANGE,
                            .timestamp_ms = (uint32_t)(esp_timer_get_time() / 1000ULL),
                            .payload = {.mode = next_mode}
                        };
                        esp_err_t err = ble_send_coordination_message(&coord_msg);
                        if (err == ESP_OK) {
                            ESP_LOGI(TAG, "Mode change synced to peer: MODE_%d", next_mode);
                        } else {
                            ESP_LOGW(TAG, "Failed to sync mode change to peer: %s", esp_err_to_name(err));
                        }
                    }

                    // Bug #25 FIX: Turn off status LED after mode change feedback
                    // The status_led_on() above was for brief visual feedback,
                    // but GPIO15 has no auto-off mechanism - must explicitly turn off.
                    status_led_off();

                    ESP_LOGI(TAG, "State: PRESSED → IDLE");
                    state = BTN_STATE_IDLE;
                } else if (elapsed >= BUTTON_BLE_HOLD_MIN_MS) {
                    // Button held ≥1s, transition to hold detection
                    ESP_LOGI(TAG, "Button held ≥1s, entering hold detection");
                    ESP_LOGI(TAG, "State: PRESSED → HOLD_DETECT");
                    status_led_pattern(STATUS_PATTERN_BUTTON_HOLD);  // Turn LED ON for hold
                    state = BTN_STATE_HOLD_DETECT;
                }
                break;
            }

            case BTN_STATE_HOLD_DETECT: {
                uint32_t elapsed = now - press_start_time;

                if (button_level == 1) {
                    // Button released between 1-2s
                    ESP_LOGI(TAG, "Button released after %u ms (1-2s hold)", elapsed);
                    status_led_off();  // Turn LED OFF when button released

                    if (elapsed >= BUTTON_BLE_HOLD_MIN_MS && elapsed < BUTTON_BLE_HOLD_MAX_MS) {
                        ESP_LOGI(TAG, "BLE re-enable triggered (1-2s hold)");
                        // Brief LED pulse for BLE re-enable feedback (non-blocking)
                        status_led_on();

                        // Phase 3: Check if this is CLIENT requesting SERVER to advertise
                        peer_role_t role = ble_get_peer_role();
                        if (role == PEER_ROLE_CLIENT && ble_is_peer_connected()) {
                            // CLIENT: Send coordination message to SERVER
                            ESP_LOGI(TAG, "CLIENT requesting SERVER to start advertising");
                            coordination_message_t coord_msg = {
                                .type = SYNC_MSG_START_ADVERTISING,
                                .timestamp_ms = (uint32_t)(esp_timer_get_time() / 1000ULL),
                                .payload = {0}  // No payload
                            };
                            esp_err_t err = ble_send_coordination_message(&coord_msg);
                            if (err != ESP_OK) {
                                ESP_LOGW(TAG, "Failed to send advertising request: %s", esp_err_to_name(err));
                            }
                        } else {
                            // SERVER or standalone: Re-enable local advertising
                            task_message_t msg = {
                                .type = MSG_BLE_REENABLE,
                                .data = {.new_mode = 0}
                            };

                            if (xQueueSend(button_to_ble_queue, &msg, 0) != pdTRUE) {
                                ESP_LOGW(TAG, "Failed to send BLE re-enable message (queue full)");
                            }
                        }

                        // BUG #18 FIX: Turn off LED after BLE re-enable feedback
                        // The status_led_on() at line 207 was for brief feedback,
                        // but we never turned it off. This left GPIO15 stuck ON.
                        status_led_off();
                    } else {
                        ESP_LOGI(TAG, "Released outside 1-2s window, no BLE action");
                    }

                    ESP_LOGI(TAG, "State: HOLD_DETECT → IDLE");
                    state = BTN_STATE_IDLE;
                } else if (elapsed >= BUTTON_SHUTDOWN_MS) {
                    // Button held ≥5s, send shutdown messages immediately
                    ESP_LOGI(TAG, "Button held ≥5s, emergency shutdown triggered");

                    // Phase 3: Send coordinated shutdown to peer device FIRST (before shutting down BLE!)
                    if (ble_is_peer_connected()) {
                        coordination_message_t coord_msg = {
                            .type = SYNC_MSG_SHUTDOWN,
                            .timestamp_ms = (uint32_t)(esp_timer_get_time() / 1000ULL),
                            .payload = {0}  // No payload for shutdown
                        };
                        esp_err_t err = ble_send_coordination_message(&coord_msg);
                        if (err == ESP_OK) {
                            ESP_LOGI(TAG, "Coordinated shutdown sent to peer");
                        } else {
                            ESP_LOGW(TAG, "Failed to send coordinated shutdown: %s", esp_err_to_name(err));
                        }

                        // Wait for BLE transmission to complete before shutting down BLE stack
                        // BLE write-without-response typically takes 10-50ms; 200ms provides safety margin
                        vTaskDelay(pdMS_TO_TICKS(200));
                    }

                    // Now shut down local tasks (after peer notification sent)
                    // Send shutdown message to motor task (stop motor NOW)
                    task_message_t motor_msg = {
                        .type = MSG_EMERGENCY_SHUTDOWN,
                        .data = {.new_mode = 0}
                    };
                    if (xQueueSend(button_to_motor_queue, &motor_msg, pdMS_TO_TICKS(100)) == pdTRUE) {
                        ESP_LOGI(TAG, "Shutdown message sent to motor_task");
                    } else {
                        ESP_LOGW(TAG, "Failed to send shutdown message to motor_task");
                    }

                    // Send shutdown message to BLE task
                    task_message_t ble_msg = {
                        .type = MSG_EMERGENCY_SHUTDOWN,
                        .data = {.new_mode = 0}
                    };
                    if (xQueueSend(button_to_ble_queue, &ble_msg, pdMS_TO_TICKS(100)) == pdTRUE) {
                        ESP_LOGI(TAG, "Shutdown message sent to ble_task");
                    } else {
                        ESP_LOGW(TAG, "Failed to send shutdown message to ble_task");
                    }

                    ESP_LOGI(TAG, "State: HOLD_DETECT → SHUTDOWN_HOLD");
                    state = BTN_STATE_SHUTDOWN_HOLD;
                }
                // No delay here - will use common delay at end of loop
                break;
            }

            case BTN_STATE_SHUTDOWN_HOLD: {
                // Button held ≥5s, blink purple LED at 5Hz while waiting for release
                // This matches reference implementation: while (gpio_get_level(GPIO_BUTTON) == 0)
                uint32_t elapsed = now - press_start_time;

                // Subscribe to watchdog for purple blink loop (must feed during blink)
                if (!watchdog_subscribed) {
                    ret = esp_task_wdt_add(NULL);
                    if (ret == ESP_OK) {
                        ESP_LOGI(TAG, "Subscribed to watchdog for purple blink");
                        watchdog_subscribed = true;
                    } else {
                        ESP_LOGW(TAG, "Failed to subscribe to watchdog: %s", esp_err_to_name(ret));
                    }
                }

                // Check for NVS clear (15s hold within 30s boot window)
                if (elapsed >= BUTTON_NVS_CLEAR_MS) {
                    uint32_t uptime = now - boot_time;
                    if (uptime < BUTTON_NVS_CLEAR_WINDOW_MS) {
                        ESP_LOGI(TAG, "Button held ≥15s within 30s window, NVS clear triggered");
                        ESP_LOGI(TAG, "Factory reset: Clearing NVS settings");

                        // Clear purple LED before NVS operations
                        led_clear();

                        ret = nvs_clear_all();
                        if (ret == ESP_OK) {
                            ESP_LOGI(TAG, "NVS cleared successfully");
                            // Flash LED to indicate success
                            status_led_pattern(STATUS_PATTERN_NVS_RESET);
                        } else {
                            ESP_LOGE(TAG, "NVS clear failed: %s", esp_err_to_name(ret));
                        }

                        // Wait for button release
                        ESP_LOGI(TAG, "Waiting for button release after NVS clear");
                        while (gpio_get_level(GPIO_BUTTON) == 0) {
                            // Feed watchdog while waiting
                            if (watchdog_subscribed) {
                                esp_task_wdt_reset();
                            }
                            vTaskDelay(pdMS_TO_TICKS(100));
                        }

                        // After factory reset, shut down the device
                        // Next boot will start with fresh default settings
                        ESP_LOGI(TAG, "NVS cleared - proceeding to shutdown for clean restart");
                        ESP_LOGI(TAG, "State: SHUTDOWN_HOLD → SHUTDOWN");
                        state = BTN_STATE_SHUTDOWN;
                        break;
                    }
                }

                // Purple blink at 5Hz (200ms toggle) while button held
                // Same as reference: while (gpio_get_level(GPIO_BUTTON) == 0)
                static bool led_state = false;
                if (led_state) {
                    led_set_rgb(128, 0, 128, 20);  // Purple at 20% brightness
                } else {
                    led_clear();
                }
                led_state = !led_state;

                // Feed watchdog (200ms blink interval < 2000ms timeout)
                if (watchdog_subscribed) {
                    esp_task_wdt_reset();
                }

                // Delay for 5Hz blink rate (200ms per toggle)
                vTaskDelay(pdMS_TO_TICKS(200));

                // Re-read button state after delay
                button_level = gpio_get_level(GPIO_BUTTON);

                if (button_level == 1) {
                    // Button released - clear LED and proceed to shutdown
                    ESP_LOGI(TAG, "Button released after purple blink, proceeding to shutdown");
                    led_clear();
                    ESP_LOGI(TAG, "State: SHUTDOWN_HOLD → SHUTDOWN");
                    state = BTN_STATE_SHUTDOWN;
                }
                break;
            }

            case BTN_STATE_COUNTDOWN: {
                // Subscribe to watchdog for countdown (must feed during purple blink loop)
                if (!watchdog_subscribed) {
                    ret = esp_task_wdt_add(NULL);
                    if (ret == ESP_OK) {
                        ESP_LOGI(TAG, "Subscribed to watchdog for countdown");
                        watchdog_subscribed = true;
                    } else {
                        ESP_LOGW(TAG, "Failed to subscribe to watchdog: %s", esp_err_to_name(ret));
                    }
                }

                // Purple WS2812B LED countdown (5 cycles)
                // Uses WS2812B LEDs at 20% brightness (same as reference implementation)
                bool countdown_aborted = false;
                for (int i = 0; i < COUNTDOWN_CYCLES; i++) {
                    // LED ON (purple at 20% brightness)
                    led_set_rgb(128, 0, 128, 20);
                    vTaskDelay(pdMS_TO_TICKS(COUNTDOWN_BLINK_MS));

                    // Feed watchdog (200ms blink interval < 2000ms timeout)
                    if (watchdog_subscribed) {
                        esp_task_wdt_reset();
                    }

                    // Check for button press (abort)
                    if (gpio_get_level(GPIO_BUTTON) == 0) {
                        ESP_LOGI(TAG, "Button pressed during countdown - ABORT SHUTDOWN");
                        led_clear();
                        countdown_aborted = true;
                        break;
                    }

                    // LED OFF
                    led_clear();
                    vTaskDelay(pdMS_TO_TICKS(COUNTDOWN_BLINK_MS));

                    // Feed watchdog again
                    if (watchdog_subscribed) {
                        esp_task_wdt_reset();
                    }

                    // Check for button press (abort)
                    if (gpio_get_level(GPIO_BUTTON) == 0) {
                        ESP_LOGI(TAG, "Button pressed during countdown - ABORT SHUTDOWN");
                        countdown_aborted = true;
                        break;
                    }
                }

                if (countdown_aborted) {
                    ESP_LOGI(TAG, "Shutdown aborted, returning to idle");
                    ESP_LOGI(TAG, "State: COUNTDOWN → IDLE");
                    state = BTN_STATE_IDLE;
                } else {
                    ESP_LOGI(TAG, "Countdown complete, proceeding to shutdown");
                    ESP_LOGI(TAG, "State: COUNTDOWN → SHUTDOWN");
                    state = BTN_STATE_SHUTDOWN;
                }
                break;
            }

            case BTN_STATE_SHUTDOWN: {
                ESP_LOGI(TAG, "Executing emergency shutdown sequence");

                // NOTE: Shutdown messages already sent at 5s hold detection
                // This state handles final cleanup and deep sleep entry

                // Give tasks time to finish shutdown (they received messages earlier)
                vTaskDelay(pdMS_TO_TICKS(500));

                // Check if settings need to be saved
                if (ble_settings_dirty()) {
                    ESP_LOGI(TAG, "Saving BLE settings to NVS before shutdown");
                    ret = ble_save_settings_to_nvs();
                    if (ret == ESP_OK) {
                        ESP_LOGI(TAG, "BLE settings saved successfully");
                    } else {
                        ESP_LOGE(TAG, "Failed to save BLE settings: %s", esp_err_to_name(ret));
                    }
                }

                // Perform low battery warning if needed (optional visual feedback)
                int raw_mv = 0;
                float battery_v = 0.0f;
                int battery_pct = 0;
                ret = battery_read_voltage(&raw_mv, &battery_v, &battery_pct);
                if (ret == ESP_OK && battery_v < LVO_WARNING_VOLTAGE && battery_v >= LVO_NO_BATTERY_THRESHOLD) {
                    ESP_LOGI(TAG, "Battery low (%.2fV), flashing warning", battery_v);
                    battery_low_battery_warning();
                }

                // Configure wake source (button press)
                ESP_LOGI(TAG, "Configuring EXT1 wake on GPIO%d (button)", GPIO_BUTTON);
                ret = esp_sleep_enable_ext1_wakeup((1ULL << GPIO_BUTTON), ESP_EXT1_WAKEUP_ANY_LOW);
                if (ret != ESP_OK) {
                    ESP_LOGE(TAG, "Failed to configure wake source: %s", esp_err_to_name(ret));
                }

                // Unsubscribe from watchdog before sleep
                if (watchdog_subscribed) {
                    esp_task_wdt_delete(NULL);
                    ESP_LOGI(TAG, "Unsubscribed from watchdog");
                    watchdog_subscribed = false;
                }

                // Enter deep sleep (never returns)
                ESP_LOGI(TAG, "Entering deep sleep...");
                vTaskDelay(pdMS_TO_TICKS(100));  // Allow log to flush
                esp_deep_sleep_start();

                // Never reached
                ESP_LOGI(TAG, "State: SHUTDOWN → SHUTDOWN_SENT");
                state = BTN_STATE_SHUTDOWN_SENT;
                break;
            }

            case BTN_STATE_SHUTDOWN_SENT: {
                // Terminal state (should never be reached after deep sleep)
                ESP_LOGI(TAG, "Button task in terminal state (should be in deep sleep)");
                break;
            }
        }

        // Fixed 10ms sample rate (consistent button checking for all states)
        // Matches reference implementation: vTaskDelay(pdMS_TO_TICKS(BUTTON_SAMPLE_MS))
        vTaskDelay(pdMS_TO_TICKS(10));
    }

    // Cleanup (should never reach here after deep sleep)
    if (watchdog_subscribed) {
        esp_task_wdt_delete(NULL);
        ESP_LOGI(TAG, "Unsubscribed from watchdog");
    }

    ESP_LOGI(TAG, "Button task stopping");
    vTaskDelete(NULL);
}
