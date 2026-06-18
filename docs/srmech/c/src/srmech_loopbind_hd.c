/*
 * srmech_loopbind_hd.c — SIMD batch for the block-octonion HD bind
 * (MS#21 v0.7.0rc11; F292 graft #2, the on-theme one).
 *
 * `loop_bind_hd` is the direct sum of NB INDEPENDENT dim-8 octonion products
 * (block-diagonal; F289 D1 verified err 0.0). That IS the data-parallel shape
 * cpuminer's N-way SIMD exploits: N independent units advanced in lockstep
 * across SIMD lanes. The block-diagonal structure F289 established is a SIMD
 * invitation — the cpuminer N-way mindset applied to the octonion substrate.
 * Until now `loop_bind_hd` (srmech.amsc.hdc) looped over the NB blocks in
 * PYTHON, one ctypes call per block; this collapses it to ONE native call
 * that processes W blocks per SIMD pass.
 *
 * MECHANISM. `srmech_loop_bind_hd_f64` binds NB blocks (x, y, out are each
 * NB*8 doubles). On x86 it dispatches at runtime to AVX (256-bit double,
 * W=4 blocks/pass) / SSE2 (128-bit double, W=2), falling back to the scalar
 * per-block path (the remainder NB mod W, non-x86, Pyodide) — which reuses
 * the SHIPPED rc7 `srmech_loop_bind_f64` (so the scalar tier is bit-exact
 * with the single-block product by construction). The SIMD kernels mirror
 * rc7's exact `mul2/mul4/mul8` Cayley-Dickson op-DAG with `double` replaced
 * by a vector holding W blocks of one component — so each LANE is bit-exact
 * with the scalar product modulo a possible 1-ULP FMA-contraction difference
 * (the rc7 bind tolerance). SRMECH_LOOP_HD_FORCE_TIER={0,1,2} overrides the
 * dispatch (test hook). NOTE the 256-bit DOUBLE ops are AVX, not AVX2.
 *
 * HAL. ALL machine-specific bits other than the kernels themselves come from
 * the SIMD optimize-path HAL (srmech_simd.h): the SRMECH_SIMD_X86 platform
 * macro, the arch intrinsic includes, the SRMECH_SIMD_TARGET_* attributes,
 * and the cpuid / env-tier dispatch (srmech_simd_has_avx / srmech_simd_tier).
 * The portable core (srmech_loopbind.c) and the public header stay agnostic.
 *
 * SCOPE / honest shape. Performance-engineering of srmech's own Class-M HD
 * bind, the F292 "apple-tree" graft (technique from cpuminer's N-way SIMD;
 * re-implemented JPL-clean). loop_bind is Class M (bind) with the Class-C
 * (4:3) ordering + Class-K associator residue — unchanged; NO new class, no
 * abs(). NOT mining (this is octonion algebra, not hashing at all).
 *
 * THREAD/STATE. Pure over caller buffers; `out` MUST NOT alias x or y.
 *
 * JPL Power-of-Ten: Rule 1 (no goto / recursion — fixed call DAG); Rule 3
 * (no malloc); Rule 4 (<=60-line functions); Rule 5 (>=2 asserts per non-
 * exempt function; the cpuid / tier probes live in the HAL); Rule 8 (only
 * SINGLE-line vector macros); Rule 10 (-Werror / /WX). ABI: new symbol only
 * -> SRMECH_ABI_VERSION stays 3 (additive).
 *
 * License: MIT.
 */

#include "srmech.h"
#include "srmech_simd.h"

#include <assert.h>
#include <stddef.h>

#define SRMECH_LOOP_DIM ((size_t)8)

#if SRMECH_SIMD_X86

/* ------------------------------------------------------------------ *
 * AVX (256-bit double, W=4 blocks). Single-line vector macros (Rule 8).
 * The vmul* DAG mirrors rc7 srmech_loopbind.c mul2/mul4/mul8 exactly,
 * `double` -> `__m256d` (one component across 4 blocks).
 * ------------------------------------------------------------------ */
#define VA_MUL(a,b) _mm256_mul_pd((a),(b))
#define VA_ADD(a,b) _mm256_add_pd((a),(b))
#define VA_SUB(a,b) _mm256_sub_pd((a),(b))
#define VA_NEG(a)   _mm256_sub_pd(_mm256_setzero_pd(),(a))

SRMECH_SIMD_TARGET_AVX
static void srmech_loophd__mul2a(const __m256d *x, const __m256d *y, __m256d *out)
{
    assert(x != NULL && y != NULL);
    assert(out != NULL);
    out[0] = VA_SUB(VA_MUL(x[0], y[0]), VA_MUL(y[1], x[1]));
    out[1] = VA_ADD(VA_MUL(y[1], x[0]), VA_MUL(x[1], y[0]));
}

SRMECH_SIMD_TARGET_AVX
static void srmech_loophd__mul4a(const __m256d *x, const __m256d *y, __m256d *out)
{
    assert(x != NULL && y != NULL);
    assert(out != NULL);
    const __m256d dconj[2] = { y[2], VA_NEG(y[3]) };
    const __m256d cconj[2] = { y[0], VA_NEG(y[1]) };
    __m256d ac[2], db[2], da[2], bc[2];
    srmech_loophd__mul2a(&x[0], &y[0], ac);
    srmech_loophd__mul2a(dconj, &x[2], db);
    srmech_loophd__mul2a(&y[2], &x[0], da);
    srmech_loophd__mul2a(&x[2], cconj, bc);
    out[0] = VA_SUB(ac[0], db[0]);
    out[1] = VA_SUB(ac[1], db[1]);
    out[2] = VA_ADD(da[0], bc[0]);
    out[3] = VA_ADD(da[1], bc[1]);
}

SRMECH_SIMD_TARGET_AVX
static void srmech_loophd__mul8a(const __m256d *x, const __m256d *y, __m256d *out)
{
    assert(x != NULL && y != NULL);
    assert(out != NULL);
    const __m256d dconj[4] = { y[4], VA_NEG(y[5]), VA_NEG(y[6]), VA_NEG(y[7]) };
    const __m256d cconj[4] = { y[0], VA_NEG(y[1]), VA_NEG(y[2]), VA_NEG(y[3]) };
    __m256d ac[4], db[4], da[4], bc[4];
    srmech_loophd__mul4a(&x[0], &y[0], ac);
    srmech_loophd__mul4a(dconj, &x[4], db);
    srmech_loophd__mul4a(&y[4], &x[0], da);
    srmech_loophd__mul4a(&x[4], cconj, bc);
    for (size_t i = 0; i < 4u; ++i) {
        out[i] = VA_SUB(ac[i], db[i]);
        out[i + 4u] = VA_ADD(da[i], bc[i]);
    }
}

SRMECH_SIMD_TARGET_AVX
static size_t srmech_loophd__avx(const double *x, const double *y,
                                 size_t nb, double *out)
{
    assert(x != NULL && y != NULL);
    assert(out != NULL);
    size_t g = 0;
    for (; g + 4u <= nb; g += 4u) {
        __m256d X[8], Y[8], OUT[8];
        for (size_t c = 0; c < 8u; ++c) {
            X[c] = _mm256_set_pd(x[(g + 3u) * 8u + c], x[(g + 2u) * 8u + c],
                                 x[(g + 1u) * 8u + c], x[g * 8u + c]);
            Y[c] = _mm256_set_pd(y[(g + 3u) * 8u + c], y[(g + 2u) * 8u + c],
                                 y[(g + 1u) * 8u + c], y[g * 8u + c]);
        }
        srmech_loophd__mul8a(X, Y, OUT);
        for (size_t c = 0; c < 8u; ++c) {
            double t[4];
            _mm256_storeu_pd(t, OUT[c]);
            out[g * 8u + c] = t[0];
            out[(g + 1u) * 8u + c] = t[1];
            out[(g + 2u) * 8u + c] = t[2];
            out[(g + 3u) * 8u + c] = t[3];
        }
    }
    return g;
}

/* ------------------------------------------------------------------ *
 * SSE2 (128-bit double, W=2 blocks). Baseline on x86-64.
 * ------------------------------------------------------------------ */
#define VS_MUL(a,b) _mm_mul_pd((a),(b))
#define VS_ADD(a,b) _mm_add_pd((a),(b))
#define VS_SUB(a,b) _mm_sub_pd((a),(b))
#define VS_NEG(a)   _mm_sub_pd(_mm_setzero_pd(),(a))

SRMECH_SIMD_TARGET_SSE2
static void srmech_loophd__mul2s(const __m128d *x, const __m128d *y, __m128d *out)
{
    assert(x != NULL && y != NULL);
    assert(out != NULL);
    out[0] = VS_SUB(VS_MUL(x[0], y[0]), VS_MUL(y[1], x[1]));
    out[1] = VS_ADD(VS_MUL(y[1], x[0]), VS_MUL(x[1], y[0]));
}

SRMECH_SIMD_TARGET_SSE2
static void srmech_loophd__mul4s(const __m128d *x, const __m128d *y, __m128d *out)
{
    assert(x != NULL && y != NULL);
    assert(out != NULL);
    const __m128d dconj[2] = { y[2], VS_NEG(y[3]) };
    const __m128d cconj[2] = { y[0], VS_NEG(y[1]) };
    __m128d ac[2], db[2], da[2], bc[2];
    srmech_loophd__mul2s(&x[0], &y[0], ac);
    srmech_loophd__mul2s(dconj, &x[2], db);
    srmech_loophd__mul2s(&y[2], &x[0], da);
    srmech_loophd__mul2s(&x[2], cconj, bc);
    out[0] = VS_SUB(ac[0], db[0]);
    out[1] = VS_SUB(ac[1], db[1]);
    out[2] = VS_ADD(da[0], bc[0]);
    out[3] = VS_ADD(da[1], bc[1]);
}

SRMECH_SIMD_TARGET_SSE2
static void srmech_loophd__mul8s(const __m128d *x, const __m128d *y, __m128d *out)
{
    assert(x != NULL && y != NULL);
    assert(out != NULL);
    const __m128d dconj[4] = { y[4], VS_NEG(y[5]), VS_NEG(y[6]), VS_NEG(y[7]) };
    const __m128d cconj[4] = { y[0], VS_NEG(y[1]), VS_NEG(y[2]), VS_NEG(y[3]) };
    __m128d ac[4], db[4], da[4], bc[4];
    srmech_loophd__mul4s(&x[0], &y[0], ac);
    srmech_loophd__mul4s(dconj, &x[4], db);
    srmech_loophd__mul4s(&y[4], &x[0], da);
    srmech_loophd__mul4s(&x[4], cconj, bc);
    for (size_t i = 0; i < 4u; ++i) {
        out[i] = VS_SUB(ac[i], db[i]);
        out[i + 4u] = VS_ADD(da[i], bc[i]);
    }
}

SRMECH_SIMD_TARGET_SSE2
static size_t srmech_loophd__sse2(const double *x, const double *y,
                                  size_t nb, double *out)
{
    assert(x != NULL && y != NULL);
    assert(out != NULL);
    size_t g = 0;
    for (; g + 2u <= nb; g += 2u) {
        __m128d X[8], Y[8], OUT[8];
        for (size_t c = 0; c < 8u; ++c) {
            X[c] = _mm_set_pd(x[(g + 1u) * 8u + c], x[g * 8u + c]);
            Y[c] = _mm_set_pd(y[(g + 1u) * 8u + c], y[g * 8u + c]);
        }
        srmech_loophd__mul8s(X, Y, OUT);
        for (size_t c = 0; c < 8u; ++c) {
            double t[2];
            _mm_storeu_pd(t, OUT[c]);
            out[g * 8u + c] = t[0];
            out[(g + 1u) * 8u + c] = t[1];
        }
    }
    return g;
}

#endif /* SRMECH_SIMD_X86 */

/* ------------------------------------------------------------------ *
 * Public entry — declared in srmech.h. Block-diagonal octonion HD bind of
 * `nb` blocks: out[k] = loop_bind(x[k], y[k]) for each 8-block k. x, y, out
 * are each nb*8 doubles; out MUST NOT alias x or y. nb == 0 is a no-op.
 * ------------------------------------------------------------------ */
srmech_status_t srmech_loop_bind_hd_f64(const double *x, const double *y,
                                        size_t nb, double *out)
{
    if (nb > 0u && (x == NULL || y == NULL || out == NULL)) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(nb == 0u || (x != NULL && y != NULL && out != NULL));
    const int detected = srmech_simd_has_avx() ? 2
                       : (srmech_simd_has_sse2() ? 1 : 0);
    const int tier = srmech_simd_tier("SRMECH_LOOP_HD_FORCE_TIER", detected, 2);
    assert(tier >= 0 && tier <= 2);
    size_t k = 0;
#if SRMECH_SIMD_X86
    if (tier == 2) {
        k = srmech_loophd__avx(x, y, nb, out);
    } else if (tier == 1) {
        k = srmech_loophd__sse2(x, y, nb, out);
    }
#else
    (void)tier;
#endif
    /* remainder (and the whole array on non-x86 / forced-scalar) via the
     * shipped rc7 single-block product — bit-exact with loop_bind. */
    for (; k < nb; ++k) {
        const srmech_status_t rc = srmech_loop_bind_f64(
            &x[k * 8u], &y[k * 8u], SRMECH_LOOP_DIM, &out[k * 8u]);
        if (rc != SRMECH_OK) {
            return rc;
        }
    }
    return SRMECH_OK;
}
