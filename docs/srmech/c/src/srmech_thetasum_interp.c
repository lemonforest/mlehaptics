/*
 * srmech_thetasum_interp.c -- the C peer of the ThetaSum STRUCTURAL
 * ELLIPTIC-INTERPOLATION is_zero completion (the pure-Python
 * srmech.amsc.thetasum._structural_is_zero shipped rc98). A 1:1 STRUCTURAL
 * MIRROR: the C verdict EQUALS the pure-Python _is_zero_interpolation verdict
 * (True AND False) -- the COMPLETE multi-variable elliptic decision, NOT the
 * bounded +/- -pair fast path of srmech_thetasum.c.
 *
 * The algorithm (Rosengren arXiv:1608.06161v3 Prop 1.6.1 / eq 1.22 + Cor
 * 1.3.5): the cleared numerator N is a theta section jointly in its symbols;
 * N == 0 IFF -- interpolating in ONE variable v at D_v+1 distinct points (a
 * degree-D theta vanishing at D+1 points is == 0) -- N vanishes at each node,
 * a LOWER-variable is_zero => RECURSE, base = the single-variable degree-bound
 * q-expansion. Nodes = the theta-FACTOR ZEROS (monomials in the remaining vars,
 * killing terms via theta(1)=0) augmented with GLOBALLY-DISTINCT PRIMES threaded
 * through the recursion (so no two variables collide to a spurious theta(1)).
 * Exact-Q, no q-grid, no float.
 *
 * Recursion -> EXPLICIT STACK (JPL Rule 1 forbids recursion): a depth-bounded
 * DFS over the interpolation tree with per-frame ARENA MARKS. Each frame owns
 * its combined terms + substitution nodes below its child-mark; between children
 * the pool bump-pointer resets to that mark, so the live arena is bounded by the
 * PATH (depth <= #variables) times the per-level term working set -- NOT the total
 * tree-node count. A too-small caller arena / coefficient cap => SRMECH_ERR_OVERFLOW
 * and the Python dispatch falls to the COMPLETE pure oracle (the C peer is the
 * accelerator, the pure path the authority -- the everything-mirrors precedent).
 *
 * Malloc-free (JPL Rule 3): every working monomial / term / node / series cell +
 * bigint scratch is carved from the caller arena `ws`. The exact-Q monomial +
 * theta-canon KERNELS are the SHARED srmech_ellbase_* single copy (aliased `ti_*`
 * below). Class-K sign is a bigint sign int, never abs().
 *
 * Additive symbol -> ABI unchanged (stays 3). License: MIT.
 */

#include "srmech.h"
#include "srmech_ellbase_internal.h"

#include <assert.h>
#include <stdint.h>
#include <string.h>

/* ---- shared-kernel aliases (the single copy lives in srmech_ellbase.c) ------- */
typedef srmech_ell_q_t    ti_q_t;
typedef srmech_ell_mono_t ti_mono_t;
typedef srmech_ell_ctx_t  ti_ctx_t;

#define ti_take_words        srmech_ellbase_take_words
#define ti_align8            srmech_ellbase_align8
#define ti_take_exps         srmech_ellbase_take_exps
#define ti_bind_bi           srmech_ellbase_bind_bi
#define ti_bind_q            srmech_ellbase_bind_q
#define ti_bind_mono         srmech_ellbase_bind_mono
#define ti_bind_mono_arr     srmech_ellbase_bind_mono_arr
#define ti_q_mul             srmech_ellbase_q_mul
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

/* The single-variable q-expansion degree margin (mirrors thetasum._STRUCT_MARGIN). */
#define TI_STRUCT_MARGIN 3

/* The globally-distinct augment primes (mirrors thetasum._STRUCT_PRIMES EXACTLY,
 * same values AND same order AND same count -- the (offset+used) % NPR index MUST
 * reproduce Python's threading). The distinct-prime augment is load-bearing for
 * SOUNDNESS: substituting two variables to the SAME constant would make a cross-
 * variable factor theta(x_i/x_j) -> theta(1)=0 a SPURIOUS zero. */
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
    ti_q_t          qa;       /* binomial coeff c1 = -ca               */
    ti_q_t          qb;       /* binomial coeff c2 = -1/ca             */
    ti_q_t          qmul;     /* per-cell product scratch              */
    ti_q_t          qtmp;     /* per-cell add scratch                  */
    srmech_bigint_t g;
    srmech_bigint_t t0;
    srmech_bigint_t t1;
    int             psym;
    int            *present;  /* n_syms variable-membership flags      */
} ti_scr_t;

/* A DFS frame: a node of the interpolation tree. */
typedef struct ti_frame {
    ti_term_t *raw;          /* un-combined input terms                 */
    size_t     n_raw;
    ti_term_t *terms;        /* combined terms                          */
    size_t     n_terms;
    ti_mono_t *nodes;        /* the d+1 substitution nodes              */
    size_t     n_nodes;
    int32_t    offset;       /* augment-prime offset for THIS frame     */
    int32_t    child_offset;
    int        v;            /* interpolation variable index            */
    size_t     next_child;
    size_t     frame_mark;   /* pool_cur before this frame's allocs     */
    size_t     child_mark;   /* pool_cur before the first child         */
    int        state;        /* 0 = NEW, 1 = BRANCHING                  */
} ti_frame_t;

/* A dense p,w-series cell grid: cells[pp*wb + (we - wmin)], pp in 0..K1-1. */
typedef struct ti_ps {
    ti_q_t *cells;
    int     K1;
    int     wb;
    int     wmin;
} ti_ps_t;

/* ---- forward declarations (Rule 1: iterative; no recursion) ----------------- */
static srmech_status_t ti_compact_terms(ti_ctx_t *c, ti_term_t *arr, size_t n,
                                        size_t *n_out);
static srmech_status_t ti_push_child(ti_ctx_t *c, ti_frame_t *frames, long depth,
                                     size_t max_thetas, ti_scr_t *s);

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
    if (st == SRMECH_OK) { st = ti_bind_q(c, &s->qb); }
    if (st == SRMECH_OK) { st = ti_bind_q(c, &s->qmul); }
    if (st == SRMECH_OK) { st = ti_bind_q(c, &s->qtmp); }
    if (st == SRMECH_OK) { st = ti_bind_bi(c, &s->g); }
    if (st == SRMECH_OK) { st = ti_bind_bi(c, &s->t0); }
    if (st == SRMECH_OK) { st = ti_bind_bi(c, &s->t1); }
    if (st != SRMECH_OK) { return st; }
    raw = ti_take_words(c, c->n_syms);
    if (raw == NULL) { return SRMECH_ERR_OVERFLOW; }
    s->present = (int *)raw;
    return SRMECH_OK;
}

/* ---- combine (mirrors thetasum._struct_combine) ----------------------------- */

/* Canonicalize ONE raw term into `dst` (fold each theta-canon prefactor into the
 * term prefactor; a theta that canonicalizes to theta(1) KILLS the term). Sets
 * *dead = 1 when the term drops (theta(1) factor OR the folded prefactor is zero).
 * The surviving canonical thetas are written (unsorted) into dst->targs. */
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

/* ---- variables / degree / pivot / nodes ------------------------------------- */

/* Mark s->present[idx]=1 for every symbol (except psym) with a nonzero exponent in
 * any theta argument. Returns the count of distinct such variables (_struct_variables). */
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

/* deg(v) = max over terms of SUM over theta args of (arg.exps[v])^2 (the elliptic
 * degree in v). Integer; mirrors _structural_is_zero's _deg. */
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
 * a with the v-factor stripped. Writes `node`. Mirrors _struct_zero_nodes' inner. */
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

/* Build the d+1 interpolation nodes into `nodes`: the distinct zero-MONOMIAL nodes
 * (first-seen, capped at d+1) then GLOBALLY-DISTINCT augment primes threaded via
 * `offset`. *used = the number of primes consumed at this level (for child_offset).
 * Mirrors _structural_is_zero's node loop. */
static srmech_status_t ti_build_nodes(ti_ctx_t *c, ti_mono_t *nodes, size_t need,
                                      const ti_term_t *terms, size_t n, int v,
                                      int32_t offset, ti_scr_t *s, int32_t *used)
{
    size_t filled = 0;
    size_t ti;
    srmech_status_t st;
    assert(c != NULL && nodes != NULL && s != NULL && used != NULL);
    assert(terms != NULL || n == 0u);
    for (ti = 0; ti < n && filled < need; ti++) {
        size_t a;
        for (a = 0; a < terms[ti].n_thetas && filled < need; a++) {
            size_t j;
            int seen = 0;
            int32_t e = terms[ti].targs[a].exps[v];
            if (e != 1 && e != -1) { continue; }
            st = ti_zero_node(c, &s->m[6], &terms[ti].targs[a], v, e, s);
            if (st != SRMECH_OK) { return st; }
            for (j = 0; j < filled; j++) {
                if (ti_mono_eq(c, &nodes[j], &s->m[6])) { seen = 1; break; }
            }
            if (seen) { continue; }
            st = ti_mono_copy(c, &nodes[filled], &s->m[6]);
            if (st != SRMECH_OK) { return st; }
            filled++;
        }
    }
    *used = 0;
    while (filled < need) {
        int32_t idx = (offset + *used) % TI_NPRIMES;
        st = ti_set_prime(c, &nodes[filled], TI_STRUCT_PRIMES[idx]);
        if (st != SRMECH_OK) { return st; }
        filled++;
        (*used)++;
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

/* ---- the single-variable base case (mirrors thetasum._struct_one_var) ------- */

/* Compute the base-case sizing: K1 = k+1 (k = max(deg-1,0)+MARGIN) and the
 * conservative w-band [wmin, wmin+wb) covering every term's q-expansion in w. */
static void ti_one_var_bounds(const ti_ctx_t *c, const ti_term_t *terms, size_t n,
                              int w, int *out_K1, int *out_wmin, int *out_wb)
{
    size_t ti;
    int deg;
    int k;
    int lo = 0;
    int hi = 0;
    int init = 0;
    assert(c != NULL && (terms != NULL || n == 0u));
    assert(out_K1 != NULL && out_wmin != NULL && out_wb != NULL);
    deg = ti_deg(c, terms, n, w);           /* max over terms of SUM sq(exp_w) */
    k = ((deg - 1) > 0 ? (deg - 1) : 0) + TI_STRUCT_MARGIN;
    for (ti = 0; ti < n; ti++) {
        size_t a;
        int span = 0;
        int pw = (int)terms[ti].pref.exps[w];
        for (a = 0; a < terms[ti].n_thetas; a++) {
            span += (k + 1) * (int)ti_iabs(terms[ti].targs[a].exps[w]);
        }
        if (!init || pw - span < lo) { lo = pw - span; }
        if (!init || pw + span > hi) { hi = pw + span; }
        init = 1;
    }
    *out_K1 = k + 1;
    *out_wmin = lo;
    *out_wb = (hi - lo) + 1;
}

static srmech_status_t ti_bind_ps(ti_ctx_t *c, ti_ps_t *ps, int K1, int wb, int wmin)
{
    size_t cnt = (size_t)K1 * (size_t)wb;
    size_t i;
    size_t words;
    uint32_t *raw;
    srmech_status_t st;
    assert(c != NULL && ps != NULL);
    assert(K1 >= 1 && wb >= 1);
    ti_align8(c);
    words = (cnt * sizeof(ti_q_t) + sizeof(uint32_t) - 1u) / sizeof(uint32_t);
    raw = ti_take_words(c, words);
    if (raw == NULL) { return SRMECH_ERR_OVERFLOW; }
    ps->cells = (ti_q_t *)raw;
    ps->K1 = K1;
    ps->wb = wb;
    ps->wmin = wmin;
    for (i = 0; i < cnt; i++) {
        st = ti_bind_q(c, &ps->cells[i]);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* Zero every cell (Q = 0/1). */
static srmech_status_t ti_ps_zero(const ti_ps_t *ps)
{
    size_t cnt = (size_t)ps->K1 * (size_t)ps->wb;
    size_t i;
    srmech_status_t st;
    assert(ps != NULL && ps->cells != NULL);
    assert(ps->K1 >= 1);
    for (i = 0; i < cnt; i++) {
        st = srmech_bigint_set_i64(&ps->cells[i].num, 0);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_set_i64(&ps->cells[i].den, 1);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* out := in * (1 + coeff * p^jp * w^dwe), truncating p past K1-1 (out fully
 * written; out != in). Mirrors one binomial factor of _struct_theta_p. */
static srmech_status_t ti_ps_binom(ti_ctx_t *c, const ti_ps_t *in, ti_ps_t *out,
                                   int jp, int dwe, const ti_q_t *coeff, ti_scr_t *s)
{
    int pp;
    int w;
    srmech_status_t st;
    assert(c != NULL && in != NULL && out != NULL && coeff != NULL && s != NULL);
    assert(jp >= 0);
    for (pp = 0; pp < in->K1; pp++) {
        for (w = 0; w < in->wb; w++) {
            ti_q_t *dst = &out->cells[pp * in->wb + w];
            int sp = pp - jp;
            int sw = w - dwe;
            st = ti_q_copy(dst, &in->cells[pp * in->wb + w]);
            if (st != SRMECH_OK) { return st; }
            if (sp < 0 || sw < 0 || sw >= in->wb) { continue; }
            st = ti_q_mul(c, &s->qmul, coeff, &in->cells[sp * in->wb + sw],
                          &s->g, &s->t0, &s->t1);
            if (st != SRMECH_OK) { return st; }
            st = ti_q_add(c, &s->qtmp, dst, &s->qmul, &s->g, &s->t0, &s->t1);
            if (st != SRMECH_OK) { return st; }
            st = ti_q_copy(dst, &s->qtmp);
            if (st != SRMECH_OK) { return st; }
        }
    }
    return SRMECH_OK;
}

/* total += term (cellwise). Both share the K1 x wb band. */
static srmech_status_t ti_ps_add(ti_ctx_t *c, ti_ps_t *total, const ti_ps_t *term,
                                 ti_scr_t *s)
{
    size_t cnt = (size_t)total->K1 * (size_t)total->wb;
    size_t i;
    srmech_status_t st;
    assert(c != NULL && total != NULL && term != NULL && s != NULL);
    assert(total->K1 == term->K1 && total->wb == term->wb);
    for (i = 0; i < cnt; i++) {
        st = ti_q_add(c, &s->qtmp, &total->cells[i], &term->cells[i],
                      &s->g, &s->t0, &s->t1);
        if (st != SRMECH_OK) { return st; }
        st = ti_q_copy(&total->cells[i], &s->qtmp);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* Multiply the running series in *cur by theta(ca * w^e; p) via its binomial
 * factors ((1 - ca w^e p^j) for j=0..k, (1 - (1/ca) w^{-e} p^{j+1}) for j+1<=k),
 * ping-ponging between *cur and *oth. Mirrors _struct_theta_p folded into the term. */
static srmech_status_t ti_series_theta(ti_ctx_t *c, ti_ps_t **cur, ti_ps_t **oth,
                                       const ti_q_t *ca, int e, ti_scr_t *s)
{
    int k = (*cur)->K1 - 1;
    int j;
    srmech_status_t st;
    ti_ps_t *tmp;
    assert(c != NULL && cur != NULL && oth != NULL && ca != NULL && s != NULL);
    assert((*cur)->K1 >= 1);
    st = ti_q_copy(&s->qa, ca);                          /* qa = ca */
    if (st != SRMECH_OK) { return st; }
    s->qa.num.sign = (s->qa.num.sign == 0) ? 0 : -s->qa.num.sign;   /* qa = -ca */
    st = srmech_bigint_copy(&s->qb.num, &ca->den);
    if (st == SRMECH_OK) { st = srmech_bigint_copy(&s->qb.den, &ca->num); }
    if (st != SRMECH_OK) { return st; }
    s->qb.num.sign = (s->qb.num.sign == 0) ? 0 : -s->qb.num.sign;   /* qb = -1/ca */
    if (s->qb.den.sign < 0) { s->qb.den.sign = -s->qb.den.sign; s->qb.num.sign = -s->qb.num.sign; }
    for (j = 0; j <= k; j++) {
        st = ti_ps_binom(c, *cur, *oth, j, e, &s->qa, s);
        if (st != SRMECH_OK) { return st; }
        tmp = *cur; *cur = *oth; *oth = tmp;
        if (j + 1 <= k) {
            st = ti_ps_binom(c, *cur, *oth, j + 1, -e, &s->qb, s);
            if (st != SRMECH_OK) { return st; }
            tmp = *cur; *cur = *oth; *oth = tmp;
        }
    }
    return SRMECH_OK;
}

/* Build ONE term's p,w-series into *cur (starting from its prefactor cell) and add
 * it into `total`. bufA/bufB are the two ping-pong buffers. */
static srmech_status_t ti_term_series(ti_ctx_t *c, const ti_term_t *t, int w,
                                      ti_ps_t *total, ti_ps_t *bufA, ti_ps_t *bufB,
                                      ti_scr_t *s)
{
    ti_ps_t *cur = bufA;
    ti_ps_t *oth = bufB;
    size_t a;
    int pw = (int)t->pref.exps[w];
    srmech_status_t st;
    assert(c != NULL && t != NULL && total != NULL && s != NULL);
    assert(bufA != NULL && bufB != NULL);
    st = ti_ps_zero(cur);
    if (st != SRMECH_OK) { return st; }
    st = ti_q_copy(&cur->cells[0 * cur->wb + (pw - cur->wmin)], &t->pref.coeff);
    if (st != SRMECH_OK) { return st; }
    for (a = 0; a < t->n_thetas; a++) {
        st = ti_series_theta(c, &cur, &oth, &t->targs[a].coeff,
                             (int)t->targs[a].exps[w], s);
        if (st != SRMECH_OK) { return st; }
    }
    return ti_ps_add(c, total, cur, s);
}

/* The single-variable degree-bound base case: the whole numerator's summed p,w-
 * series in w is identically zero IFF every coefficient cancels. Sets *is_zero.
 * Mirrors _struct_one_var. */
static srmech_status_t ti_one_var(ti_ctx_t *c, const ti_term_t *terms, size_t n, int w,
                                  ti_scr_t *s, int *is_zero)
{
    int K1;
    int wmin;
    int wb;
    size_t ti;
    size_t i;
    size_t cnt;
    ti_ps_t total;
    ti_ps_t bufA;
    ti_ps_t bufB;
    srmech_status_t st;
    assert(c != NULL && (terms != NULL || n == 0u) && s != NULL);
    assert(is_zero != NULL);
    ti_one_var_bounds(c, terms, n, w, &K1, &wmin, &wb);
    st = ti_bind_ps(c, &total, K1, wb, wmin);
    if (st == SRMECH_OK) { st = ti_bind_ps(c, &bufA, K1, wb, wmin); }
    if (st == SRMECH_OK) { st = ti_bind_ps(c, &bufB, K1, wb, wmin); }
    if (st != SRMECH_OK) { return st; }
    st = ti_ps_zero(&total);
    if (st != SRMECH_OK) { return st; }
    for (ti = 0; ti < n; ti++) {
        st = ti_term_series(c, &terms[ti], w, &total, &bufA, &bufB, s);
        if (st != SRMECH_OK) { return st; }
    }
    *is_zero = 1;
    cnt = (size_t)K1 * (size_t)wb;
    for (i = 0; i < cnt; i++) {
        if (!srmech_bigint_is_zero(&total.cells[i].num)) { *is_zero = 0; break; }
    }
    return SRMECH_OK;
}

/* ---- the explicit-stack DFS driver ------------------------------------------ */

/* Expand a NEW frame: combine its raw terms, then either DECIDE a leaf (empty ->
 * zero; no variables -> nonzero residue; one variable -> the base case) or SET UP
 * branching (pick v, build the d+1 nodes, mark child bookkeeping). Sets *is_leaf +
 * (if leaf) *verdict. Mirrors the head of _structural_is_zero. */
static srmech_status_t ti_expand(ti_ctx_t *c, ti_frame_t *fr, size_t max_thetas,
                                 ti_scr_t *s, int *is_leaf, int *verdict)
{
    size_t nvars;
    int v;
    int d;
    int32_t used;
    size_t j;
    int the_var = -1;
    srmech_status_t st;
    assert(c != NULL && fr != NULL && s != NULL);
    assert(is_leaf != NULL && verdict != NULL);
    *is_leaf = 1;
    *verdict = 1;
    st = ti_combine(c, &fr->terms, &fr->n_terms, fr->raw, fr->n_raw, max_thetas, s);
    if (st != SRMECH_OK) { return st; }
    if (fr->n_terms == 0u) { return SRMECH_OK; }             /* empty -> zero */
    nvars = ti_collect_vars(c, fr->terms, fr->n_terms, s);
    if (nvars == 0u) { *verdict = 0; return SRMECH_OK; }     /* residue -> nonzero */
    if (nvars == 1u) {
        for (j = 0; j < c->n_syms; j++) { if (s->present[j]) { the_var = (int)j; break; } }
        return ti_one_var(c, fr->terms, fr->n_terms, the_var, s, verdict);
    }
    ti_pick_v(c, fr->terms, fr->n_terms, s, &v, &d);
    if ((size_t)(d + 1) > c->n_syms + (size_t)d) { return SRMECH_ERR_INTERNAL; }
    st = ti_bind_mono_arr(c, &fr->nodes, (size_t)d + 1u);
    if (st != SRMECH_OK) { return st; }
    st = ti_build_nodes(c, fr->nodes, (size_t)d + 1u, fr->terms, fr->n_terms, v,
                        fr->offset, s, &used);
    if (st != SRMECH_OK) { return st; }
    fr->v = v;
    fr->n_nodes = (size_t)d + 1u;
    fr->child_offset = fr->offset + used;
    fr->next_child = 0;
    fr->child_mark = c->pool_cur;
    fr->state = 1;
    *is_leaf = 0;
    return SRMECH_OK;
}

/* The DFS: N == 0 IFF every leaf of the interpolation tree is zero. Iterative,
 * arena-mark reclaimed (Rule 1: no recursion). Sets *out_is_zero. */
static srmech_status_t ti_decide(ti_ctx_t *c, ti_term_t *root, size_t n_root, int xsym,
                                 int ysym, ti_frame_t *frames, size_t fcap,
                                 size_t max_thetas, ti_scr_t *s, int *out_is_zero)
{
    long depth = 0;
    int is_leaf;
    int verdict;
    srmech_status_t st;
    assert(c != NULL && frames != NULL && s != NULL && out_is_zero != NULL);
    assert(root != NULL || n_root == 0u);
    (void)xsym; (void)ysym;
    *out_is_zero = 1;
    frames[0].raw = root;
    frames[0].n_raw = n_root;
    frames[0].offset = 0;
    frames[0].frame_mark = c->pool_cur;
    frames[0].state = 0;
    while (depth >= 0) {
        ti_frame_t *fr = &frames[depth];
        if (fr->state == 0) {
            st = ti_expand(c, fr, max_thetas, s, &is_leaf, &verdict);
            if (st != SRMECH_OK) { return st; }
            if (is_leaf) {
                if (!verdict) { *out_is_zero = 0; return SRMECH_OK; }
                c->pool_cur = fr->frame_mark;
                depth--;
                continue;
            }
        }
        if (fr->next_child >= fr->n_nodes) {
            c->pool_cur = fr->frame_mark;
            depth--;
            continue;
        }
        c->pool_cur = fr->child_mark;
        if ((size_t)(depth + 1) >= fcap) { return SRMECH_ERR_OVERFLOW; }
        st = ti_push_child(c, frames, depth, max_thetas, s);
        if (st != SRMECH_OK) { return st; }
        depth++;
    }
    return SRMECH_OK;
}

/* Build the next child of frames[depth] (substitute v -> the next node) and
 * initialise its frame slot. Advances the parent's next_child. */
static srmech_status_t ti_push_child(ti_ctx_t *c, ti_frame_t *frames, long depth,
                                     size_t max_thetas, ti_scr_t *s)
{
    ti_frame_t *fr = &frames[depth];
    ti_frame_t *ch = &frames[depth + 1];
    ti_mono_t *node = &fr->nodes[fr->next_child];
    srmech_status_t st;
    assert(c != NULL && frames != NULL && s != NULL);
    assert(depth >= 0);
    fr->next_child++;
    ch->frame_mark = c->pool_cur;
    st = ti_subst_terms(c, &ch->raw, fr->terms, fr->n_terms, fr->v, node,
                        max_thetas, s);
    if (st != SRMECH_OK) { return st; }
    ch->n_raw = fr->n_terms;
    ch->offset = fr->child_offset;
    ch->state = 0;
    return SRMECH_OK;
}

/* ---- wire parse + public entry + ws sizing ---------------------------------- */

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

/* Bind the DFS frame array (one slot per possible depth = #symbols + 2). */
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

/* Decide whether the cleared ThetaSum numerator is identically zero by the exact
 * structural elliptic interpolation -- the COMPLETE multi-variable mirror of the
 * pure-Python ThetaSum._is_zero_interpolation. Wire form + args identical to
 * srmech_thetasum_is_zero. *out_is_zero = 1 iff == 0. Caller arena `ws`. */
srmech_status_t srmech_thetasum_is_zero_interpolation(
    size_t n_syms, int xsym, int ysym, int psym, size_t n_terms,
    const size_t *term_nthetas, const srmech_bigint_t *coeff_num,
    const srmech_bigint_t *coeff_den, const int32_t *exps_flat,
    uint32_t coeff_cap, int *out_is_zero, void *ws, size_t ws_len)
{
    ti_ctx_t c = {0};
    ti_term_t *terms = NULL;
    ti_frame_t *frames = NULL;
    ti_scr_t scr = {0};
    size_t max_thetas;
    size_t fcap;
    srmech_status_t st;
    assert(out_is_zero != NULL);
    assert(term_nthetas != NULL || n_terms == 0u);
    if (out_is_zero == NULL) { return SRMECH_ERR_NULL_ARG; }
    *out_is_zero = 1;
    if (n_terms == 0u) { return SRMECH_OK; }
    if (term_nthetas == NULL || coeff_num == NULL || coeff_den == NULL || exps_flat == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    c.n_syms = (n_syms == 0u) ? 1u : n_syms;
    c.cap = (coeff_cap < 4u) ? 4u : coeff_cap;
    max_thetas = ti_max_thetas(term_nthetas, n_terms);
    fcap = c.n_syms + 2u;
    st = ti_arena_init(&c, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    st = ti_bind_scr(&c, &scr);
    if (st == SRMECH_OK) { st = ti_bind_frames(&c, &frames, fcap); }
    if (st == SRMECH_OK) { st = ti_bind_term_arr(&c, &terms, n_terms, max_thetas); }
    if (st != SRMECH_OK) { return st; }
    scr.psym = psym;
    st = ti_parse(&c, terms, n_terms, term_nthetas, coeff_num, coeff_den, exps_flat);
    if (st != SRMECH_OK) { return st; }
    return ti_decide(&c, terms, n_terms, xsym, ysym, frames, fcap, max_thetas, &scr,
                     out_is_zero);
}

/* The minimum `ws_len` BYTES srmech_thetasum_is_zero_interpolation needs for the
 * given shape (rc102 degree-aware sizer). `max_theta_sq_sum` is the base case's TRUE
 * p-order band degree — `ti_deg` = the max over terms of SUM of squared THETA-argument
 * exponents in a base variable (exactly what `ti_one_var` consumes: k = max(deg-1,0) +
 * MARGIN). This is NOT `max_abs_exp` squared: a leaf with >=2 same-variable thetas has
 * SUM(e^2) >> max(e^2) (the pre-rc102 max_abs_exp^2 UNDER-sized k -> SRMECH_ERR_OVERFLOW
 * false-decline), and a canonicalized prefactor can carry a large single exponent that
 * made max_abs_exp^2 OVER-size k. `max_abs_exp` (the largest |exponent| across ALL
 * monomials incl. the prefactor) still bounds the w-band SPAN + prefactor offset. A
 * shortfall on a pathological deep/wide input still trips SRMECH_ERR_OVERFLOW and the
 * caller falls to the pure oracle. Additive symbol -> SRMECH_ABI_VERSION stays 3. */
size_t srmech_thetasum_is_zero_interpolation_ws_bound2(size_t n_syms, size_t n_terms,
                                                       size_t max_thetas,
                                                       size_t coeff_limbs,
                                                       size_t max_abs_exp,
                                                       size_t max_theta_sq_sum)
{
    size_t cap = (coeff_limbs < 4u) ? 4u : coeff_limbs;
    size_t ns = (n_syms == 0u) ? 1u : n_syms;
    size_t depth = ns + 2u;
    size_t mono_words = 2u * cap + ns + 8u;
    size_t nt = (n_terms == 0u) ? 1u : n_terms;
    /* per-level term storage: two term arrays (combined + child-raw) + nodes. */
    size_t term_words = mono_words + (max_thetas + 1u) * mono_words + 32u;
    size_t level_words = 2u * nt * term_words + (max_thetas + 2u) * mono_words + 64u;
    /* the base-case series: K1 x wb dense Q grid, three buffers. k mirrors ti_one_var:
     * k = max(deg-1,0) + MARGIN <= max_theta_sq_sum + MARGIN; the +2 keeps it an UPPER
     * bound (never under-provision). */
    size_t k = max_theta_sq_sum + (size_t)TI_STRUCT_MARGIN + 2u;
    size_t wb = 2u * (k + 1u) * (max_thetas + 1u) * (max_abs_exp + 1u) + 4u;
    size_t base_words = 3u * (k + 1u) * wb * (2u * cap + 8u) + 256u;
    size_t scratch_words = cap * 16u + 512u;
    size_t total = depth * level_words + base_words
                   + (TI_SCR_MONOS + 8u) * mono_words + depth * (sizeof(ti_frame_t) / 4u + 4u)
                   + scratch_words + 4096u;
    assert(cap >= 4u);
    assert(total >= scratch_words);
    return total * sizeof(uint32_t);
}

/* Legacy 5-arg entry (pre-rc102). Reproduces the OLD sizing byte-for-byte by passing
 * `max_abs_exp * max_abs_exp` as the base-case degree, so a stale ABI-3 caller / lib
 * still links + behaves exactly as before. New callers use the degree-aware
 * srmech_thetasum_is_zero_interpolation_ws_bound2 above (true ti_deg). Additive symbol
 * set -> SRMECH_ABI_VERSION stays 3. */
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
