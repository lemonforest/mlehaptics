/*
 * srmech_eta_quotient.c — the EXACT-INTEGER q-series of a DEDEKIND-ETA QUOTIENT
 * (the C peer of srmech.amsc.eta_quotient.EtaQuotient; a WEIGHT-axis operand
 * carrier).
 *
 * A Dedekind-eta quotient is
 *
 *     Q(tau) = PROD_{d | N} eta(d tau)^{r_d}
 *            = q^{(SUM_d d r_d)/24} * PROD_d PROD_{m>=1} (1 - q^{dm})^{r_d}
 *
 * with the Dedekind eta(tau) = q^{1/24} PROD_{m>=1}(1 - q^m). This op computes the
 * EXACT INTEGER power series PROD_d PROD_{m>=1}(1 - q^{dm})^{r_d} (the part AFTER
 * factoring out the leading fractional q-power q^{(SUM_d d r_d)/24}), i.e. the
 * coefficients out[0..n_terms-1] of SUM_e c_e q^e. Each out[e] is a full
 * srmech_bigint (no int64 ceiling: the coefficients GROW -- e.g. the Ramanujan
 * tau -- so the magnitude has no compiled-in cap) and is byte-identical to the
 * Python srmech.amsc.eta_quotient.EtaQuotient q-series.
 *
 * Anchors (the build gates):
 *   eta^24 = Delta : ds={1}, rs={24}        -> [1,-24,252,-1472,4830,-6048,-16744,..]
 *                    (Ramanujan tau(1..7); the weight-12 cusp form on Gamma(1))
 *   X0(11) newform : ds={1,11}, rs={2,2}    -> [1,-2,-1,2,1,2,-2,..]
 *                    (eta(tau)^2 eta(11 tau)^2; the weight-2 level-11 newform)
 *
 * The product is built factor by factor over the bigint coefficient array out[]:
 *   r_d > 0 : multiply by (1 - q^e), |r_d| times -- a BACKWARD subtract-shift
 *             out[i] -= out[i - e]  for i = n_terms-1 .. e
 *   r_d < 0 : divide by (1 - q^e), |r_d| times -- a FORWARD add-shift (the
 *             geometric 1/(1 - q^e) expansion) out[i] += out[i - e]  for i = e .. n_terms-1
 * The sign of r_d chooses which (the Class-K sign branch), never an ALU abs().
 * Only bigint add / sub are used -- no pow, no mul, no divmod -- so the only
 * working storage is ONE scratch bigint (the shifted operand out[i-e]); it is
 * carved from the caller arena `ws` (sized via srmech_eta_quotient_ws_bound), so
 * the magnitude bound is the CALLER's RAM, not a compiled-in cap. out[] is
 * caller-owned. Additive symbols -> ABI unchanged (stays 3).
 *
 * Carrier-internal, like srmech_poly.c / srmech_unary_theta.c: NOT a Rosetta
 * ledger op. The Ligozat / order-at-cusp DECISION logic stays Python-only (the
 * carrier precedent: the q-series expansion is the compute kernel that needs the
 * C peer; the modularity decision is exact-integer congruence bookkeeping in
 * Python).
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto/recursion): OK — iterative, flat helpers
 *   - Rule 2 (bounded loops)    : OK — bounds are n_terms, n_factors, |r_d|, m
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

/* ---- forward declarations (Rule 1: no recursion) ------------------- */

static srmech_status_t eq_mul_one_minus(srmech_bigint_t *out, size_t n_terms,
                                        size_t e, srmech_bigint_t *scratch);
static srmech_status_t eq_div_one_minus(srmech_bigint_t *out, size_t n_terms,
                                        size_t e, srmech_bigint_t *scratch);
static srmech_status_t eq_apply_factor(srmech_bigint_t *out, size_t n_terms,
                                       int64_t d, int64_t r,
                                       srmech_bigint_t *scratch);

/* ---- one multiply by (1 - q^e): out[i] -= out[i - e], backward ----- */

static srmech_status_t eq_mul_one_minus(srmech_bigint_t *out, size_t n_terms,
                                        size_t e, srmech_bigint_t *scratch)
{
    size_t i;
    srmech_status_t st;
    assert(out != NULL && scratch != NULL);
    assert(e >= 1u);
    /* backward so out[i - e] is still the OLD coefficient when read */
    for (i = n_terms; i > e; --i) {
        st = srmech_bigint_copy(scratch, &out[i - 1u - e]);  /* old out[(i-1)-e] */
        if (st != SRMECH_OK) {
            return st;
        }
        st = srmech_bigint_sub(&out[i - 1u], &out[i - 1u], scratch);
        if (st != SRMECH_OK) {
            return st;
        }
    }
    return SRMECH_OK;
}

/* ---- one divide by (1 - q^e): out[i] += out[i - e], forward -------- */

static srmech_status_t eq_div_one_minus(srmech_bigint_t *out, size_t n_terms,
                                        size_t e, srmech_bigint_t *scratch)
{
    size_t i;
    srmech_status_t st;
    assert(out != NULL && scratch != NULL);
    assert(e >= 1u);
    /* forward so out[i - e] is the ALREADY-updated coefficient (geometric series) */
    for (i = e; i < n_terms; ++i) {
        st = srmech_bigint_copy(scratch, &out[i - e]);
        if (st != SRMECH_OK) {
            return st;
        }
        st = srmech_bigint_add(&out[i], &out[i], scratch);
        if (st != SRMECH_OK) {
            return st;
        }
    }
    return SRMECH_OK;
}

/* ---- apply one eta factor eta(d tau)^r to the running product ------ */

static srmech_status_t eq_apply_factor(srmech_bigint_t *out, size_t n_terms,
                                       int64_t d, int64_t r,
                                       srmech_bigint_t *scratch)
{
    int64_t m, e, k, times;
    srmech_status_t st;
    assert(out != NULL && scratch != NULL);
    assert(d >= 1 && r != 0);
    /* the Class-K sign branch: r>0 multiplies by (1-q^{dm}), r<0 divides */
    times = (r >= 0) ? r : -r;        /* Class-K magnitude, no ALU abs() */
    for (m = 1; d * m < (int64_t)n_terms; ++m) {
        e = d * m;
        for (k = 0; k < times; ++k) {
            if (r > 0) {
                st = eq_mul_one_minus(out, n_terms, (size_t)e, scratch);
            } else {
                st = eq_div_one_minus(out, n_terms, (size_t)e, scratch);
            }
            if (st != SRMECH_OK) {
                return st;
            }
        }
    }
    return SRMECH_OK;
}

/* ================================================================== *
 *  Public: srmech_eta_quotient_ws_bound + srmech_eta_quotient_qseries *
 * ================================================================== */

/* Minimum `ws_len` BYTES for srmech_eta_quotient_qseries: ONE scratch bigint at
 * `coeff_limbs` width (the only working storage — every step is a bigint add/sub
 * on a copied coefficient) plus slack. coeff_limbs is the per-coefficient limb
 * capacity the caller sized out[] to. */
size_t srmech_eta_quotient_ws_bound(size_t coeff_limbs)
{
    size_t cl = (coeff_limbs > 0u) ? coeff_limbs : 1u;
    assert(coeff_limbs > 0u);
    assert(cl >= 1u);
    return (cl + 64u) * sizeof(uint32_t);
}

/* The exact integer q-series of PROD_d PROD_{m>=1}(1 - q^{dm})^{r_d}:
 * out[e] (e = 0..n_terms-1) <- the coefficient of q^e (after the leading-power
 * factor-out), *out_len <- n_terms. ds[i] (the eta-argument multiplier, >=1) and
 * rs[i] (the exponent, != 0) are the n_factors factors (i = 0..n_factors-1);
 * out[] is a caller-owned array of n_terms srmech_bigint, each pre-bound to a
 * limb buffer of capacity >= coeff_limbs. SRMECH_ERR_BAD_INPUT on n_terms<1 /
 * n_factors<1 / a bad d or r / a NULL pointer; SRMECH_ERR_OVERFLOW if a
 * coefficient (or the scratch) exceeds its cap. */
srmech_status_t srmech_eta_quotient_qseries(
    const int64_t *ds, const int64_t *rs, size_t n_factors, size_t n_terms,
    srmech_bigint_t *out, size_t *out_len, void *ws, size_t ws_len)
{
    srmech_bigint_t scratch;
    size_t i, words, need;
    srmech_status_t st;
    assert(out != NULL && out_len != NULL);
    assert(ds != NULL && rs != NULL);
    if (n_terms < 1u || n_factors < 1u || ws == NULL) {
        return SRMECH_ERR_BAD_INPUT;
    }
    /* bind the single scratch bigint into the caller arena */
    words = ws_len / sizeof(uint32_t);
    need = out[0].cap;                 /* one scratch at the per-coeff width */
    if (words < need || need < 1u) {
        return SRMECH_ERR_OVERFLOW;
    }
    scratch.limbs = (uint32_t *)ws;
    scratch.cap = (uint32_t)need;
    scratch.n = 0u;
    scratch.sign = 0;
    /* seed the running product = 1 (out[0]=1, rest 0) */
    for (i = 0u; i < n_terms; ++i) {
        st = srmech_bigint_set_i64(&out[i], (i == 0u) ? 1 : 0);
        if (st != SRMECH_OK) {
            return st;
        }
    }
    for (i = 0u; i < n_factors; ++i) {
        if (ds[i] < 1 || rs[i] == 0) {
            return SRMECH_ERR_BAD_INPUT;
        }
        st = eq_apply_factor(out, n_terms, ds[i], rs[i], &scratch);
        if (st != SRMECH_OK) {
            return st;
        }
    }
    *out_len = n_terms;
    return SRMECH_OK;
}
