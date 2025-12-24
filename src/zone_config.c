/**
 * @file zone_config.c
 * @brief Device Zone Configuration Implementation
 *
 * @see zone_config.h for API documentation
 * @date December 2025
 * @author Claude Code (Anthropic)
 */

#include "zone_config.h"
#include "role_manager.h"
#include "esp_log.h"

static const char *TAG = "ZONE_CONFIG";

// ============================================================================
// MODULE STATE
// ============================================================================

static struct {
    zone_mode_t mode;          /**< Current assignment mode */
    device_zone_t manual_zone; /**< Zone when in MANUAL mode */
    bool initialized;          /**< Module initialized flag */
} zone_state = {
    .mode = ZONE_MODE_AUTO,
    .manual_zone = ZONE_LEFT,
    .initialized = false
};

// ============================================================================
// PUBLIC API IMPLEMENTATION
// ============================================================================

esp_err_t zone_config_init(void)
{
    zone_state.mode = ZONE_MODE_AUTO;
    zone_state.manual_zone = ZONE_LEFT;
    zone_state.initialized = true;

    ESP_LOGI(TAG, "Zone config initialized (AUTO mode)");
    return ESP_OK;
}

device_zone_t zone_config_get(void)
{
    if (!zone_state.initialized) {
        // Default to AUTO behavior even if not initialized
        device_role_t role = role_get_current();
        return (role == ROLE_SERVER) ? ZONE_RIGHT : ZONE_LEFT;
    }

    if (zone_state.mode == ZONE_MODE_MANUAL) {
        return zone_state.manual_zone;
    }

    // AUTO mode: derive from role
    // SERVER = RIGHT (starboard), CLIENT/others = LEFT (port)
    device_role_t role = role_get_current();
    return (role == ROLE_SERVER) ? ZONE_RIGHT : ZONE_LEFT;
}

esp_err_t zone_config_set(device_zone_t zone)
{
    if (zone != ZONE_LEFT && zone != ZONE_RIGHT) {
        ESP_LOGE(TAG, "Invalid zone: %d", zone);
        return ESP_ERR_INVALID_ARG;
    }

    zone_state.mode = ZONE_MODE_MANUAL;
    zone_state.manual_zone = zone;

    ESP_LOGI(TAG, "Zone manually set to %s", zone_to_string(zone));
    return ESP_OK;
}

esp_err_t zone_config_reset_to_auto(void)
{
    zone_state.mode = ZONE_MODE_AUTO;
    ESP_LOGI(TAG, "Zone config reset to AUTO mode");
    return ESP_OK;
}

zone_mode_t zone_config_get_mode(void)
{
    return zone_state.mode;
}

const char* zone_to_string(device_zone_t zone)
{
    switch (zone) {
        case ZONE_LEFT:  return "LEFT";
        case ZONE_RIGHT: return "RIGHT";
        default:         return "UNKNOWN";
    }
}
