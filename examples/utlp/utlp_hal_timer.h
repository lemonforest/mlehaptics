/**
 * @file utlp_hal_timer.h
 * @brief UTLP Hardware Abstraction Layer - Phase Timer
 *
 * Platform-agnostic timer interface for the UTLP phase engine.
 * Abstracts hardware timers to enable cross-platform synchronization.
 *
 * Implementations:
 * - utlp_hal_timer_esp32.c  (ESP32 MCPWM)
 * - utlp_hal_timer_native.c (Host software emulation)
 *
 * @version 1.0.0
 * @date 2026-01-09
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
    UTLP_TIMER_ERR_PLATFORM,
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
    uint32_t resolution_hz;         /**< Timer frequency (e.g., 10000000 for 10 MHz) */
    uint32_t period_ticks;          /**< Ticks per cycle (e.g., 10000 for 1 ms @ 10 MHz) */
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
 */
utlp_hal_timer_err_t utlp_hal_timer_deinit(void);

/**
 * @brief Get timer capabilities
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
 */
uint32_t utlp_hal_timer_get_period(void);

/**
 * @brief Reset period to nominal (from config)
 */
utlp_hal_timer_err_t utlp_hal_timer_reset_period(void);

/*============================================================================
 * CONTROL
 *==========================================================================*/

/**
 * @brief Start timer
 */
utlp_hal_timer_err_t utlp_hal_timer_start(void);

/**
 * @brief Stop timer
 */
utlp_hal_timer_err_t utlp_hal_timer_stop(void);

/**
 * @brief Check if timer is running
 */
bool utlp_hal_timer_is_running(void);

/*============================================================================
 * CRITICAL SECTIONS
 *==========================================================================*/

/**
 * @brief Enter critical section (disable interrupts)
 * @return State to pass to exit_critical
 */
uint32_t utlp_hal_timer_enter_critical(void);

/**
 * @brief Exit critical section
 * @param state  Value from enter_critical
 */
void utlp_hal_timer_exit_critical(uint32_t state);

#ifdef __cplusplus
}
#endif

#endif /* UTLP_HAL_TIMER_H */
