/**
 * @file utlp_immune.c
 * @brief STUB - Immune Checkpoint System (N≥3 feature, not implemented for N=2)
 *
 * This file provides compilation stubs for the immune/rate-limiting system.
 * The full implementation requires N≥3 for quorum sensing.
 *
 * @see utlp_immune.h for the complete API documentation
 * @version 0.0.0 (Stub for N=2 testing)
 */

#include "utlp_immune.h"
#include "utlp_hal.h"

static const char *TAG = "UTLP_IMMUNE";

/*============================================================================
 * STUB IMPLEMENTATIONS - N≥3 FEATURE NOT YET IMPLEMENTED
 *
 * These stubs allow compilation while the N=2 protocol is being validated.
 * Full implementation will be added when scaling to N≥3.
 *==========================================================================*/

void utlp_immune_init(void)
{
    utlp_hal_log_info(TAG, "Immune checkpoint STUB (N>=3 feature)");
}

bool utlp_immune_can_defend(void)
{
    /* At N=2, always allow defense (no quorum sensing) */
    return true;
}

bool utlp_immune_has_budget(void)
{
    /* At N=2, always have budget (no rate limiting) */
    return true;
}

bool utlp_immune_consume_token(void)
{
    /* At N=2, always succeed (no token tracking) */
    return true;
}

void utlp_immune_tick(void)
{
    /* No-op at N=2 */
}

bool utlp_immune_is_anergic(void)
{
    /* At N=2, never anergic */
    return false;
}

uint8_t utlp_immune_get_tokens(void)
{
    /* At N=2, always full budget */
    return 5;  /* ENTRAINMENT_BUDGET_MAX */
}
