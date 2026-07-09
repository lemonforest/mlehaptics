/*
 * srmech_mcp.c — the C MCP-server CONTROL SPINE (0.9.0rc186; the HOST-GLUE
 * JSON-RPC protocol + stdio read-loop over the rc184/rc185 tool_schema table).
 *
 * This is the C peer of srmech.mcp._server.MCPServer.handle + the
 * srmech.mcp._stdio.serve_stdio transport: a bare-C host (no Python) can serve
 * the MCP lifecycle + discovery surfaces — initialize / notifications/initialized
 * / tools/list / ping / shutdown — natively, plus the MPR attestation preimage.
 *
 * SCOPE (the honest split, per the rc186 brief). The tools/call DISPATCH
 * (invoke_tool — resolving a dotted tool name + marshalling ~403 tools' typed
 * arguments) is the SEPARATE next arc (rc187+). This rc routes tools/call to a
 * "defer" signal (out_kind == SRMECH_MCP_DEFER_CALL) so the Python host runs its
 * pure invoke_tool, OR — when no Python host is available (defer_calls == 0, the
 * bare-C serve_stdio loop) — emits an honest JSON-RPC error (inform-don't-limit).
 * So the loop is REAL (four of five methods fully in C, no hang, EOF-terminates)
 * while the dispatch tail is honestly deferred + still tracked (owed invoke_tool).
 *
 * BYTE-PARITY. srmech_mcp_handle emits the JSON-RPC response BYTE-IDENTICAL to
 * Python's json.dumps(MCPServer.handle(req), separators=(",", ":")) for
 * initialize / tools/list / ping / shutdown — INSERTION-ORDER keys (NOT the
 * sorted-key srmech_json_write_ws form), default ensure_ascii=True string
 * escaping. tools/list embeds srmech_tool_entries_to_mcp_defs verbatim.
 * srmech_mcp_build_attestation emits the MPR attestation object with the same
 * sha256 over the exact preimage (tool\x1f parser_version\x1f result\x1f ts).
 *
 * JPL-clean: no malloc (all output + parse arenas are caller-supplied), no goto,
 * no recursion (the parse tree is walked by the srmech_json parser; the dispatch
 * is a flat method switch), no libm, no abs. ABI-additive (SRMECH_ABI_VERSION
 * stays 4). License: MIT.
 */

#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

#include "srmech.h"
#include "srmech_platform.h"

/* JSON-RPC 2.0 error codes (mirror srmech.mcp._server). File-local. */
#define MCP_JSONRPC_PARSE_ERROR      (-32700)
#define MCP_JSONRPC_INVALID_REQUEST  (-32600)
#define MCP_JSONRPC_METHOD_NOT_FOUND (-32601)
#define MCP_JSONRPC_INVALID_PARAMS   (-32602)
#define MCP_JSONRPC_TOOL_ERROR       (-32000)

/* ------------------------------------------------------------------
 * Insertion-order JSON emitter (NOT sorted-key — the JSON-RPC wire form
 * mirrors json.dumps(...) which preserves dict insertion order). Same
 * two-pass buffer contract as srmech_tool_schema.c's ts_emit_t: buf == NULL
 * is a size-query (only `used` advances); a would-be over-write latches
 * `overflow` and freezes `used`.
 * ------------------------------------------------------------------ */

typedef struct {
    char  *buf;
    size_t cap;
    size_t used;
    int    overflow;
} mcp_emit_t;

static void mcp_raw(mcp_emit_t *e, const char *s, size_t n)
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

static void mcp_cstr(mcp_emit_t *e, const char *s)
{
    assert(e != NULL);
    assert(s != NULL);
    mcp_raw(e, s, strlen(s));
}

/* Decode one UTF-8 code point at p[*i], advancing *i. Trusted, complete,
 * valid UTF-8 (a srmech_json decoded string value / an ASCII literal). */
static uint32_t mcp_utf8_next(const unsigned char *p, size_t *i)
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
static void mcp_u_escape(mcp_emit_t *e, uint32_t cu)
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
    mcp_raw(e, b, 6u);
}

/* Emit the ESCAPED BODY of `s[0..len)` (no surrounding quotes), byte-identical
 * to CPython json.dumps default (ensure_ascii=True) string encoding. */
static void mcp_json_body_n(mcp_emit_t *e, const char *s, size_t len)
{
    const unsigned char *p = (const unsigned char *)s;
    size_t i = 0u;
    assert(e != NULL);
    assert(s != NULL || len == 0u);
    while (i < len) {
        uint32_t cp = mcp_utf8_next(p, &i);
        if (cp == 0x22u) {
            mcp_raw(e, "\\\"", 2u);
        } else if (cp == 0x5Cu) {
            mcp_raw(e, "\\\\", 2u);
        } else if (cp == 0x08u) {
            mcp_raw(e, "\\b", 2u);
        } else if (cp == 0x09u) {
            mcp_raw(e, "\\t", 2u);
        } else if (cp == 0x0Au) {
            mcp_raw(e, "\\n", 2u);
        } else if (cp == 0x0Cu) {
            mcp_raw(e, "\\f", 2u);
        } else if (cp == 0x0Du) {
            mcp_raw(e, "\\r", 2u);
        } else if (cp < 0x20u) {
            mcp_u_escape(e, cp);
        } else if (cp <= 0x7Eu) {
            char c = (char)cp;
            mcp_raw(e, &c, 1u);
        } else if (cp <= 0xFFFFu) {
            mcp_u_escape(e, cp);
        } else {
            uint32_t v = cp - 0x10000u;
            mcp_u_escape(e, 0xD800u + (v >> 10));
            mcp_u_escape(e, 0xDC00u + (v & 0x3FFu));
        }
    }
}

/* Emit `s[0..len)` as a JSON string (with surrounding quotes). */
static void mcp_json_str_n(mcp_emit_t *e, const char *s, size_t len)
{
    assert(e != NULL);
    assert(s != NULL || len == 0u);
    mcp_raw(e, "\"", 1u);
    mcp_json_body_n(e, s, len);
    mcp_raw(e, "\"", 1u);
}

/* Emit a NUL-terminated C string as a JSON string. */
static void mcp_json_str(mcp_emit_t *e, const char *s)
{
    assert(e != NULL);
    assert(s != NULL);
    mcp_json_str_n(e, s, strlen(s));
}

/* Emit an int64 in decimal (json.dumps emits ints verbatim). */
static void mcp_emit_i64(mcp_emit_t *e, int64_t i)
{
    char tmp[24];
    int pos = 0;
    int neg = 0;
    uint64_t u;
    assert(e != NULL);
    assert(e->buf != NULL || e->cap == 0u);
    if (i < 0) {
        neg = 1;
        u = (uint64_t)(-(i + 1)) + 1u;   /* two's-complement safe for INT64_MIN */
    } else {
        u = (uint64_t)i;
    }
    if (u == 0u) {
        tmp[pos++] = '0';
    }
    while (u > 0u) {
        tmp[pos++] = (char)('0' + (int)(u % 10u));
        u /= 10u;
    }
    if (neg) {
        mcp_raw(e, "-", 1u);
    }
    while (pos > 0) {
        pos--;
        mcp_raw(e, &tmp[pos], 1u);
    }
}

/* Echo a JSON-RPC id node verbatim: int / string / bool / null (absent ⇒
 * null). Doubles / containers degrade to null (ids are scalars per spec). */
static void mcp_emit_id(mcp_emit_t *e, const srmech_json_value_t *id)
{
    assert(e != NULL);
    assert(e->buf != NULL || e->cap == 0u);
    if (id == NULL) {
        mcp_cstr(e, "null");
    } else if (id->type == SRMECH_JSON_INT) {
        mcp_emit_i64(e, id->u.i);
    } else if (id->type == SRMECH_JSON_STRING) {
        mcp_json_str_n(e, id->u.str.ptr, id->u.str.len);
    } else if (id->type == SRMECH_JSON_BOOL) {
        mcp_cstr(e, id->u.b ? "true" : "false");
    } else {
        mcp_cstr(e, "null");
    }
}

/* Append the advertised MCP tool-defs array (srmech_tool_entries_to_mcp_defs)
 * at the emitter's current offset, respecting the size-query / overflow modes. */
static void mcp_append_mcp_defs(mcp_emit_t *e)
{
    size_t sub = 0u;
    srmech_status_t rc;
    assert(e != NULL);
    assert(e->buf != NULL || e->cap == 0u);
    if (e->buf == NULL) {                       /* size-query pass */
        rc = srmech_tool_entries_to_mcp_defs(NULL, 0u, &sub);
        if (rc == SRMECH_OK) {
            e->used += sub;
        } else {
            e->overflow = 1;
        }
        return;
    }
    if (e->overflow) {
        return;
    }
    rc = srmech_tool_entries_to_mcp_defs(e->buf + e->used, e->cap - e->used, &sub);
    if (rc == SRMECH_OK) {
        e->used += sub;
    } else {
        e->overflow = 1;
    }
}

/* ------------------------------------------------------------------
 * Response builders — each emits the whole JSON-RPC response object in
 * insertion-order key form (jsonrpc, id, result|error).
 * ------------------------------------------------------------------ */

static void mcp_build_error(mcp_emit_t *e, const srmech_json_value_t *id,
                            int code, const char *msg)
{
    assert(e != NULL);
    assert(msg != NULL);
    mcp_cstr(e, "{\"jsonrpc\":\"2.0\",\"id\":");
    mcp_emit_id(e, id);
    mcp_cstr(e, ",\"error\":{\"code\":");
    mcp_emit_i64(e, (int64_t)code);
    mcp_cstr(e, ",\"message\":");
    mcp_json_str(e, msg);
    mcp_cstr(e, "}}");
}

static void mcp_build_unknown_method(mcp_emit_t *e, const srmech_json_value_t *id,
                                     const srmech_json_value_t *method)
{
    assert(e != NULL);
    assert(method != NULL);
    mcp_cstr(e, "{\"jsonrpc\":\"2.0\",\"id\":");
    mcp_emit_id(e, id);
    mcp_cstr(e, ",\"error\":{\"code\":-32601,\"message\":\"");
    mcp_json_body_n(e, "unknown method '", 16u);   /* Python f"...{method!r}" */
    mcp_json_body_n(e, method->u.str.ptr, method->u.str.len);
    mcp_json_body_n(e, "'", 1u);
    mcp_cstr(e, "\"}}");
}

static void mcp_build_result_empty(mcp_emit_t *e, const srmech_json_value_t *id)
{
    assert(e != NULL);
    assert(e->buf != NULL || e->cap == 0u);
    mcp_cstr(e, "{\"jsonrpc\":\"2.0\",\"id\":");
    mcp_emit_id(e, id);
    mcp_cstr(e, ",\"result\":{}}");
}

static void mcp_build_tools_list(mcp_emit_t *e, const srmech_json_value_t *id)
{
    assert(e != NULL);
    assert(e->buf != NULL || e->cap == 0u);
    mcp_cstr(e, "{\"jsonrpc\":\"2.0\",\"id\":");
    mcp_emit_id(e, id);
    mcp_cstr(e, ",\"result\":{\"tools\":");
    mcp_append_mcp_defs(e);
    mcp_cstr(e, "}}");
}

static void mcp_build_initialize(mcp_emit_t *e, const srmech_json_value_t *id,
                                 const srmech_json_value_t *params)
{
    const srmech_json_value_t *pv = (params != NULL)
        ? srmech_json_object_get(params, "protocolVersion") : NULL;
    assert(e != NULL);
    assert(e->buf != NULL || e->cap == 0u);
    mcp_cstr(e, "{\"jsonrpc\":\"2.0\",\"id\":");
    mcp_emit_id(e, id);
    mcp_cstr(e, ",\"result\":{\"protocolVersion\":");
    if (pv != NULL && pv->type == SRMECH_JSON_STRING && pv->u.str.len > 0u) {
        mcp_json_str_n(e, pv->u.str.ptr, pv->u.str.len);
    } else {
        mcp_json_str(e, SRMECH_MCP_PROTOCOL_VERSION);
    }
    mcp_cstr(e, ",\"serverInfo\":{\"name\":");
    mcp_json_str(e, SRMECH_MCP_SERVER_NAME);
    mcp_cstr(e, ",\"version\":");
    mcp_json_str(e, srmech_version());
    mcp_cstr(e, "},\"capabilities\":{\"tools\":{}}}}");
}

/* True iff a srmech_json STRING value equals the NUL-terminated `lit`. */
static int mcp_json_str_eq(const srmech_json_value_t *v, const char *lit)
{
    size_t n;
    assert(v != NULL);
    assert(lit != NULL);
    if (v->type != SRMECH_JSON_STRING) {
        return 0;
    }
    n = strlen(lit);
    if ((size_t)v->u.str.len != n) {
        return 0;
    }
    return memcmp(v->u.str.ptr, lit, n) == 0;
}

/* Dispatch a validated (method is a string) request onto its builder. */
static srmech_status_t mcp_dispatch_method(const srmech_json_value_t *method,
        const srmech_json_value_t *id, const srmech_json_value_t *params,
        int is_notif, mcp_emit_t *e, size_t *out_len, int *out_kind,
        int defer_calls)
{
    assert(method != NULL);
    assert(e != NULL);
    if (mcp_json_str_eq(method, "notifications/initialized")) {
        *out_kind = SRMECH_MCP_NO_RESPONSE;
        *out_len = 0u;
        return SRMECH_OK;
    }
    if (mcp_json_str_eq(method, "initialize")) {
        mcp_build_initialize(e, id, params);
    } else if (mcp_json_str_eq(method, "tools/list")) {
        mcp_build_tools_list(e, id);
    } else if (mcp_json_str_eq(method, "ping")
               || mcp_json_str_eq(method, "shutdown")) {
        mcp_build_result_empty(e, id);
    } else if (mcp_json_str_eq(method, "tools/call")) {
        if (defer_calls) {
            *out_kind = SRMECH_MCP_DEFER_CALL;
            *out_len = 0u;
            return SRMECH_OK;
        }
        mcp_build_error(e, id, MCP_JSONRPC_TOOL_ERROR,
                        "tools/call dispatch requires the Python host "
                        "(bare-C invoke_tool arrives in a later rc)");
    } else if (is_notif) {
        *out_kind = SRMECH_MCP_NO_RESPONSE;
        *out_len = 0u;
        return SRMECH_OK;
    } else {
        mcp_build_unknown_method(e, id, method);
    }
    *out_kind = SRMECH_MCP_RESPONSE;
    *out_len = e->used;
    return e->overflow ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* Validate the top-level request object, then dispatch. */
static srmech_status_t mcp_dispatch_object(const srmech_json_value_t *root,
        mcp_emit_t *e, size_t *out_len, int *out_kind, int defer_calls)
{
    const srmech_json_value_t *method;
    const srmech_json_value_t *id;
    const srmech_json_value_t *params;
    int is_notif;
    assert(root != NULL);
    assert(e != NULL);
    method = srmech_json_object_get(root, "method");
    id = srmech_json_object_get(root, "id");
    params = srmech_json_object_get(root, "params");
    is_notif = (id == NULL);
    if (method == NULL || method->type != SRMECH_JSON_STRING) {
        if (is_notif) {
            *out_kind = SRMECH_MCP_NO_RESPONSE;
            *out_len = 0u;
            return SRMECH_OK;
        }
        mcp_build_error(e, id, MCP_JSONRPC_INVALID_REQUEST,
                        "request missing string 'method' field");
        *out_kind = SRMECH_MCP_RESPONSE;
        *out_len = e->used;
        return e->overflow ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
    }
    if (params != NULL && params->type != SRMECH_JSON_OBJECT) {
        if (is_notif) {
            *out_kind = SRMECH_MCP_NO_RESPONSE;
            *out_len = 0u;
            return SRMECH_OK;
        }
        mcp_build_error(e, id, MCP_JSONRPC_INVALID_PARAMS,
                        "'params' must be an object");
        *out_kind = SRMECH_MCP_RESPONSE;
        *out_len = e->used;
        return e->overflow ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
    }
    return mcp_dispatch_method(method, id, params, is_notif, e,
                               out_len, out_kind, defer_calls);
}

srmech_status_t srmech_mcp_handle(const char *req, size_t req_len,
                                  void *ws, size_t ws_len,
                                  char *buf, size_t buf_len,
                                  size_t *out_len, int *out_kind,
                                  int defer_calls)
{
    mcp_emit_t e;
    srmech_json_value_t *root = NULL;
    srmech_status_t prc;
    if (out_len == NULL || out_kind == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(buf != NULL || buf_len == 0u);
    assert(out_len != NULL && out_kind != NULL);
    e.buf = buf;
    e.cap = buf_len;
    e.used = 0u;
    e.overflow = 0;
    prc = srmech_json_parse(req, req_len, ws, ws_len, &root);
    if (prc != SRMECH_OK || root == NULL || root->type != SRMECH_JSON_OBJECT) {
        mcp_build_error(&e, NULL, MCP_JSONRPC_PARSE_ERROR, "Parse error");
        *out_kind = SRMECH_MCP_RESPONSE;
        *out_len = e.used;
        return e.overflow ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
    }
    return mcp_dispatch_object(root, &e, out_len, out_kind, defer_calls);
}

/* ------------------------------------------------------------------
 * MPR attestation (srmech.mcp._server.build_attestation) — the sha256 over
 * the exact preimage `tool_name \x1f parser_version \x1f result \x1f ts`,
 * emitted as the MPR attestation object.
 * ------------------------------------------------------------------ */

/* Append `src[0..n)` into ws with a bound check; returns 1 on success. */
static int mcp_ws_put(char *ws, size_t cap, size_t *pos,
                      const char *src, size_t n)
{
    assert(ws != NULL || cap == 0u);
    assert(pos != NULL && (src != NULL || n == 0u));
    if (*pos + n > cap) {
        return 0;
    }
    if (n > 0u) {
        memcpy(ws + *pos, src, n);
    }
    *pos += n;
    return 1;
}

/* Build tool\x1f pv \x1f result \x1f ts into ws; *out_len = preimage length. */
static srmech_status_t mcp_att_preimage(char *ws, size_t ws_len,
        const char *tn, const char *pv, const char *rt, const char *ra,
        size_t *out_len)
{
    static const char sep[1] = { (char)0x1f };
    size_t pos = 0u;
    int ok = 1;
    assert(out_len != NULL);
    assert(tn != NULL && pv != NULL && rt != NULL && ra != NULL);
    ok = ok && mcp_ws_put(ws, ws_len, &pos, tn, strlen(tn));
    ok = ok && mcp_ws_put(ws, ws_len, &pos, sep, 1u);
    ok = ok && mcp_ws_put(ws, ws_len, &pos, pv, strlen(pv));
    ok = ok && mcp_ws_put(ws, ws_len, &pos, sep, 1u);
    ok = ok && mcp_ws_put(ws, ws_len, &pos, rt, strlen(rt));
    ok = ok && mcp_ws_put(ws, ws_len, &pos, sep, 1u);
    ok = ok && mcp_ws_put(ws, ws_len, &pos, ra, strlen(ra));
    if (!ok) {
        return SRMECH_ERR_OVERFLOW;
    }
    *out_len = pos;
    return SRMECH_OK;
}

srmech_status_t srmech_mcp_build_attestation(const char *tool_name,
        const char *result_text, const char *retrieved_at,
        void *ws, size_t ws_len, char *buf, size_t buf_len, size_t *out_len)
{
    mcp_emit_t e;
    char pvbuf[96];
    char hex[65];
    const char *ver = srmech_version();
    size_t plen = 0u, vlen;
    srmech_status_t rc;
    if (tool_name == NULL || result_text == NULL || retrieved_at == NULL
        || out_len == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(buf != NULL || buf_len == 0u);
    assert(ver != NULL);
    vlen = strlen(ver);
    if (7u + vlen + 1u > sizeof pvbuf) {
        return SRMECH_ERR_OVERFLOW;
    }
    memcpy(pvbuf, "srmech ", 7u);
    memcpy(pvbuf + 7u, ver, vlen);
    pvbuf[7u + vlen] = '\0';
    if (buf != NULL) {   /* size-query does not need the real digest */
        rc = mcp_att_preimage((char *)ws, ws_len, tool_name, pvbuf,
                              result_text, retrieved_at, &plen);
        if (rc != SRMECH_OK) {
            return rc;
        }
        rc = srmech_sha256_hex((const uint8_t *)ws, plen, hex);
        if (rc != SRMECH_OK) {
            return rc;
        }
    } else {
        memset(hex, '0', 64u);
    }
    e.buf = buf;
    e.cap = buf_len;
    e.used = 0u;
    e.overflow = 0;
    mcp_cstr(&e, "{\"mpr_version\":\"1.0\",\"tool_name\":");
    mcp_json_str(&e, tool_name);
    mcp_cstr(&e, ",\"parser_version\":");
    mcp_json_str(&e, pvbuf);
    mcp_cstr(&e, ",\"retrieved_at\":");
    mcp_json_str(&e, retrieved_at);
    mcp_cstr(&e, ",\"response_sha256\":\"");
    mcp_raw(&e, hex, 64u);
    mcp_cstr(&e, "\"}");
    *out_len = e.used;
    return e.overflow ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* ------------------------------------------------------------------
 * The stdio JSON-RPC read-frame → handle → write-frame loop. Newline-delimited
 * requests from stdin (via the PAL); newline-delimited responses to stdout.
 * EOF (a closed stdin pipe) is the deterministic terminator → clean SRMECH_OK.
 * Never hangs: each stdin read pulls at most one byte and returns promptly on
 * EOF. tools/call is served with the honest bare-C error (defer_calls == 0).
 * ------------------------------------------------------------------ */

/* Read one newline-delimited line (the '\n' consumed, not stored) into `line`.
 * out_eof := 1 at end-of-stream (with any trailing partial line returned). A
 * line longer than `cap` returns SRMECH_ERR_OVERFLOW (the caller skips it). */
static srmech_status_t mcp_read_line(char *line, size_t cap,
                                     size_t *out_len, int *out_eof)
{
    size_t n = 0u;
    assert(line != NULL || cap == 0u);
    assert(out_len != NULL && out_eof != NULL);
    *out_eof = 0;
    *out_len = 0u;
    for (;;) {
        unsigned char c = 0u;
        size_t got = 0u;
        srmech_status_t rc = srmech_plat_stdin_read(&c, 1u, &got);
        if (rc != SRMECH_OK) {
            return rc;
        }
        if (got == 0u) {
            *out_len = n;
            *out_eof = 1;
            return SRMECH_OK;
        }
        if (c == (unsigned char)'\n') {
            *out_len = n;
            return SRMECH_OK;
        }
        if (n >= cap) {
            return SRMECH_ERR_OVERFLOW;
        }
        line[n] = (char)c;
        n += 1u;
    }
}

/* Trim leading/trailing ASCII whitespace of line[0..len); start + tlen span
 * the trimmed content (mirrors Python line.strip() + blank-line skip). */
static void mcp_trim(const char *line, size_t len, size_t *start, size_t *tlen)
{
    size_t a = 0u, b = len;
    assert(line != NULL || len == 0u);
    assert(start != NULL && tlen != NULL);
    while (a < b && (line[a] == ' ' || line[a] == '\t'
                     || line[a] == '\r' || line[a] == '\n')) {
        a++;
    }
    while (b > a && (line[b - 1u] == ' ' || line[b - 1u] == '\t'
                     || line[b - 1u] == '\r' || line[b - 1u] == '\n')) {
        b--;
    }
    *start = a;
    *tlen = b - a;
}

srmech_status_t srmech_mcp_serve_stdio(char *line_buf, size_t line_cap,
                                       void *ws, size_t ws_len,
                                       char *resp_buf, size_t resp_cap)
{
    assert(line_buf != NULL && resp_buf != NULL);
    assert(line_cap > 0u && resp_cap > 0u);
    if (line_buf == NULL || resp_buf == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (!srmech_plat_has_stdio()) {
        return SRMECH_ERR_IO;
    }
    for (;;) {
        size_t llen = 0u, start = 0u, tlen = 0u, out_len = 0u;
        int eof = 0, kind = 0;
        srmech_status_t rc = mcp_read_line(line_buf, line_cap, &llen, &eof);
        if (rc == SRMECH_ERR_OVERFLOW) {
            continue;   /* over-long line: skip, keep serving (no hang) */
        }
        if (rc != SRMECH_OK) {
            return rc;
        }
        mcp_trim(line_buf, llen, &start, &tlen);
        if (tlen > 0u) {
            rc = srmech_mcp_handle(line_buf + start, tlen, ws, ws_len,
                                   resp_buf, resp_cap, &out_len, &kind, 0);
            if (rc == SRMECH_OK && kind == SRMECH_MCP_RESPONSE && out_len > 0u) {
                (void)srmech_plat_stdout_write(
                    (const unsigned char *)resp_buf, out_len);
                (void)srmech_plat_stdout_write((const unsigned char *)"\n", 1u);
            }
        }
        if (eof) {
            return SRMECH_OK;
        }
    }
}
