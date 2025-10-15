/**
 * @file main.c
 * @brief EMDR Bilateral Stimulation Device - Configuration Test
 * 
 * This is a minimal test file to verify platformio.ini configuration.
 * It confirms ESP-IDF version and displays system information.
 * 
 * @note This is NOT the full application - just a configuration test
 * 
 * Generated with assistance from Claude Sonnet 4 (Anthropic)
 * Last Updated: 2025-10-15
 */

#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_system.h"
#include "esp_log.h"
#include "esp_chip_info.h"
#include "esp_flash.h"

static const char *TAG = "CONFIG_TEST";

/**
 * @brief Main application entry point
 * 
 * This test function verifies:
 * - ESP-IDF version is correct
 * - ESP32-C6 chip information
 * - Build configuration defines
 * - Memory availability
 */
void app_main(void)
{
    ESP_LOGI(TAG, "========================================");
    ESP_LOGI(TAG, "EMDR Bilateral Stimulation Device");
    ESP_LOGI(TAG, "Configuration Verification Test");
    ESP_LOGI(TAG, "========================================");
    
    /* ESP-IDF Version Check */
    ESP_LOGI(TAG, "ESP-IDF Version: %s", esp_get_idf_version());
    
    #if ESP_IDF_VERSION >= ESP_IDF_VERSION_VAL(5, 5, 0)
        ESP_LOGI(TAG, "✓ ESP-IDF v5.5.x or later detected");
    #elif ESP_IDF_VERSION >= ESP_IDF_VERSION_VAL(5, 0, 0)
        ESP_LOGW(TAG, "⚠ ESP-IDF v5.x detected but not v5.5+");
        ESP_LOGW(TAG, "⚠ Please update to ESP-IDF v5.5.1 for full compatibility");
    #else
        ESP_LOGE(TAG, "✗ ESP-IDF version is too old!");
        ESP_LOGE(TAG, "✗ This project requires ESP-IDF v5.5.1 or later");
    #endif
    
    /* Chip Information */
    esp_chip_info_t chip_info;
    esp_chip_info(&chip_info);
    
    ESP_LOGI(TAG, "========================================");
    ESP_LOGI(TAG, "Hardware Information:");
    ESP_LOGI(TAG, "========================================");
    ESP_LOGI(TAG, "Chip: %s", CONFIG_IDF_TARGET);
    ESP_LOGI(TAG, "Cores: %d", chip_info.cores);
    ESP_LOGI(TAG, "Features: %s%s%s%s",
             (chip_info.features & CHIP_FEATURE_WIFI_BGN) ? "WiFi/" : "",
             (chip_info.features & CHIP_FEATURE_BT) ? "BT/" : "",
             (chip_info.features & CHIP_FEATURE_BLE) ? "BLE/" : "",
             (chip_info.features & CHIP_FEATURE_IEEE802154) ? "IEEE802.15.4" : "");
    
    ESP_LOGI(TAG, "Silicon Revision: %d", chip_info.revision);
    
    /* Flash Information */
    uint32_t flash_size;
    esp_flash_get_size(NULL, &flash_size);
    ESP_LOGI(TAG, "Flash Size: %lu MB", flash_size / (1024 * 1024));
    
    /* Memory Information */
    ESP_LOGI(TAG, "Free Heap: %lu bytes", esp_get_free_heap_size());
    ESP_LOGI(TAG, "Minimum Free Heap: %lu bytes", esp_get_minimum_free_heap_size());
    
    /* Build Configuration Check */
    ESP_LOGI(TAG, "========================================");
    ESP_LOGI(TAG, "Build Configuration:");
    ESP_LOGI(TAG, "========================================");
    
    #ifdef JPL_COMPLIANT_BUILD
        ESP_LOGI(TAG, "✓ JPL Compliant Build: ENABLED");
    #else
        ESP_LOGW(TAG, "⚠ JPL Compliant Build: DISABLED");
    #endif
    
    #ifdef SAFETY_CRITICAL
        ESP_LOGI(TAG, "✓ Safety Critical Mode: ENABLED");
    #else
        ESP_LOGW(TAG, "⚠ Safety Critical Mode: DISABLED");
    #endif
    
    #ifdef TESTING_MODE
        ESP_LOGI(TAG, "✓ Testing Mode: ENABLED");
    #else
        ESP_LOGI(TAG, "  Testing Mode: DISABLED (Production)");
    #endif
    
    #ifdef ENABLE_FACTORY_RESET
        ESP_LOGI(TAG, "✓ Factory Reset: ENABLED");
    #else
        ESP_LOGI(TAG, "  Factory Reset: DISABLED");
    #endif
    
    #ifdef DEBUG_LEVEL
        ESP_LOGI(TAG, "Debug Level: %d", DEBUG_LEVEL);
    #endif
    
    ESP_LOGI(TAG, "========================================");
    ESP_LOGI(TAG, "Configuration Test Complete!");
    ESP_LOGI(TAG, "========================================");
    ESP_LOGI(TAG, " ");
    ESP_LOGI(TAG, "Next Steps:");
    ESP_LOGI(TAG, "1. Verify ESP-IDF version is v5.5.x");
    ESP_LOGI(TAG, "2. Verify chip is ESP32-C6");
    ESP_LOGI(TAG, "3. Verify build flags are enabled");
    ESP_LOGI(TAG, "4. Update docs/platformio_verification.md with results");
    ESP_LOGI(TAG, " ");
    ESP_LOGI(TAG, "If all checks passed, configuration is VERIFIED! ✓");
    ESP_LOGI(TAG, " ");
    
    /* Keep running */
    while (1) {
        vTaskDelay(pdMS_TO_TICKS(10000));  /* Delay 10 seconds */
        ESP_LOGI(TAG, "System running... (ESP-IDF %s on %s)", 
                 esp_get_idf_version(), CONFIG_IDF_TARGET);
    }
}
