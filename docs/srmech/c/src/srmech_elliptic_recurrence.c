/*
 * srmech_elliptic_recurrence.c -- the ELLIPTIC Sigma-row ORDER-1 RECURRENCE op for the
 * Frenkel-Turaev 8w7 summation (the C peer of
 * srmech.amsc.elliptic_recurrence.elliptic_recurrence_8w7). A 1:1 STRUCTURAL MIRROR of
 * the pure-Python recognize-decompose-construct pipeline -- NOT a coefficient nullspace
 * solve (which is provably dead for the elliptic case; the anti-brute-force discipline).
 *
 * Input: the 8w7 summand's TERM RATIO t(n+1)/t(n) = r(x) (x = q^n) as a full EllRatio
 * (a theta-quotient prod theta(a x;p)/prod theta(b x;p) over an exact-Q monomial
 * prefactor). The wire form mirrors srmech_elliptic_gosper: the interned symbol-table
 * dimension n_syms + the x/p/q/y interned indices + the num/den theta counts + the flat
 * exact-Q coeff arrays + the flat int32 exponent rows (in the order prefactor,
 * num0..K-1, den0..L-1).
 *
 * Output: when r is a canonical 8w7, the order-1 recurrence COEFFICIENT rho (a full
 * EllRatio in y = q^n: its prefactor exact-Q coeff + exponent row + the num/den
 * canonical theta-argument exponent rows) such that f(n+1) = rho(n)*f(n); else *out_has=0
 * (the honest out-of-class residue -> the Python re-decides on the pure path).
 *
 * The GENUINE pipeline (mirrors _elliptic_recurrence_8w7_pure exactly):
 *   (1) RECOGNIZE + DECOMPOSE the very-well-poised 8w7 (er_decompose_8w7): the unique
 *       den factor theta(a x^2) (x-exponent magnitude 2) gives the base a; the linear
 *       den factors theta(a q x u^-1) (x-exponent magnitude 1) give aq*real_base^-1 = u;
 *       drop the (q)-factor (u == a) + the y-carrying (n-dependent) params, leaving the
 *       three FREE params [b, c, d]. Out of class (no unique quadratic core, or != 3 free
 *       params) -> *out_has = 0.
 *   (2) CONSTRUCT rho (er_build_rho) from the elementary symmetric functions
 *       s2 = {bc, bd, cd}, s3 = bcd (Warnaar, Constr. Approx. 18 (2002) 479-502, Cor 2.2):
 *         num endpoints = {aq} U {aq/bc, aq/bd, aq/cd};  den = {aq/b, aq/c, aq/d} U {aq/bcd}
 *         rho = prod theta(end*y;p) over num endpoints / prod theta(end*y;p) over den.
 *       The construction IS the answer (decompose-and-compute, no undetermined-coeff solve).
 *
 * The VERIFICATION GATE (rho(n) == f(n+1)/f(n) for the 8w7 sum, the closed product form
 * the oracle) lives on the PYTHON side (it needs the truncated-theta EVAL oracle, exact-Q
 * but transcendental-valued at a sample point); the C peer constructs the EXACT rho and
 * the Python trusts it ONLY after rebuilding it byte-for-byte AND re-running the gate in
 * exact Q. A *out_has = 0 is NEVER a definitive "no recurrence" (the Python re-decides);
 * on any overflow/too-small-arena the peer returns SRMECH_ERR_OVERFLOW and the Python
 * re-runs its COMPLETE pure path.
 *
 * Reference (MPM-verified at build): S. Ole Warnaar, "Summation and transformation
 * formulas for elliptic hypergeometric series," Constr. Approx. 18 (2002) 479-502
 * (arXiv:math/0001006), Corollary 2.2 (the Frenkel-Turaev 8w7 summation; balancing
 * bcde = a^2 q^{n+1}).
 *
 * This is PURE COMPOSITION of the shared srmech_ellbase_* exact-Q monomial algebra
 * (mul / inv / copy / eq) + er_build (the EllRatio.__init__ mirror) -- the same single
 * copy srmech_elliptic_gosper / srmech_ellratio_is_elliptic / srmech_elliptic_lagrange
 * _basis ride. Malloc-free (JPL Rule 3): every working monomial / EllRatio / scratch is
 * carved from the caller arena `ws`. Byte-identical to the Python rho at ANY magnitude
 * (full bignum). The "magnitude 2 / magnitude 1" x-power test is a Class-K parity branch
 * (e == 2 || e == -2), never abs()/fabs().
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto/recursion): OK -- iterative, flat static helpers
 *   - Rule 2 (bounded loops)    : OK -- bounded by n_num / n_den / 3 free params
 *   - Rule 3 (no malloc)        : OK -- caller arena + caller out only
 *   - Rule 4 (<=60 lines/func)  : OK -- factored into static helpers
 *   - Rule 5 (>=2 asserts/fn)   : OK -- entry-pointer + pre/postcondition
 *   - Rule 7 (return-value)     : OK -- srmech_status_t propagated
 *   - Rule 8 (no multi-line mac): OK -- no function-like macros
 *   - Rule 10 (warnings clean)  : OK under -Wall -Wextra -Wpedantic -Werror
 *
 * Additive symbol -> ABI unchanged (stays 3). License: MIT.
 */

#include "srmech.h"
#include "srmech_ellbase_internal.h"

#include <assert.h>
#include <stdint.h>
#include <string.h>

/* The maximum theta-factor count the native scope handles per ratio. The canonical 8w7
 * has 7 num + 7 den (the VWP core + 5 Pochhammer pairs); after cancellation it stays
 * small. An over-cap input returns OK with *out_has = 0 and the Python decides. */
#define ER_MAX_THETA 32u
/* The number of free parameters a canonical 8w7 decomposes into (b, c, d). */
#define ER_N_FREE 3u

/* ---- shared-kernel aliases (the single copy lives in srmech_ellbase.c) ------- */
typedef srmech_ell_ctx_t       er_ctx_t;
typedef srmech_ell_mono_t      er_mono_t;
typedef srmech_ell_er_ratio_t  er_ratio_t;
typedef srmech_ell_er_scr_t    er_scr_t;

/* The working roster for the whole pipeline, carved once from the arena. */
typedef struct er_work {
    er_scr_t   s;                /* the EllRatio construction scratch         */
    er_mono_t *raw_num;          /* reusable raw num-arg arrays for er_build   */
    er_mono_t *raw_den;
    er_mono_t *cn;               /* er_build canon scratch                     */
    er_mono_t *cd;
    er_mono_t *tmp_mono;         /* ER_LOCAL_MONOS general scratch monomials   */
    er_mono_t *free_p;           /* the ER_N_FREE free params [b, c, d]        */
    er_mono_t  a_mono;           /* the base a                                 */
    er_mono_t  aq;               /* a * q                                      */
    er_mono_t  y;                /* symbol(y): coeff 1, y-exponent 1           */
    size_t     cap_arg;          /* per-array theta-arg capacity               */
} er_work_t;

#define ER_LOCAL_MONOS 16u

/* out := EllRatio(pref, num, den) canonical (er_build folds + cancels + sorts). */
static srmech_status_t er_er_build(er_ctx_t *c, er_work_t *w, er_ratio_t *out,
                                   const er_mono_t *pref, const er_mono_t *num,
                                   size_t n_num, const er_mono_t *den, size_t n_den,
                                   int psym)
{
    assert(c != NULL && w != NULL && out != NULL && pref != NULL);
    assert(n_num <= w->cap_arg && n_den <= w->cap_arg);
    return srmech_ellbase_er_build(c, out, pref, num, n_num, den, n_den, psym,
                                   &w->s, w->cn, w->cap_arg, w->cd, w->cap_arg);
}

/* The REAL base of a theta argument theta(b * x^k) (k == +-1 or +-2): strip the x-power,
 * then re-orient -- the canonicalization may have flipped theta(z)->theta(1/z), so a
 * NEGATIVE x-exponent means the stored arg is the inverse of the real base (invert back).
 * The orientation flip is the Class-K / Class-C chirality resolution (no abs()). */
static srmech_status_t er_real_base(er_ctx_t *c, er_mono_t *out, const er_mono_t *arg,
                                    int xsym, er_mono_t *tmp)
{
    int32_t k;
    srmech_status_t st;
    assert(c != NULL && out != NULL && arg != NULL && tmp != NULL);
    assert(xsym >= -1);
    k = (xsym >= 0) ? arg->exps[xsym] : 0;
    st = srmech_ellbase_mono_copy(c, tmp, arg);             /* core = arg with x stripped */
    if (st != SRMECH_OK) { return st; }
    if (xsym >= 0) { tmp->exps[xsym] = 0; }
    if (k > 0) { return srmech_ellbase_mono_copy(c, out, tmp); }
    return srmech_ellbase_mono_inv(c, out, tmp);            /* k < 0 -> the inverse base  */
}

/* True iff the canonical theta arg `arg` is an x-power of MAGNITUDE `mag` (the Class-K
 * sign branch e == mag || e == -mag, never abs()). `mag` is 1 (linear) or 2 (VWP core). */
static int er_is_x_power(const er_mono_t *arg, int xsym, int32_t mag)
{
    int32_t e;
    assert(arg != NULL);
    assert(mag == 1 || mag == 2);                      /* only the linear / VWP cores */
    if (xsym < 0) { return 0; }
    e = arg->exps[xsym];
    return (e == mag || e == -mag) ? 1 : 0;
}

/* Two monomials have the SAME exponent map (ignoring the coeff): mirrors the Python
 * `dict(u.exps) != dict(a_mono.exps)` filter that drops the (q)-factor (recovers u == a).
 * Compares the dense int32 exponent rows element-for-element (the coeff is not read). */
static int er_same_exps(const er_ctx_t *c, const er_mono_t *a, const er_mono_t *b)
{
    size_t i;
    assert(c != NULL && a != NULL && b != NULL);
    assert(c->n_syms >= 1u);                           /* the interned table is non-empty */
    for (i = 0; i < c->n_syms; i++) {
        if (a->exps[i] != b->exps[i]) { return 0; }
    }
    return 1;
}

/* RECOGNIZE + DECOMPOSE the very-well-poised 8w7 term-ratio r into the base a (w->a_mono),
 * aq (w->aq), and the ER_N_FREE free params (w->free_p[0..2]). *ok = 1 on a canonical 8w7;
 * *ok = 0 when out of class (no unique magnitude-2 quadratic core, or != 3 free params).
 * Mirrors _decompose_8w7: the linear (magnitude-1) den factors give u = aq*real_base^-1;
 * drop the (q)-factor (u == a) + the y-carrying n-dependent params (y-exponent != 0). */
static srmech_status_t er_decompose_8w7(er_ctx_t *c, er_work_t *w, const er_ratio_t *r,
                                        int xsym, int qsym, int ysym, int *ok)
{
    size_t i;
    size_t n_quad = 0;
    size_t n_free = 0;
    srmech_status_t st;
    assert(c != NULL && w != NULL && r != NULL && ok != NULL);
    assert(qsym >= 0);                                 /* q must be in the symbol table   */
    *ok = 0;
    for (i = 0; i < r->n_den; i++) {                   /* the unique VWP quadratic core   */
        if (er_is_x_power(&r->den[i], xsym, 2)) {
            n_quad++;
            st = er_real_base(c, &w->a_mono, &r->den[i], xsym, &w->tmp_mono[0]);
            if (st != SRMECH_OK) { return st; }
        }
    }
    if (n_quad != 1u) { return SRMECH_OK; }            /* no unique quadratic core -> out */
    st = srmech_ellbase_mono_copy(c, &w->tmp_mono[1], &w->a_mono);
    if (st == SRMECH_OK) { w->tmp_mono[1].exps[qsym] += 1; }            /* aq = a * q      */
    if (st == SRMECH_OK) { st = srmech_ellbase_mono_copy(c, &w->aq, &w->tmp_mono[1]); }
    if (st != SRMECH_OK) { return st; }
    for (i = 0; i < r->n_den; i++) {                   /* the linear Pochhammer den factors */
        int32_t ye;
        if (!er_is_x_power(&r->den[i], xsym, 1)) { continue; }
        st = er_real_base(c, &w->tmp_mono[2], &r->den[i], xsym, &w->tmp_mono[3]);
        if (st != SRMECH_OK) { return st; }
        st = srmech_ellbase_mono_inv(c, &w->tmp_mono[3], &w->tmp_mono[2]);  /* real_base^-1 */
        if (st != SRMECH_OK) { return st; }
        st = srmech_ellbase_mono_mul(c, &w->tmp_mono[4], &w->aq, &w->tmp_mono[3],
                                     &w->s.g, &w->s.t0, &w->s.t1);          /* u = aq/base  */
        if (st != SRMECH_OK) { return st; }
        if (er_same_exps(c, &w->tmp_mono[4], &w->a_mono)) { continue; }    /* drop (q): u==a */
        ye = (ysym >= 0) ? w->tmp_mono[4].exps[ysym] : 0;
        if (ye != 0) { continue; }                     /* drop the n-dependent params (y)  */
        if (n_free >= ER_N_FREE) { return SRMECH_OK; }                     /* > 3 free -> out */
        st = srmech_ellbase_mono_copy(c, &w->free_p[n_free], &w->tmp_mono[4]);
        if (st != SRMECH_OK) { return st; }
        n_free++;
    }
    if (n_free != ER_N_FREE) { return SRMECH_OK; }     /* != 3 free params -> out of class */
    *ok = 1;
    return SRMECH_OK;
}

/* aq / free[a] into `out` (an aq/single denominator endpoint). out = aq * free[a]^-1. */
static srmech_status_t er_aq_over_single(er_ctx_t *c, er_work_t *w, er_mono_t *out,
                                         size_t a)
{
    srmech_status_t st;
    assert(c != NULL && w != NULL && out != NULL);
    assert(a < ER_N_FREE);
    st = srmech_ellbase_mono_inv(c, &w->tmp_mono[6], &w->free_p[a]);    /* free[a]^-1      */
    if (st == SRMECH_OK) {
        st = srmech_ellbase_mono_mul(c, out, &w->aq, &w->tmp_mono[6],
                                     &w->s.g, &w->s.t0, &w->s.t1);       /* aq/free[a]      */
    }
    return st;
}

/* aq / (free[a] * free[b]) into `out` (an s2-pair numerator endpoint; a != b).
 * out = aq * free[a]^-1 * free[b]^-1. */
static srmech_status_t er_aq_over_pair(er_ctx_t *c, er_work_t *w, er_mono_t *out,
                                       size_t a, size_t b)
{
    srmech_status_t st;
    assert(c != NULL && w != NULL && out != NULL);
    assert(a < ER_N_FREE && b < ER_N_FREE);
    st = er_aq_over_single(c, w, &w->tmp_mono[7], a);                  /* aq/free[a]      */
    if (st != SRMECH_OK) { return st; }
    st = srmech_ellbase_mono_inv(c, &w->tmp_mono[8], &w->free_p[b]);    /* free[b]^-1      */
    if (st == SRMECH_OK) {
        st = srmech_ellbase_mono_mul(c, out, &w->tmp_mono[7], &w->tmp_mono[8],
                                     &w->s.g, &w->s.t0, &w->s.t1);       /* aq/(fa*fb)      */
    }
    return st;
}

/* Build the eight endpoint monomials (4 num + 4 den) of rho:
 *   num = {aq} U {aq/(f0 f1), aq/(f0 f2), aq/(f1 f2)}       (s2 pairs)
 *   den = {aq/f0, aq/f1, aq/f2} U {aq/(f0 f1 f2)}           (singles + s3)
 * Written into num_e[0..3] / den_e[0..3]. Mirrors _build_rho's endpoint lists. */
static srmech_status_t er_endpoints(er_ctx_t *c, er_work_t *w, er_mono_t *num_e,
                                    er_mono_t *den_e)
{
    static const size_t PAIR_A[3] = {0u, 0u, 1u};
    static const size_t PAIR_B[3] = {1u, 2u, 2u};
    size_t i;
    srmech_status_t st;
    assert(c != NULL && w != NULL && num_e != NULL && den_e != NULL);
    assert(ER_N_FREE == 3u);                           /* the ₈ω₇ has exactly 3 free params */
    st = srmech_ellbase_mono_copy(c, &num_e[0], &w->aq);               /* num[0] = aq      */
    if (st != SRMECH_OK) { return st; }
    for (i = 0; i < ER_N_FREE; i++) {                                  /* num[1..3] = s2   */
        st = er_aq_over_pair(c, w, &num_e[1u + i], PAIR_A[i], PAIR_B[i]);
        if (st != SRMECH_OK) { return st; }
    }
    for (i = 0; i < ER_N_FREE; i++) {                                  /* den[0..2] = aq/fi */
        st = er_aq_over_single(c, w, &den_e[i], i);
        if (st != SRMECH_OK) { return st; }
    }
    st = srmech_ellbase_mono_mul(c, &w->tmp_mono[9], &w->free_p[0], &w->free_p[1],
                                 &w->s.g, &w->s.t0, &w->s.t1);          /* f0*f1           */
    if (st == SRMECH_OK) {
        st = srmech_ellbase_mono_mul(c, &w->tmp_mono[10], &w->tmp_mono[9], &w->free_p[2],
                                     &w->s.g, &w->s.t0, &w->s.t1);       /* s3 = f0*f1*f2   */
    }
    if (st == SRMECH_OK) {
        st = srmech_ellbase_mono_inv(c, &w->tmp_mono[11], &w->tmp_mono[10]);  /* s3^-1      */
    }
    if (st == SRMECH_OK) {
        st = srmech_ellbase_mono_mul(c, &den_e[3], &w->aq, &w->tmp_mono[11],
                                     &w->s.g, &w->s.t0, &w->s.t1);       /* den[3] = aq/s3  */
    }
    return st;
}

/* CONSTRUCT rho = prod theta(num_e[i]*y) / prod theta(den_e[i]*y) as a canonical EllRatio
 * (unit prefactor; the y-multiplied endpoints become the theta arguments). Mirrors
 * _build_rho's EllRatio(num=[Theta(end*y)], den=[Theta(end*y)]). */
static srmech_status_t er_build_rho(er_ctx_t *c, er_work_t *w, er_ratio_t *rho,
                                    const er_mono_t *num_e, const er_mono_t *den_e,
                                    int psym)
{
    er_mono_t pref0 = {0};
    size_t i;
    srmech_status_t st;
    assert(c != NULL && w != NULL && rho != NULL && num_e != NULL && den_e != NULL);
    assert(w->cap_arg >= 4u);                           /* room for the 4 num + 4 den args */
    for (i = 0; i < 4u; i++) {                          /* the theta args = endpoint * y   */
        st = srmech_ellbase_mono_mul(c, &w->raw_num[i], &num_e[i], &w->y,
                                     &w->s.g, &w->s.t0, &w->s.t1);
        if (st != SRMECH_OK) { return st; }
        st = srmech_ellbase_mono_mul(c, &w->raw_den[i], &den_e[i], &w->y,
                                     &w->s.g, &w->s.t0, &w->s.t1);
        if (st != SRMECH_OK) { return st; }
    }
    pref0 = w->tmp_mono[12];
    st = srmech_ellbase_mono_set_one(c, &pref0);        /* the unit prefactor              */
    if (st != SRMECH_OK) { return st; }
    return er_er_build(c, w, rho, &pref0, w->raw_num, 4u, w->raw_den, 4u, psym);
}

/* Emit the canonical rho EllRatio: the prefactor exact-Q coeff into out_pref_num/den +
 * its exponent row, then the num/den canonical theta-argument exponent rows; the per-side
 * counts into *out_n_num / *out_n_den. Mirrors srmech_elliptic_gosper's eg_emit_cert. */
static srmech_status_t er_emit(er_ctx_t *c, const er_ratio_t *rho,
                               srmech_bigint_t *out_pref_num,
                               srmech_bigint_t *out_pref_den,
                               int32_t *out_exps_flat, size_t out_exps_cap_rows,
                               size_t *out_n_num, size_t *out_n_den)
{
    size_t i;
    size_t row = 0;
    srmech_status_t st;
    assert(c != NULL && rho != NULL && out_pref_num != NULL && out_pref_den != NULL);
    assert(out_exps_flat != NULL && out_n_num != NULL && out_n_den != NULL);
    if (1u + rho->n_num + rho->n_den > out_exps_cap_rows) {
        return SRMECH_ERR_OVERFLOW;
    }
    st = srmech_bigint_copy(out_pref_num, &rho->pref.coeff.num);
    if (st == SRMECH_OK) { st = srmech_bigint_copy(out_pref_den, &rho->pref.coeff.den); }
    if (st != SRMECH_OK) { return st; }
    memcpy(out_exps_flat + row * c->n_syms, rho->pref.exps, c->n_syms * sizeof(int32_t));
    row++;
    for (i = 0; i < rho->n_num; i++) {
        memcpy(out_exps_flat + row * c->n_syms, rho->num[i].exps,
               c->n_syms * sizeof(int32_t));
        row++;
    }
    for (i = 0; i < rho->n_den; i++) {
        memcpy(out_exps_flat + row * c->n_syms, rho->den[i].exps,
               c->n_syms * sizeof(int32_t));
        row++;
    }
    *out_n_num = rho->n_num;
    *out_n_den = rho->n_den;
    return SRMECH_OK;
}

/* ============================================================================ *
 *  arena binders + the public entry
 * ============================================================================ */

/* Carve a freshly-bound er_ratio_t with cap theta args in each of num / den. */
static srmech_status_t er_bind_ratio(er_ctx_t *c, er_ratio_t *r, size_t cap)
{
    assert(c != NULL && r != NULL);
    assert(cap >= 1u);
    return srmech_ellbase_er_bind_ratio(c, r, cap, cap);
}

/* Carve the shared work roster (the reusable raw / canon arrays + scratch monomials +
 * the base / aq / y / free-param monomials). */
static srmech_status_t er_bind_work(er_ctx_t *c, er_work_t *w, size_t cap_arg)
{
    srmech_status_t st;
    assert(c != NULL && w != NULL);
    assert(cap_arg >= 1u);
    w->cap_arg = cap_arg;
    st = srmech_ellbase_bind_mono_arr(c, &w->raw_num, cap_arg);
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono_arr(c, &w->raw_den, cap_arg); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono_arr(c, &w->cn, cap_arg); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono_arr(c, &w->cd, cap_arg); }
    if (st == SRMECH_OK) {
        st = srmech_ellbase_bind_mono_arr(c, &w->tmp_mono, ER_LOCAL_MONOS);
    }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono_arr(c, &w->free_p, ER_N_FREE); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono(c, &w->a_mono); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono(c, &w->aq); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono(c, &w->y); }
    if (st == SRMECH_OK) { st = srmech_ellbase_er_bind_scr(c, &w->s, cap_arg); }
    return st;
}

/* Parse the flat input wire (coeff_num/coeff_den bigints + int32 exps rows, in order
 * prefactor, num0..K-1, den0..L-1) into raw monomial arrays, then er_build the canonical
 * input ratio r. Mirrors srmech_elliptic_gosper's eg_parse_input. */
static srmech_status_t er_parse_input(er_ctx_t *c, er_work_t *w, er_ratio_t *r,
                                      size_t n_num, size_t n_den,
                                      const srmech_bigint_t *cnum,
                                      const srmech_bigint_t *cden,
                                      const int32_t *exps_flat, int psym)
{
    er_mono_t pref = {0};
    size_t k;
    size_t mi = 0;
    size_t ej = 0;
    srmech_status_t st;
    assert(c != NULL && w != NULL && r != NULL);
    assert(cnum != NULL && cden != NULL && exps_flat != NULL);
    assert(n_num <= w->cap_arg && n_den <= w->cap_arg);
    pref = w->tmp_mono[5];
    st = srmech_bigint_copy(&pref.coeff.num, &cnum[mi]);
    if (st == SRMECH_OK) { st = srmech_bigint_copy(&pref.coeff.den, &cden[mi]); }
    if (st != SRMECH_OK) { return st; }
    memcpy(pref.exps, exps_flat + ej, c->n_syms * sizeof(int32_t));
    mi++; ej += c->n_syms;
    for (k = 0; k < n_num; k++) {
        st = srmech_bigint_copy(&w->raw_num[k].coeff.num, &cnum[mi]);
        if (st == SRMECH_OK) { st = srmech_bigint_copy(&w->raw_num[k].coeff.den, &cden[mi]); }
        if (st != SRMECH_OK) { return st; }
        memcpy(w->raw_num[k].exps, exps_flat + ej, c->n_syms * sizeof(int32_t));
        mi++; ej += c->n_syms;
    }
    for (k = 0; k < n_den; k++) {
        st = srmech_bigint_copy(&w->raw_den[k].coeff.num, &cnum[mi]);
        if (st == SRMECH_OK) { st = srmech_bigint_copy(&w->raw_den[k].coeff.den, &cden[mi]); }
        if (st != SRMECH_OK) { return st; }
        memcpy(w->raw_den[k].exps, exps_flat + ej, c->n_syms * sizeof(int32_t));
        mi++; ej += c->n_syms;
    }
    return er_er_build(c, w, r, &pref, w->raw_num, n_num, w->raw_den, n_den, psym);
}

/* The whole working roster, carved once. */
typedef struct er_all {
    er_ctx_t   ctx;
    er_work_t  w;
    er_ratio_t r;                /* the parsed canonical input term-ratio       */
    er_ratio_t rho;              /* the constructed order-1 recurrence coeff     */
    er_mono_t *num_e;            /* the 4 numerator endpoint monomials           */
    er_mono_t *den_e;            /* the 4 denominator endpoint monomials         */
} er_all_t;

/* Carve the whole roster from the caller arena. */
static srmech_status_t er_bind_all(er_all_t *A, size_t n_num, size_t n_den, int ysym,
                                   void *ws, size_t ws_len)
{
    size_t cap_arg = n_num + n_den + 8u;
    srmech_status_t st;
    assert(A != NULL);
    assert(ws != NULL || ws_len == 0u);                 /* a non-empty arena needs a buffer */
    if (cap_arg < ER_MAX_THETA) { cap_arg = ER_MAX_THETA; }
    st = srmech_ellbase_er_arena_init(&A->ctx, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    st = er_bind_work(&A->ctx, &A->w, cap_arg);
    if (st == SRMECH_OK) { st = er_bind_ratio(&A->ctx, &A->r, cap_arg); }
    if (st == SRMECH_OK) { st = er_bind_ratio(&A->ctx, &A->rho, cap_arg); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono_arr(&A->ctx, &A->num_e, 4u); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono_arr(&A->ctx, &A->den_e, 4u); }
    /* y = symbol(y): coeff 1, y-exponent 1 (set after the work roster is bound). */
    if (st == SRMECH_OK) { st = srmech_ellbase_mono_set_one(&A->ctx, &A->w.y); }
    if (st == SRMECH_OK && ysym >= 0) { A->w.y.exps[ysym] = 1; }
    return st;
}

/* The order-1 8w7 recurrence pipeline: parse the input ratio, decompose the VWP 8w7 into
 * a + the 3 free params, construct rho from the elementary symmetric endpoints. *has = 1
 * + A->rho on a canonical 8w7; *has = 0 out of class. */
static srmech_status_t er_run(er_all_t *A, int xsym, int qsym, int ysym, int psym,
                              int *has)
{
    int ok = 0;
    srmech_status_t st;
    assert(A != NULL && has != NULL);
    assert(qsym >= 0);                                 /* q is load-bearing (aq = a·q)     */
    *has = 0;
    st = er_decompose_8w7(&A->ctx, &A->w, &A->r, xsym, qsym, ysym, &ok);
    if (st != SRMECH_OK) { return st; }
    if (!ok) { return SRMECH_OK; }                     /* out of class -> Python decides   */
    st = er_endpoints(&A->ctx, &A->w, A->num_e, A->den_e);
    if (st != SRMECH_OK) { return st; }
    st = er_build_rho(&A->ctx, &A->w, &A->rho, A->num_e, A->den_e, psym);
    if (st != SRMECH_OK) { return st; }
    *has = 1;
    return SRMECH_OK;
}

srmech_status_t srmech_elliptic_recurrence_8w7(size_t n_syms, int xsym, int psym,
                                               int qsym, int ysym,
                                               size_t n_num, size_t n_den,
                                               const srmech_bigint_t *coeff_num,
                                               const srmech_bigint_t *coeff_den,
                                               const int32_t *exps_flat,
                                               uint32_t coeff_cap, int *out_has,
                                               srmech_bigint_t *out_pref_num,
                                               srmech_bigint_t *out_pref_den,
                                               int32_t *out_exps_flat,
                                               size_t out_exps_cap_rows,
                                               size_t *out_n_num, size_t *out_n_den,
                                               void *ws, size_t ws_len)
{
    er_all_t A = {0};
    int has = 0;
    srmech_status_t st;
    assert(out_has != NULL && out_pref_num != NULL && out_pref_den != NULL);
    assert(out_exps_flat != NULL && out_n_num != NULL && out_n_den != NULL);
    if (out_has == NULL || out_pref_num == NULL || out_pref_den == NULL
        || out_exps_flat == NULL || out_n_num == NULL || out_n_den == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    *out_has = 0;
    *out_n_num = 0;
    *out_n_den = 0;
    if (coeff_num == NULL || coeff_den == NULL || exps_flat == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (qsym < 0) { return SRMECH_OK; }                /* q absent -> not an 8w7; decline */
    if (n_num > ER_MAX_THETA || n_den > ER_MAX_THETA) {
        return SRMECH_OK;                              /* over native scope -> decline    */
    }
    A.ctx.n_syms = (n_syms == 0u) ? 1u : n_syms;
    A.ctx.cap = (coeff_cap < 8u) ? 8u : coeff_cap;
    st = er_bind_all(&A, n_num, n_den, ysym, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    st = er_parse_input(&A.ctx, &A.w, &A.r, n_num, n_den, coeff_num, coeff_den,
                        exps_flat, psym);
    if (st != SRMECH_OK) { return st; }
    st = er_run(&A, xsym, qsym, ysym, psym, &has);
    if (st != SRMECH_OK) { return st; }
    if (!has) { return SRMECH_OK; }                    /* decline -> Python pure path     */
    st = er_emit(&A.ctx, &A.rho, out_pref_num, out_pref_den, out_exps_flat,
                 out_exps_cap_rows, out_n_num, out_n_den);
    if (st != SRMECH_OK) { return st; }
    *out_has = 1;
    return SRMECH_OK;
}

/* The minimum `ws_len` BYTES srmech_elliptic_recurrence_8w7 needs for the given shape
 * (n_syms symbols, n_num + n_den input theta factors, coeff_limbs the per-coefficient
 * significant-limb estimate). Sized to the inputs -- no compiled-in cap; if RAM balloons
 * the caller mis-encoded the fiber. */
size_t srmech_elliptic_recurrence_8w7_ws_bound(size_t n_syms, size_t n_num, size_t n_den,
                                               size_t coeff_cap)
{
    size_t cap = (coeff_cap < 8u) ? 8u : coeff_cap;
    size_t ns = (n_syms == 0u) ? 1u : n_syms;
    size_t cap_arg = n_num + n_den + 8u;
    size_t mw;
    size_t ratios;
    size_t arrays;
    size_t total;
    if (cap_arg < ER_MAX_THETA) { cap_arg = ER_MAX_THETA; }
    mw = srmech_ellbase_er_mono_words(cap, ns);
    /* the parsed input + the output rho (each pref + 2*cap_arg arg monomials), padded. */
    ratios = 4u * (mw + 2u * cap_arg * mw);
    /* the reusable raw / canon arrays + the scratch / free / base monomials + endpoints. */
    arrays = (4u * cap_arg + ER_LOCAL_MONOS + ER_N_FREE + 8u + SRMECH_ELL_ER_SCR_MONOS
              + 64u) * mw;
    total = ratios + arrays + cap * 32u + 4096u;
    assert(cap >= 8u);
    assert(total >= ratios);
    return total * sizeof(uint32_t);
}

/* The per-coefficient limb cap for each srmech_bigint in the OUTPUT (the rho prefactor
 * coeff), so the reduced recurrence coefficient never overflows its slot. */
size_t srmech_elliptic_recurrence_8w7_out_cap(size_t coeff_limbs)
{
    size_t cl = (coeff_limbs == 0u) ? 1u : coeff_limbs;
    size_t cap = cl * 4u + 64u;
    assert(cap >= 2u);
    assert(cap >= coeff_limbs);
    return cap;
}
