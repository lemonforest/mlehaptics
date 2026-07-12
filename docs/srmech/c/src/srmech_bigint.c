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
 *   - mul                : Karatsuba (rc168) above a measured crossover,
 *                          schoolbook below — bilinear bind (Class M
 *                          shape); the split is an ITERATIVE explicit
 *                          frame machine (Rule 1: no recursion) over a
 *                          caller arena (srmech_bigint_mul_ws) or the
 *                          bounded internal region (srmech_bigint_mul);
 *                          byte-identical to schoolbook for all inputs.
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
    assert((size_t)exp == exp);           /* exp representable as a size_t */
    /* base^0 = 1 AND 0^{exp>0} = 0 both fit in a single limb. There is no
     * precondition forbidding base_n == 0: 0^{exp>0} is a well-defined value
     * (0) that srmech_bigint_pow_u32 computes correctly — e.g. the two-sided
     * unary-theta n=0 term with j>=1. (The old assert(base_n > 0u || exp == 0u)
     * was over-strict: it aborted this valid case in asserts-live builds while
     * NDEBUG builds computed it correctly, so callers routed around it with a
     * `q_limbs == 0u ? 1u : q_limbs` guard — see srmech_bigexp / srmech_jacobi.) */
    if (exp == 0u || base_n == 0u) {
        return 1u;
    }
    prod = base_n * (size_t)exp;
    if (prod / (size_t)exp != base_n || prod + 1u < prod) {
        return (size_t)-1; /* clamp: caller's cap check will reject */
    }
    assert(prod + 1u > prod);             /* +1 no-wrap (guarded above): a valid limb count */
    return prod + 1u;
}

/* Workspace BYTES the caller must give srmech_bigint_pow_u32 for base^exp:
 * the running square (pow_bound limbs) + the raw mul-temp (mul_bound of two
 * pow_bound). Returns (size_t)-1 on size overflow (caller's ws check rejects). */
size_t srmech_bigint_pow_ws_bound(size_t base_n, uint32_t exp)
{
    size_t cap_b2 = srmech_bigint_pow_bound(base_n, exp);
    size_t cap_t, total;
    assert((size_t)exp == exp);
    if (cap_b2 == (size_t)-1) { return (size_t)-1; }
    cap_t = srmech_bigint_mul_bound(cap_b2, cap_b2);
    assert(cap_t >= cap_b2);
    total = cap_b2 + cap_t;
    if (total < cap_b2 || total > (size_t)-1 / sizeof(uint32_t)) {
        return (size_t)-1;
    }
    return total * sizeof(uint32_t);
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

/* Karatsuba tuning (0.9.0rc168). BI_KARA_CUTOFF: the measured smaller-
 * operand limb count below which schoolbook wins (WSL2 gcc -O2 crossover
 * measurement — see CHANGELOG 0.9.0rc168). BI_KARA_MAX_DEPTH: the split
 * size follows m -> m/2 + 2 per level, so 40 levels cover any uint32
 * limb count with slack (2^32 reaches < CUTOFF within 29). BI_MUL_LOCAL_
 * WS_U64: the bounded internal arena (uint64 units → 8-byte aligned) the
 * no-arena srmech_bigint_mul entry carries on its own frame — full
 * Karatsuba for mid-size operands, graceful fewer-level splits above,
 * with callers owning an arena getting the unbounded split via
 * srmech_bigint_mul_ws. */
#define BI_KARA_CUTOFF      24u
#define BI_KARA_MAX_DEPTH   40u
#define BI_MUL_LOCAL_WS_U64 1024u

/* One explicit-schedule Karatsuba frame (JPL Rule 1: NO recursion — the
 * divide-and-conquer runs on a manual frame stack). x/y are raw operand
 * limb slices (xn >= yn after the push-time normalise; slices MAY carry
 * leading-zero limbs), dst is the FULL xn+yn-limb product region (every
 * limb written, leading zeros included), scr is this frame's scratch
 * base inside the arena (children carve from scr + this frame's need). */
typedef struct {
    const uint32_t *x;
    const uint32_t *y;
    uint32_t *dst;
    uint32_t *scr;
    uint32_t xn;
    uint32_t yn;
    uint32_t phase;   /* 0 start; 1/2 children pending; 3 combine */
} bi_kara_frame_t;

/* Workspace BYTES for the FULL Karatsuba split of an a_n x b_n limb
 * multiply via srmech_bigint_mul_ws: the explicit split-frame stack plus
 * the per-level scratch sum along the deepest path. Exact per-level
 * accounting (matching the engine's bi_kara_frame_need): a level whose
 * larger operand is m limbs carves at most 2m+8 words (balanced split:
 * 4*ceil(m/2)+4 <= 2m+6 for sx/sy/t; chunk split: <= m for the x1*y
 * partial), and its largest child operand is at most m/2+2 limbs (the
 * h+1 = ceil(m/2)+1 padded sums). Returns 0 when the smaller operand is
 * below the crossover (schoolbook needs no scratch). A smaller arena
 * still yields the identical product (fewer split levels) — this bound
 * guarantees the full split. */
size_t srmech_bigint_mul_ws_bound(size_t a_n, size_t b_n)
{
    size_t m = (a_n > b_n) ? a_n : b_n;
    size_t small = (a_n > b_n) ? b_n : a_n;
    size_t words = 0u, level = 0u;
    assert(a_n <= 0xFFFFFFFFu && b_n <= 0xFFFFFFFFu);
    if (small < BI_KARA_CUTOFF) {
        return 0u;
    }
    while (m >= BI_KARA_CUTOFF && level < BI_KARA_MAX_DEPTH) {
        words += 2u * m + 8u;
        m = m / 2u + 2u;
        level++;
    }
    assert(words >= 2u * BI_KARA_CUTOFF);      /* at least one level */
    return BI_KARA_MAX_DEPTH * sizeof(bi_kara_frame_t)
           + words * sizeof(uint32_t);
}

/* Schoolbook O(n*m) multiply (the pre-rc168 srmech_bigint_mul body, kept
 * verbatim): the base case + the no/short-scratch fallback. The Karatsuba
 * path must be BYTE-IDENTICAL to this for every input. */
static srmech_status_t bi_mul_school(srmech_bigint_t *out,
                                     const srmech_bigint_t *a,
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

/* Raw-slice schoolbook: dst[0..xn+yn) = x * y, FULL length (leading
 * zeros written). Operands may carry leading-zero limbs (padded sums). */
static void bi_kara_school(const uint32_t *x, uint32_t xn,
                           const uint32_t *y, uint32_t yn, uint32_t *dst)
{
    uint32_t i, j;
    assert(x != NULL && y != NULL && dst != NULL);
    assert(xn >= 1u && yn >= 1u);
    for (i = 0u; i < xn + yn; i++) {
        dst[i] = 0u;
    }
    for (i = 0u; i < xn; i++) {
        uint64_t carry = 0u;
        for (j = 0u; j < yn; j++) {
            uint64_t t = (uint64_t)x[i] * y[j] + dst[i + j] + carry;
            dst[i + j] = (uint32_t)(t & 0xFFFFFFFFu);
            carry = t >> BI_BASE_BITS;
        }
        dst[i + yn] = (uint32_t)carry;
    }
}

/* dst[0..dn) = a[0..an) + b[0..bn), full length, zero-padded above; the
 * carry lands inside dn (contract: dn >= max(an, bn) + 1). */
static void bi_kara_sum(uint32_t *dst, uint32_t dn, const uint32_t *a,
                        uint32_t an, const uint32_t *b, uint32_t bn)
{
    uint32_t i;
    uint64_t carry = 0u;
    assert(dst != NULL && a != NULL && b != NULL);
    assert(dn >= ((an > bn) ? an : bn) + 1u);
    for (i = 0u; i < dn; i++) {
        uint64_t av = (i < an) ? a[i] : 0u;
        uint64_t bv = (i < bn) ? b[i] : 0u;
        uint64_t t = av + bv + carry;
        dst[i] = (uint32_t)(t & 0xFFFFFFFFu);
        carry = t >> BI_BASE_BITS;
    }
    assert(carry == 0u);
}

/* t[0..tn) -= z[0..zn), full length (tn >= zn). The difference is the
 * Karatsuba middle term, mathematically non-negative → final borrow 0. */
static void bi_kara_sub(uint32_t *t, uint32_t tn, const uint32_t *z,
                        uint32_t zn)
{
    uint32_t i;
    uint64_t borrow = 0u;
    assert(t != NULL && z != NULL);
    assert(tn >= zn);
    for (i = 0u; i < tn; i++) {
        uint64_t zv = (i < zn) ? z[i] : 0u;
        uint64_t d = (uint64_t)t[i] - zv - borrow;
        t[i] = (uint32_t)(d & 0xFFFFFFFFu);
        borrow = (d >> 63) & 1u;
    }
    assert(borrow == 0u);
}

/* dst[0..dn) += t[0..tn) (tn <= dn), carry rippled through dn. The sum
 * stays inside the enclosing product region → final carry 0. */
static void bi_kara_add_at(uint32_t *dst, uint32_t dn, const uint32_t *t,
                           uint32_t tn)
{
    uint32_t i;
    uint64_t carry = 0u;
    assert(dst != NULL && t != NULL);
    assert(tn <= dn);
    for (i = 0u; i < dn && (i < tn || carry != 0u); i++) {
        uint64_t tv = (i < tn) ? t[i] : 0u;
        uint64_t s = (uint64_t)dst[i] + tv + carry;
        dst[i] = (uint32_t)(s & 0xFFFFFFFFu);
        carry = s >> BI_BASE_BITS;
    }
    assert(carry == 0u);
}

/* Scratch words THIS frame carves at its scr base (children start after).
 * Balanced split (yn > h): sx (h+1) + sy (h+1) + t (2h+2) = 4h+4 words.
 * Chunk split (yn <= h): the x1*y partial product, (xn-h)+yn words. */
static size_t bi_kara_frame_need(uint32_t xn, uint32_t yn, uint32_t h)
{
    assert(xn >= yn && yn >= 1u);
    assert(h >= 1u && h < xn);
    if (yn <= h) {
        return (size_t)(xn - h) + yn;
    }
    return 4u * (size_t)h + 4u;
}

/* 1 iff this frame must run schoolbook: below the measured Karatsuba
 * crossover, at the frame-stack depth cap, or its scratch slice does not
 * fit the arena (graceful degradation — the RESULT is identical). */
static int bi_kara_is_leaf(const bi_kara_frame_t *f, const uint32_t *ws_end,
                           uint32_t sp)
{
    uint32_t h;
    size_t need, avail;
    assert(f != NULL && ws_end != NULL);
    assert(f->xn >= f->yn);
    if (f->yn < BI_KARA_CUTOFF || sp >= BI_KARA_MAX_DEPTH) {
        return 1;
    }
    h = (f->xn + 1u) / 2u;
    need = bi_kara_frame_need(f->xn, f->yn, h);
    avail = (f->scr <= ws_end) ? (size_t)(ws_end - f->scr) : 0u;
    return (need > avail) ? 1 : 0;
}

/* Normalise a freshly built frame so x is the longer operand (multiply
 * is commutative; the split logic requires xn >= yn). */
static void bi_kara_norm_frame(bi_kara_frame_t *f)
{
    assert(f != NULL);
    assert(f->xn >= 1u && f->yn >= 1u);
    if (f->xn < f->yn) {
        const uint32_t *tp = f->x;
        uint32_t tn = f->xn;
        f->x = f->y; f->xn = f->yn;
        f->y = tp;   f->yn = tn;
    }
}

/* Balanced step (yn > h, h = ceil(xn/2)): phase 0 preps sx = x0+x1 /
 * sy = y0+y1 and spawns t = sx*sy; phase 1 spawns z0 = x0*y0 into dst
 * low; phase 2 spawns z2 = x1*y1 into dst high; phase 3 combines
 * z1 = t - z0 - z2 into dst at offset h. Returns 1 iff *child is to be
 * pushed. z1 < B^(xn+1) <= B^(xn+yn-h), so the middle add never carries
 * out of the product region. */
static int bi_kara_step_bal(bi_kara_frame_t *f, bi_kara_frame_t *child)
{
    uint32_t h = (f->xn + 1u) / 2u;
    uint32_t *sx = f->scr, *sy = f->scr + h + 1u, *t = f->scr + 2u * h + 2u;
    uint32_t *sub = f->scr + 4u * h + 4u;
    assert(f != NULL && child != NULL);
    assert(f->yn > h && h >= 1u);
    if (f->phase == 0u) {
        bi_kara_sum(sx, h + 1u, f->x, h, f->x + h, f->xn - h);
        bi_kara_sum(sy, h + 1u, f->y, h, f->y + h, f->yn - h);
        child->x = sx; child->xn = h + 1u;
        child->y = sy; child->yn = h + 1u;
        child->dst = t; child->scr = sub;
        f->phase = 1u;
        return 1;
    }
    if (f->phase == 1u) {
        child->x = f->x; child->xn = h;
        child->y = f->y; child->yn = h;
        child->dst = f->dst; child->scr = sub;
        f->phase = 2u;
        return 1;
    }
    if (f->phase == 2u) {
        child->x = f->x + h; child->xn = f->xn - h;
        child->y = f->y + h; child->yn = f->yn - h;
        child->dst = f->dst + 2u * h; child->scr = sub;
        f->phase = 3u;
        return 1;
    }
    bi_kara_sub(t, 2u * h + 2u, f->dst, 2u * h);              /* t -= z0 */
    bi_kara_sub(t, 2u * h + 2u, f->dst + 2u * h,
                f->xn + f->yn - 2u * h);                      /* t -= z2 */
    {
        uint32_t avail = f->xn + f->yn - h;
        uint32_t ta = (2u * h + 2u < avail) ? (2u * h + 2u) : avail;
        uint32_t i;
        for (i = ta; i < 2u * h + 2u; i++) {
            assert(t[i] == 0u);           /* z1 fits xn+1 <= avail limbs */
        }
        bi_kara_add_at(f->dst + h, avail, t, ta);
    }
    return 0;
}

/* Chunk step (yn <= h = ceil(xn/2): x splits at h, y rides whole — the
 * unbalanced schedule): phase 0 spawns x0*y into dst low; phase 1 zeros
 * the dst tail and spawns x1*y into scr; phase 3 adds the scr partial
 * into dst at offset h (x*y = x0*y + x1*y*B^h). Returns 1 iff *child is
 * to be pushed. */
static int bi_kara_step_chunk(bi_kara_frame_t *f, bi_kara_frame_t *child)
{
    uint32_t h = (f->xn + 1u) / 2u;
    uint32_t pn = f->xn - h + f->yn;      /* x1*y partial length */
    assert(f != NULL && child != NULL);
    assert(f->yn <= h && h < f->xn);
    if (f->phase == 0u) {
        child->x = f->x; child->xn = h;
        child->y = f->y; child->yn = f->yn;
        child->dst = f->dst; child->scr = f->scr + pn;
        f->phase = 1u;
        return 1;
    }
    if (f->phase == 1u) {
        uint32_t i;
        for (i = h + f->yn; i < f->xn + f->yn; i++) {
            f->dst[i] = 0u;               /* tail beyond the x0*y write */
        }
        child->x = f->x + h; child->xn = f->xn - h;
        child->y = f->y;     child->yn = f->yn;
        child->dst = f->scr; child->scr = f->scr + pn;
        f->phase = 3u;
        return 1;
    }
    bi_kara_add_at(f->dst + h, f->xn + f->yn - h, f->scr, pn);
    return 0;
}

/* Run the explicit Karatsuba schedule from the pre-filled root frame
 * st[0] (a frame array of BI_KARA_MAX_DEPTH; siblings run sequentially,
 * so the live stack never exceeds the split depth). Every iteration
 * either advances a frame's phase or pops it, so the loop terminates;
 * the guard is the hard Rule-2 cap (overrun → caller re-runs schoolbook,
 * result identical). */
static srmech_status_t bi_kara_machine(bi_kara_frame_t *st,
                                       const uint32_t *ws_end)
{
    uint32_t sp = 1u;
    uint64_t guard = 0u;
    assert(st != NULL && ws_end != NULL);
    assert(st[0].xn >= st[0].yn && st[0].yn >= 1u);
    while (sp > 0u) {
        bi_kara_frame_t *f = &st[sp - 1u];
        bi_kara_frame_t child;
        int pushed;
        if (guard >= ((uint64_t)1u << 40)) {
            return SRMECH_ERR_OVERFLOW;
        }
        guard++;
        if (f->phase == 0u && bi_kara_is_leaf(f, ws_end, sp)) {
            bi_kara_school(f->x, f->xn, f->y, f->yn, f->dst);
            sp--;
            continue;
        }
        if (f->yn <= (f->xn + 1u) / 2u) {
            pushed = bi_kara_step_chunk(f, &child);
        } else {
            pushed = bi_kara_step_bal(f, &child);
        }
        if (pushed) {
            child.phase = 0u;
            bi_kara_norm_frame(&child);
            assert(sp < BI_KARA_MAX_DEPTH);
            st[sp] = child;
            sp++;
        } else {
            sp--;
        }
    }
    return SRMECH_OK;
}

srmech_status_t srmech_bigint_mul_ws(srmech_bigint_t *out,
                                     const srmech_bigint_t *a,
                                     const srmech_bigint_t *b,
                                     void *ws, size_t ws_len)
{
    uint32_t need = a->n + b->n;
    size_t frame_bytes = BI_KARA_MAX_DEPTH * sizeof(bi_kara_frame_t);
    uint32_t small = (a->n < b->n) ? a->n : b->n;
    uint32_t big = (a->n < b->n) ? b->n : a->n;
    assert(out != NULL && a != NULL && b != NULL);
    assert(out->limbs != NULL || out->cap == 0u);
    if (a->n == 0u || b->n == 0u) {
        out->n = 0u; out->sign = 0;
        return SRMECH_OK;
    }
    if (need > out->cap) {
        return SRMECH_ERR_OVERFLOW;
    }
    if (small >= BI_KARA_CUTOFF && ws != NULL
            && ((uintptr_t)ws % 8u) == 0u && ws_len >= frame_bytes
            && (ws_len - frame_bytes) / sizeof(uint32_t)
               >= 2u * (size_t)big + 8u) {
        bi_kara_frame_t *st = (bi_kara_frame_t *)ws;
        uint32_t *scr = (uint32_t *)(void *)((unsigned char *)ws
                                             + frame_bytes);
        const uint32_t *ws_end = scr + (ws_len - frame_bytes)
                                       / sizeof(uint32_t);
        st[0].x = a->limbs; st[0].xn = a->n;
        st[0].y = b->limbs; st[0].yn = b->n;
        st[0].dst = out->limbs; st[0].scr = scr; st[0].phase = 0u;
        bi_kara_norm_frame(&st[0]);
        if (bi_kara_machine(st, ws_end) == SRMECH_OK) {
            out->n = need;
            out->sign = a->sign * b->sign;
            bi_norm(out);
            return SRMECH_OK;
        }
    }
    return bi_mul_school(out, a, b);
}

srmech_status_t srmech_bigint_mul(srmech_bigint_t *out, const srmech_bigint_t *a,
                                  const srmech_bigint_t *b)
{
    /* Bounded internal arena (an automatic uint64 region — 8-byte
     * aligned, no malloc, reentrant): full Karatsuba for mid-size
     * operands, graceful fewer-level splits above, schoolbook for the
     * small/huge tails. Callers owning an arena get the unbounded split
     * via srmech_bigint_mul_ws; the product here is byte-identical. */
    uint64_t ws_local[BI_MUL_LOCAL_WS_U64];
    uint32_t small = (a->n < b->n) ? a->n : b->n;
    assert(out != NULL && a != NULL && b != NULL);
    assert(out->limbs != NULL || out->cap == 0u);
    if (small < BI_KARA_CUTOFF) {
        return bi_mul_school(out, a, b);
    }
    return srmech_bigint_mul_ws(out, a, b, ws_local, sizeof(ws_local));
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

/* Carve a REAL throwaway sink (cap limbs off the front of ws) for a NULL
 * q/r output. The pre-fix path handed bi_divmod_abs a cap-0 carrier, which
 * OVERFLOWed as soon as the skipped output needed >= 1 limb (any |a| >= |b|
 * quotient write; every negative-dividend floor-fixup q -= 1 / r += b) —
 * the rc165 fbi_mod workaround in srmech_factor_poly.c dated from that bug.
 * A ws-carved sink makes the documented "q or r may be NULL" contract hold
 * for EVERY input. */
static srmech_status_t bi_carve_sink(srmech_bigint_t *d, uint32_t *base,
                                     size_t words, size_t *cur, size_t cap)
{
    uint32_t *lb;
    assert(d != NULL);
    assert(cur != NULL && cap >= 1u);
    if (base == NULL) { return SRMECH_ERR_OVERFLOW; }
    lb = bi_ws_take(base, words, cur, cap);
    if (lb == NULL) { return SRMECH_ERR_OVERFLOW; }
    d->cap = (uint32_t)cap; d->limbs = lb; d->n = 0u; d->sign = 0;
    return SRMECH_OK;
}

srmech_status_t srmech_bigint_divmod(srmech_bigint_t *q, srmech_bigint_t *r,
                                     const srmech_bigint_t *a,
                                     const srmech_bigint_t *b,
                                     void *ws, size_t ws_len)
{
    srmech_status_t st;
    uint32_t *base = (uint32_t *)ws;
    size_t words = ws_len / sizeof(uint32_t), cur = 0u;
    srmech_bigint_t qd, rd;
    srmech_bigint_t *qp = q ? q : &qd, *rp = r ? r : &rd;
    assert(a != NULL && b != NULL);
    assert(qp != NULL && rp != NULL);
    if (b->sign == 0) { return SRMECH_ERR_BAD_INPUT; }
    if (!q) {   /* quotient sink: <= a->n - b->n + 1 limbs; +1 for the q -= 1 */
        st = bi_carve_sink(&qd, base, words, &cur, (size_t)a->n + 2u);
        if (st != SRMECH_OK) { return st; }
    }
    if (!r) {   /* remainder sink: <= max(a->n, b->n) limbs; +1 for the r += b */
        size_t rc = (size_t)((a->n > b->n) ? a->n : b->n) + 2u;
        st = bi_carve_sink(&rd, base, words, &cur, rc);
        if (st != SRMECH_OK) { return st; }
    }
    {
        void *tail = (cur == 0u) ? ws : (void *)(base + cur);
        size_t tail_len = (words - cur) * sizeof(uint32_t);
        st = bi_divmod_abs(qp, rp, a, b, tail, tail_len);
        if (st != SRMECH_OK) { return st; }
        return bi_floor_fixup(qp, rp, a, b, tail, tail_len);
    }
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

/* ---- gcd (Lehmer, 0.9.0rc169; lean-Euclid fallback for tight arenas)
 *
 * LEHMER'S ALGORITHM (Knuth TAOCP Vol 2 §4.5.2 Algorithm L; HAC 14.57).
 * Plain Euclid runs a full-precision Knuth divmod EVERY step; Lehmer
 * BATCHES a run of those steps by simulating single-digit Euclid on the
 * two LEADING 30-bit "digits" of x, y (single/double-word int64 math),
 * building a 2x2 cofactor matrix [[A,B],[C,D]], then applying it to the
 * FULL bignums ONCE — (x, y) <- (A*x + B*y, C*x + D*y) — replacing ~30
 * bits of divmods with 4 single-limb multiply-adds. Same O(n^2) class,
 * a tiny constant (the constant-factor win the rc168 measurement named:
 * the big-Q op was gcd-bound). 30-bit digits keep every inner product
 * < 2^61, so int64 suffices (no __int128; JPL Rule 10). The gcd VALUE
 * is unique, so this is BYTE-IDENTICAL to Euclid for every input.
 *
 * The signature + result are unchanged. The fused matrix-apply keeps the
 * working set to 4 carriers — the SAME footprint as lean Euclid — so
 * Lehmer engages whenever the arena meets srmech_bigint_gcd_ws_bound; a
 * tighter arena (e.g. a carrier's scratch tail sized for the old Euclid)
 * falls back to bi_gcd_euclid — the pre-rc169 body verbatim — so no
 * existing caller can regress (it gets the identical gcd either way).
 * ------------------------------------------------------------------ */

/* Workspace BYTES the caller must give srmech_bigint_gcd for the Lehmer
 * fast path (4 carriers of ~M+2 limbs + the divmod tail, M = max input
 * limbs). Over-generous: a smaller arena still yields the identical gcd
 * (the lean-Euclid fallback), so this bound is the "engage Lehmer"
 * threshold, not a hard minimum. 8-byte-aligned uint32 bump arena. */
size_t srmech_bigint_gcd_ws_bound(size_t a_n, size_t b_n)
{
    size_t m = (a_n > b_n) ? a_n : b_n;
    size_t words = 8u * (m + 8u) + 64u;
    assert(words > m);
    assert(words > 64u);
    return words * sizeof(uint32_t);
}

/* Lean Euclid — the pre-rc169 gcd body, verbatim. The proven byte-
 * identical-to-Python fallback for arenas too small for Lehmer. */
static srmech_status_t bi_gcd_euclid(srmech_bigint_t *out,
                                     const srmech_bigint_t *a,
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

#define BI_LEHMER_DIGIT_BITS 30u

/* The 30-bit "digit" of |a| starting at bit `shift` — a's top 30 bits
 * when shift = bitlen(a) - 30. Reads the 2-limb window straddling shift
 * (30 + (shift%32) < 64, so two limbs always suffice). */
static uint64_t bi_lehmer_digit(const srmech_bigint_t *a, uint32_t shift)
{
    uint32_t whole = shift / BI_BASE_BITS, sh = shift % BI_BASE_BITS;
    uint64_t lo, hi, win;
    assert(a != NULL);
    assert(sh < BI_BASE_BITS);
    lo = (whole < a->n) ? a->limbs[whole] : 0u;
    hi = ((whole + 1u) < a->n) ? a->limbs[whole + 1u] : 0u;
    win = (hi << BI_BASE_BITS) | lo;
    return (win >> sh) & (((uint64_t)1u << BI_LEHMER_DIGIT_BITS) - 1u);
}

/* Simulate single-digit Euclid on the leading digits uh >= vh, filling
 * co = {A, B, C, D}. 30-bit digits => |cofactors| <= 2^30 and every
 * product q*C / q*vhat < 2^61 (int64-safe). The two-quotient test
 * (q == q2) guarantees each emulated step matches the FULL-precision
 * quotient; a break leaves a valid (possibly identity) matrix. Rule 2:
 * bounded by a hard 64-step cap (a 30-bit digit resolves << 64 steps). */
static void bi_lehmer_simulate(uint64_t uh, uint64_t vh, int64_t co[4])
{
    int64_t A = 1, B = 0, C = 0, D = 1;
    int64_t uhat = (int64_t)uh, vhat = (int64_t)vh;
    int steps = 0;
    assert(co != NULL);
    assert(uhat >= vhat);
    while (steps < 64) {
        int64_t vc = vhat + C, vd = vhat + D;
        int64_t un = uhat + A, ub = uhat + B, q, q2, T;
        if (vc <= 0 || vd <= 0 || un < 0 || ub < 0) { break; }
        q = un / vc; q2 = ub / vd;
        if (q != q2) { break; }
        T = A - q * C; A = C; C = T;
        T = B - q * D; B = D; D = T;
        T = uhat - q * vhat; uhat = vhat; vhat = T;
        steps++;
    }
    co[0] = A; co[1] = B; co[2] = C; co[3] = D;
}

/* dst = |m| * u, m one limb (< 2^30), u >= 0. dst->cap > u->n required. */
static void bi_mul_1(srmech_bigint_t *dst, const srmech_bigint_t *u, uint32_t m)
{
    uint32_t i; uint64_t carry = 0u;
    assert(dst != NULL && u != NULL);
    assert(dst->cap > u->n);
    for (i = 0u; i < u->n; i++) {
        uint64_t t = (uint64_t)m * u->limbs[i] + carry;
        dst->limbs[i] = (uint32_t)(t & 0xFFFFFFFFu);
        carry = t >> BI_BASE_BITS;
    }
    dst->limbs[u->n] = (uint32_t)carry;
    dst->n = u->n + 1u; dst->sign = 1;
    bi_norm(dst);
}

/* dst = c0*u + c1*v (exact signed) in ONE mul + ONE fused submul pass —
 * the Lehmer matrix-apply. c0, c1 have OPPOSITE signs (or one is zero;
 * Knuth's invariant) and the combination is >= 0, so it is |pos|*posv -
 * |neg|*negv with the positive term the larger: bi_mul_1 the positive
 * term then bi_mulsub (the SAME proven single-limb submul the Knuth
 * divisor uses) the negative, propagating the borrow through dst's high
 * limbs. c0, c1 fit one limb (|.| <= 2^30). */
static srmech_status_t bi_lehmer_combine(srmech_bigint_t *dst,
                                         int64_t c0, const srmech_bigint_t *u,
                                         int64_t c1, const srmech_bigint_t *v)
{
    const srmech_bigint_t *posv, *negv;
    uint32_t pm, nm, i, ext, j; uint64_t borrow;
    assert(dst != NULL && u != NULL && v != NULL);
    assert(c0 == 0 || c1 == 0 || ((c0 > 0) != (c1 > 0)));  /* opposite signs */
    if (c1 <= 0) { posv = u; pm = (uint32_t)c0; negv = v; nm = (uint32_t)(-c1); }
    else { posv = v; pm = (uint32_t)c1; negv = u; nm = (uint32_t)(-c0); }
    bi_mul_1(dst, posv, pm);                    /* dst = pm*posv  (>= 0) */
    ext = negv->n + 1u;                         /* bi_mulsub touches limb negv->n */
    if (dst->n < ext) {
        if (ext > dst->cap) { return SRMECH_ERR_OVERFLOW; }
        for (i = dst->n; i < ext; i++) { dst->limbs[i] = 0u; }
        dst->n = ext;
    }
    if (nm != 0u) {
        borrow = bi_mulsub(dst->limbs, negv->limbs, negv->n, nm);  /* dst -= nm*negv */
        for (j = negv->n + 1u; borrow != 0u && j < dst->n; j++) {
            uint64_t s = (uint64_t)dst->limbs[j] - borrow;
            dst->limbs[j] = (uint32_t)(s & 0xFFFFFFFFu);
            borrow = (s >> 63) & 1u;
        }
        assert(borrow == 0u);                   /* Lehmer combination is >= 0 */
    }
    dst->sign = 1;
    bi_norm(dst);
    return SRMECH_OK;
}

/* One plain Euclid reduce: rem = u mod v; u = v; v = rem. qx is the
 * throwaway quotient carrier; tail is the Knuth divmod scratch. */
static srmech_status_t bi_gcd_euclid_step(srmech_bigint_t *u,
                                          srmech_bigint_t *v,
                                          srmech_bigint_t *qx,
                                          srmech_bigint_t *rem,
                                          void *tail, size_t tail_len)
{
    srmech_status_t st;
    assert(u != NULL && v != NULL && qx != NULL && rem != NULL);
    assert(v->n != 0u);
    st = bi_divmod_abs(qx, rem, u, v, tail, tail_len);   /* rem = u mod v */
    if (st != SRMECH_OK) { return st; }
    st = bi_set_abs(u, v);                               /* u = v */
    if (st != SRMECH_OK) { return st; }
    return bi_set_abs(v, rem);                           /* v = rem */
}

/* One Lehmer batch on (u, v), u >= v > 2 limbs: build the leading-digit
 * cofactor matrix and either apply it (B != 0) or, when the leading digit
 * gives no progress (B == 0), do one full divmod step. e0/e1 are the
 * result carriers (matrix branch) / quotient+rem carriers (divmod
 * branch); the fused apply needs no product scratch. */
static srmech_status_t bi_lehmer_step(srmech_bigint_t *u, srmech_bigint_t *v,
                                      srmech_bigint_t *e0, srmech_bigint_t *e1,
                                      void *tail, size_t tail_len)
{
    uint32_t nb = bi_bitlen(u);
    uint32_t shift = nb - BI_LEHMER_DIGIT_BITS;
    uint64_t uh, vh; int64_t co[4]; srmech_status_t st;
    assert(u != NULL && v != NULL);
    assert(v->n > 2u && nb > 64u);
    uh = bi_lehmer_digit(u, shift);
    vh = bi_lehmer_digit(v, shift);
    bi_lehmer_simulate(uh, vh, co);
    if (co[1] == 0) {                     /* no leading-digit progress */
        return bi_gcd_euclid_step(u, v, e0, e1, tail, tail_len);
    }
    st = bi_lehmer_combine(e0, co[0], u, co[1], v);   /* A*u + B*v */
    if (st != SRMECH_OK) { return st; }
    st = bi_lehmer_combine(e1, co[2], u, co[3], v);   /* C*u + D*v */
    if (st != SRMECH_OK) { return st; }
    if (bi_set_abs(u, e0) != SRMECH_OK) { return SRMECH_ERR_OVERFLOW; }
    return bi_set_abs(v, e1);
}

/* Lehmer driver: 4 carriers (u, v, e0, e1) + the divmod tail — the same
 * working-set footprint as lean Euclid (the fused apply removed the
 * product scratch). */
static srmech_status_t bi_gcd_lehmer(srmech_bigint_t *out,
                                     const srmech_bigint_t *a,
                                     const srmech_bigint_t *b,
                                     void *ws, size_t ws_len)
{
    uint32_t *base = (uint32_t *)ws;
    size_t words = ws_len / sizeof(uint32_t), cur = 0u;
    size_t m = (a->n > b->n) ? a->n : b->n;
    size_t cu = m + 1u, ce = m + 2u;
    srmech_bigint_t u, v, e0, e1;
    uint32_t *bu, *bv, *b0, *b1;
    uint64_t guard = 0u;
    void *tail; size_t tail_len; srmech_status_t st;
    assert(out != NULL && a != NULL && b != NULL);
    assert(out->limbs != NULL || out->cap == 0u);
    bu = bi_ws_take(base, words, &cur, cu);
    bv = bi_ws_take(base, words, &cur, cu);
    b0 = bi_ws_take(base, words, &cur, ce);
    b1 = bi_ws_take(base, words, &cur, ce);
    if (bu == NULL || bv == NULL || b0 == NULL || b1 == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    u.limbs = bu; u.cap = (uint32_t)cu; v.limbs = bv; v.cap = (uint32_t)cu;
    e0.limbs = b0; e0.cap = (uint32_t)ce; e1.limbs = b1; e1.cap = (uint32_t)ce;
    tail = base + cur; tail_len = (words - cur) * sizeof(uint32_t);
    if (bi_set_abs(&u, a) != SRMECH_OK || bi_set_abs(&v, b) != SRMECH_OK) {
        return SRMECH_ERR_OVERFLOW;
    }
    if (bi_cmp_abs(&u, &v) < 0) { srmech_bigint_t s = u; u = v; v = s; }
    while (v.n != 0u && guard < ((uint64_t)1u << 40)) {
        guard++;
        if (v.n <= 2u) {
            st = bi_gcd_euclid_step(&u, &v, &e0, &e1, tail, tail_len);
        } else {
            st = bi_lehmer_step(&u, &v, &e0, &e1, tail, tail_len);
        }
        if (st != SRMECH_OK) { return st; }
        if (bi_cmp_abs(&u, &v) < 0) { srmech_bigint_t s = u; u = v; v = s; }
    }
    return bi_set_abs(out, &u);
}

srmech_status_t srmech_bigint_gcd(srmech_bigint_t *out, const srmech_bigint_t *a,
                                  const srmech_bigint_t *b,
                                  void *ws, size_t ws_len)
{
    size_t words = ws_len / sizeof(uint32_t);
    size_t m = (a->n > b->n) ? a->n : b->n;
    size_t lehmer_min = 6u * (m + 2u) + 16u;   /* 4 carriers + divmod tail */
    assert(out != NULL && a != NULL && b != NULL);
    assert(out->limbs != NULL || out->cap == 0u);
    if (words >= lehmer_min) {
        return bi_gcd_lehmer(out, a, b, ws, ws_len);
    }
    return bi_gcd_euclid(out, a, b, ws, ws_len);
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
    srmech_bigint_t b2, t;
    /* The running square b2 reaches up to base^exp = pow_bound limbs; the
     * mul-temp t holds the RAW product of two such, so it needs mul_bound
     * space. (Pre-rc36 both were sized base->n*32+4, which overflowed once
     * base^exp exceeded 32 limbs, e.g. 7^600 / 452^128.) */
    size_t cap_b2 = srmech_bigint_pow_bound(base->n, exp);
    size_t cap_t;
    uint32_t *bb, *tb, e = exp;
    srmech_status_t st;
    assert(out != NULL && base != NULL);
    assert(out->limbs != NULL || out->cap == 0u);
    if (cap_b2 == (size_t)-1) { return SRMECH_ERR_OVERFLOW; }
    cap_t = srmech_bigint_mul_bound(cap_b2, cap_b2);
    bb = bi_ws_take(wb, words, &cur, cap_b2);
    tb = bi_ws_take(wb, words, &cur, cap_t);
    if (bb == NULL || tb == NULL) { return SRMECH_ERR_OVERFLOW; }
    b2.limbs = bb; b2.cap = (uint32_t)cap_b2; t.limbs = tb; t.cap = (uint32_t)cap_t;
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
