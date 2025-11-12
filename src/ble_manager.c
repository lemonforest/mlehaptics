/**
 * @file ble_manager.c
 * @brief BLE Manager Module Implementation - Configuration Service per AD032
 *
 * Implements NimBLE GATT Configuration Service for mobile app control.
 * Production UUIDs (6E400002-...), 12 characteristics, full RGB support.
 *
 * @date November 11, 2025
 * @author Claude Code (Anthropic)
 */

#include "ble_manager.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include "nvs.h"
#include "esp_crc.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"
#include "esp_timer.h"

// NimBLE includes
#include "host/ble_hs.h"
#include "host/ble_uuid.h"
#include "host/ble_gap.h"
#include "host/ble_gatt.h"
#include "services/gap/ble_svc_gap.h"
#include "services/gatt/ble_svc_gatt.h"
#include "nimble/nimble_port.h"
#include "nimble/nimble_port_freertos.h"
#include "store/config/ble_store_config.h"

static const char *TAG = "BLE_MANAGER";

// ============================================================================
// BLE SERVICE UUIDs (Production - AD032)
// ============================================================================

// Configuration Service: 6E400002-B5A3-F393-E0A9-E50E24DCCA9E (13th byte = 02)
// Characteristics: 6E400X02-B5A3-... where X = 01, 02, 03... 0C (14th byte)

// NOTE: BLE_UUID128_INIT expects bytes in REVERSE order (little-endian)
// UUID format: 6E 40 0X 02 - B5 A3 - F3 93 - E0 A9 - E5 0E 24 DC CA 9E
// Reversed:    9E CA DC 24 0E E5 A9 E0 93 F3 A3 B5 02 0X 40 6E
//                                                  ↑  ↑
//                                               13th 14th

static const ble_uuid128_t uuid_config_service = BLE_UUID128_INIT(
    0x9e, 0xca, 0xdc, 0x24, 0x0e, 0xe5, 0xa9, 0xe0,
    0x93, 0xf3, 0xa3, 0xb5, 0x02, 0x00, 0x40, 0x6e);

// Motor Control Group
static const ble_uuid128_t uuid_char_mode = BLE_UUID128_INIT(
    0x9e, 0xca, 0xdc, 0x24, 0x0e, 0xe5, 0xa9, 0xe0,
    0x93, 0xf3, 0xa3, 0xb5, 0x02, 0x01, 0x40, 0x6e);

static const ble_uuid128_t uuid_char_custom_freq = BLE_UUID128_INIT(
    0x9e, 0xca, 0xdc, 0x24, 0x0e, 0xe5, 0xa9, 0xe0,
    0x93, 0xf3, 0xa3, 0xb5, 0x02, 0x02, 0x40, 0x6e);

static const ble_uuid128_t uuid_char_custom_duty = BLE_UUID128_INIT(
    0x9e, 0xca, 0xdc, 0x24, 0x0e, 0xe5, 0xa9, 0xe0,
    0x93, 0xf3, 0xa3, 0xb5, 0x02, 0x03, 0x40, 0x6e);

static const ble_uuid128_t uuid_char_pwm_intensity = BLE_UUID128_INIT(
    0x9e, 0xca, 0xdc, 0x24, 0x0e, 0xe5, 0xa9, 0xe0,
    0x93, 0xf3, 0xa3, 0xb5, 0x02, 0x04, 0x40, 0x6e);

// LED Control Group
static const ble_uuid128_t uuid_char_led_enable = BLE_UUID128_INIT(
    0x9e, 0xca, 0xdc, 0x24, 0x0e, 0xe5, 0xa9, 0xe0,
    0x93, 0xf3, 0xa3, 0xb5, 0x02, 0x05, 0x40, 0x6e);

static const ble_uuid128_t uuid_char_led_color_mode = BLE_UUID128_INIT(
    0x9e, 0xca, 0xdc, 0x24, 0x0e, 0xe5, 0xa9, 0xe0,
    0x93, 0xf3, 0xa3, 0xb5, 0x02, 0x06, 0x40, 0x6e);

static const ble_uuid128_t uuid_char_led_palette = BLE_UUID128_INIT(
    0x9e, 0xca, 0xdc, 0x24, 0x0e, 0xe5, 0xa9, 0xe0,
    0x93, 0xf3, 0xa3, 0xb5, 0x02, 0x07, 0x40, 0x6e);

static const ble_uuid128_t uuid_char_led_custom_rgb = BLE_UUID128_INIT(
    0x9e, 0xca, 0xdc, 0x24, 0x0e, 0xe5, 0xa9, 0xe0,
    0x93, 0xf3, 0xa3, 0xb5, 0x02, 0x08, 0x40, 0x6e);

static const ble_uuid128_t uuid_char_led_brightness = BLE_UUID128_INIT(
    0x9e, 0xca, 0xdc, 0x24, 0x0e, 0xe5, 0xa9, 0xe0,
    0x93, 0xf3, 0xa3, 0xb5, 0x02, 0x09, 0x40, 0x6e);

// Status/Monitoring Group
static const ble_uuid128_t uuid_char_session_duration = BLE_UUID128_INIT(
    0x9e, 0xca, 0xdc, 0x24, 0x0e, 0xe5, 0xa9, 0xe0,
    0x93, 0xf3, 0xa3, 0xb5, 0x02, 0x0a, 0x40, 0x6e);

static const ble_uuid128_t uuid_char_session_time = BLE_UUID128_INIT(
    0x9e, 0xca, 0xdc, 0x24, 0x0e, 0xe5, 0xa9, 0xe0,
    0x93, 0xf3, 0xa3, 0xb5, 0x02, 0x0b, 0x40, 0x6e);

static const ble_uuid128_t uuid_char_battery = BLE_UUID128_INIT(
    0x9e, 0xca, 0xdc, 0x24, 0x0e, 0xe5, 0xa9, 0xe0,
    0x93, 0xf3, 0xa3, 0xb5, 0x02, 0x0c, 0x40, 0x6e);

// ============================================================================
// MODE 5 LED COLOR PALETTE (16 colors)
// ============================================================================

const rgb_color_t color_palette[16] = {
    {255, 0,   0,   "Red"},
    {0,   255, 0,   "Green"},
    {0,   0,   255, "Blue"},
    {255, 255, 0,   "Yellow"},
    {0,   255, 255, "Cyan"},
    {255, 0,   255, "Magenta"},
    {255, 128, 0,   "Orange"},
    {128, 0,   255, "Purple"},
    {0,   255, 128, "Spring Green"},
    {255, 192, 203, "Pink"},
    {255, 255, 255, "White"},
    {128, 128, 0,   "Olive"},
    {0,   128, 128, "Teal"},
    {128, 0,   128, "Violet"},
    {64,  224, 208, "Turquoise"},
    {255, 140, 0,   "Dark Orange"}
};

// ============================================================================
// BLE STATE VARIABLES
// ============================================================================

// Characteristic data (protected by mutex) - AD032 defaults
static ble_char_data_t char_data = {
    .current_mode = MODE_1HZ_50,
    .custom_frequency_hz = 100,  // 1.00 Hz
    .custom_duty_percent = 50,
    .pwm_intensity = 75,
    .led_enable = true,  // Enable LED by default for custom mode
    .led_color_mode = LED_COLOR_MODE_CUSTOM_RGB,  // Default: custom RGB
    .led_palette_index = 0,
    .led_custom_r = 255,  // Default: Red
    .led_custom_g = 0,
    .led_custom_b = 0,
    .led_brightness = 20,
    .session_duration_sec = 1200,  // 20 minutes
    .session_time_sec = 0,
    .battery_level = 0
};

static SemaphoreHandle_t char_data_mutex = NULL;

// Advertising state
typedef struct {
    bool advertising_active;
    bool client_connected;
    uint32_t advertising_start_ms;
} ble_advertising_state_t;

static ble_advertising_state_t adv_state = {
    .advertising_active = false,
    .client_connected = false,
    .advertising_start_ms = 0
};

// Settings dirty flag (thread-safe via char_data_mutex)
static bool settings_dirty = false;

// NimBLE advertising parameters
static struct ble_gap_adv_params adv_params = {
    .conn_mode = BLE_GAP_CONN_MODE_UND,  // Undirected connectable
    .disc_mode = BLE_GAP_DISC_MODE_GEN,  // General discoverable
    .itvl_min = 0x20,                     // 20ms
    .itvl_max = 0x40,                     // 40ms
};

// ============================================================================
// NVS PERSISTENCE (User Preferences)
// ============================================================================

#define NVS_NAMESPACE            "emdr_cfg"
#define NVS_KEY_SIGNATURE        "sig"
#define NVS_KEY_MODE             "mode"
#define NVS_KEY_FREQUENCY        "freq"
#define NVS_KEY_DUTY             "duty"
#define NVS_KEY_LED_ENABLE       "led_en"
#define NVS_KEY_LED_COLOR_MODE   "led_cmode"
#define NVS_KEY_LED_PALETTE      "led_pal"
#define NVS_KEY_LED_RGB_R        "led_r"
#define NVS_KEY_LED_RGB_G        "led_g"
#define NVS_KEY_LED_RGB_B        "led_b"
#define NVS_KEY_LED_BRIGHTNESS   "led_bri"
#define NVS_KEY_PWM_INTENSITY    "pwm_int"
#define NVS_KEY_SESSION_DURATION "sess_dur"

// Calculate settings signature using CRC32 (AD032 structure)
static uint32_t calculate_settings_signature(void) {
    // Signature data: {uuid_ending, byte_length} pairs for all 10 saved parameters
    uint8_t sig_data[] = {
        0x01, 1,   // Mode: uint8
        0x02, 2,   // Custom Frequency: uint16
        0x03, 1,   // Custom Duty: uint8
        0x05, 1,   // LED Enable: uint8
        0x06, 1,   // LED Color Mode: uint8
        0x07, 1,   // LED Palette: uint8
        0x08, 3,   // LED Custom RGB: uint8[3]
        0x09, 1,   // LED Brightness: uint8
        0x04, 1,   // PWM Intensity: uint8
        0x0A, 4    // Session Duration: uint32
    };
    return esp_crc32_le(0, sig_data, sizeof(sig_data));
}

// ============================================================================
// GATT CHARACTERISTIC CALLBACKS
// ============================================================================

// Helper: Update Mode 5 timing from frequency and duty cycle
static void update_mode5_timing(void) {
    uint32_t freq, duty;

    xSemaphoreTake(char_data_mutex, portMAX_DELAY);
    freq = char_data.custom_frequency_hz;
    duty = char_data.custom_duty_percent;
    xSemaphoreGive(char_data_mutex);

    uint32_t period_ms = (100000 / freq);  // Avoid float
    uint32_t on_time_ms = (period_ms * duty) / 100;
    uint32_t coast_ms = period_ms - on_time_ms;

    // Call motor_task API to update timing
    esp_err_t err = motor_update_mode5_timing(on_time_ms, coast_ms);
    if (err == ESP_OK) {
        ESP_LOGI(TAG, "Mode 5 updated: freq=%.2fHz duty=%u%% -> on=%ums coast=%ums",
                 freq / 100.0f, duty, on_time_ms, coast_ms);
    } else {
        ESP_LOGE(TAG, "Failed to update Mode 5 timing: %s", esp_err_to_name(err));
    }
}

// Mode characteristic - Read callback
static int gatt_char_mode_read(uint16_t conn_handle, uint16_t attr_handle,
                                struct ble_gatt_access_ctxt *ctxt, void *arg) {
    xSemaphoreTake(char_data_mutex, portMAX_DELAY);
    uint8_t mode_val = (uint8_t)char_data.current_mode;
    xSemaphoreGive(char_data_mutex);

    ESP_LOGI(TAG, "GATT Read: Mode = %u", mode_val);
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

    if (mode_val >= MODE_COUNT) {
        ESP_LOGE(TAG, "GATT Write: Invalid mode %u (max %u)", mode_val, MODE_COUNT - 1);
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    ESP_LOGI(TAG, "GATT Write: Mode = %u", mode_val);

    xSemaphoreTake(char_data_mutex, portMAX_DELAY);
    char_data.current_mode = (mode_t)mode_val;
    settings_dirty = true;
    xSemaphoreGive(char_data_mutex);

    ble_callback_mode_changed((mode_t)mode_val);
    return 0;
}

// Custom Frequency - Read
static int gatt_char_custom_freq_read(uint16_t conn_handle, uint16_t attr_handle,
                                       struct ble_gatt_access_ctxt *ctxt, void *arg) {
    xSemaphoreTake(char_data_mutex, portMAX_DELAY);
    uint16_t freq_val = char_data.custom_frequency_hz;
    xSemaphoreGive(char_data_mutex);

    ESP_LOGI(TAG, "GATT Read: Frequency = %u (%.2f Hz)", freq_val, freq_val / 100.0f);
    int rc = os_mbuf_append(ctxt->om, &freq_val, sizeof(freq_val));
    return (rc == 0) ? 0 : BLE_ATT_ERR_INSUFFICIENT_RES;
}

// Custom Frequency - Write
static int gatt_char_custom_freq_write(uint16_t conn_handle, uint16_t attr_handle,
                                        struct ble_gatt_access_ctxt *ctxt, void *arg) {
    uint16_t freq_val = 0;
    int rc = ble_hs_mbuf_to_flat(ctxt->om, &freq_val, sizeof(freq_val), NULL);
    if (rc != 0) {
        ESP_LOGE(TAG, "GATT Write: Frequency read failed");
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    // AD032: Range 25-200 (0.25-2.0 Hz)
    if (freq_val < 25 || freq_val > 200) {
        ESP_LOGE(TAG, "GATT Write: Invalid frequency %u (range 25-200)", freq_val);
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    ESP_LOGI(TAG, "GATT Write: Frequency = %u (%.2f Hz)", freq_val, freq_val / 100.0f);

    xSemaphoreTake(char_data_mutex, portMAX_DELAY);
    char_data.custom_frequency_hz = freq_val;
    settings_dirty = true;
    xSemaphoreGive(char_data_mutex);

    update_mode5_timing();
    ble_callback_params_updated();
    return 0;
}

// Custom Duty Cycle - Read
static int gatt_char_custom_duty_read(uint16_t conn_handle, uint16_t attr_handle,
                                       struct ble_gatt_access_ctxt *ctxt, void *arg) {
    xSemaphoreTake(char_data_mutex, portMAX_DELAY);
    uint8_t duty_val = char_data.custom_duty_percent;
    xSemaphoreGive(char_data_mutex);

    ESP_LOGI(TAG, "GATT Read: Duty = %u%%", duty_val);
    int rc = os_mbuf_append(ctxt->om, &duty_val, sizeof(duty_val));
    return (rc == 0) ? 0 : BLE_ATT_ERR_INSUFFICIENT_RES;
}

// Custom Duty Cycle - Write
static int gatt_char_custom_duty_write(uint16_t conn_handle, uint16_t attr_handle,
                                        struct ble_gatt_access_ctxt *ctxt, void *arg) {
    uint8_t duty_val = 0;
    int rc = ble_hs_mbuf_to_flat(ctxt->om, &duty_val, sizeof(duty_val), NULL);
    if (rc != 0) {
        ESP_LOGE(TAG, "GATT Write: Duty read failed");
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    // AD032: Range 10-90%
    if (duty_val < 10 || duty_val > 90) {
        ESP_LOGE(TAG, "GATT Write: Invalid duty %u%% (range 10-90)", duty_val);
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    ESP_LOGI(TAG, "GATT Write: Duty = %u%%", duty_val);

    xSemaphoreTake(char_data_mutex, portMAX_DELAY);
    char_data.custom_duty_percent = duty_val;
    settings_dirty = true;
    xSemaphoreGive(char_data_mutex);

    update_mode5_timing();
    ble_callback_params_updated();
    return 0;
}

// PWM Intensity - Read
static int gatt_char_pwm_intensity_read(uint16_t conn_handle, uint16_t attr_handle,
                                        struct ble_gatt_access_ctxt *ctxt, void *arg) {
    xSemaphoreTake(char_data_mutex, portMAX_DELAY);
    uint8_t intensity = char_data.pwm_intensity;
    xSemaphoreGive(char_data_mutex);

    ESP_LOGI(TAG, "GATT Read: PWM = %u%%", intensity);
    int rc = os_mbuf_append(ctxt->om, &intensity, sizeof(intensity));
    return (rc == 0) ? 0 : BLE_ATT_ERR_INSUFFICIENT_RES;
}

// PWM Intensity - Write
static int gatt_char_pwm_intensity_write(uint16_t conn_handle, uint16_t attr_handle,
                                         struct ble_gatt_access_ctxt *ctxt, void *arg) {
    uint8_t value;
    int rc = ble_hs_mbuf_to_flat(ctxt->om, &value, sizeof(value), NULL);
    if (rc != 0) {
        ESP_LOGE(TAG, "GATT Write: PWM read failed");
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    // AD031: Range 30-80%
    if (value < 30 || value > 80) {
        ESP_LOGE(TAG, "GATT Write: Invalid PWM %u%% (range 30-80)", value);
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    ESP_LOGI(TAG, "GATT Write: PWM = %u%%", value);

    xSemaphoreTake(char_data_mutex, portMAX_DELAY);
    char_data.pwm_intensity = value;
    settings_dirty = true;
    xSemaphoreGive(char_data_mutex);

    esp_err_t err = motor_update_mode5_intensity(value);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Failed to update PWM: %s", esp_err_to_name(err));
    }

    ble_callback_params_updated();
    return 0;
}

// LED Enable - Read
static int gatt_char_led_enable_read(uint16_t conn_handle, uint16_t attr_handle,
                                      struct ble_gatt_access_ctxt *ctxt, void *arg) {
    xSemaphoreTake(char_data_mutex, portMAX_DELAY);
    uint8_t enabled = char_data.led_enable ? 1 : 0;
    xSemaphoreGive(char_data_mutex);

    ESP_LOGI(TAG, "GATT Read: LED Enable = %d", enabled);
    int rc = os_mbuf_append(ctxt->om, &enabled, sizeof(enabled));
    return (rc == 0) ? 0 : BLE_ATT_ERR_INSUFFICIENT_RES;
}

// LED Enable - Write
static int gatt_char_led_enable_write(uint16_t conn_handle, uint16_t attr_handle,
                                       struct ble_gatt_access_ctxt *ctxt, void *arg) {
    uint8_t value;
    int rc = ble_hs_mbuf_to_flat(ctxt->om, &value, sizeof(value), NULL);
    if (rc != 0) {
        ESP_LOGE(TAG, "GATT Write: LED Enable read failed");
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    bool enabled = (value != 0);
    ESP_LOGI(TAG, "GATT Write: LED Enable = %d", enabled);

    xSemaphoreTake(char_data_mutex, portMAX_DELAY);
    char_data.led_enable = enabled;
    settings_dirty = true;
    xSemaphoreGive(char_data_mutex);

    ble_callback_params_updated();
    return 0;
}

// LED Color Mode - Read
static int gatt_char_led_color_mode_read(uint16_t conn_handle, uint16_t attr_handle,
                                          struct ble_gatt_access_ctxt *ctxt, void *arg) {
    xSemaphoreTake(char_data_mutex, portMAX_DELAY);
    uint8_t mode = char_data.led_color_mode;
    xSemaphoreGive(char_data_mutex);

    ESP_LOGI(TAG, "GATT Read: LED Color Mode = %u", mode);
    int rc = os_mbuf_append(ctxt->om, &mode, sizeof(mode));
    return (rc == 0) ? 0 : BLE_ATT_ERR_INSUFFICIENT_RES;
}

// LED Color Mode - Write
static int gatt_char_led_color_mode_write(uint16_t conn_handle, uint16_t attr_handle,
                                           struct ble_gatt_access_ctxt *ctxt, void *arg) {
    uint8_t value;
    int rc = ble_hs_mbuf_to_flat(ctxt->om, &value, sizeof(value), NULL);
    if (rc != 0) {
        ESP_LOGE(TAG, "GATT Write: Color Mode read failed");
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    if (value > 1) {
        ESP_LOGE(TAG, "GATT Write: Invalid color mode %u (0=palette, 1=RGB)", value);
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    ESP_LOGI(TAG, "GATT Write: LED Color Mode = %u (%s)",
             value, value == 0 ? "palette" : "custom RGB");

    xSemaphoreTake(char_data_mutex, portMAX_DELAY);
    char_data.led_color_mode = value;
    settings_dirty = true;
    xSemaphoreGive(char_data_mutex);

    ble_callback_params_updated();
    return 0;
}

// LED Palette - Read
static int gatt_char_led_palette_read(uint16_t conn_handle, uint16_t attr_handle,
                                       struct ble_gatt_access_ctxt *ctxt, void *arg) {
    xSemaphoreTake(char_data_mutex, portMAX_DELAY);
    uint8_t idx = char_data.led_palette_index;
    xSemaphoreGive(char_data_mutex);

    ESP_LOGI(TAG, "GATT Read: LED Palette = %u", idx);
    int rc = os_mbuf_append(ctxt->om, &idx, sizeof(idx));
    return (rc == 0) ? 0 : BLE_ATT_ERR_INSUFFICIENT_RES;
}

// LED Palette - Write
static int gatt_char_led_palette_write(uint16_t conn_handle, uint16_t attr_handle,
                                        struct ble_gatt_access_ctxt *ctxt, void *arg) {
    uint8_t value;
    int rc = ble_hs_mbuf_to_flat(ctxt->om, &value, sizeof(value), NULL);
    if (rc != 0) {
        ESP_LOGE(TAG, "GATT Write: Palette read failed");
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    if (value > 15) {
        ESP_LOGE(TAG, "GATT Write: Invalid palette %u (max 15)", value);
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    ESP_LOGI(TAG, "GATT Write: LED Palette = %u (%s)",
             value, color_palette[value].name);

    xSemaphoreTake(char_data_mutex, portMAX_DELAY);
    char_data.led_palette_index = value;
    settings_dirty = true;
    xSemaphoreGive(char_data_mutex);

    ble_callback_params_updated();
    return 0;
}

// LED Custom RGB - Read
static int gatt_char_led_custom_rgb_read(uint16_t conn_handle, uint16_t attr_handle,
                                          struct ble_gatt_access_ctxt *ctxt, void *arg) {
    uint8_t rgb[3];

    xSemaphoreTake(char_data_mutex, portMAX_DELAY);
    rgb[0] = char_data.led_custom_r;
    rgb[1] = char_data.led_custom_g;
    rgb[2] = char_data.led_custom_b;
    xSemaphoreGive(char_data_mutex);

    ESP_LOGI(TAG, "GATT Read: LED RGB = (%u, %u, %u)", rgb[0], rgb[1], rgb[2]);
    int rc = os_mbuf_append(ctxt->om, rgb, sizeof(rgb));
    return (rc == 0) ? 0 : BLE_ATT_ERR_INSUFFICIENT_RES;
}

// LED Custom RGB - Write
static int gatt_char_led_custom_rgb_write(uint16_t conn_handle, uint16_t attr_handle,
                                           struct ble_gatt_access_ctxt *ctxt, void *arg) {
    uint8_t rgb[3];
    int rc = ble_hs_mbuf_to_flat(ctxt->om, rgb, sizeof(rgb), NULL);
    if (rc != 0) {
        ESP_LOGE(TAG, "GATT Write: RGB read failed");
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    ESP_LOGI(TAG, "GATT Write: LED RGB = (%u, %u, %u)", rgb[0], rgb[1], rgb[2]);

    xSemaphoreTake(char_data_mutex, portMAX_DELAY);
    char_data.led_custom_r = rgb[0];
    char_data.led_custom_g = rgb[1];
    char_data.led_custom_b = rgb[2];
    settings_dirty = true;
    xSemaphoreGive(char_data_mutex);

    ble_callback_params_updated();
    return 0;
}

// LED Brightness - Read
static int gatt_char_led_brightness_read(uint16_t conn_handle, uint16_t attr_handle,
                                          struct ble_gatt_access_ctxt *ctxt, void *arg) {
    xSemaphoreTake(char_data_mutex, portMAX_DELAY);
    uint8_t brightness = char_data.led_brightness;
    xSemaphoreGive(char_data_mutex);

    ESP_LOGI(TAG, "GATT Read: LED Brightness = %u%%", brightness);
    int rc = os_mbuf_append(ctxt->om, &brightness, sizeof(brightness));
    return (rc == 0) ? 0 : BLE_ATT_ERR_INSUFFICIENT_RES;
}

// LED Brightness - Write
static int gatt_char_led_brightness_write(uint16_t conn_handle, uint16_t attr_handle,
                                           struct ble_gatt_access_ctxt *ctxt, void *arg) {
    uint8_t value;
    int rc = ble_hs_mbuf_to_flat(ctxt->om, &value, sizeof(value), NULL);
    if (rc != 0) {
        ESP_LOGE(TAG, "GATT Write: Brightness read failed");
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    // AD032: Range 10-30%
    if (value < 10 || value > 30) {
        ESP_LOGE(TAG, "GATT Write: Invalid brightness %u%% (range 10-30)", value);
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    ESP_LOGI(TAG, "GATT Write: LED Brightness = %u%%", value);

    xSemaphoreTake(char_data_mutex, portMAX_DELAY);
    char_data.led_brightness = value;
    settings_dirty = true;
    xSemaphoreGive(char_data_mutex);

    ble_callback_params_updated();
    return 0;
}

// Session Duration - Read
static int gatt_char_session_duration_read(uint16_t conn_handle, uint16_t attr_handle,
                                            struct ble_gatt_access_ctxt *ctxt, void *arg) {
    xSemaphoreTake(char_data_mutex, portMAX_DELAY);
    uint32_t duration = char_data.session_duration_sec;
    xSemaphoreGive(char_data_mutex);

    ESP_LOGI(TAG, "GATT Read: Session Duration = %u sec (%.1f min)",
             duration, duration / 60.0f);
    int rc = os_mbuf_append(ctxt->om, &duration, sizeof(duration));
    return (rc == 0) ? 0 : BLE_ATT_ERR_INSUFFICIENT_RES;
}

// Session Duration - Write
static int gatt_char_session_duration_write(uint16_t conn_handle, uint16_t attr_handle,
                                             struct ble_gatt_access_ctxt *ctxt, void *arg) {
    uint32_t value;
    int rc = ble_hs_mbuf_to_flat(ctxt->om, &value, sizeof(value), NULL);
    if (rc != 0) {
        ESP_LOGE(TAG, "GATT Write: Session Duration read failed");
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    // AD032: Range 1200-5400 sec (20-90 min)
    if (value < 1200 || value > 5400) {
        ESP_LOGE(TAG, "GATT Write: Invalid duration %u sec (range 1200-5400)", value);
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    ESP_LOGI(TAG, "GATT Write: Session Duration = %u sec (%.1f min)",
             value, value / 60.0f);

    xSemaphoreTake(char_data_mutex, portMAX_DELAY);
    char_data.session_duration_sec = value;
    settings_dirty = true;
    xSemaphoreGive(char_data_mutex);

    // Motor task will check this value to determine when to end session
    return 0;
}

// Session Time - Read
static int gatt_char_session_time_read(uint16_t conn_handle, uint16_t attr_handle,
                                        struct ble_gatt_access_ctxt *ctxt, void *arg) {
    xSemaphoreTake(char_data_mutex, portMAX_DELAY);
    uint32_t session_time = char_data.session_time_sec;
    xSemaphoreGive(char_data_mutex);

    ESP_LOGI(TAG, "GATT Read: Session Time = %u sec", session_time);
    int rc = os_mbuf_append(ctxt->om, &session_time, sizeof(session_time));
    return (rc == 0) ? 0 : BLE_ATT_ERR_INSUFFICIENT_RES;
}

// Battery Level - Read
static int gatt_char_battery_read(uint16_t conn_handle, uint16_t attr_handle,
                                   struct ble_gatt_access_ctxt *ctxt, void *arg) {
    xSemaphoreTake(char_data_mutex, portMAX_DELAY);
    uint8_t battery_val = char_data.battery_level;
    xSemaphoreGive(char_data_mutex);

    ESP_LOGI(TAG, "GATT Read: Battery = %u%%", battery_val);
    int rc = os_mbuf_append(ctxt->om, &battery_val, sizeof(battery_val));
    return (rc == 0) ? 0 : BLE_ATT_ERR_INSUFFICIENT_RES;
}

// GATT characteristic access dispatcher
static int gatt_svr_chr_access(uint16_t conn_handle, uint16_t attr_handle,
                                struct ble_gatt_access_ctxt *ctxt, void *arg) {
    const ble_uuid_t *uuid = ctxt->chr->uuid;

    // Match UUID to characteristic
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

    if (ble_uuid_cmp(uuid, &uuid_char_pwm_intensity.u) == 0) {
        return (ctxt->op == BLE_GATT_ACCESS_OP_READ_CHR) ?
               gatt_char_pwm_intensity_read(conn_handle, attr_handle, ctxt, arg) :
               gatt_char_pwm_intensity_write(conn_handle, attr_handle, ctxt, arg);
    }

    if (ble_uuid_cmp(uuid, &uuid_char_led_enable.u) == 0) {
        return (ctxt->op == BLE_GATT_ACCESS_OP_READ_CHR) ?
               gatt_char_led_enable_read(conn_handle, attr_handle, ctxt, arg) :
               gatt_char_led_enable_write(conn_handle, attr_handle, ctxt, arg);
    }

    if (ble_uuid_cmp(uuid, &uuid_char_led_color_mode.u) == 0) {
        return (ctxt->op == BLE_GATT_ACCESS_OP_READ_CHR) ?
               gatt_char_led_color_mode_read(conn_handle, attr_handle, ctxt, arg) :
               gatt_char_led_color_mode_write(conn_handle, attr_handle, ctxt, arg);
    }

    if (ble_uuid_cmp(uuid, &uuid_char_led_palette.u) == 0) {
        return (ctxt->op == BLE_GATT_ACCESS_OP_READ_CHR) ?
               gatt_char_led_palette_read(conn_handle, attr_handle, ctxt, arg) :
               gatt_char_led_palette_write(conn_handle, attr_handle, ctxt, arg);
    }

    if (ble_uuid_cmp(uuid, &uuid_char_led_custom_rgb.u) == 0) {
        return (ctxt->op == BLE_GATT_ACCESS_OP_READ_CHR) ?
               gatt_char_led_custom_rgb_read(conn_handle, attr_handle, ctxt, arg) :
               gatt_char_led_custom_rgb_write(conn_handle, attr_handle, ctxt, arg);
    }

    if (ble_uuid_cmp(uuid, &uuid_char_led_brightness.u) == 0) {
        return (ctxt->op == BLE_GATT_ACCESS_OP_READ_CHR) ?
               gatt_char_led_brightness_read(conn_handle, attr_handle, ctxt, arg) :
               gatt_char_led_brightness_write(conn_handle, attr_handle, ctxt, arg);
    }

    if (ble_uuid_cmp(uuid, &uuid_char_session_duration.u) == 0) {
        return (ctxt->op == BLE_GATT_ACCESS_OP_READ_CHR) ?
               gatt_char_session_duration_read(conn_handle, attr_handle, ctxt, arg) :
               gatt_char_session_duration_write(conn_handle, attr_handle, ctxt, arg);
    }

    if (ble_uuid_cmp(uuid, &uuid_char_session_time.u) == 0) {
        return gatt_char_session_time_read(conn_handle, attr_handle, ctxt, arg);
    }

    if (ble_uuid_cmp(uuid, &uuid_char_battery.u) == 0) {
        return gatt_char_battery_read(conn_handle, attr_handle, ctxt, arg);
    }

    // Unknown characteristic
    return BLE_ATT_ERR_UNLIKELY;
}

// ============================================================================
// GATT SERVICE DEFINITION (AD032)
// ============================================================================

static const struct ble_gatt_svc_def gatt_svr_svcs[] = {
    {
        // Configuration Service (UUID: 6E400002-...)
        .type = BLE_GATT_SVC_TYPE_PRIMARY,
        .uuid = &uuid_config_service.u,
        .characteristics = (struct ble_gatt_chr_def[]){
            // Motor Control Group
            {
                .uuid = &uuid_char_mode.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_WRITE,
            },
            {
                .uuid = &uuid_char_custom_freq.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_WRITE,
            },
            {
                .uuid = &uuid_char_custom_duty.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_WRITE,
            },
            {
                .uuid = &uuid_char_pwm_intensity.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_WRITE,
            },
            // LED Control Group
            {
                .uuid = &uuid_char_led_enable.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_WRITE,
            },
            {
                .uuid = &uuid_char_led_color_mode.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_WRITE,
            },
            {
                .uuid = &uuid_char_led_palette.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_WRITE,
            },
            {
                .uuid = &uuid_char_led_custom_rgb.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_WRITE,
            },
            {
                .uuid = &uuid_char_led_brightness.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_WRITE,
            },
            // Status/Monitoring Group
            {
                .uuid = &uuid_char_session_duration.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_WRITE,
            },
            {
                .uuid = &uuid_char_session_time.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_NOTIFY,
            },
            {
                .uuid = &uuid_char_battery.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_NOTIFY,
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
            ESP_LOGI(TAG, "GATT: Service %s registered",
                     ble_uuid_to_str(ctxt->svc.svc_def->uuid, buf));
            break;

        case BLE_GATT_REGISTER_OP_CHR:
            ESP_LOGI(TAG, "GATT: Characteristic %s registered",
                     ble_uuid_to_str(ctxt->chr.chr_def->uuid, buf));
            break;

        case BLE_GATT_REGISTER_OP_DSC:
            ESP_LOGI(TAG, "GATT: Descriptor %s registered",
                     ble_uuid_to_str(ctxt->dsc.dsc_def->uuid, buf));
            break;

        default:
            break;
    }
}

// Initialize GATT services
static esp_err_t gatt_svr_init(void) {
    int rc;

    ble_svc_gap_init();
    ble_svc_gatt_init();

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

    ESP_LOGI(TAG, "GATT: Configuration Service (AD032) initialized with 12 characteristics");
    return ESP_OK;
}

// ============================================================================
// NIMBLE GAP EVENT HANDLER
// ============================================================================

static int ble_gap_event(struct ble_gap_event *event, void *arg) {
    switch (event->type) {
        case BLE_GAP_EVENT_CONNECT:
            ESP_LOGI(TAG, "BLE connection %s; status=%d",
                     event->connect.status == 0 ? "established" : "failed",
                     event->connect.status);
            if (event->connect.status == 0) {
                adv_state.client_connected = true;
                adv_state.advertising_active = false;
            }
            break;

        case BLE_GAP_EVENT_DISCONNECT:
            ESP_LOGI(TAG, "BLE disconnect; reason=%d", event->disconnect.reason);
            adv_state.client_connected = false;

            // Resume advertising on disconnect
            ble_gap_adv_start(BLE_OWN_ADDR_PUBLIC, NULL, BLE_HS_FOREVER,
                              &adv_params, ble_gap_event, NULL);
            adv_state.advertising_active = true;
            adv_state.advertising_start_ms = (uint32_t)(esp_timer_get_time() / 1000);
            ESP_LOGI(TAG, "BLE advertising restarted after disconnect");
            break;

        case BLE_GAP_EVENT_ADV_COMPLETE:
            ESP_LOGI(TAG, "BLE advertising complete; reason=%d", event->adv_complete.reason);
            adv_state.advertising_active = false;
            break;

        default:
            break;
    }
    return 0;
}

// ============================================================================
// NIMBLE HOST CALLBACKS
// ============================================================================

static void ble_on_reset(int reason) {
    ESP_LOGE(TAG, "BLE host reset; reason=%d", reason);
}

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

    adv_state.advertising_active = true;
    adv_state.advertising_start_ms = (uint32_t)(esp_timer_get_time() / 1000);
    ESP_LOGI(TAG, "BLE advertising started");
}

// NimBLE host task
static void nimble_host_task(void *param) {
    ESP_LOGI(TAG, "NimBLE host task started");
    nimble_port_run();
    nimble_port_freertos_deinit();
}

// ============================================================================
// NVS PERSISTENCE
// ============================================================================

esp_err_t ble_save_settings_to_nvs(void) {
    if (!ble_settings_dirty()) {
        ESP_LOGI(TAG, "NVS: Settings unchanged, skipping save");
        return ESP_OK;
    }

    ESP_LOGI(TAG, "NVS: Saving settings...");

    nvs_handle_t nvs_handle;
    esp_err_t err = nvs_open(NVS_NAMESPACE, NVS_READWRITE, &nvs_handle);

    if (err != ESP_OK) {
        ESP_LOGE(TAG, "NVS: Failed to open: %s", esp_err_to_name(err));
        return err;
    }

    // Write signature
    uint32_t sig = calculate_settings_signature();
    err = nvs_set_u32(nvs_handle, NVS_KEY_SIGNATURE, sig);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "NVS: Failed to write signature: %s", esp_err_to_name(err));
        nvs_close(nvs_handle);
        return err;
    }

    // Write all settings (mutex-protected)
    xSemaphoreTake(char_data_mutex, portMAX_DELAY);
    nvs_set_u8(nvs_handle, NVS_KEY_MODE, (uint8_t)char_data.current_mode);
    nvs_set_u16(nvs_handle, NVS_KEY_FREQUENCY, char_data.custom_frequency_hz);
    nvs_set_u8(nvs_handle, NVS_KEY_DUTY, char_data.custom_duty_percent);
    nvs_set_u8(nvs_handle, NVS_KEY_LED_ENABLE, char_data.led_enable ? 1 : 0);
    nvs_set_u8(nvs_handle, NVS_KEY_LED_COLOR_MODE, char_data.led_color_mode);
    nvs_set_u8(nvs_handle, NVS_KEY_LED_PALETTE, char_data.led_palette_index);
    nvs_set_u8(nvs_handle, NVS_KEY_LED_RGB_R, char_data.led_custom_r);
    nvs_set_u8(nvs_handle, NVS_KEY_LED_RGB_G, char_data.led_custom_g);
    nvs_set_u8(nvs_handle, NVS_KEY_LED_RGB_B, char_data.led_custom_b);
    nvs_set_u8(nvs_handle, NVS_KEY_LED_BRIGHTNESS, char_data.led_brightness);
    nvs_set_u8(nvs_handle, NVS_KEY_PWM_INTENSITY, char_data.pwm_intensity);
    nvs_set_u32(nvs_handle, NVS_KEY_SESSION_DURATION, char_data.session_duration_sec);
    xSemaphoreGive(char_data_mutex);

    // Commit
    err = nvs_commit(nvs_handle);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "NVS: Failed to commit: %s", esp_err_to_name(err));
    } else {
        ESP_LOGI(TAG, "NVS: Settings saved successfully");
        ble_settings_mark_clean();
    }

    nvs_close(nvs_handle);
    return err;
}

esp_err_t ble_load_settings_from_nvs(void) {
    nvs_handle_t nvs_handle;
    esp_err_t err = nvs_open(NVS_NAMESPACE, NVS_READONLY, &nvs_handle);

    if (err != ESP_OK) {
        ESP_LOGW(TAG, "NVS: Unable to open (first boot?) - using defaults");
        return ESP_OK;
    }

    // Verify signature
    uint32_t stored_sig = 0;
    uint32_t expected_sig = calculate_settings_signature();
    err = nvs_get_u32(nvs_handle, NVS_KEY_SIGNATURE, &stored_sig);

    if (err != ESP_OK || stored_sig != expected_sig) {
        ESP_LOGW(TAG, "NVS: Signature mismatch - using defaults");
        nvs_close(nvs_handle);
        return ESP_OK;
    }

    ESP_LOGI(TAG, "NVS: Signature valid, loading settings...");

    // Load all settings
    uint8_t mode, duty, led_en, led_cmode, led_pal, r, g, b, led_bri, pwm;
    uint16_t freq;
    uint32_t sess_dur;

    xSemaphoreTake(char_data_mutex, portMAX_DELAY);

    if (nvs_get_u8(nvs_handle, NVS_KEY_MODE, &mode) == ESP_OK) {
        char_data.current_mode = (mode_t)mode;
    }

    if (nvs_get_u16(nvs_handle, NVS_KEY_FREQUENCY, &freq) == ESP_OK) {
        char_data.custom_frequency_hz = freq;
    }

    if (nvs_get_u8(nvs_handle, NVS_KEY_DUTY, &duty) == ESP_OK) {
        char_data.custom_duty_percent = duty;
    }

    if (nvs_get_u8(nvs_handle, NVS_KEY_LED_ENABLE, &led_en) == ESP_OK) {
        char_data.led_enable = (led_en != 0);
    }

    if (nvs_get_u8(nvs_handle, NVS_KEY_LED_COLOR_MODE, &led_cmode) == ESP_OK) {
        char_data.led_color_mode = led_cmode;
    }

    if (nvs_get_u8(nvs_handle, NVS_KEY_LED_PALETTE, &led_pal) == ESP_OK) {
        char_data.led_palette_index = led_pal;
    }

    if (nvs_get_u8(nvs_handle, NVS_KEY_LED_RGB_R, &r) == ESP_OK) {
        char_data.led_custom_r = r;
    }

    if (nvs_get_u8(nvs_handle, NVS_KEY_LED_RGB_G, &g) == ESP_OK) {
        char_data.led_custom_g = g;
    }

    if (nvs_get_u8(nvs_handle, NVS_KEY_LED_RGB_B, &b) == ESP_OK) {
        char_data.led_custom_b = b;
    }

    if (nvs_get_u8(nvs_handle, NVS_KEY_LED_BRIGHTNESS, &led_bri) == ESP_OK) {
        char_data.led_brightness = led_bri;
    }

    if (nvs_get_u8(nvs_handle, NVS_KEY_PWM_INTENSITY, &pwm) == ESP_OK) {
        char_data.pwm_intensity = pwm;
    }

    if (nvs_get_u32(nvs_handle, NVS_KEY_SESSION_DURATION, &sess_dur) == ESP_OK) {
        char_data.session_duration_sec = sess_dur;
    }

    xSemaphoreGive(char_data_mutex);

    nvs_close(nvs_handle);

    // Recalculate motor timings
    update_mode5_timing();

    ESP_LOGI(TAG, "NVS: Settings loaded successfully");
    return ESP_OK;
}

// ============================================================================
// PUBLIC API IMPLEMENTATION
// ============================================================================

esp_err_t ble_manager_init(void) {
    esp_err_t ret;

    ESP_LOGI(TAG, "Initializing BLE manager (AD032)...");

    // Create mutex
    char_data_mutex = xSemaphoreCreateMutex();
    if (char_data_mutex == NULL) {
        ESP_LOGE(TAG, "Failed to create mutex");
        return ESP_FAIL;
    }

    // Initialize NVS
    ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_LOGW(TAG, "NVS needs erase");
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "NVS init failed: %s", esp_err_to_name(ret));
        return ret;
    }

    // Load settings from NVS
    ble_load_settings_from_nvs();

    // Initialize NimBLE (handles BT controller internally)
    ret = nimble_port_init();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "NimBLE init failed: %s", esp_err_to_name(ret));
        return ret;
    }

    // Configure callbacks
    ble_hs_cfg.reset_cb = ble_on_reset;
    ble_hs_cfg.sync_cb = ble_on_sync;
    ble_hs_cfg.gatts_register_cb = gatt_svr_register_cb;
    ble_hs_cfg.store_status_cb = ble_store_util_status_rr;

    // Initialize GATT services
    ret = gatt_svr_init();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "GATT init failed");
        return ret;
    }

    // Start NimBLE host task
    nimble_port_freertos_init(nimble_host_task);

    ESP_LOGI(TAG, "BLE manager initialized (Production UUID 6E400002)");
    return ESP_OK;
}

void ble_start_advertising(void) {
    if (!adv_state.advertising_active) {
        int rc = ble_gap_adv_start(BLE_OWN_ADDR_PUBLIC, NULL, BLE_HS_FOREVER,
                                    &adv_params, ble_gap_event, NULL);
        if (rc == 0) {
            adv_state.advertising_active = true;
            adv_state.advertising_start_ms = (uint32_t)(esp_timer_get_time() / 1000);
            ESP_LOGI(TAG, "BLE advertising re-enabled");
        } else {
            ESP_LOGE(TAG, "Failed to restart advertising; rc=%d", rc);
        }
    }
}

void ble_stop_advertising(void) {
    if (adv_state.advertising_active) {
        int rc = ble_gap_adv_stop();
        if (rc == 0) {
            adv_state.advertising_active = false;
            ESP_LOGI(TAG, "BLE advertising stopped");
        } else {
            ESP_LOGE(TAG, "Failed to stop advertising; rc=%d", rc);
        }
    }
}

bool ble_is_connected(void) {
    return adv_state.client_connected;
}

bool ble_is_advertising(void) {
    return adv_state.advertising_active;
}

uint32_t ble_get_advertising_elapsed_ms(void) {
    if (!adv_state.advertising_active) {
        return 0;
    }
    uint32_t now = (uint32_t)(esp_timer_get_time() / 1000);
    return now - adv_state.advertising_start_ms;
}

void ble_update_battery_level(uint8_t percentage) {
    xSemaphoreTake(char_data_mutex, portMAX_DELAY);
    char_data.battery_level = percentage;
    xSemaphoreGive(char_data_mutex);
}

void ble_update_session_time(uint32_t seconds) {
    xSemaphoreTake(char_data_mutex, portMAX_DELAY);
    char_data.session_time_sec = seconds;
    xSemaphoreGive(char_data_mutex);
}

mode_t ble_get_current_mode(void) {
    xSemaphoreTake(char_data_mutex, portMAX_DELAY);
    mode_t mode = char_data.current_mode;
    xSemaphoreGive(char_data_mutex);
    return mode;
}

uint16_t ble_get_custom_frequency_hz(void) {
    xSemaphoreTake(char_data_mutex, portMAX_DELAY);
    uint16_t freq = char_data.custom_frequency_hz;
    xSemaphoreGive(char_data_mutex);
    return freq;
}

uint8_t ble_get_custom_duty_percent(void) {
    xSemaphoreTake(char_data_mutex, portMAX_DELAY);
    uint8_t duty = char_data.custom_duty_percent;
    xSemaphoreGive(char_data_mutex);
    return duty;
}

uint8_t ble_get_pwm_intensity(void) {
    xSemaphoreTake(char_data_mutex, portMAX_DELAY);
    uint8_t intensity = char_data.pwm_intensity;
    xSemaphoreGive(char_data_mutex);
    return intensity;
}

bool ble_get_led_enable(void) {
    xSemaphoreTake(char_data_mutex, portMAX_DELAY);
    bool enabled = char_data.led_enable;
    xSemaphoreGive(char_data_mutex);
    return enabled;
}

uint8_t ble_get_led_color_mode(void) {
    xSemaphoreTake(char_data_mutex, portMAX_DELAY);
    uint8_t mode = char_data.led_color_mode;
    xSemaphoreGive(char_data_mutex);
    return mode;
}

uint8_t ble_get_led_palette_index(void) {
    xSemaphoreTake(char_data_mutex, portMAX_DELAY);
    uint8_t idx = char_data.led_palette_index;
    xSemaphoreGive(char_data_mutex);
    return idx;
}

void ble_get_led_custom_rgb(uint8_t *r, uint8_t *g, uint8_t *b) {
    xSemaphoreTake(char_data_mutex, portMAX_DELAY);
    *r = char_data.led_custom_r;
    *g = char_data.led_custom_g;
    *b = char_data.led_custom_b;
    xSemaphoreGive(char_data_mutex);
}

uint8_t ble_get_led_brightness(void) {
    xSemaphoreTake(char_data_mutex, portMAX_DELAY);
    uint8_t brightness = char_data.led_brightness;
    xSemaphoreGive(char_data_mutex);
    return brightness;
}

uint32_t ble_get_session_duration_sec(void) {
    xSemaphoreTake(char_data_mutex, portMAX_DELAY);
    uint32_t duration = char_data.session_duration_sec;
    xSemaphoreGive(char_data_mutex);
    return duration;
}

bool ble_settings_dirty(void) {
    xSemaphoreTake(char_data_mutex, portMAX_DELAY);
    bool dirty = settings_dirty;
    xSemaphoreGive(char_data_mutex);
    return dirty;
}

void ble_settings_mark_clean(void) {
    xSemaphoreTake(char_data_mutex, portMAX_DELAY);
    settings_dirty = false;
    xSemaphoreGive(char_data_mutex);
}

esp_err_t ble_manager_deinit(void) {
    ESP_LOGI(TAG, "Deinitializing BLE manager...");
    ble_stop_advertising();
    ESP_LOGI(TAG, "BLE manager deinitialized");
    return ESP_OK;
}
