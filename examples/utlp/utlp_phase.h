/**
 * @file utlp_phase.h
 * @brief UTLP Hardware Phase Engine - Vector Time Foundation
 *
 * "Time is a chord, not a number."
 *
 * This module implements Hardware Phase Locked Coherency (HPLC) using
 * the timer HAL. Time is represented natively as a PHASE CHORD - 8 residues
 * modulo coprime primes. Scalar time is DERIVED via CRT when needed.
 *
 * @section architecture Architecture
 *
 * - **Vector Time Native**: Time is tracked as phase_chord[8], not scalar.
 *   Each element is cycles % prime[i]. Scalar time is CRT-derived when needed.
 *
 * - **Single-Register Atomic Phase**: 10 MHz × 10000 ticks = 1 ms in ONE
 *   hardware register. A single hardware SYNC resets the ENTIRE phase cycle.
 *
 * - **Protocol Primitive Precision**: 100 ns tick resolution enables true
 *   hardware-level timing for distributed time synchronization primitives.
 *
 * - **Hard Sync**: During Cold Start (first 5s), instant phase jam.
 *
 * - **Soft Slew**: After locked, period bending preserves spectral purity.
 *
 * @section timing Timing Configuration (10 MHz)
 *
 * Current configuration uses PLL160M divided by 16 for 10 MHz operation:
 * - Timer resolution: 10 MHz (100 ns per tick)
 * - Ticks per cycle: 10000 (fits 16-bit MCPWM counter)
 * - Hardware cycle: 1 ms
 * - ISR rate: 1 kHz (cycle boundary interrupt)
 *
 * @section power Power vs Precision Tradeoff
 *
 * @note **1 kHz ISR prevents light sleep.** The ESP32 cannot enter light sleep
 * with interrupt wakeups faster than ~10 ms. For battery-powered applications
 * where precision can be relaxed, consider the 1 MHz alternative below.
 *
 * @par 1 MHz Alternative (Battery-Friendly)
 * For applications where 1 µs tick resolution suffices:
 * - Timer resolution: 1 MHz (1 µs per tick)
 * - Ticks per cycle: 10000 (same counter range)
 * - Hardware cycle: 10 ms
 * - ISR rate: 100 Hz (enables light sleep between wakeups)
 *
 * Change in utlp_config.h:
 * @code
 * #define UTLP_PHASE_TIMER_RESOLUTION_HZ   1000000UL   // 1 MHz
 * #define UTLP_PHASE_CYCLE_US              10000UL     // 10 ms
 * #define UTLP_PHASE_TICK_NS               1000UL      // 1 µs
 * @endcode
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
 * @version 2.0.0
 * @date 2026-01-08
 *
 * @copyright
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#pragma once

#include <stdint.h>
#include <stdbool.h>
#include "utlp_config.h"  /* For utlp_power_profile_t, utlp_power_params_t */

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
 * VECTOR TIME TYPES - Protocol Primitive
 *
 * "Time is a chord, not a number."
 *
 * The phase chord is the NATIVE representation of time in UTLP. Each element
 * is (cycles % prime[i]). Scalar time is DERIVED via CRT when needed (and
 * marked invalid during partition).
 *==========================================================================*/

/**
 * @brief Phase chord - 8-byte vector time representation
 *
 * Wire format: packed, ready for transmission
 * Each byte is cycles % prime[i] where primes are from UTLP_PRIMES_INIT
 */
typedef uint8_t utlp_phase_chord_t[8];

/**
 * @brief Partition status (from HD similarity)
 *
 * When vector similarity drops, CRT may become ambiguous.
 * SMSP can still sync on phase tuples even during partition.
 */
typedef enum {
    UTLP_PARTITION_NONE = 0,     /**< >70% similarity - CRT unambiguous */
    UTLP_PARTITION_CAUTION,      /**< 40-70% similarity - CRT marginal */
    UTLP_PARTITION_DETECTED      /**< <40% similarity - CRT ambiguous, phase-lock only */
} utlp_partition_status_t;

/**
 * @brief Application time object (truck-packed, NOT wire format)
 *
 * Provides both vector and scalar views of time. Applications should:
 * - Use phase_chord for SMSP pattern matching (partition-resilient)
 * - Use scalar_us only when crt_valid is true (logging, calendar)
 */
typedef struct {
    utlp_phase_chord_t phase_chord;      /**< Vector time (always valid) */
    uint64_t           scalar_us;        /**< CRT-derived (check crt_valid!) */
    utlp_partition_status_t partition;   /**< Current partition status */
    bool               crt_valid;        /**< False if partition detected */
} utlp_app_time_t;

/*============================================================================
 * PHASE ENGINE STATE STRUCTURE (Truck-Packed)
 *
 * "Pack like a truck: big boxes first" - ensures optimal memory alignment.
 *
 * Phase position = timer_count (0 to 9,999) representing 0° to 360°
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
 * "Time is a chord, not a number."
 *
 * The phase_chord is the NATIVE time representation. cycle_count exists
 * for efficient chord computation (cycles % prime[i]).
 *
 * @note Packed for optimal memory layout. 8-byte fields first, then 4-byte,
 *       then 2-byte, then 1-byte. Padding ensures 8-byte alignment.
 */
typedef struct __attribute__((packed)) {
    /* 8-byte fields first (64-bit) */
    uint64_t last_beacon_timestamp_us;  /**< When last beacon processed */
    uint64_t last_sync_timestamp_us;    /**< When last hard sync occurred */
    int64_t  epoch_offset_us;           /**< Offset for CRT scalar derivation */
    uint64_t cycle_count;               /**< Full cycles since init (for chord computation) */

    /* Vector time - NATIVE representation */
    utlp_phase_chord_t phase_chord;     /**< Current phase chord (8 bytes) */

    /* 4-byte fields (32-bit) */
    uint32_t current_period_ticks;      /**< Current period (for slew, nom=10000) */
    int32_t  drift_accumulator_ppb;     /**< Sub-tick drift accumulator */

    /* 2-byte fields (16-bit) */
    uint16_t last_error_ticks;          /**< Last measured phase error */
    uint16_t error_history[4];          /**< Rolling error buffer for quality */

    /* 1-byte fields (8-bit) */
    uint8_t  error_history_idx;         /**< Index into error_history */
    uint8_t  sync_quality;              /**< Sync quality 0-100% */
    uint8_t  sync_state;                /**< COLD/LOCKED/RECOVERY (utlp_phase_sync_state_t) */
    uint8_t  partition_status;          /**< Current partition status */
    bool     slewing;                   /**< Period adjustment active */
    bool     crt_valid;                 /**< CRT scalar is valid (no partition) */
    uint8_t  _padding[8];               /**< Align to 72-byte boundary */
} utlp_phase_state_t;

/* Verify struct packing at compile time */
_Static_assert(sizeof(utlp_phase_state_t) == 72, "Phase state packing incorrect");

/*============================================================================
 * INITIALIZATION API
 *==========================================================================*/

/**
 * @brief Initialize the MCPWM phase engine
 *
 * Sets up MCPWM Timer 0 as the phase master:
 * - 10 MHz resolution (100 ns/tick) from PLL160M
 * - 10000 ticks per cycle (1 ms)
 * - Soft sync source for hard sync capability
 * - Cycle boundary ISR for absolute time derivation (1 kHz)
 *
 * @return ESP_OK on success, error code otherwise
 */
esp_err_t utlp_phase_init(void);

/**
 * @brief Phase engine configuration for init
 */
typedef struct {
    utlp_power_profile_t power_profile;  /**< Power profile selection */
} utlp_phase_config_t;

/**
 * @brief Initialize phase engine with configuration
 *
 * Allows runtime selection of power profile:
 * - PRECISION: 10 MHz, 100 ns tick, 1 kHz ISR (default)
 * - BALANCED:  1 MHz, 1 µs tick, 100 Hz ISR (battery-friendly)
 *
 * @param config Configuration (NULL for defaults = PRECISION profile)
 * @return ESP_OK on success, error code otherwise
 */
esp_err_t utlp_phase_init_with_config(const utlp_phase_config_t *config);

/**
 * @brief Get current power parameters (read-only)
 *
 * Returns pointer to the active power parameters. Valid after init.
 * Use this instead of compile-time #defines for resolution-dependent math.
 *
 * @return Pointer to active parameters, or NULL if not initialized
 */
const utlp_power_params_t *utlp_phase_get_power_params(void);

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
 * @return Phase ticks (0 to 9,999) representing entire 1 ms cycle
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
 * @return Number of complete 1 ms cycles since init
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
 * @param target_ticks Target phase (0 to 9,999)
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
 * VECTOR TIME API - Primary Interface
 *
 * "Time is a chord, not a number."
 *
 * These are the PRIMARY time access functions. Scalar time is derived.
 *==========================================================================*/

/**
 * @brief Get current time as application time object
 *
 * This is the PREFERRED way to get time in UTLP. Returns both vector
 * and scalar views, with partition status indicating CRT validity.
 *
 * @param[out] time Application time object to fill
 * @return ESP_OK on success, error code otherwise
 */
esp_err_t utlp_phase_get_time(utlp_app_time_t *time);

/**
 * @brief Get current phase chord (vector time)
 *
 * Fast path for SMSP pattern matching. Copies 8 bytes.
 *
 * @param[out] chord 8-byte buffer for phase chord
 */
void utlp_phase_get_chord(utlp_phase_chord_t chord);

/**
 * @brief Get single phase value for actuator matching
 *
 * Fastest path for SMSP - no copy, just return one phase.
 *
 * @param prime_idx Index 0-7 into primes array
 * @return Current phase for that prime (0 to prime-1)
 */
uint8_t utlp_phase_get_phase(uint8_t prime_idx);

/**
 * @brief Compute phase chord from cycle count
 *
 * Utility function for converting cycles to chord representation.
 *
 * @param cycles Cycle count
 * @param[out] chord 8-byte buffer for computed chord
 */
void utlp_phase_cycles_to_chord(uint64_t cycles, utlp_phase_chord_t chord);

/*============================================================================
 * HD SIMILARITY API - Integer-Only (No Floats)
 *
 * "Float-free similarity metric for embedded efficiency."
 *
 * These functions compute similarity between phase chords using integer math
 * only. Critical for chord-origin verification and partition detection.
 *==========================================================================*/

/**
 * @brief Compute integer HD similarity between two phase chords
 *
 * Returns the number of dimensions (0-8) where the two chords are "close"
 * on their respective prime rings. Uses circular distance with ~10% threshold.
 *
 * Design: INTEGER-ONLY (no floating point operations)
 * - Input: Two 8-byte phase chords
 * - Output: Integer 0-8 (count of matching dimensions)
 * - Threshold: ~10% of prime value for each dimension
 *
 * Threshold Semantics:
 * - 8/8: Nearly identical time (within ~20 ticks)
 * - 6-7/8: Recent divergence (within ~100 ticks)
 * - 5/8: Minimum for chord-origin verification (UTLP_CHORD_ORIGIN_MIN_SIMILARITY)
 * - <5/8: Partition detected or spoofed chord
 *
 * @param a First phase chord (8 bytes)
 * @param b Second phase chord (8 bytes)
 * @return Similarity score 0-8 (higher = more similar)
 *
 * @see UTLP_CHORD_ORIGIN_MIN_SIMILARITY in utlp_config.h
 * @see utlp_phase_chord_origin_verify() for chord-origin defense
 */
uint8_t utlp_phase_chord_similarity(const utlp_phase_chord_t a, const utlp_phase_chord_t b);

/**
 * @brief Verify chord is consistent with claimed origin_time
 *
 * Defense Layer 1: Chord-Origin Verification
 *
 * When a peer claims an origin_time, we compute what their chord SHOULD be
 * (given elapsed time since origin) and compare with their actual chord.
 * Inconsistent chords indicate spoofing or severe partition.
 *
 * @param peer_chord Peer's claimed phase chord (8 bytes)
 * @param peer_origin_time Peer's claimed origin_time (seconds)
 * @param our_origin_time Our origin_time for reference (seconds)
 * @return true if chord is plausible (similarity >= UTLP_CHORD_ORIGIN_MIN_SIMILARITY)
 */
bool utlp_phase_chord_origin_verify(const utlp_phase_chord_t peer_chord,
                                    uint32_t peer_origin_time,
                                    uint32_t our_origin_time);

/*============================================================================
 * SCALAR TIME API - Derived (use with caution during partition)
 *==========================================================================*/

/**
 * @brief Get scalar time derived from phase chord via CRT
 *
 * @warning Check crt_valid before using! Returns 0 if partition detected.
 *
 * @return Scalar time in microseconds, or 0 if CRT invalid
 */
uint64_t utlp_phase_get_scalar_us(void);

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

/*============================================================================
 * BACKWARD COMPATIBILITY (deprecated)
 *==========================================================================*/

/**
 * @brief Get atomic time derived from hardware phase
 *
 * @deprecated Use utlp_phase_get_time() or utlp_phase_get_scalar_us() instead.
 *             This function ignores partition status.
 *
 * @return Scalar time in microseconds
 */
uint64_t utlp_phase_get_atomic_time_us(void);

#ifdef __cplusplus
}
#endif
