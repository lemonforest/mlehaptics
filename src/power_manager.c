/**
 * @file power_manager.c
 * @brief Power Management Implementation - Deep sleep and shutdown control
 *
 * Implements centralized power management for EMDR device:
 * - NVS settings save coordination
 * - Peripheral deinitialization sequence
 * - Deep sleep entry with wake source configuration
 * - Battery monitoring and low voltage protection
 *
 * @date November 11, 2025
 * @author Claude Code (Anthropic)
 */

#include "power_manager.h"
#include "ble_manager.h"
#include "battery_monitor.h"
#include "led_control.h"
#include "motor_control.h"
#include "esp_log.h"
#include "esp_sleep.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "POWER_MGR";

// ============================================================================
// SETTINGS SAVE
// ============================================================================

esp_err_t power_save_settings(void) {
    ESP_LOGI(TAG, "Checking if settings need to be saved");

    if (!ble_settings_dirty()) {
        ESP_LOGI(TAG, "Settings are clean (no changes since last save)");
        return ESP_OK;
    }

    ESP_LOGI(TAG, "Settings are dirty, saving to NVS");
    esp_err_t ret = ble_save_settings_to_nvs();

    if (ret == ESP_OK) {
        ESP_LOGI(TAG, "Settings saved successfully");
    } else {
        ESP_LOGE(TAG, "Failed to save settings: %s", esp_err_to_name(ret));
    }

    return ret;
}

// ============================================================================
// PERIPHERAL DEINITIALIZATION
// ============================================================================

esp_err_t power_deinit_peripherals(void) {
    esp_err_t ret;
    esp_err_t overall_ret = ESP_OK;

    ESP_LOGI(TAG, "Deinitializing peripherals for shutdown");

    // 1. Stop BLE advertising and disconnect clients
    if (ble_is_advertising()) {
        ESP_LOGI(TAG, "Stopping BLE advertising");
        ble_stop_advertising();
        vTaskDelay(pdMS_TO_TICKS(100));  // Allow advertising to stop
    }

    // 2. Deinitialize BLE manager (NimBLE shutdown)
    ESP_LOGI(TAG, "Deinitializing BLE manager");
    ret = ble_manager_deinit();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "BLE deinit failed: %s", esp_err_to_name(ret));
        overall_ret = ret;
    }

    // 3. Disable LED power (P-MOSFET gate)
    ESP_LOGI(TAG, "Disabling LED power");
    led_disable();
    vTaskDelay(pdMS_TO_TICKS(50));  // Allow LED shutdown to complete

    // 4. Deinitialize battery monitor (ADC cleanup)
    ESP_LOGI(TAG, "Deinitializing battery monitor");
    ret = battery_monitor_deinit();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Battery monitor deinit failed: %s", esp_err_to_name(ret));
        overall_ret = ret;
    }

    ESP_LOGI(TAG, "Peripheral deinitialization complete");
    return overall_ret;
}

// ============================================================================
// DEEP SLEEP
// ============================================================================

void power_enter_deep_sleep(bool save_settings) {
    ESP_LOGI(TAG, "Entering deep sleep sequence");

    // 1. Coast motor immediately (safe state)
    motor_coast(false);  // Shutdown - no logging needed
    led_clear();

    // 2. Save settings if requested
    if (save_settings) {
        esp_err_t ret = power_save_settings();
        if (ret != ESP_OK) {
            ESP_LOGW(TAG, "Settings save failed, continuing to sleep anyway");
        }
    }

    // 3. Deinitialize peripherals
    esp_err_t ret = power_deinit_peripherals();
    if (ret != ESP_OK) {
        ESP_LOGW(TAG, "Peripheral deinit had errors, continuing to sleep anyway");
    }

    // 4. Configure wake source (button press on GPIO1)
    ESP_LOGI(TAG, "Configuring EXT1 wake on GPIO%d (button)", POWER_WAKE_BUTTON_GPIO);
    ret = esp_sleep_enable_ext1_wakeup((1ULL << POWER_WAKE_BUTTON_GPIO), ESP_EXT1_WAKEUP_ANY_LOW);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to configure wake source: %s", esp_err_to_name(ret));
        ESP_LOGE(TAG, "Continuing to deep sleep anyway (will not wake on button)");
    }

    // 5. Enter deep sleep (never returns)
    ESP_LOGI(TAG, "Entering deep sleep (wake on button press)");
    vTaskDelay(pdMS_TO_TICKS(100));  // Allow log to flush
    esp_deep_sleep_start();

    // Never reached
    ESP_LOGE(TAG, "ERROR: Returned from esp_deep_sleep_start() - this should never happen");
    while (1) {
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}

// ============================================================================
// BATTERY MONITORING
// ============================================================================

bool power_check_battery(void) {
    int raw_mv = 0;
    float battery_v = 0.0f;
    int battery_pct = 0;

    esp_err_t ret = battery_read_voltage(&raw_mv, &battery_v, &battery_pct);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Battery check failed: cannot read voltage");
        return true;  // Allow operation if we can't read battery
    }

    ESP_LOGI(TAG, "Battery check: %.2fV [%d%%]", battery_v, battery_pct);

    // Check if no battery present (< 0.5V)
    if (battery_v < LVO_NO_BATTERY_THRESHOLD) {
        ESP_LOGW(TAG, "No battery detected (%.2fV) - allowing operation", battery_v);
        ESP_LOGW(TAG, "Device can be programmed/tested without battery");
        return true;  // Skip LVO, continue operation
    }

    // Check if voltage below cutoff threshold
    if (battery_v < LVO_CUTOFF_VOLTAGE) {
        ESP_LOGW(TAG, "LVO TRIGGERED: %.2fV below cutoff (%.2fV)", battery_v, LVO_CUTOFF_VOLTAGE);

        // Flash warning if voltage in warning range
        if (battery_v >= LVO_WARNING_VOLTAGE) {
            battery_low_battery_warning();
        }

        // Enter deep sleep (never returns)
        ESP_LOGI(TAG, "Entering deep sleep due to LVO");
        power_enter_deep_sleep(true);  // Save settings before sleep

        // Never reached
        return false;
    }

    // Check if voltage in warning range
    if (battery_v < LVO_WARNING_VOLTAGE) {
        ESP_LOGW(TAG, "Battery low (%.2fV) - flashing warning", battery_v);
        battery_low_battery_warning();
    }

    // Voltage is safe
    ESP_LOGI(TAG, "Battery OK (%.2fV)", battery_v);
    return true;
}

bool power_battery_ok(void) {
    int raw_mv = 0;
    float battery_v = 0.0f;
    int battery_pct = 0;

    esp_err_t ret = battery_read_voltage(&raw_mv, &battery_v, &battery_pct);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Battery check failed: cannot read voltage");
        return true;  // Allow operation if we can't read battery
    }

    // Check if no battery present (< 0.5V)
    if (battery_v < LVO_NO_BATTERY_THRESHOLD) {
        return true;  // No battery, allow operation
    }

    // Check if voltage below cutoff threshold
    if (battery_v < LVO_CUTOFF_VOLTAGE) {
        return false;  // Battery critical
    }

    // Voltage is safe
    return true;
}
