/**
 * @file battery_monitor.c
 * @brief Battery Monitoring Module Implementation
 *
 * Implements ADC-based battery voltage and back-EMF sensing for EMDR device.
 * Extracted from single_device_ble_gatt_test.c reference implementation.
 *
 * @date November 11, 2025
 * @author Claude Code (Anthropic)
 */

#include "battery_monitor.h"
#include "button_task.h"  // For GPIO_BUTTON definition
#include "status_led.h"   // For status LED patterns
#include "esp_log.h"
#include "esp_adc/adc_oneshot.h"
#include "esp_adc/adc_cali.h"
#include "esp_adc/adc_cali_scheme.h"
#include "driver/gpio.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_sleep.h"

static const char *TAG = "BAT_MONITOR";

// ============================================================================
// GPIO DEFINITIONS
// ============================================================================

#define GPIO_BACKEMF            0       // ADC1_CH0
#define GPIO_BAT_VOLTAGE        2       // ADC1_CH2
#define GPIO_BAT_ENABLE         21      // Battery monitor enable

// ============================================================================
// ADC CONFIGURATION
// ============================================================================

#define ADC_UNIT                ADC_UNIT_1
#define ADC_CHANNEL_BACKEMF     ADC_CHANNEL_0
#define ADC_CHANNEL_BATTERY     ADC_CHANNEL_2
#define ADC_ATTEN               ADC_ATTEN_DB_12
#define ADC_BITWIDTH            ADC_BITWIDTH_12

// ============================================================================
// BATTERY VOLTAGE DIVIDER
// ============================================================================

/**
 * Hardware voltage divider: 3.3kΩ (top) + 10kΩ (bottom) = 13.3kΩ total
 * Divider ratio = 10.0 / (3.3 + 10.0) = 0.7519
 * Voltage multiplier = 1 / 0.7519 = 1.33
 */
#define RESISTOR_TOP_KOHM       3.3f
#define RESISTOR_BOTTOM_KOHM    10.0f
#define DIVIDER_RATIO           (RESISTOR_BOTTOM_KOHM / (RESISTOR_TOP_KOHM + RESISTOR_BOTTOM_KOHM))
#define VOLTAGE_MULTIPLIER      (1.0f / DIVIDER_RATIO)

// ============================================================================
// LED CONTROL
// ============================================================================
// STATIC VARIABLES
// ============================================================================

static adc_oneshot_unit_handle_t adc_handle = NULL;
static adc_cali_handle_t adc_cali_handle = NULL;
static bool adc_calibrated = false;

// ============================================================================
// ADC CALIBRATION
// ============================================================================

/**
 * @brief Initialize ADC calibration scheme
 * @param out_handle Output: Calibration handle (NULL if calibration unavailable)
 * @return true if calibration successful, false otherwise
 *
 * Tries curve fitting first (more accurate), falls back to line fitting if unavailable
 */
static bool adc_calibration_init(adc_cali_handle_t *out_handle) {
    adc_cali_handle_t handle = NULL;
    esp_err_t ret = ESP_FAIL;
    bool calibrated = false;

#if ADC_CALI_SCHEME_CURVE_FITTING_SUPPORTED
    adc_cali_curve_fitting_config_t cali_config = {
        .unit_id = ADC_UNIT,
        .atten = ADC_ATTEN,
        .bitwidth = ADC_BITWIDTH,
    };
    ret = adc_cali_create_scheme_curve_fitting(&cali_config, &handle);
    if (ret == ESP_OK) {
        calibrated = true;
        ESP_LOGI(TAG, "ADC calibration: Curve Fitting");
    }
#endif

#if ADC_CALI_SCHEME_LINE_FITTING_SUPPORTED
    if (!calibrated) {
        adc_cali_line_fitting_config_t cali_config = {
            .unit_id = ADC_UNIT,
            .atten = ADC_ATTEN,
            .bitwidth = ADC_BITWIDTH,
        };
        ret = adc_cali_create_scheme_line_fitting(&cali_config, &handle);
        if (ret == ESP_OK) {
            calibrated = true;
            ESP_LOGI(TAG, "ADC calibration: Line Fitting");
        }
    }
#endif

    *out_handle = handle;
    if (!calibrated) {
        ESP_LOGW(TAG, "ADC calibration not available (will use raw ADC values)");
    }
    return calibrated;
}

// ============================================================================
// PUBLIC API IMPLEMENTATION
// ============================================================================

esp_err_t battery_monitor_init(void) {
    esp_err_t ret;

    ESP_LOGI(TAG, "Initializing battery monitor...");

    // Configure GPIO21 for battery monitor enable (output, start LOW)
    gpio_config_t bat_en_cfg = {
        .pin_bit_mask = (1ULL << GPIO_BAT_ENABLE),
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE
    };
    ret = gpio_config(&bat_en_cfg);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to configure GPIO_BAT_ENABLE: %s", esp_err_to_name(ret));
        return ret;
    }
    gpio_set_level(GPIO_BAT_ENABLE, 0);  // Start disabled

    // Status LED is handled by status_led module

    // Initialize ADC1 unit
    adc_oneshot_unit_init_cfg_t init_config = {
        .unit_id = ADC_UNIT,
        .ulp_mode = ADC_ULP_MODE_DISABLE,
    };

    ret = adc_oneshot_new_unit(&init_config, &adc_handle);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to init ADC unit: %s", esp_err_to_name(ret));
        return ret;
    }

    // Configure back-EMF channel (GPIO0 = ADC1_CH0)
    adc_oneshot_chan_cfg_t backemf_config = {
        .atten = ADC_ATTEN,
        .bitwidth = ADC_BITWIDTH
    };
    ret = adc_oneshot_config_channel(adc_handle, ADC_CHANNEL_BACKEMF, &backemf_config);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to config back-EMF channel: %s", esp_err_to_name(ret));
        adc_oneshot_del_unit(adc_handle);
        return ret;
    }

    // Configure battery voltage channel (GPIO2 = ADC1_CH2)
    adc_oneshot_chan_cfg_t battery_config = {
        .atten = ADC_ATTEN,
        .bitwidth = ADC_BITWIDTH
    };
    ret = adc_oneshot_config_channel(adc_handle, ADC_CHANNEL_BATTERY, &battery_config);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to config battery channel: %s", esp_err_to_name(ret));
        adc_oneshot_del_unit(adc_handle);
        return ret;
    }

    // Initialize ADC calibration (optional, but improves accuracy)
    adc_calibrated = adc_calibration_init(&adc_cali_handle);

    ESP_LOGI(TAG, "Battery monitor initialized successfully");
    return ESP_OK;
}

esp_err_t battery_read_voltage(int *raw_voltage_mv, float *battery_voltage_v, int *battery_percentage) {
    if (adc_handle == NULL) {
        ESP_LOGE(TAG, "ADC not initialized");
        return ESP_ERR_INVALID_STATE;
    }

    // Enable battery monitor circuit
    gpio_set_level(GPIO_BAT_ENABLE, 1);
    vTaskDelay(pdMS_TO_TICKS(BAT_ENABLE_SETTLE_MS));

    // Read ADC
    int adc_raw = 0;
    esp_err_t ret = adc_oneshot_read(adc_handle, ADC_CHANNEL_BATTERY, &adc_raw);
    if (ret != ESP_OK) {
        gpio_set_level(GPIO_BAT_ENABLE, 0);
        ESP_LOGE(TAG, "ADC read failed: %s", esp_err_to_name(ret));
        return ret;
    }

    // Convert to voltage (mV)
    int voltage_mv = 0;
    if (adc_calibrated) {
        ret = adc_cali_raw_to_voltage(adc_cali_handle, adc_raw, &voltage_mv);
        if (ret != ESP_OK) {
            // Calibration failed, use raw conversion
            voltage_mv = (adc_raw * 3300) / 4095;
            ESP_LOGW(TAG, "Calibration conversion failed, using raw: %dmV", voltage_mv);
        }
    } else {
        // No calibration available, use raw 12-bit ADC conversion
        voltage_mv = (adc_raw * 3300) / 4095;
    }

    // Disable battery monitor circuit (reduce idle current)
    gpio_set_level(GPIO_BAT_ENABLE, 0);

    // Apply voltage divider multiplier to get actual battery voltage
    float battery_v = (voltage_mv / 1000.0f) * VOLTAGE_MULTIPLIER;

    // Calculate percentage: (V - MIN) / (MAX - MIN) × 100
    float percentage_f = ((battery_v - BAT_VOLTAGE_MIN) / (BAT_VOLTAGE_MAX - BAT_VOLTAGE_MIN)) * 100.0f;
    if (percentage_f < 0.0f) percentage_f = 0.0f;
    if (percentage_f > 100.0f) percentage_f = 100.0f;

    // Write outputs
    *raw_voltage_mv = voltage_mv;
    *battery_voltage_v = battery_v;
    *battery_percentage = (int)percentage_f;

    return ESP_OK;
}

bool battery_check_lvo(void) {
    int raw_mv = 0;
    float battery_v = 0.0f;
    int percentage = 0;

    esp_err_t ret = battery_read_voltage(&raw_mv, &battery_v, &percentage);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "LVO check failed: cannot read battery");
        return true;  // Allow operation if we can't read battery
    }

    ESP_LOGI(TAG, "LVO check: %.2fV [%d%%]", battery_v, percentage);

    // Check if no battery present (< 0.5V)
    if (battery_v < LVO_NO_BATTERY_THRESHOLD) {
        ESP_LOGW(TAG, "LVO check: No battery detected (%.2fV) - allowing operation", battery_v);
        ESP_LOGW(TAG, "Device can be programmed/tested without battery");
        ESP_LOGI(TAG, "LVO check: SKIPPED - no battery present");
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
        vTaskDelay(pdMS_TO_TICKS(100));  // Allow log to flush
        esp_sleep_enable_ext1_wakeup((1ULL << GPIO_BUTTON), ESP_EXT1_WAKEUP_ANY_LOW);
        esp_deep_sleep_start();

        return false;  // Never reached
    }

    // Voltage is safe
    return true;
}

void battery_low_battery_warning(void) {
    ESP_LOGI(TAG, "Flashing low battery warning");
    status_led_pattern(STATUS_PATTERN_LOW_BATTERY);  // 3× slow blink (200ms ON/OFF)
}

esp_err_t battery_read_backemf(int *raw_mv, int16_t *actual_backemf_mv) {
    if (adc_handle == NULL) {
        ESP_LOGE(TAG, "ADC not initialized");
        return ESP_ERR_INVALID_STATE;
    }

    // Read ADC
    int adc_raw = 0;
    esp_err_t ret = adc_oneshot_read(adc_handle, ADC_CHANNEL_BACKEMF, &adc_raw);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Back-EMF ADC read failed: %s", esp_err_to_name(ret));
        return ret;
    }

    // Convert to voltage (mV)
    int voltage_mv = 0;
    if (adc_calibrated) {
        ret = adc_cali_raw_to_voltage(adc_cali_handle, adc_raw, &voltage_mv);
        if (ret != ESP_OK) {
            // Calibration failed, use raw conversion
            voltage_mv = (adc_raw * 3300) / 4095;
        }
    } else {
        // No calibration available
        voltage_mv = (adc_raw * 3300) / 4095;
    }

    // Convert to actual back-EMF
    // Formula: V_motor = 2 × (V_adc - 1.65V)
    // Example: 1650mV ADC = 0mV motor (at rest)
    // Example: 3300mV ADC = +3300mV motor (max forward)
    // Example: 0mV ADC = -3300mV motor (max reverse)
    *raw_mv = voltage_mv;
    *actual_backemf_mv = 2 * ((int16_t)voltage_mv - BACKEMF_BIAS_MV);

    return ESP_OK;
}

esp_err_t battery_monitor_deinit(void) {
    ESP_LOGI(TAG, "Deinitializing battery monitor...");

    // Delete calibration handle if it exists
    if (adc_calibrated && adc_cali_handle != NULL) {
#if ADC_CALI_SCHEME_CURVE_FITTING_SUPPORTED
        adc_cali_delete_scheme_curve_fitting(adc_cali_handle);
#elif ADC_CALI_SCHEME_LINE_FITTING_SUPPORTED
        adc_cali_delete_scheme_line_fitting(adc_cali_handle);
#endif
        adc_cali_handle = NULL;
        adc_calibrated = false;
    }

    // Delete ADC unit handle
    if (adc_handle != NULL) {
        esp_err_t ret = adc_oneshot_del_unit(adc_handle);
        if (ret != ESP_OK) {
            ESP_LOGE(TAG, "Failed to delete ADC unit: %s", esp_err_to_name(ret));
            return ret;
        }
        adc_handle = NULL;
    }

    ESP_LOGI(TAG, "Battery monitor deinitialized");
    return ESP_OK;
}
