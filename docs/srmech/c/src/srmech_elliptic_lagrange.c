/*
 * srmech_elliptic_lagrange.c -- the 1:1 native C peer of
 * srmech.amsc.ellbase.elliptic_lagrange_basis (rc66, shipped Python-only;
 * its C mirror is owed by the everything-mirrors same-rc discipline -> rc67).
 *
 * A C-MIRROR PARITY build (NOT a new algorithm): it reproduces the EXISTING,
 * already-shipped pure-Python carrier byte-for-byte.
 *
 * elliptic_lagrange_basis(points, multiplier, var) returns the k = len(points)
 * elliptic Lagrange interpolation basis of the k-dimensional space
 *   V_t = { f analytic on C* : f(p*z) = t * z^{-k} * f(z) }
 * (Rosengren, Elliptic Hypergeometric Functions, arXiv:1608.06161v3, Sec.1.3
 * Corollary 1.3.5). For each i (0..k-1):
 *   others    = { points[j] : j != i }
 *   prod      = PROD others                                  (EllMonomial mul)
 *   v_i       = (-1)^k * multiplier * prod^{-1}              (the balancing point)
 *   L_i       = EllRatio( num = [ theta(z * u_j^{-1}) : j != i ]
 *                              + [ theta(z * v_i^{-1}) ] )   (z = symbol(var))
 * with the default unit prefactor; the EllRatio constructor (er_build) folds
 * each theta's canonicalize prefactor, cancels matching thetas between num and
 * den (here den is empty), and sorts the survivors -- so each L_i is the
 * canonical EllRatio Python returns.
 *
 * This is PURE COMPOSITION of the shared srmech_ellbase_* exact-Q monomial
 * algebra (mul / inv) + er_build (the EllRatio.__init__ mirror) -- the same
 * single copy srmech_ellratio_is_elliptic and srmech_elliptic_gosper ride.
 *
 * Wire form (mirrors srmech_ellratio_is_elliptic): the interned symbol-table
 * dimension `n_syms` (distinct symbols in the Python sorted-symbol-NAME order so
 * the dense exponent vector reproduces EllMonomial._sort_key); `varsym` / `psym`
 * the interned indices of the interpolation variable `var` and the nome `p`
 * (-1 if absent); `k` the node count; the flat point-monomial coeff arrays
 * `pt_coeff_num` / `pt_coeff_den` (point0..k-1) + the flat int32 exponent rows
 * `pt_exps_flat` (int32[n_syms] per point); the multiplier monomial
 * `mult_num` / `mult_den` / `mult_exps`. `coeff_cap` is the per-bigint limb cap.
 *
 * Output: the k basis EllRatios, written out flat -- per element i,
 * `out_pref_num[i]` / `out_pref_den[i]` the prefactor exact-Q coeff,
 * `out_n_num[i]` / `out_n_den[i]` the theta counts, and the canonical exponent
 * rows appended to `out_exps_flat` (per element: its prefactor row, then its
 * out_n_num[i] num rows, then its out_n_den[i] den rows; each int32[n_syms]).
 * `out_exps_cap_rows` is the row capacity of the caller's out_exps_flat buffer.
 *
 * Malloc-free (JPL Rule 3): every working monomial / theta + the bigint scratch
 * is carved from the caller arena `ws`, sized to the input (k, n_syms) -- no
 * compiled-in cap. The (-1)^k sign is a Class-K parity branch (an int +/-1),
 * never abs()/fabs(). Additive symbol -> ABI unchanged (stays 3). License: MIT.
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto/recursion): OK -- iterative, flat static helpers
 *   - Rule 2 (bounded loops)    : OK -- bounded by k / n_syms
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
#define elb_bind_bi        srmech_ellbase_bind_bi
#define elb_er_bind_scr    srmech_ellbase_er_bind_scr
#define elb_er_bind_ratio  srmech_ellbase_er_bind_ratio
#define elb_er_build       srmech_ellbase_er_build
#define elb_er_arena_init  srmech_ellbase_er_arena_init
#define elb_er_mono_words  srmech_ellbase_er_mono_words

typedef srmech_ell_er_scr_t   elb_scr_t;
typedef srmech_ell_er_ratio_t elb_ratio_t;

/* The bound persistent buffers: the parsed points + multiplier + the (-1)^k
 * sign monomial + the var-symbol monomial z (all live for every basis element). */
typedef struct elb_persist {
    srmech_ell_mono_t *pts;       /* k parsed point monomials                  */
    srmech_ell_mono_t  mult;      /* the parsed multiplier monomial            */
    srmech_ell_mono_t  signk;     /* (-1)^k as a scalar monomial               */
    srmech_ell_mono_t  z;         /* symbol(var): coeff 1, var-exponent 1      */
} elb_persist_t;

/* The per-element working buffers (carved fresh from a reset cursor each i). */
typedef struct elb_work {
    srmech_ell_mono_t  prod;      /* PROD others (j != i)                      */
    srmech_ell_mono_t  vi;        /* the balancing point v_i                   */
    srmech_ell_mono_t  tmp;       /* general scratch monomial                  */
    srmech_ell_mono_t  one;       /* the unit prefactor (pref0)                */
    srmech_ell_mono_t *args;      /* the k theta-argument monomials            */
    srmech_ell_mono_t *cn;        /* er_build canon scratch (num)              */
    srmech_ell_mono_t *cd;        /* er_build canon scratch (den; unused)      */
    elb_ratio_t        ratio;     /* the canonical basis EllRatio              */
    elb_scr_t          scr;       /* the er_build scratch bundle               */
} elb_work_t;

/* Parse the k flat point monomials + the multiplier into bound monomials, set the
 * (-1)^k sign monomial and the var-symbol monomial z. Mirrors the head of the
 * Python op (x = symbol(var); sign_k = scalar((-1)^k)). */
static srmech_status_t elb_parse(srmech_ell_ctx_t *c, elb_persist_t *p, size_t k,
                                 int varsym, const srmech_bigint_t *pt_num,
                                 const srmech_bigint_t *pt_den,
                                 const int32_t *pt_exps,
                                 const srmech_bigint_t *mult_num,
                                 const srmech_bigint_t *mult_den,
                                 const int32_t *mult_exps)
{
    size_t i;
    srmech_status_t st;
    assert(c != NULL && p != NULL);
    assert(pt_num != NULL && pt_den != NULL && pt_exps != NULL);
    for (i = 0; i < k; i++) {
        st = srmech_bigint_copy(&p->pts[i].coeff.num, &pt_num[i]);
        if (st == SRMECH_OK) { st = srmech_bigint_copy(&p->pts[i].coeff.den, &pt_den[i]); }
        if (st != SRMECH_OK) { return st; }
        memcpy(p->pts[i].exps, pt_exps + i * c->n_syms, c->n_syms * sizeof(int32_t));
    }
    st = srmech_bigint_copy(&p->mult.coeff.num, mult_num);
    if (st == SRMECH_OK) { st = srmech_bigint_copy(&p->mult.coeff.den, mult_den); }
    if (st != SRMECH_OK) { return st; }
    memcpy(p->mult.exps, mult_exps, c->n_syms * sizeof(int32_t));
    /* sign_k = (-1)^k : the Class-K parity branch (an int +/-1, never abs()). */
    st = elb_mono_set_one(c, &p->signk);
    if (st != SRMECH_OK) { return st; }
    if ((k & 1u) != 0u) { p->signk.coeff.num.sign = -p->signk.coeff.num.sign; }
    /* z = symbol(var) : coeff 1, var-exponent 1 (0 if var is absent from the table). */
    st = elb_mono_set_one(c, &p->z);
    if (st != SRMECH_OK) { return st; }
    if (varsym >= 0) { p->z.exps[varsym] = 1; }
    return SRMECH_OK;
}

/* Carve the persistent buffers from the (never-reset) arena head. */
static srmech_status_t elb_bind_persist(srmech_ell_ctx_t *c, elb_persist_t *p, size_t k)
{
    srmech_status_t st;
    assert(c != NULL && p != NULL && k >= 1u);
    assert(c->n_syms >= 1u && c->cap >= 1u);
    st = elb_bind_mono_arr(c, &p->pts, k);
    if (st == SRMECH_OK) { st = elb_bind_mono(c, &p->mult); }
    if (st == SRMECH_OK) { st = elb_bind_mono(c, &p->signk); }
    if (st == SRMECH_OK) { st = elb_bind_mono(c, &p->z); }
    return st;
}

/* Carve the per-element working buffers from the CURRENT cursor (the caller saved
 * the cursor first and restores it after the element, so these reuse memory). */
static srmech_status_t elb_bind_work(srmech_ell_ctx_t *c, elb_work_t *w, size_t k)
{
    srmech_status_t st;
    assert(c != NULL && w != NULL && k >= 1u);
    assert(c->n_syms >= 1u);
    st = elb_bind_mono(c, &w->prod);
    if (st == SRMECH_OK) { st = elb_bind_mono(c, &w->vi); }
    if (st == SRMECH_OK) { st = elb_bind_mono(c, &w->tmp); }
    if (st == SRMECH_OK) { st = elb_bind_mono(c, &w->one); }
    if (st == SRMECH_OK) { st = elb_bind_mono_arr(c, &w->args, k); }
    if (st == SRMECH_OK) { st = elb_bind_mono_arr(c, &w->cn, k); }
    if (st == SRMECH_OK) { st = elb_bind_mono_arr(c, &w->cd, 1u); }
    if (st == SRMECH_OK) { st = elb_er_bind_ratio(c, &w->ratio, k, 1u); }
    if (st == SRMECH_OK) { st = elb_er_bind_scr(c, &w->scr, k); }
    return st;
}

/* prod := PROD_{j != i} points[j] (the product of the OTHER nodes). Mirrors the
 * Python `prod_others` accumulation (start at one, mono_mul each other node). */
static srmech_status_t elb_prod_others(srmech_ell_ctx_t *c, elb_work_t *w,
                                       const elb_persist_t *p, size_t k, size_t i)
{
    size_t j;
    srmech_status_t st;
    assert(c != NULL && w != NULL && p != NULL);
    assert(i < k);
    st = elb_mono_set_one(c, &w->prod);
    if (st != SRMECH_OK) { return st; }
    for (j = 0; j < k; j++) {
        if (j == i) { continue; }
        st = elb_mono_mul(c, &w->tmp, &w->prod, &p->pts[j],
                          &w->scr.g, &w->scr.t0, &w->scr.t1);
        if (st != SRMECH_OK) { return st; }
        st = elb_mono_copy(c, &w->prod, &w->tmp);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* Build the k theta ARGUMENTS of L_i: for j != i, z * points[j]^{-1}; then the
 * balancing arg z * v_i^{-1}, where v_i = (-1)^k * multiplier * prod^{-1}.
 * Writes args[0..k-1]; *n_args == k. Mirrors the Python thetas list. */
static srmech_status_t elb_build_args(srmech_ell_ctx_t *c, elb_work_t *w,
                                      const elb_persist_t *p, size_t k, size_t i)
{
    size_t j;
    size_t n = 0;
    srmech_status_t st;
    assert(c != NULL && w != NULL && p != NULL);
    assert(i < k);
    for (j = 0; j < k; j++) {
        if (j == i) { continue; }
        st = elb_mono_inv(c, &w->tmp, &p->pts[j]);            /* u_j^{-1}        */
        if (st != SRMECH_OK) { return st; }
        st = elb_mono_mul(c, &w->args[n], &p->z, &w->tmp,     /* z * u_j^{-1}    */
                          &w->scr.g, &w->scr.t0, &w->scr.t1);
        if (st != SRMECH_OK) { return st; }
        n++;
    }
    /* v_i = (-1)^k * multiplier * prod^{-1} : (signk * mult) * prod^{-1}.        */
    st = elb_mono_mul(c, &w->tmp, &p->signk, &p->mult,
                      &w->scr.g, &w->scr.t0, &w->scr.t1);
    if (st != SRMECH_OK) { return st; }
    st = elb_mono_inv(c, &w->vi, &w->prod);                   /* prod^{-1}       */
    if (st != SRMECH_OK) { return st; }
    st = elb_mono_mul(c, &w->one, &w->tmp, &w->vi,            /* v_i (in `one`)  */
                      &w->scr.g, &w->scr.t0, &w->scr.t1);
    if (st != SRMECH_OK) { return st; }
    st = elb_mono_inv(c, &w->vi, &w->one);                   /* v_i^{-1}        */
    if (st != SRMECH_OK) { return st; }
    st = elb_mono_mul(c, &w->args[n], &p->z, &w->vi,         /* z * v_i^{-1}    */
                      &w->scr.g, &w->scr.t0, &w->scr.t1);
    if (st != SRMECH_OK) { return st; }
    n++;
    assert(n == k);
    return SRMECH_OK;
}

/* Copy one monomial `m` into the output row stream at `*row`: its exact-Q coeff into
 * out_coeff_num/den[*row] AND its dense exponent row into out_exps_flat. The theta
 * ARGUMENTS carry a non-unit Class-K coeff (e.g. the balancing arg z·v_i^{-1} with
 * v_i = (-1)^k·t/PROD others), so the coeff MUST travel with the exps row -- emitting
 * only the exps row (the gosper convention, where well-poised thetas are coeff 1) would
 * drop the sign. Advances *row. */
static srmech_status_t elb_emit_mono(srmech_ell_ctx_t *c, const srmech_ell_mono_t *m,
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

/* Emit the canonical EllRatio `r` for element `*elem`: the counts into
 * out_n_num/den[*elem], and the monomial rows (prefactor, then num0..n_num-1, then
 * den0..n_den-1) appended at *row -- each row carrying its exact-Q coeff (in
 * out_coeff_num/den) AND its exponent row (in out_exps_flat). */
static srmech_status_t elb_emit(srmech_ell_ctx_t *c, const elb_ratio_t *r, size_t elem,
                                srmech_bigint_t *out_coeff_num,
                                srmech_bigint_t *out_coeff_den, int32_t *out_exps_flat,
                                size_t out_exps_cap_rows, size_t *out_n_num,
                                size_t *out_n_den, size_t *row)
{
    size_t i;
    srmech_status_t st;
    assert(c != NULL && r != NULL && row != NULL);
    assert(out_coeff_num != NULL && out_coeff_den != NULL && out_exps_flat != NULL);
    if (*row + 1u + r->n_num + r->n_den > out_exps_cap_rows) {
        return SRMECH_ERR_OVERFLOW;
    }
    st = elb_emit_mono(c, &r->pref, out_coeff_num, out_coeff_den, out_exps_flat, row);
    if (st != SRMECH_OK) { return st; }
    for (i = 0; i < r->n_num; i++) {
        st = elb_emit_mono(c, &r->num[i], out_coeff_num, out_coeff_den,
                           out_exps_flat, row);
        if (st != SRMECH_OK) { return st; }
    }
    for (i = 0; i < r->n_den; i++) {
        st = elb_emit_mono(c, &r->den[i], out_coeff_num, out_coeff_den,
                           out_exps_flat, row);
        if (st != SRMECH_OK) { return st; }
    }
    out_n_num[elem] = r->n_num;
    out_n_den[elem] = r->n_den;
    return SRMECH_OK;
}

/* Build + emit one basis element L_i. Saves the arena cursor, carves the
 * per-element working set, computes prod_others / v_i / the k theta args, runs
 * er_build (the EllRatio.__init__ mirror: unit prefactor, num = the k thetas,
 * empty den), emits, then RESTORES the cursor so the next element reuses the
 * memory. */
static srmech_status_t elb_one_element(srmech_ell_ctx_t *c, const elb_persist_t *p,
                                       size_t k, size_t i, int psym,
                                       srmech_bigint_t *out_coeff_num,
                                       srmech_bigint_t *out_coeff_den,
                                       int32_t *out_exps_flat, size_t out_exps_cap_rows,
                                       size_t *out_n_num, size_t *out_n_den, size_t *row)
{
    elb_work_t w = {0};
    size_t saved = c->pool_cur;
    srmech_status_t st;
    assert(c != NULL && p != NULL && i < k);
    assert(out_n_num != NULL && out_n_den != NULL && row != NULL);
    st = elb_bind_work(c, &w, k);
    if (st != SRMECH_OK) { return st; }
    st = elb_prod_others(c, &w, p, k, i);
    if (st != SRMECH_OK) { return st; }
    st = elb_build_args(c, &w, p, k, i);
    if (st != SRMECH_OK) { return st; }
    st = elb_mono_set_one(c, &w.one);                      /* the unit pref0      */
    if (st != SRMECH_OK) { return st; }
    st = elb_er_build(c, &w.ratio, &w.one, w.args, k, NULL, 0, psym,
                      &w.scr, w.cn, k, w.cd, 1u);
    if (st != SRMECH_OK) { return st; }
    st = elb_emit(c, &w.ratio, i, out_coeff_num, out_coeff_den, out_exps_flat,
                  out_exps_cap_rows, out_n_num, out_n_den, row);
    if (st != SRMECH_OK) { return st; }
    c->pool_cur = saved;                                   /* reuse the memory    */
    return SRMECH_OK;
}

srmech_status_t srmech_elliptic_lagrange_basis(size_t n_syms, int varsym, int psym,
                                               size_t k,
                                               const srmech_bigint_t *pt_coeff_num,
                                               const srmech_bigint_t *pt_coeff_den,
                                               const int32_t *pt_exps_flat,
                                               const srmech_bigint_t *mult_num,
                                               const srmech_bigint_t *mult_den,
                                               const int32_t *mult_exps,
                                               uint32_t coeff_cap,
                                               srmech_bigint_t *out_coeff_num,
                                               srmech_bigint_t *out_coeff_den,
                                               int32_t *out_exps_flat,
                                               size_t out_exps_cap_rows,
                                               size_t *out_n_num, size_t *out_n_den,
                                               void *ws, size_t ws_len)
{
    srmech_ell_ctx_t c = {0};
    elb_persist_t p = {0};
    size_t i;
    size_t row = 0;
    srmech_status_t st;
    assert(out_n_num != NULL && out_n_den != NULL);
    assert(out_coeff_num != NULL && out_coeff_den != NULL);
    if (out_n_num == NULL || out_n_den == NULL) { return SRMECH_ERR_NULL_ARG; }
    if (out_coeff_num == NULL || out_coeff_den == NULL || out_exps_flat == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (k == 0u) { return SRMECH_ERR_NULL_ARG; }       /* >= 1 node (Python raises) */
    if (pt_coeff_num == NULL || pt_coeff_den == NULL || pt_exps_flat == NULL
        || mult_num == NULL || mult_den == NULL || mult_exps == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    c.n_syms = (n_syms == 0u) ? 1u : n_syms;
    c.cap = (coeff_cap < 4u) ? 4u : coeff_cap;
    st = elb_er_arena_init(&c, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    st = elb_bind_persist(&c, &p, k);
    if (st != SRMECH_OK) { return st; }
    st = elb_parse(&c, &p, k, varsym, pt_coeff_num, pt_coeff_den, pt_exps_flat,
                   mult_num, mult_den, mult_exps);
    if (st != SRMECH_OK) { return st; }
    for (i = 0; i < k; i++) {
        st = elb_one_element(&c, &p, k, i, psym, out_coeff_num, out_coeff_den,
                             out_exps_flat, out_exps_cap_rows, out_n_num, out_n_den,
                             &row);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* The minimum `ws_len` BYTES srmech_elliptic_lagrange_basis needs for the given
 * shape (n_syms symbols, k interpolation nodes, coeff_limbs the per-coefficient
 * significant-limb estimate). Sized to the inputs -- no compiled-in cap; if RAM
 * balloons the caller mis-encoded the fiber. The persistent head (k point monos +
 * multiplier + signk + z) plus ONE element's working set (the per-element buffers
 * reuse memory across i via the saved/restored cursor). */
size_t srmech_elliptic_lagrange_basis_ws_bound(size_t n_syms, size_t k,
                                               size_t coeff_limbs)
{
    size_t cap = (coeff_limbs < 4u) ? 4u : coeff_limbs;
    size_t ns = (n_syms == 0u) ? 1u : n_syms;
    size_t kk = (k == 0u) ? 1u : k;
    size_t mw = elb_er_mono_words(cap, ns);
    /* persistent: k points + multiplier + signk + z. */
    size_t persist = (kk + 3u) * mw;
    /* per-element: prod + vi + tmp + one + args[k] + cn[k] + cd[1] + ratio + scr. */
    size_t elem = (4u + kk + kk + 1u) * mw          /* prod/vi/tmp/one + args/cn/cd */
                  + (mw + (kk + 1u) * mw)           /* ratio (pref + num[k] + den[1]) */
                  + SRMECH_ELL_ER_SCR_MONOS * mw    /* scr.pm                         */
                  + kk + 3u * cap + 64u;            /* scr.used flags + scr bigints   */
    size_t scratch_words = cap * 16u + 512u;
    size_t total = persist + elem + scratch_words + 1024u;
    assert(cap >= 4u);
    assert(total >= scratch_words);
    return total * sizeof(uint32_t);
}
