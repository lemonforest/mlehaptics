/*
 * test_srmech_json_number_rc402.c — the rc402 (`#T1068`) correctness gate for
 * srmech_json's number scanner + integer range, and for the NUL-in-object-key
 * contract.
 *
 * WHY THIS FILE EXISTS. Before rc402 srmech_json_parse returned SRMECH_OK with
 * a WRONG VALUE for three classes of input. No status code reported any of them,
 * so every downstream consumer was silently corrupted:
 *
 *   1. An integer outside int64 CLAMPED. `99999999999999999999` parsed as
 *      SRMECH_OK / INT 9223372036854775807. The integer path called
 *      `strtoll(tmp, NULL, 10)` and never inspected errno, so the C-standard
 *      ERANGE + LLONG_MAX return was discarded. This was KNOWN at rc176 — see
 *      the comment in srmech_carrier_marshal.c that reads "the rc176 bignum
 *      transport, since srmech_json's strtoll clamps a >int64 literal" — and a
 *      decimal-string transport was built BESIDE the defect instead of fixing
 *      it, so the clamp shipped for ~225 further rcs.
 *   2. A malformed number yielded a VALUE. The scanner's character class was
 *      `[0-9.eE+-]`, so `--1` and a bare `-` both parsed as SRMECH_OK / INT 0,
 *      `01` as INT 1, `1.2.3` as DOUBLE 1.2, and `1e` / `1e+` / `1.` as
 *      DOUBLE 1 — where CPython's json raises JSONDecodeError for every one.
 *   3. An object KEY containing a NUL escape TRUNCATED. Keys are stored as
 *      NUL-terminated arena copies and re-measured with strlen, so the legal
 *      JSON key "a"+backslash-u-0000+"b" (three decoded bytes) came back as
 *      "a" with status SRMECH_OK.
 *
 * THE CONTRACT THIS FILE PINS. Every one of those inputs must now return an
 * ERROR STATUS, never SRMECH_OK-with-a-value. An honest decline the caller can
 * SEE beats a plausible wrong number. Out-of-int64 is SRMECH_ERR_OVERFLOW (the
 * value is well-formed JSON, it simply does not fit int64_t, and JSON
 * legitimately permits such integers — they ride the rc176 decimal-string
 * transport); malformed grammar and a NUL-bearing key are SRMECH_ERR_BAD_INPUT.
 *
 * AND WHAT MUST STILL WORK. The valid edges are pinned just as hard, because a
 * scanner tightened too far is its own silent defect: INT64_MAX / INT64_MIN / 0
 * / -0 still parse exactly, and the DOUBLE path is left ALONE on purpose.
 * strtod is correctly rounded and already agrees with CPython at both ends —
 * 1e400 -> inf, 1e-400 -> 0.0, 5e-324 -> the smallest subnormal — so an errno
 * check on the double path would REGRESS parity by declining input CPython
 * accepts. That non-defect is asserted here rather than assumed.
 *
 * No Python, no test framework — assert + count, like test_srmech_json.c.
 * Exits 0 on all-pass, non-zero on any fail.
 */

#include "srmech.h"

#include <stdint.h>
#include <stdio.h>
#include <string.h>

static int g_passed = 0;
static int g_failed = 0;

/* Reinterpret an IEEE-754 bit pattern as a double, without type-punning UB and
 * without <math.h> (srmech is libm-free). Used to name +/-inf portably — MSVC
 * errors on a literal `1.0 / 0.0` (C2124) that gcc/clang fold to inf. */
static double f64_from_bits(uint64_t bits)
{
    double out;
    memcpy(&out, &bits, sizeof(out));
    return out;
}

/* 1 MiB workspace arena — every document here is tiny. */
static unsigned char g_ws[1024u * 1024u];

static void check_true(int cond, const char *desc)
{
    if (cond) {
        g_passed++;
        printf("  PASS  %s\n", desc);
    } else {
        g_failed++;
        printf("  FAIL  %s\n", desc);
    }
}

/* Parse `doc` and assert it returns exactly `want` (a non-OK status). */
static void check_status(const char *doc, srmech_status_t want,
                         const char *desc)
{
    srmech_json_value_t *root = NULL;
    srmech_status_t st = srmech_json_parse(doc, strlen(doc), g_ws,
                                           sizeof(g_ws), &root);
    if (st == want) {
        g_passed++;
        printf("  PASS  %s\n", desc);
    } else {
        g_failed++;
        printf("  FAIL  %s\n    got status %d, want %d\n",
               desc, (int)st, (int)want);
    }
}

/* Parse `doc` and assert it is SRMECH_OK with INT value `want`. */
static void check_int(const char *doc, int64_t want, const char *desc)
{
    srmech_json_value_t *root = NULL;
    srmech_status_t st = srmech_json_parse(doc, strlen(doc), g_ws,
                                           sizeof(g_ws), &root);
    if (st == SRMECH_OK && root != NULL &&
        root->type == SRMECH_JSON_INT && root->u.i == want) {
        g_passed++;
        printf("  PASS  %s\n", desc);
    } else {
        g_failed++;
        printf("  FAIL  %s\n    status %d, type %d, value %lld (want %lld)\n",
               desc, (int)st, root ? (int)root->type : -1,
               root ? (long long)root->u.i : 0LL, (long long)want);
    }
}

/* Parse `doc` and assert it is SRMECH_OK with DOUBLE bit-equal to `want`.
 * Compared by memcmp on the bytes so inf / -inf / subnormals are exact and no
 * floating-point equality rule is relied on. */
static void check_double_bits(const char *doc, double want, const char *desc)
{
    srmech_json_value_t *root = NULL;
    srmech_status_t st = srmech_json_parse(doc, strlen(doc), g_ws,
                                           sizeof(g_ws), &root);
    if (st == SRMECH_OK && root != NULL &&
        root->type == SRMECH_JSON_DOUBLE &&
        memcmp(&root->u.f, &want, sizeof(double)) == 0) {
        g_passed++;
        printf("  PASS  %s\n", desc);
    } else {
        g_failed++;
        printf("  FAIL  %s\n    status %d, type %d, value %.17g (want %.17g)\n",
               desc, (int)st, root ? (int)root->type : -1,
               root ? root->u.f : 0.0, want);
    }
}

/* ---- 1. THE DEFECT: an out-of-int64 integer must DECLINE, not clamp. ---- */
static void test_int_overflow_declines(void)
{
    printf("-- integer overflow declines (was: SRMECH_OK with a clamped value) --\n");
    /* Pre-rc402 these two returned SRMECH_OK / INT64_MAX and INT64_MIN. */
    check_status("99999999999999999999", SRMECH_ERR_OVERFLOW,
                 "20-digit positive declines with OVERFLOW");
    check_status("-99999999999999999999", SRMECH_ERR_OVERFLOW,
                 "20-digit negative declines with OVERFLOW");
    /* One past each int64 boundary — the tightest possible overflow case. */
    check_status("9223372036854775808", SRMECH_ERR_OVERFLOW,
                 "INT64_MAX+1 declines with OVERFLOW");
    check_status("-9223372036854775809", SRMECH_ERR_OVERFLOW,
                 "INT64_MIN-1 declines with OVERFLOW");
    /* Nested, so the decline propagates out of a container rather than being
     * swallowed by the element loop. */
    check_status("{\"n\": 99999999999999999999}", SRMECH_ERR_OVERFLOW,
                 "overflow inside an object propagates");
    check_status("[1, 2, 99999999999999999999]", SRMECH_ERR_OVERFLOW,
                 "overflow inside an array propagates");
}

/* ---- 2. Valid integer edges must STILL parse exactly. ---- */
static void test_int_edges_still_parse(void)
{
    printf("-- valid integer edges still parse --\n");
    check_int("9223372036854775807", INT64_MAX, "INT64_MAX parses exactly");
    check_int("-9223372036854775808", INT64_MIN, "INT64_MIN parses exactly");
    check_int("0", 0, "0 parses");
    check_int("-0", 0, "-0 parses as 0 (matches CPython)");
    check_int("1", 1, "1 parses");
    check_int("-1", -1, "-1 parses");
    check_int("10", 10, "10 parses (0 after a nonzero lead is not a leading zero)");
    check_int("100", 100, "100 parses");
}

/* ---- 3. Malformed numbers must DECLINE, not yield a value. ---- */
static void test_malformed_numbers_decline(void)
{
    printf("-- malformed numbers decline (was: SRMECH_OK with a value) --\n");
    /* Each of these parsed to a VALUE before rc402; the old result is named so
     * a regression is recognisable rather than merely red. */
    check_status("01", SRMECH_ERR_BAD_INPUT, "leading zero `01` (was INT 1)");
    check_status("00", SRMECH_ERR_BAD_INPUT, "leading zero `00` (was INT 0)");
    check_status("-01", SRMECH_ERR_BAD_INPUT, "leading zero `-01`");
    check_status("1.2.3", SRMECH_ERR_BAD_INPUT, "two dots (was DOUBLE 1.2)");
    check_status("1e", SRMECH_ERR_BAD_INPUT, "empty exponent (was DOUBLE 1)");
    check_status("1e+", SRMECH_ERR_BAD_INPUT, "sign-only exponent (was DOUBLE 1)");
    check_status("1E-", SRMECH_ERR_BAD_INPUT, "sign-only exponent, capital E");
    check_status("--1", SRMECH_ERR_BAD_INPUT, "double minus (was INT 0)");
    check_status("-", SRMECH_ERR_BAD_INPUT, "bare minus (was INT 0)");
    check_status("1.", SRMECH_ERR_BAD_INPUT, "trailing dot (was DOUBLE 1)");
    check_status("1.e5", SRMECH_ERR_BAD_INPUT, "empty fraction before exponent");
    check_status(".5", SRMECH_ERR_BAD_INPUT, "leading dot");
    check_status("+1", SRMECH_ERR_BAD_INPUT, "leading plus is not legal JSON");
    /* Nested, so a malformed element cannot be swallowed by the container. */
    check_status("[--1]", SRMECH_ERR_BAD_INPUT, "malformed inside an array");
    check_status("{\"k\": 1e}", SRMECH_ERR_BAD_INPUT, "malformed inside an object");
}

/* ---- 4. Valid doubles: strtod is ADJUDICATED CORRECT and left alone. ---- */
static void test_double_path_unchanged(void)
{
    printf("-- double path matches CPython at both ends (verified non-defect) --\n");
    /* CPython: json.loads('1e400') -> inf. strtod returns HUGE_VAL on overflow,
     * so the existing behaviour ALREADY agreed and an errno check here would
     * have declined input CPython accepts.
     *
     * Build the expected infinities from their IEEE-754 BIT PATTERNS, not from
     * `1.0 / 0.0`: MSVC rejects a compile-time divide-by-zero outright (C2124,
     * measured on the windows-latest pedantic cell) where gcc/clang quietly
     * fold it to inf. srmech is libm-free, so <math.h>'s INFINITY is also out.
     * The bit form is portable, needs no libm, and is what check_double_bits
     * compares against anyway. */
    const double pos_inf = f64_from_bits(0x7FF0000000000000u);
    const double neg_inf = f64_from_bits(0xFFF0000000000000u);
    check_double_bits("1e400", pos_inf, "1e400 -> inf (matches CPython)");
    check_double_bits("-1e400", neg_inf, "-1e400 -> -inf (matches CPython)");
    /* CPython: json.loads('1e-400') -> 0.0. strtod underflows to 0.0 likewise. */
    check_double_bits("1e-400", 0.0, "1e-400 -> 0.0 (matches CPython)");
    /* Smallest positive subnormal; must survive the scanner untouched. */
    check_double_bits("5e-324", 5e-324, "5e-324 -> smallest subnormal");
    check_double_bits("1.5", 1.5, "1.5 parses");
    check_double_bits("1e5", 1e5, "1e5 parses as DOUBLE");
    check_double_bits("-0.0", -0.0, "-0.0 keeps its sign bit");
    check_double_bits("0.5", 0.5, "0.5 parses (0 lead is legal before a frac)");
    check_double_bits("1E+2", 100.0, "capital E with explicit + parses");
    check_double_bits("-1.25e-2", -1.25e-2, "full sign/frac/exp form parses");
}

/* ---- 5. A NUL-bearing object KEY declines; a NUL string VALUE survives. ---- */
static void test_nul_in_key_declines(void)
{
    printf("-- NUL in an object key declines; in a string value it survives --\n");
    /* The escape is assembled at runtime so no literal backslash-u-0000 sits in
     * this source file. key_doc is {"a<NUL>b": 1}; val_doc is {"k": "a<NUL>b"}. */
    const char key_doc[] = "{\"a\\u0000b\": 1}";
    const char val_doc[] = "{\"k\": \"a\\u0000b\"}";

    /* Pre-rc402 this returned SRMECH_OK with the key silently cut to "a". */
    check_status(key_doc, SRMECH_ERR_BAD_INPUT,
                 "NUL escape in a KEY declines (was OK with key truncated to \"a\")");

    /* A string VALUE carries an explicit length, so it was always correct and
     * must stay correct: three bytes, 'a' NUL 'b'. */
    srmech_json_value_t *root = NULL;
    srmech_status_t st = srmech_json_parse(val_doc, strlen(val_doc), g_ws,
                                           sizeof(g_ws), &root);
    check_true(st == SRMECH_OK, "NUL escape in a string VALUE still parses");
    if (st == SRMECH_OK && root != NULL && root->type == SRMECH_JSON_OBJECT &&
        root->u.obj.n == 1u) {
        const srmech_json_value_t *sv = root->u.obj.vals[0];
        check_true(sv != NULL && sv->type == SRMECH_JSON_STRING &&
                   sv->u.str.len == 3u,
                   "NUL-bearing string VALUE keeps its full length of 3");
        check_true(sv != NULL && sv->u.str.len == 3u &&
                   sv->u.str.ptr[0] == 'a' && sv->u.str.ptr[1] == '\0' &&
                   sv->u.str.ptr[2] == 'b',
                   "NUL-bearing string VALUE keeps its exact bytes a-NUL-b");
    } else {
        check_true(0, "NUL-bearing string VALUE keeps its full length of 3");
        check_true(0, "NUL-bearing string VALUE keeps its exact bytes a-NUL-b");
    }
}

/* ---- 6. The >=63-byte staging bound still declines (pre-existing guard). ---- */
static void test_long_literal_declines(void)
{
    printf("-- an over-long numeric literal declines --\n");
    /* 70 digits: longer than the 64-byte tmp[] staging buffer. */
    const char *long_int =
        "1111111111111111111111111111111111111111111111111111111111111111111111";
    check_status(long_int, SRMECH_ERR_OVERFLOW,
                 "70-digit literal declines with OVERFLOW");
}

/* ---- 7. Deep nesting still parses (the scanner change must not disturb it). */
static void test_deep_nesting_still_parses(void)
{
    printf("-- deep nesting is unaffected by the scanner change --\n");
    /* 32 levels of array around a valid int — comfortably inside
     * SRMECH_JSON_MAX_DEPTH (64), so this must SUCCEED. */
    char buf[128];
    const int depth = 32;
    int i = 0;
    size_t pos = 0;
    for (i = 0; i < depth; i++) { buf[pos++] = '['; }
    buf[pos++] = '7';
    for (i = 0; i < depth; i++) { buf[pos++] = ']'; }
    buf[pos] = '\0';

    srmech_json_value_t *root = NULL;
    srmech_status_t st = srmech_json_parse(buf, pos, g_ws, sizeof(g_ws), &root);
    check_true(st == SRMECH_OK && root != NULL &&
               root->type == SRMECH_JSON_ARRAY,
               "32-deep nested array around an int still parses");
}

int main(void)
{
    printf("== test_srmech_json_number_rc402 ==\n");
    test_int_overflow_declines();
    test_int_edges_still_parse();
    test_malformed_numbers_decline();
    test_double_path_unchanged();
    test_nul_in_key_declines();
    test_long_literal_declines();
    test_deep_nesting_still_parses();
    printf("== %d passed, %d failed ==\n", g_passed, g_failed);
    return (g_failed == 0) ? 0 : 1;
}
