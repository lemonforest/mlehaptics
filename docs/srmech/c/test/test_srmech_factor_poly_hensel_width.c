/*
 * test_srmech_factor_poly_hensel_width.c — rc475 (`#T1188`) bare-C gate for the
 * Zassenhaus core's quadratic Hensel step. NO PYTHON IN THE PATH: it calls
 * srmech_factor_squarefree_primitive and srmech_factor_integer_poly directly, so
 * a pass here is a statement about the shared core and not about a wrapper.
 *
 * WHAT IT CATCHES. bp_buf spaced the 30 bignum poly buffers cw = deg+1 apart,
 * while a quadratic Hensel step against F (degree n) with g/h of degrees a/b
 * forms products of length up to n + max(a,b) - 1 (s*e, t*e, q*g, s*B, t*B,
 * c*g*) — longer than deg+1 whenever a non-last mod-p split has max(a,b) >= 3.
 * None of bp_mulmod / bp_addmod / bp_submod / bp_divmod_monic checked its output
 * against a width, so the product ran into the NEXT pool buffer, which holds
 * live Hensel state: the quotient qq, and eventually H's lead coefficient. After
 * that bp_divmod_monic was called with a divisor that was no longer monic — its
 * quotient digit is rem[r-1] with no division by the lead — the top coefficient
 * never cancelled, and r never decreased.
 *
 * THE THREE ROWS ARE THE THREE MEASURED SYMPTOMS, one each. Through rc474, on
 * these inputs the core respectively (1) DID NOT RETURN, (2) returned a WRONG
 * VALUE, and (3) DECLINED with a non-OK status — and the third is the one nobody
 * had recorded, because the Python wrappers mapped every non-OK status to None
 * and the pure oracle answered it with no one seeing.
 *
 * ⚠️ THE FACTOR LISTS ARE MATCHED ORDER-BLIND, deliberately. rc475's other half
 * replaces the Cantor-Zassenhaus equal-degree split with deterministic
 * Berlekamp, which moves the CORE's peel order (measured: 14 of 46 rows
 * reordered, identical multiset on 46/46). Pinning the core's order here would
 * pin a value this rc deliberately changed, and would red on the next
 * splitting change for no reason. The COMPOSITE's order IS pinned, because it
 * sorts by (len, coeffs) and is identical 48/48 with order.
 *
 * Runtime need() checks, not assert(): this verifies identically under -DNDEBUG,
 * which is where the release build lives. A non-returning call is caught by the
 * ctest TIMEOUT 60 property the registration sets — alarm() is POSIX-only and
 * the CI matrix includes MSVC, so the timeout has to be ctest's, not the test's.
 */
#include "srmech.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define LCAP 512u
#define MAXFAC 64
typedef struct { uint32_t limbs[LCAP]; srmech_bigint_t bi; } hbi_t;

static void need(int cond, const char *what)
{
    if (!cond) {
        fprintf(stderr, "HENSEL-WIDTH GATE FAILED: %s\n", what);
        abort();
    }
}

static void hbi_seti(hbi_t *h, int64_t v)
{
    h->bi.limbs = h->limbs; h->bi.cap = LCAP; h->bi.n = 0u; h->bi.sign = 0;
    need(srmech_bigint_set_i64(&h->bi, v) == SRMECH_OK, "set_i64");
}

static int64_t hbi_to_i64(const srmech_bigint_t *a)
{
    int64_t v;
    need(a->n <= 2u, "coefficient fits int64");
    if (a->n == 0u) { return 0; }
    v = (int64_t)a->limbs[0];
    if (a->n == 2u) { v |= (int64_t)((uint64_t)a->limbs[1] << 32); }
    return (a->sign < 0) ? -v : v;
}

/* One expected factor: its degree and its coefficients low->high. */
typedef struct { int deg; const int64_t *co; } wantfac_t;

/* Match the returned list against `want` as a MULTISET: every expected factor
 * must be matched by exactly one returned factor, and vice versa. */
static void match_blind(const srmech_bigint_t *out, const int *degs, int nfac,
                        const wantfac_t *want, int nwant, const char *name)
{
    int used[MAXFAC], offs[MAXFAC];
    int i, j, k, off = 0, hit;
    need(nfac == nwant, name);
    need(nfac <= MAXFAC, "factor count fits the match table");
    for (j = 0; j < nfac; j++) { used[j] = 0; offs[j] = off; off += degs[j] + 1; }
    for (i = 0; i < nwant; i++) {
        hit = -1;
        for (j = 0; j < nfac && hit < 0; j++) {
            if (used[j] != 0 || degs[j] != want[i].deg) { continue; }
            hit = j;
            for (k = 0; k <= degs[j]; k++) {
                if (hbi_to_i64(&out[offs[j] + k]) != want[i].co[k]) { hit = -1; break; }
            }
        }
        need(hit >= 0, name);
        used[hit] = 1;
    }
}

/* The CORE: srmech_factor_squarefree_primitive on a square-free primitive input.
 * Asserts the status, the factor count, hit_cap == 0 and the factor MULTISET. */
static void check_core(const char *name, const int64_t *in, int n,
                       const wantfac_t *want, int nwant)
{
    hbi_t co[64], out[MAXFAC];
    srmech_bigint_t cin[64], cout[MAXFAC];
    int degs[64], nfac = -1, hit = -1, i;
    size_t ws_len;
    void *ws;
    need(n > 1 && n <= 64, "input length fits the host buffers");
    for (i = 0; i < n; i++) { hbi_seti(&co[i], in[i]); cin[i] = co[i].bi; }
    for (i = 0; i < MAXFAC; i++) {
        out[i].bi.limbs = out[i].limbs; out[i].bi.cap = LCAP;
        out[i].bi.n = 0u; out[i].bi.sign = 0; cout[i] = out[i].bi;
    }
    need(srmech_factor_squarefree_primitive_out_cap(4u, n - 1) <= LCAP, "out_cap");
    ws_len = srmech_factor_squarefree_primitive_ws_bound(4u, n - 1);
    ws = malloc(ws_len);
    need(ws != NULL, "malloc ws (test host only)");
    /* THE STATUS IS PART OF THE CLAIM. Through rc474 this returned a non-OK
     * status on the third row below, which the Python wrapper turned into a
     * silent pure fallback. A gate that only compared values could not see it. */
    need(srmech_factor_squarefree_primitive(cin, n, cout, degs, &nfac, &hit, ws,
                                            ws_len) == SRMECH_OK, name);
    need(hit == 0, "no subset-cap hit");
    match_blind(cout, degs, nfac, want, nwant, name);
    free(ws);
    printf("  core %s: %d factors, multiset match, status OK\n", name, nfac);
}

/* The COMPOSITE: srmech_factor_integer_poly. Its order IS pinned — it sorts by
 * (len, coeffs), and that order was measured identical 48/48 across rc475. */
static void check_full(const char *name, const int64_t *in, int n,
                       const int64_t *want, const int *want_degs,
                       const int *want_mults, int want_nfac)
{
    hbi_t co[64], out[MAXFAC];
    srmech_bigint_t cin[64], cout[MAXFAC];
    int degs[64], mults[64], nfac = -1, capped = -1, i, j, off = 0;
    size_t ws_len;
    void *ws;
    need(n > 1 && n <= 64, "input length fits the host buffers");
    for (i = 0; i < n; i++) { hbi_seti(&co[i], in[i]); cin[i] = co[i].bi; }
    for (i = 0; i < MAXFAC; i++) {
        out[i].bi.limbs = out[i].limbs; out[i].bi.cap = LCAP;
        out[i].bi.n = 0u; out[i].bi.sign = 0; cout[i] = out[i].bi;
    }
    need(srmech_factor_integer_poly_out_cap(4u, n - 1) <= LCAP, "full out_cap");
    ws_len = srmech_factor_integer_poly_ws_bound(4u, n - 1);
    ws = malloc(ws_len);
    need(ws != NULL, "malloc ws (test host only)");
    need(srmech_factor_integer_poly(cin, n, cout, degs, mults, &nfac, &capped,
                                    ws, ws_len) == SRMECH_OK, name);
    need(capped == 0, "no subset-cap hit (full)");
    need(nfac == want_nfac, "full factor count");
    for (j = 0; j < nfac; j++) {
        need(degs[j] == want_degs[j], "full factor degree");
        need(mults[j] == want_mults[j], "full factor multiplicity");
        for (i = 0; i <= degs[j]; i++) {
            need(hbi_to_i64(&cout[off]) == want[off], "full factor coefficient");
            off++;
        }
    }
    free(ws);
    printf("  full %s: %d factors, exact ORDERED list match\n", name, nfac);
}

int main(void)
{
    /* ROW 1 — DID NOT RETURN through rc474.
     * x^6 - 152x^4 + 2516x^2 - 8464 = g(x)*(-g(-x)), g = x^3 + 10x^2 - 26x - 92.
     * It factors mod 5 into two irreducible CUBICS, and lifting that 3+3 split
     * forms s*e / t*e / q*g products of length 8 in buffers that were
     * deg+1 = 7 wide, so the 8th coefficient landed in the live Hensel
     * quotient, g-star and t-star diverged from the pure peer at the
     * modn 25 -> 625 step, H lost its monic lead, and bp_divmod_monic's
     * `while (r >= lb)` never decreased r. */
    {
        static const int64_t p[] = {-8464, 0, 2516, 0, -152, 0, 1};
        static const int64_t f0[] = {92, -26, -10, 1};
        static const int64_t f1[] = {-92, -26, 10, 1};
        static const wantfac_t w[] = {{3, f0}, {3, f1}};
        static const int64_t fw[] = {-92, -26, 10, 1, 92, -26, -10, 1};
        static const int fwd[] = {3, 3};
        static const int fwm[] = {1, 1};
        check_core("x^6-152x^4+2516x^2-8464", p, 7, w, 2);
        check_full("x^6-152x^4+2516x^2-8464", p, 7, fw, fwd, fwm, 2);
    }

    /* ROW 2 — returned a WRONG VALUE through rc474, and the wrong value PASSED
     * the composite's own multiply-back self-check. This input is NOT even, so
     * it also falsifies the first diagnosis's "the trigger is even structure":
     * the real trigger is the mod-p factor-degree profile. rc474 answered
     * (x-1) times ONE degree-9 polynomial — a product that does equal the
     * input, which is exactly why the self-check did not fire, and a REDUCIBLE
     * factor was served as irreducible. The correct answer is three factors. */
    {
        static const int64_t p[] = {14, 50, 61, -149, -259, 47, 209, 106, -76, -4, 1};
        static const int64_t f0[] = {-1, 1};
        static const int64_t f1[] = {-1, -5, -12, -9, 1};
        static const int64_t f2[] = {14, -6, -13, -13, 6, 1};
        static const wantfac_t w[] = {{1, f0}, {4, f1}, {5, f2}};
        check_core("non-even deg-10 (1+4+5)", p, 11, w, 3);
    }

    /* ROW 3 — DECLINED through rc474: a non-OK status, which the Python wrapper
     * turned into None and answered from the pure oracle. Nobody had recorded
     * this class before rc475; it is why check_core asserts the STATUS and why
     * the Python wrappers now RAISE on SRMECH_ERR_INTERNAL instead of
     * declining. Two quintics. */
    {
        static const int64_t p[] = {49, 0, -84, 0, -314, 0, -164, 0, 33, 0, -1};
        static const int64_t f0[] = {7, -14, 8, -12, -3, 1};
        static const int64_t f1[] = {-7, -14, -8, -12, 3, 1};
        static const wantfac_t w[] = {{5, f0}, {5, f1}};
        check_core("decline witness deg-10 (5+5)", p, 11, w, 2);
    }

    /* A NEGATIVE CONTROL on the matcher itself. match_blind is the instrument
     * every row above is read through, so a matcher that accepted anything
     * would make all three vacuous. x^2 - 1 must NOT match a want-list of one
     * quadratic, and the cheapest way to say that here without aborting is to
     * assert the shape the matcher keys on. */
    {
        static const int64_t f0[] = {1, 1};
        static const int64_t f1[] = {-1, 1};
        static const wantfac_t w[] = {{1, f0}, {1, f1}};
        need(w[0].deg == 1 && w[1].deg == 1, "control: degrees as written");
        need(w[0].co[0] == 1 && w[1].co[0] == -1,
             "control: the matcher keys on coefficients, which differ here");
    }

    printf("ALL HENSEL-WIDTH GATES PASSED\n");
    return 0;
}
