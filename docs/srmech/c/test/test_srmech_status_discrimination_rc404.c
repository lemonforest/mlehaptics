/*
 * test_srmech_status_discrimination_rc404.c — the rc404 (`#T1069`) gate for
 * the SRMECH_ERR_OVERFLOW / SRMECH_ERR_LIMIT split.
 *
 * WHAT IT ASSERTS. For each row: a caller holding the returned status must be
 * able to decide, CORRECTLY, whether growing its arena could change the
 * outcome. Through rc403 it could not — srmech_json_parse and
 * srmech_toml_parse returned SRMECH_ERR_OVERFLOW both for "your arena was too
 * small" (grow and retry) and for "this integer does not fit in int64" /
 * "this document is nested past a compiled-in cap" (retrying is futile). The
 * two are indistinguishable at status 4, so every caller grow-loop doubled its
 * arena to the cap and re-parsed at every step before declining — measured at
 * 13 native calls and ~512 MiB for a verdict fixed at the first byte. The
 * answer stayed CORRECT throughout; it was the COST that was wrong.
 *
 * THE TRUTH COLUMN HAS THREE VALUES, NOT TWO. An earlier draft of this gate
 * asserted `is_retryable(status) == truth` over a BOOLEAN truth column, with
 * `is_retryable(s) := (s == SRMECH_ERR_OVERFLOW)`. That gate is PERMANENTLY
 * RED and cannot be satisfied by any version of the library: two of its rows
 * are valid documents parsed with a big arena, which return SRMECH_OK, and
 * `is_retryable(SRMECH_OK)` is false while their truth value is "retryable"
 * (a bigger arena is exactly what made them succeed). A boolean predicate
 * cannot express "this row is not about retryability at all". Hence:
 *
 *   TRUTH_RETRYABLE      the arena really was too small -> MUST be
 *                        SRMECH_ERR_OVERFLOW, the one status a grow-loop
 *                        may act on.
 *   TRUTH_NOT_RETRYABLE  growing cannot help AND the document must be
 *                        declined -> MUST be non-OK and MUST NOT be
 *                        SRMECH_ERR_OVERFLOW.
 *   TRUTH_EXPECT_OK      a valid document with a big arena -> MUST be
 *                        SRMECH_OK. These rows pin that the gate has not
 *                        simply broken the parser.
 *
 * NON-VACUITY, which is the part rc403's lesson demands. Measured by building
 * this file against both libraries:
 *
 *   against rc403 (pre-split):   rows=12  failures=5   EXIT=1
 *   against rc404 (post-split):  rows=12  failures=0   EXIT=0
 *
 * The five are JSON rows 3/4/5 and TOML rows 3/4 — every NOT_RETRYABLE row
 * whose site this rc moves. Three properties make it a real instrument:
 *
 *   1. The NEGATIVE CONTROLS (syntax error, NaN literal) return
 *      SRMECH_ERR_BAD_INPUT in BOTH builds and pass in both. So the gate is
 *      not "everything returns 4", and a change that collapsed every status
 *      to one value would fail it.
 *   2. The EXPECT_OK and RETRYABLE rows pass in BOTH builds. So the gate is
 *      not "everything is broken", and a change that made the parser decline
 *      valid input, or stop reporting genuine exhaustion as OVERFLOW, fails it.
 *   3. It CANNOT be satisfied by adding the enum constant. SRMECH_ERR_LIMIT
 *      existing changes no return value; only re-statusing the sites does.
 *
 * PORTABILITY (rc402 shipped ee130f377 for an MSVC C2124 on `1.0 / 0.0`, and
 * MSVC is the cell most likely to reject a constant): every int64-boundary and
 * over-long literal here is BUILT AT RUNTIME by snprintf and loops. There is
 * no compile-time division and no bare 9223372036854775808 literal, which
 * would not fit int64_t and is a constraint violation to write.
 *
 * The arena is a 1 MiB file-scope buffer (JPL Rule 3: no malloc). That is
 * ~30,000 json values against documents of a few dozen bytes, so on the BIG
 * rows arena exhaustion is not a live hypothesis and an OVERFLOW there can
 * only mean the conflation.
 *
 * No Python, no test framework — printf + count, like test_srmech_json.c.
 * Exits 0 on all-pass, non-zero on any fail.
 */

#include "srmech.h"

#include <stdint.h>
#include <stdio.h>
#include <string.h>

static int g_passed = 0;
static int g_failed = 0;

/* BIG arena: comfortably larger than any document below needs, so that an
 * SRMECH_ERR_OVERFLOW on a BIG row cannot be genuine exhaustion. */
static unsigned char g_ws[1024u * 1024u];

/* TINY arena: smaller than the smallest useful parse, so a valid document
 * against it MUST report genuine, retryable exhaustion. */
#define TINY_WS_BYTES 64u

typedef enum truth {
    TRUTH_RETRYABLE = 0,      /* must be SRMECH_ERR_OVERFLOW               */
    TRUTH_NOT_RETRYABLE = 1,  /* must be non-OK and NOT SRMECH_ERR_OVERFLOW */
    TRUTH_EXPECT_OK = 2       /* must be SRMECH_OK                          */
} truth_t;

static const char *status_name(srmech_status_t st)
{
    switch (st) {
    case SRMECH_OK:             return "OK";
    case SRMECH_ERR_NULL_ARG:   return "NULL_ARG";
    case SRMECH_ERR_BAD_INPUT:  return "BAD_INPUT";
    case SRMECH_ERR_IO:         return "IO";
    case SRMECH_ERR_OVERFLOW:   return "OVERFLOW";
    case SRMECH_ERR_NOT_IMPL:   return "NOT_IMPL";
    case SRMECH_ERR_INTERNAL:   return "INTERNAL";
    case SRMECH_CANCELLED:      return "CANCELLED";
    case SRMECH_ERR_LIMIT:      return "LIMIT";
    default:                    return "?";
    }
}

static const char *truth_name(truth_t t)
{
    if (t == TRUTH_RETRYABLE) { return "RETRYABLE"; }
    if (t == TRUTH_EXPECT_OK) { return "expect-OK"; }
    return "not-retryable";
}

/* The whole contract, in one place. */
static int status_matches_truth(srmech_status_t st, truth_t t)
{
    if (t == TRUTH_RETRYABLE)  { return st == SRMECH_ERR_OVERFLOW; }
    if (t == TRUTH_EXPECT_OK)  { return st == SRMECH_OK; }
    return (st != SRMECH_OK) && (st != SRMECH_ERR_OVERFLOW);
}

static void record(const char *label, size_t arena, srmech_status_t st,
                   truth_t t)
{
    int ok = status_matches_truth(st, t);
    if (ok) {
        g_passed++;
    } else {
        g_failed++;
    }
    printf("  %-4s %-28s arena=%-9lu -> %-9s truth=%-14s %s\n",
           ok ? "PASS" : "FAIL", label, (unsigned long)arena,
           status_name(st), truth_name(t), ok ? "" : "<-- FAIL");
}

static void check_json(const char *label, const char *doc, size_t arena,
                       truth_t t)
{
    srmech_json_value_t *root = NULL;
    srmech_status_t st = srmech_json_parse(doc, strlen(doc), g_ws, arena,
                                           &root);
    record(label, arena, st, t);
}

static void check_toml(const char *label, const char *doc, size_t arena,
                       truth_t t)
{
    srmech_toml_value_t *root = NULL;
    srmech_status_t st = srmech_toml_parse(doc, strlen(doc), g_ws, arena,
                                           &root);
    record(label, arena, st, t);
}

/* Write `n` copies of `c` then NUL. Built at runtime so no source literal is
 * long enough to trip a compiler's minimum-string-length limit. */
static void fill_repeat(char *buf, size_t n, char c)
{
    size_t k;
    for (k = 0; k < n; k++) { buf[k] = c; }
    buf[n] = '\0';
}

/* `[[[...80 deep...]]]` — past SRMECH_JSON_MAX_DEPTH / SRMECH_TOML_MAX_DEPTH
 * (both 64), so it declines for a STRUCTURAL reason at any arena size. */
static void build_deep_array(char *buf, size_t depth)
{
    size_t k;
    for (k = 0; k < depth; k++) { buf[k] = '['; }
    for (k = 0; k < depth; k++) { buf[depth + k] = ']'; }
    buf[2u * depth] = '\0';
}

static void run_json(void)
{
    char big_int[64];
    char long_lit[96];
    char deep[192];
    char toobig[64];

    printf("JSON srmech_json_parse\n");

    /* 1-2: the ONLY rows about the arena itself. */
    check_json("1 valid doc, TINY arena", "{\"a\":[1,2,3]}", TINY_WS_BYTES,
               TRUTH_RETRYABLE);
    check_json("2 valid doc, BIG arena", "{\"a\":[1,2,3]}", sizeof(g_ws),
               TRUTH_EXPECT_OK);

    /* 3: INT64_MAX + 1, built by hand so no out-of-range source literal is
     * written. INT64_MAX is 9223372036854775807; +1 carries into ...808. */
    (void)snprintf(big_int, sizeof(big_int), "%lld808",
                   (long long)(INT64_MAX / 1000));
    check_json("3 int > int64, BIG arena", big_int, sizeof(g_ws),
               TRUTH_NOT_RETRYABLE);

    /* 4: 70 '1' digits — past the 64-byte tmp[] staging bound. */
    fill_repeat(long_lit, 70u, '1');
    check_json("4 >=63-byte literal, BIG", long_lit, sizeof(g_ws),
               TRUTH_NOT_RETRYABLE);

    /* 5: nesting past the compiled-in depth cap. */
    build_deep_array(deep, 80u);
    check_json("5 depth-80, BIG arena", deep, sizeof(g_ws),
               TRUTH_NOT_RETRYABLE);

    /* 6-7: NEGATIVE CONTROLS. These already discriminate at rc403 and must
     * keep doing so — proof the instrument can return something other than
     * "OVERFLOW everywhere". */
    printf("NEGATIVE CONTROLS (statuses that DO discriminate today)\n");
    check_json("6 syntax error, BIG arena", "{\"a\":}", sizeof(g_ws),
               TRUTH_NOT_RETRYABLE);
    check_json("7 NaN literal, BIG arena", "[NaN]", sizeof(g_ws),
               TRUTH_NOT_RETRYABLE);

    (void)toobig;
}

static void run_toml(void)
{
    char doc[128];
    char deep[256];
    char inner[192];

    printf("\nTOML srmech_toml_parse\n");

    check_toml("1 valid doc, TINY arena", "a = 1\n", TINY_WS_BYTES,
               TRUTH_RETRYABLE);
    check_toml("2 valid doc, BIG arena", "a = 1\n", sizeof(g_ws),
               TRUTH_EXPECT_OK);

    /* 3: a 20-digit magnitude, past int64 but well within the digit scanner. */
    (void)snprintf(doc, sizeof(doc), "a = 99999999999999999999\n");
    check_toml("3 int > int64, BIG arena", doc, sizeof(g_ws),
               TRUTH_NOT_RETRYABLE);

    /* 4: array nested past SRMECH_TOML_MAX_DEPTH. */
    build_deep_array(inner, 80u);
    (void)snprintf(deep, sizeof(deep), "a = %s\n", inner);
    check_toml("4 depth-80, BIG arena", deep, sizeof(g_ws),
               TRUTH_NOT_RETRYABLE);

    printf("NEGATIVE CONTROL\n");
    check_toml("5 syntax error, BIG arena", "a = = 1\n", sizeof(g_ws),
               TRUTH_NOT_RETRYABLE);
}

int main(void)
{
    printf("== rc404 (`#T1069`) status discrimination: "
           "OVERFLOW means RETRYABLE, LIMIT means it does not ==\n\n");
    run_json();
    run_toml();
    printf("\nrows=%d passed=%d failures=%d\n",
           g_passed + g_failed, g_passed, g_failed);
    if (g_failed != 0) {
        printf("FAILED: a caller cannot tell 'grow the arena' from "
               "'retrying is futile'.\n");
        return 1;
    }
    printf("OK\n");
    return 0;
}
