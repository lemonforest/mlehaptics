/**
 * @file power_manager.h
 * @brief Power Management Module - Deep sleep and shutdown control
 *
 * This module provides centralized power management functions:
 * - Deep sleep entry with wake source configuration
 * - Pre-sleep cleanup (NVS save, peripheral deinit)
 * - Low voltage protection checks
 * - Battery status monitoring
 *
 * Used by button_task for emergency shutdown sequence.
 *
 * @date November 11, 2025
 * @author Claude Code (Anthropic)
 */

#ifndef POWER_MANAGER_H
#define POWER_MANAGER_H

#include <stdint.h>
#include <stdbool.h>
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================================
// POWER MANAGEMENT CONFIGURATION
// ============================================================================

/**
 * @brief Wake source configuration
 */
#define POWER_WAKE_BUTTON_GPIO  1       /**< Button GPIO for wake from deep sleep */

// ============================================================================
// PUBLIC API
// ============================================================================

/**
 * @brief Save all user settings to NVS before shutdown
 * @return ESP_OK on success, error code on failure
 *
 * Saves BLE configuration settings if dirty:
 * - Mode (last used)
 * - Custom frequency, duty cycle, PWM intensity
 * - LED enable, color mode, palette index, custom RGB, brightness
 * - Session duration
 *
 * Called automatically by power_enter_deep_sleep()
 * Can also be called manually for periodic saves
 */
esp_err_t power_save_settings(void);

/**
 * @brief Deinitialize all peripherals before deep sleep
 * @return ESP_OK on success, error code on failure
 *
 * Cleanup sequence:
 * 1. Stop BLE advertising and disconnect clients
 * 2. Deinitialize BLE manager (NimBLE shutdown)
 * 3. Deinitialize battery monitor (ADC cleanup)
 * 4. Turn off LEDs
 * 5. Coast motors (both directions)
 *
 * Called automatically by power_enter_deep_sleep()
 * Can also be called manually for testing
 */
esp_err_t power_deinit_peripherals(void);

/**
 * @brief Enter deep sleep with button wake
 * @param save_settings If true, save user settings to NVS before sleep
 * @return Never returns (enters deep sleep)
 *
 * Complete shutdown sequence:
 * 1. Save settings to NVS (if requested and dirty)
 * 2. Deinitialize all peripherals (BLE, ADC, LEDs, motors)
 * 3. Configure EXT1 wake source (button GPIO low)
 * 4. Enter deep sleep (never returns)
 *
 * Wake conditions:
 * - Button press (GPIO1 low = pressed)
 *
 * This function never returns - device enters deep sleep and resets on wake
 *
 * @note Caller should unsubscribe from watchdog before calling this function
 */
void power_enter_deep_sleep(bool save_settings) __attribute__((noreturn));

/**
 * @brief Check battery level and display warning if low
 * @return true if battery OK or not present, false if critically low (never returns)
 *
 * Battery status:
 * - < 0.5V: No battery detected (skip LVO, allow operation)
 * - < 2.8V: Critical (enter deep sleep immediately, never returns)
 * - < 3.0V: Warning (flash LED, continue operation)
 * - ≥ 3.0V: OK (continue operation)
 *
 * If battery critically low (< 2.8V), this function enters deep sleep
 * and never returns. Otherwise, it returns true to allow operation.
 *
 * Called at boot by main.c and optionally during shutdown by button_task
 */
bool power_check_battery(void);

/**
 * @brief Check if device should enter deep sleep due to low battery
 * @return true if battery OK, false if should enter deep sleep
 *
 * This is the non-blocking version of power_check_battery()
 * Returns false if battery < 2.8V, but doesn't enter sleep automatically
 *
 * Use this when you need to check battery status without triggering
 * automatic sleep (e.g., during shutdown sequence)
 */
bool power_battery_ok(void);

#ifdef __cplusplus
}
#endif

#endif // POWER_MANAGER_H
