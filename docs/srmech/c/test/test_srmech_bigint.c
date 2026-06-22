/*
 * test_srmech_bigint.c — standalone C-HOST smoke for the caller-arena
 * arbitrary-precision integer (srmech_bigint.c).
 *
 * THE POINT (the standalone-complete mandate): a C-ONLY host — no Python,
 * no GMP, no libm, no malloc — does unbounded signed-integer arithmetic
 * via the srmech_bigint_* ops over caller-owned limb storage + caller
 * scratch arenas. Division / shift carry PYTHON FLOOR semantics so the C
 * result is byte-identical to Python's int (the ctypes byte-parity harness
 * test/_bi_harness.py checks that against a few hundred random ~2000-bit
 * signed integers; this smoke pins a handful of worked closed-form cases).
 *
 * Build + run (Linux gcc / macOS clang), pedantic, warnings = errors:
 *   cc -std=c11 -Wall -Wextra -Wpedantic -Werror -I../include \
 *      test_srmech_bigint.c ../src/srmech_bigint.c -o /tmp/bi && /tmp/bi
 *
 * Mirrors the assert+count house style of test_srmech_qi.c (no framework;
 * exits 0 on all-pass, non-zero on first fail).
 */

#include "srmech.h"

#include <stdint.h>
#include <stdio.h>
#include <string.h>

static int g_passed = 0;
static int g_failed = 0;

/* A fixed-capacity bigint backed by a local limb array (no malloc). */
#define CAP 64
static uint32_t g_ws[4096]; /* shared scratch arena for ops that need it */

static srmech_bigint_t bi_make(uint32_t *buf, uint32_t cap)
{
    srmech_bigint_t b;
    b.sign = 0;
    b.n = 0;
    b.cap = cap;
    b.limbs = buf;
    return b;
}

static void check_i64(int64_t got, int64_t want, const char *desc)
{
    if (got == want) {
        g_passed++;
    } else {
        g_failed++;
        printf("FAIL %s: got %lld want %lld\n", desc,
               (long long)got, (long long)want);
    }
}

static void check_status(srmech_status_t got, srmech_status_t want,
                         const char *desc)
{
    if (got == want) {
        g_passed++;
    } else {
        g_failed++;
        printf("FAIL %s: status got %d want %d\n", desc, (int)got, (int)want);
    }
}

static void check_dec(const srmech_bigint_t *v, const char *want,
                      const char *desc)
{
    char buf[1024];   /* wide enough for the 508-digit pow(7,600) keystone */
    size_t olen = 0;
    srmech_status_t st = srmech_bigint_to_dec(v, buf, sizeof(buf), &olen,
                                              g_ws, sizeof(g_ws));
    if (st != SRMECH_OK) {
        g_failed++;
        printf("FAIL %s: to_dec status %d\n", desc, (int)st);
        return;
    }
    if (strcmp(buf, want) == 0 && olen == strlen(want)) {
        g_passed++;
    } else {
        g_failed++;
        printf("FAIL %s: got \"%s\" want \"%s\"\n", desc, buf, want);
    }
}

/* Read the low 64 bits of a bigint as a signed value (for small checks). */
static int64_t bi_to_i64(const srmech_bigint_t *b)
{
    uint64_t mag = 0u;
    if (b->n >= 1u) { mag |= (uint64_t)b->limbs[0]; }
    if (b->n >= 2u) { mag |= ((uint64_t)b->limbs[1]) << 32; }
    return (b->sign < 0) ? -(int64_t)mag : (int64_t)mag;
}

int main(void)
{
    uint32_t ba[CAP], bb[CAP], bo[CAP], bq[CAP], br[CAP];
    srmech_bigint_t a = bi_make(ba, CAP);
    srmech_bigint_t b = bi_make(bb, CAP);
    srmech_bigint_t o = bi_make(bo, CAP);
    srmech_bigint_t q = bi_make(bq, CAP);
    srmech_bigint_t r = bi_make(br, CAP);

    /* set_i64 + to_dec round-trip on a few values. */
    check_status(srmech_bigint_set_i64(&a, 0), SRMECH_OK, "set 0");
    check_dec(&a, "0", "dec 0");
    check_status(srmech_bigint_set_i64(&a, -123456789012345LL), SRMECH_OK,
                 "set neg");
    check_dec(&a, "-123456789012345", "dec neg");

    /* add / sub / mul (signed). */
    srmech_bigint_set_i64(&a, 1000000000000LL);     /* 1e12 */
    srmech_bigint_set_i64(&b, -7);
    check_status(srmech_bigint_add(&o, &a, &b), SRMECH_OK, "add status");
    check_i64(bi_to_i64(&o), 999999999993LL, "add");
    check_status(srmech_bigint_sub(&o, &a, &b), SRMECH_OK, "sub status");
    check_i64(bi_to_i64(&o), 1000000000007LL, "sub");
    check_status(srmech_bigint_mul(&o, &a, &b), SRMECH_OK, "mul status");
    check_i64(bi_to_i64(&o), -7000000000000LL, "mul");

    /* Big multiply via decimal: 10^20 * 10^20 = 10^40. */
    {
        const char *p20 = "100000000000000000000";
        char want40[64];
        srmech_bigint_from_dec(&a, p20, strlen(p20));
        srmech_bigint_from_dec(&b, p20, strlen(p20));
        check_status(srmech_bigint_mul(&o, &a, &b), SRMECH_OK, "mul1e40 st");
        want40[0] = '1';
        for (int i = 1; i <= 40; i++) { want40[i] = '0'; }
        want40[41] = '\0';
        check_dec(&o, want40, "mul 1e40");
    }

    /* divmod FLOOR semantics: -7 / 2 -> q=-4, r=1 (Python). */
    srmech_bigint_set_i64(&a, -7);
    srmech_bigint_set_i64(&b, 2);
    check_status(srmech_bigint_divmod(&q, &r, &a, &b, g_ws, sizeof(g_ws)),
                 SRMECH_OK, "divmod st");
    check_i64(bi_to_i64(&q), -4, "divmod q (-7/2)");
    check_i64(bi_to_i64(&r), 1, "divmod r (-7/2)");

    /* 7 / -2 -> q=-4, r=-1 (Python floor). */
    srmech_bigint_set_i64(&a, 7);
    srmech_bigint_set_i64(&b, -2);
    srmech_bigint_divmod(&q, &r, &a, &b, g_ws, sizeof(g_ws));
    check_i64(bi_to_i64(&q), -4, "divmod q (7/-2)");
    check_i64(bi_to_i64(&r), -1, "divmod r (7/-2)");

    /* divide by zero -> BAD_INPUT. */
    srmech_bigint_set_i64(&b, 0);
    check_status(srmech_bigint_divmod(&q, &r, &a, &b, g_ws, sizeof(g_ws)),
                 SRMECH_ERR_BAD_INPUT, "div0");

    /* shl / shr (floor for negatives). */
    srmech_bigint_set_i64(&a, 1);
    check_status(srmech_bigint_shl_bits(&o, &a, 100), SRMECH_OK, "shl st");
    check_dec(&o, "1267650600228229401496703205376", "shl 1<<100");
    srmech_bigint_set_i64(&a, -5);
    check_status(srmech_bigint_shr_bits(&o, &a, 1), SRMECH_OK, "shr st");
    check_i64(bi_to_i64(&o), -3, "shr -5>>1 floor");

    /* isqrt: floor sqrt. */
    srmech_bigint_set_i64(&a, 1000000);
    check_status(srmech_bigint_isqrt(&o, &a, g_ws, sizeof(g_ws)), SRMECH_OK,
                 "isqrt st");
    check_i64(bi_to_i64(&o), 1000, "isqrt 1e6");
    srmech_bigint_set_i64(&a, 99);
    srmech_bigint_isqrt(&o, &a, g_ws, sizeof(g_ws));
    check_i64(bi_to_i64(&o), 9, "isqrt 99");
    srmech_bigint_set_i64(&a, -4);
    check_status(srmech_bigint_isqrt(&o, &a, g_ws, sizeof(g_ws)),
                 SRMECH_ERR_BAD_INPUT, "isqrt neg");

    /* gcd of magnitudes. */
    srmech_bigint_set_i64(&a, 1071);
    srmech_bigint_set_i64(&b, 462);
    check_status(srmech_bigint_gcd(&o, &a, &b, g_ws, sizeof(g_ws)), SRMECH_OK,
                 "gcd st");
    check_i64(bi_to_i64(&o), 21, "gcd(1071,462)");

    /* pow: 7^13 = 96889010407. */
    srmech_bigint_set_i64(&a, 7);
    check_status(srmech_bigint_pow_u32(&o, &a, 13, g_ws, sizeof(g_ws)),
                 SRMECH_OK, "pow st");
    check_i64(bi_to_i64(&o), 96889010407LL, "pow 7^13");
    /* exp 0 -> 1. */
    srmech_bigint_pow_u32(&o, &a, 0, g_ws, sizeof(g_ws));
    check_i64(bi_to_i64(&o), 1, "pow x^0");

    /* cmp + is_zero. */
    srmech_bigint_set_i64(&a, -5);
    srmech_bigint_set_i64(&b, 3);
    check_i64((int64_t)srmech_bigint_cmp(&a, &b), -1, "cmp -5<3");
    check_i64((int64_t)srmech_bigint_cmp(&b, &a), 1, "cmp 3>-5");
    srmech_bigint_set_i64(&a, 0);
    check_i64((int64_t)srmech_bigint_is_zero(&a), 1, "is_zero 0");
    srmech_bigint_set_i64(&a, 1);
    check_i64((int64_t)srmech_bigint_is_zero(&a), 0, "is_zero 1");

    /* OVERFLOW guard: undersized out for an add. */
    {
        uint32_t tiny[1];
        srmech_bigint_t small = bi_make(tiny, 1);
        srmech_bigint_set_i64(&a, 0xFFFFFFFFLL);
        srmech_bigint_set_i64(&b, 0xFFFFFFFFLL);
        check_status(srmech_bigint_add(&small, &a, &b), SRMECH_ERR_OVERFLOW,
                     "add overflow guard");
    }

    /* ---- pow_u32 (binary exponentiation; rc36 scratch-bound fix) ---- */
    {
        uint32_t pbuf[CAP], bbuf[CAP];
        srmech_bigint_t po = bi_make(pbuf, CAP);
        srmech_bigint_t pbase = bi_make(bbuf, CAP);
        const char *e7_600 =
            "11450488332310252629233198149569278478623259821197339943425315"
            "54985163223206633039966559241257609670429897350415891980768804"
            "12794575473190385665994943189876297213016525337351380678465872"
            "58862845654893027187626149138556374802011495367934064646250942"
            "44515365050120716031569341385478652988610315682341203592396495"
            "19684199242817038581483010718844282803408485904757788145768539"
            "82063120666404156531022348503937987859541449436932669286370821"
            "170080422597177518760544741277685436943552772412354198499053082"
            "75568360001";
        size_t pneed;
        srmech_bigint_set_i64(&pbase, 3);
        check_status(srmech_bigint_pow_u32(&po, &pbase, 5, g_ws, sizeof(g_ws)),
                     SRMECH_OK, "pow(3,5) st");
        check_dec(&po, "243", "pow(3,5)");
        srmech_bigint_set_i64(&pbase, 2);
        check_status(srmech_bigint_pow_u32(&po, &pbase, 64, g_ws, sizeof(g_ws)),
                     SRMECH_OK, "pow(2,64) st");
        check_dec(&po, "18446744073709551616", "pow(2,64)");
        check_status(srmech_bigint_pow_u32(&po, &pbase, 0, g_ws, sizeof(g_ws)),
                     SRMECH_OK, "pow(2,0) st");
        check_dec(&po, "1", "pow(2,0)");
        /* KEYSTONE: 7^600 = 53 limbs > the pre-rc36 internal cap
         * (base->n*32+4 = 36), which OVERFLOWED here; now byte-identical to
         * Python's 7**600 (a C-only host has the full magnitude). */
        srmech_bigint_set_i64(&pbase, 7);
        check_status(srmech_bigint_pow_u32(&po, &pbase, 600, g_ws, sizeof(g_ws)),
                     SRMECH_OK, "pow(7,600) st");
        check_dec(&po, e7_600, "pow(7,600) keystone");
        check_i64((int64_t)(po.n > 36u), 1, "pow(7,600) exceeds old 36-limb cap");
        /* the advertised ws bound is exactly sufficient (tight, no over-alloc) */
        pneed = srmech_bigint_pow_ws_bound(pbase.n, 600);
        check_status(srmech_bigint_pow_u32(&po, &pbase, 600, g_ws, pneed),
                     SRMECH_OK, "pow(7,600) via pow_ws_bound");
        check_dec(&po, e7_600, "pow(7,600) tight ws");
    }

    printf("test_srmech_bigint: %d passed, %d failed\n", g_passed, g_failed);
    return g_failed == 0 ? 0 : 1;
}
