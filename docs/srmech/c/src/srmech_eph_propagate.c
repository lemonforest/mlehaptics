/*
 * srmech_eph_propagate.c — the EPH complex-time Wick-rotation propagator
 * (0.9.0rc136; siona gh#1274).
 *
 * `srmech_eph_propagate` is a Class-L COMPOSITE over the existing kernels —
 * it writes no new eigensolver and no new transcendental:
 *
 *   harvest = e^{-zL}·u0 = V · diag(e^{-z·λ_k}) · V^H · u0
 *
 * EPH = harvest = Propagate · excite: a propagator P = e^{-zL} (operator)
 * applied to an excitation u0 (operand) → the harvest H. The thermal
 * e^{-tL} and the coherent e^{-itL} are the ONE complex-time propagator
 * e^{-zL} with z COMPLEX — the `i` is the WICK-ROTATION PHASE, and arg(z)
 * is the coherence dial (z real → thermal/decoherent, z imaginary →
 * coherent/unitary, arg(z) between → partial coherence). The neuron is one
 * propagator choice (RBS-SNN = EPH-with-a-synaptic-propagator); no
 * privileged instance.
 *
 * Kernels reused (no re-implementation here):
 *   - srmech_hermitian_eigendecompose_ws  (V, λ from ONE eigensolve) [Class L]
 *   - srmech_exp                          (real damping; Q61 libm-free) [Class N]
 *   - srmech_cos / srmech_sin             (oscillation; Q61 octant-reduced =
 *                                          the 2π argument fold)        [Class N]
 *
 * The per-mode scalar e^{-zλ_k} = e^{-Re(z)·λ_k}·(cos(Im(z)·λ_k) −
 * i·sin(Im(z)·λ_k)). srmech_cos/sin range-reduce the oscillation argument
 * internally (the Q61 octant reduction) — the algebraic-basis twin of the
 * Python op's explicit Machin-2π Class-N-series seam-fold, so both stay
 * correct at any t·λ. The harvest is basis-invariant (each eigenvector
 * appears in both V and V^H), so it agrees with the Python op to the
 * eigensolve tolerance regardless of the eigenvector sign / degenerate-
 * subspace basis convention.
 *
 * Standalone-complete honor ([[feedback_c_must_be_standalone_complete_no_
 * python_fallback]]): all scratch is bump-carved from the CALLER arena `ws`
 * (no malloc, JPL Rule 3). Size `ws` from srmech_eph_propagate_arena_bytes.
 * The Python op is the COMPLETE alternative implementation for no-C hosts
 * (value-parity, not a rescue).
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto)        : OK
 *   - Rule 2 (bounded loops)  : OK — all loops bounded by n (eigensolve n³)
 *   - Rule 3 (no malloc)      : OK — caller arena bump only
 *   - Rule 4 (≤60 lines/func) : OK — split into kernel-driver helpers
 *   - Rule 5 (≥2 asserts/fn)  : OK
 *   - Rule 7 (return-value)   : OK — srmech_status_t throughout
 *   - Rule 10 (warnings clean): OK — pedantic -Werror
 *
 * No abs()/fabs(): the sign of the imaginary factor is a Class-K/Class-C
 * negation (an explicit `-x`), never an ALU abs of a magnitude.
 *
 * License: MIT (parent project: mlehaptics).
 */

#include "srmech.h"

#include <assert.h>
#include <stddef.h>
#include <stdint.h>

/* 8-byte-aligned bump of `need` doubles out of the caller arena (the
 * heat_trace / resonant_spectrum bump pattern). Advances *off; returns
 * NULL (caller maps to OVERFLOW) if the arena is exhausted. */
static double *eph_bump(double *ws, size_t ws_cap, size_t *off, size_t need)
{
    assert(ws != NULL || ws_cap == 0);
    assert(off != NULL);
    if (*off + need > ws_cap) {
        return NULL;
    }
    double *p = ws + *off;
    *off += need;
    return p;
}

/* The per-mode complex Wick factor e^{-z·λ} = e^{-Re(z)·λ}·(cos(Im(z)·λ)
 * − i·sin(Im(z)·λ)). Damping via srmech_exp, oscillation via
 * srmech_cos / srmech_sin (their Q61 octant reduction IS the 2π argument
 * fold). Writes (*fr, *fi); returns the first non-OK kernel status. */
static srmech_status_t eph_wick_factor(double z_re, double z_im, double lam,
                                       double *fr, double *fi)
{
    assert(fr != NULL);
    assert(fi != NULL);
    double g = -(z_re * lam);            /* real damping exponent           */
    double theta = z_im * lam;           /* oscillation angle               */
    double e = 0.0;
    double c = 0.0;
    double s = 0.0;
    srmech_status_t st = srmech_exp(g, &e);
    if (st != SRMECH_OK) {
        return st;
    }
    st = srmech_cos(theta, &c);
    if (st != SRMECH_OK) {
        return st;
    }
    st = srmech_sin(theta, &s);
    if (st != SRMECH_OK) {
        return st;
    }
    *fr = e * c;
    *fi = -(e * s);                      /* Class-C sign, never abs()       */
    return SRMECH_OK;
}

/* Project onto the eigenbasis + scale per mode:
 *   c_k = (Σ_i conj(V[i,k])·u0[i]) · e^{-z·λ_k}
 * V is row-major INTERLEAVED (V[i,k] at element i*n+k); u0 / c are
 * interleaved. Bounded n² (an eigensolve dim). */
static srmech_status_t eph_project_scale(uint32_t n, const double *V,
                                         const double *u0, double z_re,
                                         double z_im, const double *lam,
                                         double *c)
{
    assert(V != NULL || n == 0);
    assert(c != NULL || n == 0);
    for (uint32_t k = 0; k < n; k++) {
        double cr = 0.0;
        double ci = 0.0;
        for (uint32_t i = 0; i < n; i++) {
            size_t idx = (size_t)i * (size_t)n + (size_t)k;
            double vr = V[2u * idx];
            double vi = V[2u * idx + 1u];
            double ur = u0[2u * i];
            double ui = u0[2u * i + 1u];
            cr += vr * ur + vi * ui;     /* Re[conj(V)·u]                   */
            ci += vr * ui - vi * ur;     /* Im[conj(V)·u]                   */
        }
        double fr = 0.0;
        double fi = 0.0;
        srmech_status_t st = eph_wick_factor(z_re, z_im, lam[k], &fr, &fi);
        if (st != SRMECH_OK) {
            return st;
        }
        c[2u * k] = cr * fr - ci * fi;
        c[2u * k + 1u] = cr * fi + ci * fr;
    }
    return SRMECH_OK;
}

/* Recombine the scaled modes: harvest_i = Σ_k V[i,k]·c_k (complex). */
static void eph_recombine(uint32_t n, const double *V, const double *c,
                          double *out)
{
    assert(V != NULL || n == 0);
    assert(out != NULL || n == 0);
    for (uint32_t i = 0; i < n; i++) {
        double hr = 0.0;
        double hi = 0.0;
        for (uint32_t k = 0; k < n; k++) {
            size_t idx = (size_t)i * (size_t)n + (size_t)k;
            double vr = V[2u * idx];
            double vi = V[2u * idx + 1u];
            double cr = c[2u * k];
            double ci = c[2u * k + 1u];
            hr += vr * cr - vi * ci;
            hi += vr * ci + vi * cr;
        }
        out[2u * i] = hr;
        out[2u * i + 1u] = hi;
    }
}

size_t srmech_eph_propagate_arena_bytes(uint32_t n, int is_complex)
{
    /* Same arena for real / complex input — a real L is lifted to the
     * interleaved (re, 0) Hermitian form. Carved doubles: H interleaved
     * (2nn) + eigvecs V (2nn) + eig workspace (2nn) + eigvals (n) + the
     * projected mode vector c (2n). Returned in BYTES. */
    (void)is_complex;
    size_t nn = (size_t)n * (size_t)n;
    assert(n == 0u || nn / (size_t)n == (size_t)n);   /* n*n no overflow    */
    assert(nn <= SIZE_MAX / (7u * sizeof(double)));   /* 6nn+3n no overflow */
    size_t doubles = nn * 6u + (size_t)n * 3u;
    return doubles * sizeof(double);
}

srmech_status_t srmech_eph_propagate(
    uint32_t       n,
    int            is_complex,
    const double  *L,
    const double  *u0_interleaved,
    double         z_re,
    double         z_im,
    double        *out_harvest_interleaved,
    double        *ws,
    size_t         ws_len)
{
    assert(n == 0 || L != NULL);
    assert(n == 0 || (u0_interleaved != NULL && out_harvest_interleaved != NULL));
    if (n == 0) {
        return SRMECH_OK;                 /* empty problem: nothing written */
    }
    if (L == NULL || u0_interleaved == NULL
        || out_harvest_interleaved == NULL || ws == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    size_t cap = ws_len / sizeof(double);
    size_t off = 0;
    size_t nn = (size_t)n * (size_t)n;
    double *H_il = eph_bump(ws, cap, &off, nn * 2u);
    double *lam = eph_bump(ws, cap, &off, (size_t)n);
    double *V_il = eph_bump(ws, cap, &off, nn * 2u);
    double *eig_ws = eph_bump(ws, cap, &off, nn * 2u);
    double *c = eph_bump(ws, cap, &off, (size_t)n * 2u);
    if (H_il == NULL || lam == NULL || V_il == NULL || eig_ws == NULL
        || c == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    for (size_t e = 0; e < nn; e++) {     /* lift to interleaved Hermitian  */
        if (is_complex != 0) {
            H_il[2u * e] = L[2u * e];
            H_il[2u * e + 1u] = L[2u * e + 1u];
        } else {
            H_il[2u * e] = L[e];
            H_il[2u * e + 1u] = 0.0;
        }
    }
    srmech_status_t st = srmech_hermitian_eigendecompose_ws(
        n, H_il, lam, V_il, eig_ws, nn * 2u);
    if (st != SRMECH_OK) {
        return st;
    }
    st = eph_project_scale(n, V_il, u0_interleaved, z_re, z_im, lam, c);
    if (st != SRMECH_OK) {
        return st;
    }
    eph_recombine(n, V_il, c, out_harvest_interleaved);
    return SRMECH_OK;
}
