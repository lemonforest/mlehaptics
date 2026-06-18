/* srmech_platform.c — Platform Abstraction Layer (PAL) implementation.
 *
 * THE single compilation unit carrying OS-specific (`_WIN32` / POSIX)
 * threading code. Everything else in libsrmech calls the agnostic
 * srmech_plat_* API in srmech_platform.h and stays #ifdef-free. See that
 * header for the architectural rationale (PAL : OS :: HAL : CPU).
 *
 * JPL Power-of-Ten: Rule 1 (no goto) OK; Rule 2 (no unbounded loops — none
 * here) OK; Rule 3 (no malloc — the handle lives in caller storage) OK;
 * Rule 4 (≤60-line functions) OK; Rule 5 (≥2 asserts / non-trivial fn) OK;
 * Rule 7 (status returns) OK; Rule 10 (warnings clean) OK.
 *
 * License: MIT.
 */

#include "srmech_platform.h"

#include <assert.h>
#include <stdio.h>    /* snprintf (stream endpoint paths) */
#include <stdlib.h>   /* getenv (POSIX socket path under $HOME) */
#include <string.h>

#if defined(_WIN32) || defined(_WIN64)
#  define SRMECH_PLAT_THREADS_WIN 1
#  define SRMECH_PLAT_STREAM_WIN  1
#  include <windows.h>
#elif defined(__unix__) || defined(__APPLE__) || defined(__linux__)
#  define SRMECH_PLAT_THREADS_POSIX 1
#  define SRMECH_PLAT_STREAM_POSIX  1
#  include <pthread.h>
#  include <errno.h>        /* EINTR (read/write retry) */
#  include <sys/socket.h>   /* AF_UNIX stream IPC */
#  include <sys/stat.h>     /* mkdir / chmod */
#  include <sys/types.h>
#  include <sys/un.h>       /* sockaddr_un */
#  include <unistd.h>       /* read / write / close / unlink */
#  include <dirent.h>       /* opendir / readdir / closedir (rc163 dir iter) */
#endif

#if defined(SRMECH_PLAT_THREADS_POSIX)
_Static_assert(sizeof(pthread_t) <= SRMECH_PLAT_THREAD_STORAGE,
               "pthread_t does not fit srmech_plat_thread handle storage");
#elif defined(SRMECH_PLAT_THREADS_WIN)
_Static_assert(sizeof(HANDLE) <= SRMECH_PLAT_THREAD_STORAGE,
               "HANDLE does not fit srmech_plat_thread handle storage");
#endif

#if defined(SRMECH_PLAT_STREAM_POSIX)
_Static_assert(sizeof(int) <= SRMECH_PLAT_STREAM_STORAGE,
               "fd does not fit srmech_plat_stream handle storage");
#elif defined(SRMECH_PLAT_STREAM_WIN)
_Static_assert(sizeof(HANDLE) <= SRMECH_PLAT_STREAM_STORAGE,
               "HANDLE does not fit srmech_plat_stream handle storage");
#endif

int srmech_plat_has_threads(void)
{
#if defined(SRMECH_PLAT_THREADS_POSIX) || defined(SRMECH_PLAT_THREADS_WIN)
    return 1;
#else
    return 0;   /* thread-less target: callers take the serial path */
#endif
}

#if defined(SRMECH_PLAT_THREADS_POSIX)

static void *srmech_plat__posix_trampoline(void *arg)
{
    assert(arg != NULL);
    srmech_plat_thread_t *t = (srmech_plat_thread_t *)arg;
    assert(t->fn != NULL);
    t->fn(t->arg);
    return NULL;
}

srmech_status_t srmech_plat_thread_spawn(srmech_plat_thread_fn fn, void *arg,
                                         srmech_plat_thread_t *out)
{
    assert(fn != NULL);
    assert(out != NULL);
    if (fn == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    out->fn = fn;
    out->arg = arg;
    pthread_t tid;
    if (pthread_create(&tid, NULL, srmech_plat__posix_trampoline, out) != 0) {
        return SRMECH_ERR_INTERNAL;
    }
    memcpy(out->handle.bytes, &tid, sizeof tid);
    return SRMECH_OK;
}

srmech_status_t srmech_plat_thread_join(srmech_plat_thread_t *handle)
{
    assert(handle != NULL);
    if (handle == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    pthread_t tid;
    assert(sizeof tid <= sizeof handle->handle.bytes);   /* storage invariant */
    memcpy(&tid, handle->handle.bytes, sizeof tid);
    (void)pthread_join(tid, NULL);
    return SRMECH_OK;
}

#elif defined(SRMECH_PLAT_THREADS_WIN)

static DWORD WINAPI srmech_plat__win_trampoline(LPVOID arg)
{
    assert(arg != NULL);
    srmech_plat_thread_t *t = (srmech_plat_thread_t *)arg;
    assert(t->fn != NULL);
    t->fn(t->arg);
    return 0u;
}

srmech_status_t srmech_plat_thread_spawn(srmech_plat_thread_fn fn, void *arg,
                                         srmech_plat_thread_t *out)
{
    assert(fn != NULL);
    assert(out != NULL);
    if (fn == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    out->fn = fn;
    out->arg = arg;
    HANDLE th = CreateThread(NULL, 0, srmech_plat__win_trampoline, out, 0, NULL);
    if (th == NULL) {
        return SRMECH_ERR_INTERNAL;
    }
    memcpy(out->handle.bytes, &th, sizeof th);
    return SRMECH_OK;
}

srmech_status_t srmech_plat_thread_join(srmech_plat_thread_t *handle)
{
    assert(handle != NULL);
    if (handle == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    HANDLE th;
    assert(sizeof th <= sizeof handle->handle.bytes);    /* storage invariant */
    memcpy(&th, handle->handle.bytes, sizeof th);
    (void)WaitForSingleObject(th, INFINITE);
    (void)CloseHandle(th);
    return SRMECH_OK;
}

#else  /* thread-less target (bare-metal microcontroller) */

srmech_status_t srmech_plat_thread_spawn(srmech_plat_thread_fn fn, void *arg,
                                         srmech_plat_thread_t *out)
{
    assert(fn != NULL);
    assert(out != NULL);
    (void)fn;
    (void)arg;
    (void)out;
    return SRMECH_ERR_BAD_INPUT;   /* no backend — caller must run serially */
}

srmech_status_t srmech_plat_thread_join(srmech_plat_thread_t *handle)
{
    assert(handle != NULL);
    assert(srmech_plat_has_threads() == 0);   /* this stub only on thread-less */
    (void)handle;
    return SRMECH_OK;   /* nothing was spawned */
}

#endif

/* ================================================================== *
 * STREAM IPC (rc5) — AF_UNIX socket (POSIX) / named pipe (Windows).
 *
 * The bus's 4-byte-length framing + handler dispatch are OS-agnostic
 * and stay in srmech_bus.c; everything OS-specific is here, behind the
 * srmech_plat_stream_* primitives. The bus carries no #ifdef.
 * ================================================================== */

int srmech_plat_has_streams(void)
{
#if defined(SRMECH_PLAT_STREAM_POSIX) || defined(SRMECH_PLAT_STREAM_WIN)
    return 1;
#else
    return 0;   /* stream-less target: srmech.bus is unavailable */
#endif
}

#if defined(SRMECH_PLAT_STREAM_POSIX)

#define SRMECH_PLAT_STREAM_BACKLOG 8

/* Derive $HOME/.srmech/bus-<name>.sock from the short endpoint name. */
static srmech_status_t srmech_plat__derive_path(const char *name,
                                                char *out, size_t cap)
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

static srmech_status_t srmech_plat__ensure_dir(const char *home)
{
    assert(home != NULL);
    assert(home[0] != '\0');
    char dir[SRMECH_PLAT_STREAM_PATH_MAX];
    int n = snprintf(dir, sizeof dir, "%s/.srmech", home);
    if (n < 0 || (size_t)n >= sizeof dir) {
        return SRMECH_ERR_OVERFLOW;
    }
    (void)mkdir(dir, 0700);   /* idempotent; EEXIST OK */
    return SRMECH_OK;
}

static srmech_status_t srmech_plat__bind_unix(const char *path, int *out_fd)
{
    assert(path != NULL);
    assert(out_fd != NULL);
    int s = socket(AF_UNIX, SOCK_STREAM, 0);
    if (s < 0) {
        return SRMECH_ERR_IO;
    }
    struct sockaddr_un addr;
    memset(&addr, 0, sizeof addr);
    addr.sun_family = AF_UNIX;
    size_t pl = strlen(path);
    if (pl >= sizeof addr.sun_path) {
        (void)close(s);
        return SRMECH_ERR_OVERFLOW;
    }
    memcpy(addr.sun_path, path, pl);
    if (bind(s, (struct sockaddr *)&addr, sizeof addr) < 0
        || listen(s, SRMECH_PLAT_STREAM_BACKLOG) < 0)
    {
        (void)close(s);
        return SRMECH_ERR_IO;
    }
    (void)chmod(path, 0600);
    *out_fd = s;
    return SRMECH_OK;
}

static srmech_status_t srmech_plat__connect_unix(const char *path, int *out_fd)
{
    assert(path != NULL);
    assert(out_fd != NULL);
    int s = socket(AF_UNIX, SOCK_STREAM, 0);
    if (s < 0) {
        return SRMECH_ERR_IO;
    }
    struct sockaddr_un addr;
    memset(&addr, 0, sizeof addr);
    addr.sun_family = AF_UNIX;
    size_t pl = strlen(path);
    if (pl >= sizeof addr.sun_path) {
        (void)close(s);
        return SRMECH_ERR_OVERFLOW;
    }
    memcpy(addr.sun_path, path, pl);
    if (connect(s, (struct sockaddr *)&addr, sizeof addr) < 0) {
        (void)close(s);
        return SRMECH_ERR_IO;
    }
    *out_fd = s;
    return SRMECH_OK;
}

srmech_status_t srmech_plat_stream_listen(const char *name,
                                          srmech_plat_stream_server_t *out)
{
    assert(name != NULL);
    assert(out != NULL);
    if (name == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    memset(out, 0, sizeof *out);
    int listen_fd = -1;
    memcpy(out->handle.bytes, &listen_fd, sizeof listen_fd);
    const char *home = getenv("HOME");
    if (home != NULL && home[0] != '\0') {
        (void)srmech_plat__ensure_dir(home);
    }
    srmech_status_t rc = srmech_plat__derive_path(
        name, out->endpoint_path, sizeof out->endpoint_path);
    if (rc != SRMECH_OK) {
        return rc;
    }
    (void)unlink(out->endpoint_path);
    rc = srmech_plat__bind_unix(out->endpoint_path, &listen_fd);
    if (rc != SRMECH_OK) {
        return rc;
    }
    memcpy(out->handle.bytes, &listen_fd, sizeof listen_fd);
    return SRMECH_OK;
}

srmech_status_t srmech_plat_stream_accept(srmech_plat_stream_server_t *server,
                                          srmech_plat_stream_conn_t *conn_out)
{
    assert(server != NULL);
    assert(conn_out != NULL);
    if (server == NULL || conn_out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    int listen_fd;
    memcpy(&listen_fd, server->handle.bytes, sizeof listen_fd);
    int conn = accept(listen_fd, NULL, NULL);
    if (conn < 0) {
        return SRMECH_ERR_IO;
    }
    memset(conn_out, 0, sizeof *conn_out);
    memcpy(conn_out->handle.bytes, &conn, sizeof conn);
    return SRMECH_OK;
}

srmech_status_t srmech_plat_stream_server_close(
    srmech_plat_stream_server_t *server)
{
    assert(server != NULL);
    if (server == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    int listen_fd;
    assert(sizeof listen_fd <= sizeof server->handle.bytes);
    memcpy(&listen_fd, server->handle.bytes, sizeof listen_fd);
    if (listen_fd >= 0) {
        (void)close(listen_fd);
        listen_fd = -1;
        memcpy(server->handle.bytes, &listen_fd, sizeof listen_fd);
    }
    (void)unlink(server->endpoint_path);
    return SRMECH_OK;
}

srmech_status_t srmech_plat_stream_connect(const char *name,
                                           srmech_plat_stream_conn_t *out)
{
    assert(name != NULL);
    assert(out != NULL);
    if (name == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    char path[SRMECH_PLAT_STREAM_PATH_MAX];
    srmech_status_t rc = srmech_plat__derive_path(name, path, sizeof path);
    if (rc != SRMECH_OK) {
        return rc;
    }
    int fd = -1;
    rc = srmech_plat__connect_unix(path, &fd);
    if (rc != SRMECH_OK) {
        return rc;
    }
    memset(out, 0, sizeof *out);
    memcpy(out->handle.bytes, &fd, sizeof fd);
    return SRMECH_OK;
}

srmech_status_t srmech_plat_stream_read_exact(srmech_plat_stream_conn_t *conn,
                                              unsigned char *buf, size_t n)
{
    assert(conn != NULL);
    assert(buf != NULL || n == 0);
    int fd;
    memcpy(&fd, conn->handle.bytes, sizeof fd);
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
            return SRMECH_ERR_IO;   /* EOF mid-frame */
        }
        got += (size_t)r;
    }
    return SRMECH_OK;
}

srmech_status_t srmech_plat_stream_write_all(srmech_plat_stream_conn_t *conn,
                                             const unsigned char *buf, size_t n)
{
    assert(conn != NULL);
    assert(buf != NULL || n == 0);
    int fd;
    memcpy(&fd, conn->handle.bytes, sizeof fd);
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

srmech_status_t srmech_plat_stream_conn_close(srmech_plat_stream_conn_t *conn)
{
    assert(conn != NULL);
    if (conn == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    int fd;
    assert(sizeof fd <= sizeof conn->handle.bytes);
    memcpy(&fd, conn->handle.bytes, sizeof fd);
    if (fd >= 0) {
        (void)close(fd);
    }
    return SRMECH_OK;
}

#elif defined(SRMECH_PLAT_STREAM_WIN)

/* Derive \\.\pipe\srmech-<name> from the short endpoint name. */
static srmech_status_t srmech_plat__derive_path(const char *name,
                                                char *out, size_t cap)
{
    assert(name != NULL);
    assert(out != NULL);
    int n = snprintf(out, cap, "\\\\.\\pipe\\srmech-%s", name);
    if (n < 0 || (size_t)n >= cap) {
        return SRMECH_ERR_OVERFLOW;
    }
    return SRMECH_OK;
}

static HANDLE srmech_plat__create_pipe_instance(const char *path)
{
    assert(path != NULL);
    assert(path[0] != '\0');
    HANDLE h = CreateNamedPipeA(
        path, PIPE_ACCESS_DUPLEX,
        PIPE_TYPE_BYTE | PIPE_READMODE_BYTE | PIPE_WAIT,
        PIPE_UNLIMITED_INSTANCES, 65536, 65536, 0, NULL);
    return h;
}

srmech_status_t srmech_plat_stream_listen(const char *name,
                                          srmech_plat_stream_server_t *out)
{
    assert(name != NULL);
    assert(out != NULL);
    if (name == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    memset(out, 0, sizeof *out);
    srmech_status_t rc = srmech_plat__derive_path(
        name, out->endpoint_path, sizeof out->endpoint_path);
    if (rc != SRMECH_OK) {
        return rc;
    }
    HANDLE pending = INVALID_HANDLE_VALUE;
    memcpy(out->handle.bytes, &pending, sizeof pending);
    return SRMECH_OK;
}

srmech_status_t srmech_plat_stream_accept(srmech_plat_stream_server_t *server,
                                          srmech_plat_stream_conn_t *conn_out)
{
    assert(server != NULL);
    assert(conn_out != NULL);
    if (server == NULL || conn_out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    HANDLE pipe_h = srmech_plat__create_pipe_instance(server->endpoint_path);
    if (pipe_h == INVALID_HANDLE_VALUE) {
        return SRMECH_ERR_IO;
    }
    memcpy(server->handle.bytes, &pipe_h, sizeof pipe_h);   /* pending */
    BOOL ok = ConnectNamedPipe(pipe_h, NULL);
    DWORD le = ok ? 0u : GetLastError();
    HANDLE invalid = INVALID_HANDLE_VALUE;
    if (!ok && le != ERROR_PIPE_CONNECTED) {
        (void)CloseHandle(pipe_h);
        memcpy(server->handle.bytes, &invalid, sizeof invalid);
        return SRMECH_ERR_IO;
    }
    memcpy(server->handle.bytes, &invalid, sizeof invalid);   /* cleared */
    memset(conn_out, 0, sizeof *conn_out);
    memcpy(conn_out->handle.bytes, &pipe_h, sizeof pipe_h);
    return SRMECH_OK;
}

srmech_status_t srmech_plat_stream_server_close(
    srmech_plat_stream_server_t *server)
{
    assert(server != NULL);
    if (server == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    HANDLE pending;
    assert(sizeof pending <= sizeof server->handle.bytes);
    memcpy(&pending, server->handle.bytes, sizeof pending);
    if (pending != INVALID_HANDLE_VALUE) {
        (void)DisconnectNamedPipe(pending);
        (void)CloseHandle(pending);
        HANDLE invalid = INVALID_HANDLE_VALUE;
        memcpy(server->handle.bytes, &invalid, sizeof invalid);
    }
    return SRMECH_OK;
}

srmech_status_t srmech_plat_stream_connect(const char *name,
                                           srmech_plat_stream_conn_t *out)
{
    assert(name != NULL);
    assert(out != NULL);
    if (name == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    char path[SRMECH_PLAT_STREAM_PATH_MAX];
    srmech_status_t rc = srmech_plat__derive_path(name, path, sizeof path);
    if (rc != SRMECH_OK) {
        return rc;
    }
    HANDLE h = CreateFileA(path, GENERIC_READ | GENERIC_WRITE,
                           0, NULL, OPEN_EXISTING, 0, NULL);
    if (h == INVALID_HANDLE_VALUE && GetLastError() == ERROR_PIPE_BUSY) {
        (void)WaitNamedPipeA(path, 2000);
        h = CreateFileA(path, GENERIC_READ | GENERIC_WRITE,
                        0, NULL, OPEN_EXISTING, 0, NULL);
    }
    if (h == INVALID_HANDLE_VALUE) {
        return SRMECH_ERR_IO;
    }
    memset(out, 0, sizeof *out);
    memcpy(out->handle.bytes, &h, sizeof h);
    return SRMECH_OK;
}

srmech_status_t srmech_plat_stream_read_exact(srmech_plat_stream_conn_t *conn,
                                              unsigned char *buf, size_t n)
{
    assert(conn != NULL);
    assert(buf != NULL || n == 0);
    HANDLE h;
    memcpy(&h, conn->handle.bytes, sizeof h);
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

srmech_status_t srmech_plat_stream_write_all(srmech_plat_stream_conn_t *conn,
                                             const unsigned char *buf, size_t n)
{
    assert(conn != NULL);
    assert(buf != NULL || n == 0);
    HANDLE h;
    memcpy(&h, conn->handle.bytes, sizeof h);
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
    /* NO FlushFileBuffers — it blocks until the peer ALSO flushes (per
     * Microsoft KB), deadlocking request-reply. Byte-mode WriteFile is
     * already synchronously visible to the peer's ReadFile. */
    return SRMECH_OK;
}

srmech_status_t srmech_plat_stream_conn_close(srmech_plat_stream_conn_t *conn)
{
    assert(conn != NULL);
    if (conn == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    HANDLE h;
    assert(sizeof h <= sizeof conn->handle.bytes);
    memcpy(&h, conn->handle.bytes, sizeof h);
    if (h != INVALID_HANDLE_VALUE && h != NULL) {
        (void)DisconnectNamedPipe(h);   /* harmless error on a client handle */
        (void)CloseHandle(h);
    }
    return SRMECH_OK;
}

#else  /* stream-less target (bare-metal): srmech.bus is unavailable */

srmech_status_t srmech_plat_stream_listen(const char *name,
                                          srmech_plat_stream_server_t *out)
{
    assert(name != NULL);
    assert(out != NULL);
    (void)name;
    (void)out;
    return SRMECH_ERR_BAD_INPUT;
}

srmech_status_t srmech_plat_stream_accept(srmech_plat_stream_server_t *server,
                                          srmech_plat_stream_conn_t *conn_out)
{
    assert(server != NULL);
    assert(conn_out != NULL);
    (void)server;
    (void)conn_out;
    return SRMECH_ERR_BAD_INPUT;
}

srmech_status_t srmech_plat_stream_server_close(
    srmech_plat_stream_server_t *server)
{
    assert(server != NULL);
    assert(srmech_plat_has_streams() == 0);
    (void)server;
    return SRMECH_OK;
}

srmech_status_t srmech_plat_stream_connect(const char *name,
                                           srmech_plat_stream_conn_t *out)
{
    assert(name != NULL);
    assert(out != NULL);
    (void)name;
    (void)out;
    return SRMECH_ERR_BAD_INPUT;
}

srmech_status_t srmech_plat_stream_read_exact(srmech_plat_stream_conn_t *conn,
                                              unsigned char *buf, size_t n)
{
    assert(conn != NULL);
    assert(buf != NULL || n == 0);
    (void)conn;
    (void)buf;
    (void)n;
    return SRMECH_ERR_BAD_INPUT;
}

srmech_status_t srmech_plat_stream_write_all(srmech_plat_stream_conn_t *conn,
                                             const unsigned char *buf, size_t n)
{
    assert(conn != NULL);
    assert(buf != NULL || n == 0);
    (void)conn;
    (void)buf;
    (void)n;
    return SRMECH_ERR_BAD_INPUT;
}

srmech_status_t srmech_plat_stream_conn_close(srmech_plat_stream_conn_t *conn)
{
    assert(conn != NULL);
    assert(srmech_plat_has_streams() == 0);
    (void)conn;
    return SRMECH_OK;
}

#endif

/* ================================================================== *
 * FILE I/O (rc161) — portable stdio (fopen/fread/fwrite/fseek), so the
 * POSIX + Windows path is shared; only a bare-metal target (no FS) stubs.
 * stdio.h is already included above. JPL-clean: no goto, no malloc,
 * bounded loops, status returns, >=2 asserts / non-trivial fn.
 * ================================================================== */

#if defined(_WIN32) || defined(_WIN64) || defined(__unix__) \
    || defined(__APPLE__) || defined(__linux__)
#  define SRMECH_PLAT_FILE 1
#endif

int srmech_plat_has_filesystem(void)
{
#if defined(SRMECH_PLAT_FILE)
    return 1;
#else
    return 0;
#endif
}

#if defined(SRMECH_PLAT_FILE)

srmech_status_t srmech_plat_file_read(const char *path, unsigned char *buf,
                                      size_t buf_cap, size_t *out_len)
{
    assert(path != NULL);
    assert(out_len != NULL && (buf != NULL || buf_cap == 0));
    FILE *fp = fopen(path, "rb");
    if (fp == NULL) { return SRMECH_ERR_IO; }
    size_t total = 0;
    int over = 0;
    while (total < buf_cap) {
        size_t got = fread(buf + total, 1u, buf_cap - total, fp);
        if (got == 0u) { break; }
        total += got;
    }
    if (total == buf_cap) {
        unsigned char probe;
        if (fread(&probe, 1u, 1u, fp) != 0u) { over = 1; }
    }
    int err = ferror(fp);   /* a mid-read error must not look like clean EOF */
    fclose(fp);
    if (err) { return SRMECH_ERR_IO; }
    if (over) { return SRMECH_ERR_OVERFLOW; }
    *out_len = total;
    return SRMECH_OK;
}

srmech_status_t srmech_plat_file_read_region(const char *path, size_t offset,
                                             unsigned char *buf, size_t len)
{
    assert(path != NULL);
    assert(buf != NULL || len == 0);
    FILE *fp = fopen(path, "rb");
    if (fp == NULL) { return SRMECH_ERR_IO; }
    if (fseek(fp, (long)offset, SEEK_SET) != 0) {
        fclose(fp);
        return SRMECH_ERR_IO;
    }
    size_t got = (len == 0u) ? 0u : fread(buf, 1u, len, fp);
    fclose(fp);
    return (got == len) ? SRMECH_OK : SRMECH_ERR_IO;
}

srmech_status_t srmech_plat_file_write(const char *path, int append,
                                       const unsigned char *data, size_t len)
{
    assert(path != NULL);
    assert(data != NULL || len == 0);
    FILE *fp = fopen(path, append ? "ab" : "wb");
    if (fp == NULL) { return SRMECH_ERR_IO; }
    size_t wrote = (len == 0u) ? 0u : fwrite(data, 1u, len, fp);
    int closed = fclose(fp);
    if (wrote != len || closed != 0) { return SRMECH_ERR_IO; }
    return SRMECH_OK;
}

srmech_status_t srmech_plat_file_size(const char *path, size_t *out_size)
{
    assert(path != NULL);
    assert(out_size != NULL);
    FILE *fp = fopen(path, "rb");
    if (fp == NULL) { return SRMECH_ERR_IO; }
    int sk = fseek(fp, 0L, SEEK_END);
    long n = (sk == 0) ? ftell(fp) : -1L;
    fclose(fp);
    if (n < 0) { return SRMECH_ERR_IO; }
    *out_size = (size_t)n;
    return SRMECH_OK;
}

/* Streaming read (rc164) — a persistent read handle so a caller can pull a
 * file in fixed chunks without loading it whole (the §B4 ndjson tokeniser).
 * Portable stdio like the whole-file helpers; no OS split, no new backend
 * accessor (it shares `has_filesystem`). FILE* is a portable type, stored in
 * the opaque handle so srmech_platform.h need not include <stdio.h>. */
_Static_assert(sizeof(FILE *) <= SRMECH_PLAT_RSTREAM_STORAGE,
               "FILE* does not fit srmech_plat_rstream handle storage");

srmech_status_t srmech_plat_rstream_open(const char *path,
                                         srmech_plat_rstream_t *out)
{
    assert(path != NULL);
    assert(out != NULL);
    FILE *fp = fopen(path, "rb");
    if (fp == NULL) { return SRMECH_ERR_IO; }
    memcpy(out->handle.bytes, &fp, sizeof(fp));
    return SRMECH_OK;
}

srmech_status_t srmech_plat_rstream_read(srmech_plat_rstream_t *rs, void *buf,
                                         size_t cap, size_t *out_n)
{
    assert(rs != NULL && out_n != NULL);
    assert(buf != NULL || cap == 0u);
    FILE *fp = NULL;
    memcpy(&fp, rs->handle.bytes, sizeof(fp));
    size_t n = (cap == 0u) ? 0u : fread(buf, 1u, cap, fp);
    *out_n = n;
    if (n < cap && ferror(fp)) { return SRMECH_ERR_IO; }
    return SRMECH_OK;
}

srmech_status_t srmech_plat_rstream_close(srmech_plat_rstream_t *rs)
{
    assert(rs != NULL);
    assert(sizeof(FILE *) <= SRMECH_PLAT_RSTREAM_STORAGE);
    FILE *fp = NULL;
    memcpy(&fp, rs->handle.bytes, sizeof(fp));
    if (fp != NULL) { fclose(fp); }
    return SRMECH_OK;
}

#else  /* bare-metal: no filesystem — callers feed bytes directly */

srmech_status_t srmech_plat_file_read(const char *path, unsigned char *buf,
                                      size_t buf_cap, size_t *out_len)
{
    assert(srmech_plat_has_filesystem() == 0);
    assert(out_len != NULL);
    (void)path; (void)buf; (void)buf_cap; (void)out_len;
    return SRMECH_ERR_IO;
}

srmech_status_t srmech_plat_file_read_region(const char *path, size_t offset,
                                             unsigned char *buf, size_t len)
{
    assert(srmech_plat_has_filesystem() == 0);
    assert(path != NULL);
    (void)path; (void)offset; (void)buf; (void)len;
    return SRMECH_ERR_IO;
}

srmech_status_t srmech_plat_file_write(const char *path, int append,
                                       const unsigned char *data, size_t len)
{
    assert(srmech_plat_has_filesystem() == 0);
    assert(path != NULL);
    (void)path; (void)append; (void)data; (void)len;
    return SRMECH_ERR_IO;
}

srmech_status_t srmech_plat_file_size(const char *path, size_t *out_size)
{
    assert(srmech_plat_has_filesystem() == 0);
    assert(out_size != NULL);
    (void)path; (void)out_size;
    return SRMECH_ERR_IO;
}

srmech_status_t srmech_plat_rstream_open(const char *path,
                                         srmech_plat_rstream_t *out)
{
    assert(srmech_plat_has_filesystem() == 0);
    assert(out != NULL);
    (void)path; (void)out;
    return SRMECH_ERR_IO;
}

srmech_status_t srmech_plat_rstream_read(srmech_plat_rstream_t *rs, void *buf,
                                         size_t cap, size_t *out_n)
{
    assert(srmech_plat_has_filesystem() == 0);
    assert(out_n != NULL);
    (void)rs; (void)buf; (void)cap;
    *out_n = 0u;
    return SRMECH_ERR_IO;
}

srmech_status_t srmech_plat_rstream_close(srmech_plat_rstream_t *rs)
{
    assert(srmech_plat_has_filesystem() == 0);
    assert(rs != NULL);
    (void)rs;
    return SRMECH_OK;
}

#endif  /* SRMECH_PLAT_FILE */

/* ================================================================== *
 * DIRECTORY ITERATION (rc163) — POSIX opendir/readdir / Win32 FindFirstFile,
 * absorbed so the genome's §43 *.chr listing carries no #ifdef. The iterator
 * yields every entry name (incl. "." / ".."); the caller filters by suffix.
 * stdio.h + dirent.h (POSIX) / windows.h (Win) are already included above.
 * ================================================================== */

#if defined(_WIN32) || defined(_WIN64)
#  define SRMECH_PLAT_DIR_WIN   1
#elif defined(__unix__) || defined(__APPLE__) || defined(__linux__)
#  define SRMECH_PLAT_DIR_POSIX 1
#endif

#if defined(SRMECH_PLAT_DIR_POSIX)
_Static_assert(sizeof(DIR *) <= SRMECH_PLAT_DIR_STORAGE,
               "DIR* does not fit srmech_plat_dir handle storage");
#elif defined(SRMECH_PLAT_DIR_WIN)
_Static_assert(sizeof(HANDLE) <= SRMECH_PLAT_DIR_STORAGE,
               "HANDLE does not fit srmech_plat_dir handle storage");
#endif

int srmech_plat_has_dirlist(void)
{
#if defined(SRMECH_PLAT_DIR_POSIX) || defined(SRMECH_PLAT_DIR_WIN)
    return 1;
#else
    return 0;
#endif
}

#if defined(SRMECH_PLAT_DIR_POSIX)

srmech_status_t srmech_plat_dir_open(const char *path, srmech_plat_dir_t *out)
{
    assert(path != NULL);
    assert(out != NULL);
    out->pending_valid = 0;
    DIR *d = opendir(path);
    if (d == NULL) { return SRMECH_ERR_IO; }
    memcpy(out->handle.bytes, &d, sizeof(d));
    return SRMECH_OK;
}

srmech_status_t srmech_plat_dir_next(srmech_plat_dir_t *dir, char *name,
                                     size_t name_cap, int *have)
{
    assert(dir != NULL && have != NULL);
    assert(name != NULL || name_cap == 0u);
    DIR *d = NULL;
    memcpy(&d, dir->handle.bytes, sizeof(d));
    struct dirent *e = readdir(d);
    if (e == NULL) { *have = 0; return SRMECH_OK; }
    size_t nl = strlen(e->d_name);
    if (nl + 1u > name_cap) { return SRMECH_ERR_OVERFLOW; }
    memcpy(name, e->d_name, nl + 1u);
    *have = 1;
    return SRMECH_OK;
}

srmech_status_t srmech_plat_dir_close(srmech_plat_dir_t *dir)
{
    assert(dir != NULL);
    assert(dir->pending_valid == 0 || dir->pending_valid == 1);
    DIR *d = NULL;
    memcpy(&d, dir->handle.bytes, sizeof(d));
    if (d != NULL) { closedir(d); }
    dir->pending_valid = 0;
    return SRMECH_OK;
}

#elif defined(SRMECH_PLAT_DIR_WIN)

srmech_status_t srmech_plat_dir_open(const char *path, srmech_plat_dir_t *out)
{
    assert(path != NULL);
    assert(out != NULL);
    out->pending_valid = 0;
    char pattern[1024];
    int w = snprintf(pattern, sizeof(pattern), "%s/*", path);
    if (w < 0 || (size_t)w >= sizeof(pattern)) { return SRMECH_ERR_OVERFLOW; }
    WIN32_FIND_DATAA fd;
    HANDLE h = FindFirstFileA(pattern, &fd);
    if (h == INVALID_HANDLE_VALUE) { return SRMECH_ERR_IO; }
    size_t nl = strlen(fd.cFileName);
    if (nl + 1u > sizeof(out->pending)) { FindClose(h); return SRMECH_ERR_OVERFLOW; }
    memcpy(out->pending, fd.cFileName, nl + 1u);
    out->pending_valid = 1;
    memcpy(out->handle.bytes, &h, sizeof(h));
    return SRMECH_OK;
}

srmech_status_t srmech_plat_dir_next(srmech_plat_dir_t *dir, char *name,
                                     size_t name_cap, int *have)
{
    assert(dir != NULL && have != NULL);
    assert(name != NULL || name_cap == 0u);
    if (dir->pending_valid) {
        size_t pl = strlen(dir->pending);
        if (pl + 1u > name_cap) { return SRMECH_ERR_OVERFLOW; }
        memcpy(name, dir->pending, pl + 1u);
        dir->pending_valid = 0;
        *have = 1;
        return SRMECH_OK;
    }
    HANDLE h = NULL;
    memcpy(&h, dir->handle.bytes, sizeof(h));
    WIN32_FIND_DATAA fd;
    if (FindNextFileA(h, &fd) == 0) { *have = 0; return SRMECH_OK; }
    size_t nl = strlen(fd.cFileName);
    if (nl + 1u > name_cap) { return SRMECH_ERR_OVERFLOW; }
    memcpy(name, fd.cFileName, nl + 1u);
    *have = 1;
    return SRMECH_OK;
}

srmech_status_t srmech_plat_dir_close(srmech_plat_dir_t *dir)
{
    assert(dir != NULL);
    assert(dir->pending_valid == 0 || dir->pending_valid == 1);
    HANDLE h = NULL;
    memcpy(&h, dir->handle.bytes, sizeof(h));
    if (h != NULL && h != INVALID_HANDLE_VALUE) { FindClose(h); }
    dir->pending_valid = 0;
    return SRMECH_OK;
}

#else  /* bare-metal: no directory listing */

srmech_status_t srmech_plat_dir_open(const char *path, srmech_plat_dir_t *out)
{
    assert(srmech_plat_has_dirlist() == 0);
    assert(out != NULL);
    (void)path; (void)out;
    return SRMECH_ERR_IO;
}

srmech_status_t srmech_plat_dir_next(srmech_plat_dir_t *dir, char *name,
                                     size_t name_cap, int *have)
{
    assert(srmech_plat_has_dirlist() == 0);
    assert(have != NULL);
    (void)dir; (void)name; (void)name_cap;
    *have = 0;
    return SRMECH_ERR_IO;
}

srmech_status_t srmech_plat_dir_close(srmech_plat_dir_t *dir)
{
    assert(srmech_plat_has_dirlist() == 0);
    assert(dir != NULL);
    (void)dir;
    return SRMECH_OK;
}

#endif  /* SRMECH_PLAT_DIR_* */
