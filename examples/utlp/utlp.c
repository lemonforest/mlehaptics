/**
 * @file utlp.c
 * @brief UTLP v2 - Frontier Algorithm (ESP32)
 *
 * "Time cannot wait for pairwise agreement or quorum. A distributed timeline
 * must be born of one — a single genesis node declares the epoch and propagates
 * the reference." — UTLP Specification, Section 7
 *
 * GENESIS LOGIC:
 * 1. Boot → I AM the Atomic Clock (stratum 1)
 * 2. Start blinking immediately (no waiting for peers)
 * 3. If I hear a better stratum → adopt their time
 * 4. Same stratum: HIGHER genesis_score wins (topology-aware)
 * 5. Same score: lower MAC wins (tie-breaker)
 *
 * FRONTIER ALGORITHM (v2.0):
 * - Score-based election: neighbors, RSSI, drift stability → higher score wins
 * - Layered Provider Model: Genesis→Providers→Consumers (not all nodes relay)
 * - Smart Interval: Genesis Pulse / Promotion Pulse / Echo Rule
 *
 * TIME-INDEXED EXECUTION:
 * LED state is calculated from atomic time, not toggled by delays.
 * `(atomic_time % 1_000_000) < 500_000` = LED ON
 * This is drift-proof because we recalculate every tick.
 *
 * @version 3.0.0 - Frontier Algorithm (topology-aware election)
 * @date 2025-12-29
 */

#include "utlp_hal.h"

#include <string.h>
#include <stdio.h>

/* Tag for logging (passed to HAL log functions) */
static const char *TAG = "UTLP";

/*============================================================================
 * CONFIGURATION
 *==========================================================================*/

/**
 * GENESIS PULSE - Dynamic Beacon Interval
 *
 * Like a star beginning fusion, time broadcasts are rapid at genesis
 * then settle to steady-state. This provides:
 *   1. Fast initial sync (new swarm converges quickly)
 *   2. Hospitable environment for late-joining nodes
 *   3. Low steady-state overhead
 *
 * Timeline:
 *   0-1s:    100ms  (genesis burst - 10 beacons/sec)
 *   1-5s:    500ms  (fast convergence)
 *   5-10s:   1000ms (settling)
 *   10-60s:  10s    (stabilizing)
 *   60s+:    60s    (steady state)
 */
#define GENESIS_PHASE_1_END_US      1000000ULL      /*  1 second */
#define GENESIS_PHASE_2_END_US      5000000ULL      /*  5 seconds */
#define GENESIS_PHASE_3_END_US     10000000ULL      /* 10 seconds */
#define GENESIS_PHASE_4_END_US     60000000ULL      /* 60 seconds */

#define BEACON_INTERVAL_PHASE_1_US    100000        /* 100ms */
#define BEACON_INTERVAL_PHASE_2_US    500000        /* 500ms */
#define BEACON_INTERVAL_PHASE_3_US   1000000        /* 1s */
#define BEACON_INTERVAL_PHASE_4_US  10000000        /* 10s */
#define BEACON_INTERVAL_STEADY_US   60000000        /* 60s */

#define BLINK_PERIOD_US         1000000     /* 1Hz blink (1 second cycle) */

/*============================================================================
 * SEISMIC CHIRP - Time-Domain Interferometry
 *
 * Every beacon is a 3-burst "seismic chirp". This enables extraction of:
 *   - Burst 0 (t₀): Offset (position) - 0th derivative
 *   - Burst 1 (t₁): Drift (velocity) - 1st derivative
 *   - Burst 2 (t₂): Stability (acceleration) - 2nd derivative
 *
 * Tight spacing (2ms) keeps the chirp as a single "moment" in time,
 * minimizing drift smearing within the measurement window.
 *==========================================================================*/
#define CHIRP_BURST_COUNT       3
#define CHIRP_BURST_SPACING_US  2000        /* 2ms between bursts = 6ms total */

/** @brief Stratum levels (NTP-style) */
#define STRATUM_GPS             0           /* External GPS/atomic reference */
#define STRATUM_GENESIS         1           /* Self-declared master */
#define STRATUM_FOLLOWER        2           /* Synced to another node */

/*============================================================================
 * STATE
 *==========================================================================*/

typedef struct {
    uint8_t  stratum;           /* My stratum level */
    int32_t  time_offset;       /* Local + offset = atomic time (±35 min range) */
    uint8_t  best_master_mac[6];/* MAC of best time source */
} aatr_state_t;

static aatr_state_t g_aatr = {
    .stratum = STRATUM_GENESIS,  /* DEFAULT: I am the time lord */
    .time_offset = 0,
    .best_master_mac = {0}
};

static uint8_t g_local_mac[UTLP_MAC_SIZE];
static uint64_t g_last_beacon_time = 0;
static bool g_led_state = false;

/*============================================================================
 * SEISMIC CHIRP ANALYSIS - Polynomial Fitting for Drift Extraction
 *
 * Accumulates 3 bursts from a single chirp, then fits a polynomial:
 *   offset(t) = a + b*t + c*t²
 *
 * Where:
 *   a = instantaneous offset (0th derivative - position)
 *   b = drift rate in PPB (1st derivative - velocity)
 *   c = drift acceleration (2nd derivative - thermal instability)
 *
 * The receiver measures RX timestamps for bursts that should arrive
 * exactly 2ms apart. Deviation from 2ms spacing = local clock drift.
 *==========================================================================*/

/** @brief Accumulator for a single chirp's 3 bursts */
typedef struct {
    uint64_t chirp_epoch;                    /* TX timestamp (same in all 3) */
    uint64_t rx_times[CHIRP_BURST_COUNT];    /* Local RX timestamps */
    uint8_t  bursts_received;                /* Count of bursts received */
    bool     valid;                          /* All 3 bursts from same chirp? */
} chirp_accumulator_t;

/** @brief Polynomial fit results from chirp analysis */
typedef struct {
    double offset_us;           /* a: instantaneous offset in microseconds */
    double drift_ppb;           /* b: drift rate in parts-per-billion */
    double accel_ppb_s;         /* c: drift acceleration in ppb/second */
    bool   valid;               /* Fit successful? */
} sync_polynomial_t;

/** @brief Running statistics for drift monitoring */
typedef struct {
    sync_polynomial_t last_poly;    /* Most recent chirp analysis */
    double   avg_offset_us;         /* EMA: offset */
    double   avg_drift_ppb;         /* EMA: drift rate */
    double   avg_accel_ppb_s;       /* EMA: drift acceleration */
    double   max_drift_ppb;         /* Maximum observed drift */
    double   min_drift_ppb;         /* Minimum observed drift */
    uint64_t last_log_us;           /* Timestamp of last stats log */
    uint32_t chirps_analyzed;       /* Count of chirps analyzed */
} drift_stats_t;

static drift_stats_t g_drift_stats = {0};

/* Genesis-pulse logging intervals */
#define STATS_LOG_INTERVAL_FAST_US    1000000ULL   /* 1s for first 10s */
#define STATS_LOG_INTERVAL_SLOW_US   30000000ULL   /* 30s after 10s */
#define STATS_LOG_FAST_END_US        10000000ULL   /* 10s threshold */

/* Exponential moving average alpha (0.1 = 10% new, 90% old) */
#define EMA_ALPHA  0.1

static chirp_accumulator_t g_chirp_acc = {0};

/*============================================================================
 * FRONTIER ALGORITHM - Neighborhood Awareness
 *
 * Track peers to calculate genesis_score for topology-aware election.
 * This enables:
 *   1. Score-based Genesis election (higher score wins, not lower MAC)
 *   2. Frontier relay decision (edge nodes become Providers)
 *   3. Smart interval logic (Providers echo master's 60s interval)
 *==========================================================================*/

/** @brief Maximum neighbors to track */
#define MAX_NEIGHBORS           16

/** @brief Relay threshold - score above this = Provider (relay time to others) */
#define RELAY_THRESHOLD         128

/** @brief RSSI thresholds for frontier detection */
#define RSSI_EXCELLENT          (-50)   /* Strong signal, interior node */
#define RSSI_FRONTIER           (-70)   /* Weak signal, edge node */

/** @brief Neighbor timeout in microseconds (5 seconds) */
#define NEIGHBOR_TIMEOUT_US     5000000ULL

/** @brief Individual neighbor record */
typedef struct {
    uint8_t  mac[UTLP_MAC_SIZE];    /* Neighbor's MAC address */
    uint8_t  stratum;               /* Their stratum level */
    uint8_t  score;                 /* Their genesis score (from beacon) */
    int8_t   rssi;                  /* Signal strength to them */
    uint32_t last_seen_us;          /* Low 32 bits of atomic time when last heard */
    bool     valid;                 /* Slot in use? */
} neighbor_t;

/** @brief Neighborhood state */
typedef struct {
    neighbor_t neighbors[MAX_NEIGHBORS];
    uint8_t    peer_count;          /* Number of valid neighbors */
    int8_t     master_rssi;         /* RSSI to my time source */
    uint8_t    providers_nearby;    /* Count of neighbors with score > RELAY_THRESHOLD */
    uint8_t    my_score;            /* My genesis score (0-255) */
} neighborhood_t;

static neighborhood_t g_hood = {0};

/** @brief Time when my stratum last changed (for Promotion Pulse) */
static uint64_t g_last_stratum_change = 0;

/** @brief Am I currently a Provider (relay)? */
static bool g_is_provider = false;

/*============================================================================
 * HELPERS
 *==========================================================================*/

static uint64_t get_atomic_time(void)
{
    return utlp_hal_get_atomic_time_us();
}

/**
 * @brief Get current beacon interval based on uptime (Genesis Pulse)
 */
static uint32_t get_beacon_interval_us(uint32_t uptime_us)
{
    if (uptime_us < GENESIS_PHASE_1_END_US) {
        return BEACON_INTERVAL_PHASE_1_US;   /* 0-1s: 100ms */
    } else if (uptime_us < GENESIS_PHASE_2_END_US) {
        return BEACON_INTERVAL_PHASE_2_US;   /* 1-5s: 500ms */
    } else if (uptime_us < GENESIS_PHASE_3_END_US) {
        return BEACON_INTERVAL_PHASE_3_US;   /* 5-10s: 1s */
    } else if (uptime_us < GENESIS_PHASE_4_END_US) {
        return BEACON_INTERVAL_PHASE_4_US;   /* 10-60s: 10s */
    } else {
        return BEACON_INTERVAL_STEADY_US;    /* 60s+: 60s */
    }
}

static int compare_mac(const uint8_t *a, const uint8_t *b)
{
    return memcmp(a, b, UTLP_MAC_SIZE);
}

/*============================================================================
 * FRONTIER ALGORITHM - Neighborhood Management
 *==========================================================================*/

/**
 * @brief Update or add a neighbor to the tracking table
 */
static void update_neighbor(const uint8_t *mac, uint8_t stratum, uint8_t score,
                            int8_t rssi, uint32_t now_lo)
{
    int empty_slot = -1;
    int oldest_slot = -1;
    uint32_t oldest_time = 0xFFFFFFFF;

    /* Search for existing entry or find empty/oldest slot */
    for (int i = 0; i < MAX_NEIGHBORS; i++) {
        if (g_hood.neighbors[i].valid) {
            if (compare_mac(g_hood.neighbors[i].mac, mac) == 0) {
                /* Found existing entry - update it */
                g_hood.neighbors[i].stratum = stratum;
                g_hood.neighbors[i].score = score;
                g_hood.neighbors[i].rssi = rssi;
                g_hood.neighbors[i].last_seen_us = now_lo;
                return;
            }
            /* Track oldest for eviction if needed */
            if (g_hood.neighbors[i].last_seen_us < oldest_time) {
                oldest_time = g_hood.neighbors[i].last_seen_us;
                oldest_slot = i;
            }
        } else if (empty_slot < 0) {
            empty_slot = i;
        }
    }

    /* Add new neighbor */
    int slot = (empty_slot >= 0) ? empty_slot : oldest_slot;
    if (slot >= 0) {
        memcpy(g_hood.neighbors[slot].mac, mac, UTLP_MAC_SIZE);
        g_hood.neighbors[slot].stratum = stratum;
        g_hood.neighbors[slot].score = score;
        g_hood.neighbors[slot].rssi = rssi;
        g_hood.neighbors[slot].last_seen_us = now_lo;
        g_hood.neighbors[slot].valid = true;
    }
}

/**
 * @brief Expire stale neighbors and recalculate counts
 */
static void expire_neighbors(uint32_t now_lo)
{
    g_hood.peer_count = 0;
    g_hood.providers_nearby = 0;

    for (int i = 0; i < MAX_NEIGHBORS; i++) {
        if (!g_hood.neighbors[i].valid) {
            continue;
        }

        /* Check timeout (handle wrap-around) */
        uint32_t age = now_lo - g_hood.neighbors[i].last_seen_us;
        if (age > (uint32_t)(NEIGHBOR_TIMEOUT_US & 0xFFFFFFFF)) {
            g_hood.neighbors[i].valid = false;
            continue;
        }

        /* Count valid neighbors */
        g_hood.peer_count++;

        /* Count providers (high-score neighbors) */
        if (g_hood.neighbors[i].score > RELAY_THRESHOLD) {
            g_hood.providers_nearby++;
        }

        /* Track master RSSI */
        if (compare_mac(g_hood.neighbors[i].mac, g_aatr.best_master_mac) == 0) {
            g_hood.master_rssi = g_hood.neighbors[i].rssi;
        }
    }
}

/**
 * @brief Calculate my genesis score based on neighborhood metrics
 *
 * Higher score = better Genesis candidate:
 *   - More neighbors (central position)
 *   - Better RSSI (louder signal)
 *   - Stable time source (drift stability)
 *
 * @return Score 0-255 (255 = best candidate)
 */
static uint8_t calculate_genesis_score(void)
{
    uint16_t score = 0;

    /*
     * Component 1: Neighbor count (0-100 points)
     * More neighbors = more central position = better relay candidate
     */
    if (g_hood.peer_count >= 10) {
        score += 100;
    } else {
        score += g_hood.peer_count * 10;
    }

    /*
     * Component 2: Average RSSI to peers (0-100 points)
     */
    if (g_hood.peer_count > 0) {
        int32_t rssi_sum = 0;
        int count = 0;
        for (int i = 0; i < MAX_NEIGHBORS; i++) {
            if (g_hood.neighbors[i].valid) {
                rssi_sum += g_hood.neighbors[i].rssi;
                count++;
            }
        }
        if (count > 0) {
            int8_t avg_rssi = (int8_t)(rssi_sum / count);
            /* Map -100..-30 dBm to 0..100 points */
            if (avg_rssi > -30) avg_rssi = -30;
            if (avg_rssi < -100) avg_rssi = -100;
            score += (uint16_t)(100 + avg_rssi);  /* -100→0, -30→70 */
        }
    }

    /*
     * Component 3: Time stability (0-55 points)
     * Use drift stats if available
     */
    if (g_drift_stats.chirps_analyzed > 0) {
        double drift_abs = g_drift_stats.avg_drift_ppb;
        if (drift_abs < 0) drift_abs = -drift_abs;

        /* Lower drift = higher score */
        if (drift_abs < 100) {
            score += 55;        /* Excellent: <100 ppb */
        } else if (drift_abs < 1000) {
            score += 40;        /* Good: <1000 ppb */
        } else if (drift_abs < 10000) {
            score += 25;        /* Fair: <10000 ppb */
        } else {
            score += 10;        /* Poor: high drift */
        }
    } else {
        score += 30;  /* No stats yet, assume average */
    }

    /* Clamp to 255 */
    if (score > 255) score = 255;

    g_hood.my_score = (uint8_t)score;
    return (uint8_t)score;
}

/**
 * @brief Determine if I should relay (become a Provider)
 *
 * Frontier Algorithm:
 *   - If I'm Genesis (S1): Always chirp
 *   - If I'm at the edge (weak master signal) AND high score: Relay
 *   - If I'm in interior (strong signal) OR redundant: Stay silent
 *
 * @return true if I should send beacons (Genesis or Provider)
 */
static bool should_relay(void)
{
    /* Genesis always chirps */
    if (g_aatr.stratum == STRATUM_GENESIS) {
        return true;
    }

    /* Frontier Rule: At edge with high score? */
    if (g_hood.master_rssi < RSSI_FRONTIER && g_hood.my_score > RELAY_THRESHOLD) {
        return true;
    }

    /* Interior Rule: Strong signal or already covered? */
    if (g_hood.master_rssi > RSSI_EXCELLENT || g_hood.providers_nearby >= 2) {
        return false;
    }

    /* Default: Use score threshold */
    return (g_hood.my_score > RELAY_THRESHOLD);
}

/*============================================================================
 * SMART INTERVAL - Echo Rule
 *
 * Problem: A relay cannot chirp faster than it gets corrected.
 * If Genesis chirps every 60s, a Provider chirping every 10s amplifies drift.
 *
 * Solution: Providers "echo" the master's 60s interval with MAC-based jitter.
 *
 * PROMOTION PULSE: When I just became a Provider, chirp fast for 10s
 * to announce my presence, then settle to echo interval.
 *
 * JITTER: Offset by MAC to prevent collision between Providers.
 *==========================================================================*/

/** @brief Promotion pulse duration: fast chirps for 10s after becoming Provider */
#define PROMOTION_PULSE_DURATION_US     10000000ULL     /* 10 seconds */

/** @brief Promotion pulse interval: 1s chirps during promotion */
#define PROMOTION_PULSE_INTERVAL_US      1000000ULL     /* 1 second */

/** @brief Echo interval: Providers match Genesis steady-state */
#define ECHO_INTERVAL_BASE_US           60000000ULL     /* 60 seconds */

/** @brief Max jitter: MAC byte 5 * 100ms = 0-25.5 seconds */
#define ECHO_JITTER_SCALE_US              100000ULL     /* 100ms per MAC unit */

/**
 * @brief Get smart beacon interval for Providers (Echo Rule)
 *
 * Genesis uses Genesis Pulse (100ms→60s over time).
 * Providers use this function for Promotion Pulse + Echo Rule.
 */
static uint32_t get_smart_interval(uint32_t uptime_us)
{
    /* Genesis uses standard Genesis Pulse */
    if (g_aatr.stratum == STRATUM_GENESIS) {
        return get_beacon_interval_us(uptime_us);
    }

    /*
     * PROMOTION PULSE: Fast chirps when I just became Provider
     */
    uint32_t time_in_state = (uint32_t)(utlp_hal_get_micros() - g_last_stratum_change);

    if (time_in_state < PROMOTION_PULSE_DURATION_US) {
        return (uint32_t)PROMOTION_PULSE_INTERVAL_US;  /* 1s during promotion */
    }

    /*
     * ECHO RULE: Match Genesis steady-state interval with jitter
     */
    uint32_t jitter = (uint32_t)(g_local_mac[5] * ECHO_JITTER_SCALE_US);

    return (uint32_t)(ECHO_INTERVAL_BASE_US + jitter);
}

/*============================================================================
 * SEISMIC CHIRP POLYNOMIAL FITTING
 *==========================================================================*/

/**
 * @brief Analyze a complete 3-burst chirp and extract drift metrics
 */
static void fit_chirp_polynomial(const chirp_accumulator_t *acc, sync_polynomial_t *poly)
{
    poly->valid = false;

    if (!acc->valid || acc->bursts_received != CHIRP_BURST_COUNT) {
        return;
    }

    /* Calculate offset from burst 0 */
    poly->offset_us = (double)((int64_t)acc->chirp_epoch - (int64_t)acc->rx_times[0]);

    /* Calculate inter-burst deltas */
    double expected_spacing_us = (double)CHIRP_BURST_SPACING_US;  /* 2000 us */
    double expected_spacing_s = expected_spacing_us / 1e6;         /* 0.002 s */

    double actual_01 = (double)(acc->rx_times[1] - acc->rx_times[0]);
    double actual_12 = (double)(acc->rx_times[2] - acc->rx_times[1]);

    double delta_01 = actual_01 - expected_spacing_us;
    double delta_12 = actual_12 - expected_spacing_us;

    /* Drift rate (1st derivative) */
    poly->drift_ppb = (delta_01 / expected_spacing_s) * 1000.0;

    /* Drift acceleration (2nd derivative) */
    poly->accel_ppb_s = ((delta_12 - delta_01) / expected_spacing_s) * 1000.0;

    poly->valid = true;
}

/**
 * @brief Update running statistics with new chirp analysis
 */
static void update_drift_stats(const sync_polynomial_t *poly)
{
    if (!poly->valid) {
        return;
    }

    g_drift_stats.last_poly = *poly;
    g_drift_stats.chirps_analyzed++;

    /* First sample: initialize averages */
    if (g_drift_stats.chirps_analyzed == 1) {
        g_drift_stats.avg_offset_us = poly->offset_us;
        g_drift_stats.avg_drift_ppb = poly->drift_ppb;
        g_drift_stats.avg_accel_ppb_s = poly->accel_ppb_s;
        g_drift_stats.max_drift_ppb = poly->drift_ppb;
        g_drift_stats.min_drift_ppb = poly->drift_ppb;
    } else {
        /* Exponential moving average */
        g_drift_stats.avg_offset_us =
            EMA_ALPHA * poly->offset_us + (1.0 - EMA_ALPHA) * g_drift_stats.avg_offset_us;
        g_drift_stats.avg_drift_ppb =
            EMA_ALPHA * poly->drift_ppb + (1.0 - EMA_ALPHA) * g_drift_stats.avg_drift_ppb;
        g_drift_stats.avg_accel_ppb_s =
            EMA_ALPHA * poly->accel_ppb_s + (1.0 - EMA_ALPHA) * g_drift_stats.avg_accel_ppb_s;

        /* Track extremes */
        if (poly->drift_ppb > g_drift_stats.max_drift_ppb) {
            g_drift_stats.max_drift_ppb = poly->drift_ppb;
        }
        if (poly->drift_ppb < g_drift_stats.min_drift_ppb) {
            g_drift_stats.min_drift_ppb = poly->drift_ppb;
        }
    }
}

/**
 * @brief Log drift statistics (genesis-pulse style: fast initially, then slow)
 */
static void log_drift_stats_if_due(uint64_t uptime_us)
{
    /* Only log if we have data */
    if (g_drift_stats.chirps_analyzed == 0) {
        return;
    }

    /* Determine log interval based on uptime */
    uint64_t log_interval = (uptime_us < STATS_LOG_FAST_END_US)
        ? STATS_LOG_INTERVAL_FAST_US
        : STATS_LOG_INTERVAL_SLOW_US;

    /* Check if it's time to log */
    if ((uptime_us - g_drift_stats.last_log_us) < log_interval) {
        return;
    }

    g_drift_stats.last_log_us = uptime_us;

    utlp_hal_log_info(TAG, "════════════════════════════════════════════════════════");
    utlp_hal_log_info(TAG, "[DRIFT STATS] Chirps analyzed: %lu (uptime: %llus)",
             (unsigned long)g_drift_stats.chirps_analyzed,
             (unsigned long long)(uptime_us / 1000000));
    utlp_hal_log_info(TAG, "  LAST: offset=%+.0fus | drift=%+.0fppb | accel=%+.1fppb/s",
             g_drift_stats.last_poly.offset_us,
             g_drift_stats.last_poly.drift_ppb,
             g_drift_stats.last_poly.accel_ppb_s);
    utlp_hal_log_info(TAG, "  AVG:  offset=%+.0fus | drift=%+.0fppb | accel=%+.1fppb/s",
             g_drift_stats.avg_offset_us,
             g_drift_stats.avg_drift_ppb,
             g_drift_stats.avg_accel_ppb_s);
    utlp_hal_log_info(TAG, "  RANGE: drift=[%+.0f..%+.0f]ppb",
             g_drift_stats.min_drift_ppb,
             g_drift_stats.max_drift_ppb);
    utlp_hal_log_info(TAG, "════════════════════════════════════════════════════════");
}

/*============================================================================
 * BEACON PROTOCOL (Frontier Algorithm v2)
 *
 * 11-byte seismic chirp burst:
 *   [0]:      Stratum (1 byte)
 *   [1]:      Burst index (0, 1, or 2)
 *   [2]:      Genesis score (0-255, higher = better candidate)
 *   [3-10]:   TX timestamp in microseconds (8 bytes, little-endian)
 *
 * FRONTIER ELECTION:
 *   1. Lower stratum always wins
 *   2. Same stratum: higher genesis_score wins
 *   3. Same score: lower MAC wins (tie-breaker preserved)
 *==========================================================================*/

/** @brief Beacon size in bytes */
#define UTLP_BEACON_SIZE        11

/** @brief Byte offsets in beacon payload */
#define BEACON_OFF_STRATUM      0
#define BEACON_OFF_BURST        1
#define BEACON_OFF_SCORE        2
#define BEACON_OFF_TIMESTAMP    3

/** @brief Serialize 64-bit timestamp to bytes (little-endian) */
static void time_to_bytes(uint64_t t, uint8_t *bytes)
{
    bytes[0] = (uint8_t)(t);
    bytes[1] = (uint8_t)(t >> 8);
    bytes[2] = (uint8_t)(t >> 16);
    bytes[3] = (uint8_t)(t >> 24);
    bytes[4] = (uint8_t)(t >> 32);
    bytes[5] = (uint8_t)(t >> 40);
    bytes[6] = (uint8_t)(t >> 48);
    bytes[7] = (uint8_t)(t >> 56);
}

/** @brief Deserialize 64-bit timestamp from bytes (little-endian) */
static uint64_t time_from_bytes(const uint8_t *bytes)
{
    return (uint64_t)bytes[0] |
           ((uint64_t)bytes[1] << 8) |
           ((uint64_t)bytes[2] << 16) |
           ((uint64_t)bytes[3] << 24) |
           ((uint64_t)bytes[4] << 32) |
           ((uint64_t)bytes[5] << 40) |
           ((uint64_t)bytes[6] << 48) |
           ((uint64_t)bytes[7] << 56);
}

/**
 * @brief Send seismic chirp (3-burst beacon pattern)
 */
static void send_chirp(void)
{
    uint8_t payload[UTLP_BEACON_SIZE];
    uint8_t my_score;
    uint64_t wait_until;

    /* Capture timestamp ONCE at chirp start */
    uint64_t chirp_epoch = get_atomic_time();

    /* Calculate my genesis score */
    my_score = calculate_genesis_score();

    for (uint8_t burst = 0; burst < CHIRP_BURST_COUNT; burst++) {
        payload[BEACON_OFF_STRATUM] = g_aatr.stratum;
        payload[BEACON_OFF_BURST] = burst;
        payload[BEACON_OFF_SCORE] = my_score;

        time_to_bytes(chirp_epoch, &payload[BEACON_OFF_TIMESTAMP]);

        utlp_hal_tx_packet(NULL, payload, UTLP_BEACON_SIZE);

        /* Wait between bursts (except after last) */
        if (burst < CHIRP_BURST_COUNT - 1) {
            wait_until = utlp_hal_get_micros() + CHIRP_BURST_SPACING_US;
            while (utlp_hal_get_micros() < wait_until) {
                /* Tight spin for 2ms */
            }
        }
    }
}

static void process_beacon(const utlp_packet_t *pkt)
{
    uint8_t remote_stratum;
    uint8_t burst_index;
    uint8_t remote_score;
    uint64_t remote_tx_time;
    bool is_new_chirp;
    bool should_adopt;
    int32_t new_offset;
    uint32_t now_lo;
    uint8_t old_stratum;
    uint8_t my_score;

    if (pkt->len < UTLP_BEACON_SIZE) {
        return;
    }

    remote_stratum = pkt->payload[BEACON_OFF_STRATUM];
    burst_index = pkt->payload[BEACON_OFF_BURST];
    remote_score = pkt->payload[BEACON_OFF_SCORE];
    remote_tx_time = time_from_bytes(&pkt->payload[BEACON_OFF_TIMESTAMP]);

    /* Neighborhood tracking */
    now_lo = (uint32_t)pkt->rx_timestamp_us;
    update_neighbor(pkt->mac, remote_stratum, remote_score, pkt->rssi, now_lo);
    expire_neighbors(now_lo);

    /* Validate burst index */
    if (burst_index >= CHIRP_BURST_COUNT) {
        return;
    }

    /* Chirp accumulation */
    is_new_chirp = (burst_index == 0) || (g_chirp_acc.chirp_epoch != remote_tx_time);

    if (is_new_chirp) {
        g_chirp_acc.chirp_epoch = remote_tx_time;
        g_chirp_acc.bursts_received = 0;
        g_chirp_acc.valid = true;
    }

    if (g_chirp_acc.valid && burst_index < CHIRP_BURST_COUNT) {
        if (burst_index == g_chirp_acc.bursts_received) {
            g_chirp_acc.rx_times[burst_index] = pkt->rx_timestamp_us;
            g_chirp_acc.bursts_received++;
        } else {
            g_chirp_acc.valid = false;
        }
    }

    /* Chirp complete - run polynomial fitting */
    if (g_chirp_acc.valid && g_chirp_acc.bursts_received == CHIRP_BURST_COUNT) {
        sync_polynomial_t poly;
        fit_chirp_polynomial(&g_chirp_acc, &poly);
        if (poly.valid) {
            update_drift_stats(&poly);
        }
        g_chirp_acc.valid = false;
    }

    /* Sync on burst 0 only */
    if (burst_index != 0) {
        return;
    }

    /* Frontier election logic */
    should_adopt = false;

    if (remote_stratum < g_aatr.stratum) {
        should_adopt = true;
        utlp_hal_log_info(TAG, "Better stratum: %d < %d", remote_stratum, g_aatr.stratum);
    }
    else if (remote_stratum == g_aatr.stratum) {
        my_score = g_hood.my_score;
        if (my_score == 0) {
            my_score = calculate_genesis_score();
        }

        if (remote_score > my_score) {
            should_adopt = true;
            utlp_hal_log_info(TAG, "Same stratum, higher score wins (%d > %d)", remote_score, my_score);
        }
        else if (remote_score == my_score) {
            if (compare_mac(pkt->mac, g_local_mac) < 0) {
                should_adopt = true;
                utlp_hal_log_info(TAG, "Same score, lower MAC wins");
            }
        }
    }

    if (should_adopt) {
        old_stratum = g_aatr.stratum;
        new_offset = (int32_t)((int64_t)remote_tx_time - (int64_t)pkt->rx_timestamp_us);

        g_aatr.stratum = remote_stratum + 1;
        g_aatr.time_offset = new_offset;
        memcpy(g_aatr.best_master_mac, pkt->mac, UTLP_MAC_SIZE);

        /* Track stratum changes for Promotion Pulse */
        if (g_aatr.stratum != old_stratum) {
            g_last_stratum_change = utlp_hal_get_micros();
            g_is_provider = should_relay();
            utlp_hal_log_info(TAG, "Stratum changed: %d -> %d (provider=%s)",
                     old_stratum, g_aatr.stratum, g_is_provider ? "YES" : "NO");
        }

        utlp_hal_set_time_offset(new_offset);
        utlp_hal_log_info(TAG, "SYNCED: stratum=%d, offset=%+ld us",
                 g_aatr.stratum, (long)new_offset);
    }
}

/*============================================================================
 * PHYSICS - TIME-INDEXED LED CONTROL
 *==========================================================================*/

static void run_physics(uint64_t atomic_now)
{
    uint32_t cycle_pos = (uint32_t)(atomic_now % BLINK_PERIOD_US);
    bool should_be_on = (cycle_pos < (BLINK_PERIOD_US / 2));

    if (should_be_on != g_led_state) {
        g_led_state = should_be_on;

        if (g_led_state) {
            utlp_hal_set_actuator_phase(UTLP_ACTUATOR_MAIN, 1000, 0.0f, 100.0f);
        } else {
            utlp_hal_set_actuator_phase(UTLP_ACTUATOR_MAIN, 1000, 0.0f, 0.0f);
        }

        utlp_hal_log_info(TAG, "[LED] %s @ phase=%lu us (stratum %d)",
                 g_led_state ? "ON " : "OFF",
                 (unsigned long)cycle_pos,
                 g_aatr.stratum);
    }
}

/*============================================================================
 * APPLICATION ENTRY POINT
 *==========================================================================*/

void utlp_app_run(void)
{
    utlp_packet_t pkt;
    uint64_t now;
    uint64_t uptime;
    uint32_t uptime_lo;
    uint32_t beacon_interval;
    int32_t time_since_beacon;
    static uint32_t last_logged_interval = 0;

    /* Initialize HAL */
    utlp_hal_init();

    /* Get our MAC */
    utlp_hal_get_mac(g_local_mac);

    /* Startup banner */
    utlp_hal_log_info(TAG, "========================================");
    utlp_hal_log_info(TAG, "UTLP v2 - Frontier Algorithm");
    utlp_hal_log_info(TAG, "\"Time is born of one.\"");
    utlp_hal_log_info(TAG, "========================================");
    utlp_hal_log_info(TAG, "MAC: %02X:%02X:%02X:%02X:%02X:%02X",
             g_local_mac[0], g_local_mac[1], g_local_mac[2],
             g_local_mac[3], g_local_mac[4], g_local_mac[5]);
    utlp_hal_log_info(TAG, "Stratum: %d (GENESIS)", g_aatr.stratum);
    utlp_hal_log_info(TAG, "Beacon: 11-byte Seismic Chirp (3-burst @ 2ms)");
    utlp_hal_log_info(TAG, "Election: Score-based (higher score wins)");
    utlp_hal_log_info(TAG, "Relay: Frontier detection (edge nodes = Providers)");
    utlp_hal_log_info(TAG, "Interval: Genesis Pulse / Promotion Pulse / Echo Rule");
    utlp_hal_log_info(TAG, "Blink period: %d ms", BLINK_PERIOD_US / 1000);
    utlp_hal_log_info(TAG, "Drift Analysis: Enabled (polynomial fit)");
    utlp_hal_log_info(TAG, "========================================");

    /* Main loop */
    while (1) {
        /* 1. RECEIVE */
        if (utlp_hal_rx_wait(&pkt, 10)) {
            process_beacon(&pkt);

            while (utlp_hal_rx_poll(&pkt)) {
                process_beacon(&pkt);
            }
        }

        now = get_atomic_time();
        uptime = utlp_hal_get_micros();
        uptime_lo = (uint32_t)uptime;

        /* 2. TRANSMIT (if Genesis or Provider) */
        if (should_relay()) {
            beacon_interval = get_smart_interval(uptime_lo);
            time_since_beacon = (int32_t)(now - g_last_beacon_time);

            if (time_since_beacon >= (int32_t)beacon_interval) {
                send_chirp();
                g_last_beacon_time = now;

                if (beacon_interval != last_logged_interval) {
                    utlp_hal_log_info(TAG, "Beacon interval: %lu ms (uptime %lus, role=%s)",
                             (unsigned long)(beacon_interval / 1000),
                             (unsigned long)(uptime_lo / 1000000),
                             (g_aatr.stratum == STRATUM_GENESIS) ? "Genesis" : "Provider");
                    last_logged_interval = beacon_interval;
                }
            }
        }

        /* 3. PHYSICS */
        run_physics(now);

        /* 4. DRIFT STATS */
        log_drift_stats_if_due(uptime);
    }
}
