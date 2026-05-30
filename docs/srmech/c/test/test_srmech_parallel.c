/*
 * test_srmech_parallel.c — C-side smoke tests for
 * srmech_cascade_parallel_sector_dispatch (#771; MS#20 rc7).
 *
 * Exercises the THREADED dispatch with C-native bodies (a real-
 * symmetric, a sign/orientation, and a rotation body) and asserts the
 * decisive invariants:
 *   - 4 disjoint sector outputs written to out_sectors[s*n ..];
 *   - serial == threaded bit-for-bit (the dispatch output equals a
 *     locally-computed serial reference T_s(body(T_s(in))) — the
 *     sectors are independent / order-free);
 *   - sector 2 (γ₅-only) dual == srmech_cascade_chiral_dual_f64;
 *   - cap-at-4: n_sectors == 5 returns SRMECH_ERR_BAD_INPUT;
 *   - NULL / bad-arg / scratch-too-small error paths.
 *
 * assert + count, no test framework. Exits 0 on all-pass, non-zero on
 * any failure. Mirrors test_srmech_sha256.c discipline.
 */

#include "srmech.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int g_passed = 0;
static int g_failed = 0;

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

static void check_eq_int(int got, int want, const char *desc)
{
    if (got == want) {
        g_passed++;
        printf("  PASS  %s (=%d)\n", desc, got);
    } else {
        g_failed++;
        printf("  FAIL  %s\n    got:  %d\n    want: %d\n", desc, got, want);
    }
}

/* ----------------------------------------------------------------------
 * C-native cascade bodies. Each maps an f64 sequence to an f64 sequence.
 * ---------------------------------------------------------------------- */

/* Real-symmetric: out[i] = 2*x[i] (commutes with BOTH axes -> all four
 * sectors collapse to the same result). */
static srmech_status_t body_real_symmetric(const double *in, size_t n,
                                           double *out, void *user)
{
    (void)user;
    if (n > 0 && (in == NULL || out == NULL)) {
        return SRMECH_ERR_NULL_ARG;
    }
    for (size_t i = 0; i < n; ++i) {
        out[i] = 2.0 * in[i];
    }
    return SRMECH_OK;
}

/* Sign/orientation + position weight: out[i] = x[i] + (i + 1). Breaks
 * BOTH odd-equivariance and reversal-equivariance -> 4 distinct sectors
 * (the bi-axial body from the rc6 Python tests). */
static srmech_status_t body_biaxial(const double *in, size_t n,
                                    double *out, void *user)
{
    (void)user;
    if (n > 0 && (in == NULL || out == NULL)) {
        return SRMECH_ERR_NULL_ARG;
    }
    for (size_t i = 0; i < n; ++i) {
        out[i] = in[i] + (double)(i + 1);
    }
    return SRMECH_OK;
}

/* Rotation-like: out[i] = x[(i + 1) % n] (cyclic shift by one). A
 * genuine reordering body that is neither odd- nor reversal-symmetric. */
static srmech_status_t body_rotate(const double *in, size_t n,
                                   double *out, void *user)
{
    (void)user;
    if (n > 0 && (in == NULL || out == NULL)) {
        return SRMECH_ERR_NULL_ARG;
    }
    for (size_t i = 0; i < n; ++i) {
        out[i] = in[(i + 1) % n];
    }
    return SRMECH_OK;
}

/* ----------------------------------------------------------------------
 * Serial reference — recompute T_s(body(T_s(in))) directly, the same
 * way the dispatch does, so we can assert serial == threaded bit-exact.
 * gamma5 < 0 => reversal (chiral_flip); omega7 < 0 => per-element negate.
 * ---------------------------------------------------------------------- */
static const int SECTOR_G5[4] = { +1, +1, -1, -1 };
static const int SECTOR_W7[4] = { +1, -1, +1, -1 };

static void transform(int gamma5, int omega7, double *buf, size_t n)
{
    if (omega7 < 0) {
        for (size_t i = 0; i < n; ++i) {
            (void)srmech_cascade_reorient_f64((int8_t)-1, buf[i], &buf[i]);
        }
    }
    if (gamma5 < 0) {
        (void)srmech_cascade_chiral_flip_f64(buf, n, buf);
    }
}

static srmech_status_t serial_sector(srmech_cascade_body_f64 body,
                                     const double *in, size_t n, int s,
                                     double *out)
{
    double tmp[8];
    for (size_t i = 0; i < n; ++i) {
        tmp[i] = in[i];
    }
    transform(SECTOR_G5[s], SECTOR_W7[s], tmp, n);
    srmech_status_t rc = body(tmp, n, out, NULL);
    if (rc != SRMECH_OK) {
        return rc;
    }
    transform(SECTOR_G5[s], SECTOR_W7[s], out, n);
    return SRMECH_OK;
}

static int seq_equal(const double *a, const double *b, size_t n)
{
    for (size_t i = 0; i < n; ++i) {
        if (a[i] != b[i]) {
            return 0;
        }
    }
    return 1;
}

/* Run the dispatch for one body and assert serial == threaded for all 4
 * sectors plus sector-2 == chiral_dual. */
static void exercise_body(srmech_cascade_body_f64 body, const char *name)
{
    const double in[4] = { 1.0, 2.0, 4.0, 8.0 };
    const size_t n = 4;
    double out_sectors[4 * 4];
    double scratch[4 * 4];
    srmech_status_t rc = srmech_cascade_parallel_sector_dispatch(
        body, NULL, in, n, 4, out_sectors, scratch, sizeof(scratch) / sizeof(double));
    check_eq_int((int)rc, (int)SRMECH_OK, "dispatch returns OK");

    int all_match = 1;
    for (int s = 0; s < 4; ++s) {
        double ref[4];
        (void)serial_sector(body, in, n, s, ref);
        if (!seq_equal(out_sectors + (size_t)s * n, ref, n)) {
            all_match = 0;
        }
    }
    char d1[96];
    snprintf(d1, sizeof(d1), "[%s] serial == threaded bit-exact (all 4 sectors)", name);
    check_true(all_match, d1);

    /* Sector 2 (gamma5-only) dual IS srmech_cascade_chiral_dual_f64. */
    double dual[4];
    double ws[4];
    rc = srmech_cascade_chiral_dual_f64(body, NULL, in, n, dual, ws);
    char d2[96];
    snprintf(d2, sizeof(d2), "[%s] sector 2 == srmech_cascade_chiral_dual_f64", name);
    check_true(rc == SRMECH_OK && seq_equal(out_sectors + 2 * n, dual, n), d2);
}

int main(void)
{
    printf("== srmech_cascade_parallel_sector_dispatch smoke tests ==\n");
    printf("  srmech_version() = %s, ABI = %d\n",
           srmech_version(), srmech_abi_version());

    exercise_body(body_real_symmetric, "real_symmetric");
    exercise_body(body_biaxial, "biaxial");
    exercise_body(body_rotate, "rotate");

    /* Disjoint-output check: write a sentinel into every out slot, run
     * with 4 sectors, confirm every slot was overwritten (each sector
     * filled its own disjoint slice). */
    {
        const double in[4] = { 3.0, 5.0, 7.0, 11.0 };
        double out_sectors[4 * 4];
        double scratch[4 * 4];
        for (int i = 0; i < 16; ++i) {
            out_sectors[i] = -999.0;  /* sentinel */
        }
        srmech_status_t rc = srmech_cascade_parallel_sector_dispatch(
            body_biaxial, NULL, in, 4, 4, out_sectors, scratch, 16);
        int filled = (rc == SRMECH_OK);
        for (int i = 0; i < 16; ++i) {
            if (out_sectors[i] == -999.0) {
                filled = 0;
            }
        }
        check_true(filled, "all 4 disjoint output slices written (no sentinel left)");
    }

    /* Fewer sectors: n_sectors = 2 fills only the first 2 slices. */
    {
        const double in[4] = { 1.0, 2.0, 4.0, 8.0 };
        double out_sectors[2 * 4];
        double scratch[2 * 4];
        srmech_status_t rc = srmech_cascade_parallel_sector_dispatch(
            body_biaxial, NULL, in, 4, 2, out_sectors, scratch, 8);
        double ref0[4], ref1[4];
        (void)serial_sector(body_biaxial, in, 4, 0, ref0);
        (void)serial_sector(body_biaxial, in, 4, 1, ref1);
        check_true(rc == SRMECH_OK
                   && seq_equal(out_sectors + 0, ref0, 4)
                   && seq_equal(out_sectors + 4, ref1, 4),
                   "n_sectors=2 fills first 2 slices, serial-exact");
    }

    /* cap-at-4: n_sectors = 5 -> SRMECH_ERR_BAD_INPUT. */
    {
        const double in[4] = { 1.0, 2.0, 4.0, 8.0 };
        double out_sectors[5 * 4];
        double scratch[5 * 4];
        srmech_status_t rc = srmech_cascade_parallel_sector_dispatch(
            body_biaxial, NULL, in, 4, 5, out_sectors, scratch, 20);
        check_eq_int((int)rc, (int)SRMECH_ERR_BAD_INPUT,
                     "n_sectors=5 returns SRMECH_ERR_BAD_INPUT (cap-at-4)");
    }

    /* n_sectors = 0 -> SRMECH_ERR_BAD_INPUT. */
    {
        const double in[4] = { 1.0, 2.0, 4.0, 8.0 };
        double out_sectors[4];
        double scratch[4];
        srmech_status_t rc = srmech_cascade_parallel_sector_dispatch(
            body_biaxial, NULL, in, 4, 0, out_sectors, scratch, 4);
        check_eq_int((int)rc, (int)SRMECH_ERR_BAD_INPUT,
                     "n_sectors=0 returns SRMECH_ERR_BAD_INPUT");
    }

    /* NULL body -> SRMECH_ERR_NULL_ARG. */
    {
        const double in[4] = { 1.0, 2.0, 4.0, 8.0 };
        double out_sectors[4 * 4];
        double scratch[4 * 4];
        srmech_status_t rc = srmech_cascade_parallel_sector_dispatch(
            NULL, NULL, in, 4, 4, out_sectors, scratch, 16);
        check_eq_int((int)rc, (int)SRMECH_ERR_NULL_ARG,
                     "NULL body returns SRMECH_ERR_NULL_ARG");
    }

    /* scratch too small -> SRMECH_ERR_OVERFLOW. */
    {
        const double in[4] = { 1.0, 2.0, 4.0, 8.0 };
        double out_sectors[4 * 4];
        double scratch[4 * 4];
        srmech_status_t rc = srmech_cascade_parallel_sector_dispatch(
            body_biaxial, NULL, in, 4, 4, out_sectors, scratch, 8);
        check_eq_int((int)rc, (int)SRMECH_ERR_OVERFLOW,
                     "scratch_len < n_sectors*n returns SRMECH_ERR_OVERFLOW");
    }

    /* n == 0 edge: body called per sector with n=0; trivially OK. */
    {
        double out_sectors[1];
        double scratch[1];
        srmech_status_t rc = srmech_cascade_parallel_sector_dispatch(
            body_biaxial, NULL, NULL, 0, 4, out_sectors, scratch, 1);
        check_eq_int((int)rc, (int)SRMECH_OK,
                     "n=0 dispatch returns OK (empty cascade)");
    }

    printf("== %d passed, %d failed ==\n", g_passed, g_failed);
    return (g_failed == 0) ? 0 : 1;
}
