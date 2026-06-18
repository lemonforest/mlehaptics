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
 * License: MIT.
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
/* SHA-NI uses the SHA extensions plus SSE4.1 (_mm_blend_epi16) and SSSE3
 * (_mm_shuffle_epi8 / _mm_alignr_epi8); name all three so gcc/clang emit the
 * codegen from a baseline TU. MSVC emits the intrinsics regardless -> empty. */
#  define SRMECH_SIMD_TARGET_SHANI __attribute__((target("sha,sse4.1,ssse3")))
#else
#  define SRMECH_SIMD_TARGET_AVX2
#  define SRMECH_SIMD_TARGET_AVX
#  define SRMECH_SIMD_TARGET_SSE2
#  define SRMECH_SIMD_TARGET_SHANI
#endif

/* Can THIS toolchain compile the SHA-NI kernel? MSVC always; gcc/clang iff
 * <shaintrin.h> is available (the SHA Extensions intrinsics live there, and
 * `target("sha")` works wherever they do). An x86 toolchain too old to ship
 * the header (or non-x86) degrades to the scalar-only path — the public
 * srmech_sha256_shani symbol still exists, just never enters the kernel. */
#if SRMECH_SIMD_X86 && defined(_MSC_VER)
#  define SRMECH_SIMD_SHANI_KERNEL 1
#elif SRMECH_SIMD_X86 && defined(__has_include)
#  if __has_include(<shaintrin.h>)
#    define SRMECH_SIMD_SHANI_KERNEL 1
#  endif
#endif
#ifndef SRMECH_SIMD_SHANI_KERNEL
#  define SRMECH_SIMD_SHANI_KERNEL 0
#endif

/* ────────────────────────────────────────────────────────────────────
 * ATTESTATION (MPR v1) — the cpuid leaf/bit numbers + the target-attribute
 * feature strings below are externally-defined magic, NOT srmech-derived.
 * Implemented in srmech_simd.c; attested here at the HAL header per the
 * rc19 constant-attestation discipline.
 *
 *   data         : x86 CPU-feature detection bit positions + GCC/Clang
 *                  function target-attribute strings.
 *   source       : Intel® 64 and IA-32 Architectures Software Developer's
 *                  Manual, Vol 2A — CPUID instruction (+ Vol 1 §13 for the
 *                  XSAVE/XCR0 OS-enable handshake).
 *     · CPUID leaf 1 ECX bit 27 = OSXSAVE, bit 28 = AVX.
 *     · CPUID leaf 7 sub-leaf 0 EBX bit 5 = AVX2, bit 29 = SHA.
 *     · XGETBV XCR0[1] (SSE) & XCR0[2] (AVX) must both be set (==0x6)
 *       before YMM use — the OS-saves-the-state gate for AVX/AVX2.
 *       SHA-NI uses XMM only, so it has NO XGETBV gate.
 *   target_attrs : GCC/Clang function attribute target("…") strings
 *                  ("avx2" / "avx" / "sse2" / "sha,sse4.1,ssse3") per the
 *                  GCC "x86 Function Attributes" manual — the names that
 *                  let a baseline-compiled TU emit per-function SIMD.
 *   verification : the probes are exercised through every dispatch tier by
 *                  the per-op FORCE_TIER hooks (tests/test_sha256_batch.py,
 *                  tests/test_sha256_shani.py) + the CI cpuid-dump step that
 *                  records which runners carry each feature.
 *   retrieved_at : 2026-06-03
 *   cite_as      : "Intel SDM Vol 2A (CPUID) + Vol 1 §13 (XSAVE); GCC x86
 *                  Function Attributes."
 * ────────────────────────────────────────────────────────────────────
 *
 * Runtime cpuid feature probes — the SINGLE source of the OSXSAVE /
 * xgetbv / leaf-7 logic. Each returns 1 if the host (and OS, for the
 * 256-bit features) supports it, else 0. On non-x86 all return 0,
 * EXCEPT has_sse2 which also returns 0 (no SSE2 off x86). SSE2 is the
 * guaranteed baseline of x86-64, so has_sse2() is 1 on any SRMECH_SIMD_X86.
 * ------------------------------------------------------------------ */
int srmech_simd_has_avx2(void);
int srmech_simd_has_avx(void);
int srmech_simd_has_sse2(void);
/* SHA-NI (Intel SHA Extensions). 1 if the host supports the SHA feature
 * (leaf7 EBX bit29), else 0; always 0 off x86. No OS-state gate needed. */
int srmech_simd_has_shani(void);

/* Dispatch-tier helper — the env-override + clamp idiom in one place.
 * If `env_var` is set in the environment, returns atoi(value) clamped to
 * [0, max_tier] (the per-op test hook, e.g. SRMECH_SHA256_FORCE_TIER). If
 * unset, returns `detected` clamped to [0, max_tier]. The caller computes
 * `detected` from the relevant srmech_simd_has_*() probes, so the meaning of
 * each tier integer stays op-local (tier 2 = AVX2 for sha256, AVX for the
 * f64 loop-bind). */
int srmech_simd_tier(const char *env_var, int detected, int max_tier);

#endif /* SRMECH_SIMD_H */
