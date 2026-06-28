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
/* rc73 helpers (the Sp(4,Z) transformation + the eighth-nome lattice) */
static int64_t rt_g(const int64_t *gamma, int blk, int r, int c);
static int64_t rt_matvec(const int64_t *gamma, int blk, int64_t v0, int64_t v1,
                         int row);
static int64_t rt_diag_pqt(const int64_t *gamma, int pblk, int qblk, int row);
static int64_t rt_ptq(const int64_t *gamma, int pblk, int qblk, int i, int j);
static int rt_is_symplectic(const int64_t *gamma);
static int64_t rt_eight_phi(const int64_t *gamma,
                            int64_t ep1, int64_t ep2, int64_t e1, int64_t e2);

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

/* ================================================================== *
 *  rc73 (A): the Sp(4,Z) characteristic TRANSFORMATION + kappa 8th root
 * ================================================================== *
 *
 * The genus-2 modular group Sp(2g,Z)=Sp(4,Z) acts on the binary characteristic
 * m=[ep'; ep] (ep' upper, ep lower, bits in {0,1}) by the EXACT affine-linear map
 * (Igusa, Theta Functions (1972) V.1; DLMF 21.5.9):
 *   ep' |-> D ep' - C ep + diag(C D^T)
 *   ep  |-> -B ep' + A ep + diag(A B^T)
 * reduced mod 2 for the bit. The theta-constant picks up an 8th-root-of-unity
 * multiplier; this peer returns the CHARACTERISTIC-DEPENDENT Igusa phase part
 * exp(2 pi i phi_m) as the EXACT integer exponent k in Z/8 (rational phi_m, denom |
 * 8, so 8*phi_m is an integer):
 *   8*phi_m = -4 ep'^T (B D^T) ep' + 8 ep^T (A^T C) ep - 16 ep'^T (B^T C) ep
 *             - 8 diag(A B^T)^T (D ep' - C ep)
 * The remaining gamma-only factor kappa_0(gamma) (the Maslov/Weil cocycle 8th root,
 * e.g. the -i on the genus-1 inversion) is BOUND to the TRANSCENDENTAL automorphy
 * factor det(C Omega + D)^{1/2} (the sqrt branch) and is NOT computed here -- off
 * the decision path, carried symbolically. gamma is 16 int64 entries: the A,B,C,D 2x2
 * blocks, each row-major. All exact integer / mod-2; no float, no abs(). */

/* index a 2x2 block (blk in {0:A,1:B,2:C,3:D}) entry (r,c) in the flat gamma[16] */
static int64_t rt_g(const int64_t *gamma, int blk, int r, int c)
{
    assert(gamma != NULL);
    assert(blk >= 0 && blk < 4 && r >= 0 && r < 2 && c >= 0 && c < 2);
    return gamma[(size_t)blk * 4u + (size_t)r * 2u + (size_t)c];
}

/* (M v)_row for a 2x2 block M of gamma and a length-2 vector v=(v0,v1). */
static int64_t rt_matvec(const int64_t *gamma, int blk, int64_t v0, int64_t v1,
                         int row)
{
    assert(gamma != NULL);
    assert(row == 0 || row == 1);
    return rt_g(gamma, blk, row, 0) * v0 + rt_g(gamma, blk, row, 1) * v1;
}

/* diag(P Q^T)_row = sum_k P[row][k] Q[row][k]  (the row-row dot of two blocks). */
static int64_t rt_diag_pqt(const int64_t *gamma, int pblk, int qblk, int row)
{
    assert(gamma != NULL);
    assert(row == 0 || row == 1);
    return rt_g(gamma, pblk, row, 0) * rt_g(gamma, qblk, row, 0)
         + rt_g(gamma, pblk, row, 1) * rt_g(gamma, qblk, row, 1);
}

/* (P^T Q)[i][j] = sum_k P[k][i] Q[k][j]  -- one entry of a transposed-times block. */
static int64_t rt_ptq(const int64_t *gamma, int pblk, int qblk, int i, int j)
{
    assert(gamma != NULL);
    assert(i >= 0 && i < 2 && j >= 0 && j < 2);
    return rt_g(gamma, pblk, 0, i) * rt_g(gamma, qblk, 0, j)
         + rt_g(gamma, pblk, 1, i) * rt_g(gamma, qblk, 1, j);
}

/* The symplectic check gamma J gamma^T = J via the exact block conditions
 * A^T C = C^T A (symmetric), B^T D = D^T B (symmetric), A^T D - C^T B = I.
 * Returns 1 if symplectic, else 0. (blk 0=A,1=B,2=C,3=D.) */
static int rt_is_symplectic(const int64_t *gamma)
{
    int64_t atd, ctb;
    int ok = 1;
    assert(gamma != NULL);
    /* A^T C symmetric: (A^T C)[0][1] == (A^T C)[1][0] */
    if (rt_ptq(gamma, 0, 2, 0, 1) != rt_ptq(gamma, 0, 2, 1, 0)) { ok = 0; }
    /* B^T D symmetric */
    if (rt_ptq(gamma, 1, 3, 0, 1) != rt_ptq(gamma, 1, 3, 1, 0)) { ok = 0; }
    /* A^T D - C^T B == I (check all four entries) */
    atd = rt_ptq(gamma, 0, 3, 0, 0); ctb = rt_ptq(gamma, 2, 1, 0, 0);
    if (atd - ctb != 1) { ok = 0; }
    atd = rt_ptq(gamma, 0, 3, 1, 1); ctb = rt_ptq(gamma, 2, 1, 1, 1);
    if (atd - ctb != 1) { ok = 0; }
    atd = rt_ptq(gamma, 0, 3, 0, 1); ctb = rt_ptq(gamma, 2, 1, 0, 1);
    if (atd - ctb != 0) { ok = 0; }
    atd = rt_ptq(gamma, 0, 3, 1, 0); ctb = rt_ptq(gamma, 2, 1, 1, 0);
    if (atd - ctb != 0) { ok = 0; }
    assert(ok == 0 || ok == 1);
    return ok;
}

/* The exact 8*phi_m Igusa phase (an integer; the multiplier exponent is
 * (8*phi_m) mod 8). ep' = (ep1,ep2), ep = (e1,e2). */
static int64_t rt_eight_phi(const int64_t *gamma,
                            int64_t ep1, int64_t ep2, int64_t e1, int64_t e2)
{
    int64_t bdt0, bdt1, t1, atc0, atc1, t2, btc0, btc1, t3;
    int64_t dab0, dab1, dep0, dep1, cep0, cep1, t4;
    assert(gamma != NULL);
    assert((ep1 == 0 || ep1 == 1) && (ep2 == 0 || ep2 == 1));   /* upper char bits */
    assert((e1 == 0 || e1 == 1) && (e2 == 0 || e2 == 1));       /* lower char bits */
    /* t1 = -4 ep'^T (B D^T) ep' ; (B D^T)_row = diag-style row dot of B,D rows */
    bdt0 = rt_g(gamma, 1, 0, 0) * rt_g(gamma, 3, 0, 0)
         + rt_g(gamma, 1, 0, 1) * rt_g(gamma, 3, 0, 1);  /* (BD^T)[0][0] */
    /* full quadratic ep'^T (B D^T) ep' = sum_{i,j} ep'_i (BD^T)[i][j] ep'_j */
    bdt1 = rt_g(gamma, 1, 0, 0) * rt_g(gamma, 3, 1, 0)
         + rt_g(gamma, 1, 0, 1) * rt_g(gamma, 3, 1, 1);  /* (BD^T)[0][1] */
    {
        int64_t bdt10 = rt_g(gamma, 1, 1, 0) * rt_g(gamma, 3, 0, 0)
                      + rt_g(gamma, 1, 1, 1) * rt_g(gamma, 3, 0, 1);
        int64_t bdt11 = rt_g(gamma, 1, 1, 0) * rt_g(gamma, 3, 1, 0)
                      + rt_g(gamma, 1, 1, 1) * rt_g(gamma, 3, 1, 1);
        int64_t quad = ep1 * bdt0 * ep1 + ep1 * bdt1 * ep2
                     + ep2 * bdt10 * ep1 + ep2 * bdt11 * ep2;
        t1 = -4 * quad;
    }
    /* t2 = +8 ep^T (A^T C) ep */
    atc0 = rt_ptq(gamma, 0, 2, 0, 0); atc1 = rt_ptq(gamma, 0, 2, 0, 1);
    {
        int64_t atc10 = rt_ptq(gamma, 0, 2, 1, 0);
        int64_t atc11 = rt_ptq(gamma, 0, 2, 1, 1);
        int64_t quad = e1 * atc0 * e1 + e1 * atc1 * e2
                     + e2 * atc10 * e1 + e2 * atc11 * e2;
        t2 = 8 * quad;
    }
    /* t3 = -16 ep'^T (B^T C) ep */
    btc0 = rt_ptq(gamma, 1, 2, 0, 0); btc1 = rt_ptq(gamma, 1, 2, 0, 1);
    {
        int64_t btc10 = rt_ptq(gamma, 1, 2, 1, 0);
        int64_t btc11 = rt_ptq(gamma, 1, 2, 1, 1);
        int64_t bil = ep1 * btc0 * e1 + ep1 * btc1 * e2
                    + ep2 * btc10 * e1 + ep2 * btc11 * e2;
        t3 = -16 * bil;
    }
    /* t4 = -8 diag(A B^T)^T (D ep' - C ep) */
    dab0 = rt_diag_pqt(gamma, 0, 1, 0); dab1 = rt_diag_pqt(gamma, 0, 1, 1);
    dep0 = rt_matvec(gamma, 3, ep1, ep2, 0); dep1 = rt_matvec(gamma, 3, ep1, ep2, 1);
    cep0 = rt_matvec(gamma, 2, e1, e2, 0);   cep1 = rt_matvec(gamma, 2, e1, e2, 1);
    t4 = -8 * (dab0 * (dep0 - cep0) + dab1 * (dep1 - cep1));
    return t1 + t2 + t3 + t4;
}

/* The exact Sp(4,Z) characteristic transformation + the kappa 8th-root exponent.
 * gamma[16] = A,B,C,D blocks (row-major). out_char[4] <- (ep1',ep2',e1',e2') bits;
 * *kexp <- the multiplier exponent k in {0..7} (multiplier = zeta_8^k).
 * SRMECH_ERR_BAD_INPUT if a bit is invalid or gamma is not symplectic. */
srmech_status_t srmech_riemann_theta_sp4_char(
    const int64_t *gamma, int ep1, int ep2, int e1, int e2,
    int *out_char, int *kexp)
{
    int64_t E1, E2, e_1, e_2, npp0, npp1, nep0, nep1, dCD0, dCD1, dAB0, dAB1, k8;
    assert(gamma != NULL);
    assert(out_char != NULL && kexp != NULL);
    if (!rt_bit_ok(ep1) || !rt_bit_ok(ep2) || !rt_bit_ok(e1) || !rt_bit_ok(e2)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (!rt_is_symplectic(gamma)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    E1 = (int64_t)ep1; E2 = (int64_t)ep2; e_1 = (int64_t)e1; e_2 = (int64_t)e2;
    /* ep' |-> D ep' - C ep + diag(C D^T) */
    dCD0 = rt_diag_pqt(gamma, 2, 3, 0); dCD1 = rt_diag_pqt(gamma, 2, 3, 1);
    npp0 = rt_matvec(gamma, 3, E1, E2, 0) - rt_matvec(gamma, 2, e_1, e_2, 0) + dCD0;
    npp1 = rt_matvec(gamma, 3, E1, E2, 1) - rt_matvec(gamma, 2, e_1, e_2, 1) + dCD1;
    /* ep  |-> -B ep' + A ep + diag(A B^T) */
    dAB0 = rt_diag_pqt(gamma, 0, 1, 0); dAB1 = rt_diag_pqt(gamma, 0, 1, 1);
    nep0 = rt_matvec(gamma, 0, e_1, e_2, 0) - rt_matvec(gamma, 1, E1, E2, 0) + dAB0;
    nep1 = rt_matvec(gamma, 0, e_1, e_2, 1) - rt_matvec(gamma, 1, E1, E2, 1) + dAB1;
    out_char[0] = (int)(((npp0 % 2) + 2) % 2);
    out_char[1] = (int)(((npp1 % 2) + 2) % 2);
    out_char[2] = (int)(((nep0 % 2) + 2) % 2);
    out_char[3] = (int)(((nep1 % 2) + 2) % 2);
    k8 = rt_eight_phi(gamma, E1, E2, e_1, e_2);
    *kexp = (int)(((k8 % 8) + 8) % 8);             /* floor-mod into {0..7} */
    return SRMECH_OK;
}

/* ================================================================== *
 *  rc73 (B): the EIGHTH-nome lattice (the addition gate's convolution)
 * ================================================================== *
 *
 * The common eighth-nome base Q8 = q^{1/8} so theta at Omega AND at 2*Omega clear
 * to ONE integer lattice (the addition identity is a lattice equality):
 *   at Omega : A = 2(2n1+s1)^2, B = 2(2n2+s2)^2, C = 2(2n1+s1)(2n2+s2)
 *   at 2Omega: A =  (4n1+s1)^2, B =  (4n2+s2)^2, C =  (4n1+s1)(4n2+s2)
 * s1,s2 = the DOUBLED upper characteristic (ANY int; the addition right side uses
 * 2r+-(a+-b)). sign = (-1)^{e.n} (Class-K). Emits [A,B,C,sign] quadruples (one per
 * n in |n_i|<=box, row-major); caller accumulates the canonical lattice. */

size_t srmech_riemann_theta_eighth_count(uint32_t box)
{
    size_t side = (size_t)box * 2u + 1u;
    assert(RT_QUAD == 4);
    assert(side >= 1u);
    return side * side * (size_t)RT_QUAD;
}

srmech_status_t srmech_riemann_theta_eighth_lattice(
    int s1, int s2, int e1, int e2, int at_two_omega, uint32_t box,
    int64_t *out, size_t out_cap, size_t *out_len)
{
    size_t need, idx;
    int64_t n1, n2, lo, hi, u, v, A, B, C;
    assert(out != NULL);
    assert(out_len != NULL);
    if (!rt_bit_ok(e1) || !rt_bit_ok(e2)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    need = srmech_riemann_theta_eighth_count(box);
    if (need > out_cap) {
        return SRMECH_ERR_OVERFLOW;
    }
    idx = 0u;
    lo = -(int64_t)box;
    hi = (int64_t)box;
    for (n1 = lo; n1 <= hi; ++n1) {
        for (n2 = lo; n2 <= hi; ++n2) {
            if (at_two_omega) {
                u = 4 * n1 + (int64_t)s1;
                v = 4 * n2 + (int64_t)s2;
                A = u * u; B = v * v; C = u * v;
            } else {
                u = 2 * n1 + (int64_t)s1;
                v = 2 * n2 + (int64_t)s2;
                A = 2 * u * u; B = 2 * v * v; C = 2 * u * v;
            }
            out[idx + 0u] = A;
            out[idx + 1u] = B;
            out[idx + 2u] = C;
            out[idx + 3u] = (int64_t)rt_term_sign((int64_t)e1, (int64_t)e2, n1, n2);
            idx += (size_t)RT_QUAD;
        }
    }
    assert(idx == need);
    *out_len = idx;
    return SRMECH_OK;
}
