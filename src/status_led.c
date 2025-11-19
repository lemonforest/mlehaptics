/**
 * @file status_led.c
 * @brief Status LED Control Module Implementation
 *
 * Implements GPIO15 status LED control with predefined blink patterns
 * for system status indication, including WS2812B RGB integration for
 * pairing feedback (Phase 1b.3).
 *
 * @date November 11, 2025
 * @author Claude Code (Anthropic)
 */

#include "status_led.h"
#include "led_control.h"  // For WS2812B pairing patterns
#include "esp_log.h"
#include "driver/gpio.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "STATUS_LED";
static bool led_initialized = false;
static bool led_current_state = false;  // false = OFF, true = ON

// ============================================================================
// PUBLIC FUNCTION IMPLEMENTATIONS
// ============================================================================

esp_err_t status_led_init(void) {
    if (led_initialized) {
        ESP_LOGW(TAG, "Status LED already initialized");
        return ESP_OK;
    }

    // Configure GPIO15 as output
    gpio_config_t led_cfg = {
        .pin_bit_mask = (1ULL << GPIO_STATUS_LED),
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE
    };

    esp_err_t ret = gpio_config(&led_cfg);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to configure GPIO%d: %s", GPIO_STATUS_LED, esp_err_to_name(ret));
        return ret;
    }

    // Start with LED OFF
    gpio_set_level(GPIO_STATUS_LED, LED_OFF);
    led_current_state = false;
    led_initialized = true;

    ESP_LOGI(TAG, "Status LED initialized on GPIO%d (active-low)", GPIO_STATUS_LED);
    return ESP_OK;
}

void status_led_on(void) {
    if (!led_initialized) {
        ESP_LOGW(TAG, "Status LED not initialized");
        return;
    }
    gpio_set_level(GPIO_STATUS_LED, LED_ON);
    led_current_state = true;
}

void status_led_off(void) {
    if (!led_initialized) {
        ESP_LOGW(TAG, "Status LED not initialized");
        return;
    }
    gpio_set_level(GPIO_STATUS_LED, LED_OFF);
    led_current_state = false;
}

void status_led_blink(uint8_t count, uint32_t on_ms, uint32_t off_ms) {
    if (!led_initialized) {
        ESP_LOGW(TAG, "Status LED not initialized");
        return;
    }

    for (uint8_t i = 0; i < count; i++) {
        status_led_on();
        vTaskDelay(pdMS_TO_TICKS(on_ms));
        status_led_off();

        // Don't delay after last blink
        if (i < count - 1) {
            vTaskDelay(pdMS_TO_TICKS(off_ms));
        }
    }
}

void status_led_pattern(status_pattern_t pattern) {
    if (!led_initialized) {
        ESP_LOGW(TAG, "Status LED not initialized");
        return;
    }

    switch (pattern) {
        case STATUS_PATTERN_BLE_CONNECTED:
            // 5× blink (100ms ON, 100ms OFF) - BLE client connected
            ESP_LOGI(TAG, "Pattern: BLE Connected (5× blink)");
            status_led_blink(5, 100, 100);
            break;

        case STATUS_PATTERN_BLE_REENABLE:
            // 3× blink (100ms ON, 100ms OFF) - BLE advertising restarted
            ESP_LOGI(TAG, "Pattern: BLE Re-enabled (3× blink)");
            status_led_blink(3, 100, 100);
            break;

        case STATUS_PATTERN_LOW_BATTERY:
            // 3× blink (200ms ON, 200ms OFF) - Low battery warning
            ESP_LOGI(TAG, "Pattern: Low Battery Warning (3× slow blink)");
            status_led_blink(3, 200, 200);
            break;

        case STATUS_PATTERN_NVS_RESET:
            // 3× blink (100ms ON, 100ms OFF) - NVS factory reset successful
            ESP_LOGI(TAG, "Pattern: NVS Reset Success (3× blink)");
            status_led_blink(3, 100, 100);
            break;

        case STATUS_PATTERN_MODE_CHANGE:
            // 1× quick blink (50ms ON) - Mode changed
            ESP_LOGI(TAG, "Pattern: Mode Change (1× quick blink)");
            status_led_blink(1, 50, 0);
            break;

        case STATUS_PATTERN_BUTTON_HOLD:
            // Continuous ON - Button hold detected
            ESP_LOGI(TAG, "Pattern: Button Hold (continuous ON)");
            status_led_on();
            break;

        case STATUS_PATTERN_COUNTDOWN:
            // Continuous ON - Shutdown countdown
            ESP_LOGI(TAG, "Pattern: Shutdown Countdown (continuous ON)");
            status_led_on();
            break;

        case STATUS_PATTERN_PAIRING_WAIT:
            // Solid ON - Waiting for peer discovery (Phase 1b.3)
            ESP_LOGI(TAG, "Pattern: Pairing Wait (solid ON + purple WS2812B)");
            status_led_on();
            // WS2812B: Solid purple (palette index 7: RGB 128, 0, 255)
            // Only control if motor doesn't own it
            if (led_is_enabled() && !led_get_motor_ownership()) {
                led_set_palette(7, 20);  // Purple at 20% brightness
            }
            break;

        case STATUS_PATTERN_PAIRING_PROGRESS:
            // Pulsing 1Hz (500ms ON, 500ms OFF) - Pairing in progress (Phase 1b.3)
            ESP_LOGI(TAG, "Pattern: Pairing Progress (pulsing 1Hz + purple WS2812B)");
            // Note: This is a one-shot pattern, caller should loop if continuous pulsing needed
            status_led_on();
            // WS2812B: Purple ON (palette index 7: RGB 128, 0, 255)
            // Only control if motor doesn't own it
            if (led_is_enabled() && !led_get_motor_ownership()) {
                led_set_palette(7, 20);  // Purple at 20% brightness
            }
            vTaskDelay(pdMS_TO_TICKS(500));
            status_led_off();
            // WS2812B: OFF (clear)
            if (led_is_enabled() && !led_get_motor_ownership()) {
                led_clear();
            }
            vTaskDelay(pdMS_TO_TICKS(500));
            break;

        case STATUS_PATTERN_PAIRING_SUCCESS:
            // GPIO15 blink + WS2812B green 3× blink (Phase 1b.3)
            ESP_LOGI(TAG, "Pattern: Pairing Success (GPIO15 + WS2812B green 3× blink)");

            // 3× synchronized blink (250ms ON, 250ms OFF) = 1.5 seconds total
            for (int i = 0; i < 3; i++) {
                // Blink ON
                status_led_on();
                // WS2812B: Only control if motor doesn't own it
                if (led_is_enabled() && !led_get_motor_ownership()) {
                    led_set_palette(1, 20);  // Green (palette index 1) at 20% brightness
                }
                vTaskDelay(pdMS_TO_TICKS(250));

                // Blink OFF
                status_led_off();
                if (led_is_enabled() && !led_get_motor_ownership()) {
                    led_clear();
                }
                if (i < 2) {  // Don't delay after last blink
                    vTaskDelay(pdMS_TO_TICKS(250));
                }
            }
            break;

        case STATUS_PATTERN_PAIRING_FAILED:
            // GPIO15 blink + WS2812B red 3× blink (Phase 1b.3)
            ESP_LOGI(TAG, "Pattern: Pairing Failed (GPIO15 + WS2812B red 3× blink)");

            // 3× synchronized blink (250ms ON, 250ms OFF) = 1.5 seconds total
            for (int i = 0; i < 3; i++) {
                // Blink ON
                status_led_on();
                // WS2812B: Only control if motor doesn't own it
                if (led_is_enabled() && !led_get_motor_ownership()) {
                    led_set_palette(0, 20);  // Red (palette index 0) at 20% brightness
                }
                vTaskDelay(pdMS_TO_TICKS(250));

                // Blink OFF
                status_led_off();
                if (led_is_enabled() && !led_get_motor_ownership()) {
                    led_clear();
                }
                if (i < 2) {  // Don't delay after last blink
                    vTaskDelay(pdMS_TO_TICKS(250));
                }
            }
            break;

        default:
            ESP_LOGW(TAG, "Unknown pattern: %d", pattern);
            break;
    }
}

void status_led_toggle(void) {
    if (!led_initialized) {
        ESP_LOGW(TAG, "Status LED not initialized");
        return;
    }

    if (led_current_state) {
        status_led_off();
    } else {
        status_led_on();
    }
}

bool status_led_is_on(void) {
    if (!led_initialized) {
        return false;
    }
    return led_current_state;
}

esp_err_t status_led_deinit(void) {
    if (!led_initialized) {
        return ESP_OK;
    }

    // Turn LED off
    status_led_off();

    // Reset GPIO to default state (input)
    gpio_reset_pin(GPIO_STATUS_LED);

    led_initialized = false;
    ESP_LOGI(TAG, "Status LED deinitialized");

    return ESP_OK;
}