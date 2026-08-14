/*
 * srmech_cyclic.c — Class I primitive: cyclic-group / modular arithmetic.
 *
 * Task #217 Phase C1 first ship — six load-bearing modular-arithmetic
 * operations on uint64_t. These are the foundation for cyclic-cascade
 * composition (Phase C2's MFO/SM/QM operations layer): every cyclic
 * factor C_n in a cascade exposes order, mode-index arithmetic, and
 * period operations that ultimately reduce to the six primitives here.
 *
 * Class I appears in Spike #24's cumulative cross-substrate audit at
 * five of six bonus substrates (tactical, SHA-256, MFO 3+7+1, RNG,
 * cascade composition — every place a cyclic group instantiates).
 *
 * Convention: every public function returns srmech_status_t and writes
 * its result to a caller-owned *out pointer. No malloc, no goto, all
 * loops have fixed compile-time upper bounds (≤128 iterations, which
 * exceeds Fibonacci-worst-case for uint64 Euclidean ~91).
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto)        : OK
 *   - Rule 2 (bounded loops)  : OK — 64 (bit-width) / 128 (Fibonacci)
 *   - Rule 3 (no malloc)      : OK
 *   - Rule 4 (≤60 lines/func) : OK — longest is mod_inv at ~40
 *   - Rule 5 (≥2 asserts/fn)  : OK — input ptr + post-condition each
 *   - Rule 7 (return-value)   : OK — srmech_status_t throughout
 *   - Rule 10 (warnings clean): OK under -Wall -Wextra -Wpedantic
 *
 * License: MIT.
 */

#include "srmech.h"

#include <assert.h>
#include <stdint.h>

/* Fibonacci-worst-case for uint64 Euclidean is ~91 iterations; 128 is
 * a safe over-bound for any reachable input. */
#define SRMECH_CYCLIC_EUCLID_CAP 128

/* uint64 bit-width — bound for square-and-multiply / russian-peasant. */
#define SRMECH_CYCLIC_UINT64_BITS 64

srmech_status_t srmech_gcd(uint64_t a, uint64_t b, uint64_t *out)
{
    assert(out != NULL);
    if (out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    /* Euclidean GCD. Conventional gcd(0, 0) = 0; gcd(a, 0) = a. */
    for (int i = 0; i < SRMECH_CYCLIC_EUCLID_CAP; i++) {
        if (b == 0) {
            *out = a;
            return SRMECH_OK;
        }
        uint64_t t = b;
        b = a % b;
        a = t;
    }
    /* Unreachable for valid uint64 inputs (Fibonacci cap is ~91). */
    assert(0 && "srmech_gcd exceeded bounded iteration cap");
    return SRMECH_ERR_INTERNAL;
}

srmech_status_t srmech_lcm(uint64_t a, uint64_t b, uint64_t *out)
{
    assert(out != NULL);
    if (out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (a == 0 || b == 0) {
        *out = 0;
        return SRMECH_OK;
    }
    uint64_t g = 0;
    srmech_status_t st = srmech_gcd(a, b, &g);
    if (st != SRMECH_OK) {
        return st;
    }
    assert(g != 0);
    uint64_t a_over_g = a / g;
    /* Overflow guard: a_over_g * b must fit in uint64. */
    if (a_over_g != 0 && b > UINT64_MAX / a_over_g) {
        return SRMECH_ERR_OVERFLOW;
    }
    *out = a_over_g * b;
    return SRMECH_OK;
}

srmech_status_t srmech_mod_add(uint64_t a, uint64_t b, uint64_t n,
                               uint64_t *out)
{
    assert(out != NULL);
    if (out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n == 0) {
        return SRMECH_ERR_BAD_INPUT;
    }
    a %= n;
    b %= n;
    /* Overflow-safe (a + b) mod n: a + b could exceed UINT64_MAX, but
     * after reduction a < n and b < n. If a >= n - b then a + b wraps
     * past n, so subtract (n - b) from a; else a + b is safe. */
    if (a >= n - b) {
        *out = a - (n - b);
    } else {
        *out = a + b;
    }
    assert(*out < n);
    return SRMECH_OK;
}

srmech_status_t srmech_mod_mul(uint64_t a, uint64_t b, uint64_t n,
                               uint64_t *out)
{
    assert(out != NULL);
    if (out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n == 0) {
        return SRMECH_ERR_BAD_INPUT;
    }
    a %= n;
    b %= n;
    /* Russian-peasant doubling: accumulate (b's bits × a) mod n.
     * Bounded by 64 iterations (uint64 bit-width). Portable to
     * platforms without __int128 / _umul128. */
    uint64_t result = 0;
    for (int i = 0; i < SRMECH_CYCLIC_UINT64_BITS; i++) {
        if ((b & 1U) != 0U) {
            /* result = (result + a) mod n, overflow-safe */
            if (result >= n - a) {
                result = result - (n - a);
            } else {
                result += a;
            }
        }
        b >>= 1;
        /* a = (2 * a) mod n, overflow-safe */
        if (a >= n - a) {
            a = a - (n - a);
        } else {
            a += a;
        }
    }
    assert(result < n);
    *out = result;
    return SRMECH_OK;
}

srmech_status_t srmech_mod_pow(uint64_t a, uint64_t k, uint64_t n,
                               uint64_t *out)
{
    assert(out != NULL);
    if (out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n == 0) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (n == 1) {
        /* Everything is 0 mod 1, including 0^0 by convention here. */
        *out = 0;
        return SRMECH_OK;
    }
    /* Square-and-multiply. Bounded by 64 iterations (uint64 bit-width). */
    uint64_t result = 1;
    a %= n;
    for (int i = 0; i < SRMECH_CYCLIC_UINT64_BITS; i++) {
        if ((k & 1U) != 0U) {
            srmech_status_t st = srmech_mod_mul(result, a, n, &result);
            if (st != SRMECH_OK) {
                return st;
            }
        }
        k >>= 1;
        srmech_status_t st = srmech_mod_mul(a, a, n, &a);
        if (st != SRMECH_OK) {
            return st;
        }
    }
    assert(result < n);
    *out = result;
    return SRMECH_OK;
}

srmech_status_t srmech_mod_inv(uint64_t a, uint64_t n, uint64_t *out)
{
    assert(out != NULL);
    if (out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n == 0 || n == 1) {
        return SRMECH_ERR_BAD_INPUT;
    }
    /* Extended-Euclidean uses int64 intermediates for the Bezout
     * coefficients; safely representable while n ≤ INT64_MAX. */
    if (n > (uint64_t)INT64_MAX) {
        return SRMECH_ERR_OVERFLOW;
    }
    a %= n;
    if (a == 0) {
        /* gcd(0, n) = n ≠ 1; no inverse exists. */
        return SRMECH_ERR_BAD_INPUT;
    }
    int64_t old_r = (int64_t)a;
    int64_t r     = (int64_t)n;
    int64_t old_s = 1;
    int64_t s     = 0;
    for (int i = 0; i < SRMECH_CYCLIC_EUCLID_CAP; i++) {
        if (r == 0) {
            break;
        }
        int64_t q   = old_r / r;
        int64_t tmp = old_r - q * r;
        old_r = r;
        r     = tmp;
        tmp   = old_s - q * s;
        old_s = s;
        s     = tmp;
    }
    assert(old_r > 0);
    if (old_r != 1) {
        /* gcd(a, n) ≠ 1; inverse does not exist. */
        return SRMECH_ERR_BAD_INPUT;
    }
    /* old_s might be negative; normalise into [0, n). */
    int64_t signed_n = (int64_t)n;
    int64_t inv      = old_s % signed_n;
    if (inv < 0) {
        inv += signed_n;
    }
    assert(inv >= 0 && inv < signed_n);
    *out = (uint64_t)inv;
    return SRMECH_OK;
}

srmech_status_t srmech_three_cycle(uint64_t value, uint64_t *out)
{
    assert(out != NULL);
    if (out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    /* Harmonic-3 Z/3 generator (F150): (value + 1) mod 3, read on the
     * residue class of value. Computed as ((value % 3) + 1) % 3 to stay
     * overflow-safe at value == UINT64_MAX (value + 1 would wrap). */
    *out = ((value % 3u) + 1u) % 3u;
    assert(*out < 3u);
    return SRMECH_OK;
}

/* ------------------------------------------------------------------ *
 * Class I ∘ K ∘ C — primitive integer vector (0.9.0rc378, task T1049).
 *
 * The smallest integer vector on the same ray as a rational vector:
 * clear denominators by their LCM (Class I), strip the content = gcd of
 * the entry magnitudes (Class I / Class K magnitude), then pin the first
 * nonzero entry positive (Class K pin-slot + Class C reorient — NEVER an
 * abs()). Signed int64 FAST PATH: any entry == INT64_MIN, or any int64
 * intermediate overflow, returns SRMECH_ERR_OVERFLOW so the caller's
 * arbitrary-precision pure-Python body takes over (bit-identical result).
 * INT64_MIN is out of domain so every internal negation is representable.
 * ------------------------------------------------------------------ */

/* a * b into int64 with an overflow guard. Returns SRMECH_ERR_OVERFLOW when
 * the exact product leaves [INT64_MIN, INT64_MAX]. Magnitude test in uint64,
 * then the sign is re-applied (Class K pin-slot ∘ Class C reorient, no abs). */
static srmech_status_t srmech_piv_mul_checked(int64_t a, int64_t b,
                                              int64_t *out)
{
    assert(out != NULL);
    assert(a != INT64_MIN && b != INT64_MIN);
    if (out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (a == 0 || b == 0) {
        *out = 0;
        return SRMECH_OK;
    }
    uint64_t ma = (uint64_t)(a < 0 ? -a : a);
    uint64_t mb = (uint64_t)(b < 0 ? -b : b);
    int neg = (a < 0) ^ (b < 0);
    /* Cap the MAGNITUDE at INT64_MAX for BOTH signs: a product of exactly
     * 2^63 would force a later -(INT64_MIN) (signed overflow / UB), so it is
     * treated as overflow → the caller's exact bignum path handles it. */
    if (ma > (uint64_t)INT64_MAX / mb) {
        return SRMECH_ERR_OVERFLOW;
    }
    uint64_t prod = ma * mb;
    *out = neg ? -(int64_t)prod : (int64_t)prod;
    return SRMECH_OK;
}

/* LCM of the denominator MAGNITUDES (Class I) into *lcm_out, int64-bounded
 * (SRMECH_ERR_OVERFLOW past INT64_MAX). dens[i] is validated != 0, != MIN. */
static srmech_status_t srmech_piv_dens_lcm(const int64_t *dens, size_t n,
                                           int64_t *lcm_out)
{
    assert(dens != NULL);
    assert(lcm_out != NULL);
    uint64_t acc = 1;
    for (size_t i = 0; i < n; i++) {
        uint64_t dmag = (uint64_t)(dens[i] < 0 ? -dens[i] : dens[i]);
        uint64_t l = 0;
        srmech_status_t st = srmech_lcm(acc, dmag, &l);
        if (st != SRMECH_OK) {
            return st;
        }
        if (l > (uint64_t)INT64_MAX) {
            return SRMECH_ERR_OVERFLOW;
        }
        acc = l;
    }
    *lcm_out = (int64_t)acc;
    return SRMECH_OK;
}

/* Fill out[] with the denominator-cleared integer vector: for each i,
 * eff_num = (den<0 ? -num : num), scale = L / |den| (exact), out[i] =
 * eff_num * scale. Any overflow propagates SRMECH_ERR_OVERFLOW. */
static srmech_status_t srmech_piv_clear(const int64_t *nums,
                                        const int64_t *dens, size_t n,
                                        int64_t denom_lcm, int64_t *out)
{
    assert(nums != NULL && dens != NULL && out != NULL);
    assert(denom_lcm > 0);
    for (size_t i = 0; i < n; i++) {
        int64_t dmag = dens[i] < 0 ? -dens[i] : dens[i];
        int64_t eff_num = dens[i] < 0 ? -nums[i] : nums[i];
        int64_t scale = denom_lcm / dmag;      /* exact; dmag | denom_lcm */
        srmech_status_t st = srmech_piv_mul_checked(eff_num, scale, &out[i]);
        if (st != SRMECH_OK) {
            return st;
        }
    }
    return SRMECH_OK;
}

/* Content = gcd of the cleared magnitudes; strip it and pin the first nonzero
 * entry positive (Class K pin-slot ∘ Class C reorient). Writes *out_content. */
static srmech_status_t srmech_piv_strip_and_pin(int64_t *out, size_t n,
                                                int64_t *out_content)
{
    assert(out != NULL);
    assert(out_content != NULL);
    uint64_t g = 0;
    for (size_t i = 0; i < n; i++) {
        uint64_t mag = (uint64_t)(out[i] < 0 ? -out[i] : out[i]);
        srmech_status_t st = srmech_gcd(g, mag, &g);
        if (st != SRMECH_OK) {
            return st;
        }
    }
    if (g == 0) {                              /* the all-zero ray */
        *out_content = 0;
        return SRMECH_OK;
    }
    int neg = 0;                               /* first-nonzero orientation */
    for (size_t i = 0; i < n; i++) {
        if (out[i] != 0) { neg = out[i] < 0; break; }
    }
    int64_t gi = (int64_t)g;                    /* g <= INT64_MAX (MIN excl.) */
    for (size_t i = 0; i < n; i++) {
        int64_t v = out[i] / gi;               /* exact; g | out[i] */
        out[i] = neg ? -v : v;
    }
    *out_content = neg ? -gi : gi;
    return SRMECH_OK;
}

srmech_status_t srmech_primitive_integer_vector(const int64_t *nums,
                                                const int64_t *dens, size_t n,
                                                int64_t *out,
                                                int64_t *out_content)
{
    assert(out_content != NULL);
    assert(n == 0 || (nums != NULL && dens != NULL && out != NULL));
    if (out_content == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    *out_content = 0;
    if (n == 0) {
        return SRMECH_OK;
    }
    if (nums == NULL || dens == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    /* Reject INT64_MIN (magnitude/negation would overflow) + den == 0. */
    for (size_t i = 0; i < n; i++) {
        if (dens[i] == 0) {
            return SRMECH_ERR_BAD_INPUT;
        }
        if (nums[i] == INT64_MIN || dens[i] == INT64_MIN) {
            return SRMECH_ERR_OVERFLOW;
        }
    }
    int64_t denom_lcm = 0;
    srmech_status_t st = srmech_piv_dens_lcm(dens, n, &denom_lcm);
    if (st != SRMECH_OK) {
        return st;
    }
    st = srmech_piv_clear(nums, dens, n, denom_lcm, out);
    if (st != SRMECH_OK) {
        return st;
    }
    return srmech_piv_strip_and_pin(out, n, out_content);
}
