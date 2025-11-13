/**
 * @file ble_manager.h
 * @brief BLE Manager Module - NimBLE GATT Configuration Service per AD032
 *
 * This module implements a complete BLE GATT Configuration Service for EMDR
 * device configuration via mobile applications. It provides:
 * - Configuration Service (UUID: 6E400002-B5A3-F393-E0A9-E50E24DCCA9E)
 * - 12 GATT characteristics for motor control, LED control, and status monitoring
 * - Battery level and session time notifications
 * - NVS persistence for user preferences
 * - Advertising lifecycle management
 *
 * BLE Service Architecture (per AD032):
 * - **Configuration Service** (13th byte = 02)
 *   - Motor Control: Mode, Frequency, Duty, PWM (4 characteristics)
 *   - LED Control: Enable, Color Mode, Palette, RGB, Brightness (5 characteristics)
 *   - Status: Session Duration, Session Time, Battery (3 characteristics)
 *
 * @date November 11, 2025
 * @author Claude Code (Anthropic)
 */

#ifndef BLE_MANAGER_H
#define BLE_MANAGER_H

#include <stdint.h>
#include <stdbool.h>
#include "esp_err.h"
#include "motor_task.h"  // For mode_t enum

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================================
// BLE CONFIGURATION
// ============================================================================

#define BLE_DEVICE_NAME         "EMDR_Pulser"   /**< Base device name */
#define BLE_ADV_TIMEOUT_MS      300000          /**< 5-minute advertising timeout */

/**
 * @brief BLE advertising parameters
 *
 * Configured for balance between connection speed and power consumption:
 * - Interval: 20-40ms (fast connection)
 * - Undirected connectable mode
 * - General discoverable mode
 */

// ============================================================================
// GATT CHARACTERISTICS (Configuration Service - AD032)
// ============================================================================

/**
 * @brief Mode 5 LED color palette entry
 *
 * 16-color palette for WS2812B LED control
 * Each color defined as RGB 0-255
 */
typedef struct {
    uint8_t r;      /**< Red component 0-255 */
    uint8_t g;      /**< Green component 0-255 */
    uint8_t b;      /**< Blue component 0-255 */
    const char *name; /**< Color name for debugging */
} rgb_color_t;

/**
 * @brief Mode 5 (custom) LED color palette
 *
 * 16 colors for user selection via BLE
 * Index 0-15 maps to color palette
 */
extern const rgb_color_t color_palette[16];

/**
 * @brief LED color mode enumeration
 */
typedef enum {
    LED_COLOR_MODE_PALETTE = 0,  /**< Use palette index (0-15) */
    LED_COLOR_MODE_CUSTOM_RGB = 1 /**< Use custom RGB values */
} led_color_mode_t;

/**
 * @brief BLE characteristic data structure (AD032)
 *
 * Holds current values for all 12 GATT characteristics
 * Updated by write callbacks, read by read callbacks
 */
typedef struct {
    // Motor Control Group (4 characteristics)
    mode_t current_mode;              /**< Current mode 0-4 (read/write) */
    uint16_t custom_frequency_hz;     /**< Hz × 100 (25-200 = 0.25-2.0 Hz) (read/write) */
    uint8_t custom_duty_percent;      /**< Duty cycle 0-50% (0% = LED-only, 50% max prevents motor overlap) (read/write) */
    uint8_t pwm_intensity;            /**< Motor PWM 30-80% (read/write) */

    // LED Control Group (5 characteristics)
    bool led_enable;                  /**< LED enable (read/write) */
    uint8_t led_color_mode;           /**< 0=palette, 1=custom RGB (read/write) */
    uint8_t led_palette_index;        /**< Palette index 0-15 (read/write) */
    uint8_t led_custom_r;             /**< Custom RGB red 0-255 (read/write) */
    uint8_t led_custom_g;             /**< Custom RGB green 0-255 (read/write) */
    uint8_t led_custom_b;             /**< Custom RGB blue 0-255 (read/write) */
    uint8_t led_brightness;           /**< LED brightness 10-30% (read/write) */

    // Status/Monitoring Group (3 characteristics)
    uint32_t session_duration_sec;    /**< Target session length 1200-5400 sec (read/write) */
    uint32_t session_time_sec;        /**< Elapsed seconds 0-5400 (read/notify) */
    uint8_t battery_level;            /**< Battery % 0-100 (read/notify) */
} ble_char_data_t;

// ============================================================================
// PUBLIC API
// ============================================================================

/**
 * @brief Initialize BLE subsystem and GATT server
 * @return ESP_OK on success, error code on failure
 *
 * Configures:
 * - NVS flash (required for BLE)
 * - NimBLE host and stack
 * - GATT Configuration Service (AD032) with 12 characteristics
 * - Advertising parameters
 * - Callbacks for GAP events and GATT access
 *
 * Starts NimBLE host task and begins advertising
 * Device name format: "EMDR_Pulser_XXXXXX" (last 3 MAC bytes)
 *
 * Must be called after motor_init() and battery_monitor_init()
 */
esp_err_t ble_manager_init(void);

/**
 * @brief Start BLE advertising
 *
 * Begins advertising if not already active
 * Called automatically after init and after disconnect
 * Can be manually triggered via button hold (1-2s)
 */
void ble_start_advertising(void);

/**
 * @brief Stop BLE advertising
 *
 * Stops advertising if active
 * Used to save power after connection established
 */
void ble_stop_advertising(void);

/**
 * @brief Check if BLE client is connected
 * @return true if client connected, false otherwise
 *
 * Used by motor_task and button_task to determine if BLE control is active
 */
bool ble_is_connected(void);

/**
 * @brief Check if BLE is currently advertising
 * @return true if advertising active, false otherwise
 *
 * Used by BLE task for timeout management
 */
bool ble_is_advertising(void);

/**
 * @brief Get advertising elapsed time
 * @return Milliseconds since advertising started (0 if not advertising)
 *
 * Used by BLE task to enforce 5-minute advertising timeout
 */
uint32_t ble_get_advertising_elapsed_ms(void);

/**
 * @brief Update battery level for BLE notifications
 * @param percentage Battery percentage 0-100
 *
 * Thread-safe update of battery characteristic
 * Triggers BLE notification if client subscribed
 * Called by motor_task every 10 seconds
 */
void ble_update_battery_level(uint8_t percentage);

/**
 * @brief Update session time for BLE notifications
 * @param seconds Elapsed session time in seconds
 *
 * Thread-safe update of session time characteristic
 * Triggers BLE notification if client subscribed
 * Called by motor_task every second
 */
void ble_update_session_time(uint32_t seconds);

/**
 * @brief Get current BLE-configured mode
 * @return Current mode_t value (0-4)
 *
 * Thread-safe read of mode characteristic
 * Used by motor_task to determine active mode
 */
mode_t ble_get_current_mode(void);

/**
 * @brief Get Mode 5 custom frequency
 * @return Frequency in Hz × 100 (e.g., 100 = 1.00 Hz)
 *
 * Thread-safe read of custom frequency characteristic
 * Valid range: 25-200 (0.25-2.0 Hz research platform)
 */
uint16_t ble_get_custom_frequency_hz(void);

/**
 * @brief Get Mode 5 custom duty cycle
 * @return Duty cycle percentage 0-50%
 *
 * Thread-safe read of custom duty cycle characteristic
 * Percentage of half-cycle that motor is active
 * 0% enables LED-only mode (visual therapy without motor)
 * 50% maximum prevents motor overlap in bilateral alternation
 */
uint8_t ble_get_custom_duty_percent(void);

/**
 * @brief Get Mode 5 PWM intensity
 * @return PWM intensity percentage 30-80%
 *
 * Thread-safe read of PWM intensity characteristic
 * Safety-limited range per AD031
 */
uint8_t ble_get_pwm_intensity(void);

/**
 * @brief Get LED enable state
 * @return true if LED enabled, false otherwise
 *
 * Thread-safe read of LED enable characteristic
 */
bool ble_get_led_enable(void);

/**
 * @brief Get LED color mode
 * @return 0=palette mode, 1=custom RGB mode
 *
 * Thread-safe read of LED color mode characteristic
 * Determines which color source to use (palette index or custom RGB)
 */
uint8_t ble_get_led_color_mode(void);

/**
 * @brief Get LED palette index
 * @return Color index 0-15
 *
 * Thread-safe read of LED palette index characteristic
 * Index into color_palette array (used when color mode = 0)
 */
uint8_t ble_get_led_palette_index(void);

/**
 * @brief Get LED custom RGB values
 * @param r Output: Red component 0-255
 * @param g Output: Green component 0-255
 * @param b Output: Blue component 0-255
 *
 * Thread-safe read of LED custom RGB characteristic
 * Used when color mode = 1 (custom RGB)
 */
void ble_get_led_custom_rgb(uint8_t *r, uint8_t *g, uint8_t *b);

/**
 * @brief Get LED brightness
 * @return Brightness percentage 10-30%
 *
 * Thread-safe read of LED brightness characteristic
 * Limited to 30% max to prevent eye strain
 */
uint8_t ble_get_led_brightness(void);

/**
 * @brief Get target session duration
 * @return Session duration in seconds (1200-5400)
 *
 * Thread-safe read of session duration characteristic
 * Range: 20-90 minutes configurable via mobile app
 */
uint32_t ble_get_session_duration_sec(void);

/**
 * @brief Check if settings need NVS save
 * @return true if any parameter changed since last save
 *
 * Monitors dirty flag for deferred NVS writes
 * Used to reduce flash wear (save only on shutdown)
 */
bool ble_settings_dirty(void);

/**
 * @brief Mark settings as saved to NVS
 *
 * Clears dirty flag after successful NVS write
 * Called by power_manager after save_settings_to_nvs()
 */
void ble_settings_mark_clean(void);

/**
 * @brief Save user preferences to NVS
 * @return ESP_OK on success, error code on failure
 *
 * Saves all user-configurable parameters to NVS with signature validation:
 * - Mode (last used)
 * - Custom Frequency
 * - Custom Duty Cycle
 * - LED Enable
 * - LED Color Mode
 * - LED Palette Index
 * - LED Custom RGB
 * - LED Brightness
 * - PWM Intensity
 * - Session Duration
 *
 * Called before deep sleep to persist user settings
 * Only writes if dirty flag set (reduces flash wear)
 */
esp_err_t ble_save_settings_to_nvs(void);

/**
 * @brief Load user preferences from NVS
 * @return ESP_OK on success, error code on failure
 *
 * Loads all user-configurable parameters from NVS with signature verification
 * Called once at boot to restore previous configuration
 * Falls back to defaults if signature invalid or NVS empty
 */
esp_err_t ble_load_settings_from_nvs(void);

/**
 * @brief Deinitialize BLE subsystem
 * @return ESP_OK on success, error code on failure
 *
 * Stops advertising, disconnects client, and shuts down NimBLE host
 * Called during shutdown sequence before deep sleep
 */
esp_err_t ble_manager_deinit(void);

// ============================================================================
// EXTERNAL CALLBACKS (implemented by motor_task)
// ============================================================================

/**
 * @brief Callback for BLE mode change
 * @param new_mode New mode value 0-4
 *
 * Called by BLE manager when mode characteristic is written
 * Motor task should update current mode and reconfigure timings
 *
 * NOTE: Implemented in motor_task.c, declared extern here
 */
extern void ble_callback_mode_changed(mode_t new_mode);

/**
 * @brief Callback for BLE parameter update
 *
 * Called by BLE manager when any Mode 5 parameter is written
 * Motor task should reload parameters via ble_get_* functions
 *
 * NOTE: Implemented in motor_task.c, declared extern here
 */
extern void ble_callback_params_updated(void);

#ifdef __cplusplus
}
#endif

#endif // BLE_MANAGER_H
