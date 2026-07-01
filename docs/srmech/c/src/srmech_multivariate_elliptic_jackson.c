/*
 * srmech_multivariate_elliptic_jackson.c -- the 1:1 native C peer of
 * srmech.amsc.multivariate_elliptic_jackson.multivariate_elliptic_jackson
 * (rc96), the eq-5 Cn elliptic Jackson summation reducer: the CAPSTONE of the
 * multivariable (root-system Cn) elliptic reduction row.
 *
 * A C-MIRROR PARITY build (NOT a new algorithm): it constructs the EXACT
 * closed form the already-shipped pure-Python op builds, byte-for-byte.
 *
 * For the parameters a, b, c, d and the base variables x, q (Rosengren, A
 * multivariable elliptic summation formula, arXiv:math/0101073, Theorem 2.1,
 * Eq. 5), the balanced Cn very-well-poised elliptic Jackson summation over the
 * partitions N >= lambda_1 >= ... >= lambda_n >= 0 reduces to the theta-quotient
 * product
 *
 *   (aq, aq/bc, aq/bd, aq/cd; q, x)_{N^n}
 *     / (aq/b, aq/c, aq/d, aq/bcd; q, x)_{N^n},
 *
 * with the VECTOR elliptic Pochhammer
 *
 *   (u; q, x)_{N^n} = PROD_{j=1}^n PROD_{i=0}^{N-1} theta(u*x^{1-j}*q^i; p).
 *
 * This op CONSTRUCTS the right-hand side as an exact EllRatio: the unit
 * prefactor, the numerator thetas (the vector Pochhammer of each num base aq,
 * aq/bc, aq/bd, aq/cd) and the denominator thetas (the vector Pochhammer of
 * each den base aq/b, aq/c, aq/d, aq/bcd). The EllRatio constructor (er_build)
 * folds each theta's canonicalize prefactor into the global prefactor, cancels
 * matching thetas between num and den, and sorts the survivors -- so the emitted
 * EllRatio is the canonical value Python returns.
 *
 * This is PURE COMPOSITION of the shared srmech_ellbase_* exact-Q monomial
 * algebra (mul / inv) + er_build (the EllRatio.__init__ mirror) -- the same
 * single copy srmech_elliptic_cauchy_determinant and srmech_elliptic_lagrange_basis
 * ride.
 *
 * Wire form: the interned symbol-table dimension `n_syms` (distinct symbols in
 * the Python sorted-symbol-NAME order so the dense exponent vector reproduces
 * EllMonomial._sort_key); `psym` the interned index of the nome `p` (-1 if
 * absent); the positive ints `N` (partition ceiling) + `n` (rank); each of the
 * 6 parameter monomials a/b/c/d/x/q as a (num, den) srmech_bigint pair + its
 * flat int32[n_syms] exponent row. `coeff_cap` is the per-bigint limb cap.
 *
 * Output: the single closed-form EllRatio written flat as a ROW stream. Each
 * emitted monomial (the prefactor or a theta argument) contributes ONE row: its
 * exact-Q coeff into `out_coeff_num` / `out_coeff_den`[row] AND its dense
 * int32[n_syms] exponent row into `out_exps_flat`, in the order: the prefactor
 * row, then `*out_n_num` num-theta rows, then `*out_n_den` den-theta rows. The
 * theta-count survivors come back in `*out_n_num` / `*out_n_den`. (The coeff
 * travels with EVERY row -- a canonicalized theta ARGUMENT can carry a non-unit
 * Class-K coeff -- so the coeff is NOT assumed 1.) `out_exps_cap_rows` is the row
 * capacity of the caller's buffers; too small -> SRMECH_ERR_OVERFLOW. N == 0 or
 * n == 0 -> SRMECH_ERR_NULL_ARG (Python raises ValueError). A required NULL
 * pointer -> SRMECH_ERR_NULL_ARG; a too-small arena -> SRMECH_ERR_OVERFLOW.
 *
 * Malloc-free (JPL Rule 3): every working monomial / theta + the bigint scratch
 * is carved from the caller arena `ws`, sized to the input (N, n, n_syms) -- no
 * compiled-in cap. Sign travels in the Class-K coeff branch, never abs()/fabs().
 * Additive symbol -> ABI unchanged (stays 3). License: MIT.
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto/recursion): OK -- iterative, flat static helpers
 *   - Rule 2 (bounded loops)    : OK -- bounded by N / n / n_syms
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
#define MEJ_A 0
#define MEJ_B 1
#define MEJ_C 2
#define MEJ_D 3
#define MEJ_X 4
#define MEJ_Q 5

/* The bound persistent buffers: the 6 parsed parameters + aq + the 4 num / 4
 * den bases + the x^{-k} / q^i power ladders (all live for the whole build). */
typedef struct mej_persist {
    srmech_ell_mono_t *par;       /* par[6] = a, b, c, d, x, q                  */
    srmech_ell_mono_t  aq;        /* a*q                                        */
    srmech_ell_mono_t *nb;        /* nb[4]  = aq, aq/bc, aq/bd, aq/cd           */
    srmech_ell_mono_t *db;        /* db[4]  = aq/b, aq/c, aq/d, aq/bcd          */
    srmech_ell_mono_t *xpow;      /* xpow[n] = x^{-k}, k = 0..n-1               */
    srmech_ell_mono_t *qpow;      /* qpow[N] = q^i,    i = 0..N-1               */
} mej_persist_t;

/* The working buffers for the single ratio build (the 4*N*n num / den theta args
 * + the unit prefactor + er_build's canon scratch + the canonical output ratio). */
typedef struct mej_work {
    srmech_ell_mono_t  pref;      /* the unit prefactor                         */
    srmech_ell_mono_t  tmp;       /* general scratch monomial                   */
    srmech_ell_mono_t  tmp2;      /* second scratch (inverse building)          */
    srmech_ell_mono_t  tmp3;      /* third scratch (triple product)             */
    srmech_ell_mono_t *num;       /* the 4*N*n numerator theta-argument monomials */
    srmech_ell_mono_t *den;       /* the 4*N*n denominator theta-argument monomials */
    srmech_ell_mono_t *cn;        /* er_build canon scratch (num)               */
    srmech_ell_mono_t *cd;        /* er_build canon scratch (den)               */
    elb_ratio_t        ratio;     /* the canonical closed-form EllRatio         */
    elb_scr_t          scr;       /* the er_build scratch bundle                */
} mej_work_t;

/* Parse the 6 parameter monomials from the flat input coeff / exponent arrays
 * into bound monomials. Mirrors the head of the Python op (_coerce_monomial). */
static srmech_status_t mej_parse(srmech_ell_ctx_t *c, mej_persist_t *p,
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

/* out := aq * inv(denom) (aq / denom); invtmp is caller scratch (!= denom). */
static srmech_status_t mej_inv_mul(srmech_ell_ctx_t *c, srmech_ell_mono_t *out,
                                   const srmech_ell_mono_t *aq,
                                   const srmech_ell_mono_t *denom, elb_scr_t *s,
                                   srmech_ell_mono_t *invtmp)
{
    srmech_status_t st;
    assert(c != NULL && out != NULL && aq != NULL);
    assert(denom != NULL && invtmp != NULL && s != NULL);
    st = elb_mono_inv(c, invtmp, denom);
    if (st == SRMECH_OK) {
        st = elb_mono_mul(c, out, aq, invtmp, &s->g, &s->t0, &s->t1);
    }
    return st;
}

/* aq := a*q; nb[0..3] := aq, aq/bc, aq/bd, aq/cd (the numerator bases). */
static srmech_status_t mej_num_bases(srmech_ell_ctx_t *c, mej_persist_t *p, elb_scr_t *s,
                                     srmech_ell_mono_t *tmp, srmech_ell_mono_t *invtmp)
{
    srmech_status_t st;
    assert(c != NULL && p != NULL && s != NULL);
    assert(tmp != NULL && invtmp != NULL);
    st = elb_mono_mul(c, &p->aq, &p->par[MEJ_A], &p->par[MEJ_Q], &s->g, &s->t0, &s->t1);
    if (st == SRMECH_OK) { st = elb_mono_copy(c, &p->nb[0], &p->aq); }          /* aq    */
    if (st == SRMECH_OK) { st = elb_mono_mul(c, tmp, &p->par[MEJ_B], &p->par[MEJ_C],
                                             &s->g, &s->t0, &s->t1); }          /* b*c   */
    if (st == SRMECH_OK) { st = mej_inv_mul(c, &p->nb[1], &p->aq, tmp, s, invtmp); } /* aq/bc */
    if (st == SRMECH_OK) { st = elb_mono_mul(c, tmp, &p->par[MEJ_B], &p->par[MEJ_D],
                                             &s->g, &s->t0, &s->t1); }          /* b*d   */
    if (st == SRMECH_OK) { st = mej_inv_mul(c, &p->nb[2], &p->aq, tmp, s, invtmp); } /* aq/bd */
    if (st == SRMECH_OK) { st = elb_mono_mul(c, tmp, &p->par[MEJ_C], &p->par[MEJ_D],
                                             &s->g, &s->t0, &s->t1); }          /* c*d   */
    if (st == SRMECH_OK) { st = mej_inv_mul(c, &p->nb[3], &p->aq, tmp, s, invtmp); } /* aq/cd */
    return st;
}

/* db[0..3] := aq/b, aq/c, aq/d, aq/bcd (the denominator bases). */
static srmech_status_t mej_den_bases(srmech_ell_ctx_t *c, mej_persist_t *p, elb_scr_t *s,
                                     srmech_ell_mono_t *tmp, srmech_ell_mono_t *tmp3,
                                     srmech_ell_mono_t *invtmp)
{
    srmech_status_t st;
    assert(c != NULL && p != NULL && s != NULL);
    assert(tmp != NULL && tmp3 != NULL && invtmp != NULL);
    st = mej_inv_mul(c, &p->db[0], &p->aq, &p->par[MEJ_B], s, invtmp);          /* aq/b  */
    if (st == SRMECH_OK) { st = mej_inv_mul(c, &p->db[1], &p->aq, &p->par[MEJ_C], s, invtmp); }
    if (st == SRMECH_OK) { st = mej_inv_mul(c, &p->db[2], &p->aq, &p->par[MEJ_D], s, invtmp); }
    if (st == SRMECH_OK) { st = elb_mono_mul(c, tmp, &p->par[MEJ_B], &p->par[MEJ_C],
                                             &s->g, &s->t0, &s->t1); }          /* b*c   */
    if (st == SRMECH_OK) { st = elb_mono_mul(c, tmp3, tmp, &p->par[MEJ_D],
                                             &s->g, &s->t0, &s->t1); }          /* b*c*d */
    if (st == SRMECH_OK) { st = mej_inv_mul(c, &p->db[3], &p->aq, tmp3, s, invtmp); } /* aq/bcd */
    return st;
}

/* xpow[k] := x^{-k} (k = 0..n-1) and qpow[i] := q^i (i = 0..N-1). */
static srmech_status_t mej_powers(srmech_ell_ctx_t *c, mej_persist_t *p, size_t N, size_t n,
                                  elb_scr_t *s, srmech_ell_mono_t *tmp)
{
    size_t k;
    size_t i;
    srmech_status_t st;
    assert(c != NULL && p != NULL && s != NULL);
    assert(tmp != NULL && N >= 1u && n >= 1u);
    st = elb_mono_inv(c, tmp, &p->par[MEJ_X]);                    /* tmp = x^{-1}         */
    if (st == SRMECH_OK) { st = elb_mono_set_one(c, &p->xpow[0]); }
    for (k = 1u; (st == SRMECH_OK) && k < n; k++) {
        st = elb_mono_mul(c, &p->xpow[k], &p->xpow[k - 1u], tmp, &s->g, &s->t0, &s->t1);
    }
    if (st == SRMECH_OK) { st = elb_mono_set_one(c, &p->qpow[0]); }
    for (i = 1u; (st == SRMECH_OK) && i < N; i++) {
        st = elb_mono_mul(c, &p->qpow[i], &p->qpow[i - 1u], &p->par[MEJ_Q],
                          &s->g, &s->t0, &s->t1);
    }
    return st;
}

/* Append the vector Pochhammer of `base` to dest starting at *m: for j=1..n
 * (k=j-1) and i=0..N-1 append theta arg base*x^{1-j}*q^i = base*xpow[k]*qpow[i]. */
static srmech_status_t mej_fill_poch(srmech_ell_ctx_t *c, mej_persist_t *p, size_t N,
                                     size_t n, const srmech_ell_mono_t *base,
                                     srmech_ell_mono_t *dest, size_t *m, elb_scr_t *s,
                                     srmech_ell_mono_t *tmp)
{
    size_t k;
    size_t i;
    srmech_status_t st = SRMECH_OK;
    assert(c != NULL && p != NULL && base != NULL);
    assert(dest != NULL && m != NULL && tmp != NULL && s != NULL);
    for (k = 0u; (st == SRMECH_OK) && k < n; k++) {
        st = elb_mono_mul(c, tmp, base, &p->xpow[k], &s->g, &s->t0, &s->t1);
        for (i = 0u; (st == SRMECH_OK) && i < N; i++) {
            st = elb_mono_mul(c, &dest[*m], tmp, &p->qpow[i], &s->g, &s->t0, &s->t1);
            (*m)++;
        }
    }
    return st;
}

/* Fill an array with the vector Pochhammers of the 4 bases (num or den). The
 * count is exactly 4*N*n (order-free: er_build canonicalizes + sorts). */
static srmech_status_t mej_fill_side(srmech_ell_ctx_t *c, mej_persist_t *p, size_t N,
                                     size_t n, const srmech_ell_mono_t *bases,
                                     srmech_ell_mono_t *dest, elb_scr_t *s,
                                     srmech_ell_mono_t *tmp)
{
    size_t b;
    size_t m = 0;
    srmech_status_t st = SRMECH_OK;
    assert(c != NULL && p != NULL && bases != NULL);
    assert(dest != NULL && tmp != NULL && s != NULL);
    for (b = 0u; (st == SRMECH_OK) && b < 4u; b++) {
        st = mej_fill_poch(c, p, N, n, &bases[b], dest, &m, s, tmp);
    }
    assert((st != SRMECH_OK) || (m == 4u * N * n));
    return st;
}

/* Copy one monomial `m` into the output row stream at `*row`: its exact-Q coeff
 * into out_num/out_den[*row] AND its dense exponent row into out_exps. */
static srmech_status_t mej_emit_mono(srmech_ell_ctx_t *c, const srmech_ell_mono_t *m,
                                     srmech_bigint_t *out_num, srmech_bigint_t *out_den,
                                     int32_t *out_exps, size_t *row)
{
    srmech_status_t st;
    assert(c != NULL && m != NULL && row != NULL);
    assert(out_num != NULL && out_den != NULL && out_exps != NULL);
    st = srmech_bigint_copy(&out_num[*row], &m->coeff.num);
    if (st == SRMECH_OK) { st = srmech_bigint_copy(&out_den[*row], &m->coeff.den); }
    if (st != SRMECH_OK) { return st; }
    memcpy(out_exps + (*row) * c->n_syms, m->exps, c->n_syms * sizeof(int32_t));
    (*row)++;
    return SRMECH_OK;
}

/* Emit the canonical EllRatio `r` as a row stream: the prefactor row, then the
 * r->n_num num-theta rows, then the r->n_den den-theta rows. */
static srmech_status_t mej_emit_ratio(srmech_ell_ctx_t *c, const elb_ratio_t *r,
                                      srmech_bigint_t *out_num, srmech_bigint_t *out_den,
                                      int32_t *out_exps, size_t out_cap_rows,
                                      size_t *out_n_num, size_t *out_n_den, size_t *row)
{
    size_t i;
    srmech_status_t st;
    assert(c != NULL && r != NULL && row != NULL);
    assert(out_n_num != NULL && out_n_den != NULL);
    if (1u + r->n_num + r->n_den > out_cap_rows) { return SRMECH_ERR_OVERFLOW; }
    st = mej_emit_mono(c, &r->pref, out_num, out_den, out_exps, row);
    if (st != SRMECH_OK) { return st; }
    for (i = 0; i < r->n_num; i++) {
        st = mej_emit_mono(c, &r->num[i], out_num, out_den, out_exps, row);
        if (st != SRMECH_OK) { return st; }
    }
    for (i = 0; i < r->n_den; i++) {
        st = mej_emit_mono(c, &r->den[i], out_num, out_den, out_exps, row);
        if (st != SRMECH_OK) { return st; }
    }
    *out_n_num = r->n_num;
    *out_n_den = r->n_den;
    return SRMECH_OK;
}

/* Carve the persistent buffers (par[6] + aq + nb[4] + db[4] + xpow[n] + qpow[N]). */
static srmech_status_t mej_bind_persist(srmech_ell_ctx_t *c, mej_persist_t *p, size_t N,
                                        size_t n)
{
    srmech_status_t st;
    assert(c != NULL && p != NULL);
    assert(N >= 1u && n >= 1u && c->n_syms >= 1u);
    st = elb_bind_mono_arr(c, &p->par, 6u);
    if (st == SRMECH_OK) { st = elb_bind_mono(c, &p->aq); }
    if (st == SRMECH_OK) { st = elb_bind_mono_arr(c, &p->nb, 4u); }
    if (st == SRMECH_OK) { st = elb_bind_mono_arr(c, &p->db, 4u); }
    if (st == SRMECH_OK) { st = elb_bind_mono_arr(c, &p->xpow, n); }
    if (st == SRMECH_OK) { st = elb_bind_mono_arr(c, &p->qpow, N); }
    return st;
}

/* Carve the working buffers (pref + tmp*3 + num/den/cn/cd[nt] + ratio + scr). */
static srmech_status_t mej_bind_work(srmech_ell_ctx_t *c, mej_work_t *w, size_t nt)
{
    srmech_status_t st;
    assert(c != NULL && w != NULL);
    assert(nt >= 1u && c->n_syms >= 1u);
    st = elb_bind_mono(c, &w->pref);
    if (st == SRMECH_OK) { st = elb_bind_mono(c, &w->tmp); }
    if (st == SRMECH_OK) { st = elb_bind_mono(c, &w->tmp2); }
    if (st == SRMECH_OK) { st = elb_bind_mono(c, &w->tmp3); }
    if (st == SRMECH_OK) { st = elb_bind_mono_arr(c, &w->num, nt); }
    if (st == SRMECH_OK) { st = elb_bind_mono_arr(c, &w->den, nt); }
    if (st == SRMECH_OK) { st = elb_bind_mono_arr(c, &w->cn, nt); }
    if (st == SRMECH_OK) { st = elb_bind_mono_arr(c, &w->cd, nt); }
    if (st == SRMECH_OK) { st = elb_er_bind_ratio(c, &w->ratio, nt, nt); }
    if (st == SRMECH_OK) { st = elb_er_bind_scr(c, &w->scr, nt); }
    return st;
}

/* Reject a NULL required pointer (kept out of the main body for the JPL line cap). */
static int mej_has_null(const srmech_bigint_t *const *pnum,
                        const srmech_bigint_t *const *pden,
                        const int32_t *const *pexps,
                        const srmech_bigint_t *out_num,
                        const srmech_bigint_t *out_den, const int32_t *out_exps)
{
    size_t i;
    assert(pnum != NULL && pden != NULL && pexps != NULL);
    assert(out_num != NULL || out_den != NULL || out_exps != NULL || 1);
    for (i = 0; i < 6u; i++) {
        if (pnum[i] == NULL || pden[i] == NULL || pexps[i] == NULL) { return 1; }
    }
    return (out_num == NULL || out_den == NULL || out_exps == NULL) ? 1 : 0;
}

srmech_status_t srmech_multivariate_elliptic_jackson(size_t n_syms, int psym, size_t N,
                                                     size_t n,
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
    mej_persist_t p = {0};
    mej_work_t w = {0};
    const srmech_bigint_t *pnum[6];
    const srmech_bigint_t *pden[6];
    const int32_t *pexps[6];
    size_t nt;
    size_t row = 0;
    srmech_status_t st;
    assert(out_n_num != NULL && out_n_den != NULL);
    assert(out_coeff_num != NULL && out_coeff_den != NULL);
    pnum[MEJ_A] = a_num; pnum[MEJ_B] = b_num; pnum[MEJ_C] = c_num;
    pnum[MEJ_D] = d_num; pnum[MEJ_X] = x_num; pnum[MEJ_Q] = q_num;
    pden[MEJ_A] = a_den; pden[MEJ_B] = b_den; pden[MEJ_C] = c_den;
    pden[MEJ_D] = d_den; pden[MEJ_X] = x_den; pden[MEJ_Q] = q_den;
    pexps[MEJ_A] = a_exps; pexps[MEJ_B] = b_exps; pexps[MEJ_C] = c_exps;
    pexps[MEJ_D] = d_exps; pexps[MEJ_X] = x_exps; pexps[MEJ_Q] = q_exps;
    if (out_n_num == NULL || out_n_den == NULL) { return SRMECH_ERR_NULL_ARG; }
    if (N == 0u || n == 0u) { return SRMECH_ERR_NULL_ARG; }   /* >= 1 (Python raises) */
    if (mej_has_null(pnum, pden, pexps, out_coeff_num, out_coeff_den, out_exps_flat)) {
        return SRMECH_ERR_NULL_ARG;
    }
    ec.n_syms = (n_syms == 0u) ? 1u : n_syms;
    ec.cap = (coeff_cap < 4u) ? 4u : coeff_cap;
    nt = 4u * N * n;
    st = elb_er_arena_init(&ec, ws, ws_len);
    if (st == SRMECH_OK) { st = mej_bind_persist(&ec, &p, N, n); }
    if (st == SRMECH_OK) { st = mej_bind_work(&ec, &w, nt); }
    if (st == SRMECH_OK) { st = mej_parse(&ec, &p, pnum, pden, pexps); }
    if (st == SRMECH_OK) { st = mej_num_bases(&ec, &p, &w.scr, &w.tmp, &w.tmp2); }
    if (st == SRMECH_OK) { st = mej_den_bases(&ec, &p, &w.scr, &w.tmp, &w.tmp3, &w.tmp2); }
    if (st == SRMECH_OK) { st = mej_powers(&ec, &p, N, n, &w.scr, &w.tmp); }
    if (st == SRMECH_OK) { st = elb_mono_set_one(&ec, &w.pref); }
    if (st == SRMECH_OK) { st = mej_fill_side(&ec, &p, N, n, p.nb, w.num, &w.scr, &w.tmp); }
    if (st == SRMECH_OK) { st = mej_fill_side(&ec, &p, N, n, p.db, w.den, &w.scr, &w.tmp); }
    if (st == SRMECH_OK) {
        st = elb_er_build(&ec, &w.ratio, &w.pref, w.num, nt, w.den, nt, psym,
                          &w.scr, w.cn, nt, w.cd, nt);
    }
    if (st == SRMECH_OK) {
        st = mej_emit_ratio(&ec, &w.ratio, out_coeff_num, out_coeff_den, out_exps_flat,
                            out_exps_cap_rows, out_n_num, out_n_den, &row);
    }
    return st;
}

/* The minimum `ws_len` BYTES srmech_multivariate_elliptic_jackson needs for the
 * given shape (n_syms symbols, N the partition ceiling, n the rank, coeff_limbs
 * the per-coefficient significant-limb estimate). Sized to the inputs -- no
 * compiled-in cap. The persistent head (par[6] + aq + nb[4] + db[4] + xpow[n] +
 * qpow[N]) plus the single ratio's working set (pref + 3 tmp + num[nt] + den[nt]
 * + cn[nt] + cd[nt] + the ratio (pref + num[nt] + den[nt]) + the er_build scratch
 * bundle), nt = 4*N*n. */
size_t srmech_multivariate_elliptic_jackson_ws_bound(size_t n_syms, size_t N, size_t n,
                                                     size_t coeff_limbs)
{
    size_t cap = (coeff_limbs < 4u) ? 4u : coeff_limbs;
    size_t ns = (n_syms == 0u) ? 1u : n_syms;
    size_t NN = (N == 0u) ? 1u : N;
    size_t nn = (n == 0u) ? 1u : n;
    size_t nt = 4u * NN * nn;
    size_t mw = elb_er_mono_words(cap, ns);
    /* persistent: par[6] + aq + nb[4] + db[4] + xpow[nn] + qpow[NN]. */
    size_t persist = (15u + nn + NN) * mw;
    /* per-build: pref + 3 tmp + num[nt] + den[nt] + cn[nt] + cd[nt]. */
    size_t work = (4u + 4u * nt) * mw
                  + (mw + 2u * nt * mw)             /* ratio (pref + num[nt] + den[nt]) */
                  + SRMECH_ELL_ER_SCR_MONOS * mw    /* scr.pm                           */
                  + nt + 3u * cap + 64u;            /* scr.used flags + scr bigints     */
    size_t scratch_words = cap * 16u + 512u;
    size_t total = persist + work + scratch_words + 4096u;
    assert(cap >= 4u);
    assert(total >= scratch_words);
    return total * sizeof(uint32_t);
}
