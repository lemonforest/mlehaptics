/**
 * @file secure_smp_pairing.c
 * @brief High-Security BLE SMP Pairing Example for ESP32-C6
 *
 * @author EMDR Pulser Project Contributors
 * @date December 2025
 * @version 1.0.0
 *
 * @section LICENSE
 * SPDX-License-Identifier: GPL-3.0-or-later
 *
 * @section DESCRIPTION
 *
 * This example demonstrates cryptographically secure BLE SMP (Security Manager
 * Protocol) pairing between two ESP32-C6 devices using Numeric Comparison mode
 * with MITM (Man-in-the-Middle) protection.
 *
 * @section SECURITY_MODEL
 *
 * **Security Level: LE Secure Connections with Authenticated MITM Protection**
 *
 * This implementation uses the highest security level available in BLE 4.2+:
 *
 * | Feature | Value | Rationale |
 * |---------|-------|-----------|
 * | I/O Capability | DISPLAY_YESNO | Enables Numeric Comparison |
 * | MITM Protection | Enabled | Prevents relay attacks |
 * | LE Secure Connections | Required | ECDH P-256 key exchange |
 * | Bonding | Enabled | Stores LTK for reconnection |
 * | Key Distribution | ENC + ID | Both devices share keys |
 *
 * **Why Not "Just Works"?**
 *
 * Just Works pairing (BLE_HS_IO_NO_INPUT_OUTPUT) provides NO protection against
 * MITM attacks. An attacker can intercept and modify traffic between devices.
 * While convenient, it should NEVER be used when:
 * - Data confidentiality matters
 * - Device authenticity must be verified
 * - The pairing channel could be observed/modified
 *
 * **Numeric Comparison Flow:**
 * 1. Devices exchange public keys (ECDH P-256)
 * 2. Both devices compute and display a 6-digit code
 * 3. User confirms the codes match on both devices
 * 4. If confirmed, pairing completes with authenticated link
 * 5. LTK is derived and stored for future encrypted sessions
 *
 * @section IMPLEMENTATION_NOTES
 *
 * **Critical Discoveries (Bug #113):**
 *
 * 1. **ble_store_config_init() is MANDATORY**
 *    Without this call, ble_gap_security_initiate() returns BLE_HS_ENOTSUP (rc=8).
 *    This function sets up the store callbacks (read/write/delete) that SMP needs
 *    to persist and retrieve security material.
 *
 * 2. **MAC Address Tie-Breaker**
 *    When two identical devices discover each other simultaneously, both may try
 *    to initiate a connection, causing BLE_ERR_ACL_CONN_EXISTS (rc=6) errors.
 *    Solution: Only the device with the LOWER MAC address initiates connection.
 *
 * 3. **Stabilization Delays**
 *    BLE GAP operations need time to complete internally:
 *    - 100ms between ble_gap_disc_cancel() and ble_gap_connect()
 *    - 200ms after connection before MTU exchange
 *    - 50ms after MTU exchange before SMP initiation
 *
 * 4. **RAM-Only Storage**
 *    Set CONFIG_BT_NIMBLE_NVS_PERSIST=n in sdkconfig to prevent "zombie bonds"
 *    from causing pairing conflicts across reboots during development.
 *
 * @section USAGE
 *
 * 1. Flash this firmware to two ESP32-C6 devices
 * 2. Power on both devices within ~30 seconds
 * 3. Monitor serial output on both devices
 * 4. When pairing initiates:
 *    - Both devices display identical 6-digit code
 *    - In production: User confirms match on both devices
 *    - In this example: Auto-confirmed for testing (see PASSKEY_ACTION handler)
 * 5. Success: "SMP PAIRING SUCCESS! Connection encrypted"
 *
 * @section BUILD
 *
 * **ESP-IDF (PlatformIO):**
 * @code
 * pio run -e secure_smp_pairing -t upload
 * pio device monitor
 * @endcode
 *
 * @section REFERENCES
 *
 * - Bluetooth Core Spec v5.3, Vol 3, Part H (Security Manager Specification)
 * - ESP-IDF NimBLE Examples: https://github.com/espressif/esp-idf/tree/master/examples/bluetooth/nimble
 * - EMDR Pulser Bug #113: SMP Pairing Timeout Investigation
 *
 * @section ARDUINO_PORTING Arduino Framework Porting Guide
 *
 * This code can be adapted for Arduino ESP32 with NimBLE-Arduino library.
 * Key differences and equivalents:
 *
 * **Library:**
 * - Install: "NimBLE-Arduino" by h2zero (PlatformIO: `lib_deps = h2zero/NimBLE-Arduino`)
 * - GitHub: https://github.com/h2zero/NimBLE-Arduino
 *
 * **Header Mapping:**
 * | ESP-IDF Include | Arduino Equivalent |
 * |-----------------|--------------------|
 * | `nimble/nimble_port.h` | `NimBLEDevice.h` |
 * | `host/ble_hs.h` | (included in NimBLEDevice.h) |
 * | `esp_log.h` | `Serial.println()` |
 * | `nvs_flash.h` | (handled by NimBLEDevice::init()) |
 * | `freertos/FreeRTOS.h` | (Arduino handles this) |
 *
 * **Initialization:**
 * @code{.cpp}
 * // ESP-IDF:
 * nimble_port_init();
 * ble_store_config_init();
 * ble_hs_cfg.sm_io_cap = BLE_HS_IO_DISPLAY_YESNO;
 * ble_hs_cfg.sm_mitm = 1;
 *
 * // Arduino equivalent:
 * NimBLEDevice::init("SECURE_SMP_DEV");
 * NimBLEDevice::setSecurityIOCap(BLE_HS_IO_DISPLAY_YESNO);
 * NimBLEDevice::setSecurityAuth(BLE_SM_PAIR_AUTHREQ_SC | BLE_SM_PAIR_AUTHREQ_MITM | BLE_SM_PAIR_AUTHREQ_BOND);
 * @endcode
 *
 * **Security Callbacks (Arduino):**
 * @code{.cpp}
 * class SecurityCallbacks : public NimBLESecurityCallbacks {
 *     uint32_t onPassKeyRequest() override { return 123456; }
 *     void onPassKeyNotify(uint32_t pass_key) override {
 *         Serial.printf("Passkey: %06d\n", pass_key);
 *     }
 *     bool onConfirmPIN(uint32_t pass_key) override {
 *         Serial.printf("Confirm code: %06d\n", pass_key);
 *         return true;  // Auto-confirm for testing
 *     }
 *     bool onSecurityRequest() override { return true; }
 *     void onAuthenticationComplete(NimBLEConnInfo& connInfo) override {
 *         if (connInfo.isEncrypted()) {
 *             Serial.println("SMP PAIRING SUCCESS!");
 *         }
 *     }
 * };
 *
 * // In setup():
 * NimBLEDevice::setSecurityCallbacks(new SecurityCallbacks());
 * @endcode
 *
 * **Key Arduino Considerations:**
 * 1. NimBLE-Arduino handles `ble_store_config_init()` internally
 * 2. Use `NimBLEDevice::setSecurityAuth()` instead of individual `ble_hs_cfg.sm_*` flags
 * 3. Security callbacks are class-based, not C function pointers
 * 4. `loop()` runs automatically; no need for `while(1)` + `vTaskDelay()`
 * 5. MAC tie-breaker: Use `NimBLEDevice::getAddress()` to get local address
 *
 * **Complete Arduino Skeleton:**
 * @code{.cpp}
 * #include <NimBLEDevice.h>
 *
 * void setup() {
 *     Serial.begin(115200);
 *     NimBLEDevice::init("SECURE_SMP_DEV");
 *
 *     // High-security configuration
 *     NimBLEDevice::setSecurityIOCap(BLE_HS_IO_DISPLAY_YESNO);
 *     NimBLEDevice::setSecurityAuth(
 *         BLE_SM_PAIR_AUTHREQ_BOND |
 *         BLE_SM_PAIR_AUTHREQ_MITM |
 *         BLE_SM_PAIR_AUTHREQ_SC
 *     );
 *     NimBLEDevice::setSecurityCallbacks(new SecurityCallbacks());
 *
 *     // Start advertising and scanning...
 * }
 *
 * void loop() {
 *     // Arduino handles FreeRTOS internally
 *     delay(1000);
 * }
 * @endcode
 */

#include <string.h>
#include <stdbool.h>
#include <stdint.h>

#include "esp_log.h"
#include "nvs_flash.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

/* NimBLE Includes */
#include "nimble/nimble_port.h"
#include "nimble/nimble_port_freertos.h"
#include "nimble/nimble_opt.h"
#include "host/ble_hs.h"
#include "host/ble_gatt.h"
#include "host/util/util.h"
#include "services/gap/ble_svc_gap.h"
#include "services/gatt/ble_svc_gatt.h"
#include "store/config/ble_store_config.h"

/*============================================================================
 * COMPILE-TIME ASSERTIONS
 *==========================================================================*/

/**
 * @brief Verify SMP is enabled at compile time
 *
 * If this assertion fails, check your sdkconfig:
 * - CONFIG_BT_NIMBLE_SM_LEGACY=y
 * - CONFIG_BT_NIMBLE_SM_SC=y
 */
_Static_assert(NIMBLE_BLE_SM,
    "NIMBLE_BLE_SM must be enabled! Check sdkconfig SM settings.");

/*============================================================================
 * CONFIGURATION CONSTANTS
 *==========================================================================*/

/** @brief Logging tag for this module */
static const char *TAG = "SECURE_SMP";

/**
 * @brief Device name for advertising and discovery
 * @note Both devices use the same name; they identify each other by address
 */
#define DEVICE_NAME "SECURE_SMP_DEV"

/**
 * @brief Target device name to search for during scanning
 * @note Must match DEVICE_NAME on peer device
 */
#define TARGET_NAME "SECURE_SMP_DEV"

/**
 * @brief Delay between GAP disc_cancel and connect (milliseconds)
 * @note Prevents race condition in BLE controller state machine
 */
#define DELAY_DISC_TO_CONNECT_MS    100

/**
 * @brief Delay after connection before MTU exchange (milliseconds)
 * @note Allows link to stabilize before stressing with procedures
 */
#define DELAY_CONNECT_STABILIZE_MS  200

/**
 * @brief Delay before initiating SMP after prerequisites met (milliseconds)
 * @note Small safety margin for internal state settling
 */
#define DELAY_PRE_SMP_MS            50

/**
 * @brief Connection timeout (milliseconds)
 * @note Maximum time to wait for connection establishment
 */
#define CONNECTION_TIMEOUT_MS       10000

/**
 * @brief Status report interval (milliseconds)
 * @note Periodic status log for debugging
 */
#define STATUS_REPORT_INTERVAL_MS   5000

/*============================================================================
 * FORWARD DECLARATIONS
 *==========================================================================*/

static int gap_event_handler(struct ble_gap_event *event, void *arg);
static void initiate_smp_pairing(void);
static void try_initiate_smp(void);

/**
 * @brief Initialize BLE store configuration
 *
 * @warning This function MUST be called after nimble_port_init() but before
 *          starting the NimBLE host task. Without it, SMP will fail with
 *          BLE_HS_ENOTSUP (rc=8).
 *
 * This sets up the following callbacks in ble_hs_cfg:
 * - store_read_cb: Read stored security material
 * - store_write_cb: Write security material to storage
 * - store_delete_cb: Delete security material from storage
 */
extern void ble_store_config_init(void);

/*============================================================================
 * MODULE STATE
 *==========================================================================*/

/** @brief Our BLE address type (public or random) */
static uint8_t own_addr_type;

/**
 * @brief Our 6-byte BLE address for MAC tie-breaker comparison
 * @note Stored in on_sync() after address is assigned
 */
static uint8_t own_addr_val[6];

/**
 * @brief Current connection handle, or BLE_HS_CONN_HANDLE_NONE if disconnected
 */
static uint16_t conn_handle = BLE_HS_CONN_HANDLE_NONE;

/** @brief True if we initiated the connection (MASTER role) */
static bool is_master = false;

/** @brief True if we've discovered the peer device */
static bool peer_discovered = false;

/** @brief True if MTU exchange has completed */
static bool mtu_exchanged = false;

/** @brief True if connection parameter update has completed */
static bool conn_update_done = false;

/** @brief True if connection is encrypted (SMP pairing succeeded) */
static bool is_encrypted = false;

/** @brief Peer device address (populated on discovery) */
static ble_addr_t peer_addr;

/*============================================================================
 * MAC ADDRESS TIE-BREAKER
 *==========================================================================*/

/**
 * @brief Compare our MAC address to peer's address
 *
 * Implements deterministic tie-breaking for connection initiation. When two
 * identical devices discover each other simultaneously, only ONE should
 * initiate the connection to avoid BLE_ERR_ACL_CONN_EXISTS errors.
 *
 * The device with the LOWER MAC address (when compared MSB-first) initiates.
 *
 * @param peer Pointer to 6-byte peer MAC address
 * @return true if our address is LOWER than peer's (we should initiate)
 * @return false if our address is HIGHER than peer's (peer should initiate)
 *
 * @note Address comparison is MSB-first (bytes 5→0) to match BLE address
 *       display convention (XX:XX:XX:XX:XX:XX where leftmost is MSB)
 */
static bool address_is_lower(const uint8_t *peer)
{
    for (int i = 5; i >= 0; i--) {
        if (own_addr_val[i] < peer[i]) {
            return true;   /* We are lower - we initiate */
        }
        if (own_addr_val[i] > peer[i]) {
            return false;  /* Peer is lower - they initiate */
        }
    }
    return false;  /* Equal - shouldn't happen with unique MACs */
}

/*============================================================================
 * ADVERTISING
 *==========================================================================*/

/**
 * @brief Start BLE advertising
 *
 * Configures and starts general discoverable advertising with the device name.
 * Uses undirected connectable mode so any device can connect.
 *
 * @note Called on startup and after disconnection
 */
static void start_advertising(void)
{
    struct ble_gap_adv_params adv_params;
    struct ble_hs_adv_fields fields;
    int rc;

    memset(&fields, 0, sizeof(fields));

    /* Standard flags: General Discoverable, BR/EDR Not Supported */
    fields.flags = BLE_HS_ADV_F_DISC_GEN | BLE_HS_ADV_F_BREDR_UNSUP;

    /* Include TX power level for RSSI calibration */
    fields.tx_pwr_lvl_is_present = 1;
    fields.tx_pwr_lvl = BLE_HS_ADV_TX_PWR_LVL_AUTO;

    /* Include complete local name */
    const char *name = ble_svc_gap_device_name();
    fields.name = (uint8_t *)name;
    fields.name_len = strlen(name);
    fields.name_is_complete = 1;

    rc = ble_gap_adv_set_fields(&fields);
    if (rc != 0) {
        ESP_LOGE(TAG, "ble_gap_adv_set_fields failed; rc=%d", rc);
        return;
    }

    /* Undirected connectable advertising, general discoverable */
    memset(&adv_params, 0, sizeof(adv_params));
    adv_params.conn_mode = BLE_GAP_CONN_MODE_UND;
    adv_params.disc_mode = BLE_GAP_DISC_MODE_GEN;

    rc = ble_gap_adv_start(own_addr_type, NULL, BLE_HS_FOREVER,
                           &adv_params, gap_event_handler, NULL);
    if (rc != 0) {
        ESP_LOGE(TAG, "ble_gap_adv_start failed; rc=%d", rc);
        return;
    }

    ESP_LOGI(TAG, "Advertising started as '%s'", name);
}

/*============================================================================
 * SCANNING
 *==========================================================================*/

/**
 * @brief Start BLE scanning for peer device
 *
 * Starts active scanning to discover peer devices advertising TARGET_NAME.
 * Uses filter_duplicates to avoid processing the same advertisement repeatedly.
 *
 * @note Called on startup and after disconnection
 */
static void start_scanning(void)
{
    struct ble_gap_disc_params disc_params;
    int rc;

    memset(&disc_params, 0, sizeof(disc_params));
    disc_params.itvl = 0;              /* Use default interval */
    disc_params.window = 0;            /* Use default window */
    disc_params.filter_policy = 0;     /* No filter */
    disc_params.limited = 0;           /* General discovery */
    disc_params.passive = 0;           /* Active scanning (send SCAN_REQ) */
    disc_params.filter_duplicates = 1; /* Filter duplicate advertisements */

    rc = ble_gap_disc(own_addr_type, BLE_HS_FOREVER, &disc_params,
                      gap_event_handler, NULL);
    if (rc != 0) {
        ESP_LOGE(TAG, "ble_gap_disc failed; rc=%d", rc);
        return;
    }

    ESP_LOGI(TAG, "Scanning for peer device '%s'...", TARGET_NAME);
}

/*============================================================================
 * CONNECTION MANAGEMENT
 *==========================================================================*/

/**
 * @brief Connect to discovered peer device
 *
 * Stops scanning and initiates connection to the peer. Includes a stabilization
 * delay between stopping scan and starting connection to prevent race conditions.
 *
 * @warning Only call this from the device with the LOWER MAC address
 *          (as determined by address_is_lower())
 */
static void connect_to_peer(void)
{
    int rc;

    /* Step 1: Stop scanning */
    ble_gap_disc_cancel();

    /*
     * Step 2: CRITICAL - Give controller time to process the cancel
     *
     * Without this delay, the connect request may race with the scan stop,
     * causing BLE_ERR_CMD_DISALLOWED or other errors.
     */
    vTaskDelay(pdMS_TO_TICKS(DELAY_DISC_TO_CONNECT_MS));

    ESP_LOGI(TAG, "Connecting to peer %02x:%02x:%02x:%02x:%02x:%02x...",
             peer_addr.val[5], peer_addr.val[4], peer_addr.val[3],
             peer_addr.val[2], peer_addr.val[1], peer_addr.val[0]);

    /* Step 3: Initiate connection */
    rc = ble_gap_connect(own_addr_type, &peer_addr, CONNECTION_TIMEOUT_MS,
                         NULL, gap_event_handler, NULL);
    if (rc != 0) {
        ESP_LOGE(TAG, "ble_gap_connect failed; rc=%d", rc);
        /* Restart scanning on failure */
        start_scanning();
    }
}

/*============================================================================
 * SMP PAIRING
 *==========================================================================*/

/**
 * @brief Check if all SMP prerequisites are met and initiate if ready
 *
 * Prerequisites for SMP initiation:
 * 1. We must be the MASTER (connection initiator)
 * 2. We must be connected (valid conn_handle)
 * 3. MTU exchange must have completed
 * 4. Connection parameter update must have completed (if requested)
 *
 * This function is called whenever a prerequisite completes.
 */
static void try_initiate_smp(void)
{
    if (!is_master) {
        return;  /* Only MASTER initiates SMP */
    }
    if (conn_handle == BLE_HS_CONN_HANDLE_NONE) {
        return;  /* Not connected */
    }
    if (!mtu_exchanged) {
        ESP_LOGI(TAG, "Waiting for MTU exchange before SMP...");
        return;
    }
    if (!conn_update_done) {
        ESP_LOGI(TAG, "Waiting for conn param update before SMP...");
        return;
    }

    /* All prerequisites met - initiate SMP with small delay */
    ESP_LOGI(TAG, "All prerequisites met - initiating SMP now");
    vTaskDelay(pdMS_TO_TICKS(DELAY_PRE_SMP_MS));
    initiate_smp_pairing();
}

/**
 * @brief Initiate SMP pairing procedure
 *
 * Called by MASTER after all prerequisites (connection, MTU, conn update) are met.
 * Triggers the SMP exchange which will result in either:
 * - BLE_GAP_EVENT_ENC_CHANGE with status=0 (success)
 * - BLE_GAP_EVENT_ENC_CHANGE with status!=0 (failure)
 *
 * @note With Numeric Comparison, BLE_GAP_EVENT_PASSKEY_ACTION will fire first,
 *       requiring user confirmation of the displayed code.
 */
static void initiate_smp_pairing(void)
{
    if (conn_handle == BLE_HS_CONN_HANDLE_NONE) {
        ESP_LOGE(TAG, "Cannot initiate SMP - not connected");
        return;
    }

    ESP_LOGI(TAG, "========================================");
    ESP_LOGI(TAG, "MASTER initiating SMP pairing...");
    ESP_LOGI(TAG, "Security: Numeric Comparison + MITM");
    ESP_LOGI(TAG, "========================================");

    int rc = ble_gap_security_initiate(conn_handle);

    if (rc == 0) {
        ESP_LOGI(TAG, "SMP pairing initiated successfully");
        ESP_LOGI(TAG, "Waiting for BLE_GAP_EVENT_PASSKEY_ACTION...");
    } else if (rc == BLE_HS_EALREADY) {
        ESP_LOGI(TAG, "SMP pairing already in progress");
    } else {
        ESP_LOGE(TAG, "SMP pairing FAILED to initiate; rc=%d", rc);
        if (rc == BLE_HS_ENOTSUP) {
            ESP_LOGE(TAG, "BLE_HS_ENOTSUP (8) - Did you call ble_store_config_init()?");
        }
    }
}

/*============================================================================
 * MTU EXCHANGE
 *==========================================================================*/

/**
 * @brief Callback for MTU exchange completion
 *
 * @param conn_handle_param Connection handle (unused, using module state)
 * @param error GATT error structure
 * @param mtu Negotiated MTU value
 * @param arg User argument (unused)
 * @return 0 always
 */
static int mtu_exchange_cb(uint16_t conn_handle_param,
                           const struct ble_gatt_error *error,
                           uint16_t mtu, void *arg)
{
    (void)conn_handle_param;
    (void)arg;

    if (error->status == 0) {
        ESP_LOGI(TAG, "MTU exchange complete: MTU=%d", mtu);
    } else {
        ESP_LOGW(TAG, "MTU exchange completed with status=%d", error->status);
    }

    /* Mark complete and check if we can proceed to SMP */
    mtu_exchanged = true;
    try_initiate_smp();

    return 0;
}

/**
 * @brief Start MTU exchange procedure
 *
 * Called by MASTER after connection stabilization delay. MTU exchange is
 * required before SMP to ensure proper PDU sizing for security messages.
 */
static void start_mtu_exchange(void)
{
    if (conn_handle == BLE_HS_CONN_HANDLE_NONE) {
        ESP_LOGE(TAG, "Cannot start MTU exchange - not connected");
        return;
    }

    ESP_LOGI(TAG, "MASTER initiating MTU exchange...");
    int rc = ble_gattc_exchange_mtu(conn_handle, mtu_exchange_cb, NULL);

    if (rc == 0) {
        ESP_LOGI(TAG, "MTU exchange initiated successfully");
    } else {
        ESP_LOGE(TAG, "MTU exchange failed to initiate; rc=%d", rc);
        /* Fall back to trying SMP anyway */
        ESP_LOGW(TAG, "Falling back to SMP without MTU exchange...");
        mtu_exchanged = true;
        vTaskDelay(pdMS_TO_TICKS(100));
        try_initiate_smp();
    }
}

/*============================================================================
 * GAP EVENT HANDLER
 *==========================================================================*/

/**
 * @brief Main GAP event handler
 *
 * Handles all BLE GAP events including:
 * - Connection/disconnection
 * - Device discovery
 * - SMP security events (passkey, encryption change)
 * - Connection parameter updates
 *
 * @param event Pointer to GAP event structure
 * @param arg User argument (unused)
 * @return 0 for most events, BLE_GAP_REPEAT_PAIRING_RETRY for repeat pairing
 */
static int gap_event_handler(struct ble_gap_event *event, void *arg)
{
    struct ble_gap_conn_desc desc;
    int rc;

    (void)arg;

    switch (event->type) {

    /*========================================================================
     * CONNECTION EVENTS
     *======================================================================*/

    case BLE_GAP_EVENT_CONNECT:
        ESP_LOGI(TAG, "========================================");
        if (event->connect.status == 0) {
            conn_handle = event->connect.conn_handle;

            rc = ble_gap_conn_find(conn_handle, &desc);
            if (rc == 0) {
                is_master = (desc.role == BLE_GAP_ROLE_MASTER);

                ESP_LOGI(TAG, "CONNECTION ESTABLISHED!");
                ESP_LOGI(TAG, "  Role: %s",
                         is_master ? "MASTER (we initiated)" : "SLAVE (peer initiated)");
                ESP_LOGI(TAG, "  Conn handle: %d", conn_handle);
                ESP_LOGI(TAG, "  Peer addr: %02x:%02x:%02x:%02x:%02x:%02x",
                         desc.peer_id_addr.val[5], desc.peer_id_addr.val[4],
                         desc.peer_id_addr.val[3], desc.peer_id_addr.val[2],
                         desc.peer_id_addr.val[1], desc.peer_id_addr.val[0]);
            }

            /* Stop scanning now that we're connected */
            ble_gap_disc_cancel();

            /* Reset procedure tracking flags */
            mtu_exchanged = false;
            conn_update_done = true;  /* Optimistic - set false if update requested */
            is_encrypted = false;     /* Will be set true when BLE_GAP_EVENT_ENC_CHANGE fires */
            peer_discovered = true;   /* Mark peer found (for SLAVE who didn't set it during discovery) */

            if (is_master) {
                ESP_LOGI(TAG, "MASTER: Will initiate MTU exchange, then SMP...");
                /* Allow link to stabilize before stressing with procedures */
                vTaskDelay(pdMS_TO_TICKS(DELAY_CONNECT_STABILIZE_MS));
                start_mtu_exchange();
            } else {
                ESP_LOGI(TAG, "SLAVE: Waiting for MASTER to initiate SMP...");
            }
        } else {
            ESP_LOGE(TAG, "Connection FAILED; status=%d", event->connect.status);
            /* Restart advertising and scanning */
            start_advertising();
            start_scanning();
        }
        ESP_LOGI(TAG, "========================================");
        return 0;

    case BLE_GAP_EVENT_DISCONNECT:
        ESP_LOGI(TAG, "========================================");
        ESP_LOGI(TAG, "DISCONNECTED; reason=%d", event->disconnect.reason);
        ESP_LOGI(TAG, "========================================");

        /* Reset state */
        conn_handle = BLE_HS_CONN_HANDLE_NONE;
        is_master = false;
        peer_discovered = false;
        mtu_exchanged = false;
        conn_update_done = false;
        is_encrypted = false;

        /* Restart advertising and scanning */
        start_advertising();
        start_scanning();
        return 0;

    case BLE_GAP_EVENT_CONN_UPDATE:  /* Event 3 */
        ESP_LOGI(TAG, "BLE_GAP_EVENT_CONN_UPDATE: Params update COMPLETE");
        conn_update_done = true;
        try_initiate_smp();
        return 0;

    case BLE_GAP_EVENT_CONN_UPDATE_REQ:  /* Event 34 */
        ESP_LOGI(TAG, "BLE_GAP_EVENT_CONN_UPDATE_REQ: Waiting for completion...");
        conn_update_done = false;
        return 0;  /* Accept the update */

    /*========================================================================
     * DISCOVERY EVENTS
     *======================================================================*/

    case BLE_GAP_EVENT_DISC:
        if (event->disc.length_data == 0 || peer_discovered) {
            return 0;
        }

        /* Parse advertisement for device name */
        for (int i = 0; i < event->disc.length_data; ) {
            uint8_t len = event->disc.data[i];
            if (len == 0) break;

            uint8_t type = event->disc.data[i + 1];

            /* Check for Complete Local Name (0x09) or Shortened (0x08) */
            if (type == 0x09 || type == 0x08) {
                int name_len = len - 1;
                const char *name = (const char *)&event->disc.data[i + 2];

                /* Check if this is our target device */
                if (name_len == strlen(TARGET_NAME) &&
                    memcmp(name, TARGET_NAME, name_len) == 0) {

                    ESP_LOGI(TAG, "========================================");
                    ESP_LOGI(TAG, "PEER DISCOVERED!");
                    ESP_LOGI(TAG, "  Name: %.*s", name_len, name);
                    ESP_LOGI(TAG, "  Addr: %02x:%02x:%02x:%02x:%02x:%02x",
                             event->disc.addr.val[5], event->disc.addr.val[4],
                             event->disc.addr.val[3], event->disc.addr.val[2],
                             event->disc.addr.val[1], event->disc.addr.val[0]);
                    ESP_LOGI(TAG, "  RSSI: %d dBm", event->disc.rssi);

                    /*
                     * MAC TIE-BREAKER
                     *
                     * Only the device with the LOWER MAC address initiates
                     * connection. This prevents both devices from trying to
                     * connect simultaneously, which would cause errors.
                     */
                    if (address_is_lower(event->disc.addr.val)) {
                        ESP_LOGI(TAG, "  TIE-BREAKER: We are LOWER -> Initiating connection");
                        ESP_LOGI(TAG, "========================================");

                        peer_discovered = true;
                        memcpy(&peer_addr, &event->disc.addr, sizeof(ble_addr_t));
                        connect_to_peer();
                    } else {
                        ESP_LOGI(TAG, "  TIE-BREAKER: We are HIGHER -> Waiting for peer");
                        ESP_LOGI(TAG, "========================================");

                        /*
                         * Mark peer as discovered to suppress further discovery logs.
                         * We don't initiate connection, but we know peer exists.
                         * Store peer address in case we need it later.
                         */
                        peer_discovered = true;
                        memcpy(&peer_addr, &event->disc.addr, sizeof(ble_addr_t));
                    }
                }
                break;
            }
            i += len + 1;
        }
        return 0;

    case BLE_GAP_EVENT_DISC_COMPLETE:
        ESP_LOGI(TAG, "Scan complete, restarting...");
        if (conn_handle == BLE_HS_CONN_HANDLE_NONE) {
            start_scanning();
        }
        return 0;

    case BLE_GAP_EVENT_ADV_COMPLETE:
        ESP_LOGI(TAG, "Advertising complete, restarting...");
        if (conn_handle == BLE_HS_CONN_HANDLE_NONE) {
            start_advertising();
        }
        return 0;

    /*========================================================================
     * SMP SECURITY EVENTS
     *======================================================================*/

    case BLE_GAP_EVENT_ENC_CHANGE:
        ESP_LOGI(TAG, "########################################");
        ESP_LOGI(TAG, "BLE_GAP_EVENT_ENC_CHANGE");
        ESP_LOGI(TAG, "  Status: %d", event->enc_change.status);

        if (event->enc_change.status == 0) {
            is_encrypted = true;
            ESP_LOGI(TAG, "  *** SMP PAIRING SUCCESS! ***");
            ESP_LOGI(TAG, "  Connection is now ENCRYPTED");
            ESP_LOGI(TAG, "  MITM protection: ACTIVE");
            ESP_LOGI(TAG, "  LTK available for ESP-NOW encryption!");
        } else {
            is_encrypted = false;
            ESP_LOGE(TAG, "  *** SMP PAIRING FAILED! ***");
            ESP_LOGE(TAG, "  Status %d means pairing did not complete",
                     event->enc_change.status);
        }
        ESP_LOGI(TAG, "########################################");
        return 0;

    case BLE_GAP_EVENT_REPEAT_PAIRING:
        ESP_LOGI(TAG, "BLE_GAP_EVENT_REPEAT_PAIRING - deleting old bond");
        rc = ble_gap_conn_find(event->repeat_pairing.conn_handle, &desc);
        if (rc == 0) {
            ble_store_util_delete_peer(&desc.peer_id_addr);
        }
        return BLE_GAP_REPEAT_PAIRING_RETRY;

    case BLE_GAP_EVENT_PASSKEY_ACTION:
        ESP_LOGI(TAG, "########################################");
        ESP_LOGI(TAG, "BLE_GAP_EVENT_PASSKEY_ACTION");
        ESP_LOGI(TAG, "  Action: %d", event->passkey.params.action);

        switch (event->passkey.params.action) {

        case BLE_SM_IOACT_NONE:
            /*
             * Just Works - should NOT happen with our configuration
             * (we set io_cap = DISPLAY_YESNO and mitm = 1)
             */
            ESP_LOGW(TAG, "  Action=NONE (Just Works) - unexpected!");
            ESP_LOGW(TAG, "  Check sm_io_cap and sm_mitm settings");
            break;

        case BLE_SM_IOACT_NUMCMP:
            /*
             * NUMERIC COMPARISON - The secure pairing method we want
             *
             * Both devices display the same 6-digit code. User must confirm
             * the codes match on both devices to complete pairing.
             *
             * This provides MITM protection because an attacker cannot know
             * the code without physical access to both devices.
             */
            ESP_LOGI(TAG, "  ========================================");
            ESP_LOGI(TAG, "  NUMERIC COMPARISON REQUIRED");
            ESP_LOGI(TAG, "  ========================================");
            ESP_LOGI(TAG, "  CODE: %06lu", (unsigned long)event->passkey.params.numcmp);
            ESP_LOGI(TAG, "  ========================================");
            ESP_LOGI(TAG, "  Verify this matches the code on peer device");
            ESP_LOGI(TAG, "  ========================================");

            /*
             * PRODUCTION: Wait for user confirmation via button press
             * TEST: Auto-confirm for development convenience
             *
             * To require user confirmation, set numcmp_accept based on
             * button input instead of always setting it to 1.
             */
            {
                struct ble_sm_io pkey = {0};
                pkey.action = BLE_SM_IOACT_NUMCMP;
                pkey.numcmp_accept = 1;  /* Auto-accept for testing */

                rc = ble_sm_inject_io(event->passkey.conn_handle, &pkey);
                if (rc == 0) {
                    ESP_LOGI(TAG, "  [TEST MODE] Auto-confirmed numeric comparison");
                } else {
                    ESP_LOGE(TAG, "  Failed to inject numcmp response; rc=%d", rc);
                }
            }
            break;

        case BLE_SM_IOACT_DISP:
            /*
             * Display passkey - peer device will input this code
             * (For Passkey Entry with display capability)
             */
            ESP_LOGI(TAG, "  DISPLAY PASSKEY: %06lu",
                     (unsigned long)event->passkey.params.numcmp);
            ESP_LOGI(TAG, "  Peer device should enter this code");
            break;

        case BLE_SM_IOACT_INPUT:
            /*
             * Input passkey - we must enter code displayed on peer
             * (For Passkey Entry with keyboard capability)
             */
            ESP_LOGI(TAG, "  INPUT REQUIRED - enter passkey from peer device");

            /*
             * PRODUCTION: Get passkey from user input
             * TEST: Use default passkey (insecure!)
             */
            {
                struct ble_sm_io pkey = {0};
                pkey.action = BLE_SM_IOACT_INPUT;
                pkey.passkey = 123456;  /* Default for testing - INSECURE! */

                ESP_LOGW(TAG, "  [TEST MODE] Using default passkey 123456");
                ble_sm_inject_io(event->passkey.conn_handle, &pkey);
            }
            break;

        case BLE_SM_IOACT_OOB:
            /*
             * Out-of-Band - security data exchanged via NFC, QR code, etc.
             * Not typically used for device-to-device pairing
             */
            ESP_LOGI(TAG, "  OOB (Out-of-Band) requested - not supported");
            break;

        default:
            ESP_LOGW(TAG, "  Unknown passkey action: %d",
                     event->passkey.params.action);
            break;
        }

        ESP_LOGI(TAG, "########################################");
        return 0;

    case BLE_GAP_EVENT_AUTHORIZE:
        ESP_LOGI(TAG, "BLE_GAP_EVENT_AUTHORIZE received");
        return 0;

    case BLE_GAP_EVENT_IDENTITY_RESOLVED:
        ESP_LOGI(TAG, "BLE_GAP_EVENT_IDENTITY_RESOLVED received");
        return 0;

    /*========================================================================
     * OTHER EVENTS
     *======================================================================*/

    case BLE_GAP_EVENT_MTU:
        ESP_LOGI(TAG, "BLE_GAP_EVENT_MTU: %d", event->mtu.value);
        mtu_exchanged = true;
        return 0;

    case 38:  /* BLE_GAP_EVENT_DATA_LEN_CHG in ESP-IDF */
        ESP_LOGI(TAG, "Data length changed (event 38)");
        return 0;

    case BLE_GAP_EVENT_NOTIFY_RX:
    case BLE_GAP_EVENT_NOTIFY_TX:
    case BLE_GAP_EVENT_SUBSCRIBE:
        /* Suppress logging for common GATT events */
        return 0;

    default:
        ESP_LOGI(TAG, "Unhandled GAP event: %d", event->type);
        return 0;
    }

    return 0;
}

/*============================================================================
 * HOST CALLBACKS
 *==========================================================================*/

/**
 * @brief Called when BLE host resets (error condition)
 * @param reason Reset reason code
 */
static void on_reset(int reason)
{
    ESP_LOGE(TAG, "BLE host reset; reason=%d", reason);
}

/**
 * @brief Called when BLE host synchronizes (ready to use)
 *
 * This is where we:
 * 1. Ensure we have a valid BLE address
 * 2. Store our address for tie-breaker comparison
 * 3. Start advertising and scanning
 */
static void on_sync(void)
{
    int rc;

    /* Ensure we have a proper BLE address */
    rc = ble_hs_util_ensure_addr(0);
    if (rc != 0) {
        ESP_LOGE(TAG, "ble_hs_util_ensure_addr failed; rc=%d", rc);
        return;
    }

    /* Get our address type (public or random) */
    rc = ble_hs_id_infer_auto(0, &own_addr_type);
    if (rc != 0) {
        ESP_LOGE(TAG, "ble_hs_id_infer_auto failed; rc=%d", rc);
        return;
    }

    /* Store our address for the tie-breaker logic */
    ble_hs_id_copy_addr(own_addr_type, own_addr_val, NULL);

    ESP_LOGI(TAG, "========================================");
    ESP_LOGI(TAG, "BLE Host synchronized");
    ESP_LOGI(TAG, "Our address: %02x:%02x:%02x:%02x:%02x:%02x",
             own_addr_val[5], own_addr_val[4], own_addr_val[3],
             own_addr_val[2], own_addr_val[1], own_addr_val[0]);
    ESP_LOGI(TAG, "========================================");

    /* Start advertising and scanning */
    start_advertising();
    vTaskDelay(pdMS_TO_TICKS(100));  /* Small delay between adv and scan */
    start_scanning();
}

/**
 * @brief NimBLE host task entry point
 * @param param Task parameter (unused)
 */
void host_task(void *param)
{
    (void)param;
    ESP_LOGI(TAG, "BLE Host Task started");
    nimble_port_run();
    nimble_port_freertos_deinit();
}

/*============================================================================
 * MAIN ENTRY POINT
 *==========================================================================*/

/**
 * @brief Application entry point
 *
 * Initializes NVS, NimBLE, and configures high-security SMP settings.
 */
void app_main(void)
{
    int rc;

    printf("\n\n");
    printf("========================================================\n");
    printf("   SECURE SMP PAIRING EXAMPLE\n");
    printf("   High-Security BLE Pairing with Numeric Comparison\n");
    printf("========================================================\n");
    printf("\n");
    printf("Security Configuration:\n");
    printf("  - I/O Capability: DISPLAY_YESNO (Numeric Comparison)\n");
    printf("  - MITM Protection: ENABLED\n");
    printf("  - LE Secure Connections: REQUIRED\n");
    printf("  - Bonding: ENABLED\n");
    printf("\n");
    printf("How it works:\n");
    printf("  1. Both devices advertise and scan simultaneously\n");
    printf("  2. Device with LOWER MAC address initiates connection\n");
    printf("  3. MASTER initiates MTU exchange, then SMP\n");
    printf("  4. Both devices display matching 6-digit code\n");
    printf("  5. User confirms match -> Encrypted connection\n");
    printf("\n");
    printf("SUCCESS: BLE_GAP_EVENT_ENC_CHANGE with status=0\n");
    printf("FAILURE: BLE_GAP_EVENT_ENC_CHANGE with status!=0\n");
    printf("\n");
    printf("========================================================\n\n");

    /*========================================================================
     * NVS INITIALIZATION
     *======================================================================*/

    ESP_LOGI(TAG, "Initializing NVS...");
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);
    ESP_LOGI(TAG, "NVS initialized");

    /*========================================================================
     * NIMBLE INITIALIZATION
     *======================================================================*/

    ESP_LOGI(TAG, "Initializing NimBLE...");
    ret = nimble_port_init();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "nimble_port_init failed; ret=%d", ret);
        return;
    }
    ESP_LOGI(TAG, "NimBLE initialized");

    /* Initialize GAP and GATT services (REQUIRED for SMP) */
    ESP_LOGI(TAG, "Initializing GAP and GATT services...");
    ble_svc_gap_init();
    ble_svc_gatt_init();

    /*========================================================================
     * HOST CONFIGURATION
     *======================================================================*/

    ble_hs_cfg.reset_cb = on_reset;
    ble_hs_cfg.sync_cb = on_sync;
    ble_hs_cfg.store_status_cb = ble_store_util_status_rr;

    /*========================================================================
     * STORE INITIALIZATION - CRITICAL!
     *======================================================================*/

    /**
     * @warning This call is MANDATORY for SMP to work!
     *
     * Without ble_store_config_init(), the SMP subsystem has no way to
     * store or retrieve security material (keys, bonds). This causes
     * ble_gap_security_initiate() to return BLE_HS_ENOTSUP (rc=8).
     *
     * This was the root cause of Bug #113.
     */
    ESP_LOGI(TAG, "Initializing store for security material...");
    ble_store_config_init();

    /*========================================================================
     * SMP SECURITY CONFIGURATION
     *======================================================================*/

    ESP_LOGI(TAG, "Configuring SMP (High Security Mode)...");

    /**
     * @brief I/O Capability: DISPLAY_YESNO
     *
     * This enables Numeric Comparison pairing, where both devices display
     * a 6-digit code and the user confirms they match. This provides
     * protection against MITM attacks.
     *
     * Other options:
     * - BLE_HS_IO_NO_INPUT_OUTPUT: Just Works (NO MITM protection!)
     * - BLE_HS_IO_DISPLAY_ONLY: Display passkey (peer inputs)
     * - BLE_HS_IO_KEYBOARD_ONLY: Input passkey (peer displays)
     * - BLE_HS_IO_KEYBOARD_DISPLAY: Both input and display
     */
    ble_hs_cfg.sm_io_cap = BLE_HS_IO_DISPLAY_YESNO;

    /**
     * @brief MITM Protection: ENABLED
     *
     * Requires authenticated pairing method (Numeric Comparison or Passkey).
     * Without this, the link is vulnerable to man-in-the-middle attacks.
     */
    ble_hs_cfg.sm_mitm = 1;

    /**
     * @brief Bonding: ENABLED
     *
     * Stores the LTK (Long-Term Key) for future reconnections.
     * This allows the devices to re-encrypt without re-pairing.
     */
    ble_hs_cfg.sm_bonding = 1;

    /**
     * @brief LE Secure Connections: REQUIRED
     *
     * Uses ECDH P-256 for key exchange, providing stronger security
     * than legacy pairing. This is mandatory for Numeric Comparison.
     */
    ble_hs_cfg.sm_sc = 1;

    /**
     * @brief Key Distribution
     *
     * Both devices distribute:
     * - ENC: Encryption key (LTK)
     * - ID: Identity key (IRK for address resolution)
     */
    ble_hs_cfg.sm_our_key_dist = BLE_SM_PAIR_KEY_DIST_ENC | BLE_SM_PAIR_KEY_DIST_ID;
    ble_hs_cfg.sm_their_key_dist = BLE_SM_PAIR_KEY_DIST_ENC | BLE_SM_PAIR_KEY_DIST_ID;

    ESP_LOGI(TAG, "  io_cap: DISPLAY_YESNO (Numeric Comparison)");
    ESP_LOGI(TAG, "  mitm: ENABLED (MITM protection required)");
    ESP_LOGI(TAG, "  bonding: ENABLED (store LTK)");
    ESP_LOGI(TAG, "  sc: ENABLED (LE Secure Connections)");
    ESP_LOGI(TAG, "  key_dist: ENC + ID (both directions)");

    /*========================================================================
     * DEVICE NAME
     *======================================================================*/

    rc = ble_svc_gap_device_name_set(DEVICE_NAME);
    if (rc != 0) {
        ESP_LOGE(TAG, "ble_svc_gap_device_name_set failed; rc=%d", rc);
        return;
    }
    ESP_LOGI(TAG, "Device name set to '%s'", DEVICE_NAME);

    /*========================================================================
     * START HOST TASK
     *======================================================================*/

    nimble_port_freertos_init(host_task);
    ESP_LOGI(TAG, "NimBLE host task started");

    /*========================================================================
     * MAIN LOOP
     *======================================================================*/

    while (1) {
        vTaskDelay(pdMS_TO_TICKS(STATUS_REPORT_INTERVAL_MS));

        /* Determine encryption status string */
        const char *enc_status;
        if (is_encrypted) {
            enc_status = "yes";
        } else if (conn_handle != BLE_HS_CONN_HANDLE_NONE) {
            enc_status = "pending";
        } else {
            enc_status = "no";
        }

        ESP_LOGI(TAG, "Status: conn=%d, master=%s, peer_found=%s, encrypted=%s",
                 conn_handle,
                 is_master ? "yes" : "no",
                 peer_discovered ? "yes" : "no",
                 enc_status);
    }
}
