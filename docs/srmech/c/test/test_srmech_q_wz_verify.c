/*
 * test_srmech_q_wz_verify.c -- standalone smoke test for srmech_q_wz_verify (rc57).
 *
 * Validates the q-Wilf-Zeilberger VERIFY primitive against CONCRETE q-WZ triples over
 * (X,Y) = (q^n, q^k). Each triple (r_n=An/Ad, r_k=Bn/Bd, R=Xn/Xd) is a genuine q-WZ
 * pair: the cleared q-WZ identity
 *   (An - Ad)*(sigma_y(Xd)*Bd*Xd) == (sigma_y(Xn)*Bn*Xd - Xn*sigma_y(Xd)*Bd)*Ad
 * holds. srmech_q_wz_verify must return *out_equal=1 for the genuine certificate and
 * *out_equal=0 for a WRONG one (a numerator scaled by 2).
 *
 * The triples are constructed from the q-WZ equation r_n = 1 + R(X,qY)*r_k - R(X,Y):
 *   (1) R = 0, r_k = 1, r_n = 1 (the constant-summand q-WZ pair; certificate R=0).
 *   (2) R = Y/(X-Y), r_k = Y/X, r_n derived so the identity holds (a nontrivial cert).
 * Both are exact bivariate-Q[q]; the smoke checks the COMPLETE C verify (degree-bounded,
 * native), and that a wrong certificate is rejected.
 *
 * Build (WSL / POSIX):
 *   gcc -std=c11 -Wall -Wextra -Werror -pedantic -Ic/include
 *       c/test/test_srmech_q_wz_verify.c c/src/srmech_*.c -lm -o /tmp/qwz_smoke
 */

#include "srmech.h"

#include <assert.h>
#include <stdint.h>
#include <stdio.h>

static int g_fail = 0;
static int g_pass = 0;

#define CHECK(cond, msg) do { \
    if (cond) { g_pass++; } \
    else { g_fail++; printf("  FAIL: %s\n", (msg)); } \
} while (0)

/* ---- bigint pool ---- */
#define TCAP 96u
static uint32_t g_limbs[16384][TCAP];
static size_t g_used = 0u;

static void bset(srmech_bigint_t *b, int64_t v)
{
    assert(g_used < 16384u);
    b->limbs = g_limbs[g_used++];
    b->cap = TCAP; b->n = 0; b->sign = 0;
    srmech_bigint_set_i64(b, v);
}

/* A QBiPoly input in the flat bridge form (n/d q-runs Y-major-then-X, per-(Y,X)
 * qlen[], per-Y xlow[]/xcells[], ycells). We build it from a compact spec: a list of
 * (y, x, qdeg, coeff) integer monomials c * X^x * Y^y * q^qdeg. */
typedef struct qbi_in {
    srmech_bigint_t n[512], d[512];
    size_t qlen[64];
    int64_t xlow[16];
    size_t xcells[16];
    size_t ycells;
} qbi_in_t;

typedef struct mono { int y, x, qdeg, c; } mono_t;

/* Build a QBiPoly from a monomial list. The Y-window is 0..ymax; for each Y-cell the
 * X-window is its [xmin,xmax]; for each X-cell the q-run is 0..qmax of that cell. */
static void qbi_build(qbi_in_t *b, const mono_t *ms, size_t nm)
{
    int ymax = 0, dy, dx;
    size_t m;
    size_t cell = 0u, idx = 0u;
    for (m = 0u; m < nm; m++) { if (ms[m].y > ymax) { ymax = ms[m].y; } }
    b->ycells = (size_t)(ymax + 1);
    for (dy = 0; dy <= ymax; dy++) {
        int xmin = 1, xmax = -1, have = 0;
        for (m = 0u; m < nm; m++) {
            if (ms[m].y == dy) {
                if (!have || ms[m].x < xmin) { xmin = ms[m].x; }
                if (!have || ms[m].x > xmax) { xmax = ms[m].x; }
                have = 1;
            }
        }
        if (!have) { b->xlow[dy] = 0; b->xcells[dy] = 0u; continue; }
        b->xlow[dy] = xmin;
        b->xcells[dy] = (size_t)(xmax - xmin + 1);
        for (dx = xmin; dx <= xmax; dx++) {
            int qmax = -1, qd;
            for (m = 0u; m < nm; m++) {
                if (ms[m].y == dy && ms[m].x == dx && ms[m].qdeg > qmax) {
                    qmax = ms[m].qdeg;
                }
            }
            b->qlen[cell] = (size_t)(qmax + 1);
            for (qd = 0; qd <= qmax; qd++) {
                int cv = 0;
                for (m = 0u; m < nm; m++) {
                    if (ms[m].y == dy && ms[m].x == dx && ms[m].qdeg == qd) {
                        cv += ms[m].c;
                    }
                }
                bset(&b->n[idx], cv);
                bset(&b->d[idx], 1);
                idx++;
            }
            cell++;
        }
    }
}

static unsigned char g_ws[128u * 1024u * 1024u];

static int run_verify(qbi_in_t *an, qbi_in_t *ad, qbi_in_t *bn, qbi_in_t *bd,
                      qbi_in_t *xn, qbi_in_t *xd, int *eq)
{
    return (int)srmech_q_wz_verify(
        an->n, an->d, an->qlen, an->xlow, an->xcells, an->ycells,
        ad->n, ad->d, ad->qlen, ad->xlow, ad->xcells, ad->ycells,
        bn->n, bn->d, bn->qlen, bn->xlow, bn->xcells, bn->ycells,
        bd->n, bd->d, bd->qlen, bd->xlow, bd->xcells, bd->ycells,
        xn->n, xn->d, xn->qlen, xn->xlow, xn->xcells, xn->ycells,
        xd->n, xd->d, xd->qlen, xd->xlow, xd->xcells, xd->ycells,
        eq, g_ws, sizeof(g_ws));
}

int main(void)
{
    int eq = 0, rc;
    printf("srmech_q_wz_verify smoke test (rc57)\n");

    /* Case 1: the constant-summand q-WZ pair. r_n = 1, r_k = 1, R = 0.
     * The cleared identity holds trivially (both sides 0). */
    {
        qbi_in_t an, ad, bn, bd, xn, xd, xbad;
        g_used = 0u;
        { mono_t m[] = {{0,0,0,1}}; qbi_build(&an, m, 1); }      /* r_n num = 1 */
        { mono_t m[] = {{0,0,0,1}}; qbi_build(&ad, m, 1); }      /* r_n den = 1 */
        { mono_t m[] = {{0,0,0,1}}; qbi_build(&bn, m, 1); }      /* r_k num = 1 */
        { mono_t m[] = {{0,0,0,1}}; qbi_build(&bd, m, 1); }      /* r_k den = 1 */
        { mono_t m[] = {{0,0,0,0}}; qbi_build(&xn, m, 1); }      /* cert num = 0 */
        { mono_t m[] = {{0,0,0,1}}; qbi_build(&xd, m, 1); }      /* cert den = 1 */
        rc = run_verify(&an, &ad, &bn, &bd, &xn, &xd, &eq);
        CHECK(rc == SRMECH_OK, "case1 status OK");
        CHECK(eq == 1, "case1 constant-summand R=0 verifies (out_equal == 1)");
        /* a wrong cert R = Y (non-constant in Y) must NOT verify: for the constant
         * summand r_n=r_k=1, R(X,qY)-R(X,Y) = qY - Y != 0 = r_n - 1. (A CONSTANT cert
         * R=c is valid since R(X,qY)-R(X,Y)=0, so we pick a Y-dependent wrong one.) */
        { mono_t m[] = {{1,0,0,1}}; qbi_build(&xbad, m, 1); }    /* R = Y */
        rc = run_verify(&an, &ad, &bn, &bd, &xbad, &xd, &eq);
        CHECK(rc == SRMECH_OK, "case1 wrong-cert status OK");
        CHECK(eq == 0, "case1 WRONG certificate R=Y does NOT verify (out_equal == 0)");
    }

    /* Case 2: a nontrivial q-WZ triple. R = Y/(X-Y), r_k = Y/X.
     *   Xn = Y, Xd = X - Y; Bn = Y, Bd = X.
     *   sigma_y(Xn) = q*Y, sigma_y(Xd) = X - q*Y.
     *   r_n = 1 + R(X,qY)*r_k - R(X,Y) = (num)/(den), with
     *     den = sigma_y(Xd)*Bd*Xd = (X - qY)*X*(X-Y)
     *     num_rhs = sigma_y(Xn)*Bn*Xd - Xn*sigma_y(Xd)*Bd
     *             = qY*Y*(X-Y) - Y*(X-qY)*X
     *     An = num_rhs + den, Ad = den.
     * These are computed by hand below as integer-coefficient bivariate-q monomials.
     * Verified once by the Python pure path (the parity oracle); here the C must agree. */
    {
        qbi_in_t an, ad, bn, bd, xn, xd, xbad;
        g_used = 0u;
        /* Xn = Y : monomial (y=1,x=0,q=0,c=1) */
        { mono_t m[] = {{1,0,0,1}}; qbi_build(&xn, m, 1); }
        /* Xd = X - Y : (y=0,x=1,c=1), (y=1,x=0,c=-1) */
        { mono_t m[] = {{0,1,0,1},{1,0,0,-1}}; qbi_build(&xd, m, 2); }
        /* Bn = Y, Bd = X */
        { mono_t m[] = {{1,0,0,1}}; qbi_build(&bn, m, 1); }
        { mono_t m[] = {{0,1,0,1}}; qbi_build(&bd, m, 1); }
        /* den = (X - qY)*X*(X-Y). Expand:
         *   (X - qY)*X = X^2 - qXY
         *   *(X-Y) = X^3 - X^2 Y - qX^2 Y + qXY^2 = X^3 - (1+q)X^2 Y + qXY^2
         * Ad monomials: (y0,x3,q0,1), (y1,x2,q0,-1),(y1,x2,q1,-1), (y2,x1,q1,1) */
        { mono_t m[] = {{0,3,0,1},{1,2,0,-1},{1,2,1,-1},{2,1,1,1}};
          qbi_build(&ad, m, 4); }
        /* num_rhs = qY*Y*(X-Y) - Y*(X-qY)*X
         *   qY*Y*(X-Y) = qXY^2 - qY^3
         *   Y*(X-qY)*X = X^2 Y - qXY^2
         *   num_rhs = qXY^2 - qY^3 - X^2 Y + qXY^2 = -X^2 Y + 2qXY^2 - qY^3
         * An = num_rhs + den
         *   = X^3 - (1+q)X^2 Y + qXY^2  +  (-X^2 Y + 2qXY^2 - qY^3)
         *   = X^3 - (2+q)X^2 Y + 3qXY^2 - qY^3
         * An monomials:
         *   (y0,x3,q0,1)
         *   (y1,x2,q0,-2),(y1,x2,q1,-1)
         *   (y2,x1,q1,3)
         *   (y3,x0,q1,-1) */
        { mono_t m[] = {{0,3,0,1},{1,2,0,-2},{1,2,1,-1},{2,1,1,3},{3,0,1,-1}};
          qbi_build(&an, m, 5); }
        rc = run_verify(&an, &ad, &bn, &bd, &xn, &xd, &eq);
        CHECK(rc == SRMECH_OK, "case2 status OK");
        CHECK(eq == 1, "case2 R=Y/(X-Y) certificate verifies (out_equal == 1)");
        /* a wrong cert (Xn scaled by 2 -> 2Y) must NOT verify. */
        { mono_t m[] = {{1,0,0,2}}; qbi_build(&xbad, m, 1); }
        rc = run_verify(&an, &ad, &bn, &bd, &xbad, &xd, &eq);
        CHECK(rc == SRMECH_OK, "case2 wrong-cert status OK");
        CHECK(eq == 0, "case2 WRONG certificate 2Y does NOT verify (out_equal == 0)");
    }

    printf("\n%d passed, %d failed\n", g_pass, g_fail);
    return g_fail == 0 ? 0 : 1;
}
