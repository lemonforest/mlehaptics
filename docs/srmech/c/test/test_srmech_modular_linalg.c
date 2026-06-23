/*
 * test_srmech_modular_linalg.c -- standalone smoke for srmech_gf_rref +
 * srmech_next_prime (srmech 0.9.0rc44, rung 1 of the CRT-QMat re-fibration arc).
 *
 * srmech_gf_rref is cross-checked against an INDEPENDENT in-test GF(p) Gauss-
 * Jordan elimination (its own modular inverse via Fermat) -- never the library
 * against itself. srmech_next_prime is cross-checked against an independent
 * naive trial-division prime walk.
 *
 * Build (WSL / POSIX), Release to match the CI pedantic cell (NDEBUG strips
 * assert(), so any assert-only param would warn -Werror=unused-parameter):
 *   gcc -std=c11 -O2 -DNDEBUG -Wall -Wextra -Werror -pedantic -Ic/include \
 *       c/test/test_srmech_modular_linalg.c c/src/srmech_modular_linalg.c \
 *       c/src/srmech_primes.c c/src/srmech_cyclic.c -o /tmp/ml_smoke
 *   ./tmp/ml_smoke            (exit 0 = all pass)
 */

#include "srmech.h"

#include <assert.h>
#include <stdint.h>
#include <stdio.h>

static int g_fail = 0;
static int g_pass = 0;

#define CHECK(cond, msg) do { \
    if (cond) { g_pass++; } \
    else { g_fail++; printf("  FAIL: %s\n", (msg)); } \
} while (0)

/* ---- independent in-test GF(p) toolkit (no srmech) ---- */
static uint64_t t_inv(uint64_t a, uint64_t p)
{
    /* Fermat a^(p-2) mod p; p prime, a in [1, p). */
    uint64_t r = 1u, base = a % p, e = p - 2u;
    while (e != 0u) {
        if ((e & 1u) != 0u) { r = (r * base) % p; }
        base = (base * base) % p;
        e >>= 1;
    }
    return r;
}

/* Reduce a 64-bit signed value into [0, p). */
static uint64_t t_canon(int64_t v, uint64_t p)
{
    int64_t r = v % (int64_t)p;
    if (r < 0) { r += (int64_t)p; }
    return (uint64_t)r;
}

/* Independent GF(p) RREF into mat (row-major uint64), returns rank; writes
 * pivots[]. n_rows*n_cols <= caller buffer. */
static uint32_t t_gfp_rref(uint64_t *mat, uint32_t nr, uint32_t nc, uint64_t p,
                           uint32_t *pivots)
{
    uint32_t pr = 0u, col, r, c;
    for (col = 0u; col < nc && pr < nr; col++) {
        uint32_t sel = nr;
        for (r = pr; r < nr; r++) {
            if (mat[(uint64_t)r * nc + col] != 0u) { sel = r; break; }
        }
        if (sel == nr) { continue; }
        if (sel != pr) {
            for (c = 0u; c < nc; c++) {
                uint64_t tmp = mat[(uint64_t)pr * nc + c];
                mat[(uint64_t)pr * nc + c] = mat[(uint64_t)sel * nc + c];
                mat[(uint64_t)sel * nc + c] = tmp;
            }
        }
        uint64_t inv = t_inv(mat[(uint64_t)pr * nc + col], p);
        for (c = 0u; c < nc; c++) {
            mat[(uint64_t)pr * nc + c] = (mat[(uint64_t)pr * nc + c] * inv) % p;
        }
        for (r = 0u; r < nr; r++) {
            if (r == pr) { continue; }
            uint64_t f = mat[(uint64_t)r * nc + col];
            if (f == 0u) { continue; }
            for (c = 0u; c < nc; c++) {
                uint64_t s = (mat[(uint64_t)pr * nc + c] * f) % p;
                uint64_t d = mat[(uint64_t)r * nc + c];
                mat[(uint64_t)r * nc + c] = (d + (p - s)) % p;
            }
        }
        pivots[pr] = col;
        pr++;
    }
    return pr;
}

static int t_naive_prime(uint64_t x)
{
    uint64_t d;
    if (x < 2u) { return 0; }
    for (d = 2u; d <= x / d; d++) {
        if ((x % d) == 0u) { return 0; }
    }
    return 1;
}

/* ---- gf_rref test ---- */
#define MAXCELLS 4096u

static void run_gf_rref_case(const int64_t *in, uint32_t nr, uint32_t nc,
                             uint64_t p, const char *label)
{
    int64_t lib_mat[MAXCELLS];
    uint64_t orc_mat[MAXCELLS];
    uint32_t lib_piv[128], orc_piv[128];
    uint32_t lib_rank = 0u, orc_rank, i, total = nr * nc;
    srmech_status_t st;

    assert(total <= MAXCELLS);
    for (i = 0u; i < total; i++) {
        lib_mat[i] = in[i];
        orc_mat[i] = t_canon(in[i], p);
    }
    st = srmech_gf_rref(lib_mat, nr, nc, p, lib_piv, &lib_rank);
    CHECK(st == SRMECH_OK, label);
    orc_rank = t_gfp_rref(orc_mat, nr, nc, p, orc_piv);

    int ok = (lib_rank == orc_rank);
    for (i = 0u; ok && i < total; i++) {
        if ((uint64_t)lib_mat[i] != orc_mat[i]) { ok = 0; }
    }
    for (i = 0u; ok && i < lib_rank; i++) {
        if (lib_piv[i] != orc_piv[i]) { ok = 0; }
    }
    CHECK(ok, label);
}

static void test_gf_rref(void)
{
    /* A small full-rank system, a rank-deficient one (dup row), a system that
     * vanishes mod p, across several primes. */
    static const int64_t a[] = { 2, 4, 6, 1, 3, 5, 7, 0, 0, 0, 11, 13 };  /* 3x4 */
    static const int64_t b[] = { 1, 2, 3, 2, 4, 6, 5, 1, 0 };             /* 3x3 dup-ish */
    static const int64_t c[] = { 7, 14, 21, 0, 7, 0 };                    /* 2x3 zero mod 7 */
    static const int64_t neg[] = { -1, -2, 3, -4, 5, -6 };                /* 2x3 negatives */
    const uint64_t primes[] = { 3u, 5u, 7u, 101u, 65537u, 2147483647u };
    size_t pi;
    for (pi = 0u; pi < sizeof(primes) / sizeof(primes[0]); pi++) {
        run_gf_rref_case(a, 3u, 4u, primes[pi], "gf_rref 3x4");
        run_gf_rref_case(b, 3u, 3u, primes[pi], "gf_rref 3x3");
        run_gf_rref_case(c, 2u, 3u, primes[pi], "gf_rref 2x3 zero-mod-7");
        run_gf_rref_case(neg, 2u, 3u, primes[pi], "gf_rref 2x3 neg");
    }
    /* Bad-field guards: p <= 2 and p >= 2**31 rejected. (NULL-arg guards fire
     * an assert in a debug build before the return, so they are not smoke-tested
     * here -- the return-code contract is parity-tested from Python instead.) */
    {
        int64_t m[4] = { 1, 0, 0, 1 };
        uint32_t piv[2], rank = 0u;
        CHECK(srmech_gf_rref(m, 2u, 2u, 2u, piv, &rank) == SRMECH_ERR_BAD_INPUT,
              "gf_rref rejects p=2");
        CHECK(srmech_gf_rref(m, 2u, 2u, (1ull << 31), piv, &rank)
                  == SRMECH_ERR_BAD_INPUT,
              "gf_rref rejects p=2**31");
    }
}

static void test_next_prime(void)
{
    uint64_t n, out = 0u;
    srmech_status_t st;
    for (n = 0u; n < 300u; n++) {
        uint64_t exp = n + 1u;
        while (!t_naive_prime(exp)) { exp++; }
        st = srmech_next_prime(n, &out);
        CHECK(st == SRMECH_OK && out == exp, "next_prime small");
    }
    /* A few larger gaps + a known value. */
    {
        const uint64_t cases[][2] = {
            { 1000u, 1009u }, { 7918u, 7919u }, { 104728u, 104729u },
            { 2u, 3u }, { 1u, 2u }, { 0u, 2u },
        };
        size_t i;
        for (i = 0u; i < sizeof(cases) / sizeof(cases[0]); i++) {
            st = srmech_next_prime(cases[i][0], &out);
            CHECK(st == SRMECH_OK && out == cases[i][1], "next_prime known");
        }
    }
}

int main(void)
{
    printf("test_srmech_modular_linalg (gf_rref + next_prime)\n");
    test_gf_rref();
    test_next_prime();
    printf("  pass=%d fail=%d\n", g_pass, g_fail);
    return g_fail == 0 ? 0 : 1;
}
