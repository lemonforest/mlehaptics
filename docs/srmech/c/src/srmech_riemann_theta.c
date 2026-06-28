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

/* ================================================================== *
 *  rc74: the GENUS-AXIS CAPSTONE — the Eilers genus-2 ETA-MAP
 * ================================================================== *
 *
 * The Eilers genus-2 eta-map (arXiv:1707.08855, eq 4.4): the (mod-2) characteristic
 *   [eps(I)] = SUM_{k in I} [A_k] - [K_inf]   (mod 2)
 * of a branch-point index set I (subset of {1..6}, e6 = inf). [A_k] are the
 * Abelian-image characteristics (Eilers eq 4.2) and [K_inf] = [A_2]+[A_4]+[A_6]
 * (eq 4.3, the vector of Riemann constants). Pure GF(2) linear algebra: each
 * characteristic is a 4-bit vector (ep1,ep2,e1,e2), addition is XOR (mod 2), and
 * subtraction == addition (the group (Z/2)^4 is its own inverse) so NO sign branch
 * / NO abs() is needed. The single-index sets give the 6 ODD characteristics; the
 * 10 pairs of finite indices {1..5} give the 10 EVEN theta-nulls. */

/* [A_k] for k=1..6 (e6=inf), as the 4 bits (ep1,ep2,e1,e2) — Eilers eq (4.2). Row
 * index is k-1; columns are ep1,ep2,e1,e2. */
static const int RT_EILERS_A[6][4] = {
    {1, 0, 0, 0},   /* [A_1] = ((1,0),(0,0)) */
    {1, 0, 1, 0},   /* [A_2] = ((1,0),(1,0)) */
    {0, 1, 1, 0},   /* [A_3] = ((0,1),(1,0)) */
    {0, 1, 1, 1},   /* [A_4] = ((0,1),(1,1)) */
    {0, 0, 1, 1},   /* [A_5] = ((0,0),(1,1)) */
    {0, 0, 0, 0},   /* [A_6] = ((0,0),(0,0)) */
};

/* Accumulate [A_k] (1-based index k in {1..6}) into acc[4] (mod 2). Returns 1 on a
 * valid index, 0 otherwise. */
static int rt_eta_accumulate(int k, int *acc)
{
    int row;
    int col;
    assert(acc != NULL);
    if (k < 1 || k > 6) {
        return 0;
    }
    row = k - 1;
    for (col = 0; col < 4; ++col) {
        acc[col] = (acc[col] + RT_EILERS_A[row][col]) % 2;   /* GF(2) add (XOR) */
    }
    assert(acc[0] == 0 || acc[0] == 1);
    assert(acc[3] == 0 || acc[3] == 1);
    return 1;
}

/* The Eilers genus-2 eta-map: branch-point index set -> characteristic. indices[]
 * holds n_idx 1-based branch-point indices (each in {1..6}); out_char[4] <-
 * (ep1,ep2,e1,e2) the (mod-2) bits of [eps(I)] = SUM_{k in I} [A_k] - [K_inf].
 * SRMECH_ERR_BAD_INPUT on a NULL pointer or an out-of-range index. */
srmech_status_t srmech_riemann_theta_eta_char(
    const int *indices, size_t n_idx, int *out_char)
{
    int acc[4] = {0, 0, 0, 0};
    size_t i;
    assert(out_char != NULL);
    assert(indices != NULL || n_idx == 0u);
    if (out_char == NULL) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (indices == NULL && n_idx != 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    for (i = 0u; i < n_idx; ++i) {
        if (!rt_eta_accumulate(indices[i], acc)) {
            return SRMECH_ERR_BAD_INPUT;
        }
    }
    /* - [K_inf] = + [K_inf] (mod 2): [K_inf] = [A_2]+[A_4]+[A_6]. */
    (void)rt_eta_accumulate(2, acc);
    (void)rt_eta_accumulate(4, acc);
    (void)rt_eta_accumulate(6, acc);
    out_char[0] = acc[0];
    out_char[1] = acc[1];
    out_char[2] = acc[2];
    out_char[3] = acc[3];
    return SRMECH_OK;
}

/* ================================================================== *
 *  rc75: the GENUS-3 EXACT-INTEGER EXPONENT LATTICE (the next genus rung)
 * ================================================================== *
 *
 * The genus-3 Riemann theta-constant with binary characteristic [ep'; e]
 * (six bits in {0,1}; Grushevsky arXiv:1009.0369 eq.1, the genus-3 g=3
 * specialization) is the lattice sum over n in Z^3 of
 *   (-1)^{e.n} q1^{m1^2} q2^{m2^2} q3^{m3^2}
 *            q12^{m1 m2} q13^{m1 m3} q23^{m2 m3},   m_i = n_i + ep'_i/2 ,
 * with nome alphabet q_i=e^{i pi Om_ii}, q_ij=e^{2 i pi Om_ij}. Clearing the
 * half-integers m_i into the QUARTER-nome base Q_i=q_i^{1/4}, Q_ij=q_ij^{1/4} a
 * lattice term n=(n1,n2,n3) becomes
 *   Q1^A1 Q2^A2 Q3^A3 Q12^C12 Q13^C13 Q23^C23 * (-1)^{e.n}
 * with EXACT INTEGER exponents A_i=(2n_i+ep_i)^2 and the THREE cross-terms
 *   C_ij = (2n_i+ep_i)(2n_j+ep_j)   (each a denominator-4 clearing of the m_i m_j
 * product; the genus-2 peer had ONE cross-term, genus 3 has THREE -- the hardest
 * part). The lower characteristic e gives the per-term sign (-1)^{e.n} -- the
 * Class-K pin-slot (a stored +-1 from an explicit parity branch), never abs().
 *
 * This op emits the lattice as a flat caller-owned int64 array of SEXTUPLE+sign
 * SEPTUPLES [A1,A2,A3,C12,C13,C23,sign] -- ONE septuple per lattice point n in the
 * box |n_i| <= box, in row-major (n1,n2,n3) order. The genus-3 theta-CONSTANT
 * coefficients are small integer lattice counts (each term contributes +-1), so
 * int64 is exact with no ceiling (no bignum). The caller accumulates the septuples
 * into the canonical {(A1,A2,A3,C12,C13,C23): coeff} dict -- byte-identical to the
 * pure-Python srmech.amsc.riemann_theta.RiemannThetaG3._lattice_py.
 *
 * Caller-arena / caller-owned (like the genus-2 peer); no malloc. Additive symbol
 * -> ABI unchanged (stays 3). */

/* one genus-3 lattice point emits 7 int64: A1,A2,A3,C12,C13,C23,sign */
#define RT3_SEPT 7

/* The number of int64 a box needs for the genus-3 lattice: (2*box+1)^3 points,
 * RT3_SEPT int64 each. The caller sizes its out[] from this (no malloc here). */
size_t srmech_riemann_theta_g3_count(uint32_t box)
{
    size_t side = (size_t)box * 2u + 1u;
    assert(RT3_SEPT == 7);
    assert(side >= 1u);
    return side * side * side * (size_t)RT3_SEPT;
}

/* The per-term genus-3 sign (-1)^{e1 n1 + e2 n2 + e3 n3}: Class-K pin-slot (a stored
 * +1/-1 from an explicit parity branch), never an ALU abs(). */
static int rt3_term_sign(int64_t e1, int64_t e2, int64_t e3,
                         int64_t n1, int64_t n2, int64_t n3)
{
    int64_t parity = (e1 * n1 + e2 * n2 + e3 * n3) % 2;
    assert((e1 == 0 || e1 == 1) && (e2 == 0 || e2 == 1));
    assert(e3 == 0 || e3 == 1);
    if (parity < 0) {
        parity += 2;                                /* floor-mod into {0,1} */
    }
    return (parity == 0) ? 1 : -1;                  /* Class-K +-1, no abs() */
}

/* Emit the genus-3 theta-constant exponent lattice for characteristic
 * [ep1,ep2,ep3; e1,e2,e3] (each bit in {0,1}) over the box |n_i| <= box, as a flat
 * caller-owned int64 array of [A1,A2,A3,C12,C13,C23,sign] septuples in row-major
 * (n1,n2,n3) order. *out_len <- the number of int64 written (= the g3 count).
 * SRMECH_ERR_BAD_INPUT if any characteristic bit is not in {0,1}; SRMECH_ERR_OVERFLOW
 * if the caller out[] (out_cap int64) is too small. */
srmech_status_t srmech_riemann_theta_g3_lattice(
    int ep1, int ep2, int ep3, int e1, int e2, int e3, uint32_t box,
    int64_t *out, size_t out_cap, size_t *out_len)
{
    size_t need, idx;
    int64_t n1, n2, n3, lo, hi, u1, u2, u3;
    assert(out != NULL);
    assert(out_len != NULL);
    if (!rt_bit_ok(ep1) || !rt_bit_ok(ep2) || !rt_bit_ok(ep3)
            || !rt_bit_ok(e1) || !rt_bit_ok(e2) || !rt_bit_ok(e3)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    need = srmech_riemann_theta_g3_count(box);
    if (need > out_cap) {
        return SRMECH_ERR_OVERFLOW;
    }
    idx = 0u;
    lo = -(int64_t)box;
    hi = (int64_t)box;
    for (n1 = lo; n1 <= hi; ++n1) {
        u1 = 2 * n1 + (int64_t)ep1;
        for (n2 = lo; n2 <= hi; ++n2) {
            u2 = 2 * n2 + (int64_t)ep2;
            for (n3 = lo; n3 <= hi; ++n3) {
                u3 = 2 * n3 + (int64_t)ep3;
                out[idx + 0u] = u1 * u1;                /* A1 */
                out[idx + 1u] = u2 * u2;                /* A2 */
                out[idx + 2u] = u3 * u3;                /* A3 */
                out[idx + 3u] = u1 * u2;                /* C12 */
                out[idx + 4u] = u1 * u3;                /* C13 */
                out[idx + 5u] = u2 * u3;                /* C23 */
                out[idx + 6u] = (int64_t)rt3_term_sign(
                    (int64_t)e1, (int64_t)e2, (int64_t)e3, n1, n2, n3);
                idx += (size_t)RT3_SEPT;
            }
        }
    }
    assert(idx == need);
    *out_len = idx;
    return SRMECH_OK;
}

/* ------------------------------------------------------------------ *
 * rc76: IGUSA'S chi_18 — the EXACT product of the 36 even genus-3 theta-nulls.
 *
 * chi_18 in S_18(Gamma_3) is the weight-18 degree-3 Siegel cusp form DEFINED AS THE
 * PRODUCT OF ALL 36 EVEN THETA-CONSTANTS theta[eps](0|Omega) (each theta-null weight
 * 1/2 -> 36*1/2 = 18; Bernatska-Kopeliovich arXiv:2306.14889 p.1, the exact sequence
 * 0 -> chi_18 A(G3) -> A(G3) ->^rho S(2,8), "chi_18 the cusp form of weight 18,
 * defined as the product of all even theta constants"; van der Geer SMF Degree 2&3 +
 * Invariant Theory). Its divisor is H_3 + 2D (H_3 the hyperelliptic locus, D the
 * divisor at infinity) -> chi_18 vanishes EXACTLY on the genus-3 hyperelliptic locus.
 *
 * This peer computes the EXACT LEADING-ORDER HOMOGENEOUS PART of chi_18 (the
 * cusp-vanishing structure): each even null's leading diagonal slice is the minimal
 * diagonal-order (A1+A2+A3 = wt(eps')) monomials, generated DIRECTLY from
 *   n_i in {0}     if eps'_i == 0   (only n_i=0 gives A_i = 0),
 *   n_i in {0,-1}  if eps'_i == 1   (both give A_i = 1),
 * and the 36 leading slices are convolved into the canonical
 * {(A1,A2,A3,C12,C13,C23): coeff} lattice -- the EXACT leading part, NONZERO, at
 * diagonal quarter-order 48 (= 12 in q_i). Coefficients fit int64 (max |coeff| =
 * 2^34, well within int64). Byte-identical to the pure-Python
 * srmech.amsc.riemann_theta.RiemannThetaG3._chi18_leading_part_py.
 *
 * Caller-arena / caller-owned: the caller passes ONE int64 work arena (sized via
 * srmech_riemann_theta_g3_chi18_count); the convolution ping-pongs two halves of it.
 * No malloc. Additive symbols -> ABI unchanged (stays 3).
 *
 * JPL: Rule 1 (no goto/recursion) OK; Rule 2 (bounded loops, <=8 slice pts, 36 nulls,
 * caps on accumulators) OK; Rule 3 (no malloc) OK; Rule 4 (<=60 lines/fn) OK; Rule 5
 * (>=2 asserts/fn) OK; Rule 7 (status propagated) OK; Rule 8 (no fn-like macros) OK.
 * ------------------------------------------------------------------ */

/* one chi_18 lattice monomial = 7 int64: A1,A2,A3,C12,C13,C23,coeff */
#define CHI18_SEPT 7
/* a generous, fixed upper bound on the monomial count of any ping-pong buffer: the
 * product of the 36 even-null leading slices peaks at 216 intermediate monomials and
 * settles to 109; CHI18_CAP bounds BOTH buffers (the partial product never exceeds
 * this) -- a compiled-in safety ceiling, not a malloc. */
#define CHI18_CAP 512

/* The number of int64 the caller arena needs: THREE buffers (two ping-pong + one
 * per-null slice scratch), each CHI18_CAP monomials * CHI18_SEPT int64. box is accepted
 * for signature parity with the Python carrier but does not change the leading part (the
 * slice is box-independent for box >= 1); it is asserted >= 1 by the caller. */
size_t srmech_riemann_theta_g3_chi18_count(uint32_t box)
{
    (void)box;                                      /* leading part is box-independent */
    assert(CHI18_SEPT == 7);
    assert(CHI18_CAP >= 109u);
    return (size_t)3u * (size_t)CHI18_CAP * (size_t)CHI18_SEPT;
}

/* Accumulate one monomial (key0..key5, coeff) into the septuple buffer buf[0..*len),
 * merging a duplicate key by summing coeffs. *len is in MONOMIALS (not int64).
 * SRMECH_ERR_OVERFLOW if a new key would exceed cap monomials. */
static srmech_status_t chi18_accum(int64_t *buf, size_t *len, size_t cap,
                                   const int64_t *key, int64_t coeff)
{
    size_t i, base;
    assert(buf != NULL);
    assert(len != NULL && key != NULL);
    for (i = 0u; i < *len; ++i) {
        base = i * (size_t)CHI18_SEPT;
        if (buf[base + 0u] == key[0] && buf[base + 1u] == key[1]
                && buf[base + 2u] == key[2] && buf[base + 3u] == key[3]
                && buf[base + 4u] == key[4] && buf[base + 5u] == key[5]) {
            buf[base + 6u] += coeff;            /* merge duplicate key */
            return SRMECH_OK;
        }
    }
    if (*len >= cap) {
        return SRMECH_ERR_OVERFLOW;
    }
    base = (*len) * (size_t)CHI18_SEPT;
    buf[base + 0u] = key[0]; buf[base + 1u] = key[1]; buf[base + 2u] = key[2];
    buf[base + 3u] = key[3]; buf[base + 4u] = key[4]; buf[base + 5u] = key[5];
    buf[base + 6u] = coeff;
    *len += 1u;
    return SRMECH_OK;
}

/* The per-term genus-3 sign (-1)^{e.n}: Class-K pin-slot, never abs() (shared shape
 * with rt3_term_sign but specialised to the small chi_18 leading-slice indices). */
static int chi18_sign(int e1, int e2, int e3, int n1, int n2, int n3)
{
    int parity = (e1 * n1 + e2 * n2 + e3 * n3) % 2;
    assert((e1 == 0 || e1 == 1) && (e2 == 0 || e2 == 1));
    assert(e3 == 0 || e3 == 1);
    if (parity < 0) {
        parity += 2;                            /* floor-mod into {0,1} */
    }
    return (parity == 0) ? 1 : -1;              /* Class-K +-1, no abs() */
}

/* Build one even null's leading diagonal slice into slice[]/(*slen) (monomials).
 * Enumerates n_i in {0} (ep_i=0) or {0,-1} (ep_i=1); each monomial is the minimal
 * diagonal-order term. SRMECH_ERR_OVERFLOW only if cap is too small (never for a
 * single slice: <= 8 raw points). */
static srmech_status_t chi18_leading_slice(int ep1, int ep2, int ep3,
                                           int e1, int e2, int e3,
                                           int64_t *slice, size_t *slen, size_t cap)
{
    int i1, i2, i3, n1, n2, n3;
    int64_t u1, u2, u3, key[6];
    srmech_status_t st;
    assert(slice != NULL && slen != NULL);
    assert((ep1 == 0 || ep1 == 1) && (ep3 == 0 || ep3 == 1));
    *slen = 0u;
    for (i1 = 0; i1 <= ep1; ++i1) {            /* i1 in {0} or {0,1} -> n1 in {0,-1} */
        n1 = -i1; u1 = 2 * (int64_t)n1 + (int64_t)ep1;
        for (i2 = 0; i2 <= ep2; ++i2) {
            n2 = -i2; u2 = 2 * (int64_t)n2 + (int64_t)ep2;
            for (i3 = 0; i3 <= ep3; ++i3) {
                n3 = -i3; u3 = 2 * (int64_t)n3 + (int64_t)ep3;
                key[0] = u1 * u1; key[1] = u2 * u2; key[2] = u3 * u3;
                key[3] = u1 * u2; key[4] = u1 * u3; key[5] = u2 * u3;
                st = chi18_accum(slice, slen, cap, key,
                                 (int64_t)chi18_sign(e1, e2, e3, n1, n2, n3));
                if (st != SRMECH_OK) {
                    return st;
                }
            }
        }
    }
    return SRMECH_OK;
}

/* Convolve src[]/(slen) (the running product) by one slice[]/(sllen) into dst[]/(*dlen),
 * dropping zero-coeff merges at the end. dst must be a DIFFERENT buffer from src. */
static srmech_status_t chi18_convolve(const int64_t *src, size_t slen,
                                      const int64_t *slice, size_t sllen,
                                      int64_t *dst, size_t *dlen, size_t cap)
{
    size_t i, j, a, b, w;
    int64_t key[6];
    srmech_status_t st;
    assert(src != NULL && slice != NULL && dst != NULL);
    assert(dlen != NULL);
    *dlen = 0u;
    for (i = 0u; i < slen; ++i) {
        a = i * (size_t)CHI18_SEPT;
        for (j = 0u; j < sllen; ++j) {
            b = j * (size_t)CHI18_SEPT;
            key[0] = src[a + 0u] + slice[b + 0u]; key[1] = src[a + 1u] + slice[b + 1u];
            key[2] = src[a + 2u] + slice[b + 2u]; key[3] = src[a + 3u] + slice[b + 3u];
            key[4] = src[a + 4u] + slice[b + 4u]; key[5] = src[a + 5u] + slice[b + 5u];
            st = chi18_accum(dst, dlen, cap, key, src[a + 6u] * slice[b + 6u]);
            if (st != SRMECH_OK) {
                return st;
            }
        }
    }
    /* drop zero-coeff monomials (compact in place) */
    w = 0u;
    for (i = 0u; i < *dlen; ++i) {
        a = i * (size_t)CHI18_SEPT;
        if (dst[a + 6u] != 0) {
            b = w * (size_t)CHI18_SEPT;
            for (j = 0u; j < (size_t)CHI18_SEPT; ++j) { dst[b + j] = dst[a + j]; }
            w += 1u;
        }
    }
    *dlen = w;
    return SRMECH_OK;
}

/* Emit Igusa's chi_18 leading-order homogeneous part as a flat caller-owned int64
 * array of [A1,A2,A3,C12,C13,C23,coeff] septuples (one per nonzero leading monomial).
 * work[] is the caller arena (work_cap int64, >= srmech_riemann_theta_g3_chi18_count);
 * out[] receives the result (out_cap int64); *out_len <- int64 written. box is for
 * signature parity (asserted >= 1). SRMECH_ERR_BAD_INPUT on box==0 / undersized work;
 * overflow statuses on undersized buffers. */
srmech_status_t srmech_riemann_theta_g3_chi18(
    uint32_t box, int64_t *work, size_t work_cap,
    int64_t *out, size_t out_cap, size_t *out_len)
{
    int64_t *cur, *nxt, *slice, *tmp;
    size_t clen, nlen, sllen, half, i, n;
    int ep1, ep2, ep3, e1, e2, e3;
    srmech_status_t st;
    assert(work != NULL && out != NULL);
    assert(out_len != NULL);
    if (box == 0u || work_cap < srmech_riemann_theta_g3_chi18_count(box)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    half = (size_t)CHI18_CAP * (size_t)CHI18_SEPT;  /* one buffer (int64) */
    cur = work; nxt = work + half; slice = work + 2u * half;
    clen = 1u;                                       /* running product starts at 1 */
    for (i = 0u; i < (size_t)CHI18_SEPT; ++i) { cur[i] = 0; }
    cur[6] = 1;                                      /* the empty monomial, coeff 1 */
    /* multiply by each of the 36 even nulls (eps'.eps even), lexicographic order */
    for (ep1 = 0; ep1 <= 1; ++ep1) { for (ep2 = 0; ep2 <= 1; ++ep2) {
    for (ep3 = 0; ep3 <= 1; ++ep3) { for (e1 = 0; e1 <= 1; ++e1) {
    for (e2 = 0; e2 <= 1; ++e2) { for (e3 = 0; e3 <= 1; ++e3) {
        if ((ep1 * e1 + ep2 * e2 + ep3 * e3) % 2 != 0) { continue; }  /* even only */
        st = chi18_leading_slice(ep1, ep2, ep3, e1, e2, e3,
                                 slice, &sllen, (size_t)CHI18_CAP);
        if (st != SRMECH_OK) { return st; }
        st = chi18_convolve(cur, clen, slice, sllen, nxt, &nlen, (size_t)CHI18_CAP);
        if (st != SRMECH_OK) { return st; }
        tmp = cur; cur = nxt; nxt = tmp;            /* ping-pong */
        clen = nlen;
    } } } } } }
    n = clen * (size_t)CHI18_SEPT;
    if (n > out_cap) { return SRMECH_ERR_OVERFLOW; }
    for (i = 0u; i < n; ++i) { out[i] = cur[i]; }   /* copy result to out[] */
    *out_len = n;
    return SRMECH_OK;
}
