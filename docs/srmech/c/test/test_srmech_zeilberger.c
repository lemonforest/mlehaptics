/*
 * test_srmech_zeilberger.c -- standalone smoke test for srmech_zeilberger (rc42).
 *
 * Validates Zeilberger's creative-telescoping recurrence against CONCRETE term
 * sums for the rc42 acceptance cases:
 *   F(n,k)=C(n,k)   (r_n=(n+1)/(n+1-k), r_k=(n-k)/(k+1))  -> f(n)=2^n, order 1
 *   F(n,k)=C(n,k)^2 (r_n=((n+1)/(n+1-k))^2, r_k=((n-k)/(k+1))^2) -> f(n)=C(2n,n), order 1
 *
 * Build (WSL / POSIX):
 *   gcc -std=c11 -Wall -Wextra -Werror -pedantic -Ic/include
 *       c/test/test_srmech_zeilberger.c c/src/[s]rmech_*.c -lm -o /tmp/zeil_smoke
 *
 * The returned recurrence Sum_j a_j(n) f(n+j) = 0 is cross-checked by SUMMING the
 * actual term values f(n) = Sum_k F(n,k) at integers (int64 fractions; small
 * inputs), never trusting the algorithm symbolically.
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
static frac_t fmul(frac_t a, frac_t b) { return fmk(a.num * b.num, a.den * b.den); }

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

/* Build a flat bivariate input from a 2-D int table tbl[k_deg][n_deg] (row-major
 * by k-degree; each row is a Poly-in-n, ascending; -1 sentinel ends a row early).
 * Returns the flat (num,den) arrays + klen[] + kdeg via out params. */
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

/* sized above the order-1 C arena (srmech_zeilberger_ws_bound(2,4,2) ~ 123 MB). */
static unsigned char g_ws[256u * 1024u * 1024u];

/* run zeilberger; return status. */
static int run_zeil(bi_in_t *rnn, bi_in_t *rnd, bi_in_t *rkn, bi_in_t *rkd,
                    size_t max_order, int *has, size_t *order,
                    srmech_bigint_t *cn, srmech_bigint_t *cd, size_t *cnl,
                    srmech_bigint_t *ce, srmech_bigint_t *ced, size_t *cekl,
                    size_t *cekd)
{
    return (int)srmech_zeilberger(
        rnn->n, rnn->d, rnn->klen, rnn->kdeg,
        rnd->n, rnd->d, rnd->klen, rnd->kdeg,
        rkn->n, rkn->d, rkn->klen, rkn->kdeg,
        rkd->n, rkd->d, rkd->klen, rkd->kdeg,
        max_order, 1u, has, order, cn, cd, cnl, ce, ced, cekl, cekd,
        g_ws, sizeof(g_ws));
}

/* evaluate a_j(n) (out coeff arrays, ascending n) at integer nv -> frac. */
static int64_t big_to_i64(const srmech_bigint_t *b)
{
    int64_t v;
    if (b->n == 0u) { return 0; }
    v = (int64_t)b->limbs[0];
    if (b->n >= 2u) { v |= ((int64_t)b->limbs[1]) << 32; }
    return (b->sign < 0) ? -v : v;
}

static frac_t coeff_eval(const srmech_bigint_t *cn, const srmech_bigint_t *cd,
                         size_t len, int64_t nv)
{
    frac_t acc = fmk(0, 1); size_t i;
    for (i = len; i > 0u; i--) {
        int64_t num = big_to_i64(&cn[i - 1u]);
        int64_t den = (cd[i - 1u].n == 0u) ? 1 : big_to_i64(&cd[i - 1u]);
        acc = fadd(fmul(acc, fmk(nv, 1)), fmk(num, den));
    }
    return acc;
}

int main(void)
{
    static srmech_bigint_t cn[64], cd[64], ce[256], ced[256];
    static size_t cnl[16], cekl[32];
    size_t order = 0u, cekd = 0u, oi;
    int has = 0, rc, n;

    printf("srmech_zeilberger smoke test (rc42)\n");

    /* Case 1: F=C(n,k). r_n=(n+1)/(n+1-k); r_k=(n-k)/(k+1). */
    {
        bi_in_t rnn, rnd, rkn, rkd;
        g_used = 0u;
        /* size the OUTPUT arrays (their limbs are caller-owned, pre-sized). */
        for (oi = 0u; oi < 64u; oi++) { bset(&cn[oi], 0); bset(&cd[oi], 1); }
        for (oi = 0u; oi < 256u; oi++) { bset(&ce[oi], 0); bset(&ced[oi], 1); }
        /* r_n num = n+1 : k^0 -> [1,1] (Poly-in-n) */
        bi_build(&rnn, (int64_t[]){1,1}, (size_t[]){2}, 1);
        /* r_n den = (n+1) - k : k^0 -> [1,1], k^1 -> [-1] */
        bi_build(&rnd, (int64_t[]){1,1,-1}, (size_t[]){2,1}, 2);
        /* r_k num = n - k : k^0 -> [0,1], k^1 -> [-1] */
        bi_build(&rkn, (int64_t[]){0,1,-1}, (size_t[]){2,1}, 2);
        /* r_k den = k + 1 : k^0 -> [1], k^1 -> [1] */
        bi_build(&rkd, (int64_t[]){1,1}, (size_t[]){1,1}, 2);
        rc = run_zeil(&rnn, &rnd, &rkn, &rkd, 4, &has, &order, cn, cd, cnl,
                      ce, ced, cekl, &cekd);
        CHECK(rc == SRMECH_OK, "case1 status OK");
        CHECK(has == 1, "case1 has recurrence");
        CHECK(order == 1u, "case1 order == 1");
        if (has) {
            int ok = 1;
            for (n = 0; n <= 8; n++) {
                frac_t s = fmk(0, 1); size_t j, off = 0u;
                for (j = 0u; j <= order; j++) {
                    frac_t aj = coeff_eval(&cn[off], &cd[off], cnl[j], n);
                    /* f(n+j) = 2^(n+j) = Sum_k C(n+j,k) */
                    int64_t f = 0, k;
                    for (k = 0; k <= n + (int)j; k++) { f += comb_i(n + (int)j, k); }
                    s = fadd(s, fmul(aj, fmk(f, 1)));
                    off += cnl[j];
                }
                if (!(s.num == 0)) { ok = 0; }
            }
            CHECK(ok, "case1 Sum_j a_j(n) 2^(n+j) == 0 for n=0..8");
        }
    }

    /* Case 2: F=C(n,k)^2. r_n=((n+1)/(n+1-k))^2; r_k=((n-k)/(k+1))^2. */
    {
        bi_in_t rnn, rnd, rkn, rkd;
        g_used = 0u;
        for (oi = 0u; oi < 64u; oi++) { bset(&cn[oi], 0); bset(&cd[oi], 1); }
        for (oi = 0u; oi < 256u; oi++) { bset(&ce[oi], 0); bset(&ced[oi], 1); }
        /* r_n num = (n+1)^2 = n^2+2n+1 : k^0 -> [1,2,1] */
        bi_build(&rnn, (int64_t[]){1,2,1}, (size_t[]){3}, 1);
        /* r_n den = (n+1-k)^2 = (n+1)^2 - 2(n+1)k + k^2
         *   k^0 -> [1,2,1], k^1 -> [-2,-2], k^2 -> [1] */
        bi_build(&rnd, (int64_t[]){1,2,1, -2,-2, 1}, (size_t[]){3,2,1}, 3);
        /* r_k num = (n-k)^2 = n^2 - 2nk + k^2 : k^0 -> [0,0,1], k^1 -> [0,-2], k^2 -> [1] */
        bi_build(&rkn, (int64_t[]){0,0,1, 0,-2, 1}, (size_t[]){3,2,1}, 3);
        /* r_k den = (k+1)^2 = 1 + 2k + k^2 : k^0 -> [1], k^1 -> [2], k^2 -> [1] */
        bi_build(&rkd, (int64_t[]){1, 2, 1}, (size_t[]){1,1,1}, 3);
        rc = run_zeil(&rnn, &rnd, &rkn, &rkd, 4, &has, &order, cn, cd, cnl,
                      ce, ced, cekl, &cekd);
        CHECK(rc == SRMECH_OK, "case2 status OK");
        CHECK(has == 1, "case2 has recurrence");
        CHECK(order == 1u, "case2 order == 1");
        if (has) {
            int ok = 1;
            for (n = 0; n <= 6; n++) {
                frac_t s = fmk(0, 1); size_t j, off = 0u;
                for (j = 0u; j <= order; j++) {
                    frac_t aj = coeff_eval(&cn[off], &cd[off], cnl[j], n);
                    int64_t f = comb_i(2 * (n + (int)j), n + (int)j);   /* C(2m,m) */
                    s = fadd(s, fmul(aj, fmk(f, 1)));
                    off += cnl[j];
                }
                if (!(s.num == 0)) { ok = 0; }
            }
            CHECK(ok, "case2 Sum_j a_j(n) C(2(n+j),n+j) == 0 for n=0..6");
        }
    }

    printf("\n%d passed, %d failed\n", g_pass, g_fail);
    return g_fail == 0 ? 0 : 1;
}
