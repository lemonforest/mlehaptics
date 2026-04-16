/**
 * @file utlp_hal_timer_esp32.c
 * @brief UTLP Timer HAL - ESP32 MCPWM Implementation
 *
 * Uses ESP32 MCPWM peripheral for high-resolution phase timing.
 * - Default: 50 kHz resolution (20µs/tick) for current scalar time model
 * - 16-bit counter with soft sync for instant phase jam
 * - Period bending for frequency slewing
 * - Pause/resume for Precision Window power management
 * - Runtime reconfiguration for dynamic resolution switching
 *
 * CROSS-PLATFORM CLOCK SOURCE:
 * - MCPWM_TIMER_CLK_SRC_DEFAULT: ESP-IDF selects optimal clock per chip
 * - ESP32 (classic): APB clock 80 MHz
 * - ESP32-C6/S3: PLL160M 160 MHz
 *
 * @version 2.0.0
 * @date 2026-03-04
 *
 * @copyright
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#ifdef ESP_PLATFORM

#include "utlp_hal_timer.h"
#include "utlp_config.h"
#include "utlp_hal.h"

#include "driver/mcpwm_timer.h"
#include "driver/mcpwm_sync.h"
#include "hal/mcpwm_ll.h"
#include "soc/mcpwm_struct.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/portmacro.h"

static const char *TAG = "UTLP_HAL_TIMER";

/*============================================================================
 * MODULE STATE
 *==========================================================================*/

static portMUX_TYPE s_spinlock = portMUX_INITIALIZER_UNLOCKED;
static mcpwm_timer_handle_t s_timer = NULL;
static mcpwm_sync_handle_t s_soft_sync = NULL;
static bool s_initialized = false;
static bool s_running = false;
static bool s_paused = false;

/** @brief Configured resolution (for caps reporting and reconfigure) */
static uint32_t s_resolution_hz = UTLP_PHASE_TIMER_RESOLUTION_HZ;

/** @brief Nominal period (from init config, restored on hard sync) */
static uint32_t s_nominal_period = UTLP_PHASE_PERIOD_TICKS;

/** @brief Current period (may differ during slew) */
static uint32_t s_current_period = UTLP_PHASE_PERIOD_TICKS;

/** @brief Cycle callback (preserved across reconfigure) */
static utlp_hal_timer_cb_t s_callback = NULL;

/** @brief User context for callback (preserved across reconfigure) */
static void *s_user_ctx = NULL;

/** @brief Cycle count tracked by this HAL for elapsed time computation */
static volatile uint64_t s_cycle_count = 0;

/** @brief Timestamp (esp_timer) when timer was last started/resumed */
static uint64_t s_start_timestamp_us = 0;

/*============================================================================
 * ISR CALLBACK
 *
 * Wraps the user callback and tracks cycle count for elapsed time.
 *==========================================================================*/

static bool IRAM_ATTR timer_empty_isr(mcpwm_timer_handle_t timer,
                                       const mcpwm_timer_event_data_t *edata,
                                       void *user_ctx)
{
    (void)timer;
    (void)user_ctx;

    s_cycle_count++;

    if (s_callback) {
        return s_callback(s_user_ctx, edata->count_value);
    }
    return false;
}

/*============================================================================
 * INTERNAL: Create MCPWM timer with given parameters
 *
 * Shared by init and reconfigure. Does NOT set s_initialized.
 *==========================================================================*/

static utlp_hal_timer_err_t create_timer(uint32_t resolution, uint32_t period)
{
    mcpwm_timer_config_t timer_config = {
        .group_id = UTLP_PHASE_MCPWM_GROUP,
        .clk_src = MCPWM_TIMER_CLK_SRC_DEFAULT,
        .resolution_hz = resolution,
        .period_ticks = period,
        .count_mode = MCPWM_TIMER_COUNT_MODE_UP,
        .flags = {
            .update_period_on_empty = true,
            .update_period_on_sync = true,
        },
    };

    esp_err_t ret = mcpwm_new_timer(&timer_config, &s_timer);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to create timer: %s", esp_err_to_name(ret));
        return UTLP_TIMER_ERR_PLATFORM;
    }

    /* Create soft sync source for hard sync */
    mcpwm_soft_sync_config_t sync_config = {};
    ret = mcpwm_new_soft_sync_src(&sync_config, &s_soft_sync);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to create sync: %s", esp_err_to_name(ret));
        mcpwm_del_timer(s_timer);
        s_timer = NULL;
        return UTLP_TIMER_ERR_PLATFORM;
    }

    /* Register ISR callback */
    mcpwm_timer_event_callbacks_t cbs = {
        .on_empty = timer_empty_isr,
    };
    ret = mcpwm_timer_register_event_callbacks(s_timer, &cbs, NULL);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to register callback: %s", esp_err_to_name(ret));
        mcpwm_del_sync_src(s_soft_sync);
        mcpwm_del_timer(s_timer);
        s_soft_sync = NULL;
        s_timer = NULL;
        return UTLP_TIMER_ERR_PLATFORM;
    }

    /* Enable timer (but don't start yet) */
    ret = mcpwm_timer_enable(s_timer);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to enable timer: %s", esp_err_to_name(ret));
        mcpwm_del_sync_src(s_soft_sync);
        mcpwm_del_timer(s_timer);
        s_soft_sync = NULL;
        s_timer = NULL;
        return UTLP_TIMER_ERR_PLATFORM;
    }

    return UTLP_TIMER_OK;
}

/**
 * @brief Destroy MCPWM timer and sync resources
 *
 * Internal helper shared by deinit and reconfigure.
 */
static void destroy_timer(void)
{
    if (s_running) {
        mcpwm_timer_start_stop(s_timer, MCPWM_TIMER_STOP_EMPTY);
        s_running = false;
    }

    if (s_timer) {
        mcpwm_timer_disable(s_timer);
        mcpwm_del_timer(s_timer);
        s_timer = NULL;
    }

    if (s_soft_sync) {
        mcpwm_del_sync_src(s_soft_sync);
        s_soft_sync = NULL;
    }
}

/**
 * @brief Compute elapsed microseconds from cycle count and current ticks
 *
 * @return Elapsed time in microseconds since last start/resume
 */
static uint64_t compute_elapsed_us(void)
{
    portENTER_CRITICAL(&s_spinlock);
    uint64_t cycles = s_cycle_count;
    portEXIT_CRITICAL(&s_spinlock);

    uint32_t ticks = utlp_hal_timer_get_ticks();
    uint32_t tick_us = UTLP_PHASE_CYCLE_US / s_nominal_period;

    return (cycles * UTLP_PHASE_CYCLE_US) + ((uint64_t)ticks * tick_us);
}

/*============================================================================
 * INITIALIZATION
 *==========================================================================*/

utlp_hal_timer_err_t utlp_hal_timer_init(const utlp_hal_timer_config_t *config)
{
    if (s_initialized) {
        ESP_LOGW(TAG, "Already initialized");
        return UTLP_TIMER_ERR_ALREADY_INITIALIZED;
    }

    /* Use defaults if no config */
    uint32_t resolution = config ? config->resolution_hz : UTLP_PHASE_TIMER_RESOLUTION_HZ;
    uint32_t period = config ? config->period_ticks : UTLP_PHASE_PERIOD_TICKS;

    s_callback = config ? config->on_cycle : NULL;
    s_user_ctx = config ? config->user_ctx : NULL;
    s_resolution_hz = resolution;
    s_nominal_period = period;
    s_current_period = period;
    s_cycle_count = 0;
    s_paused = false;

    ESP_LOGI(TAG, "Initializing ESP32 MCPWM timer");
    ESP_LOGI(TAG, "  Resolution: %lu Hz", (unsigned long)resolution);
    ESP_LOGI(TAG, "  Period: %lu ticks", (unsigned long)period);

    utlp_hal_timer_err_t err = create_timer(resolution, period);
    if (err != UTLP_TIMER_OK) {
        return err;
    }

    s_initialized = true;
    ESP_LOGI(TAG, "Timer initialized");
    return UTLP_TIMER_OK;
}

utlp_hal_timer_err_t utlp_hal_timer_deinit(void)
{
    if (!s_initialized) {
        return UTLP_TIMER_OK;
    }

    ESP_LOGI(TAG, "Deinitializing timer");

    destroy_timer();

    s_initialized = false;
    s_paused = false;
    s_callback = NULL;
    s_user_ctx = NULL;
    s_cycle_count = 0;
    return UTLP_TIMER_OK;
}

utlp_hal_timer_err_t utlp_hal_timer_get_caps(utlp_hal_timer_caps_t *caps)
{
    if (!caps) {
        return UTLP_TIMER_ERR_INVALID_ARG;
    }

    caps->actual_resolution_hz = s_resolution_hz;
    caps->max_period_ticks = 65535;  /* 16-bit MCPWM counter */
    caps->has_hard_sync = true;
    caps->has_period_bend = true;
    caps->counter_bits = 16;

    return UTLP_TIMER_OK;
}

/*============================================================================
 * TICK ACCESS
 *==========================================================================*/

uint32_t utlp_hal_timer_get_ticks(void)
{
    if (!s_initialized || !s_timer || !s_running) {
        return 0;
    }

    mcpwm_dev_t *hw = MCPWM_LL_GET_HW(UTLP_PHASE_MCPWM_GROUP);
    return mcpwm_ll_timer_get_count_value(hw, UTLP_PHASE_MCPWM_TIMER);
}

/*============================================================================
 * SYNCHRONIZATION
 *==========================================================================*/

utlp_hal_timer_err_t utlp_hal_timer_hard_sync(uint32_t target_ticks)
{
    if (!s_initialized || !s_timer || !s_soft_sync) {
        return UTLP_TIMER_ERR_NOT_INITIALIZED;
    }

    /* Clamp to period */
    if (target_ticks >= s_nominal_period) {
        target_ticks = s_nominal_period - 1;
    }

    portENTER_CRITICAL(&s_spinlock);

    /* Reset period to nominal (prevent sticky slew) */
    mcpwm_timer_set_period(s_timer, s_nominal_period);
    s_current_period = s_nominal_period;

    /* Configure sync phase */
    mcpwm_timer_sync_phase_config_t sync_config = {
        .sync_src = s_soft_sync,
        .count_value = target_ticks,
        .direction = MCPWM_TIMER_DIRECTION_UP,
    };
    mcpwm_timer_set_phase_on_sync(s_timer, &sync_config);

    /* Fire sync - counter teleports */
    mcpwm_soft_sync_activate(s_soft_sync);

    portEXIT_CRITICAL(&s_spinlock);

    ESP_LOGD(TAG, "Hard sync to tick %lu", (unsigned long)target_ticks);
    return UTLP_TIMER_OK;
}

utlp_hal_timer_err_t utlp_hal_timer_set_period(uint32_t new_period_ticks)
{
    if (!s_initialized || !s_timer) {
        return UTLP_TIMER_ERR_NOT_INITIALIZED;
    }

    portENTER_CRITICAL(&s_spinlock);
    mcpwm_timer_set_period(s_timer, new_period_ticks);
    s_current_period = new_period_ticks;
    portEXIT_CRITICAL(&s_spinlock);

    return UTLP_TIMER_OK;
}

uint32_t utlp_hal_timer_get_period(void)
{
    return s_current_period;
}

utlp_hal_timer_err_t utlp_hal_timer_reset_period(void)
{
    return utlp_hal_timer_set_period(s_nominal_period);
}

/*============================================================================
 * CONTROL
 *==========================================================================*/

utlp_hal_timer_err_t utlp_hal_timer_start(void)
{
    if (!s_initialized || !s_timer) {
        return UTLP_TIMER_ERR_NOT_INITIALIZED;
    }

    esp_err_t ret = mcpwm_timer_start_stop(s_timer, MCPWM_TIMER_START_NO_STOP);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to start timer: %s", esp_err_to_name(ret));
        return UTLP_TIMER_ERR_PLATFORM;
    }

    s_running = true;
    s_paused = false;
    s_start_timestamp_us = utlp_hal_get_micros();
    ESP_LOGI(TAG, "Timer started");
    return UTLP_TIMER_OK;
}

utlp_hal_timer_err_t utlp_hal_timer_stop(void)
{
    if (!s_initialized || !s_timer) {
        return UTLP_TIMER_ERR_NOT_INITIALIZED;
    }

    esp_err_t ret = mcpwm_timer_start_stop(s_timer, MCPWM_TIMER_STOP_EMPTY);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to stop timer: %s", esp_err_to_name(ret));
        return UTLP_TIMER_ERR_PLATFORM;
    }

    s_running = false;
    s_paused = false;
    ESP_LOGI(TAG, "Timer stopped");
    return UTLP_TIMER_OK;
}

bool utlp_hal_timer_is_running(void)
{
    return s_running && !s_paused;
}

/*============================================================================
 * PRECISION WINDOW - Pause/Resume
 *
 * Pause stops the MCPWM counter but preserves all configuration.
 * Resume restarts counting. The phase engine reconstructs missed
 * cycles using RTC elapsed time.
 *==========================================================================*/

utlp_hal_timer_err_t utlp_hal_timer_pause(uint64_t *elapsed_us)
{
    if (!s_initialized || !s_timer) {
        return UTLP_TIMER_ERR_NOT_INITIALIZED;
    }
    if (!s_running) {
        return UTLP_TIMER_ERR_NOT_RUNNING;
    }
    if (s_paused) {
        return UTLP_TIMER_ERR_ALREADY_PAUSED;
    }

    /* Capture elapsed time before stopping */
    if (elapsed_us) {
        *elapsed_us = compute_elapsed_us();
    }

    /* Stop timer at next cycle boundary */
    esp_err_t ret = mcpwm_timer_start_stop(s_timer, MCPWM_TIMER_STOP_EMPTY);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to pause timer: %s", esp_err_to_name(ret));
        return UTLP_TIMER_ERR_PLATFORM;
    }

    s_paused = true;
    /* s_running stays true — we're paused, not stopped */

    ESP_LOGI(TAG, "Timer paused (cycles=%llu)",
             (unsigned long long)s_cycle_count);
    return UTLP_TIMER_OK;
}

utlp_hal_timer_err_t utlp_hal_timer_resume(void)
{
    if (!s_initialized || !s_timer) {
        return UTLP_TIMER_ERR_NOT_INITIALIZED;
    }
    if (!s_paused) {
        return UTLP_TIMER_ERR_NOT_PAUSED;
    }

    /* Restart timer from current position */
    esp_err_t ret = mcpwm_timer_start_stop(s_timer, MCPWM_TIMER_START_NO_STOP);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to resume timer: %s", esp_err_to_name(ret));
        return UTLP_TIMER_ERR_PLATFORM;
    }

    s_paused = false;
    s_start_timestamp_us = utlp_hal_get_micros();

    ESP_LOGI(TAG, "Timer resumed");
    return UTLP_TIMER_OK;
}

bool utlp_hal_timer_is_paused(void)
{
    return s_paused;
}

/*============================================================================
 * DYNAMIC RECONFIGURATION
 *
 * Full teardown → reinit with new parameters. Preserves callback.
 *==========================================================================*/

utlp_hal_timer_err_t utlp_hal_timer_reconfigure(
    uint32_t new_resolution_hz,
    uint32_t new_period_ticks,
    uint64_t *elapsed_us)
{
    if (!s_initialized) {
        return UTLP_TIMER_ERR_NOT_INITIALIZED;
    }
    if (new_resolution_hz == 0 || new_period_ticks == 0) {
        return UTLP_TIMER_ERR_INVALID_ARG;
    }

    /* Capture elapsed time before teardown */
    if (elapsed_us) {
        if (s_running && !s_paused) {
            *elapsed_us = compute_elapsed_us();
        } else {
            *elapsed_us = 0;
        }
    }

    ESP_LOGI(TAG, "Reconfiguring: %lu Hz / %lu ticks → %lu Hz / %lu ticks",
             (unsigned long)s_resolution_hz, (unsigned long)s_nominal_period,
             (unsigned long)new_resolution_hz, (unsigned long)new_period_ticks);

    /* Preserve callback across reconfigure */
    utlp_hal_timer_cb_t saved_cb = s_callback;
    void *saved_ctx = s_user_ctx;

    /* Teardown */
    destroy_timer();

    /* Update parameters */
    s_resolution_hz = new_resolution_hz;
    s_nominal_period = new_period_ticks;
    s_current_period = new_period_ticks;
    s_callback = saved_cb;
    s_user_ctx = saved_ctx;
    s_cycle_count = 0;
    s_paused = false;
    s_running = false;

    /* Recreate with new parameters */
    utlp_hal_timer_err_t err = create_timer(new_resolution_hz, new_period_ticks);
    if (err != UTLP_TIMER_OK) {
        ESP_LOGE(TAG, "Reconfigure failed — timer unavailable!");
        s_initialized = false;
        return err;
    }

    ESP_LOGI(TAG, "Reconfigured to %lu Hz / %lu ticks",
             (unsigned long)new_resolution_hz, (unsigned long)new_period_ticks);
    return UTLP_TIMER_OK;
}

/*============================================================================
 * CRITICAL SECTIONS
 *==========================================================================*/

uint32_t utlp_hal_timer_enter_critical(void)
{
    portENTER_CRITICAL(&s_spinlock);
    return 0;  /* ESP32 spinlock doesn't need state */
}

void utlp_hal_timer_exit_critical(uint32_t state)
{
    (void)state;
    portEXIT_CRITICAL(&s_spinlock);
}

#else  /* !ESP_PLATFORM - Native test stubs */

/*============================================================================
 * NATIVE TEST STUBS
 *
 * Minimal stubs for compilation on native (non-ESP32) platforms.
 *==========================================================================*/

#include "utlp_hal_timer.h"
#include "utlp_config.h"

static bool s_initialized = false;
static bool s_running = false;
static bool s_paused = false;
static uint32_t s_period = UTLP_PHASE_PERIOD_TICKS;

utlp_hal_timer_err_t utlp_hal_timer_init(const utlp_hal_timer_config_t *config) {
    (void)config;
    s_initialized = true;
    return UTLP_TIMER_OK;
}

utlp_hal_timer_err_t utlp_hal_timer_deinit(void) {
    s_initialized = false;
    return UTLP_TIMER_OK;
}

utlp_hal_timer_err_t utlp_hal_timer_get_caps(utlp_hal_timer_caps_t *caps) {
    if (!caps) return UTLP_TIMER_ERR_INVALID_ARG;
    caps->actual_resolution_hz = UTLP_PHASE_TIMER_RESOLUTION_HZ;
    caps->max_period_ticks = 65535;
    caps->has_hard_sync = false;
    caps->has_period_bend = false;
    caps->counter_bits = 16;
    return UTLP_TIMER_OK;
}

uint32_t utlp_hal_timer_get_ticks(void) { return 0; }

utlp_hal_timer_err_t utlp_hal_timer_hard_sync(uint32_t t) { (void)t; return UTLP_TIMER_OK; }
utlp_hal_timer_err_t utlp_hal_timer_set_period(uint32_t p) { s_period = p; return UTLP_TIMER_OK; }
uint32_t utlp_hal_timer_get_period(void) { return s_period; }
utlp_hal_timer_err_t utlp_hal_timer_reset_period(void) { s_period = UTLP_PHASE_PERIOD_TICKS; return UTLP_TIMER_OK; }

utlp_hal_timer_err_t utlp_hal_timer_start(void) { s_running = true; s_paused = false; return UTLP_TIMER_OK; }
utlp_hal_timer_err_t utlp_hal_timer_stop(void) { s_running = false; s_paused = false; return UTLP_TIMER_OK; }
bool utlp_hal_timer_is_running(void) { return s_running && !s_paused; }

utlp_hal_timer_err_t utlp_hal_timer_pause(uint64_t *e) { if (e) *e = 0; s_paused = true; return UTLP_TIMER_OK; }
utlp_hal_timer_err_t utlp_hal_timer_resume(void) { s_paused = false; return UTLP_TIMER_OK; }
bool utlp_hal_timer_is_paused(void) { return s_paused; }

utlp_hal_timer_err_t utlp_hal_timer_reconfigure(uint32_t r, uint32_t p, uint64_t *e) {
    (void)r; s_period = p; if (e) *e = 0; return UTLP_TIMER_OK;
}

uint32_t utlp_hal_timer_enter_critical(void) { return 0; }
void utlp_hal_timer_exit_critical(uint32_t s) { (void)s; }

#endif /* ESP_PLATFORM */
