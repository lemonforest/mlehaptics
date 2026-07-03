/*
 * srmech_quaternion.c — C parity for srmech.qm.quaternion (0.9.0rc109;
 * issue #1234 Item 1a, re-raise of #863 BX-5/6/7): the 4x4 left/right
 * quaternion multiplication operators + the hypercomplex exp(mu*theta)
 * twiddle — the QDFT/ODFT foundation. 0.9.0rc110 (#1234 Item 1b) adds
 * srmech_quaternion_dft — the whole O(N^2) exact-reference QUATERNION
 * DFT over that foundation (left/right form selectable; byte-exact with
 * the Python composed path cascade.quaternion_dft).
 *
 * WHY (F380 / the in-repo R21 proof): the Klein-4 group IS the quaternion
 * units modulo sign (Q8/{+-1} ~= Z2xZ2), so a quaternion FT's coefficient
 * algebra (H) matches a Klein-4 object's value algebra. These peers let a
 * C-only host build the 4x4 operator matrices and the DFT twiddle factors
 * without slicing the 8x8 octonion operators.
 *
 * THE PRODUCT. Same fixed Cayley-Dickson convention as srmech_loopbind.c
 * (matching srmech.amsc.hdc._loop_bind_raw and qm.octonion):
 *
 *     (a, b)(c, d) = (a c - conj(d) b,  d a + b conj(c))
 *
 * at the quaternion (dim-4) level: a,b,c,d complex (dim-2) pairs, the
 * scalar base case conj == identity. H is the dim-4 rung of the SAME
 * ladder, so these operators are the octonion loop operators restricted
 * to the first 4 basis elements (tested from Python).
 *
 * THE TWIDDLE. exp(mu*theta) = cos(theta)*1 + sin(theta)*mu for a UNIT
 * pure-imaginary mu (mu[0] == 0; caller-normalised — the SAME contract as
 * srmech_hypercomplex_couple_q61's caller-provided unit mu). cos/sin ride
 * the Q61 Class-N cascade (srmech_cos_q61 / srmech_sin_q61 — NOT libm),
 * projected to double once; byte-exact with the pure-Python mirror.
 * srmech_quaternion_twiddle adds the DFT angle: theta =
 * sigma * 2*pi * ((j*k) mod N) / N with the cyclic index reduction done
 * exactly in uint64 (Class I) and pi entering ONCE as the Class-N
 * 4*atan_q61(1) cascade (no libm M_PI) — the same derivation the Python
 * laplacian/quaternion modules use.
 *
 * HONEST CASCADE SHAPE. left/right mult are Class M binds with Class-C
 * ordering; the twiddle is Class N (Q61 trig) o Class C (sigma) o
 * Class I (jk mod N). No abs(); the signs live in the Cayley-Dickson
 * conjugates, never an absolute value.
 *
 * THREAD/STATE. Pure functions over caller buffers; `out` MUST NOT alias
 * the inputs. No shared static state; reentrant.
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto / recursion): early returns; fixed call DAG.
 *   - Rule 2 (bounded loops)       : all loops bounded by the dim-4 carrier.
 *   - Rule 3 (no malloc)           : caller buffers + fixed-size locals.
 *   - Rule 4 (<=60 lines/func)     : one helper per Cayley-Dickson level.
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

/* The quaternion carrier dimension (H, the dim-4 Cayley-Dickson rung). */
#define SRMECH_QUAT_DIM ((size_t)4)

/* Complex (dim-2) product, the Cayley-Dickson level above the reals:
 *   (x0,x1)(y0,y1) = (x0 y0 - y1 x1,  y1 x0 + x1 y0)
 * Identical convention to srmech_loopbind.c's level-2 helper. */
static void srmech_quat__mul2(const double *x, const double *y, double *out)
{
    assert(x != NULL && y != NULL);
    assert(out != NULL);
    out[0] = x[0] * y[0] - y[1] * x[1];
    out[1] = y[1] * x[0] + x[1] * y[0];
}

/* Quaternion (dim-4) product via complex pairs a=x[0:2], b=x[2:4],
 * c=y[0:2], d=y[2:4]:  (a c - conj(d) b,  d a + b conj(c)),  with
 * conj2(p) = (p0, -p1). A fixed two-call complex level (no recursion) —
 * identical convention to srmech_loopbind.c's level-4 helper, so H here
 * IS the octonion product restricted to the first 4 basis elements. */
static void srmech_quat__mul4(const double *x, const double *y, double *out)
{
    assert(x != NULL && y != NULL);
    assert(out != NULL);
    const double dconj[2] = { y[2], -y[3] };
    const double cconj[2] = { y[0], -y[1] };
    double ac[2], db[2], da[2], bc[2];
    srmech_quat__mul2(&x[0], &y[0], ac);   /* a c       */
    srmech_quat__mul2(dconj, &x[2], db);   /* conj(d) b */
    srmech_quat__mul2(&y[2], &x[0], da);   /* d a       */
    srmech_quat__mul2(&x[2], cconj, bc);   /* b conj(c) */
    out[0] = ac[0] - db[0];
    out[1] = ac[1] - db[1];
    out[2] = da[0] + bc[0];
    out[3] = da[1] + bc[1];
}

srmech_status_t srmech_quaternion_left_mult(
    const double *q, size_t n, double *out)
{
    if (q == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n != SRMECH_QUAT_DIM) {
        return SRMECH_ERR_BAD_INPUT;
    }
    assert(q != NULL && out != NULL);
    assert(n == SRMECH_QUAT_DIM);
    for (size_t k = 0; k < SRMECH_QUAT_DIM; ++k) {
        double e[SRMECH_QUAT_DIM] = {0.0};
        double col[SRMECH_QUAT_DIM];
        e[k] = 1.0;
        srmech_quat__mul4(q, e, col);  /* q . e_k */
        for (size_t i = 0; i < SRMECH_QUAT_DIM; ++i) {
            out[i * SRMECH_QUAT_DIM + k] = col[i];
        }
    }
    return SRMECH_OK;
}

srmech_status_t srmech_quaternion_right_mult(
    const double *q, size_t n, double *out)
{
    if (q == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n != SRMECH_QUAT_DIM) {
        return SRMECH_ERR_BAD_INPUT;
    }
    assert(q != NULL && out != NULL);
    assert(n == SRMECH_QUAT_DIM);
    for (size_t k = 0; k < SRMECH_QUAT_DIM; ++k) {
        double e[SRMECH_QUAT_DIM] = {0.0};
        double col[SRMECH_QUAT_DIM];
        e[k] = 1.0;
        srmech_quat__mul4(e, q, col);  /* e_k . q */
        for (size_t i = 0; i < SRMECH_QUAT_DIM; ++i) {
            out[i * SRMECH_QUAT_DIM + k] = col[i];
        }
    }
    return SRMECH_OK;
}

srmech_status_t srmech_quaternion_exp(
    double theta, const double *mu, size_t n, double *out)
{
    if (mu == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n != SRMECH_QUAT_DIM || mu[0] != 0.0) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (mu[1] == 0.0 && mu[2] == 0.0 && mu[3] == 0.0) {
        return SRMECH_ERR_BAD_INPUT;  /* a zero axis has no unit form */
    }
    assert(mu != NULL && out != NULL);
    assert(n == SRMECH_QUAT_DIM);
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
    out[1] = s * mu[1];
    out[2] = s * mu[2];
    out[3] = s * mu[3];
    return SRMECH_OK;
}

srmech_status_t srmech_quaternion_twiddle(
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
    return srmech_quaternion_exp(theta, mu, n, out);
}

srmech_status_t srmech_quaternion_dft(
    const double *x, uint32_t n_points, int32_t left, int32_t inverse,
    const double *mu, size_t n, double *out)
{
    if (x == NULL || mu == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n != SRMECH_QUAT_DIM || n_points == 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if ((left != 0 && left != 1) || (inverse != 0 && inverse != 1)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    assert(x != NULL && out != NULL);
    assert(n_points >= 1u);
    /* Forward sign sigma = -1; the inverse conjugates (+1) and scales 1/N. */
    const int32_t sigma = (inverse != 0) ? 1 : -1;
    const double scale = (inverse != 0) ? (1.0 / (double)n_points) : 1.0;
    for (uint32_t k = 0u; k < n_points; ++k) {
        double acc[SRMECH_QUAT_DIM] = {0.0, 0.0, 0.0, 0.0};
        for (uint32_t m = 0u; m < n_points; ++m) {
            double w[SRMECH_QUAT_DIM];
            double op[SRMECH_QUAT_DIM * SRMECH_QUAT_DIM];
            srmech_status_t st = srmech_quaternion_twiddle(
                k, m, n_points, sigma, mu, SRMECH_QUAT_DIM, w);
            if (st != SRMECH_OK) {
                return st;
            }
            st = (left != 0)
                ? srmech_quaternion_left_mult(w, SRMECH_QUAT_DIM, op)
                : srmech_quaternion_right_mult(w, SRMECH_QUAT_DIM, op);
            if (st != SRMECH_OK) {
                return st;
            }
            /* Row-dot left-to-right then accumulate over m — the float-op
             * order IS the byte-exact parity contract with _qdft_composed. */
            for (size_t i = 0; i < SRMECH_QUAT_DIM; ++i) {
                double t = 0.0;
                for (size_t c = 0; c < SRMECH_QUAT_DIM; ++c) {
                    t += op[i * SRMECH_QUAT_DIM + c]
                        * x[(size_t)m * SRMECH_QUAT_DIM + c];
                }
                acc[i] += t;
            }
        }
        for (size_t i = 0; i < SRMECH_QUAT_DIM; ++i) {
            out[(size_t)k * SRMECH_QUAT_DIM + i] = acc[i] * scale;
        }
    }
    return SRMECH_OK;
}
