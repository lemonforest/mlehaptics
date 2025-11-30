/**
 * @file backemf.c
 * @brief Back-EMF Sensing Module Implementation
 *
 * Implements back-EMF (electromotive force) measurement for motor research.
 * Uses shared ADC1 unit from battery_monitor module.
 *
 * @date November 26, 2025
 * @author Claude Code (Anthropic)
 */

#include "backemf.h"
#include "battery_monitor.h"  // For ADC handle access
#include "esp_log.h"
#include "esp_adc/adc_oneshot.h"
#include "esp_adc/adc_cali.h"

static const char *TAG = "BACKEMF";

// ADC channel for back-EMF (GPIO0 = ADC1_CH0)
#define ADC_CHANNEL_BACKEMF     ADC_CHANNEL_0

esp_err_t backemf_read(int *raw_mv, int16_t *backemf_mv) {
    // Get ADC handle from battery_monitor (shared ADC1 unit)
    adc_oneshot_unit_handle_t adc_handle = battery_get_adc_handle();
    if (adc_handle == NULL) {
        ESP_LOGE(TAG, "ADC not initialized (call battery_monitor_init first)");
        return ESP_ERR_INVALID_STATE;
    }

    // Read ADC
    int adc_raw = 0;
    esp_err_t ret = adc_oneshot_read(adc_handle, ADC_CHANNEL_BACKEMF, &adc_raw);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "ADC read failed: %s", esp_err_to_name(ret));
        return ret;
    }

    // Convert to voltage (mV)
    int voltage_mv = 0;
    if (battery_is_calibrated()) {
        adc_cali_handle_t cali_handle = battery_get_cali_handle();
        ret = adc_cali_raw_to_voltage(cali_handle, adc_raw, &voltage_mv);
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
    // The summing circuit shifts ±3.3V motor signal to 0-3.3V ADC range
    // with 1.65V bias at motor rest (0V back-EMF)
    //
    // Examples:
    // - 1650mV ADC = 0mV motor (at rest)
    // - 3300mV ADC = +3300mV motor (max forward back-EMF)
    // - 0mV ADC = -3300mV motor (max reverse back-EMF)
    *raw_mv = voltage_mv;
    *backemf_mv = 2 * ((int16_t)voltage_mv - BACKEMF_BIAS_MV);

    return ESP_OK;
}
