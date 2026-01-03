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
 * @section immunology Immunology Cross-References
 *
 * This module maps networking concepts to real immunology:
 *
 * @subsection immune_tcell T-Cell Exhaustion (PD-1 Pathway)
 * In chronic infections or cancer, T-cells become "exhausted" - they stop
 * responding to antigens. This is mediated by checkpoint molecules:
 * - **PD-1** (Programmed Death-1): Inhibits T-cell activation
 * - **CTLA-4**: Competes with CD28 for co-stimulation
 * - **TIM-3, LAG-3**: Additional exhaustion markers
 *
 * Our token bucket implements this: when tokens deplete, the node enters
 * "anergy" (exhaustion) and stops responding. This prevents cytokine storms.
 *
 * @par Clinical Relevance:
 * Cancer immunotherapy (Keytruda, Opdivo) blocks PD-1 to "release the brakes"
 * on exhausted T-cells. Our anergy recovery (3 tokens) provides similar
 * controlled re-engagement after rest.
 *
 * @par Academic Reference:
 * Wherry, E.J. (2011). "T cell exhaustion" Nature Immunology 12(6):492-499
 *
 * @subsection immune_quorum Quorum Sensing (Bacterial Communication)
 * Bacteria don't act alone. They use **autoinducers** - signaling molecules
 * that accumulate as population grows. Only when concentration exceeds a
 * threshold does the population act (e.g., bioluminescence, virulence).
 *
 * Our quorum check implements this: a node must see 2+ healthy peers agreeing
 * before firing entrainment. This prevents the "Crazy Old Man" scenario where
 * a drifted node attacks the healthy swarm.
 *
 * @par Academic Reference:
 * Waters, C.M., Bassler, B.L. (2005). "Quorum Sensing: Cell-to-Cell
 * Communication in Bacteria" Annual Review of Cell and Developmental Biology
 *
 * @subsection immune_cytokine Cytokine Storm Prevention
 * In COVID-19 and other diseases, the immune system can overreact, causing
 * a **cytokine storm** - runaway inflammation that damages the host. The
 * dual constraint system (tokens + quorum) prevents the network equivalent:
 * an RF storm where all nodes fire entrainment pulses simultaneously.
 *
 * @section algorithms Algorithm Cross-References
 *
 * @subsection algo_token Token Bucket (Networking, 1990s)
 * The token bucket is a classic traffic shaping algorithm:
 * - Bucket holds N tokens (capacity)
 * - Each action consumes 1 token
 * - Tokens refill at rate R tokens/second
 * - When empty, actions are blocked (or queued)
 *
 * Our parameters: 5 tokens, 1 token per 12 seconds = 5 entrainment pulses
 * per minute maximum sustained rate, with burst capacity of 5.
 *
 * @par Academic Reference:
 * Turner, J.S. (1986). "New directions in communications" IEEE Communications
 *
 * @subsection algo_hysteresis Hysteresis (Control Systems)
 * The anergy recovery threshold (3 tokens) implements **hysteresis**:
 * - Enter anergy at 0 tokens
 * - Exit anergy at 3 tokens
 * - Prevents rapid on/off oscillation near threshold
 *
 * This is the same principle as a thermostat with deadband: the heater
 * doesn't turn on/off at exactly 70°F, but at 69°F (on) and 71°F (off).
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
 * @section analogy Biological Mapping Table
 *
 * | Token Bucket      | Immune System            | UTLP Behavior             |
 * |-------------------|--------------------------|---------------------------|
 * | Token             | T-cell with capacity     | One entrainment pulse     |
 * | Bucket capacity   | Naive T-cell pool        | 5 pulses max              |
 * | Refill rate       | T-cell regeneration      | 1 token per 12 seconds    |
 * | Bucket empty      | T-cell exhaustion        | Enter anergy (silence)    |
 * | Anergy state      | PD-1 checkpoint engaged  | Stop responding           |
 * | Recovery threshold| CD28 re-engagement       | 3 tokens to exit anergy   |
 * | Quorum sensing    | Autoinducer threshold    | 2+ agreeing peers         |
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
 * STRUCT PACKING CONVENTION (Memory Alignment Optimization)
 *
 * Always order struct fields from largest to smallest alignment:
 *   1. 8-byte fields first (int64_t, uint64_t, double, pointers on 64-bit)
 *   2. 4-byte fields (int32_t, uint32_t, float)
 *   3. 2-byte fields (int16_t, uint16_t)
 *   4. 1-byte fields and arrays (uint8_t, bool, char[])
 *
 * This minimizes padding bytes inserted by the compiler for alignment.
 * See utlp_trust.h for detailed example.
 *==========================================================================*/

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
