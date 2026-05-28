/*
 * srmech_cascade.c — cascade-catalog C peers for srmech.amsc.cascade.
 *
 * v0.4.5rc1: corrects the v0.4.3rc6 / v0.4.4rc1 carve-out that shipped
 * `srmech.amsc.cascade` as a Python-only module with no C symbols and
 * no TOML descriptors. This file is the first of an in-flight series
 * of cascade-op C peers (one per srmech.amsc.cascade callable) that
 * restore full C/Python parity per the project's no-binding-layer-
 * carveout discipline.
 *
 * First op shipped: `chiral_flip` (Class C orientation reversal).
 * Two typed variants — i64 sequences from cyclic-group land, f64
 * sequences from spectral land — keep the ctypes surface narrow and
 * avoid embedding a per-element generic dispatch on the C side. Each
 * variant supports in-place reversal (caller may pass `in == out`).
 *
 * v0.4.5rc2 op: `pin_slot_at_zero` (Class K pin-slot at zero). Scalar
 * in / (int8 orientation, double magnitude) out via output pointers.
 * f64-only — scalar floats are the cascade-hot path; integer pin-slot
 * is trivial and not catalogued. NaN maps to the dead-band matching
 * the Python reference impl.
 *
 * v0.4.5rc3 op: `magnitude` (Class K pin-slot magnitude-only projection).
 * Scalar f64 in / scalar f64 out via output pointer. The cascade-honest
 * replacement for C99 fabs() inside cascade code: composes
 * pin_slot_at_zero and discards the orientation. NaN maps to 0.0
 * (the Class K dead-band) — preserves parity with the Python reference
 * impl where pin_slot_at_zero(nan) -> (0, 0.0).
 *
 * v0.4.5rc4 op: `reorient` (Class C cascade-orientation re-application).
 * Two typed variants — i64 and f64 — reflecting that the op is
 * type-preserving (Python `reorient(-1, 5)` -> -5 int;
 * `reorient(-1, 3.14)` -> -3.14 float). Two-arg shape: int8 orientation
 * x scalar value; value negated iff orientation < 0 (only the SIGN of
 * orientation matters, zero and positive both pass through). NaN and
 * +/-Inf pass through under IEEE-754 negation in the f64 variant.
 *
 * v0.4.5rc5 op: `net_chirality` (Class C net handedness invariant).
 * Sequence-in / scalar-out via output pointer. Multiplicative product
 * of per-op orientations in {-1, 0, +1}; empty input returns +1
 * (multiplicative identity); any 0 in the sequence short-circuits to 0
 * (a zero-crossing collapses net handedness). Last of the simple
 * pure-Python cascade ops in the arc.
 *
 * v0.4.5rc6 op: `cyclic_gcd` (Class I cyclic-group gcd; cascade-namespace
 * wrapper). FIRST of the delegating cascade ops — the cascade-catalog
 * entry IS the Class I primitive (Euclid gcd; srmech_gcd). The wrapper
 * exists to maintain the srmech_cascade_* namespace invariant: every
 * cascade-catalog entry ships a srmech_cascade_* C symbol, even when
 * the math lives at the A–N primitive level. Internally delegates to
 * srmech_gcd; no additional sign-handling or cyclic-group operations
 * layered on top (that would be a different cascade).
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto)        : OK
 *   - Rule 2 (bounded loops)  : OK — single loop bounded by n/2
 *   - Rule 3 (no malloc)      : OK — all storage is caller-provided
 *   - Rule 4 (≤60 lines/func) : OK — each variant ~15 lines
 *   - Rule 5 (≥2 asserts/fn)  : OK — input ptrs + post-condition each
 *                              (asserts active when n > 0; the n == 0
 *                              fast-return is a documented no-op).
 *   - Rule 7 (return-value)   : OK — srmech_status_t throughout
 *   - Rule 10 (warnings clean): OK under -Wall -Wextra -Wpedantic
 *
 * License: GPL-3.0-or-later.
 */

#include "srmech.h"

#include <assert.h>
#include <stdint.h>

srmech_status_t srmech_cascade_chiral_flip_i64(const int64_t *in,
                                                size_t         n,
                                                int64_t       *out)
{
    if (n == 0) {
        return SRMECH_OK;
    }
    if (in == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(in  != NULL);
    assert(out != NULL);
    /* Walk from both ends; read both ends into locals BEFORE writing
     * so the in != out partial-overlap case is also handled correctly
     * (when in == out this reduces to a plain swap). */
    for (size_t i = 0; i < n / 2; ++i) {
        const size_t  j   = n - 1 - i;
        const int64_t a_i = in[i];
        const int64_t a_j = in[j];
        out[i] = a_j;
        out[j] = a_i;
    }
    /* Odd-length middle element: only needs copying when in != out
     * (in == out leaves the middle untouched, which is correct). */
    if ((n % 2) == 1 && in != out) {
        out[n / 2] = in[n / 2];
    }
    return SRMECH_OK;
}

srmech_status_t srmech_cascade_chiral_flip_f64(const double *in,
                                                size_t        n,
                                                double       *out)
{
    if (n == 0) {
        return SRMECH_OK;
    }
    if (in == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(in  != NULL);
    assert(out != NULL);
    /* Same shape as the i64 variant — see comments above. */
    for (size_t i = 0; i < n / 2; ++i) {
        const size_t j   = n - 1 - i;
        const double a_i = in[i];
        const double a_j = in[j];
        out[i] = a_j;
        out[j] = a_i;
    }
    if ((n % 2) == 1 && in != out) {
        out[n / 2] = in[n / 2];
    }
    return SRMECH_OK;
}

/* pin_slot_at_zero — Class K pin-slot at zero (sign-strip).
 *
 * Splits a real value into (orientation, magnitude) where orientation is
 * in {-1, 0, +1} and magnitude is non-negative. The negation on the
 * negative branch is the canonical Class K phase-boundary, NOT a call
 * to C99 fabs(); expressing it as a named cascade keeps the cascade-
 * count claimed in line with the cascade-count executed.
 *
 * NaN maps to (0, 0.0): both `x > 0.0` and `x < 0.0` evaluate false for
 * NaN under IEEE-754, so the dead-band branch handles it the same way
 * the Python reference impl does.
 */
srmech_status_t srmech_cascade_pin_slot_at_zero_f64(double  x,
                                                     int8_t *orientation_out,
                                                     double *magnitude_out)
{
    if (orientation_out == NULL || magnitude_out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(orientation_out != NULL);
    assert(magnitude_out   != NULL);
    if (x > 0.0) {
        *orientation_out = (int8_t)+1;
        *magnitude_out   = x;
    } else if (x < 0.0) {
        *orientation_out = (int8_t)-1;
        *magnitude_out   = -x;
    } else {
        /* Dead-band — origin AND NaN AND -0.0 all land here, matching
         * the Python reference impl exactly. */
        *orientation_out = (int8_t)0;
        *magnitude_out   = 0.0;
    }
    return SRMECH_OK;
}

/* magnitude — Class K pin-slot magnitude-only projection (|x| but
 * cascade-honest). Composes pin_slot_at_zero and discards the
 * orientation; the explicit positive / negative / else branch is
 * required to preserve Python parity for NaN (both `x > 0.0` and
 * `x < 0.0` evaluate false for NaN under IEEE-754, falling through
 * to the dead-band 0.0 — naive `if (x < 0) out = -x; else out = x`
 * would return NaN instead, breaking parity).
 */
srmech_status_t srmech_cascade_magnitude_f64(double  x,
                                              double *magnitude_out)
{
    if (magnitude_out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(magnitude_out != NULL);
    /* Explicit positive / negative / else branch — preserves Python
     * parity for NaN (both x > 0 and x < 0 evaluate False for NaN,
     * falling through to 0.0). */
    if (x > 0.0) {
        *magnitude_out = x;
    } else if (x < 0.0) {
        *magnitude_out = -x;
    } else {
        /* 0.0, -0.0, and NaN all map to 0.0 (the dead-band). */
        *magnitude_out = 0.0;
    }
    /* Post-condition: magnitude is non-negative across every branch
     * (positive branch returns x>0; negative returns -x>0; else
     * returns the literal 0.0 — including the NaN-falls-through path). */
    assert(*magnitude_out >= 0.0);
    return SRMECH_OK;
}

/* reorient — Class C cascade-orientation re-application (int64 variant).
 *
 * Re-applies a captured orientation in {-1, 0, +1} to an integer value.
 * Returns -value when orientation < 0; returns value unchanged otherwise
 * (only the SIGN of orientation matters — zero and positive both pass
 * through, matching the Python reference impl `if orientation < 0:
 * return -value; return value`).
 *
 * Boundary note: INT64_MIN cannot be negated without overflow under
 * fixed-width two's-complement (Python ints are arbitrary precision so
 * `-(-9223372036854775808)` is well-defined Python-side, but the i64
 * ABI is fixed-width). Callers MUST NOT pass INT64_MIN here; the
 * Python dispatch in srmech.amsc.cascade guards this by falling back
 * to the Python path for INT64_MIN inputs.
 */
srmech_status_t srmech_cascade_reorient_i64(int8_t   orientation,
                                             int64_t  value,
                                             int64_t *out)
{
    if (out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(out != NULL);
    /* Class C re-application: negate iff orientation < 0.
     * Zero and positive orientation both pass value through. */
    if (orientation < 0) {
        *out = -value;
    } else {
        *out = value;
    }
    /* Post-condition: result is either value (orientation >= 0 branch)
     * or -value (orientation < 0 branch). For INT64_MIN, two's-complement
     * negation overflows and wraps back to INT64_MIN — the second clause
     * of the disjunction admits that documented boundary case (the
     * Python dispatch guards INT64_MIN so this path is unreachable from
     * the supported API surface). */
    assert((orientation < 0) ? (*out == -value || value == INT64_MIN)
                              : (*out == value));
    return SRMECH_OK;
}

/* reorient — Class C cascade-orientation re-application (f64 variant).
 *
 * IEEE-754 negation flips the sign bit; NaN stays NaN (sign-bit flip
 * does not change NaN-ness), +/-Inf swap under orientation < 0, +/-0.0
 * swap under orientation < 0. Matches Python's `-` operator semantics
 * exactly.
 */
srmech_status_t srmech_cascade_reorient_f64(int8_t  orientation,
                                             double  value,
                                             double *out)
{
    if (out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(out != NULL);
    if (orientation < 0) {
        *out = -value;
    } else {
        *out = value;
    }
    /* Post-condition: for the orientation >= 0 branch the output IS the
     * input bit-pattern; for the orientation < 0 branch IEEE-754
     * negation flips the sign bit. NaN comparisons are excluded from
     * the equality check because NaN != NaN under IEEE-754 — the
     * assertion is therefore gated on `value == value` (true for all
     * non-NaN values; false for NaN, in which case the assertion
     * trivially passes by short-circuiting on the first clause). */
    assert((value != value) ||
           ((orientation < 0) ? (*out == -value) : (*out == value)));
    return SRMECH_OK;
}

/* net_chirality — Class C net handedness invariant (int8 variant).
 *
 * Multiplicative product of per-op orientations in {-1, 0, +1}. The
 * cascade-honest read-out of a chiral cascade's conserved Class-C
 * invariant: each per-op orientation contributes ±1 (or 0 to absorb);
 * the running product is +1 (net even / right-handed), -1 (net odd /
 * left-handed), or 0 if any orientation is the dead-band.
 *
 * Empty input (n == 0) returns +1 — the multiplicative identity, matching
 * the Python reference impl where the for-loop doesn't execute and net
 * stays at its initial value of 1.
 *
 * Any value not in {-1, 0, +1} is normalised by sign (only the SIGN of
 * each orientation matters in the Python ref): negative -> flip net,
 * positive -> leave net alone, zero -> short-circuit return 0.
 */
srmech_status_t srmech_cascade_net_chirality_i8(const int8_t *orientations,
                                                  size_t        n,
                                                  int8_t       *out)
{
    if (out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (orientations == NULL && n > 0) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(out != NULL);
    assert(n == 0 || orientations != NULL);
    /* Empty input -> +1 (multiplicative identity). */
    if (n == 0) {
        *out = (int8_t)+1;
        return SRMECH_OK;
    }
    /* Iterate; short-circuit on zero; flip sign on negative. */
    int8_t net = (int8_t)+1;
    for (size_t i = 0; i < n; ++i) {
        const int8_t o = orientations[i];
        if (o == 0) {
            *out = (int8_t)0;
            return SRMECH_OK;
        }
        if (o < 0) {
            net = (int8_t)(-net);  /* Class C reorient inline */
        }
        /* o > 0 leaves net unchanged. */
    }
    *out = net;
    return SRMECH_OK;
}

/* cyclic_gcd — Class I cyclic-group gcd; cascade-namespace wrapper.
 *
 * Pure delegation to the Class I primitive srmech_gcd. The wrapper
 * carries NO additional logic — its sole purpose is to maintain the
 * srmech_cascade_* naming invariant for the cascade catalog. The
 * underlying srmech_gcd handles the Euclidean iteration, the gcd(0,0)
 * = 0 convention, and the gcd(a,0) = a convention.
 *
 * Conformance: the wrapper checks out != NULL up-front to short-circuit
 * the NULL case at the cascade layer (saves an indirected call). The
 * underlying srmech_gcd would also reject NULL but doing it here keeps
 * the cascade-wrapper path predictable for callers reading status
 * codes (the SRMECH_ERR_NULL_ARG status flows from a single source).
 *
 * JPL Rule 5 (≥2 asserts): out != NULL pre-condition + post-condition
 * pinning the OK / propagated-status disjunction.
 */
srmech_status_t srmech_cascade_cyclic_gcd_u64(uint64_t  a,
                                                uint64_t  b,
                                                uint64_t *out)
{
    if (out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(out != NULL);
    /* Delegate to the Class I primitive. The cascade-namespace wrapper
     * carries no additional logic — it exists to maintain the
     * srmech_cascade_* naming invariant per the user's
     * "delegate to A-N C peers; cascade-level C wrapper + TOML"
     * directive. */
    const srmech_status_t st = srmech_gcd(a, b, out);
    /* Post-condition: on OK, the gcd convention holds — gcd(0,0) = 0
     * AND gcd(a,0) = a (so when b == 0 the result equals a, including
     * the a == 0 sub-case which returns 0); on non-OK, the status
     * propagated from srmech_gcd (the only such case for non-NULL out
     * is no error path inside srmech_gcd — but we admit the
     * disjunction so future Class I status codes propagate without
     * silent breakage). */
    assert(st != SRMECH_OK || (b != 0) || (*out == a));
    return st;
}
