/*
 * test_srmech_sqrt_subnormal.c — 0.9.0rc476 BARE-C-HOST gate for the
 * CORRECT ROUNDING of srmech_rational_sqrt and srmech_sqrt_q61 (`#T1188`).
 *
 * THE DEFECT. Through rc475 the root was isqrt(M << 54) with M read straight
 * out of the IEEE mantissa field, so its WIDTH tracked the operand's magnitude
 * instead of being fixed: a SUBNORMAL x has M far below 2^52, and M = 1 gives
 * isqrt(1 << 54) = 2^27 — a 28-bit root where 53 are needed. Measured at the
 * exported symbol, no Python in the path: 4032 of the 4096 subnormal mantissas
 * 1..4096 served a double that is not the correctly rounded root, the worst by
 * 16,609,076 ulps; and 480 of the 1956 non-square integers in 2..2000 came
 * back one ulp LOW.
 *
 * WHY THE PREVIOUS EVIDENCE DID NOT CATCH IT. srmech_sqrt.c's own banner said
 * "Validated vs libm to machine epsilon (rel err <= 2.3e-16) over 50000+
 * values". That is (a) a LIBM ORACLE, which this library does not link and a
 * bare-C host cannot appeal to, and (b) a RELATIVE-ERROR bound, which cannot
 * see a 1-ulp misround at all. It passed for the whole life of the defect.
 *
 * SO THIS FILE USES NO ORACLE. It carries an INDEPENDENT CERTIFICATE in exact
 * 128-bit integer arithmetic: d = m*2^f is the correctly rounded double
 * nearest sqrt(x) if and only if it sits strictly inside its own two rounding
 * midpoints, which after squaring is
 *
 *      (2m-1)^2  <  mant << S  <  (2m+1)^2,      S = e - 2f + 2
 *
 * for x = mant*2^e, with (4m-1)^2 and S-2 on the low side at the binade floor
 * (m == 2^52), where the double below is half as widely spaced. Both sides fit
 * in 128 bits for every row swept here, and the comparison is done with a
 * local 64x64 -> 128 multiply — no __int128, no division, no libm, and nothing
 * borrowed from the code under test.
 *
 * Build + run (Linux gcc / macOS clang), pedantic, warnings = errors:
 *   cc -std=c11 -Wall -Wextra -Wpedantic -Werror -I../include \
 *      test_srmech_sqrt_subnormal.c ../src/srmech_*.c -lm -o /tmp/sq && /tmp/sq
 * or, as CI runs it, through ctest:
 *   ctest --test-dir build -R sqrt_subnormal --output-on-failure
 *
 * RUNTIME `if`, NEVER `assert`. The shipped wheel builds Release, Release
 * implies -DNDEBUG, and an assert compiled out of a Release build is a CI-lane
 * instrument rather than a gate. Every row is a runtime comparison that
 * reports and counts, and main returns non-zero if any row failed.
 *
 * NO abs() ANYWHERE. Every range row is an explicit two-sided comparison and
 * every sign question is a Class-K pin-slot test, which is this project's
 * standing discipline and also happens to be what keeps the file libm-free.
 *
 * License: MIT.
 */

#include "srmech.h"

#include <stdint.h>
#include <stdio.h>
#include <string.h>

static int g_passed = 0;
static int g_failed = 0;
static int g_skipped = 0;

/* ------------------------------------------------------------------ *
 * 128-bit helpers. Enough for the certificate and nothing more.
 * ------------------------------------------------------------------ */
typedef struct { uint64_t hi; uint64_t lo; } u128;

static u128 u128_mul(uint64_t a, uint64_t b)
{
    uint64_t a0 = a & 0xFFFFFFFFu, a1 = a >> 32;
    uint64_t b0 = b & 0xFFFFFFFFu, b1 = b >> 32;
    uint64_t p00 = a0 * b0, p01 = a0 * b1, p10 = a1 * b0, p11 = a1 * b1;
    uint64_t mid = (p00 >> 32) + (p01 & 0xFFFFFFFFu) + (p10 & 0xFFFFFFFFu);
    u128 r;
    r.lo = (p00 & 0xFFFFFFFFu) | (mid << 32);
    r.hi = p11 + (p01 >> 32) + (p10 >> 32) + (mid >> 32);
    return r;
}

/* v << s for s in [0, 127], as a 128-bit value. Returns 0 in *ok when the
 * shift would lose a bit off the top, so a row that cannot be certified is
 * SKIPPED and counted rather than silently passed. */
static u128 u128_shl(uint64_t v, unsigned s, int *ok)
{
    u128 r;
    unsigned bl = 0;
    uint64_t t = v;
    while (t != 0u) { t >>= 1; bl++; }
    *ok = (s < 128u) && (bl + s <= 128u);
    r.hi = 0u;
    r.lo = 0u;
    if (!*ok) { return r; }
    if (s >= 64u) { r.hi = (s == 64u) ? v : (v << (s - 64u)); r.lo = 0u; }
    else if (s == 0u) { r.lo = v; }
    else { r.hi = v >> (64u - s); r.lo = v << s; }
    return r;
}

static int u128_cmp(u128 a, u128 b)
{
    if (a.hi != b.hi) { return (a.hi > b.hi) ? 1 : -1; }
    if (a.lo != b.lo) { return (a.lo > b.lo) ? 1 : -1; }
    return 0;
}

/* ------------------------------------------------------------------ *
 * IEEE decomposition, by bits. No frexp, no libm.
 * ------------------------------------------------------------------ */
static uint64_t bits_of(double x)
{
    uint64_t b;
    memcpy(&b, &x, sizeof b);
    return b;
}

static double double_of(uint64_t b)
{
    double x;
    memcpy(&x, &b, sizeof x);
    return x;
}

/* x = *out_mant * 2^(*out_e) for a positive finite x. Returns 0 if x is not
 * positive finite. */
static int decompose(double x, uint64_t *out_mant, int32_t *out_e)
{
    uint64_t b = bits_of(x);
    uint32_t raw = (uint32_t)((b >> 52) & 0x7FFu);
    uint64_t frac = b & ((UINT64_C(1) << 52) - 1u);
    if (!(x > 0.0) || raw == 0x7FFu) { return 0; }
    *out_mant = (raw == 0u) ? frac : (frac | (UINT64_C(1) << 52));
    *out_e = (raw == 0u) ? -1074 : (int32_t)raw - 1075;
    return 1;
}

/* ------------------------------------------------------------------ *
 * THE CERTIFICATE. Returns 1 = correctly rounded, 0 = NOT, -1 = out of the
 * 128-bit window this file can decide (reported as a skip, never as a pass).
 * ------------------------------------------------------------------ */
static int is_correctly_rounded(double x, double d)
{
    uint64_t xm = 0u, m = 0u;
    int32_t xe = 0, f = 0;
    u128 lo_sq, hi_sq, rad_hi, rad_lo;
    int s_hi, s_lo, ok_hi = 0, ok_lo = 0;
    if (!decompose(x, &xm, &xe) || !decompose(d, &m, &f)) { return -1; }
    if (m < (UINT64_C(1) << 52)) { return -1; }        /* subnormal root: not here */
    /* upper: mant*2^xe < (2m+1)^2 * 2^(2f-2)  <=>  mant << (xe-2f+2) < (2m+1)^2
     * lower: the same shift, EXCEPT at the binade floor (m == 2^52), where the
     * double below is half as widely spaced, so the midpoint is
     * (4m-1)*2^(f-2) and squaring gives the shift xe-2f+4 — TWO MORE, not two
     * fewer. Getting that sign wrong reported 42 exact-power-of-two subnormals
     * as misrounded when they are exact; recorded because the failure text
     * pointed at the code under test rather than at the instrument. */
    s_hi = (int)xe - 2 * (int)f + 2;
    s_lo = (m == (UINT64_C(1) << 52)) ? (s_hi + 2) : s_hi;
    if (s_hi < 0 || s_lo < 0) { return -1; }
    hi_sq = u128_mul(2u * m + 1u, 2u * m + 1u);
    lo_sq = (m == (UINT64_C(1) << 52)) ? u128_mul(4u * m - 1u, 4u * m - 1u)
                                       : u128_mul(2u * m - 1u, 2u * m - 1u);
    rad_hi = u128_shl(xm, (unsigned)s_hi, &ok_hi);
    rad_lo = u128_shl(xm, (unsigned)s_lo, &ok_lo);
    if (!ok_hi || !ok_lo) { return -1; }
    /* strict on both sides; an exact midpoint would need an EVEN m, and an
     * inexact core root is odd, so the strict form is the whole rule here. */
    if (u128_cmp(rad_hi, hi_sq) >= 0) { return 0; }
    if (u128_cmp(rad_lo, lo_sq) <= 0) { return 0; }
    return 1;
}

/* ------------------------------------------------------------------ *
 * Rows.
 * ------------------------------------------------------------------ */
static void check_cr(double x, const char *what)
{
    double d = 0.0;
    int verdict;
    srmech_status_t st = srmech_rational_sqrt(x, &d);
    if (st != SRMECH_OK) {
        g_failed++;
        printf("  FAIL  %s: srmech_rational_sqrt refused, status=%d\n",
               what, (int)st);
        return;
    }
    verdict = is_correctly_rounded(x, d);
    if (verdict == 1) { g_passed++; return; }
    if (verdict < 0) {
        g_skipped++;
        printf("  SKIP  %s: outside the 128-bit certificate window\n", what);
        return;
    }
    g_failed++;
    printf("  FAIL  %s: srmech_rational_sqrt(x=%016llx) -> %016llx, which is "
           "NOT the correctly rounded root\n", what,
           (unsigned long long)bits_of(x), (unsigned long long)bits_of(d));
}

static void check_pin(uint64_t xbits, uint64_t want, const char *what)
{
    double d = 0.0;
    srmech_status_t st = srmech_rational_sqrt(double_of(xbits), &d);
    if (st == SRMECH_OK && bits_of(d) == want) { g_passed++; return; }
    g_failed++;
    printf("  FAIL  %s: got status=%d value %016llx, want %016llx\n",
           what, (int)st, (unsigned long long)bits_of(d),
           (unsigned long long)want);
}

/* The NORMALISE step, as a property of the Q61 pair rather than of a value:
 * the root must never be narrower than 54 bits. At rc475 the minimum over this
 * very sweep was 28. */
static void check_root_width(double x, const char *what)
{
    int64_t root = 0, p = 0;
    unsigned bl = 0;
    uint64_t t;
    srmech_status_t st = srmech_sqrt_q61(x, &root, &p);
    if (st != SRMECH_OK || root <= 0) {
        g_failed++;
        printf("  FAIL  %s: srmech_sqrt_q61 status=%d root=%lld\n",
               what, (int)st, (long long)root);
        return;
    }
    t = (uint64_t)root;
    while (t != 0u) { t >>= 1; bl++; }
    if (bl >= 54u && bl <= 56u) { g_passed++; return; }
    g_failed++;
    printf("  FAIL  %s: srmech_sqrt_q61 root is %u bits wide (want 54..56)\n",
           what, bl);
}

/* The two exports must agree: the double must be the projection of the pair.
 * Two different pairs can project to the same double, so this is the stronger
 * claim and it is the one the Python glue depends on. */
static void check_pair_projects(double x, const char *what)
{
    double d = 0.0;
    int64_t root = 0, p = 0;
    srmech_status_t sd = srmech_rational_sqrt(x, &d);
    srmech_status_t sp = srmech_sqrt_q61(x, &root, &p);
    uint64_t m = 0u;
    int32_t f = 0;
    int shift;
    u128 lhs, rhs;
    int ok = 0;
    if (sd != SRMECH_OK || sp != SRMECH_OK || root <= 0) {
        g_failed++;
        printf("  FAIL  %s: statuses %d / %d\n", what, (int)sd, (int)sp);
        return;
    }
    if (!decompose(d, &m, &f)) { g_skipped++; return; }
    /* The projection rounds to nearest, so the double and the pair must agree
     * to within half an ulp of the double:
     *     (2m-1)*2^(f-1)  <=  root*2^p  <=  (2m+1)*2^(f-1).
     * Divide through by 2^(f-1): root*2^(p-f+1) must lie in [2m-1, 2m+1]. The
     * shift is NEGATIVE for most rows (the pair is finer than the double), so
     * it is applied to whichever side keeps both integers. A first draft
     * skipped every negative shift and reported 1992 skips — a gate that was
     * measuring the pins and almost nothing else. */
    shift = (int)p - (int)f + 1;
    if (shift > 8 || shift < -8) { g_skipped++; return; }
    if (shift >= 0) {
        lhs = u128_shl((uint64_t)root, (unsigned)shift, &ok);
        if (!ok) { g_skipped++; return; }
        rhs = u128_shl(2u * m + 1u, 0u, &ok);
        if (u128_cmp(lhs, rhs) > 0) {
            g_failed++;
            printf("  FAIL  %s: the pair is ABOVE the double's upper midpoint\n",
                   what);
            return;
        }
        rhs = u128_shl(2u * m - 1u, 0u, &ok);
        if (u128_cmp(lhs, rhs) < 0) {
            g_failed++;
            printf("  FAIL  %s: the pair is BELOW the double's lower midpoint\n",
                   what);
            return;
        }
        g_passed++;
        return;
    }
    lhs = u128_shl((uint64_t)root, 0u, &ok);
    rhs = u128_shl(2u * m + 1u, (unsigned)(-shift), &ok);
    if (!ok) { g_skipped++; return; }
    if (u128_cmp(lhs, rhs) > 0) {
        g_failed++;
        printf("  FAIL  %s: the pair is ABOVE the double's upper midpoint\n", what);
        return;
    }
    rhs = u128_shl(2u * m - 1u, (unsigned)(-shift), &ok);
    if (u128_cmp(lhs, rhs) < 0) {
        g_failed++;
        printf("  FAIL  %s: the pair is BELOW the double's lower midpoint\n", what);
        return;
    }
    g_passed++;
}

/* The certificate must be able to FAIL, or every row above is a tautology. */
static void check_certificate_can_fail(void)
{
    double d = 0.0;
    srmech_status_t st = srmech_rational_sqrt(2.0, &d);
    uint64_t b = bits_of(d);
    if (st != SRMECH_OK) {
        g_failed++;
        printf("  FAIL  can-fail control: sqrt(2.0) refused\n");
        return;
    }
    if (is_correctly_rounded(2.0, d) != 1) {
        g_failed++;
        printf("  FAIL  can-fail control: the certificate rejects the true "
               "CR(sqrt 2)\n");
        return;
    }
    if (is_correctly_rounded(2.0, double_of(b + 1u)) != 0) {
        g_failed++;
        printf("  FAIL  can-fail control: the certificate ACCEPTED the "
               "neighbour ABOVE CR(sqrt 2)\n");
        return;
    }
    if (is_correctly_rounded(2.0, double_of(b - 1u)) != 0) {
        g_failed++;
        printf("  FAIL  can-fail control: the certificate ACCEPTED the "
               "neighbour BELOW CR(sqrt 2)\n");
        return;
    }
    g_passed++;
}

/* The refusal preamble rc473 repaired must be untouched by rc476. */
static void check_refusals(void)
{
    double d = 1.0;
    uint64_t nan_bits = UINT64_C(0x7FF8000000000000);
    double nan_v = double_of(nan_bits);
    double inf_v = double_of(UINT64_C(0x7FF0000000000000));
    srmech_status_t st;
    int64_t root = 1, p = 1;

    st = srmech_rational_sqrt(nan_v, &d);
    if (st == SRMECH_OK || d == d) {
        g_failed++;
        printf("  FAIL  srmech_rational_sqrt(NaN) must refuse AND write NaN\n");
    } else { g_passed++; }

    d = 1.0;
    st = srmech_rational_sqrt(-4.0, &d);
    if (st == SRMECH_OK || d == d) {
        g_failed++;
        printf("  FAIL  srmech_rational_sqrt(-4.0) must refuse AND write NaN\n");
    } else { g_passed++; }

    d = 1.0;
    st = srmech_rational_sqrt(inf_v, &d);
    if (st != SRMECH_OK || !(d > 0.0) || d == 0.0 || d != inf_v) {
        g_failed++;
        printf("  FAIL  srmech_rational_sqrt(+Inf) must serve +Inf\n");
    } else { g_passed++; }

    d = 1.0;
    st = srmech_rational_sqrt(0.0, &d);
    if (st != SRMECH_OK || d != 0.0) {
        g_failed++;
        printf("  FAIL  srmech_rational_sqrt(0.0) must serve 0.0\n");
    } else { g_passed++; }

    st = srmech_sqrt_q61(inf_v, &root, &p);
    if (st == SRMECH_OK || root != 0 || p != 0) {
        g_failed++;
        printf("  FAIL  srmech_sqrt_q61(+Inf) must refuse and zero the pair\n");
    } else { g_passed++; }
}

int main(void)
{
    /* The anchors, PINNED. Without these the sweep could be satisfied by a
     * certificate that skipped everything. */
    static const struct { uint64_t x; uint64_t want; const char *name; } pins[] = {
        { UINT64_C(0x4000000000000000), UINT64_C(0x3ff6a09e667f3bcd), "sqrt(2.0)" },
        { UINT64_C(0x4008000000000000), UINT64_C(0x3ffbb67ae8584caa), "sqrt(3.0)" },
        { UINT64_C(0x3fe8000000000000), UINT64_C(0x3febb67ae8584caa), "sqrt(0.75)" },
        { UINT64_C(0x3ff0000000000000), UINT64_C(0x3ff0000000000000), "sqrt(1.0)" },
        { UINT64_C(0x4010000000000000), UINT64_C(0x4000000000000000), "sqrt(4.0)" },
        { UINT64_C(0x0000000000000001), UINT64_C(0x1e60000000000000), "min subnormal" },
        { UINT64_C(0x000fffffffffffff), UINT64_C(0x1fffffffffffffff), "max subnormal" },
        { UINT64_C(0x0010000000000000), UINT64_C(0x2000000000000000), "min normal" },
        { UINT64_C(0x7fefffffffffffff), UINT64_C(0x5fefffffffffffff), "max double" },
    };
    size_t i;
    uint64_t mant;
    char name[64];

    printf("srmech sqrt correct-rounding gate (rc476, `#T1188`)\n");

    check_certificate_can_fail();
    check_refusals();

    for (i = 0; i < sizeof pins / sizeof pins[0]; i++) {
        check_pin(pins[i].x, pins[i].want, pins[i].name);
        check_cr(double_of(pins[i].x), pins[i].name);
        check_root_width(double_of(pins[i].x), pins[i].name);
        check_pair_projects(double_of(pins[i].x), pins[i].name);
    }

    /* EVERY subnormal mantissa 1..4096 — the class that was 4032/4096 wrong. */
    for (mant = 1u; mant <= 4096u; mant++) {
        double x = double_of(mant);
        snprintf(name, sizeof name, "subnormal mantissa %llu",
                 (unsigned long long)mant);
        check_cr(x, name);
        check_root_width(x, name);
    }

    /* The integers 2..2000 — the class that was 480/1956 one ulp low. */
    for (mant = 2u; mant <= 2000u; mant++) {
        double x = (double)mant;
        snprintf(name, sizeof name, "integer %llu", (unsigned long long)mant);
        check_cr(x, name);
        check_root_width(x, name);
        check_pair_projects(x, name);
    }

    /* The subnormal power-of-two classes, where the old root was narrowest. */
    for (i = 1; i < 52; i++) {
        uint64_t base = UINT64_C(1) << i;
        uint64_t probe[3];
        size_t j;
        probe[0] = base - 1u;
        probe[1] = base;
        probe[2] = base + 1u;
        for (j = 0; j < 3u; j++) {
            if (probe[j] == 0u || probe[j] >= (UINT64_C(1) << 52)) { continue; }
            snprintf(name, sizeof name, "subnormal 2^%u%+d",
                     (unsigned)i, (int)j - 1);
            check_cr(double_of(probe[j]), name);
            check_root_width(double_of(probe[j]), name);
        }
    }

    printf("passed=%d failed=%d skipped=%d\n", g_passed, g_failed, g_skipped);
    if (g_passed < 10000) {
        printf("  FAIL  the sweep ran only %d rows — it is not measuring\n",
               g_passed);
        return 2;
    }
    return (g_failed == 0) ? 0 : 1;
}
