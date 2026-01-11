/**
 * @file utlp_loom.c
 * @brief STUB - Emergent Time Lord Authority (N≥3 feature, not implemented for N=2)
 *
 * This file provides compilation stubs for the Loom state machine.
 * At N=2, Time Lord promotion follows simpler first-contact rules.
 * The full Loom with per-arbor state machines is for N≥3.
 *
 * @see utlp_loom.h for the complete API documentation
 * @version 0.0.0 (Stub for N=2 testing)
 */

#include "utlp_loom.h"
#include "utlp_hal.h"

static const char *TAG = "UTLP_LOOM";

/*============================================================================
 * STUB IMPLEMENTATIONS - N≥3 FEATURE NOT YET IMPLEMENTED
 *
 * At N=2, we use simpler epoch resolution rules:
 * - First contact: depth + origin_time determines winner
 * - N=2→N=1: Continue timeline unchanged
 * - N=1→N=2: Re-evaluate via first contact rules
 *
 * The Loom's per-arbor Time Lord promotion is for N≥3 scenarios.
 *==========================================================================*/

void utlp_loom_init(void)
{
    utlp_hal_log_info(TAG, "Loom subsystem STUB (N>=3 feature)");
}

void utlp_loom_tick(void)
{
    /* No-op at N=2 */
}

void utlp_loom_beacon_received(utlp_arbor_id_t arbor_id, uint8_t stratum, uint64_t tx_time)
{
    (void)arbor_id;
    (void)stratum;
    (void)tx_time;
}

utlp_loom_state_t utlp_loom_get_state(utlp_arbor_id_t arbor_id)
{
    (void)arbor_id;
    /* At N=2 with single device, we're always the time source */
    return LOOM_STATE_ANCHOR;
}

bool utlp_loom_get_status(utlp_arbor_id_t arbor_id, utlp_loom_status_t *status)
{
    if (!status) {
        return false;
    }

    status->arbor_id = arbor_id;
    status->state = LOOM_STATE_ANCHOR;
    status->last_beacon_us = 0;
    status->weave_start_us = 0;
    status->genesis_stratum = 1;
    status->time_in_state_ms = 0;

    return true;
}

bool utlp_loom_is_time_lord(void)
{
    /* At N=1, we are always the time lord */
    return true;
}

bool utlp_loom_is_anchor(utlp_arbor_id_t arbor_id)
{
    (void)arbor_id;
    /* At N=1, we are anchor on all arbors */
    return true;
}

void utlp_loom_force_anchor(utlp_arbor_id_t arbor_id, uint8_t stratum)
{
    (void)arbor_id;
    (void)stratum;
}

void utlp_loom_force_dissolve(utlp_arbor_id_t arbor_id)
{
    (void)arbor_id;
}

void utlp_loom_pause(utlp_arbor_id_t arbor_id)
{
    (void)arbor_id;
}

void utlp_loom_resume(utlp_arbor_id_t arbor_id)
{
    (void)arbor_id;
}

void utlp_loom_log_status(void)
{
    utlp_hal_log_info(TAG, "Loom: STUB (N>=3 feature) - acting as Time Lord");
}

void utlp_loom_polychromatic_update(void)
{
    /* No-op at N=2 */
}

bool utlp_loom_consume_genesis_request(utlp_arbor_id_t *out_arbor)
{
    (void)out_arbor;
    return false;  /* No pending genesis requests */
}

void utlp_loom_request_genesis_pulse(utlp_arbor_id_t arbor_id)
{
    (void)arbor_id;
}

uint8_t utlp_loom_get_genesis_stratum(void)
{
    return 1;  /* Genesis stratum */
}
