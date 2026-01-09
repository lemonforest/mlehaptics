/**
 * @file utlp_phase.c
 * @brief UTLP Hardware Phase Engine - MCPWM Implementation
 *
 * "Physics First: Hardware defines time, not software."
 *
 * This module implements Hardware Phase Locked Atomic Coherency (HPLAC) using
 * the ESP32-C6 MCPWM peripheral as the single source of phase truth.
 *
 * @section key_features Key Features
 *
 * - **Single-Register Atomic Phase**: 50kHz × 50000 ticks = 1 second
 * - **Hardware Sync**: MCPWM soft sync for instant phase jam
 * - **Spectral Purity**: Period bending for frequency slewing
 * - **Variable Gain PLL**: COLD → LOCKED → RECOVERY state machine
 *
 * @section atomicity Atomicity Guarantees
 *
 * All critical sections use `portMUX_TYPE` spinlock to:
 * 1. Prevent execution jitter during hard sync
 * 2. Prevent torn reads of 64-bit values
 * 3. Ensure period reset during hard sync (no "sticky slew")
 *
 * @version 1.0.0
 * @date 2026-01-03
 *
 * @copyright
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#include "utlp_phase.h"
#include "utlp_config.h"
#include "utlp_hal.h"

#ifdef ESP_PLATFORM
#include "driver/mcpwm_timer.h"
#include "driver/mcpwm_sync.h"
#include "hal/mcpwm_ll.h"     /* Low-level API for reading timer count */
#include "soc/mcpwm_struct.h" /* Hardware register definitions */
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/portmacro.h"
#include <string.h>

static const char *TAG = "UTLP_PHASE";

/*============================================================================
 * MODULE STATE
 *
 * "Physics First: Hardware defines time."
 *==========================================================================*/

/** @brief Module spinlock for all critical sections (Purple Team fix) */
static portMUX_TYPE s_phase_spinlock = portMUX_INITIALIZER_UNLOCKED;

/** @brief Phase engine state (truck-packed) */
static utlp_phase_state_t s_state = {0};

/** @brief MCPWM timer handle */
static mcpwm_timer_handle_t s_phase_timer = NULL;

/** @brief MCPWM soft sync handle */
static mcpwm_sync_handle_t s_soft_sync = NULL;

/** @brief Initialization flag */
static bool s_initialized = false;

/*============================================================================
 * INTERRUPT LATENCY COMPENSATION (ILC) STATE
 *
 * "The Body Learns Its Own ISR Timing"
 *
 * These variables implement proprioceptive learning for the phase timer ISR.
 * When the ISR fires late (due to interrupt arbiter), we learn to fire the
 * timer EARLIER to compensate, ensuring LED actuation at physics truth time.
 *
 * Thread Safety:
 * - g_learned_isr_latency_us: Written from ISR, read from getter. Volatile
 *   ensures visibility. 32-bit reads are atomic on ESP32.
 * - g_isr_target_time_us: Written AND read only from ISR context. Safe because
 *   ISR cannot interrupt itself. Set to 0 at end of each cycle (expects count=0).
 *==========================================================================*/

/**
 * @brief Learned ISR latency buffer (microseconds)
 *
 * Starts at conservative UTLP_ILC_INITIAL_US (1ms) and converges to
 * actual platform characteristics (~5µs for Single Stack, ~50µs for Dual).
 *
 * IRAM_ATTR: Accessed from phase timer ISR.
 */
static volatile uint32_t g_learned_isr_latency_us = UTLP_ILC_INITIAL_US;

/**
 * @brief Target ISR fire time (microseconds, esp_timer epoch)
 *
 * Set before arming the phase timer. The ISR compares its actual entry time
 * to this value to compute the latency error.
 *
 * Value UINT64_MAX indicates "no pending target" (consumed or not yet set).
 * Value 0 indicates "expect ISR when timer count = 0" (normal operation).
 *
 * IRAM_ATTR: Accessed from phase timer ISR.
 */
#define ILC_TARGET_INACTIVE UINT64_MAX
static volatile uint64_t g_isr_target_time_us = ILC_TARGET_INACTIVE;

/*============================================================================
 * ISR CALLBACK
 *
 * Minimal ISR - only increments cycle_count for absolute time derivation.
 * Fires once per second at cycle boundary (timer empty).
 *==========================================================================*/

/**
 * @brief Phase timer ISR - Cycle tracking + ILC Learning
 *
 * MCPWM timer empty event handler. Fires once per second (at counter wrap).
 * Does two things:
 *   1. Increments cycle_count for absolute time derivation
 *   2. Measures ISR latency for ILC learning
 *
 * @note IRAM_ATTR: Fast interrupt RAM for deterministic latency.
 * @note ISR context is inherently atomic (no preemption on same core).
 * @note cycle_count read requires critical section in getter (torn read hazard).
 *
 * @see UTLP_ILC_* constants in utlp_config.h
 */
static bool IRAM_ATTR phase_timer_empty_isr(mcpwm_timer_handle_t timer,
                                             const mcpwm_timer_event_data_t *edata,
                                             void *user_ctx)
{
    (void)timer;
    (void)user_ctx;

    /* Increment cycle count for absolute time derivation */
    s_state.cycle_count++;

    /*=========================================================================
     * ILC: Interrupt Latency Compensation Learning Loop
     *
     * Measure how late this ISR fired relative to target, then update
     * learned latency for the next cycle's pre-fire compensation.
     *
     * Target = 0 means we expect the ISR to fire when timer count = 0.
     * Actual = timer count × tick_us = how far past count=0 we actually are.
     * Error = actual - target = ISR dispatch latency (should be positive).
     *
     * CRITICAL: This runs in ISR context. Keep it minimal.
     *========================================================================*/
    uint64_t target = g_isr_target_time_us;
    if (target != ILC_TARGET_INACTIVE) {
        /*
         * Capture actual ISR entry time.
         *
         * We use the MCPWM event timestamp (timer count × tick duration).
         * For an EMPTY event (counter wrap), count_value represents how many
         * ticks have elapsed since the wrap - i.e., the ISR dispatch delay.
         *
         * Example: If ISR fires when count=3, actual = 3 × 20µs = 60µs late.
         */
        uint64_t actual = (uint64_t)edata->count_value * UTLP_PHASE_TICK_US;

        /* Calculate latency error (32-bit math for rollover safety) */
        int32_t error_us = (int32_t)((uint32_t)actual - (uint32_t)target);

        /* Read current latency (32-bit atomic on ESP32) */
        uint32_t current = g_learned_isr_latency_us;
        uint32_t new_latency = current;

        if (error_us > (int32_t)UTLP_ILC_DEADZONE_US) {
            /*
             * LATE: ISR fired after target. Need MORE pre-fire.
             *
             * Increase latency buffer by error/divisor (EMA learning).
             * Minimum increase of 1µs to ensure convergence.
             */
            uint32_t increase = (uint32_t)error_us / UTLP_ILC_LEARN_DIVISOR;
            if (increase < 1) increase = 1;
            new_latency = current + increase;
            if (new_latency > UTLP_ILC_MAX_US) {
                new_latency = UTLP_ILC_MAX_US;
            }
        }
        else if (error_us < -(int32_t)UTLP_ILC_DEADZONE_US) {
            /*
             * EARLY: ISR fired before target. Can reduce pre-fire.
             *
             * Decay slowly to find minimum necessary buffer.
             * Never go below ILC_MIN_US floor.
             */
            if (current > UTLP_ILC_MIN_US + UTLP_ILC_DECAY_US) {
                new_latency = current - UTLP_ILC_DECAY_US;
            } else {
                new_latency = UTLP_ILC_MIN_US;
            }
        }
        /* ELSE: Within deadzone - perfect, no learning needed */

        /* Write back if changed */
        if (new_latency != current) {
            g_learned_isr_latency_us = new_latency;
        }
    }

    /*
     * Bootstrap: Set target for NEXT cycle.
     *
     * We expect the next ISR to fire when timer count = 0 (at wrap).
     * This enables learning from the very next cycle.
     */
    g_isr_target_time_us = 0;

    return false;  /* No high-priority task woken */
}

/*============================================================================
 * INITIALIZATION
 *==========================================================================*/

esp_err_t utlp_phase_init(void)
{
    if (s_initialized) {
        ESP_LOGW(TAG, "Phase engine already initialized");
        return ESP_OK;
    }

    ESP_LOGI(TAG, "Initializing MCPWM Phase Engine (HPLAC)");
    ESP_LOGI(TAG, "  Resolution: %lu Hz (%lu µs/tick)",
             UTLP_PHASE_TIMER_RESOLUTION_HZ, UTLP_PHASE_TICK_US);
    ESP_LOGI(TAG, "  Period: %lu ticks = %lu µs",
             UTLP_PHASE_PERIOD_TICKS, UTLP_PHASE_CYCLE_US);
    ESP_LOGI(TAG, "  Phase granularity: %lu µs = 0.0072°",
             UTLP_PHASE_TICK_US);

    /* Initialize state */
    memset(&s_state, 0, sizeof(s_state));
    s_state.current_period_ticks = UTLP_PHASE_PERIOD_TICKS;
    s_state.sync_state = UTLP_PHASE_STATE_COLD;

    /* Configure MCPWM timer as Phase Master */
    mcpwm_timer_config_t timer_config = {
        .group_id = UTLP_PHASE_MCPWM_GROUP,
        .clk_src = MCPWM_TIMER_CLK_SRC_DEFAULT,
        .resolution_hz = UTLP_PHASE_TIMER_RESOLUTION_HZ,
        .period_ticks = UTLP_PHASE_PERIOD_TICKS,
        .count_mode = MCPWM_TIMER_COUNT_MODE_UP,
        .flags = {
            .update_period_on_empty = true,   /* Period change at cycle end */
            .update_period_on_sync = true,    /* Period change on sync */
        },
    };

    esp_err_t ret = mcpwm_new_timer(&timer_config, &s_phase_timer);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to create MCPWM timer: %s", esp_err_to_name(ret));
        return ret;
    }

    /* Create soft sync source for hard sync capability */
    mcpwm_soft_sync_config_t sync_config = {};
    ret = mcpwm_new_soft_sync_src(&sync_config, &s_soft_sync);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to create soft sync: %s", esp_err_to_name(ret));
        mcpwm_del_timer(s_phase_timer);
        s_phase_timer = NULL;
        return ret;
    }

    /* Register cycle boundary ISR for absolute time */
    mcpwm_timer_event_callbacks_t cbs = {
        .on_empty = phase_timer_empty_isr,
    };
    ret = mcpwm_timer_register_event_callbacks(s_phase_timer, &cbs, NULL);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to register timer callback: %s", esp_err_to_name(ret));
        mcpwm_del_sync_src(s_soft_sync);
        mcpwm_del_timer(s_phase_timer);
        s_soft_sync = NULL;
        s_phase_timer = NULL;
        return ret;
    }

    /* Enable and start timer */
    ret = mcpwm_timer_enable(s_phase_timer);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to enable timer: %s", esp_err_to_name(ret));
        mcpwm_del_sync_src(s_soft_sync);
        mcpwm_del_timer(s_phase_timer);
        s_soft_sync = NULL;
        s_phase_timer = NULL;
        return ret;
    }

    ret = mcpwm_timer_start_stop(s_phase_timer, MCPWM_TIMER_START_NO_STOP);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to start timer: %s", esp_err_to_name(ret));
        mcpwm_timer_disable(s_phase_timer);
        mcpwm_del_sync_src(s_soft_sync);
        mcpwm_del_timer(s_phase_timer);
        s_soft_sync = NULL;
        s_phase_timer = NULL;
        return ret;
    }

    s_initialized = true;
    ESP_LOGI(TAG, "Phase engine initialized - Physics First!");
    return ESP_OK;
}

esp_err_t utlp_phase_deinit(void)
{
    if (!s_initialized) {
        return ESP_OK;
    }

    ESP_LOGI(TAG, "Deinitializing phase engine");

    if (s_phase_timer) {
        mcpwm_timer_start_stop(s_phase_timer, MCPWM_TIMER_STOP_EMPTY);
        mcpwm_timer_disable(s_phase_timer);
        mcpwm_del_timer(s_phase_timer);
        s_phase_timer = NULL;
    }

    if (s_soft_sync) {
        mcpwm_del_sync_src(s_soft_sync);
        s_soft_sync = NULL;
    }

    s_initialized = false;
    return ESP_OK;
}

/*============================================================================
 * PHASE QUERY
 *==========================================================================*/

uint32_t utlp_phase_get_ticks(void)
{
    if (!s_initialized || !s_phase_timer) {
        return 0;
    }

    /* Use Low-Level API to read timer counter (high-level API not available) */
    mcpwm_dev_t *hw = MCPWM_LL_GET_HW(UTLP_PHASE_MCPWM_GROUP);
    uint32_t count = mcpwm_ll_timer_get_count_value(hw, UTLP_PHASE_MCPWM_TIMER);
    return count;
}

uint16_t utlp_phase_get_angle(void)
{
    uint32_t ticks = utlp_phase_get_ticks();
    /* ticks / PERIOD_TICKS * 360 = degrees */
    return (uint16_t)((ticks * 360UL) / UTLP_PHASE_PERIOD_TICKS);
}

uint16_t utlp_phase_get_angle_x10(void)
{
    uint32_t ticks = utlp_phase_get_ticks();
    /* ticks / PERIOD_TICKS * 3600 = 0.1 degree units */
    return (uint16_t)((ticks * 3600UL) / UTLP_PHASE_PERIOD_TICKS);
}

uint64_t utlp_phase_get_cycle_count(void)
{
    /* CRITICAL: Use critical section to prevent torn reads (Purple Team Pitfall 2) */
    portENTER_CRITICAL(&s_phase_spinlock);
    uint64_t count = s_state.cycle_count;
    portEXIT_CRITICAL(&s_phase_spinlock);
    return count;
}

esp_err_t utlp_phase_get_state(utlp_phase_state_t *state)
{
    if (!state) {
        return ESP_ERR_INVALID_ARG;
    }

    portENTER_CRITICAL(&s_phase_spinlock);
    memcpy(state, &s_state, sizeof(utlp_phase_state_t));
    portEXIT_CRITICAL(&s_phase_spinlock);

    return ESP_OK;
}

/*============================================================================
 * SYNCHRONIZATION
 *==========================================================================*/

esp_err_t utlp_phase_hard_sync(uint32_t target_ticks)
{
    if (!s_initialized || !s_phase_timer || !s_soft_sync) {
        return ESP_ERR_INVALID_STATE;
    }

    if (target_ticks >= UTLP_PHASE_PERIOD_TICKS) {
        ESP_LOGW(TAG, "Target ticks %lu exceeds period, clamping", target_ticks);
        target_ticks = UTLP_PHASE_PERIOD_TICKS - 1;
    }

    /*
     * CRITICAL SECTION (Purple Team fixes):
     * 1. Prevents execution jitter (Pitfall 1)
     * 2. Resets period to nominal (Pitfall 3 - Sticky Slew)
     */
    portENTER_CRITICAL(&s_phase_spinlock);

    /* 1. Reset Period to Nominal (Fix "Sticky Slew" - stop running fast/slow) */
    mcpwm_timer_set_period(s_phase_timer, UTLP_PHASE_PERIOD_TICKS);
    s_state.current_period_ticks = UTLP_PHASE_PERIOD_TICKS;
    s_state.slewing = false;
    s_state.drift_accumulator_ppb = 0;

    /* 2. Configure Sync Phase */
    mcpwm_timer_sync_phase_config_t sync_config = {
        .sync_src = s_soft_sync,
        .count_value = target_ticks,
        .direction = MCPWM_TIMER_DIRECTION_UP,
    };
    mcpwm_timer_set_phase_on_sync(s_phase_timer, &sync_config);

    /* 3. Fire! Counter teleports (atomic - no ISR can insert jitter) */
    mcpwm_soft_sync_activate(s_soft_sync);

    /* Update state */
    s_state.last_sync_timestamp_us = utlp_hal_get_micros();

    portEXIT_CRITICAL(&s_phase_spinlock);

    ESP_LOGI(TAG, "Hard sync to tick %lu (%.1f°)",
             target_ticks,
             (float)target_ticks * 360.0f / UTLP_PHASE_PERIOD_TICKS);

    return ESP_OK;
}

esp_err_t utlp_phase_slew(int32_t error_ticks)
{
    if (!s_initialized || !s_phase_timer) {
        return ESP_ERR_INVALID_STATE;
    }

    /* Apply deadband - ignore small errors */
    if (error_ticks > -(int32_t)UTLP_PHASE_DEADBAND_TICKS &&
        error_ticks < (int32_t)UTLP_PHASE_DEADBAND_TICKS) {
        /* Error within deadband, reset to nominal period */
        if (s_state.slewing) {
            portENTER_CRITICAL(&s_phase_spinlock);
            mcpwm_timer_set_period(s_phase_timer, UTLP_PHASE_PERIOD_TICKS);
            s_state.current_period_ticks = UTLP_PHASE_PERIOD_TICKS;
            s_state.slewing = false;
            portEXIT_CRITICAL(&s_phase_spinlock);
        }
        return ESP_OK;
    }

    /*
     * Calculate period adjustment:
     * - Positive error = we are behind → reduce period (speed up)
     * - Negative error = we are ahead → increase period (slow down)
     *
     * delta_ticks = (error × PERIOD) / CONVERGENCE_TICKS
     */
    int32_t delta_ticks = (error_ticks * (int32_t)UTLP_PHASE_PERIOD_TICKS) /
                          (int32_t)UTLP_PHASE_CONVERGENCE_TICKS;

    /* Clamp to max slew (±0.5% = ±250 ticks at 50000) */
    if (delta_ticks > (int32_t)UTLP_PHASE_SLEW_MAX_TICKS) {
        delta_ticks = (int32_t)UTLP_PHASE_SLEW_MAX_TICKS;
    } else if (delta_ticks < -(int32_t)UTLP_PHASE_SLEW_MAX_TICKS) {
        delta_ticks = -(int32_t)UTLP_PHASE_SLEW_MAX_TICKS;
    }

    /* Calculate new period */
    uint32_t new_period = UTLP_PHASE_PERIOD_TICKS - (uint32_t)delta_ticks;

    portENTER_CRITICAL(&s_phase_spinlock);
    mcpwm_timer_set_period(s_phase_timer, new_period);
    s_state.current_period_ticks = new_period;
    s_state.slewing = true;
    s_state.last_error_ticks = (uint16_t)((error_ticks < 0) ? -error_ticks : error_ticks);
    portEXIT_CRITICAL(&s_phase_spinlock);

    ESP_LOGD(TAG, "Slew: error=%ld ticks, delta=%ld, period=%lu",
             (long)error_ticks, (long)delta_ticks, new_period);

    return ESP_OK;
}

esp_err_t utlp_phase_on_beacon(uint32_t peer_tx_phase_ticks, uint64_t rx_timestamp_us)
{
    if (!s_initialized) {
        return ESP_ERR_INVALID_STATE;
    }

    /* Get current local phase */
    uint32_t local_ticks = utlp_phase_get_ticks();

    /* Calculate phase error (peer - local) */
    int32_t error_ticks = (int32_t)peer_tx_phase_ticks - (int32_t)local_ticks;

    /* Handle wrap-around (choose shortest path) */
    if (error_ticks > (int32_t)(UTLP_PHASE_PERIOD_TICKS / 2)) {
        error_ticks -= (int32_t)UTLP_PHASE_PERIOD_TICKS;
    } else if (error_ticks < -(int32_t)(UTLP_PHASE_PERIOD_TICKS / 2)) {
        error_ticks += (int32_t)UTLP_PHASE_PERIOD_TICKS;
    }

    /* Update error history for quality calculation */
    portENTER_CRITICAL(&s_phase_spinlock);
    s_state.error_history[s_state.error_history_idx] =
        (uint16_t)((error_ticks < 0) ? -error_ticks : error_ticks);
    s_state.error_history_idx = (s_state.error_history_idx + 1) % 4;
    s_state.last_beacon_timestamp_us = rx_timestamp_us;
    portEXIT_CRITICAL(&s_phase_spinlock);

    /* Select sync method based on state */
    uint8_t state = s_state.sync_state;

    if (state == UTLP_PHASE_STATE_COLD) {
        /* Cold Start: Use hard sync for fast acquisition */
        uint32_t target = peer_tx_phase_ticks;
        if (target >= UTLP_PHASE_PERIOD_TICKS) {
            target = 0;
        }
        return utlp_phase_hard_sync(target);
    } else {
        /* Locked/Recovery: Use soft slew to preserve spectral purity */
        return utlp_phase_slew(error_ticks);
    }
}

/*============================================================================
 * MAINTENANCE
 *==========================================================================*/

void utlp_phase_tick(uint64_t uptime_us)
{
    if (!s_initialized) {
        return;
    }

    /* State transition: COLD → LOCKED after cold start period */
    if (s_state.sync_state == UTLP_PHASE_STATE_COLD) {
        if (uptime_us >= UTLP_PHASE_COLD_START_US) {
            /*
             * BUG FIX (Coherence Oscillation Audit - Bug #4):
             * Reset timer period to nominal at state transition.
             *
             * During COLD, hard syncs reset period to nominal, but slews
             * (which bend the period) do not. If the last action was a slew,
             * the bent period persists into LOCKED state, causing residual
             * drift that looks like coherence oscillation.
             *
             * Solution: Always reset to nominal when transitioning to LOCKED.
             * This ensures a clean starting point for soft slew mode.
             */
            portENTER_CRITICAL(&s_phase_spinlock);
            mcpwm_timer_set_period(s_phase_timer, UTLP_PHASE_PERIOD_TICKS);
            s_state.current_period_ticks = UTLP_PHASE_PERIOD_TICKS;
            s_state.slewing = false;
            s_state.drift_accumulator_ppb = 0;
            s_state.sync_state = UTLP_PHASE_STATE_LOCKED;
            portEXIT_CRITICAL(&s_phase_spinlock);
            ESP_LOGI(TAG, "Transition: COLD → LOCKED (hard sync disabled, period reset to nominal)");
        }
    }

    /* Calculate sync quality from error history */
    uint32_t avg_error = 0;
    for (int i = 0; i < 4; i++) {
        avg_error += s_state.error_history[i];
    }
    avg_error /= 4;

    /* Quality: 100% at 0 error, 0% at PERIOD_TICKS/4 error */
    uint8_t quality;
    if (avg_error >= UTLP_PHASE_PERIOD_TICKS / 4) {
        quality = 0;
    } else {
        quality = (uint8_t)(100 - (avg_error * 400 / UTLP_PHASE_PERIOD_TICKS));
    }

    portENTER_CRITICAL(&s_phase_spinlock);
    s_state.sync_quality = quality;
    portEXIT_CRITICAL(&s_phase_spinlock);

    /* State transition: LOCKED ↔ RECOVERY based on error threshold */
    if (s_state.sync_state == UTLP_PHASE_STATE_LOCKED) {
        uint32_t threshold_ticks = UTLP_SERVO_LOCKED_THRESHOLD_US / UTLP_PHASE_TICK_US;
        if (avg_error > threshold_ticks) {
            portENTER_CRITICAL(&s_phase_spinlock);
            s_state.sync_state = UTLP_PHASE_STATE_RECOVERY;
            portEXIT_CRITICAL(&s_phase_spinlock);
            ESP_LOGW(TAG, "Transition: LOCKED → RECOVERY (error=%lu ticks)", avg_error);
        }
    } else if (s_state.sync_state == UTLP_PHASE_STATE_RECOVERY) {
        uint32_t threshold_ticks = UTLP_SERVO_LOCKED_THRESHOLD_US / UTLP_PHASE_TICK_US;
        if (avg_error < threshold_ticks / 2) {  /* Hysteresis */
            portENTER_CRITICAL(&s_phase_spinlock);
            s_state.sync_state = UTLP_PHASE_STATE_LOCKED;
            portEXIT_CRITICAL(&s_phase_spinlock);
            ESP_LOGI(TAG, "Transition: RECOVERY → LOCKED (error=%lu ticks)", avg_error);
        }
    }
}

uint8_t utlp_phase_get_quality(void)
{
    return s_state.sync_quality;
}

bool utlp_phase_is_synchronized(void)
{
    return (s_state.sync_state == UTLP_PHASE_STATE_LOCKED) &&
           (s_state.sync_quality >= 50);
}

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
 * @see phase_timer_empty_isr() for learning loop
 */
uint32_t utlp_phase_get_isr_latency_us(void)
{
    return g_learned_isr_latency_us;
}

/*============================================================================
 * BACKWARD COMPATIBILITY
 *==========================================================================*/

uint64_t utlp_phase_get_atomic_time_us(void)
{
    if (!s_initialized) {
        return 0;
    }

    /* CRITICAL: Prevent torn reads of 64-bit values (Purple Team Pitfall 2) */
    portENTER_CRITICAL(&s_phase_spinlock);
    uint64_t cycles = s_state.cycle_count;
    int64_t offset = s_state.epoch_offset_us;
    portEXIT_CRITICAL(&s_phase_spinlock);

    /* Get current phase ticks */
    uint32_t ticks = utlp_phase_get_ticks();

    /*
     * atomic_time = (cycle_count × CYCLE_US) + (ticks × TICK_US) + epoch_offset
     */
    return (cycles * UTLP_PHASE_CYCLE_US) +
           (ticks * UTLP_PHASE_TICK_US) +
           offset;
}

void utlp_phase_set_epoch_offset(int64_t offset_us)
{
    portENTER_CRITICAL(&s_phase_spinlock);
    s_state.epoch_offset_us = offset_us;
    portEXIT_CRITICAL(&s_phase_spinlock);

    ESP_LOGI(TAG, "Epoch offset set to %lld µs", (long long)offset_us);
}

int64_t utlp_phase_get_epoch_offset(void)
{
    portENTER_CRITICAL(&s_phase_spinlock);
    int64_t offset = s_state.epoch_offset_us;
    portEXIT_CRITICAL(&s_phase_spinlock);
    return offset;
}

#else  /* !ESP_PLATFORM - Native test stub */

/*============================================================================
 * NATIVE TEST STUBS
 *
 * Minimal stubs for compilation on native (non-ESP32) platforms.
 *==========================================================================*/

static utlp_phase_state_t s_state = {0};
static bool s_initialized = false;

esp_err_t utlp_phase_init(void) {
    s_initialized = true;
    s_state.current_period_ticks = UTLP_PHASE_PERIOD_TICKS;
    return ESP_OK;
}

esp_err_t utlp_phase_deinit(void) {
    s_initialized = false;
    return ESP_OK;
}

uint32_t utlp_phase_get_ticks(void) { return 0; }
uint16_t utlp_phase_get_angle(void) { return 0; }
uint16_t utlp_phase_get_angle_x10(void) { return 0; }
uint64_t utlp_phase_get_cycle_count(void) { return s_state.cycle_count; }

esp_err_t utlp_phase_get_state(utlp_phase_state_t *state) {
    if (state) *state = s_state;
    return ESP_OK;
}

esp_err_t utlp_phase_hard_sync(uint32_t target_ticks) {
    (void)target_ticks;
    return ESP_OK;
}

esp_err_t utlp_phase_slew(int32_t error_ticks) {
    (void)error_ticks;
    return ESP_OK;
}

esp_err_t utlp_phase_on_beacon(uint32_t peer_tx_phase_ticks, uint64_t rx_timestamp_us) {
    (void)peer_tx_phase_ticks;
    (void)rx_timestamp_us;
    return ESP_OK;
}

void utlp_phase_tick(uint64_t uptime_us) { (void)uptime_us; }
uint8_t utlp_phase_get_quality(void) { return 0; }
bool utlp_phase_is_synchronized(void) { return false; }
uint32_t utlp_phase_get_isr_latency_us(void) { return UTLP_ILC_INITIAL_US; }
uint64_t utlp_phase_get_atomic_time_us(void) { return 0; }
void utlp_phase_set_epoch_offset(int64_t offset_us) { s_state.epoch_offset_us = offset_us; }
int64_t utlp_phase_get_epoch_offset(void) { return s_state.epoch_offset_us; }

#endif /* ESP_PLATFORM */
