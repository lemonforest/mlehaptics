/*
 * srmech_text.c — text → tokens → co-occurrence-edge ingestion C peers
 * (v0.9.0rc217; gh #1360).
 *
 * The C mirror of `srmech.amsc.text` — the §40/§52 text→graph leaves of the
 * RBS-LM K1 presence-kernel chain `text → tokenize → cooccurrence_edges →
 * dense_laplacian`. These three ops shipped rc50/§52 as pure-Python kernels
 * and were MIS-CLASSIFIED non_compute/composes_c in the Rosetta ledger (the
 * hiding-spot the rc217 ledger fix closes): the tokenize per-codepoint loop +
 * the windowed pair-count accumulation are THE dominant corpus-encode cost
 * (the full-enwiki comprehended-encode estimated ~6 days with the hot loop in
 * Python on a native wheel — no C symbol existed to dispatch to).
 *
 *   - srmech_text_tokenize            : Unicode content-token segmentation
 *   - srmech_text_cooccurrence_edges  : windowed pair-count → sorted edge list
 *   - srmech_text_cooccurrence_topk   : bounded top-K chunk flush (§52 stream)
 *   - srmech_text_cooccurrence_topk_extract : per-node top-K + edge read-out
 *
 * BYTE-IDENTICAL parity contract (the correctness gate): every op reproduces
 * the pure-Python `srmech.amsc.text` result EXACTLY — token stream, integer
 * pair counts, deterministic tie-breaks ((-weight, index) ranking, first-seen
 * edge weights, lexicographic edge order) — or the downstream Laplacian would
 * differ between hosts.
 *
 * Unicode tables are CALLER-PROVIDED (the srmech caller-arena discipline
 * applied to data): the Python wrapper builds — once per process, from the
 * RUNNING interpreter's `unicodedata` — (a) the kept-bitset (one bit per
 * codepoint: category major class L or M), and (b) the casefold exception
 * table (codepoint → folded UTF-8, only the ~1.5k non-identity rows). So
 * native == pure is byte-identical BY CONSTRUCTION on ANY interpreter /
 * Unicode version (no vendored Unicode data to drift against the host's).
 * A bare-C host supplies its own tables (they are inputs, like the stoplist).
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto)        : OK
 *   - Rule 2 (bounded loops)  : OK — loops bounded by input sizes / guarded
 *   - Rule 3 (no malloc)      : OK — caller-arena only (hash + scratch)
 *   - Rule 4 (≤60 lines/func) : OK
 *   - Rule 5 (≥2 asserts/func): OK
 *   - Rule 8 (simple macros)  : OK — none beyond the codepoint-space bound
 *
 * No abs(): weights are unsigned exact integers; ranking uses the ~w
 * (bitwise-complement) ascending transform, a Class-K pin-slot reordering,
 * never a sign strip.
 */

#include "srmech.h"

#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

/* Unicode codepoint space: the kept-bitset is 0x110000 bits (139264 bytes),
 * one per codepoint. */
#define SRMECH_TEXT_MAX_CP 0x110000u

/* ------------------------------------------------------------------ *
 * UTF-8 + table helpers
 * ------------------------------------------------------------------ */

/* Decode one UTF-8 codepoint at *io_i. Returns 1 on success (cp + byte span
 * out, *io_i advanced), 0 on malformed input. Expects well-formed UTF-8 (the
 * Python wrapper passes `str.encode("utf-8")`); rejects stray continuation
 * bytes, truncated sequences, out-of-range and surrogate codepoints. */
static int txt_utf8_next(const uint8_t *s, size_t len, size_t *io_i,
                         uint32_t *out_cp, size_t *out_nb)
{
    uint32_t cp;
    size_t   nb;
    size_t   i;
    uint8_t  b0;
    assert(s != NULL && io_i != NULL);
    assert(out_cp != NULL && out_nb != NULL);
    i = *io_i;
    if (i >= len) { return 0; }
    b0 = s[i];
    if (b0 < 0x80u)      { cp = b0;          nb = 1u; }
    else if (b0 < 0xC2u) { return 0; }               /* cont byte / overlong */
    else if (b0 < 0xE0u) { cp = b0 & 0x1Fu;  nb = 2u; }
    else if (b0 < 0xF0u) { cp = b0 & 0x0Fu;  nb = 3u; }
    else if (b0 < 0xF5u) { cp = b0 & 0x07u;  nb = 4u; }
    else                 { return 0; }
    if (nb > len - i) { return 0; }
    for (size_t j = 1; j < nb; j++) {
        uint8_t b = s[i + j];
        if ((b & 0xC0u) != 0x80u) { return 0; }
        cp = (cp << 6) | (uint32_t)(b & 0x3Fu);
    }
    if (cp >= SRMECH_TEXT_MAX_CP) { return 0; }
    if (cp >= 0xD800u && cp < 0xE000u) { return 0; }  /* surrogate */
    *out_cp = cp;
    *out_nb = nb;
    *io_i   = i + nb;
    return 1;
}

/* Is `cp` a kept codepoint (Unicode category major class L or M) per the
 * caller-built bitset? Bit cp of `bits` (LSB-first within each byte). */
static int txt_kept(const uint8_t *bits, uint32_t cp)
{
    assert(bits != NULL);
    assert(cp < SRMECH_TEXT_MAX_CP);
    return (int)((bits[cp >> 3] >> (cp & 7u)) & 1u);
}

/* Binary-search the sorted casefold exception table for `cp`. Returns the
 * row index, or SIZE_MAX when `cp` folds to itself (the identity default). */
static size_t txt_fold_find(const uint32_t *fold_cps, size_t n_folds,
                            uint32_t cp)
{
    size_t lo = 0;
    size_t hi = n_folds;
    assert(fold_cps != NULL || n_folds == 0u);
    assert(cp < SRMECH_TEXT_MAX_CP);
    for (size_t guard = 0; guard < 64u && lo < hi; guard++) {
        size_t mid = lo + ((hi - lo) >> 1);
        if (fold_cps[mid] < cp)      { lo = mid + 1u; }
        else if (fold_cps[mid] > cp) { hi = mid; }
        else                         { return mid; }
    }
    return SIZE_MAX;
}

/* Lexicographic bytes compare (memcmp semantics with length tiebreak —
 * shorter sorts first on a common prefix, matching Python bytes order). */
static int txt_bytes_cmp(const uint8_t *a, size_t alen,
                         const uint8_t *b, size_t blen)
{
    size_t m = (alen < blen) ? alen : blen;
    int    c;
    assert(a != NULL || alen == 0u);
    assert(b != NULL || blen == 0u);
    c = (m > 0u) ? memcmp(a, b, m) : 0;
    if (c != 0) { return c; }
    if (alen == blen) { return 0; }
    return (alen < blen) ? -1 : 1;
}

/* Is the token `tok[0..tok_len)` in the sorted stoplist (n_stop entries;
 * entry e = stop_bytes[stop_off[e] .. stop_off[e+1])), by binary search?
 * UTF-8 byte order == codepoint order, so bytewise compare == str compare. */
static int txt_stop_contains(const uint32_t *stop_off, size_t n_stop,
                             const uint8_t *stop_bytes,
                             const uint8_t *tok, size_t tok_len)
{
    size_t lo = 0;
    size_t hi = n_stop;
    assert(stop_off != NULL || n_stop == 0u);
    assert(tok != NULL || tok_len == 0u);
    for (size_t guard = 0; guard < 64u && lo < hi; guard++) {
        size_t mid = lo + ((hi - lo) >> 1);
        const uint8_t *e = &stop_bytes[stop_off[mid]];
        size_t elen = (size_t)(stop_off[mid + 1u] - stop_off[mid]);
        int c = txt_bytes_cmp(e, elen, tok, tok_len);
        if (c < 0)      { lo = mid + 1u; }
        else if (c > 0) { hi = mid; }
        else            { return 1; }
    }
    return 0;
}

/* Append `len` bytes to the staging output with capacity guard. */
static srmech_status_t txt_append(uint8_t *out, size_t out_cap, size_t *io_pos,
                                  const uint8_t *src, size_t len)
{
    assert(out != NULL && io_pos != NULL);
    assert(src != NULL || len == 0u);
    if (len > out_cap - *io_pos || *io_pos > out_cap) {
        return SRMECH_ERR_OVERFLOW;
    }
    if (len > 0u) { memcpy(&out[*io_pos], src, len); }
    *io_pos += len;
    return SRMECH_OK;
}

/* Finish the token staged at out[tok_start..*io_pos): trim trailing
 * apostrophes (Python's word.strip("'"); a LEADING apostrophe is
 * structurally impossible — the accumulate rule appends one only into a
 * non-empty run), then keep iff codepoint count >= 2 and not a stoplist
 * word: commit with a '\n' separator, else rewind to tok_start. */
static srmech_status_t txt_emit(uint8_t *out, size_t out_cap,
                                size_t tok_start, size_t *io_pos,
                                size_t n_cps, const uint32_t *stop_off,
                                size_t n_stop, const uint8_t *stop_bytes)
{
    size_t pos = *io_pos;
    assert(out != NULL && io_pos != NULL);
    assert(pos >= tok_start);
    for (; pos > tok_start && out[pos - 1u] == (uint8_t)'\''; pos--) {
        n_cps--;                       /* each trimmed apostrophe is one cp */
    }
    assert(pos == tok_start || out[tok_start] != (uint8_t)'\'');
    if (n_cps >= 2u &&
        !txt_stop_contains(stop_off, n_stop, stop_bytes,
                           &out[tok_start], pos - tok_start)) {
        static const uint8_t sep = (uint8_t)'\n';
        *io_pos = pos;
        return txt_append(out, out_cap, io_pos, &sep, 1u);
    }
    *io_pos = tok_start;               /* rejected — rewind the staging */
    return SRMECH_OK;
}

/* Append the casefold of one kept codepoint (table row `fold_idx`, or the
 * original `nb` input bytes at `src` when identity) and count its folded
 * codepoints into *io_cps (UTF-8 lead bytes = codepoints). */
static srmech_status_t txt_append_folded(uint8_t *out, size_t out_cap,
                                         size_t *io_pos, size_t *io_cps,
                                         const uint8_t *src, size_t nb,
                                         size_t fold_idx,
                                         const uint32_t *fold_off,
                                         const uint8_t *fold_bytes)
{
    assert(out != NULL && io_pos != NULL && io_cps != NULL);
    assert(src != NULL && nb >= 1u);
    if (fold_idx == SIZE_MAX) {        /* identity fold: copy the input span */
        *io_cps += 1u;
        return txt_append(out, out_cap, io_pos, src, nb);
    }
    {
        const uint8_t *f = &fold_bytes[fold_off[fold_idx]];
        size_t flen = (size_t)(fold_off[fold_idx + 1u] - fold_off[fold_idx]);
        for (size_t j = 0; j < flen; j++) {
            if ((f[j] & 0xC0u) != 0x80u) { *io_cps += 1u; }
        }
        return txt_append(out, out_cap, io_pos, f, flen);
    }
}

/* ------------------------------------------------------------------ *
 * srmech_text_tokenize — the §40/F698 Unicode content tokenizer
 * ------------------------------------------------------------------ */

/* Build the 128-entry ASCII fold fast-path LUT (fold-table row index, or
 * SIZE_MAX for identity) so the dominant ASCII case skips the per-codepoint
 * binary search over the ~1.5k-row exception table (the measured tokenize
 * hot spot — uppercase ASCII legitimately hits the table). */
static void txt_ascii_fold_lut(const uint32_t *fold_cps, size_t n_folds,
                               size_t lut[128])
{
    size_t r = 0;
    assert(lut != NULL);
    assert(fold_cps != NULL || n_folds == 0u);
    for (uint32_t cp = 0; cp < 128u; cp++) {
        for (; r < n_folds && fold_cps[r] < cp; r++) { }
        lut[cp] = (r < n_folds && fold_cps[r] == cp) ? r : SIZE_MAX;
    }
}

srmech_status_t srmech_text_tokenize(
    const uint8_t *text, size_t text_len, const uint8_t *kept_bits,
    const uint32_t *fold_cps, const uint32_t *fold_off,
    const uint8_t *fold_bytes, size_t n_folds,
    const uint32_t *stop_off, const uint8_t *stop_bytes, size_t n_stop,
    uint8_t *out, size_t out_cap, size_t *out_len)
{
    /* i = input cursor; pos = committed + staged output bytes; tok_start =
     * staging start of the active run; n_cps = codepoints staged post-fold */
    size_t i = 0, pos = 0, tok_start = 0, n_cps = 0;
    int    active = 0;
    size_t ascii_lut[128];
    assert(kept_bits != NULL && out != NULL && out_len != NULL);
    assert(text != NULL || text_len == 0u);
    if (kept_bits == NULL || out == NULL || out_len == NULL ||
        (text == NULL && text_len > 0u) ||
        (fold_cps == NULL && n_folds > 0u) ||
        (stop_off == NULL && n_stop > 0u)) {
        return SRMECH_ERR_NULL_ARG;
    }
    txt_ascii_fold_lut(fold_cps, n_folds, ascii_lut);
    while (i < text_len) {
        uint32_t cp;
        size_t   nb;
        size_t   ci = i;
        srmech_status_t st = SRMECH_OK;
        uint8_t  b0 = text[i];
        if (b0 < 0x80u) {              /* ASCII fast path (no fn call) */
            cp = b0; nb = 1u; i += 1u;
        } else if (!txt_utf8_next(text, text_len, &i, &cp, &nb)) {
            return SRMECH_ERR_BAD_INPUT;
        }
        if (txt_kept(kept_bits, cp)) {
            size_t fidx = (cp < 128u) ? ascii_lut[cp]
                                      : txt_fold_find(fold_cps, n_folds, cp);
            st = txt_append_folded(out, out_cap, &pos, &n_cps, &text[ci], nb,
                                   fidx, fold_off, fold_bytes);
            active = 1;
        } else if ((cp == 0x27u || cp == 0x2019u) && active) {
            static const uint8_t apos = (uint8_t)'\'';
            st = txt_append(out, out_cap, &pos, &apos, 1u);
            n_cps += 1u;
        } else if (active) {
            st = txt_emit(out, out_cap, tok_start, &pos, n_cps,
                          stop_off, n_stop, stop_bytes);
            active = 0;
            n_cps = 0;
            tok_start = pos;
        }
        if (st != SRMECH_OK) { return st; }
    }
    if (active) {
        srmech_status_t st = txt_emit(out, out_cap, tok_start, &pos, n_cps,
                                      stop_off, n_stop, stop_bytes);
        if (st != SRMECH_OK) { return st; }
    }
    *out_len = pos;
    return SRMECH_OK;
}

/* ------------------------------------------------------------------ *
 * Deterministic heapsorts (caller-arena, iterative, in-place)
 *
 * Two shapes: (a) contiguous records of `rec_words` uint64 words ordered
 * ascending-lexicographic over the first `key_words` words; (b) tandem
 * parallel (keys[], vals[]) arrays ordered by key. Every call site keys on
 * a UNIQUE tuple, so heapsort's non-stability is immaterial (total order →
 * one result on every platform). No libc qsort (implementation-defined tie
 * behaviour). The sift guard bound 64 exceeds log2 of any record count
 * (JPL Rule 2).
 * ------------------------------------------------------------------ */

static int txt_rec_less(const uint64_t *a, const uint64_t *b,
                        size_t key_words)
{
    assert(a != NULL && b != NULL);
    assert(key_words >= 1u && key_words <= 3u);
    for (size_t w = 0; w < key_words; w++) {
        if (a[w] < b[w]) { return 1; }
        if (a[w] > b[w]) { return 0; }
    }
    return 0;
}

static void txt_rec_swap(uint64_t *a, uint64_t *b, size_t rec_words)
{
    assert(a != NULL && b != NULL);
    assert(rec_words >= 1u && rec_words <= 3u);
    for (size_t w = 0; w < rec_words; w++) {
        uint64_t t = a[w];
        a[w] = b[w];
        b[w] = t;
    }
}

static void txt_sift_down(uint64_t *base, size_t n, size_t root,
                          size_t rec_words, size_t key_words)
{
    assert(base != NULL);
    assert(root < n);
    for (size_t guard = 0; guard < 64u; guard++) {
        size_t child = 2u * root + 1u;
        if (child >= n) { return; }
        if (child + 1u < n &&
            txt_rec_less(&base[child * rec_words],
                         &base[(child + 1u) * rec_words], key_words)) {
            child += 1u;
        }
        if (txt_rec_less(&base[root * rec_words],
                         &base[child * rec_words], key_words)) {
            txt_rec_swap(&base[root * rec_words], &base[child * rec_words],
                         rec_words);
            root = child;
        } else {
            return;
        }
    }
}

static void txt_heapsort(uint64_t *base, size_t n, size_t rec_words,
                         size_t key_words)
{
    assert(base != NULL || n == 0u);
    assert(rec_words >= key_words && key_words >= 1u);
    if (n < 2u) { return; }
    for (size_t i = n / 2u; i > 0u; i--) {
        txt_sift_down(base, n, i - 1u, rec_words, key_words);
    }
    for (size_t end = n - 1u; end > 0u; end--) {
        txt_rec_swap(&base[0], &base[end * rec_words], rec_words);
        txt_sift_down(base, end, 0u, rec_words, key_words);
    }
}

/* Tandem sift for the parallel (keys[], vals[]) shape — order by key only
 * (keys unique at every call site), values ride along. */
static void txt_sift_kv(uint64_t *keys, uint64_t *vals, size_t n, size_t root)
{
    assert(keys != NULL && vals != NULL);
    assert(root < n);
    for (size_t guard = 0; guard < 64u; guard++) {
        size_t child = 2u * root + 1u;
        uint64_t tk;
        uint64_t tv;
        if (child >= n) { return; }
        if (child + 1u < n && keys[child] < keys[child + 1u]) { child += 1u; }
        if (keys[root] >= keys[child]) { return; }
        tk = keys[root]; keys[root] = keys[child]; keys[child] = tk;
        tv = vals[root]; vals[root] = vals[child]; vals[child] = tv;
        root = child;
    }
}

static void txt_heapsort_kv(uint64_t *keys, uint64_t *vals, size_t n)
{
    assert(keys != NULL || n == 0u);
    assert(vals != NULL || n == 0u);
    if (n < 2u) { return; }
    for (size_t i = n / 2u; i > 0u; i--) {
        txt_sift_kv(keys, vals, n, i - 1u);
    }
    for (size_t end = n - 1u; end > 0u; end--) {
        uint64_t tk = keys[0];
        uint64_t tv = vals[0];
        keys[0] = keys[end]; keys[end] = tk;
        vals[0] = vals[end]; vals[end] = tv;
        txt_sift_kv(keys, vals, end, 0u);
    }
}

/* ------------------------------------------------------------------ *
 * Open-addressed pair-count hash (caller arena; key 0 = empty slot)
 *
 * Keys are ((uint64)u << 32) | v with u < v (unordered pair, canonical
 * orientation), so key 0 — the pair (0,0) — can never occur and marks an
 * empty slot. Capacity is a power of two; load is kept ≤ 1/2 (overflow →
 * SRMECH_ERR_OVERFLOW so the caller can grow the arena and retry — the
 * OVERFLOW-not-wrap discipline). splitmix64-mixed linear probing.
 * ------------------------------------------------------------------ */

static srmech_status_t txt_ht_add(uint64_t *keys, uint64_t *vals, size_t cap,
                                  uint64_t key, uint64_t add, size_t *io_occ)
{
    uint64_t h = key;
    size_t   idx;
    assert(keys != NULL && vals != NULL && io_occ != NULL);
    assert(key != 0u && cap >= 2u && (cap & (cap - 1u)) == 0u);
    h ^= h >> 30; h *= 0xBF58476D1CE4E5B9ULL;    /* splitmix64 finalizer */
    h ^= h >> 27; h *= 0x94D049BB133111EBULL;
    h ^= h >> 31;
    idx = (size_t)(h & (uint64_t)(cap - 1u));
    for (size_t probe = 0; probe < cap; probe++) {
        if (keys[idx] == key) {
            vals[idx] += add;
            return SRMECH_OK;
        }
        if (keys[idx] == 0u) {
            if ((*io_occ + 1u) * 2u > cap) { return SRMECH_ERR_OVERFLOW; }
            keys[idx] = key;
            vals[idx] = add;
            *io_occ += 1u;
            return SRMECH_OK;
        }
        idx = (idx + 1u) & (cap - 1u);
    }
    return SRMECH_ERR_INTERNAL;        /* unreachable at load ≤ 1/2 */
}

/* Accumulate the windowed pair counts of every document into the (zeroed
 * here) hash arena — the EXACT pure loop: within each document, for every
 * position a and every b in (a, min(a+window+1, m)), count one pair, skipping
 * ia == ib. When `directed` is 0 the pair is the UNORDERED
 * (min(ia,ib), max(ia,ib)) canonical key (u < v); when `directed` is nonzero
 * it is the ORDERED earlier→later key (ia << 32) | ib, so (i,j) and (j,i) are
 * distinct entries. The window NEVER crosses a document boundary (doc_off has
 * n_docs+1 entries; doc d spans tok_ids[doc_off[d] .. doc_off[d+1])). The key
 * 0 sentinel stays valid in BOTH modes: key == 0 requires ia == ib == 0, a
 * self-pair the loop skips. */
static srmech_status_t txt_pairs_accumulate(
    const uint32_t *tok_ids, size_t n_tok,
    const size_t *doc_off, size_t n_docs, uint32_t window, uint32_t n_vocab,
    uint64_t *ht_keys, uint64_t *ht_vals, size_t ht_cap, int directed,
    size_t *out_occ)
{
    size_t occ = 0;
    assert(doc_off != NULL && ht_keys != NULL && ht_vals != NULL);
    assert(out_occ != NULL && window >= 1u);
    if (doc_off[n_docs] != n_tok) { return SRMECH_ERR_BAD_INPUT; }
    memset(ht_keys, 0, ht_cap * sizeof(uint64_t));
    memset(ht_vals, 0, ht_cap * sizeof(uint64_t));
    for (size_t d = 0; d < n_docs; d++) {
        const uint32_t *toks = &tok_ids[doc_off[d]];
        size_t m;
        if (doc_off[d + 1u] < doc_off[d] || doc_off[d + 1u] > n_tok) {
            return SRMECH_ERR_BAD_INPUT;
        }
        m = doc_off[d + 1u] - doc_off[d];
        for (size_t a = 0; a < m; a++) {
            uint32_t ia = toks[a];
            size_t   hi = ((size_t)window < m - a - 1u)
                              ? a + (size_t)window + 1u : m;
            if (ia >= n_vocab) { return SRMECH_ERR_BAD_INPUT; }
            for (size_t b = a + 1u; b < hi; b++) {
                uint32_t ib = toks[b];
                uint64_t key;
                srmech_status_t st;
                if (ib >= n_vocab) { return SRMECH_ERR_BAD_INPUT; }
                if (ia == ib) { continue; }
                if (directed) {
                    key = ((uint64_t)ia << 32) | (uint64_t)ib;
                } else {
                    key = (ia < ib)
                              ? (((uint64_t)ia << 32) | (uint64_t)ib)
                              : (((uint64_t)ib << 32) | (uint64_t)ia);
                }
                st = txt_ht_add(ht_keys, ht_vals, ht_cap, key, 1u, &occ);
                if (st != SRMECH_OK) { return st; }
            }
        }
    }
    *out_occ = occ;
    return SRMECH_OK;
}

/* ------------------------------------------------------------------ *
 * srmech_text_cooccurrence_edges — the §40 Class-L precursor kernel
 * ------------------------------------------------------------------ */

srmech_status_t srmech_text_cooccurrence_edges(
    const uint32_t *tok_ids, size_t n_tok,
    const size_t *doc_off, size_t n_docs, uint32_t window, uint32_t n_vocab,
    uint64_t *ht_keys, uint64_t *ht_vals, size_t ht_cap, size_t *out_n_edges)
{
    size_t occ = 0;
    size_t w = 0;
    srmech_status_t st;
    assert(doc_off != NULL && out_n_edges != NULL);
    assert(ht_keys != NULL && ht_vals != NULL);
    if (doc_off == NULL || ht_keys == NULL || ht_vals == NULL ||
        out_n_edges == NULL || (tok_ids == NULL && n_tok > 0u)) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (window < 1u || ht_cap < 2u || (ht_cap & (ht_cap - 1u)) != 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    st = txt_pairs_accumulate(tok_ids, n_tok, doc_off, n_docs, window,
                              n_vocab, ht_keys, ht_vals, ht_cap, 0, &occ);
    if (st != SRMECH_OK) { return st; }
    for (size_t r = 0; r < ht_cap; r++) {      /* compact to the front */
        if (ht_keys[r] != 0u) {
            ht_keys[w] = ht_keys[r];
            ht_vals[w] = ht_vals[r];
            if (w < r) { ht_keys[r] = 0u; }    /* keep tail scannable */
            w += 1u;
        }
    }
    assert(w == occ);
    txt_heapsort_kv(ht_keys, ht_vals, w);      /* lexicographic (u, v) */
    *out_n_edges = w;
    return SRMECH_OK;
}

/* ------------------------------------------------------------------ *
 * srmech_text_cooccurrence_edges_directed — the DIRECTED (ordered pair)
 * variant (rc243; gh #1390 item 1). Same params + arena discipline as
 * srmech_text_cooccurrence_edges, but counts ORDERED earlier→later window
 * pairs: each co-occurrence with the earlier-position token id `i` and the
 * later-position token id `j` increments the ordered edge (i, j), so (i,j)
 * and (j,i) are DISTINCT entries. On success the *out_n_edges distinct
 * ordered pairs sit compacted + sorted at the FRONT of ht_keys
 * (key = (i<<32)|j — lexicographic (i, j) order) with parallel integer
 * counts in ht_vals. The metric-subset invariant holds: for every unordered
 * pair {a,b}, w[(a,b)] + w[(b,a)] equals the undirected count for {a,b}.
 * ADDITIVE symbol — SRMECH_ABI_VERSION stays 5. ------------------------ */

srmech_status_t srmech_text_cooccurrence_edges_directed(
    const uint32_t *tok_ids, size_t n_tok,
    const size_t *doc_off, size_t n_docs, uint32_t window, uint32_t n_vocab,
    uint64_t *ht_keys, uint64_t *ht_vals, size_t ht_cap, size_t *out_n_edges)
{
    size_t occ = 0;
    size_t w = 0;
    srmech_status_t st;
    assert(doc_off != NULL && out_n_edges != NULL);
    assert(ht_keys != NULL && ht_vals != NULL);
    if (doc_off == NULL || ht_keys == NULL || ht_vals == NULL ||
        out_n_edges == NULL || (tok_ids == NULL && n_tok > 0u)) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (window < 1u || ht_cap < 2u || (ht_cap & (ht_cap - 1u)) != 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    st = txt_pairs_accumulate(tok_ids, n_tok, doc_off, n_docs, window,
                              n_vocab, ht_keys, ht_vals, ht_cap, 1, &occ);
    if (st != SRMECH_OK) { return st; }
    for (size_t r = 0; r < ht_cap; r++) {      /* compact to the front */
        if (ht_keys[r] != 0u) {
            ht_keys[w] = ht_keys[r];
            ht_vals[w] = ht_vals[r];
            if (w < r) { ht_keys[r] = 0u; }    /* keep tail scannable */
            w += 1u;
        }
    }
    assert(w == occ);
    txt_heapsort_kv(ht_keys, ht_vals, w);      /* lexicographic (i, j) */
    *out_n_edges = w;
    return SRMECH_OK;
}

/* ------------------------------------------------------------------ *
 * srmech_text_cooccurrence_topk — the §52 bounded chunk-flush kernel
 * ------------------------------------------------------------------ */

/* Merge one node's chunk group into its bounded store row. The store row
 * (nbr ascending — the storage invariant; content-equal to the pure dict)
 * two-pointer-merges with the group (nbr ascending, weights summed on a
 * match) into scr as (nbr, w) records; if the merged count exceeds `cap`
 * the row truncates to the cap best by (-w, nbr) — the pure `_truncate_to`
 * selection — via the ~w ascending transform (Class-K reorder, no abs). */
static srmech_status_t txt_store_merge_node(
    uint32_t *store_nbr, uint64_t *store_w, uint32_t *store_len,
    uint32_t u, uint32_t cap, const uint64_t *grp, size_t grp_n,
    uint64_t *scr, size_t scr_cap_recs)
{
    size_t sl = (size_t)store_len[u];
    size_t si = 0, gi = 0, s = 0;
    const uint32_t *row_n = &store_nbr[(size_t)u * cap];
    const uint64_t *row_w = &store_w[(size_t)u * cap];
    assert(store_nbr != NULL && store_w != NULL && store_len != NULL);
    assert(grp != NULL && scr != NULL && sl <= cap);
    if (sl + grp_n > scr_cap_recs) { return SRMECH_ERR_OVERFLOW; }
    for (size_t guard = 0; guard < sl + grp_n; guard++) {
        uint32_t gn;
        if (si >= sl && gi >= grp_n) { break; }
        gn = (gi < grp_n) ? (uint32_t)(grp[2u * gi] & 0xFFFFFFFFu) : 0u;
        if (gi >= grp_n || (si < sl && row_n[si] < gn)) {
            scr[2u * s] = row_n[si]; scr[2u * s + 1u] = row_w[si]; si++;
        } else if (si >= sl || gn < row_n[si]) {
            scr[2u * s] = gn;        scr[2u * s + 1u] = grp[2u * gi + 1u]; gi++;
        } else {
            scr[2u * s] = gn;
            scr[2u * s + 1u] = row_w[si] + grp[2u * gi + 1u];
            si++; gi++;
        }
        s++;
    }
    if (s > cap) {                     /* rank by (-w, nbr): (~w, nbr) asc */
        for (size_t r = 0; r < s; r++) {
            uint64_t nbr = scr[2u * r];
            scr[2u * r] = ~scr[2u * r + 1u];
            scr[2u * r + 1u] = nbr;
        }
        txt_heapsort(scr, s, 2u, 2u);
        for (size_t r = 0; r < cap; r++) {   /* back to (nbr, w) records */
            uint64_t iw = scr[2u * r];
            scr[2u * r] = scr[2u * r + 1u];
            scr[2u * r + 1u] = ~iw;
        }
        txt_heapsort(scr, cap, 2u, 1u);      /* restore nbr-asc invariant */
        s = cap;
    }
    for (size_t r = 0; r < s; r++) {
        store_nbr[(size_t)u * cap + r] = (uint32_t)scr[2u * r];
        store_w[(size_t)u * cap + r]   = scr[2u * r + 1u];
    }
    store_len[u] = (uint32_t)s;
    return SRMECH_OK;
}

/* One §52 chunk flush, fully in C: accumulate the chunk's windowed pair
 * counts (the same per-document loop as cooccurrence_edges), expand to
 * DIRECTED (node → nbr) records, sort, and merge each touched node's group
 * into its bounded store row with cap-truncation — byte-identical to the
 * pure `_flush` (within-chunk weights sum in FULL before any truncation;
 * selection by (-w, nbr)).
 *
 * store_nbr/store_w are n_vocab × cap row-major rows (nbr ascending);
 * store_len[u] the live entries of row u. `dir` holds 2·occupied (key, w)
 * scratch records; `scr` one node's merge scratch. Arena too small →
 * SRMECH_ERR_OVERFLOW (grow + retry; the result is identical). */
srmech_status_t srmech_text_cooccurrence_topk(
    const uint32_t *tok_ids, size_t n_tok,
    const size_t *doc_off, size_t n_docs, uint32_t window, uint32_t cap,
    uint32_t n_vocab, uint32_t *store_nbr, uint64_t *store_w,
    uint32_t *store_len, uint64_t *ht_keys, uint64_t *ht_vals, size_t ht_cap,
    uint64_t *dir, size_t dir_cap_recs, uint64_t *scr, size_t scr_cap_recs)
{
    size_t occ = 0, nd = 0;
    srmech_status_t st;
    assert(doc_off != NULL && store_len != NULL && dir != NULL);
    assert(scr != NULL && cap >= 1u);
    if (doc_off == NULL || store_nbr == NULL || store_w == NULL ||
        store_len == NULL || ht_keys == NULL || ht_vals == NULL ||
        dir == NULL || scr == NULL || (tok_ids == NULL && n_tok > 0u)) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (window < 1u || cap < 1u || ht_cap < 2u ||
        (ht_cap & (ht_cap - 1u)) != 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    st = txt_pairs_accumulate(tok_ids, n_tok, doc_off, n_docs, window,
                              n_vocab, ht_keys, ht_vals, ht_cap, 0, &occ);
    if (st != SRMECH_OK) { return st; }
    if (2u * occ > dir_cap_recs) { return SRMECH_ERR_OVERFLOW; }
    for (size_t r = 0; r < ht_cap; r++) {
        if (ht_keys[r] != 0u) {
            uint64_t u = ht_keys[r] >> 32;
            uint64_t v = ht_keys[r] & 0xFFFFFFFFu;
            dir[2u * nd]      = (u << 32) | v;   /* node-major directed key */
            dir[2u * nd + 1u] = ht_vals[r];
            nd++;
            dir[2u * nd]      = (v << 32) | u;
            dir[2u * nd + 1u] = ht_vals[r];
            nd++;
        }
    }
    assert(nd == 2u * occ);
    txt_heapsort(dir, nd, 2u, 1u);
    for (size_t g0 = 0; g0 < nd; ) {           /* per-node group merge */
        uint32_t u = (uint32_t)(dir[2u * g0] >> 32);
        size_t   g1 = g0;
        for (; g1 < nd && (uint32_t)(dir[2u * g1] >> 32) == u; g1++) { }
        st = txt_store_merge_node(store_nbr, store_w, store_len, u, cap,
                                  &dir[2u * g0], g1 - g0, scr, scr_cap_recs);
        if (st != SRMECH_OK) { return st; }
        g0 = g1;
    }
    return SRMECH_OK;
}

/* ------------------------------------------------------------------ *
 * srmech_text_cooccurrence_topk_extract — the §52 final read-out
 * ------------------------------------------------------------------ */

/* Read the bounded store out exactly as the pure loop does: per node u
 * (ascending), rank its row by (-w, nbr) and keep the top k (the per-token
 * `topk` view, in ranked order); union those ranked entries into the sparse
 * edge list with the FIRST-SEEN weight (u ascending, rank order within u —
 * the pure `seen` set), sorted by (min, max) edge key.
 *
 * topk_nbr/topk_w are n_vocab × k row-major out rows (topk_len[u] live);
 * edge_recs is Σ min(store_len[u], k) 3-word (key, stamp, w) scratch
 * records, compacted in place to 2-word (key, w) records on return
 * (*out_n_edges of them). node_scr holds one node's ranking scratch. */
srmech_status_t srmech_text_cooccurrence_topk_extract(
    const uint32_t *store_nbr, const uint64_t *store_w,
    const uint32_t *store_len, uint32_t n_vocab, uint32_t cap, uint32_t k,
    uint32_t *topk_nbr, uint64_t *topk_w, uint32_t *topk_len,
    uint64_t *edge_recs, size_t edge_cap_recs, size_t *out_n_edges,
    uint64_t *node_scr, size_t node_scr_cap_recs)
{
    size_t ne = 0;                     /* staged 3-word edge records */
    size_t nw = 0;                     /* compacted 2-word edge records */
    uint64_t prev_key = 0;
    assert(store_len != NULL && topk_len != NULL && out_n_edges != NULL);
    assert(cap >= 1u && k >= 1u);
    if (store_nbr == NULL || store_w == NULL || store_len == NULL ||
        topk_nbr == NULL || topk_w == NULL || topk_len == NULL ||
        edge_recs == NULL || out_n_edges == NULL || node_scr == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    for (uint32_t u = 0; u < n_vocab; u++) {
        size_t sl = (size_t)store_len[u];
        size_t kn = (sl < (size_t)k) ? sl : (size_t)k;
        if (sl > (size_t)cap || sl > node_scr_cap_recs) {
            return SRMECH_ERR_BAD_INPUT;
        }
        topk_len[u] = (uint32_t)kn;
        if (sl == 0u) { continue; }
        for (size_t r = 0; r < sl; r++) {      /* rank row by (~w, nbr) */
            node_scr[2u * r]      = ~store_w[(size_t)u * cap + r];
            node_scr[2u * r + 1u] = (uint64_t)store_nbr[(size_t)u * cap + r];
        }
        txt_heapsort(node_scr, sl, 2u, 2u);
        for (size_t r = 0; r < kn; r++) {
            uint32_t v = (uint32_t)node_scr[2u * r + 1u];
            uint64_t wgt = ~node_scr[2u * r];
            uint64_t key = (u < v) ? (((uint64_t)u << 32) | (uint64_t)v)
                                   : (((uint64_t)v << 32) | (uint64_t)u);
            topk_nbr[(size_t)u * k + r] = v;
            topk_w[(size_t)u * k + r]   = wgt;
            if (ne >= edge_cap_recs) { return SRMECH_ERR_OVERFLOW; }
            edge_recs[3u * ne]      = key;
            edge_recs[3u * ne + 1u] = (uint64_t)ne;    /* first-seen stamp */
            edge_recs[3u * ne + 2u] = wgt;
            ne++;
        }
    }
    txt_heapsort(edge_recs, ne, 3u, 2u);       /* by (key, stamp) */
    for (size_t r = 0; r < ne; r++) {          /* keep FIRST stamp per key */
        uint64_t rkey = edge_recs[3u * r];
        uint64_t rw   = edge_recs[3u * r + 2u];
        if (r == 0u || rkey != prev_key) {
            edge_recs[2u * nw]      = rkey;
            edge_recs[2u * nw + 1u] = rw;
            nw++;
        }
        prev_key = rkey;
    }
    *out_n_edges = nw;
    return SRMECH_OK;
}
