/**
 * @file hbridge_pwm_test.c
 * @brief H-bridge hardware test with LEDC PWM control (25kHz, 10-bit, 60% duty)
 * 
 * Test sequence: Forward @ 60% → Coast → Reverse @ 60% → Coast
 * GPIO15 LED: ON during Forward/Reverse, OFF during Coast
 * 
 * LED Behavior: Seeed Xiao ESP32C6 user LED is ACTIVE LOW
 *   - gpio_set_level(15, 0) = LED ON
 *   - gpio_set_level(15, 1) = LED OFF
 * 
 * This is a standalone hardware test - builds as separate PlatformIO environment.
 * Command: pio run -e hbridge_pwm_test -t upload && pio device monitor
 */

#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"
#include "driver/ledc.h"
#include "esp_log.h"

static const char *TAG = "HBRIDGE_PWM_TEST";

// GPIO Pin Definitions (from project spec)
#define GPIO_HBRIDGE_IN2        19      // Motor reverse control (LEDC PWM)
#define GPIO_HBRIDGE_IN1        18      // Motor forward control (LEDC PWM) - MOVED from GPIO20
#define GPIO_STATUS_LED         15      // Status LED (ACTIVE LOW on Xiao ESP32C6)

// LEDC PWM Configuration
#define PWM_FREQUENCY_HZ        25000   // 25kHz (above human hearing)
#define PWM_RESOLUTION          LEDC_TIMER_10_BIT  // 10-bit (0-1023 range)
#define PWM_DUTY_CYCLE_PERCENT  60      // 60% duty cycle for this test
#define PWM_TIMER               LEDC_TIMER_0
#define PWM_MODE                LEDC_LOW_SPEED_MODE

// LEDC Channel Assignments
#define PWM_CHANNEL_IN1         LEDC_CHANNEL_0
#define PWM_CHANNEL_IN2         LEDC_CHANNEL_1

// LED Control Macros (ACTIVE LOW)
#define LED_ON      0       // LED is ACTIVE LOW
#define LED_OFF     1       // LED is ACTIVE LOW

// Test timing (all in milliseconds)
#define TEST_FORWARD_TIME_MS    2000    // 2 seconds forward @ 60%
#define TEST_COAST_TIME_MS      1000    // 1 second coast
#define TEST_REVERSE_TIME_MS    2000    // 2 seconds reverse @ 60%
#define DEAD_TIME_MS            1       // 1ms dead time between transitions

/**
 * @brief Calculate LEDC duty value from percentage (0-100%)
 * @param percent Duty cycle percentage
 * @return LEDC duty value (0-1023 for 10-bit)
 */
static uint32_t duty_from_percent(uint8_t percent) {
    if (percent > 100) percent = 100;
    return (1023 * percent) / 100;
}

/**
 * @brief Initialize LEDC timer for PWM generation
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
    
    ESP_LOGI(TAG, "LEDC timer configured: %dkHz, 10-bit resolution", PWM_FREQUENCY_HZ / 1000);
    return ESP_OK;
}

/**
 * @brief Initialize LEDC channels for H-bridge control
 */
static esp_err_t init_ledc_channels(void) {
    // Configure IN1 channel (forward)
    ledc_channel_config_t ledc_channel_in1 = {
        .gpio_num       = GPIO_HBRIDGE_IN1,
        .speed_mode     = PWM_MODE,
        .channel        = PWM_CHANNEL_IN1,
        .timer_sel      = PWM_TIMER,
        .duty           = 0,
        .hpoint         = 0
    };
    
    esp_err_t ret = ledc_channel_config(&ledc_channel_in1);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "LEDC channel IN1 config failed: %s", esp_err_to_name(ret));
        return ret;
    }
    
    // Configure IN2 channel (reverse)
    ledc_channel_config_t ledc_channel_in2 = {
        .gpio_num       = GPIO_HBRIDGE_IN2,
        .speed_mode     = PWM_MODE,
        .channel        = PWM_CHANNEL_IN2,
        .timer_sel      = PWM_TIMER,
        .duty           = 0,
        .hpoint         = 0
    };
    
    ret = ledc_channel_config(&ledc_channel_in2);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "LEDC channel IN2 config failed: %s", esp_err_to_name(ret));
        return ret;
    }
    
    ESP_LOGI(TAG, "LEDC channels configured on GPIO%d (IN1) and GPIO%d (IN2)", 
             GPIO_HBRIDGE_IN1, GPIO_HBRIDGE_IN2);
    return ESP_OK;
}

/**
 * @brief Initialize GPIO pins for status LED
 */
static esp_err_t init_status_led(void) {
    gpio_config_t led_config = {
        .pin_bit_mask = (1ULL << GPIO_STATUS_LED),
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE
    };
    
    esp_err_t ret = gpio_config(&led_config);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Status LED GPIO config failed: %s", esp_err_to_name(ret));
        return ret;
    }
    
    gpio_set_level(GPIO_STATUS_LED, LED_OFF);
    ESP_LOGI(TAG, "Status LED initialized on GPIO%d (active low)", GPIO_STATUS_LED);
    return ESP_OK;
}

/**
 * @brief Set H-bridge to forward mode with PWM
 * @param duty_percent PWM duty cycle (0-100%)
 */
static void hbridge_forward_pwm(uint8_t duty_percent) {
    // Coast first (safety)
    ledc_set_duty(PWM_MODE, PWM_CHANNEL_IN1, 0);
    ledc_set_duty(PWM_MODE, PWM_CHANNEL_IN2, 0);
    ledc_update_duty(PWM_MODE, PWM_CHANNEL_IN1);
    ledc_update_duty(PWM_MODE, PWM_CHANNEL_IN2);
    vTaskDelay(pdMS_TO_TICKS(DEAD_TIME_MS));
    
    // Forward: IN1=PWM, IN2=LOW
    uint32_t duty = duty_from_percent(duty_percent);
    ledc_set_duty(PWM_MODE, PWM_CHANNEL_IN1, duty);
    ledc_set_duty(PWM_MODE, PWM_CHANNEL_IN2, 0);
    ledc_update_duty(PWM_MODE, PWM_CHANNEL_IN1);
    ledc_update_duty(PWM_MODE, PWM_CHANNEL_IN2);
    
    ESP_LOGI(TAG, "H-bridge: FORWARD @ %d%% (duty=%lu/1023)", duty_percent, duty);
}

/**
 * @brief Set H-bridge to reverse mode with PWM
 * @param duty_percent PWM duty cycle (0-100%)
 */
static void hbridge_reverse_pwm(uint8_t duty_percent) {
    // Coast first (safety)
    ledc_set_duty(PWM_MODE, PWM_CHANNEL_IN1, 0);
    ledc_set_duty(PWM_MODE, PWM_CHANNEL_IN2, 0);
    ledc_update_duty(PWM_MODE, PWM_CHANNEL_IN1);
    ledc_update_duty(PWM_MODE, PWM_CHANNEL_IN2);
    vTaskDelay(pdMS_TO_TICKS(DEAD_TIME_MS));
    
    // Reverse: IN1=LOW, IN2=PWM
    uint32_t duty = duty_from_percent(duty_percent);
    ledc_set_duty(PWM_MODE, PWM_CHANNEL_IN1, 0);
    ledc_set_duty(PWM_MODE, PWM_CHANNEL_IN2, duty);
    ledc_update_duty(PWM_MODE, PWM_CHANNEL_IN1);
    ledc_update_duty(PWM_MODE, PWM_CHANNEL_IN2);
    
    ESP_LOGI(TAG, "H-bridge: REVERSE @ %d%% (duty=%lu/1023)", duty_percent, duty);
}

/**
 * @brief Set H-bridge to coast mode
 */
static void hbridge_coast(void) {
    // Coast: IN1=LOW, IN2=LOW
    ledc_set_duty(PWM_MODE, PWM_CHANNEL_IN1, 0);
    ledc_set_duty(PWM_MODE, PWM_CHANNEL_IN2, 0);
    ledc_update_duty(PWM_MODE, PWM_CHANNEL_IN1);
    ledc_update_duty(PWM_MODE, PWM_CHANNEL_IN2);
    
    ESP_LOGI(TAG, "H-bridge: COAST");
}

/**
 * @brief Main test task - cycles through Forward/Coast/Reverse/Coast at 60% duty
 */
static void test_task(void *pvParameters) {
    ESP_LOGI(TAG, "Starting H-bridge PWM test sequence");
    ESP_LOGI(TAG, "PWM: 25kHz, 10-bit resolution, 60%% duty cycle");
    ESP_LOGI(TAG, "Watch GPIO15 LED (active low) and motor behavior");
    ESP_LOGI(TAG, "LED ON = motor active @ 60%%, LED OFF = coast");
    
    while (1) {
        // === FORWARD PHASE @ 60% ===
        ESP_LOGI(TAG, "--- FORWARD @ 60%% (LED ON) ---");
        gpio_set_level(GPIO_STATUS_LED, LED_ON);
        hbridge_forward_pwm(PWM_DUTY_CYCLE_PERCENT);
        vTaskDelay(pdMS_TO_TICKS(TEST_FORWARD_TIME_MS));
        
        // === COAST PHASE 1 ===
        ESP_LOGI(TAG, "--- COAST (LED OFF) ---");
        gpio_set_level(GPIO_STATUS_LED, LED_OFF);
        hbridge_coast();
        vTaskDelay(pdMS_TO_TICKS(TEST_COAST_TIME_MS));
        
        // === REVERSE PHASE @ 60% ===
        ESP_LOGI(TAG, "--- REVERSE @ 60%% (LED ON) ---");
        gpio_set_level(GPIO_STATUS_LED, LED_ON);
        hbridge_reverse_pwm(PWM_DUTY_CYCLE_PERCENT);
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
    ESP_LOGI(TAG, "=== H-Bridge PWM Hardware Test ===");
    ESP_LOGI(TAG, "Board: Seeed Xiao ESP32C6");
    ESP_LOGI(TAG, "Test sequence: Forward @ 60%% -> Coast -> Reverse @ 60%% -> Coast");
    ESP_LOGI(TAG, "PWM: 25kHz frequency, 10-bit resolution (0-1023)");
    ESP_LOGI(TAG, "Duty cycle: 60%% = 614/1023");
    ESP_LOGI(TAG, "GPIO15 LED: Active LOW (ON=0, OFF=1)");
    ESP_LOGI(TAG, "");
    ESP_LOGI(TAG, "Hardware Connections:");
    ESP_LOGI(TAG, "  GPIO19 (IN2) -> H-bridge IN2 (PWM reverse control)");
    ESP_LOGI(TAG, "  GPIO18 (IN1) -> H-bridge IN1 (PWM forward control) - MOVED from GPIO20");
    ESP_LOGI(TAG, "  GPIO15       -> Status LED (active low)");
    ESP_LOGI(TAG, "");
    
    esp_err_t ret;
    
    // Initialize LEDC timer
    ESP_LOGI(TAG, "Initializing LEDC timer...");
    ret = init_ledc_timer();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "LEDC timer initialization FAILED: %s", esp_err_to_name(ret));
        ESP_LOGE(TAG, "System halted - check error above");
        while(1) {
            vTaskDelay(pdMS_TO_TICKS(1000));
        }
    }
    ESP_LOGI(TAG, "LEDC timer OK");
    
    // Initialize LEDC channels
    ESP_LOGI(TAG, "Initializing LEDC channels...");
    ret = init_ledc_channels();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "LEDC channel initialization FAILED: %s", esp_err_to_name(ret));
        ESP_LOGE(TAG, "System halted - check error above");
        while(1) {
            vTaskDelay(pdMS_TO_TICKS(1000));
        }
    }
    ESP_LOGI(TAG, "LEDC channels OK");
    
    // Initialize status LED
    ESP_LOGI(TAG, "Initializing status LED...");
    ret = init_status_led();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Status LED initialization FAILED: %s", esp_err_to_name(ret));
        ESP_LOGE(TAG, "System halted - check error above");
        while(1) {
            vTaskDelay(pdMS_TO_TICKS(1000));
        }
    }
    ESP_LOGI(TAG, "Status LED OK");
    
    // Ensure coast state on startup
    ESP_LOGI(TAG, "Setting initial coast state...");
    hbridge_coast();
    ESP_LOGI(TAG, "Coast state set");
    
    // Start test task
    ESP_LOGI(TAG, "Creating test task...");
    xTaskCreate(test_task, "test_task", 2048, NULL, 5, NULL);
    
    ESP_LOGI(TAG, "Test running - monitor serial output and observe hardware");
}
