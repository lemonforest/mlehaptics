/**
 * @file battery_monitor.h
 * @brief Battery Monitoring Module - ADC-based voltage and back-EMF sensing
 *
 * This module provides battery voltage monitoring and back-EMF measurement
 * capabilities for the EMDR bilateral stimulation device. It implements:
 * - LiPo battery voltage sensing with resistive divider (3.0-4.2V range)
 * - Percentage calculation for battery state of charge
 * - Low voltage cutout (LVO) protection at 3.2V
 * - Back-EMF sensing for motor research (±3.3V with 1.65V bias)
 * - ADC calibration using curve fitting or line fitting
 *
 * Hardware Configuration:
 * - GPIO2 (ADC1_CH2): Battery voltage via 3.3kΩ/10kΩ divider
 * - GPIO0 (ADC1_CH0): Back-EMF via summing circuit with 1.65V offset
 * - GPIO21: Battery monitor enable (HIGH=enabled, reduces idle current)
 *
 * ADC Configuration:
 * - ADC1 unit (independent from WiFi/BLE)
 * - 12-bit resolution (0-4095)
 * - 12dB attenuation (0-3.3V range)
 * - One-shot mode (on-demand sampling)
 *
 * @date November 11, 2025
 * @author Claude Code (Anthropic)
 */

#ifndef BATTERY_MONITOR_H
#define BATTERY_MONITOR_H

#include <stdint.h>
#include <stdbool.h>
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================================
// BATTERY VOLTAGE THRESHOLDS
// ============================================================================

/**
 * @brief Battery voltage thresholds for LiPo cells
 *
 * Based on standard LiPo discharge curves:
 * - 4.2V: Fully charged
 * - 3.7V: Nominal voltage
 * - 3.0V: Empty (min safe discharge)
 */
#define BAT_VOLTAGE_MAX         4.2f    /**< Fully charged (100%) */
#define BAT_VOLTAGE_MIN         3.0f    /**< Empty (0%) */
#define LVO_CUTOFF_VOLTAGE      3.2f    /**< Low voltage cutout threshold */
#define LVO_WARNING_VOLTAGE     3.0f    /**< Warning threshold (visual indicator) */
#define LVO_NO_BATTERY_THRESHOLD 0.5f   /**< Below this = no battery present */

/**
 * @brief Battery monitoring intervals
 */
#define BAT_READ_INTERVAL_MS    10000   /**< Check battery every 10 seconds */
#define BAT_ENABLE_SETTLE_MS    10      /**< Wait 10ms after enabling monitor */

// ============================================================================
// BACK-EMF CONFIGURATION
// ============================================================================

/**
 * @brief Back-EMF bias voltage (1.65V offset for ±3.3V signals)
 *
 * Motor H-bridge produces -3.3V to +3.3V during coast
 * Voltage divider with 1.65V offset shifts this to 0V to 3.3V for ADC
 */
#define BACKEMF_BIAS_MV         1650    /**< ADC bias voltage in millivolts */
#define BACKEMF_SETTLE_MS       10      /**< Wait 10ms after motor off for sampling */

// ============================================================================
// PUBLIC API
// ============================================================================

/**
 * @brief Initialize battery monitoring subsystem
 * @return ESP_OK on success, error code on failure
 *
 * Configures:
 * - ADC1 unit with 12-bit resolution, 12dB attenuation
 * - GPIO2 (ADC1_CH2) for battery voltage sensing
 * - GPIO0 (ADC1_CH0) for back-EMF sensing
 * - ADC calibration (curve fitting or line fitting)
 * - GPIO21 as output for battery monitor enable
 *
 * Must be called before any battery reading functions
 */
esp_err_t battery_monitor_init(void);

/**
 * @brief Read battery voltage and calculate percentage
 * @param raw_voltage_mv Output: ADC voltage in millivolts (before divider multiply)
 * @param battery_voltage_v Output: Actual battery voltage in volts (3.0-4.2V)
 * @param battery_percentage Output: Battery percentage 0-100%
 * @return ESP_OK on success, error code on failure
 *
 * Process:
 * 1. Enable battery monitor (GPIO21 = HIGH)
 * 2. Wait BAT_ENABLE_SETTLE_MS for voltage to stabilize
 * 3. Read ADC value and apply calibration
 * 4. Multiply by voltage divider ratio (13.3kΩ / 10kΩ)
 * 5. Calculate percentage: (V - 3.0) / (4.2 - 3.0) × 100
 * 6. Disable battery monitor (GPIO21 = LOW)
 *
 * Voltage divider: 3.3kΩ (top) + 10kΩ (bottom) = 13.3kΩ total
 * Multiplier: 13.3 / 10.0 = 1.33
 */
esp_err_t battery_read_voltage(int *raw_voltage_mv, float *battery_voltage_v, int *battery_percentage);

/**
 * @brief Check for low voltage cutout condition
 * @return true if voltage is safe to continue, false if LVO triggered
 *
 * Behavior:
 * - If battery < LVO_NO_BATTERY_THRESHOLD (0.5V): Skip check, allow operation (no battery present)
 * - If battery < LVO_CUTOFF_VOLTAGE (3.2V): Trigger LVO, enter deep sleep
 * - If LVO_WARNING_VOLTAGE < battery < LVO_CUTOFF_VOLTAGE: Flash LED warning before sleep
 * - Otherwise: Return true, safe to continue
 *
 * Called at startup and during operation if MSG_BATTERY_CRITICAL received
 * Never returns if LVO triggered (enters deep sleep)
 */
bool battery_check_lvo(void);

/**
 * @brief Flash LED to indicate low battery warning
 *
 * Flashes GPIO15 (status LED) 3 times:
 * - 200ms ON, 200ms OFF (repeat 3×)
 * - Total duration: 1200ms
 *
 * Called before LVO deep sleep if voltage in warning range
 */
void battery_low_battery_warning(void);

/**
 * @brief Read back-EMF voltage from motor
 * @param raw_mv Output: ADC voltage in millivolts (0-3300mV range)
 * @param actual_backemf_mv Output: Actual back-EMF in millivolts (±3300mV range)
 * @return ESP_OK on success, error code on failure
 *
 * Conversion formula:
 * - ADC reads 0-3.3V (after voltage divider with 1.65V offset)
 * - Actual back-EMF = 2 × (V_adc - 1.65V)
 * - Example: 1.65V ADC = 0mV back-EMF (motor at rest)
 * - Example: 3.3V ADC = +3.3V back-EMF (maximum forward)
 * - Example: 0V ADC = -3.3V back-EMF (maximum reverse)
 *
 * Used for motor research during first 10 seconds after mode change
 */
esp_err_t battery_read_backemf(int *raw_mv, int16_t *actual_backemf_mv);

/**
 * @brief Deinitialize battery monitoring (cleanup)
 * @return ESP_OK on success, error code on failure
 *
 * Frees ADC calibration resources and deletes ADC unit handle
 * Called during shutdown or if initialization needs to be retried
 */
esp_err_t battery_monitor_deinit(void);

#ifdef __cplusplus
}
#endif

#endif // BATTERY_MONITOR_H
