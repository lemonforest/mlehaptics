/*
 * srmech_elliptic_gosper.c -- the ELLIPTIC analog of Gosper's indefinite
 * hypergeometric summation (the FIRST engine op of the ELLIPTIC F929 reduction
 * row, the top of the base-axis degeneration tower elliptic -> q -> ordinary). The
 * GENUINE C peer of srmech.amsc.elliptic_gosper.elliptic_gosper -- a 1:1 STRUCTURAL
 * MIRROR of the pure-Python decompose-and-compute pipeline (peel-coboundary +
 * Weierstrass three-term key-equation y-solve + exact ThetaSum.is_zero verifier),
 * NOT the rc61 bounded geometric-constant shell.
 *
 * Input: an elliptic-hypergeometric term given by its TERM RATIO t(n+1)/t(n) = r(x)
 * (x = q^n) as a full EllRatio -- a theta-quotient prod theta(a x;p)/prod theta(b x;p)
 * over an exact-Q monomial prefactor. The wire form mirrors srmech_ellratio_is_elliptic
 * (the interned symbol-table dimension + the x/p/q interned indices + the num/den theta
 * counts + the flat exact-Q monomial coeff arrays + the flat int32 exponent rows, in
 * the order prefactor, num0..K-1, den0..L-1).
 *
 * Output: when t(n) HAS an elliptic-hypergeometric antidifference T(n) = R(x)*t(n)
 * (so T(n+1) - T(n) = t(n)), the CERTIFICATE R(x) (a full EllRatio: its prefactor
 * exact-Q coefficient + exponent row + the num/den canonical theta-argument exponent
 * rows) satisfying the elliptic Gosper equation R(qx)*r(x) - R(x) = 1; else *out_has=0.
 *
 * The GENUINE pipeline (mirrors _elliptic_gosper_pure exactly):
 *   (0) the elliptic-GEOMETRIC core (_geometric_core): a CONSTANT scalar ratio r = z
 *       (no theta, no prefactor symbols) -> R = z_den/(z_num - z_den) (z == 1 declines).
 *   (1) PEEL the q-shift coboundary (_peel_coboundary) to the theta-GP normal form
 *       r = (A/B)*(sigma C / C): a den factor theta(D) is a C factor iff its q-shift
 *       partner theta(D * q^{e_x(D)}) is a num factor; fold the residual monomial into A.
 *   (2) SOLVE the elliptic Gosper key equation (_solve_certificate) via the Weierstrass
 *       three-term relation: B(x/q) = _xshift_inverse(B); x-params pa/pb/pc of A,
 *       B(x/q), C; frame = B(x/q)/C; for each of the <=8 chiral endianness combos
 *       y = (sc/sa)/[theta(sb*sa) theta(sb/sa)], cert = frame*y; ACCEPT the first whose
 *       residual ThetaSum (cert.qshift()*r - cert - 1) is_zero EXACTLY (srmech_thetasum
 *       _is_zero) -- the same no-hallucination standard as the pure path.
 *
 * Reference (MPM-verified at build): George Gasper & Michael Schlosser, "Summation,
 * transformation, and expansion formulas for multibasic theta hypergeometric series,"
 * Adv. Stud. Contemp. Math. (Kyungshang) 11, no. 1 (2005), 67-84 (arXiv:math/0505215)
 * -- derived "using indefinite summation"; the key equation is the Weierstrass three-
 * term relation, Rosengren arXiv:1608.06161 Sec.1.4 Eq.1.12.
 *
 * A has=0 is NEVER a definitive "no certificate" (the Python dispatch trusts only has=1
 * and re-verifies it in exact Q before use); on any overflow/too-small-arena the peer
 * returns SRMECH_ERR_OVERFLOW and the Python re-runs its COMPLETE pure path.
 *
 * The whole peer is malloc-free (JPL Rule 3): every working monomial / EllRatio /
 * scratch is carved from the caller arena `ws`. Byte-identical to the Python certificate
 * at ANY magnitude (full bignum). Class-K sign is an int +/-1, never abs().
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto/recursion): OK -- iterative, flat helpers
 *   - Rule 2 (bounded loops)    : OK -- bounded by n_num / n_den / the 8-combo sweep
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

/* The maximum theta-factor count the genuine native scope handles per ratio (the
 * single-Weierstrass class is small: r has <=4 num + <=4 den; the residual products
 * stay bounded). An over-cap input returns OVERFLOW and the Python decides. */
#define EG_MAX_THETA 32u

/* ---- shared-kernel aliases (the single copy lives in srmech_ellbase.c) ------- */
typedef srmech_ell_ctx_t       eg_ctx_t;
typedef srmech_ell_mono_t      eg_mono_t;
typedef srmech_ell_er_ratio_t  eg_ratio_t;
typedef srmech_ell_er_scr_t    eg_scr_t;

/* The working roster for the whole pipeline, carved once from the arena. */
typedef struct eg_work {
    eg_scr_t   s;                /* the EllRatio construction scratch        */
    eg_mono_t *raw_num;          /* reusable raw num-arg arrays for er_build  */
    eg_mono_t *raw_den;
    eg_mono_t *cn;               /* er_build canon scratch                    */
    eg_mono_t *cd;
    eg_mono_t *part_num;         /* GP-partition: surviving A num args        */
    eg_mono_t *part_den;         /* GP-partition: surviving B den args        */
    eg_mono_t *part_c;           /* GP-partition: coboundary C args           */
    eg_mono_t *tmp_mono;         /* EG_LOCAL_MONOS general monomials          */
    size_t     cap_arg;          /* per-array theta-arg capacity              */
} eg_work_t;

#define EG_LOCAL_MONOS 16u

/* ============================================================================ *
 *  EllRatio working algebra over eg_ratio_t (mirrors the carrier methods)
 * ============================================================================ */

/* out := EllRatio(pref, num, den) canonical (er_build folds + cancels + sorts). */
static srmech_status_t eg_er_build(eg_ctx_t *c, eg_work_t *w, eg_ratio_t *out,
                                   const eg_mono_t *pref, const eg_mono_t *num,
                                   size_t n_num, const eg_mono_t *den, size_t n_den,
                                   int psym)
{
    assert(c != NULL && w != NULL && out != NULL && pref != NULL);
    assert(n_num <= w->cap_arg && n_den <= w->cap_arg);
    return srmech_ellbase_er_build(c, out, pref, num, n_num, den, n_den, psym,
                                   &w->s, w->cn, w->cap_arg, w->cd, w->cap_arg);
}

/* out := a * b (EllRatio multiply: EllRatio(pref_a*pref_b, num_a+num_b, den_a+den_b)
 * re-canonicalized by er_build -- cancels matching thetas num<->den, sorts). */
static srmech_status_t eg_er_mul(eg_ctx_t *c, eg_work_t *w, eg_ratio_t *out,
                                 const eg_ratio_t *a, const eg_ratio_t *b, int psym)
{
    eg_mono_t prefm = {0};
    size_t i;
    size_t nn = 0;
    size_t nd = 0;
    srmech_status_t st;
    assert(c != NULL && w != NULL && out != NULL && a != NULL && b != NULL);
    assert(a->n_num + b->n_num <= w->cap_arg && a->n_den + b->n_den <= w->cap_arg);
    prefm = w->tmp_mono[0];
    st = srmech_ellbase_mono_mul(c, &prefm, &a->pref, &b->pref, &w->s.g, &w->s.t0,
                                 &w->s.t1);
    if (st != SRMECH_OK) { return st; }
    for (i = 0; i < a->n_num; i++) {
        st = srmech_ellbase_mono_copy(c, &w->raw_num[nn++], &a->num[i]);
        if (st != SRMECH_OK) { return st; }
    }
    for (i = 0; i < b->n_num; i++) {
        st = srmech_ellbase_mono_copy(c, &w->raw_num[nn++], &b->num[i]);
        if (st != SRMECH_OK) { return st; }
    }
    for (i = 0; i < a->n_den; i++) {
        st = srmech_ellbase_mono_copy(c, &w->raw_den[nd++], &a->den[i]);
        if (st != SRMECH_OK) { return st; }
    }
    for (i = 0; i < b->n_den; i++) {
        st = srmech_ellbase_mono_copy(c, &w->raw_den[nd++], &b->den[i]);
        if (st != SRMECH_OK) { return st; }
    }
    return eg_er_build(c, w, out, &prefm, w->raw_num, nn, w->raw_den, nd, psym);
}

/* out := 1 / a (EllRatio.inv: swap num<->den, invert prefactor; NO re-canon since the
 * inputs are already canonical -- EllRatio._wrap). a nonzero. */
static srmech_status_t eg_er_inv(eg_ctx_t *c, eg_ratio_t *out, const eg_ratio_t *a)
{
    size_t i;
    srmech_status_t st;
    assert(c != NULL && out != NULL && a != NULL);
    assert(!a->is_zero);
    st = srmech_ellbase_mono_inv(c, &out->pref, &a->pref);
    if (st != SRMECH_OK) { return st; }
    for (i = 0; i < a->n_den; i++) {                 /* out.num = a.den */
        st = srmech_ellbase_mono_copy(c, &out->num[i], &a->den[i]);
        if (st != SRMECH_OK) { return st; }
    }
    for (i = 0; i < a->n_num; i++) {                 /* out.den = a.num */
        st = srmech_ellbase_mono_copy(c, &out->den[i], &a->num[i]);
        if (st != SRMECH_OK) { return st; }
    }
    out->n_num = a->n_den;
    out->n_den = a->n_num;
    out->is_zero = 0;
    return SRMECH_OK;
}

/* out := the summation shift x -> q*x (qshift) of a (each arg + the prefactor gains
 * q^{x-exp}), then er_build re-canonicalizes. `inverse` -> the x -> x/q shift. */
static srmech_status_t eg_er_shift(eg_ctx_t *c, eg_work_t *w, eg_ratio_t *out,
                                   const eg_ratio_t *a, int xsym, int qsym, int psym,
                                   int inverse)
{
    eg_mono_t prefm = {0};
    size_t i;
    srmech_status_t st;
    assert(c != NULL && w != NULL && out != NULL && a != NULL);
    assert(a->n_num <= w->cap_arg && a->n_den <= w->cap_arg);
    prefm = w->tmp_mono[1];
    st = srmech_ellbase_er_qshift_arg(c, &prefm, &a->pref, xsym, qsym, inverse);
    if (st != SRMECH_OK) { return st; }
    for (i = 0; i < a->n_num; i++) {
        st = srmech_ellbase_er_qshift_arg(c, &w->raw_num[i], &a->num[i], xsym, qsym,
                                          inverse);
        if (st != SRMECH_OK) { return st; }
    }
    for (i = 0; i < a->n_den; i++) {
        st = srmech_ellbase_er_qshift_arg(c, &w->raw_den[i], &a->den[i], xsym, qsym,
                                          inverse);
        if (st != SRMECH_OK) { return st; }
    }
    return eg_er_build(c, w, out, &prefm, w->raw_num, a->n_num, w->raw_den, a->n_den,
                       psym);
}

/* The x-param alpha of a theta-product's x-pair theta(alpha*x)theta(alpha/x): strip x
 * from the canonical x-dependent factor (e_x == +1 -> arg/x ; e_x == -1 -> (arg*x)^-1).
 * *ok=1 + writes out_param on success; *ok=0 when no single-x factor (out of class). */
static srmech_status_t eg_x_param(eg_ctx_t *c, eg_mono_t *out_param,
                                  const eg_ratio_t *p, int xsym, int *ok,
                                  eg_mono_t *tmp)
{
    size_t i;
    srmech_status_t st;
    int32_t e;
    assert(c != NULL && out_param != NULL && p != NULL && ok != NULL && tmp != NULL);
    assert(xsym >= -1);
    *ok = 0;
    if (xsym < 0) { return SRMECH_OK; }
    for (i = 0; i < p->n_num; i++) {
        e = p->num[i].exps[xsym];
        if (e == 1) {                                /* alpha = arg * x^-1 */
            st = srmech_ellbase_mono_copy(c, out_param, &p->num[i]);
            if (st != SRMECH_OK) { return st; }
            out_param->exps[xsym] -= 1;
            *ok = 1;
            return SRMECH_OK;
        }
        if (e == -1) {                               /* alpha = (arg * x)^-1 */
            st = srmech_ellbase_mono_copy(c, tmp, &p->num[i]);
            if (st != SRMECH_OK) { return st; }
            tmp->exps[xsym] += 1;
            *ok = 1;
            return srmech_ellbase_mono_inv(c, out_param, tmp);
        }
    }
    return SRMECH_OK;                                /* no x-dependent factor */
}

/* ============================================================================ *
 *  the residual ThetaSum is_zero verifier (marshal to srmech_thetasum_is_zero)
 * ============================================================================ */

/* A theta-product = an EllMonomial prefactor + a theta-arg multiset; the residual of the
 * Gosper equation is a 3-term cleared ThetaSum numerator over a common denominator. */
typedef struct eg_term {
    eg_mono_t  pref;
    eg_mono_t *thetas;
    size_t     n;
} eg_term_t;

/* Multiply a term's theta-multiset by the SURPLUS denominator factors not already in
 * its own denominator (the _num_over re-basing), folding the prefactor unchanged. The
 * surplus = common_den \ this_den (multiset diff over canonical args). Appends the kept
 * surplus theta args to out_thetas (already holding the term's own num args). */
static srmech_status_t eg_rebase_term(eg_ctx_t *c, eg_mono_t *out_thetas, size_t *n_out,
                                      const eg_mono_t *common, size_t n_common,
                                      const eg_mono_t *self_den, size_t n_self_den,
                                      int *used_flags)
{
    size_t i;
    size_t j;
    srmech_status_t st;
    assert(c != NULL && out_thetas != NULL && n_out != NULL && used_flags != NULL);
    assert((common != NULL || n_common == 0u) && (self_den != NULL || n_self_den == 0u));
    for (j = 0; j < n_self_den; j++) { used_flags[j] = 0; }
    for (i = 0; i < n_common; i++) {
        int matched = 0;
        for (j = 0; j < n_self_den; j++) {
            if (used_flags[j]) { continue; }
            if (srmech_ellbase_mono_eq(c, &common[i], &self_den[j])) {
                used_flags[j] = 1;                   /* this den factor is covered */
                matched = 1;
                break;
            }
        }
        if (!matched) {                              /* surplus -> multiplies the num */
            st = srmech_ellbase_mono_copy(c, &out_thetas[(*n_out)++], &common[i]);
            if (st != SRMECH_OK) { return st; }
        }
    }
    return SRMECH_OK;
}

/* Multiset-union the den theta-args of two ratios into `out` (max multiplicity per
 * canonical arg). Returns the union count. Mirrors _common_denominator's theta union. */
static srmech_status_t eg_den_union(eg_ctx_t *c, eg_mono_t *out, size_t *n_out,
                                    const eg_mono_t *a, size_t na,
                                    const eg_mono_t *b, size_t nb)
{
    size_t i;
    size_t j;
    size_t cnt_b;
    srmech_status_t st;
    assert(c != NULL && out != NULL && n_out != NULL);
    assert((a != NULL || na == 0u) && (b != NULL || nb == 0u));
    *n_out = 0;
    for (i = 0; i < na; i++) {                       /* every a factor, full mult */
        st = srmech_ellbase_mono_copy(c, &out[(*n_out)++], &a[i]);
        if (st != SRMECH_OK) { return st; }
    }
    for (j = 0; j < nb; j++) {                        /* top up b's surplus mult */
        size_t cnt_a = 0;
        size_t k;
        for (i = 0; i < na; i++) {
            if (srmech_ellbase_mono_eq(c, &a[i], &b[j])) { cnt_a++; }
        }
        cnt_b = 0;
        for (k = 0; k <= j; k++) {
            if (srmech_ellbase_mono_eq(c, &b[k], &b[j])) { cnt_b++; }
        }
        if (cnt_b > cnt_a) {                          /* b needs one more copy */
            st = srmech_ellbase_mono_copy(c, &out[(*n_out)++], &b[j]);
            if (st != SRMECH_OK) { return st; }
        }
    }
    return SRMECH_OK;
}

/* The verifier working roster: the residual's three cleared-numerator terms + the
 * common-denominator union + the flat thetasum-bridge buffers, carved from the arena. */
typedef struct eg_vwork {
    eg_ratio_t       prod;       /* P = cert.qshift() * r                    */
    eg_ratio_t       qsh;        /* cert.qshift()                            */
    eg_mono_t       *common;     /* common-denominator theta union           */
    eg_term_t        term[3];    /* the cleared numerator terms              */
    eg_mono_t        coeff_pm;   /* the +/-1 scalar monomial                 */
    srmech_bigint_t  g;          /* monomial-mul scratch (g/t0/t1)           */
    srmech_bigint_t  t0;
    srmech_bigint_t  t1;
    int             *used;       /* surplus-cover flags                      */
    /* flat thetasum wire buffers */
    srmech_bigint_t *cnum;
    srmech_bigint_t *cden;
    int32_t         *exps_flat;
    size_t          *nthetas;
    void            *ts_ws;
    size_t           ts_ws_len;
    size_t           cap_theta;  /* per-term theta capacity                  */
} eg_vwork_t;

/* Append one cleared-numerator term (coeff * term.pref * thetas * surplus) to the flat
 * thetasum wire buffers at monomial cursor *mi / exps cursor *ej. The prefactor row is
 * (coeff*pref); each theta arg is its own dense exps row. */
static srmech_status_t eg_emit_term(eg_ctx_t *c, const eg_term_t *t,
                                    srmech_bigint_t *cnum, srmech_bigint_t *cden,
                                    int32_t *exps_flat, size_t *mi, size_t *ej)
{
    size_t i;
    srmech_status_t st;
    assert(c != NULL && t != NULL && cnum != NULL && cden != NULL);
    assert(exps_flat != NULL && mi != NULL && ej != NULL);
    st = srmech_bigint_copy(&cnum[*mi], &t->pref.coeff.num);
    if (st == SRMECH_OK) { st = srmech_bigint_copy(&cden[*mi], &t->pref.coeff.den); }
    if (st != SRMECH_OK) { return st; }
    memcpy(exps_flat + *ej, t->pref.exps, c->n_syms * sizeof(int32_t));
    (*mi)++;
    *ej += c->n_syms;
    for (i = 0; i < t->n; i++) {
        st = srmech_bigint_copy(&cnum[*mi], &t->thetas[i].coeff.num);
        if (st == SRMECH_OK) { st = srmech_bigint_copy(&cden[*mi], &t->thetas[i].coeff.den); }
        if (st != SRMECH_OK) { return st; }
        memcpy(exps_flat + *ej, t->thetas[i].exps, c->n_syms * sizeof(int32_t));
        (*mi)++;
        *ej += c->n_syms;
    }
    return SRMECH_OK;
}

/* Build one cleared term from a source ratio `r` (its numerator over the common
 * denominator): out.pref = (coeff)*r.pref ; out.thetas = r.num ++ (common \ r.den). */
static srmech_status_t eg_build_term(eg_ctx_t *c, eg_vwork_t *v, eg_term_t *out,
                                     const eg_ratio_t *r, int sign,
                                     const eg_mono_t *common, size_t n_common)
{
    size_t i;
    srmech_status_t st;
    assert(c != NULL && v != NULL && out != NULL && r != NULL);
    assert(r->n_num + n_common <= v->cap_theta);
    st = srmech_ellbase_mono_set_one(c, &v->coeff_pm);
    if (st != SRMECH_OK) { return st; }
    if (sign < 0) { v->coeff_pm.coeff.num.sign = -v->coeff_pm.coeff.num.sign; }
    st = srmech_ellbase_mono_mul(c, &out->pref, &r->pref, &v->coeff_pm,
                                 &v->g, &v->t0, &v->t1);
    if (st != SRMECH_OK) { return st; }
    out->n = 0;
    for (i = 0; i < r->n_num; i++) {                 /* the term's own num thetas */
        st = srmech_ellbase_mono_copy(c, &out->thetas[out->n++], &r->num[i]);
        if (st != SRMECH_OK) { return st; }
    }
    return eg_rebase_term(c, out->thetas, &out->n, common, n_common, r->den, r->n_den,
                          v->used);
}

/* Build term2 = -1 * "1" (the unit ThetaSum term, theta-free, empty own-denominator):
 * pref = -1, thetas = the WHOLE common denominator (surplus of empty self-den). */
static srmech_status_t eg_build_unit_term(eg_ctx_t *c, eg_vwork_t *v, eg_term_t *out,
                                          const eg_mono_t *common, size_t n_common)
{
    srmech_status_t st;
    assert(c != NULL && v != NULL && out != NULL);
    assert(n_common <= v->cap_theta);
    st = srmech_ellbase_mono_set_one(c, &v->coeff_pm);
    if (st != SRMECH_OK) { return st; }
    v->coeff_pm.coeff.num.sign = -v->coeff_pm.coeff.num.sign;            /* -1 */
    st = srmech_ellbase_mono_copy(c, &out->pref, &v->coeff_pm);
    if (st != SRMECH_OK) { return st; }
    out->n = 0;
    return eg_rebase_term(c, out->thetas, &out->n, common, n_common, NULL, 0, v->used);
}

/* Marshal the three cleared terms into the flat thetasum wire buffers + route the
 * is_zero decision to srmech_thetasum_is_zero. *out_ok=1 iff the residual is zero. */
static srmech_status_t eg_decide_terms(eg_ctx_t *c, eg_vwork_t *v, int xsym, int psym,
                                       int *out_ok)
{
    size_t mi = 0;
    size_t ej = 0;
    size_t i;
    int is_zero = 1;
    srmech_status_t st;
    assert(c != NULL && v != NULL && out_ok != NULL);
    assert(v->cnum != NULL && v->cden != NULL);
    for (i = 0; i < 3; i++) {
        v->nthetas[i] = v->term[i].n;
        st = eg_emit_term(c, &v->term[i], v->cnum, v->cden, v->exps_flat, &mi, &ej);
        if (st != SRMECH_OK) { return st; }
    }
    st = srmech_thetasum_is_zero(c->n_syms, xsym, -1, psym, 3u, v->nthetas,
                                 v->cnum, v->cden, v->exps_flat, c->cap, &is_zero,
                                 v->ts_ws, v->ts_ws_len);
    if (st != SRMECH_OK) { return st; }
    *out_ok = is_zero;
    return SRMECH_OK;
}

/* Decide R(qx)*r - R - 1 == 0 EXACTLY (the elliptic Gosper equation): build the
 * residual's three cleared-numerator terms over the common denominator, then decide.
 * *out_ok=1 iff the residual is zero. */
static srmech_status_t eg_verify(eg_ctx_t *c, eg_work_t *w, eg_vwork_t *v,
                                 const eg_ratio_t *cert, const eg_ratio_t *r,
                                 int xsym, int qsym, int psym, int *out_ok)
{
    size_t n_common = 0;
    srmech_status_t st;
    assert(c != NULL && w != NULL && v != NULL && cert != NULL && r != NULL);
    assert(out_ok != NULL);
    *out_ok = 0;
    st = eg_er_shift(c, w, &v->qsh, cert, xsym, qsym, psym, /*inverse*/0);  /* R(qx) */
    if (st != SRMECH_OK) { return st; }
    st = eg_er_mul(c, w, &v->prod, &v->qsh, r, psym);                       /* R(qx)*r */
    if (st != SRMECH_OK) { return st; }
    if (v->prod.n_den + cert->n_den > v->cap_theta
        || v->prod.n_num + v->cap_theta > v->cap_theta + v->cap_theta) {
        return SRMECH_ERR_OVERFLOW;
    }
    st = eg_den_union(c, v->common, &n_common, v->prod.den, v->prod.n_den,
                      cert->den, cert->n_den);                /* common denominator */
    if (st != SRMECH_OK) { return st; }
    st = eg_build_term(c, v, &v->term[0], &v->prod, +1, v->common, n_common);  /* +P */
    if (st == SRMECH_OK) {
        st = eg_build_term(c, v, &v->term[1], cert, -1, v->common, n_common);  /* -R */
    }
    if (st == SRMECH_OK) {
        st = eg_build_unit_term(c, v, &v->term[2], v->common, n_common);       /* -1 */
    }
    if (st != SRMECH_OK) { return st; }
    return eg_decide_terms(c, v, xsym, psym, out_ok);
}

/* ============================================================================ *
 *  PEEL the q-shift coboundary (_peel_coboundary) -> the theta-GP normal form
 * ============================================================================ */

/* The GP-normal-form factors A / B / C of r = (A/B)*(sigma C / C). */
typedef struct eg_gp {
    eg_ratio_t a;
    eg_ratio_t b;
    eg_ratio_t cco;          /* the coboundary C                              */
} eg_gp_t;

/* The residual-fold scratch (the four EllRatios of the _peel_coboundary fold check). */
typedef struct eg_pscr {
    eg_ratio_t t1;       /* A * B.inv()                                       */
    eg_ratio_t t2;       /* C.qshift() * C.inv()                              */
    eg_ratio_t t3;       /* t1 * t2                                           */
    eg_ratio_t t4;       /* t3.inv()                                          */
    eg_ratio_t residual; /* r * t3.inv()                                      */
    eg_ratio_t tmpr;     /* a generic intermediate (qshift / inv landing)     */
} eg_pscr_t;

/* Partition r's num/den into the coboundary C + the residual A (num) / B (den): a den
 * factor theta(D) is a C factor iff theta(D * q^{e_x(D)}) (a RAW monomial, NOT re-
 * canonicalized -- Python compares Theta args directly) equals a num factor. */
static srmech_status_t eg_partition(eg_ctx_t *c, eg_work_t *w, const eg_ratio_t *r,
                                    int xsym, int qsym, size_t *n_keep_num,
                                    size_t *n_keep_den, size_t *n_c)
{
    eg_mono_t partner = {0};
    size_t i;
    size_t j;
    srmech_status_t st;
    int *num_used = w->s.used;
    assert(c != NULL && w != NULL && r != NULL && num_used != NULL);
    assert(n_keep_num != NULL && n_keep_den != NULL && n_c != NULL);
    partner = w->tmp_mono[2];
    *n_keep_num = 0;
    *n_keep_den = 0;
    *n_c = 0;
    for (i = 0; i < r->n_num; i++) { num_used[i] = 0; }
    for (j = 0; j < r->n_den; j++) {
        int hit = -1;
        st = srmech_ellbase_er_qshift_arg(c, &partner, &r->den[j], xsym, qsym, 0);
        if (st != SRMECH_OK) { return st; }
        for (i = 0; i < r->n_num; i++) {
            if (!num_used[i] && srmech_ellbase_mono_eq(c, &r->num[i], &partner)) {
                hit = (int)i;
                break;
            }
        }
        if (hit >= 0) {                              /* theta(D) is a C factor */
            num_used[(size_t)hit] = 1;
            st = srmech_ellbase_mono_copy(c, &w->part_c[(*n_c)++], &r->den[j]);
        } else {                                     /* theta(D) survives in B */
            st = srmech_ellbase_mono_copy(c, &w->part_den[(*n_keep_den)++], &r->den[j]);
        }
        if (st != SRMECH_OK) { return st; }
    }
    for (i = 0; i < r->n_num; i++) {                 /* surviving num -> A */
        if (num_used[i]) { continue; }
        st = srmech_ellbase_mono_copy(c, &w->part_num[(*n_keep_num)++], &r->num[i]);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* The exact residual-fold check r == (A/B)*(sigma C / C): build t3 = (A*B.inv())*(
 * C.qshift()*C.inv()), residual = r * t3.inv(); the peel is EXACT iff residual carries
 * no theta. On success fold residual's prefactor monomial into A. *out_ok set. */
static srmech_status_t eg_peel_fold(eg_ctx_t *c, eg_work_t *w, eg_gp_t *gp,
                                    eg_pscr_t *ps, const eg_ratio_t *r, int xsym,
                                    int qsym, int psym, int *out_ok)
{
    eg_mono_t newpref = {0};
    srmech_status_t st;
    assert(c != NULL && w != NULL && gp != NULL && ps != NULL && r != NULL);
    assert(out_ok != NULL);
    *out_ok = 0;
    st = eg_er_inv(c, &ps->tmpr, &gp->b);                          /* B.inv() */
    if (st == SRMECH_OK) { st = eg_er_mul(c, w, &ps->t1, &gp->a, &ps->tmpr, psym); }
    if (st == SRMECH_OK) {
        st = eg_er_shift(c, w, &ps->tmpr, &gp->cco, xsym, qsym, psym, 0);  /* C.qshift */
    }
    if (st == SRMECH_OK) { st = eg_er_inv(c, &ps->t4, &gp->cco); }         /* C.inv() */
    if (st == SRMECH_OK) { st = eg_er_mul(c, w, &ps->t2, &ps->tmpr, &ps->t4, psym); }
    if (st == SRMECH_OK) { st = eg_er_mul(c, w, &ps->t3, &ps->t1, &ps->t2, psym); }
    if (st == SRMECH_OK) { st = eg_er_inv(c, &ps->t4, &ps->t3); }          /* t3.inv() */
    if (st == SRMECH_OK) { st = eg_er_mul(c, w, &ps->residual, r, &ps->t4, psym); }
    if (st != SRMECH_OK) { return st; }
    if (ps->residual.n_num != 0u || ps->residual.n_den != 0u) {
        return SRMECH_OK;                          /* not a pure monomial -> decline */
    }
    newpref = w->tmp_mono[3];
    st = srmech_ellbase_mono_mul(c, &newpref, &gp->a.pref, &ps->residual.pref,
                                 &w->s.g, &w->s.t0, &w->s.t1);   /* A *= residual.pref */
    if (st != SRMECH_OK) { return st; }
    st = srmech_ellbase_mono_copy(c, &gp->a.pref, &newpref);
    if (st != SRMECH_OK) { return st; }
    *out_ok = 1;
    return SRMECH_OK;
}

/* Bring r to the GP normal form r = (A/B)*(sigma C / C). *out_ok=0 (declines) if the
 * residual fold is not a pure monomial (out of the structurally-decidable class). */
static srmech_status_t eg_peel(eg_ctx_t *c, eg_work_t *w, eg_gp_t *gp, eg_pscr_t *ps,
                               const eg_ratio_t *r, int xsym, int qsym, int psym,
                               int *out_ok)
{
    eg_mono_t unit = {0};
    size_t nkn = 0;
    size_t nkd = 0;
    size_t ncc = 0;
    srmech_status_t st;
    assert(c != NULL && w != NULL && gp != NULL && ps != NULL && r != NULL);
    assert(out_ok != NULL && r->n_num <= w->cap_arg && r->n_den <= w->cap_arg);
    *out_ok = 0;
    st = eg_partition(c, w, r, xsym, qsym, &nkn, &nkd, &ncc);
    if (st != SRMECH_OK) { return st; }
    unit = w->tmp_mono[4];
    st = srmech_ellbase_mono_set_one(c, &unit);
    if (st != SRMECH_OK) { return st; }
    /* C = EllRatio(num = c_arg) [NO prefactor] ; A = EllRatio(r.pref, num = keep_num) ;
     * B = EllRatio(num = keep_den). */
    st = eg_er_build(c, w, &gp->cco, &unit, w->part_c, ncc, NULL, 0, psym);
    if (st == SRMECH_OK) {
        st = eg_er_build(c, w, &gp->a, &r->pref, w->part_num, nkn, NULL, 0, psym);
    }
    if (st == SRMECH_OK) {
        st = eg_er_build(c, w, &gp->b, &unit, w->part_den, nkd, NULL, 0, psym);
    }
    if (st != SRMECH_OK) { return st; }
    return eg_peel_fold(c, w, gp, ps, r, xsym, qsym, psym, out_ok);
}

/* ============================================================================ *
 *  SOLVE the elliptic Gosper key equation (_solve_certificate)
 * ============================================================================ */

/* The solve-certificate scratch: the x-params + the per-endianness candidate build. */
typedef struct eg_swork {
    eg_mono_t  pa;       /* x-param of A                                      */
    eg_mono_t  pb;       /* x-param of B(x/q)                                 */
    eg_mono_t  pc;       /* x-param of C                                      */
    eg_mono_t  sa;       /* the chosen endianness of pa / pb / pc            */
    eg_mono_t  sb;
    eg_mono_t  sc;
    eg_mono_t  ypref;    /* sc * sa.inv()                                     */
    eg_mono_t  yd0;      /* theta arg sb*sa                                   */
    eg_mono_t  yd1;      /* theta arg sb/sa                                   */
    eg_mono_t  scratch;  /* generic monomial scratch                         */
    eg_ratio_t b_shift;  /* B(x/q)                                           */
    eg_ratio_t cinv;     /* C.inv()                                          */
    eg_ratio_t frame;    /* B(x/q)/C                                          */
    eg_ratio_t yrat;     /* the y EllRatio                                    */
    eg_ratio_t cert;     /* frame * y (the candidate certificate)            */
} eg_swork_t;

/* Build the y EllRatio for one endianness (sa, sb, sc): y = EllRatio(sc*sa.inv(),
 * den = (theta(sb*sa), theta(sb/sa))) and cert = frame * y. */
static srmech_status_t eg_build_candidate(eg_ctx_t *c, eg_work_t *w, eg_swork_t *sw,
                                          int psym)
{
    srmech_status_t st;
    assert(c != NULL && w != NULL && sw != NULL);
    assert(sw->sa.exps != NULL && sw->sb.exps != NULL && sw->sc.exps != NULL);
    st = srmech_ellbase_mono_inv(c, &sw->scratch, &sw->sa);          /* sa.inv() */
    if (st == SRMECH_OK) {
        st = srmech_ellbase_mono_mul(c, &sw->ypref, &sw->sc, &sw->scratch,
                                     &w->s.g, &w->s.t0, &w->s.t1);   /* sc*sa.inv() */
    }
    if (st == SRMECH_OK) {
        st = srmech_ellbase_mono_mul(c, &sw->yd0, &sw->sb, &sw->sa,
                                     &w->s.g, &w->s.t0, &w->s.t1);   /* sb*sa */
    }
    if (st == SRMECH_OK) { st = srmech_ellbase_mono_inv(c, &sw->scratch, &sw->sa); }
    if (st == SRMECH_OK) {
        st = srmech_ellbase_mono_mul(c, &sw->yd1, &sw->sb, &sw->scratch,
                                     &w->s.g, &w->s.t0, &w->s.t1);   /* sb*sa.inv() */
    }
    if (st != SRMECH_OK) { return st; }
    w->raw_den[0] = sw->yd0;                          /* y den thetas */
    w->raw_den[1] = sw->yd1;
    st = eg_er_build(c, w, &sw->yrat, &sw->ypref, NULL, 0, w->raw_den, 2u, psym);
    if (st != SRMECH_OK) { return st; }
    return eg_er_mul(c, w, &sw->cert, &sw->frame, &sw->yrat, psym);
}

/* Pick endianness `e` (a 3-bit code) of pa/pb/pc into sa/sb/sc (bit set -> the inverse).
 * Mirrors the (sa in (pa, pa.inv())) x (sb ...) x (sc ...) triple loop order. */
static srmech_status_t eg_pick_endianness(eg_ctx_t *c, eg_swork_t *sw, unsigned e)
{
    srmech_status_t st;
    assert(c != NULL && sw != NULL);
    assert(e < 8u);
    st = (e & 4u) ? srmech_ellbase_mono_inv(c, &sw->sa, &sw->pa)
                  : srmech_ellbase_mono_copy(c, &sw->sa, &sw->pa);
    if (st != SRMECH_OK) { return st; }
    st = (e & 2u) ? srmech_ellbase_mono_inv(c, &sw->sb, &sw->pb)
                  : srmech_ellbase_mono_copy(c, &sw->sb, &sw->pb);
    if (st != SRMECH_OK) { return st; }
    return (e & 1u) ? srmech_ellbase_mono_inv(c, &sw->sc, &sw->pc)
                    : srmech_ellbase_mono_copy(c, &sw->sc, &sw->pc);
}

/* Solve the elliptic Gosper key equation for the GP factors (A, B, C): try the <=8
 * chiral endianness candidates and ACCEPT the first whose residual ThetaSum is zero.
 * *out_found=1 + sw->cert holds the verified certificate; *out_found=0 declines. */
static srmech_status_t eg_solve(eg_ctx_t *c, eg_work_t *w, eg_swork_t *sw, eg_vwork_t *v,
                                const eg_gp_t *gp, const eg_ratio_t *r, int xsym,
                                int qsym, int psym, int *out_found)
{
    unsigned e;
    int ok_a = 0;
    int ok_b = 0;
    int ok_c = 0;
    srmech_status_t st;
    assert(c != NULL && w != NULL && sw != NULL && v != NULL && gp != NULL);
    assert(r != NULL && out_found != NULL);
    *out_found = 0;
    st = eg_er_shift(c, w, &sw->b_shift, &gp->b, xsym, qsym, psym, /*inverse*/1);
    if (st != SRMECH_OK) { return st; }
    st = eg_x_param(c, &sw->pa, &gp->a, xsym, &ok_a, &sw->scratch);
    if (st == SRMECH_OK) { st = eg_x_param(c, &sw->pb, &sw->b_shift, xsym, &ok_b,
                                           &sw->scratch); }
    if (st == SRMECH_OK) { st = eg_x_param(c, &sw->pc, &gp->cco, xsym, &ok_c,
                                           &sw->scratch); }
    if (st != SRMECH_OK) { return st; }
    if (!ok_a || !ok_b || !ok_c) { return SRMECH_OK; }   /* not single-Weierstrass */
    st = eg_er_inv(c, &sw->cinv, &gp->cco);                  /* C.inv() */
    if (st == SRMECH_OK) {
        st = eg_er_mul(c, w, &sw->frame, &sw->b_shift, &sw->cinv, psym);  /* frame */
    }
    if (st != SRMECH_OK) { return st; }
    for (e = 0; e < 8u; e++) {
        int ok = 0;
        st = eg_pick_endianness(c, sw, e);
        if (st == SRMECH_OK) { st = eg_build_candidate(c, w, sw, psym); }
        if (st == SRMECH_OK) { st = eg_verify(c, w, v, &sw->cert, r, xsym, qsym, psym,
                                              &ok); }
        if (st != SRMECH_OK) { return st; }
        if (ok) { *out_found = 1; return SRMECH_OK; }
    }
    return SRMECH_OK;
}

/* ============================================================================ *
 *  the elliptic-GEOMETRIC core (_geometric_core) + output marshaling
 * ============================================================================ */

/* The constant-scalar core: a CONSTANT term ratio r = z = z_num/z_den (no theta, no
 * prefactor symbols) -> cert R = z_den/(z_num - z_den) (a scalar EllRatio). *got=1 +
 * out_cert holds the scalar cert ratio; *got=0 when z == 1 (no finite cert) or the
 * input is not a pure scalar. dn / g / t0 / t1 are caller scratch bigints (distinct). */
static srmech_status_t eg_geometric_core(eg_ctx_t *c, eg_ratio_t *out_cert,
                                         const eg_mono_t *pref, size_t n_num,
                                         size_t n_den, srmech_bigint_t *dn,
                                         srmech_bigint_t *g, srmech_bigint_t *t0,
                                         srmech_bigint_t *t1, int *got)
{
    size_t i;
    int has_sym = 0;
    srmech_status_t st;
    assert(c != NULL && out_cert != NULL && pref != NULL && got != NULL);
    assert(dn != NULL && g != NULL && t0 != NULL && t1 != NULL);
    *got = 0;
    if (n_num != 0u || n_den != 0u) { return SRMECH_OK; }
    for (i = 0; i < c->n_syms; i++) { if (pref->exps[i] != 0) { has_sym = 1; } }
    if (has_sym) { return SRMECH_OK; }               /* not a pure scalar */
    st = srmech_ellbase_mono_set_one(c, &out_cert->pref);
    if (st != SRMECH_OK) { return st; }
    /* dn = z_num - z_den (the (z - 1) numerator); z == 1 -> no finite cert. */
    st = srmech_bigint_sub(dn, &pref->coeff.num, &pref->coeff.den);
    if (st != SRMECH_OK) { return st; }
    if (srmech_bigint_is_zero(dn)) { return SRMECH_OK; }
    /* R = z_den / dn = z_den / (z_num - z_den), reduced (the prefactor coeff). */
    st = srmech_bigint_copy(&out_cert->pref.coeff.num, &pref->coeff.den);  /* z_den */
    if (st == SRMECH_OK) { st = srmech_bigint_copy(&out_cert->pref.coeff.den, dn); }
    if (st != SRMECH_OK) { return st; }
    st = srmech_ellbase_q_reduce(c, &out_cert->pref.coeff, g, t0, t1);
    if (st != SRMECH_OK) { return st; }
    out_cert->n_num = 0;
    out_cert->n_den = 0;
    out_cert->is_zero = 0;
    *got = 1;
    return SRMECH_OK;
}

/* Write the verified certificate EllRatio out: the prefactor coeff (out_pref_num /
 * out_pref_den) + the flat exponent rows (prefactor, num0..K-1, den0..L-1) + the counts.
 * out_exps_cap_rows guards the caller's exps buffer. */
static srmech_status_t eg_emit_cert(eg_ctx_t *c, const eg_ratio_t *cert,
                                    srmech_bigint_t *out_pref_num,
                                    srmech_bigint_t *out_pref_den,
                                    int32_t *out_exps_flat, size_t out_exps_cap_rows,
                                    size_t *out_n_num, size_t *out_n_den)
{
    size_t i;
    size_t row = 0;
    srmech_status_t st;
    assert(c != NULL && cert != NULL && out_pref_num != NULL && out_pref_den != NULL);
    assert(out_exps_flat != NULL && out_n_num != NULL && out_n_den != NULL);
    if (1u + cert->n_num + cert->n_den > out_exps_cap_rows) {
        return SRMECH_ERR_OVERFLOW;
    }
    st = srmech_bigint_copy(out_pref_num, &cert->pref.coeff.num);
    if (st == SRMECH_OK) { st = srmech_bigint_copy(out_pref_den, &cert->pref.coeff.den); }
    if (st != SRMECH_OK) { return st; }
    memcpy(out_exps_flat + row * c->n_syms, cert->pref.exps,
           c->n_syms * sizeof(int32_t));
    row++;
    for (i = 0; i < cert->n_num; i++) {
        memcpy(out_exps_flat + row * c->n_syms, cert->num[i].exps,
               c->n_syms * sizeof(int32_t));
        row++;
    }
    for (i = 0; i < cert->n_den; i++) {
        memcpy(out_exps_flat + row * c->n_syms, cert->den[i].exps,
               c->n_syms * sizeof(int32_t));
        row++;
    }
    *out_n_num = cert->n_num;
    *out_n_den = cert->n_den;
    return SRMECH_OK;
}

/* ============================================================================ *
 *  arena binders + the public entry
 * ============================================================================ */

/* Carve a freshly-bound eg_ratio_t with cap theta args in each of num / den. */
static srmech_status_t eg_bind_ratio(eg_ctx_t *c, eg_ratio_t *r, size_t cap)
{
    assert(c != NULL && r != NULL);
    assert(cap >= 1u);
    return srmech_ellbase_er_bind_ratio(c, r, cap, cap);
}

/* Carve the shared work roster (the reusable raw / canon / partition arrays + scratch). */
static srmech_status_t eg_bind_work(eg_ctx_t *c, eg_work_t *w, size_t cap_arg)
{
    srmech_status_t st;
    assert(c != NULL && w != NULL);
    assert(cap_arg >= 1u);
    w->cap_arg = cap_arg;
    st = srmech_ellbase_bind_mono_arr(c, &w->raw_num, cap_arg);
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono_arr(c, &w->raw_den, cap_arg); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono_arr(c, &w->cn, cap_arg); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono_arr(c, &w->cd, cap_arg); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono_arr(c, &w->part_num, cap_arg); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono_arr(c, &w->part_den, cap_arg); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono_arr(c, &w->part_c, cap_arg); }
    if (st == SRMECH_OK) {
        st = srmech_ellbase_bind_mono_arr(c, &w->tmp_mono, EG_LOCAL_MONOS);
    }
    if (st == SRMECH_OK) { st = srmech_ellbase_er_bind_scr(c, &w->s, cap_arg); }
    return st;
}

/* Carve the GP-normal-form factors + the residual-fold scratch. */
static srmech_status_t eg_bind_gp(eg_ctx_t *c, eg_gp_t *gp, eg_pscr_t *ps, size_t cap)
{
    srmech_status_t st;
    assert(c != NULL && gp != NULL && ps != NULL);
    assert(cap >= 1u);
    st = eg_bind_ratio(c, &gp->a, cap);
    if (st == SRMECH_OK) { st = eg_bind_ratio(c, &gp->b, cap); }
    if (st == SRMECH_OK) { st = eg_bind_ratio(c, &gp->cco, cap); }
    if (st == SRMECH_OK) { st = eg_bind_ratio(c, &ps->t1, cap); }
    if (st == SRMECH_OK) { st = eg_bind_ratio(c, &ps->t2, cap); }
    if (st == SRMECH_OK) { st = eg_bind_ratio(c, &ps->t3, cap); }
    if (st == SRMECH_OK) { st = eg_bind_ratio(c, &ps->t4, cap); }
    if (st == SRMECH_OK) { st = eg_bind_ratio(c, &ps->residual, cap); }
    if (st == SRMECH_OK) { st = eg_bind_ratio(c, &ps->tmpr, cap); }
    return st;
}

/* Carve the solve-certificate scratch (x-params + the per-endianness candidate). */
static srmech_status_t eg_bind_swork(eg_ctx_t *c, eg_swork_t *sw, size_t cap)
{
    srmech_status_t st;
    assert(c != NULL && sw != NULL);
    assert(cap >= 1u);
    st = srmech_ellbase_bind_mono(c, &sw->pa);
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono(c, &sw->pb); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono(c, &sw->pc); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono(c, &sw->sa); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono(c, &sw->sb); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono(c, &sw->sc); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono(c, &sw->ypref); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono(c, &sw->yd0); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono(c, &sw->yd1); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono(c, &sw->scratch); }
    if (st == SRMECH_OK) { st = eg_bind_ratio(c, &sw->b_shift, cap); }
    if (st == SRMECH_OK) { st = eg_bind_ratio(c, &sw->cinv, cap); }
    if (st == SRMECH_OK) { st = eg_bind_ratio(c, &sw->frame, cap); }
    if (st == SRMECH_OK) { st = eg_bind_ratio(c, &sw->yrat, cap); }
    if (st == SRMECH_OK) { st = eg_bind_ratio(c, &sw->cert, cap); }
    return st;
}

/* Carve the flat thetasum wire buffers (cnum/cden bigint arrays + exps rows + nthetas)
 * + the thetasum sub-arena. n_mono = the max monomials across the 3 cleared terms. */
static srmech_status_t eg_bind_vwork_wire(eg_ctx_t *c, eg_vwork_t *v, size_t n_mono,
                                          size_t ts_ws_words)
{
    size_t i;
    uint32_t *raw;
    srmech_status_t st = SRMECH_OK;
    assert(c != NULL && v != NULL);
    assert(n_mono >= 1u && ts_ws_words >= 1u);
    srmech_ellbase_align8(c);
    raw = srmech_ellbase_take_words(c,
            (n_mono * sizeof(srmech_bigint_t) + sizeof(uint32_t) - 1u)
            / sizeof(uint32_t));
    if (raw == NULL) { return SRMECH_ERR_OVERFLOW; }
    v->cnum = (srmech_bigint_t *)raw;
    srmech_ellbase_align8(c);
    raw = srmech_ellbase_take_words(c,
            (n_mono * sizeof(srmech_bigint_t) + sizeof(uint32_t) - 1u)
            / sizeof(uint32_t));
    if (raw == NULL) { return SRMECH_ERR_OVERFLOW; }
    v->cden = (srmech_bigint_t *)raw;
    for (i = 0; st == SRMECH_OK && i < n_mono; i++) {
        st = srmech_ellbase_bind_bi(c, &v->cnum[i]);
        if (st == SRMECH_OK) { st = srmech_ellbase_bind_bi(c, &v->cden[i]); }
    }
    if (st != SRMECH_OK) { return st; }
    raw = srmech_ellbase_take_words(c, n_mono * c->n_syms);   /* int32 == uint32 word */
    if (raw == NULL) { return SRMECH_ERR_OVERFLOW; }
    v->exps_flat = (int32_t *)raw;
    srmech_ellbase_align8(c);
    raw = srmech_ellbase_take_words(c,
            (3u * sizeof(size_t) + sizeof(uint32_t) - 1u) / sizeof(uint32_t));
    if (raw == NULL) { return SRMECH_ERR_OVERFLOW; }
    v->nthetas = (size_t *)raw;
    srmech_ellbase_align8(c);
    raw = srmech_ellbase_take_words(c, ts_ws_words);
    if (raw == NULL) { return SRMECH_ERR_OVERFLOW; }
    v->ts_ws = (void *)raw;
    v->ts_ws_len = ts_ws_words * sizeof(uint32_t);
    return SRMECH_OK;
}

/* Carve the verifier roster (the residual terms + the flat thetasum wire buffers + the
 * thetasum sub-arena). cap_theta = per-term theta capacity; n_mono = total wire monos. */
static srmech_status_t eg_bind_vwork(eg_ctx_t *c, eg_vwork_t *v, size_t cap,
                                     size_t cap_theta, size_t ts_ws_words)
{
    size_t i;
    size_t n_mono = 3u * (cap_theta + 1u);
    uint32_t *raw;
    srmech_status_t st;
    assert(c != NULL && v != NULL);
    assert(cap >= 1u && cap_theta >= 1u);
    v->cap_theta = cap_theta;
    st = eg_bind_ratio(c, &v->prod, cap);
    if (st == SRMECH_OK) { st = eg_bind_ratio(c, &v->qsh, cap); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono_arr(c, &v->common, cap_theta); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono(c, &v->coeff_pm); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_bi(c, &v->g); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_bi(c, &v->t0); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_bi(c, &v->t1); }
    for (i = 0; st == SRMECH_OK && i < 3u; i++) {
        st = srmech_ellbase_bind_mono(c, &v->term[i].pref);
        if (st == SRMECH_OK) {
            st = srmech_ellbase_bind_mono_arr(c, &v->term[i].thetas, cap_theta);
        }
        v->term[i].n = 0;
    }
    if (st == SRMECH_OK) {
        raw = srmech_ellbase_take_words(c, cap_theta);
        v->used = (raw == NULL) ? NULL : (int *)raw;
        if (raw == NULL) { st = SRMECH_ERR_OVERFLOW; }
    }
    if (st == SRMECH_OK) { st = eg_bind_vwork_wire(c, v, n_mono, ts_ws_words); }
    return st;
}

/* Parse the flat input wire (coeff_num/coeff_den bigints + int32 exps rows, in order
 * prefactor, num0..K-1, den0..L-1) into raw monomial arrays, then er_build the canonical
 * input ratio r. Uses w->raw_num / w->raw_den / w->tmp_mono[5] (the parsed prefactor). */
static srmech_status_t eg_parse_input(eg_ctx_t *c, eg_work_t *w, eg_ratio_t *r,
                                      size_t n_num, size_t n_den,
                                      const srmech_bigint_t *cnum,
                                      const srmech_bigint_t *cden,
                                      const int32_t *exps_flat, int psym)
{
    eg_mono_t pref = {0};
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
    return eg_er_build(c, w, r, &pref, w->raw_num, n_num, w->raw_den, n_den, psym);
}

/* The whole working roster, carved once. */
typedef struct eg_all {
    eg_ctx_t    ctx;
    eg_work_t   w;
    eg_ratio_t  r;          /* the canonical input term ratio              */
    eg_gp_t     gp;
    eg_pscr_t   ps;
    eg_swork_t  sw;
    eg_vwork_t  v;
    srmech_bigint_t gdn;    /* geometric-core scratch (dn / g / t0 / t1)   */
    srmech_bigint_t gg;
    srmech_bigint_t gt0;
    srmech_bigint_t gt1;
} eg_all_t;

/* The thetasum sub-arena word budget for the residual decision shape. */
static size_t eg_ts_ws_words(size_t cap_theta, size_t ns, size_t cap)
{
    size_t bytes;
    assert(cap_theta >= 1u && cap >= 1u);
    assert(ns >= 1u);
    bytes = srmech_thetasum_ws_bound(ns, 3u, cap_theta, cap);
    return bytes / sizeof(uint32_t) + 16u;
}

/* Bind the whole roster from the caller arena `ws`. */
static srmech_status_t eg_bind_all(eg_all_t *A, size_t n_num, size_t n_den, void *ws,
                                   size_t ws_len)
{
    size_t cap_arg;
    size_t cap_theta;
    size_t ts_words;
    srmech_status_t st;
    assert(A != NULL && ws != NULL);
    assert(A->ctx.n_syms >= 1u && A->ctx.cap >= 1u);
    cap_arg = n_num + n_den + 8u;
    if (cap_arg < EG_MAX_THETA) { cap_arg = EG_MAX_THETA; }
    cap_theta = 2u * cap_arg + 4u;
    ts_words = eg_ts_ws_words(cap_theta, A->ctx.n_syms, A->ctx.cap);
    st = srmech_ellbase_er_arena_init(&A->ctx, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    st = eg_bind_work(&A->ctx, &A->w, cap_arg);
    if (st == SRMECH_OK) { st = eg_bind_ratio(&A->ctx, &A->r, cap_arg); }
    if (st == SRMECH_OK) { st = eg_bind_gp(&A->ctx, &A->gp, &A->ps, cap_arg); }
    if (st == SRMECH_OK) { st = eg_bind_swork(&A->ctx, &A->sw, cap_arg); }
    if (st == SRMECH_OK) {
        st = eg_bind_vwork(&A->ctx, &A->v, cap_arg, cap_theta, ts_words);
    }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_bi(&A->ctx, &A->gdn); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_bi(&A->ctx, &A->gg); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_bi(&A->ctx, &A->gt0); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_bi(&A->ctx, &A->gt1); }
    return st;
}

/* Run the genuine pipeline on the parsed ratio: geometric core -> peel -> solve. On a
 * found certificate *out_has=1 and `cert_out` aliases the live certificate ratio. */
static srmech_status_t eg_run(eg_all_t *A, int xsym, int qsym, int psym,
                              eg_ratio_t **cert_out, int *out_has)
{
    int got = 0;
    int peeled = 0;
    int found = 0;
    srmech_status_t st;
    assert(A != NULL && cert_out != NULL && out_has != NULL);
    assert(A->r.pref.exps != NULL);
    *out_has = 0;
    *cert_out = NULL;
    /* (0) the elliptic-geometric core (a constant scalar ratio). */
    st = eg_geometric_core(&A->ctx, &A->gp.a, &A->r.pref, A->r.n_num, A->r.n_den,
                           &A->gdn, &A->gg, &A->gt0, &A->gt1, &got);
    if (st != SRMECH_OK) { return st; }
    if (got) { *cert_out = &A->gp.a; *out_has = 1; return SRMECH_OK; }
    /* (1) peel the q-shift coboundary -> GP normal form (A, B, C). */
    st = eg_peel(&A->ctx, &A->w, &A->gp, &A->ps, &A->r, xsym, qsym, psym, &peeled);
    if (st != SRMECH_OK) { return st; }
    if (!peeled) { return SRMECH_OK; }            /* not a pure-monomial residue */
    /* (2) solve the elliptic Gosper key equation (the <=8 chiral endianness sweep). */
    st = eg_solve(&A->ctx, &A->w, &A->sw, &A->v, &A->gp, &A->r, xsym, qsym, psym,
                  &found);
    if (st != SRMECH_OK) { return st; }
    if (found) { *cert_out = &A->sw.cert; *out_has = 1; }
    return SRMECH_OK;
}

/* The public entry: the GENUINE elliptic-Gosper certificate for the term ratio r (the
 * full EllRatio wire form, mirroring srmech_ellratio_is_elliptic). On a found cert
 * *out_has=1 and the certificate EllRatio is written out (prefactor coeff + exponent
 * rows + counts); else *out_has=0 (the Python re-decides on the complete pure path).
 * (The prototype lives in srmech.h, which this file includes.) */
srmech_status_t srmech_elliptic_gosper(size_t n_syms, int xsym, int psym, int qsym,
                                       size_t n_num, size_t n_den,
                                       const srmech_bigint_t *coeff_num,
                                       const srmech_bigint_t *coeff_den,
                                       const int32_t *exps_flat, uint32_t coeff_cap,
                                       int *out_has, srmech_bigint_t *out_pref_num,
                                       srmech_bigint_t *out_pref_den,
                                       int32_t *out_exps_flat, size_t out_exps_cap_rows,
                                       size_t *out_n_num, size_t *out_n_den,
                                       void *ws, size_t ws_len)
{
    eg_all_t A = {0};
    eg_ratio_t *cert = NULL;
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
    if (n_num > EG_MAX_THETA || n_den > EG_MAX_THETA) {
        return SRMECH_OK;                          /* over native scope -> decline */
    }
    A.ctx.n_syms = (n_syms == 0u) ? 1u : n_syms;
    A.ctx.cap = (coeff_cap < 8u) ? 8u : coeff_cap;
    st = eg_bind_all(&A, n_num, n_den, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    st = eg_parse_input(&A.ctx, &A.w, &A.r, n_num, n_den, coeff_num, coeff_den,
                        exps_flat, psym);
    if (st != SRMECH_OK) { return st; }
    st = eg_run(&A, xsym, qsym, psym, &cert, &has);
    if (st != SRMECH_OK) { return st; }
    if (!has) { return SRMECH_OK; }               /* decline -> Python pure path */
    st = eg_emit_cert(&A.ctx, cert, out_pref_num, out_pref_den, out_exps_flat,
                      out_exps_cap_rows, out_n_num, out_n_den);
    if (st != SRMECH_OK) { return st; }
    *out_has = 1;
    return SRMECH_OK;
}

/* The minimum `ws_len` BYTES srmech_elliptic_gosper needs for the given shape (n_syms
 * symbols, n_num + n_den input theta factors, coeff_limbs the per-coefficient
 * significant-limb estimate). Sized to the inputs -- no compiled-in cap; if RAM
 * balloons the caller mis-encoded the fiber. */
size_t srmech_elliptic_gosper_ws_bound(size_t n_syms, size_t n_num, size_t n_den,
                                       size_t coeff_cap)
{
    size_t cap = (coeff_cap < 8u) ? 8u : coeff_cap;
    size_t ns = (n_syms == 0u) ? 1u : n_syms;
    size_t cap_arg = n_num + n_den + 8u;
    size_t cap_theta;
    size_t mw;
    size_t ratios;
    size_t arrays;
    size_t wire;
    size_t ts_words;
    size_t total;
    if (cap_arg < EG_MAX_THETA) { cap_arg = EG_MAX_THETA; }
    cap_theta = 2u * cap_arg + 4u;
    mw = srmech_ellbase_er_mono_words(cap, ns);
    /* ~30 eg_ratio_t (each pref + 2*cap_arg arg monomials) across all the work structs. */
    ratios = 30u * (mw + 2u * cap_arg * mw);
    /* the reusable raw / canon / partition arrays + the scratch monomials. */
    arrays = (7u * cap_arg + EG_LOCAL_MONOS + SRMECH_ELL_ER_SCR_MONOS + 64u) * mw;
    /* the verifier flat wire: 3*(cap_theta+1) bigint pairs + exps rows + common/terms. */
    wire = 3u * (cap_theta + 1u) * (2u * cap + cap_theta * ns + 8u)
           + (4u * cap_theta + 16u) * mw;
    ts_words = eg_ts_ws_words(cap_theta, ns, (uint32_t)cap);
    total = ratios + arrays + wire + ts_words + cap * 32u + 4096u;
    assert(cap >= 8u && cap_theta >= EG_MAX_THETA);
    assert(total >= ts_words);
    return total * sizeof(uint32_t);
}

/* The per-coefficient limb cap for each srmech_bigint in the OUTPUT (the cert prefactor
 * coeff), so the reduced certificate coefficient never overflows its slot. */
size_t srmech_elliptic_gosper_out_cap(size_t coeff_limbs)
{
    size_t cl = (coeff_limbs == 0u) ? 1u : coeff_limbs;
    size_t cap = cl * 4u + 64u;
    assert(cap >= 2u);
    assert(cap >= coeff_limbs);
    return cap;
}
