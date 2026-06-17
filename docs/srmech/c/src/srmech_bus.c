/*
 * srmech_bus.c — Cross-process IPC for srmech.bus (v0.5.0rc2; PAL'd v0.7.5rc5).
 *
 * The C peer for srmech.bus. Five public symbols
 * (srmech_bus_serve / srmech_bus_server_stop / srmech_bus_connect /
 *  srmech_bus_send_recv / srmech_bus_client_close) plus one
 * function-pointer typedef (srmech_bus_handler_callback_t).
 *
 * Transport (v0.7.5rc5): every OS call routes through the Platform
 * Abstraction Layer (srmech_platform.h / .c). This file carries ZERO
 * `#ifdef _WIN32` — it is the last raw-OS surface that became
 * platform-agnostic. The PAL maps the endpoint name to:
 *   POSIX  : AF_UNIX socket bound at ~/.srmech/bus-<name>.sock.
 *   Windows: named pipe at \\.\pipe\srmech-<name>.
 *
 * Framing: 4-byte big-endian length prefix + payload bytes (agnostic;
 * stays here). Handler dispatch: caller-provided function-pointer
 * callback (same pattern as v0.4.5rc8's srmech_cascade_chiral_dual_f64).
 * The Python ctypes layer wraps the typedef via ctypes.CFUNCTYPE.
 *
 * JPL Power-of-Ten discipline:
 *   - Rule 1 (no goto): clean control flow, early returns only.
 *   - Rule 3 (no malloc in hot path): the per-server workspace is
 *     allocated once at srmech_bus_serve entry and freed at
 *     srmech_bus_server_stop. The accept loop reuses the same
 *     workspace across all accepted connections.
 *   - Rule 4 (functions ≤ 60 lines): each public surface is split
 *     into small helpers.
 *   - Rule 5 (≥2 asserts per non-exempt function).
 *   - Rule 8 (no multi-line macros).
 *
 * License: MIT.
 */

#include "srmech.h"
#include "srmech_platform.h"

#include <assert.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

/* ------------------------------------------------------------------ *
 * Constants
 * ------------------------------------------------------------------ */

#define SRMECH_BUS_FRAME_PREFIX_BYTES 4u
#define SRMECH_BUS_MAX_FRAME_BYTES    (16u * 1024u * 1024u)  /* 16 MiB */

/* Per-connection workspace size. Caller-supplied response buffer is
 * separate; this is the request-read buffer the accept loop owns. */
#define SRMECH_BUS_WORKSPACE_BYTES    (1u * 1024u * 1024u)   /* 1 MiB  */

/* ------------------------------------------------------------------ *
 * Opaque handle structs — the OS handle lives inside the PAL types.
 * ------------------------------------------------------------------ */

struct srmech_bus_server_handle {
    srmech_plat_stream_server_t      plat;     /* listener (PAL) */
    int                              stop_flag;
    srmech_bus_handler_callback_t    handler;
    void                            *user_data;
    uint8_t                         *workspace;
    /* response_buf is sized large enough for typical bus events.
     * Callers needing larger replies should split via streaming. */
    uint8_t                         *response_buf;
    size_t                           response_cap;
};

struct srmech_bus_client_handle {
    srmech_plat_stream_conn_t        plat;     /* connection (PAL) */
};

/* ------------------------------------------------------------------ *
 * Framed I/O — 4-byte BE length prefix + payload (OS-agnostic)
 * ------------------------------------------------------------------ */

static void srmech_bus__write_u32_be(uint8_t out[4], uint32_t v)
{
    assert(out != NULL);
    out[0] = (uint8_t)((v >> 24) & 0xFFu);
    out[1] = (uint8_t)((v >> 16) & 0xFFu);
    out[2] = (uint8_t)((v >>  8) & 0xFFu);
    out[3] = (uint8_t)((v      ) & 0xFFu);
}

static uint32_t srmech_bus__read_u32_be(const uint8_t in[4])
{
    assert(in != NULL);
    uint32_t v = 0;
    v |= ((uint32_t)in[0]) << 24;
    v |= ((uint32_t)in[1]) << 16;
    v |= ((uint32_t)in[2]) <<  8;
    v |= ((uint32_t)in[3]);
    return v;
}

/* ------------------------------------------------------------------ *
 * Per-connection worker: read one request, dispatch, write reply.
 * Loops until peer closes. One implementation for every platform —
 * the connection is a PAL stream handle.
 * ------------------------------------------------------------------ */

static srmech_status_t srmech_bus__service_request(
    srmech_bus_server_handle_t *h, srmech_plat_stream_conn_t *conn)
{
    assert(h != NULL);
    assert(conn != NULL);
    uint8_t prefix[SRMECH_BUS_FRAME_PREFIX_BYTES];
    srmech_status_t rc = srmech_plat_stream_read_exact(
        conn, prefix, sizeof prefix);
    if (rc != SRMECH_OK) {
        return rc;  /* clean EOF or I/O error */
    }
    uint32_t plen = srmech_bus__read_u32_be(prefix);
    if (plen > SRMECH_BUS_WORKSPACE_BYTES) {
        return SRMECH_ERR_OVERFLOW;
    }
    rc = srmech_plat_stream_read_exact(conn, h->workspace, plen);
    if (rc != SRMECH_OK) {
        return rc;
    }
    size_t resp_len = h->response_cap;
    srmech_status_t hrc = h->handler(
        h->workspace, plen, h->response_buf, &resp_len, h->user_data);
    if (hrc != SRMECH_OK) {
        return hrc;
    }
    if (resp_len > UINT32_MAX) {
        return SRMECH_ERR_OVERFLOW;
    }
    uint8_t out_prefix[SRMECH_BUS_FRAME_PREFIX_BYTES];
    srmech_bus__write_u32_be(out_prefix, (uint32_t)resp_len);
    rc = srmech_plat_stream_write_all(conn, out_prefix, sizeof out_prefix);
    if (rc != SRMECH_OK) {
        return rc;
    }
    return srmech_plat_stream_write_all(conn, h->response_buf, resp_len);
}

static void srmech_bus__connection_loop(
    srmech_bus_server_handle_t *h, srmech_plat_stream_conn_t *conn)
{
    assert(h != NULL);
    assert(conn != NULL);
    while (!h->stop_flag) {
        srmech_status_t rc = srmech_bus__service_request(h, conn);
        if (rc != SRMECH_OK) {
            break;  /* peer closed or I/O error */
        }
    }
    (void)srmech_plat_stream_conn_close(conn);
}

/* ------------------------------------------------------------------ *
 * Public API
 * ------------------------------------------------------------------ */

/* Allocate the per-server handle + its workspace buffers.
 * Cold-path allocation (JPL Rule 3 — no allocation in hot path).
 * Returns NULL on allocation failure. */
static srmech_bus_server_handle_t *srmech_bus__alloc_server_handle(
    srmech_bus_handler_callback_t handler, void *user_data)
{
    assert(handler != NULL);
    srmech_bus_server_handle_t *h =
        (srmech_bus_server_handle_t *)calloc(
            1, sizeof(srmech_bus_server_handle_t));
    if (h == NULL) {
        return NULL;
    }
    assert(h != NULL);
    h->handler = handler;
    h->user_data = user_data;
    h->stop_flag = 0;
    h->workspace = (uint8_t *)malloc(SRMECH_BUS_WORKSPACE_BYTES);
    h->response_buf = (uint8_t *)malloc(SRMECH_BUS_WORKSPACE_BYTES);
    h->response_cap = SRMECH_BUS_WORKSPACE_BYTES;
    if (h->workspace == NULL || h->response_buf == NULL) {
        free(h->workspace);
        free(h->response_buf);
        free(h);
        return NULL;
    }
    return h;
}

static void srmech_bus__free_server_handle(srmech_bus_server_handle_t *h)
{
    assert(h != NULL);
    assert(h->workspace != NULL || h->response_buf != NULL);
    free(h->workspace);
    free(h->response_buf);
    free(h);
}

srmech_status_t srmech_bus_serve(
    const char                       *name,
    srmech_bus_handler_callback_t     handler,
    void                             *user_data,
    srmech_bus_server_handle_t      **out_handle)
{
    if (name == NULL || handler == NULL || out_handle == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(name != NULL);
    assert(handler != NULL);
    *out_handle = NULL;
    if (!srmech_plat_has_streams()) {
        return SRMECH_ERR_BAD_INPUT;  /* no IPC backend on this target */
    }
    srmech_bus_server_handle_t *h =
        srmech_bus__alloc_server_handle(handler, user_data);
    if (h == NULL) {
        return SRMECH_ERR_INTERNAL;
    }
    srmech_status_t rc = srmech_plat_stream_listen(name, &h->plat);
    if (rc != SRMECH_OK) {
        srmech_bus__free_server_handle(h);
        return rc;
    }
    *out_handle = h;
    return SRMECH_OK;
}

srmech_status_t srmech_bus_server_accept_one(
    srmech_bus_server_handle_t *h)
{
    /* Blocking accept-one helper for tests / single-threaded harnesses.
     * Accepts ONE client, services its requests until peer closes, then
     * returns. Production callers typically spin this in a thread loop
     * (Python side handles thread-per-connection). */
    if (h == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(h != NULL);
    assert(h->handler != NULL);
    srmech_plat_stream_conn_t conn;
    srmech_status_t rc = srmech_plat_stream_accept(&h->plat, &conn);
    if (rc != SRMECH_OK) {
        return rc;
    }
    srmech_bus__connection_loop(h, &conn);
    return SRMECH_OK;
}

srmech_status_t srmech_bus_server_stop(srmech_bus_server_handle_t *h)
{
    if (h == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(h != NULL);
    assert(h->workspace != NULL);
    h->stop_flag = 1;
    (void)srmech_plat_stream_server_close(&h->plat);
    free(h->workspace);
    free(h->response_buf);
    free(h);
    return SRMECH_OK;
}

srmech_status_t srmech_bus_connect(
    const char                       *name,
    srmech_bus_client_handle_t      **out_handle)
{
    if (name == NULL || out_handle == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(name != NULL);
    assert(out_handle != NULL);
    *out_handle = NULL;
    if (!srmech_plat_has_streams()) {
        return SRMECH_ERR_BAD_INPUT;  /* no IPC backend on this target */
    }
    srmech_bus_client_handle_t *c =
        (srmech_bus_client_handle_t *)calloc(
            1, sizeof(srmech_bus_client_handle_t));
    if (c == NULL) {
        return SRMECH_ERR_INTERNAL;
    }
    srmech_status_t rc = srmech_plat_stream_connect(name, &c->plat);
    if (rc != SRMECH_OK) {
        free(c);
        return rc;
    }
    *out_handle = c;
    return SRMECH_OK;
}

static srmech_status_t srmech_bus__send_recv(
    srmech_bus_client_handle_t *h,
    const uint8_t *request, size_t request_len,
    uint8_t *response, size_t *response_len_inout)
{
    assert(h != NULL);
    assert(response_len_inout != NULL);
    uint8_t prefix[SRMECH_BUS_FRAME_PREFIX_BYTES];
    srmech_bus__write_u32_be(prefix, (uint32_t)request_len);
    srmech_status_t rc = srmech_plat_stream_write_all(
        &h->plat, prefix, sizeof prefix);
    if (rc != SRMECH_OK) {
        return rc;
    }
    rc = srmech_plat_stream_write_all(&h->plat, request, request_len);
    if (rc != SRMECH_OK) {
        return rc;
    }
    rc = srmech_plat_stream_read_exact(&h->plat, prefix, sizeof prefix);
    if (rc != SRMECH_OK) {
        return rc;
    }
    uint32_t rlen = srmech_bus__read_u32_be(prefix);
    if (rlen > *response_len_inout) {
        return SRMECH_ERR_OVERFLOW;
    }
    rc = srmech_plat_stream_read_exact(&h->plat, response, rlen);
    if (rc != SRMECH_OK) {
        return rc;
    }
    *response_len_inout = rlen;
    return SRMECH_OK;
}

srmech_status_t srmech_bus_send_recv(
    srmech_bus_client_handle_t       *h,
    const uint8_t                    *request, size_t request_len,
    uint8_t                          *response, size_t *response_len_inout)
{
    if (h == NULL || request == NULL || response == NULL
        || response_len_inout == NULL)
    {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(h != NULL);
    assert(response_len_inout != NULL);
    if (request_len > UINT32_MAX) {
        return SRMECH_ERR_OVERFLOW;
    }
    return srmech_bus__send_recv(
        h, request, request_len, response, response_len_inout);
}

srmech_status_t srmech_bus_client_close(srmech_bus_client_handle_t *h)
{
    if (h == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(h != NULL);
    srmech_status_t rc = srmech_plat_stream_conn_close(&h->plat);
    assert(rc == SRMECH_OK);
    (void)rc;
    free(h);
    return SRMECH_OK;
}
