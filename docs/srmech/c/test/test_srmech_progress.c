/*
 * test_srmech_progress.c — bare-C-HOST smoke for the progress / introspection
 * callback (0.9.0rc242, #840). Proves a C-only host (no Python) can register a
 * srmech_progress_cb_t with srmech_set_progress_cb and OBSERVE which op the
 * central invoke spine dispatched — the everything-to-C completion of Class-H
 * self-introspection (today introspection is Python-only; the C library
 * otherwise emits nothing).
 *
 * Checks, via runtime if-guards (NOT assert — Release/NDEBUG in the pedantic CI
 * strips assert, so this doubles as the warnings-as-errors compile gate AND a
 * real value check when run):
 *   1. OFF BY DEFAULT — a dispatch with no callback registered emits nothing.
 *   2. REGISTER — a dispatch fires the callback EXACTLY once with the canonical
 *      event {"category": "cascade", "mpr_version": "1.0",
 *             "op_name": "srmech.cascade.net_chirality"} (sorted keys,
 *      ", " / ": " separators — byte-identical to the Python introspect
 *      serialize shape via srmech_json_write_ws).
 *   3. CLEAR — srmech_set_progress_cb returns the PREVIOUS callback, and after
 *      clearing (cb == NULL) a dispatch is silent again.
 *
 * Run it (exit 0 = all pass):
 *   ./build/test_srmech_progress
 */
#include "srmech.h"

#include <stdio.h>
#include <string.h>

static char g_captured[512];
static int  g_count;

static void observer(const char *event_json, void *user_data)
{
    size_t n;
    (void)user_data;
    ++g_count;
    n = strlen(event_json);
    if (n >= sizeof g_captured) { n = sizeof g_captured - 1u; }
    memcpy(g_captured, event_json, n);
    g_captured[n] = '\0';
}

/* Dispatch one tool through the C invoke spine; return 0 on a clean
 * SRMECH_INVOKE_DISPATCHED, -1 otherwise. */
static int run_one(const char *name, const char *args,
                   unsigned char *ws, size_t ws_len)
{
    char buf[4096];
    size_t out_len = 0u;
    int out_kind = -1;
    srmech_status_t st = srmech_invoke_tool(name, args, strlen(args),
                                            ws, ws_len, buf, sizeof buf,
                                            &out_len, &out_kind);
    if (st != SRMECH_OK) {
        fprintf(stderr, "invoke status=%d\n", (int)st);
        return -1;
    }
    if (out_kind != SRMECH_INVOKE_DISPATCHED) {
        fprintf(stderr, "not dispatched (out_kind=%d)\n", out_kind);
        return -1;
    }
    return 0;
}

int main(void)
{
    /* net_chirality: an int8-range plain-int LIST in, one int out -- always a
     * clean batch-1 C dispatch (cf. c/test parity + the Python rc231 test). */
    const char *name = "srmech.cascade.net_chirality";
    const char *args = "{\"orientations\": [1, -1, -1]}";
    const char *expect =
        "{\"category\": \"cascade\", \"mpr_version\": \"1.0\", "
        "\"op_name\": \"srmech.cascade.net_chirality\"}";
    static unsigned char ws[131072];
    srmech_progress_cb_t prev;

    /* 1. OFF BY DEFAULT: no callback registered -> no emit. */
    g_count = 0;
    if (run_one(name, args, ws, sizeof ws) != 0) { return 1; }
    if (g_count != 0) {
        fprintf(stderr, "emit with no callback (count=%d)\n", g_count);
        return 1;
    }

    /* 2. REGISTER -> exactly one canonical event. */
    prev = srmech_set_progress_cb(observer, NULL);
    if (prev != NULL) {
        fprintf(stderr, "expected no previous callback\n");
        return 1;
    }
    g_count = 0;
    g_captured[0] = '\0';
    if (run_one(name, args, ws, sizeof ws) != 0) { return 1; }
    if (g_count != 1) {
        fprintf(stderr, "expected 1 emit, got %d\n", g_count);
        return 1;
    }
    if (strcmp(g_captured, expect) != 0) {
        fprintf(stderr, "event mismatch\n got: %s\n exp: %s\n",
                g_captured, expect);
        return 1;
    }

    /* 3. CLEAR: set_progress_cb returns the previous cb; a cleared slot is
     * silent again. */
    prev = srmech_set_progress_cb(NULL, NULL);
    if (prev != observer) {
        fprintf(stderr, "set_progress_cb did not return the previous cb\n");
        return 1;
    }
    g_count = 0;
    if (run_one(name, args, ws, sizeof ws) != 0) { return 1; }
    if (g_count != 0) {
        fprintf(stderr, "emit after clear (count=%d)\n", g_count);
        return 1;
    }

    printf("test_srmech_progress: OK  %s\n", expect);
    return 0;
}
