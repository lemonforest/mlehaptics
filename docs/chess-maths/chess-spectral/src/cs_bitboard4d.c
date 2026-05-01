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
#include <string.h>

/* Population count of one 64-bit word. */
static inline int popcount64(uint64_t x) {
#if defined(__GNUC__) || defined(__clang__)
    return __builtin_popcountll(x);
#elif defined(_MSC_VER) && (defined(_M_X64) || defined(_M_AMD64))
    /* MSVC intrinsic; _M_X64 is 64-bit Windows. */
    #include <intrin.h>
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
    return memcmp(a, b, CS_BB4_N_WORDS * sizeof(uint64_t)) == 0;
}

int cs_bb4_intersects(const uint64_t *a, const uint64_t *b) {
    for (size_t i = 0; i < CS_BB4_N_WORDS; ++i) {
        if ((a[i] & b[i]) != 0) return 1;
    }
    return 0;
}

int cs_bb4_abi_version(void) {
    return CS_BB4_ABI_VERSION;
}
