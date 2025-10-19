/**
 * @file hbridge_test.c
 * @brief Simple H-bridge hardware test (GPIO control, no PWM)
 * 
 * Test sequence: Forward -> Coast -> Reverse -> Coast
 * GPIO15 LED: ON during Forward/Reverse, OFF during Coast
 * 
 * LED Behavior: Seeed Xiao ESP32C6 user LED is ACTIVE LOW
 *   - gpio_set_level(15, 0) = LED ON
 *   - gpio_set_level(15, 1) = LED OFF
 * 
 * This is a standalone hardware test - builds as separate PlatformIO environment.
 * Command: pio run -e hbridge_test -t upload && pio device monitor
 */

#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"
#include "esp_log.h"

static const char *TAG = "HBRIDGE_TEST";

// GPIO Pin Definitions (from project spec)
#define GPIO_HBRIDGE_IN1        19      // Motor forward control
#define GPIO_HBRIDGE_IN2        20      // Motor reverse control
#define GPIO_STATUS_LED         15      // Status LED (ACTIVE LOW on Xiao ESP32C6)

// LED Control Macros (ACTIVE LOW)
#define LED_ON      0       // LED is ACTIVE LOW
#define LED_OFF     1       // LED is ACTIVE LOW

// Test timing (all in milliseconds)
#define TEST_FORWARD_TIME_MS    2000    // 2 seconds forward
#define TEST_COAST_TIME_MS      1000    // 1 second coast
#define TEST_REVERSE_TIME_MS    2000    // 2 seconds reverse
#define DEAD_TIME_MS            1       // 1ms dead time between transitions

/**
 * @brief Initialize GPIO pins for H-bridge and status LED
 */
static void init_gpio(void) {
    // Configure H-bridge control pins as outputs
    gpio_config_t hbridge_config = {
        .pin_bit_mask = (1ULL << GPIO_HBRIDGE_IN1) | (1ULL << GPIO_HBRIDGE_IN2),
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE
    };
    gpio_config(&hbridge_config);

    // Configure status LED as output (ACTIVE LOW)
    gpio_config_t led_config = {
        .pin_bit_mask = (1ULL << GPIO_STATUS_LED),
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE
    };
    gpio_config(&led_config);

    // Initialize to safe coast state
    gpio_set_level(GPIO_HBRIDGE_IN1, 0);
    gpio_set_level(GPIO_HBRIDGE_IN2, 0);
    gpio_set_level(GPIO_STATUS_LED, LED_OFF);

    ESP_LOGI(TAG, "GPIO initialized - H-bridge in coast mode, LED off (active low)");
}

/**
 * @brief Set H-bridge to forward mode
 */
static void hbridge_forward(void) {
    // Coast first (safety)
    gpio_set_level(GPIO_HBRIDGE_IN1, 0);
    gpio_set_level(GPIO_HBRIDGE_IN2, 0);
    vTaskDelay(pdMS_TO_TICKS(DEAD_TIME_MS));
    
    // Forward: IN1=HIGH, IN2=LOW
    gpio_set_level(GPIO_HBRIDGE_IN1, 1);
    gpio_set_level(GPIO_HBRIDGE_IN2, 0);
    
    ESP_LOGI(TAG, "H-bridge: FORWARD");
}

/**
 * @brief Set H-bridge to reverse mode
 */
static void hbridge_reverse(void) {
    // Coast first (safety)
    gpio_set_level(GPIO_HBRIDGE_IN1, 0);
    gpio_set_level(GPIO_HBRIDGE_IN2, 0);
    vTaskDelay(pdMS_TO_TICKS(DEAD_TIME_MS));
    
    // Reverse: IN1=LOW, IN2=HIGH
    gpio_set_level(GPIO_HBRIDGE_IN1, 0);
    gpio_set_level(GPIO_HBRIDGE_IN2, 1);
    
    ESP_LOGI(TAG, "H-bridge: REVERSE");
}

/**
 * @brief Set H-bridge to coast mode
 */
static void hbridge_coast(void) {
    // Coast: IN1=LOW, IN2=LOW
    gpio_set_level(GPIO_HBRIDGE_IN1, 0);
    gpio_set_level(GPIO_HBRIDGE_IN2, 0);
    
    ESP_LOGI(TAG, "H-bridge: COAST");
}

/**
 * @brief Main test task - cycles through Forward/Coast/Reverse/Coast
 */
static void test_task(void *pvParameters) {
    ESP_LOGI(TAG, "Starting H-bridge test sequence");
    ESP_LOGI(TAG, "Watch GPIO15 LED (active low) and motor behavior");
    ESP_LOGI(TAG, "LED ON = motor active, LED OFF = coast");
    
    while (1) {
        // === FORWARD PHASE ===
        ESP_LOGI(TAG, "--- FORWARD (LED ON) ---");
        gpio_set_level(GPIO_STATUS_LED, LED_ON);
        hbridge_forward();
        vTaskDelay(pdMS_TO_TICKS(TEST_FORWARD_TIME_MS));
        
        // === COAST PHASE 1 ===
        ESP_LOGI(TAG, "--- COAST (LED OFF) ---");
        gpio_set_level(GPIO_STATUS_LED, LED_OFF);
        hbridge_coast();
        vTaskDelay(pdMS_TO_TICKS(TEST_COAST_TIME_MS));
        
        // === REVERSE PHASE ===
        ESP_LOGI(TAG, "--- REVERSE (LED ON) ---");
        gpio_set_level(GPIO_STATUS_LED, LED_ON);
        hbridge_reverse();
        vTaskDelay(pdMS_TO_TICKS(TEST_REVERSE_TIME_MS));
        
        // === COAST PHASE 2 ===
        ESP_LOGI(TAG, "--- COAST (LED OFF) ---");
        gpio_set_level(GPIO_STATUS_LED, LED_OFF);
        hbridge_coast();
        vTaskDelay(pdMS_TO_TICKS(TEST_COAST_TIME_MS));
        
        ESP_LOGI(TAG, "Test cycle complete - repeating...\n");
    }
}

void app_main(void) {
    ESP_LOGI(TAG, "=== H-Bridge Hardware Test ===");
    ESP_LOGI(TAG, "Board: Seeed Xiao ESP32C6");
    ESP_LOGI(TAG, "Test sequence: Forward -> Coast -> Reverse -> Coast");
    ESP_LOGI(TAG, "GPIO15 LED: Active LOW (ON=0, OFF=1)");
    ESP_LOGI(TAG, "");
    ESP_LOGI(TAG, "Hardware Connections:");
    ESP_LOGI(TAG, "  GPIO19 (IN1) -> H-bridge IN1");
    ESP_LOGI(TAG, "  GPIO20 (IN2) -> H-bridge IN2");
    ESP_LOGI(TAG, "  GPIO15       -> Status LED (active low)");
    ESP_LOGI(TAG, "");
    
    // Initialize hardware
    init_gpio();
    
    // Start test task
    xTaskCreate(test_task, "test_task", 2048, NULL, 5, NULL);
    
    ESP_LOGI(TAG, "Test running - monitor serial output and observe hardware");
}
