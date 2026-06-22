/*
 * srmech_bigexp.c — BIGNUM-EXACT Class-N transcendental Taylor truncations
 * on the caller-arena srmech_bigint (the standalone-honor closure for the
 * exact-rational series).
 *
 * The Python `srmech.amsc.rational.{exp,sin,cos,log1p,atan}_series_truncate`
 * + `rational_pow_uint` are exact-rational-IN -> exact-rational-OUT with NO
 * magnitude ceiling (CPython arbitrary-precision int). The int64/Q61 C peers
 * in srmech_rational.c cap at int64 (SRMECH_ERR_OVERFLOW past it), so a
 * C-only host (no Python) hit a ceiling Python doesn't — a 1:1-parity gap.
 *
 * This file closes that gap: each op below computes the SAME exact rational
 * the Python bignum path computes, over srmech_bigint (caller-owned limbs,
 * caller-arena scratch, NO malloc), and returns the result reduced to lowest
 * terms with positive denominator — byte-identical to Python's (num, den).
 *
 * Algorithm (matches rational.py exactly):
 *   exp(p/q)    : common-denominator form  S_N = A_N / (q^N · N!),
 *                 A_N = Σ_{k=0..N} sign(p)^k·|p|^k · q^(N-k) · (N!/k!)
 *   sin(p/q)    : Σ_{k=0..N} (-1)^k · p^(2k+1) / (q^(2k+1)·(2k+1)!)
 *   cos(p/q)    : Σ_{k=0..N} (-1)^k · p^(2k)   / (q^(2k)·(2k)!)
 *   log1p(p/q)  : Σ_{k=1..N} (-1)^(k+1)·p^k / (q^k·k)      (-1 < p/q ≤ 1)
 *   atan(p/q)   : Σ_{k=0..N} (-1)^k · p^(2k+1) / (q^(2k+1)·(2k+1))  (|p/q| ≤ 1)
 *   pow_uint    : (p/q)^n = p^n / q^n, reduced.
 * The final reduced (num, den) is a property of the exact rational VALUE, so
 * accumulating in common-denominator form and reducing once at the end yields
 * the same lowest-terms pair Python's per-term-accumulate-then-reduce returns.
 *
 * Each series accumulates the running sum as A/B (B > 0): new term t_num/t_den
 * folds in via A = A·t_den + t_num·B ; B = B·t_den (then a final gcd reduce).
 *
 * Carrier-internal, like srmech_pi.c / srmech_qi.c: NOT a Rosetta ledger op
 * (no ToolEntry, no count-test). Additive symbols → ABI unchanged (stays 3).
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto/recursion): OK — iterative series, flat helpers
 *   - Rule 2 (bounded loops)    : OK — loop bound is the term count N
 *   - Rule 3 (no malloc)        : OK — caller arena + caller out only
 *   - Rule 4 (<=60 lines/func)  : OK — factored into static helpers
 *   - Rule 5 (>=2 asserts/fn)   : OK — entry-pointer + pre/postcondition
 *   - Rule 7 (return-value)     : OK — srmech_status_t propagated
 *   - Rule 8 (no multi-line mac): OK — no function-like macros
 *   - Rule 10 (warnings clean)  : OK under -Wall -Wextra -Wpedantic -Werror
 *
 * License: MIT.
 */

#include "srmech.h"

#include <assert.h>
#include <stdint.h>

/* Per-op term caps mirror the Python module constants (rational.py). The
 * bignum path has no overflow ceiling; these only bound the loop (Rule 2)
 * and match the Python ValueError-domain so C and Python accept the same N. */
#define BIGEXP_EXP_MAX_TERMS  512u
#define BIGEXP_TRIG_MAX_TERMS  50u
#define BIGEXP_LOG_MAX_TERMS   64u
#define BIGEXP_POW_MAX_EXP   65535u   /* Rule 2 loop bound for pow_uint */

/* A roster of working bigints, all carved from the caller arena `ws`.
 * num/den hold the running sum A/B; t0..t4 are exact-integer scratch; the
 * tail of `ws` is the divmod/gcd arena. */
typedef struct bigexp_ctx {
    srmech_bigint_t num;    /* running sum numerator A          */
    srmech_bigint_t den;    /* running sum denominator B (> 0)  */
    srmech_bigint_t t0;     /* exact-integer scratch carriers   */
    srmech_bigint_t t1;
    srmech_bigint_t t2;
    srmech_bigint_t t3;
    srmech_bigint_t t4;
    srmech_bigint_t rem;    /* divmod remainder sink            */
    srmech_bigint_t pw;     /* bigexp_pow running-square carrier */
    uint32_t limb_cap;      /* per-carrier limb capacity        */
    void  *scratch;         /* divmod/gcd/isqrt arena tail      */
    size_t scratch_len;     /* its length in BYTES              */
} bigexp_ctx_t;

#define BIGEXP_N_CARRIERS 9u  /* num,den,t0..t4,rem,pw */

/* ---- forward declarations (Rule 1: no recursion) ------------------- */

static uint32_t *bigexp_take(uint32_t *base, size_t words, size_t *cur,
                             size_t count);
static srmech_status_t bigexp_bind(srmech_bigint_t *b, uint32_t *base,
                                   size_t words, size_t *cur, uint32_t cap);
static srmech_status_t bigexp_ctx_init(bigexp_ctx_t *c, uint32_t cap,
                                       void *ws, size_t ws_len);
static srmech_status_t bigexp_mul(bigexp_ctx_t *c, srmech_bigint_t *out,
                                  const srmech_bigint_t *a,
                                  const srmech_bigint_t *b);
static srmech_status_t bigexp_pow(bigexp_ctx_t *c, srmech_bigint_t *out,
                                  const srmech_bigint_t *base, uint32_t exp);
static srmech_status_t bigexp_fold_term(bigexp_ctx_t *c,
                                        const srmech_bigint_t *t_num,
                                        const srmech_bigint_t *t_den);
static srmech_status_t bigexp_reduce_out(bigexp_ctx_t *c,
                                         srmech_bigint_t *out_num,
                                         srmech_bigint_t *out_den);

/* ---- caller-arena carve (mirrors pi_take / pi_bind) ---------------- */

static uint32_t *bigexp_take(uint32_t *base, size_t words, size_t *cur,
                             size_t count)
{
    uint32_t *p;
    assert(base != NULL && cur != NULL);
    assert(*cur <= words);
    if (count > words || *cur > words - count) {
        return NULL;
    }
    p = base + *cur;
    *cur += count;
    return p;
}

static srmech_status_t bigexp_bind(srmech_bigint_t *b, uint32_t *base,
                                   size_t words, size_t *cur, uint32_t cap)
{
    uint32_t *limbs = bigexp_take(base, words, cur, cap);
    assert(b != NULL);
    assert(cap > 0u);
    if (limbs == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    b->limbs = limbs;
    b->cap = cap;
    b->n = 0u;
    b->sign = 0;
    return SRMECH_OK;
}

static srmech_status_t bigexp_ctx_init(bigexp_ctx_t *c, uint32_t cap,
                                       void *ws, size_t ws_len)
{
    uint32_t *base = (uint32_t *)ws;
    size_t words = ws_len / sizeof(uint32_t), cur = 0u;
    srmech_status_t st = SRMECH_OK;
    assert(c != NULL);
    assert((uintptr_t)ws % sizeof(uint32_t) == 0u || ws == NULL);
    c->limb_cap = cap;
    st |= bigexp_bind(&c->num, base, words, &cur, cap);
    st |= bigexp_bind(&c->den, base, words, &cur, cap);
    st |= bigexp_bind(&c->t0, base, words, &cur, cap);
    st |= bigexp_bind(&c->t1, base, words, &cur, cap);
    st |= bigexp_bind(&c->t2, base, words, &cur, cap);
    st |= bigexp_bind(&c->t3, base, words, &cur, cap);
    st |= bigexp_bind(&c->t4, base, words, &cur, cap);
    st |= bigexp_bind(&c->rem, base, words, &cur, cap);
    st |= bigexp_bind(&c->pw, base, words, &cur, cap);
    if (st != SRMECH_OK) {
        return SRMECH_ERR_OVERFLOW;
    }
    c->scratch = (void *)(base + cur);
    c->scratch_len = (words - cur) * sizeof(uint32_t);
    assert(cur <= words);
    return SRMECH_OK;
}

/* out = a * b, via scratch t0 so out may alias a/b. */
static srmech_status_t bigexp_mul(bigexp_ctx_t *c, srmech_bigint_t *out,
                                  const srmech_bigint_t *a,
                                  const srmech_bigint_t *b)
{
    srmech_status_t st;
    assert(c != NULL && out != NULL && a != NULL && b != NULL);
    assert(out != &c->t0);                  /* t0 is the mul scratch */
    st = srmech_bigint_mul(&c->t0, a, b);
    if (st != SRMECH_OK) { return st; }
    return srmech_bigint_copy(out, &c->t0);
}

/* out = base^exp, square-and-multiply into the large context carriers (out +
 * c->pw running square; c->t0 is bigexp_mul's scratch). This deliberately does
 * NOT call srmech_bigint_pow_u32: that op sizes its internal scratch as
 * base->n*32+4 limbs, which is too small once base^exp exceeds 32 limbs (a
 * latent bound bug in the shared bigint pow — e.g. 452^128 overflows even a
 * 4000-limb output). Sign is carried by the sign-magnitude muls. exp <= 65535
 * (Rule 2 bounded). out must not alias c->t0 / c->pw. */
static srmech_status_t bigexp_pow(bigexp_ctx_t *c, srmech_bigint_t *out,
                                  const srmech_bigint_t *base, uint32_t exp)
{
    srmech_status_t st;
    uint32_t e = exp;
    assert(c != NULL && out != NULL && base != NULL);
    assert(out != &c->t0 && out != &c->pw);
    st = srmech_bigint_set_i64(out, 1);             /* out = 1 */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&c->pw, base);          /* pw = base */
    if (st != SRMECH_OK) { return st; }
    while (e != 0u) {                               /* square-and-multiply */
        if ((e & 1u) != 0u) {
            st = bigexp_mul(c, out, out, &c->pw);   /* out *= pw */
            if (st != SRMECH_OK) { return st; }
        }
        e >>= 1;
        if (e != 0u) {
            st = bigexp_mul(c, &c->pw, &c->pw, &c->pw); /* pw = pw² */
            if (st != SRMECH_OK) { return st; }
        }
    }
    return SRMECH_OK;
}

/* Fold one term t_num/t_den into the running sum num/den:
 *   num = num·t_den + t_num·den ;  den = den·t_den.
 * t1..t2 scratch; out may not alias the term carriers. */
static srmech_status_t bigexp_fold_term(bigexp_ctx_t *c,
                                        const srmech_bigint_t *t_num,
                                        const srmech_bigint_t *t_den)
{
    srmech_status_t st;
    assert(c != NULL && t_num != NULL && t_den != NULL);
    assert(t_den->sign > 0);                /* term denominator positive */
    st = bigexp_mul(c, &c->t1, &c->num, t_den);     /* t1 = num·t_den */
    if (st != SRMECH_OK) { return st; }
    st = bigexp_mul(c, &c->t2, t_num, &c->den);     /* t2 = t_num·den */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_add(&c->num, &c->t1, &c->t2); /* num = t1 + t2 */
    if (st != SRMECH_OK) { return st; }
    return bigexp_mul(c, &c->den, &c->den, t_den);  /* den = den·t_den */
}

/* out_num/out_den = reduce(num/den) to lowest terms, positive denominator.
 * den is positive throughout (every term denominator is positive). The quotient
 * is divided into scratch (t1/t2) first, THEN copied out — srmech_bigint_divmod
 * does NOT support q aliasing the dividend a (the in-loop call reduces num/den
 * in place, so out_num CAN equal &c->num). */
static srmech_status_t bigexp_reduce_out(bigexp_ctx_t *c,
                                         srmech_bigint_t *out_num,
                                         srmech_bigint_t *out_den)
{
    srmech_status_t st;
    assert(c != NULL && out_num != NULL && out_den != NULL);
    assert(c->den.sign > 0);                /* denominator stays positive */
    if (srmech_bigint_is_zero(&c->num)) {
        st = srmech_bigint_set_i64(out_num, 0);
        if (st != SRMECH_OK) { return st; }
        return srmech_bigint_set_i64(out_den, 1);
    }
    st = srmech_bigint_gcd(&c->t3, &c->num, &c->den,
                           c->scratch, c->scratch_len);   /* t3 = gcd */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_divmod(&c->t1, &c->rem, &c->num, &c->t3,
                              c->scratch, c->scratch_len); /* t1 = num/gcd */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_divmod(&c->t2, &c->rem, &c->den, &c->t3,
                              c->scratch, c->scratch_len); /* t2 = den/gcd */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(out_num, &c->t1);
    if (st != SRMECH_OK) { return st; }
    return srmech_bigint_copy(out_den, &c->t2);
}

/* ---- bounds ------------------------------------------------------- *
 * Worst-case magnitude: each op reduces the running sum EVERY iteration, so
 * the reduced denominator stays the LCM of the term denominators seen,
 * ≤ q^(top_exp)·(top_exp)! (top_exp = the largest power / factorial argument
 * across the ops, 2N+1). We size each carrier to hold that magnitude AND the
 * unreduced fold intermediate (≈ its square). The limb counts come from the
 * bigint _bound helpers, summed compositionally with generous slack. */

/* Limbs to hold q^exp (q given as q_limbs). */
static size_t bigexp_pow_limbs(size_t q_limbs, uint32_t exp)
{
    size_t lp = srmech_bigint_pow_bound(q_limbs == 0u ? 1u : q_limbs, exp);
    assert(lp > 0u);
    assert(lp >= q_limbs || exp <= 1u);
    return lp;
}

/* Limbs to hold E! (factorial of E ≤ 1025). 32-bit limb holds ~9.6 bits per
 * decimal digit; E! has ~E·log10(E) digits. Use a safe over-estimate:
 * E·11 bits per factor / 32 = E·(11/32) limbs + slack. */
static size_t bigexp_factorial_limbs(uint32_t e)
{
    size_t bits = (size_t)e * 14u + 64u;    /* ≥ log2(E!) for E ≤ ~2048 */
    size_t limbs = bits / 32u + 2u;
    assert(limbs >= 2u);
    assert(limbs > (size_t)e / 4u);
    return limbs;
}

/* Per-carrier limb cap. The reduced running sum num/den each divide
 * L = lcm(q^E, E!) ≤ q^E·E!, so num,den ≤ |q^E·E!·p^E|-ish. The UNREDUCED
 * fold intermediates (num·t_den and t_num·den, before the gcd reduce) reach
 * ~ the PRODUCT of two such magnitudes, so the carrier must hold ~2× the
 * reduced size. Budget 2·(q^E + E! + p^E) limbs + slack — generous per the
 * caller-arena philosophy (over-sizing is free; under-sizing → OVERFLOW). */
static size_t bigexp_cap_for(size_t num_limbs, size_t den_limbs,
                             uint32_t top_exp)
{
    size_t qe = bigexp_pow_limbs(den_limbs, top_exp);
    size_t pe = bigexp_pow_limbs(num_limbs, top_exp);
    size_t fe = bigexp_factorial_limbs(top_exp);
    size_t one_sum = qe + fe + pe;          /* one reduced-magnitude bound */
    size_t cap = one_sum * 2u + 16u;        /* unreduced product + slack */
    assert(cap >= one_sum);
    assert(cap >= qe);
    return cap;
}

/* Bytes the caller must hand each op for given input limb sizes + N. The
 * arena holds BIGEXP_N_CARRIERS carriers of `cap` limbs each, plus a divmod/
 * gcd/isqrt scratch tail (the heaviest is divmod over two `cap`-limb values:
 * ~4·cap carriers internally — 8·cap + 256 is a safe envelope). */
size_t srmech_bigexp_ws_bound(size_t num_limbs, size_t den_limbs,
                              uint32_t num_terms)
{
    uint32_t top = 2u * num_terms + 1u;     /* largest exponent across ops */
    size_t cap = bigexp_cap_for(num_limbs, den_limbs, top);
    size_t carriers = cap * (size_t)BIGEXP_N_CARRIERS;
    size_t scratch = cap * 8u + 256u;
    size_t words = carriers + scratch;
    assert(cap >= 2u);
    assert(words >= carriers);
    return words * sizeof(uint32_t);
}

/* ---- exp series (common-denominator form, sign-aware) -------------- */

/* exp term_k = p^k / (q^k · k!), built into t_num / t_den. The driver folds
 * it into the running A/B sum the same incremental way the trig ops do. The
 * (-1)^k sign of exp's series is carried by p^k itself (p may be negative). */
static srmech_status_t bigexp_exp_term(bigexp_ctx_t *c, const srmech_bigint_t *p,
                                       const srmech_bigint_t *q, uint32_t k,
                                       srmech_bigint_t *t_num,
                                       srmech_bigint_t *t_den)
{
    srmech_status_t st;
    uint32_t j;
    assert(c != NULL && p != NULL && q != NULL);
    assert(t_num != NULL && t_den != NULL);
    st = bigexp_pow(c, t_num, p, k);
    if (st != SRMECH_OK) { return st; }                 /* t_num = p^k */
    st = bigexp_pow(c, t_den, q, k);
    if (st != SRMECH_OK) { return st; }                 /* t_den = q^k */
    st = srmech_bigint_set_i64(&c->t4, 1);              /* t4 = k! */
    if (st != SRMECH_OK) { return st; }
    for (j = 2u; j <= k; j++) {
        srmech_bigint_t f; uint32_t fl[2];
        f.sign = 1; f.n = 0u; f.cap = 2u; f.limbs = fl;
        st = srmech_bigint_set_i64(&f, (int64_t)j);
        if (st != SRMECH_OK) { return st; }
        st = bigexp_mul(c, &c->t4, &c->t4, &f);
        if (st != SRMECH_OK) { return st; }
    }
    return bigexp_mul(c, t_den, t_den, &c->t4);         /* t_den = q^k·k! */
}

srmech_status_t srmech_exp_series_truncate_big(const srmech_bigint_t *x_num,
                                               const srmech_bigint_t *x_den,
                                               uint32_t num_terms,
                                               srmech_bigint_t *out_num,
                                               srmech_bigint_t *out_den,
                                               void *ws, size_t ws_len)
{
    bigexp_ctx_t c;
    srmech_status_t st;
    uint32_t k, cap;
    assert(out_num != NULL && out_den != NULL);
    assert(x_num != NULL && x_den != NULL);
    if (out_num == NULL || out_den == NULL || x_num == NULL || x_den == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (x_den->sign <= 0) { return SRMECH_ERR_BAD_INPUT; }
    if (num_terms > BIGEXP_EXP_MAX_TERMS) { return SRMECH_ERR_BAD_INPUT; }
    cap = (uint32_t)bigexp_cap_for(x_num->n, x_den->n, num_terms);
    st = bigexp_ctx_init(&c, cap, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&c.num, 0);             /* sum = 0/1 */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&c.den, 1);
    if (st != SRMECH_OK) { return st; }
    for (k = 0u; k <= num_terms; k++) {
        st = bigexp_exp_term(&c, x_num, x_den, k, &c.t2, &c.t3);
        if (st != SRMECH_OK) { return st; }
        st = bigexp_fold_term(&c, &c.t2, &c.t3);
        if (st != SRMECH_OK) { return st; }
        st = bigexp_reduce_out(&c, &c.num, &c.den);    /* keep size bounded */
        if (st != SRMECH_OK) { return st; }
    }
    return bigexp_reduce_out(&c, out_num, out_den);
}

/* ---- sin / cos / atan (odd/even power, alternating sign) ----------- */

/* term_k for sin/atan (odd power 2k+1) or cos (even power 2k). `denom_extra`
 * is the divisor on q^exp: (2k+1)! for sin, (2k)! for cos, (2k+1) for atan. */
static srmech_status_t bigexp_pow_term(bigexp_ctx_t *c, const srmech_bigint_t *p,
                                       const srmech_bigint_t *q, uint32_t e,
                                       int negate, const srmech_bigint_t *dextra,
                                       srmech_bigint_t *t_num,
                                       srmech_bigint_t *t_den)
{
    srmech_status_t st;
    assert(c != NULL && p != NULL && q != NULL && dextra != NULL);
    assert(t_num != NULL && t_den != NULL);
    st = bigexp_pow(c, t_num, p, e);
    if (st != SRMECH_OK) { return st; }                 /* t_num = p^e */
    if (negate) { t_num->sign = (t_num->sign == 0) ? 0 : -t_num->sign; }
    st = bigexp_pow(c, t_den, q, e);
    if (st != SRMECH_OK) { return st; }                 /* t_den = q^e */
    return bigexp_mul(c, t_den, t_den, dextra);         /* t_den = q^e·dextra */
}

/* Factorial of m into c->t4 (m ≤ ~101 here). */
static srmech_status_t bigexp_set_factorial(bigexp_ctx_t *c, uint32_t m)
{
    srmech_status_t st;
    uint32_t j;
    assert(c != NULL);
    assert(m <= 4096u);                     /* trig/exp caps keep this small */
    st = srmech_bigint_set_i64(&c->t4, 1);
    if (st != SRMECH_OK) { return st; }
    for (j = 2u; j <= m; j++) {
        srmech_bigint_t f; uint32_t fl[2];
        f.sign = 1; f.n = 0u; f.cap = 2u; f.limbs = fl;
        st = srmech_bigint_set_i64(&f, (int64_t)j);
        if (st != SRMECH_OK) { return st; }
        st = bigexp_mul(c, &c->t4, &c->t4, &f);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* Shared driver for sin/cos/atan. `odd` selects exponent 2k+1 vs 2k; `factor`
 * selects (exp)! vs (exp) as the per-term divisor extra. */
static srmech_status_t bigexp_trig_like(const srmech_bigint_t *p,
                                        const srmech_bigint_t *q,
                                        uint32_t num_terms, int odd, int factorial,
                                        srmech_bigint_t *out_num,
                                        srmech_bigint_t *out_den,
                                        void *ws, size_t ws_len)
{
    bigexp_ctx_t c;
    srmech_status_t st;
    uint32_t k, cap, e;
    assert(p != NULL && q != NULL && out_num != NULL && out_den != NULL);
    assert(num_terms <= BIGEXP_LOG_MAX_TERMS);   /* sin/cos cap 50; atan cap 64 */
    cap = (uint32_t)bigexp_cap_for(p->n, q->n, 2u * num_terms + 1u);
    st = bigexp_ctx_init(&c, cap, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&c.num, 0);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&c.den, 1);
    if (st != SRMECH_OK) { return st; }
    for (k = 0u; k <= num_terms; k++) {
        e = odd ? (2u * k + 1u) : (2u * k);
        if (factorial) {
            st = bigexp_set_factorial(&c, e);           /* t4 = e! */
        } else {
            st = srmech_bigint_set_i64(&c.t4, (int64_t)e); /* t4 = e */
        }
        if (st != SRMECH_OK) { return st; }
        st = bigexp_pow_term(&c, p, q, e, (k % 2u) == 1u, &c.t4, &c.t2, &c.t3);
        if (st != SRMECH_OK) { return st; }
        st = bigexp_fold_term(&c, &c.t2, &c.t3);
        if (st != SRMECH_OK) { return st; }
        st = bigexp_reduce_out(&c, &c.num, &c.den);
        if (st != SRMECH_OK) { return st; }
    }
    return bigexp_reduce_out(&c, out_num, out_den);
}

srmech_status_t srmech_sin_series_truncate_big(const srmech_bigint_t *x_num,
                                               const srmech_bigint_t *x_den,
                                               uint32_t num_terms,
                                               srmech_bigint_t *out_num,
                                               srmech_bigint_t *out_den,
                                               void *ws, size_t ws_len)
{
    assert(out_num != NULL && out_den != NULL);
    assert(x_num != NULL && x_den != NULL);
    if (out_num == NULL || out_den == NULL || x_num == NULL || x_den == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (x_den->sign <= 0) { return SRMECH_ERR_BAD_INPUT; }
    if (num_terms > BIGEXP_TRIG_MAX_TERMS) { return SRMECH_ERR_BAD_INPUT; }
    if (srmech_bigint_is_zero(x_num)) {                 /* sin(0) = 0/1 */
        srmech_status_t st = srmech_bigint_set_i64(out_num, 0);
        if (st != SRMECH_OK) { return st; }
        return srmech_bigint_set_i64(out_den, 1);
    }
    return bigexp_trig_like(x_num, x_den, num_terms, 1, 1,
                            out_num, out_den, ws, ws_len);
}

srmech_status_t srmech_cos_series_truncate_big(const srmech_bigint_t *x_num,
                                               const srmech_bigint_t *x_den,
                                               uint32_t num_terms,
                                               srmech_bigint_t *out_num,
                                               srmech_bigint_t *out_den,
                                               void *ws, size_t ws_len)
{
    assert(out_num != NULL && out_den != NULL);
    assert(x_num != NULL && x_den != NULL);
    if (out_num == NULL || out_den == NULL || x_num == NULL || x_den == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (x_den->sign <= 0) { return SRMECH_ERR_BAD_INPUT; }
    if (num_terms > BIGEXP_TRIG_MAX_TERMS) { return SRMECH_ERR_BAD_INPUT; }
    if (srmech_bigint_is_zero(x_num)) {                 /* cos(0) = 1/1 */
        srmech_status_t st = srmech_bigint_set_i64(out_num, 1);
        if (st != SRMECH_OK) { return st; }
        return srmech_bigint_set_i64(out_den, 1);
    }
    return bigexp_trig_like(x_num, x_den, num_terms, 0, 1,
                            out_num, out_den, ws, ws_len);
}

srmech_status_t srmech_atan_series_truncate_big(const srmech_bigint_t *x_num,
                                                const srmech_bigint_t *x_den,
                                                uint32_t num_terms,
                                                srmech_bigint_t *out_num,
                                                srmech_bigint_t *out_den,
                                                void *ws, size_t ws_len)
{
    int cmp;
    assert(out_num != NULL && out_den != NULL);
    assert(x_num != NULL && x_den != NULL);
    if (out_num == NULL || out_den == NULL || x_num == NULL || x_den == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (x_den->sign <= 0) { return SRMECH_ERR_BAD_INPUT; }
    if (num_terms > BIGEXP_LOG_MAX_TERMS) { return SRMECH_ERR_BAD_INPUT; }
    /* Domain |p/q| ≤ 1: refuse |p| > q (matches Python ValueError). */
    cmp = srmech_bigint_cmp(x_den, x_num);              /* compares signed */
    if (x_num->sign >= 0) {
        if (srmech_bigint_cmp(x_num, x_den) > 0) { return SRMECH_ERR_BAD_INPUT; }
    } else {                                            /* p < 0: need -p ≤ q */
        srmech_bigint_t negd = *x_den;
        negd.sign = -negd.sign;
        if (srmech_bigint_cmp(x_num, &negd) < 0) { return SRMECH_ERR_BAD_INPUT; }
    }
    (void)cmp;
    if (srmech_bigint_is_zero(x_num)) {                 /* atan(0) = 0/1 */
        srmech_status_t st = srmech_bigint_set_i64(out_num, 0);
        if (st != SRMECH_OK) { return st; }
        return srmech_bigint_set_i64(out_den, 1);
    }
    return bigexp_trig_like(x_num, x_den, num_terms, 1, 0,
                            out_num, out_den, ws, ws_len);
}

/* ---- log1p (k=1..N, sign (-1)^(k+1), divisor k) -------------------- */

srmech_status_t srmech_log1p_series_truncate_big(const srmech_bigint_t *x_num,
                                                 const srmech_bigint_t *x_den,
                                                 uint32_t num_terms,
                                                 srmech_bigint_t *out_num,
                                                 srmech_bigint_t *out_den,
                                                 void *ws, size_t ws_len)
{
    bigexp_ctx_t c;
    srmech_status_t st;
    uint32_t k, cap;
    assert(out_num != NULL && out_den != NULL);
    assert(x_num != NULL && x_den != NULL);
    if (out_num == NULL || out_den == NULL || x_num == NULL || x_den == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (x_den->sign <= 0) { return SRMECH_ERR_BAD_INPUT; }
    if (num_terms > BIGEXP_LOG_MAX_TERMS) { return SRMECH_ERR_BAD_INPUT; }
    /* Domain -1 < p/q ≤ 1: refuse p > q OR p ≤ -q (matches Python). */
    if (srmech_bigint_cmp(x_num, x_den) > 0) { return SRMECH_ERR_BAD_INPUT; }
    { srmech_bigint_t negd = *x_den; negd.sign = -negd.sign;
      if (srmech_bigint_cmp(x_num, &negd) <= 0) { return SRMECH_ERR_BAD_INPUT; } }
    if (srmech_bigint_is_zero(x_num) || num_terms == 0u) {  /* log1p(0)=0/1 */
        st = srmech_bigint_set_i64(out_num, 0);
        if (st != SRMECH_OK) { return st; }
        return srmech_bigint_set_i64(out_den, 1);
    }
    cap = (uint32_t)bigexp_cap_for(x_num->n, x_den->n, num_terms + 1u);
    st = bigexp_ctx_init(&c, cap, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&c.num, 0);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&c.den, 1);
    if (st != SRMECH_OK) { return st; }
    for (k = 1u; k <= num_terms; k++) {
        st = srmech_bigint_set_i64(&c.t4, (int64_t)k);  /* divisor k */
        if (st != SRMECH_OK) { return st; }
        /* (-1)^(k+1): negate when k even. */
        st = bigexp_pow_term(&c, x_num, x_den, k, (k % 2u) == 0u, &c.t4,
                             &c.t2, &c.t3);
        if (st != SRMECH_OK) { return st; }
        st = bigexp_fold_term(&c, &c.t2, &c.t3);
        if (st != SRMECH_OK) { return st; }
        st = bigexp_reduce_out(&c, &c.num, &c.den);
        if (st != SRMECH_OK) { return st; }
    }
    return bigexp_reduce_out(&c, out_num, out_den);
}

/* ---- rational_pow_uint (p/q)^n = p^n / q^n, reduced ---------------- */

srmech_status_t srmech_rational_pow_uint_big(const srmech_bigint_t *base_num,
                                             const srmech_bigint_t *base_den,
                                             uint32_t exp_val,
                                             srmech_bigint_t *out_num,
                                             srmech_bigint_t *out_den,
                                             void *ws, size_t ws_len)
{
    bigexp_ctx_t c;
    srmech_status_t st;
    uint32_t cap;
    assert(out_num != NULL && out_den != NULL);
    assert(base_num != NULL && base_den != NULL);
    if (out_num == NULL || out_den == NULL
        || base_num == NULL || base_den == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (base_den->sign <= 0) { return SRMECH_ERR_BAD_INPUT; }
    if (exp_val > BIGEXP_POW_MAX_EXP) { return SRMECH_ERR_BAD_INPUT; }
    cap = (uint32_t)bigexp_cap_for(base_num->n, base_den->n, exp_val);
    st = bigexp_ctx_init(&c, cap, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    st = bigexp_pow(&c, &c.num, base_num, exp_val);   /* p^n */
    if (st != SRMECH_OK) { return st; }
    st = bigexp_pow(&c, &c.den, base_den, exp_val);   /* q^n */
    if (st != SRMECH_OK) { return st; }
    return bigexp_reduce_out(&c, out_num, out_den);
}
