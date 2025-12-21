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
#include "time_sync.h"      // Phase 2: Time synchronization (AD039)
#include "time_sync_task.h" // Phase 2: Time sync task integration
#include "firmware_version.h" // AD040: Firmware version enforcement
#include "pattern_playback.h" // AD047: Pattern playback control for Mode 5
#include "espnow_transport.h" // AD048: ESP-NOW transport for low-latency time sync
#include "esp_chip_info.h"    // AD048: Silicon revision for hardware info characteristic
#include "esp_log.h"
#include "nvs_flash.h"
#include "nvs.h"
#include "esp_crc.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"
#include "esp_timer.h"
#include "esp_bt.h"  // For TX power control (esp_ble_tx_power_set_enhanced)

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

// Phase 2: Time synchronization (AD039)
static const ble_uuid128_t uuid_bilateral_time_sync = BLE_UUID128_INIT(
    0x04, 0x01, 0xe7, 0xe5, 0x7d, 0x26, 0x88, 0x9e,
    0x0a, 0x4f, 0x29, 0x98, 0xbe, 0xe9, 0xca, 0x4b);
// UUID: 4BCAE9BE-9829-4F0A-9E88-267DE5E70104

// Phase 3: Coordination messages (hybrid architecture)
static const ble_uuid128_t uuid_bilateral_coordination = BLE_UUID128_INIT(
    0x05, 0x01, 0xe7, 0xe5, 0x7d, 0x26, 0x88, 0x9e,
    0x0a, 0x4f, 0x29, 0x98, 0xbe, 0xe9, 0xca, 0x4b);
// UUID: 4BCAE9BE-9829-4F0A-9E88-267DE5E70105

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

static const ble_uuid128_t uuid_char_mode4_intensity = BLE_UUID128_INIT(
    0x04, 0x02, 0xe7, 0xe5, 0x7d, 0x26, 0x88, 0x9e,
    0x0a, 0x4f, 0x29, 0x98, 0xbe, 0xe9, 0xca, 0x4b);

static const ble_uuid128_t uuid_char_mode0_intensity = BLE_UUID128_INIT(
    0x0e, 0x02, 0xe7, 0xe5, 0x7d, 0x26, 0x88, 0x9e,
    0x0a, 0x4f, 0x29, 0x98, 0xbe, 0xe9, 0xca, 0x4b);

static const ble_uuid128_t uuid_char_mode1_intensity = BLE_UUID128_INIT(
    0x0f, 0x02, 0xe7, 0xe5, 0x7d, 0x26, 0x88, 0x9e,
    0x0a, 0x4f, 0x29, 0x98, 0xbe, 0xe9, 0xca, 0x4b);

static const ble_uuid128_t uuid_char_mode2_intensity = BLE_UUID128_INIT(
    0x10, 0x02, 0xe7, 0xe5, 0x7d, 0x26, 0x88, 0x9e,
    0x0a, 0x4f, 0x29, 0x98, 0xbe, 0xe9, 0xca, 0x4b);

static const ble_uuid128_t uuid_char_mode3_intensity = BLE_UUID128_INIT(
    0x11, 0x02, 0xe7, 0xe5, 0x7d, 0x26, 0x88, 0x9e,
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

static const ble_uuid128_t uuid_char_client_battery = BLE_UUID128_INIT(
    0x0d, 0x02, 0xe7, 0xe5, 0x7d, 0x26, 0x88, 0x9e,
    0x0a, 0x4f, 0x29, 0x98, 0xbe, 0xe9, 0xca, 0x4b);

// Firmware Version Group (AD032: bytes 13-14 = 0x02 0x12/0x13)
static const ble_uuid128_t uuid_char_local_firmware = BLE_UUID128_INIT(
    0x12, 0x02, 0xe7, 0xe5, 0x7d, 0x26, 0x88, 0x9e,
    0x0a, 0x4f, 0x29, 0x98, 0xbe, 0xe9, 0xca, 0x4b);

static const ble_uuid128_t uuid_char_peer_firmware = BLE_UUID128_INIT(
    0x13, 0x02, 0xe7, 0xe5, 0x7d, 0x26, 0x88, 0x9e,
    0x0a, 0x4f, 0x29, 0x98, 0xbe, 0xe9, 0xca, 0x4b);

// Hardware Info Group (AD048: bytes 13-14 = 0x02 0x15/0x16)
// Exposes silicon revision for 802.11mc FTM capability discovery
static const ble_uuid128_t uuid_char_local_hardware = BLE_UUID128_INIT(
    0x15, 0x02, 0xe7, 0xe5, 0x7d, 0x26, 0x88, 0x9e,
    0x0a, 0x4f, 0x29, 0x98, 0xbe, 0xe9, 0xca, 0x4b);

static const ble_uuid128_t uuid_char_peer_hardware = BLE_UUID128_INIT(
    0x16, 0x02, 0xe7, 0xe5, 0x7d, 0x26, 0x88, 0x9e,
    0x0a, 0x4f, 0x29, 0x98, 0xbe, 0xe9, 0xca, 0x4b);

// Time Beacon Group (AD047/UTLP: bytes 13-14 = 0x02 0x14)
// UTLP semantics: devices passively listen for time beacons from any source
static const ble_uuid128_t uuid_char_time_beacon = BLE_UUID128_INIT(
    0x14, 0x02, 0xe7, 0xe5, 0x7d, 0x26, 0x88, 0x9e,
    0x0a, 0x4f, 0x29, 0x98, 0xbe, 0xe9, 0xca, 0x4b);

// Pattern Control Group (AD047: bytes 13-14 = 0x02 0x17/0x18/0x19)
// Mode 5 pattern playback control for lightbar/bilateral patterns
static const ble_uuid128_t uuid_char_pattern_control = BLE_UUID128_INIT(
    0x17, 0x02, 0xe7, 0xe5, 0x7d, 0x26, 0x88, 0x9e,
    0x0a, 0x4f, 0x29, 0x98, 0xbe, 0xe9, 0xca, 0x4b);

static const ble_uuid128_t uuid_char_pattern_data = BLE_UUID128_INIT(
    0x18, 0x02, 0xe7, 0xe5, 0x7d, 0x26, 0x88, 0x9e,
    0x0a, 0x4f, 0x29, 0x98, 0xbe, 0xe9, 0xca, 0x4b);

static const ble_uuid128_t uuid_char_pattern_status = BLE_UUID128_INIT(
    0x19, 0x02, 0xe7, 0xe5, 0x7d, 0x26, 0x88, 0x9e,
    0x0a, 0x4f, 0x29, 0x98, 0xbe, 0xe9, 0xca, 0x4b);

static const ble_uuid128_t uuid_char_pattern_list = BLE_UUID128_INIT(
    0x1a, 0x02, 0xe7, 0xe5, 0x7d, 0x26, 0x88, 0x9e,
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
static esp_err_t sync_settings_to_peer(void);

// Forward declaration for GATT discovery callback (Bug #31 fix)
static int gattc_on_chr_disc(uint16_t conn_handle,
                              const struct ble_gatt_error *error,
                              const struct ble_gatt_chr *chr,
                              void *arg);

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
    .mode0_intensity = 65,  // Mode 0 (0.5Hz): 50-80% range, default 65%
    .mode1_intensity = 65,  // Mode 1 (1.0Hz): 50-80% range, default 65%
    .mode2_intensity = 80,  // Mode 2 (1.5Hz): 70-90% range, default 80%
    .mode3_intensity = 80,  // Mode 3 (2.0Hz): 70-90% range, default 80%
    .mode4_intensity = MOTOR_PWM_DEFAULT,  // Mode 4 (Custom): 30-80% range, default from motor_control.h
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

// Bug #48 Fix: Pre-initialized battery level (read before BLE init in main.c)
// This ensures battery is available when ble_on_sync() callback fires
static uint8_t g_initial_battery_pct = 0;

// Advertising state
typedef struct {
    bool advertising_active;
    bool client_connected;
    uint32_t advertising_start_ms;
    uint16_t conn_handle;              /**< Connection handle for notifications */
    bool notify_mode_subscribed;        /**< Client subscribed to Mode notifications */
    bool notify_session_time_subscribed; /**< Client subscribed to Session Time notifications */
    bool notify_battery_subscribed;     /**< Client subscribed to Battery notifications */
    bool notify_client_battery_subscribed; /**< Client subscribed to Client Battery notifications */
} ble_advertising_state_t;

static ble_advertising_state_t adv_state = {
    .advertising_active = false,
    .client_connected = false,
    .advertising_start_ms = 0,
    .conn_handle = BLE_HS_CONN_HANDLE_NONE,
    .notify_mode_subscribed = false,
    .notify_session_time_subscribed = false,
    .notify_battery_subscribed = false,
    .notify_client_battery_subscribed = false
};

// Settings dirty flag (thread-safe via char_data_mutex)
static bool settings_dirty = false;

// Bug #95: Debounced frequency change for Mode 4 (AD047 Phase 1 stepping stone)
// When frequency changes via BLE slider, we debounce before triggering coordinated sync
// This prevents rapid mode changes during slider drag while ensuring eventual sync
#define FREQ_CHANGE_DEBOUNCE_MS 300  // Wait 300ms after last change before sync
static bool freq_change_pending = false;
static uint32_t freq_change_timestamp_ms = 0;

// AD032/AD040: Firmware version strings
static char local_firmware_version_str[32] = "";   // Initialized in ble_manager_init()
static char peer_firmware_version_str[32] = "";    // Set by ble_set_peer_firmware_version()
static bool firmware_versions_match_flag = true;   // AD040: Assume match until proven otherwise
static bool firmware_version_exchanged = false;    // AD040: Set true when SYNC_MSG_FIRMWARE_VERSION processed

// AD048: Hardware info strings (silicon revision, 802.11mc FTM capability)
// Format: "ESP32-C6 v0.2 (FTM:full)" or "ESP32-C6 v0.1 (FTM:resp-only)"
static char local_hardware_info_str[48] = "";      // Initialized in ble_manager_init()
static char peer_hardware_info_str[48] = "";       // Set by ble_set_peer_hardware_info()

// AD047: Pattern status for Mode 5 pattern playback
// 0=stopped, 1=playing, 2=error
static uint8_t pattern_status = 0;

// ============================================================================
// BLE CONNECTION PARAMETERS (Phase 6p - Long Session Support)
// ============================================================================

/**
 * Custom connection parameters for therapeutic sessions
 *
 * - Connection interval: 50ms (40 units × 1.25ms) - balances power and responsiveness
 * - Slave latency: 0 - no latency for precise bilateral stimulation timing
 * - Supervision timeout: 32 seconds (3200 units × 10ms) - BLE specification maximum
 *
 * Default NimBLE parameters use ~2-6 second timeout, causing disconnects during normal use.
 * Phase 6p increases timeout to 32 seconds (BLE spec maximum) to prevent connection loss during therapeutic sessions.
 */
static const struct ble_gap_conn_params therapeutic_conn_params = {
    .scan_itvl = 0x0010,           // Scan interval (not used for connection, only for scanning)
    .scan_window = 0x0010,         // Scan window (not used for connection, only for scanning)
    .itvl_min = 40,                // Min connection interval: 40 × 1.25ms = 50ms
    .itvl_max = 40,                // Max connection interval: 40 × 1.25ms = 50ms
    .latency = 0,                  // Slave latency: 0 events (no latency)
    .supervision_timeout = 3200,   // Supervision timeout: 3200 × 10ms = 32 seconds (BLE spec maximum)
    .min_ce_len = 0,               // Min connection event length (0 = no preference)
    .max_ce_len = 0                // Max connection event length (0 = no preference)
};

/**
 * Connection parameter update structure for ble_gap_update_params()
 * Same values as therapeutic_conn_params but in update format
 */
static const struct ble_gap_upd_params therapeutic_upd_params = {
    .itvl_min = 40,                // Min connection interval: 40 × 1.25ms = 50ms
    .itvl_max = 40,                // Max connection interval: 40 × 1.25ms = 50ms
    .latency = 0,                  // Slave latency: 0 events (no latency)
    .supervision_timeout = 3200,   // Supervision timeout: 3200 × 10ms = 32 seconds (BLE spec maximum)
    .min_ce_len = 0,               // Min connection event length (0 = no preference)
    .max_ce_len = 0                // Max connection event length (0 = no preference)
};

// ============================================================================
// TIME SYNC BEACON STORAGE (Phase 2 - AD039)
// ============================================================================

// Phase 2: Time sync beacon (16 bytes, statically allocated per JPL Rule 1)
static time_sync_beacon_t g_time_sync_beacon = {0};
static SemaphoreHandle_t time_sync_beacon_mutex = NULL;

// Cache attribute handle for time sync characteristic
// - SERVER (BLE_GAP_ROLE_SLAVE): Set during GATT registration (gatt_svr_register_cb)
// - CLIENT (BLE_GAP_ROLE_MASTER): Set during GATT discovery (gattc_on_chr_disc)
static uint16_t g_time_sync_char_handle = 0;

// ============================================================================
// COORDINATION STATE (Phase 3 - Hybrid Architecture)
// ============================================================================

// Current coordination mode (thread-safe via char_data_mutex)
static coordination_mode_t g_coordination_mode = COORD_MODE_STANDALONE;

// Cache attribute handle for coordination characteristic
// - SERVER: Set during GATT registration (gatt_svr_register_cb)
// - CLIENT: Set during GATT discovery (gattc_on_chr_disc)
static uint16_t g_coordination_char_handle = 0;

// CLIENT-specific: Handle for peer's coordination characteristic
static uint16_t g_peer_coordination_char_handle = 0;

// CLIENT-specific: Discovery state tracking
static bool g_bilateral_discovery_complete = false;
static bool g_config_service_found = false;
static uint16_t g_config_service_start_handle = 0;
static uint16_t g_config_service_end_handle = 0;
static uint16_t g_discovery_conn_handle = BLE_HS_CONN_HANDLE_NONE;

// CLIENT-specific: Deferred discovery timer (Bug #31 fix)
// Avoids BLE_HS_EBUSY by deferring Config Service discovery until Bilateral discovery callback completes
static esp_timer_handle_t g_deferred_discovery_timer = NULL;

// Phase 3a: Characteristic value handles for notification-based sync
// These handles are set during GATT registration and used to send notifications
static uint16_t g_freq_val_handle = 0;
static uint16_t g_duty_val_handle = 0;
static uint16_t g_mode0_val_handle = 0;
static uint16_t g_mode1_val_handle = 0;
static uint16_t g_mode2_val_handle = 0;
static uint16_t g_mode3_val_handle = 0;
static uint16_t g_mode4_val_handle = 0;
static uint16_t g_led_enable_val_handle = 0;
static uint16_t g_led_color_mode_val_handle = 0;
static uint16_t g_led_palette_val_handle = 0;
static uint16_t g_led_custom_rgb_val_handle = 0;
static uint16_t g_led_brightness_val_handle = 0;

// Phase 3a: Peer characteristic handles for subscription
// CLIENT subscribes to SERVER's characteristics to receive notifications
static uint16_t g_peer_freq_val_handle = 0;
static uint16_t g_peer_duty_val_handle = 0;
static uint16_t g_peer_mode0_val_handle = 0;
static uint16_t g_peer_mode1_val_handle = 0;
static uint16_t g_peer_mode2_val_handle = 0;
static uint16_t g_peer_mode3_val_handle = 0;
static uint16_t g_peer_mode4_val_handle = 0;
static uint16_t g_peer_led_enable_val_handle = 0;
static uint16_t g_peer_led_color_mode_val_handle = 0;
static uint16_t g_peer_led_palette_val_handle = 0;
static uint16_t g_peer_led_custom_rgb_val_handle = 0;
static uint16_t g_peer_led_brightness_val_handle = 0;

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
 * - Conditional NVS writes based on CONFIG_BT_NIMBLE_NVS_PERSIST flag
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

// Bug #61: Battery cache for role assignment
// BLE sends advertising data and scan response in SEPARATE events:
// - Advertising packet: Contains battery Service Data (but no UUID)
// - Scan response: Contains UUID (but no battery Service Data)
// We must cache battery from advertising event and use it when scan response arrives
typedef struct {
    ble_addr_t addr;          /**< Device address */
    uint8_t battery_level;    /**< Cached battery percentage */
    bool valid;               /**< Cache entry is valid */
    uint32_t timestamp_ms;    /**< When entry was cached (for expiry) */
} battery_cache_entry_t;

#define BATTERY_CACHE_SIZE    4       // Small cache for nearby devices
#define BATTERY_CACHE_TTL_MS  5000    // Cache entry expires after 5 seconds

static battery_cache_entry_t battery_cache[BATTERY_CACHE_SIZE] = {0};

// Bug #45: Peer pairing window state flag
// Tracks whether pairing window is closed (peer paired OR 30s timeout)
// Once closed, all new connections are treated as mobile apps
static bool peer_pairing_window_closed = false;

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
#define NVS_KEY_MODE0_INTENSITY  "m0_int"
#define NVS_KEY_MODE1_INTENSITY  "m1_int"
#define NVS_KEY_MODE2_INTENSITY  "m2_int"
#define NVS_KEY_MODE3_INTENSITY  "m3_int"
#define NVS_KEY_MODE4_INTENSITY  "m4_int"
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
// FORWARD DECLARATIONS (for helper functions used before definition)
// ============================================================================

static bool ble_is_app_connected(void);

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

// ============================================================================
// PWA SETTINGS SYNCHRONIZATION (Phase 3a - Notification-Based)
// ============================================================================

// NOTE: Settings sync now uses BLE GATT notifications instead of coordination messages
// When SERVER writes a config value, ble_gatts_chr_updated() sends notification to CLIENT
// CLIENT receives notification via BLE_GAP_EVENT_NOTIFY_RX and updates char_data
// See notification handlers in ble_gap_event() around line 2377+

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

    // Phase 3: Sync mode change to peer device (PWA-triggered mode changes)
    if (ble_is_peer_connected()) {
        coordination_message_t coord_msg = {
            .type = SYNC_MSG_MODE_CHANGE,
            .timestamp_ms = (uint32_t)(esp_timer_get_time() / 1000ULL),
            .payload = {.mode = (mode_t)mode_val}
        };
        esp_err_t err = ble_send_coordination_message(&coord_msg);
        if (err == ESP_OK) {
            ESP_LOGI(TAG, "Mode change synced to peer: MODE_%u", mode_val);
        } else {
            ESP_LOGW(TAG, "Failed to sync mode change to peer: %s", esp_err_to_name(err));
        }
    }

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

    // Phase 3a: Sync ALL settings to peer device (coordination message)
    // This syncs the VALUE immediately so both devices have same frequency
    sync_settings_to_peer();

    // Bug #95: Set pending flag for debounced coordinated mode change
    // When user drags slider, we get many rapid changes. We debounce to avoid
    // triggering mode change protocol for each slider position.
    // time_sync_task checks this flag and triggers mode change after 300ms idle.
    // Only applies when we're in Mode 4 (Custom) AND peer is connected.
    if (ble_get_current_mode() == MODE_CUSTOM && ble_is_peer_connected()) {
        freq_change_pending = true;
        freq_change_timestamp_ms = (uint32_t)(esp_timer_get_time() / 1000);
        ESP_LOGI(TAG, "Frequency change pending (debounce started)");
    }

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

    // Phase 3a: Sync ALL settings to peer device (coordination message)
    sync_settings_to_peer();

    return 0;
}

// Mode 0 (0.5Hz) Intensity - Read
static int gatt_char_mode0_intensity_read(uint16_t conn_handle, uint16_t attr_handle,
                                          struct ble_gatt_access_ctxt *ctxt, void *arg) {
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in gatt_char_mode0_intensity_read");
        return BLE_ATT_ERR_UNLIKELY;
    }
    uint8_t intensity = char_data.mode0_intensity;
    xSemaphoreGive(char_data_mutex);

    ESP_LOGD(TAG, "GATT Read: Mode 0 Intensity = %u%%", intensity);
    int rc = os_mbuf_append(ctxt->om, &intensity, sizeof(intensity));
    return (rc == 0) ? 0 : BLE_ATT_ERR_INSUFFICIENT_RES;
}

// Mode 0 (0.5Hz) Intensity - Write
static int gatt_char_mode0_intensity_write(uint16_t conn_handle, uint16_t attr_handle,
                                           struct ble_gatt_access_ctxt *ctxt, void *arg) {
    uint8_t value;
    int rc = ble_hs_mbuf_to_flat(ctxt->om, &value, sizeof(value), NULL);
    if (rc != 0) {
        ESP_LOGE(TAG, "GATT Write: Mode 0 Intensity read failed");
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    // Mode 0 (0.5Hz): Range 50-80%
    if (value < 50 || value > 80) {
        ESP_LOGE(TAG, "GATT Write: Invalid Mode 0 Intensity %u%% (range 50-80)", value);
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    ESP_LOGD(TAG, "GATT Write: Mode 0 Intensity = %u%%", value);

    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in gatt_char_mode0_intensity_write");
        return BLE_ATT_ERR_UNLIKELY;
    }
    char_data.mode0_intensity = value;
    settings_dirty = true;
    xSemaphoreGive(char_data_mutex);

    ble_callback_params_updated();
    sync_settings_to_peer();
    return 0;
}

// Mode 1 (1.0Hz) Intensity - Read
static int gatt_char_mode1_intensity_read(uint16_t conn_handle, uint16_t attr_handle,
                                          struct ble_gatt_access_ctxt *ctxt, void *arg) {
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in gatt_char_mode1_intensity_read");
        return BLE_ATT_ERR_UNLIKELY;
    }
    uint8_t intensity = char_data.mode1_intensity;
    xSemaphoreGive(char_data_mutex);

    ESP_LOGD(TAG, "GATT Read: Mode 1 Intensity = %u%%", intensity);
    int rc = os_mbuf_append(ctxt->om, &intensity, sizeof(intensity));
    return (rc == 0) ? 0 : BLE_ATT_ERR_INSUFFICIENT_RES;
}

// Mode 1 (1.0Hz) Intensity - Write
static int gatt_char_mode1_intensity_write(uint16_t conn_handle, uint16_t attr_handle,
                                           struct ble_gatt_access_ctxt *ctxt, void *arg) {
    uint8_t value;
    int rc = ble_hs_mbuf_to_flat(ctxt->om, &value, sizeof(value), NULL);
    if (rc != 0) {
        ESP_LOGE(TAG, "GATT Write: Mode 1 Intensity read failed");
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    // Mode 1 (1.0Hz): Range 50-80%
    if (value < 50 || value > 80) {
        ESP_LOGE(TAG, "GATT Write: Invalid Mode 1 Intensity %u%% (range 50-80)", value);
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    ESP_LOGD(TAG, "GATT Write: Mode 1 Intensity = %u%%", value);

    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in gatt_char_mode1_intensity_write");
        return BLE_ATT_ERR_UNLIKELY;
    }
    char_data.mode1_intensity = value;
    settings_dirty = true;
    xSemaphoreGive(char_data_mutex);

    ble_callback_params_updated();
    sync_settings_to_peer();
    return 0;
}

// Mode 2 (1.5Hz) Intensity - Read
static int gatt_char_mode2_intensity_read(uint16_t conn_handle, uint16_t attr_handle,
                                          struct ble_gatt_access_ctxt *ctxt, void *arg) {
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in gatt_char_mode2_intensity_read");
        return BLE_ATT_ERR_UNLIKELY;
    }
    uint8_t intensity = char_data.mode2_intensity;
    xSemaphoreGive(char_data_mutex);

    ESP_LOGD(TAG, "GATT Read: Mode 2 Intensity = %u%%", intensity);
    int rc = os_mbuf_append(ctxt->om, &intensity, sizeof(intensity));
    return (rc == 0) ? 0 : BLE_ATT_ERR_INSUFFICIENT_RES;
}

// Mode 2 (1.5Hz) Intensity - Write
static int gatt_char_mode2_intensity_write(uint16_t conn_handle, uint16_t attr_handle,
                                           struct ble_gatt_access_ctxt *ctxt, void *arg) {
    uint8_t value;
    int rc = ble_hs_mbuf_to_flat(ctxt->om, &value, sizeof(value), NULL);
    if (rc != 0) {
        ESP_LOGE(TAG, "GATT Write: Mode 2 Intensity read failed");
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    // Mode 2 (1.5Hz): Range 70-90%
    if (value < 70 || value > 90) {
        ESP_LOGE(TAG, "GATT Write: Invalid Mode 2 Intensity %u%% (range 70-90)", value);
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    ESP_LOGD(TAG, "GATT Write: Mode 2 Intensity = %u%%", value);

    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in gatt_char_mode2_intensity_write");
        return BLE_ATT_ERR_UNLIKELY;
    }
    char_data.mode2_intensity = value;
    settings_dirty = true;
    xSemaphoreGive(char_data_mutex);

    ble_callback_params_updated();
    sync_settings_to_peer();
    return 0;
}

// Mode 3 (2.0Hz) Intensity - Read
static int gatt_char_mode3_intensity_read(uint16_t conn_handle, uint16_t attr_handle,
                                          struct ble_gatt_access_ctxt *ctxt, void *arg) {
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in gatt_char_mode3_intensity_read");
        return BLE_ATT_ERR_UNLIKELY;
    }
    uint8_t intensity = char_data.mode3_intensity;
    xSemaphoreGive(char_data_mutex);

    ESP_LOGD(TAG, "GATT Read: Mode 3 Intensity = %u%%", intensity);
    int rc = os_mbuf_append(ctxt->om, &intensity, sizeof(intensity));
    return (rc == 0) ? 0 : BLE_ATT_ERR_INSUFFICIENT_RES;
}

// Mode 3 (2.0Hz) Intensity - Write
static int gatt_char_mode3_intensity_write(uint16_t conn_handle, uint16_t attr_handle,
                                           struct ble_gatt_access_ctxt *ctxt, void *arg) {
    uint8_t value;
    int rc = ble_hs_mbuf_to_flat(ctxt->om, &value, sizeof(value), NULL);
    if (rc != 0) {
        ESP_LOGE(TAG, "GATT Write: Mode 3 Intensity read failed");
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    // Mode 3 (2.0Hz): Range 70-90%
    if (value < 70 || value > 90) {
        ESP_LOGE(TAG, "GATT Write: Invalid Mode 3 Intensity %u%% (range 70-90)", value);
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    ESP_LOGD(TAG, "GATT Write: Mode 3 Intensity = %u%%", value);

    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in gatt_char_mode3_intensity_write");
        return BLE_ATT_ERR_UNLIKELY;
    }
    char_data.mode3_intensity = value;
    settings_dirty = true;
    xSemaphoreGive(char_data_mutex);

    ble_callback_params_updated();
    sync_settings_to_peer();
    return 0;
}

// Mode 4 (Custom) Intensity - Read
static int gatt_char_mode4_intensity_read(uint16_t conn_handle, uint16_t attr_handle,
                                          struct ble_gatt_access_ctxt *ctxt, void *arg) {
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in gatt_char_mode4_intensity_read - possible deadlock");
        return BLE_ATT_ERR_UNLIKELY;
    }
    uint8_t intensity = char_data.mode4_intensity;
    xSemaphoreGive(char_data_mutex);

    ESP_LOGD(TAG, "GATT Read: Mode 4 Intensity = %u%%", intensity);
    int rc = os_mbuf_append(ctxt->om, &intensity, sizeof(intensity));
    return (rc == 0) ? 0 : BLE_ATT_ERR_INSUFFICIENT_RES;
}

// Mode 4 (Custom) Intensity - Write
static int gatt_char_mode4_intensity_write(uint16_t conn_handle, uint16_t attr_handle,
                                           struct ble_gatt_access_ctxt *ctxt, void *arg) {
    uint8_t value;
    int rc = ble_hs_mbuf_to_flat(ctxt->om, &value, sizeof(value), NULL);
    if (rc != 0) {
        ESP_LOGE(TAG, "GATT Write: Mode 4 Intensity read failed");
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    // AD032: Range 30-80% for Mode 4 (Custom) (0-29% reserved for LED-only if needed)
    if (value > 80) {
        ESP_LOGE(TAG, "GATT Write: Invalid Mode 4 Intensity %u%% (range 30-80)", value);
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    ESP_LOGD(TAG, "GATT Write: Mode 4 Intensity = %u%%", value);

    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in gatt_char_mode4_intensity_write - possible deadlock");
        return BLE_ATT_ERR_UNLIKELY;
    }
    char_data.mode4_intensity = value;
    settings_dirty = true;
    xSemaphoreGive(char_data_mutex);

    esp_err_t err = motor_update_mode5_intensity(value);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Failed to update Mode 4 Intensity: %s", esp_err_to_name(err));
    }

    ble_callback_params_updated();

    // Phase 3a: Sync ALL settings to peer device (coordination message)
    sync_settings_to_peer();

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

    // Phase 3a: Sync ALL settings to peer device (coordination message)
    sync_settings_to_peer();

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

    // Phase 3a: Sync ALL settings to peer device (coordination message)
    sync_settings_to_peer();

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

    // Phase 3a: Sync ALL settings to peer device (coordination message)
    sync_settings_to_peer();

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

    // Phase 3a: Sync ALL settings to peer device (coordination message)
    sync_settings_to_peer();

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

    // Phase 3a: Sync ALL settings to peer device (coordination message)
    sync_settings_to_peer();

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

    // Phase 3a: Sync ALL settings to peer device (coordination message)
    sync_settings_to_peer();

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

// Client Battery Level - Read (dual-device mode, Phase 6)
static int gatt_char_client_battery_read(uint16_t conn_handle, uint16_t attr_handle,
                                         struct ble_gatt_access_ctxt *ctxt, void *arg) {
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in gatt_char_client_battery_read - possible deadlock");
        return BLE_ATT_ERR_UNLIKELY;
    }
    uint8_t client_battery_val = char_data.client_battery_level;
    xSemaphoreGive(char_data_mutex);

    ESP_LOGD(TAG, "GATT Read: Client Battery = %u%%", client_battery_val);
    int rc = os_mbuf_append(ctxt->om, &client_battery_val, sizeof(client_battery_val));
    return (rc == 0) ? 0 : BLE_ATT_ERR_INSUFFICIENT_RES;
}

// Local Firmware Version - Read (AD032: immutable after init, no mutex needed)
static int gatt_char_local_firmware_read(uint16_t conn_handle, uint16_t attr_handle,
                                          struct ble_gatt_access_ctxt *ctxt, void *arg) {
    ESP_LOGD(TAG, "GATT Read: Local Firmware = %s", local_firmware_version_str);
    int rc = os_mbuf_append(ctxt->om, local_firmware_version_str,
                            strlen(local_firmware_version_str));
    return (rc == 0) ? 0 : BLE_ATT_ERR_INSUFFICIENT_RES;
}

// Peer Firmware Version - Read (AD032: TODO AD040 for peer version exchange)
static int gatt_char_peer_firmware_read(uint16_t conn_handle, uint16_t attr_handle,
                                         struct ble_gatt_access_ctxt *ctxt, void *arg) {
    ESP_LOGD(TAG, "GATT Read: Peer Firmware = %s",
             peer_firmware_version_str[0] ? peer_firmware_version_str : "(none)");
    int rc = os_mbuf_append(ctxt->om, peer_firmware_version_str,
                            strlen(peer_firmware_version_str));
    return (rc == 0) ? 0 : BLE_ATT_ERR_INSUFFICIENT_RES;
}

// Local Hardware Info - Read (AD048: silicon revision + 802.11mc FTM capability)
static int gatt_char_local_hardware_read(uint16_t conn_handle, uint16_t attr_handle,
                                          struct ble_gatt_access_ctxt *ctxt, void *arg) {
    ESP_LOGD(TAG, "GATT Read: Local Hardware = %s", local_hardware_info_str);
    int rc = os_mbuf_append(ctxt->om, local_hardware_info_str,
                            strlen(local_hardware_info_str));
    return (rc == 0) ? 0 : BLE_ATT_ERR_INSUFFICIENT_RES;
}

// Peer Hardware Info - Read (AD048: populated after peer connection)
static int gatt_char_peer_hardware_read(uint16_t conn_handle, uint16_t attr_handle,
                                         struct ble_gatt_access_ctxt *ctxt, void *arg) {
    ESP_LOGD(TAG, "GATT Read: Peer Hardware = %s",
             peer_hardware_info_str[0] ? peer_hardware_info_str : "(none)");
    int rc = os_mbuf_append(ctxt->om, peer_hardware_info_str,
                            strlen(peer_hardware_info_str));
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

// Time Sync Beacon - Read (Phase 2: AD039)
static int gatt_bilateral_time_sync_read(uint16_t conn_handle, uint16_t attr_handle,
                                          struct ble_gatt_access_ctxt *ctxt, void *arg) {
    // Only readable by peer devices (not mobile app)
    if (!ble_is_peer_connected()) {
        ESP_LOGW(TAG, "Time sync read attempted by non-peer");
        return BLE_ATT_ERR_READ_NOT_PERMITTED;
    }

    // JPL Rule 6: Bounded mutex wait
    if (xSemaphoreTake(time_sync_beacon_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in time sync read");
        return BLE_ATT_ERR_UNLIKELY;
    }

    time_sync_beacon_t beacon;
    memcpy(&beacon, &g_time_sync_beacon, sizeof(time_sync_beacon_t));
    xSemaphoreGive(time_sync_beacon_mutex);

    ESP_LOGD(TAG, "GATT Read: Time sync beacon (seq: %u)",
             beacon.sequence);

    int rc = os_mbuf_append(ctxt->om, &beacon, sizeof(beacon));
    return (rc == 0) ? 0 : BLE_ATT_ERR_INSUFFICIENT_RES;
}

// Time Sync Beacon - Write (Phase 2: CLIENT receives from SERVER)
static int gatt_bilateral_time_sync_write(uint16_t conn_handle, uint16_t attr_handle,
                                           struct ble_gatt_access_ctxt *ctxt, void *arg) {
    // Only writable by peer devices (not mobile app)
    if (!ble_is_peer_connected()) {
        ESP_LOGW(TAG, "Time sync write attempted by non-peer");
        return BLE_ATT_ERR_WRITE_NOT_PERMITTED;
    }

    time_sync_beacon_t beacon;
    int rc = ble_hs_mbuf_to_flat(ctxt->om, &beacon, sizeof(beacon), NULL);
    if (rc != 0) {
        ESP_LOGE(TAG, "Time sync write: Invalid length");
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    // Get receive timestamp ASAP for accuracy (Phase 6r: One-way timestamp protocol)
    uint64_t receive_time_us = esp_timer_get_time();

    // Forward beacon to time_sync_task for processing (AD048: mark as BLE transport)
    esp_err_t err = time_sync_task_send_beacon(&beacon, receive_time_us, BEACON_TRANSPORT_BLE);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Failed to send beacon to time_sync_task: %s", esp_err_to_name(err));
        return BLE_ATT_ERR_UNLIKELY;
    }

    ESP_LOGD(TAG, "Time sync beacon forwarded to task via BLE (seq: %u)", beacon.sequence);

    return 0;
}

// ============================================================================
// PHASE 3: COORDINATION MESSAGE WRITE HANDLER
// ============================================================================

static int gatt_bilateral_coordination_write(uint16_t conn_handle, uint16_t attr_handle,
                                             struct ble_gatt_access_ctxt *ctxt, void *arg) {
    // Only writable by peer devices (not mobile app)
    if (!ble_is_peer_connected()) {
        ESP_LOGW(TAG, "Coordination message write attempted by non-peer");
        return BLE_ATT_ERR_WRITE_NOT_PERMITTED;
    }

    // Parse coordination message from mbuf
    coordination_message_t msg;
    int rc = ble_hs_mbuf_to_flat(ctxt->om, &msg, sizeof(msg), NULL);
    if (rc != 0) {
        ESP_LOGE(TAG, "Coordination write: Invalid length");
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    // Phase 3: Forward to time_sync_task for handling (moved from motor_task)
    // This prevents BLE processing from blocking motor timing
    esp_err_t err = time_sync_task_send_coordination(&msg);
    if (err != ESP_OK) {
        ESP_LOGW(TAG, "Failed to queue coordination message: %s", esp_err_to_name(err));
    }

    ESP_LOGD(TAG, "Coordination message received: type=%d, timestamp=%lu",
             msg.type, (unsigned long)msg.timestamp_ms);

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

    if (ble_uuid_cmp(uuid, &uuid_char_mode0_intensity.u) == 0) {
        return (ctxt->op == BLE_GATT_ACCESS_OP_READ_CHR) ?
               gatt_char_mode0_intensity_read(conn_handle, attr_handle, ctxt, arg) :
               gatt_char_mode0_intensity_write(conn_handle, attr_handle, ctxt, arg);
    }

    if (ble_uuid_cmp(uuid, &uuid_char_mode1_intensity.u) == 0) {
        return (ctxt->op == BLE_GATT_ACCESS_OP_READ_CHR) ?
               gatt_char_mode1_intensity_read(conn_handle, attr_handle, ctxt, arg) :
               gatt_char_mode1_intensity_write(conn_handle, attr_handle, ctxt, arg);
    }

    if (ble_uuid_cmp(uuid, &uuid_char_mode2_intensity.u) == 0) {
        return (ctxt->op == BLE_GATT_ACCESS_OP_READ_CHR) ?
               gatt_char_mode2_intensity_read(conn_handle, attr_handle, ctxt, arg) :
               gatt_char_mode2_intensity_write(conn_handle, attr_handle, ctxt, arg);
    }

    if (ble_uuid_cmp(uuid, &uuid_char_mode3_intensity.u) == 0) {
        return (ctxt->op == BLE_GATT_ACCESS_OP_READ_CHR) ?
               gatt_char_mode3_intensity_read(conn_handle, attr_handle, ctxt, arg) :
               gatt_char_mode3_intensity_write(conn_handle, attr_handle, ctxt, arg);
    }

    if (ble_uuid_cmp(uuid, &uuid_char_mode4_intensity.u) == 0) {
        return (ctxt->op == BLE_GATT_ACCESS_OP_READ_CHR) ?
               gatt_char_mode4_intensity_read(conn_handle, attr_handle, ctxt, arg) :
               gatt_char_mode4_intensity_write(conn_handle, attr_handle, ctxt, arg);
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

    if (ble_uuid_cmp(uuid, &uuid_char_client_battery.u) == 0) {
        return gatt_char_client_battery_read(conn_handle, attr_handle, ctxt, arg);
    }

    // Firmware Version Group (AD032: read-only)
    if (ble_uuid_cmp(uuid, &uuid_char_local_firmware.u) == 0) {
        return gatt_char_local_firmware_read(conn_handle, attr_handle, ctxt, arg);
    }

    if (ble_uuid_cmp(uuid, &uuid_char_peer_firmware.u) == 0) {
        return gatt_char_peer_firmware_read(conn_handle, attr_handle, ctxt, arg);
    }

    // Hardware Info Group (AD048: read-only, silicon revision + 802.11mc FTM capability)
    if (ble_uuid_cmp(uuid, &uuid_char_local_hardware.u) == 0) {
        return gatt_char_local_hardware_read(conn_handle, attr_handle, ctxt, arg);
    }

    if (ble_uuid_cmp(uuid, &uuid_char_peer_hardware.u) == 0) {
        return gatt_char_peer_hardware_read(conn_handle, attr_handle, ctxt, arg);
    }

    // Time Beacon (AD047/UTLP: passive opportunistic time adoption)
    // PWA broadcasts time beacons; device passively listens and adopts
    if (ble_uuid_cmp(uuid, &uuid_char_time_beacon.u) == 0) {
        if (ctxt->op == BLE_GATT_ACCESS_OP_WRITE_CHR) {
            // Parse time beacon (14 bytes): stratum, quality, utc_time_us, uncertainty_us
            uint16_t om_len = OS_MBUF_PKTLEN(ctxt->om);
            if (om_len != sizeof(pwa_time_inject_t)) {
                ESP_LOGW(TAG, "Time beacon: invalid size %u (expected %u)",
                         om_len, (unsigned)sizeof(pwa_time_inject_t));
                return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
            }

            pwa_time_inject_t beacon;
            int rc = ble_hs_mbuf_to_flat(ctxt->om, &beacon, sizeof(beacon), NULL);
            if (rc != 0) {
                ESP_LOGE(TAG, "Time beacon: mbuf parse failed: %d", rc);
                return BLE_ATT_ERR_UNLIKELY;
            }

            // Log and adopt (UTLP: always adopt from external source)
            ESP_LOGI(TAG, "Time beacon received: stratum=%u quality=%u time=%llu us uncertainty=%d us",
                     beacon.stratum, beacon.quality,
                     (unsigned long long)beacon.utc_time_us, (int)beacon.uncertainty_us);

            esp_err_t err = time_sync_inject_pwa_time(&beacon);
            if (err != ESP_OK) {
                ESP_LOGE(TAG, "Time beacon adoption failed: %s", esp_err_to_name(err));
                return BLE_ATT_ERR_UNLIKELY;
            }

            return 0;  // Success
        }
        return BLE_ATT_ERR_UNLIKELY;  // Write-only characteristic
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

    // Phase 2: Time synchronization
    if (ble_uuid_cmp(uuid, &uuid_bilateral_time_sync.u) == 0) {
        return (ctxt->op == BLE_GATT_ACCESS_OP_READ_CHR) ?
               gatt_bilateral_time_sync_read(conn_handle, attr_handle, ctxt, arg) :
               gatt_bilateral_time_sync_write(conn_handle, attr_handle, ctxt, arg);
    }

    // Phase 3: Coordination messages (write-only)
    if (ble_uuid_cmp(uuid, &uuid_bilateral_coordination.u) == 0) {
        if (ctxt->op == BLE_GATT_ACCESS_OP_WRITE_CHR) {
            return gatt_bilateral_coordination_write(conn_handle, attr_handle, ctxt, arg);
        }
        return BLE_ATT_ERR_UNLIKELY;  // No READ support
    }

    // ========================================================================
    // AD047: Pattern Control Group (Mode 5 lightbar/bilateral patterns)
    // ========================================================================

    // Pattern Control (0x0217) - Write-only: 0=stop, 1=start, 2+=select builtin pattern
    if (ble_uuid_cmp(uuid, &uuid_char_pattern_control.u) == 0) {
        if (ctxt->op == BLE_GATT_ACCESS_OP_WRITE_CHR) {
            uint16_t len = OS_MBUF_PKTLEN(ctxt->om);
            if (len < 1) {
                ESP_LOGW(TAG, "Pattern control: empty write");
                return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
            }

            uint8_t control_cmd;
            int rc = ble_hs_mbuf_to_flat(ctxt->om, &control_cmd, sizeof(control_cmd), NULL);
            if (rc != 0) {
                return BLE_ATT_ERR_UNLIKELY;
            }

            esp_err_t err = ESP_OK;

            switch (control_cmd) {
                case 0:  // Stop pattern
                    ESP_LOGI(TAG, "Pattern control: STOP");
                    err = pattern_stop();
                    pattern_status = 0;  // Stopped
                    break;

                case 1:  // Start pattern (using loaded pattern)
                    ESP_LOGI(TAG, "Pattern control: START");
                    err = pattern_start(0);  // 0 = start immediately
                    if (err == ESP_OK) {
                        pattern_status = 1;  // Playing
                    } else {
                        ESP_LOGW(TAG, "Pattern start failed: %s", esp_err_to_name(err));
                        pattern_status = 2;  // Error
                    }
                    break;

                default:  // 2+ = Load and start builtin pattern
                    {
                        builtin_pattern_id_t pattern_id = (builtin_pattern_id_t)(control_cmd - 1);
                        ESP_LOGI(TAG, "Pattern control: LOAD builtin %d", pattern_id);

                        err = pattern_load_builtin(pattern_id);
                        if (err == ESP_OK) {
                            err = pattern_start(0);  // Start immediately after load
                            pattern_status = (err == ESP_OK) ? 1 : 2;
                        } else {
                            ESP_LOGW(TAG, "Pattern load failed: %s", esp_err_to_name(err));
                            pattern_status = 2;  // Error
                        }
                    }
                    break;
            }

            // Sync pattern selection to peer device (if connected)
            if (err == ESP_OK && ble_is_peer_connected()) {
                // Get synchronized start time for bilateral coordination
                uint64_t start_time_us = 0;
                time_sync_get_time(&start_time_us);

                // Send pattern change to peer with same start time
                coordination_message_t coord_msg = {
                    .type = SYNC_MSG_PATTERN_CHANGE,
                    .timestamp_ms = (uint32_t)(esp_timer_get_time() / 1000),
                    .payload.pattern_sync = {
                        .control_cmd = control_cmd,
                        .start_time_us = start_time_us
                    }
                };

                esp_err_t send_err = ble_send_coordination_message(&coord_msg);
                if (send_err == ESP_OK) {
                    ESP_LOGI(TAG, "Pattern sync sent to peer: cmd=%d, start=%llu",
                             control_cmd, (unsigned long long)start_time_us);
                } else {
                    ESP_LOGW(TAG, "Failed to send pattern sync to peer: %s", esp_err_to_name(send_err));
                }
            }

            // TODO: Send notification to subscribed clients with updated pattern_status
            return (err == ESP_OK) ? 0 : BLE_ATT_ERR_UNLIKELY;
        }
        return BLE_ATT_ERR_UNLIKELY;  // Write-only characteristic
    }

    // Pattern Data (0x0218) - Write-only: chunked pattern data (future)
    if (ble_uuid_cmp(uuid, &uuid_char_pattern_data.u) == 0) {
        if (ctxt->op == BLE_GATT_ACCESS_OP_WRITE_CHR) {
            // Future: Implement chunked pattern transfer from PWA
            // For now, return "not supported" since we only use builtin patterns
            ESP_LOGW(TAG, "Pattern data write: NOT YET IMPLEMENTED (use builtin patterns)");
            return BLE_ATT_ERR_WRITE_NOT_PERMITTED;
        }
        return BLE_ATT_ERR_UNLIKELY;  // Write-only characteristic
    }

    // Pattern Status (0x0219) - Read + Notify: 0=stopped, 1=playing, 2=error
    if (ble_uuid_cmp(uuid, &uuid_char_pattern_status.u) == 0) {
        if (ctxt->op == BLE_GATT_ACCESS_OP_READ_CHR) {
            // Update status from actual playback state
            pattern_status = pattern_is_playing() ? 1 : 0;

            int rc = os_mbuf_append(ctxt->om, &pattern_status, sizeof(pattern_status));
            return (rc == 0) ? 0 : BLE_ATT_ERR_INSUFFICIENT_RES;
        }
        return BLE_ATT_ERR_UNLIKELY;  // Read+Notify only, no write
    }

    // Pattern List (0x021A) - Read-only: JSON list of available patterns
    // PWA reads once on connection to discover available patterns
    if (ble_uuid_cmp(uuid, &uuid_char_pattern_list.u) == 0) {
        if (ctxt->op == BLE_GATT_ACCESS_OP_READ_CHR) {
            // Static JSON - pattern IDs match Pattern Control write values
            static const char pattern_list_json[] =
                "[{\"id\":2,\"name\":\"Alternating\",\"desc\":\"Green bilateral\"},"
                "{\"id\":3,\"name\":\"Emergency\",\"desc\":\"Red/blue wig-wag\"},"
                "{\"id\":4,\"name\":\"Breathe\",\"desc\":\"Cyan pulse\"}]";

            int rc = os_mbuf_append(ctxt->om, pattern_list_json, strlen(pattern_list_json));
            return (rc == 0) ? 0 : BLE_ATT_ERR_INSUFFICIENT_RES;
        }
        return BLE_ATT_ERR_UNLIKELY;  // Read-only
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
                // Phase 2: Time synchronization (AD039)
                .uuid = &uuid_bilateral_time_sync.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_WRITE | BLE_GATT_CHR_F_NOTIFY,
            },
            {
                // Phase 3: Coordination messages (hybrid architecture)
                // Mode sync, settings sync, shutdown commands, advertising control
                // Bug #60 fix: Add WRITE_NO_RSP - CLIENT uses ble_gattc_write_no_rsp_flat()
                .uuid = &uuid_bilateral_coordination.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_WRITE | BLE_GATT_CHR_F_WRITE_NO_RSP | BLE_GATT_CHR_F_NOTIFY,
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
                .flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_WRITE | BLE_GATT_CHR_F_NOTIFY,
                .val_handle = &g_freq_val_handle,  // Phase 3a: Notification-based sync
            },
            {
                .uuid = &uuid_char_custom_duty.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_WRITE | BLE_GATT_CHR_F_NOTIFY,
                .val_handle = &g_duty_val_handle,  // Phase 3a: Notification-based sync
            },
            {
                .uuid = &uuid_char_mode0_intensity.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_WRITE | BLE_GATT_CHR_F_NOTIFY,
                .val_handle = &g_mode0_val_handle,  // Phase 3a: Notification-based sync
            },
            {
                .uuid = &uuid_char_mode1_intensity.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_WRITE | BLE_GATT_CHR_F_NOTIFY,
                .val_handle = &g_mode1_val_handle,  // Phase 3a: Notification-based sync
            },
            {
                .uuid = &uuid_char_mode2_intensity.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_WRITE | BLE_GATT_CHR_F_NOTIFY,
                .val_handle = &g_mode2_val_handle,  // Phase 3a: Notification-based sync
            },
            {
                .uuid = &uuid_char_mode3_intensity.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_WRITE | BLE_GATT_CHR_F_NOTIFY,
                .val_handle = &g_mode3_val_handle,  // Phase 3a: Notification-based sync
            },
            {
                .uuid = &uuid_char_mode4_intensity.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_WRITE | BLE_GATT_CHR_F_NOTIFY,
                .val_handle = &g_mode4_val_handle,  // Phase 3a: Notification-based sync
            },
            // LED Control Group
            {
                .uuid = &uuid_char_led_enable.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_WRITE | BLE_GATT_CHR_F_NOTIFY,
                .val_handle = &g_led_enable_val_handle,  // Phase 3a: Notification-based sync
            },
            {
                .uuid = &uuid_char_led_color_mode.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_WRITE | BLE_GATT_CHR_F_NOTIFY,
                .val_handle = &g_led_color_mode_val_handle,  // Phase 3a: Notification-based sync
            },
            {
                .uuid = &uuid_char_led_palette.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_WRITE | BLE_GATT_CHR_F_NOTIFY,
                .val_handle = &g_led_palette_val_handle,  // Phase 3a: Notification-based sync
            },
            {
                .uuid = &uuid_char_led_custom_rgb.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_WRITE | BLE_GATT_CHR_F_NOTIFY,
                .val_handle = &g_led_custom_rgb_val_handle,  // Phase 3a: Notification-based sync
            },
            {
                .uuid = &uuid_char_led_brightness.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_WRITE | BLE_GATT_CHR_F_NOTIFY,
                .val_handle = &g_led_brightness_val_handle,  // Phase 3a: Notification-based sync
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
                .uuid = &uuid_char_client_battery.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_NOTIFY,
            },
            // Firmware Version Group (AD032)
            {
                .uuid = &uuid_char_local_firmware.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_READ,
            },
            {
                .uuid = &uuid_char_peer_firmware.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_READ,
            },
            // Hardware Info Group (AD048: silicon revision + 802.11mc FTM capability)
            {
                .uuid = &uuid_char_local_hardware.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_READ,
            },
            {
                .uuid = &uuid_char_peer_hardware.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_READ,
            },
            // Time Beacon Group (AD047/UTLP: passive opportunistic adoption)
            {
                .uuid = &uuid_char_time_beacon.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_WRITE,  // Write-only: PWA broadcasts time beacons
            },
            // Pattern Control Group (AD047: Mode 5 lightbar/bilateral patterns)
            {
                .uuid = &uuid_char_pattern_control.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_WRITE,  // Write-only: 0=stop, 1=start, 2+=select builtin
            },
            {
                .uuid = &uuid_char_pattern_data.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_WRITE,  // Write-only: chunked pattern data (future)
            },
            {
                .uuid = &uuid_char_pattern_status.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_NOTIFY,  // Read + Notify: 0=stopped, 1=playing, 2=error
            },
            {
                .uuid = &uuid_char_pattern_list.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_READ,  // Read-only: JSON list of available patterns
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

            // Capture time sync characteristic handle (Phase 2 - AD039)
            // This handle is required for ble_send_time_sync_beacon() to send notifications
            if (ble_uuid_cmp(ctxt->chr.chr_def->uuid, &uuid_bilateral_time_sync.u) == 0) {
                g_time_sync_char_handle = ctxt->chr.val_handle;
                ESP_LOGI(TAG, "Time sync characteristic handle captured: %u", g_time_sync_char_handle);
            }

            // Capture coordination characteristic handle (Phase 3 - Hybrid Architecture)
            // This handle is required for ble_send_coordination_message() to send notifications
            if (ble_uuid_cmp(ctxt->chr.chr_def->uuid, &uuid_bilateral_coordination.u) == 0) {
                g_coordination_char_handle = ctxt->chr.val_handle;
                ESP_LOGI(TAG, "Coordination characteristic handle captured: %u", g_coordination_char_handle);
            }
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

// ============================================================================
// GATT CLIENT DISCOVERY CALLBACKS (Phase 2 - CLIENT role time sync)
// ============================================================================

/**
 * @brief GATT client callback: CCCD write completion
 *
 * Called after successfully writing to Client Characteristic Configuration Descriptor
 * to enable notifications for time sync characteristic.
 *
 * @param conn_handle Connection handle
 * @param error Error code (0 = success)
 * @param attr Attribute handle
 * @param arg User argument (unused)
 * @return 0 on success
 */
static int gattc_on_cccd_write(uint16_t conn_handle,
                                const struct ble_gatt_error *error,
                                struct ble_gatt_attr *attr,
                                void *arg)
{
    if (error->status == 0) {
        ESP_LOGI(TAG, "CLIENT: Time sync notifications ENABLED (CCCD write successful)");
        ESP_LOGI(TAG, "CLIENT: Ready to receive sync beacons from SERVER");

        /* PHASE 6r: Now that connection is fully ready (services discovered,
         * characteristics found, notifications enabled), initialize time sync.
         * Moved from GAP connect event to fix BLE_HS_EALREADY (259) and
         * BLE_ERR_UNK_CONN_ID (0x202) race conditions.
         */
        time_sync_role_t sync_role = (peer_state.role == PEER_ROLE_SERVER) ?
                                      TIME_SYNC_ROLE_SERVER : TIME_SYNC_ROLE_CLIENT;
        esp_err_t reconnect_rc = time_sync_on_reconnection(sync_role);
        if (reconnect_rc != ESP_OK) {
            ESP_LOGW(TAG, "time_sync_on_reconnection failed; rc=%d", reconnect_rc);
        }
        // Note: time_sync_on_reconnection returns ESP_OK on initial connection too
        // (before time_sync_init called), so we don't log "initialized" here
    } else {
        ESP_LOGE(TAG, "CLIENT: Failed to write CCCD; status=%d", error->status);
    }
    return 0;
}

/**
 * @brief Timer callback for deferred Configuration Service discovery (Bug #31 fix)
 *
 * This callback runs 50ms after Bilateral Service discovery completes, giving
 * the NimBLE stack time to finish processing the completion event before starting
 * Configuration Service discovery. This avoids BLE_HS_EBUSY errors.
 *
 * @param arg Unused
 */
static void deferred_discovery_timer_cb(void *arg) {
    (void)arg;  // Unused

    if (g_config_service_found && g_discovery_conn_handle != BLE_HS_CONN_HANDLE_NONE) {
        ESP_LOGI(TAG, "CLIENT: Starting deferred Configuration Service characteristic discovery");
        int rc = ble_gattc_disc_all_chrs(g_discovery_conn_handle,
                                          g_config_service_start_handle,
                                          g_config_service_end_handle,
                                          gattc_on_chr_disc,
                                          NULL);
        if (rc != 0) {
            ESP_LOGE(TAG, "CLIENT: Failed to start deferred Configuration Service discovery; rc=%d", rc);
        }

        // Reset flags for next connection
        g_config_service_found = false;
    }
}

/**
 * @brief GATT client callback: Characteristic discovery completion
 *
 * Called for each characteristic found during discovery.
 * Searches for time sync characteristic and initiates descriptor discovery.
 *
 * @param conn_handle Connection handle
 * @param error Error code
 * @param chr Characteristic
 * @param arg User argument (unused)
 * @return 0 to continue discovery, non-zero to stop
 */
static int gattc_on_chr_disc(uint16_t conn_handle,
                              const struct ble_gatt_error *error,
                              const struct ble_gatt_chr *chr,
                              void *arg)
{
    if (error->status != 0) {
        // BLE_HS_EDONE (14) is normal "discovery done" status, not an error
        if (error->status == 14) {
            ESP_LOGD(TAG, "CLIENT: Characteristic discovery done (status=14 - BLE_HS_EDONE)");
        } else {
            ESP_LOGE(TAG, "CLIENT: Characteristic discovery error; status=%d", error->status);
        }
        return 0;
    }

    if (chr == NULL) {
        // Discovery complete
        ESP_LOGI(TAG, "CLIENT: Characteristic discovery complete");

        // If this was Bilateral Service discovery, mark complete and start Config Service discovery
        if (!g_bilateral_discovery_complete) {
            g_bilateral_discovery_complete = true;
            ESP_LOGI(TAG, "CLIENT: Bilateral Service discovery complete");

            // Bug #31 Fix: Schedule Configuration Service discovery via timer (avoids BLE_HS_EBUSY)
            // The NimBLE stack is still processing the Bilateral discovery completion event.
            // Starting Config discovery immediately causes BLE_HS_EBUSY. Defer by 50ms.
            if (g_config_service_found && g_deferred_discovery_timer != NULL) {
                ESP_LOGI(TAG, "CLIENT: Scheduling Configuration Service discovery (50ms delay to avoid BUSY)");
                esp_err_t err = esp_timer_start_once(g_deferred_discovery_timer, 50000);  // 50ms = 50000µs
                if (err != ESP_OK) {
                    ESP_LOGE(TAG, "CLIENT: Failed to start deferred discovery timer: %s", esp_err_to_name(err));
                    // Fallback: reset flag to prevent stale state
                    g_config_service_found = false;
                }
            }
        }

        return 0;
    }

    // Compare UUID with coordination characteristic (Phase 3 - Hybrid Architecture)
    // Note: Time sync CCCD subscription removed (v0.7.10) - beacons now via ESP-NOW
    if (ble_uuid_cmp(&chr->uuid.u, &uuid_bilateral_coordination.u) == 0) {
        ESP_LOGI(TAG, "CLIENT: Found coordination characteristic; val_handle=%u", chr->val_handle);

        // Store handle for notification reception and writes
        g_peer_coordination_char_handle = chr->val_handle;

        // Enable notifications for coordination messages
        uint16_t cccd_handle = chr->val_handle + 1;
        uint16_t notify_enable = 1;  // 0x0001 = notifications enabled

        int rc = ble_gattc_write_flat(conn_handle, cccd_handle,
                                       &notify_enable, sizeof(notify_enable),
                                       gattc_on_cccd_write, NULL);
        if (rc != 0) {
            ESP_LOGE(TAG, "CLIENT: Failed to write coordination CCCD at handle %u; rc=%d", cccd_handle, rc);
        } else {
            ESP_LOGI(TAG, "CLIENT: Coordination CCCD write initiated at handle %u (enabling notifications)", cccd_handle);
        }

        // AD040: Send firmware version to peer now that coordination handle is valid
        // Both SERVER and CLIENT go through GATT discovery, so both send here.
        // Each side sends once - handler does NOT respond (avoids infinite loop).
        ESP_LOGI(TAG, "AD040: Coordination handle discovered, sending firmware version");
        esp_err_t fw_err = ble_send_firmware_version_to_peer();
        if (fw_err != ESP_OK) {
            ESP_LOGW(TAG, "AD040: Firmware version send failed: %s", esp_err_to_name(fw_err));
        }

        // AD048: Send hardware info (silicon revision, FTM capability) alongside firmware version
        esp_err_t hw_err = ble_send_hardware_info_to_peer();
        if (hw_err != ESP_OK) {
            ESP_LOGW(TAG, "AD048: Hardware info send failed: %s", esp_err_to_name(hw_err));
        }

        // AD048: Send WiFi MAC for ESP-NOW transport setup (if ESP-NOW initialized)
        if (espnow_transport_get_state() != ESPNOW_STATE_UNINITIALIZED) {
            esp_err_t mac_err = ble_send_wifi_mac_to_peer();
            if (mac_err != ESP_OK) {
                ESP_LOGW(TAG, "AD048: WiFi MAC send failed: %s", esp_err_to_name(mac_err));
            }
        }
    }

    // Phase 3a: Subscribe to configuration characteristics for notification-based sync
    // Pattern: For each config characteristic that we write from SERVER, CLIENT subscribes to notifications

    // Custom Frequency
    if (ble_uuid_cmp(&chr->uuid.u, &uuid_char_custom_freq.u) == 0) {
        ESP_LOGI(TAG, "CLIENT: Found frequency characteristic; val_handle=%u", chr->val_handle);
        g_peer_freq_val_handle = chr->val_handle;

        uint16_t cccd_handle = chr->val_handle + 1;
        uint16_t notify_enable = 1;
        int rc = ble_gattc_write_flat(conn_handle, cccd_handle,
                                       &notify_enable, sizeof(notify_enable),
                                       gattc_on_cccd_write, NULL);
        if (rc == 0) {
            ESP_LOGI(TAG, "CLIENT: Subscribed to frequency notifications at handle %u", cccd_handle);
        }
    }

    // Custom Duty Cycle
    if (ble_uuid_cmp(&chr->uuid.u, &uuid_char_custom_duty.u) == 0) {
        ESP_LOGI(TAG, "CLIENT: Found duty cycle characteristic; val_handle=%u", chr->val_handle);
        g_peer_duty_val_handle = chr->val_handle;

        uint16_t cccd_handle = chr->val_handle + 1;
        uint16_t notify_enable = 1;
        int rc = ble_gattc_write_flat(conn_handle, cccd_handle,
                                       &notify_enable, sizeof(notify_enable),
                                       gattc_on_cccd_write, NULL);
        if (rc == 0) {
            ESP_LOGI(TAG, "CLIENT: Subscribed to duty cycle notifications at handle %u", cccd_handle);
        }
    }

    // Mode 0-4 Intensity Characteristics (no notifications - updated via SYNC_MSG_SETTINGS)
    if (ble_uuid_cmp(&chr->uuid.u, &uuid_char_mode0_intensity.u) == 0) {
        ESP_LOGI(TAG, "CLIENT: Found mode 0 intensity characteristic; val_handle=%u", chr->val_handle);
        g_peer_mode0_val_handle = chr->val_handle;
    }

    if (ble_uuid_cmp(&chr->uuid.u, &uuid_char_mode1_intensity.u) == 0) {
        ESP_LOGI(TAG, "CLIENT: Found mode 1 intensity characteristic; val_handle=%u", chr->val_handle);
        g_peer_mode1_val_handle = chr->val_handle;
    }

    if (ble_uuid_cmp(&chr->uuid.u, &uuid_char_mode2_intensity.u) == 0) {
        ESP_LOGI(TAG, "CLIENT: Found mode 2 intensity characteristic; val_handle=%u", chr->val_handle);
        g_peer_mode2_val_handle = chr->val_handle;
    }

    if (ble_uuid_cmp(&chr->uuid.u, &uuid_char_mode3_intensity.u) == 0) {
        ESP_LOGI(TAG, "CLIENT: Found mode 3 intensity characteristic; val_handle=%u", chr->val_handle);
        g_peer_mode3_val_handle = chr->val_handle;
    }

    if (ble_uuid_cmp(&chr->uuid.u, &uuid_char_mode4_intensity.u) == 0) {
        ESP_LOGI(TAG, "CLIENT: Found mode 4 intensity characteristic; val_handle=%u", chr->val_handle);
        g_peer_mode4_val_handle = chr->val_handle;
    }

    // LED Enable
    if (ble_uuid_cmp(&chr->uuid.u, &uuid_char_led_enable.u) == 0) {
        ESP_LOGI(TAG, "CLIENT: Found LED enable characteristic; val_handle=%u", chr->val_handle);
        g_peer_led_enable_val_handle = chr->val_handle;

        uint16_t cccd_handle = chr->val_handle + 1;
        uint16_t notify_enable = 1;
        int rc = ble_gattc_write_flat(conn_handle, cccd_handle,
                                       &notify_enable, sizeof(notify_enable),
                                       gattc_on_cccd_write, NULL);
        if (rc == 0) {
            ESP_LOGI(TAG, "CLIENT: Subscribed to LED enable notifications at handle %u", cccd_handle);
        }
    }

    // LED Color Mode
    if (ble_uuid_cmp(&chr->uuid.u, &uuid_char_led_color_mode.u) == 0) {
        ESP_LOGI(TAG, "CLIENT: Found LED color mode characteristic; val_handle=%u", chr->val_handle);
        g_peer_led_color_mode_val_handle = chr->val_handle;

        uint16_t cccd_handle = chr->val_handle + 1;
        uint16_t notify_enable = 1;
        int rc = ble_gattc_write_flat(conn_handle, cccd_handle,
                                       &notify_enable, sizeof(notify_enable),
                                       gattc_on_cccd_write, NULL);
        if (rc == 0) {
            ESP_LOGI(TAG, "CLIENT: Subscribed to LED color mode notifications at handle %u", cccd_handle);
        }
    }

    // LED Palette
    if (ble_uuid_cmp(&chr->uuid.u, &uuid_char_led_palette.u) == 0) {
        ESP_LOGI(TAG, "CLIENT: Found LED palette characteristic; val_handle=%u", chr->val_handle);
        g_peer_led_palette_val_handle = chr->val_handle;

        uint16_t cccd_handle = chr->val_handle + 1;
        uint16_t notify_enable = 1;
        int rc = ble_gattc_write_flat(conn_handle, cccd_handle,
                                       &notify_enable, sizeof(notify_enable),
                                       gattc_on_cccd_write, NULL);
        if (rc == 0) {
            ESP_LOGI(TAG, "CLIENT: Subscribed to LED palette notifications at handle %u", cccd_handle);
        }
    }

    // LED Custom RGB
    if (ble_uuid_cmp(&chr->uuid.u, &uuid_char_led_custom_rgb.u) == 0) {
        ESP_LOGI(TAG, "CLIENT: Found LED custom RGB characteristic; val_handle=%u", chr->val_handle);
        g_peer_led_custom_rgb_val_handle = chr->val_handle;

        uint16_t cccd_handle = chr->val_handle + 1;
        uint16_t notify_enable = 1;
        int rc = ble_gattc_write_flat(conn_handle, cccd_handle,
                                       &notify_enable, sizeof(notify_enable),
                                       gattc_on_cccd_write, NULL);
        if (rc == 0) {
            ESP_LOGI(TAG, "CLIENT: Subscribed to LED custom RGB notifications at handle %u", cccd_handle);
        }
    }

    // LED Brightness
    if (ble_uuid_cmp(&chr->uuid.u, &uuid_char_led_brightness.u) == 0) {
        ESP_LOGI(TAG, "CLIENT: Found LED brightness characteristic; val_handle=%u", chr->val_handle);
        g_peer_led_brightness_val_handle = chr->val_handle;

        uint16_t cccd_handle = chr->val_handle + 1;
        uint16_t notify_enable = 1;
        int rc = ble_gattc_write_flat(conn_handle, cccd_handle,
                                       &notify_enable, sizeof(notify_enable),
                                       gattc_on_cccd_write, NULL);
        if (rc == 0) {
            ESP_LOGI(TAG, "CLIENT: Subscribed to LED brightness notifications at handle %u", cccd_handle);
        }
    }

    return 0;
}

/**
 * @brief GATT client callback: Service discovery completion
 *
 * Called for each service found during discovery.
 * Searches for Bilateral Control Service and initiates characteristic discovery.
 *
 * @param conn_handle Connection handle
 * @param error Error code
 * @param service Service
 * @param arg User argument (unused)
 * @return 0 to continue discovery, non-zero to stop
 */
static int gattc_on_svc_disc(uint16_t conn_handle,
                              const struct ble_gatt_error *error,
                              const struct ble_gatt_svc *service,
                              void *arg)
{
    if (error->status != 0) {
        // BLE_HS_EDONE (14) is normal "discovery done" status, not an error
        if (error->status == 14) {
            ESP_LOGD(TAG, "CLIENT: Service discovery done (status=14 - BLE_HS_EDONE)");
        } else {
            ESP_LOGE(TAG, "CLIENT: Service discovery error; status=%d", error->status);
        }
        return 0;
    }

    if (service == NULL) {
        // Discovery complete
        ESP_LOGI(TAG, "CLIENT: Service discovery complete");
        return 0;
    }

    // Compare UUID with Bilateral Control Service
    if (ble_uuid_cmp(&service->uuid.u, &uuid_bilateral_service.u) == 0) {
        ESP_LOGI(TAG, "CLIENT: Found Bilateral Control Service; start_handle=%u, end_handle=%u",
                 service->start_handle, service->end_handle);

        // Start characteristic discovery within this service
        int rc = ble_gattc_disc_all_chrs(conn_handle,
                                          service->start_handle,
                                          service->end_handle,
                                          gattc_on_chr_disc,
                                          NULL);
        if (rc != 0) {
            ESP_LOGE(TAG, "CLIENT: Failed to start characteristic discovery; rc=%d", rc);
        } else {
            ESP_LOGI(TAG, "CLIENT: Characteristic discovery started");
        }
    }

    // Phase 3a: Also discover Configuration Service for notification-based settings sync
    // DEFER this discovery until Bilateral Service discovery completes to avoid concurrent discovery conflicts
    if (ble_uuid_cmp(&service->uuid.u, &uuid_config_service.u) == 0) {
        ESP_LOGI(TAG, "CLIENT: Found Configuration Service; start_handle=%u, end_handle=%u",
                 service->start_handle, service->end_handle);

        // Store service info for deferred discovery
        g_config_service_found = true;
        g_config_service_start_handle = service->start_handle;
        g_config_service_end_handle = service->end_handle;
        g_discovery_conn_handle = conn_handle;

        ESP_LOGI(TAG, "CLIENT: Configuration Service discovery DEFERRED (will start after Bilateral Service completes)");
    }

    return 0;
}

// ============================================================================
// BLE GAP EVENT HANDLER
// ============================================================================

static int ble_gap_event(struct ble_gap_event *event, void *arg) {
    int rc;

    switch (event->type) {
        case BLE_GAP_EVENT_CONNECT:
            if (event->connect.status == 0) {
                ESP_LOGI(TAG, "BLE connection established; conn_handle=%d", event->connect.conn_handle);

                // Reset discovery state for new connection
                g_bilateral_discovery_complete = false;
                g_config_service_found = false;
                g_config_service_start_handle = 0;
                g_config_service_end_handle = 0;
                g_discovery_conn_handle = event->connect.conn_handle;

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

                // Bug #45: Use pairing window state flag instead of time-based check
                // This prevents race conditions where multiple connections arrive simultaneously
                // and prevents accepting peers after early pairing completes (e.g., at T=5s)
                if (current_uuid == &uuid_bilateral_service && !peer_pairing_window_closed) {
                    // CASE 1: Advertising Bilateral UUID AND pairing window still open
                    // Mobile apps CANNOT discover device during Bilateral UUID window (Bug #27 eliminated!)
                    is_peer = true;
                    peer_state.peer_discovered = true;
                    memcpy(&peer_state.peer_addr, &desc.peer_id_addr, sizeof(ble_addr_t));

                    // CRITICAL: Close pairing window immediately to prevent subsequent connections
                    // from being identified as peers (handles simultaneous connection race condition)
                    peer_pairing_window_closed = true;

                    uint32_t now_ms = (uint32_t)(esp_timer_get_time() / 1000);
                    uint32_t elapsed_ms = now_ms - ble_boot_time_ms;
                    ESP_LOGI(TAG, "Peer identified (connected at T=%lu ms, pairing window now closed)", elapsed_ms);
                } else if (current_uuid == &uuid_bilateral_service && peer_pairing_window_closed) {
                    // Bug #45: Pairing window already closed (peer paired OR 30s timeout)
                    // This handles:
                    // 1. Late connections arriving after 30s timeout
                    // 2. Mobile app connections after early peer pairing (e.g., T=5s)
                    // 3. Simultaneous connections (second connection sees closed window)
                    uint32_t now_ms = (uint32_t)(esp_timer_get_time() / 1000);
                    uint32_t elapsed_ms = now_ms - ble_boot_time_ms;
                    ESP_LOGW(TAG, "Connection rejected - pairing window closed (T=%lu ms)", elapsed_ms);
                    is_peer = false;
                } else {
                    // CASE 2: Advertising Config UUID - check if this is bonded peer reconnect
                    // FIX: Check for non-zero cached address instead of peer_discovered flag
                    // (peer_discovered is cleared on disconnect, but peer_addr is preserved)
                    static const ble_addr_t zero_addr = {0};
                    bool has_cached_peer = (memcmp(&peer_state.peer_addr, &zero_addr, sizeof(ble_addr_t)) != 0);
                    bool address_matches = (memcmp(&desc.peer_id_addr, &peer_state.peer_addr, sizeof(ble_addr_t)) == 0);

                    if (has_cached_peer && address_matches) {
                        // Cached address match - peer reconnecting after disconnect
                        is_peer = true;
                        peer_state.peer_discovered = true;  // Restore flag for subsequent logic
                        ESP_LOGI(TAG, "Peer identified (reconnection by cached address)");
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
                    if (!is_bonded && ble_is_peer_connected()) {
                        ESP_LOGW(TAG, "Rejecting unbonded peer (bonded peer already connected)");
                        ble_gap_terminate(event->connect.conn_handle, BLE_ERR_REM_USER_CONN_TERM);
                        break;
                    }

                    if (is_bonded) {
                        ESP_LOGI(TAG, "Bonded peer reconnecting (NVS bond verified)");
                    } else if (current_uuid == &uuid_bilateral_service) {
                        ESP_LOGI(TAG, "Peer connecting (within 30s Bilateral UUID window - initial pairing)");
                    } else {
                        // Config UUID + address match but no NVS bond = RAM-only reconnection
                        ESP_LOGI(TAG, "Peer reconnecting (cached address match, RAM-only mode)");
                    }
                }

                // ===== CONNECTION TYPE HANDLING =====
                if (is_peer) {
                    // Check if we already have a peer connection
                    if (ble_is_peer_connected()) {
                        ESP_LOGW(TAG, "Already connected to peer, rejecting duplicate peer connection");
                        ble_gap_terminate(event->connect.conn_handle, BLE_ERR_REM_USER_CONN_TERM);
                        break;
                    }

                    // Accept peer connection
                    peer_state.peer_connected = true;
                    peer_state.peer_conn_handle = event->connect.conn_handle;
                    ESP_LOGI(TAG, "Peer device connected; conn_handle=%d", event->connect.conn_handle);

                    // AD040: Reset version exchange state for new connection
                    firmware_version_exchanged = false;
                    firmware_versions_match_flag = true;  // Assume match until proven otherwise

                    // CRITICAL: Stop scanning immediately to prevent connection race conditions
                    // This prevents scan callback from discovering and trying to connect to other devices
                    // while we're processing incoming connections (Bug #11 - Windows PC PWA misidentification)
                    int scan_rc = ble_gap_disc_cancel();
                    if (scan_rc == 0 || scan_rc == BLE_HS_EALREADY) {
                        scanning_active = false;
                        ESP_LOGI(TAG, "Scanning stopped (peer connected)");
                    } else if (scan_rc == BLE_HS_EINVAL) {
                        // Scanning wasn't active - that's fine
                        scanning_active = false;
                        ESP_LOGD(TAG, "Scanning already stopped");
                    } else {
                        ESP_LOGW(TAG, "Failed to stop scanning; rc=%d", scan_rc);
                    }

                    // Bug #43 Fix: Correct role mapping from BLE connection role to time sync role
                    // Per AD010: BLE_GAP_ROLE_MASTER = SERVER, BLE_GAP_ROLE_SLAVE = CLIENT
                    // - Connection initiator (MASTER) → TIME SYNC SERVER (sends beacons)
                    // - Connection acceptor (SLAVE) → TIME SYNC CLIENT (receives beacons, applies corrections)
                    // This mapping ensures lower battery device (initiator) has simpler role (SERVER)
                    bool we_initiated = (desc.role == BLE_GAP_ROLE_MASTER);

                    if (we_initiated) {
                        peer_state.role = PEER_ROLE_SERVER;
                        ESP_LOGI(TAG, "SERVER role assigned (BLE MASTER)");

                        // Phase 6f: SERVER initiates MTU exchange for larger beacon payload (28 bytes)
                        // Default MTU is 23 bytes (20 payload) - too small for beacons
                        // MTU exchange runs in parallel with GATT discovery
                        ESP_LOGI(TAG, "SERVER: Initiating MTU exchange for larger beacon payload");
                        int mtu_rc = ble_gattc_exchange_mtu(event->connect.conn_handle, NULL, NULL);
                        if (mtu_rc != 0) {
                            ESP_LOGW(TAG, "SERVER: MTU exchange failed (rc=%d)", mtu_rc);
                        }

                        // Start GATT service discovery to find CLIENT's coordination characteristic
                        // This runs in parallel with MTU exchange
                        ESP_LOGI(TAG, "SERVER: Starting GATT service discovery for peer services");
                        int disc_rc = ble_gattc_disc_all_svcs(event->connect.conn_handle,
                                                               gattc_on_svc_disc,
                                                               NULL);
                        if (disc_rc != 0) {
                            ESP_LOGE(TAG, "SERVER: Failed to start service discovery; rc=%d", disc_rc);
                        }
                    } else {
                        peer_state.role = PEER_ROLE_CLIENT;
                        ESP_LOGI(TAG, "CLIENT role assigned (BLE SLAVE)");

                        // Phase 6f: CLIENT also initiates MTU exchange for bidirectional communication
                        ESP_LOGI(TAG, "CLIENT: Initiating MTU exchange for larger beacon payload");
                        int mtu_rc = ble_gattc_exchange_mtu(event->connect.conn_handle, NULL, NULL);
                        if (mtu_rc != 0) {
                            ESP_LOGW(TAG, "CLIENT: MTU exchange failed (rc=%d)", mtu_rc);
                        }

                        // Start GATT service discovery to find SERVER's time sync characteristic
                        ESP_LOGI(TAG, "CLIENT: Starting GATT service discovery for peer services");
                        int disc_rc = ble_gattc_disc_all_svcs(event->connect.conn_handle,
                                                               gattc_on_svc_disc,
                                                               NULL);
                        if (disc_rc != 0) {
                            ESP_LOGE(TAG, "CLIENT: Failed to start service discovery; rc=%d", disc_rc);
                        }
                    }

                    /* PHASE 6r: time_sync_on_reconnection() MOVED to gattc_on_cccd_write()
                     *
                     * Calling it here (during GAP connection event) was too early and caused:
                     * - BLE_HS_EALREADY (259) - operation already in progress
                     * - BLE_ERR_UNK_CONN_ID (0x202) - connection handle not valid yet
                     *
                     * Now called AFTER service discovery and notification enable complete,
                     * ensuring connection is fully ready before time sync starts.
                     */

                    // Phase 6p: Update connection parameters for long therapeutic sessions
                    // This ensures both CLIENT and SERVER use 32-second supervision timeout (BLE spec max)
                    // even when peer initiated connection with default parameters
                    ESP_LOGI(TAG, "Updating connection parameters for long sessions (32s timeout)");
                    int param_rc = ble_gap_update_params(event->connect.conn_handle, &therapeutic_upd_params);
                    if (param_rc != 0) {
                        ESP_LOGW(TAG, "Failed to update connection parameters; rc=%d (will use negotiated defaults)", param_rc);
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
                    if (ble_is_app_connected()) {
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
                    adv_state.notify_client_battery_subscribed = false;
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

            // IMPROVED: If state tracking failed to identify connection, verify with NimBLE API
            // This handles race conditions where state flags got out of sync with actual connections
            if (!peer_disconnected && !app_disconnected) {
                struct ble_gap_conn_desc desc;

                // Check if peer connection still exists (if we think it should)
                if (peer_state.peer_conn_handle != BLE_HS_CONN_HANDLE_NONE) {
                    int peer_rc = ble_gap_conn_find(peer_state.peer_conn_handle, &desc);
                    if (peer_rc != 0) {
                        // Peer connection no longer exists - THIS disconnect was the peer!
                        ESP_LOGW(TAG, "State tracking mismatch: disconnect was peer (verified by NimBLE API)");
                        peer_disconnected = true;
                    }
                }

                // Check if app connection still exists (if we think it should)
                if (!peer_disconnected && adv_state.conn_handle != BLE_HS_CONN_HANDLE_NONE) {
                    int app_rc = ble_gap_conn_find(adv_state.conn_handle, &desc);
                    if (app_rc != 0) {
                        // App connection no longer exists - THIS disconnect was the app!
                        ESP_LOGW(TAG, "State tracking mismatch: disconnect was app (verified by NimBLE API)");
                        app_disconnected = true;
                    }
                }
            }

            if (peer_disconnected) {
                // Peer device disconnected
                ESP_LOGI(TAG, "Peer device disconnected (was %s)",
                         peer_state.role == PEER_ROLE_SERVER ? "SERVER" :
                         peer_state.role == PEER_ROLE_CLIENT ? "CLIENT" : "NONE");
                peer_state.peer_connected = false;
                peer_state.peer_discovered = false;
                peer_state.peer_conn_handle = BLE_HS_CONN_HANDLE_NONE;
                // NOTE: Preserve peer_state.role for mid-session reconnection!
                // Previous SERVER will initiate reconnect, previous CLIENT will wait.
                // Role is only cleared on fresh pairing (ble_reset_pairing_window).

                // Phase 3: Clear coordination characteristic handle (prevents stale handle blocking)
                g_peer_coordination_char_handle = 0;

                // Bug #31 Fix: Stop deferred discovery timer and reset discovery state
                if (g_deferred_discovery_timer != NULL) {
                    esp_timer_stop(g_deferred_discovery_timer);  // Safe even if not running
                }
                g_bilateral_discovery_complete = false;
                g_config_service_found = false;
                g_discovery_conn_handle = BLE_HS_CONN_HANDLE_NONE;

                // Phase 2: Notify time_sync_task of peer disconnection (AD039)
                if (TIME_SYNC_IS_INITIALIZED()) {
                    esp_err_t err = time_sync_task_send_disconnection();
                    if (err == ESP_OK) {
                        ESP_LOGI(TAG, "Time sync disconnection notification sent");
                    } else {
                        ESP_LOGW(TAG, "Failed to send time sync disconnection: %s",
                                 esp_err_to_name(err));
                    }
                }

                // JPL compliance: Allow NimBLE to fully clean up connection handle
                // Measured reconnection timing from logs:
                //   - Immediate retry (2s after disconnect) → BLE_ERR_UNK_CONN_ID errors
                //   - Success after 46 seconds (NimBLE finished cleanup)
                // Solution: 2-second delay prevents immediate retry errors
                vTaskDelay(pdMS_TO_TICKS(2000));

                // CRITICAL FIX (Phase 6m): Stop advertising first, then restart for peer rediscovery
                // After Phase 1b.2, SERVER continues advertising after peer connection (for mobile app).
                // When peer disconnects, advertising might still be active → must stop first before restart.
                // Stop advertising if active (ignore errors - advertising might already be stopped)
                if (ble_gap_adv_active()) {
                    ble_gap_adv_stop();
                    ESP_LOGI(TAG, "Stopped existing advertising before restart");
                }

                // Now restart advertising + scanning for peer rediscovery
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
                    // Sync flag with actual NimBLE state
                    adv_state.advertising_active = ble_gap_adv_active();
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
                adv_state.notify_client_battery_subscribed = false;

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

                // BUG FIX: Restart advertising for unknown disconnections (mobile app fallback)
                // This handles cases where connection wasn't properly registered due to race conditions
                // or timing issues during connection establishment
                ESP_LOGI(TAG, "Restarting advertising after unknown disconnect (mobile app fallback)");

                vTaskDelay(pdMS_TO_TICKS(100));  // Brief delay for BLE stack cleanup

                rc = ble_gap_adv_start(BLE_OWN_ADDR_PUBLIC, NULL, BLE_HS_FOREVER,
                                       &adv_params, ble_gap_event, NULL);
                if (rc == 0) {
                    adv_state.advertising_active = true;
                    adv_state.advertising_start_ms = (uint32_t)(esp_timer_get_time() / 1000);
                    ESP_LOGI(TAG, "Advertising restarted successfully");
                } else if (rc == BLE_HS_EALREADY) {
                    ESP_LOGI(TAG, "Advertising already active");
                    adv_state.advertising_active = ble_gap_adv_active();
                } else {
                    ESP_LOGE(TAG, "Failed to restart advertising; rc=%d", rc);
                    adv_state.advertising_active = ble_gap_adv_active();
                }

                // Stop scanning if active (mobile app doesn't need peer discovery)
                if (scanning_active) {
                    int scan_rc = ble_gap_disc_cancel();
                    if (scan_rc == 0 || scan_rc == BLE_HS_EALREADY) {
                        scanning_active = false;
                        ESP_LOGI(TAG, "Scanning stopped (mobile app fallback)");
                    }
                }
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
            ESP_LOGI(TAG, "BLE MTU exchange: %u bytes (conn_handle=%d)",
                     event->mtu.value, event->mtu.conn_handle);
            // Phase 6f: MTU negotiation complete - 28-byte beacons should work now
            // GATT discovery runs in parallel (started in connection handler)
            // AD040: Firmware version exchange happens after GATT discovery completes
            // (when coordination characteristic handle is discovered)
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

            // Client Battery subscription handling (Phase 6 - dual-device mode)
            if (ble_gatts_find_chr(&uuid_config_service.u, &uuid_char_client_battery.u, NULL, &val_handle) == 0) {
                if (event->subscribe.attr_handle == val_handle) {
                    adv_state.notify_client_battery_subscribed = event->subscribe.cur_notify;
                    ESP_LOGI(TAG, "Client Battery notifications %s", event->subscribe.cur_notify ? "enabled" : "disabled");

                    // Send initial value immediately on subscription
                    if (event->subscribe.cur_notify) {
                        uint8_t current_client_battery;
                        // JPL compliance: Bounded mutex wait with timeout error handling
                        if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
                            ESP_LOGE(TAG, "Mutex timeout in GAP event handler (client battery notify) - possible deadlock");
                            return 0;
                        }
                        current_client_battery = char_data.client_battery_level;
                        xSemaphoreGive(char_data_mutex);

                        struct os_mbuf *om = ble_hs_mbuf_from_flat(&current_client_battery, sizeof(current_client_battery));
                        if (om != NULL) {
                            int rc = ble_gatts_notify_custom(adv_state.conn_handle, val_handle, om);
                            if (rc == 0) {
                                ESP_LOGI(TAG, "Initial client battery level sent: %u%%", current_client_battery);
                            }
                        }
                    }
                }
            }
            break;

        case BLE_GAP_EVENT_NOTIFY_RX: {
            // BLE notification received from peer (Phase 2 - AD039 Time Sync)
            // This handler processes incoming sync beacons sent by SERVER device

            ESP_LOGD(TAG, "BLE notification received: attr_handle=%u, indication=%d",
                     event->notify_rx.attr_handle,
                     event->notify_rx.indication);

            // Phase 3a: Handle configuration characteristic notifications (notification-based sync)
            // When SERVER writes a config value, it sends notification. CLIENT receives it here and updates char_data.

            // Custom Frequency notification
            if (event->notify_rx.attr_handle == g_peer_freq_val_handle) {
                uint16_t freq_val;
                if (ble_hs_mbuf_to_flat(event->notify_rx.om, &freq_val, sizeof(freq_val), NULL) == 0) {
                    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) == pdTRUE) {
                        char_data.custom_frequency_hz = freq_val;
                        xSemaphoreGive(char_data_mutex);
                        ble_callback_params_updated();
                        ESP_LOGI(TAG, "CLIENT: Frequency notification received: %.2f Hz", freq_val / 100.0f);
                    }
                }
                break;
            }

            // Custom Duty Cycle notification
            if (event->notify_rx.attr_handle == g_peer_duty_val_handle) {
                uint8_t duty_val;
                if (ble_hs_mbuf_to_flat(event->notify_rx.om, &duty_val, sizeof(duty_val), NULL) == 0) {
                    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) == pdTRUE) {
                        char_data.custom_duty_percent = duty_val;
                        xSemaphoreGive(char_data_mutex);
                        ble_callback_params_updated();
                        ESP_LOGI(TAG, "CLIENT: Duty cycle notification received: %u%%", duty_val);
                    }
                }
                break;
            }

            // Note: Mode 0-4 intensity notifications removed - now handled via SYNC_MSG_SETTINGS

            // LED Enable notification
            if (event->notify_rx.attr_handle == g_peer_led_enable_val_handle) {
                uint8_t enabled;
                if (ble_hs_mbuf_to_flat(event->notify_rx.om, &enabled, sizeof(enabled), NULL) == 0) {
                    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) == pdTRUE) {
                        char_data.led_enable = enabled;
                        xSemaphoreGive(char_data_mutex);
                        ble_callback_params_updated();
                        ESP_LOGI(TAG, "CLIENT: LED enable notification received: %d", enabled);
                    }
                }
                break;
            }

            // LED Color Mode notification
            if (event->notify_rx.attr_handle == g_peer_led_color_mode_val_handle) {
                uint8_t mode;
                if (ble_hs_mbuf_to_flat(event->notify_rx.om, &mode, sizeof(mode), NULL) == 0) {
                    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) == pdTRUE) {
                        char_data.led_color_mode = mode;
                        xSemaphoreGive(char_data_mutex);
                        ble_callback_params_updated();
                        ESP_LOGI(TAG, "CLIENT: LED color mode notification received: %u (%s)",
                                 mode, mode == 0 ? "palette" : "custom RGB");
                    }
                }
                break;
            }

            // LED Palette notification
            if (event->notify_rx.attr_handle == g_peer_led_palette_val_handle) {
                uint8_t palette_idx;
                if (ble_hs_mbuf_to_flat(event->notify_rx.om, &palette_idx, sizeof(palette_idx), NULL) == 0) {
                    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) == pdTRUE) {
                        char_data.led_palette_index = palette_idx;
                        xSemaphoreGive(char_data_mutex);
                        ble_callback_params_updated();
                        ESP_LOGI(TAG, "CLIENT: LED palette notification received: %u (%s)",
                                 palette_idx, color_palette[palette_idx].name);
                    }
                }
                break;
            }

            // LED Custom RGB notification
            if (event->notify_rx.attr_handle == g_peer_led_custom_rgb_val_handle) {
                uint8_t rgb[3];
                if (ble_hs_mbuf_to_flat(event->notify_rx.om, rgb, sizeof(rgb), NULL) == 0) {
                    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) == pdTRUE) {
                        char_data.led_custom_r = rgb[0];
                        char_data.led_custom_g = rgb[1];
                        char_data.led_custom_b = rgb[2];
                        xSemaphoreGive(char_data_mutex);
                        ble_callback_params_updated();
                        ESP_LOGI(TAG, "CLIENT: LED custom RGB notification received: (%u, %u, %u)",
                                 rgb[0], rgb[1], rgb[2]);
                    }
                }
                break;
            }

            // LED Brightness notification
            if (event->notify_rx.attr_handle == g_peer_led_brightness_val_handle) {
                uint8_t brightness;
                if (ble_hs_mbuf_to_flat(event->notify_rx.om, &brightness, sizeof(brightness), NULL) == 0) {
                    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) == pdTRUE) {
                        char_data.led_brightness = brightness;
                        xSemaphoreGive(char_data_mutex);
                        ble_callback_params_updated();
                        ESP_LOGI(TAG, "CLIENT: LED brightness notification received: %u%%", brightness);
                    }
                }
                break;
            }

            // Note: Time sync beacon handler removed (v0.7.10) - beacons now via ESP-NOW
            // Unhandled notification - log for debugging
            ESP_LOGD(TAG, "Notification from unknown characteristic handle=%u",
                     event->notify_rx.attr_handle);
            break;
        }

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

    // Check connection states
    bool peer_bonded = ble_check_bonded_peer_exists();
    bool peer_connected = ble_is_peer_connected();
    bool app_connected = ble_is_app_connected();

    // Bug #45: If PWA (app) is actively connected, ALWAYS advertise Config UUID
    // This prevents UUID switching during peer reconnection from disrupting PWA connection
    if (app_connected) {
        return &uuid_config_service;
    }

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
// ADVERTISING & SCAN RESPONSE UPDATE HELPERS
// ============================================================================

/**
 * @brief Update advertising data with battery Service Data
 *
 * Bug #44: Battery extraction failure - advertising vs scan response data
 * BLE discovery events only contain advertising data, not scan response data
 * Solution: Add battery to advertising packet (visible to scanners during discovery)
 *
 * Advertising packet contents:
 * - Flags (3 bytes)
 * - TX power (3 bytes)
 * - Device name (~12 bytes)
 * - Battery Service Data (3 bytes, only during Bilateral UUID window)
 * Total: ~21 bytes (fits in 31-byte BLE advertising packet limit)
 */
static void ble_update_advertising_data(void) {
    struct ble_hs_adv_fields fields;
    memset(&fields, 0, sizeof(fields));

    // Standard advertising fields
    fields.flags = BLE_HS_ADV_F_DISC_GEN | BLE_HS_ADV_F_BREDR_UNSUP;
    fields.tx_pwr_lvl_is_present = 1;
    fields.tx_pwr_lvl = BLE_HS_ADV_TX_PWR_LVL_AUTO;

    fields.name = (uint8_t *)ble_svc_gap_device_name();
    fields.name_len = strlen((char *)fields.name);
    fields.name_is_complete = 1;

    // AD035: Add battery level as Service Data for role assignment
    // Battery Service UUID (0x180F) + battery percentage (0-100)
    // Bug #45 fix: Always broadcast battery (not just during Bilateral UUID window)
    // After Bug #9 switched to Config UUID for PWA discovery, battery was never included
    static uint8_t battery_svc_data[3];

    // Read battery level (mutex-protected)
    uint8_t battery_pct = 0;
    if (xSemaphoreTake(bilateral_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) == pdTRUE) {
        battery_pct = bilateral_data.battery_level;
        xSemaphoreGive(bilateral_data_mutex);
    }

    battery_svc_data[0] = 0x0F;  // Battery Service UUID LSB (0x180F)
    battery_svc_data[1] = 0x18;  // Battery Service UUID MSB
    battery_svc_data[2] = battery_pct;  // Battery percentage 0-100

    fields.svc_data_uuid16 = battery_svc_data;
    fields.svc_data_uuid16_len = 3;

    ESP_LOGD(TAG, "Advertising battery level: %d%% (for role assignment)", battery_pct);

    int rc = ble_gap_adv_set_fields(&fields);
    if (rc != 0) {
        ESP_LOGE(TAG, "Failed to update advertising data; rc=%d", rc);
    }
}

/**
 * @brief Update scan response with dynamic UUID
 *
 * UUID switches based on timing and bonding state:
 * - 0-30s: Bilateral Service UUID (0x0100) - peer discovery only
 * - 30s+: Configuration Service UUID (0x0200) - app discovery + bonded peer reconnect
 *
 * Scan response packet contents:
 * - 128-bit UUID (17 bytes)
 * Total: ~17 bytes (fits in 31-byte BLE scan response packet limit)
 */
static void ble_update_scan_response(void) {
    struct ble_hs_adv_fields rsp_fields;
    memset(&rsp_fields, 0, sizeof(rsp_fields));

    // Get current UUID based on timing and bonding state
    const ble_uuid128_t *advertised_uuid = ble_get_advertised_uuid();
    rsp_fields.uuids128 = advertised_uuid;
    rsp_fields.num_uuids128 = 1;
    rsp_fields.uuids128_is_complete = 1;

    int rc = ble_gap_adv_rsp_set_fields(&rsp_fields);
    if (rc != 0) {
        ESP_LOGE(TAG, "Failed to update scan response UUID; rc=%d", rc);
    } else {
        ESP_LOGI(TAG, "Scan response UUID updated: %s",
                 (advertised_uuid == &uuid_bilateral_service) ? "Bilateral (peer discovery)" : "Config (app + bonded peer)");
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

    // Set maximum TX power (+9 dBm) to compensate for nylon case and body attenuation
    // Default is +3 dBm, which gives weak RSSI (-98 dBm) in real-world use
    esp_err_t err;

    // Set advertising TX power (when device is discoverable)
    err = esp_ble_tx_power_set_enhanced(ESP_BLE_ENHANCED_PWR_TYPE_ADV, 0, ESP_PWR_LVL_P9);
    if (err != ESP_OK) {
        ESP_LOGW(TAG, "Failed to set ADV TX power to +9dBm: %s", esp_err_to_name(err));
    }

    // Set scan TX power (when device is scanning for peers)
    err = esp_ble_tx_power_set_enhanced(ESP_BLE_ENHANCED_PWR_TYPE_SCAN, 0, ESP_PWR_LVL_P9);
    if (err != ESP_OK) {
        ESP_LOGW(TAG, "Failed to set SCAN TX power to +9dBm: %s", esp_err_to_name(err));
    }

    // Set default TX power (for connections)
    err = esp_ble_tx_power_set_enhanced(ESP_BLE_ENHANCED_PWR_TYPE_DEFAULT, 0, ESP_PWR_LVL_P9);
    if (err != ESP_OK) {
        ESP_LOGW(TAG, "Failed to set DEFAULT TX power to +9dBm: %s", esp_err_to_name(err));
    } else {
        ESP_LOGI(TAG, "BLE TX power set to maximum (+9 dBm) for ADV/SCAN/CONN");
    }

    // Bug #48 Fix: Initialize battery data before first advertising update
    // This ensures battery is available for role assignment before devices connect
    if (xSemaphoreTake(bilateral_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) == pdTRUE) {
        bilateral_data.battery_level = g_initial_battery_pct;
        xSemaphoreGive(bilateral_data_mutex);
    } else {
        ESP_LOGW(TAG, "Failed to acquire bilateral_data_mutex for battery init");
    }

    // Bug #44: Configure advertising and scan response dynamically
    // - Advertising data: flags, name, battery Service Data (updated via ble_update_advertising_data)
    // - Scan response: UUID (dynamic switching via ble_update_scan_response)
    ble_update_advertising_data();  // Set initial advertising data with battery (Bug #48: now includes pre-cached battery)

    // Initialize scan response (will be updated dynamically)
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
    nvs_set_u8(nvs_handle, NVS_KEY_MODE0_INTENSITY, char_data.mode0_intensity);
    nvs_set_u8(nvs_handle, NVS_KEY_MODE1_INTENSITY, char_data.mode1_intensity);
    nvs_set_u8(nvs_handle, NVS_KEY_MODE2_INTENSITY, char_data.mode2_intensity);
    nvs_set_u8(nvs_handle, NVS_KEY_MODE3_INTENSITY, char_data.mode3_intensity);
    nvs_set_u8(nvs_handle, NVS_KEY_MODE4_INTENSITY, char_data.mode4_intensity);
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
    uint8_t duty, led_en, led_cmode, led_pal, r, g, b, led_bri;
    uint8_t m0_int, m1_int, m2_int, m3_int, m4_int;
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

    if (nvs_get_u8(nvs_handle, NVS_KEY_MODE0_INTENSITY, &m0_int) == ESP_OK) {
        char_data.mode0_intensity = m0_int;
    }

    if (nvs_get_u8(nvs_handle, NVS_KEY_MODE1_INTENSITY, &m1_int) == ESP_OK) {
        char_data.mode1_intensity = m1_int;
    }

    if (nvs_get_u8(nvs_handle, NVS_KEY_MODE2_INTENSITY, &m2_int) == ESP_OK) {
        char_data.mode2_intensity = m2_int;
    }

    if (nvs_get_u8(nvs_handle, NVS_KEY_MODE3_INTENSITY, &m3_int) == ESP_OK) {
        char_data.mode3_intensity = m3_int;
    }

    if (nvs_get_u8(nvs_handle, NVS_KEY_MODE4_INTENSITY, &m4_int) == ESP_OK) {
        char_data.mode4_intensity = m4_int;
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

esp_err_t ble_manager_init(uint8_t initial_battery_pct) {
    esp_err_t ret;

    ESP_LOGI(TAG, "Initializing BLE manager (AD032)...");

    // Bug #48 Fix: Store initial battery for use in ble_on_sync()
    g_initial_battery_pct = initial_battery_pct;
    ESP_LOGI(TAG, "Initial battery cached: %u%% (for role assignment)", g_initial_battery_pct);

    // Initialize boot timestamp for UUID-switching (Phase 1b.3)
    ble_boot_time_ms = (uint32_t)(esp_timer_get_time() / 1000);
    ESP_LOGI(TAG, "BLE boot timestamp: %lu ms (30s pairing window)", ble_boot_time_ms);

    // AD032: Initialize firmware version string (immutable after this point)
    snprintf(local_firmware_version_str, sizeof(local_firmware_version_str),
             "v%d.%d.%d (%s)",
             FIRMWARE_VERSION_MAJOR, FIRMWARE_VERSION_MINOR, FIRMWARE_VERSION_PATCH,
             __DATE__);
    ESP_LOGI(TAG, "Firmware version: %s", local_firmware_version_str);

    // AD048: Initialize hardware info string (silicon revision + 802.11mc FTM capability)
    {
        esp_chip_info_t chip_info;
        esp_chip_info(&chip_info);

        const char *model_name = "Unknown";
        switch (chip_info.model) {
            case CHIP_ESP32:   model_name = "ESP32"; break;
            case CHIP_ESP32S2: model_name = "ESP32-S2"; break;
            case CHIP_ESP32S3: model_name = "ESP32-S3"; break;
            case CHIP_ESP32C3: model_name = "ESP32-C3"; break;
            case CHIP_ESP32C6: model_name = "ESP32-C6"; break;
            case CHIP_ESP32H2: model_name = "ESP32-H2"; break;
            default: break;
        }

        uint8_t rev_major = (chip_info.revision >> 8) & 0xFF;
        uint8_t rev_minor = chip_info.revision & 0xFF;

        // Determine FTM capability string
        const char *ftm_cap = "";
        if (chip_info.model == CHIP_ESP32C6) {
            bool ftm_full = (rev_major > 0) || (rev_major == 0 && rev_minor >= 2);
            ftm_cap = ftm_full ? " FTM:full" : " FTM:resp";
        }

        snprintf(local_hardware_info_str, sizeof(local_hardware_info_str),
                 "%s v%d.%d%s", model_name, rev_major, rev_minor, ftm_cap);
        ESP_LOGI(TAG, "Hardware info: %s", local_hardware_info_str);
    }

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

    // Phase 2: Create time sync beacon mutex (AD039)
    time_sync_beacon_mutex = xSemaphoreCreateMutex();
    if (time_sync_beacon_mutex == NULL) {
        ESP_LOGE(TAG, "Failed to create time_sync_beacon mutex");
        return ESP_FAIL;
    }

    // Bug #31 Fix: Create deferred discovery timer (avoids BLE_HS_EBUSY during GATT discovery)
    const esp_timer_create_args_t timer_args = {
        .callback = deferred_discovery_timer_cb,
        .arg = NULL,
        .name = "deferred_disc"
    };
    ret = esp_timer_create(&timer_args, &g_deferred_discovery_timer);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to create deferred discovery timer: %s", esp_err_to_name(ret));
        return ret;
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

#ifdef CONFIG_BT_NIMBLE_NVS_PERSIST
    // Production mode: Persistent bonding via NVS
    // CONFIG_BT_NIMBLE_NVS_PERSIST compiles NVS store backend and enables persistence
    // ble_store_util_status_rr callback triggers NVS writes when bonding keys are generated
    ble_hs_cfg.store_status_cb = ble_store_util_status_rr;
    ESP_LOGI(TAG, "BLE bonding enabled - pairing data will persist in NVS (CONFIG_BT_NIMBLE_NVS_PERSIST)");
#else
    // Test mode: RAM-only bonding (no NVS writes)
    // CONFIG_BT_NIMBLE_NVS_PERSIST disabled - NVS store backend not compiled
    // Setting store_status_cb to NULL ensures bonding data stays in RAM only
    // Bonding data is cleared on reboot, allowing unlimited pairing test cycles without flash wear
    ble_hs_cfg.store_status_cb = NULL;
    ESP_LOGW(TAG, "BLE test mode - bonding data will NOT persist across reboots (RAM only)");
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

void ble_start_advertising(void) {
    ESP_LOGI(TAG, "ble_start_advertising() called (current state: advertising_active=%s, connected=%s)",
             adv_state.advertising_active ? "YES" : "NO",
             ble_is_app_connected() ? "YES" : "NO");

    if (!adv_state.advertising_active) {
        // Bug #44: Update BOTH advertising data (with battery) and scan response (with UUID)
        ble_update_advertising_data();  // Battery in advertising data (visible to scanners)
        ble_update_scan_response();     // UUID in scan response (dynamic switching)

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

void ble_reset_pairing_window(void) {
    // Reset boot timestamp to restart 30-second pairing window
    // This makes ble_get_advertised_uuid() return Bilateral UUID again
    ble_boot_time_ms = (uint32_t)(esp_timer_get_time() / 1000);
    ESP_LOGI(TAG, "Pairing window reset (new boot time: %lu ms)", ble_boot_time_ms);

    // Clear ONLY discovery flags for fresh pairing attempt
    // PRESERVE peer_addr and role for reconnection to same device with same role
    peer_state.peer_discovered = false;
    peer_state.peer_battery_known = false;
    peer_state.peer_battery_level = 0;
    // NOTE: peer_addr preserved for reconnection logic
    // NOTE: role preserved for time sync continuity (SERVER/CLIENT relationship)

    // Bug #45: Reset pairing window flag to allow new peer pairing
    peer_pairing_window_closed = false;

    ESP_LOGI(TAG, "Pairing window reset (address and role preserved for reconnection)");
}

void ble_close_pairing_window(void) {
    // Bug #45: Close pairing window to prevent subsequent connections from being identified as peers
    // This handles early peer pairing (T=5s), 30s timeout, and simultaneous connection race conditions
    peer_pairing_window_closed = true;
    uint32_t now_ms = (uint32_t)(esp_timer_get_time() / 1000);
    uint32_t elapsed_ms = now_ms - ble_boot_time_ms;
    ESP_LOGI(TAG, "Pairing window closed at T=%lu ms (no new peer connections allowed)", elapsed_ms);
}

// ============================================================================
// Peer Discovery & Scanning (Phase 1a)
// ============================================================================

/**
 * @brief Cache battery level from advertising packet (Bug #61)
 *
 * BLE sends advertising data and scan response in separate events.
 * Battery Service Data is in advertising packet, UUID is in scan response.
 * We cache battery when we see it, then look it up when UUID match arrives.
 */
static void battery_cache_store(const ble_addr_t *addr, uint8_t battery_level) {
    uint32_t now_ms = (uint32_t)(esp_timer_get_time() / 1000);

    // Find existing entry or oldest entry to replace
    int oldest_idx = 0;
    uint32_t oldest_time = UINT32_MAX;

    for (int i = 0; i < BATTERY_CACHE_SIZE; i++) {
        // Check for existing entry with same address
        if (battery_cache[i].valid &&
            memcmp(battery_cache[i].addr.val, addr->val, 6) == 0) {
            // Update existing entry
            battery_cache[i].battery_level = battery_level;
            battery_cache[i].timestamp_ms = now_ms;
            ESP_LOGD(TAG, "Battery cache updated: %d%% for %02X:%02X:%02X:%02X:%02X:%02X",
                     battery_level, addr->val[5], addr->val[4], addr->val[3],
                     addr->val[2], addr->val[1], addr->val[0]);
            return;
        }

        // Track oldest entry for LRU replacement
        if (!battery_cache[i].valid || battery_cache[i].timestamp_ms < oldest_time) {
            oldest_time = battery_cache[i].valid ? battery_cache[i].timestamp_ms : 0;
            oldest_idx = i;
        }
    }

    // Store in oldest/invalid slot
    memcpy(battery_cache[oldest_idx].addr.val, addr->val, 6);
    battery_cache[oldest_idx].battery_level = battery_level;
    battery_cache[oldest_idx].timestamp_ms = now_ms;
    battery_cache[oldest_idx].valid = true;

    ESP_LOGD(TAG, "Battery cache stored: %d%% for %02X:%02X:%02X:%02X:%02X:%02X",
             battery_level, addr->val[5], addr->val[4], addr->val[3],
             addr->val[2], addr->val[1], addr->val[0]);
}

/**
 * @brief Look up cached battery level by address (Bug #61)
 *
 * @param addr Device address to look up
 * @param battery_level Output: battery percentage if found
 * @return true if found and not expired, false otherwise
 */
static bool battery_cache_lookup(const ble_addr_t *addr, uint8_t *battery_level) {
    uint32_t now_ms = (uint32_t)(esp_timer_get_time() / 1000);

    for (int i = 0; i < BATTERY_CACHE_SIZE; i++) {
        if (battery_cache[i].valid &&
            memcmp(battery_cache[i].addr.val, addr->val, 6) == 0) {
            // Check TTL
            if ((now_ms - battery_cache[i].timestamp_ms) > BATTERY_CACHE_TTL_MS) {
                // Entry expired
                battery_cache[i].valid = false;
                return false;
            }

            *battery_level = battery_cache[i].battery_level;
            ESP_LOGI(TAG, "Battery cache hit: %d%% for %02X:%02X:%02X:%02X:%02X:%02X",
                     *battery_level, addr->val[5], addr->val[4], addr->val[3],
                     addr->val[2], addr->val[1], addr->val[0]);
            return true;
        }
    }

    return false;  // Not found
}

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

            // Bug #61: Cache battery data from advertising packet for later lookup
            // BLE sends advertising data (with battery) and scan response (with UUID) separately
            if (fields.svc_data_uuid16 != NULL && fields.svc_data_uuid16_len >= 3) {
                uint16_t svc_uuid = (fields.svc_data_uuid16[1] << 8) | fields.svc_data_uuid16[0];
                if (svc_uuid == 0x180F) {  // Battery Service UUID
                    battery_cache_store(&event->disc.addr, fields.svc_data_uuid16[2]);
                }
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
                        if (ble_is_peer_connected() || peer_state.peer_discovered) {
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
                        // Bug #61: Check current packet first, then fall back to cache
                        if (fields.svc_data_uuid16 != NULL && fields.svc_data_uuid16_len >= 3) {
                            uint16_t svc_uuid = (fields.svc_data_uuid16[1] << 8) | fields.svc_data_uuid16[0];
                            if (svc_uuid == 0x180F) {  // Battery Service UUID
                                peer_state.peer_battery_level = fields.svc_data_uuid16[2];
                                peer_state.peer_battery_known = true;
                                ESP_LOGI(TAG, "Peer battery: %d%% (from current packet)",
                                         peer_state.peer_battery_level);
                            }
                        }

                        // Bug #61: If battery not in current packet (scan response), check cache
                        // Battery was in advertising packet, UUID is in scan response - different events
                        if (!peer_state.peer_battery_known) {
                            uint8_t cached_battery;
                            if (battery_cache_lookup(&event->disc.addr, &cached_battery)) {
                                peer_state.peer_battery_level = cached_battery;
                                peer_state.peer_battery_known = true;
                                ESP_LOGI(TAG, "Peer battery: %d%% (from cache)", cached_battery);
                            }
                        }

                        // Phase 6n: Preserve roles for mid-session reconnection
                        // Only use battery-based assignment for FRESH PAIRING (role == PEER_ROLE_NONE)
                        // For reconnection, preserve existing role from previous session
                        if (peer_state.role != PEER_ROLE_NONE) {
                            // RECONNECTION: Preserve existing role
                            ESP_LOGI(TAG, "Reconnection detected - preserving role from previous session (%s)",
                                     peer_state.role == PEER_ROLE_SERVER ? "SERVER" : "CLIENT");

                            if (peer_state.role == PEER_ROLE_SERVER) {
                                // We were SERVER before - initiate connection again
                                ESP_LOGI(TAG, "Previous SERVER - initiating reconnection");

                                // Stop scanning before connection attempt
                                ble_gap_disc_cancel();

                                ble_connect_to_peer();
                            } else {
                                // We were CLIENT before - wait for SERVER to reconnect
                                ESP_LOGI(TAG, "Previous CLIENT - waiting for SERVER to reconnect");

                                // Bug #38: KEEP ADVERTISING - SERVER needs to discover us!
                                ESP_LOGI(TAG, "Continuing advertising + scanning - waiting for SERVER connection");
                            }
                        } else if (peer_state.peer_battery_known) {
                            // FRESH PAIRING: Use battery-based role assignment
                            // Higher battery device initiates connection (becomes SERVER/MASTER)
                            // Lower battery device waits (becomes CLIENT/SLAVE)
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

                                // Stop scanning before connection attempt
                                ble_gap_disc_cancel();

                                ble_connect_to_peer();
                            } else if (local_battery < peer_state.peer_battery_level) {
                                // Peer has higher battery - wait for peer to connect (CLIENT/SLAVE)
                                ESP_LOGI(TAG, "Lower battery (%d%% < %d%%) - waiting as CLIENT",
                                         local_battery, peer_state.peer_battery_level);

                                // Bug #38: KEEP ADVERTISING - higher-battery device needs to discover us!
                                // Only stop calling ble_gap_connect() (wait for peer to connect to us)
                                ESP_LOGI(TAG, "Continuing advertising + scanning - waiting for peer connection");
                                // Don't call ble_connect_to_peer() - peer will connect to us
                            } else {
                                // Batteries equal - use MAC address tie-breaker
                                // Lower MAC address initiates connection

                                // BUG FIX: Compare OUR MAC to PEER's MAC (not peer to peer!)
                                ble_addr_t own_addr;
                                ble_hs_id_copy_addr(BLE_ADDR_PUBLIC, own_addr.val, NULL);

                                // Bug #37: MAC addresses stored in reverse byte order (LSB first)
                                // Must compare from MSB to LSB (index 5 down to 0)
                                bool we_are_lower = false;
                                for (int j = 5; j >= 0; j--) {
                                    if (own_addr.val[j] < event->disc.addr.val[j]) {
                                        we_are_lower = true;   // We are lower, we initiate
                                        break;
                                    } else if (own_addr.val[j] > event->disc.addr.val[j]) {
                                        we_are_lower = false;  // Peer is lower, they initiate
                                        break;
                                    }
                                }

                                if (we_are_lower) {
                                    ESP_LOGI(TAG, "Equal battery (%d%%), lower MAC - initiating as SERVER",
                                             local_battery);

                                    // Stop scanning before connection attempt
                                    ble_gap_disc_cancel();

                                    ble_connect_to_peer();
                                } else {
                                    ESP_LOGI(TAG, "Equal battery (%d%%), higher MAC - waiting as CLIENT",
                                             local_battery);

                                    // Bug #38: KEEP ADVERTISING - lower-MAC device needs to discover us!
                                    ESP_LOGI(TAG, "Continuing advertising + scanning - waiting for peer connection");
                                }
                            }
                        } else {
                            // No battery data - fall back to connection-initiator logic (AD010)
                            ESP_LOGW(TAG, "No peer battery data - falling back to discovery-based role");

                            // Stop scanning before connection attempt
                            ble_gap_disc_cancel();

                            ble_connect_to_peer();
                        }

                        return 0;
                    }

                    // Phase 6: Check for Config UUID (peer reconnection after initial pairing)
                    // After 30s, devices advertise Config UUID instead of Bilateral UUID
                    // Reconnection requires address match with previously-known peer
                    if (ble_uuid_cmp(&fields.uuids128[i].u, &uuid_config_service.u) == 0) {
                        // Only attempt reconnection if we have a cached peer address
                        // (peer_addr is preserved across disconnect, peer_discovered is cleared)
                        static const ble_addr_t zero_addr = {0};
                        if (memcmp(&peer_state.peer_addr, &zero_addr, sizeof(ble_addr_t)) != 0) {
                            // Check if this is our previously-bonded peer
                            if (memcmp(&event->disc.addr, &peer_state.peer_addr, sizeof(ble_addr_t)) == 0) {
                                // Check if already reconnecting or connected
                                if (ble_is_peer_connected() || peer_state.peer_discovered) {
                                    ESP_LOGD(TAG, "Already reconnecting/connected to peer");
                                    break;
                                }

                                char addr_str[18];
                                snprintf(addr_str, sizeof(addr_str), "%02x:%02x:%02x:%02x:%02x:%02x",
                                        event->disc.addr.val[5], event->disc.addr.val[4],
                                        event->disc.addr.val[3], event->disc.addr.val[2],
                                        event->disc.addr.val[1], event->disc.addr.val[0]);

                                ESP_LOGI(TAG, "Peer RECONNECT discovered: %s (RSSI: %d, prev_role: %s)",
                                         addr_str, event->disc.rssi,
                                         peer_state.role == PEER_ROLE_SERVER ? "SERVER" :
                                         peer_state.role == PEER_ROLE_CLIENT ? "CLIENT" : "NONE");
                                peer_state.peer_discovered = true;

                                // Mid-session reconnect: Use preserved role from before disconnect
                                // Previous SERVER initiates, previous CLIENT waits
                                // This avoids battery comparison race condition
                                if (peer_state.role == PEER_ROLE_SERVER) {
                                    // We were SERVER - we initiate reconnection
                                    ESP_LOGI(TAG, "Peer reconnect: initiating (was SERVER)");
                                    ble_gap_disc_cancel();
                                    ble_connect_to_peer();
                                } else if (peer_state.role == PEER_ROLE_CLIENT) {
                                    // We were CLIENT - wait for peer (SERVER) to connect to us
                                    ESP_LOGI(TAG, "Peer reconnect: waiting (was CLIENT)");
                                    // Keep scanning - peer (SERVER) should connect to us
                                } else {
                                    // No previous role (fresh pairing) - use battery comparison
                                    uint8_t local_battery = 0;
                                    if (xSemaphoreTake(bilateral_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) == pdTRUE) {
                                        local_battery = bilateral_data.battery_level;
                                        xSemaphoreGive(bilateral_data_mutex);
                                    }
                                    if (local_battery >= peer_state.peer_battery_level || !peer_state.peer_battery_known) {
                                        ESP_LOGI(TAG, "Peer reconnect: initiating (higher battery)");
                                        ble_gap_disc_cancel();
                                        ble_connect_to_peer();
                                    } else {
                                        ESP_LOGI(TAG, "Peer reconnect: waiting (lower battery)");
                                    }
                                }

                                return 0;
                            }
                        }
                    }
                }
            }
            break;
        }

        case BLE_GAP_EVENT_DISC_COMPLETE:
            ESP_LOGI(TAG, "BLE scan complete");
            scanning_active = false;

            // If no peer found, restart scanning (continuous discovery)
            if (!peer_state.peer_discovered && !ble_is_peer_connected()) {
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

    if (ble_is_peer_connected()) {
        ESP_LOGW(TAG, "Already connected to peer, skipping scan");
        return;
    }

    // Get MAC address for scan interval jitter
    ble_addr_t own_addr;
    ble_hs_id_copy_addr(BLE_ADDR_PUBLIC, own_addr.val, NULL);

    // Add MAC-based jitter to scan interval to prevent synchronization races
    // Base: 0x10 (10ms) + jitter: 0-15 units (0-9.375ms) based on MAC last byte
    // Result: Each device scans at 10-19.375ms intervals (imperceptible to humans)
    // This desynchronizes devices over time, improving discovery
    uint16_t mac_jitter = own_addr.val[5] & 0x0F;  // Last byte, lower nibble (0-15)
    uint16_t scan_interval = 0x10 + mac_jitter;    // 16-31 units (10-19.375ms)

    // Configure scan parameters
    struct ble_gap_disc_params disc_params = {
        .itvl = scan_interval,  // MAC-based interval: 10-19.375ms (prevents sync races)
        .window = 0x10,         // Scan window: 10ms (same for all devices)
        .filter_policy = BLE_HCI_SCAN_FILT_NO_WL,  // No whitelist filtering
        .limited = 0,           // General discovery (not limited)
        .passive = 0,           // Active scanning (request scan responses)
        .filter_duplicates = 1  // Filter duplicate advertisements
    };

    int rc = ble_gap_disc(BLE_OWN_ADDR_PUBLIC, BLE_HS_FOREVER, &disc_params,
                          ble_gap_scan_event, NULL);

    if (rc == 0) {
        scanning_active = true;
        ESP_LOGI(TAG, "BLE scanning started (interval=%ums, jitter=+%ums, MAC=...%02X)",
                 scan_interval * 625 / 1000, mac_jitter * 625 / 1000, own_addr.val[5]);
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

    if (ble_is_peer_connected()) {
        ESP_LOGW(TAG, "Already connected to peer");
        return;
    }

    // Bug #45: Add MAC-based connection delay jitter to prevent simultaneous connection race
    // When both devices discover each other at the same time, both try to connect simultaneously
    // This causes BLE_ERR_UNK_CONN_ID (Unknown Connection Identifier) timeout
    // Solution: Add small random delay (0-5ms) before connection based on MAC address
    ble_addr_t own_addr;
    ble_hs_id_copy_addr(BLE_ADDR_PUBLIC, own_addr.val, NULL);
    uint8_t mac_jitter = own_addr.val[5] & 0x07;  // 0-7 from last MAC byte (half of scan jitter)
    uint32_t delay_ms = mac_jitter;  // 0-7ms delay

    if (delay_ms > 0) {
        ESP_LOGI(TAG, "Connection delay jitter: %ums (MAC-based)", delay_ms);
        vTaskDelay(pdMS_TO_TICKS(delay_ms));
    }

    ESP_LOGI(TAG, "Connecting to peer device...");

    // Phase 6p: Use custom connection parameters for long therapeutic sessions
    // 32-second supervision timeout (BLE spec max) prevents disconnects during normal use
    int rc = ble_gap_connect(BLE_OWN_ADDR_PUBLIC, &peer_state.peer_addr,
                             30000,  // 30 second timeout
                             &therapeutic_conn_params,  // Custom parameters (32s supervision timeout)
                             ble_gap_event, NULL);

    if (rc != 0) {
        ESP_LOGE(TAG, "Failed to connect to peer; rc=%d", rc);

        // BLE_ERR_ACL_CONN_EXISTS (523) means the peer successfully initiated connection to us
        // This is normal during simultaneous discovery - connection event will fire on both sides
        if (rc == 523) {  // 523 = BLE_ERR_ACL_CONN_EXISTS
            ESP_LOGI(TAG, "Peer is connecting to us (ACL already exists) - connection event will determine role");
            // Don't reset peer_discovered - connection is already in progress
        } else {
            // Actual connection failure - reset discovery flag to allow retry
            ESP_LOGW(TAG, "Connection failed (rc=%d) - will retry discovery", rc);
            peer_state.peer_discovered = false;
        }
    }
}

// ============================================================================
// Status Query Functions
// ============================================================================

bool ble_is_connected(void) {
    return ble_is_app_connected();
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
    // Use NimBLE API as source of truth (no state drift)
    if (peer_state.peer_conn_handle == BLE_HS_CONN_HANDLE_NONE) {
        return false;
    }

    struct ble_gap_conn_desc desc;
    return (ble_gap_conn_find(peer_state.peer_conn_handle, &desc) == 0);
}

bool ble_check_and_clear_freq_change_pending(uint32_t debounce_ms) {
    // Bug #95: Check if frequency change has settled (debounce expired)
    if (!freq_change_pending) {
        return false;
    }

    uint32_t now_ms = (uint32_t)(esp_timer_get_time() / 1000);
    uint32_t elapsed = now_ms - freq_change_timestamp_ms;

    if (elapsed >= debounce_ms) {
        // Debounce expired - clear flag and return true to trigger mode change
        freq_change_pending = false;
        ESP_LOGI(TAG, "Frequency change debounce complete (elapsed=%lu ms) - triggering sync", elapsed);
        return true;
    }

    // Still within debounce window
    return false;
}

static bool ble_is_app_connected(void) {
    // Use NimBLE API as source of truth (no state drift)
    if (adv_state.conn_handle == BLE_HS_CONN_HANDLE_NONE) {
        return false;
    }

    struct ble_gap_conn_desc desc;
    return (ble_gap_conn_find(adv_state.conn_handle, &desc) == 0);
}

const char* ble_get_connection_type_str(void) {
    if (ble_is_peer_connected()) {
        // Show role (Phase 1c Step 5: Log assigned role)
        if (peer_state.role == PEER_ROLE_CLIENT) {
            return "Peer (CLIENT)";
        } else if (peer_state.role == PEER_ROLE_SERVER) {
            return "Peer (SERVER)";
        } else {
            return "Peer";  // Role not yet assigned
        }
    } else if (ble_is_app_connected()) {
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

esp_err_t ble_disconnect_peer(uint8_t reason) {
    uint16_t handle = peer_state.peer_conn_handle;
    if (handle == BLE_HS_CONN_HANDLE_NONE) {
        ESP_LOGW(TAG, "ble_disconnect_peer: No peer connected");
        return ESP_ERR_INVALID_STATE;
    }

    ESP_LOGI(TAG, "Disconnecting peer (handle=%d, reason=0x%02X)", handle, reason);
    int rc = ble_gap_terminate(handle, reason);
    if (rc != 0) {
        ESP_LOGE(TAG, "ble_gap_terminate failed: rc=%d", rc);
        return ESP_FAIL;
    }
    return ESP_OK;
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
    if (ble_is_app_connected() && adv_state.notify_battery_subscribed) {
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

void ble_update_client_battery_level(uint8_t percentage) {
    // JPL compliance: Bounded mutex wait with timeout error handling
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in ble_update_client_battery_level - possible deadlock");
        return;  // Early return on timeout
    }
    char_data.client_battery_level = percentage;
    xSemaphoreGive(char_data_mutex);

    ESP_LOGI(TAG, "Client battery updated: %u%%", percentage);

    // Send notification if client subscribed
    if (ble_is_app_connected() && adv_state.notify_client_battery_subscribed) {
        uint16_t val_handle;
        if (ble_gatts_find_chr(&uuid_config_service.u, &uuid_char_client_battery.u, NULL, &val_handle) == 0) {
            struct os_mbuf *om = ble_hs_mbuf_from_flat(&percentage, sizeof(percentage));
            if (om != NULL) {
                int rc = ble_gatts_notify_custom(adv_state.conn_handle, val_handle, om);
                if (rc != 0) {
                    ESP_LOGD(TAG, "Client battery notify failed: rc=%d", rc);
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

// ============================================================================
// AD048: LTK-BASED ESP-NOW KEY DERIVATION
// ============================================================================

esp_err_t ble_get_peer_ltk(uint8_t ltk_out[16]) {
    if (ltk_out == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    // Must have peer connected
    if (!ble_is_peer_connected()) {
        ESP_LOGD(TAG, "ble_get_peer_ltk: No peer connected");
        return ESP_ERR_INVALID_STATE;
    }

    // Get peer address from connection state
    if (!peer_state.peer_discovered) {
        ESP_LOGW(TAG, "ble_get_peer_ltk: Peer discovered flag not set");
        return ESP_ERR_INVALID_STATE;
    }

    // Read LTK from NimBLE bond store
    // Use OUR_SEC because we want our local copy of the encryption keys
    // The LTK is the same on both devices after pairing
    union ble_store_key key;
    union ble_store_value value;

    memset(&key, 0, sizeof(key));
    key.sec.peer_addr = peer_state.peer_addr;

    int rc = ble_store_read(BLE_STORE_OBJ_TYPE_OUR_SEC, &key, &value);
    if (rc != 0) {
        ESP_LOGD(TAG, "ble_get_peer_ltk: ble_store_read failed (rc=%d)", rc);
        return ESP_ERR_NOT_FOUND;
    }

    // Check if LTK is present
    if (!value.sec.ltk_present) {
        ESP_LOGW(TAG, "ble_get_peer_ltk: LTK not present in bond data");
        return ESP_ERR_NOT_FOUND;
    }

    // Copy LTK to output
    memcpy(ltk_out, value.sec.ltk, 16);

    ESP_LOGI(TAG, "AD048: Retrieved peer LTK [%02X%02X...%02X%02X]",
             ltk_out[0], ltk_out[1], ltk_out[14], ltk_out[15]);

    return ESP_OK;
}

bool ble_peer_ltk_available(void) {
    if (!ble_is_peer_connected()) {
        return false;
    }

    if (!peer_state.peer_discovered) {
        return false;
    }

    // Check if we can read LTK from store
    union ble_store_key key;
    union ble_store_value value;

    memset(&key, 0, sizeof(key));
    key.sec.peer_addr = peer_state.peer_addr;

    int rc = ble_store_read(BLE_STORE_OBJ_TYPE_OUR_SEC, &key, &value);
    if (rc != 0) {
        return false;
    }

    return value.sec.ltk_present;
}

/**
 * @brief Send time sync beacon to peer device (SERVER only)
 *
 * Called periodically by motor task when time_sync_should_send_beacon() returns true.
 * Generates beacon from time sync module and sends via BLE notification to peer.
 *
 * Phase 2 (AD039): Hybrid time synchronization protocol
 *
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_STATE if not SERVER role or peer not connected
 * @return ESP_ERR_TIMEOUT if mutex timeout
 * @return ESP_FAIL if notification send failed
 */
esp_err_t ble_send_time_sync_beacon(void) {
    // Check if we're the SERVER
    if (time_sync_get_role() != TIME_SYNC_ROLE_SERVER) {
        ESP_LOGW(TAG, "Cannot send sync beacon: not SERVER role");
        return ESP_ERR_INVALID_STATE;
    }

    // Check if peer is connected
    uint16_t peer_conn_handle = ble_get_peer_conn_handle();
    if (peer_conn_handle == BLE_HS_CONN_HANDLE_NONE) {
        ESP_LOGD(TAG, "Cannot send sync beacon: peer not connected");
        return ESP_ERR_INVALID_STATE;
    }

    // Generate beacon from time sync module
    time_sync_beacon_t beacon;
    esp_err_t err = time_sync_generate_beacon(&beacon);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Failed to generate sync beacon: %s", esp_err_to_name(err));
        return err;
    }

    // Phase 6r (AD043): No RTT measurement - CLIENT uses one-way timestamp with filter

    // Check characteristic handle first (before mutex)
    if (g_time_sync_char_handle == 0) {
        ESP_LOGW(TAG, "Time sync characteristic handle not initialized");
        return ESP_ERR_INVALID_STATE;
    }

    // Hold mutex through entire critical section (update + send) for atomicity
    // This prevents GATT reads from getting stale data between update and send
    if (xSemaphoreTake(time_sync_beacon_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in ble_send_time_sync_beacon - possible deadlock");
        return ESP_ERR_TIMEOUT;
    }

    // Bug #76 (PTP Hardening): Update T1 timestamp as late as possible
    // This minimizes the gap between timestamp recording and actual RF transmission.
    // Original T1 was set in time_sync_generate_beacon() ~1-50ms earlier.
    time_sync_finalize_beacon_timestamp(&beacon);

    // UTLP Design: Time beacons use ESP-NOW broadcast ONLY
    // "Shout the time, don't care who hears" - no BLE fallback for timing
    // Broadcast eliminates ACK contention and always succeeds
    if (!espnow_transport_is_ready()) {
        ESP_LOGW(TAG, "ESP-NOW not ready - beacon skipped (UTLP: no BLE fallback for time)");
        xSemaphoreGive(time_sync_beacon_mutex);
        return ESP_ERR_INVALID_STATE;
    }

    esp_err_t espnow_err = espnow_transport_send_beacon(&beacon);
    if (espnow_err != ESP_OK) {
        ESP_LOGE(TAG, "ESP-NOW beacon broadcast failed: %s", esp_err_to_name(espnow_err));
        xSemaphoreGive(time_sync_beacon_mutex);
        return espnow_err;
    }

    // Only update global after successful send (while still holding mutex)
    g_time_sync_beacon = beacon;

    // Debug: Log beacon size and checksum
    ESP_LOGI(TAG, "Beacon sent: %u bytes, seq=%u, checksum=0x%04X [ESP-NOW]",
             (unsigned)sizeof(beacon), beacon.sequence, beacon.checksum);
    xSemaphoreGive(time_sync_beacon_mutex);

    ESP_LOGD(TAG, "Sync beacon sent to peer (seq=%u)", beacon.sequence);
    return ESP_OK;
}

// ============================================================================
// PHASE 3: COORDINATION API IMPLEMENTATION
// ============================================================================

coordination_mode_t ble_get_coordination_mode(void) {
    // Thread-safe read (atomic for enum)
    return g_coordination_mode;
}

void ble_set_coordination_mode(coordination_mode_t mode) {
    // Thread-safe write (atomic for enum)
    coordination_mode_t old_mode = g_coordination_mode;
    g_coordination_mode = mode;

    if (old_mode != mode) {
        ESP_LOGI(TAG, "Coordination mode changed: %d -> %d", old_mode, mode);
    }
}

/**
 * @brief Check if message type needs TDM scheduling
 *
 * Time-critical messages (PTP handshake, asymmetry probes) need TDM scheduling
 * to avoid BLE connection event contention. Other messages can send immediately.
 *
 * @param type Message type
 * @return true if TDM scheduling required
 */
static bool is_tdm_required_msg_type(sync_message_type_t type) {
    switch (type) {
        case SYNC_MSG_TIME_REQUEST:           // PTP handshake CLIENT→SERVER
        case SYNC_MSG_TIME_RESPONSE:          // PTP handshake SERVER→CLIENT
        case SYNC_MSG_REVERSE_PROBE:          // Asymmetry CLIENT→SERVER
        case SYNC_MSG_REVERSE_PROBE_RESPONSE: // Asymmetry SERVER→CLIENT
        case SYNC_MSG_PHASE_QUERY:            // Phase coherence query
        case SYNC_MSG_PHASE_RESPONSE:         // Phase coherence response
            return true;
        default:
            return false;
    }
}

/**
 * @brief Check if message type is a bootstrap message (must use BLE)
 *
 * Bootstrap messages are needed to ESTABLISH ESP-NOW peer configuration.
 * They must go over BLE because ESP-NOW peer isn't configured yet.
 *
 * @param type Message type
 * @return true if bootstrap message (must use BLE)
 */
static bool is_bootstrap_msg_type(sync_message_type_t type) {
    switch (type) {
        case SYNC_MSG_FIRMWARE_VERSION:       // AD040: Version exchange
        case SYNC_MSG_HARDWARE_INFO:          // AD048: Hardware info
        case SYNC_MSG_WIFI_MAC:               // AD048: WiFi MAC for ESP-NOW peer config
        case SYNC_MSG_ESPNOW_KEY_EXCHANGE:    // AD048: HKDF key derivation
        // Bug #35: Critical coordination messages need reliable BLE delivery
        // ESP-NOW fails intermittently during BLE coexistence, causing CLIENT_READY
        // and MOTOR_STARTED to be lost. Route these via BLE for reliable setup.
        case SYNC_MSG_CLIENT_READY:           // CLIENT→SERVER: handshake complete
        case SYNC_MSG_MOTOR_STARTED:          // SERVER→CLIENT: motor epoch notification
            return true;
        default:
            return false;
    }
}

/**
 * @brief Send coordination message to peer device
 *
 * AD048 Phase 7: Peer coordination uses ESP-NOW after bootstrap. BLE is used for:
 * - Bootstrap messages (firmware version, hardware info, WiFi MAC, key exchange)
 * - PWA ↔ SERVER communication
 *
 * @param msg Coordination message to send
 * @return ESP_OK on success, error code on failure
 */
esp_err_t ble_send_coordination_message(const coordination_message_t *msg) {
    if (msg == NULL) {
        ESP_LOGE(TAG, "NULL coordination message");
        return ESP_ERR_INVALID_ARG;
    }

    // Bootstrap messages MUST use BLE (ESP-NOW peer not configured yet)
    if (is_bootstrap_msg_type(msg->type)) {
        // Check if peer is connected via BLE
        uint16_t peer_conn_handle = ble_get_peer_conn_handle();
        if (peer_conn_handle == BLE_HS_CONN_HANDLE_NONE) {
            ESP_LOGD(TAG, "Cannot send bootstrap message: peer not connected");
            return ESP_ERR_INVALID_STATE;
        }

        // Check peer's coordination characteristic handle
        if (g_peer_coordination_char_handle == 0) {
            ESP_LOGW(TAG, "Peer coordination handle not discovered yet");
            return ESP_ERR_INVALID_STATE;
        }

        // Send via BLE GATT write (bootstrap path)
        int rc = ble_gattc_write_no_rsp_flat(peer_conn_handle, g_peer_coordination_char_handle,
                                              msg, sizeof(coordination_message_t));
        if (rc != 0) {
            ESP_LOGE(TAG, "Failed to write bootstrap message to peer: rc=%d", rc);
            return ESP_FAIL;
        }

        ESP_LOGD(TAG, "Bootstrap msg sent via BLE: type=%d", msg->type);
        return ESP_OK;
    }

    // Non-bootstrap messages use ESP-NOW
    if (!espnow_transport_is_ready()) {
        ESP_LOGW(TAG, "ESP-NOW not ready - coordination msg skipped: type=%d", msg->type);
        return ESP_ERR_INVALID_STATE;
    }

    esp_err_t ret;
    if (is_tdm_required_msg_type(msg->type)) {
        // Time-critical: Use TDM-scheduled send to avoid BLE contention
        ret = espnow_transport_send_coordination_tdm(
            (const uint8_t *)msg, sizeof(coordination_message_t));
    } else {
        // Non-time-critical: Send immediately via ESP-NOW
        ret = espnow_transport_send_coordination(
            (const uint8_t *)msg, sizeof(coordination_message_t));
    }

    if (ret == ESP_OK) {
        ESP_LOGD(TAG, "Coordination msg sent via ESP-NOW: type=%d%s",
                 msg->type, is_tdm_required_msg_type(msg->type) ? " [TDM]" : "");
    } else {
        ESP_LOGE(TAG, "ESP-NOW coordination send failed: type=%d, err=%s",
                 msg->type, esp_err_to_name(ret));
    }

    return ret;
}

/**
 * @brief Send all current settings to peer device (Phase 3a)
 * @return ESP_OK on success, error code on failure
 *
 * Helper function to sync all PWA-configurable settings to peer.
 * Called after ANY setting is changed via BLE write callbacks.
 * Prevents infinite sync loops (write callbacks call this, but update functions don't).
 */
static esp_err_t sync_settings_to_peer(void) {
    // Only sync if peer is connected
    if (!ble_is_peer_connected()) {
        return ESP_OK;  // Silently succeed if no peer
    }

    // Gather all current settings (mutex-protected)
    coordination_settings_t settings;
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in sync_settings_to_peer");
        return ESP_ERR_TIMEOUT;
    }

    // Copy all settings from char_data
    settings.frequency_cHz = char_data.custom_frequency_hz;
    settings.duty_pct = char_data.custom_duty_percent;
    settings.mode0_intensity_pct = char_data.mode0_intensity;
    settings.mode1_intensity_pct = char_data.mode1_intensity;
    settings.mode2_intensity_pct = char_data.mode2_intensity;
    settings.mode3_intensity_pct = char_data.mode3_intensity;
    settings.mode4_intensity_pct = char_data.mode4_intensity;
    settings.led_enable = char_data.led_enable ? 1 : 0;
    settings.led_color_mode = char_data.led_color_mode;
    settings.led_color_idx = char_data.led_palette_index;
    settings.led_custom_r = char_data.led_custom_r;
    settings.led_custom_g = char_data.led_custom_g;
    settings.led_custom_b = char_data.led_custom_b;
    settings.led_brightness_pct = char_data.led_brightness;

    // Only sync session_duration if it's been explicitly set by PWA (valid range check)
    // Prevents syncing uninitialized memory (Bug fix: Nov 23, 2025)
    if (char_data.session_duration_sec >= 1200 && char_data.session_duration_sec <= 5400) {
        settings.session_duration_sec = char_data.session_duration_sec;
    } else {
        // Skip syncing invalid/uninitialized session_duration
        // Keep peer's current value by setting to 0 (coordination handler will skip update)
        settings.session_duration_sec = 0;
    }

    xSemaphoreGive(char_data_mutex);

    // Build coordination message
    coordination_message_t msg = {
        .type = SYNC_MSG_SETTINGS,
        .timestamp_ms = (uint32_t)(esp_timer_get_time() / 1000ULL),
        .payload = {.settings = settings}
    };

    // Send to peer
    esp_err_t err = ble_send_coordination_message(&msg);
    if (err == ESP_OK) {
        ESP_LOGI(TAG, "Settings synced to peer: freq=%.2fHz duty=%u%% LED=%s (5 mode intensities)",
                 settings.frequency_cHz / 100.0f, settings.duty_pct,
                 settings.led_enable ? "ON" : "OFF");
    } else if (err != ESP_ERR_INVALID_STATE) {
        ESP_LOGW(TAG, "Failed to sync settings to peer: %s", esp_err_to_name(err));
    }

    return err;
}

// ============================================================================
// COORDINATION SETTINGS UPDATE API (Phase 3 - Internal Use Only)
// ============================================================================
// These functions update char_data WITHOUT triggering sync_settings_to_peer()
// to prevent infinite sync loops. Used only by ble_callback_coordination_message().

esp_err_t ble_update_custom_freq(uint16_t freq_cHz) {
    if (freq_cHz < 25 || freq_cHz > 200) {
        ESP_LOGE(TAG, "Invalid frequency: %u (range 25-200)", freq_cHz);
        return ESP_ERR_INVALID_ARG;
    }

    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in ble_update_custom_freq");
        return ESP_ERR_TIMEOUT;
    }

    // Only update if value changed (prevents redundant motor timing updates)
    bool changed = (char_data.custom_frequency_hz != freq_cHz);
    if (changed) {
        char_data.custom_frequency_hz = freq_cHz;
        settings_dirty = true;
    }
    xSemaphoreGive(char_data_mutex);

    // Only recalculate timing if value actually changed
    if (changed) {
        update_mode5_timing();
    }
    return ESP_OK;
}

esp_err_t ble_update_custom_duty(uint8_t duty_pct) {
    if (duty_pct < 10 || duty_pct > 100) {
        ESP_LOGE(TAG, "Invalid duty: %u (range 10-100)", duty_pct);
        return ESP_ERR_INVALID_ARG;
    }

    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in ble_update_custom_duty");
        return ESP_ERR_TIMEOUT;
    }

    // Only update if value changed (prevents redundant motor timing updates)
    bool changed = (char_data.custom_duty_percent != duty_pct);
    if (changed) {
        char_data.custom_duty_percent = duty_pct;
        settings_dirty = true;
    }
    xSemaphoreGive(char_data_mutex);

    // Only recalculate timing if value actually changed
    if (changed) {
        update_mode5_timing();
    }
    return ESP_OK;
}

// Mode 4 (Custom) PWM Intensity Update (for coordination sync)
esp_err_t ble_update_mode4_intensity(uint8_t intensity_pct) {
    if (intensity_pct > 80) {
        ESP_LOGE(TAG, "Invalid Mode 4 intensity: %u (range 30-80)", intensity_pct);
        return ESP_ERR_INVALID_ARG;
    }

    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in ble_update_mode4_intensity");
        return ESP_ERR_TIMEOUT;
    }

    bool changed = (char_data.mode4_intensity != intensity_pct);
    if (changed) {
        char_data.mode4_intensity = intensity_pct;
        settings_dirty = true;
    }
    xSemaphoreGive(char_data_mutex);

    if (changed) {
        esp_err_t err = motor_update_mode5_intensity(intensity_pct);
        if (err != ESP_OK) {
            ESP_LOGE(TAG, "Failed to update Mode 4 intensity: %s", esp_err_to_name(err));
            return err;
        }
    }
    return ESP_OK;
}

// Mode 0-3 PWM Intensity Updates (for coordination sync)
esp_err_t ble_update_mode0_intensity(uint8_t intensity_pct) {
    if (intensity_pct < 50 || intensity_pct > 80) {
        ESP_LOGE(TAG, "Invalid Mode 0 intensity: %u (range 50-80)", intensity_pct);
        return ESP_ERR_INVALID_ARG;
    }

    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in ble_update_mode0_intensity");
        return ESP_ERR_TIMEOUT;
    }
    char_data.mode0_intensity = intensity_pct;
    settings_dirty = true;
    xSemaphoreGive(char_data_mutex);
    return ESP_OK;
}

esp_err_t ble_update_mode1_intensity(uint8_t intensity_pct) {
    if (intensity_pct < 50 || intensity_pct > 80) {
        ESP_LOGE(TAG, "Invalid Mode 1 intensity: %u (range 50-80)", intensity_pct);
        return ESP_ERR_INVALID_ARG;
    }

    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in ble_update_mode1_intensity");
        return ESP_ERR_TIMEOUT;
    }
    char_data.mode1_intensity = intensity_pct;
    settings_dirty = true;
    xSemaphoreGive(char_data_mutex);
    return ESP_OK;
}

esp_err_t ble_update_mode2_intensity(uint8_t intensity_pct) {
    if (intensity_pct < 70 || intensity_pct > 90) {
        ESP_LOGE(TAG, "Invalid Mode 2 intensity: %u (range 70-90)", intensity_pct);
        return ESP_ERR_INVALID_ARG;
    }

    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in ble_update_mode2_intensity");
        return ESP_ERR_TIMEOUT;
    }
    char_data.mode2_intensity = intensity_pct;
    settings_dirty = true;
    xSemaphoreGive(char_data_mutex);
    return ESP_OK;
}

esp_err_t ble_update_mode3_intensity(uint8_t intensity_pct) {
    if (intensity_pct < 70 || intensity_pct > 90) {
        ESP_LOGE(TAG, "Invalid Mode 3 intensity: %u (range 70-90)", intensity_pct);
        return ESP_ERR_INVALID_ARG;
    }

    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in ble_update_mode3_intensity");
        return ESP_ERR_TIMEOUT;
    }
    char_data.mode3_intensity = intensity_pct;
    settings_dirty = true;
    xSemaphoreGive(char_data_mutex);
    return ESP_OK;
}

esp_err_t ble_update_led_palette(uint8_t palette_idx) {
    if (palette_idx > 15) {
        ESP_LOGE(TAG, "Invalid LED palette: %u (range 0-15)", palette_idx);
        return ESP_ERR_INVALID_ARG;
    }

    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in ble_update_led_palette");
        return ESP_ERR_TIMEOUT;
    }
    char_data.led_palette_index = palette_idx;
    settings_dirty = true;
    xSemaphoreGive(char_data_mutex);

    return ESP_OK;
}

esp_err_t ble_update_led_brightness(uint8_t brightness_pct) {
    if (brightness_pct < 10 || brightness_pct > 30) {
        ESP_LOGE(TAG, "Invalid LED brightness: %u (range 10-30)", brightness_pct);
        return ESP_ERR_INVALID_ARG;
    }

    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in ble_update_led_brightness");
        return ESP_ERR_TIMEOUT;
    }
    char_data.led_brightness = brightness_pct;
    settings_dirty = true;
    xSemaphoreGive(char_data_mutex);

    return ESP_OK;
}

esp_err_t ble_update_led_enable(bool enable) {
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in ble_update_led_enable");
        return ESP_ERR_TIMEOUT;
    }
    char_data.led_enable = enable;
    settings_dirty = true;
    xSemaphoreGive(char_data_mutex);

    return ESP_OK;
}

esp_err_t ble_update_led_color_mode(uint8_t mode) {
    if (mode > 1) {
        ESP_LOGE(TAG, "Invalid LED color mode: %u (range 0-1)", mode);
        return ESP_ERR_INVALID_ARG;
    }

    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in ble_update_led_color_mode");
        return ESP_ERR_TIMEOUT;
    }
    char_data.led_color_mode = mode;
    settings_dirty = true;
    xSemaphoreGive(char_data_mutex);

    return ESP_OK;
}

esp_err_t ble_update_led_custom_rgb(uint8_t r, uint8_t g, uint8_t b) {
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in ble_update_led_custom_rgb");
        return ESP_ERR_TIMEOUT;
    }
    char_data.led_custom_r = r;
    char_data.led_custom_g = g;
    char_data.led_custom_b = b;
    settings_dirty = true;
    xSemaphoreGive(char_data_mutex);

    return ESP_OK;
}

esp_err_t ble_update_session_duration(uint32_t duration_sec) {
    // Skip update if duration is 0 (indicates sender didn't have valid value to sync)
    // Bug fix: Nov 23, 2025 - prevents trying to sync uninitialized session_duration
    if (duration_sec == 0) {
        ESP_LOGD(TAG, "Skipping session_duration update (sender has no valid value)");
        return ESP_OK;  // Not an error - just skip the update
    }

    if (duration_sec < 1200 || duration_sec > 5400) {
        ESP_LOGE(TAG, "Invalid session duration: %lu (range 1200-5400)", duration_sec);
        return ESP_ERR_INVALID_ARG;
    }

    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in ble_update_session_duration");
        return ESP_ERR_TIMEOUT;
    }
    char_data.session_duration_sec = duration_sec;
    settings_dirty = true;
    xSemaphoreGive(char_data_mutex);

    return ESP_OK;
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
    if (ble_is_app_connected() && adv_state.notify_session_time_subscribed) {
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
    if (ble_is_app_connected() && adv_state.notify_mode_subscribed) {
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

// Legacy function - returns Mode 4 (Custom) intensity for backward compatibility
uint8_t ble_get_pwm_intensity(void) {
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in ble_get_pwm_intensity - possible deadlock");
        return 50;  // Return safe default
    }
    uint8_t intensity = char_data.mode4_intensity;
    xSemaphoreGive(char_data_mutex);
    return intensity;
}

uint8_t ble_get_mode0_intensity(void) {
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in ble_get_mode0_intensity");
        return 65;  // Safe default for mode 0 (50-80% range)
    }
    uint8_t intensity = char_data.mode0_intensity;
    xSemaphoreGive(char_data_mutex);
    return intensity;
}

uint8_t ble_get_mode1_intensity(void) {
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in ble_get_mode1_intensity");
        return 65;  // Safe default for mode 1 (50-80% range)
    }
    uint8_t intensity = char_data.mode1_intensity;
    xSemaphoreGive(char_data_mutex);
    return intensity;
}

uint8_t ble_get_mode2_intensity(void) {
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in ble_get_mode2_intensity");
        return 80;  // Safe default for mode 2 (70-90% range)
    }
    uint8_t intensity = char_data.mode2_intensity;
    xSemaphoreGive(char_data_mutex);
    return intensity;
}

uint8_t ble_get_mode3_intensity(void) {
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in ble_get_mode3_intensity");
        return 80;  // Safe default for mode 3 (70-90% range)
    }
    uint8_t intensity = char_data.mode3_intensity;
    xSemaphoreGive(char_data_mutex);
    return intensity;
}

uint8_t ble_get_mode4_intensity(void) {
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in ble_get_mode4_intensity");
        return 75;  // Safe default for mode 4 (30-80% range)
    }
    uint8_t intensity = char_data.mode4_intensity;
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

// ============================================================================
// BLE DIAGNOSTICS (Phase 2: Notification buffering investigation)
// ============================================================================

void ble_log_diagnostics(void) {
    // Only log if BLE is initialized and connected to peer
    if (!ble_is_peer_connected()) {
        return;  // Skip if no peer connection
    }

    ESP_LOGI(TAG, "=== BLE DIAGNOSTICS ===");

    // 1. HCI Controller Buffer Stats (ESP32-C6 BLE controller)
    // Note: ESP-IDF v5.5.0 may not expose detailed HCI buffer stats
    // We'll log what's available via NimBLE APIs

    // 2. Connection statistics
    uint16_t peer_handle = ble_get_peer_conn_handle();
    if (peer_handle != BLE_HS_CONN_HANDLE_NONE) {
        struct ble_gap_conn_desc desc;
        int rc = ble_gap_conn_find(peer_handle, &desc);
        if (rc == 0) {
            ESP_LOGI(TAG, "Peer connection: handle=%u, interval=%u (%.1fms), latency=%u, timeout=%u",
                     peer_handle,
                     desc.conn_itvl, desc.conn_itvl * 1.25,
                     desc.conn_latency,
                     desc.supervision_timeout);
        }
    }

    // 3. GATT notification stats (characteristic handles)
    ESP_LOGI(TAG, "GATT handles: time_sync=%u, coordination=%u (peer=%u)",
             g_time_sync_char_handle,
             g_coordination_char_handle,
             g_peer_coordination_char_handle);

    // 4. Memory stats (NimBLE host stack)
    // Note: os_mempool_info_get_next() not available in ESP-IDF v5.5.0
    // Future enhancement: Monitor NimBLE mbuf pool usage if API becomes available
    ESP_LOGI(TAG, "NimBLE mbuf pool monitoring: Not available in current ESP-IDF version");

    ESP_LOGI(TAG, "=== END DIAGNOSTICS ===");
}

// ============================================================================
// AD040: FIRMWARE VERSION EXCHANGE
// ============================================================================

esp_err_t ble_send_firmware_version_to_peer(void) {
    // Check if peer is connected
    if (!ble_is_peer_connected()) {
        ESP_LOGD(TAG, "AD040: Cannot send firmware version - peer not connected");
        return ESP_ERR_INVALID_STATE;
    }

    // Build coordination message with local firmware version
    firmware_version_t my_version = firmware_get_version();
    coordination_message_t msg = {
        .type = SYNC_MSG_FIRMWARE_VERSION,
        .timestamp_ms = (uint32_t)(esp_timer_get_time() / 1000),
    };
    memcpy(&msg.payload.firmware_version, &my_version, sizeof(firmware_version_t));

    // Send via coordination channel
    esp_err_t err = ble_send_coordination_message(&msg);
    if (err == ESP_OK) {
        ESP_LOGI(TAG, "AD040: Sent firmware version: v%d.%d.%d (%s %s)",
                 my_version.major, my_version.minor, my_version.patch,
                 my_version.build_date, my_version.build_time);
    } else {
        ESP_LOGW(TAG, "AD040: Failed to send firmware version: %s", esp_err_to_name(err));
    }

    return err;
}

void ble_set_peer_firmware_version(const char *version_str) {
    if (version_str == NULL) {
        return;
    }

    // Thread-safe update (mutex not strictly needed for simple string copy,
    // but keeping consistent with other char_data access patterns)
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(100)) == pdTRUE) {
        snprintf(peer_firmware_version_str, sizeof(peer_firmware_version_str), "%s", version_str);
        xSemaphoreGive(char_data_mutex);
        ESP_LOGD(TAG, "AD040: Peer firmware version set: %s", peer_firmware_version_str);
    } else {
        ESP_LOGW(TAG, "AD040: Mutex timeout setting peer firmware version");
    }
}

bool ble_firmware_versions_match(void) {
    return firmware_versions_match_flag;
}

bool ble_firmware_version_exchanged(void) {
    return firmware_version_exchanged;
}

/**
 * @brief Internal function to update version match flag (called from time_sync_task)
 * @param match true if versions match, false otherwise
 */
void ble_set_firmware_version_match(bool match) {
    firmware_versions_match_flag = match;
    firmware_version_exchanged = true;  // Mark that exchange completed
}

// ============================================================================
// AD048: HARDWARE INFO EXCHANGE
// ============================================================================

esp_err_t ble_send_hardware_info_to_peer(void) {
    // Check if peer is connected
    if (!ble_is_peer_connected()) {
        ESP_LOGD(TAG, "AD048: Cannot send hardware info - peer not connected");
        return ESP_ERR_INVALID_STATE;
    }

    // Build coordination message with local hardware info
    coordination_message_t msg = {
        .type = SYNC_MSG_HARDWARE_INFO,
        .timestamp_ms = (uint32_t)(esp_timer_get_time() / 1000),
    };
    snprintf(msg.payload.hardware_info.info_str,
             sizeof(msg.payload.hardware_info.info_str),
             "%s", local_hardware_info_str);

    // Send via coordination channel
    esp_err_t err = ble_send_coordination_message(&msg);
    if (err == ESP_OK) {
        ESP_LOGI(TAG, "AD048: Sent hardware info to peer: %s", local_hardware_info_str);
    } else {
        ESP_LOGW(TAG, "AD048: Failed to send hardware info: %s", esp_err_to_name(err));
    }

    return err;
}

void ble_set_peer_hardware_info(const char *hardware_str) {
    if (hardware_str == NULL) {
        return;
    }

    // Thread-safe update (mutex not strictly needed for simple string copy,
    // but keeping consistent with other char_data access patterns)
    if (xSemaphoreTake(char_data_mutex, pdMS_TO_TICKS(100)) == pdTRUE) {
        snprintf(peer_hardware_info_str, sizeof(peer_hardware_info_str), "%s", hardware_str);
        xSemaphoreGive(char_data_mutex);
        ESP_LOGD(TAG, "AD048: Peer hardware info set: %s", peer_hardware_info_str);
    } else {
        ESP_LOGW(TAG, "AD048: Mutex timeout setting peer hardware info");
    }
}

const char* ble_get_local_hardware_info(void) {
    return local_hardware_info_str;
}

esp_err_t ble_send_wifi_mac_to_peer(void) {
    if (!ble_is_peer_connected()) {
        ESP_LOGW(TAG, "AD048: Cannot send WiFi MAC - peer not connected");
        return ESP_ERR_INVALID_STATE;
    }

    coordination_message_t msg = {
        .type = SYNC_MSG_WIFI_MAC,
        .timestamp_ms = (uint32_t)(esp_timer_get_time() / 1000),
    };

    // Get local WiFi MAC address for ESP-NOW
    esp_err_t err = espnow_transport_get_local_mac(msg.payload.wifi_mac.mac);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "AD048: Failed to get WiFi MAC: %s", esp_err_to_name(err));
        return err;
    }

    ESP_LOGI(TAG, "AD048: Sending WiFi MAC to peer: %02X:%02X:%02X:%02X:%02X:%02X",
             msg.payload.wifi_mac.mac[0], msg.payload.wifi_mac.mac[1],
             msg.payload.wifi_mac.mac[2], msg.payload.wifi_mac.mac[3],
             msg.payload.wifi_mac.mac[4], msg.payload.wifi_mac.mac[5]);

    err = ble_send_coordination_message(&msg);
    if (err != ESP_OK) {
        ESP_LOGW(TAG, "AD048: Failed to send WiFi MAC: %s", esp_err_to_name(err));
    }

    return err;
}

esp_err_t ble_send_espnow_key_exchange(const uint8_t nonce[8], const uint8_t server_mac[6]) {
    if (!ble_is_peer_connected()) {
        ESP_LOGW(TAG, "AD048: Cannot send key exchange - peer not connected");
        return ESP_ERR_INVALID_STATE;
    }

    coordination_message_t msg = {
        .type = SYNC_MSG_ESPNOW_KEY_EXCHANGE,
        .timestamp_ms = (uint32_t)(esp_timer_get_time() / 1000),
    };

    // Copy nonce and server MAC to payload
    memcpy(msg.payload.espnow_key.nonce, nonce, 8);
    memcpy(msg.payload.espnow_key.server_mac, server_mac, 6);

    ESP_LOGI(TAG, "AD048: Sending ESP-NOW key exchange to CLIENT");
    ESP_LOGI(TAG, "  Nonce: %02X%02X%02X%02X%02X%02X%02X%02X",
             nonce[0], nonce[1], nonce[2], nonce[3],
             nonce[4], nonce[5], nonce[6], nonce[7]);

    esp_err_t err = ble_send_coordination_message(&msg);
    if (err != ESP_OK) {
        ESP_LOGW(TAG, "AD048: Failed to send key exchange: %s", esp_err_to_name(err));
    }

    return err;
}

esp_err_t ble_manager_deinit(void) {
    ESP_LOGI(TAG, "Deinitializing BLE manager...");
    ble_stop_advertising();
    ESP_LOGI(TAG, "BLE manager deinitialized");
    return ESP_OK;
}
