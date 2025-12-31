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
 *   health-weighted eviction. Protects "old friends" over "juveniles".
 *
 * - **Median Consensus**: Byzantine-resistant voting where a single liar
 *   cannot corrupt the swarm's perception of time.
 *
 * @section algorithms Algorithm Cross-References
 *
 * This module draws from multiple domains:
 *
 * @subsection algo_hebbian Hebbian Learning (Neuroscience, 1949)
 * Donald Hebb's postulate: "Cells that fire together, wire together."
 * When peers consistently agree with consensus, their synaptic connection
 * (health score) strengthens. This is **Long-Term Potentiation (LTP)** in
 * silicon form. The +2 reward implements associative learning where
 * temporal correlation drives trust accumulation.
 *
 * @par Academic Reference:
 * Hebb, D.O. (1949). "The Organization of Behavior: A Neuropsychological Theory"
 *
 * @subsection algo_median Median Filtering (Signal Processing)
 * The consensus mechanism uses median instead of mean because median is
 * robust to outliers. In a population of N voters, an attacker must corrupt
 * >50% to shift the median. This is the same property exploited by
 * **median filters** in image processing to remove salt-and-pepper noise.
 *
 * @par Byzantine Resistance:
 * With 2f+1 honest nodes, median consensus tolerates f Byzantine liars.
 * A single attacker claiming offset=+∞ cannot move the median.
 *
 * @par Academic Reference:
 * Lamport, L., Shostak, R., Pease, M. (1982). "The Byzantine Generals Problem"
 *
 * @subsection algo_asymmetric Asymmetric Cost Functions (Decision Theory)
 * The 25:1 penalty ratio (-50 for lying vs +2 for truth) implements
 * **asymmetric loss functions** from statistical decision theory. In
 * adversarial environments, false negatives (trusting a liar) are more
 * costly than false positives (distrusting an honest peer). This mirrors
 * **Prospect Theory**: losses loom larger than gains.
 *
 * @par Biological Analog:
 * One predator encounter teaches more than 25 peaceful grazing sessions.
 * The amygdala (fear memory) uses similar asymmetric learning rates.
 *
 * @par Academic Reference:
 * Kahneman, D., Tversky, A. (1979). "Prospect Theory: An Analysis of Decision under Risk"
 *
 * @subsection algo_dunbar Dunbar's Number (Anthropology, 1992)
 * Robin Dunbar found that primate neocortex size correlates with social
 * group size (~150 for humans). Our "Silicon Dunbar's Number" of 12 peers
 * is deliberately small to:
 * - Fit in embedded memory (288 bytes)
 * - Force prioritization (can't track everyone)
 * - Enable health-weighted eviction (protect proven friends)
 *
 * @par LRU with Health Weighting:
 * Unlike pure LRU caches, we bias eviction toward low-health peers.
 * "Don't kill a healthy friend for a stranger."
 *
 * @par Academic Reference:
 * Dunbar, R.I.M. (1992). "Neocortex size as a constraint on group size in primates"
 *
 * @subsection algo_ema Exponential Moving Average (Statistics)
 * Health velocity and coherence velocity use EMA with α=0.1:
 * @code
 * new_value = α × sample + (1-α) × old_value
 * @endcode
 * This provides smooth tracking with ~10-sample half-life. In integer form:
 * @code
 * new_value = (sample + 9 × old_value) / 10
 * @endcode
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

/**
 * @defgroup genesis_detection Genesis Pulse Detection (S2.24)
 *
 * Fast detection of rebooted peers via beacon interval tracking.
 * Prevents epoch adoption from freshly-rebooted nodes with stale trust.
 * @{
 */

/**
 * @brief Beacon interval threshold for genesis pulse detection
 *
 * If a peer's observed beacon interval is below this threshold, they are
 * likely in genesis pulse phase (recently rebooted). Genesis phases 1-3
 * use intervals of 100ms, 500ms, and 1000ms respectively.
 *
 * 2000ms allows detection within the first 3-5 beacons (~300-500ms).
 */
#define UTLP_GENESIS_PULSE_THRESHOLD_MS  2000

/**
 * @brief Atomic time regression threshold for reboot detection
 *
 * If a peer's reported TX time is more than this amount BEHIND their
 * expected time, they have rebooted. 10ms provides margin for jitter.
 *
 * Expected time = last_tx_time + elapsed * (1 + drift_rate)
 */
#define UTLP_REGRESSION_THRESHOLD_US     10000000  /* 10 seconds */

/**
 * @brief Minimum observations before trusting interval estimate
 *
 * Need at least 2 observations to compute an interval.
 */
#define UTLP_MIN_INTERVAL_OBSERVATIONS   2

/** @} */ /* genesis_detection */

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
 *
 * @section genesis_detection Genesis Pulse Detection (S2.24)
 * The first_seen_ms and observed_interval_ms fields enable fast detection
 * of rebooted peers. A peer broadcasting at genesis intervals (100-500ms)
 * can be identified within 300-500ms, preventing epoch adoption from
 * freshly-rebooted nodes that retain high trust from previous sessions.
 *
 * @section regression_detection Atomic Time Regression Detection
 * The last_tx_time_us field tracks the peer's last transmitted atomic time.
 * If a peer's atomic time goes backwards (regression), it indicates a reboot
 * and triggers trust penalty + epoch adoption block.
 */
typedef struct {
    /* 8-byte fields first */
    int64_t  last_tx_time_us;   /**< Last TX timestamp from peer (regression check) */

    /* 4-byte fields */
    uint32_t last_seen_ms;      /**< Timestamp of last observation (LRU tracking) */
    uint32_t first_seen_ms;     /**< When we first observed this peer (reboot detection) */
    int32_t  last_offset_us;    /**< Last reported time offset in microseconds */

    /* 2-byte fields */
    uint16_t interactions;      /**< Total observation count (caps at 65000) */
    uint16_t consecutive_hits;  /**< Consecutive agreements with consensus */
    uint16_t observed_interval_ms; /**< EMA of beacon intervals from this peer */

    /* 1-byte fields and arrays */
    uint8_t  mac[6];            /**< Peer MAC address (identity) */
    uint8_t  health_score;      /**< Trust level 0-255 (higher = more trusted) */
    uint8_t  stratum_claim;     /**< Last claimed stratum (1=Genesis, 2=Follower) */
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
 * @brief Check if I have quorum for entrainment action
 *
 * Quorum Sensing (S2 Section 6.2): Like bacteria waiting for autoinducer
 * concentration before turning virulent, nodes must verify they have
 * crowd support before entraining perceived bad actors.
 *
 * This prevents the "Crazy Old Man" scenario where an isolated Mature
 * node drifts, thinks the healthy swarm is wrong, and burns its entrainment
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
 * GENESIS PULSE DETECTION (S2.24)
 *
 * Fast detection of rebooted peers via beacon interval tracking.
 * Prevents epoch adoption from freshly-rebooted nodes with stale trust.
 *==========================================================================*/

/**
 * @brief Check if a peer is currently in genesis pulse phase
 *
 * A peer is considered "genesis pulsing" if their observed beacon interval
 * is below UTLP_GENESIS_PULSE_THRESHOLD_MS (2000ms). This indicates they
 * are in genesis phases 1-3 (100ms, 500ms, 1000ms intervals) and have
 * likely just rebooted.
 *
 * Use this to block epoch adoption from rebooted peers while still
 * allowing phase entrainment once they stabilize.
 *
 * @param peer Pointer to peer ledger entry
 * @return true if peer appears to be in genesis pulse phase
 * @return false if peer is at steady-state beacon interval or unknown
 */
bool utlp_trust_is_genesis_pulsing(const utlp_peer_ledger_t *peer);

/**
 * @brief Check if a peer's atomic time shows regression (reboot indicator)
 *
 * Compares the peer's reported TX time against their expected time
 * (last_tx_time + elapsed). If regression exceeds UTLP_REGRESSION_THRESHOLD_US,
 * the peer has likely rebooted.
 *
 * @param peer          Pointer to peer ledger entry
 * @param reported_tx   TX timestamp from current beacon
 * @param now_ms        Current local time in milliseconds
 * @return true if atomic time regression detected (peer rebooted)
 * @return false if time is progressing normally
 */
bool utlp_trust_check_regression(const utlp_peer_ledger_t *peer,
                                  int64_t reported_tx,
                                  uint32_t now_ms);

/**
 * @brief Update a peer's TX time tracking after receiving beacon
 *
 * Call this after processing a beacon to update the peer's last_tx_time_us
 * for future regression checks. Also updates first_seen_ms if this is a
 * new peer (detected reboot clears this).
 *
 * @param mac         Peer's 6-byte MAC address
 * @param tx_time_us  TX timestamp from current beacon
 * @param now_ms      Current local time in milliseconds
 */
void utlp_trust_update_tx_tracking(const uint8_t *mac,
                                    int64_t tx_time_us,
                                    uint32_t now_ms);

/**
 * @brief Get a peer's ledger entry by MAC address
 *
 * Returns pointer to the peer's ledger entry if found.
 *
 * @param mac Peer's 6-byte MAC address
 * @return Pointer to peer entry, or NULL if not found
 */
utlp_peer_ledger_t* utlp_trust_get_peer(const uint8_t *mac);

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
    /* 4-byte fields first */
    int32_t  consensus_us;       /**< Current median consensus offset */
    int32_t  drift_spread_us;    /**< Max - min offset among healthy peers */
    uint32_t last_coherent_ms;   /**< Time since all healthy agreed (0 = now) */
    /* 1-byte fields */
    uint8_t  healthy_peers;      /**< Peers with health >= SYNC_THRESH */
    uint8_t  agreeing_peers;     /**< Healthy peers within ±2ms of consensus */
    uint8_t  coherence_pct;      /**< Agreement rate: 100 * agreeing / healthy */
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
