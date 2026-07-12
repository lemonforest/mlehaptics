/*
 * test_srmech_wz.c -- standalone smoke test for srmech_wz_verify (rc43).
 *
 * Validates the Wilf-Zeilberger VERIFY primitive against CONCRETE WZ pairs for the
 * rc43 acceptance cases (each F normalized so Sum_k F(n,k) = const):
 *   F(n,k)=C(n,k)/2^n   (Sum=1) : R = -k/(2(n+1-k))
 *     r_n = (n+1)/(2(n+1-k)), r_k = (n-k)/(k+1)
 *   F(n,k)=C(n,k)^2/C(2n,n) (Sum=1; the WZ 1990 pair)
 *     r_n = (n+1)^3 / (2(2n+1)(n+1-k)^2), r_k = ((n-k)/(k+1))^2
 *
 * The WZ equation is checked TWO ways: (a) srmech_wz_verify returns *out_equal=1
 * for the true certificate AND 0 for a WRONG certificate (the +k sign flip); and
 * (b) the WZ equation F(n+1,k)-F(n,k) = G(n,k+1)-G(n,k), G=R*F, is cross-checked by
 * EVALUATING F and G as int64 fractions at concrete integer (n,k) -- never trusting
 * the algebra symbolically.
 *
 * Build (WSL / POSIX):
 *   gcc -std=c11 -Wall -Wextra -Werror -pedantic -Ic/include
 *       c/test/test_srmech_wz.c c/src/[s]rmech_*.c -lm -o /tmp/wz_smoke
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

/* ---- a tiny int64 rational helper (test-side only) ---- */
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
    frac_t r; int64_t g;
    if (d < 0) { n = -n; d = -d; }
    g = igcd(n, d); r.num = n / g; r.den = d / g; return r;
}
static frac_t fadd(frac_t a, frac_t b) { return fmk(a.num * b.den + b.num * a.den, a.den * b.den); }
static frac_t fsub(frac_t a, frac_t b) { return fmk(a.num * b.den - b.num * a.den, a.den * b.den); }
static frac_t fmul(frac_t a, frac_t b) { return fmk(a.num * b.num, a.den * b.den); }
static int feq(frac_t a, frac_t b) { return a.num == b.num && a.den == b.den; }

static int64_t comb_i(int64_t n, int64_t k)
{
    int64_t r = 1, i;
    if (k < 0 || k > n) { return 0; }
    if (k > n - k) { k = n - k; }
    for (i = 0; i < k; i++) { r = r * (n - i) / (i + 1); }
    return r;
}

/* ---- bigint pool + bipoly marshalling (test-side) ---- */
#define TCAP 96u
static uint32_t g_limbs[8192][TCAP];
static size_t g_used = 0u;

static void bset(srmech_bigint_t *b, int64_t v)
{
    assert(g_used < 8192u);
    b->limbs = g_limbs[g_used++];
    b->cap = TCAP; b->n = 0; b->sign = 0;
    srmech_bigint_set_i64(b, v);
}

typedef struct bi_in {
    srmech_bigint_t n[256], d[256];
    size_t klen[32];
    size_t kdeg;
} bi_in_t;

static void bi_build(bi_in_t *b, const int64_t *flat, const size_t *klen, size_t kdeg)
{
    size_t idx = 0u, dk, j;
    b->kdeg = kdeg;
    for (dk = 0u; dk < kdeg; dk++) {
        b->klen[dk] = klen[dk];
        for (j = 0u; j < klen[dk]; j++) {
            bset(&b->n[idx], flat[idx]);
            bset(&b->d[idx], 1);
            idx++;
        }
    }
}

static unsigned char g_ws[64u * 1024u * 1024u];

static int run_verify(bi_in_t *an, bi_in_t *ad, bi_in_t *bn, bi_in_t *bd,
                      bi_in_t *xn, bi_in_t *xd, int *eq)
{
    return (int)srmech_wz_verify(
        an->n, an->d, an->klen, an->kdeg,
        ad->n, ad->d, ad->klen, ad->kdeg,
        bn->n, bn->d, bn->klen, bn->kdeg,
        bd->n, bd->d, bd->klen, bd->kdeg,
        xn->n, xn->d, xn->klen, xn->kdeg,
        xd->n, xd->d, xd->klen, xd->kdeg,
        eq, g_ws, sizeof(g_ws));
}

/* Evaluate a flat bivariate input (int-coefficient) at integer (nv,kv) -> frac. */
static frac_t bi_eval(const bi_in_t *b, int64_t nv, int64_t kv)
{
    frac_t s = fmk(0, 1);
    size_t idx = 0u, dk, j;
    for (dk = 0u; dk < b->kdeg; dk++) {
        frac_t poly = fmk(0, 1);            /* horner in n over this k-slot */
        for (j = b->klen[dk]; j > 0u; j--) {
            int64_t cv = (int64_t)b->n[idx + j - 1u].limbs[0];
            if (b->n[idx + j - 1u].sign < 0) { cv = -cv; }
            if (b->n[idx + j - 1u].n == 0u) { cv = 0; }
            poly = fadd(fmul(poly, fmk(nv, 1)), fmk(cv, 1));
        }
        {
            frac_t kp = fmk(1, 1); size_t e;
            for (e = 0u; e < dk; e++) { kp = fmul(kp, fmk(kv, 1)); }
            s = fadd(s, fmul(poly, kp));
        }
        idx += b->klen[dk];
    }
    return s;
}

/* G(n,k) = R(n,k)*F(n,k) = (Xn/Xd)*F, computed exactly as (Xn*F)/Xd; the caller
 * has already checked Xd(n,k) != 0. */
static frac_t wz_g(const bi_in_t *xn, const bi_in_t *xd, int64_t nv, int64_t kv,
                   frac_t f)
{
    frac_t xnv = bi_eval(xn, nv, kv), xdv = bi_eval(xd, nv, kv);
    frac_t g = fmul(xnv, f);
    return fmul(g, fmk(xdv.den, xdv.num));       /* divide by xd = multiply by 1/xd */
}

/* Numeric WZ-equation cross-check: F(n+1,k)-F(n,k) == G(n,k+1)-G(n,k), G=R*F,
 * over the interior where the certificate denominator is nonzero. */
static int wz_numeric_ok(const bi_in_t *xn, const bi_in_t *xd,
                         frac_t (*F)(int64_t, int64_t))
{
    int n, k, ok = 1, checked = 0;
    for (n = 1; n <= 6; n++) {
        for (k = 0; k <= n + 1; k++) {
            frac_t xdk = bi_eval(xd, n, k), xdk1 = bi_eval(xd, n, k + 1);
            frac_t lhs, rhs, g0, g1;
            if (xdk.num == 0 || xdk1.num == 0) { continue; }
            g0 = wz_g(xn, xd, n, k, F(n, k));
            g1 = wz_g(xn, xd, n, k + 1, F(n, k + 1));
            lhs = fsub(F(n + 1, k), F(n, k));
            rhs = fsub(g1, g0);
            if (!feq(lhs, rhs)) { ok = 0; }
            checked++;
        }
    }
    return ok && checked > 0;
}

static frac_t F_binom(int64_t n, int64_t k)
{
    int64_t p = 1, i;
    if (k < 0 || k > n) { return fmk(0, 1); }
    for (i = 0; i < n; i++) { p *= 2; }
    return fmk(comb_i(n, k), p);
}
static frac_t F_binom_sq(int64_t n, int64_t k)
{
    int64_t c = comb_i(n, k);
    if (k < 0 || k > n) { return fmk(0, 1); }
    return fmk(c * c, comb_i(2 * n, n));
}

int main(void)
{
    int eq = 0, rc;
    printf("srmech_wz_verify smoke test (rc43)\n");

    /* Case 1: F=C(n,k)/2^n. r_n=(n+1)/(2(n+1-k)); r_k=(n-k)/(k+1).
     * true R = -k / (2(n+1-k)) -> Xn = -k, Xd = 2(n+1-k). */
    {
        bi_in_t an, ad, bn, bd, xn, xd, xbad;
        g_used = 0u;
        bi_build(&an, (int64_t[]){1,1}, (size_t[]){2}, 1);                 /* n+1 */
        bi_build(&ad, (int64_t[]){2,2,-2}, (size_t[]){2,1}, 2);            /* 2(n+1) - 2k */
        bi_build(&bn, (int64_t[]){0,1,-1}, (size_t[]){2,1}, 2);           /* n - k */
        bi_build(&bd, (int64_t[]){1,1}, (size_t[]){1,1}, 2);             /* k + 1 */
        bi_build(&xn, (int64_t[]){-1}, (size_t[]){0,1}, 2);              /* -k */
        bi_build(&xd, (int64_t[]){2,2,-2}, (size_t[]){2,1}, 2);          /* 2(n+1-k) */
        rc = run_verify(&an, &ad, &bn, &bd, &xn, &xd, &eq);
        CHECK(rc == SRMECH_OK, "case1 status OK");
        CHECK(eq == 1, "case1 true certificate verifies (out_equal == 1)");
        CHECK(wz_numeric_ok(&xn, &xd, F_binom),
              "case1 WZ equation holds numerically for R=-k/(2(n+1-k))");
        /* a WRONG certificate (+k) must NOT verify. */
        bi_build(&xbad, (int64_t[]){1}, (size_t[]){0,1}, 2);            /* +k */
        rc = run_verify(&an, &ad, &bn, &bd, &xbad, &xd, &eq);
        CHECK(rc == SRMECH_OK, "case1 wrong-cert status OK");
        CHECK(eq == 0, "case1 WRONG certificate +k does NOT verify (out_equal == 0)");
    }

    /* Case 2: F=C(n,k)^2/C(2n,n) (the Wilf-Zeilberger 1990 pair).
     * r_n=(n+1)^3/(2(2n+1)(n+1-k)^2); r_k=((n-k)/(k+1))^2. The genuine WZ certificate
     * (produced by the Python find; cross-checked here by evaluation) is
     *   R(n,k) = x / D_P,  x(n,k) = -3(n+1) k^2 + 2 k^3,  D_P = 2(2n+1)(n+1-k)^2. */
    {
        bi_in_t an, ad, bn, bd, xn, xd, xbad;
        g_used = 0u;
        bi_build(&an, (int64_t[]){1,3,3,1}, (size_t[]){4}, 1);            /* (n+1)^3 */
        /* 2(2n+1)(n+1-k)^2 : (4n+2) * ((n+1)^2 - 2(n+1)k + k^2)
         *   k^0: (4n+2)(n^2+2n+1) = 4n^3+10n^2+8n+2
         *   k^1: (4n+2)(-2)(n+1)  = -8n^2-12n-4
         *   k^2: (4n+2)                                                 */
        bi_build(&ad, (int64_t[]){2,8,10,4, -4,-12,-8, 2,4}, (size_t[]){4,3,2}, 3);
        bi_build(&bn, (int64_t[]){0,0,1, 0,-2, 1}, (size_t[]){3,2,1}, 3); /* (n-k)^2 */
        bi_build(&bd, (int64_t[]){1, 2, 1}, (size_t[]){1,1,1}, 3);       /* (k+1)^2 */
        /* x = -3(n+1) k^2 + 2 k^3 : k^0 -> empty, k^1 -> empty, k^2 -> [-3,-3], k^3 -> [2] */
        bi_build(&xn, (int64_t[]){-3,-3, 2}, (size_t[]){0,0,2,1}, 4);
        bi_build(&xd, (int64_t[]){2,8,10,4, -4,-12,-8, 2,4}, (size_t[]){4,3,2}, 3);
        rc = run_verify(&an, &ad, &bn, &bd, &xn, &xd, &eq);
        CHECK(rc == SRMECH_OK, "case2 status OK");
        CHECK(eq == 1, "case2 C(n,k)^2/C(2n,n) certificate verifies (out_equal == 1)");
        CHECK(wz_numeric_ok(&xn, &xd, F_binom_sq),
              "case2 WZ equation holds numerically for the C(2n,n) pair");
        /* a wrong certificate (negate x) must NOT verify. */
        bi_build(&xbad, (int64_t[]){3,3, 2}, (size_t[]){0,0,2,1}, 4);    /* +3(n+1)k^2 + 2k^3 */
        rc = run_verify(&an, &ad, &bn, &bd, &xbad, &xd, &eq);
        CHECK(rc == SRMECH_OK, "case2 wrong-cert status OK");
        CHECK(eq == 0, "case2 WRONG certificate does NOT verify (out_equal == 0)");
    }

    printf("\n%d passed, %d failed\n", g_pass, g_fail);
    return g_fail == 0 ? 0 : 1;
}
