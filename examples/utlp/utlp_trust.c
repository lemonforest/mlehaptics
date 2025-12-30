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
