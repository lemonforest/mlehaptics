/*
 * srmech_ellbase_internal.h -- the SHARED exact-Q monomial + theta-canon kernels
 * of the elliptic carrier family (srmech.amsc.ellbase: EllMonomial / Theta /
 * EllRatio), promoted out of srmech_thetasum.c (rc63) so the ThetaSum is_zero
 * decision AND the EllRatio is_elliptic decision share ONE copy of each kernel
 * (the 1:1-mirror discipline forbids two copies of the same algebra).
 *
 * This is an INTERNAL cross-translation-unit header (NOT installed, NOT part of
 * the public srmech.h ABI): srmech_ellbase.c DEFINES these symbols; both
 * srmech_ellbase.c and srmech_thetasum.c call them. The symbols carry the
 * `srmech_ellbase_` prefix so they are unique link-level names, but they are an
 * implementation detail of the elliptic carrier, not an advertised ABI surface.
 *
 * The working representation is the rc63 arena-bump form: an EllMonomial is an
 * exact-Q coeff (num/den srmech_bigint, Class-K sign on num) over a DENSE int32
 * exponent vector of length n_syms (an interned symbol table, in the Python
 * sorted-symbol-NAME order so the dense vector reproduces EllMonomial._sort_key's
 * sorted-(symbol,exp)-tuple compare). Every working monomial + bigint is carved
 * from the caller arena `pool` -- malloc-free (JPL Rule 3); no compiled-in cap.
 *
 * License: MIT.
 */

#ifndef SRMECH_ELLBASE_INTERNAL_H
#define SRMECH_ELLBASE_INTERNAL_H

#include "srmech.h"

#include <stdint.h>

/* A rational coefficient num/den as two srmech_bigint carved from the arena. */
typedef struct srmech_ell_q {
    srmech_bigint_t num;
    srmech_bigint_t den;
} srmech_ell_q_t;

/* An EllMonomial: an exact-Q coeff over a dense int32 exponent vector of length
 * n_syms (the interned symbol table). The zero monomial has coeff num == 0. */
typedef struct srmech_ell_mono {
    srmech_ell_q_t  coeff;
    int32_t        *exps;   /* length n_syms, arena-carved                     */
} srmech_ell_mono_t;

/* The shared working context: the arena bump allocator + sizing. (ThetaSum's
 * ts_ctx_t embeds this so its own helpers can pass &ctx.eb here.) */
typedef struct srmech_ell_ctx {
    uint32_t *pool;
    size_t    pool_words;
    size_t    pool_cur;
    void     *scratch;
    size_t    scratch_len;
    size_t    n_syms;     /* interned symbol-table dimension                   */
    uint32_t  cap;        /* per-bigint limb cap                               */
} srmech_ell_ctx_t;

/* ---- arena bump primitives (shared) ----------------------------------------- */

uint32_t *srmech_ellbase_take_words(srmech_ell_ctx_t *c, size_t cnt);
void      srmech_ellbase_align8(srmech_ell_ctx_t *c);
int32_t  *srmech_ellbase_take_exps(srmech_ell_ctx_t *c);
srmech_status_t srmech_ellbase_bind_bi(srmech_ell_ctx_t *c, srmech_bigint_t *b);
srmech_status_t srmech_ellbase_bind_q(srmech_ell_ctx_t *c, srmech_ell_q_t *q);
srmech_status_t srmech_ellbase_bind_mono(srmech_ell_ctx_t *c, srmech_ell_mono_t *m);
srmech_status_t srmech_ellbase_bind_mono_arr(srmech_ell_ctx_t *c,
                                             srmech_ell_mono_t **out, size_t count);

/* ---- exact-Q (two-bigint) helpers (shared) ---------------------------------- */

srmech_status_t srmech_ellbase_q_reduce(srmech_ell_ctx_t *c, srmech_ell_q_t *q,
                                        srmech_bigint_t *g, srmech_bigint_t *t0,
                                        srmech_bigint_t *t1);
srmech_status_t srmech_ellbase_q_mul(srmech_ell_ctx_t *c, srmech_ell_q_t *out,
                                     const srmech_ell_q_t *a, const srmech_ell_q_t *b,
                                     srmech_bigint_t *g, srmech_bigint_t *t0,
                                     srmech_bigint_t *t1);
srmech_status_t srmech_ellbase_q_add(srmech_ell_ctx_t *c, srmech_ell_q_t *out,
                                     const srmech_ell_q_t *a, const srmech_ell_q_t *b,
                                     srmech_bigint_t *g, srmech_bigint_t *t0,
                                     srmech_bigint_t *t1);
srmech_status_t srmech_ellbase_q_copy(srmech_ell_q_t *out, const srmech_ell_q_t *a);
int srmech_ellbase_q_eq(const srmech_ell_q_t *a, const srmech_ell_q_t *b);

/* ---- monomial helpers (shared) ---------------------------------------------- */

int srmech_ellbase_mono_is_zero(const srmech_ell_mono_t *m);
srmech_status_t srmech_ellbase_mono_set_one(srmech_ell_ctx_t *c,
                                            srmech_ell_mono_t *m);
srmech_status_t srmech_ellbase_mono_copy(srmech_ell_ctx_t *c, srmech_ell_mono_t *out,
                                         const srmech_ell_mono_t *a);
srmech_status_t srmech_ellbase_mono_mul(srmech_ell_ctx_t *c, srmech_ell_mono_t *out,
                                        const srmech_ell_mono_t *a,
                                        const srmech_ell_mono_t *b,
                                        srmech_bigint_t *g, srmech_bigint_t *t0,
                                        srmech_bigint_t *t1);
srmech_status_t srmech_ellbase_mono_inv(srmech_ell_ctx_t *c, srmech_ell_mono_t *out,
                                        const srmech_ell_mono_t *a);
srmech_status_t srmech_ellbase_mono_div(srmech_ell_ctx_t *c, srmech_ell_mono_t *out,
                                        const srmech_ell_mono_t *a,
                                        const srmech_ell_mono_t *b,
                                        srmech_ell_mono_t *binv, srmech_bigint_t *g,
                                        srmech_bigint_t *t0, srmech_bigint_t *t1);
int srmech_ellbase_exps_cmp(const srmech_ell_ctx_t *c, const int32_t *a,
                            const int32_t *b);
int srmech_ellbase_mono_cmp(const srmech_ell_ctx_t *c, const srmech_ell_mono_t *a,
                            const srmech_ell_mono_t *b);
int srmech_ellbase_mono_eq(const srmech_ell_ctx_t *c, const srmech_ell_mono_t *a,
                           const srmech_ell_mono_t *b);
srmech_status_t srmech_ellbase_mono_sqrt(srmech_ell_ctx_t *c, srmech_ell_mono_t *out,
                                         const srmech_ell_mono_t *z, int *ok,
                                         srmech_bigint_t *r, srmech_bigint_t *t0);

/* ---- Theta.canonicalize (shared) -------------------------------------------- *
 *
 * theta(z; p) == prefactor * theta(z0; p) with z0 having p-exponent 0 and a fixed
 * orientation of {z0, z0^-1}. The build-pinned exact identities:
 *   theta(p^k z0) = (-1)^k p^{-k(k-1)/2} z0^{-k} theta(z0)
 *   theta(w^-1)   = -w^-1 theta(w)
 * `psym` / `xsym` / `ysym` are the interned indices of p / x / y (-1 if absent).
 *
 * `_arg` writes ONLY the canonical ARGUMENT (the ThetaSum is_zero decision uses
 * only the argument; the prefactor is coeff-blind for its class key). `_full`
 * ALSO writes the exact EllMonomial PREFACTOR into out_pref (the EllRatio
 * construction folds it into the global prefactor). zinv / z0 / z0inv / tmp are
 * caller scratch monomials. */
srmech_status_t srmech_ellbase_theta_canon_arg(srmech_ell_ctx_t *c,
                                               srmech_ell_mono_t *out_arg,
                                               const srmech_ell_mono_t *z, int psym,
                                               srmech_ell_mono_t *zinv);
srmech_status_t srmech_ellbase_theta_canon_full(srmech_ell_ctx_t *c,
                                                srmech_ell_mono_t *out_pref,
                                                srmech_ell_mono_t *out_arg,
                                                const srmech_ell_mono_t *z, int psym,
                                                srmech_ell_mono_t *z0,
                                                srmech_ell_mono_t *z0inv,
                                                srmech_ell_mono_t *tmp,
                                                srmech_bigint_t *g,
                                                srmech_bigint_t *t0,
                                                srmech_bigint_t *t1);

#endif /* SRMECH_ELLBASE_INTERNAL_H */
