/**
 * @file utlp_transport.h
 * @brief Multi-Transport Management Layer for UTLP
 *
 * @section overview Overview
 *
 * This module manages multiple radio transports (arbors) for UTLP:
 * - ESP-NOW (WiFi broadcast)
 * - IEEE 802.15.4 (Thread/ZigBee PHY, raw MAC frames)
 * - BLE (future)
 *
 * The application layer can either:
 * - Specify exactly which transports to use (Option A)
 * - Let UTLP probe and enable all available transports (Option B)
 *
 * @section architecture Architecture
 *
 * ```
 * ┌─────────────────────────────────────────────────────────────┐
 * │                    UTLP Protocol Layer                       │
 * │                       (utlp.c)                               │
 * ├─────────────────────────────────────────────────────────────┤
 * │                  Transport Manager                           │
 * │                  (utlp_transport.c)                          │
 * │                                                              │
 * │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
 * │  │   ESP-NOW   │  │  802.15.4   │  │     BLE     │          │
 * │  │    Arbor    │  │    Arbor    │  │    Arbor    │          │
 * │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘          │
 * │         │                │                │                  │
 * │  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐          │
 * │  │utlp_hal_esp │  │utlp_hal_154 │  │utlp_hal_ble │          │
 * │  │   32.c      │  │   _c6.c     │  │   (future)  │          │
 * │  └─────────────┘  └─────────────┘  └─────────────┘          │
 * └─────────────────────────────────────────────────────────────┘
 *                              │
 *                    ┌─────────▼─────────┐
 *                    │ Hardware Coexist  │
 *                    │     Arbiter       │
 *                    └───────────────────┘
 * ```
 *
 * @section coexistence Hardware Coexistence
 *
 * ESP32-C6 has a hardware coexistence arbiter that time-divisions the
 * 2.4GHz radio between WiFi, BLE, and 802.15.4. We don't do software
 * multiplexing - we just initialize each transport and let the hardware
 * sort out the timing.
 *
 * @section prior_art Prior Art Claims
 *
 * - **Claim 243**: Arbor/Soma Multi-Transport Architecture
 * - **Claim 244**: Selective Arbor Yield
 * - **Claim 245**: Degraded Re-Entry with Stratum Penalty
 *
 * @version 1.0.0
 * @date 2026-01-02
 *
 * @copyright
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#pragma once

#include <stdint.h>
#include <stdbool.h>
#include "utlp_hal.h"

#ifdef __cplusplus
extern "C" {
#endif

/*============================================================================
 * TRANSPORT BITMASK
 *==========================================================================*/

/**
 * @brief Transport type bitmask values
 *
 * Use these to specify which transports to enable.
 * Can be OR'd together: `UTLP_TRANSPORT_ESPNOW | UTLP_TRANSPORT_154`
 */
typedef enum {
    UTLP_TRANSPORT_NONE     = 0x00,     /**< No transports (invalid) */
    UTLP_TRANSPORT_ESPNOW   = 0x01,     /**< ESP-NOW (WiFi broadcast) */
    UTLP_TRANSPORT_154      = 0x02,     /**< IEEE 802.15.4 raw MAC */
    UTLP_TRANSPORT_BLE      = 0x04,     /**< BLE (future) */
    UTLP_TRANSPORT_ALL      = 0xFF,     /**< All available transports */
} utlp_transport_t;

/*============================================================================
 * CONFIGURATION
 *==========================================================================*/

/**
 * @brief Transport initialization configuration
 *
 * Pass to utlp_transport_init() to specify which transports to use.
 * Pass NULL to auto-detect and enable all available transports.
 */
typedef struct {
    /**
     * @brief Bitmask of transports to enable
     *
     * - Specific transports: `UTLP_TRANSPORT_ESPNOW | UTLP_TRANSPORT_154`
     * - All available: `UTLP_TRANSPORT_ALL`
     */
    uint8_t transports;

    /**
     * @brief 802.15.4 channel (11-26)
     *
     * Only used if UTLP_TRANSPORT_154 is enabled.
     * Default: 15 (golden path, near WiFi channel 6)
     */
    uint8_t channel_154;

    /**
     * @brief TX mode for multi-transport
     *
     * - UTLP_TX_MODE_ALL: Broadcast on all enabled transports
     * - UTLP_TX_MODE_PRIMARY: TX on primary transport only (first available)
     * - UTLP_TX_MODE_BEST: TX on transport with best scheduling (802.15.4 preferred)
     */
    uint8_t tx_mode;

    /**
     * @brief Staggered ESP-NOW startup delay (milliseconds)
     *
     * When both 802.15.4 and ESP-NOW are available, this delays ESP-NOW
     * startup to enable testing of pure 802.15.4 synchronization first.
     *
     * Set to 0 to disable staggered startup (start both immediately).
     * Default: 15000 (15 seconds)
     *
     * @section stagger_test Test Scenarios Enabled
     *
     * 1. **Pure 802.15.4 Sync (t=0 to t=15s)**
     *    - Only 802.15.4 active, observe genesis election
     *    - Measure timing precision without WiFi interference
     *
     * 2. **WiFi Arbor Joins (t=15s)**
     *    - ESP-NOW comes online with its own genesis
     *    - Observe how two different genesis histories merge
     *    - Test arbor isolation and coexistence
     *
     * 3. **Steady State (t>15s)**
     *    - Both transports active
     *    - Verify TX mode routing (BEST prefers 802.15.4)
     *    - Measure combined jitter
     */
    uint32_t stagger_espnow_ms;
} utlp_transport_config_t;

/**
 * @brief TX mode options for multi-transport
 */
typedef enum {
    UTLP_TX_MODE_ALL     = 0,   /**< Broadcast on ALL enabled transports */
    UTLP_TX_MODE_PRIMARY = 1,   /**< TX on first available transport only */
    UTLP_TX_MODE_BEST    = 2,   /**< TX on best transport (802.15.4 > ESP-NOW) */
} utlp_tx_mode_t;

/**
 * @brief Default configuration macro
 *
 * Use as initializer:
 * ```c
 * utlp_transport_config_t cfg = UTLP_TRANSPORT_CONFIG_DEFAULT();
 * cfg.transports = UTLP_TRANSPORT_154;  // Override if needed
 * utlp_transport_init(&cfg);
 * ```
 */
#define UTLP_TRANSPORT_CONFIG_DEFAULT() { \
    .transports = UTLP_TRANSPORT_ALL, \
    .channel_154 = 15, \
    .tx_mode = UTLP_TX_MODE_BEST, \
    .stagger_espnow_ms = 15000, \
}

/**
 * @brief Configuration for immediate startup (no stagger)
 *
 * Use when you want both transports to start simultaneously.
 */
#define UTLP_TRANSPORT_CONFIG_IMMEDIATE() { \
    .transports = UTLP_TRANSPORT_ALL, \
    .channel_154 = 15, \
    .tx_mode = UTLP_TX_MODE_BEST, \
    .stagger_espnow_ms = 0, \
}

/*============================================================================
 * STATUS STRUCTURE
 *==========================================================================*/

/**
 * @brief Transport status information
 */
typedef struct {
    uint8_t  available;         /**< Bitmask of available transports (hardware) */
    uint8_t  enabled;           /**< Bitmask of enabled transports (initialized) */
    uint8_t  active;            /**< Bitmask of active transports (not dormant) */
    bool     has_scheduled_tx;  /**< True if any transport has hardware TX scheduling */
    uint8_t  primary;           /**< Primary transport for TX (single bit) */
} utlp_transport_status_t;

/*============================================================================
 * PUBLIC API
 *==========================================================================*/

/**
 * @brief Probe available transports on this platform
 *
 * Checks at compile-time and runtime which transports are available.
 * Does NOT initialize anything - just detection.
 *
 * @return Bitmask of available transports
 *
 * @par Example
 * @code
 * uint8_t available = utlp_transport_probe();
 * if (available & UTLP_TRANSPORT_154) {
 *     printf("802.15.4 available on this platform\n");
 * }
 * @endcode
 */
uint8_t utlp_transport_probe(void);

/**
 * @brief Initialize transport layer
 *
 * Initializes all requested transports and registers them with the arbor system.
 *
 * @param config Configuration, or NULL for auto-detect all available
 * @return true if at least one transport initialized successfully
 *
 * @par Example - Use all available transports (Option B)
 * @code
 * // Auto-detect and enable all
 * if (!utlp_transport_init(NULL)) {
 *     ESP_LOGE(TAG, "No transports available!");
 * }
 * @endcode
 *
 * @par Example - Specify transports (Option A)
 * @code
 * utlp_transport_config_t cfg = UTLP_TRANSPORT_CONFIG_DEFAULT();
 * cfg.transports = UTLP_TRANSPORT_154;  // 802.15.4 only
 * utlp_transport_init(&cfg);
 * @endcode
 */
bool utlp_transport_init(const utlp_transport_config_t *config);

/**
 * @brief Get current transport status
 *
 * @param[out] status Status structure to fill
 */
void utlp_transport_get_status(utlp_transport_status_t *status);

/**
 * @brief Enable a specific transport at runtime
 *
 * Safe to call multiple times (idempotent). Use this for:
 * - Delayed transport startup (after stagger timer fires)
 * - Re-enabling a transport after yield
 * - Manual transport management
 *
 * @param transport Single transport bit to enable
 * @return true if transport enabled (or already enabled), false on failure
 *
 * @par Example
 * @code
 * // Manually enable ESP-NOW after some delay
 * vTaskDelay(pdMS_TO_TICKS(30000));  // 30 seconds
 * utlp_transport_enable(UTLP_TRANSPORT_ESPNOW);
 * @endcode
 */
bool utlp_transport_enable(utlp_transport_t transport);

/**
 * @brief Check if ESP-NOW startup is pending (staggered)
 *
 * @return true if ESP-NOW timer is running and hasn't fired yet
 */
bool utlp_transport_is_espnow_pending(void);

/**
 * @brief Transmit packet on enabled transports
 *
 * Behavior depends on tx_mode configured at init:
 * - ALL: Sends on all enabled transports
 * - PRIMARY: Sends on primary transport only
 * - BEST: Sends on best available transport
 *
 * @param data Payload data
 * @param len Payload length
 * @return true if at least one TX succeeded
 */
bool utlp_transport_tx(const uint8_t *data, size_t len);

/**
 * @brief Transmit packet with scheduled timing
 *
 * Uses hardware scheduling if available (802.15.4), otherwise spin-wait.
 *
 * @param packets Array of scheduled TX requests
 * @param count Number of packets
 * @return true if all packets scheduled successfully
 */
bool utlp_transport_tx_scheduled(const utlp_scheduled_tx_t *packets, size_t count);

/**
 * @brief Check if hardware-scheduled TX is available
 *
 * @return true if any enabled transport supports hardware TX scheduling
 */
bool utlp_transport_has_scheduled_tx(void);

/**
 * @brief Poll for received packet from any transport
 *
 * Checks all enabled transports for received packets.
 *
 * @param[out] out_packet Buffer to store received packet
 * @return true if packet available
 */
bool utlp_transport_rx_poll(utlp_packet_t *out_packet);

/**
 * @brief Wait for packet with timeout
 *
 * Blocks until packet received on any transport or timeout.
 *
 * @param[out] out_packet Buffer to store received packet
 * @param timeout_ms Maximum time to wait
 * @return true if packet received, false on timeout
 */
bool utlp_transport_rx_wait(utlp_packet_t *out_packet, uint32_t timeout_ms);

/**
 * @brief Get this device's address (from primary transport)
 *
 * @param[out] addr Address structure to fill
 */
void utlp_transport_get_addr(utlp_addr_t *addr);

/**
 * @brief Get 6-byte MAC (legacy, from primary transport)
 *
 * @deprecated Use utlp_transport_get_addr() for transport-agnostic code
 * @param[out] mac Buffer for 6-byte MAC
 */
void utlp_transport_get_mac(uint8_t *mac);

/**
 * @brief Yield a specific transport (enter dormancy)
 *
 * Wrapper around utlp_arbor_yield() for convenience.
 *
 * @param transport Single transport bit (not a mask)
 * @return true if transport yielded successfully
 */
bool utlp_transport_yield(utlp_transport_t transport);

/**
 * @brief Wake a dormant transport
 *
 * Wrapper around utlp_arbor_wake() for convenience.
 *
 * @param transport Single transport bit
 * @return true if transport woke successfully
 */
bool utlp_transport_wake(utlp_transport_t transport);

/*============================================================================
 * UTILITY FUNCTIONS
 *==========================================================================*/

/**
 * @brief Get human-readable transport name
 *
 * @param transport Transport type
 * @return Static string with transport name
 */
const char* utlp_transport_name(utlp_transport_t transport);

/**
 * @brief Log current transport status
 *
 * Outputs status information via ESP_LOGI for debugging.
 */
void utlp_transport_log_status(void);

#ifdef __cplusplus
}
#endif
