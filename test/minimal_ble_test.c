/*
 * Minimal BLE Test for ESP32-C6 with Scanner
 *
 * Based on official ESP-IDF bleprph example, simplified for diagnostic testing
 * Source: esp-idf/examples/bluetooth/nimble/bleprph/main/main.c
 *
 * Purpose: Test BLE initialization, advertising, AND scanning for nearby devices
 * Features:
 *  - Advertises as "ESP32C6_BLE_TEST"
 *  - Scans for nearby BLE devices every 10 seconds
 *  - Displays device addresses and RSSI (signal strength)
 *  - Useful for testing PCB case RF attenuation
 *
 * Key change: Removed manual BT controller initialization - nimble_port_init() handles it
 */

#include "esp_log.h"
#include "nvs_flash.h"
/* BLE */
#include "nimble/nimble_port.h"
#include "nimble/nimble_port_freertos.h"
#include "host/ble_hs.h"
#include "host/util/util.h"
#include "services/gap/ble_svc_gap.h"

static const char *TAG = "BLE_TEST";

static int bleprph_gap_event(struct ble_gap_event *event, void *arg);
static uint8_t own_addr_type;
static bool scan_in_progress = false;

/**
 * Enables advertising with the following parameters:
 *     o General discoverable mode.
 *     o Undirected connectable mode.
 */
static void
bleprph_advertise(void)
{
    struct ble_gap_adv_params adv_params;
    struct ble_hs_adv_fields fields;
    const char *name;
    int rc;

    /**
     *  Set the advertisement data included in our advertisements:
     *     o Flags (indicates advertisement type and other general info).
     *     o Advertising tx power.
     *     o Device name.
     */

    memset(&fields, 0, sizeof fields);

    /* Advertise two flags:
     *     o Discoverability in forthcoming advertisement (general)
     *     o BLE-only (BR/EDR unsupported).
     */
    fields.flags = BLE_HS_ADV_F_DISC_GEN |
                   BLE_HS_ADV_F_BREDR_UNSUP;

    /* Indicate that the TX power level field should be included; have the
     * stack fill this value automatically.  This is done by assigning the
     * special value BLE_HS_ADV_TX_PWR_LVL_AUTO.
     */
    fields.tx_pwr_lvl_is_present = 1;
    fields.tx_pwr_lvl = BLE_HS_ADV_TX_PWR_LVL_AUTO;

    name = ble_svc_gap_device_name();
    fields.name = (uint8_t *)name;
    fields.name_len = strlen(name);
    fields.name_is_complete = 1;

    rc = ble_gap_adv_set_fields(&fields);
    if (rc != 0) {
        ESP_LOGE(TAG, "error setting advertisement data; rc=%d\n", rc);
        return;
    }

    /* Begin advertising. */
    memset(&adv_params, 0, sizeof adv_params);
    adv_params.conn_mode = BLE_GAP_CONN_MODE_UND;
    adv_params.disc_mode = BLE_GAP_DISC_MODE_GEN;
    rc = ble_gap_adv_start(own_addr_type, NULL, BLE_HS_FOREVER,
                           &adv_params, bleprph_gap_event, NULL);
    if (rc != 0) {
        ESP_LOGE(TAG, "error enabling advertisement; rc=%d\n", rc);
        return;
    }

    ESP_LOGI(TAG, "✓ Advertising started successfully!");
}

/**
 * The nimble host executes this callback when a GAP event occurs.  The
 * application associates a GAP event callback with each connection that forms.
 * bleprph uses the same callback for all connections.
 */
static int
bleprph_gap_event(struct ble_gap_event *event, void *arg)
{
    switch (event->type) {
    case BLE_GAP_EVENT_CONNECT:
        /* A new connection was established or a connection attempt failed. */
        ESP_LOGI(TAG, "connection %s; status=%d",
                    event->connect.status == 0 ? "established" : "failed",
                    event->connect.status);

        if (event->connect.status != 0) {
            /* Connection failed; resume advertising. */
            bleprph_advertise();
        }
        return 0;

    case BLE_GAP_EVENT_DISCONNECT:
        ESP_LOGI(TAG, "disconnect; reason=%d", event->disconnect.reason);

        /* Connection terminated; resume advertising. */
        bleprph_advertise();
        return 0;

    case BLE_GAP_EVENT_ADV_COMPLETE:
        ESP_LOGI(TAG, "advertise complete; reason=%d",
                    event->adv_complete.reason);
        bleprph_advertise();
        return 0;
    }

    return 0;
}

/**
 * BLE scan event handler - called for each discovered device
 */
static int
ble_scan_event(struct ble_gap_event *event, void *arg)
{
    struct ble_gap_disc_desc *disc;

    switch (event->type) {
    case BLE_GAP_EVENT_DISC:
        /* Device discovered during scan */
        disc = &event->disc;

        /* Print device address and RSSI (signal strength) */
        ESP_LOGI(TAG, "Device found: %02x:%02x:%02x:%02x:%02x:%02x  RSSI: %d dBm",
                 disc->addr.val[5], disc->addr.val[4], disc->addr.val[3],
                 disc->addr.val[2], disc->addr.val[1], disc->addr.val[0],
                 disc->rssi);

        /* If device has a name, print it */
        if (disc->length_data > 0) {
            // Parse advertisement data for device name (type 0x09 = complete local name)
            for (int i = 0; i < disc->length_data; ) {
                uint8_t len = disc->data[i];
                if (len == 0) break;

                uint8_t type = disc->data[i + 1];
                if (type == 0x09 || type == 0x08) {  // Complete or shortened name
                    ESP_LOGI(TAG, "  Name: %.*s", len - 1, &disc->data[i + 2]);
                    break;
                }
                i += len + 1;
            }
        }
        break;

    case BLE_GAP_EVENT_DISC_COMPLETE:
        ESP_LOGI(TAG, "Scan complete");
        scan_in_progress = false;
        break;
    }

    return 0;
}

/**
 * Start BLE scan for nearby devices
 */
static void
ble_scan_start(void)
{
    if (scan_in_progress) {
        ESP_LOGW(TAG, "Scan already in progress");
        return;
    }

    struct ble_gap_disc_params disc_params;
    int rc;

    /* Set scan parameters */
    memset(&disc_params, 0, sizeof(disc_params));
    disc_params.itvl = 0;  // Use default interval
    disc_params.window = 0;  // Use default window
    disc_params.filter_policy = 0;  // No whitelist
    disc_params.limited = 0;  // General discovery
    disc_params.passive = 0;  // Active scan (request scan response)
    disc_params.filter_duplicates = 1;  // Filter duplicate advertisements

    ESP_LOGI(TAG, "Starting BLE scan...");

    /* Start scan for 5 seconds */
    rc = ble_gap_disc(own_addr_type, 5000, &disc_params, ble_scan_event, NULL);
    if (rc != 0) {
        ESP_LOGE(TAG, "Error starting scan; rc=%d", rc);
        return;
    }

    scan_in_progress = true;
}

static void
bleprph_on_reset(int reason)
{
    ESP_LOGE(TAG, "Resetting state; reason=%d\n", reason);
}

static void
bleprph_on_sync(void)
{
    int rc;

    /* Make sure we have proper identity address set (public preferred) */
    rc = ble_hs_util_ensure_addr(0);
    if (rc != 0) {
        ESP_LOGE(TAG, "ensure_addr failed; rc=%d\n", rc);
        return;
    }

    /* Figure out address to use while advertising (no privacy for now) */
    rc = ble_hs_id_infer_auto(0, &own_addr_type);
    if (rc != 0) {
        ESP_LOGE(TAG, "error determining address type; rc=%d\n", rc);
        return;
    }

    /* Printing ADDR */
    uint8_t addr_val[6] = {0};
    rc = ble_hs_id_copy_addr(own_addr_type, addr_val, NULL);

    ESP_LOGI(TAG, "Device Address: %02x:%02x:%02x:%02x:%02x:%02x",
             addr_val[5], addr_val[4], addr_val[3],
             addr_val[2], addr_val[1], addr_val[0]);

    /* Begin advertising. */
    bleprph_advertise();

    /* Start first scan after a short delay to let advertising stabilize */
    vTaskDelay(pdMS_TO_TICKS(2000));
    ble_scan_start();
}

void bleprph_host_task(void *param)
{
    ESP_LOGI(TAG, "BLE Host Task Started");
    /* This function will return only when nimble_port_stop() is executed */
    nimble_port_run();

    nimble_port_freertos_deinit();
}

void
app_main(void)
{
    int rc;

    printf("\n\n=== MINIMAL BLE TEST FOR ESP32-C6 ===\n");
    printf("Based on official ESP-IDF bleprph example\n");
    printf("Key difference: NO manual BT controller init\n\n");

    /* Initialize NVS — it is used to store PHY calibration data */
    ESP_LOGI(TAG, "Step 1: Initializing NVS...");
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);
    ESP_LOGI(TAG, "✓ NVS initialized");

    /* Initialize NimBLE (this internally handles BT controller init) */
    ESP_LOGI(TAG, "Step 2: Initializing NimBLE port...");
    ret = nimble_port_init();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to init nimble %d ", ret);
        return;
    }
    ESP_LOGI(TAG, "✓ NimBLE port initialized");

    /* Initialize the NimBLE host configuration. */
    ESP_LOGI(TAG, "Step 3: Configuring NimBLE host...");
    ble_hs_cfg.reset_cb = bleprph_on_reset;
    ble_hs_cfg.sync_cb = bleprph_on_sync;
    ESP_LOGI(TAG, "✓ NimBLE host configured");

    /* Set the default device name. */
    ESP_LOGI(TAG, "Step 4: Setting device name...");
    rc = ble_svc_gap_device_name_set("ESP32C6_BLE_TEST");
    if (rc != 0) {
        ESP_LOGE(TAG, "Failed to set device name; rc=%d", rc);
        return;
    }
    ESP_LOGI(TAG, "✓ Device name set to 'ESP32C6_BLE_TEST'");

    /* Start NimBLE host task */
    ESP_LOGI(TAG, "Step 5: Starting NimBLE host task...");
    nimble_port_freertos_init(bleprph_host_task);
    ESP_LOGI(TAG, "✓ NimBLE host task started");

    ESP_LOGI(TAG, "\n=== BLE INITIALIZATION COMPLETE ===");
    ESP_LOGI(TAG, "Device should now be advertising as 'ESP32C6_BLE_TEST'");
    ESP_LOGI(TAG, "Scan for this device with a BLE scanner app\n");
    ESP_LOGI(TAG, "This device will scan for nearby BLE devices every 15 seconds");
    ESP_LOGI(TAG, "RSSI values indicate signal strength (higher = stronger signal)\n");

    /* Main loop - scan every 15 seconds (5s scan + 10s delay) */
    while (1) {
        vTaskDelay(pdMS_TO_TICKS(10000));
        ESP_LOGI(TAG, "✓ BLE test still running...");

        /* Trigger another scan if previous one completed */
        if (!scan_in_progress) {
            vTaskDelay(pdMS_TO_TICKS(5000));  // Wait 5 more seconds
            ble_scan_start();
        }
    }
}
