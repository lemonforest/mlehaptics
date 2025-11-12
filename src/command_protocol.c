/**
 * @file command_protocol.c
 * @brief Command-and-Control Protocol Implementation
 *
 * Implements command message handling for dual-device bilateral stimulation
 * per AD028 specification with synchronized fallback architecture.
 *
 * @date November 11, 2025
 * @author Claude Code (Anthropic)
 */

#include "command_protocol.h"
#include "esp_log.h"
#include <string.h>

static const char *TAG = "CMD_PROTO";

// ============================================================================
// COMMAND VALIDATION
// ============================================================================

bool cmd_validate(const command_msg_t *cmd) {
    if (cmd == NULL) {
        return false;
    }

    // Validate command type
    if (cmd->type == CMD_INVALID) {
        ESP_LOGW(TAG, "Invalid command type: 0x%02X", cmd->type);
        return false;
    }

    // Calculate and verify checksum
    uint16_t calculated = cmd_calculate_checksum(cmd);
    if (calculated != cmd->checksum) {
        ESP_LOGW(TAG, "Checksum mismatch: expected 0x%04X, got 0x%04X",
                 cmd->checksum, calculated);
        return false;
    }

    // Command-specific validation
    switch (cmd->type) {
        case CMD_MOTOR_FORWARD:
        case CMD_MOTOR_REVERSE:
        case CMD_MOTOR_COAST:
        case CMD_MOTOR_BRAKE:
            // Motor commands should have reasonable duration
            if (cmd->payload_value > 10000) {  // Max 10 seconds
                ESP_LOGW(TAG, "Motor command duration too long: %u ms",
                         cmd->payload_value);
                return false;
            }
            break;

        case CMD_CONFIG_MODE:
            // Mode should be in valid range
            if ((cmd->payload_value & 0xFF) > 5) {  // Modes 0-5
                ESP_LOGW(TAG, "Invalid mode: %u", cmd->payload_value & 0xFF);
                return false;
            }
            break;

        case CMD_CONFIG_TIMING:
            // Cycle time should be reasonable (250-4000ms)
            if (cmd->payload_value < 250 || cmd->payload_value > 4000) {
                ESP_LOGW(TAG, "Invalid cycle time: %u ms", cmd->payload_value);
                return false;
            }
            break;

        case CMD_CONFIG_INTENSITY:
            // Intensity should be 0-100%
            if ((cmd->payload_value & 0xFF) > 100) {
                ESP_LOGW(TAG, "Invalid intensity: %u%%", cmd->payload_value & 0xFF);
                return false;
            }
            break;

        default:
            // Other commands have no specific validation
            break;
    }

    return true;
}

uint16_t cmd_calculate_checksum(const command_msg_t *cmd) {
    if (cmd == NULL) {
        return 0;
    }

    // Simple checksum: XOR of all bytes except checksum field itself
    const uint8_t *bytes = (const uint8_t *)cmd;
    uint16_t checksum = 0;

    // Calculate up to checksum field
    size_t checksum_offset = offsetof(command_msg_t, checksum);
    for (size_t i = 0; i < checksum_offset; i++) {
        checksum ^= bytes[i];
        checksum = (checksum << 1) | (checksum >> 15);  // Rotate left by 1
    }

    return checksum;
}

// ============================================================================
// COMMAND CREATION HELPERS
// ============================================================================

command_msg_t cmd_create_motor(command_type_t type, uint8_t intensity,
                                uint16_t duration_ms, uint8_t sequence) {
    command_msg_t cmd = {0};

    cmd.type = type;
    cmd.sequence = sequence;
    cmd.payload_value = duration_ms;
    cmd.timestamp_ms = xTaskGetTickCount() * portTICK_PERIOD_MS;
    cmd.cycle_ref_ms = cmd.timestamp_ms;  // Current time as reference

    // Store intensity in upper byte of payload_value for motor commands
    if (intensity <= 100) {
        cmd.payload_value |= ((uint16_t)intensity << 8);
    }

    // Zero-fill reserved bytes (JPL compliance)
    memset(cmd.reserved, 0, sizeof(cmd.reserved));

    // Calculate checksum last
    cmd.checksum = cmd_calculate_checksum(&cmd);

    ESP_LOGD(TAG, "Created motor command: type=0x%02X, seq=%u, intensity=%u%%, duration=%ums",
             type, sequence, intensity, duration_ms);

    return cmd;
}

command_msg_t cmd_create_config(uint8_t mode, uint16_t cycle_ms,
                                uint16_t duty_ms, uint8_t intensity,
                                uint8_t sequence) {
    command_msg_t cmd = {0};

    cmd.type = CMD_CONFIG_MODE;
    cmd.sequence = sequence;
    cmd.timestamp_ms = xTaskGetTickCount() * portTICK_PERIOD_MS;

    // Pack configuration into available fields
    cmd.payload_value = mode | ((uint16_t)intensity << 8);
    cmd.cycle_ref_ms = (cycle_ms & 0xFFFF) | ((uint32_t)(duty_ms & 0xFFFF) << 16);

    // Zero-fill reserved bytes
    memset(cmd.reserved, 0, sizeof(cmd.reserved));

    // Calculate checksum
    cmd.checksum = cmd_calculate_checksum(&cmd);

    ESP_LOGD(TAG, "Created config command: mode=%u, cycle=%ums, duty=%ums, intensity=%u%%",
             mode, cycle_ms, duty_ms, intensity);

    return cmd;
}

command_msg_t cmd_create_system(command_type_t type, uint8_t sequence) {
    command_msg_t cmd = {0};

    cmd.type = type;
    cmd.sequence = sequence;
    cmd.timestamp_ms = xTaskGetTickCount() * portTICK_PERIOD_MS;
    cmd.cycle_ref_ms = cmd.timestamp_ms;

    // Zero-fill reserved bytes
    memset(cmd.reserved, 0, sizeof(cmd.reserved));

    // Calculate checksum
    cmd.checksum = cmd_calculate_checksum(&cmd);

    ESP_LOGD(TAG, "Created system command: type=0x%02X, seq=%u", type, sequence);

    return cmd;
}

command_msg_t cmd_create_ack(uint8_t ack_sequence, bool is_ack) {
    command_msg_t cmd = {0};

    cmd.type = is_ack ? CMD_ACK : CMD_NACK;
    cmd.sequence = ack_sequence;  // Sequence being acknowledged
    cmd.timestamp_ms = xTaskGetTickCount() * portTICK_PERIOD_MS;

    // Zero-fill reserved bytes
    memset(cmd.reserved, 0, sizeof(cmd.reserved));

    // Calculate checksum
    cmd.checksum = cmd_calculate_checksum(&cmd);

    ESP_LOGD(TAG, "Created %s for sequence %u",
             is_ack ? "ACK" : "NACK", ack_sequence);

    return cmd;
}

// ============================================================================
// COMMAND PARSING
// ============================================================================

esp_err_t cmd_parse_motor(const command_msg_t *cmd, motor_payload_t *payload) {
    if (cmd == NULL || payload == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    // Verify this is a motor command
    switch (cmd->type) {
        case CMD_MOTOR_FORWARD:
        case CMD_MOTOR_REVERSE:
        case CMD_MOTOR_COAST:
        case CMD_MOTOR_BRAKE:
            break;
        default:
            ESP_LOGW(TAG, "Not a motor command: 0x%02X", cmd->type);
            return ESP_ERR_INVALID_ARG;
    }

    // Extract motor payload
    payload->duration_ms = cmd->payload_value & 0x3FFF;  // Lower 14 bits
    payload->intensity = (cmd->payload_value >> 8) & 0xFF;  // Upper byte
    payload->pattern = 0;  // Reserved for future use

    ESP_LOGD(TAG, "Parsed motor command: duration=%ums, intensity=%u%%",
             payload->duration_ms, payload->intensity);

    return ESP_OK;
}

esp_err_t cmd_parse_config(const command_msg_t *cmd, config_payload_t *payload) {
    if (cmd == NULL || payload == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    // Verify this is a config command
    if (cmd->type != CMD_CONFIG_MODE) {
        ESP_LOGW(TAG, "Not a config command: 0x%02X", cmd->type);
        return ESP_ERR_INVALID_ARG;
    }

    // Extract configuration payload
    payload->mode = cmd->payload_value & 0xFF;
    payload->intensity = (cmd->payload_value >> 8) & 0xFF;
    payload->cycle_ms = cmd->cycle_ref_ms & 0xFFFF;
    payload->duty_ms = (cmd->cycle_ref_ms >> 16) & 0xFFFF;

    ESP_LOGD(TAG, "Parsed config: mode=%u, cycle=%ums, duty=%ums, intensity=%u%%",
             payload->mode, payload->cycle_ms, payload->duty_ms, payload->intensity);

    return ESP_OK;
}

// ============================================================================
// COMMAND STRING CONVERSION
// ============================================================================

const char* cmd_type_to_string(command_type_t type) {
    switch (type) {
        // Motor commands
        case CMD_MOTOR_FORWARD:     return "MOTOR_FORWARD";
        case CMD_MOTOR_REVERSE:     return "MOTOR_REVERSE";
        case CMD_MOTOR_COAST:       return "MOTOR_COAST";
        case CMD_MOTOR_BRAKE:       return "MOTOR_BRAKE";

        // Configuration commands
        case CMD_CONFIG_MODE:       return "CONFIG_MODE";
        case CMD_CONFIG_TIMING:     return "CONFIG_TIMING";
        case CMD_CONFIG_INTENSITY:  return "CONFIG_INTENSITY";

        // System commands
        case CMD_SYNC_TIME:         return "SYNC_TIME";
        case CMD_HEARTBEAT:         return "HEARTBEAT";
        case CMD_SHUTDOWN:          return "SHUTDOWN";
        case CMD_ROLE_ANNOUNCE:     return "ROLE_ANNOUNCE";

        // Session commands
        case CMD_SESSION_START:     return "SESSION_START";
        case CMD_SESSION_STOP:      return "SESSION_STOP";
        case CMD_SESSION_PAUSE:     return "SESSION_PAUSE";
        case CMD_SESSION_RESUME:    return "SESSION_RESUME";

        // Acknowledgments
        case CMD_ACK:               return "ACK";
        case CMD_NACK:              return "NACK";

        case CMD_INVALID:
        default:                    return "INVALID";
    }
}

void cmd_log_message(const char *tag, const command_msg_t *cmd, const char *prefix) {
    if (cmd == NULL) {
        ESP_LOGW(tag, "%s: NULL command", prefix ? prefix : "Command");
        return;
    }

    const char *type_str = cmd_type_to_string(cmd->type);

    ESP_LOGI(tag, "%s: %s (0x%02X) seq=%u, ts=%u ms, payload=0x%04X, chk=0x%04X",
             prefix ? prefix : "Command",
             type_str,
             cmd->type,
             cmd->sequence,
             cmd->timestamp_ms,
             cmd->payload_value,
             cmd->checksum);

    // Log additional details for specific commands
    if (cmd->type >= CMD_MOTOR_FORWARD && cmd->type <= CMD_MOTOR_BRAKE) {
        uint8_t intensity = (cmd->payload_value >> 8) & 0xFF;
        uint16_t duration = cmd->payload_value & 0x3FFF;
        ESP_LOGD(tag, "  Motor: intensity=%u%%, duration=%u ms", intensity, duration);
    }
}