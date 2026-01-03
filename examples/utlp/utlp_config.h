/**
 * @file utlp_config.h
 * @brief UTLP Configuration Constants - Single Source of Truth
 *
 * All tunable parameters for UTLP timing synchronization.
 * Centralizes configuration to prevent magic numbers and ensure consistency.
 *
 * @section philosophy Philosophy: Constants Define Behavior
 *
 * From CLAUDE.md: "Never hardcode comparison values, delays, thresholds, or ranges."
 * This file is the Single Source of Truth (SSOT) for all UTLP configuration.
 *
 * @section categories Configuration Categories
 *
 * 1. **Genesis Pulse** - Beacon intervals during startup
 * 2. **Servo-Lock** - Phase correction slewing (Claim 55)
 * 3. **Coherence** - Phase agreement thresholds
 * 4. **Seismic Chirp** - Burst timing for drift extraction
 * 5. **Neighborhood** - Peer tracking and frontier detection
 *
 * @see docs/UTLP_Technical_Supplement_S2.md - Claim 55 (Servo-Locked Phase Correction)
 * @see examples/utlp/utlp_trust.h - Trust-specific configuration (kept separate)
 *
 * @version 1.0.0
 * @date 2026-01-02
 *
 * @copyright
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#pragma once

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/*============================================================================
 * GENESIS PULSE - Dynamic Beacon Interval (S2, Prior Art Section 7)
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
 *==========================================================================*/

/** @defgroup genesis_pulse Genesis Pulse Timing
 * @{
 */

/** @brief Phase 1 end time (genesis burst complete) */
#define UTLP_GENESIS_PHASE_1_END_US      1000000ULL      /*  1 second */

/** @brief Phase 2 end time (fast convergence complete) */
#define UTLP_GENESIS_PHASE_2_END_US      5000000ULL      /*  5 seconds */

/** @brief Phase 3 end time (settling complete) */
#define UTLP_GENESIS_PHASE_3_END_US     10000000ULL      /* 10 seconds */

/** @brief Phase 4 end time (stabilizing complete) */
#define UTLP_GENESIS_PHASE_4_END_US     60000000ULL      /* 60 seconds */

/** @brief Beacon interval during phase 1 (genesis burst) */
#define UTLP_BEACON_INTERVAL_PHASE_1_US    100000        /* 100ms */

/** @brief Beacon interval during phase 2 (fast convergence) */
#define UTLP_BEACON_INTERVAL_PHASE_2_US    500000        /* 500ms */

/** @brief Beacon interval during phase 3 (settling) */
#define UTLP_BEACON_INTERVAL_PHASE_3_US   1000000        /* 1s */

/** @brief Beacon interval during phase 4 (stabilizing) */
#define UTLP_BEACON_INTERVAL_PHASE_4_US  10000000        /* 10s */

/** @brief Beacon interval at steady state */
#define UTLP_BEACON_INTERVAL_STEADY_US   60000000        /* 60s */

/** @} */ /* genesis_pulse */

/*============================================================================
 * SERVO-LOCKED PHASE CORRECTION (S2 Claim 55)
 *
 * "Standard Firefly" applies Δφ instantly at beacon reception.
 * "UTLP Servo-Lock" applies Δf = Δφ/T_convergence over configurable window.
 *
 * This preserves continuous waveform integrity for coherent beamforming:
 * - Phase jumps create spectral splatter (wideband noise burst)
 * - Frequency slewing maintains spectral purity throughout correction
 *
 * Exception: During GENESIS_PHASE_3 (first 10s), jumps are allowed for
 * fast initial sync. After 10s, all corrections use slewing.
 *==========================================================================*/

/** @defgroup servo_lock Servo-Locked Phase Correction
 * @{
 */

/**
 * @brief Convergence window for phase slewing (microseconds)
 *
 * From S2 Claim 55: "typically 100-1000ms"
 * We use 500ms as a balance between convergence speed and spectral purity.
 *
 * Δf = Δφ / T_CONVERGENCE
 * For a 10ms phase error: drift_correction = 10ms / 500ms = 20,000 ppb
 */
#define UTLP_SERVO_CONVERGENCE_US        500000          /* 500ms */

/**
 * @brief Maximum allowed drift correction rate (ppb)
 *
 * Caps the frequency slewing to prevent instability.
 * 100,000 ppb = 100 ppm = 0.01% max clock speed adjustment
 */
#define UTLP_SERVO_MAX_DRIFT_PPB         100000          /* ±100 ppm max */

/**
 * @brief Minimum phase error to trigger slewing (microseconds)
 *
 * Errors smaller than this are considered noise and ignored.
 * Prevents oscillation around the setpoint.
 */
#define UTLP_SERVO_DEADBAND_US           100             /* 100μs deadband */

/**
 * @brief Time after boot when phase jumps are allowed (microseconds)
 *
 * During "Cold Start" phase, we allow instant phase jumps for fast initial sync.
 * After this time, all corrections use Variable Gain PLL slewing.
 *
 * Part of Variable Gain PLL (Claim 55 compliance):
 *   - Cold Start (< 5s): Hard jumps allowed ("snap to grid")
 *   - Locked (error < 10ms): Slow slew at 200 ppm
 *   - Recovery (error > 10ms): Fast slew at 5000 ppm
 */
#define UTLP_SERVO_COLD_START_US         5000000ULL      /* 5 seconds */

/**
 * @brief Error threshold between Locked and Recovery states (microseconds)
 *
 * Variable Gain PLL state selection:
 *   - Error < threshold: LOCKED state (gentle slew)
 *   - Error >= threshold: RECOVERY state (fast catch-up)
 */
#define UTLP_SERVO_LOCKED_THRESHOLD_US   10000           /* 10ms */

/**
 * @brief Maximum slew rate in LOCKED state (ppb)
 *
 * Gentle nudge for small errors. Maintains spectral purity.
 * 200 ppm = 200,000 ppb = 0.02% clock speed adjustment
 */
#define UTLP_SERVO_MAX_SLEW_PPB_LOCKED   200000          /* 200 ppm */

/**
 * @brief Maximum slew rate in RECOVERY state (ppb)
 *
 * Fast catch-up for large errors without hard jumping.
 * 5000 ppm = 5,000,000 ppb = 0.5% clock speed adjustment
 */
#define UTLP_SERVO_MAX_SLEW_PPB_RECOVERY 5000000         /* 5000 ppm */

/**
 * @brief [DEPRECATED] Legacy constant - use UTLP_SERVO_COLD_START_US
 */
#define UTLP_SERVO_JUMP_ALLOWED_UNTIL_US UTLP_SERVO_COLD_START_US

/**
 * @brief Servo-lock update tick interval (microseconds)
 *
 * How often the servo loop runs to apply drift corrections.
 * 10ms = 100Hz, providing smooth frequency adjustment.
 */
#define UTLP_SERVO_TICK_INTERVAL_US      10000           /* 10ms */

/** @} */ /* servo_lock */

/*============================================================================
 * GENESIS RESET DETECTION (S2 Section 2.4)
 *
 * Detect when a genesis node resets during testing/operation.
 * A reset genesis will:
 * 1. Start broadcasting at genesis intervals (100ms, 500ms, 1s)
 * 2. Have atomic time that is "newer" than expected (epoch jump forward)
 * 3. Potentially disrupt timing of other nodes
 *
 * Detection strategies:
 * - Beacon interval sudden drop to genesis rates
 * - Atomic time jump forward beyond expected drift
 * - Sequence number reset (if using seqno)
 *==========================================================================*/

/** @defgroup genesis_reset Genesis Reset Detection
 * @{
 */

/**
 * @brief Maximum forward time jump to accept without reset detection (μs)
 *
 * If a peer's atomic time jumps forward by more than this amount,
 * they have likely rebooted with a newer epoch. We should NOT adopt
 * their time, but we can still entrain to their phase after verification.
 *
 * 1 second allows for legitimate network delays and jitter.
 */
#define UTLP_MAX_FORWARD_JUMP_US         1000000         /* 1 second */

/**
 * @brief Time window to monitor for genesis interval patterns (μs)
 *
 * Track beacon intervals over this window to detect genesis pulse patterns.
 */
#define UTLP_GENESIS_DETECT_WINDOW_US    5000000         /* 5 seconds */

/**
 * @brief Minimum observations to confirm genesis reset detection
 *
 * Require multiple rapid beacons before declaring "genesis reset detected".
 */
#define UTLP_GENESIS_RESET_MIN_BEACONS   3

/** @} */ /* genesis_reset */

/*============================================================================
 * COHERENCE THRESHOLDS
 *
 * Define what "in sync" means for phase agreement.
 *==========================================================================*/

/** @defgroup coherence Coherence Thresholds
 * @{
 */

/**
 * @brief Phase agreement threshold for "in sync" (microseconds)
 *
 * Two nodes are considered phase-coherent if their phase error is
 * within this threshold. 2ms is standard for UTLP.
 */
#define UTLP_COHERENCE_THRESHOLD_US      2000            /* 2ms */

/**
 * @brief Phase agreement threshold for entrainment quorum (microseconds)
 *
 * When deciding whether to send an entrainment pulse, we check if
 * enough healthy peers agree with our time within this threshold.
 */
#define UTLP_QUORUM_THRESHOLD_US         2000            /* 2ms */

/**
 * @brief Minimum coherence percentage for "healthy swarm" (0-100)
 *
 * If fewer than this percentage of healthy peers are in phase agreement,
 * the swarm is considered fragmented.
 */
#define UTLP_COHERENCE_MIN_PCT           80              /* 80% */

/** @} */ /* coherence */

/*============================================================================
 * SEISMIC CHIRP - Time-Domain Interferometry
 *
 * Every beacon is a 3-burst "seismic chirp". This enables extraction of:
 *   - Burst 0 (t₀): Offset (position) - 0th derivative
 *   - Burst 1 (t₁): Drift (velocity) - 1st derivative
 *   - Burst 2 (t₂): Stability (acceleration) - 2nd derivative
 *==========================================================================*/

/** @defgroup chirp Seismic Chirp Configuration
 * @{
 */

/** @brief Number of bursts in a seismic chirp */
#define UTLP_CHIRP_BURST_COUNT           3

/** @brief Spacing between chirp bursts (microseconds) */
#define UTLP_CHIRP_BURST_SPACING_US      2000            /* 2ms */

/** @} */ /* chirp */

/*============================================================================
 * NEIGHBORHOOD - Peer Tracking and Frontier Detection
 *==========================================================================*/

/** @defgroup neighborhood Neighborhood Configuration
 * @{
 */

/** @brief Maximum neighbors to track */
#define UTLP_MAX_NEIGHBORS               16

/** @brief Relay threshold - score above this = Provider (relay time to others) */
#define UTLP_RELAY_THRESHOLD             128

/** @brief RSSI threshold for excellent signal (interior node) */
#define UTLP_RSSI_EXCELLENT              (-50)

/** @brief RSSI threshold for weak signal (edge/frontier node) */
#define UTLP_RSSI_FRONTIER               (-70)

/** @brief Neighbor timeout (microseconds) */
#define UTLP_NEIGHBOR_TIMEOUT_US         5000000ULL      /* 5 seconds */

/** @} */ /* neighborhood */

/*============================================================================
 * STRATUM LEVELS (NTP-style, biological terminology)
 *==========================================================================*/

/** @defgroup stratum Stratum Levels
 * @{
 */

/** @brief External GPS/atomic reference */
#define UTLP_STRATUM_GPS                 0

/** @brief Self-declared time source (genesis node) */
#define UTLP_STRATUM_ORIGIN              1

/** @brief Synced to another node */
#define UTLP_STRATUM_SYNCED              2

/** @} */ /* stratum */

/*============================================================================
 * APPLICATION LAYER
 *==========================================================================*/

/** @defgroup app_config Application Configuration
 * @{
 */

/** @brief LED blink period (1Hz = 1 second cycle) */
#define UTLP_BLINK_PERIOD_US             1000000         /* 1 second */

/** @} */ /* app_config */

/*============================================================================
 * STATISTICS AND LOGGING
 *==========================================================================*/

/** @defgroup stats Statistics Configuration
 * @{
 */

/** @brief Stats logging interval during genesis (first 10s) */
#define UTLP_STATS_LOG_FAST_US           1000000ULL      /* 1 second */

/** @brief Stats logging interval after genesis */
#define UTLP_STATS_LOG_SLOW_US           30000000ULL     /* 30 seconds */

/** @brief Time threshold for switching to slow logging */
#define UTLP_STATS_FAST_END_US           10000000ULL     /* 10 seconds */

/** @brief Exponential moving average alpha (0.1 = 10% new, 90% old) */
#define UTLP_EMA_ALPHA                   0.1

/** @} */ /* stats */

#ifdef __cplusplus
}
#endif
