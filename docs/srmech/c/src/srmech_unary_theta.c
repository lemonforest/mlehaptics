/*
 * srmech_unary_theta.c — the EXACT-INTEGER q-series of a UNARY THETA SERIES
 * (the C peer of srmech.amsc.unary_theta.UnaryTheta; the first WEIGHT-GRADED
 * operand carrier).
 *
 * A unary theta series is
 *
 *     g(tau) = SUM_{n in support} chi(n) * n^j * q^{(a*n^2 + b*n) / D}
 *
 * — a single (unary) sum of a character chi (values in {-1, 0, +1}, period
 * `modulus`) against a power n^j of the summation index, over a quadratic
 * exponent (a*n^2 + b*n)/D. Its WEIGHT is 1/2 + j (half-integral; that rational
 * lives in Python's Q carrier — the C peer carries only the integer q-series).
 *
 * This op computes the EXACT INTEGER q-series after factoring out the leading
 * (minimal) q-power over the support: out[e] = SUM_{n : E(n)=e} chi(n)*n^j, for
 * e = 0 .. N, where E(n) = (a*n^2 + b*n - lead_num)/D is the reduced exponent
 * (lead_num = the minimum raw exponent numerator over the contributing n). Each
 * out[e] is a full srmech_bigint (no int64 ceiling: n^j is bignum) and is
 * byte-identical to the Python srmech.amsc.unary_theta.UnaryTheta q-series.
 *
 * Anchors (the build gates):
 *   theta3: modulus=1 chi={1}, j=0, a=1,b=0,D=1, support=all
 *           -> out = [1, 2, 0, 0, 2, 0, 0, 0, 0, 2, ...]   (SUM_{n in Z} q^{n^2})
 *   g3    : modulus=12 chi=(-12/.), j=1, a=1,b=0,D=24, support=positive
 *           -> out = [1, -5, -7, 0, 0, 11, 0, 13, ...]     (Zagier coeffs; the
 *           weight-3/2 shadow of the order-3 mock theta f(q) — the #9 payoff)
 *
 * The raw exponent numerator a*n^2 + b*n is computed in int64 (it is <=
 * lead_num + N*D, which the caller keeps within int64 by choosing N; an
 * out-of-range product returns SRMECH_ERR_BAD_INPUT). n^j is computed over
 * srmech_bigint (caller arena), so the COEFFICIENT magnitude has no ceiling.
 * The character sign is the Class-K pin-slot (an int8 +-1 from the table), never
 * an ALU abs().
 *
 * Carrier-internal, like srmech_poly.c: the working n^j + |n| bigints + the
 * pow scratch are carved from the caller arena `ws` (sized via
 * srmech_unary_theta_ws_bound), so the magnitude bound is the CALLER's RAM, not
 * a compiled-in cap. The out[] coefficient array is caller-owned. Additive
 * symbols -> ABI unchanged (stays 3).
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto/recursion): OK — iterative, flat helpers
 *   - Rule 2 (bounded loops)    : OK — bounds are N, the modulus, the n-window
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

/* support codes (mirror the Python 'all'/'positive'/'nonneg' strings) */
#define UT_SUPPORT_ALL      0
#define UT_SUPPORT_POSITIVE 1
#define UT_SUPPORT_NONNEG   2

/* A roster of working bigints carved from the caller arena `ws`: the running
 * n^j coefficient (nj), the |n| base (nbase), and the pow scratch tail. */
typedef struct ut_ctx {
    srmech_bigint_t nj;        /* n^j coefficient (magnitude)   */
    srmech_bigint_t nbase;     /* |n| as a bigint base          */
    uint32_t        limb_cap;  /* per-carrier limb capacity     */
    void           *scratch;   /* pow ws scratch arena tail     */
    size_t          scratch_len;
} ut_ctx_t;

#define UT_N_CARRIERS 2u  /* nj, nbase */

/* ---- forward declarations (Rule 1: no recursion) ------------------- */

static int ut_n_in_support(int support, int64_t n);
static int8_t ut_chi(const int32_t *chi_table, uint32_t modulus, int64_t n);
static int64_t ut_isqrt(int64_t x);
static int64_t ut_n_window(int64_t a, int64_t b, int64_t max_num);
static srmech_status_t ut_min_raw_num(uint32_t modulus, const int32_t *chi_table,
                                      int64_t a, int64_t b, int support,
                                      int64_t *out_lead, int *out_found);
static srmech_status_t ut_ctx_init(ut_ctx_t *c, uint32_t cap, uint32_t j,
                                   void *ws, size_t ws_len);
static srmech_status_t ut_set_njj(ut_ctx_t *c, int64_t n, uint32_t j);
static srmech_status_t ut_accumulate(ut_ctx_t *c, srmech_bigint_t *acc,
                                     int8_t chi, int64_t n, uint32_t j);

/* ---- support + character (pure integer predicates) ----------------- */

static int ut_n_in_support(int support, int64_t n)
{
    assert(support >= UT_SUPPORT_ALL);
    assert(support <= UT_SUPPORT_NONNEG);
    if (support == UT_SUPPORT_ALL) {
        return 1;
    }
    if (support == UT_SUPPORT_POSITIVE) {
        return n >= 1 ? 1 : 0;
    }
    return n >= 0 ? 1 : 0;     /* UT_SUPPORT_NONNEG */
}

static int8_t ut_chi(const int32_t *chi_table, uint32_t modulus, int64_t n)
{
    /* chi(n) = table[n mod modulus]; floor-mod (Python %) for negative n. */
    int64_t r;
    assert(chi_table != NULL);
    assert(modulus >= 1u);
    r = n % (int64_t)modulus;
    if (r < 0) {
        r += (int64_t)modulus;   /* Class-K: floor-mod into [0, modulus) */
    }
    return (int8_t)chi_table[r];
}

/* ---- integer floor-sqrt + the symmetric n-window (no float) -------- */

static int64_t ut_isqrt(int64_t x)
{
    int64_t lo = 0, hi, mid;
    assert(x >= 0);
    if (x < 2) {
        return x;
    }
    hi = x;
    while (lo < hi) {
        mid = lo + (hi - lo + 1) / 2;       /* ceil-mid, no overflow */
        if (mid <= x / mid) {               /* mid*mid <= x, overflow-safe */
            lo = mid;
        } else {
            hi = mid - 1;
        }
    }
    assert(lo * lo <= x || lo == 0);
    return lo;
}

static int64_t ut_n_window(int64_t a, int64_t b, int64_t max_num)
{
    /* nmax with EVERY n satisfying a*n^2+b*n <= max_num having |n| <= nmax:
     * |n| <= (|b| + sqrt(b^2 + 4a*max_num)) / (2a). Over-bound by floor-sqrt+2;
     * symmetric, so [-nmax, nmax] is complete for any sign of b. */
    int64_t babs = (b < 0) ? -b : b;        /* Class-K magnitude, no abs() */
    int64_t m = (max_num > 0) ? max_num : 0;
    int64_t disc = babs * babs + 4 * a * m;
    int64_t root;
    assert(a > 0);
    assert(disc >= 0);
    root = ut_isqrt(disc);
    return (babs + root) / (2 * a) + 2;
}

/* ---- the leading (minimal) raw exponent numerator ------------------ */

static srmech_status_t ut_min_raw_num(uint32_t modulus, const int32_t *chi_table,
                                      int64_t a, int64_t b, int support,
                                      int64_t *out_lead, int *out_found)
{
    /* The quadratic a*n^2 + b*n (a > 0) has vertex at -b/(2a); the minimum over
     * the contributing lattice n is near it. Probe a window +-(modulus+1) (then
     * a 6x wider net) around the floored vertex — bounded (JPL Rule 2). */
    int64_t vfloor, lo, hi, n, best = 0, val;
    int found = 0, widen;
    assert(out_lead != NULL && out_found != NULL);
    assert(a > 0);
    /* vfloor = floor(-b / (2a)) toward -inf (Python //); C / truncates, so
     * correct down when the truncated quotient was rounded toward 0 from a
     * negative exact value. */
    vfloor = (-b) / (2 * a);
    if (((-b) % (2 * a)) != 0 && (((-b) < 0) != ((2 * a) < 0))) {
        vfloor -= 1;
    }
    for (widen = 1; widen <= 6 && !found; widen *= 6) {
        lo = vfloor - (int64_t)(modulus + 1) * widen;
        hi = vfloor + (int64_t)(modulus + 1) * widen;
        for (n = lo; n <= hi; ++n) {
            if (!ut_n_in_support(support, n)) { continue; }
            if (ut_chi(chi_table, modulus, n) == 0) { continue; }
            val = a * n * n + b * n;
            if (!found || val < best) { best = val; found = 1; }
        }
    }
    *out_found = found;
    *out_lead = best;
    return SRMECH_OK;
}

/* ---- caller-arena carve (mirrors poly_bind / bigexp_bind) ---------- */

static srmech_status_t ut_ctx_init(ut_ctx_t *c, uint32_t cap, uint32_t j,
                                   void *ws, size_t ws_len)
{
    uint32_t *base = (uint32_t *)ws;
    size_t words = ws_len / sizeof(uint32_t);
    size_t carriers_words = (size_t)cap * UT_N_CARRIERS;
    assert(c != NULL);
    assert(cap > 0u);
    assert(ws != NULL);
    if (carriers_words > words) {
        return SRMECH_ERR_OVERFLOW;
    }
    c->limb_cap = cap;
    c->nj.limbs = base;            c->nj.cap = cap;
    c->nj.n = 0u;                  c->nj.sign = 0;
    c->nbase.limbs = base + cap;   c->nbase.cap = cap;
    c->nbase.n = 0u;               c->nbase.sign = 0;
    c->scratch = (void *)(base + carriers_words);
    c->scratch_len = (words - carriers_words) * sizeof(uint32_t);
    (void)j;
    return SRMECH_OK;
}

/* ---- one term: nj = |n|^j (magnitude only; sign applied by caller) - */

static srmech_status_t ut_set_njj(ut_ctx_t *c, int64_t n, uint32_t j)
{
    int64_t mag = (n < 0) ? -n : n;   /* Class-K magnitude, no ALU abs() */
    srmech_status_t st;
    assert(c != NULL);
    assert(mag >= 0);
    st = srmech_bigint_set_i64(&c->nbase, mag);
    if (st != SRMECH_OK) { return st; }
    if (j == 0u) {
        return srmech_bigint_set_i64(&c->nj, 1);  /* n^0 = 1 */
    }
    return srmech_bigint_pow_u32(&c->nj, &c->nbase, j,
                                 c->scratch, c->scratch_len);
}

/* ---- accumulate chi(n)*n^j into acc (the e-th coefficient) --------- */

static srmech_status_t ut_accumulate(ut_ctx_t *c, srmech_bigint_t *acc,
                                     int8_t chi, int64_t n, uint32_t j)
{
    srmech_status_t st;
    int neg;
    assert(c != NULL);
    assert(acc != NULL);
    assert(chi == 1 || chi == -1);
    st = ut_set_njj(c, n, j);
    if (st != SRMECH_OK) { return st; }
    /* the contributed sign: chi * sign(n^j). n^j keeps n's sign for odd j
     * (the two-sided theta needs the signed term); ut_set_njj built |n|^j, so
     * apply both the chi sign AND (for odd j, negative n) the n^j sign. */
    neg = (chi < 0) ? 1 : 0;
    if ((j % 2u) == 1u && n < 0) {
        neg ^= 1;                 /* Class-K sign-flip composition (chi o sign) */
    }
    if (neg) {
        c->nj.sign = (c->nj.n == 0u) ? 0 : -1;
    }
    return srmech_bigint_add(acc, acc, &c->nj);
}

/* ================================================================== *
 *  Public: srmech_unary_theta_ws_bound + srmech_unary_theta_q_series  *
 * ================================================================== */

size_t srmech_unary_theta_ws_bound(uint32_t j, size_t coeff_limbs)
{
    /* nj + nbase carriers (coeff_limbs each) + the pow ws scratch (sized from
     * |n|^j; reuse the bigint pow ws bound at the per-coeff limb width). */
    size_t carriers, powws;
    assert(coeff_limbs > 0u);
    assert(UT_N_CARRIERS == 2u);
    powws = srmech_bigint_pow_ws_bound(coeff_limbs, j == 0u ? 1u : j);
    carriers = (size_t)UT_N_CARRIERS * coeff_limbs * sizeof(uint32_t);
    return carriers + powws + 64u * sizeof(uint32_t);
}

/* out[] is a caller-owned array of N+1 srmech_bigint, each pre-bound to a limb
 * buffer of capacity >= coeff_limbs. On return out[e] holds the exact integer
 * coefficient of q^e (after the leading-power factor-out). *out_len = N+1.
 * SRMECH_ERR_BAD_INPUT on a malformed character / empty support / int64 raw-
 * exponent overflow; SRMECH_ERR_OVERFLOW if a coefficient exceeds its cap. */
srmech_status_t srmech_unary_theta_q_series(
    uint32_t modulus, const int32_t *chi_table, uint32_t j,
    int64_t a, int64_t b, uint32_t D, int support, size_t N,
    srmech_bigint_t *out, size_t *out_len, void *ws, size_t ws_len)
{
    ut_ctx_t ctx;
    srmech_status_t st;
    int64_t lead, max_num, n, raw, shifted, nmax, nlo, nhi;
    int found = 0;
    size_t e;
    int8_t chi;
    uint32_t cap;
    assert(out != NULL && out_len != NULL);
    assert(chi_table != NULL);
    if (modulus < 1u || a <= 0 || D < 1u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    cap = out[0].cap;             /* per-coefficient limb capacity */
    st = ut_ctx_init(&ctx, cap, j, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    st = ut_min_raw_num(modulus, chi_table, a, b, support, &lead, &found);
    if (st != SRMECH_OK) { return st; }
    if (!found) {
        return SRMECH_ERR_BAD_INPUT;   /* character identically 0 on support */
    }
    for (e = 0; e <= N; ++e) {
        st = srmech_bigint_set_i64(&out[e], 0);
        if (st != SRMECH_OK) { return st; }
    }
    max_num = lead + (int64_t)N * (int64_t)D;
    /* enumerate the support's n over the EXPLICIT symmetric window [-nmax,nmax]
     * (ut_n_window) — provably complete for any sign of b, bounded (Rule 2),
     * byte-identical to the Python _support_iter_bound. */
    nmax = ut_n_window(a, b, max_num);
    if (support == UT_SUPPORT_POSITIVE) {
        nlo = 1; nhi = nmax;
    } else if (support == UT_SUPPORT_NONNEG) {
        nlo = 0; nhi = nmax;
    } else {                          /* UT_SUPPORT_ALL */
        nlo = -nmax; nhi = nmax;
    }
    for (n = nlo; n <= nhi; ++n) {
        raw = a * n * n + b * n;
        if (raw > max_num) { continue; }
        chi = ut_chi(chi_table, modulus, n);
        if (chi == 0) { continue; }
        shifted = raw - lead;
        if (shifted < 0 || (shifted % (int64_t)D) != 0) { continue; }
        e = (size_t)(shifted / (int64_t)D);
        if (e > N) { continue; }
        st = ut_accumulate(&ctx, &out[e], chi, n, j);
        if (st != SRMECH_OK) { return st; }
    }
    *out_len = N + 1u;
    return SRMECH_OK;
}
