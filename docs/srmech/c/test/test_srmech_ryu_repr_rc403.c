/*
 * test_srmech_ryu_repr_rc403.c — bare-C-HOST gate for the Ryu-class
 * shortest-round-trip double -> decimal writer (`#T1071`).
 *
 * WHY THIS TEST LOOKS THE WAY IT DOES
 * -----------------------------------
 * A previously-proposed gate for this same work WENT GREEN while the defect was
 * live: it swept an attested corpus plus a hostile battery and reported zero
 * byte-diffs, because the defect lives almost entirely in the ZERO-MANTISSA
 * class (powers of two) and in exact dyadic fractions — which uniform random
 * sampling essentially never hits. MEASURED during this build: 3,000,000
 * uniformly random bit patterns found 0 divergences against the OLD, broken
 * implementation, while 4196 signed powers of two found 92. An instrument that
 * cannot return otherwise is not a measurement, so this test is built around
 * the structured classes, not around volume.
 *
 * Because a bare-C host has no CPython to ask, the gate has TWO independent
 * halves, and neither one alone would be sufficient:
 *
 *   (A) SHORTEST-ROUND-TRIP, proved rather than compared. For each value we
 *       emit the decimal, parse it back with srmech's OWN libm-free correctly-
 *       rounded decimal->double (rc397, reached through srmech_toml_parse) and
 *       require the bits to be identical; then we build BOTH one-digit-shorter
 *       neighbours (truncate, and truncate-then-increment-with-carry) and
 *       require that NEITHER round-trips. That is the definition of "shortest
 *       decimal that round-trips", checked directly, with no oracle table.
 *       It is exactly the property the old printf search failed: it returned a
 *       round-tripping decimal that was one digit too long.
 *
 *   (B) SPELLING, pinned against CPython repr(float) strings. Half (A) cannot
 *       see a formatting bug at all — '1e+16' and '10000000000000000.0' both
 *       round-trip and both are shortest. The RYU_VECTORS table below carries
 *       literal repr() output for the switch points (decpt <= -4 / decpt > 16),
 *       the mandatory trailing '.0', the minimum-two-digit exponent ('5e-08',
 *       never '5e-8'), -0.0, subnormals, and the tie class that broke the old
 *       code (2**-24 == 5.960464477539063e-08, where printf emitted the
 *       17-digit 5.9604644775390625e-08).
 *
 * Half (B) is also the platform-independence gate: the whole point of dropping
 * snprintf is that C fixes only a MINIMUM exponent width, so '%.17g' of 1e17 is
 * '1e+017' on Windows and '1e+17' on Linux. These literals are byte-exact, this
 * file is in the ctest foreach, and CI runs ctest on Linux gcc / macOS clang /
 * Windows MSVC — so a per-host spelling difference fails a job.
 *
 * assert + count, no framework (mirrors test_srmech_toml_float.c). Exit 0 = pass.
 */

#include "srmech.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

static int fails = 0;
static long checked = 0;

#define CHECK(cond, msg) do { if (!(cond)) { printf("FAIL: %s\n", msg); fails++; } } while (0)

static unsigned char ws[1 << 16];

/* ------------------------------------------------------------------ *
 * Half (B): the CPython repr(float) spelling vectors.
 * ------------------------------------------------------------------ */
static const struct { uint64_t bits; const char *want; } RYU_VECTORS[] = {
    { 0x430C6BF526340000ULL, "1000000000000000.0" },   /* fixed/scientific switch */
    { 0x4341C37937E08000ULL, "1e+16" },   /* fixed/scientific switch */
    { 0x4376345785D8A000ULL, "1e+17" },   /* fixed/scientific switch */
    { 0x4341C37937E07FFFULL, "9999999999999998.0" },   /* fixed/scientific switch */
    { 0x7FEFFFFFFFFFFFFFULL, "1.7976931348623157e+308" },   /* fixed/scientific switch */
    { 0x3F1A36E2EB1C432DULL, "0.0001" },   /* fixed/scientific switch */
    { 0x3EE4F8B588E368F1ULL, "1e-05" },   /* fixed/scientific switch */
    { 0x3F1F75104D551D69ULL, "0.00012" },   /* fixed/scientific switch */
    { 0x3EE92A737110E454ULL, "1.2e-05" },   /* fixed/scientific switch */
    { 0x0000000000000000ULL, "0.0" },   /* integral keeps .0 */
    { 0x8000000000000000ULL, "-0.0" },   /* integral keeps .0 */
    { 0x3FF0000000000000ULL, "1.0" },   /* integral keeps .0 */
    { 0x4014000000000000ULL, "5.0" },   /* integral keeps .0 */
    { 0xC014000000000000ULL, "-5.0" },   /* integral keeps .0 */
    { 0x4059000000000000ULL, "100.0" },   /* integral keeps .0 */
    { 0x4330000000000000ULL, "4503599627370496.0" },   /* integral keeps .0 */
    { 0x4340000000000000ULL, "9007199254740992.0" },   /* integral keeps .0 */
    { 0x3E6AD7F29ABCAF48ULL, "5e-08" },   /* exponent width >= 2 */
    { 0x3E7AD7F29ABCAF48ULL, "1e-07" },   /* exponent width >= 2 */
    { 0x54B249AD2594C37DULL, "1e+100" },   /* exponent width >= 2 */
    { 0x2B2BFF2EE48E0530ULL, "1e-100" },   /* exponent width >= 2 */
    { 0x0000000000000001ULL, "5e-324" },   /* exponent width >= 2 */
    { 0x000730D67819E8D2ULL, "1e-308" },   /* exponent width >= 2 */
    { 0x0010000000000000ULL, "2.2250738585072014e-308" },   /* exponent width >= 2 */
    { 0x7FE1CCF385EBC8A0ULL, "1e+308" },   /* exponent width >= 2 */
    { 0x0000000000000002ULL, "1e-323" },   /* exponent width >= 2 */
    { 0x3E70000000000000ULL, "5.960464477539063e-08" },   /* power of two (tie) */
    { 0xBE70000000000000ULL, "-5.960464477539063e-08" },   /* power of two (tie), negative */
    { 0x3E60000000000000ULL, "2.9802322387695312e-08" },   /* power of two (tie) */
    { 0xBE60000000000000ULL, "-2.9802322387695312e-08" },   /* power of two (tie), negative */
    { 0x3E10000000000000ULL, "9.313225746154785e-10" },   /* power of two (tie) */
    { 0xBE10000000000000ULL, "-9.313225746154785e-10" },   /* power of two (tie), negative */
    { 0x3D00000000000000ULL, "7.105427357601002e-15" },   /* power of two (tie) */
    { 0xBD00000000000000ULL, "-7.105427357601002e-15" },   /* power of two (tie), negative */
    { 0x3CB0000000000000ULL, "2.220446049250313e-16" },   /* power of two (tie) */
    { 0xBCB0000000000000ULL, "-2.220446049250313e-16" },   /* power of two (tie), negative */
    { 0x39B0000000000000ULL, "7.888609052210118e-31" },   /* power of two (tie) */
    { 0xB9B0000000000000ULL, "-7.888609052210118e-31" },   /* power of two (tie), negative */
    { 0x3370000000000000ULL, "6.223015277861142e-61" },   /* power of two (tie) */
    { 0xB370000000000000ULL, "-6.223015277861142e-61" },   /* power of two (tie), negative */
    { 0x2D30000000000000ULL, "4.909093465297727e-91" },   /* power of two (tie) */
    { 0xAD30000000000000ULL, "-4.909093465297727e-91" },   /* power of two (tie), negative */
    { 0x20B0000000000000ULL, "3.054936363499605e-151" },   /* power of two (tie) */
    { 0xA0B0000000000000ULL, "-3.054936363499605e-151" },   /* power of two (tie), negative */
    { 0x1430000000000000ULL, "1.90109156629516e-211" },   /* power of two (tie) */
    { 0x9430000000000000ULL, "-1.90109156629516e-211" },   /* power of two (tie), negative */
    { 0x07B0000000000000ULL, "1.1830521861667747e-271" },   /* power of two (tie) */
    { 0x87B0000000000000ULL, "-1.1830521861667747e-271" },   /* power of two (tie), negative */
    { 0x0170000000000000ULL, "9.332636185032189e-302" },   /* power of two (tie) */
    { 0x8170000000000000ULL, "-9.332636185032189e-302" },   /* power of two (tie), negative */
    { 0x0000000000000010ULL, "8e-323" },   /* power of two (tie) */
    { 0x8000000000000010ULL, "-8e-323" },   /* power of two (tie), negative */
    { 0x4170000000000000ULL, "16777216.0" },   /* power of two (positive exponent) */
    { 0x4630000000000000ULL, "1.2676506002282294e+30" },   /* power of two (positive exponent) */
    { 0x52B0000000000000ULL, "2.037035976334486e+90" },   /* power of two (positive exponent) */
    { 0x5F30000000000000ULL, "3.273390607896142e+150" },   /* power of two (positive exponent) */
    { 0x6BB0000000000000ULL, "5.260135901548374e+210" },   /* power of two (positive exponent) */
    { 0x7830000000000000ULL, "8.452712498170644e+270" },   /* power of two (positive exponent) */
    { 0x7E70000000000000ULL, "1.0715086071862673e+301" },   /* power of two (positive exponent) */
    { 0x3FB999999999999AULL, "0.1" },   /* everyday value */
    { 0x3FC999999999999AULL, "0.2" },   /* everyday value */
    { 0x3FD3333333333333ULL, "0.3" },   /* everyday value */
    { 0x3FD5555555555555ULL, "0.3333333333333333" },   /* everyday value */
    { 0x3FE5555555555555ULL, "0.6666666666666666" },   /* everyday value */
    { 0x400921FB54442D11ULL, "3.14159265358979" },   /* everyday value */
    { 0x4005BF0A8B145769ULL, "2.718281828459045" },   /* everyday value */
    { 0x3FF199999999999AULL, "1.1" },   /* everyday value */
    { 0x4023CCCCCCCCCCCDULL, "9.9" },   /* everyday value */
    { 0x3FE6666666666666ULL, "0.7" },   /* everyday value */
    { 0x40934A456D5CFAADULL, "1234.5678" },   /* everyday value */
    { 0x8000000000000001ULL, "-5e-324" },   /* subnormal, negative */
    { 0x8000000000000002ULL, "-1e-323" },   /* subnormal, negative */
    { 0x0000000000000003ULL, "1.5e-323" },   /* subnormal */
    { 0x8000000000000003ULL, "-1.5e-323" },   /* subnormal, negative */
    { 0x0008000000000000ULL, "1.1125369292536007e-308" },   /* subnormal */
    { 0x8008000000000000ULL, "-1.1125369292536007e-308" },   /* subnormal, negative */
    { 0x000FFFFFFFFFFFFFULL, "2.225073858507201e-308" },   /* subnormal */
    { 0x800FFFFFFFFFFFFFULL, "-2.225073858507201e-308" },   /* subnormal, negative */
    { 0x41E0000000000000ULL, "2147483648.0" },   /* int boundary */
    { 0x41F0000000000000ULL, "4294967296.0" },   /* int boundary */
    { 0x43E0000000000000ULL, "9.223372036854776e+18" },   /* int boundary */
    { 0x43F0000000000000ULL, "1.8446744073709552e+19" },   /* int boundary */
    { 0x4340000000000001ULL, "9007199254740994.0" },   /* int boundary */
    { 0x4341C37937E08004ULL, "1.0000000000000008e+16" },   /* int boundary */
    { 0x3EE9E409302678BAULL, "1.2345678901234568e-05" },   /* long significand */
    { 0x44B52D02C7E14AF6ULL, "1e+23" },   /* long significand */
    { 0x0004000000000000ULL, "5.562684646268003e-309" },   /* long significand */
};

/* ------------------------------------------------------------------ *
 * Plumbing: srmech's OWN libm-free correctly-rounded decimal -> double
 * (rc397), reached through the public TOML parser. Using srmech's own
 * parser rather than the platform strtod keeps the whole gate inside
 * ADR-0003's bare-C host.
 * ------------------------------------------------------------------ */

/* Parse `dec` as a TOML float; 1 on success with *out set. */
static int parse_decimal(const char *dec, double *out)
{
    char doc[96];
    srmech_toml_value_t *root = NULL;
    const srmech_toml_value_t *v;
    int w = snprintf(doc, sizeof(doc), "x = %s\n", dec);
    if (w <= 0 || (size_t)w >= sizeof(doc)) { return 0; }
    if (srmech_toml_parse(doc, (size_t)w, ws, sizeof(ws), &root) != SRMECH_OK) {
        return 0;
    }
    v = srmech_toml_table_get(root, "x");
    if (v == NULL || v->type != SRMECH_TOML_FLOAT) { return 0; }
    *out = v->u.f;
    return 1;
}

/* True iff `dec` parses back to exactly the bits of `want`. */
static int round_trips(const char *dec, double want)
{
    double got = 0.0;
    if (!parse_decimal(dec, &got)) { return 0; }
    return memcmp(&got, &want, sizeof(double)) == 0;
}

static double from_bits(uint64_t bits)
{
    double v;
    memcpy(&v, &bits, sizeof(v));
    return v;
}

/* ------------------------------------------------------------------ *
 * Half (A): decompose the emitted repr into (significant digits, decpt)
 * so the one-digit-shorter neighbours can be constructed.
 * ------------------------------------------------------------------ */

/* Pull the significant digits + decimal-point position out of a repr string.
 * Trailing zeros are stripped so `ndig` is the significant-digit COUNT.
 * Returns 0 if the string is not a finite decimal we can decompose. */
static int split_repr(const char *s, char *digs, int *ndig, int *decpt)
{
    int i = 0, n = 0, dot = -1, exp10 = 0, lead = 0;
    if (s[i] == '-') { i++; }
    for (; s[i] != '\0' && s[i] != 'e'; i++) {
        if (s[i] == '.') { dot = n; continue; }
        if (s[i] < '0' || s[i] > '9') { return 0; }
        if (n == 0 && s[i] == '0' && dot < 0) { continue; }  /* leading "0." */
        digs[n++] = s[i];
    }
    if (dot < 0) { dot = n; }
    if (s[i] == 'e') { exp10 = (int)strtol(s + i + 1, NULL, 10); }
    while (lead < n && digs[lead] == '0') { lead++; }         /* 0.000123 */
    memmove(digs, digs + lead, (size_t)(n - lead));
    n -= lead;
    if (n == 0) { return 0; }
    *decpt = dot - lead + exp10;
    while (n > 1 && digs[n - 1] == '0') { n--; }              /* 100.0 -> 1 */
    *ndig = n;
    return 1;
}

/* Render (digits, decpt, negative) as "D.DDDe+XX" for re-parsing. */
static void render_sci(char *out, const char *digs, int ndig, int decpt, int neg)
{
    int p = 0, i;
    if (neg) { out[p++] = '-'; }
    out[p++] = digs[0];
    out[p++] = '.';
    for (i = 1; i < ndig; i++) { out[p++] = digs[i]; }
    if (ndig == 1) { out[p++] = '0'; }
    out[p] = '\0';
    snprintf(out + p, 16, "e%+d", decpt - 1);
}

/* Build the two (ndig-1)-digit candidates: truncate, and truncate-then-
 * increment (with carry). Both are written as decimal strings. */
static void shorter_pair(const char *digs, int ndig, int decpt, int neg,
                         char *lo, char *hi)
{
    char t[24];
    int m = ndig - 1, i, carry = 1;
    memcpy(t, digs, (size_t)m);
    render_sci(lo, t, m, decpt, neg);
    for (i = m - 1; i >= 0 && carry; i--) {
        if (t[i] == '9') { t[i] = '0'; }
        else { t[i] = (char)(t[i] + 1); carry = 0; }
    }
    if (carry) {                       /* 999 -> 1000, i.e. "1" one decade up */
        t[0] = '1';
        render_sci(hi, t, 1, decpt + 1, neg);
        return;
    }
    render_sci(hi, t, m, decpt, neg);
}

/* THE MINIMALITY PROOF for one value: the emitted decimal round-trips, and
 * neither one-digit-shorter neighbour does. */
static void check_shortest(uint64_t bits)
{
    double v = from_bits(bits);
    char rep[64], digs[24], lo[64], hi[64];
    size_t rlen = 0u;
    int ndig = 0, decpt = 0, neg = (int)(bits >> 63);
    if (srmech_double_repr(v, rep, sizeof(rep), &rlen) != SRMECH_OK) { return; }
    checked++;
    if (!round_trips(rep, v)) {
        printf("FAIL: %s does not round-trip (bits %016llx)\n",
               rep, (unsigned long long)bits);
        fails++;
        return;
    }
    if (v == 0.0) { return; }
    if (!split_repr(rep, digs, &ndig, &decpt)) {
        printf("FAIL: cannot split %s\n", rep); fails++; return;
    }
    if (ndig < 2) { return; }                  /* already 1 digit — minimal */
    shorter_pair(digs, ndig, decpt, neg, lo, hi);
    if (round_trips(lo, v) || round_trips(hi, v)) {
        printf("FAIL: %s is NOT shortest — %s / %s also round-trip\n",
               rep, lo, hi);
        fails++;
    }
}

/* Deterministic xorshift64* — no rand(), so every host sweeps the same set. */
static uint64_t rng_state = 0x9E3779B97F4A7C15ULL;
static uint64_t next_bits(void)
{
    uint64_t x = rng_state;
    x ^= x >> 12; x ^= x << 25; x ^= x >> 27;
    rng_state = x;
    return x * 0x2545F4914F6CDD1DULL;
}

int main(void)
{
    size_t i;
    int e, k;
    char rep[64];
    size_t rlen = 0u;

    /* --- Half (B): the CPython repr(float) spelling vectors --------- */
    for (i = 0; i < sizeof(RYU_VECTORS) / sizeof(RYU_VECTORS[0]); i++) {
        double v = from_bits(RYU_VECTORS[i].bits);
        srmech_status_t st = srmech_double_repr(v, rep, sizeof(rep), &rlen);
        if (st != SRMECH_OK) {
            printf("FAIL: status %d for %016llx\n", (int)st,
                   (unsigned long long)RYU_VECTORS[i].bits);
            fails++;
            continue;
        }
        if (strcmp(rep, RYU_VECTORS[i].want) != 0) {
            printf("FAIL: %016llx -> \"%s\", want \"%s\"\n",
                   (unsigned long long)RYU_VECTORS[i].bits, rep,
                   RYU_VECTORS[i].want);
            fails++;
        }
        CHECK(rlen == strlen(rep), "out_len disagrees with strlen");
    }

    /* --- Half (A) on the ZERO-MANTISSA class, EXHAUSTIVELY ---------- */
    /* All 4196 signed powers of two. 92 of these were wrong before rc403. */
    for (e = 1; e < 2047; e++) {
        check_shortest(((uint64_t)e) << 52);
        check_shortest((1ULL << 63) | (((uint64_t)e) << 52));
    }
    for (k = 0; k < 52; k++) {                        /* subnormal powers */
        check_shortest(1ULL << k);
        check_shortest((1ULL << 63) | (1ULL << k));
    }

    /* --- Half (A) on exact dyadic fractions k / 2**n ---------------- */
    for (e = 1; e < 2047; e += 7) {
        for (k = 1; k < 40; k++) {
            check_shortest((((uint64_t)e) << 52) | (uint64_t)k);
            check_shortest((((uint64_t)e) << 52) | ((uint64_t)k << 48));
        }
    }

    /* --- Half (A) on a deterministic random sweep ------------------- */
    for (i = 0; i < 60000u; i++) {
        uint64_t b = next_bits();
        if (((b >> 52) & 0x7FFULL) == 0x7FFULL) { b &= ~(1ULL << 62); }
        check_shortest(b);
    }

    /* --- boundary contract ----------------------------------------- */
    CHECK(srmech_double_repr(1.0, NULL, 32u, &rlen) == SRMECH_ERR_NULL_ARG,
          "NULL buffer must be NULL_ARG");
    CHECK(srmech_double_repr(1.0, rep, 8u, &rlen) == SRMECH_ERR_NULL_ARG,
          "too-small cap must be NULL_ARG");
    {   /* non-finite DEFERS — built from bits, never 1.0/0.0 (MSVC C2124) */
        double inf = from_bits(0x7FF0000000000000ULL);
        double nan = from_bits(0x7FF8000000000000ULL);
        CHECK(srmech_double_repr(inf, rep, sizeof(rep), &rlen)
              == SRMECH_ERR_BAD_INPUT, "+inf must defer");
        CHECK(srmech_double_repr(-inf, rep, sizeof(rep), &rlen)
              == SRMECH_ERR_BAD_INPUT, "-inf must defer");
        CHECK(srmech_double_repr(nan, rep, sizeof(rep), &rlen)
              == SRMECH_ERR_BAD_INPUT, "nan must defer");
    }

    printf("test_srmech_ryu_repr_rc403: %ld values proved shortest, %d failures\n",
           checked, fails);
    return fails == 0 ? 0 : 1;
}
