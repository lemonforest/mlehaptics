/**
 * @file espnow_transport.c
 * @brief ESP-NOW Transport Layer Implementation
 *
 * @see espnow_transport.h for API documentation
 * @date December 2025
 * @author Claude Code (Anthropic)
 */

#include "espnow_transport.h"
#include "role_manager.h"  // Bug #41: Role-aware TDM (CLIENT skips TDM)
#include "esp_wifi.h"
#include "esp_now.h"
#include "esp_timer.h"
#include "esp_log.h"
#include "esp_mac.h"
#include "esp_random.h"
#include "nvs_flash.h"
#include <string.h>
#include <math.h>

// mbedTLS for hardware-accelerated HKDF-SHA256
#include "mbedtls/hkdf.h"
#include "mbedtls/md.h"

// FreeRTOS for TDM scheduling delays
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "ESPNOW";

// Broadcast MAC address for UTLP time beacons (no ACK expected)
static const uint8_t ESPNOW_BROADCAST_MAC[6] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};

// ============================================================================
// MODULE STATE (JPL Rule 1: Static allocation)
// ============================================================================

static struct {
    espnow_state_t state;
    uint8_t peer_mac[6];              // Unicast peer for coordination messages
    bool peer_configured;              // Unicast peer registered
    bool broadcast_configured;         // Broadcast peer registered for beacons
    bool encryption_enabled;
    espnow_beacon_callback_t beacon_callback;
    espnow_coordination_callback_t coordination_callback;
    espnow_metrics_t metrics;
    bool wifi_initialized;
} s_espnow = {
    .state = ESPNOW_STATE_UNINITIALIZED,
    .peer_configured = false,
    .broadcast_configured = false,
    .encryption_enabled = false,
    .beacon_callback = NULL,
    .coordination_callback = NULL,
    .wifi_initialized = false
};

// ============================================================================
// PRIVATE FUNCTIONS
// ============================================================================

/**
 * @brief Update jitter statistics (running variance algorithm)
 */
static void update_jitter_stats(int64_t jitter_us)
{
    // Add to ring buffer
    uint8_t idx = s_espnow.metrics.jitter_head;

    // Remove old value from sums if buffer is full
    if (s_espnow.metrics.jitter_count == ESPNOW_JITTER_WINDOW_SIZE) {
        int64_t old_val = s_espnow.metrics.jitter_samples[idx];
        s_espnow.metrics.jitter_sum -= old_val;
        s_espnow.metrics.jitter_sum_sq -= (old_val * old_val);
    }

    // Add new value
    s_espnow.metrics.jitter_samples[idx] = jitter_us;
    s_espnow.metrics.jitter_sum += jitter_us;
    s_espnow.metrics.jitter_sum_sq += (jitter_us * jitter_us);

    // Update head
    s_espnow.metrics.jitter_head = (idx + 1) % ESPNOW_JITTER_WINDOW_SIZE;
    if (s_espnow.metrics.jitter_count < ESPNOW_JITTER_WINDOW_SIZE) {
        s_espnow.metrics.jitter_count++;
    }
}

/**
 * @brief ESP-NOW receive callback (runs in WiFi task context)
 *
 * Routes incoming packets based on type:
 * - Beacons: 25 bytes, starts with server_time_us
 * - Coordination: Variable length, starts with 0xC0 marker
 */
static void espnow_recv_cb(const esp_now_recv_info_t *recv_info,
                           const uint8_t *data,
                           int len)
{
    // Capture receive timestamp immediately
    uint64_t rx_time_us = esp_timer_get_time();

    // Bug #43 diagnostic: Log ALL ESP-NOW packet arrivals at INFO level
    ESP_LOGI(TAG, "ESP-NOW RX: %d bytes from %02X:%02X:%02X:%02X:%02X:%02X",
             len,
             recv_info->src_addr[0], recv_info->src_addr[1], recv_info->src_addr[2],
             recv_info->src_addr[3], recv_info->src_addr[4], recv_info->src_addr[5]);

    // Verify sender is our peer
    if (s_espnow.peer_configured) {
        if (memcmp(recv_info->src_addr, s_espnow.peer_mac, 6) != 0) {
            ESP_LOGW(TAG, "Ignoring packet from unknown sender (expected %02X:%02X:%02X:%02X:%02X:%02X)",
                     s_espnow.peer_mac[0], s_espnow.peer_mac[1], s_espnow.peer_mac[2],
                     s_espnow.peer_mac[3], s_espnow.peer_mac[4], s_espnow.peer_mac[5]);
            return;
        }
    }

    // Route based on packet type
    // Coordination messages start with 0xC0 marker byte
    if (len > 0 && data[0] == ESPNOW_PKT_TYPE_COORDINATION) {
        // Coordination message (PTP, asymmetry probes)
        if (s_espnow.coordination_callback != NULL && len > 1) {
            // Pass message data without the marker byte
            s_espnow.coordination_callback(data + 1, len - 1, rx_time_us);
        }
        ESP_LOGD(TAG, "Coordination msg received via ESP-NOW (%d bytes)", len - 1);
        return;
    }

    // Beacon message - validate size
    if (len != sizeof(time_sync_beacon_t)) {
        ESP_LOGW(TAG, "Unexpected packet size: %d (expected %zu for beacon)",
                 len, sizeof(time_sync_beacon_t));
        return;
    }

    // Update metrics (beacons only)
    s_espnow.metrics.beacons_received++;
    s_espnow.metrics.last_actual_us = rx_time_us;

    // Calculate jitter if we have expected time
    if (s_espnow.metrics.last_expected_us > 0) {
        int64_t jitter = (int64_t)rx_time_us - (int64_t)s_espnow.metrics.last_expected_us;
        update_jitter_stats(jitter);
    }

    // Deliver to callback
    if (s_espnow.beacon_callback != NULL) {
        const time_sync_beacon_t *beacon = (const time_sync_beacon_t *)data;
        s_espnow.beacon_callback(beacon, rx_time_us);
    }

    ESP_LOGD(TAG, "Beacon received via ESP-NOW (seq: %u)",
             ((const time_sync_beacon_t *)data)->sequence);
}

/**
 * @brief ESP-NOW send callback (confirms transmission)
 *
 * Note: ESP-IDF v5.5.0 changed the callback signature to use wifi_tx_info_t
 */
static void espnow_send_cb(const wifi_tx_info_t *tx_info, esp_now_send_status_t status)
{
    if (status == ESP_NOW_SEND_SUCCESS) {
        ESP_LOGD(TAG, "ESP-NOW send success");
    } else {
        // Bug #43 diagnostic: Log detailed channel and WiFi state info
        uint8_t primary_chan = 0;
        wifi_second_chan_t second_chan;
        wifi_mode_t mode;
        esp_wifi_get_channel(&primary_chan, &second_chan);
        esp_wifi_get_mode(&mode);
        ESP_LOGW(TAG, "ESP-NOW send failed (channel=%d, mode=%d, peer=%02X:%02X:%02X:%02X:%02X:%02X)",
                 primary_chan, mode,
                 s_espnow.peer_mac[0], s_espnow.peer_mac[1], s_espnow.peer_mac[2],
                 s_espnow.peer_mac[3], s_espnow.peer_mac[4], s_espnow.peer_mac[5]);
        s_espnow.metrics.send_failures++;
    }
}

/**
 * @brief Initialize WiFi in STA mode for ESP-NOW
 */
static esp_err_t wifi_init_for_espnow(void)
{
    if (s_espnow.wifi_initialized) {
        return ESP_OK;
    }

    // Initialize WiFi with default config
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    esp_err_t ret = esp_wifi_init(&cfg);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "WiFi init failed: %s", esp_err_to_name(ret));
        return ret;
    }

    // Set storage to RAM (don't persist WiFi config to NVS)
    ret = esp_wifi_set_storage(WIFI_STORAGE_RAM);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "WiFi storage config failed: %s", esp_err_to_name(ret));
        return ret;
    }

    // Set mode to STA (required for ESP-NOW)
    ret = esp_wifi_set_mode(WIFI_MODE_STA);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "WiFi set mode failed: %s", esp_err_to_name(ret));
        return ret;
    }

    // Start WiFi
    ret = esp_wifi_start();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "WiFi start failed: %s", esp_err_to_name(ret));
        return ret;
    }

    // Set channel for ESP-NOW
    ret = esp_wifi_set_channel(ESPNOW_CHANNEL, WIFI_SECOND_CHAN_NONE);
    if (ret != ESP_OK) {
        ESP_LOGW(TAG, "WiFi set channel failed: %s (may be set by scan)",
                 esp_err_to_name(ret));
        // Not fatal - channel can be set dynamically
    }

    // Configure long-range mode for better reliability
    ret = esp_wifi_set_protocol(WIFI_IF_STA,
                                WIFI_PROTOCOL_11B |
                                WIFI_PROTOCOL_11G |
                                WIFI_PROTOCOL_11N |
                                WIFI_PROTOCOL_LR);
    if (ret != ESP_OK) {
        ESP_LOGW(TAG, "WiFi LR mode config failed: %s", esp_err_to_name(ret));
        // Not fatal - proceed without LR
    }

    s_espnow.wifi_initialized = true;
    ESP_LOGI(TAG, "WiFi initialized for ESP-NOW (channel %d)", ESPNOW_CHANNEL);

    return ESP_OK;
}

// ============================================================================
// PUBLIC API IMPLEMENTATION
// ============================================================================

esp_err_t espnow_transport_init(void)
{
    if (s_espnow.state != ESPNOW_STATE_UNINITIALIZED) {
        ESP_LOGW(TAG, "Already initialized");
        return ESP_OK;
    }

    ESP_LOGI(TAG, "Initializing ESP-NOW transport...");

    // Initialize WiFi first
    esp_err_t ret = wifi_init_for_espnow();
    if (ret != ESP_OK) {
        s_espnow.state = ESPNOW_STATE_ERROR;
        return ret;
    }

    // Initialize ESP-NOW
    ret = esp_now_init();
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "ESP-NOW init failed: %s", esp_err_to_name(ret));
        s_espnow.state = ESPNOW_STATE_ERROR;
        return ret;
    }

    // Register callbacks
    ret = esp_now_register_recv_cb(espnow_recv_cb);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Register recv callback failed: %s", esp_err_to_name(ret));
        esp_now_deinit();
        s_espnow.state = ESPNOW_STATE_ERROR;
        return ret;
    }

    ret = esp_now_register_send_cb(espnow_send_cb);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Register send callback failed: %s", esp_err_to_name(ret));
        esp_now_deinit();
        s_espnow.state = ESPNOW_STATE_ERROR;
        return ret;
    }

    // Clear metrics
    memset(&s_espnow.metrics, 0, sizeof(s_espnow.metrics));

    // Register broadcast peer for UTLP time beacons (no ACK expected)
    // This allows fire-and-forget beacon transmission per UTLP design
    esp_now_peer_info_t broadcast_peer = {0};
    memcpy(broadcast_peer.peer_addr, ESPNOW_BROADCAST_MAC, 6);
    broadcast_peer.channel = ESPNOW_CHANNEL;
    broadcast_peer.ifidx = WIFI_IF_STA;
    broadcast_peer.encrypt = false;  // Broadcast cannot be encrypted

    ret = esp_now_add_peer(&broadcast_peer);
    if (ret != ESP_OK) {
        ESP_LOGW(TAG, "Add broadcast peer failed: %s (non-fatal)", esp_err_to_name(ret));
        // Non-fatal - beacons will fall back to unicast if needed
    } else {
        s_espnow.broadcast_configured = true;
        ESP_LOGI(TAG, "Broadcast peer registered for UTLP time beacons");
    }

    s_espnow.state = ESPNOW_STATE_READY;

    // Log local MAC for debugging
    uint8_t mac[6];
    espnow_transport_get_local_mac(mac);
    ESP_LOGI(TAG, "ESP-NOW initialized. Local MAC: %02X:%02X:%02X:%02X:%02X:%02X",
             mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);

    return ESP_OK;
}

esp_err_t espnow_transport_deinit(void)
{
    if (s_espnow.state == ESPNOW_STATE_UNINITIALIZED) {
        return ESP_OK;
    }

    esp_now_deinit();

    // Note: We don't deinit WiFi as it might be used by other components
    // and BLE/WiFi coexistence should remain active

    s_espnow.state = ESPNOW_STATE_UNINITIALIZED;
    s_espnow.peer_configured = false;

    ESP_LOGI(TAG, "ESP-NOW transport deinitialized");
    return ESP_OK;
}

esp_err_t espnow_transport_set_peer(const uint8_t peer_mac[6])
{
    if (peer_mac == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    if (s_espnow.state == ESPNOW_STATE_UNINITIALIZED ||
        s_espnow.state == ESPNOW_STATE_ERROR) {
        ESP_LOGE(TAG, "Cannot set peer: transport not initialized");
        return ESP_ERR_INVALID_STATE;
    }

    // Remove existing peer if any
    if (s_espnow.peer_configured) {
        esp_now_del_peer(s_espnow.peer_mac);
    }

    // Configure peer info
    esp_now_peer_info_t peer_info = {0};
    memcpy(peer_info.peer_addr, peer_mac, 6);
    peer_info.channel = ESPNOW_CHANNEL;
    peer_info.ifidx = WIFI_IF_STA;
    peer_info.encrypt = false;  // No encryption for now (BLE handles security)

    esp_err_t ret = esp_now_add_peer(&peer_info);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Add peer failed: %s", esp_err_to_name(ret));
        return ret;
    }

    // Store peer MAC
    memcpy(s_espnow.peer_mac, peer_mac, 6);
    s_espnow.peer_configured = true;
    s_espnow.state = ESPNOW_STATE_PEER_SET;

    // Bug #43: Re-synchronize WiFi channel after BLE operations
    // BLE scanning/connection may have changed WiFi channel state
    uint8_t current_chan = 0;
    wifi_second_chan_t second_chan;
    esp_wifi_get_channel(&current_chan, &second_chan);

    if (current_chan != ESPNOW_CHANNEL) {
        ESP_LOGW(TAG, "WiFi channel mismatch: current=%d, expected=%d - re-setting",
                 current_chan, ESPNOW_CHANNEL);
        esp_err_t ch_ret = esp_wifi_set_channel(ESPNOW_CHANNEL, WIFI_SECOND_CHAN_NONE);
        if (ch_ret != ESP_OK) {
            ESP_LOGE(TAG, "Failed to re-set WiFi channel: %s", esp_err_to_name(ch_ret));
        } else {
            ESP_LOGI(TAG, "WiFi channel re-set to %d", ESPNOW_CHANNEL);
        }
    }

    ESP_LOGI(TAG, "Peer configured: %02X:%02X:%02X:%02X:%02X:%02X (peer_channel=%d, wifi_channel=%d)",
             peer_mac[0], peer_mac[1], peer_mac[2],
             peer_mac[3], peer_mac[4], peer_mac[5],
             ESPNOW_CHANNEL, current_chan);

    return ESP_OK;
}

esp_err_t espnow_transport_clear_peer(void)
{
    if (s_espnow.peer_configured) {
        esp_now_del_peer(s_espnow.peer_mac);
        memset(s_espnow.peer_mac, 0, 6);
        s_espnow.peer_configured = false;
        s_espnow.encryption_enabled = false;

        if (s_espnow.state == ESPNOW_STATE_PEER_SET) {
            s_espnow.state = ESPNOW_STATE_READY;
        }

        ESP_LOGI(TAG, "Peer cleared");
    }

    return ESP_OK;
}

esp_err_t espnow_transport_register_callback(espnow_beacon_callback_t callback)
{
    s_espnow.beacon_callback = callback;
    return ESP_OK;
}

esp_err_t espnow_transport_send_beacon(const time_sync_beacon_t *beacon)
{
    if (beacon == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    // UTLP Design: Time beacons use broadcast (no ACK expected)
    // "Shout the time, don't care who hears" - fire and forget
    // This eliminates ACK contention with BLE and always succeeds
    if (!s_espnow.broadcast_configured) {
        // Fallback to unicast if broadcast not available
        if (!s_espnow.peer_configured) {
            ESP_LOGW(TAG, "Cannot send beacon: no peer configured");
            return ESP_ERR_INVALID_STATE;
        }
        // Use unicast (legacy path)
        esp_err_t ret = esp_now_send(s_espnow.peer_mac,
                                      (const uint8_t *)beacon,
                                      sizeof(time_sync_beacon_t));
        if (ret != ESP_OK) {
            ESP_LOGE(TAG, "ESP-NOW beacon send failed: %s", esp_err_to_name(ret));
            s_espnow.metrics.send_failures++;
            return ESP_FAIL;
        }
        s_espnow.metrics.beacons_sent++;
        ESP_LOGD(TAG, "Beacon sent via ESP-NOW unicast (seq: %u)", beacon->sequence);
        return ESP_OK;
    }

    // Record expected arrival time for jitter calculation
    // Assuming ~1ms one-way latency for ESP-NOW
    s_espnow.metrics.last_expected_us = esp_timer_get_time() + 1000;

    // Send beacon via broadcast - no ACK, no contention, always succeeds
    esp_err_t ret = esp_now_send(ESPNOW_BROADCAST_MAC,
                                  (const uint8_t *)beacon,
                                  sizeof(time_sync_beacon_t));
    if (ret != ESP_OK) {
        // This should rarely fail (only if ESP-NOW not ready)
        ESP_LOGE(TAG, "ESP-NOW broadcast failed: %s", esp_err_to_name(ret));
        s_espnow.metrics.send_failures++;
        return ESP_FAIL;
    }

    s_espnow.metrics.beacons_sent++;

    ESP_LOGD(TAG, "Beacon broadcast via ESP-NOW (seq: %u)", beacon->sequence);
    return ESP_OK;
}

espnow_state_t espnow_transport_get_state(void)
{
    return s_espnow.state;
}

esp_err_t espnow_transport_get_local_mac(uint8_t mac_out[6])
{
    if (mac_out == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    return esp_read_mac(mac_out, ESP_MAC_WIFI_STA);
}

const espnow_metrics_t* espnow_transport_get_metrics(void)
{
    return &s_espnow.metrics;
}

void espnow_transport_log_jitter_stats(void)
{
    if (s_espnow.metrics.jitter_count == 0) {
        ESP_LOGI(TAG, "Jitter stats: No samples collected");
        return;
    }

    // Calculate mean
    double mean = (double)s_espnow.metrics.jitter_sum /
                  (double)s_espnow.metrics.jitter_count;

    // Calculate variance and stddev
    double variance = ((double)s_espnow.metrics.jitter_sum_sq /
                       (double)s_espnow.metrics.jitter_count) - (mean * mean);
    double stddev = sqrt(variance > 0 ? variance : 0);

    ESP_LOGI(TAG, "═══════════════════════════════════════════════════");
    ESP_LOGI(TAG, "  ESP-NOW Jitter Statistics");
    ESP_LOGI(TAG, "═══════════════════════════════════════════════════");
    ESP_LOGI(TAG, "  Samples:     %u", s_espnow.metrics.jitter_count);
    ESP_LOGI(TAG, "  Mean jitter: %.1f μs", mean);
    ESP_LOGI(TAG, "  Std dev:     %.1f μs", stddev);
    ESP_LOGI(TAG, "  Sent:        %lu beacons", s_espnow.metrics.beacons_sent);
    ESP_LOGI(TAG, "  Received:    %lu beacons", s_espnow.metrics.beacons_received);
    ESP_LOGI(TAG, "  Failures:    %lu", s_espnow.metrics.send_failures);
    ESP_LOGI(TAG, "═══════════════════════════════════════════════════");
}

bool espnow_transport_is_ready(void)
{
    return s_espnow.state == ESPNOW_STATE_PEER_SET && s_espnow.peer_configured;
}

// ============================================================================
// COORDINATION MESSAGE IMPLEMENTATION
// ============================================================================

esp_err_t espnow_transport_register_coordination_callback(espnow_coordination_callback_t callback)
{
    s_espnow.coordination_callback = callback;
    ESP_LOGI(TAG, "Coordination callback %s",
             callback ? "registered" : "cleared");
    return ESP_OK;
}

esp_err_t espnow_transport_send_coordination(const uint8_t *data, size_t len)
{
    if (data == NULL || len == 0) {
        return ESP_ERR_INVALID_ARG;
    }

    if (!s_espnow.peer_configured) {
        ESP_LOGW(TAG, "Cannot send coordination: no peer configured");
        return ESP_ERR_INVALID_STATE;
    }

    // Build packet: [0xC0 marker][coordination message bytes]
    // Use stack buffer - coordination messages are small (<100 bytes)
    uint8_t pkt[ESPNOW_MAX_PAYLOAD];
    if (len + 1 > ESPNOW_MAX_PAYLOAD) {
        ESP_LOGE(TAG, "Coordination message too large: %zu > %u",
                 len, ESPNOW_MAX_PAYLOAD - 1);
        return ESP_ERR_INVALID_ARG;
    }

    pkt[0] = ESPNOW_PKT_TYPE_COORDINATION;
    memcpy(pkt + 1, data, len);

    // Bug #43: Retry logic for ESP-NOW send failures
    esp_err_t ret = ESP_FAIL;
    for (uint8_t retry = 0; retry < ESPNOW_COORD_MAX_RETRIES; retry++) {
        if (retry > 0) {
            vTaskDelay(pdMS_TO_TICKS(ESPNOW_COORD_RETRY_DELAY_MS));
            ESP_LOGD(TAG, "ESP-NOW coordination retry %u/%u", retry + 1, ESPNOW_COORD_MAX_RETRIES);
        }

        ret = esp_now_send(s_espnow.peer_mac, pkt, len + 1);
        if (ret == ESP_OK) {
            break;  // Success
        }
    }

    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "ESP-NOW coordination send failed after %u retries: %s",
                 ESPNOW_COORD_MAX_RETRIES, esp_err_to_name(ret));
        s_espnow.metrics.send_failures++;
        return ESP_FAIL;
    }

    ESP_LOGD(TAG, "Coordination msg sent via ESP-NOW (%zu bytes)", len);
    return ESP_OK;
}

// ============================================================================
// TDM SCHEDULING IMPLEMENTATION (BLE/ESP-NOW Coexistence)
// ============================================================================

/**
 * @brief Check if currently in TDM safe window for ESP-NOW
 *
 * BLE connection events occur at regular intervals (50ms).
 * Safe window is centered at the midpoint between events.
 *
 * Timeline: |---BLE---||--------SAFE--------|---BLE---||--------SAFE--------|
 *           0         5       15-35          50        55      65-85         100
 */
bool espnow_transport_is_tdm_safe(void)
{
    // Get current time in milliseconds
    uint32_t now_ms = (uint32_t)(esp_timer_get_time() / 1000);

    // Calculate position within BLE interval
    uint32_t phase = now_ms % ESPNOW_TDM_BLE_INTERVAL_MS;

    // Safe window is centered at ESPNOW_TDM_SAFE_OFFSET_MS (25ms)
    // Window spans from (offset - window/2) to (offset + window/2)
    uint32_t window_start = ESPNOW_TDM_SAFE_OFFSET_MS - (ESPNOW_TDM_SAFE_WINDOW_MS / 2);
    uint32_t window_end = ESPNOW_TDM_SAFE_OFFSET_MS + (ESPNOW_TDM_SAFE_WINDOW_MS / 2);

    return (phase >= window_start && phase <= window_end);
}

/**
 * @brief Wait until next TDM safe window
 *
 * Calculates time until midpoint of next BLE interval and waits.
 */
uint32_t espnow_transport_wait_for_tdm_safe(void)
{
    uint32_t now_ms = (uint32_t)(esp_timer_get_time() / 1000);
    uint32_t phase = now_ms % ESPNOW_TDM_BLE_INTERVAL_MS;

    // Calculate delay to reach safe window center
    uint32_t delay_ms;
    if (phase < ESPNOW_TDM_SAFE_OFFSET_MS) {
        // Haven't reached safe window yet in this interval
        delay_ms = ESPNOW_TDM_SAFE_OFFSET_MS - phase;
    } else {
        // Past safe window, wait for next interval
        delay_ms = (ESPNOW_TDM_BLE_INTERVAL_MS - phase) + ESPNOW_TDM_SAFE_OFFSET_MS;
    }

    if (delay_ms > 0) {
        ESP_LOGD(TAG, "TDM: Waiting %lu ms for safe window (phase=%lu)",
                 (unsigned long)delay_ms, (unsigned long)phase);
        vTaskDelay(pdMS_TO_TICKS(delay_ms));
    }

    return delay_ms;
}

/**
 * @brief Send coordination message with TDM scheduling
 *
 * Waits for TDM-safe window, then sends via ESP-NOW unicast.
 * This minimizes radio contention with BLE connection events.
 */
esp_err_t espnow_transport_send_coordination_tdm(const uint8_t *data, size_t len)
{
    if (data == NULL || len == 0) {
        return ESP_ERR_INVALID_ARG;
    }

    if (!s_espnow.peer_configured) {
        ESP_LOGW(TAG, "Cannot send coordination: no peer configured");
        return ESP_ERR_INVALID_STATE;
    }

    // Bug #41: Role-aware TDM scheduling
    // - SERVER: Maintains BLE for PWA access, needs TDM to avoid BLE/ESP-NOW contention
    // - CLIENT: BLE stopped after bootstrap (Bug #7), no contention → skip TDM wait
    uint32_t waited = 0;
    if (role_get_current() == ROLE_SERVER) {
        // SERVER has BLE + ESP-NOW coexistence - wait for TDM safe window
        waited = espnow_transport_wait_for_tdm_safe();
        if (waited > 0) {
            ESP_LOGD(TAG, "TDM: SERVER delayed %lu ms for safe window", (unsigned long)waited);
        }
    }
    // CLIENT: Send immediately (no BLE activity after bootstrap)

    // Build packet: [0xC0 marker][coordination message bytes]
    uint8_t pkt[ESPNOW_MAX_PAYLOAD];
    if (len + 1 > ESPNOW_MAX_PAYLOAD) {
        ESP_LOGE(TAG, "Coordination message too large: %zu > %u",
                 len, ESPNOW_MAX_PAYLOAD - 1);
        return ESP_ERR_INVALID_ARG;
    }

    pkt[0] = ESPNOW_PKT_TYPE_COORDINATION;
    memcpy(pkt + 1, data, len);

    // Bug #43: Retry logic for ESP-NOW send failures (with TDM)
    esp_err_t ret = ESP_FAIL;
    for (uint8_t retry = 0; retry < ESPNOW_COORD_MAX_RETRIES; retry++) {
        if (retry > 0) {
            // On retry, wait for next TDM safe window (SERVER only)
            if (role_get_current() == ROLE_SERVER) {
                waited += espnow_transport_wait_for_tdm_safe();
            } else {
                vTaskDelay(pdMS_TO_TICKS(ESPNOW_COORD_RETRY_DELAY_MS));
            }
            ESP_LOGD(TAG, "ESP-NOW TDM coordination retry %u/%u", retry + 1, ESPNOW_COORD_MAX_RETRIES);
        }

        ret = esp_now_send(s_espnow.peer_mac, pkt, len + 1);
        if (ret == ESP_OK) {
            break;  // Success
        }
    }

    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "ESP-NOW TDM coordination send failed after %u retries: %s",
                 ESPNOW_COORD_MAX_RETRIES, esp_err_to_name(ret));
        s_espnow.metrics.send_failures++;
        return ESP_FAIL;
    }

    ESP_LOGD(TAG, "Coordination msg sent via ESP-NOW with TDM (%zu bytes, waited %lu ms)",
             len, (unsigned long)waited);
    return ESP_OK;
}

// ============================================================================
// SECURE KEY DERIVATION IMPLEMENTATION
// ============================================================================

esp_err_t espnow_transport_generate_key_exchange(espnow_key_exchange_t *key_exchange)
{
    if (key_exchange == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    if (s_espnow.state == ESPNOW_STATE_UNINITIALIZED ||
        s_espnow.state == ESPNOW_STATE_ERROR) {
        ESP_LOGE(TAG, "Cannot generate key exchange: transport not initialized");
        return ESP_ERR_INVALID_STATE;
    }

    // Generate cryptographically random nonce from hardware RNG
    esp_fill_random(key_exchange->nonce, ESPNOW_NONCE_SIZE);

    // Include our WiFi MAC for verification on CLIENT side
    esp_err_t ret = esp_read_mac(key_exchange->server_mac, ESP_MAC_WIFI_STA);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to read WiFi MAC: %s", esp_err_to_name(ret));
        return ret;
    }

    ESP_LOGI(TAG, "Key exchange generated: nonce[0..3]=%02X%02X%02X%02X",
             key_exchange->nonce[0], key_exchange->nonce[1],
             key_exchange->nonce[2], key_exchange->nonce[3]);

    return ESP_OK;
}

esp_err_t espnow_transport_derive_session_key(
    const uint8_t server_mac[6],
    const uint8_t client_mac[6],
    const uint8_t nonce[ESPNOW_NONCE_SIZE],
    uint8_t lmk_out[ESPNOW_KEY_SIZE])
{
    if (server_mac == NULL || client_mac == NULL ||
        nonce == NULL || lmk_out == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    // Build input keying material: SERVER_MAC || CLIENT_MAC || nonce
    // Total: 6 + 6 + 8 = 20 bytes
    uint8_t ikm[20];
    memcpy(ikm, server_mac, 6);
    memcpy(ikm + 6, client_mac, 6);
    memcpy(ikm + 12, nonce, ESPNOW_NONCE_SIZE);

    // Get SHA-256 message digest info for HKDF
    const mbedtls_md_info_t *md_info = mbedtls_md_info_from_type(MBEDTLS_MD_SHA256);
    if (md_info == NULL) {
        ESP_LOGE(TAG, "Failed to get SHA-256 MD info");
        return ESP_FAIL;
    }

    // Derive 16-byte LMK using HKDF-SHA256
    // Note: No salt used (NULL, 0) - the nonce provides uniqueness
    // Info string provides domain separation for this specific use case
    int ret = mbedtls_hkdf(
        md_info,
        NULL, 0,                                    // salt (optional)
        ikm, sizeof(ikm),                           // input keying material
        (const uint8_t *)ESPNOW_HKDF_INFO,          // info string
        strlen(ESPNOW_HKDF_INFO),                   // info length
        lmk_out, ESPNOW_KEY_SIZE                    // output key
    );

    // Zero out sensitive input keying material
    memset(ikm, 0, sizeof(ikm));

    if (ret != 0) {
        ESP_LOGE(TAG, "HKDF derivation failed: -0x%04X", -ret);
        return ESP_FAIL;
    }

    ESP_LOGI(TAG, "Session LMK derived (nonce): [%02X%02X...%02X%02X]",
             lmk_out[0], lmk_out[1],
             lmk_out[ESPNOW_KEY_SIZE - 2], lmk_out[ESPNOW_KEY_SIZE - 1]);

    return ESP_OK;
}

esp_err_t espnow_transport_derive_key_from_ltk(
    const uint8_t ltk[ESPNOW_LTK_SIZE],
    const uint8_t server_mac[6],
    const uint8_t client_mac[6],
    uint8_t lmk_out[ESPNOW_KEY_SIZE])
{
    if (ltk == NULL || server_mac == NULL || client_mac == NULL || lmk_out == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    // Build input keying material: LTK || SERVER_MAC || CLIENT_MAC
    // Total: 16 + 6 + 6 = 28 bytes
    // LTK provides 128-bit entropy (vs 64-bit from nonce approach)
    // MACs provide binding to specific device pair
    uint8_t ikm[28];
    memcpy(ikm, ltk, ESPNOW_LTK_SIZE);
    memcpy(ikm + 16, server_mac, 6);
    memcpy(ikm + 22, client_mac, 6);

    // Get SHA-256 message digest info for HKDF
    const mbedtls_md_info_t *md_info = mbedtls_md_info_from_type(MBEDTLS_MD_SHA256);
    if (md_info == NULL) {
        ESP_LOGE(TAG, "Failed to get SHA-256 MD info");
        memset(ikm, 0, sizeof(ikm));
        return ESP_FAIL;
    }

    // Derive 16-byte LMK using HKDF-SHA256
    // Note: No salt needed - LTK already has 128-bit entropy from SMP
    // Info string "v2" distinguishes from legacy nonce-based derivation
    int ret = mbedtls_hkdf(
        md_info,
        NULL, 0,                                    // salt (not needed with high-entropy IKM)
        ikm, sizeof(ikm),                           // input keying material
        (const uint8_t *)ESPNOW_HKDF_INFO,          // info string ("EMDR-ESP-NOW-LMK-v2")
        strlen(ESPNOW_HKDF_INFO),                   // info length
        lmk_out, ESPNOW_KEY_SIZE                    // output key
    );

    // Zero out sensitive input keying material
    memset(ikm, 0, sizeof(ikm));

    if (ret != 0) {
        ESP_LOGE(TAG, "HKDF (LTK) derivation failed: -0x%04X", -ret);
        return ESP_FAIL;
    }

    ESP_LOGI(TAG, "Session LMK derived (LTK-based): [%02X%02X...%02X%02X]",
             lmk_out[0], lmk_out[1],
             lmk_out[ESPNOW_KEY_SIZE - 2], lmk_out[ESPNOW_KEY_SIZE - 1]);

    return ESP_OK;
}

esp_err_t espnow_transport_set_peer_encrypted(
    const uint8_t peer_mac[6],
    const uint8_t lmk[ESPNOW_KEY_SIZE])
{
    if (peer_mac == NULL || lmk == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    if (s_espnow.state == ESPNOW_STATE_UNINITIALIZED ||
        s_espnow.state == ESPNOW_STATE_ERROR) {
        ESP_LOGE(TAG, "Cannot set encrypted peer: transport not initialized");
        return ESP_ERR_INVALID_STATE;
    }

    // Remove existing peer if any
    if (s_espnow.peer_configured) {
        esp_now_del_peer(s_espnow.peer_mac);
    }

    // Configure peer with encryption
    esp_now_peer_info_t peer_info = {0};
    memcpy(peer_info.peer_addr, peer_mac, 6);
    peer_info.channel = ESPNOW_CHANNEL;
    peer_info.ifidx = WIFI_IF_STA;
    peer_info.encrypt = true;  // Enable encryption
    memcpy(peer_info.lmk, lmk, ESPNOW_KEY_SIZE);

    esp_err_t ret = esp_now_add_peer(&peer_info);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Add encrypted peer failed: %s", esp_err_to_name(ret));
        return ret;
    }

    // Store peer MAC and update state
    memcpy(s_espnow.peer_mac, peer_mac, 6);
    s_espnow.peer_configured = true;
    s_espnow.encryption_enabled = true;
    s_espnow.state = ESPNOW_STATE_PEER_SET;

    // Log current WiFi channel for diagnostics
    uint8_t current_chan = 0;
    wifi_second_chan_t second_chan;
    esp_wifi_get_channel(&current_chan, &second_chan);
    ESP_LOGI(TAG, "Encrypted peer configured: %02X:%02X:%02X:%02X:%02X:%02X (peer_channel=%d, wifi_channel=%d)",
             peer_mac[0], peer_mac[1], peer_mac[2],
             peer_mac[3], peer_mac[4], peer_mac[5],
             ESPNOW_CHANNEL, current_chan);

    return ESP_OK;
}

bool espnow_transport_is_encrypted(void)
{
    return s_espnow.peer_configured && s_espnow.encryption_enabled;
}
