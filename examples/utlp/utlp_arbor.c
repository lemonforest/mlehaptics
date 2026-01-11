/**
 * @file utlp_arbor.c
 * @brief Per-Transport Selective Dormancy - Phase 0 Stub
 *
 * PHASE 0 STUB: All functions return success/defaults.
 * Full implementation will be added when multi-transport is needed.
 *
 * @version 0.0.1 (Phase 0 Stub)
 * @date 2026-01-08
 *
 * @copyright
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#include "utlp_arbor.h"
#include "utlp_hal.h"

static const char *TAG = "UTLP_ARBOR";

/*============================================================================
 * STUB STATE
 *==========================================================================*/

static struct {
    utlp_arbor_state_t states[UTLP_ARBOR_COUNT];
    bool registered[UTLP_ARBOR_COUNT];
    bool initialized;
} s_arbor_state = {0};

/*============================================================================
 * PUBLIC API STUBS
 *==========================================================================*/

void utlp_arbor_init(void)
{
    for (int i = 0; i < UTLP_ARBOR_COUNT; i++) {
        s_arbor_state.states[i] = UTLP_ARBOR_STATE_ERROR;
        s_arbor_state.registered[i] = false;
    }
    s_arbor_state.initialized = true;

    utlp_hal_log_info(TAG, "Phase 0 stub: arbor_init()");
}

esp_err_t utlp_arbor_register(utlp_arbor_id_t id)
{
    if (id >= UTLP_ARBOR_COUNT) {
        return ESP_ERR_INVALID_ARG;
    }

    s_arbor_state.registered[id] = true;
    s_arbor_state.states[id] = UTLP_ARBOR_STATE_ACTIVE;

    return ESP_OK;
}

esp_err_t utlp_arbor_yield(utlp_arbor_id_t id, const utlp_dormancy_params_t *params)
{
    (void)params;

    if (id >= UTLP_ARBOR_COUNT) {
        return ESP_ERR_INVALID_ARG;
    }

    s_arbor_state.states[id] = UTLP_ARBOR_STATE_DORMANT;
    return ESP_OK;
}

esp_err_t utlp_arbor_wake(utlp_arbor_id_t id)
{
    if (id >= UTLP_ARBOR_COUNT) {
        return ESP_ERR_INVALID_ARG;
    }

    s_arbor_state.states[id] = UTLP_ARBOR_STATE_ACTIVE;
    return ESP_OK;
}

esp_err_t utlp_arbor_force_wake(utlp_arbor_id_t id)
{
    return utlp_arbor_wake(id);
}

utlp_arbor_state_t utlp_arbor_get_state(utlp_arbor_id_t id)
{
    if (id >= UTLP_ARBOR_COUNT) {
        return UTLP_ARBOR_STATE_ERROR;
    }

    return s_arbor_state.states[id];
}

esp_err_t utlp_arbor_get_status(utlp_arbor_id_t id, utlp_arbor_status_t *status)
{
    if (id >= UTLP_ARBOR_COUNT || status == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    status->id = id;
    status->state = s_arbor_state.states[id];
    status->last_stratum = 0;
    status->reentry_stratum = 0;
    status->dormant_since = 0;
    status->wakeup_beacons = 0;

    return ESP_OK;
}

bool utlp_arbor_can_tx(utlp_arbor_id_t id)
{
    if (id >= UTLP_ARBOR_COUNT) {
        return false;
    }

    return s_arbor_state.states[id] == UTLP_ARBOR_STATE_ACTIVE;
}

bool utlp_arbor_can_rx(utlp_arbor_id_t id)
{
    if (id >= UTLP_ARBOR_COUNT) {
        return false;
    }

    utlp_arbor_state_t state = s_arbor_state.states[id];
    return (state == UTLP_ARBOR_STATE_ACTIVE || state == UTLP_ARBOR_STATE_WAKING);
}

esp_err_t utlp_arbor_beacon_verified(utlp_arbor_id_t id)
{
    (void)id;
    return ESP_OK;
}

const char* utlp_arbor_name(utlp_arbor_id_t id)
{
    switch (id) {
        case UTLP_ARBOR_WIFI: return "WiFi";
        case UTLP_ARBOR_154:  return "15.4";
        case UTLP_ARBOR_BLE:  return "BLE";
        default:              return "Unknown";
    }
}

uint8_t utlp_arbor_active_count(void)
{
    uint8_t count = 0;
    for (int i = 0; i < UTLP_ARBOR_COUNT; i++) {
        if (s_arbor_state.states[i] == UTLP_ARBOR_STATE_ACTIVE) {
            count++;
        }
    }
    return count;
}

uint8_t utlp_arbor_registered_count(void)
{
    uint8_t count = 0;
    for (int i = 0; i < UTLP_ARBOR_COUNT; i++) {
        if (s_arbor_state.registered[i]) {
            count++;
        }
    }
    return count;
}
