/**
 * @file utlp_immune.c
 * @brief Immune Checkpoint System Implementation
 *
 * Implements token bucket rate limiting for entrainment pulses,
 * preventing cytokine storm (runaway entrainment wars).
 *
 * @section biology Biological Mapping
 *
 * | Token Bucket      | Immune System            | UTLP Behavior           |
 * |-------------------|--------------------------|-------------------------|
 * | Token             | T-cell with capacity     | One entrainment pulse   |
 * | Bucket capacity   | Naive T-cell pool        | 5 pulses max            |
 * | Refill rate       | T-cell regeneration      | 1 token per 12 seconds  |
 * | Bucket empty      | T-cell exhaustion        | Enter anergy (silence)  |
 * | Anergy state      | PD-1 checkpoint engaged  | Stop responding         |
 *
 * @see docs/UTLP_Technical_Supplement_S2.md - Section 2.4.1
 *
 * @version 1.0.0
 * @date 2025-12-29
 *
 * @copyright
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#include "utlp_immune.h"
#include "utlp_hal.h"

/** @brief Logging tag */
static const char *TAG = "IMMUNE";

/*============================================================================
 * STATIC STATE
 *==========================================================================*/

/**
 * @brief Immune checkpoint state
 *
 * Tracks entrainment budget and anergy state.
 * Static allocation - no malloc.
 */
typedef struct {
    /* 4-byte fields first */
    uint32_t last_refill_ms;    /**< Last refill timestamp */
    /* 1-byte fields */
    uint8_t  tokens;            /**< Current entrainment budget */
    bool     in_anergy;         /**< Exhaustion state (PD-1 engaged) */
} immune_state_t;

static immune_state_t g_immune = {
    .tokens = UTLP_IMMUNE_BUDGET_MAX,
    .last_refill_ms = 0,
    .in_anergy = false
};

/*============================================================================
 * INTERNAL HELPERS
 *==========================================================================*/

/**
 * @brief Get current time in milliseconds
 */
static uint32_t get_time_ms(void) {
    return (uint32_t)(utlp_hal_get_micros() / 1000);
}

/*============================================================================
 * PUBLIC API
 *==========================================================================*/

void utlp_immune_init(void) {
    g_immune.tokens = UTLP_IMMUNE_BUDGET_MAX;
    g_immune.last_refill_ms = get_time_ms();
    g_immune.in_anergy = false;

    utlp_hal_log_info(TAG, "Immune checkpoint initialized: %d tokens",
                      UTLP_IMMUNE_BUDGET_MAX);
}

void utlp_immune_tick(void) {
    uint32_t now = get_time_ms();
    uint32_t elapsed = now - g_immune.last_refill_ms;

    /* Refill tokens over time (T-cell regeneration) */
    if (elapsed >= UTLP_IMMUNE_REFILL_MS) {
        uint32_t new_tokens = elapsed / UTLP_IMMUNE_REFILL_MS;

        /* Add tokens, capped at maximum */
        if (g_immune.tokens + new_tokens > UTLP_IMMUNE_BUDGET_MAX) {
            g_immune.tokens = UTLP_IMMUNE_BUDGET_MAX;
        } else {
            g_immune.tokens += (uint8_t)new_tokens;
        }

        /* Update last refill time */
        g_immune.last_refill_ms = now - (elapsed % UTLP_IMMUNE_REFILL_MS);

        /* Exit anergy if tokens restored (hysteresis) */
        if (g_immune.in_anergy &&
            g_immune.tokens >= UTLP_IMMUNE_ANERGY_RECOVERY) {
            g_immune.in_anergy = false;
            utlp_hal_log_info(TAG, "Exiting anergy, entrainment capacity restored (%d tokens)",
                              g_immune.tokens);
        }
    }
}

bool utlp_immune_can_defend(void) {
    /* First, tick to update tokens */
    utlp_immune_tick();

    /* PD-1 engaged: no response allowed */
    if (g_immune.in_anergy) {
        return false;
    }

    /* Check if we have budget */
    if (g_immune.tokens > 0) {
        g_immune.tokens--;

        /* Last token consumed? Enter anergy */
        if (g_immune.tokens == 0) {
            g_immune.in_anergy = true;
            utlp_hal_log_warn(TAG, "Entrainment budget exhausted. Entering anergy. "
                              "Possible: chronic infection, or self-disagreement.");
        }

        return true;
    }

    return false;
}

bool utlp_immune_is_anergic(void) {
    return g_immune.in_anergy;
}

uint8_t utlp_immune_get_tokens(void) {
    return g_immune.tokens;
}
