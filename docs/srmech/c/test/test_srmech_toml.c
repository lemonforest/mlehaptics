/*
 * test_srmech_toml.c — C-side smoke tests for the malloc-free TOML
 * parser (srmech_toml_parse / srmech_toml_table_get).
 *
 * Exercises every supported construct (scalars with underscores +
 * exponents, both string flavours + multiline, arrays incl. nested /
 * multiline / trailing comma, inline tables, dotted keys, nested
 * tables, table reopening, arrays-of-tables + descent into the last
 * element, the backslash-uXXXX -> UTF-8 escape) plus the error /
 * boundary paths (NULL args, missing value, no '=', newline-in-basic-
 * string, arena overflow, empty doc, lookup edge cases). Mirrors the
 * discipline of test_srmech_sha256.c — assert + count, no test
 * framework. Exits 0 on all-pass, non-zero on any failure.
 */

#include "srmech.h"
#include <stdio.h>
#include <string.h>

static int fails = 0;
#define CHECK(cond, msg) do { if (!(cond)) { printf("FAIL: %s\n", msg); fails++; } } while (0)

static const srmech_toml_value_t *get(const srmech_toml_value_t *t, const char *k)
{
    return srmech_toml_table_get(t, k);
}

static unsigned char ws[1 << 20];

static void test_unicode_escape(void)
{
    /* Build "uni = \"AA\"\n" as explicit bytes so the HOST compiler
     * never sees a universal-character-name. The parser must turn the
     * 6-char sequence backslash-u-0-0-4-1 into 'A'. */
    char buf[64];
    size_t n = 0;
    const char *pre = "uni = \"A";
    memcpy(buf, pre, strlen(pre));
    n = strlen(pre);
    buf[n++] = (char)0x5c;   /* backslash */
    buf[n++] = 'u';
    buf[n++] = '0'; buf[n++] = '0'; buf[n++] = '4'; buf[n++] = '1';
    buf[n++] = '"';
    buf[n++] = '\n';
    srmech_toml_value_t *root = NULL;
    srmech_status_t st = srmech_toml_parse(buf, n, ws, sizeof(ws), &root);
    CHECK(st == SRMECH_OK, "uni parse ok");
    const srmech_toml_value_t *v = get(root, "uni");
    CHECK(v && v->type == SRMECH_TOML_STRING && strcmp(v->u.str.ptr, "AA") == 0,
          "unicode backslash-u0041 -> A");
}

int main(void)
{
    srmech_toml_value_t *root = NULL;
    srmech_status_t st;

    const char *src =
        "# comment line\n"
        "title = \"srmech\"\n"
        "count = 1_000\n"
        "neg = -42\n"
        "ratio = 3.14_15\n"
        "expo = 6.022e23\n"
        "flag = true\n"
        "off = false\n"
        "lit = 'C:\\\\no\\\\escapes'\n"
        "esc = \"tab\\tnl\\n\"\n"
        "ml = \"\"\"\nline1\nline2\"\"\"\n"
        "mll = '''\nraw\\nkept'''\n"
        "arr = [1, 2, 3,]\n"
        "nested_arr = [[1,2],[3,4]]\n"
        "multiline_arr = [\n  10,\n  20,\n  30,\n]\n"
        "inline = { a = 1, b = \"x\" }\n"
        "dotted.deep.key = 99\n"
        "\n"
        "[server]\n"
        "host = \"localhost\"\n"
        "port = 8080\n"
        "\n"
        "[server.tls]\n"
        "enabled = true\n"
        "\n"
        "[server]\n"
        "extra = \"reopened\"\n"
        "\n"
        "[[products]]\n"
        "name = \"hammer\"\n"
        "sku = 738\n"
        "\n"
        "[[products]]\n"
        "name = \"nail\"\n"
        "sku = 284\n"
        "[products.meta]\n"
        "tag = \"metal\"\n";

    st = srmech_toml_parse(src, strlen(src), ws, sizeof(ws), &root);
    CHECK(st == SRMECH_OK, "parse returns OK");
    CHECK(root && root->type == SRMECH_TOML_TABLE, "root is table");

    const srmech_toml_value_t *v;
    v = get(root, "title");
    CHECK(v && v->type == SRMECH_TOML_STRING && strcmp(v->u.str.ptr, "srmech") == 0, "title");
    v = get(root, "count");
    CHECK(v && v->type == SRMECH_TOML_INT && v->u.i == 1000, "count underscore");
    v = get(root, "neg");
    CHECK(v && v->type == SRMECH_TOML_INT && v->u.i == -42, "neg");
    v = get(root, "ratio");
    CHECK(v && v->type == SRMECH_TOML_FLOAT && v->u.f > 3.1414 && v->u.f < 3.1416, "ratio float underscore");
    v = get(root, "expo");
    CHECK(v && v->type == SRMECH_TOML_FLOAT && v->u.f > 6.0e23 && v->u.f < 6.1e23, "expo");
    v = get(root, "flag");
    CHECK(v && v->type == SRMECH_TOML_BOOL && v->u.b == 1, "flag true");
    v = get(root, "off");
    CHECK(v && v->type == SRMECH_TOML_BOOL && v->u.b == 0, "off false");
    v = get(root, "lit");
    CHECK(v && v->type == SRMECH_TOML_STRING && strcmp(v->u.str.ptr, "C:\\\\no\\\\escapes") == 0, "literal no-escape");
    v = get(root, "esc");
    CHECK(v && v->type == SRMECH_TOML_STRING && strcmp(v->u.str.ptr, "tab\tnl\n") == 0, "basic escapes");
    v = get(root, "ml");
    CHECK(v && v->type == SRMECH_TOML_STRING && strcmp(v->u.str.ptr, "line1\nline2") == 0, "multiline trim");
    v = get(root, "mll");
    CHECK(v && v->type == SRMECH_TOML_STRING && strcmp(v->u.str.ptr, "raw\\nkept") == 0, "multiline literal");
    v = get(root, "arr");
    CHECK(v && v->type == SRMECH_TOML_ARRAY && v->u.arr.n == 3 && v->u.arr.items[2]->u.i == 3, "arr trailing comma");
    v = get(root, "nested_arr");
    CHECK(v && v->u.arr.n == 2 && v->u.arr.items[1]->u.arr.items[1]->u.i == 4, "nested array");
    v = get(root, "multiline_arr");
    CHECK(v && v->u.arr.n == 3 && v->u.arr.items[1]->u.i == 20, "multiline array");
    v = get(root, "inline");
    CHECK(v && v->type == SRMECH_TOML_TABLE && get(v, "a")->u.i == 1 &&
          strcmp(get(v, "b")->u.str.ptr, "x") == 0, "inline table");
    {
        const srmech_toml_value_t *d = get(root, "dotted");
        const srmech_toml_value_t *deep = d ? get(d, "deep") : NULL;
        const srmech_toml_value_t *key = deep ? get(deep, "key") : NULL;
        CHECK(key && key->u.i == 99, "dotted.deep.key");
    }
    {
        const srmech_toml_value_t *s = get(root, "server");
        CHECK(s && get(s, "host") && strcmp(get(s, "host")->u.str.ptr, "localhost") == 0, "server.host");
        CHECK(get(s, "port") && get(s, "port")->u.i == 8080, "server.port");
        CHECK(get(s, "extra") && strcmp(get(s, "extra")->u.str.ptr, "reopened") == 0, "server reopened");
        const srmech_toml_value_t *tls = get(s, "tls");
        CHECK(tls && get(tls, "enabled") && get(tls, "enabled")->u.b == 1, "server.tls.enabled");
    }
    {
        const srmech_toml_value_t *prods = get(root, "products");
        CHECK(prods && prods->type == SRMECH_TOML_ARRAY && prods->u.arr.n == 2, "products len 2");
        const srmech_toml_value_t *p0 = prods->u.arr.items[0];
        const srmech_toml_value_t *p1 = prods->u.arr.items[1];
        CHECK(strcmp(get(p0, "name")->u.str.ptr, "hammer") == 0 && get(p0, "sku")->u.i == 738, "products[0]");
        CHECK(strcmp(get(p1, "name")->u.str.ptr, "nail") == 0 && get(p1, "sku")->u.i == 284, "products[1]");
        const srmech_toml_value_t *meta = get(p1, "meta");
        CHECK(meta && strcmp(get(meta, "tag")->u.str.ptr, "metal") == 0, "products[1].meta.tag");
    }

    test_unicode_escape();

    /* Error / boundary cases. */
    st = srmech_toml_parse(NULL, 5, ws, sizeof(ws), &root);
    CHECK(st == SRMECH_ERR_NULL_ARG, "null src len>0");
    st = srmech_toml_parse("x=1", 3, NULL, 0, &root);
    CHECK(st == SRMECH_ERR_NULL_ARG, "null ws");
    st = srmech_toml_parse("key = ", 6, ws, sizeof(ws), &root);
    CHECK(st == SRMECH_ERR_BAD_INPUT, "missing value");
    st = srmech_toml_parse("key \"x\"", 7, ws, sizeof(ws), &root);
    CHECK(st == SRMECH_ERR_BAD_INPUT, "no eq sign");
    st = srmech_toml_parse("s = \"open\nx\"", 12, ws, sizeof(ws), &root);
    CHECK(st == SRMECH_ERR_BAD_INPUT, "newline in basic string");
    {
        unsigned char small[16];
        st = srmech_toml_parse("a = \"verylongvalue\"", 19, small, sizeof(small), &root);
        CHECK(st == SRMECH_ERR_OVERFLOW, "tiny arena overflow");
    }
    st = srmech_toml_parse("", 0, ws, sizeof(ws), &root);
    CHECK(st == SRMECH_OK && root->type == SRMECH_TOML_TABLE && root->u.tbl.n == 0, "empty doc");
    CHECK(srmech_toml_table_get(NULL, "x") == NULL, "get null table");
    CHECK(srmech_toml_table_get(root, NULL) == NULL, "get null key");

    if (fails == 0) {
        printf("ALL PASS\n");
    } else {
        printf("%d FAILURES\n", fails);
    }
    return fails ? 1 : 0;
}
