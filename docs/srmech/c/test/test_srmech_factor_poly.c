/*
 * test_srmech_factor_poly.c — standalone C smoke for the Zassenhaus integer
 * polynomial factorizer srmech_factor_squarefree_primitive. Proves the C-only
 * host recovers the irreducible factors of known polynomials (multiply-back ==
 * input), with NO Python present.
 *
 * Build (from docs/srmech), asserts-live OR Release(-DNDEBUG):
 *   gcc -std=c17 -Wall -Wextra -Werror -pedantic [-DNDEBUG] -Ic/include \
 *       c/test/test_srmech_factor_poly.c c/src/srmech_factor_poly.c \
 *       c/src/srmech_bigint.c -o /tmp/fac_smoke && /tmp/fac_smoke
 *
 * Exit 0 on all-pass; abort()s on any mismatch (runtime checks, not assert()s,
 * so it verifies identically under -DNDEBUG to match the CI pedantic Release).
 */

#include "srmech.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define LCAP 512u
typedef struct { uint32_t limbs[LCAP]; srmech_bigint_t bi; } hbi_t;

static void need(int cond, const char *what)
{
    if (!cond) {
        fprintf(stderr, "FACTOR-POLY SMOKE FAILED: %s\n", what);
        abort();
    }
}

static void hbi_seti(hbi_t *h, int64_t v)
{
    srmech_status_t rc;
    h->bi.limbs = h->limbs;
    h->bi.cap = LCAP;
    h->bi.n = 0u;
    h->bi.sign = 0;
    rc = srmech_bigint_set_i64(&h->bi, v);
    need(rc == SRMECH_OK, "hbi_seti");
}

static int64_t hbi_to_i64(const srmech_bigint_t *a)
{
    int64_t v;
    need(a->n <= 2u, "hbi_to_i64 magnitude");
    if (a->n == 0u) { return 0; }
    v = (int64_t)a->limbs[0];
    if (a->n == 2u) { v |= (int64_t)((uint64_t)a->limbs[1] << 32); }
    return (a->sign < 0) ? -v : v;
}

/* Factor `in` (deg = n-1), verify Π factors == in (integer multiply-back) and
 * the factor count. Prints the factorization. */
static void check_factor(const char *name, const int64_t *in, int n,
                         int expect_nfac)
{
    hbi_t coeffs[32];
    srmech_bigint_t cin[32];
    hbi_t out[64];
    srmech_bigint_t cout[64];
    int degs[32], nfac = 0, hit = 0, i, j, off, deg = n - 1;
    int64_t prod[64];
    size_t ws_len, ocap;
    void *ws;
    srmech_status_t st;

    for (i = 0; i < n; i++) { hbi_seti(&coeffs[i], in[i]); cin[i] = coeffs[i].bi; }
    ocap = srmech_factor_squarefree_primitive_out_cap(4u, deg);
    need(ocap <= LCAP, "out_cap fits harness LCAP");
    for (i = 0; i < 64; i++) {
        out[i].bi.limbs = out[i].limbs; out[i].bi.cap = LCAP;
        out[i].bi.n = 0u; out[i].bi.sign = 0;
        cout[i] = out[i].bi;
    }
    ws_len = srmech_factor_squarefree_primitive_ws_bound(4u, deg);
    ws = malloc(ws_len);
    need(ws != NULL, "malloc ws");
    st = srmech_factor_squarefree_primitive(cin, n, cout, degs, &nfac, &hit,
                                            ws, ws_len);
    need(st == SRMECH_OK, name);
    need(hit == 0, "no cap hit");
    /* multiply-back: prod = Π factor_j */
    for (i = 0; i < 64; i++) { prod[i] = 0; }
    prod[0] = 1;
    off = 0;
    printf("  %s -> %d factor(s):", name, nfac);
    for (j = 0; j < nfac; j++) {
        int64_t fac[32], tmp[64];
        int fl = degs[j] + 1, k;
        for (k = 0; k < fl; k++) { fac[k] = hbi_to_i64(&cout[off + k]); }
        off += fl;
        printf(" [");
        for (k = 0; k < fl; k++) { printf("%s%lld", k ? "," : "", (long long)fac[k]); }
        printf("]");
        for (k = 0; k < 64; k++) { tmp[k] = 0; }
        for (k = 0; k < 64 - fl; k++) {
            int t;
            if (prod[k] == 0) { continue; }
            for (t = 0; t < fl; t++) { tmp[k + t] += prod[k] * fac[t]; }
        }
        for (k = 0; k < 64; k++) { prod[k] = tmp[k]; }
    }
    printf("\n");
    for (i = 0; i < n; i++) { need(prod[i] == in[i], "multiply-back == input"); }
    for (i = n; i < 64; i++) { need(prod[i] == 0, "multiply-back tail zero"); }
    need(nfac == expect_nfac, "factor count");
    free(ws);
}

int main(void)
{
    /* x^2 - 1 = (x-1)(x+1) */
    { int64_t p[] = {-1, 0, 1}; check_factor("x^2-1", p, 3, 2); }
    /* x^2 + 1 irreducible */
    { int64_t p[] = {1, 0, 1}; check_factor("x^2+1", p, 3, 1); }
    /* x^4 - 1 = (x-1)(x+1)(x^2+1) */
    { int64_t p[] = {-1, 0, 0, 0, 1}; check_factor("x^4-1", p, 5, 3); }
    /* cyclotomic Phi_8 = x^4 + 1 (irreducible over Q) */
    { int64_t p[] = {1, 0, 0, 0, 1}; check_factor("Phi_8=x^4+1", p, 5, 1); }
    /* cyclotomic Phi_12 = x^4 - x^2 + 1 (irreducible) */
    { int64_t p[] = {1, 0, -1, 0, 1}; check_factor("Phi_12", p, 5, 1); }
    /* (x^2+1)(x^2+2) = x^4 + 3x^2 + 2 */
    { int64_t p[] = {2, 0, 3, 0, 1}; check_factor("(x^2+1)(x^2+2)", p, 5, 2); }
    /* (x-2)(x+3)(x^2+x+1) = x^4 + 2x^3 - 4x^2 - 5x - 6 (3 irreducibles) */
    { int64_t p[] = {-6, -5, -4, 2, 1}; check_factor("(x-2)(x+3)(x^2+x+1)", p, 5, 3); }
    /* x^3 - x = x(x-1)(x+1) */
    { int64_t p[] = {0, -1, 0, 1}; check_factor("x^3-x", p, 4, 3); }
    /* x^6 - 1 = (x-1)(x+1)(x^2+x+1)(x^2-x+1) */
    { int64_t p[] = {-1, 0, 0, 0, 0, 0, 1}; check_factor("x^6-1", p, 7, 4); }
    /* x^8 - 1 = (x-1)(x+1)(x^2+1)(x^4+1) */
    { int64_t p[] = {-1, 0, 0, 0, 0, 0, 0, 0, 1}; check_factor("x^8-1", p, 9, 4); }
    printf("ALL FACTOR-POLY C SMOKE TESTS PASSED\n");
    return 0;
}
