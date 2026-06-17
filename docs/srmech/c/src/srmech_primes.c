/*
 * srmech_primes.c — Class J primitive: prime factorisation / period.
 *
 * Task #217 Phase C1 third ship. Class J appears in Spike #24's
 * cumulative cross-substrate audit as the integer-period / prime-
 * factorisation primitive ("J prime-factorisation/period" in the
 * canonical table), complementing Class I (modular arithmetic) with
 * the non-modular integer-structure operations:
 *
 *   - srmech_is_prime          : trial-division primality test
 *   - srmech_factor            : trial-division prime factorisation
 *   - srmech_cyclic_period     : multiplicative order of a in (Z/nZ)*
 *
 * Pi-free integer arithmetic; no LAPACK; no malloc. Bounded loops via
 * the trial-division terminator d <= n / d (equivalent to d² ≤ n, no
 * overflow) and caller-supplied max_count / max_k caps for the
 * fixed-size-buffer operations.
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto)        : OK
 *   - Rule 2 (bounded loops)  : OK — caller-input-length bounded
 *                              (the trial-division loop terminates
 *                              when d² > n; same pattern as srmech_
 *                              sha256.c per the JPL audit doc)
 *   - Rule 3 (no malloc)      : OK
 *   - Rule 4 (≤60 lines/func) : OK
 *   - Rule 5 (≥2 asserts/fn)  : OK
 *   - Rule 7 (return-value)   : OK — srmech_status_t throughout
 *   - Rule 10 (warnings clean): OK under -Wall -Wextra -Wpedantic
 *
 * License: MIT.
 */

#include "srmech.h"

#include <assert.h>
#include <stdbool.h>
#include <stdint.h>

srmech_status_t srmech_is_prime(uint64_t n, bool *out)
{
    assert(out != NULL);
    if (out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    /* Initialise out to false; written again at exit on every path. */
    *out = false;
    assert(*out == false);
    if (n < 2) {
        return SRMECH_OK;
    }
    if (n < 4) {
        /* 2, 3 are prime. */
        *out = true;
        return SRMECH_OK;
    }
    if ((n % 2) == 0) {
        return SRMECH_OK;
    }
    /* Trial division by odd d in [3, sqrt(n)]. The terminator
     * `d <= n / d` avoids the d*d overflow trap and means the loop
     * exits when d² > n. Bounded by sqrt(n) iterations. */
    for (uint64_t d = 3; d <= n / d; d += 2) {
        if ((n % d) == 0) {
            return SRMECH_OK;
        }
    }
    *out = true;
    return SRMECH_OK;
}

srmech_status_t srmech_factor(uint64_t  n,
                              uint64_t *primes,
                              uint8_t  *exponents,
                              uint32_t  max_count,
                              uint32_t *out_count)
{
    assert(primes != NULL);
    assert(out_count != NULL);
    if (primes == NULL || exponents == NULL || out_count == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    *out_count = 0;
    if (n < 2) {
        return SRMECH_OK;
    }
    /* Extract factor 2 separately, then odd factors. */
    if ((n % 2) == 0) {
        if (*out_count >= max_count) {
            return SRMECH_ERR_OVERFLOW;
        }
        primes[*out_count] = 2;
        uint8_t e = 0;
        while ((n % 2) == 0 && e < UINT8_MAX) {
            n /= 2;
            e++;
        }
        exponents[*out_count] = e;
        (*out_count)++;
    }
    /* Odd trial division. Bounded by sqrt(n). */
    for (uint64_t d = 3; d <= n / d; d += 2) {
        if ((n % d) != 0) {
            continue;
        }
        if (*out_count >= max_count) {
            return SRMECH_ERR_OVERFLOW;
        }
        primes[*out_count] = d;
        uint8_t e = 0;
        while ((n % d) == 0 && e < UINT8_MAX) {
            n /= d;
            e++;
        }
        exponents[*out_count] = e;
        (*out_count)++;
    }
    /* Remaining n > 1 is itself prime (largest factor). */
    if (n > 1) {
        if (*out_count >= max_count) {
            return SRMECH_ERR_OVERFLOW;
        }
        primes[*out_count] = n;
        exponents[*out_count] = 1;
        (*out_count)++;
    }
    return SRMECH_OK;
}

srmech_status_t srmech_cyclic_period(uint64_t  a,
                                     uint64_t  n,
                                     uint64_t  max_k,
                                     uint64_t *out_period)
{
    assert(out_period != NULL);
    if (out_period == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n < 2) {
        return SRMECH_ERR_BAD_INPUT;
    }
    assert(n >= 2);
    a %= n;
    /* Order requires gcd(a, n) = 1 (a in (Z/nZ)*); the trivial case
     * a = 0 has no order. */
    if (a == 0) {
        return SRMECH_ERR_BAD_INPUT;
    }
    /* By convention a^0 = 1; smallest k > 0 with a^k ≡ 1 mod n.
     * Trial: k = 1, 2, ..., max_k. By Lagrange's theorem order divides
     * φ(n) ≤ n, so a bound of max_k = n suffices when caller supplies
     * it; tighter is fine if caller knows. */
    if (max_k == 0) {
        return SRMECH_ERR_BAD_INPUT;
    }
    uint64_t cur = 1;
    for (uint64_t k = 1; k <= max_k; k++) {
        srmech_status_t st = srmech_mod_mul(cur, a, n, &cur);
        if (st != SRMECH_OK) {
            return st;
        }
        if (cur == 1) {
            *out_period = k;
            return SRMECH_OK;
        }
    }
    /* No period within max_k. Caller can retry with larger bound or
     * check gcd(a, n) externally if they suspect it isn't 1. */
    return SRMECH_ERR_OVERFLOW;
}
