/**
 * @file button_task.h
 * @brief Button Task Module - FreeRTOS task for button state machine
 *
 * This module implements the button task that manages:
 * - Hardware button debouncing and state detection
 * - Mode cycling (short press < 1s)
 * - BLE advertising re-enable (1-2s hold)
 * - Emergency shutdown (5s hold with purple countdown LED)
 * - NVS clear for factory reset (10s hold, first 30s after boot only)
 *
 * State Machine: 8 states
 * - IDLE: Waiting for button press
 * - DEBOUNCE: Debouncing press (50ms)
 * - PRESSED: Button confirmed pressed, waiting for release or hold
 * - HOLD_DETECT: Detecting hold type (1-2s BLE, 5s shutdown, 10s NVS clear)
 * - SHUTDOWN_HOLD: Shutdown detected, waiting for release to confirm
 * - COUNTDOWN: Purple LED countdown (5 cycles), waiting for release to abort
 * - SHUTDOWN: Final cleanup before deep sleep
 * - SHUTDOWN_SENT: Terminal state after sending shutdown message
 *
 * Message Queue Outputs:
 * - button_to_motor_queue: MSG_MODE_CHANGE, MSG_EMERGENCY_SHUTDOWN
 * - button_to_ble_queue: MSG_BLE_REENABLE, MSG_EMERGENCY_SHUTDOWN
 *
 * @date November 11, 2025
 * @author Claude Code (Anthropic)
 */

#ifndef BUTTON_TASK_H
#define BUTTON_TASK_H

#include <stdint.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "esp_err.h"
#include "motor_task.h"  // For message_type_t

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================================
// BUTTON CONFIGURATION
// ============================================================================

/**
 * @brief Button GPIO pin
 */
#define GPIO_BUTTON             1       /**< Button input (RTC wake capable) */

/**
 * @brief Button timing constants
 */
#define BUTTON_DEBOUNCE_MS      50      /**< Debounce time (ignore bounces) */
#define BUTTON_BLE_HOLD_MIN_MS  1000    /**< BLE re-enable minimum hold (1s) */
#define BUTTON_BLE_HOLD_MAX_MS  2000    /**< BLE re-enable maximum hold (2s) */
#define BUTTON_SHUTDOWN_MS      5000    /**< Emergency shutdown hold time (5s) */
#define BUTTON_NVS_CLEAR_MS     15000   /**< NVS clear hold time (15s, first 30s only) */
#define BUTTON_NVS_CLEAR_WINDOW_MS 30000 /**< NVS clear only allowed in first 30s */

/**
 * @brief Countdown LED configuration
 */
#define COUNTDOWN_CYCLES        5       /**< Purple blink cycles before shutdown */
#define COUNTDOWN_BLINK_MS      200     /**< Purple LED on/off duration */

// ============================================================================
// BUTTON STATE MACHINE
// ============================================================================

/**
 * @brief Button task state machine states
 *
 * 8-state machine for button handling with debouncing and hold detection
 */
typedef enum {
    BTN_STATE_IDLE,             /**< Waiting for button press */
    BTN_STATE_DEBOUNCE,         /**< Debouncing press (50ms) */
    BTN_STATE_PRESSED,          /**< Button confirmed pressed, waiting for release or hold */
    BTN_STATE_HOLD_DETECT,      /**< Detecting hold type (1-2s, 5s, 10s) */
    BTN_STATE_SHUTDOWN_HOLD,    /**< Shutdown hold confirmed (>5s), waiting for release */
    BTN_STATE_COUNTDOWN,        /**< Purple LED countdown (release to abort) */
    BTN_STATE_SHUTDOWN,         /**< Final cleanup before deep sleep */
    BTN_STATE_SHUTDOWN_SENT     /**< Terminal state after shutdown message sent */
} button_state_t;

// ============================================================================
// PUBLIC API
// ============================================================================

/**
 * @brief Button control FreeRTOS task
 * @param pvParameters Task parameters (unused, pass NULL)
 *
 * Main button control loop implementing 8-state machine:
 * 1. IDLE: Wait for button press (GPIO low = pressed)
 * 2. DEBOUNCE: Wait 50ms to confirm press (ignore bounces)
 * 3. PRESSED: Wait for release or hold detection
 * 4. HOLD_DETECT: Determine hold type based on duration
 * 5. SHUTDOWN_HOLD: Confirm shutdown hold (>5s), wait for release
 * 6. COUNTDOWN: Purple LED blink countdown (release aborts, feed watchdog)
 * 7. SHUTDOWN: Send shutdown messages, enter deep sleep
 * 8. SHUTDOWN_SENT: Terminal state (task exits)
 *
 * Actions by hold duration:
 * - <1s: Mode change (cycle through MODE_05HZ_25 → MODE_1HZ_25 → MODE_15HZ_25 → MODE_2HZ_25 → MODE_CUSTOM)
 * - 1-2s: BLE advertising re-enable (if BLE idle)
 * - >5s: Emergency shutdown (purple countdown, enter deep sleep)
 * - >10s: Factory reset (NVS clear, only in first 30s after boot)
 *
 * State transitions:
 * - IDLE → DEBOUNCE: Button pressed (GPIO low)
 * - DEBOUNCE → PRESSED: Debounce complete (50ms), still pressed
 * - DEBOUNCE → IDLE: Button released during debounce (false trigger)
 * - PRESSED → IDLE: Button released <1s (trigger mode change)
 * - PRESSED → HOLD_DETECT: Button held ≥1s
 * - HOLD_DETECT → IDLE: Button released 1-2s (trigger BLE re-enable)
 * - HOLD_DETECT → SHUTDOWN_HOLD: Button held ≥5s
 * - SHUTDOWN_HOLD → COUNTDOWN: Button released after ≥5s hold
 * - COUNTDOWN → IDLE: Button pressed during countdown (abort shutdown)
 * - COUNTDOWN → SHUTDOWN: Countdown complete (5 cycles)
 * - SHUTDOWN → SHUTDOWN_SENT: Cleanup complete, messages sent
 *
 * Message queue outputs:
 * - button_to_motor_queue: MSG_MODE_CHANGE (short press), MSG_EMERGENCY_SHUTDOWN (5s hold)
 * - button_to_ble_queue: MSG_BLE_REENABLE (1-2s hold), MSG_EMERGENCY_SHUTDOWN (5s hold)
 *
 * Task parameters:
 * - Priority: 4 (higher than motor and BLE tasks for responsiveness)
 * - Stack size: 3072 bytes
 * - Pinned to core: None (auto)
 *
 * Watchdog:
 * - Subscribes at start, feeds during countdown loop (200ms interval)
 * - Unsubscribes before task exit
 *
 * Never returns (self-deletes on shutdown)
 */
void button_task(void *pvParameters);

// ============================================================================
// EXTERNAL DEPENDENCIES
// ============================================================================

/**
 * @brief Message queue from button_task to motor_task
 *
 * Created in main.c, used by button_task and motor_task
 * Queue size: 5 messages (mode changes can queue up)
 */
extern QueueHandle_t button_to_motor_queue;

/**
 * @brief Message queue from button_task to BLE task
 *
 * Created in main.c, used by button_task and ble_task
 * Queue size: 3 messages (small, low traffic)
 */
extern QueueHandle_t button_to_ble_queue;

/**
 * @brief Message queue from motor_task to button_task
 *
 * Created in main.c, used for session timeout notification
 * Queue size: 1 message (only session timeout)
 */
extern QueueHandle_t motor_to_button_queue;

#ifdef __cplusplus
}
#endif

#endif // BUTTON_TASK_H
