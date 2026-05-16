/*
 * srmech_rational.c — Class N primitive: rational-approximation.
 *
 * Task #217 Phase C1 rc6 — Class N earns its C surface per the per-class
 * parity discipline. Pure integer arithmetic on uint64_t; pi-free; no
 * malloc; no LAPACK.
 *
 * Two load-bearing operations:
 *
 *   - srmech_continued_fraction:  simple continued-fraction expansion
 *                                 p/q = [a_0; a_1, a_2, ...] via the
 *                                 Euclidean recurrence
 *   - srmech_best_rational:       best rational p'/q' with q' ≤ bound
 *                                 approximating p/q via continued-
 *                                 fraction convergents
 *
 * Class N appears in Spike #24's cross-substrate audit as the
 * rational-approximation primitive. Complements Class I (modular
 * arithmetic) and Class J (prime factorisation / period) as the third
 * pure-integer primitive in the vocabulary. Continued-fraction
 * expansion is the bridge between rational numbers and their best
 * lower-denominator approximations — the Stern-Brocot mediant tree
 * walked in canonical order.
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto)        : OK
 *   - Rule 2 (bounded loops)  : OK — Fibonacci-worst-case for uint64
 *                              Euclidean is ~91 iter; bound at 128
 *   - Rule 3 (no malloc)      : OK
 *   - Rule 4 (≤60 lines/func) : OK
 *   - Rule 5 (≥2 asserts/fn)  : OK — entry-pointer assert +
 *                              precondition / post-condition invariant
 *                              (per [[feedback_jpl_rule_5_two_assert_habit]])
 *   - Rule 7 (return-value)   : OK — srmech_status_t throughout
 *   - Rule 10 (warnings clean): OK
 *
 * License: GPL-3.0-or-later.
 */

#include "srmech.h"

#include <assert.h>
#include <stdint.h>

/* Fibonacci-worst-case for uint64 Euclidean is ~91 iter; 128 is safe
 * upper bound. Same constant Class I (cyclic) uses. */
#define SRMECH_RATIONAL_EUCLID_CAP 128

srmech_status_t srmech_continued_fraction(uint64_t  numerator,
                                          uint64_t  denominator,
                                          uint64_t *terms,
                                          uint32_t  max_terms,
                                          uint32_t *out_count)
{
    assert(out_count != NULL);
    assert(max_terms == 0 || terms != NULL);
    if (out_count == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    *out_count = 0;
    if (denominator == 0) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (max_terms == 0) {
        return SRMECH_ERR_OVERFLOW;
    }
    if (terms == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    /* Euclidean expansion: a_i = floor(p / q); (p, q) := (q, p mod q).
     * Halt when q == 0. Bounded by Fibonacci-worst-case for uint64. */
    uint64_t p = numerator;
    uint64_t q = denominator;
    for (uint32_t i = 0; i < SRMECH_RATIONAL_EUCLID_CAP; i++) {
        if (q == 0) {
            return SRMECH_OK;
        }
        if (*out_count >= max_terms) {
            return SRMECH_ERR_OVERFLOW;
        }
        terms[*out_count] = p / q;
        (*out_count)++;
        uint64_t r = p % q;
        p = q;
        q = r;
    }
    /* Unreachable for valid uint64; the Euclidean cap is conservative. */
    assert(0 && "srmech_continued_fraction exceeded bounded iteration cap");
    return SRMECH_ERR_INTERNAL;
}

srmech_status_t srmech_best_rational(uint64_t  numerator,
                                     uint64_t  denominator,
                                     uint64_t  max_denominator,
                                     uint64_t *out_p,
                                     uint64_t *out_q)
{
    assert(out_p != NULL);
    assert(out_q != NULL);
    if (out_p == NULL || out_q == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    *out_p = 0;
    *out_q = 1;
    if (denominator == 0 || max_denominator == 0) {
        return SRMECH_ERR_BAD_INPUT;
    }
    /* Compute convergents h_k = a_k * h_{k-1} + h_{k-2},
     *                    k_k = a_k * k_{k-1} + k_{k-2}
     * walking the continued fraction. Keep the last convergent whose
     * denominator k_k ≤ max_denominator. Bounded by the Euclidean cap. */
    uint64_t p = numerator;
    uint64_t q = denominator;
    uint64_t h_prev = 1, h_curr = 0;  /* h_{-1} = 1, h_{-2} = 0 by convention */
    uint64_t k_prev = 0, k_curr = 1;  /* k_{-1} = 0, k_{-2} = 1 */
    uint64_t best_p = 0;
    uint64_t best_q = 1;
    for (uint32_t i = 0; i < SRMECH_RATIONAL_EUCLID_CAP; i++) {
        if (q == 0) {
            break;
        }
        uint64_t a = p / q;
        /* Overflow guards on the convergent recurrence. */
        if (h_prev > 0 && a > (UINT64_MAX - h_curr) / h_prev) {
            break;
        }
        if (k_prev > 0 && a > (UINT64_MAX - k_curr) / k_prev) {
            break;
        }
        uint64_t h_next = a * h_prev + h_curr;
        uint64_t k_next = a * k_prev + k_curr;
        if (k_next > max_denominator) {
            break;
        }
        best_p = h_next;
        best_q = k_next;
        h_curr = h_prev;
        h_prev = h_next;
        k_curr = k_prev;
        k_prev = k_next;
        uint64_t r = p % q;
        p = q;
        q = r;
    }
    assert(best_q > 0);
    assert(best_q <= max_denominator);
    *out_p = best_p;
    *out_q = best_q;
    return SRMECH_OK;
}
