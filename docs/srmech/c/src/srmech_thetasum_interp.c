/*
 * srmech_thetasum_interp.c -- the C peer of the ThetaSum SOUND structural
 * CERTIFICATE recursion (rc210 -- the is_zero soundness rebuild). A 1:1 mirror of
 * the consumer BOOL of the pure-Python srmech.amsc.thetasum._decide_struct:
 * *out_is_zero = 1 IFF the cleared numerator is CERTIFICATE-PROVEN identically
 * zero; 0 = "not proven" (a proven-nonzero object or an honest decline -- the
 * bool deliberately does not distinguish them; the sound contract is True-only).
 *
 * WHY THE REWRITE (stop-the-line): the pre-rc210 decision in this file certified
 * provably-NONZERO objects as zero through two unsound devices -- (D1) the
 * single-variable p-order BAND k = max-term(sum e^2)-1+3 (ti_one_var), which
 * under-counts MULTI-TERM cancellation gaps, and (D2) the MIXED-character node
 * count d = max-term sum e^2 (ti_decide), which has no supporting theorem (a sum
 * of terms of different quasi-periodicity lies in no single theta-section space).
 * Two more rode along: (D3) ti_collect_vars scanned theta args only (prefactor-
 * only symbols dropped -> a*theta(2x) - b*theta(2x) "proven" zero) and (D4)
 * augment primes were not deduplicated against zero-node constants. The True
 * side was REPLACED, not repaired: there is NO series band anywhere in this file
 * any more (the old ti_ps_* q-expansion machinery is deleted outright).
 *
 * THE CERTIFICATE RECURSION (the bool of thetasum._decide_struct; the NONZERO /
 * UNKNOWN refinement of the three-valued Python is detection-only and never
 * feeds back into a ZERO, so the AND-recursion below IS the exact bool mirror):
 *
 *   Z1  combine -> empty: exact carrier cancellation + theta(1)=0 kills.
 *   Z3s the exact JOINT-CHARACTER split: per symbol v, a term's character is
 *       (D_v = sum e^2, mu_v = the full Rosengren Eq. 1.6 multiplier monomial,
 *       Q*-coefficient included, v-part dropped). Different characters are
 *       linearly independent over Q(q,p); the sum is proven zero IFF every
 *       component is (recursively) proven zero.
 *   Z2  the Weierstrass +/- -pair three-term reduction (Rosengren Eq. 1.12) to
 *       the EMPTY normal form, generalized over the component's ACTUAL live
 *       symbols -- the SHARED srmech_ts_* single-copy kernels
 *       (srmech_thetasum_internal.h).
 *   Z4  per-character elliptic interpolation: a SINGLE-character component of
 *       v-degree D >= 1 proven zero at D+1 nodes PAIRWISE DISTINCT mod p^Z is
 *       identically zero (Rosengren arXiv:1608.06161v3 Cor. 1.3.5). Nodes = the
 *       theta-factor zeros + DEDUPLICATED globally-distinct augment primes.
 *   Everything else (a singleton term, a 0-variable residue, an incomplete node
 *   set, an unproven child) -> NOT PROVEN (0). No band. No exceptions.
 *
 * Recursion -> EXPLICIT STACK (JPL Rule 1): a depth-bounded DFS with per-frame
 * ARENA MARKS; a frame's children are either its character COMPONENTS or its
 * interpolation NODE substitutions. Malloc-free (Rule 3): everything is carved
 * from the caller arena `ws`; OVERFLOW => decline (the Python dispatch falls to
 * the sound pure oracle). Class-K sign is a bigint sign int, never abs().
 *
 * Wire form + symbol set are UNCHANGED from rc99/rc102/rc103 -> ABI stays 4.
 * License: MIT.
 */

#include "srmech.h"
#include "srmech_ellbase_internal.h"
#include "srmech_thetasum_internal.h"
#include "srmech_platform.h"   /* PAL: srmech_plat_thread_* -- the rc103 parallel peer */

#include <assert.h>
#include <stdint.h>
#include <string.h>

/* ---- shared-kernel aliases (the single copy lives in srmech_ellbase.c) ------- */
typedef srmech_ell_q_t    ti_q_t;
typedef srmech_ell_mono_t ti_mono_t;
typedef srmech_ell_ctx_t  ti_ctx_t;

#define ti_take_words        srmech_ellbase_take_words
#define ti_align8            srmech_ellbase_align8
#define ti_bind_bi           srmech_ellbase_bind_bi
#define ti_bind_q            srmech_ellbase_bind_q
#define ti_bind_mono         srmech_ellbase_bind_mono
#define ti_bind_mono_arr     srmech_ellbase_bind_mono_arr
#define ti_q_add             srmech_ellbase_q_add
#define ti_q_copy            srmech_ellbase_q_copy
#define ti_mono_is_zero      srmech_ellbase_mono_is_zero
#define ti_mono_set_one      srmech_ellbase_mono_set_one
#define ti_mono_copy         srmech_ellbase_mono_copy
#define ti_mono_mul          srmech_ellbase_mono_mul
#define ti_mono_inv          srmech_ellbase_mono_inv
#define ti_exps_cmp          srmech_ellbase_exps_cmp
#define ti_mono_cmp          srmech_ellbase_mono_cmp
#define ti_mono_eq           srmech_ellbase_mono_eq
#define ti_theta_canon_full  srmech_ellbase_theta_canon_full

/* The globally-distinct augment primes (mirrors thetasum._STRUCT_PRIMES EXACTLY,
 * same values AND same order AND same count -- the (offset+used) % NPR index MUST
 * reproduce Python's threading). Distinct primes are load-bearing for SOUNDNESS:
 * substituting two variables to the SAME constant would make a cross-variable
 * factor theta(x_i/x_j) -> theta(1)=0 a SPURIOUS zero. */
static const int32_t TI_STRUCT_PRIMES[] = {
    2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83,
    89, 97, 101, 103, 107, 109, 113, 127, 131, 137, 139, 149, 151, 157, 163, 167, 173, 179,
    181, 191, 193, 197, 199, 211, 223, 227, 229, 233, 239, 241, 251, 257, 263, 269, 271, 277,
    281, 283, 293, 307, 311, 313, 317, 331, 337, 347, 349, 353, 359, 367, 373, 379, 383, 389,
    397, 401, 409, 419, 421, 431, 433, 439, 443, 449, 457, 461, 463, 467, 479, 487, 491, 499,
    503, 509, 521, 523, 541, 547, 557, 563, 569, 571, 577, 587, 593, 599, 601, 607, 613, 617};

#define TI_NPRIMES ((int)(sizeof(TI_STRUCT_PRIMES) / sizeof(TI_STRUCT_PRIMES[0])))

/* One numerator term: a prefactor monomial + an array of theta-argument monomials. */
typedef struct ti_term {
    ti_mono_t  pref;
    ti_mono_t *targs;
    size_t     n_thetas;
} ti_term_t;

/* A reusable scratch bundle (general monomials + coeff Q's + bigints). */
#define TI_SCR_MONOS 24u
typedef struct ti_scr {
    ti_mono_t      *m;        /* TI_SCR_MONOS general scratch monomials */
    ti_q_t          qa;       /* combine coeff-add scratch              */
    srmech_bigint_t g;
    srmech_bigint_t t0;
    srmech_bigint_t t1;
    int             psym;
    int             xsym;     /* canonical pair orientation (Z2)        */
    int             ysym;
    int            *present;  /* n_syms variable-membership flags       */
} ti_scr_t;

/* A DFS frame: one node of the certificate tree. Children are either the frame's
 * joint-character COMPONENTS (kind 2) or its interpolation NODE substitutions
 * (kind 1). */
typedef struct ti_frame {
    ti_term_t *raw;          /* un-combined input terms                 */
    size_t     n_raw;
    ti_term_t *terms;        /* combined terms                          */
    size_t     n_terms;
    int32_t   *comp_of;      /* per-term component id (kind 2)          */
    ti_mono_t *nodes;        /* the D+1 substitution nodes (kind 1)     */
    size_t     n_children;
    int        kind;         /* 1 = nodes, 2 = components               */
    int        v;            /* interpolation variable index (kind 1)   */
    int32_t    offset;       /* augment-prime offset for THIS frame     */
    int32_t    child_offset;
    size_t     next_child;
    size_t     frame_mark;   /* pool_cur before this frame's allocs     */
    size_t     child_mark;   /* pool_cur before the first child         */
    int        state;        /* 0 = NEW, 1 = BRANCHING                  */
} ti_frame_t;

/* The exact v-character of one term (mirrors thetasum._term_char_v): degree D_v,
 * the multiplier's p-power, and the multiplier monomial (v / p coordinates
 * zeroed -- the p-power is the explicit int so the character is exact even when
 * p is absent from the interned table). */
typedef struct ti_char {
    ti_mono_t mu;
    int32_t   D;
    int32_t   pexp;
} ti_char_t;

/* The per-worker runtime bundle: general scratch + the SHARED pair-reduce scratch
 * + recover flags + the DFS frame stack. */
typedef struct ti_rt {
    ti_scr_t         s;
    srmech_ts_scr_t  ts;
    int             *tsused;   /* >= max_thetas recover flags */
    ti_frame_t      *frames;
    size_t           fcap;
} ti_rt_t;

/* ---- forward declarations (Rule 1: iterative; no recursion) ----------------- */
static srmech_status_t ti_compact_terms(ti_ctx_t *c, ti_term_t *arr, size_t n,
                                        size_t *n_out);
static srmech_status_t ti_expand(ti_ctx_t *c, ti_frame_t *fr, size_t max_thetas,
                                 ti_rt_t *rt, int *is_leaf, int *verdict);

/* ---- small helpers ---------------------------------------------------------- */

/* Integer magnitude (Class-K, never abs()). */
static int32_t ti_iabs(int32_t e)
{
    assert(e >= INT32_MIN);
    assert(e <= INT32_MAX);
    return (e < 0) ? -e : e;
}

/* 1 iff the bigint b holds exactly +1. */
static int ti_bi_is_one(const srmech_bigint_t *b)
{
    assert(b != NULL);
    assert(b->limbs != NULL || b->n == 0u);
    return (b->sign == 1 && b->n == 1u && b->limbs[0] == 1u);
}

/* 1 iff the monomial m is the unit 1 (coeff 1/1, all exps zero) -- theta(1)=0 test. */
static int ti_mono_is_unit(const ti_ctx_t *c, const ti_mono_t *m)
{
    size_t i;
    assert(c != NULL && m != NULL);
    assert(m->exps != NULL);
    for (i = 0; i < c->n_syms; i++) {
        if (m->exps[i] != 0) { return 0; }
    }
    return ti_bi_is_one(&m->coeff.num) && ti_bi_is_one(&m->coeff.den);
}

/* m := EllMonomial(Q(prime, 1)) -- a rational-constant node (no exps). */
static srmech_status_t ti_set_prime(ti_ctx_t *c, ti_mono_t *m, int32_t prime)
{
    srmech_status_t st;
    assert(c != NULL && m != NULL);
    assert(prime > 0);
    st = ti_mono_set_one(c, m);
    if (st != SRMECH_OK) { return st; }
    return srmech_bigint_set_i64(&m->coeff.num, (int64_t)prime);
}

/* out := base^e (integer power; e may be negative). acc / inv are scratch monos. */
static srmech_status_t ti_mono_pow(ti_ctx_t *c, ti_mono_t *out, const ti_mono_t *base,
                                   int32_t e, ti_mono_t *acc, ti_mono_t *inv,
                                   ti_scr_t *s)
{
    int32_t i;
    int32_t mag = ti_iabs(e);
    srmech_status_t st;
    assert(c != NULL && out != NULL && base != NULL && acc != NULL);
    assert(inv != NULL && s != NULL);
    st = ti_mono_set_one(c, acc);
    if (st != SRMECH_OK) { return st; }
    for (i = 0; i < mag; i++) {
        st = ti_mono_mul(c, inv, acc, base, &s->g, &s->t0, &s->t1);
        if (st != SRMECH_OK) { return st; }
        st = ti_mono_copy(c, acc, inv);
        if (st != SRMECH_OK) { return st; }
    }
    if (e < 0) {
        st = ti_mono_inv(c, inv, acc);
        if (st != SRMECH_OK) { return st; }
        return ti_mono_copy(c, out, inv);
    }
    return ti_mono_copy(c, out, acc);
}

/* Insertion-sort a monomial array by ti_mono_cmp (the EllMonomial._sort_key order). */
static srmech_status_t ti_sort_monos(ti_ctx_t *c, ti_mono_t *arr, size_t n, ti_mono_t *tmp)
{
    size_t i;
    size_t j;
    srmech_status_t st;
    assert(c != NULL && (arr != NULL || n == 0u));
    assert(tmp != NULL);
    for (i = 1; i < n; i++) {
        st = ti_mono_copy(c, tmp, &arr[i]);
        if (st != SRMECH_OK) { return st; }
        j = i;
        while (j > 0 && ti_mono_cmp(c, &arr[j - 1], tmp) > 0) {
            st = ti_mono_copy(c, &arr[j], &arr[j - 1]);
            if (st != SRMECH_OK) { return st; }
            j--;
        }
        st = ti_mono_copy(c, &arr[j], tmp);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* ---- binding ---------------------------------------------------------------- */

static srmech_status_t ti_bind_term(ti_ctx_t *c, ti_term_t *t, size_t max_thetas)
{
    srmech_status_t st;
    assert(c != NULL && t != NULL);
    assert(c->cap > 0u);
    st = ti_bind_mono(c, &t->pref);
    if (st != SRMECH_OK) { return st; }
    st = ti_bind_mono_arr(c, &t->targs, (max_thetas == 0u) ? 1u : max_thetas);
    if (st != SRMECH_OK) { return st; }
    t->n_thetas = 0;
    return SRMECH_OK;
}

static srmech_status_t ti_bind_term_arr(ti_ctx_t *c, ti_term_t **out, size_t count,
                                        size_t max_thetas)
{
    size_t i;
    size_t words;
    uint32_t *raw;
    srmech_status_t st;
    assert(c != NULL && out != NULL);
    assert(count >= 1u);
    ti_align8(c);
    words = (count * sizeof(ti_term_t) + sizeof(uint32_t) - 1u) / sizeof(uint32_t);
    raw = ti_take_words(c, words);
    if (raw == NULL) { return SRMECH_ERR_OVERFLOW; }
    *out = (ti_term_t *)raw;
    for (i = 0; i < count; i++) {
        st = ti_bind_term(c, &(*out)[i], max_thetas);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

static srmech_status_t ti_bind_scr(ti_ctx_t *c, ti_scr_t *s)
{
    uint32_t *raw;
    srmech_status_t st;
    assert(c != NULL && s != NULL);
    assert(c->cap > 0u);
    st = ti_bind_mono_arr(c, &s->m, TI_SCR_MONOS);
    if (st == SRMECH_OK) { st = ti_bind_q(c, &s->qa); }
    if (st == SRMECH_OK) { st = ti_bind_bi(c, &s->g); }
    if (st == SRMECH_OK) { st = ti_bind_bi(c, &s->t0); }
    if (st == SRMECH_OK) { st = ti_bind_bi(c, &s->t1); }
    if (st != SRMECH_OK) { return st; }
    raw = ti_take_words(c, c->n_syms);
    if (raw == NULL) { return SRMECH_ERR_OVERFLOW; }
    s->present = (int *)raw;
    return SRMECH_OK;
}

/* Bind an array of ti_char_t (each with a bound mu monomial). */
static srmech_status_t ti_bind_char_arr(ti_ctx_t *c, ti_char_t **out, size_t count)
{
    size_t i;
    size_t words;
    uint32_t *raw;
    srmech_status_t st;
    assert(c != NULL && out != NULL);
    assert(count >= 1u);
    ti_align8(c);
    words = (count * sizeof(ti_char_t) + sizeof(uint32_t) - 1u) / sizeof(uint32_t);
    raw = ti_take_words(c, words);
    if (raw == NULL) { return SRMECH_ERR_OVERFLOW; }
    *out = (ti_char_t *)raw;
    for (i = 0; i < count; i++) {
        st = ti_bind_mono(c, &(*out)[i].mu);
        if (st != SRMECH_OK) { return st; }
        (*out)[i].D = 0;
        (*out)[i].pexp = 0;
    }
    return SRMECH_OK;
}

/* ---- combine (mirrors thetasum._struct_combine) ----------------------------- */

/* Canonicalize ONE raw term into `dst` (fold each theta-canon prefactor into the
 * term prefactor; a theta that canonicalizes to theta(1) KILLS the term). Sets
 * *dead = 1 when the term drops (theta(1) factor OR the folded prefactor is zero).
 * The surviving canonical thetas are written (sorted) into dst->targs. */
static srmech_status_t ti_canon_term(ti_ctx_t *c, ti_term_t *dst, const ti_term_t *src,
                                     ti_scr_t *s, int *dead)
{
    size_t i;
    srmech_status_t st;
    assert(c != NULL && dst != NULL && src != NULL);
    assert(s != NULL && dead != NULL);
    *dead = 0;
    st = ti_mono_copy(c, &dst->pref, &src->pref);
    if (st != SRMECH_OK) { return st; }
    dst->n_thetas = 0;
    for (i = 0; i < src->n_thetas; i++) {
        st = ti_theta_canon_full(c, &s->m[0], &s->m[1], &src->targs[i], s->psym,
                                 &s->m[2], &s->m[3], &s->m[4], &s->g, &s->t0, &s->t1);
        if (st != SRMECH_OK) { return st; }
        st = ti_mono_mul(c, &s->m[5], &dst->pref, &s->m[0], &s->g, &s->t0, &s->t1);
        if (st != SRMECH_OK) { return st; }
        st = ti_mono_copy(c, &dst->pref, &s->m[5]);
        if (st != SRMECH_OK) { return st; }
        if (ti_mono_is_unit(c, &s->m[1])) { *dead = 1; return SRMECH_OK; }
        st = ti_mono_copy(c, &dst->targs[dst->n_thetas], &s->m[1]);
        if (st != SRMECH_OK) { return st; }
        dst->n_thetas++;
    }
    if (ti_mono_is_zero(&dst->pref)) { *dead = 1; return SRMECH_OK; }
    return ti_sort_monos(c, dst->targs, dst->n_thetas, &s->m[0]);
}

/* 1 iff terms a and b are LIKE (same prefactor EXPONENT monomial AND same sorted
 * canonical theta multiset) -- the _struct_combine grouping key. */
static int ti_term_like(const ti_ctx_t *c, const ti_term_t *a, const ti_term_t *b)
{
    size_t i;
    assert(c != NULL && a != NULL && b != NULL);
    assert(a->pref.exps != NULL && b->pref.exps != NULL);
    if (a->n_thetas != b->n_thetas) { return 0; }
    if (ti_exps_cmp(c, a->pref.exps, b->pref.exps) != 0) { return 0; }
    for (i = 0; i < a->n_thetas; i++) {
        if (!ti_mono_eq(c, &a->targs[i], &b->targs[i])) { return 0; }
    }
    return 1;
}

/* Combine `in`[0..n_in) into freshly-bound `out` (canonicalize, drop theta(1) /
 * zero terms, merge LIKE terms by adding prefactor coeffs, drop coeff-zero, keep
 * first-seen order). Mirrors _struct_combine. *n_out set to the live count. */
static srmech_status_t ti_combine(ti_ctx_t *c, ti_term_t **out, size_t *n_out,
                                  const ti_term_t *in, size_t n_in, size_t max_thetas,
                                  ti_scr_t *s)
{
    size_t i;
    size_t j;
    size_t k = 0;
    int dead;
    srmech_status_t st;
    assert(c != NULL && out != NULL && n_out != NULL && s != NULL);
    assert(in != NULL || n_in == 0u);
    st = ti_bind_term_arr(c, out, (n_in == 0u) ? 1u : n_in, max_thetas);
    if (st != SRMECH_OK) { return st; }
    for (i = 0; i < n_in; i++) {
        st = ti_canon_term(c, &(*out)[k], &in[i], s, &dead);
        if (st != SRMECH_OK) { return st; }
        if (dead) { continue; }
        j = 0;
        while (j < k && !ti_term_like(c, &(*out)[j], &(*out)[k])) { j++; }
        if (j < k) {
            st = ti_q_add(c, &s->qa, &(*out)[j].pref.coeff, &(*out)[k].pref.coeff,
                          &s->g, &s->t0, &s->t1);
            if (st != SRMECH_OK) { return st; }
            st = ti_q_copy(&(*out)[j].pref.coeff, &s->qa);
            if (st != SRMECH_OK) { return st; }
        } else {
            k++;
        }
    }
    return ti_compact_terms(c, *out, k, n_out);
}

/* Drop coeff-zero terms in place (order-stable). *n_out = the surviving count. */
static srmech_status_t ti_compact_terms(ti_ctx_t *c, ti_term_t *arr, size_t n,
                                        size_t *n_out)
{
    size_t i;
    size_t k = 0;
    srmech_status_t st;
    assert(c != NULL && (arr != NULL || n == 0u));
    assert(n_out != NULL);
    for (i = 0; i < n; i++) {
        if (srmech_bigint_is_zero(&arr[i].pref.coeff.num)) { continue; }
        if (k != i) {
            st = ti_mono_copy(c, &arr[k].pref, &arr[i].pref);
            if (st != SRMECH_OK) { return st; }
            {
                size_t t;
                for (t = 0; t < arr[i].n_thetas; t++) {
                    st = ti_mono_copy(c, &arr[k].targs[t], &arr[i].targs[t]);
                    if (st != SRMECH_OK) { return st; }
                }
            }
            arr[k].n_thetas = arr[i].n_thetas;
        }
        k++;
    }
    *n_out = k;
    return SRMECH_OK;
}

/* ---- variables / degree / character / pivot / nodes ------------------------- */

/* Mark s->present[idx]=1 for every symbol (except psym) with a nonzero exponent
 * on a theta argument OR THE PREFACTOR (rc210 defect-D3 fix: prefactor-only
 * symbols carry a character too -- dropping them merged a*theta(2x) - b*theta(2x)
 * into one falsely-cancelling class). Returns the count of distinct variables.
 * Mirrors the fixed thetasum._struct_variables. */
static size_t ti_collect_vars(const ti_ctx_t *c, const ti_term_t *terms, size_t n,
                              ti_scr_t *s)
{
    size_t ti;
    size_t j;
    size_t cnt = 0;
    assert(c != NULL && s != NULL);
    assert(terms != NULL || n == 0u);
    memset(s->present, 0, c->n_syms * sizeof(int));
    for (ti = 0; ti < n; ti++) {
        size_t a;
        for (j = 0; j < c->n_syms; j++) {
            if ((int)j == s->psym) { continue; }
            if (terms[ti].pref.exps[j] != 0) { s->present[j] = 1; }
        }
        for (a = 0; a < terms[ti].n_thetas; a++) {
            for (j = 0; j < c->n_syms; j++) {
                if ((int)j == s->psym) { continue; }
                if (terms[ti].targs[a].exps[j] != 0) { s->present[j] = 1; }
            }
        }
    }
    for (j = 0; j < c->n_syms; j++) { cnt += (size_t)s->present[j]; }
    return cnt;
}

/* deg(v) = max over terms of SUM over theta args of (arg.exps[v])^2 -- the TRUE
 * elliptic degree (quasi-period index = zeros per annulus) of a theta-product in
 * v (Rosengren Eq. 1.6: theta(c*v^e;p) gains a v^{-e^2} multiplier under v->p*v).
 * rc210: this feeds ONLY the per-character Z4 node count and the pivot choice --
 * never a p-order band. */
static int ti_deg(const ti_ctx_t *c, const ti_term_t *terms, size_t n, int v)
{
    size_t ti;
    int best = 0;
    assert(c != NULL && (terms != NULL || n == 0u));
    assert(v >= 0 && (size_t)v < c->n_syms);
    (void)c;
    for (ti = 0; ti < n; ti++) {
        size_t a;
        int acc = 0;
        for (a = 0; a < terms[ti].n_thetas; a++) {
            int32_t e = terms[ti].targs[a].exps[v];
            acc += (int)(e * e);
        }
        if (acc > best) { best = acc; }
    }
    return best;
}

/* The exact v-character of one term (mirrors thetasum._term_char_v): D = sum e^2
 * over the theta args; mu = p^{d} * prod_a [(-1)^{e_a} p^{-e_a(e_a-1)/2}
 * z_a^{-e_a}] with the v / p coordinates lifted out (pexp int; exps[v]=0). The
 * coefficient is exact Q (sign = Class-K parity flip). */
static srmech_status_t ti_char_of(ti_ctx_t *c, const ti_term_t *t, int v,
                                  ti_char_t *ch, ti_scr_t *s)
{
    size_t a;
    int flips = 0;
    srmech_status_t st;
    assert(c != NULL && t != NULL && ch != NULL && s != NULL);
    assert(v >= 0 && (size_t)v < c->n_syms);
    ch->D = 0;
    ch->pexp = t->pref.exps[v];                          /* d = pref.exp_of(v) */
    st = ti_mono_set_one(c, &ch->mu);
    if (st != SRMECH_OK) { return st; }
    for (a = 0; a < t->n_thetas; a++) {
        int32_t e = t->targs[a].exps[v];
        if (e == 0) { continue; }
        ch->D += e * e;
        if (ti_iabs(e) % 2 == 1) { flips++; }
        ch->pexp -= (e * (e - 1)) / 2;
        /* mu *= z^{-e} (coefficient part c^{-e} + exps scaled by -e, in one go). */
        st = ti_mono_pow(c, &s->m[11], &t->targs[a], -e, &s->m[9], &s->m[10], s);
        if (st != SRMECH_OK) { return st; }
        st = ti_mono_mul(c, &s->m[12], &ch->mu, &s->m[11], &s->g, &s->t0, &s->t1);
        if (st != SRMECH_OK) { return st; }
        st = ti_mono_copy(c, &ch->mu, &s->m[12]);
        if (st != SRMECH_OK) { return st; }
    }
    if (flips % 2 == 1) {                                /* (-1)^{e odd} parity */
        ch->mu.coeff.num.sign = -ch->mu.coeff.num.sign;
    }
    if (s->psym >= 0) {                                  /* fold p into pexp   */
        ch->pexp += ch->mu.exps[s->psym];
        ch->mu.exps[s->psym] = 0;
    }
    ch->mu.exps[v] = 0;                                  /* the v^{-D} part IS D */
    return SRMECH_OK;
}

/* 1 iff two v-characters are equal (exact: degree, p-power, Q coeff, exponents). */
static int ti_chars_eq(const ti_ctx_t *c, const ti_char_t *a, const ti_char_t *b)
{
    assert(c != NULL);
    assert(a != NULL && b != NULL);
    if (a->D != b->D || a->pexp != b->pexp) { return 0; }
    return ti_mono_eq(c, &a->mu, &b->mu);
}

/* Partition fr->terms by JOINT character over the present variables (ascending
 * symbol index = Python's sorted-name order): comp_of[i] = the component id of
 * term i (first-seen ids, matching Python's dict-insertion grouping). The char
 * table is TRANSIENT (arena mark reset by the caller); comp_of persists. */
static srmech_status_t ti_partition(ti_ctx_t *c, ti_frame_t *fr, ti_scr_t *s,
                                    size_t *n_comps)
{
    size_t nv = 0;
    size_t i;
    size_t j;
    ti_char_t *chars;
    srmech_status_t st;
    assert(c != NULL && fr != NULL && s != NULL && n_comps != NULL);
    assert(fr->comp_of != NULL);
    for (j = 0; j < c->n_syms; j++) { nv += (size_t)s->present[j]; }
    st = ti_bind_char_arr(c, &chars, fr->n_terms * ((nv == 0u) ? 1u : nv));
    if (st != SRMECH_OK) { return st; }
    for (i = 0; i < fr->n_terms; i++) {
        size_t vi = 0;
        for (j = 0; j < c->n_syms; j++) {
            if (!s->present[j]) { continue; }
            st = ti_char_of(c, &fr->terms[i], (int)j, &chars[i * nv + vi], s);
            if (st != SRMECH_OK) { return st; }
            vi++;
        }
    }
    *n_comps = 0;
    for (i = 0; i < fr->n_terms; i++) {
        size_t g;
        int found = 0;
        for (g = 0; g < i; g++) {
            size_t vi;
            int eq = 1;
            for (vi = 0; vi < nv; vi++) {
                if (!ti_chars_eq(c, &chars[i * nv + vi], &chars[g * nv + vi])) {
                    eq = 0;
                    break;
                }
            }
            if (eq) { fr->comp_of[i] = fr->comp_of[g]; found = 1; break; }
        }
        if (!found) { fr->comp_of[i] = (int32_t)(*n_comps); (*n_comps)++; }
    }
    return SRMECH_OK;
}

/* Strip every present variable of theta-degree 0 from the (single-character)
 * component: the character split guarantees a shared prefactor exponent d_v, so
 * v^d factors out of every term and v disappears (mirror of the Python strip;
 * unequal d_v would mean the split is broken -> SRMECH_ERR_INTERNAL, and the
 * Python dispatch declines to the pure oracle). Updates s->present in place. */
static srmech_status_t ti_strip_deg0(ti_ctx_t *c, ti_frame_t *fr, ti_scr_t *s)
{
    size_t j;
    size_t i;
    assert(c != NULL && fr != NULL && s != NULL);
    assert(fr->terms != NULL || fr->n_terms == 0u);
    for (j = 0; j < c->n_syms; j++) {
        int32_t d0;
        if (!s->present[j]) { continue; }
        if (ti_deg(c, fr->terms, fr->n_terms, (int)j) != 0) { continue; }
        d0 = fr->terms[0].pref.exps[j];
        for (i = 1; i < fr->n_terms; i++) {
            if (fr->terms[i].pref.exps[j] != d0) { return SRMECH_ERR_INTERNAL; }
        }
        for (i = 0; i < fr->n_terms; i++) { fr->terms[i].pref.exps[j] = 0; }
        s->present[j] = 0;
    }
    return SRMECH_OK;
}

/* Pick the interpolation variable v = argmin over present vars of (deg(v), index)
 * (fewest nodes; tie by symbol index = symbol NAME). Sets *out_v / *out_d. */
static void ti_pick_v(const ti_ctx_t *c, const ti_term_t *terms, size_t n,
                      const ti_scr_t *s, int *out_v, int *out_d)
{
    size_t j;
    int best_v = -1;
    int best_d = 0;
    assert(c != NULL && s != NULL && out_v != NULL && out_d != NULL);
    assert(terms != NULL || n == 0u);
    for (j = 0; j < c->n_syms; j++) {
        int d;
        if (!s->present[j]) { continue; }
        d = ti_deg(c, terms, n, (int)j);
        if (best_v < 0 || d < best_d) {
            best_v = (int)j;
            best_d = d;
        }
    }
    *out_v = best_v;
    *out_d = best_d;
}

/* The zero-MONOMIAL node of a LINEAR (exp +/-1) v-theta arg `a`: theta(alpha*v^e)=0
 * at v = (alpha without v)^(-1/e). node = rest.inv() if e==1 else rest, where rest =
 * a with the v-factor stripped. Writes `node`. */
static srmech_status_t ti_zero_node(ti_ctx_t *c, ti_mono_t *node, const ti_mono_t *a,
                                    int v, int32_t e, ti_scr_t *s)
{
    srmech_status_t st;
    assert(c != NULL && node != NULL && a != NULL && s != NULL);
    assert(e == 1 || e == -1);
    st = ti_mono_copy(c, &s->m[0], a);
    if (st != SRMECH_OK) { return st; }
    s->m[0].exps[v] = 0;                       /* rest = a without the v factor */
    if (e == 1) {
        return ti_mono_inv(c, node, &s->m[0]);
    }
    return ti_mono_copy(c, node, &s->m[0]);
}

/* Build up to `need` = D+1 interpolation nodes into `nodes`: the distinct
 * theta-factor zero monomials (first-seen order) then augment primes threaded via
 * `offset` -- with EVERY candidate (zero node AND prime) deduplicated against the
 * already-chosen nodes by EXACT monomial equality, coefficient included (rc210
 * defect-D4 fix: a theta(x/5) zero node IS the constant 5; appending the prime 5
 * again would double-count one point of Cx mod p^Z and under-count the
 * interpolation). *used = prime candidates consumed (dups included -- mirrors
 * thetasum._pick_nodes' offset threading); *filled = nodes actually placed
 * (< need iff the bounded prime scan exhausted: the caller declines to prove). */
static srmech_status_t ti_build_nodes(ti_ctx_t *c, ti_mono_t *nodes, size_t need,
                                      const ti_term_t *terms, size_t n, int v,
                                      int32_t offset, ti_scr_t *s, int32_t *used,
                                      size_t *filled)
{
    size_t ti;
    int32_t guard = 0;
    srmech_status_t st;
    assert(c != NULL && nodes != NULL && s != NULL && used != NULL);
    assert(filled != NULL && (terms != NULL || n == 0u));
    *filled = 0;
    for (ti = 0; ti < n && *filled < need; ti++) {
        size_t a;
        for (a = 0; a < terms[ti].n_thetas && *filled < need; a++) {
            size_t j;
            int seen = 0;
            int32_t e = terms[ti].targs[a].exps[v];
            if (e != 1 && e != -1) { continue; }
            st = ti_zero_node(c, &s->m[6], &terms[ti].targs[a], v, e, s);
            if (st != SRMECH_OK) { return st; }
            for (j = 0; j < *filled; j++) {
                if (ti_mono_eq(c, &nodes[j], &s->m[6])) { seen = 1; break; }
            }
            if (seen) { continue; }
            st = ti_mono_copy(c, &nodes[*filled], &s->m[6]);
            if (st != SRMECH_OK) { return st; }
            (*filled)++;
        }
    }
    *used = 0;
    while (*filled < need && guard < 4 * TI_NPRIMES) {
        size_t j;
        int seen = 0;
        int32_t idx = (offset + *used) % TI_NPRIMES;
        st = ti_set_prime(c, &s->m[6], TI_STRUCT_PRIMES[idx]);
        if (st != SRMECH_OK) { return st; }
        (*used)++;
        guard++;
        for (j = 0; j < *filled; j++) {
            if (ti_mono_eq(c, &nodes[j], &s->m[6])) { seen = 1; break; }
        }
        if (seen) { continue; }
        st = ti_mono_copy(c, &nodes[*filled], &s->m[6]);
        if (st != SRMECH_OK) { return st; }
        (*filled)++;
    }
    return SRMECH_OK;
}

/* ---- substitution (mirrors thetasum._struct_subst) -------------------------- */

/* out := substitute v -> node in `mono`: replace the v-factor v^{e_v} with
 * node^{e_v} (out = (mono without v) * node^{mono.exps[v]}). */
static srmech_status_t ti_subst_mono(ti_ctx_t *c, ti_mono_t *out, const ti_mono_t *mono,
                                     int v, const ti_mono_t *node, ti_scr_t *s)
{
    int32_t e;
    srmech_status_t st;
    assert(c != NULL && out != NULL && mono != NULL && node != NULL);
    assert(s != NULL);
    e = mono->exps[v];
    st = ti_mono_copy(c, &s->m[7], mono);           /* s->m[7] = mono without v */
    if (st != SRMECH_OK) { return st; }
    s->m[7].exps[v] = 0;
    if (e == 0) {
        return ti_mono_copy(c, out, &s->m[7]);
    }
    st = ti_mono_pow(c, &s->m[8], node, e, &s->m[9], &s->m[10], s);   /* node^e */
    if (st != SRMECH_OK) { return st; }
    return ti_mono_mul(c, out, &s->m[7], &s->m[8], &s->g, &s->t0, &s->t1);
}

/* Substitute v -> node in every term of `in` into freshly-bound `out`. */
static srmech_status_t ti_subst_terms(ti_ctx_t *c, ti_term_t **out, const ti_term_t *in,
                                      size_t n, int v, const ti_mono_t *node,
                                      size_t max_thetas, ti_scr_t *s)
{
    size_t i;
    srmech_status_t st;
    assert(c != NULL && out != NULL && s != NULL);
    assert(in != NULL || n == 0u);
    st = ti_bind_term_arr(c, out, (n == 0u) ? 1u : n, max_thetas);
    if (st != SRMECH_OK) { return st; }
    for (i = 0; i < n; i++) {
        size_t a;
        st = ti_subst_mono(c, &(*out)[i].pref, &in[i].pref, v, node, s);
        if (st != SRMECH_OK) { return st; }
        for (a = 0; a < in[i].n_thetas; a++) {
            st = ti_subst_mono(c, &(*out)[i].targs[a], &in[i].targs[a], v, node, s);
            if (st != SRMECH_OK) { return st; }
        }
        (*out)[i].n_thetas = in[i].n_thetas;
    }
    return SRMECH_OK;
}

/* ---- Z2: the generalized Weierstrass pair reduction (SHARED srmech_ts_*) ----- */

/* Try to prove the (single-character) component zero by the exact three-term
 * reduction over its live symbols, ascending (mirrors _pair_reduce_component:
 * the rewrite loop runs over the component's ACTUAL variables, not just x/y;
 * xsym/ysym feed only the canonical pair orientation). *proved = 1 on the empty
 * normal form. TRANSIENT: everything is bound above an arena mark and released. */
static srmech_status_t ti_pair_reduce(ti_ctx_t *c, ti_frame_t *fr, size_t max_thetas,
                                      ti_rt_t *rt, int *proved)
{
    size_t mark;
    size_t i;
    size_t n_rw = 0;
    size_t cap_rt = srmech_ts_work_cap(fr->n_terms, max_thetas);
    size_t max_pairs = (max_thetas / 2u) + 1u;
    int32_t *rw;
    srmech_ts_work_t w;
    int isz = 0;
    srmech_status_t st = SRMECH_OK;
    assert(c != NULL && fr != NULL && rt != NULL && proved != NULL);
    assert(fr->terms != NULL && fr->n_terms >= 1u);
    *proved = 0;
    mark = c->pool_cur;
    rw = (int32_t *)ti_take_words(c, c->n_syms);
    if (rw == NULL) { return SRMECH_ERR_OVERFLOW; }
    for (i = 0; i < c->n_syms; i++) {
        if (rt->s.present[i]) { rw[n_rw++] = (int32_t)i; }
    }
    st = srmech_ts_bind_rterm_arr(c, &w.cur, cap_rt, max_pairs);
    if (st == SRMECH_OK) { st = srmech_ts_bind_rterm_arr(c, &w.nxt, cap_rt, max_pairs); }
    if (st != SRMECH_OK) { c->pool_cur = mark; return st; }
    w.cap = cap_rt;
    w.n_cur = 0;
    w.n_nxt = 0;
    for (i = 0; i < fr->n_terms; i++) {
        int ok = 0;
        st = ti_mono_copy(c, &w.cur[i].pref, &fr->terms[i].pref);
        if (st != SRMECH_OK) { c->pool_cur = mark; return st; }
        w.cur[i].live = 1;
        st = srmech_ts_recover_pairs(c, &w.cur[i], fr->terms[i].targs,
                                     fr->terms[i].n_thetas, rt->s.xsym, rt->s.ysym,
                                     &ok, &rt->ts, rt->tsused);
        if (st != SRMECH_OK) { c->pool_cur = mark; return st; }
        if (!ok) { c->pool_cur = mark; return SRMECH_OK; }   /* not provable here */
        w.n_cur++;
    }
    st = srmech_ts_reduce_syms(c, &w, rt->s.xsym, rt->s.ysym, rw, n_rw, &isz, &rt->ts);
    c->pool_cur = mark;
    if (st != SRMECH_OK) { return st; }
    *proved = isz;
    return SRMECH_OK;
}

/* ---- the frame expansion (the head of thetasum._decide_struct) --------------- */

/* Set up a frame as a BRANCH with `n_children` children. */
static void ti_branch_setup(ti_ctx_t *c, ti_frame_t *fr, int kind, size_t n_children,
                            int32_t child_offset)
{
    assert(c != NULL && fr != NULL);
    assert(kind == 1 || kind == 2);
    fr->kind = kind;
    fr->n_children = n_children;
    fr->child_offset = child_offset;
    fr->next_child = 0;
    fr->child_mark = c->pool_cur;
    fr->state = 1;
}

/* Expansion stage 1: combine + variable scan + joint-character split. On return:
 * *done = 1 with *is_leaf + *verdict set (leaf) or fr branched (kind 2); *done = 0
 * -> fall through to stage 2 (single character), *nvars carrying the live count. */
static srmech_status_t ti_expand_split(ti_ctx_t *c, ti_frame_t *fr, size_t max_thetas,
                                       ti_rt_t *rt, size_t *nvars, int *done,
                                       int *is_leaf, int *verdict)
{
    size_t n_comps = 0;
    size_t mark;
    uint32_t *raw;
    srmech_status_t st;
    assert(c != NULL && fr != NULL && rt != NULL && nvars != NULL);
    assert(done != NULL && is_leaf != NULL && verdict != NULL);
    *done = 0;
    *is_leaf = 1;
    *verdict = 1;
    st = ti_combine(c, &fr->terms, &fr->n_terms, fr->raw, fr->n_raw, max_thetas,
                    &rt->s);
    if (st != SRMECH_OK) { return st; }
    if (fr->n_terms == 0u) { *done = 1; return SRMECH_OK; }      /* Z1: proven zero */
    *nvars = ti_collect_vars(c, fr->terms, fr->n_terms, &rt->s);
    if (*nvars == 0u) { return SRMECH_OK; }
    ti_align8(c);
    raw = ti_take_words(c, fr->n_terms);                          /* comp_of persists */
    if (raw == NULL) { return SRMECH_ERR_OVERFLOW; }
    fr->comp_of = (int32_t *)raw;
    mark = c->pool_cur;                                           /* chars transient */
    st = ti_partition(c, fr, &rt->s, &n_comps);
    if (st != SRMECH_OK) { return st; }
    c->pool_cur = mark;
    if (n_comps > 1u) {
        /* Z3s branch: every component must be (recursively) proven zero; children
         * inherit THIS frame's augment-prime offset (mirrors _decide_struct). */
        ti_branch_setup(c, fr, 2, n_comps, fr->offset);
        *done = 1;
        *is_leaf = 0;
    }
    return SRMECH_OK;
}

/* ---- Z5: the theta-constant-leaf PRIME-LIFT ZERO certificate (rc228) --------- *
 *
 * The 0-VARIABLE theta-CONSTANT leaf Sum c_i prod theta(rational; p) had no ZERO
 * certificate before rc228 (Z1 needs carrier cancellation, Z2/Z4 a LIVE variable,
 * the N-detect only NONZERO), so a genuinely-zero constant leaf declined and
 * is_zero false-negatived (the #695 wall, root-caused to this leaf). Z5 lifts a
 * constant PRIME rho back into an UNUSED symbol slot: the lifted single-variable
 * object L(v) satisfies L(v = rho) = leaf EXACTLY (substituting the integer prime
 * back reproduces every coeff), so if the EXACT Weierstrass +/- pair reduction
 * (ti_pair_reduce, the Z2 kernel -- a value-faithful rewrite proving L == 0 in v)
 * closes L to the empty normal form, then leaf = L(rho) == 0 by specialization.
 * Only ever proves ZERO; never a nonzero claim. The 1:1 mirror of
 * thetasum._z5_theta_constant_zero. Coeffs read as int64 (the leaf constants are
 * products of the small interpolation primes); a coeff beyond int64 makes Z5 N/A
 * at that leaf (not-proved -- SOUND, Z5 only ever ADDS zero proofs), and the
 * arbitrary-precision pure oracle covers any such leaf's lift. */

#define TI_Z5_MAX_PRIMES 16
#define TI_Z5_PRIME_CAP  32

/* Read bigint b as an int64 into *out; return 1 iff it fits [INT64_MIN, INT64_MAX]. */
static int ti_bi_to_i64(const srmech_bigint_t *b, int64_t *out)
{
    uint64_t mag;
    assert(b != NULL && out != NULL);
    assert(b->limbs != NULL || b->n == 0u);
    if (b->n == 0u) { *out = 0; return 1; }
    if (b->n == 1u) { mag = (uint64_t)b->limbs[0]; }
    else if (b->n == 2u) { mag = (uint64_t)b->limbs[0] | ((uint64_t)b->limbs[1] << 32); }
    else { return 0; }
    if (mag > (uint64_t)INT64_MAX) { return 0; }
    *out = (b->sign < 0) ? -(int64_t)mag : (int64_t)mag;
    return 1;
}

/* Insert prime p ASCENDING + deduplicated into prm[0..*n) (keeps the smallest
 * TI_Z5_PRIME_CAP; a duplicate or an over-cap larger prime is ignored). */
static void ti_prime_insert(int64_t *prm, size_t *n, int64_t p)
{
    size_t i = 0;
    size_t j;
    assert(prm != NULL && n != NULL);
    assert(p >= 2);
    while (i < *n && prm[i] < p) { i++; }
    if (i < *n && prm[i] == p) { return; }             /* already present              */
    if (i >= TI_Z5_PRIME_CAP) { return; }              /* larger than the kept smallest */
    if (*n < TI_Z5_PRIME_CAP) { (*n)++; }
    for (j = (*n > 0u) ? (*n - 1u) : 0u; j > i; j--) { prm[j] = prm[j - 1]; }
    prm[i] = p;
}

/* Trial-divide the magnitude of int64 v (v != 0) collecting its distinct prime
 * factors into prm (mirrors _leaf_prime_set: d = 2,3,... while d*d <= mag). */
static void ti_collect_i64_primes(int64_t v, int64_t *prm, size_t *n)
{
    int64_t mag = (v < 0) ? -v : v;                    /* Class-K magnitude, no abs()  */
    int64_t d = 2;
    assert(prm != NULL && n != NULL);
    assert(v != 0);
    while (d <= mag / d) {                              /* d*d <= mag, overflow-safe    */
        if (mag % d == 0) {
            ti_prime_insert(prm, n, d);
            while (mag % d == 0) { mag /= d; }
        }
        d++;
    }
    if (mag > 1) { ti_prime_insert(prm, n, mag); }
}

/* Collect one monomial's num + den prime factors; *decline = 1 iff a coeff > int64. */
static void ti_collect_mono_primes(const ti_mono_t *m, int64_t *prm, size_t *n,
                                   int *decline)
{
    int64_t v;
    assert(m != NULL && prm != NULL && n != NULL && decline != NULL);
    assert(m->coeff.num.limbs != NULL || m->coeff.num.n == 0u);
    if (!ti_bi_to_i64(&m->coeff.num, &v)) { *decline = 1; return; }
    if (v != 0) { ti_collect_i64_primes(v, prm, n); }
    if (!ti_bi_to_i64(&m->coeff.den, &v)) { *decline = 1; return; }
    if (v != 0) { ti_collect_i64_primes(v, prm, n); }
}

/* Collect the distinct primes across every coeff (pref + theta args) of the leaf
 * terms into prm; *decline = 1 iff any coeff exceeds int64 (-> the pure oracle). */
static void ti_leaf_collect_primes(const ti_term_t *terms,
                                   size_t n_terms, int64_t *prm, size_t *n_prm,
                                   int *decline)
{
    size_t ti;
    size_t a;
    assert(terms != NULL && prm != NULL);
    assert(n_prm != NULL && decline != NULL);
    *n_prm = 0;
    *decline = 0;
    for (ti = 0; ti < n_terms; ti++) {
        ti_collect_mono_primes(&terms[ti].pref, prm, n_prm, decline);
        if (*decline) { return; }
        for (a = 0; a < terms[ti].n_thetas; a++) {
            ti_collect_mono_primes(&terms[ti].targs[a], prm, n_prm, decline);
            if (*decline) { return; }
        }
    }
}

/* dst := src with `prime` factored out of the int64 coeff (num/den) and its net
 * valuation added to exps[lv] (mirrors _lift_prime_terms's lift_mono). *ok = 0
 * (decline) iff a coeff exceeds int64. */
static srmech_status_t ti_lift_mono(ti_ctx_t *c, ti_mono_t *dst, const ti_mono_t *src,
                                    int64_t prime, int lv, int *ok)
{
    int64_t num;
    int64_t den;
    int32_t e = 0;
    srmech_status_t st;
    assert(c != NULL && dst != NULL && src != NULL && ok != NULL);
    assert(prime >= 2 && lv >= 0);
    *ok = 1;
    st = ti_mono_copy(c, dst, src);                    /* copies coeff + exps          */
    if (st != SRMECH_OK) { return st; }
    if (!ti_bi_to_i64(&src->coeff.num, &num) || !ti_bi_to_i64(&src->coeff.den, &den)) {
        *ok = 0; return SRMECH_OK;
    }
    while (num != 0 && num % prime == 0) { num /= prime; e++; }   /* + from numerator  */
    while (den != 0 && den % prime == 0) { den /= prime; e--; }   /* - from denominator */
    st = srmech_bigint_set_i64(&dst->coeff.num, num);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&dst->coeff.den, den);
    if (st != SRMECH_OK) { return st; }
    dst->exps[lv] += e;
    return SRMECH_OK;
}

/* Build the prime-`prime` lift of `in`[0..n_terms) into `out` (caller-bound),
 * lifting every coeff into slot lv. *ok = 0 (decline) iff a coeff exceeds int64. */
static srmech_status_t ti_lift_terms(ti_ctx_t *c, ti_term_t *out, const ti_term_t *in,
                                     size_t n_terms, int64_t prime, int lv, int *ok)
{
    size_t i;
    size_t a;
    srmech_status_t st;
    assert(c != NULL && out != NULL && in != NULL && ok != NULL);
    assert(prime >= 2 && lv >= 0);
    *ok = 1;
    for (i = 0; i < n_terms; i++) {
        st = ti_lift_mono(c, &out[i].pref, &in[i].pref, prime, lv, ok);
        if (st != SRMECH_OK || !*ok) { return st; }
        for (a = 0; a < in[i].n_thetas; a++) {
            st = ti_lift_mono(c, &out[i].targs[a], &in[i].targs[a], prime, lv, ok);
            if (st != SRMECH_OK || !*ok) { return st; }
        }
        out[i].n_thetas = in[i].n_thetas;
    }
    return SRMECH_OK;
}

/* The Z5 driver: try each present prime lift into a free slot; *proved = 1 on the
 * first lift the exact +/- pair reduction closes to empty (a genuine ZERO cert).
 * A coeff beyond int64 makes Z5 not-applicable at this leaf (*proved stays 0 --
 * SOUND, never a false zero; the pure oracle covers it). Transient: each attempt
 * above an arena mark, released before the next. */
static srmech_status_t ti_z5_leaf(ti_ctx_t *c, ti_frame_t *fr, size_t max_thetas,
                                  ti_rt_t *rt, int *proved)
{
    int64_t prm[TI_Z5_PRIME_CAP];
    size_t n_prm = 0;
    size_t k;
    size_t j;
    int lv = -1;
    int decline = 0;
    srmech_status_t st;
    assert(c != NULL && fr != NULL && rt != NULL && proved != NULL);
    assert(fr->terms != NULL && fr->n_terms >= 1u);
    *proved = 0;
    if (fr->n_terms < 2u) { return SRMECH_OK; }        /* Z5 needs cancellation        */
    for (j = 0; j < c->n_syms; j++) {                  /* first unused non-p lift slot */
        if ((int)j != rt->s.psym && !rt->s.present[j]) { lv = (int)j; break; }
    }
    if (lv < 0) { return SRMECH_OK; }                  /* no free slot -> cannot lift  */
    ti_leaf_collect_primes(fr->terms, fr->n_terms, prm, &n_prm, &decline);
    if (decline) { return SRMECH_OK; }                 /* coeff > int64 -> Z5 N/A here */
    for (k = 0; k < n_prm && k < (size_t)TI_Z5_MAX_PRIMES; k++) {
        size_t mark = c->pool_cur;
        ti_frame_t lf;
        ti_term_t *lifted = NULL;
        int ok = 1;
        int pv = 0;
        st = ti_bind_term_arr(c, &lifted, fr->n_terms, max_thetas);
        if (st != SRMECH_OK) { c->pool_cur = mark; return st; }
        st = ti_lift_terms(c, lifted, fr->terms, fr->n_terms, prm[k], lv, &ok);
        if (st != SRMECH_OK) { c->pool_cur = mark; return st; }
        if (ok) {
            memset(&lf, 0, sizeof(lf));
            lf.terms = lifted;
            lf.n_terms = fr->n_terms;
            rt->s.present[lv] = 1;
            st = ti_pair_reduce(c, &lf, max_thetas, rt, &pv);
            rt->s.present[lv] = 0;
            if (st != SRMECH_OK) { c->pool_cur = mark; return st; }
        }
        c->pool_cur = mark;
        if (pv) { *proved = 1; return SRMECH_OK; }
    }
    return SRMECH_OK;
}

/* Expansion stage 2 (single joint character): strip degree-0 symbols, the N1 /
 * 0-variable leaves, the Z2 pair reduction, then the Z4 node branch. */
static srmech_status_t ti_expand_single(ti_ctx_t *c, ti_frame_t *fr, size_t max_thetas,
                                        ti_rt_t *rt, size_t nvars, int *is_leaf,
                                        int *verdict)
{
    size_t n_live = 0;
    size_t j;
    size_t filled = 0;
    int32_t used = 0;
    int proved = 0;
    int v;
    int d;
    srmech_status_t st;
    assert(c != NULL && fr != NULL && rt != NULL);
    assert(is_leaf != NULL && verdict != NULL);
    *is_leaf = 1;
    *verdict = 1;
    if (nvars >= 1u) {
        st = ti_strip_deg0(c, fr, &rt->s);
        if (st != SRMECH_OK) { return st; }
    }
    for (j = 0; j < c->n_syms; j++) { n_live += (size_t)rt->s.present[j]; }
    if (fr->n_terms == 1u) { *verdict = 0; return SRMECH_OK; }    /* N1: not proven */
    if (n_live == 0u) {                                           /* 0-var residue  */
        int z5 = 0;
        st = ti_z5_leaf(c, fr, max_thetas, rt, &z5);             /* Z5 prime-lift  */
        if (st != SRMECH_OK) { return st; }                      /* decline -> pure */
        *verdict = z5 ? 1 : 0;                                    /* 1 = proven zero */
        return SRMECH_OK;
    }
    st = ti_pair_reduce(c, fr, max_thetas, rt, &proved);          /* Z2             */
    if (st != SRMECH_OK) { return st; }
    if (proved) { return SRMECH_OK; }                             /* proven zero    */
    ti_pick_v(c, fr->terms, fr->n_terms, &rt->s, &v, &d);
    st = ti_bind_mono_arr(c, &fr->nodes, (size_t)d + 1u);         /* nodes persist  */
    if (st != SRMECH_OK) { return st; }
    st = ti_build_nodes(c, fr->nodes, (size_t)d + 1u, fr->terms, fr->n_terms, v,
                        fr->offset, &rt->s, &used, &filled);
    if (st != SRMECH_OK) { return st; }
    if (filled < (size_t)d + 1u) { *verdict = 0; return SRMECH_OK; }  /* not proven */
    fr->v = v;
    ti_branch_setup(c, fr, 1, (size_t)d + 1u, fr->offset + used); /* Z4 branch      */
    *is_leaf = 0;
    return SRMECH_OK;
}

/* Expand a NEW frame: stage 1 (combine / split) then stage 2 (single character).
 * On a leaf, *verdict = 1 iff PROVEN zero (Z1 / Z2); on a branch, fr is set up
 * (kind 1 nodes or kind 2 components) and *is_leaf = 0. */
static srmech_status_t ti_expand(ti_ctx_t *c, ti_frame_t *fr, size_t max_thetas,
                                 ti_rt_t *rt, int *is_leaf, int *verdict)
{
    size_t nvars = 0;
    int done = 0;
    srmech_status_t st;
    assert(c != NULL && fr != NULL);
    assert(rt != NULL && is_leaf != NULL && verdict != NULL);
    st = ti_expand_split(c, fr, max_thetas, rt, &nvars, &done, is_leaf, verdict);
    if (st != SRMECH_OK) { return st; }
    if (done) { return SRMECH_OK; }
    return ti_expand_single(c, fr, max_thetas, rt, nvars, is_leaf, verdict);
}

/* Materialize child `k` of an EXPANDED branch frame: the node-substituted terms
 * (kind 1) or the k-th character component's term subset (kind 2). *out_off = the
 * augment-prime offset the child resumes from. */
static srmech_status_t ti_child_raw(ti_ctx_t *c, const ti_frame_t *fr, size_t k,
                                    size_t max_thetas, ti_rt_t *rt,
                                    ti_term_t **out_raw, size_t *out_n,
                                    int32_t *out_off)
{
    srmech_status_t st;
    assert(c != NULL && fr != NULL && rt != NULL);
    assert(out_raw != NULL && out_n != NULL && out_off != NULL);
    if (fr->kind == 1) {
        st = ti_subst_terms(c, out_raw, fr->terms, fr->n_terms, fr->v,
                            &fr->nodes[k], max_thetas, &rt->s);
        if (st != SRMECH_OK) { return st; }
        *out_n = fr->n_terms;
        *out_off = fr->child_offset;
        return SRMECH_OK;
    }
    {
        size_t i;
        size_t m = 0;
        for (i = 0; i < fr->n_terms; i++) {
            if (fr->comp_of[i] == (int32_t)k) { m++; }
        }
        if (m == 0u) { return SRMECH_ERR_INTERNAL; }
        st = ti_bind_term_arr(c, out_raw, m, max_thetas);
        if (st != SRMECH_OK) { return st; }
        m = 0;
        for (i = 0; i < fr->n_terms; i++) {
            size_t a;
            if (fr->comp_of[i] != (int32_t)k) { continue; }
            st = ti_mono_copy(c, &(*out_raw)[m].pref, &fr->terms[i].pref);
            if (st != SRMECH_OK) { return st; }
            for (a = 0; a < fr->terms[i].n_thetas; a++) {
                st = ti_mono_copy(c, &(*out_raw)[m].targs[a], &fr->terms[i].targs[a]);
                if (st != SRMECH_OK) { return st; }
            }
            (*out_raw)[m].n_thetas = fr->terms[i].n_thetas;
            m++;
        }
        *out_n = m;
        *out_off = fr->child_offset;      /* == fr->offset for a component branch */
    }
    return SRMECH_OK;
}

/* Build the next child of frames[depth] and initialise its frame slot. Advances
 * the parent's next_child. */
static srmech_status_t ti_push_child(ti_ctx_t *c, ti_frame_t *frames, long depth,
                                     size_t max_thetas, ti_rt_t *rt)
{
    ti_frame_t *fr = &frames[depth];
    ti_frame_t *ch = &frames[depth + 1];
    size_t k = fr->next_child;
    srmech_status_t st;
    assert(c != NULL && frames != NULL && rt != NULL);
    assert(depth >= 0 && k < fr->n_children);
    fr->next_child++;
    ch->frame_mark = c->pool_cur;
    st = ti_child_raw(c, fr, k, max_thetas, rt, &ch->raw, &ch->n_raw, &ch->offset);
    if (st != SRMECH_OK) { return st; }
    ch->state = 0;
    return SRMECH_OK;
}

/* The DFS: proven-zero IFF every leaf of the certificate tree is proven zero (the
 * bool of the three-valued _decide_struct -- its NONZERO/UNKNOWN refinement never
 * feeds a ZERO, so the AND-fold is the exact mirror). Iterative, arena-mark
 * reclaimed (Rule 1: no recursion). `start_offset` seeds frame 0's augment-prime
 * offset (0 for a fresh root; the accumulated offset when the rc103 parallel peer
 * resumes a REPLAYED subtree). */
static srmech_status_t ti_decide(ti_ctx_t *c, ti_term_t *root, size_t n_root,
                                 int32_t start_offset, size_t max_thetas, ti_rt_t *rt,
                                 int *out_is_zero)
{
    long depth = 0;
    int is_leaf;
    int verdict;
    srmech_status_t st;
    assert(c != NULL && rt != NULL && out_is_zero != NULL);
    assert(root != NULL || n_root == 0u);
    *out_is_zero = 1;
    rt->frames[0].raw = root;
    rt->frames[0].n_raw = n_root;
    rt->frames[0].offset = start_offset;
    rt->frames[0].frame_mark = c->pool_cur;
    rt->frames[0].state = 0;
    while (depth >= 0) {
        ti_frame_t *fr = &rt->frames[depth];
        if (fr->state == 0) {
            st = ti_expand(c, fr, max_thetas, rt, &is_leaf, &verdict);
            if (st != SRMECH_OK) { return st; }
            if (is_leaf) {
                if (!verdict) { *out_is_zero = 0; return SRMECH_OK; }
                c->pool_cur = fr->frame_mark;
                depth--;
                continue;
            }
        }
        if (fr->next_child >= fr->n_children) {
            c->pool_cur = fr->frame_mark;
            depth--;
            continue;
        }
        c->pool_cur = fr->child_mark;
        if ((size_t)(depth + 1) >= rt->fcap) { return SRMECH_ERR_OVERFLOW; }
        st = ti_push_child(c, rt->frames, depth, max_thetas, rt);
        if (st != SRMECH_OK) { return st; }
        depth++;
    }
    return SRMECH_OK;
}

/* ---- wire parse + runtime bind + public entry + ws sizing -------------------- */

/* Parse the flat wire form into `terms` (identical layout to srmech_thetasum_is_zero:
 * term0.pref, term0.theta0..K, term1.pref, ... over coeff_num/coeff_den + exps rows). */
static srmech_status_t ti_parse(ti_ctx_t *c, ti_term_t *terms, size_t n_terms,
                                const size_t *term_nthetas,
                                const srmech_bigint_t *coeff_num,
                                const srmech_bigint_t *coeff_den,
                                const int32_t *exps_flat)
{
    size_t ti;
    size_t mi = 0;
    size_t ej = 0;
    srmech_status_t st;
    assert(c != NULL && terms != NULL && term_nthetas != NULL);
    assert(coeff_num != NULL && coeff_den != NULL && exps_flat != NULL);
    for (ti = 0; ti < n_terms; ti++) {
        size_t k;
        st = srmech_bigint_copy(&terms[ti].pref.coeff.num, &coeff_num[mi]);
        if (st == SRMECH_OK) { st = srmech_bigint_copy(&terms[ti].pref.coeff.den, &coeff_den[mi]); }
        if (st != SRMECH_OK) { return st; }
        memcpy(terms[ti].pref.exps, exps_flat + ej, c->n_syms * sizeof(int32_t));
        mi++;
        ej += c->n_syms;
        for (k = 0; k < term_nthetas[ti]; k++) {
            st = srmech_bigint_copy(&terms[ti].targs[k].coeff.num, &coeff_num[mi]);
            if (st == SRMECH_OK) { st = srmech_bigint_copy(&terms[ti].targs[k].coeff.den, &coeff_den[mi]); }
            if (st != SRMECH_OK) { return st; }
            memcpy(terms[ti].targs[k].exps, exps_flat + ej, c->n_syms * sizeof(int32_t));
            mi++;
            ej += c->n_syms;
        }
        terms[ti].n_thetas = term_nthetas[ti];
    }
    return SRMECH_OK;
}

static size_t ti_max_thetas(const size_t *term_nthetas, size_t n_terms)
{
    size_t i;
    size_t mx = 0;
    assert(term_nthetas != NULL || n_terms == 0u);
    for (i = 0; i < n_terms; i++) {
        assert(term_nthetas != NULL);
        if (term_nthetas[i] > mx) { mx = term_nthetas[i]; }
    }
    return mx;
}

/* Carve `ws` into the bump pool + a trailing bigint scratch region (mirrors the
 * thetasum arena_init). */
static srmech_status_t ti_arena_init(ti_ctx_t *c, void *ws, size_t ws_len)
{
    uint32_t *base = (uint32_t *)ws;
    size_t words = ws_len / sizeof(uint32_t);
    size_t scratch_words = (size_t)c->cap * 16u + 512u;
    assert(c != NULL);
    assert((uintptr_t)ws % 8u == 0u || ws == NULL);
    if (ws == NULL || words < scratch_words + 64u) { return SRMECH_ERR_OVERFLOW; }
    c->pool = base;
    c->pool_words = words - scratch_words;
    c->pool_cur = 0u;
    c->scratch = (void *)(base + (words - scratch_words));
    c->scratch_len = scratch_words * sizeof(uint32_t);
    return SRMECH_OK;
}

/* Bind the DFS frame array (one slot per possible depth: a character split adds at
 * most one extra level per interpolation level, so 2*(n_syms+2)+4 bounds the path). */
static srmech_status_t ti_bind_frames(ti_ctx_t *c, ti_frame_t **out, size_t count)
{
    size_t words;
    uint32_t *raw;
    assert(c != NULL && out != NULL);
    assert(count >= 1u);
    ti_align8(c);
    words = (count * sizeof(ti_frame_t) + sizeof(uint32_t) - 1u) / sizeof(uint32_t);
    raw = ti_take_words(c, words);
    if (raw == NULL) { return SRMECH_ERR_OVERFLOW; }
    *out = (ti_frame_t *)raw;
    memset(*out, 0, count * sizeof(ti_frame_t));
    return SRMECH_OK;
}

/* Bind the whole per-arena runtime bundle (general scratch + SHARED pair scratch +
 * recover flags + frames). Sets the symbol indices. */
static srmech_status_t ti_bind_rt(ti_ctx_t *c, ti_rt_t *rt, size_t max_thetas,
                                  int xsym, int ysym, int psym)
{
    uint32_t *raw;
    srmech_status_t st;
    assert(c != NULL && rt != NULL);
    assert(c->cap > 0u);
    st = ti_bind_scr(c, &rt->s);
    if (st == SRMECH_OK) { st = srmech_ts_bind_scr(c, &rt->ts, max_thetas); }
    if (st != SRMECH_OK) { return st; }
    raw = ti_take_words(c, (max_thetas == 0u) ? 1u : max_thetas);
    if (raw == NULL) { return SRMECH_ERR_OVERFLOW; }
    rt->tsused = (int *)raw;
    rt->fcap = 2u * (c->n_syms + 2u) + 4u;
    st = ti_bind_frames(c, &rt->frames, rt->fcap);
    if (st != SRMECH_OK) { return st; }
    rt->s.psym = psym;
    rt->s.xsym = xsym;
    rt->s.ysym = ysym;
    rt->ts.psym = psym;
    return SRMECH_OK;
}

/* Decide whether the cleared ThetaSum numerator is CERTIFICATE-PROVEN identically
 * zero -- the 1:1 mirror of the pure-Python sound bool
 * ThetaSum._is_zero_interpolation (rc210). Wire form + args identical to
 * srmech_thetasum_is_zero. *out_is_zero = 1 iff proven == 0; 0 = not proven
 * (nonzero OR honest decline). Caller arena `ws`. */
srmech_status_t srmech_thetasum_is_zero_interpolation(
    size_t n_syms, int xsym, int ysym, int psym, size_t n_terms,
    const size_t *term_nthetas, const srmech_bigint_t *coeff_num,
    const srmech_bigint_t *coeff_den, const int32_t *exps_flat,
    uint32_t coeff_cap, int *out_is_zero, void *ws, size_t ws_len)
{
    ti_ctx_t c = {0};
    ti_term_t *terms = NULL;
    ti_rt_t rt;
    size_t max_thetas;
    srmech_status_t st;
    assert(out_is_zero != NULL);
    assert(term_nthetas != NULL || n_terms == 0u);
    if (out_is_zero == NULL) { return SRMECH_ERR_NULL_ARG; }
    *out_is_zero = 1;
    if (n_terms == 0u) { return SRMECH_OK; }
    if (term_nthetas == NULL || coeff_num == NULL || coeff_den == NULL || exps_flat == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    memset(&rt, 0, sizeof(rt));
    c.n_syms = (n_syms == 0u) ? 1u : n_syms;
    c.cap = (coeff_cap < 4u) ? 4u : coeff_cap;
    max_thetas = ti_max_thetas(term_nthetas, n_terms);
    st = ti_arena_init(&c, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    st = ti_bind_rt(&c, &rt, max_thetas, xsym, ysym, psym);
    if (st == SRMECH_OK) { st = ti_bind_term_arr(&c, &terms, n_terms, max_thetas); }
    if (st != SRMECH_OK) { return st; }
    st = ti_parse(&c, terms, n_terms, term_nthetas, coeff_num, coeff_den, exps_flat);
    if (st != SRMECH_OK) { return st; }
    return ti_decide(&c, terms, n_terms, 0, max_thetas, &rt, out_is_zero);
}

/* The minimum `ws_len` BYTES srmech_thetasum_is_zero_interpolation needs for the
 * given shape (rc210 certificate-recursion sizer). The old base-case series grid
 * is GONE (no band on the True side), so the arena is the DFS path (two term
 * arrays + the node monomials + comp ids per level) + the transient character
 * table + the transient Z2 pair-reduce work buffers + the runtime bundle.
 * `max_theta_sq_sum` (the max per-term/per-variable sum of squared theta
 * exponents) bounds the per-frame node count D+1; `max_abs_exp` rides only as
 * slack (the coefficient growth it used to size is the caller's coeff_cap job).
 * A shortfall on a pathological input trips SRMECH_ERR_OVERFLOW and the caller
 * falls to the sound pure oracle. Signature UNCHANGED from rc102 -> ABI stays. */
size_t srmech_thetasum_is_zero_interpolation_ws_bound2(size_t n_syms, size_t n_terms,
                                                       size_t max_thetas,
                                                       size_t coeff_limbs,
                                                       size_t max_abs_exp,
                                                       size_t max_theta_sq_sum)
{
    size_t cap = (coeff_limbs < 4u) ? 4u : coeff_limbs;
    size_t ns = (n_syms == 0u) ? 1u : n_syms;
    size_t nt = (n_terms == 0u) ? 1u : n_terms;
    size_t depth = 2u * (ns + 2u) + 4u;
    size_t mono_words = 2u * cap + ns + 8u;
    size_t term_words = (max_thetas + 1u) * mono_words + ns + 96u;
    size_t nodes_words = (max_theta_sq_sum + 2u) * mono_words;
    size_t level_words = 2u * nt * term_words + nt * 4u + nodes_words + 128u;
    size_t char_words = nt * ns * (mono_words + 16u) + 256u;
    size_t pairs = (max_thetas / 2u) + 1u;
    size_t cap_rt = srmech_ts_work_cap(nt, max_thetas);
    size_t rterm_words = mono_words + pairs * 2u * mono_words + 64u;
    size_t z2_words = 2u * (cap_rt + 1u) * rterm_words
                      + (SRMECH_TS_SCR_MONOS + SRMECH_TS_REWRITE_MONOS + max_thetas
                         + 8u) * mono_words + 12u * mono_words + pairs + max_thetas
                      + 512u;
    size_t rt_words = (TI_SCR_MONOS + 8u) * mono_words + ns
                      + depth * (sizeof(ti_frame_t) / 4u + 8u) + 512u;
    size_t scratch_words = cap * 16u + 512u;
    size_t z5_words = nt * term_words + 128u;          /* rc228: the Z5 lift copy      */
    size_t total = depth * level_words + char_words + z2_words + rt_words
                   + scratch_words + z5_words + max_abs_exp + 4096u;
    assert(cap >= 4u);
    assert(total >= scratch_words);
    return total * sizeof(uint32_t);
}

/* Legacy 5-arg entry (pre-rc102). Passes `max_abs_exp^2` as the degree bound, so a
 * stale caller still links + gets a valid (conservative) sizing. New callers use
 * srmech_thetasum_is_zero_interpolation_ws_bound2. */
size_t srmech_thetasum_is_zero_interpolation_ws_bound(size_t n_syms, size_t n_terms,
                                                      size_t max_thetas,
                                                      size_t coeff_limbs,
                                                      size_t max_abs_exp)
{
    size_t sq = max_abs_exp * max_abs_exp;
    assert(max_abs_exp == 0u || sq / max_abs_exp == max_abs_exp);   /* no square overflow */
    assert(sq >= max_abs_exp || max_abs_exp <= 1u);                 /* square monotone */
    return srmech_thetasum_is_zero_interpolation_ws_bound2(
        n_syms, n_terms, max_thetas, coeff_limbs, max_abs_exp, sq);
}

/* ======================================================================== *
 * rc103 -- the CHIRALITY-PRESERVING native PARALLEL fan-out, retargeted in
 * rc210 onto the certificate tree.
 *
 * MODEL. Bounded-depth top-level fan-out: BFS-PEEL the top branching levels of
 * the CERTIFICATE tree (a branch's children are its character components OR its
 * interpolation nodes -- whatever ti_expand produces) into a fixed array of
 * independent SUB-PROBLEMS (each a root->node PATH), then run the sequential
 * ti_decide DFS on each task over a flat PAL worker pool. AND-fold the per-task
 * verdicts with a best-effort cancel flag. Bit-identical serial fallback when
 * the PAL has no threads OR n_workers <= 1.
 *
 * PATH REPLAY: a task is a small integer PATH; a worker RE-DERIVES its
 * sub-problem by replaying the path from the read-only parsed root with the
 * SAME deterministic ti_expand / ti_child_raw the serial DFS uses, threading the
 * SAME augment-prime offsets -- so the peel frontier is a COMPLETE antichain of
 * the serial tree and ANDing the per-task verdicts EQUALS the serial verdict,
 * ORDER-FREE (`task_order` 0 forward / 1 reverse makes that testable).
 *
 * ARENA: W disjoint contiguous slices of the caller ws (klein4's disjoint-slice
 * race-freedom argument); the shared parsed root is READ-ONLY during the run.
 * The cancel flag is best-effort (volatile int, sticky 0->1); correctness rides
 * the disjoint result slots + the join barrier, never the flag.
 *
 * ABI: symbols + wire unchanged (rc210 is an internal rebuild) -> stays 4.
 * ======================================================================== */

#define TIP_MAX_WORKERS     32   /* worker/thread stack-array cap                */
#define TIP_MAX_TASKS      256   /* task-frontier cap (control band is fixed)    */
#define TIP_MAX_PEEL_DEPTH   8   /* max root->node path length peeled            */
#define TIP_TARGET_MULT      2   /* aim for K*n_workers tasks (K=2)              */

/* One peeled sub-problem: a root->node path (nodes[0..len-1]) + a known-leaf
 * flag (so the peel does not try to expand a leaf). len == 0 is the whole root. */
typedef struct tip_task {
    int32_t len;
    int32_t terminal;
    int32_t nodes[TIP_MAX_PEEL_DEPTH];
} tip_task_t;

/* The read-only shared wire bundle (parsed once into the shared region). */
typedef struct tip_wire {
    size_t                 n_syms;
    int                    xsym;
    int                    ysym;
    int                    psym;
    size_t                 n_terms;
    const size_t          *term_nthetas;
    const srmech_bigint_t *coeff_num;
    const srmech_bigint_t *coeff_den;
    const int32_t         *exps_flat;
    uint32_t               coeff_cap;
    size_t                 max_thetas;
} tip_wire_t;

/* Fixed control-band bytes = the task-frontier double-buffer (two tip_task_t
 * arrays), 8-aligned. Independent of n_workers. */
static size_t tip_control_bytes(void)
{
    size_t raw = 2u * (size_t)TIP_MAX_TASKS * sizeof(tip_task_t);
    assert(sizeof(tip_task_t) >= 8u);
    assert(raw >= sizeof(tip_task_t));
    return (raw + 7u) & ~(size_t)7u;
}

/* Parse the root terms ONCE into a dedicated SHARED region (its own ctx / pool),
 * so every worker + the peel REPLAY from these read-only terms. */
static srmech_status_t tip_parse_root(const tip_wire_t *w, void *region, size_t region_len,
                                      ti_ctx_t *rc, ti_term_t **root)
{
    srmech_status_t st;
    assert(w != NULL && rc != NULL && root != NULL);
    assert(region != NULL || region_len == 0u);
    rc->n_syms = (w->n_syms == 0u) ? 1u : w->n_syms;
    rc->cap = (w->coeff_cap < 4u) ? 4u : w->coeff_cap;
    st = ti_arena_init(rc, region, region_len);
    if (st != SRMECH_OK) { return st; }
    st = ti_bind_term_arr(rc, root, w->n_terms, w->max_thetas);
    if (st != SRMECH_OK) { return st; }
    return ti_parse(rc, *root, w->n_terms, w->term_nthetas, w->coeff_num, w->coeff_den,
                    w->exps_flat);
}

/* Arena-init a WORKER `slice` + bind its runtime bundle (NO parse -- the worker
 * replays from the SHARED root). The caller passes ZEROED ctx / rt. */
static srmech_status_t tip_worker_setup(const tip_wire_t *w, void *slice, size_t slice_len,
                                        ti_ctx_t *c, ti_rt_t *rt)
{
    srmech_status_t st;
    assert(w != NULL && c != NULL && rt != NULL);
    assert(slice != NULL || slice_len == 0u);
    c->n_syms = (w->n_syms == 0u) ? 1u : w->n_syms;
    c->cap = (w->coeff_cap < 4u) ? 4u : w->coeff_cap;
    st = ti_arena_init(c, slice, slice_len);
    if (st != SRMECH_OK) { return st; }
    return ti_bind_rt(c, rt, w->max_thetas, w->xsym, w->ysym, w->psym);
}

/* ONE peel/replay level: expand `cur` (a scratch frame) and materialize child
 * `node_index`. SRMECH_ERR_INTERNAL if the frame is a LEAF or node_index is out
 * of range -- a malformed path (the caller declines to serial). `*off` threads
 * the augment-prime offset (in: this level's offset; out: the child's). */
static srmech_status_t tip_descend(ti_ctx_t *c, ti_rt_t *rt, ti_term_t *cur,
                                   size_t ncur, int32_t node_index, size_t max_thetas,
                                   int32_t *off, ti_term_t **out_next, size_t *out_n)
{
    ti_frame_t fr;
    int is_leaf = 0;
    int verdict = 0;
    srmech_status_t st;
    assert(c != NULL && rt != NULL && off != NULL);
    assert(out_next != NULL && out_n != NULL);
    memset(&fr, 0, sizeof(fr));
    fr.raw = cur;
    fr.n_raw = ncur;
    fr.offset = *off;
    fr.frame_mark = c->pool_cur;
    st = ti_expand(c, &fr, max_thetas, rt, &is_leaf, &verdict);
    if (st != SRMECH_OK) { return st; }
    if (is_leaf) { return SRMECH_ERR_INTERNAL; }
    if (node_index < 0 || (size_t)node_index >= fr.n_children) {
        return SRMECH_ERR_INTERNAL;
    }
    st = ti_child_raw(c, &fr, (size_t)node_index, max_thetas, rt, out_next, out_n, off);
    if (st != SRMECH_OK) { return st; }
    return SRMECH_OK;
}

/* Replay a task PATH from `root`: descend one level per path step, accumulating
 * the augment-prime offset. *out_cur / *out_n = the sub-problem raw terms at the
 * path end; *out_off = the offset ti_decide must resume from. */
static srmech_status_t tip_replay(ti_ctx_t *c, ti_rt_t *rt, ti_term_t *root,
                                  size_t n_root, const tip_task_t *task,
                                  size_t max_thetas, ti_term_t **out_cur,
                                  size_t *out_n, int32_t *out_off)
{
    ti_term_t *cur = root;
    size_t ncur = n_root;
    int32_t off = 0;
    int32_t lvl;
    srmech_status_t st;
    assert(c != NULL && rt != NULL && task != NULL);
    assert(out_cur != NULL && out_n != NULL && out_off != NULL);
    for (lvl = 0; lvl < task->len; lvl++) {
        ti_term_t *nxt;
        size_t nn;
        st = tip_descend(c, rt, cur, ncur, task->nodes[lvl], max_thetas, &off,
                         &nxt, &nn);
        if (st != SRMECH_OK) { return st; }
        cur = nxt;
        ncur = nn;
    }
    *out_cur = cur;
    *out_n = ncur;
    *out_off = off;
    return SRMECH_OK;
}

/* Run ONE task to a verdict in `slice`: worker-setup -> replay the path from the
 * SHARED root -> ti_decide the sub-DFS from the replayed frontier + resumed
 * offset (bit-identical to the serial DFS at this path depth). */
static srmech_status_t tip_run_subproblem(const tip_wire_t *w, ti_term_t *root,
                                          size_t n_root, const tip_task_t *task,
                                          void *slice, size_t slice_len, int *out_verdict)
{
    ti_ctx_t c;
    ti_rt_t rt;
    ti_term_t *cur;
    size_t ncur;
    int32_t off;
    srmech_status_t st;
    assert(w != NULL && task != NULL && out_verdict != NULL);
    assert(root != NULL || n_root == 0u);
    memset(&c, 0, sizeof(c));
    memset(&rt, 0, sizeof(rt));
    st = tip_worker_setup(w, slice, slice_len, &c, &rt);
    if (st != SRMECH_OK) { return st; }
    st = tip_replay(&c, &rt, root, n_root, task, w->max_thetas, &cur, &ncur, &off);
    if (st != SRMECH_OK) { return st; }
    return ti_decide(&c, cur, ncur, off, w->max_thetas, &rt, out_verdict);
}

/* Classify the node at a task PATH: *out_children = -1 iff it is a LEAF, else the
 * branch child count. Serial peel only; replays from the SHARED root in `slice`
 * (reset each call). */
static srmech_status_t tip_peel_count(const tip_wire_t *w, ti_term_t *root,
                                      size_t n_root, const tip_task_t *task,
                                      void *slice, size_t slice_len, int *out_children)
{
    ti_ctx_t c;
    ti_rt_t rt;
    ti_term_t *cur;
    size_t ncur;
    int32_t off;
    ti_frame_t fr;
    int is_leaf = 0;
    int verdict = 0;
    srmech_status_t st;
    assert(w != NULL && task != NULL && out_children != NULL);
    assert(root != NULL || n_root == 0u);
    memset(&c, 0, sizeof(c));
    memset(&rt, 0, sizeof(rt));
    st = tip_worker_setup(w, slice, slice_len, &c, &rt);
    if (st != SRMECH_OK) { return st; }
    st = tip_replay(&c, &rt, root, n_root, task, w->max_thetas, &cur, &ncur, &off);
    if (st != SRMECH_OK) { return st; }
    memset(&fr, 0, sizeof(fr));
    fr.raw = cur;
    fr.n_raw = ncur;
    fr.offset = off;
    fr.frame_mark = c.pool_cur;
    st = ti_expand(&c, &fr, w->max_thetas, &rt, &is_leaf, &verdict);
    if (st != SRMECH_OK) { return st; }
    *out_children = is_leaf ? -1 : (int)fr.n_children;
    return SRMECH_OK;
}

/* One BFS peel level: expand each branch task in `in` into ALL its children (into
 * `out`), keeping leaves + budget-blocked branches whole. *expanded = 1 iff any
 * task was expanded; *ok = 0 on a peel error. Returns the new task count. */
static size_t tip_peel_round(const tip_wire_t *w, ti_term_t *root, size_t n_root,
                             void *slice, size_t slice_len,
                             const tip_task_t *in, size_t n, tip_task_t *out,
                             int *expanded, int *ok)
{
    size_t i;
    size_t k = 0;
    assert(w != NULL && in != NULL && out != NULL);
    assert(expanded != NULL && ok != NULL);
    for (i = 0; i < n; i++) {
        int m;
        srmech_status_t st;
        if (in[i].terminal || in[i].len >= TIP_MAX_PEEL_DEPTH) { out[k++] = in[i]; continue; }
        st = tip_peel_count(w, root, n_root, &in[i], slice, slice_len, &m);
        if (st != SRMECH_OK) { *ok = 0; return k; }
        if (m < 0) { out[k] = in[i]; out[k].terminal = 1; k++; continue; }
        if (k + (size_t)m + (n - i - 1u) <= (size_t)TIP_MAX_TASKS) {
            int j;
            for (j = 0; j < m; j++) {
                out[k] = in[i];
                out[k].nodes[in[i].len] = j;
                out[k].len = in[i].len + 1;
                out[k].terminal = 0;
                k++;
            }
            *expanded = 1;
        } else {
            out[k++] = in[i];
        }
    }
    return k;
}

/* BFS-peel the certificate tree into a task frontier (ping-ponging bufA/bufB;
 * the final frontier is left in bufA). Expands until >= `target` tasks, or the
 * depth / MAX_TASKS budget or a non-expanding round stops it. *ok = 0 on a peel
 * error. Returns the task count. */
static size_t tip_enumerate(const tip_wire_t *w, ti_term_t *root, size_t n_root,
                            void *slice, size_t slice_len,
                            size_t target, tip_task_t *bufA, tip_task_t *bufB, int *ok)
{
    size_t n = 1u;
    int round;
    assert(w != NULL && bufA != NULL && bufB != NULL);
    assert(ok != NULL);
    *ok = 1;
    bufA[0].len = 0;
    bufA[0].terminal = 0;
    for (round = 0; round < TIP_MAX_PEEL_DEPTH; round++) {
        size_t nn;
        size_t i;
        int expanded = 0;
        if (n >= target) { break; }
        nn = tip_peel_round(w, root, n_root, slice, slice_len, bufA, n, bufB, &expanded, ok);
        if (!*ok) { return n; }
        for (i = 0; i < nn; i++) { bufA[i] = bufB[i]; }
        n = nn;
        if (!expanded) { break; }
    }
    return n;
}

/* The exact SEQUENTIAL path over the WHOLE ws (parse root + ti_decide from offset
 * 0) -- bit-identical to srmech_thetasum_is_zero_interpolation. The thread-less /
 * n_workers<=1 fallback (preserves the capability). */
static srmech_status_t tip_serial(const tip_wire_t *w, void *ws, size_t ws_len,
                                  int *out_is_zero)
{
    ti_ctx_t c;
    ti_rt_t rt;
    ti_term_t *root;
    srmech_status_t st;
    assert(w != NULL && out_is_zero != NULL);
    assert(ws != NULL || ws_len == 0u);
    memset(&c, 0, sizeof(c));
    memset(&rt, 0, sizeof(rt));
    st = tip_worker_setup(w, ws, ws_len, &c, &rt);   /* one arena */
    if (st != SRMECH_OK) { return st; }
    st = ti_bind_term_arr(&c, &root, w->n_terms, w->max_thetas);
    if (st != SRMECH_OK) { return st; }
    st = ti_parse(&c, root, w->n_terms, w->term_nthetas, w->coeff_num, w->coeff_den,
                  w->exps_flat);
    if (st != SRMECH_OK) { return st; }
    return ti_decide(&c, root, w->n_terms, 0, w->max_thetas, &rt, out_is_zero);
}

/* One worker's partition: process tasks {worker_id, +n_workers, ...} (through the
 * task_order permutation), AND-folding into job->verdict; first False sets the
 * cancel flag + stops; an error stops + is recorded (the fold declines). */
typedef struct tip_job {
    const tip_wire_t *w;
    ti_term_t        *root;      /* SHARED read-only parsed root */
    size_t            n_root;
    const tip_task_t *tasks;
    size_t            n_tasks;
    uint32_t          worker_id;
    uint32_t          n_workers;
    uint32_t          task_order;
    void             *slice;
    size_t            slice_len;
    volatile int     *cancel;
    int               verdict;
    srmech_status_t   status;
} tip_job_t;

static void tip_worker_run(tip_job_t *job)
{
    size_t t;
    assert(job != NULL);
    assert(job->tasks != NULL || job->n_tasks == 0u);
    job->verdict = 1;
    job->status = SRMECH_OK;
    for (t = job->worker_id; t < job->n_tasks; t += job->n_workers) {
        size_t idx = (job->task_order != 0u) ? (job->n_tasks - 1u - t) : t;
        int v;
        srmech_status_t st;
        if (*job->cancel) { break; }
        st = tip_run_subproblem(job->w, job->root, job->n_root, &job->tasks[idx],
                                job->slice, job->slice_len, &v);
        if (st != SRMECH_OK) { job->status = st; break; }
        if (v == 0) { job->verdict = 0; *job->cancel = 1; break; }
    }
}

/* PAL thread entry -- a plain void(void*) job. */
static void tip_worker_trampoline(void *arg)
{
    tip_job_t *job;
    assert(arg != NULL);
    job = (tip_job_t *)arg;
    assert(job->w != NULL);
    tip_worker_run(job);
}

/* Fold the finished worker jobs into the verdict: a definitive False (some worker
 * proved a leaf unproven) WINS over any error; else the first error declines;
 * else all-True. Reads jobs only AFTER join (the happens-before barrier). */
static srmech_status_t tip_fold(const tip_job_t *jobs, uint32_t nw, int *out_is_zero)
{
    uint32_t s;
    srmech_status_t rc = SRMECH_OK;
    assert(jobs != NULL && out_is_zero != NULL);
    assert(nw >= 1u);
    *out_is_zero = 1;
    for (s = 0; s < nw; s++) {
        if (jobs[s].verdict == 0) { *out_is_zero = 0; return SRMECH_OK; }
    }
    for (s = 0; s < nw; s++) {
        if (jobs[s].status != SRMECH_OK) { rc = jobs[s].status; }
    }
    return rc;
}

/* Spawn nw workers over disjoint slices (spawn-failure runs that worker inline),
 * join, fold. Job + handle arrays are fixed [TIP_MAX_WORKERS] stack arrays (JPL
 * Rule 3: no malloc). `slice_len` is 8-aligned so every slice base is aligned. */
static srmech_status_t tip_threaded(const tip_wire_t *w, ti_term_t *root, size_t n_root,
                                    const tip_task_t *tasks,
                                    size_t n_tasks, uint32_t nw, uint32_t task_order,
                                    unsigned char *region, size_t region_len,
                                    int *out_is_zero)
{
    tip_job_t            jobs[TIP_MAX_WORKERS];
    srmech_plat_thread_t threads[TIP_MAX_WORKERS];
    uint8_t              live[TIP_MAX_WORKERS] = { 0 };
    volatile int         cancel = 0;
    size_t               slice_len = (region_len / nw) & ~(size_t)7u;
    uint32_t             s;
    assert(w != NULL && tasks != NULL && out_is_zero != NULL);
    assert(nw >= 1u && nw <= (uint32_t)TIP_MAX_WORKERS);
    for (s = 0; s < nw; s++) {
        jobs[s].w = w;               jobs[s].tasks = tasks;   jobs[s].n_tasks = n_tasks;
        jobs[s].root = root;         jobs[s].n_root = n_root;
        jobs[s].worker_id = s;       jobs[s].n_workers = nw;  jobs[s].task_order = task_order;
        jobs[s].slice = region + (size_t)s * slice_len;       jobs[s].slice_len = slice_len;
        jobs[s].cancel = &cancel;    jobs[s].verdict = 1;     jobs[s].status = SRMECH_ERR_INTERNAL;
        if (srmech_plat_thread_spawn(tip_worker_trampoline, &jobs[s], &threads[s]) == SRMECH_OK) {
            live[s] = 1u;
        } else {
            tip_worker_run(&jobs[s]);
        }
    }
    for (s = 0; s < nw; s++) {
        if (live[s]) { (void)srmech_plat_thread_join(&threads[s]); }
    }
    return tip_fold(jobs, nw, out_is_zero);
}

/* The BYTES tip_parse_root needs to parse the root terms ONCE into the read-only
 * SHARED region: a function of the WIRE shape only. Computed by the SAME formula
 * in the parallel ws sizer AND in tip_dispatch, so the carve agrees. PROVABLY
 * smaller than a worker slice (the parse is a strict subset of the serial arena). */
static size_t tip_root_parse_bytes(size_t n_syms, size_t n_terms, size_t max_thetas,
                                   size_t coeff_limbs)
{
    size_t cap = (coeff_limbs < 4u) ? 4u : coeff_limbs;
    size_t ns = (n_syms == 0u) ? 1u : n_syms;
    size_t nt = (n_terms == 0u) ? 1u : n_terms;
    size_t mono_words = 2u * cap + ns + 8u;
    size_t term_struct = (sizeof(ti_term_t) + sizeof(uint32_t) - 1u) / sizeof(uint32_t);
    /* per term: the ti_term_t slot + pref mono + (max_thetas) targ monos + their
     * struct array + generous per-term slack. */
    size_t per_term = term_struct + (max_thetas + 4u) * (mono_words + 16u) + 64u;
    size_t scratch_words = cap * 16u + 512u;
    size_t words = nt * per_term + scratch_words + 256u;
    assert(cap >= 4u);
    assert(words >= scratch_words);
    return words * sizeof(uint32_t);
}

/* Minimum `ws_len` BYTES the parallel entry needs: a fixed control band (the task
 * frontier) + ONE parse-sized shared-root region + nw disjoint worker arena slices,
 * each EXACTLY the ws_bound2 path sizing (a worker's peak arena is the same
 * full-path high-water the serial DFS reaches). A genuine shortfall still trips
 * SRMECH_ERR_OVERFLOW -> the pure oracle. Signature unchanged -> ABI stays. */
size_t srmech_thetasum_is_zero_interpolation_parallel_ws_bound(
    size_t n_syms, size_t n_terms, size_t max_thetas, size_t coeff_limbs,
    size_t max_abs_exp, size_t max_theta_sq_sum, size_t n_workers)
{
    size_t nw = (n_workers < 1u) ? 1u
              : (n_workers > (size_t)TIP_MAX_WORKERS ? (size_t)TIP_MAX_WORKERS : n_workers);
    size_t slice = srmech_thetasum_is_zero_interpolation_ws_bound2(
        n_syms, n_terms, max_thetas, coeff_limbs, max_abs_exp, max_theta_sq_sum);
    size_t per = ((slice + 4096u) + 7u) & ~(size_t)7u;
    size_t root = (tip_root_parse_bytes(n_syms, n_terms, max_thetas, coeff_limbs)
                   + 7u) & ~(size_t)7u;
    assert(nw >= 1u);
    assert(per >= slice);
    assert(root <= per);   /* parse is a strict subset of the serial arena < ws_bound2 */
    return tip_control_bytes() + root + nw * per;   /* +root = the shared-root region */
}

/* The threaded orchestration: carve `ws` into [control | shared-root | worker
 * region], parse the root ONCE into the shared region, BFS-peel the task frontier
 * (into the control-band double-buffer), then run the worker pool. Any layout /
 * parse / peel shortfall falls to the exact serial path (never a wrong verdict). */
static srmech_status_t tip_dispatch(const tip_wire_t *w, uint32_t nw, uint32_t task_order,
                                    void *ws, size_t ws_len, int *out_is_zero)
{
    ti_ctx_t root_ctx;
    ti_term_t *root_terms;
    unsigned char *base = (unsigned char *)ws;
    tip_task_t *bufA = (tip_task_t *)ws;
    size_t control = tip_control_bytes();
    size_t region_len;
    size_t root_bytes;
    size_t worker_region;
    size_t unit;
    size_t target;
    size_t n_tasks;
    int ok;
    srmech_status_t st;
    assert(w != NULL && out_is_zero != NULL);
    assert(nw >= 2u && nw <= (uint32_t)TIP_MAX_WORKERS);
    if (ws_len <= control) { return tip_serial(w, ws, ws_len, out_is_zero); }
    region_len = ws_len - control;
    root_bytes = (tip_root_parse_bytes(w->n_syms, w->n_terms, w->max_thetas, w->coeff_cap)
                  + 7u) & ~(size_t)7u;
    if (root_bytes >= region_len) { return tip_serial(w, ws, ws_len, out_is_zero); }
    worker_region = region_len - root_bytes;
    unit = (worker_region / nw) & ~(size_t)7u;               /* per-worker path slice */
    if (unit == 0u) { return tip_serial(w, ws, ws_len, out_is_zero); }
    memset(&root_ctx, 0, sizeof(root_ctx));
    st = tip_parse_root(w, base + control, root_bytes, &root_ctx, &root_terms);
    if (st != SRMECH_OK) { return tip_serial(w, ws, ws_len, out_is_zero); }
    target = (size_t)nw * (size_t)TIP_TARGET_MULT;
    if (target > (size_t)TIP_MAX_TASKS) { target = (size_t)TIP_MAX_TASKS; }
    n_tasks = tip_enumerate(w, root_terms, w->n_terms, base + control + root_bytes,
                            worker_region, target, bufA, bufA + TIP_MAX_TASKS, &ok);
    if (!ok || n_tasks == 0u) { return tip_serial(w, ws, ws_len, out_is_zero); }
    return tip_threaded(w, root_terms, w->n_terms, bufA, n_tasks, nw, task_order,
                        base + control + root_bytes, worker_region, out_is_zero);
}

/* Decide the cleared ThetaSum numerator's certificate-proven is_zero by the
 * CHIRALITY-PRESERVING PARALLEL fan-out. Wire form + verdict are IDENTICAL to
 * srmech_thetasum_is_zero_interpolation (byte-for-byte the same exact-Q verdict).
 * `n_workers` = the parallel width (clamped to [1, TIP_MAX_WORKERS]);
 * `task_order` (0 forward / 1 reverse) exercises the order-invariance
 * (CHIRALITY) contract. No threads OR n_workers <= 1 -> the exact serial path. */
srmech_status_t srmech_thetasum_is_zero_interpolation_parallel(
    size_t n_syms, int xsym, int ysym, int psym, size_t n_terms,
    const size_t *term_nthetas, const srmech_bigint_t *coeff_num,
    const srmech_bigint_t *coeff_den, const int32_t *exps_flat,
    uint32_t coeff_cap, uint32_t n_workers, uint32_t task_order,
    int *out_is_zero, void *ws, size_t ws_len)
{
    tip_wire_t w;
    uint32_t nw;
    assert(out_is_zero != NULL);
    assert(term_nthetas != NULL || n_terms == 0u);
    if (out_is_zero == NULL) { return SRMECH_ERR_NULL_ARG; }
    *out_is_zero = 1;
    if (n_terms == 0u) { return SRMECH_OK; }
    if (term_nthetas == NULL || coeff_num == NULL || coeff_den == NULL
            || exps_flat == NULL || ws == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    w.n_syms = n_syms;   w.xsym = xsym;   w.ysym = ysym;   w.psym = psym;
    w.n_terms = n_terms; w.term_nthetas = term_nthetas;
    w.coeff_num = coeff_num; w.coeff_den = coeff_den; w.exps_flat = exps_flat;
    w.coeff_cap = coeff_cap; w.max_thetas = ti_max_thetas(term_nthetas, n_terms);
    nw = (n_workers < 1u) ? 1u
       : (n_workers > (uint32_t)TIP_MAX_WORKERS ? (uint32_t)TIP_MAX_WORKERS : n_workers);
    if (!srmech_plat_has_threads() || nw == 1u) {
        return tip_serial(&w, ws, ws_len, out_is_zero);
    }
    return tip_dispatch(&w, nw, task_order, ws, ws_len, out_is_zero);
}
