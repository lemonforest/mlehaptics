/**
 * @file utlp_hal_timer.h
 * @brief UTLP Hardware Abstraction Layer - Phase Timer
 *
 * Platform-agnostic timer interface for the UTLP phase engine.
 * Abstracts hardware timers to enable cross-platform synchronization
 * and power-managed Precision Window operation.
 *
 * Key capabilities:
 * - Init/deinit with configurable resolution and period
 * - Fast tick access (<1µs, ISR-safe)
 * - Hard sync (instant phase teleport) and period bending (frequency slew)
 * - Pause/resume for Precision Windows (timer OFF during sleep)
 * - Runtime reconfigure for dynamic resolution switching
 *
 * Implementations:
 * - utlp_hal_timer_esp32.c  (ESP32 MCPWM)
 * - utlp_hal_timer_native.c (Host software emulation, future)
 *
 * @version 2.0.0
 * @date 2026-03-04
 *
 * @copyright
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#ifndef UTLP_HAL_TIMER_H
#define UTLP_HAL_TIMER_H

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/*============================================================================
 * TYPES
 *==========================================================================*/

/**
 * @brief Timer error codes
 */
typedef enum {
    UTLP_TIMER_OK = 0,
    UTLP_TIMER_ERR_INVALID_ARG,
    UTLP_TIMER_ERR_NOT_INITIALIZED,
    UTLP_TIMER_ERR_ALREADY_INITIALIZED,
    UTLP_TIMER_ERR_NOT_RUNNING,
    UTLP_TIMER_ERR_ALREADY_PAUSED,
    UTLP_TIMER_ERR_NOT_PAUSED,
    UTLP_TIMER_ERR_PLATFORM,
    UTLP_TIMER_ERR_COUNT         /**< Sentinel for bounds checking */
} utlp_hal_timer_err_t;

/**
 * @brief Cycle boundary callback
 *
 * Called from ISR context when timer wraps. Must be ISR-safe.
 *
 * @param user_ctx      Context pointer from config
 * @param count_at_isr  Timer count at ISR entry (for latency measurement)
 * @return true if higher-priority task was woken
 */
typedef bool (*utlp_hal_timer_cb_t)(void *user_ctx, uint32_t count_at_isr);

/**
 * @brief Timer configuration
 */
typedef struct {
    uint32_t resolution_hz;         /**< Timer frequency (e.g., 50000 for 50 kHz) */
    uint32_t period_ticks;          /**< Ticks per cycle (e.g., 50000 for 1s @ 50 kHz) */
    utlp_hal_timer_cb_t on_cycle;   /**< Cycle boundary callback (ISR context) */
    void *user_ctx;                 /**< Context for callback */
} utlp_hal_timer_config_t;

/**
 * @brief Timer capabilities (populated after init)
 */
typedef struct {
    uint32_t actual_resolution_hz;  /**< Achieved resolution */
    uint32_t max_period_ticks;      /**< Maximum period supported */
    bool has_hard_sync;             /**< Supports instant phase jam */
    bool has_period_bend;           /**< Supports runtime period adjustment */
    uint8_t counter_bits;           /**< Counter width (16, 24, 32) */
} utlp_hal_timer_caps_t;

/*============================================================================
 * INITIALIZATION
 *==========================================================================*/

/**
 * @brief Initialize phase timer hardware
 *
 * @param config  Configuration (NULL for defaults from utlp_config.h)
 * @return UTLP_TIMER_OK on success
 */
utlp_hal_timer_err_t utlp_hal_timer_init(const utlp_hal_timer_config_t *config);

/**
 * @brief Deinitialize phase timer
 *
 * Stops timer if running, releases all hardware resources.
 *
 * @return UTLP_TIMER_OK on success
 */
utlp_hal_timer_err_t utlp_hal_timer_deinit(void);

/**
 * @brief Get timer capabilities
 *
 * @param[out] caps  Capabilities structure to fill
 * @return UTLP_TIMER_OK on success
 */
utlp_hal_timer_err_t utlp_hal_timer_get_caps(utlp_hal_timer_caps_t *caps);

/*============================================================================
 * TICK ACCESS (FAST PATH - must be < 1 microsecond)
 *==========================================================================*/

/**
 * @brief Get current timer tick count
 *
 * MUST be atomic single-register read. Safe for ISR context.
 *
 * @return Current tick (0 to period_ticks-1)
 */
uint32_t utlp_hal_timer_get_ticks(void);

/*============================================================================
 * SYNCHRONIZATION
 *==========================================================================*/

/**
 * @brief Hard sync - instant phase teleport
 *
 * Atomically sets counter to target value. Resets period to nominal.
 * Used during cold start for fast acquisition.
 *
 * @param target_ticks  Target phase (clamped to period-1)
 * @return UTLP_TIMER_OK on success
 */
utlp_hal_timer_err_t utlp_hal_timer_hard_sync(uint32_t target_ticks);

/**
 * @brief Set timer period for frequency slewing
 *
 * Bends period to gradually correct phase error.
 * - new_period > nominal: timer runs slower
 * - new_period < nominal: timer runs faster
 *
 * @param new_period_ticks  New period value
 * @return UTLP_TIMER_OK on success
 */
utlp_hal_timer_err_t utlp_hal_timer_set_period(uint32_t new_period_ticks);

/**
 * @brief Get current period
 *
 * @return Current period in ticks
 */
uint32_t utlp_hal_timer_get_period(void);

/**
 * @brief Reset period to nominal (from init config)
 *
 * @return UTLP_TIMER_OK on success
 */
utlp_hal_timer_err_t utlp_hal_timer_reset_period(void);

/*============================================================================
 * CONTROL
 *==========================================================================*/

/**
 * @brief Start timer
 *
 * Begins counting from current position. Timer must be initialized.
 *
 * @return UTLP_TIMER_OK on success
 */
utlp_hal_timer_err_t utlp_hal_timer_start(void);

/**
 * @brief Stop timer (full stop, not for Precision Windows)
 *
 * Stops timer at next cycle boundary (STOP_EMPTY). For Precision Window
 * sleep, use utlp_hal_timer_pause() instead.
 *
 * @return UTLP_TIMER_OK on success
 */
utlp_hal_timer_err_t utlp_hal_timer_stop(void);

/**
 * @brief Check if timer is running
 *
 * @return true if timer is counting (not paused, not stopped)
 */
bool utlp_hal_timer_is_running(void);

/*============================================================================
 * PRECISION WINDOW - Pause/Resume for Power Management
 *
 * Distinct from stop/start: pause preserves configuration and state
 * for fast resume. The caller captures elapsed time for phase
 * continuity reconstruction via RTC.
 *==========================================================================*/

/**
 * @brief Pause timer for Precision Window sleep
 *
 * Stops the hardware counter but preserves all configuration
 * (resolution, period, callback). Returns the cumulative time
 * elapsed since last start/resume for phase reconstruction.
 *
 * On resume, the phase engine uses this elapsed value plus
 * RTC-measured sleep duration to reconstruct cycle_count.
 *
 * @param[out] elapsed_us  Total microseconds of timer running time
 *                         since last start/resume. NULL to skip.
 * @return UTLP_TIMER_OK on success
 * @return UTLP_TIMER_ERR_NOT_RUNNING if timer not running
 * @return UTLP_TIMER_ERR_ALREADY_PAUSED if already paused
 */
utlp_hal_timer_err_t utlp_hal_timer_pause(uint64_t *elapsed_us);

/**
 * @brief Resume timer from Precision Window pause
 *
 * Restarts the hardware counter from zero with existing configuration.
 * Phase engine handles cycle_count reconstruction using RTC elapsed time.
 *
 * @return UTLP_TIMER_OK on success
 * @return UTLP_TIMER_ERR_NOT_PAUSED if not in paused state
 */
utlp_hal_timer_err_t utlp_hal_timer_resume(void);

/**
 * @brief Check if timer is paused
 *
 * @return true if timer was paused via utlp_hal_timer_pause()
 */
bool utlp_hal_timer_is_paused(void);

/*============================================================================
 * DYNAMIC RECONFIGURATION
 *
 * Runtime resolution switching for future power profile support.
 * The timer is stopped during reconfiguration — caller must account
 * for the gap in tick counting.
 *==========================================================================*/

/**
 * @brief Reconfigure timer resolution at runtime
 *
 * Tears down and recreates the MCPWM timer with new parameters.
 * Returns cumulative elapsed time for phase continuity.
 *
 * The callback and user_ctx from init are preserved.
 *
 * @param new_resolution_hz  New timer frequency
 * @param new_period_ticks   New ticks per cycle
 * @param[out] elapsed_us    Elapsed time before reconfigure. NULL to skip.
 * @return UTLP_TIMER_OK on success
 */
utlp_hal_timer_err_t utlp_hal_timer_reconfigure(
    uint32_t new_resolution_hz,
    uint32_t new_period_ticks,
    uint64_t *elapsed_us);

/*============================================================================
 * CRITICAL SECTIONS
 *==========================================================================*/

/**
 * @brief Enter critical section (disable interrupts)
 *
 * @return State to pass to exit_critical
 */
uint32_t utlp_hal_timer_enter_critical(void);

/**
 * @brief Exit critical section
 *
 * @param state  Value from enter_critical
 */
void utlp_hal_timer_exit_critical(uint32_t state);

#ifdef __cplusplus
}
#endif

#endif /* UTLP_HAL_TIMER_H */
