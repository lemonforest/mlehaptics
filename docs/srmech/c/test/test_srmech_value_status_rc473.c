/*
 * test_srmech_value_status_rc473.c — 0.9.0rc473 BARE-C-HOST gate for the
 * value/status contract of the Class-N scalar roster and every exported
 * composite that calls it (`#T1188`).
 *
 * THE POINT. srmech's central architectural claim is that Python and C are
 * CO-EQUAL PROJECTIONS of the same mathematics — a bare-C host, with no Python
 * present, runs every op (ADR-0009 §2.1: "'Realizes it by calling the other
 * implementation' is not realizing it"; §2.4: implementations "may not differ
 * in which inputs they serve"). Measured on the rc472 tree, that claim was
 * false and nothing in the package could tell:
 *
 *     Python : equation_of_centre(2.0**53+1, 0.0549, 4)        -> REFUSES
 *     C      : srmech_equation_of_centre(2.0**53+1, 0.0549, 4) -> SRMECH_OK,
 *                                                    -0.08984990210223018
 *
 * A bare-C host computed a wrong number and was told it was correct — the
 * project's own top-severity class, silent wrong answer, live in one of the two
 * projections the architecture rests on.
 *
 * WHY THIS FILE EXISTS RATHER THAN ANOTHER PYTHON PARITY TEST. Every parity
 * test in the tree compares native-through-the-Python-wrapper against
 * pure-through-the-Python-wrapper. Measured at rc472: of the 47 test files
 * under python/tests whose name carries "parity", 42 make ZERO direct calls to
 * a C symbol, and of the five that do, none names a math op. So the sentence "our two
 * projections agree" had never been tested at the place where they could
 * disagree, and a guard added inside the Python wrapper turned those gates
 * green while the defect stayed exactly where it was. This file has no Python
 * anywhere in its acceptance path: it links libsrmech and calls the exported
 * symbols, which is the only vantage point from which the C projection's own
 * answer is observable.
 *
 * Build + run (Linux gcc / macOS clang), pedantic, warnings = errors:
 *   cc -std=c11 -Wall -Wextra -Wpedantic -Werror -I../include \
 *      test_srmech_value_status_rc473.c ../src/srmech_*.c -lm -o /tmp/vs && /tmp/vs
 * or, as CI runs it, through ctest:
 *   ctest --test-dir build -R value_status --output-on-failure
 *
 * RUNTIME `if`, NEVER `assert`. The shipped wheel builds Release
 * (python/pyproject.toml cmake.build-type), Release implies -DNDEBUG, and an
 * assert compiled out of a Release build is a CI-lane instrument rather than a
 * gate. Every row below is a runtime comparison that reports and counts, in the
 * g_passed / g_failed house style of test_srmech_trans_q61.c, and main returns
 * non-zero if any row failed.
 *
 * <math.h> is included for the INFINITY and NAN MACROS only. No libm function
 * is called anywhere in this file — NaN is detected as (x != x), which is the
 * same predicate srmech_trig.c uses, and no magnitude is ever taken (no abs();
 * every range row is written as an explicit two-sided comparison).
 *
 * ROW CLASSES, so a reader can tell what each failure means:
 *
 *   (1) DISCARD rows. The callee ALREADY refuses at rc472 and the composite
 *       returns SRMECH_OK anyway, because the call site spells
 *       `(void)srmech_sin(...)`. These rows need no contract change at all —
 *       they are red purely from the 24 discarded statuses, and they are the
 *       load-bearing proof that the discard is observable from outside the
 *       library.
 *   (2) CONTRACT rows. The callee itself answers SRMECH_OK for an argument the
 *       pure projection refuses. For sin/cos/atan/atan2 this is a repair to a
 *       PUBLISHED promise, not a new contract: srmech.h has said "returns
 *       SRMECH_ERR_BAD_INPUT for non-finite x (out set to NaN)" the whole time.
 *   (3) RANGE rows. An op that returns SRMECH_OK must return a value inside its
 *       own published range. These are decidable without settling any contract
 *       question, which is why they are here.
 *   (4) CONTROL rows. Arguments that MUST still succeed, so that a library
 *       which refused everything could not pass. An instrument that cannot
 *       return otherwise is not a measurement.
 *   (5) DECLINE rows, pinned. Behaviour rc473 deliberately does NOT change,
 *       named inline with the task that tracks it, so that changing it later is
 *       a decision rather than a drift.
 */

#include "srmech.h"

#include <math.h>
#include <stdint.h>
#include <stdio.h>

static int g_passed = 0;
static int g_failed = 0;

/* The double immediately below 2^55: just under a power of two the ulp is
 * 2^(54-52) = 4, so this is exactly 2^55 - 4. Self-checked in main() rather
 * than trusted, and nextafter() is deliberately not called (it is libm). */
#define SRMECH_VS_JUST_UNDER_2_55 36028797018963964.0
#define SRMECH_VS_2_55            36028797018963968.0

/* ------------------------------------------------------------------ *
 * Value spelling.
 *
 * Every value this file prints goes through srmech_double_repr — srmech's own
 * integer-only Ryu conversion — rather than printf("%.17g"), for two reasons
 * that are both about this gate being readable as evidence.
 *
 *  1. "%.17g" is NOT portable output. srmech.h records the measurement: MSVC
 *     spells 1e17 as `1e+017`. A gate that runs on three OSes and prints a
 *     different number on one of them cannot be quoted.
 *  2. srmech_double_repr returns the SHORTEST round-tripping spelling, which is
 *     the same one CPython's repr() returns. That makes the C projection's
 *     printed figure byte-identical to the Python projection's for the same
 *     double — which is the whole subject of this file.
 *
 * srmech_double_repr refuses a non-finite v by design (the caller decides the
 * spelling), so the helper supplies one.
 * ------------------------------------------------------------------ */
#define SRMECH_VS_REPR_CAP 40

static const char *vs_repr(double v, char *buf)
{
    size_t len = 0;
    if (srmech_double_repr(v, buf, (size_t)SRMECH_VS_REPR_CAP, &len) == SRMECH_OK) {
        return buf;
    }
    if (v != v) { return "nan"; }
    if (v > 0.0) { return "inf"; }
    return "-inf";
}

/* ------------------------------------------------------------------ *
 * Row primitives. Each reports its own line and counts.
 * ------------------------------------------------------------------ */

/* A row that MUST be refused. The failure text is deliberately phrased as a
 * complete sentence naming the call, the status and the value, because that is
 * what a reader of a CI log needs in order to act. */
static void check_refuses(srmech_status_t st, double out, const char *desc)
{
    char buf[SRMECH_VS_REPR_CAP];
    if (st != SRMECH_OK) {
        g_passed++;
        printf("  PASS  %s -> refused, status=%d\n", desc, (int)st);
        return;
    }
    g_failed++;
    printf("  FAIL  %s\n    %s returned SRMECH_OK with %s\n",
           desc, desc, vs_repr(out, buf));
}

/* A row that MUST succeed. Without these the gate could be satisfied by a
 * library that refused every input. */
static void check_accepts(srmech_status_t st, const char *desc)
{
    if (st == SRMECH_OK) {
        g_passed++;
        printf("  PASS  %s -> accepted\n", desc);
        return;
    }
    g_failed++;
    printf("  FAIL  %s\n    expected SRMECH_OK, got status=%d\n", desc, (int)st);
}

static void check_close(double got, double want, double tol, const char *desc)
{
    char buf[SRMECH_VS_REPR_CAP];
    char buf2[SRMECH_VS_REPR_CAP];
    double d = got - want;
    if (d < 0.0) { d = -d; }   /* a diagnostic magnitude, not a cascade op */
    if (d <= tol) {
        g_passed++;
        printf("  PASS  %s (got=%s)\n", desc, vs_repr(got, buf));
        return;
    }
    g_failed++;
    printf("  FAIL  %s\n    got:  %s\n    want: %s\n",
           desc, vs_repr(got, buf), vs_repr(want, buf2));
}

static void check_is_nan(double got, const char *desc)
{
    char buf[SRMECH_VS_REPR_CAP];
    if (got != got) {
        g_passed++;
        printf("  PASS  %s -> out is NaN\n", desc);
        return;
    }
    g_failed++;
    printf("  FAIL  %s\n    %s wrote %s where the header promises NaN\n",
           desc, desc, vs_repr(got, buf));
}

/* An op that returns SRMECH_OK must return a value inside its published range.
 * Written as a two-sided comparison so no magnitude is taken. */
static void check_in_range_if_ok(srmech_status_t st, double got,
                                 double lo, double hi, const char *desc)
{
    char buf[SRMECH_VS_REPR_CAP];
    char lobuf[SRMECH_VS_REPR_CAP];
    char hibuf[SRMECH_VS_REPR_CAP];
    if (st != SRMECH_OK) {
        g_passed++;
        printf("  PASS  %s -> refused, so no range claim is made\n", desc);
        return;
    }
    if (got >= lo && got <= hi) {
        g_passed++;
        printf("  PASS  %s -> in range [%s, %s]\n",
               desc, vs_repr(lo, lobuf), vs_repr(hi, hibuf));
        return;
    }
    g_failed++;
    printf("  FAIL  %s\n    %s returned SRMECH_OK with %s, outside [%s, %s]\n",
           desc, desc, vs_repr(got, buf), vs_repr(lo, lobuf), vs_repr(hi, hibuf));
}

/* A DECLINE row: behaviour rc473 leaves alone, pinned so that changing it is a
 * decision. `note` names the task that tracks the decline. */
static void check_pinned(srmech_status_t st, double out,
                         srmech_status_t want_st, double want_out,
                         const char *desc, const char *note)
{
    char buf[SRMECH_VS_REPR_CAP];
    char wbuf[SRMECH_VS_REPR_CAP];
    int st_ok = (st == want_st);
    int out_ok = (out == want_out) || ((out != out) && (want_out != want_out));
    if (st_ok && out_ok) {
        g_passed++;
        printf("  PASS  %s -> pinned at status=%d value=%s (%s)\n",
               desc, (int)st, vs_repr(out, buf), note);
        return;
    }
    g_failed++;
    printf("  FAIL  %s\n    pinned as status=%d value=%s; got status=%d value=%s\n"
           "    This is a tracked decline (%s). Moving it is a decision, not a drift.\n",
           desc, (int)want_st, vs_repr(want_out, wbuf), (int)st, vs_repr(out, buf),
           note);
}

/* ------------------------------------------------------------------ *
 * (4) CONTROL rows — the arguments that must still be served.
 * ------------------------------------------------------------------ */
static void rows_controls(void)
{
    double out = 0.0;
    srmech_status_t st;

    printf("\n[controls] arguments the roster MUST still serve\n");

    st = srmech_sin(SRMECH_VS_JUST_UNDER_2_55, &out);
    check_accepts(st, "sin(2^55 - 1ulp)");
    check_close(out, 0.05581618041342654, 1e-15, "sin(2^55 - 1ulp) value");

    st = srmech_cos(SRMECH_VS_JUST_UNDER_2_55, &out);
    check_accepts(st, "cos(2^55 - 1ulp)");
    check_close(out, 0.99844106185796258, 1e-15, "cos(2^55 - 1ulp) value");

    st = srmech_atan(1.0, &out);
    check_accepts(st, "atan(1.0)");
    check_close(out, 0.78539816339744828, 1e-15, "atan(1.0) value");

    st = srmech_atan2(1.0, 1.0, &out);
    check_accepts(st, "atan2(1.0, 1.0)");

    st = srmech_exp(1.0, &out);
    check_accepts(st, "exp(1.0)");

    st = srmech_log(2.0, &out);
    check_accepts(st, "log(2.0)");

    st = srmech_rational_sqrt(4.0, &out);
    check_accepts(st, "rational_sqrt(4.0)");
    check_close(out, 2.0, 1e-15, "rational_sqrt(4.0) value");

    /* atan is TOTAL on the extended reals and the pure projection agrees:
     * measured at rc472, srmech_atan(+inf) -> (OK, 1.5707963267948966) and
     * rational.atan(+inf) -> Q(3622009729038561421, 2305843009213693952),
     * the same pi/2. These rows are written FROM that measurement, not
     * assumed, and they are controls rather than refusals for that reason. */
    st = srmech_atan(INFINITY, &out);
    check_accepts(st, "atan(+inf)");
    check_close(out, 1.5707963267948966, 1e-15, "atan(+inf) value");

    st = srmech_atan(-INFINITY, &out);
    check_accepts(st, "atan(-inf)");
    check_close(out, -1.5707963267948966, 1e-15, "atan(-inf) value");

    st = srmech_atan2(INFINITY, 1.0, &out);
    check_accepts(st, "atan2(+inf, 1.0)");
    check_close(out, 1.5707963267948966, 1e-15, "atan2(+inf, 1.0) value");

    st = srmech_atan2(1.0, -INFINITY, &out);
    check_accepts(st, "atan2(1.0, -inf)");
    check_close(out, 3.1415926535897931, 1e-15, "atan2(1.0, -inf) value");

    /* Already correct at rc472: these rows would catch a repair that widened
     * a refusal past its domain. */
    st = srmech_sin(INFINITY, &out);
    check_refuses(st, out, "sin(+inf)");
    st = srmech_cos(-INFINITY, &out);
    check_refuses(st, out, "cos(-inf)");
    st = srmech_sin(SRMECH_VS_2_55, &out);
    check_refuses(st, out, "sin(2^55)");
    st = srmech_log(-1.0, &out);
    check_refuses(st, out, "log(-1.0)");
    st = srmech_rational_sqrt(-INFINITY, &out);
    check_refuses(st, out, "rational_sqrt(-inf)");
}

/* ------------------------------------------------------------------ *
 * (2) CONTRACT rows — the scalar callees themselves.
 *
 * For sin/cos/atan/atan2 this is the header's own published promise, which
 * srmech_trig.c has been violating: `(x == x) ? SRMECH_ERR_BAD_INPUT :
 * SRMECH_OK` returns OK for NaN. Every *_q61 peer in the same file already
 * refuses NaN (srmech_sin_q61(nan) and srmech_atan_q61(nan) both measured at
 * SRMECH_ERR_BAD_INPUT on the rc472 tree), so this is the double projection
 * being brought up to its own sibling. For exp/log/rational_sqrt the pure
 * projection refuses NaN and the C projection does not, which is ADR-0009 §2.4
 * "may not differ in which inputs they serve".
 * ------------------------------------------------------------------ */
static void rows_scalar_contract(void)
{
    double out = 0.0;
    srmech_status_t st;

    printf("\n[contract] the scalar roster must refuse what the pure projection refuses\n");

    st = srmech_sin(NAN, &out);
    check_refuses(st, out, "sin(nan)");
    st = srmech_cos(NAN, &out);
    check_refuses(st, out, "cos(nan)");
    st = srmech_atan(NAN, &out);
    check_refuses(st, out, "atan(nan)");
    st = srmech_atan2(NAN, 1.0, &out);
    check_refuses(st, out, "atan2(nan, 1.0)");
    st = srmech_atan2(1.0, NAN, &out);
    check_refuses(st, out, "atan2(1.0, nan)");
    /* The x == 0.0 early return, which never reaches srmech_atan at all —
     * so propagating atan's status is NOT sufficient for this row and the
     * repair has to check the arguments where they enter. Added in the
     * repair pass; the pure peer raises here too
     * (rational.atan2(nan, 0.0) -> ValueError). */
    st = srmech_atan2(NAN, 0.0, &out);
    check_refuses(st, out, "atan2(nan, 0.0)");
    st = srmech_exp(NAN, &out);
    check_refuses(st, out, "exp(nan)");
    st = srmech_log(NAN, &out);
    check_refuses(st, out, "log(nan)");
    st = srmech_rational_sqrt(NAN, &out);
    check_refuses(st, out, "rational_sqrt(nan)");

    /* The VALUE half of the contract, and a separate defect from the status
     * half. srmech.h and srmech_sqrt.c both say a negative argument leaves
     * *out at NaN; the implementation writes `x - x`, which is 0.0 for every
     * finite negative x. Measured at rc472: (SRMECH_ERR_BAD_INPUT, 0.0).
     * The status is already right here — only the written value is wrong,
     * which is exactly why a status-only gate would not have seen it. */
    out = -1.0;
    st = srmech_rational_sqrt(-4.0, &out);
    check_refuses(st, out, "rational_sqrt(-4.0)");
    check_is_nan(out, "rational_sqrt(-4.0) out");

    out = -1.0;
    st = srmech_sin(NAN, &out);
    if (st != SRMECH_OK) { check_is_nan(out, "sin(nan) out"); }
    else { printf("  SKIP  sin(nan) out — status row above already failed\n"); }
}

/* ------------------------------------------------------------------ *
 * (2) CONTRACT rows — srmech_winding_fold.
 *
 * ADDED IN THE REPAIR PASS, from a measurement the scoping did not have.
 * srmech_winding_fold is not one of the 24 discarded-status sites and was in
 * neither gate; it is in SRMECH_NODISCARD's roster as a "clean peer", which
 * is how it came to be measured at all. It carried BOTH halves of the defect
 * this rc repairs elsewhere, in the same translation unit:
 *
 *   winding_fold(NaN)  -> (SRMECH_OK, w=0, theta=NaN)          [status half]
 *   winding_fold(2^55) -> (SRMECH_ERR_BAD_INPUT, w=0, theta=0.0)  [value half]
 *
 * and srmech.h documented the first as deliberate, citing "the srmech_cos
 * convention" — a defect being quoted as a precedent. The pure peer
 * srmech.cascade.one.winding_fold raises ValueError for a non-finite theta
 * BEFORE it dispatches, so the C projection served an input the Python
 * projection refused, hidden behind a pre-dispatch guard in the other
 * projection: the exact shape this rc exists to remove.
 * ------------------------------------------------------------------ */
static void rows_winding_fold(void)
{
    int64_t w = -1;
    double th = -1.0;
    srmech_status_t st;

    printf("\n[contract] srmech_winding_fold — same domain as its own header says\n");

    w = -1; th = -1.0;
    st = srmech_winding_fold(NAN, &w, &th);
    check_refuses(st, th, "winding_fold(nan)");
    if (st != SRMECH_OK) { check_is_nan(th, "winding_fold(nan) theta"); }

    w = -1; th = -1.0;
    st = srmech_winding_fold(SRMECH_VS_2_55, &w, &th);
    check_refuses(st, th, "winding_fold(2^55)");
    if (st != SRMECH_OK) { check_is_nan(th, "winding_fold(2^55) theta"); }

    w = -1; th = -1.0;
    st = srmech_winding_fold(INFINITY, &w, &th);
    check_refuses(st, th, "winding_fold(+inf)");

    /* Control: an ordinary angle must still fold. */
    w = -1; th = -1.0;
    st = srmech_winding_fold(1.0, &w, &th);
    check_accepts(st, "winding_fold(1.0)");
    check_close(th, 1.0, 1e-15, "winding_fold(1.0) theta");
}

/* ------------------------------------------------------------------ *
 * (3) RANGE rows — decidable without settling any contract question.
 *
 * srmech_atan's published range is [-pi/2, pi/2] and srmech_atan2's is
 * [-pi, pi]. Measured at rc472, both return SRMECH_OK with
 * -3.2146018366025517 for a NaN argument — a FINITE value below -pi, produced
 * by (int64_t)(NaN * 2^61 + 0.5) in the Q61 reduction. A caller that range-
 * checks its own inputs and trusts the status gets a plausible-looking angle
 * that is outside the function's own codomain.
 *
 * srmech_atan2(+inf, +inf) is the same shape reached without any NaN input:
 * y/x is inf/inf = NaN inside srmech_atan2, so the poison value comes back
 * with SRMECH_OK. The pure projection answers pi/4 for that argument pair
 * (measured: rational.atan2(+inf, +inf) -> Q(905502432259640355,
 * 1152921504606846976) = 0.78539816339744828), so the two projections disagree
 * on this input in BOTH value and status today. This row asserts only the
 * decidable half — SRMECH_OK obliges a value in range — so it stays green
 * whichever way that disagreement is resolved.
 * ------------------------------------------------------------------ */
static void rows_range(void)
{
    double out = 0.0;
    srmech_status_t st;

    printf("\n[range] an op that returns SRMECH_OK must return a value in its own range\n");

    st = srmech_atan(NAN, &out);
    check_in_range_if_ok(st, out, -1.5707963267948966, 1.5707963267948966,
                         "atan(nan)");
    st = srmech_atan2(NAN, 1.0, &out);
    check_in_range_if_ok(st, out, -3.1415926535897931, 3.1415926535897931,
                         "atan2(nan, 1.0)");
    st = srmech_atan2(INFINITY, INFINITY, &out);
    check_in_range_if_ok(st, out, -3.1415926535897931, 3.1415926535897931,
                         "atan2(+inf, +inf)");
    st = srmech_atan2(-INFINITY, -INFINITY, &out);
    check_in_range_if_ok(st, out, -3.1415926535897931, 3.1415926535897931,
                         "atan2(-inf, -inf)");
}

/* ------------------------------------------------------------------ *
 * (1) DISCARD rows, scalar composites.
 *
 * Every row here is red at rc472 WITHOUT any contract change: the callee
 * already returns SRMECH_ERR_BAD_INPUT and the composite discards it.
 * ------------------------------------------------------------------ */
static void rows_composites(void)
{
    double out = 0.0;
    srmech_status_t st;

    printf("\n[discard] composites must propagate the status their callees return\n");

    /* 4 * (2^53 + 1) reaches exactly 2^55, which srmech_sin already refuses;
     * srmech_kepler.c:180 discards that refusal. This is the row the whole rc
     * is named for. */
    st = srmech_equation_of_centre(9007199254740993.0, 0.0549, 4, &out);
    check_refuses(st, out, "equation_of_centre(2^53+1, 0.0549, 4)");

    /* srmech_cos(2^55) already refuses; srmech_kepler.c:97 discards it. */
    st = srmech_pin_slot(SRMECH_VS_2_55, 0.5, 1.0, &out);
    check_refuses(st, out, "pin_slot(2^55, 0.5, 1.0)");

    /* srmech_sin(2^55) already refuses; srmech_kepler.c:130 discards it, and
     * the Newton iteration then never moves E off its M initial guess, so the
     * caller is handed E == M with SRMECH_OK. */
    st = srmech_kepler_solve(SRMECH_VS_2_55, 0.3, 1e-12, 20, &out);
    check_refuses(st, out, "kepler_solve(2^55, 0.3, 1e-12, 20)");

    /* Composite controls: ordinary arguments must still be served. */
    st = srmech_equation_of_centre(0.5, 0.0549, 4, &out);
    check_accepts(st, "equation_of_centre(0.5, 0.0549, 4)");
    st = srmech_pin_slot(0.5, 0.5, 1.0, &out);
    check_accepts(st, "pin_slot(0.5, 0.5, 1.0)");
    st = srmech_kepler_solve(0.5, 0.3, 1e-12, 20, &out);
    check_accepts(st, "kepler_solve(0.5, 0.3, 1e-12, 20)");
}

/* ------------------------------------------------------------------ *
 * (1) DISCARD rows, array kernels.
 * ------------------------------------------------------------------ */
static void rows_elementwise(void)
{
    double arr[1];
    double out[1];
    srmech_status_t st;

    printf("\n[discard] srmech_elementwise_transcendental must propagate per element\n");

    /* COS/SIN at 2^55 and at +inf: the scalar peer already refuses both. */
    arr[0] = SRMECH_VS_2_55; out[0] = 0.0;
    st = srmech_elementwise_transcendental(1u, arr, SRMECH_TRANS_COS, out);
    check_refuses(st, out[0], "elementwise([2^55], COS)");

    arr[0] = SRMECH_VS_2_55; out[0] = 0.0;
    st = srmech_elementwise_transcendental(1u, arr, SRMECH_TRANS_SIN, out);
    check_refuses(st, out[0], "elementwise([2^55], SIN)");

    arr[0] = INFINITY; out[0] = 0.0;
    st = srmech_elementwise_transcendental(1u, arr, SRMECH_TRANS_COS, out);
    check_refuses(st, out[0], "elementwise([+inf], COS)");

    arr[0] = INFINITY; out[0] = 0.0;
    st = srmech_elementwise_transcendental(1u, arr, SRMECH_TRANS_SIN, out);
    check_refuses(st, out[0], "elementwise([+inf], SIN)");

    /* NaN: the kernel's own LOG pre-scan is `arr[i] <= 0.0`, which is FALSE
     * for NaN, so NaN reaches the callee in every op including LOG. */
    arr[0] = NAN; out[0] = 0.0;
    st = srmech_elementwise_transcendental(1u, arr, SRMECH_TRANS_COS, out);
    check_refuses(st, out[0], "elementwise([nan], COS)");

    arr[0] = NAN; out[0] = 0.0;
    st = srmech_elementwise_transcendental(1u, arr, SRMECH_TRANS_SIN, out);
    check_refuses(st, out[0], "elementwise([nan], SIN)");

    arr[0] = NAN; out[0] = 0.0;
    st = srmech_elementwise_transcendental(1u, arr, SRMECH_TRANS_EXP, out);
    check_refuses(st, out[0], "elementwise([nan], EXP)");

    arr[0] = NAN; out[0] = 0.0;
    st = srmech_elementwise_transcendental(1u, arr, SRMECH_TRANS_LOG, out);
    check_refuses(st, out[0], "elementwise([nan], LOG)");

    /* Controls: the kernel's existing LOG domain pre-scan, and a row that
     * must still be served. */
    arr[0] = -INFINITY; out[0] = 0.0;
    st = srmech_elementwise_transcendental(1u, arr, SRMECH_TRANS_LOG, out);
    check_refuses(st, out[0], "elementwise([-inf], LOG)");

    arr[0] = 1.0; out[0] = 0.0;
    st = srmech_elementwise_transcendental(1u, arr, SRMECH_TRANS_COS, out);
    check_accepts(st, "elementwise([1.0], COS)");
}

static void rows_kuramoto(void)
{
    double theta[2];
    double omega[2] = { 0.0, 0.0 };
    double out[2];
    srmech_status_t st;

    printf("\n[discard] both Kuramoto steps must propagate their sin() status\n");

    /* At 2^55 the sin refusal is discarded and oscillator 0 is silently frozen
     * at its input phase — a wrong number with SRMECH_OK, not a NaN a caller
     * could notice. Measured at rc472: (SRMECH_OK, [0.0, 3.602879701896397e+16]). */
    theta[0] = 0.0; theta[1] = SRMECH_VS_2_55;
    out[0] = 0.0; out[1] = 0.0;
    st = srmech_cascade_kuramoto_step_f64(theta, omega, (size_t)2, 1.0, 0.1, out);
    check_refuses(st, out[0], "kuramoto_step_f64([0, 2^55])");

    theta[0] = 0.0; theta[1] = SRMECH_VS_2_55;
    out[0] = 0.0; out[1] = 0.0;
    st = srmech_cascade_kuramoto_step_general_f64(theta, omega, (size_t)2, NULL,
                                                  1.0, 0.1, NULL, NULL, 0.1, out);
    check_refuses(st, out[0], "kuramoto_step_general_f64([0, 2^55])");

    theta[0] = 0.0; theta[1] = INFINITY;
    out[0] = 0.0; out[1] = 0.0;
    st = srmech_cascade_kuramoto_step_f64(theta, omega, (size_t)2, 1.0, 0.1, out);
    check_refuses(st, out[0], "kuramoto_step_f64([0, +inf])");

    theta[0] = 0.0; theta[1] = INFINITY;
    out[0] = 0.0; out[1] = 0.0;
    st = srmech_cascade_kuramoto_step_general_f64(theta, omega, (size_t)2, NULL,
                                                  1.0, 0.1, NULL, NULL, 0.1, out);
    check_refuses(st, out[0], "kuramoto_step_general_f64([0, +inf])");

    theta[0] = 0.0; theta[1] = NAN;
    out[0] = 0.0; out[1] = 0.0;
    st = srmech_cascade_kuramoto_step_f64(theta, omega, (size_t)2, 1.0, 0.1, out);
    check_refuses(st, out[0], "kuramoto_step_f64([0, nan])");

    theta[0] = 0.0; theta[1] = NAN;
    out[0] = 0.0; out[1] = 0.0;
    st = srmech_cascade_kuramoto_step_general_f64(theta, omega, (size_t)2, NULL,
                                                  1.0, 0.1, NULL, NULL, 0.1, out);
    check_refuses(st, out[0], "kuramoto_step_general_f64([0, nan])");

    /* Control: an ordinary step must still be served. */
    theta[0] = 0.0; theta[1] = 1.0;
    out[0] = 0.0; out[1] = 0.0;
    st = srmech_cascade_kuramoto_step_f64(theta, omega, (size_t)2, 1.0, 0.1, out);
    check_accepts(st, "kuramoto_step_f64([0, 1.0])");
}

/* ------------------------------------------------------------------ *
 * (5) DECLINE rows, pinned.
 *
 * rc473 does NOT widen exp / log / rational_sqrt to refuse a non-finite
 * argument, and the reason is a measured hazard rather than a preference:
 * lap_sqrt(1.0 + tau*tau) in srmech_laplacian.c and sq_sqrt in srmech_svd_qr.c
 * both reach +Inf on the tau-overflow path and rely on sqrt(+Inf) = +Inf to get
 * t = 1/(tau + Inf) = 0. Widening the refusal turns a working numerics path
 * into a refusal inside static helpers that have no status channel. So C
 * answers these where the pure projection refuses them, which is a live
 * ADR-0009 §2.4 divergence, disclosed rather than repaired.
 *
 * Pinning it here is what keeps the decline honest: it is a row that an
 * instrument runs, not a sentence in a changelog. ADR-0009 §4 is explicit that
 * an exemption asserted in a docstring, a changelog entry or a test comment is
 * NOT an exemption, so the tracked filing this pin belongs to is owed
 * separately under `#T1188`; this row is only its executable half.
 * ------------------------------------------------------------------ */
static void rows_declines(void)
{
    double out = 0.0;
    srmech_status_t st;

    printf("\n[declined] non-finite exp/log/sqrt — C answers where pure refuses\n");

    st = srmech_exp(INFINITY, &out);
    check_pinned(st, out, SRMECH_OK, INFINITY, "exp(+inf)",
                 "tracked under `#T1188`; pure rational.exp(+inf) raises");
    st = srmech_exp(-INFINITY, &out);
    check_pinned(st, out, SRMECH_OK, 0.0, "exp(-inf)",
                 "tracked under `#T1188`; pure rational.exp(-inf) raises");
    st = srmech_log(INFINITY, &out);
    check_pinned(st, out, SRMECH_OK, INFINITY, "log(+inf)",
                 "tracked under `#T1188`; pure rational.log(+inf) raises");
    st = srmech_rational_sqrt(INFINITY, &out);
    check_pinned(st, out, SRMECH_OK, INFINITY, "rational_sqrt(+inf)",
                 "tracked under `#T1188`; the lap_sqrt/sq_sqrt tau-overflow path");
}

int main(void)
{
    printf("test_srmech_value_status_rc473 — the C projection's own answer\n");

    /* Self-check the two literal constants rather than trusting them: the
     * ulp just below a power of two is half the ulp just above it, and a
     * reader should not have to take that on faith. */
    if (SRMECH_VS_2_55 - SRMECH_VS_JUST_UNDER_2_55 == 4.0) {
        g_passed++;
        printf("  PASS  2^55 - (2^55 - 1ulp) == 4.0\n");
    } else {
        char buf[SRMECH_VS_REPR_CAP];
        g_failed++;
        printf("  FAIL  2^55 - (2^55 - 1ulp) == 4.0\n    got %s\n",
               vs_repr(SRMECH_VS_2_55 - SRMECH_VS_JUST_UNDER_2_55, buf));
    }

    rows_controls();
    rows_scalar_contract();
    rows_winding_fold();
    rows_range();
    rows_composites();
    rows_elementwise();
    rows_kuramoto();
    rows_declines();

    printf("\n%d passed, %d failed\n", g_passed, g_failed);
    return (g_failed == 0) ? 0 : 1;
}
