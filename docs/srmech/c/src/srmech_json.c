/*
 * srmech_json.c — malloc-free JSON parser + canonical writer.
 *
 * The keystone the §41 genome-persistence C mirror (and the wider AMSC
 * provenance C surface) needs: a JSON module whose writer emits bytes
 * BYTE-IDENTICAL to CPython's
 *   json.dumps(obj, sort_keys=True, ensure_ascii=False)
 * for any tree of null / bool / int / string / object / array — which
 * is exactly what an MPR manifest / a genome catalog is (float-free).
 *
 * Conventions mirror srmech's TOML parser: a caller-supplied
 * arena/workspace bump allocator (`void *ws, size_t ws_len`), a
 * value-tree union (srmech_json_value_t in srmech.h), the recursion-
 * depth guard SRMECH_JSON_MAX_DEPTH, and the JPL-clean style: no goto,
 * no malloc, no libm, <=60-line functions, >=2 asserts per non-exempt
 * function, no multi-line macros. There is NO compiled-in object-width
 * cap: object children grow arena-backed on parse, and the writer's
 * key-sort scratch is carved from a caller arena (srmech_json_write_ws
 * + srmech_json_write_arena_bytes), so an object is bounded only by the
 * caller's RAM — standalone-complete on a host or an MCU alike.
 *
 * NO RECURSION (JPL Rule 1): both the parser (srmech_json_parse) and
 * the writer (srmech_json_write_ws) walk the tree with an EXPLICIT stack
 * bounded by SRMECH_JSON_MAX_DEPTH.
 *
 * Float caveat: DOUBLE values are written best-effort (%.17g, then
 * normalised to carry a '.'); byte-parity with Python's repr(float)
 * is NOT guaranteed. The parity GUARANTEE covers null / bool / int /
 * string / object / array trees only (MPR / genome manifests are
 * float-free). See JPL_AUDIT.md + CHANGELOG.
 *
 * License: MIT.
 */

#include "srmech.h"

#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Structural byte constants by ASCII code, so no brace/bracket char
 * literals ('{' '}' '[' ']') appear in function bodies (single-token
 * object-like macros; JPL Rule 8 clean). Keeping them out of the source
 * keeps brace-balance unambiguous for tooling and readers alike. */
#define JSON_LBRACE 0x7B  /* { */
#define JSON_RBRACE 0x7D  /* } */
#define JSON_LBRACK 0x5B  /* [ */
#define JSON_RBRACK 0x5D  /* ] */

/* ------------------------------------------------------------------ *
 * Char classifiers — Rule-5 EXEMPT (trivial classifiers, like the
 * TOML parser's toml_is_ws). Mirrored in test_jpl_audit.py +
 * documented in JPL_AUDIT.md.
 * ------------------------------------------------------------------ */

static int json_is_ws(char c)
{
    return (c == ' ' || c == '\t' || c == '\n' || c == '\r');
}

static int json_is_digit(char c)
{
    return (c >= '0' && c <= '9');
}

/* ------------------------------------------------------------------ *
 * Arena bump allocator over the caller's workspace.
 * ------------------------------------------------------------------ */

typedef struct {
    unsigned char *base;
    size_t         len;
    size_t         used;
} json_arena_t;

/* Bump-allocate `n` bytes, pointer-aligned. Returns NULL on overflow. */
static void *json_arena_alloc(json_arena_t *a, size_t n)
{
    assert(a != NULL);
    assert(a->base != NULL || a->len == 0);
    const size_t align = sizeof(void *);
    size_t pad = (align - (a->used % align)) % align;
    if (pad > a->len - a->used) {
        return NULL;
    }
    a->used += pad;
    if (n > a->len - a->used) {
        return NULL;
    }
    void *p = a->base + a->used;
    a->used += n;
    return p;
}

/* Allocate a fresh, zeroed value node from the arena. */
static srmech_json_value_t *json_arena_value(json_arena_t *a)
{
    assert(a != NULL);
    assert(a->len >= a->used);
    srmech_json_value_t *v =
        (srmech_json_value_t *)json_arena_alloc(a, sizeof(*v));
    if (v != NULL) {
        memset(v, 0, sizeof(*v));
    }
    return v;
}

/* ------------------------------------------------------------------ *
 * Parser state.
 * ------------------------------------------------------------------ */

typedef struct {
    const char  *src;
    size_t       len;
    size_t       pos;
    json_arena_t arena;
} json_parser_t;

static void json_skip_ws(json_parser_t *p)
{
    assert(p != NULL);
    assert(p->src != NULL || p->len == 0);
    while (p->pos < p->len && json_is_ws(p->src[p->pos])) {
        p->pos++;
    }
}

/* Decode one \uXXXX escape (4 hex digits at p->pos) into *out. Returns
 * SRMECH_OK or SRMECH_ERR_BAD_INPUT. Advances p->pos past the 4 hex. */
static srmech_status_t json_read_hex4(json_parser_t *p, uint32_t *out)
{
    assert(p != NULL);
    assert(out != NULL);
    if (p->len - p->pos < 4u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    uint32_t v = 0;
    for (int k = 0; k < 4; k++) {
        char c = p->src[p->pos + (size_t)k];
        uint32_t d;
        if (json_is_digit(c)) {
            d = (uint32_t)(c - '0');
        } else if (c >= 'a' && c <= 'f') {
            d = (uint32_t)(c - 'a' + 10);
        } else if (c >= 'A' && c <= 'F') {
            d = (uint32_t)(c - 'A' + 10);
        } else {
            return SRMECH_ERR_BAD_INPUT;
        }
        v = (v << 4) | d;
    }
    p->pos += 4u;
    *out = v;
    return SRMECH_OK;
}

/* Encode code point `cp` as UTF-8 into `dst` (arena bytes); write the
 * byte count to *n. dst must have room for 4 bytes. */
static srmech_status_t json_utf8_encode(uint32_t cp, char *dst, size_t *n)
{
    assert(dst != NULL);
    assert(n != NULL);
    if (cp < 0x80u) {
        dst[0] = (char)cp;
        *n = 1u;
    } else if (cp < 0x800u) {
        dst[0] = (char)(0xC0u | (cp >> 6));
        dst[1] = (char)(0x80u | (cp & 0x3Fu));
        *n = 2u;
    } else if (cp < 0x10000u) {
        dst[0] = (char)(0xE0u | (cp >> 12));
        dst[1] = (char)(0x80u | ((cp >> 6) & 0x3Fu));
        dst[2] = (char)(0x80u | (cp & 0x3Fu));
        *n = 3u;
    } else {
        dst[0] = (char)(0xF0u | (cp >> 18));
        dst[1] = (char)(0x80u | ((cp >> 12) & 0x3Fu));
        dst[2] = (char)(0x80u | ((cp >> 6) & 0x3Fu));
        dst[3] = (char)(0x80u | (cp & 0x3Fu));
        *n = 4u;
    }
    return SRMECH_OK;
}

/* Resolve a \uXXXX escape (optionally a surrogate pair) to a code point
 * and emit its UTF-8 bytes into the arena. p->pos is just past the 'u'. */
static srmech_status_t json_string_unicode(json_parser_t *p, char *out,
                                           size_t *out_n)
{
    assert(p != NULL);
    assert(out != NULL && out_n != NULL);
    uint32_t hi = 0;
    srmech_status_t st = json_read_hex4(p, &hi);
    if (st != SRMECH_OK) {
        return st;
    }
    if (hi >= 0xD800u && hi <= 0xDBFFu) {
        if (p->len - p->pos < 2u ||
            p->src[p->pos] != '\\' || p->src[p->pos + 1u] != 'u') {
            return SRMECH_ERR_BAD_INPUT;
        }
        p->pos += 2u;
        uint32_t lo = 0;
        st = json_read_hex4(p, &lo);
        if (st != SRMECH_OK) {
            return st;
        }
        if (lo < 0xDC00u || lo > 0xDFFFu) {
            return SRMECH_ERR_BAD_INPUT;
        }
        hi = 0x10000u + ((hi - 0xD800u) << 10) + (lo - 0xDC00u);
    } else if (hi >= 0xDC00u && hi <= 0xDFFFu) {
        return SRMECH_ERR_BAD_INPUT;  /* lone low surrogate */
    }
    return json_utf8_encode(hi, out, out_n);
}

/* Decode the body of one backslash escape (p->pos is past the '\'),
 * appending UTF-8 bytes into dst at *dlen. */
static srmech_status_t json_string_escape(json_parser_t *p, char *dst,
                                          size_t *dlen)
{
    assert(p != NULL);
    assert(dst != NULL && dlen != NULL);
    if (p->pos >= p->len) {
        return SRMECH_ERR_BAD_INPUT;
    }
    char e = p->src[p->pos++];
    char ch = 0;
    switch (e) {
        case '"':  ch = '"';  break;
        case '\\': ch = '\\'; break;
        case '/':  ch = '/';  break;
        case 'b':  ch = '\b'; break;
        case 'f':  ch = '\f'; break;
        case 'n':  ch = '\n'; break;
        case 'r':  ch = '\r'; break;
        case 't':  ch = '\t'; break;
        case 'u': {
            size_t un = 0;
            srmech_status_t st = json_string_unicode(p, dst + *dlen, &un);
            if (st != SRMECH_OK) {
                return st;
            }
            *dlen += un;
            return SRMECH_OK;
        }
        default: return SRMECH_ERR_BAD_INPUT;
    }
    dst[(*dlen)++] = ch;
    return SRMECH_OK;
}

/* Parse a JSON string (p->pos is at the opening '"') into the value
 * node `v` (decoded UTF-8 bytes allocated in the arena). */
static srmech_status_t json_parse_string(json_parser_t *p,
                                         srmech_json_value_t *v)
{
    assert(p != NULL);
    assert(v != NULL);
    p->pos++;  /* skip opening quote */
    /* Size the decode buffer to THIS string's raw span (scan to the closing
     * quote, skipping \-escapes), not the whole remaining input — else N
     * strings cost O(input^2) arena. Decoded length <= raw span (escapes only
     * shrink); the decode loop below produces identical bytes. */
    size_t scan = p->pos;
    while (scan < p->len) {
        char sc = p->src[scan];
        if (sc == '\\') { scan += 2u; continue; }
        if (sc == '"') { break; }
        scan++;
    }
    size_t cap = (scan <= p->len && scan >= p->pos) ? (scan - p->pos)
                                                    : (p->len - p->pos);
    char *buf = (char *)json_arena_alloc(&p->arena, cap + 1u);
    if (buf == NULL && cap + 1u != 0u) {
        return SRMECH_ERR_OVERFLOW;
    }
    size_t dlen = 0;
    while (p->pos < p->len) {
        char c = p->src[p->pos];
        if (c == '"') {
            p->pos++;
            v->type = SRMECH_JSON_STRING;
            v->u.str.ptr = buf;
            v->u.str.len = (uint32_t)dlen;
            return SRMECH_OK;
        }
        if (c == '\\') {
            p->pos++;
            srmech_status_t st = json_string_escape(p, buf, &dlen);
            if (st != SRMECH_OK) {
                return st;
            }
        } else if ((unsigned char)c < 0x20u) {
            return SRMECH_ERR_BAD_INPUT;  /* raw control in string */
        } else {
            buf[dlen++] = c;
            p->pos++;
        }
    }
    return SRMECH_ERR_BAD_INPUT;  /* unterminated string */
}

/* Parse a number (int → SRMECH_JSON_INT, fractional/exponent →
 * SRMECH_JSON_DOUBLE) at p->pos into `v`. */
static srmech_status_t json_parse_number(json_parser_t *p,
                                         srmech_json_value_t *v)
{
    assert(p != NULL);
    assert(v != NULL);
    size_t start = p->pos;
    bool is_double = false;
    if (p->pos < p->len && p->src[p->pos] == '-') {
        p->pos++;
    }
    while (p->pos < p->len) {
        char c = p->src[p->pos];
        if (json_is_digit(c)) {
            p->pos++;
        } else if (c == '.' || c == 'e' || c == 'E' || c == '+' || c == '-') {
            is_double = (c == '.' || c == 'e' || c == 'E') ? true : is_double;
            p->pos++;
        } else {
            break;
        }
    }
    size_t n = p->pos - start;
    if (n == 0u || n >= 63u) {
        return (n == 0u) ? SRMECH_ERR_BAD_INPUT : SRMECH_ERR_OVERFLOW;
    }
    char tmp[64];
    memcpy(tmp, p->src + start, n);
    tmp[n] = '\0';
    if (is_double) {
        v->type = SRMECH_JSON_DOUBLE;
        v->u.f = strtod(tmp, NULL);
    } else {
        v->type = SRMECH_JSON_INT;
        v->u.i = (int64_t)strtoll(tmp, NULL, 10);
    }
    return SRMECH_OK;
}

/* Match a bare literal (`true`/`false`/`null`) at p->pos. */
static srmech_status_t json_parse_literal(json_parser_t *p,
                                          srmech_json_value_t *v)
{
    assert(p != NULL);
    assert(v != NULL);
    size_t left = p->len - p->pos;
    if (left >= 4u && memcmp(p->src + p->pos, "true", 4) == 0) {
        p->pos += 4u;
        v->type = SRMECH_JSON_BOOL;
        v->u.b = 1;
        return SRMECH_OK;
    }
    if (left >= 5u && memcmp(p->src + p->pos, "false", 5) == 0) {
        p->pos += 5u;
        v->type = SRMECH_JSON_BOOL;
        v->u.b = 0;
        return SRMECH_OK;
    }
    if (left >= 4u && memcmp(p->src + p->pos, "null", 4) == 0) {
        p->pos += 4u;
        v->type = SRMECH_JSON_NULL;
        return SRMECH_OK;
    }
    return SRMECH_ERR_BAD_INPUT;
}

/* ------------------------------------------------------------------ *
 * Explicit-stack value parser (no recursion).
 *
 * Each frame holds a partially-built array OR object, accumulating its
 * children into a fixed-cap staging array. A scalar at depth 0 is
 * returned directly; a container pushes a frame and the loop continues.
 * ------------------------------------------------------------------ */

typedef struct {
    srmech_json_value_t  *node;       /* the container being built     */
    bool                  is_object;
    uint32_t              n;          /* children staged so far        */
    uint32_t              cap;        /* current staging capacity      */
    const char          **keys;       /* arena-backed [cap]; NULL=array */
    srmech_json_value_t **vals;       /* arena-backed [cap]            */
} json_frame_t;                       /* staging grows from the arena —
                                       * no compiled-in per-container cap */

/* Finalise a container frame: copy its staged children into arena-owned
 * arrays and attach them to the node. */
static srmech_status_t json_finish_frame(json_parser_t *p, json_frame_t *fr)
{
    assert(p != NULL);
    assert(fr != NULL && fr->node != NULL);
    size_t cnt = fr->n;
    if (fr->is_object) {
        const char **keys = (const char **)json_arena_alloc(
            &p->arena, (cnt ? cnt : 1u) * sizeof(char *));
        srmech_json_value_t **vals = (srmech_json_value_t **)json_arena_alloc(
            &p->arena, (cnt ? cnt : 1u) * sizeof(srmech_json_value_t *));
        if (keys == NULL || vals == NULL) {
            return SRMECH_ERR_OVERFLOW;
        }
        for (size_t k = 0; k < cnt; k++) {
            keys[k] = fr->keys[k];
            vals[k] = fr->vals[k];
        }
        fr->node->u.obj.keys = keys;
        fr->node->u.obj.vals = vals;
        fr->node->u.obj.n = (uint32_t)cnt;
    } else {
        srmech_json_value_t **items = (srmech_json_value_t **)json_arena_alloc(
            &p->arena, (cnt ? cnt : 1u) * sizeof(srmech_json_value_t *));
        if (items == NULL) {
            return SRMECH_ERR_OVERFLOW;
        }
        for (size_t k = 0; k < cnt; k++) {
            items[k] = fr->vals[k];
        }
        fr->node->u.arr.items = items;
        fr->node->u.arr.n = (uint32_t)cnt;
    }
    return SRMECH_OK;
}

/* Parse one scalar OR open one container at p->pos into `*out_node`.
 * `*opened` is set to 1 when a container ('{' or '[') was opened (the
 * caller pushes a frame), 0 for a finished scalar. */
static srmech_status_t json_parse_value_head(json_parser_t *p,
                                             srmech_json_value_t **out_node,
                                             int *opened)
{
    assert(p != NULL);
    assert(out_node != NULL && opened != NULL);
    *opened = 0;
    json_skip_ws(p);
    if (p->pos >= p->len) {
        return SRMECH_ERR_BAD_INPUT;
    }
    srmech_json_value_t *v = json_arena_value(&p->arena);
    if (v == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    char c = p->src[p->pos];
    *out_node = v;
    if (c == '"') {
        return json_parse_string(p, v);
    }
    if (c == '-' || json_is_digit(c)) {
        return json_parse_number(p, v);
    }
    if (c == (char)JSON_LBRACE) {
        p->pos++;
        v->type = SRMECH_JSON_OBJECT;
        *opened = 1;
        return SRMECH_OK;
    }
    if (c == (char)JSON_LBRACK) {
        p->pos++;
        v->type = SRMECH_JSON_ARRAY;
        *opened = 2;
        return SRMECH_OK;
    }
    return json_parse_literal(p, v);
}

/* Read one object key string at p->pos (must be a '"'-string) and store
 * its decoded bytes pointer + len into *key_ptr. */
static srmech_status_t json_read_object_key(json_parser_t *p,
                                            const char **key_ptr)
{
    assert(p != NULL);
    assert(key_ptr != NULL);
    json_skip_ws(p);
    if (p->pos >= p->len || p->src[p->pos] != '"') {
        return SRMECH_ERR_BAD_INPUT;
    }
    srmech_json_value_t kv;
    memset(&kv, 0, sizeof(kv));
    srmech_status_t st = json_parse_string(p, &kv);
    if (st != SRMECH_OK) {
        return st;
    }
    /* Store the key as a NUL-terminated arena copy so the value-tree key
     * array carries a plain `const char *` (the writer + object_get
     * re-measure via strlen). JSON keys are NUL-free, so strlen is exact. */
    char *kbuf = (char *)json_arena_alloc(&p->arena, kv.u.str.len + 1u);
    if (kbuf == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    memcpy(kbuf, kv.u.str.ptr, kv.u.str.len);
    kbuf[kv.u.str.len] = '\0';
    *key_ptr = kbuf;
    return SRMECH_OK;
}

/* Double a full container frame's staging arrays (arena-backed; the old
 * arrays are abandoned in the bump arena). The bound is the arena, not a
 * compiled-in child cap. SRMECH_ERR_OVERFLOW if the arena is exhausted or the
 * uint32 count saturates. */
static srmech_status_t json_frame_grow(json_parser_t *p, json_frame_t *fr)
{
    assert(p != NULL && fr != NULL);
    assert(fr->n == fr->cap);
    uint32_t ncap = (fr->cap < 0x80000000u) ? (fr->cap * 2u) : 0xFFFFFFFFu;
    if (ncap == fr->cap) { return SRMECH_ERR_OVERFLOW; }
    srmech_json_value_t **nv = (srmech_json_value_t **)json_arena_alloc(
        &p->arena, (size_t)ncap * sizeof(srmech_json_value_t *));
    if (nv == NULL) { return SRMECH_ERR_OVERFLOW; }
    for (uint32_t k = 0; k < fr->n; k++) { nv[k] = fr->vals[k]; }
    if (fr->is_object) {
        const char **nk = (const char **)json_arena_alloc(
            &p->arena, (size_t)ncap * sizeof(const char *));
        if (nk == NULL) { return SRMECH_ERR_OVERFLOW; }
        for (uint32_t k = 0; k < fr->n; k++) { nk[k] = fr->keys[k]; }
        fr->keys = nk;
    }
    fr->vals = nv;
    fr->cap = ncap;
    return SRMECH_OK;
}

/* Append a child (and optional key) into a container frame, growing the
 * arena-backed staging as needed (no compiled-in child cap). */
static srmech_status_t json_frame_push_child(json_parser_t *p,
                                             json_frame_t *fr,
                                             const char *key,
                                             srmech_json_value_t *child)
{
    assert(fr != NULL);
    assert(child != NULL);
    if (fr->n == fr->cap) {
        srmech_status_t gst = json_frame_grow(p, fr);
        if (gst != SRMECH_OK) { return gst; }
    }
    if (fr->is_object) {
        fr->keys[fr->n] = key;
    }
    fr->vals[fr->n] = child;
    fr->n++;
    return SRMECH_OK;
}

/* Expect a specific delimiter char after skipping whitespace; consume
 * it. Returns SRMECH_OK iff the next non-ws byte equals `want`. */
static srmech_status_t json_expect(json_parser_t *p, char want)
{
    assert(p != NULL);
    assert(want != '\0');
    json_skip_ws(p);
    if (p->pos >= p->len || p->src[p->pos] != want) {
        return SRMECH_ERR_BAD_INPUT;
    }
    p->pos++;
    return SRMECH_OK;
}

/* Drive the explicit-stack container loop once a head value is known.
 * Pushes/pops `stack` (depth-bounded) until the root is complete. */
static srmech_status_t json_parse_containers(json_parser_t *p, srmech_json_value_t *root, json_frame_t *stack, srmech_json_value_t **final_root);

srmech_status_t srmech_json_parse(const char *src, size_t len,
                                  void *ws, size_t ws_len,
                                  srmech_json_value_t **out)
{
    assert(out != NULL);
    assert(src != NULL || len == 0);
    if (out == NULL || (src == NULL && len != 0) ||
        (ws == NULL && ws_len != 0)) {
        return SRMECH_ERR_NULL_ARG;
    }
    json_parser_t p;
    p.src = src;
    p.len = len;
    p.pos = 0;
    p.arena.base = (unsigned char *)ws;
    p.arena.len = ws_len;
    p.arena.used = 0;

    srmech_json_value_t *root = NULL;
    int opened = 0;
    srmech_status_t st = json_parse_value_head(&p, &root, &opened);
    if (st != SRMECH_OK) {
        return st;
    }
    if (opened != 0) {
        /* Stack lives in the arena (large; off the call stack). */
        json_frame_t *stack = (json_frame_t *)json_arena_alloc(
            &p.arena, (size_t)SRMECH_JSON_MAX_DEPTH * sizeof(json_frame_t));
        if (stack == NULL) {
            return SRMECH_ERR_OVERFLOW;
        }
        st = json_parse_containers(&p, root, stack, &root);
        if (st != SRMECH_OK) {
            return st;
        }
    }
    json_skip_ws(&p);
    if (p.pos != p.len) {
        return SRMECH_ERR_BAD_INPUT;  /* trailing garbage */
    }
    *out = root;
    return SRMECH_OK;
}

/* Initialise a container frame for a freshly-opened '{' or '[' — carve an
 * initial arena-backed staging buffer (grown on demand by push_child). */
static srmech_status_t json_frame_open(json_parser_t *p, json_frame_t *fr,
                                       srmech_json_value_t *node)
{
    assert(p != NULL && fr != NULL);
    assert(node != NULL);
    fr->node = node;
    fr->is_object = (node->type == SRMECH_JSON_OBJECT);
    fr->n = 0;
    fr->cap = 8u;
    fr->keys = NULL;
    fr->vals = (srmech_json_value_t **)json_arena_alloc(
        &p->arena, (size_t)fr->cap * sizeof(srmech_json_value_t *));
    if (fr->is_object) {
        fr->keys = (const char **)json_arena_alloc(
            &p->arena, (size_t)fr->cap * sizeof(const char *));
    }
    if (fr->vals == NULL || (fr->is_object && fr->keys == NULL)) {
        return SRMECH_ERR_OVERFLOW;
    }
    return SRMECH_OK;
}

/* Read the next element into the top object frame: a "key": value pair
 * (or the closing '}'). Sets *closed = 1 on '}'. */
static srmech_status_t json_step_object(json_parser_t *p, json_frame_t *top,
                                        srmech_json_value_t **child,
                                        const char **key, int *closed,
                                        int *opened)
{
    assert(p != NULL && top != NULL);
    assert(child != NULL && key != NULL && closed != NULL && opened != NULL);
    *closed = 0;
    json_skip_ws(p);
    if (p->pos < p->len && p->src[p->pos] == (char)JSON_RBRACE) {
        p->pos++;
        *closed = 1;
        return SRMECH_OK;
    }
    if (top->n > 0) {
        srmech_status_t cst = json_expect(p, ',');
        if (cst != SRMECH_OK) {
            return cst;
        }
    }
    srmech_status_t st = json_read_object_key(p, key);
    if (st != SRMECH_OK) {
        return st;
    }
    st = json_expect(p, ':');
    if (st != SRMECH_OK) {
        return st;
    }
    return json_parse_value_head(p, child, opened);
}

/* Read the next element into the top array frame (a value, or the
 * closing ']'). Sets *closed = 1 on ']'. */
static srmech_status_t json_step_array(json_parser_t *p, json_frame_t *top,
                                       srmech_json_value_t **child,
                                       int *closed, int *opened)
{
    assert(p != NULL && top != NULL);
    assert(child != NULL && closed != NULL && opened != NULL);
    *closed = 0;
    json_skip_ws(p);
    if (p->pos < p->len && p->src[p->pos] == (char)JSON_RBRACK) {
        p->pos++;
        *closed = 1;
        return SRMECH_OK;
    }
    if (top->n > 0) {
        srmech_status_t cst = json_expect(p, ',');
        if (cst != SRMECH_OK) {
            return cst;
        }
    }
    return json_parse_value_head(p, child, opened);
}

static srmech_status_t json_parse_containers(json_parser_t *p,
                                             srmech_json_value_t *root,
                                             json_frame_t *stack,
                                             srmech_json_value_t **final_root)
{
    assert(p != NULL && root != NULL);
    assert(stack != NULL && final_root != NULL);
    int depth = 0;
    srmech_status_t ost = json_frame_open(p, &stack[0], root);
    if (ost != SRMECH_OK) { return ost; }
    depth = 1;
    for (size_t guard = 0; guard < p->len + 2u; guard++) {
        if (depth == 0) {
            break;
        }
        json_frame_t *top = &stack[depth - 1];
        srmech_json_value_t *child = NULL;
        const char *key = NULL;
        int closed = 0;
        int opened = 0;
        srmech_status_t st = top->is_object
            ? json_step_object(p, top, &child, &key, &closed, &opened)
            : json_step_array(p, top, &child, &closed, &opened);
        if (st != SRMECH_OK) {
            return st;
        }
        if (closed) {
            st = json_finish_frame(p, top);
            if (st != SRMECH_OK) {
                return st;
            }
            depth--;
            continue;
        }
        st = json_frame_push_child(p, top, key, child);
        if (st != SRMECH_OK) {
            return st;
        }
        if (opened != 0) {
            if (depth >= SRMECH_JSON_MAX_DEPTH) {
                return SRMECH_ERR_OVERFLOW;
            }
            st = json_frame_open(p, &stack[depth], child);
            if (st != SRMECH_OK) {
                return st;
            }
            depth++;
        }
    }
    if (depth != 0) {
        return SRMECH_ERR_BAD_INPUT;
    }
    *final_root = root;
    return SRMECH_OK;
}

/* ------------------------------------------------------------------ *
 * srmech_json_object_get
 * ------------------------------------------------------------------ */

const srmech_json_value_t *srmech_json_object_get(
    const srmech_json_value_t *obj, const char *key)
{
    assert(obj != NULL);
    assert(key != NULL);
    if (obj == NULL || key == NULL || obj->type != SRMECH_JSON_OBJECT) {
        return NULL;
    }
    size_t klen = strlen(key);
    for (uint32_t k = 0; k < obj->u.obj.n; k++) {
        const char *cand = obj->u.obj.keys[k];
        if (cand != NULL && strlen(cand) == klen &&
            memcmp(cand, key, klen) == 0) {
            return obj->u.obj.vals[k];
        }
    }
    return NULL;
}

/* ------------------------------------------------------------------ *
 * WRITER — byte-identical to json.dumps(sort_keys=True,
 *          ensure_ascii=False).
 *
 * A bounded output cursor: when buf == NULL we count only (size query).
 * ------------------------------------------------------------------ */

typedef struct {
    char   *buf;      /* NULL => size-query mode      */
    size_t  cap;      /* buffer capacity (bytes)      */
    size_t  pos;      /* bytes written / counted      */
    int     overflow; /* 1 once a write exceeded cap  */
} json_writer_t;

/* Append `n` raw bytes (or count them in query mode). Once a write
 * exceeds capacity the `overflow` flag latches and we STOP writing
 * (only `pos` keeps advancing as a true byte count) — so `pos` may
 * legitimately exceed `cap` and we must never compute `cap - pos`
 * (size_t underflow) or memcpy past the buffer end. */
static void json_put(json_writer_t *w, const char *bytes, size_t n)
{
    assert(w != NULL);
    assert(bytes != NULL || n == 0);
    if (w->buf != NULL && w->overflow == 0) {
        if (w->pos > w->cap || n > w->cap - w->pos) {
            w->overflow = 1;
        } else {
            memcpy(w->buf + w->pos, bytes, n);
        }
    }
    w->pos += n;
}

/* Append one byte. */
static void json_put_char(json_writer_t *w, char c)
{
    assert(w != NULL);
    assert(w->buf != NULL || w->cap == 0);
    json_put(w, &c, 1u);
}

/* Emit a JSON string literal (the ensure_ascii=False escaping rules:
 * escape only " \ \b \t \n \f \r and other controls < 0x20 as \u00XX;
 * everything >= 0x20 verbatim, incl. multibyte UTF-8). */
static void json_write_string(json_writer_t *w, const char *s, uint32_t len)
{
    assert(w != NULL);
    assert(s != NULL || len == 0);
    static const char hexd[] = "0123456789abcdef";
    json_put_char(w, '"');
    for (uint32_t k = 0; k < len; k++) {
        unsigned char c = (unsigned char)s[k];
        if (c == '"') {
            json_put(w, "\\\"", 2u);
        } else if (c == '\\') {
            json_put(w, "\\\\", 2u);
        } else if (c == '\b') {
            json_put(w, "\\b", 2u);
        } else if (c == '\t') {
            json_put(w, "\\t", 2u);
        } else if (c == '\n') {
            json_put(w, "\\n", 2u);
        } else if (c == '\f') {
            json_put(w, "\\f", 2u);
        } else if (c == '\r') {
            json_put(w, "\\r", 2u);
        } else if (c < 0x20u) {
            char esc[6];
            esc[0] = '\\'; esc[1] = 'u'; esc[2] = '0'; esc[3] = '0';
            esc[4] = hexd[(c >> 4) & 0xF];
            esc[5] = hexd[c & 0xF];
            json_put(w, esc, 6u);
        } else {
            json_put_char(w, (char)c);
        }
    }
    json_put_char(w, '"');
}

/* Format an int64 in decimal (no '.0', leading '-' for negatives). */
static void json_write_int(json_writer_t *w, int64_t v)
{
    assert(w != NULL);
    assert(w->buf != NULL || w->cap == 0);
    char tmp[24];
    int n = snprintf(tmp, sizeof(tmp), "%lld", (long long)v);
    if (n < 0) {
        return;
    }
    json_put(w, tmp, (size_t)n);
}

/* Format a double best-effort (NOT byte-parity with Python repr;
 * manifests are float-free — see header). Ensures a '.'/'e' is present
 * so the value reads back as a float. */
static void json_write_double(json_writer_t *w, double v)
{
    assert(w != NULL);
    assert(w->buf != NULL || w->cap == 0);
    char tmp[40];
    int n = snprintf(tmp, sizeof(tmp), "%.17g", v);
    if (n < 0) {
        return;
    }
    bool has_dot = false;
    for (int k = 0; k < n; k++) {
        if (tmp[k] == '.' || tmp[k] == 'e' || tmp[k] == 'E' ||
            tmp[k] == 'n' || tmp[k] == 'i') {
            has_dot = true;
        }
    }
    json_put(w, tmp, (size_t)n);
    if (!has_dot && n < (int)sizeof(tmp) - 2) {
        json_put(w, ".0", 2u);
    }
}

/* ------------------------------------------------------------------ *
 * Key-sorting for objects (bytewise UTF-8 order == Python sorted()).
 *
 * We never permute the value tree; instead we compute a sorted INDEX
 * permutation into a fixed-cap stack array and emit pairs in that
 * order. Insertion sort (n is the object width; `order` is the
 * caller-arena pool slot for this frame — bounded by the arena).
 * ------------------------------------------------------------------ */

/* Bytewise compare two NUL-free keys (len-tagged). Returns <0/0/>0.
 * Shorter key sorts first on a common prefix — matches Python str
 * ordering for valid UTF-8 (code-point order == byte order). */
static int json_key_cmp(const char *a, const char *b)
{
    assert(a != NULL);
    assert(b != NULL);
    size_t la = strlen(a);
    size_t lb = strlen(b);
    size_t m = (la < lb) ? la : lb;
    int c = (m == 0) ? 0 : memcmp(a, b, m);
    if (c != 0) {
        return c;
    }
    return (la < lb) ? -1 : (la > lb) ? 1 : 0;
}

/* Build a sorted-index permutation `order[0..n)` of an object's keys. */
static void json_sort_object_keys(const srmech_json_value_t *obj,
                                  uint32_t *order)
{
    assert(obj != NULL);
    uint32_t n = obj->u.obj.n;
    /* order may be NULL only when every object in the tree is empty (the
     * arena pool has zero width); the loops below never deref it then. */
    assert(order != NULL || n == 0u);
    for (uint32_t k = 0; k < n; k++) {
        order[k] = k;
    }
    for (uint32_t i = 1; i < n; i++) {
        uint32_t cur = order[i];
        const char *ck = obj->u.obj.keys[cur];
        uint32_t j = i;
        while (j > 0 &&
               json_key_cmp(obj->u.obj.keys[order[j - 1]], ck) > 0) {
            order[j] = order[j - 1];
            j--;
        }
        order[j] = cur;
    }
}

/* ------------------------------------------------------------------ *
 * Explicit-stack tree emitter (no recursion).
 *
 * Each frame tracks a container and a cursor over its children in the
 * correct emission order (sorted for objects). We emit separators
 * (", " between children, ": " between key/value) inline.
 * ------------------------------------------------------------------ */

typedef struct {
    const srmech_json_value_t *node;
    bool                       is_object;
    uint32_t                   idx;    /* next child to emit */
    uint32_t                  *order;  /* sorted-key index permutation —
                                        * carved from the caller arena, so an
                                        * object is bounded only by the arena
                                        * (no compiled-in object-width cap). */
} json_emit_frame_t;

/* Emit a scalar (null/bool/int/double/string) directly. */
static void json_emit_scalar(json_writer_t *w, const srmech_json_value_t *v)
{
    assert(w != NULL);
    assert(v != NULL);
    switch (v->type) {
        case SRMECH_JSON_NULL:   json_put(w, "null", 4u);  break;
        case SRMECH_JSON_BOOL:
            json_put(w, v->u.b ? "true" : "false", v->u.b ? 4u : 5u);
            break;
        case SRMECH_JSON_INT:    json_write_int(w, v->u.i);    break;
        case SRMECH_JSON_DOUBLE: json_write_double(w, v->u.f); break;
        case SRMECH_JSON_STRING:
            json_write_string(w, v->u.str.ptr, v->u.str.len);
            break;
        default: break;  /* containers handled by the frame loop */
    }
}

/* Open a container frame (write '{'/'[' and prime the cursor). */
static void json_emit_open(json_writer_t *w, json_emit_frame_t *fr,
                           const srmech_json_value_t *v)
{
    assert(w != NULL);
    assert(fr != NULL && v != NULL);
    fr->node = v;
    fr->is_object = (v->type == SRMECH_JSON_OBJECT);
    fr->idx = 0;
    if (fr->is_object) {
        json_sort_object_keys(v, fr->order);
        json_put_char(w, (char)JSON_LBRACE);
    } else {
        json_put_char(w, (char)JSON_LBRACK);
    }
}

/* Advance an open container frame by one child. Returns the child to
 * descend into (a container), or NULL if the child was a scalar /
 * the container just closed (*closed set accordingly). */
static const srmech_json_value_t *json_emit_step(json_writer_t *w,
                                                 json_emit_frame_t *fr,
                                                 int *closed)
{
    assert(w != NULL);
    assert(fr != NULL && closed != NULL);
    *closed = 0;
    uint32_t n = fr->is_object ? fr->node->u.obj.n : fr->node->u.arr.n;
    if (fr->idx >= n) {
        json_put_char(w, fr->is_object ? (char)JSON_RBRACE : (char)JSON_RBRACK);
        *closed = 1;
        return NULL;
    }
    if (fr->idx > 0) {
        json_put(w, ", ", 2u);
    }
    const srmech_json_value_t *child;
    if (fr->is_object) {
        uint32_t oi = fr->order[fr->idx];
        const char *key = fr->node->u.obj.keys[oi];
        json_write_string(w, key, (uint32_t)strlen(key));
        json_put(w, ": ", 2u);
        child = fr->node->u.obj.vals[oi];
    } else {
        child = fr->node->u.arr.items[fr->idx];
    }
    fr->idx++;
    if (child->type == SRMECH_JSON_OBJECT ||
        child->type == SRMECH_JSON_ARRAY) {
        return child;
    }
    json_emit_scalar(w, child);
    return NULL;
}

/* Walk the tree with an explicit depth-bounded stack of `max_depth` emit
 * frames (the stack is carved from the caller arena — `max_depth` matches
 * its length, so the OVERFLOW guard is exactly the allocation bound). */
static srmech_status_t json_emit_tree(json_writer_t *w,
                                      const srmech_json_value_t *root,
                                      json_emit_frame_t *stack, int max_depth)
{
    assert(w != NULL && root != NULL);
    assert(stack != NULL && max_depth > 0);
    if (root->type != SRMECH_JSON_OBJECT && root->type != SRMECH_JSON_ARRAY) {
        json_emit_scalar(w, root);
        return SRMECH_OK;
    }
    int depth = 0;
    json_emit_open(w, &stack[0], root);
    depth = 1;
    while (depth > 0) {
        int closed = 0;
        const srmech_json_value_t *child =
            json_emit_step(w, &stack[depth - 1], &closed);
        if (closed) {
            depth--;
        } else if (child != NULL) {
            if (depth >= max_depth) {
                return SRMECH_ERR_OVERFLOW;
            }
            json_emit_open(w, &stack[depth], child);
            depth++;
        }
    }
    return SRMECH_OK;
}

/* Emit-scratch dimensions: the widest object child-count (the order-array
 * width W) and the deepest container nesting (D). Walks the tree with a
 * MAX_DEPTH-bounded cursor stack (a genuine recursion-depth guard, NOT a
 * problem-size cap — objects/arrays of any width are traversed). A scalar
 * root yields W = 0, D = 0. Objects below MAX_DEPTH are not measured (the
 * writer OVERFLOWs there regardless), so the (W, D) pair sizes exactly the
 * arena the writer can actually use. */
typedef struct {
    const srmech_json_value_t *node;
    bool                       is_object;
    uint32_t                   idx;
} json_dim_frame_t;

static void json_emit_dims(const srmech_json_value_t *v,
                           uint32_t *max_w, int *max_d)
{
    assert(v != NULL);
    assert(max_w != NULL && max_d != NULL);
    *max_w = 0;
    *max_d = 0;
    if (v->type != SRMECH_JSON_OBJECT && v->type != SRMECH_JSON_ARRAY) {
        return;
    }
    json_dim_frame_t stack[SRMECH_JSON_MAX_DEPTH];
    stack[0].node = v;
    stack[0].is_object = (v->type == SRMECH_JSON_OBJECT);
    stack[0].idx = 0;
    if (stack[0].is_object) { *max_w = v->u.obj.n; }
    int depth = 1;
    *max_d = 1;
    while (depth > 0) {
        json_dim_frame_t *fr = &stack[depth - 1];
        uint32_t n = fr->is_object ? fr->node->u.obj.n : fr->node->u.arr.n;
        if (fr->idx >= n) { depth--; continue; }
        const srmech_json_value_t *child = fr->is_object
            ? fr->node->u.obj.vals[fr->idx] : fr->node->u.arr.items[fr->idx];
        fr->idx++;
        if ((child->type == SRMECH_JSON_OBJECT ||
             child->type == SRMECH_JSON_ARRAY) && depth < SRMECH_JSON_MAX_DEPTH) {
            bool cobj = (child->type == SRMECH_JSON_OBJECT);
            if (cobj && child->u.obj.n > *max_w) { *max_w = child->u.obj.n; }
            stack[depth].node = child;
            stack[depth].is_object = cobj;
            stack[depth].idx = 0;
            depth++;
            if (depth > *max_d) { *max_d = depth; }
        }
    }
}

/* Bytes of caller workspace srmech_json_write_ws needs for `v`: the emit
 * frame stack (D frames) plus the shared key-order pool (D * W uint32),
 * each pointer-aligned by the arena. No object-width cap — sized to the
 * actual tree. */
size_t srmech_json_write_arena_bytes(const srmech_json_value_t *v)
{
    assert(v != NULL);
    if (v == NULL) { return 0u; }
    uint32_t w = 0;
    int d = 0;
    json_emit_dims(v, &w, &d);
    if (d < 1) { d = 1; }
    assert(d >= 1 && d <= SRMECH_JSON_MAX_DEPTH);
    size_t frames = (size_t)d * sizeof(json_emit_frame_t);
    size_t pool = (size_t)d * (size_t)w * sizeof(uint32_t);
    return frames + pool + 2u * sizeof(void *);  /* + 2 alignment pads */
}

/* Serialise `v` to `buf` using caller-supplied scratch `ws` (size it with
 * srmech_json_write_arena_bytes). The key-order permutation arrays are carved
 * from `ws`, so an object is bounded only by the arena — there is no
 * compiled-in object-width cap. Byte-identical to json.dumps(sort_keys=True,
 * ensure_ascii=False) for the float-free MPR/genome tree. */
srmech_status_t srmech_json_write_ws(const srmech_json_value_t *v,
                                     char *buf, size_t buf_len,
                                     size_t *out_len,
                                     void *ws, size_t ws_len)
{
    assert(v != NULL);
    assert(out_len != NULL);
    if (v == NULL || out_len == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    uint32_t width = 0;
    int depth = 0;
    json_emit_dims(v, &width, &depth);
    if (depth < 1) { depth = 1; }
    json_arena_t a;
    a.base = (unsigned char *)ws;
    a.len = ws_len;
    a.used = 0;
    json_emit_frame_t *stack = (json_emit_frame_t *)json_arena_alloc(
        &a, (size_t)depth * sizeof(json_emit_frame_t));
    if (stack == NULL) {
        return SRMECH_ERR_BAD_INPUT;  /* arena too small for the tree */
    }
    if (width > 0u) {
        uint32_t *pool = (uint32_t *)json_arena_alloc(
            &a, (size_t)depth * (size_t)width * sizeof(uint32_t));
        if (pool == NULL) {
            return SRMECH_ERR_BAD_INPUT;
        }
        for (int k = 0; k < depth; k++) {
            stack[k].order = pool + (size_t)k * (size_t)width;
        }
    } else {
        for (int k = 0; k < depth; k++) { stack[k].order = NULL; }
    }
    json_writer_t w;
    w.buf = buf;
    w.cap = buf_len;
    w.pos = 0;
    w.overflow = 0;
    srmech_status_t st = json_emit_tree(&w, v, stack, depth);
    if (st != SRMECH_OK) {
        return st;
    }
    *out_len = w.pos;
    if (buf != NULL && w.overflow) {
        return SRMECH_ERR_OVERFLOW;
    }
    return SRMECH_OK;
}

/* ------------------------------------------------------------------ *
 * BUILDER — construct a value tree in the same arena convention.
 * ------------------------------------------------------------------ */

srmech_status_t srmech_json_builder_init(srmech_json_builder_t *b,
                                         void *ws, size_t ws_len)
{
    assert(b != NULL);
    assert(ws != NULL || ws_len == 0);
    if (b == NULL || (ws == NULL && ws_len != 0)) {
        return SRMECH_ERR_NULL_ARG;
    }
    b->base = (unsigned char *)ws;
    b->len = ws_len;
    b->used = 0;
    b->failed = 0;
    return SRMECH_OK;
}

/* Allocate + zero a node from the builder's arena (latching `failed`). */
static srmech_json_value_t *json_builder_node(srmech_json_builder_t *b)
{
    assert(b != NULL);
    assert(b->len >= b->used);
    json_arena_t a;
    a.base = b->base;
    a.len = b->len;
    a.used = b->used;
    srmech_json_value_t *v = json_arena_value(&a);
    b->used = a.used;
    if (v == NULL) {
        b->failed = 1;
    }
    return v;
}

srmech_json_value_t *srmech_json_new_null(srmech_json_builder_t *b)
{
    assert(b != NULL);
    assert(b->base != NULL || b->len == 0);
    srmech_json_value_t *v = json_builder_node(b);
    if (v != NULL) {
        v->type = SRMECH_JSON_NULL;
    }
    return v;
}

srmech_json_value_t *srmech_json_new_bool(srmech_json_builder_t *b, int truth)
{
    assert(b != NULL);
    assert(b->len >= b->used);
    srmech_json_value_t *v = json_builder_node(b);
    if (v != NULL) {
        v->type = SRMECH_JSON_BOOL;
        v->u.b = truth ? 1 : 0;
    }
    return v;
}

srmech_json_value_t *srmech_json_new_int(srmech_json_builder_t *b, int64_t i)
{
    assert(b != NULL);
    assert(b->len >= b->used);
    srmech_json_value_t *v = json_builder_node(b);
    if (v != NULL) {
        v->type = SRMECH_JSON_INT;
        v->u.i = i;
    }
    return v;
}

srmech_json_value_t *srmech_json_new_double(srmech_json_builder_t *b, double f)
{
    assert(b != NULL);
    assert(b->len >= b->used);
    srmech_json_value_t *v = json_builder_node(b);
    if (v != NULL) {
        v->type = SRMECH_JSON_DOUBLE;
        v->u.f = f;
    }
    return v;
}

srmech_json_value_t *srmech_json_new_string(srmech_json_builder_t *b,
                                            const char *ptr, uint32_t len)
{
    assert(b != NULL);
    assert(ptr != NULL || len == 0);
    srmech_json_value_t *v = json_builder_node(b);
    if (v != NULL) {
        v->type = SRMECH_JSON_STRING;
        v->u.str.ptr = ptr;   /* not copied — caller keeps bytes alive */
        v->u.str.len = len;
    }
    return v;
}

/* Copy a child-pointer array into the builder's arena. */
static srmech_json_value_t **json_builder_copy_ptrs(
    srmech_json_builder_t *b, srmech_json_value_t **src, uint32_t n)
{
    assert(b != NULL);
    assert(src != NULL || n == 0);
    json_arena_t a;
    a.base = b->base;
    a.len = b->len;
    a.used = b->used;
    srmech_json_value_t **dst = (srmech_json_value_t **)json_arena_alloc(
        &a, (n ? n : 1u) * sizeof(srmech_json_value_t *));
    b->used = a.used;
    if (dst == NULL) {
        b->failed = 1;
        return NULL;
    }
    for (uint32_t k = 0; k < n; k++) {
        dst[k] = src[k];
    }
    return dst;
}

srmech_json_value_t *srmech_json_new_array(srmech_json_builder_t *b,
                                           srmech_json_value_t **items,
                                           uint32_t n)
{
    assert(b != NULL);
    assert(items != NULL || n == 0);
    /* No compiled-in child cap: the item-pointer copy is carved from the
     * caller arena (json_builder_copy_ptrs), so an array is bounded only by
     * the arena. (Objects stay capped — the writer's key-sort is fixed-size.) */
    srmech_json_value_t *v = json_builder_node(b);
    srmech_json_value_t **copy = json_builder_copy_ptrs(b, items, n);
    if (v == NULL || copy == NULL) {
        return NULL;
    }
    v->type = SRMECH_JSON_ARRAY;
    v->u.arr.items = copy;
    v->u.arr.n = n;
    return v;
}

/* Copy a key-pointer array (const char *) into the builder's arena. */
static const char **json_builder_copy_keys(srmech_json_builder_t *b,
                                           const char **src, uint32_t n)
{
    assert(b != NULL);
    assert(src != NULL || n == 0);
    json_arena_t a;
    a.base = b->base;
    a.len = b->len;
    a.used = b->used;
    const char **dst = (const char **)json_arena_alloc(
        &a, (n ? n : 1u) * sizeof(const char *));
    b->used = a.used;
    if (dst == NULL) {
        b->failed = 1;
        return NULL;
    }
    for (uint32_t k = 0; k < n; k++) {
        dst[k] = src[k];
    }
    return dst;
}

srmech_json_value_t *srmech_json_new_object(srmech_json_builder_t *b,
                                            const char **keys,
                                            srmech_json_value_t **vals,
                                            uint32_t n)
{
    assert(b != NULL);
    assert((keys != NULL && vals != NULL) || n == 0);
    /* No compiled-in child cap: the key/value-pointer copies are carved from
     * the caller arena (json_builder_copy_keys/_ptrs) and the writer's key
     * sort scratch is caller-arena-backed too, so an object is bounded only
     * by the arena. */
    srmech_json_value_t *v = json_builder_node(b);
    const char **kcopy = json_builder_copy_keys(b, keys, n);
    srmech_json_value_t **vcopy = json_builder_copy_ptrs(b, vals, n);
    if (v == NULL || kcopy == NULL || vcopy == NULL) {
        return NULL;
    }
    v->type = SRMECH_JSON_OBJECT;
    v->u.obj.keys = kcopy;
    v->u.obj.vals = vcopy;
    v->u.obj.n = n;
    return v;
}
