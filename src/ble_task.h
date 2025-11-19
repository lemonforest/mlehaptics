/**
 * @file ble_task.h
 * @brief BLE Task Module - FreeRTOS task for BLE advertising lifecycle management
 *
 * This module implements the BLE task that manages:
 * - BLE advertising lifecycle (start, timeout, stop)
 * - BLE pairing/bonding security (Phase 1b.3)
 * - Message queue for BLE re-enable and shutdown commands
 * - Advertising timeout enforcement (5 minutes)
 * - Pairing timeout enforcement (30 seconds)
 * - State transitions based on connection events
 *
 * State Machine: 5 states (Phase 1b.3)
 * - IDLE: Not advertising, waiting for BLE re-enable message
 * - ADVERTISING: Advertising active, monitoring for connection or timeout
 * - PAIRING: Pairing in progress, waiting for user confirmation
 * - CONNECTED: Client connected, monitoring for disconnection
 * - SHUTDOWN: Cleanup before task exit
 *
 * Message Queue Integration:
 * - button_to_ble_queue: Receives MSG_BLE_REENABLE and MSG_EMERGENCY_SHUTDOWN
 * - ble_to_motor_queue: Sends MSG_PAIRING_COMPLETE and MSG_PAIRING_FAILED
 *
 * @date November 15, 2025
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
 * 5-state machine (Phase 1b.3 adds PAIRING) for BLE advertising lifecycle management
 * Simpler than motor task (no complex timing requirements)
 */
typedef enum {
    BLE_STATE_IDLE,        /**< Not advertising, waiting for re-enable message */
    BLE_STATE_ADVERTISING, /**< Advertising active, monitoring for timeout */
    BLE_STATE_PAIRING,     /**< Pairing in progress, waiting for confirmation (Phase 1b.3) */
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
 * Main BLE control loop implementing 5-state machine (Phase 1b.3):
 * 1. IDLE: Wait for MSG_BLE_REENABLE (1-2s button hold)
 * 2. ADVERTISING: Monitor connection and 5-minute timeout
 * 3. PAIRING: Wait for user confirmation, enforce 30-second timeout (Phase 1b.3)
 * 4. CONNECTED: Monitor disconnection
 * 5. SHUTDOWN: Exit cleanly
 *
 * State transitions:
 * - IDLE → ADVERTISING: MSG_BLE_REENABLE received, advertising started
 * - ADVERTISING → PAIRING: Peer connection established, pairing initiated (Phase 1b.3)
 * - PAIRING → CONNECTED: Pairing successful, bonding complete
 * - PAIRING → IDLE: Pairing timeout (30s) or failure
 * - ADVERTISING → IDLE: 5-minute timeout expired (no connection)
 * - CONNECTED → ADVERTISING: Client disconnected (GAP event restarts advertising)
 * - CONNECTED → IDLE: Client disconnected but advertising failed to restart
 * - Any state → SHUTDOWN: MSG_EMERGENCY_SHUTDOWN received
 *
 * Message queue inputs:
 * - button_to_ble_queue: MSG_BLE_REENABLE (start advertising), MSG_EMERGENCY_SHUTDOWN
 *
 * Message queue outputs (Phase 1b.3):
 * - ble_to_motor_queue: MSG_PAIRING_COMPLETE, MSG_PAIRING_FAILED
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
