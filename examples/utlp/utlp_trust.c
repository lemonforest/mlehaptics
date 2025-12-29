/**
 * @file utlp_trust.c
 * @brief The Metabolic Ledger Implementation
 *
 * "Trust is not declared. It is accumulated."
 */

#include "utlp_trust.h"
#include "utlp_hal.h"
#include <string.h>
#include <stdlib.h> /* For abs(), labs() */

static const char *TAG = "TRUST";

/* The Ledger: Static allocation for predictability */
static utlp_peer_ledger_t g_peers[UTLP_TRUST_MAX_PEERS];

/*============================================================================
 * INTERNAL HELPERS
 *==========================================================================*/

static void clear_peer(utlp_peer_ledger_t *p) {
    memset(p, 0, sizeof(utlp_peer_ledger_t));
}

/**
 * @brief Find or create a peer entry (LRU Eviction)
 */
static utlp_peer_ledger_t* get_peer_entry(const uint8_t *mac) {
    int i;
    utlp_peer_ledger_t *oldest = &g_peers[0];
    utlp_peer_ledger_t *empty = NULL;
    uint32_t current_ms;
    utlp_time_t now_full;

    /* Get current time for LRU tracking */
    UTLP_HAL_GET_TIME(&now_full);
    /* C64 compat: assume low 32 bits sufficient for LRU */
#if defined(UTLP_NO_64BIT) || defined(__CC65__)
    current_ms = now_full.dwords.lo / 1000;
#else
    current_ms = (uint32_t)(now_full / 1000);
#endif

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

    /* 3. Eviction: If new peer is unknown, do we replace a known one?
     * Only evict if the oldest slot is "weak" (health < threshold).
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
 * @brief Sort helper for median calculation
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

void utlp_trust_init(void) {
    int i;
    for (i = 0; i < UTLP_TRUST_MAX_PEERS; i++) {
        clear_peer(&g_peers[i]);
    }
    utlp_hal_log_info(TAG, "Metabolic Ledger Init: Capacity %d peers", UTLP_TRUST_MAX_PEERS);
}

bool utlp_trust_get_consensus(int32_t *out_consensus_offset) {
    int32_t votes[UTLP_TRUST_MAX_PEERS];
    int count = 0;
    int i;
    
    /* Collect votes from HEALTHY peers */
    for (i = 0; i < UTLP_TRUST_MAX_PEERS; i++) {
        if (g_peers[i].interactions > 0 && g_peers[i].health_score >= UTLP_TRUST_MIN_VOTE) {
            votes[count++] = g_peers[i].last_offset_us;
        }
    }

    if (count == 0) return false;

    /* Sort to find median */
    qsort(votes, count, sizeof(int32_t), compare_int32);

    /* Pick Median */
    if (count % 2 == 1) {
        *out_consensus_offset = votes[count / 2];
    } else {
        /* Average of two middle elements */
        *out_consensus_offset = (votes[count/2 - 1] + votes[count/2]) / 2;
    }

    return true;
}

void utlp_trust_record_observation(const uint8_t *mac, int32_t offset_us, uint8_t stratum) {
    utlp_peer_ledger_t *p = get_peer_entry(mac);
    int32_t consensus = 0;
    bool has_consensus;
    int32_t deviation;
    utlp_time_t now_full;
    uint32_t current_ms;

    if (!p) return; /* Table full, ignored */

    UTLP_HAL_GET_TIME(&now_full);
#if defined(UTLP_NO_64BIT) || defined(__CC65__)
    current_ms = now_full.dwords.lo / 1000;
#else
    current_ms = (uint32_t)(now_full / 1000);
#endif

    /* New peer initialization */
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
    
    /* * THE JUDGEMENT: Compare against Swarm Consensus
     * If no consensus exists (I am alone), we trust lightly based on self-consistency.
     */
    has_consensus = utlp_trust_get_consensus(&consensus);
    
    if (!has_consensus) {
        /* No consensus yet. Just check self-consistency (Jitter) */
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
            /* Hebbian Reward: Trust grows */
            if (p->health_score <= (UTLP_TRUST_MAX - UTLP_REWARD_TRUTH)) {
                p->health_score += UTLP_REWARD_TRUTH;
            } else {
                p->health_score = UTLP_TRUST_MAX;
            }
            p->consecutive_hits++;
        } else {
            /* Penalty: Entropy eats trust quickly */
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

        /* * FORMULA: Survival of the Fittest
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