/*
 * srmech_tool_schema.c — accessors + canonical JSON serialiser over the
 * generated `srmech_tool_registry` const table (0.9.0rc184; the C
 * MCP-server FOUNDATION GATE).
 *
 * The table + `srmech_tool_registry_len` + `srmech_tool_schema_version_str`
 * are DEFINED in the generated translation unit `srmech_tool_registry.c`
 * (regenerate with c/tools/gen_tool_registry.py). This file provides the
 * public accessors declared in srmech.h and the canonical serialiser
 * `srmech_tool_schema_to_json`, whose output is BYTE-IDENTICAL to CPython
 *   json.dumps(get_tool_schema().to_jsonable(),
 *              sort_keys=True, separators=(",", ":"))
 * — the DEFAULT ensure_ascii=True form (non-ASCII escaped \uXXXX, astral
 * code points as a UTF-16 surrogate pair), sorted keys, compact
 * separators. That byte-identity IS the hash-ratchet contract:
 *   srmech_sha256_hex(this) == the Python tool_schema_sha256.
 *
 * JPL-clean: no malloc (the caller supplies the output buffer; a NULL
 * buffer is a size-query), no goto, no recursion (the tree is a fixed
 * two-level walk), no libm, no abs. ABI-additive (SRMECH_ABI_VERSION
 * stays 4).
 *
 * License: MIT.
 */

#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

#include "srmech.h"

/* Defined in the generated srmech_tool_registry.c. */
extern const srmech_tool_entry_t srmech_tool_registry_table[];
extern const size_t srmech_tool_registry_len;
extern const char srmech_tool_schema_version_str[];

/* ------------------------------------------------------------------
 * Accessors
 * ------------------------------------------------------------------ */

size_t srmech_tool_registry_count(void)
{
    assert(srmech_tool_registry_table != NULL);
    assert(srmech_tool_registry_len > 0u);
    return srmech_tool_registry_len;
}

const srmech_tool_entry_t *srmech_tool_registry_get(size_t index)
{
    assert(srmech_tool_registry_table != NULL);
    assert(srmech_tool_registry_len > 0u);
    if (index >= srmech_tool_registry_len) {
        return NULL;
    }
    return &srmech_tool_registry_table[index];
}

const srmech_tool_entry_t *srmech_tool_registry_find(const char *name)
{
    size_t i;
    assert(name != NULL);
    assert(srmech_tool_registry_table != NULL);
    for (i = 0u; i < srmech_tool_registry_len; i++) {
        if (strcmp(srmech_tool_registry_table[i].name, name) == 0) {
            return &srmech_tool_registry_table[i];
        }
    }
    return NULL;
}

/* ------------------------------------------------------------------
 * Canonical JSON emitter (bounded, no allocation)
 * ------------------------------------------------------------------ */

typedef struct {
    char  *buf;       /* NULL for a size-query                        */
    size_t cap;       /* capacity of buf (bytes), 0 when buf == NULL  */
    size_t used;      /* bytes produced so far                        */
    int    overflow;  /* set once a write would exceed cap            */
} ts_emit_t;

/* Append `n` raw bytes; in size-query / overflow modes only `used`
 * advances. On overflow the byte count stops growing (the caller
 * returns SRMECH_ERR_OVERFLOW and ignores `used`). */
static void ts_raw(ts_emit_t *e, const char *s, size_t n)
{
    size_t i;
    assert(e != NULL);
    assert(s != NULL || n == 0u);
    if (e->buf != NULL) {
        if (e->overflow || e->used + n > e->cap) {
            e->overflow = 1;
            return;
        }
        for (i = 0u; i < n; i++) {
            e->buf[e->used + i] = s[i];
        }
    }
    e->used += n;
}

/* Append a NUL-terminated literal / pre-canonical fragment. */
static void ts_cstr(ts_emit_t *e, const char *s)
{
    assert(e != NULL);
    assert(s != NULL);
    ts_raw(e, s, strlen(s));
}

/* Decode one UTF-8 code point at p[*i], advancing *i past it. The input
 * is trusted, complete, valid UTF-8 (Python str -> utf-8 encode). */
static uint32_t ts_utf8_next(const unsigned char *p, size_t *i)
{
    uint32_t b0;
    size_t j;
    assert(p != NULL);
    assert(i != NULL);
    j = *i;
    b0 = p[j];
    if (b0 < 0x80u) {
        *i = j + 1u;
        return b0;
    }
    if ((b0 & 0xE0u) == 0xC0u) {
        *i = j + 2u;
        return ((b0 & 0x1Fu) << 6) | (p[j + 1u] & 0x3Fu);
    }
    if ((b0 & 0xF0u) == 0xE0u) {
        *i = j + 3u;
        return ((b0 & 0x0Fu) << 12) | ((p[j + 1u] & 0x3Fu) << 6)
               | (p[j + 2u] & 0x3Fu);
    }
    *i = j + 4u;
    return ((b0 & 0x07u) << 18) | ((p[j + 1u] & 0x3Fu) << 12)
           | ((p[j + 2u] & 0x3Fu) << 6) | (p[j + 3u] & 0x3Fu);
}

/* Emit \uXXXX (lowercase hex) for a single BMP code unit. */
static void ts_u_escape(ts_emit_t *e, uint32_t cu)
{
    static const char hexd[] = "0123456789abcdef";
    char b[6];
    assert(e != NULL);
    assert(cu <= 0xFFFFu);
    b[0] = '\\';
    b[1] = 'u';
    b[2] = hexd[(cu >> 12) & 0xFu];
    b[3] = hexd[(cu >> 8) & 0xFu];
    b[4] = hexd[(cu >> 4) & 0xFu];
    b[5] = hexd[cu & 0xFu];
    ts_raw(e, b, 6u);
}

/* Emit `s` as a JSON string (with surrounding quotes), byte-identical to
 * CPython json.dumps default (ensure_ascii=True) string encoding. */
static void ts_json_string(ts_emit_t *e, const char *s)
{
    const unsigned char *p = (const unsigned char *)s;
    size_t i = 0u;
    assert(e != NULL);
    assert(s != NULL);
    ts_raw(e, "\"", 1u);
    while (p[i] != 0u) {
        uint32_t cp = ts_utf8_next(p, &i);
        if (cp == 0x22u) {
            ts_raw(e, "\\\"", 2u);
        } else if (cp == 0x5Cu) {
            ts_raw(e, "\\\\", 2u);
        } else if (cp == 0x08u) {
            ts_raw(e, "\\b", 2u);
        } else if (cp == 0x09u) {
            ts_raw(e, "\\t", 2u);
        } else if (cp == 0x0Au) {
            ts_raw(e, "\\n", 2u);
        } else if (cp == 0x0Cu) {
            ts_raw(e, "\\f", 2u);
        } else if (cp == 0x0Du) {
            ts_raw(e, "\\r", 2u);
        } else if (cp < 0x20u) {
            ts_u_escape(e, cp);
        } else if (cp <= 0x7Eu) {
            char c = (char)cp;
            ts_raw(e, &c, 1u);
        } else if (cp <= 0xFFFFu) {
            ts_u_escape(e, cp);
        } else {
            uint32_t v = cp - 0x10000u;
            ts_u_escape(e, 0xD800u + (v >> 10));
            ts_u_escape(e, 0xDC00u + (v & 0x3FFu));
        }
    }
    ts_raw(e, "\"", 1u);
}

/* Emit one parameter object: sorted keys name/required/summary/type. */
static void ts_emit_param(ts_emit_t *e, const srmech_tool_param_t *pm)
{
    assert(e != NULL);
    assert(pm != NULL);
    ts_cstr(e, "{\"name\":");
    ts_json_string(e, pm->name);
    ts_cstr(e, ",\"required\":");
    ts_cstr(e, pm->required ? "true" : "false");
    ts_cstr(e, ",\"summary\":");
    ts_json_string(e, pm->summary);
    ts_cstr(e, ",\"type\":");
    ts_json_string(e, pm->type);
    ts_cstr(e, "}");
}

/* Emit one entry object: keys in sorted order, optional keys omitted
 * when absent (mirroring ToolEntry.to_jsonable). */
static void ts_emit_entry(ts_emit_t *e, const srmech_tool_entry_t *t)
{
    uint32_t k;
    assert(e != NULL);
    assert(t != NULL);
    ts_cstr(e, "{\"category\":");
    ts_json_string(e, t->category);
    if (t->example_json != NULL) {
        ts_cstr(e, ",\"example\":");
        ts_cstr(e, t->example_json);
    }
    ts_cstr(e, ",\"mcp_callable\":");
    ts_cstr(e, t->mcp_callable ? "true" : "false");
    if (t->mcp_unavailable_reason != NULL) {
        ts_cstr(e, ",\"mcp_unavailable_reason\":");
        ts_json_string(e, t->mcp_unavailable_reason);
    }
    ts_cstr(e, ",\"name\":");
    ts_json_string(e, t->name);
    ts_cstr(e, ",\"owner\":");
    ts_json_string(e, t->owner);
    ts_cstr(e, ",\"parameters\":[");
    for (k = 0u; k < t->param_count; k++) {
        if (k > 0u) {
            ts_cstr(e, ",");
        }
        ts_emit_param(e, &t->params[k]);
    }
    ts_cstr(e, "]");
    if (t->returns_type != NULL) {
        ts_cstr(e, ",\"returns\":{\"shape\":");
        ts_json_string(e, t->returns_shape);
        ts_cstr(e, ",\"type\":");
        ts_json_string(e, t->returns_type);
        ts_cstr(e, "}");
    }
    if (t->smoke_json != NULL) {
        ts_cstr(e, ",\"smoke_test_hint\":");
        ts_cstr(e, t->smoke_json);
    }
    ts_cstr(e, ",\"summary\":");
    ts_json_string(e, t->summary);
    ts_cstr(e, "}");
}

srmech_status_t srmech_tool_schema_to_json(char *buf, size_t buf_len,
                                           size_t *out_len)
{
    ts_emit_t e;
    size_t n, i;
    if (out_len == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(buf != NULL || buf_len == 0u);
    e.buf = buf;
    e.cap = buf_len;
    e.used = 0u;
    e.overflow = 0;
    ts_cstr(&e, "{\"srmech_version\":");
    ts_json_string(&e, srmech_version());
    ts_cstr(&e, ",\"tool_schema_version\":");
    ts_json_string(&e, srmech_tool_schema_version_str);
    ts_cstr(&e, ",\"tools\":[");
    n = srmech_tool_registry_count();
    assert(n > 0u);
    for (i = 0u; i < n; i++) {
        if (i > 0u) {
            ts_cstr(&e, ",");
        }
        ts_emit_entry(&e, srmech_tool_registry_get(i));
    }
    ts_cstr(&e, "]}");
    *out_len = e.used;
    if (e.overflow) {
        return SRMECH_ERR_OVERFLOW;
    }
    return SRMECH_OK;
}
