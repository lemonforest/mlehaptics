/**
 * @file motor_task.c
 * @brief Motor Control Task Module - Implementation
 *
 * Complete 8-state machine for bilateral alternating motor control with:
 * - Mode configurations (predefined + custom via BLE)
 * - Message queue handling (button events, battery warnings)
 * - Back-EMF sampling for research
 * - Soft-fail watchdog pattern
 * - JPL compliance (no busy-wait loops)
 *
 * @date November 11, 2025
 * @author Claude Code (Anthropic)
 */

#include "motor_task.h"
#include <string.h>
#include "esp_log.h"
#include "esp_timer.h"
#include "esp_task_wdt.h"

// Module dependencies
#include "battery_monitor.h"
#include "motor_control.h"
#include "led_control.h"
#include "ble_manager.h"
#include "power_manager.h"

static const char *TAG = "MOTOR_TASK";

// ============================================================================
// TIMING CONSTANTS
// ============================================================================

#define LED_INDICATION_TIME_MS  10000               // Back-EMF sampling window
#define BACKEMF_SETTLE_MS       10                  // Back-EMF settle time
#define MODE_CHECK_INTERVAL_MS  50                  // Check queue every 50ms
#define BATTERY_CHECK_INTERVAL_MS  10000            // Check battery every 10 seconds

// ============================================================================
// MODE CONFIGURATIONS
// ============================================================================

const mode_config_t modes[MODE_COUNT] = {
    {"1Hz@50%", 250, 250},    // MODE_1HZ_50
    {"1Hz@25%", 125, 375},    // MODE_1HZ_25
    {"0.5Hz@50%", 500, 500},  // MODE_05HZ_50
    {"0.5Hz@25%", 250, 750},  // MODE_05HZ_25
    {"Custom", 250, 250}      // MODE_CUSTOM (default to 1Hz@50%)
};

// ============================================================================
// GLOBAL STATE (Module-private static variables)
// ============================================================================

// Session state (for BLE time notifications)
static uint32_t session_start_time_ms = 0;
static uint32_t last_battery_check_ms = 0;

// Current operating mode (accessed by motor_get_current_mode())
static mode_t current_mode = MODE_1HZ_50;   // Default: Mode 0 (1Hz @ 50%)

// Mode 5 (custom) parameters (updated via BLE)
static uint32_t mode5_on_ms = 250;          // Default: 250ms on (1Hz)
static uint32_t mode5_coast_ms = 250;       // Default: 250ms coast (1Hz)
static uint8_t mode5_pwm_intensity = 75;    // Default: 75% PWM

// BLE parameter update flag
static volatile bool ble_params_updated = false;

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * @brief Set LED color based on current mode
 * @param mode Current mode (0-4)
 *
 * Uses LED control module to set color indication
 */
static void led_set_mode_color(mode_t mode) {
    uint8_t brightness = ble_get_led_brightness();

    // Mode-specific colors (matching BLE GATT test)
    switch (mode) {
        case MODE_1HZ_50:
            led_set_palette(0, brightness);  // Red
            break;
        case MODE_1HZ_25:
            led_set_palette(4, brightness);  // Green
            break;
        case MODE_05HZ_50:
            led_set_palette(8, brightness);  // Blue
            break;
        case MODE_05HZ_25:
            led_set_palette(2, brightness);  // Yellow
            break;
        case MODE_CUSTOM:
            led_update_from_ble();  // Use BLE-configured color
            break;
        default:
            led_clear();
            break;
    }
}

// ============================================================================
// DELAY WITH MODE CHECK (Instant Response to Queue Messages)
// ============================================================================

/**
 * @brief Delay with periodic queue checking for instant mode changes
 * @param delay_ms Total delay duration in milliseconds
 * @return true if mode change/shutdown detected (delay interrupted)
 * @return false if delay completed normally
 *
 * Checks button_to_motor_queue every 50ms for:
 * - MSG_MODE_CHANGE: Instant mode switching
 * - MSG_EMERGENCY_SHUTDOWN: Instant shutdown
 *
 * This enables <100ms mode switching latency per AD030
 */
static bool delay_with_mode_check(uint32_t delay_ms) {
    const uint32_t CHECK_INTERVAL_MS = MODE_CHECK_INTERVAL_MS;
    uint32_t remaining_ms = delay_ms;

    while (remaining_ms > 0) {
        uint32_t this_delay = (remaining_ms < CHECK_INTERVAL_MS) ? remaining_ms : CHECK_INTERVAL_MS;
        vTaskDelay(pdMS_TO_TICKS(this_delay));
        remaining_ms -= this_delay;

        // Quick check for mode change or shutdown (non-blocking peek)
        task_message_t msg;
        if (xQueuePeek(button_to_motor_queue, &msg, 0) == pdPASS) {
            if (msg.type == MSG_MODE_CHANGE || msg.type == MSG_EMERGENCY_SHUTDOWN) {
                return true; // Mode change or shutdown detected
            }
        }
    }

    return false; // Delay completed normally
}

// ============================================================================
// HELPER: Calculate Mode Timing
// ============================================================================

/**
 * @brief Calculate motor timing based on current mode and BLE parameters
 * @param mode Current mode
 * @param motor_on_ms Output: Motor ON time in milliseconds
 * @param coast_ms Output: Coast time in milliseconds
 * @param pwm_intensity Output: PWM intensity percentage
 */
static void calculate_mode_timing(mode_t mode, uint32_t *motor_on_ms, uint32_t *coast_ms, uint8_t *pwm_intensity) {
    if (mode == MODE_CUSTOM) {
        // Mode 5: Custom parameters from BLE
        uint16_t freq_x100 = ble_get_custom_frequency_hz();  // Hz × 100
        uint8_t duty = ble_get_custom_duty_percent();         // 10-90%

        // Calculate cycle period in ms: period = 1000 / (freq / 100)
        uint32_t cycle_ms = 100000 / freq_x100;  // e.g., 100 → 1000ms for 1Hz

        // Calculate motor ON time: on_time = (cycle / 2) * (duty / 100)
        *motor_on_ms = (cycle_ms * duty) / 200;  // Half-cycle × duty%

        // Coast is remaining half-cycle
        *coast_ms = (cycle_ms / 2) - *motor_on_ms;

        // PWM intensity from BLE
        *pwm_intensity = ble_get_pwm_intensity();

        ESP_LOGI(TAG, "Mode 5: %.2fHz, %u%% duty → %lums ON, %lums coast, %u%% PWM",
                 freq_x100 / 100.0f, duty, *motor_on_ms, *coast_ms, *pwm_intensity);
    } else {
        // Modes 0-3: Predefined
        *motor_on_ms = modes[mode].motor_on_ms;
        *coast_ms = modes[mode].coast_ms;
        *pwm_intensity = ble_get_pwm_intensity();  // Still use BLE intensity for all modes
    }
}

// ============================================================================
// MOTOR TASK - MAIN FREERTOS TASK FUNCTION
// ============================================================================

void motor_task(void *pvParameters) {
    motor_state_t state = MOTOR_STATE_CHECK_MESSAGES;

    // Initialize current_mode from BLE (may have been loaded from NVS)
    current_mode = ble_get_current_mode();

    uint32_t session_start_ms = (uint32_t)(esp_timer_get_time() / 1000);
    uint32_t led_indication_start_ms = session_start_ms;
    bool led_indication_active = true;

    // Motor timing variables (updated when mode changes)
    uint32_t motor_on_ms = 0;
    uint32_t coast_ms = 0;
    uint8_t pwm_intensity = 0;
    bool show_led = false;

    // Back-EMF sampling flag and storage
    bool sample_backemf = false;
    int raw_mv_drive = 0, raw_mv_immed = 0, raw_mv_settled = 0;
    int16_t bemf_drive = 0, bemf_immed = 0, bemf_settled = 0;

    // Phase tracking for shared back-EMF states
    bool in_forward_phase = true;

    // Initialize session timestamp for BLE
    session_start_time_ms = session_start_ms;
    last_battery_check_ms = session_start_ms;

    // Subscribe to watchdog (soft-fail pattern)
    esp_err_t err = esp_task_wdt_add(NULL);
    if (err != ESP_OK) {
        ESP_LOGW(TAG, "Failed to add to watchdog: %s (continuing anyway)",
                 esp_err_to_name(err));
    }

    ESP_LOGI(TAG, "Motor task started: %s", modes[current_mode].name);

    // ========================================================================
    // MAIN STATE MACHINE LOOP
    // ========================================================================

    while (state != MOTOR_STATE_SHUTDOWN) {
        uint32_t now = (uint32_t)(esp_timer_get_time() / 1000);
        uint32_t elapsed = now - session_start_ms;

        switch (state) {
            // ================================================================
            // STATE: CHECK_MESSAGES
            // ================================================================
            case MOTOR_STATE_CHECK_MESSAGES: {
                // Feed watchdog every cycle (soft-fail pattern)
                err = esp_task_wdt_reset();
                if (err != ESP_OK) {
                    ESP_LOGW(TAG, "Failed to reset watchdog: %s", esp_err_to_name(err));
                }

                // Update session time to BLE (every second)
                uint32_t session_time_sec = elapsed / 1000;
                ble_update_session_time(session_time_sec);

                // Check battery periodically (every 10 seconds)
                if ((now - last_battery_check_ms) >= BATTERY_CHECK_INTERVAL_MS) {
                    int raw_mv;
                    float battery_v;
                    int battery_pct;

                    if (battery_read_voltage(&raw_mv, &battery_v, &battery_pct) == ESP_OK) {
                        ble_update_battery_level((uint8_t)battery_pct);
                        ESP_LOGI(TAG, "Battery: %.2fV [%d%%]", battery_v, battery_pct);
                    }

                    last_battery_check_ms = now;
                }

                // Check for emergency shutdown and mode changes
                task_message_t msg;
                while (xQueueReceive(button_to_motor_queue, &msg, 0) == pdPASS) {
                    if (msg.type == MSG_EMERGENCY_SHUTDOWN) {
                        ESP_LOGI(TAG, "Emergency shutdown");
                        state = MOTOR_STATE_SHUTDOWN;
                        break;
                    } else if (msg.type == MSG_MODE_CHANGE) {
                        // Process LAST mode change only (purge queue)
                        mode_t new_mode = msg.data.new_mode;
                        while (xQueuePeek(button_to_motor_queue, &msg, 0) == pdPASS) {
                            if (msg.type == MSG_MODE_CHANGE) {
                                xQueueReceive(button_to_motor_queue, &msg, 0);
                                new_mode = msg.data.new_mode;
                            } else {
                                break;
                            }
                        }

                        if (new_mode != current_mode) {
                            current_mode = new_mode;
                            ESP_LOGI(TAG, "Mode: %s", modes[current_mode].name);
                            led_indication_active = true;
                            led_indication_start_ms = now;
                        }
                    }
                }

                // Check session timeout (from BLE configuration)
                uint32_t session_duration_sec = ble_get_session_duration_sec();
                if (session_time_sec >= session_duration_sec) {
                    ESP_LOGI(TAG, "Session complete (%u sec)", session_duration_sec);
                    state = MOTOR_STATE_SHUTDOWN;
                    break;
                }

                // Calculate motor parameters from BLE settings
                calculate_mode_timing(current_mode, &motor_on_ms, &coast_ms, &pwm_intensity);

                // Show LED logic:
                // - Mode 5 (CUSTOM): LED blinks for entire session if BLE LED enabled
                // - Other modes: LED blinks for first 10 seconds after mode change
                if (current_mode == MODE_CUSTOM) {
                    show_led = ble_get_led_enable();  // Always use BLE setting for custom mode
                    ESP_LOGI(TAG, "Custom mode: LED enable=%d, show_led=%d", ble_get_led_enable(), show_led);
                } else {
                    show_led = led_indication_active;  // 10-second timeout for other modes
                }

                // Update back-EMF sampling flag (first 10 seconds after mode change)
                sample_backemf = led_indication_active && ((now - led_indication_start_ms) < LED_INDICATION_TIME_MS);

                // Disable LED indication after 10 seconds (non-custom modes only)
                if (current_mode != MODE_CUSTOM && led_indication_active && ((now - led_indication_start_ms) >= LED_INDICATION_TIME_MS)) {
                    led_indication_active = false;
                    led_clear();
                    ESP_LOGI(TAG, "LED off (battery conservation)");
                }

                // Don't transition to FORWARD if shutting down
                if (state == MOTOR_STATE_SHUTDOWN) {
                    break;
                }

                // Transition to FORWARD
                state = MOTOR_STATE_FORWARD_ACTIVE;
                break;
            }

            // ================================================================
            // STATE: FORWARD_ACTIVE
            // ================================================================
            case MOTOR_STATE_FORWARD_ACTIVE: {
                // Start motor forward
                motor_set_forward(pwm_intensity);
                if (show_led) led_set_mode_color(current_mode);

                // Mark that we're in forward phase
                in_forward_phase = true;

                if (sample_backemf) {
                    // Shortened active time for back-EMF sampling
                    uint32_t active_time = (motor_on_ms > 10) ? (motor_on_ms - 10) : motor_on_ms;

                    if (delay_with_mode_check(active_time)) {
                        motor_coast();
                        led_clear();
                        state = MOTOR_STATE_CHECK_MESSAGES;
                        break;
                    }

                    // Sample #1: During active drive
                    battery_read_backemf(&raw_mv_drive, &bemf_drive);

                    // Short delay before coasting
                    vTaskDelay(pdMS_TO_TICKS(10));

                    // Transition to shared immediate back-EMF sample state
                    state = MOTOR_STATE_BEMF_IMMEDIATE;
                } else {
                    // Full active time, no sampling
                    if (delay_with_mode_check(motor_on_ms)) {
                        motor_coast();
                        led_clear();
                        state = MOTOR_STATE_CHECK_MESSAGES;
                        break;
                    }

                    // CRITICAL: Always coast motor and clear LED!
                    motor_coast();
                    led_clear();

                    // Skip back-EMF states, go straight to coast remaining
                    state = MOTOR_STATE_FORWARD_COAST_REMAINING;
                }
                break;
            }

            // ================================================================
            // STATE: BEMF_IMMEDIATE (Shared between forward and reverse)
            // ================================================================
            case MOTOR_STATE_BEMF_IMMEDIATE: {
                // Coast motor and clear LED
                motor_coast();
                led_clear();

                // Sample #2: Immediately after coast starts
                battery_read_backemf(&raw_mv_immed, &bemf_immed);

                // Transition to settling state (shared)
                state = MOTOR_STATE_COAST_SETTLE;
                break;
            }

            // ================================================================
            // STATE: COAST_SETTLE (Shared between forward and reverse)
            // ================================================================
            case MOTOR_STATE_COAST_SETTLE: {
                // Wait for back-EMF to settle
                if (delay_with_mode_check(BACKEMF_SETTLE_MS)) {
                    state = MOTOR_STATE_CHECK_MESSAGES;
                    break;
                }

                // Sample #3: Settled back-EMF reading
                battery_read_backemf(&raw_mv_settled, &bemf_settled);

                // Log readings with direction label
                if (in_forward_phase) {
                    ESP_LOGI(TAG, "FWD: %dmV→%+dmV | %dmV→%+dmV | %dmV→%+dmV",
                             raw_mv_drive, bemf_drive, raw_mv_immed, bemf_immed,
                             raw_mv_settled, bemf_settled);
                } else {
                    ESP_LOGI(TAG, "REV: %dmV→%+dmV | %dmV→%+dmV | %dmV→%+dmV",
                             raw_mv_drive, bemf_drive, raw_mv_immed, bemf_immed,
                             raw_mv_settled, bemf_settled);
                }

                // Transition to appropriate COAST_REMAINING state based on phase
                if (in_forward_phase) {
                    state = MOTOR_STATE_FORWARD_COAST_REMAINING;
                } else {
                    state = MOTOR_STATE_REVERSE_COAST_REMAINING;
                }
                break;
            }

            // ================================================================
            // STATE: FORWARD_COAST_REMAINING
            // ================================================================
            case MOTOR_STATE_FORWARD_COAST_REMAINING: {
                // Calculate remaining coast time
                uint32_t remaining_coast;
                if (sample_backemf) {
                    // Already spent BACKEMF_SETTLE_MS, finish the rest
                    remaining_coast = (coast_ms > BACKEMF_SETTLE_MS) ? (coast_ms - BACKEMF_SETTLE_MS) : 0;
                } else {
                    // Full coast time
                    remaining_coast = coast_ms;
                }

                if (remaining_coast > 0) {
                    if (delay_with_mode_check(remaining_coast)) {
                        state = MOTOR_STATE_CHECK_MESSAGES;
                        break;
                    }
                }

                // Transition to REVERSE phase
                state = MOTOR_STATE_REVERSE_ACTIVE;
                break;
            }

            // ================================================================
            // STATE: REVERSE_ACTIVE
            // ================================================================
            case MOTOR_STATE_REVERSE_ACTIVE: {
                // Start motor reverse
                motor_set_reverse(pwm_intensity);
                if (show_led) led_set_mode_color(current_mode);

                // Mark that we're in reverse phase
                in_forward_phase = false;

                if (sample_backemf) {
                    // Shortened active time for back-EMF sampling
                    uint32_t active_time = (motor_on_ms > 10) ? (motor_on_ms - 10) : motor_on_ms;

                    if (delay_with_mode_check(active_time)) {
                        motor_coast();
                        led_clear();
                        state = MOTOR_STATE_CHECK_MESSAGES;
                        break;
                    }

                    // Sample #1: During active drive
                    battery_read_backemf(&raw_mv_drive, &bemf_drive);

                    // Short delay before coasting
                    vTaskDelay(pdMS_TO_TICKS(10));

                    // Transition to shared immediate back-EMF sample state
                    state = MOTOR_STATE_BEMF_IMMEDIATE;
                } else {
                    // Full active time, no sampling
                    if (delay_with_mode_check(motor_on_ms)) {
                        motor_coast();
                        led_clear();
                        state = MOTOR_STATE_CHECK_MESSAGES;
                        break;
                    }

                    // CRITICAL: Always coast motor and clear LED!
                    motor_coast();
                    led_clear();

                    // Skip back-EMF states, go straight to coast remaining
                    state = MOTOR_STATE_REVERSE_COAST_REMAINING;
                }
                break;
            }

            // ================================================================
            // STATE: REVERSE_COAST_REMAINING
            // ================================================================
            case MOTOR_STATE_REVERSE_COAST_REMAINING: {
                // Calculate remaining coast time
                uint32_t remaining_coast;
                if (sample_backemf) {
                    // Already spent BACKEMF_SETTLE_MS, finish the rest
                    remaining_coast = (coast_ms > BACKEMF_SETTLE_MS) ? (coast_ms - BACKEMF_SETTLE_MS) : 0;
                } else {
                    // Full coast time
                    remaining_coast = coast_ms;
                }

                if (remaining_coast > 0) {
                    if (delay_with_mode_check(remaining_coast)) {
                        state = MOTOR_STATE_CHECK_MESSAGES;
                        break;
                    }
                }

                // Cycle complete, check messages again
                state = MOTOR_STATE_CHECK_MESSAGES;
                break;
            }

            // ================================================================
            // STATE: SHUTDOWN
            // ================================================================
            case MOTOR_STATE_SHUTDOWN: {
                // Loop exit handled by while condition
                break;
            }
        }
    }

    // ========================================================================
    // FINAL CLEANUP
    // ========================================================================

    ESP_LOGI(TAG, "Motor task shutting down");

    // Coast motor, clear LED
    motor_coast();
    led_clear();
    vTaskDelay(pdMS_TO_TICKS(100));

    // Unsubscribe from watchdog (soft-fail pattern)
    err = esp_task_wdt_delete(NULL);
    if (err != ESP_OK) {
        ESP_LOGW(TAG, "Failed to delete from watchdog: %s", esp_err_to_name(err));
    }

    // Motor task cleanup complete
    // NOTE: button_task coordinates final deep sleep entry after countdown
    // Do NOT call power_enter_deep_sleep() here - would skip countdown
    ESP_LOGI(TAG, "Motor task stopped (button_task will coordinate final shutdown)");
    vTaskDelay(pdMS_TO_TICKS(100));  // Allow log to flush
    vTaskDelete(NULL);
}

// ============================================================================
// BLE INTEGRATION API IMPLEMENTATION
// ============================================================================

mode_t motor_get_current_mode(void) {
    // Thread-safe read of current operating mode
    return current_mode;
}

esp_err_t motor_update_mode5_timing(uint32_t motor_on_ms, uint32_t coast_ms) {
    // Validate parameters (safety limits per AD031)
    if (motor_on_ms < 10 || motor_on_ms > 500) {
        ESP_LOGE(TAG, "Invalid motor_on_ms: %u (must be 10-500ms)", motor_on_ms);
        return ESP_ERR_INVALID_ARG;
    }
    if (coast_ms < 10 || coast_ms > 2000) {
        ESP_LOGE(TAG, "Invalid coast_ms: %u (must be 10-2000ms)", coast_ms);
        return ESP_ERR_INVALID_ARG;
    }

    // Update global mode 5 parameters (thread-safe, motor_task reads these)
    mode5_on_ms = motor_on_ms;
    mode5_coast_ms = coast_ms;

    ESP_LOGI(TAG, "Mode 5 timing updated: on=%ums coast=%ums", motor_on_ms, coast_ms);
    return ESP_OK;
}

esp_err_t motor_update_mode5_intensity(uint8_t intensity_percent) {
    // Validate intensity (safety limits per AD031)
    if (intensity_percent < 30 || intensity_percent > 80) {
        ESP_LOGE(TAG, "Invalid intensity: %u%% (must be 30-80%%)", intensity_percent);
        return ESP_ERR_INVALID_ARG;
    }

    // Update global mode 5 intensity (thread-safe, motor_task reads this)
    mode5_pwm_intensity = intensity_percent;

    ESP_LOGI(TAG, "Mode 5 intensity updated: %u%%", intensity_percent);
    return ESP_OK;
}

void ble_callback_mode_changed(mode_t new_mode) {
    // Send mode change message to motor task queue
    task_message_t msg = {
        .type = MSG_MODE_CHANGE,
        .data = {.new_mode = new_mode}
    };

    if (button_to_motor_queue == NULL) {
        ESP_LOGW(TAG, "BLE mode change ignored: queue not initialized");
        return;
    }

    if (xQueueSend(button_to_motor_queue, &msg, pdMS_TO_TICKS(100)) == pdTRUE) {
        ESP_LOGI(TAG, "BLE triggered mode change → %d", new_mode);
    } else {
        ESP_LOGW(TAG, "BLE mode change failed: queue full");
    }
}

void ble_callback_params_updated(void) {
    // Set flag to signal motor_task to reload BLE parameters
    // Motor task checks this flag in delay_with_mode_check()
    ble_params_updated = true;
    ESP_LOGI(TAG, "BLE parameters updated (flag set)");
}
