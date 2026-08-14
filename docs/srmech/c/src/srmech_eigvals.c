/* srmech_eigvals.c — the GENERAL (non-Hermitian) complex eigenvalue solver.
 *
 * v0.9.0rc299 (`#918`). Until this file existed, the C surface had exactly
 * three eigen-paths and none of them was general:
 *
 *   srmech_jacobi_eigvals            — REAL SYMMETRIC only (cyclic Jacobi)
 *   srmech_hermitian_eigendecompose_ws — COMPLEX HERMITIAN only (complex Jacobi)
 *   srmech_eigvec_exact / srmech_complex_isolate — EXACT, INTEGER matrices only
 *
 * while `srmech.math.laplacian.mat_eigvals` — the general non-Hermitian float
 * solver — was classified `composition_of_c`, a bucket whose annotation reads
 * "standalone-ready". It was not: its balancing, Hessenberg reduction,
 * deflation loop, Wilkinson shift ladder and {QR} were Python-only, and it has
 * no Hermitian fast path, so a bare-C host could not run it for ANY input —
 * not merely for non-Hermitian ones. rc285 filed that gap rather than closing
 * it and named the close as its own rc. This is that rc.
 *
 * The algorithm mirrors the Python body operation-for-operation (Golub & Van
 * Loan, *Matrix Computations*, 4th ed., §7.4.3 Householder reduction to
 * Hessenberg form, §7.5 the practical QR algorithm with Wilkinson shifts,
 * §7.5.1 balancing; Parlett & Reinsch, *Numer. Math.* 13 (1969) 293-304;
 * EISPACK `hqr` for the exceptional-shift cadence).
 *
 * PARITY CONTRACT — **NUMERIC (FPU-tol)**, not byte-exact, and deliberately so.
 * Both projections run the same operation sequence in IEEE double, so the
 * shared steps agree bit-for-bit; the one honest divergence is the complex
 * MODULUS. Python's `_fhypot` roots an EXACT rational sum-of-squares (Class-N,
 * arbitrary-precision), which no float kernel reproduces exactly. Here the
 * modulus is the scaled float form `m*sqrt(1+r*r)` over the shared
 * `srmech_rational_sqrt` — relative-precision at every scale (same IEEE
 * mantissa decomposition Python's float `sqrt` path uses, so THAT step is
 * bit-identical), differing from the exact-rational modulus by ~1 ulp. Since
 * the modulus feeds a shift estimate and a reflector phase, a 1-ulp difference
 * moves the iterates by ~1 ulp and the converged spectrum by far less than the
 * deflation tolerance. Measured agreement is asserted in the Python test.
 *
 * No libm (the roots go through srmech_rational_sqrt), no <complex.h> (values
 * are interleaved (re, im) pairs = C99 `double _Complex` layout), no malloc
 * (caller arena), no goto, no recursion, no abs() — every sign decision is a
 * Class-K pin-slot with Class-C re-application.
 */
#include "srmech.h"

#include <assert.h>
#include <stddef.h>
#include <stdint.h>

/* Deflation tolerance — mirrors `_MAT_EIG_DEFLATE_TOL` in laplacian.py. */
#define SRMECH_EIG_DEFLATE_TOL 1e-14

/* Below this fraction of the (scaled, O(1)) column norm the reflector takes a
 * REAL phase rather than x0/|x0|. Mirrors `_HOUSEHOLDER_PHASE_REL`. */
#define SRMECH_EIG_PHASE_REL 1e-4

/* Guard against a denormal-driven divide in the deflation test; mirrors the
 * `+ 1e-300` in the Python pin. */
#define SRMECH_EIG_TINY 1e-300

/* ── Class-K magnitude proxies (never abs()) ─────────────────────────────── */

/* max(|re|, |im|) — a magnitude PROXY needing no root, exact at every scale.
 * Sign is a Class-K pin-slot with Class-C re-application. */
static void srmech_eig_cmax(double re, double im, double *out)
{
    assert(out != NULL);
    assert(!(re != re) && !(im != im));            /* NaN is not a magnitude */
    double r = (re >= 0.0) ? re : -re;             /* Class-K pin-slot */
    double i = (im >= 0.0) ? im : -im;             /* Class-K pin-slot */
    *out = (r >= i) ? r : i;
}

/* |re + i*im| — the SCALED float modulus. Scaling by the larger component
 * keeps the squared term in range, so this is relative-precision at every
 * magnitude (the property `#919` restored on the Python side). */
static void srmech_eig_modulus(double re, double im, double *out)
{
    assert(out != NULL);
    assert(!(re != re) && !(im != im));
    double big = 0.0;
    srmech_eig_cmax(re, im, &big);
    if (big == 0.0) { *out = 0.0; return; }
    double x = re / big;
    double y = im / big;
    double root = 0.0;
    (void)srmech_rational_sqrt(x * x + y * y, &root);
    *out = big * root;
}

/* Principal complex square root via two REAL roots joined by a Class-K sign
 * branch: sqrt(w) = sqrt((|w|+a)/2) + i*sign(b)*sqrt((|w|-a)/2). Mirrors
 * `_complex_sqrt_local`. */
static void srmech_eig_csqrt(double a, double b, double *out_re, double *out_im)
{
    assert(out_re != NULL);
    assert(out_im != NULL);
    if (a == 0.0 && b == 0.0) { *out_re = 0.0; *out_im = 0.0; return; }
    double mod = 0.0;
    srmech_eig_modulus(a, b, &mod);
    double re_arg = (mod + a) / 2.0;               /* both >= 0 mathematically */
    double im_arg = (mod - a) / 2.0;               /* a tiny <0 is round-off */
    double re = 0.0;
    double im = 0.0;
    if (re_arg > 0.0) { (void)srmech_rational_sqrt(re_arg, &re); }
    if (im_arg > 0.0) { (void)srmech_rational_sqrt(im_arg, &im); }
    *out_re = re;
    *out_im = (b >= 0.0) ? im : -im;               /* Class-K sign branch */
}

/* Both eigenvalues of [[aa,bb],[cc,dd]]: lambda = (tr +- sqrt(tr^2-4det))/2.
 * Each argument is an interleaved (re, im) pair. Mirrors `_eig2x2`. */
static void srmech_eig_2x2(const double *aa, const double *bb,
                           const double *cc, const double *dd,
                           double *out_l1, double *out_l2)
{
    assert(aa != NULL && bb != NULL && cc != NULL && dd != NULL);
    assert(out_l1 != NULL && out_l2 != NULL);
    double trr = aa[0] + dd[0];
    double tri = aa[1] + dd[1];
    /* det = aa*dd - bb*cc (complex) */
    double adr = aa[0] * dd[0] - aa[1] * dd[1];
    double adi = aa[0] * dd[1] + aa[1] * dd[0];
    double bcr = bb[0] * cc[0] - bb[1] * cc[1];
    double bci = bb[0] * cc[1] + bb[1] * cc[0];
    double detr = adr - bcr;
    double deti = adi - bci;
    /* tr^2 - 4*det */
    double t2r = trr * trr - tri * tri - 4.0 * detr;
    double t2i = 2.0 * trr * tri - 4.0 * deti;
    double dr = 0.0;
    double di = 0.0;
    srmech_eig_csqrt(t2r, t2i, &dr, &di);
    out_l1[0] = (trr + dr) / 2.0;
    out_l1[1] = (tri + di) / 2.0;
    out_l2[0] = (trr - dr) / 2.0;
    out_l2[1] = (tri - di) / 2.0;
}

/* ── Parlett-Reinsch RADIX-2 balancing (exact diagonal similarity) ───────── */

/* One index's row/col norms over the n x n interleaved H. */
static void srmech_eig_norms(uint32_t n, const double *H, uint32_t i,
                             double *out_r, double *out_c)
{
    assert(H != NULL);
    assert(out_r != NULL && out_c != NULL);
    double r = 0.0;
    double c = 0.0;
    for (uint32_t j = 0; j < n; j++) {
        if (j == i) { continue; }
        double m = 0.0;
        size_t ij = ((size_t)i * n + j) * 2;
        size_t ji = ((size_t)j * n + i) * 2;
        srmech_eig_modulus(H[ij], H[ij + 1], &m);
        r += m;
        srmech_eig_modulus(H[ji], H[ji + 1], &m);
        c += m;
    }
    *out_r = r;
    *out_c = c;
}

/* Apply the accepted radix-2 scale to row i (÷f) and column i (×f). Because f
 * is a power of two every multiply/divide is an EXACT mantissa shift, so the
 * eigenvalue multiset is invariant. */
static void srmech_eig_apply_scale(uint32_t n, double *H, uint32_t i, double f)
{
    assert(H != NULL);
    assert(f > 0.0);
    for (uint32_t j = 0; j < n; j++) {
        size_t ij = ((size_t)i * n + j) * 2;
        size_t ji = ((size_t)j * n + i) * 2;
        H[ij] = H[ij] / f;
        H[ij + 1] = H[ij + 1] / f;
        H[ji] = H[ji] * f;
        H[ji + 1] = H[ji + 1] * f;
    }
}

/* The EISPACK `balanc` inner test at radix 2. Mirrors `_balance_radix2`. */
static void srmech_eig_balance(uint32_t n, double *H)
{
    assert(H != NULL);
    assert(n > 0);
    int converged = 0;
    while (converged == 0) {
        converged = 1;
        for (uint32_t i = 0; i < n; i++) {
            double r = 0.0;
            double c = 0.0;
            srmech_eig_norms(n, H, i, &r, &c);
            if (c == 0.0 || r == 0.0) { continue; }   /* isolated index */
            double f = 1.0;
            double s = c + r;
            double g = r / 2.0;
            while (c < g) { f *= 2.0; c *= 4.0; }
            g = r * 2.0;
            while (c >= g) { f /= 2.0; c /= 4.0; }
            /* Accept only a genuine reduction of the SCALED sum — the /f is
             * what makes s strictly decrease and the sweeps terminate. */
            if ((c + r) < 0.95 * s * f && f != 1.0) {
                converged = 0;
                srmech_eig_apply_scale(n, H, i, f);
            }
        }
    }
}

/* ── Householder reflector, SCALE-INVARIANT ─────────────────────────────── */

/* P = I - beta*v*v^H with P*x = alpha*e1, written into `v` (len complex
 * entries) and `*out_beta`. Returns 0 when there is nothing to annihilate.
 *
 * Scaling x by its largest component BEFORE forming the reflector is a
 * CORRECTNESS requirement, not a nicety: it keeps the modulus call inside the
 * range where x0/|x0| is a unit phase. Mirrors `_householder_reflector`. */
static int srmech_eig_reflector(uint32_t len, const double *x,
                                double *v, double *out_beta)
{
    assert(x != NULL && v != NULL);
    assert(out_beta != NULL);
    double scale = 0.0;
    for (uint32_t i = 0; i < len; i++) {
        double c = 0.0;
        srmech_eig_cmax(x[i * 2], x[i * 2 + 1], &c);
        if (c > scale) { scale = c; }
    }
    if (scale == 0.0) { return 0; }                  /* zero vector */
    double normx2 = 0.0;
    for (uint32_t i = 0; i < len; i++) {
        v[i * 2] = x[i * 2] / scale;
        v[i * 2 + 1] = x[i * 2 + 1] / scale;
        normx2 += v[i * 2] * v[i * 2] + v[i * 2 + 1] * v[i * 2 + 1];
    }
    if (normx2 <= 0.0) { return 0; }
    double normx = 0.0;
    (void)srmech_rational_sqrt(normx2, &normx);
    double modx0 = 0.0;
    srmech_eig_modulus(v[0], v[1], &modx0);
    /* The phase exists only to keep v[0] = x0 - alpha away from cancellation;
     * when |x0| is negligible against ||x|| its phase is noise. */
    double phr = 1.0;
    double phi = 0.0;
    if (modx0 > SRMECH_EIG_PHASE_REL * normx) {
        phr = v[0] / modx0;
        phi = v[1] / modx0;
    }
    v[0] -= -phr * normx;                            /* v[0] -= alpha */
    v[1] -= -phi * normx;
    double vhv = 0.0;
    for (uint32_t i = 0; i < len; i++) {
        vhv += v[i * 2] * v[i * 2] + v[i * 2 + 1] * v[i * 2 + 1];
    }
    if (vhv == 0.0) { return 0; }
    *out_beta = 2.0 / vhv;
    return 1;
}

/* ── Householder reduction to upper-Hessenberg form ─────────────────────── */

/* LEFT application H <- (I - beta*v*v^H)*H over rows [r0, n). */
static void srmech_eig_apply_left(uint32_t n, double *H, uint32_t r0,
                                  const double *v, double beta)
{
    assert(H != NULL && v != NULL);
    assert(r0 < n);
    for (uint32_t j = 0; j < n; j++) {
        double sr = 0.0;
        double si = 0.0;
        for (uint32_t i = r0; i < n; i++) {
            size_t p = ((size_t)i * n + j) * 2;
            size_t q = (size_t)(i - r0) * 2;
            sr += v[q] * H[p] + v[q + 1] * H[p + 1];      /* conj(v)*H */
            si += v[q] * H[p + 1] - v[q + 1] * H[p];
        }
        sr *= beta;
        si *= beta;
        for (uint32_t i = r0; i < n; i++) {
            size_t p = ((size_t)i * n + j) * 2;
            size_t q = (size_t)(i - r0) * 2;
            H[p] -= v[q] * sr - v[q + 1] * si;
            H[p + 1] -= v[q] * si + v[q + 1] * sr;
        }
    }
}

/* RIGHT application H <- H*(I - beta*v*v^H) over columns [c0, n). */
static void srmech_eig_apply_right(uint32_t n, double *H, uint32_t c0,
                                   const double *v, double beta)
{
    assert(H != NULL && v != NULL);
    assert(c0 < n);
    for (uint32_t i = 0; i < n; i++) {
        double sr = 0.0;
        double si = 0.0;
        for (uint32_t j = c0; j < n; j++) {
            size_t p = ((size_t)i * n + j) * 2;
            size_t q = (size_t)(j - c0) * 2;
            sr += H[p] * v[q] - H[p + 1] * v[q + 1];
            si += H[p] * v[q + 1] + H[p + 1] * v[q];
        }
        sr *= beta;
        si *= beta;
        for (uint32_t j = c0; j < n; j++) {
            size_t p = ((size_t)i * n + j) * 2;
            size_t q = (size_t)(j - c0) * 2;
            H[p] -= sr * v[q] + si * v[q + 1];            /* s*conj(v) */
            H[p + 1] -= si * v[q] - sr * v[q + 1];
        }
    }
}

/* Unitary reduction to upper-Hessenberg: P*A*P^H, so the multiset is
 * invariant. `xbuf`/`vbuf` are caller scratch of n complex entries each.
 * Mirrors `_hessenberg_complex`. */
static void srmech_eig_hessenberg(uint32_t n, double *H,
                                  double *xbuf, double *vbuf)
{
    assert(H != NULL);
    assert(xbuf != NULL && vbuf != NULL);
    for (uint32_t k = 0; k + 2 < n; k++) {
        uint32_t len = n - (k + 1);
        for (uint32_t i = 0; i < len; i++) {
            size_t p = ((size_t)(k + 1 + i) * n + k) * 2;
            xbuf[i * 2] = H[p];
            xbuf[i * 2 + 1] = H[p + 1];
        }
        double beta = 0.0;
        if (srmech_eig_reflector(len, xbuf, vbuf, &beta) != 0) {
            srmech_eig_apply_left(n, H, k + 1, vbuf, beta);
            srmech_eig_apply_right(n, H, k + 1, vbuf, beta);
        }
        /* Class-K pin-slot at zero: the annihilated entries are pinned
         * STRUCTURALLY, so the deflation test's Hessenberg premise is a fact
         * and not a tolerance. */
        for (uint32_t i = k + 2; i < n; i++) {
            size_t p = ((size_t)i * n + k) * 2;
            H[p] = 0.0;
            H[p + 1] = 0.0;
        }
    }
}

/* ── the shifted-QR sweep ───────────────────────────────────────────────── */

/* Householder QR of the k x k interleaved `R` (overwritten), accumulating Q.
 * Mirrors `_qr_complex_list`. */
static void srmech_eig_qr(uint32_t k, double *R, double *Q,
                          double *xbuf, double *vbuf)
{
    assert(R != NULL && Q != NULL);
    assert(xbuf != NULL && vbuf != NULL);
    for (uint32_t i = 0; i < k; i++) {
        for (uint32_t j = 0; j < k; j++) {
            size_t p = ((size_t)i * k + j) * 2;
            Q[p] = (i == j) ? 1.0 : 0.0;
            Q[p + 1] = 0.0;
        }
    }
    for (uint32_t c = 0; c < k; c++) {
        uint32_t len = k - c;
        for (uint32_t i = 0; i < len; i++) {
            size_t p = ((size_t)(c + i) * k + c) * 2;
            xbuf[i * 2] = R[p];
            xbuf[i * 2 + 1] = R[p + 1];
        }
        double beta = 0.0;
        if (srmech_eig_reflector(len, xbuf, vbuf, &beta) == 0) { continue; }
        srmech_eig_apply_left(k, R, c, vbuf, beta);
        srmech_eig_apply_right(k, Q, c, vbuf, beta);
    }
}

/* Choose the shift mu for the active block [lo, m). Wilkinson by default; the
 * EISPACK exceptional shift at the it==10 / it==20 stall cadence, which is what
 * dislodges an equal-modulus lock (roots of unity / companion blocks). */
static void srmech_eig_shift(uint32_t n, const double *H, uint32_t lo,
                             uint32_t m, uint32_t it, double *mu)
{
    assert(H != NULL && mu != NULL);
    assert(m >= 2 && m <= n);
    if (it == 10 || it == 20) {
        double g = 0.0;
        size_t p = ((size_t)(m - 1) * n + (m - 2)) * 2;
        srmech_eig_modulus(H[p], H[p + 1], &g);
        mu[0] = g;
        if (m >= 3 && (m - 3) >= lo) {
            size_t q = ((size_t)(m - 2) * n + (m - 3)) * 2;
            srmech_eig_modulus(H[q], H[q + 1], &g);
            mu[0] += g;
        }
        mu[1] = 0.0;                                  /* Class-C real ad-hoc */
        return;
    }
    double l1[2];
    double l2[2];
    size_t aa = ((size_t)(m - 2) * n + (m - 2)) * 2;
    size_t bb = ((size_t)(m - 2) * n + (m - 1)) * 2;
    size_t cc = ((size_t)(m - 1) * n + (m - 2)) * 2;
    size_t dd = ((size_t)(m - 1) * n + (m - 1)) * 2;
    srmech_eig_2x2(&H[aa], &H[bb], &H[cc], &H[dd], l1, l2);
    double d1 = 0.0;
    double d2 = 0.0;
    srmech_eig_modulus(l1[0] - H[dd], l1[1] - H[dd + 1], &d1);
    srmech_eig_modulus(l2[0] - H[dd], l2[1] - H[dd + 1], &d2);
    mu[0] = (d1 < d2) ? l1[0] : l2[0];
    mu[1] = (d1 < d2) ? l1[1] : l2[1];
}

/* Pin every negligible subdiagonal of the leading m x m block to EXACT zero.
 * Each pinned zero SPLITS the Hessenberg matrix into independent diagonal
 * blocks whose spectra are disjoint (Class-K pin-slot, not a carried tol). */
static void srmech_eig_pin(uint32_t n, double *H, uint32_t m)
{
    assert(H != NULL);
    assert(m <= n);
    for (uint32_t i = 1; i < m; i++) {
        size_t d0 = ((size_t)(i - 1) * n + (i - 1)) * 2;
        size_t d1 = ((size_t)i * n + i) * 2;
        size_t sd = ((size_t)i * n + (i - 1)) * 2;
        double a = 0.0;
        double b = 0.0;
        double s = 0.0;
        srmech_eig_modulus(H[d0], H[d0 + 1], &a);
        srmech_eig_modulus(H[d1], H[d1 + 1], &b);
        srmech_eig_modulus(H[sd], H[sd + 1], &s);
        if (s <= SRMECH_EIG_DEFLATE_TOL * (a + b + SRMECH_EIG_TINY)) {
            H[sd] = 0.0;
            H[sd + 1] = 0.0;
        }
    }
}

/* One shifted QR step on the ACTIVE block H[lo:m, lo:m]: subtract mu*I, QR,
 * recombine R*Q, add mu*I back. Rows/cols outside [lo, m) are untouched — the
 * exact zero at H[lo][lo-1] makes them a separate spectral block. */
static void srmech_eig_qr_step(uint32_t n, double *H, uint32_t lo, uint32_t m,
                               const double *mu, double *ws)
{
    assert(H != NULL && mu != NULL);
    assert(ws != NULL && m > lo);
    uint32_t k = m - lo;
    double *R = ws;
    double *Q = R + (size_t)k * k * 2;
    double *xbuf = Q + (size_t)k * k * 2;
    double *vbuf = xbuf + (size_t)k * 2;
    for (uint32_t i = 0; i < k; i++) {
        for (uint32_t j = 0; j < k; j++) {
            size_t src = ((size_t)(lo + i) * n + (lo + j)) * 2;
            size_t dst = ((size_t)i * k + j) * 2;
            R[dst] = H[src] - ((i == j) ? mu[0] : 0.0);
            R[dst + 1] = H[src + 1] - ((i == j) ? mu[1] : 0.0);
        }
    }
    srmech_eig_qr(k, R, Q, xbuf, vbuf);
    for (uint32_t i = 0; i < k; i++) {
        for (uint32_t j = 0; j < k; j++) {
            double sr = 0.0;
            double si = 0.0;
            for (uint32_t t = 0; t < k; t++) {
                size_t a = ((size_t)i * k + t) * 2;
                size_t b = ((size_t)t * k + j) * 2;
                sr += R[a] * Q[b] - R[a + 1] * Q[b + 1];
                si += R[a] * Q[b + 1] + R[a + 1] * Q[b];
            }
            size_t dst = ((size_t)(lo + i) * n + (lo + j)) * 2;
            H[dst] = sr + ((i == j) ? mu[0] : 0.0);
            H[dst + 1] = si + ((i == j) ? mu[1] : 0.0);
        }
    }
}

/* ── the public entry point ─────────────────────────────────────────────── */

size_t srmech_mat_eigvals_ws_size(uint32_t n)
{
    /* H work copy (n*n complex) + the per-step QR arena (R + Q at n*n complex
     * each, plus two length-n complex staging vectors). */
    size_t nn = (size_t)n * (size_t)n * 2;
    assert(n == 0 || nn / 2 / (size_t)n == (size_t)n);   /* no size_t overflow */
    size_t total = nn + nn + nn + (size_t)n * 4;
    assert(total >= nn);                                 /* sum did not wrap */
    return total;
}

/* Deflate the trailing 1x1 or the trailing 2x2 of the active block, appending
 * to `out`. Returns the new active size m. */
static uint32_t srmech_eig_deflate(uint32_t n, const double *H, uint32_t lo,
                                   double *out, uint32_t *cnt)
{
    assert(H != NULL && out != NULL && cnt != NULL);
    assert(lo + 2 <= n);
    size_t aa = ((size_t)lo * n + lo) * 2;
    size_t bb = ((size_t)lo * n + (lo + 1)) * 2;
    size_t cc = ((size_t)(lo + 1) * n + lo) * 2;
    size_t dd = ((size_t)(lo + 1) * n + (lo + 1)) * 2;
    double l1[2];
    double l2[2];
    srmech_eig_2x2(&H[aa], &H[bb], &H[cc], &H[dd], l1, l2);
    out[*cnt * 2] = l1[0];
    out[*cnt * 2 + 1] = l1[1];
    (*cnt)++;
    out[*cnt * 2] = l2[0];
    out[*cnt * 2 + 1] = l2[1];
    (*cnt)++;
    return lo;
}

/* The deflation sweep over an ALREADY balanced + Hessenberg-reduced H. Split
 * out of srmech_mat_eigvals_ws to keep both under JPL Rule 4's 60-line limit. */
static srmech_status_t srmech_eig_sweep(uint32_t n, double *H,
                                        uint32_t max_sweeps,
                                        double *out_eigvals, double *arena)
{
    assert(H != NULL && out_eigvals != NULL && arena != NULL);
    assert(n >= 2);
    uint32_t cnt = 0;
    uint32_t m = n;
    uint32_t it = 0;
    uint64_t sweeps = 0;
    uint64_t ceiling = (uint64_t)max_sweeps * (uint64_t)n;
    while (m > 0) {
        if (m == 1) {
            out_eigvals[cnt * 2] = H[0];
            out_eigvals[cnt * 2 + 1] = H[1];
            cnt++;
            break;
        }
        srmech_eig_pin(n, H, m);
        size_t sd = ((size_t)(m - 1) * n + (m - 2)) * 2;
        if (H[sd] == 0.0 && H[sd + 1] == 0.0) {
            size_t d = ((size_t)(m - 1) * n + (m - 1)) * 2;
            out_eigvals[cnt * 2] = H[d];
            out_eigvals[cnt * 2 + 1] = H[d + 1];
            cnt++;
            m--;
            it = 0;
            continue;
        }
        uint32_t lo = m - 1;
        while (lo > 0) {
            size_t p = ((size_t)lo * n + (lo - 1)) * 2;
            if (H[p] == 0.0 && H[p + 1] == 0.0) { break; }
            lo--;
        }
        if (m - lo == 2) {
            m = srmech_eig_deflate(n, H, lo, out_eigvals, &cnt);
            it = 0;
            continue;
        }
        double mu[2];
        srmech_eig_shift(n, H, lo, m, it, mu);
        srmech_eig_qr_step(n, H, lo, m, mu, arena);
        sweeps++;
        it++;
        if (sweeps > ceiling) {
            /* NEVER silently return the raw diagonal of an un-converged block
             * — for a companion matrix that diagonal is all zeros (the historic
             * all-zero bug). Report non-convergence instead. */
            return SRMECH_ERR_OVERFLOW;
        }
    }
    assert(cnt == n);
    return SRMECH_OK;
}

srmech_status_t srmech_mat_eigvals_ws(uint32_t       n,
                                      const double  *a_interleaved,
                                      uint32_t       max_sweeps,
                                      double        *out_eigvals,
                                      double        *workspace,
                                      size_t         ws_len)
{
    assert(out_eigvals != NULL || n == 0);
    assert(max_sweeps > 0);
    if (a_interleaved == NULL || out_eigvals == NULL || workspace == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n == 0) { return SRMECH_OK; }
    if (ws_len < srmech_mat_eigvals_ws_size(n)) { return SRMECH_ERR_OVERFLOW; }
    size_t nn = (size_t)n * (size_t)n * 2;
    double *H = workspace;
    double *arena = workspace + nn;
    for (size_t i = 0; i < nn; i++) { H[i] = a_interleaved[i]; }
    if (n == 1) {
        out_eigvals[0] = H[0];
        out_eigvals[1] = H[1];
        return SRMECH_OK;
    }
    srmech_eig_balance(n, H);
    srmech_eig_hessenberg(n, H, arena, arena + (size_t)n * 2);
    return srmech_eig_sweep(n, H, max_sweeps, out_eigvals, arena);
}
