/*
 * srmech_jpeg.c — C parity for the NUMERIC JPEG-like block-DCT compression
 * pipeline (0.9.0rc213; task #753 — the float-DCT numeric op deferred out of
 * the rc144/B6b exact coder batch, now given its dedicated numeric C peer).
 *
 * THE OP. JPEG (lossy block-wise compression) IS a Class L (DCT-II eigenbasis
 * projection on bs×bs blocks) ∘ Class K (threshold quantisation) ∘ Class B
 * (byte-canonical coefficient form) composition. Per block X:
 *
 *   encode: Z = (2·B₂·X)·(2·B₂ᵀ)          (separable 2-D DCT-II, cols then rows)
 *           out = round_half_even(Z ⊘ QT)  (Class-K quantise, banker's rounding)
 *   decode: D = Q ⊙ QT                     (dequantise)
 *           Y = dct3(dct3(D, cols), rows)  (DCT-III with the weight-1 j==0 term)
 *           out = Y / (2·bs)²              (the DCT-III normalisation)
 *
 * The cosine bases B₂ / B₃ are CALLER inputs (the Python side builds them once
 * through the byte-exact Class-N rational.cos cascade — the SAME basis the pure
 * path uses, so there is no basis-derivation drift between the two paths; a
 * bare-C host builds them from the shipped libm-free srmech_cos). This is the
 * rc149 iir precedent (b/a taps are caller data; the kernel is the loop).
 *
 * WHY A NEW SYMBOL (not a composition). The pipeline is BLOCKED + FUSED:
 * strided bs×bs block extraction from the image, two basis multiplies, and the
 * elementwise quantise — per block. Routed through the generic dense matmul it
 * costs 4 Python-glue dispatches PER BLOCK (the rc155 composition_of_c shape:
 * jpeg → dct.op ×2 per axis → mat_matvec per row/col), which re-crosses the
 * ctypes boundary O(bh·bw) times and rebuilds the basis per call. The blocked
 * pipeline over caller buffers is the minimal genuinely-new numeric kernel —
 * ONE crossing for the whole image.
 *
 * NUMERIC (FPU-tol), NOT byte-exact — the stage accumulations may FMA-fuse
 * ~1 ULP on some platforms (macOS clang), so the Python parity contract is
 * WITHIN-TOL (reldiff ≤ 1e-9) on the reconstructed image, matching the F1-FFT /
 * F2-SVD / B4 numeric-foundation contract. The quantised coefficients are
 * integers and agree exactly away from rounding boundaries (the parity test
 * asserts its fixtures sit away from half-integer boundaries first). The
 * round-half-to-even quantiser is the exact C twin of Python round() — an
 * integer-truncate + tie-to-even branch, no libm rint(), no fabs()/abs()
 * (Class-K pin-slot sign branches only).
 *
 * HONEST CASCADE SHAPE. Class L (the two cosine-basis multiplies) ∘ Class K
 * (the quantise threshold / sign-branch rounding) ∘ Class B (the block-ordered
 * coefficient layout). No abs(), no libm, no privileged new primitive class.
 *
 * THREAD/STATE. Pure functions over caller buffers; all scratch is bump-carved
 * from the CALLER arena `ws` (>= srmech_jpeg_ws_bound(bs) bytes; JPL Rule 3 —
 * no malloc). `out` MUST NOT alias the input. No shared static state; reentrant.
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto / recursion): early returns; flat nested loops.
 *   - Rule 2 (bounded loops)       : every loop bounded by bs / bh / bw / blk.
 *   - Rule 3 (no malloc)           : caller arena only (2·bs² doubles).
 *   - Rule 4 (<=60 lines/func)     : split into small stage helpers.
 *   - Rule 5 (>=2 asserts/fn)      : pointer / bound pre-conditions.
 *   - Rule 7 (return-value)        : srmech_status_t on the public surface.
 *   - Rule 8 (no multi-line macro) : none defined.
 *   - Rule 10 (warnings clean)     : -Wall -Wextra -Wpedantic -Werror / /WX.
 *
 * ABI: new symbols only — SRMECH_ABI_VERSION stays 4 (additive; the Python
 * ctypes shim hasattr-guards them).
 *
 * License: MIT (parent project: mlehaptics).
 */

#include "srmech.h"

#include <assert.h>
#include <stddef.h>
#include <stdint.h>

/* Round-half-to-even (banker's rounding) — the exact C twin of Python
 * round(). |v| < 2^62 is guaranteed by the caller (jpeg_quantise guards),
 * so the truncating cast is well-defined. Class-K pin-slot sign handling:
 * explicit sign branches, no fabs()/abs(), no libm rint(). */
static double jpeg_round_half_even(double v)
{
    long long t = (long long)v;            /* trunc toward zero            */
    double frac = v - (double)t;
    assert(frac > -1.0 && frac < 1.0);     /* trunc left a proper fraction */
    assert((double)t + frac == v);         /* exact split (|v| < 2^52 + )  */
    if (frac > 0.5 || (frac == 0.5 && (t % 2LL != 0LL))) {
        t += 1LL;
    } else if (frac < -0.5 || (frac == -0.5 && (t % 2LL != 0LL))) {
        t -= 1LL;
    }
    return (double)t;
}

/* DCT stage over the COLUMNS of a bs×bs block (the Python dct axis=0):
 *   out[k][c] = 2·Σ_j basis[k][j]·in[j][c]  (− basis[k][0]·in[0][c] if dct3)
 * dct3 != 0 applies the DCT-III weight-1 j==0 correction (2·raw over-counts
 * the cos(0) term by basis[k][0]·x₀ — see closed_form_ops.dct._transform). */
static void jpeg_stage_cols(const double *in, const double *basis,
                            size_t bs, int dct3, double *out)
{
    assert(in != NULL && basis != NULL);
    assert(out != NULL && out != in);
    for (size_t k = 0u; k < bs; ++k) {
        for (size_t c = 0u; c < bs; ++c) {
            double acc = 0.0;
            for (size_t j = 0u; j < bs; ++j) {
                acc += basis[k * bs + j] * in[j * bs + c];
            }
            double v = 2.0 * acc;
            if (dct3 != 0) {
                v -= basis[k * bs] * in[c];
            }
            out[k * bs + c] = v;
        }
    }
}

/* DCT stage over the ROWS of a bs×bs block (the Python dct axis=1):
 *   out[r][k] = 2·Σ_j basis[k][j]·in[r][j]  (− basis[k][0]·in[r][0] if dct3) */
static void jpeg_stage_rows(const double *in, const double *basis,
                            size_t bs, int dct3, double *out)
{
    assert(in != NULL && basis != NULL);
    assert(out != NULL && out != in);
    for (size_t r = 0u; r < bs; ++r) {
        for (size_t k = 0u; k < bs; ++k) {
            double acc = 0.0;
            for (size_t j = 0u; j < bs; ++j) {
                acc += basis[k * bs + j] * in[r * bs + j];
            }
            double v = 2.0 * acc;
            if (dct3 != 0) {
                v -= basis[k * bs] * in[r * bs];
            }
            out[r * bs + k] = v;
        }
    }
}

/* Class-K quantise of one transformed block: dst = round_half_even(z ⊘ qt).
 * qt entries are pre-validated nonzero by the caller. A quotient at or past
 * 2^62 would make the rounding cast undefined -> OVERFLOW-not-wrap. */
static srmech_status_t jpeg_quantise(const double *z, const double *qt,
                                     size_t blk, double *dst)
{
    assert(z != NULL && qt != NULL);
    assert(dst != NULL);
    const double lim = (double)(1LL << 62);
    for (size_t idx = 0u; idx < blk; ++idx) {
        double scaled = z[idx] / qt[idx];
        if (scaled >= lim || scaled <= -lim) {
            return SRMECH_ERR_OVERFLOW;
        }
        dst[idx] = jpeg_round_half_even(scaled);
    }
    return SRMECH_OK;
}

/* Shared argument validation for encode/decode: block size sane (2·bs²·8
 * bytes must not wrap), arena large enough, quant table all-nonzero, and the
 * block-grid count bh·bw must not wrap. Returns SRMECH_OK to proceed. */
static srmech_status_t jpeg_validate(const double *basis, const double *qt,
                                     size_t bs, size_t bh, size_t bw,
                                     const double *ws, size_t ws_len)
{
    if (basis == NULL || qt == NULL || ws == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(basis != NULL && qt != NULL && ws != NULL);
    if (bs == 0u || bs > SIZE_MAX / bs / (2u * sizeof(double))) {
        return SRMECH_ERR_BAD_INPUT;               /* 2·bs²·8 would wrap    */
    }
    if (bh != 0u && bw > SIZE_MAX / bh) {
        return SRMECH_ERR_BAD_INPUT;               /* bh·bw would wrap      */
    }
    if (ws_len < srmech_jpeg_ws_bound(bs)) {
        return SRMECH_ERR_OVERFLOW;                /* under-sized arena     */
    }
    const size_t blk = bs * bs;
    for (size_t idx = 0u; idx < blk; ++idx) {
        if (qt[idx] == 0.0) {
            return SRMECH_ERR_BAD_INPUT;           /* quantise divides by qt */
        }
    }
    assert(blk <= SIZE_MAX / (2u * sizeof(double)));
    return SRMECH_OK;
}

size_t srmech_jpeg_ws_bound(size_t bs)
{
    if (bs == 0u) {
        return 0u;
    }
    assert(bs <= SIZE_MAX / bs);                   /* bs² must not wrap     */
    const size_t blk = bs * bs;
    assert(blk <= SIZE_MAX / (2u * sizeof(double)));
    return 2u * blk * sizeof(double);              /* block + stage scratch */
}

srmech_status_t srmech_jpeg_encode_f64(
    const double *image, size_t h, size_t w,
    const double *basis2, const double *qt, size_t bs,
    double *out, double *ws, size_t ws_len)
{
    const size_t bh = (bs != 0u) ? h / bs : 0u;
    const size_t bw = (bs != 0u) ? w / bs : 0u;
    srmech_status_t st = jpeg_validate(basis2, qt, bs, bh, bw, ws, ws_len);
    if (st != SRMECH_OK) {
        return st;
    }
    if (bh == 0u || bw == 0u) {
        return SRMECH_OK;                          /* no full block: no-op  */
    }
    if (image == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(image != out);                          /* out must not alias in */
    assert(ws_len >= 2u * bs * bs * sizeof(double));
    const size_t blk = bs * bs;
    double *blkbuf = ws;                           /* bump-carve: block     */
    double *tmp = ws + blk;                        /* bump-carve: stage tmp */
    for (size_t bi = 0u; bi < bh; ++bi) {
        for (size_t bj = 0u; bj < bw; ++bj) {
            for (size_t r = 0u; r < bs; ++r) {     /* strided block extract */
                const double *src = image + (bi * bs + r) * w + bj * bs;
                for (size_t c = 0u; c < bs; ++c) {
                    blkbuf[r * bs + c] = src[c];
                }
            }
            jpeg_stage_cols(blkbuf, basis2, bs, 0, tmp);
            jpeg_stage_rows(tmp, basis2, bs, 0, blkbuf);
            st = jpeg_quantise(blkbuf, qt, blk, out + (bi * bw + bj) * blk);
            if (st != SRMECH_OK) {
                return st;
            }
        }
    }
    return SRMECH_OK;
}

srmech_status_t srmech_jpeg_decode_f64(
    const double *qblocks, size_t bh, size_t bw,
    const double *basis3, const double *qt, size_t bs,
    double *out, double *ws, size_t ws_len)
{
    srmech_status_t st = jpeg_validate(basis3, qt, bs, bh, bw, ws, ws_len);
    if (st != SRMECH_OK) {
        return st;
    }
    if (bh == 0u || bw == 0u) {
        return SRMECH_OK;                          /* zero blocks: no-op    */
    }
    if (qblocks == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(qblocks != out);                        /* out must not alias in */
    assert(ws_len >= 2u * bs * bs * sizeof(double));
    const size_t blk = bs * bs;
    const size_t width = bw * bs;                  /* bw·bs <= w <= SIZE_MAX */
    const double norm = 1.0 / ((2.0 * (double)bs) * (2.0 * (double)bs));
    double *d = ws;                                /* bump-carve: dequant   */
    double *tmp = ws + blk;                        /* bump-carve: stage tmp */
    for (size_t bi = 0u; bi < bh; ++bi) {
        for (size_t bj = 0u; bj < bw; ++bj) {
            const double *src = qblocks + (bi * bw + bj) * blk;
            for (size_t idx = 0u; idx < blk; ++idx) {
                d[idx] = src[idx] * qt[idx];       /* dequantise            */
            }
            jpeg_stage_cols(d, basis3, bs, 1, tmp);
            jpeg_stage_rows(tmp, basis3, bs, 1, d);
            for (size_t r = 0u; r < bs; ++r) {     /* normalise + scatter   */
                double *dst = out + (bi * bs + r) * width + bj * bs;
                for (size_t c = 0u; c < bs; ++c) {
                    dst[c] = d[r * bs + c] * norm;
                }
            }
        }
    }
    return SRMECH_OK;
}
