/**
 * @file single_device_ble_gatt_test.c
 * @brief Phase A: BLE GATT Server Integration
 *
 * Based on: single_device_battery_bemf_queued_test.c (Phase 1)
 *
 * New Features:
 *   - BLE GATT server with advertising control
 *   - 3-tier button hold detection (short/BLE re-enable/shutdown)
 *   - Status LED feedback for button actions
 *   - BLE advertising timeout (5 minutes)
 *   - Button-triggered BLE re-enable
 *
 * Build: pio run -e single_device_ble_gatt_test -t upload && pio device monitor
 */

#include <stdio.h>
#include <inttypes.h>
#include <string.h>
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
#include "esp_pm.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "esp_task_wdt.h"
#include "led_strip.h"

// NimBLE includes
#include "nvs_flash.h"
#include "nvs.h"
#include "esp_crc.h"
#include "nimble/nimble_port.h"
#include "nimble/nimble_port_freertos.h"
#include "host/ble_hs.h"
#include "host/util/util.h"
#include "host/ble_uuid.h"
#include "host/ble_gatt.h"
#include "services/gap/ble_svc_gap.h"
#include "services/gatt/ble_svc_gatt.h"
#include "store/config/ble_store_config.h"
#include "os/os_mbuf.h"

static const char *TAG = "BLE_GATT_TEST";

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
#define LVO_NO_BATTERY_THRESHOLD 0.5f
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
#define BUTTON_HOLD_DETECT_MS       1000   // Detect hold at 1s
#define BUTTON_BLE_REENABLE_MS      2000   // BLE re-enable window ends at 2s
#define BUTTON_SHUTDOWN_THRESHOLD_MS 2000  // Shutdown countdown starts at 2s
#define BUTTON_COUNTDOWN_SEC        3      // Countdown duration (2s + 3s = 5s total)
#define BUTTON_SAMPLE_MS            10
#define BUTTON_NVS_CLEAR_MS         15000  // 15s hold for NVS factory reset
#define BUTTON_NVS_CLEAR_WINDOW_MS  30000  // Must be within first 30s of boot

// QUEUES
#define BUTTON_TO_MOTOR_QUEUE_SIZE      5
#define BATTERY_TO_MOTOR_QUEUE_SIZE     3
#define BUTTON_TO_BLE_QUEUE_SIZE        3

// MODES
typedef enum {
    MODE_1HZ_50,
    MODE_1HZ_25,
    MODE_05HZ_50,
    MODE_05HZ_25,
    MODE_CUSTOM,      // Mode 5: Custom frequency/duty (BLE configurable)
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
    {"0.5Hz@25%", 250, 750},
    {"Custom", 250, 250}    // Default to 1Hz@50%, customizable via BLE
};

// BUTTON STATE MACHINE
typedef enum {
    BTN_STATE_IDLE,
    BTN_STATE_DEBOUNCE,
    BTN_STATE_PRESSED,
    BTN_STATE_HOLD_DETECT,        // 1s-2s window for BLE re-enable
    BTN_STATE_SHUTDOWN_HOLD,      // 2s+ continued hold
    BTN_STATE_COUNTDOWN,
    BTN_STATE_SHUTDOWN,
    BTN_STATE_SHUTDOWN_SENT       // Terminal state - waiting for deep sleep
} button_state_t;

// BLE STATE MACHINE
typedef enum {
    BLE_STATE_IDLE,               // Not advertising, no client
    BLE_STATE_ADVERTISING,        // Advertising active, waiting for client
    BLE_STATE_CONNECTED,          // Client connected
    BLE_STATE_SHUTDOWN            // Cleanup and exit
} ble_state_t;

// MOTOR STATE MACHINE
typedef enum {
    MOTOR_STATE_CHECK_MESSAGES,           // Check queues, handle mode changes

    // FORWARD phase
    MOTOR_STATE_FORWARD_ACTIVE,           // Motor forward, PWM active
    MOTOR_STATE_FORWARD_COAST_REMAINING,  // Coast remaining time

    // Shared back-EMF states (used by both FORWARD and REVERSE)
    MOTOR_STATE_BEMF_IMMEDIATE,           // Coast + immediate back-EMF sample
    MOTOR_STATE_COAST_SETTLE,             // Wait settle time + settled sample

    // REVERSE phase
    MOTOR_STATE_REVERSE_ACTIVE,           // Motor reverse, PWM active
    MOTOR_STATE_REVERSE_COAST_REMAINING,  // Coast remaining time

    MOTOR_STATE_SHUTDOWN                  // Final cleanup before task exit
} motor_state_t;

// MESSAGES
typedef enum {
    MSG_MODE_CHANGE,
    MSG_EMERGENCY_SHUTDOWN,
    MSG_BLE_REENABLE,             // NEW: Re-enable BLE advertising
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
static QueueHandle_t button_to_ble_queue = NULL;

// BLE ADVERTISING STATE
typedef struct {
    bool advertising_active;
    bool client_connected;
    uint32_t advertising_start_ms;
    uint32_t advertising_timeout_ms;  // 300000ms = 5 minutes
} ble_advertising_state_t;

static ble_advertising_state_t ble_adv_state = {
    .advertising_active = false,
    .client_connected = false,
    .advertising_start_ms = 0,
    .advertising_timeout_ms = 300000
};

// NVS CONFIGURATION FOR MODE 5 PERSISTENCE
#define NVS_NAMESPACE            "mode5_cfg"
#define NVS_KEY_SIGNATURE        "sig"
#define NVS_KEY_FREQUENCY        "freq"
#define NVS_KEY_DUTY             "duty"
#define NVS_KEY_LED_ENABLE       "led_en"
#define NVS_KEY_LED_COLOR        "led_col"
#define NVS_KEY_LED_BRIGHTNESS   "led_bri"
#define NVS_KEY_PWM_INTENSITY    "pwm_int"

// BLE CONFIGURATION
#define BLE_DEVICE_NAME          "EMDR_Pulser"
#define BLE_ADV_TIMEOUT_MS       300000  // 5 minutes

// BLE UUIDs - Custom 128-bit base UUID: a1b2c3d4-e5f6-7890-a1b2-c3d4e5f67890
// Service UUID: a1b2c3d4-e5f6-7890-a1b2-c3d4e5f60000
// Characteristics use 16-bit offsets from base
//
// UUID Format: Base is {0x90, 0x78, 0xf6, 0xe5, 0xd4, 0xc3, 0xb2, 0xa1,
//                        0x90, 0x78, 0xf6, 0xe5, 0xd4, 0xc3, [LSB], [MSB]}
// Last 2 bytes are 16-bit little-endian offset

// Service and characteristic UUIDs as static const
// Base UUID: a1b2c3d4-e5f6-7890-a1b2-c3d4e5f6xxxx
// Service and characteristics use offsets in last 2 bytes
// NOTE: BLE_UUID128_INIT expects bytes in REVERSE order (little-endian for all fields)
static const ble_uuid128_t uuid_emdr_service = BLE_UUID128_INIT(
    0x00, 0x00, 0xf6, 0xe5, 0xd4, 0xc3, 0xb2, 0xa1,
    0x90, 0x78, 0xf6, 0xe5, 0xd4, 0xc3, 0xb2, 0xa1);

static const ble_uuid128_t uuid_char_mode = BLE_UUID128_INIT(
    0x01, 0x00, 0xf6, 0xe5, 0xd4, 0xc3, 0xb2, 0xa1,
    0x90, 0x78, 0xf6, 0xe5, 0xd4, 0xc3, 0xb2, 0xa1);

static const ble_uuid128_t uuid_char_custom_freq = BLE_UUID128_INIT(
    0x02, 0x00, 0xf6, 0xe5, 0xd4, 0xc3, 0xb2, 0xa1,
    0x90, 0x78, 0xf6, 0xe5, 0xd4, 0xc3, 0xb2, 0xa1);

static const ble_uuid128_t uuid_char_custom_duty = BLE_UUID128_INIT(
    0x03, 0x00, 0xf6, 0xe5, 0xd4, 0xc3, 0xb2, 0xa1,
    0x90, 0x78, 0xf6, 0xe5, 0xd4, 0xc3, 0xb2, 0xa1);

static const ble_uuid128_t uuid_char_battery = BLE_UUID128_INIT(
    0x04, 0x00, 0xf6, 0xe5, 0xd4, 0xc3, 0xb2, 0xa1,
    0x90, 0x78, 0xf6, 0xe5, 0xd4, 0xc3, 0xb2, 0xa1);

static const ble_uuid128_t uuid_char_session_time = BLE_UUID128_INIT(
    0x05, 0x00, 0xf6, 0xe5, 0xd4, 0xc3, 0xb2, 0xa1,
    0x90, 0x78, 0xf6, 0xe5, 0xd4, 0xc3, 0xb2, 0xa1);

static const ble_uuid128_t uuid_char_led_enable = BLE_UUID128_INIT(
    0x06, 0x00, 0xf6, 0xe5, 0xd4, 0xc3, 0xb2, 0xa1,
    0x90, 0x78, 0xf6, 0xe5, 0xd4, 0xc3, 0xb2, 0xa1);

static const ble_uuid128_t uuid_char_led_color = BLE_UUID128_INIT(
    0x07, 0x00, 0xf6, 0xe5, 0xd4, 0xc3, 0xb2, 0xa1,
    0x90, 0x78, 0xf6, 0xe5, 0xd4, 0xc3, 0xb2, 0xa1);

static const ble_uuid128_t uuid_char_led_brightness = BLE_UUID128_INIT(
    0x08, 0x00, 0xf6, 0xe5, 0xd4, 0xc3, 0xb2, 0xa1,
    0x90, 0x78, 0xf6, 0xe5, 0xd4, 0xc3, 0xb2, 0xa1);

static const ble_uuid128_t uuid_char_pwm_intensity = BLE_UUID128_INIT(
    0x09, 0x00, 0xf6, 0xe5, 0xd4, 0xc3, 0xb2, 0xa1,
    0x90, 0x78, 0xf6, 0xe5, 0xd4, 0xc3, 0xb2, 0xa1);

// GATT Server Configuration
#define GATTS_NUM_HANDLE         20

// Mode 5 LED Color Palette (16 colors for WS2812B)
typedef struct {
    uint8_t r;
    uint8_t g;
    uint8_t b;
} rgb_color_t;

static const rgb_color_t color_palette[16] = {
    {255, 0, 0},      // 0: Red
    {255, 127, 0},    // 1: Orange
    {255, 255, 0},    // 2: Yellow
    {0, 255, 0},      // 3: Green
    {0, 255, 127},    // 4: Spring Green
    {0, 255, 255},    // 5: Cyan
    {0, 127, 255},    // 6: Sky Blue
    {0, 0, 255},      // 7: Blue
    {127, 0, 255},    // 8: Violet
    {255, 0, 255},    // 9: Magenta
    {255, 0, 127},    // 10: Pink
    {255, 255, 255},  // 11: White
    {127, 127, 127},  // 12: Gray
    {64, 64, 64},     // 13: Dark Gray
    {192, 192, 192},  // 14: Light Gray
    {128, 64, 0}      // 15: Brown
};

// Custom Mode 5 settings (BLE configurable)
static uint16_t custom_frequency_hz = 100;   // Default 1Hz (100 = period 1000ms)
static uint8_t custom_duty_percent = 50;     // Default 50% duty cycle
static mode_t current_mode_ble = MODE_1HZ_50; // Track current mode for BLE reads
static uint32_t session_start_time_ms = 0;   // Session start timestamp

// Mode 5 LED settings (BLE configurable)
static bool mode5_led_enable = true;       // Enable LED blink with motor pattern
static uint8_t mode5_led_color_index = 0;  // Default: Red
static uint8_t mode5_led_brightness = 20;  // Default: 20% (range 10-30%)

// Mode 5 motor settings (BLE configurable)
static uint8_t mode5_pwm_intensity = 75;   // Default: 75% (range 30-90%)

// Mode 5 motor timing (separate from const modes array)
static uint32_t mode5_motor_on_ms = 250;   // Default: 250ms on (1Hz @ 50%)
static uint32_t mode5_coast_ms = 250;      // Default: 250ms coast

// NVS persistence tracking
static bool mode5_settings_dirty = false;         // True if settings changed since last NVS save
static SemaphoreHandle_t mode5_settings_mutex = NULL;  // Mutex for thread-safe access

// BLE parameter update flag (for instant mode change responsiveness)
static volatile bool ble_params_updated = false;  // Set by GATT write handlers, cleared by motor_task

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

    // Check if no battery present (< 0.5V)
    if (battery_v < LVO_NO_BATTERY_THRESHOLD) {
        ESP_LOGW(TAG, "LVO check: No battery detected (%.2fV) - allowing operation", battery_v);
        ESP_LOGW(TAG, "Device can be programmed/tested without battery");
        ESP_LOGI(TAG, "LVO check: SKIPPED - no battery present");
        return true;  // Skip LVO, continue operation
    }

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

// ============================================================================
// GATT SERVICE - CHARACTERISTIC ACCESS CALLBACKS
// ============================================================================

// Helper: Update Mode 5 timing from frequency and duty cycle
static void update_mode5_timing(void) {
    // Formula: period_ms = 1000 / (frequency_hz / 100)
    // Then: on_time = period_ms * (duty_percent / 100)
    uint32_t period_ms = (100000 / custom_frequency_hz);  // Avoid float
    uint32_t on_time_ms = (period_ms * custom_duty_percent) / 100;
    uint32_t coast_ms = period_ms - on_time_ms;

    // Update the mutable Mode 5 timing variables (not const array)
    mode5_motor_on_ms = on_time_ms;
    mode5_coast_ms = coast_ms;

    ESP_LOGI(TAG, "Mode 5 updated: freq=%.2fHz duty=%u%% -> on=%ums coast=%ums",
             custom_frequency_hz / 100.0f, custom_duty_percent, on_time_ms, coast_ms);
}

// ============================================================================
// NVS PERSISTENCE HELPERS
// ============================================================================

// Calculate Mode 5 structure signature using CRC32
static uint32_t calculate_mode5_signature(void) {
    // Signature data: {uuid_ending, byte_length} pairs for all 6 characteristics
    uint8_t sig_data[] = {
        0x02, 2,   // Custom Frequency: uint16_t
        0x03, 1,   // Custom Duty: uint8_t
        0x06, 1,   // LED Enable: uint8_t
        0x07, 1,   // LED Color: uint8_t
        0x08, 1,   // LED Brightness: uint8_t
        0x09, 1    // PWM Intensity: uint8_t
    };
    return esp_crc32_le(0, sig_data, sizeof(sig_data));
}

// Clear all NVS data (factory reset)
static esp_err_t nvs_clear_all(void) {
    ESP_LOGI(TAG, "Clearing all NVS data (factory reset)");

    // Erase NVS partition
    esp_err_t ret = nvs_flash_erase();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "NVS erase failed: %s", esp_err_to_name(ret));
        return ret;
    }

    ESP_LOGI(TAG, "NVS partition erased");

    // Reinitialize NVS
    ret = nvs_flash_init();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "NVS reinit after erase failed: %s", esp_err_to_name(ret));
        return ret;
    }

    ESP_LOGI(TAG, "Factory reset complete (all NVS data cleared)");
    return ESP_OK;
}

// Load Mode 5 settings from NVS (called once at boot)
static void load_mode5_settings_from_nvs(void) {
    nvs_handle_t nvs_handle;
    esp_err_t err = nvs_open(NVS_NAMESPACE, NVS_READONLY, &nvs_handle);

    if (err != ESP_OK) {
        ESP_LOGW(TAG, "NVS: Unable to open namespace (first boot?) - using defaults");
        return;
    }

    // Read and verify signature
    uint32_t stored_sig = 0;
    uint32_t expected_sig = calculate_mode5_signature();
    err = nvs_get_u32(nvs_handle, NVS_KEY_SIGNATURE, &stored_sig);

    if (err != ESP_OK || stored_sig != expected_sig) {
        ESP_LOGW(TAG, "NVS: Signature mismatch (0x%08" PRIx32 " != 0x%08" PRIx32 ") - using defaults",
                 stored_sig, expected_sig);
        nvs_close(nvs_handle);
        return;
    }

    ESP_LOGI(TAG, "NVS: Signature valid (0x%08" PRIx32 "), loading Mode 5 settings...", expected_sig);

    // Load all 6 settings
    uint16_t freq;
    uint8_t duty, led_en, led_col, led_bri, pwm_int;

    if (nvs_get_u16(nvs_handle, NVS_KEY_FREQUENCY, &freq) == ESP_OK) {
        custom_frequency_hz = freq;
        ESP_LOGI(TAG, "NVS: Loaded frequency = %u", freq);
    }

    if (nvs_get_u8(nvs_handle, NVS_KEY_DUTY, &duty) == ESP_OK) {
        custom_duty_percent = duty;
        ESP_LOGI(TAG, "NVS: Loaded duty = %u%%", duty);
    }

    if (nvs_get_u8(nvs_handle, NVS_KEY_LED_ENABLE, &led_en) == ESP_OK) {
        mode5_led_enable = (led_en != 0);
        ESP_LOGI(TAG, "NVS: Loaded LED enable = %u", led_en);
    }

    if (nvs_get_u8(nvs_handle, NVS_KEY_LED_COLOR, &led_col) == ESP_OK) {
        mode5_led_color_index = led_col;
        ESP_LOGI(TAG, "NVS: Loaded LED color index = %u", led_col);
    }

    if (nvs_get_u8(nvs_handle, NVS_KEY_LED_BRIGHTNESS, &led_bri) == ESP_OK) {
        mode5_led_brightness = led_bri;
        ESP_LOGI(TAG, "NVS: Loaded LED brightness = %u%%", led_bri);
    }

    if (nvs_get_u8(nvs_handle, NVS_KEY_PWM_INTENSITY, &pwm_int) == ESP_OK) {
        mode5_pwm_intensity = pwm_int;
        ESP_LOGI(TAG, "NVS: Loaded PWM intensity = %u%%", pwm_int);
    }

    nvs_close(nvs_handle);

    // Recalculate motor timings from loaded frequency/duty
    update_mode5_timing();

    ESP_LOGI(TAG, "NVS: Mode 5 settings loaded successfully");
}

// Save Mode 5 settings to NVS (called before deep sleep)
static void save_mode5_settings_to_nvs(void) {
    // Check dirty flag (thread-safe)
    if (mode5_settings_mutex != NULL) {
        xSemaphoreTake(mode5_settings_mutex, portMAX_DELAY);
    }

    bool is_dirty = mode5_settings_dirty;

    if (mode5_settings_mutex != NULL) {
        xSemaphoreGive(mode5_settings_mutex);
    }

    if (!is_dirty) {
        ESP_LOGI(TAG, "NVS: Mode 5 settings unchanged, skipping save");
        return;
    }

    ESP_LOGI(TAG, "NVS: Saving Mode 5 settings...");

    nvs_handle_t nvs_handle;
    esp_err_t err = nvs_open(NVS_NAMESPACE, NVS_READWRITE, &nvs_handle);

    if (err != ESP_OK) {
        ESP_LOGE(TAG, "NVS: Failed to open namespace for writing: %s", esp_err_to_name(err));
        return;
    }

    // Write signature first
    uint32_t sig = calculate_mode5_signature();
    err = nvs_set_u32(nvs_handle, NVS_KEY_SIGNATURE, sig);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "NVS: Failed to write signature: %s", esp_err_to_name(err));
        nvs_close(nvs_handle);
        return;
    }

    // Write all 6 settings
    nvs_set_u16(nvs_handle, NVS_KEY_FREQUENCY, custom_frequency_hz);
    nvs_set_u8(nvs_handle, NVS_KEY_DUTY, custom_duty_percent);
    nvs_set_u8(nvs_handle, NVS_KEY_LED_ENABLE, mode5_led_enable ? 1 : 0);
    nvs_set_u8(nvs_handle, NVS_KEY_LED_COLOR, mode5_led_color_index);
    nvs_set_u8(nvs_handle, NVS_KEY_LED_BRIGHTNESS, mode5_led_brightness);
    nvs_set_u8(nvs_handle, NVS_KEY_PWM_INTENSITY, mode5_pwm_intensity);

    // Commit to flash
    err = nvs_commit(nvs_handle);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "NVS: Failed to commit: %s", esp_err_to_name(err));
    } else {
        ESP_LOGI(TAG, "NVS: Mode 5 settings saved (freq=%u duty=%u%% led_en=%u led_col=%u led_bri=%u%% pwm=%u%%)",
                 custom_frequency_hz, custom_duty_percent, mode5_led_enable ? 1 : 0,
                 mode5_led_color_index, mode5_led_brightness, mode5_pwm_intensity);

        // Clear dirty flag (thread-safe)
        if (mode5_settings_mutex != NULL) {
            xSemaphoreTake(mode5_settings_mutex, portMAX_DELAY);
            mode5_settings_dirty = false;
            xSemaphoreGive(mode5_settings_mutex);
        } else {
            mode5_settings_dirty = false;
        }
    }

    nvs_close(nvs_handle);
}

// Mode characteristic - Read callback
static int gatt_char_mode_read(uint16_t conn_handle, uint16_t attr_handle,
                                struct ble_gatt_access_ctxt *ctxt, void *arg) {
    ESP_LOGI(TAG, "GATT Read: Current mode = %u", current_mode_ble);
    uint8_t mode_val = (uint8_t)current_mode_ble;
    int rc = os_mbuf_append(ctxt->om, &mode_val, sizeof(mode_val));
    return (rc == 0) ? 0 : BLE_ATT_ERR_INSUFFICIENT_RES;
}

// Mode characteristic - Write callback
static int gatt_char_mode_write(uint16_t conn_handle, uint16_t attr_handle,
                                 struct ble_gatt_access_ctxt *ctxt, void *arg) {
    uint8_t mode_val = 0;
    int rc = ble_hs_mbuf_to_flat(ctxt->om, &mode_val, sizeof(mode_val), NULL);
    if (rc != 0) {
        ESP_LOGE(TAG, "GATT Write: Mode read failed");
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    // Validate range
    if (mode_val >= MODE_COUNT) {
        ESP_LOGE(TAG, "GATT Write: Invalid mode %u (max %u)", mode_val, MODE_COUNT - 1);
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    current_mode_ble = (mode_t)mode_val;
    ESP_LOGI(TAG, "GATT Write: Mode changed to %u (%s)", mode_val, modes[mode_val].name);

    // Send mode change message to motor task
    task_message_t msg = {.type = MSG_MODE_CHANGE, .data.new_mode = current_mode_ble};
    if (xQueueSend(button_to_motor_queue, &msg, pdMS_TO_TICKS(100)) != pdTRUE) {
        ESP_LOGW(TAG, "GATT Write: Failed to send mode change to motor task");
    }

    return 0;
}

// Custom Frequency characteristic - Read callback
static int gatt_char_custom_freq_read(uint16_t conn_handle, uint16_t attr_handle,
                                       struct ble_gatt_access_ctxt *ctxt, void *arg) {
    ESP_LOGI(TAG, "GATT Read: Custom frequency = %u (%.2f Hz)",
             custom_frequency_hz, custom_frequency_hz / 100.0f);
    int rc = os_mbuf_append(ctxt->om, &custom_frequency_hz, sizeof(custom_frequency_hz));
    return (rc == 0) ? 0 : BLE_ATT_ERR_INSUFFICIENT_RES;
}

// Custom Frequency characteristic - Write callback
static int gatt_char_custom_freq_write(uint16_t conn_handle, uint16_t attr_handle,
                                        struct ble_gatt_access_ctxt *ctxt, void *arg) {
    uint16_t freq_val = 0;
    int rc = ble_hs_mbuf_to_flat(ctxt->om, &freq_val, sizeof(freq_val), NULL);
    if (rc != 0) {
        ESP_LOGE(TAG, "GATT Write: Frequency read failed");
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    // Validate range (25 = 0.25Hz, 200 = 2.0Hz)
    if (freq_val < 25 || freq_val > 200) {
        ESP_LOGE(TAG, "GATT Write: Invalid frequency %u (range 25-200 = 0.25-2.0Hz)", freq_val);
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    custom_frequency_hz = freq_val;
    ESP_LOGI(TAG, "GATT Write: Custom frequency = %u (%.2f Hz)", freq_val, freq_val / 100.0f);

    // Update Mode 5 timing
    update_mode5_timing();

    // Mark settings as dirty for NVS save
    if (mode5_settings_mutex != NULL) {
        xSemaphoreTake(mode5_settings_mutex, portMAX_DELAY);
        mode5_settings_dirty = true;
        xSemaphoreGive(mode5_settings_mutex);
    } else {
        mode5_settings_dirty = true;
    }

    // Signal motor task to reload parameters immediately
    ble_params_updated = true;

    // If currently in Mode 5, send update to motor task
    if (current_mode_ble == MODE_CUSTOM) {
        task_message_t msg = {.type = MSG_MODE_CHANGE, .data.new_mode = MODE_CUSTOM};
        xQueueSend(button_to_motor_queue, &msg, pdMS_TO_TICKS(100));
    }

    return 0;
}

// Custom Duty Cycle characteristic - Read callback
static int gatt_char_custom_duty_read(uint16_t conn_handle, uint16_t attr_handle,
                                       struct ble_gatt_access_ctxt *ctxt, void *arg) {
    ESP_LOGI(TAG, "GATT Read: Custom duty cycle = %u%%", custom_duty_percent);
    int rc = os_mbuf_append(ctxt->om, &custom_duty_percent, sizeof(custom_duty_percent));
    return (rc == 0) ? 0 : BLE_ATT_ERR_INSUFFICIENT_RES;
}

// Custom Duty Cycle characteristic - Write callback
static int gatt_char_custom_duty_write(uint16_t conn_handle, uint16_t attr_handle,
                                        struct ble_gatt_access_ctxt *ctxt, void *arg) {
    uint8_t duty_val = 0;
    int rc = ble_hs_mbuf_to_flat(ctxt->om, &duty_val, sizeof(duty_val), NULL);
    if (rc != 0) {
        ESP_LOGE(TAG, "GATT Write: Duty cycle read failed");
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    // NOTE: This OLD test file uses 10-50% range. Production code (src/) uses 10-100% range.
    // 100% duty = motor ON for entire ACTIVE period, guaranteed OFF for INACTIVE period.
    // Validate range (10-50%): 10% min ensures perception, 50% max prevents motor overlap in bilateral alternation
    // For LED-only mode, set PWM intensity to 0% instead
    if (duty_val < 10 || duty_val > 50) {
        ESP_LOGE(TAG, "GATT Write: Invalid duty cycle %u%% (range 10-50%%)", duty_val);
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    custom_duty_percent = duty_val;
    ESP_LOGI(TAG, "GATT Write: Custom duty cycle = %u%%", duty_val);

    // Update Mode 5 timing
    update_mode5_timing();

    // Mark settings as dirty for NVS save
    if (mode5_settings_mutex != NULL) {
        xSemaphoreTake(mode5_settings_mutex, portMAX_DELAY);
        mode5_settings_dirty = true;
        xSemaphoreGive(mode5_settings_mutex);
    } else {
        mode5_settings_dirty = true;
    }

    // Signal motor task to reload parameters immediately
    ble_params_updated = true;

    // If currently in Mode 5, send update to motor task
    if (current_mode_ble == MODE_CUSTOM) {
        task_message_t msg = {.type = MSG_MODE_CHANGE, .data.new_mode = MODE_CUSTOM};
        xQueueSend(button_to_motor_queue, &msg, pdMS_TO_TICKS(100));
    }

    return 0;
}

// Battery Level characteristic - Read callback
static int gatt_char_battery_read(uint16_t conn_handle, uint16_t attr_handle,
                                   struct ble_gatt_access_ctxt *ctxt, void *arg) {
    int raw_mv = 0;
    float battery_v = 0.0f;
    int percentage = 0;

    esp_err_t ret = read_battery_voltage(&raw_mv, &battery_v, &percentage);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "GATT Read: Battery read failed");
        percentage = 0;
    }

    uint8_t battery_percent = (uint8_t)percentage;
    ESP_LOGI(TAG, "GATT Read: Battery = %u%% (%.2fV)", battery_percent, battery_v);

    int rc = os_mbuf_append(ctxt->om, &battery_percent, sizeof(battery_percent));
    return (rc == 0) ? 0 : BLE_ATT_ERR_INSUFFICIENT_RES;
}

// Session Time characteristic - Read callback
static int gatt_char_session_time_read(uint16_t conn_handle, uint16_t attr_handle,
                                        struct ble_gatt_access_ctxt *ctxt, void *arg) {
    uint32_t now = (uint32_t)(esp_timer_get_time() / 1000);
    uint32_t elapsed_ms = (session_start_time_ms > 0) ? (now - session_start_time_ms) : 0;
    uint32_t elapsed_sec = elapsed_ms / 1000;

    ESP_LOGI(TAG, "GATT Read: Session time = %u seconds", elapsed_sec);

    int rc = os_mbuf_append(ctxt->om, &elapsed_sec, sizeof(elapsed_sec));
    return (rc == 0) ? 0 : BLE_ATT_ERR_INSUFFICIENT_RES;
}

// LED Enable characteristic - Read callback
static int gatt_char_led_enable_read(uint16_t conn_handle, uint16_t attr_handle,
                                      struct ble_gatt_access_ctxt *ctxt, void *arg) {
    ESP_LOGI(TAG, "GATT Read: Mode 5 LED enable = %d", mode5_led_enable);
    uint8_t value = mode5_led_enable ? 1 : 0;
    int rc = os_mbuf_append(ctxt->om, &value, sizeof(value));
    return (rc == 0) ? 0 : BLE_ATT_ERR_INSUFFICIENT_RES;
}

// LED Enable characteristic - Write callback
static int gatt_char_led_enable_write(uint16_t conn_handle, uint16_t attr_handle,
                                       struct ble_gatt_access_ctxt *ctxt, void *arg) {
    uint8_t value;
    uint16_t len = OS_MBUF_PKTLEN(ctxt->om);
    if (len != sizeof(value)) {
        ESP_LOGW(TAG, "GATT Write: LED enable invalid length %d", len);
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    int rc = ble_hs_mbuf_to_flat(ctxt->om, &value, sizeof(value), NULL);
    if (rc != 0) return BLE_ATT_ERR_UNLIKELY;

    mode5_led_enable = (value != 0);
    ESP_LOGI(TAG, "GATT Write: Mode 5 LED enable = %d", mode5_led_enable);

    // Mark settings as dirty for NVS save
    if (mode5_settings_mutex != NULL) {
        xSemaphoreTake(mode5_settings_mutex, portMAX_DELAY);
        mode5_settings_dirty = true;
        xSemaphoreGive(mode5_settings_mutex);
    } else {
        mode5_settings_dirty = true;
    }

    // Signal motor task to reload parameters immediately
    ble_params_updated = true;

    return 0;
}

// LED Color characteristic - Read callback
static int gatt_char_led_color_read(uint16_t conn_handle, uint16_t attr_handle,
                                     struct ble_gatt_access_ctxt *ctxt, void *arg) {
    ESP_LOGI(TAG, "GATT Read: Mode 5 LED color index = %d", mode5_led_color_index);
    int rc = os_mbuf_append(ctxt->om, &mode5_led_color_index, sizeof(mode5_led_color_index));
    return (rc == 0) ? 0 : BLE_ATT_ERR_INSUFFICIENT_RES;
}

// LED Color characteristic - Write callback
static int gatt_char_led_color_write(uint16_t conn_handle, uint16_t attr_handle,
                                      struct ble_gatt_access_ctxt *ctxt, void *arg) {
    uint8_t value;
    uint16_t len = OS_MBUF_PKTLEN(ctxt->om);
    if (len != sizeof(value)) {
        ESP_LOGW(TAG, "GATT Write: LED color invalid length %d", len);
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    int rc = ble_hs_mbuf_to_flat(ctxt->om, &value, sizeof(value), NULL);
    if (rc != 0) return BLE_ATT_ERR_UNLIKELY;

    if (value > 15) {
        ESP_LOGW(TAG, "GATT Write: LED color index %d out of range (0-15)", value);
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    mode5_led_color_index = value;
    ESP_LOGI(TAG, "GATT Write: Mode 5 LED color = %d (R:%d G:%d B:%d)",
             value, color_palette[value].r, color_palette[value].g, color_palette[value].b);

    // Mark settings as dirty for NVS save
    if (mode5_settings_mutex != NULL) {
        xSemaphoreTake(mode5_settings_mutex, portMAX_DELAY);
        mode5_settings_dirty = true;
        xSemaphoreGive(mode5_settings_mutex);
    } else {
        mode5_settings_dirty = true;
    }

    // Signal motor task to reload parameters immediately
    ble_params_updated = true;

    return 0;
}

// LED Brightness characteristic - Read callback
static int gatt_char_led_brightness_read(uint16_t conn_handle, uint16_t attr_handle,
                                          struct ble_gatt_access_ctxt *ctxt, void *arg) {
    ESP_LOGI(TAG, "GATT Read: Mode 5 LED brightness = %d%%", mode5_led_brightness);
    int rc = os_mbuf_append(ctxt->om, &mode5_led_brightness, sizeof(mode5_led_brightness));
    return (rc == 0) ? 0 : BLE_ATT_ERR_INSUFFICIENT_RES;
}

// LED Brightness characteristic - Write callback
static int gatt_char_led_brightness_write(uint16_t conn_handle, uint16_t attr_handle,
                                           struct ble_gatt_access_ctxt *ctxt, void *arg) {
    uint8_t value;
    uint16_t len = OS_MBUF_PKTLEN(ctxt->om);
    if (len != sizeof(value)) {
        ESP_LOGW(TAG, "GATT Write: LED brightness invalid length %d", len);
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    int rc = ble_hs_mbuf_to_flat(ctxt->om, &value, sizeof(value), NULL);
    if (rc != 0) return BLE_ATT_ERR_UNLIKELY;

    if (value < 10 || value > 30) {
        ESP_LOGW(TAG, "GATT Write: LED brightness %d%% out of range (10-30%%)", value);
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    mode5_led_brightness = value;
    ESP_LOGI(TAG, "GATT Write: Mode 5 LED brightness = %d%%", value);

    // Mark settings as dirty for NVS save
    if (mode5_settings_mutex != NULL) {
        xSemaphoreTake(mode5_settings_mutex, portMAX_DELAY);
        mode5_settings_dirty = true;
        xSemaphoreGive(mode5_settings_mutex);
    } else {
        mode5_settings_dirty = true;
    }

    // Signal motor task to reload parameters immediately
    ble_params_updated = true;

    return 0;
}

// PWM Intensity - Read callback
static int gatt_char_pwm_intensity_read(uint16_t conn_handle, uint16_t attr_handle,
                                        struct ble_gatt_access_ctxt *ctxt, void *arg) {
    ESP_LOGI(TAG, "GATT Read: Mode 5 PWM intensity = %d%%", mode5_pwm_intensity);
    int rc = os_mbuf_append(ctxt->om, &mode5_pwm_intensity, sizeof(mode5_pwm_intensity));
    return (rc == 0) ? 0 : BLE_ATT_ERR_INSUFFICIENT_RES;
}

// PWM Intensity - Write callback
static int gatt_char_pwm_intensity_write(uint16_t conn_handle, uint16_t attr_handle,
                                         struct ble_gatt_access_ctxt *ctxt, void *arg) {
    uint8_t value;
    uint16_t len = OS_MBUF_PKTLEN(ctxt->om);
    if (len != sizeof(value)) {
        ESP_LOGW(TAG, "GATT Write: PWM intensity invalid length %d", len);
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    int rc = ble_hs_mbuf_to_flat(ctxt->om, &value, sizeof(value), NULL);
    if (rc != 0) return BLE_ATT_ERR_UNLIKELY;

    // Range 0-80%: 0% = LED-only mode (no motor vibration), 80% max prevents overheating
    if (value > 80) {
        ESP_LOGW(TAG, "GATT Write: PWM intensity %d%% out of range (0-80%%)", value);
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    mode5_pwm_intensity = value;
    ESP_LOGI(TAG, "GATT Write: Mode 5 PWM intensity = %d%%", value);

    // Mark settings as dirty for NVS save
    if (mode5_settings_mutex != NULL) {
        xSemaphoreTake(mode5_settings_mutex, portMAX_DELAY);
        mode5_settings_dirty = true;
        xSemaphoreGive(mode5_settings_mutex);
    } else {
        mode5_settings_dirty = true;
    }

    // Signal motor task to reload parameters immediately
    ble_params_updated = true;

    return 0;
}

// GATT characteristic access dispatcher
static int gatt_svr_chr_access(uint16_t conn_handle, uint16_t attr_handle,
                                struct ble_gatt_access_ctxt *ctxt, void *arg) {
    const ble_uuid_t *uuid = ctxt->chr->uuid;

    // Determine which characteristic is being accessed
    if (ble_uuid_cmp(uuid, &uuid_char_mode.u) == 0) {
        return (ctxt->op == BLE_GATT_ACCESS_OP_READ_CHR) ?
               gatt_char_mode_read(conn_handle, attr_handle, ctxt, arg) :
               gatt_char_mode_write(conn_handle, attr_handle, ctxt, arg);
    }

    if (ble_uuid_cmp(uuid, &uuid_char_custom_freq.u) == 0) {
        return (ctxt->op == BLE_GATT_ACCESS_OP_READ_CHR) ?
               gatt_char_custom_freq_read(conn_handle, attr_handle, ctxt, arg) :
               gatt_char_custom_freq_write(conn_handle, attr_handle, ctxt, arg);
    }

    if (ble_uuid_cmp(uuid, &uuid_char_custom_duty.u) == 0) {
        return (ctxt->op == BLE_GATT_ACCESS_OP_READ_CHR) ?
               gatt_char_custom_duty_read(conn_handle, attr_handle, ctxt, arg) :
               gatt_char_custom_duty_write(conn_handle, attr_handle, ctxt, arg);
    }

    if (ble_uuid_cmp(uuid, &uuid_char_battery.u) == 0) {
        return gatt_char_battery_read(conn_handle, attr_handle, ctxt, arg);
    }

    if (ble_uuid_cmp(uuid, &uuid_char_session_time.u) == 0) {
        return gatt_char_session_time_read(conn_handle, attr_handle, ctxt, arg);
    }

    if (ble_uuid_cmp(uuid, &uuid_char_led_enable.u) == 0) {
        return (ctxt->op == BLE_GATT_ACCESS_OP_READ_CHR) ?
               gatt_char_led_enable_read(conn_handle, attr_handle, ctxt, arg) :
               gatt_char_led_enable_write(conn_handle, attr_handle, ctxt, arg);
    }

    if (ble_uuid_cmp(uuid, &uuid_char_led_color.u) == 0) {
        return (ctxt->op == BLE_GATT_ACCESS_OP_READ_CHR) ?
               gatt_char_led_color_read(conn_handle, attr_handle, ctxt, arg) :
               gatt_char_led_color_write(conn_handle, attr_handle, ctxt, arg);
    }

    if (ble_uuid_cmp(uuid, &uuid_char_led_brightness.u) == 0) {
        return (ctxt->op == BLE_GATT_ACCESS_OP_READ_CHR) ?
               gatt_char_led_brightness_read(conn_handle, attr_handle, ctxt, arg) :
               gatt_char_led_brightness_write(conn_handle, attr_handle, ctxt, arg);
    }

    if (ble_uuid_cmp(uuid, &uuid_char_pwm_intensity.u) == 0) {
        return (ctxt->op == BLE_GATT_ACCESS_OP_READ_CHR) ?
               gatt_char_pwm_intensity_read(conn_handle, attr_handle, ctxt, arg) :
               gatt_char_pwm_intensity_write(conn_handle, attr_handle, ctxt, arg);
    }

    return BLE_ATT_ERR_UNLIKELY;
}

// GATT service definition
static const struct ble_gatt_svc_def gatt_svr_svcs[] = {
    {
        // EMDR Motor Control Service
        .type = BLE_GATT_SVC_TYPE_PRIMARY,
        .uuid = &uuid_emdr_service.u,
        .characteristics = (struct ble_gatt_chr_def[]) {
            {
                // Mode selection (R/W)
                .uuid = &uuid_char_mode.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_WRITE,
            },
            {
                // Custom frequency (R/W, uint16, Hz × 100)
                .uuid = &uuid_char_custom_freq.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_WRITE,
            },
            {
                // Custom duty cycle (R/W, uint8, percentage)
                .uuid = &uuid_char_custom_duty.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_WRITE,
            },
            {
                // Battery level (R/N, uint8, percentage)
                .uuid = &uuid_char_battery.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_NOTIFY,
            },
            {
                // Session time (R/N, uint32, seconds)
                .uuid = &uuid_char_session_time.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_NOTIFY,
            },
            {
                // LED Enable (R/W, uint8, boolean 0/1)
                .uuid = &uuid_char_led_enable.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_WRITE,
            },
            {
                // LED Color (R/W, uint8, color index 0-15)
                .uuid = &uuid_char_led_color.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_WRITE,
            },
            {
                // LED Brightness (R/W, uint8, percentage 10-30%)
                .uuid = &uuid_char_led_brightness.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_WRITE,
            },
            {
                // PWM Intensity (R/W, uint8, percentage 30-90%)
                .uuid = &uuid_char_pwm_intensity.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_WRITE,
            },
            {
                0, // No more characteristics
            }
        },
    },
    {
        0, // No more services
    },
};

// GATT service registration callback
static void gatt_svr_register_cb(struct ble_gatt_register_ctxt *ctxt, void *arg) {
    char buf[BLE_UUID_STR_LEN];

    switch (ctxt->op) {
    case BLE_GATT_REGISTER_OP_SVC:
        ESP_LOGI(TAG, "GATT: Registered service %s with handle=%d",
                 ble_uuid_to_str(ctxt->svc.svc_def->uuid, buf), ctxt->svc.handle);
        break;

    case BLE_GATT_REGISTER_OP_CHR:
        ESP_LOGI(TAG, "GATT: Registered characteristic %s with def_handle=%d val_handle=%d",
                 ble_uuid_to_str(ctxt->chr.chr_def->uuid, buf),
                 ctxt->chr.def_handle, ctxt->chr.val_handle);
        break;

    case BLE_GATT_REGISTER_OP_DSC:
        ESP_LOGI(TAG, "GATT: Registered descriptor %s with handle=%d",
                 ble_uuid_to_str(ctxt->dsc.dsc_def->uuid, buf), ctxt->dsc.handle);
        break;

    default:
        break;
    }
}

// Initialize GATT services
static esp_err_t gatt_svr_init(void) {
    int rc;

    // Reset GATT server
    ble_svc_gatt_init();

    // Add custom services
    rc = ble_gatts_count_cfg(gatt_svr_svcs);
    if (rc != 0) {
        ESP_LOGE(TAG, "GATT: Failed to count services; rc=%d", rc);
        return ESP_FAIL;
    }

    rc = ble_gatts_add_svcs(gatt_svr_svcs);
    if (rc != 0) {
        ESP_LOGE(TAG, "GATT: Failed to add services; rc=%d", rc);
        return ESP_FAIL;
    }

    ESP_LOGI(TAG, "GATT: Services initialized successfully");
    return ESP_OK;
}

// ============================================================================
// STATUS LED HELPERS
// ============================================================================

static inline void status_led_on(void) {
    gpio_set_level(GPIO_STATUS_LED, 0);  // Active-low
}

static inline void status_led_off(void) {
    gpio_set_level(GPIO_STATUS_LED, 1);  // Active-low
}

static void status_led_blink(uint8_t count, uint32_t on_ms, uint32_t off_ms) {
    for (uint8_t i = 0; i < count; i++) {
        status_led_on();
        vTaskDelay(pdMS_TO_TICKS(on_ms));
        status_led_off();
        if (i < count - 1) {  // Don't delay after last blink
            vTaskDelay(pdMS_TO_TICKS(off_ms));
        }
    }
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

// Set LED color based on current mode (Mode 5 uses BLE-configured color/brightness)
static void led_set_mode_color(mode_t mode) {
    if (mode == MODE_CUSTOM) {
        // Mode 5: Use BLE-configured color and brightness
        const rgb_color_t *color = &color_palette[mode5_led_color_index];
        uint8_t r = color->r, g = color->g, b = color->b;
        apply_brightness(&r, &g, &b, mode5_led_brightness);
        led_strip_set_pixel(led_strip, 0, r, g, b);
        led_strip_refresh(led_strip);
    } else {
        // Other modes: Red at fixed brightness
        led_set_color(255, 0, 0);
    }
}

static void led_clear(void) {
    led_strip_clear(led_strip);
}

// NIMBLE BLE INITIALIZATION AND EVENT HANDLERS

// NimBLE advertising parameters (declared before use)
static struct ble_gap_adv_params adv_params = {
    .conn_mode = BLE_GAP_CONN_MODE_UND,  // Undirected connectable
    .disc_mode = BLE_GAP_DISC_MODE_GEN,  // General discoverable
    .itvl_min = 0x20,                     // 20ms
    .itvl_max = 0x40,                     // 40ms
};

// NimBLE GAP event handler
static int ble_gap_event(struct ble_gap_event *event, void *arg) {
    switch (event->type) {
        case BLE_GAP_EVENT_CONNECT:
            ESP_LOGI(TAG, "BLE connection %s; status=%d",
                     event->connect.status == 0 ? "established" : "failed",
                     event->connect.status);
            if (event->connect.status == 0) {
                ble_adv_state.client_connected = true;
                ble_adv_state.advertising_active = false;
                // Status LED: 5× blink for connection
                status_led_blink(5, 100, 100);
            }
            break;

        case BLE_GAP_EVENT_DISCONNECT:
            ESP_LOGI(TAG, "BLE disconnect; reason=%d", event->disconnect.reason);
            ble_adv_state.client_connected = false;

            // Resume advertising on disconnect
            ble_gap_adv_start(BLE_OWN_ADDR_PUBLIC, NULL, BLE_HS_FOREVER,
                              &adv_params, ble_gap_event, NULL);
            ble_adv_state.advertising_active = true;
            ble_adv_state.advertising_start_ms = (uint32_t)(esp_timer_get_time() / 1000);
            ESP_LOGI(TAG, "BLE advertising restarted after disconnect");
            break;

        case BLE_GAP_EVENT_ADV_COMPLETE:
            ESP_LOGI(TAG, "BLE advertising complete; reason=%d", event->adv_complete.reason);
            ble_adv_state.advertising_active = false;
            break;

        default:
            break;
    }
    return 0;
}

// NimBLE host reset callback
static void ble_on_reset(int reason) {
    ESP_LOGE(TAG, "BLE host reset; reason=%d", reason);
}

// NimBLE host sync callback
static void ble_on_sync(void) {
    int rc;

    ESP_LOGI(TAG, "BLE host synced");

    // Set device name
    rc = ble_svc_gap_device_name_set(BLE_DEVICE_NAME);
    if (rc != 0) {
        ESP_LOGE(TAG, "Failed to set device name; rc=%d", rc);
        return;
    }

    // Get BLE address for device name suffix
    uint8_t addr_val[6];
    rc = ble_hs_id_infer_auto(0, &addr_val[0]);
    if (rc == 0) {
        // Create unique device name with last 3 MAC bytes
        char unique_name[32];
        snprintf(unique_name, sizeof(unique_name), "%s_%02X%02X%02X",
                 BLE_DEVICE_NAME, addr_val[3], addr_val[4], addr_val[5]);
        ble_svc_gap_device_name_set(unique_name);
        ESP_LOGI(TAG, "BLE device name: %s", unique_name);
    }

    // Configure advertising data
    struct ble_hs_adv_fields fields;
    memset(&fields, 0, sizeof(fields));

    fields.flags = BLE_HS_ADV_F_DISC_GEN | BLE_HS_ADV_F_BREDR_UNSUP;
    fields.tx_pwr_lvl_is_present = 1;
    fields.tx_pwr_lvl = BLE_HS_ADV_TX_PWR_LVL_AUTO;

    fields.name = (uint8_t *)ble_svc_gap_device_name();
    fields.name_len = strlen((char *)fields.name);
    fields.name_is_complete = 1;

    rc = ble_gap_adv_set_fields(&fields);
    if (rc != 0) {
        ESP_LOGE(TAG, "Failed to set advertising data; rc=%d", rc);
        return;
    }

    // Start advertising
    rc = ble_gap_adv_start(BLE_OWN_ADDR_PUBLIC, NULL, BLE_HS_FOREVER,
                           &adv_params, ble_gap_event, NULL);
    if (rc != 0) {
        ESP_LOGE(TAG, "Failed to start advertising; rc=%d", rc);
        return;
    }

    ble_adv_state.advertising_active = true;
    ble_adv_state.advertising_start_ms = (uint32_t)(esp_timer_get_time() / 1000);
    ESP_LOGI(TAG, "BLE advertising started");
}

// NimBLE host task
static void nimble_host_task(void *param) {
    ESP_LOGI(TAG, "NimBLE host task started");
    nimble_port_run();  // This function will block until nimble_port_stop()
    nimble_port_freertos_deinit();
}

static esp_err_t init_ble(void) {
    esp_err_t ret;

    printf("DEBUG BLE: Step 1 - NVS init\n");
    // Initialize NVS (required for BLE)
    ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        printf("DEBUG BLE: NVS needs erase\n");
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);
    printf("DEBUG BLE: NVS init OK\n");

    printf("DEBUG BLE: Step 2 - Release classic BT memory (SKIPPED - ESP32-C6 is BLE-only)\n");
    // ESP32-C6 is BLE-only, no classic BT to release
    // ESP_ERROR_CHECK(esp_bt_controller_mem_release(ESP_BT_MODE_CLASSIC_BT));
    printf("DEBUG BLE: Classic BT memory release skipped\n");

    // IMPORTANT: Manual BT controller init/enable removed - nimble_port_init() handles it internally
    // Root cause from BLE diagnostic investigation (Nov 5, 2025):
    // Manual esp_bt_controller_init() + esp_bt_controller_enable() conflicted with
    // NimBLE's internal controller initialization, causing zero serial output bug.
    // Fix: Let nimble_port_init() handle BT controller setup entirely.

    printf("DEBUG BLE: Step 3 - Init NimBLE port (handles BT controller internally)\n");
    // Initialize NimBLE host
    ret = nimble_port_init();
    if (ret != ESP_OK) {
        printf("DEBUG BLE: NimBLE port init FAILED: %s\n", esp_err_to_name(ret));
        ESP_LOGE(TAG, "NimBLE port init failed: %s", esp_err_to_name(ret));
        return ret;
    }
    printf("DEBUG BLE: NimBLE port init OK\n");

    printf("DEBUG BLE: Step 4 - Configure callbacks\n");
    // Configure NimBLE host callbacks
    ble_hs_cfg.reset_cb = ble_on_reset;
    ble_hs_cfg.sync_cb = ble_on_sync;
    ble_hs_cfg.gatts_register_cb = gatt_svr_register_cb;  // GATT service registration
    ble_hs_cfg.store_status_cb = ble_store_util_status_rr;
    printf("DEBUG BLE: Callbacks configured\n");

    printf("DEBUG BLE: Step 4.5 - Initialize GATT services\n");
    // Initialize GATT services (must happen before NimBLE host task starts)
    ret = gatt_svr_init();
    if (ret != ESP_OK) {
        printf("DEBUG BLE: GATT service init FAILED\n");
        ESP_LOGE(TAG, "GATT service init failed");
        return ret;
    }
    printf("DEBUG BLE: GATT services initialized\n");

    printf("DEBUG BLE: Step 5 - Start NimBLE host task\n");
    // Start NimBLE host task
    nimble_port_freertos_init(nimble_host_task);
    printf("DEBUG BLE: NimBLE host task started\n");

    ESP_LOGI(TAG, "NimBLE initialized");
    return ESP_OK;
}

// BLE ADVERTISING CONTROL
static void ble_start_advertising(void) {
    if (!ble_adv_state.advertising_active) {
        int rc = ble_gap_adv_start(BLE_OWN_ADDR_PUBLIC, NULL, BLE_HS_FOREVER,
                                    &adv_params, ble_gap_event, NULL);
        if (rc == 0) {
            ble_adv_state.advertising_active = true;
            ble_adv_state.advertising_start_ms = (uint32_t)(esp_timer_get_time() / 1000);
            ESP_LOGI(TAG, "BLE advertising re-enabled");
        } else {
            ESP_LOGE(TAG, "Failed to restart advertising; rc=%d", rc);
        }
    }
}

static void ble_stop_advertising(void) {
    if (ble_adv_state.advertising_active) {
        int rc = ble_gap_adv_stop();
        if (rc == 0) {
            ble_adv_state.advertising_active = false;
            ESP_LOGI(TAG, "BLE advertising stopped");
        } else {
            ESP_LOGE(TAG, "Failed to stop advertising; rc=%d", rc);
        }
    }
}

// BLE TASK - handles advertising timeout and message queue
static void ble_task(void *pvParameters) {
    task_message_t msg;
    ble_state_t state = BLE_STATE_IDLE;

    ESP_LOGI(TAG, "BLE task started");

    while (state != BLE_STATE_SHUTDOWN) {
        uint32_t now = (uint32_t)(esp_timer_get_time() / 1000);

        switch (state) {
            case BLE_STATE_IDLE: {
                // Check for messages
                if (xQueueReceive(button_to_ble_queue, &msg, pdMS_TO_TICKS(1000)) == pdTRUE) {
                    if (msg.type == MSG_BLE_REENABLE) {
                        ESP_LOGI(TAG, "BLE re-enable requested");
                        ble_start_advertising();

                        // Transition based on result
                        if (ble_adv_state.advertising_active) {
                            state = BLE_STATE_ADVERTISING;
                        }
                    } else if (msg.type == MSG_EMERGENCY_SHUTDOWN) {
                        ESP_LOGI(TAG, "BLE shutdown requested");
                        state = BLE_STATE_SHUTDOWN;
                        break;
                    }
                }

                // Check if connection established (via GAP event)
                if (ble_adv_state.client_connected) {
                    ESP_LOGI(TAG, "BLE client connected (from IDLE)");
                    state = BLE_STATE_CONNECTED;
                }
                break;
            }

            case BLE_STATE_ADVERTISING: {
                // Check for shutdown message
                if (xQueueReceive(button_to_ble_queue, &msg, pdMS_TO_TICKS(100)) == pdTRUE) {
                    if (msg.type == MSG_EMERGENCY_SHUTDOWN) {
                        ESP_LOGI(TAG, "BLE shutdown during advertising");
                        ble_stop_advertising();
                        state = BLE_STATE_SHUTDOWN;
                        break;
                    }
                }

                // Check for client connection (set by GAP event handler)
                if (ble_adv_state.client_connected) {
                    ESP_LOGI(TAG, "BLE client connected");
                    state = BLE_STATE_CONNECTED;
                    break;
                }

                // Check advertising timeout (5 minutes)
                if (ble_adv_state.advertising_active) {
                    uint32_t elapsed = now - ble_adv_state.advertising_start_ms;

                    if (elapsed >= ble_adv_state.advertising_timeout_ms) {
                        ESP_LOGI(TAG, "BLE advertising timeout (5 min)");
                        ble_stop_advertising();
                        state = BLE_STATE_IDLE;
                    }
                } else {
                    // Advertising stopped externally, return to idle
                    state = BLE_STATE_IDLE;
                }
                break;
            }

            case BLE_STATE_CONNECTED: {
                // Check for shutdown message
                if (xQueueReceive(button_to_ble_queue, &msg, pdMS_TO_TICKS(100)) == pdTRUE) {
                    if (msg.type == MSG_EMERGENCY_SHUTDOWN) {
                        ESP_LOGI(TAG, "BLE shutdown during connection");
                        // Client disconnect is handled by GAP event handler
                        state = BLE_STATE_SHUTDOWN;
                        break;
                    }
                }

                // Check if client disconnected (set by GAP event handler)
                if (!ble_adv_state.client_connected) {
                    ESP_LOGI(TAG, "BLE client disconnected");

                    // GAP event handler automatically restarts advertising
                    if (ble_adv_state.advertising_active) {
                        state = BLE_STATE_ADVERTISING;
                    } else {
                        state = BLE_STATE_IDLE;
                    }
                }
                break;
            }

            case BLE_STATE_SHUTDOWN: {
                // Loop exit handled by while condition
                break;
            }
        }

        vTaskDelay(pdMS_TO_TICKS(1000));
    }

    // Cleanup section
    ESP_LOGI(TAG, "BLE task cleanup");

    // Stop advertising if active
    if (ble_adv_state.advertising_active) {
        ble_stop_advertising();
    }

    // Note: Full BLE stack deinit (nimble_port_stop/deinit) could be added here
    // but may cause issues if motor task enters deep sleep immediately

    ESP_LOGI(TAG, "BLE task exiting");
    vTaskDelete(NULL);
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

            // Feed watchdog during purple blink (motor_task subscribed at task start)
            esp_task_wdt_reset();

            vTaskDelay(pdMS_TO_TICKS(PURPLE_BLINK_MS));
        }
    }
    
    led_clear();
    gpio_set_level(GPIO_WS2812B_ENABLE, 1);
    gpio_set_level(GPIO_STATUS_LED, LED_OFF);

    // Save Mode 5 settings to NVS before deep sleep
    save_mode5_settings_to_nvs();

    ESP_LOGI(TAG, "Entering deep sleep");
    vTaskDelay(pdMS_TO_TICKS(100));

    // Disable power management before deep sleep to prevent spurious wakes
    // PM light sleep wake sources can interfere with deep sleep wake configuration
    esp_pm_config_t pm_config_sleep = {
        .max_freq_mhz = 160,
        .min_freq_mhz = 160,        // Disable frequency scaling
        .light_sleep_enable = false  // Disable light sleep before deep sleep
    };
    esp_pm_configure(&pm_config_sleep);
    ESP_LOGI(TAG, "PM disabled for clean deep sleep");

    vTaskDelay(pdMS_TO_TICKS(50));  // Let PM changes settle

    esp_sleep_enable_ext1_wakeup((1ULL << GPIO_BUTTON), ESP_EXT1_WAKEUP_ANY_LOW);
    esp_deep_sleep_start();
}

// BUTTON TASK - sends messages to motor
static void button_task(void *pvParameters) {
    button_state_t state = BTN_STATE_IDLE;
    uint32_t press_start = 0;
    mode_t local_mode = MODE_1HZ_50;
    uint32_t boot_time = (uint32_t)(esp_timer_get_time() / 1000);  // Boot time in ms

    ESP_LOGI(TAG, "Button task started");

    while (1) {
        bool button_pressed = (gpio_get_level(GPIO_BUTTON) == 0);
        uint32_t now = (uint32_t)(esp_timer_get_time() / 1000);
        uint32_t duration = (press_start > 0) ? (now - press_start) : 0;

        switch (state) {
            case BTN_STATE_IDLE:
                if (button_pressed) {
                    press_start = now;
                    state = BTN_STATE_DEBOUNCE;
                }
                break;

            case BTN_STATE_DEBOUNCE:
                if (!button_pressed) {
                    state = BTN_STATE_IDLE;
                } else if (duration >= BUTTON_DEBOUNCE_MS) {
                    state = BTN_STATE_PRESSED;
                }
                break;

            case BTN_STATE_PRESSED:
                if (!button_pressed) {
                    // Short press - mode cycle
                    local_mode = (local_mode + 1) % MODE_COUNT;
                    ESP_LOGI(TAG, "Mode change: %s", modes[local_mode].name);

                    task_message_t msg = {.type = MSG_MODE_CHANGE, .data.new_mode = local_mode};
                    xQueueSend(button_to_motor_queue, &msg, pdMS_TO_TICKS(100));

                    state = BTN_STATE_IDLE;
                } else if (duration >= BUTTON_HOLD_DETECT_MS) {
                    ESP_LOGI(TAG, "Hold detected (1s)");
                    status_led_on();
                    state = BTN_STATE_HOLD_DETECT;
                }
                break;

            case BTN_STATE_HOLD_DETECT:
                if (!button_pressed) {
                    // Released during 1s-2s window - BLE re-enable
                    ESP_LOGI(TAG, "BLE re-enable triggered");
                    status_led_blink(3, 100, 100);

                    task_message_t msg = {.type = MSG_BLE_REENABLE};
                    xQueueSend(button_to_ble_queue, &msg, pdMS_TO_TICKS(100));

                    state = BTN_STATE_IDLE;
                } else if (duration >= BUTTON_BLE_REENABLE_MS) {
                    ESP_LOGI(TAG, "Shutdown hold detected (2s)");
                    state = BTN_STATE_SHUTDOWN_HOLD;
                }
                break;

            case BTN_STATE_SHUTDOWN_HOLD:
                // Check for NVS clear (15s hold within 30s boot window)
                if (duration >= BUTTON_NVS_CLEAR_MS) {
                    uint32_t uptime = now - boot_time;
                    if (uptime < BUTTON_NVS_CLEAR_WINDOW_MS) {
                        ESP_LOGI(TAG, "Button held ≥15s within 30s window, NVS clear triggered");
                        ESP_LOGI(TAG, "Factory reset: Clearing NVS settings");

                        // Clear purple LED before NVS operations
                        led_clear();

                        // Clear NVS
                        esp_err_t ret = nvs_clear_all();
                        if (ret == ESP_OK) {
                            ESP_LOGI(TAG, "NVS cleared successfully");
                            // Flash status LED to indicate success
                            for (int i = 0; i < 3; i++) {
                                status_led_on();
                                vTaskDelay(pdMS_TO_TICKS(100));
                                status_led_off();
                                vTaskDelay(pdMS_TO_TICKS(100));
                            }
                        } else {
                            ESP_LOGE(TAG, "NVS clear failed: %s", esp_err_to_name(ret));
                        }

                        // Wait for button release
                        ESP_LOGI(TAG, "Waiting for button release after NVS clear");
                        while (gpio_get_level(GPIO_BUTTON) == 0) {
                            vTaskDelay(pdMS_TO_TICKS(100));
                        }

                        // After factory reset, proceed to shutdown for clean restart
                        ESP_LOGI(TAG, "NVS cleared - proceeding to shutdown");
                        state = BTN_STATE_SHUTDOWN;
                        break;
                    }
                }

                // Normal shutdown (not NVS clear)
                ESP_LOGI(TAG, "Emergency shutdown...");
                state = BTN_STATE_COUNTDOWN;
                break;

            case BTN_STATE_COUNTDOWN:
                {
                    bool cancelled = false;
                    for (int i = BUTTON_COUNTDOWN_SEC; i > 0; i--) {
                        ESP_LOGI(TAG, "%d...", i);
                        vTaskDelay(pdMS_TO_TICKS(1000));
                        if (gpio_get_level(GPIO_BUTTON) == 1) {
                            ESP_LOGI(TAG, "Countdown cancelled");
                            status_led_off();
                            cancelled = true;
                            state = BTN_STATE_IDLE;
                            break;
                        }
                    }

                    if (!cancelled) {
                        state = BTN_STATE_SHUTDOWN;
                    }
                }
                break;

            case BTN_STATE_SHUTDOWN:
                status_led_off();
                task_message_t msg = {.type = MSG_EMERGENCY_SHUTDOWN};
                xQueueSend(button_to_motor_queue, &msg, pdMS_TO_TICKS(100));
                xQueueSend(button_to_ble_queue, &msg, pdMS_TO_TICKS(100));  // Shutdown BLE too
                ESP_LOGI(TAG, "Shutdown messages sent to motor and BLE tasks");
                state = BTN_STATE_SHUTDOWN_SENT;  // Transition to terminal state
                break;

            case BTN_STATE_SHUTDOWN_SENT:
                // Terminal state - do nothing, waiting for deep sleep
                // Motor task handles purple blink and deep sleep entry
                break;
        }

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

// Helper: vTaskDelay that checks for mode changes periodically
// Returns: true if mode change detected, false if delay completed normally
static bool delay_with_mode_check(uint32_t delay_ms) {
    const uint32_t CHECK_INTERVAL_MS = 50; // Check every 50ms for responsiveness
    uint32_t remaining_ms = delay_ms;

    while (remaining_ms > 0) {
        uint32_t this_delay = (remaining_ms < CHECK_INTERVAL_MS) ? remaining_ms : CHECK_INTERVAL_MS;
        vTaskDelay(pdMS_TO_TICKS(this_delay));
        remaining_ms -= this_delay;

        // Quick check for BLE parameter updates (instant response)
        if (ble_params_updated) {
            return true; // BLE parameters changed - reload immediately
        }

        // Quick check for mode change or shutdown (non-blocking peek)
        task_message_t msg;
        if (xQueuePeek(button_to_motor_queue, &msg, 0) == pdPASS) {
            if (msg.type == MSG_MODE_CHANGE || msg.type == MSG_EMERGENCY_SHUTDOWN) {
                return true; // Mode change or shutdown detected
            }
        }
    }

    return false; // Delay completed normally
}

// MOTOR TASK - 10-state machine with instant mode switching
static void motor_task(void *pvParameters) {
    motor_state_t state = MOTOR_STATE_CHECK_MESSAGES;
    mode_t current_mode = MODE_1HZ_50;
    uint32_t session_start_ms = (uint32_t)(esp_timer_get_time() / 1000);
    uint32_t led_indication_start_ms = session_start_ms;
    bool led_indication_active = true;

    // Motor timing variables (updated when mode changes)
    uint32_t motor_on_ms = 0;
    uint32_t coast_ms = 0;
    uint8_t pwm_intensity = 0;
    bool show_led = false;

    // Back-EMF sampling flag and storage
    bool sample_backemf = false;
    int raw_mv_drive = 0, raw_mv_immed = 0, raw_mv_settled = 0;
    int16_t bemf_drive = 0, bemf_immed = 0, bemf_settled = 0;

    // Phase tracking for shared back-EMF states
    bool in_forward_phase = true;

    // Initialize session timestamp for BLE
    session_start_time_ms = session_start_ms;
    current_mode_ble = current_mode;

    // Subscribe to watchdog (needed for purple blink loop in enter_deep_sleep)
    ESP_ERROR_CHECK(esp_task_wdt_add(NULL));

    ESP_LOGI(TAG, "Motor task started: %s", modes[current_mode].name);

    while (state != MOTOR_STATE_SHUTDOWN) {
        uint32_t now = (uint32_t)(esp_timer_get_time() / 1000);
        uint32_t elapsed = now - session_start_ms;

        switch (state) {
            case MOTOR_STATE_CHECK_MESSAGES: {
                // Feed watchdog every cycle
                esp_task_wdt_reset();

                // Check for emergency shutdown and mode changes
                task_message_t msg;
                while (xQueueReceive(button_to_motor_queue, &msg, 0) == pdPASS) {
                    if (msg.type == MSG_EMERGENCY_SHUTDOWN) {
                        ESP_LOGI(TAG, "Emergency shutdown");
                        state = MOTOR_STATE_SHUTDOWN;
                        break;
                    } else if (msg.type == MSG_MODE_CHANGE) {
                        // Process LAST mode change only (purge queue)
                        mode_t new_mode = msg.data.new_mode;
                        while (xQueuePeek(button_to_motor_queue, &msg, 0) == pdPASS) {
                            if (msg.type == MSG_MODE_CHANGE) {
                                xQueueReceive(button_to_motor_queue, &msg, 0);
                                new_mode = msg.data.new_mode;
                            } else {
                                break;
                            }
                        }

                        if (new_mode != current_mode) {
                            current_mode = new_mode;
                            current_mode_ble = new_mode;
                            ESP_LOGI(TAG, "Mode: %s", modes[current_mode].name);
                            led_indication_active = true;
                            led_indication_start_ms = now;
                        }
                    }
                }

                // Check battery messages
                if (xQueueReceive(battery_to_motor_queue, &msg, 0) == pdPASS) {
                    if (msg.type == MSG_BATTERY_CRITICAL) {
                        ESP_LOGW(TAG, "Critical battery: %.2fV", msg.data.battery.voltage);
                        state = MOTOR_STATE_SHUTDOWN;
                        break;
                    }
                }

                // Check session timeout
                if (elapsed >= SESSION_DURATION_MS) {
                    ESP_LOGI(TAG, "Session complete (20 min)");
                    state = MOTOR_STATE_SHUTDOWN;
                    break;
                }

                // Update motor parameters based on current mode
                bool last_minute = (elapsed >= WARNING_START_MS);

                if (current_mode == MODE_CUSTOM) {
                    motor_on_ms = mode5_motor_on_ms;
                    coast_ms = mode5_coast_ms;
                    pwm_intensity = mode5_pwm_intensity;
                    show_led = mode5_led_enable || last_minute;
                } else {
                    motor_on_ms = modes[current_mode].motor_on_ms;
                    coast_ms = modes[current_mode].coast_ms;
                    pwm_intensity = PWM_INTENSITY_PERCENT;
                    show_led = led_indication_active || last_minute;
                }

                // Clear BLE parameter update flag (parameters have been reloaded)
                ble_params_updated = false;

                // Update back-EMF sampling flag (first 10 seconds after mode change)
                sample_backemf = led_indication_active && ((now - led_indication_start_ms) < LED_INDICATION_TIME_MS);

                // Disable LED indication after 10 seconds
                if (led_indication_active && ((now - led_indication_start_ms) >= LED_INDICATION_TIME_MS)) {
                    led_indication_active = false;
                    led_clear();
                    ESP_LOGI(TAG, "LED off (battery conservation)");
                }

                // Don't transition to FORWARD if shutting down
                if (state == MOTOR_STATE_SHUTDOWN) {
                    break;
                }

                // Transition to FORWARD
                state = MOTOR_STATE_FORWARD_ACTIVE;
                break;
            }

            case MOTOR_STATE_FORWARD_ACTIVE: {
                // Start motor forward
                motor_forward(pwm_intensity);
                if (show_led) led_set_mode_color(current_mode);

                // Mark that we're in forward phase
                in_forward_phase = true;

                if (sample_backemf) {
                    // Shortened active time for back-EMF sampling
                    uint32_t active_time = (motor_on_ms > 10) ? (motor_on_ms - 10) : motor_on_ms;

                    if (delay_with_mode_check(active_time)) {
                        motor_coast();
                        led_clear();
                        state = MOTOR_STATE_CHECK_MESSAGES;
                        break;
                    }

                    // Sample #1: During active drive
                    read_backemf(&raw_mv_drive, &bemf_drive);

                    // Short delay before coasting
                    vTaskDelay(pdMS_TO_TICKS(10));

                    // Transition to shared immediate back-EMF sample state
                    state = MOTOR_STATE_BEMF_IMMEDIATE;
                } else {
                    // Full active time, no sampling
                    if (delay_with_mode_check(motor_on_ms)) {
                        motor_coast();
                        led_clear();
                        state = MOTOR_STATE_CHECK_MESSAGES;
                        break;
                    }

                    // CRITICAL: Always coast motor and clear LED!
                    motor_coast();
                    led_clear();

                    // Skip back-EMF states, go straight to coast remaining
                    state = MOTOR_STATE_FORWARD_COAST_REMAINING;
                }
                break;
            }

            case MOTOR_STATE_BEMF_IMMEDIATE: {
                // Coast motor and clear LED
                motor_coast();
                led_clear();

                // Sample #2: Immediately after coast starts
                read_backemf(&raw_mv_immed, &bemf_immed);

                // Transition to settling state (shared)
                state = MOTOR_STATE_COAST_SETTLE;
                break;
            }

            case MOTOR_STATE_COAST_SETTLE: {
                // Wait for back-EMF to settle
                if (delay_with_mode_check(BACKEMF_SETTLE_MS)) {
                    state = MOTOR_STATE_CHECK_MESSAGES;
                    break;
                }

                // Sample #3: Settled back-EMF reading
                read_backemf(&raw_mv_settled, &bemf_settled);

                // Log readings with direction label
                if (in_forward_phase) {
                    ESP_LOGI(TAG, "FWD: %dmV→%+dmV | %dmV→%+dmV | %dmV→%+dmV",
                             raw_mv_drive, bemf_drive, raw_mv_immed, bemf_immed,
                             raw_mv_settled, bemf_settled);
                } else {
                    ESP_LOGI(TAG, "REV: %dmV→%+dmV | %dmV→%+dmV | %dmV→%+dmV",
                             raw_mv_drive, bemf_drive, raw_mv_immed, bemf_immed,
                             raw_mv_settled, bemf_settled);
                }

                // Transition to appropriate COAST_REMAINING state based on phase
                if (in_forward_phase) {
                    state = MOTOR_STATE_FORWARD_COAST_REMAINING;
                } else {
                    state = MOTOR_STATE_REVERSE_COAST_REMAINING;
                }
                break;
            }

            case MOTOR_STATE_FORWARD_COAST_REMAINING: {
                // Calculate remaining coast time
                uint32_t remaining_coast;
                if (sample_backemf) {
                    // Already spent BACKEMF_SETTLE_MS, finish the rest
                    remaining_coast = (coast_ms > BACKEMF_SETTLE_MS) ? (coast_ms - BACKEMF_SETTLE_MS) : 0;
                } else {
                    // Full coast time
                    remaining_coast = coast_ms;
                }

                if (remaining_coast > 0) {
                    if (delay_with_mode_check(remaining_coast)) {
                        state = MOTOR_STATE_CHECK_MESSAGES;
                        break;
                    }
                }

                // Transition to REVERSE phase
                state = MOTOR_STATE_REVERSE_ACTIVE;
                break;
            }

            case MOTOR_STATE_REVERSE_ACTIVE: {
                // Start motor reverse
                motor_reverse(pwm_intensity);
                if (show_led) led_set_mode_color(current_mode);

                // Mark that we're in reverse phase
                in_forward_phase = false;

                if (sample_backemf) {
                    // Shortened active time for back-EMF sampling
                    uint32_t active_time = (motor_on_ms > 10) ? (motor_on_ms - 10) : motor_on_ms;

                    if (delay_with_mode_check(active_time)) {
                        motor_coast();
                        led_clear();
                        state = MOTOR_STATE_CHECK_MESSAGES;
                        break;
                    }

                    // Sample #1: During active drive
                    read_backemf(&raw_mv_drive, &bemf_drive);

                    // Short delay before coasting
                    vTaskDelay(pdMS_TO_TICKS(10));

                    // Transition to shared immediate back-EMF sample state
                    state = MOTOR_STATE_BEMF_IMMEDIATE;
                } else {
                    // Full active time, no sampling
                    if (delay_with_mode_check(motor_on_ms)) {
                        motor_coast();
                        led_clear();
                        state = MOTOR_STATE_CHECK_MESSAGES;
                        break;
                    }

                    // CRITICAL: Always coast motor and clear LED!
                    motor_coast();
                    led_clear();

                    // Skip back-EMF states, go straight to coast remaining
                    state = MOTOR_STATE_REVERSE_COAST_REMAINING;
                }
                break;
            }

            case MOTOR_STATE_REVERSE_COAST_REMAINING: {
                // Calculate remaining coast time
                uint32_t remaining_coast;
                if (sample_backemf) {
                    // Already spent BACKEMF_SETTLE_MS, finish the rest
                    remaining_coast = (coast_ms > BACKEMF_SETTLE_MS) ? (coast_ms - BACKEMF_SETTLE_MS) : 0;
                } else {
                    // Full coast time
                    remaining_coast = coast_ms;
                }

                if (remaining_coast > 0) {
                    if (delay_with_mode_check(remaining_coast)) {
                        state = MOTOR_STATE_CHECK_MESSAGES;
                        break;
                    }
                }

                // Cycle complete, check messages again
                state = MOTOR_STATE_CHECK_MESSAGES;
                break;
            }

            case MOTOR_STATE_SHUTDOWN: {
                // Loop exit handled by while condition
                break;
            }
        }
    }

    // Final cleanup
    motor_coast();
    led_clear();
    vTaskDelay(pdMS_TO_TICKS(100));

    // Always enter deep sleep on shutdown (never returns)
    // This handles: emergency shutdown, battery critical, and session timeout
    enter_deep_sleep();

    // Never reached, but kept for safety
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
        ESP_LOGE(TAG, "Failed to create button_to_motor queue");
        return ESP_FAIL;
    }

    battery_to_motor_queue = xQueueCreate(BATTERY_TO_MOTOR_QUEUE_SIZE, sizeof(task_message_t));
    if (battery_to_motor_queue == NULL) {
        ESP_LOGE(TAG, "Failed to create battery_to_motor queue");
        return ESP_FAIL;
    }

    button_to_ble_queue = xQueueCreate(BUTTON_TO_BLE_QUEUE_SIZE, sizeof(task_message_t));
    if (button_to_ble_queue == NULL) {
        ESP_LOGE(TAG, "Failed to create button_to_ble queue");
        return ESP_FAIL;
    }

    ESP_LOGI(TAG, "Message queues initialized");
    return ESP_OK;
}

// MAIN
void app_main(void) {
    // Use printf first to bypass any logging system issues
    printf("\n\n=== APP_MAIN STARTED ===\n");

    ESP_LOGI(TAG, "========================================");
    ESP_LOGI(TAG, "Phase A: BLE GATT Server Integration");
    ESP_LOGI(TAG, "Features: Message Queues + BLE + Button Control");
    ESP_LOGI(TAG, "========================================");

    esp_sleep_wakeup_cause_t reason = esp_sleep_get_wakeup_cause();
    ESP_LOGI(TAG, "Wake: %s", reason == ESP_SLEEP_WAKEUP_EXT1 ? "Button" : "Power on");

    printf("DEBUG: About to init GPIO\n");
    init_gpio();
    printf("DEBUG: GPIO init complete\n");

    vTaskDelay(pdMS_TO_TICKS(50));

    printf("DEBUG: About to init ADC\n");
    init_adc();
    printf("DEBUG: ADC init complete\n");

    printf("DEBUG: About to init LED\n");
    init_led();
    printf("DEBUG: LED init complete\n");

    printf("DEBUG: About to init PWM\n");
    init_pwm();
    printf("DEBUG: PWM init complete\n");

    printf("DEBUG: About to motor coast\n");
    motor_coast();
    printf("DEBUG: Motor coast complete\n");

    printf("DEBUG: About to init queues\n");
    if (init_queues() != ESP_OK) {
        ESP_LOGE(TAG, "Queue init failed!");
        while(1) vTaskDelay(pdMS_TO_TICKS(1000));
    }
    printf("DEBUG: Queues init complete\n");

    printf("DEBUG: About to init BLE\n");
    if (init_ble() != ESP_OK) {
        ESP_LOGE(TAG, "BLE init failed!");
        while(1) vTaskDelay(pdMS_TO_TICKS(1000));
    }
    printf("DEBUG: BLE init complete\n");

    // Initialize Mode 5 settings mutex
    printf("DEBUG: About to create Mode 5 settings mutex\n");
    mode5_settings_mutex = xSemaphoreCreateMutex();
    if (mode5_settings_mutex == NULL) {
        ESP_LOGE(TAG, "Failed to create Mode 5 settings mutex");
    } else {
        ESP_LOGI(TAG, "Mode 5 settings mutex created successfully");
    }
    printf("DEBUG: Mode 5 settings mutex creation complete\n");

    // Load Mode 5 settings from NVS (if present)
    printf("DEBUG: About to load Mode 5 settings from NVS\n");
    load_mode5_settings_from_nvs();
    printf("DEBUG: Mode 5 settings load complete\n");

    if (!check_low_voltage_cutout()) {
        ESP_LOGE(TAG, "LVO failed!");
        while(1) vTaskDelay(pdMS_TO_TICKS(1000));
    }

    // Configure automatic power management for light sleep during idle
    // This enables automatic light sleep when all FreeRTOS tasks are blocked (vTaskDelay)
    // BLE stack is compatible - it will wake for radio events automatically
    ESP_LOGI(TAG, "Configuring automatic light sleep...");
    esp_pm_config_t pm_config = {
        .max_freq_mhz = 160,        // Max CPU frequency during active operation
        .min_freq_mhz = 80,         // Min CPU frequency (80MHz safe for BLE radio timing)
        .light_sleep_enable = true  // Enable automatic light sleep during vTaskDelay
    };
    esp_err_t pm_ret = esp_pm_configure(&pm_config);
    if (pm_ret == ESP_OK) {
        ESP_LOGI(TAG, "Automatic light sleep enabled (160MHz max, 80MHz min for BLE safety)");
        ESP_LOGI(TAG, "Expected power savings: ~10-20mA during motor coast periods");
        ESP_LOGI(TAG, "Note: Light sleep provides main savings, not CPU frequency scaling");
    } else {
        ESP_LOGW(TAG, "PM configure failed: %s (continuing anyway)", esp_err_to_name(pm_ret));
    }

    ESP_LOGI(TAG, "Starting tasks...");

    xTaskCreate(motor_task, "motor", 4096, NULL, 5, NULL);
    xTaskCreate(button_task, "button", 2048, NULL, 4, NULL);
    xTaskCreate(battery_task, "battery", 2048, NULL, 3, NULL);
    xTaskCreate(ble_task, "ble", 3072, NULL, 2, NULL);

    ESP_LOGI(TAG, "All tasks started successfully");
}
