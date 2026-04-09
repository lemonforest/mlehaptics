/**
 * @file utlp_phase.c
 * @brief UTLP Hardware Phase Engine - HAL-Abstracted Implementation
 *
 * "Physics First: Hardware defines time, not software."
 *
 * This module implements Hardware Phase Locked Atomic Coherency (HPLAC)
 * via the platform-agnostic Timer HAL (utlp_hal_timer.h). The hardware
 * timer IS the truth - not a follower of software timing.
 *
 * @section key_features Key Features
 *
 * - **Single-Register Atomic Phase**: 50kHz × 50000 ticks = 1 second
 * - **Hardware Sync**: Instant phase jam via HAL hard_sync
 * - **Spectral Purity**: Period bending for frequency slewing
 * - **Variable Gain PLL**: COLD → LOCKED → RECOVERY state machine
 * - **Precision Windows**: Pause/resume for power-managed beacon timing
 * - **Anticipatory Memory**: Diagnostic prediction/scoring framework
 *
 * @section atomicity Atomicity Guarantees
 *
 * All critical sections use Timer HAL's enter/exit_critical to:
 * 1. Prevent execution jitter during hard sync
 * 2. Prevent torn reads of 64-bit values
 * 3. Ensure period reset during hard sync (no "sticky slew")
 *
 * @version 2.0.0
 * @date 2026-03-04
 *
 * @copyright
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#include "utlp_phase.h"
#include "utlp_hal_timer.h"
#include "utlp_config.h"
#include "utlp_hal.h"

#ifdef ESP_PLATFORM
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

/** @brief Phase engine state (truck-packed) */
static utlp_phase_state_t s_state = {0};

/** @brief Initialization flag */
static bool s_initialized = false;

/*============================================================================
 * PRECISION WINDOW STATE
 *
 * Pause/resume support for power-managed beacon timing.
 * Timer OFF during sleep, ON during beacon windows.
 *==========================================================================*/

/** @brief Phase engine is paused (timer stopped, waiting for resume) */
static bool s_paused = false;

/** @brief esp_timer timestamp when phase engine was paused */
static uint64_t s_pause_timestamp_us = 0;

/** @brief Timer elapsed microseconds captured at pause */
static uint64_t s_pause_elapsed_us = 0;

/** @brief Precision Window orchestrator state */
typedef enum {
    PRECISION_CONTINUOUS = 0,   /**< Timer always on (boot/bootstrap) */
    PRECISION_AWAKE,            /**< Timer on during beacon window */
    PRECISION_SLEEPING,         /**< Timer off, RTC tracking time */
    PRECISION_STATE_COUNT       /**< Sentinel */
} precision_state_t;

static precision_state_t s_precision_state = PRECISION_CONTINUOUS;

/** @brief Consecutive missed beacons in precision mode */
static uint8_t s_precision_misses = 0;

/** @brief Predicted next beacon arrival (esp_timer epoch) */
static uint64_t s_next_beacon_predicted_us = 0;

/** @brief Last beacon arrival (esp_timer epoch) */
static uint64_t s_last_beacon_arrival_us = 0;

/*============================================================================
 * ANTICIPATORY MEMORY STATE
 *
 * Diagnostic-first: log predictions vs. reality.
 * NOT used for timing control yet.
 *==========================================================================*/

static utlp_anticipatory_state_t s_anticipatory = {0};

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
 * ISR CALLBACK (via Timer HAL)
 *
 * Minimal ISR - only increments cycle_count for absolute time derivation.
 * Fires once per second at cycle boundary (timer empty).
 *
 * Registered with the Timer HAL as the on_cycle callback.
 *==========================================================================*/

/**
 * @brief Phase timer cycle callback - Cycle tracking + ILC Learning
 *
 * Timer HAL cycle boundary handler. Fires once per second (at counter wrap).
 * Does two things:
 *   1. Increments cycle_count for absolute time derivation
 *   2. Measures ISR latency for ILC learning
 *
 * @note IRAM_ATTR: Fast interrupt RAM for deterministic latency.
 * @note ISR context is inherently atomic (no preemption on same core).
 * @note cycle_count read requires critical section in getter (torn read hazard).
 *
 * @param user_ctx      Unused context pointer
 * @param count_at_isr  Timer count at ISR entry (for latency measurement)
 * @return false (no high-priority task woken)
 *
 * @see UTLP_ILC_* constants in utlp_config.h
 */
static bool IRAM_ATTR phase_timer_cycle_callback(void *user_ctx,
                                                  uint32_t count_at_isr)
{
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
         * For an EMPTY event (counter wrap), count_at_isr represents how many
         * ticks have elapsed since the wrap - i.e., the ISR dispatch delay.
         *
         * Example: If ISR fires when count=3, actual = 3 × 20µs = 60µs late.
         */
        uint64_t actual = (uint64_t)count_at_isr * UTLP_PHASE_TICK_US;

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

    ESP_LOGI(TAG, "Initializing Phase Engine (HPLAC) via Timer HAL");
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

    /* Initialize anticipatory memory */
    memset(&s_anticipatory, 0, sizeof(s_anticipatory));

    /* Reset precision window state */
    s_paused = false;
    s_precision_state = PRECISION_CONTINUOUS;
    s_precision_misses = 0;

    /* Configure Timer HAL with phase engine callback */
    utlp_hal_timer_config_t timer_config = {
        .resolution_hz = UTLP_PHASE_TIMER_RESOLUTION_HZ,
        .period_ticks = UTLP_PHASE_PERIOD_TICKS,
        .on_cycle = phase_timer_cycle_callback,
        .user_ctx = NULL,
    };

    utlp_hal_timer_err_t err = utlp_hal_timer_init(&timer_config);
    if (err != UTLP_TIMER_OK) {
        ESP_LOGE(TAG, "Failed to initialize Timer HAL: %d", (int)err);
        return ESP_FAIL;
    }

    /* Start timer */
    err = utlp_hal_timer_start();
    if (err != UTLP_TIMER_OK) {
        ESP_LOGE(TAG, "Failed to start Timer HAL: %d", (int)err);
        utlp_hal_timer_deinit();
        return ESP_FAIL;
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

    utlp_hal_timer_deinit();

    s_initialized = false;
    s_paused = false;
    s_precision_state = PRECISION_CONTINUOUS;
    return ESP_OK;
}

/*============================================================================
 * PHASE QUERY
 *==========================================================================*/

uint32_t utlp_phase_get_ticks(void)
{
    if (!s_initialized) {
        return 0;
    }

    return utlp_hal_timer_get_ticks();
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
    uint32_t cs = utlp_hal_timer_enter_critical();
    uint64_t count = s_state.cycle_count;
    utlp_hal_timer_exit_critical(cs);
    return count;
}

esp_err_t utlp_phase_get_state(utlp_phase_state_t *state)
{
    if (!state) {
        return ESP_ERR_INVALID_ARG;
    }

    uint32_t cs = utlp_hal_timer_enter_critical();
    memcpy(state, &s_state, sizeof(utlp_phase_state_t));
    utlp_hal_timer_exit_critical(cs);

    return ESP_OK;
}

/*============================================================================
 * SYNCHRONIZATION
 *==========================================================================*/

esp_err_t utlp_phase_hard_sync(uint32_t target_ticks)
{
    if (!s_initialized) {
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
     *
     * Note: The HAL's hard_sync already resets period to nominal internally,
     * but we also need to update our local state under the same critical section.
     */
    uint32_t cs = utlp_hal_timer_enter_critical();

    s_state.current_period_ticks = UTLP_PHASE_PERIOD_TICKS;
    s_state.slewing = false;
    s_state.drift_accumulator_ppb = 0;
    s_state.last_sync_timestamp_us = utlp_hal_get_micros();

    utlp_hal_timer_exit_critical(cs);

    /* HAL hard sync handles the actual hardware teleport + period reset */
    utlp_hal_timer_err_t err = utlp_hal_timer_hard_sync(target_ticks);
    if (err != UTLP_TIMER_OK) {
        ESP_LOGE(TAG, "Hard sync failed: %d", (int)err);
        return ESP_FAIL;
    }

    ESP_LOGI(TAG, "Hard sync to tick %lu (%.1f°)",
             target_ticks,
             (float)target_ticks * 360.0f / UTLP_PHASE_PERIOD_TICKS);

    return ESP_OK;
}

esp_err_t utlp_phase_slew(int32_t error_ticks)
{
    if (!s_initialized) {
        return ESP_ERR_INVALID_STATE;
    }

    /* Apply deadband - ignore small errors */
    if (error_ticks > -(int32_t)UTLP_PHASE_DEADBAND_TICKS &&
        error_ticks < (int32_t)UTLP_PHASE_DEADBAND_TICKS) {
        /* Error within deadband, reset to nominal period */
        if (s_state.slewing) {
            utlp_hal_timer_reset_period();

            uint32_t cs = utlp_hal_timer_enter_critical();
            s_state.current_period_ticks = UTLP_PHASE_PERIOD_TICKS;
            s_state.slewing = false;
            utlp_hal_timer_exit_critical(cs);
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

    utlp_hal_timer_set_period(new_period);

    uint32_t cs = utlp_hal_timer_enter_critical();
    s_state.current_period_ticks = new_period;
    s_state.slewing = true;
    s_state.last_error_ticks = (uint16_t)((error_ticks < 0) ? -error_ticks : error_ticks);
    utlp_hal_timer_exit_critical(cs);

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
    uint32_t cs = utlp_hal_timer_enter_critical();
    s_state.error_history[s_state.error_history_idx] =
        (uint16_t)((error_ticks < 0) ? -error_ticks : error_ticks);
    s_state.error_history_idx = (s_state.error_history_idx + 1) % 4;
    s_state.last_beacon_timestamp_us = rx_timestamp_us;
    utlp_hal_timer_exit_critical(cs);

    /* Track beacon arrival for anticipatory memory */
    s_last_beacon_arrival_us = utlp_hal_get_micros();

    /* Reset precision miss counter on successful beacon */
    if (s_precision_state == PRECISION_AWAKE) {
        s_precision_misses = 0;
    }

    /* v3.12: Log phase error at each beacon for drift visibility.
     * This is the datum that shows whether LEDs are drifting apart. */
    {
        int32_t error_us = error_ticks * (int32_t)UTLP_PHASE_TICK_US;
        const char *state_names[] = {"COLD", "LOCKED", "RECOVERY"};
        const char *sn = (s_state.sync_state < 3) ? state_names[s_state.sync_state] : "?";
        ESP_LOGI(TAG, "PHASE: peer=%lu local=%lu error=%+ld ticks (%+ld us) [%s]",
                 (unsigned long)peer_tx_phase_ticks, (unsigned long)local_ticks,
                 (long)error_ticks, (long)error_us, sn);
    }

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
            utlp_hal_timer_reset_period();

            uint32_t cs = utlp_hal_timer_enter_critical();
            s_state.current_period_ticks = UTLP_PHASE_PERIOD_TICKS;
            s_state.slewing = false;
            s_state.drift_accumulator_ppb = 0;
            s_state.sync_state = UTLP_PHASE_STATE_LOCKED;
            utlp_hal_timer_exit_critical(cs);
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

    uint32_t cs = utlp_hal_timer_enter_critical();
    s_state.sync_quality = quality;
    utlp_hal_timer_exit_critical(cs);

    /* State transition: LOCKED ↔ RECOVERY based on error threshold */
    if (s_state.sync_state == UTLP_PHASE_STATE_LOCKED) {
        uint32_t threshold_ticks = UTLP_SERVO_LOCKED_THRESHOLD_US / UTLP_PHASE_TICK_US;
        if (avg_error > threshold_ticks) {
            cs = utlp_hal_timer_enter_critical();
            s_state.sync_state = UTLP_PHASE_STATE_RECOVERY;
            utlp_hal_timer_exit_critical(cs);
            ESP_LOGW(TAG, "Transition: LOCKED → RECOVERY (error=%lu ticks)", avg_error);
        }
    } else if (s_state.sync_state == UTLP_PHASE_STATE_RECOVERY) {
        uint32_t threshold_ticks = UTLP_SERVO_LOCKED_THRESHOLD_US / UTLP_PHASE_TICK_US;
        if (avg_error < threshold_ticks / 2) {  /* Hysteresis */
            cs = utlp_hal_timer_enter_critical();
            s_state.sync_state = UTLP_PHASE_STATE_LOCKED;
            utlp_hal_timer_exit_critical(cs);
            ESP_LOGI(TAG, "Transition: RECOVERY → LOCKED (error=%lu ticks)", avg_error);
        }
    }

    /*=========================================================================
     * Precision Window Orchestrator
     *
     * Manages timer ON/OFF transitions based on beacon prediction.
     * Only active when precision_state != CONTINUOUS.
     *========================================================================*/
    if (s_precision_state == PRECISION_AWAKE) {
        /* Check if trail time has expired (time to sleep) */
        uint64_t now = utlp_hal_get_micros();
        uint64_t trail_deadline = s_last_beacon_arrival_us + UTLP_PRECISION_WAKE_TRAIL_US;

        if (now > trail_deadline && s_last_beacon_arrival_us > 0) {
            /* Predict next beacon and compute wake time */
            /* Use steady-state interval as initial estimate */
            s_next_beacon_predicted_us = s_last_beacon_arrival_us + UTLP_BEACON_INTERVAL_STEADY_US;

            /* Pause phase engine */
            esp_err_t err = utlp_phase_pause();
            if (err == ESP_OK) {
                s_precision_state = PRECISION_SLEEPING;
                ESP_LOGD(TAG, "PRECISION: Sleeping until predicted beacon at +%llu s",
                         (unsigned long long)(s_next_beacon_predicted_us - now) / 1000000ULL);
            }
        }
    } else if (s_precision_state == PRECISION_SLEEPING) {
        /* Check if wake lead time has been reached */
        uint64_t now = utlp_hal_get_micros();
        uint64_t wake_time = s_next_beacon_predicted_us - UTLP_PRECISION_WAKE_LEAD_US;

        if (now >= wake_time) {
            /* Wake up for beacon window */
            esp_err_t err = utlp_phase_resume();
            if (err == ESP_OK) {
                s_precision_state = PRECISION_AWAKE;
                ESP_LOGD(TAG, "PRECISION: Awake for beacon window");
            }
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
 * @see phase_timer_cycle_callback() for learning loop
 */
uint32_t utlp_phase_get_isr_latency_us(void)
{
    return g_learned_isr_latency_us;
}

/*============================================================================
 * PRECISION WINDOW - Pause/Resume
 *==========================================================================*/

esp_err_t utlp_phase_pause(void)
{
    if (!s_initialized || s_paused) {
        return ESP_ERR_INVALID_STATE;
    }

    /* Capture elapsed time via HAL */
    uint64_t elapsed = 0;
    utlp_hal_timer_err_t err = utlp_hal_timer_pause(&elapsed);
    if (err != UTLP_TIMER_OK) {
        ESP_LOGE(TAG, "Timer HAL pause failed: %d", (int)err);
        return ESP_FAIL;
    }

    s_pause_elapsed_us = elapsed;
    s_pause_timestamp_us = utlp_hal_get_micros();
    s_paused = true;

    ESP_LOGI(TAG, "Phase engine paused (elapsed=%llu us, cycles=%llu)",
             (unsigned long long)elapsed,
             (unsigned long long)s_state.cycle_count);
    return ESP_OK;
}

esp_err_t utlp_phase_resume(void)
{
    if (!s_initialized || !s_paused) {
        return ESP_ERR_INVALID_STATE;
    }

    /* Reconstruct missed cycles from RTC */
    uint64_t rtc_now = utlp_hal_get_micros();
    uint64_t rtc_elapsed = rtc_now - s_pause_timestamp_us;

    /* Update cycle count with RTC-estimated cycles during pause */
    uint64_t missed_cycles = rtc_elapsed / UTLP_PHASE_CYCLE_US;

    uint32_t cs = utlp_hal_timer_enter_critical();
    s_state.cycle_count += missed_cycles;
    utlp_hal_timer_exit_critical(cs);

    /* Resume hardware timer */
    utlp_hal_timer_err_t err = utlp_hal_timer_resume();
    if (err != UTLP_TIMER_OK) {
        ESP_LOGE(TAG, "Timer HAL resume failed: %d", (int)err);
        return ESP_FAIL;
    }

    s_paused = false;

    ESP_LOGI(TAG, "Phase engine resumed (rtc_delta=%llu us, missed_cycles=%llu)",
             (unsigned long long)rtc_elapsed,
             (unsigned long long)missed_cycles);
    return ESP_OK;
}

bool utlp_phase_is_paused(void)
{
    return s_paused;
}

/*============================================================================
 * PRECISION WINDOW - Mode Control
 *==========================================================================*/

void utlp_phase_enable_precision_mode(void)
{
    if (s_precision_state != PRECISION_CONTINUOUS) {
        return;  /* Already in precision mode */
    }

    s_precision_state = PRECISION_AWAKE;
    s_precision_misses = 0;
    ESP_LOGI(TAG, "PRECISION: Mode enabled (timer will sleep between beacons)");
}

void utlp_phase_disable_precision_mode(void)
{
    if (s_precision_state == PRECISION_CONTINUOUS) {
        return;  /* Already continuous */
    }

    /* If sleeping, wake up first */
    if (s_precision_state == PRECISION_SLEEPING && s_paused) {
        utlp_phase_resume();
    }

    s_precision_state = PRECISION_CONTINUOUS;
    s_precision_misses = 0;
    ESP_LOGI(TAG, "PRECISION: Mode disabled (continuous timer)");
}

bool utlp_phase_is_precision_mode(void)
{
    return s_precision_state != PRECISION_CONTINUOUS;
}

/*============================================================================
 * ANTICIPATORY MEMORY - Diagnostic Framework
 *
 * Predict/observe/score beacon timing for future power optimization.
 * All devices maintain this — Genesis predicts its own schedule stability,
 * Followers predict upstream beacon arrivals.
 *==========================================================================*/

void utlp_anticipatory_predict(uint64_t expected_arrival_us, int64_t expected_offset_us)
{
    utlp_anticipatory_entry_t *entry =
        &s_anticipatory.history[s_anticipatory.history_idx];

    entry->predicted_arrival_us = expected_arrival_us;
    entry->predicted_offset_us = expected_offset_us;

    /* Clear reality fields (will be filled on observe) */
    entry->actual_arrival_us = 0;
    entry->actual_offset_us = 0;
    entry->arrival_error_us = 0;
    entry->offset_error_us = 0;
    entry->hit = false;

    s_anticipatory.total_predictions++;
}

void utlp_anticipatory_observe(uint64_t actual_arrival_us, int64_t actual_offset_us)
{
    utlp_anticipatory_entry_t *entry =
        &s_anticipatory.history[s_anticipatory.history_idx];

    /* Fill reality */
    entry->actual_arrival_us = actual_arrival_us;
    entry->actual_offset_us = actual_offset_us;

    /* Score this prediction */
    if (entry->predicted_arrival_us > 0) {
        entry->arrival_error_us = (int32_t)(
            (int64_t)actual_arrival_us - (int64_t)entry->predicted_arrival_us);
        entry->offset_error_us = (int32_t)(
            actual_offset_us - entry->predicted_offset_us);

        /* Hit = arrived within the precision wake window */
        int32_t abs_arrival_err = entry->arrival_error_us;
        if (abs_arrival_err < 0) abs_arrival_err = -abs_arrival_err;
        entry->hit = ((uint32_t)abs_arrival_err < UTLP_PRECISION_WAKE_LEAD_US);

        if (entry->hit) {
            s_anticipatory.total_hits++;
        }

        /* Update EMA of arrival error (α = 0.2 ≈ 1/5) */
        s_anticipatory.avg_arrival_error_us =
            s_anticipatory.avg_arrival_error_us -
            (s_anticipatory.avg_arrival_error_us / 5) +
            (entry->arrival_error_us / 5);

        /* Update EMA of offset error */
        s_anticipatory.avg_offset_error_us =
            s_anticipatory.avg_offset_error_us -
            (s_anticipatory.avg_offset_error_us / 5) +
            (entry->offset_error_us / 5);

        /* Update confidence: 100 * hits / predictions (capped at 100) */
        if (s_anticipatory.total_predictions > 0) {
            uint32_t pct = (uint32_t)s_anticipatory.total_hits * 100 /
                           s_anticipatory.total_predictions;
            if (pct > 100) pct = 100;
            s_anticipatory.confidence = (uint8_t)pct;
        }

        entry->confidence = s_anticipatory.confidence;
    }

    /* Advance ring buffer */
    s_anticipatory.history_idx =
        (s_anticipatory.history_idx + 1) % UTLP_ANTICIPATORY_HISTORY_SIZE;
}

uint8_t utlp_anticipatory_get_confidence(void)
{
    return s_anticipatory.confidence;
}

void utlp_anticipatory_log_state(void)
{
    ESP_LOGI(TAG, "ANTICIPATORY: confidence=%u%%, predictions=%u, hits=%u",
             s_anticipatory.confidence,
             s_anticipatory.total_predictions,
             s_anticipatory.total_hits);
    ESP_LOGI(TAG, "  avg_arrival_err=%+ld us, avg_offset_err=%+ld us",
             (long)s_anticipatory.avg_arrival_error_us,
             (long)s_anticipatory.avg_offset_error_us);
}

esp_err_t utlp_phase_get_anticipatory_state(utlp_anticipatory_state_t *state)
{
    if (!state) {
        return ESP_ERR_INVALID_ARG;
    }
    memcpy(state, &s_anticipatory, sizeof(utlp_anticipatory_state_t));
    return ESP_OK;
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
    uint32_t cs = utlp_hal_timer_enter_critical();
    uint64_t cycles = s_state.cycle_count;
    int64_t offset = s_state.epoch_offset_us;
    utlp_hal_timer_exit_critical(cs);

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
    uint32_t cs = utlp_hal_timer_enter_critical();
    s_state.epoch_offset_us = offset_us;
    utlp_hal_timer_exit_critical(cs);

    ESP_LOGI(TAG, "Epoch offset set to %lld µs", (long long)offset_us);
}

int64_t utlp_phase_get_epoch_offset(void)
{
    uint32_t cs = utlp_hal_timer_enter_critical();
    int64_t offset = s_state.epoch_offset_us;
    utlp_hal_timer_exit_critical(cs);
    return offset;
}

#else  /* !ESP_PLATFORM - Native test stub */

/*============================================================================
 * NATIVE TEST STUBS
 *
 * Minimal stubs for compilation on native (non-ESP32) platforms.
 *==========================================================================*/

#include <string.h>

static utlp_phase_state_t s_state = {0};
static bool s_initialized = false;
static bool s_paused = false;
static utlp_anticipatory_state_t s_anticipatory = {0};

esp_err_t utlp_phase_init(void) {
    s_initialized = true;
    s_state.current_period_ticks = UTLP_PHASE_PERIOD_TICKS;
    memset(&s_anticipatory, 0, sizeof(s_anticipatory));
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

/* Precision Window stubs */
esp_err_t utlp_phase_pause(void) { s_paused = true; return ESP_OK; }
esp_err_t utlp_phase_resume(void) { s_paused = false; return ESP_OK; }
bool utlp_phase_is_paused(void) { return s_paused; }
void utlp_phase_enable_precision_mode(void) {}
void utlp_phase_disable_precision_mode(void) {}
bool utlp_phase_is_precision_mode(void) { return false; }

/* Anticipatory Memory stubs */
void utlp_anticipatory_predict(uint64_t a, int64_t b) { (void)a; (void)b; }
void utlp_anticipatory_observe(uint64_t a, int64_t b) { (void)a; (void)b; }
uint8_t utlp_anticipatory_get_confidence(void) { return 0; }
void utlp_anticipatory_log_state(void) {}
esp_err_t utlp_phase_get_anticipatory_state(utlp_anticipatory_state_t *state) {
    if (state) memset(state, 0, sizeof(*state));
    return ESP_OK;
}

#endif /* ESP_PLATFORM */
