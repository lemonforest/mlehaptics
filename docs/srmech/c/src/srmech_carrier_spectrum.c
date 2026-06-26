/*
 * srmech_carrier_spectrum.c -- the OPERAND-side dual of the_one (the C peer of
 * srmech.amsc.carrier_spectrum.carrier_spectrum). A 1:1 STRUCTURAL MIRROR of the
 * pure-Python CHANNEL READ -- the harmonic occupancy of a carrier element under the
 * shift-Laplacian, in two orthogonal channels:
 *
 *   Channel 1 (Class-I) -- the cyclic sigma-EIGENSPECTRUM: the distinct x-exponents k
 *     present across the prefactor + every theta argument (sigma(x^k) = q^k x^k diagonal
 *     on monomials; k = 0 the shift-Laplacian L = sigma - 1 kernel / DC mode).
 *   Channel 2 (Class-L) -- the quasi-periodic p-CHARACTER BLOCK of each theta-factor: the
 *     net multiplier monomial the factor acquires under the period shifts x -> p x AND
 *     y -> p y (Rosengren Eq. 1.6, via the shared theta-canonicalization), with the
 *     q-coordinate STRIPPED (sigma traverses only q; the q-stripped class is sigma-
 *     invariant). This is the block LABEL the non-brute-force key-equation solve groups by.
 *
 * Input: the carrier element as a FULL EllRatio wire form (the interned symbol-table
 * dimension n_syms + the x/p/q/y interned indices + the num/den theta counts + the flat
 * exact-Q coeff arrays + the flat int32 exponent rows, in the order prefactor,
 * num0..K-1, den0..L-1 -- the same wire form srmech_elliptic_gosper / _recurrence parse).
 *
 * Output: the cyclic x-exponents (out_cyclic[], the distinct k, count out_n_cyclic) +
 * the per-theta block-label exponent rows (out_block_flat, one length-n_syms int32 row
 * per num-then-den theta, q-coordinate zeroed). The Python side rebuilds the cyclic dict
 * and groups the thetas by the block-label rows -- and trusts the native result ONLY after
 * the pure rebuild reproduces the SAME spectrum (the channels are a pure exponent-lattice
 * read, so the C must equal the pure read byte-for-byte). On any overflow / too-small
 * arena the peer returns SRMECH_ERR_OVERFLOW and the Python re-runs its COMPLETE pure path.
 *
 * The block-DECOMPOSED key-equation SOLVE (CarrierSpectrum.solve_key_equation) lives on the
 * PYTHON side -- it rides the additive ThetaSum carrier's full arithmetic (multiply / shift
 * / coordinate-emit), whose C peer is OWED (the C srmech_thetasum surface today exposes only
 * is_zero, not the arithmetic). The public carrier_spectrum op returns the channel READ,
 * which this peer mirrors completely; the solve is a method on the returned carrier object.
 *
 * Reference (the harmonic-shape framing; MPM-verified at build): Hjalmar Rosengren,
 * "Elliptic Hypergeometric Functions" (arXiv:1608.06161v3 [math.CA]), Section 1.3
 * (factorization of elliptic functions, Lemma 1.3.2) + Section 1.4 Eq. (1.12).
 *
 * This is PURE COMPOSITION of the shared srmech_ellbase_* exact-Q monomial algebra
 * (mul / copy / set_one / theta_canon_full) + er_build (the EllRatio.__init__ mirror) --
 * the same single copy srmech_elliptic_gosper / srmech_elliptic_recurrence ride.
 * Malloc-free (JPL Rule 3): every working monomial / EllRatio / scratch is carved from
 * the caller arena `ws`. Byte-identical to the Python channel read at ANY magnitude
 * (full bignum). No abs() (Class-K sign), no libm, no <complex.h>, no malloc.
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto/recursion): OK -- iterative, flat static helpers
 *   - Rule 2 (bounded loops)    : OK -- bounded by n_num / n_den / n_syms
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

/* The maximum theta-factor count the native scope handles per ratio (the canonical 8w7
 * has 7 num + 7 den). An over-cap input returns OK with *out_has = 0 -> Python decides. */
#define CS_MAX_THETA 64u
/* General scratch monomials for the channel read. */
#define CS_LOCAL_MONOS 8u

/* ---- shared-kernel aliases (the single copy lives in srmech_ellbase.c) ------- */
typedef srmech_ell_ctx_t       cs_ctx_t;
typedef srmech_ell_mono_t      cs_mono_t;
typedef srmech_ell_er_ratio_t  cs_ratio_t;
typedef srmech_ell_er_scr_t    cs_scr_t;

/* The working roster, carved once from the arena. */
typedef struct cs_work {
    cs_scr_t   s;                /* the EllRatio construction scratch         */
    cs_mono_t *raw_num;          /* reusable raw num-arg arrays for er_build   */
    cs_mono_t *raw_den;
    cs_mono_t *cn;               /* er_build canon scratch                     */
    cs_mono_t *cd;
    cs_mono_t *tmp;              /* CS_LOCAL_MONOS general scratch monomials   */
    cs_mono_t  net;             /* the net-period multiplier accumulator      */
    cs_mono_t  shifted;         /* arg * p^(exp_of sym)                        */
    cs_mono_t  pref;            /* the theta-canon prefactor                  */
    cs_mono_t  arg0;            /* the theta-canon canonical argument         */
    size_t     cap_arg;
} cs_work_t;

/* The whole working roster. */
typedef struct cs_all {
    cs_ctx_t   ctx;
    cs_work_t  w;
    cs_ratio_t r;                /* the parsed canonical input carrier element */
} cs_all_t;

/* out := EllRatio(pref, num, den) canonical (er_build folds + cancels + sorts). */
static srmech_status_t cs_er_build(cs_ctx_t *c, cs_work_t *w, cs_ratio_t *out,
                                   const cs_mono_t *pref, const cs_mono_t *num,
                                   size_t n_num, const cs_mono_t *den, size_t n_den,
                                   int psym)
{
    assert(c != NULL && w != NULL && out != NULL && pref != NULL);
    assert(n_num <= w->cap_arg && n_den <= w->cap_arg);
    return srmech_ellbase_er_build(c, out, pref, num, n_num, den, n_den, psym,
                                   &w->s, w->cn, w->cap_arg, w->cd, w->cap_arg);
}

/* Accumulate the net-period multiplier of ONE theta argument under the period shift
 * `sym -> p*sym`: shifted = arg * p^(arg.exps[sym]); canonicalize -> pref; w->net *= pref.
 * Mirrors _net_period_multiplier_exps's inner step (Rosengren Eq. 1.6 via theta-canon). */
static srmech_status_t cs_accumulate_period(cs_ctx_t *c, cs_work_t *w,
                                            const cs_mono_t *arg, int sym, int psym)
{
    int32_t e;
    srmech_status_t st;
    assert(c != NULL && w != NULL && arg != NULL);
    assert(psym >= 0);                                 /* p must be in the symbol table */
    if (sym < 0) { return SRMECH_OK; }                 /* the shift symbol is absent    */
    e = arg->exps[sym];
    st = srmech_ellbase_mono_copy(c, &w->shifted, arg);
    if (st != SRMECH_OK) { return st; }
    w->shifted.exps[psym] += e;                        /* arg * p^(exp_of sym)          */
    if (srmech_ellbase_mono_is_zero(&w->shifted)) { return SRMECH_OK; }
    st = srmech_ellbase_theta_canon_full(c, &w->pref, &w->arg0, &w->shifted, psym,
                                         &w->tmp[0], &w->tmp[1], &w->tmp[2],
                                         &w->s.g, &w->s.t0, &w->s.t1);
    if (st != SRMECH_OK) { return st; }
    st = srmech_ellbase_mono_mul(c, &w->tmp[3], &w->net, &w->pref,
                                 &w->s.g, &w->s.t0, &w->s.t1);  /* net *= pref          */
    if (st != SRMECH_OK) { return st; }
    return srmech_ellbase_mono_copy(c, &w->net, &w->tmp[3]);
}

/* Write the q-STRIPPED net-period exponent row of ONE theta `arg` into out_row (a
 * length-n_syms int32 vector). net = prod over sym in {x, y} of theta_canon(arg*p^e).exps;
 * then zero the q-coordinate (sigma traverses only q -> the sigma-invariant block label). */
static srmech_status_t cs_block_row(cs_ctx_t *c, cs_work_t *w, const cs_mono_t *arg,
                                    int xsym, int ysym, int qsym, int psym,
                                    int32_t *out_row)
{
    srmech_status_t st;
    assert(c != NULL && w != NULL && arg != NULL && out_row != NULL);
    assert(c->n_syms >= 1u);
    st = srmech_ellbase_mono_set_one(c, &w->net);      /* net := 1                      */
    if (st != SRMECH_OK) { return st; }
    st = cs_accumulate_period(c, w, arg, xsym, psym);  /* x -> p*x                      */
    if (st != SRMECH_OK) { return st; }
    st = cs_accumulate_period(c, w, arg, ysym, psym);  /* y -> p*y                      */
    if (st != SRMECH_OK) { return st; }
    memcpy(out_row, w->net.exps, c->n_syms * sizeof(int32_t));
    if (qsym >= 0) { out_row[qsym] = 0; }              /* STRIP q (sigma-invariant)     */
    return SRMECH_OK;
}

/* Insert a distinct x-exponent k into the sorted-by-insertion cyclic list (dedup). */
static void cs_add_cyclic(int32_t k, int32_t *cyc, size_t *n_cyc, size_t cap)
{
    size_t i;
    assert(cyc != NULL && n_cyc != NULL);
    assert(*n_cyc <= cap);
    for (i = 0; i < *n_cyc; i++) {
        if (cyc[i] == k) { return; }                   /* already present               */
    }
    if (*n_cyc < cap) { cyc[*n_cyc] = k; (*n_cyc)++; }
}

/* Read both channels of the canonical input ratio r: the cyclic x-exponents (prefactor +
 * every theta arg) into out_cyclic; the per-theta q-stripped block rows (num then den) into
 * out_block_flat. *out_n_cyclic / *out_n_thetas are the live counts. */
static srmech_status_t cs_read_channels(cs_ctx_t *c, cs_work_t *w, const cs_ratio_t *r,
                                        int xsym, int ysym, int qsym, int psym,
                                        int32_t *out_cyclic, size_t cyclic_cap,
                                        size_t *out_n_cyclic, int32_t *out_block_flat,
                                        size_t block_cap_rows, size_t *out_n_thetas)
{
    size_t i;
    size_t row = 0;
    size_t ncy = 0;
    srmech_status_t st;
    assert(c != NULL && w != NULL && r != NULL);
    assert(out_cyclic != NULL && out_n_cyclic != NULL);
    assert(out_block_flat != NULL && out_n_thetas != NULL);
    if (r->n_num + r->n_den > block_cap_rows) { return SRMECH_ERR_OVERFLOW; }
    cs_add_cyclic((xsym >= 0) ? r->pref.exps[xsym] : 0, out_cyclic, &ncy, cyclic_cap);
    for (i = 0; i < r->n_num; i++) {
        cs_add_cyclic((xsym >= 0) ? r->num[i].exps[xsym] : 0, out_cyclic, &ncy, cyclic_cap);
        st = cs_block_row(c, w, &r->num[i], xsym, ysym, qsym, psym,
                          out_block_flat + row * c->n_syms);
        if (st != SRMECH_OK) { return st; }
        row++;
    }
    for (i = 0; i < r->n_den; i++) {
        cs_add_cyclic((xsym >= 0) ? r->den[i].exps[xsym] : 0, out_cyclic, &ncy, cyclic_cap);
        st = cs_block_row(c, w, &r->den[i], xsym, ysym, qsym, psym,
                          out_block_flat + row * c->n_syms);
        if (st != SRMECH_OK) { return st; }
        row++;
    }
    *out_n_cyclic = ncy;
    *out_n_thetas = row;
    return SRMECH_OK;
}

/* Carve the shared work roster from the caller arena. */
static srmech_status_t cs_bind_work(cs_ctx_t *c, cs_work_t *w, size_t cap_arg)
{
    srmech_status_t st;
    assert(c != NULL && w != NULL);
    assert(cap_arg >= 1u);
    w->cap_arg = cap_arg;
    st = srmech_ellbase_bind_mono_arr(c, &w->raw_num, cap_arg);
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono_arr(c, &w->raw_den, cap_arg); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono_arr(c, &w->cn, cap_arg); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono_arr(c, &w->cd, cap_arg); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono_arr(c, &w->tmp, CS_LOCAL_MONOS); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono(c, &w->net); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono(c, &w->shifted); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono(c, &w->pref); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono(c, &w->arg0); }
    if (st == SRMECH_OK) { st = srmech_ellbase_er_bind_scr(c, &w->s, cap_arg); }
    return st;
}

/* Parse the flat input wire (coeff_num/coeff_den bigints + int32 exps rows, in order
 * prefactor, num0..K-1, den0..L-1) into raw monomial arrays, then er_build the canonical
 * input ratio r. Mirrors srmech_elliptic_recurrence's er_parse_input. */
static srmech_status_t cs_parse_input(cs_ctx_t *c, cs_work_t *w, cs_ratio_t *r,
                                      size_t n_num, size_t n_den,
                                      const srmech_bigint_t *cnum,
                                      const srmech_bigint_t *cden,
                                      const int32_t *exps_flat, int psym)
{
    cs_mono_t pref = {0};
    size_t k;
    size_t mi = 0;
    size_t ej = 0;
    srmech_status_t st;
    assert(c != NULL && w != NULL && r != NULL);
    assert(cnum != NULL && cden != NULL && exps_flat != NULL);
    assert(n_num <= w->cap_arg && n_den <= w->cap_arg);
    pref = w->tmp[4];
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
    return cs_er_build(c, w, r, &pref, w->raw_num, n_num, w->raw_den, n_den, psym);
}

/* Carve the whole roster from the caller arena. */
static srmech_status_t cs_bind_all(cs_all_t *A, size_t n_num, size_t n_den,
                                   void *ws, size_t ws_len)
{
    size_t cap_arg = n_num + n_den + 8u;
    srmech_status_t st;
    assert(A != NULL);
    assert(ws != NULL || ws_len == 0u);
    if (cap_arg < CS_MAX_THETA) { cap_arg = CS_MAX_THETA; }
    st = srmech_ellbase_er_arena_init(&A->ctx, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    st = cs_bind_work(&A->ctx, &A->w, cap_arg);
    if (st == SRMECH_OK) {
        st = srmech_ellbase_er_bind_ratio(&A->ctx, &A->r, cap_arg, cap_arg);
    }
    return st;
}

srmech_status_t srmech_carrier_spectrum(size_t n_syms, int xsym, int psym,
                                        int qsym, int ysym, size_t n_num, size_t n_den,
                                        const srmech_bigint_t *coeff_num,
                                        const srmech_bigint_t *coeff_den,
                                        const int32_t *exps_flat, uint32_t coeff_cap,
                                        int *out_has, int32_t *out_cyclic,
                                        size_t cyclic_cap, size_t *out_n_cyclic,
                                        int32_t *out_block_flat, size_t block_cap_rows,
                                        size_t *out_n_thetas, void *ws, size_t ws_len)
{
    cs_all_t A = {0};
    srmech_status_t st;
    assert(out_has != NULL && out_cyclic != NULL && out_n_cyclic != NULL);
    assert(out_block_flat != NULL && out_n_thetas != NULL);
    if (out_has == NULL || out_cyclic == NULL || out_n_cyclic == NULL
        || out_block_flat == NULL || out_n_thetas == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    *out_has = 0;
    *out_n_cyclic = 0;
    *out_n_thetas = 0;
    if (coeff_num == NULL || coeff_den == NULL || exps_flat == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (psym < 0) { return SRMECH_OK; }                /* p absent -> Python pure path  */
    if (n_num > CS_MAX_THETA || n_den > CS_MAX_THETA) {
        return SRMECH_OK;                              /* over native scope -> decline  */
    }
    A.ctx.n_syms = (n_syms == 0u) ? 1u : n_syms;
    A.ctx.cap = (coeff_cap < 8u) ? 8u : coeff_cap;
    st = cs_bind_all(&A, n_num, n_den, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    st = cs_parse_input(&A.ctx, &A.w, &A.r, n_num, n_den, coeff_num, coeff_den,
                        exps_flat, psym);
    if (st != SRMECH_OK) { return st; }
    st = cs_read_channels(&A.ctx, &A.w, &A.r, xsym, ysym, qsym, psym,
                          out_cyclic, cyclic_cap, out_n_cyclic,
                          out_block_flat, block_cap_rows, out_n_thetas);
    if (st != SRMECH_OK) { return st; }
    *out_has = 1;
    return SRMECH_OK;
}

/* The minimum `ws_len` BYTES srmech_carrier_spectrum needs for the given shape (n_syms
 * symbols, n_num + n_den input theta factors, coeff_cap the per-coefficient limb cap).
 * Sized to the inputs -- no compiled-in cap. */
size_t srmech_carrier_spectrum_ws_bound(size_t n_syms, size_t n_num, size_t n_den,
                                        size_t coeff_cap)
{
    size_t cap = (coeff_cap < 8u) ? 8u : coeff_cap;
    size_t ns = (n_syms == 0u) ? 1u : n_syms;
    size_t cap_arg = n_num + n_den + 8u;
    size_t mw;
    size_t ratio;
    size_t arrays;
    size_t total;
    if (cap_arg < CS_MAX_THETA) { cap_arg = CS_MAX_THETA; }
    mw = srmech_ellbase_er_mono_words(cap, ns);
    /* the parsed input ratio (pref + 2*cap_arg arg monomials), padded. */
    ratio = mw + 2u * cap_arg * mw;
    /* the reusable raw / canon arrays + the scratch / net / shift monomials. */
    arrays = (4u * cap_arg + CS_LOCAL_MONOS + 8u + SRMECH_ELL_ER_SCR_MONOS + 64u) * mw;
    total = ratio + arrays + cap * 32u + 4096u;
    assert(cap >= 8u);
    assert(total >= ratio);
    return total * sizeof(uint32_t);
}
