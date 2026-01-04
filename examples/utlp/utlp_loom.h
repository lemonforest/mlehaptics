/**
 * @file utlp_loom.h
 * @brief The Loom - Emergent Time Lord Authority State Machine
 *
 * @section overview Overview
 *
 * The Loom implements automatic "Time Lord" promotion when no external time
 * source is available. Each transport arbor has its own independent Loom,
 * enabling a device to be Time Lord on one transport while following on another.
 *
 * @section metaphor The Loom Metaphor
 *
 * In Norse mythology, the Norns weave the threads of fate at the base of
 * Yggdrasil. The Loom module does similar work: when the timeline "frays"
 * (no beacons received for too long), we begin "weaving" a new temporal
 * thread and become an "anchor" (Time Lord) for other devices.
 *
 * @section states Loom States
 *
 * ```
 *                    +------------------+
 *                    |                  |
 *         (silence)  v                  | (better beacon)
 *    +----------> DORMANT <-------------+
 *    |              |                   |
 *    |   (2 min silence on arbor)       |
 *    |              v                   |
 *    |          WEAVING ----------------+
 *    |              |    (10s warmup complete)
 *    |              v
 *    +---------- ANCHOR ----------------+
 *                   |                   |
 *                   | (better beacon)   |
 *                   v                   |
 *               DISSOLVING -------------+
 * ```
 *
 * @section per_arbor Per-Arbor Independence
 *
 * Each arbor has its own Loom state, meaning:
 * - WiFi may be in ANCHOR (acting as Time Lord)
 * - 802.15.4 may be in DORMANT (following another node)
 * - BLE may be WEAVING (no beacons recently, warming up)
 *
 * This isolation supports the Multi-Arbor architecture where transports
 * operate independently.
 *
 * @section prior_art Prior Art Claims
 *
 * This module supports the following prior art claims:
 * - **Claims 35-37**: Emergent Role Differentiation
 * - **Claims 38-41**: Application-Layer Dormancy Control
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
#include "utlp_arbor.h"

#ifdef __cplusplus
extern "C" {
#endif

/*============================================================================
 * CONFIGURATION CONSTANTS
 *==========================================================================*/

/**
 * @brief Silence threshold before timeline frays (microseconds)
 *
 * If no beacon is received on an arbor for this duration, we consider
 * the timeline "frayed" and begin weaving (promoting to Time Lord).
 *
 * 2 minutes = 120,000,000 microseconds
 */
#define UTLP_LOOM_FRAY_THRESHOLD_US     (120ULL * 1000000ULL)

/**
 * @brief Warmup duration in WEAVING state before becoming ANCHOR (us)
 *
 * After detecting silence, we wait this long before asserting Time Lord
 * authority. This prevents oscillation and gives existing Time Lords a
 * chance to resume broadcasting.
 *
 * 10 seconds = 10,000,000 microseconds
 */
#define UTLP_LOOM_WEAVE_WARMUP_US       (10ULL * 1000000ULL)

/**
 * @brief Genesis pulse interval when acting as ANCHOR (us)
 *
 * How often we broadcast the "seismic chirp" when we're the Time Lord.
 * 5 seconds = 5,000,000 microseconds
 */
#define UTLP_LOOM_GENESIS_INTERVAL_US   (5ULL * 1000000ULL)

/*============================================================================
 * LOOM STATE TYPES
 *==========================================================================*/

/**
 * @brief Loom state for a single arbor
 *
 * Each arbor has an independent Loom tracking its Time Lord promotion status.
 */
typedef enum {
    LOOM_STATE_DORMANT,     /**< Listening, not promoting */
    LOOM_STATE_WEAVING,     /**< Silence detected, warming up */
    LOOM_STATE_ANCHOR,      /**< Acting as Time Lord on this arbor */
    LOOM_STATE_DISSOLVING   /**< Better source found, stepping down */
} utlp_loom_state_t;

/**
 * @brief Per-arbor Loom status snapshot
 */
typedef struct {
    utlp_arbor_id_t    arbor_id;        /**< Which arbor this is */
    utlp_loom_state_t  state;           /**< Current Loom state */
    uint64_t           last_beacon_us;  /**< Last beacon timestamp on this arbor */
    uint64_t           weave_start_us;  /**< When WEAVING began (0 if not weaving) */
    uint8_t            genesis_stratum; /**< Our stratum when acting as ANCHOR */
    uint32_t           time_in_state_ms;/**< How long in current state */
} utlp_loom_status_t;

/*============================================================================
 * PUBLIC API
 *==========================================================================*/

/**
 * @brief Initialize the Loom subsystem
 *
 * Must be called once during UTLP initialization, after arbor init.
 * Sets all arbors to DORMANT state with no history.
 */
void utlp_loom_init(void);

/**
 * @brief Periodic tick for Loom state machine (called by engine timer)
 *
 * This function drives the Loom state transitions for all arbors:
 * - Checks silence duration on each active arbor
 * - Transitions DORMANT -> WEAVING if timeline frayed
 * - Transitions WEAVING -> ANCHOR after warmup complete
 * - Schedules Genesis Pulse when ANCHOR state reached
 *
 * Call this at ~10 Hz from the UTLP engine timer.
 */
void utlp_loom_tick(void);

/**
 * @brief Notify Loom that a beacon was received on an arbor
 *
 * Updates the last_beacon_us timestamp for the arbor. Also handles
 * state transitions:
 * - WEAVING -> DORMANT if beacon received (we're not alone)
 * - ANCHOR -> DISSOLVING if better Time Lord detected
 *
 * @param arbor_id  Which arbor received the beacon
 * @param stratum   Stratum of the received beacon
 * @param tx_time   TX timestamp from the beacon
 */
void utlp_loom_beacon_received(utlp_arbor_id_t arbor_id, uint8_t stratum, uint64_t tx_time);

/**
 * @brief Get current Loom state for an arbor
 *
 * @param arbor_id Target arbor
 * @return Current Loom state
 */
utlp_loom_state_t utlp_loom_get_state(utlp_arbor_id_t arbor_id);

/**
 * @brief Get detailed Loom status for an arbor
 *
 * @param arbor_id      Target arbor
 * @param[out] status   Status structure to fill
 * @return true if arbor is valid and registered
 */
bool utlp_loom_get_status(utlp_arbor_id_t arbor_id, utlp_loom_status_t *status);

/**
 * @brief Check if this device is Time Lord on any arbor
 *
 * @return true if any arbor is in ANCHOR state
 */
bool utlp_loom_is_time_lord(void);

/**
 * @brief Check if this device is Time Lord on a specific arbor
 *
 * @param arbor_id Target arbor
 * @return true if arbor is in ANCHOR state
 */
bool utlp_loom_is_anchor(utlp_arbor_id_t arbor_id);

/**
 * @brief Force a specific arbor to become Time Lord (ANCHOR)
 *
 * Bypasses the normal silence detection. Use for testing or when
 * you know this device should be the authoritative time source.
 *
 * @param arbor_id Target arbor
 * @param stratum  Stratum to claim (typically 1 for Genesis)
 */
void utlp_loom_force_anchor(utlp_arbor_id_t arbor_id, uint8_t stratum);

/**
 * @brief Force a specific arbor to step down from Time Lord
 *
 * Transitions ANCHOR -> DORMANT immediately. Use when a better
 * time source has been discovered externally.
 *
 * @param arbor_id Target arbor
 */
void utlp_loom_force_dissolve(utlp_arbor_id_t arbor_id);

/**
 * @brief Pause Loom for an arbor (used during dormancy)
 *
 * When an arbor enters DORMANT (sleeping), we pause the Loom to
 * prevent false silence detection. The Loom resumes when the arbor
 * wakes.
 *
 * @param arbor_id Target arbor
 */
void utlp_loom_pause(utlp_arbor_id_t arbor_id);

/**
 * @brief Resume Loom for an arbor (used after wakeup)
 *
 * Resets the last_beacon timestamp to "now" to give the arbor
 * time to receive beacons before triggering WEAVING.
 *
 * @param arbor_id Target arbor
 */
void utlp_loom_resume(utlp_arbor_id_t arbor_id);

/**
 * @brief Get name string for Loom state
 *
 * @param state Loom state
 * @return Human-readable state name
 */
const char* utlp_loom_state_name(utlp_loom_state_t state);

/**
 * @brief Log current Loom status for all arbors
 *
 * Outputs a summary of each arbor's Loom state for debugging.
 */
void utlp_loom_log_status(void);

/*============================================================================
 * POLYCHROMATIC STRATUM ASYMMETRY (Claim 253)
 *
 * Multi-transport stratum management for bridge nodes. Enables devices to
 * maintain different stratum levels on different transports - e.g., following
 * a Time Lord on WiFi (stratum 2) while acting as Genesis on 802.15.4
 * (stratum 1) if that spectrum is silent.
 *==========================================================================*/

/**
 * @brief Polychromatic stratum update for multi-transport bridges
 *
 * Called from utlp_loom_tick() to check if secondary transports should
 * be promoted to Genesis (stratum 1) when the primary transport is
 * synchronized and the secondary has no authority neighbors.
 *
 * Logic:
 * - If primary_time_source is synced (stratum > 1 means following)
 * - AND secondary transport has no authority neighbors (stratum <= 1)
 * - THEN promote secondary to stratum 1 (Local Genesis)
 *
 * This propagates "Genesis Truth" into silent spectral bands.
 *
 * @see Claim 253: Polychromatic Stratum Asymmetry
 */
void utlp_loom_polychromatic_update(void);

/*============================================================================
 * GENESIS PULSE INTEGRATION
 *
 * The Loom triggers Genesis Pulse when:
 * 1. An arbor transitions to ANCHOR (automatic Time Lord promotion)
 * 2. An arbor wakes from dormancy (mandatory announcement)
 *
 * These functions allow the main UTLP loop to detect pending requests
 * and trigger chirps appropriately.
 *==========================================================================*/

/**
 * @brief Check if any arbor has a pending Genesis Pulse request
 *
 * Returns true and clears the request if any arbor needs to send
 * a Genesis Pulse. The main loop should call this periodically
 * and trigger chirps when true is returned.
 *
 * For polychromatic support (Claim 253), the out_arbor parameter
 * indicates which arbor the genesis pulse should be sent on.
 *
 * @param[out] out_arbor  If non-NULL, filled with the arbor ID
 * @return true if Genesis Pulse should be sent
 */
bool utlp_loom_consume_genesis_request(utlp_arbor_id_t *out_arbor);

/**
 * @brief Request a Genesis Pulse on a specific arbor
 *
 * Called when an arbor wakes from dormancy to announce its return.
 * The request will be consumed by utlp_loom_consume_genesis_request().
 *
 * @param arbor_id Arbor requesting Genesis Pulse
 */
void utlp_loom_request_genesis_pulse(utlp_arbor_id_t arbor_id);

/**
 * @brief Get the stratum to use for Genesis chirps
 *
 * Returns the lowest stratum claimed by any ANCHOR arbor,
 * or 0xFF if no arbor is in ANCHOR state.
 *
 * @return Genesis stratum (typically 1), or 0xFF if not Time Lord
 */
uint8_t utlp_loom_get_genesis_stratum(void);

#ifdef __cplusplus
}
#endif
