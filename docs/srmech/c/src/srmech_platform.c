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
 * License: GPL-3.0-or-later.
 */

#include "srmech_platform.h"

#include <assert.h>
#include <string.h>

#if defined(_WIN32) || defined(_WIN64)
#  define SRMECH_PLAT_THREADS_WIN 1
#  include <windows.h>
#elif defined(__unix__) || defined(__APPLE__) || defined(__linux__)
#  define SRMECH_PLAT_THREADS_POSIX 1
#  include <pthread.h>
#endif

#if defined(SRMECH_PLAT_THREADS_POSIX)
_Static_assert(sizeof(pthread_t) <= SRMECH_PLAT_THREAD_STORAGE,
               "pthread_t does not fit srmech_plat_thread handle storage");
#elif defined(SRMECH_PLAT_THREADS_WIN)
_Static_assert(sizeof(HANDLE) <= SRMECH_PLAT_THREAD_STORAGE,
               "HANDLE does not fit srmech_plat_thread handle storage");
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
