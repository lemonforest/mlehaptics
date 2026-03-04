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
#include "utlp_config.h"    /* v3.9: UTLP_LINEAGE_LOYALTY_THRESHOLD_US */
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
 * LINEAGE LOYALTY CONTEXT (v3.9)
 *
 * The trust system uses lineage context to suppress health growth for
 * peers on foreign timelines. Set by utlp.c before each observation.
 *==========================================================================*/

static int32_t s_lineage_offset = 0;  /* int32_t to match offset_us parameter type */
static bool s_lineage_committed = false;

/* Forward declaration: Defined in utlp.c, called from Seniority Bankruptcy handler */
extern void utlp_lineage_on_source_bankruptcy(const uint8_t *mac);

void utlp_trust_set_lineage_context(int64_t my_offset, bool committed) {
    s_lineage_offset = (int32_t)my_offset;  /* Truncate to match offset_us in record_observation */
    s_lineage_committed = committed;
}

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
 * @brief Get aggregate health score across all arbors (Blood-Brain Barrier)
 *
 * Returns the MAXIMUM health score across all transports.
 * Used for eviction decisions: don't evict a peer that's healthy on ANY arbor.
 *
 * @param p Pointer to peer entry
 * @return Maximum health score across all arbors
 */
static uint8_t get_aggregate_health(const utlp_peer_ledger_t *p) {
    uint8_t max_health = 0;
    int i;
    for (i = 0; i < UTLP_MAX_ARBORS; i++) {
        if (p->health_score[i] > max_health) {
            max_health = p->health_score[i];
        }
    }
    return max_health;
}

/**
 * @brief Get aggregate last_seen_ms across all arbors
 *
 * Returns the MOST RECENT last_seen_ms across all transports.
 * Used for LRU decisions: a peer active on any arbor is "recently seen".
 *
 * @param p Pointer to peer entry
 * @return Most recent last_seen_ms across all arbors
 */
static uint32_t get_aggregate_last_seen(const utlp_peer_ledger_t *p) {
    uint32_t max_seen = 0;
    int i;
    for (i = 0; i < UTLP_MAX_ARBORS; i++) {
        if (p->last_seen_ms[i] > max_seen) {
            max_seen = p->last_seen_ms[i];
        }
    }
    return max_seen;
}

/**
 * @brief Find or create a peer entry with LRU eviction
 *
 * Search strategy:
 * 1. Look for existing entry matching MAC
 * 2. Use empty slot if available
 * 3. Evict weakest peer (lowest aggregate health) if below threshold
 * 4. Reject stranger if all peers are healthy on any arbor
 *
 * The eviction policy implements "don't kill a healthy friend for a stranger":
 * only peers below UTLP_TRUST_SYNC_THRESH on ALL arbors can be evicted.
 *
 * @note Phase 9 (Blood-Brain Barrier): Uses aggregate health across all arbors
 *       for eviction decisions. A peer healthy on ANY transport is protected.
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
    uint8_t oldest_health, peer_health;
    uint32_t oldest_seen, peer_seen;

    /* Get current time for LRU tracking */
    UTLP_HAL_GET_TIME(&now_full);
    current_ms = (uint32_t)(now_full / 1000);

    /* Get aggregate values for oldest candidate */
    oldest_health = get_aggregate_health(&g_peers[0]);
    oldest_seen = get_aggregate_last_seen(&g_peers[0]);

    /* 1. Try to find existing peer */
    for (i = 0; i < UTLP_TRUST_MAX_PEERS; i++) {
        if (memcmp(g_peers[i].mac, mac, 6) == 0 && g_peers[i].interactions > 0) {
            return &g_peers[i];
        }
        if (g_peers[i].interactions == 0) {
            empty = &g_peers[i];
        }

        /* Track LRU candidate using AGGREGATE health (Blood-Brain Barrier)
         * Lowest aggregate health is first to go, then oldest
         */
        peer_health = get_aggregate_health(&g_peers[i]);
        peer_seen = get_aggregate_last_seen(&g_peers[i]);

        if (peer_health < oldest_health) {
            oldest = &g_peers[i];
            oldest_health = peer_health;
            oldest_seen = peer_seen;
        } else if (peer_health == oldest_health) {
            if ((current_ms - peer_seen) > (current_ms - oldest_seen)) {
                oldest = &g_peers[i];
                oldest_health = peer_health;
                oldest_seen = peer_seen;
            }
        }
    }

    /* 2. Use empty slot if available */
    if (empty) {
        clear_peer(empty);
        return empty;
    }

    /* 3. Eviction: Only evict if aggregate health < threshold.
     * Don't kill a healthy friend for a stranger.
     * A peer healthy on ANY arbor is protected.
     */
    if (oldest_health < UTLP_TRUST_SYNC_THRESH) {
        utlp_hal_log_warn(TAG, "Evicting weak peer %02X:%02X for new entry (agg_health=%d)",
                          oldest->mac[4], oldest->mac[5], oldest_health);
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
 * aggregate health >= UTLP_TRUST_MIN_VOTE, sorts them, and returns median.
 *
 * Why median instead of mean?
 * - A single liar reporting +1000000us cannot corrupt the median
 * - The median is robust to outliers (50% of voters must be corrupted)
 * - Perfect for adversarial environments
 *
 * @note Phase 9 (Blood-Brain Barrier): Uses aggregate health and the most
 *       recent offset across all arbors. Timing consensus is transport-agnostic.
 *
 * @param[out] out_consensus_offset Median offset in microseconds
 * @return true if at least one healthy voter exists
 * @return false if no peers qualified to vote
 */
bool utlp_trust_get_consensus(int32_t *out_consensus_offset) {
    int32_t votes[UTLP_TRUST_MAX_PEERS];
    int count = 0;
    int i, j;
    uint8_t agg_health;
    uint32_t best_seen;
    int best_arbor;

    /* Collect votes from HEALTHY peers only (aggregate health check) */
    for (i = 0; i < UTLP_TRUST_MAX_PEERS; i++) {
        if (g_peers[i].interactions == 0) continue;

        agg_health = get_aggregate_health(&g_peers[i]);
        if (agg_health >= UTLP_TRUST_MIN_VOTE) {
            /* Use the most recent offset (from whichever arbor saw them last) */
            best_seen = 0;
            best_arbor = 0;
            for (j = 0; j < UTLP_MAX_ARBORS; j++) {
                if (g_peers[i].last_seen_ms[j] > best_seen) {
                    best_seen = g_peers[i].last_seen_ms[j];
                    best_arbor = j;
                }
            }
            votes[count++] = g_peers[i].last_offset_us[best_arbor];
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
 * @brief Record a timing observation from a peer (backward compatible wrapper)
 *
 * @deprecated Use utlp_trust_record_observation_arbor() for per-arbor tracking.
 *             This function assumes UTLP_ARBOR_WIFI (arbor 0) for backward compat
 *             and UTLP_RSSI_INVALID for RSSI (no spectral data).
 *
 * @param mac        Peer's 6-byte MAC address
 * @param offset_us  Reported time offset in microseconds
 * @param stratum    Peer's claimed stratum level (1=Genesis, 2=Follower, etc.)
 */
void utlp_trust_record_observation(const uint8_t *mac, int32_t offset_us, uint8_t stratum) {
    /* Default to arbor 0 (WiFi), invalid RSSI, and 0 session_salt for backward compatibility.
     * Session_salt 0 means "unknown session" - PT-6 salt change detection is skipped. */
    utlp_trust_record_observation_arbor(mac, offset_us, stratum, 0, UTLP_RSSI_INVALID, 0);
}

/**
 * @brief Record a timing observation with arbor context (Blood-Brain Barrier)
 *
 * This is the heart of the Metabolic Ledger - the judgement engine.
 *
 * @par Phase 9: Per-Arbor Trust Tracking
 * Health scores are tracked independently per transport (arbor). A peer that
 * is healthy on 802.15.4 but jittery on WiFi will only have its WiFi health
 * degraded - the 15.4 reputation remains intact.
 *
 * @par The Judgement Process:
 * 1. Find or create peer entry (may trigger LRU eviction)
 * 2. For new peers: initialize with probationary trust on THIS arbor
 * 3. Get swarm consensus (median of aggregate-healthy peers)
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
 * @param arbor_id   Transport that received this packet (0=WiFi, 1=154, 2=BLE)
 * @param rssi       Received signal strength (dBm), or UTLP_RSSI_INVALID if unavailable
 *
 * @par Phase 11: Spectral Retina
 * In addition to timing judgement, we store RSSI for each arbor and log
 * spectral coherence when both WiFi and 802.15.4 have recent readings.
 * This reveals environmental multipath ("Radio Color") for future confidence weighting.
 */
void utlp_trust_record_observation_arbor(const uint8_t *mac, int32_t offset_us,
                                          uint8_t stratum, uint8_t arbor_id,
                                          int8_t rssi, uint16_t session_salt) {
    utlp_peer_ledger_t *p = get_peer_entry(mac);
    int32_t consensus = 0;
    bool has_consensus;
    int32_t deviation;
    uint64_t now_full;
    uint32_t current_ms;
    int i;

    if (!p) return; /* Table full of healthy peers, stranger ignored */
    if (arbor_id >= UTLP_MAX_ARBORS) arbor_id = 0; /* Bounds check */

    UTLP_HAL_GET_TIME(&now_full);
    current_ms = (uint32_t)(now_full / 1000);

    /* New peer initialization - probationary trust on ALL arbors */
    if (p->interactions == 0) {
        memcpy(p->mac, mac, 6);
        /* Initialize all arbor health scores to STARTUP (probationary) */
        for (i = 0; i < UTLP_MAX_ARBORS; i++) {
            p->health_score[i] = UTLP_TRUST_STARTUP;
            p->last_seen_ms[i] = 0;
            p->last_offset_us[i] = 0;
            /* Spectral Retina: Initialize RSSI tracking */
            p->last_rssi[i] = UTLP_RSSI_INVALID;
            p->rssi_timestamp_ms[i] = 0;
        }
        p->interactions = 1;
        p->last_offset_us[arbor_id] = offset_us;
        p->last_seen_ms[arbor_id] = current_ms;
        p->stratum_claim = stratum;
        p->first_seen_ms = current_ms;
        /* PT-6: Initialize session_salt tracking (0 = never seen until now) */
        p->last_session_salt = session_salt;
        /* Spectral Retina: Store first RSSI reading if valid */
        if (rssi != UTLP_RSSI_INVALID) {
            p->last_rssi[arbor_id] = rssi;
            p->rssi_timestamp_ms[arbor_id] = current_ms;
        }
        utlp_hal_log_info(TAG, "New Peer %02X:%02X (arbor=%d, health=%d, rssi=%d, salt=0x%04X)",
                          mac[4], mac[5], arbor_id, p->health_score[arbor_id], rssi, session_salt);
        return;
    }

    /*=========================================================================
     * PT-6: SESSION CONTINUITY ENFORCEMENT ("Seniority Bankruptcy")
     *
     * "The Ghost has died. Long live the Ghost."
     *
     * If session_salt changed (same MAC, different salt), the peer rebooted.
     * ALL accumulated political capital is forfeit. The peer must re-earn
     * trust through consistent behavior, starting from ZERO (not STARTUP).
     *
     * WHY ZERO NOT STARTUP:
     * - STARTUP (50) is "probationary" - benefit of the doubt
     * - A rebooted high-trust peer could have been compromised/attacked
     * - Zero trust forces re-validation before ANY influence
     * - Genesis Guard will reject them until they earn >100 health
     *
     * DEFENSE IN DEPTH: This is the FASTEST detection method:
     * - Genesis Pulse:    Needs 2+ beacons to detect interval < 2000ms
     * - Time Regression:  Needs time to go backwards > 10s (slow)
     * - Session Salt:     FIRST beacon after reboot triggers this
     *========================================================================*/
    if (p->last_session_salt != 0 && p->last_session_salt != session_salt) {
        utlp_hal_log_warn(TAG, "*** SENIORITY BANKRUPTCY *** Peer %02X:%02X salt 0x%04X->0x%04X (REBOOT DETECTED)",
                          mac[4], mac[5], p->last_session_salt, session_salt);

        /* WIPE: Reset seniority clock (tenure starts over) */
        p->first_seen_ms = current_ms;

        /* WIPE: Reset trust history across ALL arbors to ZERO (punitive, not probationary) */
        for (i = 0; i < UTLP_MAX_ARBORS; i++) {
            p->health_score[i] = 0;         /* Zero trust, not STARTUP */
            p->last_seen_ms[i] = 0;
            p->last_offset_us[i] = 0;
            p->last_rssi[i] = UTLP_RSSI_INVALID;
            p->rssi_timestamp_ms[i] = 0;
        }

        /* WIPE: Reset interaction counters */
        p->interactions = 1;              /* This IS first valid observation in new life */
        p->consecutive_hits = 0;
        p->observed_interval_ms = 0;

        /* WIPE: Force stratum re-evaluation (worst possible) */
        p->stratum_claim = 255;

        /* WIPE: Reset TX tracking for regression detection */
        p->last_tx_time_us = 0;

        /* Update to new salt and set initial values */
        p->last_session_salt = session_salt;
        p->last_seen_ms[arbor_id] = current_ms;
        /* BUG FIX (PT-9): Do NOT set stratum here - it was just wiped to 255 at line 470.
         * Per S2 Claim 137, bankrupted peers must re-earn trust from scratch.
         * The stratum will be set normally once this peer proves itself again. */
        if (rssi != UTLP_RSSI_INVALID) {
            p->last_rssi[arbor_id] = rssi;
            p->rssi_timestamp_ms[arbor_id] = current_ms;
        }

        /*
         * v3.9: Notify lineage system of source bankruptcy.
         * If this peer was our best time source, the lineage system
         * transitions COMMITTED → GRIEVING to allow re-adoption of
         * the rebooted peer's new timeline.
         */
        utlp_lineage_on_source_bankruptcy(mac);

        /* Log and return - peer starts fresh journey to trustworthiness */
        utlp_hal_log_info(TAG, "Peer %02X:%02X reborn (arbor=%d, health=0, rssi=%d, salt=0x%04X)",
                          mac[4], mac[5], arbor_id, rssi, session_salt);
        return;
    }

    /* Update session_salt tracking (same peer, same salt = continuous session) */
    p->last_session_salt = session_salt;

    /* Update per-arbor metadata */
    p->last_seen_ms[arbor_id] = current_ms;
    p->stratum_claim = stratum;

    /* Spectral Retina: Store RSSI for this arbor if valid */
    if (rssi != UTLP_RSSI_INVALID) {
        p->last_rssi[arbor_id] = rssi;
        p->rssi_timestamp_ms[arbor_id] = current_ms;
    }

    /*
     * LINEAGE LOYALTY HEALTH GATE (v3.9)
     *
     * When we are COMMITTED to a lineage, peers whose observed offset
     * deviates far from our lineage are "foreign." They are consistent
     * on a DIFFERENT timeline — their consistency should not earn them
     * trust on OUR ledger.
     *
     * We still record the observation (interactions++, interval tracking,
     * RSSI, etc.) but skip the health reward/penalty cycle entirely.
     * This prevents foreign peers from building trust pre-adoption.
     *
     * Once a foreign peer joins our lineage (via Phenotype Truth demotion
     * + adoption), their subsequent offsets will be near ours and normal
     * health scoring resumes.
     */
    if (s_lineage_committed) {
        int32_t lineage_dev = offset_us - s_lineage_offset;
        if (lineage_dev < 0) lineage_dev = -lineage_dev;

        if (lineage_dev > (int32_t)UTLP_LINEAGE_LOYALTY_THRESHOLD_US) {
            /* Foreign lineage: record observation metadata but skip health changes */
            p->last_offset_us[arbor_id] = offset_us;
            if (p->interactions < 65000) p->interactions++;
            utlp_hal_log_info(TAG,
                "LINEAGE: Foreign peer %02X:%02X (arbor=%d, dev=%lld us), health frozen at %d",
                mac[4], mac[5], arbor_id, (long long)lineage_dev,
                p->health_score[arbor_id]);
            return;  /* Skip THE JUDGEMENT entirely */
        }
    }

    /* THE JUDGEMENT: Compare against Swarm Consensus
     * If no consensus exists (I am alone), we trust lightly based on self-consistency.
     *
     * Note: Consensus uses aggregate health, but judgement affects THIS arbor only.
     */
    has_consensus = utlp_trust_get_consensus(&consensus);

    if (!has_consensus) {
        /* No consensus yet. Just check self-consistency (jitter) on THIS arbor */
        deviation = abs(p->last_offset_us[arbor_id] - offset_us);

        /*
         * v3.8 PT-13 FIX: Bootstrap Grace Period
         *
         * During first N interactions, skip the self-consistency penalty.
         * Two unsynchronized devices WILL have high jitter between consecutive
         * observations - this is expected during initial sync, not a sign of
         * untrustworthiness.
         *
         * Without this grace, peers start at health=50 but get penalized (-1)
         * on every observation because jitter > 2ms. Health can only DECREASE,
         * never reaching SYNC_THRESH (100) = "bootstrap catch-22".
         */
        if (p->interactions < UTLP_TRUST_BOOTSTRAP_INTERACTIONS) {
            /* During bootstrap: only reward stability, never penalize */
            if (deviation < 2000) {
                if (p->health_score[arbor_id] < UTLP_TRUST_MAX) {
                    p->health_score[arbor_id]++;
                }
            }
            /* No penalty during bootstrap - jitter is expected */
        } else {
            /* Normal self-consistency check after bootstrap complete */
            if (deviation < 2000) {
                if (p->health_score[arbor_id] < UTLP_TRUST_MAX) {
                    p->health_score[arbor_id]++;
                }
            } else {
                if (p->health_score[arbor_id] > 0) {
                    p->health_score[arbor_id]--;
                }
            }
        }
    } else {
        /* CONSENSUS EXISTS: The Crowd vs. The Peer on THIS arbor */
        deviation = abs(offset_us - consensus);

        if (deviation < 2000) { /* 2ms Agreement Window */
            /* Hebbian Reward: Trust grows slowly */
            if (p->health_score[arbor_id] <= (UTLP_TRUST_MAX - UTLP_REWARD_TRUTH)) {
                p->health_score[arbor_id] += UTLP_REWARD_TRUTH;
            } else {
                p->health_score[arbor_id] = UTLP_TRUST_MAX;
            }
            p->consecutive_hits++;
        } else {
            /* Penalty: Entropy eats trust quickly on THIS arbor
             * >100ms = lying (severe), else = drifting (moderate)
             */
            uint8_t penalty = (deviation > 100000) ? UTLP_COST_LYING : UTLP_COST_DRIFTING;

            if (p->health_score[arbor_id] > penalty) {
                p->health_score[arbor_id] -= penalty;
            } else {
                p->health_score[arbor_id] = 0;
            }
            p->consecutive_hits = 0;
            utlp_hal_log_warn(TAG, "Peer %02X:%02X punished (arbor=%d, dev=%ldus, health=%d)",
                              mac[4], mac[5], arbor_id, (long)deviation, p->health_score[arbor_id]);
        }
    }

    /* Update last known offset on THIS arbor AFTER judgement */
    p->last_offset_us[arbor_id] = offset_us;
    if (p->interactions < 65000) p->interactions++;

    /* Spectral Retina: Log coherence when we have fresh RSSI from multiple arbors */
    if (rssi != UTLP_RSSI_INVALID) {
        utlp_trust_log_spectral_coherence(p, arbor_id, current_ms);
    }
}

/**
 * @brief Select the best peer for time synchronization
 *
 * Scans all tracked peers and returns the one with highest composite score.
 *
 * @par Scoring Formula:
 * @code
 * score = (aggregate_health × 10) + (16 - stratum)
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
 * @note Phase 9 (Blood-Brain Barrier): Uses aggregate health across all arbors.
 *       A peer healthy on ANY transport qualifies.
 *
 * @return Pointer to best peer, or NULL if no peer meets SYNC_THRESH
 */
utlp_peer_ledger_t* utlp_trust_select_best_peer(void) {
    int i;
    utlp_peer_ledger_t *best = NULL;
    uint32_t best_score = 0;
    uint8_t agg_health;
    uint8_t active_peer_count = 0;
    uint8_t threshold;

    /*
     * v3.8 PT-13c FIX: Count active peers first for N=2 threshold lowering
     *
     * When only 1 peer exists (N=2 swarm), use a lower threshold to break
     * the bootstrap catch-22. At N=2, we cannot use quorum consensus, so
     * we must trust the only peer we have - even during bootstrap.
     *
     * With N≥3 peers, we maintain higher standards because we have options.
     */
    for (i = 0; i < UTLP_TRUST_MAX_PEERS; i++) {
        if (g_peers[i].interactions > 0) {
            active_peer_count++;
        }
    }

    /* Lower threshold for N=2 (single peer) vs normal for N≥3 */
    threshold = (active_peer_count == 1) ?
                UTLP_TRUST_STARTUP :     /* 50 - accept single peer at startup health */
                UTLP_TRUST_SYNC_THRESH;  /* 100 - normal threshold for N≥3 */

    for (i = 0; i < UTLP_TRUST_MAX_PEERS; i++) {
        utlp_peer_ledger_t *p = &g_peers[i];
        uint32_t composite_score;

        /* Filter: Must exist and meet threshold (aggregate health) */
        if (p->interactions == 0) continue;
        agg_health = get_aggregate_health(p);
        if (agg_health < threshold) continue;

        /* FORMULA: Survival of the Fittest
         * Aggregate Health (0-255) is dominant. Stratum (0-255) is secondary.
         * Score = (Health * 10) + (16 - Stratum)
         * Note: Stratum 1 is better than 2, so we invert it.
         */
        composite_score = ((uint32_t)agg_health * 10);

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
 * - Per-arbor health scores [WiFi/15.4/BLE]
 * - Aggregate health (max across arbors)
 * - Claimed stratum
 * - Total interaction count
 *
 * Also indicates whether swarm consensus exists.
 *
 * @note Phase 9 (Blood-Brain Barrier): Shows per-arbor health breakdown.
 */
void utlp_trust_log_status(void) {
    int i;
    int32_t consensus = 0;
    bool has_cons = utlp_trust_get_consensus(&consensus);
    uint8_t agg_health;

    utlp_hal_log_info(TAG, "--- METABOLIC LEDGER (Consensus: %s) ---",
                      has_cons ? "YES" : "NO");

    for (i = 0; i < UTLP_TRUST_MAX_PEERS; i++) {
        if (g_peers[i].interactions > 0) {
            agg_health = get_aggregate_health(&g_peers[i]);
            utlp_hal_log_info(TAG, "[%02X:%02X] Health:[W%3d/P%3d/B%3d] Agg:%3d | Strat:%2d | Int:%d",
                              g_peers[i].mac[4], g_peers[i].mac[5],
                              g_peers[i].health_score[0],  /* WiFi */
                              g_peers[i].health_score[1],  /* 802.15.4 */
                              g_peers[i].health_score[2],  /* BLE */
                              agg_health,
                              g_peers[i].stratum_claim,
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
 * @par v3.5 FIX: int64_t my_offset parameter
 * Changed from int32_t to prevent truncation when g_aatr.time_offset
 * exceeds int32_t range (±35 minutes = ±2.1B µs). Deviation calculation
 * uses int64_t but threshold comparison remains int32_t (always small).
 *
 * @note Phase 9 (Blood-Brain Barrier): Uses aggregate health and most recent
 *       offset across all arbors. Quorum is transport-agnostic.
 *
 * @param my_offset    My current time offset in microseconds (64-bit)
 * @param threshold_us Maximum deviation to count as "agreement"
 * @return true if >= 2 healthy peers agree with me within threshold
 */
bool utlp_trust_has_quorum(int64_t my_offset, int32_t threshold_us) {
    int i, j;
    int agreeing_peers = 0;
    uint8_t agg_health;
    uint32_t best_seen;
    int best_arbor;
    int64_t peer_offset;
    int64_t deviation;

    for (i = 0; i < UTLP_TRUST_MAX_PEERS; i++) {
        /* Skip empty slots */
        if (g_peers[i].interactions == 0) continue;

        /* Skip unhealthy peers (aggregate health) - they don't count for quorum */
        agg_health = get_aggregate_health(&g_peers[i]);
        if (agg_health < UTLP_TRUST_MIN_VOTE) continue;

        /* Use most recent offset across all arbors */
        best_seen = 0;
        best_arbor = 0;
        for (j = 0; j < UTLP_MAX_ARBORS; j++) {
            if (g_peers[i].last_seen_ms[j] > best_seen) {
                best_seen = g_peers[i].last_seen_ms[j];
                best_arbor = j;
            }
        }
        /* Stored as int32_t, promoted to int64_t for comparison */
        peer_offset = (int64_t)g_peers[i].last_offset_us[best_arbor];

        /* Does this healthy peer agree with me? (64-bit abs for full range) */
        deviation = peer_offset - my_offset;
        if (deviation < 0) deviation = -deviation;
        if (deviation < (int64_t)threshold_us) {
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
 * @brief Look up a peer's aggregate health score
 *
 * Searches the Metabolic Ledger for a specific peer by MAC address.
 * Returns their maximum health score across all arbors, or 0 if not tracked.
 *
 * @note Phase 9 (Blood-Brain Barrier): Returns aggregate (max) health.
 *       Use utlp_trust_get_health_arbor() for per-transport health.
 *
 * @param mac Peer's 6-byte MAC address
 * @return Aggregate health score (0-255), or 0 if peer not found
 */
uint8_t utlp_trust_get_peer_health(const uint8_t *mac) {
    int i;

    for (i = 0; i < UTLP_TRUST_MAX_PEERS; i++) {
        if (g_peers[i].interactions == 0) continue;

        if (memcmp(g_peers[i].mac, mac, 6) == 0) {
            return get_aggregate_health(&g_peers[i]);
        }
    }

    /* Peer not in Ledger - treat as unknown (lowest trust) */
    return 0;
}

/**
 * @brief Look up a peer's health score on a specific arbor
 *
 * Phase 9 (Blood-Brain Barrier): Per-arbor health lookup.
 *
 * @param mac       Peer's 6-byte MAC address
 * @param arbor_id  Transport to query (0=WiFi, 1=154, 2=BLE)
 * @return Health score on that arbor (0-255), or 0 if peer not found
 */
uint8_t utlp_trust_get_health_arbor(const uint8_t *mac, uint8_t arbor_id) {
    int i;

    if (arbor_id >= UTLP_MAX_ARBORS) return 0;

    for (i = 0; i < UTLP_TRUST_MAX_PEERS; i++) {
        if (g_peers[i].interactions == 0) continue;

        if (memcmp(g_peers[i].mac, mac, 6) == 0) {
            return g_peers[i].health_score[arbor_id];
        }
    }

    /* Peer not in Ledger - treat as unknown (lowest trust) */
    return 0;
}

/*============================================================================
 * DORMANCY SUPPORT (Phase 9 - Arbor Yield/Wake)
 *
 * Snapshot per-arbor ledger state before yielding a transport.
 * Enables comparison on wake to detect anomalies.
 *==========================================================================*/

/** @brief Per-arbor snapshot storage for dormancy */
static struct {
    uint8_t snapshot_valid;  /* Bitmask of valid snapshots */
    /* Could expand with more data if needed for wake comparison */
} g_dormancy_state = {0};

/**
 * @brief Snapshot per-arbor ledger state for dormancy
 *
 * Called before arbor yield to preserve reputation snapshot.
 * Currently just marks the arbor as having a valid snapshot.
 * Future: Could save health scores for post-wake comparison.
 *
 * @param arbor_id Transport being yielded (0=WiFi, 1=154, 2=BLE)
 */
void utlp_trust_snapshot_arbor(uint8_t arbor_id) {
    if (arbor_id >= UTLP_MAX_ARBORS) return;

    g_dormancy_state.snapshot_valid |= (1 << arbor_id);

    utlp_hal_log_info(TAG, "Arbor %d ledger snapshot taken (pre-dormancy)", arbor_id);
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
 *
 * @note Phase 9 (Blood-Brain Barrier): Uses aggregate health and most recent
 *       offset across all arbors. Coherence is transport-agnostic.
 */
void utlp_trust_get_coherence(utlp_coherence_t *out) {
    int i, j;
    int32_t consensus = 0;
    int32_t min_offset = INT32_MAX;
    int32_t max_offset = INT32_MIN;
    uint8_t healthy_count = 0;
    uint8_t agreeing_count = 0;
    uint32_t now_ms;
    uint8_t agg_health;
    uint32_t best_seen;
    int best_arbor;
    int32_t peer_offset;

    /* Initialize output */
    memset(out, 0, sizeof(*out));

    /* First, get consensus (need it to measure agreement) */
    if (!utlp_trust_get_consensus(&consensus)) {
        /* No consensus available - no healthy peers */
        out->is_coherent = false;
        return;
    }
    out->consensus_us = consensus;

    /* Count healthy peers and measure spread (using aggregate health) */
    for (i = 0; i < UTLP_TRUST_MAX_PEERS; i++) {
        if (g_peers[i].interactions == 0) continue;

        agg_health = get_aggregate_health(&g_peers[i]);
        if (agg_health < UTLP_TRUST_SYNC_THRESH) continue;

        healthy_count++;

        /* Use most recent offset across all arbors */
        best_seen = 0;
        best_arbor = 0;
        for (j = 0; j < UTLP_MAX_ARBORS; j++) {
            if (g_peers[i].last_seen_ms[j] > best_seen) {
                best_seen = g_peers[i].last_seen_ms[j];
                best_arbor = j;
            }
        }
        peer_offset = g_peers[i].last_offset_us[best_arbor];

        /* Track min/max for spread calculation */
        if (peer_offset < min_offset) {
            min_offset = peer_offset;
        }
        if (peer_offset > max_offset) {
            max_offset = peer_offset;
        }

        /* Check if this peer agrees with consensus */
        int32_t deviation = peer_offset - consensus;
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
 * @par v3.5 FIX: Tenure-based detection (S2 Claim 137)
 * After seniority bankruptcy, interactions=1 and observed_interval_ms=0
 * would cause this function to return false, allowing rebooted peers to
 * bypass genesis pulse protection in INNATE IMMUNITY paths. We now also
 * check peer tenure (time since first_seen_ms). If peer was seen < 5s ago,
 * we treat them as potentially genesis-pulsing regardless of interval data.
 *
 * @param peer Pointer to peer ledger entry
 * @return true if peer appears to be in genesis pulse phase
 */
bool utlp_trust_is_genesis_pulsing(const utlp_peer_ledger_t *peer,
                                    int64_t peer_tx_time) {
    int64_t genesis_threshold_us;

    if (!peer) return false;

    /*
     * v3.6 FIX: Use peer's atomic time (TX timestamp) as age indicator
     *
     * BIOLOGICAL PRINCIPLE: "The nature of the cell is to come together."
     * A newcomer discovering an established peer should coalesce, not fight.
     * The peer's atomic time tells us how long they've been running - this
     * is intrinsic to them, not dependent on when we first noticed them.
     *
     * PREVIOUS BUG (v3.5): The tenure check used first_seen_ms (when WE first
     * saw the peer), which blocked ALL newly-discovered peers for 5 seconds,
     * even established ones that a newcomer just met. This prevented
     * coalescence between devices.
     *
     * FIX: If peer_tx_time >= 5 seconds, they've been running long enough
     * to NOT be genesis-pulsing. This is unforgeable - a newborn can't
     * claim to be old (their atomic time starts at 0).
     */
    genesis_threshold_us = (int64_t)UTLP_GENESIS_TENURE_THRESHOLD_MS * 1000;

    if (peer_tx_time >= genesis_threshold_us) {
        /* Peer has been running >= 5 seconds - clearly established */
        return false;
    }

    /*
     * Peer's atomic time < 5 seconds - they MIGHT be genesis pulsing.
     * Fall back to interval-based detection for additional confidence.
     *
     * Need at least 2 observations to have a valid interval estimate.
     * If we don't have enough observations, we're uncertain.
     */
    if (peer->interactions < UTLP_MIN_INTERVAL_OBSERVATIONS) {
        /*
         * Not enough observations AND atomic time < 5s.
         * This is the ambiguous case: could be a newborn, or could be
         * an established peer we just discovered who happens to have
         * low atomic time (rare - would require reboot within 5s).
         *
         * COALESCENCE BIAS: Return false to allow coalescence.
         * If they ARE genesis-pulsing, we'll catch them on subsequent
         * beacons when we have interval data.
         */
        return false;
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

    /* Calculate expected TX time (last TX + elapsed time)
     * Use aggregate (most recent) last_seen across all arbors */
    elapsed_us = (int64_t)(now_ms - get_aggregate_last_seen(peer)) * 1000;
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

    /* Update interval estimate if we have a previous observation
     * Use aggregate (most recent) last_seen across all arbors */
    uint32_t agg_last_seen = get_aggregate_last_seen(peer);
    if (agg_last_seen > 0) {
        uint32_t observed_interval = now_ms - agg_last_seen;

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

/*============================================================================
 * POLYCHROMATIC STRATUM HELPERS (Claim 253)
 *
 * Per-arbor neighbor queries for polychromatic stratum asymmetry.
 * These functions enable bridge nodes to detect authority presence on
 * each transport independently.
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
    utlp_arbor_id_t arbor_id, uint8_t max_stratum)
{
    uint8_t count = 0;
    int i;

    if (arbor_id >= UTLP_MAX_ARBORS) {
        return 0;
    }

    for (i = 0; i < UTLP_TRUST_MAX_PEERS; i++) {
        /* Skip empty slots */
        if (g_peers[i].interactions == 0) {
            continue;
        }

        /* Check if seen on this arbor recently (non-zero last_seen_ms) */
        if (g_peers[i].last_seen_ms[arbor_id] > 0 &&
            g_peers[i].stratum_claim <= max_stratum) {
            count++;
        }
    }

    return count;
}

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
uint8_t utlp_trust_get_best_stratum_arbor(utlp_arbor_id_t arbor_id)
{
    uint8_t best = 255;
    int i;

    if (arbor_id >= UTLP_MAX_ARBORS) {
        return 255;
    }

    for (i = 0; i < UTLP_TRUST_MAX_PEERS; i++) {
        /* Skip empty slots */
        if (g_peers[i].interactions == 0) {
            continue;
        }

        /* Check if seen on this arbor recently */
        if (g_peers[i].last_seen_ms[arbor_id] > 0 &&
            g_peers[i].stratum_claim < best) {
            best = g_peers[i].stratum_claim;
        }
    }

    return best;
}

/*============================================================================
 * SPECTRAL RETINA (Phase 11)
 *
 * Multi-transport RSSI comparison reveals environmental "Radio Color" -
 * how differently WiFi and 802.15.4 propagate through the same space.
 *
 * @par Why This Matters:
 * - WiFi (2.4GHz, 20MHz BW) and 802.15.4 (2.4GHz, 2MHz BW) experience
 *   different multipath fading profiles despite sharing the same band
 * - Large RSSI delta (>10dB) indicates cluttered RF environment
 * - Future: Could weight timing confidence by spectral coherence
 *
 * @par Output Classification:
 * - CLEAR: Delta ≤ 10dB - Both transports see similar signal strength
 * - CLUTTERED: Delta > 10dB - Multipath causing divergent propagation
 *
 * @see Claim 253: Polychromatic Architecture Foundation
 *==========================================================================*/

/**
 * @brief Log spectral coherence between WiFi and 802.15.4 transports
 *
 * Called after RSSI update to compare signal strength across transports.
 * Only logs when both WiFi and 802.15.4 have fresh RSSI readings.
 *
 * @par Example Output:
 * @code
 * RETINA: Peer 5c | WiFi:-45 15.4:-52 | Delta: 7 dB | CLEAR
 * RETINA: Peer 5c | WiFi:-45 15.4:-68 | Delta: 23 dB | CLUTTERED
 * @endcode
 *
 * @param peer          Pointer to peer ledger entry
 * @param current_arbor Which transport just received an update
 * @param now_ms        Current time in milliseconds
 */
void utlp_trust_log_spectral_coherence(const utlp_peer_ledger_t *peer,
                                        uint8_t current_arbor, uint32_t now_ms)
{
    uint8_t other_arbor;
    uint32_t other_age_ms;
    int8_t current_rssi;
    int8_t other_rssi;
    int8_t delta;
    const char *status;
    const char *wifi_label;
    const char *other_label;

    if (!peer) return;
    if (current_arbor >= UTLP_MAX_ARBORS) return;

    /*
     * Spectral Retina focuses on WiFi vs 802.15.4 comparison.
     * BLE (arbor 2) is excluded for now since it uses different channels.
     *
     * If current arbor is WiFi (0), compare with 802.15.4 (1).
     * If current arbor is 802.15.4 (1), compare with WiFi (0).
     * If current arbor is BLE (2), skip spectral coherence logging.
     */
    if (current_arbor == UTLP_ARBOR_WIFI) {
        other_arbor = UTLP_ARBOR_154;
    } else if (current_arbor == UTLP_ARBOR_154) {
        other_arbor = UTLP_ARBOR_WIFI;
    } else {
        return;  /* BLE - skip spectral coherence */
    }

    /* Check if other transport has recent RSSI (not stale) */
    if (peer->rssi_timestamp_ms[other_arbor] == 0) {
        return;  /* No reading from other transport yet */
    }

    other_age_ms = now_ms - peer->rssi_timestamp_ms[other_arbor];
    if (other_age_ms > UTLP_RSSI_STALE_MS) {
        return;  /* Other transport's RSSI is stale */
    }

    /* Check both RSSI values are valid */
    current_rssi = peer->last_rssi[current_arbor];
    other_rssi = peer->last_rssi[other_arbor];

    if (current_rssi == UTLP_RSSI_INVALID || other_rssi == UTLP_RSSI_INVALID) {
        return;  /* Invalid RSSI value */
    }

    /* Calculate delta (absolute difference) */
    delta = current_rssi - other_rssi;
    if (delta < 0) delta = -delta;  /* abs() for int8_t */

    /* Classify environment */
    status = (delta > UTLP_RSSI_DELTA_CLEAR) ? "CLUTTERED" : "CLEAR";

    /* Format labels based on current arbor */
    if (current_arbor == UTLP_ARBOR_WIFI) {
        wifi_label = "WiFi";
        other_label = "15.4";
    } else {
        wifi_label = "15.4";
        other_label = "WiFi";
    }

    /* Log the spectral coherence reading */
    utlp_hal_log_info("RETINA", "Peer %02X:%02X | %s:%d %s:%d | Delta: %d dB | %s",
                      peer->mac[4], peer->mac[5],
                      wifi_label, (int)current_rssi,
                      other_label, (int)other_rssi,
                      (int)delta, status);
}
