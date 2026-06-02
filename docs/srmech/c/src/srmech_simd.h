/*
 * srmech_simd.h — HAL (hardware-abstraction layer) for the SIMD optimize path.
 *
 * THE ONE PLACE machine-specific bits live. The portable CORE reference
 * implementations (srmech_sha256.c, srmech_loopbind.c, …) and the PUBLIC
 * header (c/include/srmech.h) stay 100% machine-agnostic — they never include
 * <immintrin.h>, never name __m256i, never cpuid. Only the per-op optimize
 * TUs (srmech_sha256_batch.c, srmech_loopbind_hd.c, …) include THIS, and they
 * get from it everything arch-specific EXCEPT their own kernels:
 *
 *   - SRMECH_SIMD_X86         1 on x86/x86-64, 0 elsewhere (Pyodide/ARM/WASM)
 *   - the arch intrinsic includes (immintrin / intrin / cpuid), x86 only
 *   - SRMECH_SIMD_TARGET_*    per-function target attributes (empty on MSVC)
 *   - srmech_simd_has_*()     runtime cpuid feature probes (single source of
 *                             the OSXSAVE/xgetbv/leaf-7 logic)
 *   - srmech_simd_tier()      the env-override + clamp dispatch idiom
 *
 * Adding a new optimize-path op (rc12 SHA-NI, an FFT autocorrelation, a
 * cache-blocked Laplacian, …) means: include this header, write the kernels,
 * call srmech_simd_has_*() / srmech_simd_tier() — NO new copy of the detection
 * portability plumbing. That is the abstraction the HAL buys.
 *
 * This is a PRIVATE internal header (lives in c/src/, not c/include/): it is
 * never part of the public API or the ABI surface; downstream ctypes callers
 * never see it.
 *
 * License: GPL-3.0-or-later.
 */
#ifndef SRMECH_SIMD_H
#define SRMECH_SIMD_H

/* x86 detection. The arch intrinsic headers come in HERE so no optimize TU
 * has to repeat the dance. On non-x86 nothing arch-specific is pulled in. */
#if defined(__x86_64__) || defined(_M_X64) || defined(__i386__) || defined(_M_IX86)
#  define SRMECH_SIMD_X86 1
#  include <immintrin.h>
#  if defined(_MSC_VER)
#    include <intrin.h>
#  else
#    include <cpuid.h>
#  endif
#else
#  define SRMECH_SIMD_X86 0
#endif

/* Per-function target attribute. gcc/clang need it to emit AVX2/AVX/SSE2
 * codegen from a baseline TU (the build sets no global -mavx2/-mavx, so the
 * core stays portable); MSVC emits the intrinsics regardless of /arch, so the
 * attribute is empty there. NB: the 256-bit DOUBLE ops (_mm256_*_pd) are AVX,
 * not AVX2 — use SRMECH_SIMD_TARGET_AVX for those. */
#if SRMECH_SIMD_X86 && !defined(_MSC_VER)
#  define SRMECH_SIMD_TARGET_AVX2 __attribute__((target("avx2")))
#  define SRMECH_SIMD_TARGET_AVX  __attribute__((target("avx")))
#  define SRMECH_SIMD_TARGET_SSE2 __attribute__((target("sse2")))
#else
#  define SRMECH_SIMD_TARGET_AVX2
#  define SRMECH_SIMD_TARGET_AVX
#  define SRMECH_SIMD_TARGET_SSE2
#endif

/* ------------------------------------------------------------------ *
 * Runtime cpuid feature probes — the SINGLE source of the OSXSAVE /
 * xgetbv / leaf-7 logic. Each returns 1 if the host (and OS, for the
 * 256-bit features) supports it, else 0. On non-x86 all return 0,
 * EXCEPT has_sse2 which also returns 0 (no SSE2 off x86). SSE2 is the
 * guaranteed baseline of x86-64, so has_sse2() is 1 on any SRMECH_SIMD_X86.
 * ------------------------------------------------------------------ */
int srmech_simd_has_avx2(void);
int srmech_simd_has_avx(void);
int srmech_simd_has_sse2(void);

/* Dispatch-tier helper — the env-override + clamp idiom in one place.
 * If `env_var` is set in the environment, returns atoi(value) clamped to
 * [0, max_tier] (the per-op test hook, e.g. SRMECH_SHA256_FORCE_TIER). If
 * unset, returns `detected` clamped to [0, max_tier]. The caller computes
 * `detected` from the relevant srmech_simd_has_*() probes, so the meaning of
 * each tier integer stays op-local (tier 2 = AVX2 for sha256, AVX for the
 * f64 loop-bind). */
int srmech_simd_tier(const char *env_var, int detected, int max_tier);

#endif /* SRMECH_SIMD_H */
