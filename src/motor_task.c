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
 * - Bug #17 Fix: Absolute time scheduling eliminates vTaskDelay jitter accumulation
 *
 * Bug #17 (November 25, 2025): vTaskDelay jitter accumulation caused phase drift
 * - Root cause: vTaskDelay() guarantees MINIMUM delay, not exact delay
 * - Each 50ms delay could be 51-55ms, accumulating 1-5ms error per cycle
 * - At 1Hz, this compounds to 50-250ms drift over 10 seconds
 * - Solution: Use delay_until_target_ms() with absolute time targets
 * - Instead of "wait 250ms from now" (accumulates error), we now do "wait until time X"
 *
 * Phase 6r (Drift Continuation): Motor coordination continues during BLE disconnect
 * - CLIENT preserves motor epoch and drift rate when BLE peer disconnects
 * - Bilateral alternation continues using frozen drift rate (±2.4ms over 20 min)
 * - Safety timeout: Motor epoch expires after 2-minute disconnect
 * - Role swap detection: Clears epoch if role changes on reconnection (shouldn't happen)
 * - Rationale: Drift stability (±30 μs / 90 min from Phase 2 testing) allows
 *   CLIENT to extrapolate correct timing without active beacons during brief
 *   disconnections, providing therapeutic continuity during BLE glitches.
 *
 * @date November 25, 2025 (Bug #17 Fix: Absolute time scheduling)
 * @date November 30, 2025 (Phase 6r: Drift continuation during disconnect)
 * @author Claude Code (Anthropic)
 */

#include "motor_task.h"
#include <string.h>
#include "esp_log.h"
#include "esp_timer.h"
#include "esp_task_wdt.h"

// Module dependencies
#include "battery_monitor.h"
#include "backemf.h"
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
#define MODE_CHECK_INTERVAL_MS  50                  // Check queue every 50ms (main branch baseline, instant button response)
#define BATTERY_CHECK_INTERVAL_MS  60000            // Check battery every 60 seconds
#define SESSION_TIME_NOTIFY_INTERVAL_MS 60000       // Notify session time every 60 seconds

// Tech Spike: Single-device drift baseline measurement
// Enable continuous activation logging when NO peer is connected
// Purpose: Measure natural oscillator drift between two independent devices
//          to determine optimal correction interval for bilateral synchronization
// Usage: Flash both devices, run as standalone (no pairing), compare logs
// #define ENABLE_SINGLE_DEVICE_DRIFT_BASELINE  // Uncomment to enable

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
// Phase 3a: Bilateral timing - ACTIVE period (motor + active coast) | INACTIVE period
// Pattern: [ACTIVE: motor_on + active_coast] [INACTIVE: always period/2]
// Motor duty % applies to ACTIVE period only (matching commercial EMDR devices)
const mode_config_t modes[MODE_COUNT] = {
    // {name, motor_on_ms, active_coast_ms, inactive_ms}
    {"0.5Hz@25%",  250,  750, 1000},  // MODE_05HZ_25: 0.5Hz, 25% motor duty (period=2000ms)
    {"1.0Hz@25%",  125,  375,  500},  // MODE_1HZ_25: 1.0Hz, 25% motor duty (period=1000ms)
    {"1.5Hz@25%",   84,  250,  333},  // MODE_15HZ_25: 1.5Hz, 25% motor duty (period=667ms)
    {"2.0Hz@25%",   63,  187,  250},  // MODE_2HZ_25: 2.0Hz, 25% motor duty (period=500ms)
    {"Custom",     250,  250,  500}   // MODE_CUSTOM: Default 1.0Hz @ 50% motor duty
};

// ============================================================================
// GLOBAL STATE (Module-private static variables)
// ============================================================================

// Session state (for BLE time notifications)
static uint32_t session_start_time_ms = 0;
static uint32_t last_battery_check_ms = 0;
static uint32_t last_session_time_notify_ms = 0;
static uint32_t last_mode_change_ms = 0;     // Track mode changes for beacon logging conflict detection

// Current operating mode (accessed by motor_get_current_mode())
static mode_t current_mode = MODE_05HZ_25;   // Default: Mode 0 (0.5Hz @ 25%)

// Mode 4 (custom) parameters (updated via BLE)
static uint32_t mode5_on_ms = 250;          // Default: 250ms on (1Hz @ 25% duty)
static uint32_t mode5_coast_ms = 750;       // Default: 750ms coast (1Hz @ 25% duty)
static uint8_t mode5_pwm_intensity = MOTOR_PWM_DEFAULT;  // From motor_control.h (single source of truth)

// BLE parameter update flag
static volatile bool ble_params_updated = false;

// Phase 6: MOTOR_STARTED message arrival flag (Issue #3 fix)
// Set when CLIENT receives MOTOR_STARTED from SERVER
// Signals waiting loop to abort wait and start motors immediately
static volatile bool motor_started_received = false;

// Direction alternation flag (fixes 2× frequency bug)
// true = forward, false = reverse
// Alternates after each INACTIVE period
static bool is_forward_direction = true;

// Phase 2 forward-compatibility: Direction mode flag
// When true: Direction alternates each cycle (motor wear reduction)
// When false: Direction fixed per device (research capability - dual-device only)
// Default: true (alternating mode)
static bool direction_alternation_enabled = true;

// Beacon-triggered back-EMF logging (Phase 2: Time synchronization verification)
// Triggered when time sync beacon is received (separate from mode-change logging)
static bool beacon_bemf_logging_active = false;
static uint32_t beacon_bemf_start_ms = 0;

// AD045: Removed correction variables (no longer needed with synchronized independent operation)
// Replaced complex drift correction with simple epoch-based calculation

// AD045: Mode change proposal state (two-phase commit protocol)
// Note: Shared with time_sync_task.c (extern declarations in motor_task.h)
bool mode_change_armed = false;          /**< True if mode change is armed and waiting for epoch */
mode_t armed_new_mode = MODE_05HZ_25;    /**< Mode to activate when armed epoch reached */
uint64_t armed_epoch_us = 0;             /**< Absolute time to activate armed mode change */
uint32_t armed_cycle_ms = 0;             /**< New cycle period for armed mode */
uint32_t armed_active_ms = 0;            /**< New active period for armed mode */
uint64_t armed_server_epoch_us = 0;      /**< Bug #82: SERVER's motor epoch for CLIENT antiphase */

// Bug #80 fix: CLIENT cycle counter (moved to file scope for mode change reset)
// Tracks cycles for activation_report correlation - must reset on mode change
static uint32_t client_inactive_cycle_count = 0;

// Bug #81 fix: CLIENT skip INACTIVE wait flag
// After coordinated start wait completes, CLIENT should go directly to ACTIVE
// (the antiphase was already pre-calculated and waited for in coordinated start)
static bool client_skip_inactive_wait = false;

// Phase 6i: Coordinated Start Time
// Both devices agree on a FUTURE timestamp to start motors simultaneously.
// This eliminates the "two activations before other starts" problem.
// Buffer accounts for BLE transmission latency + processing time + margin.
// Phase 6l Fix: Increased from 500ms to 3000ms to account for handshake overhead
// (beacon transmission ~50ms + CLIENT handshake ~500ms + CLIENT_READY ~50ms + margin)
#define COORD_START_DELAY_MS 3000  // 3000ms buffer for coordination (was 500ms)

// ============================================================================
// CLIENT HARDWARE TIMER SYNCHRONIZATION (AD044)
// ============================================================================

/**
 * @brief CLIENT-specific hardware timer for precise antiphase synchronization
 *
 * Design rationale (AD044):
 * - CLIENT must synchronize to SERVER's motor_epoch (external timing reference)
 * - Polling introduces ±1ms jitter from queue receive timeout granularity
 * - Hardware timers achieve ±50μs precision (20× improvement)
 * - Analogous to BLE callbacks responding to external radio events
 *
 * Timer lifecycle:
 * - Created during motor_task initialization
 * - Armed when CLIENT receives beacon with SERVER motor_epoch
 * - Fires callback at exact antiphase moment (halfway through SERVER's cycle)
 * - Cancelled on mode changes or shutdown
 *
 * Safety:
 * - Callback runs in esp_timer task (not ISR), full FreeRTOS API available
 * - Posts message to motor task queue, motor task handles actual transitions
 * - Timer automatically disarms after firing (one-shot mode)
 */
static esp_timer_handle_t client_motor_timer = NULL;

/**
 * @brief Timer callback that fires when CLIENT motor should transition
 *
 * Runs in esp_timer task context (ESP_TIMER_TASK dispatch mode).
 * Posts message to motor task queue to trigger state transition.
 *
 * @param arg Unused (required by esp_timer API)
 */
static void IRAM_ATTR client_motor_timer_callback(void *arg) {
    // Post message to motor task to trigger transition
    // Use FromISR variant for safety (esp_timer task has higher priority)
    task_message_t msg = { .type = MSG_TIMER_MOTOR_TRANSITION };
    BaseType_t xHigherPriorityTaskWoken = pdFALSE;
    xQueueSendFromISR(button_to_motor_queue, &msg, &xHigherPriorityTaskWoken);
    portYIELD_FROM_ISR(xHigherPriorityTaskWoken);
}

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
 * @brief Delay with periodic queue checking for instant mode changes (RELATIVE)
 * @param delay_ms Total delay duration in milliseconds
 * @return true if mode change/shutdown detected (delay interrupted)
 * @return false if delay completed normally
 *
 * NOTE: This function uses RELATIVE timing which accumulates jitter.
 * Use delay_until_target_ms() for precision timing in motor cycles.
 * Kept for backwards compatibility and non-critical delays.
 *
 * Checks button_to_motor_queue every 50ms for:
 * - MSG_MODE_CHANGE: Instant mode switching
 * - MSG_EMERGENCY_SHUTDOWN: Instant shutdown
 *
 * This enables <100ms mode switching latency per AD030
 */
__attribute__((unused))
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

/**
 * @brief Delay until an absolute target time (JITTER-FREE)
 * @param target_ms Absolute target time in milliseconds (from esp_timer_get_time)
 * @return true if mode change/shutdown detected (delay interrupted)
 * @return false if delay completed normally (target reached)
 *
 * Bug #17 Fix: Uses ABSOLUTE time targets instead of relative delays.
 * This eliminates jitter accumulation from vTaskDelay().
 *
 * How it works:
 * - Instead of "delay 250ms from now" (accumulates error)
 * - We do "wait until time X" (no accumulation)
 * - If we're already past the target, returns immediately
 * - Checks queue every 50ms for mode changes
 *
 * Example:
 *   uint32_t cycle_start = esp_timer_get_time() / 1000;
 *   delay_until_target_ms(cycle_start + motor_on_ms);  // Phase 1 end
 *   delay_until_target_ms(cycle_start + motor_on_ms + active_coast_ms);  // Phase 2 end
 */
static bool delay_until_target_ms(uint32_t target_ms) {
    const uint32_t CHECK_INTERVAL_MS = MODE_CHECK_INTERVAL_MS;

    while (true) {
        uint32_t now_ms = (uint32_t)(esp_timer_get_time() / 1000);

        // Already past target? Return immediately
        if (now_ms >= target_ms) {
            return false;  // Target reached
        }

        uint32_t remaining_ms = target_ms - now_ms;
        uint32_t this_delay = (remaining_ms < CHECK_INTERVAL_MS) ? remaining_ms : CHECK_INTERVAL_MS;

        vTaskDelay(pdMS_TO_TICKS(this_delay));

        // Feed watchdog during long waits (INACTIVE can be >2s)
        // AD044 FIX: Without this, watchdog times out during CLIENT drift correction
        esp_task_wdt_reset();

        // Quick check for mode change or shutdown (non-blocking peek)
        task_message_t msg;
        if (xQueuePeek(button_to_motor_queue, &msg, 0) == pdPASS) {
            if (msg.type == MSG_MODE_CHANGE || msg.type == MSG_EMERGENCY_SHUTDOWN) {
                return true; // Mode change or shutdown detected
            }
        }
    }
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
 *
 * IMPORTANT: Motor Active Duty Percent vs Traditional Duty Cycle
 * - This function uses "Motor Active Duty Percent" = % of ACTIVE period with motor ON
 * - Traditional "duty cycle" in electronics = % of TOTAL cycle with signal HIGH
 * - For bilateral alternation, these are DIFFERENT:
 *   • 100% Motor Active Duty = 50% Total Duty (motor on entire ACTIVE period)
 *   • 50% Motor Active Duty = 25% Total Duty
 * - Why different: Bilateral requires 50/50 ACTIVE/INACTIVE split for alternation
 * - AI models: When analyzing this code, "duty" always means Motor Active Duty Percent
 */
// Phase 3a: Updated for bilateral timing with active_coast_ms
static void calculate_mode_timing(mode_t mode, uint32_t *motor_on_ms, uint32_t *active_coast_ms,
                                   uint32_t *inactive_ms, uint8_t *pwm_intensity, bool verbose_logging) {
    if (mode == MODE_CUSTOM) {
        // Mode 4: Custom parameters from BLE
        uint16_t freq_x100 = ble_get_custom_frequency_hz();  // Hz × 100
        uint8_t duty = ble_get_custom_duty_percent();         // Motor Active Duty Percent: 10-100% of ACTIVE period (not total cycle)

        // Calculate FULL cycle period in ms: period = 1000 / (freq / 100)
        uint32_t cycle_ms = 100000 / freq_x100;  // e.g., 100 → 1000ms for 1Hz

        // Split cycle 50/50 into ACTIVE and INACTIVE periods
        uint32_t active_period_ms = cycle_ms / 2;
        *inactive_ms = cycle_ms - active_period_ms;  // Handle odd values

        // Apply Motor Active Duty Percent within ACTIVE period only (linear scaling)
        *motor_on_ms = (active_period_ms * duty) / 100;

        // Active coast is remainder of ACTIVE period
        *active_coast_ms = active_period_ms - *motor_on_ms;

        // PWM intensity for Mode 4 (Custom)
        *pwm_intensity = ble_get_mode4_intensity();

        if (verbose_logging) {
            // Bug #50 Fix: Display both total cycle duty and Motor Active Duty Percent to clarify semantics
            uint8_t total_duty = (*motor_on_ms * 100) / cycle_ms;  // Actual duty cycle of total period
            ESP_LOGI(TAG, "Mode 4 (Custom): %.2fHz, %u%% total duty (%u%% motor active duty) → ACTIVE[%lums motor + %lums coast] | INACTIVE[%lums], PWM=%u%%",
                     freq_x100 / 100.0f, total_duty, duty, *motor_on_ms, *active_coast_ms, *inactive_ms, *pwm_intensity);
        }
    } else {
        // Modes 0-3: Predefined with per-mode PWM intensity
        *motor_on_ms = modes[mode].motor_on_ms;
        *active_coast_ms = modes[mode].active_coast_ms;
        *inactive_ms = modes[mode].inactive_ms;

        // Select PWM intensity based on mode
        switch (mode) {
            case MODE_05HZ_25:
                *pwm_intensity = ble_get_mode0_intensity();
                break;
            case MODE_1HZ_25:
                *pwm_intensity = ble_get_mode1_intensity();
                break;
            case MODE_15HZ_25:
                *pwm_intensity = ble_get_mode2_intensity();
                break;
            case MODE_2HZ_25:
                *pwm_intensity = ble_get_mode3_intensity();
                break;
            default:
                *pwm_intensity = 75;  // Safe fallback (should never reach here)
                ESP_LOGW(TAG, "Unknown mode %d, using fallback PWM intensity 75%%", mode);
                break;
        }
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

    // Motor timing variables (updated when mode changes) - Phase 3a: Bilateral timing
    uint32_t motor_on_ms = 0;        // Motor ON time within ACTIVE period
    uint32_t active_coast_ms = 0;    // Coast time within ACTIVE period
    uint32_t inactive_ms = 0;        // INACTIVE period (always period/2)
    uint8_t pwm_intensity = 0;
    bool show_led = false;
    // Bug #50: Removed client_next_inactive toggle - replaced with position-based state calculation

    // Bug #17 Fix: Absolute time scheduling to eliminate vTaskDelay jitter accumulation
    // cycle_start_ms is recorded at the beginning of each cycle and used to calculate
    // absolute wake times for each phase (motor_on, active_coast, inactive)
    uint32_t cycle_start_ms = 0;

    // Back-EMF sampling flag and storage (inline in ACTIVE state)
    bool sample_backemf = false;
    int raw_mv_active = 0, raw_mv_immed = 0, raw_mv_settled = 0;
    int16_t bemf_active = 0, bemf_immed = 0, bemf_settled = 0;

    // Initialize task-specific timers (session_start_time_ms already set during hardware init)
    last_battery_check_ms = now_ms;
    last_session_time_notify_ms = now_ms;

    // Subscribe to watchdog (soft-fail pattern)
    esp_err_t err = esp_task_wdt_add(NULL);
    if (err != ESP_OK) {
        ESP_LOGW(TAG, "Failed to add to watchdog: %s (continuing anyway)",
                 esp_err_to_name(err));
    }

    // AD044: Create CLIENT hardware timer for precise antiphase synchronization
    // Timer is created at startup but only armed when CLIENT needs to synchronize
    const esp_timer_create_args_t timer_args = {
        .callback = &client_motor_timer_callback,
        .arg = NULL,
        .dispatch_method = ESP_TIMER_TASK,  // Run in esp_timer task (not ISR)
        .name = "client_motor",
        .skip_unhandled_events = false
    };
    err = esp_timer_create(&timer_args, &client_motor_timer);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Failed to create CLIENT motor timer: %s", esp_err_to_name(err));
        // Continue without timer - will fall back to polling-based synchronization
    } else {
        ESP_LOGI(TAG, "CLIENT motor timer created successfully");
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

                        // Phase 3: Simple bilateral alternation - CLIENT starts INACTIVE
                        peer_role_t role = ble_get_peer_role();

                        ESP_LOGI(TAG, "State: PAIRING_WAIT → CHECK_MESSAGES (%s)",
                                 role == PEER_ROLE_SERVER ? "SERVER" :
                                 role == PEER_ROLE_CLIENT ? "CLIENT" : "STANDALONE");

                        // Phase 6i: Coordinated Start Time
                        // SERVER sets motor_epoch as a FUTURE timestamp. Both devices will
                        // wait until this timestamp before starting motors, ensuring simultaneous start.
                        // This eliminates the "two activations before other starts" problem.
                        uint64_t coordinated_start_us = 0;  // Shared between SERVER and CLIENT paths

                        if (role == PEER_ROLE_SERVER) {
                            calculate_mode_timing(current_mode, &motor_on_ms, &active_coast_ms,
                                                 &inactive_ms, &pwm_intensity, false);
                            uint32_t cycle_ms = motor_on_ms + active_coast_ms + inactive_ms;

                            // Bug #24 fix: Wait for time_sync to initialize before setting motor_epoch
                            // The time_sync_task_send_init() message takes time to process
                            ESP_LOGI(TAG, "SERVER: Waiting for time_sync initialization...");
                            int init_wait = 20;  // 20 × 50ms = 1000ms max
                            while (init_wait > 0 && !TIME_SYNC_IS_INITIALIZED()) {
                                vTaskDelay(pdMS_TO_TICKS(50));
                                esp_task_wdt_reset();  // Feed watchdog during wait
                                init_wait--;
                            }
                            if (!TIME_SYNC_IS_INITIALIZED()) {
                                ESP_LOGW(TAG, "SERVER: Time sync init timeout - using local time");
                            }

                            /* Issue #2 Fix: Wait for CLIENT_READY BEFORE setting coordinated start time
                             * This ensures CLIENT has completed handshake and is ready to receive epoch.
                             * Original bug: SERVER set epoch, sent beacon, THEN waited for CLIENT_READY.
                             * Result: CLIENT needed 3500ms but SERVER only gave 3000ms → early activation
                             */

                            // Send initial beacon to trigger CLIENT handshake
                            vTaskDelay(pdMS_TO_TICKS(50));  // Brief delay for time_sync_task to process
                            if (ble_send_time_sync_beacon() == ESP_OK) {
                                ESP_LOGI(TAG, "SERVER: Initial beacon sent - waiting for CLIENT handshake...");

                                // Phase 6 handshake: Wait for CLIENT_READY acknowledgment
                                // Bug #11 fix: Don't reset if CLIENT_READY already buffered and processed
                                if (!time_sync_client_ready_received()) {
                                    time_sync_reset_client_ready();
                                    int ready_wait = 100;  // 100 × 50ms = 5000ms max (give CLIENT time for handshake)
                                    while (ready_wait > 0 && !time_sync_client_ready_received()) {
                                        vTaskDelay(pdMS_TO_TICKS(50));
                                        esp_task_wdt_reset();  // Feed watchdog during long wait
                                        ready_wait--;
                                    }
                                } else {
                                    ESP_LOGI(TAG, "SERVER: CLIENT_READY already received (buffered during init)");
                                }

                                if (time_sync_client_ready_received()) {
                                    ESP_LOGI(TAG, "SERVER: CLIENT_READY received - scheduling coordinated start");

                                    // Get current synchronized time (CLIENT is ready, short delay is fine)
                                    uint64_t current_time_us;
                                    if (time_sync_get_time(&current_time_us) != ESP_OK) {
                                        current_time_us = esp_timer_get_time();
                                    }

                                    /* Phase 6t: Set coordinated start with delay for fast lock acquisition
                                     * CLIENT needs time for:
                                     * - 5 forced beacons @ 200ms = 1000ms
                                     * - Fast lock detection (variance check)
                                     * - Phase calculation prep
                                     * Total: ~1200ms, use 1500ms for safety margin
                                     */
                                    coordinated_start_us = current_time_us + 1500000ULL;  // 1.5s for Phase 6t fast lock
                                    // BUG #47: Don't set motor epoch here - set it at ACTUAL motor start time (after wait)
                                    ESP_LOGI(TAG, "SERVER: Coordinated start in 1500ms (CLIENT fast lock, cycle=%lums)", cycle_ms);

                                    /* BUG #48: Removed coordinated start beacon - causes first-cycle antiphase error
                                     *
                                     * PROBLEM: Beacon sent here contains motor_epoch = 0 (not yet set per Bug #47).
                                     * CLIENT receives beacon, stores epoch = 0, then calculates antiphase using
                                     * wrong epoch. Result: CLIENT activates IN-PHASE with SERVER instead of antiphase.
                                     *
                                     * SOLUTION: Don't send beacon here. MOTOR_STARTED notification (sent after actual
                                     * motor start at line 901-918) already provides correct epoch to CLIENT.
                                     * CLIENT's antiphase pre-calculation (line 787-815) uses MOTOR_STARTED epoch.
                                     *
                                     * Evidence: Serial logs show CLIENT calc "server_pos=54ms" when it should be ~200ms,
                                     * indicating stale/zero epoch used. After fix, CLIENT should calculate correct
                                     * antiphase position on first cycle.
                                     */
                                } else {
                                    ESP_LOGW(TAG, "SERVER: CLIENT_READY timeout - using fallback delay");
                                    // CLIENT_READY timeout: Use LONG delay as fallback
                                    uint64_t current_time_us;
                                    if (time_sync_get_time(&current_time_us) != ESP_OK) {
                                        current_time_us = esp_timer_get_time();
                                    }
                                    coordinated_start_us = current_time_us + (COORD_START_DELAY_MS * 1000ULL);
                                    // BUG #47: Don't set motor epoch here - set it at ACTUAL motor start time (after wait)
                                    ESP_LOGI(TAG, "SERVER: Coordinated start in %dms (fallback, cycle=%lums)",
                                             COORD_START_DELAY_MS, cycle_ms);
                                }
                            } else {
                                ESP_LOGW(TAG, "SERVER: Failed to send initial beacon");
                                coordinated_start_us = 0;  // Clear to skip wait
                            }
                        }

                        // CLIENT: Initialize correction parameters for bilateral alternation
                        // Bug #50: Removed client_next_inactive toggle - state now calculated from SERVER position
                        // BUG FIX: Check role only, not sync state (sync may not be active yet)
                        if (role == PEER_ROLE_CLIENT) {
                            // AD045: Synchronized Independent Operation - no correction state needed
                            ESP_LOGI(TAG, "CLIENT: Bilateral alternation enabled (synchronized independent operation)");

                            /* Issue #2 FIXED: Send CLIENT_READY immediately after time sync init
                             * This breaks the deadlock where:
                             * - SERVER waits for CLIENT_READY before setting epoch
                             * - CLIENT waits for epoch before sending CLIENT_READY
                             * Now CLIENT sends CLIENT_READY as soon as handshake completes.
                             */

                            // Wait for time sync handshake to complete
                            ESP_LOGI(TAG, "CLIENT: Waiting for time sync handshake to complete...");
                            int handshake_wait = 100;  // 100 × 50ms = 5s max
                            while (handshake_wait > 0 && !TIME_SYNC_IS_INITIALIZED()) {
                                vTaskDelay(pdMS_TO_TICKS(50));
                                esp_task_wdt_reset();  // Feed watchdog during long wait (CRITICAL: 5s loop)
                                handshake_wait--;
                            }

                            if (TIME_SYNC_IS_INITIALIZED()) {
                                // Send CLIENT_READY immediately so SERVER can set coordinated start
                                coordination_message_t ready_msg = {
                                    .type = SYNC_MSG_CLIENT_READY,
                                    .timestamp_ms = (uint32_t)(esp_timer_get_time() / 1000),
                                    .payload.battery_level = 0  // Unused for this message type
                                };
                                esp_err_t err = ble_send_coordination_message(&ready_msg);
                                if (err == ESP_OK) {
                                    ESP_LOGI(TAG, "CLIENT: CLIENT_READY sent to SERVER (handshake complete)");
                                } else {
                                    ESP_LOGW(TAG, "CLIENT: Failed to send CLIENT_READY: %s", esp_err_to_name(err));
                                }
                            } else {
                                ESP_LOGW(TAG, "CLIENT: Time sync handshake timeout - proceeding without CLIENT_READY");
                            }

                            // Now wait for SERVER's coordinated start beacon with epoch
                            ESP_LOGI(TAG, "CLIENT: Waiting for SERVER's coordinated start beacon...");
                            uint64_t epoch_us;
                            uint32_t epoch_cycle_ms;
                            int wait_attempts = 100;  // 100 × 50ms = 5s safety timeout
                            while (wait_attempts > 0) {
                                if (time_sync_get_motor_epoch(&epoch_us, &epoch_cycle_ms) == ESP_OK && epoch_cycle_ms > 0) {
                                    coordinated_start_us = epoch_us;  // Store for later wait
                                    ESP_LOGI(TAG, "CLIENT: Received coordinated start time (cycle=%lums)",
                                             epoch_cycle_ms);
                                    break;
                                }
                                vTaskDelay(pdMS_TO_TICKS(50));
                                esp_task_wdt_reset();  // Feed watchdog during 5s wait
                                wait_attempts--;
                            }
                            if (wait_attempts == 0) {
                                ESP_LOGW(TAG, "CLIENT: No coordinated start received - starting immediately");
                            }

                            // Phase 6: Send initial battery to SERVER (immediate, don't wait 60s)
                            int raw_mv;
                            float battery_v;
                            int battery_pct;
                            if (battery_read_voltage(&raw_mv, &battery_v, &battery_pct) == ESP_OK) {
                                coordination_message_t coord_msg = {
                                    .type = SYNC_MSG_CLIENT_BATTERY,
                                    .timestamp_ms = (uint32_t)(esp_timer_get_time() / 1000),
                                    .payload.battery_level = (uint8_t)battery_pct
                                };
                                esp_err_t err = ble_send_coordination_message(&coord_msg);
                                if (err == ESP_OK) {
                                    ESP_LOGI(TAG, "CLIENT: Initial battery sent to SERVER: %d%%", battery_pct);
                                } else {
                                    ESP_LOGW(TAG, "CLIENT: Failed to send initial battery: %s", esp_err_to_name(err));
                                }
                            }
                        }
                        // Bug #50: Removed client_next_inactive initialization (no longer needed)

                        // Phase 6i: Both devices wait until coordinated start time
                        // This ensures SIMULTANEOUS motor activation - no "two activations before other"
                        if (coordinated_start_us > 0 && (role == PEER_ROLE_SERVER || role == PEER_ROLE_CLIENT)) {
                            // Strategy A: Pre-calculated antiphase (potential future optimization)
                            // CLIENT calculates exact antiphase offset immediately, skipping handshake wait
                            // This eliminates early activation + 3-cycle alignment (~6s savings)
                            if (role == PEER_ROLE_CLIENT) {
                                ESP_LOGI(TAG, "CLIENT: Pre-calculating antiphase offset (Strategy A)...");

                                // Check if MOTOR_STARTED already arrived (skip handshake wait if so)
                                uint64_t check_epoch;
                                uint32_t check_cycle;
                                bool motor_started_received = (time_sync_get_motor_epoch(&check_epoch, &check_cycle) == ESP_OK && check_cycle > 0);

                                if (motor_started_received) {
                                    ESP_LOGI(TAG, "CLIENT: MOTOR_STARTED already received, skipping handshake wait");
                                } else {
                                    // Wait for initial sync (RTT measurement) to complete
                                    ESP_LOGI(TAG, "CLIENT: Waiting for handshake or MOTOR_STARTED...");
                                    int sync_wait = 20;  // 20 × 50ms = 1000ms max
                                    while (sync_wait > 0 && !time_sync_is_handshake_complete()) {
                                        // Check if MOTOR_STARTED arrived during wait
                                        if (time_sync_get_motor_epoch(&check_epoch, &check_cycle) == ESP_OK && check_cycle > 0) {
                                            ESP_LOGI(TAG, "CLIENT: MOTOR_STARTED received during wait");
                                            motor_started_received = true;
                                            break;
                                        }
                                        vTaskDelay(pdMS_TO_TICKS(50));
                                        esp_task_wdt_reset();
                                        sync_wait--;
                                    }
                                }

                                int64_t handshake_offset_us = 0;
                                time_sync_get_clock_offset(&handshake_offset_us);
                                if (time_sync_is_handshake_complete()) {
                                    ESP_LOGI(TAG, "CLIENT: Handshake complete, offset=%lld μs", handshake_offset_us);
                                } else if (motor_started_received) {
                                    ESP_LOGI(TAG, "CLIENT: Using MOTOR_STARTED epoch (handshake incomplete), offset=%lld μs", handshake_offset_us);
                                } else {
                                    ESP_LOGW(TAG, "CLIENT: Handshake incomplete after 1s, offset=%lld μs (may be inaccurate)",
                                             handshake_offset_us);
                                }

                                /* AD045: Skip antiphase lock wait - chicken-and-egg problem
                                 *
                                 * OLD (Phase 6s): Waited 5s for antiphase lock before starting motors
                                 * PROBLEM: Lock criteria require motors to be running, but we haven't
                                 * started motors yet! Always timed out, adding 5s delay to startup.
                                 *
                                 * FIX: Remove wait. Coordinated start mechanism is sufficient - both
                                 * devices already agree on when to start based on synchronized clocks.
                                 * Lock monitoring happens DURING operation (passive), not before.
                                 */

                                // Calculate where SERVER currently is in its cycle
                                uint64_t sync_time_us;
                                if (time_sync_get_time(&sync_time_us) == ESP_OK) {
                                    uint64_t server_epoch_us;
                                    uint32_t cycle_ms;
                                    if (time_sync_get_motor_epoch(&server_epoch_us, &cycle_ms) == ESP_OK && cycle_ms > 0) {
                                        uint64_t cycle_us = (uint64_t)cycle_ms * 1000;
                                        uint64_t elapsed_us = sync_time_us - server_epoch_us;
                                        uint64_t server_position_us = elapsed_us % cycle_us;
                                        uint64_t half_period_us = cycle_us / 2;

                                        // Calculate wait time for perfect antiphase
                                        uint64_t target_wait_us;
                                        if (server_position_us < half_period_us) {
                                            // SERVER in ACTIVE phase, wait until half_period
                                            target_wait_us = half_period_us - server_position_us;
                                        } else {
                                            // SERVER in INACTIVE phase, wait until next cycle + half_period
                                            target_wait_us = cycle_us + half_period_us - server_position_us;
                                        }

                                        uint32_t antiphase_wait_ms = (uint32_t)(target_wait_us / 1000);
                                        ESP_LOGI(TAG, "CLIENT: Pre-calculated antiphase: server_pos=%lu/%lu ms (%.1f%%), wait=%lu ms",
                                                 (uint32_t)(server_position_us / 1000), cycle_ms,
                                                 (float)(server_position_us * 100) / cycle_us,
                                                 antiphase_wait_ms);

                                        // Override coordinated_start to use calculated antiphase timing
                                        coordinated_start_us = sync_time_us + target_wait_us;

                                        // AD045: Always use synchronized independent operation (no unclamped alignment cycles)
                                        ESP_LOGI(TAG, "CLIENT: Synchronized independent operation active");
                                    }
                                } else {
                                    ESP_LOGW(TAG, "CLIENT: time_sync_get_time() failed - fallback to standard alignment");
                                }
                            }

                            uint64_t now_us;
                            if (time_sync_get_time(&now_us) != ESP_OK) {
                                ESP_LOGW(TAG, "%s: time_sync_get_time() failed - using local time (SYNC MAY FAIL)",
                                         role == PEER_ROLE_SERVER ? "SERVER" : "CLIENT");
                                now_us = esp_timer_get_time();
                            }
                            // Log sync status for debugging
                            int64_t offset_us = 0;
                            time_sync_get_clock_offset(&offset_us);
                            ESP_LOGI(TAG, "%s: Coordinated start check: target=%llu μs, now=%llu μs, offset=%lld μs",
                                     role == PEER_ROLE_SERVER ? "SERVER" : "CLIENT",
                                     coordinated_start_us, now_us, offset_us);

                            if (coordinated_start_us > now_us) {
                                uint32_t wait_ms = (uint32_t)((coordinated_start_us - now_us) / 1000);
                                ESP_LOGI(TAG, "%s: Waiting %lu ms for coordinated start...",
                                         role == PEER_ROLE_SERVER ? "SERVER" : "CLIENT", wait_ms);

                                // Phase 6: Wait in 50ms chunks to detect MOTOR_STARTED message arrival
                                // Issue #3 fix: Check flag instead of epoch value (handshake and MOTOR_STARTED may have same epoch)
                                // AD045: Always use synchronized independent operation for CLIENT
                                motor_started_received = false;  // Clear flag before wait
                                bool strategy_a_active = (role == PEER_ROLE_CLIENT);  // Always true for CLIENT (synchronized independent)
                                while (wait_ms > 0) {
                                    uint32_t chunk_ms = (wait_ms > 50) ? 50 : wait_ms;
                                    vTaskDelay(pdMS_TO_TICKS(chunk_ms));
                                    esp_task_wdt_reset();  // Feed watchdog

                                    // Bug #46: Only abort wait if NOT using Strategy A (antiphase pre-calculated)
                                    // When Strategy A active, CLIENT must complete full antiphase wait for correct timing
                                    if (motor_started_received && role == PEER_ROLE_CLIENT && !strategy_a_active) {
                                        ESP_LOGI(TAG, "CLIENT: MOTOR_STARTED received - starting motors NOW (abort wait)");
                                        break;  // Abort wait, start immediately
                                    }

                                    wait_ms = (wait_ms > chunk_ms) ? (wait_ms - chunk_ms) : 0;
                                }
                            } else {
                                // BUG #25 diagnostic: If we get here, CLIENT thinks coord start already passed
                                ESP_LOGW(TAG, "%s: Coordinated start already PASSED (target=%llu, now=%llu, diff=%lld μs) - SYNC ISSUE?",
                                         role == PEER_ROLE_SERVER ? "SERVER" : "CLIENT",
                                         coordinated_start_us, now_us,
                                         (int64_t)now_us - (int64_t)coordinated_start_us);
                            }
                            ESP_LOGI(TAG, "%s: Coordinated start time reached - motors starting NOW",
                                     role == PEER_ROLE_SERVER ? "SERVER" : "CLIENT");

                            // BUG #47 FIX: Set motor epoch at ACTUAL motor start time (not target time)
                            // This ensures CLIENT's antiphase calculation uses correct reference point
                            //
                            // BUG #49 FIX: Use SYNCHRONIZED time, not local time
                            // All phase calculations use time_sync_get_time() (synchronized time domain).
                            // Epoch must be in same time domain or drift calculations will be wrong.
                            uint64_t actual_start_us;
                            if (time_sync_get_time(&actual_start_us) != ESP_OK) {
                                // Fallback to local time if sync not available (should never happen)
                                ESP_LOGW(TAG, "%s: time_sync_get_time() failed - using local time for epoch (SYNC MAY FAIL)",
                                         role == PEER_ROLE_SERVER ? "SERVER" : "CLIENT");
                                actual_start_us = esp_timer_get_time();
                            }

                            // Calculate cycle_ms from current mode timing
                            uint32_t temp_motor_on_ms, temp_active_coast_ms, temp_inactive_ms;
                            uint8_t temp_pwm_intensity;
                            calculate_mode_timing(current_mode, &temp_motor_on_ms, &temp_active_coast_ms,
                                                 &temp_inactive_ms, &temp_pwm_intensity, false);
                            uint32_t current_cycle_ms = temp_motor_on_ms + temp_active_coast_ms + temp_inactive_ms;

                            // AD045: Only SERVER sets motor epoch (authoritative source of truth)
                            // Bug #49 fix (coordinated start): CLIENT receives epoch via MOTOR_STARTED notification
                            // CLIENT must NOT overwrite SERVER's epoch with its own start time
                            if (role == PEER_ROLE_SERVER) {
                                time_sync_set_motor_epoch(actual_start_us, current_cycle_ms);
                                ESP_LOGI(TAG, "SERVER: Motor epoch set to actual start time: %llu μs (cycle=%lu ms)",
                                         actual_start_us, current_cycle_ms);
                            } else {
                                ESP_LOGI(TAG, "CLIENT: Using motor epoch from SERVER (coordinated start)");
                                // Bug #81 fix: Skip INACTIVE wait on first cycle
                                // Antiphase was already pre-calculated and waited for in coordinated start
                                client_skip_inactive_wait = true;
                            }

                            /* Phase 6: SERVER sends immediate motor epoch notification
                             * This eliminates the 9.5s delay for late-joining CLIENTs waiting for periodic beacons.
                             * CLIENT can receive epoch and start motors within 100-200ms.
                             */
                            if (role == PEER_ROLE_SERVER) {
                                uint64_t motor_epoch_us;
                                uint32_t motor_cycle_ms;
                                if (time_sync_get_motor_epoch(&motor_epoch_us, &motor_cycle_ms) == ESP_OK && motor_cycle_ms > 0) {
                                    coordination_message_t motor_started_msg = {
                                        .type = SYNC_MSG_MOTOR_STARTED,
                                        .timestamp_ms = (uint32_t)(esp_timer_get_time() / 1000),
                                        .payload.motor_started = {
                                            .motor_epoch_us = motor_epoch_us,
                                            .motor_cycle_ms = motor_cycle_ms
                                        }
                                    };
                                    esp_err_t err = ble_send_coordination_message(&motor_started_msg);
                                    if (err == ESP_OK) {
                                        ESP_LOGI(TAG, "SERVER: MOTOR_STARTED notification sent (epoch=%llu, cycle=%lu)",
                                                 motor_epoch_us, motor_cycle_ms);
                                    } else {
                                        ESP_LOGW(TAG, "SERVER: Failed to send MOTOR_STARTED: %s", esp_err_to_name(err));
                                    }
                                }
                            }
                        }

                        state = MOTOR_STATE_CHECK_MESSAGES;
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

                        // Phase 6: CLIENT sends battery to SERVER for PWA client_battery characteristic
                        if (ble_get_peer_role() == PEER_ROLE_CLIENT && ble_is_peer_connected()) {
                            coordination_message_t coord_msg = {
                                .type = SYNC_MSG_CLIENT_BATTERY,
                                .timestamp_ms = (uint32_t)(esp_timer_get_time() / 1000),
                                .payload.battery_level = (uint8_t)battery_pct
                            };
                            esp_err_t err = ble_send_coordination_message(&coord_msg);
                            if (err != ESP_OK) {
                                ESP_LOGW(TAG, "Failed to send client battery: %s", esp_err_to_name(err));
                            }
                        }

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

                /* Phase 6s: Periodic antiphase lock monitoring (CLIENT only)
                 *
                 * Check lock status every 10 cycles during operation. If lock is lost
                 * (stale beacons, filter issue, etc.), request forced beacons from SERVER
                 * to re-establish stable synchronization.
                 *
                 * This prevents long-term drift or desynchronization during sessions.
                 */
                static uint32_t lock_check_cycle_count = 0;
                static bool last_lock_status = true;  // Assume locked initially
                peer_role_t current_role = ble_get_peer_role();

                if (current_role == PEER_ROLE_CLIENT) {
                    lock_check_cycle_count++;

                    if (lock_check_cycle_count >= 10) {
                        bool current_lock_status = time_sync_is_antiphase_locked();

                        // Log lock status changes only (avoid spam)
                        if (current_lock_status != last_lock_status) {
                            if (current_lock_status) {
                                ESP_LOGI(TAG, "CLIENT: Antiphase lock RESTORED");
                            } else {
                                ESP_LOGW(TAG, "CLIENT: Antiphase lock LOST (will re-establish via beacons)");
                                /* Note: Forced beacons are automatically triggered on mode changes
                                 * via MOTOR_STARTED messages (Phase 6r). No explicit request needed.
                                 * Lock will naturally re-establish within 1-2 seconds via existing
                                 * beacon mechanism. */
                            }
                            last_lock_status = current_lock_status;
                        }

                        lock_check_cycle_count = 0;  // Reset counter
                    }
                }

                // Check for emergency shutdown and mode changes
                task_message_t msg;
                while (xQueueReceive(button_to_motor_queue, &msg, 0) == pdPASS) {
                    if (msg.type == MSG_EMERGENCY_SHUTDOWN) {
                        ESP_LOGI(TAG, "Emergency shutdown");

                        // AD044: Cancel CLIENT timer on shutdown
                        if (client_motor_timer != NULL && esp_timer_is_active(client_motor_timer)) {
                            esp_timer_stop(client_motor_timer);
                            ESP_LOGD(TAG, "CLIENT timer cancelled (shutdown)");
                        }

                        state = MOTOR_STATE_SHUTDOWN;
                        break;
                    } else if (msg.type == MSG_TIMER_MOTOR_TRANSITION) {
                        // AD044: CLIENT hardware timer fired - precise antiphase moment reached
                        // This message indicates the exact time for CLIENT to transition to ACTIVE
                        // No action needed here - just log and continue to normal state transition
                        ESP_LOGD(TAG, "CLIENT: Hardware timer fired (antiphase moment)");
                        // Fall through to normal ACTIVE transition below
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
                            ESP_LOGI(TAG, "Mode change requested: %s → %s", modes[current_mode].name, modes[new_mode].name);
                            led_indication_active = true;
                            led_indication_start_ms = now;
                            last_mode_change_ms = now;

                            // AD044: Cancel CLIENT timer on mode change (will be re-armed with new timing)
                            if (client_motor_timer != NULL && esp_timer_is_active(client_motor_timer)) {
                                esp_timer_stop(client_motor_timer);
                                ESP_LOGD(TAG, "CLIENT timer cancelled (mode change)");
                            }

                            peer_role_t role = ble_get_peer_role();

                            // AD045: Two-phase commit protocol for synchronized mode changes
                            if (role == PEER_ROLE_SERVER && TIME_SYNC_IS_ACTIVE()) {
                                // SERVER: Calculate new mode timing and send proposal
                                uint32_t mode_motor_on, mode_active_coast, mode_inactive;
                                uint8_t mode_pwm;
                                calculate_mode_timing(new_mode, &mode_motor_on, &mode_active_coast,
                                                     &mode_inactive, &mode_pwm, false);

                                uint32_t new_cycle_ms = mode_motor_on + mode_active_coast + mode_inactive;
                                uint32_t new_active_ms = mode_motor_on + mode_active_coast;
                                uint64_t now_us;

                                if (time_sync_get_time(&now_us) == ESP_OK) {
                                    // Calculate future epochs (2 seconds from now for coordination)
                                    uint64_t server_epoch_us = now_us + 2000000ULL;  // 2s buffer
                                    uint64_t half_cycle_us = ((uint64_t)new_cycle_ms * 1000ULL) / 2;
                                    uint64_t client_epoch_us = server_epoch_us + half_cycle_us;

                                    // Send mode change proposal to CLIENT
                                    coordination_message_t proposal = {
                                        .type = SYNC_MSG_MODE_CHANGE_PROPOSAL,
                                        .timestamp_ms = (uint32_t)(esp_timer_get_time() / 1000),
                                        .payload.mode_proposal = {
                                            .new_mode = new_mode,
                                            .new_cycle_ms = new_cycle_ms,
                                            .new_active_ms = new_active_ms,
                                            .server_epoch_us = server_epoch_us,
                                            .client_epoch_us = client_epoch_us
                                        }
                                    };

                                    esp_err_t err = ble_send_coordination_message(&proposal);
                                    if (err == ESP_OK) {
                                        // Arm mode change for SERVER epoch
                                        mode_change_armed = true;
                                        armed_new_mode = new_mode;
                                        armed_epoch_us = server_epoch_us;
                                        armed_cycle_ms = new_cycle_ms;
                                        armed_active_ms = new_active_ms;

                                        ESP_LOGI(TAG, "SERVER: Mode change proposal sent (server_epoch=%llu, client_epoch=%llu)",
                                                 server_epoch_us, client_epoch_us);
                                    } else {
                                        ESP_LOGW(TAG, "SERVER: Failed to send mode change proposal: %s", esp_err_to_name(err));
                                    }
                                }
                            } else {
                                // Standalone or CLIENT
                                if (TIME_SYNC_IS_ACTIVE()) {
                                    // CLIENT: Mode change already armed by time_sync_task (from proposal)
                                    // Bug #50 fix: Don't execute here - wait for synchronized epoch
                                    // Motors will pause during arming period (see CHECK_MESSAGES state)
                                    ESP_LOGI(TAG, "Mode change armed: %s → %s (will execute at synchronized epoch)",
                                             modes[current_mode].name, modes[new_mode].name);
                                    // Do NOT change current_mode here - wait for synchronized execution
                                } else {
                                    // Standalone (no peer): Change mode immediately
                                    current_mode = new_mode;
                                    ESP_LOGI(TAG, "Mode: %s (standalone)", modes[current_mode].name);
                                }
                            }
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

                // AD045: Check if armed mode change has reached its epoch
                if (mode_change_armed && TIME_SYNC_IS_ACTIVE()) {
                    uint64_t current_time_us;
                    if (time_sync_get_time(&current_time_us) == ESP_OK) {
                        if (current_time_us >= armed_epoch_us) {
                            // Epoch reached - execute synchronized mode change
                            current_mode = armed_new_mode;

                            peer_role_t role = ble_get_peer_role();
                            const char* role_str = (role == PEER_ROLE_SERVER) ? "SERVER" : "CLIENT";

                            ESP_LOGI(TAG, "%s: Synchronized mode change executed at epoch %llu",
                                     role_str, current_time_us);
                            ESP_LOGI(TAG, "Mode: %s (synchronized)", modes[current_mode].name);

                            // AD045: SERVER updates motor_epoch for instant antiphase coordination
                            // Bug #49 fix: CLIENT must NOT update epoch (only SERVER is authoritative)
                            // Bug #82 fix: CLIENT sets epoch from proposal for immediate antiphase
                            if (role == PEER_ROLE_SERVER) {
                                // SERVER: Set motor_epoch to its own start time
                                time_sync_set_motor_epoch(armed_epoch_us, armed_cycle_ms);
                                ESP_LOGI(TAG, "SERVER: Motor epoch updated to %llu (cycle=%lu ms)",
                                         armed_epoch_us, armed_cycle_ms);
                            } else if (role == PEER_ROLE_CLIENT && armed_server_epoch_us > 0) {
                                // Bug #82 fix: CLIENT sets motor_epoch from proposal
                                // Without this, CLIENT uses old epoch for antiphase calculation
                                time_sync_set_motor_epoch(armed_server_epoch_us, armed_cycle_ms);
                                ESP_LOGI(TAG, "CLIENT: Motor epoch set to server's epoch %llu (cycle=%lu ms)",
                                         armed_server_epoch_us, armed_cycle_ms);

                                // Bug #83 fix: CLIENT skips INACTIVE wait after mode change
                                // CLIENT's armed_epoch_us (client_epoch) is already half-cycle after server_epoch
                                // When CLIENT executes mode change at this epoch, it's at perfect antiphase
                                // Going to INACTIVE and recalculating would add an extra cycle delay
                                client_skip_inactive_wait = true;
                            }

                            // Bug #80 fix: Reset CLIENT cycle counter on mode change
                            // (Prevents cycle divergence in activation reports)
                            client_inactive_cycle_count = 0;

                            // Disarm mode change
                            mode_change_armed = false;
                            armed_new_mode = MODE_05HZ_25;
                            armed_epoch_us = 0;
                            armed_cycle_ms = 0;
                            armed_active_ms = 0;
                            armed_server_epoch_us = 0;  // Bug #82 fix

                            // Update LED indication
                            led_indication_active = true;
                            led_indication_start_ms = now;
                            last_mode_change_ms = now;
                        }
                    }
                }

                // Phase 6: Check if BLE params changed (Mode 4 frequency/duty via GATT write)
                // SERVER must republish motor epoch ONLY if cycle period changed (frequency)
                // Duty/PWM changes should NOT update epoch (breaks phase alignment)
                static uint32_t prev_cycle_ms = 0;  // Track previous cycle to detect frequency changes
                if (ble_params_updated) {
                    ble_params_updated = false;  // Clear flag

                    // Calculate current cycle period
                    uint32_t cycle_ms = motor_on_ms + active_coast_ms + inactive_ms;
                    bool cycle_changed = (cycle_ms != prev_cycle_ms && prev_cycle_ms != 0);

                    // If SERVER in MODE_CUSTOM, check if cycle period changed
                    peer_role_t params_role = ble_get_peer_role();
                    if (params_role == PEER_ROLE_SERVER && current_mode == MODE_CUSTOM && TIME_SYNC_IS_ACTIVE()) {
                        // Only update motor epoch if FREQUENCY changed (cycle period changed)
                        // Duty/PWM changes should NOT reset phase reference
                        if (cycle_changed) {
                            uint64_t motor_epoch_us;
                            if (time_sync_get_time(&motor_epoch_us) == ESP_OK) {
                                time_sync_set_motor_epoch(motor_epoch_us, cycle_ms);
                                ESP_LOGI(TAG, "SERVER: Frequency changed - motor epoch updated (cycle=%lums)", cycle_ms);

                                // Send immediate beacon so CLIENT can sync right away
                                if (ble_send_time_sync_beacon() == ESP_OK) {
                                    ESP_LOGI(TAG, "SERVER: Immediate beacon sent for frequency change");
                                }

                                // Bug #32 fix: Send motor epoch to CLIENT immediately
                                coordination_message_t motor_started_msg = {
                                    .type = SYNC_MSG_MOTOR_STARTED,
                                    .timestamp_ms = (uint32_t)(esp_timer_get_time() / 1000),
                                    .payload.motor_started = {
                                        .motor_epoch_us = motor_epoch_us,
                                        .motor_cycle_ms = cycle_ms
                                    }
                                };
                                esp_err_t err = ble_send_coordination_message(&motor_started_msg);
                                if (err == ESP_OK) {
                                    ESP_LOGI(TAG, "SERVER: MOTOR_STARTED sent for frequency change (epoch=%llu)", motor_epoch_us);
                                } else {
                                    ESP_LOGW(TAG, "SERVER: Failed to send MOTOR_STARTED: %s", esp_err_to_name(err));
                                }
                            }
                        } else {
                            ESP_LOGI(TAG, "SERVER: Duty/PWM changed - epoch unchanged (cycle=%lums)", cycle_ms);
                        }
                        prev_cycle_ms = cycle_ms;
                    } else if (params_role == PEER_ROLE_CLIENT && current_mode == MODE_CUSTOM) {
                        // Bug #50: No phase reset needed - position-based state calculation auto-adapts
                        if (cycle_changed) {
                            ESP_LOGI(TAG, "CLIENT: Frequency changed - position-based state will auto-adjust");
                        } else {
                            ESP_LOGI(TAG, "CLIENT: Duty/PWM changed - phase unchanged");
                        }
                        prev_cycle_ms = cycle_ms;
                    } else {
                        // Track cycle for STANDALONE or first time
                        prev_cycle_ms = cycle_ms;
                    }
                }

                // Bug #53 fix: Calculate timing AFTER mode change execution
                // Bug #52 incorrectly placed this BEFORE message handling, meaning timing was
                // calculated from OLD current_mode before mode change updated it.
                // Correct sequence: 1) Process messages → 2) Execute mode change → 3) Calculate timing
                //
                // Show LED logic:
                // - Mode 5 (CUSTOM): LED blinks for entire session if BLE LED enabled
                // - Other modes: LED blinks for first 10 seconds after mode change
                if (current_mode == MODE_CUSTOM) {
                    show_led = ble_get_led_enable();  // Always use BLE setting for custom mode
                } else {
                    show_led = led_indication_active;  // 10-second timeout for other modes
                }

                // Update back-EMF sampling flag (first 10 seconds after mode change OR beacon)
                bool mode_change_bemf = led_indication_active && ((now - led_indication_start_ms) < LED_INDICATION_TIME_MS);
                bool beacon_bemf = beacon_bemf_logging_active && ((now - beacon_bemf_start_ms) < LED_INDICATION_TIME_MS);
                sample_backemf = mode_change_bemf || beacon_bemf;

                // Calculate motor parameters from BLE settings (verbose logging gated with BEMF)
                // Phase 3a: Bilateral timing with active_coast_ms and inactive_ms
                calculate_mode_timing(current_mode, &motor_on_ms, &active_coast_ms, &inactive_ms, &pwm_intensity, sample_backemf);

                // BUG FIX (Phase 3a): Removed ongoing bilateral offset code that changed frequency
                // Initial offset (lines 335-351 in PAIRING state) is sufficient for phase alignment
                // Devices naturally maintain phase offset as long as they run at same frequency

                // Disable LED indication after 10 seconds (non-custom modes only)
                if (current_mode != MODE_CUSTOM && led_indication_active && ((now - led_indication_start_ms) >= LED_INDICATION_TIME_MS)) {
                    led_indication_active = false;
                    led_clear();
                    ESP_LOGI(TAG, "LED off (battery conservation)");
                }

                // Disable beacon-triggered back-EMF logging after 10 seconds
                if (beacon_bemf_logging_active && ((now - beacon_bemf_start_ms) >= LED_INDICATION_TIME_MS)) {
                    beacon_bemf_logging_active = false;
                    ESP_LOGI(TAG, "Beacon BEMF logging complete (10s window ended)");
                }

                // Don't transition to ACTIVE if shutting down
                if (state == MOTOR_STATE_SHUTDOWN) {
                    break;
                }

                // Bug #50 fix: Pause motors during mode change arming
                // Both devices enter PAUSED state until synchronized epoch is reached
                // This prevents CLIENT from running NEW pattern while SERVER runs OLD pattern
                if (mode_change_armed) {
                    ESP_LOGD(TAG, "Motors paused (mode change armed for epoch %llu)", armed_epoch_us);
                    vTaskDelay(pdMS_TO_TICKS(50));  // Wait and check again
                    continue;  // Stay in CHECK_MESSAGES
                }

                // AD045: Synchronized Independent Operation
                // CLIENT and SERVER use different state machine initialization
                peer_role_t role = ble_get_peer_role();
                if (role == PEER_ROLE_CLIENT) {
                    // Bug #81/#83 fix: Skip INACTIVE wait after coordinated start or mode change
                    // CLIENT's epoch timing already places it at perfect antiphase
                    if (client_skip_inactive_wait) {
                        client_skip_inactive_wait = false;  // Clear flag (one-shot)
                        ESP_LOGI(TAG, "CLIENT: Skipping INACTIVE (antiphase pre-calculated)");
                        state = MOTOR_STATE_ACTIVE;
                    } else {
                        // CLIENT: Normal cycle - go to INACTIVE state
                        // INACTIVE state handler calculates target time from SERVER epoch
                        // and transitions to ACTIVE when target is reached
                        state = MOTOR_STATE_INACTIVE;
                    }
                } else {
                    // SERVER/STANDALONE: Always start with ACTIVE
                    // Log ACTIVE/INACTIVE cycle to match CLIENT logging for sync verification
                    // Tech Spike: Continuous logging for single-device drift baseline measurement
                    #ifdef ENABLE_SINGLE_DEVICE_DRIFT_BASELINE
                    // Log continuously (no peer connection required) for drift baseline
                    if (role == PEER_ROLE_SERVER || role == PEER_ROLE_NONE) {
                        ESP_LOGI(TAG, "SERVER: Cycle starts ACTIVE (next will be INACTIVE)");
                    }
                    #else
                    // Production: Only log when peer is connected
                    if (role == PEER_ROLE_SERVER) {
                        ESP_LOGI(TAG, "SERVER: Cycle starts ACTIVE (next will be INACTIVE)");
                    }
                    #endif
                    state = MOTOR_STATE_ACTIVE;
                }
                break;
            }

            // ================================================================
            // STATE: ACTIVE
            // ================================================================
            case MOTOR_STATE_ACTIVE: {
                // Bug #17 Fix: Record cycle start time for ABSOLUTE timing
                // All subsequent delays are calculated relative to this timestamp
                // This eliminates vTaskDelay jitter accumulation
                cycle_start_ms = (uint32_t)(esp_timer_get_time() / 1000);

                // AD045: Motor epoch is set once at coordinated start, not updated every cycle
                // CLIENT calculates target times from the ORIGINAL epoch
                // Per-cycle updates would break synchronized independent operation
                // Motor epoch only changes on:
                //   1. Coordinated start (PAIRING_WAIT exit)
                //   2. Synchronized mode changes (two-phase commit)
                // Removed Phase 3 per-cycle epoch update for AD045

                // Start motor in current direction (determined by is_forward_direction flag)
                if (is_forward_direction) {
                    motor_set_forward(pwm_intensity, sample_backemf);
                } else {
                    motor_set_reverse(pwm_intensity, sample_backemf);
                }
                if (show_led) led_set_mode_color(current_mode);

                // Phase 3a: ACTIVE period = motor_on_ms + active_coast_ms
                // Back-EMF sampling happens DURING this period without affecting timing
                // Bug #17 Fix: Use ABSOLUTE time targets (no jitter accumulation)

                // Step 1: Motor ON until absolute target time
                uint32_t motor_off_target_ms = cycle_start_ms + motor_on_ms;
                if (delay_until_target_ms(motor_off_target_ms)) {
                    motor_coast(sample_backemf);
                    led_clear();
                    state = MOTOR_STATE_CHECK_MESSAGES;
                    break;
                }

                // Step 2: Sample during motor active (before coast) for diagnostic
                // This shows PWM average voltage on sense circuit input, proving circuit works
                if (sample_backemf) {
                    backemf_read(&raw_mv_active, &bemf_active);
                }

                // Step 3: Coast motor (turn OFF)
                motor_coast(sample_backemf);
                led_clear();

                // Step 4: Active coast period (remainder of ACTIVE period)
                // Bug #17 Fix: Use absolute target for end of ACTIVE period
                uint32_t active_end_target_ms = cycle_start_ms + motor_on_ms + active_coast_ms;

                // Phase 6j: CLIENT catch-up correction - PERMANENTLY DISABLED
                // Bug #26: Attempted to apply drift corrections during COAST state by
                // shortening the ACTIVE coast period. The calculation used INACTIVE
                // semantics during COAST state, causing inverted corrections that made
                // motor overlap WORSE. After multiple attempts to fix, this approach was
                // abandoned in favor of INACTIVE-only corrections (which work reliably).
                // The inline drift calculation in INACTIVE state (below) is the working
                // solution for bilateral antiphase coordination.
#if 0  // DISABLED - see Bug #26
                peer_role_t coast_role = ble_get_peer_role();
                if (coast_role == PEER_ROLE_CLIENT && !skip_drift_correction_once) {
                    int32_t drift_ms = 0;
                    uint32_t full_cycle_ms = motor_on_ms + active_coast_ms + inactive_ms;

                    if (calculate_drift_from_epoch(inactive_ms, full_cycle_ms, &drift_ms)) {
                        // Only apply catch-up (negative drift) here
                        // Slow-down (positive drift) is handled in INACTIVE state
                        if (drift_ms < 0) {
                            int32_t catch_up_ms = -drift_ms;  // Make positive

                            // Apply PD damping (same as INACTIVE state)
                            int32_t drift_change = 0;
                            if (last_drift_valid) {
                                drift_change = drift_ms - last_drift_ms;
                            }
                            int32_t p_term = (catch_up_ms * CORRECTION_DAMPING_PCT) / 100;
                            int32_t d_term = ((-drift_change) * DERIVATIVE_DAMPING_PCT) / 100;
                            int32_t damped_catch_up = p_term - d_term;
                            if (damped_catch_up < 0) damped_catch_up = 0;

                            // Update PD state
                            last_drift_ms = drift_ms;
                            last_drift_valid = true;

                            // Calculate available headroom
                            uint32_t coast_headroom = (active_coast_ms > MIN_COAST_MS)
                                ? (active_coast_ms - MIN_COAST_MS) : 0;

                            // Apply correction, clamped to available headroom
                            uint32_t actual_catch_up = 0;
                            if ((uint32_t)damped_catch_up <= coast_headroom) {
                                // Fits within coast headroom
                                actual_catch_up = (uint32_t)damped_catch_up;
                                last_correction_type = CORRECTION_COAST_SHORTEN;
                            } else if (coast_headroom > 0) {
                                // Use all available coast headroom
                                actual_catch_up = coast_headroom;
                                last_correction_type = CORRECTION_COAST_SHORTEN;
                                // Note: Could extend to borrow from motor_on here (Phase 6b)
                            }

                            if (actual_catch_up > 0) {
                                active_end_target_ms -= actual_catch_up;
                                last_correction_amount_ms = -(int32_t)actual_catch_up;

                                // Log significant corrections (>10% of coast)
                                if (actual_catch_up > active_coast_ms / 10) {
                                    ESP_LOGI(TAG, "CLIENT COAST CATCH-UP: drift=%+ld, damped=%ld, applied=-%lu ms",
                                             (long)drift_ms, (long)damped_catch_up, actual_catch_up);
                                }
                            }
                        } else {
                            // Positive drift (ahead) - will be handled in INACTIVE
                            last_correction_type = CORRECTION_NONE;
                            last_correction_amount_ms = 0;
                        }
                    }
                }
#endif  // DISABLED - see Bug #26

                // If sampling, take back-EMF readings DURING this time
                if (sample_backemf) {
                    // Sample #1: Immediately after coast starts
                    backemf_read(&raw_mv_immed, &bemf_immed);

                    // Wait for back-EMF to settle (absolute target)
                    uint32_t settle_target_ms = cycle_start_ms + motor_on_ms + BACKEMF_SETTLE_MS;
                    // Clamp settle target to not exceed active_end
                    if (settle_target_ms > active_end_target_ms) {
                        settle_target_ms = active_end_target_ms;
                    }

                    if (delay_until_target_ms(settle_target_ms)) {
                        state = MOTOR_STATE_CHECK_MESSAGES;
                        break;
                    }

                    // Sample #2: Settled back-EMF reading
                    backemf_read(&raw_mv_settled, &bemf_settled);

                    // Log readings with direction label (3 samples: active, immediate, settled)
                    if (is_forward_direction) {
                        ESP_LOGI(TAG, "FWD: %dmV→%+dmV | %dmV→%+dmV | %dmV→%+dmV",
                                 raw_mv_active, bemf_active,
                                 raw_mv_immed, bemf_immed,
                                 raw_mv_settled, bemf_settled);
                    } else {
                        ESP_LOGI(TAG, "REV: %dmV→%+dmV | %dmV→%+dmV | %dmV→%+dmV",
                                 raw_mv_active, bemf_active,
                                 raw_mv_immed, bemf_immed,
                                 raw_mv_settled, bemf_settled);
                    }

                    // Wait until end of ACTIVE period (absolute target)
                    if (delay_until_target_ms(active_end_target_ms)) {
                        state = MOTOR_STATE_CHECK_MESSAGES;
                        break;
                    }
                } else {
                    // No sampling - just wait until end of ACTIVE period
                    if (delay_until_target_ms(active_end_target_ms)) {
                        state = MOTOR_STATE_CHECK_MESSAGES;
                        break;
                    }
                }

                // Transition: CLIENT vs SERVER have different flows
                // SERVER: ACTIVE → INACTIVE → CHECK_MESSAGES (standard flow)
                // CLIENT: ACTIVE → CHECK_MESSAGES (skips INACTIVE state here, uses it via toggle)
                peer_role_t end_role = ble_get_peer_role();
                if (end_role == PEER_ROLE_CLIENT) {
                    // CLIENT: Skip INACTIVE after ACTIVE, go directly to CHECK_MESSAGES
                    // Toggle will make us start with INACTIVE next iteration
                    // Bug #22 FIX: Do NOT toggle direction here - CLIENT already toggles in
                    // INACTIVE state (line 1129). Double-toggle caused CLIENT to always use
                    // same direction (toggled twice = back to original value each cycle).
                    state = MOTOR_STATE_CHECK_MESSAGES;
                } else {
                    // SERVER/STANDALONE: Normal flow to INACTIVE
                    state = MOTOR_STATE_INACTIVE;
                }
                break;
            }

            // NOTE: BEMF_IMMEDIATE and COAST_SETTLE states removed (Nov 24, 2025)
            // Back-EMF sampling is now done inline in ACTIVE state without separate states
            // Separate states caused timing issues and were never transitioned to

            // ================================================================
            // STATE: INACTIVE
            // ================================================================
            case MOTOR_STATE_INACTIVE: {
                // AD045: Synchronized Independent Operation
                // Both devices calculate transitions from synced clocks independently
                // No cycle-by-cycle corrections - passive monitoring only
                //
                // SERVER: Uses fixed inactive_ms delay (it's the authoritative time reference)
                // CLIENT: Calculates target time from SERVER's motor epoch (antiphase = epoch + half_cycle)

                uint32_t wait_ms = inactive_ms;  // Default for SERVER/standalone
                uint32_t inactive_start_ms = 0;  // For CLIENT absolute timing

                // Bug #54a fix: Static variables for activation report (sent AFTER wait, not before)
                // Bug #80: client_inactive_cycle_count moved to file scope for mode change reset
                static uint64_t client_target_for_report = 0;
                static bool send_activation_report = false;

                peer_role_t inactive_role = ble_get_peer_role();

                // Log INACTIVE state for SERVER to match CLIENT logging
                #ifdef ENABLE_SINGLE_DEVICE_DRIFT_BASELINE
                // Log continuously (no peer connection required) for drift baseline
                if (inactive_role == PEER_ROLE_SERVER || inactive_role == PEER_ROLE_NONE) {
                    ESP_LOGI(TAG, "SERVER: Cycle starts INACTIVE (next will be ACTIVE)");
                }
                #else
                // Production: Only log when peer is connected
                if (inactive_role == PEER_ROLE_SERVER) {
                    ESP_LOGI(TAG, "SERVER: Cycle starts INACTIVE (next will be ACTIVE)");
                }
                #endif

                // CLIENT records start time for absolute wait
                // (SERVER uses cycle_start_ms from ACTIVE state)
                if (inactive_role == PEER_ROLE_CLIENT) {
                    inactive_start_ms = (uint32_t)(esp_timer_get_time() / 1000);
                }

                // AD045: Synchronized Independent Operation for CLIENT
                // Calculate target time from SERVER epoch, no corrections
                if (inactive_role == PEER_ROLE_CLIENT) {
                    uint64_t sync_time_us = 0;
                    uint64_t server_epoch_us = 0;
                    uint32_t cycle_ms = 0;

                    if (time_sync_get_time(&sync_time_us) == ESP_OK &&
                        time_sync_get_motor_epoch(&server_epoch_us, &cycle_ms) == ESP_OK &&
                        cycle_ms > 0) {

                        uint64_t cycle_us = (uint64_t)cycle_ms * 1000ULL;
                        uint64_t half_cycle_us = cycle_us / 2;

                        // Calculate how many complete cycles have elapsed since epoch
                        uint64_t elapsed_us = sync_time_us - server_epoch_us;
                        uint64_t cycles_since_epoch = elapsed_us / cycle_us;

                        // Calculate when SERVER started current cycle
                        uint64_t server_current_cycle_start_us = server_epoch_us + (cycles_since_epoch * cycle_us);

                        // CLIENT target: Start ACTIVE exactly half-cycle after SERVER's cycle start
                        // This achieves perfect antiphase (SERVER INACTIVE while CLIENT ACTIVE)
                        uint64_t client_target_active_us = server_current_cycle_start_us + half_cycle_us;

                        // If target already passed, advance to next cycle's antiphase point
                        if (client_target_active_us <= sync_time_us) {
                            client_target_active_us += cycle_us;
                        }

                        // Calculate wait time to reach target
                        uint64_t target_wait_us = client_target_active_us - sync_time_us;

                        // AD044: Arm hardware timer for precise antiphase synchronization
                        // Timer provides microsecond precision (no polling jitter)
                        if (client_motor_timer != NULL) {
                            // Cancel any pending timer first
                            if (esp_timer_is_active(client_motor_timer)) {
                                esp_timer_stop(client_motor_timer);
                            }

                            // Arm one-shot timer to fire at exact target time
                            esp_err_t timer_err = esp_timer_start_once(client_motor_timer, target_wait_us);
                            if (timer_err != ESP_OK) {
                                ESP_LOGW(TAG, "CLIENT: Failed to arm timer: %s (falling back to polling)",
                                         esp_err_to_name(timer_err));
                            }
                        }

                        // Convert to ms for waiting (sanity check: 0-5000ms range)
                        uint32_t calculated_ms = (uint32_t)(target_wait_us / 1000);
                        if (calculated_ms > 5000) {
                            ESP_LOGW(TAG, "CLIENT: Calculated wait %lu ms exceeds 5s, using nominal %lu ms",
                                     calculated_ms, inactive_ms);
                            wait_ms = inactive_ms;
                        } else {
                            wait_ms = calculated_ms;
                        }

                        // AD045: Passive monitoring (every 10 cycles)
                        // Monitor sync quality and drift without actively correcting
                        // Note: static variables moved to INACTIVE case level for report sending after wait
                        client_target_for_report = client_target_active_us;  // Store for report after wait

                        if (client_inactive_cycle_count % 10 == 0) {
                            time_sync_quality_t quality;
                            int32_t phase_offset_ms = (int32_t)calculated_ms - (int32_t)inactive_ms;

                            if (time_sync_get_quality(&quality) == ESP_OK) {
                                ESP_LOGI(TAG, "CLIENT SYNC: quality=%u%%, avg_drift=%+ld μs, phase_offset=%+ld ms, wait=%lu ms",
                                         quality.quality_score, (long)quality.avg_drift_us, (long)phase_offset_ms, wait_ms);

                                // Edge case detection (for future adaptive corrections)
                                if (quality.quality_score < 50 || llabs(quality.avg_drift_us) > 100000) {  // 100ms threshold
                                    ESP_LOGW(TAG, "CLIENT SYNC DEGRADED: quality=%u%%, avg_drift=%+ld μs",
                                             quality.quality_score, (long)quality.avg_drift_us);
                                    // Future: Could trigger targeted correction or re-sync
                                }
                            }
                            // Mark that we should send activation report after wait
                            send_activation_report = true;
                        }
                        client_inactive_cycle_count++;
                    } else {
                        // No epoch available - fall back to nominal timing
                        wait_ms = inactive_ms;
                        ESP_LOGD(TAG, "CLIENT: No motor epoch available, using nominal wait %lu ms", wait_ms);
                    }
                }

                // Bug #17 Fix: Use absolute time scheduling for the wait
                if (wait_ms > 0) {
                    uint32_t wait_target_ms;

                    if (inactive_role == PEER_ROLE_CLIENT) {
                        // CLIENT: Wait relative to inactive_start_ms (recorded at state entry)
                        wait_target_ms = inactive_start_ms + wait_ms;
                    } else {
                        // SERVER/STANDALONE: Wait until end of full cycle
                        // cycle_start_ms was set in ACTIVE state
                        wait_target_ms = cycle_start_ms + motor_on_ms + active_coast_ms + inactive_ms;
                    }

                    if (delay_until_target_ms(wait_target_ms)) {
                        state = MOTOR_STATE_CHECK_MESSAGES;
                        break;
                    }
                }

                // CRITICAL: Alternate direction for next cycle (fixes 2× frequency bug)
                // Single-device mode: Always alternate (motor wear reduction)
                // Dual-device mode: Depends on direction_alternation_enabled flag
                if (direction_alternation_enabled) {
                    is_forward_direction = !is_forward_direction;
                }

                // AD045: CLIENT transitions to ACTIVE, SERVER/STANDALONE to CHECK_MESSAGES
                if (inactive_role == PEER_ROLE_CLIENT) {
                    // Bug #54a fix: Send activation report NOW (after wait completed, before ACTIVE)
                    // This captures the actual transition time, not the pre-wait time
                    if (send_activation_report && client_target_for_report > 0) {
                        uint64_t actual_sync_time_us;
                        if (time_sync_get_time(&actual_sync_time_us) == ESP_OK) {
                            int32_t client_error_ms = (int32_t)((int64_t)actual_sync_time_us - (int64_t)client_target_for_report) / 1000;

                            coordination_message_t report = {
                                .type = SYNC_MSG_ACTIVATION_REPORT,
                                .timestamp_ms = (uint32_t)(esp_timer_get_time() / 1000),
                                .payload.activation_report = {
                                    .actual_time_us = actual_sync_time_us,
                                    .target_time_us = client_target_for_report,
                                    .client_error_ms = client_error_ms,
                                    .cycle_number = client_inactive_cycle_count - 1  // -1 because already incremented
                                }
                            };

                            esp_err_t send_err = ble_send_coordination_message(&report);
                            if (send_err == ESP_OK) {
                                ESP_LOGD(TAG, "CLIENT: Activation report sent (cycle=%lu, err=%ldms)",
                                         (unsigned long)(client_inactive_cycle_count - 1), (long)client_error_ms);
                            }
                        }
                        send_activation_report = false;  // Reset flag
                    }


                    // Bug #79: CLIENT must check LED timer (doesn't visit CHECK_MESSAGES)
                    // SERVER checks LED in CHECK_MESSAGES every cycle, but CLIENT bypasses it
                    // after first cycle (INACTIVE -> ACTIVE -> INACTIVE -> ... loop).
                    {
                        uint32_t now_ms = (uint32_t)(esp_timer_get_time() / 1000);
                        if (current_mode != MODE_CUSTOM && led_indication_active &&
                            ((now_ms - led_indication_start_ms) >= LED_INDICATION_TIME_MS)) {
                            led_indication_active = false;
                            led_clear();
                            ESP_LOGI(TAG, "LED off (battery conservation)");
                        }
                    }
                    state = MOTOR_STATE_ACTIVE;
                } else {
                    state = MOTOR_STATE_CHECK_MESSAGES;
                }
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

uint8_t motor_get_duty_percent(void) {
    // AD045: Pattern-broadcast - return duty percent for time_sync beacon
    // Duty = motor_on_ms / (motor_on_ms + active_coast_ms) as percentage
    mode_t mode = current_mode;
    uint32_t motor_on = modes[mode].motor_on_ms;
    uint32_t active_coast = modes[mode].active_coast_ms;
    uint32_t active_period = motor_on + active_coast;

    if (active_period == 0) {
        return 0;  // Prevent division by zero
    }

    return (uint8_t)((motor_on * 100) / active_period);
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

void motor_trigger_beacon_bemf_logging(void) {
    // Phase 2: Trigger back-EMF logging for 10 seconds after time sync beacon
    // This helps verify bilateral timing remains synchronized after time sync updates

    // Check if mode-change logging is already active
    uint32_t now = (uint32_t)(esp_timer_get_time() / 1000);
    bool mode_change_logging_active = (now - last_mode_change_ms) < LED_INDICATION_TIME_MS;

    if (mode_change_logging_active) {
        // Gracefully refuse: Mode-change logging takes priority
        ESP_LOGI(TAG, "Beacon BEMF logging skipped (mode-change logging active)");
        return;
    }

    // Start beacon-triggered logging
    beacon_bemf_logging_active = true;
    beacon_bemf_start_ms = now;
    ESP_LOGI(TAG, "Beacon BEMF logging triggered (10s window)");
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
    // Validate intensity (0% for LED-only, 30-80% for motor safety per AD031)
    if (intensity_percent != 0 && (intensity_percent < 30 || intensity_percent > 80)) {
        ESP_LOGE(TAG, "Invalid intensity: %u%% (must be 0%% or 30-80%%)", intensity_percent);
        return ESP_ERR_INVALID_ARG;
    }

    // Update global mode 5 intensity (thread-safe, motor_task reads this)
    mode5_pwm_intensity = intensity_percent;

    if (intensity_percent == 0) {
        ESP_LOGI(TAG, "Mode 5 intensity updated: 0%% (LED-only mode)");
    } else {
        ESP_LOGI(TAG, "Mode 5 intensity updated: %u%%", intensity_percent);
    }
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

void motor_task_notify_motor_started(void) {
    // Phase 6: Signal CLIENT that MOTOR_STARTED message arrived from SERVER
    // This handles TWO scenarios:
    //
    // 1. Coordinated start: Aborts wait loop immediately (Issue #3 fix)
    //    - CLIENT is in coordinated start wait loop, checks motor_started_received
    //
    // 2. Frequency change (Bug #84): Skip INACTIVE after epoch update
    //    - CLIENT is in ACTIVE/INACTIVE loop, next INACTIVE would recalculate
    //    - Setting client_skip_inactive_wait causes CLIENT to go directly to ACTIVE
    //    - This is the same pattern as Bug #81/#83 fixes
    //
    motor_started_received = true;
    client_skip_inactive_wait = true;  // Bug #84: Handle frequency changes during operation
    ESP_LOGI(TAG, "MOTOR_STARTED: flags set (coordinated start + frequency change)");
}

// NOTE: ble_callback_coordination_message() removed in Phase 3 refactor.
// Coordination messages now go through time_sync_task to prevent motor timing disruption.
// See time_sync_task.c:handle_coordination_message()
