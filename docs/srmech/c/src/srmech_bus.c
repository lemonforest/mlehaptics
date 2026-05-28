/*
 * srmech_bus.c — Cross-process IPC for srmech.bus (v0.5.0rc2)
 *
 * The C peer for srmech.bus. Five public symbols
 * (srmech_bus_serve / srmech_bus_server_stop / srmech_bus_connect /
 *  srmech_bus_send_recv / srmech_bus_client_close) plus one
 * function-pointer typedef (srmech_bus_handler_callback_t).
 *
 * Transport:
 *   POSIX  : AF_UNIX socket bound at ~/.srmech/bus-<name>.sock.
 *   Windows: named pipe at \\.\pipe\srmech-<name>.
 *
 * Framing: 4-byte big-endian length prefix + payload bytes.
 *
 * Handler dispatch: caller-provided function-pointer callback (same
 * pattern as v0.4.5rc8's srmech_cascade_chiral_dual_f64). The Python
 * ctypes layer wraps this typedef via ctypes.CFUNCTYPE to marshal
 * arbitrary Python callables.
 *
 * JPL Power-of-Ten discipline:
 *   - Rule 1 (no goto): clean control flow, early returns only.
 *   - Rule 3 (no malloc in hot path): the per-server workspace is
 *     allocated once at srmech_bus_serve entry and freed at
 *     srmech_bus_server_stop. The accept loop reuses the same
 *     workspace across all accepted connections (no per-connection
 *     allocation other than the OS-side connection state itself).
 *   - Rule 4 (functions ≤ 60 lines): each public surface is split
 *     into small helpers.
 *   - Rule 5 (≥2 asserts per non-exempt function).
 *   - Rule 8 (no multi-line macros).
 *
 * License: GPL-3.0-or-later.
 */

#include "srmech.h"

#include <assert.h>
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#if defined(_WIN32) || defined(_WIN64)
#  define SRMECH_BUS_PLATFORM_WIN 1
#  include <windows.h>
#  include <stdio.h>
#else
#  define SRMECH_BUS_PLATFORM_POSIX 1
#  include <pthread.h>
#  include <sys/socket.h>
#  include <sys/stat.h>
#  include <sys/types.h>
#  include <sys/un.h>
#  include <unistd.h>
#endif

/* ------------------------------------------------------------------ *
 * Constants
 * ------------------------------------------------------------------ */

#define SRMECH_BUS_FRAME_PREFIX_BYTES 4u
#define SRMECH_BUS_MAX_FRAME_BYTES    (16u * 1024u * 1024u)  /* 16 MiB */
#define SRMECH_BUS_PATH_MAX           512u

/* Per-connection workspace size. Caller-supplied response buffer is
 * separate; this is the request-read buffer the accept loop owns. */
#define SRMECH_BUS_WORKSPACE_BYTES    (1u * 1024u * 1024u)   /* 1 MiB  */

/* ------------------------------------------------------------------ *
 * Opaque handle structs
 * ------------------------------------------------------------------ */

struct srmech_bus_server_handle {
#if SRMECH_BUS_PLATFORM_POSIX
    int                              listen_fd;
    char                             sock_path[SRMECH_BUS_PATH_MAX];
#else
    char                             pipe_path[SRMECH_BUS_PATH_MAX];
    HANDLE                           pending_handle;
#endif
    int                              stop_flag;
    srmech_bus_handler_callback_t    handler;
    void                            *user_data;
    uint8_t                         *workspace;
    /* response_buf is sized large enough for typical bus events.
     * Callers needing larger replies should split via streaming
     * (rc3 wire format will introduce splice/extend). */
    uint8_t                         *response_buf;
    size_t                           response_cap;
};

struct srmech_bus_client_handle {
#if SRMECH_BUS_PLATFORM_POSIX
    int     fd;
#else
    HANDLE  handle;
#endif
};

/* ------------------------------------------------------------------ *
 * Path builders — POSIX socket path / Windows pipe path
 * ------------------------------------------------------------------ */

#if SRMECH_BUS_PLATFORM_POSIX
static srmech_status_t srmech_bus__build_sock_path(const char *name,
                                                    char       *out,
                                                    size_t      cap)
{
    assert(name != NULL);
    assert(out != NULL);
    const char *home = getenv("HOME");
    if (home == NULL || home[0] == '\0') {
        return SRMECH_ERR_BAD_INPUT;
    }
    int n = snprintf(out, cap, "%s/.srmech/bus-%s.sock", home, name);
    if (n < 0 || (size_t)n >= cap) {
        return SRMECH_ERR_OVERFLOW;
    }
    return SRMECH_OK;
}

static srmech_status_t srmech_bus__ensure_dir(const char *home)
{
    assert(home != NULL);
    char dir[SRMECH_BUS_PATH_MAX];
    int n = snprintf(dir, sizeof(dir), "%s/.srmech", home);
    if (n < 0 || (size_t)n >= sizeof(dir)) {
        return SRMECH_ERR_OVERFLOW;
    }
    (void)mkdir(dir, 0700);  /* idempotent; EEXIST OK */
    return SRMECH_OK;
}
#else
static srmech_status_t srmech_bus__build_pipe_path(const char *name,
                                                    char       *out,
                                                    size_t      cap)
{
    assert(name != NULL);
    assert(out != NULL);
    int n = snprintf(out, cap, "\\\\.\\pipe\\srmech-%s", name);
    if (n < 0 || (size_t)n >= cap) {
        return SRMECH_ERR_OVERFLOW;
    }
    return SRMECH_OK;
}
#endif

/* ------------------------------------------------------------------ *
 * Framed I/O — 4-byte BE length prefix + payload
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

#if SRMECH_BUS_PLATFORM_POSIX
static srmech_status_t srmech_bus__read_exact_fd(int fd,
                                                  uint8_t *buf,
                                                  size_t n)
{
    assert(buf != NULL || n == 0);
    size_t got = 0;
    while (got < n) {
        ssize_t r = read(fd, buf + got, n - got);
        if (r < 0) {
            if (errno == EINTR) {
                continue;
            }
            return SRMECH_ERR_IO;
        }
        if (r == 0) {
            return SRMECH_ERR_IO;  /* EOF mid-frame */
        }
        got += (size_t)r;
    }
    return SRMECH_OK;
}

static srmech_status_t srmech_bus__write_all_fd(int fd,
                                                 const uint8_t *buf,
                                                 size_t n)
{
    assert(buf != NULL || n == 0);
    size_t sent = 0;
    while (sent < n) {
        ssize_t w = write(fd, buf + sent, n - sent);
        if (w < 0) {
            if (errno == EINTR) {
                continue;
            }
            return SRMECH_ERR_IO;
        }
        sent += (size_t)w;
    }
    return SRMECH_OK;
}
#else
static srmech_status_t srmech_bus__read_exact_handle(HANDLE h,
                                                      uint8_t *buf,
                                                      size_t n)
{
    assert(buf != NULL || n == 0);
    DWORD got_total = 0;
    while (got_total < n) {
        DWORD got = 0;
        BOOL ok = ReadFile(h, buf + got_total,
                           (DWORD)(n - got_total), &got, NULL);
        if (!ok || got == 0) {
            return SRMECH_ERR_IO;
        }
        got_total += got;
    }
    return SRMECH_OK;
}

static srmech_status_t srmech_bus__write_all_handle(HANDLE h,
                                                     const uint8_t *buf,
                                                     size_t n)
{
    assert(buf != NULL || n == 0);
    DWORD sent_total = 0;
    while (sent_total < n) {
        DWORD sent = 0;
        BOOL ok = WriteFile(h, buf + sent_total,
                            (DWORD)(n - sent_total), &sent, NULL);
        if (!ok || sent == 0) {
            return SRMECH_ERR_IO;
        }
        sent_total += sent;
    }
    /* NOTE: NO FlushFileBuffers on a named pipe — it blocks until
     * the peer ALSO flushes (per Microsoft KB), which deadlocks the
     * request-reply pattern. WriteFile in PIPE_WAIT byte-mode is
     * already synchronous: bytes are visible to peer ReadFile as
     * soon as WriteFile returns. */
    return SRMECH_OK;
}
#endif

/* ------------------------------------------------------------------ *
 * Per-connection worker: read one request, dispatch, write reply.
 * Loops until peer closes. JPL Rule 4: split into two helpers.
 * ------------------------------------------------------------------ */

#if SRMECH_BUS_PLATFORM_POSIX
static srmech_status_t srmech_bus__service_request_posix(
    srmech_bus_server_handle_t *h, int conn_fd)
{
    assert(h != NULL);
    assert(conn_fd >= 0);
    uint8_t prefix[SRMECH_BUS_FRAME_PREFIX_BYTES];
    srmech_status_t rc = srmech_bus__read_exact_fd(
        conn_fd, prefix, sizeof(prefix));
    if (rc != SRMECH_OK) {
        return rc;  /* clean EOF or I/O error */
    }
    uint32_t plen = srmech_bus__read_u32_be(prefix);
    if (plen > SRMECH_BUS_WORKSPACE_BYTES) {
        return SRMECH_ERR_OVERFLOW;
    }
    rc = srmech_bus__read_exact_fd(conn_fd, h->workspace, plen);
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
    rc = srmech_bus__write_all_fd(
        conn_fd, out_prefix, sizeof(out_prefix));
    if (rc != SRMECH_OK) {
        return rc;
    }
    return srmech_bus__write_all_fd(conn_fd, h->response_buf, resp_len);
}

static void srmech_bus__connection_loop_posix(
    srmech_bus_server_handle_t *h, int conn_fd)
{
    assert(h != NULL);
    assert(conn_fd >= 0);
    while (!h->stop_flag) {
        srmech_status_t rc = srmech_bus__service_request_posix(h, conn_fd);
        if (rc != SRMECH_OK) {
            break;  /* peer closed or I/O error */
        }
    }
    (void)close(conn_fd);
}
#else
static srmech_status_t srmech_bus__service_request_win(
    srmech_bus_server_handle_t *h, HANDLE conn_h)
{
    assert(h != NULL);
    assert(conn_h != INVALID_HANDLE_VALUE);
    uint8_t prefix[SRMECH_BUS_FRAME_PREFIX_BYTES];
    srmech_status_t rc = srmech_bus__read_exact_handle(
        conn_h, prefix, sizeof(prefix));
    if (rc != SRMECH_OK) {
        return rc;
    }
    uint32_t plen = srmech_bus__read_u32_be(prefix);
    if (plen > SRMECH_BUS_WORKSPACE_BYTES) {
        return SRMECH_ERR_OVERFLOW;
    }
    rc = srmech_bus__read_exact_handle(conn_h, h->workspace, plen);
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
    rc = srmech_bus__write_all_handle(
        conn_h, out_prefix, sizeof(out_prefix));
    if (rc != SRMECH_OK) {
        return rc;
    }
    return srmech_bus__write_all_handle(conn_h, h->response_buf, resp_len);
}

static void srmech_bus__connection_loop_win(
    srmech_bus_server_handle_t *h, HANDLE conn_h)
{
    assert(h != NULL);
    assert(conn_h != INVALID_HANDLE_VALUE);
    while (!h->stop_flag) {
        srmech_status_t rc = srmech_bus__service_request_win(h, conn_h);
        if (rc != SRMECH_OK) {
            break;
        }
    }
    (void)DisconnectNamedPipe(conn_h);
    (void)CloseHandle(conn_h);
}
#endif

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

#if SRMECH_BUS_PLATFORM_POSIX
static srmech_status_t srmech_bus__init_server_posix(
    srmech_bus_server_handle_t *h, const char *name)
{
    assert(h != NULL);
    assert(name != NULL);
    h->listen_fd = -1;
    const char *home = getenv("HOME");
    if (home != NULL) {
        (void)srmech_bus__ensure_dir(home);
    }
    srmech_status_t rc = srmech_bus__build_sock_path(
        name, h->sock_path, sizeof(h->sock_path));
    if (rc != SRMECH_OK) {
        return rc;
    }
    (void)unlink(h->sock_path);
    int s = socket(AF_UNIX, SOCK_STREAM, 0);
    if (s < 0) {
        return SRMECH_ERR_IO;
    }
    struct sockaddr_un addr;
    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    size_t pl = strlen(h->sock_path);
    if (pl >= sizeof(addr.sun_path)) {
        (void)close(s);
        return SRMECH_ERR_OVERFLOW;
    }
    memcpy(addr.sun_path, h->sock_path, pl);
    if (bind(s, (struct sockaddr *)&addr, sizeof(addr)) < 0
        || listen(s, 8) < 0)
    {
        (void)close(s);
        return SRMECH_ERR_IO;
    }
    (void)chmod(h->sock_path, 0600);
    h->listen_fd = s;
    return SRMECH_OK;
}
#else
static srmech_status_t srmech_bus__init_server_win(
    srmech_bus_server_handle_t *h, const char *name)
{
    assert(h != NULL);
    assert(name != NULL);
    srmech_status_t rc = srmech_bus__build_pipe_path(
        name, h->pipe_path, sizeof(h->pipe_path));
    if (rc != SRMECH_OK) {
        return rc;
    }
    h->pending_handle = INVALID_HANDLE_VALUE;
    return SRMECH_OK;
}
#endif

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
    srmech_bus_server_handle_t *h =
        srmech_bus__alloc_server_handle(handler, user_data);
    if (h == NULL) {
        return SRMECH_ERR_INTERNAL;
    }
#if SRMECH_BUS_PLATFORM_POSIX
    srmech_status_t rc = srmech_bus__init_server_posix(h, name);
#else
    srmech_status_t rc = srmech_bus__init_server_win(h, name);
#endif
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
#if SRMECH_BUS_PLATFORM_POSIX
    int conn = accept(h->listen_fd, NULL, NULL);
    if (conn < 0) {
        return SRMECH_ERR_IO;
    }
    srmech_bus__connection_loop_posix(h, conn);
    return SRMECH_OK;
#else
    HANDLE pipe_h = CreateNamedPipeA(
        h->pipe_path,
        PIPE_ACCESS_DUPLEX,
        PIPE_TYPE_BYTE | PIPE_READMODE_BYTE | PIPE_WAIT,
        PIPE_UNLIMITED_INSTANCES,
        65536, 65536, 0, NULL);
    if (pipe_h == INVALID_HANDLE_VALUE) {
        return SRMECH_ERR_IO;
    }
    h->pending_handle = pipe_h;
    BOOL ok = ConnectNamedPipe(pipe_h, NULL);
    DWORD le = ok ? 0 : GetLastError();
    if (!ok && le != ERROR_PIPE_CONNECTED) {
        (void)CloseHandle(pipe_h);
        h->pending_handle = INVALID_HANDLE_VALUE;
        return SRMECH_ERR_IO;
    }
    h->pending_handle = INVALID_HANDLE_VALUE;
    srmech_bus__connection_loop_win(h, pipe_h);
    return SRMECH_OK;
#endif
}

srmech_status_t srmech_bus_server_stop(srmech_bus_server_handle_t *h)
{
    if (h == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(h != NULL);
    assert(h->workspace != NULL);
    h->stop_flag = 1;
#if SRMECH_BUS_PLATFORM_POSIX
    if (h->listen_fd >= 0) {
        (void)close(h->listen_fd);
        h->listen_fd = -1;
    }
    (void)unlink(h->sock_path);
#else
    if (h->pending_handle != INVALID_HANDLE_VALUE) {
        (void)DisconnectNamedPipe(h->pending_handle);
        (void)CloseHandle(h->pending_handle);
        h->pending_handle = INVALID_HANDLE_VALUE;
    }
#endif
    free(h->workspace);
    free(h->response_buf);
    free(h);
    return SRMECH_OK;
}

#if SRMECH_BUS_PLATFORM_POSIX
static srmech_status_t srmech_bus__client_connect_posix(
    const char *name, srmech_bus_client_handle_t *c)
{
    assert(name != NULL);
    assert(c != NULL);
    char path[SRMECH_BUS_PATH_MAX];
    srmech_status_t rc = srmech_bus__build_sock_path(
        name, path, sizeof(path));
    if (rc != SRMECH_OK) {
        return rc;
    }
    int s = socket(AF_UNIX, SOCK_STREAM, 0);
    if (s < 0) {
        return SRMECH_ERR_IO;
    }
    struct sockaddr_un addr;
    memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    size_t pl = strlen(path);
    if (pl >= sizeof(addr.sun_path)) {
        (void)close(s);
        return SRMECH_ERR_OVERFLOW;
    }
    memcpy(addr.sun_path, path, pl);
    if (connect(s, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        (void)close(s);
        return SRMECH_ERR_IO;
    }
    c->fd = s;
    return SRMECH_OK;
}
#else
static srmech_status_t srmech_bus__client_connect_win(
    const char *name, srmech_bus_client_handle_t *c)
{
    assert(name != NULL);
    assert(c != NULL);
    char path[SRMECH_BUS_PATH_MAX];
    srmech_status_t rc = srmech_bus__build_pipe_path(
        name, path, sizeof(path));
    if (rc != SRMECH_OK) {
        return rc;
    }
    HANDLE h = CreateFileA(path,
                           GENERIC_READ | GENERIC_WRITE,
                           0, NULL, OPEN_EXISTING, 0, NULL);
    if (h == INVALID_HANDLE_VALUE) {
        DWORD le = GetLastError();
        if (le == ERROR_PIPE_BUSY) {
            (void)WaitNamedPipeA(path, 2000);
            h = CreateFileA(path,
                            GENERIC_READ | GENERIC_WRITE,
                            0, NULL, OPEN_EXISTING, 0, NULL);
        }
    }
    if (h == INVALID_HANDLE_VALUE) {
        return SRMECH_ERR_IO;
    }
    c->handle = h;
    return SRMECH_OK;
}
#endif

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
    srmech_bus_client_handle_t *c =
        (srmech_bus_client_handle_t *)calloc(
            1, sizeof(srmech_bus_client_handle_t));
    if (c == NULL) {
        return SRMECH_ERR_INTERNAL;
    }
#if SRMECH_BUS_PLATFORM_POSIX
    srmech_status_t rc = srmech_bus__client_connect_posix(name, c);
#else
    srmech_status_t rc = srmech_bus__client_connect_win(name, c);
#endif
    if (rc != SRMECH_OK) {
        free(c);
        return rc;
    }
    *out_handle = c;
    return SRMECH_OK;
}

#if SRMECH_BUS_PLATFORM_POSIX
static srmech_status_t srmech_bus__send_recv_posix(
    srmech_bus_client_handle_t *h,
    const uint8_t *request, size_t request_len,
    uint8_t *response, size_t *response_len_inout)
{
    assert(h != NULL);
    assert(response_len_inout != NULL);
    uint8_t prefix[SRMECH_BUS_FRAME_PREFIX_BYTES];
    srmech_bus__write_u32_be(prefix, (uint32_t)request_len);
    srmech_status_t rc = srmech_bus__write_all_fd(
        h->fd, prefix, sizeof(prefix));
    if (rc != SRMECH_OK) {
        return rc;
    }
    rc = srmech_bus__write_all_fd(h->fd, request, request_len);
    if (rc != SRMECH_OK) {
        return rc;
    }
    rc = srmech_bus__read_exact_fd(h->fd, prefix, sizeof(prefix));
    if (rc != SRMECH_OK) {
        return rc;
    }
    uint32_t rlen = srmech_bus__read_u32_be(prefix);
    if (rlen > *response_len_inout) {
        return SRMECH_ERR_OVERFLOW;
    }
    rc = srmech_bus__read_exact_fd(h->fd, response, rlen);
    if (rc != SRMECH_OK) {
        return rc;
    }
    *response_len_inout = rlen;
    return SRMECH_OK;
}
#else
static srmech_status_t srmech_bus__send_recv_win(
    srmech_bus_client_handle_t *h,
    const uint8_t *request, size_t request_len,
    uint8_t *response, size_t *response_len_inout)
{
    assert(h != NULL);
    assert(response_len_inout != NULL);
    uint8_t prefix[SRMECH_BUS_FRAME_PREFIX_BYTES];
    srmech_bus__write_u32_be(prefix, (uint32_t)request_len);
    srmech_status_t rc = srmech_bus__write_all_handle(
        h->handle, prefix, sizeof(prefix));
    if (rc != SRMECH_OK) {
        return rc;
    }
    rc = srmech_bus__write_all_handle(h->handle, request, request_len);
    if (rc != SRMECH_OK) {
        return rc;
    }
    rc = srmech_bus__read_exact_handle(h->handle, prefix, sizeof(prefix));
    if (rc != SRMECH_OK) {
        return rc;
    }
    uint32_t rlen = srmech_bus__read_u32_be(prefix);
    if (rlen > *response_len_inout) {
        return SRMECH_ERR_OVERFLOW;
    }
    rc = srmech_bus__read_exact_handle(h->handle, response, rlen);
    if (rc != SRMECH_OK) {
        return rc;
    }
    *response_len_inout = rlen;
    return SRMECH_OK;
}
#endif

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
#if SRMECH_BUS_PLATFORM_POSIX
    return srmech_bus__send_recv_posix(
        h, request, request_len, response, response_len_inout);
#else
    return srmech_bus__send_recv_win(
        h, request, request_len, response, response_len_inout);
#endif
}

srmech_status_t srmech_bus_client_close(srmech_bus_client_handle_t *h)
{
    if (h == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(h != NULL);
#if SRMECH_BUS_PLATFORM_POSIX
    if (h->fd >= 0) {
        (void)close(h->fd);
    }
    assert(h != NULL);
#else
    if (h->handle != INVALID_HANDLE_VALUE && h->handle != NULL) {
        (void)CloseHandle(h->handle);
    }
    assert(h != NULL);
#endif
    free(h);
    return SRMECH_OK;
}
