/*
 * srmech_thetasum_internal.h -- the SHARED Weierstrass +/- -pair reduction kernels
 * (rc210). The single copy of the pair-recovery / three-term-rewrite / normal-form
 * machinery lives in srmech_thetasum.c; this header exposes it to the rc210
 * structural-certificate peer (srmech_thetasum_interp.c) so the certificate
 * recursion's Z2 stage (the generalized pair reduction over a component's ACTUAL
 * live symbols) rides the SAME algebra as the public +/- -pair fast path --
 * everything-mirrors forbids two copies of one reduction.
 *
 * Like srmech_ellbase_internal.h these are NOT public API: no srmech.h exposure,
 * no ctypes binding, no ABI surface. The names carry the srmech_ts_ prefix only
 * for link-level uniqueness. License: MIT.
 */
#ifndef SRMECH_THETASUM_INTERNAL_H
#define SRMECH_THETASUM_INTERNAL_H

#include "srmech.h"
#include "srmech_ellbase_internal.h"

#include <stddef.h>
#include <stdint.h>

/* A canonical +/- -pair (alpha, beta): theta(alpha*beta^pm). */
typedef struct srmech_ts_pair {
    srmech_ell_mono_t alpha;
    srmech_ell_mono_t beta;
} srmech_ts_pair_t;

/* A reduced term = (prefactor monomial, array of canonical +/- -pairs). */
typedef struct srmech_ts_rterm {
    srmech_ell_mono_t  pref;
    srmech_ts_pair_t  *pairs;    /* arena array, length n_pairs                    */
    size_t             n_pairs;
    int                live;     /* 0 once combined away (cancelled / consumed)    */
} srmech_ts_rterm_t;

/* Scratch bundle for the pair / rewrite algebra (bound once from the arena). */
#define SRMECH_TS_SCR_MONOS 16u
#define SRMECH_TS_REWRITE_MONOS 6u
#define SRMECH_TS_REWRITE_PAIRS 4u
typedef struct srmech_ts_scr {
    srmech_ell_mono_t *pm;         /* SRMECH_TS_SCR_MONOS general scratch monos    */
    srmech_ell_mono_t *cm;         /* SRMECH_TS_REWRITE_MONOS coeff scratch monos  */
    srmech_ell_mono_t *ca;         /* max_thetas canonical-arg scratch monos       */
    srmech_ts_pair_t  *rp;         /* SRMECH_TS_REWRITE_PAIRS rewrite output pairs */
    int               *used_pairs; /* >= max_pairs flags for the multiset compare  */
    srmech_bigint_t    g;
    srmech_bigint_t    t0;
    srmech_bigint_t    t1;
    int                psym;       /* the interned p index (-1 if absent)          */
} srmech_ts_scr_t;

/* The double-buffered rterm work arrays + counts for a class reduction. */
typedef struct srmech_ts_work {
    srmech_ts_rterm_t *cur;
    size_t             n_cur;
    srmech_ts_rterm_t *nxt;
    size_t             n_nxt;
    size_t             cap;
} srmech_ts_work_t;

/* The per-buffer rterm slot capacity for the reduction work arrays. */
size_t srmech_ts_work_cap(size_t n_terms, size_t max_thetas);

/* Bind the scratch bundle / an rterm array from the caller arena. */
srmech_status_t srmech_ts_bind_scr(srmech_ell_ctx_t *c, srmech_ts_scr_t *s,
                                   size_t max_thetas);
srmech_status_t srmech_ts_bind_rterm_arr(srmech_ell_ctx_t *c, srmech_ts_rterm_t **out,
                                         size_t count, size_t max_pairs);

/* Recover the +/- -pair decomposition of a canonical theta-product into `rt`
 * (rt->pref pre-set to the term prefactor; inversion prefactors fold in). *ok = 0
 * when the product is NOT a clean product of +/- -pairs. `used` >= n_thetas flags. */
srmech_status_t srmech_ts_recover_pairs(srmech_ell_ctx_t *c, srmech_ts_rterm_t *rt,
                                        const srmech_ell_mono_t *targs,
                                        size_t n_thetas, int xsym, int ysym, int *ok,
                                        srmech_ts_scr_t *s, int *used);

/* Reduce w->cur[0..n_cur) to the canonical Weierstrass normal form by the strictly-
 * decreasing three-term rewrite over the ORDERED symbol list rw_syms[0..n_rw)
 * (mirrors thetasum._pair_reduce_component's `for s in sorted(syms)` pass loop; the
 * +/- -pair fast path passes {x, y}). xsym/ysym feed the canonical pair ORIENTATION
 * (Python's _canon_half hardcodes x, y) and are independent of the rewrite list.
 * *is_zero = 1 IFF the final live count is 0 (the component is proven zero). */
srmech_status_t srmech_ts_reduce_syms(srmech_ell_ctx_t *c, srmech_ts_work_t *w,
                                      int xsym, int ysym, const int32_t *rw_syms,
                                      size_t n_rw, int *is_zero, srmech_ts_scr_t *s);

#endif /* SRMECH_THETASUM_INTERNAL_H */
