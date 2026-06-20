/*
 * test_srmech_trans_q61.c — 0.9.0rc8 standalone C-HOST proof for the Q61
 * stay-rational transcendental surface (F868).
 *
 * THE POINT (the user requirement: "the C code must support c host only
 * environments"): a C-ONLY host — no Python, no libm transcendentals beyond
 * what srmech itself ships — reassembles the EXACT rational that Python's
 * rational.{sin,cos,tan,atan,atan2,exp,log,sqrt,hypot} return, using ONLY the
 * six atomic srmech_*_q61 peers + the three exposed Q61 model constants
 * (SRMECH_Q61_ONE / SRMECH_Q61_LN2 / SRMECH_Q61_HALF_PI). No Python is present
 * at build or run time. (libm sin/cos/exp/... is used ONLY as the test ORACLE
 * to check srmech's own answer — never as part of the srmech computation.)
 *
 * Build + run (Linux gcc / macOS clang), pedantic, warnings = errors:
 *   cc -std=c11 -Wall -Wextra -Wpedantic -Werror -I../include \
 *      test_srmech_trans_q61.c ../src/srmech_*.c -lm -o /tmp/trans_q61 && /tmp/trans_q61
 *
 * Mirrors the assert+count house style of test_srmech_sha256.c (no framework;
 * exits 0 on all-pass, non-zero on first fail). Asserts: (1) the EXACT int64
 * identities reassemble bit-exactly (sin0=0, cos0=1, atan0=0, exp0=1, log1=0,
 * sqrt4=2, sqrt(1/4)=1/2); (2) each peer's float projection matches libm over a
 * spread; (3) the three COMPOSED ops (tan, atan2, hypot) a C host builds from
 * the peers + constants match libm — proving the full surface is standalone;
 * (4) 0.9.0rc10 — the literal exp(mu*theta) hypercomplex twiddle
 * (srmech_hypercomplex_exp_q61, F882): 8 Q61 int64 = cos theta + mu*sin theta
 * for k_axes in {1,3,7} (C/H/O), the imaginary slots bit-equal, |q| = 1, and
 * k_axes outside {1,3,7} a clean BAD_INPUT — proving the twiddle is C-host-only.
 */

#include "srmech.h"

#include <math.h>
#include <stdint.h>
#include <stdio.h>

static int g_passed = 0;
static int g_failed = 0;

static void check_close(double got, double want, double tol, const char *desc)
{
    double d = got - want;
    if (d < 0.0) { d = -d; }
    if (d <= tol) {
        g_passed++;
        printf("  PASS  %s (got=%.17g want=%.17g)\n", desc, got, want);
    } else {
        g_failed++;
        printf("  FAIL  %s\n    got:  %.17g\n    want: %.17g\n    |d|:  %.3g > %.3g\n",
               desc, got, want, d, tol);
    }
}

static void check_eq_i64(int64_t got, int64_t want, const char *desc)
{
    if (got == want) {
        g_passed++;
        printf("  PASS  %s (=%lld)\n", desc, (long long)got);
    } else {
        g_failed++;
        printf("  FAIL  %s\n    got:  %lld\n    want: %lld\n",
               desc, (long long)got, (long long)want);
    }
}

/* ---- assembly helpers: peer int64 pieces -> double, per the header recipe ---- */
/* These are exactly what a C-only consumer writes; they call NO libm trig. */

static double q61_sin(double x)
{
    int64_t c = 0;
    if (srmech_sin_q61(x, &c) != SRMECH_OK) { return NAN; }
    return (double)c / (double)SRMECH_Q61_ONE;
}

static double q61_cos(double x)
{
    int64_t c = 0;
    if (srmech_cos_q61(x, &c) != SRMECH_OK) { return NAN; }
    return (double)c / (double)SRMECH_Q61_ONE;
}

static double q61_atan(double x)
{
    int64_t c = 0;
    if (srmech_atan_q61(x, &c) != SRMECH_OK) { return NAN; }
    return (double)c / (double)SRMECH_Q61_ONE;
}

static double q61_exp(double x)
{
    int64_t core = 0, n = 0;
    if (srmech_exp_q61(x, &core, &n) != SRMECH_OK) { return NAN; }
    return ldexp((double)core / (double)SRMECH_Q61_ONE, (int)n);
}

static double q61_log(double x)
{
    int64_t logm = 0, e = 0;
    if (srmech_log_q61(x, &logm, &e) != SRMECH_OK) { return NAN; }
    /* float projection: log(m) + e*ln2 (the EXACT rational would do this
     * recombine in int128/bignum — see the header — but the float result is
     * the libm-faithful last-mile). */
    return (double)logm / (double)SRMECH_Q61_ONE
           + (double)e * ((double)SRMECH_Q61_LN2 / (double)SRMECH_Q61_ONE);
}

static double q61_sqrt(double x)
{
    int64_t root = 0, p = 0;
    if (srmech_sqrt_q61(x, &root, &p) != SRMECH_OK) { return NAN; }
    return ldexp((double)root, (int)p);
}

/* ---- composed ops a C host builds from the peers + constants (no libm) ---- */

static double q61_tan(double x)         { return q61_sin(x) / q61_cos(x); }
static double q61_hypot(double a, double b) { return q61_sqrt(a * a + b * b); }

/* atan2 via atan-peer + quadrant shift using the SRMECH_Q61_HALF_PI anchor */
static double q61_atan2(double y, double x)
{
    const double half_pi = (double)SRMECH_Q61_HALF_PI / (double)SRMECH_Q61_ONE;
    if (x > 0.0) { return q61_atan(y / x); }
    if (x < 0.0) {
        double a = q61_atan(y / x);
        return (y >= 0.0) ? a + 2.0 * half_pi : a - 2.0 * half_pi;
    }
    /* x == 0 */
    return (y > 0.0) ? half_pi : (y < 0.0) ? -half_pi : 0.0;
}

int main(void)
{
    printf("test_srmech_trans_q61 — standalone C-host Q61 transcendental surface\n");

    /* (0) the exposed constants are the documented round(c * 2^61) anchors */
    check_eq_i64(SRMECH_Q61_ONE, INT64_C(2305843009213693952), "SRMECH_Q61_ONE == 2^61");
    check_eq_i64(SRMECH_Q61_LN2, INT64_C(1598288580650331957), "SRMECH_Q61_LN2 anchor");
    check_eq_i64(SRMECH_Q61_HALF_PI, INT64_C(3622009729038561421), "SRMECH_Q61_HALF_PI anchor");

    /* (1) EXACT int64 identities — the rational reassembles bit-exactly */
    {
        int64_t c = 0, core = 0, n = 0, logm = 0, e = 0, root = 0, p = 0;
        srmech_sin_q61(0.0, &c);    check_eq_i64(c, 0, "sin(0) core == 0");
        srmech_cos_q61(0.0, &c);    check_eq_i64(c, SRMECH_Q61_ONE, "cos(0) core == 2^61 (=1)");
        srmech_atan_q61(0.0, &c);   check_eq_i64(c, 0, "atan(0) core == 0");
        srmech_exp_q61(0.0, &core, &n);
        check_eq_i64(core, SRMECH_Q61_ONE, "exp(0) core == 2^61");
        check_eq_i64(n, 0, "exp(0) n == 0");
        srmech_log_q61(1.0, &logm, &e);
        check_eq_i64(logm, 0, "log(1) logm == 0");
        check_eq_i64(e, 0, "log(1) e == 0");
        srmech_sqrt_q61(4.0, &root, &p);
        check_close(ldexp((double)root, (int)p), 2.0, 0.0, "sqrt(4) == 2 exactly");
        srmech_sqrt_q61(0.25, &root, &p);
        check_close(ldexp((double)root, (int)p), 0.5, 0.0, "sqrt(1/4) == 1/2 exactly");
    }

    /* (2) float projection of each peer vs libm over a spread */
    {
        const double xs[] = {-3.0, -1.25, -0.3, 0.1, 0.7, 1.0, 2.5};
        const int nx = (int)(sizeof xs / sizeof xs[0]);
        for (int i = 0; i < nx; i++) {
            double x = xs[i];
            check_close(q61_sin(x), sin(x), 1e-12, "sin vs libm");
            check_close(q61_cos(x), cos(x), 1e-12, "cos vs libm");
            check_close(q61_atan(x), atan(x), 1e-12, "atan vs libm");
            check_close(q61_exp(x), exp(x), 1e-12 * exp(x), "exp vs libm");
        }
        const double pos[] = {0.05, 0.5, 1.0, 2.0, 7.3, 100.0, 1.0e6};
        const int np = (int)(sizeof pos / sizeof pos[0]);
        for (int i = 0; i < np; i++) {
            double x = pos[i];
            check_close(q61_log(x), log(x), 1e-12, "log vs libm");
            check_close(q61_sqrt(x), sqrt(x), 1e-12 * sqrt(x), "sqrt vs libm");
        }
    }

    /* (3) composed ops a C host builds standalone — vs libm */
    {
        check_close(q61_tan(0.7), tan(0.7), 1e-11, "tan(0.7) = sin/cos vs libm");
        check_close(q61_tan(-1.1), tan(-1.1), 1e-11, "tan(-1.1) = sin/cos vs libm");
        check_close(q61_hypot(3.0, 4.0), 5.0, 0.0, "hypot(3,4) == 5 exactly");
        check_close(q61_hypot(0.6, 0.8), 1.0, 1e-12, "hypot(0.6,0.8) vs libm");
        check_close(q61_atan2(1.0, 1.0), atan2(1.0, 1.0), 1e-12, "atan2(1,1) vs libm");
        check_close(q61_atan2(1.0, 0.0), atan2(1.0, 0.0), 1e-12, "atan2(1,0)=pi/2 via half_pi");
        check_close(q61_atan2(1.0, -1.0), atan2(1.0, -1.0), 1e-12, "atan2(1,-1) quadrant II");
        check_close(q61_atan2(-1.0, -1.0), atan2(-1.0, -1.0), 1e-12, "atan2(-1,-1) quadrant III");
    }

    /* (4) 0.9.0rc10 — the literal exp(mu*theta) hypercomplex twiddle (F882),
     * standalone C-host: cos theta + mu*sin theta as 8 Q61 int64, |q| = 1. */
    {
        int64_t q8[8];
        const double inv = 1.0 / (double)SRMECH_Q61_ONE;   /* Q61 -> double */
        srmech_status_t st = srmech_hypercomplex_exp_q61(0.7, 1, q8);
        check_eq_i64((int64_t)st, (int64_t)SRMECH_OK, "exp_q61(0.7,1) -> OK");
        check_close((double)q8[0] * inv, cos(0.7), 1e-12, "k=1 q[0] = cos theta");
        check_close((double)q8[1] * inv, sin(0.7), 1e-12, "k=1 q[1] = sin theta");
        for (int a = 2; a < 8; a++) {
            check_eq_i64(q8[a], 0, "k=1 empty axis is exactly 0");
        }
        /* k=3 (quaternion): the 3 imaginary slots are bit-equal; |q| = 1. */
        st = srmech_hypercomplex_exp_q61(0.9, 3, q8);
        check_eq_i64((int64_t)st, (int64_t)SRMECH_OK, "exp_q61(0.9,3) -> OK");
        check_eq_i64(q8[2], q8[1], "k=3 slot2 == slot1");
        check_eq_i64(q8[3], q8[1], "k=3 slot3 == slot1");
        check_eq_i64(q8[4], 0, "k=3 slot4 is exactly 0");
        double n2 = 0.0;
        for (int a = 0; a < 8; a++) { double c = (double)q8[a] * inv; n2 += c * c; }
        check_close(n2, 1.0, 1e-9, "k=3 unit norm |q|^2 = 1");
        /* k=7 (octonion / ODFT twiddle): all 7 imaginary slots bit-equal. */
        st = srmech_hypercomplex_exp_q61(1.3, 7, q8);
        check_eq_i64((int64_t)st, (int64_t)SRMECH_OK, "exp_q61(1.3,7) -> OK");
        check_eq_i64(q8[7], q8[1], "k=7 slot7 == slot1");
        n2 = 0.0;
        for (int a = 0; a < 8; a++) { double c = (double)q8[a] * inv; n2 += c * c; }
        check_close(n2, 1.0, 1e-9, "k=7 unit norm |q|^2 = 1");
        /* k outside {1,3,7} is a clean BAD_INPUT, not a crash. */
        st = srmech_hypercomplex_exp_q61(0.5, 2, q8);
        check_eq_i64((int64_t)st, (int64_t)SRMECH_ERR_BAD_INPUT,
                     "exp_q61(.,2) -> BAD_INPUT");
    }

    printf("\n%d passed, %d failed\n", g_passed, g_failed);
    return (g_failed == 0) ? 0 : 1;
}
