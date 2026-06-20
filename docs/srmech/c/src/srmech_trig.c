/* srmech_trig.c — Class-N rational trig cascade for the NATIVE (executable)
 * tier (v0.7.0rc43; C-transpile triality coherence, the rc42->rc46 arc).
 *
 * The Python `srmech.amsc.rational.{sin,cos,atan,atan2}` compute trig as the
 * Class-N rational Taylor cascade (range-reduce the angle, then a truncated
 * Taylor series, project to float as the LAST step). rc40/rc41 routed the
 * PYTHON callers onto that cascade, but on a native install the C peers
 * (`srmech_pin_slot` / `srmech_kepler_solve` / `srmech_cascade_kuramoto_*`)
 * still called libm `sin`/`cos`/`atan2` — so the EXECUTABLE layer diverged
 * from the source + notebook (`docs/srmech/notes/continuous_math_as_14_class_cascade.md`
 * "C-transpile triality coherence"). This file makes the executable run the
 * cascade too.
 *
 * Discipline — INTEGERS for cyclic algebra (user direction 2026-06-05,
 * "should prefer ints over float always for cyclic algebra"; the continuous
 * number line is a projection, `[[feedback_continuous_number_line_pedagogical_obstacle]]`):
 *   - the CYCLIC range-reduction (mod pi/2, the Class-I/Class-K octant step)
 *     is done in INTEGER arithmetic — never float. The IEEE-754 input is read
 *     as an exact integer `M * 2^E` from its bit pattern (no `frexp`), the
 *     octant count `k` comes from an integer wide-multiply by a high-precision
 *     `2/pi`, and the remainder is an exact integer fraction.
 *   - the Class-N Taylor series runs in Q61 fixed-point (a power-of-two
 *     denominator rational — Class N).
 *   - float appears ONLY at the final projection `(double)sum / 2^61` (the
 *     one legitimate "the rational is projected to float as the last step").
 * No libm transcendental, no `abs()` (Class-K sign-branch), no malloc/goto.
 *
 * Constant attestation (derive-and-assert, the rc19 HAL discipline). The two
 * cascade constants below are derived from the Archimedes pi-cascade
 * (`srmech.amsc.rational._pi_rational(50)`, no libm):
 *   TWO_OVER_PI_Q64 = round((2/pi) * 2^64) = 11743562013128004906
 *   HALF_PI_Q61     = round((pi/2) * 2^61) = 3622009729038561421
 * `srmech_trig_self_check()` re-derives the sin/cos identity at runtime
 * (sin^2 + cos^2 == 1 to fixed-point round-off) so a corrupted constant is
 * caught. Validated vs libm to machine epsilon over 5000+ angles in
 * [-1000, 1000] (the prototype in the rc43 dispatch note).
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
#include <stdbool.h>
#include <stdint.h>
#include <string.h>

#define SRMECH_TRIG_FBITS   61
#define SRMECH_TRIG_ONE     (INT64_C(1) << SRMECH_TRIG_FBITS)   /* 1.0 in Q61 */
#define SRMECH_TRIG_MASK61  (SRMECH_TRIG_ONE - 1)

/* Cascade constants (see header block). */
static const uint64_t SRMECH_TRIG_TWO_OVER_PI_Q64 =
    UINT64_C(11743562013128004906);          /* (2/pi) * 2^64 */
static const int64_t  SRMECH_TRIG_HALF_PI_Q61 =
    INT64_C(3622009729038561421);            /* (pi/2) * 2^61 */

/* atan three-band edges tan(pi/8)=sqrt2-1, cot(pi/8)=sqrt2+1 (band SELECTION
 * thresholds only — they never enter the result, so float literals are fine;
 * the band keeps every atan series argument |m| <= sqrt2-1 for fast Class-N
 * convergence). pi/2, pi/4 doubles are projected from the cascade Q61 pi/2. */
#define SRMECH_TRIG_TAN_PI8  0.41421356237309515   /* sqrt(2) - 1 */
#define SRMECH_TRIG_COT_PI8  2.414213562373095     /* sqrt(2) + 1 */

#define SRMECH_TRIG_SIN_TERMS  10   /* |r|<=pi/4: r^21/21! < 2^-62 */
#define SRMECH_TRIG_ATAN_TERMS 40   /* |m|<=sqrt2-1: matches Python _ATAN_FLOAT_TERMS */

/* ---- portable 64x64 -> 128 unsigned multiply (no __int128 / _umul128) ---- */
static void trig_umul64(uint64_t a, uint64_t b, uint64_t *hi, uint64_t *lo)
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
 * are bounded by ~2 in magnitude here so the >>61 product fits int64. The
 * sign is an explicit Class-K branch (never abs()). */
static int64_t trig_fxmul(int64_t a, int64_t b)
{
    assert(SRMECH_TRIG_FBITS > 0 && SRMECH_TRIG_FBITS < 64);   /* shift domain */
    int neg = ((a < 0) ^ (b < 0));
    uint64_t ua = (a < 0) ? (uint64_t)(-(a + 1)) + 1u : (uint64_t)a;
    uint64_t ub = (b < 0) ? (uint64_t)(-(b + 1)) + 1u : (uint64_t)b;
    uint64_t hi, lo;
    trig_umul64(ua, ub, &hi, &lo);
    uint64_t mag = (hi << 3) | (lo >> SRMECH_TRIG_FBITS);   /* product >> 61 */
    assert(mag <= (uint64_t)INT64_MAX);
    return neg ? -(int64_t)mag : (int64_t)mag;
}

/* Integer cyclic octant reduction: x (radians) -> (*octant in 0..3, *r in Q61
 * with |r| <= pi/4). PURE INTEGER except the bit-read of x. Returns false for
 * |x| >= 2^55 (far beyond any physical angle — the 2-word product would lose
 * the high octant bits) or non-finite x. */
static bool trig_reduce(double x, int *octant, int64_t *r_q61)
{
    assert(octant != NULL);
    assert(r_q61 != NULL);
    uint64_t bits;
    memcpy(&bits, &x, sizeof bits);
    int sign = (bits >> 63) ? 1 : 0;
    uint32_t raw = (uint32_t)((bits >> 52) & 0x7FFu);
    uint64_t frac = bits & ((UINT64_C(1) << 52) - 1);
    if (raw == 0x7FFu) { return false; }                 /* Inf / NaN */
    if (raw == 0 && frac == 0) { *octant = 0; *r_q61 = 0; return true; }
    uint64_t mant = (raw == 0) ? frac : (frac | (UINT64_C(1) << 52));
    int e = (raw == 0) ? -1074 : (int)raw - 1075;        /* x = +/- mant*2^e */
    if (e >= 3) { return false; }                        /* |x| >= 2^55 */
    uint64_t phi, plo;
    trig_umul64(mant, SRMECH_TRIG_TWO_OVER_PI_Q64, &phi, &plo);  /* |x|*2/pi*2^(64-e) */
    int s = 3 - e;                                        /* >= 1: right shift to V=...*2^61 */
    uint64_t vhi, vlo;
    if (s >= 128) { *octant = 0; *r_q61 = sign ? -(int64_t)0 : 0; return true; }
    if (s >= 64)  { vhi = 0; vlo = phi >> (s - 64); }
    else          { vhi = phi >> s; vlo = (plo >> s) | (phi << (64 - s)); }
    uint64_t q = (vhi << 3) | (vlo >> SRMECH_TRIG_FBITS); /* floor(V / 2^61) */
    uint64_t vlo61 = vlo & (uint64_t)SRMECH_TRIG_MASK61;
    int64_t fr;
    uint64_t k;
    if (vlo61 >= (UINT64_C(1) << (SRMECH_TRIG_FBITS - 1))) {   /* round half up */
        k = q + 1; fr = (int64_t)vlo61 - SRMECH_TRIG_ONE;
    } else {
        k = q; fr = (int64_t)vlo61;
    }
    if (sign) { fr = -fr; k = (uint64_t)(-(int64_t)k); }
    *octant = (int)(k & 3u);
    *r_q61 = trig_fxmul(fr, SRMECH_TRIG_HALF_PI_Q61);    /* r = frac * (pi/2) */
    return true;
}

/* sin(r) for |r| <= pi/4, r in Q61 -> Q61. Class-N alternating Taylor:
 * r - r^3/3! + r^5/5! - ...  term_k carries sign(r); the (-1)^k is applied via
 * the running sum (Class C). */
static int64_t trig_sin_core(int64_t r)
{
    assert(r <= SRMECH_TRIG_ONE && r >= -SRMECH_TRIG_ONE);
    int64_t r2 = trig_fxmul(r, r);
    int64_t term = r, sum = r;
    for (int k = 1; k <= SRMECH_TRIG_SIN_TERMS; k++) {
        term = trig_fxmul(term, r2);
        int64_t divisor = (int64_t)(2 * k) * (int64_t)(2 * k + 1);
        term = term / divisor;
        sum = (k & 1) ? (sum - term) : (sum + term);
    }
    assert(sum <= SRMECH_TRIG_ONE && sum >= -SRMECH_TRIG_ONE);
    return sum;
}

/* cos(r) for |r| <= pi/4, r in Q61 -> Q61: 1 - r^2/2! + r^4/4! - ... */
static int64_t trig_cos_core(int64_t r)
{
    assert(r <= SRMECH_TRIG_ONE && r >= -SRMECH_TRIG_ONE);
    int64_t r2 = trig_fxmul(r, r);
    int64_t term = SRMECH_TRIG_ONE, sum = SRMECH_TRIG_ONE;
    for (int k = 1; k <= SRMECH_TRIG_SIN_TERMS; k++) {
        term = trig_fxmul(term, r2);
        int64_t divisor = (int64_t)(2 * k - 1) * (int64_t)(2 * k);
        term = term / divisor;
        sum = (k & 1) ? (sum - term) : (sum + term);
    }
    assert(sum <= SRMECH_TRIG_ONE && sum >= -SRMECH_TRIG_ONE);
    return sum;
}

/* atan(m) for 0 <= m <= sqrt2-1, m in Q61 -> Q61: m - m^3/3 + m^5/5 - ... */
static int64_t trig_atan_core(int64_t m)
{
    assert(m >= 0);
    assert(m <= SRMECH_TRIG_ONE);
    int64_t m2 = trig_fxmul(m, m);
    int64_t term = m, sum = m;
    for (int k = 1; k <= SRMECH_TRIG_ATAN_TERMS; k++) {
        term = trig_fxmul(term, m2);
        int64_t odd = (int64_t)(2 * k + 1);
        int64_t contrib = term / odd;
        sum = (k & 1) ? (sum - contrib) : (sum + contrib);
    }
    return sum;
}

static double trig_to_double(int64_t q61)
{
    assert(SRMECH_TRIG_ONE > 0);
    assert(q61 <= (SRMECH_TRIG_ONE << 1) && q61 >= -(SRMECH_TRIG_ONE << 1)); /* |val|<=2 */
    return (double)q61 / (double)SRMECH_TRIG_ONE;
}

srmech_status_t srmech_sin(double x, double *out)
{
    assert(out != NULL);
    if (out == NULL) { return SRMECH_ERR_NULL_ARG; }
    int oct;
    int64_t r;
    if (!trig_reduce(x, &oct, &r)) {
        *out = x - x;                      /* NaN for Inf/NaN; 0 path unreachable here */
        return (x == x) ? SRMECH_ERR_BAD_INPUT : SRMECH_OK;
    }
    assert(oct >= 0 && oct < 4);
    int64_t sc = trig_sin_core(r), cc = trig_cos_core(r);
    int64_t v = (oct == 0) ? sc : (oct == 1) ? cc : (oct == 2) ? -sc : -cc;
    *out = trig_to_double(v);
    return SRMECH_OK;
}

srmech_status_t srmech_cos(double x, double *out)
{
    assert(out != NULL);
    if (out == NULL) { return SRMECH_ERR_NULL_ARG; }
    int oct;
    int64_t r;
    if (!trig_reduce(x, &oct, &r)) {
        *out = x - x;
        return (x == x) ? SRMECH_ERR_BAD_INPUT : SRMECH_OK;
    }
    assert(oct >= 0 && oct < 4);
    int64_t sc = trig_sin_core(r), cc = trig_cos_core(r);
    int64_t v = (oct == 0) ? cc : (oct == 1) ? -sc : (oct == 2) ? -cc : sc;
    *out = trig_to_double(v);
    return SRMECH_OK;
}

/* atan(|m|) via the three-band Class-N reduction; pi/2, pi/4 from cascade Q61. */
static double trig_atan_nonneg(double m)
{
    assert(m >= 0.0);
    double half_pi = trig_to_double(SRMECH_TRIG_HALF_PI_Q61);
    assert(half_pi > 1.5 && half_pi < 1.6);
    int64_t mq;
    if (m <= SRMECH_TRIG_TAN_PI8) {
        mq = (int64_t)(m * (double)SRMECH_TRIG_ONE + 0.5);
        return trig_to_double(trig_atan_core(mq));
    }
    if (m >= SRMECH_TRIG_COT_PI8) {                       /* atan(m)=pi/2-atan(1/m) */
        double inv = 1.0 / m;
        mq = (int64_t)(inv * (double)SRMECH_TRIG_ONE + 0.5);
        return half_pi - trig_to_double(trig_atan_core(mq));
    }
    double u = (m - 1.0) / (m + 1.0);                     /* middle band: pi/4 + atan(u) */
    int neg = (u < 0.0);
    double um = neg ? -u : u;
    mq = (int64_t)(um * (double)SRMECH_TRIG_ONE + 0.5);
    double a = trig_to_double(trig_atan_core(mq));
    return half_pi / 2.0 + (neg ? -a : a);
}

srmech_status_t srmech_atan(double x, double *out)
{
    assert(out != NULL);
    if (out == NULL) { return SRMECH_ERR_NULL_ARG; }
    double xm = (x < 0.0) ? -x : x;                       /* Class-K magnitude */
    assert(xm >= 0.0);
    double r = trig_atan_nonneg(xm);
    *out = (x < 0.0) ? -r : r;                            /* Class-C re-orient */
    return SRMECH_OK;
}

srmech_status_t srmech_atan2(double y, double x, double *out)
{
    assert(out != NULL);
    if (out == NULL) { return SRMECH_ERR_NULL_ARG; }
    double half_pi = trig_to_double(SRMECH_TRIG_HALF_PI_Q61);
    double pi = 2.0 * half_pi;
    assert(pi > 3.0 && pi < 3.3);
    if (x == 0.0) {
        *out = (y > 0.0) ? half_pi : (y < 0.0) ? -half_pi : 0.0;
        return SRMECH_OK;
    }
    double base;
    (void)srmech_atan(y / x, &base);
    if (x > 0.0) { *out = base; return SRMECH_OK; }
    *out = (y >= 0.0) ? base + pi : base - pi;            /* x<0 quadrant shift (Class C) */
    return SRMECH_OK;
}

/* ── 0.9.0rc7 stay-rational Q61 surface (F868) ────────────────────────────
 * The public sin/cos/atan project the Q61 cascade value to a 52-bit double as
 * the LAST step, throwing ~9 bits away. These peers return the EXACT int64 Q61
 * (denominator 2^61) BEFORE that projection so the Python `rational.{sin,cos,
 * atan}` dispatch to native AND keep the full 61-bit rational (`Q(v, 2^61)`),
 * not a double promoted back to Q. Same cores, no float-collapse. A non-finite
 * (or |x| >= 2^55) argument has no Q61 representation -> SRMECH_ERR_BAD_INPUT
 * (the Python peer raises identically). */
srmech_status_t srmech_sin_q61(double x, int64_t *out_q61)
{
    assert(out_q61 != NULL);
    if (out_q61 == NULL) { return SRMECH_ERR_NULL_ARG; }
    int oct;
    int64_t r;
    if (!trig_reduce(x, &oct, &r)) { return SRMECH_ERR_BAD_INPUT; }
    assert(oct >= 0 && oct < 4);
    int64_t sc = trig_sin_core(r), cc = trig_cos_core(r);
    *out_q61 = (oct == 0) ? sc : (oct == 1) ? cc : (oct == 2) ? -sc : -cc;
    return SRMECH_OK;
}

srmech_status_t srmech_cos_q61(double x, int64_t *out_q61)
{
    assert(out_q61 != NULL);
    if (out_q61 == NULL) { return SRMECH_ERR_NULL_ARG; }
    int oct;
    int64_t r;
    if (!trig_reduce(x, &oct, &r)) { return SRMECH_ERR_BAD_INPUT; }
    assert(oct >= 0 && oct < 4);
    int64_t sc = trig_sin_core(r), cc = trig_cos_core(r);
    *out_q61 = (oct == 0) ? cc : (oct == 1) ? -sc : (oct == 2) ? -cc : sc;
    return SRMECH_OK;
}

/* 0.9.0rc10 hypercomplex exp(mu*theta) twiddle (F882, srmech #205). The unit
 * exponential q = cos(theta) + mu*sin(theta), mu the equal-weight unit pure-
 * imaginary over the FIRST k_axes octonion axes (k_axes = 1/3/7 -> C/H/O). Fills
 * eight Q61 components (denominator 2^61): out8[0] = cos(theta); out8[1..k] =
 * sin(theta)/sqrt(k); out8[k+1..7] = 0. mu is unit via 1/sqrt(k) in Q61 =
 * isqrt(2^122 / k) (k=1 -> 2^61 exactly); the k=3,7 anchors are round(2^61/sqrt k)
 * and are verified === the Python isqrt cascade in the parity test (no 128-bit
 * divide in -Wpedantic C, so they are stated, not derived in-place). The eight
 * components feed a Cayley-Dickson multiply (where a hypercomplex value lives),
 * then a single projection — the literal QDFT/ODFT twiddle. Byte-exact with the
 * pure-Q61 Python mirror cascade.hypercomplex_exp. A non-finite (or |theta| >=
 * 2^55) argument has no Q61 form -> SRMECH_ERR_BAD_INPUT (the cos/sin peers gate
 * it); k_axes not in {1,3,7} -> SRMECH_ERR_BAD_INPUT. */
srmech_status_t srmech_hypercomplex_exp_q61(double theta, int k_axes,
                                            int64_t *out8)
{
    assert(out8 != NULL);
    if (out8 == NULL) { return SRMECH_ERR_NULL_ARG; }
    int64_t inv;
    if (k_axes == 1) {
        inv = SRMECH_Q61_ONE;                          /* 1/sqrt(1) = 1.0 in Q61 */
    } else if (k_axes == 3) {
        inv = INT64_C(1331279082078542925);            /* round(2^61 / sqrt 3) */
    } else if (k_axes == 7) {
        inv = INT64_C(871526737819464516);             /* round(2^61 / sqrt 7) */
    } else {
        return SRMECH_ERR_BAD_INPUT;                    /* only C/H/O imaginary axes */
    }
    assert(inv > 0);                                   /* unit norm anchor positive */
    int64_t c = 0, s = 0;
    srmech_status_t st = srmech_cos_q61(theta, &c);
    if (st != SRMECH_OK) { return st; }
    st = srmech_sin_q61(theta, &s);
    if (st != SRMECH_OK) { return st; }
    int64_t scaled = trig_fxmul(s, inv);               /* sin(theta) / sqrt(k) */
    out8[0] = c;
    for (int a = 1; a < 8; a++) {
        out8[a] = (a <= k_axes) ? scaled : INT64_C(0);
    }
    return SRMECH_OK;
}

/* atan(|m|) for m >= 0 as an exact Q61 INTEGER — the three-band recombination
 * accumulates in Q61 ints (pi/2 = HALF_PI_Q61, pi/4 = that >> 1), mirror of the
 * Python `_atan_nonneg_q61`. The COT band naturally yields pi/2 for m = +Inf
 * (1/Inf = 0 -> atan_core(0) = 0). */
static int64_t trig_atan_nonneg_q61(double m)
{
    assert(m >= 0.0);
    assert(SRMECH_TRIG_HALF_PI_Q61 > 0);   /* pi/2 anchor sane (JPL Rule 5) */
    int64_t mq;
    if (m <= SRMECH_TRIG_TAN_PI8) {
        mq = (int64_t)(m * (double)SRMECH_TRIG_ONE + 0.5);
        return trig_atan_core(mq);
    }
    if (m >= SRMECH_TRIG_COT_PI8) {                       /* atan(m) = pi/2 - atan(1/m) */
        mq = (int64_t)((1.0 / m) * (double)SRMECH_TRIG_ONE + 0.5);
        return SRMECH_TRIG_HALF_PI_Q61 - trig_atan_core(mq);
    }
    double u = (m - 1.0) / (m + 1.0);                     /* middle band: pi/4 + atan(u) */
    int neg = (u < 0.0);
    double um = neg ? -u : u;
    mq = (int64_t)(um * (double)SRMECH_TRIG_ONE + 0.5);
    int64_t a = trig_atan_core(mq);
    return (SRMECH_TRIG_HALF_PI_Q61 / 2) + (neg ? -a : a);
}

srmech_status_t srmech_atan_q61(double x, int64_t *out_q61)
{
    assert(out_q61 != NULL);
    if (out_q61 == NULL) { return SRMECH_ERR_NULL_ARG; }
    if (x != x) { return SRMECH_ERR_BAD_INPUT; }          /* NaN — not a rational */
    double xm = (x < 0.0) ? -x : x;                       /* Class-K magnitude */
    assert(xm >= 0.0);                                     /* magnitude non-negative (JPL Rule 5) */
    int64_t v = trig_atan_nonneg_q61(xm);                 /* +/-Inf -> +/- pi/2 via band */
    *out_q61 = (x < 0.0) ? -v : v;                        /* Class-C re-orient */
    return SRMECH_OK;
}
