/*
 * srmech_sha256_shani.c — SHA-NI single-stream SHA-256 (F292 graft #3).
 *
 * PERFORMANCE-ENGINEERING of srmech's OWN content-addressing hash for the
 * COMMON case the batch graft (#1) does not cover: ONE message, hashed once
 * (every AMSC attestation fingerprints a single response-bytes blob via
 * `sha256_bytes`). Where graft #1 needs N independent messages to fill the
 * SIMD lanes, the Intel SHA Extensions (SHA-NI) accelerate a SINGLE message:
 * `_mm_sha256rnds2_epu32` runs two SHA-256 rounds per instruction and
 * `_mm_sha256msg1/msg2_epu32` drive the message schedule, so one 64-byte
 * block compresses in a handful of instructions.
 *
 * SCOPE: energy/perf-engineering, measured in hashes-per-op. NOT mining —
 * binding does not make hashing cheaper and SHA-256 has no PoW shortcut;
 * this is "a correct instrument," just faster at the single-message case.
 * Technique attested to PUBLIC references (FIPS 180-4 for the algorithm;
 * the Intel Intrinsics Guide + Intel SHA Extensions whitepaper for the
 * rnds2/msg1/msg2 round structure). The widely-mirrored public-domain
 * `sha256_process_x86` reference (J. Walton, noloader/SHA-Intrinsics) was
 * read only as a working-impl pointer; this is re-implemented JPL-clean
 * (intrinsics, not asm; ≤60-line functions; ≥2 asserts; single-line macros)
 * and bit-exact with the scalar path / hashlib / NIST KATs.
 *
 * MECHANISM. `srmech_sha256_shani` hashes one message. On x86 with the SHA
 * feature present it FIPS-pads the message a block at a time and runs each
 * 64-byte block through the SHA-NI compress (state kept packed in the Intel
 * ABEF/CDGH layout across blocks). Hosts WITHOUT the SHA feature — and all
 * non-x86 / Pyodide builds — take the self-contained scalar path (a
 * duplicate of srmech_sha256.c's compress, kept byte-for-byte in sync; both
 * NIST-KAT-pinned), so this graft touches the proven single-stream file
 * zero. SRMECH_SHANI_FORCE_TIER={0,1} forces the dispatch (0=scalar /
 * 1=SHA-NI-if-present); env-forcing tier 1 on a host WITHOUT SHA-NI still
 * runs the scalar path (the kernel is NEVER entered unless cpuid confirms
 * the feature), so the force hook can only ever select a SLOWER-or-equal
 * path — it can never SIGILL.
 *
 * Because the dev/most-CI hosts lack the SHA feature, the scalar duplicate
 * is what those hosts execute (and what the local full-suite exercises);
 * the SHA-NI kernel itself is parity-checked on SHA-NI-capable CI runners
 * (exercise-if-present/skip-with-log in tests/test_sha256_shani.py) and its
 * presence-per-run is surfaced by the CI cpuid-dump step.
 *
 * JPL Power-of-Ten: Rule 1 (no goto / no recursion — flat loops); Rule 3
 * (no malloc — bounded stack only); Rule 4 (≤60-line functions — the 64
 * SHA-NI rounds are factored into a load helper + a cyclic steady-state
 * group + a final group, via the message-register rotation that is
 * bit-identical to the canonical interleaving); Rule 5 (≥2 asserts per
 * non-exempt function; the cpuid probe lives in the HAL, srmech_simd.c;
 * srmech_sha256ni__ror is the documented 1-line-rotate exemption); Rule 8
 * (only SINGLE-line macros); Rule 10 (-Wall -Wextra -Wpedantic -Werror /
 * /W4 /WX). ABI: new symbol only -> SRMECH_ABI_VERSION stays 3.
 *
 * License: MIT.
 */

#include "srmech.h"
#include "srmech_simd.h"   /* SIMD optimize-path HAL: SRMECH_SIMD_X86,
                            * arch includes, SRMECH_SIMD_TARGET_*, cpuid */
#include "srmech_sha256_constants.h"   /* attested FIPS K[64] + H0[8] */
#include "srmech_sha256_shani.h"       /* attested packed KP[16][2] + the
                                        * SHA-NI instruction-sequence MPR */

#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

/* SHA-256 K[64] + H0[8] come from the attested srmech_sha256_constants.h;
 * the packed per-group round-constant table KP[16][2] + the SHA-NI rnds2/
 * msg1/msg2 instruction-sequence attestation come from srmech_sha256_shani.h
 * (rc19 constant-attestation discipline — no in-TU magic-constant copies). */

/* ------------------------------------------------------------------ *
 * Streaming per-message FIPS-padding (no malloc). Fills `out[64]` with
 * block index `b` and returns 1 if that block exists (b < nblocks).
 * nblocks = (len + 72) / 64. Duplicate of srmech_sha256_batch.c's
 * (both NIST-KAT-pinned); shared by the scalar + the SHA-NI path.
 * ------------------------------------------------------------------ */
static int srmech_sha256ni__fill_block(const uint8_t *msg, size_t len,
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

/* Big-endian serialise of the 8 state words to the 32-byte digest. */
static void srmech_sha256ni__store_digest(const uint32_t state[8],
                                          uint8_t out[32])
{
    assert(state != NULL);
    assert(out != NULL);
    for (size_t i = 0; i < 8u; i++) {
        out[i * 4u + 0u] = (uint8_t)(state[i] >> 24);
        out[i * 4u + 1u] = (uint8_t)(state[i] >> 16);
        out[i * 4u + 2u] = (uint8_t)(state[i] >> 8);
        out[i * 4u + 3u] = (uint8_t)(state[i]);
    }
}

/* ------------------------------------------------------------------ *
 * Scalar tier (the oracle + the no-SHA-NI / non-x86 fallback).
 * Byte-for-byte the srmech_sha256.c / srmech_sha256_batch.c compress.
 * ------------------------------------------------------------------ */
static uint32_t srmech_sha256ni__ror(uint32_t x, unsigned n)
{
    return (x >> n) | (x << (32u - n));
}

static void srmech_sha256ni__load_words(const uint8_t block[64], uint32_t w[16])
{
    assert(block != NULL);
    assert(w != NULL);
    for (size_t i = 0; i < 16u; i++) {
        const size_t j = i * 4u;
        w[i] = ((uint32_t)block[j] << 24) | ((uint32_t)block[j + 1u] << 16)
             | ((uint32_t)block[j + 2u] << 8) | ((uint32_t)block[j + 3u]);
    }
}

static void srmech_sha256ni__compress1(uint32_t state[8], const uint8_t block[64])
{
    assert(state != NULL);
    assert(block != NULL);
    uint32_t w[64];
    srmech_sha256ni__load_words(block, w);
    for (size_t i = 16; i < 64u; i++) {
        const uint32_t s0 = srmech_sha256ni__ror(w[i - 15u], 7) ^ srmech_sha256ni__ror(w[i - 15u], 18) ^ (w[i - 15u] >> 3);
        const uint32_t s1 = srmech_sha256ni__ror(w[i - 2u], 17) ^ srmech_sha256ni__ror(w[i - 2u], 19) ^ (w[i - 2u] >> 10);
        w[i] = w[i - 16u] + s0 + w[i - 7u] + s1;
    }
    uint32_t a = state[0], b = state[1], c = state[2], d = state[3];
    uint32_t e = state[4], f = state[5], g = state[6], h = state[7];
    for (size_t i = 0; i < 64u; i++) {
        const uint32_t bs1 = srmech_sha256ni__ror(e, 6) ^ srmech_sha256ni__ror(e, 11) ^ srmech_sha256ni__ror(e, 25);
        const uint32_t ch = (e & f) ^ ((~e) & g);
        const uint32_t t1 = h + bs1 + ch + SRMECH_SHA256_K[i] + w[i];
        const uint32_t bs0 = srmech_sha256ni__ror(a, 2) ^ srmech_sha256ni__ror(a, 13) ^ srmech_sha256ni__ror(a, 22);
        const uint32_t maj = (a & b) ^ (a & c) ^ (b & c);
        const uint32_t t2 = bs0 + maj;
        h = g; g = f; f = e; e = d + t1; d = c; c = b; b = a; a = t1 + t2;
    }
    state[0] += a; state[1] += b; state[2] += c; state[3] += d;
    state[4] += e; state[5] += f; state[6] += g; state[7] += h;
}

static void srmech_sha256ni__digest_scalar(const uint8_t *msg, size_t len,
                                           uint8_t out[32])
{
    assert(out != NULL);
    assert(msg != NULL || len == 0u);
    uint32_t state[8];
    memcpy(state, SRMECH_SHA256_H0, sizeof(state));
    uint8_t block[64];
    size_t b = 0;
    while (srmech_sha256ni__fill_block(msg, len, b, block)) {
        srmech_sha256ni__compress1(state, block);
        b++;
    }
    srmech_sha256ni__store_digest(state, out);
}

#if SRMECH_SIMD_X86 && SRMECH_SIMD_SHANI_KERNEL

/* ------------------------------------------------------------------ *
 * SHA-NI tier. The 64 rounds are factored into:
 *   - rounds_0_15:  load + initial message-schedule warm-up (special)
 *   - group_full:   one steady-state 4-round group with full schedule,
 *                   driven by a cyclic message-register index `cur`
 *                   (m[cur]=current, m[cur-1] gets msg1, m[cur+1] gets
 *                   alignr+msg2) — bit-identical to the canonical
 *                   MSG0→MSG1→MSG2→MSG3 rotation; called for rounds 16-59
 *   - group_final:  the last 4 rounds (no schedule; future words unused)
 * Single-line vector macros only (JPL Rule 8). The per-group round
 * constants are the FIPS K words, packed two-per-128 as the Intel
 * reference does (each pair = K[4g] | K[4g+3] across the lane). The
 * table below stores them as (hi64, lo64) for _mm_set_epi64x.
 * ------------------------------------------------------------------ */
#define NI_ADD(x, y)      _mm_add_epi32((x), (y))
#define NI_RNDS2(s1, s0, m) _mm_sha256rnds2_epu32((s1), (s0), (m))
#define NI_MSG1(a, b)     _mm_sha256msg1_epu32((a), (b))
#define NI_MSG2(a, b)     _mm_sha256msg2_epu32((a), (b))
#define NI_ALIGN(a, b, n) _mm_alignr_epi8((a), (b), (n))
#define NI_SHUF(a, i)     _mm_shuffle_epi32((a), (i))
#define NI_KPAIR(g) _mm_set_epi64x((long long)SRMECH_SHA256NI_KP[(g)][0], (long long)SRMECH_SHA256NI_KP[(g)][1])

/* SRMECH_SHA256NI_KP[16][2] (the packed per-group round constants) lives in
 * the attested srmech_sha256_shani.h (included at the top) — rc19
 * constant-attestation discipline; the FIPS derivation in
 * tests/test_fips_constants_attested.py is its verification gate. */

/* Running SHA-NI block context: packed state + the 4 message registers
 * (16 schedule words) + the cyclic current-register index. */
typedef struct {
    __m128i s0;       /* ABEF */
    __m128i s1;       /* CDGH */
    __m128i m[4];     /* MSG0..MSG3 */
    unsigned cur;     /* index of the "current" message register, 0..3 */
} srmech_ni_ctx;

/* Pack the natural-order state[8] (a..h) into the ABEF / CDGH layout. */
SRMECH_SIMD_TARGET_SHANI
static void srmech_sha256ni__pack(const uint32_t state[8], srmech_ni_ctx *c)
{
    assert(state != NULL);
    assert(c != NULL);
    __m128i tmp = _mm_loadu_si128((const __m128i *)(const void *)&state[0]);
    __m128i s1  = _mm_loadu_si128((const __m128i *)(const void *)&state[4]);
    tmp = NI_SHUF(tmp, 0xB1);          /* CDAB */
    s1  = NI_SHUF(s1, 0x1B);           /* EFGH */
    c->s0 = NI_ALIGN(tmp, s1, 8);      /* ABEF */
    c->s1 = _mm_blend_epi16(s1, tmp, 0xF0); /* CDGH */
}

/* Reverse the pack: ABEF / CDGH back to natural-order state[8]. */
SRMECH_SIMD_TARGET_SHANI
static void srmech_sha256ni__unpack(const srmech_ni_ctx *c, uint32_t state[8])
{
    assert(c != NULL);
    assert(state != NULL);
    __m128i tmp = NI_SHUF(c->s0, 0x1B);   /* FEBA */
    __m128i s1  = NI_SHUF(c->s1, 0xB1);   /* DCHG */
    __m128i s0  = _mm_blend_epi16(tmp, s1, 0xF0); /* DCBA */
    s1 = NI_ALIGN(s1, tmp, 8);            /* ABEF -> HGFE */
    _mm_storeu_si128((__m128i *)(void *)&state[0], s0);
    _mm_storeu_si128((__m128i *)(void *)&state[4], s1);
}

/* Rounds 0-15: load the four 16-byte words (big-endian), then the
 * warm-up schedule that the steady cyclic rule cannot express. Leaves
 * ctx->cur = 0 (round 16 reads m[0]). */
SRMECH_SIMD_TARGET_SHANI
static void srmech_sha256ni__rounds_0_15(srmech_ni_ctx *c, const uint8_t *data)
{
    assert(c != NULL);
    assert(data != NULL);
    const __m128i mask = _mm_set_epi64x(0x0c0d0e0f08090a0bULL,
                                        0x0405060700010203ULL);
    c->m[0] = _mm_shuffle_epi8(_mm_loadu_si128((const __m128i *)(const void *)(data +  0)), mask);
    c->m[1] = _mm_shuffle_epi8(_mm_loadu_si128((const __m128i *)(const void *)(data + 16)), mask);
    c->m[2] = _mm_shuffle_epi8(_mm_loadu_si128((const __m128i *)(const void *)(data + 32)), mask);
    c->m[3] = _mm_shuffle_epi8(_mm_loadu_si128((const __m128i *)(const void *)(data + 48)), mask);
    __m128i msg = NI_ADD(c->m[0], NI_KPAIR(0));        /* rounds 0-3 */
    c->s1 = NI_RNDS2(c->s1, c->s0, msg);
    msg = NI_SHUF(msg, 0x0E);
    c->s0 = NI_RNDS2(c->s0, c->s1, msg);
    msg = NI_ADD(c->m[1], NI_KPAIR(1));                /* rounds 4-7 */
    c->s1 = NI_RNDS2(c->s1, c->s0, msg);
    msg = NI_SHUF(msg, 0x0E);
    c->s0 = NI_RNDS2(c->s0, c->s1, msg);
    c->m[0] = NI_MSG1(c->m[0], c->m[1]);
    msg = NI_ADD(c->m[2], NI_KPAIR(2));                /* rounds 8-11 */
    c->s1 = NI_RNDS2(c->s1, c->s0, msg);
    msg = NI_SHUF(msg, 0x0E);
    c->s0 = NI_RNDS2(c->s0, c->s1, msg);
    c->m[1] = NI_MSG1(c->m[1], c->m[2]);
    msg = NI_ADD(c->m[3], NI_KPAIR(3));                /* rounds 12-15 */
    c->s1 = NI_RNDS2(c->s1, c->s0, msg);
    c->m[0] = NI_ADD(c->m[0], NI_ALIGN(c->m[3], c->m[2], 4));
    c->m[0] = NI_MSG2(c->m[0], c->m[3]);
    msg = NI_SHUF(msg, 0x0E);
    c->s0 = NI_RNDS2(c->s0, c->s1, msg);
    c->m[2] = NI_MSG1(c->m[2], c->m[3]);
    c->cur = 0u;
}

/* One steady-state 4-round group (rounds 16-59) with the full message
 * schedule, driven by the cyclic current-register index. Advances cur. */
SRMECH_SIMD_TARGET_SHANI
static void srmech_sha256ni__group_full(srmech_ni_ctx *c, __m128i kpair)
{
    assert(c != NULL);
    assert(c->cur < 4u);
    const unsigned cu = c->cur;
    const unsigned nx = (cu + 1u) & 3u;
    const unsigned pv = (cu + 3u) & 3u;
    __m128i msg = NI_ADD(c->m[cu], kpair);
    c->s1 = NI_RNDS2(c->s1, c->s0, msg);
    c->m[nx] = NI_ADD(c->m[nx], NI_ALIGN(c->m[cu], c->m[pv], 4));
    c->m[nx] = NI_MSG2(c->m[nx], c->m[cu]);
    msg = NI_SHUF(msg, 0x0E);
    c->s0 = NI_RNDS2(c->s0, c->s1, msg);
    c->m[pv] = NI_MSG1(c->m[pv], c->m[cu]);
    c->cur = nx;
}

/* The final 4-round group (rounds 60-63): rounds only, no schedule. */
SRMECH_SIMD_TARGET_SHANI
static void srmech_sha256ni__group_final(srmech_ni_ctx *c, __m128i kpair)
{
    assert(c != NULL);
    assert(c->cur < 4u);
    __m128i msg = NI_ADD(c->m[c->cur], kpair);
    c->s1 = NI_RNDS2(c->s1, c->s0, msg);
    msg = NI_SHUF(msg, 0x0E);
    c->s0 = NI_RNDS2(c->s0, c->s1, msg);
}

/* Compress one 64-byte block into the packed state (ctx->s0/s1). */
SRMECH_SIMD_TARGET_SHANI
static void srmech_sha256ni__compress_block(srmech_ni_ctx *c,
                                            const uint8_t block[64])
{
    assert(c != NULL);
    assert(block != NULL);
    const __m128i abef = c->s0;
    const __m128i cdgh = c->s1;
    srmech_sha256ni__rounds_0_15(c, block);
    for (unsigned g = 4u; g <= 14u; g++) {
        srmech_sha256ni__group_full(c, NI_KPAIR(g));
    }
    srmech_sha256ni__group_final(c, NI_KPAIR(15));
    c->s0 = NI_ADD(c->s0, abef);
    c->s1 = NI_ADD(c->s1, cdgh);
}

/* SHA-NI single-message digest. FIPS-pads a block at a time, keeps the
 * state packed across blocks, unpacks + serialises at the end. */
SRMECH_SIMD_TARGET_SHANI
static void srmech_sha256ni__digest_shani(const uint8_t *msg, size_t len,
                                          uint8_t out[32])
{
    assert(out != NULL);
    assert(msg != NULL || len == 0u);
    uint32_t state[8];
    memcpy(state, SRMECH_SHA256_H0, sizeof(state));
    srmech_ni_ctx c;
    srmech_sha256ni__pack(state, &c);
    uint8_t block[64];
    size_t b = 0;
    while (srmech_sha256ni__fill_block(msg, len, b, block)) {
        srmech_sha256ni__compress_block(&c, block);
        b++;
    }
    srmech_sha256ni__unpack(&c, state);
    srmech_sha256ni__store_digest(state, out);
}

#endif /* SRMECH_SIMD_X86 */

/* ------------------------------------------------------------------ *
 * Public entry — declared in srmech.h. Outputs the RAW 32-byte digest.
 * ------------------------------------------------------------------ */
srmech_status_t srmech_sha256_shani(const uint8_t *data, size_t len,
                                    uint8_t *out_digest)
{
    if (out_digest == NULL || (data == NULL && len != 0u)) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(out_digest != NULL);
    assert(data != NULL || len == 0u);
    const int detected = srmech_simd_has_shani() ? 1 : 0;
    const int tier = srmech_simd_tier("SRMECH_SHANI_FORCE_TIER", detected, 1);
    assert(tier >= 0 && tier <= 1);
#if SRMECH_SIMD_X86 && SRMECH_SIMD_SHANI_KERNEL
    if (tier >= 1 && srmech_simd_has_shani()) {
        srmech_sha256ni__digest_shani(data, len, out_digest);
        return SRMECH_OK;
    }
#else
    (void)tier;
#endif
    srmech_sha256ni__digest_scalar(data, len, out_digest);
    return SRMECH_OK;
}
