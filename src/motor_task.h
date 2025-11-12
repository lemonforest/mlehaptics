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
 * Modes 0-3 are predefined EMDR patterns
 * Mode 4 (MODE_CUSTOM) is configurable via BLE GATT characteristics
 */
typedef enum {
    MODE_1HZ_50,      /**< 1 Hz @ 50% duty (250ms ON, 250ms coast) */
    MODE_1HZ_25,      /**< 1 Hz @ 25% duty (125ms ON, 375ms coast) */
    MODE_05HZ_50,     /**< 0.5 Hz @ 50% duty (500ms ON, 500ms coast) */
    MODE_05HZ_25,     /**< 0.5 Hz @ 25% duty (250ms ON, 750ms coast) */
    MODE_CUSTOM,      /**< Mode 5: Custom frequency/duty (BLE configurable) */
    MODE_COUNT        /**< Total number of modes */
} mode_t;

/**
 * @brief Mode configuration structure
 *
 * Defines timing parameters for each motor mode
 */
typedef struct {
    const char* name;         /**< Human-readable mode name */
    uint32_t motor_on_ms;     /**< Motor ON duration in milliseconds */
    uint32_t coast_ms;        /**< Motor coast duration in milliseconds */
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
 * 8-state machine for bilateral alternating motor control with back-EMF sampling
 */
typedef enum {
    MOTOR_STATE_CHECK_MESSAGES,           /**< Check queues, handle mode changes */
    MOTOR_STATE_FORWARD_ACTIVE,           /**< Motor forward, PWM active */
    MOTOR_STATE_FORWARD_COAST_REMAINING,  /**< Coast remaining time (forward cycle) */
    MOTOR_STATE_BEMF_IMMEDIATE,           /**< Coast + immediate back-EMF sample */
    MOTOR_STATE_COAST_SETTLE,             /**< Wait settle time + settled sample */
    MOTOR_STATE_REVERSE_ACTIVE,           /**< Motor reverse, PWM active */
    MOTOR_STATE_REVERSE_COAST_REMAINING,  /**< Coast remaining time (reverse cycle) */
    MOTOR_STATE_SHUTDOWN                  /**< Final cleanup before task exit */
} motor_state_t;

// ============================================================================
// MESSAGE TYPES
// ============================================================================

/**
 * @brief Inter-task message types
 *
 * Used for communication between button_task, battery monitor, and motor_task
 */
typedef enum {
    MSG_MODE_CHANGE,          /**< Button press: cycle to next mode */
    MSG_EMERGENCY_SHUTDOWN,   /**< Button hold 5s: immediate shutdown */
    MSG_BLE_REENABLE,         /**< Button hold 1-2s: re-enable BLE advertising */
    MSG_BATTERY_WARNING,      /**< Battery voltage below warning threshold */
    MSG_BATTERY_CRITICAL      /**< Battery voltage below critical threshold (LVO) */
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
 * Main motor control loop implementing 8-state machine:
 * 1. CHECK_MESSAGES: Process queue, handle mode/shutdown messages
 * 2. FORWARD_ACTIVE: Drive motor forward with PWM
 * 3. BEMF_IMMEDIATE: Sample back-EMF immediately after motor off
 * 4. COAST_SETTLE: Wait settle time, sample settled back-EMF
 * 5. FORWARD_COAST_REMAINING: Complete forward coast period
 * 6. REVERSE_ACTIVE: Drive motor reverse with PWM
 * 7. REVERSE_COAST_REMAINING: Complete reverse coast period
 * 8. SHUTDOWN: Cleanup and exit
 *
 * Message queue inputs:
 * - button_to_motor_queue: Mode changes, emergency shutdown, BLE re-enable
 * - battery_to_motor_queue: Battery warnings, critical LVO
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
 * @brief Get session elapsed time
 * @return Milliseconds since session start (xTaskGetTickCount())
 *
 * Used by BLE GATT server for session time notifications
 */
uint32_t motor_get_session_time_ms(void);

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
 * @param intensity_percent PWM intensity 30-80% (research safety limits)
 * @return ESP_OK on success, ESP_ERR_INVALID_ARG if out of range
 *
 * Thread-safe update of Mode 5 motor intensity
 * Changes take effect on next cycle when MODE_CUSTOM is active
 *
 * NOTE: Only affects MODE_CUSTOM (Mode 5)
 * NOTE: Limited to 30-80% per AD031 research safety constraints
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

#ifdef __cplusplus
}
#endif

#endif // MOTOR_TASK_H
