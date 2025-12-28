/**
 * @file time_sync_task.h
 * @brief Time Synchronization Task Module - Header
 *
 * Dedicated FreeRTOS task for managing time synchronization between peer devices.
 * Handles periodic sync beacon transmission (SERVER) and beacon processing (CLIENT).
 *
 * Phase 2 (AD039): Hybrid time synchronization protocol
 * - Initial connection sync (< 1ms accuracy)
 * - Periodic sync beacons (10-60s adaptive intervals)
 * - Graceful degradation on disconnect
 *
 * @date 2025-11-19
 * @author Claude Code (Anthropic)
 */

#ifndef TIME_SYNC_TASK_H
#define TIME_SYNC_TASK_H

#include <stdint.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "esp_err.h"
#include "time_sync.h"
#include "ble_manager.h"  // Phase 3: For coordination_message_t

#ifdef __cplusplus
extern "C" {
#endif

/*******************************************************************************
 * TASK CONFIGURATION
 ******************************************************************************/

/** @brief Stack size for time sync task (bytes) - increased for Phase 6 diagnostic logging */
#define TIME_SYNC_TASK_STACK_SIZE  3072

/** @brief Priority for time sync task (lower than motor, higher than BLE) */
#define TIME_SYNC_TASK_PRIORITY    4

/** @brief Queue depth for time sync messages
 *
 * Bug #58 fix: Increased from 8 to 16 to handle burst traffic during mode changes.
 * Mode changes generate multiple coordination messages (proposal, ACK, SYNC_FB)
 * that can arrive faster than the task drains them.
 */
#define TIME_SYNC_QUEUE_DEPTH      16

/*******************************************************************************
 * MESSAGE TYPES
 ******************************************************************************/

/**
 * @brief Message types for time sync task communication
 */
typedef enum {
    TIME_SYNC_MSG_INIT,             /**< Initialize time sync with role */
    TIME_SYNC_MSG_DISCONNECTION,    /**< Peer disconnected */
    TIME_SYNC_MSG_BEACON_RECEIVED,  /**< Beacon received from peer (CLIENT only) */
    TIME_SYNC_MSG_COORDINATION,     /**< Coordination message from peer (Phase 3) */
    TIME_SYNC_MSG_TRIGGER_BEACONS,  /**< Bug #57: Trigger immediate forced beacon burst (SERVER only) */
    TIME_SYNC_MSG_SHUTDOWN          /**< Stop task gracefully */
} time_sync_msg_type_t;

/**
 * @brief Time sync task message structure
 */
typedef struct {
    time_sync_msg_type_t type;      /**< Message type */
    union {
        /** Data for TIME_SYNC_MSG_INIT */
        struct {
            time_sync_role_t role;          /**< SERVER or CLIENT role */
        } init;

        /** Data for TIME_SYNC_MSG_BEACON_RECEIVED */
        struct {
            time_sync_beacon_t beacon;      /**< Beacon data */
            uint64_t receive_time_us;       /**< Timestamp when received */
            uint8_t transport;              /**< 0=BLE, 1=ESP-NOW (AD048) */
        } beacon;

        /** Data for TIME_SYNC_MSG_COORDINATION (Phase 3) */
        struct {
            coordination_message_t msg;     /**< Coordination message from peer */
        } coordination;

        /** Data for TIME_SYNC_MSG_DISCONNECTION (Bug #105) */
        struct {
            bool preserve_espnow;           /**< true = bootstrap complete, keep ESP-NOW peer */
        } disconnection;
    } data;
} time_sync_message_t;

/*******************************************************************************
 * PUBLIC API
 ******************************************************************************/

/**
 * @brief Initialize and start time sync task
 *
 * Creates the time sync FreeRTOS task and message queue.
 * Must be called during system initialization.
 *
 * @return ESP_OK on success
 * @return ESP_ERR_NO_MEM if task/queue creation fails
 */
esp_err_t time_sync_task_init(void);

/**
 * @brief Send initialization message to time sync task
 *
 * Called by motor_task after pairing completes.
 * Initializes time sync module with assigned role (NTP-style, no common reference needed).
 *
 * @param role Device role (TIME_SYNC_ROLE_SERVER or TIME_SYNC_ROLE_CLIENT)
 * @return ESP_OK on success
 * @return ESP_FAIL if queue send fails
 */
esp_err_t time_sync_task_send_init(time_sync_role_t role);

/**
 * @brief Send disconnection notification to time sync task
 *
 * Called by BLE manager when peer connection drops.
 * Time sync will freeze current state and continue with last known offset.
 *
 * Bug #105: If preserve_espnow is true (bootstrap complete), ESP-NOW peer
 * is kept configured for continued coordination. Only cleared on unexpected
 * disconnects where re-pairing is needed.
 *
 * @param preserve_espnow true if bootstrap complete (keep ESP-NOW), false to clear
 * @return ESP_OK on success
 * @return ESP_FAIL if queue send fails
 */
esp_err_t time_sync_task_send_disconnection(bool preserve_espnow);

/**
 * @brief Beacon transport types (AD048)
 */
#define BEACON_TRANSPORT_BLE      0   /**< Beacon received via BLE GATT notify */
#define BEACON_TRANSPORT_ESPNOW   1   /**< Beacon received via ESP-NOW (low latency) */

/**
 * @brief Send received beacon to time sync task (CLIENT only)
 *
 * Called by BLE manager or ESP-NOW when sync beacon received from SERVER.
 * Time sync task will process beacon and update clock offset.
 *
 * @param beacon Pointer to received beacon data
 * @param receive_time_us Timestamp when beacon was received
 * @param transport Transport type (BEACON_TRANSPORT_BLE or BEACON_TRANSPORT_ESPNOW)
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_ARG if beacon is NULL
 * @return ESP_FAIL if queue send fails
 */
esp_err_t time_sync_task_send_beacon(const time_sync_beacon_t *beacon, uint64_t receive_time_us, uint8_t transport);

/**
 * @brief Send coordination message to time sync task (Phase 3)
 *
 * Called by BLE manager when coordination message received from peer.
 * Time sync task will process message and forward to appropriate task.
 * This moves BLE processing out of motor task to prevent timing disruption.
 *
 * @param msg Pointer to coordination message
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_ARG if msg is NULL
 * @return ESP_FAIL if queue send fails
 */
esp_err_t time_sync_task_send_coordination(const coordination_message_t *msg);

/**
 * @brief Get time sync task message queue handle
 *
 * Used by other modules to send messages to time sync task.
 *
 * @return Queue handle (NULL if not initialized)
 */
QueueHandle_t time_sync_task_get_queue(void);

/**
 * @brief Check if CLIENT_READY message has been received
 * @return true if CLIENT is ready, false otherwise
 *
 * Used by SERVER motor_task to wait for CLIENT synchronization before starting
 */
bool time_sync_client_ready_received(void);

/**
 * @brief Reset CLIENT_READY flag for next session
 *
 * Called at start of pairing to clear stale state from previous session
 */
void time_sync_reset_client_ready(void);

/**
 * @brief Trigger immediate forced beacon burst (Bug #57 fix)
 *
 * Sends a message to the time_sync_task to immediately start sending
 * forced beacons. This is used after mode changes to ensure CLIENT
 * receives the new motor_epoch_us and motor_cycle_ms promptly.
 *
 * Without this, forced beacons were only sent when perform_periodic_update()
 * was called (10-60 second adaptive interval), leaving CLIENT running at
 * the old frequency for an extended period after mode changes.
 *
 * @return ESP_OK on success
 * @return ESP_FAIL if queue send fails
 */
esp_err_t time_sync_task_trigger_beacons(void);

/**
 * @brief Notify time_sync that LTK is now available (Bug #108 fix)
 *
 * Called by ble_manager.c when BLE_GAP_EVENT_ENC_CHANGE fires with status=0,
 * indicating SMP pairing is complete and LTK is available in the bond store.
 *
 * If WIFI_MAC was received before LTK was ready, this function will complete
 * the deferred LTK-based key derivation and configure encrypted ESP-NOW.
 *
 * Bug #108: WIFI_MAC arrives during GATT discovery, but LTK isn't available
 * until SMP pairing completes ~0.5-1s later. Without this deferred processing,
 * both devices fall back to unencrypted ESP-NOW.
 *
 * @return ESP_OK if LTK derivation completed or wasn't needed
 * @return ESP_ERR_NOT_FOUND if no pending WIFI_MAC to process
 * @return ESP_FAIL if derivation or peer configuration failed
 */
esp_err_t time_sync_on_ltk_available(void);

#ifdef __cplusplus
}
#endif

#endif /* TIME_SYNC_TASK_H */
