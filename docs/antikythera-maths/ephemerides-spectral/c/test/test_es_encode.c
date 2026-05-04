/*
 * test_es_encode.c — smoke test for the C BIP encoder.
 *
 * Sanity-checks:
 *   1. es_version() returns "0.1.0".
 *   2. es_encode_state(0) returns the initial-phase table verbatim.
 *   3. es_encode_state(20*365.25) returns SOMETHING (no crash, all
 *      phases land in [0, 2^32)).
 *   4. es_encode_state(REFERENCE_JD - REFERENCE_JD) is identity.
 *   5. Bounds-check rejects |delta_t| > ES_DELTA_DAYS_LIMIT.
 *   6. Bounds-check rejects NaN / +/- inf.
 *   7. NULL output rejected.
 *   8. es_body_index("earth") returns the same idx the Python tables
 *      use (verified by checking that the body name at that idx is
 *      "earth").
 *   9. es_cos_lut(0, 1) == ES_COSINE_LUT_AMP, es_cos_lut(MODULO/2, 1)
 *      == -ES_COSINE_LUT_AMP.
 *  10. Bind operator: es_bind(a, MODULO - a) == 0 (modular inverse).
 *
 * Cross-language parity (the integer phases at JD = REFERENCE_JD +
 * 20yr should match the Python BIP encoder bit-for-bit) is tested by
 * a separate Python script that reads the JSON dump emitted here.
 *
 * Build (no CMake required for the smoke test):
 *
 *   gcc -std=c17 -Wall -Wextra -Wpedantic -O2 \
 *       -I include test/test_es_encode.c src/es_*.c -lm -o test_es_encode
 *
 *   ./test_es_encode
 */

#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "ephemerides_spectral.h"

/* ------------------------------------------------------------------ */

#define TEST_ASSERT(cond, msg) do {                              \
    if (!(cond)) {                                               \
        fprintf(stderr, "FAIL @ %s:%d: %s\n", __FILE__, __LINE__,\
                msg);                                            \
        return 1;                                                \
    }                                                            \
} while (0)


static int test_version(void) {
    const char *v = es_version();
    TEST_ASSERT(strcmp(v, ES_VERSION_STRING) == 0,
                "es_version() != ES_VERSION_STRING");
    return 0;
}

static int test_encode_zero(void) {
    /* delta_t = 0 should reproduce the calibrated initial phases. */
    uint32_t out[ES_N_BODIES];
    es_status_t st = es_encode_state(0.0, out);
    TEST_ASSERT(st == ES_OK, "es_encode_state(0) failed");
    for (size_t i = 0; i < ES_N_BODIES; ++i) {
        TEST_ASSERT(out[i] == es_initial_phases[i],
                    "delta_t=0 does not reproduce initial phases");
    }
    return 0;
}

static int test_encode_long(void) {
    /* +20 years; just ensure no crash and sensible output. */
    uint32_t out[ES_N_BODIES];
    es_status_t st = es_encode_state(20.0 * 365.25, out);
    TEST_ASSERT(st == ES_OK, "es_encode_state(+20yr) failed");
    for (size_t i = 0; i < ES_N_BODIES; ++i) {
        /* uint32 — implicitly in [0, 2^32). Just touch every entry. */
        (void)out[i];
    }
    return 0;
}

static int test_encode_backwards(void) {
    /* -20 years; signed step path. */
    uint32_t out[ES_N_BODIES];
    es_status_t st = es_encode_state(-20.0 * 365.25, out);
    TEST_ASSERT(st == ES_OK, "es_encode_state(-20yr) failed");
    return 0;
}

static int test_bounds_reject(void) {
    uint32_t out[ES_N_BODIES];
    /* > limit */
    es_status_t st = es_encode_state(1.0e10, out);
    TEST_ASSERT(st == ES_ERR_DELTA_OUT_OF_RANGE,
                "out-of-range delta_t not rejected");
    /* NaN */
    st = es_encode_state(NAN, out);
    TEST_ASSERT(st == ES_ERR_NON_FINITE_INPUT, "NaN delta_t not rejected");
    /* +inf */
    st = es_encode_state(INFINITY, out);
    TEST_ASSERT(st == ES_ERR_NON_FINITE_INPUT, "+inf delta_t not rejected");
    /* -inf */
    st = es_encode_state(-INFINITY, out);
    TEST_ASSERT(st == ES_ERR_NON_FINITE_INPUT, "-inf delta_t not rejected");
    return 0;
}

static int test_null_output(void) {
    es_status_t st = es_encode_state(0.0, NULL);
    TEST_ASSERT(st == ES_ERR_NULL_OUTPUT, "NULL output not rejected");
    return 0;
}

static int test_body_index(void) {
    size_t idx = es_body_index("earth");
    TEST_ASSERT(idx < ES_N_BODIES, "earth body index out of range");
    TEST_ASSERT(strcmp(es_bodies[idx].name, "earth") == 0,
                "earth body name mismatch at returned idx");
    /* Miss case */
    idx = es_body_index("not_a_real_body");
    TEST_ASSERT(idx == ES_N_BODIES, "miss-case did not return sentinel");
    /* NULL safety */
    idx = es_body_index(NULL);
    TEST_ASSERT(idx == ES_N_BODIES, "NULL name did not return sentinel");
    return 0;
}

static int test_cosine_lut(void) {
    /* cos(0) = 1 -> +AMP */
    int32_t v0 = es_cos_lut(0u, 1u);
    TEST_ASSERT(v0 == ES_COSINE_LUT_AMP, "cos_lut(0) != +AMP");
    /* cos(pi) = -1 -> -AMP. MODULO/2 = 0x80000000. */
    int32_t v_pi = es_cos_lut(0x80000000u, 1u);
    TEST_ASSERT(v_pi == -ES_COSINE_LUT_AMP, "cos_lut(pi) != -AMP");
    /* cos(pi/2) ~ 0. MODULO/4 = 0x40000000. */
    int32_t v_pi2 = es_cos_lut(0x40000000u, 1u);
    TEST_ASSERT(v_pi2 > -100 && v_pi2 < 100, "cos_lut(pi/2) far from 0");
    /* n_lobes folding: cos(pi/2 * 2) = cos(pi) = -AMP */
    int32_t v_fold = es_cos_lut(0x40000000u, 2u);
    TEST_ASSERT(v_fold == -ES_COSINE_LUT_AMP,
                "cos_lut(pi/2, n=2) != -AMP");
    return 0;
}

static int test_bind_inverse(void) {
    /* a + (2^32 - a) == 0 mod 2^32 */
    uint32_t a = 0x12345678u;
    uint32_t b = 0u - a;  /* implicit uint32 overflow gives the inverse */
    TEST_ASSERT(es_bind(a, b) == 0u, "bind(a, -a) != 0");
    return 0;
}

/* ------------------------------------------------------------------ */
/*  Parity-payload emission                                           */
/* ------------------------------------------------------------------ */

/* Emit a single line of JSON listing the encoded phases at +20yr.
 * The Python parity test runs the same encode in Python and
 * byte-compares this JSON line.
 */
static void emit_parity_payload(void) {
    uint32_t out[ES_N_BODIES];
    es_status_t st = es_encode_state(20.0 * 365.25, out);
    if (st != ES_OK) {
        fprintf(stderr, "parity payload encode failed: %d\n", (int)st);
        return;
    }
    printf("PARITY_PAYLOAD: {\"delta_t_days\": %g, \"phases_uint32\": [",
           20.0 * 365.25);
    for (size_t i = 0; i < ES_N_BODIES; ++i) {
        if (i > 0) {
            printf(", ");
        }
        printf("%u", (unsigned)out[i]);
    }
    printf("]}\n");
}

int main(void) {
    int failed = 0;
    failed += test_version();
    failed += test_encode_zero();
    failed += test_encode_long();
    failed += test_encode_backwards();
    failed += test_bounds_reject();
    failed += test_null_output();
    failed += test_body_index();
    failed += test_cosine_lut();
    failed += test_bind_inverse();
    if (failed) {
        fprintf(stderr, "%d test(s) FAILED\n", failed);
        return 1;
    }
    printf("all C smoke tests PASSED (%u bodies, version %s)\n",
           ES_N_BODIES, es_version());
    emit_parity_payload();
    return 0;
}
