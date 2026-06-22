/*
 * test_srmech_bigexp.c — standalone C-HOST smoke for the BIGNUM-EXACT
 * Class-N transcendental Taylor truncations (srmech_bigexp.c).
 *
 * THE POINT (the standalone-complete mandate): a C-ONLY host — no Python,
 * no GMP, no libm, no malloc — computes the exact-rational exp/sin/cos/
 * log1p/atan partial sums + rational_pow over the caller-arena srmech_bigint,
 * with NO int64 ceiling (the int64/Q61 peers in srmech_rational.c cap; these
 * *_big variants reach Python's unbounded exact (num, den)). The Python
 * srmech.amsc.rational.* is the byte-parity oracle (checked by the ctypes
 * harness test_c_bignum_transcendentals_rc35.py); this smoke pins a handful
 * of worked closed-form cases INCLUDING a > 2^64 result.
 *
 * Build + run (Linux gcc / macOS clang), pedantic, warnings = errors:
 *   cc -std=c11 -Wall -Wextra -Wpedantic -Werror -I../include
 *      test_srmech_bigexp.c ../src/srmech_bigexp.c ../src/srmech_bigint.c
 *      -lm -o /tmp/bigexp && /tmp/bigexp
 *
 * Mirrors the assert+count house style of test_srmech_bigint.c (no
 * framework; exits 0 on all-pass, non-zero on first fail).
 */

#include "srmech.h"

#include <stdint.h>
#include <stdio.h>
#include <string.h>

static int g_passed = 0;
static int g_failed = 0;

#define CAP 256
static uint32_t g_ws[400000]; /* shared caller arena (bytes via sizeof) */
static uint32_t g_dec_ws[8192];

static srmech_bigint_t bi_make(uint32_t *buf)
{
    srmech_bigint_t b;
    b.sign = 0;
    b.n = 0;
    b.cap = CAP;
    b.limbs = buf;
    return b;
}

static void set_dec(srmech_bigint_t *b, const char *s)
{
    srmech_status_t st = srmech_bigint_from_dec(b, s, strlen(s));
    if (st != SRMECH_OK) {
        g_failed++;
        printf("FAIL from_dec(%s) status %d\n", s, (int)st);
    }
}

/* Compare a bigint's decimal expansion to `want`. */
static void check_dec(const srmech_bigint_t *v, const char *want,
                      const char *desc)
{
    char buf[2048];
    size_t olen = 0;
    srmech_status_t st = srmech_bigint_to_dec(v, buf, sizeof(buf), &olen,
                                              g_dec_ws, sizeof(g_dec_ws));
    if (st != SRMECH_OK) {
        g_failed++;
        printf("FAIL %s: to_dec status %d\n", desc, (int)st);
        return;
    }
    if (strcmp(buf, want) == 0) {
        g_passed++;
    } else {
        g_failed++;
        printf("FAIL %s: got %s want %s\n", desc, buf, want);
    }
}

/* Run one *_big op on p/q with N terms, asserting out_num/out_den decimals. */
static void check_series(srmech_status_t (*fn)(const srmech_bigint_t *,
                                               const srmech_bigint_t *,
                                               uint32_t,
                                               srmech_bigint_t *,
                                               srmech_bigint_t *,
                                               void *, size_t),
                         const char *p_dec, const char *q_dec, uint32_t N,
                         const char *want_num, const char *want_den,
                         const char *desc)
{
    uint32_t pb[CAP], qb[CAP], onb[CAP], odb[CAP];
    srmech_bigint_t p = bi_make(pb), q = bi_make(qb);
    srmech_bigint_t on = bi_make(onb), od = bi_make(odb);
    srmech_status_t st;
    set_dec(&p, p_dec);
    set_dec(&q, q_dec);
    st = fn(&p, &q, N, &on, &od, g_ws, sizeof(g_ws));
    if (st != SRMECH_OK) {
        g_failed++;
        printf("FAIL %s: op status %d\n", desc, (int)st);
        return;
    }
    check_dec(&on, want_num, desc);
    check_dec(&od, want_den, desc);
}

int main(void)
{
    /* exp(1) to 10 terms: 9864101 / 3628800 (Python oracle). */
    check_series(srmech_exp_series_truncate_big, "1", "1", 10,
                 "9864101", "3628800", "exp(1,N=10)");

    /* exp(-5/2, N=1) = -3/2 — the sign keystone (divmod-alias regression). */
    check_series(srmech_exp_series_truncate_big, "-5", "2", 1,
                 "-3", "2", "exp(-5/2,N=1)");

    /* exp(0) = 1/1; cos(0) = 1/1; sin(0) = 0/1. */
    check_series(srmech_exp_series_truncate_big, "0", "1", 5,
                 "1", "1", "exp(0)");
    check_series(srmech_cos_series_truncate_big, "0", "1", 5,
                 "1", "1", "cos(0)");
    check_series(srmech_sin_series_truncate_big, "0", "1", 5,
                 "0", "1", "sin(0)");

    /* >2^64 KEYSTONE: exp(7/3, N=30). The exact numerator is ~148 bits
     * (45 decimal digits) — past int64; the C bignum reproduces Python's
     * exact (num, den). Values from srmech.amsc.rational.exp_series_truncate
     * (the committed oracle). */
    check_series(srmech_exp_series_truncate_big, "7", "3", 30,
                 "234562913613891831711238053208463597460789469",
                 "22746027321147539521562682531140075520000000",
                 "exp(7/3,N=30) [>2^64]");

    /* atan(1), k=0..3: 1 - 1/3 + 1/5 - 1/7 = 76/105. */
    check_series(srmech_atan_series_truncate_big, "1", "1", 3,
                 "76", "105", "atan(1,N=3)");

    /* log1p(1), k=1..3: 1 - 1/2 + 1/3 = 5/6. */
    check_series(srmech_log1p_series_truncate_big, "1", "1", 3,
                 "5", "6", "log1p(1,N=3)");

    /* (2/3)^10 = 1024 / 59049. */
    {
        uint32_t pb[CAP], qb[CAP], onb[CAP], odb[CAP];
        srmech_bigint_t p = bi_make(pb), q = bi_make(qb);
        srmech_bigint_t on = bi_make(onb), od = bi_make(odb);
        srmech_status_t st;
        set_dec(&p, "2");
        set_dec(&q, "3");
        st = srmech_rational_pow_uint_big(&p, &q, 10, &on, &od,
                                          g_ws, sizeof(g_ws));
        if (st != SRMECH_OK) {
            g_failed++;
            printf("FAIL pow(2/3,10): status %d\n", (int)st);
        } else {
            check_dec(&on, "1024", "pow(2/3,10) num");
            check_dec(&od, "59049", "pow(2/3,10) den");
        }
    }

    /* Domain refusals (match Python ValueError): atan(2/1) and log1p(2/1). */
    {
        uint32_t pb[CAP], qb[CAP], onb[CAP], odb[CAP];
        srmech_bigint_t p = bi_make(pb), q = bi_make(qb);
        srmech_bigint_t on = bi_make(onb), od = bi_make(odb);
        set_dec(&p, "2");
        set_dec(&q, "1");
        if (srmech_atan_series_truncate_big(&p, &q, 5, &on, &od,
                                            g_ws, sizeof(g_ws))
            == SRMECH_ERR_BAD_INPUT) {
            g_passed++;
        } else {
            g_failed++;
            printf("FAIL atan(2/1) should be BAD_INPUT (|x|>1)\n");
        }
        if (srmech_log1p_series_truncate_big(&p, &q, 5, &on, &od,
                                             g_ws, sizeof(g_ws))
            == SRMECH_ERR_BAD_INPUT) {
            g_passed++;
        } else {
            g_failed++;
            printf("FAIL log1p(2/1) should be BAD_INPUT (x>1)\n");
        }
    }

    printf("test_srmech_bigexp: %d passed, %d failed\n", g_passed, g_failed);
    return g_failed == 0 ? 0 : 1;
}
