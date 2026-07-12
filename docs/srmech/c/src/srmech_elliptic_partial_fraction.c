/*
 * srmech_elliptic_partial_fraction.c -- the 1:1 native C peer of
 * srmech.amsc.elliptic_partial_fraction.elliptic_partial_fraction (rc95), the
 * ELLIPTIC PARTIAL-FRACTION expansion: the reduction ENGINE of the multivariable
 * (root-system Cn) elliptic reduction row.
 *
 * A C-MIRROR PARITY build (NOT a new algorithm): it constructs the EXACT n
 * theta-quotient TERMS the already-shipped pure-Python op builds, byte-for-byte;
 * the Python side SUMS them into the returned ThetaSum (the summation is pure
 * carrier algebra, done identically to the pure path, so the native ThetaSum
 * EQUALS the pure ThetaSum -- trusted only after that == check).
 *
 * For distinct z_1..z_n, y_1..y_n and the variable x (Rosengren, Elliptic
 * Hypergeometric Functions, arXiv:1608.06161v3, Proposition 1.6.1 + Eq. 1.22):
 *
 *   PROD_{k=1}^{n} theta(x/z_k; p)/theta(x/y_k; p)
 *     = 1/theta(Y/Z; p) * SUM_{j=1}^{n}
 *         [ PROD_k theta(y_j/z_k; p) / PROD_{k!=j} theta(y_j/y_k; p) ]
 *         * [ theta(x*Y/(y_j*Z); p) / theta(x/y_j; p) ],
 *
 * with Y = y_1..y_n and Z = z_1..z_n. Each summand j is an EllRatio with the
 * unit prefactor:
 *   num thetas: theta(y_j/z_k) for all k  +  theta(x*Y/(y_j*Z))        (n+1 args)
 *   den thetas: theta(y_j/y_k) for k!=j  +  theta(x/y_j)  +  theta(Y/Z) (n+1 args)
 * er_build (the EllRatio.__init__ mirror) folds each theta's canonicalize
 * prefactor, cancels matching thetas between num and den, and sorts the
 * survivors -- so each emitted EllRatio is the canonical value Python returns.
 *
 * This is PURE COMPOSITION of the shared srmech_ellbase_* exact-Q monomial
 * algebra (mul / inv) + er_build -- the same single copy the elliptic Lagrange
 * basis / Cauchy determinant peers ride. There is NO existing ThetaSum-
 * CONSTRUCTION C surface, so the peer returns the n EllRatio TERMS (as a row
 * stream, exactly like srmech_elliptic_lagrange_basis's k basis EllRatios) and
 * the Python `from_ellratio` + `+` sums them.
 *
 * Wire form (mirrors srmech_elliptic_lagrange_basis): the interned symbol-table
 * dimension `n_syms` (distinct symbols in the Python sorted-symbol-NAME order so
 * the dense exponent vector reproduces EllMonomial._sort_key); `psym` the
 * interned index of the nome `p` (-1 if absent); `n` the term count; the variable
 * monomial `x_num` / `x_den` / `x_exps`; the flat z-monomial coeff arrays
 * `zs_num` / `zs_den` (z0..z_{n-1}) + the flat int32 exponent rows `zs_exps_flat`
 * (int32[n_syms] per z); likewise the y-monomials. `coeff_cap` is the per-bigint
 * limb cap.
 *
 * Output: the n TERM EllRatios, written out flat -- per term j, `out_n_num[j]` /
 * `out_n_den[j]` the survivor theta counts, and the canonical rows appended to
 * out_coeff_num/out_coeff_den/out_exps_flat (per term: its prefactor row, then
 * its out_n_num[j] num rows, then its out_n_den[j] den rows; each row carries its
 * exact-Q coeff AND its dense int32[n_syms] exponent row). `out_exps_cap_rows` is
 * the row capacity of the caller's buffers; too small -> SRMECH_ERR_OVERFLOW.
 * n == 0 -> SRMECH_ERR_NULL_ARG (Python raises ValueError); a required NULL
 * pointer -> SRMECH_ERR_NULL_ARG; a too-small arena -> SRMECH_ERR_OVERFLOW.
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

/* The bound persistent buffers: x + the parsed z / y monomials + the running
 * products PROD z (= Z), PROD y (= Y), the constant argument Y/Z, plus a setup
 * scratch (tmp + scr) for the product / Y/Z construction (all live for the whole
 * expansion). */
typedef struct epf_persist {
    srmech_ell_mono_t  x;         /* the variable x                            */
    srmech_ell_mono_t *zs;        /* n parsed z monomials                      */
    srmech_ell_mono_t *ys;        /* n parsed y monomials                      */
    srmech_ell_mono_t  prodz;     /* Z = PROD_k z_k                            */
    srmech_ell_mono_t  prody;     /* Y = PROD_j y_j                            */
    srmech_ell_mono_t  yz;        /* Y/Z (the 1/theta(Y/Z) denominator arg)    */
    srmech_ell_mono_t  tmp;       /* setup scratch (products / Y/Z)            */
    elb_scr_t          scr;       /* setup scratch bundle (g/t0/t1 for muls)   */
} epf_persist_t;

/* The per-term working buffers (carved fresh from a reset cursor each j). Each
 * term j is an EllRatio with n+1 num thetas + n+1 den thetas + unit prefactor. */
typedef struct epf_work {
    srmech_ell_mono_t  one;       /* the unit prefactor (pref0)                */
    srmech_ell_mono_t  tmp;       /* general scratch monomial                  */
    srmech_ell_mono_t  tmp2;      /* general scratch monomial                  */
    srmech_ell_mono_t *num;       /* the n+1 numerator theta-argument monomials */
    srmech_ell_mono_t *den;       /* the n+1 denominator theta-argument monomials */
    srmech_ell_mono_t *cn;        /* er_build canon scratch (num)              */
    srmech_ell_mono_t *cd;        /* er_build canon scratch (den)              */
    elb_ratio_t        ratio;     /* the canonical term EllRatio               */
    elb_scr_t          scr;       /* the er_build scratch bundle               */
} epf_work_t;

/* Parse x, zs[0..n-1], ys[0..n-1] from the flat input coeff / exponent arrays
 * into bound monomials. Mirrors the head of the Python op (_coerce_monomial). */
static srmech_status_t epf_parse(srmech_ell_ctx_t *c, epf_persist_t *p, size_t n,
                                 const srmech_bigint_t *x_num,
                                 const srmech_bigint_t *x_den, const int32_t *x_exps,
                                 const srmech_bigint_t *zs_num,
                                 const srmech_bigint_t *zs_den, const int32_t *zs_exps,
                                 const srmech_bigint_t *ys_num,
                                 const srmech_bigint_t *ys_den, const int32_t *ys_exps)
{
    size_t i;
    srmech_status_t st;
    assert(c != NULL && p != NULL);
    assert(x_num != NULL && x_den != NULL && x_exps != NULL);
    st = srmech_bigint_copy(&p->x.coeff.num, x_num);
    if (st == SRMECH_OK) { st = srmech_bigint_copy(&p->x.coeff.den, x_den); }
    if (st != SRMECH_OK) { return st; }
    memcpy(p->x.exps, x_exps, c->n_syms * sizeof(int32_t));
    for (i = 0; i < n; i++) {
        st = srmech_bigint_copy(&p->zs[i].coeff.num, &zs_num[i]);
        if (st == SRMECH_OK) { st = srmech_bigint_copy(&p->zs[i].coeff.den, &zs_den[i]); }
        if (st == SRMECH_OK) { st = srmech_bigint_copy(&p->ys[i].coeff.num, &ys_num[i]); }
        if (st == SRMECH_OK) { st = srmech_bigint_copy(&p->ys[i].coeff.den, &ys_den[i]); }
        if (st != SRMECH_OK) { return st; }
        memcpy(p->zs[i].exps, zs_exps + i * c->n_syms, c->n_syms * sizeof(int32_t));
        memcpy(p->ys[i].exps, ys_exps + i * c->n_syms, c->n_syms * sizeof(int32_t));
    }
    return SRMECH_OK;
}

/* prodz := PROD_k z_k, prody := PROD_j y_j, yz := prody * prodz^{-1} (= Y/Z). */
static srmech_status_t epf_prods(srmech_ell_ctx_t *c, epf_persist_t *p, size_t n)
{
    size_t i;
    elb_scr_t *s = &p->scr;
    srmech_status_t st;
    assert(c != NULL && p != NULL);
    assert(n >= 1u && c->n_syms >= 1u);
    st = elb_mono_set_one(c, &p->prodz);
    if (st == SRMECH_OK) { st = elb_mono_set_one(c, &p->prody); }
    if (st != SRMECH_OK) { return st; }
    for (i = 0; i < n; i++) {
        st = elb_mono_mul(c, &p->tmp, &p->prodz, &p->zs[i], &s->g, &s->t0, &s->t1);
        if (st == SRMECH_OK) { st = elb_mono_copy(c, &p->prodz, &p->tmp); }
        if (st != SRMECH_OK) { return st; }
        st = elb_mono_mul(c, &p->tmp, &p->prody, &p->ys[i], &s->g, &s->t0, &s->t1);
        if (st == SRMECH_OK) { st = elb_mono_copy(c, &p->prody, &p->tmp); }
        if (st != SRMECH_OK) { return st; }
    }
    st = elb_mono_inv(c, &p->tmp, &p->prodz);                  /* Z^{-1}          */
    if (st == SRMECH_OK) {
        st = elb_mono_mul(c, &p->yz, &p->prody, &p->tmp,       /* Y/Z             */
                          &s->g, &s->t0, &s->t1);
    }
    return st;
}

/* Fill num[0..n]: for k, theta arg y_j / z_k; then x*Y/(y_j*Z). Count == n+1.
 * Mirrors the Python term-j num list. */
static srmech_status_t epf_build_num(srmech_ell_ctx_t *c, epf_persist_t *p, size_t n,
                                     size_t j, srmech_ell_mono_t *num, elb_scr_t *s,
                                     srmech_ell_mono_t *tmp, srmech_ell_mono_t *tmp2)
{
    size_t k;
    size_t m = 0;
    srmech_status_t st;
    assert(c != NULL && p != NULL && num != NULL);
    assert(tmp != NULL && tmp2 != NULL && s != NULL && j < n);
    for (k = 0; k < n; k++) {                                  /* theta(y_j/z_k)  */
        st = elb_mono_inv(c, tmp, &p->zs[k]);                  /* z_k^{-1}        */
        if (st == SRMECH_OK) {
            st = elb_mono_mul(c, &num[m], &p->ys[j], tmp, &s->g, &s->t0, &s->t1);
        }
        if (st != SRMECH_OK) { return st; }
        m++;
    }
    st = elb_mono_mul(c, tmp, &p->x, &p->prody, &s->g, &s->t0, &s->t1);   /* x*Y   */
    if (st == SRMECH_OK) { st = elb_mono_inv(c, tmp2, &p->ys[j]); }       /* y_j^-1 */
    if (st == SRMECH_OK) {
        st = elb_mono_mul(c, &num[m], tmp, tmp2, &s->g, &s->t0, &s->t1);  /* x*Y/y_j */
    }
    if (st == SRMECH_OK) { st = elb_mono_inv(c, tmp2, &p->prodz); }       /* Z^-1  */
    if (st == SRMECH_OK) {
        st = elb_mono_mul(c, tmp, &num[m], tmp2, &s->g, &s->t0, &s->t1);  /* /Z    */
    }
    if (st == SRMECH_OK) { st = elb_mono_copy(c, &num[m], tmp); }
    if (st != SRMECH_OK) { return st; }
    m++;
    assert(m == n + 1u);
    return SRMECH_OK;
}

/* Fill den[0..n]: for k!=j, theta arg y_j / y_k; then x/y_j; then Y/Z. Count ==
 * n+1. Mirrors the Python term-j den list (the last arg is the 1/theta(Y/Z)). */
static srmech_status_t epf_build_den(srmech_ell_ctx_t *c, epf_persist_t *p, size_t n,
                                     size_t j, srmech_ell_mono_t *den, elb_scr_t *s,
                                     srmech_ell_mono_t *tmp)
{
    size_t k;
    size_t m = 0;
    srmech_status_t st;
    assert(c != NULL && p != NULL && den != NULL);
    assert(tmp != NULL && s != NULL && j < n);
    for (k = 0; k < n; k++) {                                  /* theta(y_j/y_k)  */
        if (k == j) { continue; }
        st = elb_mono_inv(c, tmp, &p->ys[k]);                  /* y_k^{-1}        */
        if (st == SRMECH_OK) {
            st = elb_mono_mul(c, &den[m], &p->ys[j], tmp, &s->g, &s->t0, &s->t1);
        }
        if (st != SRMECH_OK) { return st; }
        m++;
    }
    st = elb_mono_inv(c, tmp, &p->ys[j]);                      /* y_j^{-1}        */
    if (st == SRMECH_OK) {
        st = elb_mono_mul(c, &den[m], &p->x, tmp, &s->g, &s->t0, &s->t1); /* x/y_j */
    }
    if (st != SRMECH_OK) { return st; }
    m++;
    st = elb_mono_copy(c, &den[m], &p->yz);                    /* Y/Z             */
    if (st != SRMECH_OK) { return st; }
    m++;
    assert(m == n + 1u);
    return SRMECH_OK;
}

/* Copy one monomial `m` into the output row stream at `*row`: its exact-Q coeff
 * into out_coeff_num/den[*row] AND its dense exponent row into out_exps_flat. The
 * theta ARGUMENTS carry a non-unit Class-K coeff (canonicalize emits an exact
 * prefactor), so the coeff MUST travel with the exps row. Advances *row. */
static srmech_status_t epf_emit_mono(srmech_ell_ctx_t *c, const srmech_ell_mono_t *m,
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
 * out_n_num/den[term], and the monomial rows (prefactor, then num0..n_num-1, then
 * den0..n_den-1) appended at *row -- each row carrying its exact-Q coeff AND its
 * exponent row. */
static srmech_status_t epf_emit(srmech_ell_ctx_t *c, const elb_ratio_t *r, size_t term,
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
    st = epf_emit_mono(c, &r->pref, out_coeff_num, out_coeff_den, out_exps_flat, row);
    if (st != SRMECH_OK) { return st; }
    for (i = 0; i < r->n_num; i++) {
        st = epf_emit_mono(c, &r->num[i], out_coeff_num, out_coeff_den,
                           out_exps_flat, row);
        if (st != SRMECH_OK) { return st; }
    }
    for (i = 0; i < r->n_den; i++) {
        st = epf_emit_mono(c, &r->den[i], out_coeff_num, out_coeff_den,
                           out_exps_flat, row);
        if (st != SRMECH_OK) { return st; }
    }
    out_n_num[term] = r->n_num;
    out_n_den[term] = r->n_den;
    return SRMECH_OK;
}

/* Carve the persistent buffers (x + zs[n] + ys[n] + prodz + prody + yz + tmp + scr). */
static srmech_status_t epf_bind_persist(srmech_ell_ctx_t *c, epf_persist_t *p, size_t n)
{
    srmech_status_t st;
    assert(c != NULL && p != NULL);
    assert(n >= 1u && c->n_syms >= 1u);
    st = elb_bind_mono(c, &p->x);
    if (st == SRMECH_OK) { st = elb_bind_mono_arr(c, &p->zs, n); }
    if (st == SRMECH_OK) { st = elb_bind_mono_arr(c, &p->ys, n); }
    if (st == SRMECH_OK) { st = elb_bind_mono(c, &p->prodz); }
    if (st == SRMECH_OK) { st = elb_bind_mono(c, &p->prody); }
    if (st == SRMECH_OK) { st = elb_bind_mono(c, &p->yz); }
    if (st == SRMECH_OK) { st = elb_bind_mono(c, &p->tmp); }
    if (st == SRMECH_OK) { st = elb_er_bind_scr(c, &p->scr, n + 1u); }
    return st;
}

/* Carve the per-term working buffers (one + tmp + tmp2 + num[n+1] + den[n+1] +
 * cn/cd + ratio + scr) from the CURRENT cursor (the caller saves/restores it). */
static srmech_status_t epf_bind_work(srmech_ell_ctx_t *c, epf_work_t *w, size_t n)
{
    size_t np1 = n + 1u;
    srmech_status_t st;
    assert(c != NULL && w != NULL);
    assert(n >= 1u && c->n_syms >= 1u);
    st = elb_bind_mono(c, &w->one);
    if (st == SRMECH_OK) { st = elb_bind_mono(c, &w->tmp); }
    if (st == SRMECH_OK) { st = elb_bind_mono(c, &w->tmp2); }
    if (st == SRMECH_OK) { st = elb_bind_mono_arr(c, &w->num, np1); }
    if (st == SRMECH_OK) { st = elb_bind_mono_arr(c, &w->den, np1); }
    if (st == SRMECH_OK) { st = elb_bind_mono_arr(c, &w->cn, np1); }
    if (st == SRMECH_OK) { st = elb_bind_mono_arr(c, &w->cd, np1); }
    if (st == SRMECH_OK) { st = elb_er_bind_ratio(c, &w->ratio, np1, np1); }
    if (st == SRMECH_OK) { st = elb_er_bind_scr(c, &w->scr, np1); }
    return st;
}

/* Build + emit one partial-fraction TERM j. Saves the arena cursor, carves the
 * per-term working set, builds the n+1 num / n+1 den theta args, runs er_build
 * (the EllRatio.__init__ mirror: unit prefactor), emits, then RESTORES the cursor
 * so the next term reuses the memory. */
static srmech_status_t epf_one_term(srmech_ell_ctx_t *c, epf_persist_t *p, size_t n,
                                    size_t j, int psym, srmech_bigint_t *out_coeff_num,
                                    srmech_bigint_t *out_coeff_den, int32_t *out_exps_flat,
                                    size_t out_exps_cap_rows, size_t *out_n_num,
                                    size_t *out_n_den, size_t *row)
{
    epf_work_t w = {0};
    size_t saved = c->pool_cur;
    srmech_status_t st;
    assert(c != NULL && p != NULL && j < n);
    assert(out_n_num != NULL && out_n_den != NULL && row != NULL);
    st = epf_bind_work(c, &w, n);
    if (st == SRMECH_OK) { st = epf_build_num(c, p, n, j, w.num, &w.scr, &w.tmp, &w.tmp2); }
    if (st == SRMECH_OK) { st = epf_build_den(c, p, n, j, w.den, &w.scr, &w.tmp); }
    if (st == SRMECH_OK) { st = elb_mono_set_one(c, &w.one); }
    if (st == SRMECH_OK) {
        st = elb_er_build(c, &w.ratio, &w.one, w.num, n + 1u, w.den, n + 1u, psym,
                          &w.scr, w.cn, n + 1u, w.cd, n + 1u);
    }
    if (st == SRMECH_OK) {
        st = epf_emit(c, &w.ratio, j, out_coeff_num, out_coeff_den, out_exps_flat,
                      out_exps_cap_rows, out_n_num, out_n_den, row);
    }
    c->pool_cur = saved;                                       /* reuse the memory */
    return st;
}

srmech_status_t srmech_elliptic_partial_fraction(size_t n_syms, int psym, size_t n,
                                                 const srmech_bigint_t *x_num,
                                                 const srmech_bigint_t *x_den,
                                                 const int32_t *x_exps,
                                                 const srmech_bigint_t *zs_num,
                                                 const srmech_bigint_t *zs_den,
                                                 const int32_t *zs_exps_flat,
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
    epf_persist_t p = {0};
    size_t j;
    size_t row = 0;
    srmech_status_t st;
    assert(out_n_num != NULL && out_n_den != NULL);
    assert(out_coeff_num != NULL && out_coeff_den != NULL);
    if (out_n_num == NULL || out_n_den == NULL) { return SRMECH_ERR_NULL_ARG; }
    if (out_coeff_num == NULL || out_coeff_den == NULL || out_exps_flat == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n == 0u) { return SRMECH_ERR_NULL_ARG; }        /* >= 1 (Python raises) */
    if (x_num == NULL || x_den == NULL || x_exps == NULL || zs_num == NULL
        || zs_den == NULL || zs_exps_flat == NULL || ys_num == NULL
        || ys_den == NULL || ys_exps_flat == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    c.n_syms = (n_syms == 0u) ? 1u : n_syms;
    c.cap = (coeff_cap < 4u) ? 4u : coeff_cap;
    st = elb_er_arena_init(&c, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    st = epf_bind_persist(&c, &p, n);
    if (st == SRMECH_OK) {
        st = epf_parse(&c, &p, n, x_num, x_den, x_exps, zs_num, zs_den, zs_exps_flat,
                       ys_num, ys_den, ys_exps_flat);
    }
    if (st == SRMECH_OK) { st = epf_prods(&c, &p, n); }
    if (st != SRMECH_OK) { return st; }
    for (j = 0; j < n; j++) {
        st = epf_one_term(&c, &p, n, j, psym, out_coeff_num, out_coeff_den,
                          out_exps_flat, out_exps_cap_rows, out_n_num, out_n_den, &row);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* The minimum `ws_len` BYTES srmech_elliptic_partial_fraction needs for the given
 * shape (n_syms symbols, n the term count, coeff_limbs the per-coefficient
 * significant-limb estimate). Sized to the inputs -- no compiled-in cap; if RAM
 * balloons the caller mis-encoded the fiber. The persistent head (x + zs[n] +
 * ys[n] + prodz + prody + yz + tmp + setup scr) plus ONE term's working set (the
 * per-term buffers reuse memory across j via the saved/restored cursor). */
size_t srmech_elliptic_partial_fraction_ws_bound(size_t n_syms, size_t n,
                                                 size_t coeff_limbs)
{
    size_t cap = (coeff_limbs < 4u) ? 4u : coeff_limbs;
    size_t ns = (n_syms == 0u) ? 1u : n_syms;
    size_t nn = (n == 0u) ? 1u : n;
    size_t np1 = nn + 1u;
    size_t mw = elb_er_mono_words(cap, ns);
    /* persistent: x + zs[n] + ys[n] + prodz + prody + yz + tmp. */
    size_t persist = (2u * nn + 4u) * mw
                     + SRMECH_ELL_ER_SCR_MONOS * mw   /* setup scr.pm            */
                     + np1 + 3u * cap + 64u;          /* setup scr flags + bigints */
    /* per-term: one + tmp + tmp2 + num[np1] + den[np1] + cn[np1] + cd[np1]. */
    size_t term = (3u + 4u * np1) * mw
                  + (mw + 2u * np1 * mw)              /* ratio (pref + num + den) */
                  + SRMECH_ELL_ER_SCR_MONOS * mw      /* scr.pm                   */
                  + np1 + 3u * cap + 64u;             /* scr.used flags + bigints */
    size_t scratch_words = cap * 16u + 512u;
    size_t total = persist + term + scratch_words + 2048u;
    assert(cap >= 4u);
    assert(total >= scratch_words);
    return total * sizeof(uint32_t);
}
