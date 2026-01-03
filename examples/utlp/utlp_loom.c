/**
 * @file utlp_loom.c
 * @brief The Loom - Emergent Time Lord Authority Implementation
 *
 * @section overview Overview
 *
 * This module implements the Loom state machine for automatic Time Lord
 * promotion when no external time source is available on a given arbor.
 *
 * @section algorithm Algorithm
 *
 * For each arbor, the Loom tracks:
 * - last_beacon_us: When we last received a beacon on this arbor
 * - state: Current Loom state (DORMANT, WEAVING, ANCHOR, DISSOLVING)
 *
 * State transitions:
 * - DORMANT -> WEAVING: No beacon for UTLP_LOOM_FRAY_THRESHOLD_US
 * - WEAVING -> ANCHOR: Warmup complete (UTLP_LOOM_WEAVE_WARMUP_US elapsed)
 * - WEAVING -> DORMANT: Beacon received (we're not alone)
 * - ANCHOR -> DISSOLVING: Better Time Lord detected
 * - DISSOLVING -> DORMANT: Step-down complete
 *
 * @version 1.0.0
 * @date 2026-01-02
 *
 * @copyright
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#include "utlp_loom.h"
#include "utlp_hal.h"
#include "utlp_arbor.h"
#include <string.h>

static const char *TAG = "UTLP_LOOM";

/*============================================================================
 * PER-ARBOR LOOM STATE
 *==========================================================================*/

/**
 * @brief Internal Loom state for one arbor
 */
typedef struct {
    utlp_loom_state_t state;           /**< Current state */
    uint64_t          last_beacon_us;  /**< Last beacon timestamp */
    uint64_t          weave_start_us;  /**< When WEAVING began */
    uint64_t          state_enter_us;  /**< When current state was entered */
    uint8_t           genesis_stratum; /**< Stratum when acting as ANCHOR */
    bool              paused;          /**< True if Loom paused (arbor dormant) */
    bool              genesis_requested; /**< True if Genesis Pulse should be sent */
} loom_arbor_t;

/** @brief Per-arbor Loom state array */
static loom_arbor_t s_loom[UTLP_ARBOR_COUNT];

/** @brief Initialization flag */
static bool s_loom_initialized = false;

/*============================================================================
 * FORWARD DECLARATIONS
 *==========================================================================*/

static void schedule_genesis_pulse(utlp_arbor_id_t arbor_id);
static void transition_to_state(utlp_arbor_id_t arbor_id, utlp_loom_state_t new_state);

/*============================================================================
 * HELPER FUNCTIONS
 *==========================================================================*/

/**
 * @brief Get current time in microseconds
 */
static inline uint64_t get_time_us(void) {
    return utlp_hal_get_micros();
}

/**
 * @brief Validate arbor ID
 */
static inline bool is_valid_arbor(utlp_arbor_id_t id) {
    return id < UTLP_ARBOR_COUNT;
}

/**
 * @brief Transition to a new Loom state with logging
 */
static void transition_to_state(utlp_arbor_id_t arbor_id, utlp_loom_state_t new_state) {
    loom_arbor_t *loom = &s_loom[arbor_id];
    utlp_loom_state_t old_state = loom->state;

    if (old_state == new_state) {
        return;  /* No transition needed */
    }

    loom->state = new_state;
    loom->state_enter_us = get_time_us();

    utlp_hal_log_info(TAG, "Arbor %s: Loom %s -> %s",
                      utlp_arbor_name(arbor_id),
                      utlp_loom_state_name(old_state),
                      utlp_loom_state_name(new_state));

    /* State-specific entry actions */
    switch (new_state) {
        case LOOM_STATE_WEAVING:
            loom->weave_start_us = get_time_us();
            break;

        case LOOM_STATE_ANCHOR:
            loom->genesis_stratum = 1;  /* Become stratum 1 (Genesis) */
            schedule_genesis_pulse(arbor_id);
            utlp_hal_log_info(TAG, "Arbor %s: TIME LORD active (stratum=%d)",
                              utlp_arbor_name(arbor_id), loom->genesis_stratum);
            break;

        case LOOM_STATE_DISSOLVING:
            /* Begin step-down process */
            utlp_hal_log_info(TAG, "Arbor %s: Dissolving Time Lord authority",
                              utlp_arbor_name(arbor_id));
            /* Immediate transition to DORMANT for now */
            transition_to_state(arbor_id, LOOM_STATE_DORMANT);
            break;

        case LOOM_STATE_DORMANT:
            loom->weave_start_us = 0;
            break;
    }
}

/**
 * @brief Schedule a Genesis Pulse on the specified arbor
 *
 * This triggers the seismic chirp (3-burst beacon sequence) to establish
 * this device as the Time Lord on this arbor.
 *
 * The main UTLP loop should call utlp_loom_consume_genesis_request() to
 * detect pending requests and trigger chirps appropriately.
 */
static void schedule_genesis_pulse(utlp_arbor_id_t arbor_id) {
    if (!is_valid_arbor(arbor_id)) {
        return;
    }

    s_loom[arbor_id].genesis_requested = true;
    utlp_hal_log_info(TAG, "Arbor %s: Genesis Pulse SCHEDULED (stratum=%d)",
                      utlp_arbor_name(arbor_id),
                      s_loom[arbor_id].genesis_stratum);
}

/*============================================================================
 * PUBLIC API IMPLEMENTATION
 *==========================================================================*/

void utlp_loom_init(void) {
    if (s_loom_initialized) {
        utlp_hal_log_warn(TAG, "Loom already initialized");
        return;
    }

    uint64_t now = get_time_us();

    for (int i = 0; i < UTLP_ARBOR_COUNT; i++) {
        s_loom[i].state = LOOM_STATE_DORMANT;
        s_loom[i].last_beacon_us = now;  /* Pretend we just received one */
        s_loom[i].weave_start_us = 0;
        s_loom[i].state_enter_us = now;
        s_loom[i].genesis_stratum = 0xFF;  /* Not Time Lord */
        s_loom[i].paused = false;
        s_loom[i].genesis_requested = false;
    }

    s_loom_initialized = true;
    utlp_hal_log_info(TAG, "Loom initialized (%d arbors, fray=%llu ms, warmup=%llu ms)",
                      UTLP_ARBOR_COUNT,
                      (unsigned long long)(UTLP_LOOM_FRAY_THRESHOLD_US / 1000),
                      (unsigned long long)(UTLP_LOOM_WEAVE_WARMUP_US / 1000));
}

void utlp_loom_tick(void) {
    if (!s_loom_initialized) {
        return;
    }

    uint64_t now = get_time_us();

    for (utlp_arbor_id_t id = 0; id < UTLP_ARBOR_COUNT; id++) {
        loom_arbor_t *loom = &s_loom[id];

        /* Skip paused arbors (dormant/sleeping) */
        if (loom->paused) {
            continue;
        }

        /* Skip if arbor not in a receivable state */
        if (utlp_arbor_get_state(id) == UTLP_ARBOR_STATE_DORMANT ||
            utlp_arbor_get_state(id) == UTLP_ARBOR_STATE_ERROR) {
            continue;
        }

        uint64_t silence = now - loom->last_beacon_us;

        switch (loom->state) {
            case LOOM_STATE_DORMANT:
                /* Check for timeline fray (silence exceeds threshold) */
                if (silence > UTLP_LOOM_FRAY_THRESHOLD_US) {
                    utlp_hal_log_warn(TAG, "Arbor %s: Timeline FRAYED (silence=%llu ms)",
                                      utlp_arbor_name(id),
                                      (unsigned long long)(silence / 1000));
                    transition_to_state(id, LOOM_STATE_WEAVING);
                }
                break;

            case LOOM_STATE_WEAVING:
                /* Check if warmup complete */
                if (now - loom->weave_start_us > UTLP_LOOM_WEAVE_WARMUP_US) {
                    utlp_hal_log_info(TAG, "Arbor %s: Warmup complete, becoming ANCHOR",
                                      utlp_arbor_name(id));
                    transition_to_state(id, LOOM_STATE_ANCHOR);
                }
                break;

            case LOOM_STATE_ANCHOR:
                /* Already Time Lord - continue broadcasting
                 * Dissolution happens via utlp_loom_beacon_received()
                 * when a better Time Lord is detected
                 */
                break;

            case LOOM_STATE_DISSOLVING:
                /* Should transition quickly to DORMANT
                 * This is handled in transition_to_state()
                 */
                break;
        }
    }
}

void utlp_loom_beacon_received(utlp_arbor_id_t arbor_id, uint8_t stratum, uint64_t tx_time) {
    if (!is_valid_arbor(arbor_id) || !s_loom_initialized) {
        return;
    }

    loom_arbor_t *loom = &s_loom[arbor_id];
    uint64_t now = get_time_us();

    /* Update last beacon timestamp */
    loom->last_beacon_us = now;

    (void)tx_time;  /* May be used for epoch comparison later */

    switch (loom->state) {
        case LOOM_STATE_DORMANT:
            /* Good - we're supposed to be listening */
            break;

        case LOOM_STATE_WEAVING:
            /* Beacon received while warming up - abort weaving */
            utlp_hal_log_info(TAG, "Arbor %s: Beacon received during weave, aborting",
                              utlp_arbor_name(arbor_id));
            transition_to_state(arbor_id, LOOM_STATE_DORMANT);
            break;

        case LOOM_STATE_ANCHOR:
            /* We're Time Lord - check if this beacon is from a better source */
            if (stratum < loom->genesis_stratum) {
                /* Better Time Lord detected */
                utlp_hal_log_info(TAG, "Arbor %s: Better Time Lord (stratum %d < %d), dissolving",
                                  utlp_arbor_name(arbor_id), stratum, loom->genesis_stratum);
                transition_to_state(arbor_id, LOOM_STATE_DISSOLVING);
            }
            /* Note: Equal stratum uses MAC tie-breaker in the main protocol */
            break;

        case LOOM_STATE_DISSOLVING:
            /* Already stepping down */
            break;
    }
}

utlp_loom_state_t utlp_loom_get_state(utlp_arbor_id_t arbor_id) {
    if (!is_valid_arbor(arbor_id) || !s_loom_initialized) {
        return LOOM_STATE_DORMANT;
    }
    return s_loom[arbor_id].state;
}

bool utlp_loom_get_status(utlp_arbor_id_t arbor_id, utlp_loom_status_t *status) {
    if (!is_valid_arbor(arbor_id) || !s_loom_initialized || !status) {
        return false;
    }

    loom_arbor_t *loom = &s_loom[arbor_id];
    uint64_t now = get_time_us();

    status->arbor_id = arbor_id;
    status->state = loom->state;
    status->last_beacon_us = loom->last_beacon_us;
    status->weave_start_us = loom->weave_start_us;
    status->genesis_stratum = loom->genesis_stratum;
    status->time_in_state_ms = (uint32_t)((now - loom->state_enter_us) / 1000);

    return true;
}

bool utlp_loom_is_time_lord(void) {
    if (!s_loom_initialized) {
        return false;
    }

    for (utlp_arbor_id_t id = 0; id < UTLP_ARBOR_COUNT; id++) {
        if (s_loom[id].state == LOOM_STATE_ANCHOR) {
            return true;
        }
    }
    return false;
}

bool utlp_loom_is_anchor(utlp_arbor_id_t arbor_id) {
    if (!is_valid_arbor(arbor_id) || !s_loom_initialized) {
        return false;
    }
    return s_loom[arbor_id].state == LOOM_STATE_ANCHOR;
}

void utlp_loom_force_anchor(utlp_arbor_id_t arbor_id, uint8_t stratum) {
    if (!is_valid_arbor(arbor_id) || !s_loom_initialized) {
        return;
    }

    utlp_hal_log_warn(TAG, "Arbor %s: FORCE ANCHOR (stratum=%d)",
                      utlp_arbor_name(arbor_id), stratum);

    s_loom[arbor_id].genesis_stratum = stratum;
    transition_to_state(arbor_id, LOOM_STATE_ANCHOR);
}

void utlp_loom_force_dissolve(utlp_arbor_id_t arbor_id) {
    if (!is_valid_arbor(arbor_id) || !s_loom_initialized) {
        return;
    }

    if (s_loom[arbor_id].state != LOOM_STATE_ANCHOR) {
        utlp_hal_log_warn(TAG, "Arbor %s: Not ANCHOR, cannot dissolve",
                          utlp_arbor_name(arbor_id));
        return;
    }

    utlp_hal_log_warn(TAG, "Arbor %s: FORCE DISSOLVE", utlp_arbor_name(arbor_id));
    transition_to_state(arbor_id, LOOM_STATE_DISSOLVING);
}

void utlp_loom_pause(utlp_arbor_id_t arbor_id) {
    if (!is_valid_arbor(arbor_id) || !s_loom_initialized) {
        return;
    }

    s_loom[arbor_id].paused = true;
    /* Debug-level logging (demoted to info for now) */
    (void)arbor_id;  /* Suppress unused warning if logging disabled */
}

void utlp_loom_resume(utlp_arbor_id_t arbor_id) {
    if (!is_valid_arbor(arbor_id) || !s_loom_initialized) {
        return;
    }

    /* Reset last beacon to "now" to prevent immediate WEAVING trigger */
    s_loom[arbor_id].last_beacon_us = get_time_us();
    s_loom[arbor_id].paused = false;

    utlp_hal_log_info(TAG, "Arbor %s: Loom RESUMED", utlp_arbor_name(arbor_id));
}

const char* utlp_loom_state_name(utlp_loom_state_t state) {
    switch (state) {
        case LOOM_STATE_DORMANT:    return "DORMANT";
        case LOOM_STATE_WEAVING:    return "WEAVING";
        case LOOM_STATE_ANCHOR:     return "ANCHOR";
        case LOOM_STATE_DISSOLVING: return "DISSOLVING";
        default:                    return "UNKNOWN";
    }
}

void utlp_loom_log_status(void) {
    if (!s_loom_initialized) {
        utlp_hal_log_warn(TAG, "Loom not initialized");
        return;
    }

    uint64_t now = get_time_us();

    utlp_hal_log_info(TAG, "=== LOOM STATUS ===");

    for (utlp_arbor_id_t id = 0; id < UTLP_ARBOR_COUNT; id++) {
        loom_arbor_t *loom = &s_loom[id];

        if (loom->paused) {
            utlp_hal_log_info(TAG, "  %s: PAUSED", utlp_arbor_name(id));
            continue;
        }

        uint64_t silence = now - loom->last_beacon_us;
        uint64_t in_state = now - loom->state_enter_us;

        utlp_hal_log_info(TAG, "  %s: %s (silence=%llu ms, in_state=%llu ms%s)",
                          utlp_arbor_name(id),
                          utlp_loom_state_name(loom->state),
                          (unsigned long long)(silence / 1000),
                          (unsigned long long)(in_state / 1000),
                          loom->state == LOOM_STATE_ANCHOR ?
                              ", TIME LORD" : "");
    }
}

/*============================================================================
 * GENESIS PULSE INTEGRATION
 *==========================================================================*/

bool utlp_loom_consume_genesis_request(void) {
    if (!s_loom_initialized) {
        return false;
    }

    /* Check all arbors for pending Genesis Pulse requests */
    for (utlp_arbor_id_t id = 0; id < UTLP_ARBOR_COUNT; id++) {
        if (s_loom[id].genesis_requested) {
            /* Clear the request and return true */
            s_loom[id].genesis_requested = false;
            utlp_hal_log_info(TAG, "Arbor %s: Genesis Pulse CONSUMED",
                              utlp_arbor_name(id));
            return true;
        }
    }

    return false;
}

void utlp_loom_request_genesis_pulse(utlp_arbor_id_t arbor_id) {
    if (!is_valid_arbor(arbor_id) || !s_loom_initialized) {
        return;
    }

    /* Request Genesis Pulse on this arbor (e.g., after waking from dormancy) */
    s_loom[arbor_id].genesis_requested = true;

    utlp_hal_log_info(TAG, "Arbor %s: Genesis Pulse REQUESTED (wake announcement)",
                      utlp_arbor_name(arbor_id));
}

uint8_t utlp_loom_get_genesis_stratum(void) {
    if (!s_loom_initialized) {
        return 0xFF;  /* Not Time Lord on any arbor */
    }

    uint8_t lowest_stratum = 0xFF;

    /* Find the lowest stratum among all ANCHOR arbors */
    for (utlp_arbor_id_t id = 0; id < UTLP_ARBOR_COUNT; id++) {
        if (s_loom[id].state == LOOM_STATE_ANCHOR) {
            if (s_loom[id].genesis_stratum < lowest_stratum) {
                lowest_stratum = s_loom[id].genesis_stratum;
            }
        }
    }

    return lowest_stratum;
}
