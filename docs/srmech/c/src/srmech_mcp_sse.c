/*
 * srmech_mcp_sse.c — the C MCP HTTP+SSE transport (0.9.0rc194; HOST-GLUE).
 *
 * The C peer of srmech.mcp._sse.serve_http_sse: a bare-C host (no Python) can
 * serve MCP over a cross-terminal HTTP+Server-Sent-Events transport natively.
 * Per the MCP HTTP+SSE spec it exposes:
 *   GET  /sse                    — the SSE stream. First emits an `endpoint`
 *                                  event carrying the POST URL
 *                                  (/message?session=<id>); subsequent JSON-RPC
 *                                  responses ride as `message` events.
 *   POST /message?session=<id>   — one JSON-RPC request body; returns 202 and
 *                                  the response rides the matching SSE stream.
 *   GET  /healthz                — {"status": "ok"}.
 *
 * It COMPOSES the rc186 srmech_mcp_handle (the JSON-RPC dispatch, defer_calls==0
 * — the bare-C-host discipline, exactly like srmech_mcp_serve_stdio; tools/call
 * returns the honest defer error, so the transport is complete while dispatch
 * stays the rc188 invoke_tool concern) + the rc194 TCP PAL (bind/accept/read/
 * write). The HTTP/1.1 parse, the SSE event framing, and the bounded, mutex-
 * guarded session registry are OS-agnostic and live here.
 *
 * THREADS: one accept thread (poll-gated accept loop → routes GET/POST) + one
 * keepalive scanner thread (a 15s `: keepalive` comment on idle sessions). A
 * GET /sse connection is registered and LEFT OPEN (the session owns it); POSTs
 * are short and served inline on the accept thread. Writes to a session's SSE
 * connection (POST push + keepalive) serialise under the registry mutex.
 *
 * NO-HANG teardown (the rc180 socket-teardown discipline): srmech_mcp_sse_stop
 * sets the stop flag + closes the TCP listener; the poll-gated accept loop
 * returns within one poll tick, the keepalive loop within its sleep tick, all
 * session connections are closed, both threads join, then the handle frees.
 *
 * POSIX-FIRST: the rc194 TCP PAL is POSIX today; on a host where
 * srmech_plat_has_tcp() == 0 (Windows Winsock follow-up / bare-metal) serve
 * returns SRMECH_ERR_BAD_INPUT and a Python host runs the pure http.server.
 *
 * JPL-clean: no goto, no libm, no abs; malloc only at server setup / teardown
 * (RULE_3_COLD_PATH_FILES, like srmech_bus.c) — no per-request allocation; the
 * accept-thread scratch buffers are allocated once at serve. ABI-additive (new
 * symbols, no new callback typedef — the server dispatches in C via
 * srmech_mcp_handle, taking NO Python callback), so SRMECH_ABI_VERSION stays 4.
 * License: MIT.
 */

#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "srmech.h"
#include "srmech_platform.h"

/* ------------------------------------------------------------------ *
 * Bounds
 * ------------------------------------------------------------------ */

#define SSE_MAX_SESSIONS   8u
#define SSE_ID_CAP         40u            /* session-id string cap          */
#define SSE_REQ_CAP        (256u * 1024u) /* HTTP head+body read buffer     */
#define SSE_WS_CAP         (512u * 1024u) /* srmech_mcp_handle parse arena  */
#define SSE_RESP_CAP       (2u * 1024u * 1024u)   /* one JSON-RPC response  */
#define SSE_FRAME_CAP      (SSE_RESP_CAP + 256u)   /* SSE-framed response   */
#define SSE_ACCEPT_POLL_MS 200u           /* accept poll tick (teardown)    */
#define SSE_KEEPALIVE_NS   (15LL * 1000000000LL)   /* 15s keepalive cadence */

/* ------------------------------------------------------------------ *
 * Handle structs
 * ------------------------------------------------------------------ */

typedef struct sse_session {
    srmech_plat_stream_conn_t conn;          /* the open GET /sse connection */
    char                      id[SSE_ID_CAP];
    int64_t                   last_write_ns;
    int                       active;
} sse_session_t;

struct srmech_mcp_sse_server {
    srmech_plat_tcp_server_t listener;
    uint16_t                 port;
    int                      stop_flag;
    srmech_plat_thread_t     accept_thread;
    srmech_plat_thread_t     keepalive_thread;
    int                      accept_running;
    int                      keepalive_running;
    srmech_plat_mutex_t      lock;
    sse_session_t            sessions[SSE_MAX_SESSIONS];
    size_t                   session_count;
    uint64_t                 id_counter;
    /* accept-thread scratch (single-threaded there; allocated once) */
    unsigned char           *reqbuf;
    void                    *ws;
    char                    *respbuf;
    char                    *framebuf;
};

/* ------------------------------------------------------------------ *
 * HTTP/1.1 request parse (bounded — GET/POST, path, ?session=, Content-Length)
 * ------------------------------------------------------------------ */

typedef struct {
    int         method;      /* 0 GET, 1 POST, -1 other */
    const char *path;
    size_t      path_len;
    const char *query;
    size_t      query_len;
    long        content_length;
} sse_req_t;

/* Case-insensitive compare of a[0..n) against the lowercase literal `lit`. */
static int sse_ci_eq(const char *a, size_t n, const char *lit)
{
    size_t i;
    assert(a != NULL || n == 0u);
    assert(lit != NULL);
    if (strlen(lit) != n) {
        return 0;
    }
    for (i = 0u; i < n; i++) {
        char c = a[i];
        if (c >= 'A' && c <= 'Z') {
            c = (char)(c - 'A' + 'a');
        }
        if (c != lit[i]) {
            return 0;
        }
    }
    return 1;
}

/* Scan the header lines of head[0..hlen) for a Content-Length; -1 if absent. */
static long sse_scan_content_length(const char *head, size_t hlen)
{
    size_t i = 0u;
    assert(head != NULL || hlen == 0u);
    while (i < hlen) {
        size_t ls = i;
        while (i < hlen && head[i] != '\n') {
            i++;
        }
        size_t le = (i > ls && head[i - 1u] == '\r') ? (i - 1u) : i;
        assert(le >= ls && le <= hlen);
        const char *colon = memchr(head + ls, ':', le - ls);
        if (colon != NULL) {
            size_t nlen = (size_t)(colon - (head + ls));
            if (sse_ci_eq(head + ls, nlen, "content-length")) {
                long v = 0;
                const char *p = colon + 1;
                while (p < head + le && (*p == ' ' || *p == '\t')) {
                    p++;
                }
                while (p < head + le && *p >= '0' && *p <= '9') {
                    v = v * 10 + (*p - '0');
                    p++;
                }
                return v;
            }
        }
        i++;   /* past the '\n' */
    }
    return -1;
}

/* Parse the request line + Content-Length out of head[0..hlen). */
static void sse_parse_request(const char *head, size_t hlen, sse_req_t *r)
{
    assert(head != NULL || hlen == 0u);
    assert(r != NULL);
    r->method = -1;
    r->path = head;
    r->path_len = 0u;
    r->query = NULL;
    r->query_len = 0u;
    r->content_length = -1;
    const char *sp1 = memchr(head, ' ', hlen);
    if (sp1 == NULL) {
        return;
    }
    size_t mlen = (size_t)(sp1 - head);
    if (sse_ci_eq(head, mlen, "get")) {
        r->method = 0;
    } else if (sse_ci_eq(head, mlen, "post")) {
        r->method = 1;
    }
    const char *tstart = sp1 + 1;
    size_t rest = hlen - (size_t)(tstart - head);
    const char *sp2 = memchr(tstart, ' ', rest);
    size_t tlen = (sp2 != NULL) ? (size_t)(sp2 - tstart) : rest;
    const char *q = memchr(tstart, '?', tlen);
    if (q != NULL) {
        r->path = tstart;
        r->path_len = (size_t)(q - tstart);
        r->query = q + 1;
        r->query_len = tlen - r->path_len - 1u;
    } else {
        r->path = tstart;
        r->path_len = tlen;
    }
    r->content_length = sse_scan_content_length(head, hlen);
}

/* Extract the value of `session=` from a query string into `out` (cap
 * out_cap). Returns 1 on success (NUL-terminated), 0 if absent / too long. */
static int sse_query_session(const char *q, size_t qlen, char *out, size_t cap)
{
    size_t i = 0u;
    assert(out != NULL && cap > 0u);
    assert(q != NULL || qlen == 0u);
    while (i < qlen) {
        size_t ks = i;
        while (i < qlen && q[i] != '&') {
            i++;
        }
        const char *eq = memchr(q + ks, '=', i - ks);
        if (eq != NULL && sse_ci_eq(q + ks, (size_t)(eq - (q + ks)), "session")) {
            size_t vlen = (size_t)((q + i) - (eq + 1));
            if (vlen == 0u || vlen + 1u > cap) {
                return 0;
            }
            memcpy(out, eq + 1, vlen);
            out[vlen] = '\0';
            return 1;
        }
        i++;   /* past '&' */
    }
    return 0;
}

/* ------------------------------------------------------------------ *
 * SSE event framing + raw HTTP writes
 * ------------------------------------------------------------------ */

/* Frame one SSE event into `buf` (cap): "event: NAME\n" + a "data: LINE\n" per
 * newline-split line of `data` + a trailing "\n". *out_len = framed length.
 * Byte-exact with srmech.mcp._sse._sse_emit. */
static srmech_status_t sse_frame_event(char *buf, size_t cap, const char *name,
                                       const char *data, size_t dlen,
                                       size_t *out_len)
{
    size_t pos = 0u;
    size_t i = 0u;
    assert(buf != NULL && out_len != NULL);
    assert(name != NULL && (data != NULL || dlen == 0u));
    int n = snprintf(buf, cap, "event: %s\n", name);
    if (n < 0 || (size_t)n >= cap) {
        return SRMECH_ERR_OVERFLOW;
    }
    pos = (size_t)n;
    while (i <= dlen) {          /* emit one data: line per '\n'-split segment */
        size_t ls = i;
        while (i < dlen && data[i] != '\n') {
            i++;
        }
        size_t seg = i - ls;
        if (pos + 6u + seg + 1u > cap) {
            return SRMECH_ERR_OVERFLOW;
        }
        memcpy(buf + pos, "data: ", 6u);
        pos += 6u;
        memcpy(buf + pos, data + ls, seg);
        pos += seg;
        buf[pos++] = '\n';
        if (i == dlen) {
            break;
        }
        i++;                     /* past the '\n' */
    }
    if (pos + 1u > cap) {
        return SRMECH_ERR_OVERFLOW;
    }
    buf[pos++] = '\n';
    *out_len = pos;
    return SRMECH_OK;
}

/* Write a complete NUL-terminated HTTP response (status line + headers + body
 * already assembled) to a connection. */
static srmech_status_t sse_write_cstr(srmech_plat_stream_conn_t *conn,
                                      const char *s)
{
    assert(conn != NULL);
    assert(s != NULL);
    return srmech_plat_tcp_write_all(conn, (const unsigned char *)s, strlen(s));
}

/* Write a fixed-body HTTP response (JSON) with an explicit Content-Length. */
static srmech_status_t sse_write_json_response(srmech_plat_stream_conn_t *conn,
        char *scratch, size_t cap, int status, const char *reason,
        const char *body)
{
    assert(conn != NULL && scratch != NULL);
    assert(reason != NULL && body != NULL);
    int n = snprintf(scratch, cap,
                     "HTTP/1.1 %d %s\r\n"
                     "Content-Type: application/json\r\n"
                     "Content-Length: %zu\r\n"
                     "Connection: close\r\n\r\n%s",
                     status, reason, strlen(body), body);
    if (n < 0 || (size_t)n >= cap) {
        return SRMECH_ERR_OVERFLOW;
    }
    return sse_write_cstr(conn, scratch);
}

/* ------------------------------------------------------------------ *
 * Session registry (mutex-guarded)
 * ------------------------------------------------------------------ */

/* Build a URL-safe session id from the wall clock + a monotone counter
 * (unguessable enough for a localhost transport; documented). Under lock. */
static void sse_gen_id(srmech_mcp_sse_server_t *h, char *out, size_t cap)
{
    int64_t now_ns = 0;
    assert(h != NULL && out != NULL);
    assert(cap >= 24u);
    (void)srmech_plat_now_ns(&now_ns);
    uint64_t mix = (uint64_t)now_ns ^ (h->id_counter * 0x9E3779B97F4A7C15ULL);
    h->id_counter += 1u;
    int n = snprintf(out, cap, "s%016llx%08llx",
                     (unsigned long long)mix,
                     (unsigned long long)(h->id_counter & 0xFFFFFFFFu));
    assert(n > 0 && (size_t)n < cap);
    (void)n;
}

/* Register `conn` as a new SSE session; copies the generated id into `id_out`.
 * Returns SRMECH_ERR_OVERFLOW when the registry is full. Under lock. */
static srmech_status_t sse_register_locked(srmech_mcp_sse_server_t *h,
        srmech_plat_stream_conn_t *conn, char *id_out, size_t id_cap)
{
    assert(h != NULL && conn != NULL && id_out != NULL);
    assert(h->session_count <= SSE_MAX_SESSIONS);
    if (h->session_count >= SSE_MAX_SESSIONS) {
        return SRMECH_ERR_OVERFLOW;
    }
    sse_session_t *s = &h->sessions[h->session_count];
    s->conn = *conn;
    sse_gen_id(h, s->id, sizeof s->id);
    int64_t now_ns = 0;
    (void)srmech_plat_now_ns(&now_ns);
    s->last_write_ns = now_ns;
    s->active = 1;
    h->session_count += 1u;
    size_t idl = strlen(s->id);
    if (idl + 1u > id_cap) {
        return SRMECH_ERR_OVERFLOW;
    }
    memcpy(id_out, s->id, idl + 1u);
    return SRMECH_OK;
}

/* Push one JSON-RPC response body to the session `id` as a `message` SSE event
 * (framed in h->framebuf, written under lock). No-op if the session is gone. */
static srmech_status_t sse_push_message(srmech_mcp_sse_server_t *h,
        const char *id, const char *body, size_t blen)
{
    size_t flen = 0u;
    srmech_status_t rc;
    assert(h != NULL && id != NULL);
    assert(body != NULL || blen == 0u);
    rc = sse_frame_event(h->framebuf, SSE_FRAME_CAP, "message", body, blen, &flen);
    if (rc != SRMECH_OK) {
        return rc;
    }
    rc = srmech_plat_mutex_lock(&h->lock);
    if (rc != SRMECH_OK) {
        return rc;
    }
    for (size_t i = 0u; i < h->session_count; i++) {
        sse_session_t *s = &h->sessions[i];
        if (s->active && strcmp(s->id, id) == 0) {
            int64_t now_ns = 0;
            (void)srmech_plat_now_ns(&now_ns);
            s->last_write_ns = now_ns;
            (void)srmech_plat_tcp_write_all(
                &s->conn, (const unsigned char *)h->framebuf, flen);
            break;
        }
    }
    (void)srmech_plat_mutex_unlock(&h->lock);
    return SRMECH_OK;
}

/* Close every registered session connection + clear the registry. Under lock
 * (teardown, before the mutex is destroyed). */
static void sse_close_all_sessions(srmech_mcp_sse_server_t *h)
{
    assert(h != NULL);
    assert(h->session_count <= SSE_MAX_SESSIONS);
    if (srmech_plat_mutex_lock(&h->lock) != SRMECH_OK) {
        return;
    }
    for (size_t i = 0u; i < h->session_count; i++) {
        if (h->sessions[i].active) {
            (void)srmech_plat_tcp_conn_close(&h->sessions[i].conn);
            h->sessions[i].active = 0;
        }
    }
    h->session_count = 0u;
    (void)srmech_plat_mutex_unlock(&h->lock);
}

/* ------------------------------------------------------------------ *
 * Request read + per-route handlers
 * ------------------------------------------------------------------ */

/* Read the request head into h->reqbuf until "\r\n\r\n" (or cap / EOF). On
 * success *total = bytes read, *hdr_end = offset of the "\r\n\r\n" (its first
 * '\r'). Returns SRMECH_ERR_IO on a closed/stalled peer, OVERFLOW if the head
 * exceeds the buffer without terminating. */
static srmech_status_t sse_read_head(srmech_mcp_sse_server_t *h,
        srmech_plat_stream_conn_t *conn, size_t *total, size_t *hdr_end)
{
    size_t got_total = 0u;
    assert(h != NULL && conn != NULL);
    assert(total != NULL && hdr_end != NULL);
    for (;;) {
        size_t n = 0u;
        srmech_status_t rc = srmech_plat_tcp_read_some(
            conn, h->reqbuf + got_total, SSE_REQ_CAP - got_total, &n);
        if (rc != SRMECH_OK) {
            return rc;
        }
        if (n == 0u) {
            return SRMECH_ERR_IO;   /* EOF before end-of-headers */
        }
        got_total += n;
        /* rescan from a small overlap so a split "\r\n\r\n" is still found */
        size_t scan_from = (got_total > n + 3u) ? (got_total - n - 3u) : 0u;
        for (size_t i = scan_from; i + 3u < got_total; i++) {
            if (h->reqbuf[i] == '\r' && h->reqbuf[i + 1u] == '\n'
                && h->reqbuf[i + 2u] == '\r' && h->reqbuf[i + 3u] == '\n') {
                *total = got_total;
                *hdr_end = i;
                return SRMECH_OK;
            }
        }
        if (got_total >= SSE_REQ_CAP) {
            return SRMECH_ERR_OVERFLOW;
        }
    }
}

/* GET /sse: write the SSE headers + the `endpoint` event, register the session,
 * and LEAVE the connection open (the registry owns it). *keep := 1 on success
 * so the accept loop does not close it. */
static srmech_status_t sse_handle_get_sse(srmech_mcp_sse_server_t *h,
        srmech_plat_stream_conn_t *conn, int *keep)
{
    char id[SSE_ID_CAP];
    char endpoint[SSE_ID_CAP + 24];
    size_t flen = 0u;
    assert(h != NULL && conn != NULL && keep != NULL);
    *keep = 0;
    srmech_status_t rc = srmech_plat_mutex_lock(&h->lock);
    if (rc != SRMECH_OK) {
        return rc;
    }
    rc = sse_register_locked(h, conn, id, sizeof id);
    (void)srmech_plat_mutex_unlock(&h->lock);
    if (rc != SRMECH_OK) {
        return rc;   /* registry full → caller closes the connection */
    }
    rc = sse_write_cstr(conn,
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: text/event-stream\r\n"
        "Cache-Control: no-cache\r\n"
        "Connection: keep-alive\r\n"
        "X-Accel-Buffering: no\r\n\r\n");
    if (rc != SRMECH_OK) {
        return rc;
    }
    int n = snprintf(endpoint, sizeof endpoint, "/message?session=%s", id);
    assert(n > 0 && (size_t)n < (int)sizeof endpoint);
    rc = sse_frame_event(h->framebuf, SSE_FRAME_CAP, "endpoint",
                         endpoint, (size_t)n, &flen);
    if (rc != SRMECH_OK) {
        return rc;
    }
    rc = srmech_plat_tcp_write_all(
        conn, (const unsigned char *)h->framebuf, flen);
    if (rc == SRMECH_OK) {
        *keep = 1;   /* success — the session keeps the connection open */
    }
    return rc;
}

/* POST /message: look up the session, read the body, dispatch via
 * srmech_mcp_handle (defer_calls==0), push the response over the session's SSE
 * stream, and write 202 on the POST connection. */
static srmech_status_t sse_handle_post(srmech_mcp_sse_server_t *h,
        srmech_plat_stream_conn_t *conn, const sse_req_t *r,
        size_t total, size_t hdr_end)
{
    char id[SSE_ID_CAP];
    assert(h != NULL && conn != NULL && r != NULL);
    assert(total >= hdr_end);
    if (!sse_query_session(r->query, r->query_len, id, sizeof id)) {
        return sse_write_json_response(conn, h->framebuf, SSE_FRAME_CAP, 400,
            "Bad Request", "{\"error\": \"missing 'session' query-string parameter\"}");
    }
    /* body: what's already buffered after the head + more up to content_length */
    size_t body_start = hdr_end + 4u;
    size_t have = total - body_start;
    long want = (r->content_length >= 0) ? r->content_length : (long)have;
    size_t body_len = (size_t)want;
    if (body_len > SSE_REQ_CAP - body_start) {
        body_len = SSE_REQ_CAP - body_start;   /* bounded */
    }
    while (have < body_len) {
        size_t n = 0u;
        srmech_status_t rrc = srmech_plat_tcp_read_some(
            conn, h->reqbuf + body_start + have, body_len - have, &n);
        if (rrc != SRMECH_OK || n == 0u) {
            break;
        }
        have += n;
    }
    size_t out_len = 0u;
    int kind = 0;
    srmech_status_t rc = srmech_mcp_handle(
        (const char *)(h->reqbuf + body_start), have, h->ws, SSE_WS_CAP,
        h->respbuf, SSE_RESP_CAP, &out_len, &kind, 0);
    if (rc == SRMECH_OK && kind == SRMECH_MCP_RESPONSE && out_len > 0u) {
        (void)sse_push_message(h, id, h->respbuf, out_len);
    }
    return sse_write_cstr(conn, "HTTP/1.1 202 Accepted\r\n"
                                "Content-Length: 0\r\n"
                                "Connection: close\r\n\r\n");
}

/* Serve one accepted connection: read + parse the request, route it. On a
 * successfully-registered GET /sse, *keep := 1 (the accept loop leaves the
 * connection open); otherwise the caller closes it. */
static void sse_serve_connection(srmech_mcp_sse_server_t *h,
        srmech_plat_stream_conn_t *conn, int *keep)
{
    size_t total = 0u, hdr_end = 0u;
    sse_req_t r;
    assert(h != NULL && conn != NULL && keep != NULL);
    assert(h->reqbuf != NULL && h->framebuf != NULL);
    *keep = 0;
    if (sse_read_head(h, conn, &total, &hdr_end) != SRMECH_OK) {
        return;
    }
    sse_parse_request((const char *)h->reqbuf, hdr_end, &r);
    if (r.method == 0 && sse_ci_eq(r.path, r.path_len, "/sse")) {
        (void)sse_handle_get_sse(h, conn, keep);
    } else if (r.method == 0 && sse_ci_eq(r.path, r.path_len, "/healthz")) {
        (void)sse_write_json_response(conn, h->framebuf, SSE_FRAME_CAP, 200,
            "OK", "{\"status\": \"ok\"}");
    } else if (r.method == 1 && sse_ci_eq(r.path, r.path_len, "/message")) {
        (void)sse_handle_post(h, conn, &r, total, hdr_end);
    } else {
        (void)sse_write_json_response(conn, h->framebuf, SSE_FRAME_CAP, 404,
            "Not Found", "{\"error\": \"unknown path\"}");
    }
}

/* ------------------------------------------------------------------ *
 * Threads: the accept loop + the keepalive scanner
 * ------------------------------------------------------------------ */

/* Read the stop flag UNDER the registry mutex so the cross-thread stop_flag
 * accesses are synchronized (TSan-clean — the flag is set under the same lock
 * in sse_request_stop). A lock failure is treated as stop (terminate cleanly). */
static int sse_stopped(srmech_mcp_sse_server_t *h)
{
    int stopped;
    assert(h != NULL);
    assert(h->lock.initialized == 1);
    if (srmech_plat_mutex_lock(&h->lock) != SRMECH_OK) {
        return 1;
    }
    stopped = h->stop_flag;
    (void)srmech_plat_mutex_unlock(&h->lock);
    return stopped;
}

/* Set the stop flag UNDER the mutex (synchronizes with sse_stopped). */
static void sse_request_stop(srmech_mcp_sse_server_t *h)
{
    assert(h != NULL);
    assert(h->lock.initialized == 1);
    if (srmech_plat_mutex_lock(&h->lock) == SRMECH_OK) {
        h->stop_flag = 1;
        (void)srmech_plat_mutex_unlock(&h->lock);
    }
}

static void sse_accept_loop(void *arg)
{
    srmech_mcp_sse_server_t *h = (srmech_mcp_sse_server_t *)arg;
    assert(h != NULL);
    assert(h->reqbuf != NULL);
    while (!sse_stopped(h)) {
        srmech_plat_stream_conn_t conn;
        int got = 0;
        srmech_status_t rc = srmech_plat_tcp_accept(
            &h->listener, &conn, SSE_ACCEPT_POLL_MS, &got);
        if (rc != SRMECH_OK) {
            break;   /* listener closed at teardown / fatal accept error */
        }
        if (!got) {
            continue;   /* poll timeout — re-check stop_flag */
        }
        int keep = 0;
        sse_serve_connection(h, &conn, &keep);
        if (!keep) {
            (void)srmech_plat_tcp_conn_close(&conn);
        }
    }
}

static void sse_keepalive_loop(void *arg)
{
    srmech_mcp_sse_server_t *h = (srmech_mcp_sse_server_t *)arg;
    assert(h != NULL);
    assert(h->framebuf != NULL);
    while (!sse_stopped(h)) {
        (void)srmech_plat_sleep_ms(SSE_ACCEPT_POLL_MS);
        if (sse_stopped(h)) {
            break;
        }
        int64_t now_ns = 0;
        (void)srmech_plat_now_ns(&now_ns);
        if (srmech_plat_mutex_lock(&h->lock) != SRMECH_OK) {
            break;
        }
        for (size_t i = 0u; i < h->session_count; i++) {
            sse_session_t *s = &h->sessions[i];
            if (s->active && now_ns - s->last_write_ns >= SSE_KEEPALIVE_NS) {
                (void)srmech_plat_tcp_write_all(
                    &s->conn, (const unsigned char *)": keepalive\n\n", 13u);
                s->last_write_ns = now_ns;
            }
        }
        (void)srmech_plat_mutex_unlock(&h->lock);
    }
}

/* ------------------------------------------------------------------ *
 * Setup / teardown
 * ------------------------------------------------------------------ */

static void sse_free_server(srmech_mcp_sse_server_t *h)
{
    assert(h != NULL);
    assert(h->session_count <= SSE_MAX_SESSIONS);
    free(h->reqbuf);
    free(h->ws);
    free(h->respbuf);
    free(h->framebuf);
    free(h);
}

/* Allocate the server handle + its once-only scratch buffers (cold path). */
static srmech_mcp_sse_server_t *sse_alloc_server(void)
{
    srmech_mcp_sse_server_t *h =
        (srmech_mcp_sse_server_t *)calloc(1, sizeof(srmech_mcp_sse_server_t));
    if (h == NULL) {
        return NULL;
    }
    assert(h != NULL);
    assert(SSE_FRAME_CAP >= SSE_RESP_CAP);
    h->reqbuf = (unsigned char *)malloc(SSE_REQ_CAP);
    h->ws = malloc(SSE_WS_CAP);
    h->respbuf = (char *)malloc(SSE_RESP_CAP);
    h->framebuf = (char *)malloc(SSE_FRAME_CAP);
    if (h->reqbuf == NULL || h->ws == NULL || h->respbuf == NULL
        || h->framebuf == NULL) {
        sse_free_server(h);
        return NULL;
    }
    return h;
}

/* Spawn the accept + keepalive threads. On a PARTIAL failure (accept up but
 * keepalive spawn failed) stop + JOIN the accept thread so no worker outlives
 * the handle (the poll-gated accept exits within one tick of the stop flag).
 * The listener is left for the caller to close exactly once. */
static srmech_status_t sse_start_threads(srmech_mcp_sse_server_t *h)
{
    assert(h != NULL);
    assert(h->accept_running == 0 && h->keepalive_running == 0);
    if (srmech_plat_thread_spawn(sse_accept_loop, h, &h->accept_thread)
            != SRMECH_OK) {
        return SRMECH_ERR_INTERNAL;
    }
    h->accept_running = 1;
    if (srmech_plat_thread_spawn(sse_keepalive_loop, h, &h->keepalive_thread)
            != SRMECH_OK) {
        sse_request_stop(h);
        (void)srmech_plat_thread_join(&h->accept_thread);
        h->accept_running = 0;
        return SRMECH_ERR_INTERNAL;
    }
    h->keepalive_running = 1;
    return SRMECH_OK;
}

srmech_status_t srmech_mcp_sse_serve(const char *host, uint16_t port,
                                     srmech_mcp_sse_server_t **out_handle)
{
    if (host == NULL || out_handle == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(host != NULL && out_handle != NULL);
    assert(SSE_MAX_SESSIONS > 0u);
    *out_handle = NULL;
    if (!srmech_plat_has_tcp() || !srmech_plat_has_threads()) {
        return SRMECH_ERR_BAD_INPUT;   /* POSIX-first; Python runs the pure server */
    }
    srmech_mcp_sse_server_t *h = sse_alloc_server();
    if (h == NULL) {
        return SRMECH_ERR_INTERNAL;
    }
    assert(h->reqbuf != NULL);
    if (srmech_plat_mutex_init(&h->lock) != SRMECH_OK) {
        sse_free_server(h);
        return SRMECH_ERR_INTERNAL;
    }
    srmech_status_t rc = srmech_plat_tcp_listen(host, port, &h->listener, &h->port);
    if (rc != SRMECH_OK) {
        (void)srmech_plat_mutex_destroy(&h->lock);
        sse_free_server(h);
        return rc;
    }
    rc = sse_start_threads(h);
    if (rc != SRMECH_OK) {
        (void)srmech_plat_tcp_server_close(&h->listener);   /* close once */
        (void)srmech_plat_mutex_destroy(&h->lock);
        sse_free_server(h);
        return rc;
    }
    *out_handle = h;
    return SRMECH_OK;
}

uint16_t srmech_mcp_sse_port(const srmech_mcp_sse_server_t *h)
{
    if (h == NULL) {   /* rc187 discipline: runtime NULL-check, no assert-abort */
        return 0u;
    }
    return h->port;
}

srmech_status_t srmech_mcp_sse_stop(srmech_mcp_sse_server_t *h)
{
    if (h == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(h != NULL);
    assert(h->accept_running == 0 || h->accept_running == 1);
    sse_request_stop(h);   /* set stop_flag under the lock (synchronized) */
    (void)srmech_plat_tcp_server_close(&h->listener);   /* unblocks accept poll */
    if (h->accept_running) {
        (void)srmech_plat_thread_join(&h->accept_thread);
        h->accept_running = 0;
    }
    if (h->keepalive_running) {
        (void)srmech_plat_thread_join(&h->keepalive_thread);
        h->keepalive_running = 0;
    }
    sse_close_all_sessions(h);
    (void)srmech_plat_mutex_destroy(&h->lock);
    sse_free_server(h);
    return SRMECH_OK;
}

srmech_status_t srmech_mcp_serve_http_sse(const char *host, uint16_t port)
{
    srmech_mcp_sse_server_t *h = NULL;
    srmech_status_t rc = srmech_mcp_sse_serve(host, port, &h);
    if (rc != SRMECH_OK) {
        return rc;
    }
    assert(h != NULL);
    assert(h->keepalive_running == 0 || h->keepalive_running == 1);
    /* Serve forever: join the accept thread (returns only when the listener
     * closes — a bare-C host main runs until the process is signalled). Sole
     * owner of `h`, so no concurrent stop → no double-free. */
    if (h->accept_running) {
        (void)srmech_plat_thread_join(&h->accept_thread);
        h->accept_running = 0;
    }
    sse_request_stop(h);
    if (h->keepalive_running) {
        (void)srmech_plat_thread_join(&h->keepalive_thread);
        h->keepalive_running = 0;
    }
    sse_close_all_sessions(h);
    (void)srmech_plat_mutex_destroy(&h->lock);
    sse_free_server(h);
    return SRMECH_OK;
}
