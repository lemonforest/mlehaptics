/*
 * srmech_one.c — the One-family leaf ops in C (rc195; the make_class -> C arc).
 *
 * The first leaf-batch of the make_class -> C arc (#887 / the DSL [class] object
 * model). The one.toml [class] One binds accessor methods to module-level flat
 * ops in srmech.amsc.cascade.one; two of those are genuine COMPUTE leaves that
 * assemble the S(sigma,theta) generator into a matrix / scalar, and this TU is
 * their C peer so a bare-C host (no Python) runs One.matrix() / One.scalar()
 * without shelling out per method.
 *
 * BOTH ops COMPOSE srmech_the_one (rc138): they regenerate the 14 exact adjoint
 * rationals internally (the octonion-epicycle cos/sin tiled by the fixed Fano
 * planes) then assemble exactly like the Python One.to_matrix / One.to_scalar:
 *
 *   - srmech_one_scalar : the matrix/vector -> scalar projection family.
 *       mode 0 (trace)     Tr G = 3 + 3*sigma + 8*sigma*cos(theta), EXACT (num,den)
 *       mode 1 (sqnorm)    Sum (num/den)^2 over the 14 state rationals, EXACT
 *       mode 2 (component) the index-th of the 14 exact rationals, EXACT
 *     EXACT-RATIONAL over caller-arena srmech_bigint -> BYTE-IDENTICAL to the pure
 *     Python (the as_float terminal cast stays in the caller, no float here).
 *
 *   - srmech_one_matrix : the 14x14 block-diagonal float operator G(sigma,theta)
 *     = (+)_n (1 (+) sigma R_n(theta)) as 196 row-major doubles. cos/sin are the
 *     exact flat rationals CORRECTLY-ROUNDED to double (round-half-to-even, the
 *     SAME nearest binary64 CPython int/int returns), then the +-1 / +-cos / +-sin
 *     tile is placed (no float accumulation -> FMA-safe). BYTE-IDENTICAL to the
 *     pure Python One.to_matrix (rc331; #948): each cell is the bit-exact double
 *     the pure cn/cd division yields, so srmech_mcp_serialise_result emits the
 *     14x14 float array byte-for-byte with json.dumps(serialise_native(...)).
 *
 * No abs(): a sign is applied by negating the sign-magnitude numerator / by a
 * Class-K branch, never an ALU abs() (the sign is the Class-K pin, its
 * re-application the Class-C orientation).
 *
 * Carrier-internal, like srmech_the_one / srmech_bigexp: the two matrix/scalar
 * ops BACK the existing one_matrix / to_scalar Python ops (already c_dispatched
 * on srmech_the_one; this peer makes the WHOLE assembly native too). Additive
 * symbols -> SRMECH_ABI_VERSION stays 4.
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto/recursion): OK — flat helpers, bounded tile loops
 *   - Rule 2 (bounded loops)    : OK — the 14-slot / 196-cell / 4-plane tiles
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
#include <string.h>

/* The substrate dimension: 2 + 4 + 8 = 14 (One.DIM). */
#define ONE_DIM 14u

/* The 14x14 flat matrix cell count (row-major). */
#define ONE_MATRIX_N (ONE_DIM * ONE_DIM)

/* The trig-series term cap (matches srmech_the_one / rational._TRIG_SERIES_MAX). */
#define ONE_MAX_TERMS 50u

/* Correctly-rounded bigrat->double convergence bound: s = 54 - (bitlen(|num|) -
 * bitlen(den)) lands the quotient at 54 or 55 bits, so bitlen(quot) reaches the
 * target 55 in <= 1 adjustment (bitlen(floor(|num|*2^s/den)) steps by exactly 1
 * per unit s). A cap of 4 gives ample margin; JPL Rule-2 bounded loop. */
#define ONE_ROUND_ITERS 4

/* to_scalar modes (mirror the Python mode strings). */
#define ONE_SCALAR_TRACE     0
#define ONE_SCALAR_SQNORM    1
#define ONE_SCALAR_COMPONENT 2

/* ---- caller-arena carve (mirrors the_one_take / the_one_bind) --------- */

static uint32_t *one_take(uint32_t *base, size_t words, size_t *cur, size_t count)
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

static srmech_status_t one_bind(srmech_bigint_t *b, uint32_t *base, size_t words,
                                size_t *cur, uint32_t cap)
{
    uint32_t *limbs = one_take(base, words, cur, cap);
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

/* ---- result-carrier sizing --------------------------------------------- */

/* Per-carrier limb cap for the 14 flat rationals (the reduced cos/sin envelope).
 * Mirrors the PROVEN the_one_c out_cap = 32*(N + 9*(num_l + den_l)) + 128 (9
 * decimal digits ~ 1 limb) — generous; over-sizing is free, under-sizing ->
 * OVERFLOW. */
static size_t one_flat_cap(size_t num_limbs, size_t den_limbs, uint32_t num_terms)
{
    size_t nl = (num_limbs < 1u) ? 1u : num_limbs;
    size_t dl = (den_limbs < 1u) ? 1u : den_limbs;
    size_t cap = 32u * ((size_t)num_terms + 9u * (nl + dl)) + 128u;
    assert(cap >= 128u);
    assert(cap > (size_t)num_terms);
    return cap;
}

/* ---- regenerate the 14 flat rationals via srmech_the_one --------------- */

/* Carve 28 flat carriers (14 num + 14 den, cap `flat_cap`) off `base`, then run
 * srmech_the_one INTO them over the arena TAIL (base + *cur .. words). *cur is
 * left pointing PAST the carriers so the caller reuses the tail as scratch (the
 * the_one ws is only live DURING the call — sequential, so the reuse is safe). */
static srmech_status_t one_regen_flat(int32_t sigma, const srmech_bigint_t *tn,
                                      const srmech_bigint_t *td, uint32_t num_terms,
                                      uint32_t flat_cap, srmech_bigint_t *fnum,
                                      srmech_bigint_t *fden, uint32_t *base,
                                      size_t words, size_t *cur)
{
    srmech_status_t st = SRMECH_OK;
    size_t i, tail_words;
    assert(fnum != NULL && fden != NULL);
    assert(base != NULL && cur != NULL);
    for (i = 0u; i < ONE_DIM; i++) {
        st |= one_bind(&fnum[i], base, words, cur, flat_cap);
        st |= one_bind(&fden[i], base, words, cur, flat_cap);
    }
    if (st != SRMECH_OK) {
        return SRMECH_ERR_OVERFLOW;
    }
    tail_words = words - *cur;                  /* the shared scratch tail */
    return srmech_the_one(sigma, tn, td, num_terms, fnum, fden,
                          base + *cur, tail_words * sizeof(uint32_t));
}

/* ---- exact-Q reduce (mirrors poly_q_reduce) ---------------------------- */

/* Reduce num/den IN PLACE to lowest terms, positive denominator, over the four
 * private carriers (g, rem, rs0, rs1) + the scratch tail. den must be nonzero. */
static srmech_status_t one_q_reduce(srmech_bigint_t *num, srmech_bigint_t *den,
                                    srmech_bigint_t *g, srmech_bigint_t *rem,
                                    srmech_bigint_t *rs0, srmech_bigint_t *rs1,
                                    void *ws, size_t ws_len)
{
    srmech_status_t st;
    assert(num != NULL && den != NULL);
    assert(den->sign != 0);
    if (den->sign < 0) {                        /* force positive denominator */
        num->sign = (num->sign == 0) ? 0 : -num->sign;
        den->sign = -den->sign;
    }
    if (srmech_bigint_is_zero(num)) {
        return srmech_bigint_set_i64(den, 1);
    }
    st = srmech_bigint_gcd(g, num, den, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_divmod(rs0, rem, num, g, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_divmod(rs1, rem, den, g, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(num, rs0);
    if (st != SRMECH_OK) { return st; }
    return srmech_bigint_copy(den, rs1);
}

/* ---- to_scalar mode kernels -------------------------------------------- */

/* Tr G(sigma,theta) = (3 + 3*sigma)*cd + 8*sigma*cn over cd, reduced. cn/cd is
 * the RAW cos rational: flat[3] = sigma*cos (reduced), so cn = sigma * flat[3]
 * un-applies the chirality (multiply the numerator's sign by sigma — a Class-K/C
 * sign, never abs()). s carriers: cn, cd, t0, t1 + reduce(g, rem, rs0, rs1). */
static srmech_status_t one_scalar_trace(int32_t sigma, const srmech_bigint_t *f3n,
                                        const srmech_bigint_t *f3d,
                                        srmech_bigint_t *out_num,
                                        srmech_bigint_t *out_den,
                                        srmech_bigint_t *c /* [8] scratch */,
                                        void *ws, size_t ws_len)
{
    srmech_status_t st;
    assert(f3n != NULL && f3d != NULL && out_num != NULL && out_den != NULL);
    assert(sigma == 1 || sigma == -1);
    st = srmech_bigint_copy(&c[0], f3n);               /* cn = flat[3].num */
    if (st != SRMECH_OK) { return st; }
    if (sigma < 0 && c[0].sign != 0) {                  /* un-apply sigma (no abs) */
        c[0].sign = -c[0].sign;
    }
    st = srmech_bigint_set_i64(&c[1], (int64_t)(3 + 3 * sigma));   /* 6 or 0 */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_mul(&c[2], &c[1], f3d);          /* t0 = (3+3s)*cd */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&c[1], (int64_t)(8 * sigma));       /* +-8 */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_mul(&c[3], &c[1], &c[0]);        /* t1 = 8s*cn */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_add(out_num, &c[2], &c[3]);      /* (3+3s)cd + 8s cn */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(out_den, f3d);              /* den = cd */
    if (st != SRMECH_OK) { return st; }
    return one_q_reduce(out_num, out_den, &c[4], &c[5], &c[6], &c[7], ws, ws_len);
}

/* acc += (n/d)^2 over the 14 flat rationals -> out. Pure integer arithmetic
 * (squaring is sign-free). c carriers: acc_n, acc_d, sq_n, sq_d, t0, t1, na, nd
 * (8) + reduce(g, rem, rs0, rs1) (4). */
static srmech_status_t one_scalar_sqnorm(const srmech_bigint_t *fnum,
                                         const srmech_bigint_t *fden,
                                         srmech_bigint_t *out_num,
                                         srmech_bigint_t *out_den,
                                         srmech_bigint_t *c /* [12] scratch */,
                                         void *ws, size_t ws_len)
{
    srmech_status_t st;
    size_t i;
    assert(fnum != NULL && fden != NULL && out_num != NULL && out_den != NULL);
    assert(c != NULL);
    st = srmech_bigint_set_i64(&c[0], 0);              /* acc_n = 0 */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&c[1], 1);              /* acc_d = 1 */
    if (st != SRMECH_OK) { return st; }
    for (i = 0u; i < ONE_DIM; i++) {
        st = srmech_bigint_mul(&c[2], &fnum[i], &fnum[i]);   /* sq_n = n*n */
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_mul(&c[3], &fden[i], &fden[i]);   /* sq_d = d*d */
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_mul(&c[4], &c[0], &c[3]);         /* t0 = acc_n*sq_d */
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_mul(&c[5], &c[2], &c[1]);         /* t1 = sq_n*acc_d */
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_add(&c[6], &c[4], &c[5]);         /* na = t0 + t1 */
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_mul(&c[7], &c[1], &c[3]);         /* nd = acc_d*sq_d */
        if (st != SRMECH_OK) { return st; }
        st = one_q_reduce(&c[6], &c[7], &c[8], &c[9], &c[10], &c[11], ws, ws_len);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_copy(&c[0], &c[6]);               /* acc_n = na */
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_copy(&c[1], &c[7]);               /* acc_d = nd */
        if (st != SRMECH_OK) { return st; }
    }
    st = srmech_bigint_copy(out_num, &c[0]);
    if (st != SRMECH_OK) { return st; }
    return srmech_bigint_copy(out_den, &c[1]);
}

/* ---- srmech_one_scalar ------------------------------------------------- */

size_t srmech_one_scalar_ws_bound(size_t num_limbs, size_t den_limbs,
                                  uint32_t num_terms)
{
    size_t flat_cap = one_flat_cap(num_limbs, den_limbs, num_terms);
    size_t scal_cap = 8u * flat_cap;                 /* accumulation headroom */
    size_t carriers = 28u * flat_cap + 12u * scal_cap;
    size_t the_one_ws = srmech_the_one_ws_bound(num_limbs, den_limbs, num_terms)
                        / sizeof(uint32_t);
    size_t tail = (the_one_ws > 16u * flat_cap) ? the_one_ws : 16u * flat_cap;
    size_t words = carriers + tail + 32u;
    assert(words >= carriers);
    assert(words >= tail);
    return words * sizeof(uint32_t);
}

srmech_status_t srmech_one_scalar(int32_t sigma, const srmech_bigint_t *theta_num,
                                  const srmech_bigint_t *theta_den,
                                  uint32_t num_terms, int32_t mode, int32_t index,
                                  srmech_bigint_t *out_num, srmech_bigint_t *out_den,
                                  void *ws, size_t ws_len)
{
    srmech_bigint_t fnum[ONE_DIM], fden[ONE_DIM], c[12];
    uint32_t *base = (uint32_t *)ws;
    size_t words = ws_len / sizeof(uint32_t), cur = 0u;
    size_t flat_cap, scal_cap, i, tail_words;
    srmech_status_t st = SRMECH_OK;
    /* rc187: the runtime NULL-check-and-return PRECEDES any assert on the ptr. */
    if (out_num == NULL || out_den == NULL
        || theta_num == NULL || theta_den == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(out_num != NULL && out_den != NULL);
    assert(theta_num != NULL && theta_den != NULL);
    if (sigma != 1 && sigma != -1) { return SRMECH_ERR_BAD_INPUT; }
    if (theta_den->sign <= 0) { return SRMECH_ERR_BAD_INPUT; }
    if (num_terms > ONE_MAX_TERMS) { return SRMECH_ERR_BAD_INPUT; }
    if (mode < ONE_SCALAR_TRACE || mode > ONE_SCALAR_COMPONENT) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (mode == ONE_SCALAR_COMPONENT
        && (index < 0 || index >= (int32_t)ONE_DIM)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    flat_cap = one_flat_cap(theta_num->n, theta_den->n, num_terms);
    scal_cap = 8u * flat_cap;
    st = one_regen_flat(sigma, theta_num, theta_den, num_terms,
                        (uint32_t)flat_cap, fnum, fden, base, words, &cur);
    if (st != SRMECH_OK) { return st; }
    for (i = 0u; i < 12u; i++) {                     /* the scalar scratch carriers */
        st |= one_bind(&c[i], base, words, &cur, (uint32_t)scal_cap);
    }
    if (st != SRMECH_OK) { return SRMECH_ERR_OVERFLOW; }
    tail_words = words - cur;                        /* reduce/gcd/divmod scratch */
    if (mode == ONE_SCALAR_COMPONENT) {
        st = srmech_bigint_copy(out_num, &fnum[index]);
        if (st != SRMECH_OK) { return st; }
        return srmech_bigint_copy(out_den, &fden[index]);
    }
    if (mode == ONE_SCALAR_TRACE) {
        return one_scalar_trace(sigma, &fnum[3], &fden[3], out_num, out_den,
                                c, base + cur, tail_words * sizeof(uint32_t));
    }
    return one_scalar_sqnorm(fnum, fden, out_num, out_den, c,
                             base + cur, tail_words * sizeof(uint32_t));
}

/* ---- bignum rational -> double (math.h-free, CORRECTLY-ROUNDED) -------- */

/* Bit length of a non-negative bignum: (n-1)*32 + bits in the top limb. Zero ->
 * 0. Bounded 32-step top-limb scan (JPL Rule 2). No leading-zero limbs, so the
 * top limb is nonzero for n > 0. */
static uint32_t one_bigint_bitlen(const srmech_bigint_t *a)
{
    uint32_t top, bl;
    assert(a != NULL);
    assert(a->n == 0u || a->limbs != NULL);
    if (a->n == 0u) { return 0u; }
    top = a->limbs[a->n - 1u];
    bl = (a->n - 1u) * 32u;
    while (top > 0u) { bl++; top >>= 1u; }
    return bl;
}

/* quot,rem = divmod(|num|*2^s, den) for the current shift s (s < 0 shifts den by
 * -s and divides |num| instead — the same exact ratio). `shifted` is the scratch
 * carrier for the shifted operand. Python-floor divmod (num,den >= 0 -> exact). */
static srmech_status_t one_divmod_shift(const srmech_bigint_t *mag,
                                        const srmech_bigint_t *den, int32_t s,
                                        srmech_bigint_t *shifted,
                                        srmech_bigint_t *quot, srmech_bigint_t *rem,
                                        void *ws, size_t ws_len)
{
    srmech_status_t st;
    assert(mag != NULL && den != NULL);
    assert(shifted != NULL && quot != NULL && rem != NULL);
    if (s >= 0) {
        st = srmech_bigint_shl_bits(shifted, mag, (uint32_t)s);
        if (st != SRMECH_OK) { return st; }
        return srmech_bigint_divmod(quot, rem, shifted, den, ws, ws_len);
    }
    st = srmech_bigint_shl_bits(shifted, den, (uint32_t)(-s));
    if (st != SRMECH_OK) { return st; }
    return srmech_bigint_divmod(quot, rem, mag, shifted, ws, ws_len);
}

/* Assemble the IEEE-754 binary64 value keep*2^exp2 with sign `sign`, by direct
 * bit layout (deterministic across Linux/macOS/Windows; no libm/ldexp). keep is
 * normalised in [2^52, 2^53] (53-bit mantissa incl. the implicit bit; == 2^53 is
 * the round-up carry -> renormalise). biased exponent = (exp2 + 52) + 1023. */
static double one_ieee_scale(uint64_t keep, int32_t exp2, int32_t sign)
{
    uint64_t frac, biased, bits; double out;
    assert(keep >= (UINT64_C(1) << 52) && keep <= (UINT64_C(1) << 53));
    assert(sign == 1 || sign == -1);
    if (keep == (UINT64_C(1) << 53)) { keep >>= 1; exp2 += 1; }  /* carry renorm */
    biased = (uint64_t)((int64_t)exp2 + 1075);
    frac = keep - (UINT64_C(1) << 52);               /* low 52 bits = the mantissa */
    assert(biased >= 1u && biased <= 2046u);         /* normal-range (the One domain) */
    bits = ((uint64_t)(sign < 0 ? 1 : 0) << 63) | (biased << 52) | frac;
    memcpy(&out, &bits, sizeof out);
    return out;
}

/* out = num/den as the NEAREST binary64 (round-half-to-even), num signed, den > 0
 * — BYTE-IDENTICAL to CPython int(num)/int(den) at ANY magnitude (rc331; #948).
 * A dynamic shift s = 54 - (bitlen(|num|) - bitlen(den)) lands the exact quotient
 * at 55 bits (53 mantissa + 2 guard); the divmod remainder is the sticky bit;
 * round-half-even; the scale is an EXACT power of two via direct IEEE assembly.
 * Pure integer + srmech_bigint ops (libm-free). Class-K magnitude / Class-C sign
 * (no abs on the double). c carriers: mag (|num|), shifted, quot, rem. */
static srmech_status_t one_bigrat_to_double(const srmech_bigint_t *num,
                                            const srmech_bigint_t *den, double *out,
                                            srmech_bigint_t *mag,
                                            srmech_bigint_t *shifted,
                                            srmech_bigint_t *quot,
                                            srmech_bigint_t *rem,
                                            void *ws, size_t ws_len)
{
    srmech_status_t st; int32_t s, sign, iter; uint32_t bl = 0u;
    uint64_t q_u64, keep, low2; int sticky;
    assert(num != NULL && den != NULL && out != NULL);
    assert(den->sign > 0);
    if (num->sign == 0) { *out = 0.0; return SRMECH_OK; }
    sign = (num->sign < 0) ? -1 : 1;                 /* Class-K pin (no abs) */
    st = srmech_bigint_copy(mag, num);
    if (st != SRMECH_OK) { return st; }
    mag->sign = 1;                                   /* Class-K magnitude */
    s = 54 - ((int32_t)one_bigint_bitlen(mag) - (int32_t)one_bigint_bitlen(den));
    for (iter = 0; iter < ONE_ROUND_ITERS; iter++) { /* converge |quot| to 55 bits */
        st = one_divmod_shift(mag, den, s, shifted, quot, rem, ws, ws_len);
        if (st != SRMECH_OK) { return st; }
        bl = one_bigint_bitlen(quot);
        if (bl == 55u) { break; }
        s += (bl < 55u) ? 1 : -1;
    }
    if (bl != 55u) { return SRMECH_ERR_OVERFLOW; }   /* out-of-domain magnitude */
    assert(quot->n >= 1u && quot->n <= 2u);
    q_u64 = (uint64_t)quot->limbs[0];
    if (quot->n >= 2u) { q_u64 |= ((uint64_t)quot->limbs[1]) << 32; }
    sticky = srmech_bigint_is_zero(rem) ? 0 : 1;
    keep = q_u64 >> 2;                               /* top 53 bits */
    low2 = q_u64 & 3u;                               /* 2 dropped guard/round bits */
    if (low2 > 2u || (low2 == 2u && (sticky || (keep & 1u)))) { keep += 1u; }
    *out = one_ieee_scale(keep, -s + 2, sign);       /* Class-C orientation */
    return SRMECH_OK;
}

/* ---- 14x14 float assembly (mirrors One.to_matrix) ---------------------- */

/* Place the +-1 / s / s*cos / +-s*sin tile into `out` (row-major, DIM*DIM). No
 * float accumulation (each cell is one placement) -> FMA-safe. s = (double)sigma
 * (+-1, exact), so s*cos_t / s*sin_t are exact scalings of cos_t/sin_t. */
static void one_assemble_matrix(double *out, double s, double cos_t, double sin_t)
{
    static const int32_t off[3] = {0, 2, 6};         /* block offsets */
    static const int32_t dd[3] = {1, 3, 7};          /* Im dims */
    /* Fano planes {block, a, b, sgn}: H (1,2,+1); O (1,6,-1),(2,5,+1),(3,4,+1). */
    static const int32_t pl[4][4] = {
        {1, 1, 2, 1}, {2, 1, 6, -1}, {2, 2, 5, 1}, {2, 3, 4, 1}
    };
    int32_t bi, i, k, o, imo, ia, ib;
    double sgn;
    assert(out != NULL);
    for (i = 0; i < (int32_t)ONE_MATRIX_N; i++) { out[i] = 0.0; }
    for (bi = 0; bi < 3; bi++) {
        o = off[bi];
        imo = o + 1;
        out[o * (int32_t)ONE_DIM + o] = 1.0;         /* R.1 anchor — fixed */
        for (i = 0; i < dd[bi]; i++) {               /* sigma on Im */
            out[(imo + i) * (int32_t)ONE_DIM + (imo + i)] = s;
        }
    }
    for (k = 0; k < 4; k++) {                         /* turn each Fano plane by theta */
        o = off[pl[k][0]];
        imo = o + 1;
        ia = imo + (pl[k][1] - 1);
        ib = imo + (pl[k][2] - 1);
        sgn = (double)pl[k][3];
        out[ia * (int32_t)ONE_DIM + ia] = s * cos_t;
        out[ib * (int32_t)ONE_DIM + ib] = s * cos_t;
        out[ib * (int32_t)ONE_DIM + ia] = s * sgn * sin_t;
        out[ia * (int32_t)ONE_DIM + ib] = -s * sgn * sin_t;
    }
    assert(out[0] == 1.0);                            /* the C R.1 anchor */
}

/* ---- srmech_one_matrix ------------------------------------------------- */

size_t srmech_one_matrix_ws_bound(size_t num_limbs, size_t den_limbs,
                                  uint32_t num_terms)
{
    size_t flat_cap = one_flat_cap(num_limbs, den_limbs, num_terms);
    size_t mat_cap = flat_cap + 16u;                 /* bigrat scratch (<<96 = +3) */
    size_t carriers = 28u * flat_cap + 4u * mat_cap;
    size_t the_one_ws = srmech_the_one_ws_bound(num_limbs, den_limbs, num_terms)
                        / sizeof(uint32_t);
    size_t tail = (the_one_ws > 4u * flat_cap) ? the_one_ws : 4u * flat_cap;
    size_t words = carriers + tail + 32u;
    assert(words >= carriers);
    assert(words >= tail);
    return words * sizeof(uint32_t);
}

srmech_status_t srmech_one_matrix(int32_t sigma, const srmech_bigint_t *theta_num,
                                  const srmech_bigint_t *theta_den,
                                  uint32_t num_terms, double *out, size_t out_count,
                                  void *ws, size_t ws_len)
{
    srmech_bigint_t fnum[ONE_DIM], fden[ONE_DIM], c[4];
    uint32_t *base = (uint32_t *)ws;
    size_t words = ws_len / sizeof(uint32_t), cur = 0u;
    size_t flat_cap, mat_cap, i, tail_words;
    double cos_t = 0.0, sin_t = 0.0, s;
    srmech_status_t st = SRMECH_OK;
    /* rc187: the runtime NULL-check-and-return PRECEDES any assert on the ptr. */
    if (out == NULL || theta_num == NULL || theta_den == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(out != NULL && theta_den != NULL);
    assert(theta_num != NULL);
    if (sigma != 1 && sigma != -1) { return SRMECH_ERR_BAD_INPUT; }
    if (theta_den->sign <= 0) { return SRMECH_ERR_BAD_INPUT; }
    if (num_terms > ONE_MAX_TERMS) { return SRMECH_ERR_BAD_INPUT; }
    if (out_count < ONE_MATRIX_N) { return SRMECH_ERR_OVERFLOW; }
    flat_cap = one_flat_cap(theta_num->n, theta_den->n, num_terms);
    mat_cap = flat_cap + 16u;
    st = one_regen_flat(sigma, theta_num, theta_den, num_terms,
                        (uint32_t)flat_cap, fnum, fden, base, words, &cur);
    if (st != SRMECH_OK) { return st; }
    for (i = 0u; i < 4u; i++) {                      /* bigrat scratch carriers */
        st |= one_bind(&c[i], base, words, &cur, (uint32_t)mat_cap);
    }
    if (st != SRMECH_OK) { return SRMECH_ERR_OVERFLOW; }
    tail_words = words - cur;
    /* flat[3] = sigma*cos, flat[4] = sigma*sin (the stored ADJOINT of the H Fano
     * plane). Python's to_matrix rounds the RAW cos/sin: _chiral_scale un-applies
     * sigma at the RATIONAL level (twice = identity -> the raw num,den), THEN cn/cd
     * -> double. Mirror that EXACTLY — un-apply sigma here as a Class-C numerator
     * sign reversal (no abs), NOT as a float s*leaf: a float un-apply would mint
     * the WRONG signed zero (-0.0 vs +0.0) on sin(0). The assemble then applies s
     * ONCE, byte-identical to the pure s*cos_t / s*sgn*sin_t. */
    s = (double)sigma;
    if (sigma < 0) {                                 /* raw = sigma * adjoint (Class-C) */
        if (fnum[3].sign != 0) { fnum[3].sign = -fnum[3].sign; }
        if (fnum[4].sign != 0) { fnum[4].sign = -fnum[4].sign; }
    }
    st = one_bigrat_to_double(&fnum[3], &fden[3], &cos_t, &c[0], &c[1], &c[2],
                              &c[3], base + cur, tail_words * sizeof(uint32_t));
    if (st != SRMECH_OK) { return st; }
    st = one_bigrat_to_double(&fnum[4], &fden[4], &sin_t, &c[0], &c[1], &c[2],
                              &c[3], base + cur, tail_words * sizeof(uint32_t));
    if (st != SRMECH_OK) { return st; }
    one_assemble_matrix(out, s, cos_t, sin_t);       /* raw doubles; assemble applies s */
    return SRMECH_OK;
}
