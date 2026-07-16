/*
 * srmech_progress.c — the C progress / introspection callback (0.9.0rc242, #840).
 *
 * Class-H (self-introspection) projected across the BARE-C HOST boundary. Today
 * srmech's introspection stream (~/.srmech/run-*.ndjson) is written ONLY by the
 * Python srmech.introspect.Writer at Python op boundaries — the C library itself
 * emits NOTHING, so a no-Python host cannot observe which op ran. This module
 * completes the everything-to-C surface: a host registers a callback with
 * srmech_set_progress_cb, and the central invoke spine (srmech_invoke.c's
 * iv_dispatch) fires it once per successfully-dispatched tool with a compact
 * canonical-JSON event describing the op.
 *
 * The event is built through the srmech_json canonical writer (the keystone), so
 * it is BYTE-IDENTICAL to CPython
 *   json.dumps({"category": <cat>, "mpr_version": "1.0", "op_name": <name>},
 *              sort_keys=True, ensure_ascii=False)
 * — the SAME shape (and ", " / ": " separators) srmech.introspect._event.serialize
 * emits. A host may append the line straight to its own NDJSON stream, enriching
 * it with a timestamp / pid the way the Python Writer does: the C library reports
 * WHAT ran, not WHEN — the clock is the host's, keeping the emit a pure function
 * of the dispatch (deterministic, byte-exact-testable, libm/time-free).
 *
 * OFF BY DEFAULT: with no callback registered the emit builder returns after a
 * single NULL-pointer test, so the hot dispatch path pays nothing.
 *
 * JPL: Rule 1 (no goto); Rule 3 (no malloc — the JSON value tree + the write
 * scratch are carved from thread-local static arenas, reentrant across threads
 * per the #772 SRMECH_THREAD_LOCAL pattern, cf. srmech_ndjson.c's line_buf);
 * Rule 8 (single-line object-like macros). srmech_set_progress_cb is a trivial
 * setter with no pointer/bounds invariant (cb + user_data are both nullable by
 * design), so it is on the Rule-5 exemption list (cargo-cult asserts are the
 * policy anti-pattern); srmech_progress_emit_dispatch carries its >= 2 asserts.
 *
 * ABI: this rc introduces the srmech_progress_cb_t function-pointer typedef,
 * which carries a CFUNCTYPE wire-format implication for the Python ctypes shim
 * (the v2->v3 / v3->v4 callback-typedef precedent), so SRMECH_ABI_VERSION bumps
 * 4 -> 5. The srmech_set_progress_cb symbol itself is a plain addition.
 */
#include "srmech.h"
#include "srmech_progress_internal.h"

#include <assert.h>
#include <string.h>

/* Process-global callback slot. A progress observer is process-wide (mirroring
 * the Python single-global srmech.introspect._ACTIVE_WRITER); set it before
 * spinning worker threads. A plain pointer pair, read once per dispatch. */
static srmech_progress_cb_t g_progress_cb = NULL;
static void                *g_progress_userdata = NULL;

srmech_progress_cb_t srmech_set_progress_cb(srmech_progress_cb_t cb,
                                            void *user_data)
{
    srmech_progress_cb_t prev = g_progress_cb;
    g_progress_userdata = user_data;
    g_progress_cb = cb;    /* publish the function pointer LAST */
    return prev;
}

/* Thread-local static build arena. Op names + categories are short dotted-ASCII
 * identifiers (well under ~96 bytes each); 512 bytes is generous headroom for
 * the 3-string value tree, the key-sort scratch, and the output line. */
#define SRMECH_PROGRESS_ARENA  512u
#define SRMECH_PROGRESS_OUTBUF 512u

void srmech_progress_emit_dispatch(const char *op_name, const char *category)
{
    static SRMECH_THREAD_LOCAL unsigned char build_ws[SRMECH_PROGRESS_ARENA];
    static SRMECH_THREAD_LOCAL unsigned char write_ws[SRMECH_PROGRESS_ARENA];
    static SRMECH_THREAD_LOCAL char out[SRMECH_PROGRESS_OUTBUF];
    srmech_progress_cb_t cb = g_progress_cb;
    const char *op  = (op_name  != NULL) ? op_name  : "";
    const char *cat = (category != NULL) ? category : "";
    srmech_json_builder_t b;
    srmech_json_value_t *vals[3];
    const char *keys[3];
    srmech_json_value_t *root;
    size_t out_len = 0u;
    srmech_status_t st;

    assert(op != NULL && cat != NULL);        /* the ternaries guarantee this */
    assert(sizeof out >= 2u);                 /* room for at least "{}" + NUL  */

    if (cb == NULL) { return; }               /* off by default: pay nothing  */
    if (srmech_json_builder_init(&b, build_ws, sizeof build_ws) != SRMECH_OK) {
        return;
    }
    /* Natural (already alphabetical) key order; the writer sorts regardless. */
    keys[0] = "category";
    keys[1] = "mpr_version";
    keys[2] = "op_name";
    vals[0] = srmech_json_new_string(&b, cat, (uint32_t)strlen(cat));
    vals[1] = srmech_json_new_string(&b, "1.0", 3u);
    vals[2] = srmech_json_new_string(&b, op, (uint32_t)strlen(op));
    root = srmech_json_new_object(&b, keys, vals, 3u);
    if (root == NULL || b.failed != 0) { return; }   /* arena exhausted -> drop */

    st = srmech_json_write_ws(root, out, sizeof out, &out_len,
                              write_ws, sizeof write_ws);
    if (st != SRMECH_OK || out_len >= sizeof out) { return; }
    out[out_len] = '\0';                      /* NUL-terminate for the char* cb */
    cb(out, g_progress_userdata);
}
