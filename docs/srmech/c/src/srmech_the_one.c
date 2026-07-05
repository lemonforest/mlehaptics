/*
 * srmech_the_one.c — the S(sigma,theta) ADJOINT generator in C (rc138; #743).
 *
 * The FLAGSHIP C:Python-parity backfill. srmech.amsc.cascade.one.the_one builds
 * the single generator S(sigma,theta) of the 1+3+7+3 = 14 substrate: the
 * octonion-native epicycle e^{I_n theta} = cos(theta) + I_n sin(theta) tiled
 * across the Hurwitz ladder (C / H / O) by the fixed Fano-plane orientations.
 * Its exact-rational ADJOINT (One.to_flat_rational — the w-INVARIANT 2pi-periodic
 * base; the winding folds away there, so this peer is w-BLIND, same as Python)
 * was pure-Python with NO C peer, parked in the non-debt bignum_reference bucket.
 *
 * This op closes that gap. It COMPOSES the existing exact-rational bignum series
 * peers srmech_cos_series_truncate_big / srmech_sin_series_truncate_big (the same
 * Class-N Taylor partials the Python builds cos/sin from) with a block-tiling /
 * Fano-orientation kernel, producing the SAME 14 exact adjoint rationals
 * (num, den) One.to_flat_rational returns — BYTE-IDENTICAL to Python at ANY
 * magnitude (over caller-arena srmech_bigint, NO float, NO libm, NO malloc).
 *
 * The 14 flat rationals (order: [R.1, Im] per block, C then H then O):
 *   idx  value            block  note
 *    0   1/1              C      R.1 anchor (grammar B)
 *    1   sigma/1          C      Im C: theta-inert, pure sigma (n=1 degenerates)
 *    2   1/1              H      R.1 anchor (grammar H)
 *    3   sigma*cos        H      Fano plane (1,2,+1): e1 -> cos e1
 *    4   sigma*sin        H                             + sin e2
 *    5   0/1              H
 *    6   1/1              O      R.1 anchor (grammar N)
 *    7   sigma*cos        O      Fano plane (1,6,-1): e1 -> cos e1  (Im e1)
 *    8   0/1              O      Im e2
 *    9   0/1              O      Im e3
 *   10   0/1              O      Im e4
 *   11   0/1              O      Im e5
 *   12  -sigma*sin        O                             - sin e6  (orientation -1)
 *   13   0/1              O      Im e7
 * sigma in {+1,-1} is the chirality — the Class-K pin-slot sign-flip (never
 * abs(); a sign is applied by negating the sign-magnitude numerator) re-applied
 * as Class C. The Fano-line orientation of O's (1,6,-1) is why idx 11 carries
 * -sigma*sin (Baez 2002 §2; the fixed Cayley-Dickson-from-H convention).
 *
 * Carrier-internal, like srmech_bigexp.c / srmech_pi.c: NOT a Rosetta ledger op
 * of its own — it BACKS the existing the_one / one_matrix / to_scalar Python ops
 * (which move bignum_reference -> c_dispatched now that this peer exists).
 * Additive symbol -> SRMECH_ABI_VERSION stays 3.
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto/recursion): OK — flat helpers, iterative tile loop
 *   - Rule 2 (bounded loops)    : OK — the 14-slot tile (constant DIM)
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

/* The substrate dimension: 2 + 4 + 8 = 14 (One.DIM). */
#define THE_ONE_DIM 14u

/* The largest Taylor-term count the sin/cos series accept (One.DEFAULT_TERMS is
 * 24; rational._TRIG_SERIES_MAX_TERMS is 50). Matches the Python ValueError
 * domain so C and Python accept the same num_terms (Rule 2 loop bound). */
#define THE_ONE_MAX_TERMS 50u

/* A per-slot descriptor of the 14-tile. kind selects the source, sign the
 * Fano-plane orientation applied on top of sigma (Class-K/C). */
typedef struct the_one_slot {
    int32_t kind;   /* 0 = 1/1, 1 = 0/1, 2 = sigma/1, 3 = cos, 4 = sin */
    int32_t sign;   /* plane orientation multiplier for kind 3/4 (+1 or -1) */
} the_one_slot_t;

/* The fixed adjoint tile — the block-tiling / Fano-orientation kernel as data.
 * H's plane (1,2,+1) puts sigma*cos at idx 3, sigma*sin at idx 4; O's plane
 * (1,6,-1) puts sigma*cos at idx 7 and -sigma*sin at idx 11 (orientation -1). */
static const the_one_slot_t THE_ONE_TILE[THE_ONE_DIM] = {
    {0, +1},   /*  0: 1/1        (C  R.1) */
    {2, +1},   /*  1: sigma/1    (C  Im: theta-inert) */
    {0, +1},   /*  2: 1/1        (H  R.1) */
    {3, +1},   /*  3: sigma*cos  (H  e1) */
    {4, +1},   /*  4: sigma*sin  (H  e2) */
    {1, +1},   /*  5: 0/1        (H) */
    {0, +1},   /*  6: 1/1        (O  R.1) */
    {3, +1},   /*  7: sigma*cos  (O  Im e1) */
    {1, +1},   /*  8: 0/1        (O  Im e2) */
    {1, +1},   /*  9: 0/1        (O  Im e3) */
    {1, +1},   /* 10: 0/1        (O  Im e4) */
    {1, +1},   /* 11: 0/1        (O  Im e5) */
    {4, -1},   /* 12: -sigma*sin (O  Im e6, orientation -1) */
    {1, +1},   /* 13: 0/1        (O  Im e7) */
};

/* ---- caller-arena carve (mirrors bigexp_take / bigexp_bind) --------- */

static uint32_t *the_one_take(uint32_t *base, size_t words, size_t *cur,
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

static srmech_status_t the_one_bind(srmech_bigint_t *b, uint32_t *base,
                                    size_t words, size_t *cur, uint32_t cap)
{
    uint32_t *limbs = the_one_take(base, words, cur, cap);
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

/* ---- result-carrier sizing (mirrors bigexp_cap_for) ---------------- */

/* Limbs to hold E! (E <= 2*50+1 = 101 here): ~14 bits per factor is a safe
 * over-estimate of log2(E!) for the small E the trig series reach. */
static size_t the_one_factorial_limbs(uint32_t e)
{
    size_t bits = (size_t)e * 14u + 64u;
    size_t limbs = bits / 32u + 2u;
    assert(limbs >= 2u);
    assert(limbs > (size_t)e / 4u);
    return limbs;
}

/* Per-carrier limb cap for the cos/sin result — the SAME envelope bigexp_cap_for
 * uses internally, so the series' final reduced (num, den) always fits. */
static size_t the_one_cap(size_t num_limbs, size_t den_limbs, uint32_t num_terms)
{
    uint32_t top = 2u * num_terms + 1u;
    size_t qe = srmech_bigint_pow_bound(den_limbs == 0u ? 1u : den_limbs, top);
    size_t pe = srmech_bigint_pow_bound(num_limbs == 0u ? 1u : num_limbs, top);
    size_t fe = the_one_factorial_limbs(top);
    size_t cap = (qe + fe + pe) * 2u + 16u;
    assert(cap >= qe);
    assert(cap >= 16u);
    return cap;
}

size_t srmech_the_one_ws_bound(size_t num_limbs, size_t den_limbs,
                               uint32_t num_terms)
{
    size_t cap = the_one_cap(num_limbs, den_limbs, num_terms);
    size_t carriers = cap * 4u;                 /* cos_num,cos_den,sin_num,sin_den */
    size_t series = srmech_bigexp_ws_bound(num_limbs, den_limbs, num_terms)
                    / sizeof(uint32_t);
    size_t words = carriers + series + 16u;     /* + alignment slack */
    assert(words >= carriers);
    assert(words >= series);
    return words * sizeof(uint32_t);
}

/* ---- one tile slot -> its exact rational (num, den) ---------------- */

static srmech_status_t the_one_emit(srmech_bigint_t *on, srmech_bigint_t *od,
                                    int32_t kind, int32_t slot_sign, int32_t sigma,
                                    const srmech_bigint_t *cn,
                                    const srmech_bigint_t *cd,
                                    const srmech_bigint_t *sn,
                                    const srmech_bigint_t *sd)
{
    srmech_status_t st;
    int32_t total;
    assert(on != NULL && od != NULL);
    assert(kind >= 0 && kind <= 4);
    if (kind == 0 || kind == 1) {               /* 1/1 or 0/1 */
        st = srmech_bigint_set_i64(on, (kind == 0) ? 1 : 0);
        if (st != SRMECH_OK) { return st; }
        return srmech_bigint_set_i64(od, 1);
    }
    if (kind == 2) {                            /* sigma/1 (n=1 pure chirality) */
        st = srmech_bigint_set_i64(on, (int64_t)sigma);
        if (st != SRMECH_OK) { return st; }
        return srmech_bigint_set_i64(od, 1);
    }
    st = srmech_bigint_copy(on, (kind == 3) ? cn : sn);   /* cos or sin numerator */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(od, (kind == 3) ? cd : sd);   /* its positive denom */
    if (st != SRMECH_OK) { return st; }
    total = sigma * slot_sign;                  /* Class-K/C applied chirality */
    assert(total == 1 || total == -1);
    if (total < 0 && on->sign != 0) {
        on->sign = -on->sign;                   /* negate numerator; no abs() */
    }
    return SRMECH_OK;
}

/* ---- the adjoint generator ---------------------------------------- */

srmech_status_t srmech_the_one(int32_t sigma,
                               const srmech_bigint_t *theta_num,
                               const srmech_bigint_t *theta_den,
                               uint32_t num_terms,
                               srmech_bigint_t *out_num,
                               srmech_bigint_t *out_den,
                               void *ws, size_t ws_len)
{
    srmech_bigint_t cos_n, cos_d, sin_n, sin_d;
    uint32_t *base = (uint32_t *)ws;
    size_t words = ws_len / sizeof(uint32_t), cur = 0u;
    size_t cap, series_words, i;
    srmech_status_t st = SRMECH_OK;
    assert(out_num != NULL && out_den != NULL);
    assert(theta_num != NULL && theta_den != NULL);
    if (out_num == NULL || out_den == NULL
        || theta_num == NULL || theta_den == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (sigma != 1 && sigma != -1) { return SRMECH_ERR_BAD_INPUT; }
    if (theta_den->sign <= 0) { return SRMECH_ERR_BAD_INPUT; }
    if (num_terms > THE_ONE_MAX_TERMS) { return SRMECH_ERR_BAD_INPUT; }
    cap = the_one_cap(theta_num->n, theta_den->n, num_terms);
    st |= the_one_bind(&cos_n, base, words, &cur, (uint32_t)cap);
    st |= the_one_bind(&cos_d, base, words, &cur, (uint32_t)cap);
    st |= the_one_bind(&sin_n, base, words, &cur, (uint32_t)cap);
    st |= the_one_bind(&sin_d, base, words, &cur, (uint32_t)cap);
    if (st != SRMECH_OK) { return SRMECH_ERR_OVERFLOW; }
    series_words = words - cur;                 /* the series scratch tail */
    st = srmech_cos_series_truncate_big(theta_num, theta_den, num_terms,
                                        &cos_n, &cos_d,
                                        base + cur, series_words * sizeof(uint32_t));
    if (st != SRMECH_OK) { return st; }
    st = srmech_sin_series_truncate_big(theta_num, theta_den, num_terms,
                                        &sin_n, &sin_d,
                                        base + cur, series_words * sizeof(uint32_t));
    if (st != SRMECH_OK) { return st; }
    for (i = 0u; i < THE_ONE_DIM; i++) {        /* the 14-slot Fano tile */
        st = the_one_emit(&out_num[i], &out_den[i],
                          THE_ONE_TILE[i].kind, THE_ONE_TILE[i].sign, sigma,
                          &cos_n, &cos_d, &sin_n, &sin_d);
        if (st != SRMECH_OK) { return st; }
    }
    assert(cur <= words);
    return SRMECH_OK;
}
