/**
 * @file utlp_trust.h
 * @brief The Metabolic Ledger - Trust and Reputation for UTLP Peers
 *
 * @section origin Origin
 * This module originated from a collaborative rumination session with
 * Google Gemini (December 2025), implementing the Biological Governance
 * model described in UTLP Technical Supplement S2.
 *
 * @section philosophy Philosophy: Governance Without Politics
 *
 * Traditional distributed systems use **political governance**: elections,
 * leaders, quorums, voting. These models assume rational actors making
 * deliberate choices. They break when nodes misbehave, lie, or drift.
 *
 * This module implements **biological governance**: no leaders, no elections,
 * no votes. Trust emerges from observation. Authority is earned through
 * demonstrated reliability, not declared through protocol messages.
 *
 * > "Trust is not declared. It is accumulated."
 * > — UTLP Technical Supplement S2
 *
 * This is an **experiment in post-human coordination**. We are testing
 * whether immune system principles can govern distributed systems more
 * robustly than political metaphors borrowed from human institutions.
 *
 * @section overview Overview
 * The Metabolic Ledger implements an immune-system-inspired trust model
 * for distributed time synchronization. Peers earn trust through consistent
 * agreement with swarm consensus; trust decays rapidly when peers deviate.
 *
 * Key concepts from S2:
 * - **Hebbian Learning**: "Neurons that fire together, wire together"
 *   Peers agreeing with consensus earn trust incrementally.
 *
 * - **Asymmetric Trust Dynamics**: Trust grows slowly (+2 per observation)
 *   but falls rapidly (-10 to -50 per deviation). One predator attack
 *   matters more than 25 peaceful encounters.
 *
 * - **Silicon Dunbar's Number**: Bounded peer tracking (12 slots) with
 *   health-weighted eviction. Protects "old friends" over "rookies".
 *
 * - **Median Consensus**: Byzantine-resistant voting where a single liar
 *   cannot corrupt the swarm's perception of time.
 *
 * @section experiment The Experiment
 *
 * We hypothesize that biological governance will:
 * 1. **Self-heal** from Byzantine failures without central coordination
 * 2. **Resist Sybil attacks** through earned-trust barriers
 * 3. **Adapt** to changing network conditions without reconfiguration
 * 4. **Fail gracefully** under attack rather than catastrophically
 *
 * To falsify this hypothesis, observe the statistical logging output.
 * If the swarm cannot converge, or if attackers can corrupt consensus,
 * the experiment has failed. The logs will show it.
 *
 * @section usage Usage
 * @code
 * // Initialize at boot
 * utlp_trust_init();
 *
 * // Record observations from received beacons
 * utlp_trust_record_observation(peer_mac, offset_us, stratum);
 *
 * // Get consensus for self-correction
 * int32_t consensus;
 * if (utlp_trust_get_consensus(&consensus)) {
 *     // Apply consensus offset
 * }
 *
 * // Select best peer for synchronization
 * utlp_peer_ledger_t *best = utlp_trust_select_best_peer();
 * @endcode
 *
 * @see docs/UTLP_Technical_Supplement_S2.md - Biological Governance
 * @see Section 2.1: Hebbian Trust Accumulation
 * @see Section 2.2: Median Consensus Byzantine Resistance
 * @see Section 2.4: Silicon Dunbar's Number
 *
 * @version 1.0.0
 * @date 2025-12-29
 *
 * @copyright
 * SPDX-License-Identifier: GPL-3.0-or-later
 * This file is part of the EMDR Bilateral Stimulation Device project.
 */

#pragma once

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/*============================================================================
 * CONFIGURATION CONSTANTS
 *
 * These values implement the asymmetric trust dynamics from S2.
 * "Trust is not declared. It is accumulated."
 *==========================================================================*/

/**
 * @defgroup trust_config Trust Configuration
 * @{
 */

/**
 * @brief Maximum number of tracked peers (Silicon Dunbar's Number)
 *
 * From S2 Section 2.4: "12 peers sufficient for robust mesh timing"
 * Small enough for embedded memory, large enough for local mesh.
 */
#define UTLP_TRUST_MAX_PEERS    12

/**
 * @brief Maximum health score (0-255 range)
 *
 * Full trust requires ~125 consecutive agreements from startup.
 */
#define UTLP_TRUST_MAX          255

/**
 * @brief Initial health for new peers (probationary)
 *
 * Below sync threshold - must prove consistency before trusted.
 * ~25 good observations needed to reach SYNC_THRESH.
 */
#define UTLP_TRUST_STARTUP      50

/**
 * @brief Minimum health to participate in sync (be used as time source)
 *
 * Peers below this threshold are tracked but not trusted for timing.
 */
#define UTLP_TRUST_SYNC_THRESH  100

/**
 * @brief Minimum health to participate in consensus voting
 *
 * Slightly above startup - needs some history to influence swarm.
 */
#define UTLP_TRUST_MIN_VOTE     60

/** @} */ /* trust_config */

/**
 * @defgroup trust_dynamics Trust Dynamics (Asymmetric)
 *
 * From S2: "Trust grows slowly but falls rapidly"
 * One predator attack matters more than 25 peaceful encounters.
 * @{
 */

/**
 * @brief Reward for agreeing with consensus (slow growth)
 *
 * +2 per observation matching consensus within 2ms.
 * ~50 good observations to go from startup to sync threshold.
 */
#define UTLP_REWARD_TRUTH       2

/**
 * @brief Penalty for moderate drift (2ms - 100ms deviation)
 *
 * -10 per drifting observation. One drift erases 5 good observations.
 */
#define UTLP_COST_DRIFTING      10

/**
 * @brief Penalty for lying (>100ms deviation)
 *
 * -50 per lying observation. Severe punishment for gross inaccuracy.
 * One lie erases 25 good observations.
 */
#define UTLP_COST_LYING         50

/** @} */ /* trust_dynamics */

/*============================================================================
 * HAL COMPATIBILITY
 *
 * Map generic time access to UTLP HAL functions.
 *==========================================================================*/

/**
 * @brief Get current time via HAL
 *
 * Maps to utlp_hal_get_micros() for ESP32.
 * For C64 compatibility, this would use the union-based approach.
 *
 * @param ptr_out Pointer to uint64_t to store result
 */
#define UTLP_HAL_GET_TIME(ptr_out)  (*(ptr_out) = utlp_hal_get_micros())

/* Forward declaration - defined in utlp_hal.h */
uint64_t utlp_hal_get_micros(void);

/*============================================================================
 * DATA STRUCTURES
 *==========================================================================*/

/**
 * @brief Peer ledger entry - tracks trust and timing for one peer
 *
 * This is the "memory B cell" from S2's immune system analogy.
 * Each entry tracks a peer's health score, interaction history,
 * and last known timing offset.
 *
 * @note Static allocation - no malloc. Array of UTLP_TRUST_MAX_PEERS entries.
 */
typedef struct {
    uint8_t  mac[6];            /**< Peer MAC address (identity) */
    uint8_t  health_score;      /**< Trust level 0-255 (higher = more trusted) */
    uint8_t  stratum_claim;     /**< Last claimed stratum (1=Genesis, 2=Follower) */
    uint16_t interactions;      /**< Total observation count (caps at 65000) */
    uint16_t consecutive_hits;  /**< Consecutive agreements with consensus */
    uint32_t last_seen_ms;      /**< Timestamp of last observation (LRU tracking) */
    int32_t  last_offset_us;    /**< Last reported time offset in microseconds */
} utlp_peer_ledger_t;

/*============================================================================
 * PUBLIC API
 *==========================================================================*/

/**
 * @brief Initialize the Metabolic Ledger
 *
 * Clears all peer entries. Must be called before any other trust functions.
 * Safe to call multiple times (idempotent).
 */
void utlp_trust_init(void);

/**
 * @brief Record a timing observation from a peer
 *
 * This is the main entry point called when receiving a beacon.
 * The observation is judged against swarm consensus:
 *
 * - **Agreement** (within 2ms): Health increases by UTLP_REWARD_TRUTH
 * - **Drifting** (2ms - 100ms): Health decreases by UTLP_COST_DRIFTING
 * - **Lying** (>100ms): Health decreases by UTLP_COST_LYING
 *
 * If no consensus exists yet, the peer is judged by self-consistency
 * (low jitter from previous observation = small reward).
 *
 * @param mac        Peer's 6-byte MAC address
 * @param offset_us  Reported time offset in microseconds
 * @param stratum    Peer's claimed stratum level
 */
void utlp_trust_record_observation(const uint8_t *mac, int32_t offset_us, uint8_t stratum);

/**
 * @brief Get median consensus offset from healthy peers
 *
 * Collects time offsets from all peers with health >= UTLP_TRUST_MIN_VOTE,
 * sorts them, and returns the median. This is Byzantine-resistant:
 * a single liar cannot corrupt the result.
 *
 * @param[out] out_consensus_offset  Median offset in microseconds
 * @return true if consensus available (at least one healthy voter)
 * @return false if no healthy peers to form consensus
 */
bool utlp_trust_get_consensus(int32_t *out_consensus_offset);

/**
 * @brief Select the best peer for time synchronization
 *
 * Returns the peer with highest composite score:
 *   score = (health × 10) + (16 - stratum)
 *
 * Health dominates, stratum is tie-breaker. A healthy Stratum-2 peer
 * beats a sick Stratum-1 peer.
 *
 * @return Pointer to best peer entry, or NULL if no peer meets threshold
 */
utlp_peer_ledger_t* utlp_trust_select_best_peer(void);

/**
 * @brief Log current ledger status for debugging
 *
 * Outputs all tracked peers with their health, stratum, offset, and
 * interaction count. Also shows whether consensus exists.
 */
void utlp_trust_log_status(void);

/**
 * @brief Check if I have quorum for defensive action
 *
 * Quorum Sensing (S2 Section 6.2): Like bacteria waiting for autoinducer
 * concentration before turning virulent, nodes must verify they have
 * crowd support before attacking perceived bad actors.
 *
 * This prevents the "Crazy Old Man" scenario where an isolated Senior
 * node drifts, thinks the healthy swarm is wrong, and burns its defensive
 * budget attacking valid packets.
 *
 * @param my_offset    My current time offset in microseconds
 * @param threshold_us Maximum deviation to count as "agreement" (typically 2000us)
 * @return true if >= 2 healthy peers agree with me within threshold
 * @return false if I am alone or disagreeing with the crowd
 */
bool utlp_trust_has_quorum(int32_t my_offset, int32_t threshold_us);

/**
 * @brief Look up a peer's health score
 *
 * Returns the current health score for a specific peer, or 0 if
 * the peer is not in the Ledger.
 *
 * @param mac Peer's 6-byte MAC address
 * @return Health score (0-255), or 0 if peer not found
 */
uint8_t utlp_trust_get_peer_health(const uint8_t *mac);

/*============================================================================
 * PHASE 4: COHERENCE MONITORING (S2 Section 7)
 *
 * "We will debug by observing distributions, not individual samples."
 *
 * These functions provide swarm-level health metrics for detecting
 * when the network is losing coherence (sync loss, Byzantine attack,
 * partition, etc.)
 *==========================================================================*/

/**
 * @brief Swarm coherence metrics snapshot
 *
 * Captures the current state of swarm synchronization quality.
 * Used for macro-state logging and coherence alerts.
 */
typedef struct {
    uint8_t  healthy_peers;      /**< Peers with health >= SYNC_THRESH */
    uint8_t  agreeing_peers;     /**< Healthy peers within ±2ms of consensus */
    uint8_t  coherence_pct;      /**< Agreement rate: 100 * agreeing / healthy */
    int32_t  consensus_us;       /**< Current median consensus offset */
    int32_t  drift_spread_us;    /**< Max - min offset among healthy peers */
    uint32_t last_coherent_ms;   /**< Time since all healthy agreed (0 = now) */
    bool     is_coherent;        /**< True if coherence >= 80% */
} utlp_coherence_t;

/**
 * @brief Get current swarm coherence metrics
 *
 * Calculates coherence by comparing healthy peer offsets to consensus.
 * A coherent swarm has >= 80% of healthy peers within ±2ms.
 *
 * @param[out] out Coherence metrics snapshot
 */
void utlp_trust_get_coherence(utlp_coherence_t *out);

/**
 * @brief Log coherence metrics (macro-state logging)
 *
 * Outputs a single-line summary of swarm health:
 *   COHERENCE: 100% (3/3 agree) | spread=450us | consensus=-120us
 *
 * Call this periodically (every 10-60s) for Phase 4 observability.
 */
void utlp_trust_log_coherence(void);

#ifdef __cplusplus
}
#endif
