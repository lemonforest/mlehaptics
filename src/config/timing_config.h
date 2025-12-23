/**
 * @file timing_config.h
 * @brief Cross-Module Timing Constants (Single Source of Truth)
 *
 * This header provides centralized timing constants used across multiple modules.
 * All timing-related magic numbers should be extracted here with documentation.
 *
 * SSOT Rule: Never hardcode timing values. Always import and use named constants.
 *
 * @see CLAUDE.md "NO MAGIC NUMBERS" section
 * @date December 2025
 * @author Claude Code (Anthropic)
 */

#ifndef TIMING_CONFIG_H
#define TIMING_CONFIG_H

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================================
// MOTOR TASK TIMING
// ============================================================================

/**
 * @brief Back-EMF sampling window duration (ms)
 *
 * Period after mode change during which back-EMF samples are logged.
 * Used for motor research data collection.
 */
#define TIMING_LED_INDICATION_MS        10000

/**
 * @brief Back-EMF settle time (ms)
 *
 * Delay after motor turns off before taking "settled" BEMF reading.
 * Allows motor coils to stabilize for accurate measurement.
 */
#define TIMING_BACKEMF_SETTLE_MS        10

/**
 * @brief Queue check interval (ms)
 *
 * How often motor_task checks for mode changes during delays.
 * Determines mode switch latency (lower = faster response).
 * Per AD030: Must be <=100ms for instant mode switching.
 */
#define TIMING_MODE_CHECK_INTERVAL_MS   50

/**
 * @brief Battery check interval (ms)
 *
 * How often to check battery voltage and log status.
 * 60 seconds provides balance between monitoring and power savings.
 */
#define TIMING_BATTERY_CHECK_INTERVAL_MS    60000

/**
 * @brief BLE session time notification interval (ms)
 *
 * How often to notify connected BLE clients of session elapsed time.
 */
#define TIMING_SESSION_NOTIFY_INTERVAL_MS   60000

/**
 * @brief Coordinated start delay (ms)
 *
 * Buffer time for bilateral coordination startup sequence.
 * Accounts for BLE transmission latency + processing + margin.
 * Phase 6l: Increased from 500ms to 3000ms for handshake overhead.
 */
#define TIMING_COORD_START_DELAY_MS     3000

// ============================================================================
// QUEUE/TASK TIMING
// ============================================================================

/**
 * @brief Default queue receive timeout (ms)
 *
 * Standard timeout for blocking queue receives.
 * Used when task needs to respond to messages but has other work to do.
 */
#define TIMING_QUEUE_TIMEOUT_MS         100

/**
 * @brief Short delay for task synchronization (ms)
 *
 * Brief delay used for task handoffs and synchronization.
 * Allows other tasks to run and process messages.
 */
#define TIMING_TASK_SYNC_DELAY_MS       50

// ============================================================================
// TIME SYNC TIMING
// ============================================================================

/**
 * @brief Time sync initialization timeout (iterations)
 *
 * Maximum wait iterations for time_sync to initialize.
 * Total timeout = TIMING_SYNC_INIT_MAX_ITER * TIMING_TASK_SYNC_DELAY_MS
 * Default: 20 * 50ms = 1000ms
 */
#define TIMING_SYNC_INIT_MAX_ITER       20

/**
 * @brief CLIENT_READY wait timeout (iterations)
 *
 * Maximum wait iterations for CLIENT_READY acknowledgment.
 * Total timeout = TIMING_CLIENT_READY_MAX_ITER * TIMING_TASK_SYNC_DELAY_MS
 * Default: 100 * 50ms = 5000ms
 */
#define TIMING_CLIENT_READY_MAX_ITER    100

/**
 * @brief Handshake completion timeout (iterations)
 *
 * Maximum wait iterations for time sync handshake to complete.
 * Total timeout = TIMING_HANDSHAKE_MAX_ITER * TIMING_TASK_SYNC_DELAY_MS
 * Default: 100 * 50ms = 5000ms
 */
#define TIMING_HANDSHAKE_MAX_ITER       100

/**
 * @brief Coordinated start epoch wait (iterations)
 *
 * Maximum wait iterations for SERVER's coordinated start beacon.
 * Total timeout = TIMING_COORD_EPOCH_MAX_ITER * TIMING_TASK_SYNC_DELAY_MS
 * Default: 100 * 50ms = 5000ms
 */
#define TIMING_COORD_EPOCH_MAX_ITER     100

/**
 * @brief Antiphase sync wait timeout (iterations)
 *
 * Maximum wait iterations for handshake during antiphase calculation.
 * Total timeout = TIMING_ANTIPHASE_SYNC_MAX_ITER * TIMING_TASK_SYNC_DELAY_MS
 * Default: 20 * 50ms = 1000ms
 */
#define TIMING_ANTIPHASE_SYNC_MAX_ITER  20

// ============================================================================
// BLE ADVERTISING TIMING
// ============================================================================

/**
 * @brief BLE discovery window duration (ms)
 *
 * Duration for peer discovery advertising before switching to app-only mode.
 * Should be long enough for peer devices to discover each other.
 */
#define TIMING_BLE_DISCOVERY_WINDOW_MS  30000

/**
 * @brief BLE advertising timeout (ms)
 *
 * Maximum duration before advertising times out (5 minutes).
 * Prevents indefinite advertising if no connection made.
 */
#define TIMING_BLE_ADV_TIMEOUT_MS       300000

// ============================================================================
// BUTTON TIMING
// ============================================================================

/**
 * @brief Button debounce delay (ms)
 *
 * Minimum time button must be stable to register state change.
 */
#define TIMING_BUTTON_DEBOUNCE_MS       50

/**
 * @brief Button hold threshold for BLE re-enable (ms)
 *
 * Duration button must be held to trigger BLE advertising restart.
 */
#define TIMING_BUTTON_BLE_REENABLE_MS   1000

/**
 * @brief Button hold threshold for emergency shutdown (ms)
 *
 * Duration button must be held to trigger emergency shutdown sequence.
 */
#define TIMING_BUTTON_SHUTDOWN_MS       5000

// ============================================================================
// PHASE 6t FAST LOCK TIMING
// ============================================================================

/**
 * @brief Fast lock delay for CLIENT coordination (us)
 *
 * Delay to allow CLIENT time for fast lock acquisition:
 * - 5 forced beacons @ 200ms = 1000ms
 * - Fast lock detection (variance check)
 * - Phase calculation prep
 * Total: ~1200ms, use 1500ms for safety margin
 */
#define TIMING_FAST_LOCK_DELAY_US       1500000ULL

#ifdef __cplusplus
}
#endif

#endif // TIMING_CONFIG_H
