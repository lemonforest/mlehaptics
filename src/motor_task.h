/**
 * @file motor_task.h
 * @brief Motor Control Task Module - FreeRTOS task for bilateral motor control
 *
 * This module implements the motor control state machine responsible for:
 * - Bilateral alternating motor patterns (forward/reverse cycles)
 * - Mode configurations (1 Hz, 0.5 Hz, custom via BLE)
 * - Message queue handling (button events, battery warnings)
 * - Back-EMF sampling for motor research
 * - NVS settings management for Mode 5 (custom parameters)
 *
 * Architecture (per AD027):
 * - Task module (mirrors FreeRTOS task structure)
 * - Single-device vs dual-device as STATE (not separate code)
 * - Message queue communication with button_task and battery monitor
 * - Dependencies: battery_monitor.h, nvs_manager.h, led_control.h
 *
 * State Machine: 8 states
 * - CHECK_MESSAGES: Process queue messages, handle mode changes
 * - FORWARD_ACTIVE: Motor forward PWM
 * - BEMF_IMMEDIATE: Immediate back-EMF sample after motor off
 * - COAST_SETTLE: Wait for back-EMF settle time
 * - FORWARD_COAST_REMAINING: Complete forward coast period
 * - REVERSE_ACTIVE: Motor reverse PWM
 * - REVERSE_COAST_REMAINING: Complete reverse coast period
 * - SHUTDOWN: Cleanup before task exit
 *
 * @date November 11, 2025
 * @author Claude Code (Anthropic)
 */

#ifndef MOTOR_TASK_H
#define MOTOR_TASK_H

#include <stdint.h>
#include <stdbool.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================================
// MOTOR OPERATING MODES
// ============================================================================

/**
 * @brief Motor operating modes
 *
 * Modes 0-3 are predefined EMDR patterns (bilateral alternation frequencies)
 * Mode 4 (MODE_CUSTOM) is configurable via BLE GATT characteristics
 *
 * NOTE: Frequencies refer to BILATERAL alternation rate (dual-device mode)
 * - "1.0Hz" = 1 complete left-right alternation per second
 * - Single device mode: same frequency, alternating directions
 */
typedef enum {
    MODE_05HZ_25,     /**< 0.5Hz bilateral @ 25% duty (500ms ON, 1500ms coast) */
    MODE_1HZ_25,      /**< 1.0Hz bilateral @ 25% duty (250ms ON, 750ms coast) */
    MODE_15HZ_25,     /**< 1.5Hz bilateral @ 25% duty (167ms ON, 500ms coast) */
    MODE_2HZ_25,      /**< 2.0Hz bilateral @ 25% duty (125ms ON, 375ms coast) */
    MODE_CUSTOM,      /**< Mode 4: Custom frequency/duty (BLE configurable) */
    MODE_COUNT        /**< Total number of modes */
} mode_t;

/**
 * @brief Mode configuration structure
 *
 * Defines timing parameters for each motor mode (Phase 3a: Bilateral timing)
 *
 * Pattern: [ACTIVE period: motor_on_ms + active_coast_ms] [INACTIVE: inactive_ms]
 * - ACTIVE period = first half of frequency period
 * - INACTIVE period = second half (always period/2)
 * - Motor duty % applies to ACTIVE period only
 */
typedef struct {
    const char* name;             /**< Human-readable mode name */
    uint32_t motor_on_ms;         /**< Motor ON duration (motor duty % of ACTIVE period) */
    uint32_t active_coast_ms;     /**< Coast within ACTIVE period (remainder of ACTIVE period) */
    uint32_t inactive_ms;         /**< INACTIVE period (always half the frequency period) */
} mode_config_t;

/**
 * @brief Predefined mode configurations
 *
 * MODE_CUSTOM defaults to 1Hz@50% but is overwritten by BLE settings
 */
extern const mode_config_t modes[MODE_COUNT];

// ============================================================================
// MOTOR STATE MACHINE
// ============================================================================

/**
 * @brief Motor task state machine states
 *
 * 4-state machine for bilateral motor coordination
 * Direction alternates between cycles (not within cycles)
 *
 * State Flow:
 * SERVER:  PAIRING_WAIT → CHECK_MESSAGES → ACTIVE → INACTIVE → [repeat]
 * CLIENT:  PAIRING_WAIT → CHECK_MESSAGES → INACTIVE → ACTIVE → [repeat, with drift correction]
 *
 * Back-EMF sampling is done inline in ACTIVE state (not separate states)
 * CLIENT uses time sync epoch for drift correction in INACTIVE state
 */
typedef enum {
    MOTOR_STATE_PAIRING_WAIT,      /**< Wait for BLE pairing to complete (Phase 1b.3) */
    MOTOR_STATE_CHECK_MESSAGES,    /**< Check queues, handle mode changes, battery, session timeout */
    MOTOR_STATE_ACTIVE,            /**< Motor active in current direction (forward or reverse) */
    MOTOR_STATE_INACTIVE,          /**< Motor coast (inactive period), CLIENT drift correction here */
    MOTOR_STATE_SHUTDOWN           /**< Final cleanup before task exit */
} motor_state_t;

// ============================================================================
// MESSAGE TYPES
// ============================================================================

/**
 * @brief Inter-task message types
 *
 * Used for communication between button_task, battery monitor, BLE task, and motor_task
 */
typedef enum {
    MSG_MODE_CHANGE,          /**< Button press: cycle to next mode */
    MSG_EMERGENCY_SHUTDOWN,   /**< Button hold 5s: immediate shutdown */
    MSG_BLE_REENABLE,         /**< Button hold 1-2s: re-enable BLE advertising */
    MSG_BATTERY_WARNING,      /**< Battery voltage below warning threshold */
    MSG_BATTERY_CRITICAL,     /**< Battery voltage below critical threshold (LVO) */
    MSG_SESSION_TIMEOUT,      /**< Session duration exceeded (60 minutes) */
    MSG_PAIRING_COMPLETE,     /**< BLE pairing successful (Phase 1b.3) */
    MSG_PAIRING_FAILED,       /**< BLE pairing failed or timeout (Phase 1b.3) */
    MSG_TIMER_MOTOR_TRANSITION /**< CLIENT hardware timer fired (AD044: precise antiphase synchronization) */
} message_type_t;

/**
 * @brief Task message structure
 *
 * Union allows different payload types for different message types
 */
typedef struct {
    message_type_t type;      /**< Message type identifier */
    union {
        mode_t new_mode;      /**< New mode for MSG_MODE_CHANGE */
        struct {
            float voltage;    /**< Battery voltage in volts */
            int percentage;   /**< Battery percentage 0-100 */
        } battery;            /**< Battery data for MSG_BATTERY_* */
    } data;                   /**< Message payload */
} task_message_t;

// ============================================================================
// PUBLIC API
// ============================================================================

/**
 * @brief Initialize motor control subsystem
 * @return ESP_OK on success, error code on failure
 *
 * Configures:
 * - GPIO19/20 for H-bridge control (IN1/IN2)
 * - LEDC PWM: 25kHz, 10-bit resolution
 * - Dead time: 1ms FreeRTOS dead time (watchdog feed)
 * - Initial state: motors off (brake mode)
 *
 * Must be called before motor_task starts
 */
esp_err_t motor_init(void);

/**
 * @brief Motor control FreeRTOS task
 * @param pvParameters Task parameters (unused, pass NULL)
 *
 * Main motor control loop implementing 9-state machine (Phase 1b.3):
 * 1. PAIRING_WAIT: Wait for BLE pairing to complete before starting session
 * 2. CHECK_MESSAGES: Process queue, handle mode/shutdown messages
 * 3. FORWARD_ACTIVE: Drive motor forward with PWM
 * 4. BEMF_IMMEDIATE: Sample back-EMF immediately after motor off
 * 5. COAST_SETTLE: Wait settle time, sample settled back-EMF
 * 6. FORWARD_COAST_REMAINING: Complete forward coast period
 * 7. REVERSE_ACTIVE: Drive motor reverse with PWM
 * 8. REVERSE_COAST_REMAINING: Complete reverse coast period
 * 9. SHUTDOWN: Cleanup and exit
 *
 * Message queue inputs:
 * - button_to_motor_queue: Mode changes, emergency shutdown, BLE re-enable
 * - battery_to_motor_queue: Battery warnings, critical LVO
 * - ble_to_motor_queue: Pairing complete/failed (Phase 1b.3)
 *
 * Watchdog: Uses soft-fail pattern (logs errors, continues on failure)
 *
 * Task parameters:
 * - Priority: 5 (normal)
 * - Stack size: 4096 bytes
 * - Pinned to core: None (auto)
 *
 * Never returns (self-deletes on shutdown)
 */
void motor_task(void *pvParameters);

/**
 * @brief Get current motor mode
 * @return Current mode_t value
 *
 * Thread-safe read of current operating mode
 */
mode_t motor_get_current_mode(void);

/**
 * @brief Initialize session start timestamp
 *
 * Must be called during hardware initialization (before motor_task starts).
 * Captures boot time for accurate session time calculations when BLE clients
 * connect before motor_task has started.
 *
 * Called by main.c during init_hardware() sequence.
 */
void motor_init_session_time(void);

/**
 * @brief Get session elapsed time
 * @return Milliseconds since motor_init_session_time() was called
 *
 * Used by BLE GATT server for session time notifications.
 * Returns real-time uptime calculation, not cached value.
 */
uint32_t motor_get_session_time_ms(void);

/**
 * @brief Trigger 10-second back-EMF logging window after time sync beacon
 *
 * Phase 2: Time synchronization verification
 * Called by time_sync_task when a time sync beacon is received.
 * Enables back-EMF logging for 10 seconds to verify bilateral timing
 * remains synchronized after time sync updates.
 *
 * Gracefully refuses if mode-change logging is already active
 * (mode-change logging takes priority).
 */
void motor_trigger_beacon_bemf_logging(void);

/**
 * @brief Notify motor_task that MOTOR_STARTED message arrived
 *
 * Phase 6: Issue #3 fix for MOTOR_STARTED latency
 * Called by time_sync_task when CLIENT receives MOTOR_STARTED from SERVER.
 * Sets flag to abort coordinated start wait loop and start motors immediately.
 *
 * This fixes the case where handshake and MOTOR_STARTED have the same epoch value,
 * so epoch change detection doesn't work. Flag-based detection responds within 50ms.
 */
void motor_task_notify_motor_started(void);

/**
 * @brief Update Mode 5 (custom) motor parameters from BLE
 * @param motor_on_ms Motor ON duration in milliseconds (10-1000ms)
 * @param coast_ms Coast duration in milliseconds (10-1000ms)
 * @return ESP_OK on success, ESP_ERR_INVALID_ARG if out of range
 *
 * Thread-safe update of Mode 5 timing parameters
 * Changes take effect on next cycle when MODE_CUSTOM is active
 *
 * NOTE: Only affects MODE_CUSTOM (Mode 5)
 * NOTE: Parameters validated against research safety limits
 */
esp_err_t motor_update_mode5_timing(uint32_t motor_on_ms, uint32_t coast_ms);

/**
 * @brief Update Mode 5 (custom) PWM intensity from BLE
 * @param intensity_percent PWM intensity: 0% (LED-only) or 30-80% (motor active)
 * @return ESP_OK on success, ESP_ERR_INVALID_ARG if out of range
 *
 * Thread-safe update of Mode 5 motor intensity
 * Changes take effect on next cycle when MODE_CUSTOM is active
 *
 * NOTE: Only affects MODE_CUSTOM (Mode 5)
 * NOTE: 0% = LED-only mode (no motor), 30-80% per AD031 research safety constraints
 */
esp_err_t motor_update_mode5_intensity(uint8_t intensity_percent);

/**
 * @brief Check if Mode 5 settings need NVS save
 * @return true if settings changed since last save
 *
 * Used to implement deferred NVS writes (reduce flash wear)
 */
bool motor_mode5_settings_dirty(void);

/**
 * @brief Mark Mode 5 settings as saved to NVS
 *
 * Clear dirty flag after successful NVS write
 */
void motor_mode5_settings_mark_clean(void);

// ============================================================================
// EXTERNAL DEPENDENCIES
// ============================================================================

/**
 * @brief Message queues (created in main.c, extern in task modules)
 *
 * These queues are created during system initialization and used by
 * multiple tasks for inter-task communication
 */
extern QueueHandle_t button_to_motor_queue;
extern QueueHandle_t battery_to_motor_queue;
extern QueueHandle_t motor_to_button_queue;
extern QueueHandle_t ble_to_motor_queue;     /**< BLE task → motor task (Phase 1b.3) */
extern QueueHandle_t button_to_ble_queue;    /**< Button task → BLE task (existing) */

#ifdef __cplusplus
}
#endif

#endif // MOTOR_TASK_H
