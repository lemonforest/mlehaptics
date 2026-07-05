/*
 * srmech_svd_qr.c — numeric f64 QR + SVD (0.9.0rc140; Foundation F2).
 *
 * The C:Python parity backfill: the C surface had jacobi_eigvals /
 * hermitian_eigendecompose_ws / dense_matmul / dense_solve but NO SVD and NO
 * QR, so the whole subspace / MIMO / LA family (matrix_cascades.{qr,svd,lstsq}
 * + the signal_processing subspace ops) was python-only. This adds the two
 * numeric-LA foundations they dispatch to.
 *
 * THE OPS (real f64 — the complex path keeps its Gram-eigen / list-Householder
 * pure route, which is already a composition of C-dispatched primitives):
 *
 *   - srmech_qr_f64 — Householder QR (A = Q*R), A m*n (m>=n or m<n both OK),
 *     Q m*m orthogonal, R m*n upper-trapezoidal. DIRECT (no iteration): the
 *     product of min(m,n) elementary reflectors H = I - beta*v*v^T. The
 *     Householder phase alpha = -sign(x0)*||x|| is a Class-K pin-slot (a
 *     sign-BRANCH, never fabs/abs) that avoids cancellation. Malloc-free
 *     caller-arena (size via srmech_qr_f64_ws_bound).
 *
 *   - srmech_svd_f64 — A = U*diag(S)*V^T (m*n, m>=n), via ONE-SIDED JACOBI
 *     (Hestenes): orthogonalise the columns of a working copy W = A by a
 *     sequence of column Jacobi rotations, accumulating the rotations into V;
 *     the converged column norms are the singular values, U = W*diag(1/S).
 *     One-sided Jacobi is chosen over Golub-Kahan bidiagonalisation for a
 *     malloc-free JPL-clean C kernel: it is a naturally-bounded SWEEP loop
 *     (no implicit-shift bulge-chase bookkeeping), globally convergent, and
 *     numerically robust (high relative accuracy on the small singular
 *     values). ITERATIVE -> the weakest link: an EXPLICIT sweep CAP
 *     (SVD_MAX_SWEEPS, JPL Rule 2 bounded loop) + a CONVERGENCE CONTRACT — a
 *     sweep that applies ZERO rotations (every off-diagonal below tol) is
 *     converged; hitting the cap with a rotation still pending returns
 *     SRMECH_ERR_OVERFLOW (a NOT-CONVERGED status, NEVER a silent wrong
 *     answer), so the Python dispatch falls back to the pure Gram-eigen SVD.
 *     Malloc-free caller-arena (size via srmech_svd_f64_ws_bound).
 *
 * NUMERIC (FPU-tol), NOT byte-exact. Differential-tested against an
 * independent reference: QR reconstruction A == Q*R + orthogonality Q^T*Q==I;
 * SVD reconstruction U*diag(S)*V^T == A + orthogonality U^T*U==I / V^T*V==I +
 * descending S>=0, over square / tall / rank-deficient / near-degenerate-
 * singular-value shapes (the convergence stress). No libm: the only
 * transcendental is the square root, taken via the libm-free Class-N cascade
 * srmech_rational_sqrt (the C surface carries no <math.h>). No abs()/fabs():
 * every magnitude is a Class-K sign-branch.
 *
 * HONEST CASCADE SHAPE. Class L (the spectral / subspace content) . Class K
 * (the Householder / Jacobi rotation pin-slot + the sign-branch magnitude) .
 * Class M (the outer-product / column bundle) . Class N (the 2/(v^T v) and
 * 1/sigma scales, the sqrt roots).
 *
 * STANDALONE-COMPLETE honor: all scratch (the QR reflector vector; the SVD
 * working copy W + rotation accumulator V) is bump-carved from the CALLER
 * arena `ws` (no malloc, JPL Rule 3). The pure-Python cascade is the COMPLETE
 * alternative for no-C hosts (and the parity oracle).
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto / recursion): iterative sweeps + direct reflectors.
 *   - Rule 2 (bounded loops)      : every loop bounded by m / n / SVD_MAX_SWEEPS.
 *   - Rule 3 (no malloc)          : caller-arena only.
 *   - Rule 4 (<=60 lines/func)    : split into small kernel helpers.
 *   - Rule 5 (>=2 asserts/fn)     : pointer / bound pre-conditions.
 *   - Rule 7 (return-value)       : srmech_status_t on the public entries.
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

/* Explicit one-sided-Jacobi sweep cap (JPL Rule 2 bounded loop). One-sided
 * Jacobi converges quadratically once the pairs decouple; 60 sweeps is a
 * generous ceiling — a non-converging input returns NOT-CONVERGED, never a
 * silent wrong answer. Single-line #define (JPL Rule 8 clean). */
#define SVD_MAX_SWEEPS 60u

/* libm-free double square root via the Class-N rational cascade (the same
 * lap_sqrt route the native Jacobi eigensolver uses). All call sites pass a
 * provably non-negative argument. */
static double sq_sqrt(double x)
{
    double out = 0.0;
    assert(x >= 0.0);
    (void)srmech_rational_sqrt(x, &out);
    assert(out >= 0.0);
    return out;
}

/* ------------------------------------------------------------------ *
 * Householder QR (direct)
 * ------------------------------------------------------------------ */

/* R[j:, :] <- (I - beta*v*v^T) R[j:, :] — apply the reflector to the trailing
 * rows of R across every column (Class-M outer bind). */
static void qr_reflect_R(uint32_t m, uint32_t n, uint32_t j,
                         double *R, const double *v, double beta)
{
    uint32_t len = m - j;
    assert(R != NULL && v != NULL);
    assert(j < m);
    for (uint32_t col = 0; col < n; col++) {
        double vr = 0.0;
        for (uint32_t i = 0; i < len; i++) {
            vr += v[i] * R[(size_t)(j + i) * n + col];
        }
        double bvr = beta * vr;
        for (uint32_t i = 0; i < len; i++) {
            R[(size_t)(j + i) * n + col] -= bvr * v[i];
        }
    }
}

/* Q[:, j:] <- Q[:, j:] (I - beta*v*v^T) — accumulate the reflector into the
 * trailing columns of Q (Q is m*m). */
static void qr_reflect_Q(uint32_t m, uint32_t j, uint32_t len,
                         double *Q, const double *v, double beta)
{
    assert(Q != NULL && v != NULL);
    assert((size_t)j + len <= m);
    for (uint32_t row = 0; row < m; row++) {
        double qv = 0.0;
        for (uint32_t t = 0; t < len; t++) {
            qv += Q[(size_t)row * m + (j + t)] * v[t];
        }
        double bqv = beta * qv;
        for (uint32_t t = 0; t < len; t++) {
            Q[(size_t)row * m + (j + t)] -= bqv * v[t];
        }
    }
}

/* One Householder step on column j: build v from R[j:, j], compute the
 * 2/(v^T v) scale, apply to R and Q. A zero column / zero reflector is a
 * no-op (the column is already triangular). */
static void qr_step(uint32_t m, uint32_t n, uint32_t j,
                    double *R, double *Q, double *v)
{
    uint32_t len = m - j;
    double nrm2 = 0.0;
    assert(R != NULL && Q != NULL);
    assert(v != NULL && j < m);
    for (uint32_t i = 0; i < len; i++) {
        double x = R[(size_t)(j + i) * n + j];
        v[i] = x;
        nrm2 += x * x;
    }
    double normx = sq_sqrt(nrm2);
    if (normx == 0.0) {
        return;
    }
    /* Class-K pin-slot: alpha = -sign(x0)*||x|| (a sign-BRANCH, never fabs). */
    double x0 = v[0];
    double alpha = (x0 >= 0.0) ? -normx : normx;
    v[0] = x0 - alpha;
    double vhv = 0.0;
    for (uint32_t i = 0; i < len; i++) {
        vhv += v[i] * v[i];
    }
    if (vhv == 0.0) {
        return;
    }
    double beta = 2.0 / vhv;
    qr_reflect_R(m, n, j, R, v, beta);
    qr_reflect_Q(m, j, len, Q, v, beta);
}

size_t srmech_qr_f64_ws_bound(uint32_t m, uint32_t n)
{
    assert(m <= 0x7FFFFFFFu);
    assert(n <= 0x7FFFFFFFu);
    (void)n;                               /* v needs only m doubles */
    size_t doubles = (m == 0u) ? 1u : (size_t)m;
    return doubles * sizeof(double);
}

srmech_status_t srmech_qr_f64(uint32_t m, uint32_t n,
                              const double *A_rowmajor,
                              double *Q_out, double *R_out,
                              double *ws, size_t ws_len)
{
    assert(m == 0u || A_rowmajor != NULL);
    assert(m == 0u || n == 0u || (Q_out != NULL && R_out != NULL));
    if (m == 0u || n == 0u) {
        return SRMECH_OK;
    }
    if (A_rowmajor == NULL || Q_out == NULL || R_out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (ws_len / sizeof(double) < (size_t)m) {         /* v needs m doubles */
        return SRMECH_ERR_OVERFLOW;
    }
    for (size_t idx = 0; idx < (size_t)m * n; idx++) {
        R_out[idx] = A_rowmajor[idx];
    }
    for (uint32_t i = 0; i < m; i++) {
        for (uint32_t k = 0; k < m; k++) {
            Q_out[(size_t)i * m + k] = (i == k) ? 1.0 : 0.0;
        }
    }
    uint32_t kmax = (m < n) ? m : n;
    for (uint32_t j = 0; j < kmax; j++) {
        qr_step(m, n, j, R_out, Q_out, ws);
    }
    return SRMECH_OK;
}

/* ------------------------------------------------------------------ *
 * One-sided Jacobi SVD (iterative)
 * ------------------------------------------------------------------ */

/* Column-pair Gram entries of the working matrix W (m*n): aa = <c_i,c_i>,
 * bb = <c_j,c_j>, ab = <c_i,c_j>. */
static void svd_col_stats(uint32_t m, uint32_t n, const double *W,
                          uint32_t i, uint32_t j,
                          double *paa, double *pbb, double *pab)
{
    double aa = 0.0;
    double bb = 0.0;
    double ab = 0.0;
    assert(W != NULL);
    assert(paa != NULL && pbb != NULL && pab != NULL);
    for (uint32_t r = 0; r < m; r++) {
        double wi = W[(size_t)r * n + i];
        double wj = W[(size_t)r * n + j];
        aa += wi * wi;
        bb += wj * wj;
        ab += wi * wj;
    }
    *paa = aa;
    *pbb = bb;
    *pab = ab;
}

/* The Jacobi rotation (c, s) that orthogonalises a column pair with Gram
 * entries (aa, bb, ab). ab != 0 is guaranteed by the caller's tol skip. */
static void svd_jacobi_rotation(double aa, double bb, double ab,
                                double *pc, double *ps)
{
    assert(pc != NULL && ps != NULL);
    assert(ab != 0.0);
    double zeta = (bb - aa) / (2.0 * ab);
    double t;
    if (zeta >= 0.0) {
        t = 1.0 / (zeta + sq_sqrt(1.0 + zeta * zeta));
    } else {
        t = 1.0 / (zeta - sq_sqrt(1.0 + zeta * zeta));
    }
    double c = 1.0 / sq_sqrt(1.0 + t * t);
    *pc = c;
    *ps = c * t;
}

/* Rotate columns i, j of an (rows*ncols) row-major matrix M by (c, s) — the
 * Class-K pin-slot rotation, shared by W (m*n) and V (n*n). */
static void svd_rotate_cols(uint32_t rows, uint32_t ncols, double *M,
                            uint32_t i, uint32_t j, double c, double s)
{
    assert(M != NULL);
    assert(i < ncols && j < ncols);
    for (uint32_t r = 0; r < rows; r++) {
        double mi = M[(size_t)r * ncols + i];
        double mj = M[(size_t)r * ncols + j];
        M[(size_t)r * ncols + i] = c * mi - s * mj;
        M[(size_t)r * ncols + j] = s * mi + c * mj;
    }
}

/* One full sweep over every column pair (i < j). Returns 1 if any pair was
 * rotated (NOT yet converged), 0 if every pair was already below tol (the
 * convergence signal). */
static int svd_one_sweep(uint32_t m, uint32_t n, double *W, double *V,
                         double tol)
{
    int rotated = 0;
    assert(W != NULL);
    assert(V != NULL);
    for (uint32_t i = 0; i < n; i++) {
        for (uint32_t j = i + 1; j < n; j++) {
            double aa;
            double bb;
            double ab;
            svd_col_stats(m, n, W, i, j, &aa, &bb, &ab);
            double denom = sq_sqrt(aa * bb);
            double mag_ab = (ab < 0.0) ? -ab : ab;   /* Class-K, not fabs */
            if (denom <= 0.0 || mag_ab <= tol * denom) {
                continue;
            }
            double c;
            double s;
            svd_jacobi_rotation(aa, bb, ab, &c, &s);
            svd_rotate_cols(m, n, W, i, j, c, s);
            svd_rotate_cols(n, n, V, i, j, c, s);
            rotated = 1;
        }
    }
    return rotated;
}

/* Read the singular values (converged column norms) + U = W*diag(1/S); copy
 * V through. A near-zero column norm -> sigma 0, U column 0 (the Python
 * completion supplies that left-nullspace column). */
static void svd_finalize(uint32_t m, uint32_t n, const double *W,
                         const double *V, double *U_out, double *S_out,
                         double *V_out)
{
    assert(W != NULL && V != NULL);
    assert(U_out != NULL && S_out != NULL && V_out != NULL);
    for (uint32_t j = 0; j < n; j++) {
        double nrm2 = 0.0;
        for (uint32_t r = 0; r < m; r++) {
            double w = W[(size_t)r * n + j];
            nrm2 += w * w;
        }
        double sigma = sq_sqrt(nrm2);
        S_out[j] = sigma;
        double inv = (sigma > 1e-300) ? (1.0 / sigma) : 0.0;
        for (uint32_t r = 0; r < m; r++) {
            U_out[(size_t)r * n + j] = W[(size_t)r * n + j] * inv;
        }
    }
    for (size_t idx = 0; idx < (size_t)n * n; idx++) {
        V_out[idx] = V[idx];
    }
}

/* Selection-sort the SVD triple into DESCENDING singular-value order, swapping
 * the paired U (m*n) and V (n*n) columns alongside each S entry. */
static void svd_sort_desc(uint32_t m, uint32_t n,
                          double *U_out, double *S_out, double *V_out)
{
    assert(U_out != NULL && S_out != NULL);
    assert(V_out != NULL);
    for (uint32_t p = 0; p < n; p++) {
        uint32_t best = p;
        for (uint32_t q = p + 1; q < n; q++) {
            if (S_out[q] > S_out[best]) {
                best = q;
            }
        }
        if (best == p) {
            continue;
        }
        double ts = S_out[p];
        S_out[p] = S_out[best];
        S_out[best] = ts;
        for (uint32_t r = 0; r < m; r++) {
            double t = U_out[(size_t)r * n + p];
            U_out[(size_t)r * n + p] = U_out[(size_t)r * n + best];
            U_out[(size_t)r * n + best] = t;
        }
        for (uint32_t r = 0; r < n; r++) {
            double t = V_out[(size_t)r * n + p];
            V_out[(size_t)r * n + p] = V_out[(size_t)r * n + best];
            V_out[(size_t)r * n + best] = t;
        }
    }
}

size_t srmech_svd_f64_ws_bound(uint32_t m, uint32_t n)
{
    assert(m <= 0x7FFFFFFFu);
    assert(n <= 0x7FFFFFFFu);
    size_t doubles = (size_t)m * n + (size_t)n * n;   /* W (m*n) + V (n*n) */
    if (doubles == 0u) {
        doubles = 1u;
    }
    return doubles * sizeof(double);
}

srmech_status_t srmech_svd_f64(uint32_t m, uint32_t n,
                               const double *A_rowmajor,
                               double *U_out, double *S_out, double *V_out,
                               double *ws, size_t ws_len)
{
    assert(m == 0u || A_rowmajor != NULL);
    assert(n == 0u || (S_out != NULL && V_out != NULL));
    if (m == 0u || n == 0u) {
        return SRMECH_OK;
    }
    if (A_rowmajor == NULL || U_out == NULL || S_out == NULL
        || V_out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (m < n) {
        return SRMECH_ERR_BAD_INPUT;                   /* caller transposes */
    }
    size_t need = (size_t)m * n + (size_t)n * n;
    if (ws_len / sizeof(double) < need) {
        return SRMECH_ERR_OVERFLOW;
    }
    double *W = ws;
    double *V = ws + (size_t)m * n;
    for (size_t idx = 0; idx < (size_t)m * n; idx++) {
        W[idx] = A_rowmajor[idx];
    }
    for (uint32_t i = 0; i < n; i++) {
        for (uint32_t j = 0; j < n; j++) {
            V[(size_t)i * n + j] = (i == j) ? 1.0 : 0.0;
        }
    }
    int rotated = 1;
    for (uint32_t sweep = 0; sweep < SVD_MAX_SWEEPS && rotated != 0; sweep++) {
        rotated = svd_one_sweep(m, n, W, V, 1e-14);
    }
    if (rotated != 0) {
        return SRMECH_ERR_OVERFLOW;   /* hit cap unconverged — NOT silent-wrong */
    }
    svd_finalize(m, n, W, V, U_out, S_out, V_out);
    svd_sort_desc(m, n, U_out, S_out, V_out);
    return SRMECH_OK;
}
