/**
 * @file minimal_battery_voltage_test.c
 * @brief Minimal Battery Voltage Sensor Diagnostic (NO LVO PROTECTION)
 *
 * Purpose: Raw battery voltage sensor diagnostics WITHOUT any protection logic
 *
 * IMPORTANT: This is a hardware diagnostic tool only. It does NOT include:
 *   - Low Voltage Cutout (LVO) protection
 *   - Deep sleep on low battery
 *   - Session time limits
 *
 * Use this test to:
 *   - Verify ADC hardware is working
 *   - Check voltage divider circuit
 *   - Diagnose sensor behavior with/without battery
 *   - Calibrate voltage readings
 *
 * Hardware Test Behavior:
 *   - Read battery voltage every 500ms
 *   - Display raw ADC value, GPIO2 voltage, and calculated battery voltage
 *   - Runs continuously until button hold (5s) triggers deep sleep
 *   - NO automatic shutdown or protection
 *
 * Test Sequence:
 *   1. Power on → Initialize ADC and GPIO
 *   2. Continuously read and display:
 *      - Raw ADC value (0-4095)
 *      - Voltage at GPIO2 (0-3.3V)
 *      - Calculated battery voltage (accounting for divider)
 *   3. Hold button 5s: Enter deep sleep
 *
 * GPIO Configuration:
 *   - GPIO1: Button input (RTC GPIO, hardware pull-up, wake source)
 *   - GPIO2: Battery voltage ADC input (ADC1_CH2, resistor divider)
 *   - GPIO21: Battery monitor enable (P-MOSFET gate control, HIGH=enabled)
 *   - GPIO15: Status LED output (ACTIVE LOW - 0=ON, 1=OFF)
 *
 * Battery Voltage Calculation:
 *   - Resistor divider: VBAT → 3.3kΩ → GPIO2 → 10kΩ → GND
 *   - Divider ratio: 10kΩ / 13.3kΩ = 0.7519
 *   - V_GPIO2 = V_BAT × 0.7519
 *   - V_BAT = V_GPIO2 / 0.7519 = V_GPIO2 × 1.3301
 *
 * Display Format:
 *   RAW: 3250 (0-4095) | GPIO2: 2.89V | VBAT: 3.85V
 *
 * Build & Run:
 *   pio run -e minimal_battery_voltage_test -t upload && pio device monitor
 *
 * Expected Behavior WITHOUT Battery:
 *   RAW: 0-50 (floating/noise) | GPIO2: 0.00-0.05V | VBAT: 0.00-0.07V
 *
 * Expected Behavior WITH Battery (4.2V):
 *   RAW: 3300-3400 | GPIO2: 3.15V | VBAT: 4.19V
 *
 * Seeed Xiao ESP32C6: ESP-IDF v5.5.0
 * Generated with assistance from Claude Sonnet 4 (Anthropic)
 */

#include <stdio.h>
#include <inttypes.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"
#include "driver/rtc_io.h"
#include "esp_adc/adc_oneshot.h"
#include "esp_adc/adc_cali.h"
#include "esp_adc/adc_cali_scheme.h"
#include "esp_sleep.h"
#include "esp_log.h"
#include "esp_timer.h"

static const char *TAG = "MIN_BAT_TEST";

// ========================================
// GPIO PIN DEFINITIONS
// ========================================
#define GPIO_BUTTON             1       // Button input (RTC GPIO, hardware pull-up)
#define GPIO_BAT_VOLTAGE        2       // Battery voltage ADC input (ADC1_CH2)
#define GPIO_STATUS_LED         15      // Status LED (ACTIVE LOW)
#define GPIO_BAT_ENABLE         21      // Battery monitor enable (HIGH=enabled)

// ========================================
// ADC CONFIGURATION
// ========================================
#define ADC_UNIT                ADC_UNIT_1
#define ADC_CHANNEL             ADC_CHANNEL_2       // GPIO2 = ADC1_CH2
#define ADC_ATTEN               ADC_ATTEN_DB_12     // 0-3.3V range
#define ADC_BITWIDTH            ADC_BITWIDTH_12     // 12-bit resolution (0-4095)

// ========================================
// BATTERY VOLTAGE CALCULATIONS
// ========================================
// Resistor divider: VBAT → 3.3kΩ → GPIO2 → 10kΩ → GND
#define RESISTOR_TOP_KOHM       3.3f    // Top resistor (VBAT to GPIO2)
#define RESISTOR_BOTTOM_KOHM    10.0f   // Bottom resistor (GPIO2 to GND)
#define DIVIDER_RATIO           (RESISTOR_BOTTOM_KOHM / (RESISTOR_TOP_KOHM + RESISTOR_BOTTOM_KOHM))
#define VOLTAGE_MULTIPLIER      (1.0f / DIVIDER_RATIO)  // 1.3301

// ========================================
// TIMING CONFIGURATION
// ========================================
#define BAT_READ_INTERVAL_MS    500     // Read battery every 500ms (faster for diagnostics)
#define BAT_ENABLE_SETTLE_MS    10      // Voltage divider settling time
#define BUTTON_SAMPLE_PERIOD_MS 10      // Button state sampling rate
#define COUNTDOWN_START_MS      1000    // Start countdown after 1 second hold
#define COUNTDOWN_SECONDS       5       // Countdown duration
#define LED_BLINK_PERIOD_MS     200     // LED blink while waiting for release

// ========================================
// LED STATE (ACTIVE LOW)
// ========================================
#define LED_ON                  0       // GPIO low = LED on
#define LED_OFF                 1       // GPIO high = LED off

// ========================================
// GLOBAL STATE
// ========================================
static adc_oneshot_unit_handle_t adc_handle = NULL;
static adc_cali_handle_t adc_cali_handle = NULL;
static bool adc_calibrated = false;

/**
 * @brief Initialize ADC calibration for accurate voltage readings
 * @param[out] out_handle Calibration handle (output)
 * @return true if calibration successful, false otherwise
 */
static bool adc_calibration_init(adc_cali_handle_t *out_handle) {
    adc_cali_handle_t handle = NULL;
    esp_err_t ret = ESP_FAIL;
    bool calibrated = false;

    ESP_LOGI(TAG, "Initializing ADC calibration...");

    // Try eFuse calibration first (most accurate)
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

    // Fall back to Line Fitting
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
        ESP_LOGW(TAG, "ADC calibration not available - using raw values");
    }

    return calibrated;
}

/**
 * @brief Initialize ADC for battery voltage monitoring
 * @return ESP_OK on success, error code otherwise
 */
static esp_err_t init_adc(void) {
    esp_err_t ret;

    // Configure ADC Oneshot Unit
    adc_oneshot_unit_init_cfg_t init_config = {
        .unit_id = ADC_UNIT,
        .ulp_mode = ADC_ULP_MODE_DISABLE,
    };

    ret = adc_oneshot_new_unit(&init_config, &adc_handle);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "ADC unit init failed: %s", esp_err_to_name(ret));
        return ret;
    }

    ESP_LOGI(TAG, "ADC unit initialized (ADC1)");

    // Configure ADC Channel
    adc_oneshot_chan_cfg_t channel_config = {
        .atten = ADC_ATTEN,
        .bitwidth = ADC_BITWIDTH,
    };

    ret = adc_oneshot_config_channel(adc_handle, ADC_CHANNEL, &channel_config);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "ADC channel config failed: %s", esp_err_to_name(ret));
        return ret;
    }

    ESP_LOGI(TAG, "ADC channel configured (GPIO%d = ADC1_CH%d)", GPIO_BAT_VOLTAGE, ADC_CHANNEL);
    ESP_LOGI(TAG, "ADC attenuation: DB_12 (0-3.3V range)");
    ESP_LOGI(TAG, "ADC resolution: 12-bit (0-4095)");

    // Initialize Calibration
    adc_calibrated = adc_calibration_init(&adc_cali_handle);

    return ESP_OK;
}

/**
 * @brief Read battery voltage with proper enable/disable sequence
 * @param[out] adc_raw_out Raw ADC value 0-4095 (output)
 * @param[out] raw_voltage_mv Raw voltage at GPIO2 in mV (output)
 * @param[out] battery_voltage_v Calculated battery voltage (output)
 * @return ESP_OK on success, error code otherwise
 */
static esp_err_t read_battery_voltage(int *adc_raw_out, int *raw_voltage_mv, float *battery_voltage_v) {
    esp_err_t ret;
    int adc_raw = 0;

    // Enable Battery Monitor
    gpio_set_level(GPIO_BAT_ENABLE, 1);  // HIGH = enabled

    // Wait for Voltage Divider Settling
    vTaskDelay(pdMS_TO_TICKS(BAT_ENABLE_SETTLE_MS));

    // Read ADC Value
    ret = adc_oneshot_read(adc_handle, ADC_CHANNEL, &adc_raw);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "ADC read failed: %s", esp_err_to_name(ret));
        gpio_set_level(GPIO_BAT_ENABLE, 0);  // Disable on error
        return ret;
    }

    // Convert to Voltage (mV)
    int voltage_mv = 0;
    if (adc_calibrated) {
        ret = adc_cali_raw_to_voltage(adc_cali_handle, adc_raw, &voltage_mv);
        if (ret != ESP_OK) {
            ESP_LOGW(TAG, "ADC calibration conversion failed: %s", esp_err_to_name(ret));
            // Fall back to linear approximation: 3300mV / 4095
            voltage_mv = (adc_raw * 3300) / 4095;
        }
    } else {
        // No calibration available - use linear approximation
        voltage_mv = (adc_raw * 3300) / 4095;
    }

    // Disable Battery Monitor (Power Efficient)
    gpio_set_level(GPIO_BAT_ENABLE, 0);  // LOW = disabled

    // Calculate Battery Voltage
    // Account for resistor divider: V_BAT = V_GPIO2 × (R1 + R2) / R2
    float raw_voltage_v = voltage_mv / 1000.0f;
    float battery_v = raw_voltage_v * VOLTAGE_MULTIPLIER;

    // Return Results
    *adc_raw_out = adc_raw;
    *raw_voltage_mv = voltage_mv;
    *battery_voltage_v = battery_v;

    return ESP_OK;
}

/**
 * @brief Configure GPIO1 (button) as RTC GPIO for deep sleep wake
 * @return ESP_OK on success, error code otherwise
 */
static esp_err_t configure_button_wake(void) {
    if (!rtc_gpio_is_valid_gpio(GPIO_BUTTON)) {
        ESP_LOGE(TAG, "GPIO%d is not RTC-capable!", GPIO_BUTTON);
        return ESP_ERR_INVALID_ARG;
    }

    // Configure ext1 wake source
    uint64_t gpio_mask = (1ULL << GPIO_BUTTON);
    esp_err_t ret = esp_sleep_enable_ext1_wakeup(gpio_mask, ESP_EXT1_WAKEUP_ANY_LOW);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to configure ext1 wake: %s", esp_err_to_name(ret));
        return ret;
    }

    // Configure GPIO1 for RTC use
    ret = rtc_gpio_init(GPIO_BUTTON);
    if (ret != ESP_OK) return ret;

    ret = rtc_gpio_set_direction(GPIO_BUTTON, RTC_GPIO_MODE_INPUT_ONLY);
    if (ret != ESP_OK) return ret;

    ret = rtc_gpio_pullup_en(GPIO_BUTTON);
    if (ret != ESP_OK) return ret;

    ret = rtc_gpio_pulldown_dis(GPIO_BUTTON);
    if (ret != ESP_OK) return ret;

    return ESP_OK;
}

/**
 * @brief Initialize GPIO for button, LED, and battery enable
 * @return ESP_OK on success, error code otherwise
 */
static esp_err_t init_gpio(void) {
    esp_err_t ret;

    // Configure Button (GPIO1)
    gpio_config_t button_config = {
        .pin_bit_mask = (1ULL << GPIO_BUTTON),
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_ENABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE
    };

    ret = gpio_config(&button_config);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Button GPIO config failed: %s", esp_err_to_name(ret));
        return ret;
    }

    ESP_LOGI(TAG, "Button GPIO%d configured", GPIO_BUTTON);

    // Configure LED (GPIO15) - ACTIVE LOW
    gpio_config_t led_config = {
        .pin_bit_mask = (1ULL << GPIO_STATUS_LED),
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE
    };

    ret = gpio_config(&led_config);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "LED GPIO config failed: %s", esp_err_to_name(ret));
        return ret;
    }

    gpio_set_level(GPIO_STATUS_LED, LED_ON);
    ESP_LOGI(TAG, "LED GPIO%d configured (active LOW, state: ON)", GPIO_STATUS_LED);

    // Configure Battery Enable (GPIO21)
    gpio_config_t bat_enable_config = {
        .pin_bit_mask = (1ULL << GPIO_BAT_ENABLE),
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE
    };

    ret = gpio_config(&bat_enable_config);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Battery enable GPIO config failed: %s", esp_err_to_name(ret));
        return ret;
    }

    // Start with battery monitor disabled (power efficient)
    gpio_set_level(GPIO_BAT_ENABLE, 0);
    ESP_LOGI(TAG, "Battery enable GPIO%d configured (initial state: disabled)", GPIO_BAT_ENABLE);

    return ESP_OK;
}

/**
 * @brief Enter deep sleep mode (waits for button release first)
 * @return Does not return (device sleeps)
 */
static void enter_deep_sleep(void) {
    ESP_LOGI(TAG, "");

    // Check if button is still held
    if (gpio_get_level(GPIO_BUTTON) == 0) {
        ESP_LOGI(TAG, "Waiting for button release...");
        ESP_LOGI(TAG, "(LED will blink - release button when ready)");

        // Blink LED while waiting for release
        bool blink_state = LED_OFF;
        while (gpio_get_level(GPIO_BUTTON) == 0) {
            blink_state = (blink_state == LED_ON) ? LED_OFF : LED_ON;
            gpio_set_level(GPIO_STATUS_LED, blink_state);
            vTaskDelay(pdMS_TO_TICKS(LED_BLINK_PERIOD_MS));
        }

        gpio_set_level(GPIO_STATUS_LED, LED_OFF);
        ESP_LOGI(TAG, "Button released!");
    }

    ESP_LOGI(TAG, "");
    ESP_LOGI(TAG, "===========================================");
    ESP_LOGI(TAG, "Entering ultra-low power deep sleep mode...");
    ESP_LOGI(TAG, "===========================================");
    ESP_LOGI(TAG, "Press button (GPIO%d) to wake device", GPIO_BUTTON);
    ESP_LOGI(TAG, "");

    vTaskDelay(pdMS_TO_TICKS(100));

    configure_button_wake();
    esp_deep_sleep_start();
}

/**
 * @brief Battery monitoring task - reads voltage continuously
 *
 * MINIMAL VERSION: No LVO protection, no session limits
 * Just reads and displays raw sensor values for diagnostics
 */
static void battery_task(void *pvParameters) {
    ESP_LOGI(TAG, "Battery monitoring task started");
    ESP_LOGI(TAG, "Reading battery voltage every %d ms...", BAT_READ_INTERVAL_MS);
    ESP_LOGI(TAG, "NO LVO protection - raw diagnostics mode");
    ESP_LOGI(TAG, "");

    uint32_t reading_count = 0;

    while (1) {
        int adc_raw = 0;
        int raw_voltage_mv = 0;
        float battery_voltage_v = 0.0f;

        // Read battery voltage with enable/disable sequence
        esp_err_t ret = read_battery_voltage(&adc_raw, &raw_voltage_mv, &battery_voltage_v);

        if (ret == ESP_OK) {
            // Display format: RAW: 3250 (0-4095) | GPIO2: 2.89V | VBAT: 3.85V | #5
            ESP_LOGI(TAG, "RAW: %4d (0-4095) | GPIO2: %.2fV | VBAT: %.2fV | #%lu",
                     adc_raw,
                     raw_voltage_mv / 1000.0f,
                     battery_voltage_v,
                     reading_count);
            reading_count++;
        } else {
            ESP_LOGE(TAG, "Battery read failed | #%lu", reading_count);
        }

        // Wait for next reading (JPL compliant - no busy-wait)
        vTaskDelay(pdMS_TO_TICKS(BAT_READ_INTERVAL_MS));
    }
}

/**
 * @brief Button monitoring task - handles 5-second hold for deep sleep
 */
static void button_task(void *pvParameters) {
    bool previous_button_state = true;
    bool button_state = true;
    uint32_t press_start_time = 0;
    bool press_detected = false;
    bool countdown_started = false;

    ESP_LOGI(TAG, "Button monitoring task started");
    ESP_LOGI(TAG, "Hold button 5 seconds to enter deep sleep");
    ESP_LOGI(TAG, "");

    while (1) {
        button_state = gpio_get_level(GPIO_BUTTON);

        // Button press detection
        if (previous_button_state == 1 && button_state == 0) {
            press_start_time = (uint32_t)(esp_timer_get_time() / 1000);
            press_detected = true;
            countdown_started = false;
        }

        // Button hold detection with countdown
        if (button_state == 0 && press_detected) {
            uint32_t current_time = (uint32_t)(esp_timer_get_time() / 1000);
            uint32_t press_duration = current_time - press_start_time;

            if (press_duration >= COUNTDOWN_START_MS && !countdown_started) {
                ESP_LOGI(TAG, "");
                ESP_LOGI(TAG, "Hold button for deep sleep...");
                countdown_started = true;

                for (int i = COUNTDOWN_SECONDS; i > 0; i--) {
                    ESP_LOGI(TAG, "%d...", i);
                    vTaskDelay(pdMS_TO_TICKS(1000));

                    if (gpio_get_level(GPIO_BUTTON) == 1) {
                        ESP_LOGI(TAG, "Button released - cancelling deep sleep");
                        ESP_LOGI(TAG, "");
                        countdown_started = false;
                        press_detected = false;
                        goto continue_loop;
                    }
                }

                enter_deep_sleep();
            }
        }

        // Button release detection
        if (previous_button_state == 0 && button_state == 1) {
            press_detected = false;
            countdown_started = false;
        }

continue_loop:
        previous_button_state = button_state;
        vTaskDelay(pdMS_TO_TICKS(BUTTON_SAMPLE_PERIOD_MS));
    }
}

/**
 * @brief Main application entry point
 */
void app_main(void) {
    ESP_LOGI(TAG, "");
    ESP_LOGI(TAG, "================================================");
    ESP_LOGI(TAG, "=== MINIMAL Battery Voltage Diagnostic Test ===");
    ESP_LOGI(TAG, "================================================");
    ESP_LOGI(TAG, "Board: Seeed Xiao ESP32C6");
    ESP_LOGI(TAG, "Framework: ESP-IDF v5.5.0");
    ESP_LOGI(TAG, "");
    ESP_LOGW(TAG, "WARNING: NO LVO PROTECTION IN THIS TEST");
    ESP_LOGW(TAG, "This is a hardware diagnostic tool only!");
    ESP_LOGI(TAG, "");

    // Print Configuration
    ESP_LOGI(TAG, "GPIO Configuration:");
    ESP_LOGI(TAG, "  Battery voltage: GPIO%d (ADC1_CH%d)", GPIO_BAT_VOLTAGE, ADC_CHANNEL);
    ESP_LOGI(TAG, "  Battery enable: GPIO%d (HIGH=enabled)", GPIO_BAT_ENABLE);
    ESP_LOGI(TAG, "  Button: GPIO%d (wake source)", GPIO_BUTTON);
    ESP_LOGI(TAG, "  Status LED: GPIO%d (active LOW)", GPIO_STATUS_LED);
    ESP_LOGI(TAG, "");

    ESP_LOGI(TAG, "Voltage Divider:");
    ESP_LOGI(TAG, "  VBAT → %.1fkΩ → GPIO%d → %.1fkΩ → GND",
             RESISTOR_TOP_KOHM, GPIO_BAT_VOLTAGE, RESISTOR_BOTTOM_KOHM);
    ESP_LOGI(TAG, "  Divider ratio: %.4f", DIVIDER_RATIO);
    ESP_LOGI(TAG, "  Voltage multiplier: %.4f", VOLTAGE_MULTIPLIER);
    ESP_LOGI(TAG, "");

    // Initialize GPIO
    ESP_LOGI(TAG, "Initializing GPIO...");
    esp_err_t ret = init_gpio();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "GPIO initialization FAILED - halting");
        while(1) vTaskDelay(pdMS_TO_TICKS(1000));
    }
    ESP_LOGI(TAG, "GPIO initialized successfully");
    ESP_LOGI(TAG, "");

    // Initialize ADC
    ESP_LOGI(TAG, "Initializing ADC...");
    ret = init_adc();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "ADC initialization FAILED - halting");
        while(1) vTaskDelay(pdMS_TO_TICKS(1000));
    }
    ESP_LOGI(TAG, "ADC initialized successfully");
    ESP_LOGI(TAG, "");

    // Configure Deep Sleep Wake Source
    ESP_LOGI(TAG, "Configuring deep sleep wake source...");
    ret = configure_button_wake();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Wake source configuration FAILED - halting");
        while(1) vTaskDelay(pdMS_TO_TICKS(1000));
    }
    ESP_LOGI(TAG, "Wake source configured successfully");
    ESP_LOGI(TAG, "");

    // NO LVO CHECK - Start monitoring immediately
    ESP_LOGI(TAG, "Skipping LVO check (minimal diagnostic mode)");
    ESP_LOGI(TAG, "");

    // Create Tasks
    ESP_LOGI(TAG, "Starting monitoring tasks...");

    xTaskCreate(battery_task, "battery_task", 3072, NULL, 5, NULL);
    xTaskCreate(button_task, "button_task", 2048, NULL, 5, NULL);

    ESP_LOGI(TAG, "Hardware test running!");
    ESP_LOGI(TAG, "================================================");
    ESP_LOGI(TAG, "");
}
