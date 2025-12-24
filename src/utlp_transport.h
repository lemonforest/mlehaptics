/**
 * @file utlp_transport.h
 * @brief UTLP Transport Hardware Abstraction Layer
 *
 * Platform-agnostic interface for UTLP time synchronization transport.
 * This file knows NOTHING about Espressif, Nordic, or any vendor-specific APIs.
 *
 * The UTLP protocol logic (Kalman filters, stratum management, sheet music
 * scheduler) operates through this interface, enabling portability across:
 * - ESP32 ESP-NOW (current implementation)
 * - Nordic nRF52 Enhanced ShockBurst (future)
 * - STM32 WirelessMCU (future)
 * - Any low-latency connectionless transport
 *
 * Implementation Pattern:
 * - utlp_transport.h - This file (universal interface)
 * - utlp_transport_espnow.c - ESP-NOW implementation
 * - utlp_transport_shockburst.c - Nordic ESB (future)
 *
 * @see docs/adr/0048-espnow-adaptive-transport-hardware-acceleration.md
 * @date December 2025
 * @author Claude Code (Anthropic)
 */

#ifndef UTLP_TRANSPORT_H
#define UTLP_TRANSPORT_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================================
// TRANSPORT-AGNOSTIC ERROR CODES
// ============================================================================

/**
 * @brief Transport operation result codes
 *
 * Vendor-specific errors are mapped to these universal codes.
 */
typedef enum {
    UTLP_OK = 0,                    /**< Operation succeeded */
    UTLP_ERR_INVALID_ARG,           /**< Invalid argument provided */
    UTLP_ERR_INVALID_STATE,         /**< Operation not valid in current state */
    UTLP_ERR_NO_MEM,                /**< Memory allocation failed */
    UTLP_ERR_NOT_INIT,              /**< Transport not initialized */
    UTLP_ERR_SEND_FAILED,           /**< Frame transmission failed */
    UTLP_ERR_PEER_NOT_SET,          /**< No peer configured */
    UTLP_ERR_CRYPTO_FAILED,         /**< Key derivation or encryption failed */
    UTLP_ERR_TIMEOUT,               /**< Operation timed out */
    UTLP_ERR_UNKNOWN                /**< Unknown error */
} utlp_err_t;

// ============================================================================
// TRANSPORT STATE
// ============================================================================

/**
 * @brief Transport state (independent of vendor implementation)
 */
typedef enum {
    UTLP_STATE_UNINITIALIZED = 0,   /**< Not yet initialized */
    UTLP_STATE_READY,               /**< Ready but no peer configured */
    UTLP_STATE_PEER_SET,            /**< Peer configured, ready to send */
    UTLP_STATE_ENCRYPTED,           /**< Peer configured with encryption */
    UTLP_STATE_ERROR                /**< Initialization or runtime error */
} utlp_state_t;

// ============================================================================
// KEY DERIVATION CONSTANTS
// ============================================================================

/** @brief Encryption key size (shared across implementations) */
#define UTLP_KEY_SIZE               (16U)

/** @brief Session nonce size for key derivation */
#define UTLP_NONCE_SIZE             (8U)

/** @brief MAC address size (universal) */
#define UTLP_MAC_SIZE               (6U)

// ============================================================================
// DATA STRUCTURES
// ============================================================================

/**
 * @brief Universal frame structure for UTLP transport
 *
 * This is what the protocol logic passes to the transport layer.
 * Vendor implementations wrap this in their specific format.
 */
typedef struct {
    uint8_t dest_addr[UTLP_MAC_SIZE];   /**< Destination MAC address */
    const uint8_t *data;                 /**< Frame payload (beacon, coordination msg) */
    size_t len;                          /**< Payload length in bytes */
} utlp_frame_t;

/**
 * @brief Key exchange message (sent via out-of-band channel like BLE)
 *
 * Used during session establishment. The nonce and MACs are combined
 * via HKDF to derive a shared encryption key.
 */
typedef struct __attribute__((packed)) {
    uint8_t nonce[UTLP_NONCE_SIZE];     /**< Random nonce from initiator */
    uint8_t initiator_mac[UTLP_MAC_SIZE]; /**< Initiator's transport MAC */
} utlp_key_exchange_t;

/**
 * @brief Transport metrics (vendor-agnostic)
 */
typedef struct {
    uint32_t frames_sent;               /**< Total frames sent */
    uint32_t frames_received;           /**< Total frames received */
    uint32_t send_failures;             /**< Send failures */
    int64_t  last_rx_timestamp_us;      /**< Last receive timestamp */
    int64_t  jitter_mean_us;            /**< Mean jitter (running average) */
    int64_t  jitter_stddev_us;          /**< Jitter standard deviation */
} utlp_metrics_t;

/**
 * @brief Frame receive callback type
 *
 * Called when a frame is received. Implementation must capture
 * timestamp as early as possible for timing accuracy.
 *
 * @param data Pointer to received frame data
 * @param len Length of received data
 * @param src_addr Source MAC address
 * @param rx_timestamp_us Receive timestamp (local clock, microseconds)
 */
typedef void (*utlp_rx_callback_t)(const uint8_t *data, size_t len,
                                    const uint8_t src_addr[UTLP_MAC_SIZE],
                                    int64_t rx_timestamp_us);

// ============================================================================
// TRANSPORT OPERATIONS INTERFACE
// ============================================================================

/**
 * @brief Transport operations vtable
 *
 * Vendor-specific implementations provide this structure.
 * The UTLP protocol layer uses these function pointers.
 */
typedef struct {
    /**
     * @brief Initialize the transport
     * @return UTLP_OK on success
     */
    utlp_err_t (*init)(void);

    /**
     * @brief Deinitialize the transport
     * @return UTLP_OK on success
     */
    utlp_err_t (*deinit)(void);

    /**
     * @brief Send a frame to peer
     * @param frame Frame to send
     * @return UTLP_OK on success
     */
    utlp_err_t (*send)(const utlp_frame_t *frame);

    /**
     * @brief Configure peer address (unencrypted)
     * @param peer_mac Peer's MAC address
     * @return UTLP_OK on success
     */
    utlp_err_t (*set_peer)(const uint8_t peer_mac[UTLP_MAC_SIZE]);

    /**
     * @brief Configure peer with encryption key
     * @param peer_mac Peer's MAC address
     * @param key Derived session key (UTLP_KEY_SIZE bytes)
     * @return UTLP_OK on success
     */
    utlp_err_t (*set_peer_encrypted)(const uint8_t peer_mac[UTLP_MAC_SIZE],
                                      const uint8_t key[UTLP_KEY_SIZE]);

    /**
     * @brief Clear peer configuration
     * @return UTLP_OK on success
     */
    utlp_err_t (*clear_peer)(void);

    /**
     * @brief Register frame receive callback
     * @param callback Function to call on frame reception
     * @return UTLP_OK on success
     */
    utlp_err_t (*register_rx_callback)(utlp_rx_callback_t callback);

    /**
     * @brief Get local MAC address
     * @param mac_out Buffer to store MAC address
     * @return UTLP_OK on success
     */
    utlp_err_t (*get_local_mac)(uint8_t mac_out[UTLP_MAC_SIZE]);

    /**
     * @brief Get transport state
     * @return Current transport state
     */
    utlp_state_t (*get_state)(void);

    /**
     * @brief Check if transport is ready to send
     * @return true if peer configured and ready
     */
    bool (*is_ready)(void);

    /**
     * @brief Check if encryption is active
     * @return true if encrypted peer configured
     */
    bool (*is_encrypted)(void);

    /**
     * @brief Get transport metrics
     * @return Pointer to metrics structure
     */
    const utlp_metrics_t* (*get_metrics)(void);

    /**
     * @brief Log transport statistics
     */
    void (*log_stats)(void);

} utlp_transport_ops_t;

// ============================================================================
// TRANSPORT INSTANCE
// ============================================================================

/**
 * @brief Global transport instance
 *
 * Set at compile time or during init based on platform.
 * UTLP protocol logic uses: utlp_transport->send(frame);
 */
extern const utlp_transport_ops_t *utlp_transport;

// ============================================================================
// KEY DERIVATION (Transport-agnostic)
// ============================================================================

/**
 * @brief Generate key exchange message
 *
 * Creates a key exchange message with random nonce and local MAC.
 * Called by initiator (SERVER) during session establishment.
 *
 * @param[out] key_exchange Buffer to store generated message
 * @param[in] local_mac Local device MAC address
 * @return UTLP_OK on success
 */
utlp_err_t utlp_generate_key_exchange(utlp_key_exchange_t *key_exchange,
                                       const uint8_t local_mac[UTLP_MAC_SIZE]);

/**
 * @brief Derive session key from key exchange data
 *
 * Uses HKDF-SHA256 to derive a shared encryption key from:
 * - Initiator MAC
 * - Responder MAC
 * - Random nonce
 *
 * Both devices call with same inputs to derive identical keys.
 *
 * @param[in] initiator_mac Initiator's (SERVER) MAC address
 * @param[in] responder_mac Responder's (CLIENT) MAC address
 * @param[in] nonce Random nonce from key exchange
 * @param[out] key_out Buffer for derived key (UTLP_KEY_SIZE bytes)
 * @return UTLP_OK on success
 */
utlp_err_t utlp_derive_session_key(const uint8_t initiator_mac[UTLP_MAC_SIZE],
                                    const uint8_t responder_mac[UTLP_MAC_SIZE],
                                    const uint8_t nonce[UTLP_NONCE_SIZE],
                                    uint8_t key_out[UTLP_KEY_SIZE]);

#ifdef __cplusplus
}
#endif

#endif // UTLP_TRANSPORT_H
