/*
 * srmech_harmonic_maass.c — the EXACT-INTEGER q-series of the HOLOMORPHIC mock
 * part of a HARMONIC (weak) MAASS form (the C peer of
 * srmech.amsc.harmonic_maass.HarmonicMaass / MockQSeries; the pair carrier that
 * makes research item #9 a finite exact object).
 *
 * A harmonic Maass form f of weight k is determined by the PAIR (f+ holomorphic
 * mock part, g = xi_k(f) shadow): the non-holomorphic completion f- is the
 * Eichler (period) integral of the shadow g, recoverable not stored
 * (Bruinier-Funke, "On Two Geometric Theta Lifts", arXiv:math/0212286v4, Prop.
 * 3.2, p. 10). The SHADOW q-series rides the existing srmech_unary_theta C peer;
 * the genuinely-NEW computation this op mirrors is the HOLOMORPHIC mock part's
 * q-series for the #9 keystone — Ramanujan's order-3 mock theta (Zagier,
 * Asterisque 326 (2009), Exp. 986, p. 145, Eulerian series)
 *
 *     f(q) = SUM_{n>=0} q^{n^2} / PROD_{j=1}^n (1 + q^j)^2 .
 *
 * This op returns the EXACT INTEGER coefficients out[e] (e = 0..N) of f(q) to
 * depth N (leading power 0), byte-identical to the Python pure body. Each out[e]
 * is a full srmech_bigint (no int64 ceiling). The series is built over exact
 * integer power-series algebra:
 *   - prod = PROD_{j=1}^n (1 + q^j)^2 truncated to degree N (an integer poly);
 *   - invp = 1/prod as an exact integer power series (prod[0] == 1, so the
 *     reciprocal is integral): invp[0] = 1, invp[m] = - SUM_{t=1}^m prod[t]*invp[m-t];
 *   - accumulate invp shifted up by n^2 into out[].
 * The n-loop is BOUNDED (n^2 <= N), the inner convolutions are bounded by N
 * (JPL Rule 2). Sign is the Class-K pin-slot (the subtraction in the reciprocal
 * recurrence), never an ALU abs().
 *
 * Carrier-internal, like srmech_poly.c / srmech_unary_theta.c: the working
 * power-series cell banks (prod, invp, factor, and the multiply/accumulate temps)
 * are carved from the caller arena `ws` (sized via
 * srmech_harmonic_maass_ws_bound), so the magnitude bound is the CALLER's RAM,
 * not a compiled-in cap. The out[] coefficient array is caller-owned. Additive
 * symbols -> ABI unchanged (stays 3).
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto/recursion): OK — iterative, flat helpers
 *   - Rule 2 (bounded loops)    : OK — bounds are N and the n^2<=N outer loop
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
#include <stddef.h>
#include <stdint.h>

/* A power-series cell bank: `len` srmech_bigint cells of `cap` limbs each, carved
 * contiguously from the caller arena. */
typedef struct hm_bank {
    srmech_bigint_t *cell;     /* len cells                           */
    size_t           len;      /* number of cells (= N + 1)           */
} hm_bank_t;

/* The working roster carved from the caller arena `ws`: three series banks
 * (prod, invp, factor) + two scratch cells (mul accumulator + one temp) + the
 * srmech_bigint divmod/pow scratch tail (unused here but kept for parity sizing). */
typedef struct hm_ctx {
    hm_bank_t       prod;      /* PROD_{j=1}^n (1+q^j)^2               */
    hm_bank_t       invp;      /* 1 / prod                            */
    hm_bank_t       factor;    /* the (1+q^j) running multiplicand     */
    srmech_bigint_t acc;       /* convolution accumulator             */
    srmech_bigint_t tmp;       /* one product temp (mul out)          */
    uint32_t        cap;       /* per-cell limb capacity              */
} hm_ctx_t;

/* ---- forward declarations (Rule 1: no recursion) ------------------- */

static srmech_status_t hm_ctx_init(hm_ctx_t *c, size_t N, uint32_t cap,
                                   void *ws, size_t ws_len);
static srmech_status_t hm_bank_zero(hm_bank_t *bank, size_t N);
static srmech_status_t hm_series_mul(hm_ctx_t *c, hm_bank_t *dst,
                                     const hm_bank_t *a, const hm_bank_t *b, size_t N);
static srmech_status_t hm_set_factor(hm_ctx_t *c, size_t j, size_t N);
static srmech_status_t hm_series_inv(hm_ctx_t *c, size_t N);
static srmech_status_t hm_build_prod(hm_ctx_t *c, size_t n, size_t N);
static srmech_status_t hm_accumulate_shift(hm_ctx_t *c, srmech_bigint_t *out,
                                           size_t shift, size_t N);

/* ---- zero a bank's first N+1 cells to the integer 0 ---------------- */

static srmech_status_t hm_bank_zero(hm_bank_t *bank, size_t N)
{
    size_t i;
    srmech_status_t st;
    assert(bank != NULL);
    assert(bank->len >= N + 1u);
    for (i = 0; i <= N; ++i) {
        st = srmech_bigint_set_i64(&bank->cell[i], 0);
        if (st != SRMECH_OK) {
            return st;
        }
    }
    return SRMECH_OK;
}

/* ---- carve the full working roster from `ws` ----------------------- */

static srmech_status_t hm_ctx_init(hm_ctx_t *c, size_t N, uint32_t cap,
                                   void *ws, size_t ws_len)
{
    /* Layout: a struct-cell block (3*(N+1)+2 srmech_bigint structs) then the limb
     * arena. We carve the struct cells first, bind each to a cap-limb run. */
    uint32_t *limbs;
    srmech_bigint_t *cells = (srmech_bigint_t *)ws;
    size_t n_cells = 3u * (N + 1u) + 2u;
    size_t cells_bytes = n_cells * sizeof(srmech_bigint_t);
    size_t i, words_left;
    assert(c != NULL);
    assert(ws != NULL);
    if (cap == 0u || cells_bytes >= ws_len) {
        return SRMECH_ERR_OVERFLOW;
    }
    limbs = (uint32_t *)(void *)((unsigned char *)ws + cells_bytes);
    words_left = (ws_len - cells_bytes) / sizeof(uint32_t);
    if (n_cells * (size_t)cap > words_left) {
        return SRMECH_ERR_OVERFLOW;
    }
    for (i = 0; i < n_cells; ++i) {
        cells[i].limbs = limbs + i * (size_t)cap;
        cells[i].cap = cap;
        cells[i].n = 0u;
        cells[i].sign = 0;
    }
    c->cap = cap;
    c->prod.cell = cells;                 c->prod.len = N + 1u;
    c->invp.cell = cells + (N + 1u);      c->invp.len = N + 1u;
    c->factor.cell = cells + 2u * (N + 1u); c->factor.len = N + 1u;
    c->acc = cells[3u * (N + 1u)];
    c->tmp = cells[3u * (N + 1u) + 1u];
    return SRMECH_OK;
}

/* ---- dst = a * b truncated to degree N (exact integer convolution) - */

static srmech_status_t hm_series_mul(hm_ctx_t *c, hm_bank_t *dst,
                                     const hm_bank_t *a, const hm_bank_t *b, size_t N)
{
    size_t e, i;
    srmech_status_t st;
    assert(c != NULL && dst != NULL);
    assert(a != NULL && b != NULL);
    for (e = 0; e <= N; ++e) {
        st = srmech_bigint_set_i64(&c->acc, 0);
        if (st != SRMECH_OK) { return st; }
        for (i = 0; i <= e; ++i) {
            if (srmech_bigint_is_zero(&a->cell[i])
                || srmech_bigint_is_zero(&b->cell[e - i])) {
                continue;
            }
            st = srmech_bigint_mul(&c->tmp, &a->cell[i], &b->cell[e - i]);
            if (st != SRMECH_OK) { return st; }
            st = srmech_bigint_add(&c->acc, &c->acc, &c->tmp);
            if (st != SRMECH_OK) { return st; }
        }
        st = srmech_bigint_copy(&dst->cell[e], &c->acc);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* ---- factor = (1 + q^j) truncated to degree N --------------------- */

static srmech_status_t hm_set_factor(hm_ctx_t *c, size_t j, size_t N)
{
    srmech_status_t st;
    assert(c != NULL);
    assert(j >= 1u);
    st = hm_bank_zero(&c->factor, N);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&c->factor.cell[0], 1);
    if (st != SRMECH_OK) { return st; }
    if (j <= N) {
        st = srmech_bigint_set_i64(&c->factor.cell[j], 1);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* ---- invp = 1 / prod (prod[0] == 1; exact integer power series) ---- */

static srmech_status_t hm_series_inv(hm_ctx_t *c, size_t N)
{
    size_t m, t;
    srmech_status_t st;
    assert(c != NULL);
    assert(!srmech_bigint_is_zero(&c->prod.cell[0]));
    st = hm_bank_zero(&c->invp, N);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&c->invp.cell[0], 1);
    if (st != SRMECH_OK) { return st; }
    for (m = 1; m <= N; ++m) {
        st = srmech_bigint_set_i64(&c->acc, 0);
        if (st != SRMECH_OK) { return st; }
        for (t = 1; t <= m; ++t) {
            if (srmech_bigint_is_zero(&c->prod.cell[t])) { continue; }
            st = srmech_bigint_mul(&c->tmp, &c->prod.cell[t], &c->invp.cell[m - t]);
            if (st != SRMECH_OK) { return st; }
            st = srmech_bigint_add(&c->acc, &c->acc, &c->tmp);
            if (st != SRMECH_OK) { return st; }
        }
        /* invp[m] = -acc — the Class-K sign-flip (subtract from 0), not abs(). */
        st = srmech_bigint_set_i64(&c->invp.cell[m], 0);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_sub(&c->invp.cell[m], &c->invp.cell[m], &c->acc);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* ---- prod = PROD_{j=1}^n (1 + q^j)^2 truncated to degree N --------- */

static srmech_status_t hm_build_prod(hm_ctx_t *c, size_t n, size_t N)
{
    size_t j, rep;
    srmech_status_t st;
    assert(c != NULL);
    assert(c->prod.len >= N + 1u);
    st = hm_bank_zero(&c->prod, N);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&c->prod.cell[0], 1);
    if (st != SRMECH_OK) { return st; }
    for (j = 1; j <= n; ++j) {
        st = hm_set_factor(c, j, N);
        if (st != SRMECH_OK) { return st; }
        for (rep = 0; rep < 2u; ++rep) {       /* (1+q^j) twice = squared */
            /* prod <- prod * factor (into invp as scratch, then copy back) */
            st = hm_series_mul(c, &c->invp, &c->prod, &c->factor, N);
            if (st != SRMECH_OK) { return st; }
            st = hm_bank_zero(&c->prod, N);
            if (st != SRMECH_OK) { return st; }
            { size_t e;
              for (e = 0; e <= N; ++e) {
                  st = srmech_bigint_copy(&c->prod.cell[e], &c->invp.cell[e]);
                  if (st != SRMECH_OK) { return st; }
              } }
        }
    }
    return SRMECH_OK;
}

/* ---- out[e] += invp[e - shift] (the q^{n^2} shift, accumulated) ---- */

static srmech_status_t hm_accumulate_shift(hm_ctx_t *c, srmech_bigint_t *out,
                                           size_t shift, size_t N)
{
    size_t e;
    srmech_status_t st;
    assert(c != NULL && out != NULL);
    assert(shift <= N);
    for (e = shift; e <= N; ++e) {
        if (srmech_bigint_is_zero(&c->invp.cell[e - shift])) { continue; }
        st = srmech_bigint_add(&out[e], &out[e], &c->invp.cell[e - shift]);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* ================================================================== *
 *  Public: srmech_harmonic_maass_ws_bound + srmech_harmonic_maass_hol *
 * ================================================================== */

size_t srmech_harmonic_maass_ws_bound(size_t N, size_t coeff_limbs)
{
    /* 3*(N+1)+2 srmech_bigint cells (struct headers) + their limb runs at
     * coeff_limbs each, plus generous slack for the mul/divmod temps. */
    size_t n_cells = 3u * (N + 1u) + 2u;
    size_t cells_bytes = n_cells * sizeof(srmech_bigint_t);
    size_t limbs_bytes = n_cells * coeff_limbs * sizeof(uint32_t);
    assert(coeff_limbs > 0u);
    assert(N + 1u > 0u);
    return cells_bytes + limbs_bytes + 256u * sizeof(uint32_t);
}

/* out[] is a caller-owned array of N+1 srmech_bigint, each pre-bound to a limb
 * buffer of capacity >= coeff_limbs. On return out[e] holds the exact integer
 * coefficient of q^e of Ramanujan's order-3 mock theta f(q) (leading power 0).
 * *out_len = N+1. SRMECH_ERR_OVERFLOW if a coefficient exceeds its cap or the
 * arena is too small. */
srmech_status_t srmech_harmonic_maass_hol_q_series(
    size_t N, srmech_bigint_t *out, size_t *out_len, void *ws, size_t ws_len)
{
    hm_ctx_t ctx;
    srmech_status_t st;
    size_t e, n;
    uint32_t cap;
    assert(out != NULL && out_len != NULL);
    assert(ws != NULL);
    cap = out[0].cap;
    st = hm_ctx_init(&ctx, N, cap, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    for (e = 0; e <= N; ++e) {
        st = srmech_bigint_set_i64(&out[e], 0);
        if (st != SRMECH_OK) { return st; }
    }
    /* f(q) = SUM_{n: n^2<=N} q^{n^2} / PROD_{j=1}^n (1+q^j)^2 */
    for (n = 0; n * n <= N; ++n) {
        st = hm_build_prod(&ctx, n, N);
        if (st != SRMECH_OK) { return st; }
        st = hm_series_inv(&ctx, N);
        if (st != SRMECH_OK) { return st; }
        st = hm_accumulate_shift(&ctx, out, n * n, N);
        if (st != SRMECH_OK) { return st; }
    }
    *out_len = N + 1u;
    return SRMECH_OK;
}
