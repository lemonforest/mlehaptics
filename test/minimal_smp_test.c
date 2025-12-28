/*
 * Minimal SMP Pairing Test for ESP32-C6
 *
 * Based on minimal_ble_test.c - simplified to isolate SMP pairing issue
 *
 * Purpose: Test BLE SMP pairing in isolation (Bug #113)
 *
 * How it works:
 *   - Both devices advertise AND scan simultaneously
 *   - First device to discover the other initiates connection (becomes MASTER)
 *   - MASTER initiates SMP pairing after connection
 *   - Both devices should see BLE_GAP_EVENT_ENC_CHANGE with status=0
 *
 * Expected successful output:
 *   "SMP pairing SUCCESS! Connection encrypted"
 *   "LTK available for ESP-NOW encryption"
 *
 * Current issue (Bug #113): SMP times out (status=13), LTK never generated
 */

#include <string.h>
#include "esp_log.h"
#include "nvs_flash.h"
#include "nimble/nimble_port.h"
#include "nimble/nimble_port_freertos.h"
#include "nimble/nimble_opt.h"  // For NIMBLE_BLE_SM
#include "host/ble_hs.h"
#include "host/ble_gatt.h"  // For ble_gattc_exchange_mtu()
#include "host/util/util.h"
#include "services/gap/ble_svc_gap.h"
#include "services/gatt/ble_svc_gatt.h"  // Required for GATT services
// Store configuration - NVS persistence is disabled in sdkconfig (CONFIG_BT_NIMBLE_NVS_PERSIST=n)
// so this uses RAM-only storage, preventing "zombie" bonds across reboots
#include "store/config/ble_store_config.h"

// Compile-time assertion to verify SM is enabled - will fail to compile if NIMBLE_BLE_SM is 0
_Static_assert(NIMBLE_BLE_SM, "NIMBLE_BLE_SM must be enabled for SMP pairing!");

static const char *TAG = "SMP_TEST";

// Device name - both devices use same name (we identify by address)
#define DEVICE_NAME "SMP_TEST_DEV"

// Target device name to connect to
#define TARGET_NAME "SMP_TEST_DEV"

static int gap_event_handler(struct ble_gap_event *event, void *arg);
static void initiate_smp_pairing(void);  // Forward declaration
static void try_initiate_smp(void);       // Forward declaration

// Forward declaration for store init - REQUIRED for SMP to work!
// This sets up the read/write/delete callbacks for security material storage
void ble_store_config_init(void);

static uint8_t own_addr_type;
static uint8_t own_addr_val[6];  // Store our own address for MAC tie-breaker
static uint16_t conn_handle = BLE_HS_CONN_HANDLE_NONE;
static bool is_master = false;  // True if we initiated the connection
static bool peer_discovered = false;
static bool mtu_exchanged = false;      // Wait for MTU before SMP
static bool conn_update_done = false;   // Wait for conn params update to complete
static ble_addr_t peer_addr;

/**
 * MAC Address Tie-Breaker - Compare addresses MSB to LSB
 * Returns true if OUR address is LOWER than peer's address
 * Only the device with the LOWER address initiates the connection
 */
static bool address_is_lower(const uint8_t *peer) {
    for (int i = 5; i >= 0; i--) {  // Compare MSB to LSB
        if (own_addr_val[i] < peer[i]) return true;
        if (own_addr_val[i] > peer[i]) return false;
    }
    return false;  // Equal (shouldn't happen)
}

/**
 * Start advertising
 */
static void start_advertising(void)
{
    struct ble_gap_adv_params adv_params;
    struct ble_hs_adv_fields fields;
    int rc;

    memset(&fields, 0, sizeof(fields));
    fields.flags = BLE_HS_ADV_F_DISC_GEN | BLE_HS_ADV_F_BREDR_UNSUP;
    fields.tx_pwr_lvl_is_present = 1;
    fields.tx_pwr_lvl = BLE_HS_ADV_TX_PWR_LVL_AUTO;

    const char *name = ble_svc_gap_device_name();
    fields.name = (uint8_t *)name;
    fields.name_len = strlen(name);
    fields.name_is_complete = 1;

    rc = ble_gap_adv_set_fields(&fields);
    if (rc != 0) {
        ESP_LOGE(TAG, "Error setting advertisement data; rc=%d", rc);
        return;
    }

    memset(&adv_params, 0, sizeof(adv_params));
    adv_params.conn_mode = BLE_GAP_CONN_MODE_UND;
    adv_params.disc_mode = BLE_GAP_DISC_MODE_GEN;

    rc = ble_gap_adv_start(own_addr_type, NULL, BLE_HS_FOREVER, &adv_params, gap_event_handler, NULL);
    if (rc != 0) {
        ESP_LOGE(TAG, "Error starting advertisement; rc=%d", rc);
        return;
    }

    ESP_LOGI(TAG, "Advertising started as '%s'", name);
}

/**
 * Start scanning for peer device
 */
static void start_scanning(void)
{
    struct ble_gap_disc_params disc_params;
    int rc;

    memset(&disc_params, 0, sizeof(disc_params));
    disc_params.itvl = 0;
    disc_params.window = 0;
    disc_params.filter_policy = 0;
    disc_params.limited = 0;
    disc_params.passive = 0;
    disc_params.filter_duplicates = 1;

    rc = ble_gap_disc(own_addr_type, BLE_HS_FOREVER, &disc_params, gap_event_handler, NULL);
    if (rc != 0) {
        ESP_LOGE(TAG, "Error starting scan; rc=%d", rc);
        return;
    }

    ESP_LOGI(TAG, "Scanning for peer device '%s'...", TARGET_NAME);
}

/**
 * Connect to discovered peer
 */
static void connect_to_peer(void)
{
    int rc;

    // 1. Stop scanning before connecting
    ble_gap_disc_cancel();

    // 2. CRITICAL: Give controller time to process the cancel
    // Prevents race condition between scan stop and connect start
    vTaskDelay(pdMS_TO_TICKS(100));

    ESP_LOGI(TAG, "Connecting to peer %02x:%02x:%02x:%02x:%02x:%02x...",
             peer_addr.val[5], peer_addr.val[4], peer_addr.val[3],
             peer_addr.val[2], peer_addr.val[1], peer_addr.val[0]);

    // 3. Initiate connection
    rc = ble_gap_connect(own_addr_type, &peer_addr, 10000, NULL, gap_event_handler, NULL);
    if (rc != 0) {
        ESP_LOGE(TAG, "Error initiating connection; rc=%d", rc);
        // Restart scanning on failure
        start_scanning();
    }
}

/**
 * Try to initiate SMP if all prerequisites are met
 * Prerequisites: MASTER role, connected, MTU exchanged, conn update done
 */
static void try_initiate_smp(void)
{
    if (!is_master) {
        return;  // Only MASTER initiates SMP
    }
    if (conn_handle == BLE_HS_CONN_HANDLE_NONE) {
        return;  // Not connected
    }
    if (!mtu_exchanged) {
        ESP_LOGI(TAG, "Waiting for MTU exchange before SMP...");
        return;
    }
    if (!conn_update_done) {
        ESP_LOGI(TAG, "Waiting for conn param update before SMP...");
        return;
    }

    // All prerequisites met - initiate SMP
    ESP_LOGI(TAG, "All prerequisites met - initiating SMP now");
    vTaskDelay(pdMS_TO_TICKS(50));  // Small delay for safety
    initiate_smp_pairing();
}

/**
 * MTU exchange callback - called when MTU exchange completes
 * This is when we check if we can initiate SMP pairing
 */
static int mtu_exchange_cb(uint16_t conn_handle_param,
                           const struct ble_gatt_error *error,
                           uint16_t mtu, void *arg)
{
    if (error->status == 0) {
        ESP_LOGI(TAG, "MTU exchange complete: MTU=%d", mtu);
        mtu_exchanged = true;
        try_initiate_smp();
    } else {
        ESP_LOGE(TAG, "MTU exchange failed: status=%d", error->status);
        // Mark as done anyway so we can try SMP
        mtu_exchanged = true;
        try_initiate_smp();
    }
    return 0;
}

/**
 * Start MTU exchange (called by MASTER after connection)
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
        // Fall back to just trying SMP anyway
        ESP_LOGW(TAG, "Falling back to SMP without MTU exchange...");
        vTaskDelay(pdMS_TO_TICKS(100));
        initiate_smp_pairing();
    }
}

/**
 * Initiate SMP pairing (called by MASTER after MTU exchange)
 */
static void initiate_smp_pairing(void)
{
    if (conn_handle == BLE_HS_CONN_HANDLE_NONE) {
        ESP_LOGE(TAG, "Cannot initiate SMP - not connected");
        return;
    }

    ESP_LOGI(TAG, "========================================");
    ESP_LOGI(TAG, "MASTER initiating SMP pairing...");
    ESP_LOGI(TAG, "========================================");

    int rc = ble_gap_security_initiate(conn_handle);
    if (rc == 0) {
        ESP_LOGI(TAG, "SMP pairing initiated successfully");
        ESP_LOGI(TAG, "Waiting for BLE_GAP_EVENT_ENC_CHANGE...");
    } else if (rc == BLE_HS_EALREADY) {
        ESP_LOGI(TAG, "SMP pairing already in progress");
    } else {
        ESP_LOGE(TAG, "SMP pairing FAILED to initiate; rc=%d", rc);
    }
}

/**
 * GAP event handler - handles connection, scanning, and SMP events
 */
static int gap_event_handler(struct ble_gap_event *event, void *arg)
{
    struct ble_gap_conn_desc desc;
    int rc;

    switch (event->type) {

    case BLE_GAP_EVENT_CONNECT:
        ESP_LOGI(TAG, "========================================");
        if (event->connect.status == 0) {
            conn_handle = event->connect.conn_handle;

            rc = ble_gap_conn_find(conn_handle, &desc);
            if (rc == 0) {
                is_master = (desc.role == BLE_GAP_ROLE_MASTER);
                ESP_LOGI(TAG, "CONNECTION ESTABLISHED!");
                ESP_LOGI(TAG, "  Role: %s", is_master ? "MASTER (we initiated)" : "SLAVE (peer initiated)");
                ESP_LOGI(TAG, "  Conn handle: %d", conn_handle);
                ESP_LOGI(TAG, "  Peer addr: %02x:%02x:%02x:%02x:%02x:%02x",
                         desc.peer_id_addr.val[5], desc.peer_id_addr.val[4],
                         desc.peer_id_addr.val[3], desc.peer_id_addr.val[2],
                         desc.peer_id_addr.val[1], desc.peer_id_addr.val[0]);
            }

            // Stop scanning if we're now connected
            ble_gap_disc_cancel();

            // Reset procedure flags
            mtu_exchanged = false;
            // Start optimistic - if no conn update request comes, we're ready
            // If event 34 arrives, it will set this false until event 3 completes
            conn_update_done = true;

            // MASTER initiates MTU exchange, then SMP after all procedures complete
            if (is_master) {
                ESP_LOGI(TAG, "MASTER will initiate MTU exchange, wait for conn update if any, then SMP...");
                // Allow link to stabilize before stressing it with procedures
                vTaskDelay(pdMS_TO_TICKS(200));
                start_mtu_exchange();
            } else {
                ESP_LOGI(TAG, "SLAVE waiting for MASTER to initiate SMP...");
            }
        } else {
            ESP_LOGE(TAG, "Connection FAILED; status=%d", event->connect.status);
            // Restart advertising and scanning
            start_advertising();
            start_scanning();
        }
        ESP_LOGI(TAG, "========================================");
        return 0;

    case BLE_GAP_EVENT_DISCONNECT:
        ESP_LOGI(TAG, "========================================");
        ESP_LOGI(TAG, "DISCONNECTED; reason=%d", event->disconnect.reason);
        ESP_LOGI(TAG, "========================================");
        conn_handle = BLE_HS_CONN_HANDLE_NONE;
        is_master = false;
        peer_discovered = false;
        mtu_exchanged = false;
        conn_update_done = false;
        // Note: RAM-only storage (NVS_PERSIST=0) means bonds are already cleared on reboot
        // Restart advertising and scanning
        start_advertising();
        start_scanning();
        return 0;

    case BLE_GAP_EVENT_DISC:
        // Device discovered during scan
        if (event->disc.length_data > 0 && !peer_discovered) {
            // Parse advertisement for device name
            for (int i = 0; i < event->disc.length_data; ) {
                uint8_t len = event->disc.data[i];
                if (len == 0) break;

                uint8_t type = event->disc.data[i + 1];
                if (type == 0x09 || type == 0x08) {  // Complete or shortened name
                    int name_len = len - 1;
                    const char *name = (const char *)&event->disc.data[i + 2];

                    // Check if this is our target device
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

                        // MAC TIE-BREAKER: Only connect if OUR address is LOWER
                        // This prevents both devices from trying to connect simultaneously
                        if (address_is_lower(event->disc.addr.val)) {
                            ESP_LOGI(TAG, "  TIE-BREAKER: We are LOWER addr -> Initiating connection");
                            ESP_LOGI(TAG, "========================================");

                            peer_discovered = true;
                            memcpy(&peer_addr, &event->disc.addr, sizeof(ble_addr_t));

                            // Connect to peer
                            connect_to_peer();
                        } else {
                            ESP_LOGI(TAG, "  TIE-BREAKER: We are HIGHER addr -> Waiting for peer to connect");
                            ESP_LOGI(TAG, "========================================");
                            // Don't set peer_discovered - keep scanning but don't initiate
                            // The other device will connect to us
                        }
                    }
                    break;
                }
                i += len + 1;
            }
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

    // ========== SMP EVENTS ==========

    case BLE_GAP_EVENT_ENC_CHANGE:
        ESP_LOGI(TAG, "########################################");
        ESP_LOGI(TAG, "BLE_GAP_EVENT_ENC_CHANGE received!");
        ESP_LOGI(TAG, "  Status: %d", event->enc_change.status);
        if (event->enc_change.status == 0) {
            ESP_LOGI(TAG, "  *** SMP PAIRING SUCCESS! ***");
            ESP_LOGI(TAG, "  Connection is now ENCRYPTED");
            ESP_LOGI(TAG, "  LTK available for ESP-NOW encryption!");
        } else {
            ESP_LOGE(TAG, "  *** SMP PAIRING FAILED! ***");
            ESP_LOGE(TAG, "  Status %d means pairing did not complete", event->enc_change.status);
        }
        ESP_LOGI(TAG, "########################################");
        return 0;

    case BLE_GAP_EVENT_REPEAT_PAIRING:
        ESP_LOGI(TAG, "BLE_GAP_EVENT_REPEAT_PAIRING - deleting old bond");
        // Delete old bond and allow re-pairing
        rc = ble_gap_conn_find(event->repeat_pairing.conn_handle, &desc);
        if (rc == 0) {
            ble_store_util_delete_peer(&desc.peer_id_addr);
        }
        return BLE_GAP_REPEAT_PAIRING_RETRY;

    case BLE_GAP_EVENT_PASSKEY_ACTION:
        ESP_LOGI(TAG, "BLE_GAP_EVENT_PASSKEY_ACTION received!");
        ESP_LOGI(TAG, "  Action: %d", event->passkey.params.action);

        // For Just Works (io_cap = NO_INPUT_OUTPUT), this shouldn't be called
        // But if it is, respond appropriately
        if (event->passkey.params.action == BLE_SM_IOACT_NONE) {
            ESP_LOGI(TAG, "  Action=NONE (Just Works), no response needed");
        } else if (event->passkey.params.action == BLE_SM_IOACT_NUMCMP) {
            ESP_LOGI(TAG, "  Action=NUMCMP, passkey=%lu", (unsigned long)event->passkey.params.numcmp);
            // Auto-confirm for testing
            struct ble_sm_io pkey = {0};
            pkey.action = BLE_SM_IOACT_NUMCMP;
            pkey.numcmp_accept = 1;  // Accept the comparison
            ble_sm_inject_io(event->passkey.conn_handle, &pkey);
            ESP_LOGI(TAG, "  Auto-confirmed numeric comparison");
        } else if (event->passkey.params.action == BLE_SM_IOACT_DISP) {
            ESP_LOGI(TAG, "  Action=DISPLAY, showing passkey=%lu", (unsigned long)event->passkey.params.numcmp);
        } else if (event->passkey.params.action == BLE_SM_IOACT_INPUT) {
            ESP_LOGI(TAG, "  Action=INPUT, need to enter passkey");
            // For testing, just use 123456
            struct ble_sm_io pkey = {0};
            pkey.action = BLE_SM_IOACT_INPUT;
            pkey.passkey = 123456;
            ble_sm_inject_io(event->passkey.conn_handle, &pkey);
        }
        return 0;

    case BLE_GAP_EVENT_AUTHORIZE:
        ESP_LOGI(TAG, "BLE_GAP_EVENT_AUTHORIZE received");
        return 0;

    case BLE_GAP_EVENT_IDENTITY_RESOLVED:
        ESP_LOGI(TAG, "BLE_GAP_EVENT_IDENTITY_RESOLVED received");
        return 0;

    case BLE_GAP_EVENT_NOTIFY_RX:
        ESP_LOGI(TAG, "BLE_GAP_EVENT_NOTIFY_RX received");
        return 0;

    case BLE_GAP_EVENT_NOTIFY_TX:
        ESP_LOGI(TAG, "BLE_GAP_EVENT_NOTIFY_TX received");
        return 0;

    case BLE_GAP_EVENT_SUBSCRIBE:
        ESP_LOGI(TAG, "BLE_GAP_EVENT_SUBSCRIBE received");
        return 0;

    case BLE_GAP_EVENT_MTU:
        // Standard NimBLE MTU event (event 9) - may not fire if using callback
        ESP_LOGI(TAG, "BLE_GAP_EVENT_MTU: %d (conn_handle=%d)", event->mtu.value, event->mtu.conn_handle);
        mtu_exchanged = true;
        // Note: We use ble_gattc_exchange_mtu() callback instead, so this may be redundant
        return 0;

    case BLE_GAP_EVENT_CONN_UPDATE:  // Event 3
        ESP_LOGI(TAG, "BLE_GAP_EVENT_CONN_UPDATE (event 3): Connection params update COMPLETE");
        conn_update_done = true;
        try_initiate_smp();  // Check if we can now initiate SMP
        return 0;

    case BLE_GAP_EVENT_CONN_UPDATE_REQ:  // Event 34
        ESP_LOGI(TAG, "BLE_GAP_EVENT_CONN_UPDATE_REQ (event 34): Connection param update REQUESTED (waiting for completion)");
        // Mark as not done - will be set true when event 3 (CONN_UPDATE) arrives
        conn_update_done = false;
        // Accept the update request
        return 0;

    case 38:  // BLE_GAP_EVENT_DATA_LEN_CHG in ESP-IDF NimBLE
        ESP_LOGI(TAG, "BLE_GAP_EVENT_DATA_LEN_CHG (event 38): Data length changed");
        return 0;

    case 31:  // Connection retry/failed attempt
        ESP_LOGI(TAG, "Event 31: Connection attempt event");
        return 0;

    default:
        ESP_LOGI(TAG, "Unhandled GAP event: %d", event->type);
        return 0;
    }

    return 0;
}

static void on_reset(int reason)
{
    ESP_LOGE(TAG, "BLE host reset; reason=%d", reason);
}

static void on_sync(void)
{
    int rc;

    // Ensure we have proper address
    rc = ble_hs_util_ensure_addr(0);
    if (rc != 0) {
        ESP_LOGE(TAG, "ble_hs_util_ensure_addr failed; rc=%d", rc);
        return;
    }

    // Get our address type
    rc = ble_hs_id_infer_auto(0, &own_addr_type);
    if (rc != 0) {
        ESP_LOGE(TAG, "ble_hs_id_infer_auto failed; rc=%d", rc);
        return;
    }

    // Store our address for the tie-breaker logic
    ble_hs_id_copy_addr(own_addr_type, own_addr_val, NULL);

    ESP_LOGI(TAG, "========================================");
    ESP_LOGI(TAG, "BLE Host synchronized");
    ESP_LOGI(TAG, "Our address: %02x:%02x:%02x:%02x:%02x:%02x",
             own_addr_val[5], own_addr_val[4], own_addr_val[3],
             own_addr_val[2], own_addr_val[1], own_addr_val[0]);
    ESP_LOGI(TAG, "========================================");

    // Start advertising and scanning
    start_advertising();
    vTaskDelay(pdMS_TO_TICKS(100));  // Small delay between adv and scan
    start_scanning();
}

void host_task(void *param)
{
    ESP_LOGI(TAG, "BLE Host Task started");
    nimble_port_run();
    nimble_port_freertos_deinit();
}

void app_main(void)
{
    int rc;

    printf("\n\n");
    printf("========================================\n");
    printf("   MINIMAL SMP PAIRING TEST (Bug #113)\n");
    printf("========================================\n");
    printf("\n");
    printf("This test isolates SMP pairing from app complexity.\n");
    printf("Both devices advertise AND scan simultaneously.\n");
    printf("First to discover connects as MASTER and initiates SMP.\n");
    printf("\n");
    printf("SUCCESS looks like:\n");
    printf("  BLE_GAP_EVENT_ENC_CHANGE with status=0\n");
    printf("  'SMP PAIRING SUCCESS! Connection encrypted'\n");
    printf("\n");
    printf("FAILURE looks like:\n");
    printf("  BLE_GAP_EVENT_ENC_CHANGE with status=13 (timeout)\n");
    printf("  Or no ENC_CHANGE event at all\n");
    printf("\n");
    printf("========================================\n\n");

    // Initialize NVS
    ESP_LOGI(TAG, "Initializing NVS...");
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);
    ESP_LOGI(TAG, "NVS initialized");

    // Initialize NimBLE
    ESP_LOGI(TAG, "Initializing NimBLE...");
    ret = nimble_port_init();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "nimble_port_init failed; ret=%d", ret);
        return;
    }
    ESP_LOGI(TAG, "NimBLE initialized");

    // Initialize GAP and GATT services (REQUIRED for SMP to work!)
    ESP_LOGI(TAG, "Initializing GAP and GATT services...");
    ble_svc_gap_init();
    ble_svc_gatt_init();

    // Configure NimBLE host
    ble_hs_cfg.reset_cb = on_reset;
    ble_hs_cfg.sync_cb = on_sync;

    // Set store callbacks for bonding persistence
    ble_hs_cfg.store_status_cb = ble_store_util_status_rr;

    // Initialize store for security material - CRITICAL for SMP!
    // Without this, ble_gap_security_initiate() returns BLE_HS_ENOTSUP (rc=8)
    ESP_LOGI(TAG, "Initializing store for security material...");
    ble_store_config_init();

    // SMP Configuration - Just Works (no passkey)
    ESP_LOGI(TAG, "Configuring SMP (Just Works mode)...");
    ble_hs_cfg.sm_io_cap = BLE_HS_IO_NO_INPUT_OUTPUT;  // Just Works
    ble_hs_cfg.sm_bonding = 1;                          // Enable bonding
    ble_hs_cfg.sm_mitm = 0;                             // No MITM (Just Works)
    ble_hs_cfg.sm_sc = 1;                               // LE Secure Connections
    ble_hs_cfg.sm_our_key_dist = BLE_SM_PAIR_KEY_DIST_ENC | BLE_SM_PAIR_KEY_DIST_ID;
    ble_hs_cfg.sm_their_key_dist = BLE_SM_PAIR_KEY_DIST_ENC | BLE_SM_PAIR_KEY_DIST_ID;
    ESP_LOGI(TAG, "  io_cap: NO_INPUT_OUTPUT (Just Works)");
    ESP_LOGI(TAG, "  bonding: enabled");
    ESP_LOGI(TAG, "  mitm: disabled");
    ESP_LOGI(TAG, "  sc: enabled (LE Secure Connections)");

    // Set device name
    rc = ble_svc_gap_device_name_set(DEVICE_NAME);
    if (rc != 0) {
        ESP_LOGE(TAG, "ble_svc_gap_device_name_set failed; rc=%d", rc);
        return;
    }
    ESP_LOGI(TAG, "Device name set to '%s'", DEVICE_NAME);

    // Start NimBLE host task
    nimble_port_freertos_init(host_task);
    ESP_LOGI(TAG, "NimBLE host task started");

    // Main loop - just keep alive
    while (1) {
        vTaskDelay(pdMS_TO_TICKS(5000));
        ESP_LOGI(TAG, "Status: conn_handle=%d, is_master=%s, peer_discovered=%s",
                 conn_handle,
                 is_master ? "yes" : "no",
                 peer_discovered ? "yes" : "no");
    }
}
