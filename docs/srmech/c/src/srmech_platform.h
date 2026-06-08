/* srmech_platform.h — the Platform Abstraction Layer (PAL), v0.7.5rc5.
 *
 * PAL is to the OPERATING SYSTEM what srmech_simd.{h,c} (the HAL) is to the
 * CPU: the SINGLE compilation unit where platform-specific code lives
 * (`_WIN32` / POSIX / bare-metal). The functional C cores
 * (`srmech_parallel.c`, `srmech_bus.c`, …) call ONLY these agnostic
 * primitives and carry NO `#ifdef _WIN32`. Adding an OS surface = a new
 * `srmech_plat_*` primitive here; the cores never change. In the user's
 * framing the OS *is* part of the hardware the binary runs on, so the PAL
 * is a second hardware-abstraction sibling of the HAL.
 *
 * Per [[feedback_simd_optimize_path_goes_through_hal]] generalised from the
 * CPU to the OS: "machine-specific bits go behind another *.h; the core
 * stays agnostic." This is what lets the complete C mirror of the Python
 * surface build standalone on embedded (no threads, no OS) OR a full OS.
 *
 * Surfaces (grown incrementally, one consumer retrofitted at a time):
 *   - THREADS (rc4): spawn / join + a capability query. The serial path is
 *     ALWAYS available, so a thread-less microcontroller keeps every
 *     capability (computed serially). First consumer: srmech_parallel.c.
 *     Tracked follow-up: the srmech_bus.c background thread.
 *   - STREAM IPC (rc5): listen/accept/connect/read/write over the
 *     AF_UNIX-socket (POSIX) / named-pipe (Windows) duality, with the
 *     endpoint-name -> OS-path mapping absorbed into the PAL. Consumer:
 *     srmech_bus.c — the last raw-OS surface in the library, now #ifdef-free.
 *
 * NOT exported in the public ABI (srmech.h): these are internal cross-TU
 * symbols, exactly like the srmech_simd_* HAL functions.
 *
 * JPL Power-of-Ten: no goto, no malloc, bounded, status returns, ≤60-line
 * functions, warnings-clean. License: GPL-3.0-or-later.
 */
#ifndef SRMECH_PLATFORM_H
#define SRMECH_PLATFORM_H

#include <stddef.h>   /* size_t (stream read/write) */
#include "srmech.h"   /* srmech_status_t */

/* The agnostic thread-entry signature — a plain void(void*) job. The PAL
 * adapts it to pthread's void*(void*) / Windows' DWORD WINAPI(LPVOID). */
typedef void (*srmech_plat_thread_fn)(void *arg);

/* Opaque thread handle. Holds the job (read by the PAL trampoline) plus
 * max-aligned storage the PAL .c reinterprets as the platform thread handle
 * (pthread_t on POSIX, HANDLE on Windows). No heap — handle lives in the
 * caller's storage and must outlive the thread (i.e. until join). */
#define SRMECH_PLAT_THREAD_STORAGE 16
typedef struct srmech_plat_thread {
    srmech_plat_thread_fn fn;
    void                 *arg;
    union {
        void        *align_ptr;
        long double  align_ld;
        unsigned char bytes[SRMECH_PLAT_THREAD_STORAGE];
    } handle;
} srmech_plat_thread_t;

/* 1 iff a real threading backend is compiled in; 0 on a thread-less target
 * (the caller then runs its work serially — the capability is preserved). */
int srmech_plat_has_threads(void);

/* Spawn `fn(arg)` on a new thread. SRMECH_OK on success (handle in *out).
 * On a thread-less build returns SRMECH_ERR_BAD_INPUT (the caller must check
 * srmech_plat_has_threads() first and take the serial path). */
srmech_status_t srmech_plat_thread_spawn(srmech_plat_thread_fn fn, void *arg,
                                         srmech_plat_thread_t *out);

/* Join a thread previously spawned (releases its platform handle). */
srmech_status_t srmech_plat_thread_join(srmech_plat_thread_t *handle);

/* ================================================================== *
 * STREAM IPC (rc5) — the AF_UNIX-socket / named-pipe duality.
 *
 * The bus calls ONLY these primitives; the name -> OS-path mapping
 * (POSIX ~/.srmech/bus-<name>.sock, Windows \\.\pipe\srmech-<name>)
 * lives entirely in srmech_platform.c. Framing, the Bio-TOTP cipher
 * and handler dispatch stay in srmech_bus.c — they are OS-agnostic.
 * ================================================================== */

/* Cap for the FULL derived OS path the PAL builds from the short name
 * (POSIX $HOME/.srmech/bus-<name>.sock / Windows \\.\pipe\srmech-<name>);
 * matches the bus's original SRMECH_BUS_PATH_MAX. */
#define SRMECH_PLAT_STREAM_PATH_MAX  512
/* Max-aligned opaque storage for one OS stream handle (POSIX int fd /
 * Windows HANDLE). Sized like the thread handle's storage. */
#define SRMECH_PLAT_STREAM_STORAGE   16

/* One bidirectional byte-stream connection (POSIX fd / Windows pipe HANDLE).
 * No heap — lives in the caller's storage. */
typedef struct srmech_plat_stream_conn {
    union {
        void         *align_ptr;
        long double   align_ld;
        unsigned char bytes[SRMECH_PLAT_STREAM_STORAGE];
    } handle;
} srmech_plat_stream_conn_t;

/* A bound, listening endpoint. Carries the derived OS path (POSIX: to
 * unlink the socket at close; Windows: to re-create pipe instances) plus
 * one OS handle slot (POSIX: listen_fd; Windows: the pre-created pending
 * pipe instance that the next accept() will connect). No heap. */
typedef struct srmech_plat_stream_server {
    char endpoint_path[SRMECH_PLAT_STREAM_PATH_MAX];
    union {
        void         *align_ptr;
        long double   align_ld;
        unsigned char bytes[SRMECH_PLAT_STREAM_STORAGE];
    } handle;
} srmech_plat_stream_server_t;

/* 1 iff a real stream-IPC backend is compiled in; 0 on a stream-less
 * (e.g. bare-metal) target, where the bus surface is unavailable. */
int srmech_plat_has_streams(void);

/* Bind + listen on the endpoint named `name`. *out receives the server
 * handle (its derived OS path + listener). SRMECH_OK on success. */
srmech_status_t srmech_plat_stream_listen(const char *name,
                                          srmech_plat_stream_server_t *out);

/* Block until exactly one client connects; return that connection in
 * *conn_out. POSIX accept()s a fresh fd; Windows connects the pending pipe
 * instance and pre-creates the next one (so the listener stays armed). */
srmech_status_t srmech_plat_stream_accept(srmech_plat_stream_server_t *server,
                                          srmech_plat_stream_conn_t *conn_out);

/* Close the listener: POSIX close(listen_fd) + unlink(path); Windows close
 * the pending pipe instance. Safe on a zero-initialised server. */
srmech_status_t srmech_plat_stream_server_close(
    srmech_plat_stream_server_t *server);

/* Connect to the endpoint named `name` as a client (*out = connection). */
srmech_status_t srmech_plat_stream_connect(const char *name,
                                           srmech_plat_stream_conn_t *out);

/* Read exactly n / write exactly n bytes over a connection, looping until
 * complete. EOF mid-read is SRMECH_ERR_IO. write_all does NOT flush on
 * Windows pipes (FlushFileBuffers deadlocks the request-reply pattern;
 * byte-mode WriteFile is already synchronously visible to the peer). */
srmech_status_t srmech_plat_stream_read_exact(srmech_plat_stream_conn_t *conn,
                                              unsigned char *buf, size_t n);
srmech_status_t srmech_plat_stream_write_all(srmech_plat_stream_conn_t *conn,
                                             const unsigned char *buf, size_t n);

/* Close one connection (POSIX close(fd) / Windows FlushFileBuffers-free
 * DisconnectNamedPipe+CloseHandle as appropriate). */
srmech_status_t srmech_plat_stream_conn_close(srmech_plat_stream_conn_t *conn);

#endif /* SRMECH_PLATFORM_H */
