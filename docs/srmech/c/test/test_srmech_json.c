/*
 * test_srmech_json.c — standalone C smoke tests for srmech_json.
 *
 * No Python, no test framework — assert + count, like
 * test_srmech_sha256.c. Exits 0 on all-pass, non-zero on first fail.
 *
 * Covers: parse+write round-trip of a nested object; key-sort (insert
 * out of order, assert sorted output); escaping (" \ newline tab a
 * control char a UTF-8 multibyte char emitted verbatim); int64 (incl.
 * negative + a large value); empty object/array; srmech_json_object_get;
 * the builder ({"b":2,"a":[1,2,3]} -> {"a": [1, 2, 3], "b": 2}).
 */

#include "srmech.h"

#include <stdint.h>
#include <stdio.h>
#include <string.h>

static int g_passed = 0;
static int g_failed = 0;

/* 8 MiB workspace arena — matches the parity harness. */
static unsigned char g_ws[8u * 1024u * 1024u];

static void check_str(const char *got, const char *want, const char *desc)
{
    if (got != NULL && strcmp(got, want) == 0) {
        g_passed++;
        printf("  PASS  %s\n", desc);
    } else {
        g_failed++;
        printf("  FAIL  %s\n    got:  %s\n    want: %s\n",
               desc, got ? got : "(null)", want);
    }
}

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

/* Parse `src`, write canonically, compare against `want`. */
static void roundtrip(const char *src, const char *want, const char *desc)
{
    srmech_json_value_t *root = NULL;
    srmech_status_t st = srmech_json_parse(src, strlen(src),
                                           g_ws, sizeof(g_ws), &root);
    if (st != SRMECH_OK) {
        g_failed++;
        printf("  FAIL  %s — parse status %d\n", desc, (int)st);
        return;
    }
    size_t need = 0;
    st = srmech_json_write(root, NULL, 0, &need);   /* size query */
    if (st != SRMECH_OK) {
        g_failed++;
        printf("  FAIL  %s — size-query status %d\n", desc, (int)st);
        return;
    }
    static char out[65536];
    if (need + 1u > sizeof(out)) {
        g_failed++;
        printf("  FAIL  %s — output too large (%zu)\n", desc, need);
        return;
    }
    size_t wrote = 0;
    st = srmech_json_write(root, out, sizeof(out), &wrote);
    if (st != SRMECH_OK || wrote != need) {
        g_failed++;
        printf("  FAIL  %s — write status %d (wrote %zu, need %zu)\n",
               desc, (int)st, wrote, need);
        return;
    }
    out[wrote] = '\0';
    check_str(out, want, desc);
}

int main(void)
{
    printf("== srmech_json smoke tests ==\n");

    /* Nested object round-trip + key-sort (input keys out of order). */
    roundtrip(
        "{\"z\": 1, \"a\": {\"y\": 2, \"x\": 3}, \"m\": [10, 20]}",
        "{\"a\": {\"x\": 3, \"y\": 2}, \"m\": [10, 20], \"z\": 1}",
        "nested object, keys sorted, separators canonical");

    /* Key-sort: byte order (uppercase < lowercase; shorter prefix first). */
    roundtrip(
        "{\"bb\": 1, \"b\": 2, \"B\": 3, \"a\": 4}",
        "{\"B\": 3, \"a\": 4, \"b\": 2, \"bb\": 1}",
        "key sort is bytewise UTF-8 / code-point order");

    /* Escaping: quote, backslash, newline, tab, a control char (0x01),
     * a UTF-8 multibyte char (e-acute = 0xC3 0xA9) emitted VERBATIM. */
    roundtrip(
        "{\"k\": \"q\\\"b\\\\n\\nt\\t\\u0001\\u00e9\"}",
        "{\"k\": \"q\\\"b\\\\n\\nt\\t\\u0001\xC3\xA9\"}",
        "string escaping + non-ASCII verbatim (ensure_ascii=False)");

    /* Forward-slash is NOT escaped. */
    roundtrip("{\"u\": \"a/b\"}", "{\"u\": \"a/b\"}",
              "forward slash emitted verbatim (not \\/)");

    /* int64: zero, negative, large positive (2**53), large negative. */
    roundtrip("[0, -7, 9007199254740992, -9223372036854775807]",
              "[0, -7, 9007199254740992, -9223372036854775807]",
              "int64 incl. negative + large values, array separators");

    /* bool + null. */
    roundtrip("{\"t\": true, \"f\": false, \"n\": null}",
              "{\"f\": false, \"n\": null, \"t\": true}",
              "bool + null");

    /* Empty object + empty array. */
    roundtrip("{}", "{}", "empty object");
    roundtrip("[]", "[]", "empty array");
    roundtrip("{\"o\": {}, \"a\": []}", "{\"a\": [], \"o\": {}}",
              "nested empty object + array");

    /* Surrogate pair: U+1F600 (grinning face) = 😀 ->
     * F0 9F 98 80 verbatim. */
    roundtrip("[\"\\ud83d\\ude00\"]", "[\"\xF0\x9F\x98\x80\"]",
              "UTF-16 surrogate pair decodes to 4-byte UTF-8");

    /* srmech_json_object_get. */
    {
        srmech_json_value_t *root = NULL;
        srmech_status_t st = srmech_json_parse(
            "{\"alpha\": 11, \"beta\": \"hi\"}", 27,
            g_ws, sizeof(g_ws), &root);
        check_true(st == SRMECH_OK, "object_get fixture parses");
        const srmech_json_value_t *a = srmech_json_object_get(root, "alpha");
        check_true(a != NULL && a->type == SRMECH_JSON_INT && a->u.i == 11,
                   "object_get('alpha') == int 11");
        const srmech_json_value_t *b = srmech_json_object_get(root, "beta");
        check_true(b != NULL && b->type == SRMECH_JSON_STRING &&
                   b->u.str.len == 2u && memcmp(b->u.str.ptr, "hi", 2) == 0,
                   "object_get('beta') == string 'hi'");
        check_true(srmech_json_object_get(root, "missing") == NULL,
                   "object_get('missing') == NULL");
    }

    /* Builder: construct {"b":2,"a":[1,2,3]} and assert canonical write. */
    {
        srmech_json_builder_t bld;
        srmech_status_t st = srmech_json_builder_init(&bld, g_ws, sizeof(g_ws));
        check_true(st == SRMECH_OK, "builder_init");

        srmech_json_value_t *items[3];
        items[0] = srmech_json_new_int(&bld, 1);
        items[1] = srmech_json_new_int(&bld, 2);
        items[2] = srmech_json_new_int(&bld, 3);
        srmech_json_value_t *arr = srmech_json_new_array(&bld, items, 3);

        const char *keys[2] = { "b", "a" };
        srmech_json_value_t *vals[2];
        vals[0] = srmech_json_new_int(&bld, 2);
        vals[1] = arr;
        srmech_json_value_t *obj = srmech_json_new_object(&bld, keys, vals, 2);
        check_true(bld.failed == 0, "builder did not overflow");

        size_t need = 0;
        st = srmech_json_write(obj, NULL, 0, &need);
        check_true(st == SRMECH_OK, "builder tree size-query");
        static char out[256];
        size_t wrote = 0;
        st = srmech_json_write(obj, out, sizeof(out), &wrote);
        out[wrote] = '\0';
        check_str(out, "{\"a\": [1, 2, 3], \"b\": 2}",
                  "builder writes {\"a\": [1, 2, 3], \"b\": 2}");
    }

    /* Error: too-small buffer returns SRMECH_ERR_OVERFLOW. */
    {
        srmech_json_value_t *root = NULL;
        srmech_json_parse("[1, 2, 3]", 9, g_ws, sizeof(g_ws), &root);
        char tiny[4];
        size_t wrote = 0;
        srmech_status_t st = srmech_json_write(root, tiny, sizeof(tiny), &wrote);
        check_true(st == SRMECH_ERR_OVERFLOW,
                   "too-small buffer returns SRMECH_ERR_OVERFLOW");
    }

    /* Error: trailing garbage rejected. */
    {
        srmech_json_value_t *root = NULL;
        srmech_status_t st = srmech_json_parse("{} x", 4,
                                               g_ws, sizeof(g_ws), &root);
        check_true(st != SRMECH_OK, "trailing garbage rejected");
    }

    printf("== %d passed, %d failed ==\n", g_passed, g_failed);
    return (g_failed == 0) ? 0 : 1;
}
