/*
 * test_srmech_poly.c — standalone C smoke for the exact-rational polynomial
 * carrier srmech_poly_* (the §76 telescope foundation). Proves the C-only host
 * computes the same exact-Q coefficients the Python Poly does, over caller-arena
 * srmech_bigint, with NO Python present.
 *
 * Build (from docs/srmech), one line:
 *   gcc -std=c11 -Wall -Wextra -Werror -pedantic -Ic/include
 *       c/test/test_srmech_poly.c c/src/[star].c -lm -o /tmp/poly_smoke
 *
 * Exit 0 on all-pass; aborts on any mismatch, and exits non-zero if any case
 * failed to run.
 *
 * ⚠️ rc453 (`#T1171`) — THIS FILE DID NO WORK UNDER Release/NDEBUG. Every call
 * into the library was the OPERAND of an `assert()`, and CMAKE_BUILD_TYPE=Release
 * compiles `-DNDEBUG`, which deletes the assert AND its operand. So
 * `hbi_set` never parsed, `hbi_dec` never rendered, and `expect_coeff` then ran
 * `strcmp` over an UNINITIALISED 8192-byte stack buffer — undefined behaviour in
 * the only configuration CI builds. gcc said so directly
 * (`-Werror=uninitialized` on `bn`), which is why registering this file with
 * CMake in rc452 turned the whole 3-OS pedantic matrix red: the compiler was
 * reporting a real defect, not being fussy.
 *
 * MEASURED, not inferred — and the measurement corrected the first guess. Build
 * HEAD's version `gcc -std=c11 -O2 -DNDEBUG` against libsrmech.so and run it:
 *
 *     FAIL add c0: got / expected 1/1
 *     Aborted (core dumped)
 *
 * It does NOT pass vacuously, which is what "the asserts are stripped" suggests
 * at first. `expect_coeff`'s comparison is a real `if`/`abort`, so it survives —
 * it just compares the EMPTY string that `hbi_dec` never wrote. So these two
 * files could not have been green in ctest even with the warnings silenced, and
 * "38/38 on 3 OSes" was false on two independent counts, not one.
 *
 * The fix is NOT `(void)param;`. Every side-effecting call is HOISTED out of the
 * assert into `must_ok`, and every value check into `check_true` — both of which
 * survive NDEBUG. The unused-variable warnings disappear as a CONSEQUENCE of the
 * variables becoming genuinely used; silencing them would have left the abort.
 */

#include "srmech.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ---- NDEBUG-surviving checks (see the ⚠️ note above) ---- */

/* A library call that must succeed. Takes the STATUS as an argument, so the call
 * is evaluated by the caller and cannot be compiled away. */
static void must_ok(srmech_status_t st, const char *what)
{
    if (st != SRMECH_OK) {
        fprintf(stderr, "FAIL %s: status %d\n", what, (int)st);
        abort();
    }
}

/* A value/bounds check. Replaces `assert(cond)` where the condition is a real
 * assertion about the result, not a debug-only sanity note. */
static void check_true(int cond, const char *what)
{
    if (!cond) {
        fprintf(stderr, "FAIL %s\n", what);
        abort();
    }
}

/* ---- tiny bigint helpers for the harness (caller-owned limb buffers) ---- */

#define LCAP 4096u   /* limbs per harness bigint — far past 2^64 magnitudes */

typedef struct { uint32_t limbs[LCAP]; srmech_bigint_t bi; } hbi_t;

static void hbi_set(hbi_t *h, const char *dec)
{
    h->bi.limbs = h->limbs;
    h->bi.cap = LCAP;
    h->bi.n = 0u;
    h->bi.sign = 0;
    must_ok(srmech_bigint_from_dec(&h->bi, dec, strlen(dec)), "hbi_set from_dec");
}

static void hbi_blank(hbi_t *h)
{
    h->bi.limbs = h->limbs;
    h->bi.cap = LCAP;
    h->bi.n = 0u;
    h->bi.sign = 0;
}

/* Render a harness bigint to decimal into `buf`. */
static void hbi_dec(const srmech_bigint_t *a, char *buf, size_t cap)
{
    static uint32_t ws[LCAP * 16];
    size_t outlen = 0u;
    must_ok(srmech_bigint_to_dec(a, buf, cap, &outlen, ws, sizeof(ws)),
            "hbi_dec to_dec");
}

/* Assert a (num,den) coefficient equals the expected decimal strings. */
static void expect_coeff(const srmech_bigint_t *num, const srmech_bigint_t *den,
                         const char *enum_, const char *eden, const char *what)
{
    char bn[8192], bd[8192];
    hbi_dec(num, bn, sizeof(bn));
    hbi_dec(den, bd, sizeof(bd));
    if (strcmp(bn, enum_) != 0 || strcmp(bd, eden) != 0) {
        fprintf(stderr, "FAIL %s: got %s/%s expected %s/%s\n",
                what, bn, bd, enum_, eden);
        abort();
    }
}

/* ---- a fixed-width polynomial-array harness ---- */

#define MAXTERMS 16u

typedef struct {
    hbi_t num[MAXTERMS];
    hbi_t den[MAXTERMS];
    srmech_bigint_t bn[MAXTERMS];     /* parallel srmech_bigint views */
    srmech_bigint_t bd[MAXTERMS];
    size_t n;
} hpoly_t;

/* Build a polynomial from parallel decimal num/den string arrays. */
static void hpoly_set(hpoly_t *p, const char *const *nums,
                      const char *const *dens, size_t n)
{
    size_t i;
    check_true(n <= MAXTERMS, "hpoly_set n <= MAXTERMS");
    p->n = n;
    for (i = 0u; i < n; i++) {
        hbi_set(&p->num[i], nums[i]);
        hbi_set(&p->den[i], dens[i]);
        p->bn[i] = p->num[i].bi;
        p->bd[i] = p->den[i].bi;
    }
}

/* Blank an output polynomial of `n` coefficient slots (cap-ready). */
static void hpoly_blank(hpoly_t *p, size_t n)
{
    size_t i;
    check_true(n <= MAXTERMS, "hpoly_blank n <= MAXTERMS");
    p->n = n;
    for (i = 0u; i < n; i++) {
        hbi_blank(&p->num[i]);
        hbi_blank(&p->den[i]);
        p->bn[i] = p->num[i].bi;
        p->bd[i] = p->den[i].bi;
    }
    /* re-point the srmech_bigint views at the (now-blank) limb buffers and
     * keep them in sync after the op writes through bn/bd. */
}

/* After an op writes through p->bn / p->bd, sync the hbi wrappers back so the
 * limb data the op wrote (via the bn/bd srmech_bigint structs, which alias the
 * same limb buffers) is what hbi_dec reads. The op writes n/sign/limb data into
 * p->bn[i]; copy those struct fields back into the rendering view. */
static void hpoly_sync(hpoly_t *p, size_t n)
{
    size_t i;
    for (i = 0u; i < n; i++) {
        p->num[i].bi = p->bn[i];
        p->den[i].bi = p->bd[i];
    }
}

static size_t arena_words = 0u;
static uint32_t *arena = NULL;

static void arena_ensure(size_t bytes)
{
    size_t words = bytes / sizeof(uint32_t) + 8u;
    if (words > arena_words) {
        free(arena);
        arena = (uint32_t *)malloc(words * sizeof(uint32_t));
        check_true(arena != NULL, "arena_ensure malloc");
        arena_words = words;
    }
}

/* ---- the smoke cases ---- */

static int npass = 0;

static void t_add(void)
{
    /* (1 + 2x + 3x^2) + (x) = 1 + 3x + 3x^2 */
    const char *an[] = {"1", "2", "3"}, *ad[] = {"1", "1", "1"};
    const char *bn[] = {"0", "1"}, *bd[] = {"1", "1"};
    hpoly_t a, b, o; size_t olen = 0u, ws;
    hpoly_set(&a, an, ad, 3); hpoly_set(&b, bn, bd, 2);
    hpoly_blank(&o, 3);
    ws = srmech_poly_ws_bound(2u, 3u); arena_ensure(ws);
    must_ok(srmech_poly_add(a.bn, a.bd, 3, b.bn, b.bd, 2,
                            o.bn, o.bd, &olen, arena, ws), "poly_add");
    hpoly_sync(&o, 3);
    check_true(olen == 3, "add olen == 3");
    expect_coeff(&o.bn[0], &o.bd[0], "1", "1", "add c0");
    expect_coeff(&o.bn[1], &o.bd[1], "3", "1", "add c1");
    expect_coeff(&o.bn[2], &o.bd[2], "3", "1", "add c2");
    npass++;
}

static void t_mul(void)
{
    /* (x + 1)(x - 1) = x^2 - 1  ->  [-1, 0, 1] */
    const char *an[] = {"1", "1"}, *ad[] = {"1", "1"};
    const char *bn[] = {"-1", "1"}, *bd[] = {"1", "1"};
    hpoly_t a, b, o; size_t olen = 0u, ws;
    hpoly_set(&a, an, ad, 2); hpoly_set(&b, bn, bd, 2);
    hpoly_blank(&o, 3);
    ws = srmech_poly_ws_bound(2u, 4u); arena_ensure(ws);
    must_ok(srmech_poly_mul(a.bn, a.bd, 2, b.bn, b.bd, 2,
                            o.bn, o.bd, &olen, arena, ws), "poly_mul");
    hpoly_sync(&o, 3);
    check_true(olen == 3, "mul olen == 3");
    expect_coeff(&o.bn[0], &o.bd[0], "-1", "1", "mul c0");
    expect_coeff(&o.bn[1], &o.bd[1], "0", "1", "mul c1");
    expect_coeff(&o.bn[2], &o.bd[2], "1", "1", "mul c2");
    npass++;
}

static void t_divmod(void)
{
    /* (x^3 + 2) / (x + 1): q = x^2 - x + 1, r = 1  ->  q[1,-1,1] r[1] */
    const char *an[] = {"2", "0", "0", "1"}, *ad[] = {"1", "1", "1", "1"};
    const char *bn[] = {"1", "1"}, *bd[] = {"1", "1"};
    hpoly_t a, b, q, r; size_t qn = 0u, rn = 0u, ws;
    hpoly_set(&a, an, ad, 4); hpoly_set(&b, bn, bd, 2);
    hpoly_blank(&q, 3); hpoly_blank(&r, 4);
    ws = srmech_poly_ws_bound(2u, 5u); arena_ensure(ws);
    must_ok(srmech_poly_divmod(a.bn, a.bd, 4, b.bn, b.bd, 2,
                               q.bn, q.bd, &qn, r.bn, r.bd, &rn,
                               arena, ws), "poly_divmod");
    hpoly_sync(&q, 3); hpoly_sync(&r, 4);
    check_true(qn == 3 && rn == 1, "divmod qn == 3 && rn == 1");
    expect_coeff(&q.bn[0], &q.bd[0], "1", "1", "divmod q0");
    expect_coeff(&q.bn[1], &q.bd[1], "-1", "1", "divmod q1");
    expect_coeff(&q.bn[2], &q.bd[2], "1", "1", "divmod q2");
    expect_coeff(&r.bn[0], &r.bd[0], "1", "1", "divmod r0");
    npass++;
}

static void t_eval(void)
{
    /* (1 + 2x + 3x^2) at x = 2  ->  1 + 4 + 12 = 17/1 */
    const char *pn[] = {"1", "2", "3"}, *pd[] = {"1", "1", "1"};
    hpoly_t p; hbi_t x_n, x_d, o_n, o_d; size_t ws;
    hpoly_set(&p, pn, pd, 3);
    hbi_set(&x_n, "2"); hbi_set(&x_d, "1");
    hbi_blank(&o_n); hbi_blank(&o_d);
    ws = srmech_poly_ws_bound(2u, 4u); arena_ensure(ws);
    must_ok(srmech_poly_eval(p.bn, p.bd, 3, &x_n.bi, &x_d.bi,
                             &o_n.bi, &o_d.bi, arena, ws), "poly_eval");
    expect_coeff(&o_n.bi, &o_d.bi, "17", "1", "eval(2)");
    npass++;
}

static void t_shift(void)
{
    /* p = 1 + 2x + 3x^2 ; p(x+1) = 6 + 8x + 3x^2  ->  [6, 8, 3] */
    const char *pn[] = {"1", "2", "3"}, *pd[] = {"1", "1", "1"};
    const char *hn = "1", *hd = "1";
    hpoly_t p, o; hbi_t h_n, h_d; size_t olen = 0u, ws;
    hpoly_set(&p, pn, pd, 3);
    hbi_set(&h_n, hn); hbi_set(&h_d, hd);
    hpoly_blank(&o, 3);
    ws = srmech_poly_ws_bound(2u, 4u); arena_ensure(ws);
    must_ok(srmech_poly_shift(p.bn, p.bd, 3, &h_n.bi, &h_d.bi,
                              o.bn, o.bd, &olen, arena, ws), "poly_shift");
    hpoly_sync(&o, 3);
    check_true(olen == 3, "shift olen == 3");
    expect_coeff(&o.bn[0], &o.bd[0], "6", "1", "shift c0");
    expect_coeff(&o.bn[1], &o.bd[1], "8", "1", "shift c1");
    expect_coeff(&o.bn[2], &o.bd[2], "3", "1", "shift c2");
    npass++;
}

static void t_rational_divmod(void)
{
    /* (1/2 + 1/3 x + x^2) / (2/5 + x): exact-Q non-integer coefficients.
     * Verified against the Python Poly / Fraction oracle separately; here we
     * check the reconstruction q*b + r == a by re-multiplying is exercised in
     * the Python==C parity test. This case checks a known small exact result:
     *   q = (1/3 - 2/5) + x = -1/15 + x   ->  q0 = -1/15, q1 = 1
     *   r = 1/2 - (2/5)(-1/15) = 1/2 + 2/75 = 79/150 */
    const char *an[] = {"1", "1", "1"}, *ad[] = {"2", "3", "1"};
    const char *bn[] = {"2", "1"}, *bd[] = {"5", "1"};
    hpoly_t a, b, q, r; size_t qn = 0u, rn = 0u, ws;
    hpoly_set(&a, an, ad, 3); hpoly_set(&b, bn, bd, 2);
    hpoly_blank(&q, 2); hpoly_blank(&r, 3);
    ws = srmech_poly_ws_bound(2u, 4u); arena_ensure(ws);
    must_ok(srmech_poly_divmod(a.bn, a.bd, 3, b.bn, b.bd, 2,
                               q.bn, q.bd, &qn, r.bn, r.bd, &rn,
                               arena, ws), "poly_divmod rational");
    hpoly_sync(&q, 2); hpoly_sync(&r, 3);
    check_true(qn == 2 && rn == 1, "ratdivmod qn == 2 && rn == 1");
    expect_coeff(&q.bn[0], &q.bd[0], "-1", "15", "ratdivmod q0");
    expect_coeff(&q.bn[1], &q.bd[1], "1", "1", "ratdivmod q1");
    expect_coeff(&r.bn[0], &r.bd[0], "79", "150", "ratdivmod r0");
    npass++;
}

static void t_bignum_eval(void)
{
    /* huge-coefficient eval: p = (10^40+1)/3^30 + x ; at x = 2^65/1
     * value = (10^40+1)/3^30 + 2^65.  3^30 = 205891132094649.
     * num = (10^40+1) + 2^65 * 3^30 ; den = 3^30. (reduced if gcd==1) */
    const char *pn[] = {"10000000000000000000000000000000000000001", "1"};
    const char *pd[] = {"205891132094649", "1"};
    hpoly_t p; hbi_t x_n, x_d, o_n, o_d; size_t ws;
    hpoly_set(&p, pn, pd, 2);
    hbi_set(&x_n, "36893488147419103232");   /* 2^65 */
    hbi_set(&x_d, "1");
    hbi_blank(&o_n); hbi_blank(&o_d);
    ws = srmech_poly_ws_bound(4u, 3u); arena_ensure(ws);
    must_ok(srmech_poly_eval(p.bn, p.bd, 2, &x_n.bi, &x_d.bi,
                             &o_n.bi, &o_d.bi, arena, ws), "poly_eval bignum");
    /* expected (verified against the Python Poly / Fraction oracle):
     *   num = (10^40+1) + 2^65 * 3^30  (reduced; gcd == 1)
     *   den = 3^30 = 205891132094649 */
    expect_coeff(&o_n.bi, &o_d.bi,
                 "10000007596042041592633802526409325805569",
                 "205891132094649", "bignum eval");
    npass++;
}

static void t_gcd(void)
{
    /* gcd(x^2 - 1, x - 1) = x - 1 (monic)  ->  [-1, 1] */
    const char *an[] = {"-1", "0", "1"}, *ad[] = {"1", "1", "1"};
    const char *bn[] = {"-1", "1"}, *bd[] = {"1", "1"};
    hpoly_t a, b, o; size_t olen = 0u, ws;
    hpoly_set(&a, an, ad, 3); hpoly_set(&b, bn, bd, 2);
    hpoly_blank(&o, 3);
    ws = srmech_poly_gcd_ws_bound(2u, 3u); arena_ensure(ws);
    must_ok(srmech_poly_gcd(a.bn, a.bd, 3, b.bn, b.bd, 2,
                            o.bn, o.bd, &olen, arena, ws), "poly_gcd");
    hpoly_sync(&o, 3);
    check_true(olen == 2, "gcd olen == 2");
    expect_coeff(&o.bn[0], &o.bd[0], "-1", "1", "gcd c0");
    expect_coeff(&o.bn[1], &o.bd[1], "1", "1", "gcd c1");
    npass++;
}

static void t_gcd_coprime(void)
{
    /* gcd(x, x + 3) = 1 (coprime -> monic constant 1)  ->  [1] */
    const char *an[] = {"0", "1"}, *ad[] = {"1", "1"};
    const char *bn[] = {"3", "1"}, *bd[] = {"1", "1"};
    hpoly_t a, b, o; size_t olen = 0u, ws;
    hpoly_set(&a, an, ad, 2); hpoly_set(&b, bn, bd, 2);
    hpoly_blank(&o, 2);
    ws = srmech_poly_gcd_ws_bound(2u, 2u); arena_ensure(ws);
    must_ok(srmech_poly_gcd(a.bn, a.bd, 2, b.bn, b.bd, 2,
                            o.bn, o.bd, &olen, arena, ws), "poly_gcd coprime");
    hpoly_sync(&o, 2);
    check_true(olen == 1, "gcd-coprime olen == 1");
    expect_coeff(&o.bn[0], &o.bd[0], "1", "1", "gcd-coprime c0");
    npass++;
}

static void t_gcd_p_zero(void)
{
    /* gcd(2x^2 + 4, 0) = monic(2x^2+4) = x^2 + 2  ->  [2, 0, 1] */
    const char *an[] = {"4", "0", "2"}, *ad[] = {"1", "1", "1"};
    hpoly_t a, b, o; size_t olen = 0u, ws;
    hpoly_set(&a, an, ad, 3);
    hpoly_blank(&b, 0);
    hpoly_blank(&o, 3);
    ws = srmech_poly_gcd_ws_bound(2u, 3u); arena_ensure(ws);
    must_ok(srmech_poly_gcd(a.bn, a.bd, 3, b.bn, b.bd, 0,
                            o.bn, o.bd, &olen, arena, ws), "poly_gcd p_zero");
    hpoly_sync(&o, 3);
    check_true(olen == 3, "gcd(p,0) olen == 3");
    expect_coeff(&o.bn[0], &o.bd[0], "2", "1", "gcd(p,0) c0");
    expect_coeff(&o.bn[2], &o.bd[2], "1", "1", "gcd(p,0) c2");
    npass++;
}

static void t_gcd_bignum(void)
{
    /* A higher-degree case that drives the Euclidean chain (a degree-3 factor
     * shared by two degree-4 polynomials) over RATIONAL coefficients — the
     * regime the rc38 naive per-op envelope OVERFLOWED on. Shared cubic
     * x^3 - (1/3)x^2 - 2x + 2/3  ->  [2/3, -2, -1/3, 1]:
     *   a = shared*(x + 1/2)  ;  b = shared*(2x - 1)
     *   gcd = monic(shared) = x^3 - (1/3)x^2 - 2x + 2/3.
     * a, b coefficients pre-reduced by the Python Poly / Fraction oracle. */
    const char *an[] = {"1", "-1", "-13", "1", "1"};
    const char *ad[] = {"3", "3", "6", "6", "1"};
    const char *bn[] = {"-2", "10", "-11", "-5", "2"};
    const char *bd[] = {"3", "3", "3", "3", "1"};
    hpoly_t a, b, o; size_t olen = 0u, ws;
    hpoly_set(&a, an, ad, 5); hpoly_set(&b, bn, bd, 5);
    hpoly_blank(&o, 5);
    ws = srmech_poly_gcd_ws_bound(2u, 5u); arena_ensure(ws);
    must_ok(srmech_poly_gcd(a.bn, a.bd, 5, b.bn, b.bd, 5,
                            o.bn, o.bd, &olen, arena, ws), "poly_gcd bignum");
    hpoly_sync(&o, 5);
    check_true(olen == 4, "gcd-bignum olen == 4");
    expect_coeff(&o.bn[0], &o.bd[0], "2", "3", "gcd-bignum c0");
    expect_coeff(&o.bn[1], &o.bd[1], "-2", "1", "gcd-bignum c1");
    expect_coeff(&o.bn[2], &o.bd[2], "-1", "3", "gcd-bignum c2");
    expect_coeff(&o.bn[3], &o.bd[3], "1", "1", "gcd-bignum c3");
    npass++;
}

int main(void)
{
    t_add();
    t_mul();
    t_divmod();
    t_eval();
    t_shift();
    t_rational_divmod();
    t_bignum_eval();
    t_gcd();
    t_gcd_coprime();
    t_gcd_p_zero();
    t_gcd_bignum();
    free(arena);
    printf("srmech_poly smoke: %d/%d cases PASS\n", npass, 11);
    /* NOT `assert(npass == 11)` — Release/NDEBUG strips it, and a stripped
     * count check is how a test that ran nothing still exits 0. */
    if (npass != 11) {
        fprintf(stderr, "FAIL: %d/11 cases ran\n", npass);
        return 1;
    }
    return 0;
}
