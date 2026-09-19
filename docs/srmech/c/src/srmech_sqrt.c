/* srmech_sqrt.c — Class-N rational sqrt cascade for the NATIVE (executable)
 * tier (v0.7.0rc45; C-transpile triality coherence, rc42->rc46 arc step 3).
 *
 * The Python `srmech.math.rational.sqrt` computes sqrt as an INTEGER
 * floor-isqrt on a scaled radicand — `isqrt(xn*2^(2b)/xd) / 2^b` — Class N
 * rational arithmetic ∘ Class K sqrt-convergence (asymptotic-DoF), no float
 * `math.sqrt`. rc40 routed the Python callers onto it; this file gives the C
 * peer so `srmech_laplacian.c`'s cyclic-Jacobi eigensolver (the off-diagonal
 * norm + rotation angles) runs the cascade on a native install, not libm.
 *
 * Algorithm (no libm, no float sqrt):
 *   x = +/- M * 2^e read from the IEEE-754 bit pattern (no frexp), handed to
 *   srmech_sqrt_core (srmech_sqrt_internal.h): NORMALISE the radicand into
 *   [2^106, 2^109) so the floor root always carries 54 or 55 bits, pin the
 *   halved exponent's parity, root it with the portable two-limb 128-bit
 *   integer square root below (bit-by-bit, no division, no __int128), and set
 *   a STICKY low bit when the radicand is not a perfect square. The double
 *   projection then rounds that root to 53 bits IN INTEGERS and scales by a
 *   power of two built directly from the IEEE exponent field (exact, no
 *   ldexp). The result is the CORRECTLY ROUNDED double of sqrt(x).
 *
 * 0.9.0rc476 (`#T1188`) — WHAT THIS PARAGRAPH USED TO SAY, AND WHY IT WAS THE
 * DEFECT. It read "root = isqrt(M << 2K) ... K = 27 gives full double
 * precision", and "Validated vs libm to machine epsilon (rel err <= 2.3e-16)
 * over 50000+ values; 1/sqrt(d) bit-exact". Three things wrong at once.
 * (a) K = 27 does NOT give full double precision: M is taken straight from the
 * IEEE mantissa field, so for a SUBNORMAL x it is far below 2^52 -- M = 1
 * gives isqrt(1 << 54) = 2^27, a 28-BIT root -- and the root's width therefore
 * tracked the operand's magnitude instead of being fixed. Measured at rc475 at
 * this exported symbol: 4032 of the 4096 subnormal mantissas 1..4096 served a
 * double that is NOT the correctly rounded root, the worst by 16,609,076 ulps.
 * (b) Even for normal x the floor is not a rounding: 480 of the 1956
 * non-square integers in 2..2000 came back one ulp LOW, all on the same side,
 * because a floored root can sit on a rounding midpoint. (c) "Validated vs
 * libm" is a LIBM ORACLE, which this library does not use and cannot be
 * checked against by a bare-C host; and a relative-error bound cannot see a
 * 1-ulp misround at all, which is why it passed while (a) and (b) were true.
 * The oracle is now EXACT INTEGER arithmetic -- c/test/test_srmech_sqrt.c and
 * python/tests/test_sqrt_correct_rounding_rc476.py decide every row by an
 * integer midpoint comparison -- and the measured misround count is 0 over
 * both row sets, with a minimum root width of 55.
 *
 * JPL Power-of-Ten: Rule 1 (no goto) OK; Rule 2 (bounded loops) OK -- there
 * are now TWO counted loops, the isqrt at exactly 64 iterations and the
 * 192-bit long division at exactly 192, both `for` with entry-fixed trip
 * counts and neither `while (1)` nor `for (;;)`; Rule 3 (no malloc) OK; Rule 4
 * (<=60 lines/fn) OK; Rule 5 (>=2 asserts/fn) OK; Rule 7 (status) OK -- and
 * see srmech_sqrt_internal.h for the one thing Rule 7's detector CANNOT see
 * here; Rule 10 (warnings clean) OK.
 *
 * License: MIT.
 */

#include "srmech.h"
#include "srmech_sqrt_internal.h"

#include <assert.h>
#include <stdint.h>
#include <string.h>

/* (0.9.0rc476, `#T1188`: `#define SRMECH_SQRT_K 27` stood here, commented
 * "root precision bits: isqrt(M<<54) -> 54-bit root". Its four uses went with
 * the algorithm it named; measured ZERO other readers tree-wide, so the macro
 * went too rather than being left describing a deleted recipe. Its successor
 * is SRMECH_SQRT_CORE_BITS = 108, beside srmech_sqrt_core below.) */

/* floor(sqrt(N)) for a 128-bit unsigned N = (nhi:nlo); result fits uint64.
 * Restoring binary digit-by-digit sqrt, two bits per step (Wikipedia
 * "Methods of computing square roots", binary). No division. */
static uint64_t srmech_isqrt128(uint64_t nhi, uint64_t nlo)
{
    uint64_t rem_hi = 0, rem_lo = 0;     /* running remainder (128-bit) */
    uint64_t root = 0;                    /* running root */
    assert(rem_hi == 0 && rem_lo == 0);  /* remainder starts empty */
    for (int i = 63; i >= 0; i--) {
        unsigned sh = (unsigned)(2 * i);
        uint64_t two = (sh >= 64) ? ((nhi >> (sh - 64)) & 3u) : ((nlo >> sh) & 3u);
        rem_hi = (rem_hi << 2) | (rem_lo >> 62);     /* rem = (rem<<2) | two */
        rem_lo = (rem_lo << 2) | two;
        uint64_t cand_lo = (root << 2) | 1u;         /* cand = (root<<2) | 1 */
        uint64_t cand_hi = root >> 62;
        int ge = (rem_hi > cand_hi) || (rem_hi == cand_hi && rem_lo >= cand_lo);
        if (ge) {
            uint64_t borrow = (rem_lo < cand_lo) ? 1u : 0u;
            rem_lo -= cand_lo;
            rem_hi = rem_hi - cand_hi - borrow;
            root = (root << 1) | 1u;
        } else {
            root <<= 1;
        }
    }
    assert(rem_hi <= nhi || nhi == 0);   /* remainder did not exceed radicand */
    return root;
}

/* Build 2^p as a double directly from the IEEE-754 exponent field (exact, no
 * ldexp). p must keep the biased exponent in the normal range [1, 2046]. */
static double srmech_pow2(int p)
{
    assert(p > -1023 && p < 1024);
    assert((uint64_t)(p + 1023) <= 0x7FFu);   /* biased exponent in range */
    uint64_t bits = ((uint64_t)(p + 1023) & 0x7FFu) << 52;
    double out;
    memcpy(&out, &bits, sizeof out);
    return out;
}

/* ── 0.9.0rc476 (`#T1188`) the STICKY, MAGNITUDE-NORMALISED core ───────────
 * Declared in srmech_sqrt_internal.h; see that header for the contract and
 * for what the JPL Rule-7 detector cannot see about it. The Python twin is
 * srmech.math.rational._sqrt_core and the two agree bit for bit. */

/* The normalise window. s = 108 - (bitlen(num) - bitlen(den)) lands the scaled
 * radicand in [2^106, 2^109) at EVERY magnitude, so the floor root always
 * carries 54 or 55 bits and the sticky root 55 or 56. 108 is the measured
 * floor: at 107 the parity pin can drop the radicand to 105 bits and the root
 * to 53, one bit short of deciding the rounding. */
#define SRMECH_SQRT_CORE_BITS 108

static unsigned srmech_bitlen64(uint64_t v)
{
    unsigned n = 0;
    assert(v != 0u);
    while (v != 0u) { v >>= 1; n++; }
    assert(n >= 1u && n <= 64u);
    return n;
}

/* 192-bit (h2:h1:h0) / 64-bit d -> 128-bit quotient (*qhi:*qlo), 64-bit
 * remainder returned. Exactly 192 iterations; no __int128, no division
 * instruction, so gcc / clang / MSVC compute the same integers. */
static uint64_t srmech_div192_64(uint64_t h2, uint64_t h1, uint64_t h0,
                                 uint64_t d, uint64_t *qhi, uint64_t *qlo)
{
    uint64_t rem = 0, q_hi = 0, q_lo = 0;
    assert(d != 0u);
    assert(qhi != NULL && qlo != NULL);
    for (int i = 191; i >= 0; i--) {
        uint64_t src = (i >= 128) ? h2 : ((i >= 64) ? h1 : h0);
        unsigned sh = (unsigned)(i & 63);
        uint64_t bit = (src >> sh) & 1u;
        rem = (rem << 1) | bit;
        q_hi = (q_hi << 1) | (q_lo >> 63);
        q_lo <<= 1;
        if (rem >= d) { rem -= d; q_lo |= 1u; }
    }
    *qhi = q_hi;
    *qlo = q_lo;
    return rem;
}

/* STATIC on purpose. The shared entry this file publishes to the other
 * translation units is srmech_sqrt_scaled (below), the DOUBLE projection, so
 * that the rounding lives in exactly one place instead of being re-derived at
 * every consumer. Keeping the core file-local also puts it inside Rule 7's own
 * population — test_jpl_audit.py::_rule7_discards builds that population as
 * `srmech.h exports | same-file statics`, so a discarded status HERE is seen,
 * which is not true of srmech_sqrt_scaled. */
static srmech_status_t srmech_sqrt_core(uint64_t num, uint64_t den, int32_t e0,
                                        uint64_t *out_root, int32_t *out_p)
{
    uint64_t t[3] = {0u, 0u, 0u};
    uint64_t rhi = 0, rlo = 0, rem = 0u, root, a, b, ab, bb, aa, sq_hi, sq_lo;
    int bn, bd, s, w, off, exact;
    assert(out_root != NULL);
    assert(out_p != NULL);
    if (out_root == NULL || out_p == NULL) { return SRMECH_ERR_NULL_ARG; }
    if (num == 0u || den == 0u) { return SRMECH_ERR_BAD_INPUT; }
    bn = (int)srmech_bitlen64(num);
    bd = (int)srmech_bitlen64(den);
    s = SRMECH_SQRT_CORE_BITS - (bn - bd);                        /* NORMALISE */
    if ((((uint64_t)(int64_t)e0 - (uint64_t)(int64_t)s) & 1u) != 0u) { s -= 1; }
    /* No bignum here, so a radicand needing a NEGATIVE shift is REFUSED, not
     * asserted away — the header declares that domain. Unreachable from the
     * two exported callers (den == 1, num <= 2^53 gives s >= 56). */
    if (s < 0 || s + bn > 192) { return SRMECH_ERR_BAD_INPUT; }
    w = s / 64;
    off = s % 64;
    t[w] = (off == 0) ? num : (num << off);
    if (off != 0 && w + 1 < 3) { t[w + 1] = num >> (64 - off); }
    if (den == 1u) { rhi = t[1]; rlo = t[0]; assert(t[2] == 0u); }
    else { rem = srmech_div192_64(t[2], t[1], t[0], den, &rhi, &rlo); }
    root = srmech_isqrt128(rhi, rlo);
    a = root >> 32; b = root & 0xFFFFFFFFu;                  /* root^2 in 128b */
    ab = a * b; bb = b * b; aa = a * a;
    sq_lo = bb + (ab << 33);
    sq_hi = aa + (ab >> 31) + ((sq_lo < bb) ? 1u : 0u);
    exact = (rem == 0u) && (sq_hi == rhi) && (sq_lo == rlo);
    if (exact) { *out_root = root; *out_p = (int32_t)((e0 - s) / 2); }
    else { *out_root = 2u * root + 1u; *out_p = (int32_t)((e0 - s) / 2) - 1; }
    assert(*out_root >= (UINT64_C(1) << 53));              /* the NORMALISE */
    return SRMECH_OK;
}

/* The double projection: round the core's root to 53 bits IN INTEGERS, so the
 * served value does not depend on the host's uint64 -> double conversion or on
 * the FPU rounding mode. A tie is impossible for an INEXACT root: that root is
 * 2*floor+1, hence ODD, while a tie needs the discarded low k bits to equal
 * 2^(k-1) with k >= 2, whose low bit is 0. An EXACT root's discarded bits are
 * the true value's own, where ties-to-even is the right answer. */
static double srmech_sqrt_project(uint64_t root, int32_t p)
{
    unsigned bl, k;
    uint64_t m, low, half;
    assert(root >= (UINT64_C(1) << 53));
    bl = srmech_bitlen64(root);
    assert(bl >= 54u && bl <= 57u);
    k = bl - 53u;
    m = root >> k;
    low = root & ((UINT64_C(1) << k) - 1u);
    half = UINT64_C(1) << (k - 1u);
    if (low > half || (low == half && (m & 1u) != 0u)) { m += 1u; }
    if ((m >> 53) != 0u) { m >>= 1; p += 1; }
    p += (int32_t)k;
    return (double)m * srmech_pow2(p);       /* (double)m is EXACT: m < 2^53 */
}

/* The ONE shared entry (srmech_sqrt_internal.h). See that header for the
 * contract and for what Rule 7's detector cannot see about its call sites. */
srmech_status_t srmech_sqrt_scaled(uint64_t num, uint64_t den, int32_t e0,
                                   double *out)
{
    uint64_t root = 0;
    int32_t p = 0;
    srmech_status_t st;
    assert(out != NULL);
    if (out == NULL) { return SRMECH_ERR_NULL_ARG; }
    st = srmech_sqrt_core(num, den, e0, &root, &p);
    if (st != SRMECH_OK) { *out = 0.0; return st; }
    assert(root >= (UINT64_C(1) << 53));
    *out = srmech_sqrt_project(root, p);
    return SRMECH_OK;
}

/* The SAME projection, over a (root, p) pair a caller produced itself.
 *
 * rc477 (`#T1188`). srmech_axis_unit normalises an arbitrary double axis
 * EXACTLY, which needs a bignum radicand and therefore cannot go through
 * srmech_sqrt_core's uint64 num/den wire. What it must NOT do is re-derive the
 * 53-bit rounding: this header's own sentence is that "a rounding rule written
 * twice is a rounding rule that will disagree once". So the bignum side hands
 * back the core's OWN output shape -- the odd sticky root and its exponent --
 * and the projection stays here, in one place, byte-identical for both callers.
 *
 * `root` must satisfy the core's post-condition (>= 2^53, 54..57 bits), which
 * is what srmech_sqrt_project asserts; a caller that cannot meet it is REFUSED
 * rather than served, because the assert is a contract and not a hope. */
srmech_status_t srmech_sqrt_project_root(uint64_t root, int32_t p, double *out)
{
    unsigned bl;
    assert(out != NULL);
    assert(sizeof(root) == 8u);
    if (out == NULL) { return SRMECH_ERR_NULL_ARG; }
    if (root < (UINT64_C(1) << 53)) { *out = 0.0; return SRMECH_ERR_BAD_INPUT; }
    bl = srmech_bitlen64(root);
    if (bl < 54u || bl > 57u) { *out = 0.0; return SRMECH_ERR_BAD_INPUT; }
    *out = srmech_sqrt_project(root, p);
    return SRMECH_OK;
}

/* 1/sqrt(x) for a POSITIVE FINITE double, correctly rounded, in one step.
 *
 * rc476 (`#T1188`). The normalised-Laplacian consumers spelled this
 * `1.0 / lap_sqrt(d)`, which rounds TWICE, and the second rounding is not
 * repaired by fixing the first: measured, repairing the root alone moved
 * srmech_normalized_laplacian's off-diagonal by one ulp, because the shipped
 * value was right only by the two errors cancelling. A double IS a dyadic
 * rational mant*2^e, so its RECIPROCAL is the exact rational (1/mant)*2^-e and
 * goes straight into the core -- one rounding, at the projection.
 *
 * Refuses a non-positive or non-finite x with SRMECH_ERR_BAD_INPUT; every
 * caller guards `d > 0` already, and none of them can reach +Inf with a finite
 * edge-weight sum, but a refusal is cheaper than an assumption. */
srmech_status_t srmech_inv_sqrt(double x, double *out)
{
    uint64_t bits, frac, mant;
    uint32_t raw;
    int32_t e;
    assert(out != NULL);
    if (out == NULL) { return SRMECH_ERR_NULL_ARG; }
    if (!(x > 0.0)) { *out = 0.0; return SRMECH_ERR_BAD_INPUT; }  /* NaN too */
    memcpy(&bits, &x, sizeof bits);
    raw = (uint32_t)((bits >> 52) & 0x7FFu);
    if (raw == 0x7FFu) { *out = 0.0; return SRMECH_ERR_BAD_INPUT; } /* +Inf */
    frac = bits & ((UINT64_C(1) << 52) - 1);
    mant = (raw == 0) ? frac : (frac | (UINT64_C(1) << 52));
    e = (raw == 0) ? -1074 : (int32_t)raw - 1075;             /* x = mant*2^e */
    assert(mant != 0u);
    return srmech_sqrt_scaled(1u, mant, -e, out);             /* sqrt(1/x) */
}

/* 0.9.0rc473 (`#T1188`) — two repairs in the refusal path, one to the STATUS
 * and one to the written VALUE, and they are independent defects.
 *
 *  1. NaN was SERVED. `x < 0.0` is false for NaN and so is `x == 0.0`, so a
 *     NaN fell through to the bit-read, matched raw == 0x7FF, and returned
 *     (SRMECH_OK, NaN) on the +Inf path. The pure peer raises ("sqrt: x must
 *     be finite"); srmech_sqrt_q61 already returned SRMECH_ERR_BAD_INPUT.
 *  2. The negative branch wrote `x - x`, which the comment called NaN and
 *     which is NaN only for a non-finite x. For every FINITE negative x it is
 *     exactly 0.0 — measured at rc472, srmech_rational_sqrt(-4.0) returned
 *     (SRMECH_ERR_BAD_INPUT, 0.0), so the status was already right and a
 *     caller reading the value alone got a real number where srmech.h and the
 *     comment on that very line both promised NaN. The status-only half of
 *     this rc would not have closed it, which is why the gate asserts the
 *     written value as well.
 *
 * +Inf stays served (-> +Inf) and that decline is tracked: lap_sqrt and
 * sq_sqrt reach it on the tau-overflow path and rely on sqrt(+Inf) = +Inf. */
srmech_status_t srmech_rational_sqrt(double x, double *out)
{
    assert(out != NULL);
    if (out == NULL) { return SRMECH_ERR_NULL_ARG; }
    if (x != x) { *out = x; return SRMECH_ERR_BAD_INPUT; }        /* NaN; no root */
    if (x < 0.0) {
        uint64_t nan_bits = UINT64_C(0x7FF8000000000000);
        memcpy(out, &nan_bits, sizeof *out);
        return SRMECH_ERR_BAD_INPUT;                              /* NaN; domain */
    }
    if (x == 0.0) { *out = 0.0; return SRMECH_OK; }
    uint64_t bits;
    memcpy(&bits, &x, sizeof bits);
    uint32_t raw = (uint32_t)((bits >> 52) & 0x7FFu);
    uint64_t frac = bits & ((UINT64_C(1) << 52) - 1);
    if (raw == 0x7FFu) { *out = x; return SRMECH_OK; }            /* +Inf -> +Inf */
    uint64_t mant = (raw == 0) ? frac : (frac | (UINT64_C(1) << 52));
    int32_t e = (raw == 0) ? -1074 : (int32_t)raw - 1075;        /* x = mant * 2^e */
    uint64_t root = 0;
    int32_t p = 0;
    srmech_status_t st;
    assert(mant != 0);                                          /* nonzero handled above */
    /* rc476 (`#T1188`): the core owns the parity pin, the NORMALISE the inline
     * version lacked, and the sticky bit. `st` is CAPTURED and asserted rather
     * than discarded — see srmech_sqrt_internal.h: Rule 7's detector builds its
     * population from srmech.h exports plus same-file statics, and this callee
     * is neither, so the gate cannot see a discard here. */
    st = srmech_sqrt_core(mant, 1u, e, &root, &p);
    assert(st == SRMECH_OK);                                    /* den==1 cannot refuse */
    if (st != SRMECH_OK) { *out = 0.0; return st; }
    *out = srmech_sqrt_project(root, p);
    return SRMECH_OK;
}

/* ── 0.9.0rc7 stay-rational Q61 surface (F868) ────────────────────────────
 * sqrt(x) = root * 2^p EXACTLY, with (root, p) the STICKY pair from
 * srmech_sqrt_core. This peer returns the integer pieces instead of projecting
 * to a double, so the Python `rational.sqrt` dispatches to native AND keeps
 * the exact rational: Python forms _q(root << p, 1) for p >= 0, else
 * _q(root, 1 << -p) — the GLUE IS UNCHANGED by rc476 and reinterprets the new
 * pair correctly, which is measured through sqrt() itself and not argued.
 * sqrt(0) = 0 -> (*out_root, *out_p) = (0, 0). Negative / non-finite x has no
 * rational sqrt -> SRMECH_ERR_BAD_INPUT (the Python peer raises identically).
 *
 * 0.9.0rc476 (`#T1188`): the pair MOVED. It was root = isqrt(M << 54),
 * p = e/2 - 27, whose root was as narrow as 28 bits for a subnormal M; it is
 * now the normalised sticky pair, root >= 2^53 always and ODD unless the
 * radicand is a perfect square. `root` stays inside int64 with room (<= 56
 * bits), which is why this signature does not change while its VALUES do. */
srmech_status_t srmech_sqrt_q61(double x, int64_t *out_root, int64_t *out_p)
{
    assert(out_root != NULL);
    assert(out_p != NULL);
    if (out_root == NULL || out_p == NULL) { return SRMECH_ERR_NULL_ARG; }
    if (x < 0.0 || x != x) { *out_root = 0; *out_p = 0; return SRMECH_ERR_BAD_INPUT; }
    if (x == 0.0) { *out_root = 0; *out_p = 0; return SRMECH_OK; }
    uint64_t bits;
    memcpy(&bits, &x, sizeof bits);
    uint32_t raw = (uint32_t)((bits >> 52) & 0x7FFu);
    uint64_t frac = bits & ((UINT64_C(1) << 52) - 1);
    if (raw == 0x7FFu) { *out_root = 0; *out_p = 0; return SRMECH_ERR_BAD_INPUT; } /* +Inf */
    uint64_t mant = (raw == 0) ? frac : (frac | (UINT64_C(1) << 52));
    int32_t e = (raw == 0) ? -1074 : (int32_t)raw - 1075;       /* x = mant * 2^e */
    uint64_t root = 0;
    int32_t p = 0;
    srmech_status_t st;
    assert(mant != 0);
    st = srmech_sqrt_core(mant, 1u, e, &root, &p);              /* rc476 core */
    assert(st == SRMECH_OK);                                    /* den==1 cannot refuse */
    if (st != SRMECH_OK) { *out_root = 0; *out_p = 0; return st; }
    *out_root = (int64_t)root;
    *out_p = (int64_t)p;
    return SRMECH_OK;
}

/* ── 0.9.0rc13 public integer floor-sqrt (the stdlib `math.isqrt` purge) ───
 * floor(sqrt((nhi:nlo))) for a 128-bit unsigned radicand, written to
 * *out_root. Exposes the file-local two-limb isqrt128 as a standalone-C
 * symbol so a C-only host (and the Python `rational._integer_sqrt` dispatch)
 * computes the integer square root with NO stdlib `math.isqrt` — the last
 * pure-integer primitive Python was still borrowing from the maths library.
 * The Python peer falls back to an arbitrary-precision integer-Newton for
 * radicands beyond 128 bits (the pi_cascade D=1000 scale). */
srmech_status_t srmech_isqrt(uint64_t nhi, uint64_t nlo, uint64_t *out_root)
{
    assert(out_root != NULL);
    if (out_root == NULL) { return SRMECH_ERR_NULL_ARG; }
    uint64_t root = srmech_isqrt128(nhi, nlo);
    assert(nhi != 0 || root * root <= nlo);   /* floor property (64-bit case) */
    *out_root = root;
    return SRMECH_OK;
}
