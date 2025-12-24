/**
 * @file led_control.h
 * @brief LED Control Module - WS2812B RGB LED control via RMT
 *
 * This module provides WS2812B RGB LED control using ESP32-C6 RMT peripheral:
 * - LED initialization (RMT driver configuration)
 * - RGB color setting with brightness control
 * - Palette mode (16 preset colors) and custom RGB mode
 * - Power management (enable/disable)
 * - Integration with BLE configuration service
 *
 * Hardware Configuration:
 * - 1× WS2812B RGB LED
 * - GPIO16: WS2812B power enable (P-MOSFET, LOW=enabled)
 * - GPIO17: WS2812B data input (RMT TX)
 *
 * Color Modes:
 * - Palette Mode (0): Select from 16 preset colors via index
 * - Custom RGB Mode (1): Full-spectrum color from color wheel
 *
 * @date November 11, 2025
 * @author Claude Code (Anthropic)
 */

#ifndef LED_CONTROL_H
#define LED_CONTROL_H

#include <stdint.h>
#include <stdbool.h>
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================================
// LED HARDWARE CONFIGURATION
// ============================================================================

/**
 * @brief LED GPIO pins
 */
#define GPIO_WS2812B_ENABLE     16      /**< WS2812B power enable (P-MOSFET, LOW=enabled) */
#define GPIO_WS2812B_DIN        17      /**< WS2812B data input (RMT TX) */

/**
 * @brief LED count
 */
#define LED_COUNT               1       /**< Number of WS2812B LEDs */

/**
 * @brief Brightness limits (percentage)
 */
#define LED_BRIGHTNESS_MIN      10      /**< Minimum brightness % */
#define LED_BRIGHTNESS_MAX      30      /**< Maximum brightness % (eye strain prevention) */
#define LED_BRIGHTNESS_DEFAULT  20      /**< Default brightness % */

// ============================================================================
// COLOR DEFINITIONS
// ============================================================================

/**
 * @brief RGB color structure
 */
typedef struct {
    uint8_t r;      /**< Red component 0-255 */
    uint8_t g;      /**< Green component 0-255 */
    uint8_t b;      /**< Blue component 0-255 */
} led_rgb_t;

/**
 * @brief 16-color palette for mode 0 (palette mode)
 *
 * Index 0-15 maps to preset colors for easy mobile app selection
 */
extern const led_rgb_t led_color_palette[16];

// ============================================================================
// PUBLIC API
// ============================================================================

/**
 * @brief Initialize LED subsystem
 * @return ESP_OK on success, error code on failure
 *
 * Configures:
 * - GPIO16 for WS2812B power enable (output, start disabled)
 * - GPIO17 for RMT TX (WS2812B data)
 * - RMT peripheral for WS2812B timing (800kHz)
 *
 * LEDs start in disabled state (off)
 * Call led_enable() to turn on power and update colors
 *
 * Must be called once at boot before any LED operations
 */
esp_err_t led_init(void);

/**
 * @brief Enable LED power
 *
 * Turns on WS2812B power via P-MOSFET (GPIO16 low)
 * LEDs will show last configured color/brightness
 *
 * Thread-safe: Can be called from any task
 */
void led_enable(void);

/**
 * @brief Disable LED power
 *
 * Turns off WS2812B power via P-MOSFET (GPIO16 high)
 * Reduces idle power consumption
 *
 * Thread-safe: Can be called from any task
 */
void led_disable(void);

/**
 * @brief Check if LEDs are enabled
 * @return true if enabled, false if disabled
 *
 * Thread-safe: Can be called from any task
 */
bool led_is_enabled(void);

/**
 * @brief Set LED color from palette index
 * @param index Palette index 0-15
 * @param brightness Brightness percentage 10-30%
 * @return ESP_OK on success, error code on failure
 *
 * Sets both LEDs to the same color from 16-color palette
 * Brightness is applied as scaling factor (0-255 → 0-brightness%)
 *
 * LEDs must be enabled via led_enable() to be visible
 *
 * Thread-safe: Can be called from any task
 */
esp_err_t led_set_palette(uint8_t index, uint8_t brightness);

/**
 * @brief Set LED color from custom RGB values
 * @param r Red component 0-255
 * @param g Green component 0-255
 * @param b Blue component 0-255
 * @param brightness Brightness percentage 10-30%
 * @return ESP_OK on success, error code on failure
 *
 * Sets both LEDs to the same custom RGB color
 * Brightness is applied as scaling factor (0-255 → 0-brightness%)
 *
 * LEDs must be enabled via led_enable() to be visible
 *
 * Thread-safe: Can be called from any task
 */
esp_err_t led_set_rgb(uint8_t r, uint8_t g, uint8_t b, uint8_t brightness);

/**
 * @brief Set individual LED color (for back-EMF visualization)
 * @param led_index LED index 0-1 (0=left/forward, 1=right/reverse)
 * @param r Red component 0-255
 * @param g Green component 0-255
 * @param b Blue component 0-255
 * @param brightness Brightness percentage 10-30%
 * @return ESP_OK on success, error code on failure
 *
 * Sets one LED to a specific color, useful for:
 * - Back-EMF polarity visualization (red=forward, blue=reverse)
 * - Direction indication (left/right for bilateral stimulation)
 *
 * LEDs must be enabled via led_enable() to be visible
 *
 * Thread-safe: Can be called from any task
 */
esp_err_t led_set_single(uint8_t led_index, uint8_t r, uint8_t g, uint8_t b, uint8_t brightness);

/**
 * @brief Clear all LEDs (turn off)
 *
 * Sets both LEDs to black (0, 0, 0) but keeps power enabled
 * Use led_disable() to also cut power
 *
 * Thread-safe: Can be called from any task
 */
void led_clear(void);

/**
 * @brief Update LED state from BLE configuration
 *
 * Reads current BLE settings and updates LEDs accordingly:
 * - If LED disabled: Clear LEDs and disable power
 * - If LED enabled:
 *   - Color Mode 0 (palette): Use palette index
 *   - Color Mode 1 (custom RGB): Use custom RGB values
 *   - Apply brightness setting
 *
 * Called by motor_task when mode changes or BLE parameters updated
 *
 * Thread-safe: Can be called from any task
 */
void led_update_from_ble(void);

/**
 * @brief Set LED color with perceptual (CIE 1931) brightness
 * @param r Red component 0-255
 * @param g Green component 0-255
 * @param b Blue component 0-255
 * @param brightness Perceived brightness percentage 0-100%
 * @return ESP_OK on success, error code on failure
 *
 * Uses CIE 1931 lightness function for smooth, "organic" fades:
 * - 50% perceived brightness = 18.4% actual PWM
 * - Human eye sees uniform brightness steps
 *
 * Recommended for pattern playback transitions.
 *
 * Thread-safe: Can be called from any task
 */
esp_err_t led_set_rgb_perceptual(uint8_t r, uint8_t g, uint8_t b, uint8_t brightness);

/**
 * @brief Set LED from palette with perceptual brightness
 * @param index Palette index 0-15
 * @param brightness Perceived brightness percentage 0-100%
 * @return ESP_OK on success, error code on failure
 *
 * Same as led_set_palette but uses CIE 1931 perceptual dimming.
 */
esp_err_t led_set_palette_perceptual(uint8_t index, uint8_t brightness);

/**
 * @brief Deinitialize LED subsystem
 * @return ESP_OK on success, error code on failure
 *
 * Cleanup sequence:
 * 1. Clear all LEDs (turn off)
 * 2. Disable LED power
 * 3. Deinitialize RMT driver
 *
 * Called during shutdown sequence before deep sleep
 */
esp_err_t led_deinit(void);

// ============================================================================
// LED OWNERSHIP MANAGEMENT (Phase 1b.3)
// ============================================================================

/**
 * @brief Set motor task ownership of WS2812B
 * @param motor_owns true if motor task owns WS2812B, false otherwise
 *
 * When motor_owns=true, status_led patterns will skip WS2812B control
 * to prevent interrupting motor task's 10-second LED indication.
 *
 * Motor task should call this:
 * - Set true when entering operational state (CHECK_MESSAGES)
 * - Set false when entering shutdown state
 *
 * Thread-safe: Can be called from any task
 */
void led_set_motor_ownership(bool motor_owns);

/**
 * @brief Check if motor task owns WS2812B
 * @return true if motor task owns WS2812B, false if status_led can use it
 *
 * Status LED patterns should check this before controlling WS2812B
 * to avoid interrupting motor task's LED indication.
 *
 * Thread-safe: Can be called from any task
 */
bool led_get_motor_ownership(void);

#ifdef __cplusplus
}
#endif

#endif // LED_CONTROL_H
