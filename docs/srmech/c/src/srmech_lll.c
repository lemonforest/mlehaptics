/*
 * srmech_lll.c — EXACT-ℚ LLL lattice-basis reduction (the C peer of
 * srmech.amsc.cascade.matrix_cascades.lll_reduce). Classic Lenstra–Lenstra–
 * Lovász (1982): an integer lattice basis → a reduced basis of the SAME lattice
 * (unimodular change of basis, det = ±1), size-reduced (|μ_{k,j}| ≤ 1/2) and
 * Lovász-satisfying (‖b*_k‖² ≥ (δ − μ²_{k,k−1})·‖b*_{k−1}‖²).
 *
 * The engine is EXACT throughout — the Gram–Schmidt μ_{i,j} and ‖b*_i‖² are
 * carried as num/den srmech_bigint rationals (NO malloc, JPL Rule 3; NO float,
 * NO libm), the size-reduction round is the exact integer floor((2a+b)/(2b))
 * (the |μ| ≤ 1/2 guard a Class-K sign branch on 2·|num| vs den — never an ALU
 * abs), and the Lovász swap decides on the exact ℚ inequality. The GSO is
 * recomputed from the CURRENT integer basis at the top of each outer step (a
 * pure function of the integer basis), so the whole computation is a pure
 * function of (basis, δ) → byte-identical to the Python pure body, which is the
 * complete no-native fallback AND the parity oracle. Integer-in, integer-out;
 * rotation-last-trivial (no projection).
 *
 * ARENA SOUNDNESS. Every working carrier — the integer basis copy, the μ matrix,
 * the ‖b*‖² vector, the scalar Q carriers, the gcd/divmod scratch tail — is
 * carved from the caller arena `ws` (>= srmech_lll_reduce_ws_bound). The GSO
 * B_i / μ_{i,j} are ratios of Gram sub-determinants (integer minors), so their
 * limb count is dominated by the per-entry cap (a determinant-Hadamard
 * envelope, 6·m·coeff_limbs + slack); any residual overflow returns
 * SRMECH_ERR_OVERFLOW (never a silent wrap) and the Python falls back to its
 * byte-identical pure body — the standalone-complete honor holds.
 *
 * Termination: each Lovász swap strictly decreases the positive-integer
 * potential D = Π_i d_i (d_i = the i×i leading Gram determinant), so the swap
 * count ≤ log₂(D₀); the outer loop is bounded by a generous multiple of that.
 *
 * Class L (the lattice / Gram–Schmidt spectral content) ∘ Class K (the
 * size-reduction sign pin-slots + the swap-sign boundary — never an ALU abs) ∘
 * Class N (the exact nearest-integer rational rounding) ∘ Class I (the ordered
 * integer vector row operations).
 *
 * Additive symbols -> SRMECH_ABI_VERSION unchanged (stays 4).
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto/recursion): OK — iterative, flat helpers
 *   - Rule 2 (bounded loops)    : OK — bounds are m/n counts + the swap potential
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

/* Scalar working carriers carved from the arena (mirrors qmat_ctx). */
typedef struct lll_ctx {
    srmech_bigint_t qr_n, qr_d;   /* general Q result (mul/add/div output) */
    srmech_bigint_t qs_n, qs_d;   /* the running Gram–Schmidt s            */
    srmech_bigint_t qt_n, qt_d;   /* Q temp product (μ·μ)                  */
    srmech_bigint_t qu_n, qu_d;   /* Q temp product (·B / the subtrahend)  */
    srmech_bigint_t qv_n, qv_d;   /* Q temp (Lovász rhs / δ−μ²)            */
    srmech_bigint_t iacc, iacc2;  /* integer dot-product accumulator       */
    srmech_bigint_t iprod;        /* integer product term                  */
    srmech_bigint_t ir0, ir1;     /* integer round/compare scratch         */
    srmech_bigint_t ir2, ir3;     /* integer round/compare scratch         */
    srmech_bigint_t qq;           /* the size-reduction quotient q (int)   */
    srmech_bigint_t addt;         /* q_addsub cross-product temp           */
    srmech_bigint_t g, rem;       /* reduce-private gcd / divmod sinks      */
    srmech_bigint_t rs0, rs1;     /* reduce-private quotient scratch        */
    srmech_bigint_t z1;           /* read-only 1                           */
    uint32_t limb_cap;            /* per-carrier limb capacity             */
    void  *scratch;               /* gcd/divmod scratch arena tail         */
    size_t scratch_len;           /* its length in BYTES                   */
} lll_ctx_t;

#define LLL_N_CARRIERS 24u

/* ---- caller-arena bump carve (mirrors qmat_take / fac_take) -------- */

static uint32_t *lll_take(uint32_t *base, size_t words, size_t *cur, size_t count)
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

static srmech_status_t lll_bind(srmech_bigint_t *b, uint32_t *base, size_t words,
                                size_t *cur, uint32_t cap)
{
    uint32_t *limbs = lll_take(base, words, cur, cap);
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

/* Carve `count` bigint headers + `cap`-limb runs (each the integer 0). NULL on
 * exhaustion. Mirrors fac_carve_bigints. */
static srmech_bigint_t *lll_carve_bigints(uint32_t *base, size_t words,
                                          size_t *cur, size_t count, uint32_t cap)
{
    srmech_bigint_t *arr;
    size_t hw = (sizeof(srmech_bigint_t) + sizeof(uint32_t) - 1u) / sizeof(uint32_t);
    size_t k;
    assert(base != NULL && cur != NULL);
    assert(cap > 0u && count > 0u);
    arr = (srmech_bigint_t *)lll_take(base, words, cur, hw * count);
    if (arr == NULL) {
        return NULL;
    }
    for (k = 0u; k < count; k++) {
        if (lll_bind(&arr[k], base, words, cur, cap) != SRMECH_OK) {
            return NULL;
        }
    }
    return arr;
}

static srmech_status_t lll_ctx_init(lll_ctx_t *c, uint32_t *base, size_t words,
                                    size_t *cur, uint32_t cap)
{
    srmech_bigint_t *slots = &c->qr_n;   /* the 24 fields are a contiguous run */
    size_t k;
    srmech_status_t st;
    assert(c != NULL && base != NULL);
    assert(cap > 0u);
    c->limb_cap = cap;
    for (k = 0u; k < LLL_N_CARRIERS; k++) {
        st = lll_bind(&slots[k], base, words, cur, cap);
        if (st != SRMECH_OK) {
            return st;
        }
    }
    st = srmech_bigint_set_i64(&c->z1, 1);
    if (st != SRMECH_OK) {
        return st;
    }
    c->scratch = (void *)(base + *cur);
    c->scratch_len = (words - *cur) * sizeof(uint32_t);
    return SRMECH_OK;
}

/* ---- exact-Q helpers (reduce / add-sub / mul / div) --------------- */

static srmech_status_t lll_q_reduce(lll_ctx_t *c, srmech_bigint_t *num,
                                    srmech_bigint_t *den)
{
    srmech_status_t st;
    assert(c != NULL && num != NULL && den != NULL);
    assert(den->sign != 0);
    if (den->sign < 0) {                          /* force positive denominator */
        num->sign = (num->sign == 0) ? 0 : -num->sign;
        den->sign = -den->sign;
    }
    if (srmech_bigint_is_zero(num)) {
        return srmech_bigint_set_i64(den, 1);
    }
    st = srmech_bigint_gcd(&c->g, num, den, c->scratch, c->scratch_len);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_divmod(&c->rs0, &c->rem, num, &c->g, c->scratch, c->scratch_len);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_divmod(&c->rs1, &c->rem, den, &c->g, c->scratch, c->scratch_len);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(num, &c->rs0);
    if (st != SRMECH_OK) { return st; }
    return srmech_bigint_copy(den, &c->rs1);
}

/* out = a +/- b (exact Q), reduced. sub != 0 selects subtraction. out_* may NOT
 * alias the four input carriers. Uses c->addt (cross product). Mirrors qmat_q_add. */
static srmech_status_t lll_q_addsub(lll_ctx_t *c, srmech_bigint_t *on,
                                    srmech_bigint_t *od, const srmech_bigint_t *an,
                                    const srmech_bigint_t *ad, const srmech_bigint_t *bn,
                                    const srmech_bigint_t *bd, int sub)
{
    srmech_status_t st;
    assert(c != NULL && on != NULL && od != NULL);
    assert(an != NULL && ad != NULL && bn != NULL && bd != NULL);
    st = srmech_bigint_mul(&c->addt, an, bd);         /* addt = an*bd     */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_mul(on, bn, ad);               /* on = bn*ad       */
    if (st != SRMECH_OK) { return st; }
    if (sub) {
        st = srmech_bigint_sub(od, &c->addt, on);     /* od = an*bd-bn*ad */
    } else {
        st = srmech_bigint_add(od, &c->addt, on);     /* od = an*bd+bn*ad */
    }
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(on, od);                  /* on = combined num */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_mul(od, ad, bd);               /* od = ad*bd        */
    if (st != SRMECH_OK) { return st; }
    return lll_q_reduce(c, on, od);
}

/* out = a * b (exact Q), reduced. out_* may NOT alias the inputs. */
static srmech_status_t lll_q_mul(lll_ctx_t *c, srmech_bigint_t *on,
                                 srmech_bigint_t *od, const srmech_bigint_t *an,
                                 const srmech_bigint_t *ad, const srmech_bigint_t *bn,
                                 const srmech_bigint_t *bd)
{
    srmech_status_t st;
    assert(c != NULL && on != NULL && od != NULL);
    assert(an != NULL && ad != NULL && bn != NULL && bd != NULL);
    st = srmech_bigint_mul(on, an, bn);               /* num = an*bn */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_mul(od, ad, bd);               /* den = ad*bd */
    if (st != SRMECH_OK) { return st; }
    return lll_q_reduce(c, on, od);
}

/* out = a / b (exact Q), reduced. bn != 0 (else BAD_INPUT). out_* not alias in. */
static srmech_status_t lll_q_div(lll_ctx_t *c, srmech_bigint_t *on,
                                 srmech_bigint_t *od, const srmech_bigint_t *an,
                                 const srmech_bigint_t *ad, const srmech_bigint_t *bn,
                                 const srmech_bigint_t *bd)
{
    srmech_status_t st;
    assert(c != NULL && on != NULL && od != NULL);
    assert(an != NULL && ad != NULL && bn != NULL && bd != NULL);
    if (srmech_bigint_is_zero(bn)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    st = srmech_bigint_mul(on, an, bd);               /* num = an*bd */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_mul(od, ad, bn);               /* den = ad*bn */
    if (st != SRMECH_OK) { return st; }
    return lll_q_reduce(c, on, od);                   /* reduce fixes den sign */
}

/* ---- integer dot product of basis rows i, j -> out --------------- */

static srmech_status_t lll_dot(lll_ctx_t *c, const srmech_bigint_t *b, int n,
                               int i, int j, srmech_bigint_t *out)
{
    srmech_status_t st;
    int t;
    assert(c != NULL && b != NULL && out != NULL);
    assert(i >= 0 && j >= 0 && n >= 0);
    st = srmech_bigint_set_i64(&c->iacc, 0);
    if (st != SRMECH_OK) { return st; }
    for (t = 0; t < n; t++) {
        st = srmech_bigint_mul(&c->iprod, &b[(size_t)i * (size_t)n + (size_t)t],
                               &b[(size_t)j * (size_t)n + (size_t)t]);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_add(&c->iacc2, &c->iacc, &c->iprod);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_copy(&c->iacc, &c->iacc2);
        if (st != SRMECH_OK) { return st; }
    }
    return srmech_bigint_copy(out, &c->iacc);
}

/* ---- one Gram–Schmidt s = <b_i, b_rowj> - Σ_{k<jj} μ[rowj][k]·μ[i][k]·B[k] --
 * written into c->qs (num/den). Used for μ_{i,j} (rowj=j, jj=j) and B_i
 * (rowj=i, jj=i). m = the μ-matrix stride (row length). */
static srmech_status_t lll_gso_s(lll_ctx_t *c, const srmech_bigint_t *b, int n,
                                 const srmech_bigint_t *mn, const srmech_bigint_t *md,
                                 const srmech_bigint_t *bn, const srmech_bigint_t *bd,
                                 int m, int i, int rowj, int jj)
{
    srmech_status_t st;
    int k;
    assert(c != NULL && b != NULL && mn != NULL);
    assert(md != NULL && bn != NULL && bd != NULL);
    st = lll_dot(c, b, n, i, rowj, &c->qs_n);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&c->qs_d, 1);
    if (st != SRMECH_OK) { return st; }
    for (k = 0; k < jj; k++) {
        size_t a = (size_t)rowj * (size_t)m + (size_t)k;
        size_t d = (size_t)i * (size_t)m + (size_t)k;
        st = lll_q_mul(c, &c->qt_n, &c->qt_d, &mn[a], &md[a], &mn[d], &md[d]);
        if (st != SRMECH_OK) { return st; }
        st = lll_q_mul(c, &c->qu_n, &c->qu_d, &c->qt_n, &c->qt_d, &bn[k], &bd[k]);
        if (st != SRMECH_OK) { return st; }
        st = lll_q_addsub(c, &c->qr_n, &c->qr_d, &c->qs_n, &c->qs_d,
                          &c->qu_n, &c->qu_d, 1);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_copy(&c->qs_n, &c->qr_n);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_copy(&c->qs_d, &c->qr_d);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* ---- full GSO: fill μ (m*m, num/den) + B (m, num/den) from the basis ---- */

static srmech_status_t lll_gso(lll_ctx_t *c, const srmech_bigint_t *b, int m, int n,
                               srmech_bigint_t *mn, srmech_bigint_t *md,
                               srmech_bigint_t *bn, srmech_bigint_t *bd)
{
    srmech_status_t st;
    int i, j;
    assert(c != NULL && b != NULL && mn != NULL);
    assert(bn != NULL && bd != NULL && m >= 0);
    for (i = 0; i < m; i++) {
        for (j = 0; j < i; j++) {
            size_t e = (size_t)i * (size_t)m + (size_t)j;
            st = lll_gso_s(c, b, n, mn, md, bn, bd, m, i, j, j);
            if (st != SRMECH_OK) { return st; }
            if (srmech_bigint_is_zero(&bn[j])) {
                return SRMECH_ERR_BAD_INPUT;    /* degenerate: ‖b*_j‖² = 0 */
            }
            st = lll_q_div(c, &mn[e], &md[e], &c->qs_n, &c->qs_d, &bn[j], &bd[j]);
            if (st != SRMECH_OK) { return st; }
        }
        st = lll_gso_s(c, b, n, mn, md, bn, bd, m, i, i, i);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_copy(&bn[i], &c->qs_n);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_copy(&bd[i], &c->qs_d);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* ---- size-reduction round + the RED(k,l) step -------------------- */

/* 1 iff |μ[k][l]| <= 1/2, i.e. 2·|num| <= den (Class-K sign branch; never abs).
 * *out set accordingly; returns status (the shl can overflow the scratch). */
static srmech_status_t lll_size_reduced(lll_ctx_t *c, const srmech_bigint_t *mn,
                                        const srmech_bigint_t *md, size_t e, int *out)
{
    srmech_status_t st;
    assert(c != NULL && mn != NULL && out != NULL);
    assert(md != NULL);
    st = srmech_bigint_copy(&c->ir0, &mn[e]);         /* ir0 = num       */
    if (st != SRMECH_OK) { return st; }
    if (c->ir0.sign < 0) { c->ir0.sign = -c->ir0.sign; }   /* |num|      */
    st = srmech_bigint_shl_bits(&c->ir1, &c->ir0, 1u);     /* 2·|num|    */
    if (st != SRMECH_OK) { return st; }
    *out = (srmech_bigint_cmp(&c->ir1, &md[e]) <= 0) ? 1 : 0;
    return SRMECH_OK;
}

/* c->qq <- round(μ[k][l]) = floor((2·num + den)/(2·den)), exact integer. */
static srmech_status_t lll_round(lll_ctx_t *c, const srmech_bigint_t *mn,
                                 const srmech_bigint_t *md, size_t e)
{
    srmech_status_t st;
    assert(c != NULL && mn != NULL && md != NULL);
    assert(md[e].sign > 0);
    st = srmech_bigint_shl_bits(&c->ir0, &mn[e], 1u);      /* 2·num          */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_add(&c->ir1, &c->ir0, &md[e]);      /* 2·num + den    */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_shl_bits(&c->ir2, &md[e], 1u);      /* 2·den          */
    if (st != SRMECH_OK) { return st; }
    return srmech_bigint_divmod(&c->qq, &c->ir3, &c->ir1, &c->ir2,
                                c->scratch, c->scratch_len);   /* floor div  */
}

/* b[k] -= q·b[l] over the integer row (n entries), q = c->qq. */
static srmech_status_t lll_row_axpy(lll_ctx_t *c, srmech_bigint_t *b, int n,
                                    int k, int l)
{
    srmech_status_t st;
    int t;
    assert(c != NULL && b != NULL);
    assert(k >= 0 && l >= 0 && n >= 0);
    for (t = 0; t < n; t++) {
        size_t ki = (size_t)k * (size_t)n + (size_t)t;
        size_t li = (size_t)l * (size_t)n + (size_t)t;
        st = srmech_bigint_mul(&c->iprod, &c->qq, &b[li]);   /* q·b[l][t]   */
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_sub(&c->iacc, &b[ki], &c->iprod); /* b[k]-q·b[l] */
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_copy(&b[ki], &c->iacc);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* RED(k,l): if |μ[k][l]| > 1/2, subtract round(μ[k][l])·b[l] from b[k] and update
 * the μ row (μ[k][l] -= q; μ[k][i] -= q·μ[l][i] for i < l). */
static srmech_status_t lll_red(lll_ctx_t *c, srmech_bigint_t *b, int n,
                               srmech_bigint_t *mn, srmech_bigint_t *md,
                               int m, int k, int l)
{
    srmech_status_t st;
    int reduced = 0, i;
    size_t e = (size_t)k * (size_t)m + (size_t)l;
    assert(c != NULL && b != NULL && mn != NULL);
    assert(k >= 1 && l >= 0 && l < k);
    st = lll_size_reduced(c, mn, md, e, &reduced);
    if (st != SRMECH_OK) { return st; }
    if (reduced) { return SRMECH_OK; }
    st = lll_round(c, mn, md, e);
    if (st != SRMECH_OK) { return st; }
    st = lll_row_axpy(c, b, n, k, l);
    if (st != SRMECH_OK) { return st; }
    st = lll_q_addsub(c, &c->qr_n, &c->qr_d, &mn[e], &md[e], &c->qq, &c->z1, 1);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&mn[e], &c->qr_n);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&md[e], &c->qr_d);
    if (st != SRMECH_OK) { return st; }
    for (i = 0; i < l; i++) {
        size_t ek = (size_t)k * (size_t)m + (size_t)i;
        size_t el = (size_t)l * (size_t)m + (size_t)i;
        st = lll_q_mul(c, &c->qt_n, &c->qt_d, &c->qq, &c->z1, &mn[el], &md[el]);
        if (st != SRMECH_OK) { return st; }
        st = lll_q_addsub(c, &c->qr_n, &c->qr_d, &mn[ek], &md[ek],
                          &c->qt_n, &c->qt_d, 1);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_copy(&mn[ek], &c->qr_n);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_copy(&md[ek], &c->qr_d);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* ---- Lovász test: 1 iff B[k] >= (δ − μ²[k][k−1])·B[k−1] ---------- */

static srmech_status_t lll_lovasz_ok(lll_ctx_t *c, const srmech_bigint_t *mn,
                                     const srmech_bigint_t *md,
                                     const srmech_bigint_t *bn,
                                     const srmech_bigint_t *bd, int m, int k,
                                     int32_t dn, int32_t dd, int *out)
{
    srmech_status_t st;
    size_t e = (size_t)k * (size_t)m + (size_t)(k - 1);
    assert(c != NULL && mn != NULL && out != NULL);
    assert(k >= 1 && bn != NULL);
    st = lll_q_mul(c, &c->qt_n, &c->qt_d, &mn[e], &md[e], &mn[e], &md[e]);  /* μ² */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&c->qu_n, (int64_t)dn);       /* δ = dn/dd */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&c->qu_d, (int64_t)dd);
    if (st != SRMECH_OK) { return st; }
    st = lll_q_addsub(c, &c->qv_n, &c->qv_d, &c->qu_n, &c->qu_d,
                      &c->qt_n, &c->qt_d, 1);                 /* δ − μ² */
    if (st != SRMECH_OK) { return st; }
    st = lll_q_mul(c, &c->qr_n, &c->qr_d, &c->qv_n, &c->qv_d,
                   &bn[k - 1], &bd[k - 1]);                   /* ·B[k−1] = rhs */
    if (st != SRMECH_OK) { return st; }
    /* B[k]/Bd[k] >= rhs_n/rhs_d (dens>0)  ⟺  B[k]·rhs_d >= rhs_n·Bd[k] */
    st = srmech_bigint_mul(&c->ir0, &bn[k], &c->qr_d);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_mul(&c->ir1, &c->qr_n, &bd[k]);
    if (st != SRMECH_OK) { return st; }
    *out = (srmech_bigint_cmp(&c->ir0, &c->ir1) >= 0) ? 1 : 0;
    return SRMECH_OK;
}

/* ---- arena bounds ------------------------------------------------- */

/* Exact magnitude bit length of a bigint — matches Python int.bit_length
 * (0 -> 0), so the C-side maxbits equals the Python-side maxbits and the caller
 * arena / out cap sized by srmech_lll_reduce_ws_bound / _entry_cap agree exactly
 * with the cap this op carves internally (no under-sizing overflow). */
static size_t lll_bigint_bits(const srmech_bigint_t *a)
{
    uint32_t top;
    size_t bits;
    assert(a != NULL);
    assert(a->n == 0u || a->limbs != NULL);
    if (a->n == 0u) {
        return 0u;
    }
    top = a->limbs[a->n - 1u];
    bits = (size_t)(a->n - 1u) * 32u;
    while (top != 0u) {
        bits++;
        top >>= 1;
    }
    return bits;
}

static size_t lll_coeff_limbs(int maxbits)
{
    size_t mb = (maxbits > 0) ? (size_t)maxbits : 1u;
    assert(mb >= 1u);
    assert(mb / 32u + 2u >= 2u);
    return mb / 32u + 2u;
}

static size_t lll_cap_for(int m, int n, int maxbits)
{
    size_t cl = lll_coeff_limbs(maxbits);
    size_t mm = (m > 0) ? (size_t)m : 1u;
    size_t nn = (n > 0) ? (size_t)n : 1u;
    size_t cap = 6u * mm * cl + 2u * nn + 64u;
    assert(mm >= 1u && nn >= 1u);
    assert(cap >= cl);
    return cap;
}

size_t srmech_lll_reduce_entry_cap(int m, int n, int maxbits)
{
    size_t cap = lll_cap_for(m, n, maxbits);
    assert(cap >= 64u);
    assert(cap >= lll_coeff_limbs(maxbits));
    return cap;
}

size_t srmech_lll_reduce_ws_bound(int m, int n, int maxbits)
{
    size_t cap = lll_cap_for(m, n, maxbits);
    size_t mm = (m > 0) ? (size_t)m : 1u;
    size_t nn = (n > 0) ? (size_t)n : 1u;
    size_t hw = (sizeof(srmech_bigint_t) + sizeof(uint32_t) - 1u) / sizeof(uint32_t);
    size_t n_big = mm * nn + 2u * mm * mm + 2u * mm + (size_t)LLL_N_CARRIERS;
    size_t headers = hw * (n_big + 8u);
    size_t limbs = cap * (n_big + 8u);
    size_t scratch = cap * 8u + 512u;
    size_t words = headers + limbs + scratch + 64u;
    assert(words >= limbs);
    assert(cap >= 2u);
    return words * sizeof(uint32_t);
}

/* ---- the reduction ----------------------------------------------- */

/* Copy the m*n input basis into the working (or out) integer matrix. */
static srmech_status_t lll_copy_matrix(srmech_bigint_t *dst,
                                       const srmech_bigint_t *src, size_t count)
{
    size_t idx;
    srmech_status_t st;
    assert(dst != NULL || count == 0u);
    assert(src != NULL || count == 0u);
    for (idx = 0u; idx < count; idx++) {
        st = srmech_bigint_copy(&dst[idx], &src[idx]);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* Swap integer rows k and k-1 of the m×n basis by exchanging the bigint headers
 * (limb pointers) — no limb copy, no scratch. */
static srmech_status_t lll_swap_rows(srmech_bigint_t *b, int n, int k)
{
    int t;
    assert(b != NULL && n >= 0);
    assert(k >= 1);
    for (t = 0; t < n; t++) {
        size_t ki = (size_t)k * (size_t)n + (size_t)t;
        size_t li = (size_t)(k - 1) * (size_t)n + (size_t)t;
        srmech_bigint_t tmp = b[ki];
        b[ki] = b[li];
        b[li] = tmp;
    }
    return SRMECH_OK;
}

/* The LLL outer loop over the working basis b (m rows × n cols); μ/B are the
 * carved GSO arrays. Returns OK / OVERFLOW / BAD_INPUT / INTERNAL. */
static srmech_status_t lll_run(lll_ctx_t *c, srmech_bigint_t *b, int m, int n,
                               srmech_bigint_t *mn, srmech_bigint_t *md,
                               srmech_bigint_t *bn, srmech_bigint_t *bd,
                               int32_t dn, int32_t dd, size_t iter_cap)
{
    srmech_status_t st;
    int k = 1, lov = 0, l;
    size_t iters = 0u;
    assert(c != NULL && b != NULL && m >= 2);
    assert(mn != NULL && bn != NULL);
    while (k < m) {
        if (++iters > iter_cap) { return SRMECH_ERR_INTERNAL; }
        st = lll_gso(c, b, m, n, mn, md, bn, bd);
        if (st != SRMECH_OK) { return st; }
        st = lll_red(c, b, n, mn, md, m, k, k - 1);
        if (st != SRMECH_OK) { return st; }
        st = lll_lovasz_ok(c, mn, md, bn, bd, m, k, dn, dd, &lov);
        if (st != SRMECH_OK) { return st; }
        if (lov) {
            for (l = k - 2; l >= 0; l--) {
                st = lll_red(c, b, n, mn, md, m, k, l);
                if (st != SRMECH_OK) { return st; }
            }
            k++;
        } else {
            st = lll_swap_rows(b, n, k);
            if (st != SRMECH_OK) { return st; }
            k = (k - 1 >= 1) ? (k - 1) : 1;
        }
    }
    return SRMECH_OK;
}

srmech_status_t srmech_lll_reduce(const srmech_bigint_t *basis, int m, int n,
                                  int32_t delta_num, int32_t delta_den,
                                  srmech_bigint_t *out, void *ws, size_t ws_len)
{
    lll_ctx_t ctx;
    uint32_t *base = (uint32_t *)ws;
    size_t words = ws_len / sizeof(uint32_t), cur = 0u, cnt;
    srmech_bigint_t *b, *mn, *md, *bn, *bd;
    size_t maxbits, iter_cap;
    srmech_status_t st;
    uint32_t cap;
    assert(m >= 0 && n >= 0);
    assert(ws != NULL || ws_len == 0u);
    if (delta_den <= 0 || delta_num > delta_den || delta_num * 4 <= delta_den) {
        return SRMECH_ERR_BAD_INPUT;
    }
    cnt = (size_t)m * (size_t)n;
    if (cnt > 0u && (basis == NULL || out == NULL)) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (m <= 1) {                                    /* trivially reduced */
        return lll_copy_matrix(out, basis, cnt);
    }
    if (ws == NULL) { return SRMECH_ERR_NULL_ARG; }
    maxbits = 1u;
    for (cnt = 0u; cnt < (size_t)m * (size_t)n; cnt++) {
        size_t bits = lll_bigint_bits(&basis[cnt]);
        if (bits > maxbits) { maxbits = bits; }
    }
    cap = (uint32_t)lll_cap_for(m, n, (int)maxbits);
    b = lll_carve_bigints(base, words, &cur, (size_t)m * (size_t)n, cap);
    mn = lll_carve_bigints(base, words, &cur, (size_t)m * (size_t)m, cap);
    md = lll_carve_bigints(base, words, &cur, (size_t)m * (size_t)m, cap);
    bn = lll_carve_bigints(base, words, &cur, (size_t)m, cap);
    bd = lll_carve_bigints(base, words, &cur, (size_t)m, cap);
    if (b == NULL || mn == NULL || md == NULL || bn == NULL || bd == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    st = lll_ctx_init(&ctx, base, words, &cur, cap);
    if (st != SRMECH_OK) { return st; }
    st = lll_copy_matrix(b, basis, (size_t)m * (size_t)n);
    if (st != SRMECH_OK) { return st; }
    iter_cap = (size_t)m * (size_t)m * (maxbits * 2u + 40u) + 4u * (size_t)m + 4096u;
    st = lll_run(&ctx, b, m, n, mn, md, bn, bd, delta_num, delta_den, iter_cap);
    if (st != SRMECH_OK) { return st; }
    return lll_copy_matrix(out, b, (size_t)m * (size_t)n);
}
