/**
 * @file utlp_phase.c
 * @brief UTLP Hardware Phase Engine - Vector Time Foundation
 *
 * "Time is a chord, not a number."
 *
 * This module implements Hardware Phase Locked Coherency (HPLC) using
 * the platform timer HAL. Time is represented NATIVELY as a phase chord -
 * 8 residues modulo coprime primes. Scalar time is DERIVED via CRT.
 *
 * @section key_features Key Features
 *
 * - **Vector Time Native**: phase_chord[8] is the primary representation
 * - **Single-Register Atomic Phase**: 10 MHz × 10000 ticks = 1 ms (100 ns resolution)
 * - **Hardware Sync**: Instant phase jam via HAL
 * - **Spectral Purity**: Period bending for frequency slewing
 * - **Variable Gain PLL**: COLD → LOCKED → RECOVERY state machine
 *
 * @section platform Platform Independence
 *
 * All hardware access goes through utlp_hal_timer.h:
 * - ESP32: MCPWM peripheral (utlp_hal_timer_esp32.c)
 * - Native: Software emulation (utlp_hal_timer_native.c)
 *
 * @version 3.0.0
 * @date 2026-01-09
 *
 * @copyright
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#include "utlp_phase.h"
#include "utlp_config.h"
#include "utlp_hal.h"
#include "utlp_hal_timer.h"

#include <string.h>

#ifdef ESP_PLATFORM
#include "esp_log.h"
#define LOG_INFO(tag, fmt, ...)  ESP_LOGI(tag, fmt, ##__VA_ARGS__)
#define LOG_WARN(tag, fmt, ...)  ESP_LOGW(tag, fmt, ##__VA_ARGS__)
#define LOG_DEBUG(tag, fmt, ...) ESP_LOGD(tag, fmt, ##__VA_ARGS__)
#else
#include <stdio.h>
#define LOG_INFO(tag, fmt, ...)  printf("[%s] " fmt "\n", tag, ##__VA_ARGS__)
#define LOG_WARN(tag, fmt, ...)  printf("[%s] WARN: " fmt "\n", tag, ##__VA_ARGS__)
#define LOG_DEBUG(tag, fmt, ...) ((void)0)
#endif

static const char *TAG = "UTLP_PHASE";

/*============================================================================
 * VECTOR TIME CONSTANTS - Protocol Primitive
 *
 * "Time is a chord, not a number."
 *==========================================================================*/

/** @brief The 8 coprime primes for phase chord representation */
static const uint8_t s_primes[UTLP_CHORD_SIZE] = UTLP_PRIMES_INIT;

/*============================================================================
 * MODULE STATE
 *==========================================================================*/

/** @brief Phase engine state */
static utlp_phase_state_t s_state = {0};

/** @brief Initialization flag */
static bool s_initialized = false;

/*============================================================================
 * INTERRUPT LATENCY COMPENSATION (ILC) STATE
 *==========================================================================*/

static volatile uint32_t g_learned_isr_latency_us = UTLP_ILC_INITIAL_US;

/*============================================================================
 * TIMER CALLBACK
 *==========================================================================*/

/**
 * @brief Cycle boundary callback from timer HAL
 *
 * Called once per cycle (1 ms at 10 MHz / 10000 ticks).
 * Updates phase chord (vector time) and performs ILC learning.
 *
 * "Time is a chord, not a number."
 */
static bool phase_cycle_callback(void *user_ctx, uint32_t count_at_isr)
{
    (void)user_ctx;

    /* Increment cycle count */
    s_state.cycle_count++;

    /* Update phase chord - the NATIVE time representation */
    uint64_t cycles = s_state.cycle_count;
    for (int i = 0; i < UTLP_CHORD_SIZE; i++) {
        s_state.phase_chord[i] = (uint8_t)(cycles % s_primes[i]);
    }

    /* ILC learning from count_at_isr */
    if (count_at_isr > 0) {
        uint32_t latency_us = (count_at_isr * UTLP_PHASE_TICK_NS) / 1000;
        uint32_t current = g_learned_isr_latency_us;

        if (latency_us > current + UTLP_ILC_DEADZONE_US) {
            /* Late - increase buffer */
            uint32_t increase = (latency_us - current) / UTLP_ILC_LEARN_DIVISOR;
            if (increase < 1) increase = 1;
            uint32_t new_val = current + increase;
            if (new_val > UTLP_ILC_MAX_US) new_val = UTLP_ILC_MAX_US;
            g_learned_isr_latency_us = new_val;
        } else if (latency_us + UTLP_ILC_DEADZONE_US < current) {
            /* Early - decay slowly */
            if (current > UTLP_ILC_MIN_US + UTLP_ILC_DECAY_US) {
                g_learned_isr_latency_us = current - UTLP_ILC_DECAY_US;
            }
        }
    }

    return false;
}

/*============================================================================
 * INITIALIZATION
 *==========================================================================*/

esp_err_t utlp_phase_init(void)
{
    if (s_initialized) {
        LOG_WARN(TAG, "Phase engine already initialized");
        return ESP_OK;
    }

    LOG_INFO(TAG, "Initializing Phase Engine (HPLC - Vector Time)");
    LOG_INFO(TAG, "  \"Time is a chord, not a number\"");
    LOG_INFO(TAG, "  Resolution: %lu Hz (%lu ns/tick)",
             (unsigned long)UTLP_PHASE_TIMER_RESOLUTION_HZ,
             (unsigned long)UTLP_PHASE_TICK_NS);
    LOG_INFO(TAG, "  Period: %lu ticks = %lu us",
             (unsigned long)UTLP_PHASE_PERIOD_TICKS,
             (unsigned long)UTLP_PHASE_CYCLE_US);
    LOG_INFO(TAG, "  Primes: [%u,%u,%u,%u,%u,%u,%u,%u]",
             s_primes[0], s_primes[1], s_primes[2], s_primes[3],
             s_primes[4], s_primes[5], s_primes[6], s_primes[7]);

    /* Initialize state */
    memset(&s_state, 0, sizeof(s_state));
    s_state.current_period_ticks = UTLP_PHASE_PERIOD_TICKS;
    s_state.sync_state = UTLP_PHASE_STATE_COLD;
    s_state.crt_valid = true;  /* CRT valid until partition detected */
    s_state.partition_status = UTLP_PARTITION_NONE;

    /* Initialize timer HAL */
    utlp_hal_timer_config_t config = {
        .resolution_hz = UTLP_PHASE_TIMER_RESOLUTION_HZ,
        .period_ticks = UTLP_PHASE_PERIOD_TICKS,
        .on_cycle = phase_cycle_callback,
        .user_ctx = &s_state,
    };

    utlp_hal_timer_err_t err = utlp_hal_timer_init(&config);
    if (err != UTLP_TIMER_OK) {
        LOG_WARN(TAG, "Failed to init timer HAL: %d", err);
        return ESP_FAIL;
    }

    /* Start timer */
    err = utlp_hal_timer_start();
    if (err != UTLP_TIMER_OK) {
        LOG_WARN(TAG, "Failed to start timer: %d", err);
        utlp_hal_timer_deinit();
        return ESP_FAIL;
    }

    s_initialized = true;
    LOG_INFO(TAG, "Phase engine initialized - Physics First!");
    return ESP_OK;
}

esp_err_t utlp_phase_deinit(void)
{
    if (!s_initialized) {
        return ESP_OK;
    }

    LOG_INFO(TAG, "Deinitializing phase engine");

    utlp_hal_timer_stop();
    utlp_hal_timer_deinit();

    s_initialized = false;
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
    return (uint16_t)((ticks * 360UL) / UTLP_PHASE_PERIOD_TICKS);
}

uint16_t utlp_phase_get_angle_x10(void)
{
    uint32_t ticks = utlp_phase_get_ticks();
    return (uint16_t)((ticks * 3600UL) / UTLP_PHASE_PERIOD_TICKS);
}

uint64_t utlp_phase_get_cycle_count(void)
{
    uint32_t crit = utlp_hal_timer_enter_critical();
    uint64_t count = s_state.cycle_count;
    utlp_hal_timer_exit_critical(crit);
    return count;
}

esp_err_t utlp_phase_get_state(utlp_phase_state_t *state)
{
    if (!state) {
        return ESP_ERR_INVALID_ARG;
    }

    uint32_t crit = utlp_hal_timer_enter_critical();
    memcpy(state, &s_state, sizeof(utlp_phase_state_t));
    utlp_hal_timer_exit_critical(crit);

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
        LOG_WARN(TAG, "Target ticks %lu exceeds period, clamping",
                 (unsigned long)target_ticks);
        target_ticks = UTLP_PHASE_PERIOD_TICKS - 1;
    }

    uint32_t crit = utlp_hal_timer_enter_critical();

    /* Hard sync via HAL */
    utlp_hal_timer_err_t err = utlp_hal_timer_hard_sync(target_ticks);

    /* Update state */
    s_state.current_period_ticks = UTLP_PHASE_PERIOD_TICKS;
    s_state.slewing = false;
    s_state.drift_accumulator_ppb = 0;
    s_state.last_sync_timestamp_us = utlp_hal_get_micros();

    utlp_hal_timer_exit_critical(crit);

    if (err != UTLP_TIMER_OK) {
        return ESP_FAIL;
    }

    LOG_INFO(TAG, "Hard sync to tick %lu (%.1f deg)",
             (unsigned long)target_ticks,
             (float)target_ticks * 360.0f / UTLP_PHASE_PERIOD_TICKS);

    return ESP_OK;
}

esp_err_t utlp_phase_slew(int32_t error_ticks)
{
    if (!s_initialized) {
        return ESP_ERR_INVALID_STATE;
    }

    /* Apply deadband */
    if (error_ticks > -(int32_t)UTLP_PHASE_DEADBAND_TICKS &&
        error_ticks < (int32_t)UTLP_PHASE_DEADBAND_TICKS) {
        /* Within deadband - reset to nominal */
        if (s_state.slewing) {
            utlp_hal_timer_reset_period();
            s_state.current_period_ticks = UTLP_PHASE_PERIOD_TICKS;
            s_state.slewing = false;
        }
        return ESP_OK;
    }

    /* Calculate period adjustment */
    int32_t delta_ticks = (error_ticks * (int32_t)UTLP_PHASE_PERIOD_TICKS) /
                          (int32_t)UTLP_PHASE_CONVERGENCE_TICKS;

    /* Clamp to max slew */
    if (delta_ticks > (int32_t)UTLP_PHASE_SLEW_MAX_TICKS) {
        delta_ticks = (int32_t)UTLP_PHASE_SLEW_MAX_TICKS;
    } else if (delta_ticks < -(int32_t)UTLP_PHASE_SLEW_MAX_TICKS) {
        delta_ticks = -(int32_t)UTLP_PHASE_SLEW_MAX_TICKS;
    }

    uint32_t new_period = UTLP_PHASE_PERIOD_TICKS - (uint32_t)delta_ticks;

    utlp_hal_timer_set_period(new_period);
    s_state.current_period_ticks = new_period;
    s_state.slewing = true;
    s_state.last_error_ticks = (uint16_t)((error_ticks < 0) ? -error_ticks : error_ticks);

    LOG_DEBUG(TAG, "Slew: error=%ld, delta=%ld, period=%lu",
              (long)error_ticks, (long)delta_ticks, (unsigned long)new_period);

    return ESP_OK;
}

esp_err_t utlp_phase_on_beacon(uint32_t peer_tx_phase_ticks, uint64_t rx_timestamp_us)
{
    if (!s_initialized) {
        return ESP_ERR_INVALID_STATE;
    }

    uint32_t local_ticks = utlp_phase_get_ticks();
    int32_t error_ticks = (int32_t)peer_tx_phase_ticks - (int32_t)local_ticks;

    /* Handle wrap-around */
    if (error_ticks > (int32_t)(UTLP_PHASE_PERIOD_TICKS / 2)) {
        error_ticks -= (int32_t)UTLP_PHASE_PERIOD_TICKS;
    } else if (error_ticks < -(int32_t)(UTLP_PHASE_PERIOD_TICKS / 2)) {
        error_ticks += (int32_t)UTLP_PHASE_PERIOD_TICKS;
    }

    /* Update error history */
    uint32_t crit = utlp_hal_timer_enter_critical();
    s_state.error_history[s_state.error_history_idx] =
        (uint16_t)((error_ticks < 0) ? -error_ticks : error_ticks);
    s_state.error_history_idx = (s_state.error_history_idx + 1) % 4;
    s_state.last_beacon_timestamp_us = rx_timestamp_us;
    utlp_hal_timer_exit_critical(crit);

    /* Select sync method */
    if (s_state.sync_state == UTLP_PHASE_STATE_COLD) {
        uint32_t target = peer_tx_phase_ticks;
        if (target >= UTLP_PHASE_PERIOD_TICKS) {
            target = 0;
        }
        return utlp_phase_hard_sync(target);
    } else {
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

    /* State transition: COLD → LOCKED */
    if (s_state.sync_state == UTLP_PHASE_STATE_COLD) {
        if (uptime_us >= UTLP_PHASE_COLD_START_US) {
            utlp_hal_timer_reset_period();
            s_state.current_period_ticks = UTLP_PHASE_PERIOD_TICKS;
            s_state.slewing = false;
            s_state.drift_accumulator_ppb = 0;
            s_state.sync_state = UTLP_PHASE_STATE_LOCKED;
            LOG_INFO(TAG, "Transition: COLD -> LOCKED");
        }
    }

    /* Calculate sync quality */
    uint32_t avg_error = 0;
    for (int i = 0; i < 4; i++) {
        avg_error += s_state.error_history[i];
    }
    avg_error /= 4;

    uint8_t quality;
    if (avg_error >= UTLP_PHASE_PERIOD_TICKS / 4) {
        quality = 0;
    } else {
        quality = (uint8_t)(100 - (avg_error * 400 / UTLP_PHASE_PERIOD_TICKS));
    }
    s_state.sync_quality = quality;

    /* State transitions: LOCKED ↔ RECOVERY */
    uint32_t threshold_ticks = UTLP_SERVO_LOCKED_THRESHOLD_US * UTLP_PHASE_TICKS_PER_US;

    if (s_state.sync_state == UTLP_PHASE_STATE_LOCKED && avg_error > threshold_ticks) {
        s_state.sync_state = UTLP_PHASE_STATE_RECOVERY;
        LOG_WARN(TAG, "Transition: LOCKED -> RECOVERY (error=%lu)", (unsigned long)avg_error);
    } else if (s_state.sync_state == UTLP_PHASE_STATE_RECOVERY && avg_error < threshold_ticks / 2) {
        s_state.sync_state = UTLP_PHASE_STATE_LOCKED;
        LOG_INFO(TAG, "Transition: RECOVERY -> LOCKED");
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

uint32_t utlp_phase_get_isr_latency_us(void)
{
    return g_learned_isr_latency_us;
}

/*============================================================================
 * ABSOLUTE TIME
 *==========================================================================*/

uint64_t utlp_phase_get_atomic_time_us(void)
{
    if (!s_initialized) {
        return 0;
    }

    uint32_t crit = utlp_hal_timer_enter_critical();
    uint64_t cycles = s_state.cycle_count;
    int64_t offset = s_state.epoch_offset_us;
    utlp_hal_timer_exit_critical(crit);

    uint32_t ticks = utlp_phase_get_ticks();
    uint64_t ticks_us = ((uint64_t)ticks * UTLP_PHASE_TICK_NS) / 1000;

    return (cycles * UTLP_PHASE_CYCLE_US) + ticks_us + offset;
}

void utlp_phase_set_epoch_offset(int64_t offset_us)
{
    uint32_t crit = utlp_hal_timer_enter_critical();
    s_state.epoch_offset_us = offset_us;
    utlp_hal_timer_exit_critical(crit);

    LOG_INFO(TAG, "Epoch offset set to %lld us", (long long)offset_us);
}

int64_t utlp_phase_get_epoch_offset(void)
{
    uint32_t crit = utlp_hal_timer_enter_critical();
    int64_t offset = s_state.epoch_offset_us;
    utlp_hal_timer_exit_critical(crit);
    return offset;
}

/*============================================================================
 * VECTOR TIME API - Primary Interface
 *
 * "Time is a chord, not a number."
 *
 * These functions provide the PRIMARY time access in UTLP. The phase chord
 * is always valid; scalar time is derived and may be invalid during partition.
 *==========================================================================*/

esp_err_t utlp_phase_get_time(utlp_app_time_t *time)
{
    if (!time) {
        return ESP_ERR_INVALID_ARG;
    }

    if (!s_initialized) {
        return ESP_ERR_INVALID_STATE;
    }

    uint32_t crit = utlp_hal_timer_enter_critical();

    /* Copy phase chord - always valid */
    for (int i = 0; i < UTLP_CHORD_SIZE; i++) {
        time->phase_chord[i] = s_state.phase_chord[i];
    }

    /* Copy partition status */
    time->partition = (utlp_partition_status_t)s_state.partition_status;
    time->crt_valid = s_state.crt_valid;

    /* Derive scalar time from cycles + ticks + offset (if CRT valid) */
    if (s_state.crt_valid) {
        uint64_t cycles = s_state.cycle_count;
        int64_t offset = s_state.epoch_offset_us;
        utlp_hal_timer_exit_critical(crit);

        uint32_t ticks = utlp_phase_get_ticks();
        uint64_t ticks_us = ((uint64_t)ticks * UTLP_PHASE_TICK_NS) / 1000;
        time->scalar_us = (cycles * UTLP_PHASE_CYCLE_US) + ticks_us + offset;
    } else {
        utlp_hal_timer_exit_critical(crit);
        time->scalar_us = 0;  /* Invalid during partition */
    }

    return ESP_OK;
}

void utlp_phase_get_chord(utlp_phase_chord_t chord)
{
    if (!chord || !s_initialized) {
        return;
    }

    uint32_t crit = utlp_hal_timer_enter_critical();
    for (int i = 0; i < UTLP_CHORD_SIZE; i++) {
        chord[i] = s_state.phase_chord[i];
    }
    utlp_hal_timer_exit_critical(crit);
}

uint8_t utlp_phase_get_phase(uint8_t prime_idx)
{
    if (prime_idx >= UTLP_CHORD_SIZE || !s_initialized) {
        return 0;
    }

    /* Single byte read - atomic on all platforms */
    return s_state.phase_chord[prime_idx];
}

void utlp_phase_cycles_to_chord(uint64_t cycles, utlp_phase_chord_t chord)
{
    if (!chord) {
        return;
    }

    for (int i = 0; i < UTLP_CHORD_SIZE; i++) {
        chord[i] = (uint8_t)(cycles % s_primes[i]);
    }
}

uint64_t utlp_phase_get_scalar_us(void)
{
    if (!s_initialized) {
        return 0;
    }

    /* Check CRT validity first */
    if (!s_state.crt_valid) {
        LOG_WARN(TAG, "Scalar time requested but CRT invalid (partition detected)");
        return 0;
    }

    uint32_t crit = utlp_hal_timer_enter_critical();
    uint64_t cycles = s_state.cycle_count;
    int64_t offset = s_state.epoch_offset_us;
    utlp_hal_timer_exit_critical(crit);

    uint32_t ticks = utlp_phase_get_ticks();
    uint64_t ticks_us = ((uint64_t)ticks * UTLP_PHASE_TICK_NS) / 1000;

    return (cycles * UTLP_PHASE_CYCLE_US) + ticks_us + offset;
}
