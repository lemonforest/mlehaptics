/*
 * srmech_jacobi.c — BIGNUM-EXACT Jacobi elliptic sn/cn/dn Maclaurin truncation
 * on the caller-arena srmech_bigint (the C peer of
 * srmech.amsc.rational.jacobi_sncndn_series_truncate).
 *
 * The Python op is the exact-rational "rotation-last" sibling of
 * sin/cos_series_truncate: it builds the Maclaurin coefficient sequences of
 * the three Jacobi elliptic functions from the coupled power-series ODE, then
 * evaluates each at u = p/q, all over exact rationals (CPython bignum int, NO
 * float, NO mid-body projection). This file computes the SAME exact rationals
 * over srmech_bigint (caller-owned limbs, caller-arena scratch, NO malloc), and
 * returns each reduced to lowest terms with positive denominator —
 * byte-identical to Python's (sn, cn, dn) triple at ANY magnitude.
 *
 * Recurrence (matches rational.py exactly). ODE:
 *   sn' =  cn·dn,  cn' = -sn·dn,  dn' = -m·sn·cn ;  sn(0)=0, cn(0)=cn(0)=1.
 * With a/b/c the Maclaurin coeffs of sn/cn/dn, a0=0, b0=c0=1, for k=0..N-1
 * (⊛ = discrete convolution Σ_{i+j=k}):
 *   a[k+1] = ( b⊛c )[k] / (k+1)
 *   b[k+1] = -( a⊛c )[k] / (k+1)
 *   c[k+1] = -m·( a⊛b )[k] / (k+1)
 * Then sn(u)=Σ a[k]·u^k, cn(u)=Σ b[k]·u^k, dn(u)=Σ c[k]·u^k.
 *
 * Each coefficient and each running sum is a rational A/B (B>0). Rational add
 * folds t_num/t_den into A/B via A=A·t_den+t_num·B, B=B·t_den, then a gcd
 * reduce; rational mul is (a_num·b_num)/(a_den·b_den) reduced. Reducing every
 * coefficient to lowest terms keeps the limb growth bounded (≤ lcm of the term
 * denominators), so the result is a property of the exact VALUE — identical to
 * Python's per-step reduce.
 *
 * Carrier-internal feed for a Rosetta-ledger Python op: srmech_jacobi_sncndn is
 * the dispatched C twin (Python routes to it when present). Additive symbol →
 * SRMECH_ABI_VERSION unchanged (stays 3).
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto/recursion): OK — iterative, flat static helpers
 *   - Rule 2 (bounded loops)    : OK — every loop bound is N (<= 50) or limb n
 *   - Rule 3 (no malloc)        : OK — caller arena + caller out only
 *   - Rule 4 (<=60 lines/func)  : OK — factored into static helpers
 *   - Rule 5 (>=2 asserts/fn)   : OK — entry-pointer + pre/postcondition
 *   - Rule 7 (return-value)     : OK — srmech_status_t propagated everywhere
 *   - Rule 8 (no multi-line mac): OK — object-like #defines only
 *   - Rule 10 (warnings clean)  : OK under -Wall -Wextra -Wpedantic -Werror
 *
 * License: MIT.
 */

#include "srmech.h"

#include <assert.h>
#include <stdint.h>

#define JAC_MAX_TERMS 50u       /* mirrors _JACOBI_SERIES_MAX_TERMS (rational.py) */

/* A rational carrier pair (num/den, den > 0), both bigints over the arena. */
typedef struct jac_rat {
    srmech_bigint_t num;
    srmech_bigint_t den;
} jac_rat_t;

/* The full working set: three coefficient arrays a/b/c (each N+1 rationals),
 * the modulus m, three running convolution sums, the running poly value +
 * u-power, and the rational-arithmetic scratch carriers. All limbs come from
 * the caller arena `ws`; the tail of `ws` is the divmod/gcd scratch. */
typedef struct jac_ctx {
    jac_rat_t       *a;         /* sn coeffs  (N+1)                 */
    jac_rat_t       *b;         /* cn coeffs  (N+1)                 */
    jac_rat_t       *c;         /* dn coeffs  (N+1)                 */
    jac_rat_t        m;         /* modulus m = m_p/m_q              */
    jac_rat_t        bc;        /* running (b⊛c) sum                */
    jac_rat_t        ac;        /* running (a⊛c) sum                */
    jac_rat_t        ab;        /* running (a⊛b) sum                */
    jac_rat_t        acc;       /* poly-eval running value          */
    jac_rat_t        upow;      /* poly-eval running u^k            */
    jac_rat_t        uval;      /* the argument u = p/q             */
    jac_rat_t        s0;        /* rational scratch (inv / term)    */
    jac_rat_t        s1;        /* rational scratch (product)       */
    srmech_bigint_t  t0;        /* mul scratch                      */
    srmech_bigint_t  t1;        /* fold scratch                     */
    srmech_bigint_t  t2;        /* fold scratch                     */
    srmech_bigint_t  t3;        /* gcd / quotient scratch           */
    srmech_bigint_t  rem;       /* divmod remainder sink            */
    uint32_t         limb_cap;  /* per-carrier limb capacity        */
    uint32_t         n_terms;   /* truncation order N               */
    void            *scratch;   /* divmod/gcd arena tail            */
    size_t           scratch_len;
} jac_ctx_t;

/* ---- forward declarations (Rule 1: no recursion) ------------------- */

static uint32_t *jac_take(uint32_t *base, size_t words, size_t *cur,
                          size_t count);
static srmech_status_t jac_bind(srmech_bigint_t *b, uint32_t *base,
                                size_t words, size_t *cur, uint32_t cap);
static srmech_status_t jac_bind_rat(jac_rat_t *r, uint32_t *base, size_t words,
                                    size_t *cur, uint32_t cap);
static srmech_status_t jac_mul(jac_ctx_t *c, srmech_bigint_t *out,
                               const srmech_bigint_t *a,
                               const srmech_bigint_t *b);
static srmech_status_t jac_reduce(jac_ctx_t *c, jac_rat_t *r);
static srmech_status_t jac_rat_mul(jac_ctx_t *c, jac_rat_t *out,
                                   const jac_rat_t *x, const jac_rat_t *y);
static srmech_status_t jac_rat_add(jac_ctx_t *c, jac_rat_t *acc,
                                   const jac_rat_t *t);
static srmech_status_t jac_set_small(jac_rat_t *r, int64_t num, int64_t den);
static srmech_status_t jac_conv_step(jac_ctx_t *c, uint32_t k);
static srmech_status_t jac_recurrence(jac_ctx_t *c);
static srmech_status_t jac_eval_poly(jac_ctx_t *c, const jac_rat_t *coeffs,
                                     srmech_bigint_t *out_num,
                                     srmech_bigint_t *out_den);

/* ---- caller-arena carve (mirrors bigexp_take / bigexp_bind) -------- */

static uint32_t *jac_take(uint32_t *base, size_t words, size_t *cur,
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

static srmech_status_t jac_bind(srmech_bigint_t *b, uint32_t *base,
                                size_t words, size_t *cur, uint32_t cap)
{
    uint32_t *limbs = jac_take(base, words, cur, cap);
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

static srmech_status_t jac_bind_rat(jac_rat_t *r, uint32_t *base, size_t words,
                                    size_t *cur, uint32_t cap)
{
    srmech_status_t st;
    assert(r != NULL && base != NULL && cur != NULL);
    assert(cap > 0u);
    st = jac_bind(&r->num, base, words, cur, cap);
    if (st != SRMECH_OK) { return st; }
    return jac_bind(&r->den, base, words, cur, cap);
}

/* out = a * b via scratch t0 so out may alias a/b. */
static srmech_status_t jac_mul(jac_ctx_t *c, srmech_bigint_t *out,
                               const srmech_bigint_t *a,
                               const srmech_bigint_t *b)
{
    srmech_status_t st;
    assert(c != NULL && out != NULL && a != NULL && b != NULL);
    assert(out != &c->t0);                          /* t0 is the mul scratch */
    st = srmech_bigint_mul(&c->t0, a, b);
    if (st != SRMECH_OK) { return st; }
    return srmech_bigint_copy(out, &c->t0);
}

/* r <- reduce(r) to lowest terms, positive denominator. den stays > 0
 * throughout (every constructed denominator is positive). */
static srmech_status_t jac_reduce(jac_ctx_t *c, jac_rat_t *r)
{
    srmech_status_t st;
    assert(c != NULL && r != NULL);
    assert(r->den.sign > 0);                        /* denominator positive */
    if (srmech_bigint_is_zero(&r->num)) {
        st = srmech_bigint_set_i64(&r->num, 0);
        if (st != SRMECH_OK) { return st; }
        return srmech_bigint_set_i64(&r->den, 1);
    }
    st = srmech_bigint_gcd(&c->t3, &r->num, &r->den,
                           c->scratch, c->scratch_len);  /* t3 = gcd */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_divmod(&c->t1, &c->rem, &r->num, &c->t3,
                              c->scratch, c->scratch_len);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_divmod(&c->t2, &c->rem, &r->den, &c->t3,
                              c->scratch, c->scratch_len);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&r->num, &c->t1);
    if (st != SRMECH_OK) { return st; }
    return srmech_bigint_copy(&r->den, &c->t2);
}

/* out <- reduce(x * y).  out must NOT alias x or y (writes num then den). */
static srmech_status_t jac_rat_mul(jac_ctx_t *c, jac_rat_t *out,
                                   const jac_rat_t *x, const jac_rat_t *y)
{
    srmech_status_t st;
    assert(c != NULL && out != NULL && x != NULL && y != NULL);
    assert(out != x && out != y);
    st = jac_mul(c, &out->num, &x->num, &y->num);   /* num = x_n·y_n */
    if (st != SRMECH_OK) { return st; }
    st = jac_mul(c, &out->den, &x->den, &y->den);   /* den = x_d·y_d */
    if (st != SRMECH_OK) { return st; }
    return jac_reduce(c, out);
}

/* acc <- reduce(acc + t).  acc = (A/B) + (t_n/t_d):
 *   A = A·t_d + t_n·B ; B = B·t_d ; then reduce. t1/t2 scratch. */
static srmech_status_t jac_rat_add(jac_ctx_t *c, jac_rat_t *acc,
                                   const jac_rat_t *t)
{
    srmech_status_t st;
    assert(c != NULL && acc != NULL && t != NULL);
    assert(acc != t);
    st = jac_mul(c, &c->t1, &acc->num, &t->den);    /* t1 = A·t_d */
    if (st != SRMECH_OK) { return st; }
    st = jac_mul(c, &c->t2, &t->num, &acc->den);    /* t2 = t_n·B */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_add(&acc->num, &c->t1, &c->t2);
    if (st != SRMECH_OK) { return st; }
    st = jac_mul(c, &acc->den, &acc->den, &t->den); /* B = B·t_d */
    if (st != SRMECH_OK) { return st; }
    return jac_reduce(c, acc);
}

/* r <- num/den (small i64 literals; den > 0). Used for the 0/1 and 1/1 seeds
 * and the per-step 1/(k+1) factor. */
static srmech_status_t jac_set_small(jac_rat_t *r, int64_t num, int64_t den)
{
    srmech_status_t st;
    assert(r != NULL);
    assert(den > 0);
    st = srmech_bigint_set_i64(&r->num, num);
    if (st != SRMECH_OK) { return st; }
    return srmech_bigint_set_i64(&r->den, den);
}

/* Build the a/b/c coefficient sequences (indices 0..N) in place. */
static srmech_status_t jac_conv_step(jac_ctx_t *c, uint32_t k)
{
    srmech_status_t st;
    uint32_t i, j;
    assert(c != NULL);
    assert(k <= c->n_terms);
    st = jac_set_small(&c->bc, 0, 1); if (st != SRMECH_OK) { return st; }
    st = jac_set_small(&c->ac, 0, 1); if (st != SRMECH_OK) { return st; }
    st = jac_set_small(&c->ab, 0, 1); if (st != SRMECH_OK) { return st; }
    for (i = 0u; i <= k; i++) {
        j = k - i;
        st = jac_rat_mul(c, &c->s1, &c->b[i], &c->c[j]);
        if (st != SRMECH_OK) { return st; }
        st = jac_rat_add(c, &c->bc, &c->s1); if (st != SRMECH_OK) { return st; }
        st = jac_rat_mul(c, &c->s1, &c->a[i], &c->c[j]);
        if (st != SRMECH_OK) { return st; }
        st = jac_rat_add(c, &c->ac, &c->s1); if (st != SRMECH_OK) { return st; }
        st = jac_rat_mul(c, &c->s1, &c->a[i], &c->b[j]);
        if (st != SRMECH_OK) { return st; }
        st = jac_rat_add(c, &c->ab, &c->s1); if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

static srmech_status_t jac_recurrence(jac_ctx_t *c)
{
    srmech_status_t st;
    uint32_t k;
    assert(c != NULL);
    assert(c->n_terms <= JAC_MAX_TERMS);
    st = jac_set_small(&c->a[0], 0, 1); if (st != SRMECH_OK) { return st; }
    st = jac_set_small(&c->b[0], 1, 1); if (st != SRMECH_OK) { return st; }
    st = jac_set_small(&c->c[0], 1, 1); if (st != SRMECH_OK) { return st; }
    for (k = 0u; k < c->n_terms; k++) {
        st = jac_conv_step(c, k);
        if (st != SRMECH_OK) { return st; }
        st = jac_set_small(&c->s0, 1, (int64_t)k + 1);      /* s0 = 1/(k+1) */
        if (st != SRMECH_OK) { return st; }
        st = jac_rat_mul(c, &c->a[k + 1], &c->bc, &c->s0);  /* a = (b⊛c)/(k+1) */
        if (st != SRMECH_OK) { return st; }
        /* Class-K sign-flip the convolution numerators (never abs()). */
        c->ac.num.sign = (c->ac.num.sign == 0) ? 0 : -c->ac.num.sign;
        st = jac_rat_mul(c, &c->b[k + 1], &c->ac, &c->s0);  /* b = -(a⊛c)/(k+1) */
        if (st != SRMECH_OK) { return st; }
        c->ab.num.sign = (c->ab.num.sign == 0) ? 0 : -c->ab.num.sign;
        st = jac_rat_mul(c, &c->s1, &c->ab, &c->m);         /* s1 = -m·(a⊛b) */
        if (st != SRMECH_OK) { return st; }
        st = jac_rat_mul(c, &c->c[k + 1], &c->s1, &c->s0);  /* c = -m(a⊛b)/(k+1) */
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* out_num/out_den = reduce(Σ_k coeffs[k]·u^k), u = uval. Accumulates u^k
 * incrementally in upow; both borrowed back to dedicated carriers here. */
static srmech_status_t jac_eval_poly(jac_ctx_t *c, const jac_rat_t *coeffs,
                                     srmech_bigint_t *out_num,
                                     srmech_bigint_t *out_den)
{
    srmech_status_t st;
    uint32_t k;
    assert(c != NULL && coeffs != NULL && out_num != NULL && out_den != NULL);
    assert(c->n_terms <= JAC_MAX_TERMS);
    st = jac_set_small(&c->acc, 0, 1);  if (st != SRMECH_OK) { return st; }
    st = jac_set_small(&c->upow, 1, 1); if (st != SRMECH_OK) { return st; }
    for (k = 0u; k <= c->n_terms; k++) {
        if (k > 0u) {
            st = jac_rat_mul(c, &c->s1, &c->upow, &c->uval);  /* s1 = u^(k) */
            if (st != SRMECH_OK) { return st; }
            st = srmech_bigint_copy(&c->upow.num, &c->s1.num);
            if (st != SRMECH_OK) { return st; }
            st = srmech_bigint_copy(&c->upow.den, &c->s1.den);
            if (st != SRMECH_OK) { return st; }
        }
        if (!srmech_bigint_is_zero(&coeffs[k].num)) {
            st = jac_rat_mul(c, &c->s1, &coeffs[k], &c->upow);
            if (st != SRMECH_OK) { return st; }
            st = jac_rat_add(c, &c->acc, &c->s1);
            if (st != SRMECH_OK) { return st; }
        }
    }
    st = srmech_bigint_copy(out_num, &c->acc.num);
    if (st != SRMECH_OK) { return st; }
    return srmech_bigint_copy(out_den, &c->acc.den);
}

/* ---- arena sizing ------------------------------------------------- */

/* Per-carrier limb cap. The reduced coefficients grow like (k+1)!·m_den^k for
 * k <= N; the poly-eval running value adds q^N + p^N. Budget a generous
 * envelope: factorial(N) ~ N·14 bits, plus N·(m + p + q) limbs, ×2 for the
 * unreduced fold intermediate, + slack. Over-sizing is free (caller arena). */
static uint32_t jac_cap_for(size_t p_limbs, size_t q_limbs,
                            size_t mp_limbs, size_t mq_limbs, uint32_t n)
{
    size_t fact_bits = (size_t)n * 14u + 64u;       /* >= log2(N!) for N<=2048 */
    size_t fact_limbs = fact_bits / 32u + 2u;
    size_t pe = srmech_bigint_pow_bound(p_limbs == 0u ? 1u : p_limbs, n);
    size_t qe = srmech_bigint_pow_bound(q_limbs == 0u ? 1u : q_limbs, n);
    size_t me = srmech_bigint_pow_bound(
        (mp_limbs > mq_limbs ? mp_limbs : mq_limbs), n);
    size_t one = fact_limbs + pe + qe + me;
    size_t cap = one * 2u + 32u;                    /* unreduced product + slack */
    assert(cap >= one);
    assert(cap >= fact_limbs);
    return (uint32_t)cap;
}

/* ---- ctx init ----------------------------------------------------- */

static srmech_status_t jac_ctx_init(jac_ctx_t *c, uint32_t cap, uint32_t n,
                                    jac_rat_t *rats, void *ws, size_t ws_len)
{
    uint32_t *base = (uint32_t *)ws;
    size_t words = ws_len / sizeof(uint32_t), cur = 0u;
    srmech_status_t st = SRMECH_OK;
    uint32_t i;
    assert(c != NULL && rats != NULL);
    assert((uintptr_t)ws % sizeof(uint32_t) == 0u || ws == NULL);
    c->limb_cap = cap;
    c->n_terms = n;
    c->a = rats;
    c->b = rats + (size_t)(n + 1u);
    c->c = rats + (size_t)(n + 1u) * 2u;
    for (i = 0u; i < (n + 1u) * 3u; i++) {
        st |= jac_bind_rat(&rats[i], base, words, &cur, cap);
    }
    st |= jac_bind_rat(&c->m,    base, words, &cur, cap);
    st |= jac_bind_rat(&c->bc,   base, words, &cur, cap);
    st |= jac_bind_rat(&c->ac,   base, words, &cur, cap);
    st |= jac_bind_rat(&c->ab,   base, words, &cur, cap);
    st |= jac_bind_rat(&c->acc,  base, words, &cur, cap);
    st |= jac_bind_rat(&c->upow, base, words, &cur, cap);
    st |= jac_bind_rat(&c->uval, base, words, &cur, cap);
    st |= jac_bind_rat(&c->s0,   base, words, &cur, cap);
    st |= jac_bind_rat(&c->s1,   base, words, &cur, cap);
    st |= jac_bind(&c->t0,  base, words, &cur, cap);
    st |= jac_bind(&c->t1,  base, words, &cur, cap);
    st |= jac_bind(&c->t2,  base, words, &cur, cap);
    st |= jac_bind(&c->t3,  base, words, &cur, cap);
    st |= jac_bind(&c->rem, base, words, &cur, cap);
    if (st != SRMECH_OK) {
        return SRMECH_ERR_OVERFLOW;
    }
    c->scratch = (void *)(base + cur);
    c->scratch_len = (words - cur) * sizeof(uint32_t);
    assert(cur <= words);
    return SRMECH_OK;
}

/* ---- public ws-bound + entry point -------------------------------- */

size_t srmech_jacobi_sncndn_ws_bound(size_t num_limbs, size_t den_limbs,
                                     size_t m_num_limbs, size_t m_den_limbs,
                                     uint32_t num_terms)
{
    uint32_t n = (num_terms > JAC_MAX_TERMS) ? JAC_MAX_TERMS : num_terms;
    uint32_t cap = jac_cap_for(num_limbs, den_limbs,
                               m_num_limbs, m_den_limbs, n);
    /* carriers: 3·(N+1) coeff rationals + 11 named rationals (m, bc, ac, ab,
     * acc, upow, uval, s0, s1 — 9; plus 2 slack) + 5 scalars (t0..t3, rem),
     * each rational = 2 carriers of `cap` limbs. */
    size_t rat_carriers = ((size_t)(n + 1u) * 3u + 11u) * 2u;
    size_t scalar_carriers = 5u;
    size_t carriers = (rat_carriers + scalar_carriers) * (size_t)cap;
    size_t scratch = (size_t)cap * 8u + 256u;       /* divmod/gcd envelope */
    size_t words = carriers + scratch;
    assert(cap >= 2u);
    assert(words >= carriers);
    return words * sizeof(uint32_t);
}

/* The coefficient-rational structs (a/b/c, 3·(N+1) of them) live on a
 * fixed-size stack array (Rule 3: no malloc) bounded by 3·(JAC_MAX_TERMS+1);
 * only their limb buffers come from the caller arena. The named scratch
 * rationals (m, bc, ... s1) are jac_ctx_t members. */
#define JAC_RAT_SLOTS (3u * (JAC_MAX_TERMS + 1u))

srmech_status_t srmech_jacobi_sncndn(const srmech_bigint_t *u_num,
                                     const srmech_bigint_t *u_den,
                                     const srmech_bigint_t *m_num,
                                     const srmech_bigint_t *m_den,
                                     uint32_t num_terms,
                                     srmech_bigint_t *sn_num,
                                     srmech_bigint_t *sn_den,
                                     srmech_bigint_t *cn_num,
                                     srmech_bigint_t *cn_den,
                                     srmech_bigint_t *dn_num,
                                     srmech_bigint_t *dn_den,
                                     void *ws, size_t ws_len)
{
    jac_ctx_t c;
    jac_rat_t rats[JAC_RAT_SLOTS];
    srmech_status_t st;
    uint32_t cap;
    assert(u_num != NULL && u_den != NULL && m_num != NULL && m_den != NULL);
    assert(sn_num != NULL && dn_den != NULL);
    if (u_num == NULL || u_den == NULL || m_num == NULL || m_den == NULL ||
        sn_num == NULL || sn_den == NULL || cn_num == NULL || cn_den == NULL ||
        dn_num == NULL || dn_den == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (u_den->sign <= 0 || m_den->sign <= 0) { return SRMECH_ERR_BAD_INPUT; }
    if (num_terms > JAC_MAX_TERMS) { return SRMECH_ERR_BAD_INPUT; }
    cap = jac_cap_for(u_num->n, u_den->n, m_num->n, m_den->n, num_terms);
    st = jac_ctx_init(&c, cap, num_terms, rats, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    /* Seed m = m_num/m_den (reduced) and u = u_num/u_den (reduced). */
    st = srmech_bigint_copy(&c.m.num, m_num);   if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&c.m.den, m_den);   if (st != SRMECH_OK) { return st; }
    st = jac_reduce(&c, &c.m);                  if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&c.uval.num, u_num); if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&c.uval.den, u_den); if (st != SRMECH_OK) { return st; }
    st = jac_reduce(&c, &c.uval);               if (st != SRMECH_OK) { return st; }
    st = jac_recurrence(&c);                    if (st != SRMECH_OK) { return st; }
    st = jac_eval_poly(&c, c.a, sn_num, sn_den); if (st != SRMECH_OK) { return st; }
    st = jac_eval_poly(&c, c.b, cn_num, cn_den); if (st != SRMECH_OK) { return st; }
    return jac_eval_poly(&c, c.c, dn_num, dn_den);
}
