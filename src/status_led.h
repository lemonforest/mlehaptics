/**
 * @file status_led.h
 * @brief Status LED Control Module - GPIO15 blink patterns for system feedback
 *
 * Provides consistent status indication through GPIO15 LED blink patterns.
 * Extracted from single_device_ble_gatt_test.c reference implementation.
 *
 * @date November 11, 2025
 * @author Claude Code (Anthropic)
 */

#ifndef STATUS_LED_H
#define STATUS_LED_H

#include <stdint.h>
#include <stdbool.h>
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================================
// CONSTANTS AND CONFIGURATION
// ============================================================================

#define GPIO_STATUS_LED         15      /**< Status LED GPIO (ACTIVE LOW) */
#define LED_ON                  0       /**< Active LOW - LED turns on */
#define LED_OFF                 1       /**< Active LOW - LED turns off */

// ============================================================================
// PREDEFINED BLINK PATTERNS
// ============================================================================

/**
 * @brief Status LED patterns for different system events
 */
typedef enum {
    STATUS_PATTERN_BLE_CONNECTED,      /**< GPIO15 5× blink (100ms ON, 100ms OFF) - BLE client connected */
    STATUS_PATTERN_BLE_REENABLE,       /**< GPIO15 3× blink (100ms ON, 100ms OFF) - BLE advertising restarted */
    STATUS_PATTERN_LOW_BATTERY,        /**< GPIO15 3× blink (200ms ON, 200ms OFF) - Low battery warning */
    STATUS_PATTERN_NVS_RESET,          /**< GPIO15 3× blink (100ms ON, 100ms OFF) - NVS factory reset successful */
    STATUS_PATTERN_MODE_CHANGE,        /**< GPIO15 1× quick blink (50ms ON) - Mode changed */
    STATUS_PATTERN_BUTTON_HOLD,        /**< GPIO15 continuous ON - Button hold detected (1s+) */
    STATUS_PATTERN_COUNTDOWN,          /**< GPIO15 continuous ON - Shutdown countdown in progress */
    STATUS_PATTERN_PAIRING_WAIT,       /**< GPIO15 solid ON + WS2812B purple solid - Waiting for peer discovery (Phase 1b.3) */
    STATUS_PATTERN_PAIRING_PROGRESS,   /**< GPIO15 pulsing 1Hz + WS2812B purple pulsing - Pairing in progress (Phase 1b.3) */
    STATUS_PATTERN_PAIRING_SUCCESS,    /**< GPIO15 + WS2812B green 3× synchronized blink - Pairing success (Phase 1b.3) */
    STATUS_PATTERN_PAIRING_FAILED,     /**< GPIO15 + WS2812B red 3× synchronized blink - Pairing failed (Phase 1b.3) */
    STATUS_PATTERN_VERSION_MISMATCH    /**< GPIO15 + WS2812B yellow/amber 3× blink - Firmware version mismatch warning (AD040) */
} status_pattern_t;

// ============================================================================
// PUBLIC FUNCTION DECLARATIONS
// ============================================================================

/**
 * @brief Initialize the status LED GPIO
 * @return ESP_OK on success, error code on failure
 *
 * Configures GPIO15 as output with no pull resistors.
 * LED starts in OFF state (HIGH level due to active-low).
 */
esp_err_t status_led_init(void);

/**
 * @brief Turn status LED on
 *
 * Sets GPIO15 to LOW (active-low LED).
 */
void status_led_on(void);

/**
 * @brief Turn status LED off
 *
 * Sets GPIO15 to HIGH (active-low LED).
 */
void status_led_off(void);

/**
 * @brief Blink status LED with custom pattern
 * @param count Number of blinks
 * @param on_ms Duration of ON state in milliseconds
 * @param off_ms Duration of OFF state in milliseconds
 *
 * Blocking function that uses vTaskDelay for timing.
 * Example: status_led_blink(3, 100, 100) = 3 blinks, 100ms each
 */
void status_led_blink(uint8_t count, uint32_t on_ms, uint32_t off_ms);

/**
 * @brief Execute predefined blink pattern
 * @param pattern Pattern to execute from status_pattern_t enum
 *
 * Convenience function for common status indications.
 * Calls status_led_blink() with appropriate parameters.
 */
void status_led_pattern(status_pattern_t pattern);

/**
 * @brief Toggle status LED state
 *
 * If LED is ON, turns it OFF. If LED is OFF, turns it ON.
 * Useful for heartbeat or activity indication.
 */
void status_led_toggle(void);

/**
 * @brief Get current status LED state
 * @return true if LED is ON (GPIO LOW), false if LED is OFF (GPIO HIGH)
 */
bool status_led_is_on(void);

/**
 * @brief Deinitialize status LED
 * @return ESP_OK on success
 *
 * Turns LED off and resets GPIO to default state.
 * Called during system shutdown.
 */
esp_err_t status_led_deinit(void);

#ifdef __cplusplus
}
#endif

#endif // STATUS_LED_H