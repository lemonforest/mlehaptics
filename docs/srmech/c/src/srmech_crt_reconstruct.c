/*
 * srmech_crt_reconstruct.c -- the CRT closers (srmech 0.9.0rc45, rung 2 of the
 * CRT-QMat re-fibration arc).
 *
 * After the swell-free GF(p) elimination (srmech_gf_rref, rung 1) has produced
 * one residue per reduction prime, these two ops turn the per-prime residues
 * back into the EXACT rational answer:
 *
 *   srmech_crt_combine          -- Class I: CRT-combine k congruences
 *                                  r_i (mod m_i) into one residue mod prod(m_i),
 *                                  via iterative Garner. The combined modulus
 *                                  exceeds 64 bits for k >= 3 of the ~31-bit
 *                                  reduction primes, so the accumulator is
 *                                  bignum (srmech_bigint); only the per-step
 *                                  inverse, taken modulo a single uint64 prime,
 *                                  stays inside uint64.
 *   srmech_rational_reconstruct -- Class N: recover the bounded p/q congruent
 *                                  to a residue modulo the combined modulus, via
 *                                  the half-GCD (Wang) extended-Euclidean
 *                                  recurrence over srmech_bigint.
 *
 * Byte-identical to the pure-Python srmech.amsc.modular_linalg.crt_combine /
 * srmech.amsc.rational.rational_reconstruct (their parity oracle). Both run over
 * the caller-arena srmech_bigint -- caller-owned out limbs, caller-arena scratch,
 * NO malloc. Sign is Class-K: an explicit sign-branch, never abs().
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto/recursion): OK -- iterative, flat static helpers
 *   - Rule 2 (bounded loops)    : OK -- k congruences / the Euclid remainder
 *   - Rule 3 (no malloc)        : OK -- caller arena + caller out only
 *   - Rule 4 (<=60 lines/func)  : OK -- factored into static helpers
 *   - Rule 5 (>=2 asserts/fn)   : OK -- entry-pointer + pre/postcondition
 *   - Rule 7 (return-value)     : OK -- srmech_status_t propagated
 *   - Rule 8 (no multi-line mac): OK -- no function-like macros
 *   - Rule 10 (warnings clean)  : OK under -Wall -Wextra -Wpedantic -Werror
 *
 * License: MIT.
 */

#include "srmech.h"

#include <assert.h>
#include <stdint.h>

/* The reduction primes m_i are < 2**31 (the gf_rref field bound), so a*b fits
 * uint64 with no doubling. This cap bounds the uint64 helpers' domain. */
#define CRT_MOD_CEILING (((uint64_t)1) << 31)

/* ------------------------------------------------------------------ *
 * uint64 modular helpers (the per-step inverse rides a single prime).
 * ------------------------------------------------------------------ */

/* (a * b) mod m, with a, b already in [0, m) and m < 2**31 so a*b < 2**62. */
static uint64_t crt_mulmod(uint64_t a, uint64_t b, uint64_t m)
{
    assert(m >= 2u);
    assert(a < m && b < m);
    return (a * b) % m;
}

/* Modular inverse of a in (Z/mZ)* via extended Euclidean (works for any modulus
 * coprime to a, not just a prime). Returns 0 iff gcd(a, m) != 1 (no inverse);
 * the caller guarantees coprimality (distinct primes), so a valid inverse is in
 * [1, m). The signed running coefficients stay within int64 for m < 2**31. */
static uint64_t crt_invmod(uint64_t a, uint64_t m)
{
    int64_t t = 0;
    int64_t newt = 1;
    int64_t r = (int64_t)m;
    int64_t newr = (int64_t)(a % m);
    assert(m >= 2u);
    assert(m < CRT_MOD_CEILING);
    while (newr != 0) {
        int64_t quot = r / newr;
        int64_t tmp = t - quot * newt;
        t = newt;
        newt = tmp;
        tmp = r - quot * newr;
        r = newr;
        newr = tmp;
    }
    if (r != 1) {
        return 0u;                              /* not invertible */
    }
    if (t < 0) {                                /* Class-K: lift into [0, m) */
        t += (int64_t)m;
    }
    return (uint64_t)t;
}

/* ------------------------------------------------------------------ *
 * srmech_bigint glue: a working roster carved from the caller arena.
 * ------------------------------------------------------------------ */

typedef struct crt_ctx {
    srmech_bigint_t cur;      /* running CRT residue (bignum)        */
    srmech_bigint_t modulus;  /* running product of primes (bignum)  */
    srmech_bigint_t t0;       /* scratch carriers                    */
    srmech_bigint_t t1;
    srmech_bigint_t t2;
    srmech_bigint_t rem;      /* divmod remainder sink               */
    srmech_bigint_t small;    /* a single uint64 lifted to bignum    */
    uint32_t limb_cap;        /* per-carrier limb capacity           */
    void  *scratch;           /* divmod/gcd arena tail               */
    size_t scratch_len;       /* its length in BYTES                 */
} crt_ctx_t;

#define CRT_N_CARRIERS 7u     /* cur,modulus,t0,t1,t2,rem,small */

static uint32_t *crt_take(uint32_t *base, size_t words, size_t *cur,
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

static srmech_status_t crt_bind(srmech_bigint_t *b, uint32_t *base,
                                size_t words, size_t *cur, uint32_t cap)
{
    uint32_t *limbs = crt_take(base, words, cur, cap);
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

static srmech_status_t crt_ctx_init(crt_ctx_t *c, uint32_t cap,
                                    void *ws, size_t ws_len)
{
    uint32_t *base = (uint32_t *)ws;
    size_t words = ws_len / sizeof(uint32_t);
    size_t pos = 0u;
    srmech_status_t st = SRMECH_OK;
    assert(c != NULL);
    assert(ws != NULL);
    c->limb_cap = cap;
    st |= crt_bind(&c->cur, base, words, &pos, cap);
    st |= crt_bind(&c->modulus, base, words, &pos, cap);
    st |= crt_bind(&c->t0, base, words, &pos, cap);
    st |= crt_bind(&c->t1, base, words, &pos, cap);
    st |= crt_bind(&c->t2, base, words, &pos, cap);
    st |= crt_bind(&c->rem, base, words, &pos, cap);
    st |= crt_bind(&c->small, base, words, &pos, cap);
    if (st != SRMECH_OK) {
        return SRMECH_ERR_OVERFLOW;
    }
    c->scratch = (void *)(base + pos);
    c->scratch_len = (words - pos) * sizeof(uint32_t);
    assert(pos <= words);
    return SRMECH_OK;
}

/* out = (uint64) v, always non-negative (two 32-bit limbs). */
static srmech_status_t crt_set_u64(srmech_bigint_t *out, uint64_t v)
{
    assert(out != NULL);
    assert(out->cap >= 2u);
    out->n = 0u;
    out->sign = 0;
    if (v != 0u) {
        out->limbs[0] = (uint32_t)(v & 0xFFFFFFFFu);
        out->n = 1u;
        if ((v >> 32) != 0u) {
            out->limbs[1] = (uint32_t)(v >> 32);
            out->n = 2u;
        }
        out->sign = 1;
    }
    return SRMECH_OK;
}

/* r = a mod m (m a uint64 in [2, 2**31)); returns the remainder as a uint64.
 * Uses srmech_bigint_divmod (q skipped) into c->rem, then reads its low limb(s).
 * a is non-negative on entry (CRT residues are non-negative). */
static srmech_status_t crt_mod_u64(crt_ctx_t *c, const srmech_bigint_t *a,
                                   uint64_t m, uint64_t *out_r)
{
    srmech_status_t st;
    uint64_t r;
    assert(c != NULL && a != NULL && out_r != NULL);
    assert(m >= 2u && m < CRT_MOD_CEILING);
    st = crt_set_u64(&c->small, m);
    if (st != SRMECH_OK) { return st; }
    /* A real quotient sink (t0): the bigint divmod writes the full quotient even
     * when asked to skip it via a cap-0 NULL stand-in, so never pass q == NULL. */
    st = srmech_bigint_divmod(&c->t0, &c->rem, a, &c->small,
                              c->scratch, c->scratch_len);
    if (st != SRMECH_OK) { return st; }
    r = 0u;
    if (c->rem.n >= 1u) {
        r = (uint64_t)c->rem.limbs[0];
    }
    if (c->rem.n >= 2u) {
        r |= ((uint64_t)c->rem.limbs[1]) << 32;
    }
    *out_r = r;
    return SRMECH_OK;
}

/* ------------------------------------------------------------------ *
 * srmech_crt_combine.
 * ------------------------------------------------------------------ */

size_t srmech_crt_combine_ws_bound(size_t k)
{
    /* The running product grows ~31 bits per prime -> ~k limbs; the carriers
     * hold ~2k limbs (product * a single-limb multiplier) and the divmod arena
     * a few multiples of that. A generous envelope: (8k + 64) limbs in BYTES. */
    size_t limbs = (k * 8u) + 64u;
    assert(limbs > k);                          /* size_t did not wrap */
    assert(limbs >= 64u);
    return (limbs * CRT_N_CARRIERS + limbs * 8u) * sizeof(uint32_t);
}

/* Fold prime i: cur += modulus * t ; modulus *= m_i. t is a uint64 in [0, m_i).
 * t0 = modulus * t ; cur = cur + t0 ; modulus = modulus * m_i. */
static srmech_status_t crt_fold(crt_ctx_t *c, uint64_t t, uint64_t m_i)
{
    srmech_status_t st;
    assert(c != NULL);
    assert(m_i >= 2u && m_i < CRT_MOD_CEILING);
    st = crt_set_u64(&c->small, t);                 /* small = t */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_mul(&c->t0, &c->modulus, &c->small);  /* t0 = mod*t */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_add(&c->t1, &c->cur, &c->t0);         /* t1 = cur+t0 */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&c->cur, &c->t1);               /* cur = t1 */
    if (st != SRMECH_OK) { return st; }
    st = crt_set_u64(&c->small, m_i);                       /* small = m_i */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_mul(&c->t2, &c->modulus, &c->small);  /* t2 = mod*m_i */
    if (st != SRMECH_OK) { return st; }
    return srmech_bigint_copy(&c->modulus, &c->t2);         /* modulus = t2 */
}

srmech_status_t srmech_crt_combine(const uint64_t *residues,
                                   const uint64_t *moduli,
                                   uint32_t k,
                                   srmech_bigint_t *out_residue,
                                   srmech_bigint_t *out_modulus,
                                   void *ws, size_t ws_len)
{
    crt_ctx_t c;
    srmech_status_t st;
    uint32_t i;
    uint32_t cap;
    assert(residues != NULL && moduli != NULL);
    assert(out_residue != NULL && out_modulus != NULL);
    if (residues == NULL || moduli == NULL || out_residue == NULL
        || out_modulus == NULL || ws == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (k == 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    for (i = 0u; i < k; i++) {
        if (moduli[i] < 2u || moduli[i] >= CRT_MOD_CEILING) {
            return SRMECH_ERR_BAD_INPUT;
        }
    }
    cap = (uint32_t)((k * 8u) + 64u);
    st = crt_ctx_init(&c, cap, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    /* Seed with the first congruence reduced into [0, m_0). */
    st = crt_set_u64(&c.cur, residues[0] % moduli[0]);
    if (st != SRMECH_OK) { return st; }
    st = crt_set_u64(&c.modulus, moduli[0]);
    if (st != SRMECH_OK) { return st; }
    for (i = 1u; i < k; i++) {
        uint64_t m_i = moduli[i];
        uint64_t mr;            /* modulus mod m_i */
        uint64_t cr;            /* cur mod m_i     */
        uint64_t inv;
        uint64_t diff;
        uint64_t t;
        st = crt_mod_u64(&c, &c.modulus, m_i, &mr);
        if (st != SRMECH_OK) { return st; }
        st = crt_mod_u64(&c, &c.cur, m_i, &cr);
        if (st != SRMECH_OK) { return st; }
        inv = crt_invmod(mr, m_i);
        if (inv == 0u) {
            return SRMECH_ERR_BAD_INPUT;        /* moduli not coprime */
        }
        /* diff = (r_i - cur) mod m_i, Class-K non-negative lift. */
        diff = (residues[i] % m_i + m_i - cr) % m_i;
        t = crt_mulmod(diff, inv, m_i);
        st = crt_fold(&c, t, m_i);
        if (st != SRMECH_OK) { return st; }
    }
    /* cur is already in [0, modulus): each fold adds modulus*t with t < m_i, so
     * cur stays below the new modulus = old_modulus * m_i. Copy out. */
    st = srmech_bigint_copy(out_residue, &c.cur);
    if (st != SRMECH_OK) { return st; }
    return srmech_bigint_copy(out_modulus, &c.modulus);
}

/* ------------------------------------------------------------------ *
 * srmech_rational_reconstruct -- half-GCD (Wang) reconstruction.
 * ------------------------------------------------------------------ */

/* A second roster for the extended-Euclidean recurrence (r0,r1 / t0c,t1c) plus
 * the quotient + the temporaries. Sized off the modulus limb count. */
typedef struct rr_ctx {
    srmech_bigint_t r0;       /* Euclid remainder pair    */
    srmech_bigint_t r1;
    srmech_bigint_t t0c;      /* t-coefficient pair       */
    srmech_bigint_t t1c;
    srmech_bigint_t q;        /* quotient                 */
    srmech_bigint_t prod;     /* q * r1 / q * t1c         */
    srmech_bigint_t tmp;      /* recurrence tmp           */
    srmech_bigint_t g;        /* gcd carrier              */
    srmech_bigint_t rem;      /* divmod remainder sink    */
    uint32_t limb_cap;
    void  *scratch;
    size_t scratch_len;
} rr_ctx_t;

#define RR_N_CARRIERS 9u      /* r0,r1,t0c,t1c,q,prod,tmp,g,rem */

static srmech_status_t rr_bind(srmech_bigint_t *b, uint32_t *base,
                               size_t words, size_t *cur, uint32_t cap)
{
    uint32_t *limbs = crt_take(base, words, cur, cap);   /* reuse crt_take */
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

static srmech_status_t rr_ctx_init(rr_ctx_t *c, uint32_t cap,
                                   void *ws, size_t ws_len)
{
    uint32_t *base = (uint32_t *)ws;
    size_t words = ws_len / sizeof(uint32_t);
    size_t pos = 0u;
    srmech_status_t st = SRMECH_OK;
    assert(c != NULL);
    assert(ws != NULL);
    c->limb_cap = cap;
    st |= rr_bind(&c->r0, base, words, &pos, cap);
    st |= rr_bind(&c->r1, base, words, &pos, cap);
    st |= rr_bind(&c->t0c, base, words, &pos, cap);
    st |= rr_bind(&c->t1c, base, words, &pos, cap);
    st |= rr_bind(&c->q, base, words, &pos, cap);
    st |= rr_bind(&c->prod, base, words, &pos, cap);
    st |= rr_bind(&c->tmp, base, words, &pos, cap);
    st |= rr_bind(&c->g, base, words, &pos, cap);
    st |= rr_bind(&c->rem, base, words, &pos, cap);
    if (st != SRMECH_OK) {
        return SRMECH_ERR_OVERFLOW;
    }
    c->scratch = (void *)(base + pos);
    c->scratch_len = (words - pos) * sizeof(uint32_t);
    assert(pos <= words);
    return SRMECH_OK;
}

/* One Euclid step on (r0,r1) carrying the t-coefficient (t0c,t1c):
 *   q = r0 / r1 ; (r0,r1) = (r1, r0 - q*r1) ; (t0c,t1c) = (t1c, t0c - q*t1c).
 * NOTE srmech_bigint_divmod does NOT allow q aliasing the dividend, so the
 * quotient lands in c->q (distinct) and the new remainder in c->rem. */
static srmech_status_t rr_euclid_step(rr_ctx_t *c)
{
    srmech_status_t st;
    assert(c != NULL);
    assert(!srmech_bigint_is_zero(&c->r1));
    st = srmech_bigint_divmod(&c->q, &c->rem, &c->r0, &c->r1,
                              c->scratch, c->scratch_len);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&c->r0, &c->r1);            /* r0 = r1 */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&c->r1, &c->rem);           /* r1 = r0 - q*r1 */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_mul(&c->prod, &c->q, &c->t1c);   /* prod = q*t1c */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_sub(&c->tmp, &c->t0c, &c->prod); /* tmp = t0c - prod */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&c->t0c, &c->t1c);          /* t0c = t1c */
    if (st != SRMECH_OK) { return st; }
    return srmech_bigint_copy(&c->t1c, &c->tmp);        /* t1c = tmp */
}

size_t srmech_rational_reconstruct_ws_bound(size_t modulus_limbs)
{
    /* Each carrier holds at most the modulus magnitude (the remainders shrink,
     * the t-coefficients grow toward the modulus); pad for the q*t product. The
     * divmod/gcd arena tail mirrors the carrier pool. */
    size_t cap = (modulus_limbs * 2u) + 16u;
    assert(cap > modulus_limbs);                /* size_t did not wrap */
    assert(cap >= 16u);
    return (cap * RR_N_CARRIERS + cap * 8u) * sizeof(uint32_t);
}

/* gcd(|a|, |b|) == 1 ? (1 = coprime, 0 = not). Uses c->g + the arena. */
static srmech_status_t rr_is_coprime(rr_ctx_t *c, const srmech_bigint_t *a,
                                     const srmech_bigint_t *b, int *out_coprime)
{
    srmech_status_t st;
    assert(c != NULL && a != NULL && b != NULL && out_coprime != NULL);
    assert(c->scratch != NULL);
    st = srmech_bigint_gcd(&c->g, a, b, c->scratch, c->scratch_len);
    if (st != SRMECH_OK) { return st; }
    *out_coprime = (c->g.n == 1u && c->g.limbs[0] == 1u) ? 1 : 0;
    return SRMECH_OK;
}

/* Seed (r0,r1)=(modulus, residue mod modulus), (t0c,t1c)=(0,1), then advance the
 * extended-Euclidean recurrence while r1 > num_bound (each step strictly shrinks
 * r1, so the loop is bounded by the Euclid depth). */
static srmech_status_t rr_run_euclid(rr_ctx_t *c, const srmech_bigint_t *residue,
                                     const srmech_bigint_t *modulus,
                                     const srmech_bigint_t *num_bound)
{
    srmech_status_t st;
    assert(c != NULL && residue != NULL && modulus != NULL && num_bound != NULL);
    assert(modulus->sign > 0);
    /* A real quotient sink (c->q): the bigint divmod writes the full quotient
     * even when asked to skip it via a cap-0 NULL stand-in -> never pass NULL. */
    st = srmech_bigint_copy(&c->r0, modulus);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_divmod(&c->q, &c->r1, residue, modulus,
                              c->scratch, c->scratch_len);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&c->t0c, 0);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&c->t1c, 1);
    if (st != SRMECH_OK) { return st; }
    while (srmech_bigint_cmp(&c->r1, num_bound) > 0) {
        if (srmech_bigint_is_zero(&c->r1)) {
            break;                              /* defensive (r1 > bound >= 0) */
        }
        st = rr_euclid_step(c);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* Validate the Euclid row (p = r1 signed, q = t1c) against the bounds + the
 * uniqueness coprimality contract; on acceptance write the reduced signed p/q
 * and set *out_found = 1, else leave *out_found = 0. */
static srmech_status_t rr_finalize(rr_ctx_t *c, const srmech_bigint_t *modulus,
                                   const srmech_bigint_t *den_bound,
                                   srmech_bigint_t *out_num,
                                   srmech_bigint_t *out_den, int32_t *out_found)
{
    srmech_status_t st;
    int coprime;
    assert(c != NULL && modulus != NULL && den_bound != NULL);
    assert(out_num != NULL && out_den != NULL && out_found != NULL);
    if (c->t1c.sign == 0) {
        return SRMECH_OK;                       /* q == 0 -> no reconstruction */
    }
    st = srmech_bigint_copy(&c->g, &c->t1c);    /* g := |t1c| (Class-K |q|) */
    if (st != SRMECH_OK) { return st; }
    c->g.sign = 1;
    if (srmech_bigint_cmp(&c->g, den_bound) > 0) {
        return SRMECH_OK;                       /* |q| > den_bound -> None */
    }
    /* Canonicalise q positive: a negative q flips both signs (Class-C reorient). */
    st = srmech_bigint_copy(out_den, &c->g);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(out_num, &c->r1);
    if (st != SRMECH_OK) { return st; }
    if (c->t1c.sign < 0 && out_num->sign != 0) {
        out_num->sign = (int32_t)(-out_num->sign);
    }
    st = srmech_bigint_copy(&c->r0, out_num);   /* r0 := |p| */
    if (st != SRMECH_OK) { return st; }
    if (c->r0.sign < 0) {
        c->r0.sign = 1;
    }
    st = rr_is_coprime(c, out_den, modulus, &coprime);    /* gcd(q, mod) == 1 */
    if (st != SRMECH_OK) { return st; }
    if (coprime) {
        st = rr_is_coprime(c, &c->r0, out_den, &coprime); /* gcd(|p|, q) == 1 */
        if (st != SRMECH_OK) { return st; }
    }
    *out_found = coprime ? 1 : 0;
    return SRMECH_OK;
}

srmech_status_t srmech_rational_reconstruct(const srmech_bigint_t *residue,
                                            const srmech_bigint_t *modulus,
                                            const srmech_bigint_t *num_bound,
                                            const srmech_bigint_t *den_bound,
                                            srmech_bigint_t *out_num,
                                            srmech_bigint_t *out_den,
                                            int32_t *out_found,
                                            void *ws, size_t ws_len)
{
    rr_ctx_t c;
    srmech_status_t st;
    uint32_t cap;
    assert(residue != NULL && modulus != NULL);
    assert(out_num != NULL && out_den != NULL && out_found != NULL);
    if (residue == NULL || modulus == NULL || num_bound == NULL
        || den_bound == NULL || out_num == NULL || out_den == NULL
        || out_found == NULL || ws == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    *out_found = 0;
    if (modulus->sign <= 0 || (modulus->n == 1u && modulus->limbs[0] < 2u)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    cap = (uint32_t)((modulus->n * 2u) + 16u);
    st = rr_ctx_init(&c, cap, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    st = rr_run_euclid(&c, residue, modulus, num_bound);
    if (st != SRMECH_OK) { return st; }
    return rr_finalize(&c, modulus, den_bound, out_num, out_den, out_found);
}
