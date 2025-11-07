/*
 * Minimal WiFi Test for ESP32-C6
 *
 * Purpose: Test if the 2.4GHz radio hardware is functional
 * WiFi and BLE use the same radio hardware - if WiFi works, radio is fine
 * This test just scans for WiFi networks and reports them
 */

#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/event_groups.h"
#include "esp_log.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "nvs_flash.h"

static const char *TAG = "WIFI_TEST";

static void wifi_scan_done_handler(void* arg, esp_event_base_t event_base,
                                   int32_t event_id, void* event_data)
{
    uint16_t number = 0;
    wifi_ap_record_t *ap_info = NULL;

    ESP_LOGI(TAG, "WiFi scan completed");

    // Get number of APs found
    ESP_ERROR_CHECK(esp_wifi_scan_get_ap_num(&number));
    ESP_LOGI(TAG, "Total APs found: %d", number);

    if (number > 0) {
        ap_info = malloc(sizeof(wifi_ap_record_t) * number);
        if (ap_info == NULL) {
            ESP_LOGE(TAG, "Failed to allocate memory for AP list");
            return;
        }

        ESP_ERROR_CHECK(esp_wifi_scan_get_ap_records(&number, ap_info));

        printf("\n=== WiFi Networks Found ===\n");
        for (int i = 0; i < number; i++) {
            printf("%d: SSID: %-32s | RSSI: %d | Channel: %d\n",
                   i + 1, ap_info[i].ssid, ap_info[i].rssi, ap_info[i].primary);
        }
        printf("===========================\n\n");

        free(ap_info);

        ESP_LOGI(TAG, "✓ WiFi scan successful - 2.4GHz radio hardware is working!");
    } else {
        ESP_LOGW(TAG, "No WiFi networks found - check if WiFi networks are nearby");
    }
}

void app_main(void)
{
    printf("\n\n=== MINIMAL WIFI TEST FOR ESP32-C6 ===\n");
    printf("Purpose: Verify 2.4GHz radio hardware functionality\n");
    printf("Note: WiFi and BLE use the same radio hardware\n\n");

    ESP_LOGI(TAG, "Starting WiFi hardware test...");

    // Step 1: Initialize NVS
    printf("Step 1: Initializing NVS...\n");
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);
    ESP_LOGI(TAG, "✓ NVS initialized");

    // Step 2: Initialize network interface
    printf("Step 2: Initializing network interface...\n");
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_LOGI(TAG, "✓ Network interface initialized");

    // Step 3: Create default event loop
    printf("Step 3: Creating event loop...\n");
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    ESP_LOGI(TAG, "✓ Event loop created");

    // Step 4: Create default WiFi STA
    printf("Step 4: Creating WiFi station interface...\n");
    esp_netif_t *sta_netif = esp_netif_create_default_wifi_sta();
    if (sta_netif == NULL) {
        ESP_LOGE(TAG, "Failed to create WiFi station interface");
        return;
    }
    ESP_LOGI(TAG, "✓ WiFi station interface created");

    // Step 5: Initialize WiFi
    printf("Step 5: Initializing WiFi...\n");
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ret = esp_wifi_init(&cfg);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "WiFi init failed: %s", esp_err_to_name(ret));
        return;
    }
    ESP_LOGI(TAG, "✓ WiFi initialized");

    // Step 6: Register event handler for scan done
    printf("Step 6: Registering scan completion handler...\n");
    ESP_ERROR_CHECK(esp_event_handler_register(WIFI_EVENT, WIFI_EVENT_SCAN_DONE,
                                               &wifi_scan_done_handler, NULL));
    ESP_LOGI(TAG, "✓ Event handler registered");

    // Step 7: Set WiFi mode to station
    printf("Step 7: Setting WiFi mode to station...\n");
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_LOGI(TAG, "✓ WiFi mode set to station");

    // Step 8: Start WiFi
    printf("Step 8: Starting WiFi...\n");
    ret = esp_wifi_start();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "WiFi start failed: %s", esp_err_to_name(ret));
        return;
    }
    ESP_LOGI(TAG, "✓ WiFi started");

    printf("\n=== WIFI INITIALIZATION COMPLETE ===\n");
    printf("Starting WiFi scan...\n\n");

    // Step 9: Start scan
    wifi_scan_config_t scan_config = {
        .ssid = NULL,
        .bssid = NULL,
        .channel = 0,
        .show_hidden = false,
        .scan_type = WIFI_SCAN_TYPE_ACTIVE,
        .scan_time.active.min = 0,
        .scan_time.active.max = 0,
    };

    ESP_ERROR_CHECK(esp_wifi_scan_start(&scan_config, false));
    ESP_LOGI(TAG, "WiFi scan in progress...");

    // Wait for scan to complete and repeat every 10 seconds
    while (1) {
        vTaskDelay(pdMS_TO_TICKS(10000));
        ESP_LOGI(TAG, "Starting another scan...");
        esp_wifi_scan_start(&scan_config, false);
    }
}
