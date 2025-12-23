/**
 * @file threshold_config.h
 * @brief Validation Thresholds and Limits (Single Source of Truth)
 *
 * This header provides centralized validation thresholds used across modules.
 * All range checks and validation limits should use these named constants.
 *
 * SSOT Rule: Never hardcode threshold values. Always import and use named constants.
 *
 * @see CLAUDE.md "NO MAGIC NUMBERS" section
 * @date December 2025
 * @author Claude Code (Anthropic)
 */

#ifndef THRESHOLD_CONFIG_H
#define THRESHOLD_CONFIG_H

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================================
// FREQUENCY THRESHOLDS (centihertz for BLE transmission)
// ============================================================================

/**
 * @brief Minimum bilateral frequency (centihertz)
 *
 * 25 cHz = 0.25 Hz (one alternation per 4 seconds)
 * Lower limit for therapeutic bilateral stimulation.
 */
#define THRESHOLD_FREQ_MIN_CHZ          25

/**
 * @brief Maximum bilateral frequency (centihertz)
 *
 * 200 cHz = 2.0 Hz (two alternations per second)
 * Upper limit for EMDR therapeutic range per EMDRIA guidelines.
 */
#define THRESHOLD_FREQ_MAX_CHZ          200

// ============================================================================
// DUTY CYCLE THRESHOLDS (percentage)
// ============================================================================

/**
 * @brief Minimum motor duty cycle (%)
 *
 * 10% = minimum perceptible vibration intensity.
 * Below this, motor may not produce tactile sensation.
 */
#define THRESHOLD_DUTY_MIN_PCT          10

/**
 * @brief Maximum motor duty cycle (%)
 *
 * 100% = continuous motor activation during active phase.
 * Allows full duty for short pulses.
 */
#define THRESHOLD_DUTY_MAX_PCT          100

// ============================================================================
// PWM INTENSITY THRESHOLDS (percentage)
// ============================================================================

/**
 * @brief Mode 0/1 intensity minimum (%)
 *
 * Lower frequencies (0.5-1.0 Hz) allow lower intensity due to longer pulse.
 */
#define THRESHOLD_MODE01_INTENSITY_MIN  50

/**
 * @brief Mode 0/1 intensity maximum (%)
 *
 * Upper limit to prevent motor damage at lower frequencies.
 */
#define THRESHOLD_MODE01_INTENSITY_MAX  80

/**
 * @brief Mode 2/3 intensity minimum (%)
 *
 * Higher frequencies (1.5-2.0 Hz) need higher intensity for perception.
 */
#define THRESHOLD_MODE23_INTENSITY_MIN  70

/**
 * @brief Mode 2/3 intensity maximum (%)
 *
 * Upper limit to prevent motor damage at higher frequencies.
 */
#define THRESHOLD_MODE23_INTENSITY_MAX  90

/**
 * @brief Mode 4 (custom) intensity maximum (%)
 *
 * Custom mode allows flexible intensity with upper safety limit.
 */
#define THRESHOLD_MODE4_INTENSITY_MAX   80

/**
 * @brief PWM intensity fallback (%)
 *
 * Safe fallback value if mode is unknown (should never occur).
 */
#define THRESHOLD_PWM_FALLBACK          75

// ============================================================================
// LED THRESHOLDS
// ============================================================================

/**
 * @brief LED palette size (number of colors)
 *
 * 16-color palette (0-15 index range).
 */
#define THRESHOLD_LED_PALETTE_SIZE      16

/**
 * @brief LED brightness minimum (%)
 *
 * 10% = minimum visible brightness in normal lighting.
 */
#define THRESHOLD_LED_BRIGHTNESS_MIN    10

/**
 * @brief LED brightness maximum (%)
 *
 * 30% = maximum to prevent eye strain during therapy.
 * Per AD031 research safety constraints.
 */
#define THRESHOLD_LED_BRIGHTNESS_MAX    30

/**
 * @brief LED brightness percentage maximum (internal)
 *
 * 100% = maximum brightness for internal calculations.
 */
#define THRESHOLD_BRIGHTNESS_MAX_PCT    100

// ============================================================================
// SESSION DURATION THRESHOLDS
// ============================================================================

/**
 * @brief Minimum session duration (seconds)
 *
 * 1200 seconds = 20 minutes (minimum therapeutic session).
 */
#define THRESHOLD_SESSION_MIN_SEC       1200

/**
 * @brief Maximum session duration (seconds)
 *
 * 5400 seconds = 90 minutes (maximum safe session).
 */
#define THRESHOLD_SESSION_MAX_SEC       5400

// ============================================================================
// COMMAND PROTOCOL THRESHOLDS
// ============================================================================

/**
 * @brief Maximum delay command value (ms)
 *
 * 10000ms = 10 seconds maximum delay.
 */
#define THRESHOLD_DELAY_MAX_MS          10000

/**
 * @brief Minimum cycle period (ms)
 *
 * 250ms = 4 Hz maximum frequency (safety limit).
 */
#define THRESHOLD_CYCLE_MIN_MS          250

/**
 * @brief Maximum cycle period (ms)
 *
 * 4000ms = 0.25 Hz minimum frequency.
 */
#define THRESHOLD_CYCLE_MAX_MS          4000

/**
 * @brief Maximum intensity in command payload (%)
 *
 * 100% = full motor intensity.
 */
#define THRESHOLD_CMD_INTENSITY_MAX     100

// ============================================================================
// TIME SYNC THRESHOLDS
// ============================================================================

/**
 * @brief Antiphase lock cycle count threshold
 *
 * Number of cycles to wait before checking lock status.
 * 10 cycles provides enough samples for variance calculation.
 */
#define THRESHOLD_LOCK_CHECK_CYCLES     10

/**
 * @brief Significant drift correction threshold (%)
 *
 * Log corrections that exceed 10% of coast period.
 * Helps debug timing issues.
 */
#define THRESHOLD_SIGNIFICANT_DRIFT_PCT 10

/**
 * @brief Maximum reasonable phase offset (ms)
 *
 * Phase calculations exceeding 5000ms indicate error.
 */
#define THRESHOLD_MAX_PHASE_OFFSET_MS   5000

// ============================================================================
// BLE ERROR CODES (for readability)
// Note: Prefixed with THRESHOLD_ to avoid collision with NimBLE's ble.h defines
// ============================================================================

/**
 * @brief BLE Security Manager "PIN or Key Missing" error
 *
 * Status 14 (0x0E) indicates encryption required but key unavailable.
 */
#define THRESHOLD_BLE_SM_ERR_PIN_MISSING    14

/**
 * @brief BLE "ACL Connection Exists" error value
 *
 * Error 523 indicates connection already established.
 * Used for race condition handling in peer discovery.
 * Note: NimBLE defines BLE_ERR_ACL_CONN_EXISTS as enum, this is the raw value.
 */
#define THRESHOLD_BLE_ERR_ACL_CONN_EXISTS   523

// ============================================================================
// LOGGING/DEBUGGING THRESHOLDS
// ============================================================================

/**
 * @brief Pairing status log interval (ms)
 *
 * How often to log pairing wait status.
 */
#define THRESHOLD_PAIRING_LOG_INTERVAL_MS   5000

/**
 * @brief Idle state log interval (iterations)
 *
 * Log idle state every N iterations to reduce log spam.
 */
#define THRESHOLD_IDLE_LOG_INTERVAL     30

#ifdef __cplusplus
}
#endif

#endif // THRESHOLD_CONFIG_H
