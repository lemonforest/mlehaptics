/* srmech_ryu.c — the shortest-round-trip double -> decimal writer (rc403).
 *
 * ONE conversion engine, integer-only and table-driven, behind
 * srmech_double_repr(). Both byte-parity surfaces ride it: the MCP marshal's
 * mm_emit_double (srmech_mcp_marshal.c) and the canonical JSON writer's
 * json_write_double (srmech_json.c).
 *
 * WHY THIS FILE EXISTS — the two defects it replaces
 * ---------------------------------------------------
 * Both writers previously reached for printf, and printf is the wrong tool for
 * a serialiser whose bytes go behind a sha256:
 *
 *   (1) json_write_double used "%.17g". That is PLATFORM-DEPENDENT — Windows
 *       spells the exponent `1e+017`, Linux `1e+17` — so the same C source, on
 *       the same double, hashed differently per host. It also diverged from
 *       CPython on 8 of 16 everyday values (0.1 -> "0.10000000000000001").
 *
 *   (2) srmech_double_repr (rc190..rc402) searched for the shortest `%.*e`
 *       that strtod round-trips. That is the shortest PRINTF-REACHABLE
 *       round-tripper, not the shortest round-tripper. When the correctly-
 *       rounded decimal at some precision is an exact TIE, glibc breaks it
 *       to-even; the tie's OTHER neighbour — which does round-trip at that
 *       length — is never offered as a candidate, so the search fell through
 *       to one digit too many. MEASURED: 92 of the 4196 signed powers of two
 *       (2.2%) disagreed with CPython, 2**-24 (the float32 machine epsilon)
 *       among them:
 *           2**-24 = 5.9604644775390625e-08
 *             p=15 -> 5.960464477539062e-08   round-trips? no  (tie-to-even)
 *             p=16 -> 5.9604644775390625e-08  round-trips? YES <- was emitted
 *             CPython repr  5.960464477539063e-08  <- 16 digits, tie away
 *       The header's claim that this was "David Gay 'r' mode" was false, and
 *       the wrong bytes reached callers at SRMECH_OK through the MCP surface.
 *
 * Ryu (Ulf Adams, "Ryu: fast float-to-string conversion", PLDI 2018) has
 * neither failure mode by construction: the shortest interval is computed in
 * exact integer arithmetic against vendored 128-bit powers of five, so the
 * answer depends on nothing but the input bits. No libm, no printf, no strtod,
 * and no floating-point arithmetic anywhere in the digit path.
 *
 * ONE MULTIPLY PATH, ON PURPOSE
 * -----------------------------
 * Ryu needs a 64x64 -> 128 multiply. The obvious speed move is `unsigned
 * __int128` on gcc/clang with `_umul128` under MSVC and a limb fallback
 * elsewhere — three code paths. This file uses only the 32-bit-limb form
 * (ryu_umul128). A 64x64 product is EXACT in every path, so the paths cannot
 * disagree numerically; what they can do is disagree in whether they COMPILE
 * (MSVC has no __int128; _umul128 is x64/ARM64-only; the unused-function
 * warning under -DNDEBUG bit rc397). Since this is a formatter and not an
 * inner loop, buying ~4 extra 32-bit multiplies per 64x64 to make "identical
 * bytes on every compiler" a structural property rather than a tested one is
 * the right trade. There is nothing to cross-check because there is one path.
 *
 * TWO SEPARABLE HALVES
 * --------------------
 *   1. ryu_d2d()  — shortest decimal DIGITS + base-10 exponent (Ryu proper).
 *   2. dr_*()     — FORMATTING those digits into CPython's exact repr spelling.
 * Half 2 is not a detail: repr switches to scientific iff decpt <= -4 or
 * decpt > 16 (repr(1e16) == '1e+16' but repr(1e15) == '1000000000000000.0'),
 * always keeps a trailing '.0' on an integral fixed form, and pads the
 * exponent to a MINIMUM of two digits ('5e-08', never '5e-8').
 *
 * JPL Power-of-Ten: no recursion, no goto, no malloc, no multi-line macros,
 * every function under 60 lines with >= 2 assertions.
 */

#include <assert.h>
#include <stdint.h>
#include <string.h>

#include "srmech.h"
#include "srmech_ryu_tables.h"

#define RYU_MANTISSA_BITS  52
#define RYU_BIAS           1023

/* Intermediate decimal interval: the exact value `vr` and the half-way bounds
 * `vp` / `vm`, all scaled to 10^e10, plus the two trailing-zero flags and the
 * boundary-inclusion flag. Bounds are INCLUSIVE iff the binary mantissa is
 * even — IEEE-754 round-half-to-even — and that is exactly what makes the tie
 * behaviour agree with CPython's dtoa mode 0. */
typedef struct {
    uint64_t vr;
    uint64_t vp;
    uint64_t vm;
    int32_t  e10;
    int      vr_zeros;
    int      vm_zeros;
    int      accept_bounds;
} ryu_interval_t;

/* Shortest decimal: value == mantissa * 10^exponent. */
typedef struct {
    uint64_t mantissa;
    int32_t  exponent;
} ryu_decimal_t;

/* ------------------------------------------------------------------ *
 * Integer logarithms. These magic-multiply forms are EXACT (not merely
 * approximate) over the whole reachable range; c/tools/gen_ryu_tables.py
 * proves it by comparing them against Python's exact integers for every
 * e in [0, 1600), and the same file emits the tables they index.
 * ------------------------------------------------------------------ */

/* ceil(log2(5^e)) == bit_length(5^e), for e >= 0. */
static int32_t ryu_pow5bits(int32_t e)
{
    assert(e >= 0);
    assert(e < 1600);
    return (int32_t)((((uint32_t)e * 1217359u) >> 19) + 1u);
}

/* floor(log10(2^e)), for e >= 0. */
static uint32_t ryu_log10_pow2(int32_t e)
{
    assert(e >= 0);
    assert(e < 1600);
    return ((uint32_t)e * 78913u) >> 18;
}

/* floor(log10(5^e)), for e >= 0. */
static uint32_t ryu_log10_pow5(int32_t e)
{
    assert(e >= 0);
    assert(e < 1600);
    return ((uint32_t)e * 732923u) >> 20;
}

/* ------------------------------------------------------------------ *
 * Exact 64x64 -> 128 multiply, 32-bit limbs. The ONLY multiply path
 * (see the header comment). Portable to any conforming C11 compiler.
 * ------------------------------------------------------------------ */
static uint64_t ryu_umul128(uint64_t a, uint64_t b, uint64_t *hi)
{
    uint64_t a_lo = a & 0xFFFFFFFFu, a_hi = a >> 32;
    uint64_t b_lo = b & 0xFFFFFFFFu, b_hi = b >> 32;
    uint64_t p00 = a_lo * b_lo, p01 = a_lo * b_hi;
    uint64_t p10 = a_hi * b_lo, p11 = a_hi * b_hi;
    uint64_t mid;
    assert(hi != NULL);
    mid = (p00 >> 32) + (p01 & 0xFFFFFFFFu) + (p10 & 0xFFFFFFFFu);
    /* `mid` sums three values each < 2^32 into a 64-bit accumulator, so it
     * cannot wrap and the carry out is exactly mid >> 32. */
    assert(mid >= (p00 >> 32));
    *hi = p11 + (p01 >> 32) + (p10 >> 32) + (mid >> 32);
    return (mid << 32) | (p00 & 0xFFFFFFFFu);
}

/* floor(m * MUL / 2^j) where MUL = mul[1]*2^64 + mul[0], keeping only the high
 * half of the low partial product — Ryu's error analysis (PLDI 2018, section 4)
 * shows the discarded 64 low bits cannot change the shortest result at
 * SRMECH_RYU_POW5_BITCOUNT = 125 table bits. `j` is always in (64, 128); the
 * generator proves the reachable shift distance is [54, 61], so neither shift
 * below is ever undefined. */
static uint64_t ryu_mul_shift64(uint64_t m, const uint64_t mul[2], int32_t j)
{
    uint64_t hi0 = 0u, hi1 = 0u, lo1, sum;
    uint32_t dist;
    assert(mul != NULL);
    assert(j > 64 && j < 128);
    (void)ryu_umul128(m, mul[0], &hi0);
    lo1 = ryu_umul128(m, mul[1], &hi1);
    sum = hi0 + lo1;
    if (sum < hi0) {
        hi1++;                                   /* carry into the high half */
    }
    dist = (uint32_t)(j - 64);
    return (hi1 << (64u - dist)) | (sum >> dist);
}

/* The three interval endpoints share one multiply shape: 4*m2 (the value),
 * 4*m2+2 (upper half-way) and 4*m2-1-mm_shift (lower half-way). */
static uint64_t ryu_mul_shift_all(uint64_t m2, const uint64_t mul[2], int32_t j,
                                  uint64_t *vp, uint64_t *vm, uint32_t mm_shift)
{
    assert(vp != NULL && vm != NULL);
    assert(mm_shift <= 1u);
    *vp = ryu_mul_shift64(4u * m2 + 2u, mul, j);
    *vm = ryu_mul_shift64(4u * m2 - 1u - mm_shift, mul, j);
    return ryu_mul_shift64(4u * m2, mul, j);
}

/* ------------------------------------------------------------------ *
 * Trailing-zero predicates.
 * ------------------------------------------------------------------ */

/* Largest p with 5^p | value. Bounded by 27 because 5^28 > 2^64. */
static uint32_t ryu_pow5_factor(uint64_t value)
{
    const uint64_t inv5 = 14757395258967641293u;   /* 5 * inv5 == 1 mod 2^64 */
    const uint64_t max5 = 3689348814741910323u;    /* floor(2^64 / 5)        */
    uint32_t count = 0u;
    assert(value != 0u);
    for (;;) {
        value *= inv5;
        if (value > max5) {
            break;
        }
        count++;
    }
    assert(count <= 27u);
    return count;
}

static int ryu_multiple_of_pow5(uint64_t value, uint32_t p)
{
    assert(value != 0u);
    assert(p < 64u);
    return (ryu_pow5_factor(value) >= p) ? 1 : 0;
}

static int ryu_multiple_of_pow2(uint64_t value, uint32_t p)
{
    assert(value != 0u);
    assert(p < 64u);
    return ((value & ((1ull << p) - 1ull)) == 0u) ? 1 : 0;
}

/* ------------------------------------------------------------------ *
 * Step 3 — scale the binary interval into a decimal power base. Split
 * into the two exponent-sign branches so each stays under 60 lines.
 * ------------------------------------------------------------------ */

/* Non-negative binary exponent: divide by 10^q using the INVERSE table. */
static void ryu_interval_pos(uint64_t m2, int32_t e2, uint32_t mm_shift,
                             ryu_interval_t *iv)
{
    uint32_t q;
    int32_t k, i;
    uint64_t mv;
    assert(iv != NULL);
    assert(e2 >= 0);
    q = ryu_log10_pow2(e2) - ((e2 > 3) ? 1u : 0u);
    iv->e10 = (int32_t)q;
    k = SRMECH_RYU_POW5_INV_BITCOUNT + ryu_pow5bits((int32_t)q) - 1;
    i = -e2 + (int32_t)q + k;
    iv->vr = ryu_mul_shift_all(m2, RYU_POW5_INV_SPLIT[q], i,
                               &iv->vp, &iv->vm, mm_shift);
    if (q > 21u) {
        return;                     /* no endpoint can carry trailing zeros */
    }
    mv = 4u * m2;
    /* At most one of mm, mv, mp can be a multiple of 5. */
    if (mv % 5u == 0u) {
        iv->vr_zeros = ryu_multiple_of_pow5(mv, q);
    } else if (iv->accept_bounds) {
        iv->vm_zeros = ryu_multiple_of_pow5(mv - 1u - mm_shift, q);
    } else {
        iv->vp -= (uint64_t)ryu_multiple_of_pow5(mv + 2u, q);
    }
}

/* Negative binary exponent: multiply by 5^i using the FORWARD table. */
static void ryu_interval_neg(uint64_t m2, int32_t e2, uint32_t mm_shift,
                             ryu_interval_t *iv)
{
    uint32_t q;
    int32_t i, k, j;
    assert(iv != NULL);
    assert(e2 < 0);
    q = ryu_log10_pow5(-e2) - ((-e2 > 1) ? 1u : 0u);
    iv->e10 = (int32_t)q + e2;
    i = -e2 - (int32_t)q;
    k = ryu_pow5bits(i) - SRMECH_RYU_POW5_BITCOUNT;
    j = (int32_t)q - k;
    iv->vr = ryu_mul_shift_all(m2, RYU_POW5_SPLIT[i], j,
                               &iv->vp, &iv->vm, mm_shift);
    if (q <= 1u) {
        /* mv == 4*m2 always has >= 2 trailing zero bits. */
        iv->vr_zeros = 1;
        if (iv->accept_bounds) {
            iv->vm_zeros = (mm_shift == 1u) ? 1 : 0;
        } else {
            iv->vp--;
        }
    } else if (q < 63u) {
        iv->vr_zeros = ryu_multiple_of_pow2(4u * m2, q);
    }
}

/* ------------------------------------------------------------------ *
 * Step 4 — shorten. Two variants: the rare exact-tail case (~0.7% of
 * inputs, where a trailing-zero flag is live and the half-even rule
 * must be honoured) and the common case.
 * ------------------------------------------------------------------ */

/* Strip digits while an endpoint still carries trailing zeros. `*last` holds
 * the most recently removed digit; `*removed` counts the strips. */
static void ryu_strip_exact(ryu_interval_t *iv, uint8_t *last, int32_t *removed)
{
    uint64_t vr10;
    assert(iv != NULL);
    assert(last != NULL && removed != NULL);
    while (iv->vp / 10u > iv->vm / 10u) {
        iv->vm_zeros &= (iv->vm % 10u == 0u) ? 1 : 0;
        iv->vr_zeros &= (*last == 0u) ? 1 : 0;
        *last = (uint8_t)(iv->vr % 10u);
        iv->vr /= 10u; iv->vp /= 10u; iv->vm /= 10u;
        (*removed)++;
    }
    while (iv->vm_zeros && (iv->vm % 10u == 0u)) {
        vr10 = iv->vr / 10u;
        iv->vr_zeros &= (*last == 0u) ? 1 : 0;
        *last = (uint8_t)(iv->vr % 10u);
        iv->vr = vr10; iv->vp /= 10u; iv->vm /= 10u;
        (*removed)++;
    }
}

/* The exact-tail shortening (a trailing-zero flag is live on entry). */
static uint64_t ryu_shorten_exact(ryu_interval_t *iv, int32_t *removed)
{
    uint8_t last = 0u;
    int bump;
    assert(iv != NULL);
    assert(removed != NULL);
    ryu_strip_exact(iv, &last, removed);
    if (iv->vr_zeros && last == 5u && (iv->vr % 2u) == 0u) {
        last = 4u;             /* exact ...50..0 tie -> round half to EVEN */
    }
    bump = ((iv->vr == iv->vm && (!iv->accept_bounds || !iv->vm_zeros))
            || last >= 5u) ? 1 : 0;
    return iv->vr + (uint64_t)bump;
}

/* The common shortening (no trailing zeros anywhere; ~99.3% of inputs). */
static uint64_t ryu_shorten_common(ryu_interval_t *iv, int32_t *removed)
{
    int round_up = 0;
    assert(iv != NULL);
    assert(removed != NULL);
    if (iv->vp / 100u > iv->vm / 100u) {          /* two digits at a time */
        round_up = (iv->vr % 100u >= 50u) ? 1 : 0;
        iv->vr /= 100u; iv->vp /= 100u; iv->vm /= 100u;
        *removed += 2;
    }
    while (iv->vp / 10u > iv->vm / 10u) {
        round_up = (iv->vr % 10u >= 5u) ? 1 : 0;
        iv->vr /= 10u; iv->vp /= 10u; iv->vm /= 10u;
        (*removed)++;
    }
    return iv->vr + (uint64_t)(((iv->vr == iv->vm) || round_up) ? 1 : 0);
}

/* Shortest decimal for a POSITIVE finite double given its raw IEEE fields. */
static ryu_decimal_t ryu_d2d(uint64_t ieee_mantissa, uint32_t ieee_exponent)
{
    ryu_interval_t iv;
    ryu_decimal_t fd;
    int32_t e2, removed = 0;
    uint64_t m2;
    uint32_t mm_shift;
    assert(ieee_exponent < 2047u);
    assert(ieee_mantissa < (1ull << RYU_MANTISSA_BITS));
    memset(&iv, 0, sizeof iv);
    if (ieee_exponent == 0u) {
        e2 = 1 - RYU_BIAS - RYU_MANTISSA_BITS - 2;
        m2 = ieee_mantissa;
    } else {
        e2 = (int32_t)ieee_exponent - RYU_BIAS - RYU_MANTISSA_BITS - 2;
        m2 = (1ull << RYU_MANTISSA_BITS) | ieee_mantissa;
    }
    iv.accept_bounds = ((m2 & 1u) == 0u) ? 1 : 0;
    mm_shift = (ieee_mantissa != 0u || ieee_exponent <= 1u) ? 1u : 0u;
    if (e2 >= 0) {
        ryu_interval_pos(m2, e2, mm_shift, &iv);
    } else {
        ryu_interval_neg(m2, e2, mm_shift, &iv);
    }
    if (iv.vm_zeros || iv.vr_zeros) {
        fd.mantissa = ryu_shorten_exact(&iv, &removed);
    } else {
        fd.mantissa = ryu_shorten_common(&iv, &removed);
    }
    fd.exponent = iv.e10 + removed;
    return fd;
}

/* ------------------------------------------------------------------ *
 * Half 2 — FORMATTING to CPython's exact repr(float) spelling.
 * ------------------------------------------------------------------ */

/* Decimal digits of v (1..17). Precondition: 0 < v < 10^17. */
static uint32_t ryu_decimal_length(uint64_t v)
{
    uint64_t p = 10u;
    uint32_t n = 1u;
    assert(v > 0u);
    assert(v < 100000000000000000ull);
    while (n < 18u && v >= p) {
        p *= 10u;
        n++;
    }
    return n;
}

/* Write the decimal digits of v into digs (>= 18 chars); returns the count. */
static uint32_t ryu_digits(uint64_t v, char *digs)
{
    uint32_t n, i;
    assert(digs != NULL);
    assert(v > 0u);
    n = ryu_decimal_length(v);
    for (i = n; i > 0u; i--) {
        digs[i - 1u] = (char)('0' + (int)(v % 10u));
        v /= 10u;
    }
    return n;
}

/* Append `n` '0' characters at *pos. */
static void dr_zeros(char *out, size_t *pos, int n)
{
    int i;
    assert(out != NULL && pos != NULL);
    assert(n >= 0);
    for (i = 0; i < n; i++) {
        out[(*pos)++] = '0';
    }
}

/* Write the base-10 exponent: 'e', sign, then a MINIMUM of two digits
 * ('5e-08', never '5e-8'; '1e+100' keeps all three). Integer-only — printf's
 * exponent width is platform-defined ('1e+017' on Windows) and inheriting that
 * is exactly what this writer must not do. */
static void dr_exponent(char *out, size_t *pos, int exp10)
{
    int mag, hundreds;
    assert(out != NULL && pos != NULL);
    assert(exp10 > -400 && exp10 < 400);
    out[(*pos)++] = 'e';
    out[(*pos)++] = (exp10 < 0) ? '-' : '+';
    /* Class K pin-slot (sign as a phase boundary), not an ALU abs(). */
    mag = (exp10 < 0) ? -exp10 : exp10;
    hundreds = mag / 100;
    if (hundreds != 0) {
        out[(*pos)++] = (char)('0' + hundreds);
    }
    out[(*pos)++] = (char)('0' + (mag / 10) % 10);
    out[(*pos)++] = (char)('0' + mag % 10);
}

/* Scientific form: D[.DDDD]e{+-}XX. */
static void dr_scientific(char *out, size_t *pos, const char *digs,
                          uint32_t ndig, int decpt)
{
    uint32_t i;
    assert(out != NULL && pos != NULL && digs != NULL);
    assert(ndig >= 1u);
    out[(*pos)++] = digs[0];
    if (ndig > 1u) {
        out[(*pos)++] = '.';
        for (i = 1u; i < ndig; i++) {
            out[(*pos)++] = digs[i];
        }
    }
    dr_exponent(out, pos, decpt - 1);
}

/* Fixed form, with CPython's mandatory trailing '.0' on an integral value. */
static void dr_fixed(char *out, size_t *pos, const char *digs,
                     uint32_t ndig, int decpt)
{
    uint32_t i;
    assert(out != NULL && pos != NULL && digs != NULL);
    assert(ndig >= 1u);
    if (decpt <= 0) {                                /* 0.<zeros><digits> */
        out[(*pos)++] = '0';
        out[(*pos)++] = '.';
        dr_zeros(out, pos, -decpt);
        for (i = 0u; i < ndig; i++) { out[(*pos)++] = digs[i]; }
    } else if ((uint32_t)decpt >= ndig) {            /* <digits><zeros>.0 */
        for (i = 0u; i < ndig; i++) { out[(*pos)++] = digs[i]; }
        dr_zeros(out, pos, decpt - (int)ndig);
        out[(*pos)++] = '.';
        out[(*pos)++] = '0';
    } else {                                         /* <digits>.<digits> */
        for (i = 0u; i < (uint32_t)decpt; i++) { out[(*pos)++] = digs[i]; }
        out[(*pos)++] = '.';
        for (i = (uint32_t)decpt; i < ndig; i++) { out[(*pos)++] = digs[i]; }
    }
}

/* ------------------------------------------------------------------ *
 * The public entry point.
 * ------------------------------------------------------------------ */

srmech_status_t srmech_double_repr(double v, char *out, size_t cap,
                                   size_t *out_len)
{
    char digs[24];
    ryu_decimal_t fd;
    uint64_t bits, mantissa;
    uint32_t exponent, ndig;
    int decpt, neg;
    size_t pos = 0u;
    /* A NULL / too-small buffer is a contractually-handled caller error and
     * returns NULL_ARG BEFORE any assert fires (rc715). */
    if (out == NULL || out_len == NULL || cap < 32u) {
        return SRMECH_ERR_NULL_ARG;
    }
    memcpy(&bits, &v, sizeof bits);
    neg = (int)(bits >> 63);
    exponent = (uint32_t)((bits >> RYU_MANTISSA_BITS) & 0x7FFu);
    mantissa = bits & ((1ull << RYU_MANTISSA_BITS) - 1ull);
    assert(cap >= 32u);
    if (exponent == 0x7FFu) {
        return SRMECH_ERR_BAD_INPUT;                 /* NaN / +-Inf: defer */
    }
    if (exponent == 0u && mantissa == 0u) {
        const char *z = neg ? "-0.0" : "0.0";
        memcpy(out, z, strlen(z) + 1u);
        *out_len = strlen(z);
        return SRMECH_OK;
    }
    fd = ryu_d2d(mantissa, exponent);
    ndig = ryu_digits(fd.mantissa, digs);
    decpt = fd.exponent + (int)ndig;
    if (neg) {
        out[pos++] = '-';
    }
    /* CPython format_float_short, 'r' mode: scientific iff decpt <= -4 or
     * decpt > 16. repr(1e16) == '1e+16'; repr(1e15) == '1000000000000000.0'. */
    if (decpt <= -4 || decpt > 16) {
        dr_scientific(out, &pos, digs, ndig, decpt);
    } else {
        dr_fixed(out, &pos, digs, ndig, decpt);
    }
    assert(pos < cap);
    out[pos] = '\0';
    *out_len = pos;
    return SRMECH_OK;
}
