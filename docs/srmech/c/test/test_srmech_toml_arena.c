/*
 * test_srmech_toml_arena.c — C-side tests for srmech_toml_parse_arena_bytes
 * (0.9.0rc391, #T907 slice 1). The sizer removes the guess-and-grow hazard
 * from a ctypes / C-only caller: ask it for the arena size, allocate exactly
 * that, parse. This test proves (a) the returned bound is monotonic + has a
 * nonzero floor, and (b) an arena of exactly that size parses a real document
 * to completion — a round-trip through the sizer. Mirrors the assert+count
 * discipline of test_srmech_toml.c: no framework, exit 0 on all-pass.
 */

#include "srmech.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int fails = 0;
#define CHECK(cond, msg) do { if (!(cond)) { printf("FAIL: %s\n", msg); fails++; } } while (0)

static const srmech_toml_value_t *get(const srmech_toml_value_t *t, const char *k)
{
    return srmech_toml_table_get(t, k);
}

/* The sizer must have a nonzero floor and grow with the source length. */
static void test_bound_shape(void)
{
    size_t z = srmech_toml_parse_arena_bytes(0);
    size_t small = srmech_toml_parse_arena_bytes(64);
    size_t big = srmech_toml_parse_arena_bytes(65536);
    CHECK(z >= 4096u, "empty-doc bound has a real floor");
    CHECK(small > z, "bound grows with source length");
    CHECK(big > small, "bound keeps growing with source length");
}

/* Round-trip: size a real document, allocate EXACTLY the sizer's bound, and
 * confirm srmech_toml_parse fits and yields the expected tree. This is the
 * whole point of the sizer — no guess, no OVERFLOW retry. */
static void test_exact_arena_round_trip(void)
{
    const char *src =
        "title = \"srmech\"\n"
        "count = 1_000\n"
        "flag = true\n"
        "arr = [1, 2, 3]\n"
        "inline = { a = 1, b = \"x\" }\n"
        "[server]\n"
        "host = \"localhost\"\n"
        "port = 8080\n"
        "[[products]]\n"
        "name = \"hammer\"\n"
        "[[products]]\n"
        "name = \"nail\"\n";
    size_t len = strlen(src);
    size_t need = srmech_toml_parse_arena_bytes(len);
    unsigned char *ws = (unsigned char *)malloc(need);
    CHECK(ws != NULL, "test harness allocated the sized arena");
    if (ws == NULL) { return; }

    srmech_toml_value_t *root = NULL;
    srmech_status_t st = srmech_toml_parse(src, len, ws, need, &root);
    CHECK(st == SRMECH_OK, "exact sized arena parses OK (no OVERFLOW)");
    CHECK(root != NULL && root->type == SRMECH_TOML_TABLE, "root is a table");

    const srmech_toml_value_t *v = get(root, "title");
    CHECK(v && v->type == SRMECH_TOML_STRING && strcmp(v->u.str.ptr, "srmech") == 0,
          "title survives the sized parse");
    v = get(root, "count");
    CHECK(v && v->type == SRMECH_TOML_INT && v->u.i == 1000, "count underscore int");
    v = get(root, "arr");
    CHECK(v && v->type == SRMECH_TOML_ARRAY && v->u.arr.n == 3 &&
          v->u.arr.items[2]->u.i == 3, "array survives the sized parse");
    {
        const srmech_toml_value_t *s = get(root, "server");
        CHECK(s && get(s, "port") && get(s, "port")->u.i == 8080, "server.port");
    }
    {
        const srmech_toml_value_t *prods = get(root, "products");
        CHECK(prods && prods->type == SRMECH_TOML_ARRAY && prods->u.arr.n == 2,
              "array-of-tables survives the sized parse");
    }
    free(ws);
}

/* A densest-possible many-tiny-keys corpus is the worst case for the linear
 * factor; the sized arena must still fit it (headroom proof). */
static void test_dense_keys_fit(void)
{
    static char doc[8192];
    size_t n = 0;
    for (int i = 0; i < 500; i++) {
        int w = snprintf(doc + n, sizeof(doc) - n, "k%d=%d\n", i, i);
        if (w <= 0) { break; }
        n += (size_t)w;
    }
    size_t need = srmech_toml_parse_arena_bytes(n);
    unsigned char *ws = (unsigned char *)malloc(need);
    CHECK(ws != NULL, "dense-keys arena allocated");
    if (ws == NULL) { return; }
    srmech_toml_value_t *root = NULL;
    srmech_status_t st = srmech_toml_parse(doc, n, ws, need, &root);
    CHECK(st == SRMECH_OK, "dense many-tiny-keys doc fits the sized arena");
    const srmech_toml_value_t *v = root ? get(root, "k499") : NULL;
    CHECK(v && v->type == SRMECH_TOML_INT && v->u.i == 499, "k499 present");
    free(ws);
}

int main(void)
{
    test_bound_shape();
    test_exact_arena_round_trip();
    test_dense_keys_fit();

    if (fails == 0) {
        printf("ALL PASS\n");
    } else {
        printf("%d FAILURES\n", fails);
    }
    return fails ? 1 : 0;
}
