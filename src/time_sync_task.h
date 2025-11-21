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

#ifdef __cplusplus
extern "C" {
#endif

/*******************************************************************************
 * TASK CONFIGURATION
 ******************************************************************************/

/** @brief Stack size for time sync task (bytes) */
#define TIME_SYNC_TASK_STACK_SIZE  2048

/** @brief Priority for time sync task (lower than motor, higher than BLE) */
#define TIME_SYNC_TASK_PRIORITY    4

/** @brief Queue depth for time sync messages */
#define TIME_SYNC_QUEUE_DEPTH      8

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
        } beacon;
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
 * @return ESP_OK on success
 * @return ESP_FAIL if queue send fails
 */
esp_err_t time_sync_task_send_disconnection(void);

/**
 * @brief Send received beacon to time sync task (CLIENT only)
 *
 * Called by BLE manager when sync beacon received from SERVER.
 * Time sync task will process beacon and update clock offset.
 *
 * @param beacon Pointer to received beacon data
 * @param receive_time_us Timestamp when beacon was received
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_ARG if beacon is NULL
 * @return ESP_FAIL if queue send fails
 */
esp_err_t time_sync_task_send_beacon(const time_sync_beacon_t *beacon, uint64_t receive_time_us);

/**
 * @brief Get time sync task message queue handle
 *
 * Used by other modules to send messages to time sync task.
 *
 * @return Queue handle (NULL if not initialized)
 */
QueueHandle_t time_sync_task_get_queue(void);

#ifdef __cplusplus
}
#endif

#endif /* TIME_SYNC_TASK_H */
