/*
 * srmech_qi.c — the EXACT-complex (Gaussian-rational) carrier's C-host peer
 * (0.9.0rc15; the NORTH STAR C-host parity for the `Qi` carrier in
 * srmech/amsc/qi.py).
 *
 * A `Qi` value is the exact complex `re + im·i` over ℚ, carried as FOUR
 * integer limbs: `{re_num, re_den, im_num, im_den}`. Denominators are
 * positive and fit `int64` (the Python `Q` carrier hands reduced positive
 * pairs; the unbounded `fractions.Fraction` path is the oracle past the
 * int64 limb domain). This peer lets a C-ONLY host — no Python — do exact
 * Gaussian-rational arithmetic in a single call per op, the way Python's
 * `Qi.__mul__` etc. route through it when the limbs fit int64.
 *
 * Each op is a NAMED A–N cascade, composed from the exported Class-N
 * rational ops (`srmech_rational_add` / `srmech_rational_mul` in
 * srmech_rational.c) — bit-exact, no float, no libm, no malloc:
 *
 *   - srmech_qi_add / _sub / _mul : Class M (bilinear bind) ∘ Class C
 *                                   (cross-term order). mul is the Gaussian
 *                                   identity (ac−bd) + (ad+bc)i.
 *   - srmech_qi_conjugate         : Class K — the im sign-flip (never abs()).
 *   - srmech_qi_quadrant          : Class C orientation → the Klein-4 sector
 *                                   (bit0 = re<0, bit1 = im<0).
 *   - srmech_qi_norm_sq           : Class N anchor — re² + im² (exact ℚ).
 *
 * NO bignum (the user's fixed-limb mandate): any intermediate that escapes
 * the int64/uint64 limb domain returns SRMECH_ERR_OVERFLOW, and the Python
 * `Qi` carrier falls through to its exact-`Fraction` path (the unbounded
 * reference). This is the same documented domain ceiling as the rc13 isqrt
 * (n ≥ 2^128 → bignum) — a genuine no-bignum representation boundary, not a
 * compiled-in cap.
 *
 * Carrier-internal, like the `Mat`/`Vec` native dense kernels: NOT a Rosetta
 * ledger op (no ToolEntry, no count-test). Additive symbols → ABI unchanged.
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto/recursion): OK — straight-line composition
 *   - Rule 2 (bounded loops)    : OK — no loops
 *   - Rule 3 (no malloc)        : OK — caller-owned out params only
 *   - Rule 4 (≤60 lines/func)   : OK
 *   - Rule 5 (≥2 asserts/fn)    : OK — entry-pointer + post/precondition
 *   - Rule 7 (return-value)     : OK — srmech_status_t throughout
 *   - Rule 10 (warnings clean)  : OK under -Wall -Wextra -Wpedantic -Werror
 *
 * License: MIT.
 */

#include "srmech.h"

#include <assert.h>
#include <stdint.h>

/* Helper — validate one Qi limb-vector: denominators strictly positive. */
static srmech_status_t qi_check(const int64_t v[4])
{
    assert(v != NULL);
    if (v == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (v[1] <= 0 || v[3] <= 0) {
        return SRMECH_ERR_BAD_INPUT;
    }
    assert(v[1] > 0 && v[3] > 0);
    return SRMECH_OK;
}

/* Helper — Class-K sign-flip on one int64; INT64_MIN has no representable
 * negation (no bignum) so report SRMECH_ERR_OVERFLOW. Never an ALU abs(). */
static srmech_status_t qi_negate(int64_t x, int64_t *out)
{
    assert(out != NULL);
    if (x == INT64_MIN) {
        return SRMECH_ERR_OVERFLOW;
    }
    *out = -x;
    assert(*out == -x);
    return SRMECH_OK;
}

/* Helper — product of two (num, den) rationals via the exported Class-N op,
 * with the reduced denominator clamped back into the int64 limb domain
 * (Qi limbs are int64; a reduced den past INT64_MAX returns OVERFLOW). */
static srmech_status_t qi_rat_mul(int64_t an, int64_t ad, int64_t bn, int64_t bd,
                                  int64_t *on, int64_t *od)
{
    assert(on != NULL && od != NULL);
    assert(ad > 0 && bd > 0);
    uint64_t od_u = 0;
    srmech_status_t st = srmech_rational_mul(an, (uint64_t)ad, bn, (uint64_t)bd,
                                             on, &od_u);
    if (st != SRMECH_OK) {
        return st;
    }
    if (od_u > (uint64_t)INT64_MAX) {
        return SRMECH_ERR_OVERFLOW;
    }
    *od = (int64_t)od_u;
    return SRMECH_OK;
}

/* Helper — sum of two (num, den) rationals via the exported Class-N op, with
 * the reduced denominator clamped back into the int64 limb domain. */
static srmech_status_t qi_rat_add(int64_t an, int64_t ad, int64_t bn, int64_t bd,
                                  int64_t *on, int64_t *od)
{
    assert(on != NULL && od != NULL);
    assert(ad > 0 && bd > 0);
    uint64_t od_u = 0;
    srmech_status_t st = srmech_rational_add(an, (uint64_t)ad, bn, (uint64_t)bd,
                                             on, &od_u);
    if (st != SRMECH_OK) {
        return st;
    }
    if (od_u > (uint64_t)INT64_MAX) {
        return SRMECH_ERR_OVERFLOW;
    }
    *od = (int64_t)od_u;
    return SRMECH_OK;
}

srmech_status_t srmech_qi_add(const int64_t a[4], const int64_t b[4],
                              int64_t out[4])
{
    assert(a != NULL && b != NULL);
    assert(out != NULL);
    if (a == NULL || b == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    srmech_status_t st = qi_check(a);
    if (st != SRMECH_OK) return st;
    st = qi_check(b);
    if (st != SRMECH_OK) return st;
    st = qi_rat_add(a[0], a[1], b[0], b[1], &out[0], &out[1]);
    if (st != SRMECH_OK) return st;
    return qi_rat_add(a[2], a[3], b[2], b[3], &out[2], &out[3]);
}

srmech_status_t srmech_qi_sub(const int64_t a[4], const int64_t b[4],
                              int64_t out[4])
{
    assert(a != NULL && b != NULL);
    assert(out != NULL);
    if (a == NULL || b == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    srmech_status_t st = qi_check(a);
    if (st != SRMECH_OK) return st;
    st = qi_check(b);
    if (st != SRMECH_OK) return st;
    int64_t nb0 = 0, nb2 = 0;
    st = qi_negate(b[0], &nb0);
    if (st != SRMECH_OK) return st;
    st = qi_negate(b[2], &nb2);
    if (st != SRMECH_OK) return st;
    st = qi_rat_add(a[0], a[1], nb0, b[1], &out[0], &out[1]);
    if (st != SRMECH_OK) return st;
    return qi_rat_add(a[2], a[3], nb2, b[3], &out[2], &out[3]);
}

srmech_status_t srmech_qi_mul(const int64_t a[4], const int64_t b[4],
                              int64_t out[4])
{
    assert(a != NULL && b != NULL);
    assert(out != NULL);
    if (a == NULL || b == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    srmech_status_t st = qi_check(a);
    if (st != SRMECH_OK) return st;
    st = qi_check(b);
    if (st != SRMECH_OK) return st;
    /* re = a_re·b_re − a_im·b_im (Class M bind ∘ Class C cross-term order) */
    int64_t t1n = 0, t1d = 0, t2n = 0, t2d = 0, neg = 0;
    st = qi_rat_mul(a[0], a[1], b[0], b[1], &t1n, &t1d);
    if (st != SRMECH_OK) return st;
    st = qi_rat_mul(a[2], a[3], b[2], b[3], &t2n, &t2d);
    if (st != SRMECH_OK) return st;
    st = qi_negate(t2n, &neg);
    if (st != SRMECH_OK) return st;
    st = qi_rat_add(t1n, t1d, neg, t2d, &out[0], &out[1]);
    if (st != SRMECH_OK) return st;
    /* im = a_re·b_im + a_im·b_re */
    int64_t t3n = 0, t3d = 0, t4n = 0, t4d = 0;
    st = qi_rat_mul(a[0], a[1], b[2], b[3], &t3n, &t3d);
    if (st != SRMECH_OK) return st;
    st = qi_rat_mul(a[2], a[3], b[0], b[1], &t4n, &t4d);
    if (st != SRMECH_OK) return st;
    return qi_rat_add(t3n, t3d, t4n, t4d, &out[2], &out[3]);
}

srmech_status_t srmech_qi_conjugate(const int64_t a[4], int64_t out[4])
{
    assert(a != NULL);
    assert(out != NULL);
    if (a == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    srmech_status_t st = qi_check(a);
    if (st != SRMECH_OK) return st;
    int64_t neg = 0;
    st = qi_negate(a[2], &neg);    /* Class K — im sign-flip (never abs()) */
    if (st != SRMECH_OK) return st;
    out[0] = a[0];
    out[1] = a[1];
    out[2] = neg;
    out[3] = a[3];
    return SRMECH_OK;
}

srmech_status_t srmech_qi_quadrant(const int64_t a[4], int *out_quadrant)
{
    assert(a != NULL);
    assert(out_quadrant != NULL);
    if (a == NULL || out_quadrant == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    srmech_status_t st = qi_check(a);
    if (st != SRMECH_OK) return st;
    /* Class C orientation → Klein-4 sector: bit0 = re<0, bit1 = im<0. */
    int bit_re = (a[0] < 0) ? 1 : 0;
    int bit_im = (a[2] < 0) ? 1 : 0;
    *out_quadrant = bit_re | (bit_im << 1);
    assert(*out_quadrant >= 0 && *out_quadrant <= 3);
    return SRMECH_OK;
}

srmech_status_t srmech_qi_norm_sq(const int64_t a[4], int64_t out[2])
{
    assert(a != NULL);
    assert(out != NULL);
    if (a == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    srmech_status_t st = qi_check(a);
    if (st != SRMECH_OK) return st;
    /* |z|² = re² + im² (Class N rational anchor; non-negative). */
    int64_t t1n = 0, t1d = 0, t2n = 0, t2d = 0;
    st = qi_rat_mul(a[0], a[1], a[0], a[1], &t1n, &t1d);
    if (st != SRMECH_OK) return st;
    st = qi_rat_mul(a[2], a[3], a[2], a[3], &t2n, &t2d);
    if (st != SRMECH_OK) return st;
    st = qi_rat_add(t1n, t1d, t2n, t2d, &out[0], &out[1]);
    if (st != SRMECH_OK) return st;
    assert(out[0] >= 0 && out[1] > 0);
    return SRMECH_OK;
}
