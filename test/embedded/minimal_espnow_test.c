/**
 * @file minimal_espnow_test.c
 * @brief Minimal ESP-NOW test WITHOUT BLE - isolates ESP-NOW functionality
 *
 * Bug #115 Investigation: ESP-NOW TX fails with status=1 even with matching
 * LMK and encryption disabled. This test removes BLE entirely to determine
 * if the issue is BLE/WiFi coexistence or ESP-NOW configuration.
 *
 * APPROACH:
 * 1. Initialize WiFi in STA mode
 * 2. Initialize ESP-NOW with callbacks
 * 3. Broadcast "HELLO" messages periodically
 * 4. When we receive a HELLO, add that device as peer
 * 5. After peer added, send direct messages
 * 6. Log all TX/RX events
 *
 * BUILD: pio run -e minimal_espnow_test -t upload
 *
 * @version 1.0.0
 * @date 2025-12-26
 */

#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_system.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include "esp_wifi.h"
#include "esp_now.h"
#include "esp_mac.h"

static const char *TAG = "ESPNOW_TEST";

/*============================================================================
 * CONFIGURATION
 *==========================================================================*/

/** @brief WiFi channel to use (1-11 for US compatibility) */
#define ESPNOW_CHANNEL          1

/** @brief Broadcast interval in milliseconds */
#define BROADCAST_INTERVAL_MS   2000

/** @brief Direct message interval after peer discovered */
#define DIRECT_MSG_INTERVAL_MS  1000

/** @brief Message types */
#define MSG_TYPE_HELLO          0x01
#define MSG_TYPE_PING           0x02
#define MSG_TYPE_PONG           0x03

/*============================================================================
 * STATE
 *==========================================================================*/

/** @brief Our WiFi MAC address */
static uint8_t local_mac[6];

/** @brief Peer's WiFi MAC address (populated on discovery) */
static uint8_t peer_mac[6];

/** @brief True if peer has been discovered and added */
static volatile bool peer_discovered = false;

/** @brief Message counters */
static uint32_t tx_count = 0;
static uint32_t rx_count = 0;
static uint32_t tx_success = 0;
static uint32_t tx_fail = 0;

/** @brief Broadcast address */
static const uint8_t broadcast_mac[6] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};

/*============================================================================
 * MESSAGE STRUCTURE
 *==========================================================================*/

typedef struct __attribute__((packed)) {
    uint8_t type;           /* MSG_TYPE_* */
    uint8_t sender_mac[6];  /* Sender's MAC for discovery */
    uint32_t counter;       /* Message counter */
} espnow_msg_t;

/*============================================================================
 * ESP-NOW CALLBACKS
 *==========================================================================*/

/**
 * @brief ESP-NOW send callback
 *
 * @note ESP-IDF v5.5+ changed the callback signature from (const uint8_t *mac_addr, ...)
 *       to (const wifi_tx_info_t *tx_info, ...). The MAC is in tx_info->des_addr.
 */
static void espnow_send_cb(const wifi_tx_info_t *tx_info, esp_now_send_status_t status)
{
    const uint8_t *mac_addr = tx_info->des_addr;
    if (status == ESP_NOW_SEND_SUCCESS) {
        tx_success++;
        ESP_LOGI(TAG, "TX SUCCESS to %02x:%02x:%02x:%02x:%02x:%02x (total: %lu/%lu)",
                 mac_addr[0], mac_addr[1], mac_addr[2],
                 mac_addr[3], mac_addr[4], mac_addr[5],
                 (unsigned long)tx_success, (unsigned long)tx_count);
    } else {
        tx_fail++;
        ESP_LOGE(TAG, "TX FAILED to %02x:%02x:%02x:%02x:%02x:%02x (status=%d, fails: %lu/%lu)",
                 mac_addr[0], mac_addr[1], mac_addr[2],
                 mac_addr[3], mac_addr[4], mac_addr[5],
                 status, (unsigned long)tx_fail, (unsigned long)tx_count);
    }
}

/**
 * @brief ESP-NOW receive callback
 */
static void espnow_recv_cb(const esp_now_recv_info_t *recv_info, const uint8_t *data, int len)
{
    const uint8_t *src_mac = recv_info->src_addr;
    rx_count++;

    ESP_LOGI(TAG, "RX from %02x:%02x:%02x:%02x:%02x:%02x len=%d (total rx: %lu)",
             src_mac[0], src_mac[1], src_mac[2],
             src_mac[3], src_mac[4], src_mac[5],
             len, (unsigned long)rx_count);

    if (len < sizeof(espnow_msg_t)) {
        ESP_LOGW(TAG, "  Message too short: %d < %d", len, sizeof(espnow_msg_t));
        return;
    }

    const espnow_msg_t *msg = (const espnow_msg_t *)data;

    switch (msg->type) {
        case MSG_TYPE_HELLO:
            ESP_LOGI(TAG, "  HELLO from %02x:%02x:%02x:%02x:%02x:%02x counter=%lu",
                     msg->sender_mac[0], msg->sender_mac[1], msg->sender_mac[2],
                     msg->sender_mac[3], msg->sender_mac[4], msg->sender_mac[5],
                     (unsigned long)msg->counter);

            /* If we haven't discovered peer yet, add them */
            if (!peer_discovered) {
                /* Verify MAC in message matches source address */
                if (memcmp(msg->sender_mac, src_mac, 6) == 0) {
                    memcpy(peer_mac, src_mac, 6);

                    /* Add peer for direct communication */
                    esp_now_peer_info_t peer_info = {0};
                    memcpy(peer_info.peer_addr, peer_mac, 6);
                    peer_info.channel = ESPNOW_CHANNEL;
                    peer_info.ifidx = WIFI_IF_STA;
                    peer_info.encrypt = false;

                    esp_err_t ret = esp_now_add_peer(&peer_info);
                    if (ret == ESP_OK || ret == ESP_ERR_ESPNOW_EXIST) {
                        peer_discovered = true;
                        ESP_LOGI(TAG, "========================================");
                        ESP_LOGI(TAG, "PEER DISCOVERED!");
                        ESP_LOGI(TAG, "  MAC: %02x:%02x:%02x:%02x:%02x:%02x",
                                 peer_mac[0], peer_mac[1], peer_mac[2],
                                 peer_mac[3], peer_mac[4], peer_mac[5]);
                        ESP_LOGI(TAG, "  Will now send direct PING messages");
                        ESP_LOGI(TAG, "========================================");
                    } else {
                        ESP_LOGE(TAG, "Failed to add peer: %s", esp_err_to_name(ret));
                    }
                }
            }
            break;

        case MSG_TYPE_PING:
            ESP_LOGI(TAG, "  PING #%lu - sending PONG", (unsigned long)msg->counter);
            /* Send PONG response */
            {
                espnow_msg_t pong = {
                    .type = MSG_TYPE_PONG,
                    .counter = msg->counter
                };
                memcpy(pong.sender_mac, local_mac, 6);
                tx_count++;
                esp_now_send(src_mac, (const uint8_t *)&pong, sizeof(pong));
            }
            break;

        case MSG_TYPE_PONG:
            ESP_LOGI(TAG, "  PONG #%lu received!", (unsigned long)msg->counter);
            break;

        default:
            ESP_LOGW(TAG, "  Unknown message type: 0x%02x", msg->type);
            break;
    }
}

/*============================================================================
 * WIFI & ESP-NOW INITIALIZATION
 *==========================================================================*/

/**
 * @brief Initialize WiFi for ESP-NOW
 */
static esp_err_t init_wifi(void)
{
    ESP_LOGI(TAG, "Initializing WiFi...");

    esp_err_t ret = esp_netif_init();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "esp_netif_init failed: %s", esp_err_to_name(ret));
        return ret;
    }

    ret = esp_event_loop_create_default();
    if (ret != ESP_OK && ret != ESP_ERR_INVALID_STATE) {
        ESP_LOGE(TAG, "esp_event_loop_create_default failed: %s", esp_err_to_name(ret));
        return ret;
    }

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ret = esp_wifi_init(&cfg);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "esp_wifi_init failed: %s", esp_err_to_name(ret));
        return ret;
    }

    ret = esp_wifi_set_storage(WIFI_STORAGE_RAM);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "esp_wifi_set_storage failed: %s", esp_err_to_name(ret));
        return ret;
    }

    ret = esp_wifi_set_mode(WIFI_MODE_STA);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "esp_wifi_set_mode failed: %s", esp_err_to_name(ret));
        return ret;
    }

    ret = esp_wifi_start();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "esp_wifi_start failed: %s", esp_err_to_name(ret));
        return ret;
    }

    /* Set WiFi channel */
    ret = esp_wifi_set_channel(ESPNOW_CHANNEL, WIFI_SECOND_CHAN_NONE);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "esp_wifi_set_channel failed: %s", esp_err_to_name(ret));
        return ret;
    }

    /* Get our MAC address */
    ret = esp_read_mac(local_mac, ESP_MAC_WIFI_STA);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "esp_read_mac failed: %s", esp_err_to_name(ret));
        return ret;
    }

    /* Verify channel */
    uint8_t primary_channel;
    wifi_second_chan_t secondary_channel;
    esp_wifi_get_channel(&primary_channel, &secondary_channel);

    ESP_LOGI(TAG, "========================================");
    ESP_LOGI(TAG, "WiFi initialized");
    ESP_LOGI(TAG, "  Local MAC: %02x:%02x:%02x:%02x:%02x:%02x",
             local_mac[0], local_mac[1], local_mac[2],
             local_mac[3], local_mac[4], local_mac[5]);
    ESP_LOGI(TAG, "  Channel: %d (requested: %d)", primary_channel, ESPNOW_CHANNEL);
    ESP_LOGI(TAG, "========================================");

    return ESP_OK;
}

/**
 * @brief Initialize ESP-NOW
 */
static esp_err_t init_espnow(void)
{
    ESP_LOGI(TAG, "Initializing ESP-NOW...");

    esp_err_t ret = esp_now_init();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "esp_now_init failed: %s", esp_err_to_name(ret));
        return ret;
    }

    ret = esp_now_register_send_cb(espnow_send_cb);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "esp_now_register_send_cb failed: %s", esp_err_to_name(ret));
        return ret;
    }

    ret = esp_now_register_recv_cb(espnow_recv_cb);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "esp_now_register_recv_cb failed: %s", esp_err_to_name(ret));
        return ret;
    }

    /* Add broadcast peer for discovery */
    esp_now_peer_info_t broadcast_peer = {0};
    memcpy(broadcast_peer.peer_addr, broadcast_mac, 6);
    broadcast_peer.channel = ESPNOW_CHANNEL;
    broadcast_peer.ifidx = WIFI_IF_STA;
    broadcast_peer.encrypt = false;

    ret = esp_now_add_peer(&broadcast_peer);
    if (ret != ESP_OK && ret != ESP_ERR_ESPNOW_EXIST) {
        ESP_LOGE(TAG, "Failed to add broadcast peer: %s", esp_err_to_name(ret));
        return ret;
    }

    ESP_LOGI(TAG, "ESP-NOW initialized (broadcast peer added)");
    return ESP_OK;
}

/*============================================================================
 * MAIN
 *==========================================================================*/

void app_main(void)
{
    ESP_LOGI(TAG, "========================================");
    ESP_LOGI(TAG, "MINIMAL ESP-NOW TEST");
    ESP_LOGI(TAG, "Bug #115 Investigation - NO BLE");
    ESP_LOGI(TAG, "========================================");

    /* Initialize NVS */
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    /* Initialize WiFi */
    ret = init_wifi();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "WiFi init failed - aborting");
        return;
    }

    /* Initialize ESP-NOW */
    ret = init_espnow();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "ESP-NOW init failed - aborting");
        return;
    }

    ESP_LOGI(TAG, "========================================");
    ESP_LOGI(TAG, "Starting message loop...");
    ESP_LOGI(TAG, "  Broadcasting HELLO every %d ms", BROADCAST_INTERVAL_MS);
    ESP_LOGI(TAG, "  After peer found, PING every %d ms", DIRECT_MSG_INTERVAL_MS);
    ESP_LOGI(TAG, "========================================");

    uint32_t hello_counter = 0;
    uint32_t ping_counter = 0;
    TickType_t last_broadcast = 0;
    TickType_t last_ping = 0;

    while (1) {
        TickType_t now = xTaskGetTickCount();

        if (!peer_discovered) {
            /* Broadcast HELLO for discovery */
            if ((now - last_broadcast) >= pdMS_TO_TICKS(BROADCAST_INTERVAL_MS)) {
                last_broadcast = now;

                espnow_msg_t hello = {
                    .type = MSG_TYPE_HELLO,
                    .counter = ++hello_counter
                };
                memcpy(hello.sender_mac, local_mac, 6);

                ESP_LOGI(TAG, "Broadcasting HELLO #%lu...", (unsigned long)hello_counter);
                tx_count++;
                esp_now_send(broadcast_mac, (const uint8_t *)&hello, sizeof(hello));
            }
        } else {
            /* Send direct PING to peer */
            if ((now - last_ping) >= pdMS_TO_TICKS(DIRECT_MSG_INTERVAL_MS)) {
                last_ping = now;

                espnow_msg_t ping = {
                    .type = MSG_TYPE_PING,
                    .counter = ++ping_counter
                };
                memcpy(ping.sender_mac, local_mac, 6);

                ESP_LOGI(TAG, "Sending PING #%lu to peer...", (unsigned long)ping_counter);
                tx_count++;
                esp_now_send(peer_mac, (const uint8_t *)&ping, sizeof(ping));
            }
        }

        vTaskDelay(pdMS_TO_TICKS(100));
    }
}
