/**
 * @file ledc_blink_test.c
 * @brief Minimal LEDC PWM test - blink GPIO15 LED at 1Hz using PWM
 * 
 * Purpose: Verify LEDC peripheral works before using for H-bridge control
 * 
 * Test behavior:
 *   - GPIO15 LED blinks at 1Hz (500ms on, 500ms off)
 *   - Uses LEDC PWM at 1kHz carrier frequency, 8-bit resolution
 *   - LED is ACTIVE LOW (duty=255 = LED OFF, duty=0 = LED ON)
 * 
 * Seeed Xiao ESP32C6 LED: ACTIVE LOW
 *   - ledc_set_duty(0)   = LED FULLY ON (100% low)
 *   - ledc_set_duty(255) = LED FULLY OFF (100% high)
 * 
 * Build: pio run -e ledc_blink_test -t upload && pio device monitor
 * 
 * Generated with assistance from Claude Sonnet 4 (Anthropic)
 */

#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/ledc.h"
#include "esp_log.h"

static const char *TAG = "LEDC_BLINK";

// GPIO Pin Definition
#define GPIO_STATUS_LED         15      // Status LED (ACTIVE LOW on Xiao ESP32C6)

// LEDC PWM Configuration
#define PWM_FREQUENCY_HZ        1000    // 1kHz carrier frequency
#define PWM_RESOLUTION          LEDC_TIMER_8_BIT   // 8-bit (0-255 range)
#define PWM_TIMER               LEDC_TIMER_0
#define PWM_MODE                LEDC_LOW_SPEED_MODE
#define PWM_CHANNEL             LEDC_CHANNEL_0

// LED duty cycles (ACTIVE LOW: 0=ON, 255=OFF)
#define LED_ON_DUTY             0       // LED fully on
#define LED_OFF_DUTY            255     // LED fully off

// Blink timing
#define BLINK_ON_TIME_MS        500     // 500ms on
#define BLINK_OFF_TIME_MS       500     // 500ms off (1Hz total)

/**
 * @brief Initialize LEDC timer for PWM generation
 * @return ESP_OK on success, error code otherwise
 */
static esp_err_t init_ledc_timer(void) {
    ledc_timer_config_t ledc_timer = {
        .speed_mode       = PWM_MODE,
        .timer_num        = PWM_TIMER,
        .duty_resolution  = PWM_RESOLUTION,
        .freq_hz          = PWM_FREQUENCY_HZ,
        .clk_cfg          = LEDC_AUTO_CLK
    };
    
    esp_err_t ret = ledc_timer_config(&ledc_timer);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "LEDC timer config failed: %s", esp_err_to_name(ret));
        return ret;
    }
    
    ESP_LOGI(TAG, "LEDC timer OK: %dHz, 8-bit resolution", PWM_FREQUENCY_HZ);
    return ESP_OK;
}

/**
 * @brief Initialize LEDC channel for LED control
 * @return ESP_OK on success, error code otherwise
 */
static esp_err_t init_ledc_channel(void) {
    ledc_channel_config_t ledc_channel = {
        .gpio_num       = GPIO_STATUS_LED,
        .speed_mode     = PWM_MODE,
        .channel        = PWM_CHANNEL,
        .timer_sel      = PWM_TIMER,
        .duty           = LED_OFF_DUTY,  // Start with LED off
        .hpoint         = 0
    };
    
    esp_err_t ret = ledc_channel_config(&ledc_channel);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "LEDC channel config failed: %s", esp_err_to_name(ret));
        return ret;
    }
    
    ESP_LOGI(TAG, "LEDC channel OK: GPIO%d", GPIO_STATUS_LED);
    return ESP_OK;
}

/**
 * @brief Blink task - toggles LED using LEDC PWM at 1Hz
 */
static void blink_task(void *pvParameters) {
    ESP_LOGI(TAG, "Starting 1Hz blink test");
    ESP_LOGI(TAG, "LED duty: 0=ON, 255=OFF (active low)");
    
    uint32_t blink_count = 0;
    
    while (1) {
        // LED ON (duty = 0 for active low LED)
        ledc_set_duty(PWM_MODE, PWM_CHANNEL, LED_ON_DUTY);
        ledc_update_duty(PWM_MODE, PWM_CHANNEL);
        ESP_LOGI(TAG, "LED ON  [%lu]", blink_count);
        vTaskDelay(pdMS_TO_TICKS(BLINK_ON_TIME_MS));
        
        // LED OFF (duty = 255 for active low LED)
        ledc_set_duty(PWM_MODE, PWM_CHANNEL, LED_OFF_DUTY);
        ledc_update_duty(PWM_MODE, PWM_CHANNEL);
        ESP_LOGI(TAG, "LED OFF [%lu]", blink_count);
        vTaskDelay(pdMS_TO_TICKS(BLINK_OFF_TIME_MS));
        
        blink_count++;
    }
}

void app_main(void) {
    ESP_LOGI(TAG, "=== Minimal LEDC PWM Blink Test ===");
    ESP_LOGI(TAG, "Board: Seeed Xiao ESP32C6");
    ESP_LOGI(TAG, "LED: GPIO15 (active low)");
    ESP_LOGI(TAG, "PWM: 1kHz carrier, 8-bit resolution");
    ESP_LOGI(TAG, "Blink rate: 1Hz (500ms on, 500ms off)");
    ESP_LOGI(TAG, "");
    
    // Initialize LEDC timer
    ESP_LOGI(TAG, "Initializing LEDC timer...");
    esp_err_t ret = init_ledc_timer();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "LEDC timer FAILED - halting");
        while(1) vTaskDelay(pdMS_TO_TICKS(1000));
    }
    
    // Initialize LEDC channel
    ESP_LOGI(TAG, "Initializing LEDC channel...");
    ret = init_ledc_channel();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "LEDC channel FAILED - halting");
        while(1) vTaskDelay(pdMS_TO_TICKS(1000));
    }
    
    ESP_LOGI(TAG, "LEDC initialized successfully");
    ESP_LOGI(TAG, "Starting blink task...");
    
    // Create blink task
    xTaskCreate(blink_task, "blink_task", 2048, NULL, 5, NULL);
}
