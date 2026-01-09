/**
 * @file button_deepsleep_test.c
 * @brief Button, Deep Sleep, and Wake Hardware Test
 * 
 * Purpose: Verify button functionality, deep sleep mode, and wake-from-sleep
 * 
 * Hardware Test Behavior:
 *   - LED starts ON (GPIO15 = 0, active LOW)
 *   - Short button press: Toggle LED state
 *   - Button hold 5 seconds: Countdown while holding, wait for release, then sleep
 *   - Wake from deep sleep: Only on NEW button press (guaranteed)
 *   - After wake: LED illuminated (GPIO15 = 0)
 * 
 * Test Sequence:
 *   1. Power on → LED ON, waiting for button
 *   2. Press button → Toggle LED (with debounce)
 *   3. Hold button → Countdown "5... 4... 3... 2... 1..."
 *   4. After countdown → "Waiting for button release..." (blink LED)
 *   5. Release button → Sleep immediately
 *   6. Press button → Wake up, LED ON, restart cycle
 * 
 * GPIO Configuration:
 *   - GPIO1: Button input (RTC GPIO, hardware pull-up, wake source)
 *   - GPIO15: Status LED output (ACTIVE LOW - 0=ON, 1=OFF)
 * 
 * Wake Guarantee Strategy:
 *   - Wait for button release before entering sleep
 *   - Blink LED while waiting (visual feedback without serial monitor)
 *   - Configure ext1 to wake on LOW (button press) only when button is HIGH
 *   - Guarantees next wake is from NEW button press
 * 
 * Deep Sleep Power Consumption:
 *   - ESP32-C6 deep sleep: <1mA
 *   - RTC domain active for GPIO wake
 *   - Main CPU and peripherals powered down
 * 
 * Build & Run:
 *   pio run -e button_deepsleep_test -t upload && pio device monitor
 * 
 * Expected Behavior:
 *   === Button & Deep Sleep Hardware Test ===
 *   LED: ON (press button to toggle)
 *   Button pressed! LED: OFF
 *   Button pressed! LED: ON
 *   Hold button for deep sleep...
 *   5... 4... 3... 2... 1...
 *   Waiting for button release... (LED blinks)
 *   Button released! Entering deep sleep...
 *   [Device sleeps, <1mA consumption]
 *   [User presses button]
 *   ESP-ROM:esp32c6-20220919
 *   ...
 *   Wake up! Reason: EXT1 (RTC GPIO)
 *   LED: ON (press button to toggle)
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
#include "esp_sleep.h"
#include "esp_log.h"
#include "esp_timer.h"

static const char *TAG = "BTN_SLEEP_TEST";

// ========================================
// GPIO PIN DEFINITIONS
// ========================================
#define GPIO_BUTTON             1       // Button input (RTC GPIO, hardware pull-up)
#define GPIO_STATUS_LED         15      // Status LED (ACTIVE LOW)

// ========================================
// BUTTON TIMING CONFIGURATION
// ========================================
#define BUTTON_DEBOUNCE_MS      50      // Debounce time (ignore bounces <50ms)
#define COUNTDOWN_START_MS      1000    // Start countdown after 1 second of holding
#define COUNTDOWN_SECONDS       5       // Countdown duration (5 seconds)
#define BUTTON_SAMPLE_PERIOD_MS 10      // Button state sampling rate

// ========================================
// LED BLINK CONFIGURATION (while waiting for release)
// ========================================
#define LED_BLINK_PERIOD_MS     200     // Fast blink (200ms on, 200ms off)

// ========================================
// LED STATE (ACTIVE LOW)
// ========================================
#define LED_ON                  0       // GPIO low = LED on
#define LED_OFF                 1       // GPIO high = LED off

// ========================================
// GLOBAL STATE
// ========================================
static volatile bool led_state = LED_ON;    // Start with LED on

/**
 * @brief Print wake-up reason for debugging
 */
static void print_wakeup_reason(void) {
    esp_sleep_wakeup_cause_t wakeup_reason = esp_sleep_get_wakeup_cause();
    
    switch (wakeup_reason) {
        case ESP_SLEEP_WAKEUP_EXT0:
            ESP_LOGI(TAG, "Wake up! Reason: EXT0");
            break;
        case ESP_SLEEP_WAKEUP_EXT1:
            ESP_LOGI(TAG, "Wake up! Reason: EXT1 (RTC GPIO - button press)");
            break;
        case ESP_SLEEP_WAKEUP_TIMER:
            ESP_LOGI(TAG, "Wake up! Reason: Timer");
            break;
        case ESP_SLEEP_WAKEUP_TOUCHPAD:
            ESP_LOGI(TAG, "Wake up! Reason: Touchpad");
            break;
        case ESP_SLEEP_WAKEUP_ULP:
            ESP_LOGI(TAG, "Wake up! Reason: ULP program");
            break;
        case ESP_SLEEP_WAKEUP_GPIO:
            ESP_LOGI(TAG, "Wake up! Reason: GPIO wake");
            break;
        case ESP_SLEEP_WAKEUP_UART:
            ESP_LOGI(TAG, "Wake up! Reason: UART");
            break;
        default:
            ESP_LOGI(TAG, "Wake up! Reason: Power-on or reset (not from deep sleep)");
            break;
    }
}

/**
 * @brief Configure GPIO1 (button) as RTC GPIO for deep sleep wake
 * @return ESP_OK on success, error code otherwise
 */
static esp_err_t configure_button_wake(void) {
    // ESP32-C6 uses ext1 wake for RTC GPIOs
    // Configure GPIO1 as wake source (wake on LOW - button pressed)
    
    // Check if GPIO1 is RTC-capable
    if (!rtc_gpio_is_valid_gpio(GPIO_BUTTON)) {
        ESP_LOGE(TAG, "GPIO%d is not RTC-capable!", GPIO_BUTTON);
        return ESP_ERR_INVALID_ARG;
    }
    
    ESP_LOGI(TAG, "Configuring GPIO%d for RTC wake...", GPIO_BUTTON);
    
    // Configure ext1 wake source (RTC GPIO mask-based wake)
    // Wake when GPIO1 is LOW (button pressed)
    uint64_t gpio_mask = (1ULL << GPIO_BUTTON);
    esp_err_t ret = esp_sleep_enable_ext1_wakeup(gpio_mask, ESP_EXT1_WAKEUP_ANY_LOW);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to configure ext1 wake: %s", esp_err_to_name(ret));
        return ret;
    }
    
    // Configure GPIO1 for RTC use
    ret = rtc_gpio_init(GPIO_BUTTON);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to init RTC GPIO%d: %s", GPIO_BUTTON, esp_err_to_name(ret));
        return ret;
    }
    
    // Set as input
    ret = rtc_gpio_set_direction(GPIO_BUTTON, RTC_GPIO_MODE_INPUT_ONLY);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to set RTC GPIO%d direction: %s", GPIO_BUTTON, esp_err_to_name(ret));
        return ret;
    }
    
    // Enable internal pull-up (in addition to hardware pull-up)
    ret = rtc_gpio_pullup_en(GPIO_BUTTON);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to enable RTC GPIO%d pull-up: %s", GPIO_BUTTON, esp_err_to_name(ret));
        return ret;
    }
    
    // Disable pull-down
    ret = rtc_gpio_pulldown_dis(GPIO_BUTTON);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to disable RTC GPIO%d pull-down: %s", GPIO_BUTTON, esp_err_to_name(ret));
        return ret;
    }
    
    ESP_LOGI(TAG, "RTC wake configured: GPIO%d (wake on LOW)", GPIO_BUTTON);
    return ESP_OK;
}

/**
 * @brief Initialize GPIO for button and LED
 * @return ESP_OK on success, error code otherwise
 */
static esp_err_t init_gpio(void) {
    esp_err_t ret;
    
    // ========================================
    // Configure Button (GPIO1)
    // ========================================
    gpio_config_t button_config = {
        .pin_bit_mask = (1ULL << GPIO_BUTTON),
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_ENABLE,    // Internal pull-up (in addition to hardware pull-up)
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE       // No interrupts for this test (polling-based)
    };
    
    ret = gpio_config(&button_config);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Button GPIO config failed: %s", esp_err_to_name(ret));
        return ret;
    }
    
    ESP_LOGI(TAG, "Button GPIO%d configured (pull-up enabled)", GPIO_BUTTON);
    
    // ========================================
    // Configure LED (GPIO15) - ACTIVE LOW
    // ========================================
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
    
    // Set initial LED state (ON for active low)
    ret = gpio_set_level(GPIO_STATUS_LED, led_state);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to set LED initial state: %s", esp_err_to_name(ret));
        return ret;
    }
    
    ESP_LOGI(TAG, "LED GPIO%d configured (active LOW, initial state: %s)", 
             GPIO_STATUS_LED, led_state == LED_ON ? "ON" : "OFF");
    
    return ESP_OK;
}

/**
 * @brief Toggle LED state
 */
static void toggle_led(void) {
    led_state = (led_state == LED_ON) ? LED_OFF : LED_ON;
    gpio_set_level(GPIO_STATUS_LED, led_state);
    ESP_LOGI(TAG, "Button pressed! LED: %s", led_state == LED_ON ? "ON" : "OFF");
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
        
        // Blink LED while waiting for release (visual feedback without serial)
        bool blink_state = LED_OFF;
        while (gpio_get_level(GPIO_BUTTON) == 0) {
            blink_state = (blink_state == LED_ON) ? LED_OFF : LED_ON;
            gpio_set_level(GPIO_STATUS_LED, blink_state);
            vTaskDelay(pdMS_TO_TICKS(LED_BLINK_PERIOD_MS));
        }
        
        // Button released - turn LED off before sleep
        gpio_set_level(GPIO_STATUS_LED, LED_OFF);
        ESP_LOGI(TAG, "Button released!");
    }
    
    ESP_LOGI(TAG, "");
    ESP_LOGI(TAG, "===========================================");
    ESP_LOGI(TAG, "Entering ultra-low power deep sleep mode...");
    ESP_LOGI(TAG, "===========================================");
    ESP_LOGI(TAG, "Power consumption: <1mA");
    ESP_LOGI(TAG, "Press button (GPIO%d) to wake device", GPIO_BUTTON);
    ESP_LOGI(TAG, "Upon wake, LED will be ON");
    ESP_LOGI(TAG, "");
    
    // Small delay to allow serial output to flush
    vTaskDelay(pdMS_TO_TICKS(100));
    
    // Configure wake source (button must be HIGH at this point)
    configure_button_wake();
    
    // Enter deep sleep
    esp_deep_sleep_start();
    
    // This line will never execute (device sleeps)
}

/**
 * @brief Button monitoring task - polls button state and handles press/hold
 */
static void button_task(void *pvParameters) {
    bool previous_button_state = true;  // true = released (pull-up)
    bool button_state = true;
    uint32_t press_start_time = 0;
    bool press_detected = false;
    bool countdown_started = false;
    
    ESP_LOGI(TAG, "Button monitoring task started");
    ESP_LOGI(TAG, "LED: %s (press button to toggle, hold 5s for deep sleep)", 
             led_state == LED_ON ? "ON" : "OFF");
    
    while (1) {
        // Read current button state (0 = pressed, 1 = released due to pull-up)
        button_state = gpio_get_level(GPIO_BUTTON);
        
        // ========================================
        // Button Press Detection (Falling Edge)
        // ========================================
        if (previous_button_state == 1 && button_state == 0) {
            // Button just pressed (falling edge)
            press_start_time = (uint32_t)(esp_timer_get_time() / 1000);  // Convert to ms
            press_detected = true;
            countdown_started = false;
            ESP_LOGD(TAG, "Button pressed (start time: %lu ms)", press_start_time);
        }
        
        // ========================================
        // Button Hold Detection (with countdown)
        // ========================================
        if (button_state == 0 && press_detected) {
            uint32_t current_time = (uint32_t)(esp_timer_get_time() / 1000);
            uint32_t press_duration = current_time - press_start_time;
            
            // Start countdown after initial hold period
            if (press_duration >= COUNTDOWN_START_MS && !countdown_started) {
                ESP_LOGI(TAG, "");
                ESP_LOGI(TAG, "Hold button for deep sleep...");
                countdown_started = true;
                
                // Visual countdown (5 seconds)
                for (int i = COUNTDOWN_SECONDS; i > 0; i--) {
                    ESP_LOGI(TAG, "%d...", i);
                    vTaskDelay(pdMS_TO_TICKS(1000));
                    
                    // Check if button released during countdown
                    if (gpio_get_level(GPIO_BUTTON) == 1) {
                        ESP_LOGI(TAG, "Button released - cancelling deep sleep");
                        ESP_LOGI(TAG, "");
                        countdown_started = false;
                        press_detected = false;
                        goto continue_loop;
                    }
                }
                
                // Countdown complete - enter deep sleep (waits for release with blink)
                enter_deep_sleep();
                
                // Never returns from here
            }
        }
        
        // ========================================
        // Button Release Detection (Rising Edge)
        // ========================================
        if (previous_button_state == 0 && button_state == 1) {
            // Button just released (rising edge)
            if (press_detected && !countdown_started) {
                uint32_t current_time = (uint32_t)(esp_timer_get_time() / 1000);
                uint32_t press_duration = current_time - press_start_time;
                
                // Debounce check
                if (press_duration >= BUTTON_DEBOUNCE_MS) {
                    // Valid short press (not a hold) - toggle LED
                    if (press_duration < COUNTDOWN_START_MS) {
                        toggle_led();
                    }
                } else {
                    ESP_LOGD(TAG, "Button bounce detected (%lu ms) - ignored", press_duration);
                }
            }
            
            press_detected = false;
            countdown_started = false;
            ESP_LOGD(TAG, "Button released");
        }
        
continue_loop:
        previous_button_state = button_state;
        
        // Sample button state at configured rate (JPL compliant - no busy-wait)
        vTaskDelay(pdMS_TO_TICKS(BUTTON_SAMPLE_PERIOD_MS));
    }
}

/**
 * @brief Main application entry point
 */
void app_main(void) {
    ESP_LOGI(TAG, "");
    ESP_LOGI(TAG, "============================================");
    ESP_LOGI(TAG, "=== Button & Deep Sleep Hardware Test ===");
    ESP_LOGI(TAG, "============================================");
    ESP_LOGI(TAG, "Board: Seeed Xiao ESP32C6");
    ESP_LOGI(TAG, "Framework: ESP-IDF v5.5.0");
    ESP_LOGI(TAG, "Button: GPIO%d (hardware pull-up, debounced)", GPIO_BUTTON);
    ESP_LOGI(TAG, "LED: GPIO%d (active LOW - 0=ON, 1=OFF)", GPIO_STATUS_LED);
    ESP_LOGI(TAG, "");
    
    // ========================================
    // Print Wake-Up Reason
    // ========================================
    print_wakeup_reason();
    ESP_LOGI(TAG, "");
    
    // ========================================
    // Initialize GPIO
    // ========================================
    ESP_LOGI(TAG, "Initializing GPIO...");
    esp_err_t ret = init_gpio();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "GPIO initialization FAILED - halting");
        while(1) vTaskDelay(pdMS_TO_TICKS(1000));
    }
    ESP_LOGI(TAG, "GPIO initialized successfully");
    ESP_LOGI(TAG, "");
    
    // ========================================
    // Configure Deep Sleep Wake Source
    // ========================================
    ESP_LOGI(TAG, "Configuring deep sleep wake source...");
    ret = configure_button_wake();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Wake source configuration FAILED - halting");
        while(1) vTaskDelay(pdMS_TO_TICKS(1000));
    }
    ESP_LOGI(TAG, "Wake source configured successfully");
    ESP_LOGI(TAG, "");
    
    // ========================================
    // Test Instructions
    // ========================================
    ESP_LOGI(TAG, "=== Test Instructions ===");
    ESP_LOGI(TAG, "1. LED should be ON (GPIO%d = 0)", GPIO_STATUS_LED);
    ESP_LOGI(TAG, "2. Press button (GPIO%d): Toggle LED ON/OFF", GPIO_BUTTON);
    ESP_LOGI(TAG, "3. Hold button: Countdown starts after 1s, counts 5s");
    ESP_LOGI(TAG, "4. After countdown: LED blinks (release button)");
    ESP_LOGI(TAG, "5. Release button: Device enters deep sleep");
    ESP_LOGI(TAG, "6. Press button to wake: LED turns ON");
    ESP_LOGI(TAG, "");
    ESP_LOGI(TAG, "Note: LED blinks while waiting for release");
    ESP_LOGI(TAG, "      This gives visual feedback without serial monitor");
    ESP_LOGI(TAG, "");
    
    // ========================================
    // Create Button Monitoring Task
    // ========================================
    ESP_LOGI(TAG, "Starting button monitoring task...");
    xTaskCreate(button_task, "button_task", 2048, NULL, 5, NULL);
    
    ESP_LOGI(TAG, "Hardware test running!");
    ESP_LOGI(TAG, "============================================");
    ESP_LOGI(TAG, "");
}
