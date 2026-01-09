/**
 * @file utlp_phase.h
 * @brief UTLP Hardware Phase Engine - MCPWM-Based Atomic Coherency
 *
 * "Physics First: Hardware defines time, not software."
 *
 * This module implements Hardware Phase Locked Atomic Coherency (HPLAC) using
 * the ESP32-C6 MCPWM peripheral. The hardware timer IS the truth - not a
 * follower of software timing.
 *
 * @section architecture Architecture
 *
 * - **Single-Register Atomic Phase**: 50kHz × 50000 ticks = 1 second in ONE
 *   hardware register. A single hardware SYNC resets the ENTIRE phase cycle.
 *
 * - **Atomic Acquisition (Hard Sync)**: During Cold Start (first 5s), the
 *   MCPWM soft sync instantly jams the counter to the received phase.
 *
 * - **Disciplined Maintenance (Soft Slew)**: After locked, phase errors are
 *   corrected by bending the timer period (frequency slewing) to preserve
 *   spectral purity.
 *
 * @section atomicity Critical Atomicity Requirements
 *
 * Three hazards are addressed (see Purple Team review):
 *
 * 1. **Execution Jitter**: Hard sync uses `portENTER_CRITICAL()` to prevent
 *    ISR insertion between calculation and sync activation.
 *
 * 2. **Torn Reads**: 64-bit `cycle_count` getters use critical sections to
 *    prevent reading mixed old/new 32-bit halves on 32-bit RISC-V.
 *
 * 3. **Sticky Slew**: Hard sync resets period to nominal to prevent drift
 *    continuation after phase jam.
 *
 * @see utlp_config.h - Phase engine constants (SSOT)
 * @see docs/UTLP_Technical_Supplement_S2.md - Claim 55 (Servo-Locked Phase)
 *
 * @version 1.0.0
 * @date 2026-01-03
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
 * INITIALIZATION API
 *==========================================================================*/

/**
 * @brief Initialize the MCPWM phase engine
 *
 * Sets up MCPWM Timer 0 as the phase master:
 * - 50kHz resolution (20µs/tick)
 * - 50000 ticks per cycle (1 second)
 * - Soft sync source for hard sync capability
 * - Cycle boundary ISR for absolute time derivation
 *
 * @return ESP_OK on success, error code otherwise
 */
esp_err_t utlp_phase_init(void);

/**
 * @brief Deinitialize the phase engine
 *
 * Stops the MCPWM timer and releases resources.
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
