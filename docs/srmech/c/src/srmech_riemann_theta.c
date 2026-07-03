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
/* rc77 helpers (the genus-3 Sp(6,Z) transformation; 3x3 blocks in a 36-int gamma) */
static int64_t rt3_g(const int64_t *gamma, int blk, int r, int c);
static int64_t rt3_matvec(const int64_t *gamma, int blk, const int64_t *v, int row);
static int64_t rt3_diag_pqt(const int64_t *gamma, int pblk, int qblk, int row);
static int64_t rt3_ptq(const int64_t *gamma, int pblk, int qblk, int i, int j);
static int64_t rt3_pqt(const int64_t *gamma, int pblk, int qblk, int i, int j);
static int rt3_is_symplectic(const int64_t *gamma);
static int64_t rt3_eight_phi(const int64_t *gamma,
                             const int64_t *epp, const int64_t *eps);
static int rt3_eighth_sign(int64_t e1, int64_t e2, int64_t e3,
                           int64_t n1, int64_t n2, int64_t n3);
/* rc80 helper (the genus-4 per-term Class-K sign) */
static int rt4_term_sign(int64_t e1, int64_t e2, int64_t e3, int64_t e4,
                         int64_t n1, int64_t n2, int64_t n3, int64_t n4);
/* rc85 helpers (the genus-4 Sp(8,Z) transformation; 4x4 blocks in a 64-int gamma) */
static int64_t rt4_g(const int64_t *gamma, int blk, int r, int c);
static int64_t rt4_matvec(const int64_t *gamma, int blk, const int64_t *v, int row);
static int64_t rt4_diag_pqt(const int64_t *gamma, int pblk, int qblk, int row);
static int64_t rt4_ptq(const int64_t *gamma, int pblk, int qblk, int i, int j);
static int64_t rt4_pqt(const int64_t *gamma, int pblk, int qblk, int i, int j);
static int rt4_is_symplectic(const int64_t *gamma);
static int64_t rt4_eight_phi(const int64_t *gamma,
                             const int64_t *epp, const int64_t *eps);

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
 *  rc87: EXACT theta evaluation at a RATIONAL argument (the genus-axis
 *  Fay-trisecant / KP-Hirota FOUNDATION). C peer of
 *  srmech.amsc.riemann_theta.RiemannTheta.theta_at.
 * ================================================================== *
 *
 * The genus-2 theta at a RATIONAL argument z = z_num/z_den (z_den even = 2N) is
 * exactly representable: the extra Fourier factor of each lattice point n,
 *   exp(2 pi i (n + ep'/2) . z) = zeta_m^{(2n1+ep1) z1 + (2n2+ep2) z2}, m = 2 z_den,
 * is a ROOT OF UNITY in the cyclotomic ring Z[zeta_m] (NO transcendental eval). This
 * peer mirrors the genuinely-new EXACT-INTEGER per-term content: the SAME (A,B,C)
 * quarter-nome exponents as srmech_riemann_theta_lattice PLUS the phase exponent
 * e_mod = ((2n1+ep1) z1 + (2n2+ep2) z2) mod m (the root-of-unity exponent, reduced
 * into [0,m) -- a Class-I cyclic reduction) PLUS the Class-K sign (-1)^{e.n}. It emits
 * one [A, B, C, e_mod, sign] QUINTUPLE per lattice point |n_i| <= box, row-major
 * (n1,n2); the Python marshaller accumulates sign * zeta_m^{e_mod} into the canonical
 * {(A,B,C): cyclotomic-coeff} lattice by looking each zeta_m^{e_mod} up in the REUSED
 * exact-DFT cyclotomic power basis (srmech.amsc.cascade.exact_dft) -- byte-identical to
 * the pure-Python theta_at. Caller-owned out[] (no malloc), like the lattice peer.
 * Additive symbols -> ABI unchanged (stays 3). */

/* one lattice point emits 5 int64: A, B, C, e_mod, sign */
#define RT_AT_QUINT 5

/* The root-of-unity exponent e = (u1 z1 + u2 z2) mod m, reduced into [0, m) (the
 * Class-I cyclic reduction; a floor-mod, never abs). m = 2*z_den >= 2. */
static int64_t rt_phase_mod(int64_t u1, int64_t u2, int64_t z1, int64_t z2, int64_t m)
{
    int64_t e = u1 * z1 + u2 * z2;
    assert(m >= 2);
    e %= m;
    if (e < 0) {
        e += m;                                     /* floor-mod into [0, m) */
    }
    assert(e >= 0 && e < m);
    return e;
}

/* The number of int64 a box needs for the theta_at lattice: (2*box+1)^2 points,
 * RT_AT_QUINT int64 each. The caller sizes its out[] from this (no malloc here). */
size_t srmech_riemann_theta_at_count(uint32_t box)
{
    size_t side = (size_t)box * 2u + 1u;
    assert(RT_AT_QUINT == 5);
    assert(side >= 1u);
    return side * side * (size_t)RT_AT_QUINT;
}

/* Emit the genus-2 theta_at phase lattice for characteristic [ep1,ep2; e1,e2] (each
 * bit in {0,1}) at rational argument z=(z1,z2)/z_den, m = 2*z_den (>= 2), over the box
 * |n_i| <= box, as a flat caller-owned int64 array of [A, B, C, e_mod, sign]
 * quintuples in row-major (n1,n2) order. *out_len <- the number of int64 written
 * (= srmech_riemann_theta_at_count). SRMECH_ERR_BAD_INPUT if a characteristic bit is
 * not in {0,1} or m < 2; SRMECH_ERR_OVERFLOW if out[] is too small. */
srmech_status_t srmech_riemann_theta_at(
    int ep1, int ep2, int e1, int e2,
    int64_t z1, int64_t z2, int64_t m, uint32_t box,
    int64_t *out, size_t out_cap, size_t *out_len)
{
    size_t need, idx;
    int64_t n1, n2, lo, hi, u1, u2;
    assert(out != NULL);
    assert(out_len != NULL);
    if (!rt_bit_ok(ep1) || !rt_bit_ok(ep2) || !rt_bit_ok(e1) || !rt_bit_ok(e2)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (m < 2) {
        return SRMECH_ERR_BAD_INPUT;
    }
    need = srmech_riemann_theta_at_count(box);
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
            out[idx + 0u] = u1 * u1;                                /* A */
            out[idx + 1u] = u2 * u2;                                /* B */
            out[idx + 2u] = u1 * u2;                                /* C */
            out[idx + 3u] = rt_phase_mod(u1, u2, z1, z2, m);        /* e_mod in [0,m) */
            out[idx + 4u] = (int64_t)rt_term_sign((int64_t)e1, (int64_t)e2,
                                                  n1, n2);          /* Class-K sign */
            idx += (size_t)RT_AT_QUINT;
        }
    }
    assert(idx == need);
    *out_len = idx;
    return SRMECH_OK;
}

/* ================================================================== *
 *  rc88: srmech_riemann_theta_cyc_mul — exact Z[zeta_m] power-basis MULTIPLY
 * ================================================================== *
 *
 * The genuinely-new exact-integer kernel behind the rc88 genus-axis Fay / Hirota
 * bilinear VERIFIER (RiemannTheta.addition_holds_at / RiemannThetaG3.addition_holds_at,
 * Riemann's theta addition formula in second-order thetas). theta_at (rc87) gives theta
 * at a rational argument as a {key: Z[zeta_m] coeff} lattice; the verifier's BILINEAR
 * product multiplies the cyclotomic COEFFICIENTS (this kernel) while convolving the
 * integer exponent keys (caller bookkeeping in Python -- the rc73/rc74 addition/Goepel
 * gate precedent). The product is
 *   (sum_i a_i zeta^i)(sum_j b_j zeta^j) = sum_{i,j} a_i b_j zeta^{i+j},
 * each zeta^{i+j} reduced to the power basis {1,zeta,...,zeta^{deg-1}} via the REUSED
 * rc29 exact-DFT reduction table (table[(i+j) mod m], deg = phi(m)) -- byte-identical to
 * the pure-Python _cyc_mul_py. Pure integer (no float, no abs, no malloc, no goto). The
 * int64 fast path GUARDS the per-coefficient magnitude (a Class-K sign-branch range read,
 * never abs); on a too-large coefficient it returns SRMECH_ERR_OVERFLOW so the caller
 * falls to the pure-Python bignum body (the complete alternative). Additive symbol ->
 * SRMECH_ABI_VERSION unchanged (stays 3). out[] MUST NOT alias a or b. */

#define RT_CYC_MAXMAG ((int64_t)1 << 18)   /* per-coefficient int64 fast-path guard */
#define RT_CYC_MAXDEG 16u                  /* power-basis degree guard (deg = phi(m)) */

/* True (1) iff every one of n int64 entries lies in [-RT_CYC_MAXMAG, RT_CYC_MAXMAG]
 * (a Class-K sign-branch range read, never abs). The guard keeps the multiply-accumulate
 * (deg^2 terms of a three-factor product) provably inside int64. */
static int rt_cyc_in_range(const int64_t *v, size_t n)
{
    size_t i;
    assert(v != NULL);
    assert(RT_CYC_MAXMAG > 0);
    for (i = 0u; i < n; ++i) {
        if (v[i] > RT_CYC_MAXMAG || v[i] < -RT_CYC_MAXMAG) {
            return 0;
        }
    }
    return 1;
}

/* out[deg] <- a[deg] * b[deg] in Z[zeta_m], reduced via the m-row x deg-col table
 * (table[j*deg + k] = coefficient k of zeta_m^j). Returns SRMECH_ERR_BAD_INPUT on a NULL
 * pointer / bad deg / m < 2, SRMECH_ERR_OVERFLOW if a coefficient exceeds the int64
 * fast-path guard (caller runs the pure bignum path), else SRMECH_OK. */
srmech_status_t srmech_riemann_theta_cyc_mul(
    const int64_t *a, const int64_t *b, uint32_t deg,
    const int64_t *table, uint32_t m, int64_t *out)
{
    uint32_t i, j, k;
    assert(out != NULL);
    assert(a != NULL && b != NULL && table != NULL);
    if (a == NULL || b == NULL || table == NULL || out == NULL) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (deg == 0u || deg > RT_CYC_MAXDEG || m < 2u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (!rt_cyc_in_range(a, (size_t)deg) || !rt_cyc_in_range(b, (size_t)deg) ||
        !rt_cyc_in_range(table, (size_t)m * (size_t)deg)) {
        return SRMECH_ERR_OVERFLOW;            /* caller falls to the pure bignum path */
    }
    for (k = 0u; k < deg; ++k) {
        out[k] = 0;
    }
    for (i = 0u; i < deg; ++i) {
        if (a[i] == 0) {
            continue;
        }
        for (j = 0u; j < deg; ++j) {
            int64_t c;
            const int64_t *row;
            if (b[j] == 0) {
                continue;
            }
            c = a[i] * b[j];                   /* |c| <= MAXMAG^2 < 2^37 */
            row = table + (size_t)((i + j) % m) * (size_t)deg;   /* Class-I cyclic index */
            for (k = 0u; k < deg; ++k) {
                out[k] += c * row[k];          /* |sum| <= deg^2 * MAXMAG^3 < 2^63 */
            }
        }
    }
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

/* ================================================================== *
 *  rc87: GENUS-3 EXACT theta evaluation at a RATIONAL argument. C peer of
 *  srmech.amsc.riemann_theta.RiemannThetaG3.theta_at (the genus-3 analog of
 *  srmech_riemann_theta_at, ONE genus up).
 * ================================================================== */

/* one genus-3 lattice point emits 8 int64: A1, A2, A3, C12, C13, C23, e_mod, sign */
#define RT3_AT_OCT 8

/* The genus-3 root-of-unity exponent e = (u1 z1 + u2 z2 + u3 z3) mod m, reduced into
 * [0, m) (the Class-I cyclic reduction; a floor-mod, never abs). m = 2*z_den >= 2. */
static int64_t rt3_phase_mod(int64_t u1, int64_t u2, int64_t u3,
                             int64_t z1, int64_t z2, int64_t z3, int64_t m)
{
    int64_t e = u1 * z1 + u2 * z2 + u3 * z3;
    assert(m >= 2);
    e %= m;
    if (e < 0) {
        e += m;                                     /* floor-mod into [0, m) */
    }
    assert(e >= 0 && e < m);
    return e;
}

/* The number of int64 a box needs for the genus-3 theta_at lattice: (2*box+1)^3
 * points, RT3_AT_OCT int64 each. The caller sizes its out[] from this (no malloc). */
size_t srmech_riemann_theta_g3_at_count(uint32_t box)
{
    size_t side = (size_t)box * 2u + 1u;
    assert(RT3_AT_OCT == 8);
    assert(side >= 1u);
    return side * side * side * (size_t)RT3_AT_OCT;
}

/* Emit the genus-3 theta_at phase lattice for characteristic [ep1,ep2,ep3; e1,e2,e3]
 * (each bit in {0,1}) at rational argument z=(z1,z2,z3)/z_den, m = 2*z_den (>= 2), over
 * the box |n_i| <= box, as a flat caller-owned int64 array of
 * [A1, A2, A3, C12, C13, C23, e_mod, sign] octuples in row-major (n1,n2,n3) order.
 * *out_len <- the number of int64 written (= srmech_riemann_theta_g3_at_count).
 * SRMECH_ERR_BAD_INPUT if a characteristic bit is not in {0,1} or m < 2;
 * SRMECH_ERR_OVERFLOW if out[] is too small. */
srmech_status_t srmech_riemann_theta_g3_at(
    int ep1, int ep2, int ep3, int e1, int e2, int e3,
    int64_t z1, int64_t z2, int64_t z3, int64_t m, uint32_t box,
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
    if (m < 2) {
        return SRMECH_ERR_BAD_INPUT;
    }
    need = srmech_riemann_theta_g3_at_count(box);
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
                out[idx + 0u] = u1 * u1;                            /* A1 */
                out[idx + 1u] = u2 * u2;                            /* A2 */
                out[idx + 2u] = u3 * u3;                            /* A3 */
                out[idx + 3u] = u1 * u2;                            /* C12 */
                out[idx + 4u] = u1 * u3;                            /* C13 */
                out[idx + 5u] = u2 * u3;                            /* C23 */
                out[idx + 6u] = rt3_phase_mod(u1, u2, u3, z1, z2, z3, m);
                out[idx + 7u] = (int64_t)rt3_term_sign(
                    (int64_t)e1, (int64_t)e2, (int64_t)e3, n1, n2, n3);
                idx += (size_t)RT3_AT_OCT;
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

/* ================================================================== *
 *  rc77 (A): the genus-3 Sp(6,Z) characteristic TRANSFORMATION + kappa 8th root
 * ================================================================== *
 *
 * The genus-3 modular group Sp(2g,Z)=Sp(6,Z) acts on the binary characteristic
 * m=[ep'; ep] (six bits in {0,1}; ep' upper, ep lower, each a 3-vector) by the EXACT
 * affine-linear map (Igusa, Theta Functions (1972) V.1; DLMF 21.5.9, stated for
 * GENERAL genus g with g x g blocks -- here g=3, 3x3 blocks):
 *   ep' |-> D ep' - C ep + diag(C D^T)
 *   ep  |-> -B ep' + A ep + diag(A B^T)
 * reduced mod 2 for the bit. The theta-constant picks up an 8th-root-of-unity
 * multiplier; this peer returns the CHARACTERISTIC-DEPENDENT Igusa phase part
 * exp(2 pi i phi_m) as the EXACT integer exponent k in Z/8 (rational phi_m, denom |
 * 8, so 8*phi_m is an integer). The genus-g phi_m (a sum over k,l = 1..g; the same
 * expression at every g) is
 *   phi_m = -1/2 ep'^T (B D^T) ep' + ep^T (A^T C) ep - 2 ep'^T (B^T C) ep
 *           - diag(A B^T)^T (D ep' - C ep)
 * -> 8*phi_m = -4 ep'^T (B D^T) ep' + 8 ep^T (A^T C) ep - 16 ep'^T (B^T C) ep
 *              - 8 diag(A B^T)^T (D ep' - C ep)
 * (the g=2 expression of srmech_riemann_theta_sp4_char, parametrically extended to
 * 3-vectors / 3x3 blocks). The remaining gamma-only kappa_0(gamma) (the Maslov/Weil
 * cocycle 8th root) is BOUND to the TRANSCENDENTAL automorphy factor
 * det(C Omega + D)^{1/2} and is NOT computed here -- off the decision path, carried
 * symbolically. gamma is 36 int64 entries: the A,B,C,D 3x3 blocks, each row-major.
 * All exact integer / mod-2; no float, no abs(). */

/* index a 3x3 block (blk in {0:A,1:B,2:C,3:D}) entry (r,c) in the flat gamma[36] */
static int64_t rt3_g(const int64_t *gamma, int blk, int r, int c)
{
    assert(gamma != NULL);
    assert(blk >= 0 && blk < 4 && r >= 0 && r < 3 && c >= 0 && c < 3);
    return gamma[(size_t)blk * 9u + (size_t)r * 3u + (size_t)c];
}

/* (M v)_row for a 3x3 block M of gamma and a length-3 vector v. */
static int64_t rt3_matvec(const int64_t *gamma, int blk, const int64_t *v, int row)
{
    int c;
    int64_t acc = 0;
    assert(gamma != NULL && v != NULL);
    assert(row >= 0 && row < 3);
    for (c = 0; c < 3; ++c) { acc += rt3_g(gamma, blk, row, c) * v[c]; }
    return acc;
}

/* diag(P Q^T)_row = sum_k P[row][k] Q[row][k]  (the row-row dot of two 3x3 blocks). */
static int64_t rt3_diag_pqt(const int64_t *gamma, int pblk, int qblk, int row)
{
    int k;
    int64_t acc = 0;
    assert(gamma != NULL);
    assert(row >= 0 && row < 3);
    for (k = 0; k < 3; ++k) {
        acc += rt3_g(gamma, pblk, row, k) * rt3_g(gamma, qblk, row, k);
    }
    return acc;
}

/* (P^T Q)[i][j] = sum_k P[k][i] Q[k][j]  -- one entry of a transposed-times block. */
static int64_t rt3_ptq(const int64_t *gamma, int pblk, int qblk, int i, int j)
{
    int k;
    int64_t acc = 0;
    assert(gamma != NULL);
    assert(i >= 0 && i < 3 && j >= 0 && j < 3);
    for (k = 0; k < 3; ++k) {
        acc += rt3_g(gamma, pblk, k, i) * rt3_g(gamma, qblk, k, j);
    }
    return acc;
}

/* (P Q^T)[i][j] = sum_k P[i][k] Q[j][k]  -- one entry of a block-times-transposed. */
static int64_t rt3_pqt(const int64_t *gamma, int pblk, int qblk, int i, int j)
{
    int k;
    int64_t acc = 0;
    assert(gamma != NULL);
    assert(i >= 0 && i < 3 && j >= 0 && j < 3);
    for (k = 0; k < 3; ++k) {
        acc += rt3_g(gamma, pblk, i, k) * rt3_g(gamma, qblk, j, k);
    }
    return acc;
}

/* The symplectic check gamma J gamma^T = J via the exact block conditions
 * A^T C = C^T A (symmetric), B^T D = D^T B (symmetric), A^T D - C^T B = I (3x3).
 * Returns 1 if symplectic, else 0. (blk 0=A,1=B,2=C,3=D.) */
static int rt3_is_symplectic(const int64_t *gamma)
{
    int i, j, ok = 1;
    assert(gamma != NULL);
    for (i = 0; i < 3; ++i) {
        for (j = 0; j < 3; ++j) {
            /* A^T C symmetric, B^T D symmetric */
            if (rt3_ptq(gamma, 0, 2, i, j) != rt3_ptq(gamma, 0, 2, j, i)) { ok = 0; }
            if (rt3_ptq(gamma, 1, 3, i, j) != rt3_ptq(gamma, 1, 3, j, i)) { ok = 0; }
            /* A^T D - C^T B == I */
            if (rt3_ptq(gamma, 0, 3, i, j) - rt3_ptq(gamma, 2, 1, i, j)
                    != ((i == j) ? 1 : 0)) { ok = 0; }
        }
    }
    assert(ok == 0 || ok == 1);
    return ok;
}

/* The exact 8*phi_m Igusa phase at genus 3 (an integer; the multiplier exponent is
 * (8*phi_m) mod 8). epp = ep' = (ep1,ep2,ep3), eps = ep = (e1,e2,e3). */
static int64_t rt3_eight_phi(const int64_t *gamma,
                             const int64_t *epp, const int64_t *eps)
{
    int i, j;
    int64_t t1 = 0, t2 = 0, t3 = 0, t4 = 0, depp[3], ceps[3], dab;
    assert(gamma != NULL);
    assert(epp != NULL && eps != NULL);
    for (i = 0; i < 3; ++i) {
        for (j = 0; j < 3; ++j) {
            /* t1: -4 ep'^T (B D^T) ep'   ((BD^T)[i][j] = row-row dot of B,D) */
            t1 += epp[i] * rt3_pqt(gamma, 1, 3, i, j) * epp[j];
            t2 += eps[i] * rt3_ptq(gamma, 0, 2, i, j) * eps[j];   /* ep^T(A^TC)ep */
            t3 += epp[i] * rt3_ptq(gamma, 1, 2, i, j) * eps[j];   /* ep'^T(B^TC)ep */
        }
    }
    for (i = 0; i < 3; ++i) {
        depp[i] = rt3_matvec(gamma, 3, epp, i);     /* (D ep')_i */
        ceps[i] = rt3_matvec(gamma, 2, eps, i);     /* (C ep)_i */
    }
    for (i = 0; i < 3; ++i) {
        dab = rt3_diag_pqt(gamma, 0, 1, i);          /* diag(A B^T)_i */
        t4 += dab * (depp[i] - ceps[i]);
    }
    return -4 * t1 + 8 * t2 - 16 * t3 - 8 * t4;
}

/* The exact genus-3 Sp(6,Z) characteristic transformation + the kappa 8th-root
 * exponent. gamma[36] = A,B,C,D 3x3 blocks (row-major). out_char[6] <-
 * (ep1',ep2',ep3',e1',e2',e3') bits; *kexp <- the multiplier exponent k in {0..7}
 * (multiplier = zeta_8^k). SRMECH_ERR_BAD_INPUT if a bit is invalid or gamma is not
 * symplectic. */
srmech_status_t srmech_riemann_theta_g3_sp6_char(
    const int64_t *gamma, int ep1, int ep2, int ep3, int e1, int e2, int e3,
    int *out_char, int *kexp)
{
    int i;
    int64_t epp[3], eps[3], npp, nep, k8;
    assert(gamma != NULL);
    assert(out_char != NULL && kexp != NULL);
    if (!rt_bit_ok(ep1) || !rt_bit_ok(ep2) || !rt_bit_ok(ep3)
            || !rt_bit_ok(e1) || !rt_bit_ok(e2) || !rt_bit_ok(e3)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (!rt3_is_symplectic(gamma)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    epp[0] = ep1; epp[1] = ep2; epp[2] = ep3;
    eps[0] = e1;  eps[1] = e2;  eps[2] = e3;
    for (i = 0; i < 3; ++i) {
        /* ep' |-> D ep' - C ep + diag(C D^T) */
        npp = rt3_matvec(gamma, 3, epp, i) - rt3_matvec(gamma, 2, eps, i)
            + rt3_diag_pqt(gamma, 2, 3, i);
        /* ep  |-> -B ep' + A ep + diag(A B^T) */
        nep = rt3_matvec(gamma, 0, eps, i) - rt3_matvec(gamma, 1, epp, i)
            + rt3_diag_pqt(gamma, 0, 1, i);
        out_char[i] = (int)(((npp % 2) + 2) % 2);
        out_char[i + 3] = (int)(((nep % 2) + 2) % 2);
    }
    k8 = rt3_eight_phi(gamma, epp, eps);
    *kexp = (int)(((k8 % 8) + 8) % 8);              /* floor-mod into {0..7} */
    return SRMECH_OK;
}

/* ================================================================== *
 *  rc77 (B): the genus-3 EIGHTH-nome lattice (the addition gate's convolution)
 * ================================================================== *
 *
 * The genus-3 two-argument addition theorem (DLMF 21.6.8 at z1=z2=0, lower chars 0,
 * the g=3 specialization -- the sum runs over nu in (Z/2)^3, EIGHT terms) is a
 * lattice equality once theta at Omega AND at 2*Omega clear to ONE common eighth-nome
 * base Q8 = q^{1/8}:
 *   at Omega : A_i = 2(2 n_i + s_i)^2,  C_ij = 2(2 n_i + s_i)(2 n_j + s_j)
 *   at 2Omega: A_i =  (4 n_i + s_i)^2,  C_ij =  (4 n_i + s_i)(4 n_j + s_j)
 * s = (s1,s2,s3) = the DOUBLED upper characteristic (ANY int; the addition right side
 * uses 2 r +- (a +- b)). sign = (-1)^{e.n} (Class-K). Emits the
 * [A1,A2,A3,C12,C13,C23,sign] SEPTUPLE lattice (one per n in |n_i|<=box, row-major);
 * the caller convolves the Omega-side product of two distinct nulls against the
 * 2Omega-side eight-term sum. The genus-3 THREE cross-terms are all exercised. */

/* The per-term genus-3 eighth-nome sign (-1)^{e.n}: Class-K pin-slot, never abs(). */
static int rt3_eighth_sign(int64_t e1, int64_t e2, int64_t e3,
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

/* The number of int64 the genus-3 eighth-nome lattice needs: (2*box+1)^3 points,
 * RT3_SEPT int64 each (same shape as the g3 lattice). No malloc. */
size_t srmech_riemann_theta_g3_eighth_count(uint32_t box)
{
    size_t side = (size_t)box * 2u + 1u;
    assert(RT3_SEPT == 7);
    assert(side >= 1u);
    return side * side * side * (size_t)RT3_SEPT;
}

/* Emit the genus-3 eighth-nome [A1,A2,A3,C12,C13,C23,sign] septuple lattice for the
 * DOUBLED upper characteristic s=(s1,s2,s3) and lower char (e1,e2,e3), at Omega
 * (at_two_omega=0) or at 2Omega (at_two_omega=1), over |n_i|<=box, row-major.
 * *out_len <- int64 written. SRMECH_ERR_BAD_INPUT if a lower-char bit is invalid;
 * SRMECH_ERR_OVERFLOW if out[] is too small. */
srmech_status_t srmech_riemann_theta_g3_eighth_lattice(
    int s1, int s2, int s3, int e1, int e2, int e3, int at_two_omega, uint32_t box,
    int64_t *out, size_t out_cap, size_t *out_len)
{
    size_t need, idx;
    int64_t n1, n2, n3, lo, hi, u1, u2, u3, m;
    assert(out != NULL);
    assert(out_len != NULL);
    if (!rt_bit_ok(e1) || !rt_bit_ok(e2) || !rt_bit_ok(e3)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    need = srmech_riemann_theta_g3_eighth_count(box);
    if (need > out_cap) {
        return SRMECH_ERR_OVERFLOW;
    }
    m = at_two_omega ? 1 : 2;                        /* Omega scales A,C by 2 */
    idx = 0u;
    lo = -(int64_t)box;
    hi = (int64_t)box;
    for (n1 = lo; n1 <= hi; ++n1) {
        u1 = (at_two_omega ? 4 : 2) * n1 + (int64_t)s1;
        for (n2 = lo; n2 <= hi; ++n2) {
            u2 = (at_two_omega ? 4 : 2) * n2 + (int64_t)s2;
            for (n3 = lo; n3 <= hi; ++n3) {
                u3 = (at_two_omega ? 4 : 2) * n3 + (int64_t)s3;
                out[idx + 0u] = m * u1 * u1;            /* A1 */
                out[idx + 1u] = m * u2 * u2;            /* A2 */
                out[idx + 2u] = m * u3 * u3;            /* A3 */
                out[idx + 3u] = m * u1 * u2;            /* C12 */
                out[idx + 4u] = m * u1 * u3;            /* C13 */
                out[idx + 5u] = m * u2 * u3;            /* C23 */
                out[idx + 6u] = (int64_t)rt3_eighth_sign(
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
 * rc78: the genus-3 GÖPEL / FROBENIUS quadratic theta-null SYZYGY gate — the C peer
 * of srmech.amsc.riemann_theta.RiemannThetaG3.goepel_holds.
 *
 * The genus-3 GÖPEL/FROBENIUS quadratic relation among the even theta-NULLS (the
 * genus-3 analog of the genus-2 rc74 Göpel syzygy). It is a 4-PAIR / 8-NULL relation
 * among SAME-Omega even theta-nulls (genus 2 is 3-pair / 6-null; the genus-2-style
 * 6-null lift does NOT hold for genus 3 — exhaustively checked):
 *
 *   theta^2[a]theta^2[b] = theta^2[c]theta^2[d] + theta^2[e]theta^2[f] - theta^2[g]theta^2[h]
 *
 * with the eight even nulls (eps' ; eps, six bits each)
 *   a=[000;001] b=[111;110] | c=[000;010] d=[111;101]
 *   e=[001;000] f=[110;111] | g=[010;000] h=[101;111]
 * all summing to the common GF(2) characteristic [1,1,1; 1,1,1] (a genus-3 Goepel /
 * azygetic system). Glass, Compositio Math 40 (1980) §3 (type-(2) products-of-squares,
 * coeffs +-1); Fiorentino-Salvati Manni SIGMA 16 (2020) 057 §1-2; Igusa Theta Functions
 * (1972) §IV/V; van der Geer SMF Degree 2&3. Holds for ALL Omega.
 *
 * This peer DECIDES the gate: it accumulates the residual LHS - RHS, restricted to the
 * box-stable safe inner region (each A_i, |C_ij| <= box^2), and returns *out_holds=1 iff
 * the residual is EMPTY (the identity holds exactly) and *out_has_cross=1 iff the region
 * is genuinely populated with a genus-3 cross-term (C13 or C23 != 0). Byte-identical to
 * the pure-Python decision.
 *
 * SOUND PRE-RESTRICT (the perf key, mirrors the Python _diag_restrict): each squared
 * null is built with its DIAGONAL exponents A_i <= box^2 only — sound because A_i are
 * non-negative and ADD under the pair product, so any safe product monomial comes from
 * factors each with A_i <= box^2. The pair convolution then keeps only safe-region
 * (A and |C|) output monomials. The negative-C cross-terms are NOT pre-restricted (only
 * the output is C-restricted) — exactly the Python order.
 *
 * Caller-arena / caller-owned: ONE int64 work[] (sized via the count helper) holds the
 * two diag-square scratch buffers + the residual accumulator. No malloc. Additive
 * symbols -> ABI unchanged (stays 3).
 *
 * JPL: Rule 1 (no goto/recursion) OK; Rule 2 (bounded loops — box, <=8 nulls, capped
 * accumulators) OK; Rule 3 (no malloc) OK; Rule 4 (<=60 lines/fn) OK; Rule 5 (>=2
 * asserts/fn) OK; Rule 7 (status propagated) OK; Rule 8 (no fn-like macros) OK.
 * ------------------------------------------------------------------ */

/* one Goepel lattice monomial = 7 int64: A1,A2,A3,C12,C13,C23,coeff */
#define GOEPEL_SEPT 7

/* The eight even-null characteristics (eps'1,eps'2,eps'3, eps1,eps2,eps3) of the
 * canonical genus-3 Goepel quad, in pair order a,b,c,d,e,f,g,h. */
static const int g3_goepel_chars[8][6] = {
    {0, 0, 0, 0, 0, 1}, {1, 1, 1, 1, 1, 0},   /* a, b  (LHS, +) */
    {0, 0, 0, 0, 1, 0}, {1, 1, 1, 1, 0, 1},   /* c, d  (RHS, +) */
    {0, 0, 1, 0, 0, 0}, {1, 1, 0, 1, 1, 1},   /* e, f  (RHS, +) */
    {0, 1, 0, 0, 0, 0}, {1, 0, 1, 1, 1, 1},   /* g, h  (RHS, -) */
};

/* The per-pair residual sign: residual = LHS - RHS = +ab - cd - ef + gh. Pair 0..3. */
static const int g3_goepel_pair_sign[4] = {1, -1, -1, 1};

/* The number of int64 the caller arena needs. THREE buffers: two diag-square scratch +
 * one residual accumulator, each GOEPEL_CAP monomials * GOEPEL_SEPT int64. GOEPEL_CAP is
 * sized to comfortably bound the diag-restricted square AND the safe-restricted residual
 * for box up to ~5 (diag-square <= ~1187, residual <= ~60000 at box 5; box=3 the gate
 * default is ~105 / ~204). A compiled-in safety ceiling, not a malloc. */
#define GOEPEL_CAP 70000

size_t srmech_riemann_theta_g3_goepel_count(uint32_t box)
{
    (void)box;                                      /* arena is box-independent (capped) */
    assert(GOEPEL_SEPT == 7);
    assert(GOEPEL_CAP >= 204u);
    return (size_t)3u * (size_t)GOEPEL_CAP * (size_t)GOEPEL_SEPT;
}

/* Merge one monomial (key0..key5, coeff) into buf[0..*len) (in monomials), summing a
 * duplicate key. SRMECH_ERR_OVERFLOW if a new key would exceed cap monomials. */
static srmech_status_t goepel_accum(int64_t *buf, size_t *len, size_t cap,
                                    const int64_t *key, int64_t coeff)
{
    size_t i, base;
    assert(buf != NULL && len != NULL);
    assert(key != NULL);
    for (i = 0u; i < *len; ++i) {
        base = i * (size_t)GOEPEL_SEPT;
        if (buf[base + 0u] == key[0] && buf[base + 1u] == key[1]
                && buf[base + 2u] == key[2] && buf[base + 3u] == key[3]
                && buf[base + 4u] == key[4] && buf[base + 5u] == key[5]) {
            buf[base + 6u] += coeff;                 /* merge duplicate key */
            return SRMECH_OK;
        }
    }
    if (*len >= cap) {
        return SRMECH_ERR_OVERFLOW;
    }
    base = (*len) * (size_t)GOEPEL_SEPT;
    buf[base + 0u] = key[0]; buf[base + 1u] = key[1]; buf[base + 2u] = key[2];
    buf[base + 3u] = key[3]; buf[base + 4u] = key[4]; buf[base + 5u] = key[5];
    buf[base + 6u] = coeff;
    *len += 1u;
    return SRMECH_OK;
}

/* Build one even null's DIAGONAL-RESTRICTED squared lattice into sq[]/(*slen): the
 * self-convolution of theta[null](Omega) keeping ONLY monomials with each A_i <= bound
 * (sound pre-restrict). The per-term sign is the Class-K pin-slot (-1)^{e.n} * (-1)^{e.m}. */
static srmech_status_t goepel_diag_square(const int *ch, int64_t box, int64_t bound,
                                          int64_t *sq, size_t *slen, size_t cap)
{
    int64_t n1, n2, n3, m1, m2, m3, un[3], um[3], key[6];
    int64_t ep1 = ch[0], ep2 = ch[1], ep3 = ch[2], e1 = ch[3], e2 = ch[4], e3 = ch[5];
    int sgn_n, sgn_m;
    srmech_status_t st;
    assert(sq != NULL && slen != NULL);
    assert(box >= 0 && bound >= 0);
    *slen = 0u;
    for (n1 = -box; n1 <= box; ++n1) { un[0] = 2 * n1 + ep1;
    for (n2 = -box; n2 <= box; ++n2) { un[1] = 2 * n2 + ep2;
    for (n3 = -box; n3 <= box; ++n3) { un[2] = 2 * n3 + ep3;
        sgn_n = rt3_term_sign(e1, e2, e3, n1, n2, n3);
        for (m1 = -box; m1 <= box; ++m1) { um[0] = 2 * m1 + ep1;
            key[0] = un[0] * un[0] + um[0] * um[0]; if (key[0] > bound) { continue; }
        for (m2 = -box; m2 <= box; ++m2) { um[1] = 2 * m2 + ep2;
            key[1] = un[1] * un[1] + um[1] * um[1]; if (key[1] > bound) { continue; }
        for (m3 = -box; m3 <= box; ++m3) { um[2] = 2 * m3 + ep3;
            key[2] = un[2] * un[2] + um[2] * um[2]; if (key[2] > bound) { continue; }
            key[3] = un[0] * un[1] + um[0] * um[1];
            key[4] = un[0] * un[2] + um[0] * um[2];
            key[5] = un[1] * un[2] + um[1] * um[2];
            sgn_m = rt3_term_sign(e1, e2, e3, m1, m2, m3);
            st = goepel_accum(sq, slen, cap, key, (int64_t)(sgn_n * sgn_m));
            if (st != SRMECH_OK) { return st; }
        } } }
    } } }
    return SRMECH_OK;
}

/* Accumulate (sign) * [ theta^2[na] * theta^2[nb] restricted to the safe region ] into
 * the residual res[]/(*rlen). sqa/sqb are the two diag-restricted squares; only output
 * monomials with each A_i <= bound AND |C_ij| <= bound are accumulated (the final safe
 * cut, mirroring Python). */
static srmech_status_t goepel_pair_into_res(const int64_t *sqa, size_t alen,
                                            const int64_t *sqb, size_t blen,
                                            int sign, int64_t bound,
                                            int64_t *res, size_t *rlen, size_t cap)
{
    size_t i, j, ia, ib;
    int64_t key[6], m12, m13, m23;
    srmech_status_t st;
    assert(sqa != NULL && sqb != NULL);
    assert(res != NULL && rlen != NULL);
    for (i = 0u; i < alen; ++i) { ia = i * (size_t)GOEPEL_SEPT;
        for (j = 0u; j < blen; ++j) { ib = j * (size_t)GOEPEL_SEPT;
            key[0] = sqa[ia + 0u] + sqb[ib + 0u]; if (key[0] > bound) { continue; }
            key[1] = sqa[ia + 1u] + sqb[ib + 1u]; if (key[1] > bound) { continue; }
            key[2] = sqa[ia + 2u] + sqb[ib + 2u]; if (key[2] > bound) { continue; }
            key[3] = sqa[ia + 3u] + sqb[ib + 3u];
            m12 = (key[3] >= 0) ? key[3] : -key[3]; if (m12 > bound) { continue; }
            key[4] = sqa[ia + 4u] + sqb[ib + 4u];
            m13 = (key[4] >= 0) ? key[4] : -key[4]; if (m13 > bound) { continue; }
            key[5] = sqa[ia + 5u] + sqb[ib + 5u];
            m23 = (key[5] >= 0) ? key[5] : -key[5]; if (m23 > bound) { continue; }
            st = goepel_accum(res, rlen, cap, key,
                              (int64_t)sign * sqa[ia + 6u] * sqb[ib + 6u]);
            if (st != SRMECH_OK) { return st; }
        }
    }
    return SRMECH_OK;
}

/* Scan the residual for a genuine genus-3 cross-term (C13 or C23 != 0 with nonzero
 * coeff). Returns 1 if present, else 0. */
static int goepel_res_has_cross(const int64_t *res, size_t rlen)
{
    size_t i, base;
    int has = 0;
    assert(res != NULL);
    assert(rlen <= (size_t)GOEPEL_CAP);
    for (i = 0u; i < rlen; ++i) {
        base = i * (size_t)GOEPEL_SEPT;
        if (res[base + 6u] != 0 && (res[base + 4u] != 0 || res[base + 5u] != 0)) {
            has = 1;
        }
    }
    return has;
}

/* DECIDE the genus-3 Goepel syzygy gate. work[] is the caller arena (work_cap int64, >=
 * srmech_riemann_theta_g3_goepel_count(box)); *out_holds <- 1 iff LHS==RHS on the safe
 * region (residual empty), *out_has_cross <- 1 iff a genuine genus-3 cross-term monomial
 * (C13 or C23 != 0) is present in the LHS safe region. SRMECH_ERR_BAD_INPUT on box<3 /
 * undersized work; SRMECH_ERR_OVERFLOW on an over-cap accumulator. */
srmech_status_t srmech_riemann_theta_g3_goepel(
    uint32_t box, int64_t *work, size_t work_cap,
    int *out_holds, int *out_has_cross)
{
    int64_t *sqa, *sqb, *res, bnd;
    size_t alen, blen, rlen, half, i, base;
    int p, holds;
    srmech_status_t st;
    assert(work != NULL);
    assert(out_holds != NULL && out_has_cross != NULL);
    if (box < 3u || work_cap < srmech_riemann_theta_g3_goepel_count(box)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    half = (size_t)GOEPEL_CAP * (size_t)GOEPEL_SEPT;
    sqa = work; sqb = work + half; res = work + 2u * half;
    bnd = (int64_t)box * (int64_t)box;              /* the box-stable safe bound */
    rlen = 0u;
    for (p = 0; p < 4; ++p) {                        /* four pairs: ab cd ef gh */
        st = goepel_diag_square(g3_goepel_chars[2 * p], (int64_t)box, bnd,
                                sqa, &alen, (size_t)GOEPEL_CAP);
        if (st != SRMECH_OK) { return st; }
        st = goepel_diag_square(g3_goepel_chars[2 * p + 1], (int64_t)box, bnd,
                                sqb, &blen, (size_t)GOEPEL_CAP);
        if (st != SRMECH_OK) { return st; }
        st = goepel_pair_into_res(sqa, alen, sqb, blen, g3_goepel_pair_sign[p], bnd,
                                  res, &rlen, (size_t)GOEPEL_CAP);
        if (st != SRMECH_OK) { return st; }
    }
    holds = 1;                                       /* residual must vanish (LHS==RHS) */
    for (i = 0u; i < rlen; ++i) {
        base = i * (size_t)GOEPEL_SEPT;
        if (res[base + 6u] != 0) { holds = 0; }      /* nonzero coeff -> not exact */
    }
    /* cross-term presence: re-derive the LHS-only safe region (pair 0) and check C13/C23 */
    st = goepel_diag_square(g3_goepel_chars[0], (int64_t)box, bnd,
                            sqa, &alen, (size_t)GOEPEL_CAP);
    if (st != SRMECH_OK) { return st; }
    st = goepel_diag_square(g3_goepel_chars[1], (int64_t)box, bnd,
                            sqb, &blen, (size_t)GOEPEL_CAP);
    if (st != SRMECH_OK) { return st; }
    rlen = 0u;
    st = goepel_pair_into_res(sqa, alen, sqb, blen, 1, bnd,
                              res, &rlen, (size_t)GOEPEL_CAP);
    if (st != SRMECH_OK) { return st; }
    *out_holds = holds;
    *out_has_cross = goepel_res_has_cross(res, rlen);
    return SRMECH_OK;
}

/* ------------------------------------------------------------------ *
 * rc80 (NEXT GENUS RUNG, the SCHOTTKY FRONTIER): the GENUS-4 EXACT-INTEGER EXPONENT
 * LATTICE -- the C peer of srmech.amsc.riemann_theta.RiemannThetaG4, the genus-4
 * analog of the rc75 genus-3 peer. The genus-4 theta-constant theta[ep'; e](0|Omega)
 * (Grushevsky arXiv:1009.0369 eq.1, the g=4 specialization; binary characteristic
 * [ep1,ep2,ep3,ep4; e1,e2,e3,e4], eight bits in {0,1}) is a lattice sum over n in Z^4
 * of (-1)^{e.n} prod_i q_i^{m_i^2} prod_{i<j} q_ij^{m_i m_j}, m_i = n_i + ep'_i/2.
 * Cleared to the quarter-nome base (Q_i,Q_ij)=(q_i,q_ij)^{1/4} a term is
 *   Q1^A1 Q2^A2 Q3^A3 Q4^A4 Q12^C12 Q13^C13 Q14^C14 Q23^C23 Q24^C24 Q34^C34 *(-1)^{e.n}
 * with EXACT INTEGER exponents A_i=(2n_i+ep_i)^2 and the SIX cross-terms
 *   C_ij = (2n_i+ep_i)(2n_j+ep_j)   for the 6 pairs {12,13,14,23,24,34}
 * (genus 2 had ONE cross-term, genus 3 THREE, genus 4 SIX -- the scaling difficulty).
 * The lower characteristic e gives the per-term sign (-1)^{e.n} (Class-K pin-slot,
 * never abs). This op emits the lattice as a flat caller-owned int64 array of
 * [A1,A2,A3,A4,C12,C13,C14,C23,C24,C34,sign] 11-TUPLES (one per lattice point
 * |n_i| <= box, row-major (n1,n2,n3,n4)); the genus-4 theta-CONSTANT coefficients are
 * small +-1 lattice counts (int64-exact, no bignum), and the caller accumulates the
 * 11-tuples into the canonical {(A1..A4,C12,C13,C14,C23,C24,C34):coeff} lattice
 * (byte-identical to the Python carrier). Caller-owned out[]; no malloc. Additive
 * symbol -> ABI unchanged (stays 3). NOTE: (2*box+1)^4 grows fast -- the caller keeps
 * box small (2 or 3); the formal relations are box-stable. */

/* one genus-4 lattice point emits 11 int64:
 * A1,A2,A3,A4,C12,C13,C14,C23,C24,C34,sign */
#define RT4_TUP 11

/* The number of int64 a box needs for the genus-4 lattice: (2*box+1)^4 points,
 * RT4_TUP int64 each. The caller sizes its out[] from this (no malloc here). */
size_t srmech_riemann_theta_g4_count(uint32_t box)
{
    size_t side = (size_t)box * 2u + 1u;
    assert(RT4_TUP == 11);
    assert(side >= 1u);
    return side * side * side * side * (size_t)RT4_TUP;
}

/* The per-term genus-4 sign (-1)^{e1 n1 + e2 n2 + e3 n3 + e4 n4}: Class-K pin-slot (a
 * stored +1/-1 from an explicit parity branch), never an ALU abs(). */
static int rt4_term_sign(int64_t e1, int64_t e2, int64_t e3, int64_t e4,
                         int64_t n1, int64_t n2, int64_t n3, int64_t n4)
{
    int64_t parity = (e1 * n1 + e2 * n2 + e3 * n3 + e4 * n4) % 2;
    assert((e1 == 0 || e1 == 1) && (e2 == 0 || e2 == 1));
    assert((e3 == 0 || e3 == 1) && (e4 == 0 || e4 == 1));
    if (parity < 0) {
        parity += 2;                                /* floor-mod into {0,1} */
    }
    return (parity == 0) ? 1 : -1;                  /* Class-K +-1, no abs() */
}

/* Emit the genus-4 theta-constant exponent lattice for characteristic
 * [ep1,ep2,ep3,ep4; e1,e2,e3,e4] (each bit in {0,1}) over the box |n_i| <= box, as a
 * flat caller-owned int64 array of [A1,A2,A3,A4,C12,C13,C14,C23,C24,C34,sign] 11-tuples
 * in row-major (n1,n2,n3,n4) order. *out_len <- the number of int64 written (= the g4
 * count). SRMECH_ERR_BAD_INPUT if any characteristic bit is not in {0,1};
 * SRMECH_ERR_OVERFLOW if the caller out[] (out_cap int64) is too small. */
srmech_status_t srmech_riemann_theta_g4_lattice(
    int ep1, int ep2, int ep3, int ep4,
    int e1, int e2, int e3, int e4, uint32_t box,
    int64_t *out, size_t out_cap, size_t *out_len)
{
    size_t need, idx;
    int64_t n1, n2, n3, n4, lo, hi, u1, u2, u3, u4;
    assert(out != NULL);
    assert(out_len != NULL);
    if (!rt_bit_ok(ep1) || !rt_bit_ok(ep2) || !rt_bit_ok(ep3) || !rt_bit_ok(ep4)
            || !rt_bit_ok(e1) || !rt_bit_ok(e2) || !rt_bit_ok(e3)
            || !rt_bit_ok(e4)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    need = srmech_riemann_theta_g4_count(box);
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
                for (n4 = lo; n4 <= hi; ++n4) {
                    u4 = 2 * n4 + (int64_t)ep4;
                    out[idx + 0u] = u1 * u1;            /* A1 */
                    out[idx + 1u] = u2 * u2;            /* A2 */
                    out[idx + 2u] = u3 * u3;            /* A3 */
                    out[idx + 3u] = u4 * u4;            /* A4 */
                    out[idx + 4u] = u1 * u2;            /* C12 */
                    out[idx + 5u] = u1 * u3;            /* C13 */
                    out[idx + 6u] = u1 * u4;            /* C14 */
                    out[idx + 7u] = u2 * u3;            /* C23 */
                    out[idx + 8u] = u2 * u4;            /* C24 */
                    out[idx + 9u] = u3 * u4;            /* C34 */
                    out[idx + 10u] = (int64_t)rt4_term_sign(
                        (int64_t)e1, (int64_t)e2, (int64_t)e3, (int64_t)e4,
                        n1, n2, n3, n4);
                    idx += (size_t)RT4_TUP;
                }
            }
        }
    }
    assert(idx == need);
    *out_len = idx;
    return SRMECH_OK;
}

/* ------------------------------------------------------------------ *
 * rc86 (NEXT GENUS RUNG, PAST the SCHOTTKY FRONTIER): the GENUS-5 EXACT-INTEGER EXPONENT
 * LATTICE -- the C peer of srmech.amsc.riemann_theta.RiemannThetaG5, the genus-5 analog
 * of the rc80 genus-4 peer. The genus-5 theta-constant theta[ep'; e](0|Omega)
 * (Grushevsky arXiv:1009.0369 eq.1, the g=5 specialization; binary characteristic
 * [ep1..ep5; e1..e5], ten bits in {0,1}) is a lattice sum over n in Z^5 of
 * (-1)^{e.n} prod_i q_i^{m_i^2} prod_{i<j} q_ij^{m_i m_j}, m_i = n_i + ep'_i/2.
 * Cleared to the quarter-nome base (Q_i,Q_ij)=(q_i,q_ij)^{1/4} a term is
 *   prod_i Q_i^{A_i} prod_{i<j} Q_ij^{C_ij} *(-1)^{e.n}
 * with EXACT INTEGER exponents A_i=(2n_i+ep_i)^2 and the TEN cross-terms
 *   C_ij = (2n_i+ep_i)(2n_j+ep_j)  for the 10 pairs {12,13,14,15,23,24,25,34,35,45}
 * (genus 2 had ONE, genus 3 THREE, genus 4 SIX, genus 5 TEN -- the scaling difficulty).
 * The lower characteristic e gives the per-term sign (-1)^{e.n} (Class-K pin-slot, never
 * abs). This op emits the lattice as a flat caller-owned int64 array of
 * [A1..A5,C12,C13,C14,C15,C23,C24,C25,C34,C35,C45,sign] 16-TUPLES (one per lattice point
 * |n_i| <= box, row-major (n1,n2,n3,n4,n5)); the genus-5 theta-CONSTANT coefficients are
 * small +-1 lattice counts (int64-exact, no bignum), and the caller accumulates the
 * 16-tuples into the canonical 15-tuple:coeff lattice (byte-identical to the Python
 * carrier). Caller-owned out[]; no malloc. Additive symbol -> ABI unchanged (stays 3).
 * NOTE: (2*box+1)^5 grows FAST -- the caller keeps box small (1 or 2; box >= 3 is
 * catastrophic); the formal relations are box-stable. The genuinely-OPEN genus-5 Schottky
 * decision (NO single modular form cuts J_5: codim 3 in A_5, NOT a hypersurface) is
 * DOCUMENTED in the Python carrier, NOT built here. */

/* one genus-5 lattice point emits 16 int64:
 * A1..A5, C12,C13,C14,C15,C23,C24,C25,C34,C35,C45, sign */
#define RT5_TUP 16

/* The number of int64 a box needs for the genus-5 lattice: (2*box+1)^5 points,
 * RT5_TUP int64 each. The caller sizes its out[] from this (no malloc here). */
size_t srmech_riemann_theta_g5_count(uint32_t box)
{
    size_t side = (size_t)box * 2u + 1u;
    assert(RT5_TUP == 16);
    assert(side >= 1u);
    return side * side * side * side * side * (size_t)RT5_TUP;
}

/* The per-term genus-5 sign (-1)^{e1 n1 + ... + e5 n5}: Class-K pin-slot (a stored
 * +1/-1 from an explicit parity branch), never an ALU abs(). e[5], n[5]. */
static int rt5_term_sign(const int64_t *e, const int64_t *n)
{
    int64_t parity;
    assert(e != NULL);
    assert(n != NULL);
    parity = (e[0] * n[0] + e[1] * n[1] + e[2] * n[2]
              + e[3] * n[3] + e[4] * n[4]) % 2;
    if (parity < 0) {
        parity += 2;                                /* floor-mod into {0,1} */
    }
    return (parity == 0) ? 1 : -1;                  /* Class-K +-1, no abs() */
}

/* Write one genus-5 16-tuple [A1..A5, C12..C45, sign] from the cleared coords
 * u[5] = 2 n_i + ep'_i and the per-term Class-K sign into out[idx .. idx+15]. */
static void rt5_emit(int64_t *out, size_t idx, const int64_t *u, int sign)
{
    assert(out != NULL);
    assert(u != NULL);
    out[idx + 0u] = u[0] * u[0];        /* A1 */
    out[idx + 1u] = u[1] * u[1];        /* A2 */
    out[idx + 2u] = u[2] * u[2];        /* A3 */
    out[idx + 3u] = u[3] * u[3];        /* A4 */
    out[idx + 4u] = u[4] * u[4];        /* A5 */
    out[idx + 5u] = u[0] * u[1];        /* C12 */
    out[idx + 6u] = u[0] * u[2];        /* C13 */
    out[idx + 7u] = u[0] * u[3];        /* C14 */
    out[idx + 8u] = u[0] * u[4];        /* C15 */
    out[idx + 9u] = u[1] * u[2];        /* C23 */
    out[idx + 10u] = u[1] * u[3];       /* C24 */
    out[idx + 11u] = u[1] * u[4];       /* C25 */
    out[idx + 12u] = u[2] * u[3];       /* C34 */
    out[idx + 13u] = u[2] * u[4];       /* C35 */
    out[idx + 14u] = u[3] * u[4];       /* C45 */
    out[idx + 15u] = (int64_t)sign;
}

/* Emit the genus-5 theta-constant exponent lattice for characteristic
 * [ep1..ep5; e1..e5] (each bit in {0,1}) over the box |n_i| <= box, as a flat
 * caller-owned int64 array of [A1..A5,C12,C13,C14,C15,C23,C24,C25,C34,C35,C45,sign]
 * 16-tuples in row-major (n1,n2,n3,n4,n5) order. *out_len <- the number of int64 written
 * (= the g5 count). SRMECH_ERR_BAD_INPUT if any characteristic bit is not in {0,1};
 * SRMECH_ERR_OVERFLOW if the caller out[] (out_cap int64) is too small. */
srmech_status_t srmech_riemann_theta_g5_lattice(
    int ep1, int ep2, int ep3, int ep4, int ep5,
    int e1, int e2, int e3, int e4, int e5, uint32_t box,
    int64_t *out, size_t out_cap, size_t *out_len)
{
    size_t need, idx;
    int64_t n1, n2, n3, n4, n5, lo, hi, u[5], nn[5];
    const int64_t ev[5] = {(int64_t)e1, (int64_t)e2, (int64_t)e3,
                           (int64_t)e4, (int64_t)e5};
    assert(out != NULL);
    assert(out_len != NULL);
    if (!rt_bit_ok(ep1) || !rt_bit_ok(ep2) || !rt_bit_ok(ep3) || !rt_bit_ok(ep4)
            || !rt_bit_ok(ep5) || !rt_bit_ok(e1) || !rt_bit_ok(e2)
            || !rt_bit_ok(e3) || !rt_bit_ok(e4) || !rt_bit_ok(e5)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    need = srmech_riemann_theta_g5_count(box);
    if (need > out_cap) {
        return SRMECH_ERR_OVERFLOW;
    }
    idx = 0u;
    lo = -(int64_t)box;
    hi = (int64_t)box;
    for (n1 = lo; n1 <= hi; ++n1) {
        u[0] = 2 * n1 + (int64_t)ep1; nn[0] = n1;
        for (n2 = lo; n2 <= hi; ++n2) {
            u[1] = 2 * n2 + (int64_t)ep2; nn[1] = n2;
            for (n3 = lo; n3 <= hi; ++n3) {
                u[2] = 2 * n3 + (int64_t)ep3; nn[2] = n3;
                for (n4 = lo; n4 <= hi; ++n4) {
                    u[3] = 2 * n4 + (int64_t)ep4; nn[3] = n4;
                    for (n5 = lo; n5 <= hi; ++n5) {
                        u[4] = 2 * n5 + (int64_t)ep5; nn[4] = n5;
                        rt5_emit(out, idx, u, rt5_term_sign(ev, nn));
                        idx += (size_t)RT5_TUP;
                    }
                }
            }
        }
    }
    assert(idx == need);
    *out_len = idx;
    return SRMECH_OK;
}

/* ================================================================== *
 *  rc85: the genus-4 Sp(8,Z) MODULAR ACTION KIT -- the C peers of
 *  srmech.amsc.riemann_theta.RiemannThetaG4.{transform, goepel_holds} (the g=3->g=4
 *  parametric extension of the rc77/rc78 genus-3 peers). gamma is the 64 int64 entries
 *  (A,B,C,D 4x4 blocks row-major); 4-vectors over an 8x8 symplectic gamma. Caller-owned
 *  out[] / caller arena; no malloc. Additive symbols -> ABI unchanged (stays 3).
 * ================================================================== */

/* gamma[64] = A,B,C,D 4x4 blocks row-major; one block entry M_blk[r][c]. */
static int64_t rt4_g(const int64_t *gamma, int blk, int r, int c)
{
    assert(gamma != NULL);
    assert(blk >= 0 && blk < 4 && r >= 0 && r < 4 && c >= 0 && c < 4);
    return gamma[(size_t)blk * 16u + (size_t)r * 4u + (size_t)c];
}

/* (M v)_row for a 4x4 block M of gamma and a length-4 vector v. */
static int64_t rt4_matvec(const int64_t *gamma, int blk, const int64_t *v, int row)
{
    int c;
    int64_t acc = 0;
    assert(gamma != NULL && v != NULL);
    assert(row >= 0 && row < 4);
    for (c = 0; c < 4; ++c) { acc += rt4_g(gamma, blk, row, c) * v[c]; }
    return acc;
}

/* diag(P Q^T)_row = sum_k P[row][k] Q[row][k]  (the row-row dot of two 4x4 blocks). */
static int64_t rt4_diag_pqt(const int64_t *gamma, int pblk, int qblk, int row)
{
    int k;
    int64_t acc = 0;
    assert(gamma != NULL);
    assert(row >= 0 && row < 4);
    for (k = 0; k < 4; ++k) {
        acc += rt4_g(gamma, pblk, row, k) * rt4_g(gamma, qblk, row, k);
    }
    return acc;
}

/* (P^T Q)[i][j] = sum_k P[k][i] Q[k][j]  -- one entry of a transposed-times block. */
static int64_t rt4_ptq(const int64_t *gamma, int pblk, int qblk, int i, int j)
{
    int k;
    int64_t acc = 0;
    assert(gamma != NULL);
    assert(i >= 0 && i < 4 && j >= 0 && j < 4);
    for (k = 0; k < 4; ++k) {
        acc += rt4_g(gamma, pblk, k, i) * rt4_g(gamma, qblk, k, j);
    }
    return acc;
}

/* (P Q^T)[i][j] = sum_k P[i][k] Q[j][k]  -- one entry of a block-times-transposed. */
static int64_t rt4_pqt(const int64_t *gamma, int pblk, int qblk, int i, int j)
{
    int k;
    int64_t acc = 0;
    assert(gamma != NULL);
    assert(i >= 0 && i < 4 && j >= 0 && j < 4);
    for (k = 0; k < 4; ++k) {
        acc += rt4_g(gamma, pblk, i, k) * rt4_g(gamma, qblk, j, k);
    }
    return acc;
}

/* The symplectic check gamma J gamma^T = J via the exact block conditions
 * A^T C = C^T A (symmetric), B^T D = D^T B (symmetric), A^T D - C^T B = I (4x4).
 * Returns 1 if symplectic, else 0. (blk 0=A,1=B,2=C,3=D.) */
static int rt4_is_symplectic(const int64_t *gamma)
{
    int i, j, ok = 1;
    assert(gamma != NULL);
    for (i = 0; i < 4; ++i) {
        for (j = 0; j < 4; ++j) {
            /* A^T C symmetric, B^T D symmetric */
            if (rt4_ptq(gamma, 0, 2, i, j) != rt4_ptq(gamma, 0, 2, j, i)) { ok = 0; }
            if (rt4_ptq(gamma, 1, 3, i, j) != rt4_ptq(gamma, 1, 3, j, i)) { ok = 0; }
            /* A^T D - C^T B == I */
            if (rt4_ptq(gamma, 0, 3, i, j) - rt4_ptq(gamma, 2, 1, i, j)
                    != ((i == j) ? 1 : 0)) { ok = 0; }
        }
    }
    assert(ok == 0 || ok == 1);
    return ok;
}

/* The exact 8*phi_m Igusa phase at genus 4 (an integer; the multiplier exponent is
 * (8*phi_m) mod 8). epp = ep' (4), eps = ep (4). The SAME expression as g2/g3 one
 * genus up:
 *   8*phi_m = -4 ep'^T(B D^T)ep' + 8 ep^T(A^TC)ep - 16 ep'^T(B^TC)ep
 *             - 8 diag(A B^T)^T (D ep' - C ep). */
static int64_t rt4_eight_phi(const int64_t *gamma,
                             const int64_t *epp, const int64_t *eps)
{
    int i, j;
    int64_t t1 = 0, t2 = 0, t3 = 0, t4 = 0, depp[4], ceps[4], dab;
    assert(gamma != NULL);
    assert(epp != NULL && eps != NULL);
    for (i = 0; i < 4; ++i) {
        for (j = 0; j < 4; ++j) {
            t1 += epp[i] * rt4_pqt(gamma, 1, 3, i, j) * epp[j];  /* ep'^T(B D^T)ep' */
            t2 += eps[i] * rt4_ptq(gamma, 0, 2, i, j) * eps[j];  /* ep^T(A^TC)ep */
            t3 += epp[i] * rt4_ptq(gamma, 1, 2, i, j) * eps[j];  /* ep'^T(B^TC)ep */
        }
    }
    for (i = 0; i < 4; ++i) {
        depp[i] = rt4_matvec(gamma, 3, epp, i);     /* (D ep')_i */
        ceps[i] = rt4_matvec(gamma, 2, eps, i);     /* (C ep)_i */
    }
    for (i = 0; i < 4; ++i) {
        dab = rt4_diag_pqt(gamma, 0, 1, i);          /* diag(A B^T)_i */
        t4 += dab * (depp[i] - ceps[i]);
    }
    return -4 * t1 + 8 * t2 - 16 * t3 - 8 * t4;
}

/* The exact genus-4 Sp(8,Z) characteristic transformation + the kappa 8th-root
 * exponent. gamma[64] = A,B,C,D 4x4 blocks (row-major). out_char[8] <-
 * (ep1',ep2',ep3',ep4',e1',e2',e3',e4') bits; *kexp <- the multiplier exponent k in
 * {0..7} (multiplier = zeta_8^k). SRMECH_ERR_BAD_INPUT if a bit is invalid or gamma is
 * not symplectic. */
srmech_status_t srmech_riemann_theta_g4_sp8_char(
    const int64_t *gamma, int ep1, int ep2, int ep3, int ep4,
    int e1, int e2, int e3, int e4, int *out_char, int *kexp)
{
    int i;
    int64_t epp[4], eps[4], npp, nep, k8;
    assert(gamma != NULL);
    assert(out_char != NULL && kexp != NULL);
    if (!rt_bit_ok(ep1) || !rt_bit_ok(ep2) || !rt_bit_ok(ep3) || !rt_bit_ok(ep4)
            || !rt_bit_ok(e1) || !rt_bit_ok(e2) || !rt_bit_ok(e3)
            || !rt_bit_ok(e4)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (!rt4_is_symplectic(gamma)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    epp[0] = ep1; epp[1] = ep2; epp[2] = ep3; epp[3] = ep4;
    eps[0] = e1;  eps[1] = e2;  eps[2] = e3;  eps[3] = e4;
    for (i = 0; i < 4; ++i) {
        /* ep' |-> D ep' - C ep + diag(C D^T) */
        npp = rt4_matvec(gamma, 3, epp, i) - rt4_matvec(gamma, 2, eps, i)
            + rt4_diag_pqt(gamma, 2, 3, i);
        /* ep  |-> -B ep' + A ep + diag(A B^T) */
        nep = rt4_matvec(gamma, 0, eps, i) - rt4_matvec(gamma, 1, epp, i)
            + rt4_diag_pqt(gamma, 0, 1, i);
        out_char[i] = (int)(((npp % 2) + 2) % 2);
        out_char[i + 4] = (int)(((nep % 2) + 2) % 2);
    }
    k8 = rt4_eight_phi(gamma, epp, eps);
    *kexp = (int)(((k8 % 8) + 8) % 8);              /* floor-mod into {0..7} */
    return SRMECH_OK;
}

/* one genus-4 eighth-nome lattice point emits 11 int64:
 * A1,A2,A3,A4,C12,C13,C14,C23,C24,C34,sign (same shape as the g4 quarter-nome lattice) */
#define RT4_EIGHTH_TUP 11

/* The per-term genus-4 eighth-nome sign (-1)^{e.n}: Class-K pin-slot, never abs(). */
static int rt4_eighth_sign(int64_t e1, int64_t e2, int64_t e3, int64_t e4,
                           int64_t n1, int64_t n2, int64_t n3, int64_t n4)
{
    int64_t parity = (e1 * n1 + e2 * n2 + e3 * n3 + e4 * n4) % 2;
    assert((e1 == 0 || e1 == 1) && (e2 == 0 || e2 == 1));
    assert((e3 == 0 || e3 == 1) && (e4 == 0 || e4 == 1));
    if (parity < 0) {
        parity += 2;                                /* floor-mod into {0,1} */
    }
    return (parity == 0) ? 1 : -1;                  /* Class-K +-1, no abs() */
}

/* The number of int64 the genus-4 eighth-nome lattice needs: (2*box+1)^4 points,
 * RT4_EIGHTH_TUP int64 each. No malloc. */
size_t srmech_riemann_theta_g4_eighth_count(uint32_t box)
{
    size_t side = (size_t)box * 2u + 1u;
    assert(RT4_EIGHTH_TUP == 11);
    assert(side >= 1u);
    return side * side * side * side * (size_t)RT4_EIGHTH_TUP;
}

/* Emit the genus-4 eighth-nome [A1..A4,C12,C13,C14,C23,C24,C34,sign] 11-tuple lattice
 * for the DOUBLED upper characteristic s=(s1..s4) + lower char (e1..e4), at Omega
 * (at_two_omega=0: A=2(2n+s)^2 ...) or 2Omega (at_two_omega=1: A=(4n+s)^2 ...) over
 * |n_i|<=box, row-major; *out_len <- int64 written. SRMECH_ERR_BAD_INPUT if a lower-char
 * bit is invalid; SRMECH_ERR_OVERFLOW if out[] is too small. */
srmech_status_t srmech_riemann_theta_g4_eighth_lattice(
    int s1, int s2, int s3, int s4, int e1, int e2, int e3, int e4,
    int at_two_omega, uint32_t box, int64_t *out, size_t out_cap, size_t *out_len)
{
    size_t need, idx;
    int64_t n1, n2, n3, n4, lo, hi, u1, u2, u3, u4, m, step;
    assert(out != NULL);
    assert(out_len != NULL);
    if (!rt_bit_ok(e1) || !rt_bit_ok(e2) || !rt_bit_ok(e3) || !rt_bit_ok(e4)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    need = srmech_riemann_theta_g4_eighth_count(box);
    if (need > out_cap) {
        return SRMECH_ERR_OVERFLOW;
    }
    m = at_two_omega ? 1 : 2;                        /* Omega scales A,C by 2 */
    step = at_two_omega ? 4 : 2;
    idx = 0u;
    lo = -(int64_t)box;
    hi = (int64_t)box;
    for (n1 = lo; n1 <= hi; ++n1) { u1 = step * n1 + (int64_t)s1;
    for (n2 = lo; n2 <= hi; ++n2) { u2 = step * n2 + (int64_t)s2;
    for (n3 = lo; n3 <= hi; ++n3) { u3 = step * n3 + (int64_t)s3;
    for (n4 = lo; n4 <= hi; ++n4) { u4 = step * n4 + (int64_t)s4;
        out[idx + 0u] = m * u1 * u1;            /* A1 */
        out[idx + 1u] = m * u2 * u2;            /* A2 */
        out[idx + 2u] = m * u3 * u3;            /* A3 */
        out[idx + 3u] = m * u4 * u4;            /* A4 */
        out[idx + 4u] = m * u1 * u2;            /* C12 */
        out[idx + 5u] = m * u1 * u3;            /* C13 */
        out[idx + 6u] = m * u1 * u4;            /* C14 */
        out[idx + 7u] = m * u2 * u3;            /* C23 */
        out[idx + 8u] = m * u2 * u4;            /* C24 */
        out[idx + 9u] = m * u3 * u4;            /* C34 */
        out[idx + 10u] = (int64_t)rt4_eighth_sign(
            (int64_t)e1, (int64_t)e2, (int64_t)e3, (int64_t)e4, n1, n2, n3, n4);
        idx += (size_t)RT4_EIGHTH_TUP;
    } } } }
    assert(idx == need);
    *out_len = idx;
    return SRMECH_OK;
}

/* ------------------------------------------------------------------ *
 * rc85: the genus-4 GÖPEL universal quadratic theta-null relation gate -- the C peer of
 * srmech.amsc.riemann_theta.RiemannThetaG4.goepel_holds. A 4-PAIR / 8-NULL same-Omega
 * relation theta^2[a]theta^2[b] = theta^2[c]theta^2[d] + theta^2[e]theta^2[f]
 * - theta^2[g]theta^2[h] among eight even nulls all summing to [1,1,1,1;1,1,1,1] (a
 * genus-4 Goepel/azygetic system). The genus-4 instance of the same goepel_holds surface
 * g2/g3 expose (the Riemann theta relation among theta squares -- Glass, Compositio Math
 * 40 (1980); Fiorentino-Salvati Manni SIGMA 16 (2020) 057; Igusa Theta Functions (1972)
 * SS IV/V; van der Geer SMF Degree 2&3). Holds for ALL Omega; decided EXACTLY on the
 * box-stable safe inner region (each A_i, |C_ij| <= box^2). Caller arena (one int64
 * work[] sized via the count helper); no malloc. Additive symbols -> ABI stays 3. ------ */

/* one g4 Goepel lattice monomial = 11 int64: A1,A2,A3,A4,C12,C13,C14,C23,C24,C34,coeff */
#define G4_GOEPEL_TUP 11

/* The number of signed pairs in the genus-4 Goepel relation (an 8-PAIR / 16-NULL
 * same-Omega relation; genus 2 is 3-pair, genus 3 is 4-pair). */
#define G4_GOEPEL_NPAIR 8

/* The sixteen even-null characteristics (ep'1..ep'4, e1..e4) of the canonical genus-4
 * Goepel relation, in pair order (2 nulls per pair; all sum to [1,1,1,1;1,1,1,1]).
 * Byte-identical to the Python RiemannThetaG4._G4_GOEPEL_PAIRS. */
static const int g4_goepel_chars[16][8] = {
    {0, 0, 0, 0, 0, 1, 0, 1}, {1, 1, 1, 1, 1, 0, 1, 0},   /* pair 0  (+) */
    {0, 0, 0, 0, 0, 1, 1, 0}, {1, 1, 1, 1, 1, 0, 0, 1},   /* pair 1  (-) */
    {0, 0, 0, 0, 1, 0, 0, 1}, {1, 1, 1, 1, 0, 1, 1, 0},   /* pair 2  (+) */
    {0, 0, 0, 0, 1, 0, 1, 0}, {1, 1, 1, 1, 0, 1, 0, 1},   /* pair 3  (-) */
    {0, 0, 0, 1, 0, 1, 0, 0}, {1, 1, 1, 0, 1, 0, 1, 1},   /* pair 4  (-) */
    {0, 0, 0, 1, 1, 0, 0, 0}, {1, 1, 1, 0, 0, 1, 1, 1},   /* pair 5  (-) */
    {0, 0, 1, 0, 0, 1, 0, 0}, {1, 1, 0, 1, 1, 0, 1, 1},   /* pair 6  (+) */
    {0, 0, 1, 0, 1, 0, 0, 0}, {1, 1, 0, 1, 0, 1, 1, 1},   /* pair 7  (+) */
};

/* The per-pair residual sign (residual = Sum sign*pair == 0). Pair 0..7. */
static const int g4_goepel_pair_sign[8] = {1, -1, 1, -1, -1, -1, 1, 1};

/* A compiled-in safety ceiling for one accumulator (box up to ~4); not a malloc.
 * box=3 default: diag-square ~ a few hundred, residual a few thousand. */
#define G4_GOEPEL_CAP 200000

/* The number of int64 the caller arena needs. THREE buffers: two diag-square scratch +
 * one residual accumulator, each G4_GOEPEL_CAP monomials * G4_GOEPEL_TUP int64. */
size_t srmech_riemann_theta_g4_goepel_count(uint32_t box)
{
    (void)box;                                      /* arena is box-independent (capped) */
    assert(G4_GOEPEL_TUP == 11);
    assert(G4_GOEPEL_CAP >= 1000u);
    return (size_t)3u * (size_t)G4_GOEPEL_CAP * (size_t)G4_GOEPEL_TUP;
}

/* Merge one g4 monomial (key0..key9, coeff) into buf[0..*len) (in monomials), summing a
 * duplicate key. SRMECH_ERR_OVERFLOW if a new key would exceed cap monomials. */
static srmech_status_t g4_goepel_accum(int64_t *buf, size_t *len, size_t cap,
                                       const int64_t *key, int64_t coeff)
{
    size_t i, base, t;
    int same;
    assert(buf != NULL && len != NULL);
    assert(key != NULL);
    for (i = 0u; i < *len; ++i) {
        base = i * (size_t)G4_GOEPEL_TUP;
        same = 1;
        for (t = 0u; t < 10u; ++t) {
            if (buf[base + t] != key[t]) { same = 0; }
        }
        if (same) {
            buf[base + 10u] += coeff;                /* merge duplicate key */
            return SRMECH_OK;
        }
    }
    if (*len >= cap) {
        return SRMECH_ERR_OVERFLOW;
    }
    base = (*len) * (size_t)G4_GOEPEL_TUP;
    for (t = 0u; t < 10u; ++t) {
        buf[base + t] = key[t];
    }
    buf[base + 10u] = coeff;
    *len += 1u;
    return SRMECH_OK;
}

/* Build one even null's DIAGONAL-RESTRICTED squared g4 lattice into sq[]/(*slen): the
 * self-convolution of theta[null](Omega) keeping ONLY monomials with each A_i <= bound
 * (sound pre-restrict). The per-term sign is (-1)^{e.n} * (-1)^{e.m} (Class-K). */
static srmech_status_t g4_goepel_diag_square(const int *ch, int64_t box, int64_t bound,
                                             int64_t *sq, size_t *slen, size_t cap)
{
    int64_t n[4], mm[4], un[4], um[4], key[10];
    int64_t ep[4], e[4];
    int sgn_n, sgn_m, d, ok;
    srmech_status_t st;
    assert(sq != NULL && slen != NULL);
    assert(box >= 0 && bound >= 0);
    for (d = 0; d < 4; ++d) { ep[d] = ch[d]; e[d] = ch[d + 4]; }
    *slen = 0u;
    for (n[0] = -box; n[0] <= box; ++n[0]) {
    for (n[1] = -box; n[1] <= box; ++n[1]) {
    for (n[2] = -box; n[2] <= box; ++n[2]) {
    for (n[3] = -box; n[3] <= box; ++n[3]) {
        for (d = 0; d < 4; ++d) { un[d] = 2 * n[d] + ep[d]; }
        sgn_n = rt4_term_sign(e[0], e[1], e[2], e[3], n[0], n[1], n[2], n[3]);
        for (mm[0] = -box; mm[0] <= box; ++mm[0]) {
        for (mm[1] = -box; mm[1] <= box; ++mm[1]) {
        for (mm[2] = -box; mm[2] <= box; ++mm[2]) {
        for (mm[3] = -box; mm[3] <= box; ++mm[3]) {
            for (d = 0; d < 4; ++d) { um[d] = 2 * mm[d] + ep[d]; }
            ok = 1;
            for (d = 0; d < 4; ++d) {
                key[d] = un[d] * un[d] + um[d] * um[d];
                if (key[d] > bound) { ok = 0; }
            }
            if (ok) {
                key[4] = un[0] * un[1] + um[0] * um[1];   /* C12 */
                key[5] = un[0] * un[2] + um[0] * um[2];   /* C13 */
                key[6] = un[0] * un[3] + um[0] * um[3];   /* C14 */
                key[7] = un[1] * un[2] + um[1] * um[2];   /* C23 */
                key[8] = un[1] * un[3] + um[1] * um[3];   /* C24 */
                key[9] = un[2] * un[3] + um[2] * um[3];   /* C34 */
                sgn_m = rt4_term_sign(e[0], e[1], e[2], e[3],
                                      mm[0], mm[1], mm[2], mm[3]);
                st = g4_goepel_accum(sq, slen, cap, key, (int64_t)(sgn_n * sgn_m));
                if (st != SRMECH_OK) { return st; }
            }
        } } } }
    } } } }
    return SRMECH_OK;
}

/* Accumulate (sign) * [ theta^2[na] * theta^2[nb] restricted to the safe region ] into
 * the residual res[]/(*rlen). sqa/sqb are the two diag-restricted squares; only output
 * monomials with each A_i <= bound AND |C_ij| <= bound are accumulated. */
static srmech_status_t g4_goepel_pair_into_res(const int64_t *sqa, size_t alen,
                                               const int64_t *sqb, size_t blen,
                                               int sign, int64_t bound,
                                               int64_t *res, size_t *rlen, size_t cap)
{
    size_t i, j, ia, ib, t;
    int64_t key[10], m;
    int ok;
    srmech_status_t st;
    assert(sqa != NULL && sqb != NULL);
    assert(res != NULL && rlen != NULL);
    for (i = 0u; i < alen; ++i) { ia = i * (size_t)G4_GOEPEL_TUP;
        for (j = 0u; j < blen; ++j) { ib = j * (size_t)G4_GOEPEL_TUP;
            ok = 1;
            for (t = 0u; t < 4u; ++t) {
                key[t] = sqa[ia + t] + sqb[ib + t];
                if (key[t] > bound) { ok = 0; }
            }
            for (t = 4u; t < 10u; ++t) {
                key[t] = sqa[ia + t] + sqb[ib + t];
                m = (key[t] >= 0) ? key[t] : -key[t];     /* Class-K magnitude */
                if (m > bound) { ok = 0; }
            }
            if (ok) {
                st = g4_goepel_accum(res, rlen, cap, key,
                                     (int64_t)sign * sqa[ia + 10u] * sqb[ib + 10u]);
                if (st != SRMECH_OK) { return st; }
            }
        }
    }
    return SRMECH_OK;
}

/* Scan the residual for a genuine genus-4 cross-term (C14, C24 or C34 != 0 with nonzero
 * coeff). Returns 1 if present, else 0. */
static int g4_goepel_res_has_cross(const int64_t *res, size_t rlen)
{
    size_t i, base;
    int has = 0;
    assert(res != NULL);
    assert(rlen <= (size_t)G4_GOEPEL_CAP);
    for (i = 0u; i < rlen; ++i) {
        base = i * (size_t)G4_GOEPEL_TUP;
        if (res[base + 10u] != 0
                && (res[base + 6u] != 0 || res[base + 8u] != 0
                    || res[base + 9u] != 0)) {       /* C14,C24,C34 */
            has = 1;
        }
    }
    return has;
}

/* DECIDE the genus-4 Goepel relation gate. work[] is the caller arena (work_cap int64,
 * >= srmech_riemann_theta_g4_goepel_count(box)); *out_holds <- 1 iff LHS==RHS on the safe
 * region (residual empty), *out_has_cross <- 1 iff a genuine genus-4 cross-term monomial
 * (C14, C24 or C34 != 0) is present in the LHS safe region. SRMECH_ERR_BAD_INPUT on
 * box<2 / undersized work; SRMECH_ERR_OVERFLOW on an over-cap accumulator. */
srmech_status_t srmech_riemann_theta_g4_goepel(
    uint32_t box, int64_t *work, size_t work_cap,
    int *out_holds, int *out_has_cross)
{
    int64_t *sqa, *sqb, *res, bnd;
    size_t alen, blen, rlen, half, i, base;
    int p, holds;
    srmech_status_t st;
    assert(work != NULL);
    assert(out_holds != NULL && out_has_cross != NULL);
    if (box < 2u || work_cap < srmech_riemann_theta_g4_goepel_count(box)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    half = (size_t)G4_GOEPEL_CAP * (size_t)G4_GOEPEL_TUP;
    sqa = work; sqb = work + half; res = work + 2u * half;
    bnd = (int64_t)box * (int64_t)box;              /* the box-stable safe bound */
    rlen = 0u;
    for (p = 0; p < G4_GOEPEL_NPAIR; ++p) {          /* eight signed pairs */
        st = g4_goepel_diag_square(g4_goepel_chars[2 * p], (int64_t)box, bnd,
                                   sqa, &alen, (size_t)G4_GOEPEL_CAP);
        if (st != SRMECH_OK) { return st; }
        st = g4_goepel_diag_square(g4_goepel_chars[2 * p + 1], (int64_t)box, bnd,
                                   sqb, &blen, (size_t)G4_GOEPEL_CAP);
        if (st != SRMECH_OK) { return st; }
        st = g4_goepel_pair_into_res(sqa, alen, sqb, blen, g4_goepel_pair_sign[p], bnd,
                                     res, &rlen, (size_t)G4_GOEPEL_CAP);
        if (st != SRMECH_OK) { return st; }
    }
    holds = 1;                                       /* residual must vanish (LHS==RHS) */
    for (i = 0u; i < rlen; ++i) {
        base = i * (size_t)G4_GOEPEL_TUP;
        if (res[base + 10u] != 0) { holds = 0; }     /* nonzero coeff -> not exact */
    }
    /* cross-term presence: re-derive the LHS-only safe region (pair 0) and check C14/24/34 */
    st = g4_goepel_diag_square(g4_goepel_chars[0], (int64_t)box, bnd,
                               sqa, &alen, (size_t)G4_GOEPEL_CAP);
    if (st != SRMECH_OK) { return st; }
    st = g4_goepel_diag_square(g4_goepel_chars[1], (int64_t)box, bnd,
                               sqb, &blen, (size_t)G4_GOEPEL_CAP);
    if (st != SRMECH_OK) { return st; }
    rlen = 0u;
    st = g4_goepel_pair_into_res(sqa, alen, sqb, blen, 1, bnd,
                                 res, &rlen, (size_t)G4_GOEPEL_CAP);
    if (st != SRMECH_OK) { return st; }
    *out_holds = holds;
    *out_has_cross = g4_goepel_res_has_cross(res, rlen);
    return SRMECH_OK;
}

/* ------------------------------------------------------------------ *
 * rc81 (the GENUS-4 CAPSTONE): the SCHOTTKY FORM J = theta^4(E8+E8) - theta^4(E16)
 * representation-number COUNTER -- the C peer of
 * srmech.amsc.riemann_theta.SchottkyFormG4.{_count_gram_py, _full_shell_grams_py}.
 *
 * The Schottky form J (weight-8 degree-4 level-1 Siegel CUSP form; Schottky 1888,
 * Igusa 1981, Poor-Yuen 1996) is the difference of the genus-4 theta-SERIES of the two
 * rank-16 even-unimodular lattices E8+E8 and E16=D16+. Organized by the Gram matrix T of
 * a g-tuple of lattice vectors, J's coefficient at T is the EXACT INTEGER representation-
 * number difference r_{E8+E8}(T) - r_{E16}(T). This kernel COUNTS r_L(T) over the MINIMAL
 * shell (norm-2 vectors; the leading part of J) for one lattice, given the lattice's
 * minimal (doubled) vectors as a flat int64 array. In the doubled-integer model a real
 * coordinate is *2, so a half-integer lattice coord is an EXACT odd integer and the
 * doubled inner product <2u,2v> = 4<u,v> is exactly the q_ij quarter-nome exponent C_ij
 * (diagonal 8 = norm 2). The off-diagonal doubled inners lie in {-8,-4,0,4,8} (real in
 * {-2,-1,0,1,2}, Cauchy-Schwarz on norm-2 vectors) -> 5 value classes.
 *
 * The count is a pure NON-NEGATIVE INTEGER tally (no sign, so NO abs()). It walks the
 * inner-value BITSET table S[i][class] (the indices j with <i,j> in that class) -- the
 * Class-L adjacency-by-inner-value -- intersecting + popcounting per the Gram pattern,
 * exactly mirroring the Python bitset walk. The table is the CALLER ARENA (no malloc):
 * n * 5 * RTSCH_WORDS uint64 (RTSCH_WORDS = ceil(n/64)) + 2 scratch bitsets. Two ops:
 *   srmech_riemann_theta_g4_schottky_count -- ONE prescribed off-Gram (genus 1/2/3/4);
 *   srmech_riemann_theta_g4_schottky_shell -- the FULL single-pass off-Gram histogram
 *     emitted as flat [off_1..off_k, count] rows (k = g(g-1)/2).
 * Additive symbols -> ABI stays 3.
 *
 * JPL Power-of-Ten: Rule 1 (no goto/recursion: iterative flat helpers),
 *   Rule 2 (bounded loops: n, the 5 classes, the word count), Rule 3 (no malloc:
 *   caller arena), Rule 4 (<=60 lines/func), Rule 5 (>=2 asserts/fn), Rule 7
 *   (status propagated), Rule 8 (no multi-line macros), Rule 10 (warnings clean).
 * ------------------------------------------------------------------ */

/* the 5 off-diagonal doubled inner-product value classes for the minimal shell */
#define RTSCH_NCLASS 5
/* max minimal vectors we size for: 480 (E8+E8 / D16+) -> 8 uint64 words; headroom 16 */
#define RTSCH_MAX_WORDS 16

/* forward declarations (Rule 1: no recursion). Single-line so the JPL Rule-4/5 scanner
 * skips them as declarations (it skips only `;`-terminated lines). */
static int rtsch_class_of(int64_t t);
static int64_t rtsch_inner(const int64_t *vecs, size_t dim, size_t i, size_t j);
static size_t rtsch_words(size_t n);
static unsigned rtsch_ctz(uint64_t x);
static void rtsch_build_table(const int64_t *v, size_t n, size_t d, uint64_t *t, size_t w);
static int64_t rtsch_popcount_words(const uint64_t *w, size_t words);
static const uint64_t *rtsch_row(const uint64_t *tbl, size_t i, int cls, size_t words);
static int64_t rtsch_count_g2(const uint64_t *tbl, size_t n, size_t words, int c0);
static int64_t rtsch_count_g3(const uint64_t *t, size_t n, size_t w, int a, int b, int c);
static int64_t rtsch_count_g4(const uint64_t *t, size_t n, size_t w, int a, int b, int c, int d, int e, int f, uint64_t *s);
static int64_t rtsch_class_val(int cls);
static int64_t rtsch_shell_count_pat(const uint64_t *t, size_t n, size_t w, int g, const int *c, uint64_t *s);

/* map a doubled off-diagonal inner product to its class index 0..4, or -1 if it is
 * outside the minimal shell {-8,-4,0,4,8} (then the count is 0). */
static int rtsch_class_of(int64_t t)
{
    assert(RTSCH_NCLASS == 5);
    switch (t) {
    case -8: return 0;
    case -4: return 1;
    case  0: return 2;
    case  4: return 3;
    case  8: return 4;
    default: return -1;
    }
}

/* the exact-integer DOUBLED inner product <2v_i, 2v_j> = 4<v_i, v_j> (the q_ij
 * quarter-nome exponent). Bounded dot (Rule 2), no float, no abs(). */
static int64_t rtsch_inner(const int64_t *vecs, size_t dim, size_t i, size_t j)
{
    size_t d;
    int64_t acc = 0;
    const int64_t *vi = vecs + i * dim;
    const int64_t *vj = vecs + j * dim;
    assert(vecs != NULL);
    assert(dim > 0u);
    for (d = 0u; d < dim; ++d) {
        acc += vi[d] * vj[d];
    }
    return acc;
}

/* the number of uint64 words a bitset over n indices needs (ceil(n/64)). */
static size_t rtsch_words(size_t n)
{
    assert(n > 0u);
    assert(RTSCH_MAX_WORDS == 16);
    return (n + 63u) / 64u;
}

/* the row of the bitset table for vector i, class cls (the indices j with <i,j> in
 * that class). */
static const uint64_t *rtsch_row(const uint64_t *tbl, size_t i, int cls, size_t words)
{
    assert(tbl != NULL);
    assert(cls >= 0 && cls < RTSCH_NCLASS);
    return tbl + (i * (size_t)RTSCH_NCLASS + (size_t)cls) * words;
}

/* build the inner-value bitset table tbl[(i*5 + cls)*words + w]. */
static void rtsch_build_table(const int64_t *vecs, size_t n, size_t dim,
                              uint64_t *tbl, size_t words)
{
    size_t i, j, idx, total;
    int cls;
    assert(tbl != NULL);
    assert(words <= (size_t)RTSCH_MAX_WORDS);
    total = n * (size_t)RTSCH_NCLASS * words;
    for (idx = 0u; idx < total; ++idx) {
        tbl[idx] = 0u;
    }
    for (i = 0u; i < n; ++i) {
        for (j = 0u; j < n; ++j) {
            cls = rtsch_class_of(rtsch_inner(vecs, dim, i, j));
            if (cls >= 0) {
                idx = (i * (size_t)RTSCH_NCLASS + (size_t)cls) * words + (j / 64u);
                tbl[idx] |= ((uint64_t)1u << (j % 64u));
            }
        }
    }
}

/* popcount over a multi-word bitset. Bounded (Rule 2), exact non-negative tally. */
static int64_t rtsch_popcount_words(const uint64_t *w, size_t words)
{
    size_t k;
    int64_t total = 0;
    uint64_t x;
    assert(w != NULL);
    assert(words <= (size_t)RTSCH_MAX_WORDS);
    for (k = 0u; k < words; ++k) {
        x = w[k];
        while (x != 0u) {
            x &= (x - 1u);                       /* clear the lowest set bit */
            ++total;
        }
    }
    return total;
}

/* genus-2 count: sum_i popcount(S[i][c0]). */
static int64_t rtsch_count_g2(const uint64_t *tbl, size_t n, size_t words, int c0)
{
    size_t i;
    int64_t total = 0;
    assert(tbl != NULL);
    assert(c0 >= 0 && c0 < RTSCH_NCLASS);
    for (i = 0u; i < n; ++i) {
        total += rtsch_popcount_words(rtsch_row(tbl, i, c0, words), words);
    }
    return total;
}

/* genus-3 count: sum over (i, j in S[i][c0]) popcount(S[i][c1] & S[j][c2]). */
static int64_t rtsch_count_g3(const uint64_t *tbl, size_t n, size_t words,
                              int c0, int c1, int c2)
{
    size_t i, jw;
    int64_t total = 0;
    const uint64_t *Sic0, *Sic1, *Sjc2;
    uint64_t bits;
    assert(tbl != NULL);
    assert(c0 >= 0 && c1 >= 0 && c2 >= 0);
    for (i = 0u; i < n; ++i) {
        Sic0 = rtsch_row(tbl, i, c0, words);
        Sic1 = rtsch_row(tbl, i, c1, words);
        for (jw = 0u; jw < words; ++jw) {
            bits = Sic0[jw];
            while (bits != 0u) {
                size_t j = jw * 64u + (size_t)rtsch_ctz(bits);
                size_t kw;
                bits &= (bits - 1u);
                Sjc2 = rtsch_row(tbl, j, c2, words);
                for (kw = 0u; kw < words; ++kw) {
                    uint64_t inter = Sic1[kw] & Sjc2[kw];
                    while (inter != 0u) {
                        inter &= (inter - 1u);
                        ++total;
                    }
                }
            }
        }
    }
    return total;
}

/* genus-4 count: sum over (i, j in S[i][c0], k in S[i][c1] & S[j][c3])
 *   popcount(S[i][c2] & S[j][c4] & S[k][c5]). scratch is one `words` bitset. */
static int64_t rtsch_count_g4(const uint64_t *tbl, size_t n, size_t words,
                              int c0, int c1, int c2, int c3, int c4, int c5,
                              uint64_t *scratch)
{
    size_t i, jw, kw, w;
    int64_t total = 0;
    uint64_t jbits, kbits;
    assert(tbl != NULL);
    assert(scratch != NULL);
    for (i = 0u; i < n; ++i) {
        const uint64_t *Sic0 = rtsch_row(tbl, i, c0, words);
        const uint64_t *Sic1 = rtsch_row(tbl, i, c1, words);
        const uint64_t *Sic2 = rtsch_row(tbl, i, c2, words);
        for (jw = 0u; jw < words; ++jw) {
            jbits = Sic0[jw];
            while (jbits != 0u) {
                size_t j = jw * 64u + (size_t)rtsch_ctz(jbits);
                const uint64_t *Sjc3 = rtsch_row(tbl, j, c3, words);
                const uint64_t *Sjc4 = rtsch_row(tbl, j, c4, words);
                jbits &= (jbits - 1u);
                for (w = 0u; w < words; ++w) {
                    scratch[w] = Sic1[w] & Sjc3[w];      /* k candidates */
                }
                for (kw = 0u; kw < words; ++kw) {
                    kbits = scratch[kw];
                    while (kbits != 0u) {
                        size_t k = kw * 64u + (size_t)rtsch_ctz(kbits);
                        const uint64_t *Skc5 = rtsch_row(tbl, k, c5, words);
                        size_t lw;
                        kbits &= (kbits - 1u);
                        for (lw = 0u; lw < words; ++lw) {
                            uint64_t lb = Sic2[lw] & Sjc4[lw] & Skc5[lw];
                            while (lb != 0u) {
                                lb &= (lb - 1u);
                                ++total;
                            }
                        }
                    }
                }
            }
        }
    }
    return total;
}

/* count-trailing-zeros of a nonzero uint64 (the lowest set-bit index). */
static unsigned rtsch_ctz(uint64_t x)
{
    unsigned c = 0u;
    assert(x != 0u);
    while ((x & 1u) == 0u) {
        x >>= 1;
        ++c;
    }
    return c;
}

/* The caller-arena uint64 count the count/shell ops need: the bitset table
 * (n*5*words) plus one scratch bitset (words). */
size_t srmech_riemann_theta_g4_schottky_arena(size_t n)
{
    size_t words;
    assert(RTSCH_NCLASS == 5);
    assert(RTSCH_MAX_WORDS == 16);
    if (n == 0u) {
        return 1u;
    }
    words = (n + 63u) / 64u;
    return n * (size_t)RTSCH_NCLASS * words + words;
}

/* Count ordered g-tuples of minimal (doubled) vectors vecs[n*dim] whose OFF-DIAGONAL
 * doubled Gram is gram_off[k] (k = g(g-1)/2 for genus in {1,2,3,4}; the diagonal is 8 =
 * norm 2). *out_count <- the exact non-negative count. arena (arena_cap uint64) is the
 * caller bitset table + scratch (>= srmech_riemann_theta_g4_schottky_arena(n)).
 * SRMECH_ERR_BAD_INPUT: unsupported genus, n=0/dim=0, or n > RTSCH_MAX_WORDS*64, or an
 * off-Gram value outside {-8,-4,0,4,8}; SRMECH_ERR_OVERFLOW: arena too small;
 * SRMECH_ERR_NULL_ARG: NULL pointers. */
srmech_status_t srmech_riemann_theta_g4_schottky_count(
    const int64_t *vecs, size_t n, size_t dim, int genus,
    const int64_t *gram_off, uint64_t *arena, size_t arena_cap,
    int64_t *out_count)
{
    size_t words;
    int c[6];
    int k, noff;
    if (vecs == NULL || arena == NULL || out_count == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (genus < 1 || genus > 4 || n == 0u || dim == 0u
            || n > (size_t)RTSCH_MAX_WORDS * 64u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    noff = genus * (genus - 1) / 2;
    assert(noff >= 0 && noff <= 6);              /* g(g-1)/2 for g in {1..4} */
    assert(genus >= 1 && genus <= 4);
    if (noff > 0 && gram_off == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (arena_cap < srmech_riemann_theta_g4_schottky_arena(n)) {
        return SRMECH_ERR_OVERFLOW;
    }
    for (k = 0; k < noff; ++k) {
        c[k] = rtsch_class_of(gram_off[k]);
        if (c[k] < 0) {                          /* off-shell value -> 0 reps */
            *out_count = 0;
            return SRMECH_ERR_BAD_INPUT;
        }
    }
    words = rtsch_words(n);
    rtsch_build_table(vecs, n, dim, arena, words);
    if (genus == 1) {
        *out_count = (int64_t)n;
    } else if (genus == 2) {
        *out_count = rtsch_count_g2(arena, n, words, c[0]);
    } else if (genus == 3) {
        *out_count = rtsch_count_g3(arena, n, words, c[0], c[1], c[2]);
    } else {
        *out_count = rtsch_count_g4(arena, n, words, c[0], c[1], c[2],
                                    c[3], c[4], c[5],
                                    arena + n * (size_t)RTSCH_NCLASS * words);
    }
    return SRMECH_OK;
}

/* The off-diagonal doubled value for class index 0..4 (the inverse of rtsch_class_of):
 * {0:-8, 1:-4, 2:0, 3:4, 4:8}. */
static int64_t rtsch_class_val(int cls)
{
    static const int64_t vals[RTSCH_NCLASS] = {-8, -4, 0, 4, 8};
    assert(cls >= 0 && cls < RTSCH_NCLASS);
    assert(RTSCH_NCLASS == 5);
    return vals[cls];
}

/* Count for one class-pattern with the bitset table ALREADY built (the shell op's
 * per-pattern step; reuses the genus counters; scratch is the genus-4 k-candidate
 * bitset = the arena tail). genus in {1,2,3,4}. */
static int64_t rtsch_shell_count_pat(const uint64_t *tbl, size_t n, size_t words,
                                     int genus, const int *cls, uint64_t *scratch)
{
    assert(tbl != NULL);
    assert(genus >= 1 && genus <= 4);
    if (genus == 1) {
        return (int64_t)n;
    }
    if (genus == 2) {
        return rtsch_count_g2(tbl, n, words, cls[0]);
    }
    if (genus == 3) {
        return rtsch_count_g3(tbl, n, words, cls[0], cls[1], cls[2]);
    }
    return rtsch_count_g4(tbl, n, words, cls[0], cls[1], cls[2], cls[3], cls[4],
                          cls[5], scratch);
}

/* The number of int64 the shell op's out[] needs: at most 5^(genus*(genus-1)/2) rows,
 * each (genus*(genus-1)/2 off-values + 1 count). genus in {1,2,3,4}. */
size_t srmech_riemann_theta_g4_schottky_shell_count(int genus)
{
    size_t noff, rows, k;
    assert(RTSCH_NCLASS == 5);
    if (genus < 1 || genus > 4) {
        return 0u;
    }
    noff = (size_t)(genus * (genus - 1) / 2);
    assert(noff <= 6u);
    rows = 1u;
    for (k = 0u; k < noff; ++k) {
        rows *= (size_t)RTSCH_NCLASS;
    }
    return rows * (noff + 1u);
}

/* The FULL minimal-shell off-Gram HISTOGRAM for one lattice: emit, for every off-Gram
 * class-pattern with a NONZERO count, the row [off_1..off_noff, count] (off values the
 * doubled inners in {-8,-4,0,4,8}). *out_len <- the number of int64 written. The pattern
 * is enumerated by mixed-radix over the 5 classes; each count reuses the rtsch counters
 * (the bitset table is built ONCE). arena per srmech_riemann_theta_g4_schottky_arena(n).
 * Mirrors srmech.amsc.riemann_theta.SchottkyFormG4._full_shell_grams_py. */
srmech_status_t srmech_riemann_theta_g4_schottky_shell(
    const int64_t *vecs, size_t n, size_t dim, int genus,
    uint64_t *arena, size_t arena_cap, int64_t *out, size_t out_cap,
    size_t *out_len)
{
    size_t words, noff, total_pat, pat, w, idx;
    int cls[6];
    int64_t cnt;
    if (vecs == NULL || arena == NULL || out == NULL || out_len == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (genus < 1 || genus > 4 || n == 0u || dim == 0u
            || n > (size_t)RTSCH_MAX_WORDS * 64u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (arena_cap < srmech_riemann_theta_g4_schottky_arena(n)) {
        return SRMECH_ERR_OVERFLOW;
    }
    assert(genus >= 1 && genus <= 4);
    assert(out_cap > 0u);
    words = rtsch_words(n);
    rtsch_build_table(vecs, n, dim, arena, words);
    noff = (size_t)(genus * (genus - 1) / 2);
    total_pat = 1u;
    for (w = 0u; w < noff; ++w) {
        total_pat *= (size_t)RTSCH_NCLASS;
    }
    idx = 0u;
    for (pat = 0u; pat < total_pat; ++pat) {
        size_t t = pat;
        for (w = 0u; w < noff; ++w) {
            cls[w] = (int)(t % (size_t)RTSCH_NCLASS);
            t /= (size_t)RTSCH_NCLASS;
        }
        cnt = rtsch_shell_count_pat(arena, n, words, genus, cls,
                                    arena + n * (size_t)RTSCH_NCLASS * words);
        if (cnt != 0) {
            if (idx + noff + 1u > out_cap) {
                return SRMECH_ERR_OVERFLOW;
            }
            for (w = 0u; w < noff; ++w) {
                out[idx + w] = rtsch_class_val(cls[w]);
            }
            out[idx + noff] = cnt;
            idx += noff + 1u;
        }
    }
    *out_len = idx;
    return SRMECH_OK;
}

/* ------------------------------------------------------------------ *
 * rc107: the generic SPARSE SAFE-SUPPORT GATE DECISION kernel — the ONE C peer of
 * ALL the genus-axis theta identity/distinctness gates (g in {2..5}) of
 * srmech.amsc.riemann_theta (duplication_holds / addition_holds / goepel_holds +
 * the *_is_distinct_* gates) — the #707 dive's SAFE-REGION PUSH-DOWN.
 *
 * The mathematics (the soundness argument, same as the shipped _diag_restrict):
 * every gate compares two signed sums of theta-lattice PRODUCTS only on the safe
 * inner region {A_i <= safe, |C_ij| <= safe}. The diagonal exponents A_i are
 * non-negative squares and ADD under the lattice convolution, so a product
 * monomial inside the safe region can only come from factor monomials each with
 * A_i <= safe — each factor is therefore enumerated DIRECTLY on its safe support
 * {u : dc*u^2 <= safe} (the exact safe region of the INFINITE theta series —
 * box-parameter-free) and the convolutions carry a diagonal-additivity guard.
 * The compared (restricted) lattices are BIT-IDENTICAL to the dense
 * box-enumerate-then-restrict path (the rc107 bit-identity tests re-prove it).
 *
 * Wire format (int32 spec; the Python side is the SSOT of the pair/syzygy data):
 *   per comparison: [n_lhs, n_rhs] then (n_lhs + n_rhs) products
 *   per product:    [sign(+-1), n_factors(2 or 4)] then the factor specs
 *   per factor:     [dc, step, a[0..g-1], e[0..g-1]]   (2 + 2g int32)
 * A factor's terms are u_i = step*n_i + a_i with diagonal dc*u_i^2, cross
 * dc*u_i*u_j, and the Class-K pin-slot sign (-1)^{e.n} (explicit +-1 branch,
 * never an ALU abs()). Per comparison: accumulate LHS products (hash table)
 * -> out_cross[c] (a surviving genus-g cross monomial C_{i,g} != 0), subtract
 * RHS products -> out_equal[c] (residual vanishes <=> LHS == RHS as zero-dropped
 * dicts). restrict_crosses=0 is the diagonal-only (_diag_restrict-shaped) mode
 * of the distinctness gates.
 *
 * Caller-arena: ONE int64 work[] (sized via srmech_riemann_theta_gate_count)
 * holding the MAIN accumulator hash table + four aux tables (2 factor + 2
 * intermediate), each slot [used, key(n), coeff], n = g + g(g-1)/2. Per-genus
 * compiled caps (the GOEPEL_CAP precedent); a cap overflow returns
 * SRMECH_ERR_OVERFLOW (overflow-not-wrap) and the caller falls to the pure
 * sparse body. No malloc. Additive symbols -> ABI unchanged (stays 3).
 *
 * JPL: Rule 1 (no goto/recursion) OK; Rule 2 (bounded loops — supports capped at
 * RTGATE_SUP_MAX per coordinate, probes capped at the table size, spec parsing
 * bounds-checked) OK; Rule 3 (no malloc) OK; Rule 4 (<=60 lines/fn) OK; Rule 5
 * (>=2 asserts/fn) OK; Rule 7 (status propagated) OK; Rule 8 (no fn-like
 * macros) OK.
 * ------------------------------------------------------------------ */

#define RTGATE_MAX_G 5u
#define RTGATE_MAX_N 15u                /* g + g(g-1)/2 at g = 5 */
#define RTGATE_AUX_SLOTS 8192u          /* factor/intermediate table slots (pow2) */
#define RTGATE_SUP_MAX 256u             /* per-coordinate safe-support ceiling */
#define RTGATE_MAX_PRODS 64u            /* per-side product ceiling (dup g5 = 32) */

/* The MAIN accumulator hash-table slot count for genus g (powers of two; sized
 * from the measured safe-region key counts at the shipped gate boxes with >2x
 * headroom: g2 dup box8 = 4772, g3 dup box4 = 14833, g4 dup box2 = 3747 (box3 =
 * 89109 exceeds the cap -> pure path), g5 dup box2 = 47254). */
static size_t rtgate_main_slots(uint32_t g)
{
    assert(g >= 2u && g <= RTGATE_MAX_G);
    assert((RTGATE_AUX_SLOTS & (RTGATE_AUX_SLOTS - 1u)) == 0u);
    if (g == 2u) { return 32768u; }
    if (g == 5u) { return 131072u; }
    return 65536u;                      /* g3, g4 */
}

size_t srmech_riemann_theta_gate_count(uint32_t g)
{
    size_t n, stride;
    assert(RTGATE_MAX_N == RTGATE_MAX_G + RTGATE_MAX_G * (RTGATE_MAX_G - 1u) / 2u);
    assert(RTGATE_SUP_MAX >= 2u);
    if (g < 2u || g > RTGATE_MAX_G) {
        return 0u;
    }
    n = (size_t)g + (size_t)g * ((size_t)g - 1u) / 2u;
    stride = n + 2u;                    /* [used, key(n), coeff] */
    return (rtgate_main_slots(g) + 4u * (size_t)RTGATE_AUX_SLOTS) * stride;
}

/* FNV-1a over the n int64 key slots + a final avalanche — the hash-table index
 * source. Deterministic; the table order never reaches the verdict (only the
 * all-zero / cross-presence scans do). */
static uint64_t rtgate_hash(const int64_t *key, size_t n)
{
    uint64_t h = 1469598103934665603ULL;
    size_t i;
    assert(key != NULL);
    assert(n >= 3u && n <= (size_t)RTGATE_MAX_N);
    for (i = 0u; i < n; ++i) {
        h ^= (uint64_t)key[i];
        h *= 1099511628211ULL;
    }
    h ^= h >> 29;
    h *= 0xbf58476d1ce4e5b9ULL;
    h ^= h >> 32;
    return h;
}

/* Clear a table's used flags (key/coeff slots may stay stale — never read while
 * unused). Bounded loop over the slots (JPL Rule 2). */
static void rtgate_reset(int64_t *tab, size_t slots, size_t stride)
{
    size_t i;
    assert(tab != NULL);
    assert(slots > 0u && stride >= 5u && stride <= (size_t)RTGATE_MAX_N + 2u);
    for (i = 0u; i < slots; ++i) {
        tab[i * stride] = 0;
    }
}

/* Merge one monomial (key, coeff) into a hash table (linear probing; load
 * ceiling 1/2 -> SRMECH_ERR_OVERFLOW, overflow-not-wrap). */
static srmech_status_t rtgate_accum(int64_t *tab, size_t slots, size_t n,
                                    const int64_t *key, int64_t coeff,
                                    size_t *count)
{
    size_t stride = n + 2u, probe, i;
    uint64_t idx;
    int64_t *slot;
    int match;
    assert(tab != NULL && key != NULL && count != NULL);
    assert(slots >= 8u && (slots & (slots - 1u)) == 0u);
    idx = rtgate_hash(key, n) & (uint64_t)(slots - 1u);
    for (probe = 0u; probe < slots; ++probe) {
        slot = tab + (size_t)((idx + (uint64_t)probe) & (uint64_t)(slots - 1u)) * stride;
        if (slot[0] == 0) {
            if ((*count + 1u) * 2u > slots) {
                return SRMECH_ERR_OVERFLOW;   /* load ceiling — caller falls pure */
            }
            slot[0] = 1;
            for (i = 0u; i < n; ++i) { slot[1u + i] = key[i]; }
            slot[1u + n] = coeff;
            *count += 1u;
            return SRMECH_OK;
        }
        match = 1;
        for (i = 0u; i < n; ++i) {
            if (slot[1u + i] != key[i]) { match = 0; break; }
        }
        if (match == 1) {
            slot[1u + n] += coeff;
            return SRMECH_OK;
        }
    }
    return SRMECH_ERR_OVERFLOW;               /* unreachable below the ceiling */
}

/* Exact integer floor square root (Newton, integer-only — no libm/float): the
 * safe-support radius. */
static int64_t rtgate_isqrt(int64_t v)
{
    int64_t x, y;
    assert(v >= 0);
    if (v == 0) { return 0; }
    x = v;
    y = (x + 1) / 2;
    while (y < x) {
        x = y;
        y = (x + v / x) / 2;
    }
    assert(x >= 0 && x <= v && x * x <= v);
    return x;
}

/* Build the per-coordinate SAFE SUPPORTS of one factor spec fs = [dc, step,
 * a[0..g-1], e[0..g-1]]: su[i][] <- the u values with u = step*n + a_i and
 * dc*u^2 <= safe; sn[i][] <- the matching n-PARITY bits (the Class-K sign
 * source); ns[i] <- the count. The exact safe support of the INFINITE theta
 * series — no box parameter. */
static srmech_status_t rtgate_supports(uint32_t g, int64_t safe,
                                       const int32_t *fs,
                                       int32_t su[][RTGATE_SUP_MAX],
                                       int32_t sn[][RTGATE_SUP_MAX],
                                       size_t *ns)
{
    int64_t dc = (int64_t)fs[0], step = (int64_t)fs[1], umax, u, a, e;
    size_t i, c;
    assert(fs != NULL && ns != NULL);
    assert(g >= 2u && g <= RTGATE_MAX_G);
    if ((dc != 1 && dc != 2) || (step != 2 && step != 4) || safe < 0) {
        return SRMECH_ERR_BAD_INPUT;
    }
    umax = rtgate_isqrt(safe / dc);
    for (i = 0u; i < (size_t)g; ++i) {
        a = (int64_t)fs[2u + i];
        e = (int64_t)fs[2u + (size_t)g + i];
        if ((e != 0 && e != 1) || a < -16 || a > 16) {
            return SRMECH_ERR_BAD_INPUT;
        }
        c = 0u;
        for (u = -umax; u <= umax; ++u) {
            if ((u - a) % step != 0 || dc * u * u > safe) {
                continue;
            }
            if (c >= (size_t)RTGATE_SUP_MAX) {
                return SRMECH_ERR_BAD_INPUT;  /* support ceiling (safe too big) */
            }
            su[i][c] = (int32_t)u;
            sn[i][c] = (int32_t)((((u - a) / step) % 2 + 2) % 2);
            c += 1u;
        }
        ns[i] = c;
    }
    return SRMECH_OK;
}

/* Enumerate one sparse theta FACTOR into a (reset) hash table: a bounded
 * odometer over the per-coordinate safe supports; per point the key
 * (dc*u_i^2 .., dc*u_i*u_j ..) and the Class-K sign (-1)^{e.n}. */
static srmech_status_t rtgate_factor(uint32_t g, int64_t safe, const int32_t *fs,
                                     int64_t *tab, size_t slots, size_t *count)
{
    int32_t su[RTGATE_MAX_G][RTGATE_SUP_MAX];
    int32_t sn[RTGATE_MAX_G][RTGATE_SUP_MAX];
    size_t ns[RTGATE_MAX_G], i, j, k, idx, total, flat, rem;
    size_t n = (size_t)g + (size_t)g * ((size_t)g - 1u) / 2u;
    int64_t u[RTGATE_MAX_G], key[RTGATE_MAX_N], dc, par, coeff;
    srmech_status_t st;
    assert(tab != NULL && count != NULL);
    assert(fs != NULL && g >= 2u && g <= RTGATE_MAX_G);
    st = rtgate_supports(g, safe, fs, su, sn, ns);
    if (st != SRMECH_OK) { return st; }
    rtgate_reset(tab, slots, n + 2u);
    *count = 0u;
    dc = (int64_t)fs[0];
    total = 1u;
    for (i = 0u; i < (size_t)g; ++i) {
        if (ns[i] == 0u) { return SRMECH_OK; }    /* empty support, empty factor */
        total *= ns[i];
    }
    for (flat = 0u; flat < total; ++flat) {
        rem = flat;
        par = 0;
        for (i = (size_t)g; i > 0u; --i) {
            idx = rem % ns[i - 1u];
            rem /= ns[i - 1u];
            u[i - 1u] = (int64_t)su[i - 1u][idx];
            par += (int64_t)fs[2u + (size_t)g + (i - 1u)] * (int64_t)sn[i - 1u][idx];
        }
        coeff = ((par % 2) == 0) ? 1 : -1;        /* Class-K pin-slot, never abs() */
        k = 0u;
        for (i = 0u; i < (size_t)g; ++i) { key[k] = dc * u[i] * u[i]; k += 1u; }
        for (i = 0u; i < (size_t)g; ++i) {
            for (j = i + 1u; j < (size_t)g; ++j) { key[k] = dc * u[i] * u[j]; k += 1u; }
        }
        st = rtgate_accum(tab, slots, n, key, coeff, count);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* Guarded lattice convolution ta x tb -> out (+= sign * coeff products): the
 * DIAGONAL-ADDITIVITY GUARD (each diagonal sum <= safe — sound: diagonals are
 * non-negative and additive) always applies; final_crosses != 0 additionally
 * applies the |C_ij| <= safe cut (the full safe region; a per-key filter, so
 * applying it during accumulation == restricting afterwards). Zero-coefficient
 * entries are skipped (they contribute nothing — the dicts' zero-drop). */
static srmech_status_t rtgate_conv(uint32_t g, int64_t safe, int final_crosses,
                                   int64_t sign, const int64_t *ta, size_t sa,
                                   const int64_t *tb, size_t sb,
                                   int64_t *out, size_t out_slots,
                                   size_t *out_count)
{
    size_t n = (size_t)g + (size_t)g * ((size_t)g - 1u) / 2u;
    size_t stride = n + 2u, ia, ib, i;
    int64_t key[RTGATE_MAX_N], m;
    const int64_t *ra, *rb;
    int ok;
    srmech_status_t st;
    assert(ta != NULL && tb != NULL && out != NULL);
    assert(out_count != NULL && (sign == 1 || sign == -1));
    for (ia = 0u; ia < sa; ++ia) {
        ra = ta + ia * stride;
        if (ra[0] == 0 || ra[1u + n] == 0) { continue; }
        for (ib = 0u; ib < sb; ++ib) {
            rb = tb + ib * stride;
            if (rb[0] == 0 || rb[1u + n] == 0) { continue; }
            ok = 1;
            for (i = 0u; i < (size_t)g; ++i) {
                key[i] = ra[1u + i] + rb[1u + i];
                if (key[i] > safe) { ok = 0; break; }
            }
            for (i = (size_t)g; ok == 1 && i < n; ++i) {
                key[i] = ra[1u + i] + rb[1u + i];
                if (final_crosses != 0) {
                    m = (key[i] >= 0) ? key[i] : -key[i];  /* Class-K, no abs() */
                    if (m > safe) { ok = 0; }
                }
            }
            if (ok == 0) { continue; }
            st = rtgate_accum(out, out_slots, n, key,
                              sign * ra[1u + n] * rb[1u + n], out_count);
            if (st != SRMECH_OK) { return st; }
        }
    }
    return SRMECH_OK;
}

/* Accumulate ONE product spec ps = [sign, nf, factors...] into the main table
 * with overall sign (sign_mul * ps.sign). nf == 2: one guarded convolution;
 * nf == 4 (the Goepel theta^2[a]*theta^2[b] shape): pair the squares first —
 * intermediates carry the diagonal guard only (sound by additivity), the LAST
 * convolution applies the requested final restriction. f1/f2/ta/tb are the aux
 * tables (RTGATE_AUX_SLOTS each). */
static srmech_status_t rtgate_product(uint32_t g, int64_t safe, int final_crosses,
                                      int64_t sign_mul, const int32_t *ps,
                                      int64_t *f1, int64_t *f2,
                                      int64_t *ta, int64_t *tb,
                                      int64_t *main_tab, size_t main_slots,
                                      size_t *main_count)
{
    size_t n = (size_t)g + (size_t)g * ((size_t)g - 1u) / 2u;
    size_t fstride = 2u + 2u * (size_t)g, c1, c2, ca, cb;
    size_t aux = (size_t)RTGATE_AUX_SLOTS;
    int64_t sign = (int64_t)ps[0];
    int32_t nf = ps[1];
    srmech_status_t st;
    assert(ps != NULL && main_tab != NULL && main_count != NULL);
    assert(f1 != NULL && f2 != NULL && ta != NULL && tb != NULL);
    if ((sign != 1 && sign != -1) || (nf != 2 && nf != 4)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    sign = sign * sign_mul;
    st = rtgate_factor(g, safe, ps + 2u, f1, aux, &c1);
    if (st != SRMECH_OK) { return st; }
    st = rtgate_factor(g, safe, ps + 2u + fstride, f2, aux, &c2);
    if (st != SRMECH_OK) { return st; }
    if (nf == 2) {
        return rtgate_conv(g, safe, final_crosses, sign, f1, aux, f2, aux,
                           main_tab, main_slots, main_count);
    }
    rtgate_reset(ta, aux, n + 2u);
    ca = 0u;
    st = rtgate_conv(g, safe, 0, 1, f1, aux, f2, aux, ta, aux, &ca);
    if (st != SRMECH_OK) { return st; }
    st = rtgate_factor(g, safe, ps + 2u + 2u * fstride, f1, aux, &c1);
    if (st != SRMECH_OK) { return st; }
    st = rtgate_factor(g, safe, ps + 2u + 3u * fstride, f2, aux, &c2);
    if (st != SRMECH_OK) { return st; }
    rtgate_reset(tb, aux, n + 2u);
    cb = 0u;
    st = rtgate_conv(g, safe, 0, 1, f1, aux, f2, aux, tb, aux, &cb);
    if (st != SRMECH_OK) { return st; }
    return rtgate_conv(g, safe, final_crosses, sign, ta, aux, tb, aux,
                       main_tab, main_slots, main_count);
}

/* 1 iff a surviving (coeff != 0) monomial in the table carries a GENUS-g
 * cross-term C_{i,g} != 0 (a pair slot whose second index is the last
 * coordinate) — the per-gate "genuinely genus-g" cross check. */
static int rtgate_scan_cross(uint32_t g, const int64_t *tab, size_t slots)
{
    size_t n = (size_t)g + (size_t)g * ((size_t)g - 1u) / 2u;
    size_t stride = n + 2u, s, i, j, p;
    int is_gc[RTGATE_MAX_N];
    const int64_t *row;
    int has = 0;
    assert(tab != NULL);
    assert(g >= 2u && g <= RTGATE_MAX_G);
    p = (size_t)g;
    for (i = 0u; i < (size_t)g; ++i) {
        for (j = i + 1u; j < (size_t)g; ++j) {
            is_gc[p] = (j == (size_t)g - 1u) ? 1 : 0;
            p += 1u;
        }
    }
    for (s = 0u; s < slots && has == 0; ++s) {
        row = tab + s * stride;
        if (row[0] == 0 || row[1u + n] == 0) { continue; }
        for (i = (size_t)g; i < n; ++i) {
            if (is_gc[i] == 1 && row[1u + i] != 0) { has = 1; break; }
        }
    }
    return has;
}

/* 1 iff every used slot's coefficient is zero (the residual vanishes — the two
 * zero-dropped sides are equal). */
static int rtgate_scan_zero(uint32_t g, const int64_t *tab, size_t slots)
{
    size_t n = (size_t)g + (size_t)g * ((size_t)g - 1u) / 2u;
    size_t stride = n + 2u, s;
    assert(tab != NULL);
    assert(g >= 2u && g <= RTGATE_MAX_G);
    for (s = 0u; s < slots; ++s) {
        if (tab[s * stride] != 0 && tab[s * stride + 1u + n] != 0) {
            return 0;
        }
    }
    return 1;
}

/* Parse + accumulate ONE side (n_prods products) of a comparison from the spec
 * at *pos (bounds-checked), with the side's overall sign_mul (+1 LHS / -1 RHS). */
static srmech_status_t rtgate_side(uint32_t g, int64_t safe, int final_crosses,
                                   int64_t sign_mul, const int32_t *spec,
                                   size_t spec_len, size_t *pos, uint32_t n_prods,
                                   int64_t *f1, int64_t *f2, int64_t *ta, int64_t *tb,
                                   int64_t *main_tab, size_t main_slots,
                                   size_t *main_count)
{
    size_t fstride = 2u + 2u * (size_t)g, need;
    uint32_t p;
    int32_t nf;
    srmech_status_t st;
    assert(spec != NULL && pos != NULL);
    assert(main_tab != NULL && main_count != NULL);
    if (n_prods == 0u || n_prods > RTGATE_MAX_PRODS) {
        return SRMECH_ERR_BAD_INPUT;
    }
    for (p = 0u; p < n_prods; ++p) {
        if (*pos + 2u > spec_len) {
            return SRMECH_ERR_BAD_INPUT;
        }
        nf = spec[*pos + 1u];
        if (nf != 2 && nf != 4) {
            return SRMECH_ERR_BAD_INPUT;
        }
        need = 2u + (size_t)nf * fstride;
        if (*pos + need > spec_len) {
            return SRMECH_ERR_BAD_INPUT;
        }
        st = rtgate_product(g, safe, final_crosses, sign_mul, spec + *pos,
                            f1, f2, ta, tb, main_tab, main_slots, main_count);
        if (st != SRMECH_OK) { return st; }
        *pos += need;
    }
    return SRMECH_OK;
}

srmech_status_t srmech_riemann_theta_gate_decide(
    uint32_t g, int64_t safe, uint32_t restrict_crosses,
    const int32_t *spec, size_t spec_len, uint32_t n_comparisons,
    int64_t *work, size_t work_cap,
    int32_t *out_equal, int32_t *out_cross)
{
    size_t n, stride, main_slots, aux, pos, main_count;
    int64_t *main_tab, *f1, *f2, *ta, *tb;
    uint32_t c, n_lhs, n_rhs;
    int fc;
    srmech_status_t st;
    assert(out_equal != NULL && out_cross != NULL);
    assert(work != NULL || work_cap == 0u);
    if (g < 2u || g > RTGATE_MAX_G || safe < 0 || n_comparisons == 0u
            || spec == NULL || work == NULL
            || work_cap < srmech_riemann_theta_gate_count(g)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    n = (size_t)g + (size_t)g * ((size_t)g - 1u) / 2u;
    stride = n + 2u;
    main_slots = rtgate_main_slots(g);
    aux = (size_t)RTGATE_AUX_SLOTS * stride;
    main_tab = work;
    f1 = work + main_slots * stride;
    f2 = f1 + aux;
    ta = f2 + aux;
    tb = ta + aux;
    fc = (restrict_crosses != 0u) ? 1 : 0;
    pos = 0u;
    for (c = 0u; c < n_comparisons; ++c) {
        if (pos + 2u > spec_len) {
            return SRMECH_ERR_BAD_INPUT;
        }
        n_lhs = (uint32_t)spec[pos];
        n_rhs = (uint32_t)spec[pos + 1u];
        pos += 2u;
        rtgate_reset(main_tab, main_slots, stride);
        main_count = 0u;
        st = rtgate_side(g, safe, fc, 1, spec, spec_len, &pos, n_lhs,
                         f1, f2, ta, tb, main_tab, main_slots, &main_count);
        if (st != SRMECH_OK) { return st; }
        out_cross[c] = (int32_t)rtgate_scan_cross(g, main_tab, main_slots);
        st = rtgate_side(g, safe, fc, -1, spec, spec_len, &pos, n_rhs,
                         f1, f2, ta, tb, main_tab, main_slots, &main_count);
        if (st != SRMECH_OK) { return st; }
        out_equal[c] = (int32_t)rtgate_scan_zero(g, main_tab, main_slots);
    }
    if (pos != spec_len) {
        return SRMECH_ERR_BAD_INPUT;      /* trailing garbage in the spec */
    }
    return SRMECH_OK;
}
