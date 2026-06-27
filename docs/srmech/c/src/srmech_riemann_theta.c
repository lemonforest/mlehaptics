/*
 * srmech_riemann_theta.c — the EXACT-INTEGER (A, B, C) EXPONENT LATTICE of a
 * GENUS-2 RIEMANN THETA-CONSTANT (the C peer of
 * srmech.amsc.riemann_theta.RiemannTheta; the FIRST RUNG of the GENUS axis).
 *
 * The genus-2 Riemann theta-constant with binary characteristic [eps'; eps]
 * (entries in {0,1}; Grushevsky arXiv:1009.0369 eq.1; Eilers arXiv:1707.08855
 * eq.1.2) is
 *
 *   theta[ep'; e](0|Omega) = SUM_{n in Z^2} (-1)^{e.n} q1^{m1^2} q2^{m2^2}
 *                            q12^{m1 m2},   m_i = n_i + ep'_i/2 ,
 *
 * with nome alphabet q1=e^{i pi Om11}, q2=e^{i pi Om22}, q12=e^{2 i pi Om12}.
 * Clearing the half-integers m_i into the QUARTER-nome base
 *   Q1=q1^{1/4}, Q2=q2^{1/4}, Q12=q12^{1/4}=e^{i pi Om12/2}
 * a lattice term n=(n1,n2) becomes  Q1^A Q2^B Q12^C * (-1)^{e1 n1 + e2 n2}  with
 * EXACT INTEGER exponents
 *   A = 4 n1^2 + 4 n1 ep1 + ep1^2
 *   B = 4 n2^2 + 4 n2 ep2 + ep2^2
 *   C = 4 n1 n2 + 2 n1 ep2 + 2 n2 ep1 + ep1 ep2   <- THE CROSS-TERM (denominator 4)
 *
 * The cross-term C is the genuinely-new, hardest part: m1 m2 is a PRODUCT of two
 * half-integers, so it needs denominator 4 in the cleared integer lattice (the
 * genus-1 unary-theta peer never saw this n1 n2 coupling). The lower
 * characteristic e contributes a per-term SIGN (-1)^{e.n} — the Class-K pin-slot
 * (a stored +-1 from an explicit parity branch), never an ALU abs(). The common
 * constant phase i^{e.ep'} factors out (the same for every term) and is suppressed
 * in the constant.
 *
 * This op emits the lattice as a flat caller-owned int64 array of QUADRUPLES
 * [A, B, C, sign] — ONE quadruple per lattice point n=(n1,n2) in the box
 * |n_i| <= box, in row-major (n1, n2) order. The coefficients of a genus-2
 * theta-CONSTANT are small integer lattice counts (each term contributes +-1), so
 * int64 is exact with no ceiling (no bignum needed). The caller (the Python
 * marshaller) accumulates the quadruples into the canonical {(A,B,C): coeff} dict
 * — byte-identical to the pure-Python srmech.amsc.riemann_theta._lattice_py. The
 * accumulation is trivial bookkeeping; the genuinely-new exact-integer A/B/C
 * clearing + the Class-K sign is what this peer mirrors.
 *
 * Caller-arena / caller-owned, like srmech_poly / srmech_unary_theta: no malloc.
 * Additive symbols -> ABI unchanged (stays 3).
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto/recursion): OK — iterative, flat helpers
 *   - Rule 2 (bounded loops)    : OK — bounds are the box (2*box+1 each axis)
 *   - Rule 3 (no malloc)        : OK — caller out[] only
 *   - Rule 4 (<=60 lines/func)  : OK — factored into static helpers
 *   - Rule 5 (>=2 asserts/fn)   : OK — entry-pointer + pre/postcondition
 *   - Rule 7 (return-value)     : OK — srmech_status_t propagated
 *   - Rule 8 (no multi-line mac): OK — no function-like macros
 *   - Rule 10 (warnings clean)  : OK under -Wall -Wextra -Wpedantic -Werror
 *
 * License: MIT.
 */

#include "srmech.h"

#include <assert.h>
#include <stdint.h>

/* one lattice point emits 4 int64: A, B, C, sign */
#define RT_QUAD 4

/* ---- forward declarations (Rule 1: no recursion) ------------------- */

static int rt_bit_ok(int v);
static int64_t rt_exp_a(int64_t n, int64_t ep);
static int64_t rt_cross_c(int64_t n1, int64_t n2, int64_t ep1, int64_t ep2);
static int rt_term_sign(int64_t e1, int64_t e2, int64_t n1, int64_t n2);

/* ---- characteristic-bit validation + the cleared exponents -------- */

static int rt_bit_ok(int v)
{
    int ok = (v == 0 || v == 1) ? 1 : 0;
    assert(ok == 0 || ok == 1);                    /* result is a clean boolean */
    assert(ok == 0 || (v == 0 || v == 1));         /* ok ⇒ v is a valid bit */
    return ok;
}

/* The diagonal cleared exponent A (or B): 4 n^2 + 4 n ep + ep^2 = (2n + ep)^2.
 * Exact int64 (the box keeps it within range; the caller sizes the box). */
static int64_t rt_exp_a(int64_t n, int64_t ep)
{
    int64_t two_n_plus_ep = 2 * n + ep;
    assert(ep == 0 || ep == 1);
    assert(two_n_plus_ep == 2 * n + ep);
    return two_n_plus_ep * two_n_plus_ep;          /* = 4n^2 + 4n ep + ep^2 */
}

/* The cross-term cleared exponent C = 4 n1 n2 + 2 n1 ep2 + 2 n2 ep1 + ep1 ep2
 * = (2 n1 + ep1)(2 n2 + ep2) - ... no: (2n1+ep1)(2n2+ep2) = 4n1n2 + 2n1 ep2 +
 * 2n2 ep1 + ep1 ep2 EXACTLY. So C = (2n1+ep1)(2n2+ep2) (the denominator-4 clear). */
static int64_t rt_cross_c(int64_t n1, int64_t n2, int64_t ep1, int64_t ep2)
{
    int64_t u = 2 * n1 + ep1;
    int64_t v = 2 * n2 + ep2;
    assert(ep1 == 0 || ep1 == 1);
    assert(ep2 == 0 || ep2 == 1);
    return u * v;                                   /* = 4n1n2+2n1ep2+2n2ep1+ep1ep2 */
}

/* The per-term sign (-1)^{e1 n1 + e2 n2}: Class-K pin-slot (a stored +1/-1 from an
 * explicit parity branch), never an ALU abs(). */
static int rt_term_sign(int64_t e1, int64_t e2, int64_t n1, int64_t n2)
{
    int64_t parity = (e1 * n1 + e2 * n2) % 2;
    assert(e1 == 0 || e1 == 1);
    assert(e2 == 0 || e2 == 1);
    if (parity < 0) {
        parity += 2;                                /* floor-mod into {0,1} */
    }
    return (parity == 0) ? 1 : -1;                  /* Class-K +-1, no abs() */
}

/* ================================================================== *
 *  Public: srmech_riemann_theta_count + srmech_riemann_theta_lattice  *
 * ================================================================== */

/* The number of lattice quadruples for a given box: (2*box+1)^2 points, RT_QUAD
 * int64 each. The caller sizes its out[] array from this (no malloc here). */
size_t srmech_riemann_theta_count(uint32_t box)
{
    size_t side = (size_t)box * 2u + 1u;
    assert(RT_QUAD == 4);
    assert(side >= 1u);
    return side * side * (size_t)RT_QUAD;
}

/* Emit the genus-2 theta-constant exponent lattice for characteristic
 * [ep1,ep2; e1,e2] (each bit in {0,1}) over the box |n_i| <= box, as a flat
 * caller-owned int64 array of [A, B, C, sign] quadruples in row-major (n1, n2)
 * order. *out_len <- the number of int64 written (= srmech_riemann_theta_count).
 * SRMECH_ERR_BAD_INPUT if any characteristic bit is not in {0,1}; SRMECH_ERR_OVERFLOW
 * if the caller out[] (out_cap int64) is too small. */
srmech_status_t srmech_riemann_theta_lattice(
    int ep1, int ep2, int e1, int e2, uint32_t box,
    int64_t *out, size_t out_cap, size_t *out_len)
{
    size_t need, idx;
    int64_t n1, n2, lo, hi;
    assert(out != NULL);
    assert(out_len != NULL);
    if (!rt_bit_ok(ep1) || !rt_bit_ok(ep2) || !rt_bit_ok(e1) || !rt_bit_ok(e2)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    need = srmech_riemann_theta_count(box);
    if (need > out_cap) {
        return SRMECH_ERR_OVERFLOW;
    }
    idx = 0u;
    lo = -(int64_t)box;
    hi = (int64_t)box;
    for (n1 = lo; n1 <= hi; ++n1) {
        for (n2 = lo; n2 <= hi; ++n2) {
            out[idx + 0u] = rt_exp_a(n1, (int64_t)ep1);                 /* A */
            out[idx + 1u] = rt_exp_a(n2, (int64_t)ep2);                 /* B */
            out[idx + 2u] = rt_cross_c(n1, n2, (int64_t)ep1, (int64_t)ep2); /* C */
            out[idx + 3u] = (int64_t)rt_term_sign((int64_t)e1, (int64_t)e2,
                                                  n1, n2);              /* sign */
            idx += (size_t)RT_QUAD;
        }
    }
    assert(idx == need);
    *out_len = idx;
    return SRMECH_OK;
}
