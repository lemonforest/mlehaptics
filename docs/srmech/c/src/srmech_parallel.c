/*
 * srmech_parallel.c — C-orchestration parity for the rc6 Python
 * Klein-4 four-sector PARALLEL cascade dispatch (#771; MS#20 rc7).
 *
 * The C peer for srmech.amsc.cascade.parallel.parallel_sector_dispatch.
 * Runs ONE caller-supplied cascade `body` across its ≤4 Klein-4
 * chirality sectors and writes the four sector duals. This closes the
 * C/Python parity gap rc6 left open: under srmech's full-parity
 * commitment the library must be able to do the four-sector dispatch
 * NATIVELY (a thread-less microcontroller with no host Python still
 * gets all four sectors — serially when there is no threading backend).
 *
 * THE FOUR SECTORS (F233 §1). Each sector `s` runs the SAME `body`
 * conjugated by its Klein-4 stream-transform T_s — the sector dual:
 *
 *     sector_dual(body, s, x) = inv_T_s( body( T_s(x) ) )
 *
 * The two commuting involution axes are γ₅ (orientation reversal,
 * srmech_cascade_chiral_flip_f64) and iω₇ (a per-element Class-C sign-
 * flip, srmech_cascade_reorient_f64 with orientation -1). Together they
 * generate Z₂ × Z₂, so every T_s is its OWN inverse (inv_T_s == T_s):
 *
 *   sector 0 (+,+) identity;  sector 1 (+,−) iω₇-flip only;
 *   sector 2 (−,+) γ₅-flip only  (its dual IS srmech_cascade_chiral_dual_f64);
 *   sector 3 (−,−) both / CPT mirror.
 *
 * INDEPENDENCE == THREAD-SAFETY (the F233 crux). Each sector writes
 * ONLY its own disjoint `out_sectors[s*n ..]` slice and uses ONLY its
 * own disjoint `scratch[s*n ..]` slice — 0 cross-thread writes. That
 * disjointness is exactly what makes the threaded path correct, so the
 * SERIAL result equals the THREADED result BIT-FOR-BIT (the sectors are
 * order-free). The composed atoms (chiral_flip / reorient) are
 * themselves reentrant (no shared static state), so a `body` that only
 * touches its own buffers makes the whole dispatch race-free.
 *
 * CAP AT 4 (F220). Klein-4 = Z₂ × Z₂ has order 4 and NO order-4+
 * element, so the dispatch is hard-capped at 4 sectors. Going past 4
 * needs the genuinely order-3 triality (F220) — NOT here.
 *
 * THREADING (portable shim, guarded like srmech_bus.c):
 *   POSIX   : pthread_create / pthread_join.
 *   Windows : CreateThread / WaitForMultipleObjects.
 *   else    : SERIAL fallback (compute the ≤4 sectors in a loop).
 * The serial fallback PRESERVES the capability — all 4 sectors are
 * computed, bit-identical to the threaded path. Thread handles live in
 * a fixed-size [4] stack array (JPL Rule 3: no malloc).
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto)        : early returns only.
 *   - Rule 2 (bounded loops)  : every loop bounded by n_sectors ≤ 4.
 *   - Rule 3 (no malloc)      : caller buffers + a [4] stack handle array.
 *   - Rule 4 (≤60 lines/func) : per-sector worker / spawn-join / transform
 *                               each factored into its own helper.
 *   - Rule 5 (≥2 asserts/fn)  : pointer / bound pre-conditions.
 *   - Rule 7 (return-value)   : srmech_status_t checked throughout.
 *   - Rule 10 (warnings clean): -Wall -Wextra -Wpedantic -Werror / /WX.
 *
 * ABI: new symbol(s) only — SRMECH_ABI_VERSION stays 3 (additive).
 *
 * License: GPL-3.0-or-later.
 */

#include "srmech.h"

#include <assert.h>
#include <stddef.h>
#include <stdint.h>

#if defined(_WIN32) || defined(_WIN64)
#  define SRMECH_PARALLEL_PLATFORM_WIN 1
#  include <windows.h>
#elif defined(__unix__) || defined(__APPLE__) || defined(__linux__)
#  define SRMECH_PARALLEL_PLATFORM_POSIX 1
#  include <pthread.h>
#endif

/* ------------------------------------------------------------------ *
 * Klein-4 sector labels — (γ₅, iω₇) sign pair per sector, mirroring
 * the rc6 Python SECTOR_LABELS. +1 = axis NOT flipped, -1 = flipped.
 * γ₅ is the reversal axis; iω₇ is the per-element sign-flip axis.
 * ------------------------------------------------------------------ */
typedef struct srmech_sector_label {
    int8_t gamma5;   /* -1 => apply chiral_flip (reversal)        */
    int8_t omega7;   /* -1 => apply per-element reorient(-1, .)   */
} srmech_sector_label_t;

static const srmech_sector_label_t SRMECH_SECTOR_LABELS[SRMECH_PARALLEL_SECTOR_CAP] = {
    { (int8_t)+1, (int8_t)+1 },  /* sector 0 — identity                 */
    { (int8_t)+1, (int8_t)-1 },  /* sector 1 — iω₇-flip only            */
    { (int8_t)-1, (int8_t)+1 },  /* sector 2 — γ₅-flip only (chiral_dual)*/
    { (int8_t)-1, (int8_t)-1 },  /* sector 3 — both / CPT mirror        */
};

/* ------------------------------------------------------------------ *
 * The Klein-4 stream-transform T_s (an involution, == inv_T_s).
 *
 * Composes the EXISTING C atoms: the iω₇ per-element Class-C
 * reorient(-1, .) then the γ₅ Class-C chiral_flip (reversal). Order
 * matches the rc6 Python _stream_transform (omega7 first, gamma5
 * second). In-place over `buf` (length n); chiral_flip_f64 supports
 * in == out, and reorient is applied element-by-element.
 * ------------------------------------------------------------------ */
static srmech_status_t srmech_parallel__stream_transform(
    const srmech_sector_label_t *label, double *buf, size_t n)
{
    assert(label != NULL);
    assert(buf != NULL || n == 0);
    if (label->omega7 < 0) {
        for (size_t i = 0; i < n; ++i) {
            srmech_status_t rc = srmech_cascade_reorient_f64(
                (int8_t)-1, buf[i], &buf[i]);
            if (rc != SRMECH_OK) {
                return rc;
            }
        }
    }
    if (label->gamma5 < 0) {
        srmech_status_t rc = srmech_cascade_chiral_flip_f64(buf, n, buf);
        if (rc != SRMECH_OK) {
            return rc;
        }
    }
    return SRMECH_OK;
}

/* ------------------------------------------------------------------ *
 * The per-sector worker: compute one sector dual into its OWN disjoint
 * output + scratch slices.
 *
 *   scratch_slice = T_s(in)         (T_s in-place on a copy of `in`)
 *   out_slice     = body(scratch_slice)
 *   out_slice     = T_s(out_slice)  (inv_T_s == T_s, in-place)
 *
 * Reads ONLY `in` (shared, read-only) and writes ONLY its own slices —
 * the F233 4-way independence, which is what makes the threaded path
 * correct AND order-free (serial == threaded bit-for-bit).
 * ------------------------------------------------------------------ */
static srmech_status_t srmech_parallel__run_sector(
    srmech_cascade_body_f64 body, void *user,
    const double *in, size_t n, uint32_t sector,
    double *out_slice, double *scratch_slice)
{
    assert(body != NULL);
    assert(out_slice != NULL || n == 0);
    assert(scratch_slice != NULL || n == 0);
    assert(sector < (uint32_t)SRMECH_PARALLEL_SECTOR_CAP);
    const srmech_sector_label_t *label = &SRMECH_SECTOR_LABELS[sector];
    /* Copy `in` into the sector's own scratch, then T_s in-place. */
    for (size_t i = 0; i < n; ++i) {
        scratch_slice[i] = in[i];
    }
    srmech_status_t rc = srmech_parallel__stream_transform(
        label, scratch_slice, n);
    if (rc != SRMECH_OK) {
        return rc;
    }
    rc = body(scratch_slice, n, out_slice, user);
    if (rc != SRMECH_OK) {
        return rc;
    }
    /* inv_T_s == T_s: apply the same transform in-place to the output. */
    return srmech_parallel__stream_transform(label, out_slice, n);
}

/* ------------------------------------------------------------------ *
 * Argument validation + the SERIAL fallback (always available;
 * preserves the capability on thread-less targets and is the bit-exact
 * reference the threaded path must match).
 * ------------------------------------------------------------------ */
static srmech_status_t srmech_parallel__validate(
    srmech_cascade_body_f64 body, const double *in, uint32_t n_sectors,
    const double *out_sectors, size_t n, const double *scratch,
    size_t scratch_len)
{
    /* Runtime guards FIRST — every documented clean-error input
     * (NULL ptr, n_sectors out of 1..4, scratch too small) returns a
     * status; the asserts below pin invariants that hold only AFTER
     * validation passes, so a debug build never aborts on a caller
     * error the contract says to reject cleanly. */
    if (body == NULL || out_sectors == NULL || scratch == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n > 0 && in == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n_sectors < 1u || n_sectors > (uint32_t)SRMECH_PARALLEL_SECTOR_CAP) {
        /* CAP-AT-4: Klein-4 (Z₂ × Z₂) has no order-4+ element. 8+
         * sectors need the order-3 triality (F220) — not here. */
        return SRMECH_ERR_BAD_INPUT;
    }
    if (scratch_len < (size_t)n_sectors * n) {
        return SRMECH_ERR_OVERFLOW;
    }
    /* Post-validation invariants. */
    assert(n_sectors >= 1u && n_sectors <= (uint32_t)SRMECH_PARALLEL_SECTOR_CAP);
    assert(scratch_len >= (size_t)n_sectors * n);
    return SRMECH_OK;
}

#if !defined(SRMECH_PARALLEL_PLATFORM_POSIX) && !defined(SRMECH_PARALLEL_PLATFORM_WIN)
static srmech_status_t srmech_parallel__serial(
    srmech_cascade_body_f64 body, void *user, const double *in, size_t n,
    uint32_t n_sectors, double *out_sectors, double *scratch)
{
    assert(body != NULL);
    assert(n_sectors >= 1u && n_sectors <= (uint32_t)SRMECH_PARALLEL_SECTOR_CAP);
    for (uint32_t s = 0; s < n_sectors; ++s) {
        srmech_status_t rc = srmech_parallel__run_sector(
            body, user, in, n, s,
            out_sectors + (size_t)s * n, scratch + (size_t)s * n);
        if (rc != SRMECH_OK) {
            return rc;
        }
    }
    return SRMECH_OK;
}
#endif

/* ------------------------------------------------------------------ *
 * Threaded backend — per-sector job + the spawn-join over a fixed [4]
 * stack handle array (JPL Rule 3: no malloc). On POSIX/Windows the ≤4
 * sectors run concurrently; the disjoint-slice contract makes the
 * result identical to the serial path. The job struct + runner are only
 * compiled when a threading backend is present (the thread-less path
 * uses srmech_parallel__serial directly).
 * ------------------------------------------------------------------ */
#if defined(SRMECH_PARALLEL_PLATFORM_POSIX) || defined(SRMECH_PARALLEL_PLATFORM_WIN)
typedef struct srmech_sector_job {
    srmech_cascade_body_f64 body;
    void                   *user;
    const double           *in;
    size_t                  n;
    uint32_t                sector;
    double                 *out_slice;
    double                 *scratch_slice;
    srmech_status_t         status;
} srmech_sector_job_t;

static void srmech_parallel__job_run(srmech_sector_job_t *job)
{
    assert(job != NULL);
    assert(job->body != NULL);
    job->status = srmech_parallel__run_sector(
        job->body, job->user, job->in, job->n, job->sector,
        job->out_slice, job->scratch_slice);
}
#endif

#if defined(SRMECH_PARALLEL_PLATFORM_POSIX)
static void *srmech_parallel__thread_posix(void *arg)
{
    assert(arg != NULL);
    srmech_sector_job_t *job = (srmech_sector_job_t *)arg;
    assert(job->body != NULL);
    srmech_parallel__job_run(job);
    return NULL;
}

static srmech_status_t srmech_parallel__threaded(
    srmech_cascade_body_f64 body, void *user, const double *in, size_t n,
    uint32_t n_sectors, double *out_sectors, double *scratch)
{
    assert(body != NULL);
    assert(n_sectors >= 1u && n_sectors <= (uint32_t)SRMECH_PARALLEL_SECTOR_CAP);
    srmech_sector_job_t jobs[SRMECH_PARALLEL_SECTOR_CAP];
    pthread_t           threads[SRMECH_PARALLEL_SECTOR_CAP];
    uint32_t            spawned = 0;
    for (uint32_t s = 0; s < n_sectors; ++s) {
        jobs[s].body = body;          jobs[s].user = user;
        jobs[s].in = in;              jobs[s].n = n;
        jobs[s].sector = s;           jobs[s].status = SRMECH_ERR_INTERNAL;
        jobs[s].out_slice = out_sectors + (size_t)s * n;
        jobs[s].scratch_slice = scratch + (size_t)s * n;
        if (pthread_create(&threads[s], NULL,
                           srmech_parallel__thread_posix, &jobs[s]) != 0) {
            break;  /* fall back to serial for the remaining sectors */
        }
        spawned = s + 1u;
    }
    for (uint32_t s = 0; s < spawned; ++s) {
        (void)pthread_join(threads[s], NULL);
    }
    for (uint32_t s = spawned; s < n_sectors; ++s) {
        srmech_parallel__job_run(&jobs[s]);  /* spawn-failure tail */
    }
    for (uint32_t s = 0; s < n_sectors; ++s) {
        if (jobs[s].status != SRMECH_OK) {
            return jobs[s].status;
        }
    }
    return SRMECH_OK;
}
#elif defined(SRMECH_PARALLEL_PLATFORM_WIN)
static DWORD WINAPI srmech_parallel__thread_win(LPVOID arg)
{
    assert(arg != NULL);
    srmech_sector_job_t *job = (srmech_sector_job_t *)arg;
    assert(job->body != NULL);
    srmech_parallel__job_run(job);
    return 0u;
}

static srmech_status_t srmech_parallel__threaded(
    srmech_cascade_body_f64 body, void *user, const double *in, size_t n,
    uint32_t n_sectors, double *out_sectors, double *scratch)
{
    assert(body != NULL);
    assert(n_sectors >= 1u && n_sectors <= (uint32_t)SRMECH_PARALLEL_SECTOR_CAP);
    srmech_sector_job_t jobs[SRMECH_PARALLEL_SECTOR_CAP];
    HANDLE              threads[SRMECH_PARALLEL_SECTOR_CAP];
    DWORD               spawned = 0u;
    for (uint32_t s = 0; s < n_sectors; ++s) {
        jobs[s].body = body;          jobs[s].user = user;
        jobs[s].in = in;              jobs[s].n = n;
        jobs[s].sector = s;           jobs[s].status = SRMECH_ERR_INTERNAL;
        jobs[s].out_slice = out_sectors + (size_t)s * n;
        jobs[s].scratch_slice = scratch + (size_t)s * n;
        threads[spawned] = CreateThread(
            NULL, 0, srmech_parallel__thread_win, &jobs[s], 0, NULL);
        if (threads[spawned] == NULL) {
            srmech_parallel__job_run(&jobs[s]);  /* spawn failure: serial */
        } else {
            spawned++;
        }
    }
    if (spawned > 0u) {
        (void)WaitForMultipleObjects(spawned, threads, TRUE, INFINITE);
        for (DWORD t = 0; t < spawned; ++t) {
            (void)CloseHandle(threads[t]);
        }
    }
    for (uint32_t s = 0; s < n_sectors; ++s) {
        if (jobs[s].status != SRMECH_OK) {
            return jobs[s].status;
        }
    }
    return SRMECH_OK;
}
#endif

/* ------------------------------------------------------------------ *
 * Public entry — see srmech.h for the full contract.
 * ------------------------------------------------------------------ */
srmech_status_t srmech_cascade_parallel_sector_dispatch(
    srmech_cascade_body_f64 body, void *user,
    const double *in, size_t n,
    uint32_t n_sectors,
    double  *out_sectors,
    double  *scratch, size_t scratch_len)
{
    srmech_status_t rc = srmech_parallel__validate(
        body, in, n_sectors, out_sectors, n, scratch, scratch_len);
    if (rc != SRMECH_OK) {
        return rc;
    }
    assert(body != NULL);
    assert(out_sectors != NULL && scratch != NULL);
#if defined(SRMECH_PARALLEL_PLATFORM_POSIX) || defined(SRMECH_PARALLEL_PLATFORM_WIN)
    return srmech_parallel__threaded(
        body, user, in, n, n_sectors, out_sectors, scratch);
#else
    /* No threading backend (thread-less microcontroller): SERIAL
     * fallback preserves the four-sector capability, bit-identical to
     * the threaded path (the sectors are independent / order-free). */
    return srmech_parallel__serial(
        body, user, in, n, n_sectors, out_sectors, scratch);
#endif
}
