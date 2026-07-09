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

/* Emit the ESCAPED BODY of `s` (no surrounding quotes), byte-identical to
 * the inside of CPython json.dumps default (ensure_ascii=True) string
 * encoding. Split out so a multi-piece string (e.g. the rc185 MCP-def
 * description joined with " — ") can be assembled inline without a
 * scratch buffer. */
static void ts_json_body(ts_emit_t *e, const char *s)
{
    const unsigned char *p = (const unsigned char *)s;
    size_t i = 0u;
    assert(e != NULL);
    assert(s != NULL);
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
}

/* Emit `s` as a JSON string (with surrounding quotes), byte-identical to
 * CPython json.dumps default (ensure_ascii=True) string encoding. */
static void ts_json_string(ts_emit_t *e, const char *s)
{
    assert(e != NULL);
    assert(s != NULL);
    ts_raw(e, "\"", 1u);
    ts_json_body(e, s);
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

/* The whole registry as canonical (sorted-key) JSON — the shared body of
 * srmech_tool_schema_to_json / srmech_get_tool_schema / srmech_tool_schema_view.
 * The srmech version field is injected from srmech_version() at call time. */
static void ts_emit_schema_sorted(ts_emit_t *e)
{
    size_t n, i;
    assert(e != NULL);
    ts_cstr(e, "{\"srmech_version\":");
    ts_json_string(e, srmech_version());
    ts_cstr(e, ",\"tool_schema_version\":");
    ts_json_string(e, srmech_tool_schema_version_str);
    ts_cstr(e, ",\"tools\":[");
    n = srmech_tool_registry_count();
    assert(n > 0u);
    for (i = 0u; i < n; i++) {
        if (i > 0u) {
            ts_cstr(e, ",");
        }
        ts_emit_entry(e, srmech_tool_registry_get(i));
    }
    ts_cstr(e, "]}");
}

/* Common two-pass epilogue: publish the byte count + overflow verdict. */
static srmech_status_t ts_finish(const ts_emit_t *e, size_t *out_len)
{
    assert(e != NULL);
    assert(out_len != NULL);
    *out_len = e->used;
    return e->overflow ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

srmech_status_t srmech_tool_schema_to_json(char *buf, size_t buf_len,
                                           size_t *out_len)
{
    ts_emit_t e;
    if (out_len == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(buf != NULL || buf_len == 0u);
    assert(out_len != NULL);  /* guaranteed by the early NULL-arg return */
    e.buf = buf;
    e.cap = buf_len;
    e.used = 0u;
    e.overflow = 0;
    ts_emit_schema_sorted(&e);
    return ts_finish(&e, out_len);
}

/* ==================================================================
 * rc185 — the tool-schema PROJECTION ops (HOST-GLUE tier).
 *
 * srmech_get_tool_schema / srmech_tool_schema_view emit the SAME canonical
 * (sorted-key) whole-schema JSON as srmech_tool_schema_to_json (reused per
 * the rc185 brief: Python get_tool_schema() takes no filter and
 * tool_schema_view() IS get_tool_schema().to_jsonable(), so both project the
 * WHOLE schema). The bytes are byte-identical to the rc184 canonical hash
 * pre-image and json-parse back EQUAL to get_tool_schema().to_jsonable()
 * (structural identity — dict equality is order-insensitive; the opaque
 * example/smoke_test_hint payloads are baked sorted-canonical in the rc184
 * table, so the sorted form is the only byte-stable whole-schema JSON the
 * table can produce). srmech_tool_entries_to_mcp_defs is the MCP tool-def
 * array projection (byte-identical to the Python list(...) compact dump).
 * ================================================================== */

srmech_status_t srmech_get_tool_schema(char *buf, size_t buf_len,
                                       size_t *out_len)
{
    ts_emit_t e;
    if (out_len == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(buf != NULL || buf_len == 0u);
    assert(out_len != NULL);  /* guaranteed by the early NULL-arg return */
    e.buf = buf;
    e.cap = buf_len;
    e.used = 0u;
    e.overflow = 0;
    ts_emit_schema_sorted(&e);
    return ts_finish(&e, out_len);
}

srmech_status_t srmech_tool_schema_view(char *buf, size_t buf_len,
                                        size_t *out_len)
{
    ts_emit_t e;
    if (out_len == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(buf != NULL || buf_len == 0u);
    assert(out_len != NULL);  /* guaranteed by the early NULL-arg return */
    e.buf = buf;
    e.cap = buf_len;
    e.used = 0u;
    e.overflow = 0;
    ts_emit_schema_sorted(&e);
    return ts_finish(&e, out_len);
}

/* ------------------------------------------------------------------
 * MCP tool-definitions projection
 *
 * The srmech-param-type-string lexicon (→ JSON-schema type + wire-encoding
 * hint) mirrors srmech.mcp._tools._TYPE_LEXICON / _ENCODING_HINT EXACTLY.
 * An unknown type degrades to "string" with no hint (the Python default).
 * ------------------------------------------------------------------ */

typedef struct {
    const char *k;
    const char *v;
} mcp_kv_t;

/* type-string → JSON-schema primitive type (mirrors _TYPE_LEXICON). */
static const mcp_kv_t MCP_TYPE_LEXICON[] = {
    {"int", "integer"},
    {"Optional[int]", "integer"},
    {"list[int]", "array"},
    {"float", "number"},
    {"Optional[float]", "number"},
    {"number", "number"},
    {"complex", "array"},
    {"bool", "boolean"},
    {"str", "string"},
    {"Optional[str]", "string"},
    {"bytes", "string"},
    {"Sequence[bytes]", "array"},
    {"list[tuple[bytes, bytes]]", "array"},
    {"list[tuple[bytes, int]]", "array"},
    {"list[tuple[int, int]]", "array"},
    {"list[list[int]]", "array"},
    {"Mapping[bytes, bytes]", "object"},
    {"dict", "object"},
    {"Optional[dict]", "object"},
    {"list", "array"},
    {"sequence", "array"},
    {"iterable[int]", "array"},
    {"tuple[int, int]", "array"},
    {"Mat", "array"},
    {"Vec", "array"},
    {"HV", "array"},
    {"Optional[Vec]", "array"},
    {"Optional[HV]", "array"},
    {"Mat | Vec", "array"},
    {"Sequence[Vec]", "array"},
    {"Sequence[HV]", "array"},
    {"tuple[Mat, ...]", "array"},
    {"list[list[list[float]]]", "array"},
    {"list[list[list[int]]]", "array"},
    {"tuple[np.ndarray, ...]", "array"},
    {"np.ndarray", "array"},
    {"Optional[np.ndarray]", "array"},
    {"Optional[list[float]]", "array"},
    {"Sequence[np.ndarray]", "array"},
    {"pathlib.Path", "string"},
    {"callable", "string"},
    {"operator_name", "string"},
    {"ChainSpec", "object"},
    {"SpectralHandle", "object"},
    {"SpectralHandle | bytes", "object"},
    {"numpy.random.Generator", "object"}
};

/* type-string → per-type JSON wire-encoding hint (mirrors _ENCODING_HINT).
 * The two SpectralHandle hints carry a literal '"' and (the first) a
 * U+2014 em-dash; they are stored as decoded UTF-8 and JSON-escaped on
 * emit, byte-identical to the Python str. */
static const mcp_kv_t MCP_ENCODING_HINT[] = {
    {"bytes", "base64-encoded bytes"},
    {"complex", "[real, imaginary]"},
    {"Mat",
     "nested JSON array of rows, row-major; complex elements as [re, im]"},
    {"Vec", "flat JSON array (length-n); complex elements as [re, im]"},
    {"HV", "flat JSON array of integers (the hypervector elements)"},
    {"Optional[Vec]",
     "flat JSON array (length-n) or null; complex elements as [re, im]"},
    {"Optional[HV]", "flat JSON array of integers, or null"},
    {"Mat | Vec",
     "nested JSON array of rows (2-D) OR a flat JSON array (1-D); "
     "complex elements as [re, im]"},
    {"Sequence[Vec]", "array of flat JSON arrays (each a 1-D vector)"},
    {"Sequence[HV]",
     "array of flat JSON integer arrays (each a hypervector)"},
    {"tuple[Mat, ...]",
     "array of nested JSON arrays (each a row-major matrix; complex as "
     "[re, im])"},
    {"list[list[list[float]]]", "rank-3 nested JSON array of real numbers"},
    {"list[list[int]]",
     "nested JSON array of integer lists (rows / coefficient cells)"},
    {"Sequence[bytes]", "array of base64-encoded byte strings"},
    {"np.ndarray",
     "nested JSON array, row-major; complex elements as [re, im]"},
    {"Optional[np.ndarray]",
     "nested JSON array, row-major; complex elements as [re, im]"},
    {"Sequence[np.ndarray]",
     "array of nested JSON arrays (each row-major; complex as [re, im])"},
    {"tuple[np.ndarray, ...]",
     "array of nested JSON arrays (each row-major; complex as [re, im])"},
    {"Mapping[bytes, bytes]",
     "object mapping base64-encoded key bytes to base64-encoded value bytes"},
    {"list[tuple[bytes, int]]",
     "array of [base64-encoded bytes, integer] pairs"},
    {"list[tuple[bytes, bytes]]",
     "array of [base64-encoded key, base64-encoded value] pairs"},
    {"SpectralHandle",
     "an opaque handle id {\"$srmech_handle\": {\"uuid\": ..., "
     "\"name\": ...}} returned by a producing spectral tool (decompose / "
     "predict / truncate_sparse) \xE2\x80\x94 pass it back verbatim"},
    {"SpectralHandle | bytes",
     "an opaque handle id {\"$srmech_handle\": {\"uuid\": ..., "
     "\"name\": ...}} returned by a producing spectral tool, OR "
     "base64-encoded bytes"},
    {"operator_name",
     "dotted import path of a unary sequence->sequence srmech operator, "
     "e.g. \"srmech.amsc.cascade.chiral_flip\""}
};

/* Bounded linear scan of a static kv table; NULL when the key is absent. */
static const char *mcp_lookup(const mcp_kv_t *tbl, size_t n, const char *key)
{
    size_t i;
    assert(tbl != NULL);
    assert(key != NULL);
    for (i = 0u; i < n; i++) {
        if (strcmp(tbl[i].k, key) == 0) {
            return tbl[i].v;
        }
    }
    return NULL;
}

static const char *mcp_json_type_for(const char *type)
{
    const size_t n = sizeof MCP_TYPE_LEXICON / sizeof MCP_TYPE_LEXICON[0];
    const char *v;
    assert(type != NULL);
    assert(n > 0u);
    v = mcp_lookup(MCP_TYPE_LEXICON, n, type);
    return (v != NULL) ? v : "string";
}

static const char *mcp_encoding_hint_for(const char *type)
{
    const size_t n = sizeof MCP_ENCODING_HINT / sizeof MCP_ENCODING_HINT[0];
    assert(type != NULL);
    assert(n > 0u);
    return mcp_lookup(MCP_ENCODING_HINT, n, type);
}

/* True iff `s` matches the Anthropic/MCP grammar ^[a-zA-Z0-9_.-]{1,64}$. */
static int mcp_key_is_clean(const char *s)
{
    size_t n = 0u;
    assert(s != NULL);
    while (s[n] != '\0') {
        unsigned char c = (unsigned char)s[n];
        int ok = (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z')
                 || (c >= '0' && c <= '9')
                 || c == '_' || c == '.' || c == '-';
        if (!ok) {
            return 0;
        }
        n++;
        if (n > 64u) {
            return 0;
        }
    }
    assert(n <= 64u);
    return (n >= 1u) ? 1 : 0;
}

/* Sanitise a property key into `out` (capacity 65) — mirrors
 * srmech.mcp._tools._sanitise_property_key: a clean key is copied
 * verbatim; otherwise leading '*' are stripped, out-of-grammar bytes
 * become '_', the result is clamped to 64 bytes, and an empty result
 * degrades to "arg". */
static void mcp_sanitise_key(const char *name, char *out)
{
    const char *p;
    size_t i, j;
    assert(name != NULL);
    assert(out != NULL);
    if (mcp_key_is_clean(name)) {
        j = 0u;
        while (name[j] != '\0' && j < 64u) {
            out[j] = name[j];
            j++;
        }
        out[j] = '\0';
        return;
    }
    p = name;
    while (*p == '*') {
        p++;
    }
    for (i = 0u, j = 0u; p[i] != '\0' && j < 64u; i++, j++) {
        unsigned char c = (unsigned char)p[i];
        int ok = (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z')
                 || (c >= '0' && c <= '9')
                 || c == '_' || c == '.' || c == '-';
        out[j] = ok ? (char)c : '_';
    }
    out[j] = '\0';
    if (j == 0u) {
        out[0] = 'a';
        out[1] = 'r';
        out[2] = 'g';
        out[3] = '\0';
    }
}

/* One JSON-schema property VALUE {"type":..,"description":..} for a param
 * (mirrors _parameter_to_schema_prop). */
static void mcp_emit_prop(ts_emit_t *e, const srmech_tool_param_t *pm)
{
    const char *hint;
    assert(e != NULL);
    assert(pm != NULL);
    ts_cstr(e, "{\"type\":");
    ts_json_string(e, mcp_json_type_for(pm->type));
    ts_cstr(e, ",\"description\":\"");
    if (pm->summary[0] != '\0') {
        ts_json_body(e, pm->summary);
        ts_cstr(e, " (srmech-type: ");
        ts_json_body(e, pm->type);
        ts_cstr(e, ")");
    } else {
        ts_cstr(e, "srmech-type: ");
        ts_json_body(e, pm->type);
    }
    hint = mcp_encoding_hint_for(pm->type);
    if (hint != NULL) {
        ts_cstr(e, " (");
        ts_json_body(e, hint);
        ts_cstr(e, ")");
    }
    ts_raw(e, "\"}", 2u);
}

/* The tool `description`: the parts joined by " — " (space em-dash
 * space) — summary, an optional Returns: line, then the category/owner
 * tag (mirrors tool_entry_to_mcp_def). */
static void mcp_emit_description(ts_emit_t *e, const srmech_tool_entry_t *t)
{
    static const char sep[] = " \xE2\x80\x94 "; /* space U+2014 space */
    assert(e != NULL);
    assert(t != NULL);
    ts_raw(e, "\"", 1u);
    ts_json_body(e, t->summary);
    if (t->returns_type != NULL) {
        ts_json_body(e, sep);
        ts_cstr(e, "Returns: ");
        ts_json_body(e, t->returns_type);
        if (t->returns_shape != NULL && t->returns_shape[0] != '\0') {
            ts_cstr(e, " (");
            ts_json_body(e, t->returns_shape);
            ts_cstr(e, ")");
        }
    }
    ts_json_body(e, sep);
    ts_cstr(e, "[srmech category: ");
    ts_json_body(e, t->category);
    ts_cstr(e, "; owner: ");
    ts_json_body(e, t->owner);
    ts_cstr(e, "]");
    ts_raw(e, "\"", 1u);
}

/* One MCP tool-definition object. */
static void mcp_emit_def(ts_emit_t *e, const srmech_tool_entry_t *t)
{
    uint32_t k;
    int first;
    char keybuf[65];
    assert(e != NULL);
    assert(t != NULL);
    ts_cstr(e, "{\"name\":");
    ts_json_string(e, t->name);
    ts_cstr(e, ",\"description\":");
    mcp_emit_description(e, t);
    ts_cstr(e, ",\"inputSchema\":{\"type\":\"object\",\"properties\":{");
    for (k = 0u; k < t->param_count; k++) {
        if (k > 0u) {
            ts_cstr(e, ",");
        }
        mcp_sanitise_key(t->params[k].name, keybuf);
        ts_json_string(e, keybuf);
        ts_cstr(e, ":");
        mcp_emit_prop(e, &t->params[k]);
    }
    ts_cstr(e, "},\"required\":[");
    first = 1;
    for (k = 0u; k < t->param_count; k++) {
        if (t->params[k].required == 0) {
            continue;
        }
        if (first == 0) {
            ts_cstr(e, ",");
        }
        first = 0;
        mcp_sanitise_key(t->params[k].name, keybuf);
        ts_json_string(e, keybuf);
    }
    ts_cstr(e, "]}}");
}

srmech_status_t srmech_tool_entries_to_mcp_defs(char *buf, size_t buf_len,
                                                size_t *out_len)
{
    ts_emit_t e;
    size_t n, i;
    int wrote;
    if (out_len == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(buf != NULL || buf_len == 0u);
    assert(out_len != NULL);  /* guaranteed by the early NULL-arg return */
    e.buf = buf;
    e.cap = buf_len;
    e.used = 0u;
    e.overflow = 0;
    ts_cstr(&e, "[");
    n = srmech_tool_registry_count();
    assert(n > 0u);
    wrote = 0;
    for (i = 0u; i < n; i++) {
        const srmech_tool_entry_t *t = srmech_tool_registry_get(i);
        if (t->mcp_callable == 0) {
            continue;
        }
        if (wrote != 0) {
            ts_cstr(&e, ",");
        }
        wrote = 1;
        mcp_emit_def(&e, t);
    }
    ts_cstr(&e, "]");
    return ts_finish(&e, out_len);
}
