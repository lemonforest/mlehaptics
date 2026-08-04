/*
 * srmech_toml.c — malloc-free TOML parser (caller arena).
 *
 * A self-contained reader for the TOML subset srmech's descriptor /
 * cascade-catalog files actually use (see srmech.h for the exact
 * grammar). NOT a full TOML 1.0 parser — every unsupported construct is
 * rejected with SRMECH_ERR_BAD_INPUT so a silent mis-parse can never
 * slip through. No datetimes (they do not appear in the corpus). No
 * vendored code; pure C11 + stdlib (string.h for memcpy/strcmp/strncmp).
 *
 * Memory model
 * ------------
 * The whole parse runs against the caller-supplied arena `ws` used as an
 * 8-byte-aligned bump allocator (toml_arena). There are TWO node shapes:
 *
 *   1. A MUTABLE builder tree (toml_btable / toml_bvalue) grows during
 *      parsing. Builder tables hold their children as an arena-allocated
 *      singly-linked list so a table can be REOPENED ([a] then [a.b]
 *      then [a] again) and grown without realloc — each new key bumps one
 *      list node out of the arena. An array-of-tables ([[a]]) is a builder
 *      value whose own chained list of builder tables grows one element
 *      per [[a]] header. NOTHING is fixed-cap final storage; the caps are
 *      validity bounds only (JPL Rule 2).
 *
 *   2. At end of document toml_finalize_*() recurse the builder tree once
 *      and emit the right-sized, contiguous srmech_toml_value_t tree the
 *      public API returns (keys[]/vals[]/items[] are arena arrays sized
 *      exactly to the child count). This is the "collect, then copy
 *      right-sized" discipline the task spec calls for.
 *
 * Per-table / per-array element count is NOT capped (rc159 standalone-complete
 * honor): children are collected into arena linked lists (no fixed staging
 * arrays), so the only bound is the caller arena — a C-only / MCU host can
 * parse a descriptor with any number of entries its RAM fits. Nesting depth is
 * still bounded by SRMECH_TOML_MAX_DEPTH (a recursion-depth guard, not a
 * problem-size cap) -> SRMECH_ERR_OVERFLOW.
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto)        : OK
 *   - Rule 2 (bounded loops)  : OK — every scan bounded by `len` (an element
 *                              consumes >= 1 byte, so child count <= len),
 *                              every recursion by SRMECH_TOML_MAX_DEPTH
 *   - Rule 3 (no malloc)      : OK — caller arena only
 *   - Rule 4 (<=60 lines/func): OK — split into static helpers
 *   - Rule 5 (>=2 asserts/fn) : OK
 *   - Rule 7 (return-value)   : OK — srmech_status_t throughout
 *   - Rule 8 (no multi-line macros) : OK
 *   - Rule 10 (warnings clean): OK under -Wall -Wextra -Wpedantic -Werror
 *
 * License: MIT.
 */

#include "srmech.h"

#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

/* Arena alignment (every allocation is rounded up so the returned
 * pointer suits any srmech_toml_value_t member). */
#define SRMECH_TOML_ALIGN 8u

/* ================================================================== *
 * Arena (bump allocator over the caller's workspace).
 * ================================================================== */

typedef struct toml_arena {
    uint8_t *base;
    size_t   len;
    size_t   used;
} toml_arena_t;

/* Round `n` up to the next SRMECH_TOML_ALIGN multiple; saturates to
 * SIZE_MAX (the caller's capacity check then fails cleanly). */
static size_t toml_align_up(size_t n)
{
    assert(SRMECH_TOML_ALIGN >= 1u);
    assert((SRMECH_TOML_ALIGN & (SRMECH_TOML_ALIGN - 1u)) == 0u);
    size_t mask = (size_t)(SRMECH_TOML_ALIGN - 1u);
    if (n > SIZE_MAX - mask) {
        return SIZE_MAX;
    }
    return (n + mask) & ~mask;
}

/* Bump `nbytes` (aligned) out of the arena, zeroing the block. On
 * success writes the block pointer to *out; on exhaustion -> OVERFLOW. */
static srmech_status_t toml_arena_alloc(toml_arena_t *a, size_t nbytes,
                                        void **out)
{
    assert(a != NULL);
    assert(out != NULL);
    *out = NULL;
    size_t want = (nbytes == 0u) ? SRMECH_TOML_ALIGN : toml_align_up(nbytes);
    if (want == SIZE_MAX || want > a->len - a->used) {
        return SRMECH_ERR_OVERFLOW;
    }
    uint8_t *p = a->base + a->used;
    a->used += want;
    for (size_t k = 0; k < nbytes; k++) {
        p[k] = 0u;
    }
    *out = p;
    return SRMECH_OK;
}

/* ================================================================== *
 * Mutable builder tree.
 *
 * A builder value is one of:
 *   - KIND_LEAF  : a finalised scalar or array-of-scalars (held inline
 *                  as a srmech_toml_value_t in `leaf`);
 *   - KIND_TABLE : a table still being populated (`table`);
 *   - KIND_ATABLE: an array-of-tables, a chained list of builder tables
 *                  (`atable_head`/`atable_tail`/`atable_n`).
 * ================================================================== */

#define TOML_KIND_LEAF   0
#define TOML_KIND_TABLE  1
#define TOML_KIND_ATABLE 2

struct toml_btable;

typedef struct toml_atable_node {
    struct toml_btable      *table;
    struct toml_atable_node *next;
} toml_atable_node_t;

typedef struct toml_bvalue {
    int                  kind;
    struct toml_btable  *table;        /* KIND_TABLE */
    srmech_toml_value_t  leaf;         /* KIND_LEAF  */
    toml_atable_node_t  *atable_head;  /* KIND_ATABLE */
    toml_atable_node_t  *atable_tail;
    uint32_t             atable_n;
} toml_bvalue_t;

typedef struct toml_bentry {
    const char         *key;           /* NUL-terminated, arena-owned */
    toml_bvalue_t      *val;
    struct toml_bentry *next;
} toml_bentry_t;

typedef struct toml_btable {
    toml_bentry_t *head;
    toml_bentry_t *tail;
    uint32_t       count;
    bool           is_inline;          /* inline {..}: cannot be reopened */
} toml_btable_t;

/* Arena linked-list node for collecting `[ ... ]` array elements before the
 * "copy right-sized" emit (mirrors the builder-table entry list). No fixed
 * staging array, so the element count is bounded only by the caller arena —
 * not a compiled-in 256-entry cap (rc159 standalone-complete). */
typedef struct toml_alist_node {
    srmech_toml_value_t    *val;
    struct toml_alist_node *next;
} toml_alist_node_t;

/* ================================================================== *
 * Parser cursor.
 * ================================================================== */

typedef struct toml_parser {
    const char  *s;
    size_t       n;
    size_t       i;
    toml_arena_t arena;
} toml_parser_t;

/* ------------------------------------------------------------------ *
 * Forward declarations (mutually-recursive parse + finalise).
 * ------------------------------------------------------------------ */
static srmech_status_t toml_parse_value(toml_parser_t *p,
                                        srmech_toml_value_t *out, int depth);
static srmech_status_t toml_finalize_btable(toml_parser_t *p,
                                            const toml_btable_t *t,
                                            srmech_toml_value_t *out, int depth);
static srmech_status_t toml_finalize_bvalue(toml_parser_t *p,
                                            const toml_bvalue_t *bv,
                                            srmech_toml_value_t **out,
                                            int depth);
static srmech_status_t toml_atable_link(toml_parser_t *p, toml_bvalue_t *bv,
                                        toml_btable_t **out);

/* ================================================================== *
 * Builder allocation helpers.
 * ================================================================== */

/* Allocate + init an empty builder table. */
static srmech_status_t toml_btable_new(toml_parser_t *p, bool is_inline,
                                       toml_btable_t **out)
{
    assert(p != NULL);
    assert(out != NULL);
    void *mem = NULL;
    srmech_status_t st = toml_arena_alloc(&p->arena, sizeof(toml_btable_t),
                                          &mem);
    if (st != SRMECH_OK) {
        return st;
    }
    toml_btable_t *t = (toml_btable_t *)mem;
    t->head = NULL;
    t->tail = NULL;
    t->count = 0u;
    t->is_inline = is_inline;
    *out = t;
    return SRMECH_OK;
}

/* Allocate a zeroed builder value of the given kind. */
static srmech_status_t toml_bvalue_new(toml_parser_t *p, int kind,
                                       toml_bvalue_t **out)
{
    assert(p != NULL);
    assert(out != NULL);
    void *mem = NULL;
    srmech_status_t st = toml_arena_alloc(&p->arena, sizeof(toml_bvalue_t),
                                          &mem);
    if (st != SRMECH_OK) {
        return st;
    }
    toml_bvalue_t *v = (toml_bvalue_t *)mem;
    v->kind = kind;
    v->table = NULL;
    v->atable_head = NULL;
    v->atable_tail = NULL;
    v->atable_n = 0u;
    *out = v;
    return SRMECH_OK;
}

/* Find an existing entry by key in a builder table, or NULL. */
static toml_bentry_t *toml_btable_find(const toml_btable_t *t, const char *key)
{
    assert(t != NULL);
    assert(key != NULL);
    toml_bentry_t *e = t->head;
    /* The list holds exactly t->count entries (append increments both in
     * lockstep), so bound the walk by t->count — a runtime bound (JPL Rule 2),
     * not a compiled-in 256-entry cap. */
    for (uint32_t guard = 0; guard <= t->count; guard++) {
        if (e == NULL) {
            return NULL;
        }
        if (strcmp(e->key, key) == 0) {
            return e;
        }
        e = e->next;
    }
    return NULL;
}

/* Append a new (key,val) entry to a builder table. Key MUST be absent
 * (caller checks). No entry-count cap: the entry is arena-allocated and linked,
 * so the table size is bounded only by the caller arena (rc159 honor). */
static srmech_status_t toml_btable_append(toml_parser_t *p, toml_btable_t *t,
                                          const char *key, toml_bvalue_t *val)
{
    assert(t != NULL);
    assert(key != NULL && val != NULL);
    void *mem = NULL;
    srmech_status_t st = toml_arena_alloc(&p->arena, sizeof(toml_bentry_t),
                                          &mem);
    if (st != SRMECH_OK) {
        return st;
    }
    toml_bentry_t *e = (toml_bentry_t *)mem;
    e->key = key;
    e->val = val;
    e->next = NULL;
    if (t->tail == NULL) {
        t->head = e;
    } else {
        t->tail->next = e;
    }
    t->tail = e;
    t->count++;
    return SRMECH_OK;
}

/* ================================================================== *
 * Character classes + lexer skips.
 * ================================================================== */

static bool toml_is_ws(char c)
{
    return c == ' ' || c == '\t';
}

static bool toml_is_bare_key_char(char c)
{
    bool alpha = (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z');
    bool digit = (c >= '0' && c <= '9');
    return alpha || digit || c == '_' || c == '-';
}

/* Skip spaces/tabs (NOT newlines) and any '#' comment to end of line. */
static void toml_skip_ws_inline(toml_parser_t *p)
{
    assert(p != NULL);
    assert(p->i <= p->n);
    while (p->i < p->n) {
        char c = p->s[p->i];
        if (toml_is_ws(c)) {
            p->i++;
        } else if (c == '#') {
            while (p->i < p->n && p->s[p->i] != '\n') {
                p->i++;
            }
        } else {
            break;
        }
    }
}

/* Skip spaces/tabs, comments AND newlines (inside arrays/inline tables
 * and between top-level statements). */
static void toml_skip_ws_nl(toml_parser_t *p)
{
    assert(p != NULL);
    assert(p->i <= p->n);
    while (p->i < p->n) {
        char c = p->s[p->i];
        if (toml_is_ws(c) || c == '\n' || c == '\r') {
            p->i++;
        } else if (c == '#') {
            while (p->i < p->n && p->s[p->i] != '\n') {
                p->i++;
            }
        } else {
            break;
        }
    }
}

/* ================================================================== *
 * String parsing.
 * ================================================================== */

/* Encode codepoint cp as UTF-8 into buf[*pos..]; advances *pos. Rejects
 * surrogates, out-of-range, and insufficient room. */
static srmech_status_t toml_utf8_encode(uint32_t cp, char *buf, size_t cap,
                                        size_t *pos)
{
    assert(buf != NULL);
    assert(pos != NULL);
    size_t need = (cp < 0x80u) ? 1u : (cp < 0x800u) ? 2u
                : (cp < 0x10000u) ? 3u : 4u;
    if (cp > 0x10FFFFu || (cp >= 0xD800u && cp <= 0xDFFFu) ||
        need > cap - *pos) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (cp < 0x80u) {
        buf[(*pos)++] = (char)cp;
    } else if (cp < 0x800u) {
        buf[(*pos)++] = (char)(0xC0u | (cp >> 6));
        buf[(*pos)++] = (char)(0x80u | (cp & 0x3Fu));
    } else if (cp < 0x10000u) {
        buf[(*pos)++] = (char)(0xE0u | (cp >> 12));
        buf[(*pos)++] = (char)(0x80u | ((cp >> 6) & 0x3Fu));
        buf[(*pos)++] = (char)(0x80u | (cp & 0x3Fu));
    } else {
        buf[(*pos)++] = (char)(0xF0u | (cp >> 18));
        buf[(*pos)++] = (char)(0x80u | ((cp >> 12) & 0x3Fu));
        buf[(*pos)++] = (char)(0x80u | ((cp >> 6) & 0x3Fu));
        buf[(*pos)++] = (char)(0x80u | (cp & 0x3Fu));
    }
    return SRMECH_OK;
}

/* Parse exactly 4 hex digits at p->i (advancing it) into *out. */
static srmech_status_t toml_parse_hex4(toml_parser_t *p, uint32_t *out)
{
    assert(p != NULL);
    assert(out != NULL);
    uint32_t v = 0u;
    for (int k = 0; k < 4; k++) {
        if (p->i >= p->n) {
            return SRMECH_ERR_BAD_INPUT;
        }
        char c = p->s[p->i];
        uint32_t d;
        if (c >= '0' && c <= '9') {
            d = (uint32_t)(c - '0');
        } else if (c >= 'a' && c <= 'f') {
            d = (uint32_t)(c - 'a') + 10u;
        } else if (c >= 'A' && c <= 'F') {
            d = (uint32_t)(c - 'A') + 10u;
        } else {
            return SRMECH_ERR_BAD_INPUT;
        }
        v = (v << 4) | d;
        p->i++;
    }
    *out = v;
    return SRMECH_OK;
}

/* Handle one backslash escape inside a basic string (p->i points just
 * past the '\\'); appends the decoded byte(s) to dst[*pos]. */
static srmech_status_t toml_string_escape(toml_parser_t *p, char *dst,
                                          size_t cap, size_t *pos)
{
    assert(p != NULL);
    assert(dst != NULL && pos != NULL);
    if (p->i >= p->n) {
        return SRMECH_ERR_BAD_INPUT;
    }
    char e = p->s[p->i];
    p->i++;
    char out = 0;
    bool simple = true;
    switch (e) {
        case '"':  out = '"';  break;
        case '\\': out = '\\'; break;
        case 'n':  out = '\n'; break;
        case 't':  out = '\t'; break;
        case 'r':  out = '\r'; break;
        case 'b':  out = '\b'; break;
        case 'f':  out = '\f'; break;
        case 'u':  simple = false; break;
        default:   return SRMECH_ERR_BAD_INPUT;
    }
    if (simple) {
        if (*pos >= cap) {
            return SRMECH_ERR_BAD_INPUT;
        }
        dst[(*pos)++] = out;
        return SRMECH_OK;
    }
    uint32_t cp = 0u;
    srmech_status_t st = toml_parse_hex4(p, &cp);
    if (st != SRMECH_OK) {
        return st;
    }
    return toml_utf8_encode(cp, dst, cap, pos);
}

/* Body for single-line basic ("...") / literal ('...') strings. `quote`
 * is the delimiter; `escapes` enables backslash handling. Writes a
 * NUL-terminated copy into the arena and fills *out. */
static srmech_status_t toml_parse_quoted(toml_parser_t *p, char quote,
                                         bool escapes, srmech_toml_value_t *out)
{
    assert(p != NULL);
    assert(out != NULL);
    size_t avail = p->n - p->i;
    void *mem = NULL;
    srmech_status_t st = toml_arena_alloc(&p->arena, avail + 1u, &mem);
    if (st != SRMECH_OK) {
        return st;
    }
    char *dst = (char *)mem;
    size_t pos = 0u;
    while (p->i < p->n) {
        char c = p->s[p->i];
        if (c == quote) {
            p->i++;
            dst[pos] = '\0';
            out->type = SRMECH_TOML_STRING;
            out->u.str.ptr = dst;
            out->u.str.len = (uint32_t)pos;
            return SRMECH_OK;
        }
        if (c == '\n') {
            return SRMECH_ERR_BAD_INPUT;  /* newline in single-line string */
        }
        if (escapes && c == '\\') {
            p->i++;
            st = toml_string_escape(p, dst, avail, &pos);
            if (st != SRMECH_OK) {
                return st;
            }
        } else {
            dst[pos++] = c;
            p->i++;
        }
    }
    return SRMECH_ERR_BAD_INPUT;  /* unterminated string */
}

/* Body for multiline """...""" / '''...''' (three openers already
 * consumed). A leading newline directly after the opener is trimmed. */
static srmech_status_t toml_parse_multiline(toml_parser_t *p, char quote,
                                            bool escapes,
                                            srmech_toml_value_t *out)
{
    assert(p != NULL);
    assert(out != NULL);
    if (p->i < p->n && p->s[p->i] == '\r') {
        p->i++;
    }
    if (p->i < p->n && p->s[p->i] == '\n') {
        p->i++;
    }
    size_t avail = p->n - p->i;
    void *mem = NULL;
    srmech_status_t st = toml_arena_alloc(&p->arena, avail + 1u, &mem);
    if (st != SRMECH_OK) {
        return st;
    }
    char *dst = (char *)mem;
    size_t pos = 0u;
    while (p->i < p->n) {
        char c = p->s[p->i];
        if (c == quote && p->n - p->i >= 3u &&
            p->s[p->i + 1u] == quote && p->s[p->i + 2u] == quote) {
            p->i += 3u;
            dst[pos] = '\0';
            out->type = SRMECH_TOML_STRING;
            out->u.str.ptr = dst;
            out->u.str.len = (uint32_t)pos;
            return SRMECH_OK;
        }
        if (escapes && c == '\\') {
            p->i++;
            st = toml_string_escape(p, dst, avail, &pos);
            if (st != SRMECH_OK) {
                return st;
            }
        } else if (c == '\r' && p->i + 1u < p->n && p->s[p->i + 1u] == '\n') {
            /* Normalize CRLF -> LF inside multiline strings, matching
             * Python tomllib/tomli (a CRLF newline decodes to a single LF).
             * Without this, a CRLF-checked-out descriptor would parse to a
             * different string in C than in Python. */
            dst[pos++] = '\n';
            p->i += 2u;
        } else {
            dst[pos++] = c;
            p->i++;
        }
    }
    return SRMECH_ERR_BAD_INPUT;  /* unterminated multiline string */
}

/* Dispatch a value that begins with a quote (already at p->i). */
static srmech_status_t toml_parse_string(toml_parser_t *p,
                                         srmech_toml_value_t *out)
{
    assert(p != NULL);
    assert(out != NULL);
    char q = p->s[p->i];
    bool escapes = (q == '"');
    bool triple = (p->n - p->i >= 3u) &&
                  p->s[p->i + 1u] == q && p->s[p->i + 2u] == q;
    if (triple) {
        p->i += 3u;
        return toml_parse_multiline(p, q, escapes, out);
    }
    p->i += 1u;
    return toml_parse_quoted(p, q, escapes, out);
}

/* ================================================================== *
 * Number / bool parsing.
 * ================================================================== */

/* Copy a number token (dropping '_' separators) into `buf`; classifies
 * it as float iff it contains '.', 'e', or 'E'. */
static srmech_status_t toml_collect_number(toml_parser_t *p, char *buf,
                                           size_t cap, bool *is_float)
{
    assert(p != NULL);
    assert(buf != NULL && is_float != NULL);
    size_t k = 0u;
    *is_float = false;
    while (p->i < p->n) {
        char c = p->s[p->i];
        bool glyph = (c >= '0' && c <= '9') || c == '+' || c == '-' ||
                     c == '.' || c == 'e' || c == 'E' || c == '_';
        if (!glyph) {
            break;
        }
        p->i++;
        if (c == '_') {
            continue;
        }
        if (c == '.' || c == 'e' || c == 'E') {
            *is_float = true;
        }
        if (k >= cap - 1u) {
            return SRMECH_ERR_BAD_INPUT;
        }
        buf[k++] = c;
    }
    buf[k] = '\0';
    return (k == 0u) ? SRMECH_ERR_BAD_INPUT : SRMECH_OK;
}

/* Parse a cleaned decimal-integer token (optional +/-) to int64 with
 * overflow detection. */
static srmech_status_t toml_str_to_i64(const char *buf, int64_t *out)
{
    assert(buf != NULL);
    assert(out != NULL);
    size_t k = 0u;
    bool neg = false;
    if (buf[0] == '+' || buf[0] == '-') {
        neg = (buf[0] == '-');
        k = 1u;
    }
    if (buf[k] == '\0') {
        return SRMECH_ERR_BAD_INPUT;
    }
    uint64_t mag = 0u;
    for (; buf[k] != '\0'; k++) {
        if (buf[k] < '0' || buf[k] > '9') {
            return SRMECH_ERR_BAD_INPUT;
        }
        uint64_t d = (uint64_t)(buf[k] - '0');
        if (mag > (UINT64_MAX - d) / 10u) {
            return SRMECH_ERR_OVERFLOW;
        }
        mag = mag * 10u + d;
    }
    uint64_t limit = neg ? (uint64_t)INT64_MAX + 1u : (uint64_t)INT64_MAX;
    if (mag > limit) {
        return SRMECH_ERR_OVERFLOW;
    }
    *out = neg ? -(int64_t)mag : (int64_t)mag;
    return SRMECH_OK;
}

/* ================================================================== *
 * Correctly-rounded decimal -> double (rc397, #T1066).
 *
 * The token is parsed into a sign, an integer significand `D` (all mantissa
 * digits, point removed, leading + trailing zeros trimmed) and a net base-10
 * exponent `E`, so value = (+/-) D * 10^E. Two paths, both libm-free:
 *
 *   Clinger fast path (Clinger, PLDI 1990, "How to Read Floating Point Numbers
 *   Accurately"): when D is exactly representable (D <= 2^53) AND |E| <= 22, a
 *   SINGLE IEEE multiply/divide by an exact power of ten is provably correctly
 *   rounded — return (double)D * 10^E (or / 10^-E).
 *
 *   Exact slow path (everything else): compute the correctly-rounded double of
 *   the exact rational D * 10^E via srmech_bigint (num/den, one big divmod,
 *   round-to-nearest-EVEN on the halfway tie), assembling the IEEE bit pattern
 *   directly so normals, denormals, underflow (-> +/-0) and overflow (-> +/-inf)
 *   all round exactly. No malloc (fixed caller-owned limb storage), no libm,
 *   no goto, no recursion.
 * ================================================================== */

/* 10^0 .. 10^22 — each exactly representable in an IEEE double. */
static const double TOML_POW10[23] = {
    1e0,  1e1,  1e2,  1e3,  1e4,  1e5,  1e6,  1e7,  1e8,  1e9,  1e10, 1e11,
    1e12, 1e13, 1e14, 1e15, 1e16, 1e17, 1e18, 1e19, 1e20, 1e21, 1e22
};

/* Point a srmech_bigint carrier at caller-owned limb storage (value 0). */
static void toml_bi_init(srmech_bigint_t *bi, uint32_t *limbs, uint32_t cap)
{
    assert(bi != NULL && limbs != NULL);
    assert(cap > 0u);
    bi->sign = 0;
    bi->n = 0u;
    bi->cap = cap;
    bi->limbs = limbs;
}

/* Bit length of |a| (0 for a == 0). */
static uint32_t toml_bi_bitlen(const srmech_bigint_t *a)
{
    uint32_t top, bits = 0u;
    assert(a != NULL);
    assert(a->n == 0u || a->limbs != NULL);
    if (a->n == 0u) {
        return 0u;
    }
    top = a->limbs[a->n - 1u];
    while (top != 0u) {
        bits++;
        top >>= 1;
    }
    return (a->n - 1u) * 32u + bits;
}

/* Low 64 bits of |a| (a must fit in <= 2 limbs). */
static uint64_t toml_bi_lo64(const srmech_bigint_t *a)
{
    uint64_t v;
    assert(a != NULL);
    assert(a->n <= 2u);
    if (a->n == 0u) {
        return 0u;
    }
    v = (uint64_t)a->limbs[0];
    if (a->n == 2u) {
        v |= ((uint64_t)a->limbs[1]) << 32;
    }
    return v;
}

/* Assemble the double value = (neg?-1:+1) * m * 2^q from its IEEE bit pattern.
 * m == 0 -> +/-0; m >= 2^52 -> normal (or +/-inf on exponent overflow);
 * 0 < m < 2^52 -> denormal (q is then the fixed -1074 floor). */
static double toml_f64_assemble(int neg, uint64_t m, int q)
{
    uint64_t bits, frac;
    double out;
    int biased = 0;
    assert(m <= ((uint64_t)1u << 53));
    assert(q >= -1074);
    if (m == 0u) {
        bits = 0u;
    } else if ((m >> 52) != 0u) {
        biased = q + 1075;
        if (biased >= 2047) {
            bits = (uint64_t)2047u << 52;              /* overflow -> inf */
        } else {
            assert(biased >= 1);
            frac = m & (((uint64_t)1u << 52) - 1u);
            bits = ((uint64_t)(unsigned int)biased << 52) | frac;
        }
    } else {
        bits = m;                                      /* denormal (biased 0) */
    }
    if (neg) {
        bits |= (uint64_t)1u << 63;
    }
    memcpy(&out, &bits, sizeof(out));
    return out;
}

/* A = num << sn ; B = den << sd (exactly one of sn,sd is 0), then
 * *M = floor(A / B), *rem = A - (*M)*B. B is the effective denominator the
 * caller compares against for the half-ulp round. */
static srmech_status_t toml_f64_scaled_div(
        srmech_bigint_t *A, srmech_bigint_t *B,
        const srmech_bigint_t *num, const srmech_bigint_t *den,
        uint32_t sn, uint32_t sd, srmech_bigint_t *M, srmech_bigint_t *rem,
        void *ws, size_t ws_len)
{
    srmech_status_t st;
    assert(A != NULL && B != NULL && num != NULL && den != NULL);
    assert(M != NULL && rem != NULL);
    st = srmech_bigint_copy(A, num);
    if (st != SRMECH_OK) { return st; }
    if (sn != 0u) {
        st = srmech_bigint_shl_bits(A, A, sn);
        if (st != SRMECH_OK) { return st; }
    }
    st = srmech_bigint_copy(B, den);
    if (st != SRMECH_OK) { return st; }
    if (sd != 0u) {
        st = srmech_bigint_shl_bits(B, B, sd);
        if (st != SRMECH_OK) { return st; }
    }
    return srmech_bigint_divmod(M, rem, A, B, ws, ws_len);
}

/* Correctly round value = num/den (both > 0) to a double, round-to-nearest,
 * ties-to-even. neg carries the sign. */
static srmech_status_t toml_f64_round(
        srmech_bigint_t *num, srmech_bigint_t *den, int neg, double *out,
        srmech_bigint_t *A, srmech_bigint_t *B, srmech_bigint_t *M,
        srmech_bigint_t *rem, srmech_bigint_t *r2, void *ws, size_t ws_len)
{
    int q, iter, cmp;
    uint64_t m64 = 0u;
    srmech_status_t st;
    assert(num != NULL && den != NULL && out != NULL);
    assert(A != NULL && B != NULL && M != NULL && rem != NULL && r2 != NULL);
    q = (int)toml_bi_bitlen(num) - (int)toml_bi_bitlen(den) - 52;
    if (q < -1074) { q = -1074; }
    for (iter = 0; iter < 8; iter++) {
        uint32_t sn = (q < 0) ? (uint32_t)(-q) : 0u;
        uint32_t sd = (q > 0) ? (uint32_t)q : 0u;
        st = toml_f64_scaled_div(A, B, num, den, sn, sd, M, rem, ws, ws_len);
        if (st != SRMECH_OK) { return st; }
        assert(M->n <= 2u);
        m64 = toml_bi_lo64(M);
        if (m64 >= ((uint64_t)1u << 53)) { q += 1; continue; }
        if (m64 < ((uint64_t)1u << 52) && q > -1074) { q -= 1; continue; }
        break;
    }
    assert(iter < 8);
    st = srmech_bigint_add(r2, rem, rem);              /* r2 = 2 * rem */
    if (st != SRMECH_OK) { return st; }
    cmp = srmech_bigint_cmp(r2, B);                     /* vs the denominator */
    if (cmp > 0 || (cmp == 0 && (m64 & 1u) != 0u)) {
        m64 += 1u;
        if (m64 == ((uint64_t)1u << 53)) { m64 = (uint64_t)1u << 52; q += 1; }
    }
    *out = toml_f64_assemble(neg, m64, q);
    return SRMECH_OK;
}

/* Build the exact rational num/den for <dig[0..ndig)> * 10^E (dig are ASCII
 * digits, ndig > 0). E >= 0 folds into num as trailing zeros; E < 0 into den. */
static srmech_status_t toml_f64_build_frac(const char *dig, int ndig, int E,
                                           srmech_bigint_t *num,
                                           srmech_bigint_t *den)
{
    char tmp[420];
    int i, z;
    srmech_status_t st;
    assert(dig != NULL && num != NULL && den != NULL);
    assert(ndig > 0 && ndig < 64);
    if (E >= 0) {
        assert(ndig + E < (int)sizeof(tmp));
        for (i = 0; i < ndig; i++) { tmp[i] = dig[i]; }
        for (z = 0; z < E; z++) { tmp[ndig + z] = '0'; }
        st = srmech_bigint_from_dec(num, tmp, (size_t)(ndig + E));
        if (st != SRMECH_OK) { return st; }
        return srmech_bigint_set_i64(den, 1);
    }
    st = srmech_bigint_from_dec(num, dig, (size_t)ndig);
    if (st != SRMECH_OK) { return st; }
    assert(1 - E < (int)sizeof(tmp));
    tmp[0] = '1';
    for (z = 0; z < -E; z++) { tmp[1 + z] = '0'; }
    return srmech_bigint_from_dec(den, tmp, (size_t)(1 - E));
}

/* Exact slow path: correctly-rounded double of <dig> * 10^E over srmech_bigint,
 * with fixed caller-owned limb storage (JPL Rule 3: no malloc). */
static srmech_status_t toml_f64_bignum(const char *dig, int ndig, int E,
                                       int neg, double *out)
{
    uint32_t l_num[48], l_den[48], l_A[64], l_B[64], l_M[6], l_rem[64], l_r2[66];
    uint32_t ws[256];
    srmech_bigint_t num, den, A, B, M, rem, r2;
    srmech_status_t st;
    assert(dig != NULL && out != NULL);
    assert(ndig > 0);
    toml_bi_init(&num, l_num, 48u);
    toml_bi_init(&den, l_den, 48u);
    toml_bi_init(&A, l_A, 64u);
    toml_bi_init(&B, l_B, 64u);
    toml_bi_init(&M, l_M, 6u);
    toml_bi_init(&rem, l_rem, 64u);
    toml_bi_init(&r2, l_r2, 66u);
    st = toml_f64_build_frac(dig, ndig, E, &num, &den);
    if (st != SRMECH_OK) { return st; }
    return toml_f64_round(&num, &den, neg, out, &A, &B, &M, &rem, &r2,
                          ws, sizeof(ws));
}

/* Parse the exponent tail (chars after 'e'/'E') to a signed int, saturating
 * the magnitude so the range clamp in the caller decides inf/zero. */
static srmech_status_t toml_f64_scan_exp(const char *s, int *pexpo)
{
    int j = 0, esign = 1, expo = 0, seen = 0;
    assert(s != NULL && pexpo != NULL);
    if (s[0] == '+' || s[0] == '-') {
        esign = (s[0] == '-') ? -1 : 1;
        j = 1;
    }
    for (; s[j] != '\0'; j++) {
        if (s[j] < '0' || s[j] > '9') { return SRMECH_ERR_BAD_INPUT; }
        expo = expo * 10 + (s[j] - '0');
        if (expo > 100000) { expo = 100000; }
        seen = 1;
    }
    if (seen == 0) { return SRMECH_ERR_BAD_INPUT; }
    assert(expo >= 0 && expo <= 100000);
    *pexpo = esign * expo;
    return SRMECH_OK;
}

/* Scan a cleaned float token into sign, significand digits (point removed,
 * leading + trailing zeros trimmed) and a net base-10 exponent E such that
 * value = (neg?-1:+1) * <dig[0..*pndig)> * 10^E. *pndig == 0 means the value is
 * +/- zero. */
static srmech_status_t toml_f64_scan(const char *buf, char *dig, int dcap,
                                     int *pndig, int *pE, int *pneg)
{
    char raw[64];
    int nraw = 0, frac = 0, seen = 0, dot = 0, k = 0, had_exp = 0;
    int lo, hi, i, E;
    srmech_status_t st;
    assert(buf != NULL && dig != NULL && pndig != NULL);
    assert(pE != NULL && pneg != NULL && dcap >= 64);
    *pneg = 0;
    if (buf[0] == '+' || buf[0] == '-') { *pneg = (buf[0] == '-'); k = 1; }
    for (; buf[k] != '\0'; k++) {
        char c = buf[k];
        if (c >= '0' && c <= '9') {
            if (nraw < (int)sizeof(raw)) { raw[nraw++] = c; }
            if (dot) { frac++; }
            seen = 1;
        } else if (c == '.') {
            if (dot) { return SRMECH_ERR_BAD_INPUT; }
            dot = 1;
        } else if (c == 'e' || c == 'E') {
            had_exp = 1;
            k++;
            break;
        } else {
            return SRMECH_ERR_BAD_INPUT;
        }
    }
    if (seen == 0) { return SRMECH_ERR_BAD_INPUT; }
    E = -frac;
    if (had_exp) {
        int expo = 0;
        st = toml_f64_scan_exp(buf + k, &expo);
        if (st != SRMECH_OK) { return st; }
        E += expo;
    }
    lo = 0;
    while (lo < nraw && raw[lo] == '0') { lo++; }
    hi = nraw - 1;
    while (hi >= lo && raw[hi] == '0') { hi--; }
    if (hi < lo) { *pndig = 0; *pE = 0; return SRMECH_OK; }   /* all zero */
    E += (nraw - 1 - hi);                                      /* trailing 0s */
    if (hi - lo + 1 > dcap) { return SRMECH_ERR_OVERFLOW; }     /* live dcap bound (not assert-only) */
    for (i = 0; i <= hi - lo; i++) { dig[i] = raw[lo + i]; }
    *pndig = hi - lo + 1;
    *pE = E;
    return SRMECH_OK;
}

/* Parse a cleaned decimal-float token to a correctly-rounded double. */
static srmech_status_t toml_str_to_f64(const char *buf, double *out)
{
    char dig[64];
    int ndig = 0, E = 0, neg = 0, i;
    uint64_t D;
    srmech_status_t st;
    assert(buf != NULL && out != NULL);
    st = toml_f64_scan(buf, dig, (int)sizeof(dig), &ndig, &E, &neg);
    if (st != SRMECH_OK) { return st; }
    assert(ndig >= 0 && ndig < 64);
    if (ndig == 0) {                                   /* +/- zero */
        *out = neg ? -0.0 : 0.0;
        return SRMECH_OK;
    }
    if (E >= 309) {                                    /* >= 10^309 -> inf */
        *out = toml_f64_assemble(neg, (uint64_t)1u << 52, 4000);
        return SRMECH_OK;
    }
    if (E <= -400) {                                   /* < half min-denormal */
        *out = neg ? -0.0 : 0.0;
        return SRMECH_OK;
    }
    if (ndig <= 19) {                                  /* Clinger fast path */
        D = 0u;
        for (i = 0; i < ndig; i++) { D = D * 10u + (uint64_t)(dig[i] - '0'); }
        if (D <= ((uint64_t)1u << 53) && E >= -22 && E <= 22) {
            double v = (double)D;
            v = (E >= 0) ? (v * TOML_POW10[E]) : (v / TOML_POW10[-E]);
            *out = neg ? -v : v;
            return SRMECH_OK;
        }
    }
    return toml_f64_bignum(dig, ndig, E, neg, out);
}

/* Parse a numeric value (int or float) at p->i. */
static srmech_status_t toml_parse_number(toml_parser_t *p,
                                         srmech_toml_value_t *out)
{
    assert(p != NULL);
    assert(out != NULL);
    char buf[64];
    bool is_float = false;
    srmech_status_t st = toml_collect_number(p, buf, sizeof(buf), &is_float);
    if (st != SRMECH_OK) {
        return st;
    }
    if (is_float) {
        double f = 0.0;
        st = toml_str_to_f64(buf, &f);
        if (st != SRMECH_OK) {
            return st;
        }
        out->type = SRMECH_TOML_FLOAT;
        out->u.f = f;
        return SRMECH_OK;
    }
    int64_t v = 0;
    st = toml_str_to_i64(buf, &v);
    if (st != SRMECH_OK) {
        return st;
    }
    out->type = SRMECH_TOML_INT;
    out->u.i = v;
    return SRMECH_OK;
}

/* Match the literal `lit` at p->i; on success advance past it. */
static bool toml_match_literal(toml_parser_t *p, const char *lit)
{
    assert(p != NULL);
    assert(lit != NULL);
    size_t k = strlen(lit);
    if (p->n - p->i < k || strncmp(p->s + p->i, lit, k) != 0) {
        return false;
    }
    p->i += k;
    return true;
}

/* ================================================================== *
 * Keys.
 * ================================================================== */

/* Parse one bare-key segment at p->i into an arena NUL-terminated
 * string; *out points at it, *out_len is the byte length. */
static srmech_status_t toml_parse_bare_key(toml_parser_t *p,
                                           const char **out, uint32_t *out_len)
{
    assert(p != NULL);
    assert(out != NULL && out_len != NULL);
    size_t start = p->i;
    while (p->i < p->n && toml_is_bare_key_char(p->s[p->i])) {
        p->i++;
    }
    size_t klen = p->i - start;
    if (klen == 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    void *mem = NULL;
    srmech_status_t st = toml_arena_alloc(&p->arena, klen + 1u, &mem);
    if (st != SRMECH_OK) {
        return st;
    }
    char *dst = (char *)mem;
    memcpy(dst, p->s + start, klen);
    dst[klen] = '\0';
    *out = dst;
    *out_len = (uint32_t)klen;
    return SRMECH_OK;
}

/* Parse a dotted key path `a.b.c` at p->i into seg pointers; *n_seg gets
 * the count (>=1). Each segment is an arena bare-key string. */
static srmech_status_t toml_parse_key_path(toml_parser_t *p, const char **segs,
                                           uint32_t cap, uint32_t *n_seg)
{
    assert(p != NULL);
    assert(segs != NULL && n_seg != NULL);
    uint32_t count = 0u;
    for (uint32_t guard = 0; guard <= cap; guard++) {
        if (count >= cap) {
            return SRMECH_ERR_OVERFLOW;
        }
        uint32_t klen = 0u;
        srmech_status_t st = toml_parse_bare_key(p, &segs[count], &klen);
        if (st != SRMECH_OK) {
            return st;
        }
        count++;
        toml_skip_ws_inline(p);
        if (p->i < p->n && p->s[p->i] == '.') {
            p->i++;
            toml_skip_ws_inline(p);
            continue;
        }
        break;
    }
    *n_seg = count;
    return SRMECH_OK;
}

/* ================================================================== *
 * Value insertion.
 * ================================================================== */

/* Insert (key, leaf-value) into a builder table, rejecting duplicate
 * keys. The leaf value is copied into a fresh KIND_LEAF builder value. */
static srmech_status_t toml_put_leaf(toml_parser_t *p, toml_btable_t *t,
                                     const char *key,
                                     const srmech_toml_value_t *leaf)
{
    assert(p != NULL);
    assert(t != NULL && key != NULL && leaf != NULL);
    if (toml_btable_find(t, key) != NULL) {
        return SRMECH_ERR_BAD_INPUT;  /* duplicate key */
    }
    toml_bvalue_t *bv = NULL;
    srmech_status_t st = toml_bvalue_new(p, TOML_KIND_LEAF, &bv);
    if (st != SRMECH_OK) {
        return st;
    }
    bv->leaf = *leaf;
    return toml_btable_append(p, t, key, bv);
}

/* ================================================================== *
 * Compound values: array + inline table.
 * ================================================================== */

/* Copy the collected element pointers (an arena linked list of `count` nodes)
 * into a right-sized arena items[] and fill the ARRAY value `out`. */
static srmech_status_t toml_emit_array(toml_parser_t *p,
                                       const toml_alist_node_t *head,
                                       uint32_t count, srmech_toml_value_t *out)
{
    assert(p != NULL);
    assert(out != NULL);
    srmech_toml_value_t **arr = NULL;
    if (count > 0u) {
        void *mem = NULL;
        size_t bytes = (size_t)count * sizeof(srmech_toml_value_t *);
        srmech_status_t st = toml_arena_alloc(&p->arena, bytes, &mem);
        if (st != SRMECH_OK) {
            return st;
        }
        arr = (srmech_toml_value_t **)mem;
        const toml_alist_node_t *n = head;
        for (uint32_t k = 0u; k < count; k++) {
            assert(n != NULL);
            arr[k] = n->val;
            n = n->next;
        }
    }
    out->type = SRMECH_TOML_ARRAY;
    out->u.arr.items = arr;
    out->u.arr.n = count;
    return SRMECH_OK;
}

/* Copy a fully-built leaf/array/inline-table value into a fresh arena
 * value slot, returning the pointer. */
static srmech_status_t toml_dup_value(toml_parser_t *p,
                                      const srmech_toml_value_t *src,
                                      srmech_toml_value_t **out)
{
    assert(p != NULL);
    assert(src != NULL && out != NULL);
    void *mem = NULL;
    srmech_status_t st = toml_arena_alloc(&p->arena,
                                          sizeof(srmech_toml_value_t), &mem);
    if (st != SRMECH_OK) {
        return st;
    }
    srmech_toml_value_t *v = (srmech_toml_value_t *)mem;
    *v = *src;
    *out = v;
    return SRMECH_OK;
}

/* Parse `[ v, v, ... ]` (opening '[' already consumed). Array elements
 * are values that are themselves already finalised (scalars, nested
 * arrays, inline tables) — no deferred builder tables appear here. */
static srmech_status_t toml_parse_array(toml_parser_t *p,
                                        srmech_toml_value_t *out, int depth)
{
    assert(p != NULL);
    assert(out != NULL);
    if (depth >= SRMECH_TOML_MAX_DEPTH) {
        return SRMECH_ERR_OVERFLOW;
    }
    /* Collect elements into an arena linked list (like the builder tables) —
     * NO fixed staging array, so the element count is bounded only by the
     * caller arena, not a compiled-in 256-entry cap (rc159
     * standalone-complete honor). The scan is still JPL-Rule-2-bounded: each
     * element consumes >= 1 input byte, so it cannot exceed p->n. */
    toml_alist_node_t *head = NULL;
    toml_alist_node_t *tail = NULL;
    uint32_t count = 0u;
    for (size_t guard = 0; guard <= p->n; guard++) {
        toml_skip_ws_nl(p);
        if (p->i >= p->n) {
            return SRMECH_ERR_BAD_INPUT;  /* unterminated array */
        }
        if (p->s[p->i] == ']') {
            p->i++;
            return toml_emit_array(p, head, count, out);
        }
        srmech_toml_value_t elem;
        srmech_status_t st = toml_parse_value(p, &elem, depth + 1);
        if (st != SRMECH_OK) {
            return st;
        }
        void *mem = NULL;
        st = toml_arena_alloc(&p->arena, sizeof(toml_alist_node_t), &mem);
        if (st != SRMECH_OK) {
            return st;
        }
        toml_alist_node_t *node = (toml_alist_node_t *)mem;
        st = toml_dup_value(p, &elem, &node->val);
        if (st != SRMECH_OK) {
            return st;
        }
        node->next = NULL;
        if (tail == NULL) {
            head = node;
        } else {
            tail->next = node;
        }
        tail = node;
        count++;
        toml_skip_ws_nl(p);
        if (p->i < p->n && p->s[p->i] == ',') {
            p->i++;
        }
    }
    return SRMECH_ERR_OVERFLOW;
}

/* Parse `{ k = v, ... }` (opening '{' already consumed) into a builder
 * table, then finalise it into the TABLE value `out`. */
static srmech_status_t toml_parse_inline_table(toml_parser_t *p,
                                               srmech_toml_value_t *out,
                                               int depth)
{
    assert(p != NULL);
    assert(out != NULL);
    if (depth >= SRMECH_TOML_MAX_DEPTH) {
        return SRMECH_ERR_OVERFLOW;
    }
    toml_btable_t *t = NULL;
    srmech_status_t st = toml_btable_new(p, true, &t);
    if (st != SRMECH_OK) {
        return st;
    }
    toml_skip_ws_nl(p);
    /* No entry cap: keys append to an arena linked list, so the inline table
     * is bounded only by the caller arena. Still JPL-Rule-2-bounded — each
     * key/value pair consumes >= 1 input byte, so it cannot exceed p->n. */
    for (size_t guard = 0; guard <= p->n; guard++) {
        if (p->i >= p->n) {
            return SRMECH_ERR_BAD_INPUT;  /* unterminated inline table */
        }
        if (p->s[p->i] == '}') {
            p->i++;
            return toml_finalize_btable(p, t, out, depth);
        }
        const char *key = NULL;
        uint32_t klen = 0u;
        st = toml_parse_bare_key(p, &key, &klen);
        if (st != SRMECH_OK) {
            return st;
        }
        toml_skip_ws_inline(p);
        if (p->i >= p->n || p->s[p->i] != '=') {
            return SRMECH_ERR_BAD_INPUT;
        }
        p->i++;
        toml_skip_ws_inline(p);
        srmech_toml_value_t elem;
        st = toml_parse_value(p, &elem, depth + 1);
        if (st != SRMECH_OK) {
            return st;
        }
        st = toml_put_leaf(p, t, key, &elem);
        if (st != SRMECH_OK) {
            return st;
        }
        toml_skip_ws_nl(p);
        if (p->i < p->n && p->s[p->i] == ',') {
            p->i++;
            toml_skip_ws_nl(p);
        }
    }
    return SRMECH_ERR_OVERFLOW;
}

/* ================================================================== *
 * Value dispatch.
 * ================================================================== */

static srmech_status_t toml_parse_value(toml_parser_t *p,
                                        srmech_toml_value_t *out, int depth)
{
    assert(p != NULL);
    assert(out != NULL);
    if (p->i >= p->n) {
        return SRMECH_ERR_BAD_INPUT;
    }
    char c = p->s[p->i];
    if (c == '"' || c == '\'') {
        return toml_parse_string(p, out);
    }
    if (c == '[') {
        p->i++;
        return toml_parse_array(p, out, depth);
    }
    if (c == '{') {
        p->i++;
        return toml_parse_inline_table(p, out, depth);
    }
    if (toml_match_literal(p, "true")) {
        out->type = SRMECH_TOML_BOOL;
        out->u.b = 1;
        return SRMECH_OK;
    }
    if (toml_match_literal(p, "false")) {
        out->type = SRMECH_TOML_BOOL;
        out->u.b = 0;
        return SRMECH_OK;
    }
    return toml_parse_number(p, out);
}

/* ================================================================== *
 * Finalisation: builder tree -> srmech_toml_value_t tree.
 * ================================================================== */

/* Allocate the parallel keys[]/vals[] arrays for a finalised table. */
static srmech_status_t toml_alloc_table_arrays(toml_parser_t *p, uint32_t count,
                                               const char ***out_keys,
                                               srmech_toml_value_t ***out_vals)
{
    assert(p != NULL);
    assert(out_keys != NULL && out_vals != NULL);
    void *km = NULL;
    void *vm = NULL;
    srmech_status_t st = toml_arena_alloc(&p->arena,
                                          (size_t)count * sizeof(char *), &km);
    if (st != SRMECH_OK) {
        return st;
    }
    st = toml_arena_alloc(&p->arena,
                          (size_t)count * sizeof(srmech_toml_value_t *), &vm);
    if (st != SRMECH_OK) {
        return st;
    }
    *out_keys = (const char **)km;
    *out_vals = (srmech_toml_value_t **)vm;
    return SRMECH_OK;
}

/* Finalise a KIND_ATABLE builder value into an ARRAY value whose items
 * are each a finalised TABLE. */
static srmech_status_t toml_finalize_atable(toml_parser_t *p,
                                            const toml_bvalue_t *bv,
                                            srmech_toml_value_t *out, int depth)
{
    assert(p != NULL);
    assert(bv != NULL && out != NULL);
    srmech_toml_value_t **items = NULL;
    if (bv->atable_n > 0u) {
        void *mem = NULL;
        size_t bytes = (size_t)bv->atable_n * sizeof(srmech_toml_value_t *);
        srmech_status_t st = toml_arena_alloc(&p->arena, bytes, &mem);
        if (st != SRMECH_OK) {
            return st;
        }
        items = (srmech_toml_value_t **)mem;
    }
    const toml_atable_node_t *node = bv->atable_head;
    for (uint32_t k = 0u; k < bv->atable_n; k++) {
        assert(node != NULL);
        void *slot = NULL;
        srmech_status_t st = toml_arena_alloc(&p->arena,
                                              sizeof(srmech_toml_value_t),
                                              &slot);
        if (st != SRMECH_OK) {
            return st;
        }
        items[k] = (srmech_toml_value_t *)slot;
        st = toml_finalize_btable(p, node->table, items[k], depth + 1);
        if (st != SRMECH_OK) {
            return st;
        }
        node = node->next;
    }
    out->type = SRMECH_TOML_ARRAY;
    out->u.arr.items = items;
    out->u.arr.n = bv->atable_n;
    return SRMECH_OK;
}

/* Recurse a builder table into a right-sized TABLE value. */
static srmech_status_t toml_finalize_btable(toml_parser_t *p,
                                            const toml_btable_t *t,
                                            srmech_toml_value_t *out, int depth)
{
    assert(p != NULL);
    assert(t != NULL && out != NULL);
    if (depth >= SRMECH_TOML_MAX_DEPTH) {
        return SRMECH_ERR_OVERFLOW;
    }
    const char **keys = NULL;
    srmech_toml_value_t **vals = NULL;
    if (t->count > 0u) {
        srmech_status_t st = toml_alloc_table_arrays(p, t->count, &keys, &vals);
        if (st != SRMECH_OK) {
            return st;
        }
    }
    const toml_bentry_t *e = t->head;
    for (uint32_t k = 0u; k < t->count; k++) {
        assert(e != NULL);
        srmech_status_t st = toml_finalize_bvalue(p, e->val, &vals[k],
                                                  depth + 1);
        if (st != SRMECH_OK) {
            return st;
        }
        keys[k] = e->key;
        e = e->next;
    }
    out->type = SRMECH_TOML_TABLE;
    out->u.tbl.keys = keys;
    out->u.tbl.vals = vals;
    out->u.tbl.n = t->count;
    return SRMECH_OK;
}

/* Finalise a builder value (leaf / table / array-of-tables) into a fresh
 * value slot. */
static srmech_status_t toml_finalize_bvalue(toml_parser_t *p,
                                            const toml_bvalue_t *bv,
                                            srmech_toml_value_t **out,
                                            int depth)
{
    assert(p != NULL);
    assert(bv != NULL && out != NULL);
    void *mem = NULL;
    srmech_status_t st = toml_arena_alloc(&p->arena,
                                          sizeof(srmech_toml_value_t), &mem);
    if (st != SRMECH_OK) {
        return st;
    }
    srmech_toml_value_t *v = (srmech_toml_value_t *)mem;
    if (bv->kind == TOML_KIND_TABLE) {
        st = toml_finalize_btable(p, bv->table, v, depth);
    } else if (bv->kind == TOML_KIND_ATABLE) {
        st = toml_finalize_atable(p, bv, v, depth);
    } else {
        *v = bv->leaf;
        st = SRMECH_OK;
    }
    if (st != SRMECH_OK) {
        return st;
    }
    *out = v;
    return SRMECH_OK;
}

/* ================================================================== *
 * Document structure: dotted paths, key/value, table headers.
 * ================================================================== */

/* Resolve one path segment to its child builder table, creating it if
 * absent. Errors if the segment already names a non-table (or inline). */
static srmech_status_t toml_path_child(toml_parser_t *p, toml_btable_t *parent,
                                       const char *seg, toml_btable_t **out)
{
    assert(p != NULL);
    assert(parent != NULL && seg != NULL && out != NULL);
    toml_bentry_t *e = toml_btable_find(parent, seg);
    if (e != NULL) {
        if (e->val->kind == TOML_KIND_ATABLE) {
            /* Path descends into the LAST element of an array-of-tables. */
            assert(e->val->atable_tail != NULL);
            *out = e->val->atable_tail->table;
            return SRMECH_OK;
        }
        if (e->val->kind != TOML_KIND_TABLE || e->val->table->is_inline) {
            return SRMECH_ERR_BAD_INPUT;  /* crosses a non-table */
        }
        *out = e->val->table;
        return SRMECH_OK;
    }
    toml_btable_t *child = NULL;
    srmech_status_t st = toml_btable_new(p, false, &child);
    if (st != SRMECH_OK) {
        return st;
    }
    toml_bvalue_t *bv = NULL;
    st = toml_bvalue_new(p, TOML_KIND_TABLE, &bv);
    if (st != SRMECH_OK) {
        return st;
    }
    bv->table = child;
    st = toml_btable_append(p, parent, seg, bv);
    if (st != SRMECH_OK) {
        return st;
    }
    *out = child;
    return SRMECH_OK;
}

/* Descend `root` along the first `n_seg` segments, creating/reopening
 * intermediate builder tables; returns the final table in *out. */
static srmech_status_t toml_descend_path(toml_parser_t *p, toml_btable_t *root,
                                         const char *const *segs, uint32_t n_seg,
                                         toml_btable_t **out)
{
    assert(p != NULL);
    assert(root != NULL && (segs != NULL || n_seg == 0u) && out != NULL);
    toml_btable_t *cur = root;
    for (uint32_t k = 0u; k < n_seg; k++) {
        srmech_status_t st = toml_path_child(p, cur, segs[k], &cur);
        if (st != SRMECH_OK) {
            return st;
        }
    }
    *out = cur;
    return SRMECH_OK;
}

/* Handle a `key = value` (or `a.b = value`) line; `cur` is the active
 * table set by the most recent header. */
static srmech_status_t toml_parse_keyval(toml_parser_t *p, toml_btable_t *cur)
{
    assert(p != NULL);
    assert(cur != NULL);
    const char *segs[SRMECH_TOML_MAX_DEPTH];
    uint32_t n_seg = 0u;
    srmech_status_t st = toml_parse_key_path(p, segs, SRMECH_TOML_MAX_DEPTH,
                                             &n_seg);
    if (st != SRMECH_OK) {
        return st;
    }
    toml_btable_t *parent = cur;
    if (n_seg > 1u) {
        st = toml_descend_path(p, cur, segs, n_seg - 1u, &parent);
        if (st != SRMECH_OK) {
            return st;
        }
    }
    const char *key = segs[n_seg - 1u];
    toml_skip_ws_inline(p);
    if (p->i >= p->n || p->s[p->i] != '=') {
        return SRMECH_ERR_BAD_INPUT;
    }
    p->i++;
    toml_skip_ws_inline(p);
    srmech_toml_value_t val;
    st = toml_parse_value(p, &val, 0);
    if (st != SRMECH_OK) {
        return st;
    }
    return toml_put_leaf(p, parent, key, &val);
}

/* Append a fresh builder table to the array-of-tables named `seg` under
 * `parent` (creating the array if absent); returns the new table. */
static srmech_status_t toml_array_of_tables_append(toml_parser_t *p,
                                                   toml_btable_t *parent,
                                                   const char *seg,
                                                   toml_btable_t **out)
{
    assert(p != NULL);
    assert(parent != NULL && seg != NULL && out != NULL);
    toml_bentry_t *e = toml_btable_find(parent, seg);
    toml_bvalue_t *bv = NULL;
    if (e != NULL) {
        if (e->val->kind != TOML_KIND_ATABLE) {
            return SRMECH_ERR_BAD_INPUT;  /* seg already a non-array */
        }
        bv = e->val;
    } else {
        srmech_status_t st = toml_bvalue_new(p, TOML_KIND_ATABLE, &bv);
        if (st != SRMECH_OK) {
            return st;
        }
        st = toml_btable_append(p, parent, seg, bv);
        if (st != SRMECH_OK) {
            return st;
        }
    }
    /* No element cap for an array-of-tables: each element table links onto an
     * arena list, bounded only by the caller arena (rc159 honor). */
    return toml_atable_link(p, bv, out);
}

/* Allocate a new element table for an array-of-tables and link it on. */
static srmech_status_t toml_atable_link(toml_parser_t *p, toml_bvalue_t *bv,
                                        toml_btable_t **out)
{
    assert(p != NULL);
    assert(bv != NULL && out != NULL);
    toml_btable_t *elem = NULL;
    srmech_status_t st = toml_btable_new(p, false, &elem);
    if (st != SRMECH_OK) {
        return st;
    }
    void *mem = NULL;
    st = toml_arena_alloc(&p->arena, sizeof(toml_atable_node_t), &mem);
    if (st != SRMECH_OK) {
        return st;
    }
    toml_atable_node_t *node = (toml_atable_node_t *)mem;
    node->table = elem;
    node->next = NULL;
    if (bv->atable_tail == NULL) {
        bv->atable_head = node;
    } else {
        bv->atable_tail->next = node;
    }
    bv->atable_tail = node;
    bv->atable_n++;
    *out = elem;
    return SRMECH_OK;
}

/* Handle a `[header]` or `[[header]]` line; opening bracket at p->i.
 * Updates *cur to the active table the following keys land in. */
static srmech_status_t toml_parse_table_header(toml_parser_t *p,
                                               toml_btable_t *root,
                                               toml_btable_t **cur)
{
    assert(p != NULL);
    assert(root != NULL && cur != NULL);
    bool array_tbl = false;
    p->i++;  /* consume first '[' */
    if (p->i < p->n && p->s[p->i] == '[') {
        array_tbl = true;
        p->i++;
    }
    toml_skip_ws_inline(p);
    const char *segs[SRMECH_TOML_MAX_DEPTH];
    uint32_t n_seg = 0u;
    srmech_status_t st = toml_parse_key_path(p, segs, SRMECH_TOML_MAX_DEPTH,
                                             &n_seg);
    if (st != SRMECH_OK) {
        return st;
    }
    toml_skip_ws_inline(p);
    if (!toml_match_literal(p, array_tbl ? "]]" : "]")) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (!array_tbl) {
        return toml_descend_path(p, root, segs, n_seg, cur);
    }
    toml_btable_t *parent = root;
    if (n_seg > 1u) {
        st = toml_descend_path(p, root, segs, n_seg - 1u, &parent);
        if (st != SRMECH_OK) {
            return st;
        }
    }
    return toml_array_of_tables_append(p, parent, segs[n_seg - 1u], cur);
}

/* ================================================================== *
 * Top-level driver.
 * ================================================================== */

/* Parse one statement (header or key/value) at the cursor; updates *cur
 * for headers; requires a newline (or EOF) to follow. */
static srmech_status_t toml_parse_statement(toml_parser_t *p,
                                            toml_btable_t *root,
                                            toml_btable_t **cur)
{
    assert(p != NULL);
    assert(root != NULL && cur != NULL);
    char c = p->s[p->i];
    srmech_status_t st;
    if (c == '[') {
        st = toml_parse_table_header(p, root, cur);
    } else if (toml_is_bare_key_char(c)) {
        st = toml_parse_keyval(p, *cur);
    } else {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (st != SRMECH_OK) {
        return st;
    }
    toml_skip_ws_inline(p);
    if (p->i < p->n && p->s[p->i] != '\n' && p->s[p->i] != '\r') {
        return SRMECH_ERR_BAD_INPUT;  /* trailing junk after statement */
    }
    return SRMECH_OK;
}

/* Finalise the root builder table into the returned root TABLE value. */
static srmech_status_t toml_finalize_root(toml_parser_t *p, toml_btable_t *root,
                                          srmech_toml_value_t **out)
{
    assert(p != NULL);
    assert(root != NULL && out != NULL);
    void *mem = NULL;
    srmech_status_t st = toml_arena_alloc(&p->arena,
                                          sizeof(srmech_toml_value_t), &mem);
    if (st != SRMECH_OK) {
        return st;
    }
    srmech_toml_value_t *rootv = (srmech_toml_value_t *)mem;
    st = toml_finalize_btable(p, root, rootv, 0);
    if (st != SRMECH_OK) {
        return st;
    }
    *out = rootv;
    return SRMECH_OK;
}

/* Safe upper bound for the parse arena (see srmech.h for the contract). The
 * transient builder tree and the finalised value tree both live in `ws`, so the
 * cost is linear in the source length; the constant floor covers a tiny doc's
 * fixed root overhead. 256 bytes/source-byte is the same parse-only budget
 * srmech_dsl_toml_chain_to_json carves internally, and it dwarfs the ~56
 * bytes/source-byte a densest-possible `a=1\n` corpus actually consumes. */
size_t srmech_toml_parse_arena_bytes(size_t src_len)
{
    assert(sizeof(srmech_toml_value_t) <= 256u);
    assert(sizeof(toml_bvalue_t) <= 256u);
    return 256u * src_len + 65536u;
}

srmech_status_t srmech_toml_parse(const char *src, size_t len,
                                  void *ws, size_t ws_len,
                                  srmech_toml_value_t **out)
{
    assert(out != NULL);
    assert(ws != NULL || ws_len == 0u);
    if (ws == NULL || out == NULL || (src == NULL && len > 0u)) {
        return SRMECH_ERR_NULL_ARG;
    }
    *out = NULL;
    toml_parser_t p;
    p.s = src;
    p.n = len;
    p.i = 0u;
    p.arena.base = (uint8_t *)ws;
    p.arena.len = ws_len;
    p.arena.used = 0u;
    toml_btable_t *root = NULL;
    srmech_status_t st = toml_btable_new(&p, false, &root);
    if (st != SRMECH_OK) {
        return st;
    }
    toml_btable_t *cur = root;
    for (size_t guard = 0; guard <= len; guard++) {
        toml_skip_ws_nl(&p);
        if (p.i >= p.n) {
            break;
        }
        st = toml_parse_statement(&p, root, &cur);
        if (st != SRMECH_OK) {
            return st;
        }
    }
    return toml_finalize_root(&p, root, out);
}

/* ================================================================== *
 * Public lookup.
 * ================================================================== */

const srmech_toml_value_t *srmech_toml_table_get(
    const srmech_toml_value_t *table, const char *key)
{
    assert(table != NULL || key != NULL);
    if (table == NULL || key == NULL || table->type != SRMECH_TOML_TABLE) {
        return NULL;
    }
    /* A well-formed TABLE value always has both parallel arrays present
     * whenever it has entries (the finaliser allocates them together). */
    assert(table->u.tbl.n == 0u || table->u.tbl.keys != NULL);
    for (uint32_t k = 0u; k < table->u.tbl.n; k++) {
        if (strcmp(table->u.tbl.keys[k], key) == 0) {
            return table->u.tbl.vals[k];
        }
    }
    return NULL;
}
