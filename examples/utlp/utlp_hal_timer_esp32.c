/**
 * @file utlp_hal_timer_esp32.c
 * @brief UTLP Timer HAL - ESP32 MCPWM Implementation
 *
 * Uses ESP32 MCPWM peripheral for high-resolution phase timing.
 * - 10 MHz resolution (100 ns tick) from PLL160M
 * - 16-bit counter with soft sync for instant phase jam
 * - Period bending for frequency slewing
 *
 * @version 1.0.0
 * @date 2026-01-09
 *
 * @copyright
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#ifdef ESP_PLATFORM

#include "utlp_hal_timer.h"
#include "utlp_config.h"

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

static uint32_t s_nominal_period = UTLP_PHASE_PERIOD_TICKS;
static uint32_t s_current_period = UTLP_PHASE_PERIOD_TICKS;
static utlp_hal_timer_cb_t s_callback = NULL;
static void *s_user_ctx = NULL;

/*============================================================================
 * ISR CALLBACK
 *==========================================================================*/

static bool IRAM_ATTR timer_empty_isr(mcpwm_timer_handle_t timer,
                                       const mcpwm_timer_event_data_t *edata,
                                       void *user_ctx)
{
    (void)timer;
    (void)user_ctx;

    if (s_callback) {
        return s_callback(s_user_ctx, edata->count_value);
    }
    return false;
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
    s_nominal_period = period;
    s_current_period = period;

    ESP_LOGI(TAG, "Initializing ESP32 MCPWM timer");
    ESP_LOGI(TAG, "  Resolution: %lu Hz", (unsigned long)resolution);
    ESP_LOGI(TAG, "  Period: %lu ticks", (unsigned long)period);

    /* Configure MCPWM timer */
    mcpwm_timer_config_t timer_config = {
        .group_id = UTLP_PHASE_MCPWM_GROUP,
        .clk_src = MCPWM_TIMER_CLK_SRC_PLL160M,
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

    if (s_running) {
        utlp_hal_timer_stop();
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

    s_initialized = false;
    s_callback = NULL;
    s_user_ctx = NULL;
    return UTLP_TIMER_OK;
}

utlp_hal_timer_err_t utlp_hal_timer_get_caps(utlp_hal_timer_caps_t *caps)
{
    if (!caps) {
        return UTLP_TIMER_ERR_INVALID_ARG;
    }

    caps->actual_resolution_hz = UTLP_PHASE_TIMER_RESOLUTION_HZ;
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
    if (!s_initialized || !s_timer) {
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
    ESP_LOGI(TAG, "Timer stopped");
    return UTLP_TIMER_OK;
}

bool utlp_hal_timer_is_running(void)
{
    return s_running;
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

#endif /* ESP_PLATFORM */
