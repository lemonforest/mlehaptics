/**
 * @file nvs_manager.c
 * @brief NVS Manager Implementation - Non-Volatile Storage management
 *
 * Implements centralized NVS operations for EMDR device:
 * - NVS flash initialization with automatic recovery
 * - Factory reset (clear all NVS data)
 * - NVS initialization state tracking
 *
 * @date November 11, 2025
 * @author Claude Code (Anthropic)
 */

#include "nvs_manager.h"
#include "nvs_flash.h"
#include "esp_log.h"

static const char *TAG = "NVS_MGR";

// ============================================================================
// STATE TRACKING
// ============================================================================

static bool nvs_initialized = false;

// ============================================================================
// PUBLIC API IMPLEMENTATION
// ============================================================================

esp_err_t nvs_manager_init(void) {
    if (nvs_initialized) {
        ESP_LOGI(TAG, "NVS already initialized");
        return ESP_OK;
    }

    ESP_LOGI(TAG, "Initializing NVS flash");

    esp_err_t ret = nvs_flash_init();

    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        // NVS partition was truncated or version changed
        // Erase and retry initialization
        ESP_LOGW(TAG, "NVS init failed (%s), erasing and retrying", esp_err_to_name(ret));

        ret = nvs_flash_erase();
        if (ret != ESP_OK) {
            ESP_LOGE(TAG, "NVS erase failed: %s", esp_err_to_name(ret));
            return ret;
        }

        ret = nvs_flash_init();
        if (ret != ESP_OK) {
            ESP_LOGE(TAG, "NVS init retry failed: %s", esp_err_to_name(ret));
            return ret;
        }

        ESP_LOGI(TAG, "NVS erased and reinitialized successfully");
    } else if (ret != ESP_OK) {
        ESP_LOGE(TAG, "NVS init failed: %s", esp_err_to_name(ret));
        return ret;
    }

    nvs_initialized = true;
    ESP_LOGI(TAG, "NVS flash initialized successfully");
    return ESP_OK;
}

esp_err_t nvs_clear_all(void) {
    ESP_LOGI(TAG, "Clearing all NVS data (factory reset)");

    // Erase NVS partition
    esp_err_t ret = nvs_flash_erase();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "NVS erase failed: %s", esp_err_to_name(ret));
        return ret;
    }

    ESP_LOGI(TAG, "NVS partition erased");

    // Reinitialize NVS
    nvs_initialized = false;
    ret = nvs_manager_init();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "NVS reinit after erase failed: %s", esp_err_to_name(ret));
        return ret;
    }

    ESP_LOGI(TAG, "Factory reset complete (all NVS data cleared)");
    return ESP_OK;
}

bool nvs_is_initialized(void) {
    return nvs_initialized;
}
