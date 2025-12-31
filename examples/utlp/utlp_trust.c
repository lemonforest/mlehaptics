/**
 * @file utlp_trust.c
 * @brief The Metabolic Ledger Implementation
 *
 * @section origin Origin and Attribution
 * This module originated from a collaborative rumination session with
 * **Google Gemini** (December 2025). The implementation translates the
 * Biological Governance concepts from UTLP Technical Supplement S2 into
 * working embedded C code.
 *
 * > "Trust is not declared. It is accumulated."
 *
 * @section philosophy Design Philosophy
 *
 * The Metabolic Ledger treats trust as a metabolic resource that must be
 * continuously earned. Like biological immunity, the system:
 *
 * 1. **Learns from experience**: Hebbian "fire together, wire together"
 * 2. **Remembers threats longer than friends**: Asymmetric trust dynamics
 * 3. **Resists manipulation**: Median consensus defeats single-liar attacks
 * 4. **Forgets gracefully**: LRU eviction with health weighting
 *
 * @section algorithm Core Algorithm
 *
 * @subsection observation Recording an Observation
 * When a beacon is received:
 * @code
 * 1. Find or create peer entry (LRU eviction if full)
 * 2. Get swarm consensus (median of healthy peers)
 * 3. If no consensus: judge by self-consistency (jitter)
 * 4. If consensus exists: compare peer to median
 *    - Within 2ms: reward (+2 health)
 *    - 2-100ms off: drift penalty (-10 health)
 *    - >100ms off: lying penalty (-50 health)
 * 5. Update peer's last offset and timestamp
 * @endcode
 *
 * @subsection eviction LRU Eviction Strategy
 * When the ledger is full and a new peer appears:
 * @code
 * 1. If empty slot exists: use it
 * 2. Else find lowest-health peer
 * 3. Only evict if health < SYNC_THRESH ("weak")
 * 4. Never evict healthy peers for strangers
 *    "Don't kill a healthy friend for a stranger"
 * @endcode
 *
 * @section memory Memory Model
 * - Static allocation: g_peers[UTLP_TRUST_MAX_PEERS]
 * - No malloc/free - predictable embedded behavior
 * - 12 peer slots × ~24 bytes ≈ 288 bytes total
 *
 * @see docs/UTLP_Technical_Supplement_S2.md
 * @see Section 2.1: Hebbian Trust Accumulation
 * @see Section 2.2: Median Consensus Byzantine Resistance
 * @see Section 2.3: Asymmetric Trust Dynamics
 * @see Section 2.4: Silicon Dunbar's Number
 *
 * @version 1.0.0
 * @date 2025-12-29
 * @author Google Gemini (initial implementation)
 * @author Claude Opus 4.5 (documentation, header file, integration)
 *
 * @copyright
 * SPDX-License-Identifier: GPL-3.0-or-later
 * This file is part of the EMDR Bilateral Stimulation Device project.
 */

#include "utlp_trust.h"
#include "utlp_hal.h"
#include <string.h>
#include <stdlib.h> /* For qsort(), abs() */

/** @brief Logging tag for ESP-IDF log filtering */
static const char *TAG = "TRUST";

/*============================================================================
 * STATIC DATA
 *
 * The Ledger: Static allocation for predictable embedded behavior.
 * No malloc, no fragmentation, no surprises.
 *==========================================================================*/

/**
 * @brief The peer ledger array (Silicon Dunbar's Number)
 *
 * 12 slots for tracking peer trust and timing information.
 * Static allocation ensures predictable memory usage.
 */
static utlp_peer_ledger_t g_peers[UTLP_TRUST_MAX_PEERS];

/*============================================================================
 * INTERNAL HELPERS
 *==========================================================================*/

/**
 * @brief Clear a peer entry to initial state
 *
 * Zeroes all fields, effectively marking the slot as empty.
 * An empty slot has interactions == 0.
 *
 * @param p Pointer to peer entry to clear
 */
static void clear_peer(utlp_peer_ledger_t *p) {
    memset(p, 0, sizeof(utlp_peer_ledger_t));
}

/**
 * @brief Find or create a peer entry with LRU eviction
 *
 * Search strategy:
 * 1. Look for existing entry matching MAC
 * 2. Use empty slot if available
 * 3. Evict weakest peer (lowest health) if below threshold
 * 4. Reject stranger if all peers are healthy
 *
 * The eviction policy implements "don't kill a healthy friend for a stranger":
 * only peers below UTLP_TRUST_SYNC_THRESH can be evicted.
 *
 * @param mac 6-byte MAC address to find/create
 * @return Pointer to peer entry, or NULL if table full of healthy peers
 */
static utlp_peer_ledger_t* get_peer_entry(const uint8_t *mac) {
    int i;
    utlp_peer_ledger_t *oldest = &g_peers[0];
    utlp_peer_ledger_t *empty = NULL;
    uint32_t current_ms;
    uint64_t now_full;

    /* Get current time for LRU tracking */
    UTLP_HAL_GET_TIME(&now_full);
    current_ms = (uint32_t)(now_full / 1000);

    /* 1. Try to find existing peer */
    for (i = 0; i < UTLP_TRUST_MAX_PEERS; i++) {
        if (memcmp(g_peers[i].mac, mac, 6) == 0 && g_peers[i].interactions > 0) {
            return &g_peers[i];
        }
        if (g_peers[i].interactions == 0) {
            empty = &g_peers[i];
        }
        /* Track LRU candidate (lowest health is first to go, then oldest) */
        if (g_peers[i].health_score < oldest->health_score) {
            oldest = &g_peers[i];
        } else if (g_peers[i].health_score == oldest->health_score) {
            if ((current_ms - g_peers[i].last_seen_ms) > (current_ms - oldest->last_seen_ms)) {
                oldest = &g_peers[i];
            }
        }
    }

    /* 2. Use empty slot if available */
    if (empty) {
        clear_peer(empty);
        return empty;
    }

    /* 3. Eviction: Only evict if the oldest slot is "weak" (health < threshold).
     * Don't kill a healthy friend for a stranger.
     */
    if (oldest->health_score < UTLP_TRUST_SYNC_THRESH) {
        utlp_hal_log_warn(TAG, "Evicting weak peer %02X for new entry", oldest->mac[5]);
        clear_peer(oldest);
        return oldest;
    }

    /* Table full of healthy peers. Stranger ignored. */
    return NULL;
}

/**
 * @brief Comparison function for qsort (ascending int32_t)
 *
 * Used by utlp_trust_get_consensus() to sort offsets for median calculation.
 *
 * @param a Pointer to first int32_t
 * @param b Pointer to second int32_t
 * @return Negative if a < b, positive if a > b, zero if equal
 */
static int compare_int32(const void *a, const void *b) {
    int32_t val_a = *(const int32_t*)a;
    int32_t val_b = *(const int32_t*)b;
    if (val_a < val_b) return -1;
    if (val_a > val_b) return 1;
    return 0;
}

/*============================================================================
 * PUBLIC API
 *==========================================================================*/

/**
 * @brief Initialize the Metabolic Ledger
 *
 * Clears all peer entries to empty state (interactions = 0).
 * Safe to call multiple times - each call resets the ledger.
 *
 * Call this once at boot before processing any beacons.
 */
void utlp_trust_init(void) {
    int i;
    for (i = 0; i < UTLP_TRUST_MAX_PEERS; i++) {
        clear_peer(&g_peers[i]);
    }
    utlp_hal_log_info(TAG, "Metabolic Ledger Init: Capacity %d peers", UTLP_TRUST_MAX_PEERS);
}

/**
 * @brief Get median consensus offset from healthy peers
 *
 * Byzantine-resistant consensus: collects offsets from all peers with
 * health >= UTLP_TRUST_MIN_VOTE, sorts them, and returns the median.
 *
 * Why median instead of mean?
 * - A single liar reporting +1000000us cannot corrupt the median
 * - The median is robust to outliers (50% of voters must be corrupted)
 * - Perfect for adversarial environments
 *
 * @param[out] out_consensus_offset Median offset in microseconds
 * @return true if at least one healthy voter exists
 * @return false if no peers qualified to vote
 */
bool utlp_trust_get_consensus(int32_t *out_consensus_offset) {
    int32_t votes[UTLP_TRUST_MAX_PEERS];
    int count = 0;
    int i;

    /* Collect votes from HEALTHY peers only */
    for (i = 0; i < UTLP_TRUST_MAX_PEERS; i++) {
        if (g_peers[i].interactions > 0 && g_peers[i].health_score >= UTLP_TRUST_MIN_VOTE) {
            votes[count++] = g_peers[i].last_offset_us;
        }
    }

    if (count == 0) return false;

    /* Sort to find median */
    qsort(votes, count, sizeof(int32_t), compare_int32);

    /* Pick median (middle element, or average of two middle for even count) */
    if (count % 2 == 1) {
        *out_consensus_offset = votes[count / 2];
    } else {
        /* Average of two middle elements */
        *out_consensus_offset = (votes[count/2 - 1] + votes[count/2]) / 2;
    }

    return true;
}

/**
 * @brief Record a timing observation from a peer
 *
 * This is the heart of the Metabolic Ledger - the judgement engine.
 *
 * @par The Judgement Process:
 * 1. Find or create peer entry (may trigger LRU eviction)
 * 2. For new peers: initialize with probationary trust (UTLP_TRUST_STARTUP)
 * 3. Get swarm consensus (median of healthy peers)
 * 4. Compare this observation against consensus:
 *    - No consensus: judge by self-consistency (jitter < 2ms = small reward)
 *    - Consensus exists: deviation determines reward/penalty
 *
 * @par Asymmetric Trust Dynamics:
 * From S2: "One predator attack matters more than 25 peaceful encounters"
 * - Agreement: +2 health (slow growth)
 * - Drifting (2-100ms): -10 health (moderate penalty)
 * - Lying (>100ms): -50 health (severe penalty)
 *
 * @param mac        Peer's 6-byte MAC address
 * @param offset_us  Reported time offset in microseconds
 * @param stratum    Peer's claimed stratum level (1=Genesis, 2=Follower, etc.)
 */
void utlp_trust_record_observation(const uint8_t *mac, int32_t offset_us, uint8_t stratum) {
    utlp_peer_ledger_t *p = get_peer_entry(mac);
    int32_t consensus = 0;
    bool has_consensus;
    int32_t deviation;
    uint64_t now_full;
    uint32_t current_ms;

    if (!p) return; /* Table full of healthy peers, stranger ignored */

    UTLP_HAL_GET_TIME(&now_full);
    current_ms = (uint32_t)(now_full / 1000);

    /* New peer initialization - probationary trust */
    if (p->interactions == 0) {
        memcpy(p->mac, mac, 6);
        p->health_score = UTLP_TRUST_STARTUP; /* Probationary trust */
        p->interactions = 1;
        p->last_offset_us = offset_us;
        p->last_seen_ms = current_ms;
        p->stratum_claim = stratum;
        utlp_hal_log_info(TAG, "New Peer %02X:%02X (Health %d)", mac[4], mac[5], p->health_score);
        return;
    }

    /* Update metadata */
    p->last_seen_ms = current_ms;
    p->stratum_claim = stratum;

    /* THE JUDGEMENT: Compare against Swarm Consensus
     * If no consensus exists (I am alone), we trust lightly based on self-consistency.
     */
    has_consensus = utlp_trust_get_consensus(&consensus);

    if (!has_consensus) {
        /* No consensus yet. Just check self-consistency (jitter) */
        deviation = abs(p->last_offset_us - offset_us);
        /* If jitter is low (<2ms), small reward. Else small penalty. */
        if (deviation < 2000) {
            if (p->health_score < UTLP_TRUST_MAX) p->health_score++;
        } else {
            if (p->health_score > 0) p->health_score--;
        }
    } else {
        /* CONSENSUS EXISTS: The Crowd vs. The Peer */
        deviation = abs(offset_us - consensus);

        if (deviation < 2000) { /* 2ms Agreement Window */
            /* Hebbian Reward: Trust grows slowly */
            if (p->health_score <= (UTLP_TRUST_MAX - UTLP_REWARD_TRUTH)) {
                p->health_score += UTLP_REWARD_TRUTH;
            } else {
                p->health_score = UTLP_TRUST_MAX;
            }
            p->consecutive_hits++;
        } else {
            /* Penalty: Entropy eats trust quickly
             * >100ms = lying (severe), else = drifting (moderate)
             */
            uint8_t penalty = (deviation > 100000) ? UTLP_COST_LYING : UTLP_COST_DRIFTING;

            if (p->health_score > penalty) {
                p->health_score -= penalty;
            } else {
                p->health_score = 0;
            }
            p->consecutive_hits = 0;
            utlp_hal_log_warn(TAG, "Peer %02X punished (Dev: %ldus, Health: %d)",
                              mac[5], (long)deviation, p->health_score);
        }
    }

    /* Update last known offset AFTER judgement */
    p->last_offset_us = offset_us;
    if (p->interactions < 65000) p->interactions++;
}

/**
 * @brief Select the best peer for time synchronization
 *
 * Scans all tracked peers and returns the one with highest composite score.
 *
 * @par Scoring Formula:
 * @code
 * score = (health × 10) + (16 - stratum)
 * @endcode
 *
 * Health (0-255) dominates the score (0-2550 contribution).
 * Stratum provides small tie-breaker (0-16 contribution).
 *
 * @par Why Health Dominates:
 * A sick Stratum-1 peer (health=50) scores 500 + 15 = 515
 * A healthy Stratum-2 peer (health=200) scores 2000 + 14 = 2014
 *
 * The healthy Stratum-2 wins. Consistency beats proximity.
 *
 * @return Pointer to best peer, or NULL if no peer meets SYNC_THRESH
 */
utlp_peer_ledger_t* utlp_trust_select_best_peer(void) {
    int i;
    utlp_peer_ledger_t *best = NULL;
    uint32_t best_score = 0;

    for (i = 0; i < UTLP_TRUST_MAX_PEERS; i++) {
        utlp_peer_ledger_t *p = &g_peers[i];
        uint32_t composite_score;

        /* Filter: Must exist and meet threshold */
        if (p->interactions == 0) continue;
        if (p->health_score < UTLP_TRUST_SYNC_THRESH) continue;

        /* FORMULA: Survival of the Fittest
         * Health (0-255) is dominant. Stratum (0-255) is secondary.
         * Score = (Health * 10) + (16 - Stratum)
         * Note: Stratum 1 is better than 2, so we invert it.
         */
        composite_score = ((uint32_t)p->health_score * 10);

        /* Add small bonus for better stratum, but cap it so a sick Stratum 1
           never beats a healthy Stratum 2 */
        if (p->stratum_claim < 16) {
            composite_score += (16 - p->stratum_claim);
        }

        if (composite_score > best_score) {
            best_score = composite_score;
            best = p;
        }
    }

    return best;
}

/**
 * @brief Log current ledger status for debugging
 *
 * Outputs all tracked peers showing:
 * - MAC address (last byte for brevity)
 * - Health score (0-255)
 * - Claimed stratum
 * - Last offset in microseconds
 * - Total interaction count
 *
 * Also indicates whether swarm consensus exists.
 */
void utlp_trust_log_status(void) {
    int i;
    int32_t consensus = 0;
    bool has_cons = utlp_trust_get_consensus(&consensus);

    utlp_hal_log_info(TAG, "--- METABOLIC LEDGER (Consensus: %s) ---",
                      has_cons ? "YES" : "NO");

    for (i = 0; i < UTLP_TRUST_MAX_PEERS; i++) {
        if (g_peers[i].interactions > 0) {
            utlp_hal_log_info(TAG, "[%02X] Health:%3d | Strat:%2d | Ofs:%+ldus | Int:%d",
                              g_peers[i].mac[5],
                              g_peers[i].health_score,
                              g_peers[i].stratum_claim,
                              (long)g_peers[i].last_offset_us,
                              g_peers[i].interactions);
        }
    }
}

/**
 * @brief Check if I have quorum for entrainment action
 *
 * Quorum Sensing (S2 Section 6.2): Like bacteria waiting for autoinducer
 * concentration before turning virulent, nodes must verify they have
 * crowd support before entraining perceived bad actors.
 *
 * This prevents the "Crazy Old Man" scenario where an isolated Mature
 * node drifts, thinks the healthy swarm is wrong, and burns its entrainment
 * budget entraining valid packets.
 *
 * @param my_offset    My current time offset in microseconds
 * @param threshold_us Maximum deviation to count as "agreement"
 * @return true if >= 2 healthy peers agree with me within threshold
 */
bool utlp_trust_has_quorum(int32_t my_offset, int32_t threshold_us) {
    int i;
    int agreeing_peers = 0;

    for (i = 0; i < UTLP_TRUST_MAX_PEERS; i++) {
        /* Skip empty slots */
        if (g_peers[i].interactions == 0) continue;

        /* Skip unhealthy peers - they don't count for quorum */
        if (g_peers[i].health_score < UTLP_TRUST_MIN_VOTE) continue;

        /* Does this healthy peer agree with me? */
        int32_t deviation = abs(g_peers[i].last_offset_us - my_offset);
        if (deviation < threshold_us) {
            agreeing_peers++;
        }
    }

    /*
     * Quorum = at least 2 healthy peers agree with me.
     *
     * If I have 0-1 agreeing peers, I may be:
     * - Alone (no swarm yet)
     * - The outlier (I drifted, not them)
     *
     * Either way, I should NOT fire entrainment pulses.
     */
    return (agreeing_peers >= 2);
}

/**
 * @brief Look up a peer's health score
 *
 * Searches the Metabolic Ledger for a specific peer by MAC address.
 * Returns their current health score, or 0 if the peer is not tracked.
 *
 * @param mac Peer's 6-byte MAC address
 * @return Health score (0-255), or 0 if peer not found
 */
uint8_t utlp_trust_get_peer_health(const uint8_t *mac) {
    int i;

    for (i = 0; i < UTLP_TRUST_MAX_PEERS; i++) {
        if (g_peers[i].interactions == 0) continue;

        if (memcmp(g_peers[i].mac, mac, 6) == 0) {
            return g_peers[i].health_score;
        }
    }

    /* Peer not in Ledger - treat as unknown (lowest trust) */
    return 0;
}

/*============================================================================
 * PHASE 4: COHERENCE MONITORING
 *
 * Swarm-level health metrics for detecting sync loss.
 * "We will debug by observing distributions, not individual samples."
 *==========================================================================*/

/** @brief Threshold for "agreement" with consensus (2ms) */
#define COHERENCE_AGREEMENT_THRESHOLD_US    2000

/** @brief Minimum coherence percentage to be considered "coherent" */
#define COHERENCE_MIN_PERCENT               80

/** @brief Track last time swarm was fully coherent */
static uint32_t g_last_coherent_ms = 0;

/**
 * @brief Get current swarm coherence metrics
 */
void utlp_trust_get_coherence(utlp_coherence_t *out) {
    int i;
    int32_t consensus = 0;
    int32_t min_offset = INT32_MAX;
    int32_t max_offset = INT32_MIN;
    uint8_t healthy_count = 0;
    uint8_t agreeing_count = 0;
    uint32_t now_ms;

    /* Initialize output */
    memset(out, 0, sizeof(*out));

    /* First, get consensus (need it to measure agreement) */
    if (!utlp_trust_get_consensus(&consensus)) {
        /* No consensus available - no healthy peers */
        out->is_coherent = false;
        return;
    }
    out->consensus_us = consensus;

    /* Count healthy peers and measure spread */
    for (i = 0; i < UTLP_TRUST_MAX_PEERS; i++) {
        if (g_peers[i].interactions == 0) continue;
        if (g_peers[i].health_score < UTLP_TRUST_SYNC_THRESH) continue;

        healthy_count++;

        /* Track min/max for spread calculation */
        if (g_peers[i].last_offset_us < min_offset) {
            min_offset = g_peers[i].last_offset_us;
        }
        if (g_peers[i].last_offset_us > max_offset) {
            max_offset = g_peers[i].last_offset_us;
        }

        /* Check if this peer agrees with consensus */
        int32_t deviation = g_peers[i].last_offset_us - consensus;
        if (deviation < 0) deviation = -deviation;
        if (deviation < COHERENCE_AGREEMENT_THRESHOLD_US) {
            agreeing_count++;
        }
    }

    out->healthy_peers = healthy_count;
    out->agreeing_peers = agreeing_count;

    /* Calculate spread (only valid if we have peers) */
    if (healthy_count > 0 && min_offset != INT32_MAX) {
        out->drift_spread_us = max_offset - min_offset;
    }

    /* Calculate coherence percentage */
    if (healthy_count > 0) {
        out->coherence_pct = (uint8_t)((100 * agreeing_count) / healthy_count);
    }

    /* Determine if coherent (>= 80% agreement) */
    out->is_coherent = (out->coherence_pct >= COHERENCE_MIN_PERCENT);

    /* Track time since last coherent state */
    now_ms = (uint32_t)(utlp_hal_get_micros() / 1000);
    if (out->is_coherent) {
        g_last_coherent_ms = now_ms;
        out->last_coherent_ms = 0;  /* Coherent now */
    } else {
        if (g_last_coherent_ms == 0) {
            /* Never been coherent */
            out->last_coherent_ms = now_ms;
        } else {
            out->last_coherent_ms = now_ms - g_last_coherent_ms;
        }
    }
}

/**
 * @brief Log coherence metrics (macro-state logging)
 */
void utlp_trust_log_coherence(void) {
    utlp_coherence_t c;
    utlp_trust_get_coherence(&c);

    if (c.healthy_peers == 0) {
        utlp_hal_log_info(TAG, "COHERENCE: No healthy peers (swarm empty)");
        return;
    }

    if (c.is_coherent) {
        utlp_hal_log_info(TAG, "COHERENCE: %d%% (%d/%d agree) | spread=%ldus | consensus=%+ldus",
                          c.coherence_pct, c.agreeing_peers, c.healthy_peers,
                          (long)c.drift_spread_us, (long)c.consensus_us);
    } else {
        utlp_hal_log_warn(TAG, "COHERENCE LOST: %d%% (%d/%d agree) | spread=%ldus | drift=%lums",
                          c.coherence_pct, c.agreeing_peers, c.healthy_peers,
                          (long)c.drift_spread_us, (unsigned long)c.last_coherent_ms);
    }
}

/*============================================================================
 * GENESIS PULSE DETECTION (S2.24)
 *
 * Fast detection of rebooted peers via beacon interval tracking.
 * Prevents epoch adoption from freshly-rebooted nodes with stale trust.
 *
 * The Problem: Past trust persists in the Metabolic Ledger across peer reboots.
 * A peer that was trusted at health=150 before rebooting still has health=150.
 * When it sends genesis beacons (atomic time ~100ms), we must NOT adopt
 * its epoch - that would corrupt our established timeline.
 *
 * The Solution: Two-pronged detection:
 * 1. Interval tracking: Genesis phases use 100-1000ms intervals (vs 60s steady)
 * 2. Regression check: Rebooted peer's atomic time goes backwards
 *
 * Defense: Block epoch adoption, but allow phase entrainment once they
 * stabilize. "Proof of Stability" required for epoch authority.
 *==========================================================================*/

/**
 * @brief Check if a peer is currently in genesis pulse phase
 *
 * Genesis pulse detection works by observing beacon intervals:
 * - Phase 1: 100ms (0-1s uptime)
 * - Phase 2: 500ms (1-5s uptime)
 * - Phase 3: 1000ms (5-10s uptime)
 * - Phase 4: 10000ms (10-60s uptime)
 * - Steady: 60000ms (60s+ uptime)
 *
 * If observed_interval_ms < 2000, peer is likely in genesis phases 1-3.
 *
 * @param peer Pointer to peer ledger entry
 * @return true if peer appears to be in genesis pulse phase
 */
bool utlp_trust_is_genesis_pulsing(const utlp_peer_ledger_t *peer) {
    if (!peer) return false;

    /* Need at least 2 observations to have a valid interval estimate */
    if (peer->interactions < UTLP_MIN_INTERVAL_OBSERVATIONS) {
        return false;  /* Unknown, assume not genesis pulsing */
    }

    /* Genesis pulsing if observed interval is below threshold */
    return (peer->observed_interval_ms > 0 &&
            peer->observed_interval_ms < UTLP_GENESIS_PULSE_THRESHOLD_MS);
}

/**
 * @brief Check if a peer's atomic time shows regression (reboot indicator)
 *
 * Atomic time should always increase monotonically. If a peer's reported
 * TX time is significantly behind their expected time (based on last known
 * TX + elapsed time), they have rebooted.
 *
 * @par Expected Time Calculation:
 * @code
 * expected = last_tx_time + (now_ms - last_seen_ms) * 1000
 * // (ms to us conversion, assuming 1x drift rate)
 * @endcode
 *
 * @param peer          Pointer to peer ledger entry
 * @param reported_tx   TX timestamp from current beacon (microseconds)
 * @param now_ms        Current local time in milliseconds
 * @return true if atomic time regression detected (peer rebooted)
 */
bool utlp_trust_check_regression(const utlp_peer_ledger_t *peer,
                                  int64_t reported_tx,
                                  uint32_t now_ms) {
    int64_t elapsed_us;
    int64_t expected_tx;

    if (!peer) return false;

    /* Need previous TX time to check for regression */
    if (peer->last_tx_time_us == 0) {
        return false;  /* First observation, no regression possible */
    }

    /* Calculate expected TX time (last TX + elapsed time) */
    elapsed_us = (int64_t)(now_ms - peer->last_seen_ms) * 1000;
    expected_tx = peer->last_tx_time_us + elapsed_us;

    /*
     * Check for regression: Is reported TX significantly behind expected?
     *
     * We use a generous threshold (10 seconds) to avoid false positives
     * from jitter or network delays. A reboot causes regression of
     * millions of microseconds (the peer's entire uptime), so 10s is
     * conservative enough to catch real reboots without false alarms.
     */
    if (reported_tx < (expected_tx - (int64_t)UTLP_REGRESSION_THRESHOLD_US)) {
        return true;  /* Regression detected - peer rebooted! */
    }

    return false;
}

/**
 * @brief Update a peer's TX time tracking after receiving beacon
 *
 * This updates the interval estimate (EMA) and TX time tracking for
 * future genesis pulse and regression detection.
 *
 * @par Interval Tracking:
 * Uses exponential moving average (EMA) with simple formula:
 * @code
 * new_interval = (old_interval + observed_interval) / 2
 * @endcode
 *
 * This provides ~3-sample smoothing, enough to detect genesis pulse
 * within 300-500ms while avoiding single-observation noise.
 *
 * @param mac         Peer's 6-byte MAC address
 * @param tx_time_us  TX timestamp from current beacon
 * @param now_ms      Current local time in milliseconds
 */
void utlp_trust_update_tx_tracking(const uint8_t *mac,
                                    int64_t tx_time_us,
                                    uint32_t now_ms) {
    int i;
    utlp_peer_ledger_t *peer = NULL;

    /* Find peer in ledger */
    for (i = 0; i < UTLP_TRUST_MAX_PEERS; i++) {
        if (g_peers[i].interactions > 0 &&
            memcmp(g_peers[i].mac, mac, 6) == 0) {
            peer = &g_peers[i];
            break;
        }
    }

    if (!peer) return;  /* Peer not found */

    /* Update interval estimate if we have a previous observation */
    if (peer->last_seen_ms > 0) {
        uint32_t observed_interval = now_ms - peer->last_seen_ms;

        if (peer->observed_interval_ms == 0) {
            /* First interval observation */
            peer->observed_interval_ms = (uint16_t)observed_interval;
        } else {
            /* EMA: new = (old + observed) / 2 */
            peer->observed_interval_ms =
                (peer->observed_interval_ms + (uint16_t)observed_interval) / 2;
        }
    }

    /* Update first_seen_ms if this is a fresh entry */
    if (peer->first_seen_ms == 0) {
        peer->first_seen_ms = now_ms;
    }

    /* Update TX time tracking for regression detection */
    peer->last_tx_time_us = tx_time_us;
}

/**
 * @brief Get a peer's ledger entry by MAC address
 *
 * Public accessor for peer ledger entries. Used by utlp.c to access
 * genesis pulse detection fields.
 *
 * @param mac Peer's 6-byte MAC address
 * @return Pointer to peer entry, or NULL if not found
 */
utlp_peer_ledger_t* utlp_trust_get_peer(const uint8_t *mac) {
    int i;

    for (i = 0; i < UTLP_TRUST_MAX_PEERS; i++) {
        if (g_peers[i].interactions > 0 &&
            memcmp(g_peers[i].mac, mac, 6) == 0) {
            return &g_peers[i];
        }
    }

    return NULL;
}
