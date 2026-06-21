/*
 * test_srmech_qi.c — 0.9.0rc15 standalone C-HOST proof for the EXACT-complex
 * (Gaussian-rational) `Qi` carrier peer (srmech_qi.c).
 *
 * THE POINT (the C-host-only mandate): a C-ONLY host — no Python — does exact
 * `re + im·i` arithmetic over ℚ via the six srmech_qi_* ops, reassembling the
 * SAME exact rational limbs the Python `Qi` carrier returns. No Python at build
 * or run time; no libm (the ops are pure integer cascades over srmech_rational_*).
 *
 * Build + run (Linux gcc / macOS clang), pedantic, warnings = errors:
 *   cc -std=c11 -Wall -Wextra -Wpedantic -Werror -I../include \
 *      test_srmech_qi.c ../src/srmech_qi.c ../src/srmech_rational.c \
 *      ../src/srmech_cyclic.c -o /tmp/qi && /tmp/qi
 *
 * Mirrors the assert+count house style of test_srmech_sha256.c (no framework;
 * exits 0 on all-pass, non-zero on first fail). Checks: (1) add/sub/mul/
 * conjugate/quadrant/norm_sq return the EXACT reduced limbs for a worked
 * Gaussian-rational pair (bit-identical to Python's Qi); (2) the int64 limb
 * domain ceiling — an overflowing product returns SRMECH_ERR_OVERFLOW (the
 * Python Fraction path is the unbounded oracle); (3) a non-positive denominator
 * is a clean SRMECH_ERR_BAD_INPUT.
 */

#include "srmech.h"

#include <stdint.h>
#include <stdio.h>

static int g_passed = 0;
static int g_failed = 0;

static void check_i64(int64_t got, int64_t want, const char *desc)
{
    if (got == want) {
        g_passed++;
    } else {
        g_failed++;
        printf("FAIL %s: got %lld want %lld\n", desc,
               (long long)got, (long long)want);
    }
}

static void check_vec4(const int64_t got[4], int64_t w0, int64_t w1,
                       int64_t w2, int64_t w3, const char *desc)
{
    check_i64(got[0], w0, desc);
    check_i64(got[1], w1, desc);
    check_i64(got[2], w2, desc);
    check_i64(got[3], w3, desc);
}

static void check_status(srmech_status_t got, srmech_status_t want,
                         const char *desc)
{
    if (got == want) {
        g_passed++;
    } else {
        g_failed++;
        printf("FAIL %s: status got %d want %d\n", desc, (int)got, (int)want);
    }
}

int main(void)
{
    /* a = 3/2 − 4/5 i ; b = 1 + 2/3 i  (the Python Qi probe vectors). */
    const int64_t a[4] = {3, 2, -4, 5};
    const int64_t b[4] = {1, 1, 2, 3};
    int64_t out[4] = {0, 0, 0, 0};

    /* mul = (ac−bd) + (ad+bc)i = 61/30 + 1/5 i */
    check_status(srmech_qi_mul(a, b, out), SRMECH_OK, "mul status");
    check_vec4(out, 61, 30, 1, 5, "mul");

    /* add = 5/2 − 2/15 i */
    check_status(srmech_qi_add(a, b, out), SRMECH_OK, "add status");
    check_vec4(out, 5, 2, -2, 15, "add");

    /* sub = 1/2 − 22/15 i */
    check_status(srmech_qi_sub(a, b, out), SRMECH_OK, "sub status");
    check_vec4(out, 1, 2, -22, 15, "sub");

    /* conjugate(a) = 3/2 + 4/5 i */
    check_status(srmech_qi_conjugate(a, out), SRMECH_OK, "conj status");
    check_vec4(out, 3, 2, 4, 5, "conj");

    /* quadrant(a): re>0 -> bit0=0, im<0 -> bit1=1 -> 2 */
    int quad = -1;
    check_status(srmech_qi_quadrant(a, &quad), SRMECH_OK, "quad status");
    check_i64((int64_t)quad, 2, "quad");

    /* norm_sq(a) = (3/2)² + (4/5)² = 289/100 */
    int64_t nrm[2] = {0, 0};
    check_status(srmech_qi_norm_sq(a, nrm), SRMECH_OK, "norm status");
    check_i64(nrm[0], 289, "norm num");
    check_i64(nrm[1], 100, "norm den");

    /* int64 limb domain ceiling: (4e9)² overflows int64 -> OVERFLOW. */
    const int64_t big[4] = {4000000000LL, 1, 0, 1};
    check_status(srmech_qi_mul(big, big, out), SRMECH_ERR_OVERFLOW,
                 "overflow mul");

    /* a non-positive denominator is a clean BAD_INPUT. */
    const int64_t bad[4] = {1, 0, 0, 1};
    check_status(srmech_qi_add(bad, b, out), SRMECH_ERR_BAD_INPUT, "bad den");

    printf("test_srmech_qi: %d passed, %d failed\n", g_passed, g_failed);
    return g_failed == 0 ? 0 : 1;
}
