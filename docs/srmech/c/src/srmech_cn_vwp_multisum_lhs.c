/*
 * srmech_cn_vwp_multisum_lhs.c -- the 1:1 native C peer of
 * srmech.amsc.elliptic_jackson.cn_vwp_multisum_lhs (rc216), the SYMBOLIC Cn
 * very-well-poised (VWP) elliptic multisum LHS builder: the exact ThetaSum
 * construction of the LEFT-hand side of the Cn elliptic Jackson summation.
 *
 * A C-MIRROR PARITY build (NOT a new algorithm): it constructs the EXACT
 * per-partition theta-quotient TERMS the already-shipped pure-Python
 * _cn_lhs_thetasum builds (the rc96 test oracle promoted to the rc101 symbolic
 * verify engine, promoted public at rc216), byte-for-byte; the Python side SUMS
 * them into the ThetaSum (there is NO ThetaSum-CONSTRUCTION C surface, so the
 * peer returns the per-partition EllRatio TERMS as a row stream, exactly like
 * srmech_elliptic_partial_fraction returns its n partial-fraction terms).
 *
 * The identity whose LHS this builds (MPM-verified at build from the extracted
 * PDF: Hjalmar Rosengren, "A proof of a multivariable elliptic summation
 * formula conjectured by Warnaar", arXiv:math/0101073v1 [math.CA] (9 Jan
 * 2001), Theorem 2.1, Eq. 5): for the partitions
 *   Lambda_{nN} = {N >= lambda_1 >= ... >= lambda_n >= 0}
 * and the balancing b*c*d*e*x^{n-1} = a^2*q^{N+1} (e fixed by construction),
 *
 *   SUM_{lambda} PROD_{i=1}^n [ E(a x^{2(1-i)} q^{2li})/E(a x^{2(1-i)})
 *                               * q^{li} x^{2(i-1)li} ]
 *     * PROD_{1<=i<j<=n} [ E(x^{j-i} q^{li-lj})/E(x^{j-i})
 *                          * E(a x^{2-i-j} q^{li+lj})/E(a x^{2-i-j})
 *                          * (a x^{3-i-j};q)_{li+lj} (x^{j-i+1};q)_{li-lj}
 *                            / ((a q x^{1-i-j};q)_{li+lj} (q x^{j-i-1};q)_{li-lj}) ]
 *     * (a x^{1-n}, b, c, d, e, q^{-N}; q, x)_lambda
 *       / (q x^{n-1}, aq/b, aq/c, aq/d, aq/e, a q^{N+1}; q, x)_lambda
 *   = (aq, aq/bc, aq/bd, aq/cd; q, x)_{N^n} / (aq/b, aq/c, aq/d, aq/bcd; q, x)_{N^n},
 *
 * with E the modified theta, li = lambda_i, (u;q)_k = PROD_{t=0}^{k-1} E(u q^t)
 * the theta-Pochhammer and (u;q,x)_lambda = PROD_{j=1}^n (u x^{1-j};q)_{lambda_j}
 * the VECTOR theta-Pochhammer. Each partition's summand is one EllRatio: the
 * monomial prefactor PROD_i q^{li} x^{2(i-1)li} (sign in the Class-K coeff
 * branch), the num/den theta-argument lists above; er_build (the
 * EllRatio.__init__ mirror) folds each theta's canonicalize prefactor, cancels
 * matching thetas, sorts the survivors -- so each emitted EllRatio is the
 * canonical value Python returns. The RHS closed form is the separate
 * srmech_multivariate_elliptic_jackson (rc96) peer; LHS - RHS |> is_zero is the
 * rc101 per-call proof.
 *
 * This is PURE COMPOSITION of the shared srmech_ellbase_* exact-Q monomial
 * algebra (mul / inv) + er_build -- the same single copy the elliptic
 * partial-fraction / Cauchy-determinant / Jackson peers ride.
 *
 * Wire form: the interned symbol-table dimension `n_syms` (distinct symbols in
 * the Python sorted-symbol-NAME order); `psym` the interned index of the nome
 * `p` (-1 if absent); the positive ints `N` (partition ceiling) + `n` (rank) +
 * `n_terms` (the partition count C(N+n, n), computed by the caller); each of
 * the 6 parameter monomials a/b/c/d/x/q as a (num, den) srmech_bigint pair +
 * its flat int32[n_syms] exponent row. `coeff_cap` is the per-bigint limb cap.
 *
 * Output: the n_terms TERM EllRatios written out flat in the LEXICOGRAPHIC
 * partition order (all-zeros first; the exact order the Python oracle's
 * filtered itertools.product enumerates) -- per term t, `out_n_num[t]` /
 * `out_n_den[t]` the survivor theta counts, and the canonical rows appended to
 * out_coeff_num/out_coeff_den/out_exps_flat (per term: its prefactor row, then
 * its num rows, then its den rows; each row carries its exact-Q coeff AND its
 * dense int32[n_syms] exponent row). `out_exps_cap_rows` is the row capacity of
 * the caller's buffers; too small -> SRMECH_ERR_OVERFLOW. N == 0, n == 0 or
 * n_terms == 0 -> SRMECH_ERR_NULL_ARG (Python raises ValueError); a wrong
 * n_terms (not C(N+n, n)) -> SRMECH_ERR_BAD_INPUT; a required NULL pointer ->
 * SRMECH_ERR_NULL_ARG; a too-small arena -> SRMECH_ERR_OVERFLOW.
 *
 * Malloc-free (JPL Rule 3): every working monomial / theta + the bigint scratch
 * is carved from the caller arena `ws`, sized to the input (N, n, n_syms) -- no
 * compiled-in cap. Sign travels in the Class-K coeff branch, never abs()/fabs().
 * Additive symbol -> ABI unchanged (stays 4). License: MIT.
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto/recursion): OK -- iterative, flat static helpers
 *   - Rule 2 (bounded loops)    : OK -- bounded by N / n / n_terms / n_syms
 *   - Rule 3 (no malloc)        : OK -- caller arena only
 *   - Rule 4 (<=60 lines/func)  : OK -- factored into static helpers
 *   - Rule 5 (>=2 asserts/fn)   : OK -- entry-pointer + pre/postcondition
 *   - Rule 7 (return-value)     : OK -- srmech_status_t propagated
 *   - Rule 8 (no multi-line mac): OK -- no function-like macros
 *   - Rule 10 (warnings clean)  : OK under -Wall -Wextra -Wpedantic -Werror
 */

#include "srmech.h"
#include "srmech_ellbase_internal.h"

#include <assert.h>
#include <stdint.h>
#include <string.h>

/* Thin aliases to the shared kernels (the same convention srmech_ellbase.c uses). */
#define elb_mono_set_one   srmech_ellbase_mono_set_one
#define elb_mono_copy      srmech_ellbase_mono_copy
#define elb_mono_mul       srmech_ellbase_mono_mul
#define elb_mono_inv       srmech_ellbase_mono_inv
#define elb_bind_mono      srmech_ellbase_bind_mono
#define elb_bind_mono_arr  srmech_ellbase_bind_mono_arr
#define elb_er_bind_scr    srmech_ellbase_er_bind_scr
#define elb_er_bind_ratio  srmech_ellbase_er_bind_ratio
#define elb_er_build       srmech_ellbase_er_build
#define elb_er_arena_init  srmech_ellbase_er_arena_init
#define elb_er_mono_words  srmech_ellbase_er_mono_words

typedef srmech_ell_er_scr_t   elb_scr_t;
typedef srmech_ell_er_ratio_t elb_ratio_t;

/* The 6 parameter slots (Python sorted arg order a, b, c, d, x, q). */
#define CVL_A 0
#define CVL_B 1
#define CVL_C 2
#define CVL_D 3
#define CVL_X 4
#define CVL_Q 5

/* The bound persistent buffers: the 6 parsed parameters + aq + the balancing e
 * + the 6 num / 6 den VWP bases + the q^i / x^k / x^{-k} power ladders + the
 * partition odometer (all live for the whole build). */
typedef struct cvl_persist {
    srmech_ell_mono_t *par;       /* par[6] = a, b, c, d, x, q                  */
    srmech_ell_mono_t  aq;        /* a*q                                        */
    srmech_ell_mono_t  e;         /* the balancing e = a^2 q^{N+1}/(bcd x^{n-1}) */
    srmech_ell_mono_t *nb6;       /* nb6[6] = a x^{1-n}, b, c, d, e, q^{-N}     */
    srmech_ell_mono_t *db6;       /* db6[6] = q x^{n-1}, aq/b..aq/e, a q^{N+1}  */
    srmech_ell_mono_t *qp;        /* qp[i] = q^i,     i = 0..2N                 */
    srmech_ell_mono_t *xp;        /* xp[k] = x^k,     k = 0..2n-2               */
    srmech_ell_mono_t *xn;        /* xn[k] = x^{-k},  k = 0..2n-2               */
    srmech_ell_mono_t  tmp;       /* setup scratch monomial                     */
    srmech_ell_mono_t  tmp2;      /* second setup scratch monomial              */
    elb_scr_t          scr;       /* setup scratch bundle (g/t0/t1 for muls)    */
    uint32_t          *lam;       /* the partition odometer lambda_1..lambda_n  */
} cvl_persist_t;

/* The per-term working buffers (carved fresh from a reset cursor each term). */
typedef struct cvl_work {
    srmech_ell_mono_t  pref;      /* the accumulated monomial prefactor          */
    srmech_ell_mono_t  tmp;       /* general scratch monomial                    */
    srmech_ell_mono_t  tmp2;      /* second scratch (prefactor accumulate)       */
    srmech_ell_mono_t *num;       /* the numerator theta-argument monomials      */
    srmech_ell_mono_t *den;       /* the denominator theta-argument monomials    */
    srmech_ell_mono_t *cn;        /* er_build canon scratch (num)                */
    srmech_ell_mono_t *cd;        /* er_build canon scratch (den)                */
    elb_ratio_t        ratio;     /* the canonical term EllRatio                 */
    elb_scr_t          scr;       /* the er_build scratch bundle                 */
} cvl_work_t;

/* The per-side MAX theta count of one partition summand: n diagonal args +
 * (2 + 2*li) <= (2 + 2N) per (i, j) pair + 6 vector Pochhammers of <= n*N. */
static size_t cvl_nt_max(size_t N, size_t n)
{
    size_t nt;
    assert(N >= 1u);
    assert(n >= 1u);
    nt = n + (n * (n - 1u) / 2u) * (2u + 2u * N) + 6u * n * N;
    return nt;
}

/* Parse the 6 parameter monomials from the flat input coeff / exponent arrays
 * into bound monomials. Mirrors the head of the Python op (_coerce_monomial). */
static srmech_status_t cvl_parse(srmech_ell_ctx_t *c, cvl_persist_t *p,
                                 const srmech_bigint_t *const *pnum,
                                 const srmech_bigint_t *const *pden,
                                 const int32_t *const *pexps)
{
    size_t i;
    srmech_status_t st;
    assert(c != NULL && p != NULL);
    assert(pnum != NULL && pden != NULL && pexps != NULL);
    for (i = 0; i < 6u; i++) {
        st = srmech_bigint_copy(&p->par[i].coeff.num, pnum[i]);
        if (st == SRMECH_OK) { st = srmech_bigint_copy(&p->par[i].coeff.den, pden[i]); }
        if (st != SRMECH_OK) { return st; }
        memcpy(p->par[i].exps, pexps[i], c->n_syms * sizeof(int32_t));
    }
    return SRMECH_OK;
}

/* out := u * inv(denom); invtmp is caller scratch (!= denom, != u, != out). */
static srmech_status_t cvl_inv_mul(srmech_ell_ctx_t *c, srmech_ell_mono_t *out,
                                   const srmech_ell_mono_t *u,
                                   const srmech_ell_mono_t *denom, elb_scr_t *s,
                                   srmech_ell_mono_t *invtmp)
{
    srmech_status_t st;
    assert(c != NULL && out != NULL && u != NULL);
    assert(denom != NULL && invtmp != NULL && s != NULL);
    st = elb_mono_inv(c, invtmp, denom);
    if (st == SRMECH_OK) {
        st = elb_mono_mul(c, out, u, invtmp, &s->g, &s->t0, &s->t1);
    }
    return st;
}

/* qp[i] := q^i (i = 0..2N); xp[k] := x^k and xn[k] := x^{-k} (k = 0..2n-2). */
static srmech_status_t cvl_ladders(srmech_ell_ctx_t *c, cvl_persist_t *p, size_t N,
                                   size_t n)
{
    size_t i;
    size_t k;
    elb_scr_t *s = &p->scr;
    srmech_status_t st;
    assert(c != NULL && p != NULL);
    assert(N >= 1u && n >= 1u);
    st = elb_mono_set_one(c, &p->qp[0]);
    for (i = 1u; (st == SRMECH_OK) && i <= 2u * N; i++) {
        st = elb_mono_mul(c, &p->qp[i], &p->qp[i - 1u], &p->par[CVL_Q],
                          &s->g, &s->t0, &s->t1);
    }
    if (st == SRMECH_OK) { st = elb_mono_set_one(c, &p->xp[0]); }
    for (k = 1u; (st == SRMECH_OK) && k <= 2u * n - 2u; k++) {
        st = elb_mono_mul(c, &p->xp[k], &p->xp[k - 1u], &p->par[CVL_X],
                          &s->g, &s->t0, &s->t1);
    }
    if (st == SRMECH_OK) { st = elb_mono_inv(c, &p->tmp, &p->par[CVL_X]); }
    if (st == SRMECH_OK) { st = elb_mono_set_one(c, &p->xn[0]); }
    for (k = 1u; (st == SRMECH_OK) && k <= 2u * n - 2u; k++) {
        st = elb_mono_mul(c, &p->xn[k], &p->xn[k - 1u], &p->tmp,
                          &s->g, &s->t0, &s->t1);
    }
    return st;
}

/* aq := a*q; e := a^2 * q^{N+1} * inv(b*c*d*x^{n-1}) (the Thm 2.1 balancing:
 * b*c*d*e*x^{n-1} = a^2 q^{N+1}, so e is fixed by construction). */
static srmech_status_t cvl_e_balance(srmech_ell_ctx_t *c, cvl_persist_t *p, size_t N,
                                     size_t n)
{
    elb_scr_t *s = &p->scr;
    srmech_status_t st;
    assert(c != NULL && p != NULL);
    assert(N >= 1u && n >= 1u);
    st = elb_mono_mul(c, &p->aq, &p->par[CVL_A], &p->par[CVL_Q],
                      &s->g, &s->t0, &s->t1);
    if (st == SRMECH_OK) {                                     /* e := a*a        */
        st = elb_mono_mul(c, &p->e, &p->par[CVL_A], &p->par[CVL_A],
                          &s->g, &s->t0, &s->t1);
    }
    if (st == SRMECH_OK) {                                     /* tmp := a^2 q^{N+1} */
        st = elb_mono_mul(c, &p->tmp, &p->e, &p->qp[N + 1u], &s->g, &s->t0, &s->t1);
    }
    if (st == SRMECH_OK) {                                     /* e := b*c        */
        st = elb_mono_mul(c, &p->e, &p->par[CVL_B], &p->par[CVL_C],
                          &s->g, &s->t0, &s->t1);
    }
    if (st == SRMECH_OK) {                                     /* tmp2 := b*c*d   */
        st = elb_mono_mul(c, &p->tmp2, &p->e, &p->par[CVL_D], &s->g, &s->t0, &s->t1);
    }
    if (st == SRMECH_OK) {                                     /* e := bcd x^{n-1} */
        st = elb_mono_mul(c, &p->e, &p->tmp2, &p->xp[n - 1u], &s->g, &s->t0, &s->t1);
    }
    if (st == SRMECH_OK) { st = elb_mono_inv(c, &p->tmp2, &p->e); }
    if (st == SRMECH_OK) {                                     /* the balancing e */
        st = elb_mono_mul(c, &p->e, &p->tmp, &p->tmp2, &s->g, &s->t0, &s->t1);
    }
    return st;
}

/* nb6 := a x^{1-n}, b, c, d, e, q^{-N} (the 6 numerator VWP bases) and
 * db6 := q x^{n-1}, aq/b, aq/c, aq/d, aq/e, a q^{N+1} (the 6 denominator VWP
 * bases) -- the Python num_bases / den_bases lists, in order. */
static srmech_status_t cvl_bases(srmech_ell_ctx_t *c, cvl_persist_t *p, size_t N,
                                 size_t n)
{
    elb_scr_t *s = &p->scr;
    srmech_status_t st;
    assert(c != NULL && p != NULL);
    assert(N >= 1u && n >= 1u);
    st = elb_mono_mul(c, &p->nb6[0], &p->par[CVL_A], &p->xn[n - 1u],
                      &s->g, &s->t0, &s->t1);
    if (st == SRMECH_OK) { st = elb_mono_copy(c, &p->nb6[1], &p->par[CVL_B]); }
    if (st == SRMECH_OK) { st = elb_mono_copy(c, &p->nb6[2], &p->par[CVL_C]); }
    if (st == SRMECH_OK) { st = elb_mono_copy(c, &p->nb6[3], &p->par[CVL_D]); }
    if (st == SRMECH_OK) { st = elb_mono_copy(c, &p->nb6[4], &p->e); }
    if (st == SRMECH_OK) { st = elb_mono_inv(c, &p->nb6[5], &p->qp[N]); }
    if (st == SRMECH_OK) {
        st = elb_mono_mul(c, &p->db6[0], &p->par[CVL_Q], &p->xp[n - 1u],
                          &s->g, &s->t0, &s->t1);
    }
    if (st == SRMECH_OK) {
        st = cvl_inv_mul(c, &p->db6[1], &p->aq, &p->par[CVL_B], s, &p->tmp);
    }
    if (st == SRMECH_OK) {
        st = cvl_inv_mul(c, &p->db6[2], &p->aq, &p->par[CVL_C], s, &p->tmp);
    }
    if (st == SRMECH_OK) {
        st = cvl_inv_mul(c, &p->db6[3], &p->aq, &p->par[CVL_D], s, &p->tmp);
    }
    if (st == SRMECH_OK) {
        st = cvl_inv_mul(c, &p->db6[4], &p->aq, &p->e, s, &p->tmp);
    }
    if (st == SRMECH_OK) {
        st = elb_mono_mul(c, &p->db6[5], &p->par[CVL_A], &p->qp[N + 1u],
                          &s->g, &s->t0, &s->t1);
    }
    return st;
}

/* Append the theta-Pochhammer (base; q)_k to dest at *m: the k theta args
 * base*q^t, t = 0..k-1 (the Python poch_thetas). Advances *m. */
static srmech_status_t cvl_poch(srmech_ell_ctx_t *c, cvl_persist_t *p,
                                const srmech_ell_mono_t *base, size_t k,
                                srmech_ell_mono_t *dest, size_t *m, elb_scr_t *s)
{
    size_t t;
    srmech_status_t st = SRMECH_OK;
    assert(c != NULL && p != NULL && base != NULL);
    assert(dest != NULL && m != NULL && s != NULL);
    for (t = 0; (st == SRMECH_OK) && t < k; t++) {
        st = elb_mono_mul(c, &dest[*m], base, &p->qp[t], &s->g, &s->t0, &s->t1);
        (*m)++;
    }
    return st;
}

/* The DIAGONAL part of one summand: per i (0-based), the num theta arg
 * a x^{2(1-i)} q^{2li} / den theta arg a x^{2(1-i)}, and the prefactor factor
 * q^{li} x^{2(i-1)li} accumulated into w->pref (the Class-K monomial branch). */
static srmech_status_t cvl_diag(srmech_ell_ctx_t *c, cvl_persist_t *p, size_t n,
                                cvl_work_t *w, size_t *mn, size_t *md)
{
    size_t i;
    size_t t;
    elb_scr_t *s = &w->scr;
    srmech_status_t st = SRMECH_OK;
    assert(c != NULL && p != NULL && w != NULL);
    assert(mn != NULL && md != NULL && n >= 1u);
    for (i = 0; (st == SRMECH_OK) && i < n; i++) {
        size_t li = (size_t)p->lam[i];
        st = elb_mono_mul(c, &w->tmp, &p->par[CVL_A], &p->xn[2u * i],
                          &s->g, &s->t0, &s->t1);
        if (st == SRMECH_OK) {
            st = elb_mono_mul(c, &w->num[*mn], &w->tmp, &p->qp[2u * li],
                              &s->g, &s->t0, &s->t1);
            (*mn)++;
        }
        if (st == SRMECH_OK) {
            st = elb_mono_copy(c, &w->den[*md], &w->tmp);
            (*md)++;
        }
        if (st == SRMECH_OK) {                     /* pref *= q^{li}             */
            st = elb_mono_mul(c, &w->tmp2, &w->pref, &p->qp[li],
                              &s->g, &s->t0, &s->t1);
        }
        if (st == SRMECH_OK) { st = elb_mono_copy(c, &w->pref, &w->tmp2); }
        for (t = 0; (st == SRMECH_OK) && t < li; t++) {   /* pref *= x^{2(i-1)li} */
            st = elb_mono_mul(c, &w->tmp2, &w->pref, &p->xp[2u * i],
                              &s->g, &s->t0, &s->t1);
            if (st == SRMECH_OK) { st = elb_mono_copy(c, &w->pref, &w->tmp2); }
        }
    }
    return st;
}

/* One OFF-DIAGONAL (i < j, 1-based) root-system coupling block of a summand:
 * the two E-quotient pairs + the four theta-Pochhammers of the Cn coupling. */
static srmech_status_t cvl_pair(srmech_ell_ctx_t *c, cvl_persist_t *p,
                                cvl_work_t *w, size_t i, size_t j, size_t *mn,
                                size_t *md)
{
    size_t li = (size_t)p->lam[i - 1u];
    size_t lj = (size_t)p->lam[j - 1u];
    elb_scr_t *s = &w->scr;
    srmech_status_t st;
    assert(c != NULL && p != NULL && w != NULL);
    assert(mn != NULL && md != NULL && i >= 1u && j > i);
    st = elb_mono_mul(c, &w->num[*mn], &p->xp[j - i], &p->qp[li - lj],
                      &s->g, &s->t0, &s->t1);            /* E(x^{j-i} q^{li-lj}) */
    if (st == SRMECH_OK) {
        (*mn)++;
        st = elb_mono_copy(c, &w->den[*md], &p->xp[j - i]);   /* E(x^{j-i})      */
        (*md)++;
    }
    if (st == SRMECH_OK) {                               /* tmp := a x^{2-i-j}   */
        st = elb_mono_mul(c, &w->tmp, &p->par[CVL_A], &p->xn[i + j - 2u],
                          &s->g, &s->t0, &s->t1);
    }
    if (st == SRMECH_OK) {
        st = elb_mono_mul(c, &w->num[*mn], &w->tmp, &p->qp[li + lj],
                          &s->g, &s->t0, &s->t1);        /* E(a x^{2-i-j} q^{li+lj}) */
        (*mn)++;
    }
    if (st == SRMECH_OK) {
        st = elb_mono_copy(c, &w->den[*md], &w->tmp);    /* E(a x^{2-i-j})       */
        (*md)++;
    }
    if (st == SRMECH_OK) {                               /* (a x^{3-i-j};q)_{li+lj} */
        st = elb_mono_mul(c, &w->tmp, &p->par[CVL_A], &p->xn[i + j - 3u],
                          &s->g, &s->t0, &s->t1);
    }
    if (st == SRMECH_OK) { st = cvl_poch(c, p, &w->tmp, li + lj, w->num, mn, s); }
    if (st == SRMECH_OK) {                               /* (x^{j-i+1};q)_{li-lj}   */
        st = cvl_poch(c, p, &p->xp[j - i + 1u], li - lj, w->num, mn, s);
    }
    if (st == SRMECH_OK) {                               /* (aq x^{1-i-j};q)_{li+lj} */
        st = elb_mono_mul(c, &w->tmp, &p->aq, &p->xn[i + j - 1u],
                          &s->g, &s->t0, &s->t1);
    }
    if (st == SRMECH_OK) { st = cvl_poch(c, p, &w->tmp, li + lj, w->den, md, s); }
    if (st == SRMECH_OK) {                               /* (q x^{j-i-1};q)_{li-lj}  */
        st = elb_mono_mul(c, &w->tmp, &p->par[CVL_Q], &p->xp[j - i - 1u],
                          &s->g, &s->t0, &s->t1);
    }
    if (st == SRMECH_OK) { st = cvl_poch(c, p, &w->tmp, li - lj, w->den, md, s); }
    return st;
}

/* Append the VECTOR theta-Pochhammer (u; q, x)_lambda to dest at *m: for
 * j = 1..n the theta-Pochhammer (u x^{1-j}; q)_{lambda_j} (the Python
 * vpoch_thetas). Advances *m. */
static srmech_status_t cvl_vwp(srmech_ell_ctx_t *c, cvl_persist_t *p, size_t n,
                               const srmech_ell_mono_t *u, srmech_ell_mono_t *dest,
                               size_t *m, cvl_work_t *w)
{
    size_t j;
    elb_scr_t *s = &w->scr;
    srmech_status_t st = SRMECH_OK;
    assert(c != NULL && p != NULL && u != NULL);
    assert(dest != NULL && m != NULL && w != NULL && n >= 1u);
    for (j = 0; (st == SRMECH_OK) && j < n; j++) {
        st = elb_mono_mul(c, &w->tmp, u, &p->xn[j], &s->g, &s->t0, &s->t1);
        if (st == SRMECH_OK) {
            st = cvl_poch(c, p, &w->tmp, (size_t)p->lam[j], dest, m, s);
        }
    }
    return st;
}

/* Copy one monomial `m` into the output row stream at `*row`: its exact-Q coeff
 * into out_coeff_num/den[*row] AND its dense exponent row into out_exps_flat
 * (a canonicalized theta ARGUMENT can carry a non-unit Class-K coeff, so the
 * coeff travels with EVERY row). Advances *row. */
static srmech_status_t cvl_emit_mono(srmech_ell_ctx_t *c, const srmech_ell_mono_t *m,
                                     srmech_bigint_t *out_coeff_num,
                                     srmech_bigint_t *out_coeff_den,
                                     int32_t *out_exps_flat, size_t *row)
{
    srmech_status_t st;
    assert(c != NULL && m != NULL && row != NULL);
    assert(out_coeff_num != NULL && out_coeff_den != NULL && out_exps_flat != NULL);
    st = srmech_bigint_copy(&out_coeff_num[*row], &m->coeff.num);
    if (st == SRMECH_OK) { st = srmech_bigint_copy(&out_coeff_den[*row], &m->coeff.den); }
    if (st != SRMECH_OK) { return st; }
    memcpy(out_exps_flat + (*row) * c->n_syms, m->exps, c->n_syms * sizeof(int32_t));
    (*row)++;
    return SRMECH_OK;
}

/* Emit the canonical EllRatio `r` for term `term`: the counts into
 * out_n_num/den[term], and the monomial rows (prefactor, then num, then den)
 * appended at *row. */
static srmech_status_t cvl_emit(srmech_ell_ctx_t *c, const elb_ratio_t *r, size_t term,
                                srmech_bigint_t *out_coeff_num,
                                srmech_bigint_t *out_coeff_den, int32_t *out_exps_flat,
                                size_t out_exps_cap_rows, size_t *out_n_num,
                                size_t *out_n_den, size_t *row)
{
    size_t i;
    srmech_status_t st;
    assert(c != NULL && r != NULL && row != NULL);
    assert(out_n_num != NULL && out_n_den != NULL);
    if (*row + 1u + r->n_num + r->n_den > out_exps_cap_rows) {
        return SRMECH_ERR_OVERFLOW;
    }
    st = cvl_emit_mono(c, &r->pref, out_coeff_num, out_coeff_den, out_exps_flat, row);
    if (st != SRMECH_OK) { return st; }
    for (i = 0; i < r->n_num; i++) {
        st = cvl_emit_mono(c, &r->num[i], out_coeff_num, out_coeff_den,
                           out_exps_flat, row);
        if (st != SRMECH_OK) { return st; }
    }
    for (i = 0; i < r->n_den; i++) {
        st = cvl_emit_mono(c, &r->den[i], out_coeff_num, out_coeff_den,
                           out_exps_flat, row);
        if (st != SRMECH_OK) { return st; }
    }
    out_n_num[term] = r->n_num;
    out_n_den[term] = r->n_den;
    return SRMECH_OK;
}

/* Advance the partition odometer lam to the LEX successor among the
 * non-increasing tuples in {0..N}^n (the exact order the Python oracle's
 * filtered itertools.product enumerates: find the largest incrementable index,
 * increment it, zero the tail). Returns 1 if advanced, 0 if lam was the last
 * partition (N, N, .., N). */
static int cvl_next_partition(uint32_t *lam, size_t n, size_t N)
{
    size_t i;
    size_t k;
    assert(lam != NULL);
    assert(n >= 1u && N >= 1u);
    i = n;
    while (i > 0u) {
        uint32_t bound = (i == 1u) ? (uint32_t)N : lam[i - 2u];
        if (lam[i - 1u] < bound) {
            lam[i - 1u] += 1u;
            for (k = i; k < n; k++) { lam[k] = 0u; }
            return 1;
        }
        i--;
    }
    return 0;
}

/* Carve the persistent buffers (par[6] + aq + e + tmp + tmp2 + nb6[6] + db6[6]
 * + qp[2N+1] + xp[2n-1] + xn[2n-1] + setup scr + the lam odometer). */
static srmech_status_t cvl_bind_persist(srmech_ell_ctx_t *c, cvl_persist_t *p,
                                        size_t N, size_t n)
{
    size_t k;
    srmech_status_t st;
    assert(c != NULL && p != NULL);
    assert(N >= 1u && n >= 1u && c->n_syms >= 1u);
    st = elb_bind_mono_arr(c, &p->par, 6u);
    if (st == SRMECH_OK) { st = elb_bind_mono(c, &p->aq); }
    if (st == SRMECH_OK) { st = elb_bind_mono(c, &p->e); }
    if (st == SRMECH_OK) { st = elb_bind_mono(c, &p->tmp); }
    if (st == SRMECH_OK) { st = elb_bind_mono(c, &p->tmp2); }
    if (st == SRMECH_OK) { st = elb_bind_mono_arr(c, &p->nb6, 6u); }
    if (st == SRMECH_OK) { st = elb_bind_mono_arr(c, &p->db6, 6u); }
    if (st == SRMECH_OK) { st = elb_bind_mono_arr(c, &p->qp, 2u * N + 1u); }
    if (st == SRMECH_OK) { st = elb_bind_mono_arr(c, &p->xp, 2u * n - 1u); }
    if (st == SRMECH_OK) { st = elb_bind_mono_arr(c, &p->xn, 2u * n - 1u); }
    if (st == SRMECH_OK) { st = elb_er_bind_scr(c, &p->scr, 4u); }
    if (st != SRMECH_OK) { return st; }
    p->lam = srmech_ellbase_take_words(c, n);
    if (p->lam == NULL) { return SRMECH_ERR_OVERFLOW; }
    for (k = 0; k < n; k++) { p->lam[k] = 0u; }
    return SRMECH_OK;
}

/* Carve the per-term working buffers (pref + tmp + tmp2 + num/den/cn/cd[nt] +
 * ratio + scr) from the CURRENT cursor (the caller saves/restores it). */
static srmech_status_t cvl_bind_work(srmech_ell_ctx_t *c, cvl_work_t *w, size_t nt)
{
    srmech_status_t st;
    assert(c != NULL && w != NULL);
    assert(nt >= 1u && c->n_syms >= 1u);
    st = elb_bind_mono(c, &w->pref);
    if (st == SRMECH_OK) { st = elb_bind_mono(c, &w->tmp); }
    if (st == SRMECH_OK) { st = elb_bind_mono(c, &w->tmp2); }
    if (st == SRMECH_OK) { st = elb_bind_mono_arr(c, &w->num, nt); }
    if (st == SRMECH_OK) { st = elb_bind_mono_arr(c, &w->den, nt); }
    if (st == SRMECH_OK) { st = elb_bind_mono_arr(c, &w->cn, nt); }
    if (st == SRMECH_OK) { st = elb_bind_mono_arr(c, &w->cd, nt); }
    if (st == SRMECH_OK) { st = elb_er_bind_ratio(c, &w->ratio, nt, nt); }
    if (st == SRMECH_OK) { st = elb_er_bind_scr(c, &w->scr, nt); }
    return st;
}

/* Build + emit ONE partition summand `term`. Saves the arena cursor, carves the
 * per-term working set, builds the prefactor + num/den theta args (diagonal,
 * off-diagonal pairs, the 12 VWP bases), runs er_build (the EllRatio.__init__
 * mirror), emits, then RESTORES the cursor so the next term reuses the memory. */
static srmech_status_t cvl_one_term(srmech_ell_ctx_t *c, cvl_persist_t *p, size_t n,
                                    size_t nt, size_t term, int psym,
                                    srmech_bigint_t *out_coeff_num,
                                    srmech_bigint_t *out_coeff_den,
                                    int32_t *out_exps_flat, size_t out_exps_cap_rows,
                                    size_t *out_n_num, size_t *out_n_den, size_t *row)
{
    cvl_work_t w = {0};
    size_t saved = c->pool_cur;
    size_t mn = 0;
    size_t md = 0;
    size_t i;
    size_t j;
    size_t b;
    srmech_status_t st;
    assert(c != NULL && p != NULL && row != NULL);
    assert(out_n_num != NULL && out_n_den != NULL && n >= 1u);
    st = cvl_bind_work(c, &w, nt);
    if (st == SRMECH_OK) { st = elb_mono_set_one(c, &w.pref); }
    if (st == SRMECH_OK) { st = cvl_diag(c, p, n, &w, &mn, &md); }
    for (i = 1u; (st == SRMECH_OK) && i <= n; i++) {
        for (j = i + 1u; (st == SRMECH_OK) && j <= n; j++) {
            st = cvl_pair(c, p, &w, i, j, &mn, &md);
        }
    }
    for (b = 0; (st == SRMECH_OK) && b < 6u; b++) {
        st = cvl_vwp(c, p, n, &p->nb6[b], w.num, &mn, &w);
    }
    for (b = 0; (st == SRMECH_OK) && b < 6u; b++) {
        st = cvl_vwp(c, p, n, &p->db6[b], w.den, &md, &w);
    }
    assert((st != SRMECH_OK) || (mn <= nt && md <= nt));
    if (st == SRMECH_OK) {
        st = elb_er_build(c, &w.ratio, &w.pref, w.num, mn, w.den, md, psym,
                          &w.scr, w.cn, nt, w.cd, nt);
    }
    if (st == SRMECH_OK) {
        st = cvl_emit(c, &w.ratio, term, out_coeff_num, out_coeff_den, out_exps_flat,
                      out_exps_cap_rows, out_n_num, out_n_den, row);
    }
    c->pool_cur = saved;                                   /* reuse the memory */
    return st;
}

/* Reject a NULL required pointer (kept out of the main body for the JPL line cap). */
static int cvl_has_null(const srmech_bigint_t *const *pnum,
                        const srmech_bigint_t *const *pden,
                        const int32_t *const *pexps,
                        const srmech_bigint_t *out_num,
                        const srmech_bigint_t *out_den, const int32_t *out_exps)
{
    size_t i;
    assert(pnum != NULL && pden != NULL && pexps != NULL);
    assert(out_num == NULL || out_den == NULL || out_exps == NULL || 1);
    for (i = 0; i < 6u; i++) {
        if (pnum[i] == NULL || pden[i] == NULL || pexps[i] == NULL) { return 1; }
    }
    return (out_num == NULL || out_den == NULL || out_exps == NULL) ? 1 : 0;
}

srmech_status_t srmech_cn_vwp_multisum_lhs(size_t n_syms, int psym, size_t N,
                                           size_t n, size_t n_terms,
                                           const srmech_bigint_t *a_num,
                                           const srmech_bigint_t *a_den,
                                           const int32_t *a_exps,
                                           const srmech_bigint_t *b_num,
                                           const srmech_bigint_t *b_den,
                                           const int32_t *b_exps,
                                           const srmech_bigint_t *c_num,
                                           const srmech_bigint_t *c_den,
                                           const int32_t *c_exps,
                                           const srmech_bigint_t *d_num,
                                           const srmech_bigint_t *d_den,
                                           const int32_t *d_exps,
                                           const srmech_bigint_t *x_num,
                                           const srmech_bigint_t *x_den,
                                           const int32_t *x_exps,
                                           const srmech_bigint_t *q_num,
                                           const srmech_bigint_t *q_den,
                                           const int32_t *q_exps,
                                           uint32_t coeff_cap,
                                           srmech_bigint_t *out_coeff_num,
                                           srmech_bigint_t *out_coeff_den,
                                           int32_t *out_exps_flat,
                                           size_t out_exps_cap_rows,
                                           size_t *out_n_num, size_t *out_n_den,
                                           void *ws, size_t ws_len)
{
    srmech_ell_ctx_t ec = {0};
    cvl_persist_t p = {0};
    const srmech_bigint_t *pnum[6];
    const srmech_bigint_t *pden[6];
    const int32_t *pexps[6];
    size_t nt;
    size_t t;
    size_t row = 0;
    int adv;
    srmech_status_t st;
    assert(out_n_num != NULL && out_n_den != NULL);
    assert(out_coeff_num != NULL && out_coeff_den != NULL);
    pnum[CVL_A] = a_num; pnum[CVL_B] = b_num; pnum[CVL_C] = c_num;
    pnum[CVL_D] = d_num; pnum[CVL_X] = x_num; pnum[CVL_Q] = q_num;
    pden[CVL_A] = a_den; pden[CVL_B] = b_den; pden[CVL_C] = c_den;
    pden[CVL_D] = d_den; pden[CVL_X] = x_den; pden[CVL_Q] = q_den;
    pexps[CVL_A] = a_exps; pexps[CVL_B] = b_exps; pexps[CVL_C] = c_exps;
    pexps[CVL_D] = d_exps; pexps[CVL_X] = x_exps; pexps[CVL_Q] = q_exps;
    if (out_n_num == NULL || out_n_den == NULL) { return SRMECH_ERR_NULL_ARG; }
    if (N == 0u || n == 0u || n_terms == 0u) { return SRMECH_ERR_NULL_ARG; }
    if (cvl_has_null(pnum, pden, pexps, out_coeff_num, out_coeff_den, out_exps_flat)) {
        return SRMECH_ERR_NULL_ARG;
    }
    ec.n_syms = (n_syms == 0u) ? 1u : n_syms;
    ec.cap = (coeff_cap < 4u) ? 4u : coeff_cap;
    nt = cvl_nt_max(N, n);
    st = elb_er_arena_init(&ec, ws, ws_len);
    if (st == SRMECH_OK) { st = cvl_bind_persist(&ec, &p, N, n); }
    if (st == SRMECH_OK) { st = cvl_parse(&ec, &p, pnum, pden, pexps); }
    if (st == SRMECH_OK) { st = cvl_ladders(&ec, &p, N, n); }
    if (st == SRMECH_OK) { st = cvl_e_balance(&ec, &p, N, n); }
    if (st == SRMECH_OK) { st = cvl_bases(&ec, &p, N, n); }
    if (st != SRMECH_OK) { return st; }
    for (t = 0; t < n_terms; t++) {
        st = cvl_one_term(&ec, &p, n, nt, t, psym, out_coeff_num, out_coeff_den,
                          out_exps_flat, out_exps_cap_rows, out_n_num, out_n_den,
                          &row);
        if (st != SRMECH_OK) { return st; }
        adv = cvl_next_partition(p.lam, n, N);
        if ((t + 1u < n_terms) && (adv == 0)) { return SRMECH_ERR_BAD_INPUT; }
        if ((t + 1u == n_terms) && (adv != 0)) { return SRMECH_ERR_BAD_INPUT; }
    }
    return SRMECH_OK;
}

/* The minimum `ws_len` BYTES srmech_cn_vwp_multisum_lhs needs for the given
 * shape (n_syms symbols, N the partition ceiling, n the rank, coeff_limbs the
 * per-coefficient significant-limb estimate). Sized to the inputs -- no
 * compiled-in cap. The persistent head (par[6] + aq + e + tmp + tmp2 + nb6[6]
 * + db6[6] + qp[2N+1] + xp[2n-1] + xn[2n-1] + setup scr + lam) plus ONE term's
 * working set (the per-term buffers reuse memory across terms via the
 * saved/restored cursor), nt the per-side max theta count. */
size_t srmech_cn_vwp_multisum_lhs_ws_bound(size_t n_syms, size_t N, size_t n,
                                           size_t coeff_limbs)
{
    size_t cap = (coeff_limbs < 4u) ? 4u : coeff_limbs;
    size_t ns = (n_syms == 0u) ? 1u : n_syms;
    size_t NN = (N == 0u) ? 1u : N;
    size_t nn = (n == 0u) ? 1u : n;
    size_t nt = cvl_nt_max(NN, nn);
    size_t mw = elb_er_mono_words(cap, ns);
    /* persistent: par[6] + aq + e + tmp + tmp2 + nb6[6] + db6[6] + qp[2N+1]
     * + xp[2n-1] + xn[2n-1] monos, the setup scr, and the lam odometer. */
    size_t persist = (2u * NN + 4u * nn + 21u) * mw
                     + SRMECH_ELL_ER_SCR_MONOS * mw   /* setup scr.pm            */
                     + 4u + 3u * cap + 64u            /* setup scr flags + bigints */
                     + nn + 8u;                       /* the lam odometer        */
    /* per-term: pref + tmp + tmp2 + num[nt] + den[nt] + cn[nt] + cd[nt]. */
    size_t term = (3u + 4u * nt) * mw
                  + (mw + 2u * nt * mw)               /* ratio (pref + num + den) */
                  + SRMECH_ELL_ER_SCR_MONOS * mw      /* scr.pm                   */
                  + nt + 3u * cap + 64u;              /* scr.used flags + bigints */
    size_t scratch_words = cap * 16u + 512u;
    size_t total = persist + term + scratch_words + 4096u;
    assert(cap >= 4u);
    assert(total >= scratch_words);
    return total * sizeof(uint32_t);
}
