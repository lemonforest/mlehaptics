/**
 * @file utlp_arbor.h
 * @brief Per-Transport Selective Dormancy API (Arbor-Specific Sleep)
 *
 * @section overview Overview
 *
 * In the Multi-Arbor architecture, each transport (ESP-NOW, 802.15.4, BLE) is
 * a sensory "arbor" (branch) feeding the central phase ("soma"). This module
 * enables **selective dormancy** — the ability to sleep individual transports
 * while keeping others active.
 *
 * This is NOT just power management. It enables:
 * 1. **Isolation Testing**: Silence WiFi to prove 802.15.4 can maintain Hard-PLL
 * 2. **Energy Conservation**: Hibernate high-power transports, keep heartbeat on low-power
 * 3. **Security/Immunity**: Shutdown contaminated arbor without killing temporal awareness
 *
 * @section architecture Arbor/Soma Architecture
 *
 * ```
 * ┌─────────────────────────────────────────────────────────────────┐
 * │                      SOMA (Central Phase)                       │
 * │   Aggregates observations from all arbors                       │
 * │   Maintains unified atomic time                                 │
 * │                                                                 │
 * │   ┌─────────┐     ┌─────────┐     ┌─────────┐                   │
 * │   │  ARBOR  │     │  ARBOR  │     │  ARBOR  │                   │
 * │   │  WiFi   │     │  15.4   │     │  BLE    │                   │
 * │   │ ESP-NOW │     │ 802.15.4│     │ NimBLE  │                   │
 * │   └────┬────┘     └────┬────┘     └────┬────┘                   │
 * │        │ ACTIVE        │ DORMANT       │ WAKING                 │
 * │        ▼               ▼               ▼                        │
 * │   [Beacons]       [Sleeping]      [Re-verifying]               │
 * └─────────────────────────────────────────────────────────────────┘
 * ```
 *
 * @section states Arbor States
 *
 * | State | Description | TX | RX |
 * |-------|-------------|----|----|
 * | **ACTIVE** | Normal operation | Yes | Yes |
 * | **DORMANT** | Transport disabled, ledger preserved | No | No |
 * | **WAKING** | Degraded re-entry, listening only | No | Yes |
 * | **ERROR** | Initialization failed | No | No |
 *
 * @section degraded_reentry Degraded Re-Entry
 *
 * When an arbor wakes from dormancy, it doesn't immediately resume authority.
 * Instead, it enters at a higher stratum (lower authority) until it can:
 * 1. Verify received beacons match the Soma's internal phase
 * 2. Confirm N consistent beacons (default: 5)
 * 3. Restore original stratum level
 *
 * This prevents "Phantom Arbor" attacks where a waking transport could
 * corrupt the swarm with stale timing data.
 *
 * @section prior_art Prior Art Claims
 *
 * This module supports the following prior art claims:
 * - **Claim 38**: Hibernation pattern for opportunistic participation
 * - **Claim 231**: Arbor Specific Immunity
 * - **Claim 232**: Identity Separation
 * - **Claim 237+**: Per-transport selective dormancy API
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
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/*============================================================================
 * ARBOR TYPES
 *==========================================================================*/

/**
 * @brief Transport arbor identifiers
 *
 * Each arbor represents a distinct radio transport that can be
 * independently enabled, disabled, and managed.
 */
typedef enum {
    UTLP_ARBOR_WIFI = 0,    /**< ESP-NOW transport (WiFi-based) */
    UTLP_ARBOR_154,         /**< IEEE 802.15.4 transport */
    UTLP_ARBOR_BLE,         /**< Bluetooth Low Energy transport */
    UTLP_ARBOR_COUNT        /**< Number of arbor types */
} utlp_arbor_id_t;

/**
 * @brief Arbor operational state
 */
typedef enum {
    UTLP_ARBOR_STATE_ACTIVE,    /**< Normal operation */
    UTLP_ARBOR_STATE_DORMANT,   /**< Transport disabled, ledger preserved */
    UTLP_ARBOR_STATE_WAKING,    /**< Degraded re-entry in progress */
    UTLP_ARBOR_STATE_ERROR      /**< Initialization or hardware failure */
} utlp_arbor_state_t;

/**
 * @brief Dormancy parameters for arbor yield
 */
typedef struct {
    uint32_t expected_duration_ms;  /**< Hint for peers (0 = indefinite) */
    bool     broadcast_beacon;      /**< Announce dormancy to swarm before sleeping */
    bool     preserve_ledger;       /**< Keep reputation snapshot for wakeup */
} utlp_dormancy_params_t;

/**
 * @brief Arbor status information
 */
typedef struct {
    utlp_arbor_id_t    id;              /**< Arbor identifier */
    utlp_arbor_state_t state;           /**< Current state */
    uint8_t            last_stratum;    /**< Stratum before dormancy */
    uint8_t            reentry_stratum; /**< Elevated stratum during WAKING */
    uint32_t           dormant_since;   /**< Timestamp when entered dormancy (ms) */
    uint32_t           wakeup_beacons;  /**< Beacons verified since WAKING */
} utlp_arbor_status_t;

/*============================================================================
 * CONFIGURATION CONSTANTS
 *==========================================================================*/

/**
 * @brief Stratum penalty for degraded re-entry
 *
 * When an arbor wakes, it starts at (last_stratum + penalty).
 * This ensures waking transports don't immediately assert authority
 * with potentially stale timing data.
 */
#define UTLP_DEGRADED_REENTRY_PENALTY   2

/**
 * @brief Beacons required to exit WAKING state
 *
 * The arbor must verify this many consistent beacons (matching Soma phase)
 * before transitioning from WAKING to ACTIVE.
 */
#define UTLP_REENTRY_VERIFY_BEACONS     5

/**
 * @brief Maximum dormancy duration before ledger expiry (ms)
 *
 * If an arbor stays dormant longer than this, its preserved ledger
 * is considered stale and will be cleared on wakeup.
 */
#define UTLP_MAX_DORMANCY_MS            (120 * 1000)  /* 2 minutes */

/*============================================================================
 * ARBOR MANAGEMENT API
 *==========================================================================*/

/**
 * @brief Initialize arbor management subsystem
 *
 * Called once during UTLP initialization to set up arbor tracking.
 */
void utlp_arbor_init(void);

/**
 * @brief Register an arbor with the management system
 *
 * Each transport calls this during its initialization to register
 * itself with the arbor manager.
 *
 * @param id Arbor identifier
 * @return ESP_OK on success, ESP_ERR_INVALID_ARG if already registered
 */
esp_err_t utlp_arbor_register(utlp_arbor_id_t id);

/**
 * @brief Selectively hibernate a specific transport arbor
 *
 * This function:
 * 1. Snapshots the arbor's reputation ledger (if preserve_ledger=true)
 * 2. Broadcasts "Dormant" beacon to peers (if broadcast_beacon=true)
 * 3. Performs physical layer shutdown
 * 4. Sets arbor state to DORMANT
 *
 * @section usage Usage Example
 *
 * @code
 * // Silence WiFi to prove 802.15.4 Hard-PLL
 * utlp_dormancy_params_t params = {
 *     .expected_duration_ms = 30000,  // 30 seconds
 *     .broadcast_beacon = true,       // Notify peers
 *     .preserve_ledger = true         // Keep reputation
 * };
 * utlp_arbor_yield(UTLP_ARBOR_WIFI, &params);
 * @endcode
 *
 * @param id     Target arbor (UTLP_ARBOR_WIFI, UTLP_ARBOR_154, etc.)
 * @param params Dormancy parameters (NULL for defaults)
 * @return ESP_OK on success, ESP_ERR_INVALID_STATE if already dormant
 */
esp_err_t utlp_arbor_yield(utlp_arbor_id_t id, const utlp_dormancy_params_t *params);

/**
 * @brief Wake a dormant arbor with degraded re-entry
 *
 * The arbor enters at elevated stratum (lower authority) until it
 * re-verifies phase against the Soma's continuous internal clock.
 *
 * @section degraded Degraded Re-Entry Process
 *
 * 1. Physical layer restarted
 * 2. Arbor state → WAKING
 * 3. Listens for beacons (no TX)
 * 4. Verifies N beacons match Soma phase
 * 5. State → ACTIVE, stratum restored
 *
 * @param id Target arbor to wake
 * @return ESP_OK on success, ESP_ERR_INVALID_STATE if not dormant
 */
esp_err_t utlp_arbor_wake(utlp_arbor_id_t id);

/**
 * @brief Force immediate wake without degraded re-entry
 *
 * CAUTION: Use only for emergency recovery. Skips the degraded re-entry
 * verification, potentially allowing stale timing to propagate.
 *
 * @param id Target arbor to force wake
 * @return ESP_OK on success
 */
esp_err_t utlp_arbor_force_wake(utlp_arbor_id_t id);

/**
 * @brief Query arbor state
 *
 * @param id Target arbor
 * @return Current arbor state
 */
utlp_arbor_state_t utlp_arbor_get_state(utlp_arbor_id_t id);

/**
 * @brief Get detailed arbor status
 *
 * @param id     Target arbor
 * @param[out] status Status structure to fill
 * @return ESP_OK on success, ESP_ERR_INVALID_ARG if not registered
 */
esp_err_t utlp_arbor_get_status(utlp_arbor_id_t id, utlp_arbor_status_t *status);

/**
 * @brief Check if arbor is available for TX
 *
 * Returns true only if arbor is ACTIVE. DORMANT and WAKING arbors
 * should not transmit beacons.
 *
 * @param id Target arbor
 * @return true if arbor can transmit
 */
bool utlp_arbor_can_tx(utlp_arbor_id_t id);

/**
 * @brief Check if arbor is receiving
 *
 * Returns true if arbor is ACTIVE or WAKING (listening for verification).
 *
 * @param id Target arbor
 * @return true if arbor can receive
 */
bool utlp_arbor_can_rx(utlp_arbor_id_t id);

/**
 * @brief Notify arbor of verified beacon during WAKING
 *
 * Called by the protocol layer when a received beacon matches the
 * Soma's internal phase. Increments verification counter.
 *
 * @param id Arbor that received the beacon
 * @return ESP_OK, or ESP_ERR_INVALID_STATE if not WAKING
 */
esp_err_t utlp_arbor_beacon_verified(utlp_arbor_id_t id);

/**
 * @brief Get arbor name string for logging
 *
 * @param id Arbor identifier
 * @return Human-readable arbor name ("WiFi", "15.4", "BLE", "Unknown")
 */
const char* utlp_arbor_name(utlp_arbor_id_t id);

/*============================================================================
 * ITERATION HELPERS
 *==========================================================================*/

/**
 * @brief Iterate over all active arbors
 *
 * @section usage Usage Example
 *
 * @code
 * utlp_arbor_id_t id;
 * for (id = 0; id < UTLP_ARBOR_COUNT; id++) {
 *     if (utlp_arbor_get_state(id) == UTLP_ARBOR_STATE_ACTIVE) {
 *         // Process active arbor
 *     }
 * }
 * @endcode
 */

/**
 * @brief Get count of currently active arbors
 *
 * @return Number of arbors in ACTIVE state
 */
uint8_t utlp_arbor_active_count(void);

/**
 * @brief Get count of registered arbors
 *
 * @return Number of registered arbors (0 to UTLP_ARBOR_COUNT)
 */
uint8_t utlp_arbor_registered_count(void);

#ifdef __cplusplus
}
#endif
