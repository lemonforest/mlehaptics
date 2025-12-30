/**
 * @file utlp_immune.h
 * @brief Immune Checkpoint System - Active Immunity for UTLP
 *
 * @section philosophy Why Immune Systems, Not Voting Systems?
 *
 * When a distributed system detects misbehavior, it must respond. Traditional
 * approaches use **political metaphors**: Byzantine fault tolerance requires
 * 2/3 honest nodes to "vote out" bad actors. This assumes nodes can identify
 * attackers and coordinate a response.
 *
 * Biology offers a different model. Your immune system doesn't vote. It
 * doesn't elect antibodies. Instead, it uses **resource constraints** and
 * **self-limiting feedback loops** to prevent overreaction while still
 * mounting effective responses.
 *
 * This module implements that model:
 * - **Token Bucket** = T-cell budget (you can't attack forever)
 * - **Anergy State** = Exhaustion checkpoint (forced rest after depletion)
 * - **Quorum Sensing** = External validation (don't attack alone)
 *
 * The result: nodes that detect threats respond proportionally, then stop.
 * No voting required. No leader needed. Just physics.
 *
 * @section overview Overview
 * Implements the Active Immunity layer from UTLP Technical Supplement S2,
 * Section 2.4. This provides the "internal constraint" (token bucket) that
 * works alongside the "external constraint" (quorum sensing) to prevent
 * cytokine storm scenarios.
 *
 * @section dual_constraint The Dual Constraint System
 *
 * Before firing an entrainment pulse, a node must pass TWO independent checks:
 *
 * 1. **Internal Constraint (This Module)**: Do I have tokens left?
 *    - Prevents RF pollution from a single aggressive node
 *    - Forces rest periods through anergy state
 *
 * 2. **External Constraint (utlp_trust.h)**: Does the crowd agree with me?
 *    - Prevents the "Crazy Old Man" scenario
 *    - Requires 2+ healthy peers to confirm my perception
 *
 * Both must pass. A node with tokens but no quorum stays silent.
 * A node with quorum but no tokens enters anergy. This is how
 * immune systems prevent autoimmune disorders.
 *
 * @section analogy Biological Analogy
 * Real immune systems have checkpoint molecules (PD-1, CTLA-4, TIM-3) that
 * induce T-cell exhaustion to prevent runaway inflammation. The token bucket
 * serves the same purpose: limiting entrainment responses to prevent a node
 * from flooding the RF spectrum with entrainment pulses.
 *
 * @section usage Usage
 * @code
 * // Before firing an entrainment pulse:
 * if (utlp_immune_can_defend()) {
 *     // Token consumed, fire entrainment pulse
 *     send_entrainment();
 * } else {
 *     // Anergy state - either I'm exhausted or I might be the problem
 * }
 *
 * // Call periodically to refill tokens:
 * utlp_immune_tick();
 * @endcode
 *
 * @section config Configuration
 * - ENTRAINMENT_BUDGET_MAX: 5 tokens (max pulses before exhaustion)
 * - ENTRAINMENT_REFILL_MS: 12000ms (1 token per 12 seconds)
 * - ANERGY_RECOVERY_TOKENS: 3 (exit anergy when 3 tokens restored)
 *
 * @see docs/UTLP_Technical_Supplement_S2.md - Section 2.4.1
 *
 * @version 1.0.0
 * @date 2025-12-29
 *
 * @copyright
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#pragma once

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/*============================================================================
 * CONFIGURATION
 *==========================================================================*/

/**
 * @brief Maximum entrainment tokens (bucket capacity)
 *
 * 5 pulses before exhaustion. Prevents rapid-fire entrainment.
 */
#define UTLP_IMMUNE_BUDGET_MAX          5

/**
 * @brief Token refill rate in milliseconds
 *
 * 1 token per 12 seconds = 5 tokens in 60 seconds (1 minute recovery).
 */
#define UTLP_IMMUNE_REFILL_MS           12000

/**
 * @brief Tokens required to exit anergy state
 *
 * Must recover 3 tokens before resuming entrainment actions.
 * Provides hysteresis to prevent rapid on/off cycling.
 */
#define UTLP_IMMUNE_ANERGY_RECOVERY     3

/*============================================================================
 * PUBLIC API
 *==========================================================================*/

/**
 * @brief Initialize the immune checkpoint system
 *
 * Sets tokens to maximum and clears anergy state.
 * Call once at boot.
 */
void utlp_immune_init(void);

/**
 * @brief Attempt to fire an entrainment action
 *
 * Checks if we have entrainment budget available:
 * - If in anergy state, returns false (PD-1 engaged)
 * - If tokens available, consumes one and returns true
 * - If last token consumed, enters anergy state
 *
 * @return true if action allowed (token consumed)
 * @return false if budget exhausted or in anergy
 */
bool utlp_immune_can_defend(void);

/**
 * @brief Tick the immune system (call periodically)
 *
 * Refills tokens over time (T-cell regeneration).
 * Exits anergy state when ANERGY_RECOVERY tokens restored.
 *
 * Call this from the main loop or at regular intervals.
 */
void utlp_immune_tick(void);

/**
 * @brief Check if currently in anergy state
 *
 * Anergy = T-cell exhaustion. The node has fired too many
 * entrainment pulses and is now silent, possibly because:
 * - Chronic infection (persistent bad actor)
 * - Self-disagreement (I am the problem)
 *
 * @return true if in anergy (entrainment actions blocked)
 */
bool utlp_immune_is_anergic(void);

/**
 * @brief Get current token count
 *
 * For debugging/logging purposes.
 *
 * @return Current number of tokens (0 to BUDGET_MAX)
 */
uint8_t utlp_immune_get_tokens(void);

#ifdef __cplusplus
}
#endif
