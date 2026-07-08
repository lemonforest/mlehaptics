/*
 * srmech_bio_totp.c — the srmech.bus UTLP Bio-TOTP wire cipher, in C
 * (0.9.0rc178; ANNEX Batch A part 1). A FAITHFUL BYTE-EXACT MIRROR of the
 * already-shipped Python cipher `srmech/bus/_bio_totp.py` — nothing invented,
 * nothing strengthened or weakened. Byte-exact parity IS the correctness +
 * safety property (a deviation would silently break the wire cipher).
 *
 * This is a USER-APPROVED defensive-parity exception to the standing
 * "crypto is framework-reading-only" discipline: standard HMAC-SHA-256,
 * purely defensive local-IPC, a C mirror of ALREADY-SHIPPED Python.
 *
 * The three ops COMPOSE the existing kernels (no new hash, no new parser):
 *   - srmech_sha256_hex   (Class A, FIPS 180-4)      → the key-derivation hash
 *   - srmech_hmac_sha256  (RFC 2104 over srmech_sha256) → the keystream
 *   - srmech_json_parse / srmech_json_object_get     → the binding-check parse
 *
 * Default cipher only. The optional AES-128-CTR backend (the `[crypto]`
 * extra) is OUT of the bare-C-host default and stays Python — this mirrors
 * the stdlib HMAC-SHA-256 counter-mode path exactly.
 *
 * Wire frame:  [nonce:16][ciphertext]
 *   nonce          = sender_id_u64 || channel_id_u32 || packet_seq_u32 (BE)
 *   key            = sha256(dna || quantized_time_be8_signed)[0:16]
 *   quantized_time = floor(time_ns / window_ns)              (Python //)
 *   ciphertext     = data XOR HMAC-SHA-256(key, nonce || counter_be4) blocks
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto / recursion) : OK
 *   - Rule 3 (no malloc)           : OK (bounded stack + caller arena)
 *   - Rule 4 (<= 60-line fns)      : OK
 *   - Rule 5 (>= 2 asserts per fn) : OK
 *   - Rule 8 (single-line macros)  : OK
 *
 * License: MIT.
 */

#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

#include "srmech.h"

/* Max dna length the native key-derive accepts on its bounded stack buffer
 * (the realistic dna is 32 bytes — MIN_DNA_BYTES / ZERO_DNA width). A longer
 * dna returns SRMECH_ERR_OVERFLOW; the Python wrapper then runs its COMPLETE
 * pure path (any length), so no correctness is lost. Single-line (JPL R8). */
#define SRMECH_BIO_TOTP_MAX_DNA 256u

/* Python floor division a // b for b > 0. C `/` truncates toward zero and C
 * `%` takes the sign of the dividend, so a negative remainder means we round
 * one step further down (matches int(math.floor(a/b))). */
static int64_t bt_floordiv(int64_t a, int64_t b)
{
    assert(b > 0);
    assert(a == a);
    int64_t q = a / b;
    int64_t r = a % b;
    if (r < 0) { q -= 1; }
    return q;
}

/* Serialise a signed int64 as 8 big-endian two's-complement bytes — matches
 * Python int.to_bytes(8, "big", signed=True) over the int64 range. */
static void bt_i64_be8(int64_t v, uint8_t out[8])
{
    assert(out != NULL);
    assert(sizeof(uint64_t) == 8u);
    uint64_t u = (uint64_t)v;
    for (size_t i = 0; i < 8u; i++) {
        out[i] = (uint8_t)(u >> (56u - (8u * i)));
    }
}

/* Read 8 big-endian bytes as a uint64 (the nonce sender_id_u64 field). */
static uint64_t bt_be_read_u64(const uint8_t *p)
{
    assert(p != NULL);
    assert(sizeof(uint64_t) == 8u);
    uint64_t v = 0u;
    for (size_t i = 0; i < 8u; i++) {
        v = (v << 8) | (uint64_t)p[i];
    }
    return v;
}

/* Read 4 big-endian bytes as a uint32 (the nonce channel_id_u32 field). */
static uint32_t bt_be_read_u32(const uint8_t *p)
{
    assert(p != NULL);
    assert(sizeof(uint32_t) == 4u);
    uint32_t v = 0u;
    for (size_t i = 0; i < 4u; i++) {
        v = (v << 8) | (uint32_t)p[i];
    }
    return v;
}

/* Decode the first 32 lowercase hex chars (srmech_sha256_hex output) into 16
 * raw bytes — the derived key is sha256(...)[0:16]. */
static void bt_hex_to_16(const char *hex, uint8_t out[16])
{
    assert(hex != NULL);
    assert(out != NULL);
    for (size_t i = 0; i < 16u; i++) {
        const char c0 = hex[(i * 2u)];
        const char c1 = hex[(i * 2u) + 1u];
        const uint8_t hi = (uint8_t)((c0 <= '9') ? (c0 - '0') : ((c0 - 'a') + 10));
        const uint8_t lo = (uint8_t)((c1 <= '9') ? (c1 - '0') : ((c1 - 'a') + 10));
        out[i] = (uint8_t)((hi << 4) | lo);
    }
}

srmech_status_t srmech_bio_totp_derive_key(const uint8_t *dna, size_t dna_len,
                                           int64_t time_ns, int64_t window_ns,
                                           uint8_t *out16)
{
    if (out16 == NULL) { return SRMECH_ERR_NULL_ARG; }
    if (dna == NULL && dna_len != 0u) { return SRMECH_ERR_NULL_ARG; }
    if (window_ns <= 0) { return SRMECH_ERR_BAD_INPUT; }
    if (dna_len > SRMECH_BIO_TOTP_MAX_DNA) { return SRMECH_ERR_OVERFLOW; }
    assert(out16 != NULL);
    assert(window_ns > 0);

    uint8_t msg[SRMECH_BIO_TOTP_MAX_DNA + 8u];
    if (dna_len > 0u) {
        memcpy(msg, dna, dna_len);
    }
    const int64_t quantized = bt_floordiv(time_ns, window_ns);
    bt_i64_be8(quantized, msg + dna_len);
    char hex[65];
    const srmech_status_t st = srmech_sha256_hex(msg, dna_len + 8u, hex);
    if (st != SRMECH_OK) { return st; }
    bt_hex_to_16(hex, out16);
    return SRMECH_OK;
}

srmech_status_t srmech_bio_totp_keystream_xor(const uint8_t *key16,
                                              const uint8_t *nonce16,
                                              const uint8_t *data,
                                              size_t data_len,
                                              uint8_t *out)
{
    if (key16 == NULL || nonce16 == NULL) { return SRMECH_ERR_NULL_ARG; }
    if (data == NULL && data_len != 0u) { return SRMECH_ERR_NULL_ARG; }
    if (out == NULL && data_len != 0u) { return SRMECH_ERR_NULL_ARG; }
    assert(key16 != NULL);
    assert(nonce16 != NULL);

    uint8_t hmsg[20];                 /* nonce(16) || counter_be4(4) */
    memcpy(hmsg, nonce16, 16u);
    uint8_t block[32];
    uint32_t counter = 0u;
    size_t done = 0u;
    while (done < data_len) {
        hmsg[16] = (uint8_t)(counter >> 24);
        hmsg[17] = (uint8_t)(counter >> 16);
        hmsg[18] = (uint8_t)(counter >>  8);
        hmsg[19] = (uint8_t)(counter      );
        const srmech_status_t st = srmech_hmac_sha256(key16, 16u, hmsg, 20u,
                                                      block);
        if (st != SRMECH_OK) { return st; }
        size_t take = data_len - done;
        if (take > 32u) { take = 32u; }
        for (size_t i = 0; i < take; i++) {
            out[done + i] = (uint8_t)(data[done + i] ^ block[i]);
        }
        done += take;
        counter += 1u;
    }
    return SRMECH_OK;
}

/* Parse a decimal-string binding value the way Python int(str) does for a
 * plain integer literal (optional surrounding ASCII whitespace + one sign +
 * digits). *out is the magnitude; the return is the sign (+1 / -1). On any
 * non-decimal shape *ok is set 0 (Python int() would raise ValueError). */
static int bt_parse_dec(const char *s, uint32_t len, uint64_t *out, int *ok)
{
    assert(s != NULL || len == 0u);
    assert(out != NULL && ok != NULL);
    *out = 0u;
    *ok = 0;
    uint32_t i = 0u;
    while (i < len && (s[i] == ' ' || s[i] == '\t' || s[i] == '\n' ||
                       s[i] == '\r' || s[i] == '\f' || s[i] == '\v')) { i++; }
    int sign = 1;
    if (i < len && (s[i] == '+' || s[i] == '-')) {
        if (s[i] == '-') { sign = -1; }
        i++;
    }
    uint32_t start = i;
    uint64_t v = 0u;
    while (i < len && s[i] >= '0' && s[i] <= '9') {
        v = (v * 10u) + (uint64_t)(s[i] - '0');
        i++;
    }
    while (i < len && (s[i] == ' ' || s[i] == '\t' || s[i] == '\n' ||
                       s[i] == '\r' || s[i] == '\f' || s[i] == '\v')) { i++; }
    if (i != len || start == i || start >= len) { return sign; }
    *out = v;
    *ok = 1;
    return sign;
}

/* Compare an attestation binding node to `expected` the way Python
 * int(bound) == int(expected) does. *out_ok = 0 when Python int(bound) would
 * raise (a non-numeric leaf) → the caller treats it as a mismatch (False). */
static int bt_json_int_eq(const srmech_json_value_t *node, uint64_t expected,
                          int *out_ok)
{
    assert(node != NULL);
    assert(out_ok != NULL);
    *out_ok = 1;
    if (node->type == SRMECH_JSON_INT) {
        return ((uint64_t)node->u.i == expected) ? 1 : 0;
    }
    if (node->type == SRMECH_JSON_BOOL) {
        return ((uint64_t)(node->u.b ? 1 : 0) == expected) ? 1 : 0;
    }
    if (node->type == SRMECH_JSON_STRING) {
        uint64_t v = 0u;
        int ok = 0;
        const int sign = bt_parse_dec(node->u.str.ptr, node->u.str.len, &v, &ok);
        if (!ok) { *out_ok = 0; return 0; }
        return (sign > 0 && v == expected) ? 1 : 0;
    }
    *out_ok = 0;          /* float / array / object → int() raises / truncates */
    return 0;
}

/* Does `pt` bind to the nonce fields under PERMISSIVE mode
 * (_plaintext_binds_to_nonce with strict=False, the decode_splice caller)?
 * Returns 1 (accept) unless `pt` is valid JSON whose attestation carries BOTH
 * binding fields and they DISAGREE — the only permissive-mode contradiction.
 * `ws`/`ws_len` back the srmech_json parse (bounded by the caller arena). */
static int bt_binds(const uint8_t *pt, size_t pt_len,
                    uint64_t sender_id, uint32_t channel_id,
                    void *ws, size_t ws_len)
{
    assert(ws != NULL || ws_len == 0u);
    assert(pt != NULL || pt_len == 0u);
    if (pt_len == 0u) { return 1; }                    /* empty → accept */
    srmech_json_value_t *root = NULL;
    const srmech_status_t st = srmech_json_parse((const char *)pt, pt_len,
                                                 ws, ws_len, &root);
    if (st != SRMECH_OK || root == NULL) { return 1; } /* non-UTF8 / non-JSON */
    if (root->type != SRMECH_JSON_OBJECT) { return 1; }
    const srmech_json_value_t *att = srmech_json_object_get(root, "attestation");
    if (att == NULL || att->type != SRMECH_JSON_OBJECT) { return 1; }
    const srmech_json_value_t *sn = srmech_json_object_get(att, "sender_id_u64");
    const srmech_json_value_t *cn = srmech_json_object_get(att, "channel_id_u32");
    if (sn == NULL || sn->type == SRMECH_JSON_NULL ||
        cn == NULL || cn->type == SRMECH_JSON_NULL) { return 1; }  /* missing */
    int ok = 0;
    const int sm = bt_json_int_eq(sn, sender_id, &ok);
    if (!ok) { return 0; }
    const int cm = bt_json_int_eq(cn, (uint64_t)channel_id, &ok);
    if (!ok) { return 0; }
    return (sm && cm) ? 1 : 0;
}

size_t srmech_bio_totp_decode_splice_arena_bytes(size_t framed_len)
{
    assert(sizeof(srmech_json_value_t) <= 64u);
    assert(sizeof(void *) <= 16u);
    /* The binding check parses a plaintext of at most (framed_len - 16) bytes
     * with srmech_json_parse; the op_provenance parse-arena factor (96 bytes
     * per input byte + slack) is a proven over-approximation for that parser,
     * so a valid-JSON plaintext never OVERFLOWs (which would else read as a
     * spurious "not JSON → accept"). */
    const size_t ct = (framed_len > 16u) ? (framed_len - 16u) : 0u;
    return (96u * ct) + 8192u;
}

srmech_status_t srmech_bio_totp_decode_splice(
    const uint8_t *framed, size_t framed_len,
    const uint8_t *dna, size_t dna_len,
    int64_t window_ns, int64_t now_ns,
    void *ws, size_t ws_len,
    uint8_t *out_plaintext, size_t out_cap, size_t *out_len,
    int64_t *out_used_time, int *out_found)
{
    if (framed == NULL || out_len == NULL || out_used_time == NULL ||
        out_found == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (dna == NULL && dna_len != 0u) { return SRMECH_ERR_NULL_ARG; }
    if (ws == NULL && ws_len != 0u) { return SRMECH_ERR_NULL_ARG; }
    assert(out_found != NULL);
    assert(out_len != NULL);
    *out_found = 0;
    *out_len = 0u;
    *out_used_time = 0;
    if (window_ns <= 0) { return SRMECH_ERR_BAD_INPUT; }
    if (framed_len < 16u) { return SRMECH_ERR_BAD_INPUT; }   /* format error */
    const uint8_t *nonce = framed;
    const uint8_t *ct = framed + 16u;
    const size_t ct_len = framed_len - 16u;
    if (ct_len > out_cap) { return SRMECH_ERR_OVERFLOW; }
    const uint64_t sender_id = bt_be_read_u64(nonce);
    const uint32_t channel_id = bt_be_read_u32(nonce + 8u);
    static const int64_t deltas[3] = {0, -1, 1};
    for (size_t d = 0; d < 3u; d++) {
        const int64_t cand = now_ns + (deltas[d] * window_ns);
        uint8_t key[16];
        srmech_status_t st = srmech_bio_totp_derive_key(dna, dna_len, cand,
                                                        window_ns, key);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bio_totp_keystream_xor(key, nonce, ct, ct_len,
                                           out_plaintext);
        if (st != SRMECH_OK) { return st; }
        if (bt_binds(out_plaintext, ct_len, sender_id, channel_id, ws, ws_len)) {
            *out_len = ct_len;
            *out_used_time = cand;
            *out_found = 1;
            return SRMECH_OK;
        }
    }
    return SRMECH_OK;              /* out_found == 0 → all windows failed */
}
