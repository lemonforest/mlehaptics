/**
 * @file ulp_hbridge_test.c
 * @brief ULP-coordinated H-bridge test with light sleep power management
 * 
 * Architecture:
 * - ULP (LP) core: Runs continuously, manages timing, wakes HP core as needed
 * - HP core: Light sleep most of the time, wakes for motor control, returns to sleep
 * 
 * Power efficiency:
 * - LP core: ~100µA continuous (timing and command processing)
 * - HP core: ~1-2mA light sleep, ~50mA when active for PWM
 * - Total average: ~5-10mA (vs ~50mA continuous HP core)
 * 
 * Command: pio run -e ulp_hbridge_test -t upload && pio device monitor
 * 
 * @note Follows architecture_decisions.md AD020: Power Management Strategy
 * @note JPL compliant: No busy-wait loops, all delays use FreeRTOS or hardware
 */

#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"
#include "driver/ledc.h"
#include "driver/rtc_io.h"
#include "esp_log.h"
#include "esp_sleep.h"
#include "ulp_riscv.h"
#include "ulp_riscv_gpio.h"

// Include ULP binary
extern const uint8_t ulp_main_bin_start[] asm("_binary_ulp_motor_control_bin_start");
extern const uint8_t ulp_main_bin_end[]   asm("_binary_ulp_motor_control_bin_end");

static const char *TAG = "ULP_HBRIDGE_TEST";

// GPIO Pin Definitions (from project spec)
#define GPIO_HBRIDGE_IN1        19      // Motor forward control (LEDC PWM)
#define GPIO_HBRIDGE_IN2        20      // Motor reverse control (LEDC PWM)
#define GPIO_STATUS_LED         15      // Status LED (ACTIVE LOW on Xiao ESP32C6)

// LEDC PWM Configuration
#define PWM_FREQUENCY_HZ        25000   // 25kHz (above human hearing)
#define PWM_RESOLUTION          LEDC_TIMER_10_BIT  // 10-bit (0-1023 range)
#define PWM_DUTY_CYCLE_PERCENT  60      // 60% duty cycle
#define PWM_TIMER               LEDC_TIMER_0
#define PWM_MODE                LEDC_LOW_SPEED_MODE

// LEDC Channel Assignments
#define PWM_CHANNEL_IN1         LEDC_CHANNEL_0
#define PWM_CHANNEL_IN2         LEDC_CHANNEL_1

// LED Control Macros (ACTIVE LOW)
#define LED_ON      0       // LED is ACTIVE LOW
#define LED_OFF     1       // LED is ACTIVE LOW

// Dead time (JPL compliant: FreeRTOS delay)
#define DEAD_TIME_MS            1

// ULP shared variables (defined in ulp_motor_control.c)
typedef enum {
    CMD_NONE = 0,
    CMD_FORWARD,
    CMD_REVERSE,
    CMD_COAST,
    CMD_SLEEP_HP
} motor_command_t;

extern volatile motor_command_t ulp_motor_command;
extern volatile uint32_t ulp_motor_intensity;
extern volatile uint32_t ulp_half_cycle_ms;
extern volatile uint32_t ulp_wake_count;
extern volatile uint32_t ulp_cycle_count;

/**
 * @brief Calculate LEDC duty value from percentage (0-100%)
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
    
    ESP_LOGI(TAG, "✓ LEDC timer: %dkHz, 10-bit", PWM_FREQUENCY_HZ / 1000);
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
        ESP_LOGE(TAG, "LEDC IN1 config failed: %s", esp_err_to_name(ret));
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
        ESP_LOGE(TAG, "LEDC IN2 config failed: %s", esp_err_to_name(ret));
        return ret;
    }
    
    ESP_LOGI(TAG, "✓ LEDC channels: GPIO%d(IN1), GPIO%d(IN2)", 
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
        ESP_LOGE(TAG, "Status LED config failed: %s", esp_err_to_name(ret));
        return ret;
    }
    
    gpio_set_level(GPIO_STATUS_LED, LED_OFF);
    ESP_LOGI(TAG, "✓ Status LED: GPIO%d (active low)", GPIO_STATUS_LED);
    return ESP_OK;
}

/**
 * @brief Set H-bridge to coast mode (both inputs LOW)
 */
static void hbridge_coast(void) {
    ledc_set_duty(PWM_MODE, PWM_CHANNEL_IN1, 0);
    ledc_set_duty(PWM_MODE, PWM_CHANNEL_IN2, 0);
    ledc_update_duty(PWM_MODE, PWM_CHANNEL_IN1);
    ledc_update_duty(PWM_MODE, PWM_CHANNEL_IN2);
}

/**
 * @brief Execute motor command from ULP core
 * @param cmd Motor command (FORWARD, REVERSE, COAST)
 * @param intensity PWM duty cycle percentage (0-100%)
 */
static void execute_motor_command(motor_command_t cmd, uint8_t intensity) {
    // Always coast first for safety (1ms dead time)
    hbridge_coast();
    vTaskDelay(pdMS_TO_TICKS(DEAD_TIME_MS));
    
    uint32_t duty = duty_from_percent(intensity);
    
    switch (cmd) {
        case CMD_FORWARD:
            // Forward: IN1=PWM, IN2=LOW
            ledc_set_duty(PWM_MODE, PWM_CHANNEL_IN1, duty);
            ledc_set_duty(PWM_MODE, PWM_CHANNEL_IN2, 0);
            ledc_update_duty(PWM_MODE, PWM_CHANNEL_IN1);
            ledc_update_duty(PWM_MODE, PWM_CHANNEL_IN2);
            gpio_set_level(GPIO_STATUS_LED, LED_ON);
            ESP_LOGI(TAG, "→ FORWARD @ %d%% (ULP wake #%lu)", intensity, ulp_wake_count);
            break;
            
        case CMD_REVERSE:
            // Reverse: IN1=LOW, IN2=PWM
            ledc_set_duty(PWM_MODE, PWM_CHANNEL_IN1, 0);
            ledc_set_duty(PWM_MODE, PWM_CHANNEL_IN2, duty);
            ledc_update_duty(PWM_MODE, PWM_CHANNEL_IN1);
            ledc_update_duty(PWM_MODE, PWM_CHANNEL_IN2);
            gpio_set_level(GPIO_STATUS_LED, LED_ON);
            ESP_LOGI(TAG, "← REVERSE @ %d%% (ULP wake #%lu)", intensity, ulp_wake_count);
            break;
            
        case CMD_COAST:
            // Already coasted above
            gpio_set_level(GPIO_STATUS_LED, LED_OFF);
            ESP_LOGI(TAG, "⏸ COAST (ULP wake #%lu)", ulp_wake_count);
            break;
            
        default:
            ESP_LOGW(TAG, "Unknown command: %d", cmd);
            break;
    }
}

/**
 * @brief Initialize ULP RISC-V core
 */
static esp_err_t init_ulp(void) {
    esp_err_t ret = ESP_OK;
    
    // Load ULP binary
    ret = ulp_riscv_load_binary(ulp_main_bin_start, 
                                 (ulp_main_bin_end - ulp_main_bin_start));
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "ULP binary load failed: %s", esp_err_to_name(ret));
        return ret;
    }
    
    // Initialize ULP shared variables
    ulp_motor_command = CMD_NONE;
    ulp_motor_intensity = PWM_DUTY_CYCLE_PERCENT;
    ulp_half_cycle_ms = 500;  // Default 500ms half-cycle (1Hz bilateral)
    ulp_wake_count = 0;
    ulp_cycle_count = 0;
    
    ESP_LOGI(TAG, "✓ ULP binary loaded (%d bytes)", 
             ulp_main_bin_end - ulp_main_bin_start);
    
    // Configure ULP wake source
    esp_sleep_enable_ulp_wakeup();
    
    // Start ULP
    ret = ulp_riscv_run();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "ULP start failed: %s", esp_err_to_name(ret));
        return ret;
    }
    
    ESP_LOGI(TAG, "✓ ULP core running (LP @ ~17MHz, <100µA)");
    return ESP_OK;
}

/**
 * @brief Configure light sleep for power efficiency
 * 
 * Per AD020: BLE-compatible power management with 80MHz minimum
 * Light sleep: HP core sleeps, LP core continues running
 */
static void configure_light_sleep(void) {
    // Enable automatic light sleep when idle
    esp_sleep_pd_config(ESP_PD_DOMAIN_RTC_PERIPH, ESP_PD_OPTION_ON);
    esp_sleep_pd_config(ESP_PD_DOMAIN_RTC_SLOW_MEM, ESP_PD_OPTION_ON);
    esp_sleep_pd_config(ESP_PD_DOMAIN_RTC_FAST_MEM, ESP_PD_OPTION_ON);
    
    ESP_LOGI(TAG, "✓ Light sleep configured (HP core: ~1-2mA when idle)");
    ESP_LOGI(TAG, "  ULP will wake HP core for motor control");
}

void app_main(void) {
    ESP_LOGI(TAG, "╔═══════════════════════════════════════════════════════════╗");
    ESP_LOGI(TAG, "║  ULP-Coordinated H-Bridge Test (Light Sleep Enabled)     ║");
    ESP_LOGI(TAG, "╚═══════════════════════════════════════════════════════════╝");
    ESP_LOGI(TAG, "");
    ESP_LOGI(TAG, "Power Architecture:");
    ESP_LOGI(TAG, "  • LP core: ~100µA continuous (timing + command queue)");
    ESP_LOGI(TAG, "  • HP core: Light sleep (~1-2mA) between motor commands");
    ESP_LOGI(TAG, "  • Motor active: ~50mA for PWM control");
    ESP_LOGI(TAG, "  • Average: ~5-10mA (90% power savings vs continuous HP)");
    ESP_LOGI(TAG, "");
    ESP_LOGI(TAG, "Bilateral Pattern: Forward ←→ Reverse (500ms half-cycles)");
    ESP_LOGI(TAG, "PWM: 25kHz, 10-bit, 60%% duty cycle");
    ESP_LOGI(TAG, "LED: ON during motor active, OFF during light sleep");
    ESP_LOGI(TAG, "");
    
    esp_err_t ret;
    
    // Initialize hardware peripherals
    ESP_LOGI(TAG, "Initializing hardware...");
    ret = init_ledc_timer();
    if (ret != ESP_OK) goto error;
    
    ret = init_ledc_channels();
    if (ret != ESP_OK) goto error;
    
    ret = init_status_led();
    if (ret != ESP_OK) goto error;
    
    // Ensure coast on startup
    hbridge_coast();
    ESP_LOGI(TAG, "✓ Initial coast state set");
    
    // Initialize ULP core
    ESP_LOGI(TAG, "");
    ESP_LOGI(TAG, "Initializing ULP RISC-V core...");
    ret = init_ulp();
    if (ret != ESP_OK) goto error;
    
    // Configure power management
    configure_light_sleep();
    
    ESP_LOGI(TAG, "");
    ESP_LOGI(TAG, "═══════════════════════════════════════════════════════════");
    ESP_LOGI(TAG, "✓ System Ready - ULP controlling bilateral timing");
    ESP_LOGI(TAG, "  HP core will sleep and wake automatically");
    ESP_LOGI(TAG, "  Monitor: Wake count, cycle count, power consumption");
    ESP_LOGI(TAG, "═══════════════════════════════════════════════════════════");
    ESP_LOGI(TAG, "");
    
    // Main loop: Wait for ULP commands and execute motor control
    while (1) {
        // Check for ULP command
        if (ulp_motor_command != CMD_NONE) {
            // Execute motor command
            execute_motor_command(ulp_motor_command, ulp_motor_intensity);
            
            // Clear command
            ulp_motor_command = CMD_NONE;
            
            // Log ULP statistics every 10 wakes
            if (ulp_wake_count % 10 == 0) {
                ESP_LOGI(TAG, "📊 Stats: Wakes=%lu, ULP_Cycles=%lu", 
                         ulp_wake_count, ulp_cycle_count);
            }
        }
        
        // Enter light sleep (ULP will wake us)
        // ULP continues running at ~17MHz, HP core sleeps at ~1-2mA
        ESP_LOGD(TAG, "💤 HP core → light sleep (ULP continues)");
        gpio_set_level(GPIO_STATUS_LED, LED_OFF);
        
        // Light sleep until ULP wakes us
        esp_light_sleep_start();
        
        ESP_LOGD(TAG, "⏰ HP core ← woken by ULP");
    }
    
    return;
    
error:
    ESP_LOGE(TAG, "");
    ESP_LOGE(TAG, "❌ INITIALIZATION FAILED - System halted");
    ESP_LOGE(TAG, "   Error: %s", esp_err_to_name(ret));
    while(1) {
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}
