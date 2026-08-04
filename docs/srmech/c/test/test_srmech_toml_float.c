/*
 * test_srmech_toml_float.c — bare-C-HOST smoke for rc397 (#T1066): the
 * correctly-rounded, libm-free decimal->double parse in srmech_toml.
 *
 * For each token the parser's SRMECH_TOML_FLOAT value is compared BIT-FOR-BIT
 * (memcmp of the 8 IEEE-754 bytes) against the host compiler's own double
 * literal for the same text. Host C literal parsing is correctly rounded
 * (round-to-nearest-even), so this is a real correctness oracle for a C-ONLY
 * host with no Python present: it pins the Clinger fast path AND the
 * srmech_bigint exact tail (denormals, ties, long significands), plus the
 * overflow->inf and underflow->0 boundaries (built from bit patterns so the
 * source carries no out-of-range float literal — those are -Werror warnings).
 *
 * assert + count, no framework (mirrors test_srmech_toml.c). Exit 0 = pass.
 */

#include "srmech.h"
#include <stdio.h>
#include <string.h>
#include <stdint.h>

static int fails = 0;
#define CHECK(cond, msg) do { if (!(cond)) { printf("FAIL: %s\n", msg); fails++; } } while (0)

static unsigned char ws[1 << 16];

/* Parse "x = <tok>" and return the parsed double via *out; 1 on success. */
static int parse_one(const char *tok, double *out)
{
    char doc[128];
    srmech_toml_value_t *root = NULL;
    const srmech_toml_value_t *v;
    size_t n = 0;
    int w = snprintf(doc, sizeof(doc), "x = %s\n", tok);
    if (w <= 0 || (size_t)w >= sizeof(doc)) { return 0; }
    n = (size_t)w;
    if (srmech_toml_parse(doc, n, ws, sizeof(ws), &root) != SRMECH_OK) { return 0; }
    v = srmech_toml_table_get(root, "x");
    if (v == NULL || v->type != SRMECH_TOML_FLOAT) { return 0; }
    *out = v->u.f;
    return 1;
}

/* True iff the parse of `tok` is bit-identical to `expect`. */
static int bits_eq(const char *tok, double expect)
{
    double got = 0.0;
    if (!parse_one(tok, &got)) { return 0; }
    return memcmp(&got, &expect, sizeof(double)) == 0;
}

/* A double from an explicit IEEE-754 bit pattern (no libm / no literal). */
static double from_bits(uint64_t bits)
{
    double d;
    memcpy(&d, &bits, sizeof(d));
    return d;
}

int main(void)
{
    /* Correctly-rounded finite values — the parse must equal the host literal. */
    CHECK(bits_eq("0.1", 0.1), "0.1 bit-exact");
    CHECK(bits_eq("0.2", 0.2), "0.2 bit-exact");
    CHECK(bits_eq("0.3", 0.3), "0.3 bit-exact");
    CHECK(bits_eq("3.141592653589793", 3.141592653589793), "pi bit-exact");
    CHECK(bits_eq("1e-12", 1e-12), "1e-12 bit-exact");
    CHECK(bits_eq("6.022e23", 6.022e23), "6.022e23 bit-exact");
    CHECK(bits_eq("1e-300", 1e-300), "1e-300 bit-exact (exponent-compounding)");
    CHECK(bits_eq("9.999999999999999e22", 9.999999999999999e22), "9.999...e22");
    CHECK(bits_eq("1234567890123456789.0", 1234567890123456789.0), "19-digit int.0");
    CHECK(bits_eq("0.00000000000000000001", 1e-20), "1e-20 written out");
    CHECK(bits_eq("9007199254740993.0", 9007199254740993.0), "2^53+1 rounds down");

    /* IEEE boundary values. */
    CHECK(bits_eq("2.2250738585072014e-308", 2.2250738585072014e-308), "min normal");
    CHECK(bits_eq("2.2250738585072009e-308", 2.2250738585072009e-308), "max subnormal");
    CHECK(bits_eq("5e-324", 5e-324), "min denormal 5e-324");
    CHECK(bits_eq("4.9406564584124654e-324", 4.9406564584124654e-324), "min denormal full");
    CHECK(bits_eq("1.7976931348623157e308", 1.7976931348623157e308), "DBL_MAX");

    /* Signed zero — the sign bit must survive (== would not catch its loss). */
    {
        double z = 0.0;
        CHECK(bits_eq("-0.0", from_bits((uint64_t)1u << 63)), "-0.0 keeps sign bit");
        CHECK(bits_eq("0.0", z), "0.0 is +zero");
    }

    /* Overflow -> +/-inf, underflow -> +/-0 (inf built from its bit pattern). */
    CHECK(bits_eq("1e400", from_bits((uint64_t)0x7FF0000000000000ULL)), "1e400 -> +inf");
    CHECK(bits_eq("-1e400", from_bits((uint64_t)0xFFF0000000000000ULL)), "-1e400 -> -inf");
    CHECK(bits_eq("1e-500", 0.0), "1e-500 -> +0");

    if (fails == 0) {
        printf("ALL PASS\n");
    } else {
        printf("%d FAILURES\n", fails);
    }
    return fails ? 1 : 0;
}
