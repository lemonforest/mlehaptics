/**
 * @file led_control.c
 * @brief LED Control Implementation - WS2812B RGB LED control via RMT
 *
 * Implements WS2812B RGB LED control using ESP32-C6 RMT peripheral.
 * Uses ESP-IDF led_strip component for timing and encoding.
 * Extracted from single_device_ble_gatt_test.c reference implementation.
 *
 * @date November 11, 2025
 * @author Claude Code (Anthropic)
 */

#include "led_control.h"
#include "cie_lut.h"
#include "ble_manager.h"
#include "esp_log.h"
#include "driver/gpio.h"
#include "led_strip.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"

static const char *TAG = "LED_CTRL";

// ============================================================================
// 16-COLOR PALETTE
// ============================================================================

const led_rgb_t led_color_palette[16] = {
    {255,   0,   0},  // 0: Red
    {0,   255,   0},  // 1: Green
    {0,     0, 255},  // 2: Blue
    {255, 255,   0},  // 3: Yellow
    {0,   255, 255},  // 4: Cyan
    {255,   0, 255},  // 5: Magenta
    {255, 128,   0},  // 6: Orange
    {128,   0, 255},  // 7: Purple
    {0,   255, 128},  // 8: Spring Green
    {255, 192, 203},  // 9: Pink
    {255, 255, 255},  // 10: White
    {128, 128,   0},  // 11: Olive
    {0,   128, 128},  // 12: Teal
    {128,   0, 128},  // 13: Violet
    {64,  224, 208},  // 14: Turquoise
    {255, 140,   0}   // 15: Dark Orange
};

// ============================================================================
// HARDWARE STATE
// ============================================================================

static led_strip_handle_t led_strip = NULL;

// LED state
static bool led_power_enabled = false;
static SemaphoreHandle_t led_mutex = NULL;

// LED ownership flag (Phase 1b.3: Prevents status_led from interrupting motor_task)
static bool motor_owns_ws2812b = false;

// ============================================================================
// INTERNAL HELPERS
// ============================================================================

/**
 * @brief Apply brightness scaling to RGB color
 * @param r Red component 0-255 (input)
 * @param g Green component 0-255 (input)
 * @param b Blue component 0-255 (input)
 * @param brightness Brightness percentage 10-30%
 * @param out_r Output: Scaled red component
 * @param out_g Output: Scaled green component
 * @param out_b Output: Scaled blue component
 */
static void apply_brightness(uint8_t r, uint8_t g, uint8_t b, uint8_t brightness,
                              uint8_t *out_r, uint8_t *out_g, uint8_t *out_b) {
    // Clamp brightness to valid range
    if (brightness < LED_BRIGHTNESS_MIN) brightness = LED_BRIGHTNESS_MIN;
    if (brightness > LED_BRIGHTNESS_MAX) brightness = LED_BRIGHTNESS_MAX;

    // Scale RGB by brightness percentage
    *out_r = (r * brightness) / 100;
    *out_g = (g * brightness) / 100;
    *out_b = (b * brightness) / 100;
}

// ============================================================================
// PUBLIC API IMPLEMENTATION
// ============================================================================

esp_err_t led_init(void) {
    ESP_LOGI(TAG, "Initializing LED control");

    // Create mutex for thread-safe LED operations
    led_mutex = xSemaphoreCreateMutex();
    if (led_mutex == NULL) {
        ESP_LOGE(TAG, "Failed to create LED mutex");
        return ESP_ERR_NO_MEM;
    }

    // Configure GPIO16 for WS2812B power enable (output, start disabled)
    gpio_config_t power_cfg = {
        .pin_bit_mask = (1ULL << GPIO_WS2812B_ENABLE),
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE
    };
    esp_err_t ret = gpio_config(&power_cfg);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to configure WS2812B power GPIO: %s", esp_err_to_name(ret));
        return ret;
    }
    gpio_set_level(GPIO_WS2812B_ENABLE, 1);  // P-MOSFET: HIGH = disabled
    led_power_enabled = false;

    // Configure led_strip for WS2812B (1 LED)
    led_strip_config_t strip_config = {
        .strip_gpio_num = GPIO_WS2812B_DIN,
        .max_leds = LED_COUNT,  // 1 LED
        .led_pixel_format = LED_PIXEL_FORMAT_GRB,
        .led_model = LED_MODEL_WS2812,
        .flags.invert_out = false,
    };

    led_strip_rmt_config_t rmt_config = {
        .clk_src = RMT_CLK_SRC_DEFAULT,
        .resolution_hz = 10 * 1000 * 1000,  // 10MHz
        .flags.with_dma = false,
    };

    ret = led_strip_new_rmt_device(&strip_config, &rmt_config, &led_strip);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to create led_strip device: %s", esp_err_to_name(ret));
        return ret;
    }

    // Clear all LEDs (turn off)
    led_strip_clear(led_strip);

    ESP_LOGI(TAG, "LED control initialized (1 LED, GPIO%d power, GPIO%d data)",
             GPIO_WS2812B_ENABLE, GPIO_WS2812B_DIN);
    return ESP_OK;
}

void led_enable(void) {
    if (xSemaphoreTake(led_mutex, pdMS_TO_TICKS(100)) == pdTRUE) {
        if (!led_power_enabled) {
            gpio_set_level(GPIO_WS2812B_ENABLE, 0);  // P-MOSFET: LOW = enabled
            led_power_enabled = true;
            ESP_LOGI(TAG, "LED power enabled");
        }
        xSemaphoreGive(led_mutex);
    }
}

void led_disable(void) {
    if (xSemaphoreTake(led_mutex, pdMS_TO_TICKS(100)) == pdTRUE) {
        if (led_power_enabled) {
            led_strip_clear(led_strip);  // Turn off LEDs before disabling power
            gpio_set_level(GPIO_WS2812B_ENABLE, 1);  // P-MOSFET: HIGH = disabled
            led_power_enabled = false;
            ESP_LOGI(TAG, "LED power disabled");
        }
        xSemaphoreGive(led_mutex);
    }
}

bool led_is_enabled(void) {
    return led_power_enabled;
}

esp_err_t led_set_palette(uint8_t index, uint8_t brightness) {
    if (index >= 16) {
        ESP_LOGE(TAG, "Invalid palette index: %d (max 15)", index);
        return ESP_ERR_INVALID_ARG;
    }

    const led_rgb_t *color = &led_color_palette[index];
    return led_set_rgb(color->r, color->g, color->b, brightness);
}

esp_err_t led_set_rgb(uint8_t r, uint8_t g, uint8_t b, uint8_t brightness) {
    if (xSemaphoreTake(led_mutex, pdMS_TO_TICKS(100)) != pdTRUE) {
        ESP_LOGW(TAG, "Failed to take LED mutex");
        return ESP_ERR_TIMEOUT;
    }

    // Apply brightness scaling
    uint8_t r_scaled, g_scaled, b_scaled;
    apply_brightness(r, g, b, brightness, &r_scaled, &g_scaled, &b_scaled);

    // Set LED color
    esp_err_t ret = ESP_OK;
    for (int i = 0; i < LED_COUNT; i++) {
        esp_err_t result = led_strip_set_pixel(led_strip, i, r_scaled, g_scaled, b_scaled);
        if (result != ESP_OK) {
            ESP_LOGE(TAG, "Failed to set LED %d: %s", i, esp_err_to_name(result));
            ret = result;
        }
    }

    // Refresh to apply changes
    if (ret == ESP_OK) {
        ret = led_strip_refresh(led_strip);
        if (ret != ESP_OK) {
            ESP_LOGE(TAG, "Failed to refresh LED strip: %s", esp_err_to_name(ret));
        }
    }

    xSemaphoreGive(led_mutex);
    return ret;
}

esp_err_t led_set_individual(uint8_t led_index, uint8_t r, uint8_t g, uint8_t b, uint8_t brightness) {
    if (led_index >= LED_COUNT) {
        ESP_LOGE(TAG, "Invalid LED index: %d (max %d)", led_index, LED_COUNT - 1);
        return ESP_ERR_INVALID_ARG;
    }

    if (xSemaphoreTake(led_mutex, pdMS_TO_TICKS(100)) != pdTRUE) {
        ESP_LOGW(TAG, "Failed to take LED mutex");
        return ESP_ERR_TIMEOUT;
    }

    // Apply brightness scaling
    uint8_t r_scaled, g_scaled, b_scaled;
    apply_brightness(r, g, b, brightness, &r_scaled, &g_scaled, &b_scaled);

    // Set individual LED
    esp_err_t ret = led_strip_set_pixel(led_strip, led_index, r_scaled, g_scaled, b_scaled);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to set LED %d: %s", led_index, esp_err_to_name(ret));
        xSemaphoreGive(led_mutex);
        return ret;
    }

    // Refresh to apply changes
    ret = led_strip_refresh(led_strip);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to refresh LED strip: %s", esp_err_to_name(ret));
    }

    xSemaphoreGive(led_mutex);
    return ret;
}

void led_clear(void) {
    if (xSemaphoreTake(led_mutex, pdMS_TO_TICKS(100)) != pdTRUE) {
        ESP_LOGW(TAG, "Failed to take LED mutex");
        return;
    }

    esp_err_t ret = led_strip_clear(led_strip);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to clear LED strip: %s", esp_err_to_name(ret));
    }

    xSemaphoreGive(led_mutex);
}

// ============================================================================
// CIE 1931 PERCEPTUAL BRIGHTNESS FUNCTIONS
// ============================================================================

/**
 * @brief Apply CIE 1931 perceptual brightness scaling to RGB color
 * @param r Red component 0-255 (input)
 * @param g Green component 0-255 (input)
 * @param b Blue component 0-255 (input)
 * @param brightness Perceived brightness percentage 0-100%
 * @param out_r Output: Perceptually scaled red component
 * @param out_g Output: Perceptually scaled green component
 * @param out_b Output: Perceptually scaled blue component
 *
 * Uses CIE 1931 lightness function for smooth, "organic" fades.
 * 50% perceived brightness = 18.4% actual PWM.
 */
static void apply_brightness_perceptual(uint8_t r, uint8_t g, uint8_t b, uint8_t brightness,
                                         uint8_t *out_r, uint8_t *out_g, uint8_t *out_b) {
    // Clamp brightness to 0-100
    if (brightness > 100) brightness = 100;

    // Get CIE-corrected 8-bit value for brightness percentage
    uint8_t cie_scale = cie_get_pwm_8bit(brightness);

    // Scale RGB by CIE-corrected value (0-255)
    *out_r = (uint8_t)(((uint16_t)r * cie_scale) / 255);
    *out_g = (uint8_t)(((uint16_t)g * cie_scale) / 255);
    *out_b = (uint8_t)(((uint16_t)b * cie_scale) / 255);
}

esp_err_t led_set_rgb_perceptual(uint8_t r, uint8_t g, uint8_t b, uint8_t brightness) {
    if (xSemaphoreTake(led_mutex, pdMS_TO_TICKS(100)) != pdTRUE) {
        ESP_LOGW(TAG, "Failed to take LED mutex");
        return ESP_ERR_TIMEOUT;
    }

    // Apply CIE 1931 perceptual brightness scaling
    uint8_t r_scaled, g_scaled, b_scaled;
    apply_brightness_perceptual(r, g, b, brightness, &r_scaled, &g_scaled, &b_scaled);

    // Set LED color
    esp_err_t ret = ESP_OK;
    for (int i = 0; i < LED_COUNT; i++) {
        esp_err_t result = led_strip_set_pixel(led_strip, i, r_scaled, g_scaled, b_scaled);
        if (result != ESP_OK) {
            ESP_LOGE(TAG, "Failed to set LED %d: %s", i, esp_err_to_name(result));
            ret = result;
        }
    }

    // Refresh to apply changes
    if (ret == ESP_OK) {
        ret = led_strip_refresh(led_strip);
        if (ret != ESP_OK) {
            ESP_LOGE(TAG, "Failed to refresh LED strip: %s", esp_err_to_name(ret));
        }
    }

    xSemaphoreGive(led_mutex);
    return ret;
}

esp_err_t led_set_palette_perceptual(uint8_t index, uint8_t brightness) {
    if (index >= 16) {
        ESP_LOGE(TAG, "Invalid palette index: %d (max 15)", index);
        return ESP_ERR_INVALID_ARG;
    }

    const led_rgb_t *color = &led_color_palette[index];
    return led_set_rgb_perceptual(color->r, color->g, color->b, brightness);
}

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
 */
void led_set_motor_ownership(bool motor_owns) {
    motor_owns_ws2812b = motor_owns;
    ESP_LOGI(TAG, "WS2812B ownership: %s", motor_owns ? "MOTOR_TASK" : "STATUS_LED");
}

/**
 * @brief Check if motor task owns WS2812B
 * @return true if motor task owns WS2812B, false if status_led can use it
 *
 * Status LED patterns should check this before controlling WS2812B
 * to avoid interrupting motor task's LED indication.
 */
bool led_get_motor_ownership(void) {
    return motor_owns_ws2812b;
}

esp_err_t led_deinit(void) {
    ESP_LOGI(TAG, "Deinitializing LED control");

    if (xSemaphoreTake(led_mutex, pdMS_TO_TICKS(100)) == pdTRUE) {
        // Clear and disable LEDs
        led_strip_clear(led_strip);
        gpio_set_level(GPIO_WS2812B_ENABLE, 1);  // P-MOSFET: HIGH = disabled
        led_power_enabled = false;

        // Delete led_strip handle
        if (led_strip != NULL) {
            esp_err_t ret = led_strip_del(led_strip);
            if (ret != ESP_OK) {
                ESP_LOGE(TAG, "Failed to delete led_strip: %s", esp_err_to_name(ret));
            }
            led_strip = NULL;
        }

        xSemaphoreGive(led_mutex);
    }

    // Delete mutex
    if (led_mutex != NULL) {
        vSemaphoreDelete(led_mutex);
        led_mutex = NULL;
    }

    ESP_LOGI(TAG, "LED control deinitialized");
    return ESP_OK;
}

void led_update_from_ble(void) {
    // Check if LED is enabled via BLE
    if (!ble_get_led_enable()) {
        led_clear();  // Turn off LED if disabled
        return;
    }

    // Get BLE configuration
    uint8_t color_mode = ble_get_led_color_mode();
    uint8_t brightness = ble_get_led_brightness();

    // Determine color source
    uint8_t r, g, b;
    if (color_mode == LED_COLOR_MODE_PALETTE) {
        // Use palette color
        uint8_t palette_index = ble_get_led_palette_index();
        if (palette_index >= 16) {
            ESP_LOGW(TAG, "Invalid palette index %d, using 0", palette_index);
            palette_index = 0;
        }
        const led_rgb_t *color = &led_color_palette[palette_index];
        r = color->r;
        g = color->g;
        b = color->b;
    } else {
        // Use custom RGB
        ble_get_led_custom_rgb(&r, &g, &b);
    }

    // Apply color with BLE-configured brightness
    led_set_rgb(r, g, b, brightness);
}
