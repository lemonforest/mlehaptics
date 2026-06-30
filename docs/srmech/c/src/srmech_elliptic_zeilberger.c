/*
 * srmech_elliptic_zeilberger.c -- the ELLIPTIC Sigma-row CREATIVE-TELESCOPING op for the
 * Frenkel-Turaev 8w7 summation (the C peer of
 * srmech.amsc.elliptic_zeilberger.elliptic_zeilberger). The order-1 recurrence
 * f(n+1) = rho(n)*f(n) PLUS an EXACT connection-coefficient certificate that PROVES it
 * (the ThetaSum.is_zero decision, NOT rc68's 1e-9 numerical convergence gate).
 *
 * Input: the 8w7 summand's TERM RATIO t(n+1)/t(n) = r(x) (x = q^n) as a full EllRatio
 * (the SAME wire form srmech_elliptic_recurrence_8w7 parses: the interned symbol-table
 * dimension n_syms + the x/p/q/y interned indices + the num/den theta counts + the flat
 * exact-Q coeff arrays + the flat int32 exponent rows), PLUS the two extra interned
 * indices nsym/ksym for the recurrence index symbols N = q^n, K = q^k the certificate
 * carries (the Python force-interns "N"/"K" into the table for this op; the input ratio's
 * own monomials are zero in those two columns).
 *
 * Output: *out_has = 1 iff r is a canonical 8w7 (recognized by the SAME recognize-
 * decompose pipeline srmech_elliptic_recurrence_8w7 runs) AND the connection-coefficient
 * inductive-step certificate decides EXACTLY ZERO (via the shared srmech_thetasum_is_zero
 * kernel); else *out_has = 0 (out of class / certificate did not close -> the Python
 * re-decides on its complete pure path AND re-builds + re-verifies rho there; the C peer
 * does NOT emit rho -- the Python builds rho on its side and trusts has=1 only after its
 * own cert.is_zero agrees in exact Q).
 *
 * The GENUINE pipeline (mirrors the Python elliptic_zeilberger exactly):
 *   (1) RECOGNIZE + DECOMPOSE the very-well-poised 8w7 (ez_decompose_8w7, the 1:1 mirror
 *       of _decompose_8w7 / srmech_elliptic_recurrence's er_decompose_8w7): the unique den
 *       factor theta(a x^2) (x-exponent magnitude 2) gives the base a; the linear den
 *       factors theta(a q x u^-1) (x-exponent magnitude 1) give aq*real_base^-1 = u; drop
 *       the (q)-factor (u == a) + the y-carrying (n-dependent) params, leaving the three
 *       FREE params [b, c, d]. Out of class -> *out_has = 0.
 *   (2) BUILD the connection-coefficient split certificate (ez_build_certificate, the 1:1
 *       mirror of _connection_split_certificate) from a, b = free[0], c = free[1]. With
 *       N = q^n, K = q^k, the theta variable x, and theta(u v^pm) = theta(uv) theta(u/v):
 *         +1            * theta(bK*(cN/K)^pm) * theta(aN*x^pm)
 *         -1            * theta(aN*(cN/K)^pm) * theta(bK*x^pm)
 *         +(b/c)(K^2/N) * theta(aN*(bK)^pm)   * theta(cN/K*x^pm)   == 0.
 *       Every term is two clean +/- pairs (perfect-square midpoints aN, bK, cN/K) -- the
 *       carrier-reducible shape srmech_thetasum_is_zero decides.
 *   (3) DECIDE the certificate ThetaSum == 0 (ez_decide, marshalling the 3 terms x (1
 *       prefactor + 4 thetas) into the flat thetasum wire + routing srmech_thetasum_is_zero
 *       in x with ysym = -1, mirroring srmech_elliptic_gosper's eg_decide_terms).
 *
 * Reference (MPM-verified at build by reading the source PDF): Hjalmar Rosengren,
 * "Elliptic Hypergeometric Functions," arXiv:1608.06161v3 [math.CA] (2017), Sec.2.3
 * Eqs.(2.12)-(2.14) [the connection-coefficient expansion + the elliptic binomial
 * coefficient + the elliptic Pascal recurrence] -> Sec.1.4 Eq.(1.12) [the Weierstrass
 * three-term theta relation]; the closed product form + rho are Warnaar, Constr. Approx.
 * 18 (2002) 479-502, Cor 2.2.
 *
 * PURE COMPOSITION of the shared srmech_ellbase_* exact-Q monomial algebra (mul / inv /
 * copy / set_one / eq) + er_build (the EllRatio.__init__ mirror) + srmech_thetasum_is_zero
 * -- the same single copies srmech_elliptic_recurrence / srmech_elliptic_gosper ride.
 * Malloc-free (JPL Rule 3): every working monomial / EllRatio / scratch / wire buffer is
 * carved from the caller arena `ws`. The "magnitude 2 / magnitude 1" x-power test + the
 * +/-1 prefactor sign are Class-K parity branches (e == m || e == -m ; num.sign flip),
 * never abs()/fabs().
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto/recursion): OK -- iterative, flat static helpers
 *   - Rule 2 (bounded loops)    : OK -- bounded by n_num / n_den / 3 free / 3 terms
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

/* The maximum theta-factor count the native scope handles per input ratio (the canonical
 * 8w7 stays small). An over-cap input returns OK with *out_has = 0 and the Python decides. */
#define EZ_MAX_THETA 32u
/* The number of free parameters a canonical 8w7 decomposes into (b, c, d). */
#define EZ_N_FREE 3u
/* The general scratch-monomial roster size. */
#define EZ_LOCAL_MONOS 16u
/* The fixed certificate shape: 3 terms, each 1 prefactor + 4 theta args (two +/- pairs). */
#define EZ_CERT_TERMS 3u
#define EZ_CERT_THETAS 4u
#define EZ_CERT_MONOS 15u            /* 3 * (1 + 4) */

/* ---- shared-kernel aliases (the single copy lives in srmech_ellbase.c) ------- */
typedef srmech_ell_ctx_t       ez_ctx_t;
typedef srmech_ell_mono_t      ez_mono_t;
typedef srmech_ell_er_ratio_t  ez_ratio_t;
typedef srmech_ell_er_scr_t    ez_scr_t;

/* The working roster for the recognize-decompose half, carved once from the arena. */
typedef struct ez_work {
    ez_scr_t   s;                /* the EllRatio construction scratch         */
    ez_mono_t *raw_num;          /* reusable raw num-arg arrays for er_build   */
    ez_mono_t *raw_den;
    ez_mono_t *cn;               /* er_build canon scratch                     */
    ez_mono_t *cd;
    ez_mono_t *tmp_mono;         /* EZ_LOCAL_MONOS general scratch monomials   */
    ez_mono_t *free_p;           /* the EZ_N_FREE free params [b, c, d]        */
    ez_mono_t  a_mono;           /* the base a                                 */
    ez_mono_t  aq;               /* a * q                                      */
    size_t     cap_arg;          /* per-array theta-arg capacity               */
} ez_work_t;

/* The certificate-build + decide roster (the symbols + midpoints + the flat thetasum wire). */
typedef struct ez_cwork {
    ez_mono_t  N;                /* symbol(N) = q^n                            */
    ez_mono_t  K;                /* symbol(K) = q^k                            */
    ez_mono_t  x;                /* symbol(x) = the theta variable             */
    ez_mono_t  aN;               /* a * N                                      */
    ez_mono_t  bK;               /* b * K                                      */
    ez_mono_t  cNK;              /* c * N / K                                  */
    ez_mono_t  weight;           /* (b/c) * K^2 / N (the term-3 prefactor)     */
    ez_mono_t  pref_pm;          /* the +1 / -1 scalar prefactor               */
    ez_mono_t  s0;               /* generic scratch monomial                   */
    ez_mono_t  s1;               /* generic scratch monomial                   */
    ez_mono_t  s2;               /* generic scratch monomial                   */
    ez_mono_t  term_pref;        /* the accumulating term prefactor (scalar * canon prefs) */
    ez_mono_t  cpref;            /* theta_canon_full extracted prefactor out   */
    ez_mono_t  pacc;             /* term_pref * cpref accumulator scratch      */
    ez_mono_t  z0;               /* theta_canon_full scratch                   */
    ez_mono_t  z0inv;
    ez_mono_t  ctmp;
    ez_mono_t *carg;             /* the EZ_CERT_THETAS canonical theta args     */
    srmech_bigint_t *cnum;       /* flat thetasum coeff numerators (EZ_CERT_MONOS) */
    srmech_bigint_t *cden;       /* flat thetasum coeff denominators            */
    int32_t         *exps_flat;  /* flat thetasum exponent rows                 */
    size_t          *nthetas;    /* per-term theta counts (EZ_CERT_TERMS)       */
    void            *ts_ws;      /* the thetasum sub-arena                       */
    size_t           ts_ws_len;
} ez_cwork_t;

/* ============================================================================ *
 *  recognize + decompose (1:1 mirror of srmech_elliptic_recurrence's er_*)
 * ============================================================================ */

/* out := EllRatio(pref, num, den) canonical (er_build folds + cancels + sorts). */
static srmech_status_t ez_er_build(ez_ctx_t *c, ez_work_t *w, ez_ratio_t *out,
                                   const ez_mono_t *pref, const ez_mono_t *num,
                                   size_t n_num, const ez_mono_t *den, size_t n_den,
                                   int psym)
{
    assert(c != NULL && w != NULL && out != NULL && pref != NULL);
    assert(n_num <= w->cap_arg && n_den <= w->cap_arg);
    return srmech_ellbase_er_build(c, out, pref, num, n_num, den, n_den, psym,
                                   &w->s, w->cn, w->cap_arg, w->cd, w->cap_arg);
}

/* The REAL base of a theta argument theta(b * x^k) (k == +-1 or +-2): strip the x-power,
 * then re-orient (a NEGATIVE x-exponent means the stored arg is the inverse of the real
 * base -> invert back). The orientation flip is the Class-K chirality resolution (no abs). */
static srmech_status_t ez_real_base(ez_ctx_t *c, ez_mono_t *out, const ez_mono_t *arg,
                                    int xsym, ez_mono_t *tmp)
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
static int ez_is_x_power(const ez_mono_t *arg, int xsym, int32_t mag)
{
    int32_t e;
    assert(arg != NULL);
    assert(mag == 1 || mag == 2);                      /* only the linear / VWP cores */
    if (xsym < 0) { return 0; }
    e = arg->exps[xsym];
    return (e == mag || e == -mag) ? 1 : 0;
}

/* Two monomials have the SAME exponent map (ignoring the coeff): mirrors the Python
 * `dict(u.exps) != dict(a_mono.exps)` filter that drops the (q)-factor (recovers u == a). */
static int ez_same_exps(const ez_ctx_t *c, const ez_mono_t *a, const ez_mono_t *b)
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
 * aq (w->aq), and the EZ_N_FREE free params (w->free_p[0..2]). *ok = 1 on a canonical 8w7;
 * *ok = 0 out of class (no unique magnitude-2 quadratic core, or != 3 free params). */
static srmech_status_t ez_decompose_8w7(ez_ctx_t *c, ez_work_t *w, const ez_ratio_t *r,
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
        if (ez_is_x_power(&r->den[i], xsym, 2)) {
            n_quad++;
            st = ez_real_base(c, &w->a_mono, &r->den[i], xsym, &w->tmp_mono[0]);
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
        if (!ez_is_x_power(&r->den[i], xsym, 1)) { continue; }
        st = ez_real_base(c, &w->tmp_mono[2], &r->den[i], xsym, &w->tmp_mono[3]);
        if (st != SRMECH_OK) { return st; }
        st = srmech_ellbase_mono_inv(c, &w->tmp_mono[3], &w->tmp_mono[2]);  /* real_base^-1 */
        if (st != SRMECH_OK) { return st; }
        st = srmech_ellbase_mono_mul(c, &w->tmp_mono[4], &w->aq, &w->tmp_mono[3],
                                     &w->s.g, &w->s.t0, &w->s.t1);          /* u = aq/base  */
        if (st != SRMECH_OK) { return st; }
        if (ez_same_exps(c, &w->tmp_mono[4], &w->a_mono)) { continue; }    /* drop (q): u==a */
        ye = (ysym >= 0) ? w->tmp_mono[4].exps[ysym] : 0;
        if (ye != 0) { continue; }                     /* drop the n-dependent params (y)  */
        if (n_free >= EZ_N_FREE) { return SRMECH_OK; }                     /* > 3 free -> out */
        st = srmech_ellbase_mono_copy(c, &w->free_p[n_free], &w->tmp_mono[4]);
        if (st != SRMECH_OK) { return st; }
        n_free++;
    }
    if (n_free != EZ_N_FREE) { return SRMECH_OK; }     /* != 3 free params -> out of class */
    *ok = 1;
    return SRMECH_OK;
}

/* Parse the flat input wire (coeff_num/coeff_den bigints + int32 exps rows, in order
 * prefactor, num0..K-1, den0..L-1) into raw monomial arrays, then er_build the canonical
 * input ratio r. (Mirrors srmech_elliptic_recurrence's er_parse_input.) */
static srmech_status_t ez_parse_input(ez_ctx_t *c, ez_work_t *w, ez_ratio_t *r,
                                      size_t n_num, size_t n_den,
                                      const srmech_bigint_t *cnum,
                                      const srmech_bigint_t *cden,
                                      const int32_t *exps_flat, int psym)
{
    ez_mono_t pref = {0};
    size_t k;
    size_t mi = 0;
    size_t ej = 0;
    srmech_status_t st;
    assert(c != NULL && w != NULL && r != NULL);
    assert(cnum != NULL && cden != NULL && exps_flat != NULL);
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
    return ez_er_build(c, w, r, &pref, w->raw_num, n_num, w->raw_den, n_den, psym);
}

/* ============================================================================ *
 *  the connection-coefficient split certificate (mirror _connection_split_certificate)
 * ============================================================================ */

/* out := the symbol monomial symbol(sym) (coeff 1, exps[sym] = 1). sym >= 0. */
static srmech_status_t ez_symbol(ez_ctx_t *c, ez_mono_t *out, int sym)
{
    srmech_status_t st;
    assert(c != NULL && out != NULL);
    assert(sym >= 0);
    st = srmech_ellbase_mono_set_one(c, out);
    if (st != SRMECH_OK) { return st; }
    out->exps[sym] = 1;
    return SRMECH_OK;
}

/* out := a * b (a thin name over the shared monomial multiply with cw scratch bigints). */
static srmech_status_t ez_mul(ez_ctx_t *c, ez_work_t *w, ez_mono_t *out,
                              const ez_mono_t *a, const ez_mono_t *b)
{
    assert(c != NULL && w != NULL && out != NULL && a != NULL && b != NULL);
    assert(a->exps != NULL && b->exps != NULL);
    return srmech_ellbase_mono_mul(c, out, a, b, &w->s.g, &w->s.t0, &w->s.t1);
}

/* Build the certificate's midpoints aN = a*N, bK = b*K, cNK = c*N/K, and the term-3
 * weight = (b/c)*K^2/N, into cw. a = w->a_mono, b = w->free_p[0], c = w->free_p[1]. */
static srmech_status_t ez_build_midpoints(ez_ctx_t *c, ez_work_t *w, ez_cwork_t *cw)
{
    srmech_status_t st;
    assert(c != NULL && w != NULL && cw != NULL);
    assert(cw->N.exps != NULL && cw->K.exps != NULL);
    st = ez_mul(c, w, &cw->aN, &w->a_mono, &cw->N);                 /* aN = a*N            */
    if (st == SRMECH_OK) { st = ez_mul(c, w, &cw->bK, &w->free_p[0], &cw->K); }  /* bK=b*K */
    if (st == SRMECH_OK) { st = ez_mul(c, w, &cw->s0, &w->free_p[1], &cw->N); }  /* c*N    */
    if (st == SRMECH_OK) { st = srmech_ellbase_mono_inv(c, &cw->s1, &cw->K); }   /* K^-1   */
    if (st == SRMECH_OK) { st = ez_mul(c, w, &cw->cNK, &cw->s0, &cw->s1); }      /* c*N/K  */
    if (st != SRMECH_OK) { return st; }
    /* weight = (b/c)*K^2/N = (b*K*K) * (c*N)^-1 ; cw->s0 already holds c*N. */
    st = ez_mul(c, w, &cw->s1, &w->free_p[0], &cw->K);             /* b*K                 */
    if (st == SRMECH_OK) { st = ez_mul(c, w, &cw->s2, &cw->s1, &cw->K); }        /* b*K*K  */
    if (st == SRMECH_OK) { st = srmech_ellbase_mono_inv(c, &cw->s1, &cw->s0); }  /* (c*N)^-1 */
    if (st == SRMECH_OK) { st = ez_mul(c, w, &cw->weight, &cw->s2, &cw->s1); }   /* weight */
    return st;
}

/* Emit one monomial (coeff num/den + dense exps row) into the flat thetasum wire at the
 * monomial cursor *mi / exps cursor *ej. */
static srmech_status_t ez_emit_mono(ez_ctx_t *c, ez_cwork_t *cw, const ez_mono_t *m,
                                    size_t *mi, size_t *ej)
{
    srmech_status_t st;
    assert(c != NULL && cw != NULL && m != NULL && mi != NULL && ej != NULL);
    assert(*mi < EZ_CERT_MONOS);
    st = srmech_bigint_copy(&cw->cnum[*mi], &m->coeff.num);
    if (st == SRMECH_OK) { st = srmech_bigint_copy(&cw->cden[*mi], &m->coeff.den); }
    if (st != SRMECH_OK) { return st; }
    memcpy(cw->exps_flat + *ej, m->exps, c->n_syms * sizeof(int32_t));
    (*mi)++;
    *ej += c->n_syms;
    return SRMECH_OK;
}

/* Canonicalize one RAW theta arg ``z`` (theta_canon_full) into ``cw->carg[k]`` (the
 * canonical argument) and FOLD the extracted quasi-periodicity prefactor into the running
 * term prefactor ``cw->term_pref`` (term_pref *= cpref). This mirrors what er_build /
 * Theta.canonicalize do: the kernel srmech_thetasum_is_zero canonicalizes only the arg KEY
 * (it does NOT re-extract the prefactor), so the caller MUST pre-fold the canon prefactor
 * into the term coefficient — exactly as the Python ThetaSum constructor stores it. */
static srmech_status_t ez_canon_fold(ez_ctx_t *c, ez_work_t *w, ez_cwork_t *cw,
                                     const ez_mono_t *z, int psym, size_t k)
{
    srmech_status_t st;
    assert(c != NULL && w != NULL && cw != NULL && z != NULL);
    assert(k < EZ_CERT_THETAS);
    st = srmech_ellbase_theta_canon_full(c, &cw->cpref, &cw->carg[k], z, psym,
                                         &cw->z0, &cw->z0inv, &cw->ctmp,
                                         &w->s.g, &w->s.t0, &w->s.t1);
    if (st != SRMECH_OK) { return st; }
    st = ez_mul(c, w, &cw->pacc, &cw->term_pref, &cw->cpref);      /* term_pref *= cpref  */
    if (st == SRMECH_OK) { st = srmech_ellbase_mono_copy(c, &cw->term_pref, &cw->pacc); }
    return st;
}

/* Build + emit one certificate term: the two ±-pairs θ(mid_a·half_a^±) θ(mid_b·half_b^±)
 * (4 raw args) are each theta-canonicalized into cw->carg[0..3] with their prefactors
 * folded into term_pref = ``scalar`` · ∏(canon prefs); then term_pref is emitted FIRST,
 * then the 4 canonical args (the thetasum wire order: prefactor, theta0..3). */
static srmech_status_t ez_emit_term(ez_ctx_t *c, ez_work_t *w, ez_cwork_t *cw,
                                    const ez_mono_t *scalar, const ez_mono_t *mid_a,
                                    const ez_mono_t *half_a, const ez_mono_t *mid_b,
                                    const ez_mono_t *half_b, int psym,
                                    size_t *mi, size_t *ej)
{
    srmech_status_t st;
    assert(c != NULL && w != NULL && cw != NULL && scalar != NULL);
    assert(mid_a != NULL && half_a != NULL && mid_b != NULL && half_b != NULL);
    st = srmech_ellbase_mono_copy(c, &cw->term_pref, scalar);      /* start from scalar    */
    if (st == SRMECH_OK) { st = ez_mul(c, w, &cw->s0, mid_a, half_a); }      /* mid_a*half_a */
    if (st == SRMECH_OK) { st = ez_canon_fold(c, w, cw, &cw->s0, psym, 0); }
    if (st == SRMECH_OK) { st = srmech_ellbase_mono_inv(c, &cw->s1, half_a); }
    if (st == SRMECH_OK) { st = ez_mul(c, w, &cw->s0, mid_a, &cw->s1); }     /* mid_a/half_a */
    if (st == SRMECH_OK) { st = ez_canon_fold(c, w, cw, &cw->s0, psym, 1); }
    if (st == SRMECH_OK) { st = ez_mul(c, w, &cw->s0, mid_b, half_b); }      /* mid_b*half_b */
    if (st == SRMECH_OK) { st = ez_canon_fold(c, w, cw, &cw->s0, psym, 2); }
    if (st == SRMECH_OK) { st = srmech_ellbase_mono_inv(c, &cw->s1, half_b); }
    if (st == SRMECH_OK) { st = ez_mul(c, w, &cw->s0, mid_b, &cw->s1); }     /* mid_b/half_b */
    if (st == SRMECH_OK) { st = ez_canon_fold(c, w, cw, &cw->s0, psym, 3); }
    if (st == SRMECH_OK) { st = ez_emit_mono(c, cw, &cw->term_pref, mi, ej); }
    if (st == SRMECH_OK) { st = ez_emit_mono(c, cw, &cw->carg[0], mi, ej); }
    if (st == SRMECH_OK) { st = ez_emit_mono(c, cw, &cw->carg[1], mi, ej); }
    if (st == SRMECH_OK) { st = ez_emit_mono(c, cw, &cw->carg[2], mi, ej); }
    if (st == SRMECH_OK) { st = ez_emit_mono(c, cw, &cw->carg[3], mi, ej); }
    return st;
}

/* Build the whole 3-term certificate into the flat thetasum wire (15 monomials) +
 * nthetas = {4,4,4}. Mirrors _connection_split_certificate term-for-term (each theta
 * canonicalized + its prefactor folded, exactly as the Python ThetaSum constructor). */
static srmech_status_t ez_emit_certificate(ez_ctx_t *c, ez_work_t *w, ez_cwork_t *cw,
                                           int psym)
{
    size_t mi = 0;
    size_t ej = 0;
    srmech_status_t st;
    assert(c != NULL && w != NULL && cw != NULL);
    assert(cw->cnum != NULL && cw->exps_flat != NULL);
    st = ez_build_midpoints(c, w, cw);
    if (st != SRMECH_OK) { return st; }
    /* term 1: +1 * θ(bK·(cN/K)^±) * θ(aN·x^±) */
    st = srmech_ellbase_mono_set_one(c, &cw->pref_pm);
    if (st == SRMECH_OK) {
        st = ez_emit_term(c, w, cw, &cw->pref_pm, &cw->bK, &cw->cNK, &cw->aN, &cw->x,
                          psym, &mi, &ej);
    }
    if (st != SRMECH_OK) { return st; }
    cw->nthetas[0] = EZ_CERT_THETAS;
    /* term 2: -1 * θ(aN·(cN/K)^±) * θ(bK·x^±) */
    st = srmech_ellbase_mono_set_one(c, &cw->pref_pm);
    if (st == SRMECH_OK) {                              /* Class-K sign flip (never abs()) */
        cw->pref_pm.coeff.num.sign = -cw->pref_pm.coeff.num.sign;
        st = ez_emit_term(c, w, cw, &cw->pref_pm, &cw->aN, &cw->cNK, &cw->bK, &cw->x,
                          psym, &mi, &ej);
    }
    if (st != SRMECH_OK) { return st; }
    cw->nthetas[1] = EZ_CERT_THETAS;
    /* term 3: +(b/c)(K^2/N) * θ(aN·(bK)^±) * θ(cN/K·x^±) */
    st = ez_emit_term(c, w, cw, &cw->weight, &cw->aN, &cw->bK, &cw->cNK, &cw->x,
                      psym, &mi, &ej);
    if (st != SRMECH_OK) { return st; }
    cw->nthetas[2] = EZ_CERT_THETAS;
    assert(mi == EZ_CERT_MONOS);
    return SRMECH_OK;
}

/* Build the certificate + route the is_zero decision to srmech_thetasum_is_zero. The
 * theta variable is x; ysym = -1 (no second period in this certificate); psym the nome
 * (the same (xsym, -1, psym) call shape srmech_elliptic_gosper uses). */
static srmech_status_t ez_decide(ez_ctx_t *c, ez_work_t *w, ez_cwork_t *cw, int xsym,
                                 int psym, int *out_is_zero)
{
    int is_zero = 0;
    srmech_status_t st;
    assert(c != NULL && w != NULL && cw != NULL && out_is_zero != NULL);
    assert(cw->nthetas != NULL && cw->ts_ws != NULL);
    st = ez_emit_certificate(c, w, cw, psym);
    if (st != SRMECH_OK) { return st; }
    st = srmech_thetasum_is_zero(c->n_syms, xsym, -1, psym, EZ_CERT_TERMS, cw->nthetas,
                                 cw->cnum, cw->cden, cw->exps_flat, c->cap, &is_zero,
                                 cw->ts_ws, cw->ts_ws_len);
    if (st != SRMECH_OK) { return st; }
    *out_is_zero = is_zero;
    return SRMECH_OK;
}

/* ============================================================================ *
 *  arena binders + the public entry
 * ============================================================================ */

/* Carve the recognize-decompose work roster (the reusable raw / canon arrays + scratch). */
static srmech_status_t ez_bind_work(ez_ctx_t *c, ez_work_t *w, size_t cap_arg)
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
        st = srmech_ellbase_bind_mono_arr(c, &w->tmp_mono, EZ_LOCAL_MONOS);
    }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono_arr(c, &w->free_p, EZ_N_FREE); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono(c, &w->a_mono); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono(c, &w->aq); }
    if (st == SRMECH_OK) { st = srmech_ellbase_er_bind_scr(c, &w->s, cap_arg); }
    return st;
}

/* Carve the certificate monomials (symbols + midpoints + scratch). */
static srmech_status_t ez_bind_cwork_monos(ez_ctx_t *c, ez_cwork_t *cw)
{
    srmech_status_t st;
    assert(c != NULL && cw != NULL);
    assert(c->n_syms >= 1u);
    st = srmech_ellbase_bind_mono(c, &cw->N);
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono(c, &cw->K); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono(c, &cw->x); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono(c, &cw->aN); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono(c, &cw->bK); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono(c, &cw->cNK); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono(c, &cw->weight); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono(c, &cw->pref_pm); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono(c, &cw->s0); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono(c, &cw->s1); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono(c, &cw->s2); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono(c, &cw->term_pref); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono(c, &cw->cpref); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono(c, &cw->pacc); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono(c, &cw->z0); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono(c, &cw->z0inv); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono(c, &cw->ctmp); }
    if (st == SRMECH_OK) {
        st = srmech_ellbase_bind_mono_arr(c, &cw->carg, EZ_CERT_THETAS);
    }
    return st;
}

/* The thetasum sub-arena word budget for the certificate decision shape (3 terms, 4
 * thetas each). */
static size_t ez_ts_ws_words(size_t ns, size_t cap)
{
    size_t bytes;
    assert(ns >= 1u);
    assert(cap >= 1u);
    bytes = srmech_thetasum_ws_bound(ns, EZ_CERT_TERMS, EZ_CERT_THETAS, cap);
    return bytes / sizeof(uint32_t) + 16u;
}

/* Carve the flat thetasum wire buffers (cnum/cden bigint arrays + exps rows + nthetas)
 * + the thetasum sub-arena. (Mirrors srmech_elliptic_gosper's eg_bind_vwork_wire.) */
static srmech_status_t ez_bind_cwork_wire(ez_ctx_t *c, ez_cwork_t *cw, size_t ts_ws_words)
{
    size_t i;
    uint32_t *raw;
    srmech_status_t st = SRMECH_OK;
    assert(c != NULL && cw != NULL);
    assert(ts_ws_words >= 1u);
    srmech_ellbase_align8(c);
    raw = srmech_ellbase_take_words(c,
            (EZ_CERT_MONOS * sizeof(srmech_bigint_t) + sizeof(uint32_t) - 1u)
            / sizeof(uint32_t));
    if (raw == NULL) { return SRMECH_ERR_OVERFLOW; }
    cw->cnum = (srmech_bigint_t *)raw;
    srmech_ellbase_align8(c);
    raw = srmech_ellbase_take_words(c,
            (EZ_CERT_MONOS * sizeof(srmech_bigint_t) + sizeof(uint32_t) - 1u)
            / sizeof(uint32_t));
    if (raw == NULL) { return SRMECH_ERR_OVERFLOW; }
    cw->cden = (srmech_bigint_t *)raw;
    for (i = 0; st == SRMECH_OK && i < EZ_CERT_MONOS; i++) {
        st = srmech_ellbase_bind_bi(c, &cw->cnum[i]);
        if (st == SRMECH_OK) { st = srmech_ellbase_bind_bi(c, &cw->cden[i]); }
    }
    if (st != SRMECH_OK) { return st; }
    raw = srmech_ellbase_take_words(c, EZ_CERT_MONOS * c->n_syms);   /* int32 == uint32 word */
    if (raw == NULL) { return SRMECH_ERR_OVERFLOW; }
    cw->exps_flat = (int32_t *)raw;
    srmech_ellbase_align8(c);
    raw = srmech_ellbase_take_words(c,
            (EZ_CERT_TERMS * sizeof(size_t) + sizeof(uint32_t) - 1u) / sizeof(uint32_t));
    if (raw == NULL) { return SRMECH_ERR_OVERFLOW; }
    cw->nthetas = (size_t *)raw;
    srmech_ellbase_align8(c);
    raw = srmech_ellbase_take_words(c, ts_ws_words);
    if (raw == NULL) { return SRMECH_ERR_OVERFLOW; }
    cw->ts_ws = (void *)raw;
    cw->ts_ws_len = ts_ws_words * sizeof(uint32_t);
    return SRMECH_OK;
}

/* The whole working roster, carved once. */
typedef struct ez_all {
    ez_ctx_t   ctx;
    ez_work_t  w;
    ez_ratio_t r;                /* the parsed canonical input term-ratio       */
    ez_cwork_t cw;               /* the certificate build + decide roster        */
} ez_all_t;

/* Carve the whole roster from the caller arena. */
static srmech_status_t ez_bind_all(ez_all_t *A, size_t n_num, size_t n_den, void *ws,
                                   size_t ws_len)
{
    size_t cap_arg = n_num + n_den + 8u;
    size_t ts_words;
    srmech_status_t st;
    assert(A != NULL);
    assert(ws != NULL || ws_len == 0u);                 /* a non-empty arena needs a buffer */
    if (cap_arg < EZ_MAX_THETA) { cap_arg = EZ_MAX_THETA; }
    ts_words = ez_ts_ws_words(A->ctx.n_syms, A->ctx.cap);
    st = srmech_ellbase_er_arena_init(&A->ctx, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    st = ez_bind_work(&A->ctx, &A->w, cap_arg);
    if (st == SRMECH_OK) { st = srmech_ellbase_er_bind_ratio(&A->ctx, &A->r, cap_arg, cap_arg); }
    if (st == SRMECH_OK) { st = ez_bind_cwork_monos(&A->ctx, &A->cw); }
    if (st == SRMECH_OK) { st = ez_bind_cwork_wire(&A->ctx, &A->cw, ts_words); }
    return st;
}

/* The order-1 8w7 zeilberger verdict: parse the input ratio, decompose the VWP 8w7 into
 * a + the 3 free params, build the connection-coefficient certificate from a/b/c and
 * decide it == 0. *has = 1 iff recognized AND the certificate is exactly zero. */
static srmech_status_t ez_run(ez_all_t *A, int xsym, int qsym, int ysym, int psym,
                              int nsym, int ksym, int *has)
{
    int ok = 0;
    int is_zero = 0;
    srmech_status_t st;
    assert(A != NULL && has != NULL);
    assert(qsym >= 0 && nsym >= 0 && ksym >= 0);       /* q + the cert symbols N/K needed */
    *has = 0;
    st = ez_decompose_8w7(&A->ctx, &A->w, &A->r, xsym, qsym, ysym, &ok);
    if (st != SRMECH_OK) { return st; }
    if (!ok) { return SRMECH_OK; }                     /* out of class -> Python decides   */
    st = ez_symbol(&A->ctx, &A->cw.N, nsym);
    if (st == SRMECH_OK) { st = ez_symbol(&A->ctx, &A->cw.K, ksym); }
    if (st == SRMECH_OK) { st = ez_symbol(&A->ctx, &A->cw.x, xsym); }
    if (st != SRMECH_OK) { return st; }
    st = ez_decide(&A->ctx, &A->w, &A->cw, xsym, psym, &is_zero);
    if (st != SRMECH_OK) { return st; }
    *has = is_zero ? 1 : 0;
    return SRMECH_OK;
}

srmech_status_t srmech_elliptic_zeilberger(size_t n_syms, int xsym, int psym, int qsym,
                                           int ysym, int nsym, int ksym,
                                           size_t n_num, size_t n_den,
                                           const srmech_bigint_t *coeff_num,
                                           const srmech_bigint_t *coeff_den,
                                           const int32_t *exps_flat, uint32_t coeff_cap,
                                           int *out_has, void *ws, size_t ws_len)
{
    ez_all_t A = {0};
    int has = 0;
    srmech_status_t st;
    assert(out_has != NULL);
    assert(coeff_num != NULL && coeff_den != NULL && exps_flat != NULL);
    if (out_has == NULL) { return SRMECH_ERR_NULL_ARG; }
    *out_has = 0;
    if (coeff_num == NULL || coeff_den == NULL || exps_flat == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (qsym < 0 || nsym < 0 || ksym < 0) { return SRMECH_OK; }  /* missing symbol -> decline */
    if (n_num > EZ_MAX_THETA || n_den > EZ_MAX_THETA) {
        return SRMECH_OK;                              /* over native scope -> decline    */
    }
    A.ctx.n_syms = (n_syms == 0u) ? 1u : n_syms;
    A.ctx.cap = (coeff_cap < 8u) ? 8u : coeff_cap;
    st = ez_bind_all(&A, n_num, n_den, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    st = ez_parse_input(&A.ctx, &A.w, &A.r, n_num, n_den, coeff_num, coeff_den,
                        exps_flat, psym);
    if (st != SRMECH_OK) { return st; }
    st = ez_run(&A, xsym, qsym, ysym, psym, nsym, ksym, &has);
    if (st != SRMECH_OK) { return st; }
    *out_has = has;
    return SRMECH_OK;
}

/* The minimum `ws_len` BYTES srmech_elliptic_zeilberger needs for the given shape (n_syms
 * symbols, n_num + n_den input theta factors, coeff_cap the per-coefficient significant-
 * limb estimate). Sized to the inputs -- no compiled-in cap. */
size_t srmech_elliptic_zeilberger_ws_bound(size_t n_syms, size_t n_num, size_t n_den,
                                           size_t coeff_cap)
{
    size_t cap = (coeff_cap < 8u) ? 8u : coeff_cap;
    size_t ns = (n_syms == 0u) ? 1u : n_syms;
    size_t cap_arg = n_num + n_den + 8u;
    size_t mw;
    size_t ratios;
    size_t arrays;
    size_t wire;
    size_t ts_words;
    size_t total;
    if (cap_arg < EZ_MAX_THETA) { cap_arg = EZ_MAX_THETA; }
    mw = srmech_ellbase_er_mono_words(cap, ns);
    /* the parsed input ratio (pref + 2*cap_arg arg monomials), padded generously. */
    ratios = 4u * (mw + 2u * cap_arg * mw);
    /* the reusable raw / canon arrays + the scratch / free / base + the cert monomials
     * (symbols + midpoints + the canon-fold scratch + the EZ_CERT_THETAS canon args). */
    arrays = (4u * cap_arg + EZ_LOCAL_MONOS + EZ_N_FREE + 32u + SRMECH_ELL_ER_SCR_MONOS
              + 64u) * mw;
    /* the flat cert wire: EZ_CERT_MONOS bigint pairs + the exps rows + the nthetas row. */
    wire = EZ_CERT_MONOS * (2u * cap + ns + 8u) + 64u;
    ts_words = ez_ts_ws_words(ns, cap);
    total = ratios + arrays + wire + ts_words + cap * 32u + 4096u;
    assert(cap >= 8u);
    assert(total >= ts_words);
    return total * sizeof(uint32_t);
}
