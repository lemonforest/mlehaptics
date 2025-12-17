/**
 * @file zone_config.h
 * @brief Device Zone Configuration for Bilateral Pattern Playback
 *
 * Provides zone assignment (LEFT/RIGHT) for pattern segment routing.
 * Each bilateral segment contains outputs for both zones - this module
 * tells the device which zone's column to execute.
 *
 * Initial Implementation (2-device):
 * - SERVER = ZONE_RIGHT (starboard)
 * - CLIENT = ZONE_LEFT (port)
 * - Zone derived from role_get_current()
 *
 * Future Expansion (4+ devices / mesh):
 * - Zone assigned via NVS or BLE (independent of role)
 * - Use zone_config_set() to configure
 *
 * @see docs/bilateral_pattern_playback_architecture.md
 * @date December 2025
 * @author Claude Code (Anthropic)
 */

#ifndef ZONE_CONFIG_H
#define ZONE_CONFIG_H

#include <stdint.h>
#include <stdbool.h>
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================================
// ZONE DEFINITIONS
// ============================================================================

/**
 * @brief Physical zone assignment for bilateral patterns
 *
 * Zones represent physical position (LEFT/RIGHT), orthogonal to logical
 * role (SERVER/CLIENT). In 2-device configuration, these are coupled:
 * - SERVER = RIGHT
 * - CLIENT = LEFT
 *
 * In future 4+ device configurations, zones will be explicitly assigned.
 */
typedef enum {
    ZONE_LEFT  = 0,  /**< Left side (port) - typically CLIENT in 2-device mode */
    ZONE_RIGHT = 1   /**< Right side (starboard) - typically SERVER in 2-device mode */
} device_zone_t;

/**
 * @brief Zone assignment mode
 */
typedef enum {
    ZONE_MODE_AUTO = 0,  /**< Derive zone from role (SERVER=RIGHT, CLIENT=LEFT) */
    ZONE_MODE_MANUAL     /**< Zone explicitly set (for 4+ device configurations) */
} zone_mode_t;

// ============================================================================
// PUBLIC API
// ============================================================================

/**
 * @brief Initialize zone configuration module
 * @return ESP_OK on success
 *
 * Sets default mode to ZONE_MODE_AUTO (role-based assignment).
 * Call after role_manager_init().
 */
esp_err_t zone_config_init(void);

/**
 * @brief Get current device zone
 * @return Device zone (LEFT or RIGHT)
 *
 * In AUTO mode: Returns ZONE_RIGHT if SERVER, ZONE_LEFT otherwise.
 * In MANUAL mode: Returns explicitly set zone.
 *
 * Thread-safe: Can be called from any task.
 */
device_zone_t zone_config_get(void);

/**
 * @brief Set device zone explicitly (MANUAL mode)
 * @param zone Zone to assign (ZONE_LEFT or ZONE_RIGHT)
 * @return ESP_OK on success
 *
 * Switches to ZONE_MODE_MANUAL and sets the specified zone.
 * Used for 4+ device configurations where zone != role.
 *
 * Note: In 2-device mode, prefer AUTO mode (leave uncalled).
 */
esp_err_t zone_config_set(device_zone_t zone);

/**
 * @brief Reset to automatic zone assignment
 * @return ESP_OK on success
 *
 * Switches back to ZONE_MODE_AUTO (role-based assignment).
 */
esp_err_t zone_config_reset_to_auto(void);

/**
 * @brief Get current zone assignment mode
 * @return Current mode (AUTO or MANUAL)
 */
zone_mode_t zone_config_get_mode(void);

/**
 * @brief Get human-readable zone name
 * @param zone Device zone
 * @return String representation ("LEFT" or "RIGHT")
 */
const char* zone_to_string(device_zone_t zone);

#ifdef __cplusplus
}
#endif

#endif // ZONE_CONFIG_H
