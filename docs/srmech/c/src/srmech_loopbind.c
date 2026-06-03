/*
 * srmech_loopbind.c — C parity for the octonion "loop-bind" Moufang
 * family (MS#21 v0.7.0; the dim-8 octonion product + companions).
 *
 * Closes the C/Python parity gap for the loop-bind family the MS#21 arc
 * hand-rolled in Python (srmech/amsc/hdc.py): the octonion
 * (Cayley-Dickson, dim 8) product loop_bind, the conjugate loop_conj,
 * the Moufang inverse loop_inv, the 7-D cross product
 * cross7 = Im(loop_bind), and the G2 associative calibration 3-form
 * g2_three_form = <x, cross7(y, z)>. The HD block variants
 * (loop_bind_hd, loop_unbind_hd, ...) inherit native acceleration for
 * FREE: their Python wrappers loop over 8-blocks calling the per-block
 * loop_bind / loop_conj, which dispatch to the symbols here.
 *
 * THE PRODUCT. An octonion is a pair of quaternions (a, b); the
 * Cayley-Dickson product, matching srmech.amsc.hdc._loop_bind_raw:
 *
 *     (a, b)(c, d) = (a c - conj(d) b,  d a + b conj(c))
 *
 * where the sub-products are quaternion (dim 4), themselves built from
 * complex (dim 2), themselves real. We UNROLL this fixed three-level
 * hierarchy (real -> complex -> quaternion -> octonion) as a bounded
 * call DAG — NOT recursion (JPL Rule 1): a finite set of helpers, none
 * self-referential. The scalar base case has conj == identity, so the
 * complex helper srmech_loop__mul2 is bit-exact with the Python at n==1.
 *
 * HONEST CASCADE SHAPE. loop_bind is Class M (bind) with the Class-C
 * (4:3)|(3:4) ordering; its non-associativity is the Class-K associator
 * residue. NO new privileged primitive; NO new class. No abs() — the
 * Class-K sign lives in the conjugate's imaginary index-flip, never an
 * absolute value.
 *
 * THREAD/STATE. Pure functions over caller buffers; `out` MUST NOT alias
 * the inputs. No shared static state; reentrant.
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto / recursion): early returns; fixed call DAG.
 *   - Rule 2 (bounded loops)       : all loops bounded by the dim-8 carrier.
 *   - Rule 3 (no malloc)           : caller buffers + fixed-size locals.
 *   - Rule 4 (<=60 lines/func)     : one helper per Cayley-Dickson level.
 *   - Rule 5 (>=2 asserts/fn)      : pointer / dimension pre-conditions.
 *   - Rule 7 (return-value)        : srmech_status_t throughout.
 *   - Rule 10 (warnings clean)     : -Wall -Wextra -Wpedantic -Werror / /WX.
 *
 * ABI: new symbols only — SRMECH_ABI_VERSION stays 3 (additive).
 *
 * License: GPL-3.0-or-later.
 */

#include "srmech.h"

#include <assert.h>
#include <stddef.h>

/* The octonion / k=7 carrier dimension (division holds at dim <= 8). */
#define SRMECH_LOOP_DIM ((size_t)8)

/* Complex (dim-2) product, the Cayley-Dickson level above the reals:
 *   (x0,x1)(y0,y1) = (x0 y0 - y1 x1,  y1 x0 + x1 y0)
 * Bit-exact with _loop_bind_raw at n==1 (scalar conj == identity). */
static void srmech_loop__mul2(const double *x, const double *y, double *out)
{
    assert(x != NULL && y != NULL);
    assert(out != NULL);
    out[0] = x[0] * y[0] - y[1] * x[1];
    out[1] = y[1] * x[0] + x[1] * y[0];
}

/* Quaternion (dim-4) product via complex pairs a=x[0:2], b=x[2:4],
 * c=y[0:2], d=y[2:4]:  (a c - conj(d) b,  d a + b conj(c)),  with
 * conj2(p) = (p0, -p1). A fixed two-call complex level (no recursion). */
static void srmech_loop__mul4(const double *x, const double *y, double *out)
{
    assert(x != NULL && y != NULL);
    assert(out != NULL);
    const double dconj[2] = { y[2], -y[3] };
    const double cconj[2] = { y[0], -y[1] };
    double ac[2], db[2], da[2], bc[2];
    srmech_loop__mul2(&x[0], &y[0], ac);   /* a c       */
    srmech_loop__mul2(dconj, &x[2], db);   /* conj(d) b */
    srmech_loop__mul2(&y[2], &x[0], da);   /* d a       */
    srmech_loop__mul2(&x[2], cconj, bc);   /* b conj(c) */
    out[0] = ac[0] - db[0];
    out[1] = ac[1] - db[1];
    out[2] = da[0] + bc[0];
    out[3] = da[1] + bc[1];
}

/* Octonion (dim-8) product via quaternion pairs a=x[0:4], b=x[4:8],
 * c=y[0:4], d=y[4:8]:  (a c - conj(d) b,  d a + b conj(c)),  with
 * conj4(p) = (p0, -p1, -p2, -p3). THE shipped loop_bind octonion. */
static void srmech_loop__mul8(const double *x, const double *y, double *out)
{
    assert(x != NULL && y != NULL);
    assert(out != NULL);
    const double dconj[4] = { y[4], -y[5], -y[6], -y[7] };
    const double cconj[4] = { y[0], -y[1], -y[2], -y[3] };
    double ac[4], db[4], da[4], bc[4];
    srmech_loop__mul4(&x[0], &y[0], ac);   /* a c       */
    srmech_loop__mul4(dconj, &x[4], db);   /* conj(d) b */
    srmech_loop__mul4(&y[4], &x[0], da);   /* d a       */
    srmech_loop__mul4(&x[4], cconj, bc);   /* b conj(c) */
    for (size_t i = 0; i < 4; ++i) {
        out[i] = ac[i] - db[i];
        out[i + 4] = da[i] + bc[i];
    }
}

srmech_status_t srmech_loop_bind_f64(
    const double *x, const double *y, size_t n, double *out)
{
    if (x == NULL || y == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n != SRMECH_LOOP_DIM) {
        return SRMECH_ERR_BAD_INPUT;
    }
    assert(x != NULL && y != NULL && out != NULL);
    assert(n == SRMECH_LOOP_DIM);
    srmech_loop__mul8(x, y, out);
    return SRMECH_OK;
}

srmech_status_t srmech_loop_conj_f64(const double *x, size_t n, double *out)
{
    if (x == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n != SRMECH_LOOP_DIM) {
        return SRMECH_ERR_BAD_INPUT;
    }
    assert(x != NULL && out != NULL);
    assert(n == SRMECH_LOOP_DIM);
    out[0] = x[0];
    for (size_t i = 1; i < SRMECH_LOOP_DIM; ++i) {
        out[i] = -x[i];
    }
    return SRMECH_OK;
}

srmech_status_t srmech_loop_inv_f64(const double *x, size_t n, double *out)
{
    if (x == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n != SRMECH_LOOP_DIM) {
        return SRMECH_ERR_BAD_INPUT;
    }
    assert(x != NULL && out != NULL);
    assert(n == SRMECH_LOOP_DIM);
    double nsq = 0.0;
    for (size_t i = 0; i < SRMECH_LOOP_DIM; ++i) {
        nsq += x[i] * x[i];
    }
    if (nsq == 0.0) {
        return SRMECH_ERR_BAD_INPUT;  /* zero vector has no Moufang inverse */
    }
    out[0] = x[0] / nsq;
    for (size_t i = 1; i < SRMECH_LOOP_DIM; ++i) {
        out[i] = -x[i] / nsq;
    }
    return SRMECH_OK;
}

srmech_status_t srmech_cross7_f64(
    const double *x, const double *y, size_t n, double *out)
{
    if (x == NULL || y == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n != SRMECH_LOOP_DIM) {
        return SRMECH_ERR_BAD_INPUT;
    }
    assert(x != NULL && y != NULL && out != NULL);
    assert(n == SRMECH_LOOP_DIM);
    srmech_loop__mul8(x, y, out);
    out[0] = 0.0;  /* Im: drop the e0 real anchor (Class-C imaginary part) */
    return SRMECH_OK;
}

srmech_status_t srmech_g2_three_form_f64(
    const double *x, const double *y, const double *z, size_t n, double *out)
{
    if (x == NULL || y == NULL || z == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n != SRMECH_LOOP_DIM) {
        return SRMECH_ERR_BAD_INPUT;
    }
    assert(x != NULL && y != NULL && z != NULL);
    assert(out != NULL && n == SRMECH_LOOP_DIM);
    double yz[SRMECH_LOOP_DIM];
    srmech_loop__mul8(y, z, yz);
    yz[0] = 0.0;  /* cross7(y, z) = Im(y z) */
    double acc = 0.0;
    for (size_t i = 0; i < SRMECH_LOOP_DIM; ++i) {
        acc += x[i] * yz[i];
    }
    *out = acc;
    return SRMECH_OK;
}

/* The Class-K associator residue (a·b)·c − a·(b·c) — zero in an associative
 * (quaternionic / Fano-line) region, nonzero outside (the (4:3)|(3:4)
 * boundary). 8 doubles in each of a,b,c; 8 doubles out. Two fixed triple-
 * products via the static octonion product (no recursion). */
srmech_status_t srmech_loop_associator_f64(
    const double *a, const double *b, const double *c, size_t n, double *out)
{
    if (a == NULL || b == NULL || c == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n != SRMECH_LOOP_DIM) {
        return SRMECH_ERR_BAD_INPUT;
    }
    assert(a != NULL && b != NULL && c != NULL);
    assert(out != NULL && n == SRMECH_LOOP_DIM);
    double ab[SRMECH_LOOP_DIM], bc[SRMECH_LOOP_DIM];
    double ab_c[SRMECH_LOOP_DIM], a_bc[SRMECH_LOOP_DIM];
    srmech_loop__mul8(a, b, ab);     /* (a·b)   */
    srmech_loop__mul8(ab, c, ab_c);  /* (a·b)·c */
    srmech_loop__mul8(b, c, bc);     /* (b·c)   */
    srmech_loop__mul8(a, bc, a_bc);  /* a·(b·c) */
    for (size_t i = 0; i < SRMECH_LOOP_DIM; ++i) {
        out[i] = ab_c[i] - a_bc[i];
    }
    return SRMECH_OK;
}

/* Left-multiplication operator matrix L_a: column k = a·e_k (the (4:3)
 * ordering). `out` is n*n doubles, row-major, out[i*n + k] = (a·e_k)_i —
 * byte-matching numpy ``column_stack`` of the per-basis binds. */
srmech_status_t srmech_loop_left_op_f64(const double *a, size_t n, double *out)
{
    if (a == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n != SRMECH_LOOP_DIM) {
        return SRMECH_ERR_BAD_INPUT;
    }
    assert(a != NULL && out != NULL);
    assert(n == SRMECH_LOOP_DIM);
    for (size_t k = 0; k < SRMECH_LOOP_DIM; ++k) {
        double e[SRMECH_LOOP_DIM] = {0.0};
        double col[SRMECH_LOOP_DIM];
        e[k] = 1.0;
        srmech_loop__mul8(a, e, col);  /* a · e_k */
        for (size_t i = 0; i < SRMECH_LOOP_DIM; ++i) {
            out[i * SRMECH_LOOP_DIM + k] = col[i];
        }
    }
    return SRMECH_OK;
}

/* Right-multiplication operator matrix R_a: column k = e_k·a (the (3:4)
 * mirror ordering). `out` is n*n doubles, row-major, out[i*n + k] =
 * (e_k·a)_i — byte-matching numpy ``column_stack`` of the per-basis binds. */
srmech_status_t srmech_loop_right_op_f64(const double *a, size_t n, double *out)
{
    if (a == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n != SRMECH_LOOP_DIM) {
        return SRMECH_ERR_BAD_INPUT;
    }
    assert(a != NULL && out != NULL);
    assert(n == SRMECH_LOOP_DIM);
    for (size_t k = 0; k < SRMECH_LOOP_DIM; ++k) {
        double e[SRMECH_LOOP_DIM] = {0.0};
        double col[SRMECH_LOOP_DIM];
        e[k] = 1.0;
        srmech_loop__mul8(e, a, col);  /* e_k · a */
        for (size_t i = 0; i < SRMECH_LOOP_DIM; ++i) {
            out[i * SRMECH_LOOP_DIM + k] = col[i];
        }
    }
    return SRMECH_OK;
}
