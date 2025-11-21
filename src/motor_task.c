/**
 * @file motor_task.c
 * @brief Motor Control Task Module - Implementation
 *
 * Complete 9-state machine for bilateral alternating motor control with:
 * - Pairing wait state (Phase 1b.3) - delays session start until BLE pairing completes
 * - Mode configurations (predefined + custom via BLE)
 * - Message queue handling (button events, battery warnings, pairing events)
 * - Back-EMF sampling for research
 * - Soft-fail watchdog pattern
 * - JPL compliance (no busy-wait loops)
 *
 * @date November 15, 2025 (Phase 1b.3: Added pairing wait state)
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
#include "role_manager.h"
#include "power_manager.h"
#include "time_sync.h"
#include "time_sync_task.h"

static const char *TAG = "MOTOR_TASK";

// ============================================================================
// TIMING CONSTANTS
// ============================================================================

#define LED_INDICATION_TIME_MS  10000               // Back-EMF sampling window
#define BACKEMF_SETTLE_MS       10                  // Back-EMF settle time
#define MODE_CHECK_INTERVAL_MS  50                  // Check queue every 50ms
#define BATTERY_CHECK_INTERVAL_MS  60000            // Check battery every 60 seconds
#define SESSION_TIME_NOTIFY_INTERVAL_MS 60000       // Notify session time every 60 seconds

// ============================================================================
// MODE CONFIGURATIONS
// ============================================================================

// NOTE: Frequencies are BILATERAL alternation rates (not per-device rates)
// ACTIVE/INACTIVE Architecture (50/50 split):
// - Each cycle is divided into ACTIVE (50%) and INACTIVE (50%) periods
// - All presets use 50% duty for consistency (50% of ACTIVE period)
// - Direction alternates AFTER each INACTIVE period
//
// BILATERAL MODE (dual devices):
// - "1.0Hz" = 1 complete left-right alternation per second
// - DEV A ACTIVE while DEV B INACTIVE, then vice versa
// - Example 1.0Hz: DEV_A [250ms ON | 750ms OFF], DEV_B [750ms OFF | 250ms ON]
//
// SINGLE DEVICE MODE:
// - "1.0Hz" = motor reverses direction every 1000ms
// - Total cycle time: 1000ms (250ms ON, 750ms OFF per direction)
const mode_config_t modes[MODE_COUNT] = {
    {"0.5Hz@25%",  500, 1500},  // MODE_05HZ_25 → 0.5Hz: 500ms ON, 1500ms OFF (25% of 2000ms period)
    {"1.0Hz@25%",  250,  750},  // MODE_1HZ_25 → 1.0Hz: 250ms ON, 750ms OFF (25% of 1000ms period)
    {"1.5Hz@25%",  167,  500},  // MODE_15HZ_25 → 1.5Hz: 167ms ON, 500ms OFF (25% of 667ms period)
    {"2.0Hz@25%",  125,  375},  // MODE_2HZ_25 → 2.0Hz: 125ms ON, 375ms OFF (25% of 500ms period)
    {"Custom", 250, 750}        // MODE_CUSTOM (default to 1.0Hz@25%)
};

// ============================================================================
// GLOBAL STATE (Module-private static variables)
// ============================================================================

// Session state (for BLE time notifications)
static uint32_t session_start_time_ms = 0;
static uint32_t last_battery_check_ms = 0;
static uint32_t last_session_time_notify_ms = 0;

// Current operating mode (accessed by motor_get_current_mode())
static mode_t current_mode = MODE_05HZ_25;   // Default: Mode 0 (0.5Hz @ 25%)

// Mode 4 (custom) parameters (updated via BLE)
static uint32_t mode5_on_ms = 250;          // Default: 250ms on (1Hz @ 25% duty)
static uint32_t mode5_coast_ms = 750;       // Default: 750ms coast (1Hz @ 25% duty)
static uint8_t mode5_pwm_intensity = MOTOR_PWM_DEFAULT;  // From motor_control.h (single source of truth)

// BLE parameter update flag
static volatile bool ble_params_updated = false;

// Direction alternation flag (fixes 2× frequency bug)
// true = forward, false = reverse
// Alternates after each INACTIVE period
static bool is_forward_direction = true;

// Phase 2 forward-compatibility: Direction mode flag
// When true: Direction alternates each cycle (motor wear reduction)
// When false: Direction fixed per device (research capability - dual-device only)
// Default: true (alternating mode)
static bool direction_alternation_enabled = true;

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
        case MODE_05HZ_25:
            led_set_palette(0, brightness);  // Red
            break;
        case MODE_1HZ_25:
            led_set_palette(4, brightness);  // Green
            break;
        case MODE_15HZ_25:
            led_set_palette(8, brightness);  // Blue
            break;
        case MODE_2HZ_25:
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
 * @param coast_ms Output: Coast time in milliseconds (INACTIVE period)
 * @param pwm_intensity Output: PWM intensity percentage
 * @param verbose_logging If true, log timing calculations (gated with BEMF sampling)
 *
 * ACTIVE/INACTIVE Architecture:
 * - Cycle is split 50/50 into ACTIVE and INACTIVE periods
 * - ACTIVE period: Motor can be ON (based on duty%) or coasting
 * - INACTIVE period: Motor always coasting (guaranteed 50% OFF time)
 * - Duty% applies only to ACTIVE period (10% duty = 10% of ACTIVE period)
 * - Direction alternates AFTER each INACTIVE period
 */
static void calculate_mode_timing(mode_t mode, uint32_t *motor_on_ms, uint32_t *coast_ms, uint8_t *pwm_intensity, bool verbose_logging) {
    if (mode == MODE_CUSTOM) {
        // Mode 4: Custom parameters from BLE
        uint16_t freq_x100 = ble_get_custom_frequency_hz();  // Hz × 100
        uint8_t duty = ble_get_custom_duty_percent();         // 10-100% of ACTIVE period

        // Calculate FULL cycle period in ms: period = 1000 / (freq / 100)
        uint32_t cycle_ms = 100000 / freq_x100;  // e.g., 100 → 1000ms for 1Hz

        // Split cycle 50/50 into ACTIVE and INACTIVE periods
        uint32_t active_period_ms = cycle_ms / 2;
        uint32_t inactive_period_ms = cycle_ms - active_period_ms;  // Handle odd values

        // Apply duty% within ACTIVE period only (linear scaling)
        *motor_on_ms = (active_period_ms * duty) / 100;

        // Coast time is always the INACTIVE period (guaranteed 50% OFF)
        *coast_ms = inactive_period_ms;

        // PWM intensity from BLE
        *pwm_intensity = ble_get_pwm_intensity();

        if (verbose_logging) {
            ESP_LOGI(TAG, "Mode 4 (Custom): %.2fHz, %u%% duty → %lums ON, %lums OFF (50/50 split), %u%% PWM",
                     freq_x100 / 100.0f, duty, *motor_on_ms, *coast_ms, *pwm_intensity);
        }
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
    // Phase 1b.3: Start in PAIRING_WAIT state
    // Session timer will be initialized only after pairing completes
    motor_state_t state = MOTOR_STATE_PAIRING_WAIT;

    // Initialize current_mode from BLE (may have been loaded from NVS)
    current_mode = ble_get_current_mode();

    // Note: session_start_time_ms will be set AFTER pairing completes (Phase 1b.3)
    // Use current time for task-specific timers
    uint32_t now_ms = (uint32_t)(esp_timer_get_time() / 1000);
    uint32_t led_indication_start_ms = now_ms;
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

    // Initialize task-specific timers (session_start_time_ms already set during hardware init)
    last_battery_check_ms = now_ms;
    last_session_time_notify_ms = now_ms;

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

        // NOTE: elapsed calculation moved inside CHECK_MESSAGES state
        // (not available during PAIRING_WAIT since session hasn't started yet)

        switch (state) {
            // ================================================================
            // STATE: PAIRING_WAIT (Phase 1b.3)
            // ================================================================
            case MOTOR_STATE_PAIRING_WAIT: {
                // Feed watchdog during pairing wait
                esp_err_t err = esp_task_wdt_reset();
                if (err != ESP_OK) {
                    ESP_LOGW(TAG, "Failed to reset watchdog: %s", esp_err_to_name(err));
                }

                // Check for emergency shutdown from button task
                task_message_t msg;
                if (xQueueReceive(button_to_motor_queue, &msg, pdMS_TO_TICKS(100)) == pdTRUE) {
                    if (msg.type == MSG_EMERGENCY_SHUTDOWN) {
                        ESP_LOGI(TAG, "Emergency shutdown during pairing wait");
                        state = MOTOR_STATE_SHUTDOWN;
                        break;
                    }
                }

                // Check for pairing completion from BLE task
                if (xQueueReceive(ble_to_motor_queue, &msg, 0) == pdTRUE) {
                    if (msg.type == MSG_PAIRING_COMPLETE) {
                        ESP_LOGI(TAG, "Pairing completed successfully");

                        // Initialize session timer NOW (after pairing complete)
                        motor_init_session_time();
                        ESP_LOGI(TAG, "Session timer initialized (pairing complete)");

                        // Phase 2: Initialize time synchronization via dedicated task (AD039)
                        peer_role_t peer_role = ble_get_peer_role();
                        if (peer_role != PEER_ROLE_NONE) {
                            // Map peer role to time sync role
                            time_sync_role_t sync_role = (peer_role == PEER_ROLE_SERVER)
                                ? TIME_SYNC_ROLE_SERVER
                                : TIME_SYNC_ROLE_CLIENT;

                            // Send initialization message to time_sync_task (NTP-style, no timestamp needed)
                            esp_err_t err = time_sync_task_send_init(sync_role);
                            if (err == ESP_OK) {
                                ESP_LOGI(TAG, "Time sync initialization requested (%s role, NTP-style)",
                                         sync_role == TIME_SYNC_ROLE_SERVER ? "SERVER" : "CLIENT");
                            } else {
                                ESP_LOGE(TAG, "Failed to send time sync init message: %s",
                                         esp_err_to_name(err));
                            }
                        }

                        // Motor task now owns WS2812B (Phase 1b.3: Prevent status_led interruption)
                        led_set_motor_ownership(true);

                        // Reset LED indication timer (BUG FIX: Timer starts during BLE pattern)
                        led_indication_start_ms = (uint32_t)(esp_timer_get_time() / 1000);

                        // Bilateral Coordination: CLIENT starts in INACTIVE to offset from SERVER
                        peer_role_t role = ble_get_peer_role();
                        if (role == PEER_ROLE_CLIENT) {
                            // Initialize timing parameters for initial cycle
                            calculate_mode_timing(current_mode, &motor_on_ms, &coast_ms, &pwm_intensity, false);
                            show_led = (current_mode == MODE_CUSTOM) ? ble_get_led_enable() : led_indication_active;
                            is_forward_direction = true;  // Start in forward direction

                            // Calculate proper bilateral offset (half of bilateral cycle)
                            // For 1.0Hz@50%: bilateral_cycle = 250ms + 750ms = 1000ms → offset = 500ms
                            // This ensures CLIENT activates when SERVER is inactive (true alternation)
                            uint32_t bilateral_cycle_ms = motor_on_ms + coast_ms;
                            uint32_t bilateral_offset_ms = bilateral_cycle_ms / 2;
                            coast_ms = bilateral_offset_ms;  // Override for initial INACTIVE wait

                            ESP_LOGI(TAG, "State: PAIRING_WAIT → INACTIVE (CLIENT offset=%lums, bilateral_cycle=%lums)",
                                     bilateral_offset_ms, bilateral_cycle_ms);
                            state = MOTOR_STATE_INACTIVE;
                        } else {
                            // SERVER or STANDALONE: Normal forward start
                            ESP_LOGI(TAG, "State: PAIRING_WAIT → CHECK_MESSAGES (%s)",
                                     role == PEER_ROLE_SERVER ? "SERVER" : "STANDALONE");
                            state = MOTOR_STATE_CHECK_MESSAGES;
                        }
                        break;
                    } else if (msg.type == MSG_PAIRING_FAILED) {
                        ESP_LOGW(TAG, "Peer pairing failed or timeout - continuing as single device");

                        // Initialize session timer (single-device mode)
                        motor_init_session_time();
                        ESP_LOGI(TAG, "Session timer initialized (single-device mode)");

                        // Motor task now owns WS2812B (Phase 1b.3: Prevent status_led interruption)
                        led_set_motor_ownership(true);

                        // Reset LED indication timer (BUG FIX: Timer starts during BLE pattern)
                        led_indication_start_ms = (uint32_t)(esp_timer_get_time() / 1000);

                        // Transition to normal operation (single-device)
                        ESP_LOGI(TAG, "State: PAIRING_WAIT → CHECK_MESSAGES (single-device)");
                        state = MOTOR_STATE_CHECK_MESSAGES;
                        break;
                    }
                }

                // Periodic status log (every 5 seconds)
                static uint32_t last_pairing_log_ms = 0;
                if ((now - last_pairing_log_ms) >= 5000) {
                    ESP_LOGI(TAG, "Waiting for BLE pairing to complete...");
                    last_pairing_log_ms = now;
                }

                break;
            }

            // ================================================================
            // STATE: CHECK_MESSAGES
            // ================================================================
            case MOTOR_STATE_CHECK_MESSAGES: {
                // Calculate elapsed time (session timer now initialized)
                uint32_t elapsed = now - session_start_time_ms;
                // Feed watchdog every cycle (soft-fail pattern)
                esp_err_t err = esp_task_wdt_reset();
                if (err != ESP_OK) {
                    ESP_LOGW(TAG, "Failed to reset watchdog: %s", esp_err_to_name(err));
                }

                // Calculate current session time (used for notifications and timeout check)
                uint32_t session_time_sec = elapsed / 1000;

                // Notify session time periodically (every 60 seconds)
                // Mobile app counts seconds in UI between notifications
                if ((now - last_session_time_notify_ms) >= SESSION_TIME_NOTIFY_INTERVAL_MS) {
                    ble_update_session_time(session_time_sec);
                    last_session_time_notify_ms = now;
                }

                // Check battery periodically (every 60 seconds)
                if ((now - last_battery_check_ms) >= BATTERY_CHECK_INTERVAL_MS) {
                    int raw_mv;
                    float battery_v;
                    int battery_pct;

                    if (battery_read_voltage(&raw_mv, &battery_v, &battery_pct) == ESP_OK) {
                        ble_update_battery_level((uint8_t)battery_pct);           // Configuration Service (mobile app)
                        ble_update_bilateral_battery_level((uint8_t)battery_pct); // Bilateral Control Service (peer device)

                        // Phase 2: Add sync quality to battery log if time sync active (AD039)
                        if (TIME_SYNC_IS_ACTIVE()) {
                            int64_t clock_offset_us = 0;
                            time_sync_quality_t quality;

                            if (time_sync_get_clock_offset(&clock_offset_us) == ESP_OK &&
                                time_sync_get_quality(&quality) == ESP_OK) {
                                ESP_LOGI(TAG, "Battery: %.2fV [%d%%] | BLE: %s | Sync: %u%% (offset: %lld μs)",
                                         battery_v, battery_pct, ble_get_connection_type_str(),
                                         quality.quality_score, clock_offset_us);
                            } else {
                                ESP_LOGI(TAG, "Battery: %.2fV [%d%%] | BLE: %s", battery_v, battery_pct, ble_get_connection_type_str());
                            }
                        } else {
                            ESP_LOGI(TAG, "Battery: %.2fV [%d%%] | BLE: %s", battery_v, battery_pct, ble_get_connection_type_str());
                        }
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

                    // Send session timeout message to button task
                    task_message_t timeout_msg = {
                        .type = MSG_SESSION_TIMEOUT,
                        .data = {.new_mode = 0}
                    };
                    if (xQueueSend(motor_to_button_queue, &timeout_msg, pdMS_TO_TICKS(100)) == pdTRUE) {
                        ESP_LOGI(TAG, "Session timeout message sent to button_task");
                    } else {
                        ESP_LOGW(TAG, "Failed to send session timeout message to button_task");
                    }

                    state = MOTOR_STATE_SHUTDOWN;
                    break;
                }

                // Show LED logic:
                // - Mode 5 (CUSTOM): LED blinks for entire session if BLE LED enabled
                // - Other modes: LED blinks for first 10 seconds after mode change
                if (current_mode == MODE_CUSTOM) {
                    show_led = ble_get_led_enable();  // Always use BLE setting for custom mode
                } else {
                    show_led = led_indication_active;  // 10-second timeout for other modes
                }

                // Update back-EMF sampling flag (first 10 seconds after mode change)
                sample_backemf = led_indication_active && ((now - led_indication_start_ms) < LED_INDICATION_TIME_MS);

                // Calculate motor parameters from BLE settings (verbose logging gated with BEMF)
                calculate_mode_timing(current_mode, &motor_on_ms, &coast_ms, &pwm_intensity, sample_backemf);

                // Phase 2: Apply bilateral offset for CLIENT devices throughout session
                // This ensures CLIENT maintains half-cycle offset from SERVER for true alternation
                if (ble_get_peer_role() == PEER_ROLE_CLIENT) {
                    uint32_t bilateral_cycle_ms = motor_on_ms + coast_ms;
                    coast_ms = bilateral_cycle_ms / 2;  // Maintain half-cycle offset
                    ESP_LOGD(TAG, "CLIENT bilateral: coast=%lu ms (cycle=%lu ms)",
                             coast_ms, bilateral_cycle_ms);
                }

                // Disable LED indication after 10 seconds (non-custom modes only)
                if (current_mode != MODE_CUSTOM && led_indication_active && ((now - led_indication_start_ms) >= LED_INDICATION_TIME_MS)) {
                    led_indication_active = false;
                    led_clear();
                    ESP_LOGI(TAG, "LED off (battery conservation)");
                }

                // Don't transition to ACTIVE if shutting down
                if (state == MOTOR_STATE_SHUTDOWN) {
                    break;
                }

                // Transition to ACTIVE (direction determined by is_forward_direction flag)
                state = MOTOR_STATE_ACTIVE;
                break;
            }

            // ================================================================
            // STATE: ACTIVE
            // ================================================================
            case MOTOR_STATE_ACTIVE: {
                // Start motor in current direction (determined by is_forward_direction flag)
                if (is_forward_direction) {
                    motor_set_forward(pwm_intensity, sample_backemf);
                } else {
                    motor_set_reverse(pwm_intensity, sample_backemf);
                }
                if (show_led) led_set_mode_color(current_mode);

                if (sample_backemf) {
                    // Shortened active time for back-EMF sampling
                    uint32_t active_time = (motor_on_ms > 10) ? (motor_on_ms - 10) : motor_on_ms;

                    if (delay_with_mode_check(active_time)) {
                        motor_coast(sample_backemf);
                        led_clear();
                        state = MOTOR_STATE_CHECK_MESSAGES;
                        break;
                    }

                    // Sample #1: During active drive
                    battery_read_backemf(&raw_mv_drive, &bemf_drive);

                    // Short delay before coasting
                    vTaskDelay(pdMS_TO_TICKS(10));

                    // Transition to immediate back-EMF sample state
                    state = MOTOR_STATE_BEMF_IMMEDIATE;
                } else {
                    // Full active time, no sampling
                    if (delay_with_mode_check(motor_on_ms)) {
                        motor_coast(sample_backemf);
                        led_clear();
                        state = MOTOR_STATE_CHECK_MESSAGES;
                        break;
                    }

                    // CRITICAL: Always coast motor and clear LED!
                    motor_coast(sample_backemf);
                    led_clear();

                    // Transition to INACTIVE state
                    state = MOTOR_STATE_INACTIVE;
                }
                break;
            }

            // ================================================================
            // STATE: BEMF_IMMEDIATE
            // ================================================================
            case MOTOR_STATE_BEMF_IMMEDIATE: {
                // Coast motor and clear LED
                motor_coast(sample_backemf);
                led_clear();

                // Sample #2: Immediately after coast starts
                battery_read_backemf(&raw_mv_immed, &bemf_immed);

                // Transition to settling state
                state = MOTOR_STATE_COAST_SETTLE;
                break;
            }

            // ================================================================
            // STATE: COAST_SETTLE
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
                if (is_forward_direction) {
                    ESP_LOGI(TAG, "FWD: %dmV→%+dmV | %dmV→%+dmV | %dmV→%+dmV",
                             raw_mv_drive, bemf_drive, raw_mv_immed, bemf_immed,
                             raw_mv_settled, bemf_settled);
                } else {
                    ESP_LOGI(TAG, "REV: %dmV→%+dmV | %dmV→%+dmV | %dmV→%+dmV",
                             raw_mv_drive, bemf_drive, raw_mv_immed, bemf_immed,
                             raw_mv_settled, bemf_settled);
                }

                // Transition to INACTIVE state
                state = MOTOR_STATE_INACTIVE;
                break;
            }

            // ================================================================
            // STATE: INACTIVE
            // ================================================================
            case MOTOR_STATE_INACTIVE: {
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

                // CRITICAL: Alternate direction for next cycle (fixes 2× frequency bug)
                // Single-device mode: Always alternate (motor wear reduction)
                // Dual-device mode: Depends on direction_alternation_enabled flag
                //   - Mode 0 (alternating): Both devices alternate forward/reverse
                //   - Mode 1 (fixed_opposite): Device A always forward, Device B always reverse
                if (direction_alternation_enabled) {
                    is_forward_direction = !is_forward_direction;
                }

                // Cycle complete, check messages again
                state = MOTOR_STATE_CHECK_MESSAGES;
                break;
            }

            // ================================================================
            // STATE: SHUTDOWN
            // ================================================================
            case MOTOR_STATE_SHUTDOWN: {
                // Release WS2812B ownership (Phase 1b.3: Allow status_led patterns)
                led_set_motor_ownership(false);

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
    motor_coast(sample_backemf);
    led_clear();
    vTaskDelay(pdMS_TO_TICKS(100));

    // Unsubscribe from watchdog (soft-fail pattern)
    err = esp_task_wdt_delete(NULL);
    if (err != ESP_OK) {
        ESP_LOGW(TAG, "Failed to delete from watchdog: %s", esp_err_to_name(err));
    }

    // Motor task cleanup complete
    // NOTE: For emergency shutdown (button hold), button_task coordinates deep sleep
    // NOTE: For session timeout, we've notified button_task via motor_to_button_queue
    // Do NOT call power_enter_deep_sleep() here - would skip proper shutdown sequence
    ESP_LOGI(TAG, "Motor task stopped");
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

void motor_init_session_time(void) {
    // Initialize session start time during hardware init
    // This allows BLE clients connecting early to get correct uptime
    session_start_time_ms = (uint32_t)(esp_timer_get_time() / 1000);
    ESP_LOGI(TAG, "Session start time initialized: %lu ms", session_start_time_ms);
}

uint32_t motor_get_session_time_ms(void) {
    // Calculate elapsed time since session start
    // Returns milliseconds since motor_init_session_time() was called
    if (session_start_time_ms == 0) {
        return 0;  // Not initialized yet (shouldn't happen in normal flow)
    }
    uint32_t now = (uint32_t)(esp_timer_get_time() / 1000);
    return now - session_start_time_ms;
}

esp_err_t motor_update_mode5_timing(uint32_t motor_on_ms, uint32_t coast_ms) {
    // Validate parameters (safety limits per AD031/AD032)
    // AD032: 0.25-2.0Hz @ 10-100% duty (full cycle timing)
    uint32_t cycle_ms = motor_on_ms + coast_ms;

    if (motor_on_ms < 10) {
        ESP_LOGE(TAG, "Invalid motor_on_ms: %u (must be ≥10ms for perception)", motor_on_ms);
        return ESP_ERR_INVALID_ARG;
    }

    if (motor_on_ms > cycle_ms) {
        ESP_LOGE(TAG, "Invalid motor_on_ms: %u exceeds cycle %u", motor_on_ms, cycle_ms);
        return ESP_ERR_INVALID_ARG;
    }

    if (coast_ms > 4000) {
        ESP_LOGE(TAG, "Invalid coast_ms: %u (must be ≤4000ms)", coast_ms);
        return ESP_ERR_INVALID_ARG;
    }

    // Update global mode 4 parameters (thread-safe, motor_task reads these)
    mode5_on_ms = motor_on_ms;
    mode5_coast_ms = coast_ms;

    ESP_LOGI(TAG, "Mode 4 (Custom) timing updated: on=%ums coast=%ums", motor_on_ms, coast_ms);
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
