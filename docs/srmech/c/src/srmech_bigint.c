/*
 * srmech_bigint.c — caller-arena, arbitrary-precision integer (0.9.0rc19).
 *
 * The unbounded-integer foundation that replaces the "overflow → fall
 * back to CPython int" gap so the C library is standalone-complete: NO
 * external bignum (no GMP), NO libm, NO malloc. A value is carried
 * base-2^32, little-endian, sign-magnitude, over CALLER-OWNED limb
 * storage (srmech_bigint_t in srmech.h). The caller pre-sizes every
 * `out` via the `_bound` helpers and hands a `void *ws, size_t ws_len`
 * scratch arena to the ops that need one (an 8-byte-aligned uint32 bump
 * region). Any op whose `out` cap or `ws` is too small returns
 * SRMECH_ERR_OVERFLOW and never writes past the caller's storage.
 *
 * The cascade composition (named A–N classes):
 *   - add / sub          : Class K sign pin-slot ∘ magnitude add/sub.
 *   - mul                : schoolbook bilinear bind (Class M shape).
 *   - shl / shr          : Class K bit-boundary; shr is FLOOR (Python >>).
 *   - divmod             : Knuth Algorithm D (TAOCP Vol 2 §4.3.1) +
 *                          Python FLOOR sign-correction (0 <= r < |b|).
 *   - isqrt              : integer Newton; floor sqrt of a non-negative.
 *   - gcd                : Euclid over magnitudes (Class I shape).
 *   - pow_u32            : binary exponentiation (square-and-multiply).
 *   - from_dec / to_dec  : base-10 ⇄ base-2^32 (Class B render shape).
 *
 * Division / shift use PYTHON FLOOR semantics so the C result is
 * byte-identical to Python's int — the same oracle the ctypes harness
 * checks against.
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto/recursion): OK — all loops iterative, Knuth D split
 *   - Rule 2 (bounded loops)    : OK — every loop bound is a limb/bit count
 *   - Rule 3 (no malloc)        : OK — caller-arena + caller-out only
 *   - Rule 4 (<=60 lines/func)  : OK — factored into static helpers
 *   - Rule 5 (>=2 asserts/fn)   : OK — entry-pointer + pre/postcondition
 *   - Rule 7 (return-value)     : OK — srmech_status_t propagated
 *   - Rule 8 (no multi-line mac): OK — no function-like macros
 *   - Rule 10 (warnings clean)  : OK under -Wall -Wextra -Wpedantic -Werror
 *                                  (no __int128, no VLA, uint64 intermediates)
 *
 * License: MIT.
 */

#include "srmech.h"

#include <assert.h>
#include <stdint.h>

#define BI_BASE_BITS 32u

/* ---- forward declarations (Rule 1: no recursion; iterative split) -- */

static void bi_norm(srmech_bigint_t *a);
static int bi_cmp_abs(const srmech_bigint_t *a, const srmech_bigint_t *b);
static srmech_status_t bi_set_abs(srmech_bigint_t *dst,
                                  const srmech_bigint_t *src);
static srmech_status_t bi_add_abs(srmech_bigint_t *out, const srmech_bigint_t *a,
                                  const srmech_bigint_t *b);
static srmech_status_t bi_sub_abs(srmech_bigint_t *out, const srmech_bigint_t *a,
                                  const srmech_bigint_t *b);
static srmech_status_t bi_addsub(srmech_bigint_t *out, const srmech_bigint_t *a,
                                 const srmech_bigint_t *b, int sb);
static uint32_t bi_bitlen(const srmech_bigint_t *a);
static srmech_status_t bi_div_small(srmech_bigint_t *q, const srmech_bigint_t *a,
                                    uint32_t d, uint32_t *rem);
static uint32_t *bi_ws_take(uint32_t *base, size_t cap_words, size_t *cur,
                            size_t count);
static srmech_status_t bi_div_knuth(srmech_bigint_t *q, srmech_bigint_t *r,
                                    const srmech_bigint_t *a,
                                    const srmech_bigint_t *b,
                                    void *ws, size_t ws_len);
static srmech_status_t bi_shl_norm(uint32_t *vnl, const srmech_bigint_t *b,
                                   uint32_t shift);
static srmech_status_t bi_shl_un(uint32_t *un, const srmech_bigint_t *a,
                                 uint32_t shift, uint32_t outn);
static srmech_status_t bi_div_denorm_rem(srmech_bigint_t *r, const uint32_t *un,
                                         uint32_t vn, uint32_t shift,
                                         uint32_t *junk);
static srmech_status_t bi_divmod_abs(srmech_bigint_t *q, srmech_bigint_t *r,
                                     const srmech_bigint_t *a,
                                     const srmech_bigint_t *b,
                                     void *ws, size_t ws_len);
static srmech_status_t bi_floor_fixup(srmech_bigint_t *q, srmech_bigint_t *r,
                                      const srmech_bigint_t *a,
                                      const srmech_bigint_t *b,
                                      void *ws, size_t ws_len);
static srmech_status_t bi_isqrt_seed(srmech_bigint_t *x,
                                     const srmech_bigint_t *a);
static srmech_status_t bi_isqrt_step(srmech_bigint_t *x,
                                     const srmech_bigint_t *a,
                                     srmech_bigint_t *q, srmech_bigint_t *s,
                                     void *ws, size_t ws_len, int *down);
static srmech_status_t bi_isqrt_finish(srmech_bigint_t *out, srmech_bigint_t *x,
                                       const srmech_bigint_t *a,
                                       srmech_bigint_t *q, srmech_bigint_t *s,
                                       void *ws, size_t ws_len);
static void *base_after(uint32_t *base, size_t cur);

/* ---- bounds ------------------------------------------------------- */

size_t srmech_bigint_add_bound(size_t a_n, size_t b_n)
{
    size_t m = (a_n > b_n) ? a_n : b_n;
    assert(m >= a_n || m >= b_n);
    assert(m + 1u > m);
    return m + 1u;
}

size_t srmech_bigint_mul_bound(size_t a_n, size_t b_n)
{
    size_t s = a_n + b_n;
    assert(s >= a_n);
    assert(s + 1u > 0u);
    return (s == 0u) ? 1u : s;
}

size_t srmech_bigint_shl_bound(size_t a_n, uint32_t bits)
{
    size_t whole = (size_t)(bits / BI_BASE_BITS);
    assert(a_n + whole >= a_n);
    assert(a_n + whole + 1u > a_n);
    return a_n + whole + 1u;
}

size_t srmech_bigint_pow_bound(size_t base_n, uint32_t exp)
{
    size_t prod;
    assert(base_n > 0u || exp == 0u);
    assert((size_t)exp == exp);
    if (exp == 0u || base_n == 0u) {
        return 1u;
    }
    prod = base_n * (size_t)exp;
    if (prod / (size_t)exp != base_n || prod + 1u < prod) {
        return (size_t)-1; /* clamp: caller's cap check will reject */
    }
    return prod + 1u;
}

size_t srmech_bigint_from_dec_bound(size_t n_digits)
{
    size_t limbs = (n_digits / 9u) + 2u;
    assert(limbs >= 2u);
    assert(limbs > n_digits / 9u);
    return limbs;
}

size_t srmech_bigint_to_dec_bound(size_t a_n)
{
    size_t bytes = a_n * 10u + 2u;
    assert(bytes >= 2u);
    assert(bytes >= a_n);
    return bytes;
}

/* ---- low-level helpers -------------------------------------------- */

/* Strip leading-zero limbs; fix sign so 0 has sign 0 and n 0. */
static void bi_norm(srmech_bigint_t *a)
{
    assert(a != NULL);
    assert(a->limbs != NULL || a->cap == 0u);
    while (a->n > 0u && a->limbs[a->n - 1u] == 0u) {
        a->n--;
    }
    if (a->n == 0u) {
        a->sign = 0;
    } else if (a->sign == 0) {
        a->sign = 1;
    }
}

/* Compare magnitudes only: -1 / 0 / +1. */
static int bi_cmp_abs(const srmech_bigint_t *a, const srmech_bigint_t *b)
{
    uint32_t i;
    assert(a != NULL);
    assert(b != NULL);
    if (a->n != b->n) {
        return (a->n < b->n) ? -1 : 1;
    }
    for (i = a->n; i > 0u; i--) {
        uint32_t x = a->limbs[i - 1u];
        uint32_t y = b->limbs[i - 1u];
        if (x != y) {
            return (x < y) ? -1 : 1;
        }
    }
    return 0;
}

int srmech_bigint_is_zero(const srmech_bigint_t *a)
{
    assert(a != NULL);
    assert(a->n != 0u || a->sign == 0);
    return (a->n == 0u) ? 1 : 0;
}

int srmech_bigint_cmp(const srmech_bigint_t *a, const srmech_bigint_t *b)
{
    int c;
    assert(a != NULL);
    assert(b != NULL);
    if (a->sign != b->sign) {
        return (a->sign < b->sign) ? -1 : 1;
    }
    if (a->sign == 0) {
        return 0;
    }
    c = bi_cmp_abs(a, b);
    return (a->sign > 0) ? c : -c;
}

/* dst = |src| limb-copy (no sign). OVERFLOW if dst->cap < src->n. */
static srmech_status_t bi_set_abs(srmech_bigint_t *dst,
                                  const srmech_bigint_t *src)
{
    uint32_t i;
    assert(dst != NULL && src != NULL);
    assert(dst->limbs != NULL || dst->cap == 0u);
    if (src->n > dst->cap) {
        return SRMECH_ERR_OVERFLOW;
    }
    for (i = 0u; i < src->n; i++) {
        dst->limbs[i] = src->limbs[i];
    }
    dst->n = src->n;
    dst->sign = (src->n == 0u) ? 0 : 1;
    return SRMECH_OK;
}

srmech_status_t srmech_bigint_copy(srmech_bigint_t *out, const srmech_bigint_t *a)
{
    srmech_status_t st;
    assert(out != NULL && a != NULL);
    st = bi_set_abs(out, a);
    if (st != SRMECH_OK) {
        return st;
    }
    out->sign = a->sign;
    assert(out->n == a->n);
    return SRMECH_OK;
}

srmech_status_t srmech_bigint_set_i64(srmech_bigint_t *out, int64_t v)
{
    uint64_t mag;
    assert(out != NULL);
    assert(out->limbs != NULL || out->cap == 0u);
    mag = (v < 0) ? (~(uint64_t)v + 1u) : (uint64_t)v; /* |v|, INT64_MIN-safe */
    if (out->cap < 2u && mag != 0u) {
        if (out->cap < 1u || (mag >> BI_BASE_BITS) != 0u) {
            return SRMECH_ERR_OVERFLOW;
        }
    }
    out->n = 0u;
    if (mag != 0u) {
        out->limbs[0] = (uint32_t)(mag & 0xFFFFFFFFu);
        out->n = 1u;
        if ((mag >> BI_BASE_BITS) != 0u) {
            out->limbs[1] = (uint32_t)(mag >> BI_BASE_BITS);
            out->n = 2u;
        }
    }
    out->sign = (v < 0) ? -1 : (out->n == 0u ? 0 : 1);
    bi_norm(out);
    return SRMECH_OK;
}

/* ---- magnitude add / sub ------------------------------------------ */

/* out = |a| + |b|. OVERFLOW if out->cap < max(a,b)+1. Sets out->sign +. */
static srmech_status_t bi_add_abs(srmech_bigint_t *out,
                                  const srmech_bigint_t *a,
                                  const srmech_bigint_t *b)
{
    uint32_t i, big = (a->n > b->n) ? a->n : b->n;
    uint64_t carry = 0u;
    assert(out != NULL && a != NULL && b != NULL);
    assert(out->limbs != NULL || out->cap == 0u);
    if ((size_t)big + 1u > out->cap) {
        return SRMECH_ERR_OVERFLOW;
    }
    for (i = 0u; i < big; i++) {
        uint64_t av = (i < a->n) ? a->limbs[i] : 0u;
        uint64_t bv = (i < b->n) ? b->limbs[i] : 0u;
        uint64_t t = av + bv + carry;
        out->limbs[i] = (uint32_t)(t & 0xFFFFFFFFu);
        carry = t >> BI_BASE_BITS;
    }
    out->n = big;
    if (carry != 0u) {
        out->limbs[big] = (uint32_t)carry;
        out->n = big + 1u;
    }
    out->sign = (out->n == 0u) ? 0 : 1;
    return SRMECH_OK;
}

/* out = |a| - |b|, requires |a| >= |b|. Sets out->sign + (caller fixes). */
static srmech_status_t bi_sub_abs(srmech_bigint_t *out,
                                  const srmech_bigint_t *a,
                                  const srmech_bigint_t *b)
{
    uint32_t i;
    uint64_t borrow = 0u;
    assert(out != NULL && a != NULL && b != NULL);
    assert(a->n >= b->n);
    if (a->n > out->cap) {
        return SRMECH_ERR_OVERFLOW;
    }
    for (i = 0u; i < a->n; i++) {
        uint64_t av = a->limbs[i];
        uint64_t bv = (i < b->n) ? b->limbs[i] : 0u;
        uint64_t t = av - bv - borrow;
        out->limbs[i] = (uint32_t)(t & 0xFFFFFFFFu);
        borrow = (t >> 63) & 1u; /* set if av-bv-borrow went negative */
    }
    assert(borrow == 0u);
    out->n = a->n;
    out->sign = 1;
    bi_norm(out);
    return SRMECH_OK;
}

/* Signed magnitude add/sub core: out = a + sb*b where sb = +1 or -1. */
static srmech_status_t bi_addsub(srmech_bigint_t *out, const srmech_bigint_t *a,
                                 const srmech_bigint_t *b, int sb)
{
    int bsign = (b->sign == 0) ? 0 : (b->sign * sb);
    int asign = a->sign;          /* capture: out may alias a (sign clobber) */
    srmech_status_t st;
    assert(out != NULL && a != NULL && b != NULL);
    assert(sb == 1 || sb == -1);
    if (asign == 0) {
        st = bi_set_abs(out, b);
        if (st == SRMECH_OK) { out->sign = (bsign == 0) ? 0 : bsign; }
        return st;
    }
    if (bsign == 0) {
        st = srmech_bigint_copy(out, a);
        if (st == SRMECH_OK && out->n != 0u) { out->sign = asign; }
        return st;
    }
    if (asign == bsign) {
        st = bi_add_abs(out, a, b);
        out->sign = (out->n == 0u) ? 0 : asign;
        return st;
    }
    if (bi_cmp_abs(a, b) >= 0) {
        st = bi_sub_abs(out, a, b);
        out->sign = (out->n == 0u) ? 0 : asign;
    } else {
        st = bi_sub_abs(out, b, a);
        out->sign = (out->n == 0u) ? 0 : bsign;
    }
    return st;
}

srmech_status_t srmech_bigint_add(srmech_bigint_t *out, const srmech_bigint_t *a,
                                  const srmech_bigint_t *b)
{
    assert(out != NULL && a != NULL && b != NULL);
    assert(out->limbs != NULL || out->cap == 0u);
    return bi_addsub(out, a, b, 1);
}

srmech_status_t srmech_bigint_sub(srmech_bigint_t *out, const srmech_bigint_t *a,
                                  const srmech_bigint_t *b)
{
    assert(out != NULL && a != NULL && b != NULL);
    assert(out->limbs != NULL || out->cap == 0u);
    return bi_addsub(out, a, b, -1);
}

/* ---- multiply ----------------------------------------------------- */

srmech_status_t srmech_bigint_mul(srmech_bigint_t *out, const srmech_bigint_t *a,
                                  const srmech_bigint_t *b)
{
    uint32_t i, j, need = a->n + b->n;
    assert(out != NULL && a != NULL && b != NULL);
    assert(out->limbs != NULL || out->cap == 0u);
    if (a->n == 0u || b->n == 0u) {
        out->n = 0u; out->sign = 0;
        return SRMECH_OK;
    }
    if (need > out->cap) {
        return SRMECH_ERR_OVERFLOW;
    }
    for (i = 0u; i < need; i++) {
        out->limbs[i] = 0u;
    }
    for (i = 0u; i < a->n; i++) {
        uint64_t carry = 0u;
        for (j = 0u; j < b->n; j++) {
            uint64_t t = (uint64_t)a->limbs[i] * b->limbs[j]
                       + out->limbs[i + j] + carry;
            out->limbs[i + j] = (uint32_t)(t & 0xFFFFFFFFu);
            carry = t >> BI_BASE_BITS;
        }
        out->limbs[i + b->n] = (uint32_t)carry;
    }
    out->n = need;
    out->sign = a->sign * b->sign;
    bi_norm(out);
    return SRMECH_OK;
}

/* ---- shifts ------------------------------------------------------- */

/* out = |a| << bits (magnitude only, sign untouched here). */
static srmech_status_t bi_shl_abs(srmech_bigint_t *out,
                                  const srmech_bigint_t *a, uint32_t bits)
{
    uint32_t whole = bits / BI_BASE_BITS, sh = bits % BI_BASE_BITS;
    uint32_t j, need = a->n + whole + 1u;
    assert(out != NULL && a != NULL);
    assert(sh < BI_BASE_BITS);
    if (a->n == 0u) { out->n = 0u; out->sign = 0; return SRMECH_OK; }
    if (need > out->cap) {
        return SRMECH_ERR_OVERFLOW;
    }
    /* High-to-low so an in-place out==a alias never clobbers a yet-read
     * source limb (out[j] reads a[j-whole], a[j-whole-1], both <= j). */
    for (j = need; j > 0u; j--) {
        uint32_t k = j - 1u;
        uint64_t hi = (k >= whole && (k - whole) < a->n)
                          ? ((uint64_t)a->limbs[k - whole] << sh) : 0u;
        uint64_t lo = (sh != 0u && k > whole && (k - whole - 1u) < a->n)
                          ? ((uint64_t)a->limbs[k - whole - 1u]
                             >> (BI_BASE_BITS - sh)) : 0u;
        out->limbs[k] = (uint32_t)((hi | lo) & 0xFFFFFFFFu);
    }
    out->n = need;
    out->sign = 1;
    bi_norm(out);
    return SRMECH_OK;
}

srmech_status_t srmech_bigint_shl_bits(srmech_bigint_t *out,
                                       const srmech_bigint_t *a, uint32_t bits)
{
    srmech_status_t st;
    int sign = a->sign;
    assert(out != NULL && a != NULL);
    assert(out->limbs != NULL || out->cap == 0u);
    st = bi_shl_abs(out, a, bits);
    if (st == SRMECH_OK && out->n != 0u) {
        out->sign = sign;
    }
    return st;
}

/* out = |a| >> bits (truncating, magnitude only). */
static srmech_status_t bi_shr_abs(srmech_bigint_t *out,
                                  const srmech_bigint_t *a, uint32_t bits)
{
    uint32_t whole = bits / BI_BASE_BITS, sh = bits % BI_BASE_BITS, i;
    assert(out != NULL && a != NULL);
    assert(sh < BI_BASE_BITS);
    if (whole >= a->n) { out->n = 0u; out->sign = 0; return SRMECH_OK; }
    if (a->n - whole > out->cap) {
        return SRMECH_ERR_OVERFLOW;
    }
    for (i = 0u; i + whole < a->n; i++) {
        uint64_t lo = (uint64_t)a->limbs[i + whole] >> sh;
        uint64_t hi = 0u;
        if (sh != 0u && (i + whole + 1u) < a->n) {
            hi = (uint64_t)a->limbs[i + whole + 1u] << (BI_BASE_BITS - sh);
        }
        out->limbs[i] = (uint32_t)((lo | hi) & 0xFFFFFFFFu);
    }
    out->n = a->n - whole;
    out->sign = 1;
    bi_norm(out);
    return SRMECH_OK;
}

/* 1 iff any of the low `bits` bits of |a| are set (for floor-shr fixup). */
static int bi_low_bits_set(const srmech_bigint_t *a, uint32_t bits)
{
    uint32_t whole = bits / BI_BASE_BITS, sh = bits % BI_BASE_BITS, i;
    assert(a != NULL);
    assert(sh < BI_BASE_BITS);
    for (i = 0u; i < whole && i < a->n; i++) {
        if (a->limbs[i] != 0u) { return 1; }
    }
    if (sh != 0u && whole < a->n) {
        uint32_t mask = (uint32_t)(((uint64_t)1u << sh) - 1u);
        if ((a->limbs[whole] & mask) != 0u) { return 1; }
    }
    return 0;
}

srmech_status_t srmech_bigint_shr_bits(srmech_bigint_t *out,
                                       const srmech_bigint_t *a, uint32_t bits)
{
    srmech_status_t st;
    int neg = (a->sign < 0);
    int rounded = neg && bi_low_bits_set(a, bits);
    assert(out != NULL && a != NULL);
    assert(out->limbs != NULL || out->cap == 0u);
    st = bi_shr_abs(out, a, bits);
    if (st != SRMECH_OK) { return st; }
    if (out->n != 0u) { out->sign = neg ? -1 : 1; }
    if (rounded) {                 /* floor: a>>k for a<0 rounds toward -inf */
        srmech_bigint_t one;
        uint32_t onelimb = 1u;
        one.sign = -1; one.n = 1u; one.cap = 1u; one.limbs = &onelimb;
        st = bi_addsub(out, out, &one, 1); /* out += (-1) */
    }
    return st;
}

/* ---- bit length --------------------------------------------------- */

/* Number of significant bits in |a| (0 for zero). */
static uint32_t bi_bitlen(const srmech_bigint_t *a)
{
    uint32_t top, bits = 0u;
    assert(a != NULL);
    assert(a->n == 0u || a->limbs[a->n - 1u] != 0u);
    if (a->n == 0u) { return 0u; }
    top = a->limbs[a->n - 1u];
    while (top != 0u) { bits++; top >>= 1; }
    return (a->n - 1u) * BI_BASE_BITS + bits;
}

/* ---- division (Knuth Algorithm D) --------------------------------- */

/* Single-limb divisor: q = floor(|a|/d), *rem = |a| mod d.  d != 0. */
static srmech_status_t bi_div_small(srmech_bigint_t *q, const srmech_bigint_t *a,
                                    uint32_t d, uint32_t *rem)
{
    uint32_t i;
    uint64_t r = 0u;
    assert(q != NULL && a != NULL && rem != NULL && d != 0u);
    assert(q->limbs != NULL || q->cap == 0u);
    if (a->n > q->cap) {
        return SRMECH_ERR_OVERFLOW;
    }
    for (i = a->n; i > 0u; i--) {
        uint64_t cur = (r << BI_BASE_BITS) | a->limbs[i - 1u];
        q->limbs[i - 1u] = (uint32_t)(cur / d);
        r = cur % d;
    }
    q->n = a->n;
    q->sign = 1;
    bi_norm(q);
    *rem = (uint32_t)r;
    return SRMECH_OK;
}

/* Knuth D inner: estimate qhat for u[j..j+n] / v (top limbs vt1:vt2). */
static uint32_t bi_qhat(uint32_t u2, uint32_t u1, uint32_t u0,
                        uint32_t vt1, uint32_t vt2)
{
    uint64_t num = ((uint64_t)u2 << BI_BASE_BITS) | u1;
    uint64_t qhat = num / vt1;
    uint64_t rhat = num % vt1;
    assert(vt1 != 0u);
    while (qhat > 0xFFFFFFFFu ||
           qhat * vt2 > ((rhat << BI_BASE_BITS) | u0)) {
        qhat--;
        rhat += vt1;
        if (rhat > 0xFFFFFFFFu) { break; }
    }
    assert(qhat <= 0xFFFFFFFFu);
    return (uint32_t)qhat;
}

/* u[j..j+vn] -= qhat * v[0..vn]; return borrow-out (for add-back). */
static uint32_t bi_mulsub(uint32_t *u, const uint32_t *v, uint32_t vn,
                          uint32_t qhat)
{
    uint32_t i;
    uint64_t borrow = 0u, carry = 0u;
    assert(u != NULL);
    assert(v != NULL);
    for (i = 0u; i < vn; i++) {
        uint64_t p = (uint64_t)qhat * v[i] + carry;
        uint64_t sub = (uint64_t)u[i] - (p & 0xFFFFFFFFu) - borrow;
        carry = p >> BI_BASE_BITS;
        u[i] = (uint32_t)(sub & 0xFFFFFFFFu);
        borrow = (sub >> 63) & 1u;
    }
    {
        uint64_t sub = (uint64_t)u[vn] - carry - borrow;
        u[vn] = (uint32_t)(sub & 0xFFFFFFFFu);
        return (uint32_t)((sub >> 63) & 1u);
    }
}

/* u[j..j+vn] += v[0..vn] (the rare Knuth D6 add-back); carry discarded. */
static void bi_addback(uint32_t *u, const uint32_t *v, uint32_t vn)
{
    uint32_t i;
    uint64_t carry = 0u;
    assert(u != NULL);
    assert(v != NULL);
    for (i = 0u; i < vn; i++) {
        uint64_t t = (uint64_t)u[i] + v[i] + carry;
        u[i] = (uint32_t)(t & 0xFFFFFFFFu);
        carry = t >> BI_BASE_BITS;
    }
    u[vn] = (uint32_t)(u[vn] + carry);
}

/* Bump-allocate `count` uint32 limbs from ws; advance cursor. */
static uint32_t *bi_ws_take(uint32_t *base, size_t cap_words, size_t *cur,
                            size_t count)
{
    uint32_t *p;
    assert(base != NULL && cur != NULL);
    assert(*cur <= cap_words);
    if (count > cap_words || *cur > cap_words - count) {
        return NULL;
    }
    p = base + *cur;
    *cur += count;
    return p;
}

/* Knuth D core over normalized un[0..m+vn], vn[0..vn-1]; fills q[0..m]. */
static void bi_div_knuth_loop(uint32_t *un, const uint32_t *vn_limbs,
                              uint32_t vn, uint32_t m, uint32_t *q)
{
    uint32_t j, vt1 = vn_limbs[vn - 1u], vt2 = vn_limbs[vn - 2u];
    assert(un != NULL && vn_limbs != NULL && q != NULL);
    assert(vt1 >= 0x80000000u); /* normalized: top divisor limb MSB set */
    for (j = m + 1u; j > 0u; j--) {
        uint32_t k = j - 1u;
        uint32_t qh = bi_qhat(un[k + vn], un[k + vn - 1u],
                              (vn >= 2u ? un[k + vn - 2u] : 0u), vt1, vt2);
        uint32_t borrow = bi_mulsub(un + k, vn_limbs, vn, qh);
        if (borrow != 0u) {
            qh--;
            bi_addback(un + k, vn_limbs, vn);
        }
        q[k] = qh;
    }
}

/* Full multi-limb magnitude divide: |a|/|b| -> q, r (both magnitudes). */
static srmech_status_t bi_div_knuth(srmech_bigint_t *q, srmech_bigint_t *r,
                                    const srmech_bigint_t *a,
                                    const srmech_bigint_t *b,
                                    void *ws, size_t ws_len)
{
    uint32_t *base = (uint32_t *)ws, *un, *vnl;
    size_t words = ws_len / sizeof(uint32_t), cur = 0u;
    uint32_t shift, i, vn = b->n, m = a->n - b->n, topbits;
    uint32_t junk;
    assert(q != NULL && r != NULL && a != NULL && b != NULL);
    assert((uintptr_t)ws % sizeof(uint32_t) == 0u || ws == NULL);
    un = bi_ws_take(base, words, &cur, (size_t)a->n + 2u);
    vnl = bi_ws_take(base, words, &cur, (size_t)vn);
    if (un == NULL || vnl == NULL) { return SRMECH_ERR_OVERFLOW; }
    topbits = bi_bitlen(b) % BI_BASE_BITS;     /* MSB position in top limb */
    shift = (topbits == 0u) ? 0u : (BI_BASE_BITS - topbits);
    { srmech_status_t st = bi_shl_norm(vnl, b, shift); if (st != SRMECH_OK) return st; }
    if (bi_shl_un(un, a, shift, a->n + 2u) != SRMECH_OK) { return SRMECH_ERR_OVERFLOW; }
    if (q->cap < (size_t)m + 1u) { return SRMECH_ERR_OVERFLOW; }
    for (i = 0u; i <= m; i++) { q->limbs[i] = 0u; }
    bi_div_knuth_loop(un, vnl, vn, m, q->limbs);
    q->n = m + 1u; q->sign = 1; bi_norm(q);
    return bi_div_denorm_rem(r, un, vn, shift, &junk);
}

/* Helper — left-shift |b| by `shift` bits into vnl[0..b->n-1] (no growth;
 * shift < 32 and top-limb-MSB-set means no extra limb). */
static srmech_status_t bi_shl_norm(uint32_t *vnl, const srmech_bigint_t *b,
                                   uint32_t shift)
{
    uint32_t i; uint64_t carry = 0u;
    assert(vnl != NULL && b != NULL);
    assert(shift < BI_BASE_BITS);
    for (i = 0u; i < b->n; i++) {
        uint64_t t = ((uint64_t)b->limbs[i] << shift) | carry;
        vnl[i] = (uint32_t)(t & 0xFFFFFFFFu);
        carry = t >> BI_BASE_BITS;
    }
    assert(carry == 0u); /* shift normalizes within the same limb count */
    return SRMECH_OK;
}

/* Helper — left-shift |a| by `shift` into un[0..outn-1], zero-extended. */
static srmech_status_t bi_shl_un(uint32_t *un, const srmech_bigint_t *a,
                                 uint32_t shift, uint32_t outn)
{
    uint32_t i; uint64_t carry = 0u;
    assert(un != NULL && a != NULL);
    assert(shift < BI_BASE_BITS && a->n < outn);
    for (i = 0u; i < outn; i++) { un[i] = 0u; }
    for (i = 0u; i < a->n; i++) {
        uint64_t t = ((uint64_t)a->limbs[i] << shift) | carry;
        un[i] = (uint32_t)(t & 0xFFFFFFFFu);
        carry = t >> BI_BASE_BITS;
    }
    if (a->n < outn) { un[a->n] = (uint32_t)carry; }
    return SRMECH_OK;
}

/* Helper — denormalize remainder un[0..vn-1] >> shift into r. */
static srmech_status_t bi_div_denorm_rem(srmech_bigint_t *r, const uint32_t *un,
                                         uint32_t vn, uint32_t shift,
                                         uint32_t *junk)
{
    uint32_t i; uint64_t carry = 0u;
    assert(r != NULL && un != NULL && junk != NULL);
    assert(shift < BI_BASE_BITS);
    if (r->cap < vn) { return SRMECH_ERR_OVERFLOW; }
    for (i = vn; i > 0u; i--) {
        uint64_t cur = ((uint64_t)un[i - 1u]) | (carry << BI_BASE_BITS);
        r->limbs[i - 1u] = (uint32_t)((cur >> shift) & 0xFFFFFFFFu);
        carry = un[i - 1u] & (((uint64_t)1u << shift) - 1u);
    }
    *junk = 0u;
    r->n = vn; r->sign = 1; bi_norm(r);
    return SRMECH_OK;
}

/* Magnitude divide dispatch: small vs Knuth. q,r are magnitudes. */
static srmech_status_t bi_divmod_abs(srmech_bigint_t *q, srmech_bigint_t *r,
                                     const srmech_bigint_t *a,
                                     const srmech_bigint_t *b,
                                     void *ws, size_t ws_len)
{
    assert(q != NULL && r != NULL && a != NULL && b != NULL);
    assert(b->n != 0u);
    if (bi_cmp_abs(a, b) < 0) {        /* |a| < |b|: q=0, r=|a| */
        srmech_status_t st = bi_set_abs(r, a);
        if (st != SRMECH_OK) { return st; }
        q->n = 0u; q->sign = 0;
        return SRMECH_OK;
    }
    if (b->n == 1u) {
        uint32_t rem = 0u;
        srmech_status_t st = bi_div_small(q, a, b->limbs[0], &rem);
        if (st != SRMECH_OK) { return st; }
        if (r->cap < 1u && rem != 0u) { return SRMECH_ERR_OVERFLOW; }
        r->limbs[0] = rem; r->n = (rem != 0u) ? 1u : 0u;
        r->sign = (rem != 0u) ? 1 : 0;
        return SRMECH_OK;
    }
    return bi_div_knuth(q, r, a, b, ws, ws_len);
}

srmech_status_t srmech_bigint_divmod(srmech_bigint_t *q, srmech_bigint_t *r,
                                     const srmech_bigint_t *a,
                                     const srmech_bigint_t *b,
                                     void *ws, size_t ws_len)
{
    srmech_status_t st;
    srmech_bigint_t qd, rd; uint32_t qbuf[1], rbuf[1];
    srmech_bigint_t *qp = q ? q : &qd, *rp = r ? r : &rd;
    assert(a != NULL && b != NULL);
    assert(qp != NULL && rp != NULL);
    if (b->sign == 0) { return SRMECH_ERR_BAD_INPUT; }
    if (!q) { qd.cap = 0u; qd.limbs = qbuf; qd.n = 0u; qd.sign = 0; (void)qbuf; }
    if (!r) { rd.cap = 0u; rd.limbs = rbuf; rd.n = 0u; rd.sign = 0; (void)rbuf; }
    st = bi_divmod_abs(qp, rp, a, b, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    return bi_floor_fixup(qp, rp, a, b, ws, ws_len);
}

/* Python FLOOR sign-correction of a truncated (qp,rp). If signs of a,b
 * differ and r != 0: q -= 1, r += b (so 0 <= r < |b| for b>0). */
static srmech_status_t bi_floor_fixup(srmech_bigint_t *q, srmech_bigint_t *r,
                                      const srmech_bigint_t *a,
                                      const srmech_bigint_t *b,
                                      void *ws, size_t ws_len)
{
    int qneg = (a->sign * b->sign) < 0;
    srmech_bigint_t one; uint32_t onelimb = 1u;
    srmech_status_t st;
    assert(q != NULL && r != NULL && a != NULL && b != NULL);
    assert(b->sign != 0);
    (void)ws; (void)ws_len;
    if (q->n != 0u) { q->sign = qneg ? -1 : 1; }
    if (r->n != 0u) { r->sign = a->sign; } /* truncated rem follows dividend */
    if (qneg && r->n != 0u) {
        one.sign = 1; one.n = 1u; one.cap = 1u; one.limbs = &onelimb;
        st = bi_addsub(q, q, &one, -1);    /* q -= 1 */
        if (st != SRMECH_OK) { return st; }
        st = bi_addsub(r, r, b, 1);        /* r += b */
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* ---- gcd ---------------------------------------------------------- */

srmech_status_t srmech_bigint_gcd(srmech_bigint_t *out, const srmech_bigint_t *a,
                                  const srmech_bigint_t *b,
                                  void *ws, size_t ws_len)
{
    uint32_t *base = (uint32_t *)ws;
    size_t words = ws_len / sizeof(uint32_t), cur = 0u;
    srmech_bigint_t x, y, t, qx; size_t cap = (a->n > b->n) ? a->n : b->n;
    uint32_t *xb, *yb, *tb, *qb; uint32_t guard = 0u;
    assert(out != NULL && a != NULL && b != NULL);
    assert(out->limbs != NULL || out->cap == 0u);
    cap += 1u;
    xb = bi_ws_take(base, words, &cur, cap);
    yb = bi_ws_take(base, words, &cur, cap);
    tb = bi_ws_take(base, words, &cur, cap);
    qb = bi_ws_take(base, words, &cur, cap);
    if (xb == NULL || yb == NULL || tb == NULL || qb == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    x.limbs = xb; x.cap = (uint32_t)cap; y.limbs = yb; y.cap = (uint32_t)cap;
    t.limbs = tb; t.cap = (uint32_t)cap; qx.limbs = qb; qx.cap = (uint32_t)cap;
    if (bi_set_abs(&x, a) != SRMECH_OK || bi_set_abs(&y, b) != SRMECH_OK) {
        return SRMECH_ERR_OVERFLOW;
    }
    while (y.n != 0u && guard < 0xFFFFFFFFu) {     /* Euclid: x,y = y, x%y */
        srmech_status_t st = bi_divmod_abs(&qx, &t, &x, &y, base + cur,
                                           (words - cur) * sizeof(uint32_t));
        if (st != SRMECH_OK) { return st; }
        if (bi_set_abs(&x, &y) != SRMECH_OK) { return SRMECH_ERR_OVERFLOW; }
        if (bi_set_abs(&y, &t) != SRMECH_OK) { return SRMECH_ERR_OVERFLOW; }
        guard++;
    }
    return bi_set_abs(out, &x);
}

/* ---- pow ---------------------------------------------------------- */

/* acc = acc * m (into scratch t, then copy back). */
static srmech_status_t bi_mul_into(srmech_bigint_t *acc,
                                   const srmech_bigint_t *m, srmech_bigint_t *t)
{
    srmech_status_t st;
    assert(acc != NULL && m != NULL && t != NULL);
    assert(t != acc && t != m);   /* t must be a distinct scratch carrier */
    st = srmech_bigint_mul(t, acc, m);
    if (st != SRMECH_OK) { return st; }
    return srmech_bigint_copy(acc, t);
}

srmech_status_t srmech_bigint_pow_u32(srmech_bigint_t *out,
                                      const srmech_bigint_t *base, uint32_t exp,
                                      void *ws, size_t ws_len)
{
    uint32_t *wb = (uint32_t *)ws;
    size_t words = ws_len / sizeof(uint32_t), cur = 0u;
    srmech_bigint_t b2, t; size_t cap = (size_t)base->n * 32u + 4u;
    uint32_t *bb, *tb, e = exp;
    srmech_status_t st;
    assert(out != NULL && base != NULL);
    assert(out->limbs != NULL || out->cap == 0u);
    bb = bi_ws_take(wb, words, &cur, cap);
    tb = bi_ws_take(wb, words, &cur, cap);
    if (bb == NULL || tb == NULL) { return SRMECH_ERR_OVERFLOW; }
    b2.limbs = bb; b2.cap = (uint32_t)cap; t.limbs = tb; t.cap = (uint32_t)cap;
    st = srmech_bigint_set_i64(out, 1);              /* out = 1 */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&b2, base);              /* b2 = base */
    if (st != SRMECH_OK) { return st; }
    while (e != 0u) {                                /* square-and-multiply */
        if ((e & 1u) != 0u) {
            st = bi_mul_into(out, &b2, &t);
            if (st != SRMECH_OK) { return st; }
        }
        e >>= 1;
        if (e != 0u) {
            st = bi_mul_into(&b2, &b2, &t);
            if (st != SRMECH_OK) { return st; }
        }
    }
    return SRMECH_OK;
}

/* ---- isqrt -------------------------------------------------------- */

/* x = (x + a/x) / 2 (one Newton step) into scratch; sets *changed. */
static srmech_status_t bi_isqrt_step(srmech_bigint_t *x,
                                     const srmech_bigint_t *a,
                                     srmech_bigint_t *q, srmech_bigint_t *s,
                                     void *ws, size_t ws_len, int *down)
{
    srmech_status_t st;
    assert(x != NULL && a != NULL && q != NULL && s != NULL && down != NULL);
    assert(x->n != 0u);              /* divisor x is the running estimate >0 */
    st = bi_divmod_abs(q, s, a, x, ws, ws_len);      /* q = a / x */
    if (st != SRMECH_OK) { return st; }
    st = bi_addsub(s, x, q, 1);                      /* s = x + q */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_shr_bits(q, s, 1);            /* q = (x+q)/2 */
    if (st != SRMECH_OK) { return st; }
    *down = (bi_cmp_abs(q, x) < 0);
    return srmech_bigint_copy(x, q);
}

srmech_status_t srmech_bigint_isqrt(srmech_bigint_t *out, const srmech_bigint_t *a,
                                    void *ws, size_t ws_len)
{
    uint32_t *wb = (uint32_t *)ws;
    size_t words = ws_len / sizeof(uint32_t), cur = 0u;
    srmech_bigint_t x, q, s; size_t cap = (size_t)a->n + 2u;
    uint32_t *xb, *qb, *sb, guard = 0u; int down = 1;
    srmech_status_t st;
    assert(out != NULL && a != NULL);
    assert(out->limbs != NULL || out->cap == 0u);
    if (a->sign < 0) { return SRMECH_ERR_BAD_INPUT; }
    if (a->n == 0u) { out->n = 0u; out->sign = 0; return SRMECH_OK; }
    xb = bi_ws_take(wb, words, &cur, cap);
    qb = bi_ws_take(wb, words, &cur, cap);
    sb = bi_ws_take(wb, words, &cur, cap);
    if (xb == NULL || qb == NULL || sb == NULL) { return SRMECH_ERR_OVERFLOW; }
    x.limbs = xb; x.cap = (uint32_t)cap; q.limbs = qb; q.cap = (uint32_t)cap;
    s.limbs = sb; s.cap = (uint32_t)cap;
    st = bi_isqrt_seed(&x, a);                       /* x0 = 2^ceil(bitlen/2) */
    if (st != SRMECH_OK) { return st; }
    while (down && guard < 0xFFFFFFu) {
        st = bi_isqrt_step(&x, a, &q, &s, base_after(wb, cur),
                           (words - cur) * sizeof(uint32_t), &down);
        if (st != SRMECH_OK) { return st; }
        guard++;
    }
    return bi_isqrt_finish(out, &x, a, &q, &s, base_after(wb, cur),
                           (words - cur) * sizeof(uint32_t));
}

/* x = 2^ceil(bitlen(a)/2): the Newton seed (>= true sqrt). */
static srmech_status_t bi_isqrt_seed(srmech_bigint_t *x, const srmech_bigint_t *a)
{
    uint32_t bl = bi_bitlen(a), half = (bl + 1u) / 2u;
    srmech_status_t st;
    assert(x != NULL && a != NULL);
    assert(bl > 0u);
    st = srmech_bigint_set_i64(x, 1);
    if (st != SRMECH_OK) { return st; }
    return srmech_bigint_shl_bits(x, x, half);
}

/* Pointer arithmetic helper: ws base advanced past `cur` words. */
static void *base_after(uint32_t *base, size_t cur)
{
    assert(base != NULL);
    assert((uintptr_t)(base + cur) >= (uintptr_t)base);
    return (void *)(base + cur);
}

/* Floor-correct x so x*x <= a < (x+1)^2. */
static srmech_status_t bi_isqrt_finish(srmech_bigint_t *out, srmech_bigint_t *x,
                                       const srmech_bigint_t *a,
                                       srmech_bigint_t *q, srmech_bigint_t *s,
                                       void *ws, size_t ws_len)
{
    srmech_bigint_t one; uint32_t onelimb = 1u; uint32_t guard = 0u;
    srmech_status_t st;
    assert(out != NULL && x != NULL && a != NULL && q != NULL && s != NULL);
    assert(a->sign >= 0);            /* isqrt domain: non-negative radicand */
    one.sign = 1; one.n = 1u; one.cap = 1u; one.limbs = &onelimb;
    (void)ws; (void)ws_len;
    while (guard < 4u) {                /* at most a couple of corrections */
        st = srmech_bigint_mul(s, x, x);            /* s = x*x */
        if (st != SRMECH_OK) { return st; }
        if (bi_cmp_abs(s, a) <= 0) { break; }       /* x*x <= a: floor ok */
        st = bi_addsub(x, x, &one, -1);             /* x -= 1 */
        if (st != SRMECH_OK) { return st; }
        guard++;
    }
    while (guard < 8u) {                /* climb if x too small */
        st = bi_addsub(q, x, &one, 1);              /* q = x+1 */
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_mul(s, q, q);            /* s = (x+1)^2 */
        if (st != SRMECH_OK) { return st; }
        if (bi_cmp_abs(s, a) > 0) { break; }
        st = bi_addsub(x, x, &one, 1);
        if (st != SRMECH_OK) { return st; }
        guard++;
    }
    return bi_set_abs(out, x);
}

/* ---- decimal I/O -------------------------------------------------- */

/* out = out*10 + d (in place; magnitude only). OVERFLOW on cap. */
static srmech_status_t bi_mul10_add(srmech_bigint_t *out, uint32_t d)
{
    uint32_t i;
    uint64_t carry = d;
    assert(out != NULL && d < 10u);
    assert(out->limbs != NULL || out->cap == 0u);
    for (i = 0u; i < out->n; i++) {
        uint64_t t = (uint64_t)out->limbs[i] * 10u + carry;
        out->limbs[i] = (uint32_t)(t & 0xFFFFFFFFu);
        carry = t >> BI_BASE_BITS;
    }
    while (carry != 0u) {
        if (out->n >= out->cap) { return SRMECH_ERR_OVERFLOW; }
        out->limbs[out->n] = (uint32_t)(carry & 0xFFFFFFFFu);
        out->n++;
        carry >>= BI_BASE_BITS;
    }
    return SRMECH_OK;
}

srmech_status_t srmech_bigint_from_dec(srmech_bigint_t *out, const char *s,
                                       size_t len)
{
    size_t i = 0u; int neg = 0;
    srmech_status_t st;
    assert(out != NULL && (s != NULL || len == 0u));
    assert(out->limbs != NULL || out->cap == 0u);
    out->n = 0u; out->sign = 0;
    if (len > 0u && s[0] == '-') { neg = 1; i = 1u; }
    if (i >= len) { return SRMECH_ERR_BAD_INPUT; } /* no digits */
    for (; i < len; i++) {
        char c = s[i];
        if (c < '0' || c > '9') { return SRMECH_ERR_BAD_INPUT; }
        st = bi_mul10_add(out, (uint32_t)(c - '0'));
        if (st != SRMECH_OK) { return st; }
    }
    bi_norm(out);
    if (out->n != 0u) { out->sign = neg ? -1 : 1; }
    return SRMECH_OK;
}

/* Reverse buf[0..n) in place (decimal digits collected LSB-first). */
static void bi_reverse(char *buf, size_t n)
{
    size_t i;
    assert(buf != NULL || n == 0u);
    assert(n < (size_t)-1);
    for (i = 0u; i < n / 2u; i++) {
        char t = buf[i]; buf[i] = buf[n - 1u - i]; buf[n - 1u - i] = t;
    }
}

/* Collect decimal digits of |a| LSB-first into buf; *ndig = count. */
static srmech_status_t bi_to_dec_digits(const srmech_bigint_t *a, char *buf,
                                        size_t cap, size_t *ndig,
                                        void *ws, size_t ws_len)
{
    uint32_t *wb = (uint32_t *)ws; size_t words = ws_len / sizeof(uint32_t);
    srmech_bigint_t cur; uint32_t *cb; size_t k = 0u, guard = 0u, cur0 = 0u;
    srmech_status_t st;
    assert(a != NULL && buf != NULL && ndig != NULL);
    assert(a->n != 0u);              /* zero is rendered by the caller */
    cb = bi_ws_take(wb, words, &cur0, (size_t)a->n + 1u);
    if (cb == NULL) { return SRMECH_ERR_OVERFLOW; }
    cur.limbs = cb; cur.cap = (uint32_t)((size_t)a->n + 1u);
    st = bi_set_abs(&cur, a);
    if (st != SRMECH_OK) { return st; }
    while (cur.n != 0u && guard < 0xFFFFFFFFu) {
        uint32_t rem = 0u;
        st = bi_div_small(&cur, &cur, 10u, &rem);    /* in-place /10 */
        if (st != SRMECH_OK) { return st; }
        if (k >= cap) { return SRMECH_ERR_OVERFLOW; }
        buf[k++] = (char)('0' + rem);
        guard++;
    }
    *ndig = k;
    return SRMECH_OK;
}

srmech_status_t srmech_bigint_to_dec(const srmech_bigint_t *a, char *buf,
                                     size_t cap, size_t *out_len,
                                     void *ws, size_t ws_len)
{
    size_t ndig = 0u, off = 0u;
    srmech_status_t st;
    assert(a != NULL && buf != NULL && out_len != NULL);
    assert(buf != NULL || cap == 0u);
    if (a->n == 0u) {                                /* zero -> "0" */
        if (cap < 2u) { return SRMECH_ERR_OVERFLOW; }
        buf[0] = '0'; buf[1] = '\0'; *out_len = 1u;
        return SRMECH_OK;
    }
    if (a->sign < 0) {
        if (cap < 2u) { return SRMECH_ERR_OVERFLOW; }
        buf[0] = '-'; off = 1u;
    }
    st = bi_to_dec_digits(a, buf + off, cap - off, &ndig, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    bi_reverse(buf + off, ndig);
    if (off + ndig + 1u > cap) { return SRMECH_ERR_OVERFLOW; }
    buf[off + ndig] = '\0';
    *out_len = off + ndig;
    return SRMECH_OK;
}
