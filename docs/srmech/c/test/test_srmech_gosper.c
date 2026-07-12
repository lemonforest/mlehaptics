/*
 * test_srmech_gosper.c -- standalone smoke test for srmech_gosper (rc41).
 *
 * Validates Gosper's indefinite summation certificate against CONCRETE term
 * values for the four rc41 acceptance cases:
 *   t(k)=k          (ratio (k+1)/k)        -> R=(k-1)/2, sum_{0..n-1} k = n(n-1)/2
 *   t(k)=k*k!       (ratio (k+1)^2/k)       -> R=1/k,     sum_{0..n-1} k*k! = n!-1
 *   t(k)=1/k harmonic (ratio k/(k+1))       -> NO SOLUTION (the negative test)
 *   t(k)=1/(k(k+1)) (ratio k/(k+2))         -> R=-(k+1),  telescopes to -1/k
 *
 * Build (WSL / POSIX):
 *   gcc -std=c11 -Wall -Wextra -Werror -pedantic -Ic/include
 *       c/test/test_srmech_gosper.c c/src/[s]rmech_*.c -lm -o /tmp/gosper_smoke
 *
 * Each certificate is cross-checked by EVALUATING R(k) and the term values at
 * integers (rational arithmetic via int64 fractions; the test inputs stay small),
 * never trusting the algorithm symbolically.
 */

#include "srmech.h"

#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static int g_fail = 0;
static int g_pass = 0;

#define CHECK(cond, msg) do { \
    if (cond) { g_pass++; } \
    else { g_fail++; printf("  FAIL: %s\n", (msg)); } \
} while (0)

/* ---- a tiny int64 rational helper for the cross-checks (test-side only) ---- */
typedef struct { int64_t num, den; } frac_t;

static int64_t igcd(int64_t a, int64_t b)
{
    if (a < 0) { a = -a; }
    if (b < 0) { b = -b; }
    while (b != 0) { int64_t t = a % b; a = b; b = t; }
    return a == 0 ? 1 : a;
}

static frac_t fmk(int64_t n, int64_t d)
{
    frac_t r;
    int64_t g;
    if (d < 0) { n = -n; d = -d; }
    g = igcd(n, d);
    r.num = n / g; r.den = d / g;
    return r;
}

static frac_t fadd(frac_t a, frac_t b)
{
    return fmk(a.num * b.den + b.num * a.den, a.den * b.den);
}

static frac_t fmul(frac_t a, frac_t b)
{
    return fmk(a.num * b.num, a.den * b.den);
}

static int feq(frac_t a, frac_t b)
{
    return a.num == b.num && a.den == b.den;
}

/* ---- srmech_bigint poly marshalling for the test ---- */

/* A small fixed-cap bigint allocator (test-side; the op is the thing under test). */
#define TCAP 64u
static uint32_t g_limbs[4096][TCAP];
static size_t g_limb_used = 0u;

static void bset(srmech_bigint_t *b, int64_t v)
{
    assert(g_limb_used < 4096u);
    b->limbs = g_limbs[g_limb_used++];
    b->cap = TCAP;
    b->n = 0;
    b->sign = 0;
    srmech_bigint_set_i64(b, v);
}

/* build a poly from int coefficients (ascending). den all 1. */
static void poly_from_ints(srmech_bigint_t *pn, srmech_bigint_t *pd,
                           const int64_t *coeffs, size_t n)
{
    size_t i;
    for (i = 0u; i < n; i++) {
        bset(&pn[i], coeffs[i]);
        bset(&pd[i], 1);
    }
}

/* evaluate a (num,den) poly at integer x -> frac_t (test-side Horner). */
static frac_t poly_eval_int(const srmech_bigint_t *pn, const srmech_bigint_t *pd,
                            size_t n, int64_t x)
{
    frac_t acc = fmk(0, 1);
    size_t k;
    for (k = n; k > 0u; k--) {
        frac_t coeff;
        int64_t cn, cd;
        cn = (pn[k - 1u].n == 0u) ? 0 : (int64_t)pn[k - 1u].limbs[0];
        if (pn[k - 1u].sign < 0) { cn = -cn; }
        cd = (pd[k - 1u].n == 0u) ? 1 : (int64_t)pd[k - 1u].limbs[0];
        coeff = fmk(cn, cd);
        acc = fadd(fmul(acc, fmk(x, 1)), coeff);
    }
    return acc;
}

static unsigned char g_ws[8u * 1024u * 1024u];

/* Run gosper for the term ratio num/den (int coeffs) and return the certificate
 * arrays + has_solution. */
static int run_gosper(const int64_t *num, size_t nn, const int64_t *den, size_t nd,
                      int *has, srmech_bigint_t *rn_n, srmech_bigint_t *rn_d,
                      size_t *lrn, srmech_bigint_t *rd_n, srmech_bigint_t *rd_d,
                      size_t *lrd)
{
    static srmech_bigint_t numn[16], numd[16], denn[16], dend[16];
    size_t i, deg = (nn > nd) ? nn : nd;
    srmech_status_t st;
    g_limb_used = 0u;
    poly_from_ints(numn, numd, num, nn);
    poly_from_ints(denn, dend, den, nd);
    /* size the out arrays */
    for (i = 0u; i < deg + 2u; i++) {
        bset(&rn_n[i], 0); bset(&rn_d[i], 1);
        bset(&rd_n[i], 0); bset(&rd_d[i], 1);
    }
    st = srmech_gosper(numn, numd, nn, denn, dend, nd, has,
                       rn_n, rn_d, lrn, rd_n, rd_d, lrd,
                       g_ws, sizeof(g_ws));
    return (int)st;
}

/* The R(k) value as a frac (from the cert arrays). */
static frac_t cert_eval(const srmech_bigint_t *rn_n, const srmech_bigint_t *rn_d,
                        size_t lrn, const srmech_bigint_t *rd_n,
                        const srmech_bigint_t *rd_d, size_t lrd, int64_t k)
{
    frac_t num = poly_eval_int(rn_n, rn_d, lrn, k);
    frac_t den = poly_eval_int(rd_n, rd_d, lrd, k);
    return fmk(num.num * den.den, num.den * den.num);
}

static int64_t ifact(int64_t k)
{
    int64_t r = 1, i;
    for (i = 2; i <= k; i++) { r *= i; }
    return r;
}

int main(void)
{
    static srmech_bigint_t rn_n[16], rn_d[16], rd_n[16], rd_d[16];
    size_t lrn, lrd;
    int has, rc, n;

    printf("srmech_gosper smoke test (rc41)\n");

    /* Case 1: t(k)=k, ratio (k+1)/k. sum_{0..n-1} k = n(n-1)/2; T(k)=R(k)*t(k). */
    {
        int64_t num[] = {1, 1};   /* k+1 */
        int64_t den[] = {0, 1};   /* k   */
        rc = run_gosper(num, 2, den, 2, &has, rn_n, rn_d, &lrn, rd_n, rd_d, &lrd);
        CHECK(rc == SRMECH_OK, "case1 status OK");
        CHECK(has == 1, "case1 has solution");
        if (has) {
            int ok = 1;
            for (n = 1; n <= 7; n++) {
                frac_t S = fmk(0, 1);
                int k;
                frac_t Tn, T0, diff;
                for (k = 0; k < n; k++) { S = fadd(S, fmk(k, 1)); }
                Tn = fmul(cert_eval(rn_n, rn_d, lrn, rd_n, rd_d, lrd, n), fmk(n, 1));
                T0 = fmul(cert_eval(rn_n, rn_d, lrn, rd_n, rd_d, lrd, 0), fmk(0, 1));
                diff = fadd(Tn, fmk(-T0.num, T0.den));
                if (!feq(S, diff) || !feq(S, fmk((int64_t)n * (n - 1), 2))) { ok = 0; }
            }
            CHECK(ok, "case1 sum_{0..n-1} k == T(n)-T(0) == n(n-1)/2");
        }
    }

    /* Case 2: t(k)=k*k!, ratio (k+1)^2/k. sum_{0..n-1} = n!-1. T(k)=k! (R=1/k). */
    {
        int64_t num[] = {1, 2, 1};  /* (k+1)^2 = k^2+2k+1 */
        int64_t den[] = {0, 1};     /* k */
        rc = run_gosper(num, 3, den, 2, &has, rn_n, rn_d, &lrn, rd_n, rd_d, &lrd);
        CHECK(rc == SRMECH_OK, "case2 status OK");
        CHECK(has == 1, "case2 has solution");
        if (has) {
            /* concrete sum check: sum_{0..n-1} k*k! == n!-1 (term values, no pole) */
            int ok = 1;
            for (n = 1; n <= 7; n++) {
                int64_t S = 0, k;
                for (k = 0; k < n; k++) { S += k * ifact(k); }
                if (S != ifact(n) - 1) { ok = 0; }
            }
            CHECK(ok, "case2 sum_{0..n-1} k*k! == n!-1 (concrete)");
            /* Gosper identity R(k+1)*num(k)/den(k) - R(k) == 1 (pole-free) */
            ok = 1;
            for (n = 1; n <= 6; n++) {
                frac_t Rk1 = cert_eval(rn_n, rn_d, lrn, rd_n, rd_d, lrd, n + 1);
                frac_t Rk = cert_eval(rn_n, rn_d, lrn, rd_n, rd_d, lrd, n);
                frac_t ratio = fmk(((int64_t)(n + 1)) * (n + 1), n);  /* (k+1)^2/k */
                frac_t lhs = fadd(fmul(Rk1, ratio), fmk(-Rk.num, Rk.den));
                if (!feq(lhs, fmk(1, 1))) { ok = 0; }
            }
            CHECK(ok, "case2 Gosper identity R(k+1)*(k+1)^2/k - R(k) == 1");
        }
    }

    /* Case 3: harmonic t(k)=1/k, ratio k/(k+1) -> NO SOLUTION. */
    {
        int64_t num[] = {0, 1};   /* k */
        int64_t den[] = {1, 1};   /* k+1 */
        rc = run_gosper(num, 2, den, 2, &has, rn_n, rn_d, &lrn, rd_n, rd_d, &lrd);
        CHECK(rc == SRMECH_OK, "case3 status OK");
        CHECK(has == 0, "case3 harmonic -> NO solution");
    }

    /* Case 4: t(k)=1/(k(k+1)), ratio k/(k+2). telescopes to -1/k. */
    {
        int64_t num[] = {0, 1};   /* k */
        int64_t den[] = {2, 1};   /* k+2 */
        rc = run_gosper(num, 2, den, 2, &has, rn_n, rn_d, &lrn, rd_n, rd_d, &lrd);
        CHECK(rc == SRMECH_OK, "case4 status OK");
        CHECK(has == 1, "case4 has solution");
        if (has) {
            /* t(k)=1/(k(k+1)); sum_{k=1..n} = n/(n+1) = T(n+1)-T(1) */
            int ok = 1;
            for (n = 1; n <= 7; n++) {
                frac_t S = fmk(0, 1);
                int k;
                frac_t Tn1, T1, diff;
                for (k = 1; k <= n; k++) { S = fadd(S, fmk(1, (int64_t)k * (k + 1))); }
                Tn1 = fmul(cert_eval(rn_n, rn_d, lrn, rd_n, rd_d, lrd, n + 1),
                           fmk(1, (int64_t)(n + 1) * (n + 2)));
                T1 = fmul(cert_eval(rn_n, rn_d, lrn, rd_n, rd_d, lrd, 1), fmk(1, 2));
                diff = fadd(Tn1, fmk(-T1.num, T1.den));
                if (!feq(S, diff) || !feq(S, fmk(n, n + 1))) { ok = 0; }
            }
            CHECK(ok, "case4 telescopes: sum_{1..n}==T(n+1)-T(1)==n/(n+1)");
        }
    }

    printf("\n%d passed, %d failed\n", g_pass, g_fail);
    return g_fail == 0 ? 0 : 1;
}
