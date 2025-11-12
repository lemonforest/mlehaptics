/**
 * @file command_protocol.h
 * @brief Command-and-Control Protocol Definitions (AD028)
 *
 * Implements command message protocol for dual-device bilateral stimulation
 * with synchronized fallback architecture per AD028 specification.
 *
 * Key Features:
 * - Command message types for motor control
 * - Timestamped commands for synchronization
 * - Sequence numbers for reliability
 * - Fallback state tracking
 *
 * @date November 11, 2025
 * @author Claude Code (Anthropic)
 */

#ifndef COMMAND_PROTOCOL_H
#define COMMAND_PROTOCOL_H

#include <stdint.h>
#include <stdbool.h>
#include "esp_err.h"
#include "freertos/FreeRTOS.h"

// ============================================================================
// COMMAND TYPES
// ============================================================================

/**
 * @brief Command types for motor control and system management
 */
typedef enum {
    // Motor control commands
    CMD_MOTOR_FORWARD   = 0x01,  /**< Start forward motor rotation */
    CMD_MOTOR_REVERSE   = 0x02,  /**< Start reverse motor rotation */
    CMD_MOTOR_COAST     = 0x03,  /**< Coast motor (both outputs low) */
    CMD_MOTOR_BRAKE     = 0x04,  /**< Brake motor (both outputs high) */

    // Configuration commands
    CMD_CONFIG_MODE     = 0x10,  /**< Change therapy mode */
    CMD_CONFIG_TIMING   = 0x11,  /**< Update cycle timing */
    CMD_CONFIG_INTENSITY= 0x12,  /**< Update motor intensity */

    // System commands
    CMD_SYNC_TIME       = 0x20,  /**< Time synchronization */
    CMD_HEARTBEAT       = 0x21,  /**< Connection keepalive */
    CMD_SHUTDOWN        = 0x22,  /**< Emergency shutdown */
    CMD_ROLE_ANNOUNCE   = 0x23,  /**< Role announcement */

    // Session commands
    CMD_SESSION_START   = 0x30,  /**< Start therapy session */
    CMD_SESSION_STOP    = 0x31,  /**< Stop therapy session */
    CMD_SESSION_PAUSE   = 0x32,  /**< Pause therapy session */
    CMD_SESSION_RESUME  = 0x33,  /**< Resume therapy session */

    // Acknowledgment
    CMD_ACK             = 0x40,  /**< Command acknowledgment */
    CMD_NACK            = 0x41,  /**< Command negative acknowledgment */

    CMD_INVALID         = 0xFF   /**< Invalid command */
} command_type_t;

// ============================================================================
// COMMAND STRUCTURE
// ============================================================================

/**
 * @brief Command message structure
 *
 * All fields are explicitly sized for consistent BLE transmission.
 * Total size: 16 bytes (fits in single BLE packet)
 */
typedef struct __attribute__((packed)) {
    uint8_t  type;           /**< Command type (command_type_t) */
    uint8_t  sequence;       /**< Sequence number for reliability */
    uint16_t payload_value;  /**< Command-specific value (mode, intensity, etc.) */
    uint32_t timestamp_ms;   /**< Command timestamp (ms since boot) */
    uint32_t cycle_ref_ms;   /**< Cycle reference time for synchronization */
    uint16_t checksum;       /**< Simple checksum for integrity */
    uint8_t  reserved[2];    /**< Reserved for future use, zero-filled */
} command_msg_t;

// ============================================================================
// MOTOR COMMAND PAYLOAD
// ============================================================================

/**
 * @brief Motor command specific payload
 */
typedef struct {
    uint8_t  intensity;      /**< Motor intensity (0-100%) */
    uint16_t duration_ms;    /**< Duration in milliseconds */
    uint8_t  pattern;        /**< Pattern type (for future use) */
} motor_payload_t;

// ============================================================================
// CONFIGURATION PAYLOAD
// ============================================================================

/**
 * @brief Configuration command specific payload
 */
typedef struct {
    uint8_t  mode;           /**< Therapy mode (0-4 or custom) */
    uint16_t cycle_ms;       /**< Total bilateral cycle time */
    uint16_t duty_ms;        /**< Active duty time per half-cycle */
    uint8_t  intensity;      /**< Motor intensity percentage */
} config_payload_t;

// ============================================================================
// COMMAND QUEUE CONFIGURATION
// ============================================================================

#define CMD_QUEUE_LENGTH      10    /**< Command queue depth */
#define CMD_QUEUE_TIMEOUT_MS  100   /**< Queue operation timeout */
#define CMD_ACK_TIMEOUT_MS    500   /**< Command acknowledgment timeout */
#define CMD_MAX_RETRIES       3     /**< Maximum command retransmit attempts */

// ============================================================================
// COMMAND VALIDATION
// ============================================================================

/**
 * @brief Validate command message integrity
 * @param cmd Pointer to command message
 * @return true if valid, false otherwise
 */
bool cmd_validate(const command_msg_t *cmd);

/**
 * @brief Calculate checksum for command message
 * @param cmd Pointer to command message
 * @return Calculated checksum value
 */
uint16_t cmd_calculate_checksum(const command_msg_t *cmd);

// ============================================================================
// COMMAND CREATION HELPERS
// ============================================================================

/**
 * @brief Create motor control command
 * @param type Motor command type (FORWARD/REVERSE/COAST/BRAKE)
 * @param intensity Motor intensity (0-100%)
 * @param duration_ms Duration in milliseconds
 * @param sequence Sequence number
 * @return Initialized command message
 */
command_msg_t cmd_create_motor(command_type_t type, uint8_t intensity,
                                uint16_t duration_ms, uint8_t sequence);

/**
 * @brief Create configuration command
 * @param mode Therapy mode
 * @param cycle_ms Total bilateral cycle time
 * @param duty_ms Active duty time
 * @param intensity Motor intensity
 * @param sequence Sequence number
 * @return Initialized command message
 */
command_msg_t cmd_create_config(uint8_t mode, uint16_t cycle_ms,
                                uint16_t duty_ms, uint8_t intensity,
                                uint8_t sequence);

/**
 * @brief Create system command
 * @param type System command type
 * @param sequence Sequence number
 * @return Initialized command message
 */
command_msg_t cmd_create_system(command_type_t type, uint8_t sequence);

/**
 * @brief Create acknowledgment command
 * @param ack_sequence Sequence number being acknowledged
 * @param is_ack true for ACK, false for NACK
 * @return Initialized command message
 */
command_msg_t cmd_create_ack(uint8_t ack_sequence, bool is_ack);

// ============================================================================
// COMMAND PARSING
// ============================================================================

/**
 * @brief Parse motor payload from command
 * @param cmd Command message
 * @param payload Output motor payload structure
 * @return ESP_OK on success
 */
esp_err_t cmd_parse_motor(const command_msg_t *cmd, motor_payload_t *payload);

/**
 * @brief Parse configuration payload from command
 * @param cmd Command message
 * @param payload Output configuration payload structure
 * @return ESP_OK on success
 */
esp_err_t cmd_parse_config(const command_msg_t *cmd, config_payload_t *payload);

// ============================================================================
// COMMAND STRING CONVERSION
// ============================================================================

/**
 * @brief Get human-readable command type name
 * @param type Command type
 * @return String representation of command type
 */
const char* cmd_type_to_string(command_type_t type);

/**
 * @brief Log command message for debugging
 * @param tag Log tag to use
 * @param cmd Command message to log
 * @param prefix Optional prefix string
 */
void cmd_log_message(const char *tag, const command_msg_t *cmd, const char *prefix);

#endif // COMMAND_PROTOCOL_H