/*
 * srmech_text.c — text → tokens → co-occurrence-edge ingestion C peers
 * (v0.9.0rc217; gh #1360).
 *
 * The C mirror of `srmech.amsc.text` — the §40/§52 text→graph leaves of the
 * RBS-LM K1 presence-kernel chain `text → glyph_stream → cooccurrence_edges →
 * dense_laplacian`. These three ops shipped rc50/§52 as pure-Python kernels
 * and were MIS-CLASSIFIED non_compute/composes_c in the Rosetta ledger (the
 * hiding-spot the rc217 ledger fix closes): the per-codepoint segmentation loop +
 * the windowed pair-count accumulation are THE dominant corpus-encode cost
 * (the full-enwiki comprehended-encode estimated ~6 days with the hot loop in
 * Python on a native wheel — no C symbol existed to dispatch to).
 *
 *   - srmech_text_glyph_stream        : UAX #29 grapheme-cluster segmentation
 *   - srmech_text_default_gb_table    : the vendored default break table
 *   - srmech_text_fold_marks          : combining-mark folding (rc293)
 *   - srmech_text_default_fold_table  : the vendored default fold table
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
 * applied to data), and that contract is UNCHANGED by rc287. What changed is
 * where the table comes from. The retired tokenizer built its tables from the
 * RUNNING interpreter's `unicodedata`, which made native == pure hold by
 * construction with nothing vendored. That is not available for UAX #29:
 * `unicodedata` exposes no grapheme-break property, no Extended_Pictographic
 * (GB11) and no InCB (GB9c), so the choice is vendored-vs-ABSENT, not
 * vendored-vs-derived. srmech therefore ships ONE attested default table
 * (srmech_unicode_gb_tables.h, UCD 16.0.0, re-derivable via
 * c/tools/gen_unicode_gb_tables.py --verify) that BOTH coherency projections
 * load, and byte-identity is pinned by test rather than by construction.
 *
 * A bare-C host with no Python present calls srmech_text_default_gb_table()
 * and hands the result straight to the segmenter; a host with its own table
 * passes that instead. The table is an input, never a hidden global.
 *
 * A side effect worth naming: because the table no longer tracks the host,
 * two hosts at different Python / Unicode versions now segment text
 * IDENTICALLY. Under the old derive-from-host scheme they would not have.
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
#include "srmech_unicode_gb_tables.h"
#include "srmech_unicode_fold_tables.h"

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

/* ------------------------------------------------------------------ *
 * srmech_text_glyph_stream — the UAX #29 extended-grapheme-cluster
 * segmenter (rc287)
 *
 * The glyph cluster replaces the word as the tokenizer's unit. A cluster
 * is what a human reads as ONE character, in EVERY script — so there is
 * no per-language word decision, no length floor, no casefold and no
 * stoplist at the front door (each of those was a property of the word
 * decision, and each encoded a Latin-shaped assumption).
 *
 * The break-property table is a CALLER-PROVIDED INPUT (ADR-0003), the
 * same discipline the retired tokenizer used for its Unicode tables. The
 * difference is where the table comes from: it can no longer be derived
 * from a host interpreter, because Extended_Pictographic (GB11) and InCB
 * (GB9c) are not exposed by any `unicodedata`. srmech therefore VENDORS
 * one attested default table (srmech_unicode_gb_tables.h) that both
 * coherency projections load, and a bare-C host with no Python present
 * reaches it through srmech_text_default_gb_table().
 *
 * Implemented as a single forward pass over a small state record — no
 * lookbehind buffer, no scratch arena, no file-scope state. GB9c and
 * GB11 both need lookbehind in their spec form; both are folded into
 * running flags instead, which is what keeps every function inside JPL
 * Rule 4 and the whole op reentrant.
 * ------------------------------------------------------------------ */

/* Running state for the GB rules that are specified with lookbehind.
 *   gb11 : 0 none · 1 saw `ExtPict Extend*` · 2 that, then ZWJ (GB11)
 *   incb_consonant / incb_linker : the `Consonant [Extend|Linker]*
 *       Linker` prefix GB9c requires
 *   ri_run : Regional_Indicator run length, for the GB12/GB13 parity */
typedef struct {
    uint8_t  prev;
    int      gb11;
    int      incb_consonant;
    int      incb_linker;
    uint32_t ri_run;
} txt_gb_state;

/* Packed property byte for `cp`: gbp in bits 0-3, Extended_Pictographic
 * in bit 4, InCB in bits 5-6. Hangul LV/LVT are recovered by the UAX #29
 * §3 syllable algebra rather than table rows (the precomposed block is
 * 798 ranges of pure alternation — 7,254 B of table saved, exactly).
 * NOTE the algebra covers ONLY U+AC00..U+D7A3; jamo L/V/T stay table
 * rows, because LBase/VBase/TBase are composition anchors that do not
 * coincide with the GBP jamo ranges (U+1160 is GBP=V yet below VBase). */
static uint8_t txt_gb_prop(const uint32_t *lo, const uint32_t *hi,
                           const uint8_t *prop, size_t n_ranges, uint32_t cp)
{
    size_t l = 0;
    size_t h = n_ranges;
    assert(lo != NULL && hi != NULL && prop != NULL);
    assert(cp < SRMECH_TEXT_MAX_CP);
    if (cp >= SRMECH_HANGUL_SBASE &&
        cp < SRMECH_HANGUL_SBASE + SRMECH_HANGUL_SCOUNT) {
        return (uint8_t)((((cp - SRMECH_HANGUL_SBASE) % SRMECH_HANGUL_TCOUNT)
                          == 0u) ? SRMECH_GBP_LV : SRMECH_GBP_LVT);
    }
    for (size_t guard = 0; guard < 64u && l < h; guard++) {
        size_t mid = l + ((h - l) >> 1);
        if (hi[mid] < cp)      { l = mid + 1u; }
        else if (lo[mid] > cp) { h = mid; }
        else                   { return prop[mid]; }
    }
    return (uint8_t)SRMECH_GBP_OTHER;      /* GB999 default */
}

/* The GB1..GB999 rule ladder: does a cluster boundary sit between the
 * codepoint whose property is `st->prev` and the one whose property is
 * `cur`? Rule order is significant and mirrors UAX #29 exactly. */
static int txt_gb_is_break(const txt_gb_state *st, uint8_t cur)
{
    uint8_t a = (uint8_t)(st->prev & SRMECH_GB_PROP_GBP_MASK);
    uint8_t b = (uint8_t)(cur & SRMECH_GB_PROP_GBP_MASK);
    int a_ctl = (a == SRMECH_GBP_CONTROL || a == SRMECH_GBP_CR ||
                 a == SRMECH_GBP_LF);
    int b_ctl = (b == SRMECH_GBP_CONTROL || b == SRMECH_GBP_CR ||
                 b == SRMECH_GBP_LF);
    assert(st != NULL);
    assert(st->gb11 >= 0 && st->gb11 <= 2);
    if (a == SRMECH_GBP_CR && b == SRMECH_GBP_LF) { return 0; }   /* GB3  */
    if (a_ctl || b_ctl)                           { return 1; }   /* GB4/5 */
    if (a == SRMECH_GBP_L && (b == SRMECH_GBP_L || b == SRMECH_GBP_V ||
                              b == SRMECH_GBP_LV || b == SRMECH_GBP_LVT)) {
        return 0;                                                 /* GB6  */
    }
    if ((a == SRMECH_GBP_LV || a == SRMECH_GBP_V) &&
        (b == SRMECH_GBP_V || b == SRMECH_GBP_T))  { return 0; }  /* GB7  */
    if ((a == SRMECH_GBP_LVT || a == SRMECH_GBP_T) &&
        b == SRMECH_GBP_T)                         { return 0; }  /* GB8  */
    if (b == SRMECH_GBP_EXTEND || b == SRMECH_GBP_ZWJ) { return 0; } /* GB9 */
    if (b == SRMECH_GBP_SPACINGMARK)               { return 0; }  /* GB9a */
    if (a == SRMECH_GBP_PREPEND)                   { return 0; }  /* GB9b */
    if (a == SRMECH_GBP_ZWJ && (cur & SRMECH_GB_PROP_EXTPICT_BIT) != 0u) {
        return (st->gb11 == 2) ? 0 : 1;                           /* GB11 */
    }
    if (a == SRMECH_GBP_REGIONAL_INDICATOR &&
        b == SRMECH_GBP_REGIONAL_INDICATOR) {
        return ((st->ri_run % 2u) == 0u) ? 1 : 0;                 /* GB12/13 */
    }
    if (((cur & SRMECH_GB_PROP_INCB_MASK) >> SRMECH_GB_PROP_INCB_SHIFT)
        == SRMECH_INCB_CONSONANT && st->incb_consonant && st->incb_linker) {
        return 0;                                                 /* GB9c */
    }
    return 1;                                                     /* GB999 */
}

/* Fold `cur` into the running state, given whether a boundary was just
 * placed before it. Must run AFTER txt_gb_is_break for that pair. */
static void txt_gb_advance(txt_gb_state *st, uint8_t cur, int was_break)
{
    uint8_t b = (uint8_t)(cur & SRMECH_GB_PROP_GBP_MASK);
    uint8_t incb = (uint8_t)((cur & SRMECH_GB_PROP_INCB_MASK)
                             >> SRMECH_GB_PROP_INCB_SHIFT);
    int is_ext = (cur & SRMECH_GB_PROP_EXTPICT_BIT) != 0u;
    assert(st != NULL);
    assert(was_break == 0 || was_break == 1);
    if (is_ext)                                     { st->gb11 = 1; }
    else if (st->gb11 == 1 && b == SRMECH_GBP_EXTEND) { /* stay armed */ }
    else if (st->gb11 == 1 && b == SRMECH_GBP_ZWJ)  { st->gb11 = 2; }
    else                                            { st->gb11 = 0; }
    if (incb == SRMECH_INCB_CONSONANT) {
        st->incb_consonant = 1;
        st->incb_linker = 0;
    } else if (incb == SRMECH_INCB_LINKER) {
        if (st->incb_consonant) { st->incb_linker = 1; }
    } else if (incb != SRMECH_INCB_EXTEND) {
        st->incb_consonant = 0;
        st->incb_linker = 0;
    }
    if (b == SRMECH_GBP_REGIONAL_INDICATOR) {
        st->ri_run = ((st->prev & SRMECH_GB_PROP_GBP_MASK)
                      == SRMECH_GBP_REGIONAL_INDICATOR && !was_break)
                     ? st->ri_run + 1u : 1u;
    } else {
        st->ri_run = 0u;
    }
    st->prev = cur;
}

/* The srmech-shipped DEFAULT break table (srmech_unicode_gb_tables.h).
 * This is what lets a bare-C host with no Python present segment the full
 * Unicode domain: hand these three pointers straight to
 * srmech_text_glyph_stream. A host with its own table passes that
 * instead — the table is an input, never a hidden global. */
void srmech_text_default_gb_table(const uint32_t **out_lo,
                                  const uint32_t **out_hi,
                                  const uint8_t **out_prop,
                                  size_t *out_n_ranges)
{
    assert(out_lo != NULL && out_hi != NULL);
    assert(out_prop != NULL && out_n_ranges != NULL);
    if (out_lo == NULL || out_hi == NULL ||
        out_prop == NULL || out_n_ranges == NULL) {
        return;
    }
    *out_lo       = SRMECH_GB_LO;
    *out_hi       = SRMECH_GB_HI;
    *out_prop     = SRMECH_GB_PROP;
    *out_n_ranges = (size_t)SRMECH_GB_RANGE_COUNT;
}

srmech_status_t srmech_text_glyph_stream(
    const uint8_t *text, size_t text_len,
    const uint32_t *lo, const uint32_t *hi, const uint8_t *prop,
    size_t n_ranges, uint32_t *out_off, size_t out_cap, size_t *out_n)
{
    txt_gb_state st;
    size_t i = 0;
    size_t n = 0;
    assert(out_off != NULL || out_cap == 0u);
    assert(out_n != NULL);
    if (out_n == NULL || lo == NULL || hi == NULL || prop == NULL ||
        (text == NULL && text_len > 0u) || (out_off == NULL && out_cap > 0u)) {
        return SRMECH_ERR_NULL_ARG;
    }
    st.prev = 0u;
    st.gb11 = 0;
    st.incb_consonant = 0;
    st.incb_linker = 0;
    st.ri_run = 0u;
    while (i < text_len) {
        uint32_t cp;
        size_t   nb;
        size_t   start = i;
        uint8_t  cur;
        int      brk;
        if (!txt_utf8_next(text, text_len, &i, &cp, &nb)) {
            return SRMECH_ERR_BAD_INPUT;
        }
        cur = txt_gb_prop(lo, hi, prop, n_ranges, cp);
        brk = (start == 0u) ? 1 : txt_gb_is_break(&st, cur);
        if (brk) {
            if (n >= out_cap) { return SRMECH_ERR_OVERFLOW; }
            out_off[n] = (uint32_t)start;
            n++;
        }
        /* Seeds correctly at start too: `prev` is Other, so a leading
         * Regional_Indicator sets ri_run = 1 and anything else 0. */
        txt_gb_advance(&st, cur, brk);
    }
    if (n >= out_cap) { return SRMECH_ERR_OVERFLOW; }
    out_off[n] = (uint32_t)text_len;        /* sentinel: cluster i spans
                                             * [out_off[i], out_off[i+1]) */
    *out_n = n;
    return SRMECH_OK;
}

/* ------------------------------------------------------------------ *
 * srmech_text_fold_marks — combining-mark folding (rc293)
 *
 * Drops combining marks by Unicode General_Category (Mn / Mc / Me). The
 * name is the contract: a VIRAMA is a mark, not an accent, so calling
 * this "fold_accents" would have been wrong in exactly the Indic cases
 * that matter most while quietly re-scoping the op toward Latin.
 *
 * Category ONLY — no case change, no locale tailoring, no NFKD
 * compatibility folding, no ligature expansion. So U+00F8 `ø` is
 * unchanged (a stroke is part of the letter, not a mark) and Hangul is
 * unchanged in either normalization form (it decomposes to jamo, which
 * are starters).
 *
 * Two facts merge into ONE table row, so one binary search serves both:
 * rep == SRMECH_FOLD_DROP means the codepoint IS a mark and is deleted;
 * any other value is the codepoint it is REPLACED by. Replacements are
 * transitively resolved AT GENERATION TIME (U+1EBF -> U+0065 directly,
 * not via U+00EA), which is what keeps this loop flat: no recursion, no
 * decomposition buffer, and one pass is provably enough because the
 * generator asserts the table is CLOSED (no replacement is itself a row).
 *
 * The op calls no normalizer and needs none: precomposed characters are
 * handled by the map rows and decomposed sequences by the drop rows, so
 * the SAME marks fall out whichever form the caller supplies. That is
 * what lets a bare-C host with no Python fold correctly — there is no
 * `unicodedata` to ask, which is why the table is vendored at all.
 *
 * Folding never GROWS the UTF-8 byte length (asserted by the generator),
 * so out_cap >= text_len always suffices.
 * ------------------------------------------------------------------ */

/* Look `cp` up in the caller-provided fold table. Returns 1 when a row
 * covers `cp` (*out_rep set: SRMECH_FOLD_DROP to delete, else the
 * replacement codepoint), 0 when none does — the codepoint passes
 * through unchanged. Mirrors txt_gb_prop's guarded binary search; the
 * guard bound 64 exceeds log2 of any table size (JPL Rule 2). */
static int txt_fold_lookup(const uint32_t *lo, const uint32_t *hi,
                           const uint32_t *rep, size_t n_ranges,
                           uint32_t cp, uint32_t *out_rep)
{
    size_t l = 0;
    size_t h = n_ranges;
    assert(lo != NULL && hi != NULL && rep != NULL);
    assert(out_rep != NULL && cp < SRMECH_TEXT_MAX_CP);
    for (size_t guard = 0; guard < 64u && l < h; guard++) {
        size_t mid = l + ((h - l) >> 1);
        if (hi[mid] < cp)      { l = mid + 1u; }
        else if (lo[mid] > cp) { h = mid; }
        else                   { *out_rep = rep[mid]; return 1; }
    }
    return 0;
}

/* Encode `cp` as UTF-8 at out[*io_n], advancing *io_n. Returns 1 on
 * success, 0 when the caller arena is too small. Only reached for
 * REPLACEMENT codepoints (table data, attested in range); pass-through
 * codepoints are byte-copied instead. */
static int txt_utf8_encode(uint8_t *out, size_t out_cap, size_t *io_n,
                           uint32_t cp)
{
    size_t n;
    assert(io_n != NULL && cp < SRMECH_TEXT_MAX_CP);
    assert(out != NULL || out_cap == 0u);
    n = *io_n;
    if (cp < 0x80u) {
        if (n + 1u > out_cap) { return 0; }
        out[n] = (uint8_t)cp;
        *io_n = n + 1u;
    } else if (cp < 0x800u) {
        if (n + 2u > out_cap) { return 0; }
        out[n]      = (uint8_t)(0xC0u | (cp >> 6));
        out[n + 1u] = (uint8_t)(0x80u | (cp & 0x3Fu));
        *io_n = n + 2u;
    } else if (cp < 0x10000u) {
        if (n + 3u > out_cap) { return 0; }
        out[n]      = (uint8_t)(0xE0u | (cp >> 12));
        out[n + 1u] = (uint8_t)(0x80u | ((cp >> 6) & 0x3Fu));
        out[n + 2u] = (uint8_t)(0x80u | (cp & 0x3Fu));
        *io_n = n + 3u;
    } else {
        if (n + 4u > out_cap) { return 0; }
        out[n]      = (uint8_t)(0xF0u | (cp >> 18));
        out[n + 1u] = (uint8_t)(0x80u | ((cp >> 12) & 0x3Fu));
        out[n + 2u] = (uint8_t)(0x80u | ((cp >> 6) & 0x3Fu));
        out[n + 3u] = (uint8_t)(0x80u | (cp & 0x3Fu));
        *io_n = n + 4u;
    }
    return 1;
}

/* The srmech-shipped DEFAULT fold table (srmech_unicode_fold_tables.h).
 * This is what lets a bare-C host with no Python present fold combining
 * marks over the full Unicode domain: hand these three pointers straight
 * to srmech_text_fold_marks. A host with its own table passes that
 * instead — the table is an input, never a hidden global. */
void srmech_text_default_fold_table(const uint32_t **out_lo,
                                    const uint32_t **out_hi,
                                    const uint32_t **out_rep,
                                    size_t *out_n_ranges)
{
    assert(out_lo != NULL && out_hi != NULL);
    assert(out_rep != NULL && out_n_ranges != NULL);
    if (out_lo == NULL || out_hi == NULL ||
        out_rep == NULL || out_n_ranges == NULL) {
        return;
    }
    *out_lo       = SRMECH_FOLD_LO;
    *out_hi       = SRMECH_FOLD_HI;
    *out_rep      = SRMECH_FOLD_REP;
    *out_n_ranges = (size_t)SRMECH_FOLD_RANGE_COUNT;
}

srmech_status_t srmech_text_fold_marks(
    const uint8_t *text, size_t text_len,
    const uint32_t *lo, const uint32_t *hi, const uint32_t *rep,
    size_t n_ranges, uint8_t *out, size_t out_cap, size_t *out_len)
{
    size_t i = 0;
    size_t n = 0;
    assert(out != NULL || out_cap == 0u);
    assert(out_len != NULL);
    if (out_len == NULL || lo == NULL || hi == NULL || rep == NULL ||
        (text == NULL && text_len > 0u) || (out == NULL && out_cap > 0u)) {
        return SRMECH_ERR_NULL_ARG;
    }
    while (i < text_len) {
        uint32_t cp;
        uint32_t folded = 0u;
        size_t   nb;
        if (!txt_utf8_next(text, text_len, &i, &cp, &nb)) {
            return SRMECH_ERR_BAD_INPUT;
        }
        if (txt_fold_lookup(lo, hi, rep, n_ranges, cp, &folded)) {
            if (folded == SRMECH_FOLD_DROP) { continue; }   /* combining mark */
            if (!txt_utf8_encode(out, out_cap, &n, folded)) {
                return SRMECH_ERR_OVERFLOW;
            }
            continue;
        }
        /* Unchanged: copy the ORIGINAL bytes rather than re-encoding, so a
         * pass-through codepoint is byte-preserved by construction. */
        if (n > out_cap || nb > out_cap - n) { return SRMECH_ERR_OVERFLOW; }
        memcpy(out + n, text + i - nb, nb);
        n += nb;
    }
    *out_len = n;
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

/* Accumulate the windowed unordered pair counts of every document into the
 * (zeroed here) hash arena — the EXACT pure loop: within each document, for
 * every position a and every b in (a, min(a+window+1, m)), count the pair
 * (min(ia,ib), max(ia,ib)) once, skipping ia == ib. The window NEVER crosses
 * a document boundary (doc_off has n_docs+1 entries; doc d spans
 * tok_ids[doc_off[d] .. doc_off[d+1])). */
static srmech_status_t txt_pairs_accumulate(
    const uint32_t *tok_ids, size_t n_tok,
    const size_t *doc_off, size_t n_docs, uint32_t window, uint32_t n_vocab,
    uint64_t *ht_keys, uint64_t *ht_vals, size_t ht_cap, size_t *out_occ)
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
                key = (ia < ib)
                          ? (((uint64_t)ia << 32) | (uint64_t)ib)
                          : (((uint64_t)ib << 32) | (uint64_t)ia);
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
                              n_vocab, ht_keys, ht_vals, ht_cap, &occ);
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
 * srmech_text_cooccurrence_edges_directed — the directed (metric +
 * charge) SUPERSET of srmech_text_cooccurrence_edges (#1390 item 1).
 *
 * On the SAME canonical unordered key (min,max) it accumulates two
 * columns in one pass: metric (+1 per co-occurrence == the undirected
 * weight) and charge (+1 when the EARLIER-position token has the smaller
 * id — forward on (lo,hi) — else -1). So charge = w_fwd - w_bwd, the
 * direction the unordered fold discards; metric == the directed=False
 * weight exactly. No second fold. ADDITIVE symbol — ABI stays 5.
 * ------------------------------------------------------------------ */

/* sift/heapsort over three parallel arrays (key asc; metric + signed
 * charge ride along the key swaps). */
static void txt_sift_kvc(uint64_t *keys, uint64_t *met, int64_t *chg,
                         size_t n, size_t root)
{
    assert(keys != NULL && met != NULL && chg != NULL);
    assert(root < n);
    for (size_t guard = 0; guard < 64u; guard++) {
        size_t child = 2u * root + 1u;
        uint64_t tk, tv;
        int64_t tc;
        if (child >= n) { return; }
        if (child + 1u < n && keys[child] < keys[child + 1u]) { child += 1u; }
        if (keys[root] >= keys[child]) { return; }
        tk = keys[root]; keys[root] = keys[child]; keys[child] = tk;
        tv = met[root];  met[root]  = met[child];  met[child]  = tv;
        tc = chg[root];  chg[root]  = chg[child];  chg[child]  = tc;
        root = child;
    }
}

static void txt_heapsort_kvc(uint64_t *keys, uint64_t *met, int64_t *chg,
                             size_t n)
{
    assert(keys != NULL || n == 0u);
    assert(met != NULL || n == 0u);
    if (n < 2u) { return; }
    for (size_t i = n / 2u; i > 0u; i--) {
        txt_sift_kvc(keys, met, chg, n, i - 1u);
    }
    for (size_t end = n - 1u; end > 0u; end--) {
        uint64_t tk = keys[0], tv = met[0];
        int64_t tc = chg[0];
        keys[0] = keys[end]; keys[end] = tk;
        met[0]  = met[end];  met[end]  = tv;
        chg[0]  = chg[end];  chg[end]  = tc;
        txt_sift_kvc(keys, met, chg, end, 0u);
    }
}

/* canonical-key hash add with two columns (metric +1, charge += sign). */
static srmech_status_t txt_ht_add_directed(
    uint64_t *keys, uint64_t *met, int64_t *chg, size_t cap,
    uint64_t key, int sign, size_t *io_occ)
{
    uint64_t h = key;
    size_t idx;
    assert(keys != NULL && met != NULL && chg != NULL && io_occ != NULL);
    assert(key != 0u && cap >= 2u && (cap & (cap - 1u)) == 0u);
    h ^= h >> 30; h *= 0xBF58476D1CE4E5B9ULL;
    h ^= h >> 27; h *= 0x94D049BB133111EBULL;
    h ^= h >> 31;
    idx = (size_t)(h & (uint64_t)(cap - 1u));
    for (size_t probe = 0; probe < cap; probe++) {
        if (keys[idx] == key) {
            met[idx] += 1u;
            chg[idx] += sign;
            return SRMECH_OK;
        }
        if (keys[idx] == 0u) {
            if ((*io_occ + 1u) * 2u > cap) { return SRMECH_ERR_OVERFLOW; }
            keys[idx] = key;
            met[idx] = 1u;
            chg[idx] = sign;
            *io_occ += 1u;
            return SRMECH_OK;
        }
        idx = (idx + 1u) & (cap - 1u);
    }
    return SRMECH_ERR_INTERNAL;
}

static srmech_status_t txt_pairs_accumulate_directed(
    const uint32_t *tok_ids, size_t n_tok,
    const size_t *doc_off, size_t n_docs, uint32_t window, uint32_t n_vocab,
    uint64_t *keys, uint64_t *met, int64_t *chg, size_t cap, size_t *out_occ)
{
    size_t occ = 0;
    assert(doc_off != NULL && keys != NULL && met != NULL);
    assert(chg != NULL && out_occ != NULL && window >= 1u);
    if (doc_off[n_docs] != n_tok) { return SRMECH_ERR_BAD_INPUT; }
    memset(keys, 0, cap * sizeof(uint64_t));
    memset(met, 0, cap * sizeof(uint64_t));
    memset(chg, 0, cap * sizeof(int64_t));
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
                key = (ia < ib) ? (((uint64_t)ia << 32) | (uint64_t)ib)
                                : (((uint64_t)ib << 32) | (uint64_t)ia);
                st = txt_ht_add_directed(keys, met, chg, cap, key,
                                         (ia < ib) ? 1 : -1, &occ);
                if (st != SRMECH_OK) { return st; }
            }
        }
    }
    *out_occ = occ;
    return SRMECH_OK;
}

srmech_status_t srmech_text_cooccurrence_edges_directed(
    const uint32_t *tok_ids, size_t n_tok,
    const size_t *doc_off, size_t n_docs, uint32_t window, uint32_t n_vocab,
    uint64_t *ht_keys, uint64_t *ht_metric, int64_t *ht_charge, size_t ht_cap,
    size_t *out_n_edges)
{
    size_t occ = 0;
    size_t w = 0;
    srmech_status_t st;
    assert(doc_off != NULL && out_n_edges != NULL);
    assert(ht_keys != NULL && ht_metric != NULL && ht_charge != NULL);
    if (doc_off == NULL || ht_keys == NULL || ht_metric == NULL ||
        ht_charge == NULL || out_n_edges == NULL ||
        (tok_ids == NULL && n_tok > 0u)) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (window < 1u || ht_cap < 2u || (ht_cap & (ht_cap - 1u)) != 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    st = txt_pairs_accumulate_directed(tok_ids, n_tok, doc_off, n_docs, window,
                                       n_vocab, ht_keys, ht_metric, ht_charge,
                                       ht_cap, &occ);
    if (st != SRMECH_OK) { return st; }
    for (size_t r = 0; r < ht_cap; r++) {      /* compact 3 columns */
        if (ht_keys[r] != 0u) {
            ht_keys[w] = ht_keys[r];
            ht_metric[w] = ht_metric[r];
            ht_charge[w] = ht_charge[r];
            if (w < r) { ht_keys[r] = 0u; }
            w += 1u;
        }
    }
    assert(w == occ);
    txt_heapsort_kvc(ht_keys, ht_metric, ht_charge, w);
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
                              n_vocab, ht_keys, ht_vals, ht_cap, &occ);
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
