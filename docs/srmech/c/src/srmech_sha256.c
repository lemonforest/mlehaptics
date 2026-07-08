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
 * License: MIT.
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
 * Apply the FIPS 180-4 §5.1.1 padding + length suffix to close a hash.
 *
 * `state` holds the running hash AFTER every full 64-byte block of the
 * message has been compressed; `tail` is the final partial block
 * (`tail_len` < 64 bytes; may be NULL iff tail_len == 0); `total_bytes`
 * is the COMPLETE message length in bytes (drives the 64-bit big-endian
 * length suffix). On return `state` holds the final digest words. Shared
 * by srmech_sha256_hex + the HMAC construction so the padding logic
 * lives in exactly one place.
 * ------------------------------------------------------------------ */
static void srmech_sha256_finalize(uint32_t state[8], const uint8_t *tail,
                                   size_t tail_len, uint64_t total_bytes)
{
    assert(state != NULL);
    assert(tail != NULL || tail_len == 0u);
    assert(tail_len < 64u);

    uint8_t buf[128];
    /* Zero-init both blocks so the FIPS padding zeros are already in
     * place; we just slot in the 0x80 byte + the length suffix. */
    memset(buf, 0, sizeof(buf));
    if (tail_len > 0u) {
        memcpy(buf, tail, tail_len);
    }
    buf[tail_len] = 0x80u;
    const size_t nb = (tail_len >= 56u) ? 2u : 1u;
    const uint64_t bit_len = total_bytes * 8u;
    const size_t off = (nb * 64u) - 8u;
    for (size_t i = 0; i < 8u; i++) {
        buf[off + i] = (uint8_t)(bit_len >> (56u - (8u * i)));
    }
    for (size_t i = 0; i < nb; i++) {
        srmech_sha256_compress(state, buf + (i * 64u));
    }
}

/* ------------------------------------------------------------------ *
 * Serialise the 8 hash words as 32 big-endian bytes (the RAW digest).
 * ------------------------------------------------------------------ */
static void srmech_sha256_words_be(const uint32_t state[8], uint8_t out[32])
{
    assert(state != NULL);
    assert(out != NULL);
    for (size_t i = 0; i < 8u; i++) {
        const uint32_t w = state[i];
        out[(i * 4u) + 0u] = (uint8_t)(w >> 24);
        out[(i * 4u) + 1u] = (uint8_t)(w >> 16);
        out[(i * 4u) + 2u] = (uint8_t)(w >>  8);
        out[(i * 4u) + 3u] = (uint8_t)(w      );
    }
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

    /* Handle the tail + length-bit suffix via the shared FIPS finalize
     * (worst case the tail spans two padded blocks when remaining >= 56). */
    const size_t tail_len = data_len - (full_blocks * 64u);
    srmech_sha256_finalize(state, data + (full_blocks * 64u), tail_len,
                           (uint64_t)data_len);

    srmech_sha256_state_to_hex(state, out_hex);
    return SRMECH_OK;
}

/* ------------------------------------------------------------------ *
 * One-shot RAW 32-byte SHA-256 digest of `data[0..len)`. Used inside the
 * HMAC construction below to (a) compress an over-length key per RFC 2104
 * and (b) reduce the inner/outer blocks. Byte-identical to the leading 32
 * bytes decoded from srmech_sha256_hex — a raw view, not a new hash.
 * ------------------------------------------------------------------ */
static void srmech_sha256_raw(const uint8_t *data, size_t len, uint8_t out[32])
{
    assert(data != NULL || len == 0u);
    assert(out != NULL);
    uint32_t state[8];
    memcpy(state, SRMECH_SHA256_H0, sizeof(state));
    const size_t full = len / 64u;
    for (size_t i = 0; i < full; i++) {
        srmech_sha256_compress(state, data + (i * 64u));
    }
    srmech_sha256_finalize(state, data + (full * 64u), len - (full * 64u),
                           (uint64_t)len);
    srmech_sha256_words_be(state, out);
}

/* ------------------------------------------------------------------ *
 * One HMAC "half": digest = sha256(pad_block(64) || data(data_len)),
 * computed INCREMENTALLY (compress the 64-byte ipad/opad block first, then
 * the message block-by-block) so NO key||msg concatenation buffer is needed
 * and `data_len` may be arbitrarily long. `pad_block` is the ipad or opad.
 * ------------------------------------------------------------------ */
static void srmech_hmac_half(const uint8_t pad_block[64],
                             const uint8_t *data, size_t data_len,
                             uint8_t out[32])
{
    assert(pad_block != NULL);
    assert(data != NULL || data_len == 0u);
    uint32_t state[8];
    memcpy(state, SRMECH_SHA256_H0, sizeof(state));
    srmech_sha256_compress(state, pad_block);
    const size_t full = data_len / 64u;
    for (size_t i = 0; i < full; i++) {
        srmech_sha256_compress(state, data + (i * 64u));
    }
    srmech_sha256_finalize(state, data + (full * 64u), data_len - (full * 64u),
                           (uint64_t)(64u + data_len));
    srmech_sha256_words_be(state, out);
}

/* ------------------------------------------------------------------ *
 * Public entry — declared in srmech.h.
 *
 * Standard RFC 2104 HMAC-SHA-256 over the srmech SHA-256 compression: the
 * RAW 32-byte MAC of `msg` under `key` is written to `out32`. Byte-exact
 * with Python `hmac.new(key, msg, "sha256").digest()` and the RFC 4231
 * test vectors. Block size B = 64; ipad/opad = 0x36/0x5c; an over-length
 * key (> 64 bytes) is first reduced with SHA-256 per the spec. Bounded
 * stack only (JPL Rule 3 — no malloc); arbitrary key_len / msg_len.
 * ------------------------------------------------------------------ */
srmech_status_t srmech_hmac_sha256(const uint8_t *key, size_t key_len,
                                   const uint8_t *msg, size_t msg_len,
                                   uint8_t *out32)
{
    if (out32 == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if ((key == NULL && key_len != 0u) || (msg == NULL && msg_len != 0u)) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(out32 != NULL);
    assert(key != NULL || key_len == 0u);

    uint8_t k0[64];
    memset(k0, 0, sizeof(k0));
    if (key_len > 64u) {
        srmech_sha256_raw(key, key_len, k0);     /* K0 = H(key) || 0-pad */
    } else if (key_len > 0u) {
        memcpy(k0, key, key_len);                /* K0 = key   || 0-pad */
    }
    uint8_t ipad[64];
    uint8_t opad[64];
    for (size_t i = 0; i < 64u; i++) {
        ipad[i] = (uint8_t)(k0[i] ^ 0x36u);
        opad[i] = (uint8_t)(k0[i] ^ 0x5cu);
    }
    uint8_t inner[32];
    srmech_hmac_half(ipad, msg, msg_len, inner);
    srmech_hmac_half(opad, inner, 32u, out32);
    return SRMECH_OK;
}
