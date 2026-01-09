/**
 * @file minimal_test.c
 * @brief Minimal test - just blink LED to verify basic operation
 */

#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"
#include "esp_log.h"

static const char *TAG = "MINIMAL_TEST";

#define GPIO_LED 15

void app_main(void) {
    ESP_LOGI(TAG, "=== MINIMAL TEST STARTING ===");
    ESP_LOGI(TAG, "If you see this, serial works!");
    
    // Configure LED
    gpio_config_t led_cfg = {
        .pin_bit_mask = (1ULL << GPIO_LED),
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE
    };
    gpio_config(&led_cfg);
    
    ESP_LOGI(TAG, "LED configured, starting blink...");
    
    while(1) {
        gpio_set_level(GPIO_LED, 0);  // LED ON (active low)
        ESP_LOGI(TAG, "LED ON");
        vTaskDelay(pdMS_TO_TICKS(500));
        
        gpio_set_level(GPIO_LED, 1);  // LED OFF
        ESP_LOGI(TAG, "LED OFF");
        vTaskDelay(pdMS_TO_TICKS(500));
    }
}
