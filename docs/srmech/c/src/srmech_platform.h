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

/* ================================================================== *
 * FILE I/O (rc161) — the last raw-OS surface in the library.
 *
 * File access is portable stdio (fopen/fread/fwrite/fseek), so POSIX and
 * Windows share ONE implementation; only the presence of a filesystem
 * differs. Callers that read/write files (srmech_config, and — retrofit
 * follow-up — srmech_genome / srmech_ndjson) go through these primitives
 * instead of carrying their own fopen, so the OS file surface lives in
 * exactly one TU, like threads + streams above. A bare-metal target with
 * no filesystem reports has_filesystem() == 0 and every call returns
 * SRMECH_ERR_IO; such a target feeds bytes directly (e.g. a flash blob to
 * srmech_config_load_toml) instead.
 * ================================================================== */

/* 1 iff a filesystem-backed file backend is compiled in (POSIX / Windows);
 * 0 on a bare-metal target with no filesystem. */
int srmech_plat_has_filesystem(void);

/* Read up to `buf_cap` bytes of `path` into `buf`; *out_len gets the count.
 * A file larger than buf_cap is SRMECH_ERR_OVERFLOW (nothing partial is
 * relied upon). Missing / unreadable file → SRMECH_ERR_IO. */
srmech_status_t srmech_plat_file_read(const char *path, unsigned char *buf,
                                      size_t buf_cap, size_t *out_len);

/* Read exactly `len` bytes from `path` starting at byte `offset` into `buf`.
 * Short read (offset+len past EOF) → SRMECH_ERR_IO. */
srmech_status_t srmech_plat_file_read_region(const char *path, size_t offset,
                                             unsigned char *buf, size_t len);

/* Write `len` bytes of `data` to `path`. `append` != 0 opens in append mode
 * ("ab"); else truncate ("wb"). fopen/fwrite/fclose failure → SRMECH_ERR_IO. */
srmech_status_t srmech_plat_file_write(const char *path, int append,
                                       const unsigned char *data, size_t len);

/* Byte length of `path` into *out_size. Missing / unstattable → SRMECH_ERR_IO. */
srmech_status_t srmech_plat_file_size(const char *path, size_t *out_size);

/* ================================================================== *
 * DIRECTORY ITERATION (rc163) — the POSIX opendir / Win32 FindFirstFile
 * duality, absorbed into the PAL so a caller (srmech_genome's §43 *.chr
 * pack/explode listing) carries NO `#ifdef _WIN32`. The iterator yields
 * every entry name in a directory; the caller filters (e.g. by suffix).
 * No heap — the OS handle + a one-entry lookahead live in the caller's
 * `srmech_plat_dir_t` storage. Win32's FindFirstFile reads the first
 * entry at open, so it is buffered as the lookahead.
 * ================================================================== */

/* Max bytes for one directory-entry name (filename only, NUL-terminated). */
#define SRMECH_PLAT_DIR_NAME_MAX 256
/* Max-aligned opaque storage for one OS dir handle (POSIX DIR* / Win HANDLE). */
#define SRMECH_PLAT_DIR_STORAGE  16

/* One open directory iterator. No heap — lives in the caller's storage. */
typedef struct srmech_plat_dir {
    union {
        void         *align_ptr;
        long double   align_ld;
        unsigned char bytes[SRMECH_PLAT_DIR_STORAGE];
    } handle;
    char pending[SRMECH_PLAT_DIR_NAME_MAX];  /* Win32 FindFirstFile lookahead */
    int  pending_valid;                       /* 1 iff `pending` holds an entry */
} srmech_plat_dir_t;

/* 1 iff a directory-listing backend is compiled in (POSIX / Windows); 0 on a
 * bare-metal target with no filesystem. */
int srmech_plat_has_dirlist(void);

/* Open `path` for iteration; *out receives the handle. SRMECH_ERR_IO if the
 * directory cannot be opened (the caller may treat that as "no entries"). */
srmech_status_t srmech_plat_dir_open(const char *path, srmech_plat_dir_t *out);

/* Fetch the next entry name into `name` (capacity `name_cap`). *have is set to
 * 1 and `name` written when an entry is produced, or 0 at end-of-directory.
 * SRMECH_ERR_OVERFLOW if a name does not fit `name_cap`. */
srmech_status_t srmech_plat_dir_next(srmech_plat_dir_t *dir, char *name,
                                     size_t name_cap, int *have);

/* Close the iterator (POSIX closedir / Win32 FindClose). Safe on a
 * zero-initialised handle. */
srmech_status_t srmech_plat_dir_close(srmech_plat_dir_t *dir);

/* ================================================================== *
 * STREAMING READ (rc164) — a persistent read handle so a caller can pull a
 * file in fixed chunks without loading it whole (the §B4 ndjson tokeniser,
 * which assembles lines across chunk boundaries). Part of the FILE backend
 * (portable stdio, shared `srmech_plat_has_filesystem`); no new accessor.
 * The OS handle (a portable FILE*) lives in the caller's storage — no heap,
 * and srmech_platform.h stays free of <stdio.h>.
 * ================================================================== */

/* Max-aligned opaque storage for one streaming-read handle (a FILE*). */
#define SRMECH_PLAT_RSTREAM_STORAGE 16

/* One open streaming-read handle. No heap — lives in the caller's storage. */
typedef struct srmech_plat_rstream {
    union {
        void         *align_ptr;
        long double   align_ld;
        unsigned char bytes[SRMECH_PLAT_RSTREAM_STORAGE];
    } handle;
} srmech_plat_rstream_t;

/* Open `path` for streaming reads; *out receives the handle. SRMECH_ERR_IO if
 * the file cannot be opened. */
srmech_status_t srmech_plat_rstream_open(const char *path,
                                         srmech_plat_rstream_t *out);

/* Read up to `cap` bytes into `buf`; *out_n receives the count actually read
 * (0 at end-of-file). SRMECH_ERR_IO on a read error (short read with the
 * stream's error flag set). A short read with no error is a clean partial/EOF. */
srmech_status_t srmech_plat_rstream_read(srmech_plat_rstream_t *rs, void *buf,
                                         size_t cap, size_t *out_n);

/* Close the handle (POSIX/Win fclose). Safe on a zero-initialised handle. */
srmech_status_t srmech_plat_rstream_close(srmech_plat_rstream_t *rs);

#endif /* SRMECH_PLATFORM_H */
