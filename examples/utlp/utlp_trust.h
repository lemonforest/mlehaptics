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
#include "utlp_arbor.h"  /* For utlp_arbor_id_t in polychromatic helpers */

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
 * @brief Number of transport arbors (Blood-Brain Barrier)
 *
 * Phase 9: Per-arbor trust tracking. Each peer has independent health
 * scores for each transport to prevent cross-contamination of reputation.
 *
 * A peer that is healthy on 802.15.4 but jittery on WiFi should not have
 * its WiFi misbehavior pollute its 15.4 reputation.
 *
 * Matches UTLP_ARBOR_COUNT from utlp_arbor.h:
 *   0 = WiFi (ESP-NOW)
 *   1 = 802.15.4
 *   2 = BLE
 */
#define UTLP_MAX_ARBORS         3

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

/**
 * @brief Bootstrap grace period for new peer relationships (v3.8 PT-13)
 *
 * During the first N interactions with a new peer, skip the self-consistency
 * penalty in the no-consensus path. Two unsynchronized devices WILL have high
 * jitter between consecutive observations - this is expected, not a sign of
 * untrustworthiness.
 *
 * Without this grace period, peers start at health=50 but get penalized (-1)
 * on every observation because jitter > 2ms. This creates a "bootstrap catch-22"
 * where health can only DECREASE, never reaching the SYNC_THRESH (100) needed
 * to be considered "healthy" for ADAPTIVE immunity.
 *
 * @par Biological Analogy
 * When cells first meet, they must establish communication. Initial handshake
 * jitter is normal - don't penalize a newcomer for taking time to sync.
 *
 * @see utlp_trust_record_observation_arbor() - no-consensus path
 */
#define UTLP_TRUST_BOOTSTRAP_INTERACTIONS   5

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

/**
 * @brief Tenure threshold for treating peer as potentially genesis-pulsing (ms)
 *
 * After seniority bankruptcy, a peer's interaction count and interval are reset
 * but we know they just rebooted. If tenure (now - first_seen_ms) is below this
 * threshold, treat as genesis-pulsing regardless of interval observations.
 *
 * This matches UTLP_GENESIS_DETECT_WINDOW_US (5 seconds) from utlp_config.h.
 *
 * @par v3.5 FIX: Seniority bankruptcy genesis bypass (S2 Claim 137)
 * Without this check, a rebooted peer with interactions=1 and observed_interval_ms=0
 * would bypass genesis pulse detection in INNATE IMMUNITY paths.
 */
#define UTLP_GENESIS_TENURE_THRESHOLD_MS 5000

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
 *
 * STRUCT PACKING CONVENTION (Memory Alignment Optimization):
 * Always order struct fields from largest to smallest alignment:
 *   1. 8-byte fields first (int64_t, uint64_t, double, pointers on 64-bit)
 *   2. 4-byte fields (int32_t, uint32_t, float)
 *   3. 2-byte fields (int16_t, uint16_t)
 *   4. 1-byte fields and arrays (uint8_t, bool, char[])
 *
 * This minimizes padding bytes inserted by the compiler for alignment,
 * reducing memory footprint on embedded systems.
 *
 * Example - BAD (15 bytes + 5 padding = 20 bytes):
 *   uint8_t  a;     // 1 byte + 7 padding
 *   uint64_t b;     // 8 bytes
 *   uint8_t  c;     // 1 byte + 3 padding
 *   uint32_t d;     // 4 bytes
 *
 * Example - GOOD (15 bytes + 1 padding = 16 bytes):
 *   uint64_t b;     // 8 bytes
 *   uint32_t d;     // 4 bytes
 *   uint8_t  a;     // 1 byte
 *   uint8_t  c;     // 1 byte + 2 padding (at end, unavoidable)
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
 * @section blood_brain_barrier Blood-Brain Barrier (Phase 9)
 *
 * Trust is tracked **per-arbor** (per-transport), not globally per-peer.
 * A peer healthy on 802.15.4 but jittery on WiFi should have independent
 * reputation on each transport. This prevents cross-contamination:
 *
 * | Scenario | Old (Global) | New (Per-Arbor) |
 * |----------|--------------|-----------------|
 * | WiFi jitter | Peer loses all trust | Only WiFi trust degrades |
 * | 15.4 failure | Full reputation wipe | 15.4 isolated, WiFi OK |
 *
 * Arrays indexed by arbor_id: [0]=WiFi, [1]=15.4, [2]=BLE
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
 *
 * @section packing Memory Layout (Packed)
 * Uses __attribute__((packed)) for consistent layout across platforms.
 * _Static_assert verifies expected size (important for NVS serialization).
 */
typedef struct __attribute__((packed)) {
    /* 8-byte fields first */
    int64_t  last_tx_time_us;   /**< Last TX timestamp from peer (regression check) */

    /* 4-byte array fields (per-arbor) */
    uint32_t last_seen_ms[UTLP_MAX_ARBORS];   /**< Per-arbor last seen (LRU) */
    int32_t  last_offset_us[UTLP_MAX_ARBORS]; /**< Per-arbor timing offset */

    /* 4-byte scalar field */
    uint32_t first_seen_ms;     /**< When we first observed this peer (reboot detection) */

    /* 2-byte fields */
    uint16_t interactions;      /**< Total observation count (caps at 65000) */
    uint16_t consecutive_hits;  /**< Consecutive agreements with consensus */
    uint16_t observed_interval_ms; /**< EMA of beacon intervals from this peer */

    /* 1-byte fields and arrays */
    uint8_t  mac[6];            /**< Peer MAC address (identity) */
    uint8_t  health_score[UTLP_MAX_ARBORS]; /**< Per-arbor trust 0-255 */
    uint8_t  stratum_claim;     /**< Last claimed stratum (1=Genesis, 2=Follower) */

    /*========================================================================
     * SPECTRAL RETINA: Per-Arbor RSSI Tracking (Claim: Polychromatic Awareness)
     *
     * "See the Radio Color"
     *
     * WHY: WiFi (2.4GHz) and 802.15.4 (2.4GHz but different modulation) experience
     * different multipath propagation. A peer that appears at -45dBm on WiFi but
     * -68dBm on 802.15.4 is in a "cluttered" RF environment where signals are
     * bouncing differently for each transport.
     *
     * WHAT: Store the most recent RSSI reading from each transport so we can
     * compare them when the same peer is seen on multiple transports.
     *
     * HOW: On each beacon reception, store RSSI indexed by arbor_id. When both
     * transports have recent readings (< 5s), calculate the delta and log it.
     * Large deltas (> 10dB) indicate multipath clutter.
     *
     * FUTURE: Polychromatic Confidence Weighting - timing from cluttered
     * environments gets lower weight in consensus calculations.
     *======================================================================*/
    int8_t   last_rssi[UTLP_MAX_ARBORS];        /**< Per-arbor RSSI (dBm) */
    uint32_t rssi_timestamp_ms[UTLP_MAX_ARBORS]; /**< When RSSI was recorded (ms) */

    /*========================================================================
     * SESSION CONTINUITY: Boot Instance Tracking (Purple Team PT-6)
     *
     * "The Ghost has died. Long live the Ghost."
     *
     * WHY: A rebooted device has the same MAC but a NEW Session_Salt.
     * This is definitive proof of reboot - the "Ghost in the Machine" died
     * and was replaced. We use this to instantly detect reboots on the
     * FIRST beacon, before interval-based or regression-based methods.
     *
     * WHAT: Track the last observed Session_Salt from each peer. If it
     * changes, the peer has rebooted and loses all accumulated trust
     * ("Seniority Bankruptcy").
     *
     * HOW: Compare pkt->session_salt to last_session_salt. If different
     * (and last_session_salt != 0 meaning "never seen"), wipe all
     * seniority metrics: first_seen_ms, health_score[], stratum_claim,
     * interactions, consecutive_hits, observed_interval_ms.
     *
     * DEFENSE: Prevents "Fresh Boot Genesis Attack" where a rebooted
     * high-trust peer immediately claims Genesis authority before
     * interval/regression detection fires.
     *======================================================================*/
    uint16_t last_session_salt;     /**< Last observed Session_Salt (0 = never seen) */
} utlp_peer_ledger_t;

/**
 * @brief Verify ledger struct packing
 *
 * Expected layout (packed):
 *   int64_t last_tx_time_us:         8 bytes
 *   uint32_t last_seen_ms[3]:       12 bytes
 *   int32_t last_offset_us[3]:      12 bytes
 *   uint32_t first_seen_ms:          4 bytes
 *   uint16_t interactions:           2 bytes
 *   uint16_t consecutive_hits:       2 bytes
 *   uint16_t observed_interval_ms:   2 bytes
 *   uint8_t mac[6]:                  6 bytes
 *   uint8_t health_score[3]:         3 bytes
 *   uint8_t stratum_claim:           1 byte
 *   --- Spectral Retina (Phase 11) ---
 *   int8_t last_rssi[3]:             3 bytes
 *   uint32_t rssi_timestamp_ms[3]:  12 bytes
 *   --- Session Continuity (Purple Team PT-6) ---
 *   uint16_t last_session_salt:      2 bytes
 *   TOTAL:                          69 bytes
 */
_Static_assert(sizeof(utlp_peer_ledger_t) == 69, "Ledger struct packing incorrect");

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
 *
 * @deprecated Use utlp_trust_record_observation_arbor() for per-arbor tracking.
 *             This function assumes UTLP_ARBOR_WIFI (arbor 0) for backward compat.
 */
void utlp_trust_record_observation(const uint8_t *mac, int32_t offset_us, uint8_t stratum);

/**
 * @brief Record a timing observation with arbor context (Blood-Brain Barrier)
 *
 * Phase 9: Per-arbor trust tracking. Records the observation only against
 * the specific transport that received the packet, preventing WiFi jitter
 * from polluting 802.15.4 reputation (or vice versa).
 *
 * Phase 11 (Spectral Retina): Also stores RSSI for cross-transport comparison.
 * When the same peer is seen on multiple transports within 5 seconds, the
 * RSSI delta reveals multipath clutter in the RF environment.
 *
 * Phase 12 (PT-6): Session_Salt detection added. If peer's salt changes
 * (same MAC, different salt), triggers SENIORITY BANKRUPTCY - all trust
 * metrics are wiped. "The Ghost has died. Long live the Ghost."
 *
 * @param mac          Peer's 6-byte MAC address
 * @param offset_us    Reported time offset in microseconds
 * @param stratum      Peer's claimed stratum level
 * @param arbor_id     Transport that received this packet (0=WiFi, 1=154, 2=BLE)
 * @param rssi         Received signal strength (dBm)
 * @param session_salt Peer's session_salt (16-bit boot instance ID)
 */
void utlp_trust_record_observation_arbor(const uint8_t *mac, int32_t offset_us,
                                          uint8_t stratum, uint8_t arbor_id,
                                          int8_t rssi, uint16_t session_salt);

/**
 * @brief Get health score for a specific arbor (Blood-Brain Barrier)
 *
 * @param mac        Peer's 6-byte MAC address
 * @param arbor_id   Transport to query (0=WiFi, 1=154, 2=BLE)
 * @return Health score 0-255, or 0 if peer not found
 */
uint8_t utlp_trust_get_health_arbor(const uint8_t *mac, uint8_t arbor_id);

/*============================================================================
 * SPECTRAL RETINA API (Phase 11)
 *==========================================================================*/

/**
 * @brief Log spectral coherence for a peer (Spectral Retina)
 *
 * Compares RSSI readings across transports to detect multipath clutter.
 * Only logs if the peer has been seen on another transport within
 * UTLP_RSSI_STALE_MS (5 seconds).
 *
 * Output format:
 *   I (12345) RETINA: Peer 5c | WiFi:-45 15.4:-52 | Delta: 7 dB | CLEAR
 *   I (12456) RETINA: Peer 5c | WiFi:-45 15.4:-68 | Delta: 23 dB | CLUTTERED
 *
 * @param peer          Pointer to peer ledger entry
 * @param current_arbor The arbor that just received a packet (0=WiFi, 1=154)
 * @param now_ms        Current time in milliseconds (for staleness check)
 */
void utlp_trust_log_spectral_coherence(const utlp_peer_ledger_t *peer,
                                        uint8_t current_arbor, uint32_t now_ms);

/**
 * @brief Snapshot per-arbor ledger state for dormancy
 *
 * Called before arbor yield to preserve reputation snapshot.
 * Allows comparison on wake to detect anomalies.
 *
 * @param arbor_id   Transport being yielded
 */
void utlp_trust_snapshot_arbor(uint8_t arbor_id);

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
 * @par v3.5 FIX: int64_t offset parameter
 * Changed from int32_t to int64_t to match g_aatr.time_offset type.
 * Prevents truncation of offsets exceeding ±35 minutes (int32_t max ~2.1B µs).
 * On 32-bit platforms, comparison is still safe since peer offsets are stored
 * as int32_t in the ledger (truncation happens at storage, not comparison).
 *
 * @param my_offset    My current time offset in microseconds (64-bit)
 * @param threshold_us Maximum deviation to count as "agreement" (typically 2000us)
 * @return true if >= 2 healthy peers agree with me within threshold
 * @return false if I am alone or disagreeing with the crowd
 */
bool utlp_trust_has_quorum(int64_t my_offset, int32_t threshold_us);

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
 * Genesis pulse detection uses the peer's ATOMIC TIME (TX timestamp) as the
 * primary indicator of how long they've been running. If peer_tx_time >= 5s,
 * the peer is clearly established and NOT genesis-pulsing, regardless of when
 * we first observed them.
 *
 * For peers with atomic time < 5s, we fall back to beacon interval measurement.
 * Peers transmitting at intervals below UTLP_GENESIS_PULSE_THRESHOLD_MS
 * (2000ms) are in genesis phases 1-3 and have likely just rebooted.
 *
 * BIOLOGICAL ANALOGY: A cell's age is intrinsic, not based on when a neighbor
 * first noticed it. An established organism tells you how old it is; a newborn
 * cannot fake being old (their atomic time starts at 0).
 *
 * Use this to block epoch adoption from rebooted peers while still allowing
 * phase entrainment once they stabilize.
 *
 * @param peer          Pointer to peer ledger entry
 * @param peer_tx_time  Peer's TX timestamp from current beacon (µs since boot)
 * @return true if peer appears to be in genesis pulse phase
 * @return false if peer is established or at steady-state beacon interval
 */
bool utlp_trust_is_genesis_pulsing(const utlp_peer_ledger_t *peer,
                                    int64_t peer_tx_time);

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
 * POLYCHROMATIC STRATUM HELPERS (Claim 253)
 *
 * Per-arbor neighbor queries for polychromatic stratum asymmetry.
 * Enable bridge nodes to detect authority presence on each transport.
 *==========================================================================*/

/**
 * @brief Count neighbors with stratum <= threshold on a specific arbor
 *
 * Used by polychromatic logic to detect authority presence on a transport.
 * Only counts peers that have been seen recently on the specified arbor.
 *
 * @param arbor_id  Which arbor to scan
 * @param max_stratum  Count neighbors with stratum <= this value
 * @return Count of matching neighbors
 *
 * @see Claim 253: Polychromatic Stratum Asymmetry
 */
uint8_t utlp_trust_count_neighbors_by_stratum_arbor(
    utlp_arbor_id_t arbor_id, uint8_t max_stratum);

/**
 * @brief Get lowest (best) stratum seen on a specific arbor
 *
 * Used by polychromatic logic to determine what stratum to adopt when
 * an authority appears on a previously silent secondary transport.
 *
 * @param arbor_id  Which arbor to scan
 * @return Best (lowest) stratum, or 255 if no neighbors on that arbor
 *
 * @see Claim 253: Polychromatic Stratum Asymmetry
 */
uint8_t utlp_trust_get_best_stratum_arbor(utlp_arbor_id_t arbor_id);

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
