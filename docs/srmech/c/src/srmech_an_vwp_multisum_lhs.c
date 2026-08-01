/*
 * srmech_an_vwp_multisum_lhs.c -- the 1:1 native C peer of
 * srmech.apokatastasis.elliptic_jackson_an.an_vwp_multisum_lhs (rc227), the SYMBOLIC An
 * elliptic multisum LHS builder: the exact ThetaSum construction of the
 * LEFT-hand side of the An (type-A / Milne) elliptic Jackson summation.
 *
 * A C-MIRROR PARITY build (NOT a new algorithm): it constructs the EXACT
 * per-composition theta-quotient TERMS the already-shipped pure-Python
 * _an_lhs_thetasum builds, byte-for-byte; the Python side SUMS them into the
 * ThetaSum (there is NO ThetaSum-CONSTRUCTION C surface, so the peer returns
 * the per-composition EllRatio TERMS as a row stream, exactly like
 * srmech_cn_vwp_multisum_lhs returns its per-partition terms).
 *
 * The identity whose LHS this builds (MPM-verified at build from the extracted
 * PDF, sha256 299d2738c4539a390a437c795a0b0084a5c82d403566c4f549db39482e3076ce:
 * Hjalmar Rosengren, "New transformations for elliptic hypergeometric series on
 * the root system An", arXiv:math/0305379v1 [math.CA] (27 May 2003), Eq. 6 --
 * the elliptic analogue of Milne's An Jackson summation): over the SIMPLEX
 * y_1..y_n >= 0 with y_1+..+y_n = N, with w = z_1..z_n * a_1..a_{n+1} the
 * COMPUTED balancing,
 *
 *   SUM_{|y|=N} Delta(z q^y)/Delta(z)
 *     * PROD_{k=1}^n [ PROD_{j=1}^{n+1} (a_j z_k)_{y_k} ]
 *                    / [ (w z_k)_{y_k} PROD_{j=1}^n (q z_k/z_j)_{y_k} ]
 *   = PROD_{j=1}^{n+1} (w/a_j)_N / [ PROD_{j=1}^n (w z_j)_N (q)_N ],
 *
 * with (u)_k = PROD_{i=0}^{k-1} E(u q^i) the theta-Pochhammer (E the modified
 * theta) and the type-A Vandermonde ratio
 *   Delta(z q^y)/Delta(z)
 *     = PROD_{1<=j<k<=n} q^{y_j} E(z_k q^{y_k}/(z_j q^{y_j})) / E(z_k/z_j),
 * whose monomial part PROD_{j<k} q^{y_j} = q^{SUM_j (n-j) y_j} travels in the
 * per-term EllRatio PREFACTOR (the Class-K coeff/monomial branch, never abs()).
 * Each composition's summand is one EllRatio; er_build (the EllRatio.__init__
 * mirror) folds each theta's canonicalize prefactor, cancels matching thetas,
 * sorts the survivors -- so each emitted EllRatio is the canonical value Python
 * returns. The RHS closed form is the separate
 * srmech_multivariate_elliptic_jackson_an peer; LHS - RHS |> is_zero is the
 * per-call proof.
 *
 * This is PURE COMPOSITION of the shared srmech_ellbase_* exact-Q monomial
 * algebra (mul / inv) + er_build -- the same single copy the Cn multisum /
 * partial-fraction / Cauchy-determinant peers ride.
 *
 * Wire form: the interned symbol-table dimension `n_syms` (distinct symbols in
 * the Python sorted-symbol-NAME order); `psym` the interned index of the nome
 * `p` (-1 if absent); the positive ints `N` (simplex ceiling) + `n` (rank) +
 * `n_terms` (the composition count C(N+n-1, n-1), computed by the caller); the
 * VARIABLE-ARITY vectors as parallel arrays (the elliptic_cauchy_determinant
 * convention): `zs_num`/`zs_den` n bigints + `zs_exps_flat` int32[n*n_syms];
 * `as_num`/`as_den` n+1 bigints + `as_exps_flat` int32[(n+1)*n_syms]; q as a
 * (num, den) pair + its int32[n_syms] row. `coeff_cap` is the per-bigint limb
 * cap.
 *
 * Output: the n_terms TERM EllRatios written out flat in the ASCENDING
 * LEXICOGRAPHIC composition order ((0,..,0,N) first, (N,0,..,0) last; the
 * exact order the Python builder's filtered itertools.product enumerates) --
 * per term t, `out_n_num[t]` / `out_n_den[t]` the survivor theta counts, and
 * the canonical rows appended to out_coeff_num/out_coeff_den/out_exps_flat
 * (per term: its prefactor row, then its num rows, then its den rows; each row
 * carries its exact-Q coeff AND its dense int32[n_syms] exponent row).
 * `out_exps_cap_rows` is the row capacity of the caller's buffers; too small
 * -> SRMECH_ERR_OVERFLOW. N == 0, n == 0 or n_terms == 0 ->
 * SRMECH_ERR_NULL_ARG (Python raises ValueError); a wrong n_terms (not
 * C(N+n-1, n-1)) -> SRMECH_ERR_BAD_INPUT; a required NULL pointer ->
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

/* The bound persistent buffers: the parsed z[n] / a[n+1] / q, the z inverses,
 * the computed balancing w, the y-independent theta bases (a_j*z_k, w*z_k,
 * q*z_k/z_j, z_k/z_j), the q^i / q^{-i} ladders, and the composition odometer
 * (all live for the whole build). */
typedef struct avl_persist {
    srmech_ell_mono_t *z;         /* z[n]                                        */
    srmech_ell_mono_t *zi;        /* zi[j] = z_j^{-1}                            */
    srmech_ell_mono_t *a;         /* a[n+1]                                      */
    srmech_ell_mono_t  q;         /* the base q                                  */
    srmech_ell_mono_t  w;         /* the balancing w = PROD z * PROD a           */
    srmech_ell_mono_t *azb;       /* azb[j*n + k] = a_j * z_k  (j=0..n, k=0..n-1) */
    srmech_ell_mono_t *wzb;       /* wzb[k] = w * z_k                            */
    srmech_ell_mono_t *qzz;       /* qzz[k*n + j] = q * z_k / z_j                */
    srmech_ell_mono_t *dzz;       /* dzz[pair] = z_k / z_j for j < k (loop order) */
    srmech_ell_mono_t *qp;        /* qp[i] = q^i,    i = 0..N                    */
    srmech_ell_mono_t *qn;        /* qn[i] = q^{-i}, i = 0..N                    */
    srmech_ell_mono_t  tmp;       /* setup scratch monomial                      */
    elb_scr_t          scr;       /* setup scratch bundle (g/t0/t1 for muls)     */
    uint32_t          *y;         /* the composition odometer y_1..y_n           */
} avl_persist_t;

/* The per-term working buffers (carved fresh from a reset cursor each term). */
typedef struct avl_work {
    srmech_ell_mono_t  pref;      /* the accumulated monomial prefactor          */
    srmech_ell_mono_t  tmp;       /* general scratch monomial                    */
    srmech_ell_mono_t  tmp2;      /* second scratch (prefactor accumulate)       */
    srmech_ell_mono_t *num;       /* the numerator theta-argument monomials      */
    srmech_ell_mono_t *den;       /* the denominator theta-argument monomials    */
    srmech_ell_mono_t *cn;        /* er_build canon scratch (num)                */
    srmech_ell_mono_t *cd;        /* er_build canon scratch (den)                */
    elb_ratio_t        ratio;     /* the canonical term EllRatio                 */
    elb_scr_t          scr;       /* the er_build scratch bundle                 */
} avl_work_t;

/* The per-side MAX theta count of one composition summand: n(n-1)/2 Vandermonde
 * args + (n+1)*N theta-Pochhammer factors (num: SUM_k (n+1) y_k; den:
 * SUM_k (1 + n) y_k -- both (n+1)*N). Mirrors the Python _max_thetas_per_side. */
static size_t avl_nt_max(size_t N, size_t n)
{
    size_t nt;
    assert(N >= 1u);
    assert(n >= 1u);
    nt = (n * (n - 1u)) / 2u + (n + 1u) * N;
    return nt;
}

/* Parse one monomial slot from the parallel-array wire. */
static srmech_status_t avl_parse_one(srmech_ell_ctx_t *c, srmech_ell_mono_t *m,
                                     const srmech_bigint_t *nums,
                                     const srmech_bigint_t *dens,
                                     const int32_t *exps_flat, size_t i)
{
    srmech_status_t st;
    assert(c != NULL && m != NULL);
    assert(nums != NULL && dens != NULL && exps_flat != NULL);
    st = srmech_bigint_copy(&m->coeff.num, &nums[i]);
    if (st == SRMECH_OK) { st = srmech_bigint_copy(&m->coeff.den, &dens[i]); }
    if (st != SRMECH_OK) { return st; }
    memcpy(m->exps, exps_flat + i * c->n_syms, c->n_syms * sizeof(int32_t));
    return SRMECH_OK;
}

/* Parse the n z-monomials (+ their inverses), the n+1 a-monomials and q. */
static srmech_status_t avl_parse(srmech_ell_ctx_t *c, avl_persist_t *p, size_t n,
                                 const srmech_bigint_t *zs_num,
                                 const srmech_bigint_t *zs_den,
                                 const int32_t *zs_exps_flat,
                                 const srmech_bigint_t *as_num,
                                 const srmech_bigint_t *as_den,
                                 const int32_t *as_exps_flat,
                                 const srmech_bigint_t *q_num,
                                 const srmech_bigint_t *q_den,
                                 const int32_t *q_exps)
{
    size_t i;
    srmech_status_t st = SRMECH_OK;
    assert(c != NULL && p != NULL);
    assert(n >= 1u);
    for (i = 0; (st == SRMECH_OK) && i < n; i++) {
        st = avl_parse_one(c, &p->z[i], zs_num, zs_den, zs_exps_flat, i);
        if (st == SRMECH_OK) { st = elb_mono_inv(c, &p->zi[i], &p->z[i]); }
    }
    for (i = 0; (st == SRMECH_OK) && i < n + 1u; i++) {
        st = avl_parse_one(c, &p->a[i], as_num, as_den, as_exps_flat, i);
    }
    if (st == SRMECH_OK) { st = avl_parse_one(c, &p->q, q_num, q_den, q_exps, 0); }
    return st;
}

/* w := PROD_j z_j * PROD_j a_j (the Eq-6 balancing, COMPUTED). */
static srmech_status_t avl_balancing_w(srmech_ell_ctx_t *c, avl_persist_t *p,
                                       size_t n)
{
    size_t i;
    elb_scr_t *s = &p->scr;
    srmech_status_t st;
    assert(c != NULL && p != NULL);
    assert(n >= 1u);
    st = elb_mono_set_one(c, &p->w);
    for (i = 0; (st == SRMECH_OK) && i < n; i++) {
        st = elb_mono_mul(c, &p->tmp, &p->w, &p->z[i], &s->g, &s->t0, &s->t1);
        if (st == SRMECH_OK) { st = elb_mono_copy(c, &p->w, &p->tmp); }
    }
    for (i = 0; (st == SRMECH_OK) && i < n + 1u; i++) {
        st = elb_mono_mul(c, &p->tmp, &p->w, &p->a[i], &s->g, &s->t0, &s->t1);
        if (st == SRMECH_OK) { st = elb_mono_copy(c, &p->w, &p->tmp); }
    }
    return st;
}

/* The y-independent theta bases: azb[j*n+k] = a_j*z_k, wzb[k] = w*z_k,
 * qzz[k*n+j] = q*z_k*zi[j], dzz[pair] = z_k*zi[j] for j<k in loop order
 * (j = 1..n outer, k = j+1..n inner -- the Python pair order). */
static srmech_status_t avl_bases(srmech_ell_ctx_t *c, avl_persist_t *p, size_t n)
{
    size_t j;
    size_t k;
    size_t pair = 0;
    elb_scr_t *s = &p->scr;
    srmech_status_t st = SRMECH_OK;
    assert(c != NULL && p != NULL);
    assert(n >= 1u);
    for (j = 0; (st == SRMECH_OK) && j < n + 1u; j++) {
        for (k = 0; (st == SRMECH_OK) && k < n; k++) {
            st = elb_mono_mul(c, &p->azb[j * n + k], &p->a[j], &p->z[k],
                              &s->g, &s->t0, &s->t1);
        }
    }
    for (k = 0; (st == SRMECH_OK) && k < n; k++) {
        st = elb_mono_mul(c, &p->wzb[k], &p->w, &p->z[k], &s->g, &s->t0, &s->t1);
    }
    for (k = 0; (st == SRMECH_OK) && k < n; k++) {
        for (j = 0; (st == SRMECH_OK) && j < n; j++) {
            st = elb_mono_mul(c, &p->tmp, &p->z[k], &p->zi[j], &s->g, &s->t0, &s->t1);
            if (st == SRMECH_OK) {
                st = elb_mono_mul(c, &p->qzz[k * n + j], &p->q, &p->tmp,
                                  &s->g, &s->t0, &s->t1);
            }
        }
    }
    for (j = 0; (st == SRMECH_OK) && j + 1u < n; j++) {
        for (k = j + 1u; (st == SRMECH_OK) && k < n; k++) {
            st = elb_mono_mul(c, &p->dzz[pair], &p->z[k], &p->zi[j],
                              &s->g, &s->t0, &s->t1);
            pair++;
        }
    }
    assert((st != SRMECH_OK) || (pair == (n * (n - 1u)) / 2u));
    return st;
}

/* qp[i] := q^i and qn[i] := q^{-i} (i = 0..N). */
static srmech_status_t avl_ladders(srmech_ell_ctx_t *c, avl_persist_t *p, size_t N)
{
    size_t i;
    elb_scr_t *s = &p->scr;
    srmech_status_t st;
    assert(c != NULL && p != NULL);
    assert(N >= 1u);
    st = elb_mono_set_one(c, &p->qp[0]);
    for (i = 1u; (st == SRMECH_OK) && i <= N; i++) {
        st = elb_mono_mul(c, &p->qp[i], &p->qp[i - 1u], &p->q, &s->g, &s->t0, &s->t1);
    }
    if (st == SRMECH_OK) { st = elb_mono_inv(c, &p->tmp, &p->q); }
    if (st == SRMECH_OK) { st = elb_mono_set_one(c, &p->qn[0]); }
    for (i = 1u; (st == SRMECH_OK) && i <= N; i++) {
        st = elb_mono_mul(c, &p->qn[i], &p->qn[i - 1u], &p->tmp, &s->g, &s->t0, &s->t1);
    }
    return st;
}

/* Append the theta-Pochhammer (base)_k to dest at *m: the k theta args
 * base*q^t, t = 0..k-1 (the Python poch_thetas). Advances *m. */
static srmech_status_t avl_poch(srmech_ell_ctx_t *c, avl_persist_t *p,
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

/* The Vandermonde-ratio part of one summand: per pair j < k (0-based), the num
 * theta arg dzz[pair]*q^{y_k - y_j} and the den theta arg dzz[pair]; the
 * monomial part q^{y_j} per pair accumulated into w->pref. */
static srmech_status_t avl_vandermonde(srmech_ell_ctx_t *c, avl_persist_t *p,
                                       size_t n, avl_work_t *w, size_t *mn,
                                       size_t *md)
{
    size_t j;
    size_t k;
    size_t pair = 0;
    elb_scr_t *s = &w->scr;
    srmech_status_t st = SRMECH_OK;
    assert(c != NULL && p != NULL && w != NULL);
    assert(mn != NULL && md != NULL && n >= 1u);
    for (j = 0; (st == SRMECH_OK) && j + 1u < n; j++) {
        for (k = j + 1u; (st == SRMECH_OK) && k < n; k++) {
            uint32_t yj = p->y[j];
            uint32_t yk = p->y[k];
            const srmech_ell_mono_t *qd = (yk >= yj) ? &p->qp[yk - yj]
                                                     : &p->qn[yj - yk];
            st = elb_mono_mul(c, &w->num[*mn], &p->dzz[pair], qd,
                              &s->g, &s->t0, &s->t1);
            if (st == SRMECH_OK) {
                (*mn)++;
                st = elb_mono_copy(c, &w->den[*md], &p->dzz[pair]);
                (*md)++;
            }
            if (st == SRMECH_OK) {                     /* pref *= q^{y_j}        */
                st = elb_mono_mul(c, &w->tmp2, &w->pref, &p->qp[yj],
                                  &s->g, &s->t0, &s->t1);
            }
            if (st == SRMECH_OK) { st = elb_mono_copy(c, &w->pref, &w->tmp2); }
            pair++;
        }
    }
    assert((st != SRMECH_OK) || (pair == (n * (n - 1u)) / 2u));
    return st;
}

/* The theta-Pochhammer part of one summand: per k, the n+1 num Pochhammers
 * (a_j z_k)_{y_k}, the den Pochhammer (w z_k)_{y_k} and the n den Pochhammers
 * (q z_k/z_j)_{y_k}. */
static srmech_status_t avl_poch_blocks(srmech_ell_ctx_t *c, avl_persist_t *p,
                                       size_t n, avl_work_t *w, size_t *mn,
                                       size_t *md)
{
    size_t k;
    size_t j;
    elb_scr_t *s = &w->scr;
    srmech_status_t st = SRMECH_OK;
    assert(c != NULL && p != NULL && w != NULL);
    assert(mn != NULL && md != NULL && n >= 1u);
    for (k = 0; (st == SRMECH_OK) && k < n; k++) {
        size_t yk = (size_t)p->y[k];
        for (j = 0; (st == SRMECH_OK) && j < n + 1u; j++) {
            st = avl_poch(c, p, &p->azb[j * n + k], yk, w->num, mn, s);
        }
        if (st == SRMECH_OK) { st = avl_poch(c, p, &p->wzb[k], yk, w->den, md, s); }
        for (j = 0; (st == SRMECH_OK) && j < n; j++) {
            st = avl_poch(c, p, &p->qzz[k * n + j], yk, w->den, md, s);
        }
    }
    return st;
}

/* Copy one monomial into the output row stream at *row (coeff + dense exps). */
static srmech_status_t avl_emit_mono(srmech_ell_ctx_t *c, const srmech_ell_mono_t *m,
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
 * out_n_num/den[term], and the monomial rows (prefactor, num, den) at *row. */
static srmech_status_t avl_emit(srmech_ell_ctx_t *c, const elb_ratio_t *r, size_t term,
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
    st = avl_emit_mono(c, &r->pref, out_coeff_num, out_coeff_den, out_exps_flat, row);
    if (st != SRMECH_OK) { return st; }
    for (i = 0; i < r->n_num; i++) {
        st = avl_emit_mono(c, &r->num[i], out_coeff_num, out_coeff_den,
                           out_exps_flat, row);
        if (st != SRMECH_OK) { return st; }
    }
    for (i = 0; i < r->n_den; i++) {
        st = avl_emit_mono(c, &r->den[i], out_coeff_num, out_coeff_den,
                           out_exps_flat, row);
        if (st != SRMECH_OK) { return st; }
    }
    out_n_num[term] = r->n_num;
    out_n_den[term] = r->n_den;
    return SRMECH_OK;
}

/* Advance the composition odometer y to the ASCENDING-LEX successor among the
 * sum-N tuples in {0..N}^n (the exact order the Python builder's filtered
 * itertools.product enumerates: (0,..,0,N) first, (N,0,..,0) last). Find the
 * RIGHTMOST positive index t; if t == 0 the odometer is exhausted; else
 * increment y[t-1], zero y[t..n-1], and put the remaining sum y_old[t] - 1
 * into the last slot. Returns 1 if advanced, 0 if y was the last composition. */
static int avl_next_composition(uint32_t *y, size_t n)
{
    size_t t;
    size_t u;
    uint32_t rem;
    assert(y != NULL);
    assert(n >= 1u);
    t = n;
    while (t > 0u && y[t - 1u] == 0u) { t--; }
    if (t <= 1u) { return 0; }              /* all-zero tail or t==1: exhausted */
    rem = y[t - 1u] - 1u;                   /* the tail sum after the increment */
    y[t - 2u] += 1u;
    for (u = t - 1u; u < n; u++) { y[u] = 0u; }
    y[n - 1u] = rem;
    return 1;
}

/* Carve the persistent buffers. */
static srmech_status_t avl_bind_persist(srmech_ell_ctx_t *c, avl_persist_t *p,
                                        size_t N, size_t n)
{
    size_t k;
    srmech_status_t st;
    assert(c != NULL && p != NULL);
    assert(N >= 1u && n >= 1u && c->n_syms >= 1u);
    st = elb_bind_mono_arr(c, &p->z, n);
    if (st == SRMECH_OK) { st = elb_bind_mono_arr(c, &p->zi, n); }
    if (st == SRMECH_OK) { st = elb_bind_mono_arr(c, &p->a, n + 1u); }
    if (st == SRMECH_OK) { st = elb_bind_mono(c, &p->q); }
    if (st == SRMECH_OK) { st = elb_bind_mono(c, &p->w); }
    if (st == SRMECH_OK) { st = elb_bind_mono_arr(c, &p->azb, (n + 1u) * n); }
    if (st == SRMECH_OK) { st = elb_bind_mono_arr(c, &p->wzb, n); }
    if (st == SRMECH_OK) { st = elb_bind_mono_arr(c, &p->qzz, n * n); }
    if (st == SRMECH_OK) {
        st = elb_bind_mono_arr(c, &p->dzz, (n * (n - 1u)) / 2u + 1u);
    }
    if (st == SRMECH_OK) { st = elb_bind_mono_arr(c, &p->qp, N + 1u); }
    if (st == SRMECH_OK) { st = elb_bind_mono_arr(c, &p->qn, N + 1u); }
    if (st == SRMECH_OK) { st = elb_bind_mono(c, &p->tmp); }
    if (st == SRMECH_OK) { st = elb_er_bind_scr(c, &p->scr, 4u); }
    if (st != SRMECH_OK) { return st; }
    p->y = srmech_ellbase_take_words(c, n);
    if (p->y == NULL) { return SRMECH_ERR_OVERFLOW; }
    for (k = 0; k < n; k++) { p->y[k] = 0u; }
    p->y[n - 1u] = (uint32_t)N;             /* the ascending-lex first composition */
    return SRMECH_OK;
}

/* Carve the per-term working buffers from the CURRENT cursor (caller restores). */
static srmech_status_t avl_bind_work(srmech_ell_ctx_t *c, avl_work_t *w, size_t nt)
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

/* Build + emit ONE composition summand `term`. Saves the arena cursor, carves
 * the per-term working set, builds the prefactor + num/den theta args
 * (Vandermonde ratio, then the Pochhammer blocks), runs er_build, emits, then
 * RESTORES the cursor so the next term reuses the memory. */
static srmech_status_t avl_one_term(srmech_ell_ctx_t *c, avl_persist_t *p, size_t n,
                                    size_t nt, size_t term, int psym,
                                    srmech_bigint_t *out_coeff_num,
                                    srmech_bigint_t *out_coeff_den,
                                    int32_t *out_exps_flat, size_t out_exps_cap_rows,
                                    size_t *out_n_num, size_t *out_n_den, size_t *row)
{
    avl_work_t w = {0};
    size_t saved = c->pool_cur;
    size_t mn = 0;
    size_t md = 0;
    srmech_status_t st;
    assert(c != NULL && p != NULL && row != NULL);
    assert(out_n_num != NULL && out_n_den != NULL && n >= 1u);
    st = avl_bind_work(c, &w, nt);
    if (st == SRMECH_OK) { st = elb_mono_set_one(c, &w.pref); }
    if (st == SRMECH_OK) { st = avl_vandermonde(c, p, n, &w, &mn, &md); }
    if (st == SRMECH_OK) { st = avl_poch_blocks(c, p, n, &w, &mn, &md); }
    assert((st != SRMECH_OK) || (mn <= nt && md <= nt));
    if (st == SRMECH_OK) {
        st = elb_er_build(c, &w.ratio, &w.pref, w.num, mn, w.den, md, psym,
                          &w.scr, w.cn, nt, w.cd, nt);
    }
    if (st == SRMECH_OK) {
        st = avl_emit(c, &w.ratio, term, out_coeff_num, out_coeff_den, out_exps_flat,
                      out_exps_cap_rows, out_n_num, out_n_den, row);
    }
    c->pool_cur = saved;                                   /* reuse the memory */
    return st;
}

/* Reject a NULL required pointer (kept out of the main body for the JPL line cap). */
static int avl_has_null(const srmech_bigint_t *zs_num, const srmech_bigint_t *zs_den,
                        const int32_t *zs_exps_flat, const srmech_bigint_t *as_num,
                        const srmech_bigint_t *as_den, const int32_t *as_exps_flat,
                        const srmech_bigint_t *q_num, const srmech_bigint_t *q_den,
                        const int32_t *q_exps, const srmech_bigint_t *out_num,
                        const srmech_bigint_t *out_den, const int32_t *out_exps)
{
    int bad_in;
    int bad_out;
    bad_in = (zs_num == NULL || zs_den == NULL || zs_exps_flat == NULL
              || as_num == NULL || as_den == NULL || as_exps_flat == NULL
              || q_num == NULL || q_den == NULL || q_exps == NULL);
    bad_out = (out_num == NULL || out_den == NULL || out_exps == NULL);
    assert(bad_in == 0 || bad_in == 1);
    assert(bad_out == 0 || bad_out == 1);
    return (bad_in || bad_out) ? 1 : 0;
}

srmech_status_t srmech_an_vwp_multisum_lhs(
    size_t n_syms, int psym, size_t N, size_t n, size_t n_terms,
    const srmech_bigint_t *zs_num, const srmech_bigint_t *zs_den,
    const int32_t *zs_exps_flat,
    const srmech_bigint_t *as_num, const srmech_bigint_t *as_den,
    const int32_t *as_exps_flat,
    const srmech_bigint_t *q_num, const srmech_bigint_t *q_den,
    const int32_t *q_exps, uint32_t coeff_cap,
    srmech_bigint_t *out_coeff_num, srmech_bigint_t *out_coeff_den,
    int32_t *out_exps_flat, size_t out_exps_cap_rows,
    size_t *out_n_num, size_t *out_n_den, void *ws, size_t ws_len)
{
    srmech_ell_ctx_t ec = {0};
    avl_persist_t p = {0};
    size_t nt;
    size_t t;
    size_t row = 0;
    int adv;
    srmech_status_t st;
    assert(out_n_num != NULL && out_n_den != NULL);
    assert(out_coeff_num != NULL && out_coeff_den != NULL);
    if (out_n_num == NULL || out_n_den == NULL) { return SRMECH_ERR_NULL_ARG; }
    if (N == 0u || n == 0u || n_terms == 0u) { return SRMECH_ERR_NULL_ARG; }
    if (avl_has_null(zs_num, zs_den, zs_exps_flat, as_num, as_den, as_exps_flat,
                     q_num, q_den, q_exps, out_coeff_num, out_coeff_den,
                     out_exps_flat)) {
        return SRMECH_ERR_NULL_ARG;
    }
    ec.n_syms = (n_syms == 0u) ? 1u : n_syms;
    ec.cap = (coeff_cap < 4u) ? 4u : coeff_cap;
    nt = avl_nt_max(N, n);
    st = elb_er_arena_init(&ec, ws, ws_len);
    if (st == SRMECH_OK) { st = avl_bind_persist(&ec, &p, N, n); }
    if (st == SRMECH_OK) {
        st = avl_parse(&ec, &p, n, zs_num, zs_den, zs_exps_flat, as_num, as_den,
                       as_exps_flat, q_num, q_den, q_exps);
    }
    if (st == SRMECH_OK) { st = avl_balancing_w(&ec, &p, n); }
    if (st == SRMECH_OK) { st = avl_bases(&ec, &p, n); }
    if (st == SRMECH_OK) { st = avl_ladders(&ec, &p, N); }
    if (st != SRMECH_OK) { return st; }
    for (t = 0; t < n_terms; t++) {
        st = avl_one_term(&ec, &p, n, nt, t, psym, out_coeff_num, out_coeff_den,
                          out_exps_flat, out_exps_cap_rows, out_n_num, out_n_den,
                          &row);
        if (st != SRMECH_OK) { return st; }
        adv = avl_next_composition(p.y, n);
        if ((t + 1u < n_terms) && (adv == 0)) { return SRMECH_ERR_BAD_INPUT; }
        if ((t + 1u == n_terms) && (adv != 0)) { return SRMECH_ERR_BAD_INPUT; }
    }
    return SRMECH_OK;
}

/* The minimum `ws_len` BYTES srmech_an_vwp_multisum_lhs needs for the given
 * shape (n_syms symbols, N the simplex ceiling, n the rank, coeff_limbs the
 * per-coefficient significant-limb estimate). Sized to the inputs -- no
 * compiled-in cap. The persistent head (z[n] + zi[n] + a[n+1] + q + w +
 * azb[(n+1)n] + wzb[n] + qzz[n*n] + dzz[n(n-1)/2+1] + qp[N+1] + qn[N+1] + tmp
 * + setup scr + the y odometer) plus ONE term's working set (the per-term
 * buffers reuse memory across terms via the saved/restored cursor), nt the
 * per-side max theta count. */
size_t srmech_an_vwp_multisum_lhs_ws_bound(size_t n_syms, size_t N, size_t n,
                                           size_t coeff_limbs)
{
    size_t cap = (coeff_limbs < 4u) ? 4u : coeff_limbs;
    size_t ns = (n_syms == 0u) ? 1u : n_syms;
    size_t NN = (N == 0u) ? 1u : N;
    size_t nn = (n == 0u) ? 1u : n;
    size_t nt = avl_nt_max(NN, nn);
    size_t mw = elb_er_mono_words(cap, ns);
    /* persistent monomials: 2nn (z, zi) + (nn+1) (a) + 2 (q, w) + (nn+1)*nn
     * (azb) + nn (wzb) + nn*nn (qzz) + nn(nn-1)/2+1 (dzz) + 2(NN+1) (qp, qn)
     * + 1 (tmp). */
    size_t persist = (2u * nn * nn + (nn * (nn - 1u)) / 2u + 5u * nn
                      + 2u * NN + 7u) * mw
                     + SRMECH_ELL_ER_SCR_MONOS * mw   /* setup scr.pm            */
                     + 4u + 3u * cap + 64u            /* setup scr flags + bigints */
                     + nn + 8u;                       /* the y odometer          */
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
