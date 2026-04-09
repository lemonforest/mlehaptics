/**
 * @file utlp.c
 * @brief UTLP v3 - Biological Governance for Distributed Time
 *
 * @section manifesto Manifesto: Beyond Human Governance Models
 *
 * For decades, distributed systems have borrowed from human politics:
 * - **Elections** (Raft, Paxos) - nodes vote for leaders
 * - **Quorums** (BFT) - majority agreement required for action
 * - **Hierarchies** (NTP) - stratum levels assign authority
 *
 * These work, but they encode human assumptions: that coordination requires
 * conscious agreement, that authority must be explicitly granted, that
 * misbehavior requires deliberate exclusion.
 *
 * This code asks: **what if we governed like cells, not like congresses?**
 *
 * @section biology The Biological Model
 *
 * Your body coordinates 37 trillion cells without elections. It uses:
 * - **Hebbian Learning**: "Neurons that fire together, wire together"
 * - **Immune Checkpoints**: Self-limiting responses prevent autoimmunity
 * - **Quorum Sensing**: Bacteria wait for critical mass before acting
 * - **Dominance Hierarchies**: Static traits resolve ties (no negotiation)
 *
 * This module implements all four. The result is a distributed system that:
 * - Has no leader (any node can be "Genesis")
 * - Holds no votes (trust accumulates through observation)
 * - Requires no coordinator (consensus emerges from local interactions)
 * - Heals without intervention (bad actors lose trust, good actors gain it)
 *
 * @section experiment The Experiment
 *
 * We are testing whether biological governance outperforms political governance
 * for distributed time synchronization. Success metrics:
 *
 * 1. **Convergence**: Does the swarm agree on time within 2ms?
 * 2. **Resilience**: Can a Byzantine node corrupt consensus?
 * 3. **Stability**: Does trust correctly identify reliable peers?
 * 4. **Efficiency**: How many beacons to reach steady state?
 *
 * The statistical logging system (planned) will answer these questions.
 * We will debug by observing distributions, not individual samples.
 *
 * @section refs References
 *
 * - UTLP Specification: docs/UTLP_Specification.md
 * - Technical Supplement S1: docs/UTLP_Technical_Supplement_S1.md (Precision)
 * - Technical Supplement S2: docs/UTLP_Technical_Supplement_S2.md (Governance)
 * - Prior Art: docs/Connectionless_Distributed_Timing_Prior_Art.md
 *
 * @section quote
 * > "Time cannot wait for pairwise agreement or quorum. A distributed timeline
 * > must be born of one — a single genesis node declares the epoch and
 * > propagates the reference."
 * > — UTLP Specification, Section 7
 *
 * @section genesis The Genesis Philosophy: A Swarm is Born of One
 *
 * A UTLP swarm must be able to bootstrap from a single device in an uninhabited
 * zone. The first device doesn't NEED peers - it IS the atomic clock. When a
 * second device arrives, it should recognize "there's an established Genesis
 * here" and defer.
 *
 * This matters because UTLP is NOT the primary job of any device. A new TV gets
 * turned on, used for 3 days until the novelty wears off, then sits idle. NOW
 * UTLP awakens - but it cannot change how the application layer does its work.
 * UTLP is opportunistic background coordination.
 *
 * @section food GPS/NTP as Delicious Food
 *
 * External time sources (GPS, NTP) are NOT requirements - they are resources.
 * Think of them as "delicious food that is rare":
 *
 * - We don't NEED them to operate (a swarm can self-sync without external time)
 * - We don't carry them for ourselves (our local oscillator works fine)
 * - We carry them because they're YUMMY to share
 * - Distributing accurate time costs us almost nothing
 * - But it attracts other devices to participate in our swarm
 *
 * GPS/NTP is honey that draws bees to the hive. A device with an NTP connection
 * becomes a time benefactor - other devices want to sync with it, which grows
 * the swarm. The benefactor gains redundancy and resilience in return.
 *
 * > "It costs us very little but distributing it has a high reward potential"
 *
 * @section impl Implementation Notes
 *
 * **GENESIS LOGIC:**
 * 1. Boot → I AM the Atomic Clock (stratum 1)
 * 2. Start blinking immediately (no waiting for peers)
 * 3. If I hear a better stratum → adopt their time
 * 4. Same stratum: HIGHER genesis_score wins (topology-aware)
 * 5. Same score: lower MAC wins (tie-breaker)
 *
 * **BIOLOGICAL GOVERNANCE (v3.0):**
 * - Metabolic Ledger: Trust accumulated through observation, not declaration
 * - Innate Immunity: Stratum + MAC tie-breaker for instant bootstrap (no waiting)
 * - Adaptive Immunity: Health-based selection after observations accumulate
 * - Active Immunity: Entrainment pulses with dual constraints (budget + quorum)
 * - Dominance Hierarchy: Lower MAC = dominant (prevents "Polite Crash")
 *
 * **THE LOOM: Emergent State Machine (S2.31)**
 *
 * The Loom weaves emergent states from entropy signals across multiple dimensions
 * of entity health. It is not programmed with specific responses—it detects
 * threats and weaves homeostatic responses.
 *
 * | Threat Domain | Entropy Signal        | Loom Response      | Emergent State     |
 * |---------------|-----------------------|--------------------|--------------------|
 * | **Temporal**  | Clock drift/instability| Weave authority   | Time Lord (Anchor) |
 * | **Spectral**  | RF congestion/jamming | Weave chirality   | Channel divergence |
 * | **Spatial**   | Position uncertainty  | Weave triangulation| RFIP coordinates   |
 * | **Thermal**   | Power budget stress   | Weave dormancy    | Sleep states       |
 * | **Social**    | Trust distribution    | Weave clustering  | Affinity groups    |
 *
 * The pattern is general: detect threat → weave response → maintain organism.
 * Clock entropy produces Time Lords. Spectral congestion produces channel
 * chirality. The Loom is the generalized homeostatic mechanism that maintains
 * swarm health across ALL dimensions, not just temporal.
 *
 * > "The Loom weaves authority from entropy. It does not assign roles—
 * >  it observes stability and lets structure emerge." — S2, Section 3.4
 *
 * **VARIABLE GAIN PLL (v3.1, S2 Claim 55):**
 *
 * Standard firefly applies Δφ instantly (phase jump). UTLP v3.1 uses frequency
 * slewing with variable gain based on error magnitude:
 *
 * - **COLD START (<5s):** Hard jumps allowed ("snap to grid")
 * - **LOCKED (<10ms error):** Slow slew at 200 ppm (spectral purity)
 * - **RECOVERY (≥10ms error):** Fast slew at 5000 ppm ("warp drive")
 *
 * This preserves continuous waveform integrity for coherent beamforming.
 * Hard phase jumps create spectral splatter; frequency slewing maintains
 * spectral purity while still correcting.
 *
 * - **Deadband:** Corrections < 100μs ignored (avoids oscillation)
 * - **Genesis Reset Detection:** Forward jumps > 1s blocked as stale epochs
 *
 * **ENGINE TIMER (v3.1):**
 * 10Hz independent timer keeps drift model ticking even when transports
 * are yielded to the application layer. Critical for Arbor architecture.
 *
 * Configuration: See UTLP_SERVO_* constants in utlp_config.h
 *
 * **TIME-INDEXED EXECUTION:**
 * LED state is calculated from atomic time, not toggled by delays.
 * `(atomic_time % 1_000_000) < 500_000` = LED ON
 * This is drift-proof because we recalculate every tick.
 *
 * **SMSP APPLICATION LAYER (v3.0):**
 * LED actuation moved from protocol layer to SMSP task (utlp_smsp.c).
 * Protocol calls smsp_notify_sync_ready() after first beacon adoption.
 * SMSP then takes over actuator control using score-driven patterns.
 *
 * @version 3.2.0 - Variable Gain PLL + Engine Timer (Phase 9 Biological Architecture)
 * @date 2026-01-02
 *
 * @copyright
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#include "utlp_config.h"  /* SSOT for all configuration constants */
#include "utlp_hal.h"
#include "utlp_transport.h"  /* Multi-transport layer (Phase 8) */
#include "utlp_trust.h"
#include "utlp_immune.h"
#include "utlp_smsp.h"
#include "utlp_loom.h"   /* Emergent Time Lord state machine (Phase 9) */
#include "utlp_arbor.h"  /* Per-arbor dormancy API (Phase 9) */
#include "utlp_phase.h"  /* Hardware Phase Locked Atomic Coherency (HPLAC) */
#include "utlp_security.h"  /* 32-byte wire packet + Bio-TOTP encryption */

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_timer.h"  /* Engine Timer for independent 10Hz tick */

#include <string.h>
#include <stdio.h>

/* Tag for logging (passed to HAL log functions) */
static const char *TAG = "UTLP";

/*============================================================================
 * CONFIGURATION - Import from utlp_config.h
 *
 * All tunable parameters are now centralized in utlp_config.h for SSOT.
 * Local aliases for backward compatibility with existing code.
 *==========================================================================*/

/* Genesis Pulse timing (from utlp_config.h) */
#define GENESIS_PHASE_1_END_US      UTLP_GENESIS_PHASE_1_END_US
#define GENESIS_PHASE_2_END_US      UTLP_GENESIS_PHASE_2_END_US
#define GENESIS_PHASE_3_END_US      UTLP_GENESIS_PHASE_3_END_US
#define GENESIS_PHASE_4_END_US      UTLP_GENESIS_PHASE_4_END_US

#define BEACON_INTERVAL_PHASE_1_US  UTLP_BEACON_INTERVAL_PHASE_1_US
#define BEACON_INTERVAL_PHASE_2_US  UTLP_BEACON_INTERVAL_PHASE_2_US
#define BEACON_INTERVAL_PHASE_3_US  UTLP_BEACON_INTERVAL_PHASE_3_US
#define BEACON_INTERVAL_PHASE_4_US  UTLP_BEACON_INTERVAL_PHASE_4_US
#define BEACON_INTERVAL_STEADY_US   UTLP_BEACON_INTERVAL_STEADY_US

#define BLINK_PERIOD_US             UTLP_BLINK_PERIOD_US

/* Seismic Chirp (from utlp_config.h) */
#define CHIRP_BURST_COUNT           UTLP_CHIRP_BURST_COUNT
#define CHIRP_BURST_SPACING_US      UTLP_CHIRP_BURST_SPACING_US

/* Stratum levels (from utlp_config.h) */
#define STRATUM_GPS                 UTLP_STRATUM_GPS
#define STRATUM_ORIGIN              UTLP_STRATUM_ORIGIN
#define STRATUM_SYNCED              UTLP_STRATUM_SYNCED

/*============================================================================
 * STATE
 *==========================================================================*/

/**
 * @brief AATR (Atomic Alignment Time Reference) state
 *
 * Extended for Polychromatic Stratum Asymmetry (Claim 253):
 * - Per-arbor stratum levels allow different authority on different transports
 * - primary_time_source tracks which arbor drives the local clock
 * - Split-horizon protection prevents echo chamber between bridges
 */
typedef struct {
    /* 8-byte fields first */
    int64_t  time_offset;                       /**< Local + offset = atomic time */

    /* 1-byte fields and arrays */
    uint8_t  best_source_mac[6];                /**< MAC of best time source */
    uint8_t  stratum[UTLP_ARBOR_COUNT];         /**< Per-arbor stratum (Claim 253) */
    uint8_t  primary_time_source;               /**< Arbor driving clock (Claim 253) */
} aatr_state_t;

/**
 * @brief Spinlock for per-arbor stratum access (thread safety)
 *
 * Required because stratum is read/written from multiple contexts:
 * - Engine timer callback (Loom polychromatic update)
 * - Beacon processing (stratum adoption)
 * - Beacon generation (per-arbor stratum in payload)
 */
static portMUX_TYPE g_stratum_spinlock = portMUX_INITIALIZER_UNLOCKED;

static aatr_state_t g_aatr = {
    .time_offset = 0,
    .best_source_mac = {0},
    .stratum = {
        [UTLP_ARBOR_WIFI] = STRATUM_ORIGIN,     /* Default: Genesis on WiFi */
        [UTLP_ARBOR_154]  = STRATUM_ORIGIN,     /* Default: Genesis on 15.4 */
        [UTLP_ARBOR_BLE]  = STRATUM_ORIGIN      /* Default: Genesis on BLE */
    },
    .primary_time_source = UTLP_ARBOR_WIFI      /* Default: WiFi primary */
};

static uint8_t g_local_mac[UTLP_MAC_SIZE];
static uint64_t g_last_beacon_time = 0;
static bool g_smsp_notified = false;  /* SMSP sync notification sent */

/**
 * @brief Self-demotion vote counter for Origin nodes (S2 self-awareness)
 *
 * When an Origin node sees a healthier peer with a dominant MAC address,
 * it accumulates votes to voluntarily demote itself. This prevents the
 * "Polite Crash" where two healthy Origin nodes both try to demote.
 *
 * Uses dominance hierarchy tie-breaker: lower MAC = dominant (holds ground)
 */
static uint8_t g_self_demotion_votes = 0;

/*============================================================================
 * POLYCHROMATIC STRATUM ACCESSORS (Claim 253)
 *
 * Thread-safe accessors for per-arbor stratum levels.
 * All accesses protected by spinlock to prevent torn reads on 32-bit MCU.
 *==========================================================================*/

/**
 * @brief Set stratum for a specific arbor (thread-safe)
 *
 * @param arbor  Which transport arbor
 * @param stratum  New stratum value
 */
void utlp_set_stratum_for_arbor(utlp_arbor_id_t arbor, uint8_t stratum)
{
    if (arbor >= UTLP_ARBOR_COUNT) return;

    portENTER_CRITICAL(&g_stratum_spinlock);
    g_aatr.stratum[arbor] = stratum;
    portEXIT_CRITICAL(&g_stratum_spinlock);
}

/**
 * @brief Get stratum for a specific arbor (thread-safe)
 *
 * @param arbor  Which transport arbor
 * @return Stratum level for that arbor, or STRATUM_ORIGIN if invalid
 */
uint8_t utlp_get_stratum_for_arbor(utlp_arbor_id_t arbor)
{
    if (arbor >= UTLP_ARBOR_COUNT) return STRATUM_ORIGIN;

    portENTER_CRITICAL(&g_stratum_spinlock);
    uint8_t s = g_aatr.stratum[arbor];
    portEXIT_CRITICAL(&g_stratum_spinlock);
    return s;
}

/**
 * @brief Set which arbor is the primary time source (thread-safe)
 *
 * The primary time source is the only arbor allowed to update time_offset.
 * Other arbors use split-horizon protection.
 *
 * @param arbor  Which transport arbor becomes primary
 */
void utlp_set_primary_time_source(utlp_arbor_id_t arbor)
{
    if (arbor >= UTLP_ARBOR_COUNT) return;

    portENTER_CRITICAL(&g_stratum_spinlock);
    g_aatr.primary_time_source = arbor;
    portEXIT_CRITICAL(&g_stratum_spinlock);
}

/**
 * @brief Get which arbor is the primary time source (thread-safe)
 *
 * @return The arbor ID driving the local clock
 */
utlp_arbor_id_t utlp_get_primary_time_source(void)
{
    portENTER_CRITICAL(&g_stratum_spinlock);
    utlp_arbor_id_t p = (utlp_arbor_id_t)g_aatr.primary_time_source;
    portEXIT_CRITICAL(&g_stratum_spinlock);
    return p;
}

/**
 * @brief Get stratum of primary time source (backward compatibility)
 *
 * Returns the stratum of whichever arbor is currently the primary time source.
 * This maintains API compatibility with code that used the old single-stratum model.
 *
 * @return Stratum level of the primary time source
 */
uint8_t utlp_get_stratum(void)
{
    portENTER_CRITICAL(&g_stratum_spinlock);
    uint8_t s = g_aatr.stratum[g_aatr.primary_time_source];
    portEXIT_CRITICAL(&g_stratum_spinlock);
    return s;
}

/*============================================================================
 * PROTOCOL STATUS API - Drift and Role for Intron Telemetry
 *
 * These functions provide protocol-level status data embedded in the
 * encrypted Intron payload for peer visibility.
 *==========================================================================*/

/**
 * @brief Get current drift rate in parts-per-million
 *
 * Used in Intron to help peers understand local clock quality.
 *
 * @return Drift rate in PPM (positive = running fast, negative = slow)
 */
int16_t utlp_get_drift_ppm(void)
{
    /* STUB: Return 0 (no drift measured yet) */
    /* TODO: Integrate with seismic chirp polynomial fitting */
    return 0;
}

/**
 * @brief Get current node role
 *
 * @return Role enum (0=GENESIS, 1=SERVER, 2=CLIENT, 3=OBSERVER)
 */
uint8_t utlp_get_role(void)
{
    /* Role is determined by stratum:
     * - Stratum 0 = GPS-synced (not applicable in this implementation)
     * - Stratum 1 = Genesis (Origin)
     * - Stratum 2+ = Synced follower
     */
    uint8_t stratum = utlp_get_stratum();

    if (stratum <= STRATUM_ORIGIN) {
        return 0;  /* GENESIS role */
    } else {
        return 2;  /* CLIENT role (following a time source) */
    }
}

/*============================================================================
 * SEISMIC CHIRP ANALYSIS - Multi-Sample Jitter Filtering
 *
 * Accumulates 3 bursts from a single chirp to filter software/hardware jitter.
 * Over 6ms, crystal drift is ~0.24µs (negligible), but stack jitter is 10-100µs.
 *
 * Fits a polynomial:   offset(t) = a + b*t + c*t²
 *
 * Where:
 *   a = instantaneous offset (0th derivative - position)
 *   b = jitter rate (1st derivative) - NOT crystal drift!
 *   c = [DISABLED] jitter acceleration (2nd derivative - noise-dominated)
 *
 * The receiver measures RX timestamps for bursts that should arrive
 * exactly 2ms apart. Deviation from 2ms spacing = local jitter (not drift!).
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
    uint32_t clamped_count;         /* v3.10: Chirps where drift hit ±500ppm clamp */

    /* v3.10: Beacon-to-beacon drift (long-term, much better measurement window) */
    double   prev_offset_us;        /* Previous beacon's offset for delta calc */
    uint64_t prev_offset_time_us;   /* Timestamp of previous offset measurement */
    double   beacon_drift_ppb;      /* EMA: drift from offset change between beacons */
    bool     has_prev_offset;       /* Have a previous offset to compare against */
} drift_stats_t;

static drift_stats_t g_drift_stats = {0};

/* Stats logging config (from utlp_config.h) */
#define STATS_LOG_INTERVAL_FAST_US    UTLP_STATS_LOG_FAST_US
#define STATS_LOG_INTERVAL_SLOW_US    UTLP_STATS_LOG_SLOW_US
#define STATS_LOG_FAST_END_US         UTLP_STATS_FAST_END_US
#define EMA_ALPHA                     UTLP_EMA_ALPHA

static chirp_accumulator_t g_chirp_acc = {0};

/*============================================================================
 * SERVO-LOCKED PHASE CORRECTION (S2 Claim 55)
 *
 * Implements frequency slewing instead of instant phase jumps.
 *
 * Standard Firefly (Peskin/Kuramoto): Δφ applied instantly at beacon reception
 * UTLP Servo-Lock: Δf = Δφ/T_convergence applied over configurable window
 *
 * This preserves continuous waveform integrity for coherent beamforming:
 * - Phase jumps create spectral splatter (wideband noise burst)
 * - Frequency slewing maintains spectral purity throughout correction
 *
 * EXCEPTION: During genesis phase (first 10s), jumps are allowed for fast sync.
 *==========================================================================*/

/** @brief Servo-lock state for gradual phase correction */
typedef struct {
    /* 8-byte fields first */
    int64_t  target_offset;          /**< Target time offset we're slewing toward */
    int64_t  current_offset;         /**< Current applied time offset */
    uint64_t slew_start_time_us;     /**< When we started slewing */

    /* 4-byte fields */
    int32_t  drift_correction_ppb;   /**< Current frequency adjustment (ppb) */

    /* 1-byte fields */
    bool     slewing_active;         /**< True if currently slewing toward target */
    bool     genesis_jumps_allowed;  /**< True during first 10s (instant jumps OK) */
} servo_lock_state_t;

static servo_lock_state_t g_servo = {
    .target_offset = 0,
    .current_offset = 0,
    .slew_start_time_us = 0,
    .drift_correction_ppb = 0,
    .slewing_active = false,
    .genesis_jumps_allowed = true,   /* Jumps allowed at boot */
};

/**
 * @brief Spinlock for servo state protection
 *
 * RACE CONDITION FIX (January 2026):
 *
 * The servo state is accessed from two contexts:
 *   1. Main task: servo_apply_offset() called from beacon handler
 *   2. Timer callback: servo_tick() called from engine_timer_callback (high priority)
 *
 * Without spinlock protection, torn reads/writes of the 64-bit fields
 * (target_offset, current_offset, slew_start_time_us) could occur on
 * ESP32's 32-bit architecture.
 *
 * This spinlock ensures atomic access to the entire servo state structure.
 */
static portMUX_TYPE g_servo_spinlock = portMUX_INITIALIZER_UNLOCKED;

/*============================================================================
 * FRONTIER ALGORITHM - Neighborhood Awareness
 *
 * Track peers to calculate genesis_score for topology-aware election.
 * This enables:
 *   1. Score-based source selection (higher score wins, not lower MAC)
 *   2. Frontier relay decision (edge nodes become Providers)
 *   3. Smart interval logic (Providers echo source's 60s interval)
 *==========================================================================*/

/* Neighborhood config (from utlp_config.h) */
#define MAX_NEIGHBORS           UTLP_MAX_NEIGHBORS
#define RELAY_THRESHOLD         UTLP_RELAY_THRESHOLD
#define RSSI_EXCELLENT          UTLP_RSSI_EXCELLENT
#define RSSI_FRONTIER           UTLP_RSSI_FRONTIER
#define NEIGHBOR_TIMEOUT_US     UTLP_NEIGHBOR_TIMEOUT_US

/** @brief Individual neighbor record */
typedef struct {
    /* 4-byte fields first */
    uint32_t last_seen_us;          /* Low 32 bits of atomic time when last heard */
    /* 1-byte fields and arrays */
    uint8_t  mac[UTLP_MAC_SIZE];    /* Neighbor's MAC address */
    uint8_t  stratum;               /* Their stratum level */
    uint8_t  score;                 /* Their genesis score (from beacon) */
    int8_t   rssi;                  /* Signal strength to them */
    bool     valid;                 /* Slot in use? */
} neighbor_t;

/** @brief Neighborhood state */
typedef struct {
    neighbor_t neighbors[MAX_NEIGHBORS];
    uint8_t    peer_count;          /* Number of valid neighbors */
    int8_t     source_rssi;         /* RSSI to my time source */
    uint8_t    providers_nearby;    /* Count of neighbors with score > RELAY_THRESHOLD */
    uint8_t    my_score;            /* My genesis score (0-255) */
} neighborhood_t;

static neighborhood_t g_hood = {0};

/** @brief Time when my stratum last changed (for Promotion Pulse) */
static uint64_t g_last_stratum_change = 0;

/** @brief Am I currently a Provider (relay)? */
static bool g_is_provider = false;

/*============================================================================
 * LINEAGE LOYALTY STATE MACHINE (v3.9)
 *
 * Commitment lifecycle for timeline identity defense.
 * Prevents foreign-lineage beacons from corrupting synchronization.
 *
 * Biological analogy: Self/Non-Self discrimination in transplant immunology.
 * Once the body (device) develops tolerance for its own tissue (timeline),
 * it actively rejects foreign tissue (foreign timelines) regardless of
 * the donor's apparent health.
 *
 * States:
 *   NAIVE      - Boot state. No commitment. Accept any timeline.
 *   PROBATION  - Recently adopted an epoch. Servo converging. Gate permissive.
 *   COMMITTED  - Stably entrained. Gate active: reject foreign timelines.
 *   GRIEVING   - Lost best source (seniority bankruptcy or loneliness).
 *                Gate temporarily relaxed to allow re-entrainment.
 *
 * @see utlp_config.h - UTLP_LINEAGE_LOYALTY_THRESHOLD_US
 * @see utlp_config.h - UTLP_LINEAGE_COMMITMENT_MIN_US
 *==========================================================================*/

/** @brief Lineage loyalty commitment state */
typedef enum {
    LINEAGE_NAIVE = 0,      /**< No commitment - accept any timeline */
    LINEAGE_PROBATION,      /**< Recently adopted - servo converging */
    LINEAGE_COMMITTED,      /**< Stable entrainment - reject foreign */
    LINEAGE_GRIEVING,       /**< Lost best peer - temporarily open */
    LINEAGE_STATE_COUNT     /**< Sentinel - must be last */
} lineage_state_t;

static lineage_state_t g_lineage_state = LINEAGE_NAIVE;
static uint64_t g_lineage_committed_since_us = 0;

static const char *lineage_state_name(lineage_state_t state) {
    switch (state) {
        case LINEAGE_NAIVE:     return "NAIVE";
        case LINEAGE_PROBATION: return "PROBATION";
        case LINEAGE_COMMITTED: return "COMMITTED";
        case LINEAGE_GRIEVING:  return "GRIEVING";
        default:                return "UNKNOWN";
    }
}

/**
 * @brief Lineage Loyalty Gate: Is this beacon from a peer on (or near) my timeline?
 *
 * Called before ALL synchronization inputs (phase tracker, adoption, servo).
 * Only blocks beacons when in COMMITTED state — all other states are permissive
 * to allow bootstrap, convergence, and re-entrainment.
 *
 * @param proposed_offset  The offset this beacon implies (remote_tx - rx_ts)
 * @return true if beacon should be processed for synchronization
 *         false if beacon is from a foreign lineage (informational only)
 */
static bool is_near_my_lineage(int64_t proposed_offset) {
    /* NAIVE, PROBATION, GRIEVING: accept everything (bootstrap / recovery) */
    if (g_lineage_state != LINEAGE_COMMITTED) {
        return true;
    }

    /* COMMITTED: check proximity to established timeline */
    int64_t deviation = proposed_offset - g_aatr.time_offset;
    if (deviation < 0) deviation = -deviation;

    return (deviation < (int64_t)UTLP_LINEAGE_LOYALTY_THRESHOLD_US);
}

/**
 * @brief Valid transition table for the lineage state machine.
 *
 * Indexed as [from_state][to_state]. true = legal transition.
 *
 * Legal transitions:
 *   NAIVE      → PROBATION  (first adoption)
 *   PROBATION  → COMMITTED  (stability timer elapsed)
 *   PROBATION  → NAIVE      (loneliness before commitment)
 *   COMMITTED  → GRIEVING   (best source bankruptcy or loneliness)
 *   COMMITTED  → NAIVE      (loneliness - extended silence)
 *   GRIEVING   → PROBATION  (re-adoption after grief)
 *   GRIEVING   → NAIVE      (loneliness during grief)
 */
static const bool s_lineage_valid_transitions[LINEAGE_STATE_COUNT][LINEAGE_STATE_COUNT] = {
    /*                  NAIVE  PROB   COMMIT GRIEV */
    /* NAIVE     */ {  false, true,  false, false },
    /* PROBATION */ {  true,  false, true,  false },
    /* COMMITTED */ {  true,  false, false, true  },
    /* GRIEVING  */ {  true,  true,  false, false },
};

/**
 * @brief Transition the lineage state machine with validation.
 *
 * Validates the transition against the legal transition table,
 * logs all transitions for diagnostics, and tracks commitment duration.
 * Centralized to prevent scattered state changes.
 *
 * @param new_state  Target state
 */
static void lineage_transition(lineage_state_t new_state) {
    if (g_lineage_state == new_state) return;

    /* Bounds check - defensive against memory corruption */
    if ((unsigned)new_state >= LINEAGE_STATE_COUNT ||
        (unsigned)g_lineage_state >= LINEAGE_STATE_COUNT) {
        utlp_hal_log_warn(TAG,
            "LINEAGE: Invalid state value (current=%d, requested=%d) - ignoring",
            (int)g_lineage_state, (int)new_state);
        return;
    }

    /* Validate transition against legal table */
    if (!s_lineage_valid_transitions[g_lineage_state][new_state]) {
        utlp_hal_log_warn(TAG,
            "LINEAGE: Illegal transition %s -> %s - ignoring",
            lineage_state_name(g_lineage_state),
            lineage_state_name(new_state));
        return;
    }

    /* Log commitment duration when leaving COMMITTED state */
    if (g_lineage_state == LINEAGE_COMMITTED && g_lineage_committed_since_us > 0) {
        uint64_t commitment_duration_us = utlp_hal_get_micros() - g_lineage_committed_since_us;
        utlp_hal_log_info(TAG,
            "LINEAGE: %s -> %s after %llu s committed (offset=%+lld, stratum=%d)",
            lineage_state_name(g_lineage_state),
            lineage_state_name(new_state),
            (unsigned long long)(commitment_duration_us / 1000000ULL),
            (long long)g_aatr.time_offset,
            utlp_get_stratum());
    } else {
        utlp_hal_log_info(TAG, "LINEAGE: %s -> %s (offset=%+lld, stratum=%d)",
                          lineage_state_name(g_lineage_state),
                          lineage_state_name(new_state),
                          (long long)g_aatr.time_offset,
                          utlp_get_stratum());
    }

    g_lineage_state = new_state;

    if (new_state == LINEAGE_COMMITTED) {
        g_lineage_committed_since_us = utlp_hal_get_micros();
    }

    /*
     * PRECISION WINDOW gating (v3.10, v3.13: compile-flag guarded)
     *
     * COMMITTED with sufficient anticipatory confidence enables
     * precision mode (timer ON only during beacon windows).
     * Any regression (GRIEVING, NAIVE) falls back to continuous.
     *
     * v3.13: Disabled by default (UTLP_PRECISION_ENABLED=0).
     * Precision mode has three interacting bugs that break N>=3:
     *   A) Stale beacon TX (frozen phase timestamps)
     *   B) Stale beacon RX (garbage phase error)
     *   C) Mutual starvation (2/3 devices sleeping)
     * All infrastructure preserved for future fix.
     */
#if UTLP_PRECISION_ENABLED
    if (new_state == LINEAGE_COMMITTED) {
        utlp_phase_enable_precision_mode();
    } else if (new_state == LINEAGE_GRIEVING || new_state == LINEAGE_NAIVE) {
        utlp_phase_disable_precision_mode();
    }
#endif
}

/**
 * @brief Notify lineage system that our best time source underwent Seniority Bankruptcy.
 *
 * Called from the trust system when a peer matching our best_source_mac
 * changes session_salt (indicating reboot). Triggers COMMITTED→GRIEVING
 * transition so we can re-adopt the rebooted source's new timeline.
 *
 * @param mac  The MAC address of the peer that rebooted
 */
void utlp_lineage_on_source_bankruptcy(const uint8_t *mac) {
    /* Only relevant if we're committed and this is our source */
    if (g_lineage_state != LINEAGE_COMMITTED) return;
    if (memcmp(mac, g_aatr.best_source_mac, UTLP_MAC_SIZE) != 0) return;

    utlp_hal_log_warn(TAG,
        "LINEAGE: Best source " PEER_FMT " underwent Seniority Bankruptcy - entering GRIEVING",
        PEER_ID(mac));
    lineage_transition(LINEAGE_GRIEVING);
}

/**
 * @brief Notify lineage system of extended silence (loneliness).
 *
 * Called from the Loom when entering WEAVING state (no beacons for 120s).
 * Resets lineage commitment so the device can adopt a new timeline when
 * peers reappear. This handles:
 * - Genesis reboot where followers lost all peers
 * - Network partition where this device was isolated
 * - New deployment where device was left running alone
 */
void utlp_lineage_on_loneliness(void) {
    if (g_lineage_state == LINEAGE_NAIVE) return;  /* Already open */

    utlp_hal_log_warn(TAG,
        "LINEAGE: Extended silence (Loom WEAVING) - resetting to NAIVE");
    lineage_transition(LINEAGE_NAIVE);
}

/*============================================================================
 * LUCKY PACKET MINIMUM FILTER (v3.8 PT-15)
 *
 * Network jitter is ASYMMETRIC (Log-Normal distribution):
 *   - Packets can only arrive LATE, never early (physics!)
 *   - Averaging late packets drags clock backward
 *   - The servo "hunts" the noise floor instead of finding truth
 *
 * Solution: Track the FLOOR (minimum offset seen) and only slew when
 * packets arrive near it. The minimum is the "truth" - everything else
 * is jitter.
 *
 * Analogy: Like popcorn kernels falling - the truth is the kernel that
 * hit the floor first, not the average pile height.
 *
 * @see utlp_config.h - UTLP_LUCKY_* constants
 *==========================================================================*/

/**
 * @brief Packet quality classification for Lucky Packet filter
 */
typedef enum {
    PACKET_LUCKY,      /**< New floor - update servo with full authority */
    PACKET_OKAY,       /**< Near floor - update servo normally */
    PACKET_JITTER      /**< Far from floor - ignore for sync, just log stats */
} packet_quality_t;

/**
 * @brief Lucky Packet minimum filter state
 *
 * Implements minimum envelope tracking for network time sync.
 * The "floor" is the best offset seen recently - packets near the
 * floor are "lucky" (low jitter), packets far from floor are noise.
 */
typedef struct {
    /* 8-byte fields first */
    int64_t  floor_offset_us;     /**< Best offset seen recently (the truth) */
    int64_t  jitter_sum_us;       /**< Sum of jitter offsets for averaging */
    int64_t  jitter_max_us;       /**< Worst jitter seen this period */

    /* 4-byte fields */
    uint32_t floor_timestamp_ms;  /**< When we last saw a lucky packet */
    uint32_t jitter_count;        /**< Jitter packets since last log */
    uint32_t jitter_last_log_ms;  /**< Last jitter stats log timestamp */
    uint32_t lucky_count;         /**< Lucky packets since last log */
    uint32_t okay_count;          /**< Okay packets since last log */

    /* 1-byte fields */
    bool     floor_valid;         /**< True after first packet establishes floor */
} lucky_packet_filter_t;

/** @brief Jitter stats log interval (60 seconds) */
#define LUCKY_JITTER_LOG_INTERVAL_MS    60000

static lucky_packet_filter_t g_lucky = {
    .floor_offset_us = 0,
    .jitter_sum_us = 0,
    .jitter_max_us = 0,
    .floor_timestamp_ms = 0,
    .jitter_count = 0,
    .jitter_last_log_ms = 0,
    .lucky_count = 0,
    .okay_count = 0,
    .floor_valid = false
};

/**
 * @brief Decay the floor toward drift (compensate for crystal drift)
 *
 * The floor must decay (rise) slowly to prevent one lucky glitch from
 * trapping it forever. Decay rate matches expected crystal drift.
 *
 * Called before each packet classification.
 */
static void lucky_packet_decay(void)
{
    if (!g_lucky.floor_valid) return;

    uint32_t now_ms = (uint32_t)(utlp_hal_get_micros() / 1000);
    uint32_t elapsed_ms = now_ms - g_lucky.floor_timestamp_ms;

    /* Decay at crystal drift rate (40ppm = 40us per second = 0.04us per ms) */
    /* decay_us = elapsed_ms * 40000 ppb / 1000000 = elapsed_ms * 0.04 */
    int64_t decay_us = ((int64_t)elapsed_ms * UTLP_LUCKY_DECAY_PPB) / 1000000;

    if (decay_us > 0) {
        g_lucky.floor_offset_us += decay_us;
        g_lucky.floor_timestamp_ms = now_ms;
    }
}

/**
 * @brief Classify incoming packet for Lucky Packet filter
 *
 * @param observed_offset  The offset calculated from this packet
 * @return Packet quality classification
 */
static packet_quality_t classify_packet(int64_t observed_offset)
{
    uint32_t now_ms = (uint32_t)(utlp_hal_get_micros() / 1000);

    /* First packet establishes the floor */
    if (!g_lucky.floor_valid) {
        g_lucky.floor_offset_us = observed_offset;
        g_lucky.floor_timestamp_ms = now_ms;
        g_lucky.floor_valid = true;
        return PACKET_LUCKY;
    }

    /* Decay the floor toward average (compensate for drift) */
    lucky_packet_decay();

    /* Case 1: New minimum - this is the truth! */
    if (observed_offset < g_lucky.floor_offset_us) {
        /* Check holdoff to prevent oscillation from burst noise */
        uint32_t elapsed_since_floor = now_ms - g_lucky.floor_timestamp_ms;
        if (elapsed_since_floor >= UTLP_LUCKY_FLOOR_HOLDOFF_MS) {
            g_lucky.floor_offset_us = observed_offset;
            g_lucky.floor_timestamp_ms = now_ms;
            return PACKET_LUCKY;
        }
        /* Within holdoff - treat as OKAY, still a good packet */
        return PACKET_OKAY;
    }

    /* Case 2: Near the floor - probably good data */
    if (observed_offset < (g_lucky.floor_offset_us + UTLP_LUCKY_NOISE_WINDOW_US)) {
        return PACKET_OKAY;
    }

    /* Case 3: Far from floor - this is jitter, ignore for sync */
    return PACKET_JITTER;
}

/**
 * @brief Record jitter packet and log aggregate stats periodically
 *
 * Tracks jitter offset for this packet. Every 60 seconds, logs aggregated
 * stats (count, avg, max) and resets counters.
 *
 * @param offset_us  The jitter packet's offset (far from floor)
 */
static void record_jitter_stats(int64_t offset_us)
{
    uint32_t now_ms = (uint32_t)(utlp_hal_get_micros() / 1000);

    /* Track this jitter packet */
    g_lucky.jitter_count++;
    g_lucky.jitter_sum_us += offset_us;
    if (offset_us > g_lucky.jitter_max_us) {
        g_lucky.jitter_max_us = offset_us;
    }

    /* Check if it's time to log (every 60s) */
    uint32_t elapsed = now_ms - g_lucky.jitter_last_log_ms;
    if (elapsed >= LUCKY_JITTER_LOG_INTERVAL_MS) {
        /* Calculate totals for the period */
        uint32_t total_packets = g_lucky.lucky_count + g_lucky.okay_count + g_lucky.jitter_count;

        if (total_packets > 0) {
            int64_t avg_jitter = (g_lucky.jitter_count > 0) ?
                                 (g_lucky.jitter_sum_us / (int64_t)g_lucky.jitter_count) : 0;

            utlp_hal_log_debug(TAG, "LUCKY-STATS: lucky=%lu okay=%lu jitter=%lu "
                               "(avg=%+lld max=%+lld floor=%+lld)",
                               (unsigned long)g_lucky.lucky_count,
                               (unsigned long)g_lucky.okay_count,
                               (unsigned long)g_lucky.jitter_count,
                               (long long)avg_jitter,
                               (long long)g_lucky.jitter_max_us,
                               (long long)g_lucky.floor_offset_us);
        }

        /* Reset counters for next period */
        g_lucky.jitter_count = 0;
        g_lucky.jitter_sum_us = 0;
        g_lucky.jitter_max_us = 0;
        g_lucky.lucky_count = 0;
        g_lucky.okay_count = 0;
        g_lucky.jitter_last_log_ms = now_ms;
    }
}

/*============================================================================
 * FORWARD DECLARATIONS
 *==========================================================================*/

/* Active Immunity: Entrainment response with dual constraints (defined later) */
static void evaluate_entrainment_response(const uint8_t *peer_mac,
                                          uint8_t peer_health,
                                          int32_t deviation_us,
                                          bool peer_is_genesis);

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
 * SERVO-LOCKED PHASE CORRECTION - Helper Functions (S2 Claim 55)
 *
 * These functions implement firefly-style synchronization with frequency
 * slewing instead of phase jumps. The key difference:
 *
 * Standard Firefly:  local_time += offset;           // Discontinuity
 * UTLP Servo-Lock:   drift_correction_ppb = offset * 1e9 / T_convergence;
 *                    // Clock speeds up/slows down rather than jumping
 *==========================================================================*/

/**
 * @brief Check if we're in Cold Start phase (phase jumps allowed)
 *
 * Variable Gain PLL State 1: COLD START
 *
 * During the first 5 seconds after boot (UTLP_SERVO_COLD_START_US),
 * instant phase jumps are allowed for fast initial synchronization
 * ("snap to grid"). No coherence has been established yet, so
 * teleporting to the correct time is acceptable.
 *
 * After Cold Start ends, the system transitions to LOCKED or RECOVERY
 * states which use frequency slewing instead of hard jumps.
 *
 * @param uptime_us Current uptime in microseconds
 * @return true if in Cold Start (jumps allowed), false if slewing required
 */
static bool servo_jumps_allowed(uint64_t uptime_us)
{
#if UTLP_SERVO_DISABLE_SLEWING
    /* Slewing disabled - always allow instant jumps */
    (void)uptime_us;
    return true;
#else
    return uptime_us < UTLP_SERVO_COLD_START_US;
#endif
}

/**
 * @brief Apply a time offset correction using Variable Gain PLL
 *
 * Implements S2 Claim 55: Servo-locked phase correction.
 *
 * THREE-STATE VARIABLE GAIN PLL:
 *
 *   1. COLD START (uptime < 5s):
 *      - Hard jumps allowed for fast initial sync ("snap to grid")
 *      - No coherence established yet, teleport is acceptable
 *
 *   2. LOCKED (error < 10ms):
 *      - Slow slew at 200 ppm (0.02% speed change)
 *      - Maintains spectral purity for coherent beamforming
 *      - Gentle cruise mode for small corrections
 *
 *   3. RECOVERY (error >= 10ms):
 *      - Fast slew at 5000 ppm (0.5% speed change)
 *      - Aggressive catch-up without hard jumping
 *      - "Warp drive" mode after disturbance or reconnection
 *
 * The key insight is that hard phase jumps create spectral splatter
 * (wideband noise bursts) that corrupt coherent aperture integration.
 * Frequency slewing maintains spectral purity while still correcting.
 *
 * @param new_offset     Target time offset to reach
 * @param uptime_us      Current uptime (for Cold Start check)
 * @return true if jump was applied (Cold Start only), false if slewing
 */
static bool servo_apply_offset(int64_t new_offset, uint64_t uptime_us)
{
    /*
     * EPOCH vs PHASE SEPARATION (Critical Architecture Fix)
     *
     * The total error between new_offset and current_offset may be MASSIVE
     * (e.g., 7 million µs = 7 seconds) if devices booted at different times.
     * We cannot SLEW such large offsets - that's insane.
     *
     * Instead, we split the error into two components:
     *   1. EPOCH ERROR: Whole cycles (multiples of 1,000,000 µs) → HARD JUMP
     *   2. PHASE ERROR: Within-cycle error (0 to ±500,000 µs) → GENTLE SLEW
     *
     * The epoch is the "which second are we in" question - this must be
     * aligned instantly. The phase is the "where in that second" question -
     * this can be slewed to maintain spectral purity.
     *
     * Example:
     *   total_error = 7,267,966 µs (7.27 seconds)
     *   epoch_error = 7,000,000 µs (7 whole cycles) → JUMP immediately
     *   phase_error = +267,966 µs (within cycle) → SLEW gently
     */

    /* SPINLOCK: Read current offset atomically */
    portENTER_CRITICAL(&g_servo_spinlock);
    int64_t current_offset = g_servo.current_offset;
    bool was_slewing = g_servo.slewing_active;
    portEXIT_CRITICAL(&g_servo_spinlock);

    int64_t total_error = new_offset - current_offset;
    const int64_t cycle_us = UTLP_PHASE_CYCLE_US;  /* 1,000,000 µs */

    /* Split into epoch (whole cycles) and phase (within cycle) */
    int64_t epoch_error = (total_error / cycle_us) * cycle_us;
    int64_t phase_error = total_error - epoch_error;

    /* Diagnostic: Log error decomposition (only for significant errors) */
    if (total_error > cycle_us || total_error < -cycle_us) {
        utlp_hal_log_info(TAG, "SERVO: total=%+lld, epoch=%+lld (%+lld cycles), phase=%+lld",
                          (long long)total_error, (long long)epoch_error,
                          (long long)(epoch_error / cycle_us), (long long)phase_error);
    }

    /*
     * Wrap-around correction: Choose shortest path within cycle.
     * If phase_error is > half a cycle, it's faster to go the other way.
     *
     * Example: phase_error = +800,000 µs → better as -200,000 µs
     *          (add one cycle to epoch, subtract from phase)
     */
    if (phase_error > cycle_us / 2) {
        phase_error -= cycle_us;
        epoch_error += cycle_us;
    } else if (phase_error < -cycle_us / 2) {
        phase_error += cycle_us;
        epoch_error -= cycle_us;
    }

    int64_t abs_phase_error = (phase_error < 0) ? -phase_error : phase_error;

    /*
     * EPOCH JUMP: If there's an epoch error, jump it immediately.
     * This is the "which second are we in" alignment - cannot be slewed.
     */
    if (epoch_error != 0) {
        int64_t new_current = current_offset + epoch_error;

        /* SPINLOCK: Update offset atomically */
        portENTER_CRITICAL(&g_servo_spinlock);
        g_servo.current_offset = new_current;
        portEXIT_CRITICAL(&g_servo_spinlock);

        /* Update HAL and phase engine outside spinlock (they have own locks) */
        utlp_hal_set_time_offset(new_current);
        utlp_phase_set_epoch_offset(new_current);
        utlp_hal_log_info(TAG, "SERVO: Epoch jump %+lld cycles (%+lld us), remaining phase=%+lld us",
                          (long long)(epoch_error / cycle_us), (long long)epoch_error,
                          (long long)phase_error);

        current_offset = new_current;  /* Update local for subsequent logic */
    }

    /* Check if remaining phase error is within deadband (noise floor) */
    if (abs_phase_error < UTLP_SERVO_DEADBAND_US) {
        /* Already at target - no correction needed */
        portENTER_CRITICAL(&g_servo_spinlock);
        g_servo.slewing_active = false;
        portEXIT_CRITICAL(&g_servo_spinlock);
        return (epoch_error != 0);  /* Return true if we jumped */
    }

    /* Genesis phase: instant jumps allowed for fast initial sync */
    if (servo_jumps_allowed(uptime_us)) {
        /* SPINLOCK: Update all servo state atomically */
        portENTER_CRITICAL(&g_servo_spinlock);
        g_servo.current_offset = new_offset;
        g_servo.target_offset = new_offset;
        g_servo.slewing_active = false;
        g_servo.drift_correction_ppb = 0;
        portEXIT_CRITICAL(&g_servo_spinlock);

        /* Apply to HAL immediately + sync HPLAC phase engine */
        utlp_hal_set_time_offset(new_offset);
        utlp_phase_set_epoch_offset(new_offset);

        utlp_hal_log_info(TAG, "SERVO: Genesis jump applied, offset=%+lld us",
                          (long long)new_offset);
        return true;
    }

    /*
     * VARIABLE GAIN PLL (S2 Claim 55: Servo-Locked Phase Correction)
     *
     * Three states based on error magnitude:
     *   1. COLD START (< 5s):  Hard jump allowed (handled above)
     *   2. LOCKED (error < 10ms): Slow slew at 200 ppm (spectral purity)
     *   3. RECOVERY (error >= 10ms): Fast slew at 5000 ppm (catch-up mode)
     *
     * This replaces hard jumps with frequency slewing while maintaining
     * continuous waveform integrity for coherent beamforming applications.
     *
     * BUG FIX (Coherence Oscillation Audit):
     * Only reset slew window if not already slewing. Resetting on every beacon
     * causes infinite convergence - beacons arrive faster than convergence window,
     * so clock never stabilizes. New beacons update target but keep window running.
     */

    /*
     * Select slew rate based on error magnitude (Variable Gain)
     *
     * LOCKED state: Small errors use gentle slew to maintain spectral purity
     * RECOVERY state: Large errors use aggressive slew to catch up without jumping
     */
    int64_t max_slew_ppb;
    const char *state_name;

    if (abs_phase_error < UTLP_SERVO_LOCKED_THRESHOLD_US) {
        /* LOCKED: Small error - gentle cruise */
        max_slew_ppb = UTLP_SERVO_MAX_SLEW_PPB_LOCKED;
        state_name = "LOCKED";
    } else {
        /* RECOVERY: Large error - engage "warp drive" */
        max_slew_ppb = UTLP_SERVO_MAX_SLEW_PPB_RECOVERY;
        state_name = "RECOVERY";
    }

    /*
     * Calculate drift correction rate: Δf = Δφ / T_convergence
     *
     * Example: 10ms phase error, 500ms convergence window
     *   drift_correction = 10,000us / 500,000us * 1e9 = 20,000 ppb
     *
     * ppb = parts per billion = microseconds per second adjustment
     */
    int64_t drift_ppb = (phase_error * 1000000LL) / UTLP_SERVO_CONVERGENCE_US;

    /* Clamp to state-specific maximum slew rate */
    if (drift_ppb > max_slew_ppb) {
        drift_ppb = max_slew_ppb;
    } else if (drift_ppb < -max_slew_ppb) {
        drift_ppb = -max_slew_ppb;
    }

    /* SPINLOCK: Update slew state atomically */
    portENTER_CRITICAL(&g_servo_spinlock);
    g_servo.target_offset = new_offset;
    /* Only reset slew start time if this is a NEW slew operation */
    if (!was_slewing) {
        g_servo.slew_start_time_us = uptime_us;
    }
    g_servo.slewing_active = true;
    g_servo.drift_correction_ppb = (int32_t)drift_ppb;
    portEXIT_CRITICAL(&g_servo_spinlock);

    utlp_hal_log_info(TAG, "SERVO[%s]: Slewing offset=%+lld us (error=%+lld us, drift=%+ld ppb, max=%lld ppb)",
                      state_name, (long long)new_offset, (long long)phase_error,
                      (long)drift_ppb, (long long)max_slew_ppb);

    /*
     * Return true if we did an epoch jump, even if also starting to slew phase.
     * This ensures SYNCED log correctly says "jumped" when epoch alignment occurred.
     * The phase slew happens in parallel via servo_tick().
     */
    return (epoch_error != 0);
}

/**
 * @brief Tick the servo-lock loop (called periodically from main loop)
 *
 * When slewing is active, this function updates the current offset
 * toward the target using the calculated drift correction rate.
 *
 * NOTE: This function is called from esp_timer callback (high priority).
 * All g_servo accesses are protected by g_servo_spinlock to prevent
 * torn reads/writes when racing with servo_apply_offset() in main task.
 *
 * @param now_us Current time in microseconds
 */
static void servo_tick(uint64_t now_us)
{
    /* SPINLOCK: Read all needed state atomically */
    portENTER_CRITICAL(&g_servo_spinlock);
    bool slewing = g_servo.slewing_active;
    if (!slewing) {
        portEXIT_CRITICAL(&g_servo_spinlock);
        return;
    }
    uint64_t slew_start = g_servo.slew_start_time_us;
    int32_t drift_ppb = g_servo.drift_correction_ppb;
    int64_t current = g_servo.current_offset;
    int64_t target = g_servo.target_offset;
    portEXIT_CRITICAL(&g_servo_spinlock);

    /* Calculate elapsed time since slew started */
    uint64_t elapsed_us = now_us - slew_start;

    /* Calculate how much offset we should have accumulated */
    int64_t expected_correction = (drift_ppb * (int64_t)elapsed_us) / 1000000LL;

    /* Calculate new offset */
    int64_t new_offset = current + expected_correction;

    /* Check if we've reached or passed the target */
    int64_t remaining = target - new_offset;
    int64_t abs_remaining = (remaining < 0) ? -remaining : remaining;

    if (abs_remaining < UTLP_SERVO_DEADBAND_US ||
        elapsed_us >= UTLP_SERVO_CONVERGENCE_US) {
        /* Converged - snap to target and stop slewing */
        portENTER_CRITICAL(&g_servo_spinlock);
        g_servo.current_offset = target;
        g_servo.slewing_active = false;
        g_servo.drift_correction_ppb = 0;
        portEXIT_CRITICAL(&g_servo_spinlock);

        /* Update HAL and phase engine outside spinlock (they have own locks) */
        utlp_hal_set_time_offset(target);
        utlp_phase_set_epoch_offset(target);  /* Sync HPLAC */
        utlp_hal_log_info(TAG, "SERVO: Converged to offset=%+lld us",
                          (long long)target);
    } else {
        /* Still slewing - apply interpolated offset to SOFTWARE only.
         *
         * BUG FIX: Do NOT update phase engine (HPLAC) during slewing!
         * The phase engine should only receive:
         *   1. Epoch jumps (whole-cycle corrections)
         *   2. Genesis jumps (one-time bootstrap)
         *   3. Final converged values (slew complete)
         *
         * Updating phase engine with every 10Hz interpolated value causes
         * offset oscillation chaos. The software offset (g_time_offset_us in HAL)
         * handles smooth interpolation; the hardware phase engine (epoch_offset_us)
         * should remain stable at last-known-good value during slewing.
         */
        portENTER_CRITICAL(&g_servo_spinlock);
        g_servo.current_offset = new_offset;
        portEXIT_CRITICAL(&g_servo_spinlock);

        utlp_hal_set_time_offset(new_offset);
        /* Phase engine NOT updated here - wait for convergence */
    }
}

/*============================================================================
 * ENGINE TIMER - Independent 10Hz Tick for Drift Model Maintenance
 *
 * The Engine Timer runs independently of the packet handler to ensure the
 * drift model keeps ticking even when transports are yielded. This is
 * critical for the Arbor architecture where transports can be independently
 * hibernated by the application layer.
 *
 * PROBLEM SOLVED:
 *   When arbor is yielded → utlp_hal_rx_wait() never returns →
 *   servo_tick() never runs → drift model freezes → time drifts away
 *
 * SOLUTION:
 *   10Hz timer runs independently, calls servo_tick() every 100ms.
 *   Even when all transports are dormant, the internal clock model is
 *   maintained based on last-known drift rate.
 *
 * FUTURE INTEGRATION:
 *   This timer will also call the Loom state machine (utlp_loom_tick)
 *   to detect per-arbor timeline fray and trigger emergent Time Lord
 *   promotion.
 *==========================================================================*/

/** @brief Engine Timer interval (100ms = 10Hz) */
#define ENGINE_TICK_INTERVAL_US      100000

/** @brief Engine Timer handle */
static esp_timer_handle_t s_engine_timer = NULL;

/**
 * @brief Engine Timer callback - called every 100ms
 *
 * This callback runs from esp_timer context (high priority).
 * It must be fast and non-blocking.
 *
 * @param arg Unused
 */
static void engine_timer_callback(void *arg)
{
    (void)arg;

    uint64_t uptime = utlp_hal_get_micros();

    /* 1. Update phase engine (HPLAC - Physics First!)
     *
     * The phase engine now owns timing via MCPWM hardware timer.
     * This tick handles state transitions (COLD→LOCKED→RECOVERY)
     * and quality metric updates.
     *
     * Note: servo_tick() remains for legacy software-based timing
     * until phase engine is fully integrated.
     */
    utlp_phase_tick(uptime);
    servo_tick(uptime);  /* Legacy: will be removed after validation */

    /* 2. Tick Loom state machine for per-arbor Time Lord promotion
     * The Loom detects silence on each arbor and promotes to Time Lord
     * when no beacons are received for 2 minutes.
     */
    utlp_loom_tick();
}

/**
 * @brief Initialize the Engine Timer
 *
 * Creates and starts a periodic timer that ticks at 10Hz to maintain
 * the drift model independently of packet reception.
 *
 * @return ESP_OK on success
 */
static esp_err_t engine_timer_init(void)
{
    esp_timer_create_args_t args = {
        .callback = engine_timer_callback,
        .arg = NULL,
        .dispatch_method = ESP_TIMER_TASK,
        .name = "utlp_engine",
        .skip_unhandled_events = true,
    };

    esp_err_t ret = esp_timer_create(&args, &s_engine_timer);
    if (ret != ESP_OK) {
        utlp_hal_log_error(TAG, "ENGINE: Failed to create timer (err=%d)", ret);
        return ret;
    }

    ret = esp_timer_start_periodic(s_engine_timer, ENGINE_TICK_INTERVAL_US);
    if (ret != ESP_OK) {
        utlp_hal_log_error(TAG, "ENGINE: Failed to start timer (err=%d)", ret);
        esp_timer_delete(s_engine_timer);
        s_engine_timer = NULL;
        return ret;
    }

    utlp_hal_log_info(TAG, "ENGINE: 10Hz timer started (drift model always ticking)");
    return ESP_OK;
}

/**
 * @brief Check if a forward time jump indicates a genesis reset
 *
 * When a peer's atomic time suddenly jumps forward beyond expected drift,
 * it indicates they may have rebooted with a newer epoch. We should NOT
 * adopt their epoch, but can entrain to their phase after verification.
 *
 * @param old_tx_time    Last known TX time from this peer
 * @param new_tx_time    Current TX time from beacon
 * @param elapsed_ms     Milliseconds since last beacon
 * @return true if forward jump exceeds threshold (genesis reset detected)
 */
static bool servo_detect_genesis_reset(int64_t old_tx_time, int64_t new_tx_time,
                                        uint32_t elapsed_ms)
{
    /* Calculate expected time based on elapsed time + reasonable drift */
    int64_t expected_time = old_tx_time + (elapsed_ms * 1000LL);

    /* How much did they jump forward? */
    int64_t forward_jump = new_tx_time - expected_time;

    /* If they jumped forward more than threshold, it's a reset */
    if (forward_jump > (int64_t)UTLP_MAX_FORWARD_JUMP_US) {
        utlp_hal_log_warn(TAG, "GENESIS RESET: Peer jumped forward %lld us (max=%d)",
                          (long long)forward_jump, UTLP_MAX_FORWARD_JUMP_US);
        return true;
    }

    return false;
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
        if (compare_mac(g_hood.neighbors[i].mac, g_aatr.best_source_mac) == 0) {
            g_hood.source_rssi = g_hood.neighbors[i].rssi;
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
    /* Genesis always chirps (check primary arbor stratum) */
    if (utlp_get_stratum() == STRATUM_ORIGIN) {
        return true;
    }

    /*
     * v3.12: Small swarm override.
     *
     * In a 2-3 device swarm, the follower's genesis score is too low to
     * pass RELAY_THRESHOLD (128). Score breakdown: 1 peer (10 pts) +
     * RSSI -66 (34 pts) + 100% clamped drift (10 pts) = 54. Result:
     * the Genesis node never hears from followers — health frozen,
     * consensus impossible, bidirectional communication broken.
     *
     * Fix: if no other providers exist and I have peers, always relay.
     * When more providers appear, normal scoring/suppression takes over.
     */
    if (g_hood.providers_nearby == 0 && g_hood.peer_count > 0) {
        return true;
    }

    /* Frontier Rule: At edge with high score? */
    if (g_hood.source_rssi < RSSI_FRONTIER && g_hood.my_score > RELAY_THRESHOLD) {
        return true;
    }

    /* Interior Rule: Strong signal or already covered? */
    if (g_hood.source_rssi > RSSI_EXCELLENT || g_hood.providers_nearby >= 2) {
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
    /* Genesis uses standard Genesis Pulse (check primary arbor stratum) */
    if (utlp_get_stratum() == STRATUM_ORIGIN) {
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
 * @brief Analyze a complete 3-burst chirp and extract JITTER metrics
 *
 * The "Seismic Chirp" is a 3-burst beacon pattern with known 2ms spacing.
 * By measuring the actual inter-burst timing against the known reference,
 * we filter out SOFTWARE/HARDWARE JITTER to get a cleaner offset estimate.
 *
 * **CRITICAL INSIGHT: This Measures JITTER, Not Crystal Drift**
 *
 * Timescale analysis proves why:
 *   - Crystal drift at 40ppm over 6ms chirp span = 0.24µs (negligible)
 *   - Stack jitter (ISR latency, WiFi arbitration) = 10-100µs (dominates!)
 *   - The crystal IS the stable reference ("D" in control theory)
 *   - Drift characterization requires SECONDS of observation, not milliseconds
 *
 * **Derivative Stack (The Stack is the Message):**
 * - Burst 0 (t₀): Offset (0th derivative) - "where is the clock?"
 * - Burst 1 (t₁): Jitter rate (1st derivative) - used for control
 * - Burst 2 (t₂): Jitter acceleration (2nd derivative) - LOGGED, NOT for control
 *
 * **Observation vs. Control:**
 * The 2nd derivative is noise-dominated ("Derivative Noise Explosion") and
 * produces values like +169M ppb. It is NOT used for servo corrections.
 * However, we CALCULATE and LOG it for statistical analysis:
 *   - Environmental fingerprinting (WiFi congestion, thermal cycles)
 *   - Hardware characterization (jitter profiles differ by device)
 *   - Research data for future algorithm improvements
 *
 * **Why Same Timestamp for All Bursts:**
 * All 3 bursts carry the chirp_epoch from burst 0. This creates a known
 * reference (2ms spacing) that isolates RECEIVER jitter from sender jitter.
 * Fresh timestamps per burst would mix the two, corrupting the measurement.
 *
 * **Where Does Drift Come From?**
 * Crystal drift is measured over SECONDS via inter-exchange analysis:
 *   drift_ppb = (offset_now - offset_10s_ago) / 10s
 * This is done in the servo loop, NOT in this chirp fitting function.
 *
 * @param acc   Accumulated chirp data (3 RX timestamps + chirp_epoch)
 * @param poly  Output: Polynomial fit results (offset, jitter rate, jitter accel)
 *
 * @note drift_ppb is clamped to UTLP_MAX_PHYSICAL_DRIFT_PPB (±500 ppm)
 * @note accel_ppb_s is UNCLAMPED (raw values for statistical analysis)
 * @warning DO NOT use accel_ppb_s for servo control!
 *
 * @see utlp_config.h "SEISMIC CHIRP - Jitter Rejection" section
 * @see README.md "Seismic Chirp" section for protocol overview
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

    /*
     * Drift rate calculation (1st derivative of timing error).
     *
     * delta_01 = actual_spacing - expected_spacing (microseconds)
     * drift = delta / expected_spacing = relative error per sample
     * drift_ppb = drift × 1e9 = parts-per-billion
     *
     * Example: delta_01 = 4µs means 4/2000 = 0.2% = 2000 ppm = 2,000,000 ppb
     *
     * NOTE: This is PROPORTIONAL-ONLY. We removed the derivative term
     * (accel_ppb_s) because it amplified measurement noise into
     * +169,500,000 ppb garbage values ("Derivative Noise Explosion").
     */
    poly->drift_ppb = (delta_01 / expected_spacing_s) * 1000.0;

    /*
     * SANITY CLAMP: Physical crystal drift is <100 ppm.
     * Values exceeding ±500 ppm indicate measurement error
     * (bad timestamps, missed bursts, multipath, etc.)
     */
    if (poly->drift_ppb > (double)UTLP_MAX_PHYSICAL_DRIFT_PPB) {
        poly->drift_ppb = (double)UTLP_MAX_PHYSICAL_DRIFT_PPB;
    } else if (poly->drift_ppb < -(double)UTLP_MAX_PHYSICAL_DRIFT_PPB) {
        poly->drift_ppb = -(double)UTLP_MAX_PHYSICAL_DRIFT_PPB;
    }

    /*
     * Jitter Acceleration (2nd derivative of timing error)
     *
     * **CALCULATED FOR LOGGING, NOT FOR CONTROL**
     *
     * The 2nd derivative amplifies measurement noise ("Derivative Noise Explosion").
     * Values like +169,500,000 ppb are common and physically impossible.
     *
     * However, we still CALCULATE and LOG it because:
     *   1. Statistical analysis over time may reveal patterns
     *   2. Environmental fingerprinting (WiFi congestion, thermal cycles)
     *   3. Hardware characterization (different devices = different profiles)
     *   4. Research data for future algorithm improvements
     *
     * accel = (delta_12 - delta_01) / expected_spacing^2
     *       = change in jitter rate per sample interval
     *
     * @warning DO NOT use accel_ppb_s for servo control!
     */
    double accel_us_per_s2 = (delta_12 - delta_01) / (expected_spacing_s * expected_spacing_s);
    poly->accel_ppb_s = accel_us_per_s2 * 1000.0;  /* Convert to ppb/s */

    /* NOTE: No clamping on accel - we want raw values for statistical analysis.
     * Wild values are expected and informative (they reveal jitter magnitude). */

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

    /* v3.10: Track how many chirps hit the ±500ppm clamp */
    {
        double abs_drift = poly->drift_ppb;
        if (abs_drift < 0) abs_drift = -abs_drift;
        if (abs_drift >= (double)(UTLP_MAX_PHYSICAL_DRIFT_PPB - 1)) {
            g_drift_stats.clamped_count++;
        }
    }

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

    /*
     * v3.10: Beacon-to-beacon drift measurement.
     *
     * The chirp-based drift (2ms window) is too noisy to be useful — any
     * 1µs of ISR jitter saturates the ±500ppm clamp. Instead, measure
     * offset change between consecutive beacons (60s window = 30000×
     * better measurement resolution).
     *
     * drift_ppb = (offset_delta / time_delta) × 1e9
     */
    {
        uint64_t now_us = utlp_hal_get_micros();
        if (g_drift_stats.has_prev_offset) {
            double offset_delta = poly->offset_us - g_drift_stats.prev_offset_us;
            double time_delta_s = (double)(now_us - g_drift_stats.prev_offset_time_us) / 1e6;
            if (time_delta_s > 0.5) {  /* Avoid division by near-zero */
                double beacon_drift = (offset_delta / time_delta_s) * 1000.0;  /* ppb */
                if (g_drift_stats.beacon_drift_ppb == 0.0 &&
                    g_drift_stats.chirps_analyzed <= 2) {
                    g_drift_stats.beacon_drift_ppb = beacon_drift;
                } else {
                    g_drift_stats.beacon_drift_ppb =
                        EMA_ALPHA * beacon_drift +
                        (1.0 - EMA_ALPHA) * g_drift_stats.beacon_drift_ppb;
                }
            }
        }
        g_drift_stats.prev_offset_us = poly->offset_us;
        g_drift_stats.prev_offset_time_us = now_us;
        g_drift_stats.has_prev_offset = true;
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

    {
        uint32_t clamped_pct = (g_drift_stats.chirps_analyzed > 0) ?
            (uint32_t)((100UL * g_drift_stats.clamped_count) / g_drift_stats.chirps_analyzed) : 0;

        utlp_hal_log_info(TAG, "--- DRIFT STATS (uptime: %llus) ---",
                 (unsigned long long)(uptime_us / 1000000));
        utlp_hal_log_info(TAG, "Chirps: %lu (clamped: %lu/%lu = %lu%%) | LAST: off=%+.0fus drift=%+.0fppb",
                 (unsigned long)g_drift_stats.chirps_analyzed,
                 (unsigned long)g_drift_stats.clamped_count,
                 (unsigned long)g_drift_stats.chirps_analyzed,
                 (unsigned long)clamped_pct,
                 g_drift_stats.last_poly.offset_us,
                 g_drift_stats.last_poly.drift_ppb);
        utlp_hal_log_info(TAG, "AVG: off=%+.0fus chirp_drift=%+.0fppb | RANGE: [%+.0f..%+.0f]ppb",
                 g_drift_stats.avg_offset_us,
                 g_drift_stats.avg_drift_ppb,
                 g_drift_stats.min_drift_ppb,
                 g_drift_stats.max_drift_ppb);

        /* v3.10: Beacon-to-beacon drift (much more meaningful than chirp drift) */
        if (g_drift_stats.has_prev_offset) {
            utlp_hal_log_info(TAG, "BEACON DRIFT: %+.0f ppb (EMA, inter-beacon measurement)",
                     g_drift_stats.beacon_drift_ppb);
        }

        if (clamped_pct >= 90) {
            utlp_hal_log_warn(TAG, "DRIFT WARNING: %lu%% of chirps clamped - chirp drift stats unreliable (use BEACON DRIFT)",
                     (unsigned long)clamped_pct);
        }
    }
}

/*============================================================================
 * BEACON PROTOCOL (32-byte Wire Packet)
 *
 * Fixed 32-byte packet structure (utlp_wire_packet_t from utlp_security.h):
 *   Exon [0-23]:  Cleartext timing/versioning (SequenceID, Timestamp, etc.)
 *   Intron [24-31]: AES-128-CTR encrypted (TX_Power, Drift, Opcode, Payload)
 *
 * @see utlp_security.h for complete packet structure documentation
 *
 * FRONTIER ELECTION:
 *   1. Lower stratum always wins
 *   2. Same stratum: higher genesis_score wins
 *   3. Same score: lower MAC wins (tie-breaker preserved)
 *
 * TX MODE SELECTION (HAL Pattern - S2.42):
 *
 * Following Silicon Labs RAIL API precedent (RAIL_StartTx vs RAIL_StartScheduledTx),
 * UTLP provides two chirp transmission modes:
 *
 * | Function             | Behavior | Use Case |
 * |----------------------|----------|----------|
 * | send_chirp()         | Prefers hardware scheduling if available | Default - max precision |
 * | send_chirp_immediate() | Always spin-wait, bypasses scheduling | Emergency, entrainment |
 *
 * Rationale for dual modes:
 * - Scheduled TX achieves ±1µs precision but requires upfront commitment
 * - Immediate TX allows reactive transmission (e.g., entrainment pulses)
 * - Some scenarios need determinism (seismic chirp), others need responsiveness
 *
 * @see Silicon Labs RAIL API: RAIL_StartTx() vs RAIL_StartScheduledTx()
 * @see Zephyr IEEE 802.15.4: IEEE802154_TX_MODE_TXTIME vs immediate
 * @see SAE 2024-01-2989: Time-controlled hardware access patterns
 *==========================================================================*/

/*============================================================================
 * 32-BYTE WIRE PACKET GEOMETRY (utlp_security.h)
 *
 * DEPRECATED LEGACY (13-byte beacon) REMOVED.
 *
 * New fixed structure:
 *   - Exon (24 bytes cleartext): SequenceID, Timestamp, NTP, Salt, Stratum, Version
 *   - Intron (8 bytes AES-CTR): TX_Power, Battery, Drift, Opcode, Payload[3]
 *
 * @see utlp_security.h for utlp_wire_packet_t, utlp_exon_t, utlp_intron_t
 * @see Claim 255: Rolling Splice-Site Security (Bio-TOTP)
 *==========================================================================*/

/**
 * @brief Swarm DNA (16-byte shared secret)
 *
 * Loaded from NVS or set via API. Default is UTLP_ZERO_KEY (public mode).
 *
 * Public Mode: All packets use deterministic key derived from Zero Key.
 * This is "Herd Immunity" - public nodes protect private nodes by making
 * all traffic patterns identical (Purple Team PT-4).
 *
 * @see utlp_security_derive_splice_key() for key derivation
 * @see Claim 255: Rolling Splice-Site Security
 */
static uint8_t g_swarm_dna[UTLP_DNA_SIZE] = {0};  /* Zero = public mode */

/**
 * @brief Set swarm DNA for encrypted communication
 *
 * @param dna 16-byte shared secret (or NULL to use UTLP_ZERO_KEY)
 */
void utlp_set_swarm_dna(const uint8_t dna[UTLP_DNA_SIZE])
{
    if (dna) {
        memcpy(g_swarm_dna, dna, UTLP_DNA_SIZE);
    } else {
        memset(g_swarm_dna, 0, UTLP_DNA_SIZE);  /* Reset to public mode */
    }
}

/**
 * @brief Build 32-byte UTLP wire packet for a single burst
 *
 * Populates both Exon (cleartext) and Intron (encrypted) fields, then calls
 * the security layer to encrypt the Intron before transmission.
 *
 * @param[out] pkt          Pointer to wire packet structure to fill (32 bytes)
 * @param      chirp_epoch  Monotonic timestamp for all bursts in this chirp
 * @param      burst_index  Index of this burst (0, 1, or 2)
 * @param      score        Genesis election score
 * @param      arbor_id     Which arbor this beacon is for (Claim 253)
 *
 * @note Protocol version is enforced as UTLP_PROTOCOL_VERSION (0x01).
 * @note Encryption ALWAYS runs, even for Zero Key (Herd Immunity - PT-4).
 * @note Uses per-arbor stratum for polychromatic support.
 *
 * @see utlp_security_encrypt_intron() for encryption details
 * @see Claim 255: Rolling Splice-Site Security (Bio-TOTP)
 * @see Claim 253: Polychromatic Stratum (per-arbor genesis)
 */
static void build_utlp_packet(utlp_wire_packet_t *pkt, uint64_t chirp_epoch,
                               uint8_t burst_index, uint8_t score,
                               utlp_arbor_id_t arbor_id)
{
    /* Initialize Exon with auto-populated fields (version, salt, sequence) */
    utlp_security_init_exon(&pkt->exon);

    /* Exon: Timing fields */
    pkt->exon.utlp_timestamp_us = chirp_epoch;
    pkt->exon.ntp_timestamp_utc = utlp_hal_get_ntp_time_utc();  /* Or random if stealth */
    pkt->exon.stratum = utlp_get_stratum_for_arbor(arbor_id);

    /* Exon: Protocol version — marks genesis-pulsing beacons explicitly.
     * During first 10s (genesis phases 1-3), use 0xFE so receivers can
     * identify newborn beacons on the FIRST packet without needing
     * behavioral detection (which requires ≥2 observations).
     * Uses raw uptime (not atomic time) since genesis phase is local.
     *
     * v3.13: Reduced from PHASE_4 (60s) to PHASE_3 (10s). The 60s
     * duration blocked ALL adoption for a full minute, creating a race
     * condition in N>=3 swarms where devices adopt in the wrong order:
     *   - C adopts B's time before B has adopted A's genesis timeline
     *   - B then jumps to A's timeline, stranding C on a dead timeline
     *   - Lineage loyalty makes C's isolation permanent
     * 10s still covers the rapid-beacon phases (100ms/500ms/1s) where
     * the wire flag provides first-beacon identification value. After
     * 10s, the behavioral check (peer_tx_time >= 5s) takes over. */
    pkt->exon.protocol_version =
        (utlp_hal_get_micros() < UTLP_GENESIS_PHASE_3_END_US)
            ? UTLP_PROTOCOL_VERSION_GENESIS
            : UTLP_PROTOCOL_VERSION;

    /* Initialize Intron via .u64 = 0 then populate fields directly
     * (Avoids taking address of packed struct member) */
    pkt->intron.u64 = 0;

    /* Intron: Physics telemetry (hidden from adversaries) */
    pkt->intron.field.tx_power_dbm = utlp_hal_get_tx_power_dbm();
    pkt->intron.field.battery_level = utlp_hal_get_battery_scaled();
    pkt->intron.field.drift_ppm = (int16_t)utlp_get_drift_ppm();

    /* Intron: Multiplexed payload (Heartbeat mode with burst info) */
    pkt->intron.field.opcode = UTLP_CMD_NONE;  /* 0x00 = Heartbeat */
    pkt->intron.field.payload[0] = utlp_hal_get_cpu_load();      /* CPU_Load */
    pkt->intron.field.payload[1] = (uint8_t)utlp_get_role();     /* Role */
    pkt->intron.field.payload[2] = (burst_index & 0x0F) | ((score & 0x0F) << 4);  /* Burst + Score nibbles */

    /*
     * CRITICAL: Encrypt Intron BEFORE transmission
     *
     * Even for Public Mode (g_swarm_dna = UTLP_ZERO_KEY), encryption runs
     * the same code path (Herd Immunity - Purple Team PT-4).
     */
    utlp_security_encrypt_intron(pkt, g_swarm_dna);
}

/**
 * @brief Send seismic chirp using spin-wait timing (immediate mode)
 *
 * Always uses spin-wait between bursts regardless of platform capabilities.
 * Use this for reactive transmissions where scheduling is inappropriate:
 * - Entrainment pulses (immediate response to drifting peer)
 * - Emergency beacons
 * - Debugging (predictable timing without scheduler involvement)
 *
 * Achieves ±100µs precision on ESP32, ±10µs on MG24 bare metal.
 *
 * @note Uses 32-byte wire packet with encrypted Intron.
 * @note Analogous to RAIL_StartTx() in Silicon Labs RAIL API
 * @see send_chirp() for the scheduling-preferred variant
 */
static void send_chirp_immediate(void)
{
    utlp_wire_packet_t pkt;
    uint8_t my_score;
    uint64_t wait_until;

    /* Capture timestamp ONCE at chirp start */
    uint64_t chirp_epoch = get_atomic_time();

    /* Calculate my genesis score */
    my_score = calculate_genesis_score();

    /* Use primary time source arbor for stratum (Claim 253) */
    utlp_arbor_id_t arbor = utlp_get_primary_time_source();

    for (uint8_t burst = 0; burst < CHIRP_BURST_COUNT; burst++) {
        build_utlp_packet(&pkt, chirp_epoch, burst, my_score, arbor);

        utlp_hal_tx_packet(NULL, (uint8_t *)&pkt, UTLP_PACKET_SIZE);

        /* Wait between bursts (except after last) */
        if (burst < CHIRP_BURST_COUNT - 1) {
            wait_until = utlp_hal_get_micros() + CHIRP_BURST_SPACING_US;
            while (utlp_hal_get_micros() < wait_until) {
                /* Tight spin for 2ms - yields would add jitter */
            }
        }
    }
}

/**
 * @brief Send seismic chirp with optimal timing (default mode)
 *
 * Prefers hardware TX scheduling when available (MG24 RAIL), falling back
 * to spin-wait on platforms without scheduling support (ESP32).
 *
 * Scheduled TX achieves ±1µs precision by queueing all 3 bursts upfront
 * with absolute timestamps. The radio hardware handles the timing,
 * eliminating software jitter from RTOS scheduling.
 *
 * Use this as the default for:
 * - Regular beacon transmission (Genesis Pulse, Echo Rule)
 * - Any chirp where maximum timing precision matters
 *
 * Use send_chirp_immediate() instead when:
 * - Reactive transmission needed (entrainment pulses)
 * - Hardware scheduling would introduce unacceptable latency
 * - Debugging timing behavior
 *
 * @note Analogous to RAIL_StartScheduledTx() in Silicon Labs RAIL API
 * @see send_chirp_immediate() for the spin-wait variant
 */
static void send_chirp(void)
{
    uint8_t my_score;
    uint64_t chirp_epoch;

    /* Capture timestamp ONCE at chirp start */
    chirp_epoch = get_atomic_time();

    /* Calculate my genesis score */
    my_score = calculate_genesis_score();

    /* Use primary time source arbor for stratum (Claim 253) */
    utlp_arbor_id_t arbor = utlp_get_primary_time_source();

    /*
     * TX Mode Selection (following RAIL API pattern):
     *
     * If platform supports hardware TX scheduling (MG24 RAIL), schedule
     * all 3 bursts upfront for ±1µs precision. Otherwise, fall back to
     * spin-wait with ±100µs precision.
     */
    if (utlp_hal_has_scheduled_tx()) {
        /*
         * SCHEDULED TX PATH (MG24 RAIL, future platforms)
         *
         * Queue all 3 bursts atomically with absolute timestamps.
         * Hardware handles inter-burst timing with µs precision.
         */
        utlp_scheduled_tx_t bursts[CHIRP_BURST_COUNT];
        utlp_wire_packet_t pkt;
        uint64_t now = utlp_hal_get_micros();

        for (uint8_t i = 0; i < CHIRP_BURST_COUNT; i++) {
            bursts[i].tx_time_us = now + (i * CHIRP_BURST_SPACING_US);
            bursts[i].len = UTLP_PACKET_SIZE;
            /* Build 32-byte encrypted wire packet, copy to scheduled buffer */
            build_utlp_packet(&pkt, chirp_epoch, i, my_score, arbor);
            memcpy(bursts[i].payload, &pkt, UTLP_PACKET_SIZE);
        }

        if (!utlp_hal_tx_schedule(bursts, CHIRP_BURST_COUNT)) {
            utlp_hal_log_warn(TAG, "Scheduled TX failed, falling back to immediate");
            send_chirp_immediate();
        }
    } else {
        /*
         * IMMEDIATE TX PATH (ESP32, fallback)
         *
         * Spin-wait between bursts. Less precise but universally available.
         */
        send_chirp_immediate();
    }
}

/**
 * @brief Process received beacon with 32-byte wire packet decryption
 *
 * Implements the new Bio-TOTP security model:
 * 1. Validate packet size and protocol version (cleartext Exon)
 * 2. Decrypt Intron using sliding window (T-1, T, T+1)
 * 3. Apply semantic plausibility checks to detect wrong-key decryption
 * 4. Extract timing/trust data and continue with normal processing
 *
 * @param pkt HAL-level receive packet (contains payload, rssi, timestamp, mac)
 *
 * @note Decryption failure causes silent drop (no health penalty to sender)
 * @see utlp_security_decrypt_intron() for sliding window logic
 * @see Claim 255: Rolling Splice-Site Security (Bio-TOTP)
 */
static void process_beacon(const utlp_packet_t *pkt)
{
    uint8_t remote_stratum;
    uint8_t burst_index;
    uint8_t remote_score;
    uint64_t remote_tx_time;
    uint16_t remote_session_salt;  /* PT-6: Boot instance identifier */
    bool is_new_chirp;
    bool should_adopt;
    int64_t new_offset;       /* Must be 64-bit to handle runtimes > 35 minutes */
    uint32_t now_lo;
    uint8_t old_stratum;

    /* Validate 32-byte packet geometry */
    if (pkt->len < UTLP_PACKET_SIZE) {
        /* Silent drop for undersized packets (avoid log spam) */
        return;
    }

    /* Cast HAL payload to wire packet structure */
    const utlp_wire_packet_t *wire = (const utlp_wire_packet_t *)pkt->payload;

    /*
     * Protocol version gate (cleartext Exon byte [23]).
     *
     * Accept both 0x01 (established) and 0xFE (genesis-pulsing).
     * Both use the same SCALAR wire format (bytes [4-11] = uint64_t).
     * The HDC experimental branch uses 0x02 where those bytes carry a
     * phase_chord[8] — reject that to avoid timestamp corruption.
     *
     * The genesis flag (0xFE) is extracted and passed downstream so
     * adoption guards can reject genesis timelines on the FIRST beacon
     * without needing behavioral detection (≥2 observations).
     */
    uint8_t proto_ver = wire->exon.protocol_version;
    bool peer_is_genesis_wire = (proto_ver == UTLP_PROTOCOL_VERSION_GENESIS);
    if (proto_ver != UTLP_PROTOCOL_VERSION && !peer_is_genesis_wire) {
        /* Unknown version — silent drop (avoids spam in mixed swarms) */
        return;
    }

    /* Decrypt Intron using sliding window (tries T-1, T, T+1 key windows) */
    utlp_intron_t plaintext;
    if (!utlp_security_decrypt_intron(wire, g_swarm_dna, &plaintext)) {
        /* Decryption failed - wrong swarm key or corrupted packet */
        /* Silent drop, no health penalty (could be from different swarm) */
        return;
    }

    /*
     * Extract fields from decrypted packet:
     * - Exon: stratum, utlp_timestamp_us, session_salt (cleartext)
     * - Intron: payload[2] contains packed burst_index + score (decrypted)
     */
    remote_stratum = wire->exon.stratum;
    remote_tx_time = wire->exon.utlp_timestamp_us;
    remote_session_salt = wire->exon.session_salt;

    /* Unpack burst_index (lower nibble) and score (upper nibble) from Intron payload */
    burst_index = plaintext.field.payload[2] & 0x0F;
    remote_score = (plaintext.field.payload[2] >> 4) & 0x0F;

    /* Neighborhood tracking */
    now_lo = (uint32_t)pkt->rx_timestamp_us;
    update_neighbor(pkt->mac, remote_stratum, remote_score, pkt->rssi, now_lo);
    expire_neighbors(now_lo);

    /*
     * METABOLIC LEDGER: Record observation for trust/health tracking
     *
     * Record the observation, then evaluate if entrainment response is warranted.
     * The dual constraint system (token bucket + quorum) prevents RF pollution.
     */
    {
        /*
         * NOTE: observed_offset for trust stays int32_t (peer offsets are relative,
         * typically small). The overflow risk is in absolute atomic time comparisons.
         */
        int32_t observed_offset = (int32_t)((int64_t)remote_tx_time - (int64_t)pkt->rx_timestamp_us);
        uint32_t now_ms_for_tracking = (uint32_t)(pkt->rx_timestamp_us / 1000);

        /*
         * Phase 9 (Blood-Brain Barrier): Use arbor-aware observation recording.
         * Phase 11 (Spectral Retina): Pass RSSI for per-arbor signal tracking.
         * Phase 12 (PT-6): Session_Salt for reboot detection ("Seniority Bankruptcy").
         *
         * BUG FIX: Previously called utlp_trust_record_observation() which
         * defaulted to arbor 0 (WiFi), breaking per-transport trust separation.
         */
        /* v3.9: Set lineage context before recording observation.
         * This enables the trust system to freeze health for foreign-lineage peers. */
        utlp_trust_set_lineage_context(
            g_aatr.time_offset,
            (g_lineage_state == LINEAGE_COMMITTED));

        utlp_trust_record_observation_arbor(pkt->mac, observed_offset, remote_stratum,
                                            pkt->arbor_id, pkt->rssi, remote_session_salt);

        /* Update TX time tracking for genesis pulse and regression detection (S2.24) */
        utlp_trust_update_tx_tracking(pkt->mac, (int64_t)remote_tx_time, now_ms_for_tracking);

        /* Notify Loom that a beacon was received on this arbor
         * This resets the silence timer and may abort WEAVING or trigger DISSOLVING */
        utlp_loom_beacon_received(pkt->arbor_id, remote_stratum, remote_tx_time);

        /*
         * ACTIVE IMMUNITY: Evaluate entrainment response
         *
         * Compute deviation: How far is their claimed time from MY atomic time?
         * deviation = their_tx_time - my_atomic_time_at_rx
         *           = remote_tx_time - (rx_timestamp + my_offset)
         *
         * my_atomic_at_rx MUST be 64-bit to avoid overflow after 35 minutes.
         */
        int64_t my_atomic_at_rx = (int64_t)pkt->rx_timestamp_us + g_aatr.time_offset;
        int64_t deviation_us = (int64_t)remote_tx_time - my_atomic_at_rx;
        uint8_t peer_health = utlp_trust_get_peer_health(pkt->mac);

        /* Cast to int32_t for entrainment (deviation > 35 min = definitely wrong) */
        evaluate_entrainment_response(pkt->mac, peer_health, (int32_t)deviation_us, peer_is_genesis_wire);
    }

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

    /*
     * SPLIT-HORIZON PROTECTION (Claim 253: Polychromatic Stratum Asymmetry)
     *
     * Only accept timing corrections from the PRIMARY time source arbor.
     * Secondary arbors update neighbor tracking and Loom state (above), but
     * CANNOT modify time_offset or phase. This prevents "echo chamber" loops
     * where two bridges sync to each other's secondary beacons.
     *
     * Example: Bridge A follows Time Lord on WiFi (primary), broadcasts as
     * Genesis on 802.15.4. Bridge B does the same. Without split-horizon,
     * they could each adopt timing from the other's 802.15.4 beacon,
     * creating a positive feedback loop that drifts from both Time Lords.
     */
#if UTLP_POLYCHROMATIC_SPLIT_HORIZON_ENABLED
    {
        utlp_arbor_id_t primary = utlp_get_primary_time_source();
        if (pkt->arbor_id != primary) {
            /*
             * Silent skip - this can be frequent during multi-transport operation.
             * Neighbor tracking and Loom notification already done above.
             * Phase engine and source selection skipped.
             */
            return;
        }
    }
#endif

    /*
     * LINEAGE LOYALTY GATE (v3.9)
     *
     * Compute the proposed offset BEFORE any synchronization processing.
     * This single check gates both the phase engine and source selection.
     *
     * A foreign-lineage beacon is informational only: it was already
     * recorded for trust scoring (above), but it must NOT feed the
     * phase tracker or trigger epoch adoption.
     */
    {
        int64_t proposed_offset = (int64_t)remote_tx_time - (int64_t)pkt->rx_timestamp_us;

        if (!is_near_my_lineage(proposed_offset)) {
            utlp_hal_log_info(TAG,
                "LINEAGE: Foreign beacon from " PEER_FMT " (dev=%+lld us from my offset %+lld), informational only",
                PEER_ID(pkt->mac),
                (long long)(proposed_offset - g_aatr.time_offset),
                (long long)g_aatr.time_offset);
            /*
             * Skip phase engine, source selection, and adoption entirely.
             * Trust observation was already recorded above.
             * Entrainment evaluation still runs below (we may want to
             * entrain this foreign peer once they're on our lineage).
             */
            should_adopt = false;
            goto skip_source_selection;
        }
    }

    /*
     * HARDWARE PHASE ENGINE (HPLAC - Physics First!)
     *
     * Notify the phase engine of this beacon. The phase engine tracks
     * phase errors and decides whether to use hard sync (Cold Start) or
     * soft slew (Locked/Recovery) based on its internal state machine.
     *
     * This runs in PARALLEL with the legacy servo_apply_offset system
     * during the transition period. Once validated, servo_apply_offset
     * will be removed.
     *
     * v3.9: Only processes beacons from peers on (or near) our lineage.
     * Foreign beacons are filtered by the Lineage Loyalty gate above.
     *
     * Conversion: TX time (µs) → phase ticks (0-49999)
     *   peer_phase_ticks = (remote_tx_time % CYCLE_US) / TICK_US
     */
    {
        uint32_t peer_phase_ticks = (uint32_t)((remote_tx_time % UTLP_PHASE_CYCLE_US) /
                                               UTLP_PHASE_TICK_US);
        utlp_phase_on_beacon(peer_phase_ticks, pkt->rx_timestamp_us);

        /*
         * ANTICIPATORY MEMORY (v3.10 diagnostic)
         *
         * Record this beacon arrival for prediction scoring, then
         * predict the next beacon arrival based on current interval.
         * Diagnostic-only: predictions are logged, not yet used for timing.
         */
        int64_t measured_offset = (int64_t)remote_tx_time - (int64_t)pkt->rx_timestamp_us;
        utlp_anticipatory_observe(pkt->rx_timestamp_us, measured_offset);

        /* Predict next beacon: current arrival + steady-state interval */
        uint64_t next_predicted_arrival = pkt->rx_timestamp_us +
                                          BEACON_INTERVAL_STEADY_US;
        utlp_anticipatory_predict(next_predicted_arrival, measured_offset);
    }

    /*
     * BIOLOGICAL SOURCE SELECTION (S2 Governance Model)
     *
     * Replaces political "Frontier election" with health-based selection.
     * Trust is not declared - it is accumulated through observation.
     */
    should_adopt = false;

    {
        /* Get health-based recommendation from Metabolic Ledger */
        utlp_peer_ledger_t *best = utlp_trust_select_best_peer();
        /*
         * PT-16 FIX: Use system time (utlp_hal_get_micros), NOT packet RX timestamp.
         *
         * record_observation_arbor() uses UTLP_HAL_GET_TIME() for last_seen_ms.
         * check_regression() computes elapsed = now_ms - last_seen_ms.
         * If now_ms came from pkt->rx_timestamp_us (captured EARLIER than processing),
         * the subtraction wraps to ~4 billion, causing false regression detection.
         *
         * Both must use the same clock source for elapsed time to be correct.
         */
        uint32_t now_ms = (uint32_t)(utlp_hal_get_micros() / 1000);

        if (best && memcmp(best->mac, pkt->mac, 6) == 0) {
            /*
             * ADAPTIVE IMMUNITY: This sender is our most trusted peer.
             * Health (experiential) beats stratum (credential).
             * A reliable Stratum-2 peer beats an unreliable Stratum-1 peer.
             *
             * HOWEVER: Past trust persists across peer reboots (S2.24 bug).
             * A peer that was trusted at health=150 before rebooting still
             * has health=150. We must check for:
             * 1. Genesis pulse (rapid beacon intervals = recently rebooted)
             * 2. Atomic time regression (TX time went backwards = rebooted)
             */

            /* Check 1: Genesis Pulse Detection (S2.24)
             * Primary: wire-format version 0xFE (works on FIRST beacon).
             * Fallback: behavioral detection for peers on older firmware.
             */
            if (peer_is_genesis_wire ||
                utlp_trust_is_genesis_pulsing(best, (int64_t)remote_tx_time)) {
                utlp_hal_log_warn(TAG, "GENESIS PULSE: Peer " PEER_FMT " detected (interval=%dms), epoch adoption blocked",
                                  PEER_ID(pkt->mac), best->observed_interval_ms);
                should_adopt = false;
                /* Don't punish - they're legitimately rebooting, not lying */
            }
            /* Check 2: Atomic Time Regression
             * If peer's reported TX time is behind their expected time,
             * their atomic time went backwards - they rebooted.
             */
            else if (utlp_trust_check_regression(best, (int64_t)remote_tx_time, now_ms)) {
                utlp_hal_log_warn(TAG, "REGRESSION: Peer " PEER_FMT " atomic time went backwards! Epoch adoption blocked.",
                                  PEER_ID(pkt->mac));
                should_adopt = false;
                /* Punish for regression - this is unexpected behavior
                 * Apply penalty to all arbors (peer rebooted, affects all transports) */
                int arbor_idx;
                for (arbor_idx = 0; arbor_idx < UTLP_MAX_ARBORS; arbor_idx++) {
                    if (best->health_score[arbor_idx] > UTLP_COST_LYING) {
                        best->health_score[arbor_idx] -= UTLP_COST_LYING;
                    } else {
                        best->health_score[arbor_idx] = 0;
                    }
                }
            }
            else {
                /*
                 * All checks passed - safe to consider epoch adoption.
                 *
                 * PT-17 FIX: Same-stratum tiebreaker for ADAPTIVE path
                 *
                 * When two same-stratum devices meet, BOTH may have each other
                 * as "best peer" (due to PT-13c lowered threshold for N=2).
                 * Without a tiebreaker, BOTH would adopt and BOTH would drop
                 * stratum, leaving no Genesis!
                 *
                 * Apply "First Born Wins" rule: only the YOUNGER device adopts.
                 * This matches INNATE behavior at line 2240-2286.
                 *
                 * For different-stratum peers, normal ADAPTIVE adoption applies
                 * (lower-stratum peer is the authority).
                 */
                if (remote_stratum == utlp_get_stratum()) {
                    /* Same stratum - use atomic time to decide who adopts */
                    int64_t my_atomic_at_rx = pkt->rx_timestamp_us + g_aatr.time_offset;
                    bool they_are_elder = ((int64_t)remote_tx_time > my_atomic_at_rx);

                    if (they_are_elder) {
                        should_adopt = true;
                        utlp_hal_log_info(TAG, "ADAPTIVE: Same-stratum elder peer " PEER_FMT " (health=%d, atomic %lld > mine %lld) - deferring",
                                          PEER_ID(pkt->mac), utlp_trust_get_peer_health(best->mac),
                                          (long long)remote_tx_time, (long long)my_atomic_at_rx);
                    } else {
                        /* I am elder - hold ground, do not adopt */
                        utlp_hal_log_info(TAG, "ADAPTIVE: Same-stratum but I'm elder (atomic %lld > peer's %lld) - holding Genesis",
                                          (long long)my_atomic_at_rx, (long long)remote_tx_time);
                    }
                } else if (remote_stratum < utlp_get_stratum()) {
                    /*
                     * Different stratum, peer has BETTER authority - adopt.
                     *
                     * v3.9 STRATUM GUARD: Only adopt peers with strictly lower
                     * (better) stratum. A Genesis (Stratum 1) must NEVER adopt
                     * a Follower (Stratum 2+) via the ADAPTIVE path, even if
                     * that Follower is highly trusted. Authority flows downward
                     * in the stratum hierarchy; health cannot invert it.
                     *
                     * If a Genesis device is truly broken, the entrainment
                     * system (not adoption) handles correction. If irredeemable,
                     * self-demotion logic (line ~2505) will step it down.
                     */
                    should_adopt = true;
                    utlp_hal_log_info(TAG, "ADAPTIVE: Trusted peer " PEER_FMT " (health=%d, stratum=%d < mine=%d)",
                                      PEER_ID(pkt->mac), utlp_trust_get_peer_health(best->mac),
                                      remote_stratum, utlp_get_stratum());
                } else {
                    /* Different stratum, peer has LOWER authority (higher number).
                     * Do not adopt upward - this prevents authority inversion.
                     * A Genesis should never follow a Follower. */
                    utlp_hal_log_info(TAG, "ADAPTIVE: Trusted peer " PEER_FMT " has lower authority (stratum=%d > mine=%d), holding ground",
                                      PEER_ID(pkt->mac), remote_stratum, utlp_get_stratum());
                }
            }
        }
        else if (!best && remote_stratum < utlp_get_stratum()) {
            /*
             * INNATE IMMUNITY (S2 Bootstrap) - Better Stratum
             *
             * The Ledger is empty - no memory cells exist yet.
             * Like a newborn's innate immune system, we provisionally trust
             * signals that "look healthy" (low stratum = proper MHC markers).
             *
             * This is not blind trust - we will watch closely and build
             * adaptive immunity (Ledger entries) from this interaction.
             *
             * v3.4 FIX-1: Genesis pulse protection - a newly booted peer
             * transmits rapid 100ms beacons that can disrupt established sync.
             * Block INNATE adoption until peer exits genesis phase.
             */
            utlp_peer_ledger_t *sender = utlp_trust_get_peer(pkt->mac);
            if (peer_is_genesis_wire ||
                (sender && utlp_trust_is_genesis_pulsing(sender, (int64_t)remote_tx_time))) {
                utlp_hal_log_warn(TAG, "INNATE: Blocking genesis-pulsing peer " PEER_FMT " (stratum=%d, ver=0x%02X)",
                                  PEER_ID(pkt->mac), remote_stratum, proto_ver);
                /* Do NOT adopt - wait for peer to exit genesis phase */
            } else {
                should_adopt = true;
                utlp_hal_log_info(TAG, "INNATE: Provisional trust for stratum %d peer " PEER_FMT " (ledger empty)",
                                  remote_stratum, PEER_ID(pkt->mac));
            }
        }
        else if (!best && remote_stratum == utlp_get_stratum()) {
            /*
             * INNATE IMMUNITY (S2 Bootstrap) - Same Stratum "First Born Wins"
             *
             * THE GENESIS PROBLEM: Two devices boot as Genesis (Stratum 1).
             * Both think they ARE the atomic clock. Without this check, they
             * would wait 80+ seconds for Adaptive Immunity to resolve the tie.
             *
             * A swarm must be able to be born of one. The first device IS the
             * atomic clock. When the second arrives, it should recognize
             * "there's an established Genesis here" and defer IMMEDIATELY.
             *
             * TIE-BREAKER: Oldest atomic time wins.
             *
             * Compare the peer's TX timestamp (their atomic time) with our
             * atomic time at reception. Higher value = been running longer.
             * The device that booted first has accumulated more atomic time.
             *
             * This is philosophically correct: "the swarm is born of one,
             * so the first one should be the one." The elder establishes
             * the timeline; the newcomer joins it.
             *
             * NOTE: This is easily spoofable (just claim a high TX time).
             * For production, consider MAC fallback or cryptographic proof.
             * For testing, this matches the "first boot = Genesis" expectation.
             *
             * v3.4 FIX-1: Genesis pulse protection applies here too.
             * A newly booted same-stratum peer should not be trusted
             * until they exit their rapid-beacon genesis phase.
             */
            utlp_peer_ledger_t *sender = utlp_trust_get_peer(pkt->mac);
            if (peer_is_genesis_wire ||
                (sender && utlp_trust_is_genesis_pulsing(sender, (int64_t)remote_tx_time))) {
                utlp_hal_log_warn(TAG, "INNATE: Blocking genesis-pulsing same-stratum peer " PEER_FMT " (ver=0x%02X)",
                                  PEER_ID(pkt->mac), proto_ver);
                /* Do NOT adopt - wait for peer to exit genesis phase.
                 *
                 * PHENOTYPE TRUTH (v3.9): Even though adoption is blocked,
                 * we can compare atomic times to determine if we're younger.
                 * If so, we should NOT claim Genesis stratum. */
                {
                    int64_t my_atomic_at_rx = pkt->rx_timestamp_us + g_aatr.time_offset;
                    bool they_are_elder = ((int64_t)remote_tx_time > my_atomic_at_rx);
                    if (they_are_elder && utlp_get_stratum() == STRATUM_ORIGIN) {
                        utlp_set_stratum_for_arbor(
                            (utlp_arbor_id_t)pkt->arbor_id, remote_stratum + 1);
                        g_last_stratum_change = utlp_hal_get_micros();
                        utlp_hal_log_info(TAG,
                            "PHENOTYPE: Demoting to stratum %d (elder " PEER_FMT " genesis-pulsing, adoption deferred)",
                            remote_stratum + 1, PEER_ID(pkt->mac));
                    }
                }
            } else {
                int64_t my_atomic_at_rx = pkt->rx_timestamp_us + g_aatr.time_offset;
                bool they_are_elder = ((int64_t)remote_tx_time > my_atomic_at_rx);

                if (they_are_elder) {
                    should_adopt = true;
                    utlp_hal_log_info(TAG, "INNATE: Same-stratum elder - peer " PEER_FMT " atomic time %lld > mine %lld, deferring",
                                      PEER_ID(pkt->mac), (long long)remote_tx_time, (long long)my_atomic_at_rx);
                }
                /* If I am elder (higher atomic time), I hold ground - do not adopt */
            }
        }
        /* If best exists but is not this sender, OR no best and stratum not better:
         * Do not adopt. Trust the established relationships. */
    }

skip_source_selection:
    /* Lineage Loyalty gate jumps here for foreign beacons (should_adopt=false) */

    /*
     * LINEAGE LOYALTY: PROBATION → COMMITTED transition (v3.9)
     *
     * Check on every non-foreign beacon (not just adoption successes).
     * This ensures commitment can occur even when should_adopt is false,
     * e.g., an elder Genesis correctly holding ground still advances
     * through PROBATION → COMMITTED after the stability period.
     */
    if (g_lineage_state == LINEAGE_PROBATION) {
        uint64_t time_since_change = utlp_hal_get_micros() - g_last_stratum_change;
        if (time_since_change > UTLP_LINEAGE_COMMITMENT_MIN_US) {
            lineage_transition(LINEAGE_COMMITTED);
        }
    }

    if (should_adopt) {
        old_stratum = utlp_get_stratum();  /* Primary arbor stratum */
        new_offset = (int64_t)remote_tx_time - (int64_t)pkt->rx_timestamp_us;

        /*
         * GENESIS RESET DETECTION (S2 Section 8.24)
         *
         * Check if peer's atomic time jumped forward unexpectedly.
         * This indicates they may have reset with a newer epoch.
         *
         * If detected:
         * - Block epoch adoption (don't trust their new timeline)
         * - Allow phase entrainment after they stabilize
         */
        utlp_peer_ledger_t *peer = utlp_trust_get_peer(pkt->mac);
        if (peer && peer->last_tx_time_us > 0) {
            uint32_t now_ms = (uint32_t)(pkt->rx_timestamp_us / 1000);
            /* Get aggregate (most recent) last_seen across all arbors */
            uint32_t agg_last_seen = 0;
            int arbor_i;
            for (arbor_i = 0; arbor_i < UTLP_MAX_ARBORS; arbor_i++) {
                if (peer->last_seen_ms[arbor_i] > agg_last_seen) {
                    agg_last_seen = peer->last_seen_ms[arbor_i];
                }
            }
            uint32_t elapsed_ms = now_ms - agg_last_seen;

            if (servo_detect_genesis_reset(peer->last_tx_time_us, remote_tx_time, elapsed_ms)) {
                utlp_hal_log_warn(TAG, "GENESIS RESET blocked: Peer " PEER_FMT " jumped to newer epoch",
                                  PEER_ID(pkt->mac));
                /* Don't adopt their new epoch, but don't punish either */
                /* They'll stabilize and we can entrain later */
                goto skip_adoption;
            }
        }

        /*
         * POLYCHROMATIC STRATUM UPDATE (Claim 253)
         *
         * Update stratum for the arbor this beacon arrived on, and set it
         * as the primary time source. This enables per-arbor stratum tracking
         * for bridge nodes operating across multiple transports.
         */
        utlp_set_stratum_for_arbor((utlp_arbor_id_t)pkt->arbor_id, remote_stratum + 1);
        utlp_set_primary_time_source((utlp_arbor_id_t)pkt->arbor_id);
        memcpy(g_aatr.best_source_mac, pkt->mac, UTLP_MAC_SIZE);

        /* Track stratum changes for Promotion Pulse */
        {
            uint8_t new_stratum = utlp_get_stratum();
            if (new_stratum != old_stratum) {
                g_last_stratum_change = utlp_hal_get_micros();
                g_is_provider = should_relay();
                utlp_hal_log_info(TAG, "Stratum changed: %d -> %d (provider=%s, arbor=%d)",
                         old_stratum, new_stratum, g_is_provider ? "YES" : "NO",
                         pkt->arbor_id);
            }
        }

        /*
         * LINEAGE LOYALTY: State transition on successful adoption (v3.9)
         *
         * NAIVE/GRIEVING → PROBATION: We just adopted a new timeline.
         * The servo is converging; gate remains permissive to allow
         * subsequent beacons from this source to fine-tune the offset.
         *
         * PROBATION → COMMITTED: Check if we've been stable long enough.
         * This transition activates the lineage gate, which will reject
         * beacons from foreign timelines going forward.
         */
        if (g_lineage_state == LINEAGE_NAIVE ||
            g_lineage_state == LINEAGE_GRIEVING) {
            lineage_transition(LINEAGE_PROBATION);
        }

        /* NOTE: PROBATION→COMMITTED check moved to skip_source_selection label
         * so it runs on ALL non-foreign beacons, not just adoption successes.
         * This ensures commitment can occur even when should_adopt is false
         * (e.g., elder Genesis correctly holding ground). */

        /*
         * LUCKY PACKET MINIMUM FILTER (v3.8 PT-15)
         *
         * Network jitter is asymmetric - packets can only arrive LATE.
         * Classify this packet to decide if we should update the servo:
         *   - LUCKY: New floor (best offset seen) - trust fully
         *   - OKAY: Near floor - trust normally
         *   - JITTER: Far from floor - ignore for sync, just record observation
         */
        uint64_t uptime_us = utlp_hal_get_micros();
        packet_quality_t quality = classify_packet(new_offset);

        if (quality == PACKET_JITTER) {
            /*
             * Jitter packet - skip servo update but still process for trust.
             * The observation was already recorded above in the trust system.
             * Record stats for periodic aggregate logging (every 60s).
             * Stratum tracking already updated above, just don't slew.
             */
            record_jitter_stats(new_offset);
        } else {
            /* Track lucky/okay counts for aggregate stats */
            if (quality == PACKET_LUCKY) {
                g_lucky.lucky_count++;
            } else {
                g_lucky.okay_count++;
            }
            /*
             * SERVO-LOCKED PHASE CORRECTION (S2 Claim 55)
             *
             * Use frequency slewing instead of instant phase jumps.
             * During genesis phase (first 10s): instant jumps allowed for fast sync.
             * After genesis: slew toward target to maintain spectral purity.
             *
             * This replaces the direct assignment:
             *   g_aatr.time_offset = new_offset;
             *   utlp_hal_set_time_offset(new_offset);
             */
            bool jumped = servo_apply_offset(new_offset, uptime_us);

            /*
             * Update internal state to track CURRENT offset (not target!)
             *
             * BUG FIX (Coherence Oscillation Audit - Bug #5):
             * Previously used target_offset when slewing, but servo_tick() is
             * still interpolating toward target. Using target causes subsequent
             * phase error calculations to see phantom errors (double-correction).
             *
             * current_offset reflects where the clock ACTUALLY is, not where
             * it wants to be. This fixes stale offset usage in deviation
             * calculations (Bug #3 was a symptom of this).
             */
            if (jumped) {
                g_aatr.time_offset = new_offset;
            } else {
                /* SPINLOCK: Read current offset atomically (64-bit on 32-bit MCU) */
                portENTER_CRITICAL(&g_servo_spinlock);
                g_aatr.time_offset = g_servo.current_offset;
                portEXIT_CRITICAL(&g_servo_spinlock);
            }

            /* Log with Lucky Packet indicator */
            if (quality == PACKET_LUCKY) {
                utlp_hal_log_info(TAG, "LUCKY: offset=%+lld us (new floor) stratum=%d %s",
                                  (long long)new_offset, utlp_get_stratum(),
                                  jumped ? "jumped" : "slewing");
            } else {
                utlp_hal_log_info(TAG, "SYNCED: stratum=%d, offset=%+lld us (%s)",
                                  utlp_get_stratum(), (long long)new_offset,
                                  jumped ? "jumped" : "slewing");
            }

            /* Notify SMSP that atomic time is now valid (first sync only) */
            if (!g_smsp_notified) {
                smsp_notify_sync_ready();
                g_smsp_notified = true;
            }
        }
    }
skip_adoption:

    /*
     * PHENOTYPE TRUTH (v3.9 Lineage Loyalty - Component A)
     *
     * If we reached skip_adoption via genesis reset detection, the adoption
     * was blocked but we HAD determined should_adopt=true. This means a
     * peer with equal-or-better stratum exists, and we are NOT the authority.
     * Demote our stratum to prevent false Genesis advertising.
     *
     * The principle: claiming a stratum you haven't earned is a protocol
     * violation. Observable phenotype (beacon stratum field) must match
     * actual genotype (whether you are truly the timeline authority).
     */
    if (should_adopt &&
        utlp_get_stratum() == STRATUM_ORIGIN &&
        remote_stratum <= utlp_get_stratum()) {
        utlp_set_stratum_for_arbor(
            (utlp_arbor_id_t)pkt->arbor_id, remote_stratum + 1);
        g_last_stratum_change = utlp_hal_get_micros();
        utlp_hal_log_info(TAG,
            "PHENOTYPE: Demoting at skip_adoption (stratum %d claim invalid, peer " PEER_FMT " has stratum %d)",
            STRATUM_ORIGIN, PEER_ID(pkt->mac), remote_stratum);
    }

    /*
     * ORIGIN SELF-AWARENESS (S2 Biological Governance)
     *
     * Time Lord (Genesis/Origin) nodes should recognize when to step down.
     * This prevents stale or inferior time sources from persisting as
     * Origin when better sources exist.
     *
     * NOTE: This uses MAC tie-breaker (not atomic time) because:
     * 1. The Metabolic Ledger doesn't store absolute atomic times
     * 2. This triggers for ESTABLISHED peers (health > 200), not newcomers
     * 3. MAC is a stable fallback for late-stage role resolution
     *
     * For BOOTSTRAP (newcomers), see Innate Immunity above which uses
     * atomic time ("first born wins") for philosophically correct behavior.
     */
    if (utlp_get_stratum() == STRATUM_ORIGIN) {
        utlp_peer_ledger_t *best = utlp_trust_select_best_peer();
        uint8_t best_health = best ? utlp_trust_get_peer_health(best->mac) : 0;

        if (best && best_health > 200) {
            /*
             * A very healthy peer exists. Should I step down?
             *
             * DOMINANCE HIERARCHY: Two healthy Origin nodes don't both leave.
             * Like wolves sizing each other up, one must submit based on
             * a static trait (MAC address serves as the "size" equivalent).
             *
             * Lower MAC = dominant (holds ground as Time Lord)
             */
            bool they_are_dominant = (compare_mac(best->mac, g_local_mac) < 0);

            if (they_are_dominant) {
                utlp_hal_log_warn(TAG, "Origin self-awareness: Dominant peer " PEER_FMT " detected (health=%d)",
                                  PEER_ID(best->mac), best_health);
                g_self_demotion_votes++;

                if (g_self_demotion_votes > 3) {
                    /* Voluntary submission: step down gracefully on primary arbor */
                    utlp_arbor_id_t primary = utlp_get_primary_time_source();
                    utlp_set_stratum_for_arbor(primary, STRATUM_ORIGIN + 1);
                    g_self_demotion_votes = 0;
                    g_last_stratum_change = utlp_hal_get_micros();
                    utlp_hal_log_info(TAG, "Voluntary demotion: Better Origin exists");
                }
            } else {
                /* I am dominant - hold my ground, reset vote count */
                g_self_demotion_votes = 0;
            }
        }
    }
}

/*============================================================================
 * ACTIVE IMMUNITY - ENTRAINMENT (S2 Section 2.4)
 *
 * When we detect a significantly wrong beacon from a juvenile (low-health peer),
 * we may fire an "entrainment pulse" to pull the swarm into synchronization.
 *
 * DUAL CONSTRAINT SYSTEM:
 *   1. Internal: Token bucket (prevents cytokine storm / RF pollution)
 *   2. External: Quorum sensing (prevents Crazy Old Man attacking valid peers)
 *
 * Both constraints must be satisfied before firing entrainment.
 *==========================================================================*/

/** @brief Deviation thresholds for classifying peer timing quality */
#define ENTRAINMENT_THRESHOLD_DRIFTING_US     2000    /* 2ms = drifting */
#define ENTRAINMENT_THRESHOLD_LYING_US       100000   /* 100ms = lying */

/** @brief Minimum health to be considered for entrainment (juveniles only) */
#define ENTRAINMENT_TARGET_MAX_HEALTH         80      /* Only entrain juveniles */

/** @brief Quorum threshold for agreement check */
/**
 * v3.11: Scale quorum agreement window with steady-state beacon interval.
 *
 * At 60s intervals, crystal drift (20-100 ppm) causes 1.2-6ms of offset
 * divergence between agreeing peers. The fixed 2ms window meant peers that
 * agree on lineage still fail the quorum "agreement" check, blocking all
 * entrainment even when the swarm is healthy.
 *
 * Same formula as self-consistency/consensus scaling: for 60s beacons,
 * the calculated value (60000*2=120000) exceeds the 10ms clamp, so we
 * use 10ms. This allows ~166 ppm of crystal drift — well within the
 * 20-100 ppm typical range with safety margin.
 */
#define ENTRAINMENT_QUORUM_THRESHOLD_US       10000   /* 10ms for 60s beacons */

/**
 * @brief Evaluate and potentially fire an entrainment pulse
 *
 * Called when we detect a peer with significantly wrong timing.
 * Uses dual constraint system to prevent both RF pollution (token bucket)
 * and the "Crazy Old Man" scenario (quorum sensing).
 *
 * @param peer_mac      MAC of the drifting/lying peer
 * @param peer_health   Health score of the peer (from Ledger)
 * @param deviation_us  How far off their timing was (absolute value)
 */
static void evaluate_entrainment_response(const uint8_t *peer_mac,
                                        uint8_t peer_health,
                                        int32_t deviation_us,
                                        bool peer_is_genesis)
{
    /*
     * TARGETING: Only entrain "juveniles" (low-health peers)
     *
     * High-health peers have earned trust through observation.
     * If they're reporting different timing, maybe WE are the problem.
     */
    if (peer_health > ENTRAINMENT_TARGET_MAX_HEALTH) {
        return;  /* Trusted peer - defer to their experience */
    }

    /*
     * SEVERITY: Only respond to significant deviations
     */
    int32_t abs_deviation = deviation_us;
    if (abs_deviation < 0) abs_deviation = -abs_deviation;

    if (abs_deviation < ENTRAINMENT_THRESHOLD_DRIFTING_US) {
        return;  /* Within tolerance - no action needed */
    }

    /*
     * DUAL CONSTRAINT SYSTEM (S2 Active Immunity)
     *
     * Like real immune systems, we need BOTH:
     * 1. Internal capacity (T-cells/tokens)
     * 2. External validation (quorum sensing)
     *
     * This prevents the "Crazy Old Man" attacking the healthy swarm.
     */

    /*
     * v3.4 FIX-2: Genesis Pulse Conservation
     *
     * Genesis-pulsing peers (100ms interval) will naturally stabilize after 5s.
     * Wasting entrainment tokens on them causes:
     *   - Token exhaustion → ANERGY state
     *   - Established peers become deaf to each other
     *   - Sync collapse in the established swarm
     *
     * STRATEGY: Don't entrain genesis-pulsing peers - they'll self-correct.
     * This preserves our immune budget for real threats.
     */
    utlp_peer_ledger_t *target_peer = utlp_trust_get_peer(peer_mac);
    if (peer_is_genesis ||
        (target_peer && utlp_trust_is_genesis_pulsing(target_peer, target_peer->last_tx_time_us))) {
        utlp_hal_log_info(TAG, "Entrainment: Skipping genesis-pulsing peer " PEER_FMT " - will self-correct",
                          PEER_ID(peer_mac));
        return;  /* Conserve tokens - genesis peer will stabilize naturally */
    }

    /*
     * Constraint 1: INTERNAL CHECK - Do I have budget? (Token Bucket)
     *
     * v3.7 FIX (PT-12): Use has_budget() (check only) instead of can_defend()
     * (check + consume). Token consumption happens ONLY when we actually fire,
     * not when checking. This prevents token waste when quorum check fails.
     */
    if (!utlp_immune_has_budget()) {
        utlp_hal_log_warn(TAG, "Entrainment: Budget exhausted (anergy) - " PEER_FMT " escapes",
                          PEER_ID(peer_mac));
        return;
    }

    /* Constraint 2: EXTERNAL CHECK - Do I have crowd support? (Quorum Sensing) */
    if (!utlp_trust_has_quorum(g_aatr.time_offset, ENTRAINMENT_QUORUM_THRESHOLD_US)) {
        utlp_hal_log_warn(TAG, "Entrainment: No quorum - I may be the outlier, not " PEER_FMT,
                          PEER_ID(peer_mac));
        return;  /* Don't attack! I might be wrong! - NO TOKEN CONSUMED */
    }

    /*
     * BOTH CONSTRAINTS SATISFIED - Fire entrainment pulse
     *
     * This is a "fever response" - temporarily increase beacon rate
     * to pull the drifting peer into sync. The pulse contains our
     * atomic time, which they can use to entrain.
     *
     * Use send_chirp_immediate() because:
     * 1. Entrainment is REACTIVE - we need to respond NOW
     * 2. Scheduling adds latency (queue + wait for scheduled time)
     * 3. Precision matters less than timeliness for entrainment
     */
    if (abs_deviation >= ENTRAINMENT_THRESHOLD_LYING_US) {
        utlp_hal_log_info(TAG, "ENTRAINMENT [LYING]: Entraining juvenile " PEER_FMT " (dev=%+ldus, health=%d)",
                          PEER_ID(peer_mac), (long)deviation_us, peer_health);
    } else {
        utlp_hal_log_info(TAG, "ENTRAINMENT [DRIFT]: Entraining juvenile " PEER_FMT " (dev=%+ldus, health=%d)",
                          PEER_ID(peer_mac), (long)deviation_us, peer_health);
    }

    /* Consume token NOW - right before actually firing (v3.7 PT-12) */
    utlp_immune_consume_token();

    /* Send entrainment pulse (immediate mode - reactive response) */
    send_chirp_immediate();

    /* Log entrainment budget status */
    utlp_hal_log_info(TAG, "  Entrainment budget: %d/%d tokens remaining",
                      utlp_immune_get_tokens(), UTLP_IMMUNE_BUDGET_MAX);
}

/*============================================================================
 * PHYSICS - Stub (LED control moved to SMSP task)
 *
 * Prior to SMSP, this function contained time-indexed LED control logic.
 * LED actuation is now handled by the SMSP task (utlp_smsp.c) which:
 *   1. Waits for UTLP sync before starting
 *   2. Uses atomic time from utlp_hal_get_atomic_time_us()
 *   3. Executes score-based patterns (not hardcoded physics)
 *
 * This stub remains for backward compatibility and potential future use
 * (e.g., motor control, sensor sampling at specific atomic times).
 *==========================================================================*/

static void run_physics(uint64_t atomic_now)
{
    /* LED control moved to SMSP task - see utlp_smsp.c */
    (void)atomic_now;
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

    /* Initialize MCPWM Phase Engine (HPLAC - Physics First!)
     *
     * The phase engine MUST be initialized first because it owns the
     * hardware timer that defines atomic time. All subsequent subsystems
     * derive their timing from this single source of truth.
     *
     * "Physics First: Hardware defines time, not software."
     */
    esp_err_t phase_ret = utlp_phase_init();
    if (phase_ret != ESP_OK) {
        utlp_hal_log_error(TAG, "Phase engine init failed! Falling back to software timing.");
        /* Continue with legacy software-based timing */
    }

    /* Initialize transport layer (handles staggered startup for multi-arbor)
     *
     * TEMPORARY: ESP-NOW only while debugging epoch/phase servo.
     * To re-enable dual arbor (802.15.4 + ESP-NOW), change to:
     *   transport_cfg.transports = UTLP_TRANSPORT_ALL;
     *
     * Original behavior with UTLP_TRANSPORT_ALL:
     * - 802.15.4 starts immediately (scheduled send PHY)
     * - ESP-NOW delayed by stagger_espnow_ms (default 15s)
     */
    utlp_transport_config_t transport_cfg = UTLP_TRANSPORT_CONFIG_DEFAULT();
    transport_cfg.transports = UTLP_TRANSPORT_ESPNOW;  /* ESP-NOW only for now */
    if (!utlp_transport_init(&transport_cfg)) {
        utlp_hal_log_error(TAG, "Transport init failed! Falling back to HAL only.");
        utlp_hal_init();  /* Fallback to direct HAL init */
    }

    /* Initialize Metabolic Ledger (Biological Governance) */
    utlp_trust_init();

    /* Initialize Immune Checkpoint (Active Immunity - S2 Section 2.4) */
    utlp_immune_init();

    /* Initialize SMSP (Synchronized Multimodal Score Protocol) */
    smsp_init();

    /* Create SMSP task (waits for sync before starting playback) */
    xTaskCreate(smsp_task, "SMSP", SMSP_TASK_STACK_SIZE, NULL, SMSP_TASK_PRIORITY, NULL);

    /* Initialize Engine Timer (10Hz independent drift model tick)
     *
     * This timer runs servo_tick() independently of packet reception,
     * ensuring the drift model stays updated even when transports are
     * yielded to the application layer. Critical for Arbor architecture.
     */
    engine_timer_init();

    /* Initialize Arbor subsystem (per-transport dormancy tracking) */
    utlp_arbor_init();

    /* Initialize Loom state machine (emergent Time Lord promotion)
     *
     * The Loom detects silence on each arbor and triggers Time Lord
     * promotion when no beacons are received for 2 minutes.
     */
    utlp_loom_init();

    /*
     * GENESIS BOOTSTRAP: If we're stratum 1 (Genesis), our local time IS
     * the atomic clock. Notify SMSP immediately - no external sync needed.
     * Followers will wait for beacon adoption to trigger sync.
     */
    if (utlp_get_stratum() == STRATUM_ORIGIN) {
        smsp_notify_sync_ready();
        g_smsp_notified = true;
        utlp_hal_log_info(TAG, "Genesis: SMSP unlocked (no external sync needed)");
    }

    /* Get our MAC */
    utlp_hal_get_mac(g_local_mac);

    /* Eagerly generate session salt so it appears in the startup banner.
     * Without this, salt is lazily generated on first beacon TX. */
    uint16_t salt = utlp_security_get_session_salt();

    /* Startup banner */
    utlp_hal_log_info(TAG, "========================================");
    utlp_hal_log_info(TAG, "UTLP v3 - Biological Governance + SMSP");
    utlp_hal_log_info(TAG, "\"Time is born of one.\"");
    utlp_hal_log_info(TAG, "========================================");
    utlp_hal_log_info(TAG, "MAC: %02X:%02X:%02X:%02X:%02X:%02X  Salt: 0x%04X",
             g_local_mac[0], g_local_mac[1], g_local_mac[2],
             g_local_mac[3], g_local_mac[4], g_local_mac[5], salt);
    utlp_hal_log_info(TAG, "Stratum: %d (GENESIS)", utlp_get_stratum());
    utlp_hal_log_info(TAG, "Beacon: 11-byte Seismic Chirp (3-burst @ 2ms)");
    utlp_hal_log_info(TAG, "Trust: Metabolic Ledger (Adaptive Immunity)");
    utlp_hal_log_info(TAG, "Relay: Frontier detection (edge nodes = Providers)");
    utlp_hal_log_info(TAG, "Interval: Genesis Pulse / Promotion Pulse / Echo Rule");
    utlp_hal_log_info(TAG, "Servo-Lock: Variable Gain PLL (Cold/Locked/Recovery @ 5s/10ms)");
    utlp_hal_log_info(TAG, "Engine: 10Hz independent tick (drift model always running)");
    utlp_hal_log_info(TAG, "SMSP: Score-based LED (pattern=%s)", smsp_get_pattern_name());
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

        /* 2. GENESIS PULSE (Loom-triggered Time Lord announcement)
         *
         * The Loom schedules Genesis Pulses when:
         * - An arbor transitions to ANCHOR (automatic Time Lord promotion)
         * - An arbor wakes from dormancy (mandatory announcement)
         * - POLYCHROMATIC: Secondary transport promoted to genesis (Claim 253)
         *
         * Genesis Pulse uses stratum from the Loom and sends on the
         * arbor that requested the genesis pulse.
         */
        utlp_arbor_id_t genesis_arbor;
        if (utlp_loom_consume_genesis_request(&genesis_arbor)) {
            uint8_t genesis_stratum = utlp_loom_get_genesis_stratum();
            if (genesis_stratum != 0xFF) {
                /*
                 * Polychromatic support (Claim 253): Use the arbor from the
                 * genesis request, not necessarily the primary. This enables
                 * genesis pulses on silent secondary transports.
                 */
                uint8_t saved_stratum = utlp_get_stratum_for_arbor(genesis_arbor);
                utlp_set_stratum_for_arbor(genesis_arbor, genesis_stratum);

                send_chirp();
                g_last_beacon_time = now;

                utlp_hal_log_info(TAG, "=== GENESIS PULSE (stratum=%d, arbor=%s) ===",
                                  genesis_stratum, utlp_arbor_name(genesis_arbor));

                /* Restore stratum (will be updated by normal processing) */
                utlp_set_stratum_for_arbor(genesis_arbor, saved_stratum);
            }
        }

        /* 3. TRANSMIT (if Genesis or Provider) */
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
                             (utlp_get_stratum() == STRATUM_ORIGIN) ? "Origin" : "Provider");
                    last_logged_interval = beacon_interval;
                }
            }
        }

        /* 4. SERVO-LOCK (S2 Claim 55)
         *
         * Tick the servo-lock loop to apply gradual phase corrections.
         * This implements firefly synchronization with frequency slewing
         * instead of phase jumps, maintaining spectral purity for
         * coherent beamforming applications.
         */
        servo_tick(uptime);

        /* 5. PHYSICS */
        run_physics(now);

        /* 6. DRIFT STATS */
        log_drift_stats_if_due(uptime);

        /* 7. METABOLIC LEDGER STATUS (same intervals as drift stats)
         *
         * Phase 1: Passive observation - log trust data to verify
         * the Ledger is populating correctly before Phase 2 activation.
         */
        {
            static uint64_t last_trust_log_us = 0;
            uint64_t log_interval = (uptime < STATS_LOG_FAST_END_US)
                ? STATS_LOG_INTERVAL_FAST_US
                : STATS_LOG_INTERVAL_SLOW_US;

            if ((uptime - last_trust_log_us) >= log_interval) {
                last_trust_log_us = uptime;
                utlp_trust_log_status();
                utlp_trust_log_coherence();  /* Phase 4: Macro-state logging */
            }
        }
    }
}
