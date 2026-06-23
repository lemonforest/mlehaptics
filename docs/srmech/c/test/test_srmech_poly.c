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
 * Exit 0 on all-pass; aborts (assert) on any mismatch.
 */

#include "srmech.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ---- tiny bigint helpers for the harness (caller-owned limb buffers) ---- */

#define LCAP 4096u   /* limbs per harness bigint — far past 2^64 magnitudes */

typedef struct { uint32_t limbs[LCAP]; srmech_bigint_t bi; } hbi_t;

static void hbi_set(hbi_t *h, const char *dec)
{
    h->bi.limbs = h->limbs;
    h->bi.cap = LCAP;
    h->bi.n = 0u;
    h->bi.sign = 0;
    assert(srmech_bigint_from_dec(&h->bi, dec, strlen(dec)) == SRMECH_OK);
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
    assert(srmech_bigint_to_dec(a, buf, cap, &outlen, ws, sizeof(ws)) == SRMECH_OK);
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
    assert(n <= MAXTERMS);
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
    assert(n <= MAXTERMS);
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
        assert(arena != NULL);
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
    assert(srmech_poly_add(a.bn, a.bd, 3, b.bn, b.bd, 2,
                           o.bn, o.bd, &olen, arena, ws) == SRMECH_OK);
    hpoly_sync(&o, 3);
    assert(olen == 3);
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
    assert(srmech_poly_mul(a.bn, a.bd, 2, b.bn, b.bd, 2,
                           o.bn, o.bd, &olen, arena, ws) == SRMECH_OK);
    hpoly_sync(&o, 3);
    assert(olen == 3);
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
    assert(srmech_poly_divmod(a.bn, a.bd, 4, b.bn, b.bd, 2,
                              q.bn, q.bd, &qn, r.bn, r.bd, &rn,
                              arena, ws) == SRMECH_OK);
    hpoly_sync(&q, 3); hpoly_sync(&r, 4);
    assert(qn == 3 && rn == 1);
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
    assert(srmech_poly_eval(p.bn, p.bd, 3, &x_n.bi, &x_d.bi,
                            &o_n.bi, &o_d.bi, arena, ws) == SRMECH_OK);
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
    assert(srmech_poly_shift(p.bn, p.bd, 3, &h_n.bi, &h_d.bi,
                             o.bn, o.bd, &olen, arena, ws) == SRMECH_OK);
    hpoly_sync(&o, 3);
    assert(olen == 3);
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
    assert(srmech_poly_divmod(a.bn, a.bd, 3, b.bn, b.bd, 2,
                              q.bn, q.bd, &qn, r.bn, r.bd, &rn,
                              arena, ws) == SRMECH_OK);
    hpoly_sync(&q, 2); hpoly_sync(&r, 3);
    assert(qn == 2 && rn == 1);
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
    assert(srmech_poly_eval(p.bn, p.bd, 2, &x_n.bi, &x_d.bi,
                            &o_n.bi, &o_d.bi, arena, ws) == SRMECH_OK);
    /* expected (verified against the Python Poly / Fraction oracle):
     *   num = (10^40+1) + 2^65 * 3^30  (reduced; gcd == 1)
     *   den = 3^30 = 205891132094649 */
    expect_coeff(&o_n.bi, &o_d.bi,
                 "10000007596042041592633802526409325805569",
                 "205891132094649", "bignum eval");
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
    free(arena);
    printf("srmech_poly smoke: %d/%d cases PASS\n", npass, 7);
    assert(npass == 7);
    return 0;
}
