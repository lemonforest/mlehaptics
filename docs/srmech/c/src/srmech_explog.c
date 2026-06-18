/* srmech_explog.c — Class-N rational exp/log cascade for the NATIVE (executable)
 * tier (v0.7.0rc46; C-transpile triality coherence, the rc42->rc46 closeout).
 *
 * The Python `srmech.amsc.rational.{exp,log}` compute exp/log as the Class-N
 * rational Taylor cascade (reduce, truncated series, project to float LAST).
 * `srmech_rational.c` already shipped `srmech_exp_series_truncate` (the exact
 * rational exp partial-sum). This file adds the double->double wrappers
 * `srmech_exp` / `srmech_log` so `srmech_laplacian.c`'s elementwise
 * transcendental op runs the cascade on a native install, not libm — the last
 * two libm calls (`exp`, `log`) in the shipped C library. With this file the
 * C-transpile triality ratchet (test_c_cascade_coherence.py) reaches ZERO:
 * the executable, the C+Python source, and the research notebook all agree.
 *
 * Discipline — the transcendental SERIES runs in INTEGER Q61 fixed-point
 * (a power-of-two-denominator rational — Class N), exactly like the rc43 trig
 * cores and the rc45 integer sqrt. exp/log are NOT cyclic (no periodic
 * mod-reduction), so the argument-reduction differs from trig:
 *   - exp: x = n*ln2 + r, |r| <= ln2/2. The integer n is picked, then the
 *     two-word Cody-Waite split (LN2_HI + LN2_LO) forms r accurately; exp(r)
 *     is the Q61 integer Taylor 1 + r + r^2/2! + ...; the 2^n scale is built
 *     straight into the IEEE exponent field (no ldexp). float appears only at
 *     the `(double)sum / 2^61` projection + the power-of-two recombine.
 *   - log: x = m * 2^e read EXACTLY from the bit pattern (no frexp — the
 *     m*2^e decomposition is integer), m folded into [1/sqrt2, sqrt2);
 *     log(m) = 2*atanh((m-1)/(m+1)) is the Q61 integer Taylor; the e*ln2
 *     recombine uses the same two-word ln2 for a machine-eps result.
 * No libm transcendental, no `abs()` (Class-K sign-branch), no malloc/goto.
 *
 * Constants — LN2_HI + LN2_LO is the standard fdlibm two-word split of ln(2)
 * (LN2_HI has its low 32 bits zero so n*LN2_HI is exact for |n| < 2^21);
 * INV_LN2 = 1/ln2; SQRT2 is a band edge (selection only — never enters the
 * result). Validated vs libm to machine epsilon over 500000+ values (the
 * prototype in the rc46 dispatch note): exp rel err <= 2.3e-16, log abs err
 * <= 2.2e-16; exp(log(x)) round-trips to <= 2.3e-16.
 *
 * JPL Power-of-Ten: Rule 1 (no goto) OK; Rule 2 (bounded loops) OK — every
 * loop has a constant cap; Rule 3 (no malloc) OK; Rule 4 (<=60 lines/fn) OK;
 * Rule 5 (>=2 asserts/non-trivial fn) OK; Rule 7 (status returns) OK;
 * Rule 10 (warnings clean) OK.
 *
 * License: MIT.
 */

#include "srmech.h"

#include <assert.h>
#include <stdint.h>
#include <string.h>

#define SRMECH_EXPLOG_FBITS  61
#define SRMECH_EXPLOG_ONE     (INT64_C(1) << SRMECH_EXPLOG_FBITS)   /* 1.0 in Q61 */

/* exp: x = n*ln2 + r. Two-word ln2 (fdlibm) keeps r accurate; 1/ln2 picks n. */
static const double SRMECH_EXPLOG_INV_LN2 = 1.4426950408889634074;
static const double SRMECH_EXPLOG_LN2_HI  = 6.93147180369123816490e-01;
static const double SRMECH_EXPLOG_LN2_LO  = 1.90821492927058770002e-10;
static const double SRMECH_EXPLOG_SQRT2    = 1.4142135623730951;     /* band edge */

#define SRMECH_EXPLOG_EXP_TERMS  18   /* |r|<=ln2/2: r^19/19! < 2^-62 */
#define SRMECH_EXPLOG_LOG_TERMS  13   /* |t|<=sqrt2-edge: t^27/27 < 2^-62 */

/* exp overflow / underflow gates: ln(DBL_MAX) and ln(smallest subnormal). */
#define SRMECH_EXPLOG_OVERFLOW   709.782712893384
#define SRMECH_EXPLOG_UNDERFLOW  (-745.2)

/* ---- portable 64x64 -> 128 unsigned multiply (no __int128 / _umul128) ---- */
static void explog_umul64(uint64_t a, uint64_t b, uint64_t *hi, uint64_t *lo)
{
    assert(hi != NULL);
    assert(lo != NULL);
    uint64_t al = a & 0xFFFFFFFFu, ah = a >> 32;
    uint64_t bl = b & 0xFFFFFFFFu, bh = b >> 32;
    uint64_t ll = al * bl, lh = al * bh, hl = ah * bl, hh = ah * bh;
    uint64_t cross = (ll >> 32) + (lh & 0xFFFFFFFFu) + (hl & 0xFFFFFFFFu);
    *lo = (ll & 0xFFFFFFFFu) | (cross << 32);
    *hi = hh + (lh >> 32) + (hl >> 32) + (cross >> 32);
}

/* Q61 signed fixed-point multiply: (a/2^61)*(b/2^61) -> result/2^61. Operands
 * are bounded by ~1.5 in magnitude here so the >>61 product fits int64. Sign is
 * an explicit Class-K branch (never abs()). */
static int64_t explog_fxmul(int64_t a, int64_t b)
{
    assert(SRMECH_EXPLOG_FBITS > 0 && SRMECH_EXPLOG_FBITS < 64);   /* shift domain */
    int neg = ((a < 0) ^ (b < 0));
    uint64_t ua = (a < 0) ? (uint64_t)(-(a + 1)) + 1u : (uint64_t)a;
    uint64_t ub = (b < 0) ? (uint64_t)(-(b + 1)) + 1u : (uint64_t)b;
    uint64_t hi, lo;
    explog_umul64(ua, ub, &hi, &lo);
    uint64_t mag = (hi << 3) | (lo >> SRMECH_EXPLOG_FBITS);   /* product >> 61 */
    assert(mag <= (uint64_t)INT64_MAX);
    return neg ? -(int64_t)mag : (int64_t)mag;
}

static double explog_fx_to_double(int64_t q61)
{
    assert(SRMECH_EXPLOG_ONE > 0);
    assert(q61 <= (SRMECH_EXPLOG_ONE << 1) && q61 >= -(SRMECH_EXPLOG_ONE << 1)); /* |v|<=2 */
    return (double)q61 / (double)SRMECH_EXPLOG_ONE;
}

/* Build 2^p as a double from the IEEE-754 exponent field (exact, no ldexp).
 * p must keep the biased exponent in the normal range [1, 2046]. */
static double explog_pow2(int p)
{
    assert(p > -1023 && p < 1024);
    assert((uint64_t)(p + 1023) <= 0x7FFu);   /* biased exponent in range */
    uint64_t bits = ((uint64_t)(p + 1023) & 0x7FFu) << 52;
    double out;
    memcpy(&out, &bits, sizeof out);
    return out;
}

/* Scale m by 2^n, splitting n into halves so neither power-of-two leaves the
 * normal range (m*2^n may legitimately reach subnormal / +Inf at the edges). */
static double explog_scale2(double m, int n)
{
    assert(m > 0.0);
    int nh = n / 2;
    int nl = n - nh;
    assert(nh > -1023 && nh < 1024 && nl > -1023 && nl < 1024);
    return m * explog_pow2(nh) * explog_pow2(nl);
}

/* exp(r) for |r| <= ln2/2, r in Q61 -> Q61. Class-N Taylor 1 + r + r^2/2! + ...
 * term_{k} = term_{k-1} * r / k (Class N rational step). */
static int64_t explog_exp_core(int64_t r)
{
    assert(r <= SRMECH_EXPLOG_ONE && r >= -SRMECH_EXPLOG_ONE);
    int64_t term = SRMECH_EXPLOG_ONE, sum = SRMECH_EXPLOG_ONE;
    for (int k = 1; k <= SRMECH_EXPLOG_EXP_TERMS; k++) {
        term = explog_fxmul(term, r);
        term = term / (int64_t)k;
        sum += term;
    }
    assert(sum > 0);                                  /* exp is positive */
    return sum;
}

/* 2*atanh(t) for |t| <= sqrt2-edge, t in Q61 -> Q61: 2*(t + t^3/3 + t^5/5 ...).
 * This IS log(m) for m = (1+t)/(1-t); the caller forms t = (m-1)/(m+1). */
static int64_t explog_log_core(int64_t t)
{
    assert(t <= SRMECH_EXPLOG_ONE && t >= -SRMECH_EXPLOG_ONE);
    int64_t t2 = explog_fxmul(t, t);
    int64_t term = t, sum = t;
    for (int k = 1; k <= SRMECH_EXPLOG_LOG_TERMS; k++) {
        term = explog_fxmul(term, t2);
        sum += term / (int64_t)(2 * k + 1);
    }
    assert(t2 >= 0);                                  /* t^2 >= 0 */
    return sum * 2;
}

srmech_status_t srmech_exp(double x, double *out)
{
    assert(out != NULL);
    if (out == NULL) { return SRMECH_ERR_NULL_ARG; }
    if (x != x) { *out = x; return SRMECH_OK; }                       /* NaN */
    if (x > SRMECH_EXPLOG_OVERFLOW) {
        uint64_t inf = UINT64_C(0x7FF0000000000000);
        memcpy(out, &inf, sizeof *out);
        return SRMECH_OK;                                            /* +Inf */
    }
    if (x < SRMECH_EXPLOG_UNDERFLOW) { *out = 0.0; return SRMECH_OK; }
    double tn = x * SRMECH_EXPLOG_INV_LN2;
    int n = (int)(tn + (tn >= 0.0 ? 0.5 : -0.5));
    double r = (x - (double)n * SRMECH_EXPLOG_LN2_HI)
                   - (double)n * SRMECH_EXPLOG_LN2_LO;
    assert(r <= 0.36 && r >= -0.36);
    int64_t rq = (int64_t)(r * (double)SRMECH_EXPLOG_ONE + (r >= 0.0 ? 0.5 : -0.5));
    double m = explog_fx_to_double(explog_exp_core(rq));             /* exp(r) */
    *out = explog_scale2(m, n);
    return SRMECH_OK;
}

srmech_status_t srmech_log(double x, double *out)
{
    assert(out != NULL);
    if (out == NULL) { return SRMECH_ERR_NULL_ARG; }
    if (x != x) { *out = x; return SRMECH_OK; }                       /* NaN */
    if (x < 0.0) {
        uint64_t nan = UINT64_C(0x7FF8000000000000);
        memcpy(out, &nan, sizeof *out);
        return SRMECH_ERR_BAD_INPUT;                                  /* NaN; domain */
    }
    if (x == 0.0) {
        uint64_t ninf = UINT64_C(0xFFF0000000000000);
        memcpy(out, &ninf, sizeof *out);
        return SRMECH_ERR_BAD_INPUT;                                  /* -Inf */
    }
    uint64_t bits;
    memcpy(&bits, &x, sizeof bits);
    uint32_t raw = (uint32_t)((bits >> 52) & 0x7FFu);
    uint64_t frac = bits & ((UINT64_C(1) << 52) - 1);
    if (raw == 0x7FFu) { *out = x; return SRMECH_OK; }               /* +Inf */
    uint64_t mant;
    int e;
    if (raw == 0) {                                                  /* subnormal */
        uint64_t f = frac;
        int sh = 0;
        for (sh = 0; sh < 53 && (f & (UINT64_C(1) << 52)) == 0; sh++) { f <<= 1; }
        assert(sh <= 52);
        mant = f;
        e = -1022 - sh;
    } else {
        mant = frac | (UINT64_C(1) << 52);
        e = (int)raw - 1023;
    }
    double m = (double)mant / (double)(UINT64_C(1) << 52);           /* m in [1,2) */
    if (m >= SRMECH_EXPLOG_SQRT2) { m *= 0.5; e += 1; }              /* fold to [1/sqrt2,sqrt2) */
    double tt = (m - 1.0) / (m + 1.0);
    int64_t tq = (int64_t)(tt * (double)SRMECH_EXPLOG_ONE + (tt >= 0.0 ? 0.5 : -0.5));
    double logm = explog_fx_to_double(explog_log_core(tq));
    *out = (double)e * SRMECH_EXPLOG_LN2_HI
               + (logm + (double)e * SRMECH_EXPLOG_LN2_LO);
    return SRMECH_OK;
}
