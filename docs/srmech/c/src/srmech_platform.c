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

/* Declare nanosleep (POSIX.1b, _POSIX_C_SOURCE >= 199309L) under the strict
 * -std=c11 the build uses (CMAKE_C_EXTENSIONS OFF). MUST precede all includes.
 * Additive — the socket/pthread PAL code compiles unchanged. */
#define _POSIX_C_SOURCE 200809L

#include "srmech_platform.h"

#include <assert.h>
#include <errno.h>    /* ENOENT / EEXIST (rc284 mkdir/remove idempotence) — needed
                       * on BOTH branches, so it is hoisted out of the POSIX block */
#include <stdio.h>    /* snprintf (stream endpoint paths); remove/rename (rc284) */
#include <stdlib.h>   /* getenv (POSIX socket path under $HOME) */
#include <string.h>
#include <time.h>     /* timespec_get / TIME_UTC (wall clock, rc179) */

#if defined(_WIN32) || defined(_WIN64)
#  define SRMECH_PLAT_THREADS_WIN 1
#  define SRMECH_PLAT_STREAM_WIN  1
#  include <windows.h>
#elif defined(__unix__) || defined(__APPLE__) || defined(__linux__)
#  define SRMECH_PLAT_THREADS_POSIX 1
#  define SRMECH_PLAT_STREAM_POSIX  1
#  include <pthread.h>
#  include <sys/socket.h>   /* AF_UNIX / AF_INET stream IPC */
#  include <sys/stat.h>     /* mkdir / chmod */
#  include <sys/types.h>
#  include <sys/un.h>       /* sockaddr_un */
#  include <netinet/in.h>   /* sockaddr_in (TCP, rc194) */
#  include <arpa/inet.h>    /* inet_pton / htons / ntohs (TCP, rc194) */
#  include <poll.h>         /* poll (TCP accept timeout, rc194) */
#  include <sys/time.h>     /* struct timeval (SO_RCVTIMEO, rc194) */
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

/* TCP (rc194) — POSIX-first (BSD sockets). Windows Winsock is a follow-up. */
#if defined(SRMECH_PLAT_STREAM_POSIX)
#  define SRMECH_PLAT_TCP_POSIX 1
_Static_assert(sizeof(int) <= SRMECH_PLAT_TCP_STORAGE,
               "fd does not fit srmech_plat_tcp_server handle storage");
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
 * MUTEX (rc180) — pthread_mutex (POSIX) / CRITICAL_SECTION (Windows) /
 * no-op (thread-less). The OS lock lives IN the caller's storage (cast in
 * place — never memcpy'd after init, since a live lock has identity), so
 * the same address is always passed to lock/unlock (ThreadSanitizer tracks
 * the lock by that stable pointer). No heap; JPL-clean.
 * ================================================================== */

#if defined(SRMECH_PLAT_THREADS_POSIX)
_Static_assert(sizeof(pthread_mutex_t) <= SRMECH_PLAT_MUTEX_STORAGE,
               "pthread_mutex_t does not fit srmech_plat_mutex handle storage");

srmech_status_t srmech_plat_mutex_init(srmech_plat_mutex_t *m)
{
    assert(m != NULL);
    assert(sizeof(pthread_mutex_t) <= sizeof m->handle.bytes);
    if (m == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    pthread_mutex_t *mtx = (pthread_mutex_t *)(void *)m->handle.bytes;
    if (pthread_mutex_init(mtx, NULL) != 0) {
        m->initialized = 0;
        return SRMECH_ERR_INTERNAL;
    }
    m->initialized = 1;
    return SRMECH_OK;
}

srmech_status_t srmech_plat_mutex_lock(srmech_plat_mutex_t *m)
{
    assert(m != NULL);
    assert(m->initialized == 1);
    pthread_mutex_t *mtx = (pthread_mutex_t *)(void *)m->handle.bytes;
    if (pthread_mutex_lock(mtx) != 0) {
        return SRMECH_ERR_INTERNAL;
    }
    return SRMECH_OK;
}

srmech_status_t srmech_plat_mutex_unlock(srmech_plat_mutex_t *m)
{
    assert(m != NULL);
    assert(m->initialized == 1);
    pthread_mutex_t *mtx = (pthread_mutex_t *)(void *)m->handle.bytes;
    if (pthread_mutex_unlock(mtx) != 0) {
        return SRMECH_ERR_INTERNAL;
    }
    return SRMECH_OK;
}

srmech_status_t srmech_plat_mutex_destroy(srmech_plat_mutex_t *m)
{
    assert(m != NULL);
    assert(m->initialized == 0 || m->initialized == 1);
    if (m == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (m->initialized) {
        pthread_mutex_t *mtx = (pthread_mutex_t *)(void *)m->handle.bytes;
        (void)pthread_mutex_destroy(mtx);
        m->initialized = 0;
    }
    return SRMECH_OK;
}

#elif defined(SRMECH_PLAT_THREADS_WIN)
_Static_assert(sizeof(CRITICAL_SECTION) <= SRMECH_PLAT_MUTEX_STORAGE,
               "CRITICAL_SECTION does not fit srmech_plat_mutex handle storage");

srmech_status_t srmech_plat_mutex_init(srmech_plat_mutex_t *m)
{
    assert(m != NULL);
    assert(sizeof(CRITICAL_SECTION) <= sizeof m->handle.bytes);
    if (m == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    CRITICAL_SECTION *cs = (CRITICAL_SECTION *)(void *)m->handle.bytes;
    InitializeCriticalSection(cs);
    m->initialized = 1;
    return SRMECH_OK;
}

srmech_status_t srmech_plat_mutex_lock(srmech_plat_mutex_t *m)
{
    assert(m != NULL);
    assert(m->initialized == 1);
    CRITICAL_SECTION *cs = (CRITICAL_SECTION *)(void *)m->handle.bytes;
    EnterCriticalSection(cs);
    return SRMECH_OK;
}

srmech_status_t srmech_plat_mutex_unlock(srmech_plat_mutex_t *m)
{
    assert(m != NULL);
    assert(m->initialized == 1);
    CRITICAL_SECTION *cs = (CRITICAL_SECTION *)(void *)m->handle.bytes;
    LeaveCriticalSection(cs);
    return SRMECH_OK;
}

srmech_status_t srmech_plat_mutex_destroy(srmech_plat_mutex_t *m)
{
    assert(m != NULL);
    assert(m->initialized == 0 || m->initialized == 1);
    if (m == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (m->initialized) {
        CRITICAL_SECTION *cs = (CRITICAL_SECTION *)(void *)m->handle.bytes;
        DeleteCriticalSection(cs);
        m->initialized = 0;
    }
    return SRMECH_OK;
}

#else  /* thread-less target: the lock is a no-op (serial caller, no races) */

srmech_status_t srmech_plat_mutex_init(srmech_plat_mutex_t *m)
{
    assert(m != NULL);
    assert(srmech_plat_has_threads() == 0);
    m->initialized = 1;
    return SRMECH_OK;
}

srmech_status_t srmech_plat_mutex_lock(srmech_plat_mutex_t *m)
{
    assert(m != NULL);
    assert(m->initialized == 1);
    return SRMECH_OK;
}

srmech_status_t srmech_plat_mutex_unlock(srmech_plat_mutex_t *m)
{
    assert(m != NULL);
    assert(m->initialized == 1);
    return SRMECH_OK;
}

srmech_status_t srmech_plat_mutex_destroy(srmech_plat_mutex_t *m)
{
    assert(m != NULL);
    assert(srmech_plat_has_threads() == 0);
    m->initialized = 0;
    return SRMECH_OK;
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
    /* FILE_FLAG_OVERLAPPED: accept() waits on the ConnectNamedPipe overlapped
     * event alongside the server stop-event, so a blocked accept is woken at
     * teardown (a synchronous ConnectNamedPipe cannot be cancelled by a
     * CloseHandle from another thread). Read/write on the connected instance
     * then go through srmech_plat__pipe_io (overlapped-aware). */
    HANDLE h = CreateNamedPipeA(
        path, PIPE_ACCESS_DUPLEX | FILE_FLAG_OVERLAPPED,
        PIPE_TYPE_BYTE | PIPE_READMODE_BYTE | PIPE_WAIT,
        PIPE_UNLIMITED_INSTANCES, 65536, 65536, 0, NULL);
    return h;
}

/* One overlapped-capable read OR write over a pipe HANDLE. Uniform across an
 * OVERLAPPED server instance (created above) AND a synchronous client handle
 * (CreateFile without the flag): a synchronous handle completes inline (never
 * ERROR_IO_PENDING) and ignores hEvent, so the same path serves both. Blocks
 * until the transfer completes or fails; *moved gets the byte count. */
static srmech_status_t srmech_plat__pipe_io(HANDLE h, void *buf, DWORD n,
                                            BOOL is_read, DWORD *moved)
{
    assert(h != INVALID_HANDLE_VALUE);
    assert(moved != NULL);
    OVERLAPPED ov;
    memset(&ov, 0, sizeof ov);
    ov.hEvent = CreateEventA(NULL, TRUE, FALSE, NULL);
    if (ov.hEvent == NULL) {
        return SRMECH_ERR_IO;
    }
    BOOL ok = is_read ? ReadFile(h, buf, n, moved, &ov)
                      : WriteFile(h, buf, n, moved, &ov);
    if (!ok && GetLastError() == ERROR_IO_PENDING) {
        ok = GetOverlappedResult(h, &ov, moved, TRUE);   /* block till done */
    }
    (void)CloseHandle(ov.hEvent);
    return ok ? SRMECH_OK : SRMECH_ERR_IO;
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
    HANDLE invalid = INVALID_HANDLE_VALUE;
    memcpy(out->handle.bytes, &invalid, sizeof invalid);
    memcpy(out->stop_handle.bytes, &invalid, sizeof invalid);
    srmech_status_t rc = srmech_plat__derive_path(
        name, out->endpoint_path, sizeof out->endpoint_path);
    if (rc != SRMECH_OK) {
        return rc;
    }
    /* Manual-reset stop-event: server_close SetEvent()s it to wake a blocked
     * overlapped ConnectNamedPipe in accept(). */
    HANDLE stop_ev = CreateEventA(NULL, TRUE, FALSE, NULL);
    if (stop_ev == NULL) {
        return SRMECH_ERR_IO;
    }
    /* Pre-create the FIRST instance so the endpoint EXISTS before any client
     * connects (mirrors POSIX listen() pre-binding): a racing client's
     * CreateFile then sees the pipe (ERROR_PIPE_BUSY, retryable) instead of
     * ERROR_FILE_NOT_FOUND against a not-yet-created lazy instance. */
    HANDLE pipe_h = srmech_plat__create_pipe_instance(out->endpoint_path);
    if (pipe_h == INVALID_HANDLE_VALUE) {
        (void)CloseHandle(stop_ev);
        return SRMECH_ERR_IO;
    }
    memcpy(out->handle.bytes, &pipe_h, sizeof pipe_h);
    memcpy(out->stop_handle.bytes, &stop_ev, sizeof stop_ev);
    return SRMECH_OK;
}

/* Overlapped ConnectNamedPipe on `pipe_h`, waiting on EITHER the connect
 * completion OR the server stop-event. Returns SRMECH_OK once a client is
 * connected; SRMECH_ERR_IO if stopped (the pending connect is CancelIoEx'd +
 * reaped) or a real connect error. Ownership of pipe_h stays with the caller
 * in every case. */
static srmech_status_t srmech_plat__wait_connect(HANDLE pipe_h, HANDLE stop_ev)
{
    assert(pipe_h != INVALID_HANDLE_VALUE);
    assert(stop_ev != INVALID_HANDLE_VALUE);
    OVERLAPPED ov;
    memset(&ov, 0, sizeof ov);
    ov.hEvent = CreateEventA(NULL, TRUE, FALSE, NULL);
    if (ov.hEvent == NULL) {
        return SRMECH_ERR_IO;
    }
    BOOL ok = ConnectNamedPipe(pipe_h, &ov);
    DWORD le = ok ? 0u : GetLastError();
    srmech_status_t rc = SRMECH_OK;
    if (!ok && le == ERROR_IO_PENDING) {
        HANDLE waits[2];
        waits[0] = ov.hEvent;
        waits[1] = stop_ev;
        DWORD w = WaitForMultipleObjects(2, waits, FALSE, INFINITE);
        if (w != WAIT_OBJECT_0) {   /* stop-event fired or wait failed */
            DWORD reaped = 0;
            (void)CancelIoEx(pipe_h, &ov);
            (void)GetOverlappedResult(pipe_h, &ov, &reaped, TRUE);
            rc = SRMECH_ERR_IO;
        }
    } else if (!ok && le != ERROR_PIPE_CONNECTED) {
        rc = SRMECH_ERR_IO;   /* client already connected is NOT an error */
    }
    (void)CloseHandle(ov.hEvent);
    return rc;
}

srmech_status_t srmech_plat_stream_accept(srmech_plat_stream_server_t *server,
                                          srmech_plat_stream_conn_t *conn_out)
{
    assert(server != NULL);
    assert(conn_out != NULL);
    if (server == NULL || conn_out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    HANDLE pipe_h, stop_ev;
    memcpy(&pipe_h, server->handle.bytes, sizeof pipe_h);
    memcpy(&stop_ev, server->stop_handle.bytes, sizeof stop_ev);
    if (pipe_h == INVALID_HANDLE_VALUE || stop_ev == INVALID_HANDLE_VALUE) {
        return SRMECH_ERR_IO;   /* not armed (listen failed / already closed) */
    }
    srmech_status_t rc = srmech_plat__wait_connect(pipe_h, stop_ev);
    if (rc != SRMECH_OK) {
        return rc;   /* stopped / connect error; pipe_h stays for close */
    }
    /* Connected. Pre-arm the NEXT instance so the endpoint name never
     * vanishes (a client between accepts sees ERROR_PIPE_BUSY, retryable,
     * not ERROR_FILE_NOT_FOUND), then hand the connected instance out. */
    HANDLE next = srmech_plat__create_pipe_instance(server->endpoint_path);
    memcpy(server->handle.bytes, &next, sizeof next);   /* may be INVALID */
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
    HANDLE stop_ev, pending;
    assert(sizeof pending <= sizeof server->handle.bytes);
    memcpy(&stop_ev, server->stop_handle.bytes, sizeof stop_ev);
    /* Wake a thread blocked in accept()'s overlapped ConnectNamedPipe FIRST
     * (it returns SRMECH_ERR_IO), then drop the instance + the stop-event. */
    if (stop_ev != INVALID_HANDLE_VALUE && stop_ev != NULL) {
        (void)SetEvent(stop_ev);
    }
    memcpy(&pending, server->handle.bytes, sizeof pending);
    if (pending != INVALID_HANDLE_VALUE) {
        (void)DisconnectNamedPipe(pending);
        (void)CloseHandle(pending);
    }
    if (stop_ev != INVALID_HANDLE_VALUE && stop_ev != NULL) {
        (void)CloseHandle(stop_ev);
    }
    HANDLE invalid = INVALID_HANDLE_VALUE;
    memcpy(server->handle.bytes, &invalid, sizeof invalid);
    memcpy(server->stop_handle.bytes, &invalid, sizeof invalid);
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
    /* Bounded connect retry: ERROR_PIPE_BUSY (all instances in use) waits for a
     * free one; ERROR_FILE_NOT_FOUND (a client that raced the server's listen()
     * before the endpoint was created) briefly re-polls. Any other error is
     * terminal. Bounded iteration count keeps JPL Rule 2. */
    HANDLE h = INVALID_HANDLE_VALUE;
    for (int tries = 0; tries < 50; tries++) {
        h = CreateFileA(path, GENERIC_READ | GENERIC_WRITE,
                        0, NULL, OPEN_EXISTING, 0, NULL);
        if (h != INVALID_HANDLE_VALUE) {
            break;
        }
        DWORD le = GetLastError();
        if (le == ERROR_PIPE_BUSY) {
            (void)WaitNamedPipeA(path, 2000);
        } else if (le == ERROR_FILE_NOT_FOUND) {
            Sleep(20);
        } else {
            break;   /* terminal error */
        }
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
    size_t got_total = 0;
    while (got_total < n) {
        DWORD got = 0;
        srmech_status_t rc = srmech_plat__pipe_io(
            h, buf + got_total, (DWORD)(n - got_total), TRUE, &got);
        if (rc != SRMECH_OK || got == 0) {
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
    size_t sent_total = 0;
    while (sent_total < n) {
        DWORD sent = 0;
        srmech_status_t rc = srmech_plat__pipe_io(
            h, (void *)(buf + sent_total), (DWORD)(n - sent_total),
            FALSE, &sent);
        if (rc != SRMECH_OK || sent == 0) {
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

/* The rc296 read-path open counter (see srmech_platform.h for why it exists).
 * Defined OUTSIDE the SRMECH_PLAT_FILE guard so a no-filesystem host still
 * links the accessors — there it simply reads 0 forever, which is the truth. */
static uint64_t g_plat_file_opens = 0u;

uint64_t srmech_plat_file_opens(void)
{
    uint64_t n = g_plat_file_opens;
    assert(sizeof(n) == 8u);
    /* A target with no filesystem cannot have opened anything. */
    assert(srmech_plat_has_filesystem() != 0 || n == 0u);
    return n;
}

void srmech_plat_file_opens_reset(void)
{
    assert(sizeof(g_plat_file_opens) == 8u);
    g_plat_file_opens = 0u;
    assert(g_plat_file_opens == 0u);
}

#if defined(SRMECH_PLAT_FILE)

srmech_status_t srmech_plat_file_read(const char *path, unsigned char *buf,
                                      size_t buf_cap, size_t *out_len)
{
    assert(path != NULL);
    assert(out_len != NULL && (buf != NULL || buf_cap == 0));
    FILE *fp = fopen(path, "rb");
    g_plat_file_opens++;                      /* rc296 read-path open counter */
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
    g_plat_file_opens++;                      /* rc296 read-path open counter */
    if (fp == NULL) { return SRMECH_ERR_IO; }
    if (fseek(fp, (long)offset, SEEK_SET) != 0) {
        fclose(fp);
        return SRMECH_ERR_IO;
    }
    size_t got = (len == 0u) ? 0u : fread(buf, 1u, len, fp);
    fclose(fp);
    return (got == len) ? SRMECH_OK : SRMECH_ERR_IO;
}

srmech_status_t srmech_plat_file_open_ro(const char *path, srmech_file_ro_t *out)
{
    assert(path != NULL);
    assert(out != NULL);
    out->fp = (void *)fopen(path, "rb");
    g_plat_file_opens++;                      /* rc296 read-path open counter */
    return (out->fp == NULL) ? SRMECH_ERR_IO : SRMECH_OK;
}

srmech_status_t srmech_plat_file_read_at(srmech_file_ro_t *fh, size_t offset,
                                         unsigned char *buf, size_t len)
{
    assert(fh != NULL);
    assert(buf != NULL || len == 0);
    if (fh->fp == NULL) { return SRMECH_ERR_IO; }
    if (fseek((FILE *)fh->fp, (long)offset, SEEK_SET) != 0) {
        return SRMECH_ERR_IO;
    }
    size_t got = (len == 0u) ? 0u : fread(buf, 1u, len, (FILE *)fh->fp);
    return (got == len) ? SRMECH_OK : SRMECH_ERR_IO;
}

void srmech_plat_file_close_ro(srmech_file_ro_t *fh)
{
    assert(fh != NULL);
    assert(srmech_plat_has_filesystem() != 0);
    if (fh->fp != NULL) {
        (void)fclose((FILE *)fh->fp);
        fh->fp = NULL;
    }
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
    g_plat_file_opens++;                      /* rc296 read-path open counter */
    if (fp == NULL) { return SRMECH_ERR_IO; }
    int sk = fseek(fp, 0L, SEEK_END);
    long n = (sk == 0) ? ftell(fp) : -1L;
    fclose(fp);
    if (n < 0) { return SRMECH_ERR_IO; }
    *out_size = (size_t)n;
    return SRMECH_OK;
}

/* Mutating filesystem ops (rc284) — mkdir / remove / replacing-rename, the
 * three surfaces the out-of-core recursive_cut work QUEUE needs. remove() and
 * rename() are C89 stdio; mkdir and replacing-rename carry the only OS split
 * in this block, kept here so srmech_laplacian.c stays #ifdef-free. */

srmech_status_t srmech_plat_mkdir(const char *path)
{
    assert(path != NULL);
    /* rc357 (`#T980`): assert BELOW the guard — an empty path is a recoverable
     * SRMECH_ERR_BAD_INPUT, so asserting its negation above would abort the
     * host on the very input the guard exists to handle. Latent only because
     * no test drives an empty path; same shape as srmech_rational.c:121. */
    if (path == NULL || path[0] == '\0') { return SRMECH_ERR_BAD_INPUT; }
    assert(path[0] != '\0');
#if defined(_WIN32) || defined(_WIN64)
    if (CreateDirectoryA(path, NULL)) { return SRMECH_OK; }
    /* already-there is SUCCESS: the os.makedirs(exist_ok=True) semantic. */
    return (GetLastError() == ERROR_ALREADY_EXISTS) ? SRMECH_OK : SRMECH_ERR_IO;
#else
    if (mkdir(path, 0700) == 0) { return SRMECH_OK; }
    return (errno == EEXIST) ? SRMECH_OK : SRMECH_ERR_IO;
#endif
}

srmech_status_t srmech_plat_file_remove(const char *path)
{
    assert(path != NULL);
    /* rc357 (`#T980`): assert BELOW the guard — see srmech_plat_mkdir above. */
    if (path == NULL || path[0] == '\0') { return SRMECH_ERR_BAD_INPUT; }
    assert(path[0] != '\0');
    if (remove(path) == 0) { return SRMECH_OK; }
    /* MISSING is SUCCESS — the caller wanted it gone and it is gone. */
    return (errno == ENOENT) ? SRMECH_OK : SRMECH_ERR_IO;
}

srmech_status_t srmech_plat_file_replace(const char *src, const char *dst)
{
    /* rc357 (`#T980`): this one was STRICTLY WORSE than its two peers above —
     * the asserts demanded non-empty src/dst while the guard checked only NULL,
     * so an empty string aborted the host with no recoverable peer AT ALL. The
     * empty-path case now returns BAD_INPUT, matching srmech_plat_mkdir and
     * srmech_plat_file_remove; the asserts move below the guards they duplicate. */
    if (src == NULL || dst == NULL) { return SRMECH_ERR_NULL_ARG; }
    if (src[0] == '\0' || dst[0] == '\0') { return SRMECH_ERR_BAD_INPUT; }
    assert(src[0] != '\0');
    assert(dst[0] != '\0');
#if defined(_WIN32) || defined(_WIN64)
    /* Win32 rename() FAILS on an existing dst; MoveFileEx replaces it. */
    if (MoveFileExA(src, dst, MOVEFILE_REPLACE_EXISTING)) { return SRMECH_OK; }
    return SRMECH_ERR_IO;
#else
    /* POSIX rename() already replaces an existing dst atomically. */
    return (rename(src, dst) == 0) ? SRMECH_OK : SRMECH_ERR_IO;
#endif
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
    g_plat_file_opens++;                      /* rc296 read-path open counter */
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

srmech_status_t srmech_plat_file_open_ro(const char *path, srmech_file_ro_t *out)
{
    assert(srmech_plat_has_filesystem() == 0);
    assert(path != NULL && out != NULL);
    (void)path;
    out->fp = NULL;
    return SRMECH_ERR_IO;
}

srmech_status_t srmech_plat_file_read_at(srmech_file_ro_t *fh, size_t offset,
                                         unsigned char *buf, size_t len)
{
    assert(srmech_plat_has_filesystem() == 0);
    assert(fh != NULL);
    (void)fh; (void)offset; (void)buf; (void)len;
    return SRMECH_ERR_IO;
}

void srmech_plat_file_close_ro(srmech_file_ro_t *fh)
{
    assert(srmech_plat_has_filesystem() == 0);
    assert(fh != NULL);
    fh->fp = NULL;
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

srmech_status_t srmech_plat_mkdir(const char *path)
{
    assert(srmech_plat_has_filesystem() == 0);
    assert(path != NULL);
    (void)path;
    return SRMECH_ERR_IO;
}

srmech_status_t srmech_plat_file_remove(const char *path)
{
    assert(srmech_plat_has_filesystem() == 0);
    assert(path != NULL);
    (void)path;
    return SRMECH_ERR_IO;
}

srmech_status_t srmech_plat_file_replace(const char *src, const char *dst)
{
    assert(srmech_plat_has_filesystem() == 0);
    assert(src != NULL && dst != NULL);
    (void)src; (void)dst;
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
    memset(out->handle.bytes, 0, sizeof(out->handle.bytes));
    /* opendir keeps "opened but empty" and "could not open" apart natively: an
     * empty directory opens fine and readdir simply reports end-of-stream (on
     * ordinary POSIX filesystems it still yields "." and ".."). So a NULL here
     * means a REAL failure — ENOENT / EACCES / ENOTDIR — and is an error. The
     * Windows branch below has to reconstruct this distinction by hand. */
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
    memset(out->handle.bytes, 0, sizeof(out->handle.bytes));
    char pattern[1024];
    int w = snprintf(pattern, sizeof(pattern), "%s/*", path);
    if (w < 0 || (size_t)w >= sizeof(pattern)) { return SRMECH_ERR_OVERFLOW; }
    WIN32_FIND_DATAA fd;
    HANDLE h = FindFirstFileA(pattern, &fd);
    /* rc294: FindFirstFile CONFLATES two outcomes that POSIX opendir keeps
     * apart, and the difference is load-bearing now that an unopenable root is
     * an ERROR rather than "zero entries".
     *
     *   ERROR_FILE_NOT_FOUND — the search RAN and matched nothing. The
     *       directory opened fine; it simply has no entries to enumerate. Most
     *       Windows volumes hand back "." and ".." so the wildcard always
     *       matches, but a FAT/exFAT ROOT directory has no "." / ".." entries
     *       at all, and some network / virtual filesystems suppress them too.
     *       On those an EMPTY directory lands HERE. That is the documented
     *       supported input whose contract is n_genomes 0 (see
     *       genome_list_genomes), so it MUST NOT become an error.
     *   anything else (ERROR_PATH_NOT_FOUND, ERROR_ACCESS_DENIED,
     *       ERROR_DIRECTORY, ...) — the directory could not be opened.
     *
     * The empty-match case therefore returns an EXHAUSTED iterator (NULL
     * handle, no lookahead) with SRMECH_OK: dir_next reports end-of-directory
     * immediately and dir_close is a no-op on it. Without this split, the
     * POSIX projection would report 0 genomes for an empty root while the
     * Windows one reported SRMECH_ERR_IO — trading the ADR-0009 split this rc
     * closes for a new one along a platform seam instead of a language seam. */
    if (h == INVALID_HANDLE_VALUE) {
        if (GetLastError() == ERROR_FILE_NOT_FOUND) { return SRMECH_OK; }
        return SRMECH_ERR_IO;
    }
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
    /* rc294: a NULL handle is the EXHAUSTED iterator dir_open returns for the
     * ERROR_FILE_NOT_FOUND (opened-but-empty) case. Report end-of-directory
     * rather than handing NULL to FindNextFile. */
    if (h == NULL) { *have = 0; return SRMECH_OK; }
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

/* ================================================================== *
 * WALL CLOCK (rc179) — ISO C11 timespec_get(TIME_UTC). One
 * implementation for POSIX + Windows (no #ifdef); a clock-less libc
 * (timespec_get returning 0) reports SRMECH_ERR_IO. Consumer: the bus
 * Bio-TOTP encrypted transport, which rolls its key window on wall time.
 * ================================================================== */

srmech_status_t srmech_plat_now_ns(int64_t *out_ns)
{
    assert(out_ns != NULL);
    if (out_ns == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    struct timespec ts;
    if (timespec_get(&ts, TIME_UTC) != TIME_UTC) {
        return SRMECH_ERR_IO;   /* no wall-clock backend on this target */
    }
    assert(ts.tv_nsec >= 0);
    *out_ns = ((int64_t)ts.tv_sec * 1000000000LL) + (int64_t)ts.tv_nsec;
    return SRMECH_OK;
}

/* ================================================================== *
 * STANDARD I/O (rc186) — POSIX read(0)/write(1) / Windows ReadFile/WriteFile
 * on GetStdHandle. The MCP stdio loop (srmech_mcp.c) is the consumer; it
 * carries no #ifdef. EOF (0-byte read / broken pipe) is a clean terminator.
 * ================================================================== */

#if defined(_WIN32) || defined(_WIN64) || defined(__unix__) \
    || defined(__APPLE__) || defined(__linux__)
#  define SRMECH_PLAT_STDIO 1
#endif

int srmech_plat_has_stdio(void)
{
#if defined(SRMECH_PLAT_STDIO)
    return 1;
#else
    return 0;
#endif
}

#if defined(SRMECH_PLAT_STDIO) && (defined(_WIN32) || defined(_WIN64))

srmech_status_t srmech_plat_stdin_read(unsigned char *buf, size_t cap,
                                       size_t *out_n)
{
    HANDLE h;
    DWORD got = 0;
    BOOL ok;
    assert(buf != NULL || cap == 0u);
    assert(out_n != NULL);
    *out_n = 0u;
    if (cap == 0u) {
        return SRMECH_OK;
    }
    h = GetStdHandle(STD_INPUT_HANDLE);
    if (h == INVALID_HANDLE_VALUE || h == NULL) {
        return SRMECH_ERR_IO;
    }
    ok = ReadFile(h, buf, (DWORD)cap, &got, NULL);
    if (!ok) {
        DWORD le = GetLastError();
        if (le == ERROR_BROKEN_PIPE || le == ERROR_HANDLE_EOF) {
            return SRMECH_OK;   /* peer closed stdin → clean EOF (*out_n == 0) */
        }
        return SRMECH_ERR_IO;
    }
    *out_n = (size_t)got;       /* got == 0 is also EOF */
    return SRMECH_OK;
}

srmech_status_t srmech_plat_stdout_write(const unsigned char *buf, size_t n)
{
    HANDLE h;
    DWORD sent_total = 0;
    assert(buf != NULL || n == 0u);
    assert(n == 0u || buf != NULL);
    if (n == 0u) {
        return SRMECH_OK;
    }
    h = GetStdHandle(STD_OUTPUT_HANDLE);
    if (h == INVALID_HANDLE_VALUE || h == NULL) {
        return SRMECH_ERR_IO;
    }
    while (sent_total < n) {
        DWORD sent = 0;
        BOOL ok = WriteFile(h, buf + sent_total,
                            (DWORD)(n - sent_total), &sent, NULL);
        if (!ok || sent == 0) {
            return SRMECH_ERR_IO;
        }
        sent_total += sent;
    }
    return SRMECH_OK;
}

#elif defined(SRMECH_PLAT_STDIO)

srmech_status_t srmech_plat_stdin_read(unsigned char *buf, size_t cap,
                                       size_t *out_n)
{
    assert(buf != NULL || cap == 0u);
    assert(out_n != NULL);
    *out_n = 0u;
    if (cap == 0u) {
        return SRMECH_OK;
    }
    for (;;) {
        ssize_t r = read(0, buf, cap);
        if (r < 0) {
            if (errno == EINTR) {
                continue;
            }
            return SRMECH_ERR_IO;
        }
        *out_n = (size_t)r;   /* r == 0 is EOF (closed stdin) */
        return SRMECH_OK;
    }
}

srmech_status_t srmech_plat_stdout_write(const unsigned char *buf, size_t n)
{
    size_t sent = 0u;
    assert(buf != NULL || n == 0u);
    assert(n == 0u || buf != NULL);
    while (sent < n) {
        ssize_t w = write(1, buf + sent, n - sent);
        if (w < 0) {
            if (errno == EINTR) {
                continue;
            }
            return SRMECH_ERR_IO;
        }
        sent += (size_t)w;
    }
    assert(sent == n);
    return SRMECH_OK;
}

#else  /* bare-metal: no standard streams — the MCP loop feeds bytes another way */

srmech_status_t srmech_plat_stdin_read(unsigned char *buf, size_t cap,
                                       size_t *out_n)
{
    assert(srmech_plat_has_stdio() == 0);
    assert(out_n != NULL);
    (void)buf;
    (void)cap;
    *out_n = 0u;
    return SRMECH_ERR_IO;
}

srmech_status_t srmech_plat_stdout_write(const unsigned char *buf, size_t n)
{
    assert(srmech_plat_has_stdio() == 0);
    assert(buf != NULL || n == 0u);
    (void)buf;
    (void)n;
    return SRMECH_ERR_IO;
}

#endif  /* SRMECH_PLAT_STDIO backends */

/* ================================================================== *
 * TCP STREAM (rc194) — localhost TCP for the MCP HTTP+SSE server.
 * POSIX BSD sockets; Windows / bare-metal report has_tcp() == 0.
 * The accept is poll()-gated so teardown never hangs (rc180 discipline).
 * ================================================================== */

int srmech_plat_has_tcp(void)
{
#if defined(SRMECH_PLAT_TCP_POSIX)
    return 1;
#else
    return 0;   /* Windows Winsock is a follow-up; bare-metal has no TCP */
#endif
}

#if defined(SRMECH_PLAT_TCP_POSIX)

#define SRMECH_PLAT_TCP_BACKLOG      16
#define SRMECH_PLAT_TCP_RECV_TIMEO_S 10   /* half-open client can't stall us */

srmech_status_t srmech_plat_tcp_listen(const char *host, uint16_t port,
                                       srmech_plat_tcp_server_t *out,
                                       uint16_t *out_port)
{
    assert(out != NULL);
    assert(out_port != NULL);
    if (host == NULL || out == NULL || out_port == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    memset(out, 0, sizeof *out);
    int init_fd = -1;   /* a failed listen leaves -1 so close() is a no-op */
    memcpy(out->handle.bytes, &init_fd, sizeof init_fd);
    int s = socket(AF_INET, SOCK_STREAM, 0);
    if (s < 0) {
        return SRMECH_ERR_IO;
    }
    int one = 1;
    (void)setsockopt(s, SOL_SOCKET, SO_REUSEADDR, &one, sizeof one);
    struct sockaddr_in addr;
    memset(&addr, 0, sizeof addr);
    addr.sin_family = AF_INET;
    addr.sin_port = htons(port);
    if (inet_pton(AF_INET, host, &addr.sin_addr) != 1) {
        (void)close(s);
        return SRMECH_ERR_BAD_INPUT;
    }
    if (bind(s, (struct sockaddr *)&addr, sizeof addr) < 0
        || listen(s, SRMECH_PLAT_TCP_BACKLOG) < 0) {
        (void)close(s);
        return SRMECH_ERR_IO;
    }
    struct sockaddr_in bound;
    socklen_t blen = sizeof bound;
    if (getsockname(s, (struct sockaddr *)&bound, &blen) < 0) {
        (void)close(s);
        return SRMECH_ERR_IO;
    }
    *out_port = ntohs(bound.sin_port);
    memcpy(out->handle.bytes, &s, sizeof s);
    return SRMECH_OK;
}

srmech_status_t srmech_plat_tcp_accept(srmech_plat_tcp_server_t *server,
                                       srmech_plat_stream_conn_t *conn_out,
                                       unsigned timeout_ms, int *got)
{
    assert(server != NULL && conn_out != NULL);
    assert(got != NULL);
    if (server == NULL || conn_out == NULL || got == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    *got = 0;
    int listen_fd;
    memcpy(&listen_fd, server->handle.bytes, sizeof listen_fd);
    if (listen_fd < 0) {
        return SRMECH_ERR_IO;   /* closed at teardown */
    }
    struct pollfd pfd;
    pfd.fd = listen_fd;
    pfd.events = POLLIN;
    pfd.revents = 0;
    int pr = poll(&pfd, 1, (timeout_ms == 0u) ? -1 : (int)timeout_ms);
    if (pr < 0) {
        return (errno == EINTR) ? SRMECH_OK : SRMECH_ERR_IO;
    }
    if (pr == 0) {
        return SRMECH_OK;   /* timeout — *got stays 0, caller re-checks stop */
    }
    int conn = accept(listen_fd, NULL, NULL);
    if (conn < 0) {
        return (errno == EINTR || errno == ECONNABORTED)
            ? SRMECH_OK : SRMECH_ERR_IO;
    }
    struct timeval tv;
    tv.tv_sec = SRMECH_PLAT_TCP_RECV_TIMEO_S;
    tv.tv_usec = 0;
    (void)setsockopt(conn, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof tv);
    memset(conn_out, 0, sizeof *conn_out);
    memcpy(conn_out->handle.bytes, &conn, sizeof conn);
    *got = 1;
    return SRMECH_OK;
}

srmech_status_t srmech_plat_tcp_server_close(srmech_plat_tcp_server_t *server)
{
    assert(server != NULL);
    if (server == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    int listen_fd;
    assert(sizeof listen_fd <= sizeof server->handle.bytes);
    memcpy(&listen_fd, server->handle.bytes, sizeof listen_fd);
    /* Do NOT write the handle back (a concurrent poll-gated accept thread reads
     * these bytes with no lock — a write-back would data-race it). shutdown+
     * close releases the socket; the accept loop's poll timeout + its stop flag
     * terminate it. Call once (the SSE server calls it exactly once at stop). */
    if (listen_fd >= 0) {
        (void)shutdown(listen_fd, SHUT_RDWR);
        (void)close(listen_fd);
    }
    return SRMECH_OK;
}

srmech_status_t srmech_plat_tcp_read_some(srmech_plat_stream_conn_t *conn,
                                          unsigned char *buf, size_t cap,
                                          size_t *out_n)
{
    assert(conn != NULL && out_n != NULL);
    assert(buf != NULL || cap == 0u);
    *out_n = 0u;
    if (cap == 0u) {
        return SRMECH_OK;
    }
    int fd;
    memcpy(&fd, conn->handle.bytes, sizeof fd);
    for (;;) {
        ssize_t r = recv(fd, buf, cap, 0);
        if (r < 0) {
            if (errno == EINTR) {
                continue;
            }
            return SRMECH_ERR_IO;   /* recv timeout / peer error */
        }
        *out_n = (size_t)r;   /* r == 0 is EOF (peer closed) */
        return SRMECH_OK;
    }
}

srmech_status_t srmech_plat_tcp_write_all(srmech_plat_stream_conn_t *conn,
                                          const unsigned char *buf, size_t n)
{
    assert(conn != NULL);
    assert(buf != NULL || n == 0u);
    int fd;
    memcpy(&fd, conn->handle.bytes, sizeof fd);
    size_t sent = 0u;
    while (sent < n) {
        ssize_t w = send(fd, buf + sent, n - sent, 0);
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

srmech_status_t srmech_plat_tcp_conn_close(srmech_plat_stream_conn_t *conn)
{
    assert(conn != NULL);
    if (conn == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    int fd;
    assert(sizeof fd <= sizeof conn->handle.bytes);
    memcpy(&fd, conn->handle.bytes, sizeof fd);
    if (fd >= 0) {
        (void)shutdown(fd, SHUT_RDWR);
        (void)close(fd);
    }
    return SRMECH_OK;
}

#else  /* Windows (Winsock follow-up) / bare-metal: no TCP backend */

srmech_status_t srmech_plat_tcp_listen(const char *host, uint16_t port,
                                       srmech_plat_tcp_server_t *out,
                                       uint16_t *out_port)
{
    assert(srmech_plat_has_tcp() == 0);
    assert(out != NULL);
    (void)host; (void)port; (void)out; (void)out_port;
    return SRMECH_ERR_BAD_INPUT;   /* MCP HTTP+SSE C server declines → pure */
}

srmech_status_t srmech_plat_tcp_accept(srmech_plat_tcp_server_t *server,
                                       srmech_plat_stream_conn_t *conn_out,
                                       unsigned timeout_ms, int *got)
{
    assert(srmech_plat_has_tcp() == 0);
    assert(got != NULL);
    (void)server; (void)conn_out; (void)timeout_ms;
    *got = 0;
    return SRMECH_ERR_BAD_INPUT;
}

srmech_status_t srmech_plat_tcp_server_close(srmech_plat_tcp_server_t *server)
{
    assert(srmech_plat_has_tcp() == 0);
    assert(server != NULL);
    (void)server;
    return SRMECH_OK;
}

srmech_status_t srmech_plat_tcp_read_some(srmech_plat_stream_conn_t *conn,
                                          unsigned char *buf, size_t cap,
                                          size_t *out_n)
{
    assert(srmech_plat_has_tcp() == 0);
    assert(out_n != NULL);
    (void)conn; (void)buf; (void)cap;
    *out_n = 0u;
    return SRMECH_ERR_BAD_INPUT;
}

srmech_status_t srmech_plat_tcp_write_all(srmech_plat_stream_conn_t *conn,
                                          const unsigned char *buf, size_t n)
{
    assert(srmech_plat_has_tcp() == 0);
    assert(buf != NULL || n == 0u);
    (void)conn; (void)buf; (void)n;
    return SRMECH_ERR_BAD_INPUT;
}

srmech_status_t srmech_plat_tcp_conn_close(srmech_plat_stream_conn_t *conn)
{
    assert(srmech_plat_has_tcp() == 0);
    assert(conn != NULL);
    (void)conn;
    return SRMECH_OK;
}

#endif  /* SRMECH_PLAT_TCP_POSIX */

/* ================================================================== *
 * SLEEP (rc194) — nanosleep (POSIX) / Sleep (Windows). One consumer:
 * the MCP HTTP+SSE keepalive scanner. A sleepless target returns IO.
 * ================================================================== */

#if defined(SRMECH_PLAT_TCP_POSIX)

srmech_status_t srmech_plat_sleep_ms(unsigned ms)
{
    struct timespec ts;
    ts.tv_sec = (time_t)(ms / 1000u);
    ts.tv_nsec = (long)(ms % 1000u) * 1000000L;
    assert(ts.tv_nsec >= 0);
    assert(ts.tv_nsec < 1000000000L);
    (void)nanosleep(&ts, NULL);   /* early return on a signal is fine */
    return SRMECH_OK;
}

#elif defined(SRMECH_PLAT_STREAM_WIN)

srmech_status_t srmech_plat_sleep_ms(unsigned ms)
{
    assert(sizeof(DWORD) >= sizeof(unsigned));
    assert(ms <= 0xFFFFFFFFu);
    Sleep((DWORD)ms);
    return SRMECH_OK;
}

#else  /* bare-metal: no sleep backend */

srmech_status_t srmech_plat_sleep_ms(unsigned ms)
{
    assert(srmech_plat_has_tcp() == 0);
    (void)ms;
    return SRMECH_ERR_IO;
}

#endif  /* sleep backends */
