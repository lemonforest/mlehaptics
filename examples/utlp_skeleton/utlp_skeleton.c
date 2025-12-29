/**
 * @file utlp_skeleton.c
 * @brief UTLP Genesis Node - Auto-Master & Time-Indexed Visuals
 *
 * "Time cannot wait for pairwise agreement or quorum. A distributed timeline
 * must be born of one — a single genesis node declares the epoch and propagates
 * the reference." — UTLP Specification, Section 7
 *
 * GENESIS LOGIC:
 * 1. Boot → I AM the Atomic Clock (stratum 1)
 * 2. Start blinking immediately (no waiting for peers)
 * 3. If I hear a better stratum → adopt their time
 * 4. If same stratum, lower MAC wins
 *
 * TIME-INDEXED EXECUTION:
 * LED state is calculated from atomic time, not toggled by delays.
 * `(atomic_time % 1_000_000) < 500_000` = LED ON
 * This is drift-proof because we recalculate every tick.
 *
 * @version 2.0.0 - Simplified Genesis Node
 * @date 2025-12-28
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
 *
 * See: UTLP_Technical_Supplement_S1.md Section 1.4
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
static utlp_time_t g_last_beacon_time = UTLP_TIME_ZERO;
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
    utlp_time_t chirp_epoch;                    /* TX timestamp (same in all 3) */
#if UTLP_NO_64BIT
    utlp_time_t rx_times[CHIRP_BURST_COUNT];    /* Local RX timestamps (C64: union) */
#else
    uint64_t rx_times[CHIRP_BURST_COUNT];       /* Local RX timestamps (ESP32: native) */
#endif
    uint8_t  bursts_received;                   /* Count of bursts received */
    bool     valid;                             /* All 3 bursts from same chirp? */
} chirp_accumulator_t;

/** @brief Polynomial fit results from chirp analysis */
/*============================================================================
 * DRIFT STATISTICS (Requires floating-point - disabled on C64)
 *
 * These structures and functions require double/float for polynomial fitting.
 * On cc65 (C64), drift stats are disabled - sync still works, just no stats.
 *==========================================================================*/

#if !UTLP_NO_FLOAT

typedef struct {
    double offset_us;           /* a: instantaneous offset in microseconds */
    double drift_ppb;           /* b: drift rate in parts-per-billion */
    double accel_ppb_s;         /* c: drift acceleration in ppb/second */
    bool   valid;               /* Fit successful? */
} sync_polynomial_t;

/** @brief Running statistics for drift monitoring (ordered large→small) */
typedef struct {
    /* Largest: compound type */
    sync_polynomial_t last_poly;    /* Most recent chirp analysis */

    /* 8-byte types (double/uint64_t) */
    double   avg_offset_us;         /* EMA: offset */
    double   avg_drift_ppb;         /* EMA: drift rate */
    double   avg_accel_ppb_s;       /* EMA: drift acceleration */
    double   max_drift_ppb;         /* Maximum observed drift */
    double   min_drift_ppb;         /* Minimum observed drift */
    uint64_t last_log_us;           /* Timestamp of last stats log */

    /* 4-byte types */
    uint32_t chirps_analyzed;       /* Count of chirps analyzed */
} drift_stats_t;

static drift_stats_t g_drift_stats = {0};

/* Genesis-pulse logging intervals */
#define STATS_LOG_INTERVAL_FAST_US    1000000ULL   /* 1s for first 10s */
#define STATS_LOG_INTERVAL_SLOW_US   30000000ULL   /* 30s after 10s */
#define STATS_LOG_FAST_END_US        10000000ULL   /* 10s threshold */

/* Exponential moving average alpha (0.1 = 10% new, 90% old) */
#define EMA_ALPHA  0.1

#endif /* !UTLP_NO_FLOAT */

static chirp_accumulator_t g_chirp_acc = {0};

/*============================================================================
 * HELPERS
 *==========================================================================*/

/**
 * @brief Get atomic time as utlp_time_t
 *
 * Adds time offset to local time and returns as platform-appropriate type.
 * On ESP32: Simple uint64_t addition via HAL
 * On C64: HAL returns utlp_time_t directly (offset added internally)
 */
static utlp_time_t get_atomic_time(void)
{
#if UTLP_NO_64BIT
    /* C64: HAL returns utlp_time_t with offset already applied */
    return utlp_hal_get_atomic_time();
#else
    /* ESP32: HAL returns uint64_t, which IS utlp_time_t */
    return utlp_hal_get_atomic_time_us();
#endif
}

/**
 * @brief Get current beacon interval based on uptime (Genesis Pulse)
 *
 * Returns progressively longer intervals as the node ages,
 * creating a hospitable environment for new nodes to join.
 *
 * NOTE: Uses uint32_t because all phase boundaries fit in 32 bits.
 * Max check is 60s = 60,000,000 us (well under 2^32 = 4.2 billion).
 * This makes the function work on both ESP32 and C64 without conditionals.
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
 * SEISMIC CHIRP POLYNOMIAL FITTING (Requires floating-point)
 *
 * Given 3 RX timestamps from a chirp with known 2ms TX spacing:
 *   Expected: rx[0], rx[0]+2000, rx[0]+4000 (microseconds)
 *   Actual:   rx[0], rx[1], rx[2]
 *
 * Deviation from expected spacing reveals local clock drift.
 *
 * Math:
 *   delta_1 = (rx[1] - rx[0]) - 2000  // should be 0 if clocks perfect
 *   delta_2 = (rx[2] - rx[0]) - 4000  // should be 0 if clocks perfect
 *
 *   drift_ppb = delta_1 / 0.002s * 1e9  // deviation per second in ppb
 *   accel = (delta_2 - 2*delta_1) / (0.002s)^2  // 2nd derivative
 *
 * NOTE: Disabled on C64 (cc65) - no floating-point support.
 *       Time sync still works, just without drift statistics.
 *==========================================================================*/

#if !UTLP_NO_FLOAT

/**
 * @brief Analyze a complete 3-burst chirp and extract drift metrics
 *
 * @param acc  Chirp accumulator with all 3 bursts received
 * @param poly Output polynomial fit results
 */
static void fit_chirp_polynomial(const chirp_accumulator_t *acc, sync_polynomial_t *poly)
{
    poly->valid = false;

    if (!acc->valid || acc->bursts_received != CHIRP_BURST_COUNT) {
        return;
    }

    /*
     * Calculate offset from burst 0 (same as before)
     * offset = chirp_epoch - rx_time[0]
     */
    poly->offset_us = (double)((int64_t)acc->chirp_epoch - (int64_t)acc->rx_times[0]);

    /*
     * Calculate inter-burst deltas
     *
     * If local clock is perfect:
     *   rx[1] - rx[0] = 2000 us (expected)
     *   rx[2] - rx[1] = 2000 us (expected)
     *
     * Deviation = actual - expected
     */
    double expected_spacing_us = (double)CHIRP_BURST_SPACING_US;  /* 2000 us */
    double expected_spacing_s = expected_spacing_us / 1e6;         /* 0.002 s */

    double actual_01 = (double)(acc->rx_times[1] - acc->rx_times[0]);
    double actual_12 = (double)(acc->rx_times[2] - acc->rx_times[1]);

    double delta_01 = actual_01 - expected_spacing_us;  /* Deviation in us */
    double delta_12 = actual_12 - expected_spacing_us;

    /*
     * Drift rate (1st derivative):
     *   drift_ppb = (delta_us / interval_s) * 1e3
     *
     * Example: If delta_01 = +2 us over 2ms interval:
     *   drift = 2us / 0.002s = 1000 us/s = 1000 ppm = 1,000,000 ppb
     *
     * Typical crystal: ±20 ppm = ±20,000 ppb
     */
    poly->drift_ppb = (delta_01 / expected_spacing_s) * 1000.0;  /* us/s → ppb */

    /*
     * Drift acceleration (2nd derivative):
     *   accel = (delta_12 - delta_01) / interval_s
     *
     * Measures if drift rate is changing (thermal instability)
     */
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
 *
 * @param uptime_us Current uptime in microseconds
 */
static void log_drift_stats_if_due(uint64_t uptime_us)
{
    /* Only log if we have data */
    if (g_drift_stats.chirps_analyzed == 0) {
        return;
    }

    /* Determine log interval based on uptime (genesis pulse style) */
    uint64_t log_interval = (uptime_us < STATS_LOG_FAST_END_US)
        ? STATS_LOG_INTERVAL_FAST_US    /* 1s for first 10s */
        : STATS_LOG_INTERVAL_SLOW_US;   /* 30s after */

    /* Check if it's time to log */
    if ((uptime_us - g_drift_stats.last_log_us) < log_interval) {
        return;
    }

    g_drift_stats.last_log_us = uptime_us;

    /*
     * Print drift statistics snapshot
     *
     * Format:
     *   [DRIFT] n=5 | offset=+1234us | drift=+500ppb | accel=+10ppb/s
     *           avg: offset=+1200us drift=+480ppb accel=+8ppb/s
     *           range: drift=[+450..+520]ppb
     */
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

#endif /* !UTLP_NO_FLOAT - End of drift statistics section */

/*============================================================================
 * BEACON PROTOCOL
 *
 * Simple 9-byte beacon:
 *   [0]:     Stratum (1 byte)
 *   [1-8]:   TX timestamp in microseconds (8 bytes, little-endian)
 *
 * One-way timing: No reply needed. Receiver calculates offset from
 * the difference between TX timestamp and RX timestamp.
 *==========================================================================*/

/**
 * @brief Send seismic chirp (3-burst beacon pattern)
 *
 * All 3 bursts carry the SAME timestamp (captured once at chirp start).
 * The receiver uses the KNOWN 2ms burst spacing as a reference ruler
 * to measure their own clock drift.
 *
 * Seismic principle: The chirp is a known signal (2ms spacing).
 * Deviation in received spacing = receiver clock drift.
 *
 * Payload format (10 bytes):
 *   [0]:     stratum
 *   [1]:     burst_index (0, 1, or 2)
 *   [2-9]:   tx_timestamp (SAME in all 3 bursts - chirp epoch)
 */
static void send_chirp(void)
{
    uint8_t payload[10];
    uint8_t burst;
#if UTLP_NO_64BIT
    utlp_time_t wait_start;
    uint32_t wait_until_lo;
#else
    uint64_t wait_until;
#endif

    /*
     * CRITICAL: Capture timestamp ONCE at chirp start.
     * All 3 bursts carry this same "chirp epoch" value.
     * The 2ms spacing is the known reference - receiver compares
     * expected spacing vs observed spacing to detect drift.
     */
    utlp_time_t chirp_epoch = get_atomic_time();

    for (burst = 0; burst < CHIRP_BURST_COUNT; burst++) {
        payload[0] = g_aatr.stratum;
        payload[1] = burst;  /* Burst index: 0, 1, 2 */

        /* Serialize timestamp using platform-agnostic byte interface */
        UTLP_TIME_TO_BYTES(chirp_epoch, &payload[2]);

        utlp_hal_tx_packet(NULL, payload, 10);  /* Broadcast */

        /* Wait between bursts (except after last) */
        if (burst < CHIRP_BURST_COUNT - 1) {
            /*
             * Busy-wait for precise 2ms spacing.
             * vTaskDelay(1) = 1ms minimum, too coarse for sub-ms precision.
             * This is acceptable for rare chirps (every 100ms→60s).
             */
#if UTLP_NO_64BIT
            /* C64: Use 32-bit lo dword (71 min range, plenty for 2ms) */
            wait_start = utlp_hal_get_time();
            wait_until_lo = wait_start.dwords.lo + CHIRP_BURST_SPACING_US;
            while (utlp_hal_get_time().dwords.lo < wait_until_lo) {
                /* Tight spin for 2ms */
            }
#else
            /* ESP32: Native 64-bit */
            wait_until = utlp_hal_get_micros() + CHIRP_BURST_SPACING_US;
            while (utlp_hal_get_micros() < wait_until) {
                /* Tight spin for 2ms */
            }
#endif
        }
    }
}

static void process_beacon(const utlp_packet_t *pkt)
{
    uint8_t remote_stratum;
    uint8_t burst_index;
    utlp_time_t remote_tx_time;
    bool is_new_chirp;
    bool should_adopt;
    int64_t new_offset;

    if (pkt->len < 10) {
        return;  /* Invalid chirp burst */
    }

    remote_stratum = pkt->payload[0];
    burst_index = pkt->payload[1];

    /* Deserialize timestamp using platform-agnostic byte interface */
    remote_tx_time = UTLP_TIME_FROM_BYTES(&pkt->payload[2]);

    /* Validate burst index */
    if (burst_index >= CHIRP_BURST_COUNT) {
        return;  /* Invalid burst index */
    }

    /*
     * SEISMIC CHIRP ACCUMULATION
     *
     * Collect all 3 bursts from a single chirp to enable polynomial fitting.
     * Detect new chirp by: different chirp_epoch OR burst_index == 0 after
     * we already have bursts.
     */

    /* Detect new chirp (reset accumulator) */
    /* Use UTLP_TIME_EQ for platform-agnostic comparison */
    is_new_chirp = (burst_index == 0) ||
                   !UTLP_TIME_EQ(g_chirp_acc.chirp_epoch, remote_tx_time);

    if (is_new_chirp) {
        /* Start fresh accumulator */
        g_chirp_acc.chirp_epoch = remote_tx_time;
        g_chirp_acc.bursts_received = 0;
        g_chirp_acc.valid = true;
    }

    /* Store this burst's RX timestamp */
    if (g_chirp_acc.valid && burst_index < CHIRP_BURST_COUNT) {
        /* Verify bursts arrive in order (0, 1, 2) */
        if (burst_index == g_chirp_acc.bursts_received) {
#if UTLP_NO_64BIT
            /* C64: Copy utlp_time_t union */
            g_chirp_acc.rx_times[burst_index] = pkt->rx_timestamp;
#else
            /* ESP32: Copy uint64_t */
            g_chirp_acc.rx_times[burst_index] = pkt->rx_timestamp_us;
#endif
            g_chirp_acc.bursts_received++;
        } else {
            /* Out-of-order or missing burst - invalidate */
            g_chirp_acc.valid = false;
        }
    }

    /*
     * CHIRP COMPLETE: All 3 bursts received
     *
     * Now we can:
     * 1. Sync offset from burst 0 (as before)
     * 2. Extract drift/stability from polynomial fit
     */
    if (g_chirp_acc.valid && g_chirp_acc.bursts_received == CHIRP_BURST_COUNT) {
#if !UTLP_NO_FLOAT
        /* Run polynomial fitting (requires floating-point) */
        sync_polynomial_t poly;
        fit_chirp_polynomial(&g_chirp_acc, &poly);

        if (poly.valid) {
            update_drift_stats(&poly);
        }
#endif

        /* Mark as processed (don't re-process same chirp) */
        g_chirp_acc.valid = false;
    }

    /*
     * SYNC ON BURST 0 ONLY (as before)
     *
     * We still use burst 0 for the actual time sync.
     * Bursts 1 and 2 are only for drift analysis.
     */
    if (burst_index != 0) {
        return;
    }

    /*
     * ELECTION LOGIC:
     *
     * 1. Better stratum (lower number) always wins
     * 2. Same stratum: lower MAC wins (tie-breaker)
     * 3. If I lose, adopt their time and become follower
     */
    should_adopt = false;

    if (remote_stratum < g_aatr.stratum) {
        /* They have better stratum - adopt unconditionally */
        should_adopt = true;
        utlp_hal_log_info(TAG, "Better stratum: %d < %d", remote_stratum, g_aatr.stratum);
    }
    else if (remote_stratum == g_aatr.stratum) {
        /* Same stratum - lower MAC wins */
        if (compare_mac(pkt->mac, g_local_mac) < 0) {
            should_adopt = true;
            utlp_hal_log_info(TAG, "Same stratum, lower MAC wins");
        }
    }

    if (should_adopt) {
        /*
         * SYNC MATH (one-way timing):
         *
         * atomic_time = remote_tx_time + flight_time
         *
         * For short-range ESP-NOW (same room), flight_time ≈ 0.
         * So: atomic_time ≈ remote_tx_time
         *
         * My local clock + offset = atomic_time
         * offset = remote_tx_time - my_local_rx_time
         *
         * C64 NOTE: Offset calculation uses only low 32 bits.
         * This limits sync accuracy to ~71 minute windows, which is
         * sufficient for real-time synchronization (drift re-sync often).
         */
#if UTLP_NO_64BIT
        /* C64: 32-bit offset (±35 minute range) */
        new_offset = (int32_t)(remote_tx_time.dwords.lo - pkt->rx_timestamp.dwords.lo);
#else
        /* ESP32: Full 64-bit offset */
        new_offset = (int64_t)remote_tx_time - (int64_t)pkt->rx_timestamp_us;
#endif

        g_aatr.stratum = remote_stratum + 1;  /* I'm one hop from source */
        g_aatr.time_offset = (int32_t)new_offset;  /* Truncate for storage */
        memcpy(g_aatr.best_master_mac, pkt->mac, UTLP_MAC_SIZE);

        /* Update HAL offset */
        utlp_hal_set_time_offset((int32_t)new_offset);

        utlp_hal_log_info(TAG, "SYNCED: stratum=%d, offset=%+ld us",
                 g_aatr.stratum, (long)new_offset);
    }
}

/*============================================================================
 * PHYSICS - TIME-INDEXED LED CONTROL
 *
 * The LED state is CALCULATED from atomic time, not TOGGLED by delays.
 * This is the key insight for drift-proof synchronization.
 *
 * cycle_position = UTLP_GET_PHASE(atomic_time, BLINK_PERIOD_US)
 * LED ON if cycle_position < (BLINK_PERIOD_US / 2)
 *
 * All nodes with the same atomic time will have their LEDs in sync!
 *
 * C64 OPTIMIZATION:
 *   Uses UTLP_GET_PHASE() which applies the "Magic Remainder" trick
 *   to avoid expensive 64-bit modulo operations.
 *==========================================================================*/

static void run_physics(utlp_time_t atomic_now)
{
    uint32_t cycle_pos;
    bool should_be_on;

    /* Calculate where we are in the 1-second blink cycle */
    /* C64: Uses magic remainder trick for phase calculation */
    cycle_pos = UTLP_GET_PHASE(atomic_now, BLINK_PERIOD_US);

    /* 50% duty: ON for first half, OFF for second half */
    should_be_on = (cycle_pos < (BLINK_PERIOD_US / 2));

    /* Only update if state changed (reduces log spam) */
    if (should_be_on != g_led_state) {
        g_led_state = should_be_on;

        /*
         * Use HAL actuator API.
         * duty=100% means LED ON, duty=0% means LED OFF.
         * The HAL handles GPIO15 active-low polarity.
         */
        if (g_led_state) {
            utlp_hal_set_actuator_phase(UTLP_ACTUATOR_MAIN, 1000, UTLP_PHASE(0), UTLP_DUTY(100));
        } else {
            utlp_hal_set_actuator_phase(UTLP_ACTUATOR_MAIN, 1000, UTLP_PHASE(0), UTLP_DUTY(0));
        }

        /* Log state changes (every 500ms at 1Hz) */
        utlp_hal_log_info(TAG, "[LED] %s @ phase=%lu us (stratum %d)",
                 g_led_state ? "ON " : "OFF",
                 (unsigned long)cycle_pos,
                 g_aatr.stratum);
    }
}

/*============================================================================
 * APPLICATION ENTRY POINT
 *
 * This function is called from the platform-specific entry point.
 * For ESP32: utlp_main_esp32c6.c contains app_main() which calls this.
 * For Arduino: setup() would call this.
 * For Linux: main() would call this.
 *==========================================================================*/

void utlp_app_run(void)
{
    /*
     * C89 COMPATIBILITY: All variables declared at function start.
     * This ensures the code compiles on cc65 (C64) and other C89 compilers.
     *
     * utlp_time_t: Platform-specific time type
     *   - ESP32: uint64_t (native)
     *   - C64: union { bytes[8], words[4], dwords[2] } for fast math
     */
    utlp_packet_t pkt;
    utlp_time_t now;
    utlp_time_t uptime_full;          /* Full time for getting raw uptime */
    uint32_t uptime_lo;               /* Low 32 bits (71 min range - plenty) */
    uint32_t beacon_interval;         /* Interval fits in 32-bit (max 60s) */
    int32_t time_since_beacon;        /* Time diff for beacon check */
    static uint32_t last_logged_interval = 0;

    /* Initialize HAL */
    utlp_hal_init();

    /* Get our MAC */
    utlp_hal_get_mac(g_local_mac);

    utlp_hal_log_info(TAG, "========================================");
    utlp_hal_log_info(TAG, "UTLP GENESIS NODE");
    utlp_hal_log_info(TAG, "\"Time is born of one.\"");
    utlp_hal_log_info(TAG, "========================================");
    utlp_hal_log_info(TAG, "MAC: %02X:%02X:%02X:%02X:%02X:%02X",
             g_local_mac[0], g_local_mac[1], g_local_mac[2],
             g_local_mac[3], g_local_mac[4], g_local_mac[5]);
    utlp_hal_log_info(TAG, "Stratum: %d (GENESIS)", g_aatr.stratum);
    utlp_hal_log_info(TAG, "Beacon: Seismic Chirp (3-burst @ 2ms spacing)");
    utlp_hal_log_info(TAG, "Interval: Genesis Pulse (100ms→500ms→1s→10s→60s)");
    utlp_hal_log_info(TAG, "Blink period: %d ms", BLINK_PERIOD_US / 1000);
    utlp_hal_log_info(TAG, "Drift Analysis: Enabled (polynomial fit)");
    utlp_hal_log_info(TAG, "Stats Log: 1s (first 10s) → 30s (steady state)");
    utlp_hal_log_info(TAG, "========================================");

    /*
     * GENESIS PRINCIPLE: Start immediately.
     * No waiting for peers. I AM the atomic clock until proven otherwise.
     */

    while (1) {
        /*
         * 1. RECEIVE: Wait for packet OR timeout (10ms = physics tick)
         *
         * The semaphore-based rx_wait eliminates polling delay.
         * When a packet arrives, we wake immediately (<100us).
         */
        if (utlp_hal_rx_wait(&pkt, 10)) {
            process_beacon(&pkt);

            /* Drain any additional packets */
            while (utlp_hal_rx_poll(&pkt)) {
                process_beacon(&pkt);
            }
        }

        now = get_atomic_time();

        /* Get raw uptime for genesis pulse intervals */
#if UTLP_NO_64BIT
        uptime_full = utlp_hal_get_time();
        uptime_lo = uptime_full.dwords.lo;
#else
        uptime_full = utlp_hal_get_micros();
        uptime_lo = (uint32_t)uptime_full;
#endif

        /*
         * 2. TRANSMIT: Send seismic chirp at dynamic intervals (Genesis Pulse)
         *
         * Each chirp is 3 bursts spaced 2ms apart (6ms total).
         * Interval decreases as node ages:
         *   Genesis burst → Fast convergence → Settling → Steady state
         *
         * C64 OPTIMIZATION: Use UTLP_TIME_DIFF for time comparison.
         * This uses only the low 32 bits (~71 min range - plenty for beacons).
         */
        beacon_interval = get_beacon_interval_us(uptime_lo);
        time_since_beacon = UTLP_DIFF_US(now, g_last_beacon_time);
        if (time_since_beacon >= (int32_t)beacon_interval) {
            send_chirp();
            g_last_beacon_time = now;

            /* Log phase transitions (helpful for debugging) */
            if (beacon_interval != last_logged_interval) {
                utlp_hal_log_info(TAG, "Beacon interval: %lu ms (uptime %lus)",
                         (unsigned long)(beacon_interval / 1000),
                         (unsigned long)(uptime_lo / 1000000));
                last_logged_interval = beacon_interval;
            }
        }

        /*
         * 3. PHYSICS: Update LED based on atomic time
         *
         * This is TIME-INDEXED: we calculate what state SHOULD be
         * based on current time, not based on elapsed time since last change.
         */
        run_physics(now);

        /*
         * 4. DRIFT STATS: Log seismic chirp analysis (genesis-pulse style)
         *
         * For first 10s: Log every 1s (fast feedback during convergence)
         * After 10s: Log every 30s (steady-state monitoring)
         *
         * Shows offset, drift (ppb), and acceleration from polynomial fit.
         * (Disabled on C64 - no floating-point support)
         */
#if !UTLP_NO_FLOAT
        log_drift_stats_if_due(uptime_full);
#endif

        /*
         * No explicit yield needed - rx_wait handles it.
         * Loop runs at ~100Hz (10ms timeout) for responsive physics.
         */
    }
}
