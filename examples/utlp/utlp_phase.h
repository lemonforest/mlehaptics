/**
 * @file utlp_phase.h
 * @brief UTLP Hardware Phase Engine - HAL-Abstracted Atomic Coherency
 *
 * "Physics First: Hardware defines time, not software."
 *
 * This module implements Hardware Phase Locked Atomic Coherency (HPLAC)
 * via the platform-agnostic Timer HAL. The hardware timer IS the truth -
 * not a follower of software timing.
 *
 * @section architecture Architecture
 *
 * - **Single-Register Atomic Phase**: 50kHz × 50000 ticks = 1 second in ONE
 *   hardware register. A single hardware SYNC resets the ENTIRE phase cycle.
 *
 * - **Atomic Acquisition (Hard Sync)**: During Cold Start (first 5s), the
 *   Timer HAL hard_sync instantly jams the counter to the received phase.
 *
 * - **Disciplined Maintenance (Soft Slew)**: After locked, phase errors are
 *   corrected by bending the timer period (frequency slewing) to preserve
 *   spectral purity.
 *
 * - **Precision Windows**: Timer pauses between beacons for 20× power savings.
 *   Phase continuity maintained via RTC + anticipatory prediction.
 *
 * - **Anticipatory Memory**: Diagnostic framework predicting beacon timing,
 *   scoring accuracy, and building confidence for future power optimization.
 *
 * @section atomicity Critical Atomicity Requirements
 *
 * Three hazards are addressed (see Purple Team review):
 *
 * 1. **Execution Jitter**: Hard sync uses critical sections to prevent
 *    ISR insertion between calculation and sync activation.
 *
 * 2. **Torn Reads**: 64-bit `cycle_count` getters use critical sections to
 *    prevent reading mixed old/new 32-bit halves on 32-bit RISC-V.
 *
 * 3. **Sticky Slew**: Hard sync resets period to nominal to prevent drift
 *    continuation after phase jam.
 *
 * @see utlp_hal_timer.h - Platform-agnostic timer interface
 * @see utlp_config.h - Phase engine constants (SSOT)
 * @see docs/UTLP_Technical_Supplement_S2.md - Claim 55 (Servo-Locked Phase)
 *
 * @version 2.0.0
 * @date 2026-03-04
 *
 * @copyright
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#pragma once

#include <stdint.h>
#include <stdbool.h>

#ifdef ESP_PLATFORM
#include "esp_err.h"
#else
/* Native test environment */
typedef int esp_err_t;
#define ESP_OK          0
#define ESP_FAIL        (-1)
#define ESP_ERR_INVALID_ARG     0x102
#define ESP_ERR_INVALID_STATE   0x103
#endif

#ifdef __cplusplus
extern "C" {
#endif

/*============================================================================
 * PHASE ENGINE STATE STRUCTURE (Truck-Packed)
 *
 * "Pack like a truck: big boxes first" - ensures optimal memory alignment.
 *
 * Phase position = timer_count (0 to 49,999) representing 0° to 360°
 * Single hardware SYNC resets entire phase - true atomic coherency.
 *==========================================================================*/

/**
 * @brief Sync state machine states
 *
 * Variable Gain PLL state for selecting sync behavior:
 * - COLD: Hard jumps allowed, fast initial acquisition
 * - LOCKED: Soft slew only, maintain spectral purity
 * - RECOVERY: Fast slew rate for catching up after drift
 */
typedef enum {
    UTLP_PHASE_STATE_COLD = 0,      /**< Cold start - hard jumps allowed */
    UTLP_PHASE_STATE_LOCKED,        /**< Locked - soft slew only */
    UTLP_PHASE_STATE_RECOVERY       /**< Recovery - fast slew rate */
} utlp_phase_sync_state_t;

/**
 * @brief Phase engine state structure
 *
 * Physics First: Hardware defines time.
 *
 * @note Packed for optimal memory layout. 8-byte fields first, then 4-byte,
 *       then 2-byte, then 1-byte. Padding ensures 8-byte alignment.
 */
typedef struct __attribute__((packed)) {
    /* 8-byte fields first (64-bit) */
    uint64_t last_beacon_timestamp_us;  /**< When last beacon processed */
    uint64_t last_sync_timestamp_us;    /**< When last hard sync occurred */
    int64_t  epoch_offset_us;           /**< Offset for absolute time derivation */
    uint64_t cycle_count;               /**< Full cycles since init (for atomic time) */

    /* 4-byte fields (32-bit) */
    uint32_t current_period_ticks;      /**< Current period (for slew, nom=50000) */
    int32_t  drift_accumulator_ppb;     /**< Sub-tick drift accumulator */

    /* 2-byte fields (16-bit) */
    uint16_t last_error_ticks;          /**< Last measured phase error */
    uint16_t error_history[4];          /**< Rolling error buffer for quality */

    /* 1-byte fields (8-bit) */
    uint8_t  error_history_idx;         /**< Index into error_history */
    uint8_t  sync_quality;              /**< Sync quality 0-100% */
    uint8_t  sync_state;                /**< COLD/LOCKED/RECOVERY (utlp_phase_sync_state_t) */
    bool     slewing;                   /**< Period adjustment active */
    uint8_t  _padding[10];              /**< Align to 64-byte boundary */
} utlp_phase_state_t;

/* Verify struct packing at compile time */
_Static_assert(sizeof(utlp_phase_state_t) == 64, "Phase state packing incorrect");

/*============================================================================
 * ANTICIPATORY MEMORY STRUCTURES
 *
 * Diagnostic-first framework for predicting beacon timing, scoring
 * prediction accuracy, and building confidence for power optimization.
 *
 * All devices maintain this — Genesis predicts its own beacon schedule
 * stability, Followers predict upstream beacon arrivals.
 *==========================================================================*/

/** @brief Anticipatory memory history buffer size (must be power of 2) */
#define UTLP_ANTICIPATORY_HISTORY_SIZE  8

/**
 * @brief Anticipatory memory entry — one beacon prediction cycle
 *
 * Records what we predicted vs. what actually happened, for each beacon.
 * This is the atomic unit of "proprioceptive time memory."
 */
typedef struct {
    /* Prediction (set before beacon arrives) */
    uint64_t predicted_arrival_us;      /**< When we expected the beacon */
    int64_t  predicted_offset_us;       /**< What offset we expected */

    /* Reality (set when beacon actually arrives) */
    uint64_t actual_arrival_us;         /**< When beacon actually arrived */
    int64_t  actual_offset_us;          /**< Actual measured offset */

    /* Scoring (computed after beacon) */
    int32_t  arrival_error_us;          /**< actual - predicted arrival */
    int32_t  offset_error_us;           /**< actual - predicted offset */
    uint8_t  confidence;                /**< 0-100, snapshot at time of observation */
    bool     hit;                       /**< Beacon arrived within wake window */
} utlp_anticipatory_entry_t;

/**
 * @brief Anticipatory memory diagnostic state
 *
 * Rolling window of prediction results for diagnostic logging.
 * All devices (Genesis and Follower) maintain this — Genesis predicts
 * its own beacon schedule stability, Followers predict upstream arrivals.
 */
typedef struct {
    utlp_anticipatory_entry_t history[UTLP_ANTICIPATORY_HISTORY_SIZE];
    uint8_t  history_idx;               /**< Current write index */
    uint8_t  total_predictions;         /**< Total predictions made */
    uint8_t  total_hits;                /**< Predictions within window */
    uint8_t  confidence;                /**< Current EMA confidence 0-100 */
    int32_t  avg_arrival_error_us;      /**< EMA of arrival timing error */
    int32_t  avg_offset_error_us;       /**< EMA of offset prediction error */
} utlp_anticipatory_state_t;

/*============================================================================
 * INITIALIZATION API
 *==========================================================================*/

/**
 * @brief Initialize the phase engine via Timer HAL
 *
 * Sets up the phase timer as the phase master:
 * - 50kHz resolution (20µs/tick)
 * - 50000 ticks per cycle (1 second)
 * - Cycle boundary callback for absolute time derivation
 * - Starts in CONTINUOUS mode (timer always on)
 *
 * @return ESP_OK on success, error code otherwise
 */
esp_err_t utlp_phase_init(void);

/**
 * @brief Deinitialize the phase engine
 *
 * Stops the timer and releases resources.
 *
 * @return ESP_OK on success, error code otherwise
 */
esp_err_t utlp_phase_deinit(void);

/*============================================================================
 * PHASE QUERY API
 *==========================================================================*/

/**
 * @brief Get current phase in timer ticks
 *
 * @return Phase ticks (0 to 49,999) representing entire 1-second cycle
 */
uint32_t utlp_phase_get_ticks(void);

/**
 * @brief Get current phase angle in degrees
 *
 * @return Phase angle 0-359 degrees
 */
uint16_t utlp_phase_get_angle(void);

/**
 * @brief Get current phase angle with 0.1 degree precision
 *
 * @return Phase angle 0-3599 (representing 0.0° to 359.9°)
 */
uint16_t utlp_phase_get_angle_x10(void);

/**
 * @brief Get full cycle count since initialization
 *
 * @note Uses critical section to prevent torn reads on 32-bit MCU.
 *
 * @return Number of complete 1-second cycles since init
 */
uint64_t utlp_phase_get_cycle_count(void);

/**
 * @brief Get copy of current phase engine state
 *
 * @param[out] state Pointer to state structure to fill
 * @return ESP_OK on success, ESP_ERR_INVALID_ARG if state is NULL
 */
esp_err_t utlp_phase_get_state(utlp_phase_state_t *state);

/*============================================================================
 * SYNCHRONIZATION API
 *==========================================================================*/

/**
 * @brief Perform hard sync (phase jam) during Cold Start
 *
 * Instantly teleports the hardware counter to the target phase.
 * Used during first 5 seconds for fast initial acquisition.
 *
 * @note Uses critical section to prevent execution jitter.
 * @note Resets period to nominal to prevent "sticky slew".
 *
 * @param target_ticks Target phase (0 to 49,999)
 * @return ESP_OK on success, error code otherwise
 */
esp_err_t utlp_phase_hard_sync(uint32_t target_ticks);

/**
 * @brief Apply soft slew for phase correction
 *
 * Bends the timer period to gradually correct phase error.
 * Used after Cold Start to maintain spectral purity.
 *
 * @param error_ticks Phase error in ticks (positive = behind, negative = ahead)
 * @return ESP_OK on success, error code otherwise
 */
esp_err_t utlp_phase_slew(int32_t error_ticks);

/**
 * @brief Process received beacon for phase synchronization
 *
 * High-level entry point called on beacon reception. Automatically
 * selects hard sync (Cold Start) or soft slew (Locked/Recovery)
 * based on current sync state.
 *
 * @param peer_tx_phase_ticks Peer's transmit phase in ticks
 * @param rx_timestamp_us Local receive timestamp (esp_timer_get_time)
 * @return ESP_OK on success, error code otherwise
 */
esp_err_t utlp_phase_on_beacon(uint32_t peer_tx_phase_ticks, uint64_t rx_timestamp_us);

/*============================================================================
 * MAINTENANCE API
 *==========================================================================*/

/**
 * @brief Periodic maintenance tick
 *
 * Called by engine timer (e.g., 10Hz) to:
 * - Update sync state (COLD → LOCKED → RECOVERY)
 * - Apply drift corrections
 * - Update quality metrics
 * - Drive Precision Window orchestrator (sleep/wake transitions)
 *
 * @param uptime_us Current uptime in microseconds
 */
void utlp_phase_tick(uint64_t uptime_us);

/**
 * @brief Get current sync quality (0-100%)
 *
 * @return Quality percentage based on recent phase errors
 */
uint8_t utlp_phase_get_quality(void);

/**
 * @brief Check if phase is synchronized
 *
 * @return true if in LOCKED state with quality >= 50%
 */
bool utlp_phase_is_synchronized(void);

/**
 * @brief Get current learned ISR latency (ILC diagnostic)
 *
 * Returns the current learned ISR latency in microseconds. This value
 * represents how much the ISR fires late due to interrupt dispatch overhead.
 *
 * Use for debugging and performance tuning. Typical values:
 * - Single Stack: ~5-20µs
 * - Dual Stack (WiFi+BLE coexistence): ~40-80µs
 *
 * @return Learned ISR latency in microseconds
 *
 * @see UTLP_ILC_* constants in utlp_config.h
 */
uint32_t utlp_phase_get_isr_latency_us(void);

/*============================================================================
 * PRECISION WINDOW API - Power-Managed Beacon Timing
 *
 * The phase engine can pause between beacons to save power.
 * Timer ON for ~2s around beacon events, OFF for ~58s sleep.
 * Phase continuity maintained via RTC + anticipatory prediction.
 *
 * Lifecycle:
 *   CONTINUOUS (boot) → PRECISION (after COMMITTED + confidence) → CONTINUOUS (fallback)
 *==========================================================================*/

/**
 * @brief Pause phase engine for Precision Window sleep
 *
 * Stops the hardware timer, captures cumulative time for reconstruction.
 * Phase can be reconstructed on resume using RTC elapsed time.
 *
 * @return ESP_OK on success, ESP_ERR_INVALID_STATE if not initialized or already paused
 */
esp_err_t utlp_phase_pause(void);

/**
 * @brief Resume phase engine from Precision Window pause
 *
 * Restarts the hardware timer, reconstructs cycle_count from RTC elapsed time.
 * Returns to previous PLL state (COLD/LOCKED/RECOVERY).
 *
 * @return ESP_OK on success, ESP_ERR_INVALID_STATE if not paused
 */
esp_err_t utlp_phase_resume(void);

/**
 * @brief Check if phase engine is currently paused
 *
 * @return true if paused (timer stopped, waiting for resume)
 */
bool utlp_phase_is_paused(void);

/**
 * @brief Enable Precision Window mode
 *
 * Allows the phase engine to sleep between beacons once anticipatory
 * confidence is sufficient. Call when Lineage Loyalty enters COMMITTED state.
 */
void utlp_phase_enable_precision_mode(void);

/**
 * @brief Disable Precision Window mode (return to continuous timer)
 *
 * Forces the phase engine back to always-on operation. Call when
 * Lineage Loyalty enters GRIEVING or NAIVE state, or on repeated
 * beacon misses.
 */
void utlp_phase_disable_precision_mode(void);

/**
 * @brief Check if Precision Window mode is active
 *
 * @return true if in PRECISION mode (may be AWAKE or SLEEPING)
 */
bool utlp_phase_is_precision_mode(void);

/*============================================================================
 * ANTICIPATORY MEMORY API - Diagnostic Prediction Framework
 *
 * Predict/observe/score beacon timing accuracy. All devices maintain this:
 * - Genesis predicts its own beacon schedule stability
 * - Followers predict upstream beacon arrivals
 *
 * Diagnostic-first: data collection only, NOT used for timing control yet.
 *==========================================================================*/

/**
 * @brief Record a beacon prediction (call before beacon expected)
 *
 * @param expected_arrival_us  Predicted beacon arrival (esp_timer epoch)
 * @param expected_offset_us   Predicted time offset from this beacon
 */
void utlp_anticipatory_predict(uint64_t expected_arrival_us, int64_t expected_offset_us);

/**
 * @brief Record actual beacon arrival (call when beacon received)
 *
 * Scores the most recent prediction against observed reality.
 * Updates confidence and error EMA.
 *
 * @param actual_arrival_us  Actual beacon arrival time (esp_timer epoch)
 * @param actual_offset_us   Actual measured time offset
 */
void utlp_anticipatory_observe(uint64_t actual_arrival_us, int64_t actual_offset_us);

/**
 * @brief Get current anticipatory confidence (0-100)
 *
 * @return Confidence percentage based on prediction accuracy history
 */
uint8_t utlp_anticipatory_get_confidence(void);

/**
 * @brief Log anticipatory memory state (diagnostic dump)
 *
 * Outputs current confidence, hit rate, and average errors via ESP_LOGI.
 */
void utlp_anticipatory_log_state(void);

/**
 * @brief Get copy of current anticipatory memory state
 *
 * @param[out] state Pointer to state structure to fill
 * @return ESP_OK on success, ESP_ERR_INVALID_ARG if state is NULL
 */
esp_err_t utlp_phase_get_anticipatory_state(utlp_anticipatory_state_t *state);

/*============================================================================
 * BACKWARD COMPATIBILITY API
 *==========================================================================*/

/**
 * @brief Get atomic time derived from hardware phase
 *
 * Replaces software-based utlp_hal_get_atomic_time_us().
 *
 * Calculation:
 *   atomic_time = (cycle_count × CYCLE_US) + (ticks × TICK_US) + epoch_offset
 *
 * @note Uses critical section to prevent torn reads.
 *
 * @return Atomic time in microseconds
 */
uint64_t utlp_phase_get_atomic_time_us(void);

/**
 * @brief Set epoch offset for time adoption
 *
 * Used when adopting time from a peer (e.g., genesis node adoption).
 *
 * @param offset_us Epoch offset in microseconds
 */
void utlp_phase_set_epoch_offset(int64_t offset_us);

/**
 * @brief Get current epoch offset
 *
 * @return Current epoch offset in microseconds
 */
int64_t utlp_phase_get_epoch_offset(void);

#ifdef __cplusplus
}
#endif
