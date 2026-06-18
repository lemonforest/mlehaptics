/*
 * srmech_ndjson.c — streaming NDJSON line reader.
 *
 * Mirrors the Python reference path in
 * `srmech.amsc.format.read_ndjson` — opens a file, walks it line by
 * line, skips empty lines, hands each non-empty line to a caller-
 * supplied callback together with its 1-indexed original line
 * number. JSON parsing stays in Python (the Python side uses
 * `MPRRecord.from_json_line` on the bytes we hand it); the speedup
 * is in file IO + line tokenisation.
 *
 * Task #201 Phase B4 — second native symbol in the srmech C library.
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto)        : OK
 *   - Rule 2 (bounded loops)  : OK — every loop bounded by file
 *                              size (caller-supplied) or by the
 *                              fixed read-buffer size.
 *   - Rule 3 (no malloc)      : OK — fixed-size thread-local line-
 *                              assembly buffer + stack chunk buffer.
 *                              #772 reentrancy trade: the line buffer
 *                              is per-thread (SRMECH_THREAD_LOCAL),
 *                              so srmech_ndjson_iter is now safe to
 *                              call from multiple threads concurrently
 *                              (each thread owns its own 1 MiB buffer).
 *                              Thread-local static is still Rule-3-
 *                              clean (static duration, no malloc) and
 *                              keeps the 1 MiB buffer off the stack.
 *   - Rule 4 (≤60 lines/fn)   : OK — split into chunk-process helper.
 *   - Rule 5 (≥2 asserts/fn)  : OK — input pointer + bound asserts
 *                              at every entry/state-transition point.
 *
 * Line semantics
 * --------------
 *   Line separator: '\n' (0x0A). Bare '\r' is NOT a separator
 *   (POSIX NDJSON convention; matches Python's `path.open("r")`
 *   universal-newlines but we work on bytes here, not text).
 *   A trailing CR before LF ('\r\n') is preserved as part of the
 *   line bytes and stripped by the caller (mirrors the Python
 *   side's `raw.strip()` call). Empty lines (zero-length after
 *   any CR-strip) are skipped silently — we never invoke the
 *   callback on them.
 *
 * License: MIT.
 */

#include "srmech.h"
#include "srmech_platform.h"   /* PAL streaming-read surface (rc164) */

#include <assert.h>
#include <stdint.h>
#include <string.h>

/* ------------------------------------------------------------------ *
 * Configuration knobs (compile-time, JPL Rule 2 bounds)
 * ------------------------------------------------------------------ */

/* Read buffer size — bytes pulled from disk per PAL streaming-read call.
 * 64 KiB matches glibc's default stdio block size on most kernels;
 * Windows ucrt is the same. Stack-resident.
 */
#define SRMECH_NDJSON_CHUNK_BYTES (64u * 1024u)

/* Maximum bytes per NDJSON line. AMSC ground-proof rows in
 * srmech/ephemerides-spectral run a few hundred bytes typically;
 * pathological rows with deep nested data can reach a few KB. 1 MiB
 * is a comfortable headroom and keeps the static buffer footprint
 * modest. Lines longer than this return SRMECH_ERR_OVERFLOW.
 */
#define SRMECH_NDJSON_MAX_LINE_BYTES (1u * 1024u * 1024u)

/* Line-assembly buffer (#772 reentrancy).
 *
 * At 1 MiB this is too large to stack-allocate safely per call, so it
 * stays a static-duration buffer — but qualified SRMECH_THREAD_LOCAL
 * so every thread gets its own copy. The buffer must persist across
 * srmech_ndjson_process_chunk invocations WITHIN a single
 * srmech_ndjson_iter call (a line can straddle chunk boundaries);
 * function-local thread-local static gives exactly that lifetime —
 * one private 1 MiB buffer per thread, reused across iter calls on
 * that thread. The buffer pointer is threaded explicitly into
 * process_chunk / emit so no helper references a file-scope global. */

/* ------------------------------------------------------------------ *
 * Helper: emit one assembled line to the callback if it's non-empty.
 *
 * The Python side's `read_ndjson` does `raw.strip()` — that strips
 * '\r' as well as whitespace. We trim a trailing '\r' here so the
 * bytes handed to the callback are LF-stripped (the chunk loop
 * already dropped the LF) AND CR-stripped, which is the equivalent
 * of Python's `raw.rstrip("\r\n")`. Caller can still .strip() the
 * Python side if it wants additional whitespace removal; we don't
 * do that in C to keep behaviour bytes-faithful.
 * ------------------------------------------------------------------ */
static srmech_status_t srmech_ndjson_emit(srmech_ndjson_line_cb cb,
                                          char                 *line_buf,
                                          size_t                line_len,
                                          size_t                lineno,
                                          void                 *user)
{
    assert(cb != NULL);
    assert(line_buf != NULL);

    size_t effective = line_len;
    if (effective > 0u && line_buf[effective - 1u] == '\r') {
        effective -= 1u;
    }
    if (effective == 0u) {
        /* Empty line — Python skips silently, we do too. The
         * lineno still advances upstream. */
        return SRMECH_OK;
    }
    return cb(line_buf, effective, lineno, user);
}

/* ------------------------------------------------------------------ *
 * Helper: process one chunk of bytes through the line-tokeniser
 * state machine. Updates *line_len_inout and *lineno_inout in
 * place; invokes the callback for every complete non-empty line.
 *
 * Phase B6 (Task #201) refactor: extracted out of
 * srmech_ndjson_iter to bring that function under JPL Rule 4's
 * 60-line limit. Same byte semantics as the original inline loop.
 * ------------------------------------------------------------------ */
static srmech_status_t srmech_ndjson_process_chunk(
    const uint8_t           *chunk,
    size_t                   n_read,
    srmech_ndjson_line_cb    cb,
    void                    *user,
    char                    *line_buf,
    size_t                  *line_len_inout,
    size_t                  *lineno_inout)
{
    assert(chunk != NULL);
    assert(cb != NULL);
    assert(line_buf != NULL);
    assert(line_len_inout != NULL);
    assert(lineno_inout != NULL);

    size_t line_len = *line_len_inout;
    size_t lineno = *lineno_inout;

    for (size_t i = 0u; i < n_read; i++) {
        const uint8_t b = chunk[i];
        if (b == (uint8_t)'\n') {
            const srmech_status_t st = srmech_ndjson_emit(
                cb, line_buf, line_len, lineno, user);
            if (st != SRMECH_OK) {
                *line_len_inout = line_len;
                *lineno_inout = lineno;
                return st;
            }
            line_len = 0u;
            lineno += 1u;
        } else {
            if (line_len >= SRMECH_NDJSON_MAX_LINE_BYTES) {
                *line_len_inout = line_len;
                *lineno_inout = lineno;
                return SRMECH_ERR_OVERFLOW;
            }
            line_buf[line_len] = (char)b;
            line_len += 1u;
        }
    }

    *line_len_inout = line_len;
    *lineno_inout = lineno;
    return SRMECH_OK;
}

/* ------------------------------------------------------------------ *
 * Public entry — declared in srmech.h.
 *
 * Open `path`, walk it line by line, invoke `cb(line, line_len,
 * lineno, user)` for every non-empty line. `lineno` is 1-indexed
 * over ALL lines in the file (including empties); the caller's
 * error messages then line up byte-exactly with the file.
 *
 * Errors:
 *   SRMECH_ERR_NULL_ARG     — path or cb is NULL.
 *   SRMECH_ERR_IO           — PAL rstream open / read failed (or no FS).
 *   SRMECH_ERR_OVERFLOW     — a line exceeds SRMECH_NDJSON_MAX_LINE_BYTES.
 *   <callback return value> — propagated as the function's return.
 *                              The callback may use SRMECH_ERR_BAD_INPUT
 *                              etc. to signal a malformed payload.
 * ------------------------------------------------------------------ */
srmech_status_t srmech_ndjson_iter(const char            *path,
                                   srmech_ndjson_line_cb  cb,
                                   void                  *user)
{
    if (path == NULL || cb == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(path != NULL);
    assert(cb != NULL);

    srmech_plat_rstream_t rs;
    srmech_status_t st = srmech_plat_rstream_open(path, &rs);
    if (st != SRMECH_OK) {
        return st;                       /* SRMECH_ERR_IO (or bare-metal stub) */
    }

    /* Per-thread line-assembly buffer (#772). Static duration (1 MiB
     * is too large to stack) but thread-local, so concurrent
     * srmech_ndjson_iter calls on different threads never collide. */
    static SRMECH_THREAD_LOCAL char line_buf[SRMECH_NDJSON_MAX_LINE_BYTES];
    uint8_t chunk[SRMECH_NDJSON_CHUNK_BYTES];
    size_t line_len = 0u;
    size_t lineno = 1u;
    int eof_reached = 0;

    while (!eof_reached) {
        size_t n_read = 0u;
        st = srmech_plat_rstream_read(
            &rs, chunk, SRMECH_NDJSON_CHUNK_BYTES, &n_read);
        if (st != SRMECH_OK) {           /* a mid-read error (rstream checked
                                          * the error flag) — not clean EOF */
            srmech_plat_rstream_close(&rs);
            return st;
        }
        if (n_read == 0u) {
            break;                        /* clean end-of-file */
        }
        st = srmech_ndjson_process_chunk(
            chunk, n_read, cb, user, line_buf, &line_len, &lineno);
        if (st != SRMECH_OK) {
            srmech_plat_rstream_close(&rs);
            return st;
        }
        if (n_read < SRMECH_NDJSON_CHUNK_BYTES) {
            eof_reached = 1;              /* short read with no error == EOF */
        }
    }

    if (st == SRMECH_OK && line_len > 0u) {
        st = srmech_ndjson_emit(cb, line_buf, line_len, lineno, user);
    }

    srmech_plat_rstream_close(&rs);
    return st;
}
