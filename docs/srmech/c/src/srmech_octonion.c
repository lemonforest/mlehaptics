/*
 * srmech_octonion.c — C parity for the srmech.qm.octonion ODFT twiddle
 * family + the whole-transform OCTONION DFT (0.9.0rc111; issue #1234
 * Item 1c, re-raise of #863): srmech_octonion_exp / srmech_octonion_twiddle
 * (the dim-8 mirror of the rc109 srmech_quaternion_{exp,twiddle}) and
 * srmech_octonion_dft — the O(N^2) exact-reference ODFT over the existing
 * octonion loop operators (srmech_loop_{left,right}_op_f64), ALL THREE
 * forms (left / right / two_sided) in one peer.
 *
 * WHY THE BRACKETING IS AN EXPLICIT FIELD (F378): octonion multiplication
 * is NON-ASSOCIATIVE, so "the ODFT" is NOT unique until its bracketing
 * convention is DECLARED — a different bracketing is a DIFFERENT (also-
 * declarable) transform. The declared convention (attested in
 * octonion_dft.toml [cascade.bracketing]): per-summand-single-product;
 * the inverse applies the conjugate twiddle (sigma flip) on the SAME
 * declared side; the two-sided 3-factor association order is the explicit
 * `bracketing` argument (0 = (W_l . x) . W_r, 1 = W_l . (x . W_r)).
 *
 * WHERE NON-ASSOCIATIVITY BITES (the alternativity finding, verified from
 * Python over the fixed table): O is ALTERNATIVE (a(ax) = (aa)x) and by
 * Artin's theorem every 2-generated subalgebra is associative — so the
 * one-sided summand + its inverse composition live in <mu, x[m]> and the
 * same-axis round-trip is EXACT; non-associativity bites only at >= 3
 * independent generators (two_sided with distinct axes; a twiddle
 * associated through a product of two samples). The two-sided form is
 * FORWARD-ONLY (inverse == 1 with form == 2 is SRMECH_ERR_BAD_INPUT).
 *
 * THE TWIDDLE. exp(mu*theta) = cos(theta)*1 + sin(theta)*mu for a UNIT
 * pure-imaginary mu (mu[0] == 0; caller-normalised — the SAME contract as
 * srmech_quaternion_exp). cos/sin ride the Q61 Class-N cascade
 * (srmech_cos_q61 / srmech_sin_q61 — NOT libm), projected to double once;
 * byte-exact with the pure-Python mirror. srmech_octonion_twiddle adds the
 * DFT angle: theta = sigma * 2*pi * ((j*k) mod N) / N with the cyclic
 * index reduction done exactly in uint64 (Class I) and pi entering ONCE as
 * the Class-N 4*atan_q61(1) cascade (no libm M_PI).
 *
 * HONEST CASCADE SHAPE. The DFT is Class M (octonion multiply via the
 * loop operators) o Class C (sigma / twiddle orientation) o Class N (Q61
 * trig + the pi cascade) o Class I (jk mod N). No abs(); the signs live
 * in the Cayley-Dickson conjugates, never an absolute value.
 *
 * THREAD/STATE. Pure functions over caller buffers; `out` MUST NOT alias
 * the inputs. No shared static state; reentrant.
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto / recursion): early returns; fixed call DAG.
 *   - Rule 2 (bounded loops)       : all loops bounded by dim-8 / n_points.
 *   - Rule 3 (no malloc)           : caller buffers + fixed-size locals.
 *   - Rule 4 (<=60 lines/func)     : per-summand helper split out.
 *   - Rule 5 (>=2 asserts/fn)      : pointer / dimension pre-conditions.
 *   - Rule 7 (return-value)        : srmech_status_t throughout.
 *   - Rule 10 (warnings clean)     : -Wall -Wextra -Wpedantic -Werror / /WX.
 *
 * ABI: new symbols only — SRMECH_ABI_VERSION stays 3 (additive).
 *
 * License: MIT.
 */

#include "srmech.h"

#include <assert.h>
#include <stddef.h>
#include <stdint.h>

/* BYTE-EXACT parity contract (the rc110 lesson): the pure-Python mirrors
 * replicate this TU's float-op ORDER, so FMA contraction must be OFF — a
 * fused multiply-add rounds once where mul+add round twice, diverging in
 * the last ulp. GCC in strict -std=c11 mode already defaults to
 * -ffp-contract=off; CLANG defaults to ON (the macOS arm64 CI cell
 * diverged in the rc110 DFT accumulation loop), so the standard C11
 * pragma is applied for clang. MSVC /fp:precise does not contract. */
#if defined(__clang__)
#pragma STDC FP_CONTRACT OFF
#endif

/* The octonion carrier dimension (O, the dim-8 Cayley-Dickson rung). */
#define SRMECH_OCT_DIM ((size_t)8)

/* The 8x8 operator matvec with the row-dot accumulated LEFT-TO-RIGHT in a
 * scalar t — the exact float-op order of the Python `_odft_matvec8` mirror
 * (the byte-exact parity contract, not a tolerance). `op` is row-major
 * (out[i] = sum_c op[i*8 + c] * v[c]); `out` must not alias `v`. */
static void srmech_oct__matvec8(const double *op, const double *v, double *out)
{
    assert(op != NULL && v != NULL);
    assert(out != NULL);
    for (size_t i = 0; i < SRMECH_OCT_DIM; ++i) {
        double t = 0.0;
        for (size_t c = 0; c < SRMECH_OCT_DIM; ++c) {
            t += op[i * SRMECH_OCT_DIM + c] * v[c];
        }
        out[i] = t;
    }
}

/* The per-(k,m) twiddle pair: `w` always (axis mu); `w_r` only for the
 * two-sided form (form == 2, axis mu_r) — untouched otherwise. */
static srmech_status_t srmech_oct__twiddles(
    uint32_t k, uint32_t m, uint32_t n_points, int32_t sigma, int32_t form,
    const double *mu, const double *mu_r, double *w, double *w_r)
{
    assert(mu != NULL && w != NULL);
    assert(w_r != NULL);
    srmech_status_t st = srmech_octonion_twiddle(
        k, m, n_points, sigma, mu, SRMECH_OCT_DIM, w);
    if (st != SRMECH_OK) {
        return st;
    }
    if (form == 2) {
        st = srmech_octonion_twiddle(
            k, m, n_points, sigma, mu_r, SRMECH_OCT_DIM, w_r);
    }
    return st;
}

/* One ODFT summand under the DECLARED bracketing convention. form: 0 = left
 * (W . x, ONE product), 1 = right (x . W, ONE product), 2 = two_sided
 * (THREE factors — bracketing 0 = (W_l . x) . W_r, 1 = W_l . (x . W_r);
 * the F378 association order made an explicit argument). Composes the
 * existing octonion loop operators (srmech_loop_{left,right}_op_f64). */
static srmech_status_t srmech_oct__summand(
    int32_t form, int32_t bracketing, const double *w, const double *w_r,
    const double *x_m, double *term)
{
    double op[SRMECH_OCT_DIM * SRMECH_OCT_DIM];
    double inner[SRMECH_OCT_DIM];
    srmech_status_t st;
    assert(w != NULL && x_m != NULL);
    assert(w_r != NULL && term != NULL);
    if (form == 0) {                          /* left: W . x */
        st = srmech_loop_left_op_f64(w, SRMECH_OCT_DIM, op);
        if (st != SRMECH_OK) {
            return st;
        }
        srmech_oct__matvec8(op, x_m, term);
        return SRMECH_OK;
    }
    if (form == 1) {                          /* right: x . W */
        st = srmech_loop_right_op_f64(w, SRMECH_OCT_DIM, op);
        if (st != SRMECH_OK) {
            return st;
        }
        srmech_oct__matvec8(op, x_m, term);
        return SRMECH_OK;
    }
    /* two_sided — the bracketing DECLARES the association order (F378). */
    if (bracketing == 0) {                    /* (W_l . x) . W_r */
        st = srmech_loop_left_op_f64(w, SRMECH_OCT_DIM, op);
        if (st != SRMECH_OK) {
            return st;
        }
        srmech_oct__matvec8(op, x_m, inner);
        st = srmech_loop_right_op_f64(w_r, SRMECH_OCT_DIM, op);
        if (st != SRMECH_OK) {
            return st;
        }
        srmech_oct__matvec8(op, inner, term);
        return SRMECH_OK;
    }
    st = srmech_loop_right_op_f64(w_r, SRMECH_OCT_DIM, op);
    if (st != SRMECH_OK) {                    /* W_l . (x . W_r) */
        return st;
    }
    srmech_oct__matvec8(op, x_m, inner);
    st = srmech_loop_left_op_f64(w, SRMECH_OCT_DIM, op);
    if (st != SRMECH_OK) {
        return st;
    }
    srmech_oct__matvec8(op, inner, term);
    return SRMECH_OK;
}

srmech_status_t srmech_octonion_exp(
    double theta, const double *mu, size_t n, double *out)
{
    if (mu == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n != SRMECH_OCT_DIM || mu[0] != 0.0) {
        return SRMECH_ERR_BAD_INPUT;
    }
    int nonzero = 0;
    for (size_t i = 1; i < SRMECH_OCT_DIM; ++i) {
        if (mu[i] != 0.0) {
            nonzero = 1;
        }
    }
    if (nonzero == 0) {
        return SRMECH_ERR_BAD_INPUT;  /* a zero axis has no unit form */
    }
    assert(mu != NULL && out != NULL);
    assert(n == SRMECH_OCT_DIM);
    int64_t cq = 0;
    int64_t sq = 0;
    srmech_status_t st = srmech_cos_q61(theta, &cq);
    if (st != SRMECH_OK) {
        return st;
    }
    st = srmech_sin_q61(theta, &sq);
    if (st != SRMECH_OK) {
        return st;
    }
    /* Project the exact Q61 rationals to double ONCE (the float64 boundary
     * of the qm.* surface); division by 2^61 is an exact scaling. */
    const double c = (double)cq / (double)SRMECH_Q61_ONE;
    const double s = (double)sq / (double)SRMECH_Q61_ONE;
    out[0] = c;
    for (size_t i = 1; i < SRMECH_OCT_DIM; ++i) {
        out[i] = s * mu[i];
    }
    return SRMECH_OK;
}

srmech_status_t srmech_octonion_twiddle(
    uint32_t j, uint32_t k, uint32_t n_points, int32_t sigma,
    const double *mu, size_t n, double *out)
{
    if (mu == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n_points == 0u || (sigma != 1 && sigma != -1)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    assert(mu != NULL && out != NULL);
    assert(n_points >= 1u);
    /* pi enters ONCE as the Class-N 4*atan_q61(1) cascade (no libm M_PI) —
     * the same derivation the Python modules project at their boundary. */
    int64_t pi4_q61 = 0;
    srmech_status_t st = srmech_atan_q61(1.0, &pi4_q61);
    if (st != SRMECH_OK) {
        return st;
    }
    const double pi_c = 4.0 * ((double)pi4_q61 / (double)SRMECH_Q61_ONE);
    /* Class-I cyclic reduction of the twiddle index — exact in uint64
     * (j, k < 2^32 so the product cannot overflow). */
    const uint64_t r = ((uint64_t)j * (uint64_t)k) % (uint64_t)n_points;
    /* Float-op order is the parity contract with the pure-Python mirror:
     * theta = sigma * (2*pi) * (r/N), evaluated left-to-right. */
    const double two_pi = 2.0 * pi_c;
    const double frac = (double)r / (double)n_points;
    const double theta = (double)sigma * two_pi * frac;
    return srmech_octonion_exp(theta, mu, n, out);
}

srmech_status_t srmech_octonion_dft(
    const double *x, uint32_t n_points, int32_t form, int32_t bracketing,
    int32_t inverse, const double *mu, const double *mu_r, size_t n,
    double *out)
{
    if (x == NULL || mu == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (form == 2 && mu_r == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n != SRMECH_OCT_DIM || n_points == 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (form < 0 || form > 2 || (bracketing != 0 && bracketing != 1)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if ((inverse != 0 && inverse != 1) || (form == 2 && inverse != 0)) {
        return SRMECH_ERR_BAD_INPUT;  /* two_sided is FORWARD-ONLY (F378) */
    }
    assert(x != NULL && out != NULL);
    assert(n_points >= 1u);
    /* Forward sign sigma = -1; the inverse conjugates (+1) and scales 1/N
     * on the SAME declared side — the attested convention. */
    const int32_t sigma = (inverse != 0) ? 1 : -1;
    const double scale = (inverse != 0) ? (1.0 / (double)n_points) : 1.0;
    for (uint32_t k = 0u; k < n_points; ++k) {
        double acc[SRMECH_OCT_DIM] = {0.0};
        for (uint32_t m = 0u; m < n_points; ++m) {
            double w[SRMECH_OCT_DIM];
            double w_r[SRMECH_OCT_DIM];
            double term[SRMECH_OCT_DIM];
            srmech_status_t st = srmech_oct__twiddles(
                k, m, n_points, sigma, form, mu, mu_r, w, w_r);
            if (st != SRMECH_OK) {
                return st;
            }
            st = srmech_oct__summand(
                form, bracketing, w, (form == 2) ? w_r : w,
                &x[(size_t)m * SRMECH_OCT_DIM], term);
            if (st != SRMECH_OK) {
                return st;
            }
            for (size_t i = 0; i < SRMECH_OCT_DIM; ++i) {
                acc[i] += term[i];
            }
        }
        for (size_t i = 0; i < SRMECH_OCT_DIM; ++i) {
            out[(size_t)k * SRMECH_OCT_DIM + i] = acc[i] * scale;
        }
    }
    return SRMECH_OK;
}
