/*
 * srmech_sturm.c -- EXACT real-eigenvalue ISOLATION over srmech_bigint
 * (the C peer of the real-root path of
 * srmech.amsc.cascade.matrix_cascades.eigvals_exact; Qalg TAIL Batch 6).
 *
 * eigvals_exact is the exact ROOTS of the characteristic polynomial: the
 * eigenvalues of an integer matrix are ALGEBRAIC numbers, not transcendental,
 * so the Wilkinson ill-conditioning of "float root-finding from char-poly
 * coefficients" is a float artifact, NOT inherent. Kept in EXACT integer /
 * rational arithmetic the whole way -- char_poly (srmech_faddeev_leverrier,
 * rc161) -> Yun square-free factorisation (exact multiplicities) -> STURM
 * sign-sequence isolation (sign-count at rational interval boundaries) ->
 * rational BISECTION to width < 2^-bits -- the real eigenvalues come out as
 * exact isolating (lo, hi) rational intervals, well-conditioned.
 *
 * srmech_sturm_isolate(cp, n, bits, ...) takes the n+1 monic INTEGER char-poly
 * coefficients HIGH->LOW (as srmech_bigint, dens implied 1 -- the
 * srmech_faddeev_leverrier output format) and returns the real eigenvalues as
 * exact isolating rational intervals WITH multiplicity: out_lo_ / out_hi_ are
 * the reduced-fraction (num, den) endpoints, *out_count intervals total (=
 * number of real roots with multiplicity). Byte-identical to the pure-Python
 * _square_free_factors + _isolate_real_roots (the same monic factors, the same
 * Sturm chain, the same deterministic subdivision -> the same reduced-Fraction
 * endpoints). The caller sorts by lo+hi and projects to float (the single
 * terminal rotation) exactly as the pure path does.
 *
 * The algorithm composes the exact-Q srmech_poly_* kernels (gcd / divmod / eval
 * -- the same primitives the pure Poly uses) with scalar exact-Q arithmetic over
 * srmech_bigint (add / sub / mul / gcd-reduce / floor-divmod), all over the
 * caller arena `ws` (>= srmech_sturm_isolate_ws_bound; NO malloc, JPL Rule 3).
 * Each output endpoint carries >= srmech_sturm_isolate_entry_cap limbs. A
 * too-small arena / entry cap / a subdivision that exceeds the bounded stack ->
 * SRMECH_ERR_OVERFLOW, and the caller falls back to the byte-identical pure
 * Python (the parity oracle). n in [1, SRMECH_STURM_MAX_DIM].
 *
 * Class L (the spectral content) o Class C (the Sturm sign-count) o Class K (the
 * Q interval pin-slots) o Class N (the rational bisection anchors).
 *
 * Additive symbol -> ABI unchanged (stays 3). License: MIT.
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto/recursion): OK -- iterative, flat helpers
 *   - Rule 2 (bounded loops)    : OK -- bounds are degree / stack cap / bits
 *   - Rule 3 (no malloc)        : OK -- caller arena + caller out only
 *   - Rule 4 (<=60 lines/func)  : OK -- factored into static helpers
 *   - Rule 5 (>=2 asserts/fn)   : OK -- entry-pointer + pre/postcondition
 *   - Rule 7 (return-value)     : OK -- srmech_status_t propagated
 *   - Rule 8 (no multi-line mac): OK -- no function-like macros
 *   - Rule 10 (warnings clean)  : OK under -Wall -Wextra -Wpedantic -Werror
 */

#include "srmech.h"

#include <assert.h>
#include <stdint.h>

/* ---- a single exact-rational scalar (two caller-arena bigints) ------- */
typedef struct st_rat {
    srmech_bigint_t num;
    srmech_bigint_t den;
} st_rat_t;

/* ---- a polynomial: parallel num/den bigint arrays, ASCENDING degree --- */
typedef struct st_poly {
    srmech_bigint_t *num;   /* W headers */
    srmech_bigint_t *den;
    size_t len;             /* trimmed live coefficient count */
} st_poly_t;

/* ---- the working context carved from the caller arena --------------- */
typedef struct st_ctx {
    uint32_t *base;
    size_t    words;
    size_t    cur;
    uint32_t  cap;          /* per-coefficient limb capacity          */
    size_t    W;            /* coefficient slots per polynomial       */
    /* scalar scratch temporaries for the exact-Q scalar ops */
    srmech_bigint_t t0, t1, t2, t3, t4, t5;
    /* poly_ws / bigint scratch tail (shared; ops never overlap in time) */
    void  *ws;
    size_t ws_len;
} st_ctx_t;

/* ---- forward declarations (Rule 1: no recursion) -------------------- */
static uint32_t *st_take(st_ctx_t *c, size_t count);
static srmech_status_t st_bind(st_ctx_t *c, srmech_bigint_t *b);
static srmech_status_t st_carve_poly(st_ctx_t *c, st_poly_t *p);
static srmech_status_t st_rat_reduce(st_ctx_t *c, srmech_bigint_t *num,
                                     srmech_bigint_t *den);
static srmech_status_t st_rat_addsub(st_ctx_t *c, srmech_bigint_t *on,
                                     srmech_bigint_t *od,
                                     const srmech_bigint_t *an,
                                     const srmech_bigint_t *ad,
                                     const srmech_bigint_t *bn,
                                     const srmech_bigint_t *bd, int sub);
static srmech_status_t st_rat_mul(st_ctx_t *c, srmech_bigint_t *on,
                                  srmech_bigint_t *od,
                                  const srmech_bigint_t *an,
                                  const srmech_bigint_t *ad,
                                  const srmech_bigint_t *bn,
                                  const srmech_bigint_t *bd, int divide);
static srmech_status_t st_rat_cmp(st_ctx_t *c, const srmech_bigint_t *an,
                                  const srmech_bigint_t *ad,
                                  const srmech_bigint_t *bn,
                                  const srmech_bigint_t *bd, int *out);
static size_t st_poly_trim(const st_poly_t *p);
static srmech_status_t st_poly_deriv(st_ctx_t *c, st_poly_t *out,
                                     const st_poly_t *p);
static srmech_status_t st_poly_gcd(st_ctx_t *c, st_poly_t *out,
                                   const st_poly_t *a, const st_poly_t *b);
static srmech_status_t st_poly_quot(st_ctx_t *c, st_poly_t *q,
                                    st_poly_t *r, const st_poly_t *a,
                                    const st_poly_t *b);
static srmech_status_t st_poly_sub(st_ctx_t *c, st_poly_t *out,
                                   const st_poly_t *a, const st_poly_t *b);
static srmech_status_t st_poly_copy(st_poly_t *dst, const st_poly_t *src);
static srmech_status_t st_poly_eval_sign(st_ctx_t *c, const st_poly_t *p,
                                         const srmech_bigint_t *xn,
                                         const srmech_bigint_t *xd, int *sign);

/* ==================================================================== *
 * caller-arena carve (mirrors srmech_poly.c poly_take / poly_bind)
 * ==================================================================== */

static uint32_t *st_take(st_ctx_t *c, size_t count)
{
    uint32_t *p;
    assert(c != NULL);
    assert(c->cur <= c->words);
    if (count > c->words || c->cur > c->words - count) {
        return NULL;
    }
    p = c->base + c->cur;
    c->cur += count;
    return p;
}

static srmech_status_t st_bind(st_ctx_t *c, srmech_bigint_t *b)
{
    uint32_t *limbs;
    assert(c != NULL && b != NULL);
    assert(c->cap > 0u);
    limbs = st_take(c, c->cap);
    if (limbs == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    b->limbs = limbs;
    b->cap = c->cap;
    b->n = 0u;
    b->sign = 0;
    return SRMECH_OK;
}

/* Bind the six shared scalar scratch temporaries t0..t5 (cap limbs each). */
static srmech_status_t st_bind_temps(st_ctx_t *c)
{
    srmech_status_t st;
    assert(c != NULL);
    assert(c->cap > 0u);
    st = st_bind(c, &c->t0);   if (st != SRMECH_OK) { return st; }
    st = st_bind(c, &c->t1);   if (st != SRMECH_OK) { return st; }
    st = st_bind(c, &c->t2);   if (st != SRMECH_OK) { return st; }
    st = st_bind(c, &c->t3);   if (st != SRMECH_OK) { return st; }
    st = st_bind(c, &c->t4);   if (st != SRMECH_OK) { return st; }
    return st_bind(c, &c->t5);
}

/* Carve a W-wide poly (num + den header arrays + their cap-limb runs). */
static srmech_status_t st_carve_poly(st_ctx_t *c, st_poly_t *p)
{
    size_t hdr_words = (sizeof(srmech_bigint_t) + sizeof(uint32_t) - 1u)
                       / sizeof(uint32_t);
    uint32_t *hn, *hd;
    size_t k;
    srmech_status_t st;
    assert(c != NULL && p != NULL);
    assert(c->W > 0u);
    hn = st_take(c, hdr_words * c->W);
    hd = st_take(c, hdr_words * c->W);
    if (hn == NULL || hd == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    p->num = (srmech_bigint_t *)(void *)hn;
    p->den = (srmech_bigint_t *)(void *)hd;
    p->len = 0u;
    for (k = 0u; k < c->W; k++) {
        st = st_bind(c, &p->num[k]);
        if (st != SRMECH_OK) { return st; }
        st = st_bind(c, &p->den[k]);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* ==================================================================== *
 * exact-Q scalar arithmetic over the ctx temporaries + ws scratch
 * ==================================================================== */

/* Reduce num/den IN PLACE to lowest terms, positive denominator. den != 0;
 * 0/d -> 0/1. Uses t4 (gcd), t5 (divmod remainder sink) + the ws scratch. */
static srmech_status_t st_rat_reduce(st_ctx_t *c, srmech_bigint_t *num,
                                     srmech_bigint_t *den)
{
    srmech_status_t st;
    assert(c != NULL && num != NULL && den != NULL);
    assert(den->sign != 0);
    if (den->sign < 0) {
        num->sign = (num->sign == 0) ? 0 : -num->sign;
        den->sign = -den->sign;
    }
    if (srmech_bigint_is_zero(num)) {
        return srmech_bigint_set_i64(den, 1);
    }
    st = srmech_bigint_gcd(&c->t4, num, den, c->ws, c->ws_len);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_divmod(&c->t0, &c->t5, num, &c->t4, c->ws, c->ws_len);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(num, &c->t0);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_divmod(&c->t1, &c->t5, den, &c->t4, c->ws, c->ws_len);
    if (st != SRMECH_OK) { return st; }
    return srmech_bigint_copy(den, &c->t1);
}

/* out = a +/- b (exact Q), reduced. out_* must NOT alias the four inputs.
 * Uses t2 (cross product). sub != 0 selects subtraction. */
static srmech_status_t st_rat_addsub(st_ctx_t *c, srmech_bigint_t *on,
                                     srmech_bigint_t *od,
                                     const srmech_bigint_t *an,
                                     const srmech_bigint_t *ad,
                                     const srmech_bigint_t *bn,
                                     const srmech_bigint_t *bd, int sub)
{
    srmech_status_t st;
    assert(c != NULL && on != NULL && od != NULL);
    assert(an != NULL && ad != NULL && bn != NULL && bd != NULL);
    st = srmech_bigint_mul(&c->t2, an, bd);          /* t2 = an*bd */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_mul(on, bn, ad);              /* on = bn*ad */
    if (st != SRMECH_OK) { return st; }
    if (sub) {
        st = srmech_bigint_sub(od, &c->t2, on);      /* an*bd - bn*ad */
    } else {
        st = srmech_bigint_add(od, &c->t2, on);      /* an*bd + bn*ad */
    }
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(on, od);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_mul(od, ad, bd);              /* od = ad*bd */
    if (st != SRMECH_OK) { return st; }
    return st_rat_reduce(c, on, od);
}

/* out = a*b (divide == 0) or a/b (divide != 0), exact Q, reduced. out_* must
 * NOT alias the inputs. */
static srmech_status_t st_rat_mul(st_ctx_t *c, srmech_bigint_t *on,
                                  srmech_bigint_t *od,
                                  const srmech_bigint_t *an,
                                  const srmech_bigint_t *ad,
                                  const srmech_bigint_t *bn,
                                  const srmech_bigint_t *bd, int divide)
{
    srmech_status_t st;
    assert(c != NULL && on != NULL && od != NULL);
    assert(an != NULL && ad != NULL && bn != NULL && bd != NULL);
    if (divide) {
        st = srmech_bigint_mul(on, an, bd);          /* num = an*bd */
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_mul(od, ad, bn);          /* den = ad*bn */
    } else {
        st = srmech_bigint_mul(on, an, bn);          /* num = an*bn */
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_mul(od, ad, bd);          /* den = ad*bd */
    }
    if (st != SRMECH_OK) { return st; }
    if (srmech_bigint_is_zero(od)) {
        return SRMECH_ERR_BAD_INPUT;                 /* divide by zero */
    }
    return st_rat_reduce(c, on, od);
}

/* *out = sign(a - b) in {-1, 0, +1}; a, b are reduced (dens > 0). Uses t2/t3. */
static srmech_status_t st_rat_cmp(st_ctx_t *c, const srmech_bigint_t *an,
                                  const srmech_bigint_t *ad,
                                  const srmech_bigint_t *bn,
                                  const srmech_bigint_t *bd, int *out)
{
    srmech_status_t st;
    assert(c != NULL && out != NULL);
    assert(an != NULL && ad != NULL && bn != NULL && bd != NULL);
    st = srmech_bigint_mul(&c->t2, an, bd);          /* an*bd */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_mul(&c->t3, bn, ad);          /* bn*ad */
    if (st != SRMECH_OK) { return st; }
    *out = srmech_bigint_cmp(&c->t2, &c->t3);        /* dens > 0 -> order kept */
    return SRMECH_OK;
}

/* ==================================================================== *
 * polynomial glue over srmech_poly_* (byte-identical to the pure Poly)
 * ==================================================================== */

static size_t st_poly_trim(const st_poly_t *p)
{
    size_t k;
    assert(p != NULL);
    assert(p->len == 0u || p->num != NULL);
    k = p->len;
    while (k > 0u && srmech_bigint_is_zero(&p->num[k - 1u])) {
        k--;
    }
    return k;
}

/* out = d/dx p  (out[i-1] = i * p[i]); out may alias nothing live. */
static srmech_status_t st_poly_deriv(st_ctx_t *c, st_poly_t *out,
                                     const st_poly_t *p)
{
    srmech_status_t st;
    size_t i;
    assert(c != NULL && out != NULL && p != NULL);
    assert(out != p);
    if (p->len <= 1u) {                              /* derivative is 0 */
        st = srmech_bigint_set_i64(&out->num[0], 0);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_set_i64(&out->den[0], 1);
        if (st != SRMECH_OK) { return st; }
        out->len = 0u;
        return SRMECH_OK;
    }
    for (i = 1u; i < p->len; i++) {
        st = srmech_bigint_set_i64(&c->t0, (int64_t)i);   /* the integer i */
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_mul(&out->num[i - 1u], &p->num[i], &c->t0);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_copy(&out->den[i - 1u], &p->den[i]);
        if (st != SRMECH_OK) { return st; }
        st = st_rat_reduce(c, &out->num[i - 1u], &out->den[i - 1u]);
        if (st != SRMECH_OK) { return st; }
    }
    out->len = p->len - 1u;
    out->len = st_poly_trim(out);
    return SRMECH_OK;
}

/* out = monic gcd(a, b) over Q (Euclidean; srmech_poly_gcd is monic-normalized,
 * byte-identical to _poly_gcd's final monic result). */
static srmech_status_t st_poly_gcd(st_ctx_t *c, st_poly_t *out,
                                   const st_poly_t *a, const st_poly_t *b)
{
    srmech_status_t st;
    size_t olen = 0u;
    assert(c != NULL && out != NULL && a != NULL && b != NULL);
    assert(out->num != NULL);
    st = srmech_poly_gcd(a->num, a->den, a->len, b->num, b->den, b->len,
                         out->num, out->den, &olen, c->ws, c->ws_len);
    if (st != SRMECH_OK) { return st; }
    out->len = olen;
    return SRMECH_OK;
}

/* q = a // b (quotient), r = a % b (remainder) over Q. r may be NULL. */
static srmech_status_t st_poly_quot(st_ctx_t *c, st_poly_t *q,
                                    st_poly_t *r, const st_poly_t *a,
                                    const st_poly_t *b)
{
    srmech_status_t st;
    size_t ql = 0u, rl = 0u;
    srmech_bigint_t *rn, *rd;
    assert(c != NULL && q != NULL && a != NULL && b != NULL);
    assert(r != NULL);                               /* r sink required here */
    rn = r->num;
    rd = r->den;
    st = srmech_poly_divmod(a->num, a->den, a->len, b->num, b->den, b->len,
                            q->num, q->den, &ql, rn, rd, &rl,
                            c->ws, c->ws_len);
    if (st != SRMECH_OK) { return st; }
    q->len = ql;
    r->len = rl;
    return SRMECH_OK;
}

/* out = a - b (coefficientwise exact-Q, trimmed). */
static srmech_status_t st_poly_sub(st_ctx_t *c, st_poly_t *out,
                                   const st_poly_t *a, const st_poly_t *b)
{
    srmech_status_t st;
    size_t olen = 0u;
    assert(c != NULL && out != NULL && a != NULL && b != NULL);
    assert(out->num != NULL);
    st = srmech_poly_sub(a->num, a->den, a->len, b->num, b->den, b->len,
                         out->num, out->den, &olen, c->ws, c->ws_len);
    if (st != SRMECH_OK) { return st; }
    out->len = olen;
    return SRMECH_OK;
}

static srmech_status_t st_poly_copy(st_poly_t *dst, const st_poly_t *src)
{
    srmech_status_t st;
    size_t k;
    assert(dst != NULL && src != NULL);
    assert(dst->num != NULL);
    for (k = 0u; k < src->len; k++) {
        st = srmech_bigint_copy(&dst->num[k], &src->num[k]);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_copy(&dst->den[k], &src->den[k]);
        if (st != SRMECH_OK) { return st; }
    }
    dst->len = src->len;
    return SRMECH_OK;
}

/* *sign = sign of p(x) at x = xn/xd (in {-1,0,+1}); exact Horner via
 * srmech_poly_eval into t0/t1, then the reduced numerator's sign. */
static srmech_status_t st_poly_eval_sign(st_ctx_t *c, const st_poly_t *p,
                                         const srmech_bigint_t *xn,
                                         const srmech_bigint_t *xd, int *sign)
{
    srmech_status_t st;
    assert(c != NULL && p != NULL && sign != NULL);
    assert(xn != NULL && xd != NULL);
    if (p->len == 0u) { *sign = 0; return SRMECH_OK; }
    st = srmech_poly_eval(p->num, p->den, p->len, xn, xd,
                          &c->t0, &c->t1, c->ws, c->ws_len);
    if (st != SRMECH_OK) { return st; }
    *sign = c->t0.sign;                              /* den > 0 -> value's sign */
    return SRMECH_OK;
}

/* dst = |src| (Class-K magnitude pin-slot: sign forced non-negative; NEVER the
 * ALU abs -- the srmech-native sign-branch on the sign field). */
static srmech_status_t st_abs_into(srmech_bigint_t *dst,
                                   const srmech_bigint_t *src)
{
    srmech_status_t st;
    assert(dst != NULL);
    assert(src != NULL);
    st = srmech_bigint_copy(dst, src);
    if (st != SRMECH_OK) { return st; }
    if (dst->sign < 0) { dst->sign = 1; }            /* |x| = pin-slot re-sign */
    return SRMECH_OK;
}

/* ==================================================================== *
 * the working roster: every poly + scalar buffer + the interval stack
 * ==================================================================== */
typedef struct st_work {
    st_poly_t p, dp, aa, bb, cc, dd, gg, db, qq, rr;
    st_poly_t *chain;          /* maxchain wide */
    size_t     maxchain;
    /* scalar rationals for the isolation cascade */
    st_rat_t bound, eps, ra, rb, rm, ssum, sdiff, half, absn, absd;
    /* the interval stack (parallel a/b rational arrays) */
    srmech_bigint_t *stk_an, *stk_ad, *stk_bn, *stk_bd;
    size_t stackcap;
    size_t top;                /* stack pointer */
} st_work_t;

/* ---- Sturm chain: chain[0]=trim(p), chain[1]=p', then -rem(chain[k-2],
 * chain[k-1]) while the last has degree >= 1. Byte-identical to _sturm_chain.
 * *out_L = the chain length. */
static srmech_status_t st_sturm_chain(st_ctx_t *c, st_work_t *w,
                                      const st_poly_t *factor, size_t *out_L)
{
    srmech_status_t st;
    size_t L;
    assert(c != NULL && w != NULL && factor != NULL && out_L != NULL);
    assert(w->maxchain >= 2u);
    st = st_poly_copy(&w->chain[0], factor);
    if (st != SRMECH_OK) { return st; }
    w->chain[0].len = st_poly_trim(&w->chain[0]);
    st = st_poly_deriv(c, &w->chain[1], factor);
    if (st != SRMECH_OK) { return st; }
    L = 2u;
    while (w->chain[L - 1u].len > 1u) {
        size_t rl, k;
        if (L >= w->maxchain) { return SRMECH_ERR_OVERFLOW; }
        st = st_poly_quot(c, &w->qq, &w->rr, &w->chain[L - 2u],
                          &w->chain[L - 1u]);         /* _, r = divmod */
        if (st != SRMECH_OK) { return st; }
        rl = st_poly_trim(&w->rr);
        if (rl == 0u) { break; }                      /* remainder is 0 */
        for (k = 0u; k < rl; k++) {                    /* chain[L] = -r */
            st = srmech_bigint_copy(&w->chain[L].num[k], &w->rr.num[k]);
            if (st != SRMECH_OK) { return st; }
            if (w->chain[L].num[k].sign != 0) {
                w->chain[L].num[k].sign = -w->chain[L].num[k].sign;
            }
            st = srmech_bigint_copy(&w->chain[L].den[k], &w->rr.den[k]);
            if (st != SRMECH_OK) { return st; }
        }
        w->chain[L].len = rl;
        L++;
    }
    *out_L = L;
    return SRMECH_OK;
}

/* *V = the sign-variation count of a polynomial sequence at x = xn/xd: the number
 * of sign changes in the subsequence of NONZERO evaluations (zeros filtered,
 * exactly _sturm_V). Shared by the real Sturm chain + the complex Cauchy-index
 * generalised-Sturm sequence. */
static srmech_status_t st_signvar(st_ctx_t *c, const st_poly_t *polys, size_t L,
                                  const srmech_bigint_t *xn,
                                  const srmech_bigint_t *xd, int *V)
{
    srmech_status_t st;
    size_t i;
    int prev = 0, cnt = 0, s = 0;
    assert(c != NULL && polys != NULL && V != NULL);
    assert(xn != NULL && xd != NULL);
    for (i = 0u; i < L; i++) {
        st = st_poly_eval_sign(c, &polys[i], xn, xd, &s);
        if (st != SRMECH_OK) { return st; }
        if (s != 0) {
            if (prev != 0 && s != prev) { cnt++; }
            prev = s;
        }
    }
    *V = cnt;
    return SRMECH_OK;
}

/* The Sturm sign-variation count over the real chain (w->chain[0..L)). */
static srmech_status_t st_sturm_V(st_ctx_t *c, const st_work_t *w, size_t L,
                                  const srmech_bigint_t *xn,
                                  const srmech_bigint_t *xd, int *V)
{
    assert(c != NULL);
    assert(w != NULL && V != NULL);
    return st_signvar(c, w->chain, L, xn, xd, V);
}

/* rm = (ra + rb) / 2 (exact-Q midpoint). */
static srmech_status_t st_midpoint(st_ctx_t *c, st_work_t *w,
                                   const st_rat_t *ra, const st_rat_t *rb)
{
    srmech_status_t st;
    assert(c != NULL);
    assert(w != NULL && ra != NULL && rb != NULL);
    st = st_rat_addsub(c, &w->ssum.num, &w->ssum.den, &ra->num, &ra->den,
                       &rb->num, &rb->den, 0);
    if (st != SRMECH_OK) { return st; }
    return st_rat_mul(c, &w->rm.num, &w->rm.den, &w->ssum.num, &w->ssum.den,
                      &w->half.num, &w->half.den, 0);   /* * 1/2 */
}

static srmech_status_t st_rat_copy(st_rat_t *dst, const st_rat_t *src)
{
    srmech_status_t st;
    assert(dst != NULL);
    assert(src != NULL);
    st = srmech_bigint_copy(&dst->num, &src->num);
    if (st != SRMECH_OK) { return st; }
    return srmech_bigint_copy(&dst->den, &src->den);
}

/* w->bound = 1 + max_{i < deg}( |g[i]| / |g_lead| ) -- the Cauchy root bound,
 * exact-Q, Class-K magnitude (never abs()). Byte-identical to _isolate_real_roots'
 * `1 + max(mag(c)/lead for c in factor[:-1])`. */
static srmech_status_t st_factor_bound(st_ctx_t *c, st_work_t *w,
                                       const st_poly_t *g)
{
    srmech_status_t st;
    size_t i, glen = g->len;
    int cmp = 0;
    assert(c != NULL && w != NULL && g != NULL);
    assert(glen >= 1u);
    st = st_abs_into(&w->absd.num, &g->num[glen - 1u]);       /* |lead| */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&w->absd.den, &g->den[glen - 1u]);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&w->bound.num, 0);            /* max acc = 0/1 */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&w->bound.den, 1);
    if (st != SRMECH_OK) { return st; }
    for (i = 0u; i + 1u < glen; i++) {
        st = st_abs_into(&w->absn.num, &g->num[i]);          /* |c| */
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_copy(&w->absn.den, &g->den[i]);
        if (st != SRMECH_OK) { return st; }
        st = st_rat_mul(c, &w->ssum.num, &w->ssum.den, &w->absn.num,
                        &w->absn.den, &w->absd.num, &w->absd.den, 1); /* /|lead| */
        if (st != SRMECH_OK) { return st; }
        st = st_rat_cmp(c, &w->ssum.num, &w->ssum.den, &w->bound.num,
                        &w->bound.den, &cmp);
        if (st != SRMECH_OK) { return st; }
        if (cmp > 0) {
            st = st_rat_copy(&w->bound, &w->ssum);
            if (st != SRMECH_OK) { return st; }
        }
    }
    st = srmech_bigint_set_i64(&w->sdiff.num, 1);           /* the +1 */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&w->sdiff.den, 1);
    if (st != SRMECH_OK) { return st; }
    st = st_rat_addsub(c, &w->rm.num, &w->rm.den, &w->bound.num, &w->bound.den,
                       &w->sdiff.num, &w->sdiff.den, 0);
    if (st != SRMECH_OK) { return st; }
    return st_rat_copy(&w->bound, &w->rm);
}

/* Refine the isolating interval (w->ra, w->rb) -- guaranteed to hold exactly ONE
 * root -- to width <= eps by root-free bisection, IN PLACE. Byte-identical to
 * `while b-a > eps: m=(a+b)/2; if V(a)-V(m)==1: b=m else a=m`. */
static srmech_status_t st_bisect(st_ctx_t *c, st_work_t *w, size_t L)
{
    srmech_status_t st;
    size_t guard = 0u, guard_max;
    int cmp = 0, va = 0, vm = 0;
    assert(c != NULL && w != NULL);
    assert(L >= 1u);
    guard_max = (size_t)0u + w->bound.num.n * 32u + 4096u;
    while (guard <= guard_max) {
        st = st_rat_addsub(c, &w->sdiff.num, &w->sdiff.den, &w->rb.num,
                           &w->rb.den, &w->ra.num, &w->ra.den, 1);  /* b - a */
        if (st != SRMECH_OK) { return st; }
        st = st_rat_cmp(c, &w->sdiff.num, &w->sdiff.den, &w->eps.num,
                        &w->eps.den, &cmp);
        if (st != SRMECH_OK) { return st; }
        if (cmp <= 0) { break; }                             /* b - a <= eps */
        st = st_midpoint(c, w, &w->ra, &w->rb);              /* rm = (a+b)/2 */
        if (st != SRMECH_OK) { return st; }
        st = st_sturm_V(c, w, L, &w->ra.num, &w->ra.den, &va);
        if (st != SRMECH_OK) { return st; }
        st = st_sturm_V(c, w, L, &w->rm.num, &w->rm.den, &vm);
        if (st != SRMECH_OK) { return st; }
        if (va - vm == 1) {
            st = st_rat_copy(&w->rb, &w->rm);                /* b = m */
        } else {
            st = st_rat_copy(&w->ra, &w->rm);                /* a = m */
        }
        if (st != SRMECH_OK) { return st; }
        guard++;
    }
    return SRMECH_OK;
}

/* Push the interval (an/ad, bn/bd) onto the subdivision stack (a deep copy). */
static srmech_status_t st_stack_push(st_work_t *w, const st_rat_t *a,
                                     const st_rat_t *b)
{
    srmech_status_t st;
    size_t t = w->top;
    assert(w != NULL);
    assert(a != NULL && b != NULL);
    if (t >= w->stackcap) { return SRMECH_ERR_OVERFLOW; }
    st = srmech_bigint_copy(&w->stk_an[t], &a->num);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&w->stk_ad[t], &a->den);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&w->stk_bn[t], &b->num);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&w->stk_bd[t], &b->den);
    if (st != SRMECH_OK) { return st; }
    w->top = t + 1u;
    return SRMECH_OK;
}

/* Pop the top interval into (w->ra, w->rb). Caller ensures top > 0. */
static srmech_status_t st_stack_pop(st_work_t *w)
{
    srmech_status_t st;
    size_t t;
    assert(w != NULL);
    assert(w->top > 0u);
    t = w->top - 1u;
    st = srmech_bigint_copy(&w->ra.num, &w->stk_an[t]);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&w->ra.den, &w->stk_ad[t]);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&w->rb.num, &w->stk_bn[t]);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&w->rb.den, &w->stk_bd[t]);
    if (st != SRMECH_OK) { return st; }
    w->top = t;
    return SRMECH_OK;
}

/* Emit the isolating interval (w->ra, w->rb) `mult` times into the caller output
 * arrays (mirrors `for _ in range(mult): eigs.append((lo, hi))`). */
static srmech_status_t st_emit(st_work_t *w, size_t mult, size_t out_cap,
                               srmech_bigint_t *lon, srmech_bigint_t *lod,
                               srmech_bigint_t *hin, srmech_bigint_t *hid,
                               size_t *count)
{
    srmech_status_t st;
    size_t j;
    assert(w != NULL && count != NULL && lon != NULL);
    assert(lod != NULL && hin != NULL && hid != NULL);
    for (j = 0u; j < mult; j++) {
        size_t k = *count;
        if (k >= out_cap) { return SRMECH_ERR_OVERFLOW; }
        st = srmech_bigint_copy(&lon[k], &w->ra.num);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_copy(&lod[k], &w->ra.den);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_copy(&hin[k], &w->rb.num);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_copy(&hid[k], &w->rb.den);
        if (st != SRMECH_OK) { return st; }
        *count = k + 1u;
    }
    return SRMECH_OK;
}

/* Isolate the distinct real roots of the monic square-free factor `g` and bisect
 * each to width < 2^-bits, emitting each isolating interval `mult` times. The
 * Sturm chain must already be built (length L) for `g`. */
static srmech_status_t st_isolate_factor(st_ctx_t *c, st_work_t *w, size_t L,
                                         size_t mult, size_t out_cap,
                                         srmech_bigint_t *lon,
                                         srmech_bigint_t *lod,
                                         srmech_bigint_t *hin,
                                         srmech_bigint_t *hid, size_t *count)
{
    srmech_status_t st;
    int va = 0, vb = 0, cnt;
    assert(c != NULL && w != NULL && count != NULL);
    assert(L >= 1u);
    /* seed the stack with (-bound, bound): absn = -bound. */
    st = st_rat_copy(&w->absn, &w->bound);
    if (st != SRMECH_OK) { return st; }
    if (w->absn.num.sign != 0) { w->absn.num.sign = -w->absn.num.sign; }
    w->top = 0u;
    st = st_stack_push(w, &w->absn, &w->bound);
    if (st != SRMECH_OK) { return st; }
    while (w->top > 0u) {
        st = st_stack_pop(w);
        if (st != SRMECH_OK) { return st; }
        st = st_sturm_V(c, w, L, &w->ra.num, &w->ra.den, &va);
        if (st != SRMECH_OK) { return st; }
        st = st_sturm_V(c, w, L, &w->rb.num, &w->rb.den, &vb);
        if (st != SRMECH_OK) { return st; }
        cnt = va - vb;
        if (cnt == 0) { continue; }
        if (cnt == 1) {
            st = st_bisect(c, w, L);
            if (st != SRMECH_OK) { return st; }
            st = st_emit(w, mult, out_cap, lon, lod, hin, hid, count);
            if (st != SRMECH_OK) { return st; }
        } else {
            st = st_midpoint(c, w, &w->ra, &w->rb);          /* m = (a+b)/2 */
            if (st != SRMECH_OK) { return st; }
            st = st_stack_push(w, &w->ra, &w->rm);           /* (a, m) */
            if (st != SRMECH_OK) { return st; }
            st = st_stack_push(w, &w->rm, &w->rb);           /* (m, b) */
            if (st != SRMECH_OK) { return st; }
        }
    }
    return SRMECH_OK;
}

/* ==================================================================== *
 * dimensioning + arena carve
 * ==================================================================== */

#define STURM_HDR_WORDS  ((sizeof(srmech_bigint_t) + 3u) / sizeof(uint32_t))
#define STURM_PHDR_WORDS ((sizeof(st_poly_t) + 3u) / sizeof(uint32_t))

/* Per-coefficient limb cap + geometry, from the input coeff magnitude, n, bits.
 * cap covers: the exact-Q gcd/Sturm chain coefficient growth (linear-in-degree
 * envelope, MONIC-normalized) + the Horner evaluation denominator growth
 * (x_den^deg = 2^(bits*deg)) + slack. A genuinely-larger case that outgrows cap
 * returns SRMECH_ERR_OVERFLOW mid-op -> the byte-identical pure fallback. */
static void st_dims(size_t coeff_limbs, size_t n, uint32_t bits,
                    uint32_t *cap, size_t *W, size_t *maxchain,
                    size_t *stackcap)
{
    size_t base = coeff_limbs + 1u;
    size_t bit_growth = ((size_t)bits / 32u + 2u) * (n + 2u);
    size_t cc = base * (n + 4u) * 3u + bit_growth + 128u;
    assert(cap != NULL && W != NULL);
    assert(maxchain != NULL && stackcap != NULL);
    *cap = (uint32_t)cc;
    *W = n + 2u;
    *maxchain = n + 3u;
    *stackcap = 8u * (n + 2u) + 256u;
}

/* Carve `count` cap-limb srmech_bigint (header array + limb runs) from the arena
 * -> *out points at the header array. */
static srmech_status_t st_carve_bi_array(st_ctx_t *c, srmech_bigint_t **out,
                                         size_t count)
{
    uint32_t *h;
    srmech_bigint_t *arr;
    size_t k;
    srmech_status_t st;
    assert(c != NULL && out != NULL);
    assert(count > 0u);
    h = st_take(c, STURM_HDR_WORDS * count);
    if (h == NULL) { return SRMECH_ERR_OVERFLOW; }
    arr = (srmech_bigint_t *)(void *)h;
    for (k = 0u; k < count; k++) {
        st = st_bind(c, &arr[k]);
        if (st != SRMECH_OK) { return st; }
    }
    *out = arr;
    return SRMECH_OK;
}

static srmech_status_t st_bind_rat(st_ctx_t *c, st_rat_t *r)
{
    srmech_status_t st;
    assert(c != NULL);
    assert(r != NULL);
    st = st_bind(c, &r->num);
    if (st != SRMECH_OK) { return st; }
    return st_bind(c, &r->den);
}

/* Carve the 10 named working polynomials + the maxchain Sturm-chain buffers. */
static srmech_status_t st_carve_polys(st_ctx_t *c, st_work_t *w)
{
    st_poly_t *pv[10];
    uint32_t *h;
    size_t i;
    srmech_status_t st;
    assert(c != NULL && w != NULL);
    assert(w->maxchain >= 2u);
    pv[0] = &w->p; pv[1] = &w->dp; pv[2] = &w->aa; pv[3] = &w->bb;
    pv[4] = &w->cc; pv[5] = &w->dd; pv[6] = &w->gg; pv[7] = &w->db;
    pv[8] = &w->qq; pv[9] = &w->rr;
    for (i = 0u; i < 10u; i++) {
        st = st_carve_poly(c, pv[i]);
        if (st != SRMECH_OK) { return st; }
    }
    h = st_take(c, STURM_PHDR_WORDS * w->maxchain);
    if (h == NULL) { return SRMECH_ERR_OVERFLOW; }
    w->chain = (st_poly_t *)(void *)h;
    for (i = 0u; i < w->maxchain; i++) {
        st = st_carve_poly(c, &w->chain[i]);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* Carve the 10 scalar rationals + the four interval-stack bigint arrays. */
static srmech_status_t st_carve_rats_stack(st_ctx_t *c, st_work_t *w)
{
    st_rat_t *rv[10];
    size_t i;
    srmech_status_t st;
    assert(c != NULL && w != NULL);
    assert(w->stackcap > 0u);
    rv[0] = &w->bound; rv[1] = &w->eps; rv[2] = &w->ra; rv[3] = &w->rb;
    rv[4] = &w->rm; rv[5] = &w->ssum; rv[6] = &w->sdiff; rv[7] = &w->half;
    rv[8] = &w->absn; rv[9] = &w->absd;
    for (i = 0u; i < 10u; i++) {
        st = st_bind_rat(c, rv[i]);
        if (st != SRMECH_OK) { return st; }
    }
    st = st_carve_bi_array(c, &w->stk_an, w->stackcap);
    if (st != SRMECH_OK) { return st; }
    st = st_carve_bi_array(c, &w->stk_ad, w->stackcap);
    if (st != SRMECH_OK) { return st; }
    st = st_carve_bi_array(c, &w->stk_bn, w->stackcap);
    if (st != SRMECH_OK) { return st; }
    return st_carve_bi_array(c, &w->stk_bd, w->stackcap);
}

/* The Yun square-free factorisation fused with the per-factor Sturm isolation
 * (mirrors _square_free_factors + the eigvals_exact real loop). Each square-free
 * factor of multiplicity k has its distinct real roots isolated + each emitted
 * k times. p (w->p) must already carry the low->high monic polynomial. */
static srmech_status_t st_squarefree_driver(st_ctx_t *c, st_work_t *w,
                                            size_t n, size_t out_cap,
                                            srmech_bigint_t *lon,
                                            srmech_bigint_t *lod,
                                            srmech_bigint_t *hin,
                                            srmech_bigint_t *hid,
                                            size_t *count)
{
    srmech_status_t st;
    size_t k = 1u, L = 0u;
    assert(c != NULL && w != NULL && count != NULL);
    assert(w->p.num != NULL);
    st = st_poly_deriv(c, &w->dp, &w->p);                    /* dp = p'      */
    if (st != SRMECH_OK) { return st; }
    st = st_poly_gcd(c, &w->aa, &w->p, &w->dp);              /* a = gcd(p,p') */
    if (st != SRMECH_OK) { return st; }
    st = st_poly_quot(c, &w->bb, &w->rr, &w->p, &w->aa);     /* b = p // a    */
    if (st != SRMECH_OK) { return st; }
    st = st_poly_quot(c, &w->cc, &w->rr, &w->dp, &w->aa);    /* c = p' // a   */
    if (st != SRMECH_OK) { return st; }
    st = st_poly_deriv(c, &w->db, &w->bb);
    if (st != SRMECH_OK) { return st; }
    st = st_poly_sub(c, &w->dd, &w->cc, &w->db);             /* d = c - b'    */
    if (st != SRMECH_OK) { return st; }
    while (w->bb.len > 1u) {
        if (k > n + 2u) { return SRMECH_ERR_OVERFLOW; }      /* Rule 2 guard  */
        st = st_poly_gcd(c, &w->gg, &w->bb, &w->dd);         /* g = gcd(b,d)  */
        if (st != SRMECH_OK) { return st; }
        if (w->gg.len > 1u) {                                /* a real factor */
            st = st_sturm_chain(c, w, &w->gg, &L);
            if (st != SRMECH_OK) { return st; }
            st = st_factor_bound(c, w, &w->gg);
            if (st != SRMECH_OK) { return st; }
            st = st_isolate_factor(c, w, L, k, out_cap, lon, lod, hin, hid,
                                   count);
            if (st != SRMECH_OK) { return st; }
        }
        st = st_poly_quot(c, &w->qq, &w->rr, &w->bb, &w->gg);/* b //= g       */
        if (st != SRMECH_OK) { return st; }
        st = st_poly_copy(&w->bb, &w->qq);
        if (st != SRMECH_OK) { return st; }
        st = st_poly_quot(c, &w->qq, &w->rr, &w->dd, &w->gg);/* c = d // g    */
        if (st != SRMECH_OK) { return st; }
        st = st_poly_copy(&w->cc, &w->qq);
        if (st != SRMECH_OK) { return st; }
        st = st_poly_deriv(c, &w->db, &w->bb);
        if (st != SRMECH_OK) { return st; }
        st = st_poly_sub(c, &w->dd, &w->cc, &w->db);         /* d = c - b'    */
        if (st != SRMECH_OK) { return st; }
        k++;
    }
    return SRMECH_OK;
}

/* Load the low->high monic polynomial into w->p from the HIGH->LOW integer
 * char-poly `cp` (n+1 coefficients, dens implied 1), and set eps = 1/2^bits +
 * half = 1/2. */
static srmech_status_t st_load_inputs(st_ctx_t *c, st_work_t *w,
                                      const srmech_bigint_t *cp, size_t n,
                                      uint32_t bits)
{
    srmech_status_t st;
    size_t i;
    assert(c != NULL && w != NULL && cp != NULL);
    assert(w->p.num != NULL);
    for (i = 0u; i <= n; i++) {                              /* p[i] = cp[n-i] */
        st = srmech_bigint_copy(&w->p.num[i], &cp[n - i]);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_set_i64(&w->p.den[i], 1);
        if (st != SRMECH_OK) { return st; }
    }
    w->p.len = n + 1u;
    w->p.len = st_poly_trim(&w->p);
    st = srmech_bigint_set_i64(&w->eps.num, 1);              /* eps = 1/2^bits */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&c->t0, 1);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_shl_bits(&w->eps.den, &c->t0, bits);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&w->half.num, 1);             /* half = 1/2 */
    if (st != SRMECH_OK) { return st; }
    return srmech_bigint_set_i64(&w->half.den, 2);
}

/* ==================================================================== *
 * public API
 * ==================================================================== */

size_t srmech_sturm_isolate_entry_cap(size_t coeff_limbs, size_t n,
                                      uint32_t bits)
{
    uint32_t cap;
    size_t W, maxchain, stackcap;
    st_dims(coeff_limbs == 0u ? 1u : coeff_limbs, n == 0u ? 1u : n, bits,
            &cap, &W, &maxchain, &stackcap);
    assert(cap > 0u);
    assert(W > 0u);
    return (size_t)cap;
}

size_t srmech_sturm_isolate_ws_bound(size_t coeff_limbs, size_t n, uint32_t bits)
{
    uint32_t cap;
    size_t W, maxchain, stackcap, per_poly, n_polys, persistent, tail;
    st_dims(coeff_limbs == 0u ? 1u : coeff_limbs, n == 0u ? 1u : n, bits,
            &cap, &W, &maxchain, &stackcap);
    assert(cap > 0u);
    assert(W > 0u);
    per_poly = 2u * W * STURM_HDR_WORDS + 2u * W * (size_t)cap;
    n_polys = 10u + maxchain;
    persistent = n_polys * per_poly                       /* poly buffers      */
               + maxchain * STURM_PHDR_WORDS              /* chain st_poly_t[]  */
               + 10u * 2u * (size_t)cap                   /* scalar rationals   */
               + 6u * (size_t)cap                         /* scalar temps       */
               + 4u * stackcap * STURM_HDR_WORDS          /* stack headers      */
               + 4u * stackcap * (size_t)cap              /* stack limbs        */
               + 256u;                                    /* slack              */
    tail = srmech_poly_gcd_ws_bound((size_t)cap, W);      /* heaviest poly ws   */
    return persistent * sizeof(uint32_t) + tail + 64u;
}

srmech_status_t srmech_sturm_isolate(const srmech_bigint_t *cp, int n,
                                     uint32_t bits,
                                     srmech_bigint_t *out_lo_n,
                                     srmech_bigint_t *out_lo_d,
                                     srmech_bigint_t *out_hi_n,
                                     srmech_bigint_t *out_hi_d,
                                     size_t *out_count, void *ws, size_t ws_len)
{
    st_ctx_t c;
    st_work_t w;
    srmech_status_t st;
    size_t coeff_limbs = 1u, i, W, maxchain, stackcap, tail;
    uint32_t cap;
    assert(cp != NULL && out_count != NULL && ws != NULL);
    assert(out_lo_n != NULL && out_hi_n != NULL);
    if (cp == NULL || out_lo_n == NULL || out_lo_d == NULL || out_hi_n == NULL
        || out_hi_d == NULL || out_count == NULL || ws == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n < 1 || n > SRMECH_STURM_MAX_DIM) { return SRMECH_ERR_BAD_INPUT; }
    *out_count = 0u;
    for (i = 0u; i <= (size_t)n; i++) {
        if (cp[i].n > coeff_limbs) { coeff_limbs = cp[i].n; }
    }
    st_dims(coeff_limbs, (size_t)n, bits, &cap, &W, &maxchain, &stackcap);
    if (cap > 0x0FFFFFFFu) { return SRMECH_ERR_OVERFLOW; }   /* absurd growth */
    w.maxchain = maxchain;
    w.stackcap = stackcap;
    w.top = 0u;
    c.base = (uint32_t *)ws;
    c.words = ws_len / sizeof(uint32_t);
    c.cur = 0u;
    c.cap = cap;
    c.W = W;
    st = st_bind(&c, &c.t0);  if (st != SRMECH_OK) { return st; }
    st = st_bind(&c, &c.t1);  if (st != SRMECH_OK) { return st; }
    st = st_bind(&c, &c.t2);  if (st != SRMECH_OK) { return st; }
    st = st_bind(&c, &c.t3);  if (st != SRMECH_OK) { return st; }
    st = st_bind(&c, &c.t4);  if (st != SRMECH_OK) { return st; }
    st = st_bind(&c, &c.t5);  if (st != SRMECH_OK) { return st; }
    st = st_carve_polys(&c, &w);       if (st != SRMECH_OK) { return st; }
    st = st_carve_rats_stack(&c, &w);  if (st != SRMECH_OK) { return st; }
    tail = srmech_poly_gcd_ws_bound((size_t)cap, W);
    if ((c.words - c.cur) * sizeof(uint32_t) < tail) { return SRMECH_ERR_OVERFLOW; }
    c.ws = (void *)(c.base + c.cur);
    c.ws_len = (c.words - c.cur) * sizeof(uint32_t);
    st = st_load_inputs(&c, &w, cp, (size_t)n, bits);
    if (st != SRMECH_OK) { return st; }
    st = st_squarefree_driver(&c, &w, (size_t)n, (size_t)n, out_lo_n, out_lo_d,
                              out_hi_n, out_hi_d, out_count);
    return st;
}




/* ==================================================================== *
 * COMPLEX-root isolation: the exact argument-principle box certifier +
 * pure rational-box subdivision (the C peer of the include_complex path of
 * eigvals_exact: _count_roots_in_box + _isolate_complex_roots_upper).
 * ==================================================================== */

/* The box-certifier working roster: the per-edge U(t)+iV(t) accumulation polys +
 * the generalised-Sturm sequence + the box-delta / eval-point scalars. */
typedef struct st_bctx {
    st_poly_t ea, eb, powU, powV, uU, uV, csc, tmpA, pmt1, pmt2, tra, trb;
    st_poly_t *seq;             /* generalised Sturm seq (maxseq wide) */
    size_t     maxseq;
    st_rat_t w1, h1, nw1, nh1, zero, one;   /* box deltas + eval points 0/1 */
} st_bctx_t;

/* out = a + b over Q, trimmed (the poly-add sibling of st_poly_sub). */
static srmech_status_t st_poly_add(st_ctx_t *c, st_poly_t *out,
                                   const st_poly_t *a, const st_poly_t *b)
{
    srmech_status_t st;
    size_t olen = 0u;
    assert(c != NULL && out != NULL && a != NULL && b != NULL);
    assert(out->num != NULL);
    st = srmech_poly_add(a->num, a->den, a->len, b->num, b->den, b->len,
                         out->num, out->den, &olen, c->ws, c->ws_len);
    if (st != SRMECH_OK) { return st; }
    out->len = olen;
    return SRMECH_OK;
}

/* out = a * b (coefficient convolution) over Q, trimmed. */
static srmech_status_t st_poly_mul(st_ctx_t *c, st_poly_t *out,
                                   const st_poly_t *a, const st_poly_t *b)
{
    srmech_status_t st;
    size_t olen = 0u;
    assert(c != NULL && out != NULL && a != NULL && b != NULL);
    assert(out->num != NULL);
    st = srmech_poly_mul(a->num, a->den, a->len, b->num, b->den, b->len,
                         out->num, out->den, &olen, c->ws, c->ws_len);
    if (st != SRMECH_OK) { return st; }
    out->len = olen;
    return SRMECH_OK;
}

/* out = (sn/sd) * p (scale a polynomial by a scalar rational), trimmed. out must
 * not alias p. */
static srmech_status_t st_poly_scale(st_ctx_t *c, st_poly_t *out,
                                     const st_poly_t *p,
                                     const srmech_bigint_t *sn,
                                     const srmech_bigint_t *sd)
{
    srmech_status_t st;
    size_t k;
    assert(c != NULL && out != NULL && p != NULL);
    assert(out != p && sn != NULL && sd != NULL);
    for (k = 0u; k < p->len; k++) {
        st = st_rat_mul(c, &out->num[k], &out->den[k], &p->num[k], &p->den[k],
                        sn, sd, 0);
        if (st != SRMECH_OK) { return st; }
    }
    out->len = p->len;
    out->len = st_poly_trim(out);
    return SRMECH_OK;
}

/* Set a degree-<=1 polynomial to [c0, c1] (c1 == 0 -> degree 0), trimmed. */
static srmech_status_t st_poly_set_lin(st_poly_t *p,
                                       const srmech_bigint_t *c0n,
                                       const srmech_bigint_t *c0d,
                                       const srmech_bigint_t *c1n,
                                       const srmech_bigint_t *c1d)
{
    srmech_status_t st;
    assert(p != NULL && c0n != NULL && c1n != NULL);
    assert(p->num != NULL);
    st = srmech_bigint_copy(&p->num[0], c0n);   if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&p->den[0], c0d);   if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&p->num[1], c1n);   if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&p->den[1], c1d);   if (st != SRMECH_OK) { return st; }
    p->len = 2u;
    p->len = st_poly_trim(p);
    return SRMECH_OK;
}

/* (powU, powV) <- (powU*ea - powV*eb, powU*eb + powV*ea): complex multiply of the
 * running z^k accumulator by z(t) = ea + i*eb. */
static srmech_status_t st_cmul_step(st_ctx_t *c, st_bctx_t *b)
{
    srmech_status_t st;
    assert(c != NULL && b != NULL);
    assert(b->powU.num != NULL);
    st = st_poly_mul(c, &b->pmt1, &b->powU, &b->ea);       /* powU*ea */
    if (st != SRMECH_OK) { return st; }
    st = st_poly_mul(c, &b->pmt2, &b->powV, &b->eb);       /* powV*eb */
    if (st != SRMECH_OK) { return st; }
    st = st_poly_sub(c, &b->tra, &b->pmt1, &b->pmt2);      /* real part */
    if (st != SRMECH_OK) { return st; }
    st = st_poly_mul(c, &b->pmt1, &b->powU, &b->eb);       /* powU*eb */
    if (st != SRMECH_OK) { return st; }
    st = st_poly_mul(c, &b->pmt2, &b->powV, &b->ea);       /* powV*ea */
    if (st != SRMECH_OK) { return st; }
    st = st_poly_add(c, &b->trb, &b->pmt1, &b->pmt2);      /* imag part */
    if (st != SRMECH_OK) { return st; }
    st = st_poly_copy(&b->powU, &b->tra);
    if (st != SRMECH_OK) { return st; }
    return st_poly_copy(&b->powV, &b->trb);
}

/* One accumulation step: U += p[k]*powU ; V += p[k]*powV. */
static srmech_status_t st_edge_accum(st_ctx_t *c, st_bctx_t *b,
                                     const srmech_bigint_t *cn,
                                     const srmech_bigint_t *cd)
{
    srmech_status_t st;
    assert(c != NULL && b != NULL && cn != NULL && cd != NULL);
    assert(b->uU.num != NULL);
    st = st_poly_scale(c, &b->csc, &b->powU, cn, cd);      /* c*powU */
    if (st != SRMECH_OK) { return st; }
    st = st_poly_add(c, &b->tmpA, &b->uU, &b->csc);
    if (st != SRMECH_OK) { return st; }
    st = st_poly_copy(&b->uU, &b->tmpA);
    if (st != SRMECH_OK) { return st; }
    st = st_poly_scale(c, &b->csc, &b->powV, cn, cd);      /* c*powV */
    if (st != SRMECH_OK) { return st; }
    st = st_poly_add(c, &b->tmpA, &b->uV, &b->csc);
    if (st != SRMECH_OK) { return st; }
    return st_poly_copy(&b->uV, &b->tmpA);
}

/* Substitute z(t) = (x0 + dx*t) + i*(y0 + dy*t) into `p` (low->high) and build
 * b->uU + i*b->uV = p(z(t)) in Q[t] (exactly _poly_real_imag_on_edge). */
static srmech_status_t st_edge_uv(st_ctx_t *c, st_bctx_t *b, const st_poly_t *p,
                                  const st_rat_t *x0, const st_rat_t *y0,
                                  const st_rat_t *dx, const st_rat_t *dy)
{
    srmech_status_t st;
    size_t k;
    assert(c != NULL && b != NULL && p != NULL);
    assert(x0 != NULL && y0 != NULL && dx != NULL && dy != NULL);
    st = st_poly_set_lin(&b->ea, &x0->num, &x0->den, &dx->num, &dx->den);
    if (st != SRMECH_OK) { return st; }
    st = st_poly_set_lin(&b->eb, &y0->num, &y0->den, &dy->num, &dy->den);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&b->powU.num[0], 1);        /* powU = 1 */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&b->powU.den[0], 1);
    if (st != SRMECH_OK) { return st; }
    b->powU.len = 1u;
    b->powV.len = 0u;                                      /* powV = 0 */
    b->uU.len = 0u;                                        /* U = 0 */
    b->uV.len = 0u;                                        /* V = 0 */
    for (k = 0u; k < p->len; k++) {
        st = st_edge_accum(c, b, &p->num[k], &p->den[k]);
        if (st != SRMECH_OK) { return st; }
        st = st_cmul_step(c, b);
        if (st != SRMECH_OK) { return st; }
    }
    b->uU.len = st_poly_trim(&b->uU);
    b->uV.len = st_poly_trim(&b->uV);
    return SRMECH_OK;
}

/* Build the generalised Sturm (remainder) sequence starting (f, g) into b->seq;
 * *out_S <- its length. seq[0]=f, seq[1]=g, seq[k+1] = -rem(seq[k-1], seq[k]),
 * until the remainder is 0 (exactly _sturm_seq_general). */
static srmech_status_t st_seq_general(st_ctx_t *c, st_bctx_t *b,
                                      const st_poly_t *f, const st_poly_t *g,
                                      size_t *out_S)
{
    srmech_status_t st;
    size_t S;
    assert(c != NULL && b != NULL && f != NULL && g != NULL && out_S != NULL);
    assert(b->maxseq >= 2u);
    st = st_poly_copy(&b->seq[0], f);   if (st != SRMECH_OK) { return st; }
    b->seq[0].len = st_poly_trim(&b->seq[0]);
    st = st_poly_copy(&b->seq[1], g);   if (st != SRMECH_OK) { return st; }
    b->seq[1].len = st_poly_trim(&b->seq[1]);
    S = 2u;
    while (b->seq[S - 1u].len > 0u) {
        size_t rl, k;
        if (S >= b->maxseq) { return SRMECH_ERR_OVERFLOW; }
        st = st_poly_quot(c, &b->pmt1, &b->pmt2, &b->seq[S - 2u],
                          &b->seq[S - 1u]);                /* _, r = divmod */
        if (st != SRMECH_OK) { return st; }
        rl = st_poly_trim(&b->pmt2);
        if (rl == 0u) { break; }
        for (k = 0u; k < rl; k++) {                        /* seq[S] = -r */
            st = srmech_bigint_copy(&b->seq[S].num[k], &b->pmt2.num[k]);
            if (st != SRMECH_OK) { return st; }
            if (b->seq[S].num[k].sign != 0) {
                b->seq[S].num[k].sign = -b->seq[S].num[k].sign;
            }
            st = srmech_bigint_copy(&b->seq[S].den[k], &b->pmt2.den[k]);
            if (st != SRMECH_OK) { return st; }
        }
        b->seq[S].len = rl;
        S++;
    }
    *out_S = S;
    return SRMECH_OK;
}

/* One edge's contribution to the winding: substitute z(t) along the edge, then
 * *idx <- the Cauchy index I(V/U) over (0,1) = signvar(seq,0) - signvar(seq,1).
 * *degen set to 1 when p vanishes on the whole edge (U == V == 0). */
static srmech_status_t st_box_edge_index(st_ctx_t *c, st_bctx_t *b,
                                         const st_poly_t *p, const st_rat_t *xs,
                                         const st_rat_t *ys, const st_rat_t *dx,
                                         const st_rat_t *dy, int *idx, int *degen)
{
    srmech_status_t st;
    size_t S = 0u;
    int v0 = 0, v1 = 0;
    assert(c != NULL && b != NULL && p != NULL && idx != NULL && degen != NULL);
    assert(xs != NULL && ys != NULL);
    st = st_edge_uv(c, b, p, xs, ys, dx, dy);
    if (st != SRMECH_OK) { return st; }
    if (b->uU.len == 0u && b->uV.len == 0u) { *degen = 1; return SRMECH_OK; }
    st = st_seq_general(c, b, &b->uU, &b->uV, &S);
    if (st != SRMECH_OK) { return st; }
    st = st_signvar(c, b->seq, S, &b->zero.num, &b->zero.den, &v0);
    if (st != SRMECH_OK) { return st; }
    st = st_signvar(c, b->seq, S, &b->one.num, &b->one.den, &v1);
    if (st != SRMECH_OK) { return st; }
    *idx = v0 - v1;
    return SRMECH_OK;
}

/* The number of roots of `p` (low->high, over Q) STRICTLY inside the open box
 * (x0,x1) x (y0,y1) by the exact argument principle (winding = -1/2 sum of the
 * per-edge Cauchy indices). *count <- the count; *degenerate <- 1 when a corner /
 * edge hits a root (the caller nudges) -- mirrors _count_roots_in_box's ValueError. */
static srmech_status_t st_box_count(st_ctx_t *c, st_bctx_t *b, const st_poly_t *p,
                                    const st_rat_t *x0, const st_rat_t *x1,
                                    const st_rat_t *y0, const st_rat_t *y1,
                                    int *count, int *degenerate)
{
    srmech_status_t st;
    int cmp = 0, total = 0, idx = 0, i, n2;
    const st_rat_t *xs[4], *ys[4], *dxs[4], *dys[4];
    assert(c != NULL && b != NULL && p != NULL && count != NULL);
    assert(degenerate != NULL);
    *degenerate = 0; *count = 0;
    st = st_rat_cmp(c, &x0->num, &x0->den, &x1->num, &x1->den, &cmp);
    if (st != SRMECH_OK) { return st; }
    if (cmp >= 0) { *degenerate = 1; return SRMECH_OK; }
    st = st_rat_cmp(c, &y0->num, &y0->den, &y1->num, &y1->den, &cmp);
    if (st != SRMECH_OK) { return st; }
    if (cmp >= 0) { *degenerate = 1; return SRMECH_OK; }
    st = st_rat_addsub(c, &b->w1.num, &b->w1.den, &x1->num, &x1->den,
                       &x0->num, &x0->den, 1);   if (st != SRMECH_OK) { return st; }
    st = st_rat_addsub(c, &b->h1.num, &b->h1.den, &y1->num, &y1->den,
                       &y0->num, &y0->den, 1);   if (st != SRMECH_OK) { return st; }
    st = st_rat_addsub(c, &b->nw1.num, &b->nw1.den, &x0->num, &x0->den,
                       &x1->num, &x1->den, 1);   if (st != SRMECH_OK) { return st; }
    st = st_rat_addsub(c, &b->nh1.num, &b->nh1.den, &y0->num, &y0->den,
                       &y1->num, &y1->den, 1);   if (st != SRMECH_OK) { return st; }
    xs[0]=x0; ys[0]=y0; dxs[0]=&b->w1;  dys[0]=&b->zero;   /* bottom */
    xs[1]=x1; ys[1]=y0; dxs[1]=&b->zero; dys[1]=&b->h1;    /* right  */
    xs[2]=x1; ys[2]=y1; dxs[2]=&b->nw1; dys[2]=&b->zero;   /* top    */
    xs[3]=x0; ys[3]=y1; dxs[3]=&b->zero; dys[3]=&b->nh1;   /* left   */
    for (i = 0; i < 4; i++) {
        st = st_box_edge_index(c, b, p, xs[i], ys[i], dxs[i], dys[i],
                               &idx, degenerate);
        if (st != SRMECH_OK) { return st; }
        if (*degenerate) { return SRMECH_OK; }
        total += idx;
    }
    n2 = -total;
    if (n2 % 2 != 0) { *degenerate = 1; return SRMECH_OK; }   /* boundary root */
    if (n2 < 0) { *degenerate = 1; return SRMECH_OK; }        /* negative winding */
    *count = n2 / 2;
    return SRMECH_OK;
}

/* Dimensioning for the box path (U/V accumulation + generalised Sturm seq). W /
 * maxseq bound the working polynomial widths; cap covers the corner^deg coefficient
 * growth (coeff_limbs already reflects the box-corner magnitude, e.g. 2^bits during
 * refinement). */
static void st_dims_box(size_t coeff_limbs, size_t ncoef, uint32_t *cap,
                        size_t *W, size_t *maxseq)
{
    size_t base = coeff_limbs + 1u;
    size_t cc = base * (ncoef + 4u) * 4u + 512u;
    assert(cap != NULL);
    assert(W != NULL && maxseq != NULL);
    *cap = (uint32_t)cc;
    *W = ncoef + 4u;
    *maxseq = ncoef + 4u;
}

/* Carve the box-context polynomials + the generalised-Sturm seq array + the box
 * scalars, and set the read-only rationals zero = 0/1, one = 1/1. */
static srmech_status_t st_carve_bctx(st_ctx_t *c, st_bctx_t *b)
{
    st_poly_t *pv[12];
    st_rat_t *rv[6];
    uint32_t *h;
    size_t i;
    srmech_status_t st;
    assert(c != NULL && b != NULL);
    assert(b->maxseq >= 2u);
    pv[0]=&b->ea; pv[1]=&b->eb; pv[2]=&b->powU; pv[3]=&b->powV;
    pv[4]=&b->uU; pv[5]=&b->uV; pv[6]=&b->csc; pv[7]=&b->tmpA;
    pv[8]=&b->pmt1; pv[9]=&b->pmt2; pv[10]=&b->tra; pv[11]=&b->trb;
    for (i = 0u; i < 12u; i++) {
        st = st_carve_poly(c, pv[i]);
        if (st != SRMECH_OK) { return st; }
    }
    h = st_take(c, ((sizeof(st_poly_t) + 3u) / sizeof(uint32_t)) * b->maxseq);
    if (h == NULL) { return SRMECH_ERR_OVERFLOW; }
    b->seq = (st_poly_t *)(void *)h;
    for (i = 0u; i < b->maxseq; i++) {
        st = st_carve_poly(c, &b->seq[i]);
        if (st != SRMECH_OK) { return st; }
    }
    rv[0]=&b->w1; rv[1]=&b->h1; rv[2]=&b->nw1; rv[3]=&b->nh1;
    rv[4]=&b->zero; rv[5]=&b->one;
    for (i = 0u; i < 6u; i++) {
        st = st_bind(c, &rv[i]->num);
        if (st != SRMECH_OK) { return st; }
        st = st_bind(c, &rv[i]->den);
        if (st != SRMECH_OK) { return st; }
    }
    st = srmech_bigint_set_i64(&b->zero.num, 0);  if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&b->zero.den, 1);  if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&b->one.num, 1);   if (st != SRMECH_OK) { return st; }
    return srmech_bigint_set_i64(&b->one.den, 1);
}

/* Copy a caller (num, den) pair into a carved scalar rational register. */
static srmech_status_t st_load_corner(st_rat_t *r, const srmech_bigint_t *num,
                                      const srmech_bigint_t *den)
{
    srmech_status_t st;
    assert(r != NULL);
    assert(num != NULL && den != NULL);
    st = srmech_bigint_copy(&r->num, num);
    if (st != SRMECH_OK) { return st; }
    return srmech_bigint_copy(&r->den, den);
}

/* Bytes the caller hands srmech_poly_root_box_certify for a polynomial of `np`
 * coefficients whose coefficients + box corners have <= `coeff_limbs` limbs. */
size_t srmech_poly_root_box_certify_ws_bound(size_t coeff_limbs, size_t np)
{
    uint32_t cap;
    size_t W, maxseq, per_poly, n_polys, persistent, tail;
    st_dims_box(coeff_limbs == 0u ? 1u : coeff_limbs, np == 0u ? 1u : np,
                &cap, &W, &maxseq);
    assert(cap > 0u);
    assert(W > 0u);
    per_poly = 2u * W * STURM_HDR_WORDS + 2u * W * (size_t)cap;
    n_polys = 1u + 12u + maxseq;                  /* p + 12 bctx polys + seq */
    persistent = n_polys * per_poly
               + maxseq * STURM_PHDR_WORDS
               + (6u + 4u) * 2u * (size_t)cap     /* 6 box + 4 corner rationals */
               + 6u * (size_t)cap                 /* scalar temps */
               + 256u;
    tail = srmech_poly_gcd_ws_bound((size_t)cap, W);
    return persistent * sizeof(uint32_t) + tail + 64u;
}

/* Public: count the roots of `p` (np coefficients, low->high, over Q) strictly
 * inside the open rational box (x0,x1) x (y0,y1). *out_count receives the count;
 * *out_degenerate is 1 when a corner/edge hits a root (the caller nudges the box).
 * The C peer of _count_roots_in_box; caller-arena, no malloc. */
srmech_status_t srmech_poly_root_box_certify(
        const srmech_bigint_t *p_num, const srmech_bigint_t *p_den, size_t np,
        const srmech_bigint_t *x0n, const srmech_bigint_t *x0d,
        const srmech_bigint_t *x1n, const srmech_bigint_t *x1d,
        const srmech_bigint_t *y0n, const srmech_bigint_t *y0d,
        const srmech_bigint_t *y1n, const srmech_bigint_t *y1d,
        int *out_count, int *out_degenerate, void *ws, size_t ws_len)
{
    st_ctx_t c;
    st_bctx_t b;
    st_poly_t pp;
    st_rat_t x0, x1, y0, y1;
    srmech_status_t st;
    size_t coeff_limbs = 1u, i, W, maxseq, tail;
    uint32_t cap;
    const srmech_bigint_t *cn[8];
    assert(out_count != NULL && out_degenerate != NULL);
    assert(p_num != NULL && p_den != NULL);
    if (p_num == NULL || p_den == NULL || out_count == NULL
        || out_degenerate == NULL || ws == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (np == 0u) { return SRMECH_ERR_BAD_INPUT; }
    cn[0]=x0n; cn[1]=x0d; cn[2]=x1n; cn[3]=x1d;
    cn[4]=y0n; cn[5]=y0d; cn[6]=y1n; cn[7]=y1d;
    for (i = 0u; i < np; i++) {
        if (p_num[i].n > coeff_limbs) { coeff_limbs = p_num[i].n; }
        if (p_den[i].n > coeff_limbs) { coeff_limbs = p_den[i].n; }
    }
    for (i = 0u; i < 8u; i++) {
        if (cn[i] != NULL && cn[i]->n > coeff_limbs) { coeff_limbs = cn[i]->n; }
    }
    st_dims_box(coeff_limbs, np, &cap, &W, &maxseq);
    if (cap > 0x0FFFFFFFu) { return SRMECH_ERR_OVERFLOW; }
    c.base = (uint32_t *)ws; c.words = ws_len / sizeof(uint32_t);
    c.cur = 0u; c.cap = cap; c.W = W;
    b.maxseq = maxseq;
    st = st_bind_temps(&c);              if (st != SRMECH_OK) { return st; }
    st = st_carve_poly(&c, &pp);         if (st != SRMECH_OK) { return st; }
    st = st_bind_rat(&c, &x0);           if (st != SRMECH_OK) { return st; }
    st = st_bind_rat(&c, &x1);           if (st != SRMECH_OK) { return st; }
    st = st_bind_rat(&c, &y0);           if (st != SRMECH_OK) { return st; }
    st = st_bind_rat(&c, &y1);           if (st != SRMECH_OK) { return st; }
    st = st_carve_bctx(&c, &b);          if (st != SRMECH_OK) { return st; }
    tail = srmech_poly_gcd_ws_bound((size_t)cap, W);
    if ((c.words - c.cur) * sizeof(uint32_t) < tail) { return SRMECH_ERR_OVERFLOW; }
    c.ws = (void *)(c.base + c.cur);
    c.ws_len = (c.words - c.cur) * sizeof(uint32_t);
    for (i = 0u; i < np; i++) {
        st = srmech_bigint_copy(&pp.num[i], &p_num[i]); if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_copy(&pp.den[i], &p_den[i]); if (st != SRMECH_OK) { return st; }
    }
    pp.len = np;
    pp.len = st_poly_trim(&pp);
    st = st_load_corner(&x0, x0n, x0d);  if (st != SRMECH_OK) { return st; }
    st = st_load_corner(&x1, x1n, x1d);  if (st != SRMECH_OK) { return st; }
    st = st_load_corner(&y0, y0n, y0d);  if (st != SRMECH_OK) { return st; }
    st = st_load_corner(&y1, y1n, y1d);  if (st != SRMECH_OK) { return st; }
    return st_box_count(&c, &b, &pp, &x0, &x1, &y0, &y1, out_count, out_degenerate);
}

/* ---- the complex-isolation working roster (box subdivision + refinement) --- */
typedef struct st_iwork {
    st_rat_t B, eta, jx, jy;                /* strip bound + jitters       */
    st_rat_t ix0, ix1, iy0, iy1;            /* the initial strip box       */
    st_rat_t bx0, bx1, by0, by1, wx, wy;    /* popped box + widths         */
    st_rat_t cut, span, frac, lo, hi, eps;  /* split / refine work         */
    st_rat_t fcut;                          /* a found root-free cut       */
    st_rat_t lox, hix, loy, hiy, cx, cy;    /* refine registers + center   */
    st_rat_t s0, s1, one;                   /* scratch + the unit 1/1      */
    srmech_bigint_t *sx0n, *sx0d, *sx1n, *sx1d;   /* box stack (x corners) */
    srmech_bigint_t *sy0n, *sy0d, *sy1n, *sy1d;   /* box stack (y corners) */
    int *scnt;                              /* box stack root counts       */
    size_t boxcap, btop;
} st_iwork_t;

/* The nine refine-box jitter fractions (num, den), tried in order (exactly the
 * _refine_box `jitters` tuple). */
static const int32_t ST_REFINE_JIT[9][2] = {
    {1, 2}, {127, 256}, {129, 256}, {63, 128}, {65, 128},
    {31, 64}, {33, 64}, {509, 1024}, {515, 1024}
};

static srmech_status_t st_set_small(st_ctx_t *c, st_rat_t *r, int64_t n, int64_t d)
{
    srmech_status_t st;
    assert(c != NULL);
    assert(r != NULL && d != 0);
    st = srmech_bigint_set_i64(&r->num, n);   if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&r->den, d);   if (st != SRMECH_OK) { return st; }
    return st_rat_reduce(c, &r->num, &r->den);
}

/* r = 1 / 2^k  (num = 1, den = 1 << k), reduced. */
static srmech_status_t st_recip_pow2(st_ctx_t *c, st_rat_t *r, uint32_t k)
{
    srmech_status_t st;
    assert(c != NULL);
    assert(r != NULL);
    st = srmech_bigint_set_i64(&r->num, 1);   if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&c->t0, 1);    if (st != SRMECH_OK) { return st; }
    return srmech_bigint_shl_bits(&r->den, &c->t0, k);
}

/* iw->B = 1 + max_{i<deg}( |p[i]| / |p_lead| ) -- the Cauchy root bound of p (over
 * the whole polynomial), exact-Q. Same shape as st_factor_bound, over iw scratch. */
static srmech_status_t st_cauchy_bound(st_ctx_t *c, st_iwork_t *iw,
                                       const st_poly_t *p)
{
    srmech_status_t st;
    size_t i, plen = p->len;
    int cmp = 0;
    assert(c != NULL && iw != NULL && p != NULL);
    assert(plen >= 1u);
    st = st_abs_into(&iw->s1.num, &p->num[plen - 1u]);          /* |lead| */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&iw->s1.den, &p->den[plen - 1u]);
    if (st != SRMECH_OK) { return st; }
    st = st_set_small(c, &iw->B, 0, 1);
    if (st != SRMECH_OK) { return st; }
    for (i = 0u; i + 1u < plen; i++) {
        st = st_abs_into(&iw->s0.num, &p->num[i]);              /* |c| */
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_copy(&iw->s0.den, &p->den[i]);
        if (st != SRMECH_OK) { return st; }
        st = st_rat_mul(c, &iw->frac.num, &iw->frac.den, &iw->s0.num,
                        &iw->s0.den, &iw->s1.num, &iw->s1.den, 1); /* /|lead| */
        if (st != SRMECH_OK) { return st; }
        st = st_rat_cmp(c, &iw->frac.num, &iw->frac.den, &iw->B.num,
                        &iw->B.den, &cmp);
        if (st != SRMECH_OK) { return st; }
        if (cmp > 0) {
            st = st_rat_copy(&iw->B, &iw->frac);
            if (st != SRMECH_OK) { return st; }
        }
    }
    st = st_set_small(c, &iw->s0, 1, 1);
    if (st != SRMECH_OK) { return st; }
    st = st_rat_addsub(c, &iw->s1.num, &iw->s1.den, &iw->B.num, &iw->B.den,
                       &iw->s0.num, &iw->s0.den, 0);            /* +1 */
    if (st != SRMECH_OK) { return st; }
    return st_rat_copy(&iw->B, &iw->s1);
}

/* cut = lo + span*frac (exact-Q). */
static srmech_status_t st_cut_at(st_ctx_t *c, st_iwork_t *iw,
                                 const st_rat_t *lo, const st_rat_t *span,
                                 const st_rat_t *frac, st_rat_t *out)
{
    srmech_status_t st;
    assert(c != NULL && iw != NULL && out != NULL);
    assert(lo != NULL && span != NULL && frac != NULL);
    st = st_rat_mul(c, &iw->s0.num, &iw->s0.den, &span->num, &span->den,
                    &frac->num, &frac->den, 0);
    if (st != SRMECH_OK) { return st; }
    return st_rat_addsub(c, &out->num, &out->den, &lo->num, &lo->den,
                         &iw->s0.num, &iw->s0.den, 0);
}

/* Find a near-midpoint cut on `axis` (0=x, 1=y) of the box such that BOTH
 * sub-boxes are non-degenerate (exactly _root_free_split's 80-jitter scan);
 * *out_cut receives it, *fail = 1 when no root-free cut exists. */
static srmech_status_t st_root_free_split(st_ctx_t *c, st_bctx_t *b,
                                          st_iwork_t *iw, const st_poly_t *p,
                                          const st_rat_t *x0, const st_rat_t *x1,
                                          const st_rat_t *y0, const st_rat_t *y1,
                                          int axis, st_rat_t *out_cut, int *fail)
{
    srmech_status_t st;
    int k, cnt = 0, d1 = 0, d2 = 0, cmpa = 0, cmpb = 0;
    const st_rat_t *lo = (axis == 0) ? x0 : y0;
    const st_rat_t *hi = (axis == 0) ? x1 : y1;
    assert(c != NULL && b != NULL && iw != NULL && p != NULL && fail != NULL);
    assert(out_cut != NULL);
    *fail = 1;
    st = st_rat_addsub(c, &iw->span.num, &iw->span.den, &hi->num, &hi->den,
                       &lo->num, &lo->den, 1);                  /* span=hi-lo */
    if (st != SRMECH_OK) { return st; }
    for (k = 0; k < 80; k++) {
        int off = (k * 13 + 5) % 101 - 50;
        st = st_set_small(c, &iw->frac, 1024 + off, 2048);      /* 1/2 + off/2^11 */
        if (st != SRMECH_OK) { return st; }
        st = st_rat_cmp(c, &iw->frac.num, &iw->frac.den, &iw->one.num,
                        &iw->one.den, &cmpb);
        if (st != SRMECH_OK) { return st; }
        if (iw->frac.num.sign <= 0 || cmpb >= 0) { continue; }  /* frac<=0 or >=1 */
        st = st_cut_at(c, iw, lo, &iw->span, &iw->frac, &iw->cut);
        if (st != SRMECH_OK) { return st; }
        if (axis == 0) {
            st = st_box_count(c, b, p, x0, &iw->cut, y0, y1, &cnt, &d1);
            if (st != SRMECH_OK) { return st; }
            st = st_box_count(c, b, p, &iw->cut, x1, y0, y1, &cnt, &d2);
        } else {
            st = st_box_count(c, b, p, x0, x1, y0, &iw->cut, &cnt, &d1);
            if (st != SRMECH_OK) { return st; }
            st = st_box_count(c, b, p, x0, x1, &iw->cut, y1, &cnt, &d2);
        }
        if (st != SRMECH_OK) { return st; }
        (void)cmpa;
        if (d1 || d2) { continue; }
        st = st_rat_copy(out_cut, &iw->cut);
        if (st != SRMECH_OK) { return st; }
        *fail = 0;
        return SRMECH_OK;
    }
    return SRMECH_OK;
}

/* One refine step: pick the first non-degenerate jitter cut on the chosen axis,
 * then keep the sub-box holding the single root (cnt == 1) else its complement.
 * *done = 1 when both axes are already <= eps. *fail = 1 when no jitter works. */
static srmech_status_t st_refine_step(st_ctx_t *c, st_bctx_t *b, st_iwork_t *iw,
                                      const st_poly_t *p, int *done, int *fail)
{
    srmech_status_t st;
    int cmpx = 0, cmpy = 0, xaxis, j, cnt = 0, degen = 0, chosen = 0, ccnt = 0;
    const st_rat_t *lo, *hi;
    assert(c != NULL && b != NULL && iw != NULL && p != NULL);
    assert(done != NULL && fail != NULL);
    *done = 0; *fail = 0;
    st = st_rat_addsub(c, &iw->s0.num, &iw->s0.den, &iw->hix.num, &iw->hix.den,
                       &iw->lox.num, &iw->lox.den, 1);          /* wx */
    if (st != SRMECH_OK) { return st; }
    st = st_rat_addsub(c, &iw->s1.num, &iw->s1.den, &iw->hiy.num, &iw->hiy.den,
                       &iw->loy.num, &iw->loy.den, 1);          /* wy */
    if (st != SRMECH_OK) { return st; }
    st = st_rat_cmp(c, &iw->s0.num, &iw->s0.den, &iw->eps.num, &iw->eps.den, &cmpx);
    if (st != SRMECH_OK) { return st; }
    st = st_rat_cmp(c, &iw->s1.num, &iw->s1.den, &iw->eps.num, &iw->eps.den, &cmpy);
    if (st != SRMECH_OK) { return st; }
    if (cmpx <= 0 && cmpy <= 0) { *done = 1; return SRMECH_OK; }
    st = st_rat_cmp(c, &iw->s0.num, &iw->s0.den, &iw->s1.num, &iw->s1.den, &cmpx);
    if (st != SRMECH_OK) { return st; }
    xaxis = (cmpx >= 0);
    lo = xaxis ? &iw->lox : &iw->loy;
    hi = xaxis ? &iw->hix : &iw->hiy;
    st = st_rat_addsub(c, &iw->span.num, &iw->span.den, &hi->num, &hi->den,
                       &lo->num, &lo->den, 1);
    if (st != SRMECH_OK) { return st; }
    for (j = 0; j < 9; j++) {
        st = st_set_small(c, &iw->frac, ST_REFINE_JIT[j][0], ST_REFINE_JIT[j][1]);
        if (st != SRMECH_OK) { return st; }
        st = st_cut_at(c, iw, lo, &iw->span, &iw->frac, &iw->cut);
        if (st != SRMECH_OK) { return st; }
        if (xaxis) {
            st = st_box_count(c, b, p, &iw->lox, &iw->cut, &iw->loy, &iw->hiy,
                              &cnt, &degen);
        } else {
            st = st_box_count(c, b, p, &iw->lox, &iw->hix, &iw->loy, &iw->cut,
                              &cnt, &degen);
        }
        if (st != SRMECH_OK) { return st; }
        if (!degen) { chosen = 1; ccnt = cnt; break; }
    }
    if (!chosen) { *fail = 1; return SRMECH_OK; }
    if (xaxis) {
        st = st_rat_copy((ccnt == 1) ? &iw->hix : &iw->lox, &iw->cut);
    } else {
        st = st_rat_copy((ccnt == 1) ? &iw->hiy : &iw->loy, &iw->cut);
    }
    return st;
}

/* Refine the box (iw->bx0..by1, holding exactly ONE root) to width < 2^-bits and
 * write the center to iw->cx, iw->cy (exactly _refine_box). *fail on no cut. */
static srmech_status_t st_refine_box(st_ctx_t *c, st_bctx_t *b, st_iwork_t *iw,
                                     const st_poly_t *p, uint32_t bits, int *fail)
{
    srmech_status_t st;
    size_t guard = 0u, gmax;
    int done = 0;
    assert(c != NULL);
    assert(b != NULL && iw != NULL && p != NULL && fail != NULL);
    st = st_recip_pow2(c, &iw->eps, bits);   if (st != SRMECH_OK) { return st; }
    st = st_rat_copy(&iw->lox, &iw->bx0);    if (st != SRMECH_OK) { return st; }
    st = st_rat_copy(&iw->hix, &iw->bx1);    if (st != SRMECH_OK) { return st; }
    st = st_rat_copy(&iw->loy, &iw->by0);    if (st != SRMECH_OK) { return st; }
    st = st_rat_copy(&iw->hiy, &iw->by1);    if (st != SRMECH_OK) { return st; }
    gmax = (size_t)bits * 4u + iw->B.num.n * 32u + 8192u;
    while (guard <= gmax) {
        st = st_refine_step(c, b, iw, p, &done, fail);
        if (st != SRMECH_OK) { return st; }
        if (done || *fail) { break; }
        guard++;
    }
    if (*fail) { return SRMECH_OK; }
    st = st_rat_addsub(c, &iw->s0.num, &iw->s0.den, &iw->lox.num, &iw->lox.den,
                       &iw->hix.num, &iw->hix.den, 0);          /* lox+hix */
    if (st != SRMECH_OK) { return st; }
    st = st_set_small(c, &iw->s1, 1, 2);
    if (st != SRMECH_OK) { return st; }
    st = st_rat_mul(c, &iw->cx.num, &iw->cx.den, &iw->s0.num, &iw->s0.den,
                    &iw->s1.num, &iw->s1.den, 0);               /* /2 */
    if (st != SRMECH_OK) { return st; }
    st = st_rat_addsub(c, &iw->s0.num, &iw->s0.den, &iw->loy.num, &iw->loy.den,
                       &iw->hiy.num, &iw->hiy.den, 0);          /* loy+hiy */
    if (st != SRMECH_OK) { return st; }
    return st_rat_mul(c, &iw->cy.num, &iw->cy.den, &iw->s0.num, &iw->s0.den,
                      &iw->s1.num, &iw->s1.den, 0);             /* /2 */
}

/* Push a box (x0,x1,y0,y1,cnt) onto the subdivision stack (deep copy). */
static srmech_status_t st_boxstack_push(st_iwork_t *iw, const st_rat_t *x0,
                                        const st_rat_t *x1, const st_rat_t *y0,
                                        const st_rat_t *y1, int cnt)
{
    srmech_status_t st;
    size_t t = iw->btop;
    assert(iw != NULL);
    assert(x0 != NULL && x1 != NULL && y0 != NULL && y1 != NULL);
    if (t >= iw->boxcap) { return SRMECH_ERR_OVERFLOW; }
    st = srmech_bigint_copy(&iw->sx0n[t], &x0->num); if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&iw->sx0d[t], &x0->den); if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&iw->sx1n[t], &x1->num); if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&iw->sx1d[t], &x1->den); if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&iw->sy0n[t], &y0->num); if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&iw->sy0d[t], &y0->den); if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&iw->sy1n[t], &y1->num); if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&iw->sy1d[t], &y1->den); if (st != SRMECH_OK) { return st; }
    iw->scnt[t] = cnt;
    iw->btop = t + 1u;
    return SRMECH_OK;
}

/* Pop the top box into iw->bx0..by1; *cnt <- its root count. */
static srmech_status_t st_boxstack_pop(st_iwork_t *iw, int *cnt)
{
    srmech_status_t st;
    size_t t;
    assert(iw != NULL);
    assert(cnt != NULL && iw->btop > 0u);
    t = iw->btop - 1u;
    st = srmech_bigint_copy(&iw->bx0.num, &iw->sx0n[t]); if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&iw->bx0.den, &iw->sx0d[t]); if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&iw->bx1.num, &iw->sx1n[t]); if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&iw->bx1.den, &iw->sx1d[t]); if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&iw->by0.num, &iw->sy0n[t]); if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&iw->by0.den, &iw->sy0d[t]); if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&iw->by1.num, &iw->sy1n[t]); if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&iw->by1.den, &iw->sy1d[t]); if (st != SRMECH_OK) { return st; }
    *cnt = iw->scnt[t];
    iw->btop = t;
    return SRMECH_OK;
}

/* Write one (re, im) center at slot *count (im negated when conj != 0), advancing
 * *count. OVERFLOW when the caller output is full. */
static srmech_status_t st_emit_one(st_iwork_t *iw, size_t out_cap,
                                   srmech_bigint_t *ren, srmech_bigint_t *red,
                                   srmech_bigint_t *imn, srmech_bigint_t *imd,
                                   size_t *count, int conj)
{
    srmech_status_t st;
    size_t k = *count;
    assert(iw != NULL && count != NULL && ren != NULL && imn != NULL);
    assert(red != NULL && imd != NULL);
    if (k >= out_cap) { return SRMECH_ERR_OVERFLOW; }
    st = srmech_bigint_copy(&ren[k], &iw->cx.num);   if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&red[k], &iw->cx.den);   if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&imn[k], &iw->cy.num);   if (st != SRMECH_OK) { return st; }
    if (conj && imn[k].sign != 0) { imn[k].sign = -imn[k].sign; }
    st = srmech_bigint_copy(&imd[k], &iw->cy.den);   if (st != SRMECH_OK) { return st; }
    *count = k + 1u;
    return SRMECH_OK;
}

/* Emit the certified upper-half box center (iw->cx, iw->cy) then its conjugate,
 * `mult` times each (exactly `for _ in range(mult): append z, conj(z)`). */
static srmech_status_t st_cplx_emit(st_iwork_t *iw, size_t mult, size_t out_cap,
                                    srmech_bigint_t *ren, srmech_bigint_t *red,
                                    srmech_bigint_t *imn, srmech_bigint_t *imd,
                                    size_t *count)
{
    srmech_status_t st;
    size_t j;
    assert(iw != NULL);
    assert(count != NULL);
    for (j = 0u; j < mult; j++) {
        st = st_emit_one(iw, out_cap, ren, red, imn, imd, count, 0);
        if (st != SRMECH_OK) { return st; }
        st = st_emit_one(iw, out_cap, ren, red, imn, imd, count, 1);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* Seed the upper-half strip box (ix0,ix1,iy0,iy1) + its root count `*total`.
 * x0 = -B-jx, x1 = B+jx, y0 = eta, y1 = B+jy; on a degenerate boundary, retry
 * with the 1/503, 1/509, 1/521 jitters (exactly _isolate_complex_roots_upper). */
static srmech_status_t st_cplx_seed(st_ctx_t *c, st_bctx_t *b, st_iwork_t *iw,
                                    const st_poly_t *p, int *total, int *err)
{
    srmech_status_t st;
    int degen = 0;
    assert(c != NULL && b != NULL && iw != NULL && p != NULL);
    assert(total != NULL && err != NULL);
    *err = 0;
    st = st_cauchy_bound(c, iw, p);                 if (st != SRMECH_OK) { return st; }
    st = st_recip_pow2(c, &iw->eta, 24);            if (st != SRMECH_OK) { return st; }
    st = st_set_small(c, &iw->jx, 1, 997);          if (st != SRMECH_OK) { return st; }
    st = st_set_small(c, &iw->jy, 1, 991);          if (st != SRMECH_OK) { return st; }
    st = st_rat_addsub(c, &iw->ix1.num, &iw->ix1.den, &iw->B.num, &iw->B.den,
                       &iw->jx.num, &iw->jx.den, 0);  /* x1 = B+jx */
    if (st != SRMECH_OK) { return st; }
    st = st_rat_copy(&iw->ix0, &iw->ix1);           if (st != SRMECH_OK) { return st; }
    if (iw->ix0.num.sign != 0) { iw->ix0.num.sign = -iw->ix0.num.sign; }  /* x0 = -x1 */
    st = st_rat_copy(&iw->iy0, &iw->eta);           if (st != SRMECH_OK) { return st; }
    st = st_rat_addsub(c, &iw->iy1.num, &iw->iy1.den, &iw->B.num, &iw->B.den,
                       &iw->jy.num, &iw->jy.den, 0);  /* y1 = B+jy */
    if (st != SRMECH_OK) { return st; }
    st = st_box_count(c, b, p, &iw->ix0, &iw->ix1, &iw->iy0, &iw->iy1, total, &degen);
    if (st != SRMECH_OK) { return st; }
    if (!degen) { return SRMECH_OK; }
    st = st_set_small(c, &iw->jx, 1, 503);          if (st != SRMECH_OK) { return st; }
    st = st_rat_addsub(c, &iw->ix0.num, &iw->ix0.den, &iw->B.num, &iw->B.den,
                       &iw->jx.num, &iw->jx.den, 0);
    if (st != SRMECH_OK) { return st; }
    if (iw->ix0.num.sign != 0) { iw->ix0.num.sign = -iw->ix0.num.sign; }  /* -(B+1/503) */
    st = st_set_small(c, &iw->jx, 1, 509);          if (st != SRMECH_OK) { return st; }
    st = st_rat_addsub(c, &iw->ix1.num, &iw->ix1.den, &iw->B.num, &iw->B.den,
                       &iw->jx.num, &iw->jx.den, 0);
    if (st != SRMECH_OK) { return st; }
    st = st_set_small(c, &iw->jy, 1, 521);          if (st != SRMECH_OK) { return st; }
    st = st_rat_addsub(c, &iw->iy1.num, &iw->iy1.den, &iw->B.num, &iw->B.den,
                       &iw->jy.num, &iw->jy.den, 0);
    if (st != SRMECH_OK) { return st; }
    st = st_box_count(c, b, p, &iw->ix0, &iw->ix1, &iw->iy0, &iw->iy1, total, &degen);
    if (st != SRMECH_OK) { return st; }
    if (degen) { *err = 1; }
    return SRMECH_OK;
}

/* Split the popped box along its longer axis at a root-free cut, pushing the two
 * non-empty children (exactly the wx>=wy / else branch of the isolation loop). */
static srmech_status_t st_cplx_subdivide(st_ctx_t *c, st_bctx_t *b,
                                         st_iwork_t *iw, const st_poly_t *p,
                                         int cnt, int *err)
{
    srmech_status_t st;
    int cmpxy = 0, sub = 0, degen = 0, other, fail = 0;
    assert(c != NULL);
    assert(b != NULL && iw != NULL && p != NULL && err != NULL);
    st = st_rat_cmp(c, &iw->wx.num, &iw->wx.den, &iw->wy.num, &iw->wy.den, &cmpxy);
    if (st != SRMECH_OK) { return st; }
    st = st_root_free_split(c, b, iw, p, &iw->bx0, &iw->bx1, &iw->by0, &iw->by1,
                            (cmpxy >= 0) ? 0 : 1, &iw->fcut, &fail);
    if (st != SRMECH_OK) { return st; }
    if (fail) { *err = 1; return SRMECH_OK; }
    if (cmpxy >= 0) {                                   /* split x */
        st = st_box_count(c, b, p, &iw->bx0, &iw->fcut, &iw->by0, &iw->by1,
                          &sub, &degen);
        if (st != SRMECH_OK) { return st; }
        other = cnt - sub;
        if (sub) { st = st_boxstack_push(iw, &iw->bx0, &iw->fcut, &iw->by0, &iw->by1, sub); }
        if (st == SRMECH_OK && other) {
            st = st_boxstack_push(iw, &iw->fcut, &iw->bx1, &iw->by0, &iw->by1, other);
        }
    } else {                                            /* split y */
        st = st_box_count(c, b, p, &iw->bx0, &iw->bx1, &iw->by0, &iw->fcut,
                          &sub, &degen);
        if (st != SRMECH_OK) { return st; }
        other = cnt - sub;
        if (sub) { st = st_boxstack_push(iw, &iw->bx0, &iw->bx1, &iw->by0, &iw->fcut, sub); }
        if (st == SRMECH_OK && other) {
            st = st_boxstack_push(iw, &iw->bx0, &iw->bx1, &iw->fcut, &iw->by1, other);
        }
    }
    return st;
}

/* Isolate ALL upper-half (im>0) roots of the square-free factor `p` by pure exact
 * rational-box subdivision, refine each to 2^-bits, and emit each certified center
 * + its conjugate `mult` times (the C peer of _isolate_complex_roots_upper folded
 * with the eigvals conjugate/multiplicity emit). */
static srmech_status_t st_isolate_complex_upper(st_ctx_t *c, st_bctx_t *b,
        st_iwork_t *iw, const st_poly_t *p, uint32_t bits, size_t mult,
        srmech_bigint_t *ren, srmech_bigint_t *red, srmech_bigint_t *imn,
        srmech_bigint_t *imd, size_t *count, size_t out_cap, int *err)
{
    srmech_status_t st;
    int total = 0, cnt = 0, cw = 0, ch = 0, fail = 0;
    size_t guard = 0u;
    assert(c != NULL);
    assert(b != NULL && iw != NULL && p != NULL && err != NULL);
    st = st_cplx_seed(c, b, iw, p, &total, err);
    if (st != SRMECH_OK || *err) { return st; }
    iw->btop = 0u;
    st = st_boxstack_push(iw, &iw->ix0, &iw->ix1, &iw->iy0, &iw->iy1, total);
    if (st != SRMECH_OK) { return st; }
    while (iw->btop > 0u) {
        guard++;
        if (guard > 20000u) { *err = 1; return SRMECH_OK; }
        st = st_boxstack_pop(iw, &cnt);
        if (st != SRMECH_OK) { return st; }
        if (cnt == 0) { continue; }
        st = st_rat_addsub(c, &iw->wx.num, &iw->wx.den, &iw->bx1.num, &iw->bx1.den,
                           &iw->bx0.num, &iw->bx0.den, 1);
        if (st != SRMECH_OK) { return st; }
        st = st_rat_addsub(c, &iw->wy.num, &iw->wy.den, &iw->by1.num, &iw->by1.den,
                           &iw->by0.num, &iw->by0.den, 1);
        if (st != SRMECH_OK) { return st; }
        st = st_rat_cmp(c, &iw->wx.num, &iw->wx.den, &iw->one.num, &iw->one.den, &cw);
        if (st != SRMECH_OK) { return st; }
        st = st_rat_cmp(c, &iw->wy.num, &iw->wy.den, &iw->one.num, &iw->one.den, &ch);
        if (st != SRMECH_OK) { return st; }
        if (cnt == 1 && cw <= 0 && ch <= 0) {           /* isolated + small box */
            st = st_refine_box(c, b, iw, p, bits, &fail);
            if (st != SRMECH_OK) { return st; }
            if (fail) { *err = 1; return SRMECH_OK; }
            st = st_cplx_emit(iw, mult, out_cap, ren, red, imn, imd, count);
            if (st != SRMECH_OK) { return st; }
            continue;
        }
        st = st_cplx_subdivide(c, b, iw, p, cnt, err);
        if (st != SRMECH_OK || *err) { return st; }
    }
    return SRMECH_OK;
}

/* The Yun square-free factorisation fused with the per-factor COMPLEX isolation
 * (mirrors _square_free_factors + the eigvals_exact include_complex loop). Each
 * square-free factor of DEGREE >= 2 and multiplicity k has its upper-half complex
 * roots isolated + each root + conjugate emitted k times. */
static srmech_status_t st_squarefree_driver_cplx(st_ctx_t *c, st_work_t *w,
        st_bctx_t *b, st_iwork_t *iw, size_t n, uint32_t bits,
        srmech_bigint_t *ren, srmech_bigint_t *red, srmech_bigint_t *imn,
        srmech_bigint_t *imd, size_t *count)
{
    srmech_status_t st;
    size_t k = 1u;
    int err = 0;
    assert(c != NULL);
    assert(w != NULL && b != NULL && iw != NULL && count != NULL);
    st = st_poly_deriv(c, &w->dp, &w->p);              if (st != SRMECH_OK) { return st; }
    st = st_poly_gcd(c, &w->aa, &w->p, &w->dp);        if (st != SRMECH_OK) { return st; }
    st = st_poly_quot(c, &w->bb, &w->rr, &w->p, &w->aa); if (st != SRMECH_OK) { return st; }
    st = st_poly_quot(c, &w->cc, &w->rr, &w->dp, &w->aa); if (st != SRMECH_OK) { return st; }
    st = st_poly_deriv(c, &w->db, &w->bb);             if (st != SRMECH_OK) { return st; }
    st = st_poly_sub(c, &w->dd, &w->cc, &w->db);       if (st != SRMECH_OK) { return st; }
    while (w->bb.len > 1u) {
        if (k > n + 2u) { return SRMECH_ERR_OVERFLOW; }
        st = st_poly_gcd(c, &w->gg, &w->bb, &w->dd);   if (st != SRMECH_OK) { return st; }
        if (w->gg.len >= 3u) {                          /* degree >= 2 */
            st = st_isolate_complex_upper(c, b, iw, &w->gg, bits, k,
                                          ren, red, imn, imd, count, n, &err);
            if (st != SRMECH_OK) { return st; }
            if (err) { return SRMECH_ERR_OVERFLOW; }
        }
        st = st_poly_quot(c, &w->qq, &w->rr, &w->bb, &w->gg); if (st != SRMECH_OK) { return st; }
        st = st_poly_copy(&w->bb, &w->qq);             if (st != SRMECH_OK) { return st; }
        st = st_poly_quot(c, &w->qq, &w->rr, &w->dd, &w->gg); if (st != SRMECH_OK) { return st; }
        st = st_poly_copy(&w->cc, &w->qq);             if (st != SRMECH_OK) { return st; }
        st = st_poly_deriv(c, &w->db, &w->bb);         if (st != SRMECH_OK) { return st; }
        st = st_poly_sub(c, &w->dd, &w->cc, &w->db);   if (st != SRMECH_OK) { return st; }
        k++;
    }
    return SRMECH_OK;
}

/* Dimensioning for the full complex isolation (square-free + box subdivision). */
static void st_dims_cplx(size_t coeff_limbs, size_t n, uint32_t bits,
                         uint32_t *cap, size_t *W, size_t *maxchain,
                         size_t *maxseq, size_t *boxcap)
{
    size_t base = coeff_limbs + 1u;
    size_t bit_growth = ((size_t)bits / 32u + 2u) * (n + 4u) * 4u;
    size_t cc = base * (n + 4u) * 4u + bit_growth + 512u;
    assert(cap != NULL && W != NULL && maxchain != NULL);
    assert(maxseq != NULL && boxcap != NULL);
    *cap = (uint32_t)cc;
    *W = n + 4u;
    *maxchain = n + 3u;
    *maxseq = n + 4u;
    *boxcap = 16u * (n + 2u) + 512u;
}

/* Carve the 30 isolation scalar rationals + the box-subdivision stack (8 bigint
 * corner arrays + the int root-count array), and set iw->one = 1/1. */
static srmech_status_t st_carve_iwork(st_ctx_t *c, st_iwork_t *iw)
{
    st_rat_t *rv[30];
    uint32_t *sc;
    size_t i;
    srmech_status_t st;
    assert(c != NULL && iw != NULL);
    assert(iw->boxcap > 0u);
    rv[0]=&iw->B; rv[1]=&iw->eta; rv[2]=&iw->jx; rv[3]=&iw->jy;
    rv[4]=&iw->ix0; rv[5]=&iw->ix1; rv[6]=&iw->iy0; rv[7]=&iw->iy1;
    rv[8]=&iw->bx0; rv[9]=&iw->bx1; rv[10]=&iw->by0; rv[11]=&iw->by1;
    rv[12]=&iw->wx; rv[13]=&iw->wy; rv[14]=&iw->cut; rv[15]=&iw->span;
    rv[16]=&iw->frac; rv[17]=&iw->lo; rv[18]=&iw->hi; rv[19]=&iw->eps;
    rv[20]=&iw->fcut; rv[21]=&iw->lox; rv[22]=&iw->hix; rv[23]=&iw->loy;
    rv[24]=&iw->hiy; rv[25]=&iw->cx; rv[26]=&iw->cy; rv[27]=&iw->s0;
    rv[28]=&iw->s1; rv[29]=&iw->one;
    for (i = 0u; i < 30u; i++) {
        st = st_bind_rat(c, rv[i]);
        if (st != SRMECH_OK) { return st; }
    }
    st = st_carve_bi_array(c, &iw->sx0n, iw->boxcap); if (st != SRMECH_OK) { return st; }
    st = st_carve_bi_array(c, &iw->sx0d, iw->boxcap); if (st != SRMECH_OK) { return st; }
    st = st_carve_bi_array(c, &iw->sx1n, iw->boxcap); if (st != SRMECH_OK) { return st; }
    st = st_carve_bi_array(c, &iw->sx1d, iw->boxcap); if (st != SRMECH_OK) { return st; }
    st = st_carve_bi_array(c, &iw->sy0n, iw->boxcap); if (st != SRMECH_OK) { return st; }
    st = st_carve_bi_array(c, &iw->sy0d, iw->boxcap); if (st != SRMECH_OK) { return st; }
    st = st_carve_bi_array(c, &iw->sy1n, iw->boxcap); if (st != SRMECH_OK) { return st; }
    st = st_carve_bi_array(c, &iw->sy1d, iw->boxcap); if (st != SRMECH_OK) { return st; }
    sc = st_take(c, iw->boxcap);
    if (sc == NULL) { return SRMECH_ERR_OVERFLOW; }
    iw->scnt = (int *)(void *)sc;
    iw->btop = 0u;
    st = srmech_bigint_set_i64(&iw->one.num, 1);  if (st != SRMECH_OK) { return st; }
    return srmech_bigint_set_i64(&iw->one.den, 1);
}

size_t srmech_complex_isolate_entry_cap(size_t coeff_limbs, size_t n, uint32_t bits)
{
    uint32_t cap;
    size_t W, mc, ms, bc;
    st_dims_cplx(coeff_limbs == 0u ? 1u : coeff_limbs, n == 0u ? 1u : n, bits,
                 &cap, &W, &mc, &ms, &bc);
    assert(cap > 0u);
    assert(W > 0u);
    return (size_t)cap;
}

size_t srmech_complex_isolate_ws_bound(size_t coeff_limbs, size_t n, uint32_t bits)
{
    uint32_t cap;
    size_t W, mc, ms, bc, per_poly, persistent, tail;
    st_dims_cplx(coeff_limbs == 0u ? 1u : coeff_limbs, n == 0u ? 1u : n, bits,
                 &cap, &W, &mc, &ms, &bc);
    assert(cap > 0u);
    assert(W > 0u);
    per_poly = 2u * W * STURM_HDR_WORDS + 2u * W * (size_t)cap;
    persistent = (10u + mc) * per_poly + mc * STURM_PHDR_WORDS      /* st_work    */
               + (12u + ms) * per_poly + ms * STURM_PHDR_WORDS      /* st_bctx    */
               + 6u * 2u * (size_t)cap                              /* bctx rats  */
               + 30u * 2u * (size_t)cap                             /* iwork rats */
               + 8u * bc * STURM_HDR_WORDS + 8u * bc * (size_t)cap   /* box stack  */
               + bc                                                 /* scnt ints  */
               + 6u * (size_t)cap                                   /* temps      */
               + 512u;
    tail = srmech_poly_gcd_ws_bound((size_t)cap, W);
    return persistent * sizeof(uint32_t) + tail + 64u;
}

/* Public: the exact COMPLEX eigenvalues of the integer matrix whose monic INTEGER
 * char-poly is `cp` (HIGH->LOW, n+1 coeffs) -- the certified upper-half box centers
 * + their conjugates, WITH multiplicity, in per-square-free-factor emit order (the
 * caller sorts by (re, im) + projects to complex). *out_count <- the number of
 * complex eigenvalues (n - #real). C peer of the eigvals_exact include_complex path. */
srmech_status_t srmech_complex_isolate(const srmech_bigint_t *cp, int n,
                                       uint32_t bits,
                                       srmech_bigint_t *out_re_n,
                                       srmech_bigint_t *out_re_d,
                                       srmech_bigint_t *out_im_n,
                                       srmech_bigint_t *out_im_d,
                                       size_t *out_count, void *ws, size_t ws_len)
{
    st_ctx_t c;
    st_work_t w;
    st_bctx_t b;
    st_iwork_t iw;
    srmech_status_t st;
    size_t coeff_limbs = 1u, i, W, mc, ms, bc, tail;
    uint32_t cap;
    assert(cp != NULL && out_count != NULL && ws != NULL);
    assert(out_re_n != NULL && out_im_n != NULL);
    if (cp == NULL || out_re_n == NULL || out_re_d == NULL || out_im_n == NULL
        || out_im_d == NULL || out_count == NULL || ws == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n < 1 || n > SRMECH_STURM_MAX_DIM) { return SRMECH_ERR_BAD_INPUT; }
    *out_count = 0u;
    for (i = 0u; i <= (size_t)n; i++) {
        if (cp[i].n > coeff_limbs) { coeff_limbs = cp[i].n; }
    }
    st_dims_cplx(coeff_limbs, (size_t)n, bits, &cap, &W, &mc, &ms, &bc);
    if (cap > 0x0FFFFFFFu) { return SRMECH_ERR_OVERFLOW; }
    c.base = (uint32_t *)ws; c.words = ws_len / sizeof(uint32_t);
    c.cur = 0u; c.cap = cap; c.W = W;
    w.maxchain = mc; b.maxseq = ms; iw.boxcap = bc;
    st = st_bind_temps(&c);        if (st != SRMECH_OK) { return st; }
    st = st_carve_polys(&c, &w);   if (st != SRMECH_OK) { return st; }
    st = st_carve_bctx(&c, &b);    if (st != SRMECH_OK) { return st; }
    st = st_carve_iwork(&c, &iw);  if (st != SRMECH_OK) { return st; }
    tail = srmech_poly_gcd_ws_bound((size_t)cap, W);
    if ((c.words - c.cur) * sizeof(uint32_t) < tail) { return SRMECH_ERR_OVERFLOW; }
    c.ws = (void *)(c.base + c.cur);
    c.ws_len = (c.words - c.cur) * sizeof(uint32_t);
    for (i = 0u; i <= (size_t)n; i++) {
        st = srmech_bigint_copy(&w.p.num[i], &cp[(size_t)n - i]);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_set_i64(&w.p.den[i], 1);
        if (st != SRMECH_OK) { return st; }
    }
    w.p.len = (size_t)n + 1u;
    w.p.len = st_poly_trim(&w.p);
    return st_squarefree_driver_cplx(&c, &w, &b, &iw, (size_t)n, bits,
                                     out_re_n, out_re_d, out_im_n, out_im_d,
                                     out_count);
}
