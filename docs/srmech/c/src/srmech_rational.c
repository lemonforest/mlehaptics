/*
 * srmech_rational.c — Class N primitive: rational-approximation.
 *
 * Task #217 Phase C1 rc6 — Class N earns its C surface per the per-class
 * parity discipline. Pure integer arithmetic on uint64_t; pi-free; no
 * malloc; no LAPACK.
 *
 * Three load-bearing operations:
 *
 *   - srmech_continued_fraction:  simple continued-fraction expansion
 *                                 p/q = [a_0; a_1, a_2, ...] via the
 *                                 Euclidean recurrence
 *   - srmech_best_rational:       best rational p'/q' with q' ≤ bound
 *                                 approximating p/q via continued-
 *                                 fraction convergents
 *   - srmech_exp_series_truncate: exp Taylor partial sum
 *                                 S_N(p/q) = sum_{k=0..N} (p/q)^k / k!
 *                                 as exact rational; bounded N ≤ 20 to
 *                                 keep N! within u64 (Python fallback
 *                                 handles larger N with bignum)
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
#include <stdbool.h>
#include <stdint.h>

/* Fibonacci-worst-case for uint64 Euclidean is ~91 iter; 128 is safe
 * upper bound. Same constant Class I (cyclic) uses. */
#define SRMECH_RATIONAL_EUCLID_CAP 128

/* exp_series_truncate bound: 20! = 2.4e18 < UINT64_MAX = 1.8e19. At
 * num_terms=21 the factorial overflows u64 (21! = 5.1e19). Python
 * srmech.amsc.rational.exp_series_truncate handles larger N via bignum. */
#define SRMECH_EXP_SERIES_MAX_TERMS 20

/* Helper — Euclidean GCD on uint64. Used by exp_series_truncate for the
 * final reduce-to-lowest-terms step. */
static uint64_t exp_series_gcd(uint64_t a, uint64_t b)
{
    assert(b > 0 || a > 0);  /* gcd(0,0) is undefined; caller must avoid */
    /* Rule 2 bound: |a|+|b| strictly decreases each iter; bounded by 64 */
    for (uint32_t i = 0; i < 128; i++) {
        if (b == 0) {
            return a == 0 ? 1 : a;
        }
        uint64_t t = a % b;
        a = b;
        b = t;
    }
    assert(0 && "exp_series_gcd exceeded bounded iteration cap");
    return 1;
}

/* Helper — uint64 multiply with overflow check.
 * Sets *out = a * b if no overflow; returns SRMECH_ERR_OVERFLOW otherwise. */
static srmech_status_t exp_series_mul_u64(uint64_t a,
                                          uint64_t b,
                                          uint64_t *out)
{
    assert(out != NULL);
    assert(a < UINT64_MAX || b < UINT64_MAX);  /* trivial precondition */
    if (a == 0 || b == 0) {
        *out = 0;
        return SRMECH_OK;
    }
    if (a > UINT64_MAX / b) {
        return SRMECH_ERR_OVERFLOW;
    }
    *out = a * b;
    return SRMECH_OK;
}

/* Helper — uint64 power with overflow check. Bounded by max num_terms. */
static srmech_status_t exp_series_pow_u64(uint64_t base,
                                          uint32_t exp,
                                          uint64_t *out)
{
    assert(out != NULL);
    assert(exp <= SRMECH_EXP_SERIES_MAX_TERMS);  /* Rule 2: bounded */
    uint64_t result = 1;
    for (uint32_t i = 0; i < exp; i++) {
        srmech_status_t st = exp_series_mul_u64(result, base, &result);
        if (st != SRMECH_OK) {
            return st;
        }
    }
    *out = result;
    return SRMECH_OK;
}

/* Helper — accumulate one signed term into sum_num with overflow check. */
static srmech_status_t exp_series_accumulate(int64_t *sum_num,
                                             uint64_t term_abs,
                                             bool     term_negative)
{
    assert(sum_num != NULL);
    assert(term_abs <= (uint64_t)INT64_MAX || term_abs == 0);
    if (term_abs > (uint64_t)INT64_MAX) {
        return SRMECH_ERR_OVERFLOW;
    }
    int64_t term_signed = term_negative
                          ? -(int64_t)term_abs
                          :  (int64_t)term_abs;
    if (term_signed > 0 && *sum_num > INT64_MAX - term_signed) {
        return SRMECH_ERR_OVERFLOW;
    }
    if (term_signed < 0 && *sum_num < INT64_MIN - term_signed) {
        return SRMECH_ERR_OVERFLOW;
    }
    *sum_num += term_signed;
    return SRMECH_OK;
}

/* Helper — compute |p|^k * q^(N-k) * (N!/k!) into *out_term_abs. */
static srmech_status_t exp_series_compute_term(uint64_t p_pow,
                                               uint64_t x_den,
                                               uint64_t N_factorial,
                                               uint64_t k_factorial,
                                               uint32_t k,
                                               uint32_t num_terms,
                                               uint64_t *out_term_abs)
{
    assert(out_term_abs != NULL);
    assert(k_factorial > 0);  /* k! is at least 0! = 1 */
    uint64_t q_complement = 0;
    srmech_status_t st = exp_series_pow_u64(x_den, num_terms - k,
                                             &q_complement);
    if (st != SRMECH_OK) {
        return st;
    }
    uint64_t n_over_k = N_factorial / k_factorial;
    uint64_t pq = 0;
    st = exp_series_mul_u64(p_pow, q_complement, &pq);
    if (st != SRMECH_OK) {
        return st;
    }
    return exp_series_mul_u64(pq, n_over_k, out_term_abs);
}

/* Helper — compute N! into *out_N_factorial; overflow check at each step. */
static srmech_status_t exp_series_compute_n_factorial(uint32_t num_terms,
                                                     uint64_t *out_N_factorial)
{
    assert(out_N_factorial != NULL);
    assert(num_terms <= SRMECH_EXP_SERIES_MAX_TERMS);
    *out_N_factorial = 1;
    for (uint32_t k = 1; k <= num_terms; k++) {
        srmech_status_t st = exp_series_mul_u64(*out_N_factorial,
                                                  (uint64_t)k,
                                                  out_N_factorial);
        if (st != SRMECH_OK) {
            return st;
        }
    }
    return SRMECH_OK;
}

/* Helper — one iteration of the main exp-series loop. Adds term_k to
 * sum_num and advances p_pow + k_factorial for the next iteration. */
static srmech_status_t exp_series_add_one_term(int64_t   *sum_num,
                                              uint64_t  *p_pow,
                                              uint64_t  *k_factorial,
                                              uint64_t   p_abs,
                                              uint64_t   x_den,
                                              bool       p_negative,
                                              uint64_t   N_factorial,
                                              uint32_t   k,
                                              uint32_t   num_terms)
{
    assert(sum_num != NULL);
    assert(p_pow != NULL && k_factorial != NULL);
    uint64_t term_abs = 0;
    srmech_status_t st = exp_series_compute_term(*p_pow, x_den, N_factorial,
                                                  *k_factorial, k, num_terms,
                                                  &term_abs);
    if (st != SRMECH_OK) {
        return st;
    }
    bool term_negative = p_negative && ((k % 2u) == 1u);
    st = exp_series_accumulate(sum_num, term_abs, term_negative);
    if (st != SRMECH_OK) {
        return st;
    }
    if (k < num_terms) {
        st = exp_series_mul_u64(*p_pow, p_abs, p_pow);
        if (st != SRMECH_OK) {
            return st;
        }
        st = exp_series_mul_u64(*k_factorial, (uint64_t)(k + 1u),
                                 k_factorial);
        if (st != SRMECH_OK) {
            return st;
        }
    }
    return SRMECH_OK;
}

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

/* Helper — reduce signed (sum_num, sum_den) to lowest terms via gcd.
 * Handles the zero-numerator case explicitly (sum_num == 0 -> 0/1). */
static void exp_series_reduce(int64_t   sum_num,
                              uint64_t  sum_den,
                              int64_t  *out_num,
                              uint64_t *out_den)
{
    assert(out_num != NULL);
    assert(sum_den > 0);
    if (sum_num == 0) {
        *out_num = 0;
        *out_den = 1;
        return;
    }
    uint64_t abs_num = (sum_num < 0) ? (uint64_t)(-sum_num)
                                      : (uint64_t)sum_num;
    uint64_t g = exp_series_gcd(abs_num, sum_den);
    *out_num = sum_num / (int64_t)g;
    *out_den = sum_den / g;
}

/* Compute S_N(p/q) = sum_{k=0..N} (p/q)^k / k! as exact rational.
 *
 * Algorithm: common-denominator integer accumulation.
 *   S_N = sum_num / sum_den where
 *   sum_num = sum_{k=0..N} sign(p)^k * |p|^k * q^(N-k) * (N!/k!)
 *   sum_den = q^N * N!
 * Final result reduced by gcd(|sum_num|, sum_den).
 *
 * Bounded to num_terms ≤ 20 (20! fits u64). Python wrapper falls back
 * to bignum (srmech.amsc.rational.exp_series_truncate) when inputs
 * exceed this bound or any intermediate overflows. Per
 * [[feedback_no_binding_layer_carveout]] the C library is usable
 * STANDALONE — no Python required for catalog-row-shaped inputs.
 */
srmech_status_t srmech_exp_series_truncate(int64_t   x_num,
                                           uint64_t  x_den,
                                           uint32_t  num_terms,
                                           int64_t  *out_num,
                                           uint64_t *out_den)
{
    assert(out_num != NULL);
    assert(out_den != NULL);
    if (out_num == NULL || out_den == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    *out_num = 0;
    *out_den = 1;
    if (x_den == 0) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (num_terms > SRMECH_EXP_SERIES_MAX_TERMS) {
        return SRMECH_ERR_OVERFLOW;
    }
    uint64_t N_factorial = 1;
    srmech_status_t st = exp_series_compute_n_factorial(num_terms,
                                                         &N_factorial);
    if (st != SRMECH_OK) {
        return st;
    }
    uint64_t q_to_N = 0;
    st = exp_series_pow_u64(x_den, num_terms, &q_to_N);
    if (st != SRMECH_OK) {
        return st;
    }
    int64_t  sum_num = 0;
    uint64_t k_factorial = 1;
    uint64_t p_abs = (x_num < 0) ? (uint64_t)(-x_num) : (uint64_t)x_num;
    bool     p_negative = (x_num < 0);
    uint64_t p_pow = 1;
    for (uint32_t k = 0; k <= num_terms; k++) {
        st = exp_series_add_one_term(&sum_num, &p_pow, &k_factorial,
                                      p_abs, x_den, p_negative,
                                      N_factorial, k, num_terms);
        if (st != SRMECH_OK) {
            return st;
        }
    }
    uint64_t sum_den = 0;
    st = exp_series_mul_u64(q_to_N, N_factorial, &sum_den);
    if (st != SRMECH_OK) {
        return st;
    }
    exp_series_reduce(sum_num, sum_den, out_num, out_den);
    return SRMECH_OK;
}

/* ──────────────────────────────────────────────────────────────────────
 * Class N rational arithmetic primitives (rc10).
 *
 * Three load-bearing primitives compose the `cosmos_validation`
 * catalog's Friedmann dark-fraction chain under Phase 2 v1 chain DSL.
 * All three reuse the static helpers above (exp_series_gcd,
 * exp_series_mul_u64) for overflow-checked u64 arithmetic.
 *
 * Each returns SRMECH_ERR_OVERFLOW if any intermediate exceeds u64;
 * Python bignum fallback handles those cases.
 * ────────────────────────────────────────────────────────────────────── */

/* Helper — signed multiply with overflow check. Returns SRMECH_ERR_OVERFLOW
 * if |a*b| exceeds INT64_MAX. */
static srmech_status_t rational_smul_i64(int64_t a, int64_t b, int64_t *out)
{
    assert(out != NULL);
    assert(a != INT64_MIN || b != -1);  /* avoid abs() overflow on INT64_MIN */
    if (a == 0 || b == 0) {
        *out = 0;
        return SRMECH_OK;
    }
    /* |a| * |b| in u64 with overflow check, then re-apply sign */
    uint64_t abs_a = (a < 0) ? (uint64_t)(-a) : (uint64_t)a;
    uint64_t abs_b = (b < 0) ? (uint64_t)(-b) : (uint64_t)b;
    if (abs_a > (uint64_t)INT64_MAX / abs_b) {
        return SRMECH_ERR_OVERFLOW;
    }
    uint64_t product = abs_a * abs_b;
    bool negative = (a < 0) ^ (b < 0);
    *out = negative ? -(int64_t)product : (int64_t)product;
    return SRMECH_OK;
}

/* Helper — reduce signed (num, den) rational to lowest terms in (*out_num,
 * *out_den). Denominator must be positive on input; output denominator
 * is always positive. Handles zero-numerator case explicitly. */
static void rational_reduce(int64_t   num,
                            uint64_t  den,
                            int64_t  *out_num,
                            uint64_t *out_den)
{
    assert(out_num != NULL);
    assert(den > 0);
    if (num == 0) {
        *out_num = 0;
        *out_den = 1;
        return;
    }
    uint64_t abs_num = (num < 0) ? (uint64_t)(-num) : (uint64_t)num;
    uint64_t g = exp_series_gcd(abs_num, den);
    *out_num = num / (int64_t)g;
    *out_den = den / g;
}

srmech_status_t srmech_rational_add(int64_t   a_num,
                                    uint64_t  a_den,
                                    int64_t   b_num,
                                    uint64_t  b_den,
                                    int64_t  *out_num,
                                    uint64_t *out_den)
{
    /* (a_num/a_den) + (b_num/b_den) = (a_num*b_den + b_num*a_den) / (a_den*b_den) */
    assert(out_num != NULL);
    assert(out_den != NULL);
    if (a_den == 0 || b_den == 0) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (a_den > (uint64_t)INT64_MAX || b_den > (uint64_t)INT64_MAX) {
        return SRMECH_ERR_OVERFLOW;
    }
    int64_t lhs = 0, rhs = 0;
    srmech_status_t st = rational_smul_i64(a_num, (int64_t)b_den, &lhs);
    if (st != SRMECH_OK) return st;
    st = rational_smul_i64(b_num, (int64_t)a_den, &rhs);
    if (st != SRMECH_OK) return st;
    if ((lhs > 0 && rhs > INT64_MAX - lhs) ||
        (lhs < 0 && rhs < INT64_MIN - lhs)) {
        return SRMECH_ERR_OVERFLOW;
    }
    int64_t  num = lhs + rhs;
    uint64_t den = 0;
    st = exp_series_mul_u64(a_den, b_den, &den);
    if (st != SRMECH_OK) return st;
    rational_reduce(num, den, out_num, out_den);
    return SRMECH_OK;
}

srmech_status_t srmech_rational_mul(int64_t   a_num,
                                    uint64_t  a_den,
                                    int64_t   b_num,
                                    uint64_t  b_den,
                                    int64_t  *out_num,
                                    uint64_t *out_den)
{
    /* (a_num/a_den) * (b_num/b_den) = (a_num*b_num) / (a_den*b_den) */
    assert(out_num != NULL);
    assert(out_den != NULL);
    if (a_den == 0 || b_den == 0) {
        return SRMECH_ERR_BAD_INPUT;
    }
    int64_t num = 0;
    srmech_status_t st = rational_smul_i64(a_num, b_num, &num);
    if (st != SRMECH_OK) return st;
    uint64_t den = 0;
    st = exp_series_mul_u64(a_den, b_den, &den);
    if (st != SRMECH_OK) return st;
    rational_reduce(num, den, out_num, out_den);
    return SRMECH_OK;
}

srmech_status_t srmech_rational_div(int64_t   a_num,
                                    uint64_t  a_den,
                                    int64_t   b_num,
                                    uint64_t  b_den,
                                    int64_t  *out_num,
                                    uint64_t *out_den)
{
    /* (a_num/a_den) / (b_num/b_den) = (a_num*b_den) / (a_den*b_num).
     * If b_num < 0, negate both to keep denominator positive. */
    assert(out_num != NULL);
    assert(out_den != NULL);
    if (a_den == 0 || b_den == 0 || b_num == 0) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (b_den > (uint64_t)INT64_MAX) {
        return SRMECH_ERR_OVERFLOW;
    }
    int64_t num = 0;
    srmech_status_t st = rational_smul_i64(a_num, (int64_t)b_den, &num);
    if (st != SRMECH_OK) return st;
    /* denom = a_den * |b_num|; sign comes from b_num */
    uint64_t abs_b_num = (b_num < 0) ? (uint64_t)(-b_num) : (uint64_t)b_num;
    uint64_t den = 0;
    st = exp_series_mul_u64(a_den, abs_b_num, &den);
    if (st != SRMECH_OK) return st;
    if (b_num < 0) {
        num = -num;
    }
    rational_reduce(num, den, out_num, out_den);
    return SRMECH_OK;
}

/* Helper — bounded loop for rational_pow_uint, separated to satisfy
 * JPL Rule 4 (≤60 lines per function). */
static srmech_status_t rational_pow_loop(int64_t   base_num,
                                         uint64_t  base_den,
                                         uint32_t  exp_val,
                                         int64_t  *out_num,
                                         uint64_t *out_den)
{
    assert(out_num != NULL);
    assert(exp_val <= 64);  /* Rule 2: bounded */
    int64_t  acc_num = 1;
    uint64_t acc_den = 1;
    for (uint32_t i = 0; i < exp_val; i++) {
        int64_t  next_num = 0;
        srmech_status_t st = rational_smul_i64(acc_num, base_num, &next_num);
        if (st != SRMECH_OK) return st;
        uint64_t next_den = 0;
        st = exp_series_mul_u64(acc_den, base_den, &next_den);
        if (st != SRMECH_OK) return st;
        acc_num = next_num;
        acc_den = next_den;
    }
    rational_reduce(acc_num, acc_den, out_num, out_den);
    return SRMECH_OK;
}

srmech_status_t srmech_rational_pow_uint(int64_t   base_num,
                                         uint64_t  base_den,
                                         uint32_t  exp_val,
                                         int64_t  *out_num,
                                         uint64_t *out_den)
{
    /* (base_num/base_den)^exp; result reduced. */
    assert(out_num != NULL);
    assert(out_den != NULL);
    if (out_num == NULL || out_den == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (base_den == 0) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (exp_val > 64) {
        return SRMECH_ERR_OVERFLOW;
    }
    if (exp_val == 0) {
        *out_num = 1;
        *out_den = 1;
        return SRMECH_OK;
    }
    return rational_pow_loop(base_num, base_den, exp_val, out_num, out_den);
}

/* ──────────────────────────────────────────────────────────────────────
 * Class N — π geometric-cascade primitives (Milestone #4 / Task #245).
 *
 * One load-bearing operation at the C surface for int64-fit cases:
 *
 *   - srmech_cf_convergents_int64:
 *     Given a list of continued-fraction coefficients [a_0; a_1, ...],
 *     produce the convergent ladder (h_k, k_k) for k = 0..n-1 via
 *     the standard recurrence
 *         h_k = a_k * h_{k-1} + h_{k-2}
 *         k_k = a_k * k_{k-1} + k_{k-2}
 *     with h_{-1}=1, h_{-2}=0, k_{-1}=0, k_{-2}=1.
 *
 * Anchored to `[[user_stance_pi_spectral_shape_scalar_invariant]]` —
 * the convergent ladder IS π's substrate identity (Spike #32 / PR #460).
 *
 * Bounded loop (n ≤ 256). All overflow checks return SRMECH_ERR_OVERFLOW;
 * Python wrapper falls back to bignum.
 * ────────────────────────────────────────────────────────────────────── */

#define SRMECH_CF_CONVERGENTS_MAX_N 256

/* Helper — signed-add overflow check on int64. Returns SRMECH_OK and
 * sets *out on success; SRMECH_ERR_OVERFLOW otherwise. */
static srmech_status_t cf_conv_sadd_i64(int64_t a, int64_t b, int64_t *out)
{
    assert(out != NULL);
    /* Rule 5 second assert: precondition invariant — INT64_MIN
     * cannot be safely negated, so callers that hand both INT64_MIN
     * inputs would step into UB on the overflow check below. We
     * forbid the corner case as a precondition. (Same shape as
     * rational_smul_i64's assert pattern in this file.) */
    assert(!(a == INT64_MIN && b == INT64_MIN));
    if ((b > 0 && a > INT64_MAX - b) || (b < 0 && a < INT64_MIN - b)) {
        return SRMECH_ERR_OVERFLOW;
    }
    *out = a + b;
    return SRMECH_OK;
}

/* Helper — one CF convergent step: compute (h_next, k_next) =
 * (a * h_prev + h_curr, a * k_prev + k_curr) with overflow checks. */
static srmech_status_t cf_conv_step(int64_t a,
                                    int64_t h_prev,
                                    int64_t h_curr,
                                    int64_t k_prev,
                                    int64_t k_curr,
                                    int64_t *out_h_next,
                                    int64_t *out_k_next)
{
    assert(out_h_next != NULL);
    assert(out_k_next != NULL);
    int64_t a_h = 0;
    srmech_status_t st = rational_smul_i64(a, h_prev, &a_h);
    if (st != SRMECH_OK) return st;
    int64_t a_k = 0;
    st = rational_smul_i64(a, k_prev, &a_k);
    if (st != SRMECH_OK) return st;
    st = cf_conv_sadd_i64(a_h, h_curr, out_h_next);
    if (st != SRMECH_OK) return st;
    return cf_conv_sadd_i64(a_k, k_curr, out_k_next);
}

srmech_status_t srmech_cf_convergents_int64(const int64_t *coefs,
                                            size_t         n,
                                            int64_t       *out_nums,
                                            int64_t       *out_dens)
{
    /* Convergent ladder for a continued-fraction coefficient list.
     * Standard recurrence with overflow guards on every multiply +
     * add; SRMECH_ERR_OVERFLOW the moment any convergent escapes int64.
     * Bounded loop n ≤ SRMECH_CF_CONVERGENTS_MAX_N. */
    assert(out_nums != NULL);
    assert(out_dens != NULL);
    if (coefs == NULL || out_nums == NULL || out_dens == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n == 0 || n > SRMECH_CF_CONVERGENTS_MAX_N) {
        return SRMECH_ERR_BAD_INPUT;
    }
    int64_t h_prev = 1;   /* h_{-1} */
    int64_t h_curr = 0;   /* h_{-2}  (here we keep "prev" = h_{k-1} and "curr" = h_{k-2}) */
    int64_t k_prev = 0;   /* k_{-1} */
    int64_t k_curr = 1;   /* k_{-2} */
    for (size_t i = 0; i < n; i++) {
        int64_t h_next = 0;
        int64_t k_next = 0;
        srmech_status_t st = cf_conv_step(coefs[i],
                                          h_prev, h_curr,
                                          k_prev, k_curr,
                                          &h_next, &k_next);
        if (st != SRMECH_OK) {
            return st;
        }
        out_nums[i] = h_next;
        out_dens[i] = k_next;
        h_curr = h_prev;
        h_prev = h_next;
        k_curr = k_prev;
        k_prev = k_next;
    }
    return SRMECH_OK;
}
