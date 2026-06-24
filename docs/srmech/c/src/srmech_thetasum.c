/*
 * srmech_thetasum.c -- the C peer of the ThetaSum ADDITIVE theta-function
 * carrier (srmech.amsc.thetasum.ThetaSum), the foundation under GENUINE elliptic
 * creative telescoping. A 1:1 STRUCTURAL MIRROR of the pure-Python is_zero -- the
 * EXACT Weierstrass three-term reduction partitioned by quasi-periodicity class
 * (Rosengren, arXiv:1608.06161v3 §1.4 Eq. 1.12 + §1.3 Lemma 1.3.2). This is NOT a
 * bounded shell: the C decision reproduces the Python decision byte-for-byte,
 * including the honest "NOT-zero" verdict on a shape outside the clean +/- -pair
 * form the carrier reduces (sound, never false-accept; never a converging eval).
 *
 * The carrier (a CLEARED rational theta-function): is_zero only inspects the
 * numerator terms (the denominator is a nonzero elliptic function, so
 * self == 0 <=> numerator == 0). Each numerator term is
 *   (EllMonomial prefactor, tuple-of-Theta) ,
 * an EllMonomial = an exact-Q coefficient (num/den, Class-K sign) over a dense
 * integer exponent vector on an interned symbol table; a Theta = a single
 * EllMonomial argument. The Python carries arbitrary string symbols; the bridge
 * interns the distinct names so the C works over integer symbol-indices, and the
 * exponent monomial + sort key are byte-identical to the Python's sorted
 * (symbol, exp) tuple.
 *
 * The decision pipeline mirrors thetasum.py exactly:
 *   1. CLEAR -> numerator terms only (the bridge passes those).
 *   2. CANONICALIZE each Theta (theta_canon: quasi-periodicity + inversion, the
 *      ellbase Theta.canonicalize rewrites) and fold the prefactor.
 *   3. PARTITION by quasi-periodicity class (net_period_multiplier_exps).
 *   4. each class -> recover the +/- -pairs (recover_pairs via the monomial sqrt
 *      midpoint test), reduce by the strictly-decreasing three-term rewrite
 *      (three_term_rewrite) to a canonical normal form, combine like terms
 *      (combine_rterms); the class is == 0 IFF its normal form is empty.
 *
 * Coefficients stay tiny in practice (the +/-1 / a-over-c weights), but every
 * coefficient is an exact rational over srmech_bigint -- byte-identical at ANY
 * magnitude, OVERFLOW-not-wrap. Class-K sign is an int +/-1, never abs().
 *
 * Malloc-free (JPL Rule 3): every working monomial, theta, term, rterm + the
 * bigint scratch is carved from the caller arena `ws`. If the working set
 * balloons, the caller has mis-encoded the fiber -- the arena is sized to the
 * input (n_terms, n_thetas, n_syms), no compiled-in cap.
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto/recursion): OK -- iterative, flat static helpers
 *   - Rule 2 (bounded loops)    : OK -- TS_REDUCE_MAX_PASSES bound (mirrors py)
 *   - Rule 3 (no malloc)        : OK -- caller arena only
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

/* The exact-Q monomial + theta-canon KERNELS this decision rides on were PROMOTED
 * to srmech_ellbase.c (rc64) so ThetaSum.is_zero and EllRatio.is_elliptic share ONE
 * copy of each (the everything-mirrors discipline forbids two copies of the same
 * algebra). The arena context / monomial / exact-Q carriers + their algebra are the
 * shared srmech_ell_* types + srmech_ellbase_* functions; the thin aliases below keep
 * this file's call sites (`ts_*`) unchanged while pointing at the single shared copy.
 * What stays HERE is the thetasum-SPECIFIC algebra: the +/- -pair / rterm storage, the
 * recover_pairs / canon_pair / three-term rewrite, and the is_zero orchestration. */

/* The Weierstrass-reduction pass bound (mirrors thetasum._REDUCE_MAX_PASSES): the
 * non-reference s-pair midpoint multiset strictly decreases each pass, so a small
 * cap suffices; an over-cap term is left un-reduced and the class honestly reports
 * NOT-zero rather than looping (the Python parity). */
#define TS_REDUCE_MAX_PASSES 64u

/* ---- shared-kernel aliases (the single copy lives in srmech_ellbase.c) ------- */
typedef srmech_ell_q_t    ts_q_t;
typedef srmech_ell_mono_t ts_mono_t;
typedef srmech_ell_ctx_t  ts_ctx_t;

#define ts_take_words        srmech_ellbase_take_words
#define ts_align8            srmech_ellbase_align8
#define ts_take_exps         srmech_ellbase_take_exps
#define ts_bind_bi           srmech_ellbase_bind_bi
#define ts_bind_q            srmech_ellbase_bind_q
#define ts_bind_mono         srmech_ellbase_bind_mono
#define ts_bind_mono_arr     srmech_ellbase_bind_mono_arr
#define ts_q_reduce          srmech_ellbase_q_reduce
#define ts_q_mul             srmech_ellbase_q_mul
#define ts_q_add             srmech_ellbase_q_add
#define ts_q_copy            srmech_ellbase_q_copy
#define ts_q_eq              srmech_ellbase_q_eq
#define ts_mono_is_zero      srmech_ellbase_mono_is_zero
#define ts_mono_set_one      srmech_ellbase_mono_set_one
#define ts_mono_copy         srmech_ellbase_mono_copy
#define ts_mono_mul          srmech_ellbase_mono_mul
#define ts_mono_inv          srmech_ellbase_mono_inv
#define ts_mono_div          srmech_ellbase_mono_div
#define ts_exps_cmp          srmech_ellbase_exps_cmp
#define ts_mono_cmp          srmech_ellbase_mono_cmp
#define ts_mono_eq           srmech_ellbase_mono_eq
#define ts_mono_sqrt         srmech_ellbase_mono_sqrt
#define ts_theta_canon_arg   srmech_ellbase_theta_canon_arg

/* A canonical +/- -pair (alpha, beta): theta(alpha*beta^pm). */
typedef struct ts_pair {
    ts_mono_t alpha;
    ts_mono_t beta;
} ts_pair_t;

/* The arena bump primitives + per-bigint / per-monomial binds are the SHARED kernels
 * (srmech_ellbase_take_words / align8 / take_exps / bind_bi / bind_q / bind_mono,
 * aliased above). Only the thetasum-SPECIFIC pair bind stays here. */

static srmech_status_t ts_bind_pair(ts_ctx_t *c, ts_pair_t *pr)
{
    srmech_status_t st;
    assert(c != NULL && pr != NULL);
    assert(c->cap > 0u);
    st = ts_bind_mono(c, &pr->alpha);
    if (st != SRMECH_OK) { return st; }
    return ts_bind_mono(c, &pr->beta);
}


/* The quasi-periodicity-class KEY of a theta-product: the net multiplier monomial
 * EXPONENT vector the product acquires under x->p*x AND y->p*y
 * (thetasum._net_period_multiplier_exps). For each sym in (x, y) and each theta arg
 * t: shifted = t * p^{exp_of(sym)}; canonicalize Theta(shifted); multiply its
 * prefactor into the net. The Python classifies by the prefactor's EXPONENT monomial
 * (coeff-blind). We reproduce the prefactor EXPONENT contribution exactly.
 *
 * Python prefactor of theta(p^k z0):  (-1)^k p^{-k(k-1)/2} z0^{-k}  then (orientation)
 * an extra * (-1) * z0  when z0._sort_key() > z0inv._sort_key().  We accumulate the
 * EXPONENT vector of that prefactor into `net_exps` (coeff sign is independence-blind
 * and the Python key drops it). */
static srmech_status_t ts_pref_exps_of_shift(ts_ctx_t *c, const ts_mono_t *targ,
                                             int sym, int psym, int32_t *net_exps,
                                             ts_mono_t *sh, ts_mono_t *z0,
                                             ts_mono_t *z0inv, ts_mono_t *tmp);

static srmech_status_t ts_net_period_key(ts_ctx_t *c, const ts_mono_t *thetas,
                                         size_t n_thetas, int xsym, int ysym,
                                         int psym, int32_t *net_exps,
                                         ts_mono_t *sh, ts_mono_t *z0,
                                         ts_mono_t *z0inv, ts_mono_t *tmp)
{
    size_t ti;
    int which;
    int syms2[2];
    srmech_status_t st;
    assert(c != NULL && net_exps != NULL);
    assert(thetas != NULL || n_thetas == 0u);
    memset(net_exps, 0, c->n_syms * sizeof(int32_t));
    syms2[0] = xsym;
    syms2[1] = ysym;
    for (which = 0; which < 2; which++) {
        int sym = syms2[which];
        if (sym < 0) { continue; }
        for (ti = 0; ti < n_thetas; ti++) {
            st = ts_pref_exps_of_shift(c, &thetas[ti], sym, psym, net_exps,
                                       sh, z0, z0inv, tmp);
            if (st != SRMECH_OK) { return st; }
        }
    }
    return SRMECH_OK;
}

/* Accumulate the prefactor EXPONENT vector of canonicalize(theta(targ * p^{e_sym}))
 * into net_exps (one theta, one period direction). Mirrors the inner body of
 * thetasum._net_period_multiplier_exps. A shifted_arg that is the zero monomial is
 * skipped (it never is here -- monomials are nonzero). */
static srmech_status_t ts_pref_exps_of_shift(ts_ctx_t *c, const ts_mono_t *targ,
                                             int sym, int psym, int32_t *net_exps,
                                             ts_mono_t *sh, ts_mono_t *z0,
                                             ts_mono_t *z0inv, ts_mono_t *tmp)
{
    int32_t k;
    int32_t esym;
    int32_t i;
    int cmp;
    srmech_status_t st;
    assert(c != NULL && targ != NULL && net_exps != NULL && sh != NULL);
    assert(z0 != NULL && z0inv != NULL && tmp != NULL);
    (void)tmp;
    /* sh = targ * p^{targ.exp_of(sym)} */
    st = ts_mono_copy(c, sh, targ);
    if (st != SRMECH_OK) { return st; }
    esym = (sym >= 0) ? targ->exps[sym] : 0;
    if (psym >= 0) { sh->exps[psym] += esym; }
    /* z0 = sh with p-exp 0; k = sh.exp_of(p) */
    st = ts_mono_copy(c, z0, sh);
    if (st != SRMECH_OK) { return st; }
    k = (psym >= 0) ? sh->exps[psym] : 0;
    if (psym >= 0) { z0->exps[psym] = 0; }
    /* prefactor exps so far: p^{-k(k-1)/2} * z0^{-k}  (the (-1)^k sign is dropped). */
    if (psym >= 0) {
        net_exps[psym] += -(int32_t)((k * (k - 1)) / 2);
    }
    for (i = 0; i < (int32_t)c->n_syms; i++) {
        net_exps[i] += -k * z0->exps[i];
    }
    /* orientation flip prefactor: extra * (-1) * z0 when z0 > z0inv (sort-key). */
    st = ts_mono_inv(c, z0inv, z0);
    if (st != SRMECH_OK) { return st; }
    if (ts_mono_eq(c, z0, z0inv)) {
        return SRMECH_OK;
    }
    cmp = ts_mono_cmp(c, z0, z0inv);
    if (cmp > 0) {
        for (i = 0; i < (int32_t)c->n_syms; i++) {
            net_exps[i] += z0->exps[i];
        }
    }
    return SRMECH_OK;
}

/* ts_mono_sqrt (the +/- -pair midpoint perfect-square test) is the SHARED
 * srmech_ellbase_mono_sqrt (aliased above). */

/* canon_half: fix the half `beta` orientation (FREE): positive leading summation
 * exponent (x then y), else the lex-smaller of {beta, 1/beta}. `alpha` (midpoint)
 * is untouched. Writes the chosen half into `out_beta`. Mirrors _canon_half. */
static srmech_status_t ts_canon_half(ts_ctx_t *c, ts_mono_t *out_beta,
                                     const ts_mono_t *beta, int xsym, int ysym,
                                     ts_mono_t *binv)
{
    int syms2[2];
    int which;
    int cmp;
    srmech_status_t st;
    assert(c != NULL && out_beta != NULL && beta != NULL && binv != NULL);
    assert(!ts_mono_is_zero(beta));
    st = ts_mono_inv(c, binv, beta);
    if (st != SRMECH_OK) { return st; }
    syms2[0] = xsym;
    syms2[1] = ysym;
    for (which = 0; which < 2; which++) {
        int s = syms2[which];
        int32_t eb = (s >= 0) ? beta->exps[s] : 0;
        if (eb != 0) {
            return ts_mono_copy(c, out_beta, (eb > 0) ? beta : binv);
        }
    }
    cmp = ts_mono_cmp(c, beta, binv);
    return ts_mono_copy(c, out_beta, (cmp <= 0) ? beta : binv);
}

/* canon_pair: canonicalize an arbitrary +/- pair theta(u*v^pm) to a totally-fixed
 * (alpha, beta), folding the EXACT inversion prefactor each reorientation costs
 * (Mirrors _canon_pair). The two candidate reps:
 *   rep A: midpoint u, half v  -> prefactor 1
 *   rep B: midpoint v, half u  -> prefactor -(u/v)
 * canon_half each, then pick the lex-smaller (alpha, beta) and emit its prefactor.
 * Writes out_pref (monomial), out_alpha, out_beta. Uses caller scratch monomials. */
static srmech_status_t ts_canon_pair(ts_ctx_t *c, const ts_mono_t *u,
                                     const ts_mono_t *v, int xsym, int ysym,
                                     ts_mono_t *out_pref, ts_mono_t *out_alpha,
                                     ts_mono_t *out_beta, ts_mono_t *scr,
                                     srmech_bigint_t *g, srmech_bigint_t *t0,
                                     srmech_bigint_t *t1)
{
    /* scr is an array of 7 scratch monomials: bA, bB, uv, neg, binvA, binvB, prefB */
    ts_mono_t *bA = &scr[0];
    ts_mono_t *bB = &scr[1];
    ts_mono_t *uv = &scr[2];
    ts_mono_t *neg = &scr[3];
    ts_mono_t *binv = &scr[4];
    ts_mono_t *prefB = &scr[5];
    int cmpa;
    int cmpb;
    srmech_status_t st;
    assert(c != NULL && u != NULL && v != NULL && out_pref != NULL);
    assert(out_alpha != NULL && out_beta != NULL && scr != NULL);
    /* rep A: half = canon_half(v); alpha_A = u. */
    st = ts_canon_half(c, bA, v, xsym, ysym, binv);
    if (st != SRMECH_OK) { return st; }
    /* rep B: half = canon_half(u); alpha_B = v; prefB = -(u/v). */
    st = ts_canon_half(c, bB, u, xsym, ysym, binv);
    if (st != SRMECH_OK) { return st; }
    st = ts_mono_div(c, uv, u, v, scr + 6, g, t0, t1);
    if (st != SRMECH_OK) { return st; }
    st = ts_mono_set_one(c, neg);
    if (st != SRMECH_OK) { return st; }
    neg->coeff.num.sign = -neg->coeff.num.sign;        /* neg = -1 */
    st = ts_mono_mul(c, prefB, neg, uv, g, t0, t1);    /* prefB = -(u/v) */
    if (st != SRMECH_OK) { return st; }
    /* pick the lex-smaller (alpha, beta): A = (u, bA), B = (v, bB). */
    cmpa = ts_mono_cmp(c, u, v);             /* alpha A vs alpha B */
    if (cmpa < 0) {
        cmpb = -1;
    } else if (cmpa > 0) {
        cmpb = 1;
    } else {
        cmpb = ts_mono_cmp(c, bA, bB);        /* tie on alpha -> compare beta */
    }
    if (cmpb <= 0) {
        st = ts_mono_copy(c, out_alpha, u);
        if (st == SRMECH_OK) { st = ts_mono_copy(c, out_beta, bA); }
        if (st == SRMECH_OK) { st = ts_mono_set_one(c, out_pref); }
        return st;
    }
    st = ts_mono_copy(c, out_alpha, v);
    if (st == SRMECH_OK) { st = ts_mono_copy(c, out_beta, bB); }
    if (st == SRMECH_OK) { st = ts_mono_copy(c, out_pref, prefB); }
    return st;
}

/* ---- reduced-term (rterm) storage ------------------------------------------- *
 *
 * A reduced term = (prefactor monomial, array of canonical +/- -pairs). The whole
 * reduction works over a fixed-capacity arena array of rterms; each rewrite splits
 * one rterm into two, bounded by TS_REDUCE_MAX_PASSES passes. */
typedef struct ts_rterm {
    ts_mono_t  pref;
    ts_pair_t *pairs;     /* arena array, length n_pairs                       */
    size_t     n_pairs;
    int        live;      /* 0 once combined away (coeff cancelled / consumed) */
} ts_rterm_t;

static srmech_status_t ts_bind_rterm(ts_ctx_t *c, ts_rterm_t *rt,
                                     size_t max_pairs)
{
    size_t i;
    size_t words;
    uint32_t *raw;
    srmech_status_t st;
    assert(c != NULL && rt != NULL);
    assert(max_pairs >= 1u);
    st = ts_bind_mono(c, &rt->pref);
    if (st != SRMECH_OK) { return st; }
    /* The pair array is a plain ts_pair_t[]; carve its struct storage from the
     * arena as raw words (8-byte aligned -- it embeds pointers), then bind each
     * pair's bigints. */
    ts_align8(c);
    words = (max_pairs * sizeof(ts_pair_t) + sizeof(uint32_t) - 1u)
            / sizeof(uint32_t);
    raw = ts_take_words(c, words);
    if (raw == NULL) { return SRMECH_ERR_OVERFLOW; }
    rt->pairs = (ts_pair_t *)raw;
    for (i = 0; i < max_pairs; i++) {
        st = ts_bind_pair(c, &rt->pairs[i]);
        if (st != SRMECH_OK) { return st; }
    }
    rt->n_pairs = 0;
    rt->live = 1;
    return SRMECH_OK;
}

/* Order-INDEPENDENT pair-MULTISET equality for two rterms (the _rterm_key: Python
 * SORTS the (alpha_key, beta_key) tuples before comparing, so two rterms are LIKE iff
 * their pair multisets match regardless of the live emission order). Returns 0 iff the
 * multisets are equal, +1 otherwise. `used` is a scratch flag array (>= nb). The pairs
 * are NOT sorted in place -- the rewrite scan needs Python's live order preserved. */
static int ts_pairs_cmp(const ts_ctx_t *c, const ts_pair_t *pa, size_t na,
                        const ts_pair_t *pb, size_t nb, int *used)
{
    size_t i;
    size_t j;
    assert(c != NULL && used != NULL);
    assert((pa != NULL || na == 0u) && (pb != NULL || nb == 0u));
    if (na != nb) { return 1; }
    for (j = 0; j < nb; j++) { used[j] = 0; }
    for (i = 0; i < na; i++) {
        int found = 0;
        for (j = 0; j < nb; j++) {
            if (used[j]) { continue; }
            if (ts_mono_cmp(c, &pa[i].alpha, &pb[j].alpha) == 0
                && ts_mono_cmp(c, &pa[i].beta, &pb[j].beta) == 0) {
                used[j] = 1;
                found = 1;
                break;
            }
        }
        if (!found) { return 1; }
    }
    return 0;
}

/* A bundle of reusable scratch monomials + bigints for the pair / rewrite algebra,
 * carved once. `pm` is an array of >= TS_SCR_MONOS monomials; g/t0/t1 bigints. */
#define TS_SCR_MONOS 16u
#define TS_REWRITE_MONOS 6u
#define TS_REWRITE_PAIRS 4u
typedef struct ts_scr {
    ts_mono_t  *pm;        /* TS_SCR_MONOS canon_pair / general scratch monos */
    ts_mono_t  *cm;        /* TS_REWRITE_MONOS rewrite coeff scratch monos    */
    ts_mono_t  *ca;        /* max_thetas canonical-arg scratch monos          */
    ts_pair_t  *rp;        /* TS_REWRITE_PAIRS rewrite output pairs           */
    int        *used_pairs;/* >= max_pairs flags for the multiset compare    */
    srmech_bigint_t g;
    srmech_bigint_t t0;
    srmech_bigint_t t1;
    int         psym;      /* the interned p index (-1 if absent)            */
} ts_scr_t;

/* ts_bind_mono_arr is the SHARED srmech_ellbase_bind_mono_arr (aliased above). */

/* Carve a contiguous bound pair array of `count` pairs (8-byte aligned). */
static srmech_status_t ts_bind_pair_arr(ts_ctx_t *c, ts_pair_t **out, size_t count)
{
    size_t i;
    size_t words;
    uint32_t *raw;
    srmech_status_t st;
    assert(c != NULL && out != NULL && count >= 1u);
    assert(c->cap > 0u);
    ts_align8(c);
    words = (count * sizeof(ts_pair_t) + sizeof(uint32_t) - 1u) / sizeof(uint32_t);
    raw = ts_take_words(c, words);
    if (raw == NULL) { return SRMECH_ERR_OVERFLOW; }
    *out = (ts_pair_t *)raw;
    for (i = 0; i < count; i++) {
        st = ts_bind_pair(c, &(*out)[i]);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

static srmech_status_t ts_bind_scr(ts_ctx_t *c, ts_scr_t *s, size_t max_thetas)
{
    size_t max_pairs = (max_thetas / 2u) + 1u;
    uint32_t *raw;
    srmech_status_t st;
    assert(c != NULL && s != NULL);
    assert(c->cap > 0u);
    st = ts_bind_mono_arr(c, &s->pm, TS_SCR_MONOS);
    if (st == SRMECH_OK) { st = ts_bind_mono_arr(c, &s->cm, TS_REWRITE_MONOS); }
    if (st == SRMECH_OK) {
        st = ts_bind_mono_arr(c, &s->ca, (max_thetas == 0u) ? 1u : max_thetas);
    }
    if (st == SRMECH_OK) { st = ts_bind_pair_arr(c, &s->rp, TS_REWRITE_PAIRS); }
    if (st != SRMECH_OK) { return st; }
    raw = ts_take_words(c, max_pairs);
    if (raw == NULL) { return SRMECH_ERR_OVERFLOW; }
    s->used_pairs = (int *)raw;
    st = ts_bind_bi(c, &s->g);
    if (st == SRMECH_OK) { st = ts_bind_bi(c, &s->t0); }
    if (st == SRMECH_OK) { st = ts_bind_bi(c, &s->t1); }
    s->psym = -1;
    return st;
}

/* Try to recover a +/- -pair from canonical thetas ca[i], ca[j]: alpha = sqrt(zi*zj),
 * beta = sqrt(zi/zj); if BOTH are perfect-square monomials, canon_pair them, fold the
 * inversion prefactor into rt->pref, append the (alpha, beta) pair to rt, and set
 * *got = 1. Otherwise *got = 0 (not a pair). Mirrors the inner _recover_pairs body. */
static srmech_status_t ts_try_pair(ts_ctx_t *c, ts_rterm_t *rt,
                                   const ts_mono_t *zi, const ts_mono_t *zj,
                                   int xsym, int ysym, int *got, ts_scr_t *s)
{
    int sq_ok;
    srmech_status_t st;
    assert(c != NULL && rt != NULL && zi != NULL && zj != NULL);
    assert(got != NULL && s != NULL);
    *got = 0;
    st = ts_mono_mul(c, &s->pm[0], zi, zj, &s->g, &s->t0, &s->t1);
    if (st != SRMECH_OK) { return st; }
    st = ts_mono_sqrt(c, &s->pm[1], &s->pm[0], &sq_ok, &s->t0, &s->t1);
    if (st != SRMECH_OK || !sq_ok) { return st; }
    st = ts_mono_div(c, &s->pm[2], zi, zj, &s->pm[3], &s->g, &s->t0, &s->t1);
    if (st != SRMECH_OK) { return st; }
    st = ts_mono_sqrt(c, &s->pm[4], &s->pm[2], &sq_ok, &s->t0, &s->t1);
    if (st != SRMECH_OK || !sq_ok) { return st; }
    /* canon_pair(alpha=pm[1], beta=pm[4]) -> pref pm[5], (pm[6], pm[7]) */
    st = ts_canon_pair(c, &s->pm[1], &s->pm[4], xsym, ysym, &s->pm[5],
                       &s->pm[6], &s->pm[7], &s->pm[8], &s->g, &s->t0, &s->t1);
    if (st != SRMECH_OK) { return st; }
    st = ts_mono_mul(c, &s->pm[9], &rt->pref, &s->pm[5], &s->g, &s->t0, &s->t1);
    if (st != SRMECH_OK) { return st; }
    st = ts_mono_copy(c, &rt->pref, &s->pm[9]);
    if (st != SRMECH_OK) { return st; }
    st = ts_mono_copy(c, &rt->pairs[rt->n_pairs].alpha, &s->pm[6]);
    if (st == SRMECH_OK) {
        st = ts_mono_copy(c, &rt->pairs[rt->n_pairs].beta, &s->pm[7]);
    }
    if (st != SRMECH_OK) { return st; }
    rt->n_pairs++;
    *got = 1;
    return SRMECH_OK;
}

/* recover_pairs: write the +/- -pair decomposition of a canonical theta-product
 * (the term's `n_thetas` canonical theta ARGUMENT monomials in `targs`) into `rt`
 * (its pref pre-set to the term prefactor; this folds each inversion prefactor in).
 * Sets *ok = 0 when the product is NOT a clean product of +/- -pairs (odd count, no
 * consistent pairing) -> the class is honestly NOT-zero. Mirrors _recover_pairs. */
static srmech_status_t ts_recover_pairs(ts_ctx_t *c, ts_rterm_t *rt,
                                        const ts_mono_t *targs, size_t n_thetas,
                                        int xsym, int ysym, int *ok,
                                        ts_scr_t *s, int *used)
{
    size_t i;
    size_t j;
    srmech_status_t st;
    assert(c != NULL && rt != NULL && ok != NULL && s != NULL && used != NULL);
    assert(targs != NULL || n_thetas == 0u);
    *ok = 0;
    if ((n_thetas & 1u) != 0u) { return SRMECH_OK; }
    /* canonicalize each input theta ARGUMENT (idempotent on canonical input, but a
     * faithful mirror of _recover_pairs which re-canonicalizes each factor). */
    for (i = 0; i < n_thetas; i++) {
        st = ts_theta_canon_arg(c, &s->ca[i], &targs[i], s->psym, &s->pm[15]);
        if (st != SRMECH_OK) { return st; }
    }
    for (i = 0; i < n_thetas; i++) { used[i] = 0; }
    rt->n_pairs = 0;
    for (i = 0; i < n_thetas; i++) {
        int matched = 0;
        if (used[i]) { continue; }
        for (j = i + 1; j < n_thetas; j++) {
            if (used[j]) { continue; }
            st = ts_try_pair(c, rt, &s->ca[i], &s->ca[j], xsym, ysym, &matched, s);
            if (st != SRMECH_OK) { return st; }
            if (matched) { used[i] = used[j] = 1; break; }
        }
        if (!matched) { return SRMECH_OK; }    /* no consistent pairing -> not-zero */
    }
    *ok = 1;
    /* NOTE: the pairs are LEFT in recovery / emission order (NOT sorted) -- the
     * Python three-term rewrite scans pairs in their stored order to pick the s-pair
     * (largest midpoint, first-of-ties) + the FIRST qualifying constant partner, so
     * the C scan must see the SAME order. The combine key (ts_pairs_cmp) is
     * order-independent (a multiset compare), matching Python's sorted _rterm_key. */
    return SRMECH_OK;
}

/* Two rterms are LIKE iff same pair-multiset AND same prefactor EXPONENT monomial
 * (coeff aside) -- the _combine_rterms key. Returns 1 iff like. `used` is a scratch
 * flag array (>= b->n_pairs) for the order-independent multiset compare. */
static int ts_rterm_like(const ts_ctx_t *c, const ts_rterm_t *a,
                         const ts_rterm_t *b, int *used)
{
    assert(c != NULL && a != NULL && b != NULL);
    assert(a->pref.exps != NULL && b->pref.exps != NULL);
    if (ts_exps_cmp(c, a->pref.exps, b->pref.exps) != 0) { return 0; }
    return ts_pairs_cmp(c, a->pairs, a->n_pairs, b->pairs, b->n_pairs, used) == 0;
}

/* combine_rterms in place over `rts[0..n)`: add the Q coeffs of LIKE rterms into the
 * first occurrence, mark duplicates dead, then drop coeff-zero rterms (live = 0).
 * Mirrors _combine_rterms (separating the Q scalar from the symbol monomial: like
 * rterms share the same pref EXPONENT monomial, and their coeffs add). */
static srmech_status_t ts_combine_rterms(ts_ctx_t *c, ts_rterm_t *rts, size_t n,
                                         ts_scr_t *s)
{
    size_t i;
    size_t j;
    srmech_status_t st;
    assert(c != NULL && rts != NULL && s != NULL);
    assert(s->pm != NULL);
    for (i = 0; i < n; i++) {
        if (!rts[i].live) { continue; }
        for (j = i + 1; j < n; j++) {
            if (!rts[j].live) { continue; }
            if (!ts_rterm_like(c, &rts[i], &rts[j], s->used_pairs)) { continue; }
            /* same key: add the Q coeffs (both prefs share the exp monomial). */
            st = ts_q_add(c, &s->pm[0].coeff, &rts[i].pref.coeff,
                          &rts[j].pref.coeff, &s->g, &s->t0, &s->t1);
            if (st != SRMECH_OK) { return st; }
            st = ts_q_copy(&rts[i].pref.coeff, &s->pm[0].coeff);
            if (st != SRMECH_OK) { return st; }
            rts[j].live = 0;
        }
    }
    for (i = 0; i < n; i++) {
        if (rts[i].live && srmech_bigint_is_zero(&rts[i].pref.coeff.num)) {
            rts[i].live = 0;
        }
    }
    return SRMECH_OK;
}

/* Copy one rterm (pref + the n_pairs pairs) into dst. dst pre-bound with >= n_pairs
 * pair capacity. */
static srmech_status_t ts_rterm_copy(ts_ctx_t *c, ts_rterm_t *dst,
                                     const ts_rterm_t *src)
{
    size_t i;
    srmech_status_t st;
    assert(c != NULL && dst != NULL && src != NULL);
    assert(dst != src);
    st = ts_mono_copy(c, &dst->pref, &src->pref);
    if (st != SRMECH_OK) { return st; }
    for (i = 0; i < src->n_pairs; i++) {
        st = ts_mono_copy(c, &dst->pairs[i].alpha, &src->pairs[i].alpha);
        if (st == SRMECH_OK) {
            st = ts_mono_copy(c, &dst->pairs[i].beta, &src->pairs[i].beta);
        }
        if (st != SRMECH_OK) { return st; }
    }
    dst->n_pairs = src->n_pairs;
    dst->live = 1;
    return SRMECH_OK;
}

/* Build one output rterm of a three-term split: pref' = pref * coeff, pairs =
 * rest (all pairs of `src` except s_idx + partner_idx) + the two new canon pairs
 * (newA, newB). `rest` is taken from src by skipping the two indices. */
static srmech_status_t ts_emit_split_term(ts_ctx_t *c, ts_rterm_t *dst,
                                          const ts_rterm_t *src, size_t s_idx,
                                          size_t partner_idx,
                                          const ts_mono_t *coeff,
                                          const ts_pair_t *newA,
                                          const ts_pair_t *newB, ts_scr_t *s)
{
    size_t i;
    size_t np = 0;
    srmech_status_t st;
    assert(c != NULL && dst != NULL && src != NULL && s != NULL);
    assert(dst != src && coeff != NULL && newA != NULL && newB != NULL);
    /* pref' = src.pref * coeff */
    st = ts_mono_mul(c, &dst->pref, &src->pref, coeff, &s->g, &s->t0, &s->t1);
    if (st != SRMECH_OK) { return st; }
    /* rest pairs */
    for (i = 0; i < src->n_pairs; i++) {
        if (i == s_idx || i == partner_idx) { continue; }
        st = ts_mono_copy(c, &dst->pairs[np].alpha, &src->pairs[i].alpha);
        if (st == SRMECH_OK) {
            st = ts_mono_copy(c, &dst->pairs[np].beta, &src->pairs[i].beta);
        }
        if (st != SRMECH_OK) { return st; }
        np++;
    }
    st = ts_mono_copy(c, &dst->pairs[np].alpha, &newA->alpha);
    if (st == SRMECH_OK) { st = ts_mono_copy(c, &dst->pairs[np].beta, &newA->beta); }
    if (st != SRMECH_OK) { return st; }
    np++;
    st = ts_mono_copy(c, &dst->pairs[np].alpha, &newB->alpha);
    if (st == SRMECH_OK) { st = ts_mono_copy(c, &dst->pairs[np].beta, &newB->beta); }
    if (st != SRMECH_OK) { return st; }
    np++;
    dst->n_pairs = np;
    dst->live = 1;
    /* pairs left in emission order (rest + newA + newB) -- matches Python's
     * termA = rest + [pairA1, pairA2]; the combine key is order-independent. */
    return SRMECH_OK;
}

/* Locate the rewrite operands in `src`: the s-pair (HALF carries `sym`) with the
 * LARGEST midpoint, and a partner CONSTANT pair (both halves sym-free) whose BOTH
 * midpoints' sort-keys are strictly < the s-pair midpoint. Sets *s_idx / *p_idx, or
 * leaves them SIZE_MAX when no such rewrite applies. Mirrors the index scan in
 * _three_term_rewrite. */
static void ts_find_rewrite(const ts_ctx_t *c, const ts_rterm_t *src, int sym,
                            size_t *s_idx, size_t *p_idx)
{
    size_t idx;
    size_t best = (size_t)-1;
    assert(c != NULL && src != NULL && s_idx != NULL && p_idx != NULL);
    assert(sym >= 0 && (size_t)sym < c->n_syms);
    *s_idx = (size_t)-1;
    *p_idx = (size_t)-1;
    for (idx = 0; idx < src->n_pairs; idx++) {
        if (src->pairs[idx].beta.exps[sym] == 0) { continue; }
        if (best == (size_t)-1
            || ts_mono_cmp(c, &src->pairs[idx].alpha,
                           &src->pairs[best].alpha) > 0) {
            best = idx;
        }
    }
    if (best == (size_t)-1) { return; }
    *s_idx = best;
    for (idx = 0; idx < src->n_pairs; idx++) {
        if (idx == best) { continue; }
        if (src->pairs[idx].alpha.exps[sym] != 0
            || src->pairs[idx].beta.exps[sym] != 0) { continue; }
        if (ts_mono_cmp(c, &src->pairs[idx].alpha, &src->pairs[best].alpha) < 0
            && ts_mono_cmp(c, &src->pairs[idx].beta,
                           &src->pairs[best].alpha) < 0) {
            *p_idx = idx;
            return;
        }
    }
    *s_idx = (size_t)-1;     /* found an s-pair but no partner -> no rewrite */
}

/* Build termA + termB of a three-term rewrite (the operands at s_idx / p_idx).
 * `rp` is an array of 4 bound scratch pairs (pA1, pA2, pB1, pB2); `cm` an array of
 * >= 6 scratch monomials for the coefficient products. Mirrors _three_term_rewrite
 * exactly (orientations load-bearing):
 *   termA: canon_pair(pa, svar) + canon_pair(a_mid, pb),  coeff cA1*cA2
 *   termB: canon_pair(pb, svar) + canon_pair(pa, a_mid),  coeff (a_mid/pb)*cB1*cB2 */
static srmech_status_t ts_build_rewrite(ts_ctx_t *c, const ts_rterm_t *src,
                                        size_t s_idx, size_t p_idx, ts_rterm_t *outA,
                                        ts_rterm_t *outB, ts_pair_t *rp,
                                        ts_mono_t *cm, int xsym, int ysym,
                                        ts_scr_t *s)
{
    const ts_mono_t *a_mid = &src->pairs[s_idx].alpha;
    const ts_mono_t *svar = &src->pairs[s_idx].beta;
    const ts_mono_t *pa = &src->pairs[p_idx].alpha;
    const ts_mono_t *pb = &src->pairs[p_idx].beta;
    srmech_status_t st;
    assert(c != NULL && src != NULL && rp != NULL && cm != NULL && s != NULL);
    assert(outA != NULL && outB != NULL);
    /* termA pairs + coeff cA1*cA2. */
    st = ts_canon_pair(c, pa, svar, xsym, ysym, &cm[0], &rp[0].alpha,
                       &rp[0].beta, s->pm, &s->g, &s->t0, &s->t1);
    if (st != SRMECH_OK) { return st; }
    st = ts_canon_pair(c, a_mid, pb, xsym, ysym, &cm[1], &rp[1].alpha,
                       &rp[1].beta, s->pm, &s->g, &s->t0, &s->t1);
    if (st != SRMECH_OK) { return st; }
    st = ts_mono_mul(c, &cm[2], &cm[0], &cm[1], &s->g, &s->t0, &s->t1);
    if (st != SRMECH_OK) { return st; }
    st = ts_emit_split_term(c, outA, src, s_idx, p_idx, &cm[2],
                            &rp[0], &rp[1], s);
    if (st != SRMECH_OK) { return st; }
    /* termB pairs + coeff (a_mid/pb)*cB1*cB2. */
    st = ts_canon_pair(c, pb, svar, xsym, ysym, &cm[3], &rp[2].alpha,
                       &rp[2].beta, s->pm, &s->g, &s->t0, &s->t1);
    if (st != SRMECH_OK) { return st; }
    st = ts_canon_pair(c, pa, a_mid, xsym, ysym, &cm[4], &rp[3].alpha,
                       &rp[3].beta, s->pm, &s->g, &s->t0, &s->t1);
    if (st != SRMECH_OK) { return st; }
    st = ts_mono_div(c, &cm[5], a_mid, pb, &cm[0], &s->g, &s->t0, &s->t1);
    if (st != SRMECH_OK) { return st; }
    st = ts_mono_mul(c, &cm[0], &cm[5], &cm[3], &s->g, &s->t0, &s->t1);
    if (st != SRMECH_OK) { return st; }
    st = ts_mono_mul(c, &cm[1], &cm[0], &cm[4], &s->g, &s->t0, &s->t1);
    if (st != SRMECH_OK) { return st; }
    return ts_emit_split_term(c, outB, src, s_idx, p_idx, &cm[1],
                              &rp[2], &rp[3], s);
}

/* The double-buffered rterm work arrays + counts for a class reduction. */
typedef struct ts_work {
    ts_rterm_t *cur;       /* current live rterms                            */
    size_t      n_cur;
    ts_rterm_t *nxt;       /* the rewrite output buffer                      */
    size_t      n_nxt;
    size_t      cap;       /* per-buffer rterm slot capacity                 */
} ts_work_t;

static srmech_status_t ts_bind_rterm_arr(ts_ctx_t *c, ts_rterm_t **out,
                                         size_t count, size_t max_pairs)
{
    size_t i;
    size_t words;
    uint32_t *raw;
    srmech_status_t st;
    assert(c != NULL && out != NULL && count >= 1u);
    assert(max_pairs >= 1u);
    ts_align8(c);
    words = (count * sizeof(ts_rterm_t) + sizeof(uint32_t) - 1u) / sizeof(uint32_t);
    raw = ts_take_words(c, words);
    if (raw == NULL) { return SRMECH_ERR_OVERFLOW; }
    *out = (ts_rterm_t *)raw;
    for (i = 0; i < count; i++) {
        st = ts_bind_rterm(c, &(*out)[i], max_pairs);
        if (st != SRMECH_OK) { return st; }
        (*out)[i].live = 0;
    }
    return SRMECH_OK;
}

static srmech_status_t ts_build_rewrite_if(ts_ctx_t *c, const ts_rterm_t *src,
                                           int sym, int xsym, int ysym,
                                           ts_rterm_t *outA, ts_rterm_t *outB,
                                           int *did, ts_scr_t *s);

/* One reduction pass over symbol `sym`: rewrite every live cur-rterm (1->2) into
 * nxt, or copy it through when no rewrite applies. Sets *changed. Then combine nxt
 * and copy it back to cur. */
static srmech_status_t ts_reduce_pass(ts_ctx_t *c, ts_work_t *w, int sym,
                                      int xsym, int ysym, int *changed,
                                      ts_scr_t *s)
{
    size_t i;
    int did;
    srmech_status_t st;
    assert(c != NULL && w != NULL && changed != NULL && s != NULL);
    assert(w->cur != NULL && w->nxt != NULL);
    w->n_nxt = 0;
    for (i = 0; i < w->n_cur; i++) {
        if (!w->cur[i].live) { continue; }
        if (w->n_nxt + 2u > w->cap) { return SRMECH_ERR_OVERFLOW; }
        st = ts_build_rewrite_if(c, &w->cur[i], sym, xsym, ysym,
                                 &w->nxt[w->n_nxt], &w->nxt[w->n_nxt + 1],
                                 &did, s);
        if (st != SRMECH_OK) { return st; }
        if (did) {
            w->n_nxt += 2u;
            *changed = 1;
        } else {
            st = ts_rterm_copy(c, &w->nxt[w->n_nxt], &w->cur[i]);
            if (st != SRMECH_OK) { return st; }
            w->n_nxt += 1u;
        }
    }
    st = ts_combine_rterms(c, w->nxt, w->n_nxt, s);
    if (st != SRMECH_OK) { return st; }
    /* copy nxt (live only) back into cur. */
    w->n_cur = 0;
    for (i = 0; i < w->n_nxt; i++) {
        if (!w->nxt[i].live) { continue; }
        if (w->n_cur >= w->cap) { return SRMECH_ERR_OVERFLOW; }
        st = ts_rterm_copy(c, &w->cur[w->n_cur], &w->nxt[i]);
        if (st != SRMECH_OK) { return st; }
        w->n_cur++;
    }
    return SRMECH_OK;
}

/* The find+build wrapper: locate the rewrite operands and build the two terms (or
 * set *did = 0). Keeps ts_reduce_pass short. */
static srmech_status_t ts_build_rewrite_if(ts_ctx_t *c, const ts_rterm_t *src,
                                           int sym, int xsym, int ysym,
                                           ts_rterm_t *outA, ts_rterm_t *outB,
                                           int *did, ts_scr_t *s)
{
    size_t s_idx;
    size_t p_idx;
    assert(c != NULL && src != NULL && did != NULL);
    assert(outA != NULL && outB != NULL && s != NULL);
    *did = 0;
    ts_find_rewrite(c, src, sym, &s_idx, &p_idx);
    if (s_idx == (size_t)-1) { return SRMECH_OK; }
    *did = 1;
    return ts_build_rewrite(c, src, s_idx, p_idx, outA, outB, s->rp, s->cm,
                            xsym, ysym, s);
}

/* Reduce ONE quasi-periodicity class (its members in `cur[0..n_cur)`, already
 * recovered into +/- -pairs) to canonical Weierstrass normal form: repeatedly apply
 * the strictly-decreasing three-term rewrite on x then y until no change, combining
 * like terms each pass. The class is == 0 IFF the final live count is 0. Sets
 * *is_zero accordingly. Mirrors _reduce_class + _class_is_zero (the reduce-None
 * case -- a non-+/- -pair member -- is handled by the caller before this). */
static srmech_status_t ts_reduce_class(ts_ctx_t *c, ts_work_t *w, int xsym,
                                       int ysym, int *is_zero, ts_scr_t *s)
{
    uint32_t pass;
    int syms2[2];
    size_t i;
    int which;
    srmech_status_t st;
    assert(c != NULL && w != NULL && is_zero != NULL && s != NULL);
    assert(w->cur != NULL && w->n_cur <= w->cap);
    *is_zero = 0;
    /* initial combine of the recovered members. */
    st = ts_combine_rterms(c, w->cur, w->n_cur, s);
    if (st != SRMECH_OK) { return st; }
    /* compact cur to live-only. */
    {
        size_t k = 0;
        for (i = 0; i < w->n_cur; i++) {
            if (!w->cur[i].live) { continue; }
            if (k != i) {
                st = ts_rterm_copy(c, &w->cur[k], &w->cur[i]);
                if (st != SRMECH_OK) { return st; }
            }
            k++;
        }
        w->n_cur = k;
    }
    syms2[0] = xsym;
    syms2[1] = ysym;
    for (pass = 0; pass < TS_REDUCE_MAX_PASSES; pass++) {
        int changed = 0;
        for (which = 0; which < 2; which++) {
            if (syms2[which] < 0) { continue; }
            st = ts_reduce_pass(c, w, syms2[which], xsym, ysym, &changed, s);
            if (st != SRMECH_OK) { return st; }
        }
        if (!changed) { break; }
    }
    *is_zero = (w->n_cur == 0) ? 1 : 0;
    return SRMECH_OK;
}

/* ---- input term storage + the public is_zero orchestration ------------------ */

/* One parsed numerator term: a prefactor monomial + an array of theta-argument
 * monomials (the canonical thetas the bridge passed). */
typedef struct ts_term {
    ts_mono_t  pref;
    ts_mono_t *targs;      /* n_thetas theta-argument monomials              */
    size_t     n_thetas;
    int32_t   *class_key;  /* the quasi-periodicity class key exps (n_syms)  */
} ts_term_t;

/* Parse the wire form into `terms[0..n_terms)`. The flat monomial arrays are read
 * in order: term0.pref, term0.theta0..thetaK, term1.pref, ... . Each monomial's
 * coeff (num, den) is a srmech_bigint pair; its exps a flat int32[n_syms] row. */
static srmech_status_t ts_parse_terms(ts_ctx_t *c, ts_term_t *terms,
                                      size_t n_terms, const size_t *term_nthetas,
                                      const srmech_bigint_t *coeff_num,
                                      const srmech_bigint_t *coeff_den,
                                      const int32_t *exps_flat)
{
    size_t ti;
    size_t mi = 0;       /* running monomial index into the flat arrays */
    size_t ej = 0;       /* running exps-row index                      */
    srmech_status_t st;
    assert(c != NULL && terms != NULL && term_nthetas != NULL);
    assert(coeff_num != NULL && coeff_den != NULL && exps_flat != NULL);
    for (ti = 0; ti < n_terms; ti++) {
        size_t k;
        st = srmech_bigint_copy(&terms[ti].pref.coeff.num, &coeff_num[mi]);
        if (st == SRMECH_OK) {
            st = srmech_bigint_copy(&terms[ti].pref.coeff.den, &coeff_den[mi]);
        }
        if (st != SRMECH_OK) { return st; }
        memcpy(terms[ti].pref.exps, exps_flat + ej, c->n_syms * sizeof(int32_t));
        mi++;
        ej += c->n_syms;
        for (k = 0; k < term_nthetas[ti]; k++) {
            st = srmech_bigint_copy(&terms[ti].targs[k].coeff.num, &coeff_num[mi]);
            if (st == SRMECH_OK) {
                st = srmech_bigint_copy(&terms[ti].targs[k].coeff.den,
                                        &coeff_den[mi]);
            }
            if (st != SRMECH_OK) { return st; }
            memcpy(terms[ti].targs[k].exps, exps_flat + ej,
                   c->n_syms * sizeof(int32_t));
            mi++;
            ej += c->n_syms;
        }
        terms[ti].n_thetas = term_nthetas[ti];
    }
    return SRMECH_OK;
}

/* Decide whether ONE class (the terms whose class_key == `key`) reduces to zero.
 * Recovers each member's +/- -pairs into the work `cur` buffer; a member outside the
 * clean +/- -pair shape -> the class is NOT zero (honest, like _reduce_class None).
 * Sets *class_zero. Mirrors _class_is_zero for a single class. */
static srmech_status_t ts_one_class_is_zero(ts_ctx_t *c, const ts_term_t *terms,
                                            size_t n_terms, const int32_t *key,
                                            int xsym, int ysym, ts_work_t *w,
                                            int *class_zero, ts_scr_t *s, int *used)
{
    size_t ti;
    int ok;
    srmech_status_t st;
    assert(c != NULL && terms != NULL && key != NULL && w != NULL);
    assert(class_zero != NULL && s != NULL && used != NULL);
    *class_zero = 0;
    w->n_cur = 0;
    for (ti = 0; ti < n_terms; ti++) {
        if (ts_exps_cmp(c, terms[ti].class_key, key) != 0) { continue; }
        if (w->n_cur >= w->cap) { return SRMECH_ERR_OVERFLOW; }
        st = ts_mono_copy(c, &w->cur[w->n_cur].pref, &terms[ti].pref);
        if (st != SRMECH_OK) { return st; }
        w->cur[w->n_cur].live = 1;
        st = ts_recover_pairs(c, &w->cur[w->n_cur], terms[ti].targs,
                              terms[ti].n_thetas, xsym, ysym, &ok, s, used);
        if (st != SRMECH_OK) { return st; }
        if (!ok) {
            return SRMECH_OK;        /* not a clean +/- -pair shape -> NOT zero */
        }
        w->n_cur++;
    }
    return ts_reduce_class(c, w, xsym, ysym, class_zero, s);
}

/* The public is_zero orchestration: parse the terms, compute each term's quasi-
 * periodicity class key, then -- for each DISTINCT class -- decide it reduces to
 * zero. The whole numerator is == 0 IFF every class is == 0. An empty numerator is
 * == 0 with no work (the caller passes n_terms == 0). */
static srmech_status_t ts_decide(ts_ctx_t *c, ts_term_t *terms, size_t n_terms,
                                 int xsym, int ysym, int psym, int *out_is_zero,
                                 ts_work_t *w, ts_scr_t *s, int *used)
{
    size_t ti;
    size_t tj;
    srmech_status_t st;
    assert(c != NULL && out_is_zero != NULL && w != NULL && s != NULL);
    assert(terms != NULL || n_terms == 0u);
    *out_is_zero = 1;
    if (n_terms == 0u) { return SRMECH_OK; }
    /* class key per term. */
    for (ti = 0; ti < n_terms; ti++) {
        st = ts_net_period_key(c, terms[ti].targs, terms[ti].n_thetas, xsym, ysym,
                               psym, terms[ti].class_key, &s->pm[0], &s->pm[1],
                               &s->pm[2], &s->pm[3]);
        if (st != SRMECH_OK) { return st; }
    }
    /* for each DISTINCT class (first occurrence), decide it is zero. */
    for (ti = 0; ti < n_terms; ti++) {
        int seen = 0;
        int class_zero = 0;
        for (tj = 0; tj < ti; tj++) {
            if (ts_exps_cmp(c, terms[tj].class_key, terms[ti].class_key) == 0) {
                seen = 1;
                break;
            }
        }
        if (seen) { continue; }
        st = ts_one_class_is_zero(c, terms, n_terms, terms[ti].class_key, xsym,
                                  ysym, w, &class_zero, s, used);
        if (st != SRMECH_OK) { return st; }
        if (!class_zero) {
            *out_is_zero = 0;
            return SRMECH_OK;
        }
    }
    return SRMECH_OK;
}

/* ---- sizing + bind-all + the public entry ----------------------------------- */

/* The per-buffer rterm slot capacity for the reduction work arrays: each class has
 * at most `n_terms` members; each three-term rewrite pass can at most DOUBLE the
 * live count, but the strictly-decreasing midpoint multiset bounds the firing depth.
 * A generous arena-sized bound (no compiled-in MATH cap -- it scales with the input
 * term count) that the combine step keeps from actually ballooning. */
static size_t ts_work_cap(size_t n_terms, size_t max_thetas)
{
    size_t base = (n_terms == 0u) ? 1u : n_terms;
    size_t pairs = (max_thetas / 2u) + 1u;
    assert(base >= 1u);
    assert(pairs >= 1u);
    /* room for the per-pass 1->2 fan-out before each combine collapses it. */
    return (base * 4u + 8u) * (pairs + 1u);
}

static size_t ts_max_thetas(const size_t *term_nthetas, size_t n_terms)
{
    size_t i;
    size_t mx = 0;
    assert(term_nthetas != NULL || n_terms == 0u);
    for (i = 0; i < n_terms; i++) {
        assert(term_nthetas != NULL);
        if (term_nthetas[i] > mx) { mx = term_nthetas[i]; }
    }
    return mx;
}

/* Bind the term array (each term's pref + theta-arg monomials + class-key row). */
static srmech_status_t ts_bind_terms(ts_ctx_t *c, ts_term_t **out, size_t n_terms,
                                     const size_t *term_nthetas)
{
    size_t i;
    size_t words;
    uint32_t *raw;
    srmech_status_t st;
    assert(c != NULL && out != NULL);
    assert(term_nthetas != NULL || n_terms == 0u);
    ts_align8(c);
    words = ((n_terms == 0u ? 1u : n_terms) * sizeof(ts_term_t)
             + sizeof(uint32_t) - 1u) / sizeof(uint32_t);
    raw = ts_take_words(c, words);
    if (raw == NULL) { return SRMECH_ERR_OVERFLOW; }
    *out = (ts_term_t *)raw;
    for (i = 0; i < n_terms; i++) {
        size_t nt = term_nthetas[i];
        st = ts_bind_mono(c, &(*out)[i].pref);
        if (st != SRMECH_OK) { return st; }
        st = ts_bind_mono_arr(c, &(*out)[i].targs, (nt == 0u) ? 1u : nt);
        if (st != SRMECH_OK) { return st; }
        (*out)[i].class_key = ts_take_exps(c);
        if ((*out)[i].class_key == NULL) { return SRMECH_ERR_OVERFLOW; }
        (*out)[i].n_thetas = nt;
    }
    return SRMECH_OK;
}

/* Carve the arena: split `ws` into the bump pool + a trailing bigint scratch region
 * (8-byte-aligned uint32). Returns OVERFLOW if `ws` is NULL or too small. */
static srmech_status_t ts_arena_init(ts_ctx_t *c, void *ws, size_t ws_len)
{
    uint32_t *base = (uint32_t *)ws;
    size_t words = ws_len / sizeof(uint32_t);
    size_t scratch_words = (size_t)c->cap * 16u + 512u;
    assert(c != NULL);
    assert((uintptr_t)ws % 8u == 0u || ws == NULL);
    if (ws == NULL || words < scratch_words + 64u) {
        return SRMECH_ERR_OVERFLOW;
    }
    c->pool = base;
    c->pool_words = words - scratch_words;
    c->pool_cur = 0u;
    c->scratch = (void *)(base + (words - scratch_words));
    c->scratch_len = scratch_words * sizeof(uint32_t);
    return SRMECH_OK;
}

/* Bind every working buffer (terms, scratch bundle, the two rterm work buffers, the
 * `used` recover marks) from the arena. Sets w->cap / w->cur / w->nxt + *used. */
static srmech_status_t ts_bind_all(ts_ctx_t *c, ts_term_t **terms,
                                   const size_t *term_nthetas, size_t n_terms,
                                   ts_scr_t *scr, ts_work_t *w, int **used)
{
    size_t max_thetas = ts_max_thetas(term_nthetas, n_terms);
    size_t cap_rt = ts_work_cap(n_terms, max_thetas);
    size_t max_pairs = (max_thetas / 2u) + 1u;
    uint32_t *u;
    srmech_status_t st;
    assert(c != NULL && terms != NULL && scr != NULL && w != NULL && used != NULL);
    assert(n_terms >= 1u);
    st = ts_bind_terms(c, terms, n_terms, term_nthetas);
    if (st == SRMECH_OK) { st = ts_bind_scr(c, scr, max_thetas); }
    if (st == SRMECH_OK) { st = ts_bind_rterm_arr(c, &w->cur, cap_rt, max_pairs); }
    if (st == SRMECH_OK) { st = ts_bind_rterm_arr(c, &w->nxt, cap_rt, max_pairs); }
    if (st != SRMECH_OK) { return st; }
    u = ts_take_words(c, (max_thetas == 0u) ? 1u : max_thetas);
    if (u == NULL) { return SRMECH_ERR_OVERFLOW; }
    *used = (int *)u;
    w->cap = cap_rt;
    w->n_cur = 0;
    w->n_nxt = 0;
    return SRMECH_OK;
}

/* Decide whether the cleared numerator (the `n_terms` terms) is identically zero --
 * the C peer of ThetaSum.is_zero, a COMPLETE structural mirror of the Weierstrass
 * three-term + quasi-periodicity reduction. The wire form: the interned symbol-table
 * dimension `n_syms` + the p / x / y indices (-1 if absent); the per-term theta
 * counts `term_nthetas`; the flat monomial coeff arrays (coeff_num/coeff_den, in
 * term0.pref, term0.thetas, term1.pref, ... order) + the flat exps rows
 * (int32[n_syms] each, same order). *out_is_zero = 1 iff == 0. Caller arena `ws`. */
srmech_status_t srmech_thetasum_is_zero(size_t n_syms, int xsym, int ysym, int psym,
                                        size_t n_terms, const size_t *term_nthetas,
                                        const srmech_bigint_t *coeff_num,
                                        const srmech_bigint_t *coeff_den,
                                        const int32_t *exps_flat,
                                        uint32_t coeff_cap, int *out_is_zero,
                                        void *ws, size_t ws_len)
{
    ts_ctx_t c = {0};
    ts_term_t *terms = NULL;
    ts_scr_t scr = {0};
    ts_work_t w = {0};
    int *used = NULL;
    srmech_status_t st;
    assert(out_is_zero != NULL);
    assert(term_nthetas != NULL || n_terms == 0u);
    if (out_is_zero == NULL) { return SRMECH_ERR_NULL_ARG; }
    *out_is_zero = 1;
    if (n_terms == 0u) { return SRMECH_OK; }
    if (term_nthetas == NULL || coeff_num == NULL || coeff_den == NULL
        || exps_flat == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    c.n_syms = (n_syms == 0u) ? 1u : n_syms;
    c.cap = (coeff_cap < 4u) ? 4u : coeff_cap;
    st = ts_arena_init(&c, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    st = ts_bind_all(&c, &terms, term_nthetas, n_terms, &scr, &w, &used);
    if (st != SRMECH_OK) { return st; }
    scr.psym = psym;
    st = ts_parse_terms(&c, terms, n_terms, term_nthetas, coeff_num, coeff_den,
                        exps_flat);
    if (st != SRMECH_OK) { return st; }
    return ts_decide(&c, terms, n_terms, xsym, ysym, psym, out_is_zero, &w, &scr,
                     used);
}

/* The minimum `ws_len` BYTES srmech_thetasum_is_zero needs for the given shape. */
size_t srmech_thetasum_ws_bound(size_t n_syms, size_t n_terms, size_t max_thetas,
                                size_t coeff_limbs)
{
    size_t cap = (coeff_limbs < 4u) ? 4u : coeff_limbs;
    size_t ns = (n_syms == 0u) ? 1u : n_syms;
    size_t cap_rt = ts_work_cap(n_terms, max_thetas);
    size_t pairs = (max_thetas / 2u) + 1u;
    /* Per-monomial words: 2 bigints (2*cap) + an exps row (ns int32). */
    size_t mono_words = 2u * cap + ns + 8u;
    /* a pair = 2 monomials; an rterm = pref mono + `pairs` pair slots + struct. */
    size_t rterm_words = mono_words + pairs * (2u * mono_words) + 64u;
    /* the parsed-term storage (pref + max_thetas targs + class key + struct). */
    size_t term_words = mono_words + max_thetas * mono_words + ns + 64u;
    size_t terms_total = (n_terms + 1u) * term_words;
    size_t scr_words = (TS_SCR_MONOS + TS_REWRITE_MONOS + 4u) * mono_words
                       + 6u * (2u * mono_words) + 8u * cap + 256u;
    size_t work_words = 2u * (cap_rt + 1u) * rterm_words + max_thetas + 64u;
    size_t scratch_words = cap * 16u + 512u;
    size_t total = terms_total + scr_words + work_words + scratch_words + 1024u;
    assert(cap >= 4u);
    assert(total >= scratch_words);
    return total * sizeof(uint32_t);
}
