/**
 * @file motor_control.h
 * @brief Motor Control Module - H-bridge PWM control via LEDC
 *
 * This module provides low-level motor control for ERM vibration motors:
 * - LEDC PWM initialization (25kHz, 10-bit resolution)
 * - Forward and reverse motor control
 * - Motor coast (both directions off)
 * - PWM intensity adjustment (30-80% safety limits)
 *
 * Hardware Configuration:
 * - TB6612FNG H-bridge driver
 * - GPIO19: IN2 (reverse/backward) - LEDC Channel 0
 * - GPIO20: IN1 (forward) - LEDC Channel 1
 * - Motor operates in "slow decay" mode (one side PWM, other side LOW)
 *
 * PWM Configuration:
 * - Frequency: 25kHz (ultrasonic, prevents audible motor noise)
 * - Resolution: 10-bit (1024 levels, 0-1023)
 * - Timer: LEDC Timer 0
 * - Mode: High-speed mode
 *
 * Safety Limits (per AD031):
 * - Minimum PWM: 30% (prevents motor damage from undervoltage)
 * - Maximum PWM: 80% (prevents excessive stimulation and overheating)
 *
 * @date November 11, 2025
 * @author Claude Code (Anthropic)
 */

#ifndef MOTOR_CONTROL_H
#define MOTOR_CONTROL_H

#include <stdint.h>
#include <stdbool.h>
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================================
// MOTOR HARDWARE CONFIGURATION
// ============================================================================

/**
 * @brief Motor GPIO pins (H-bridge control)
 */
#define GPIO_HBRIDGE_IN2        19      /**< H-bridge reverse control (LEDC PWM) */
#define GPIO_HBRIDGE_IN1        20      /**< H-bridge forward control (LEDC PWM) */

/**
 * @brief LEDC PWM configuration
 */
#define MOTOR_PWM_FREQUENCY     25000   /**< PWM frequency in Hz (25kHz ultrasonic) */
#define MOTOR_PWM_RESOLUTION    LEDC_TIMER_10_BIT  /**< 10-bit resolution (1024 levels) */
#define MOTOR_PWM_TIMER         LEDC_TIMER_0       /**< LEDC timer number */
#define MOTOR_PWM_MODE          LEDC_LOW_SPEED_MODE /**< LEDC speed mode (ESP32-C6 only supports LOW_SPEED) */

/**
 * @brief LEDC channel assignments
 */
#define MOTOR_LEDC_CHANNEL_IN2  LEDC_CHANNEL_0  /**< IN2 (reverse) channel */
#define MOTOR_LEDC_CHANNEL_IN1  LEDC_CHANNEL_1  /**< IN1 (forward) channel */

/**
 * @brief PWM intensity limits (percentage)
 */
#define MOTOR_PWM_MIN           0       /**< Minimum PWM % (0% = LED-only mode, no motor) */
#define MOTOR_PWM_MAX           80      /**< Maximum PWM % (safety limit per AD031) */
#define MOTOR_PWM_DEFAULT       60      /**< Default PWM % (comfortable intensity) */

// ============================================================================
// PUBLIC API
// ============================================================================

/**
 * @brief Initialize motor control subsystem
 * @return ESP_OK on success, error code on failure
 *
 * Configures:
 * - LEDC Timer 0 (25kHz, 10-bit resolution)
 * - LEDC Channel 0 (GPIO19/IN2 for reverse)
 * - LEDC Channel 1 (GPIO20/IN1 for forward)
 *
 * Motor starts in coast state (both channels at 0% duty)
 *
 * Must be called once at boot before any motor operations
 */
esp_err_t motor_init(void);

/**
 * @brief Set motor forward PWM
 * @param intensity_percent PWM intensity percentage (30-80%)
 * @param verbose_logging If true, log the operation (gated with BEMF sampling)
 * @return ESP_OK on success, error code on failure
 *
 * Drives motor in forward direction:
 * - IN1 (GPIO20) = PWM at specified intensity
 * - IN2 (GPIO19) = LOW (0%)
 *
 * Intensity is clamped to safety limits (30-80%)
 * Values outside range are automatically adjusted
 *
 * Thread-safe: Can be called from any task
 */
esp_err_t motor_set_forward(uint8_t intensity_percent, bool verbose_logging);

/**
 * @brief Set motor reverse PWM
 * @param intensity_percent PWM intensity percentage (30-80%)
 * @param verbose_logging If true, log the operation (gated with BEMF sampling)
 * @return ESP_OK on success, error code on failure
 *
 * Drives motor in reverse direction:
 * - IN2 (GPIO19) = PWM at specified intensity
 * - IN1 (GPIO20) = LOW (0%)
 *
 * Intensity is clamped to safety limits (30-80%)
 * Values outside range are automatically adjusted
 *
 * Thread-safe: Can be called from any task
 */
esp_err_t motor_set_reverse(uint8_t intensity_percent, bool verbose_logging);

/**
 * @brief Coast motor (both directions off)
 * @param verbose_logging If true, log the operation (gated with BEMF sampling)
 *
 * Sets both IN1 and IN2 to LOW (0% duty):
 * - IN1 (GPIO20) = LOW
 * - IN2 (GPIO19) = LOW
 *
 * Motor enters "coast" state (high impedance, free spin)
 * This is the safest state for shutdown and idle periods
 *
 * Thread-safe: Can be called from any task
 */
void motor_coast(bool verbose_logging);

/**
 * @brief Get current PWM intensity setting
 * @return Current intensity percentage (30-80%)
 *
 * Returns the last configured PWM intensity
 * Does not indicate which direction is active
 *
 * Thread-safe: Can be called from any task
 */
uint8_t motor_get_intensity(void);

/**
 * @brief Check if motor is in coast state
 * @return true if coasting (both channels 0%), false if active
 *
 * Thread-safe: Can be called from any task
 */
bool motor_is_coasting(void);

/**
 * @brief Deinitialize motor control subsystem
 * @return ESP_OK on success, error code on failure
 *
 * Cleanup sequence:
 * 1. Coast motor (both channels to 0%)
 * 2. Stop LEDC channels
 * 3. Deinitialize LEDC timer
 *
 * Called during shutdown sequence before deep sleep
 */
esp_err_t motor_deinit(void);

#ifdef __cplusplus
}
#endif

#endif // MOTOR_CONTROL_H
