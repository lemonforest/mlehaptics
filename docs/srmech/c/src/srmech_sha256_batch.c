/*
 * srmech_sha256_batch.c — N-way SIMD SHA-256 batch (F292 graft #1).
 *
 * PERFORMANCE-ENGINEERING of srmech's OWN content-addressing hash, the
 * common AMSC case being "hash many independent records" (bulk
 * attestation: response_sha256 / descriptor_hash / parser_rule_hash over
 * a whole catalog). This is the apple-tree graft of cpuminer's N-way SIMD
 * SHA-256 TECHNIQUE (sha256d_ms_4way / _8way) onto srmech's hash, re-
 * implemented JPL-clean (intrinsics, not asm; no goto; no multi-line
 * macros) and bit-exact with the scalar path / hashlib / NIST KATs.
 *
 * SCOPE: energy/perf-engineering, measured in hashes-per-op. NOT mining —
 * binding does not make hashing cheaper and SHA-256 has no PoW shortcut;
 * this is "a correct instrument," just faster at the bulk case. Technique
 * attested to PUBLIC references (FIPS 180-4 for the algorithm; the Intel
 * Intrinsics Guide + Gueron & Krasnov, "Parallelizing message schedules
 * to accelerate SHA-256" for the N-way-lane structure); cpuminer (GPLv2+,
 * forward-compatible with srmech GPL-3.0+) was read only as a working-impl
 * pointer.
 *
 * MECHANISM. `srmech_sha256_batch` hashes n messages. On x86 with the
 * feature present it processes them W-at-a-time (W=8 AVX2 / W=4 SSE2):
 * the W lanes step through their own message's 512-bit blocks in SIMD
 * lockstep, and a per-lane "active" mask freezes a lane's state once its
 * (shorter) message has consumed all its blocks — so variable-length
 * messages are correct, each lane's state advancing EXACTLY as the scalar
 * one-shot would. The remainder (n mod W) + non-x86 + Pyodide all take the
 * scalar path. SRMECH_SHA256_FORCE_TIER={0,1,2} overrides the cpuid
 * dispatch (test hook; 0=scalar/1=SSE2/2=AVX2) so every tier is parity-
 * exercised on one host.
 *
 * The scalar constants + compress here are a self-contained duplicate of
 * srmech_sha256.c's (kept byte-for-byte in sync; both pinned to the SAME
 * NIST KATs by tests/test_sha256_batch.py + tests/test_native_sha256.py)
 * so this graft touches the proven single-stream file zero.
 *
 * JPL Power-of-Ten: Rule 1 (no goto / no recursion — flat loops); Rule 3
 * (no malloc — bounded stack only); Rule 4 (<=60-line functions); Rule 5
 * (>=2 asserts per non-exempt function; the cpuid / tier probes live in the
 * HAL, srmech_simd.c); Rule 8 (only SINGLE-line macros for the vector sigma
 * ops); Rule 10 (-Wall -Wextra -Wpedantic -Werror / /W4 /WX). ABI: new
 * symbol only -> SRMECH_ABI_VERSION stays 3.
 *
 * License: GPL-3.0-or-later.
 */

#include "srmech.h"
#include "srmech_simd.h"   /* SIMD optimize-path HAL: SRMECH_SIMD_X86,
                            * arch includes, SRMECH_SIMD_TARGET_*, cpuid */

#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

/* ------------------------------------------------------------------ *
 * SHA-256 constants (FIPS 180-4 §4.2.2 / §5.3.3) — duplicate of
 * srmech_sha256.c (kept in sync; both NIST-KAT-pinned).
 * ------------------------------------------------------------------ */
static const uint32_t SRMECH_SHA256B_K[64] = {
    0x428a2f98u, 0x71374491u, 0xb5c0fbcfu, 0xe9b5dba5u,
    0x3956c25bu, 0x59f111f1u, 0x923f82a4u, 0xab1c5ed5u,
    0xd807aa98u, 0x12835b01u, 0x243185beu, 0x550c7dc3u,
    0x72be5d74u, 0x80deb1feu, 0x9bdc06a7u, 0xc19bf174u,
    0xe49b69c1u, 0xefbe4786u, 0x0fc19dc6u, 0x240ca1ccu,
    0x2de92c6fu, 0x4a7484aau, 0x5cb0a9dcu, 0x76f988dau,
    0x983e5152u, 0xa831c66du, 0xb00327c8u, 0xbf597fc7u,
    0xc6e00bf3u, 0xd5a79147u, 0x06ca6351u, 0x14292967u,
    0x27b70a85u, 0x2e1b2138u, 0x4d2c6dfcu, 0x53380d13u,
    0x650a7354u, 0x766a0abbu, 0x81c2c92eu, 0x92722c85u,
    0xa2bfe8a1u, 0xa81a664bu, 0xc24b8b70u, 0xc76c51a3u,
    0xd192e819u, 0xd6990624u, 0xf40e3585u, 0x106aa070u,
    0x19a4c116u, 0x1e376c08u, 0x2748774cu, 0x34b0bcb5u,
    0x391c0cb3u, 0x4ed8aa4au, 0x5b9cca4fu, 0x682e6ff3u,
    0x748f82eeu, 0x78a5636fu, 0x84c87814u, 0x8cc70208u,
    0x90befffau, 0xa4506cebu, 0xbef9a3f7u, 0xc67178f2u
};
static const uint32_t SRMECH_SHA256B_H0[8] = {
    0x6a09e667u, 0xbb67ae85u, 0x3c6ef372u, 0xa54ff53au,
    0x510e527fu, 0x9b05688cu, 0x1f83d9abu, 0x5be0cd19u
};

/* ------------------------------------------------------------------ *
 * Streaming per-message block padder (no malloc). Fills `out[64]` with
 * block index `b` of the FIPS-padded message and returns 1 if that block
 * exists (b < nblocks), else 0. Shared by the scalar + every SIMD lane.
 * nblocks = ceil((len + 1 + 8) / 64) = (len + 72) / 64 — matches
 * srmech_sha256.c's full_blocks + (1 or 2) padding-block accounting.
 * ------------------------------------------------------------------ */
static int srmech_sha256b__fill_block(const uint8_t *msg, size_t len,
                                      size_t b, uint8_t out[64])
{
    assert(out != NULL);
    assert(msg != NULL || len == 0u);

    const size_t nblocks = (len + 72u) / 64u;
    if (b >= nblocks) {
        return 0;
    }
    const uint64_t bit_len = (uint64_t)len * 8u;
    const size_t suffix_off = (nblocks * 64u) - 8u;
    for (size_t p = 0; p < 64u; p++) {
        const size_t off = (b * 64u) + p;
        if (off < len) {
            out[p] = msg[off];
        } else if (off == len) {
            out[p] = 0x80u;
        } else if (off >= suffix_off) {
            const unsigned shift = (unsigned)(56u - (8u * (off - suffix_off)));
            out[p] = (uint8_t)(bit_len >> shift);
        } else {
            out[p] = 0x00u;
        }
    }
    return 1;
}

/* Big-endian load of 16 message-schedule words from a 64-byte block. */
static void srmech_sha256b__load_words(const uint8_t block[64], uint32_t w[16])
{
    assert(block != NULL);
    assert(w != NULL);
    for (size_t i = 0; i < 16u; i++) {
        const size_t j = i * 4u;
        w[i] = ((uint32_t)block[j] << 24) | ((uint32_t)block[j + 1u] << 16)
             | ((uint32_t)block[j + 2u] << 8) | ((uint32_t)block[j + 3u]);
    }
}

/* ------------------------------------------------------------------ *
 * Scalar tier (the oracle + the remainder + the non-x86 path).
 * ------------------------------------------------------------------ */
static uint32_t srmech_sha256b__ror(uint32_t x, unsigned n)
{
    return (x >> n) | (x << (32u - n));
}

static void srmech_sha256b__compress1(uint32_t state[8], const uint8_t block[64])
{
    assert(state != NULL);
    assert(block != NULL);
    uint32_t w[64];
    srmech_sha256b__load_words(block, w);
    for (size_t i = 16; i < 64u; i++) {
        const uint32_t s0 = srmech_sha256b__ror(w[i - 15u], 7) ^ srmech_sha256b__ror(w[i - 15u], 18) ^ (w[i - 15u] >> 3);
        const uint32_t s1 = srmech_sha256b__ror(w[i - 2u], 17) ^ srmech_sha256b__ror(w[i - 2u], 19) ^ (w[i - 2u] >> 10);
        w[i] = w[i - 16u] + s0 + w[i - 7u] + s1;
    }
    uint32_t a = state[0], b = state[1], c = state[2], d = state[3];
    uint32_t e = state[4], f = state[5], g = state[6], h = state[7];
    for (size_t i = 0; i < 64u; i++) {
        const uint32_t bs1 = srmech_sha256b__ror(e, 6) ^ srmech_sha256b__ror(e, 11) ^ srmech_sha256b__ror(e, 25);
        const uint32_t ch = (e & f) ^ ((~e) & g);
        const uint32_t t1 = h + bs1 + ch + SRMECH_SHA256B_K[i] + w[i];
        const uint32_t bs0 = srmech_sha256b__ror(a, 2) ^ srmech_sha256b__ror(a, 13) ^ srmech_sha256b__ror(a, 22);
        const uint32_t maj = (a & b) ^ (a & c) ^ (b & c);
        const uint32_t t2 = bs0 + maj;
        h = g; g = f; f = e; e = d + t1; d = c; c = b; b = a; a = t1 + t2;
    }
    state[0] += a; state[1] += b; state[2] += c; state[3] += d;
    state[4] += e; state[5] += f; state[6] += g; state[7] += h;
}

static void srmech_sha256b__digest1(const uint8_t *msg, size_t len,
                                    uint8_t out[32])
{
    assert(out != NULL);
    assert(msg != NULL || len == 0u);
    uint32_t state[8];
    memcpy(state, SRMECH_SHA256B_H0, sizeof(state));
    uint8_t block[64];
    size_t b = 0;
    while (srmech_sha256b__fill_block(msg, len, b, block)) {
        srmech_sha256b__compress1(state, block);
        b++;
    }
    for (size_t i = 0; i < 8u; i++) {
        out[i * 4u + 0u] = (uint8_t)(state[i] >> 24);
        out[i * 4u + 1u] = (uint8_t)(state[i] >> 16);
        out[i * 4u + 2u] = (uint8_t)(state[i] >> 8);
        out[i * 4u + 3u] = (uint8_t)(state[i]);
    }
}

#if SRMECH_SIMD_X86

/* ------------------------------------------------------------------ *
 * SSE2 4-way kernel. Single-line vector macros only (JPL Rule 8).
 * ------------------------------------------------------------------ */
#define S4_ADD(x,y)   _mm_add_epi32((x),(y))
#define S4_XOR(x,y)   _mm_xor_si128((x),(y))
#define S4_AND(x,y)   _mm_and_si128((x),(y))
#define S4_ANDN(x,y)  _mm_andnot_si128((x),(y))
#define S4_OR(x,y)    _mm_or_si128((x),(y))
#define S4_SHR(x,n)   _mm_srli_epi32((x),(n))
#define S4_SHL(x,n)   _mm_slli_epi32((x),(n))
#define S4_ROR(x,n)   S4_OR(S4_SHR((x),(n)), S4_SHL((x),32-(n)))
#define S4_CH(x,y,z)  S4_XOR(S4_AND((x),(y)), S4_ANDN((x),(z)))
#define S4_MAJ(x,y,z) S4_XOR(S4_XOR(S4_AND((x),(y)), S4_AND((x),(z))), S4_AND((y),(z)))
#define S4_BS0(x)     S4_XOR(S4_XOR(S4_ROR((x),2), S4_ROR((x),13)), S4_ROR((x),22))
#define S4_BS1(x)     S4_XOR(S4_XOR(S4_ROR((x),6), S4_ROR((x),11)), S4_ROR((x),25))
#define S4_SS0(x)     S4_XOR(S4_XOR(S4_ROR((x),7), S4_ROR((x),18)), S4_SHR((x),3))
#define S4_SS1(x)     S4_XOR(S4_XOR(S4_ROR((x),17), S4_ROR((x),19)), S4_SHR((x),10))

SRMECH_SIMD_TARGET_SSE2
static void srmech_sha256b__compress4(__m128i state[8], const __m128i win[16])
{
    assert(state != NULL);
    assert(win != NULL);
    __m128i w[64];
    for (size_t i = 0; i < 16u; i++) { w[i] = win[i]; }
    for (size_t i = 16; i < 64u; i++) {
        w[i] = S4_ADD(S4_ADD(S4_ADD(w[i - 16u], S4_SS0(w[i - 15u])), w[i - 7u]), S4_SS1(w[i - 2u]));
    }
    __m128i a = state[0], b = state[1], c = state[2], d = state[3];
    __m128i e = state[4], f = state[5], g = state[6], h = state[7];
    for (size_t i = 0; i < 64u; i++) {
        const __m128i kk = _mm_set1_epi32((int)SRMECH_SHA256B_K[i]);
        const __m128i t1 = S4_ADD(S4_ADD(S4_ADD(S4_ADD(h, S4_BS1(e)), S4_CH(e, f, g)), kk), w[i]);
        const __m128i t2 = S4_ADD(S4_BS0(a), S4_MAJ(a, b, c));
        h = g; g = f; f = e; e = S4_ADD(d, t1); d = c; c = b; b = a; a = S4_ADD(t1, t2);
    }
    state[0] = S4_ADD(state[0], a); state[1] = S4_ADD(state[1], b);
    state[2] = S4_ADD(state[2], c); state[3] = S4_ADD(state[3], d);
    state[4] = S4_ADD(state[4], e); state[5] = S4_ADD(state[5], f);
    state[6] = S4_ADD(state[6], g); state[7] = S4_ADD(state[7], h);
}

SRMECH_SIMD_TARGET_SSE2
static void srmech_sha256b__hash4(const uint8_t *const *msgs,
                                  const size_t *lens, uint8_t *out)
{
    assert(msgs != NULL);
    assert(out != NULL);
    __m128i st[8];
    for (size_t i = 0; i < 8u; i++) { st[i] = _mm_set1_epi32((int)SRMECH_SHA256B_H0[i]); }
    size_t maxb = 0;
    for (size_t L = 0; L < 4u; L++) {
        const size_t nb = (lens[L] + 72u) / 64u;
        if (nb > maxb) { maxb = nb; }
    }
    for (size_t bidx = 0; bidx < maxb; bidx++) {
        uint32_t lw[4][16];
        int active[4];
        for (size_t L = 0; L < 4u; L++) {
            uint8_t blk[64];
            active[L] = srmech_sha256b__fill_block(msgs[L], lens[L], bidx, blk);
            srmech_sha256b__load_words(blk, lw[L]);
        }
        __m128i win[16];
        for (size_t i = 0; i < 16u; i++) {
            win[i] = _mm_setr_epi32((int)lw[0][i], (int)lw[1][i], (int)lw[2][i], (int)lw[3][i]);
        }
        __m128i nst[8];
        for (size_t i = 0; i < 8u; i++) { nst[i] = st[i]; }
        srmech_sha256b__compress4(nst, win);
        const __m128i m = _mm_setr_epi32(active[0] ? -1 : 0, active[1] ? -1 : 0,
                                         active[2] ? -1 : 0, active[3] ? -1 : 0);
        for (size_t i = 0; i < 8u; i++) {
            st[i] = S4_OR(S4_AND(nst[i], m), S4_ANDN(m, st[i]));
        }
    }
    for (size_t i = 0; i < 8u; i++) {
        uint32_t lane[4];
        _mm_storeu_si128((__m128i *)(void *)lane, st[i]);
        for (size_t L = 0; L < 4u; L++) {
            uint8_t *d = out + (L * 32u) + (i * 4u);
            d[0] = (uint8_t)(lane[L] >> 24); d[1] = (uint8_t)(lane[L] >> 16);
            d[2] = (uint8_t)(lane[L] >> 8);  d[3] = (uint8_t)(lane[L]);
        }
    }
}

/* ------------------------------------------------------------------ *
 * AVX2 8-way kernel. Single-line vector macros only (JPL Rule 8).
 * ------------------------------------------------------------------ */
#define A8_ADD(x,y)   _mm256_add_epi32((x),(y))
#define A8_XOR(x,y)   _mm256_xor_si256((x),(y))
#define A8_AND(x,y)   _mm256_and_si256((x),(y))
#define A8_ANDN(x,y)  _mm256_andnot_si256((x),(y))
#define A8_OR(x,y)    _mm256_or_si256((x),(y))
#define A8_SHR(x,n)   _mm256_srli_epi32((x),(n))
#define A8_SHL(x,n)   _mm256_slli_epi32((x),(n))
#define A8_ROR(x,n)   A8_OR(A8_SHR((x),(n)), A8_SHL((x),32-(n)))
#define A8_CH(x,y,z)  A8_XOR(A8_AND((x),(y)), A8_ANDN((x),(z)))
#define A8_MAJ(x,y,z) A8_XOR(A8_XOR(A8_AND((x),(y)), A8_AND((x),(z))), A8_AND((y),(z)))
#define A8_BS0(x)     A8_XOR(A8_XOR(A8_ROR((x),2), A8_ROR((x),13)), A8_ROR((x),22))
#define A8_BS1(x)     A8_XOR(A8_XOR(A8_ROR((x),6), A8_ROR((x),11)), A8_ROR((x),25))
#define A8_SS0(x)     A8_XOR(A8_XOR(A8_ROR((x),7), A8_ROR((x),18)), A8_SHR((x),3))
#define A8_SS1(x)     A8_XOR(A8_XOR(A8_ROR((x),17), A8_ROR((x),19)), A8_SHR((x),10))

SRMECH_SIMD_TARGET_AVX2
static void srmech_sha256b__compress8(__m256i state[8], const __m256i win[16])
{
    assert(state != NULL);
    assert(win != NULL);
    __m256i w[64];
    for (size_t i = 0; i < 16u; i++) { w[i] = win[i]; }
    for (size_t i = 16; i < 64u; i++) {
        w[i] = A8_ADD(A8_ADD(A8_ADD(w[i - 16u], A8_SS0(w[i - 15u])), w[i - 7u]), A8_SS1(w[i - 2u]));
    }
    __m256i a = state[0], b = state[1], c = state[2], d = state[3];
    __m256i e = state[4], f = state[5], g = state[6], h = state[7];
    for (size_t i = 0; i < 64u; i++) {
        const __m256i kk = _mm256_set1_epi32((int)SRMECH_SHA256B_K[i]);
        const __m256i t1 = A8_ADD(A8_ADD(A8_ADD(A8_ADD(h, A8_BS1(e)), A8_CH(e, f, g)), kk), w[i]);
        const __m256i t2 = A8_ADD(A8_BS0(a), A8_MAJ(a, b, c));
        h = g; g = f; f = e; e = A8_ADD(d, t1); d = c; c = b; b = a; a = A8_ADD(t1, t2);
    }
    state[0] = A8_ADD(state[0], a); state[1] = A8_ADD(state[1], b);
    state[2] = A8_ADD(state[2], c); state[3] = A8_ADD(state[3], d);
    state[4] = A8_ADD(state[4], e); state[5] = A8_ADD(state[5], f);
    state[6] = A8_ADD(state[6], g); state[7] = A8_ADD(state[7], h);
}

SRMECH_SIMD_TARGET_AVX2
static void srmech_sha256b__hash8(const uint8_t *const *msgs,
                                  const size_t *lens, uint8_t *out)
{
    assert(msgs != NULL);
    assert(out != NULL);
    __m256i st[8];
    for (size_t i = 0; i < 8u; i++) { st[i] = _mm256_set1_epi32((int)SRMECH_SHA256B_H0[i]); }
    size_t maxb = 0;
    for (size_t L = 0; L < 8u; L++) {
        const size_t nb = (lens[L] + 72u) / 64u;
        if (nb > maxb) { maxb = nb; }
    }
    for (size_t bidx = 0; bidx < maxb; bidx++) {
        uint32_t lw[8][16];
        int active[8];
        for (size_t L = 0; L < 8u; L++) {
            uint8_t blk[64];
            active[L] = srmech_sha256b__fill_block(msgs[L], lens[L], bidx, blk);
            srmech_sha256b__load_words(blk, lw[L]);
        }
        __m256i win[16];
        for (size_t i = 0; i < 16u; i++) {
            win[i] = _mm256_setr_epi32((int)lw[0][i], (int)lw[1][i], (int)lw[2][i], (int)lw[3][i],
                                       (int)lw[4][i], (int)lw[5][i], (int)lw[6][i], (int)lw[7][i]);
        }
        __m256i nst[8];
        for (size_t i = 0; i < 8u; i++) { nst[i] = st[i]; }
        srmech_sha256b__compress8(nst, win);
        const __m256i m = _mm256_setr_epi32(active[0] ? -1 : 0, active[1] ? -1 : 0,
                                            active[2] ? -1 : 0, active[3] ? -1 : 0,
                                            active[4] ? -1 : 0, active[5] ? -1 : 0,
                                            active[6] ? -1 : 0, active[7] ? -1 : 0);
        for (size_t i = 0; i < 8u; i++) {
            st[i] = _mm256_blendv_epi8(st[i], nst[i], m);
        }
    }
    for (size_t i = 0; i < 8u; i++) {
        uint32_t lane[8];
        _mm256_storeu_si256((__m256i *)(void *)lane, st[i]);
        for (size_t L = 0; L < 8u; L++) {
            uint8_t *d = out + (L * 32u) + (i * 4u);
            d[0] = (uint8_t)(lane[L] >> 24); d[1] = (uint8_t)(lane[L] >> 16);
            d[2] = (uint8_t)(lane[L] >> 8);  d[3] = (uint8_t)(lane[L]);
        }
    }
}

#endif /* SRMECH_SIMD_X86 */

/* ------------------------------------------------------------------ *
 * Public entry — declared in srmech.h.
 * ------------------------------------------------------------------ */
srmech_status_t srmech_sha256_batch(const uint8_t *const *msgs,
                                    const size_t *lens, size_t n,
                                    uint8_t *out_digests)
{
    if (n > 0u && (msgs == NULL || lens == NULL || out_digests == NULL)) {
        return SRMECH_ERR_NULL_ARG;
    }
    for (size_t i = 0; i < n; i++) {
        if (msgs[i] == NULL && lens[i] != 0u) {
            return SRMECH_ERR_NULL_ARG;
        }
    }
    assert(n == 0u || (msgs != NULL && lens != NULL && out_digests != NULL));

    size_t i = 0;
    const int detected = srmech_simd_has_avx2() ? 2
                       : (srmech_simd_has_sse2() ? 1 : 0);
    const int tier = srmech_simd_tier("SRMECH_SHA256_FORCE_TIER", detected, 2);
    assert(tier >= 0 && tier <= 2);
#if SRMECH_SIMD_X86
    if (tier == 2) {
        for (; i + 8u <= n; i += 8u) {
            srmech_sha256b__hash8(&msgs[i], &lens[i], out_digests + (i * 32u));
        }
    } else if (tier == 1) {
        for (; i + 4u <= n; i += 4u) {
            srmech_sha256b__hash4(&msgs[i], &lens[i], out_digests + (i * 32u));
        }
    }
#else
    (void)tier;
#endif
    for (; i < n; i++) {
        srmech_sha256b__digest1(msgs[i], lens[i], out_digests + (i * 32u));
    }
    return SRMECH_OK;
}
