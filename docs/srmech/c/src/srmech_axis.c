/*
 * srmech_axis.c -- the EXACT unit of a pure-imaginary axis (0.9.0rc477,
 * `#T1188`). Declared in the PRIVATE c/src/srmech_sqrt_internal.h: no srmech.h
 * declaration, no ctypes binding, no ABI surface.
 *
 * THE DEFECT THIS REPLACES. Every axis resolver in this library normalised the
 * same way -- take the root of the sum of squares, take its reciprocal, then
 * multiply each component. That is THREE roundings for a value the prose at
 * each site called one, and the second and third are not repaired by fixing
 * the first. Measured at rc476 with an exact integer oracle:
 * `1.0 / srmech_rational_sqrt(k)` misses the correctly rounded 1/sqrt(k) on
 * 101 of the 399 integers k in 2..400, while the one-rounding route misses 0;
 * and even a perfectly correctly rounded double sits 77 Q61 words below the
 * nearest word at k = 3 and 60 above it at k = 7, because 53 bits cannot
 * address a 61-bit grid at all.
 *
 * THE ROUTE. v[j] is a double, so it IS the exact dyadic rational m_j * 2^e_j.
 * Put every component over the common denominator 2^min(e) -- which CANCELS
 * out of v[j]/||v|| -- and the direction is a vector of INTEGERS w with
 * S = SUM w^2 an integer. Then
 *
 *     out[j] = sign(w_j) * CR( sqrt( w_j^2 / S ) )
 *
 * is one root of one exact rational, and the 53-bit rounding is the sqrt
 * core's own (srmech_sqrt_project_root) rather than a second copy of it.
 *
 * WHY A BIGNUM. w_j^2 reaches 2 * (53 + spread) bits and S one more, so the
 * radicand does not cross srmech_sqrt_core's uint64 num/den wire. The
 * normalised quotient, though, is always in [2^106, 2^109) by construction, so
 * it lands in the two-limb srmech_isqrt this library already exports, and only
 * the SQUARE, the SUM and the DIVISION need arbitrary precision. All of it is
 * carved from one stack arena -- JPL Rule 3, no malloc.
 *
 * THE DECLARED CEILING. The arena is sized for an exponent spread of
 * SRMECH_AXIS_MAX_SPREAD_BITS; a wider axis is REFUSED with
 * SRMECH_ERR_NOT_IMPL rather than answered approximately. The Python caller
 * then runs its complete pure path, which has no ceiling and computes the same
 * value -- the shipped inform-don't-limit shape. License: MIT.
 */

#include "srmech.h"
#include "srmech_sqrt_internal.h"

#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

/* The sqrt core's normalise window, restated here because this file reaches
 * the same post-condition by its own arithmetic. Identical to
 * SRMECH_SQRT_CORE_BITS in srmech_sqrt.c; a parity test pins the two
 * projections' agreement rather than the constant's. */
#define AX_CORE_BITS 108

/* Limb budgets. m_j < 2^53 (2 limbs) shifted by at most the spread, so a
 * direction limb count is 2 + SPREAD/32 + 1; the square doubles it; the shift
 * before the division adds (AX_CORE_BITS + bitlen(S))/32 + 1. Each is a
 * CONSTANT, so the arena below is a fixed stack object with no malloc and no
 * caller argument. */
#define AX_W_LIMBS   (2u + (SRMECH_AXIS_MAX_SPREAD_BITS / 32u) + 2u)
#define AX_SQ_LIMBS  (2u * AX_W_LIMBS + 2u)
#define AX_NUM_LIMBS (AX_SQ_LIMBS + ((AX_CORE_BITS + 64u * AX_W_LIMBS) / 32u) + 2u)
#define AX_WS_LIMBS  (4u * AX_NUM_LIMBS + 64u)

typedef struct ax_arena {
    uint32_t w[SRMECH_AXIS_MAX_DIM][AX_W_LIMBS];
    uint32_t sq[AX_SQ_LIMBS];
    uint32_t acc[AX_SQ_LIMBS];
    uint32_t sum[AX_SQ_LIMBS];
    uint32_t num[AX_NUM_LIMBS];
    uint32_t quo[AX_NUM_LIMBS];
    uint32_t rem[AX_SQ_LIMBS];
    uint32_t ws[AX_WS_LIMBS];
} ax_arena_t;

/* v = sign * m * 2^e EXACTLY, with m the 53-bit significand as an integer
 * (subnormals keep their own narrower m). Returns 0 for a non-finite v. */
static int ax_split(double v, int *sign, uint64_t *m, int32_t *e)
{
    uint64_t bits, frac;
    uint32_t biased;
    assert(sign != NULL && m != NULL && e != NULL);
    assert(sizeof(bits) == sizeof(v));
    memcpy(&bits, &v, sizeof(bits));
    biased = (uint32_t)((bits >> 52) & 0x7FFu);
    frac = bits & ((UINT64_C(1) << 52) - 1u);
    if (biased == 0x7FFu) { return 0; }                 /* Inf / NaN: refuse */
    *sign = ((bits >> 63) != 0u) ? -1 : 1;              /* Class K pin-slot  */
    if (biased == 0u) { *m = frac; *e = -1074; }        /* subnormal / zero  */
    else { *m = frac | (UINT64_C(1) << 52); *e = (int32_t)biased - 1075; }
    if (*m == 0u) { *sign = 0; }
    return 1;
}

/* Bind `b` to `limbs` with capacity `cap` and set it to the unsigned u64 `v`. */
static srmech_status_t ax_bind_u64(srmech_bigint_t *b, uint32_t *limbs,
                                   uint32_t cap, uint64_t v)
{
    assert(b != NULL);
    assert(limbs != NULL);
    b->limbs = limbs; b->cap = cap; b->n = 0u; b->sign = 0;
    if (v == 0u) { return SRMECH_OK; }
    /* A COMPILED-IN cap, not a caller-supplied buffer, so the status is
     * SRMECH_ERR_LIMIT and not OVERFLOW (rc404's division: status 4 means "grow
     * it and retry", and there is nothing here a caller can grow). Unreachable
     * as shipped -- AX_W_LIMBS is 12 -- and a refusal is cheaper than an
     * assumption. */
    if (cap < 2u) { return SRMECH_ERR_LIMIT; }
    b->limbs[0] = (uint32_t)(v & 0xFFFFFFFFu);
    b->limbs[1] = (uint32_t)(v >> 32);
    b->n = (b->limbs[1] != 0u) ? 2u : 1u;
    b->sign = 1;
    return SRMECH_OK;
}

/* Bit length of a non-negative bigint (0 for zero). */
static uint32_t ax_bitlen(const srmech_bigint_t *a)
{
    uint32_t top, n = 0u;
    assert(a != NULL);
    assert(a->n == 0u || a->limbs != NULL);
    if (a->n == 0u) { return 0u; }
    top = a->limbs[a->n - 1u];
    while (top != 0u) { top >>= 1; n++; }
    return (a->n - 1u) * 32u + n;
}

/* The low 128 bits of a non-negative bigint, as (hi, lo). The caller has
 * already bounded the value below 2^128, which this asserts. */
static void ax_to_u128(const srmech_bigint_t *a, uint64_t *hi, uint64_t *lo)
{
    uint64_t parts[4] = {0u, 0u, 0u, 0u};
    uint32_t i;
    assert(a != NULL);
    assert(a->n <= 4u);
    for (i = 0u; i < a->n && i < 4u; i++) { parts[i] = (uint64_t)a->limbs[i]; }
    *lo = parts[0] | (parts[1] << 32);
    *hi = parts[2] | (parts[3] << 32);
}

/* The exponent spread of the non-zero components, and their (sign, m, e).
 * Returns SRMECH_ERR_BAD_INPUT on a non-finite or all-zero axis, and
 * SRMECH_ERR_NOT_IMPL when the spread is past the declared ceiling. */
static srmech_status_t ax_read(const double *v, size_t n, int *sgn,
                               uint64_t *mant, int32_t *expo, int32_t *e_min)
{
    size_t j;
    int any = 0;
    int32_t lo = 0, hi = 0;
    assert(v != NULL && sgn != NULL);
    assert(mant != NULL && expo != NULL && e_min != NULL);
    for (j = 0u; j < n; j++) {
        if (!ax_split(v[j], &sgn[j], &mant[j], &expo[j])) {
            return SRMECH_ERR_BAD_INPUT;
        }
        if (sgn[j] == 0) { continue; }
        if (!any) { lo = expo[j]; hi = expo[j]; any = 1; }
        if (expo[j] < lo) { lo = expo[j]; }
        if (expo[j] > hi) { hi = expo[j]; }
    }
    if (!any) { return SRMECH_ERR_BAD_INPUT; }
    if ((int64_t)hi - (int64_t)lo > (int64_t)SRMECH_AXIS_MAX_SPREAD_BITS) {
        return SRMECH_ERR_NOT_IMPL;                     /* the declared ceiling */
    }
    *e_min = lo;
    return SRMECH_OK;
}

/* S = SUM w_j^2 into `sum`, with `sq` / `acc` as the two working squares. */
static srmech_status_t ax_sum_squares(ax_arena_t *a, srmech_bigint_t *w,
                                      size_t n, srmech_bigint_t *sum)
{
    srmech_bigint_t sq, acc;
    size_t j;
    srmech_status_t st;
    assert(a != NULL && w != NULL && sum != NULL);
    assert(n <= SRMECH_AXIS_MAX_DIM);
    sq.limbs = a->sq; sq.cap = AX_SQ_LIMBS; sq.n = 0u; sq.sign = 0;
    acc.limbs = a->acc; acc.cap = AX_SQ_LIMBS; acc.n = 0u; acc.sign = 0;
    st = srmech_bigint_set_i64(sum, 0);
    if (st != SRMECH_OK) { return st; }
    for (j = 0u; j < n; j++) {
        if (w[j].n == 0u) { continue; }
        st = srmech_bigint_mul_ws(&sq, &w[j], &w[j], a->ws,
                                  AX_WS_LIMBS * sizeof(uint32_t));
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_add(&acc, sum, &sq);          /* no aliasing of out */
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_copy(sum, &acc);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* out = CR( sqrt(N / S) ) for 0 < N <= S, by the sqrt core's own normalise /
 * sticky / project rule with a bignum radicand. */
static srmech_status_t ax_ratio_sqrt(ax_arena_t *a, const srmech_bigint_t *nsq,
                                     const srmech_bigint_t *sum, double *out)
{
    srmech_bigint_t num, quo, rem;
    uint64_t hi = 0u, lo = 0u, root = 0u, shi, slo, ab, bb, aa, x, y;
    int32_t s, p;
    int exact;
    srmech_status_t st;
    assert(a != NULL && nsq != NULL && sum != NULL && out != NULL);
    assert(sum->n != 0u);
    s = (int32_t)AX_CORE_BITS - ((int32_t)ax_bitlen(nsq) - (int32_t)ax_bitlen(sum));
    if ((s & 1) != 0) { s -= 1; }              /* (e0 - s) even, with e0 = 0 */
    if (s < 0) { return SRMECH_ERR_NOT_IMPL; }
    num.limbs = a->num; num.cap = AX_NUM_LIMBS; num.n = 0u; num.sign = 0;
    quo.limbs = a->quo; quo.cap = AX_NUM_LIMBS; quo.n = 0u; quo.sign = 0;
    rem.limbs = a->rem; rem.cap = AX_SQ_LIMBS; rem.n = 0u; rem.sign = 0;
    st = srmech_bigint_shl_bits(&num, nsq, (uint32_t)s);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_divmod(&quo, &rem, &num, sum, a->ws,
                              AX_WS_LIMBS * sizeof(uint32_t));
    if (st != SRMECH_OK) { return st; }
    if (quo.n > 4u) { return SRMECH_ERR_NOT_IMPL; }       /* must be < 2^109 */
    ax_to_u128(&quo, &hi, &lo);
    st = srmech_isqrt(hi, lo, &root);
    if (st != SRMECH_OK) { return st; }
    x = root >> 32; y = root & 0xFFFFFFFFu;               /* root^2 in 128 bits */
    ab = x * y; bb = y * y; aa = x * x;
    slo = bb + (ab << 33);
    shi = aa + (ab >> 31) + ((slo < bb) ? 1u : 0u);
    exact = (rem.n == 0u) && (shi == hi) && (slo == lo);
    p = (int32_t)(-s / 2);
    if (!exact) { root = 2u * root + 1u; p -= 1; }        /* the STICKY low bit */
    return srmech_sqrt_project_root(root, p, out);
}

srmech_status_t srmech_axis_unit(const double *v, size_t n, double *out)
{
    ax_arena_t a;
    srmech_bigint_t w[SRMECH_AXIS_MAX_DIM], sum, nsq;
    int sgn[SRMECH_AXIS_MAX_DIM];
    uint64_t mant[SRMECH_AXIS_MAX_DIM];
    int32_t expo[SRMECH_AXIS_MAX_DIM], e_min = 0;
    size_t j;
    double mag = 0.0;
    srmech_status_t st;
    if (v == NULL || out == NULL) { return SRMECH_ERR_NULL_ARG; }
    if (n == 0u || n > SRMECH_AXIS_MAX_DIM) { return SRMECH_ERR_BAD_INPUT; }
    assert(v != NULL && out != NULL);
    assert(n >= 1u && n <= SRMECH_AXIS_MAX_DIM);
    st = ax_read(v, n, sgn, mant, expo, &e_min);
    if (st != SRMECH_OK) { return st; }
    for (j = 0u; j < n; j++) {
        st = ax_bind_u64(&w[j], a.w[j], AX_W_LIMBS,
                         (sgn[j] == 0) ? 0u : mant[j]);
        if (st != SRMECH_OK) { return st; }
        if (sgn[j] == 0 || expo[j] == e_min) { continue; }
        st = srmech_bigint_shl_bits(&w[j], &w[j],
                                    (uint32_t)(expo[j] - e_min));
        if (st != SRMECH_OK) { return st; }
    }
    sum.limbs = a.sum; sum.cap = AX_SQ_LIMBS; sum.n = 0u; sum.sign = 0;
    st = ax_sum_squares(&a, w, n, &sum);
    if (st != SRMECH_OK) { return st; }
    nsq.limbs = a.sq; nsq.cap = AX_SQ_LIMBS; nsq.n = 0u; nsq.sign = 0;
    for (j = 0u; j < n; j++) {
        if (sgn[j] == 0) { out[j] = 0.0; continue; }
        st = srmech_bigint_mul_ws(&nsq, &w[j], &w[j], a.ws,
                                  AX_WS_LIMBS * sizeof(uint32_t));
        if (st != SRMECH_OK) { return st; }
        st = ax_ratio_sqrt(&a, &nsq, &sum, &mag);
        if (st != SRMECH_OK) { return st; }
        out[j] = (sgn[j] < 0) ? -mag : mag;          /* Class C re-orientation */
    }
    return SRMECH_OK;
}
