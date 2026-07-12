/*
 * srmech_rbs_lm.c — RBS-LM Klein-4 word/context encode C peers
 * (v0.9.0rc219; gh #827 — the encode-pipeline's other half).
 *
 * The C mirror of the `srmech.rbs_lm.substrate` encode kernels — the per-token
 * loop an autoregressive RBS-LM pays PER WINDOW at inference/encode time:
 *
 *   - srmech_rbs_lm_encode_word    : one token → its Klein-4 word vector
 *                                    (byteglyph = klein4_encode_bytes ∘ sector
 *                                    bind; wordhash = sha256-seeded
 *                                    klein4_random ∘ sector bind)
 *   - srmech_rbs_lm_encode_context : the WHOLE last-k-token window → ONE
 *                                    Klein-4 context state (per-token encode +
 *                                    positional role-filler bind + odd-padded
 *                                    majority bundle) in ONE call
 *
 * Profile-first rationale (#827): at D=4096, k=16 the Python encode_context
 * measured 127 ms/window — ~90%+ Python per-token orchestration + k separate
 * FFI hops (each paying ctypes marshal + array copy around the C body). This
 * peer collapses the loop into one crossing. Profiling the collapsed call
 * showed the residual cost is the MT19937 mints themselves (~85 µs each at
 * D=4096; ~260 per byteglyph window) — and the byte-vocab vectors (seeds
 * 0..255), the byteglyph position keys (seeds 0x10000+i) and the window
 * position keys ("__ctx_pos_{p}__") are all WINDOW-INVARIANT, so the context
 * peer takes an optional caller-owned MINT CACHE (lazily filled, byte-exact
 * by construction — a cached mint is the same bytes as a fresh one): the
 * steady-state window then pays only binds + the majority bundle. That
 * per-window latency is what compounds to the multi-day full-enwiki encode.
 *
 * BYTE-IDENTICAL parity contract (the correctness gate): every op reproduces
 * the pure-Python `srmech.rbs_lm.substrate` result EXACTLY. All the leaves are
 * integer/byte ops — sha256 token seeds (Class A), the CPython-replicating
 * MT19937 klein4_random mint, (F₂)² XOR bind (Class M), per-bit strict
 * majority bundle with ties → 0 — so there is no float anywhere and exact
 * parity is the correct gate (the rc217 srmech_text precedent, NOT the
 * within-tol numeric contract).
 *
 * Composes the EXISTING public C leaves — srmech_sha256_hex,
 * srmech_klein4_random, srmech_klein4_bind, srmech_klein4_bundle_accumulate /
 * _resolve — exactly like srmech_klein4_compose does (the model composite).
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto)        : OK
 *   - Rule 2 (bounded loops)  : OK — loops bounded by input sizes
 *   - Rule 3 (no malloc)      : OK — caller-arena only (acc + scratch + cache)
 *   - Rule 4 (≤60 lines/func) : OK
 *   - Rule 5 (≥2 asserts/func): OK
 *   - Rule 8 (simple macros)  : OK — none beyond the seed-word bound
 *
 * No abs(): the seed-magnitude branch never occurs here (sha256 prefixes are
 * non-negative by construction); everything else is XOR / majority.
 */

#include "srmech.h"

#include <assert.h>
#include <stddef.h>
#include <stdint.h>

/* A sha256 hex digest is 64 nibbles → the token seed value is ≤ 256 bits =
 * at most 8 little-endian uint32 key words (CPython init_by_array shape). */
#define SRMECH_RBS_SEED_WORDS_MAX 8u

/* The position-namespaced seed base for the byteglyph per-byte role keys —
 * byte-identical to hdc._KLEIN4_POS_SEED_BASE (and srmech_hdc.c's own
 * SRMECH_KLEIN4_POS_SEED_BASE; re-stated here as this TU composes only the
 * PUBLIC leaf symbols). */
#define SRMECH_RBS_POS_SEED_BASE 0x10000u

/* enc_mode discriminants (mirror substrate.py enc_mode strings). */
#define SRMECH_RBS_MODE_BYTEGLYPH 0u
#define SRMECH_RBS_MODE_WORDHASH  1u

/* "no cache row" sentinel for the mint helpers. */
#define SRMECH_RBS_NO_SLOT UINT32_MAX

/* The caller-owned window-invariant mint cache (see the header contract):
 * rows = (256 + n_bytepos + n_ctxpos) D-byte rows — [0,256) the byte vocab
 * (seed = byte value), [256, 256+n_bytepos) the byteglyph position keys
 * (seed 0x10000+i), [256+n_bytepos, ...) the RAW window position-key mints
 * (pre-sector-bind) — with one lazily-set occupancy flag byte per row.
 * rows == NULL disables caching entirely. */
typedef struct rbs_mint_cache {
    uint8_t  *rows;
    uint8_t  *flags;
    uint32_t  n_bytepos;
    uint32_t  n_ctxpos;
} rbs_mint_cache_t;

/* ------------------------------------------------------------------ *
 * Seed helpers
 * ------------------------------------------------------------------ */

/* One hex nibble value (lowercase srmech_sha256_hex output). */
static uint32_t rbs_hexval(uint8_t c)
{
    assert((c >= (uint8_t)'0' && c <= (uint8_t)'9') ||
           (c >= (uint8_t)'a' && c <= (uint8_t)'f'));
    assert(c != 0u);
    if (c >= (uint8_t)'a') { return (uint32_t)(c - (uint8_t)'a') + 10u; }
    return (uint32_t)(c - (uint8_t)'0');
}

/* token_seed(name, hex_chars) → the CPython random.Random(seed) init_by_array
 * key: sha256(name) hex prefix of `hex_chars` nibbles as a big-endian value,
 * split into little-endian uint32 words with the Python _seed_to_le_words
 * word-count rule (nwords = ceil(bit_length/32), minimum 1 — leading-zero
 * nibbles SHRINK the key, which is load-bearing for MT19937 parity). */
static srmech_status_t rbs_seed_words(const uint8_t *name, size_t name_len,
                                      uint32_t hex_chars, uint32_t *words,
                                      size_t *out_nwords)
{
    char hex[65];
    srmech_status_t st;
    size_t top = 0;
    int nonzero = 0;
    assert(words != NULL && out_nwords != NULL);
    assert(hex_chars >= 1u && hex_chars <= 64u);
    st = srmech_sha256_hex(name, name_len, hex);
    if (st != SRMECH_OK) { return st; }
    for (size_t w = 0; w < SRMECH_RBS_SEED_WORDS_MAX; w++) { words[w] = 0u; }
    for (uint32_t j = 0; j < hex_chars; j++) {
        uint32_t shift = 4u * (hex_chars - 1u - j);
        words[shift >> 5] |= rbs_hexval((uint8_t)hex[j]) << (shift & 31u);
    }
    for (size_t w = SRMECH_RBS_SEED_WORDS_MAX; w > 0u; w--) {
        if (words[w - 1u] != 0u) { top = w - 1u; nonzero = 1; break; }
    }
    *out_nwords = nonzero ? (top + 1u) : 1u;   /* value 0 → the [0] key */
    return SRMECH_OK;
}

/* Mint D Klein-4 codes for a SMALL single-word integer seed (the 256-byte
 * vocab seeds 0..255 / the 0x10000+i position keys / the empty-token atom). */
static srmech_status_t rbs_mint_u32(uint32_t seed, uint32_t D, uint8_t *out)
{
    uint32_t key = seed;
    assert(out != NULL);
    assert(D >= 1u);
    return srmech_klein4_random(&key, (size_t)1, D, out);
}

/* The D-byte mint for a small integer `seed` — from cache row `slot` when the
 * cache is active and slot != SRMECH_RBS_NO_SLOT (lazily minting into the row
 * on first use; a cached mint is byte-identical to a fresh one), else minted
 * into `fallback`. Returns the vector pointer, or NULL with *st set. */
static const uint8_t *rbs_vec_u32(const rbs_mint_cache_t *mc, uint32_t slot,
                                  uint32_t seed, uint32_t D,
                                  uint8_t *fallback, srmech_status_t *st)
{
    assert(mc != NULL && fallback != NULL && st != NULL);
    assert(D >= 1u);
    if (mc->rows != NULL && slot != SRMECH_RBS_NO_SLOT) {
        uint8_t *row = &mc->rows[(size_t)slot * D];
        if (mc->flags[slot] == 0u) {
            *st = rbs_mint_u32(seed, D, row);
            if (*st != SRMECH_OK) { return NULL; }
            mc->flags[slot] = 1u;
        }
        *st = SRMECH_OK;
        return row;
    }
    *st = rbs_mint_u32(seed, D, fallback);
    return (*st == SRMECH_OK) ? fallback : NULL;
}

/* XOR the constant sector key into a D-byte Klein-4 vector in place — the
 * klein4_bind(v, sector_const(D, sector)) of the pure path (bind with a
 * constant vector IS the elementwise XOR; sector ≤ 3 keeps codes in-range). */
static void rbs_sector_bind(uint8_t *v, uint32_t D, uint8_t sector)
{
    assert(v != NULL);
    assert(sector <= 3u);
    for (uint32_t i = 0; i < D; i++) {
        v[i] = (uint8_t)(v[i] ^ sector);
    }
}

/* ------------------------------------------------------------------ *
 * Word encode core (shared by both public symbols)
 * ------------------------------------------------------------------ */

/* klein4_encode_bytes(data, D) — the §60/F864 byte-composed word vector:
 * bundle_i( bind(klein4_random(D, seed=data[i]), klein4_random(D, seed=
 * 0x10000+i)) ), ties → 0 (the plain bundle; NO odd-pad here, matching the
 * pure klein4_encode_bytes). The byte-vocab and position-key mints ride the
 * cache when active. acc is a (1 + 2*D) uint32 accumulator; vec / key / bnd
 * are D-byte scratch regions. */
static srmech_status_t rbs_encode_bytes(const uint8_t *data, size_t data_len,
                                        uint32_t D,
                                        const rbs_mint_cache_t *mc,
                                        uint32_t *acc, uint8_t *vec,
                                        uint8_t *key, uint8_t *bnd,
                                        uint8_t *out)
{
    assert(data != NULL && mc != NULL && acc != NULL && out != NULL);
    assert(data_len >= 1u && D >= 1u);
    for (size_t k = 0; k < (size_t)1u + (size_t)2u * D; k++) { acc[k] = 0u; }
    for (size_t i = 0; i < data_len; i++) {
        srmech_status_t st;
        const uint8_t *vp;
        const uint8_t *kp;
        uint32_t vslot;
        uint32_t kslot;
        if (i > (size_t)(UINT32_MAX - SRMECH_RBS_POS_SEED_BASE)) {
            return SRMECH_ERR_BAD_INPUT;   /* pos seed would overflow u32 */
        }
        vslot = (mc->rows != NULL) ? (uint32_t)data[i] : SRMECH_RBS_NO_SLOT;
        vp = rbs_vec_u32(mc, vslot, (uint32_t)data[i], D, vec, &st);
        if (vp == NULL) { return st; }
        kslot = (mc->rows != NULL && i < (size_t)mc->n_bytepos)
                    ? 256u + (uint32_t)i : SRMECH_RBS_NO_SLOT;
        kp = rbs_vec_u32(mc, kslot, SRMECH_RBS_POS_SEED_BASE + (uint32_t)i,
                         D, key, &st);
        if (kp == NULL) { return st; }
        st = srmech_klein4_bind(vp, kp, D, bnd);
        if (st != SRMECH_OK) { return st; }
        st = srmech_klein4_bundle_accumulate(acc, bnd, (size_t)D);
        if (st != SRMECH_OK) { return st; }
    }
    return srmech_klein4_bundle_resolve(acc, out, (size_t)D);
}

/* enc(tok) — ONE token → its Klein-4 word vector, byte-identical to
 * substrate.encode_word_byteglyph / encode_word_k4:
 *   byteglyph: klein4_encode_bytes(utf8) (empty token → the seed-0 neutral
 *              atom), then the sector bind;
 *   wordhash : klein4_random(D, seed=token_seed(tok, hex_chars)), then the
 *              sector bind. */
static srmech_status_t rbs_encode_word_core(const uint8_t *tok, size_t tok_len,
                                            uint32_t D, uint8_t sector,
                                            uint32_t hex_chars,
                                            uint32_t enc_mode,
                                            const rbs_mint_cache_t *mc,
                                            uint32_t *acc, uint8_t *vec,
                                            uint8_t *key, uint8_t *bnd,
                                            uint8_t *out)
{
    srmech_status_t st;
    assert(mc != NULL && acc != NULL && out != NULL);
    assert(sector <= 3u && D >= 1u);
    if (enc_mode == SRMECH_RBS_MODE_WORDHASH) {
        uint32_t words[SRMECH_RBS_SEED_WORDS_MAX];
        size_t nwords = 0;
        st = rbs_seed_words(tok, tok_len, hex_chars, words, &nwords);
        if (st != SRMECH_OK) { return st; }
        st = srmech_klein4_random(words, nwords, D, out);
    } else if (tok_len == 0u) {
        st = rbs_mint_u32(0u, D, out);           /* the empty/pad atom */
    } else {
        st = rbs_encode_bytes(tok, tok_len, D, mc, acc, vec, key, bnd, out);
    }
    if (st != SRMECH_OK) { return st; }
    rbs_sector_bind(out, D, sector);
    return SRMECH_OK;
}

/* ------------------------------------------------------------------ *
 * srmech_rbs_lm_encode_word — one token → one Klein-4 word vector
 * ------------------------------------------------------------------ */

srmech_status_t srmech_rbs_lm_encode_word(
    const uint8_t *tok, size_t tok_len, uint32_t D, uint8_t sector,
    uint32_t hex_chars, uint32_t enc_mode, uint32_t *acc, uint8_t *scratch,
    uint8_t *out)
{
    rbs_mint_cache_t mc = { NULL, NULL, 0u, 0u };   /* one-shot: uncached */
    assert(acc != NULL && scratch != NULL && out != NULL);
    assert(tok != NULL || tok_len == 0u);
    if (acc == NULL || scratch == NULL || out == NULL ||
        (tok == NULL && tok_len > 0u)) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (D == 0u || sector > 3u ||
        enc_mode > SRMECH_RBS_MODE_WORDHASH ||
        (enc_mode == SRMECH_RBS_MODE_WORDHASH &&
         (hex_chars < 1u || hex_chars > 64u))) {
        return SRMECH_ERR_BAD_INPUT;
    }
    return rbs_encode_word_core(tok, tok_len, D, sector, hex_chars, enc_mode,
                                &mc, acc, &scratch[0], &scratch[D],
                                &scratch[(size_t)2u * D], out);
}

/* ------------------------------------------------------------------ *
 * srmech_rbs_lm_encode_context — the whole k-token window in one call
 * ------------------------------------------------------------------ */

/* Decimal render of a uint32 (no stdio). Returns the digit count. */
static size_t rbs_u32_dec(uint32_t v, uint8_t *dst)
{
    uint8_t tmp[10];
    size_t n = 0;
    assert(dst != NULL);
    tmp[n] = (uint8_t)('0' + (v % 10u));
    n++;
    v /= 10u;
    for (; v > 0u && n < 10u; v /= 10u) {
        tmp[n] = (uint8_t)('0' + (v % 10u));
        n++;
    }
    assert(n >= 1u && n <= 10u);
    for (size_t i = 0; i < n; i++) { dst[i] = tmp[n - 1u - i]; }
    return n;
}

/* The RAW (pre-sector-bind) position-key mint for window slot p: the wordhash
 * atom of the label "__ctx_pos_{p}__" (enc_mode-INDEPENDENT, matching
 * ContextSubstrate.pos_key). */
static srmech_status_t rbs_pos_mint(uint32_t p, uint32_t D, uint32_t hex_chars,
                                    uint8_t *out)
{
    static const uint8_t head[10] = { '_', '_', 'c', 't', 'x', '_',
                                      'p', 'o', 's', '_' };
    uint8_t label[24];
    size_t len = 0;
    uint32_t words[SRMECH_RBS_SEED_WORDS_MAX];
    size_t nwords = 0;
    srmech_status_t st;
    assert(out != NULL);
    assert(D >= 1u);
    for (size_t i = 0; i < sizeof head; i++) { label[len] = head[i]; len++; }
    len += rbs_u32_dec(p, &label[len]);
    label[len] = (uint8_t)'_';
    len++;
    label[len] = (uint8_t)'_';
    len++;
    st = rbs_seed_words(label, len, hex_chars, words, &nwords);
    if (st != SRMECH_OK) { return st; }
    return srmech_klein4_random(words, nwords, D, out);
}

/* pos_key(p) into `key`: the raw mint (from the cache's ctxpos section when
 * active — the pure path's per-instance _poskey dict, mirrored) with the
 * substrate sector bound in. */
static srmech_status_t rbs_pos_key(uint32_t p, uint32_t D, uint8_t sector,
                                   uint32_t hex_chars,
                                   const rbs_mint_cache_t *mc, uint8_t *key)
{
    srmech_status_t st;
    assert(mc != NULL && key != NULL);
    assert(D >= 1u && sector <= 3u);
    if (mc->rows != NULL && p < mc->n_ctxpos) {
        size_t slot = (size_t)256u + (size_t)mc->n_bytepos + (size_t)p;
        uint8_t *row = &mc->rows[slot * D];
        if (mc->flags[slot] == 0u) {
            st = rbs_pos_mint(p, D, hex_chars, row);
            if (st != SRMECH_OK) { return st; }
            mc->flags[slot] = 1u;
        }
        for (uint32_t j = 0; j < D; j++) {
            key[j] = (uint8_t)(row[j] ^ sector);
        }
        return SRMECH_OK;
    }
    st = rbs_pos_mint(p, D, hex_chars, key);
    if (st != SRMECH_OK) { return st; }
    rbs_sector_bind(key, D, sector);
    return SRMECH_OK;
}

/* Fold one window slot into the outer bundle accumulator:
 * klein4_bind(pos_key(p), enc(tok)) — the positional role-filler bind. */
static srmech_status_t rbs_fold_slot(const uint8_t *tok, size_t tok_len,
                                     uint32_t p, uint32_t D, uint8_t sector,
                                     uint32_t hex_chars, uint32_t enc_mode,
                                     const rbs_mint_cache_t *mc,
                                     uint32_t *acc_outer, uint32_t *acc_inner,
                                     uint8_t *scratch)
{
    /* scratch: vec [0,D) + key [D,2D) + bnd [2D,3D) + word [3D,4D) */
    uint8_t *vec  = &scratch[0];
    uint8_t *key  = &scratch[D];
    uint8_t *bnd  = &scratch[(size_t)2u * D];
    uint8_t *word = &scratch[(size_t)3u * D];
    srmech_status_t st;
    assert(mc != NULL && acc_outer != NULL && acc_inner != NULL);
    assert(scratch != NULL && D >= 1u);
    st = rbs_encode_word_core(tok, tok_len, D, sector, hex_chars, enc_mode,
                              mc, acc_inner, vec, key, bnd, word);
    if (st != SRMECH_OK) { return st; }
    st = rbs_pos_key(p, D, sector, hex_chars, mc, key);
    if (st != SRMECH_OK) { return st; }
    st = srmech_klein4_bind(key, word, D, bnd);
    if (st != SRMECH_OK) { return st; }
    return srmech_klein4_bundle_accumulate(acc_outer, bnd, (size_t)D);
}

/* The even-count odd-pad (ContextSubstrate.bundle_odd): an even window —
 * including the empty one — APPENDS the fixed neutral pad enc("__bundle_pad__")
 * rather than dropping a real token. `pad` may be the caller's precomputed
 * D-byte pad vector (the Python substrate caches it); NULL → computed here. */
static srmech_status_t rbs_fold_pad(const uint8_t *pad, uint32_t D,
                                    uint8_t sector, uint32_t hex_chars,
                                    uint32_t enc_mode,
                                    const rbs_mint_cache_t *mc,
                                    uint32_t *acc_outer, uint32_t *acc_inner,
                                    uint8_t *scratch)
{
    static const uint8_t pad_tok[14] = { '_', '_', 'b', 'u', 'n', 'd', 'l',
                                         'e', '_', 'p', 'a', 'd', '_', '_' };
    uint8_t *word = &scratch[(size_t)3u * D];
    srmech_status_t st;
    assert(mc != NULL && acc_outer != NULL && scratch != NULL);
    assert(D >= 1u);
    if (pad != NULL) {
        return srmech_klein4_bundle_accumulate(acc_outer, pad, (size_t)D);
    }
    st = rbs_encode_word_core(pad_tok, sizeof pad_tok, D, sector, hex_chars,
                              enc_mode, mc, acc_inner, &scratch[0],
                              &scratch[D], &scratch[(size_t)2u * D], word);
    if (st != SRMECH_OK) { return st; }
    return srmech_klein4_bundle_accumulate(acc_outer, word, (size_t)D);
}

/* encode_context(window) — the F166 rolling context state: last-k tokens →
 * ONE Klein-4 vector via bundle_p( bind(pos_key(p), enc(token_p)) ) with the
 * even-count odd-pad. Tokens ride as concatenated UTF-8 bytes + n_tokens+1
 * offsets (tok d spans tok_bytes[tok_off[d] .. tok_off[d+1])). mint_cache /
 * mint_flags (both non-NULL or both NULL) carry the window-invariant mints
 * across calls — see the header contract. acc_outer / acc_inner are
 * (1 + 2*D) uint32 caller accumulators; scratch is 4*D caller bytes; out is
 * D bytes. Byte-identical to the pure encode_context. */
srmech_status_t srmech_rbs_lm_encode_context(
    const uint8_t *tok_bytes, const uint32_t *tok_off, uint32_t n_tokens,
    uint32_t D, uint8_t sector, uint32_t hex_chars, uint32_t enc_mode,
    const uint8_t *pad, uint8_t *mint_cache, uint8_t *mint_flags,
    uint32_t n_bytepos, uint32_t n_ctxpos, uint32_t *acc_outer,
    uint32_t *acc_inner, uint8_t *scratch, uint8_t *out)
{
    rbs_mint_cache_t mc;
    srmech_status_t st;
    assert(tok_off != NULL || n_tokens == 0u);
    assert(acc_outer != NULL && acc_inner != NULL);
    assert(scratch != NULL && out != NULL);
    if (acc_outer == NULL || acc_inner == NULL || scratch == NULL ||
        out == NULL || (tok_off == NULL && n_tokens > 0u) ||
        ((mint_cache == NULL) != (mint_flags == NULL))) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (D == 0u || sector > 3u || hex_chars < 1u || hex_chars > 64u ||
        enc_mode > SRMECH_RBS_MODE_WORDHASH) {
        return SRMECH_ERR_BAD_INPUT;
    }
    mc.rows = mint_cache;
    mc.flags = mint_flags;
    mc.n_bytepos = (mint_cache != NULL) ? n_bytepos : 0u;
    mc.n_ctxpos = (mint_cache != NULL) ? n_ctxpos : 0u;
    for (size_t k = 0; k < (size_t)1u + (size_t)2u * D; k++) {
        acc_outer[k] = 0u;
    }
    for (uint32_t p = 0; p < n_tokens; p++) {
        uint32_t lo = tok_off[p];
        uint32_t hi = tok_off[p + 1u];
        const uint8_t *tok;
        if (hi < lo || (tok_bytes == NULL && hi > lo)) {
            return SRMECH_ERR_BAD_INPUT;
        }
        tok = (hi > lo) ? &tok_bytes[lo] : NULL;   /* empty → NULL (no NULL+i) */
        st = rbs_fold_slot(tok, (size_t)(hi - lo), p, D, sector,
                           hex_chars, enc_mode, &mc, acc_outer, acc_inner,
                           scratch);
        if (st != SRMECH_OK) { return st; }
    }
    if ((n_tokens % 2u) == 0u) {
        st = rbs_fold_pad(pad, D, sector, hex_chars, enc_mode, &mc,
                          acc_outer, acc_inner, scratch);
        if (st != SRMECH_OK) { return st; }
    }
    return srmech_klein4_bundle_resolve(acc_outer, out, (size_t)D);
}
