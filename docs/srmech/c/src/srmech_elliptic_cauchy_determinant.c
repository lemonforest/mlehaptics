/*
 * srmech_elliptic_cauchy_determinant.c -- the 1:1 native C peer of
 * srmech.amsc.elliptic_determinant.elliptic_cauchy_determinant (rc94), the
 * ELLIPTIC-DETERMINANT primitive: Frobenius's elliptic Cauchy determinant
 * evaluation, the foundation of the multivariable (root-system Cn) elliptic
 * reduction row.
 *
 * A C-MIRROR PARITY build (NOT a new algorithm): it constructs the EXACT
 * closed form the already-shipped pure-Python op builds, byte-for-byte.
 *
 * For distinct x_1..x_n, y_1..y_n and a parameter t (Rosengren, Elliptic
 * Hypergeometric Functions, arXiv:1608.06161v3, Exercise 1.6.6; classically
 * Frobenius 1882):
 *
 *   det_{1<=i,j<=n} [ theta(t*x_i*y_j; p) / theta(x_i*y_j; p) ]
 *     = theta(t; p)^{n-1} * theta(t*x_1..x_n*y_1..y_n; p)
 *       * PROD_{i<j} [ x_j*y_j * theta(x_i/x_j; p)*theta(y_i/y_j; p) ]
 *       / PROD_{i,j} theta(x_i*y_j; p).
 *
 * This op CONSTRUCTS the right-hand side as an exact EllRatio: the EllMonomial
 * prefactor PROD_{i<j} x_j*y_j, the numerator thetas theta(t) x (n-1),
 * theta(t*PRODx*PRODy) and theta(x_i/x_j), theta(y_i/y_j) for i<j, and the
 * denominator thetas theta(x_i*y_j) for all i,j. The EllRatio constructor
 * (er_build) folds each theta's canonicalize prefactor into the global
 * prefactor, cancels matching thetas between num and den, and sorts the
 * survivors -- so the emitted EllRatio is the canonical value Python returns.
 *
 * This is PURE COMPOSITION of the shared srmech_ellbase_* exact-Q monomial
 * algebra (mul / inv) + er_build (the EllRatio.__init__ mirror) -- the same
 * single copy srmech_elliptic_lagrange_basis and srmech_elliptic_gosper ride.
 *
 * Wire form (mirrors srmech_elliptic_lagrange_basis): the interned symbol-table
 * dimension `n_syms` (distinct symbols in the Python sorted-symbol-NAME order so
 * the dense exponent vector reproduces EllMonomial._sort_key); `psym` the
 * interned index of the nome `p` (-1 if absent); `n` the matrix dimension; the
 * parameter monomial `t_num` / `t_den` / `t_exps`; the flat x-monomial coeff
 * arrays `xs_num` / `xs_den` (x0..x_{n-1}) + the flat int32 exponent rows
 * `xs_exps_flat` (int32[n_syms] per x); likewise the y-monomials. `coeff_cap` is
 * the per-bigint limb cap.
 *
 * Output: the single closed-form EllRatio written flat as a ROW stream. Each
 * emitted monomial (the prefactor or a theta argument) contributes ONE row: its
 * exact-Q coeff into `out_coeff_num` / `out_coeff_den`[row] AND its dense
 * int32[n_syms] exponent row into `out_exps_flat`, in the order: the prefactor
 * row, then `*out_n_num` num-theta rows, then `*out_n_den` den-theta rows. The
 * theta-count survivors come back in `*out_n_num` / `*out_n_den`. (The coeff
 * travels with EVERY row -- a canonicalized theta ARGUMENT can carry a non-unit
 * Class-K coeff -- so the coeff is NOT assumed 1.) `out_exps_cap_rows` is the row
 * capacity of the caller's buffers; too small -> SRMECH_ERR_OVERFLOW. n == 0 ->
 * SRMECH_ERR_NULL_ARG (Python raises ValueError). A required NULL pointer ->
 * SRMECH_ERR_NULL_ARG; a too-small arena -> SRMECH_ERR_OVERFLOW.
 *
 * Malloc-free (JPL Rule 3): every working monomial / theta + the bigint scratch
 * is carved from the caller arena `ws`, sized to the input (n, n_syms) -- no
 * compiled-in cap. Sign travels in the Class-K coeff branch, never abs()/fabs().
 * Additive symbol -> ABI unchanged (stays 3). License: MIT.
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto/recursion): OK -- iterative, flat static helpers
 *   - Rule 2 (bounded loops)    : OK -- bounded by n / n_syms
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

/* The bound persistent buffers: t + the parsed x / y monomials + the running
 * products PROD x, PROD y (all live for the whole construction). */
typedef struct ecd_persist {
    srmech_ell_mono_t  t;         /* the parameter t                           */
    srmech_ell_mono_t *xs;        /* n parsed x monomials                      */
    srmech_ell_mono_t *ys;        /* n parsed y monomials                      */
    srmech_ell_mono_t  prodx;     /* PROD_i x_i                                */
    srmech_ell_mono_t  prody;     /* PROD_j y_j                                */
} ecd_persist_t;

/* The working buffers for the single ratio build (the n*n num / den theta args
 * + the prefactor + er_build's canon scratch + the canonical output ratio). */
typedef struct ecd_work {
    srmech_ell_mono_t  pref;      /* PROD_{i<j} x_j*y_j                         */
    srmech_ell_mono_t  tmp;       /* general scratch monomial                  */
    srmech_ell_mono_t *num;       /* the n*n numerator theta-argument monomials */
    srmech_ell_mono_t *den;       /* the n*n denominator theta-argument monomials */
    srmech_ell_mono_t *cn;        /* er_build canon scratch (num)              */
    srmech_ell_mono_t *cd;        /* er_build canon scratch (den)              */
    elb_ratio_t        ratio;     /* the canonical closed-form EllRatio        */
    elb_scr_t          scr;       /* the er_build scratch bundle               */
} ecd_work_t;

/* Parse t, xs[0..n-1], ys[0..n-1] from the flat input coeff / exponent arrays
 * into bound monomials. Mirrors the head of the Python op (_coerce_monomial). */
static srmech_status_t ecd_parse(srmech_ell_ctx_t *c, ecd_persist_t *p, size_t n,
                                 const srmech_bigint_t *t_num,
                                 const srmech_bigint_t *t_den, const int32_t *t_exps,
                                 const srmech_bigint_t *xs_num,
                                 const srmech_bigint_t *xs_den, const int32_t *xs_exps,
                                 const srmech_bigint_t *ys_num,
                                 const srmech_bigint_t *ys_den, const int32_t *ys_exps)
{
    size_t i;
    srmech_status_t st;
    assert(c != NULL && p != NULL);
    assert(t_num != NULL && t_den != NULL && t_exps != NULL);
    st = srmech_bigint_copy(&p->t.coeff.num, t_num);
    if (st == SRMECH_OK) { st = srmech_bigint_copy(&p->t.coeff.den, t_den); }
    if (st != SRMECH_OK) { return st; }
    memcpy(p->t.exps, t_exps, c->n_syms * sizeof(int32_t));
    for (i = 0; i < n; i++) {
        st = srmech_bigint_copy(&p->xs[i].coeff.num, &xs_num[i]);
        if (st == SRMECH_OK) { st = srmech_bigint_copy(&p->xs[i].coeff.den, &xs_den[i]); }
        if (st == SRMECH_OK) { st = srmech_bigint_copy(&p->ys[i].coeff.num, &ys_num[i]); }
        if (st == SRMECH_OK) { st = srmech_bigint_copy(&p->ys[i].coeff.den, &ys_den[i]); }
        if (st != SRMECH_OK) { return st; }
        memcpy(p->xs[i].exps, xs_exps + i * c->n_syms, c->n_syms * sizeof(int32_t));
        memcpy(p->ys[i].exps, ys_exps + i * c->n_syms, c->n_syms * sizeof(int32_t));
    }
    return SRMECH_OK;
}

/* prodx := PROD_i x_i and prody := PROD_j y_j (start at one, mono_mul each). */
static srmech_status_t ecd_prods(srmech_ell_ctx_t *c, ecd_persist_t *p, size_t n,
                                 elb_scr_t *s, srmech_ell_mono_t *tmp)
{
    size_t i;
    srmech_status_t st;
    assert(c != NULL && p != NULL && s != NULL);
    assert(tmp != NULL);
    st = elb_mono_set_one(c, &p->prodx);
    if (st == SRMECH_OK) { st = elb_mono_set_one(c, &p->prody); }
    if (st != SRMECH_OK) { return st; }
    for (i = 0; i < n; i++) {
        st = elb_mono_mul(c, tmp, &p->prodx, &p->xs[i], &s->g, &s->t0, &s->t1);
        if (st == SRMECH_OK) { st = elb_mono_copy(c, &p->prodx, tmp); }
        if (st != SRMECH_OK) { return st; }
        st = elb_mono_mul(c, tmp, &p->prody, &p->ys[i], &s->g, &s->t0, &s->t1);
        if (st == SRMECH_OK) { st = elb_mono_copy(c, &p->prody, tmp); }
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* Fill num[0..n*n-1]: (n-1) copies of t, then t*prodx*prody, then for i<j the
 * arguments x_i/x_j and y_i/y_j. Order-free (er_build canonicalizes + sorts the
 * multiset); the count is exactly n*n. Mirrors the Python num list. */
static srmech_status_t ecd_build_num(srmech_ell_ctx_t *c, ecd_persist_t *p, size_t n,
                                     srmech_ell_mono_t *num, elb_scr_t *s,
                                     srmech_ell_mono_t *tmp)
{
    size_t i;
    size_t j;
    size_t m = 0;
    srmech_status_t st;
    assert(c != NULL && p != NULL && num != NULL);
    assert(tmp != NULL && s != NULL);
    for (i = 0; i + 1u < n; i++) {                       /* theta(t)^{n-1}     */
        st = elb_mono_copy(c, &num[m], &p->t);
        if (st != SRMECH_OK) { return st; }
        m++;
    }
    st = elb_mono_mul(c, tmp, &p->t, &p->prodx, &s->g, &s->t0, &s->t1);   /* t*prodx */
    if (st == SRMECH_OK) {
        st = elb_mono_mul(c, &num[m], tmp, &p->prody, &s->g, &s->t0, &s->t1); /* *prody */
    }
    if (st != SRMECH_OK) { return st; }
    m++;
    for (i = 0; i < n; i++) {
        for (j = i + 1u; j < n; j++) {
            st = elb_mono_inv(c, tmp, &p->xs[j]);                        /* x_j^{-1} */
            if (st == SRMECH_OK) {
                st = elb_mono_mul(c, &num[m], &p->xs[i], tmp, &s->g, &s->t0, &s->t1);
            }
            if (st != SRMECH_OK) { return st; }
            m++;
            st = elb_mono_inv(c, tmp, &p->ys[j]);                        /* y_j^{-1} */
            if (st == SRMECH_OK) {
                st = elb_mono_mul(c, &num[m], &p->ys[i], tmp, &s->g, &s->t0, &s->t1);
            }
            if (st != SRMECH_OK) { return st; }
            m++;
        }
    }
    assert(m == n * n);
    return SRMECH_OK;
}

/* Fill den[i*n+j] = x_i * y_j for all i, j (the denominator theta arguments). */
static srmech_status_t ecd_build_den(srmech_ell_ctx_t *c, ecd_persist_t *p, size_t n,
                                     srmech_ell_mono_t *den, elb_scr_t *s)
{
    size_t i;
    size_t j;
    size_t m = 0;
    srmech_status_t st;
    assert(c != NULL && p != NULL && den != NULL);
    assert(s != NULL);
    for (i = 0; i < n; i++) {
        for (j = 0; j < n; j++) {
            st = elb_mono_mul(c, &den[m], &p->xs[i], &p->ys[j], &s->g, &s->t0, &s->t1);
            if (st != SRMECH_OK) { return st; }
            m++;
        }
    }
    assert(m == n * n);
    return SRMECH_OK;
}

/* pref := PROD_{i<j} x_j * y_j (the Frobenius closed-form monomial prefactor). */
static srmech_status_t ecd_build_pref(srmech_ell_ctx_t *c, ecd_persist_t *p, size_t n,
                                      srmech_ell_mono_t *pref, elb_scr_t *s,
                                      srmech_ell_mono_t *tmp)
{
    size_t i;
    size_t j;
    srmech_status_t st;
    assert(c != NULL && p != NULL && pref != NULL);
    assert(tmp != NULL && s != NULL);
    st = elb_mono_set_one(c, pref);
    if (st != SRMECH_OK) { return st; }
    for (i = 0; i < n; i++) {
        for (j = i + 1u; j < n; j++) {
            st = elb_mono_mul(c, tmp, pref, &p->xs[j], &s->g, &s->t0, &s->t1);
            if (st == SRMECH_OK) {
                st = elb_mono_mul(c, pref, tmp, &p->ys[j], &s->g, &s->t0, &s->t1);
            }
            if (st != SRMECH_OK) { return st; }
        }
    }
    return SRMECH_OK;
}

/* Copy one monomial `m` into the output row stream at `*row`: its exact-Q coeff
 * into out_num/out_den[*row] AND its dense exponent row into out_exps. Advances
 * *row. */
static srmech_status_t ecd_emit_mono(srmech_ell_ctx_t *c, const srmech_ell_mono_t *m,
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
 * r->n_num num-theta rows, then the r->n_den den-theta rows -- each row carrying
 * its exact-Q coeff AND its exponent row. Writes *out_n_num / *out_n_den. */
static srmech_status_t ecd_emit_ratio(srmech_ell_ctx_t *c, const elb_ratio_t *r,
                                      srmech_bigint_t *out_num, srmech_bigint_t *out_den,
                                      int32_t *out_exps, size_t out_cap_rows,
                                      size_t *out_n_num, size_t *out_n_den, size_t *row)
{
    size_t i;
    srmech_status_t st;
    assert(c != NULL && r != NULL && row != NULL);
    assert(out_n_num != NULL && out_n_den != NULL);
    if (1u + r->n_num + r->n_den > out_cap_rows) { return SRMECH_ERR_OVERFLOW; }
    st = ecd_emit_mono(c, &r->pref, out_num, out_den, out_exps, row);
    if (st != SRMECH_OK) { return st; }
    for (i = 0; i < r->n_num; i++) {
        st = ecd_emit_mono(c, &r->num[i], out_num, out_den, out_exps, row);
        if (st != SRMECH_OK) { return st; }
    }
    for (i = 0; i < r->n_den; i++) {
        st = ecd_emit_mono(c, &r->den[i], out_num, out_den, out_exps, row);
        if (st != SRMECH_OK) { return st; }
    }
    *out_n_num = r->n_num;
    *out_n_den = r->n_den;
    return SRMECH_OK;
}

/* Carve the persistent buffers (t + xs[n] + ys[n] + prodx + prody). */
static srmech_status_t ecd_bind_persist(srmech_ell_ctx_t *c, ecd_persist_t *p, size_t n)
{
    srmech_status_t st;
    assert(c != NULL && p != NULL);
    assert(n >= 1u && c->n_syms >= 1u);
    st = elb_bind_mono(c, &p->t);
    if (st == SRMECH_OK) { st = elb_bind_mono_arr(c, &p->xs, n); }
    if (st == SRMECH_OK) { st = elb_bind_mono_arr(c, &p->ys, n); }
    if (st == SRMECH_OK) { st = elb_bind_mono(c, &p->prodx); }
    if (st == SRMECH_OK) { st = elb_bind_mono(c, &p->prody); }
    return st;
}

/* Carve the working buffers (pref + tmp + num[n*n] + den[n*n] + cn/cd + ratio + scr). */
static srmech_status_t ecd_bind_work(srmech_ell_ctx_t *c, ecd_work_t *w, size_t n)
{
    size_t nsq = n * n;
    srmech_status_t st;
    assert(c != NULL && w != NULL);
    assert(n >= 1u && c->n_syms >= 1u);
    st = elb_bind_mono(c, &w->pref);
    if (st == SRMECH_OK) { st = elb_bind_mono(c, &w->tmp); }
    if (st == SRMECH_OK) { st = elb_bind_mono_arr(c, &w->num, nsq); }
    if (st == SRMECH_OK) { st = elb_bind_mono_arr(c, &w->den, nsq); }
    if (st == SRMECH_OK) { st = elb_bind_mono_arr(c, &w->cn, nsq); }
    if (st == SRMECH_OK) { st = elb_bind_mono_arr(c, &w->cd, nsq); }
    if (st == SRMECH_OK) { st = elb_er_bind_ratio(c, &w->ratio, nsq, nsq); }
    if (st == SRMECH_OK) { st = elb_er_bind_scr(c, &w->scr, nsq); }
    return st;
}

srmech_status_t srmech_elliptic_cauchy_determinant(size_t n_syms, int psym, size_t n,
                                                   const srmech_bigint_t *t_num,
                                                   const srmech_bigint_t *t_den,
                                                   const int32_t *t_exps,
                                                   const srmech_bigint_t *xs_num,
                                                   const srmech_bigint_t *xs_den,
                                                   const int32_t *xs_exps_flat,
                                                   const srmech_bigint_t *ys_num,
                                                   const srmech_bigint_t *ys_den,
                                                   const int32_t *ys_exps_flat,
                                                   uint32_t coeff_cap,
                                                   srmech_bigint_t *out_coeff_num,
                                                   srmech_bigint_t *out_coeff_den,
                                                   int32_t *out_exps_flat,
                                                   size_t out_exps_cap_rows,
                                                   size_t *out_n_num, size_t *out_n_den,
                                                   void *ws, size_t ws_len)
{
    srmech_ell_ctx_t c = {0};
    ecd_persist_t p = {0};
    ecd_work_t w = {0};
    size_t row = 0;
    srmech_status_t st;
    assert(out_n_num != NULL && out_n_den != NULL);
    assert(out_coeff_num != NULL && out_coeff_den != NULL);
    if (out_n_num == NULL || out_n_den == NULL) { return SRMECH_ERR_NULL_ARG; }
    if (out_coeff_num == NULL || out_coeff_den == NULL || out_exps_flat == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n == 0u) { return SRMECH_ERR_NULL_ARG; }        /* >= 1 (Python raises) */
    if (t_num == NULL || t_den == NULL || t_exps == NULL || xs_num == NULL
        || xs_den == NULL || xs_exps_flat == NULL || ys_num == NULL
        || ys_den == NULL || ys_exps_flat == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    c.n_syms = (n_syms == 0u) ? 1u : n_syms;
    c.cap = (coeff_cap < 4u) ? 4u : coeff_cap;
    st = elb_er_arena_init(&c, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    st = ecd_bind_persist(&c, &p, n);
    if (st == SRMECH_OK) { st = ecd_bind_work(&c, &w, n); }
    if (st == SRMECH_OK) {
        st = ecd_parse(&c, &p, n, t_num, t_den, t_exps, xs_num, xs_den, xs_exps_flat,
                       ys_num, ys_den, ys_exps_flat);
    }
    if (st == SRMECH_OK) { st = ecd_prods(&c, &p, n, &w.scr, &w.tmp); }
    if (st == SRMECH_OK) { st = ecd_build_num(&c, &p, n, w.num, &w.scr, &w.tmp); }
    if (st == SRMECH_OK) { st = ecd_build_den(&c, &p, n, w.den, &w.scr); }
    if (st == SRMECH_OK) { st = ecd_build_pref(&c, &p, n, &w.pref, &w.scr, &w.tmp); }
    if (st == SRMECH_OK) {
        st = elb_er_build(&c, &w.ratio, &w.pref, w.num, n * n, w.den, n * n, psym,
                          &w.scr, w.cn, n * n, w.cd, n * n);
    }
    if (st == SRMECH_OK) {
        st = ecd_emit_ratio(&c, &w.ratio, out_coeff_num, out_coeff_den, out_exps_flat,
                            out_exps_cap_rows, out_n_num, out_n_den, &row);
    }
    return st;
}

/* The minimum `ws_len` BYTES srmech_elliptic_cauchy_determinant needs for the
 * given shape (n_syms symbols, n the matrix dimension, coeff_limbs the per-
 * coefficient significant-limb estimate). Sized to the inputs -- no compiled-in
 * cap; if RAM balloons the caller mis-encoded the fiber. The persistent head
 * (t + xs[n] + ys[n] + prodx + prody) plus the single ratio's working set
 * (pref + tmp + num[n*n] + den[n*n] + cn[n*n] + cd[n*n] + the ratio (pref +
 * num[n*n] + den[n*n]) + the er_build scratch bundle). */
size_t srmech_elliptic_cauchy_determinant_ws_bound(size_t n_syms, size_t n,
                                                   size_t coeff_limbs)
{
    size_t cap = (coeff_limbs < 4u) ? 4u : coeff_limbs;
    size_t ns = (n_syms == 0u) ? 1u : n_syms;
    size_t nn = (n == 0u) ? 1u : n;
    size_t nsq = nn * nn;
    size_t mw = elb_er_mono_words(cap, ns);
    /* persistent: t + xs[n] + ys[n] + prodx + prody. */
    size_t persist = (2u * nn + 3u) * mw;
    /* per-build: pref + tmp + num[nsq] + den[nsq] + cn[nsq] + cd[nsq]. */
    size_t work = (2u + 4u * nsq) * mw
                  + (mw + 2u * nsq * mw)            /* ratio (pref + num[nsq] + den[nsq]) */
                  + SRMECH_ELL_ER_SCR_MONOS * mw    /* scr.pm                             */
                  + nsq + 3u * cap + 64u;           /* scr.used flags + scr bigints       */
    size_t scratch_words = cap * 16u + 512u;
    size_t total = persist + work + scratch_words + 2048u;
    assert(cap >= 4u);
    assert(total >= scratch_words);
    return total * sizeof(uint32_t);
}
