/* cs_bitboard4d.c — implementation of cs_bitboard4d.h.
 *
 * Pure-C, no external deps. Compiles into a shared library shipped
 * alongside the chess_spectral wheel under ``chess_spectral/_native/``.
 * The Python ctypes wrapper (``chess_spectral._native_bitboard4d``)
 * dlopens it at import; if it isn't present (sdist install without
 * the C toolchain, Pyodide without our WASM build, etc.), the
 * pure-Python ``Bitboard4D`` carries on unchanged.
 *
 * Per-platform notes:
 *   - GCC / Clang: ``__builtin_popcountll`` is hardware popcount on
 *     CPUs with POPCNT; fallback to a software mask-and-add otherwise.
 *   - MSVC: ``__popcnt64`` requires SSE 4.2 / hardware popcount; we
 *     wrap it conditionally and fall back to a software popcount when
 *     compiled without /arch:AVX2 or on older CPUs.
 *
 * No undefined behaviour: ``sq`` validation is the caller's job.
 * Per CS_BB4_ABI_VERSION discipline, any change to function signatures
 * or storage layout must bump CS_BB4_ABI_VERSION (in the header) so
 * the Python wrapper rejects mismatched binaries.
 */

#include "cs_bitboard4d.h"

#include <stddef.h>

/* MSVC popcount intrinsic. Pulled in unconditionally on MSVC builds
 * (rather than from inside the popcount64 body) because the C++
 * frontend treats `#include` inside a function body more strictly
 * than the C frontend. The header is harmless on non-x64 MSVC
 * targets (no AVX/SSE-only declarations referenced). On gcc / clang
 * the __builtin_popcountll path is taken and this header isn't
 * needed. */
#if defined(_MSC_VER) && (defined(_M_X64) || defined(_M_AMD64))
#include <intrin.h>
#endif

/* Note: deliberately NOT including <string.h>. MSVC + Windows SDK
 * 10.0.26100 + strict C17 (CMAKE_C_EXTENSIONS OFF) trips a known
 * compiler bug where <string.h> -> <malloc.h> chain pulls in C23-era
 * SAL annotations that strict C17 mis-parses (errors on `_Ptr`,
 * `_Memory`, `_Size` identifiers). The bug doesn't reproduce with
 * MSVC + older SDKs or with extensions enabled, but the existing
 * tree's CMakeLists pins strict C17 globally, so we work around it
 * by avoiding the entire memcpy/memcmp surface and writing the
 * 64-uint64 byte-compare inline. Trivial loop; identical perf. */

/* MSVC route: this file is compiled as C++ on MSVC (see CMakeLists)
 * to sidestep the SAL-annotation / SIMD-intrinsic dialect mismatch
 * the strict-C MSVC frontend hits against Windows SDK 10.0.26100+.
 * The header wraps its API in `extern "C"`, but the function
 * DEFINITIONS need a matching extern "C" block here so name mangling
 * doesn't break the ABI when the file goes through the C++ frontend.
 * On C compilers the block is invisible (no __cplusplus). */
#ifdef __cplusplus
extern "C" {
#endif

/* Population count of one 64-bit word. */
static inline int popcount64(uint64_t x) {
#if defined(__GNUC__) || defined(__clang__)
    return __builtin_popcountll(x);
#elif defined(_MSC_VER) && (defined(_M_X64) || defined(_M_AMD64))
    /* MSVC intrinsic; <intrin.h> included at the top of the file. */
    return (int) __popcnt64(x);
#else
    /* Software popcount: SWAR algorithm (Hacker's Delight 5-1). */
    x = x - ((x >> 1) & 0x5555555555555555ULL);
    x = (x & 0x3333333333333333ULL) + ((x >> 2) & 0x3333333333333333ULL);
    x = (x + (x >> 4)) & 0x0f0f0f0f0f0f0f0fULL;
    return (int) ((x * 0x0101010101010101ULL) >> 56);
#endif
}

int cs_bb4_popcount(const uint64_t *bits) {
    int total = 0;
    for (size_t i = 0; i < CS_BB4_N_WORDS; ++i) {
        total += popcount64(bits[i]);
    }
    return total;
}

void cs_bb4_and(uint64_t *out, const uint64_t *a, const uint64_t *b) {
    for (size_t i = 0; i < CS_BB4_N_WORDS; ++i) {
        out[i] = a[i] & b[i];
    }
}

void cs_bb4_or(uint64_t *out, const uint64_t *a, const uint64_t *b) {
    for (size_t i = 0; i < CS_BB4_N_WORDS; ++i) {
        out[i] = a[i] | b[i];
    }
}

void cs_bb4_xor(uint64_t *out, const uint64_t *a, const uint64_t *b) {
    for (size_t i = 0; i < CS_BB4_N_WORDS; ++i) {
        out[i] = a[i] ^ b[i];
    }
}

void cs_bb4_not(uint64_t *out, const uint64_t *a) {
    for (size_t i = 0; i < CS_BB4_N_WORDS; ++i) {
        out[i] = ~a[i];
    }
}

void cs_bb4_sub(uint64_t *out, const uint64_t *a, const uint64_t *b) {
    /* Set difference: a & ~b. */
    for (size_t i = 0; i < CS_BB4_N_WORDS; ++i) {
        out[i] = a[i] & ~b[i];
    }
}

void cs_bb4_set_square(uint64_t *bits, int sq) {
    bits[sq >> 6] |= (uint64_t) 1 << (sq & 63);
}

void cs_bb4_clear_square(uint64_t *bits, int sq) {
    bits[sq >> 6] &= ~((uint64_t) 1 << (sq & 63));
}

void cs_bb4_toggle_square(uint64_t *bits, int sq) {
    bits[sq >> 6] ^= (uint64_t) 1 << (sq & 63);
}

int cs_bb4_test_square(const uint64_t *bits, int sq) {
    return (bits[sq >> 6] >> (sq & 63)) & 1ULL;
}

int cs_bb4_is_empty(const uint64_t *bits) {
    for (size_t i = 0; i < CS_BB4_N_WORDS; ++i) {
        if (bits[i] != 0) return 0;
    }
    return 1;
}

int cs_bb4_is_full(const uint64_t *bits) {
    for (size_t i = 0; i < CS_BB4_N_WORDS; ++i) {
        if (bits[i] != ~(uint64_t) 0) return 0;
    }
    return 1;
}

int cs_bb4_equals(const uint64_t *a, const uint64_t *b) {
    /* Inline byte-compare; see top-of-file note for why memcmp is avoided. */
    for (size_t i = 0; i < CS_BB4_N_WORDS; ++i) {
        if (a[i] != b[i]) return 0;
    }
    return 1;
}

int cs_bb4_intersects(const uint64_t *a, const uint64_t *b) {
    for (size_t i = 0; i < CS_BB4_N_WORDS; ++i) {
        if ((a[i] & b[i]) != 0) return 1;
    }
    return 0;
}

/* Index of the lowest set bit (0..63). Caller guarantees x != 0. */
static inline int ctz64(uint64_t x) {
#if defined(__GNUC__) || defined(__clang__)
    return __builtin_ctzll(x);
#elif defined(_MSC_VER) && (defined(_M_X64) || defined(_M_AMD64))
    /* MSVC intrinsic; <intrin.h> included at the top of the file. */
    unsigned long idx;
    _BitScanForward64(&idx, x);
    return (int) idx;
#else
    /* Software: De Bruijn sequence. Hacker's Delight 5-3.
     * 64-bit De Bruijn constant 0x03f79d71b4cb0a89; table maps
     * the high 6 bits of (lsb * constant) to the bit index. */
    static const int kDebruijn64Index[64] = {
         0,  1, 56,  2, 57, 49, 28,  3,
        61, 58, 42, 50, 38, 29, 17,  4,
        62, 47, 59, 36, 45, 43, 51, 22,
        53, 39, 33, 30, 24, 18, 12,  5,
        63, 55, 48, 27, 60, 41, 37, 16,
        46, 35, 44, 21, 52, 32, 23, 11,
        54, 26, 40, 15, 34, 20, 31, 10,
        25, 14, 19,  9, 13,  8,  7,  6
    };
    uint64_t lsb = x & (uint64_t)(-(int64_t)x);
    return kDebruijn64Index[(lsb * 0x03f79d71b4cb0a89ULL) >> 58];
#endif
}

int cs_bb4_to_squares(int *out_squares, const uint64_t *bits) {
    int count = 0;
    for (size_t w = 0; w < CS_BB4_N_WORDS; ++w) {
        uint64_t b = bits[w];
        int word_offset = (int) (w * 64);
        while (b) {
            out_squares[count++] = word_offset + ctz64(b);
            b &= b - 1;  /* clear lowest set bit */
        }
    }
    return count;
}

int cs_bb4_abi_version(void) {
    return CS_BB4_ABI_VERSION;
}

#ifdef __cplusplus
}  /* extern "C" */
#endif
