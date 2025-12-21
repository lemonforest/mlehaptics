/**
 * @file espnow_transport.h
 * @brief ESP-NOW Transport Layer for UTLP Time Synchronization
 *
 * Provides low-latency beacon transport using ESP-NOW protocol.
 * ESP-NOW offers sub-millisecond latency (±100μs jitter) compared to
 * BLE's typical 50-100ms latency with outliers.
 *
 * Architecture:
 * - Runs alongside BLE (WiFi/BLE coexistence enabled)
 * - BLE handles PWA connectivity + coordination messages
 * - ESP-NOW handles time sync beacons for maximum timing precision
 *
 * Usage Flow:
 * 1. Call espnow_transport_init() during system init
 * 2. Exchange WiFi MAC addresses during BLE pairing
 * 3. Call espnow_transport_set_peer() with peer's MAC
 * 4. Use espnow_transport_send_beacon() instead of BLE notifications
 *
 * @see docs/adr/0048-espnow-adaptive-transport-hardware-acceleration.md
 * @see docs/ESP-NOW_vs_BLE_Power_Analysis.md
 * @date December 2025
 * @author Claude Code (Anthropic)
 */

#ifndef ESPNOW_TRANSPORT_H
#define ESPNOW_TRANSPORT_H

#include <stdint.h>
#include <stdbool.h>
#include "esp_err.h"
#include "time_sync.h"

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================================
// CONSTANTS
// ============================================================================

/** @brief ESP-NOW channel (must match on both devices) */
#define ESPNOW_CHANNEL              (1U)

/** @brief ESP-NOW max payload (250 bytes) - beacon is only 25 bytes */
#define ESPNOW_MAX_PAYLOAD          (250U)

/** @brief Jitter measurement window size */
#define ESPNOW_JITTER_WINDOW_SIZE   (32U)

// ============================================================================
// TDM SCHEDULING CONSTANTS (BLE/ESP-NOW Coexistence)
// ============================================================================

/**
 * @brief BLE connection interval in milliseconds
 *
 * BLE connection events occur at this interval (50ms = 40 × 1.25ms units).
 * ESP-NOW coordination messages should be scheduled between BLE events.
 */
#define ESPNOW_TDM_BLE_INTERVAL_MS  (50U)

/**
 * @brief TDM safe window offset from BLE event start (ms)
 *
 * BLE events use the radio for ~1-5ms at the start of each interval.
 * Schedule ESP-NOW at the midpoint (25ms offset) for maximum clearance.
 */
#define ESPNOW_TDM_SAFE_OFFSET_MS   (25U)

/**
 * @brief TDM safe window duration (ms)
 *
 * How long the "safe" window lasts around the midpoint.
 * ESP-NOW should complete transmission within this window.
 */
#define ESPNOW_TDM_SAFE_WINDOW_MS   (20U)

/** @brief ESP-NOW encryption key size (PMK/LMK) */
#define ESPNOW_KEY_SIZE             (16U)

/** @brief Session nonce size for HKDF key derivation (legacy, kept for API compat) */
#define ESPNOW_NONCE_SIZE           (8U)

/** @brief BLE Long Term Key size (128-bit from SMP pairing) */
#define ESPNOW_LTK_SIZE             (16U)

/** @brief ESP-NOW packet type (first byte for non-beacon messages) */
#define ESPNOW_PKT_TYPE_COORDINATION (0xC0U)  /**< Coordination message marker */

/** @brief HKDF context string for ESP-NOW session keys (v2 uses LTK as IKM) */
#define ESPNOW_HKDF_INFO            "EMDR-ESP-NOW-LMK-v2"

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

/**
 * @brief ESP-NOW key exchange message (sent via BLE)
 *
 * This structure is exchanged during BLE bootstrap to establish
 * a shared ESP-NOW encryption key using HKDF.
 *
 * Both devices:
 * 1. Exchange WiFi MAC addresses (already done)
 * 2. SERVER generates and sends nonce via this message
 * 3. Both derive LMK = HKDF-SHA256(MACs || nonce, info)
 * 4. ESP-NOW communication is now encrypted
 */
typedef struct __attribute__((packed)) {
    uint8_t nonce[ESPNOW_NONCE_SIZE];  /**< Server-generated random nonce */
    uint8_t server_mac[6];              /**< Server's WiFi MAC (for verification) */
} espnow_key_exchange_t;

/**
 * @brief ESP-NOW transport state
 */
typedef enum {
    ESPNOW_STATE_UNINITIALIZED = 0, /**< Not yet initialized */
    ESPNOW_STATE_READY,              /**< Ready but no peer configured */
    ESPNOW_STATE_PEER_SET,           /**< Peer MAC configured, ready to send */
    ESPNOW_STATE_ERROR               /**< Initialization failed */
} espnow_state_t;

/**
 * @brief Beacon receive callback type
 *
 * Called when a time sync beacon is received via ESP-NOW.
 * The callback runs in WiFi task context - keep it fast!
 *
 * @param beacon Pointer to received beacon data
 * @param receive_time_us Timestamp when beacon was received (esp_timer_get_time)
 */
typedef void (*espnow_beacon_callback_t)(const time_sync_beacon_t *beacon,
                                         uint64_t receive_time_us);

/**
 * @brief Coordination message receive callback type
 *
 * Called when a coordination message is received via ESP-NOW.
 * Enables PTP handshake and asymmetry probes to use low-latency transport.
 * The callback runs in WiFi task context - keep it fast!
 *
 * @param data Pointer to received coordination message bytes
 * @param len Length of received data (excluding type marker byte)
 * @param receive_time_us Timestamp when message was received (esp_timer_get_time)
 */
typedef void (*espnow_coordination_callback_t)(const uint8_t *data,
                                                size_t len,
                                                uint64_t receive_time_us);

/**
 * @brief ESP-NOW timing metrics for jitter measurement
 */
typedef struct {
    uint64_t last_expected_us;           /**< When we expected the beacon */
    uint64_t last_actual_us;             /**< When beacon actually arrived */
    int64_t  jitter_samples[ESPNOW_JITTER_WINDOW_SIZE]; /**< Ring buffer */
    uint8_t  jitter_head;                /**< Ring buffer head */
    uint8_t  jitter_count;               /**< Number of samples collected */
    int64_t  jitter_sum;                 /**< Sum for running average */
    int64_t  jitter_sum_sq;              /**< Sum of squares for stddev */
    uint32_t beacons_sent;               /**< Total beacons sent */
    uint32_t beacons_received;           /**< Total beacons received */
    uint32_t send_failures;              /**< Send failures */
} espnow_metrics_t;

// ============================================================================
// PUBLIC API
// ============================================================================

/**
 * @brief Initialize ESP-NOW transport layer
 *
 * Initializes WiFi in STA mode and configures ESP-NOW.
 * WiFi/BLE coexistence is handled by ESP-IDF automatically.
 *
 * @return ESP_OK on success
 * @return ESP_ERR_NO_MEM if initialization fails
 * @return ESP_ERR_WIFI_NOT_INIT if WiFi not enabled in sdkconfig
 */
esp_err_t espnow_transport_init(void);

/**
 * @brief Deinitialize ESP-NOW transport
 *
 * @return ESP_OK on success
 */
esp_err_t espnow_transport_deinit(void);

/**
 * @brief Set peer device MAC address
 *
 * Configures the peer device for unicast ESP-NOW communication.
 * Call this after receiving peer MAC via BLE during pairing.
 *
 * @param peer_mac 6-byte MAC address of peer device
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_ARG if peer_mac is NULL
 * @return ESP_ERR_INVALID_STATE if not initialized
 */
esp_err_t espnow_transport_set_peer(const uint8_t peer_mac[6]);

/**
 * @brief Clear peer device (disconnect)
 *
 * Removes the configured peer. Call on BLE disconnect.
 *
 * @return ESP_OK on success
 */
esp_err_t espnow_transport_clear_peer(void);

/**
 * @brief Register beacon receive callback
 *
 * @param callback Function to call when beacon received
 * @return ESP_OK on success
 */
esp_err_t espnow_transport_register_callback(espnow_beacon_callback_t callback);

/**
 * @brief Send time sync beacon via ESP-NOW
 *
 * Sends the beacon to the configured peer with minimal latency.
 * Timestamp should be updated immediately before calling this.
 *
 * @param beacon Pointer to beacon to send
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_STATE if no peer configured
 * @return ESP_FAIL if send fails
 */
esp_err_t espnow_transport_send_beacon(const time_sync_beacon_t *beacon);

/**
 * @brief Get current transport state
 *
 * @return Current ESP-NOW transport state
 */
espnow_state_t espnow_transport_get_state(void);

/**
 * @brief Get local WiFi MAC address
 *
 * Returns the device's WiFi STA MAC address for exchange during BLE pairing.
 *
 * @param mac_out Buffer to store 6-byte MAC address
 * @return ESP_OK on success
 */
esp_err_t espnow_transport_get_local_mac(uint8_t mac_out[6]);

/**
 * @brief Get timing metrics
 *
 * @return Pointer to metrics structure (read-only)
 */
const espnow_metrics_t* espnow_transport_get_metrics(void);

/**
 * @brief Log jitter statistics
 *
 * Logs mean jitter, stddev, and sample count for analysis.
 */
void espnow_transport_log_jitter_stats(void);

/**
 * @brief Check if ESP-NOW transport is ready for beacons
 *
 * @return true if peer is configured and ready to send
 */
bool espnow_transport_is_ready(void);

// ============================================================================
// COORDINATION MESSAGE API (PTP/Asymmetry over ESP-NOW)
// ============================================================================

/**
 * @brief Register coordination message receive callback
 *
 * Enables receiving coordination messages (PTP handshake, asymmetry probes)
 * via ESP-NOW for sub-millisecond timing accuracy.
 *
 * @param callback Function to call when coordination message received
 * @return ESP_OK on success
 */
esp_err_t espnow_transport_register_coordination_callback(espnow_coordination_callback_t callback);

/**
 * @brief Send coordination message via ESP-NOW
 *
 * Sends time-critical coordination messages (PTP, asymmetry probes) via
 * low-latency ESP-NOW instead of BLE GATT.
 *
 * Message format: [0xC0][coordination_message_t bytes...]
 * The 0xC0 marker distinguishes from beacons for routing on receive.
 *
 * @param data Pointer to coordination message bytes
 * @param len Length of message data
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_ARG if data is NULL or len is 0
 * @return ESP_ERR_INVALID_STATE if no peer configured
 * @return ESP_FAIL if send fails
 */
esp_err_t espnow_transport_send_coordination(const uint8_t *data, size_t len);

/**
 * @brief Send coordination message with TDM scheduling
 *
 * Like espnow_transport_send_coordination() but waits for a TDM-safe
 * window before transmitting. This avoids radio contention with BLE
 * connection events.
 *
 * TDM schedule:
 * - BLE events occur at t=0, 50, 100ms, etc.
 * - Safe window is centered at t=25, 75, 125ms, etc.
 * - Function blocks up to ESPNOW_TDM_BLE_INTERVAL_MS until safe window
 *
 * @param data Pointer to coordination message bytes
 * @param len Length of message data
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_ARG if data is NULL or len is 0
 * @return ESP_ERR_INVALID_STATE if no peer configured
 * @return ESP_FAIL if send fails
 */
esp_err_t espnow_transport_send_coordination_tdm(const uint8_t *data, size_t len);

/**
 * @brief Check if currently in TDM safe window for ESP-NOW
 *
 * Returns true if the current time is in the safe window for ESP-NOW
 * transmission (midpoint between BLE connection events).
 *
 * @return true if safe to send ESP-NOW now
 * @return false if BLE event may be active
 */
bool espnow_transport_is_tdm_safe(void);

/**
 * @brief Wait until next TDM safe window
 *
 * Blocks until the next TDM-safe window for ESP-NOW transmission.
 * Maximum wait is ESPNOW_TDM_BLE_INTERVAL_MS.
 *
 * @return Time waited in milliseconds
 */
uint32_t espnow_transport_wait_for_tdm_safe(void);

// ============================================================================
// SECURE KEY DERIVATION API (HKDF-SHA256)
// ============================================================================

/**
 * @brief Generate key exchange message for BLE transmission
 *
 * SERVER calls this to generate a key exchange message containing:
 * - Random nonce (8 bytes from hardware RNG)
 * - Server's WiFi MAC (for CLIENT verification)
 *
 * @param[out] key_exchange Buffer to store generated message
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_ARG if key_exchange is NULL
 * @return ESP_ERR_INVALID_STATE if transport not initialized
 */
esp_err_t espnow_transport_generate_key_exchange(espnow_key_exchange_t *key_exchange);

/**
 * @brief Derive session LMK from BLE LTK and WiFi MACs (recommended)
 *
 * Both SERVER and CLIENT call this after BLE pairing completes.
 * Each device independently derives identical ESP-NOW session keys.
 *
 * Input keying material (38 bytes total):
 *   LTK (16 bytes) - BLE Long Term Key from SMP pairing (128-bit entropy)
 *   SERVER_MAC (6 bytes) - WiFi STA MAC of SERVER device
 *   CLIENT_MAC (6 bytes) - WiFi STA MAC of CLIENT device
 *
 * Salt: None (LTK provides sufficient entropy)
 * Info string: "EMDR-ESP-NOW-LMK-v2"
 * Output: 16-byte LMK for ESP-NOW encryption
 *
 * Security properties:
 * - 128-bit entropy from BLE pairing (vs 64-bit from nonce approach)
 * - MAC binding prevents replay across different device pairs
 * - No key exchange message needed (both devices derive independently)
 * - Ephemeral: LTK captured at pairing time, never persisted
 *
 * @param[in] ltk BLE Long Term Key from SMP pairing (16 bytes)
 * @param[in] server_mac Server's WiFi MAC address (6 bytes)
 * @param[in] client_mac Client's WiFi MAC address (6 bytes)
 * @param[out] lmk_out Buffer to store 16-byte derived LMK
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_ARG if any parameter is NULL
 * @return ESP_FAIL if HKDF derivation fails
 */
esp_err_t espnow_transport_derive_key_from_ltk(
    const uint8_t ltk[ESPNOW_LTK_SIZE],
    const uint8_t server_mac[6],
    const uint8_t client_mac[6],
    uint8_t lmk_out[ESPNOW_KEY_SIZE]
);

/**
 * @brief Derive session LMK from nonce (deprecated - use derive_key_from_ltk)
 *
 * @deprecated Use espnow_transport_derive_key_from_ltk() instead.
 *             This function provides only 64-bit entropy from the nonce
 *             and requires an additional key exchange message.
 *
 * Input keying material: SERVER_MAC || CLIENT_MAC || nonce
 * Info string: "EMDR-ESP-NOW-LMK-v1"
 * Output: 16-byte LMK for ESP-NOW encryption
 *
 * @param[in] server_mac Server's WiFi MAC address (6 bytes)
 * @param[in] client_mac Client's WiFi MAC address (6 bytes)
 * @param[in] nonce Server-generated random nonce (8 bytes)
 * @param[out] lmk_out Buffer to store 16-byte derived LMK
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_ARG if any parameter is NULL
 * @return ESP_FAIL if HKDF derivation fails
 */
esp_err_t espnow_transport_derive_session_key(
    const uint8_t server_mac[6],
    const uint8_t client_mac[6],
    const uint8_t nonce[ESPNOW_NONCE_SIZE],
    uint8_t lmk_out[ESPNOW_KEY_SIZE]
);

/**
 * @brief Set peer with encrypted LMK for secure communication
 *
 * Configures the peer with derived session key for encrypted ESP-NOW.
 * This is the secure version of espnow_transport_set_peer().
 *
 * @param[in] peer_mac 6-byte MAC address of peer device
 * @param[in] lmk 16-byte Local Master Key for encryption
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_ARG if peer_mac or lmk is NULL
 * @return ESP_ERR_INVALID_STATE if not initialized
 */
esp_err_t espnow_transport_set_peer_encrypted(
    const uint8_t peer_mac[6],
    const uint8_t lmk[ESPNOW_KEY_SIZE]
);

/**
 * @brief Check if ESP-NOW encryption is active
 *
 * @return true if peer is configured with encryption enabled
 */
bool espnow_transport_is_encrypted(void);

#ifdef __cplusplus
}
#endif

#endif // ESPNOW_TRANSPORT_H
