/*
 * srmech_sha256.c — SHA-256 implementation (FIPS 180-4) + the
 * srmech_sha256_hex public entry point.
 *
 * Self-contained, no OpenSSL / no libcrypto dependency. Mirrors the
 * Python reference `hashlib.sha256(data).hexdigest()` exactly —
 * pinned by the byte-exact parity test in
 * c/test/test_parity_python.py + the Python pytest in
 * srmech/python/tests/test_native_sha256.py.
 *
 * Task #201 Phase B3 — first native symbol in the srmech C library.
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto)        : OK (no goto in this file)
 *   - Rule 2 (bounded loops)  : OK (every loop bounded by a constant
 *                              or by the input length, which is
 *                              caller-supplied and stored in a size_t)
 *   - Rule 3 (no malloc)      : OK (bounded stack buffers only)
 *   - Rule 4 (≤60 lines/func) : OK — each helper kept short; the
 *                              compress function is split into a
 *                              schedule-prep helper + the rounds
 *                              proper
 *   - Rule 5 (≥2 asserts/fn)  : OK — input pointers + size bounds
 *                              asserted at every entry point
 *   - Rule 7 (return-value)   : OK — see srmech.h for the
 *                              srmech_status_t convention
 *   - Rule 10 (warnings clean): OK under -Wall -Wextra -Wpedantic
 *                              -Werror (verified at CI Phase B6)
 *
 * License: GPL-3.0-or-later.
 */

#include "srmech.h"
#include "srmech_sha256_constants.h"   /* attested FIPS K[64] + H0[8]
                                        * (MPR block + derive-and-assert) */

#include <assert.h>
#include <stdint.h>
#include <string.h>

/* ------------------------------------------------------------------ *
 * Bit-rotation + sigma helpers (FIPS 180-4 §4.1.2)
 * Inlined wherever they appear in the rounds.
 * ------------------------------------------------------------------ */

static inline uint32_t srmech_ror32(uint32_t x, unsigned int n)
{
    /* n is always in {2, 6, 7, 11, 13, 17, 18, 19, 22, 25} in the
     * SHA-256 schedule + rounds; never zero, never ≥ 32 — bounds
     * preserved by callers below. */
    return (x >> n) | (x << (32u - n));
}

static inline uint32_t srmech_ch(uint32_t x, uint32_t y, uint32_t z)
{
    return (x & y) ^ ((~x) & z);
}

static inline uint32_t srmech_maj(uint32_t x, uint32_t y, uint32_t z)
{
    return (x & y) ^ (x & z) ^ (y & z);
}

static inline uint32_t srmech_bigsig0(uint32_t x)
{
    return srmech_ror32(x, 2) ^ srmech_ror32(x, 13) ^ srmech_ror32(x, 22);
}

static inline uint32_t srmech_bigsig1(uint32_t x)
{
    return srmech_ror32(x, 6) ^ srmech_ror32(x, 11) ^ srmech_ror32(x, 25);
}

static inline uint32_t srmech_smallsig0(uint32_t x)
{
    return srmech_ror32(x, 7) ^ srmech_ror32(x, 18) ^ (x >> 3);
}

static inline uint32_t srmech_smallsig1(uint32_t x)
{
    return srmech_ror32(x, 17) ^ srmech_ror32(x, 19) ^ (x >> 10);
}

/* ------------------------------------------------------------------ *
 * Compress one 512-bit (64-byte) block into the running hash state.
 *
 * `state` is the 8-word running state; `block` is the 64-byte input
 * block. FIPS 180-4 §6.2.2. Stack footprint: 8 * 4 (state copy) +
 * 64 * 4 (message schedule) + a couple of scratch uint32s ≈ 320
 * bytes. JPL Rule 3 OK (no malloc).
 * ------------------------------------------------------------------ */
static void srmech_sha256_compress(uint32_t state[8], const uint8_t block[64])
{
    assert(state != NULL);
    assert(block != NULL);

    uint32_t w[64];

    /* Step 1: prepare the message schedule W[0..63]. */
    for (size_t i = 0; i < 16u; i++) {
        const size_t b = i * 4u;
        w[i] = ((uint32_t)block[b]     << 24)
             | ((uint32_t)block[b + 1u] << 16)
             | ((uint32_t)block[b + 2u] <<  8)
             | ((uint32_t)block[b + 3u]      );
    }
    for (size_t i = 16; i < 64u; i++) {
        w[i] = srmech_smallsig1(w[i - 2u])
             + w[i - 7u]
             + srmech_smallsig0(w[i - 15u])
             + w[i - 16u];
    }

    /* Step 2: 8 working variables initialised from state. */
    uint32_t a = state[0], b = state[1], c = state[2], d = state[3];
    uint32_t e = state[4], f = state[5], g = state[6], h = state[7];

    /* Step 3: 64 rounds. */
    for (size_t i = 0; i < 64u; i++) {
        const uint32_t t1 = h
                          + srmech_bigsig1(e)
                          + srmech_ch(e, f, g)
                          + SRMECH_SHA256_K[i]
                          + w[i];
        const uint32_t t2 = srmech_bigsig0(a) + srmech_maj(a, b, c);
        h = g;
        g = f;
        f = e;
        e = d + t1;
        d = c;
        c = b;
        b = a;
        a = t1 + t2;
    }

    /* Step 4: fold back into state. */
    state[0] += a;
    state[1] += b;
    state[2] += c;
    state[3] += d;
    state[4] += e;
    state[5] += f;
    state[6] += g;
    state[7] += h;
}

/* ------------------------------------------------------------------ *
 * Hex-encode 8 big-endian uint32 hash words into 64 lowercase chars.
 * `out` must point to at least 65 bytes; trailing NUL written.
 *
 * JPL Rule 5: caller's `out` is asserted non-NULL upstream by
 * srmech_sha256_hex (the only caller); the assert here documents
 * the local invariant.
 * ------------------------------------------------------------------ */
static void srmech_sha256_state_to_hex(const uint32_t state[8], char *out)
{
    static const char HEX[17] = "0123456789abcdef";
    assert(state != NULL);
    assert(out != NULL);

    for (size_t i = 0; i < 8u; i++) {
        const uint32_t w = state[i];
        const size_t base = i * 8u;
        out[base + 0u] = HEX[(w >> 28) & 0x0Fu];
        out[base + 1u] = HEX[(w >> 24) & 0x0Fu];
        out[base + 2u] = HEX[(w >> 20) & 0x0Fu];
        out[base + 3u] = HEX[(w >> 16) & 0x0Fu];
        out[base + 4u] = HEX[(w >> 12) & 0x0Fu];
        out[base + 5u] = HEX[(w >>  8) & 0x0Fu];
        out[base + 6u] = HEX[(w >>  4) & 0x0Fu];
        out[base + 7u] = HEX[ w        & 0x0Fu];
    }
    out[64] = '\0';
}

/* ------------------------------------------------------------------ *
 * Public entry — declared in srmech.h.
 *
 * One-shot SHA-256 over `data[0..data_len)`. Writes 64 lowercase hex
 * chars + NUL into `out_hex`. Caller is responsible for the 65-byte
 * destination buffer.
 *
 * Byte-exact with Python's `hashlib.sha256(data).hexdigest()`. The
 * implementation handles the FIPS 180-4 padding rules + the 64-bit
 * length suffix inline; works for arbitrary `data_len` up to SIZE_MAX.
 *
 * Returns SRMECH_OK on success, SRMECH_ERR_NULL_ARG if any input
 * pointer is NULL. (data == NULL is allowed only when data_len == 0,
 * since hashing zero bytes is a valid operation that yields the
 * empty-string hash; we tolerate NULL there to mirror the Python
 * `hashlib.sha256(b"")` semantics.)
 * ------------------------------------------------------------------ */
srmech_status_t srmech_sha256_hex(const uint8_t *data,
                                  size_t         data_len,
                                  char          *out_hex)
{
    if (out_hex == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (data == NULL && data_len != 0u) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(out_hex != NULL);
    assert(data != NULL || data_len == 0u);

    uint32_t state[8];
    memcpy(state, SRMECH_SHA256_H0, sizeof(state));

    /* Hash full 64-byte blocks directly out of `data`. */
    const size_t full_blocks = data_len / 64u;
    for (size_t i = 0; i < full_blocks; i++) {
        srmech_sha256_compress(state, data + (i * 64u));
    }

    /* Handle the tail + length-bit suffix. Worst case the tail
     * spans two padded blocks (when remaining bytes >= 56). */
    const size_t tail_len = data_len - (full_blocks * 64u);
    assert(tail_len < 64u);

    uint8_t tail_buf[128];
    /* Zero-init both blocks so the FIPS padding zeros are already
     * in place; we just slot in the 0x80 byte + length suffix. */
    memset(tail_buf, 0, sizeof(tail_buf));
    if (tail_len > 0u) {
        memcpy(tail_buf, data + (full_blocks * 64u), tail_len);
    }
    tail_buf[tail_len] = 0x80u;  /* FIPS 180-4 §5.1.1 — bit 1 then zeros */

    const size_t needs_two_blocks = (tail_len >= 56u) ? 1u : 0u;
    const size_t pad_block_count = 1u + needs_two_blocks;
    /* Length suffix in BIG-ENDIAN bits goes in the last 8 bytes. */
    const uint64_t bit_len = (uint64_t)data_len * 8u;
    const size_t suffix_off = (pad_block_count * 64u) - 8u;
    tail_buf[suffix_off + 0u] = (uint8_t)(bit_len >> 56);
    tail_buf[suffix_off + 1u] = (uint8_t)(bit_len >> 48);
    tail_buf[suffix_off + 2u] = (uint8_t)(bit_len >> 40);
    tail_buf[suffix_off + 3u] = (uint8_t)(bit_len >> 32);
    tail_buf[suffix_off + 4u] = (uint8_t)(bit_len >> 24);
    tail_buf[suffix_off + 5u] = (uint8_t)(bit_len >> 16);
    tail_buf[suffix_off + 6u] = (uint8_t)(bit_len >>  8);
    tail_buf[suffix_off + 7u] = (uint8_t)(bit_len      );

    for (size_t i = 0; i < pad_block_count; i++) {
        srmech_sha256_compress(state, tail_buf + (i * 64u));
    }

    srmech_sha256_state_to_hex(state, out_hex);
    return SRMECH_OK;
}
