/*
 * srmech_fft.c — numeric complex128 FFT / IFFT (0.9.0rc139; Foundation F1).
 *
 * The C:Python parity backfill (#743 / #747): the C surface had NO numeric
 * complex FFT — only srmech_exact_dft_i64 (exact-integer, Z[zeta_N]) and
 * srmech_autocorrelation_f64. So the whole signal_processing fft-family
 * (dft/fft/idft/ifft + every transform that USES an FFT) was python-only.
 * This adds the numeric foundation the fft-family dispatches to.
 *
 * THE OP. The complex128 discrete Fourier transform of an N-point signal:
 *
 *     X[k] = Sum_n x[n] * e^{s*2*pi*i*k*n/N},   s = -1 forward / +1 inverse,
 *
 * with a single 1/N scale applied on the inverse (matching NumPy fft/ifft
 * and srmech.amsc.cascade.spectral_cascades.fft/ifft addend-for-addend).
 *
 *   - Power-of-two N: the ITERATIVE (no-recursion, JPL Rule 1) radix-2
 *     Cooley-Tukey butterfly over a bit-reversed copy, twiddles from ONE
 *     e^{s*2*pi*i*k/N} table (k = 0 .. N/2-1) strided per stage.
 *   - Arbitrary / PRIME N: Bluestein's chirp-z algorithm — the size-N DFT
 *     becomes a size-M (M = next pow2 >= 2N-1) circular convolution of the
 *     chirp-modulated signal with the conjugate chirp, evaluated by three
 *     radix-2 FFTs. So it is NOT power-of-2-only.
 *
 * NUMERIC (FPU-tol), NOT byte-exact — contrast the exact-integer
 * srmech_exact_dft_i64. The twiddle / chirp trig is the LIBM-FREE Class-N
 * cascade srmech_cos / srmech_sin (the C surface carries no <math.h>); pi
 * is the exact Q61 half-pi anchor, double-projected. Differential-tested
 * against an independent naive O(N^2) DFT (stdlib cmath) and against the
 * pure-Python spectral_cascades path to ~1e-10, plus FFT-then-IFFT == id.
 *
 * HONEST CASCADE SHAPE. Class A (canonical sequence order) . Class I
 * (cyclic Z/N transform domain) . Class J (the radix N = 2*(N/2) split) .
 * Class K (the butterfly / rotation pin-slot) . Class M (the bundle sum).
 * No abs(): the FFT is all complex add / subtract / multiply — there is no
 * magnitude read (so no Class-K abs is even reachable).
 *
 * STANDALONE-COMPLETE honor: all scratch (bit-reversed twiddle table +
 * Bluestein buffers) is bump-carved from the CALLER arena `ws` (no malloc,
 * JPL Rule 3) — size it from srmech_fft_c128_ws_bound(n). `out` MUST NOT
 * alias `in`. The pure-Python cascade is the COMPLETE alternative for
 * no-C hosts (value-parity, not a rescue).
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto / recursion): iterative radix-2 + Bluestein; no goto.
 *   - Rule 2 (bounded loops)      : every loop bounded by n / m / log2(m).
 *   - Rule 3 (no malloc)          : caller-arena bump only.
 *   - Rule 4 (<=60 lines/func)    : split into small kernel helpers.
 *   - Rule 5 (>=2 asserts/fn)     : pointer / bound pre-conditions.
 *   - Rule 7 (return-value)       : srmech_status_t throughout.
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

/* pi from the exact Q61 half-pi anchor (libm-free), double-projected. A
 * floating constant expression — no runtime, no libm. */
static const double FFT_PI =
    2.0 * ((double)SRMECH_Q61_HALF_PI / (double)SRMECH_Q61_ONE);

/* Single-line predicate macro (JPL Rule 8 clean): n a power of two. Callers
 * guarantee n >= 1, so (n & (n-1)) == 0 is the Class-J radix test. */
#define FFT_POW2(n) (((size_t)(n) & ((size_t)(n) - 1u)) == 0u)

/* Smallest power of two >= v (v >= 1). Bounded doubling loop (Rule 2). */
static size_t fft_next_pow2(size_t v)
{
    size_t p = 1u;
    assert(v >= 1u);
    assert(v <= (SIZE_MAX >> 1) + 1u);
    while (p < v) {
        p <<= 1;
    }
    return p;
}

/* 8-byte-aligned bump of `need` doubles out of the caller arena (the
 * heat_trace / resonant_spectrum bump pattern). Advances *off; returns NULL
 * (caller maps to OVERFLOW) if the arena is exhausted. */
static double *fft_bump(double *ws, size_t cap, size_t *off, size_t need)
{
    assert(off != NULL);
    assert(ws != NULL || cap == 0u);
    if (*off + need < *off || *off + need > cap) {   /* overflow-safe */
        return NULL;
    }
    double *p = ws + *off;
    *off += need;
    return p;
}

/* Fill tw[0 .. 2*(n/2)) with the n/2 roots e^{s*2*pi*i*k/n}, s = inverse?
 * +1 : -1, via the libm-free srmech_cos / srmech_sin. */
static srmech_status_t fft_build_twiddle(double *tw, size_t n, int inverse)
{
    double two_pi = 2.0 * FFT_PI;
    double s = (inverse != 0) ? 1.0 : -1.0;
    size_t half = n / 2u;
    assert(tw != NULL || half == 0u);
    assert(n >= 1u);
    for (size_t k = 0; k < half; k++) {
        double ang = s * two_pi * (double)k / (double)n;
        double c = 0.0;
        double sn = 0.0;
        srmech_status_t st = srmech_cos(ang, &c);
        if (st != SRMECH_OK) {
            return st;
        }
        st = srmech_sin(ang, &sn);
        if (st != SRMECH_OK) {
            return st;
        }
        tw[2u * k] = c;
        tw[2u * k + 1u] = sn;
    }
    return SRMECH_OK;
}

/* Copy `in` (n complex, interleaved re,im) into `out` in bit-reversed index
 * order — the decimation-in-time permutation. bits = log2(n). */
static void fft_bitrev_copy(const double *in, double *out, size_t n)
{
    size_t bits = 0u;
    assert(in != NULL);
    assert(out != NULL);
    while (((size_t)1u << bits) < n) {
        bits++;
    }
    for (size_t i = 0; i < n; i++) {
        size_t r = 0u;
        size_t x = i;
        for (size_t b = 0; b < bits; b++) {
            r = (r << 1) | (x & 1u);
            x >>= 1;
        }
        out[2u * r] = in[2u * i];
        out[2u * r + 1u] = in[2u * i + 1u];
    }
}

/* In-place iterative Cooley-Tukey butterflies over the bit-reversed `out`
 * (n complex). tw = the n/2-root table (matching sign); the stage-`len`
 * step-j twiddle is tw[j*(n/len)]. */
static void fft_butterflies(double *out, size_t n, const double *tw)
{
    assert(out != NULL);
    assert(tw != NULL);
    for (size_t len = 2u; len <= n; len <<= 1) {
        size_t half = len >> 1;
        size_t step = n / len;
        for (size_t i = 0; i < n; i += len) {
            for (size_t j = 0; j < half; j++) {
                size_t t = (i + j) * 2u;
                size_t u = (i + j + half) * 2u;
                double wr = tw[2u * (j * step)];
                double wi = tw[2u * (j * step) + 1u];
                double xr = out[u];
                double xi = out[u + 1u];
                double pr = wr * xr - wi * xi;
                double pim = wr * xi + wi * xr;
                out[u] = out[t] - pr;
                out[u + 1u] = out[t + 1u] - pim;
                out[t] = out[t] + pr;
                out[t + 1u] = out[t + 1u] + pim;
            }
        }
    }
}

/* Out-of-place radix-2 FFT: out = DFT(in), n a power of two. tw = scratch
 * for the n/2-root table (>= n doubles). Applies the 1/n scale when
 * inverse != 0 (the single normalisation the Python ifft applies). */
static srmech_status_t fft_radix2(const double *in, double *out, size_t n,
                                  int inverse, double *tw)
{
    assert(out != NULL);
    assert(tw != NULL);
    fft_bitrev_copy(in, out, n);
    if (n >= 2u) {
        srmech_status_t st = fft_build_twiddle(tw, n, inverse);
        if (st != SRMECH_OK) {
            return st;
        }
        fft_butterflies(out, n, tw);
    }
    if (inverse != 0) {
        double inv = 1.0 / (double)n;
        for (size_t i = 0; i < 2u * n; i++) {
            out[i] *= inv;
        }
    }
    return SRMECH_OK;
}

/* Bluestein chirp b[j] = e^{s*pi*i*(j^2 mod 2n)/n}, j = 0 .. n-1, into `b`
 * (n complex). j^2 is reduced mod 2n in integer BEFORE the trig so the
 * srmech_cos/sin argument stays bounded (e^{i*pi*2n/n} = e^{2*pi*i} = 1). */
static srmech_status_t fft_chirp(double *b, size_t n, int inverse)
{
    double s = (inverse != 0) ? 1.0 : -1.0;
    size_t two_n = 2u * n;
    assert(b != NULL);
    assert(n >= 1u);
    for (size_t j = 0; j < n; j++) {
        size_t m2 = (size_t)(((uint64_t)j * (uint64_t)j) % (uint64_t)two_n);
        double ang = s * FFT_PI * (double)m2 / (double)n;
        double c = 0.0;
        double sn = 0.0;
        srmech_status_t st = srmech_cos(ang, &c);
        if (st != SRMECH_OK) {
            return st;
        }
        st = srmech_sin(ang, &sn);
        if (st != SRMECH_OK) {
            return st;
        }
        b[2u * j] = c;
        b[2u * j + 1u] = sn;
    }
    return SRMECH_OK;
}

/* Build the two length-m Bluestein inputs: apad[j] = x[j]*b[j] (zero-padded
 * to m); the kernel v with v[l] = v[m-l] = conj(b[l]) = c[l] (the conjugate
 * chirp, symmetric because it depends on l^2). All other entries zero. */
static void fft_bluestein_prepare(const double *x, size_t n, size_t m,
                                  const double *b, double *apad, double *v)
{
    assert(apad != NULL);
    assert(v != NULL);
    for (size_t i = 0; i < 2u * m; i++) {
        apad[i] = 0.0;
        v[i] = 0.0;
    }
    for (size_t j = 0; j < n; j++) {
        double xr = x[2u * j];
        double xi = x[2u * j + 1u];
        double br = b[2u * j];
        double bi = b[2u * j + 1u];
        apad[2u * j] = xr * br - xi * bi;
        apad[2u * j + 1u] = xr * bi + xi * br;
        v[2u * j] = br;
        v[2u * j + 1u] = -bi;
        if (j > 0u) {
            v[2u * (m - j)] = br;
            v[2u * (m - j) + 1u] = -bi;
        }
    }
}

/* Pointwise complex product fa[k] *= fv[k], k = 0 .. m-1 (the convolution
 * theorem's frequency-domain multiply). */
static void fft_pointwise_mul(double *fa, const double *fv, size_t m)
{
    assert(fa != NULL);
    assert(fv != NULL);
    for (size_t k = 0; k < m; k++) {
        double ar = fa[2u * k];
        double ai = fa[2u * k + 1u];
        double br = fv[2u * k];
        double bi = fv[2u * k + 1u];
        fa[2u * k] = ar * br - ai * bi;
        fa[2u * k + 1u] = ar * bi + ai * br;
    }
}

/* X[k] = b[k]*conv[k], k = 0 .. n-1, with the 1/n scale on the inverse —
 * the final chirp demodulation that recovers the DFT from the convolution. */
static void fft_bluestein_finish(const double *b, const double *conv,
                                 size_t n, int inverse, double *out)
{
    double inv = (inverse != 0) ? (1.0 / (double)n) : 1.0;
    assert(out != NULL);
    assert(n >= 1u);
    for (size_t k = 0; k < n; k++) {
        double br = b[2u * k];
        double bi = b[2u * k + 1u];
        double cr = conv[2u * k];
        double ci = conv[2u * k + 1u];
        out[2u * k] = (br * cr - bi * ci) * inv;
        out[2u * k + 1u] = (br * ci + bi * cr) * inv;
    }
}

/* Bluestein / chirp-z DFT for arbitrary (incl. prime) n via a size-m
 * circular convolution (m = next pow2 >= 2n-1), three radix-2 FFTs. All
 * buffers bump-carved from the caller arena. */
static srmech_status_t fft_bluestein(const double *in, double *out, size_t n,
                                     int inverse, double *ws, size_t cap,
                                     size_t *off)
{
    size_t m = fft_next_pow2(2u * n - 1u);
    double *b = fft_bump(ws, cap, off, 2u * n);
    double *ap = fft_bump(ws, cap, off, 2u * m);
    double *v = fft_bump(ws, cap, off, 2u * m);
    double *fa = fft_bump(ws, cap, off, 2u * m);
    double *fv = fft_bump(ws, cap, off, 2u * m);
    double *cv = fft_bump(ws, cap, off, 2u * m);
    double *tw = fft_bump(ws, cap, off, m);
    srmech_status_t st;
    assert(in != NULL);
    assert(out != NULL);
    if (b == NULL || ap == NULL || v == NULL || fa == NULL || fv == NULL
        || cv == NULL || tw == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    st = fft_chirp(b, n, inverse);
    if (st != SRMECH_OK) {
        return st;
    }
    fft_bluestein_prepare(in, n, m, b, ap, v);
    st = fft_radix2(ap, fa, m, 0, tw);            /* FA = FFT(a)         */
    if (st != SRMECH_OK) {
        return st;
    }
    st = fft_radix2(v, fv, m, 0, tw);             /* FV = FFT(v)         */
    if (st != SRMECH_OK) {
        return st;
    }
    fft_pointwise_mul(fa, fv, m);
    st = fft_radix2(fa, cv, m, 1, tw);            /* conv = IFFT(FA.FV)  */
    if (st != SRMECH_OK) {
        return st;
    }
    fft_bluestein_finish(b, cv, n, inverse, out);
    return SRMECH_OK;
}

size_t srmech_fft_c128_ws_bound(size_t n)
{
    assert(n <= SIZE_MAX / 2u);                   /* 2n must not overflow */
    if (n <= 1u) {
        return sizeof(double);                    /* trivial; nonzero     */
    }
    if (FFT_POW2(n)) {
        return n * sizeof(double);                /* n/2-root twiddle tbl */
    }
    size_t m = fft_next_pow2(2u * n - 1u);
    assert(m >= n);                               /* covers the n taps    */
    /* b(2n) + apad(2m) + v(2m) + fa(2m) + fv(2m) + cv(2m) + tw(m) */
    size_t doubles = 2u * n + 11u * m;
    return doubles * sizeof(double);
}

srmech_status_t srmech_fft_c128(const double *in_interleaved, size_t n,
                                int inverse, double *out_interleaved,
                                double *ws, size_t ws_len)
{
    assert(n == 0u || in_interleaved != NULL);
    assert(n == 0u || out_interleaved != NULL);
    if (n == 0u) {
        return SRMECH_OK;                         /* empty signal, no write */
    }
    if (in_interleaved == NULL || out_interleaved == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (in_interleaved == out_interleaved) {
        return SRMECH_ERR_BAD_INPUT;              /* out must not alias in */
    }
    size_t cap = ws_len / sizeof(double);
    size_t off = 0u;
    if (FFT_POW2(n)) {
        double *tw = fft_bump(ws, cap, &off, (n >= 2u) ? n : 1u);
        if (tw == NULL) {
            return SRMECH_ERR_OVERFLOW;
        }
        return fft_radix2(in_interleaved, out_interleaved, n, inverse, tw);
    }
    return fft_bluestein(in_interleaved, out_interleaved, n, inverse,
                         ws, cap, &off);
}
