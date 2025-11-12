/**
 * @file role_manager.h
 * @brief Role Management and Fallback State Definitions (AD028)
 *
 * Manages device role (SERVER/CLIENT) and synchronized fallback states
 * for dual-device bilateral stimulation per AD028 specification.
 *
 * Key Features:
 * - Automatic role determination and switching
 * - Synchronized fallback phase management
 * - "Survivor becomes server" recovery
 * - Connection state tracking
 *
 * @date November 11, 2025
 * @author Claude Code (Anthropic)
 */

#ifndef ROLE_MANAGER_H
#define ROLE_MANAGER_H

#include <stdint.h>
#include <stdbool.h>
#include "esp_err.h"
#include "freertos/FreeRTOS.h"

// ============================================================================
// ROLE DEFINITIONS
// ============================================================================

/**
 * @brief Device role in dual-device system
 */
typedef enum {
    ROLE_UNDETERMINED = 0,  /**< Role not yet determined */
    ROLE_SERVER,            /**< Server device - controls timing */
    ROLE_CLIENT,            /**< Client device - follows commands */
    ROLE_STANDALONE         /**< Single device operation */
} device_role_t;

// ============================================================================
// FALLBACK PHASES
// ============================================================================

/**
 * @brief Fallback phase after BLE disconnection
 */
typedef enum {
    FALLBACK_NONE = 0,      /**< Normal operation (BLE connected) */
    FALLBACK_PHASE1_SYNC,   /**< 0-2 minutes: Maintain bilateral rhythm */
    FALLBACK_PHASE2_ROLE    /**< 2+ minutes: Continue assigned role only */
} fallback_phase_t;

// ============================================================================
// CONNECTION STATES
// ============================================================================

/**
 * @brief BLE connection state
 */
typedef enum {
    CONN_STATE_IDLE = 0,    /**< Not advertising or connected */
    CONN_STATE_ADVERTISING, /**< Advertising for connection */
    CONN_STATE_CONNECTING,  /**< Connection in progress */
    CONN_STATE_CONNECTED,   /**< Connected to peer device */
    CONN_STATE_DISCONNECTED,/**< Disconnected (fallback active) */
    CONN_STATE_RECONNECTING /**< Attempting reconnection */
} connection_state_t;

// ============================================================================
// TIMING CONSTANTS (per AD028)
// ============================================================================

#define ROLE_SURVIVOR_TIMEOUT_MS     30000   /**< 30s before client becomes server */
#define FALLBACK_PHASE1_DURATION_MS  120000  /**< 2 minutes synchronized fallback */
#define RECONNECT_INTERVAL_MS        300000  /**< 5 minutes between reconnect attempts */
#define SESSION_DURATION_MIN_MS      3600000 /**< 60 minutes minimum session */
#define SESSION_DURATION_MAX_MS      5400000 /**< 90 minutes maximum session */

// ============================================================================
// FALLBACK STATE STRUCTURE
// ============================================================================

/**
 * @brief Fallback state management structure
 *
 * Tracks all state needed for synchronized fallback operation
 * per AD028 specification.
 */
typedef struct {
    // Connection tracking
    uint32_t disconnect_time;         /**< When BLE disconnected (tick count) */
    uint32_t last_command_time;       /**< Timestamp of last server command */
    uint32_t last_reconnect_attempt;  /**< Last reconnection attempt time */

    // Established parameters (captured at disconnect)
    uint16_t established_cycle_ms;    /**< Current cycle period (e.g., 500ms) */
    uint16_t established_duty_ms;     /**< Current duty cycle (e.g., 125ms) */
    uint8_t  established_intensity;   /**< Motor intensity percentage */
    uint8_t  established_mode;        /**< Therapy mode */

    // Role and phase
    device_role_t current_role;       /**< Current device role */
    device_role_t fallback_role;      /**< Role to use during fallback */
    fallback_phase_t current_phase;   /**< Current fallback phase */

    // Synchronization
    bool phase1_sync_active;          /**< True during 2-minute sync phase */
    uint32_t sync_reference_ms;       /**< Reference time for synchronization */
    bool is_forward_turn;             /**< Track which motor direction is active */

    // Session tracking
    uint32_t session_start_time;      /**< Session start timestamp */
    bool session_active;              /**< Session in progress */
} fallback_state_t;

// ============================================================================
// ROLE MANAGER API
// ============================================================================

/**
 * @brief Initialize role manager
 * @return ESP_OK on success
 */
esp_err_t role_manager_init(void);

/**
 * @brief Deinitialize role manager
 * @return ESP_OK on success
 */
esp_err_t role_manager_deinit(void);

// ============================================================================
// ROLE DETERMINATION
// ============================================================================

/**
 * @brief Determine device role based on connection state
 * @param is_first_device True if this device started advertising first
 * @return Determined device role
 */
device_role_t role_determine(bool is_first_device);

/**
 * @brief Get current device role
 * @return Current device role
 */
device_role_t role_get_current(void);

/**
 * @brief Set device role
 * @param role New device role
 * @return ESP_OK on success
 */
esp_err_t role_set(device_role_t role);

/**
 * @brief Check if device should become server (survivor logic)
 * @param disconnect_duration_ms Time since disconnection in ms
 * @return true if device should become server
 */
bool role_should_become_server(uint32_t disconnect_duration_ms);

// ============================================================================
// FALLBACK MANAGEMENT
// ============================================================================

/**
 * @brief Start fallback mode after BLE disconnection
 * @param established_params Current operational parameters to maintain
 * @return ESP_OK on success
 */
esp_err_t fallback_start(const fallback_state_t *established_params);

/**
 * @brief Update fallback phase based on elapsed time
 * @return Current fallback phase
 */
fallback_phase_t fallback_update_phase(void);

/**
 * @brief Get current fallback phase
 * @return Current fallback phase
 */
fallback_phase_t fallback_get_phase(void);

/**
 * @brief Get fallback state structure
 * @return Pointer to fallback state (read-only)
 */
const fallback_state_t* fallback_get_state(void);

/**
 * @brief Stop fallback mode (connection restored)
 * @return ESP_OK on success
 */
esp_err_t fallback_stop(void);

/**
 * @brief Check if reconnection attempt should be made
 * @return true if reconnection should be attempted
 */
bool fallback_should_reconnect(void);

/**
 * @brief Record reconnection attempt
 */
void fallback_mark_reconnect_attempt(void);

// ============================================================================
// CONNECTION STATE MANAGEMENT
// ============================================================================

/**
 * @brief Set connection state
 * @param state New connection state
 * @return ESP_OK on success
 */
esp_err_t connection_state_set(connection_state_t state);

/**
 * @brief Get current connection state
 * @return Current connection state
 */
connection_state_t connection_state_get(void);

/**
 * @brief Check if device is connected
 * @return true if connected to peer
 */
bool connection_is_active(void);

// ============================================================================
// SESSION MANAGEMENT
// ============================================================================

/**
 * @brief Start therapy session
 * @return ESP_OK on success
 */
esp_err_t session_start(void);

/**
 * @brief Check if session should end
 * @return true if session duration exceeded
 */
bool session_should_end(void);

/**
 * @brief Get elapsed session time
 * @return Session duration in milliseconds
 */
uint32_t session_get_elapsed_ms(void);

/**
 * @brief End therapy session
 * @return ESP_OK on success
 */
esp_err_t session_end(void);

// ============================================================================
// SYNCHRONIZATION HELPERS
// ============================================================================

/**
 * @brief Calculate next motor activation time during fallback
 * @param is_forward True for forward, false for reverse
 * @return Next activation timestamp in ms
 */
uint32_t fallback_get_next_activation_ms(bool is_forward);

/**
 * @brief Check if motor should be active during fallback
 * @param is_forward True for forward, false for reverse
 * @return true if motor should be active now
 */
bool fallback_should_activate_motor(bool is_forward);

// ============================================================================
// STATUS AND LOGGING
// ============================================================================

/**
 * @brief Get human-readable role name
 * @param role Device role
 * @return String representation of role
 */
const char* role_to_string(device_role_t role);

/**
 * @brief Get human-readable fallback phase name
 * @param phase Fallback phase
 * @return String representation of phase
 */
const char* fallback_phase_to_string(fallback_phase_t phase);

/**
 * @brief Log current role and fallback state
 * @param tag Log tag to use
 */
void role_log_status(const char *tag);

#endif // ROLE_MANAGER_H