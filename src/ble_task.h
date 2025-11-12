/**
 * @file ble_task.h
 * @brief BLE Task Module - FreeRTOS task for BLE advertising lifecycle management
 *
 * This module implements the BLE task that manages:
 * - BLE advertising lifecycle (start, timeout, stop)
 * - Message queue for BLE re-enable and shutdown commands
 * - Advertising timeout enforcement (5 minutes)
 * - State transitions based on connection events
 *
 * State Machine: 4 states
 * - IDLE: Not advertising, waiting for BLE re-enable message
 * - ADVERTISING: Advertising active, monitoring for connection or timeout
 * - CONNECTED: Client connected, monitoring for disconnection
 * - SHUTDOWN: Cleanup before task exit
 *
 * Message Queue Integration:
 * - button_to_ble_queue: Receives MSG_BLE_REENABLE and MSG_EMERGENCY_SHUTDOWN
 *
 * @date November 11, 2025
 * @author Claude Code (Anthropic)
 */

#ifndef BLE_TASK_H
#define BLE_TASK_H

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
// BLE STATE MACHINE
// ============================================================================

/**
 * @brief BLE task state machine states
 *
 * 4-state machine for BLE advertising lifecycle management
 * Simpler than motor task (no complex timing requirements)
 */
typedef enum {
    BLE_STATE_IDLE,        /**< Not advertising, waiting for re-enable message */
    BLE_STATE_ADVERTISING, /**< Advertising active, monitoring for timeout */
    BLE_STATE_CONNECTED,   /**< Client connected */
    BLE_STATE_SHUTDOWN     /**< Final cleanup before task exit */
} ble_state_t;

// ============================================================================
// PUBLIC API
// ============================================================================

/**
 * @brief BLE control FreeRTOS task
 * @param pvParameters Task parameters (unused, pass NULL)
 *
 * Main BLE control loop implementing 4-state machine:
 * 1. IDLE: Wait for MSG_BLE_REENABLE (1-2s button hold)
 * 2. ADVERTISING: Monitor connection and 5-minute timeout
 * 3. CONNECTED: Monitor disconnection
 * 4. SHUTDOWN: Exit cleanly
 *
 * State transitions:
 * - IDLE → ADVERTISING: MSG_BLE_REENABLE received, advertising started
 * - ADVERTISING → CONNECTED: Client connection established (via GAP event)
 * - ADVERTISING → IDLE: 5-minute timeout expired
 * - CONNECTED → ADVERTISING: Client disconnected (GAP event restarts advertising)
 * - CONNECTED → IDLE: Client disconnected but advertising failed to restart
 * - Any state → SHUTDOWN: MSG_EMERGENCY_SHUTDOWN received
 *
 * Message queue inputs:
 * - button_to_ble_queue: MSG_BLE_REENABLE (start advertising), MSG_EMERGENCY_SHUTDOWN
 *
 * Task parameters:
 * - Priority: 3 (lower than motor_task)
 * - Stack size: 3072 bytes
 * - Pinned to core: None (auto)
 *
 * Never returns (self-deletes on shutdown)
 */
void ble_task(void *pvParameters);

// ============================================================================
// EXTERNAL DEPENDENCIES
// ============================================================================

/**
 * @brief Message queue from button_task to BLE task
 *
 * Created in main.c, used by button_task and ble_task
 * Queue size: 3 messages (small, low traffic)
 */
extern QueueHandle_t button_to_ble_queue;

#ifdef __cplusplus
}
#endif

#endif // BLE_TASK_H
