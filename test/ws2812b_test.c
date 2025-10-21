/**
 * @file ws2812b_test.c
 * @brief WS2812B LED Hardware Verification Test with Deep Sleep
 * 
 * Purpose: Verify WS2812B LED functionality, power control, and deep sleep integration
 * 
 * Hardware Test Behavior:
 *   - LED starts in RED state
 *   - Short button press: Cycle through colors (Red → Green → Blue → Rainbow → repeat)
 *   - GPIO15 status LED blinks with pattern indicating current color state
 *   - Button hold 5 seconds: Purple blink shutdown effect, then deep sleep
 *   - Wake from deep sleep: LED returns to RED state (NEW button press guaranteed)
 * 
 * Test Sequence:
 *   1. Power on → WS2812B RED, GPIO15 slow blink (2Hz)
 *   2. Press button → GREEN, GPIO15 medium blink (4Hz)
 *   3. Press button → BLUE, GPIO15 fast blink (8Hz)
 *   4. Press button → RAINBOW cycle, GPIO15 very fast blink (10Hz)
 *   5. Press button → RED (cycle repeats)
 *   6. Hold button 5s → Countdown, WS2812B PURPLE blink effect, wait for release
 *   7. Release button → Sleep immediately
 *   8. Press button → Wake up, WS2812B RED, restart cycle
 * 
 * GPIO Configuration:
 *   - GPIO1: Button input (RTC GPIO, hardware pull-up, wake source)
 *   - GPIO15: Status LED output (ACTIVE LOW - 0=ON, 1=OFF)
 *   - GPIO16: WS2812B power enable (P-MOSFET gate control, HIGH=enabled)
 *   - GPIO17: WS2812B DIN (data control pin)
 * 
 * Color States:
 *   - RED: RGB(255, 0, 0), GPIO15 slow blink (500ms period, 2Hz)
 *   - GREEN: RGB(0, 255, 0), GPIO15 medium blink (250ms period, 4Hz)
 *   - BLUE: RGB(0, 0, 255), GPIO15 fast blink (125ms period, 8Hz)
 *   - RAINBOW: Smooth color cycle, GPIO15 very fast blink (100ms period, 10Hz)
 *   - PURPLE (shutdown): RGB(128, 0, 128), WS2812B blinks while counting down
 * 
 * Wake Guarantee Strategy (AD023):
 *   - Wait for button release before entering sleep
 *   - Purple blink effect on WS2812B while waiting (visual feedback)
 *   - Configure ext1 to wake on LOW (button press) only when button is HIGH
 *   - Guarantees next wake is from NEW button press
 * 
 * Power Management:
 *   - GPIO16 HIGH: WS2812B powered (during active states)
 *   - GPIO16 LOW: WS2812B unpowered (during deep sleep)
 *   - Deep sleep: <1mA consumption (ESP32-C6 + unpowered WS2812B)
 * 
 * Build & Run:
 *   pio run -e ws2812b_test -t upload && pio device monitor
 * 
 * Expected Behavior:
 *   === WS2812B LED Hardware Test ===
 *   WS2812B powered ON
 *   State: RED (press button to cycle colors)
 *   Button pressed! State: GREEN
 *   Button pressed! State: BLUE
 *   Button pressed! State: RAINBOW
 *   Button pressed! State: RED
 *   Hold button for deep sleep...
 *   5... 4... 3... 2... 1...
 *   Waiting for button release... (purple blink)
 *   Button released! Entering deep sleep...
 *   [Device sleeps, <1mA consumption]
 *   [User presses button]
 *   Wake up! Reason: EXT1 (RTC GPIO)
 *   State: RED (press button to cycle colors)
 * 
 * Seeed Xiao ESP32C6: ESP-IDF v5.5.0
 * Generated with assistance from Claude Sonnet 4 (Anthropic)
 */

#include <stdio.h>
#include <inttypes.h>
#include <math.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"
#include "driver/rtc_io.h"
#include "esp_sleep.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "led_strip.h"

static const char *TAG = "WS2812B_TEST";

// ========================================
// GPIO PIN DEFINITIONS
// ========================================
#define GPIO_BUTTON             1       // Button input (RTC GPIO, hardware pull-up)
#define GPIO_STATUS_LED         15      // Status LED (ACTIVE LOW)
#define GPIO_WS2812B_ENABLE     16      // WS2812B power enable (P-MOSFET gate, HIGH=enabled)
#define GPIO_WS2812B_DIN        17      // WS2812B data input pin

// ========================================
// WS2812B CONFIGURATION
// ========================================
#define WS2812B_NUM_LEDS        1       // Single WS2812B LED
#define WS2812B_RMT_CHANNEL     0       // RMT channel for WS2812B control

// ========================================
// BUTTON TIMING CONFIGURATION
// ========================================
#define BUTTON_DEBOUNCE_MS      50      // Debounce time (ignore bounces <50ms)
#define COUNTDOWN_START_MS      1000    // Start countdown after 1 second of holding
#define COUNTDOWN_SECONDS       5       // Countdown duration (5 seconds)
#define BUTTON_SAMPLE_PERIOD_MS 10      // Button state sampling rate

// ========================================
// LED BLINK PATTERNS (status LED indicators)
// ========================================
#define RED_BLINK_PERIOD_MS     500     // Slow blink for RED state (2Hz)
#define GREEN_BLINK_PERIOD_MS   250     // Medium blink for GREEN state (4Hz)
#define BLUE_BLINK_PERIOD_MS    125     // Fast blink for BLUE state (8Hz)
#define RAINBOW_BLINK_PERIOD_MS 100     // Very fast blink for RAINBOW state (10Hz)
#define PURPLE_BLINK_PERIOD_MS  200     // Purple shutdown blink (5Hz)

// ========================================
// RAINBOW EFFECT CONFIGURATION
// ========================================
#define RAINBOW_HUE_STEP        1       // Hue increment per update (0-360 degrees)
#define RAINBOW_UPDATE_MS       20      // Rainbow color update rate (50Hz)

// ========================================
// LED STATE (ACTIVE LOW for GPIO15)
// ========================================
#define LED_ON                  0       // GPIO low = LED on
#define LED_OFF                 1       // GPIO high = LED off

// ========================================
// COLOR STATE MACHINE
// ========================================
typedef enum {
    COLOR_RED = 0,
    COLOR_GREEN,
    COLOR_BLUE,
    COLOR_RAINBOW,
    COLOR_PURPLE,       // Special state for shutdown
    COLOR_COUNT         // Total number of color states (excluding PURPLE)
} color_state_t;

// ========================================
// GLOBAL STATE
// ========================================
static led_strip_handle_t led_strip = NULL;
static color_state_t current_color = COLOR_RED;
static bool status_led_state = LED_ON;
static uint16_t rainbow_hue = 0;  // 0-360 degrees

/**
 * @brief Convert HSV to RGB
 * @param h Hue (0-360 degrees)
 * @param s Saturation (0-100%)
 * @param v Value/Brightness (0-100%)
 * @param r Output red (0-255)
 * @param g Output green (0-255)
 * @param b Output blue (0-255)
 */
static void hsv_to_rgb(uint16_t h, uint8_t s, uint8_t v, uint8_t *r, uint8_t *g, uint8_t *b) {
    // Normalize inputs
    float hue = (h % 360) / 60.0f;
    float sat = s / 100.0f;
    float val = v / 100.0f;
    
    int hi = (int)hue % 6;
    float f = hue - (int)hue;
    
    float p = val * (1.0f - sat);
    float q = val * (1.0f - f * sat);
    float t = val * (1.0f - (1.0f - f) * sat);
    
    float rf, gf, bf;
    
    switch (hi) {
        case 0: rf = val; gf = t;   bf = p;   break;
        case 1: rf = q;   gf = val; bf = p;   break;
        case 2: rf = p;   gf = val; bf = t;   break;
        case 3: rf = p;   gf = q;   bf = val; break;
        case 4: rf = t;   gf = p;   bf = val; break;
        case 5: rf = val; gf = p;   bf = q;   break;
        default: rf = 0; gf = 0; bf = 0; break;
    }
    
    *r = (uint8_t)(rf * 255.0f);
    *g = (uint8_t)(gf * 255.0f);
    *b = (uint8_t)(bf * 255.0f);
}

/**
 * @brief Get status LED blink period for current color state
 * @return Blink period in milliseconds
 */
static uint32_t get_status_blink_period(void) {
    switch (current_color) {
        case COLOR_RED:     return RED_BLINK_PERIOD_MS;
        case COLOR_GREEN:   return GREEN_BLINK_PERIOD_MS;
        case COLOR_BLUE:    return BLUE_BLINK_PERIOD_MS;
        case COLOR_RAINBOW: return RAINBOW_BLINK_PERIOD_MS;
        case COLOR_PURPLE:  return PURPLE_BLINK_PERIOD_MS;
        default:            return RED_BLINK_PERIOD_MS;
    }
}

/**
 * @brief Get color state name as string
 * @param state Color state
 * @return String representation
 */
static const char* get_color_name(color_state_t state) {
    switch (state) {
        case COLOR_RED:     return "RED";
        case COLOR_GREEN:   return "GREEN";
        case COLOR_BLUE:    return "BLUE";
        case COLOR_RAINBOW: return "RAINBOW";
        case COLOR_PURPLE:  return "PURPLE";
        default:            return "UNKNOWN";
    }
}

/**
 * @brief Update WS2812B LED with current color
 * @return ESP_OK on success
 */
static esp_err_t update_ws2812b(void) {
    if (led_strip == NULL) {
        return ESP_ERR_INVALID_STATE;
    }
    
    uint8_t r, g, b;
    
    switch (current_color) {
        case COLOR_RED:
            r = 255; g = 0; b = 0;
            break;
        case COLOR_GREEN:
            r = 0; g = 255; b = 0;
            break;
        case COLOR_BLUE:
            r = 0; g = 0; b = 255;
            break;
        case COLOR_PURPLE:
            r = 128; g = 0; b = 128;
            break;
        case COLOR_RAINBOW:
            // Rainbow handled in separate task
            return ESP_OK;
        default:
            r = 0; g = 0; b = 0;
            break;
    }
    
    esp_err_t ret = led_strip_set_pixel(led_strip, 0, r, g, b);
    if (ret != ESP_OK) {
        return ret;
    }
    
    return led_strip_refresh(led_strip);
}

/**
 * @brief Print wake-up reason for debugging
 */
static void print_wakeup_reason(void) {
    esp_sleep_wakeup_cause_t wakeup_reason = esp_sleep_get_wakeup_cause();
    
    switch (wakeup_reason) {
        case ESP_SLEEP_WAKEUP_EXT1:
            ESP_LOGI(TAG, "Wake up! Reason: EXT1 (RTC GPIO - button press)");
            break;
        case ESP_SLEEP_WAKEUP_UNDEFINED:
            ESP_LOGI(TAG, "Wake up! Reason: Power-on or reset (not from deep sleep)");
            break;
        default:
            ESP_LOGI(TAG, "Wake up! Reason: %d", wakeup_reason);
            break;
    }
}

/**
 * @brief Configure GPIO1 (button) as RTC GPIO for deep sleep wake
 * @return ESP_OK on success, error code otherwise
 */
static esp_err_t configure_button_wake(void) {
    // Check if GPIO1 is RTC-capable
    if (!rtc_gpio_is_valid_gpio(GPIO_BUTTON)) {
        ESP_LOGE(TAG, "GPIO%d is not RTC-capable!", GPIO_BUTTON);
        return ESP_ERR_INVALID_ARG;
    }
    
    ESP_LOGI(TAG, "Configuring GPIO%d for RTC wake...", GPIO_BUTTON);
    
    // Configure ext1 wake source (wake when GPIO1 is LOW - button pressed)
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
    
    ret = rtc_gpio_set_direction(GPIO_BUTTON, RTC_GPIO_MODE_INPUT_ONLY);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to set RTC GPIO%d direction: %s", GPIO_BUTTON, esp_err_to_name(ret));
        return ret;
    }
    
    ret = rtc_gpio_pullup_en(GPIO_BUTTON);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to enable RTC GPIO%d pull-up: %s", GPIO_BUTTON, esp_err_to_name(ret));
        return ret;
    }
    
    ret = rtc_gpio_pulldown_dis(GPIO_BUTTON);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to disable RTC GPIO%d pull-down: %s", GPIO_BUTTON, esp_err_to_name(ret));
        return ret;
    }
    
    ESP_LOGI(TAG, "RTC wake configured: GPIO%d (wake on LOW)", GPIO_BUTTON);
    return ESP_OK;
}

/**
 * @brief Initialize GPIO for button, status LED, and WS2812B power control
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
    
    // ========================================
    // Configure Status LED (GPIO15) - ACTIVE LOW
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
        ESP_LOGE(TAG, "Status LED GPIO config failed: %s", esp_err_to_name(ret));
        return ret;
    }
    
    ret = gpio_set_level(GPIO_STATUS_LED, status_led_state);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to set status LED initial state: %s", esp_err_to_name(ret));
        return ret;
    }
    
    ESP_LOGI(TAG, "Status LED GPIO%d configured (active LOW)", GPIO_STATUS_LED);
    
    // ========================================
    // Configure WS2812B Power Enable (GPIO16)
    // ========================================
    gpio_config_t ws2812b_enable_config = {
        .pin_bit_mask = (1ULL << GPIO_WS2812B_ENABLE),
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE
    };
    
    ret = gpio_config(&ws2812b_enable_config);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "WS2812B enable GPIO config failed: %s", esp_err_to_name(ret));
        return ret;
    }
    
    // Enable WS2812B power (HIGH = P-MOSFET conducts)
    ret = gpio_set_level(GPIO_WS2812B_ENABLE, 1);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to enable WS2812B power: %s", esp_err_to_name(ret));
        return ret;
    }
    
    ESP_LOGI(TAG, "WS2812B power enable GPIO%d configured (HIGH=enabled)", GPIO_WS2812B_ENABLE);
    
    return ESP_OK;
}

/**
 * @brief Initialize WS2812B LED strip
 * @return ESP_OK on success, error code otherwise
 */
static esp_err_t init_ws2812b(void) {
    ESP_LOGI(TAG, "Initializing WS2812B LED strip...");
    
    // Configure LED strip
    led_strip_config_t strip_config = {
        .strip_gpio_num = GPIO_WS2812B_DIN,
        .max_leds = WS2812B_NUM_LEDS,
        .led_pixel_format = LED_PIXEL_FORMAT_GRB,  // WS2812B uses GRB format
        .led_model = LED_MODEL_WS2812,
        .flags.invert_out = false,
    };
    
    // Configure RMT backend
    led_strip_rmt_config_t rmt_config = {
        .clk_src = RMT_CLK_SRC_DEFAULT,
        .resolution_hz = 10 * 1000 * 1000,  // 10MHz resolution
        .flags.with_dma = false,
    };
    
    esp_err_t ret = led_strip_new_rmt_device(&strip_config, &rmt_config, &led_strip);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to create LED strip: %s", esp_err_to_name(ret));
        return ret;
    }
    
    // Clear LED strip (all off)
    ret = led_strip_clear(led_strip);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to clear LED strip: %s", esp_err_to_name(ret));
        return ret;
    }
    
    ESP_LOGI(TAG, "WS2812B LED strip initialized successfully");
    return ESP_OK;
}

/**
 * @brief Cycle to next color state
 */
static void cycle_color(void) {
    // Cycle through colors (skip PURPLE - it's for shutdown only)
    current_color = (current_color + 1) % (COLOR_COUNT - 1);  // -1 to exclude PURPLE
    
    // Reset rainbow hue when entering rainbow state
    if (current_color == COLOR_RAINBOW) {
        rainbow_hue = 0;
    }
    
    // Update WS2812B (if not rainbow - that's handled by rainbow task)
    if (current_color != COLOR_RAINBOW) {
        update_ws2812b();
    }
    
    ESP_LOGI(TAG, "Button pressed! State: %s", get_color_name(current_color));
}

/**
 * @brief Enter deep sleep mode with purple blink effect (waits for button release)
 * @return Does not return (device sleeps)
 */
static void enter_deep_sleep(void) {
    ESP_LOGI(TAG, "");
    
    // Set purple color for shutdown effect
    current_color = COLOR_PURPLE;
    update_ws2812b();
    
    // Check if button is still held
    if (gpio_get_level(GPIO_BUTTON) == 0) {
        ESP_LOGI(TAG, "Waiting for button release...");
        ESP_LOGI(TAG, "(Purple blink effect - release button when ready)");
        
        // Purple blink effect while waiting for release
        bool ws2812b_on = true;
        while (gpio_get_level(GPIO_BUTTON) == 0) {
            if (ws2812b_on) {
                led_strip_set_pixel(led_strip, 0, 128, 0, 128);  // Purple
            } else {
                led_strip_set_pixel(led_strip, 0, 0, 0, 0);      // Off
            }
            led_strip_refresh(led_strip);
            ws2812b_on = !ws2812b_on;
            
            vTaskDelay(pdMS_TO_TICKS(PURPLE_BLINK_PERIOD_MS));
        }
        
        ESP_LOGI(TAG, "Button released!");
    }
    
    // Turn off WS2812B before sleep
    led_strip_clear(led_strip);
    gpio_set_level(GPIO_STATUS_LED, LED_OFF);
    gpio_set_level(GPIO_WS2812B_ENABLE, 0);  // Disable WS2812B power
    
    ESP_LOGI(TAG, "");
    ESP_LOGI(TAG, "===========================================");
    ESP_LOGI(TAG, "Entering ultra-low power deep sleep mode...");
    ESP_LOGI(TAG, "===========================================");
    ESP_LOGI(TAG, "Power consumption: <1mA");
    ESP_LOGI(TAG, "WS2812B powered OFF");
    ESP_LOGI(TAG, "Press button (GPIO%d) to wake device", GPIO_BUTTON);
    ESP_LOGI(TAG, "Upon wake, WS2812B will show RED");
    ESP_LOGI(TAG, "");
    
    // Small delay to allow serial output to flush
    vTaskDelay(pdMS_TO_TICKS(100));
    
    // Configure wake source
    configure_button_wake();
    
    // Enter deep sleep
    esp_deep_sleep_start();
    
    // Never returns
}

/**
 * @brief Rainbow effect task - smoothly cycles through colors
 */
static void rainbow_task(void *pvParameters) {
    ESP_LOGI(TAG, "Rainbow effect task started");
    
    while (1) {
        if (current_color == COLOR_RAINBOW) {
            // Calculate RGB from current hue
            uint8_t r, g, b;
            hsv_to_rgb(rainbow_hue, 100, 100, &r, &g, &b);
            
            // Update WS2812B
            led_strip_set_pixel(led_strip, 0, r, g, b);
            led_strip_refresh(led_strip);
            
            // Increment hue for next iteration
            rainbow_hue = (rainbow_hue + RAINBOW_HUE_STEP) % 360;
        }
        
        vTaskDelay(pdMS_TO_TICKS(RAINBOW_UPDATE_MS));
    }
}

/**
 * @brief Status LED blink task - indicates current color state
 */
static void status_led_task(void *pvParameters) {
    ESP_LOGI(TAG, "Status LED blink task started");
    
    while (1) {
        // Get blink period for current state
        uint32_t blink_period = get_status_blink_period();
        
        // Toggle status LED
        status_led_state = (status_led_state == LED_ON) ? LED_OFF : LED_ON;
        gpio_set_level(GPIO_STATUS_LED, status_led_state);
        
        // Wait half period (for 50% duty cycle)
        vTaskDelay(pdMS_TO_TICKS(blink_period / 2));
    }
}

/**
 * @brief Button monitoring task - polls button state and handles press/hold
 */
static void button_task(void *pvParameters) {
    bool previous_button_state = true;
    bool button_state = true;
    uint32_t press_start_time = 0;
    bool press_detected = false;
    bool countdown_started = false;
    
    ESP_LOGI(TAG, "Button monitoring task started");
    ESP_LOGI(TAG, "State: %s (press button to cycle colors)", get_color_name(current_color));
    
    while (1) {
        button_state = gpio_get_level(GPIO_BUTTON);
        
        // Button Press Detection (Falling Edge)
        if (previous_button_state == 1 && button_state == 0) {
            press_start_time = (uint32_t)(esp_timer_get_time() / 1000);
            press_detected = true;
            countdown_started = false;
        }
        
        // Button Hold Detection (with countdown)
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
                
                // Countdown complete - enter deep sleep
                enter_deep_sleep();
            }
        }
        
        // Button Release Detection (Rising Edge)
        if (previous_button_state == 0 && button_state == 1) {
            if (press_detected && !countdown_started) {
                uint32_t current_time = (uint32_t)(esp_timer_get_time() / 1000);
                uint32_t press_duration = current_time - press_start_time;
                
                if (press_duration >= BUTTON_DEBOUNCE_MS && press_duration < COUNTDOWN_START_MS) {
                    cycle_color();
                }
            }
            
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
    ESP_LOGI(TAG, "=== WS2812B LED Hardware Verification Test ===");
    ESP_LOGI(TAG, "================================================");
    ESP_LOGI(TAG, "Board: Seeed Xiao ESP32C6");
    ESP_LOGI(TAG, "Framework: ESP-IDF v5.5.0");
    ESP_LOGI(TAG, "Button: GPIO%d (hardware pull-up)", GPIO_BUTTON);
    ESP_LOGI(TAG, "Status LED: GPIO%d (active LOW - 0=ON, 1=OFF)", GPIO_STATUS_LED);
    ESP_LOGI(TAG, "WS2812B Enable: GPIO%d (HIGH=powered)", GPIO_WS2812B_ENABLE);
    ESP_LOGI(TAG, "WS2812B DIN: GPIO%d (data control)", GPIO_WS2812B_DIN);
    ESP_LOGI(TAG, "");
    
    // Print Wake-Up Reason
    print_wakeup_reason();
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
    
    // Small delay for WS2812B power stabilization
    vTaskDelay(pdMS_TO_TICKS(50));
    
    // Initialize WS2812B
    ret = init_ws2812b();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "WS2812B initialization FAILED - halting");
        while(1) vTaskDelay(pdMS_TO_TICKS(1000));
    }
    ESP_LOGI(TAG, "WS2812B powered ON");
    ESP_LOGI(TAG, "");
    
    // Set initial color (RED)
    current_color = COLOR_RED;
    update_ws2812b();
    
    // Configure Deep Sleep Wake Source
    ESP_LOGI(TAG, "Configuring deep sleep wake source...");
    ret = configure_button_wake();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Wake source configuration FAILED - halting");
        while(1) vTaskDelay(pdMS_TO_TICKS(1000));
    }
    ESP_LOGI(TAG, "Wake source configured successfully");
    ESP_LOGI(TAG, "");
    
    // Test Instructions
    ESP_LOGI(TAG, "=== Test Instructions ===");
    ESP_LOGI(TAG, "1. WS2812B should show RED");
    ESP_LOGI(TAG, "2. GPIO%d blinks slowly (2Hz) for RED state", GPIO_STATUS_LED);
    ESP_LOGI(TAG, "3. Press button: Cycle through colors");
    ESP_LOGI(TAG, "   - RED → GREEN (GPIO%d blinks 4Hz)", GPIO_STATUS_LED);
    ESP_LOGI(TAG, "   - GREEN → BLUE (GPIO%d blinks 8Hz)", GPIO_STATUS_LED);
    ESP_LOGI(TAG, "   - BLUE → RAINBOW (GPIO%d blinks 10Hz)", GPIO_STATUS_LED);
    ESP_LOGI(TAG, "   - RAINBOW → RED (cycle repeats)");
    ESP_LOGI(TAG, "4. Hold button 5s: Countdown + purple blink");
    ESP_LOGI(TAG, "5. Release button: Deep sleep (<1mA)");
    ESP_LOGI(TAG, "6. Press button to wake: Returns to RED");
    ESP_LOGI(TAG, "");
    
    // Create Tasks
    ESP_LOGI(TAG, "Starting tasks...");
    xTaskCreate(button_task, "button_task", 2048, NULL, 5, NULL);
    xTaskCreate(rainbow_task, "rainbow_task", 2048, NULL, 4, NULL);
    xTaskCreate(status_led_task, "status_led_task", 2048, NULL, 3, NULL);
    
    ESP_LOGI(TAG, "Hardware test running!");
    ESP_LOGI(TAG, "State: %s (press button to cycle colors)", get_color_name(current_color));
    ESP_LOGI(TAG, "================================================");
    ESP_LOGI(TAG, "");
}
