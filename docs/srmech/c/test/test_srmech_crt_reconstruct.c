/*
 * test_srmech_crt_reconstruct.c -- standalone smoke for srmech_crt_combine +
 * srmech_rational_reconstruct (srmech 0.9.0rc45, rung 2 of the CRT-QMat
 * re-fibration arc).
 *
 * crt_combine is cross-checked by asserting residue % m_i == r_i for every
 * prime AND the combined modulus decimal == the independently-computed product.
 * rational_reconstruct is cross-checked by a round-trip: pick a known p/q, form
 * residue = (p * q^-1) mod M, reconstruct, assert it recovers (p, q); plus a
 * deliberate out-of-bound case that must return found == 0.
 *
 * Build (WSL / POSIX), Release to match the CI pedantic cell (NDEBUG strips
 * assert(), so any assert-only param would warn -Werror=unused-parameter):
 *   gcc -std=c11 -O2 -DNDEBUG -Wall -Wextra -Werror -pedantic -Ic/include \
 *       c/test/test_srmech_crt_reconstruct.c c/src/srmech_crt_reconstruct.c \
 *       c/src/srmech_bigint.c -o /tmp/crt_smoke
 *   /tmp/crt_smoke            (exit 0 = all pass)
 */

#include "srmech.h"

#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static int g_pass = 0;
static int g_fail = 0;

#define CHECK(cond, msg) do { \
    if (cond) { g_pass++; } \
    else { g_fail++; printf("  FAIL: %s\n", (msg)); } \
} while (0)

#define CAP 512
static uint32_t g_ws[400000];
static uint32_t g_dec_ws[16384];

static srmech_bigint_t bi_make(uint32_t *buf)
{
    srmech_bigint_t b;
    b.sign = 0;
    b.n = 0u;
    b.cap = CAP;
    b.limbs = buf;
    return b;
}

static void bi_set_dec(srmech_bigint_t *b, const char *s)
{
    srmech_status_t st = srmech_bigint_from_dec(b, s, strlen(s));
    if (st != SRMECH_OK) {
        g_fail++;
        printf("  FAIL: from_dec(%s) status %d\n", s, (int)st);
    }
}

static int bi_eq_dec(const srmech_bigint_t *v, const char *want)
{
    char buf[4096];
    size_t olen = 0u;
    srmech_status_t st = srmech_bigint_to_dec(v, buf, sizeof(buf), &olen,
                                              g_dec_ws, sizeof(g_dec_ws));
    if (st != SRMECH_OK) {
        printf("  FAIL: to_dec status %d\n", (int)st);
        return 0;
    }
    return strcmp(buf, want) == 0;
}

/* read a small non-negative bigint back as uint64 (test residues stay small). */
static uint64_t bi_to_u64(const srmech_bigint_t *v)
{
    uint64_t r = 0u;
    if (v->n >= 1u) { r = (uint64_t)v->limbs[0]; }
    if (v->n >= 2u) { r |= ((uint64_t)v->limbs[1]) << 32; }
    return r;
}

/* ---- crt_combine ---- */
static void test_crt_combine(void)
{
    uint32_t rb[CAP], mb[CAP];
    srmech_bigint_t out_r = bi_make(rb);
    srmech_bigint_t out_m = bi_make(mb);
    /* three distinct primes; residues chosen, modulus = 2*3*5... use real
     * ~31-bit primes to exercise the >2^64 modulus. */
    const uint64_t primes[4] = {2147483647u, 2147483629u, 2147483587u,
                                2147483579u};
    const uint64_t resid[4]  = {12345u, 67890u, 13579u, 24680u};
    srmech_status_t st;
    uint32_t i;
    char want[256];
    /* independent product over a small bignum done by hand: print via the lib
     * out_modulus and re-derive by multiplying as long double is unsafe; instead
     * assert residue % p == r % p for every prime and modulus divisibility. */
    st = srmech_crt_combine(resid, primes, 4u, &out_r, &out_m,
                            g_ws, sizeof(g_ws));
    CHECK(st == SRMECH_OK, "crt_combine status OK");
    /* modulus = 2147483647 * 2147483629 * 2147483587 * 2147483579
     *         = 21267646447030638312596530828283033699 (computed in Python). */
    strcpy(want, "21267646447030638312596530828283033699");
    CHECK(bi_eq_dec(&out_m, want), "crt_combine modulus == product");
    /* combined residue (Python CRT oracle). */
    CHECK(bi_eq_dec(&out_r, "20231506489026670404249431641792729451"),
          "crt_combine residue == oracle");
    /* residue % p_i == resid_i for each prime: reduce out_r by each prime using
     * divmod against a small bigint. */
    for (i = 0u; i < 4u; i++) {
        uint32_t pb[CAP], remb[CAP], qb[CAP];
        srmech_bigint_t pbi = bi_make(pb);
        srmech_bigint_t rem = bi_make(remb);
        srmech_bigint_t quo = bi_make(qb);
        uint64_t got;
        st = srmech_bigint_set_i64(&pbi, (int64_t)primes[i]);
        CHECK(st == SRMECH_OK, "set prime");
        st = srmech_bigint_divmod(&quo, &rem, &out_r, &pbi,
                                  g_ws, sizeof(g_ws));
        CHECK(st == SRMECH_OK, "divmod residue%p");
        got = bi_to_u64(&rem);
        CHECK(got == resid[i] % primes[i], "residue % p_i == r_i");
    }
}

/* ---- rational_reconstruct round-trip ---- *
 * Use the same 4-prime modulus. Pick p/q small enough to satisfy the Wang
 * bound, compute residue = (p * q^-1) mod M, reconstruct, assert (p, q). */
static void test_rational_reconstruct(void)
{
    /* M = product above. Reconstruct 355/113 (the Archimedes pi convergent).
     * The residue is computed in Python and hard-coded so this stays an
     * INDEPENDENT oracle (the test never asks the library to also compute it).
     *   M   = 21267646447030638312596530828283033699
     *   res = (355 * inverse(113, M)) % M
     *       = 1505674084745531915936037580763400619  (Python pow(113,-1,M)). */
    uint32_t mb[CAP], resb[CAP], nbb[CAP], dbb[CAP], onb[CAP], odb[CAP];
    srmech_bigint_t modulus = bi_make(mb);
    srmech_bigint_t residue = bi_make(resb);
    srmech_bigint_t num_b = bi_make(nbb);
    srmech_bigint_t den_b = bi_make(dbb);
    srmech_bigint_t out_n = bi_make(onb);
    srmech_bigint_t out_d = bi_make(odb);
    int32_t found = 0;
    srmech_status_t st;
    bi_set_dec(&modulus, "21267646447030638312596530828283033699");
    bi_set_dec(&residue, "1505674084745531915936037580763400619");
    /* Wang bound: isqrt(M//2) ~ 3.26e18; use a generous symmetric bound 10^19. */
    bi_set_dec(&num_b, "10000000000000000000");
    bi_set_dec(&den_b, "10000000000000000000");
    st = srmech_rational_reconstruct(&residue, &modulus, &num_b, &den_b,
                                     &out_n, &out_d, &found,
                                     g_ws, sizeof(g_ws));
    CHECK(st == SRMECH_OK, "reconstruct status OK");
    CHECK(found == 1, "reconstruct found");
    CHECK(bi_eq_dec(&out_n, "355"), "reconstruct num == 355");
    CHECK(bi_eq_dec(&out_d, "113"), "reconstruct den == 113");

    /* Negative numerator: -355/113 -> residue = (-355 * inv(113)) % M
     *  = 19761972362285106396660493247519633080  (Python (-355*inv)%M). */
    {
        uint32_t resb2[CAP];
        srmech_bigint_t residue2 = bi_make(resb2);
        bi_set_dec(&residue2, "19761972362285106396660493247519633080");
        st = srmech_rational_reconstruct(&residue2, &modulus, &num_b, &den_b,
                                         &out_n, &out_d, &found,
                                         g_ws, sizeof(g_ws));
        CHECK(st == SRMECH_OK, "reconstruct(neg) status OK");
        CHECK(found == 1, "reconstruct(neg) found");
        CHECK(bi_eq_dec(&out_n, "-355"), "reconstruct num == -355");
        CHECK(bi_eq_dec(&out_d, "113"), "reconstruct den == 113");
    }

    /* Out-of-bound: tiny bounds (num<=2, den<=2) cannot represent 355/113. */
    {
        bi_set_dec(&num_b, "2");
        bi_set_dec(&den_b, "2");
        st = srmech_rational_reconstruct(&residue, &modulus, &num_b, &den_b,
                                         &out_n, &out_d, &found,
                                         g_ws, sizeof(g_ws));
        CHECK(st == SRMECH_OK, "reconstruct(oob) status OK");
        CHECK(found == 0, "reconstruct(oob) returns found == 0");
    }
}

int main(void)
{
    test_crt_combine();
    test_rational_reconstruct();
    printf("crt_reconstruct smoke: %d passed, %d failed\n", g_pass, g_fail);
    return g_fail == 0 ? 0 : 1;
}
