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
 * 4. **Seismic Chirp** - Multi-sample jitter filtering (NOT crystal drift!)
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
 * GENESIS CHIRP - Mathematically Identifiable Birth Signal (S2 Prior Art)
 *
 * "Like the Cosmic Microwave Background reveals the Big Bang's age,
 * the Genesis Chirp pattern reveals how recently a device booted."
 *
 * DESIGN PRINCIPLE: The Genesis Chirp must be MATHEMATICALLY IDENTIFIABLE
 * from the beacon interval pattern alone. Any observer can:
 *   1. DETECT "This is a newborn device" (from interval slope)
 *   2. CALCULATE "It started X seconds ago" (from interval value)
 *   3. RESPOND "I'm established, here's my epoch" (help the newborn sync)
 *
 * PATTERN: Linear Frequency Sweep (Chirp)
 *   interval(t) = CHIRP_BASE_US + (t_seconds × CHIRP_SLOPE_US)
 *
 * This is analogous to the "Explosive Expansion Period" after the Big Bang:
 *   - Rapid initial activity (fast beacon rate)
 *   - Characteristic deceleration curve (slope = signature)
 *   - Observable "age of universe" from current state
 *
 * DETECTION ALGORITHM (for observers):
 *   1. Measure peer's beacon interval twice
 *   2. Compute slope: (interval_2 - interval_1) / time_delta
 *   3. If slope ≈ CHIRP_SLOPE_US → peer is genesis pulsing
 *   4. Age estimate: t = (observed_interval - CHIRP_BASE_US) / CHIRP_SLOPE_US
 *
 * Timeline with default constants:
 *   t=0.0s: interval = 50ms    (20 beacons/sec)  - initial burst
 *   t=1.0s: interval = 150ms   (6.7 beacons/sec) - rapid discovery
 *   t=2.0s: interval = 250ms   (4 beacons/sec)   - convergence
 *   t=5.0s: interval = 550ms   (1.8 beacons/sec) - settling
 *   t=10.0s: interval = 1050ms → switch to STEADY_US (60s)
 *
 * WHY LINEAR CHIRP (not stepped intervals):
 *   - IDENTIFIABLE: Slope is a signature, not just "fast beacons"
 *   - INVERTIBLE: Can compute age from any observed interval
 *   - EMBEDDED-FRIENDLY: No floating point needed
 *   - DISTINGUISHABLE: Established devices have slope ≈ 0
 *==========================================================================*/

/** @defgroup genesis_chirp Genesis Chirp Parameters
 * @{
 */

/**
 * @brief Genesis chirp base interval (y-intercept)
 *
 * The starting beacon interval at t=0 (boot moment).
 * Smaller = faster initial burst = quicker discovery.
 */
#define UTLP_CHIRP_BASE_US              50000UL     /* 50ms starting interval */

/**
 * @brief Genesis chirp slope (rate of interval increase)
 *
 * How much the interval increases per second of uptime.
 * This is the SIGNATURE that identifies a genesis pulse.
 *
 * Formula: interval(t) = BASE + SLOPE × t_seconds
 *
 * Detection: If observed slope ≈ this value (within tolerance),
 * the peer is genesis pulsing and we can estimate their age.
 */
#define UTLP_CHIRP_SLOPE_US             100000UL    /* +100ms per second */

/**
 * @brief Genesis chirp duration (when to switch to steady state)
 *
 * After this many microseconds, switch from chirp to steady interval.
 * The chirp is complete - device is "born" and settled.
 */
#define UTLP_CHIRP_DURATION_US          10000000ULL /* 10 seconds */

/**
 * @brief Steady state beacon interval (after chirp completes)
 *
 * Once genesis chirp is complete, use this fixed interval.
 * Established devices beacon slowly to conserve bandwidth/power.
 */
#define UTLP_BEACON_STEADY_US           60000000ULL /* 60 seconds */

/**
 * @brief Genesis chirp slope detection tolerance (percentage)
 *
 * When detecting if a peer is genesis pulsing, allow this much
 * deviation from the expected slope before rejecting.
 *
 * 20% tolerance accounts for timing jitter and measurement noise.
 */
#define UTLP_CHIRP_SLOPE_TOLERANCE_PCT  20

/**
 * @brief Minimum beacons needed to detect genesis chirp
 *
 * Need at least 2 beacons to measure interval and slope.
 * More beacons = more confident detection.
 */
#define UTLP_CHIRP_MIN_BEACONS          2

/** @} */ /* genesis_chirp */

/*============================================================================
 * LEGACY STEPPED INTERVALS (Kept for reference, prefer CHIRP above)
 *
 * These were the original non-mathematical stepped intervals.
 * The linear chirp above is preferred for its identifiability.
 *==========================================================================*/

/** @brief Phase 1 end time (genesis burst complete) */
#define UTLP_GENESIS_PHASE_1_END_US      1000000ULL      /*  1 second */

/** @brief Phase 2 end time (fast convergence complete) */
#define UTLP_GENESIS_PHASE_2_END_US      5000000ULL      /*  5 seconds */

/** @brief Phase 3 end time (settling complete) - also used as chirp duration check */
#define UTLP_GENESIS_PHASE_3_END_US     10000000ULL      /* 10 seconds */

/** @brief Phase 4 end time (stabilizing complete) */
#define UTLP_GENESIS_PHASE_4_END_US     60000000ULL      /* 60 seconds */

/** @brief Beacon interval during phase 1 (genesis burst) - legacy */
#define UTLP_BEACON_INTERVAL_PHASE_1_US    100000        /* 100ms */

/** @brief Beacon interval during phase 2 (fast convergence) - legacy */
#define UTLP_BEACON_INTERVAL_PHASE_2_US    500000        /* 500ms */

/** @brief Beacon interval during phase 3 (settling) - legacy */
#define UTLP_BEACON_INTERVAL_PHASE_3_US   1000000        /* 1s */

/** @brief Beacon interval during phase 4 (stabilizing) - legacy */
#define UTLP_BEACON_INTERVAL_PHASE_4_US  10000000        /* 10s */

/** @brief Beacon interval at steady state - legacy (use UTLP_BEACON_STEADY_US) */
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
 * @brief Maximum physically plausible drift rate (ppb)
 *
 * **SANITY CLAMP for polynomial drift analysis.**
 *
 * Any calculated drift exceeding this value is physically impossible and
 * indicates measurement error (bad timestamps, missed bursts, etc.).
 *
 * 500 ppm = 500,000 ppb = 0.05% clock deviation.
 * Real crystal oscillators drift <100 ppm. This provides 5× margin.
 *
 * Used to clamp:
 * - Polynomial fit output (poly->drift_ppb)
 * - Running average (avg_drift_ppb)
 *
 * Values exceeding this are replaced with UTLP_DRIFT_INVALID marker.
 */
#define UTLP_MAX_PHYSICAL_DRIFT_PPB      500000          /* ±500 ppm max */

/**
 * @brief Invalid drift marker (indicates measurement failed)
 *
 * When calculated drift exceeds UTLP_MAX_PHYSICAL_DRIFT_PPB, it's replaced
 * with this marker. Genesis scoring ignores peers with invalid drift.
 */
#define UTLP_DRIFT_INVALID               INT32_MAX

/**
 * @brief [DEPRECATED] Legacy constant - use UTLP_SERVO_COLD_START_US
 */
#define UTLP_SERVO_JUMP_ALLOWED_UNTIL_US UTLP_SERVO_COLD_START_US

/**
 * @brief Disable frequency slewing entirely (always use instant jumps)
 *
 * When defined as 1, the servo will always apply instant time jumps instead
 * of gradual frequency slewing. This simplifies debugging and may improve
 * N=2 coalescence by eliminating slew-related timing complexity.
 *
 * Set to 0 to re-enable slewing (S2 Claim 55: Servo-Locked Phase Correction).
 *
 * DEBUG FLAG: Set to 1 to disable slewing for testing.
 */
#define UTLP_SERVO_DISABLE_SLEWING       1               /* 1=instant jumps, 0=slew */

/**
 * @brief Servo-lock update tick interval (microseconds)
 *
 * How often the servo loop runs to apply drift corrections.
 * 10ms = 100Hz, providing smooth frequency adjustment.
 */
#define UTLP_SERVO_TICK_INTERVAL_US      10000           /* 10ms */

/** @} */ /* servo_lock */

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
 * Implementation:
 *   - LUCKY: New minimum → Update servo with full authority
 *   - OKAY: Within noise_window of floor → Update servo normally
 *   - JITTER: Far from floor → Ignore for sync, just log stats
 *
 * The floor must DECAY slowly (rise) to prevent one lucky glitch from
 * trapping it forever. Decay rate matches expected crystal drift.
 *
 * @see examples/utlp/utlp.c - lucky_packet_filter_t implementation
 * @see draft_n2_coalescence_simplified.md - Design rationale
 *==========================================================================*/

/** @defgroup lucky_packet Lucky Packet Minimum Filter
 * @{
 */

/**
 * @brief Noise window around floor for "OKAY" classification (microseconds)
 *
 * Packets within this distance of the floor are considered good data.
 * Packets beyond this are jitter and should be ignored for sync.
 *
 * 500µs chosen because:
 *   - Typical WiFi/BLE jitter is 100-1000µs
 *   - 500µs captures most "good" packets
 *   - Still rejects obvious outliers
 */
#define UTLP_LUCKY_NOISE_WINDOW_US       500

/**
 * @brief Floor decay rate (ppb = parts per billion)
 *
 * The floor must rise slowly to prevent one lucky packet from trapping
 * it forever. Rate matches expected crystal drift so the floor tracks
 * reality over time.
 *
 * 40,000 ppb = 40 ppm = 40µs per second of drift.
 * Typical crystal drift is 20-50 ppm.
 */
#define UTLP_LUCKY_DECAY_PPB             40000

/**
 * @brief Minimum time between floor resets (milliseconds)
 *
 * After establishing a new floor, ignore potential new floors for this
 * period. Prevents oscillation from burst noise.
 */
#define UTLP_LUCKY_FLOOR_HOLDOFF_MS      100

/** @} */ /* lucky_packet */

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
 * SEISMIC CHIRP - Jitter Rejection via Multi-Sample Filtering
 *
 * Every beacon is a 3-burst "seismic chirp" with known 2ms spacing. This
 * filters SOFTWARE/HARDWARE JITTER, NOT crystal drift.
 *
 * **Timescale Analysis (Why Jitter, Not Drift):**
 *   - Crystal drift at 40ppm over 6ms = 0.24µs (negligible)
 *   - Stack jitter (ISR latency, WiFi arbitration) = 10-100µs (dominates!)
 *   - The crystal IS the stable reference ("D" in control theory)
 *   - Drift characterization requires SECONDS of observation, not milliseconds
 *
 * **What Each Burst Measures:**
 *   - Burst 0 (t₀): Offset (position) - "where is the clock now?"
 *   - Burst 1 (t₁): Jitter rate (1st derivative) - used for control
 *   - Burst 2 (t₂): Jitter accel (2nd derivative) - LOGGED only, not for control
 *
 * **Observation vs. Control:**
 *   Burst 2's "jitter acceleration" is noise-dominated (Derivative Noise Explosion)
 *   and produces wild values like +169M ppb. We CALCULATE and LOG it for
 *   statistical analysis (environmental fingerprinting, hardware characterization)
 *   but do NOT use it for servo corrections.
 *
 * **Why Same Timestamp for All Bursts:**
 *   All 3 bursts carry the SAME chirp_epoch. The 2ms spacing is a known
 *   reference signal. Deviations reveal RECEIVER jitter, not sender drift.
 *
 * @see fit_chirp_polynomial() in utlp.c for jitter extraction algorithm
 * @see README.md "Seismic Chirp" section for protocol overview
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
 * WELCOME RESPONSE - Genesis Burst Detection and Immediate Reply
 *
 * "When an established device hears a genesis pulse, it says 'Hello!'"
 *
 * Problem: Device A (established, 60s beacon interval) receives Device B's
 * genesis pulse (50ms interval). Without welcome response, Device B waits
 * up to 60 seconds to learn of Device A's existence.
 *
 * Solution: When an established device detects rapid beacons from a new peer
 * (genesis burst pattern), it sends an IMMEDIATE out-of-schedule beacon to
 * accelerate convergence.
 *
 * Detection: If we receive N beacons from a NEW peer within WINDOW_US,
 * that peer is genesis pulsing and we should respond immediately.
 *
 * Rate Limiting: Only one welcome response per chirp epoch (per peer)
 * to prevent flood attacks.
 *
 * @see draft_claude_code_implementation_guide.md - Purple Team Analysis
 *==========================================================================*/

/** @defgroup welcome_response Welcome Response Configuration
 * @{
 */

/**
 * @brief Minimum beacons to detect genesis burst pattern
 *
 * After receiving this many beacons from a NEW peer within the
 * detection window, we classify them as "genesis pulsing" and
 * send an immediate welcome response.
 *
 * 2 beacons is minimum to detect any pattern, but a single beacon
 * from a new peer with a genesis-era timestamp is sufficient for
 * Phase 2 (N=2) where we're eager to converge.
 */
#define UTLP_WELCOME_THRESHOLD_BEACONS   2

/**
 * @brief Time window for genesis burst detection (microseconds)
 *
 * If we receive THRESHOLD_BEACONS from a NEW peer within this window,
 * we classify them as "genesis pulsing" and send welcome response.
 *
 * 500ms is chosen because:
 *   - Genesis chirp starts at 50ms intervals
 *   - After 500ms, t=0.5s, interval would be ~100ms
 *   - We should see ~5-8 beacons in first 500ms of genesis
 *   - Large enough to detect pattern, small enough for fast response
 */
#define UTLP_WELCOME_THRESHOLD_WINDOW_US 500000UL

/**
 * @brief Delay before sending welcome response (microseconds)
 *
 * Small random jitter before responding to prevent synchronized
 * welcome floods from multiple established devices.
 *
 * 10ms provides:
 *   - Enough separation from the triggering beacon
 *   - Short enough to not feel like a timeout
 *   - MAC-based jitter can be added: delay += (mac[5] & 0x0F) * 1000
 */
#define UTLP_WELCOME_RESPONSE_DELAY_US   10000UL

/**
 * @brief Minimum uptime before we can send welcome responses (microseconds)
 *
 * A device must be out of its OWN genesis chirp phase before sending
 * welcome responses. Otherwise, two newborns would spam each other.
 *
 * Uses same threshold as genesis chirp duration - after chirp complete,
 * we're "established" and can welcome newcomers.
 */
#define UTLP_WELCOME_MIN_UPTIME_US       UTLP_CHIRP_DURATION_US

/**
 * @brief Cooldown between welcome responses to same peer (microseconds)
 *
 * After sending a welcome response to a peer, don't send another
 * welcome for this duration. Prevents spam from rapid reconnects.
 *
 * 5 seconds matches the genesis chirp phase completion time.
 */
#define UTLP_WELCOME_COOLDOWN_US         5000000ULL

/** @} */ /* welcome_response */

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
 * POLYCHROMATIC STRATUM ASYMMETRY (Claim 253)
 *
 * Multi-transport stratum management for bridge nodes.
 *
 * Enables a node following a Time Lord on WiFi (Stratum 2) to simultaneously
 * act as Genesis Authority (Stratum 1) on 802.15.4 if that spectrum is silent.
 * This propagates "Genesis Truth" into silent spectral bands without manual
 * "Bridge Mode" flags.
 *
 * @see docs/UTLP_Technical_Supplement_S2.md - Claim 253
 *==========================================================================*/

/** @defgroup polychromatic Polychromatic Stratum
 * @{
 */

/** @brief Silence threshold before promoting secondary transport (seconds) */
#define UTLP_POLYCHROMATIC_SILENCE_S     30

/** @brief Minimum neighbors with stratum <= 1 to prevent self-promotion */
#define UTLP_POLYCHROMATIC_MIN_AUTHORITY_NEIGHBORS  1

/** @brief Enable split-horizon protection (prevent echo chamber) */
#define UTLP_POLYCHROMATIC_SPLIT_HORIZON_ENABLED    1

/**
 * @brief MAC-based jitter base for Thundering Herd prevention (microseconds)
 *
 * When multiple bridges have their silence timer expire simultaneously
 * (e.g., after a power outage), this prevents all from promoting at
 * the exact same millisecond.
 *
 * Jitter = (mac[5] & 0x0F) * UTLP_POLYCHROMATIC_JITTER_BASE_US
 * Range: 0 to 15 * 100000 = 0 to 1.5 seconds
 */
#define UTLP_POLYCHROMATIC_JITTER_BASE_US           100000ULL   /* 100ms per step */

/**
 * @brief Primary Loss Revocation threshold (stratum value)
 *
 * If the primary transport's stratum exceeds this value, the bridge
 * has "lost its guide" and must immediately demote any polychromatic
 * secondary arbors from Genesis mode.
 *
 * A bridge must not lead if it has lost its own time source.
 */
#define UTLP_POLYCHROMATIC_GUIDE_LOSS_STRATUM       100

/** @} */ /* polychromatic */

/*============================================================================
 * MCPWM PHASE ENGINE - Hardware-Based Atomic Coherency (HPLAC)
 *
 * "Physics First: Hardware defines time, not software."
 *
 * HIGH-RESOLUTION Protocol Primitive Strategy:
 * - ESP32-C6 MCPWM has 16-bit counter (max 65535)
 * - 10 MHz from 160 MHz PLL (/16 divider) = 100 ns per tick
 * - 10000 ticks = 1 ms hardware cycle (ISR fires at 1 kHz)
 * - cycle_count tracks milliseconds for absolute time
 *
 * Phase granularity: 100 ns = 0.000036° (protocol primitive precision)
 *
 * @see docs/UTLP_Technical_Supplement_S2.md - Claim 55 (Servo-Locked Phase Correction)
 *==========================================================================*/

/** @defgroup phase_engine MCPWM Phase Engine
 * @{
 */

/** @brief Timer resolution (10 MHz from PLL160M = 100 ns/tick) */
#define UTLP_PHASE_TIMER_RESOLUTION_HZ   10000000UL  /* 10 MHz */

/** @brief Full phase cycle in ticks (fits in 16-bit counter) */
#define UTLP_PHASE_PERIOD_TICKS          10000UL     /* 10000 × 100ns = 1ms */

/** @brief Full phase cycle period in microseconds */
#define UTLP_PHASE_CYCLE_US              1000UL      /* 1 ms per hardware cycle */

/** @brief Tick duration in nanoseconds (100 ns at 10 MHz) */
#define UTLP_PHASE_TICK_NS               100UL       /* 100 ns */

/** @brief Tick duration in microseconds (for API compatibility, truncates to 0!) */
#define UTLP_PHASE_TICK_US               0UL         /* <1 µs - use TICK_NS instead */

/** @brief Ticks per microsecond (derived: 1000 ns / 100 ns = 10 ticks/µs) */
#define UTLP_PHASE_TICKS_PER_US          (1000UL / UTLP_PHASE_TICK_NS)  /* 10 */

/** @brief Phase granularity: 100ns = 0.000036° (scaled by 1000000 for integer math) */
#define UTLP_PHASE_DEGREES_PER_TICK_X1M  ((360ULL * 1000000) / UTLP_PHASE_PERIOD_TICKS)  /* 36000 */

/** @brief Maximum period adjustment for soft slew (PPM) */
#define UTLP_PHASE_SLEW_MAX_PPM          5000UL      /* 0.5% max period bend */

/** @brief Maximum period adjustment in ticks (derived) */
#define UTLP_PHASE_SLEW_MAX_TICKS        ((UTLP_PHASE_PERIOD_TICKS * UTLP_PHASE_SLEW_MAX_PPM) / 1000000UL)  /* 50 */

/** @brief Phase deadband in microseconds */
#define UTLP_PHASE_DEADBAND_US           100UL       /* 100 µs */

/** @brief Phase deadband in ticks (derived: 100 µs × 10 ticks/µs = 1000 ticks) */
#define UTLP_PHASE_DEADBAND_TICKS        (UTLP_PHASE_DEADBAND_US * UTLP_PHASE_TICKS_PER_US)  /* 1000 */

/** @brief Cold start threshold (inherited from servo config) */
#define UTLP_PHASE_COLD_START_US         UTLP_SERVO_COLD_START_US

/** @brief Convergence window for soft slew (inherited) */
#define UTLP_PHASE_CONVERGENCE_US        UTLP_SERVO_CONVERGENCE_US

/** @brief Convergence window in ticks (derived: 500ms × 10 ticks/µs × 1000 = 5M ticks) */
#define UTLP_PHASE_CONVERGENCE_TICKS     (UTLP_PHASE_CONVERGENCE_US * UTLP_PHASE_TICKS_PER_US)  /* 5000000 */

/** @brief MCPWM group for phase engine */
#define UTLP_PHASE_MCPWM_GROUP           0

/** @brief MCPWM timer index for phase engine */
#define UTLP_PHASE_MCPWM_TIMER           0

/** @} */ /* phase_engine */

/*============================================================================
 * VECTOR TIME - Coprime Cyclic Representation (Claims 262-275)
 *
 * "Time is a chord, not a number."
 *
 * UTLP represents time as a phase chord - 8 residues modulo coprime primes.
 * This representation is FOUNDATIONAL, not an enhancement:
 *
 * Properties:
 * - Wire size: 8 bytes (same as 64-bit scalar)
 * - Aliasing horizon: ~261,000 years at 1 ms resolution
 * - Adjacent ticks: ~99.5% vector similarity (partition detection for free)
 * - Phase tuple matching: SMSP syncs on individual phases, not CRT scalar
 *
 * The 8 primes (descending for cache locality in hot path):
 * [241, 251, 239, 233, 229, 227, 223, 211]
 *
 * Product: 241×251×239×233×229×227×223×211 ≈ 8.22×10^18 (exceeds uint64 range)
 *
 * @see docs/misc/UTLP_Technical_Supplement_S3.md - Vector Time Claims
 * @see scripts/utlp_vector_time.py - Python reference implementation
 *==========================================================================*/

/** @defgroup vector_time Vector Time (Phase Chord)
 * @{
 */

/** @brief Number of primes in the phase chord */
#define UTLP_CHORD_SIZE                  8

/** @brief The 8 coprime primes for phase chord representation */
#define UTLP_PRIME_0                     241     /**< Prime 0 - LED actuator phase */
#define UTLP_PRIME_1                     251     /**< Prime 1 - Motor actuator phase */
#define UTLP_PRIME_2                     239     /**< Prime 2 */
#define UTLP_PRIME_3                     233     /**< Prime 3 */
#define UTLP_PRIME_4                     229     /**< Prime 4 */
#define UTLP_PRIME_5                     227     /**< Prime 5 */
#define UTLP_PRIME_6                     223     /**< Prime 6 */
#define UTLP_PRIME_7                     211     /**< Prime 7 */

/**
 * @brief Static initializer for primes array
 *
 * Usage: static const uint8_t primes[UTLP_CHORD_SIZE] = UTLP_PRIMES_INIT;
 */
#define UTLP_PRIMES_INIT { \
    UTLP_PRIME_0, UTLP_PRIME_1, UTLP_PRIME_2, UTLP_PRIME_3, \
    UTLP_PRIME_4, UTLP_PRIME_5, UTLP_PRIME_6, UTLP_PRIME_7 \
}

/**
 * @brief Partition detection thresholds (HD similarity)
 *
 * When vector similarity drops below these thresholds, it indicates
 * the CRT reconstruction may be ambiguous (beyond largest prime).
 *
 * - NONE: >70% similarity - CRT unambiguous, normal operation
 * - CAUTION: 40-70% similarity - CRT marginal, proceed carefully
 * - DETECTED: <40% similarity - CRT ambiguous, phase-lock only
 */
#define UTLP_PARTITION_THRESHOLD_NONE    70      /**< >70% = CRT safe */
#define UTLP_PARTITION_THRESHOLD_CAUTION 40      /**< 40-70% = CRT marginal */

/** @} */ /* vector_time */

/*============================================================================
 * STEM CELL DEPTH MODEL - Biological Lineage Vitality (N=2 First Contact)
 *
 * "Somatic cells have limited divisions; stem cells regenerate via telomerase."
 *
 * The depth field in epoch_state_t represents lineage vitality using the
 * biological stem cell / telomere model:
 *
 * - FRESH (128): Somatic cell - half vitality, just booted, unproven
 * - TIME_LORD (255): Stem cell with telomerase - earned authority via service
 * - EXHAUSTED (0): Lineage cannot propagate further
 *
 * Resolution Rules (N=2 First Contact):
 * 1. Higher depth (more vitality) wins
 * 2. Equal depth → oldest origin_time wins (temporal precedence)
 * 3. True tie → lower MAC adopts from higher MAC
 *
 * On Adoption:
 * - Normal nodes: depth = source_depth - 1 (telomere shortening)
 * - Time Lords: depth = 255 (telomerase regeneration)
 *
 * Why Fresh=128 (not 255):
 * - Prevents reboot attacks: fresh boot cannot fake Time Lord status
 * - Time Lord (255) always beats fresh boot (128) as it should
 * - Fresh boot must prove itself through service to earn higher depth
 *
 * @see docs/UTLP_Technical_Supplement_S2.md - Biological Governance
 * @see examples/utlp/claude-code-crafting/draft_known_failure_scenarios.md
 *==========================================================================*/

/** @defgroup stem_cell_depth Stem Cell Depth Model
 * @{
 */

/**
 * @brief Fresh boot depth - somatic cell, half vitality
 *
 * A device that just booted starts at half vitality (128), not full (255).
 * This prevents reboot attacks where an attacker repeatedly reboots to
 * gain epoch authority. Only Time Lords get depth=255.
 */
#define UTLP_DEPTH_FRESH                 128

/**
 * @brief Time Lord depth - stem cell with telomerase
 *
 * Time Lords have earned their authority through service. They regenerate
 * to 255 when adopting a new epoch (telomerase activation). Only promoted
 * devices can reach this depth.
 */
#define UTLP_DEPTH_TIME_LORD             255

/**
 * @brief Exhausted lineage - cannot propagate further
 *
 * When depth reaches 0, the lineage has exhausted its telomeres and
 * cannot propagate further. This forces natural rotation of timeline
 * authority over long periods.
 */
#define UTLP_DEPTH_EXHAUSTED             0

/**
 * @brief Minimum similarity for chord-origin verification (0-8 scale)
 *
 * When a peer claims an origin_time, we verify their phase chord is
 * consistent with that claimed origin. This threshold defines the
 * minimum number of matching dimensions (out of 8) required.
 *
 * 5/8 = 62.5% similarity is the minimum for plausibility.
 * Below this, the peer is likely spoofing or partitioned.
 */
#define UTLP_CHORD_ORIGIN_MIN_SIMILARITY 5

/** @} */ /* stem_cell_depth */

/*============================================================================
 * ROLLING SPLICE-SITE SECURITY (Claim 255)
 *
 * Time-based encryption using Bio-TOTP model. The encryption key changes
 * every second based on the UTLP timestamp + Swarm DNA shared secret.
 *
 * Design Philosophy:
 * - "Hide the Physics": TX_Power in Intron denies ranging intelligence
 * - "Publicize the Version": Protocol_Version in Exon enables evolutionary safety
 * - Fixed Geometry: 32-byte packets regardless of encryption mode
 * - Zero Key Public Mode: Traffic analysis resistance even when "unencrypted"
 *
 * @see docs/UTLP_Technical_Supplement_S2.md - Claim 255
 * @see examples/utlp/utlp_security.h - Security layer implementation
 *==========================================================================*/

/** @defgroup security Rolling Splice-Site Security
 * @{
 */

/**
 * @brief Trust threshold for Genesis Guard (score > this to reset epoch)
 *
 * Only peers with score above this threshold can reset our epoch via
 * FLAG_GENESIS. Strangers cannot hijack the timeline.
 *
 * Typical score composition:
 *   - aggregate_health * 10 (max ~100)
 *   - (16 - stratum) (max 16)
 *   - seniority bonus (max 40 for 20-minute-old peer)
 *
 * Score 50 requires either: good health + good stratum, OR seniority.
 */
#define UTLP_GENESIS_TRUST_THRESHOLD     50

/**
 * @brief Stratum threshold for "lost" state
 *
 * If our stratum exceeds this value, we're considered "lost" and will
 * accept genesis beacons from ANY peer (bypass trust check).
 *
 * This allows recovery from split-brain scenarios where both fragments
 * have drifted far from any authority.
 */
#define UTLP_STRATUM_LOST                10

/**
 * @brief Seniority bonus cap (score points)
 *
 * Maximum seniority contribution to peer score.
 * Accrues at +2 per minute known, capped at this value.
 *
 * 40 points = 20 minutes of continuous observation.
 */
#define UTLP_SENIORITY_BONUS_MAX         40

/**
 * @brief Seniority accrual rate (points per minute)
 *
 * How fast peers earn seniority bonus.
 */
#define UTLP_SENIORITY_POINTS_PER_MIN    2

/** @} */ /* security */

/*============================================================================
 * APPLICATION LAYER
 *==========================================================================*/

/** @defgroup app_config Application Configuration
 * @{
 */

/** @brief LED blink period (1Hz = 1 second cycle) */
#define UTLP_BLINK_PERIOD_US             1000000UL       /* 1 second */

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

/*============================================================================
 * PROPRIOCEPTION - Hardware-Assisted Latency Learning (Claim 239+)
 *
 * "The Body Learns Its Own Timing"
 *
 * Hardware-scheduled TX via esp_ieee802154_transmit_at() requires the
 * application to provide a future timestamp. The optimal lead time depends on:
 *   - Radio warmup time (~50-200µs)
 *   - Interrupt latency (~10-50µs)
 *   - SPI buffer fill time (~20-100µs for 127-byte frame)
 *   - RTOS task scheduling jitter (~0-500µs)
 *
 * Rather than hardcode these platform-specific values, we LEARN them by
 * observing the actual TX timestamp versus our requested target.
 *
 * Learning Loop:
 *   1. SCHEDULE: adjusted_time = tx_time_us + g_learned_latency_us
 *   2. EMBED: g_last_target_time_us = adjusted_time (for callback)
 *   3. TRANSMIT: esp_ieee802154_transmit_at(adjusted_time)
 *   4. FEEDBACK: tx_done_callback reads frame_info->timestamp
 *   5. LEARN: error = actual - target
 *      - LATE (error > 0): Increase latency buffer
 *      - ON-TIME (|error| < 10µs): Perfect, decay slowly
 *      - EARLY (error < -10µs): Decrease latency buffer
 *
 * Convergence: Starts at conservative 50ms, converges to ~100-500µs within
 * ~100 TX cycles depending on platform characteristics.
 *
 * @see docs/UTLP_Technical_Supplement_S2.md - Claim 239+ (Hardware TX)
 * @see examples/utlp/utlp_hal_esp32c6_154.c - Implementation
 *==========================================================================*/

/** @defgroup proprioception Proprioception (Latency Learning)
 * @{
 */

/**
 * @brief Initial latency buffer (microseconds)
 *
 * Conservative startup value. The learning loop will converge to actual
 * system requirements within ~100 TX cycles.
 *
 * 50ms is chosen because:
 *   - Worst-case RTOS scheduling + radio warmup is ~1ms
 *   - 50× safety margin ensures NO early TX at startup
 *   - Learning quickly reduces this to optimal value
 */
#define UTLP_LATENCY_INITIAL_US          50000UL     /* 50ms conservative */

/**
 * @brief Minimum latency floor (microseconds)
 *
 * Never learn below this value. Provides safety margin for:
 *   - Minimum radio warmup time
 *   - Worst-case ISR latency spike
 *   - Prevents unstable oscillation near zero
 */
#define UTLP_LATENCY_MIN_US              100UL       /* 100µs minimum */

/**
 * @brief Maximum latency ceiling (microseconds)
 *
 * Sanity check - if we're consistently this late, something is broken.
 * Also prevents runaway if death spiral detection fails.
 */
#define UTLP_LATENCY_MAX_US              100000UL    /* 100ms maximum */

/**
 * @brief Late error learning divisor (convergence speed)
 *
 * When TX is LATE, we add (error_us / divisor) to the latency buffer.
 * Divisor of 16 means we correct ~6% of the error per cycle.
 *
 * Lower = faster convergence but more oscillation
 * Higher = slower convergence but more stable
 */
#define UTLP_LATENCY_LEARN_DIVISOR       16

/**
 * @brief Early decay rate (microseconds per cycle)
 *
 * When TX is ON-TIME or EARLY, we slowly reduce the latency buffer.
 * This finds the minimum necessary buffer over time.
 *
 * 10µs per cycle means 5ms reduction over 500 cycles (~8 minutes at 1Hz).
 * Slow decay prevents oscillation while still optimizing.
 */
#define UTLP_LATENCY_DECAY_US            10UL

/**
 * @brief Dead zone threshold (microseconds)
 *
 * Errors within ±DEADZONE are considered "on time" - no learning.
 * Prevents oscillation around the optimal point.
 */
#define UTLP_LATENCY_DEADZONE_US         10UL

/**
 * @brief Death spiral bump (microseconds)
 *
 * If esp_ieee802154_transmit_at() returns ESP_ERR_INVALID_STATE
 * (meaning we're already past the target time), bump latency by this amount.
 *
 * This is the "death spiral" prevention patch - without it, a system under
 * heavy load could repeatedly miss deadlines and never recover.
 */
#define UTLP_LATENCY_DEATH_SPIRAL_BUMP_US  5000UL   /* 5ms emergency bump */

/** @} */ /* proprioception */

/*============================================================================
 * SPECTRAL RETINA - Multi-Transport RSSI Telemetry (Claim: Polychromatic Awareness)
 *
 * "See the Radio Color"
 *
 * When the same peer is observed on multiple transports (WiFi and 802.15.4),
 * the RSSI values reveal environmental RF characteristics:
 *
 *   - SIMILAR RSSI (Delta < 10dB): CLEAR environment, minimal multipath
 *   - DIFFERENT RSSI (Delta > 10dB): CLUTTERED environment, multipath divergence
 *
 * WHY THIS MATTERS:
 *   - Multipath causes timing jitter (signal bouncing = variable delay)
 *   - High RSSI delta = high multipath = less reliable timing
 *   - Future: Weight consensus contributions by RF clarity
 *
 * MEASUREMENT:
 *   - Store RSSI per-arbor per-peer in the Metabolic Ledger
 *   - When peer seen on arbor B, check if arbor A has recent reading (< 5s)
 *   - If both fresh, calculate delta and log spectral coherence
 *
 * @see examples/utlp/utlp_trust.c - Spectral coherence logging
 * @see examples/utlp/utlp_trust.h - Per-arbor RSSI fields in peer ledger
 *==========================================================================*/

/** @defgroup spectral_retina Spectral Retina (RSSI Telemetry)
 * @{
 */

/**
 * @brief RSSI staleness threshold (milliseconds)
 *
 * RSSI readings older than this are considered stale and won't be used
 * for spectral coherence comparison.
 *
 * 5 seconds allows for:
 *   - Normal beacon intervals (100ms to 60s)
 *   - Brief transport outages
 *   - Enough freshness for meaningful comparison
 */
#define UTLP_RSSI_STALE_MS              5000UL      /* 5 seconds */

/**
 * @brief RSSI delta threshold for CLEAR vs CLUTTERED classification (dB)
 *
 * If |WiFi_RSSI - 154_RSSI| <= this value, environment is CLEAR.
 * If |WiFi_RSSI - 154_RSSI| > this value, environment is CLUTTERED.
 *
 * 10dB is chosen because:
 *   - Typical free-space variance is < 5dB
 *   - Multipath environments show 15-30dB divergence
 *   - 10dB is a reasonable boundary
 */
#define UTLP_RSSI_DELTA_CLEAR           10          /* 10 dB threshold */

/**
 * @brief Invalid RSSI sentinel value
 *
 * Used to mark RSSI fields as "never measured" (distinct from -127dBm).
 * Chosen as absolute minimum int8_t since real RSSI never reaches -128dBm.
 */
#define UTLP_RSSI_INVALID               (-128)

/** @} */ /* spectral_retina */

/*============================================================================
 * INTERRUPT LATENCY COMPENSATION (ILC) - Phase Timer Proprioception
 *
 * "The Body Learns Its Own Timing - For ISR Paths"
 *
 * Dual Stack (WiFi+BLE) devices experience ~40-60µs interrupt latency due to
 * the coexistence arbiter. Single Stack devices experience ~5µs. Without
 * compensation, these devices will show a visible phase offset.
 *
 * ILC learns the actual ISR latency and PRE-FIRES the timer to compensate,
 * ensuring the LED actuates at the intended physics time regardless of
 * interrupt weight.
 *
 * The ILC learning loop runs in the phase timer ISR:
 * 1. MEASURE: At ISR entry, capture actual time vs. expected target
 * 2. LEARN: Update EMA of ISR latency based on error
 * 3. COMPENSATE: Pre-fire next timer by learned latency
 *
 * Expected Convergence:
 * - Single Stack: ~5-20µs after ~100 cycles
 * - Dual Stack: ~40-80µs after ~100 cycles
 *
 * @see examples/utlp/utlp_phase.c - Learning loop in phase_timer_empty_isr()
 * @see docs/UTLP_Technical_Supplement_S2.md - Claim 239+ (Hardware TX)
 *==========================================================================*/

/** @defgroup ilc Interrupt Latency Compensation
 * @{
 */

/**
 * @brief Initial ISR latency estimate (microseconds)
 *
 * Conservative startup value. The learning loop will converge to actual
 * platform characteristics within ~100 cycles.
 *
 * 1ms is chosen because:
 *   - Worst-case ISR latency is ~100µs
 *   - 10× safety margin ensures NO early actuation at startup
 *   - Learning quickly reduces this to optimal value
 */
#define UTLP_ILC_INITIAL_US              1000UL      /* 1ms conservative */

/**
 * @brief Minimum ISR latency floor (microseconds)
 *
 * Never learn below this value. Provides safety margin for:
 *   - Minimum interrupt dispatch time
 *   - Worst-case priority inversion spike
 *   - Prevents unstable oscillation near zero
 */
#define UTLP_ILC_MIN_US                  5UL         /* 5µs floor */

/**
 * @brief Maximum ISR latency ceiling (microseconds)
 *
 * Sanity check - if we're consistently this late, something is broken.
 * Also prevents runaway if death spiral detection fails.
 */
#define UTLP_ILC_MAX_US                  100000UL    /* 100ms ceiling */

/**
 * @brief Learning rate divisor (convergence speed)
 *
 * When ISR is LATE, we add (error_us / divisor) to the latency buffer.
 * Divisor of 16 means we correct ~6% of the error per cycle.
 *
 * Lower = faster convergence but more oscillation
 * Higher = slower convergence but more stable
 */
#define UTLP_ILC_LEARN_DIVISOR           16

/**
 * @brief Early decay rate (microseconds per cycle)
 *
 * When ISR is ON-TIME or EARLY, we slowly reduce the latency buffer.
 * This finds the minimum necessary buffer over time.
 *
 * 2µs per cycle means 200µs reduction over 100 cycles (~100 seconds).
 * Slow decay prevents oscillation while still optimizing.
 */
#define UTLP_ILC_DECAY_US                2UL

/**
 * @brief Deadzone threshold (microseconds)
 *
 * Errors within ±DEADZONE are considered "on time" - no learning.
 * Prevents oscillation around the optimal point.
 */
#define UTLP_ILC_DEADZONE_US             5UL

/**
 * @brief Death spiral bump (microseconds)
 *
 * Emergency bump if ISR fires extremely late (>deadzone).
 * Provides faster recovery from pathological conditions.
 * Used when error exceeds normal learning rate capacity.
 */
#define UTLP_ILC_DEATH_SPIRAL_BUMP_US    1000UL      /* 1ms emergency bump */

/** @} */ /* ilc */

#ifdef __cplusplus
}
#endif
