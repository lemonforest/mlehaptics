/**
 * @file single_device_battery_bemf_test.c
 * @brief Integrated 4-Mode EMDR Test with Battery Monitoring and Back-EMF Sensing
 * 
 * Purpose: Research test combining motor patterns, battery management, and back-EMF characterization
 * 
 * Motor Modes:
 *   Mode 1: 1Hz @ 50% duty (250ms motor, 250ms coast per half-cycle)
 *   Mode 2: 1Hz @ 25% duty (125ms motor, 375ms coast per half-cycle)
 *   Mode 3: 0.5Hz @ 50% duty (500ms motor, 500ms coast per half-cycle)
 *   Mode 4: 0.5Hz @ 25% duty (250ms motor, 750ms coast per half-cycle)
 * 
 * Battery Monitoring:
 *   - Startup: LVO check (< 3.2V enters sleep with 3-blink warning if ≥ 3.0V)
 *   - Runtime: Read battery every 10 seconds
 *   - Warning: 3 blinks on GPIO15 (active LOW) if 3.0V ≤ V_BAT < 3.2V
 *   - Deep sleep: If V_BAT < 3.0V at any time
 * 
 * Back-EMF Sensing:
 *   - Sample on GPIO0 (ADC1_CH0) with resistive summing network
 *   - Three readings per pulse: during drive + immediate coast + 10ms settled
 *   - Log both forward and reverse directions
 *   - Active only during first 10 seconds of each mode
 *   - Restart sampling on mode change
 * 
 * LED Indication:
 *   - First 10 seconds: RED @ 20% brightness, blinks IN SYNC with motor
 *   - After 10s: LED off (battery conservation)
 *   - Last minute: Slow blink warning (1 second on/off)
 * 
 * Operation:
 *   - Power on: Starts in Mode 1, LED + back-EMF sampling for 10s
 *   - Button press: Cycle modes, restart 10s sampling window
 *   - Session runs for 20 minutes, then auto-sleep
 *   - Button hold 5s: Emergency shutdown (purple blink pattern)
 * 
 * GPIO Configuration:
 *   - GPIO0: Back-EMF sense (ADC1_CH0, resistive summing network)
 *   - GPIO1: Button (RTC wake source)
 *   - GPIO2: Battery voltage (ADC1_CH2, resistor divider)
 *   - GPIO15: Status LED (ACTIVE LOW - 0=ON, 1=OFF)
 *   - GPIO16: WS2812B power enable (P-MOSFET, LOW=enabled)
 *   - GPIO17: WS2812B data
 *   - GPIO19: H-bridge IN2 (reverse)
 *   - GPIO18: H-bridge IN1 (forward) - MOVED from GPIO20
 *   - GPIO21: Battery monitor enable (HIGH=enabled)
 * 
 * Build & Run:
 *   pio run -e single_device_battery_bemf_test -t upload && pio device monitor
 * 
 * Based on:
 *   - single_device_demo_test.c (motor control and LED patterns)
 *   - battery_voltage_test.c (battery monitoring and LVO)
 *   - Architecture Decision AD021 (back-EMF sensing strategy)
 * 
 * Seeed Xiao ESP32C6: ESP-IDF v5.5.0
 * Generated with assistance from Claude Sonnet 4 (Anthropic)
 */

#include <stdio.h>
#include <inttypes.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"
#include "driver/ledc.h"
#include "driver/rtc_io.h"
#include "esp_adc/adc_oneshot.h"
#include "esp_adc/adc_cali.h"
#include "esp_adc/adc_cali_scheme.h"
#include "esp_sleep.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "led_strip.h"

static const char *TAG = "BATTERY_BEMF_TEST";

// ========================================
// GPIO DEFINITIONS
// ========================================
#define GPIO_BACKEMF            0       // Back-EMF sense (ADC1_CH0)
#define GPIO_BUTTON             1       // Button (RTC wake)
#define GPIO_BAT_VOLTAGE        2       // Battery voltage (ADC1_CH2)
#define GPIO_STATUS_LED         15      // Status LED (ACTIVE LOW)
#define GPIO_WS2812B_ENABLE     16      // WS2812B power (P-MOSFET, LOW=enabled)
#define GPIO_WS2812B_DIN        17      // WS2812B data
#define GPIO_HBRIDGE_IN2        19      // H-bridge reverse
#define GPIO_HBRIDGE_IN1        20      // H-bridge forward
#define GPIO_BAT_ENABLE         21      // Battery monitor enable (HIGH=enabled)

// ========================================
// ADC CONFIGURATION
// ========================================
#define ADC_UNIT                ADC_UNIT_1
#define ADC_CHANNEL_BACKEMF     ADC_CHANNEL_0       // GPIO0 = ADC1_CH0
#define ADC_CHANNEL_BATTERY     ADC_CHANNEL_2       // GPIO2 = ADC1_CH2
#define ADC_ATTEN               ADC_ATTEN_DB_12     // 0-3.3V range
#define ADC_BITWIDTH            ADC_BITWIDTH_12     // 12-bit (0-4095)

// ========================================
// BATTERY VOLTAGE CALCULATIONS (from AD021)
// ========================================
#define RESISTOR_TOP_KOHM       3.3f    // VBAT to GPIO2
#define RESISTOR_BOTTOM_KOHM    10.0f   // GPIO2 to GND
#define DIVIDER_RATIO           (RESISTOR_BOTTOM_KOHM / (RESISTOR_TOP_KOHM + RESISTOR_BOTTOM_KOHM))
#define VOLTAGE_MULTIPLIER      (1.0f / DIVIDER_RATIO)  // 1.3301

#define BAT_VOLTAGE_MAX         4.2f    // Fully charged (100%)
#define BAT_VOLTAGE_MIN         3.0f    // Cutoff voltage (0%)
#define LVO_NO_BATTERY_THRESHOLD 0.5f   // Below this = no battery, skip LVO
#define LVO_CUTOFF_VOLTAGE      3.2f    // LVO threshold
#define LVO_WARNING_VOLTAGE     3.0f    // Visual warning threshold

// ========================================
// BACK-EMF CALCULATIONS (from AD021)
// ========================================
// Resistive summing network: V_GPIO0 = 1.65V + 0.5 × V_OUTA
// Where V_OUTA is the back-EMF from H-bridge (-3.3V to +3.3V)
// To convert back: V_OUTA = 2 × (V_GPIO0 - 1.65V)
#define BACKEMF_BIAS_MV         1650    // Center point (1.65V)

// ========================================
// PWM CONFIGURATION
// ========================================
#define PWM_FREQUENCY_HZ        25000
#define PWM_RESOLUTION          LEDC_TIMER_10_BIT
#define PWM_INTENSITY_PERCENT   60
#define PWM_TIMER               LEDC_TIMER_0
#define PWM_MODE                LEDC_LOW_SPEED_MODE
#define PWM_CHANNEL_IN1         LEDC_CHANNEL_0
#define PWM_CHANNEL_IN2         LEDC_CHANNEL_1

// ========================================
// LED CONFIGURATION
// ========================================
#define WS2812B_BRIGHTNESS      20      // 20% brightness
#define LED_INDICATION_TIME_MS  10000   // 10 seconds
#define PURPLE_BLINK_MS         200     // Purple blink rate

// ========================================
// TIMING CONFIGURATION
// ========================================
#define SESSION_DURATION_MS     (20 * 60 * 1000)    // 20 minutes
#define WARNING_START_MS        (19 * 60 * 1000)    // Last minute warning
#define WARNING_BLINK_MS        1000                // 1 second blink
#define BAT_READ_INTERVAL_MS    10000               // Read battery every 10 seconds
#define BAT_ENABLE_SETTLE_MS    10                  // Battery voltage settling time
#define BACKEMF_SETTLE_MS       10                  // Back-EMF filter settling time
#define BUTTON_DEBOUNCE_MS      50
#define BUTTON_HOLD_MS          1000                // 1 second hold before countdown
#define BUTTON_COUNTDOWN_SEC    4                   // 4 second countdown (5 total)
#define BUTTON_SAMPLE_MS        10

// ========================================
// LED STATE (ACTIVE LOW)
// ========================================
#define LED_ON                  0       // GPIO low = LED on
#define LED_OFF                 1       // GPIO high = LED off

// ========================================
// MODE DEFINITIONS
// ========================================
typedef enum {
    MODE_1HZ_50,        // Mode 1: 1Hz @ 50% duty
    MODE_1HZ_25,        // Mode 2: 1Hz @ 25% duty
    MODE_05HZ_50,       // Mode 3: 0.5Hz @ 50% duty
    MODE_05HZ_25,       // Mode 4: 0.5Hz @ 25% duty
    MODE_COUNT
} mode_t;

typedef struct {
    const char* name;
    uint32_t motor_on_ms;       // Motor active time per half-cycle
    uint32_t coast_ms;          // Coast time per half-cycle
} mode_config_t;

static const mode_config_t modes[MODE_COUNT] = {
    {"1Hz@50%", 250, 250},      // Mode 1
    {"1Hz@25%", 125, 375},      // Mode 2
    {"0.5Hz@50%", 500, 500},    // Mode 3
    {"0.5Hz@25%", 250, 750}     // Mode 4
};

// ========================================
// GLOBAL STATE
// ========================================
static led_strip_handle_t led_strip = NULL;
static adc_oneshot_unit_handle_t adc_handle = NULL;
static adc_cali_handle_t adc_cali_handle = NULL;
static bool adc_calibrated = false;

static mode_t current_mode = MODE_1HZ_50;
static volatile bool session_active = true;
static uint32_t session_start_ms = 0;
static uint32_t led_indication_start_ms = 0;
static bool led_indication_active = false;
static uint32_t last_battery_read_ms = 0;

// ========================================
// ADC INITIALIZATION
// ========================================

static bool adc_calibration_init(adc_cali_handle_t *out_handle) {
    adc_cali_handle_t handle = NULL;
    esp_err_t ret = ESP_FAIL;
    bool calibrated = false;

    ESP_LOGI(TAG, "Initializing ADC calibration...");

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

static esp_err_t init_adc(void) {
    esp_err_t ret;
    
    // Configure ADC unit
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
    
    // Configure back-EMF channel (GPIO0)
    adc_oneshot_chan_cfg_t backemf_config = {
        .atten = ADC_ATTEN,
        .bitwidth = ADC_BITWIDTH,
    };
    
    ret = adc_oneshot_config_channel(adc_handle, ADC_CHANNEL_BACKEMF, &backemf_config);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Back-EMF ADC channel config failed: %s", esp_err_to_name(ret));
        return ret;
    }
    
    ESP_LOGI(TAG, "Back-EMF channel configured (GPIO%d = ADC1_CH%d)", GPIO_BACKEMF, ADC_CHANNEL_BACKEMF);
    
    // Configure battery voltage channel (GPIO2)
    adc_oneshot_chan_cfg_t battery_config = {
        .atten = ADC_ATTEN,
        .bitwidth = ADC_BITWIDTH,
    };
    
    ret = adc_oneshot_config_channel(adc_handle, ADC_CHANNEL_BATTERY, &battery_config);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Battery ADC channel config failed: %s", esp_err_to_name(ret));
        return ret;
    }
    
    ESP_LOGI(TAG, "Battery channel configured (GPIO%d = ADC1_CH%d)", GPIO_BAT_VOLTAGE, ADC_CHANNEL_BATTERY);
    
    // Initialize calibration
    adc_calibrated = adc_calibration_init(&adc_cali_handle);
    
    return ESP_OK;
}

// ========================================
// BATTERY VOLTAGE READING
// ========================================

static esp_err_t read_battery_voltage(int *raw_voltage_mv, float *battery_voltage_v, int *battery_percentage) {
    esp_err_t ret;
    int adc_raw = 0;
    
    // Enable battery monitor
    gpio_set_level(GPIO_BAT_ENABLE, 1);
    vTaskDelay(pdMS_TO_TICKS(BAT_ENABLE_SETTLE_MS));
    
    // Read ADC
    ret = adc_oneshot_read(adc_handle, ADC_CHANNEL_BATTERY, &adc_raw);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Battery ADC read failed: %s", esp_err_to_name(ret));
        gpio_set_level(GPIO_BAT_ENABLE, 0);
        return ret;
    }
    
    // Convert to voltage (mV)
    int voltage_mv = 0;
    if (adc_calibrated) {
        ret = adc_cali_raw_to_voltage(adc_cali_handle, adc_raw, &voltage_mv);
        if (ret != ESP_OK) {
            voltage_mv = (adc_raw * 3300) / 4095;
        }
    } else {
        voltage_mv = (adc_raw * 3300) / 4095;
    }
    
    // Disable battery monitor
    gpio_set_level(GPIO_BAT_ENABLE, 0);
    
    // Calculate battery voltage
    float raw_voltage_v = voltage_mv / 1000.0f;
    float battery_v = raw_voltage_v * VOLTAGE_MULTIPLIER;
    
    // Calculate percentage
    float percentage_f = ((battery_v - BAT_VOLTAGE_MIN) / (BAT_VOLTAGE_MAX - BAT_VOLTAGE_MIN)) * 100.0f;
    if (percentage_f < 0.0f) percentage_f = 0.0f;
    if (percentage_f > 100.0f) percentage_f = 100.0f;
    
    *raw_voltage_mv = voltage_mv;
    *battery_voltage_v = battery_v;
    *battery_percentage = (int)percentage_f;
    
    return ESP_OK;
}

static void low_battery_warning(void) {
    ESP_LOGW(TAG, "Low battery warning! (3.0V ≤ V_BAT < 3.2V)");
    ESP_LOGW(TAG, "Providing visual warning (3 blinks on GPIO15)...");
    
    for (int i = 0; i < 3; i++) {
        gpio_set_level(GPIO_STATUS_LED, LED_ON);   // Active LOW
        vTaskDelay(pdMS_TO_TICKS(200));
        gpio_set_level(GPIO_STATUS_LED, LED_OFF);
        vTaskDelay(pdMS_TO_TICKS(200));
    }
}

static bool check_low_voltage_cutout(void) {
    ESP_LOGI(TAG, "Checking battery voltage for LVO...");
    
    int raw_voltage_mv = 0;
    float battery_voltage_v = 0.0f;
    int battery_percentage = 0;
    
    esp_err_t ret = read_battery_voltage(&raw_voltage_mv, &battery_voltage_v, &battery_percentage);
    
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "LVO check: Battery read failed - continuing anyway");
        return true;
    }
    
    ESP_LOGI(TAG, "LVO check: Battery voltage = %.2fV [%d%%]", battery_voltage_v, battery_percentage);

    // Check if no battery present (< 0.5V)
    if (battery_voltage_v < LVO_NO_BATTERY_THRESHOLD) {
        ESP_LOGW(TAG, "LVO check: No battery detected (%.2fV) - allowing operation", battery_voltage_v);
        ESP_LOGW(TAG, "Device can be programmed/tested without battery");
        ESP_LOGI(TAG, "LVO check: SKIPPED - no battery present");
        ESP_LOGI(TAG, "");
        return true;  // Skip LVO, continue operation
    }

    if (battery_voltage_v < LVO_CUTOFF_VOLTAGE) {
        ESP_LOGW(TAG, "");
        ESP_LOGW(TAG, "============================================");
        ESP_LOGW(TAG, "   LOW VOLTAGE CUTOUT (LVO) TRIGGERED");
        ESP_LOGW(TAG, "============================================");
        ESP_LOGW(TAG, "Battery voltage: %.2fV (threshold: %.2fV)", battery_voltage_v, LVO_CUTOFF_VOLTAGE);
        
        if (battery_voltage_v >= LVO_WARNING_VOLTAGE) {
            low_battery_warning();
        }
        
        ESP_LOGW(TAG, "Entering deep sleep to protect battery");
        ESP_LOGW(TAG, "============================================");
        vTaskDelay(pdMS_TO_TICKS(100));
        
        // Configure wake and sleep
        esp_sleep_enable_ext1_wakeup((1ULL << GPIO_BUTTON), ESP_EXT1_WAKEUP_ANY_LOW);
        esp_deep_sleep_start();
        
        return false;
    }
    
    ESP_LOGI(TAG, "LVO check: PASSED - voltage OK for operation");
    ESP_LOGI(TAG, "");
    return true;
}

// ========================================
// BACK-EMF READING
// ========================================

static esp_err_t read_backemf(int *raw_mv, int16_t *actual_backemf_mv) {
    esp_err_t ret;
    int adc_raw = 0;
    
    // Read ADC on GPIO0
    ret = adc_oneshot_read(adc_handle, ADC_CHANNEL_BACKEMF, &adc_raw);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Back-EMF ADC read failed: %s", esp_err_to_name(ret));
        return ret;
    }
    
    // Convert to voltage (mV)
    int voltage_mv = 0;
    if (adc_calibrated) {
        ret = adc_cali_raw_to_voltage(adc_cali_handle, adc_raw, &voltage_mv);
        if (ret != ESP_OK) {
            voltage_mv = (adc_raw * 3300) / 4095;
        }
    } else {
        voltage_mv = (adc_raw * 3300) / 4095;
    }
    
    // Convert ADC voltage to actual back-EMF
    // V_GPIO0 = 1.65V + 0.5 × V_OUTA
    // V_OUTA = 2 × (V_GPIO0 - 1.65V)
    int16_t backemf_mv = 2 * ((int16_t)voltage_mv - BACKEMF_BIAS_MV);
    
    *raw_mv = voltage_mv;
    *actual_backemf_mv = backemf_mv;
    
    return ESP_OK;
}

// ========================================
// MOTOR CONTROL FUNCTIONS
// ========================================

static uint32_t duty_from_percent(uint8_t percent) {
    if (percent > 100) percent = 100;
    return (1023 * percent) / 100;
}

static void motor_forward(uint8_t intensity) {
    uint32_t duty = duty_from_percent(intensity);
    ledc_set_duty(PWM_MODE, PWM_CHANNEL_IN1, duty);
    ledc_set_duty(PWM_MODE, PWM_CHANNEL_IN2, 0);
    ledc_update_duty(PWM_MODE, PWM_CHANNEL_IN1);
    ledc_update_duty(PWM_MODE, PWM_CHANNEL_IN2);
}

static void motor_reverse(uint8_t intensity) {
    uint32_t duty = duty_from_percent(intensity);
    ledc_set_duty(PWM_MODE, PWM_CHANNEL_IN1, 0);
    ledc_set_duty(PWM_MODE, PWM_CHANNEL_IN2, duty);
    ledc_update_duty(PWM_MODE, PWM_CHANNEL_IN1);
    ledc_update_duty(PWM_MODE, PWM_CHANNEL_IN2);
}

static void motor_coast(void) {
    ledc_set_duty(PWM_MODE, PWM_CHANNEL_IN1, 0);
    ledc_set_duty(PWM_MODE, PWM_CHANNEL_IN2, 0);
    ledc_update_duty(PWM_MODE, PWM_CHANNEL_IN1);
    ledc_update_duty(PWM_MODE, PWM_CHANNEL_IN2);
}

// ========================================
// LED CONTROL FUNCTIONS
// ========================================

static void apply_brightness(uint8_t *r, uint8_t *g, uint8_t *b, uint8_t brightness) {
    *r = (*r * brightness) / 100;
    *g = (*g * brightness) / 100;
    *b = (*b * brightness) / 100;
}

static void led_set_color(uint8_t r, uint8_t g, uint8_t b) {
    apply_brightness(&r, &g, &b, WS2812B_BRIGHTNESS);
    led_strip_set_pixel(led_strip, 0, r, g, b);
    led_strip_refresh(led_strip);
}

static void led_clear(void) {
    led_strip_clear(led_strip);
}

// ========================================
// DEEP SLEEP WITH PURPLE BLINK (from AD023)
// ========================================

static void enter_deep_sleep(void) {
    ESP_LOGI(TAG, "");
    ESP_LOGI(TAG, "Entering deep sleep sequence...");
    
    motor_coast();
    
    // Purple blink while waiting for button release (AD023 pattern)
    if (gpio_get_level(GPIO_BUTTON) == 0) {
        ESP_LOGI(TAG, "Waiting for button release...");
        ESP_LOGI(TAG, "(Purple blink - release when ready)");
        
        bool led_on = true;
        while (gpio_get_level(GPIO_BUTTON) == 0) {
            if (led_on) {
                led_set_color(128, 0, 128);     // Purple
            } else {
                led_clear();
            }
            led_on = !led_on;
            vTaskDelay(pdMS_TO_TICKS(PURPLE_BLINK_MS));
        }
        
        ESP_LOGI(TAG, "Button released!");
    }
    
    // Power down
    led_clear();
    gpio_set_level(GPIO_WS2812B_ENABLE, 1);     // Disable LED power
    gpio_set_level(GPIO_STATUS_LED, LED_OFF);   // Ensure status LED off
    
    ESP_LOGI(TAG, "Entering deep sleep...");
    ESP_LOGI(TAG, "Press button to wake");
    vTaskDelay(pdMS_TO_TICKS(100));
    
    // Configure wake and sleep
    esp_sleep_enable_ext1_wakeup((1ULL << GPIO_BUTTON), ESP_EXT1_WAKEUP_ANY_LOW);
    esp_deep_sleep_start();
}

// ========================================
// BUTTON TASK
// ========================================

static void button_task(void *pvParameters) {
    bool prev_state = true;
    bool button_state = true;
    uint32_t press_start = 0;
    bool press_detected = false;
    bool countdown_started = false;
    
    ESP_LOGI(TAG, "Button task started");
    
    while (1) {
        button_state = gpio_get_level(GPIO_BUTTON);
        
        // Button pressed (falling edge)
        if (prev_state == 1 && button_state == 0) {
            press_start = (uint32_t)(esp_timer_get_time() / 1000);
            press_detected = true;
            countdown_started = false;
        }
        
        // Button held (check for 5-second hold)
        if (button_state == 0 && press_detected) {
            uint32_t now = (uint32_t)(esp_timer_get_time() / 1000);
            uint32_t duration = now - press_start;
            
            if (duration >= BUTTON_HOLD_MS && !countdown_started) {
                ESP_LOGI(TAG, "");
                ESP_LOGI(TAG, "Hold detected! Emergency shutdown...");
                countdown_started = true;
                
                // Countdown
                for (int i = BUTTON_COUNTDOWN_SEC; i > 0; i--) {
                    ESP_LOGI(TAG, "%d...", i);
                    vTaskDelay(pdMS_TO_TICKS(1000));
                    
                    // Allow cancel
                    if (gpio_get_level(GPIO_BUTTON) == 1) {
                        ESP_LOGI(TAG, "Cancelled!");
                        countdown_started = false;
                        press_detected = false;
                        goto continue_loop;
                    }
                }
                
                // Shutdown
                session_active = false;
                vTaskDelay(pdMS_TO_TICKS(100));
                enter_deep_sleep();
            }
        }
        
        // Button released (rising edge)
        if (prev_state == 0 && button_state == 1) {
            if (press_detected && !countdown_started) {
                uint32_t now = (uint32_t)(esp_timer_get_time() / 1000);
                uint32_t duration = now - press_start;
                
                if (duration >= BUTTON_DEBOUNCE_MS && duration < BUTTON_HOLD_MS) {
                    // Cycle mode
                    current_mode = (current_mode + 1) % MODE_COUNT;
                    ESP_LOGI(TAG, "");
                    ESP_LOGI(TAG, "=== Mode Change ===");
                    ESP_LOGI(TAG, "New mode: %s", modes[current_mode].name);
                    ESP_LOGI(TAG, "Restarting 10-second sampling window");
                    ESP_LOGI(TAG, "");
                    
                    // Restart LED indication and back-EMF sampling
                    led_indication_active = true;
                    led_indication_start_ms = (uint32_t)(esp_timer_get_time() / 1000);
                }
            }
            
            press_detected = false;
            countdown_started = false;
        }
        
continue_loop:
        prev_state = button_state;
        vTaskDelay(pdMS_TO_TICKS(BUTTON_SAMPLE_MS));
    }
}

// ========================================
// BATTERY MONITORING TASK
// ========================================

static void battery_task(void *pvParameters) {
    ESP_LOGI(TAG, "Battery monitoring task started");
    ESP_LOGI(TAG, "Reading battery every %d seconds", BAT_READ_INTERVAL_MS / 1000);
    
    while (session_active) {
        uint32_t now = (uint32_t)(esp_timer_get_time() / 1000);
        
        // Check if it's time to read battery (every 10 seconds)
        if ((now - last_battery_read_ms) >= BAT_READ_INTERVAL_MS) {
            int raw_voltage_mv = 0;
            float battery_voltage_v = 0.0f;
            int battery_percentage = 0;
            
            esp_err_t ret = read_battery_voltage(&raw_voltage_mv, &battery_voltage_v, &battery_percentage);
            
            if (ret == ESP_OK) {
                ESP_LOGI(TAG, "Battery: %.2fV [%d%%]", battery_voltage_v, battery_percentage);
                
                // Check for low battery warning (3.0V ≤ V_BAT < 3.2V)
                if (battery_voltage_v >= LVO_WARNING_VOLTAGE && battery_voltage_v < LVO_CUTOFF_VOLTAGE) {
                    low_battery_warning();
                }
                
                // Check for critical low battery (< 3.0V)
                if (battery_voltage_v < LVO_WARNING_VOLTAGE) {
                    ESP_LOGW(TAG, "Critical battery voltage! Entering deep sleep...");
                    session_active = false;
                    vTaskDelay(pdMS_TO_TICKS(100));
                    enter_deep_sleep();
                }
            }
            
            last_battery_read_ms = now;
        }
        
        vTaskDelay(pdMS_TO_TICKS(1000));  // Check every second
    }
    
    vTaskDelete(NULL);
}

// ========================================
// MOTOR TASK WITH BACK-EMF SENSING
// ========================================

static void motor_task(void *pvParameters) {
    ESP_LOGI(TAG, "Motor task started");
    ESP_LOGI(TAG, "Mode: %s", modes[current_mode].name);
    ESP_LOGI(TAG, "");
    
    session_start_ms = (uint32_t)(esp_timer_get_time() / 1000);
    led_indication_start_ms = session_start_ms;
    led_indication_active = true;
    last_battery_read_ms = session_start_ms;
    
    while (session_active) {
        uint32_t now = (uint32_t)(esp_timer_get_time() / 1000);
        uint32_t elapsed = now - session_start_ms;
        
        // Check for session timeout (20 minutes)
        if (elapsed >= SESSION_DURATION_MS) {
            ESP_LOGI(TAG, "");
            ESP_LOGI(TAG, "Session complete! (20 minutes)");
            session_active = false;
            break;
        }
        
        // Check if we should sample back-EMF (during first 10 seconds)
        bool sample_backemf = led_indication_active && ((now - led_indication_start_ms) < LED_INDICATION_TIME_MS);
        
        // Check if we're in last minute warning period
        bool last_minute_warning = (elapsed >= WARNING_START_MS);
        
        // Turn off LED after 10 seconds (until last minute)
        if (led_indication_active && ((now - led_indication_start_ms) >= LED_INDICATION_TIME_MS)) {
            led_indication_active = false;
            led_clear();
            ESP_LOGI(TAG, "LED off - back-EMF sampling stopped (battery conservation)");
            ESP_LOGI(TAG, "");
        }
        
        // Last minute: Re-enable LED to sync with motor
        if (last_minute_warning && !led_indication_active) {
            static bool logged_warning = false;
            if (!logged_warning) {
                ESP_LOGI(TAG, "Last minute warning - LED synced with motor");
                logged_warning = true;
            }
        }
        
        // Get current mode config
        const mode_config_t *cfg = &modes[current_mode];
        
        // ========================================
        // FORWARD HALF-CYCLE
        // ========================================
        motor_forward(PWM_INTENSITY_PERCENT);
        if (led_indication_active || last_minute_warning) led_set_color(255, 0, 0);
        
        if (sample_backemf) {
            // Sample DURING motor operation (near end of drive period)
            // This helps verify the circuit is working and shows drive voltage
            if (cfg->motor_on_ms > 10) {
                vTaskDelay(pdMS_TO_TICKS(cfg->motor_on_ms - 10));
            }
            
            // Reading #1: During active drive
            int raw_mv_during_drive = 0;
            int16_t backemf_during_drive = 0;
            esp_err_t ret0 = read_backemf(&raw_mv_during_drive, &backemf_during_drive);
            
            // Finish motor drive period
            vTaskDelay(pdMS_TO_TICKS(10));
            
            // Coast and sample back-EMF
            motor_coast();
            if (led_indication_active || last_minute_warning) led_clear();
            
            // Reading #2: Immediate coast (no settling delay)
            int raw_mv_immediate = 0;
            int16_t backemf_immediate = 0;
            esp_err_t ret1 = read_backemf(&raw_mv_immediate, &backemf_immediate);
            
            // Wait for filter to settle
            vTaskDelay(pdMS_TO_TICKS(BACKEMF_SETTLE_MS));
            
            // Reading #3: After settling
            int raw_mv_settled = 0;
            int16_t backemf_settled = 0;
            esp_err_t ret2 = read_backemf(&raw_mv_settled, &backemf_settled);
            
            if (ret0 == ESP_OK && ret1 == ESP_OK && ret2 == ESP_OK) {
                ESP_LOGI(TAG, "FWD: Drive: GPIO0=%dmV → %+dmV | Coast-Immed: GPIO0=%dmV → %+dmV | Coast-Settled: GPIO0=%dmV → %+dmV",
                         raw_mv_during_drive, backemf_during_drive,
                         raw_mv_immediate, backemf_immediate,
                         raw_mv_settled, backemf_settled);
            }
            
            // Continue coasting for remainder of period
            uint32_t remaining_coast = cfg->coast_ms - BACKEMF_SETTLE_MS;
            if (remaining_coast > 0) {
                vTaskDelay(pdMS_TO_TICKS(remaining_coast));
            }
        } else {
            // No sampling - just drive and coast normally
            vTaskDelay(pdMS_TO_TICKS(cfg->motor_on_ms));
            motor_coast();
            if (led_indication_active || last_minute_warning) led_clear();
            vTaskDelay(pdMS_TO_TICKS(cfg->coast_ms));
        }
        
        // ========================================
        // REVERSE HALF-CYCLE
        // ========================================
        motor_reverse(PWM_INTENSITY_PERCENT);
        if (led_indication_active || last_minute_warning) led_set_color(255, 0, 0);
        
        if (sample_backemf) {
            // Sample DURING motor operation (near end of drive period)
            if (cfg->motor_on_ms > 10) {
                vTaskDelay(pdMS_TO_TICKS(cfg->motor_on_ms - 10));
            }
            
            // Reading #1: During active drive
            int raw_mv_during_drive = 0;
            int16_t backemf_during_drive = 0;
            esp_err_t ret0 = read_backemf(&raw_mv_during_drive, &backemf_during_drive);
            
            // Finish motor drive period
            vTaskDelay(pdMS_TO_TICKS(10));
            
            // Coast and sample back-EMF
            motor_coast();
            if (led_indication_active || last_minute_warning) led_clear();
            
            // Reading #2: Immediate coast
            int raw_mv_immediate = 0;
            int16_t backemf_immediate = 0;
            esp_err_t ret1 = read_backemf(&raw_mv_immediate, &backemf_immediate);
            
            // Wait for filter to settle
            vTaskDelay(pdMS_TO_TICKS(BACKEMF_SETTLE_MS));
            
            // Reading #3: After settling
            int raw_mv_settled = 0;
            int16_t backemf_settled = 0;
            esp_err_t ret2 = read_backemf(&raw_mv_settled, &backemf_settled);
            
            if (ret0 == ESP_OK && ret1 == ESP_OK && ret2 == ESP_OK) {
                ESP_LOGI(TAG, "REV: Drive: GPIO0=%dmV → %+dmV | Coast-Immed: GPIO0=%dmV → %+dmV | Coast-Settled: GPIO0=%dmV → %+dmV",
                         raw_mv_during_drive, backemf_during_drive,
                         raw_mv_immediate, backemf_immediate,
                         raw_mv_settled, backemf_settled);
            }
            
            // Continue coasting for remainder of period
            uint32_t remaining_coast = cfg->coast_ms - BACKEMF_SETTLE_MS;
            if (remaining_coast > 0) {
                vTaskDelay(pdMS_TO_TICKS(remaining_coast));
            }
        } else {
            // No sampling - just drive and coast normally
            vTaskDelay(pdMS_TO_TICKS(cfg->motor_on_ms));
            motor_coast();
            if (led_indication_active || last_minute_warning) led_clear();
            vTaskDelay(pdMS_TO_TICKS(cfg->coast_ms));
        }
    }
    
    // Session ended - enter sleep
    motor_coast();
    vTaskDelay(pdMS_TO_TICKS(100));
    enter_deep_sleep();
    
    vTaskDelete(NULL);
}

// ========================================
// INITIALIZATION
// ========================================

static esp_err_t init_gpio(void) {
    // Button
    gpio_config_t btn = {
        .pin_bit_mask = (1ULL << GPIO_BUTTON),
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_ENABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE
    };
    ESP_ERROR_CHECK(gpio_config(&btn));
    
    // Status LED (ACTIVE LOW)
    gpio_config_t status_led = {
        .pin_bit_mask = (1ULL << GPIO_STATUS_LED),
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE
    };
    ESP_ERROR_CHECK(gpio_config(&status_led));
    gpio_set_level(GPIO_STATUS_LED, LED_OFF);  // Start with LED off
    
    // WS2812B power
    gpio_config_t led_pwr = {
        .pin_bit_mask = (1ULL << GPIO_WS2812B_ENABLE),
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE
    };
    ESP_ERROR_CHECK(gpio_config(&led_pwr));
    gpio_set_level(GPIO_WS2812B_ENABLE, 0);     // Enable LED power (active LOW)
    
    // Battery enable
    gpio_config_t bat_enable = {
        .pin_bit_mask = (1ULL << GPIO_BAT_ENABLE),
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE
    };
    ESP_ERROR_CHECK(gpio_config(&bat_enable));
    gpio_set_level(GPIO_BAT_ENABLE, 0);  // Start disabled
    
    ESP_LOGI(TAG, "GPIO initialized");
    return ESP_OK;
}

static esp_err_t init_pwm(void) {
    // Timer
    ledc_timer_config_t timer = {
        .speed_mode = PWM_MODE,
        .timer_num = PWM_TIMER,
        .duty_resolution = PWM_RESOLUTION,
        .freq_hz = PWM_FREQUENCY_HZ,
        .clk_cfg = LEDC_AUTO_CLK
    };
    ESP_ERROR_CHECK(ledc_timer_config(&timer));
    
    // Channel IN1 (forward)
    ledc_channel_config_t ch1 = {
        .gpio_num = GPIO_HBRIDGE_IN1,
        .speed_mode = PWM_MODE,
        .channel = PWM_CHANNEL_IN1,
        .timer_sel = PWM_TIMER,
        .duty = 0,
        .hpoint = 0
    };
    ESP_ERROR_CHECK(ledc_channel_config(&ch1));
    
    // Channel IN2 (reverse)
    ledc_channel_config_t ch2 = {
        .gpio_num = GPIO_HBRIDGE_IN2,
        .speed_mode = PWM_MODE,
        .channel = PWM_CHANNEL_IN2,
        .timer_sel = PWM_TIMER,
        .duty = 0,
        .hpoint = 0
    };
    ESP_ERROR_CHECK(ledc_channel_config(&ch2));
    
    ESP_LOGI(TAG, "PWM initialized: 25kHz, 60%%");
    return ESP_OK;
}

static esp_err_t init_led(void) {
    led_strip_config_t strip_config = {
        .strip_gpio_num = GPIO_WS2812B_DIN,
        .max_leds = 1,
        .led_pixel_format = LED_PIXEL_FORMAT_GRB,
        .led_model = LED_MODEL_WS2812,
        .flags.invert_out = false,
    };
    
    led_strip_rmt_config_t rmt_config = {
        .clk_src = RMT_CLK_SRC_DEFAULT,
        .resolution_hz = 10 * 1000 * 1000,
        .flags.with_dma = false,
    };
    
    ESP_ERROR_CHECK(led_strip_new_rmt_device(&strip_config, &rmt_config, &led_strip));
    led_strip_clear(led_strip);
    
    ESP_LOGI(TAG, "LED initialized");
    return ESP_OK;
}

// ========================================
// MAIN
// ========================================

void app_main(void) {
    ESP_LOGI(TAG, "");
    ESP_LOGI(TAG, "========================================================");
    ESP_LOGI(TAG, "=== Integrated Battery + Back-EMF + Motor Test ===");
    ESP_LOGI(TAG, "========================================================");
    ESP_LOGI(TAG, "Board: Seeed Xiao ESP32C6");
    ESP_LOGI(TAG, "Session: 20 minutes");
    ESP_LOGI(TAG, "");
    
    ESP_LOGI(TAG, "Motor Modes:");
    for (int i = 0; i < MODE_COUNT; i++) {
        ESP_LOGI(TAG, "  %d. %s (%lums motor, %lums coast)", 
                 i+1, modes[i].name, modes[i].motor_on_ms, modes[i].coast_ms);
    }
    ESP_LOGI(TAG, "");
    
    ESP_LOGI(TAG, "Battery Monitoring:");
    ESP_LOGI(TAG, "  - Startup: LVO check (< 3.2V → sleep with warning)");
    ESP_LOGI(TAG, "  - Runtime: Check every 10 seconds");
    ESP_LOGI(TAG, "  - Warning: 3 blinks on GPIO15 if 3.0V ≤ V_BAT < 3.2V");
    ESP_LOGI(TAG, "  - Critical: Deep sleep if V_BAT < 3.0V");
    ESP_LOGI(TAG, "");
    
    ESP_LOGI(TAG, "Back-EMF Sensing:");
    ESP_LOGI(TAG, "  - GPIO0 (ADC1_CH0) with resistive summing network");
    ESP_LOGI(TAG, "  - Three readings per pulse: during drive + immediate coast + 10ms settled");
    ESP_LOGI(TAG, "  - Active for first 10 seconds of each mode");
    ESP_LOGI(TAG, "  - Restart on mode change (button press)");
    ESP_LOGI(TAG, "");
    
    ESP_LOGI(TAG, "Controls:");
    ESP_LOGI(TAG, "  - Press button: Cycle modes, restart 10s sampling");
    ESP_LOGI(TAG, "  - Hold 5s: Emergency shutdown");
    ESP_LOGI(TAG, "");
    
    ESP_LOGI(TAG, "LED Indication:");
    ESP_LOGI(TAG, "  - First 10s: RED blinks with motor");
    ESP_LOGI(TAG, "  - After 10s: LED off (battery saving)");
    ESP_LOGI(TAG, "  - Last minute: Slow warning blink");
    ESP_LOGI(TAG, "");
    
    // Wake reason
    esp_sleep_wakeup_cause_t reason = esp_sleep_get_wakeup_cause();
    if (reason == ESP_SLEEP_WAKEUP_EXT1) {
        ESP_LOGI(TAG, "Wake: Button press");
    } else {
        ESP_LOGI(TAG, "Wake: Power on");
    }
    ESP_LOGI(TAG, "");
    
    // Initialize hardware
    ESP_LOGI(TAG, "Initializing hardware...");
    init_gpio();
    vTaskDelay(pdMS_TO_TICKS(50));
    init_adc();
    init_led();
    init_pwm();
    motor_coast();
    
    ESP_LOGI(TAG, "Hardware ready!");
    ESP_LOGI(TAG, "");
    
    // LVO check
    if (!check_low_voltage_cutout()) {
        ESP_LOGE(TAG, "CRITICAL: LVO check failed to enter deep sleep!");
        while(1) vTaskDelay(pdMS_TO_TICKS(1000));
    }
    
    ESP_LOGI(TAG, "=== Session Start ===");
    ESP_LOGI(TAG, "");
    
    // Start tasks
    xTaskCreate(motor_task, "motor", 4096, NULL, 5, NULL);
    xTaskCreate(button_task, "button", 2048, NULL, 4, NULL);
    xTaskCreate(battery_task, "battery", 2048, NULL, 3, NULL);
}
