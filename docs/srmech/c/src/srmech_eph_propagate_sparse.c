/*
 * srmech_eph_propagate_sparse.c — the SPARSE-SCALED EPH propagator
 * (0.9.0rc206; siona gh#1274 item 1c — the corpus-scale residual).
 *
 * `srmech_eph_propagate_sparse` computes the SAME harvest as the rc136
 * `srmech_eph_propagate` — harvest = e^{-zL}·u0, the ONE complex-time
 * Wick-rotation propagator with the arg(z) coherence dial — but via a
 * CHEBYSHEV polynomial approximation applied with MATRIX-VECTOR PRODUCTS
 * ONLY, so it runs on a corpus-scale L past the n<=256 dense-eigensolve
 * cap. NO eigendecomposition, NO dense e^{-zL} is ever formed.
 *
 * The operator is the SIGNED graph Laplacian read straight off the edge
 * list (the srmech.amsc.laplacian.signed_laplacian convention):
 *     (L v)[i] = deg[i]·v[i] − Σ_{(i,j) edge} w_ij·v[j]
 * with deg[i] = Σ_incident |w| (a Class-K sign BRANCH, never fabs) and
 * self-loops skipped (they cancel in D̄ − A). Duplicate edges are read
 * PER-EDGE (each contributes |w| to the degree); pre-merge duplicates
 * that may carry opposite signs if exact signed_laplacian parity is
 * needed for such a list.
 *
 * Method (deterministic Chebyshev; no Lanczos, no orthogonalisation):
 *   1. Spectral interval by Gershgorin: 0 <= lambda <= 2·max_i deg[i]
 *      (the signed Laplacian is PSD; the bound is cheap + deterministic,
 *      an overestimate only widens the interval). Affine map
 *      L = cc·I + h·L~ with cc = h = lambda_max/2, spec(L~) in [-1, 1].
 *   2. Chebyshev interpolation coefficients of g(s) = e^{-z(cc + h·s)}
 *      at the M Chebyshev nodes s_j = cos(pi(2j+1)/(2M)):
 *          c_k = (2 - delta_k0)/M · Σ_j g(s_j)·cos(k·theta_j),
 *      cos(k·theta_j) by the 3-term recurrence (NO per-(k,j) trig). The
 *      per-node g(s_j) = e^{-z·lambda_j} reuses the rc136 Wick-factor
 *      kernels: srmech_exp (real damping) + srmech_cos / srmech_sin
 *      (oscillation; their Q61 octant reduction IS the 2π seam-fold, the
 *      algebraic twin of the Python op's Machin-2π Class-N fold).
 *   3. Adaptive node-count doubling M = 64, 128, ... up to the HARD CAP
 *      max_degree+1: accept when the coefficient tail (the top eighth)
 *      falls below tol·max_j|g(s_j)| (compared in SQUARES — no fabs, no
 *      sqrt); else double. Not converged at the cap → honest
 *      SRMECH_ERR_OVERFLOW (JPL Rule 2: every loop hard-bounded).
 *   4. Forward Chebyshev synthesis on VECTORS:
 *          y = Σ_{k<=m} c_k·T_k(L~)·u0,
 *          T_{k+1} = 2·L~·T_k − T_{k-1}
 *      — m matvecs, O(m·n_edges) time, O(n) memory. T_k of an operator
 *      with spectrum in [-1,1] has norm <= 1, so the forward recurrence
 *      is stable.
 *
 * Standalone-complete honor ([[feedback_c_must_be_standalone_complete_no_
 * python_fallback]]): all scratch is bump-carved from the CALLER arena
 * `ws` (no malloc, JPL Rule 3). Size `ws` from
 * srmech_eph_propagate_sparse_arena_bytes. The Python op is the COMPLETE
 * alternative implementation for no-C hosts (value-parity within tol,
 * not a rescue).
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto)        : OK
 *   - Rule 2 (bounded loops)  : OK — every loop bounded by n / n_edges /
 *                                M <= max_degree+1; the doubling loop by
 *                                EPHS_MAX_DOUBLINGS
 *   - Rule 3 (no malloc)      : OK — caller arena bump only
 *   - Rule 4 (≤60 lines/func) : OK — split into stage helpers
 *   - Rule 5 (≥2 asserts/fn)  : OK
 *   - Rule 7 (return-value)   : OK — srmech_status_t throughout
 *   - Rule 10 (warnings clean): OK — pedantic -Werror
 *
 * No abs()/fabs(): every magnitude is a sign branch or a magnitude-
 * SQUARE (re² + im²); signs are explicit Class-K/Class-C negations.
 *
 * License: MIT (parent project: mlehaptics).
 */

#include "srmech.h"

#include <assert.h>
#include <stddef.h>
#include <stdint.h>

/* The initial Chebyshev node count of the adaptive expansion (doubled up
 * to max_degree+1). 64 covers |z|·lambda_max up to ~40 at tol 1e-10. */
#define EPHS_M0 64u

/* Hard bound on the doubling loop (2^32 nodes is far past any uint32
 * max_degree, so the loop ALWAYS terminates within this). */
#define EPHS_MAX_DOUBLINGS 33u

/* 8-byte-aligned bump of `need` doubles out of the caller arena (the
 * eph_propagate / heat_trace bump pattern). Advances *off; returns NULL
 * (caller maps to OVERFLOW) if the arena is exhausted. */
static double *ephs_bump(double *ws, size_t ws_cap, size_t *off, size_t need)
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

/* Finiteness is checked inline as ((x == x) && (x - x == 0.0)) — x == x
 * rejects NaN, x - x == 0 rejects +-Inf (Inf - Inf is NaN). No isfinite,
 * no libm, no dedicated predicate function (a pure single-scalar
 * predicate would need a Rule-5 exemption; the inline form does not). */
#define EPHS_FINITE(x) (((x) == (x)) && ((x) - (x) == 0.0))

/* The per-mode complex Wick factor e^{-z·lam} = e^{-Re(z)·lam}·
 * (cos(Im(z)·lam) − i·sin(Im(z)·lam)) — the SAME kernel composition as
 * the rc136 eph_wick_factor (srmech_exp damping + srmech_cos/srmech_sin
 * oscillation; their Q61 octant reduction IS the 2π seam-fold). Writes
 * (*fr, *fi); returns the first non-OK kernel status. */
static srmech_status_t ephs_wick_factor(double z_re, double z_im, double lam,
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

/* Signed degrees deg[i] = Σ_incident |w| (Class-K sign BRANCH — never
 * fabs; self-loops skipped, the signed_laplacian convention) + the
 * Gershgorin bound *out_lam_max = 2·max_i deg[i]. Validates every edge
 * endpoint < n (SRMECH_ERR_BAD_INPUT otherwise). */
static srmech_status_t ephs_degrees(uint32_t n, uint32_t n_edges,
                                    const uint32_t *eu, const uint32_t *ev,
                                    const double *wts, double *deg,
                                    double *out_lam_max)
{
    assert(deg != NULL || n == 0);
    assert(out_lam_max != NULL);
    for (uint32_t i = 0; i < n; i++) {
        deg[i] = 0.0;
    }
    for (uint32_t e = 0; e < n_edges; e++) {
        uint32_t a = eu[e];
        uint32_t b = ev[e];
        if (a >= n || b >= n) {
            return SRMECH_ERR_BAD_INPUT;
        }
        if (a == b) {
            continue;                    /* self-loop cancels in D̄ − A     */
        }
        double w = (wts != NULL) ? wts[e] : 1.0;
        if (!EPHS_FINITE(w)) {
            return SRMECH_ERR_BAD_INPUT;
        }
        double m = (w >= 0.0) ? w : -w;  /* Class-K magnitude, no fabs      */
        deg[a] += m;
        deg[b] += m;
    }
    double lam_max = 0.0;
    for (uint32_t i = 0; i < n; i++) {
        double g2 = 2.0 * deg[i];
        if (g2 > lam_max) {
            lam_max = g2;
        }
    }
    *out_lam_max = lam_max;
    return SRMECH_OK;
}

/* Evaluate the M Chebyshev nodes: cosn[j] = cos(theta_j) (theta_j =
 * pi(2j+1)/(2M)) and f[j] = e^{-z·lambda_j} (interleaved re, im) with
 * lambda_j = cc + h·cosn[j]; *out_scale2 = max_j |f_j|² (a magnitude-
 * SQUARE — no fabs, no sqrt). A non-finite f_j (exp overflow on a
 * backward-propagation z) → SRMECH_ERR_BAD_INPUT. */
static srmech_status_t ephs_nodes(double pi, uint32_t M, double z_re,
                                  double z_im, double cc, double h,
                                  double *cosn, double *f_il,
                                  double *out_scale2)
{
    assert(cosn != NULL && f_il != NULL);
    assert(out_scale2 != NULL && M > 0u);
    double scale2 = 0.0;
    for (uint32_t j = 0; j < M; j++) {
        double theta = pi * (double)(2u * j + 1u) / (2.0 * (double)M);
        double cth = 0.0;
        srmech_status_t st = srmech_cos(theta, &cth);
        if (st != SRMECH_OK) {
            return st;
        }
        double lam = cc + h * cth;
        double fr = 0.0;
        double fi = 0.0;
        st = ephs_wick_factor(z_re, z_im, lam, &fr, &fi);
        if (st != SRMECH_OK) {
            return st;
        }
        if (!EPHS_FINITE(fr) || !EPHS_FINITE(fi)) {
            return SRMECH_ERR_BAD_INPUT;
        }
        cosn[j] = cth;
        f_il[2u * j] = fr;
        f_il[2u * j + 1u] = fi;
        double m2 = fr * fr + fi * fi;   /* Class-K magnitude-square        */
        if (m2 > scale2) {
            scale2 = m2;
        }
    }
    *out_scale2 = scale2;
    return SRMECH_OK;
}

/* The discrete Chebyshev transform: coeff[k] = (2 − delta_k0)/M ·
 * Σ_j f_j·cos(k·theta_j), k = 0..M−1, with cos(k·theta_j) by the 3-term
 * recurrence T_{k+1} = 2·cos(theta_j)·T_k − T_{k−1} (NO per-(k,j) trig).
 * j-outer / k-inner accumulation — the SAME order as the Python twin. */
static void ephs_coeffs(uint32_t M, const double *cosn, const double *f_il,
                        double *coeff_il)
{
    assert(cosn != NULL && f_il != NULL);
    assert(coeff_il != NULL && M > 0u);
    for (uint32_t k = 0; k < 2u * M; k++) {
        coeff_il[k] = 0.0;
    }
    for (uint32_t j = 0; j < M; j++) {
        double fr = f_il[2u * j];
        double fi = f_il[2u * j + 1u];
        double t_prev = 1.0;             /* T_0(s_j)                        */
        double t_cur = cosn[j];          /* T_1(s_j)                        */
        coeff_il[0] += fr;
        coeff_il[1] += fi;
        if (M > 1u) {
            coeff_il[2] += fr * t_cur;
            coeff_il[3] += fi * t_cur;
        }
        for (uint32_t k = 2; k < M; k++) {
            double t_next = 2.0 * cosn[j] * t_cur - t_prev;
            coeff_il[2u * k] += fr * t_next;
            coeff_il[2u * k + 1u] += fi * t_next;
            t_prev = t_cur;
            t_cur = t_next;
        }
    }
    double inv = 1.0 / (double)M;
    coeff_il[0] *= inv;
    coeff_il[1] *= inv;
    for (uint32_t k = 1; k < M; k++) {
        coeff_il[2u * k] *= 2.0 * inv;
        coeff_il[2u * k + 1u] *= 2.0 * inv;
    }
}

/* Tail scan: *out_m_eff = the largest k with |coeff_k|² > thresh2 (0 if
 * none — the all-damped-to-zero case). Converged (return 1) iff the top
 * eighth of the coefficient run is below threshold (the aliasing guard
 * of the M-node interpolation); else 0 → the caller doubles M. */
static int ephs_tail_scan(uint32_t M, const double *coeff_il,
                          double thresh2, uint32_t *out_m_eff)
{
    assert(coeff_il != NULL && out_m_eff != NULL);
    assert(M > 0u);
    uint32_t m_eff = 0u;
    for (uint32_t k = M; k > 0u; k--) {
        double cr = coeff_il[2u * (k - 1u)];
        double ci = coeff_il[2u * (k - 1u) + 1u];
        if (cr * cr + ci * ci > thresh2) {  /* Class-K magnitude-square     */
            m_eff = k - 1u;
            break;
        }
    }
    *out_m_eff = m_eff;
    uint32_t guard = (M / 8u > 1u) ? (M / 8u) : 1u;
    return (m_eff + guard <= M - 1u) ? 1 : 0;
}

/* The adaptive Chebyshev expansion: evaluate nodes + coefficients at
 * M = min(EPHS_M0, m_cap_nodes), test the tail, double M up to the HARD
 * CAP m_cap_nodes (= max_degree+1). Writes the accepted coefficients
 * (coeff_il, degree *out_m_eff). Not converged at the cap → honest
 * SRMECH_ERR_OVERFLOW (the caller's max_degree is the JPL loop bound). */
static srmech_status_t ephs_expand(double pi, double z_re, double z_im,
                                   double cc, double h, double tol,
                                   uint32_t m_cap_nodes, double *cosn,
                                   double *f_il, double *coeff_il,
                                   uint32_t *out_m_eff)
{
    assert(cosn != NULL && f_il != NULL && coeff_il != NULL);
    assert(out_m_eff != NULL && m_cap_nodes > 0u);
    uint32_t M = (EPHS_M0 < m_cap_nodes) ? EPHS_M0 : m_cap_nodes;
    for (uint32_t round = 0; round < EPHS_MAX_DOUBLINGS; round++) {
        double scale2 = 0.0;
        srmech_status_t st = ephs_nodes(pi, M, z_re, z_im, cc, h, cosn,
                                        f_il, &scale2);
        if (st != SRMECH_OK) {
            return st;
        }
        ephs_coeffs(M, cosn, f_il, coeff_il);
        double thresh2 = (tol * tol) * scale2;
        uint32_t m_eff = 0u;
        if (ephs_tail_scan(M, coeff_il, thresh2, &m_eff) != 0) {
            *out_m_eff = m_eff;
            return SRMECH_OK;
        }
        if (M >= m_cap_nodes) {
            return SRMECH_ERR_OVERFLOW;  /* honest: cap hit, tail not down  */
        }
        M = (M <= m_cap_nodes / 2u) ? (2u * M) : m_cap_nodes;
    }
    return SRMECH_ERR_INTERNAL;          /* unreachable: M doubles each round */
}

/* One scaled matvec out = L~·v = ((L·v) − cc·v)/h on the INTERLEAVED
 * complex vector v: (L v)[i] = deg[i]·v[i] − Σ_{(a,b) edge} w·v[other]
 * by edge-scatter — the SAME order as the Python twin. O(n + n_edges). */
static void ephs_matvec(uint32_t n, uint32_t n_edges, const uint32_t *eu,
                        const uint32_t *ev, const double *wts,
                        const double *deg, double cc, double hinv,
                        const double *v_il, double *out_il)
{
    assert(v_il != NULL && out_il != NULL);
    assert(deg != NULL || n == 0);
    for (uint32_t i = 0; i < n; i++) {
        out_il[2u * i] = deg[i] * v_il[2u * i];
        out_il[2u * i + 1u] = deg[i] * v_il[2u * i + 1u];
    }
    for (uint32_t e = 0; e < n_edges; e++) {
        uint32_t a = eu[e];
        uint32_t b = ev[e];
        if (a == b) {
            continue;                    /* self-loop cancels in D̄ − A     */
        }
        double w = (wts != NULL) ? wts[e] : 1.0;
        out_il[2u * a] -= w * v_il[2u * b];
        out_il[2u * a + 1u] -= w * v_il[2u * b + 1u];
        out_il[2u * b] -= w * v_il[2u * a];
        out_il[2u * b + 1u] -= w * v_il[2u * a + 1u];
    }
    for (uint32_t i = 0; i < 2u * n; i++) {
        out_il[i] = (out_il[i] - cc * v_il[i]) * hinv;
    }
}

/* Forward Chebyshev synthesis: y = Σ_{k<=m_eff} c_k·T_k(L~)·u0 via the
 * 3-term vector recurrence (m_eff matvecs; T_k norm <= 1 → stable).
 * v_prev / v_cur / v_next are the three rotating 2n-double stages. */
static void ephs_synthesis(uint32_t n, uint32_t n_edges, const uint32_t *eu,
                           const uint32_t *ev, const double *wts,
                           const double *deg, double cc, double hinv,
                           uint32_t m_eff, const double *coeff_il,
                           const double *u0, double *v_prev, double *v_cur,
                           double *v_next, double *y)
{
    assert(coeff_il != NULL && u0 != NULL);
    assert(v_prev != NULL && v_cur != NULL && v_next != NULL && y != NULL);
    double c0r = coeff_il[0];
    double c0i = coeff_il[1];
    for (uint32_t i = 0; i < n; i++) {
        v_prev[2u * i] = u0[2u * i];     /* copy first: y may alias u0      */
        v_prev[2u * i + 1u] = u0[2u * i + 1u];
        y[2u * i] = c0r * v_prev[2u * i] - c0i * v_prev[2u * i + 1u];
        y[2u * i + 1u] = c0r * v_prev[2u * i + 1u] + c0i * v_prev[2u * i];
    }
    if (m_eff == 0u) {
        return;
    }
    ephs_matvec(n, n_edges, eu, ev, wts, deg, cc, hinv, v_prev, v_cur);
    for (uint32_t k = 1; k <= m_eff; k++) {
        double ckr = coeff_il[2u * k];
        double cki = coeff_il[2u * k + 1u];
        for (uint32_t i = 0; i < 2u * n; i += 2u) {
            y[i] += ckr * v_cur[i] - cki * v_cur[i + 1u];
            y[i + 1u] += ckr * v_cur[i + 1u] + cki * v_cur[i];
        }
        if (k == m_eff) {
            break;                       /* last term: no further matvec    */
        }
        ephs_matvec(n, n_edges, eu, ev, wts, deg, cc, hinv, v_cur, v_next);
        for (uint32_t i = 0; i < 2u * n; i++) {
            v_next[i] = 2.0 * v_next[i] - v_prev[i];
        }
        double *rot = v_prev;            /* rotate the three stages         */
        v_prev = v_cur;
        v_cur = v_next;
        v_next = rot;
    }
}

/* The seven arena stages of the sparse propagator, bump-carved from the
 * caller arena in one pass (keeps the entry point within JPL Rule 4).
 * The harvest accumulates straight into the caller's output buffer, so
 * no separate y stage is carved. */
typedef struct {
    double *deg;                         /* signed degrees          (n)     */
    double *v_prev;                      /* T_{k-1}·u0 interleaved  (2n)    */
    double *v_cur;                       /* T_k·u0 interleaved      (2n)    */
    double *v_next;                      /* T_{k+1}·u0 interleaved  (2n)    */
    double *cosn;                        /* node cosines            (Mcap)  */
    double *f_il;                        /* node values interleaved (2Mcap) */
    double *coeff_il;                    /* coefficients interleaved(2Mcap) */
} ephs_arena_t;

/* Carve the seven stages out of the caller arena `ws` (ws_len BYTES);
 * SRMECH_ERR_OVERFLOW if it is too small (size it from
 * srmech_eph_propagate_sparse_arena_bytes). */
static srmech_status_t ephs_carve(uint32_t n, size_t mcap, double *ws,
                                  size_t ws_len, ephs_arena_t *a)
{
    assert(a != NULL);
    assert(mcap > 0u);
    size_t cap = ws_len / sizeof(double);
    size_t off = 0;
    a->deg = ephs_bump(ws, cap, &off, (size_t)n);
    a->v_prev = ephs_bump(ws, cap, &off, (size_t)n * 2u);
    a->v_cur = ephs_bump(ws, cap, &off, (size_t)n * 2u);
    a->v_next = ephs_bump(ws, cap, &off, (size_t)n * 2u);
    a->cosn = ephs_bump(ws, cap, &off, mcap);
    a->f_il = ephs_bump(ws, cap, &off, mcap * 2u);
    a->coeff_il = ephs_bump(ws, cap, &off, mcap * 2u);
    if (a->deg == NULL || a->v_prev == NULL || a->v_cur == NULL
        || a->v_next == NULL || a->cosn == NULL
        || a->f_il == NULL || a->coeff_il == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    return SRMECH_OK;
}

/* The expand + synthesize stage for a NON-ZERO spectral interval:
 * pi = 4·atan(1) (Class-N cascade), the adaptive Chebyshev expansion,
 * then the forward vector recurrence accumulating the harvest straight
 * into `out` (2n interleaved). Writes the accepted degree to
 * *out_m_eff; returns the first non-OK stage status. */
static srmech_status_t ephs_run(uint32_t n, uint32_t n_edges,
                                const uint32_t *eu, const uint32_t *ev,
                                const double *wts, double z_re, double z_im,
                                double tol, uint32_t mcap_nodes,
                                double lam_max, const double *u0,
                                double *out, const ephs_arena_t *a,
                                uint32_t *out_m_eff)
{
    assert(a != NULL && out_m_eff != NULL);
    assert(lam_max > 0.0);
    double a1 = 0.0;
    srmech_status_t st = srmech_atan(1.0, &a1);
    if (st != SRMECH_OK) {
        return st;
    }
    st = ephs_expand(4.0 * a1, z_re, z_im, 0.5 * lam_max, 0.5 * lam_max,
                     tol, mcap_nodes, a->cosn, a->f_il, a->coeff_il,
                     out_m_eff);
    if (st != SRMECH_OK) {
        return st;
    }
    ephs_synthesis(n, n_edges, eu, ev, wts, a->deg, 0.5 * lam_max,
                   2.0 / lam_max, *out_m_eff, a->coeff_il, u0,
                   a->v_prev, a->v_cur, a->v_next, out);
    return SRMECH_OK;
}

size_t srmech_eph_propagate_sparse_arena_bytes(uint32_t n, uint32_t n_edges,
                                               uint32_t max_degree)
{
    /* Carved doubles: deg (n) + three interleaved 2n vectors (v_prev,
     * v_cur, v_next; the harvest accumulates into the caller's output
     * buffer) + node cosines (Mcap) + node values f (2·Mcap) +
     * coefficients (2·Mcap), Mcap = max_degree+1. Edge arrays stay the
     * caller's own buffers (streamed per matvec). Returned in BYTES. */
    (void)n_edges;
    size_t mcap = (size_t)max_degree + 1u;
    size_t doubles = (size_t)n * 7u + mcap * 5u;
    assert(doubles >= mcap);                          /* no size_t wrap    */
    assert(doubles <= SIZE_MAX / sizeof(double));     /* bytes no overflow */
    return doubles * sizeof(double);
}

srmech_status_t srmech_eph_propagate_sparse(
    uint32_t        n,
    uint32_t        n_edges,
    const uint32_t *edges_u,
    const uint32_t *edges_v,
    const double   *weights,
    const double   *u0_interleaved,
    double          z_re,
    double          z_im,
    double          tol,
    uint32_t        max_degree,
    double         *out_harvest_interleaved,
    uint32_t       *out_degree_used,
    double         *ws,
    size_t          ws_len)
{
    assert(n == 0 || (u0_interleaved != NULL && out_harvest_interleaved != NULL));
    assert(n_edges == 0 || (edges_u != NULL && edges_v != NULL));
    if (n == 0) {
        return SRMECH_OK;                 /* empty problem: nothing written */
    }
    if (u0_interleaved == NULL || out_harvest_interleaved == NULL
        || ws == NULL || (n_edges > 0 && (edges_u == NULL || edges_v == NULL))) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (!(tol > 0.0) || max_degree == 0u || max_degree > (1u << 28)) {
        return SRMECH_ERR_BAD_INPUT;      /* degree cap: sane + no uint wrap */
    }
    size_t mcap = (size_t)max_degree + 1u;
    ephs_arena_t a;
    srmech_status_t st = ephs_carve(n, mcap, ws, ws_len, &a);
    if (st != SRMECH_OK) {
        return st;
    }
    double lam_max = 0.0;
    st = ephs_degrees(n, n_edges, edges_u, edges_v, weights, a.deg,
                      &lam_max);
    if (st != SRMECH_OK) {
        return st;
    }
    uint32_t m_eff = 0u;
    if (lam_max > 0.0) {
        st = ephs_run(n, n_edges, edges_u, edges_v, weights, z_re, z_im,
                      tol, (uint32_t)mcap, lam_max, u0_interleaved,
                      out_harvest_interleaved, &a, &m_eff);
        if (st != SRMECH_OK) {
            return st;
        }
    } else {
        for (uint32_t i = 0; i < 2u * n; i++) {
            out_harvest_interleaved[i] = u0_interleaved[i];  /* e^{0} = I  */
        }
    }
    if (out_degree_used != NULL) {
        *out_degree_used = m_eff;
    }
    return SRMECH_OK;
}
