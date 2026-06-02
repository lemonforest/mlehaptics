/*
 * srmech_simd.c — implementation of the SIMD optimize-path HAL.
 *
 * The single home of the cpuid / xgetbv feature-detection logic and the
 * dispatch-tier env-override idiom. See srmech_simd.h for the contract and
 * the rationale (keep machine-specific bits OUT of the portable core).
 *
 * JPL Power-of-Ten: Rule 1 (no goto / recursion); Rule 3 (no malloc); Rule 4
 * (<=60-line functions); Rule 5 (>=2 asserts per non-exempt function — the
 * three has_*() cpuid probes are the documented exempt feature-detectors, see
 * c/JPL_AUDIT.md; srmech_simd_tier is NOT exempt and carries its asserts);
 * Rule 8 (no multi-line macros); Rule 10 (-Werror / /WX). ABI: no exported
 * symbol (internal TU) — SRMECH_ABI_VERSION unaffected.
 *
 * License: GPL-3.0-or-later.
 */

#include "srmech_simd.h"

#include <assert.h>
#include <stdlib.h>   /* getenv, atoi (_CRT_SECURE_NO_WARNINGS set by CMake) */

/* AVX2: leaf1 ECX bit28 (AVX) + bit27 (OSXSAVE) + xgetbv XCR0&0x6==0x6
 * (OS saves YMM) + leaf7 EBX bit5 (AVX2). JPL Rule 5 EXEMPT (feature
 * detector; no pointer/bounds invariant to assert). */
int srmech_simd_has_avx2(void)
{
#if !SRMECH_SIMD_X86
    return 0;
#elif defined(_MSC_VER)
    int regs[4];
    __cpuid(regs, 1);
    const int osxsave = (regs[2] >> 27) & 1;
    const int avx = (regs[2] >> 28) & 1;
    if (!osxsave || !avx) { return 0; }
    if ((_xgetbv(0) & 0x6u) != 0x6u) { return 0; }
    __cpuidex(regs, 7, 0);
    return (regs[1] >> 5) & 1;
#else
    return __builtin_cpu_supports("avx2") ? 1 : 0;
#endif
}

/* AVX (256-bit DOUBLE): leaf1 ECX bit28 (AVX) + bit27 (OSXSAVE) + xgetbv
 * XCR0&0x6==0x6. JPL Rule 5 EXEMPT (feature detector). */
int srmech_simd_has_avx(void)
{
#if !SRMECH_SIMD_X86
    return 0;
#elif defined(_MSC_VER)
    int regs[4];
    __cpuid(regs, 1);
    const int osxsave = (regs[2] >> 27) & 1;
    const int avx = (regs[2] >> 28) & 1;
    if (!osxsave || !avx) { return 0; }
    return ((_xgetbv(0) & 0x6u) == 0x6u) ? 1 : 0;
#else
    return __builtin_cpu_supports("avx") ? 1 : 0;
#endif
}

/* SSE2 is the guaranteed baseline of x86-64 (and assumed on the i386 path,
 * matching the prior "SSE2 is baseline" dispatch). JPL Rule 5 EXEMPT
 * (trivial constant feature detector). */
int srmech_simd_has_sse2(void)
{
#if SRMECH_SIMD_X86
    return 1;
#else
    return 0;
#endif
}

/* Env-override + clamp. NOT Rule-5 exempt — carries its invariants. */
int srmech_simd_tier(const char *env_var, int detected, int max_tier)
{
    assert(env_var != NULL);
    assert(max_tier >= 0);
    const char *force = getenv(env_var);
    const int want = (force != NULL) ? atoi(force) : detected;
    if (want < 0) { return 0; }
    if (want > max_tier) { return max_tier; }
    return want;
}
