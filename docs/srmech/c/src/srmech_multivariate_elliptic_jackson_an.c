/*
 * srmech_multivariate_elliptic_jackson_an.c -- the 1:1 native C peer of
 * srmech.apokatastasis.elliptic_jackson_an.multivariate_elliptic_jackson_an (rc227),
 * the eq-6 An elliptic Jackson summation reducer: the type-A member of the
 * multivariable (root-system) elliptic reduction row.
 *
 * A C-MIRROR PARITY build (NOT a new algorithm): it constructs the EXACT
 * closed form the already-shipped pure-Python op builds, byte-for-byte.
 *
 * For the variables z_1..z_n, the parameters a_1..a_{n+1}, the base q and the
 * balancing w = z_1..z_n * a_1..a_{n+1} (Rosengren, "New transformations for
 * elliptic hypergeometric series on the root system An", arXiv:math/0305379v1,
 * Eq. 6 -- the elliptic analogue of Milne's An Jackson summation; PDF sha256
 * 299d2738c4539a390a437c795a0b0084a5c82d403566c4f549db39482e3076ce), the An
 * elliptic Jackson summation over the SIMPLEX y_1+..+y_n = N reduces to
 *
 *   PROD_{j=1}^{n+1} (w/a_j)_N / [ PROD_{j=1}^{n} (w*z_j)_N * (q)_N ],
 *
 * with (u)_k = PROD_{i=0}^{k-1} theta(u*q^i) the elliptic shifted factorial.
 * This op CONSTRUCTS the right-hand side as an exact EllRatio: the unit
 * prefactor, the (n+1)*N numerator thetas (w/a_j * q^i) and the (n+1)*N
 * denominator thetas (w*z_j * q^i, plus the (q)_N block q*q^i). The EllRatio
 * constructor (er_build) folds each theta's canonicalize prefactor, cancels
 * matching thetas, sorts the survivors -- so the emitted EllRatio is the
 * canonical value Python returns. The balancing w is COMPUTED (never an input),
 * mirroring the Python op.
 *
 * This is PURE COMPOSITION of the shared srmech_ellbase_* exact-Q monomial
 * algebra (mul / inv) + er_build (the EllRatio.__init__ mirror) -- the same
 * single copy the Cn Jackson / Cauchy-determinant / Lagrange peers ride.
 *
 * Wire form: the interned symbol-table dimension `n_syms` (distinct symbols in
 * the Python sorted-symbol-NAME order); `psym` the interned index of the nome
 * `p` (-1 if absent); the positive ints `N` (simplex ceiling) + `n` (rank);
 * the VARIABLE-ARITY parameter vectors as parallel arrays (the
 * srmech_elliptic_cauchy_determinant convention): `zs_num`/`zs_den` n bigints +
 * `zs_exps_flat` int32[n*n_syms]; `as_num`/`as_den` n+1 bigints +
 * `as_exps_flat` int32[(n+1)*n_syms]; the base monomial q as a (num, den) pair
 * + its int32[n_syms] exponent row. `coeff_cap` is the per-bigint limb cap.
 *
 * Output: the single closed-form EllRatio written flat as a ROW stream (the
 * srmech_multivariate_elliptic_jackson wire form): per emitted monomial ONE
 * row -- its exact-Q coeff into `out_coeff_num`/`out_coeff_den`[row] AND its
 * dense int32[n_syms] exponent row into `out_exps_flat`, in the order: the
 * prefactor row, then `*out_n_num` num-theta rows, then `*out_n_den`
 * den-theta rows. `out_exps_cap_rows` is the caller's row capacity; too small
 * -> SRMECH_ERR_OVERFLOW. N == 0 or n == 0 -> SRMECH_ERR_NULL_ARG (Python
 * raises ValueError); a required NULL pointer -> SRMECH_ERR_NULL_ARG; a
 * too-small arena -> SRMECH_ERR_OVERFLOW.
 *
 * Malloc-free (JPL Rule 3): every working monomial / theta + the bigint
 * scratch is carved from the caller arena `ws`, sized to the input
 * (N, n, n_syms) -- no compiled-in cap. Sign travels in the Class-K coeff
 * branch, never abs()/fabs(). Additive symbol -> ABI unchanged (stays 4).
 * License: MIT.
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

/* The bound persistent buffers: the parsed z[n] / a[n+1] / q, the computed
 * balancing w, the n+1 num bases (w/a_j), the n den bases (w*z_j), and the
 * q^i power ladder (all live for the whole build). */
typedef struct mja_persist {
    srmech_ell_mono_t *z;         /* z[n]                                        */
    srmech_ell_mono_t *a;         /* a[n+1]                                      */
    srmech_ell_mono_t  q;         /* the base q                                  */
    srmech_ell_mono_t  w;         /* the balancing w = PROD z * PROD a           */
    srmech_ell_mono_t *nb;        /* nb[n+1] = w/a_j                             */
    srmech_ell_mono_t *db;        /* db[n]   = w*z_j                             */
    srmech_ell_mono_t *qp;        /* qp[i] = q^i, i = 0..N-1                     */
} mja_persist_t;

/* The working buffers for the single ratio build. */
typedef struct mja_work {
    srmech_ell_mono_t  pref;      /* the unit prefactor                          */
    srmech_ell_mono_t  tmp;       /* general scratch monomial                    */
    srmech_ell_mono_t  tmp2;      /* second scratch (inverse building)           */
    srmech_ell_mono_t *num;       /* the (n+1)*N numerator theta-argument monos  */
    srmech_ell_mono_t *den;       /* the (n+1)*N denominator theta-argument monos */
    srmech_ell_mono_t *cn;        /* er_build canon scratch (num)                */
    srmech_ell_mono_t *cd;        /* er_build canon scratch (den)                */
    elb_ratio_t        ratio;     /* the canonical closed-form EllRatio          */
    elb_scr_t          scr;       /* the er_build scratch bundle                 */
} mja_work_t;

/* Parse one monomial slot from the parallel-array wire (index i of nums/dens +
 * the i-th int32[n_syms] row of exps_flat) into a bound monomial. */
static srmech_status_t mja_parse_one(srmech_ell_ctx_t *c, srmech_ell_mono_t *m,
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

/* Parse the n z-monomials, the n+1 a-monomials and q. */
static srmech_status_t mja_parse(srmech_ell_ctx_t *c, mja_persist_t *p, size_t n,
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
        st = mja_parse_one(c, &p->z[i], zs_num, zs_den, zs_exps_flat, i);
    }
    for (i = 0; (st == SRMECH_OK) && i < n + 1u; i++) {
        st = mja_parse_one(c, &p->a[i], as_num, as_den, as_exps_flat, i);
    }
    if (st == SRMECH_OK) { st = mja_parse_one(c, &p->q, q_num, q_den, q_exps, 0); }
    return st;
}

/* w := PROD_j z_j * PROD_j a_j (the Eq-6 balancing, COMPUTED -- mirrors the
 * Python _balancing_w; the Cn analogue is the computed e). */
static srmech_status_t mja_balancing_w(srmech_ell_ctx_t *c, mja_persist_t *p,
                                       size_t n, elb_scr_t *s,
                                       srmech_ell_mono_t *tmp)
{
    size_t i;
    srmech_status_t st;
    assert(c != NULL && p != NULL && s != NULL);
    assert(tmp != NULL && n >= 1u);
    st = elb_mono_set_one(c, &p->w);
    for (i = 0; (st == SRMECH_OK) && i < n; i++) {
        st = elb_mono_mul(c, tmp, &p->w, &p->z[i], &s->g, &s->t0, &s->t1);
        if (st == SRMECH_OK) { st = elb_mono_copy(c, &p->w, tmp); }
    }
    for (i = 0; (st == SRMECH_OK) && i < n + 1u; i++) {
        st = elb_mono_mul(c, tmp, &p->w, &p->a[i], &s->g, &s->t0, &s->t1);
        if (st == SRMECH_OK) { st = elb_mono_copy(c, &p->w, tmp); }
    }
    return st;
}

/* nb[j] := w / a_j (j = 0..n) and db[j] := w * z_j (j = 0..n-1); qp[i] := q^i. */
static srmech_status_t mja_bases(srmech_ell_ctx_t *c, mja_persist_t *p, size_t N,
                                 size_t n, elb_scr_t *s, srmech_ell_mono_t *tmp)
{
    size_t i;
    srmech_status_t st = SRMECH_OK;
    assert(c != NULL && p != NULL && s != NULL);
    assert(tmp != NULL && N >= 1u && n >= 1u);
    for (i = 0; (st == SRMECH_OK) && i < n + 1u; i++) {
        st = elb_mono_inv(c, tmp, &p->a[i]);
        if (st == SRMECH_OK) {
            st = elb_mono_mul(c, &p->nb[i], &p->w, tmp, &s->g, &s->t0, &s->t1);
        }
    }
    for (i = 0; (st == SRMECH_OK) && i < n; i++) {
        st = elb_mono_mul(c, &p->db[i], &p->w, &p->z[i], &s->g, &s->t0, &s->t1);
    }
    if (st == SRMECH_OK) { st = elb_mono_set_one(c, &p->qp[0]); }
    for (i = 1u; (st == SRMECH_OK) && i < N; i++) {
        st = elb_mono_mul(c, &p->qp[i], &p->qp[i - 1u], &p->q, &s->g, &s->t0, &s->t1);
    }
    return st;
}

/* Fill the num side: for j = 0..n, i = 0..N-1 the theta arg nb[j]*q^i; and the
 * den side: for j = 0..n-1 the arg db[j]*q^i, then the (q)_N block q*q^i. Each
 * side is exactly (n+1)*N args (order-free: er_build canonicalizes + sorts). */
static srmech_status_t mja_fill(srmech_ell_ctx_t *c, mja_persist_t *p, size_t N,
                                size_t n, mja_work_t *w)
{
    size_t j;
    size_t i;
    size_t mn = 0;
    size_t md = 0;
    elb_scr_t *s = &w->scr;
    srmech_status_t st = SRMECH_OK;
    assert(c != NULL && p != NULL && w != NULL);
    assert(N >= 1u && n >= 1u);
    for (j = 0; (st == SRMECH_OK) && j < n + 1u; j++) {
        for (i = 0; (st == SRMECH_OK) && i < N; i++) {
            st = elb_mono_mul(c, &w->num[mn], &p->nb[j], &p->qp[i],
                              &s->g, &s->t0, &s->t1);
            mn++;
        }
    }
    for (j = 0; (st == SRMECH_OK) && j < n; j++) {
        for (i = 0; (st == SRMECH_OK) && i < N; i++) {
            st = elb_mono_mul(c, &w->den[md], &p->db[j], &p->qp[i],
                              &s->g, &s->t0, &s->t1);
            md++;
        }
    }
    for (i = 0; (st == SRMECH_OK) && i < N; i++) {           /* (q)_N: q * q^i  */
        st = elb_mono_mul(c, &w->den[md], &p->q, &p->qp[i], &s->g, &s->t0, &s->t1);
        md++;
    }
    assert((st != SRMECH_OK) || (mn == (n + 1u) * N && md == (n + 1u) * N));
    return st;
}

/* Copy one monomial into the output row stream at *row (coeff + dense exps). */
static srmech_status_t mja_emit_mono(srmech_ell_ctx_t *c, const srmech_ell_mono_t *m,
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

/* Emit the canonical EllRatio as a row stream: prefactor, num rows, den rows. */
static srmech_status_t mja_emit_ratio(srmech_ell_ctx_t *c, const elb_ratio_t *r,
                                      srmech_bigint_t *out_num, srmech_bigint_t *out_den,
                                      int32_t *out_exps, size_t out_cap_rows,
                                      size_t *out_n_num, size_t *out_n_den, size_t *row)
{
    size_t i;
    srmech_status_t st;
    assert(c != NULL && r != NULL && row != NULL);
    assert(out_n_num != NULL && out_n_den != NULL);
    if (1u + r->n_num + r->n_den > out_cap_rows) { return SRMECH_ERR_OVERFLOW; }
    st = mja_emit_mono(c, &r->pref, out_num, out_den, out_exps, row);
    if (st != SRMECH_OK) { return st; }
    for (i = 0; i < r->n_num; i++) {
        st = mja_emit_mono(c, &r->num[i], out_num, out_den, out_exps, row);
        if (st != SRMECH_OK) { return st; }
    }
    for (i = 0; i < r->n_den; i++) {
        st = mja_emit_mono(c, &r->den[i], out_num, out_den, out_exps, row);
        if (st != SRMECH_OK) { return st; }
    }
    *out_n_num = r->n_num;
    *out_n_den = r->n_den;
    return SRMECH_OK;
}

/* Carve the persistent buffers (z[n] + a[n+1] + q + w + nb[n+1] + db[n] + qp[N]). */
static srmech_status_t mja_bind_persist(srmech_ell_ctx_t *c, mja_persist_t *p,
                                        size_t N, size_t n)
{
    srmech_status_t st;
    assert(c != NULL && p != NULL);
    assert(N >= 1u && n >= 1u && c->n_syms >= 1u);
    st = elb_bind_mono_arr(c, &p->z, n);
    if (st == SRMECH_OK) { st = elb_bind_mono_arr(c, &p->a, n + 1u); }
    if (st == SRMECH_OK) { st = elb_bind_mono(c, &p->q); }
    if (st == SRMECH_OK) { st = elb_bind_mono(c, &p->w); }
    if (st == SRMECH_OK) { st = elb_bind_mono_arr(c, &p->nb, n + 1u); }
    if (st == SRMECH_OK) { st = elb_bind_mono_arr(c, &p->db, n); }
    if (st == SRMECH_OK) { st = elb_bind_mono_arr(c, &p->qp, N); }
    return st;
}

/* Carve the working buffers (pref + 2 tmp + num/den/cn/cd[nt] + ratio + scr). */
static srmech_status_t mja_bind_work(srmech_ell_ctx_t *c, mja_work_t *w, size_t nt)
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

/* Reject a NULL required pointer (kept out of the main body for the JPL line cap). */
static int mja_has_null(const srmech_bigint_t *zs_num, const srmech_bigint_t *zs_den,
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

srmech_status_t srmech_multivariate_elliptic_jackson_an(
    size_t n_syms, int psym, size_t N, size_t n,
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
    mja_persist_t p = {0};
    mja_work_t w = {0};
    size_t nt;
    size_t row = 0;
    srmech_status_t st;
    assert(out_n_num != NULL && out_n_den != NULL);
    assert(out_coeff_num != NULL && out_coeff_den != NULL);
    if (out_n_num == NULL || out_n_den == NULL) { return SRMECH_ERR_NULL_ARG; }
    if (N == 0u || n == 0u) { return SRMECH_ERR_NULL_ARG; }  /* >= 1 (Python raises) */
    if (mja_has_null(zs_num, zs_den, zs_exps_flat, as_num, as_den, as_exps_flat,
                     q_num, q_den, q_exps, out_coeff_num, out_coeff_den,
                     out_exps_flat)) {
        return SRMECH_ERR_NULL_ARG;
    }
    ec.n_syms = (n_syms == 0u) ? 1u : n_syms;
    ec.cap = (coeff_cap < 4u) ? 4u : coeff_cap;
    nt = (n + 1u) * N;
    st = elb_er_arena_init(&ec, ws, ws_len);
    if (st == SRMECH_OK) { st = mja_bind_persist(&ec, &p, N, n); }
    if (st == SRMECH_OK) { st = mja_bind_work(&ec, &w, nt); }
    if (st == SRMECH_OK) {
        st = mja_parse(&ec, &p, n, zs_num, zs_den, zs_exps_flat, as_num, as_den,
                       as_exps_flat, q_num, q_den, q_exps);
    }
    if (st == SRMECH_OK) { st = mja_balancing_w(&ec, &p, n, &w.scr, &w.tmp); }
    if (st == SRMECH_OK) { st = mja_bases(&ec, &p, N, n, &w.scr, &w.tmp); }
    if (st == SRMECH_OK) { st = elb_mono_set_one(&ec, &w.pref); }
    if (st == SRMECH_OK) { st = mja_fill(&ec, &p, N, n, &w); }
    if (st == SRMECH_OK) {
        st = elb_er_build(&ec, &w.ratio, &w.pref, w.num, nt, w.den, nt, psym,
                          &w.scr, w.cn, nt, w.cd, nt);
    }
    if (st == SRMECH_OK) {
        st = mja_emit_ratio(&ec, &w.ratio, out_coeff_num, out_coeff_den,
                            out_exps_flat, out_exps_cap_rows, out_n_num,
                            out_n_den, &row);
    }
    return st;
}

/* The minimum `ws_len` BYTES srmech_multivariate_elliptic_jackson_an needs for
 * the given shape (n_syms symbols, N the simplex ceiling, n the rank,
 * coeff_limbs the per-coefficient significant-limb estimate). Sized to the
 * inputs -- no compiled-in cap. The persistent head (z[n] + a[n+1] + q + w +
 * nb[n+1] + db[n] + qp[N]) plus the single ratio's working set, nt = (n+1)*N. */
size_t srmech_multivariate_elliptic_jackson_an_ws_bound(size_t n_syms, size_t N,
                                                        size_t n, size_t coeff_limbs)
{
    size_t cap = (coeff_limbs < 4u) ? 4u : coeff_limbs;
    size_t ns = (n_syms == 0u) ? 1u : n_syms;
    size_t NN = (N == 0u) ? 1u : N;
    size_t nn = (n == 0u) ? 1u : n;
    size_t nt = (nn + 1u) * NN;
    size_t mw = elb_er_mono_words(cap, ns);
    /* persistent: z[nn] + a[nn+1] + q + w + nb[nn+1] + db[nn] + qp[NN]. */
    size_t persist = (4u * nn + NN + 4u) * mw;
    /* per-build: pref + 2 tmp + num[nt] + den[nt] + cn[nt] + cd[nt]. */
    size_t work = (3u + 4u * nt) * mw
                  + (mw + 2u * nt * mw)             /* ratio (pref + num + den) */
                  + SRMECH_ELL_ER_SCR_MONOS * mw    /* scr.pm                   */
                  + nt + 3u * cap + 64u;            /* scr.used flags + bigints */
    size_t scratch_words = cap * 16u + 512u;
    size_t total = persist + work + scratch_words + 4096u;
    assert(cap >= 4u);
    assert(total >= scratch_words);
    return total * sizeof(uint32_t);
}
