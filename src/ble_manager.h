/**
 * @file ble_manager.h
 * @brief BLE Manager Module - NimBLE GATT Configuration Service per AD032
 *
 * @defgroup ble_manager BLE Manager Module
 * @{
 *
 * @section bm_overview Overview
 *
 * This module implements a complete BLE GATT Configuration Service for EMDR
 * device configuration via mobile applications (nRF Connect, custom PWA). It provides:
 * - Dual-device peer discovery and role assignment
 * - Configuration Service with 13+ GATT characteristics
 * - Battery level and session time notifications
 * - NVS persistence for user preferences
 * - Coordinated bilateral motor synchronization messages
 *
 * @section bm_arduino Arduino Developers: BLE Differences
 *
 * | Arduino BLE | NimBLE (This Code) |
 * |-------------|-------------------|
 * | `BLE.begin()` | `nimble_port_init()` + `ble_hs_cfg` setup |
 * | `BLECharacteristic` class | Flat `ble_gatt_chr_def` struct arrays |
 * | `characteristic.setValue()` | `os_mbuf` and `ble_gattc_notify()` |
 * | Blocking read/write | Callback-based async I/O |
 * | Single connection | Multiple simultaneous connections |
 *
 * @section bm_gatt GATT Service Architecture
 *
 * @code{.unparsed}
 * Configuration Service (UUID: ...0200)
 * ├── Motor Control
 * │   ├── Mode (R/W)           - Current mode 0-4
 * │   ├── Frequency (R/W)      - Hz × 100 (25-200)
 * │   ├── Duty (R/W)           - Percentage 10-100%
 * │   └── Intensity (R/W)      - PWM 0-80% per mode
 * ├── LED Control
 * │   ├── Enable (R/W)         - On/off
 * │   ├── Color Mode (R/W)     - Palette or RGB
 * │   ├── Palette Index (R/W)  - 0-15 color selection
 * │   └── Brightness (R/W)     - 10-30%
 * └── Status
 *     ├── Battery (R/Notify)   - 0-100%
 *     └── Session Time (R/Notify) - Seconds elapsed
 * @endcode
 *
 * @section bm_peer Peer-to-Peer Coordination
 *
 * Two devices discover each other via Bilateral Control Service UUID.
 * Higher-battery device becomes SERVER (timing authority), lower becomes CLIENT.
 *
 * @section bm_safety Safety Considerations
 *
 * @warning BLE callbacks run in NimBLE's context, not FreeRTOS tasks.
 *          Never block in callbacks. Use queues to signal tasks.
 *
 * @warning Notifications can fail silently if client not subscribed.
 *          Always check return values from `ble_gattc_notify()`.
 *
 * @see docs/adr/0032-ble-configuration-service-architecture.md
 * @see docs/adr/0030-ble-bilateral-control-service.md
 *
 * @version 0.6.122
 * @date 2025-12-14
 * @author Claude Code (Anthropic) - Sonnet 4, Sonnet 4.5, Opus 4.5
 */

#ifndef BLE_MANAGER_H
#define BLE_MANAGER_H

#include <stdint.h>
#include <stdbool.h>
#include "esp_err.h"
#include "motor_task.h"        // For mode_t enum
#include "firmware_version.h"  // For firmware_version_t (AD040)

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================================
// BLE CONFIGURATION
// ============================================================================

#define BLE_DEVICE_NAME         "EMDR_Pulser"   /**< Base device name */
#define BLE_ADV_TIMEOUT_MS      300000          /**< 5-minute advertising timeout */

/**
 * @brief BLE advertising parameters
 *
 * Configured for balance between connection speed and power consumption:
 * - Interval: 20-40ms (fast connection)
 * - Undirected connectable mode
 * - General discoverable mode
 */

// ============================================================================
// GATT CHARACTERISTICS (Configuration Service - AD032)
// ============================================================================

/**
 * @brief Mode 5 LED color palette entry
 *
 * 16-color palette for WS2812B LED control
 * Each color defined as RGB 0-255
 */
typedef struct {
    uint8_t r;      /**< Red component 0-255 */
    uint8_t g;      /**< Green component 0-255 */
    uint8_t b;      /**< Blue component 0-255 */
    const char *name; /**< Color name for debugging */
} rgb_color_t;

/**
 * @brief Mode 5 (custom) LED color palette
 *
 * 16 colors for user selection via BLE
 * Index 0-15 maps to color palette
 */
extern const rgb_color_t color_palette[16];

/**
 * @brief LED color mode enumeration
 */
typedef enum {
    LED_COLOR_MODE_PALETTE = 0,  /**< Use palette index (0-15) */
    LED_COLOR_MODE_CUSTOM_RGB = 1 /**< Use custom RGB values */
} led_color_mode_t;

/**
 * @brief BLE characteristic data structure (AD032)
 *
 * Holds current values for all 12 GATT characteristics
 * Updated by write callbacks, read by read callbacks
 */
typedef struct {
    // Motor Control Group (8 characteristics - per-mode PWM intensity)
    mode_t current_mode;              /**< Current mode 0-4 (read/write) */
    uint16_t custom_frequency_hz;     /**< Hz × 100 (25-200 = 0.25-2.0 Hz) (read/write) */
    uint8_t custom_duty_percent;      /**< Duty cycle 10-100% (10% min, 100% = entire half-cycle) (read/write) */
    uint8_t mode0_intensity;          /**< Mode 0 (0.5Hz) PWM 50-80% (read/write) */
    uint8_t mode1_intensity;          /**< Mode 1 (1.0Hz) PWM 50-80% (read/write) */
    uint8_t mode2_intensity;          /**< Mode 2 (1.5Hz) PWM 70-90% (read/write) */
    uint8_t mode3_intensity;          /**< Mode 3 (2.0Hz) PWM 70-90% (read/write) */
    uint8_t mode4_intensity;          /**< Mode 4 (Custom) PWM 30-80% (0% = LED-only) (read/write) */

    // LED Control Group (5 characteristics)
    bool led_enable;                  /**< LED enable (read/write) */
    uint8_t led_color_mode;           /**< 0=palette, 1=custom RGB (read/write) */
    uint8_t led_palette_index;        /**< Palette index 0-15 (read/write) */
    uint8_t led_custom_r;             /**< Custom RGB red 0-255 (read/write) */
    uint8_t led_custom_g;             /**< Custom RGB green 0-255 (read/write) */
    uint8_t led_custom_b;             /**< Custom RGB blue 0-255 (read/write) */
    uint8_t led_brightness;           /**< LED brightness 10-30% (read/write) */

    // Status/Monitoring Group (4 characteristics)
    uint32_t session_duration_sec;    /**< Target session length 1200-5400 sec (read/write) */
    uint32_t session_time_sec;        /**< Elapsed seconds 0-5400 (read/notify) */
    uint8_t battery_level;            /**< SERVER battery % 0-100 (read/notify) */
    uint8_t client_battery_level;     /**< CLIENT battery % 0-100 (read/notify, dual-device) */
} ble_char_data_t;

// ============================================================================
// PUBLIC API
// ============================================================================

/**
 * @brief Initialize BLE subsystem and GATT server
 *
 * This is the main entry point for BLE functionality. Initializes the full
 * NimBLE stack, configures GATT services, and starts advertising.
 *
 * @par Arduino Equivalent
 * @code{.c}
 * // Arduino (simple):
 * BLE.begin();
 * BLE.setLocalName("EMDR_Pulser");
 * BLE.advertise();
 *
 * // ESP-IDF (this function does internally):
 * nimble_port_init();           // Initialize BLE controller
 * ble_hs_cfg.xxx = callback;    // Set up ALL callbacks manually
 * ble_gatts_count_cfg(...);     // Configure GATT table
 * ble_gatts_add_svcs(...);      // Register services
 * nimble_port_freertos_init();  // Start FreeRTOS task for BLE
 * // Much more explicit, but full control over every aspect
 * @endcode
 *
 * @warning This function starts a FreeRTOS task internally. Calling it
 *          multiple times without ble_manager_deinit() will leak resources.
 *
 * @warning Battery percentage must be measured BEFORE calling this function.
 *          It's used for peer role assignment during advertising (Bug #48).
 *
 * @warning BLE uses 2.4GHz radio. WiFi coexistence can cause timing jitter.
 *          Disable WiFi for best bilateral sync performance.
 *
 * @pre NVS flash initialized (esp_flash_init())
 * @pre Battery monitor initialized (battery_monitor_init())
 * @pre Motor hardware initialized (motor_init())
 * @post NimBLE host task running
 * @post Advertising started (device discoverable)
 *
 * @param[in] initial_battery_pct Battery percentage 0-100 for role assignment
 *                                 during peer discovery (higher battery = SERVER)
 *
 * @return
 * - ESP_OK: BLE stack initialized and advertising
 * - ESP_ERR_NO_MEM: Failed to allocate NimBLE buffers
 * - ESP_ERR_INVALID_STATE: Already initialized or NVS not ready
 * - ESP_FAIL: NimBLE port initialization failed
 *
 * @see ble_manager_deinit() for clean shutdown
 * @see ble_start_advertising() to manually restart advertising
 */
esp_err_t ble_manager_init(uint8_t initial_battery_pct);

/**
 * @brief Start BLE advertising
 *
 * Begins advertising if not already active
 * Called automatically after init and after disconnect
 * Can be manually triggered via button hold (1-2s)
 */
void ble_start_advertising(void);

/**
 * @brief Stop BLE advertising
 *
 * Stops advertising if active
 * Used to save power after connection established
 */
void ble_stop_advertising(void);

/**
 * @brief Reset pairing window for re-pairing after disconnect
 *
 * Resets the boot timestamp so devices advertise Bilateral UUID again,
 * enabling fresh battery-based role assignment instead of stale reconnection logic.
 * Also clears cached peer state to start fresh.
 *
 * Called by ble_task on MSG_BLE_REENABLE (button hold 1-2s)
 */
void ble_reset_pairing_window(void);

/**
 * @brief Close peer pairing window permanently (Bug #45)
 *
 * Closes the peer pairing window to prevent subsequent connections from being
 * identified as peers. This handles:
 * - Early peer pairing (e.g., at T=5s) - prevents mobile apps connecting after
 * - 30s timeout expiry - prevents late peer connections
 * - Simultaneous connection race conditions
 *
 * Called by:
 * - ble_manager connection handler when first peer identified
 * - ble_task when 30s pairing timeout expires
 */
void ble_close_pairing_window(void);

/**
 * @brief Start BLE scanning for peer devices (Phase 1a)
 *
 * Initiates BLE scanning while maintaining advertising (simultaneous mode).
 * Scans for Bilateral Control Service (6E400001-B5A3-F393-E0A9-E50E24DCCA9E).
 * Automatically connects when peer discovered.
 *
 * Called by ble_task after advertising starts (dual-device pairing)
 */
void ble_start_scanning(void);

/**
 * @brief Stop BLE scanning (Phase 1a)
 *
 * Stops active scanning for peer devices
 * Called when peer connection established or during shutdown
 */
void ble_stop_scanning(void);

/**
 * @brief Connect to discovered peer device (Phase 1a)
 *
 * Initiates BLE connection to peer advertising Bilateral Control Service.
 * Called automatically by scan callback when peer discovered.
 *
 * Connection events handled by existing ble_gap_event() callback
 */
void ble_connect_to_peer(void);

/**
 * @brief Check if BLE client is connected
 * @return true if client connected, false otherwise
 *
 * Used by motor_task and button_task to determine if BLE control is active
 */
bool ble_is_connected(void);

/**
 * @brief Check if connected to peer device (Phase 1b)
 * @return true if peer device connected, false otherwise
 *
 * Differentiates peer connections from mobile app connections
 * Used by motor_task for connection status logging
 */
bool ble_is_peer_connected(void);

/**
 * @brief Check and clear pending frequency change for debounced sync (Bug #95)
 * @param debounce_ms Debounce time in milliseconds (300ms recommended)
 * @return true if frequency change is ready for coordinated sync, false otherwise
 *
 * Called by time_sync_task to check if a Mode 4 frequency change has settled.
 * Returns true (and clears pending flag) if:
 * - A frequency change is pending AND
 * - At least debounce_ms has elapsed since last change
 *
 * Used to trigger AD045 mode change protocol after slider drag ends.
 */
bool ble_check_and_clear_freq_change_pending(uint32_t debounce_ms);

/**
 * @brief Get connection type string for logging (Phase 1b)
 * @return "Peer" if peer connected, "App" if mobile app connected, "Disconnected" if no connection
 *
 * Used by motor_task for periodic connection status heartbeat
 */
const char* ble_get_connection_type_str(void);

/**
 * @brief Get peer connection handle
 * @return Peer connection handle, or BLE_HS_CONN_HANDLE_NONE (0xFFFF) if not connected
 *
 * Used for graceful disconnect during shutdown
 */
uint16_t ble_get_peer_conn_handle(void);

/**
 * @brief Get mobile app connection handle
 * @return Mobile app connection handle, or BLE_HS_CONN_HANDLE_NONE (0xFFFF) if not connected
 *
 * Used for graceful disconnect during shutdown
 */
uint16_t ble_get_app_conn_handle(void);

/**
 * @brief Check if BLE pairing is in progress (Phase 1b.3)
 * @return true if pairing/bonding active, false otherwise
 *
 * Used by button task to handle pairing confirmation
 */
bool ble_is_pairing(void);

/**
 * @brief Get connection handle for active pairing (Phase 1b.3)
 * @return Connection handle for pairing, or BLE_HS_CONN_HANDLE_NONE if not pairing
 *
 * Used by button task for pairing confirmation via ble_sm_inject_io()
 */
uint16_t ble_get_pairing_conn_handle(void);

/**
 * @brief Check if BLE is currently advertising
 * @return true if advertising active, false otherwise
 *
 * Used by BLE task for timeout management
 */
bool ble_is_advertising(void);

/**
 * @brief Get advertising elapsed time
 * @return Milliseconds since advertising started (0 if not advertising)
 *
 * Used by BLE task to enforce 5-minute advertising timeout
 */
uint32_t ble_get_advertising_elapsed_ms(void);

/**
 * @brief Update battery level for BLE notifications
 * @param percentage Battery percentage 0-100
 *
 * Thread-safe update of battery characteristic
 * Triggers BLE notification if client subscribed
 * Called by motor_task every 10 seconds
 */
void ble_update_battery_level(uint8_t percentage);

/**
 * @brief Update client battery level for BLE notifications (SERVER only)
 * @param percentage CLIENT battery percentage 0-100
 *
 * Thread-safe update of client_battery characteristic
 * Triggers BLE notification if PWA client subscribed
 * Called when SERVER receives SYNC_MSG_CLIENT_BATTERY from CLIENT
 *
 * Phase 6: Dual-device CLIENT battery reporting for PWA display
 */
void ble_update_client_battery_level(uint8_t percentage);

/**
 * @brief Peer role in dual-device configuration (Phase 1b.2)
 */
typedef enum {
    PEER_ROLE_NONE = 0,    /**< No peer connection */
    PEER_ROLE_CLIENT,      /**< We initiated connection (stop advertising) */
    PEER_ROLE_SERVER       /**< Peer initiated connection (keep advertising) */
} peer_role_t;

/**
 * @brief Get current peer role (CLIENT/SERVER/NONE)
 * @return Current peer role
 *
 * Thread-safe read of peer connection role state
 * Used by motor_task for bilateral coordination (Phase 1b.3)
 * Returns PEER_ROLE_NONE if no peer connected
 */
peer_role_t ble_get_peer_role(void);

// ============================================================================
// PHASE 3: COORDINATION MESSAGES (Hybrid Architecture)
// ============================================================================

/**
 * @brief Coordination mode for dual-device operation (Phase 3)
 *
 * Tracks current coordination state for seamless fallback behavior
 */
typedef enum {
    COORD_MODE_STANDALONE = 0,  /**< No peer connected, independent operation */
    COORD_MODE_SERVER,          /**< Connected as SERVER, sending sync messages */
    COORD_MODE_CLIENT,          /**< Connected as CLIENT, receiving sync messages */
    COORD_MODE_FALLBACK         /**< Was coordinated, now independent (seamless fallback) */
} coordination_mode_t;

/**
 * @brief Coordination message types (Phase 3)
 *
 * Messages exchanged between peer devices for synchronized operation
 */
typedef enum {
    SYNC_MSG_MODE_CHANGE = 0,      /**< Mode changed (MODE_1 through MODE_CUSTOM) - deprecated, use PROPOSAL/ACK */
    SYNC_MSG_SETTINGS,             /**< Custom settings changed (frequency, duty, intensity, LED) */
    SYNC_MSG_SHUTDOWN,             /**< Coordinated shutdown request (fire-and-forget) */
    SYNC_MSG_START_ADVERTISING,    /**< CLIENT requests SERVER to enable advertising */
    SYNC_MSG_CLIENT_BATTERY,       /**< CLIENT battery level update (Phase 6) */
    SYNC_MSG_CLIENT_READY,         /**< CLIENT ready to start (received beacon, calculated phase) */
    SYNC_MSG_TIME_REQUEST,         /**< Time sync handshake: CLIENT→SERVER with T1 (client send time) */
    SYNC_MSG_TIME_RESPONSE,        /**< Time sync handshake: SERVER→CLIENT with T1, T2, T3 */
    SYNC_MSG_MOTOR_STARTED,        /**< Phase 6: SERVER→CLIENT immediate motor epoch notification */
    SYNC_MSG_MODE_CHANGE_PROPOSAL, /**< AD045: SERVER→CLIENT mode change proposal with future epochs */
    SYNC_MSG_MODE_CHANGE_ACK,      /**< AD045: CLIENT→SERVER mode change acknowledgment */
    SYNC_MSG_ACTIVATION_REPORT,    /**< PTP-style: CLIENT→SERVER activation timing for drift verification */
    SYNC_MSG_REVERSE_PROBE,        /**< IEEE 1588 bidirectional: CLIENT→SERVER with T1' timestamp */
    SYNC_MSG_REVERSE_PROBE_RESPONSE, /**< IEEE 1588 bidirectional: SERVER→CLIENT with T2', T3' timestamps */
    SYNC_MSG_FIRMWARE_VERSION = 0x10 /**< AD040: One-time firmware version exchange after MTU */
} sync_message_type_t;

/**
 * @brief Settings payload for SYNC_MSG_SETTINGS
 *
 * Contains ALL PWA-configurable parameters that sync between devices (Phase 3a)
 *
 * BUG FIX (Nov 24, 2025): Added __attribute__((packed)) to prevent compiler padding
 * that causes data corruption during BLE transmission
 */
typedef struct __attribute__((packed)) {
    // Motor Control
    uint16_t frequency_cHz;        /**< Frequency Hz × 100 (25-200 = 0.25-2.0 Hz) */
    uint8_t duty_pct;              /**< Duty cycle 10-100% */
    uint8_t mode0_intensity_pct;   /**< Mode 0 (0.5Hz) PWM intensity 50-80% */
    uint8_t mode1_intensity_pct;   /**< Mode 1 (1.0Hz) PWM intensity 50-80% */
    uint8_t mode2_intensity_pct;   /**< Mode 2 (1.5Hz) PWM intensity 70-90% */
    uint8_t mode3_intensity_pct;   /**< Mode 3 (2.0Hz) PWM intensity 70-90% */
    uint8_t mode4_intensity_pct;   /**< Mode 4 (Custom) PWM intensity 30-80% */

    // LED Control
    uint8_t led_enable;            /**< LED enable (0=off, 1=on) */
    uint8_t led_color_mode;        /**< LED color mode (0=palette, 1=custom RGB) */
    uint8_t led_color_idx;         /**< LED palette index 0-15 */
    uint8_t led_custom_r;          /**< LED custom RGB red 0-255 */
    uint8_t led_custom_g;          /**< LED custom RGB green 0-255 */
    uint8_t led_custom_b;          /**< LED custom RGB blue 0-255 */
    uint8_t led_brightness_pct;    /**< LED brightness 10-30% */

    // Session Control
    uint32_t session_duration_sec; /**< Target session duration 1200-5400 sec */
} coordination_settings_t;

/**
 * @brief Time sync request payload for SYNC_MSG_TIME_REQUEST
 *
 * CLIENT sends this to SERVER to initiate NTP-style handshake.
 * T1 = CLIENT's local time when request was sent.
 */
typedef struct __attribute__((packed)) {
    uint64_t t1_client_send_us;    /**< CLIENT's local time when request sent */
} time_sync_request_t;

/**
 * @brief Time sync response payload for SYNC_MSG_TIME_RESPONSE
 *
 * SERVER sends this back to CLIENT with all timestamps.
 * CLIENT calculates: offset = ((T2-T1) + (T3-T4)) / 2
 *                    RTT = (T4-T1) - (T3-T2)
 *
 * Also includes motor_epoch so CLIENT doesn't have to wait for next beacon.
 */
typedef struct __attribute__((packed)) {
    uint64_t t1_client_send_us;    /**< Echo back T1 from request */
    uint64_t t2_server_recv_us;    /**< SERVER's local time when request received */
    uint64_t t3_server_send_us;    /**< SERVER's local time when response sent */
    uint64_t motor_epoch_us;       /**< SERVER's motor epoch (0 if not set) */
    uint32_t motor_cycle_ms;       /**< Motor cycle period in ms (0 if not set) */
} time_sync_response_t;

/**
 * @brief Mode change proposal payload for SYNC_MSG_MODE_CHANGE_PROPOSAL (AD045)
 *
 * SERVER sends this to CLIENT to propose a synchronized mode change.
 * Contains future epochs ensuring both devices transition together while
 * maintaining perfect antiphase alignment.
 *
 * Two-Phase Commit Protocol:
 * 1. SERVER proposes mode change with future epochs (2s from now)
 * 2. CLIENT validates epochs are in future, sends SYNC_MSG_MODE_CHANGE_ACK
 * 3. Both devices arm mode change and wait until their respective epochs
 * 4. Both transition simultaneously - SERVER at server_epoch_us, CLIENT at client_epoch_us
 */
typedef struct __attribute__((packed)) {
    mode_t new_mode;               /**< New mode to activate (0-4) */
    uint32_t new_cycle_ms;         /**< New cycle period in ms */
    uint32_t new_active_ms;        /**< New active period in ms */
    uint64_t server_epoch_us;      /**< When SERVER will start new pattern */
    uint64_t client_epoch_us;      /**< When CLIENT should start new pattern (server + half_cycle) */
} mode_change_proposal_t;

/**
 * @brief Motor started payload for SYNC_MSG_MOTOR_STARTED
 *
 * Phase 6: SERVER sends this to CLIENT immediately when motors start.
 * Eliminates the 9.5s delay waiting for periodic beacon or handshake.
 * CLIENT can calculate antiphase and start motors within 100-200ms.
 */
typedef struct __attribute__((packed)) {
    uint64_t motor_epoch_us;       /**< SERVER's motor epoch (cycle start time) */
    uint32_t motor_cycle_ms;       /**< Motor cycle period in ms */
} motor_started_t;

/**
 * @brief Activation report payload for SYNC_MSG_ACTIVATION_REPORT
 *
 * PTP-style synchronization error feedback: CLIENT reports its activation
 * timing to SERVER for independent drift verification.
 *
 * Following IEEE 1588 Delay_Req/Delay_Resp pattern:
 * - CLIENT sends this after transitioning to ACTIVE state
 * - SERVER receives and independently calculates drift
 * - Enables bidirectional timing verification (both sides know the error)
 *
 * AD043 Enhancement (v0.6.72): Added paired timestamps for NTP-style offset calculation
 * CLIENT includes beacon timestamps so SERVER can calculate bias-corrected offset:
 *   offset = ((T2-T1) + (T3-T4)) / 2
 * where T1=beacon_server_time, T2=beacon_rx_time, T3=report_tx_time, T4=SERVER rx
 * This corrects the systematic one-way delay bias in the EMA filter.
 *
 * Rate limited: Sent every N cycles to avoid BLE congestion
 */
typedef struct __attribute__((packed)) {
    uint64_t actual_time_us;       /**< CLIENT's actual ACTIVE start (synchronized time) */
    uint64_t target_time_us;       /**< CLIENT's calculated target time */
    int32_t  client_error_ms;      /**< CLIENT's self-measured error (actual - target) */
    uint32_t cycle_number;         /**< Cycle count for correlation */
    /* AD043: Paired timestamps for NTP-style offset calculation */
    uint64_t beacon_server_time_us; /**< T1: server_time_us from last beacon */
    uint64_t beacon_rx_time_us;     /**< T2: CLIENT's local time when beacon received */
    uint64_t report_tx_time_us;     /**< T3: CLIENT's local time when sending this report */
} activation_report_t;

/**
 * @brief Reverse probe payload for SYNC_MSG_REVERSE_PROBE
 *
 * IEEE 1588 bidirectional path measurement: CLIENT initiates probe to SERVER.
 * This is the "reverse direction" compared to the normal SERVER→CLIENT beacons.
 *
 * Purpose: Detect path asymmetry by measuring delay from CLIENT→SERVER direction.
 * If BLE paths are symmetric, forward and reverse offsets should match.
 * If asymmetric, the difference reveals the "ghost time" causing drift.
 *
 * Flow:
 * 1. CLIENT records T1' (local time) just before sending this probe
 * 2. SERVER receives probe, records T2' (local time at receipt)
 * 3. SERVER sends REVERSE_PROBE_RESPONSE with T2', T3' (send time)
 * 4. CLIENT receives response, records T4' (local time)
 * 5. CLIENT calculates reverse offset: ((T2'-T1') - (T4'-T3')) / 2
 */
typedef struct __attribute__((packed)) {
    uint64_t client_send_time_us;  /**< T1': CLIENT's local time when probe sent */
    uint32_t probe_sequence;       /**< Sequence number for correlation */
} reverse_probe_t;

/**
 * @brief Reverse probe response payload for SYNC_MSG_REVERSE_PROBE_RESPONSE
 *
 * SERVER response to CLIENT's reverse probe, completing the bidirectional
 * timing measurement. Contains T2' and T3' for CLIENT's offset calculation.
 */
typedef struct __attribute__((packed)) {
    uint64_t client_send_time_us;  /**< T1': Echo from probe (for CLIENT correlation) */
    uint64_t server_recv_time_us;  /**< T2': SERVER's local time when probe received */
    uint64_t server_send_time_us;  /**< T3': SERVER's local time when response sent */
    uint32_t probe_sequence;       /**< Sequence number echo for correlation */
} reverse_probe_response_t;

/**
 * @brief Coordination message structure (Phase 3)
 *
 * Unified message format for all peer-to-peer coordination
 * Includes timestamp for conflict resolution using Phase 2 time sync
 *
 * BUG FIX (Nov 24, 2025): Added __attribute__((packed)) to prevent compiler padding
 */
typedef struct __attribute__((packed)) {
    sync_message_type_t type;      /**< Message type */
    uint32_t timestamp_ms;         /**< Synchronized timestamp for conflict resolution */
    union {
        mode_t mode;               /**< MODE_CHANGE: New mode (0-4) - deprecated */
        coordination_settings_t settings;  /**< SETTINGS: PWA parameter changes */
        uint8_t battery_level;     /**< CLIENT_BATTERY: Battery percentage 0-100 */
        time_sync_request_t time_request;   /**< TIME_REQUEST: NTP handshake T1 */
        time_sync_response_t time_response; /**< TIME_RESPONSE: NTP handshake T1,T2,T3 */
        motor_started_t motor_started;      /**< MOTOR_STARTED: Immediate epoch notification (Phase 6) */
        mode_change_proposal_t mode_proposal; /**< MODE_CHANGE_PROPOSAL: Two-phase commit proposal (AD045) */
        activation_report_t activation_report; /**< ACTIVATION_REPORT: PTP-style timing feedback */
        reverse_probe_t reverse_probe;       /**< REVERSE_PROBE: CLIENT→SERVER bidirectional timing */
        reverse_probe_response_t reverse_probe_response; /**< REVERSE_PROBE_RESPONSE: SERVER→CLIENT response */
        firmware_version_t firmware_version; /**< FIRMWARE_VERSION: AD040 one-time version exchange */
        // MODE_CHANGE_ACK, SHUTDOWN and START_ADVERTISING have no payload
    } payload;
} coordination_message_t;

/**
 * @brief Check if any bonded peer exists in NVS storage
 * @return true if bonded peer found, false otherwise
 *
 * Used by BLE task to determine if pairing window should be skipped
 * on reconnection (Phase 1b.3). If bonded peer exists, device can
 * silently wait for reconnection without 30-second pairing window.
 */
bool ble_check_bonded_peer_exists(void);

/**
 * @brief Update bilateral battery level for peer device role comparison (Phase 1b)
 * @param percentage Battery percentage 0-100
 *
 * Thread-safe update of Bilateral Control Service battery characteristic
 * Used by peer devices for battery-based role assignment (AD034)
 * Called by motor_task alongside ble_update_battery_level()
 */
void ble_update_bilateral_battery_level(uint8_t percentage);

/**
 * @brief Send time sync beacon to peer device (SERVER only)
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_STATE if not SERVER role or peer not connected
 * @return ESP_ERR_TIMEOUT if mutex timeout
 * @return ESP_FAIL if notification send failed
 *
 * Called periodically by motor_task when time_sync_should_send_beacon() returns true
 * Generates sync beacon from time sync module and sends via BLE notification to peer
 *
 * Phase 2 (AD039): Hybrid time synchronization protocol
 */
esp_err_t ble_send_time_sync_beacon(void);

/**
 * @brief Update session time for BLE notifications
 * @param seconds Elapsed session time in seconds
 *
 * Thread-safe update of session time characteristic
 * Triggers BLE notification if client subscribed
 * NOTE: Should be called every 30-60 seconds (not every second)
 * Mobile app counts seconds in UI between notifications
 */
void ble_update_session_time(uint32_t seconds);

/**
 * @brief Update mode and send BLE notification
 * @param mode New mode value (0-4)
 *
 * Thread-safe update of mode characteristic
 * Triggers BLE notification if client subscribed
 * Called by button_task when mode changes via button press
 * Allows mobile app to stay synchronized with device mode
 */
void ble_update_mode(mode_t mode);

/**
 * @brief Get current BLE-configured mode
 * @return Current mode_t value (0-4)
 *
 * Thread-safe read of mode characteristic
 * Used by motor_task to determine active mode
 */
mode_t ble_get_current_mode(void);

/**
 * @brief Get Mode 5 custom frequency
 * @return Frequency in Hz × 100 (e.g., 100 = 1.00 Hz)
 *
 * Thread-safe read of custom frequency characteristic
 * Valid range: 25-200 (0.25-2.0 Hz research platform)
 */
uint16_t ble_get_custom_frequency_hz(void);

/**
 * @brief Get Mode 5 custom duty cycle
 * @return Duty cycle percentage 10-100%
 *
 * Thread-safe read of custom duty cycle characteristic
 * Percentage of half-cycle that motor/LED is active
 * DUTY CYCLE CLARIFICATION: Percentage of ACTIVE half-cycle only
 * Each frequency cycle has ACTIVE/INACTIVE periods (50/50 split)
 * GUARANTEE: Motor is always OFF for at least 50% of total cycle time
 * 10% minimum ensures perceptible timing pattern
 * 100% duty = motor ON for entire ACTIVE period, then guaranteed OFF for INACTIVE period
 * For LED-only mode (no motor), use PWM intensity = 0% instead
 */
uint8_t ble_get_custom_duty_percent(void);

/**
 * @brief Get Mode 5 PWM intensity (legacy - returns Mode 4 intensity)
 * @return PWM intensity percentage 0-80%
 * @deprecated Use ble_get_mode0_intensity() through ble_get_mode4_intensity() instead
 *
 * Thread-safe read of PWM intensity characteristic
 * 0% enables LED-only mode (no motor vibration)
 * 80% maximum prevents motor overheating (safety limit per AD031)
 */
uint8_t ble_get_pwm_intensity(void);

/**
 * @brief Get Mode 0 (0.5Hz) PWM intensity
 * @return Intensity percentage (50-80%)
 */
uint8_t ble_get_mode0_intensity(void);

/**
 * @brief Get Mode 1 (1.0Hz) PWM intensity
 * @return Intensity percentage (50-80%)
 */
uint8_t ble_get_mode1_intensity(void);

/**
 * @brief Get Mode 2 (1.5Hz) PWM intensity
 * @return Intensity percentage (70-90%)
 */
uint8_t ble_get_mode2_intensity(void);

/**
 * @brief Get Mode 3 (2.0Hz) PWM intensity
 * @return Intensity percentage (70-90%)
 */
uint8_t ble_get_mode3_intensity(void);

/**
 * @brief Get Mode 4 (Custom) PWM intensity
 * @return Intensity percentage (30-80%)
 */
uint8_t ble_get_mode4_intensity(void);

/**
 * @brief Get LED enable state
 * @return true if LED enabled, false otherwise
 *
 * Thread-safe read of LED enable characteristic
 */
bool ble_get_led_enable(void);

/**
 * @brief Get LED color mode
 * @return 0=palette mode, 1=custom RGB mode
 *
 * Thread-safe read of LED color mode characteristic
 * Determines which color source to use (palette index or custom RGB)
 */
uint8_t ble_get_led_color_mode(void);

/**
 * @brief Get LED palette index
 * @return Color index 0-15
 *
 * Thread-safe read of LED palette index characteristic
 * Index into color_palette array (used when color mode = 0)
 */
uint8_t ble_get_led_palette_index(void);

/**
 * @brief Get LED custom RGB values
 * @param r Output: Red component 0-255
 * @param g Output: Green component 0-255
 * @param b Output: Blue component 0-255
 *
 * Thread-safe read of LED custom RGB characteristic
 * Used when color mode = 1 (custom RGB)
 */
void ble_get_led_custom_rgb(uint8_t *r, uint8_t *g, uint8_t *b);

/**
 * @brief Get LED brightness
 * @return Brightness percentage 10-30%
 *
 * Thread-safe read of LED brightness characteristic
 * Limited to 30% max to prevent eye strain
 */
uint8_t ble_get_led_brightness(void);

/**
 * @brief Get target session duration
 * @return Session duration in seconds (1200-5400)
 *
 * Thread-safe read of session duration characteristic
 * Range: 20-90 minutes configurable via mobile app
 */
uint32_t ble_get_session_duration_sec(void);

/**
 * @brief Check if settings need NVS save
 * @return true if any parameter changed since last save
 *
 * Monitors dirty flag for deferred NVS writes
 * Used to reduce flash wear (save only on shutdown)
 */
bool ble_settings_dirty(void);

/**
 * @brief Mark settings as saved to NVS
 *
 * Clears dirty flag after successful NVS write
 * Called by power_manager after save_settings_to_nvs()
 */
void ble_settings_mark_clean(void);

/**
 * @brief Save user preferences to NVS
 * @return ESP_OK on success, error code on failure
 *
 * Saves all user-configurable parameters to NVS with signature validation:
 * - Mode (last used)
 * - Custom Frequency
 * - Custom Duty Cycle
 * - LED Enable
 * - LED Color Mode
 * - LED Palette Index
 * - LED Custom RGB
 * - LED Brightness
 * - PWM Intensity
 * - Session Duration
 *
 * Called before deep sleep to persist user settings
 * Only writes if dirty flag set (reduces flash wear)
 */
esp_err_t ble_save_settings_to_nvs(void);

/**
 * @brief Load user preferences from NVS
 * @return ESP_OK on success, error code on failure
 *
 * Loads all user-configurable parameters from NVS with signature verification
 * Called once at boot to restore previous configuration
 * Falls back to defaults if signature invalid or NVS empty
 */
esp_err_t ble_load_settings_from_nvs(void);

/**
 * @brief Deinitialize BLE subsystem
 * @return ESP_OK on success, error code on failure
 *
 * Stops advertising, disconnects client, and shuts down NimBLE host
 * Called during shutdown sequence before deep sleep
 */
esp_err_t ble_manager_deinit(void);

// ============================================================================
// PHASE 3: COORDINATION API
// ============================================================================

/**
 * @brief Send coordination message to peer device (Phase 3)
 * @param msg Coordination message to send
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_STATE if peer not connected
 * @return ESP_FAIL if notification send failed
 *
 * Non-blocking send via BLE notification. Does not wait for acknowledgment.
 * Used for mode sync, settings sync, shutdown commands, advertising requests.
 * Called by motor_task, button_task, and BLE characteristic write callbacks.
 */
esp_err_t ble_send_coordination_message(const coordination_message_t *msg);

/**
 * @brief Get current coordination mode (Phase 3)
 * @return Current coordination mode (STANDALONE/SERVER/CLIENT/FALLBACK)
 *
 * Thread-safe read of coordination state
 * Used by motor_task to determine sync behavior
 */
coordination_mode_t ble_get_coordination_mode(void);

/**
 * @brief Set coordination mode (Phase 3)
 * @param mode New coordination mode
 *
 * Thread-safe write of coordination state
 * Called by BLE manager during connection/disconnection events
 * Called by motor_task when detecting fallback condition
 */
void ble_set_coordination_mode(coordination_mode_t mode);

/**
 * @brief Internal update functions for coordination message handling
 *
 * These functions update char_data WITHOUT triggering sync_settings_to_peer()
 * to prevent infinite sync loops. Used ONLY by ble_callback_coordination_message().
 *
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_ARG if parameter out of range
 * @return ESP_ERR_TIMEOUT if mutex timeout
 */
esp_err_t ble_update_custom_freq(uint16_t freq_cHz);
esp_err_t ble_update_custom_duty(uint8_t duty_pct);
esp_err_t ble_update_mode0_intensity(uint8_t intensity_pct);
esp_err_t ble_update_mode1_intensity(uint8_t intensity_pct);
esp_err_t ble_update_mode2_intensity(uint8_t intensity_pct);
esp_err_t ble_update_mode3_intensity(uint8_t intensity_pct);
esp_err_t ble_update_mode4_intensity(uint8_t intensity_pct);
esp_err_t ble_update_led_enable(bool enable);
esp_err_t ble_update_led_color_mode(uint8_t mode);
esp_err_t ble_update_led_palette(uint8_t palette_idx);
esp_err_t ble_update_led_custom_rgb(uint8_t r, uint8_t g, uint8_t b);
esp_err_t ble_update_led_brightness(uint8_t brightness_pct);
esp_err_t ble_update_session_duration(uint32_t duration_sec);

/**
 * @brief Log BLE diagnostics (RX queue, HCI buffers, connection stats)
 *
 * Logs diagnostic information to help identify BLE notification buffering issues:
 * - NimBLE notification queue depth
 * - HCI controller buffer usage (ACL RX/TX)
 * - Connection event statistics
 * - BLE error counters
 *
 * Call periodically (e.g., with sync beacons) to monitor BLE health.
 */
void ble_log_diagnostics(void);

// ============================================================================
// AD040: FIRMWARE VERSION EXCHANGE
// ============================================================================

/**
 * @brief Send local firmware version to connected peer (AD040)
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_STATE if peer not connected
 * @return ESP_FAIL if send failed
 *
 * Called after MTU exchange completes to exchange firmware versions.
 * Both SERVER and CLIENT call this after their MTU negotiation completes.
 * The peer handles the received version in time_sync_task via SYNC_MSG_FIRMWARE_VERSION.
 */
esp_err_t ble_send_firmware_version_to_peer(void);

/**
 * @brief Set peer firmware version string (AD040)
 * @param version_str Version string to store (e.g., "v0.6.124 (Dec 16 2025)")
 *
 * Called by time_sync_task when SYNC_MSG_FIRMWARE_VERSION is received.
 * Updates the peer_firmware_version_str for BLE characteristic reads.
 *
 * Thread-safe: Uses internal mutex
 */
void ble_set_peer_firmware_version(const char *version_str);

/**
 * @brief Check if firmware versions match (AD040)
 * @return true if peer firmware matches local (or no peer connected)
 * @return false if mismatch detected
 *
 * Used by time_sync_task to determine if LED warning should be shown.
 */
bool ble_firmware_versions_match(void);

/**
 * @brief Set firmware version match flag (AD040)
 * @param match true if versions match, false otherwise
 *
 * Called by time_sync_task when SYNC_MSG_FIRMWARE_VERSION is received
 * after comparing local and peer versions.
 */
void ble_set_firmware_version_match(bool match);

// ============================================================================
// EXTERNAL CALLBACKS (implemented by time_sync_task)
// ============================================================================

/**
 * @brief Callback for BLE mode change
 * @param new_mode New mode value 0-4
 *
 * Called by BLE manager when mode characteristic is written
 * Motor task should update current mode and reconfigure timings
 *
 * NOTE: Implemented in motor_task.c, declared extern here
 */
extern void ble_callback_mode_changed(mode_t new_mode);

/**
 * @brief Callback for BLE parameter update
 *
 * Called by BLE manager when any Mode 5 parameter is written
 * Motor task should reload parameters via ble_get_* functions
 *
 * NOTE: Implemented in motor_task.c, declared extern here
 */
extern void ble_callback_params_updated(void);

// NOTE: ble_callback_coordination_message() removed in Phase 3 refactor.
// Coordination messages now go through time_sync_task_send_coordination()
// to prevent BLE processing from blocking motor timing.

/** @} */ // end of ble_manager group

#ifdef __cplusplus
}
#endif

#endif // BLE_MANAGER_H
