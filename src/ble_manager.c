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
#include "motor_task.h"
#include "motor_control.h"  // For MOTOR_PWM_DEFAULT
#include "role_manager.h"
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

/**
 * @brief Mutex timeout for operations
 *
 * JPL Rule #6: No unbounded waits - all mutex operations must have timeouts
 * 100ms timeout provides safety margin
 * If mutex timeout occurs, indicates potential deadlock or system failure
 */
#define MUTEX_TIMEOUT_MS 100

// ============================================================================
// BLE SERVICE UUIDs (Production - AD030/AD032)
// ============================================================================

// EMDR Pulser Project UUID Base: 4BCAE9BE-9829-4F0A-9E88-267DE5E7XXYY
// Service differentiation: XX = service type, YY = characteristic ID

// NOTE: BLE_UUID128_INIT expects bytes in REVERSE order (little-endian)
// UUID format: 4B CA E9 BE - 9829 - 4F0A - 9E88 - 267D E5 E7 XX YY
// Reversed:    0x0b, 0x14, 0xe7, 0xe5, 0x7d, 0x26, 0x88, 0x9e,
//              0x0a, 0x4f, 0x29, 0x98, 0xbe, 0xe9, 0xca, 0x4b
//                                                  ↑  ↑  ↑  ↑
//                                              13th 14th 15th 16th
// Service differentiation (bytes 13-14):
//   0x01 0x00 = Bilateral Control Service (device-to-device, AD030)
//   0x02 0x00 = Configuration Service (mobile app, AD032)

// Bilateral Control Service (4BCAE9BE-9829-4F0A-9E88-267DE5E70100)
// Device-to-device communication for dual-device coordination
static const ble_uuid128_t uuid_bilateral_service = BLE_UUID128_INIT(
    0x00, 0x01, 0xe7, 0xe5, 0x7d, 0x26, 0x88, 0x9e,
    0x0a, 0x4f, 0x29, 0x98, 0xbe, 0xe9, 0xca, 0x4b);

// Bilateral Control Service Characteristics (bytes 13-14 = 0x01 0xNN)
// Phase 1b: Battery-based role assignment (AD030/AD034)
static const ble_uuid128_t uuid_bilateral_battery = BLE_UUID128_INIT(
    0x01, 0x01, 0xe7, 0xe5, 0x7d, 0x26, 0x88, 0x9e,
    0x0a, 0x4f, 0x29, 0x98, 0xbe, 0xe9, 0xca, 0x4b);

static const ble_uuid128_t uuid_bilateral_mac = BLE_UUID128_INIT(
    0x02, 0x01, 0xe7, 0xe5, 0x7d, 0x26, 0x88, 0x9e,
    0x0a, 0x4f, 0x29, 0x98, 0xbe, 0xe9, 0xca, 0x4b);

static const ble_uuid128_t uuid_bilateral_role = BLE_UUID128_INIT(
    0x03, 0x01, 0xe7, 0xe5, 0x7d, 0x26, 0x88, 0x9e,
    0x0a, 0x4f, 0x29, 0x98, 0xbe, 0xe9, 0xca, 0x4b);

// Configuration Service (4BCAE9BE-9829-4F0A-9E88-267DE5E70200)
// Mobile app control interface (single or dual device)
static const ble_uuid128_t uuid_config_service = BLE_UUID128_INIT(
    0x00, 0x02, 0xe7, 0xe5, 0x7d, 0x26, 0x88, 0x9e,
    0x0a, 0x4f, 0x29, 0x98, 0xbe, 0xe9, 0xca, 0x4b);

// Motor Control Group (bytes 13-14 = 0x02 0x0N)
static const ble_uuid128_t uuid_char_mode = BLE_UUID128_INIT(
    0x01, 0x02, 0xe7, 0xe5, 0x7d, 0x26, 0x88, 0x9e,
    0x0a, 0x4f, 0x29, 0x98, 0xbe, 0xe9, 0xca, 0x4b);

static const ble_uuid128_t uuid_char_custom_freq = BLE_UUID128_INIT(
    0x02, 0x02, 0xe7, 0xe5, 0x7d, 0x26, 0x88, 0x9e,
    0x0a, 0x4f, 0x29, 0x98, 0xbe, 0xe9, 0xca, 0x4b);

static const ble_uuid128_t uuid_char_custom_duty = BLE_UUID128_INIT(
    0x03, 0x02, 0xe7, 0xe5, 0x7d, 0x26, 0x88, 0x9e,
    0x0a, 0x4f, 0x29, 0x98, 0xbe, 0xe9, 0xca, 0x4b);

static const ble_uuid128_t uuid_char_pwm_intensity = BLE_UUID128_INIT(
    0x04, 0x02, 0xe7, 0xe5, 0x7d, 0x26, 0x88, 0x9e,
    0x0a, 0x4f, 0x29, 0x98, 0xbe, 0xe9, 0xca, 0x4b);

// LED Control Group (bytes 13-14 = 0x02 0x0N)
static const ble_uuid128_t uuid_char_led_enable = BLE_UUID128_INIT(
    0x05, 0x02, 0xe7, 0xe5, 0x7d, 0x26, 0x88, 0x9e,
    0x0a, 0x4f, 0x29, 0x98, 0xbe, 0xe9, 0xca, 0x4b);

static const ble_uuid128_t uuid_char_led_color_mode = BLE_UUID128_INIT(
    0x06, 0x02, 0xe7, 0xe5, 0x7d, 0x26, 0x88, 0x9e,
    0x0a, 0x4f, 0x29, 0x98, 0xbe, 0xe9, 0xca, 0x4b);

static const ble_uuid128_t uuid_char_led_palette = BLE_UUID128_INIT(
    0x07, 0x02, 0xe7, 0xe5, 0x7d, 0x26, 0x88, 0x9e,
    0x0a, 0x4f, 0x29, 0x98, 0xbe, 0xe9, 0xca, 0x4b);

static const ble_uuid128_t uuid_char_led_custom_rgb = BLE_UUID128_INIT(
    0x08, 0x02, 0xe7, 0xe5, 0x7d, 0x26, 0x88, 0x9e,
    0x0a, 0x4f, 0x29, 0x98, 0xbe, 0xe9, 0xca, 0x4b);

static const ble_uuid128_t uuid_char_led_brightness = BLE_UUID128_INIT(
    0x09, 0x02, 0xe7, 0xe5, 0x7d, 0x26, 0x88, 0x9e,
    0x0a, 0x4f, 0x29, 0x98, 0xbe, 0xe9, 0xca, 0x4b);

// Status/Monitoring Group (bytes 13-14 = 0x02 0x0N)
static const ble_uuid128_t uuid_char_session_duration = BLE_UUID128_INIT(
    0x0a, 0x02, 0xe7, 0xe5, 0x7d, 0x26, 0x88, 0x9e,
    0x0a, 0x4f, 0x29, 0x98, 0xbe, 0xe9, 0xca, 0x4b);

static const ble_uuid128_t uuid_char_session_time = BLE_UUID128_INIT(
    0x0b, 0x02, 0xe7, 0xe5, 0x7d, 0x26, 0x88, 0x9e,
    0x0a, 0x4f, 0x29, 0x98, 0xbe, 0xe9, 0xca, 0x4b);

static const ble_uuid128_t uuid_char_battery = BLE_UUID128_INIT(
    0x0c, 0x02, 0xe7, 0xe5, 0x7d, 0x26, 0x88, 0x9e,
    0x0a, 0x4f, 0x29, 0x98, 0xbe, 0xe9, 0xca, 0x4b);

// ============================================================================
// UUID-SWITCHING CONFIGURATION (Phase 1b.3)
// ============================================================================

/**
 * @brief Pairing window duration (30 seconds)
 *
 * During first 30s: Advertise Bilateral UUID (peer discovery only)
 * After 30s: Switch to Config UUID (app discovery + bonded peer reconnect)
 */
#define PAIRING_WINDOW_MS 30000

/**
 * @brief Boot timestamp for pairing window tracking
 *
 * Initialized in ble_init() to esp_timer_get_time() / 1000
 * Used to determine which UUID to advertise (Bilateral vs Config)
 */
static uint32_t ble_boot_time_ms = 0;

// Forward declarations for helper functions
static const ble_uuid128_t* ble_get_advertised_uuid(void);
static bool ble_get_bonded_peer_addr(ble_addr_t *addr_out);

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
    .current_mode = MODE_05HZ_25,
    .custom_frequency_hz = 100,  // 1.00 Hz
    .custom_duty_percent = 50,
    .pwm_intensity = MOTOR_PWM_DEFAULT,  // From motor_control.h (single source of truth)
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
    uint16_t conn_handle;              /**< Connection handle for notifications */
    bool notify_mode_subscribed;        /**< Client subscribed to Mode notifications */
    bool notify_session_time_subscribed; /**< Client subscribed to Session Time notifications */
    bool notify_battery_subscribed;     /**< Client subscribed to Battery notifications */
} ble_advertising_state_t;

static ble_advertising_state_t adv_state = {
    .advertising_active = false,
    .client_connected = false,
    .advertising_start_ms = 0,
    .conn_handle = BLE_HS_CONN_HANDLE_NONE,
    .notify_mode_subscribed = false,
    .notify_session_time_subscribed = false,
    .notify_battery_subscribed = false
};

// Settings dirty flag (thread-safe via char_data_mutex)
static bool settings_dirty = false;

// ============================================================================
// BLE SECURITY CONFIGURATION (Phase 1b.3)
// ============================================================================

/**
 * @brief BLE pairing/bonding state
 *
 * Configuration: LE Secure Connections with MITM protection via button confirmation
 * - Just Works pairing method (no passkey display required)
 * - Button confirmation required (MITM protection)
 * - Bonding enabled (keys stored in NVS)
 * - Conditional NVS writes based on BLE_PAIRING_TEST_MODE flag
 *
 * Security configured via global ble_hs_cfg in ble_manager_init()
 */
static bool pairing_in_progress = false;
static uint16_t pairing_conn_handle = BLE_HS_CONN_HANDLE_NONE;

// NOTE: peer_role_t typedef moved to ble_manager.h (Phase 1b.3)

// Peer device state (Phase 1a: Dual-device support)
typedef struct {
    bool peer_discovered;              /**< Peer device found via scan */
    bool peer_connected;               /**< BLE connection established to peer */
    ble_addr_t peer_addr;              /**< Peer device BLE address */
    uint16_t peer_conn_handle;         /**< Peer connection handle */
    uint8_t peer_battery_level;        /**< Peer's battery percentage (0-100) */
    bool peer_battery_known;           /**< Peer battery received via advertising (AD035) */
    uint8_t peer_mac[6];               /**< Peer's MAC address for tiebreaker */
    peer_role_t role;                  /**< Our role: CLIENT or SERVER (Phase 1b.2) */
} ble_peer_state_t;

static ble_peer_state_t peer_state = {
    .peer_discovered = false,
    .peer_connected = false,
    .peer_addr = {0},
    .peer_conn_handle = BLE_HS_CONN_HANDLE_NONE,
    .role = PEER_ROLE_NONE,
    .peer_battery_level = 0,
    .peer_battery_known = false,
    .peer_mac = {0}
};

// Bilateral Control Service characteristic data (Phase 1b: AD030/AD034)
typedef struct {
    uint8_t battery_level;      /**< Local battery percentage 0-100% */
    uint8_t mac_address[6];     /**< Local MAC address (6 bytes) */
    uint8_t device_role;        /**< Device role: 0=SERVER, 1=CLIENT, 2=CONTROLLER, 3=FOLLOWER */
} bilateral_char_data_t;

static bilateral_char_data_t bilateral_data = {
    .battery_level = 0,
    .mac_address = {0},
    .device_role = ROLE_SERVER  // Default to SERVER until role determined
};

static SemaphoreHandle_t bilateral_data_mutex = NULL;
static bool scanning_active = false;

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
    // Signature data: {uuid_ending, byte_length} pairs for all 9 saved parameters
    // NOTE: Mode (0x01) is NOT saved - device always boots to MODE_05HZ_25
    uint8_t sig_data[] = {
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

    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in update_mode5_timing - possible deadlock");
        return;  // Early return on timeout
    }
    freq = char_data.custom_frequency_hz;
    duty = char_data.custom_duty_percent;
    xSemaphoreGive(char_data_mutex);

    uint32_t period_ms = (100000 / freq);  // Full period in ms (avoid float)

    // ACTIVE/INACTIVE Architecture (50/50 split):
    // Split cycle into 50% ACTIVE and 50% INACTIVE periods
    uint32_t active_period_ms = period_ms / 2;
    uint32_t inactive_period_ms = period_ms - active_period_ms;  // Handle odd values

    // Apply duty% within ACTIVE period only (linear scaling)
    uint32_t on_time_ms = (active_period_ms * duty) / 100;
    uint32_t coast_ms = inactive_period_ms;  // Coast time is always INACTIVE period (guaranteed 50% OFF)

    // Call motor_task API to update timing
    esp_err_t err = motor_update_mode5_timing(on_time_ms, coast_ms);
    if (err == ESP_OK) {
        ESP_LOGI(TAG, "Mode 4 (Custom) updated: freq=%.2fHz duty=%u%% -> on=%ums off=%ums (50/50 split)",
                 freq / 100.0f, duty, on_time_ms, coast_ms);
    } else {
        ESP_LOGE(TAG, "Failed to update Mode 4 timing: %s", esp_err_to_name(err));
    }
}

// Mode characteristic - Read callback
static int gatt_char_mode_read(uint16_t conn_handle, uint16_t attr_handle,
                                struct ble_gatt_access_ctxt *ctxt, void *arg) {
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in gatt_char_mode_read - possible deadlock");
        return BLE_ATT_ERR_UNLIKELY;
    }
    uint8_t mode_val = (uint8_t)char_data.current_mode;
    xSemaphoreGive(char_data_mutex);

    ESP_LOGD(TAG, "GATT Read: Mode = %u", mode_val);
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

    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in gatt_char_mode_write - possible deadlock");
        return BLE_ATT_ERR_UNLIKELY;
    }
    char_data.current_mode = (mode_t)mode_val;
    settings_dirty = true;
    xSemaphoreGive(char_data_mutex);

    ble_callback_mode_changed((mode_t)mode_val);
    return 0;
}

// Custom Frequency - Read
static int gatt_char_custom_freq_read(uint16_t conn_handle, uint16_t attr_handle,
                                       struct ble_gatt_access_ctxt *ctxt, void *arg) {
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in gatt_char_custom_freq_read - possible deadlock");
        return BLE_ATT_ERR_UNLIKELY;
    }
    uint16_t freq_val = char_data.custom_frequency_hz;
    xSemaphoreGive(char_data_mutex);

    ESP_LOGD(TAG, "GATT Read: Frequency = %u (%.2f Hz)", freq_val, freq_val / 100.0f);
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

    ESP_LOGD(TAG, "GATT Write: Frequency = %u (%.2f Hz)", freq_val, freq_val / 100.0f);

    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in gatt_char_custom_freq_write - possible deadlock");
        return BLE_ATT_ERR_UNLIKELY;
    }
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
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in gatt_char_custom_duty_read - possible deadlock");
        return BLE_ATT_ERR_UNLIKELY;
    }
    uint8_t duty_val = char_data.custom_duty_percent;
    xSemaphoreGive(char_data_mutex);

    ESP_LOGD(TAG, "GATT Read: Duty = %u%%", duty_val);
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

    // AD032: Range 10-100% (10% min ensures perception, 100% max = entire half-cycle)
    // For LED-only mode, set PWM intensity to 0% instead
    if (duty_val < 10 || duty_val > 100) {
        ESP_LOGE(TAG, "GATT Write: Invalid duty %u%% (range 10-100)", duty_val);
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    ESP_LOGD(TAG, "GATT Write: Duty = %u%%", duty_val);

    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in gatt_char_custom_duty_write - possible deadlock");
        return BLE_ATT_ERR_UNLIKELY;
    }
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
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in gatt_char_pwm_intensity_read - possible deadlock");
        return BLE_ATT_ERR_UNLIKELY;
    }
    uint8_t intensity = char_data.pwm_intensity;
    xSemaphoreGive(char_data_mutex);

    ESP_LOGD(TAG, "GATT Read: PWM = %u%%", intensity);
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

    // AD031: Range 0-80% (0% = LED-only mode, no motor vibration)
    if (value > 80) {
        ESP_LOGE(TAG, "GATT Write: Invalid PWM %u%% (range 0-80)", value);
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    ESP_LOGD(TAG, "GATT Write: PWM = %u%%", value);

    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in gatt_char_pwm_intensity_write - possible deadlock");
        return BLE_ATT_ERR_UNLIKELY;
    }
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
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in gatt_char_led_enable_read - possible deadlock");
        return BLE_ATT_ERR_UNLIKELY;
    }
    uint8_t enabled = char_data.led_enable ? 1 : 0;
    xSemaphoreGive(char_data_mutex);

    ESP_LOGD(TAG, "GATT Read: LED Enable = %d", enabled);
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
    ESP_LOGD(TAG, "GATT Write: LED Enable = %d", enabled);

    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in gatt_char_led_enable_write - possible deadlock");
        return BLE_ATT_ERR_UNLIKELY;
    }
    char_data.led_enable = enabled;
    settings_dirty = true;
    xSemaphoreGive(char_data_mutex);

    ble_callback_params_updated();
    return 0;
}

// LED Color Mode - Read
static int gatt_char_led_color_mode_read(uint16_t conn_handle, uint16_t attr_handle,
                                          struct ble_gatt_access_ctxt *ctxt, void *arg) {
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in gatt_char_led_color_mode_read - possible deadlock");
        return BLE_ATT_ERR_UNLIKELY;
    }
    uint8_t mode = char_data.led_color_mode;
    xSemaphoreGive(char_data_mutex);

    ESP_LOGD(TAG, "GATT Read: LED Color Mode = %u", mode);
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

    ESP_LOGD(TAG, "GATT Write: LED Color Mode = %u (%s)",
             value, value == 0 ? "palette" : "custom RGB");

    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in gatt_char_led_color_mode_write - possible deadlock");
        return BLE_ATT_ERR_UNLIKELY;
    }
    char_data.led_color_mode = value;
    settings_dirty = true;
    xSemaphoreGive(char_data_mutex);

    ble_callback_params_updated();
    return 0;
}

// LED Palette - Read
static int gatt_char_led_palette_read(uint16_t conn_handle, uint16_t attr_handle,
                                       struct ble_gatt_access_ctxt *ctxt, void *arg) {
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in gatt_char_led_palette_read - possible deadlock");
        return BLE_ATT_ERR_UNLIKELY;
    }
    uint8_t idx = char_data.led_palette_index;
    xSemaphoreGive(char_data_mutex);

    ESP_LOGD(TAG, "GATT Read: LED Palette = %u", idx);
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

    ESP_LOGD(TAG, "GATT Write: LED Palette = %u (%s)",
             value, color_palette[value].name);

    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in gatt_char_led_palette_write - possible deadlock");
        return BLE_ATT_ERR_UNLIKELY;
    }
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

    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in gatt_char_led_custom_rgb_read - possible deadlock");
        return BLE_ATT_ERR_UNLIKELY;
    }
    rgb[0] = char_data.led_custom_r;
    rgb[1] = char_data.led_custom_g;
    rgb[2] = char_data.led_custom_b;
    xSemaphoreGive(char_data_mutex);

    ESP_LOGD(TAG, "GATT Read: LED RGB = (%u, %u, %u)", rgb[0], rgb[1], rgb[2]);
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

    ESP_LOGD(TAG, "GATT Write: LED RGB = (%u, %u, %u)", rgb[0], rgb[1], rgb[2]);

    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in gatt_char_led_custom_rgb_write - possible deadlock");
        return BLE_ATT_ERR_UNLIKELY;
    }
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
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in gatt_char_led_brightness_read - possible deadlock");
        return BLE_ATT_ERR_UNLIKELY;
    }
    uint8_t brightness = char_data.led_brightness;
    xSemaphoreGive(char_data_mutex);

    ESP_LOGD(TAG, "GATT Read: LED Brightness = %u%%", brightness);
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

    ESP_LOGD(TAG, "GATT Write: LED Brightness = %u%%", value);

    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in gatt_char_led_brightness_write - possible deadlock");
        return BLE_ATT_ERR_UNLIKELY;
    }
    char_data.led_brightness = value;
    settings_dirty = true;
    xSemaphoreGive(char_data_mutex);

    ble_callback_params_updated();
    return 0;
}

// Session Duration - Read
static int gatt_char_session_duration_read(uint16_t conn_handle, uint16_t attr_handle,
                                            struct ble_gatt_access_ctxt *ctxt, void *arg) {
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in gatt_char_session_duration_read - possible deadlock");
        return BLE_ATT_ERR_UNLIKELY;
    }
    uint32_t duration = char_data.session_duration_sec;
    xSemaphoreGive(char_data_mutex);

    ESP_LOGD(TAG, "GATT Read: Session Duration = %u sec (%.1f min)",
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

    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in gatt_char_session_duration_write - possible deadlock");
        return BLE_ATT_ERR_UNLIKELY;
    }
    char_data.session_duration_sec = value;
    settings_dirty = true;
    xSemaphoreGive(char_data_mutex);

    // Motor task will check this value to determine when to end session
    return 0;
}

// Session Time - Read
static int gatt_char_session_time_read(uint16_t conn_handle, uint16_t attr_handle,
                                        struct ble_gatt_access_ctxt *ctxt, void *arg) {
    // Calculate REAL-TIME session time instead of using cached value
    // This ensures GATT reads always return current uptime
    uint32_t session_time_ms = motor_get_session_time_ms();
    uint32_t session_time = session_time_ms / 1000;  // Convert to seconds

    ESP_LOGD(TAG, "GATT Read: Session Time = %u sec", session_time);
    int rc = os_mbuf_append(ctxt->om, &session_time, sizeof(session_time));
    return (rc == 0) ? 0 : BLE_ATT_ERR_INSUFFICIENT_RES;
}

// Battery Level - Read
static int gatt_char_battery_read(uint16_t conn_handle, uint16_t attr_handle,
                                   struct ble_gatt_access_ctxt *ctxt, void *arg) {
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in gatt_char_battery_read - possible deadlock");
        return BLE_ATT_ERR_UNLIKELY;
    }
    uint8_t battery_val = char_data.battery_level;
    xSemaphoreGive(char_data_mutex);

    ESP_LOGD(TAG, "GATT Read: Battery = %u%%", battery_val);
    int rc = os_mbuf_append(ctxt->om, &battery_val, sizeof(battery_val));
    return (rc == 0) ? 0 : BLE_ATT_ERR_INSUFFICIENT_RES;
}

// ============================================================================
// BILATERAL CONTROL SERVICE CHARACTERISTIC HANDLERS (Phase 1b: AD030/AD034)
// ============================================================================

// Bilateral Battery Level - Read (for peer device role comparison)
static int gatt_bilateral_battery_read(uint16_t conn_handle, uint16_t attr_handle,
                                        struct ble_gatt_access_ctxt *ctxt, void *arg) {
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(bilateral_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in gatt_bilateral_battery_read - possible deadlock");
        return BLE_ATT_ERR_UNLIKELY;
    }
    uint8_t battery_val = bilateral_data.battery_level;
    xSemaphoreGive(bilateral_data_mutex);

    ESP_LOGD(TAG, "GATT Read: Bilateral Battery = %u%%", battery_val);
    int rc = os_mbuf_append(ctxt->om, &battery_val, sizeof(battery_val));
    return (rc == 0) ? 0 : BLE_ATT_ERR_INSUFFICIENT_RES;
}

// Bilateral MAC Address - Read (for role assignment tiebreaker)
static int gatt_bilateral_mac_read(uint16_t conn_handle, uint16_t attr_handle,
                                    struct ble_gatt_access_ctxt *ctxt, void *arg) {
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(bilateral_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in gatt_bilateral_mac_read - possible deadlock");
        return BLE_ATT_ERR_UNLIKELY;
    }
    uint8_t mac[6];
    memcpy(mac, bilateral_data.mac_address, 6);
    xSemaphoreGive(bilateral_data_mutex);

    ESP_LOGD(TAG, "GATT Read: MAC = %02X:%02X:%02X:%02X:%02X:%02X",
             mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
    int rc = os_mbuf_append(ctxt->om, mac, 6);
    return (rc == 0) ? 0 : BLE_ATT_ERR_INSUFFICIENT_RES;
}

// Bilateral Device Role - Read/Write
static int gatt_bilateral_role_read(uint16_t conn_handle, uint16_t attr_handle,
                                     struct ble_gatt_access_ctxt *ctxt, void *arg) {
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(bilateral_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in gatt_bilateral_role_read - possible deadlock");
        return BLE_ATT_ERR_UNLIKELY;
    }
    uint8_t role = bilateral_data.device_role;
    xSemaphoreGive(bilateral_data_mutex);

    ESP_LOGD(TAG, "GATT Read: Device Role = %u", role);
    int rc = os_mbuf_append(ctxt->om, &role, sizeof(role));
    return (rc == 0) ? 0 : BLE_ATT_ERR_INSUFFICIENT_RES;
}

static int gatt_bilateral_role_write(uint16_t conn_handle, uint16_t attr_handle,
                                      struct ble_gatt_access_ctxt *ctxt, void *arg) {
    uint8_t role;
    int rc = ble_hs_mbuf_to_flat(ctxt->om, &role, sizeof(role), NULL);
    if (rc != 0) {
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    // Validate role value (0-3: SERVER, CLIENT, CONTROLLER, FOLLOWER)
    if (role > 3) {
        ESP_LOGE(TAG, "GATT Write: Invalid role %u (valid: 0-3)", role);
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    ESP_LOGI(TAG, "GATT Write: Device Role = %u", role);
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(bilateral_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in gatt_bilateral_role_write - possible deadlock");
        return BLE_ATT_ERR_UNLIKELY;
    }
    bilateral_data.device_role = role;
    xSemaphoreGive(bilateral_data_mutex);

    // Update role_manager with new role
    role_set((device_role_t)role);

    return 0;
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

    // Bilateral Control Service characteristics (Phase 1b)
    if (ble_uuid_cmp(uuid, &uuid_bilateral_battery.u) == 0) {
        return gatt_bilateral_battery_read(conn_handle, attr_handle, ctxt, arg);
    }

    if (ble_uuid_cmp(uuid, &uuid_bilateral_mac.u) == 0) {
        return gatt_bilateral_mac_read(conn_handle, attr_handle, ctxt, arg);
    }

    if (ble_uuid_cmp(uuid, &uuid_bilateral_role.u) == 0) {
        return (ctxt->op == BLE_GATT_ACCESS_OP_READ_CHR) ?
               gatt_bilateral_role_read(conn_handle, attr_handle, ctxt, arg) :
               gatt_bilateral_role_write(conn_handle, attr_handle, ctxt, arg);
    }

    // Unknown characteristic
    return BLE_ATT_ERR_UNLIKELY;
}

// ============================================================================
// GATT SERVICE DEFINITION (AD030 + AD032)
// ============================================================================

static const struct ble_gatt_svc_def gatt_svr_svcs[] = {
    {
        // Bilateral Control Service (UUID: 6E400001-...) - Phase 1b: AD030/AD034
        // Device-to-device coordination for dual-device operation
        .type = BLE_GATT_SVC_TYPE_PRIMARY,
        .uuid = &uuid_bilateral_service.u,
        .characteristics = (struct ble_gatt_chr_def[]){
            {
                .uuid = &uuid_bilateral_battery.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_READ,
            },
            {
                .uuid = &uuid_bilateral_mac.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_READ,
            },
            {
                .uuid = &uuid_bilateral_role.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_WRITE,
            },
            {
                0, // No more characteristics
            }
        },
    },
    {
        // Configuration Service (UUID: 6E400002-...) - AD032
        .type = BLE_GATT_SVC_TYPE_PRIMARY,
        .uuid = &uuid_config_service.u,
        .characteristics = (struct ble_gatt_chr_def[]){
            // Motor Control Group
            {
                .uuid = &uuid_char_mode.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_WRITE | BLE_GATT_CHR_F_NOTIFY,
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

/**
 * @brief Decode BLE disconnect reason code to human-readable string
 * @param reason BLE disconnect reason code
 * @return Human-readable string describing the disconnect reason
 */
static const char* ble_disconnect_reason_str(uint8_t reason) {
    switch (reason) {
        case 0x08: return "Connection Timeout";
        case 0x13: return "Remote User Terminated";
        case 0x14: return "Remote Device Terminated (Low Resources)";
        case 0x15: return "Remote Device Terminated (Power Off)";
        case 0x16: return "Connection Terminated by Local Host";
        case 0x22: return "Connection Failed to be Established";
        case 0x3E: return "Connection Failed (LMP Response Timeout)";
        default:   return "Unknown";
    }
}

/**
 * @brief Decode BLE connection status code to human-readable string
 * @param status BLE connection status code
 * @return Human-readable string describing the connection status
 */
static const char* ble_connect_status_str(uint8_t status) {
    switch (status) {
        case 0:    return "Success";
        case 2:    return "Unknown HCI Error";
        case 5:    return "Authentication Failure";
        case 6:    return "PIN or Key Missing";
        case 7:    return "Memory Capacity Exceeded";
        case 8:    return "Connection Timeout";
        case 13:   return "Remote Terminated (User)";
        case 14:   return "Remote Terminated (Low Resources)";
        case 15:   return "Remote Terminated (Power Off)";
        case 22:   return "LMP Response Timeout";
        case 26:   return "Unsupported Remote Feature";
        case 34:   return "LMP Error Transaction Collision";
        case 40:   return "Advertising Timeout";
        default:   return "Unknown Status";
    }
}

static int ble_gap_event(struct ble_gap_event *event, void *arg) {
    int rc;

    switch (event->type) {
        case BLE_GAP_EVENT_CONNECT:
            if (event->connect.status == 0) {
                ESP_LOGI(TAG, "BLE connection established; conn_handle=%d", event->connect.conn_handle);

                // Get connection descriptor
                struct ble_gap_conn_desc desc;
                if (ble_gap_conn_find(event->connect.conn_handle, &desc) != 0) {
                    ESP_LOGE(TAG, "Failed to get connection descriptor");
                    ble_gap_terminate(event->connect.conn_handle, BLE_ERR_REM_USER_CONN_TERM);
                    break;
                }

                // Check if device is bonded
                union ble_store_value bond_value;
                union ble_store_key bond_key;
                memset(&bond_key, 0, sizeof(bond_key));
                bond_key.sec.peer_addr = desc.peer_id_addr;
                int bond_rc = ble_store_read(BLE_STORE_OBJ_TYPE_OUR_SEC, &bond_key, &bond_value);
                bool is_bonded = (bond_rc == 0);

                // CRITICAL: Determine connection type BEFORE applying security
                // Phase 1b.3: UUID-based connection identification (SIMPLIFIED)
                // No more grace period, state machine complexity, or timing windows!
                // Connection type is determined by which UUID we're currently advertising:
                // - Bilateral UUID (0-30s): Only peers can discover → connection = peer
                // - Config UUID (30s+): Apps can discover, bonded peers reconnect by address
                bool is_peer = false;

                // Get currently advertised UUID to determine connection type
                const ble_uuid128_t *current_uuid = ble_get_advertised_uuid();

                if (current_uuid == &uuid_bilateral_service) {
                    // CASE 1: Advertising Bilateral UUID - this connection is from peer discovery
                    // Mobile apps CANNOT discover device during Bilateral UUID window (Bug #27 eliminated!)
                    is_peer = true;
                    peer_state.peer_discovered = true;
                    memcpy(&peer_state.peer_addr, &desc.peer_id_addr, sizeof(ble_addr_t));
                    ESP_LOGI(TAG, "Peer identified (connected during Bilateral UUID window)");
                } else {
                    // CASE 2: Advertising Config UUID - check if this is bonded peer reconnect
                    if (memcmp(&desc.peer_id_addr, &peer_state.peer_addr, sizeof(ble_addr_t)) == 0 &&
                        peer_state.peer_discovered) {
                        // Cached address match - bonded peer reconnecting
                        is_peer = true;
                        ESP_LOGI(TAG, "Peer identified (bonded reconnection by address)");
                    } else {
                        // New connection during Config UUID window - mobile app
                        is_peer = false;
                        ESP_LOGI(TAG, "Mobile app connected; conn_handle=%d", event->connect.conn_handle);
                    }
                }


                // SECURITY: Apply connection-type-specific security rules (Phase 1b.3)
                if (is_peer) {
                    // ===== PEER CONNECTION SECURITY =====
                    // UUID-switching enforces pairing window automatically:
                    // - Bilateral UUID (0-30s): Unbonded peers allowed (initial pairing)
                    // - Config UUID (30s+): Only bonded peers reconnect (unbonded = app)
                    //
                    // EXCLUSIVE PAIRING: Once a peer is bonded, ONLY that peer can connect
                    // This ensures devices remain paired until explicit NVS erase
                    ble_addr_t bonded_peer_addr;
                    if (ble_get_bonded_peer_addr(&bonded_peer_addr)) {
                        // We have a bonded peer in NVS - check if this connection is from that peer
                        if (memcmp(&desc.peer_id_addr, &bonded_peer_addr, sizeof(ble_addr_t)) != 0) {
                            // Different peer trying to connect - reject
                            ESP_LOGW(TAG, "EXCLUSIVE PAIRING: Rejecting peer connection from %02X:%02X:%02X:%02X:%02X:%02X",
                                     desc.peer_id_addr.val[0], desc.peer_id_addr.val[1], desc.peer_id_addr.val[2],
                                     desc.peer_id_addr.val[3], desc.peer_id_addr.val[4], desc.peer_id_addr.val[5]);
                            ESP_LOGW(TAG, "  Different peer already bonded - NVS erase required to re-pair");
                            ble_gap_terminate(event->connect.conn_handle, BLE_ERR_REM_USER_CONN_TERM);
                            break;
                        } else {
                            ESP_LOGI(TAG, "EXCLUSIVE PAIRING: Bonded peer reconnecting (address match verified)");
                        }
                    }

                    // Security check: Prevent multiple peer connections
                    if (!is_bonded && peer_state.peer_connected) {
                        ESP_LOGW(TAG, "Rejecting unbonded peer (bonded peer already connected)");
                        ble_gap_terminate(event->connect.conn_handle, BLE_ERR_REM_USER_CONN_TERM);
                        break;
                    }

                    if (is_bonded) {
                        ESP_LOGI(TAG, "Bonded peer reconnecting (allowed anytime via Config UUID)");
                    } else {
                        ESP_LOGI(TAG, "Unbonded peer connecting (within 30s Bilateral UUID window - allowed for pairing)");
                    }
                }

                // ===== CONNECTION TYPE HANDLING =====
                if (is_peer) {
                    // Check if we already have a peer connection
                    if (peer_state.peer_connected) {
                        ESP_LOGW(TAG, "Already connected to peer, rejecting duplicate peer connection");
                        ble_gap_terminate(event->connect.conn_handle, BLE_ERR_REM_USER_CONN_TERM);
                        break;
                    }

                    // Accept peer connection
                    peer_state.peer_connected = true;
                    peer_state.peer_conn_handle = event->connect.conn_handle;
                    ESP_LOGI(TAG, "Peer device connected; conn_handle=%d", event->connect.conn_handle);

                    // Stop scanning once peer connected
                    if (scanning_active) {
                        int scan_rc = ble_gap_disc_cancel();
                        if (scan_rc == 0 || scan_rc == BLE_HS_EALREADY) {
                            scanning_active = false;
                            ESP_LOGI(TAG, "Scanning stopped (peer connected)");
                        } else {
                            ESP_LOGW(TAG, "Failed to stop scanning; rc=%d", scan_rc);
                        }
                    }

                    // CRITICAL FIX (Bug #16): Assign role FIRST, regardless of advertising state
                    // Use desc.role from NimBLE to determine connection initiator
                    // BLE_GAP_ROLE_MASTER (0) = we initiated connection (CLIENT)
                    // BLE_GAP_ROLE_SLAVE (1) = peer initiated connection to us (SERVER)
                    bool we_initiated = (desc.role == BLE_GAP_ROLE_MASTER);

                    if (we_initiated) {
                        peer_state.role = PEER_ROLE_CLIENT;
                        ESP_LOGI(TAG, "CLIENT role assigned (BLE MASTER)");
                    } else {
                        peer_state.role = PEER_ROLE_SERVER;
                        ESP_LOGI(TAG, "SERVER role assigned (BLE SLAVE)");
                    }

                    // Role-aware advertising strategy (Phase 1b.3 - Bug #26 fix):
                    // - CLIENT (initiated connection): Stop advertising immediately
                    // - SERVER (received connection): BLE_TASK will restart advertising after pairing
                    //
                    // BUG #26 FIX: Don't restart advertising immediately here (timing race with NimBLE controller)
                    // Immediate restart (20ms after connection) causes intermittent BLE_HS_ECONTROLLER errors (rc=6)
                    // BLE_TASK handles advertising restart in PAIRING → ADVERTISING transition (~4s later)
                    if (adv_state.advertising_active) {
                        if (we_initiated) {
                            // CLIENT: Stop advertising (we don't need more connections)
                            ble_gap_adv_stop();
                            adv_state.advertising_active = false;
                            ESP_LOGI(TAG, "CLIENT: Advertising stopped (prevents timeout)");
                        } else {
                            // SERVER: Stop advertising now, BLE_TASK will restart after pairing completes
                            // This prevents timing race with NimBLE controller initialization
                            ble_gap_adv_stop();
                            adv_state.advertising_active = false;
                            ESP_LOGI(TAG, "SERVER: Advertising stopped (will restart after pairing)");
                        }
                    }
                } else {
                    // ===== APP CONNECTION HANDLING =====
                    // Check if we already have an app connection
                    if (adv_state.client_connected) {
                        ESP_LOGW(TAG, "Already connected to app, rejecting duplicate app connection");
                        ble_gap_terminate(event->connect.conn_handle, BLE_ERR_REM_USER_CONN_TERM);
                        break;
                    }

                    // Accept mobile app connection
                    adv_state.client_connected = true;
                    adv_state.conn_handle = event->connect.conn_handle;
                    ESP_LOGI(TAG, "Mobile app connected; conn_handle=%d", event->connect.conn_handle);

                    // Stop advertising (have both connections or just app)
                    if (adv_state.advertising_active) {
                        ble_gap_adv_stop();
                        adv_state.advertising_active = false;
                        ESP_LOGI(TAG, "Advertising stopped (mobile app connected)");
                    }

                    // Clear subscription flags (client must resubscribe)
                    adv_state.notify_mode_subscribed = false;
                    adv_state.notify_session_time_subscribed = false;
                    adv_state.notify_battery_subscribed = false;
                }
            } else {
                ESP_LOGW(TAG, "BLE connection failed; status=%d (%s)",
                         event->connect.status,
                         ble_connect_status_str(event->connect.status));

                // Phase 1a: Reset peer discovery on connection failure
                if (peer_state.peer_discovered) {
                    ESP_LOGW(TAG, "Peer connection failed, will retry discovery");
                    peer_state.peer_discovered = false;
                    peer_state.peer_connected = false;

                    // Resume scanning for retry
                    if (!scanning_active) {
                        vTaskDelay(pdMS_TO_TICKS(1000));  // Brief delay before retry
                        ble_start_scanning();
                    }
                }
            }
            break;

        case BLE_GAP_EVENT_DISCONNECT:
            // Mask to 1 byte (BLE spec uses 1-byte reason codes)
            ESP_LOGI(TAG, "BLE disconnect; conn_handle=%d, reason=0x%02X (%s)",
                     event->disconnect.conn.conn_handle,
                     event->disconnect.reason & 0xFF,
                     ble_disconnect_reason_str(event->disconnect.reason & 0xFF));

            // Phase 1a: Determine if this is peer or mobile app disconnect
            // CRITICAL: Check BOTH connection handles explicitly (don't use else!)
            bool peer_disconnected = (peer_state.peer_connected &&
                                      event->disconnect.conn.conn_handle == peer_state.peer_conn_handle);
            bool app_disconnected = (adv_state.client_connected &&
                                     event->disconnect.conn.conn_handle == adv_state.conn_handle);

            if (peer_disconnected) {
                // Peer device disconnected
                ESP_LOGI(TAG, "Peer device disconnected");
                peer_state.peer_connected = false;
                peer_state.peer_discovered = false;
                peer_state.peer_conn_handle = BLE_HS_CONN_HANDLE_NONE;
                peer_state.role = PEER_ROLE_NONE;

                // JPL compliance: Allow NimBLE to fully clean up connection handle
                // Measured reconnection timing from logs:
                //   - Immediate retry (2s after disconnect) → BLE_ERR_UNK_CONN_ID errors
                //   - Success after 46 seconds (NimBLE finished cleanup)
                // Solution: 2-second delay prevents immediate retry errors
                vTaskDelay(pdMS_TO_TICKS(2000));

                // CRITICAL FIX (Phase 1b.2): Restart advertising + scanning for peer rediscovery
                // Phase 1b.2 stopped advertising after peer connection, so we must restart it here
                // Don't rely on advertising_active flag - explicitly restart both services
                rc = ble_gap_adv_start(BLE_OWN_ADDR_PUBLIC, NULL, BLE_HS_FOREVER,
                                       &adv_params, ble_gap_event, NULL);
                if (rc == 0) {
                    adv_state.advertising_active = true;
                    adv_state.advertising_start_ms = (uint32_t)(esp_timer_get_time() / 1000);
                    ESP_LOGI(TAG, "Advertising restarted after peer disconnect");

                    // Resume scanning for peer rediscovery
                    ble_start_scanning();
                    ESP_LOGI(TAG, "Scanning restarted for peer rediscovery");
                } else {
                    ESP_LOGE(TAG, "Failed to restart advertising after peer disconnect; rc=%d", rc);
                    // Sync flag with actual NimBLE state (handles BLE_HS_EALREADY case)
                    adv_state.advertising_active = ble_gap_adv_active();
                    // BLE task will retry via state machine
                }
            }

            if (app_disconnected) {
                // Mobile app disconnected
                ESP_LOGI(TAG, "Mobile app disconnected");
                adv_state.client_connected = false;
                adv_state.conn_handle = BLE_HS_CONN_HANDLE_NONE;
                adv_state.notify_mode_subscribed = false;
                adv_state.notify_session_time_subscribed = false;
                adv_state.notify_battery_subscribed = false;

                // Small delay to allow BLE stack cleanup (Android compatibility)
                vTaskDelay(pdMS_TO_TICKS(100));

                // Resume advertising on mobile app disconnect (if not already restarted by peer disconnect)
                if (!adv_state.advertising_active) {
                    rc = ble_gap_adv_start(BLE_OWN_ADDR_PUBLIC, NULL, BLE_HS_FOREVER,
                                           &adv_params, ble_gap_event, NULL);
                    if (rc == 0) {
                        adv_state.advertising_active = true;
                        adv_state.advertising_start_ms = (uint32_t)(esp_timer_get_time() / 1000);
                        ESP_LOGI(TAG, "BLE advertising restarted after mobile app disconnect");
                    } else {
                        ESP_LOGE(TAG, "Failed to restart advertising after disconnect; rc=%d", rc);
                        // Sync flag with actual NimBLE state (handles BLE_HS_EALREADY case)
                        adv_state.advertising_active = ble_gap_adv_active();
                        // BLE task will retry via CHECK_ADVERTISING_STATE message
                    }
                } else {
                    ESP_LOGI(TAG, "Advertising already active (peer still connected)");
                }
            }

            if (!peer_disconnected && !app_disconnected) {
                ESP_LOGW(TAG, "Unknown connection disconnected; conn_handle=%d",
                         event->disconnect.conn.conn_handle);
            }
            break;

        case BLE_GAP_EVENT_ADV_COMPLETE:
            ESP_LOGI(TAG, "BLE advertising complete; reason=%d", event->adv_complete.reason);
            adv_state.advertising_active = false;
            break;

        case BLE_GAP_EVENT_CONN_UPDATE:
            ESP_LOGI(TAG, "BLE conn params updated; status=%d", event->conn_update.status);
            break;

        case BLE_GAP_EVENT_CONN_UPDATE_REQ:
            ESP_LOGI(TAG, "BLE conn params update requested");
            break;

        case BLE_GAP_EVENT_MTU:
            ESP_LOGI(TAG, "BLE MTU exchange: %u bytes", event->mtu.value);
            break;

        case BLE_GAP_EVENT_SUBSCRIBE:
            ESP_LOGI(TAG, "BLE characteristic subscription: handle=%u, cur_notify=%d, cur_indicate=%d",
                     event->subscribe.attr_handle,
                     event->subscribe.cur_notify,
                     event->subscribe.cur_indicate);

            // Find which characteristic was subscribed to by comparing handles
            uint16_t val_handle;

            if (ble_gatts_find_chr(&uuid_config_service.u, &uuid_char_mode.u, NULL, &val_handle) == 0) {
                if (event->subscribe.attr_handle == val_handle) {
                    adv_state.notify_mode_subscribed = event->subscribe.cur_notify;
                    ESP_LOGI(TAG, "Mode notifications %s", event->subscribe.cur_notify ? "enabled" : "disabled");
                }
            }

            if (ble_gatts_find_chr(&uuid_config_service.u, &uuid_char_session_time.u, NULL, &val_handle) == 0) {
                if (event->subscribe.attr_handle == val_handle) {
                    adv_state.notify_session_time_subscribed = event->subscribe.cur_notify;
                    ESP_LOGI(TAG, "Session Time notifications %s", event->subscribe.cur_notify ? "enabled" : "disabled");

                        // Send initial value immediately on subscription
                    if (event->subscribe.cur_notify) {
                        // Get REAL-TIME session time instead of cached value
                        // This ensures clients connecting within first 60s get correct uptime
                        uint32_t current_time_ms = motor_get_session_time_ms();
                        uint32_t current_time_sec = current_time_ms / 1000;

                        struct os_mbuf *om = ble_hs_mbuf_from_flat(&current_time_sec, sizeof(current_time_sec));
                        if (om != NULL) {
                            int rc = ble_gatts_notify_custom(adv_state.conn_handle, val_handle, om);
                            if (rc == 0) {
                                ESP_LOGI(TAG, "Initial session time sent: %lu seconds", current_time_sec);
                            }
                        }
                    }
                }
            }

            if (ble_gatts_find_chr(&uuid_config_service.u, &uuid_char_battery.u, NULL, &val_handle) == 0) {
                if (event->subscribe.attr_handle == val_handle) {
                    adv_state.notify_battery_subscribed = event->subscribe.cur_notify;
                    ESP_LOGI(TAG, "Battery notifications %s", event->subscribe.cur_notify ? "enabled" : "disabled");

                    // Send initial value immediately on subscription
                    if (event->subscribe.cur_notify) {
                        uint8_t current_battery;
                        // JPL compliance: Bounded mutex wait with timeout error handling
                        if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
                            ESP_LOGE(TAG, "Mutex timeout in GAP event handler (battery notify) - possible deadlock");
                            return 0;
                        }
                        current_battery = char_data.battery_level;
                        xSemaphoreGive(char_data_mutex);

                        struct os_mbuf *om = ble_hs_mbuf_from_flat(&current_battery, sizeof(current_battery));
                        if (om != NULL) {
                            int rc = ble_gatts_notify_custom(adv_state.conn_handle, val_handle, om);
                            if (rc == 0) {
                                ESP_LOGI(TAG, "Initial battery level sent: %u%%", current_battery);
                            }
                        }
                    }
                }
            }
            break;

        case BLE_GAP_EVENT_ENC_CHANGE: {
            // Encryption state changed (pairing started or completed)
            ESP_LOGI(TAG, "BLE encryption change; conn_handle=%d, status=%d",
                     event->enc_change.conn_handle, event->enc_change.status);

            // CRITICAL: Only trigger pairing workflow for PEER connections
            // Mobile app/PWA connections can encrypt without triggering motor task wait
            bool is_peer_connection = (event->enc_change.conn_handle == peer_state.peer_conn_handle);

            if (!is_peer_connection) {
                // App connection - allow encryption but don't trigger pairing workflow
                if (event->enc_change.status == 0) {
                    ESP_LOGI(TAG, "App connection encrypted successfully (no pairing workflow)");
                } else {
                    ESP_LOGI(TAG, "App connection encryption in progress (no pairing workflow)");
                }
                break;
            }

            // This is a PEER connection - handle pairing workflow
            if (event->enc_change.status == 0) {
                // Peer pairing completed successfully
                pairing_in_progress = false;
                pairing_conn_handle = BLE_HS_CONN_HANDLE_NONE;
                ESP_LOGI(TAG, "PEER pairing completed successfully");

                // Send success message to motor_task (Phase 1b.3)
                extern QueueHandle_t ble_to_motor_queue;
                if (ble_to_motor_queue != NULL) {
                    task_message_t msg = {
                        .type = MSG_PAIRING_COMPLETE,
                        .data = {.new_mode = 0}
                    };
                    if (xQueueSend(ble_to_motor_queue, &msg, pdMS_TO_TICKS(100)) != pdTRUE) {
                        ESP_LOGW(TAG, "Failed to send peer pairing complete message");
                    } else {
                        ESP_LOGI(TAG, "Peer pairing complete message sent to motor_task");
                    }
                }
            } else {
                // Peer pairing in progress or failed
                // Check if this is a pairing request
                if (!pairing_in_progress) {
                    // New peer pairing request
                    pairing_in_progress = true;
                    pairing_conn_handle = event->enc_change.conn_handle;
                    ESP_LOGI(TAG, "PEER pairing started; conn_handle=%d", pairing_conn_handle);
                } else {
                    // Peer pairing failed
                    pairing_in_progress = false;
                    pairing_conn_handle = BLE_HS_CONN_HANDLE_NONE;
                    ESP_LOGW(TAG, "PEER pairing failed: status=%d", event->enc_change.status);

                    // Send failure message to motor_task
                    extern QueueHandle_t ble_to_motor_queue;
                    if (ble_to_motor_queue != NULL) {
                        task_message_t msg = {
                            .type = MSG_PAIRING_FAILED,
                            .data = {.new_mode = 0}
                        };
                        xQueueSend(ble_to_motor_queue, &msg, pdMS_TO_TICKS(100));
                    }
                }
            }
            break;
        }

        default:
            break;
    }
    return 0;
}

// ============================================================================
// UUID-SWITCHING HELPER FUNCTIONS (Phase 1b.3)
// ============================================================================

/**
 * @brief Determine which UUID to advertise based on timing and pairing state
 * @return Pointer to UUID to advertise (Bilateral or Config)
 *
 * Logic:
 * - No peer bonded AND within 30s: Bilateral UUID (peer discovery only)
 * - Peer bonded OR after 30s: Config UUID (app discovery + bonded peer reconnect)
 *
 * This eliminates complex state-based connection identification by preventing
 * wrong connection types at the BLE scan level (pre-connection).
 */
static const ble_uuid128_t* ble_get_advertised_uuid(void) {
    uint32_t now_ms = (uint32_t)(esp_timer_get_time() / 1000);
    uint32_t elapsed_ms = now_ms - ble_boot_time_ms;

    // Check if peer already bonded (NVS check) OR peer currently connected
    bool peer_bonded = ble_check_bonded_peer_exists();
    bool peer_connected = ble_is_peer_connected();

    if (!peer_bonded && !peer_connected && elapsed_ms < PAIRING_WINDOW_MS) {
        // Within pairing window, no peer bonded/connected yet - advertise Bilateral UUID
        // Mobile apps cannot discover device during this window (security benefit)
        return &uuid_bilateral_service;
    } else {
        // After pairing window OR peer bonded/connected - advertise Config UUID
        // Apps can discover device, bonded peers reconnect by address (no scan needed)
        return &uuid_config_service;
    }
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

    // BONDING FIX (Bug #19): Only use PUBLIC address for stable device identity
    // Random addresses break bonding - devices MUST have consistent MAC for pairing
    uint8_t addr_val[6];
    int is_nrpa;  // NimBLE API requires int*, not uint8_t*
    rc = ble_hs_id_copy_addr(BLE_ADDR_PUBLIC, addr_val, &is_nrpa);

    if (rc == 0) {
        // CRITICAL FIX (Bug #21): NimBLE stores MAC in reverse byte order
        // For MAC b4:3a:45:89:45:de, addr_val = [de, 45, 89, 45, 3a, b4]
        // We want LAST 3 bytes of actual MAC (89:45:de) = addr_val[2], addr_val[1], addr_val[0]
        char unique_name[32];
        snprintf(unique_name, sizeof(unique_name), "%s_%02X%02X%02X",
                 BLE_DEVICE_NAME, addr_val[2], addr_val[1], addr_val[0]);
        ble_svc_gap_device_name_set(unique_name);
        ESP_LOGI(TAG, "BLE device name: %s (MAC: %02X:%02X:%02X:%02X:%02X:%02X)",
                 unique_name, addr_val[5], addr_val[4], addr_val[3],
                 addr_val[2], addr_val[1], addr_val[0]);
    } else {
        ESP_LOGE(TAG, "CRITICAL: Failed to get PUBLIC MAC address; rc=%d (bonding requires stable identity!)", rc);
    }

    // Configure advertising data (main packet: flags + name only, fits in 31 bytes)
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

    // Configure scan response with dynamic UUID (Phase 1b.3 UUID-switching)
    // - 0-30s: Bilateral Service UUID (0x0100) - peer discovery only
    // - 30s+: Configuration Service UUID (0x0200) - app discovery + bonded peer reconnect
    // Using scan response prevents exceeding 31-byte advertising packet limit
    struct ble_hs_adv_fields rsp_fields;
    memset(&rsp_fields, 0, sizeof(rsp_fields));

    // Get UUID to advertise based on timing and bonding state
    const ble_uuid128_t *advertised_uuid = ble_get_advertised_uuid();
    rsp_fields.uuids128 = advertised_uuid;
    rsp_fields.num_uuids128 = 1;
    rsp_fields.uuids128_is_complete = 1;

    ESP_LOGI(TAG, "Advertising UUID: %s",
             (advertised_uuid == &uuid_bilateral_service) ? "Bilateral (peer discovery)" : "Config (app + bonded peer)");

    rc = ble_gap_adv_rsp_set_fields(&rsp_fields);
    if (rc != 0) {
        ESP_LOGE(TAG, "Failed to set scan response data; rc=%d", rc);
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
    // NOTE: Mode is NOT saved - device always boots to MODE_05HZ_25
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in ble_settings_save_to_nvs - possible deadlock");
        nvs_close(nvs_handle);
        return ESP_ERR_TIMEOUT;
    }
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
    // NOTE: Mode is NOT loaded - device always boots to MODE_05HZ_25
    uint8_t duty, led_en, led_cmode, led_pal, r, g, b, led_bri, pwm;
    uint16_t freq;
    uint32_t sess_dur;

    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in ble_settings_load_from_nvs - possible deadlock");
        nvs_close(nvs_handle);
        return ESP_ERR_TIMEOUT;
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

    // Initialize boot timestamp for UUID-switching (Phase 1b.3)
    ble_boot_time_ms = (uint32_t)(esp_timer_get_time() / 1000);
    ESP_LOGI(TAG, "BLE boot timestamp: %lu ms (30s pairing window)", ble_boot_time_ms);

    // Create mutexes
    char_data_mutex = xSemaphoreCreateMutex();
    if (char_data_mutex == NULL) {
        ESP_LOGE(TAG, "Failed to create char_data mutex");
        return ESP_FAIL;
    }

    bilateral_data_mutex = xSemaphoreCreateMutex();
    if (bilateral_data_mutex == NULL) {
        ESP_LOGE(TAG, "Failed to create bilateral_data mutex");
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

    // Get local MAC address for Bilateral Control Service (Phase 1b)
    // This is needed for role assignment tiebreaker (AD034)
    uint8_t own_addr[6];
    int is_nrpa;  // NimBLE API requires int*, not uint8_t*
    ret = ble_hs_id_copy_addr(BLE_ADDR_PUBLIC, own_addr, &is_nrpa);

    if (ret == ESP_OK) {
        // JPL compliance: Bounded mutex wait with timeout error handling
        if (xSemaphoreTake(bilateral_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
            ESP_LOGE(TAG, "Mutex timeout in ble_manager_init (MAC copy) - possible deadlock");
            return ESP_ERR_TIMEOUT;
        }
        memcpy(bilateral_data.mac_address, own_addr, 6);
        xSemaphoreGive(bilateral_data_mutex);
        ESP_LOGI(TAG, "Local MAC: %02X:%02X:%02X:%02X:%02X:%02X",
                 own_addr[0], own_addr[1], own_addr[2], own_addr[3], own_addr[4], own_addr[5]);
    } else {
        ESP_LOGW(TAG, "Failed to get MAC address, will retry after sync");
    }

    // Configure callbacks
    ble_hs_cfg.reset_cb = ble_on_reset;
    ble_hs_cfg.sync_cb = ble_on_sync;
    ble_hs_cfg.gatts_register_cb = gatt_svr_register_cb;

    // Configure BLE security (Phase 1b.3: Pairing/Bonding)
    // LE Secure Connections with MITM protection via button confirmation
    ble_hs_cfg.sm_io_cap = BLE_SM_IO_CAP_KEYBOARD_DISP;  // Support numeric comparison
    ble_hs_cfg.sm_bonding = 1;                               // Enable bonding (store keys)
    ble_hs_cfg.sm_mitm = 1;                                  // Require MITM protection
    ble_hs_cfg.sm_sc = 1;                                    // Use LE Secure Connections (ECDH)
    ble_hs_cfg.sm_our_key_dist = BLE_SM_PAIR_KEY_DIST_ENC | BLE_SM_PAIR_KEY_DIST_ID;
    ble_hs_cfg.sm_their_key_dist = BLE_SM_PAIR_KEY_DIST_ENC | BLE_SM_PAIR_KEY_DIST_ID;

#ifdef BLE_PAIRING_TEST_MODE
    // Test mode: RAM-only bonding (no NVS writes)
    // Setting store_status_cb to NULL prevents NimBLE from writing pairing data to NVS
    // Bonding data is kept in RAM only and cleared on reboot
    // This allows unlimited pairing test cycles without flash wear
    ble_hs_cfg.store_status_cb = NULL;
    ESP_LOGW(TAG, "BLE_PAIRING_TEST_MODE enabled - bonding data will NOT persist across reboots (RAM only)");
#else
    // Production mode: Persistent bonding via NVS
    // ble_store_util_status_rr callback triggers NVS writes when bonding keys are generated
    ble_hs_cfg.store_status_cb = ble_store_util_status_rr;
    ESP_LOGI(TAG, "BLE bonding enabled - pairing data will persist in NVS");
#endif

    ESP_LOGI(TAG, "BLE security configured: LE SC + MITM + bonding");

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

/**
 * @brief Update scan response with current UUID based on timing and bonding state
 *
 * Called before starting/restarting advertising to ensure correct UUID is advertised:
 * - 0-30s: Bilateral UUID (peer discovery)
 * - 30s+: Config UUID (app discovery)
 *
 * Phase 1b.3 UUID-switching fix for Bug #30
 */
static void ble_update_scan_response(void) {
    struct ble_hs_adv_fields rsp_fields;
    memset(&rsp_fields, 0, sizeof(rsp_fields));

    // Get current UUID based on timing and bonding state
    const ble_uuid128_t *advertised_uuid = ble_get_advertised_uuid();
    rsp_fields.uuids128 = advertised_uuid;
    rsp_fields.num_uuids128 = 1;
    rsp_fields.uuids128_is_complete = 1;

    // AD035: Add battery level as Service Data for role assignment
    // Battery Service UUID (0x180F) + battery percentage (0-100)
    // Only broadcast during Bilateral UUID window (peer discovery phase)
    static uint8_t battery_svc_data[3];
    if (advertised_uuid == &uuid_bilateral_service) {
        // Read battery level (mutex-protected)
        uint8_t battery_pct = 0;
        if (xSemaphoreTake(bilateral_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) == pdTRUE) {
            battery_pct = bilateral_data.battery_level;
            xSemaphoreGive(bilateral_data_mutex);
        }

        battery_svc_data[0] = 0x0F;  // Battery Service UUID LSB (0x180F)
        battery_svc_data[1] = 0x18;  // Battery Service UUID MSB
        battery_svc_data[2] = battery_pct;  // Battery percentage 0-100

        rsp_fields.svc_data_uuid16 = battery_svc_data;
        rsp_fields.svc_data_uuid16_len = 3;

        ESP_LOGI(TAG, "Advertising battery level: %d%% (for role assignment)", battery_pct);
    }

    int rc = ble_gap_adv_rsp_set_fields(&rsp_fields);
    if (rc != 0) {
        ESP_LOGE(TAG, "Failed to update scan response UUID; rc=%d", rc);
    } else {
        ESP_LOGI(TAG, "Scan response UUID updated: %s",
                 (advertised_uuid == &uuid_bilateral_service) ? "Bilateral (peer discovery)" : "Config (app + bonded peer)");
    }
}

void ble_start_advertising(void) {
    ESP_LOGI(TAG, "ble_start_advertising() called (current state: advertising_active=%s, connected=%s)",
             adv_state.advertising_active ? "YES" : "NO",
             adv_state.client_connected ? "YES" : "NO");

    if (!adv_state.advertising_active) {
        // Update scan response with current UUID before starting advertising
        ble_update_scan_response();

        ESP_LOGI(TAG, "Starting BLE advertising via ble_gap_adv_start()...");
        int rc = ble_gap_adv_start(BLE_OWN_ADDR_PUBLIC, NULL, BLE_HS_FOREVER,
                                    &adv_params, ble_gap_event, NULL);
        if (rc == 0) {
            adv_state.advertising_active = true;
            adv_state.advertising_start_ms = (uint32_t)(esp_timer_get_time() / 1000);
            ESP_LOGI(TAG, "✓ BLE advertising started successfully");
        } else {
            ESP_LOGE(TAG, "✗ Failed to start advertising: NimBLE rc=%d (0x%x)", rc, rc);
            ESP_LOGE(TAG, "  Common causes: BLE stack not ready, already advertising, or GAP error");
        }
    } else {
        ESP_LOGW(TAG, "Advertising already active, skipping ble_gap_adv_start()");
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

// ============================================================================
// Peer Discovery & Scanning (Phase 1a)
// ============================================================================

/**
 * @brief BLE GAP scan event callback
 *
 * Detects peer devices advertising Bilateral Control Service (6E400001-...).
 * Devices advertising this service are potential peers for dual-device operation.
 *
 * @param event GAP event data
 * @param arg User argument (unused)
 * @return 0 on success
 */
static int ble_gap_scan_event(struct ble_gap_event *event, void *arg) {
    switch (event->type) {
        case BLE_GAP_EVENT_DISC: {
            // Device discovered - check if it advertises Bilateral Control Service
            struct ble_hs_adv_fields fields;
            int rc = ble_hs_adv_parse_fields(&fields, event->disc.data, event->disc.length_data);

            if (rc != 0) {
                ESP_LOGI(TAG, "Scan: malformed adv data (rc=%d)", rc);
                return 0;  // Skip malformed advertisements
            }

            // Log device name for debugging (temporary - can remove once working)
            if (fields.name != NULL) {
                ESP_LOGI(TAG, "Scan: Device '%.*s' (%d UUIDs)",
                         fields.name_len, fields.name, fields.num_uuids128);
            }

            // Check for Bilateral Control Service in scan response
            // UUID: 4BCAE9BE-9829-4F0A-9E88-267DE5E70100
            if (fields.uuids128 != NULL && fields.num_uuids128 > 0) {
                for (int i = 0; i < fields.num_uuids128; i++) {
                    // Compare against Bilateral Service UUID (Phase 1b.3: UUID-switching)
                    // Peer devices advertise this UUID during pairing window (0-30s)
                    // After pairing, bonded peers reconnect by address (no scanning needed)
                    if (ble_uuid_cmp(&fields.uuids128[i].u, &uuid_bilateral_service.u) == 0) {
                        // Check if already connected to a peer (prevent multiple peer connections)
                        if (peer_state.peer_connected || peer_state.peer_discovered) {
                            // Already connected or connecting to a peer, ignore this one
                            ESP_LOGD(TAG, "Already have peer connection, ignoring additional peer");
                            break;
                        }

                        // NOTE: Pairing window enforcement handled by UUID-switching
                        // Peers only advertise Bilateral UUID for first 30s, then switch to Config UUID
                        // This scan match automatically guarantees we're within the pairing window

                        // Found peer device! Log discovery
                        char addr_str[18];
                        snprintf(addr_str, sizeof(addr_str), "%02x:%02x:%02x:%02x:%02x:%02x",
                                event->disc.addr.val[5], event->disc.addr.val[4],
                                event->disc.addr.val[3], event->disc.addr.val[2],
                                event->disc.addr.val[1], event->disc.addr.val[0]);

                        ESP_LOGI(TAG, "Peer discovered: %s (RSSI: %d)", addr_str, event->disc.rssi);

                        // Save peer address
                        memcpy(&peer_state.peer_addr, &event->disc.addr, sizeof(ble_addr_t));
                        peer_state.peer_discovered = true;

                        // AD035: Extract peer battery level from Service Data for role assignment
                        // Battery Service UUID (0x180F) + battery percentage (0-100)
                        if (fields.svc_data_uuid16 != NULL && fields.svc_data_uuid16_len >= 3) {
                            uint16_t svc_uuid = (fields.svc_data_uuid16[1] << 8) | fields.svc_data_uuid16[0];
                            if (svc_uuid == 0x180F) {  // Battery Service UUID
                                peer_state.peer_battery_level = fields.svc_data_uuid16[2];
                                peer_state.peer_battery_known = true;
                                ESP_LOGI(TAG, "Peer battery: %d%% (for role assignment)",
                                         peer_state.peer_battery_level);
                            }
                        }

                        // Stop scanning (peer discovered)
                        ble_gap_disc_cancel();

                        // AD035: Battery-based role assignment
                        // Higher battery device initiates connection (becomes SERVER/MASTER)
                        // Lower battery device waits (becomes CLIENT/SLAVE)
                        if (peer_state.peer_battery_known) {
                            // Read local battery level (mutex-protected)
                            uint8_t local_battery = 0;
                            if (xSemaphoreTake(bilateral_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) == pdTRUE) {
                                local_battery = bilateral_data.battery_level;
                                xSemaphoreGive(bilateral_data_mutex);
                            }

                            if (local_battery > peer_state.peer_battery_level) {
                                // We have higher battery - initiate connection (SERVER/MASTER)
                                ESP_LOGI(TAG, "Higher battery (%d%% > %d%%) - initiating as SERVER",
                                         local_battery, peer_state.peer_battery_level);
                                ble_connect_to_peer();
                            } else if (local_battery < peer_state.peer_battery_level) {
                                // Peer has higher battery - wait for peer to connect (CLIENT/SLAVE)
                                ESP_LOGI(TAG, "Lower battery (%d%% < %d%%) - waiting as CLIENT",
                                         local_battery, peer_state.peer_battery_level);
                                // Don't call ble_connect_to_peer() - peer will connect to us
                            } else {
                                // Batteries equal - use MAC address tie-breaker
                                // Lower MAC address initiates connection
                                bool we_are_lower = false;
                                for (int j = 0; j < 6; j++) {
                                    if (event->disc.addr.val[j] < peer_state.peer_addr.val[j]) {
                                        we_are_lower = false;  // Peer is lower, they initiate
                                        break;
                                    } else if (event->disc.addr.val[j] > peer_state.peer_addr.val[j]) {
                                        we_are_lower = true;  // We are lower, we initiate
                                        break;
                                    }
                                }

                                if (we_are_lower) {
                                    ESP_LOGI(TAG, "Equal battery (%d%%), lower MAC - initiating as SERVER",
                                             local_battery);
                                    ble_connect_to_peer();
                                } else {
                                    ESP_LOGI(TAG, "Equal battery (%d%%), higher MAC - waiting as CLIENT",
                                             local_battery);
                                }
                            }
                        } else {
                            // No battery data - fall back to connection-initiator logic (AD010)
                            ESP_LOGW(TAG, "No peer battery data - falling back to discovery-based role");
                            ble_connect_to_peer();
                        }

                        return 0;
                    }
                }
            }
            break;
        }

        case BLE_GAP_EVENT_DISC_COMPLETE:
            ESP_LOGI(TAG, "BLE scan complete");
            scanning_active = false;

            // If no peer found, restart scanning (continuous discovery)
            if (!peer_state.peer_discovered && !peer_state.peer_connected) {
                ESP_LOGI(TAG, "No peer found, restarting scan...");
                vTaskDelay(pdMS_TO_TICKS(1000));  // Brief delay before retry
                ble_start_scanning();
            }
            break;

        default:
            break;
    }

    return 0;
}

/**
 * @brief Start BLE scanning for peer devices
 *
 * Initiates BLE scanning while maintaining advertising (simultaneous mode).
 * Scans for devices advertising Bilateral Control Service.
 *
 * RACE CONDITION FIX: Adds random delay to break symmetry when both devices
 * power on simultaneously. Uses MAC address as seed for deterministic randomness.
 */
void ble_start_scanning(void) {
    if (scanning_active) {
        ESP_LOGW(TAG, "BLE scanning already active");
        return;
    }

    if (peer_state.peer_connected) {
        ESP_LOGW(TAG, "Already connected to peer, skipping scan");
        return;
    }

    // RACE CONDITION FIX: Add randomized delay (0-500ms) before scanning
    // This breaks symmetry when both devices power on simultaneously
    // Use last 3 bytes of MAC as seed for unique but deterministic delay per device
    uint8_t addr_val[6];
    int is_nrpa;
    int rc_addr = ble_hs_id_copy_addr(BLE_ADDR_PUBLIC, addr_val, &is_nrpa);

    if (rc_addr == 0) {
        // Use last 3 bytes of MAC to generate delay (0-500ms)
        uint32_t seed = (addr_val[0] << 16) | (addr_val[1] << 8) | addr_val[2];
        uint32_t delay_ms = seed % 500;  // 0-499ms delay

        ESP_LOGI(TAG, "Scan startup delay: %lums (MAC-based)", delay_ms);
        vTaskDelay(pdMS_TO_TICKS(delay_ms));
    } else {
        ESP_LOGW(TAG, "Failed to get MAC for scan delay, using default 100ms");
        vTaskDelay(pdMS_TO_TICKS(100));
    }

    // Configure scan parameters
    struct ble_gap_disc_params disc_params = {
        .itvl = 0x10,           // Scan interval: 10ms (units of 0.625ms)
        .window = 0x10,         // Scan window: 10ms
        .filter_policy = BLE_HCI_SCAN_FILT_NO_WL,  // No whitelist filtering
        .limited = 0,           // General discovery (not limited)
        .passive = 0,           // Active scanning (request scan responses)
        .filter_duplicates = 1  // Filter duplicate advertisements
    };

    int rc = ble_gap_disc(BLE_OWN_ADDR_PUBLIC, BLE_HS_FOREVER, &disc_params,
                          ble_gap_scan_event, NULL);

    if (rc == 0) {
        scanning_active = true;
        ESP_LOGI(TAG, "BLE scanning started (searching for peer devices)");
    } else {
        ESP_LOGE(TAG, "Failed to start BLE scanning; rc=%d", rc);
    }
}

/**
 * @brief Stop BLE scanning
 */
void ble_stop_scanning(void) {
    if (scanning_active) {
        int rc = ble_gap_disc_cancel();
        if (rc == 0) {
            scanning_active = false;
            ESP_LOGI(TAG, "BLE scanning stopped");
        } else {
            ESP_LOGE(TAG, "Failed to stop scanning; rc=%d", rc);
        }
    }
}

/**
 * @brief Connect to discovered peer device
 *
 * Initiates BLE connection to peer advertising Bilateral Control Service.
 * Uses existing ble_gap_event() callback for connection events.
 */
void ble_connect_to_peer(void) {
    if (!peer_state.peer_discovered) {
        ESP_LOGW(TAG, "Cannot connect: no peer discovered");
        return;
    }

    if (peer_state.peer_connected) {
        ESP_LOGW(TAG, "Already connected to peer");
        return;
    }

    ESP_LOGI(TAG, "Connecting to peer device...");

    // Initiate connection (uses default connection parameters)
    int rc = ble_gap_connect(BLE_OWN_ADDR_PUBLIC, &peer_state.peer_addr,
                             30000,  // 30 second timeout
                             NULL,   // Default connection parameters
                             ble_gap_event, NULL);

    if (rc != 0) {
        ESP_LOGE(TAG, "Failed to connect to peer; rc=%d", rc);

        // BLE_ERR_ACL_CONN_EXISTS (523) means the peer successfully initiated connection to us
        // This is normal during simultaneous discovery - connection event will fire on both sides
        if (rc == 523) {  // 523 = BLE_ERR_ACL_CONN_EXISTS
            ESP_LOGI(TAG, "Peer is connecting to us (ACL already exists) - connection event will determine role");
        }

        // Reset discovery flag for retry
        peer_state.peer_discovered = false;
    }
}

// ============================================================================
// Status Query Functions
// ============================================================================

bool ble_is_connected(void) {
    return adv_state.client_connected;
}

bool ble_is_advertising(void) {
    // Return our internal flag (set by start/stop functions)
    // Note: NimBLE's ble_gap_adv_active() can return false transiently during state transitions
    // or when scanning is active (CONFIG_BT_NIMBLE_HOST_ALLOW_CONNECT_WITH_SCAN=n)
    // Trust our flag which tracks explicit start/stop calls
    return adv_state.advertising_active;
}

uint32_t ble_get_advertising_elapsed_ms(void) {
    if (!adv_state.advertising_active) {
        return 0;
    }
    uint32_t now = (uint32_t)(esp_timer_get_time() / 1000);
    return now - adv_state.advertising_start_ms;
}

bool ble_is_peer_connected(void) {
    return peer_state.peer_connected;
}

const char* ble_get_connection_type_str(void) {
    if (peer_state.peer_connected) {
        // Show role (Phase 1c Step 5: Log assigned role)
        if (peer_state.role == PEER_ROLE_CLIENT) {
            return "Peer (CLIENT)";
        } else if (peer_state.role == PEER_ROLE_SERVER) {
            return "Peer (SERVER)";
        } else {
            return "Peer";  // Role not yet assigned
        }
    } else if (adv_state.client_connected) {
        return "App";
    } else {
        return "Disconnected";
    }
}

bool ble_is_pairing(void) {
    return pairing_in_progress;
}

uint16_t ble_get_pairing_conn_handle(void) {
    return pairing_conn_handle;
}

uint16_t ble_get_peer_conn_handle(void) {
    return peer_state.peer_conn_handle;
}

uint16_t ble_get_app_conn_handle(void) {
    return adv_state.conn_handle;
}

void ble_update_battery_level(uint8_t percentage) {
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in ble_update_battery_level - possible deadlock");
        return;  // Early return on timeout
    }
    char_data.battery_level = percentage;
    xSemaphoreGive(char_data_mutex);

    // Send notification if client subscribed
    if (adv_state.client_connected && adv_state.notify_battery_subscribed) {
        uint16_t val_handle;
        if (ble_gatts_find_chr(&uuid_config_service.u, &uuid_char_battery.u, NULL, &val_handle) == 0) {
            struct os_mbuf *om = ble_hs_mbuf_from_flat(&percentage, sizeof(percentage));
            if (om != NULL) {
                int rc = ble_gatts_notify_custom(adv_state.conn_handle, val_handle, om);
                if (rc != 0) {
                    ESP_LOGD(TAG, "Battery notify failed: rc=%d", rc);
                }
            }
        }
    }
}

peer_role_t ble_get_peer_role(void) {
    return peer_state.role;
}

bool ble_check_bonded_peer_exists(void) {
    // Check if any bonded peer exists in NVS storage
    // This is used to determine if we should skip pairing window on reconnection
    union ble_store_key key;
    union ble_store_value value;

    // Clear key to search for any bonded device
    memset(&key, 0, sizeof(key));
    key.sec.idx = 0;  // Start at first index

    // Try to read first bonded peer entry
    int rc = ble_store_read(BLE_STORE_OBJ_TYPE_OUR_SEC, &key, &value);

    if (rc == 0) {
        ESP_LOGI(TAG, "Found bonded peer in NVS: %02X:%02X:%02X:%02X:%02X:%02X",
                 value.sec.peer_addr.val[0], value.sec.peer_addr.val[1],
                 value.sec.peer_addr.val[2], value.sec.peer_addr.val[3],
                 value.sec.peer_addr.val[4], value.sec.peer_addr.val[5]);
        return true;
    }

    ESP_LOGD(TAG, "No bonded peers found in NVS (rc=%d)", rc);
    return false;
}

/**
 * @brief Get bonded peer address from NVS storage
 * @param addr_out Pointer to store bonded peer address
 * @return true if bonded peer found and address copied, false otherwise
 *
 * Used for EXCLUSIVE PAIRING enforcement - only the bonded peer can connect
 * until NVS is erased.
 */
static bool ble_get_bonded_peer_addr(ble_addr_t *addr_out) {
    union ble_store_key key;
    union ble_store_value value;

    // Clear key to search for first bonded device
    memset(&key, 0, sizeof(key));
    key.sec.idx = 0;  // First bonded peer index

    // Try to read first bonded peer entry
    int rc = ble_store_read(BLE_STORE_OBJ_TYPE_OUR_SEC, &key, &value);

    if (rc == 0) {
        // Copy bonded peer address to output
        memcpy(addr_out, &value.sec.peer_addr, sizeof(ble_addr_t));
        ESP_LOGD(TAG, "Bonded peer address: %02X:%02X:%02X:%02X:%02X:%02X (type=%d)",
                 addr_out->val[0], addr_out->val[1], addr_out->val[2],
                 addr_out->val[3], addr_out->val[4], addr_out->val[5],
                 addr_out->type);
        return true;
    }

    ESP_LOGD(TAG, "No bonded peer address found (rc=%d)", rc);
    return false;
}

void ble_update_bilateral_battery_level(uint8_t percentage) {
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(bilateral_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in ble_update_bilateral_battery_level - possible deadlock");
        return;  // Early return on timeout
    }

    uint8_t old_level = bilateral_data.battery_level;
    bilateral_data.battery_level = percentage;
    xSemaphoreGive(bilateral_data_mutex);

    ESP_LOGD(TAG, "Bilateral battery level updated: %u%%", percentage);

    // AD035: Restart advertising if battery changed and we're in peer discovery window
    // This updates the Service Data in scan response for role assignment
    if (old_level != percentage && adv_state.advertising_active) {
        const ble_uuid128_t *current_uuid = ble_get_advertised_uuid();
        if (current_uuid == &uuid_bilateral_service) {
            ESP_LOGI(TAG, "Battery changed %d%% → %d%%, updating advertising (peer discovery)",
                     old_level, percentage);
            ble_stop_advertising();
            vTaskDelay(pdMS_TO_TICKS(50));  // Brief delay for cleanup
            ble_start_advertising();
        }
    }
}

void ble_update_session_time(uint32_t seconds) {
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in ble_update_session_time - possible deadlock");
        return;  // Early return on timeout
    }
    char_data.session_time_sec = seconds;
    xSemaphoreGive(char_data_mutex);

    // Send notification if client subscribed
    // NOTE: Motor task should call this every 30-60 seconds, not every second
    // Mobile app is responsible for counting seconds in UI between notifications
    if (adv_state.client_connected && adv_state.notify_session_time_subscribed) {
        uint16_t val_handle;
        if (ble_gatts_find_chr(&uuid_config_service.u, &uuid_char_session_time.u, NULL, &val_handle) == 0) {
            struct os_mbuf *om = ble_hs_mbuf_from_flat(&seconds, sizeof(seconds));
            if (om != NULL) {
                int rc = ble_gatts_notify_custom(adv_state.conn_handle, val_handle, om);
                if (rc != 0) {
                    ESP_LOGD(TAG, "Session time notify failed: rc=%d", rc);
                }
            }
        }
    }
}

void ble_update_mode(mode_t mode) {
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in ble_update_mode - possible deadlock");
        return;  // Early return on timeout
    }
    char_data.current_mode = mode;
    xSemaphoreGive(char_data_mutex);

    // Send notification if client subscribed
    // This notifies mobile app when mode is changed via button press
    if (adv_state.client_connected && adv_state.notify_mode_subscribed) {
        uint16_t val_handle;
        if (ble_gatts_find_chr(&uuid_config_service.u, &uuid_char_mode.u, NULL, &val_handle) == 0) {
            uint8_t mode_val = (uint8_t)mode;
            struct os_mbuf *om = ble_hs_mbuf_from_flat(&mode_val, sizeof(mode_val));
            if (om != NULL) {
                int rc = ble_gatts_notify_custom(adv_state.conn_handle, val_handle, om);
                if (rc != 0) {
                    ESP_LOGD(TAG, "Mode notify failed: rc=%d", rc);
                } else {
                    ESP_LOGI(TAG, "Mode notification sent: %d", mode_val);
                }
            }
        }
    }
}

mode_t ble_get_current_mode(void) {
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in ble_get_current_mode - possible deadlock");
        return MODE_05HZ_25;  // Return safe default
    }
    mode_t mode = char_data.current_mode;
    xSemaphoreGive(char_data_mutex);
    return mode;
}

uint16_t ble_get_custom_frequency_hz(void) {
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in ble_get_custom_frequency_hz - possible deadlock");
        return 100;  // Return safe default (1.0 Hz)
    }
    uint16_t freq = char_data.custom_frequency_hz;
    xSemaphoreGive(char_data_mutex);
    return freq;
}

uint8_t ble_get_custom_duty_percent(void) {
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in ble_get_custom_duty_percent - possible deadlock");
        return 50;  // Return safe default
    }
    uint8_t duty = char_data.custom_duty_percent;
    xSemaphoreGive(char_data_mutex);
    return duty;
}

uint8_t ble_get_pwm_intensity(void) {
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in ble_get_pwm_intensity - possible deadlock");
        return 50;  // Return safe default
    }
    uint8_t intensity = char_data.pwm_intensity;
    xSemaphoreGive(char_data_mutex);
    return intensity;
}

bool ble_get_led_enable(void) {
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in ble_get_led_enable - possible deadlock");
        return true;  // Return safe default
    }
    bool enabled = char_data.led_enable;
    xSemaphoreGive(char_data_mutex);
    return enabled;
}

uint8_t ble_get_led_color_mode(void) {
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in ble_get_led_color_mode - possible deadlock");
        return 0;  // Return safe default (palette mode)
    }
    uint8_t mode = char_data.led_color_mode;
    xSemaphoreGive(char_data_mutex);
    return mode;
}

uint8_t ble_get_led_palette_index(void) {
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in ble_get_led_palette_index - possible deadlock");
        return 0;  // Return safe default
    }
    uint8_t idx = char_data.led_palette_index;
    xSemaphoreGive(char_data_mutex);
    return idx;
}

void ble_get_led_custom_rgb(uint8_t *r, uint8_t *g, uint8_t *b) {
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in ble_get_led_custom_rgb - possible deadlock");
        *r = 0; *g = 0; *b = 255;  // Return safe default (blue)
        return;
    }
    *r = char_data.led_custom_r;
    *g = char_data.led_custom_g;
    *b = char_data.led_custom_b;
    xSemaphoreGive(char_data_mutex);
}

uint8_t ble_get_led_brightness(void) {
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in ble_get_led_brightness - possible deadlock");
        return 20;  // Return safe default
    }
    uint8_t brightness = char_data.led_brightness;
    xSemaphoreGive(char_data_mutex);
    return brightness;
}

uint32_t ble_get_session_duration_sec(void) {
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in ble_get_session_duration_sec - possible deadlock");
        return 1800;  // Return safe default (30 minutes)
    }
    uint32_t duration = char_data.session_duration_sec;
    xSemaphoreGive(char_data_mutex);
    return duration;
}

bool ble_settings_dirty(void) {
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in ble_settings_dirty - possible deadlock");
        return false;  // Return safe default
    }
    bool dirty = settings_dirty;
    xSemaphoreGive(char_data_mutex);
    return dirty;
}

void ble_settings_mark_clean(void) {
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in ble_settings_mark_clean - possible deadlock");
        return;  // Early return on timeout
    }
    settings_dirty = false;
    xSemaphoreGive(char_data_mutex);
}

esp_err_t ble_manager_deinit(void) {
    ESP_LOGI(TAG, "Deinitializing BLE manager...");
    ble_stop_advertising();
    ESP_LOGI(TAG, "BLE manager deinitialized");
    return ESP_OK;
}
