/* srmech_platform.h — the Platform Abstraction Layer (PAL), v0.7.5rc4.
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
 *   - STREAM IPC (planned rc5): listen/accept/connect/read/write over the
 *     AF_UNIX-socket (POSIX) / named-pipe (Windows) duality. Consumer:
 *     srmech_bus.c — the last raw-OS surface in the library.
 *
 * NOT exported in the public ABI (srmech.h): these are internal cross-TU
 * symbols, exactly like the srmech_simd_* HAL functions.
 *
 * JPL Power-of-Ten: no goto, no malloc, bounded, status returns, ≤60-line
 * functions, warnings-clean. License: GPL-3.0-or-later.
 */
#ifndef SRMECH_PLATFORM_H
#define SRMECH_PLATFORM_H

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

#endif /* SRMECH_PLATFORM_H */
