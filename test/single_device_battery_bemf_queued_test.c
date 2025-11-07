/**
 * @file single_device_battery_bemf_queued_test.c
 * @brief Phase 1: Message Queue Architecture for JPL Compliance
 * 
 * Changes from baseline (single_device_battery_bemf_test.c):
 *   - Added FreeRTOS message queues for inter-task communication
 *   - Removed shared global state (current_mode, session_active, led_indication_*)
 *   - Each task owns its local data (proper task isolation)
 *   - Button → Motor: Mode changes, emergency shutdown
 *   - Battery → Motor: LVO warnings, critical shutdown
 * 
 * JPL Compliance Improvements:
 *   ✓ No shared state between tasks
 *   ✓ All inter-task communication via queues
 *   ✓ Error checking on queue operations
 *   ✓ Clear data ownership
 * 
 * Build: pio run -e single_device_battery_bemf_queued_test -t upload && pio device monitor
 */

#include <stdio.h>
#include <inttypes.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
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

static const char *TAG = "QUEUED_TEST";

// GPIO DEFINITIONS
#define GPIO_BACKEMF            0
#define GPIO_BUTTON             1
#define GPIO_BAT_VOLTAGE        2
#define GPIO_STATUS_LED         15
#define GPIO_WS2812B_ENABLE     16
#define GPIO_WS2812B_DIN        17
#define GPIO_HBRIDGE_IN2        19
#define GPIO_HBRIDGE_IN1        20
#define GPIO_BAT_ENABLE         21

// ADC CONFIGURATION
#define ADC_UNIT                ADC_UNIT_1
#define ADC_CHANNEL_BACKEMF     ADC_CHANNEL_0
#define ADC_CHANNEL_BATTERY     ADC_CHANNEL_2
#define ADC_ATTEN               ADC_ATTEN_DB_12
#define ADC_BITWIDTH            ADC_BITWIDTH_12

// BATTERY CALCULATIONS
#define RESISTOR_TOP_KOHM       3.3f
#define RESISTOR_BOTTOM_KOHM    10.0f
#define DIVIDER_RATIO           (RESISTOR_BOTTOM_KOHM / (RESISTOR_TOP_KOHM + RESISTOR_BOTTOM_KOHM))
#define VOLTAGE_MULTIPLIER      (1.0f / DIVIDER_RATIO)
#define BAT_VOLTAGE_MAX         4.2f
#define BAT_VOLTAGE_MIN         3.0f
#define LVO_CUTOFF_VOLTAGE      3.2f
#define LVO_WARNING_VOLTAGE     3.0f

// BACK-EMF
#define BACKEMF_BIAS_MV         1650

// PWM
#define PWM_FREQUENCY_HZ        25000
#define PWM_RESOLUTION          LEDC_TIMER_10_BIT
#define PWM_INTENSITY_PERCENT   60
#define PWM_TIMER               LEDC_TIMER_0
#define PWM_MODE                LEDC_LOW_SPEED_MODE
#define PWM_CHANNEL_IN1         LEDC_CHANNEL_0
#define PWM_CHANNEL_IN2         LEDC_CHANNEL_1

// LED
#define WS2812B_BRIGHTNESS      20
#define LED_INDICATION_TIME_MS  10000
#define PURPLE_BLINK_MS         200
#define LED_ON                  0
#define LED_OFF                 1

// TIMING
#define SESSION_DURATION_MS     (20 * 60 * 1000)
#define WARNING_START_MS        (19 * 60 * 1000)
#define WARNING_BLINK_MS        1000
#define BAT_READ_INTERVAL_MS    10000
#define BAT_ENABLE_SETTLE_MS    10
#define BACKEMF_SETTLE_MS       10
#define BUTTON_DEBOUNCE_MS      50
#define BUTTON_HOLD_MS          1000
#define BUTTON_COUNTDOWN_SEC    4
#define BUTTON_SAMPLE_MS        10

// QUEUES
#define BUTTON_TO_MOTOR_QUEUE_SIZE      5
#define BATTERY_TO_MOTOR_QUEUE_SIZE     3

// MODES
typedef enum {
    MODE_1HZ_50,
    MODE_1HZ_25,
    MODE_05HZ_50,
    MODE_05HZ_25,
    MODE_COUNT
} mode_t;

typedef struct {
    const char* name;
    uint32_t motor_on_ms;
    uint32_t coast_ms;
} mode_config_t;

static const mode_config_t modes[MODE_COUNT] = {
    {"1Hz@50%", 250, 250},
    {"1Hz@25%", 125, 375},
    {"0.5Hz@50%", 500, 500},
    {"0.5Hz@25%", 250, 750}
};

// MESSAGES
typedef enum {
    MSG_MODE_CHANGE,
    MSG_EMERGENCY_SHUTDOWN,
    MSG_BATTERY_WARNING,
    MSG_BATTERY_CRITICAL
} message_type_t;

typedef struct {
    message_type_t type;
    union {
        mode_t new_mode;
        struct {
            float voltage;
            int percentage;
        } battery;
    } data;
} task_message_t;

// HARDWARE HANDLES (read-only after init)
static led_strip_handle_t led_strip = NULL;
static adc_oneshot_unit_handle_t adc_handle = NULL;
static adc_cali_handle_t adc_cali_handle = NULL;
static bool adc_calibrated = false;

// MESSAGE QUEUES
static QueueHandle_t button_to_motor_queue = NULL;
static QueueHandle_t battery_to_motor_queue = NULL;

// ADC INIT (same as baseline)
static bool adc_calibration_init(adc_cali_handle_t *out_handle) {
    adc_cali_handle_t handle = NULL;
    esp_err_t ret = ESP_FAIL;
    bool calibrated = false;

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
        ESP_LOGW(TAG, "ADC calibration not available");
    }
    return calibrated;
}

static esp_err_t init_adc(void) {
    esp_err_t ret;
    
    adc_oneshot_unit_init_cfg_t init_config = {
        .unit_id = ADC_UNIT,
        .ulp_mode = ADC_ULP_MODE_DISABLE,
    };
    
    ret = adc_oneshot_new_unit(&init_config, &adc_handle);
    if (ret != ESP_OK) return ret;
    
    adc_oneshot_chan_cfg_t backemf_config = {.atten = ADC_ATTEN, .bitwidth = ADC_BITWIDTH};
    ret = adc_oneshot_config_channel(adc_handle, ADC_CHANNEL_BACKEMF, &backemf_config);
    if (ret != ESP_OK) return ret;
    
    adc_oneshot_chan_cfg_t battery_config = {.atten = ADC_ATTEN, .bitwidth = ADC_BITWIDTH};
    ret = adc_oneshot_config_channel(adc_handle, ADC_CHANNEL_BATTERY, &battery_config);
    if (ret != ESP_OK) return ret;
    
    adc_calibrated = adc_calibration_init(&adc_cali_handle);
    ESP_LOGI(TAG, "ADC initialized");
    return ESP_OK;
}

// BATTERY (same as baseline)
static esp_err_t read_battery_voltage(int *raw_voltage_mv, float *battery_voltage_v, int *battery_percentage) {
    gpio_set_level(GPIO_BAT_ENABLE, 1);
    vTaskDelay(pdMS_TO_TICKS(BAT_ENABLE_SETTLE_MS));
    
    int adc_raw = 0;
    esp_err_t ret = adc_oneshot_read(adc_handle, ADC_CHANNEL_BATTERY, &adc_raw);
    if (ret != ESP_OK) {
        gpio_set_level(GPIO_BAT_ENABLE, 0);
        return ret;
    }
    
    int voltage_mv = 0;
    if (adc_calibrated) {
        ret = adc_cali_raw_to_voltage(adc_cali_handle, adc_raw, &voltage_mv);
        if (ret != ESP_OK) voltage_mv = (adc_raw * 3300) / 4095;
    } else {
        voltage_mv = (adc_raw * 3300) / 4095;
    }
    
    gpio_set_level(GPIO_BAT_ENABLE, 0);
    
    float battery_v = (voltage_mv / 1000.0f) * VOLTAGE_MULTIPLIER;
    float percentage_f = ((battery_v - BAT_VOLTAGE_MIN) / (BAT_VOLTAGE_MAX - BAT_VOLTAGE_MIN)) * 100.0f;
    if (percentage_f < 0.0f) percentage_f = 0.0f;
    if (percentage_f > 100.0f) percentage_f = 100.0f;
    
    *raw_voltage_mv = voltage_mv;
    *battery_voltage_v = battery_v;
    *battery_percentage = (int)percentage_f;
    
    return ESP_OK;
}

static void low_battery_warning(void) {
    for (int i = 0; i < 3; i++) {
        gpio_set_level(GPIO_STATUS_LED, LED_ON);
        vTaskDelay(pdMS_TO_TICKS(200));
        gpio_set_level(GPIO_STATUS_LED, LED_OFF);
        vTaskDelay(pdMS_TO_TICKS(200));
    }
}

static bool check_low_voltage_cutout(void) {
    int raw_mv = 0;
    float battery_v = 0.0f;
    int percentage = 0;
    
    esp_err_t ret = read_battery_voltage(&raw_mv, &battery_v, &percentage);
    if (ret != ESP_OK) return true;
    
    ESP_LOGI(TAG, "LVO check: %.2fV [%d%%]", battery_v, percentage);
    
    if (battery_v < LVO_CUTOFF_VOLTAGE) {
        ESP_LOGW(TAG, "LVO TRIGGERED: %.2fV", battery_v);
        if (battery_v >= LVO_WARNING_VOLTAGE) low_battery_warning();
        vTaskDelay(pdMS_TO_TICKS(100));
        esp_sleep_enable_ext1_wakeup((1ULL << GPIO_BUTTON), ESP_EXT1_WAKEUP_ANY_LOW);
        esp_deep_sleep_start();
        return false;
    }
    return true;
}

// BACK-EMF (same as baseline)
static esp_err_t read_backemf(int *raw_mv, int16_t *actual_backemf_mv) {
    int adc_raw = 0;
    esp_err_t ret = adc_oneshot_read(adc_handle, ADC_CHANNEL_BACKEMF, &adc_raw);
    if (ret != ESP_OK) return ret;
    
    int voltage_mv = 0;
    if (adc_calibrated) {
        ret = adc_cali_raw_to_voltage(adc_cali_handle, adc_raw, &voltage_mv);
        if (ret != ESP_OK) voltage_mv = (adc_raw * 3300) / 4095;
    } else {
        voltage_mv = (adc_raw * 3300) / 4095;
    }
    
    *raw_mv = voltage_mv;
    *actual_backemf_mv = 2 * ((int16_t)voltage_mv - BACKEMF_BIAS_MV);
    return ESP_OK;
}

// MOTOR (same as baseline)
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

// LED (same as baseline)
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

// DEEP SLEEP (same as baseline)
static void enter_deep_sleep(void) {
    motor_coast();
    
    if (gpio_get_level(GPIO_BUTTON) == 0) {
        bool led_on = true;
        while (gpio_get_level(GPIO_BUTTON) == 0) {
            if (led_on) led_set_color(128, 0, 128);
            else led_clear();
            led_on = !led_on;
            vTaskDelay(pdMS_TO_TICKS(PURPLE_BLINK_MS));
        }
    }
    
    led_clear();
    gpio_set_level(GPIO_WS2812B_ENABLE, 1);
    gpio_set_level(GPIO_STATUS_LED, LED_OFF);
    
    ESP_LOGI(TAG, "Entering deep sleep");
    vTaskDelay(pdMS_TO_TICKS(100));
    
    esp_sleep_enable_ext1_wakeup((1ULL << GPIO_BUTTON), ESP_EXT1_WAKEUP_ANY_LOW);
    esp_deep_sleep_start();
}

// BUTTON TASK - sends messages to motor
static void button_task(void *pvParameters) {
    bool prev_state = true;
    uint32_t press_start = 0;
    bool press_detected = false;
    bool countdown_started = false;
    mode_t local_mode = MODE_1HZ_50;
    
    ESP_LOGI(TAG, "Button task started");
    
    while (1) {
        bool button_state = gpio_get_level(GPIO_BUTTON);
        
        if (prev_state == 1 && button_state == 0) {
            press_start = (uint32_t)(esp_timer_get_time() / 1000);
            press_detected = true;
            countdown_started = false;
        }
        
        if (button_state == 0 && press_detected) {
            uint32_t duration = (uint32_t)(esp_timer_get_time() / 1000) - press_start;
            
            if (duration >= BUTTON_HOLD_MS && !countdown_started) {
                ESP_LOGI(TAG, "Emergency shutdown...");
                countdown_started = true;
                
                bool cancelled = false;
                for (int i = BUTTON_COUNTDOWN_SEC; i > 0; i--) {
                    ESP_LOGI(TAG, "%d...", i);
                    vTaskDelay(pdMS_TO_TICKS(1000));
                    if (gpio_get_level(GPIO_BUTTON) == 1) {
                        ESP_LOGI(TAG, "Cancelled");
                        countdown_started = false;
                        press_detected = false;
                        cancelled = true;
                        break;
                    }
                }
                
                if (!cancelled) {
                    task_message_t msg = {.type = MSG_EMERGENCY_SHUTDOWN};
                    xQueueSend(button_to_motor_queue, &msg, pdMS_TO_TICKS(100));
                    vTaskDelay(pdMS_TO_TICKS(500));
                }
            }
        }
        
        if (prev_state == 0 && button_state == 1) {
            if (press_detected && !countdown_started) {
                uint32_t duration = (uint32_t)(esp_timer_get_time() / 1000) - press_start;
                
                if (duration >= BUTTON_DEBOUNCE_MS && duration < BUTTON_HOLD_MS) {
                    local_mode = (local_mode + 1) % MODE_COUNT;
                    ESP_LOGI(TAG, "Mode change: %s", modes[local_mode].name);
                    
                    task_message_t msg = {.type = MSG_MODE_CHANGE, .data.new_mode = local_mode};
                    xQueueSend(button_to_motor_queue, &msg, pdMS_TO_TICKS(100));
                }
            }
            press_detected = false;
            countdown_started = false;
        }
        
        prev_state = button_state;
        vTaskDelay(pdMS_TO_TICKS(BUTTON_SAMPLE_MS));
    }
}

// BATTERY TASK - sends messages to motor
static void battery_task(void *pvParameters) {
    uint32_t last_read_ms = (uint32_t)(esp_timer_get_time() / 1000);
    
    ESP_LOGI(TAG, "Battery task started");
    
    while (1) {
        uint32_t now = (uint32_t)(esp_timer_get_time() / 1000);
        
        if ((now - last_read_ms) >= BAT_READ_INTERVAL_MS) {
            int raw_mv = 0;
            float battery_v = 0.0f;
            int percentage = 0;
            
            if (read_battery_voltage(&raw_mv, &battery_v, &percentage) == ESP_OK) {
                ESP_LOGI(TAG, "Battery: %.2fV [%d%%]", battery_v, percentage);
                
                if (battery_v < LVO_WARNING_VOLTAGE) {
                    task_message_t msg = {
                        .type = MSG_BATTERY_CRITICAL,
                        .data.battery = {.voltage = battery_v, .percentage = percentage}
                    };
                    xQueueSend(battery_to_motor_queue, &msg, pdMS_TO_TICKS(100));
                } else if (battery_v < LVO_CUTOFF_VOLTAGE) {
                    low_battery_warning();
                    task_message_t msg = {
                        .type = MSG_BATTERY_WARNING,
                        .data.battery = {.voltage = battery_v, .percentage = percentage}
                    };
                    xQueueSend(battery_to_motor_queue, &msg, pdMS_TO_TICKS(100));
                }
            }
            last_read_ms = now;
        }
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}

// MOTOR TASK - receives messages
static void motor_task(void *pvParameters) {
    mode_t current_mode = MODE_1HZ_50;
    uint32_t session_start_ms = (uint32_t)(esp_timer_get_time() / 1000);
    uint32_t led_indication_start_ms = session_start_ms;
    bool led_indication_active = true;
    bool session_active = true;
    
    ESP_LOGI(TAG, "Motor task started: %s", modes[current_mode].name);
    
    while (session_active) {
        // Check messages
        task_message_t msg;
        if (xQueueReceive(button_to_motor_queue, &msg, 0) == pdPASS) {
            if (msg.type == MSG_MODE_CHANGE) {
                current_mode = msg.data.new_mode;
                ESP_LOGI(TAG, "Mode: %s", modes[current_mode].name);
                led_indication_active = true;
                led_indication_start_ms = (uint32_t)(esp_timer_get_time() / 1000);
            } else if (msg.type == MSG_EMERGENCY_SHUTDOWN) {
                ESP_LOGI(TAG, "Emergency shutdown");
                break;
            }
        }
        
        if (xQueueReceive(battery_to_motor_queue, &msg, 0) == pdPASS) {
            if (msg.type == MSG_BATTERY_CRITICAL) {
                ESP_LOGW(TAG, "Critical battery: %.2fV", msg.data.battery.voltage);
                break;
            }
        }
        
        uint32_t now = (uint32_t)(esp_timer_get_time() / 1000);
        uint32_t elapsed = now - session_start_ms;
        
        if (elapsed >= SESSION_DURATION_MS) {
            ESP_LOGI(TAG, "Session complete (20 min)");
            break;
        }
        
        bool sample_backemf = led_indication_active && ((now - led_indication_start_ms) < LED_INDICATION_TIME_MS);
        bool last_minute = (elapsed >= WARNING_START_MS);
        
        if (led_indication_active && ((now - led_indication_start_ms) >= LED_INDICATION_TIME_MS)) {
            led_indication_active = false;
            led_clear();
            ESP_LOGI(TAG, "LED off (battery conservation)");
        }
        
        const mode_config_t *cfg = &modes[current_mode];
        
        // FORWARD
        motor_forward(PWM_INTENSITY_PERCENT);
        if (led_indication_active || last_minute) led_set_color(255, 0, 0);
        
        if (sample_backemf) {
            if (cfg->motor_on_ms > 10) vTaskDelay(pdMS_TO_TICKS(cfg->motor_on_ms - 10));
            
            int raw_mv_drive, raw_mv_immed, raw_mv_settled;
            int16_t bemf_drive, bemf_immed, bemf_settled;
            read_backemf(&raw_mv_drive, &bemf_drive);
            vTaskDelay(pdMS_TO_TICKS(10));
            
            motor_coast();
            if (led_indication_active || last_minute) led_clear();
            
            read_backemf(&raw_mv_immed, &bemf_immed);
            vTaskDelay(pdMS_TO_TICKS(BACKEMF_SETTLE_MS));
            read_backemf(&raw_mv_settled, &bemf_settled);
            
            ESP_LOGI(TAG, "FWD: %dmV→%+dmV | %dmV→%+dmV | %dmV→%+dmV",
                     raw_mv_drive, bemf_drive, raw_mv_immed, bemf_immed, raw_mv_settled, bemf_settled);
            
            uint32_t remaining = cfg->coast_ms - BACKEMF_SETTLE_MS;
            if (remaining > 0) vTaskDelay(pdMS_TO_TICKS(remaining));
        } else {
            vTaskDelay(pdMS_TO_TICKS(cfg->motor_on_ms));
            motor_coast();
            if (led_indication_active || last_minute) led_clear();
            vTaskDelay(pdMS_TO_TICKS(cfg->coast_ms));
        }
        
        // REVERSE (same pattern)
        motor_reverse(PWM_INTENSITY_PERCENT);
        if (led_indication_active || last_minute) led_set_color(255, 0, 0);
        
        if (sample_backemf) {
            if (cfg->motor_on_ms > 10) vTaskDelay(pdMS_TO_TICKS(cfg->motor_on_ms - 10));
            
            int raw_mv_drive, raw_mv_immed, raw_mv_settled;
            int16_t bemf_drive, bemf_immed, bemf_settled;
            read_backemf(&raw_mv_drive, &bemf_drive);
            vTaskDelay(pdMS_TO_TICKS(10));
            
            motor_coast();
            if (led_indication_active || last_minute) led_clear();
            
            read_backemf(&raw_mv_immed, &bemf_immed);
            vTaskDelay(pdMS_TO_TICKS(BACKEMF_SETTLE_MS));
            read_backemf(&raw_mv_settled, &bemf_settled);
            
            ESP_LOGI(TAG, "REV: %dmV→%+dmV | %dmV→%+dmV | %dmV→%+dmV",
                     raw_mv_drive, bemf_drive, raw_mv_immed, bemf_immed, raw_mv_settled, bemf_settled);
            
            uint32_t remaining = cfg->coast_ms - BACKEMF_SETTLE_MS;
            if (remaining > 0) vTaskDelay(pdMS_TO_TICKS(remaining));
        } else {
            vTaskDelay(pdMS_TO_TICKS(cfg->motor_on_ms));
            motor_coast();
            if (led_indication_active || last_minute) led_clear();
            vTaskDelay(pdMS_TO_TICKS(cfg->coast_ms));
        }
    }
    
    motor_coast();
    vTaskDelay(pdMS_TO_TICKS(100));
    enter_deep_sleep();
    vTaskDelete(NULL);
}

// GPIO INIT
static esp_err_t init_gpio(void) {
    gpio_config_t btn = {
        .pin_bit_mask = (1ULL << GPIO_BUTTON),
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_ENABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE
    };
    ESP_ERROR_CHECK(gpio_config(&btn));
    
    gpio_config_t status_led = {
        .pin_bit_mask = (1ULL << GPIO_STATUS_LED),
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE
    };
    ESP_ERROR_CHECK(gpio_config(&status_led));
    gpio_set_level(GPIO_STATUS_LED, LED_OFF);
    
    gpio_config_t led_pwr = {
        .pin_bit_mask = (1ULL << GPIO_WS2812B_ENABLE),
        .mode = GPIO_MODE_OUTPUT
    };
    ESP_ERROR_CHECK(gpio_config(&led_pwr));
    gpio_set_level(GPIO_WS2812B_ENABLE, 0);
    
    gpio_config_t bat_enable = {
        .pin_bit_mask = (1ULL << GPIO_BAT_ENABLE),
        .mode = GPIO_MODE_OUTPUT
    };
    ESP_ERROR_CHECK(gpio_config(&bat_enable));
    gpio_set_level(GPIO_BAT_ENABLE, 0);
    
    ESP_LOGI(TAG, "GPIO initialized");
    return ESP_OK;
}

// PWM INIT
static esp_err_t init_pwm(void) {
    ledc_timer_config_t timer = {
        .speed_mode = PWM_MODE,
        .timer_num = PWM_TIMER,
        .duty_resolution = PWM_RESOLUTION,
        .freq_hz = PWM_FREQUENCY_HZ,
        .clk_cfg = LEDC_AUTO_CLK
    };
    ESP_ERROR_CHECK(ledc_timer_config(&timer));
    
    ledc_channel_config_t ch1 = {
        .gpio_num = GPIO_HBRIDGE_IN1,
        .speed_mode = PWM_MODE,
        .channel = PWM_CHANNEL_IN1,
        .timer_sel = PWM_TIMER,
        .duty = 0,
        .hpoint = 0
    };
    ESP_ERROR_CHECK(ledc_channel_config(&ch1));
    
    ledc_channel_config_t ch2 = {
        .gpio_num = GPIO_HBRIDGE_IN2,
        .speed_mode = PWM_MODE,
        .channel = PWM_CHANNEL_IN2,
        .timer_sel = PWM_TIMER,
        .duty = 0,
        .hpoint = 0
    };
    ESP_ERROR_CHECK(ledc_channel_config(&ch2));
    
    ESP_LOGI(TAG, "PWM initialized");
    return ESP_OK;
}

// LED INIT
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

// QUEUE INIT
static esp_err_t init_queues(void) {
    button_to_motor_queue = xQueueCreate(BUTTON_TO_MOTOR_QUEUE_SIZE, sizeof(task_message_t));
    if (button_to_motor_queue == NULL) {
        ESP_LOGE(TAG, "Failed to create button queue");
        return ESP_FAIL;
    }
    
    battery_to_motor_queue = xQueueCreate(BATTERY_TO_MOTOR_QUEUE_SIZE, sizeof(task_message_t));
    if (battery_to_motor_queue == NULL) {
        ESP_LOGE(TAG, "Failed to create battery queue");
        return ESP_FAIL;
    }
    
    ESP_LOGI(TAG, "Message queues initialized");
    return ESP_OK;
}

// MAIN
void app_main(void) {
    ESP_LOGI(TAG, "========================================");
    ESP_LOGI(TAG, "Phase 1: Message Queue Architecture");
    ESP_LOGI(TAG, "JPL Compliance: Task Isolation");
    ESP_LOGI(TAG, "========================================");
    
    esp_sleep_wakeup_cause_t reason = esp_sleep_get_wakeup_cause();
    ESP_LOGI(TAG, "Wake: %s", reason == ESP_SLEEP_WAKEUP_EXT1 ? "Button" : "Power on");
    
    init_gpio();
    vTaskDelay(pdMS_TO_TICKS(50));
    init_adc();
    init_led();
    init_pwm();
    motor_coast();
    
    if (init_queues() != ESP_OK) {
        ESP_LOGE(TAG, "Queue init failed!");
        while(1) vTaskDelay(pdMS_TO_TICKS(1000));
    }
    
    if (!check_low_voltage_cutout()) {
        ESP_LOGE(TAG, "LVO failed!");
        while(1) vTaskDelay(pdMS_TO_TICKS(1000));
    }
    
    ESP_LOGI(TAG, "Starting tasks...");
    
    xTaskCreate(motor_task, "motor", 4096, NULL, 5, NULL);
    xTaskCreate(button_task, "button", 2048, NULL, 4, NULL);
    xTaskCreate(battery_task, "battery", 2048, NULL, 3, NULL);
}
