/*
 * srmech_jade.c — JADE joint-diagonalisation Givens sweep (0.9.0rc155;
 * BATCH B-residue, the FINAL compute op → python_only_debt = 0).
 *
 * THE OP (srmech_jade_jointdiag): the iterative kernel at the heart of
 * ICA-JADE (Cardoso & Souloumiac 1993). Given the fourth-order cumulant
 * tensor C (k*k*k*k, row-major) of the whitened observations, drive its
 * (i,j) slices toward joint diagonality by a sequence of Givens rotations,
 * accumulating the rotations into V (k*k). The rotation basis V IS the
 * un-mixing rotation the caller composes with the whitening matrix.
 *
 * This is the last compute gap: whitening (PCA eig) already dispatches to
 * srmech_hermitian_eigendecompose_ws, and the cumulant assembly is a plain
 * Class-M multiply-accumulate; only the Givens JOINT-DIAGONALISATION sweep
 * was a Python-only kernel with no C twin. It is genuinely ITERATIVE with
 * a data-dependent rotation schedule (like the one-sided-Jacobi SVD), so it
 * earns its own standalone-C symbol rather than a false composition tag.
 *
 * The per-(i,j) update mirrors the Python reference EXACTLY, including the
 * simplified-JADE angle theta = 0.25*atan2(2*C[i][j][i][j],
 * C[i][i][i][i]-C[j][j][j][j]) and the first-axis tensor rotation applied
 * TWICE per Givens step (a preserved quirk of the reference), so the native
 * sweep and the pure-Python sweep recover the SAME sources up to the
 * inherent JADE permutation/sign/scale ambiguity (within-tol on the
 * separation, per the parity contract).
 *
 * NUMERIC (FPU-tol), NOT byte-exact. No libm: the angle is the libm-free
 * Class-N cascade srmech_atan2, the sine/cosine srmech_sin / srmech_cos
 * (the same cascades the Python rational.{atan2,cos,sin} dispatch to). No
 * abs()/fabs(): every magnitude is a Class-K sign-branch expression.
 *
 * HONEST CASCADE SHAPE. Class L (the cumulant-slice spectral content) .
 * Class K (the Givens rotation pin-slot + the sign-branch magnitudes) .
 * Class C (the which-way rotation orientation) . Class N (the atan2 angle
 * + the sin/cos twiddle).
 *
 * STANDALONE-COMPLETE honor: all scratch (the Givens matrix G, the V . G
 * product accumulator, the rotated-cumulant ping-pong buffer) is bump-carved
 * from the CALLER arena `ws` (no malloc, JPL Rule 3). The pure-Python sweep
 * is the COMPLETE alternative for no-C hosts (and the parity oracle).
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto / recursion): iterative sweeps only.
 *   - Rule 2 (bounded loops)      : every loop bounded by k / max_iter.
 *   - Rule 3 (no malloc)          : caller-arena only.
 *   - Rule 4 (<=60 lines/func)    : split into small kernel helpers.
 *   - Rule 5 (>=2 asserts/fn)     : pointer / bound pre-conditions.
 *   - Rule 7 (return-value)       : srmech_status_t on the public entry.
 *   - Rule 8 (no multi-line macro): single-line #define only.
 *   - Rule 10 (warnings clean)    : -Wall -Wextra -Wpedantic -Werror / /WX.
 *
 * ABI: new symbols only — SRMECH_ABI_VERSION stays 3 (additive; the Python
 * ctypes shim hasattr-guards them).
 *
 * License: MIT (parent project: mlehaptics).
 */

#include "srmech.h"

#include <assert.h>
#include <stddef.h>
#include <stdint.h>

/* The reference's numerical-zero guard on |num|+|den| (JPL Rule 8 clean). */
#define JADE_SKIP_EPS 1e-15

/* out[a][j][l][m] = Σ_i G[i][a] · in[i][j][l][m] — rotate the cumulant
 * tensor's first axis by Gᵀ (the reference's _rotate_first_axis). */
static void jade_rotate_first_axis(uint32_t k, const double *in,
                                   const double *g, double *out)
{
    size_t k4 = (size_t)k * k * k * k;
    assert(in != NULL && g != NULL && out != NULL);
    assert(k > 0u);
    for (size_t t = 0; t < k4; t++) {
        out[t] = 0.0;
    }
    for (uint32_t a = 0; a < k; a++) {
        for (uint32_t i = 0; i < k; i++) {
            double gia = g[(size_t)i * k + a];
            if (gia == 0.0) {
                continue;
            }
            for (uint32_t j = 0; j < k; j++) {
                for (uint32_t l = 0; l < k; l++) {
                    size_t bo = (((size_t)a * k + j) * k + l) * k;
                    size_t bi = (((size_t)i * k + j) * k + l) * k;
                    for (uint32_t mm = 0; mm < k; mm++) {
                        out[bo + mm] += gia * in[bi + mm];
                    }
                }
            }
        }
    }
}

/* out = V · G (both k*k, row-major) — accumulate over the inner index in the
 * SAME order as the reference _matmul (out[r][c] = Σ_t V[r][t]·G[t][c]). */
static void jade_matmul(uint32_t k, const double *v,
                        const double *g, double *out)
{
    assert(v != NULL && g != NULL && out != NULL);
    assert(k > 0u);
    for (uint32_t r = 0; r < k; r++) {
        for (uint32_t c = 0; c < k; c++) {
            double acc = 0.0;
            for (uint32_t t = 0; t < k; t++) {
                acc += v[(size_t)r * k + t] * g[(size_t)t * k + c];
            }
            out[(size_t)r * k + c] = acc;
        }
    }
}

/* G = I(k) with the (i,j) Givens block: G[i][i]=G[j][j]=c, G[i][j]=-s,
 * G[j][i]=s (the reference's rotation matrix). */
static void jade_build_givens(uint32_t k, uint32_t i, uint32_t j,
                              double c, double s, double *g)
{
    assert(g != NULL);
    assert(i < k && j < k);
    for (uint32_t a = 0; a < k; a++) {
        for (uint32_t b = 0; b < k; b++) {
            g[(size_t)a * k + b] = (a == b) ? 1.0 : 0.0;
        }
    }
    g[(size_t)i * k + i] = c;
    g[(size_t)j * k + j] = c;
    g[(size_t)i * k + j] = -s;
    g[(size_t)j * k + i] = s;
}

/* One (i,j) pair update: compute the JADE angle, and — when it clears the
 * tol/eps guards — rotate V and the cumulant tensor (twice, per the
 * reference), adding |theta| to *poff. */
static void jade_pair(double *cum, uint32_t k, uint32_t i, uint32_t j,
                      double tol, double *g, double *vscr,
                      double *cumscr, double *v, double *poff)
{
    double num = 2.0 * cum[(((size_t)i * k + j) * k + i) * k + j];
    double dii = cum[(((size_t)i * k + i) * k + i) * k + i];
    double djj = cum[(((size_t)j * k + j) * k + j) * k + j];
    double den = dii - djj;
    double theta = 0.0;
    double c = 0.0;
    double s = 0.0;
    double mnum = (num >= 0.0) ? num : -num;       /* Class-K, not fabs */
    double mden = (den >= 0.0) ? den : -den;
    assert(cum != NULL && v != NULL && poff != NULL);
    assert(i < k && j < k);
    if (mnum + mden < JADE_SKIP_EPS) {
        return;
    }
    (void)srmech_atan2(num, den + JADE_SKIP_EPS, &theta);
    theta *= 0.25;
    double mtheta = (theta >= 0.0) ? theta : -theta;
    if (mtheta < tol) {
        return;
    }
    *poff += mtheta;
    (void)srmech_cos(theta, &c);
    (void)srmech_sin(theta, &s);
    jade_build_givens(k, i, j, c, s, g);
    jade_matmul(k, v, g, vscr);
    for (size_t t = 0; t < (size_t)k * k; t++) {
        v[t] = vscr[t];
    }
    jade_rotate_first_axis(k, cum, g, cumscr);
    jade_rotate_first_axis(k, cumscr, g, cum);
}

/* One full sweep over every (i<j) column pair; returns the accumulated
 * off-diagonal rotation magnitude Σ|theta| (the convergence signal). */
static double jade_sweep(double *cum, uint32_t k, double tol, double *g,
                         double *vscr, double *cumscr, double *v)
{
    double off = 0.0;
    assert(cum != NULL && v != NULL);
    assert(k > 0u);
    for (uint32_t i = 0; i < k; i++) {
        for (uint32_t j = i + 1; j < k; j++) {
            jade_pair(cum, k, i, j, tol, g, vscr, cumscr, v, &off);
        }
    }
    return off;
}

size_t srmech_jade_jointdiag_ws_bound(uint32_t k)
{
    assert(k <= 0xFFFFu);                          /* k^4 must fit size_t */
    size_t kk = (size_t)k * k;
    assert(kk <= 0xFFFFFFFFu);                     /* kk*kk (=k^4) stays < 2^64 */
    size_t doubles = 2u * kk + kk * kk;            /* G + Vscratch + cumscratch */
    if (doubles == 0u) {
        doubles = 1u;
    }
    return doubles * sizeof(double);
}

srmech_status_t srmech_jade_jointdiag(double *cum, uint32_t k,
                                      uint32_t max_iter, double tol,
                                      double *v_out, double *ws,
                                      size_t ws_len)
{
    assert(k == 0u || (cum != NULL && v_out != NULL));
    assert(ws != NULL || ws_len == 0u);
    if (k == 0u) {
        return SRMECH_OK;
    }
    if (cum == NULL || v_out == NULL || ws == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    size_t kk = (size_t)k * k;
    size_t need = 2u * kk + kk * kk;
    if (ws_len / sizeof(double) < need) {
        return SRMECH_ERR_OVERFLOW;
    }
    double *g = ws;
    double *vscr = ws + kk;
    double *cumscr = ws + 2u * kk;
    for (uint32_t a = 0; a < k; a++) {
        for (uint32_t b = 0; b < k; b++) {
            v_out[(size_t)a * k + b] = (a == b) ? 1.0 : 0.0;
        }
    }
    for (uint32_t it = 0; it < max_iter; it++) {
        double off = jade_sweep(cum, k, tol, g, vscr, cumscr, v_out);
        if (off < tol) {
            break;
        }
    }
    return SRMECH_OK;
}
