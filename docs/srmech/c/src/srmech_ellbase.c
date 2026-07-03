/*
 * srmech_ellbase.c -- the 1:1 native C peer of the ELLIPTIC carrier family
 * srmech.amsc.ellbase (EllMonomial / Theta / EllRatio), the rc59/rc60 carriers
 * the GENUINE elliptic creative-telescoping engine manipulates. A C-MIRROR
 * PARITY build (NOT a new algorithm): the C decision reproduces the pure-Python
 * carrier methods byte-for-byte.
 *
 * Two halves:
 *
 *  (1) The SHARED exact-Q monomial + theta-canon KERNELS (declared in
 *      srmech_ellbase_internal.h), PROMOTED out of srmech_thetasum.c (rc63) so
 *      ThetaSum.is_zero and EllRatio.is_elliptic share ONE copy of each kernel
 *      (the everything-mirrors discipline forbids two copies). srmech_thetasum.c
 *      now includes the internal header and calls these.
 *
 *  (2) The EllRatio decision peer `srmech_ellratio_is_elliptic` (+ the carrier
 *      compute methods qshift / pshift / mul / inv reachable through it): the
 *      COMPLETE balancing / very-well-poised predicate
 *
 *          is_elliptic() == (pshift() == self)
 *
 *      where pshift substitutes x -> p*x in the prefactor + every theta argument,
 *      RE-CANONICALIZES (Theta.canonicalize folds the quasi-periodicity prefactor),
 *      cancels matching thetas between numerator and denominator, sorts the
 *      surviving multisets, and compares the canonical (prefactor, num, den) to the
 *      original's EXACTLY. NOT a bounded/numeric shell -- where Python returns a
 *      clean verdict via the exact theta-canon, the C returns the SAME, byte-for-
 *      byte (sound; no convergence threshold on any decision path).
 *
 * An EllMonomial = an exact-Q coeff (num/den srmech_bigint, Class-K sign) over a
 * dense int32 exponent vector on an interned symbol table. A Theta = a single
 * EllMonomial argument. The Python carries arbitrary string symbols; the bridge
 * interns the distinct names so the C works over integer symbol-indices, and the
 * exponent monomial + sort key are byte-identical to the Python's sorted
 * (symbol, exp) tuple.
 *
 * Coefficients stay tiny in practice but every coefficient is an exact rational
 * over srmech_bigint -- byte-identical at ANY magnitude, OVERFLOW-not-wrap.
 * Class-K sign is an int +/-1, never abs().
 *
 * Malloc-free (JPL Rule 3): every working monomial / theta + the bigint scratch
 * is carved from the caller arena `ws`. If the working set balloons, the caller
 * has mis-encoded the fiber -- the arena is sized to the input (n_num, n_den,
 * n_syms), no compiled-in cap.
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto/recursion): OK -- iterative, flat static helpers
 *   - Rule 2 (bounded loops)    : OK -- bounded by n_syms / n_num / n_den
 *   - Rule 3 (no malloc)        : OK -- caller arena only
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

/* ============================================================================ *
 *  (1) SHARED KERNELS -- promoted from srmech_thetasum.c (rc63), byte-identical
 * ============================================================================ */

/* ---- arena bump primitives -------------------------------------------------- */

uint32_t *srmech_ellbase_take_words(srmech_ell_ctx_t *c, size_t cnt)
{
    uint32_t *p;
    assert(c != NULL);
    assert(c->pool_cur <= c->pool_words);
    if (cnt > c->pool_words || c->pool_cur > c->pool_words - cnt) {
        return NULL;
    }
    p = c->pool + c->pool_cur;
    c->pool_cur += cnt;
    return p;
}

/* 8-byte-align the bump cursor before carving a struct array that embeds pointers,
 * so the cast-from-uint32* storage is correctly aligned on a 64-bit target. The
 * arena base is 8-byte aligned by contract. */
void srmech_ellbase_align8(srmech_ell_ctx_t *c)
{
    assert(c != NULL);
    assert(c->pool_cur <= c->pool_words);
    if ((c->pool_cur & 1u) != 0u && c->pool_cur < c->pool_words) {
        c->pool_cur += 1u;     /* pad one 4-byte word -> 8-byte boundary */
    }
}

int32_t *srmech_ellbase_take_exps(srmech_ell_ctx_t *c)
{
    /* one int32 exponent per symbol (round up to a uint32-word multiple). */
    size_t words;
    uint32_t *raw;
    assert(c != NULL);
    assert(c->n_syms >= 1u);
    words = c->n_syms;                      /* int32 == uint32 word           */
    raw = srmech_ellbase_take_words(c, words);
    if (raw == NULL) {
        return NULL;
    }
    memset(raw, 0, words * sizeof(uint32_t));
    return (int32_t *)raw;
}

srmech_status_t srmech_ellbase_bind_bi(srmech_ell_ctx_t *c, srmech_bigint_t *b)
{
    uint32_t *limbs;
    assert(c != NULL && b != NULL);
    assert(c->cap > 0u);
    limbs = srmech_ellbase_take_words(c, c->cap);
    if (limbs == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    b->limbs = limbs;
    b->cap = c->cap;
    b->n = 0;
    b->sign = 0;
    return SRMECH_OK;
}

srmech_status_t srmech_ellbase_bind_q(srmech_ell_ctx_t *c, srmech_ell_q_t *q)
{
    srmech_status_t st;
    assert(c != NULL && q != NULL);
    assert(c->cap > 0u);
    st = srmech_ellbase_bind_bi(c, &q->num);
    if (st != SRMECH_OK) { return st; }
    return srmech_ellbase_bind_bi(c, &q->den);
}

srmech_status_t srmech_ellbase_bind_mono(srmech_ell_ctx_t *c, srmech_ell_mono_t *m)
{
    srmech_status_t st;
    assert(c != NULL && m != NULL);
    assert(c->n_syms >= 1u);
    st = srmech_ellbase_bind_q(c, &m->coeff);
    if (st != SRMECH_OK) { return st; }
    m->exps = srmech_ellbase_take_exps(c);
    if (m->exps == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    return SRMECH_OK;
}

/* Carve a contiguous bound monomial array of `count` monos (8-byte aligned). */
srmech_status_t srmech_ellbase_bind_mono_arr(srmech_ell_ctx_t *c,
                                             srmech_ell_mono_t **out, size_t count)
{
    size_t i;
    size_t words;
    uint32_t *raw;
    srmech_status_t st;
    assert(c != NULL && out != NULL && count >= 1u);
    assert(c->n_syms >= 1u);
    srmech_ellbase_align8(c);
    words = (count * sizeof(srmech_ell_mono_t) + sizeof(uint32_t) - 1u)
            / sizeof(uint32_t);
    raw = srmech_ellbase_take_words(c, words);
    if (raw == NULL) { return SRMECH_ERR_OVERFLOW; }
    *out = (srmech_ell_mono_t *)raw;
    for (i = 0; i < count; i++) {
        st = srmech_ellbase_bind_mono(c, &(*out)[i]);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* ---- exact-Q (two-bigint) helpers ------------------------------------------- */

/* q := num/den in lowest terms with den > 0 (Class-K sign on num). den nonzero. */
srmech_status_t srmech_ellbase_q_reduce(srmech_ell_ctx_t *c, srmech_ell_q_t *q,
                                        srmech_bigint_t *g, srmech_bigint_t *t0,
                                        srmech_bigint_t *t1)
{
    srmech_status_t st;
    assert(c != NULL && q != NULL && g != NULL);
    assert(q->den.sign != 0);
    if (q->den.sign < 0) {
        q->num.sign = (q->num.sign == 0) ? 0 : -q->num.sign;
        q->den.sign = -q->den.sign;
    }
    if (srmech_bigint_is_zero(&q->num)) {
        return srmech_bigint_set_i64(&q->den, 1);
    }
    st = srmech_bigint_gcd(g, &q->num, &q->den, c->scratch, c->scratch_len);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_divmod(t0, t1, &q->num, g, c->scratch, c->scratch_len);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&q->num, t0);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_divmod(t0, t1, &q->den, g, c->scratch, c->scratch_len);
    if (st != SRMECH_OK) { return st; }
    return srmech_bigint_copy(&q->den, t0);
}

/* out := a * b (exact rational; reduced). out distinct from a, b. */
srmech_status_t srmech_ellbase_q_mul(srmech_ell_ctx_t *c, srmech_ell_q_t *out,
                                     const srmech_ell_q_t *a, const srmech_ell_q_t *b,
                                     srmech_bigint_t *g, srmech_bigint_t *t0,
                                     srmech_bigint_t *t1)
{
    srmech_status_t st;
    assert(c != NULL && out != NULL && a != NULL && b != NULL);
    assert(g != NULL);
    st = srmech_bigint_mul(&out->num, &a->num, &b->num);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_mul(&out->den, &a->den, &b->den);
    if (st != SRMECH_OK) { return st; }
    return srmech_ellbase_q_reduce(c, out, g, t0, t1);
}

/* out := a + b (exact rational; reduced). out distinct from a, b. */
srmech_status_t srmech_ellbase_q_add(srmech_ell_ctx_t *c, srmech_ell_q_t *out,
                                     const srmech_ell_q_t *a, const srmech_ell_q_t *b,
                                     srmech_bigint_t *g, srmech_bigint_t *t0,
                                     srmech_bigint_t *t1)
{
    srmech_status_t st;
    assert(out != NULL && a != NULL && b != NULL);
    assert(g != NULL && t0 != NULL && t1 != NULL);
    /* num = a.num*b.den + b.num*a.den ; den = a.den*b.den */
    st = srmech_bigint_mul(t0, &a->num, &b->den);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_mul(t1, &b->num, &a->den);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_add(&out->num, t0, t1);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_mul(&out->den, &a->den, &b->den);
    if (st != SRMECH_OK) { return st; }
    return srmech_ellbase_q_reduce(c, out, g, t0, t1);
}

srmech_status_t srmech_ellbase_q_copy(srmech_ell_q_t *out, const srmech_ell_q_t *a)
{
    srmech_status_t st;
    assert(out != NULL && a != NULL);
    assert(out->num.limbs != NULL && out->den.limbs != NULL);
    st = srmech_bigint_copy(&out->num, &a->num);
    if (st != SRMECH_OK) { return st; }
    return srmech_bigint_copy(&out->den, &a->den);
}

/* 1 iff a == b as exact rationals (both assumed reduced, den > 0). */
int srmech_ellbase_q_eq(const srmech_ell_q_t *a, const srmech_ell_q_t *b)
{
    assert(a != NULL && b != NULL);
    assert(a->den.sign >= 0 && b->den.sign >= 0);
    return (srmech_bigint_cmp(&a->num, &b->num) == 0
            && srmech_bigint_cmp(&a->den, &b->den) == 0);
}

/* ---- monomial helpers ------------------------------------------------------- */

int srmech_ellbase_mono_is_zero(const srmech_ell_mono_t *m)
{
    assert(m != NULL);
    assert(m->coeff.num.limbs != NULL);
    return srmech_bigint_is_zero(&m->coeff.num);
}

srmech_status_t srmech_ellbase_mono_set_one(srmech_ell_ctx_t *c,
                                            srmech_ell_mono_t *m)
{
    srmech_status_t st;
    assert(c != NULL && m != NULL);
    assert(m->exps != NULL);
    st = srmech_bigint_set_i64(&m->coeff.num, 1);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&m->coeff.den, 1);
    if (st != SRMECH_OK) { return st; }
    memset(m->exps, 0, c->n_syms * sizeof(int32_t));
    return SRMECH_OK;
}

srmech_status_t srmech_ellbase_mono_copy(srmech_ell_ctx_t *c, srmech_ell_mono_t *out,
                                         const srmech_ell_mono_t *a)
{
    srmech_status_t st;
    assert(c != NULL && out != NULL && a != NULL);
    assert(out->exps != NULL && a->exps != NULL);
    st = srmech_ellbase_q_copy(&out->coeff, &a->coeff);
    if (st != SRMECH_OK) { return st; }
    memcpy(out->exps, a->exps, c->n_syms * sizeof(int32_t));
    return SRMECH_OK;
}

/* out := a * b (monomial multiply: coeff *, exponents +). out distinct. */
srmech_status_t srmech_ellbase_mono_mul(srmech_ell_ctx_t *c, srmech_ell_mono_t *out,
                                        const srmech_ell_mono_t *a,
                                        const srmech_ell_mono_t *b,
                                        srmech_bigint_t *g, srmech_bigint_t *t0,
                                        srmech_bigint_t *t1)
{
    srmech_status_t st;
    size_t i;
    assert(c != NULL && out != NULL && a != NULL && b != NULL);
    assert(g != NULL);
    st = srmech_ellbase_q_mul(c, &out->coeff, &a->coeff, &b->coeff, g, t0, t1);
    if (st != SRMECH_OK) { return st; }
    for (i = 0; i < c->n_syms; i++) {
        out->exps[i] = a->exps[i] + b->exps[i];
    }
    return SRMECH_OK;
}

/* out := 1 / a (monomial inverse: coeff 1/coeff, exponents negated). a nonzero. */
srmech_status_t srmech_ellbase_mono_inv(srmech_ell_ctx_t *c, srmech_ell_mono_t *out,
                                        const srmech_ell_mono_t *a)
{
    srmech_status_t st;
    size_t i;
    assert(c != NULL && out != NULL && a != NULL);
    assert(!srmech_ellbase_mono_is_zero(a));
    st = srmech_bigint_copy(&out->coeff.num, &a->coeff.den);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(&out->coeff.den, &a->coeff.num);
    if (st != SRMECH_OK) { return st; }
    if (out->coeff.den.sign < 0) {
        out->coeff.num.sign = (out->coeff.num.sign == 0) ? 0
                              : -out->coeff.num.sign;
        out->coeff.den.sign = -out->coeff.den.sign;
    }
    for (i = 0; i < c->n_syms; i++) {
        out->exps[i] = -a->exps[i];
    }
    return SRMECH_OK;
}

/* out := a / b (monomial divide). b nonzero. */
srmech_status_t srmech_ellbase_mono_div(srmech_ell_ctx_t *c, srmech_ell_mono_t *out,
                                        const srmech_ell_mono_t *a,
                                        const srmech_ell_mono_t *b,
                                        srmech_ell_mono_t *binv, srmech_bigint_t *g,
                                        srmech_bigint_t *t0, srmech_bigint_t *t1)
{
    srmech_status_t st;
    assert(c != NULL && out != NULL && a != NULL && b != NULL && binv != NULL);
    assert(!srmech_ellbase_mono_is_zero(b));
    st = srmech_ellbase_mono_inv(c, binv, b);
    if (st != SRMECH_OK) { return st; }
    return srmech_ellbase_mono_mul(c, out, a, binv, g, t0, t1);
}

/* Compare two monomial EXPONENT maps the way Python's EllMonomial._sort_key does:
 * each is `tuple(sorted(exps.items()))` -- a sorted list of (symbol, exp) pairs with
 * ZERO exponents OMITTED -- compared LEXICOGRAPHICALLY pair-by-pair. The symbol table
 * is interned in the Python sorted-symbol-NAME order, so a merge-walk over the NONZERO
 * dense entries (in ascending index = ascending symbol-name) reproduces the tuple
 * compare exactly. A plain index-wise compare would be WRONG: ((a,2),(c,1)) vs ((b,1),)
 * tuple-compares ('a',2) < ('b',1) by symbol-name FIRST, not by the index-0 exponent.
 * Returns -1 / 0 / +1. */
int srmech_ellbase_exps_cmp(const srmech_ell_ctx_t *c, const int32_t *a,
                            const int32_t *b)
{
    size_t ia = 0;
    size_t ib = 0;
    assert(c != NULL && a != NULL && b != NULL);
    assert(c->n_syms >= 1u);
    for (;;) {
        while (ia < c->n_syms && a[ia] == 0) { ia++; }   /* next nonzero pair in a */
        while (ib < c->n_syms && b[ib] == 0) { ib++; }   /* next nonzero pair in b */
        if (ia >= c->n_syms && ib >= c->n_syms) { return 0; }   /* both exhausted  */
        if (ia >= c->n_syms) { return -1; }   /* a is a prefix -> a < b (shorter)   */
        if (ib >= c->n_syms) { return 1; }    /* b is a prefix -> a > b             */
        if (ia != ib) {
            /* the lex-first present symbol differs: smaller symbol INDEX (= name) wins. */
            return (ia < ib) ? -1 : 1;
        }
        if (a[ia] != b[ib]) {                 /* same symbol: compare its exponent. */
            return (a[ia] < b[ib]) ? -1 : 1;
        }
        ia++;
        ib++;
    }
}

/* Full monomial sort-key compare (exps, then coeff num, then coeff den) -- the
 * Python EllMonomial._sort_key total order. Returns -1 / 0 / +1. */
int srmech_ellbase_mono_cmp(const srmech_ell_ctx_t *c, const srmech_ell_mono_t *a,
                            const srmech_ell_mono_t *b)
{
    int e;
    int cn;
    assert(c != NULL && a != NULL && b != NULL);
    assert(a->exps != NULL && b->exps != NULL);
    e = srmech_ellbase_exps_cmp(c, a->exps, b->exps);
    if (e != 0) { return e; }
    cn = srmech_bigint_cmp(&a->coeff.num, &b->coeff.num);
    if (cn != 0) { return cn; }
    return srmech_bigint_cmp(&a->coeff.den, &b->coeff.den);
}

/* 1 iff a == b as monomials (same exps AND same reduced coeff). */
int srmech_ellbase_mono_eq(const srmech_ell_ctx_t *c, const srmech_ell_mono_t *a,
                           const srmech_ell_mono_t *b)
{
    assert(c != NULL && a != NULL && b != NULL);
    assert(a->exps != NULL && b->exps != NULL);
    return (srmech_ellbase_exps_cmp(c, a->exps, b->exps) == 0
            && srmech_ellbase_q_eq(&a->coeff, &b->coeff));
}

/* out := sqrt(z): halve every exponent (each must be even) and take the exact
 * rational sqrt of the coeff (num + den each a perfect square). Sets *ok = 1 on
 * success, 0 when z is NOT a perfect-square monomial. Mirrors _monomial_sqrt. */
srmech_status_t srmech_ellbase_mono_sqrt(srmech_ell_ctx_t *c, srmech_ell_mono_t *out,
                                         const srmech_ell_mono_t *z, int *ok,
                                         srmech_bigint_t *r, srmech_bigint_t *t0)
{
    size_t i;
    srmech_status_t st;
    assert(c != NULL && out != NULL && z != NULL && ok != NULL);
    assert(r != NULL && t0 != NULL);
    *ok = 0;
    if (srmech_ellbase_mono_is_zero(z)) {
        return SRMECH_OK;
    }
    for (i = 0; i < c->n_syms; i++) {
        if ((z->exps[i] & 1) != 0) {     /* odd exponent -> not a perfect square */
            return SRMECH_OK;
        }
    }
    /* sqrt of the coeff numerator + denominator (both >= 0 after Class-K split). */
    st = srmech_bigint_isqrt(r, &z->coeff.num, c->scratch, c->scratch_len);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_mul(t0, r, r);
    if (st != SRMECH_OK) { return st; }
    if (srmech_bigint_cmp(t0, &z->coeff.num) != 0) {
        return SRMECH_OK;                /* numerator not a perfect square */
    }
    st = srmech_bigint_copy(&out->coeff.num, r);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_isqrt(r, &z->coeff.den, c->scratch, c->scratch_len);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_mul(t0, r, r);
    if (st != SRMECH_OK) { return st; }
    if (srmech_bigint_cmp(t0, &z->coeff.den) != 0) {
        return SRMECH_OK;                /* denominator not a perfect square */
    }
    st = srmech_bigint_copy(&out->coeff.den, r);
    if (st != SRMECH_OK) { return st; }
    for (i = 0; i < c->n_syms; i++) {
        out->exps[i] = z->exps[i] / 2;
    }
    *ok = 1;
    return SRMECH_OK;
}

/* ---- Theta.canonicalize ----------------------------------------------------- */

/* Write ONLY the canonical ARGUMENT of theta(z; p) into out_arg (the ThetaSum
 * is_zero decision uses just the argument, never the prefactor). `out_arg` doubles
 * as the z0 working buffer (rc63's NO-ALLOC behaviour: copy z -> out_arg, strip p,
 * compare to its inverse, possibly overwrite with the inverse). `zinv` is the ONE
 * caller scratch monomial. Mirrors ellbase.Theta.canonicalize's argument (the
 * orientation rule theta(w^-1) = -w^-1 theta(w) flips the rep but the decision needs
 * only the argument). */
srmech_status_t srmech_ellbase_theta_canon_arg(srmech_ell_ctx_t *c,
                                               srmech_ell_mono_t *out_arg,
                                               const srmech_ell_mono_t *z, int psym,
                                               srmech_ell_mono_t *zinv)
{
    int cmp;
    srmech_status_t st;
    assert(c != NULL && out_arg != NULL && z != NULL);
    assert(zinv != NULL);
    /* strip p^k -> z0 (p-exponent 0). */
    st = srmech_ellbase_mono_copy(c, out_arg, z);
    if (st != SRMECH_OK) { return st; }
    if (psym >= 0) { out_arg->exps[psym] = 0; }
    /* orientation: pick the canonical rep of {z0, z0^-1}; theta(w^-1) = -w^-1 theta(w).
     * The DECISION only needs the canonical ARGUMENT, so we flip z0 -> z0^-1 when z0's
     * sort-key exceeds z0^-1's (and z0 != z0^-1), exactly as Python does. */
    st = srmech_ellbase_mono_inv(c, zinv, out_arg);
    if (st != SRMECH_OK) { return st; }
    if (srmech_ellbase_mono_eq(c, out_arg, zinv)) {
        return SRMECH_OK;                    /* self-inverse: left as-is */
    }
    cmp = srmech_ellbase_mono_cmp(c, out_arg, zinv);
    if (cmp > 0) {
        st = srmech_ellbase_mono_copy(c, out_arg, zinv);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* Write the FULL Theta.canonicalize: the exact EllMonomial PREFACTOR into out_pref
 * AND the canonical argument into out_arg, with theta(z; p) == out_pref * theta(out_arg).
 * Mirrors ellbase.Theta.canonicalize:
 *   k = z.exp_of(p); z0 = z * p^-k
 *   pref = (-1)^k * p^{-k(k-1)/2} * z0^{-k}
 *   if z0 != z0^-1 and z0 > z0^-1 (sort-key): pref *= (-1) * z0; z0 = z0^-1
 * z0 / z0inv / tmp are caller scratch monomials; g/t0/t1 caller bigints. */
srmech_status_t srmech_ellbase_theta_canon_full(srmech_ell_ctx_t *c,
                                                srmech_ell_mono_t *out_pref,
                                                srmech_ell_mono_t *out_arg,
                                                const srmech_ell_mono_t *z, int psym,
                                                srmech_ell_mono_t *z0,
                                                srmech_ell_mono_t *z0inv,
                                                srmech_ell_mono_t *tmp,
                                                srmech_bigint_t *g,
                                                srmech_bigint_t *t0,
                                                srmech_bigint_t *t1)
{
    int32_t k;
    int32_t i;
    int neg_exp;
    srmech_status_t st;
    assert(c != NULL && out_pref != NULL && out_arg != NULL && z != NULL);
    assert(z0 != NULL && z0inv != NULL && tmp != NULL);
    /* z0 = z with p-exp 0; k = z.exp_of(p). */
    st = srmech_ellbase_mono_copy(c, z0, z);
    if (st != SRMECH_OK) { return st; }
    k = (psym >= 0) ? z->exps[psym] : 0;
    if (psym >= 0) { z0->exps[psym] = 0; }
    /* out_pref = (-1)^k * p^{-k(k-1)/2}; then *= z0^{-k}. */
    st = srmech_ellbase_mono_set_one(c, out_pref);
    if (st != SRMECH_OK) { return st; }
    if ((k % 2) != 0) { out_pref->coeff.num.sign = -out_pref->coeff.num.sign; }
    if (psym >= 0) { out_pref->exps[psym] = -(int32_t)((k * (k - 1)) / 2); }
    /* z0^{-k}: monomial power by -k (mirrors z0 ** (-k)). neg_exp = (-k) sign. */
    neg_exp = (-k < 0) ? 1 : 0;
    st = srmech_ellbase_mono_set_one(c, tmp);          /* tmp accumulates z0^{|−k|} */
    if (st != SRMECH_OK) { return st; }
    for (i = 0; i < (neg_exp ? k : -k); i++) {         /* |−k| iterations          */
        st = srmech_ellbase_mono_mul(c, z0inv, tmp, z0, g, t0, t1);
        if (st != SRMECH_OK) { return st; }
        st = srmech_ellbase_mono_copy(c, tmp, z0inv);
        if (st != SRMECH_OK) { return st; }
    }
    if (neg_exp) {                                     /* (-k) < 0 -> invert */
        st = srmech_ellbase_mono_inv(c, z0inv, tmp);
        if (st != SRMECH_OK) { return st; }
        st = srmech_ellbase_mono_copy(c, tmp, z0inv);
        if (st != SRMECH_OK) { return st; }
    }
    st = srmech_ellbase_mono_mul(c, z0inv, out_pref, tmp, g, t0, t1);  /* pref*z0^-k */
    if (st != SRMECH_OK) { return st; }
    st = srmech_ellbase_mono_copy(c, out_pref, z0inv);
    if (st != SRMECH_OK) { return st; }
    /* orientation flip: z0inv = z0^-1; if z0 != z0inv and z0 > z0inv -> pref *= -z0. */
    st = srmech_ellbase_mono_inv(c, z0inv, z0);
    if (st != SRMECH_OK) { return st; }
    if (!srmech_ellbase_mono_eq(c, z0, z0inv)
        && srmech_ellbase_mono_cmp(c, z0, z0inv) > 0) {
        st = srmech_ellbase_mono_mul(c, tmp, out_pref, z0, g, t0, t1);  /* pref*z0 */
        if (st != SRMECH_OK) { return st; }
        tmp->coeff.num.sign = (tmp->coeff.num.sign == 0) ? 0
                              : -tmp->coeff.num.sign;                   /* * (-1) */
        st = srmech_ellbase_mono_copy(c, out_pref, tmp);
        if (st != SRMECH_OK) { return st; }
        return srmech_ellbase_mono_copy(c, out_arg, z0inv);            /* z0 = z0^-1 */
    }
    return srmech_ellbase_mono_copy(c, out_arg, z0);
}

/* ============================================================================ *
 *  (2) EllRatio decision peer -- srmech_ellratio_is_elliptic (COMPLETE predicate)
 * ============================================================================ *
 *
 * is_elliptic() == (pshift() == self): the term-ratio is a genuine elliptic
 * function (invariant under the period shift x -> p*x) IFF its period-shift equals
 * itself. pshift multiplies the prefactor + every theta argument by p^{x-exponent},
 * builds a FRESH EllRatio (Theta.canonicalize each factor folding the quasi-
 * periodicity prefactor, cancel matching canonical thetas num<->den, sort), and the
 * decision compares that canonical (prefactor, num-multiset, den-multiset) to self's
 * (already-canonical) form EXACTLY. */

/* The EllRatio scratch + working-value types + their construction algebra were
 * PROMOTED to srmech_ellbase_internal.h (rc-genuine) so the GENUINE elliptic-Gosper
 * engine builds on ONE copy of EllRatio.__init__ (the everything-mirrors discipline
 * forbids two copies). The thin aliases below keep this file's call sites (`er_*`)
 * unchanged while the single shared definitions carry the exported symbols. */
typedef srmech_ell_er_scr_t   er_scr_t;
typedef srmech_ell_er_ratio_t er_ratio_t;

#define ER_SCR_MONOS SRMECH_ELL_ER_SCR_MONOS

/* Keep this file's internal call sites on the short `er_*` names; the single shared
 * definitions carry the exported `srmech_ellbase_er_*` symbols. */
#define er_bind_scr    srmech_ellbase_er_bind_scr
#define er_bind_ratio  srmech_ellbase_er_bind_ratio
#define er_build       srmech_ellbase_er_build
#define er_ratio_eq    srmech_ellbase_er_ratio_eq
#define er_pshift_arg  srmech_ellbase_er_pshift_arg
#define er_qshift_arg  srmech_ellbase_er_qshift_arg
#define er_arena_init  srmech_ellbase_er_arena_init
#define er_mono_words  srmech_ellbase_er_mono_words

srmech_status_t srmech_ellbase_er_bind_scr(srmech_ell_ctx_t *c, er_scr_t *s,
                                           size_t flagcap)
{
    uint32_t *raw;
    srmech_status_t st;
    assert(c != NULL && s != NULL);
    assert(c->cap > 0u);
    st = srmech_ellbase_bind_mono_arr(c, &s->pm, ER_SCR_MONOS);
    if (st != SRMECH_OK) { return st; }
    raw = srmech_ellbase_take_words(c, (flagcap == 0u) ? 1u : flagcap);
    if (raw == NULL) { return SRMECH_ERR_OVERFLOW; }
    s->used = (int *)raw;
    st = srmech_ellbase_bind_bi(c, &s->g);
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_bi(c, &s->t0); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_bi(c, &s->t1); }
    return st;
}

srmech_status_t er_bind_ratio(srmech_ell_ctx_t *c, er_ratio_t *r,
                                     size_t cap_num, size_t cap_den)
{
    srmech_status_t st;
    assert(c != NULL && r != NULL);
    assert(cap_num >= 1u && cap_den >= 1u);
    st = srmech_ellbase_bind_mono(c, &r->pref);
    if (st == SRMECH_OK) {
        st = srmech_ellbase_bind_mono_arr(c, &r->num, (cap_num == 0u) ? 1u : cap_num);
    }
    if (st == SRMECH_OK) {
        st = srmech_ellbase_bind_mono_arr(c, &r->den, (cap_den == 0u) ? 1u : cap_den);
    }
    r->n_num = 0;
    r->n_den = 0;
    r->is_zero = 0;
    return st;
}

/* Insert canonical-argument monomial `a` into the sorted array `arr[0..*n)` keeping it
 * ascending by the EllMonomial._sort_key total order (a STABLE multiset sort matching
 * Python's list.sort(key=arg._sort_key)). cap is the array capacity. */
static srmech_status_t er_sorted_insert(srmech_ell_ctx_t *c, srmech_ell_mono_t *arr,
                                        size_t *n, size_t cap,
                                        const srmech_ell_mono_t *a)
{
    size_t i;
    size_t j;
    srmech_status_t st;
    assert(c != NULL && arr != NULL && n != NULL && a != NULL);
    assert(cap >= 1u && a->exps != NULL);
    if (*n >= cap) { return SRMECH_ERR_OVERFLOW; }
    i = *n;
    while (i > 0 && srmech_ellbase_mono_cmp(c, &arr[i - 1], a) > 0) {
        i--;
    }
    for (j = *n; j > i; j--) {                          /* shift up to open a slot */
        st = srmech_ellbase_mono_copy(c, &arr[j], &arr[j - 1]);
        if (st != SRMECH_OK) { return st; }
    }
    st = srmech_ellbase_mono_copy(c, &arr[i], a);
    if (st != SRMECH_OK) { return st; }
    *n += 1u;
    return SRMECH_OK;
}

/* Canonicalize each raw theta arg into `canon[i]`, folding its prefactor into the global
 * prefactor `pref` -- multiply for a numerator factor (`do_mul`=1), divide for a
 * denominator factor (`do_mul`=0). Mirrors the EllRatio.__init__ fold loops. */
static srmech_status_t er_canon_fold(srmech_ell_ctx_t *c, srmech_ell_mono_t *pref,
                                     const srmech_ell_mono_t *args, size_t n,
                                     srmech_ell_mono_t *canon, int do_mul, int psym,
                                     er_scr_t *s)
{
    size_t i;
    srmech_status_t st;
    assert(c != NULL && pref != NULL && s != NULL);
    assert(args != NULL || n == 0u);
    for (i = 0; i < n; i++) {
        st = srmech_ellbase_theta_canon_full(c, &s->pm[0], &canon[i], &args[i], psym,
                                             &s->pm[2], &s->pm[3], &s->pm[4],
                                             &s->g, &s->t0, &s->t1);
        if (st != SRMECH_OK) { return st; }
        if (do_mul) {
            st = srmech_ellbase_mono_mul(c, &s->pm[1], pref, &s->pm[0],
                                         &s->g, &s->t0, &s->t1);
        } else {
            st = srmech_ellbase_mono_div(c, &s->pm[1], pref, &s->pm[0], &s->pm[5],
                                         &s->g, &s->t0, &s->t1);
        }
        if (st != SRMECH_OK) { return st; }
        st = srmech_ellbase_mono_copy(c, pref, &s->pm[1]);
        if (st != SRMECH_OK) { return st; }
    }
    return SRMECH_OK;
}

/* Cancel matching canonical thetas (cn vs cd, multiset min) then sort the survivors into
 * out->num / out->den. Mirrors _ratio_cancel. */
static srmech_status_t er_cancel_sort(srmech_ell_ctx_t *c, er_ratio_t *out,
                                      srmech_ell_mono_t *cn, size_t n_num, size_t cn_cap,
                                      srmech_ell_mono_t *cd, size_t n_den, size_t cd_cap,
                                      er_scr_t *s)
{
    size_t i;
    size_t j;
    size_t kept_n = 0;
    size_t kept_d = 0;
    srmech_status_t st;
    assert(c != NULL && out != NULL && s != NULL);
    assert(s->used != NULL);
    for (i = 0; i < n_num; i++) { s->used[i] = 0; }     /* num kept-flag */
    for (j = 0; j < n_den; j++) {
        int matched = 0;
        for (i = 0; i < n_num; i++) {
            if (s->used[i]) { continue; }
            if (srmech_ellbase_mono_eq(c, &cn[i], &cd[j])) {
                s->used[i] = 1;                         /* this num cancels */
                matched = 1;
                break;
            }
        }
        if (!matched) {                                 /* den survivor */
            st = er_sorted_insert(c, out->den, &kept_d, cd_cap, &cd[j]);
            if (st != SRMECH_OK) { return st; }
        }
    }
    for (i = 0; i < n_num; i++) {                       /* num survivors */
        if (s->used[i]) { continue; }
        st = er_sorted_insert(c, out->num, &kept_n, cn_cap, &cn[i]);
        if (st != SRMECH_OK) { return st; }
    }
    out->n_num = kept_n;
    out->n_den = kept_d;
    return SRMECH_OK;
}

/* Build the canonical EllRatio from raw inputs: the prefactor `pref0` + the raw num /
 * den theta ARGUMENT monomials (each canonicalized via theta_canon_full, its prefactor
 * folded -- a num factor multiplies the global pref, a den factor divides it), then the
 * matching canonical thetas cancel between num and den (multiset min), and the survivors
 * are sorted. Mirrors EllRatio.__init__ exactly. */
srmech_status_t er_build(srmech_ell_ctx_t *c, er_ratio_t *out,
                                const srmech_ell_mono_t *pref0,
                                const srmech_ell_mono_t *num_args, size_t n_num,
                                const srmech_ell_mono_t *den_args, size_t n_den,
                                int psym, er_scr_t *s, srmech_ell_mono_t *cn,
                                size_t cn_cap, srmech_ell_mono_t *cd, size_t cd_cap)
{
    srmech_status_t st;
    assert(c != NULL && out != NULL && pref0 != NULL && s != NULL);
    assert((num_args != NULL || n_num == 0u) && (den_args != NULL || n_den == 0u));
    /* global prefactor starts at pref0; fold each theta's canonicalize prefactor. */
    st = srmech_ellbase_mono_copy(c, &out->pref, pref0);
    if (st != SRMECH_OK) { return st; }
    st = er_canon_fold(c, &out->pref, num_args, n_num, cn, /*do_mul*/1, psym, s);
    if (st != SRMECH_OK) { return st; }
    st = er_canon_fold(c, &out->pref, den_args, n_den, cd, /*do_mul*/0, psym, s);
    if (st != SRMECH_OK) { return st; }
    if (srmech_ellbase_mono_is_zero(&out->pref)) {
        out->is_zero = 1;
        out->n_num = 0;
        out->n_den = 0;
        return SRMECH_OK;
    }
    out->is_zero = 0;
    return er_cancel_sort(c, out, cn, n_num, cn_cap, cd, n_den, cd_cap, s);
}

/* 1 iff two canonical sorted argument arrays are EQUAL element-wise (both already
 * sorted by er_sorted_insert, so a positional compare is a multiset compare). */
static int er_args_eq(const srmech_ell_ctx_t *c, const srmech_ell_mono_t *a, size_t na,
                      const srmech_ell_mono_t *b, size_t nb)
{
    size_t i;
    assert(c != NULL);
    assert((a != NULL || na == 0u) && (b != NULL || nb == 0u));
    if (na != nb) { return 0; }
    for (i = 0; i < na; i++) {
        if (!srmech_ellbase_mono_eq(c, &a[i], &b[i])) { return 0; }
    }
    return 1;
}

/* 1 iff two canonical EllRatios are EQUAL (EllRatio.__eq__: same prefactor monomial
 * AND same num-multiset AND same den-multiset; a zero ratio equals a zero ratio). */
int er_ratio_eq(const srmech_ell_ctx_t *c, const er_ratio_t *a,
                       const er_ratio_t *b)
{
    assert(c != NULL && a != NULL && b != NULL);
    assert(a->pref.exps != NULL && b->pref.exps != NULL);
    if (a->is_zero || b->is_zero) {
        return (a->is_zero && b->is_zero) ? 1 : 0;
    }
    if (!srmech_ellbase_mono_eq(c, &a->pref, &b->pref)) { return 0; }
    return er_args_eq(c, a->num, a->n_num, b->num, b->n_num)
           && er_args_eq(c, a->den, a->n_den, b->den, b->n_den);
}

/* Period-shift one canonical argument monomial: a -> a * p^{a.exp_of(x)} (the x -> p*x
 * substitution's monomial effect). Mirrors EllRatio._shift's `sm`. */
srmech_status_t er_pshift_arg(srmech_ell_ctx_t *c, srmech_ell_mono_t *out,
                                     const srmech_ell_mono_t *a, int xsym, int psym)
{
    int32_t ex;
    srmech_status_t st;
    assert(c != NULL && out != NULL && a != NULL);
    assert(a->exps != NULL && out->exps != NULL);
    st = srmech_ellbase_mono_copy(c, out, a);
    if (st != SRMECH_OK) { return st; }
    ex = (xsym >= 0) ? a->exps[xsym] : 0;
    if (psym >= 0) { out->exps[psym] += ex; }            /* * p^{x-exponent} */
    return SRMECH_OK;
}

/* Summation-shift one canonical argument monomial along q: a -> a * q^{a.exp_of(x)}
 * (the x -> q*x substitution, EllRatio.qshift's `sm`), or the INVERSE shift x -> x/q
 * (a -> a * q^{-a.exp_of(x)}, the elliptic_gosper _xshift_inverse `_sm`) when `inverse`
 * is set. The qsym analogue of er_pshift_arg; no abs (Class-K sign on the exponent). */
srmech_status_t er_qshift_arg(srmech_ell_ctx_t *c, srmech_ell_mono_t *out,
                              const srmech_ell_mono_t *a, int xsym, int qsym,
                              int inverse)
{
    int32_t ex;
    srmech_status_t st;
    assert(c != NULL && out != NULL && a != NULL);
    assert(a->exps != NULL && out->exps != NULL);
    st = srmech_ellbase_mono_copy(c, out, a);
    if (st != SRMECH_OK) { return st; }
    ex = (xsym >= 0) ? a->exps[xsym] : 0;
    if (inverse) { ex = -ex; }                           /* x -> x/q : q^{-x-exp} */
    if (qsym >= 0) { out->exps[qsym] += ex; }            /* * q^{+/- x-exponent}  */
    return SRMECH_OK;
}

/* ---- input parse + the public is_elliptic orchestration --------------------- */

/* Parse a flat monomial array (coeff_num/coeff_den srmech_bigint + int32[n_syms]
 * exps rows, in order: prefactor, num0..K-1, den0..L-1) into the prefactor monomial
 * `pref` + the num / den raw-argument arrays. `mi`/`ej` are the running monomial /
 * exps-row cursors (advanced). */
static srmech_status_t er_parse(srmech_ell_ctx_t *c, srmech_ell_mono_t *pref,
                                srmech_ell_mono_t *num, size_t n_num,
                                srmech_ell_mono_t *den, size_t n_den,
                                const srmech_bigint_t *cnum,
                                const srmech_bigint_t *cden,
                                const int32_t *exps_flat)
{
    size_t k;
    size_t mi = 0;
    size_t ej = 0;
    srmech_status_t st;
    assert(c != NULL && pref != NULL);
    assert((num != NULL || n_num == 0u) && (den != NULL || n_den == 0u));
    assert(cnum != NULL && cden != NULL && exps_flat != NULL);
    st = srmech_bigint_copy(&pref->coeff.num, &cnum[mi]);
    if (st == SRMECH_OK) { st = srmech_bigint_copy(&pref->coeff.den, &cden[mi]); }
    if (st != SRMECH_OK) { return st; }
    memcpy(pref->exps, exps_flat + ej, c->n_syms * sizeof(int32_t));
    mi++;
    ej += c->n_syms;
    for (k = 0; k < n_num; k++) {
        st = srmech_bigint_copy(&num[k].coeff.num, &cnum[mi]);
        if (st == SRMECH_OK) { st = srmech_bigint_copy(&num[k].coeff.den, &cden[mi]); }
        if (st != SRMECH_OK) { return st; }
        memcpy(num[k].exps, exps_flat + ej, c->n_syms * sizeof(int32_t));
        mi++;
        ej += c->n_syms;
    }
    for (k = 0; k < n_den; k++) {
        st = srmech_bigint_copy(&den[k].coeff.num, &cnum[mi]);
        if (st == SRMECH_OK) { st = srmech_bigint_copy(&den[k].coeff.den, &cden[mi]); }
        if (st != SRMECH_OK) { return st; }
        memcpy(den[k].exps, exps_flat + ej, c->n_syms * sizeof(int32_t));
        mi++;
        ej += c->n_syms;
    }
    return SRMECH_OK;
}

/* Carve the arena: split `ws` into the bump pool + a trailing bigint scratch region
 * (8-byte-aligned uint32). Returns OVERFLOW if `ws` is NULL or too small. (Mirrors
 * the thetasum arena split.) */
srmech_status_t er_arena_init(srmech_ell_ctx_t *c, void *ws, size_t ws_len)
{
    uint32_t *base = (uint32_t *)ws;
    size_t words = ws_len / sizeof(uint32_t);
    size_t scratch_words = (size_t)c->cap * 16u + 512u;
    assert(c != NULL);
    assert((uintptr_t)ws % 8u == 0u || ws == NULL);
    if (ws == NULL || words < scratch_words + 64u) {
        return SRMECH_ERR_OVERFLOW;
    }
    c->pool = base;
    c->pool_words = words - scratch_words;
    c->pool_cur = 0u;
    c->scratch = (void *)(base + (words - scratch_words));
    c->scratch_len = scratch_words * sizeof(uint32_t);
    return SRMECH_OK;
}

/* The per-monomial arena footprint (words): 2 bigints (2*cap) + an exps row (ns). */
size_t er_mono_words(size_t cap, size_t ns)
{
    assert(cap >= 1u);
    assert(ns >= 1u);
    return 2u * cap + ns + 8u;
}

/* Decide whether the EllRatio (prefactor `pref` + the canonical `n_num` numerator +
 * `n_den` denominator theta arguments) is a genuine ELLIPTIC function, i.e. invariant
 * under the period shift x -> p*x (EllRatio.is_elliptic == (pshift() == self)). The
 * input ratio is assumed ALREADY canonical (Python passes self's canonical form); the
 * C re-builds self canonically too (idempotent) so the comparison is apples-to-apples.
 *
 * Wire form: the interned symbol-table dimension `n_syms`; the x / p interned indices
 * (`xsym` / `psym`, -1 if absent); the num / den theta counts; the flat monomial coeff
 * arrays `coeff_num` / `coeff_den` (each an exact-Q num/den srmech_bigint, in order
 * prefactor, num0..K-1, den0..L-1) + the flat int32 exponent rows `exps_flat`
 * (int32[n_syms] per monomial, same order). `coeff_cap` is the per-bigint limb cap.
 * *out_is_elliptic = 1 iff genuinely elliptic. Caller arena `ws`. */
/* The bound working buffers for the is_elliptic decision (carved once from the arena). */
typedef struct er_work {
    er_scr_t           s;
    srmech_ell_mono_t  pref;     /* parsed input prefactor                       */
    srmech_ell_mono_t  spref;    /* period-shifted prefactor                     */
    srmech_ell_mono_t *num;      /* parsed raw num args                          */
    srmech_ell_mono_t *den;      /* parsed raw den args                          */
    srmech_ell_mono_t *snum;     /* period-shifted raw num args                  */
    srmech_ell_mono_t *sden;     /* period-shifted raw den args                  */
    srmech_ell_mono_t *cn;       /* canon scratch for er_build (self / shift)    */
    srmech_ell_mono_t *cd;
    er_ratio_t         self_r;
    er_ratio_t         shift_r;
    size_t             cap_num;
    size_t             cap_den;
} er_work_t;

/* Carve every working buffer for the decision from the arena. */
static srmech_status_t er_bind_work(srmech_ell_ctx_t *c, er_work_t *w)
{
    size_t flagcap = (w->cap_num > w->cap_den) ? w->cap_num : w->cap_den;
    srmech_status_t st;
    assert(c != NULL && w != NULL);
    assert(w->cap_num >= 1u && w->cap_den >= 1u);
    st = srmech_ellbase_bind_mono(c, &w->pref);
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono(c, &w->spref); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono_arr(c, &w->num, w->cap_num); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono_arr(c, &w->den, w->cap_den); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono_arr(c, &w->snum, w->cap_num); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono_arr(c, &w->sden, w->cap_den); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono_arr(c, &w->cn, w->cap_num); }
    if (st == SRMECH_OK) { st = srmech_ellbase_bind_mono_arr(c, &w->cd, w->cap_den); }
    if (st == SRMECH_OK) { st = er_bind_ratio(c, &w->self_r, w->cap_num, w->cap_den); }
    if (st == SRMECH_OK) { st = er_bind_ratio(c, &w->shift_r, w->cap_num, w->cap_den); }
    if (st == SRMECH_OK) { st = er_bind_scr(c, &w->s, flagcap); }
    return st;
}

/* Compute shift_r = the canonical EllRatio of the PERIOD-SHIFT of (pref, num, den):
 * spref = pref * p^{pref.x-exp}; each arg *= p^{arg.x-exp}; then er_build. */
static srmech_status_t er_compute_shift(srmech_ell_ctx_t *c, er_work_t *w,
                                        size_t n_num, size_t n_den, int xsym, int psym)
{
    size_t i;
    srmech_status_t st;
    assert(c != NULL && w != NULL);
    assert(n_num <= w->cap_num && n_den <= w->cap_den);
    st = er_pshift_arg(c, &w->spref, &w->pref, xsym, psym);
    if (st != SRMECH_OK) { return st; }
    for (i = 0; i < n_num; i++) {
        st = er_pshift_arg(c, &w->snum[i], &w->num[i], xsym, psym);
        if (st != SRMECH_OK) { return st; }
    }
    for (i = 0; i < n_den; i++) {
        st = er_pshift_arg(c, &w->sden[i], &w->den[i], xsym, psym);
        if (st != SRMECH_OK) { return st; }
    }
    return er_build(c, &w->shift_r, &w->spref, w->snum, n_num, w->sden, n_den, psym,
                    &w->s, w->cn, w->cap_num, w->cd, w->cap_den);
}

srmech_status_t srmech_ellratio_is_elliptic(size_t n_syms, int xsym, int psym,
                                            size_t n_num, size_t n_den,
                                            const srmech_bigint_t *coeff_num,
                                            const srmech_bigint_t *coeff_den,
                                            const int32_t *exps_flat,
                                            uint32_t coeff_cap, int *out_is_elliptic,
                                            void *ws, size_t ws_len)
{
    srmech_ell_ctx_t c = {0};
    er_work_t w = {0};
    srmech_status_t st;
    assert(out_is_elliptic != NULL);
    assert(n_num == 0u || coeff_num != NULL);
    if (out_is_elliptic == NULL) { return SRMECH_ERR_NULL_ARG; }
    *out_is_elliptic = 0;
    if (coeff_num == NULL || coeff_den == NULL || exps_flat == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    c.n_syms = (n_syms == 0u) ? 1u : n_syms;
    c.cap = (coeff_cap < 4u) ? 4u : coeff_cap;
    w.cap_num = (n_num == 0u) ? 1u : n_num;
    w.cap_den = (n_den == 0u) ? 1u : n_den;
    st = er_arena_init(&c, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    st = er_bind_work(&c, &w);
    if (st != SRMECH_OK) { return st; }
    /* parse the input prefactor + raw num/den arguments. */
    st = er_parse(&c, &w.pref, w.num, n_num, w.den, n_den, coeff_num, coeff_den,
                  exps_flat);
    if (st != SRMECH_OK) { return st; }
    /* self_r = canonical EllRatio(pref, num, den). */
    st = er_build(&c, &w.self_r, &w.pref, w.num, n_num, w.den, n_den, psym, &w.s,
                  w.cn, w.cap_num, w.cd, w.cap_den);
    if (st != SRMECH_OK) { return st; }
    /* shift_r = canonical EllRatio of the period shift x -> p*x. */
    st = er_compute_shift(&c, &w, n_num, n_den, xsym, psym);
    if (st != SRMECH_OK) { return st; }
    /* is_elliptic == (pshift() == self). */
    *out_is_elliptic = er_ratio_eq(&c, &w.shift_r, &w.self_r);
    return SRMECH_OK;
}

/* ---- the #712 half-period edge-multiplier reader (rc119) -------------------- *
 *
 * The C peer of EllRatio.half_shift_response: the exact monomial multiplier the
 * carrier acquires under a HALF-period translation. Two axes (the Dzhanibekov
 * torque-free torus's two half-beats, #712):
 *   axis 0 (REAL 2K)  : the double-cover deck transformation var -> -var (each
 *                       monomial's Class-K coeff picks up (-1)^{var-exponent});
 *                       bare (a pure sign) iff every theta arg is EVEN in var.
 *   axis 1 (NOME 2iK'): the carrier period shift var -> p*var (the -x^-1-type
 *                       Theta.canonicalize quasi-periodicity prefactor); always
 *                       bare (pshift maps each canonical theta to a scalar
 *                       multiple of itself).
 * The multiplier is (shift(self) * self.inv()).prefactor -- a bare monomial iff
 * the shifted theta-parts equal self's (they cancel against self.inv()); *out_is_
 * bare reports it (the boundary-blind #712 finding: a chirality-EVEN reader has
 * even-in-var thetas -> real-axis-bare with a +1 sign). */

/* Negate one canonical argument monomial's Class-K coeff by var-parity (var -> -var:
 * a -> a with coeff *= (-1)^{a.exp_of(var)}). No abs (sign is the Class-K pin-slot). */
static srmech_status_t er_negate_arg(srmech_ell_ctx_t *c, srmech_ell_mono_t *out,
                                     const srmech_ell_mono_t *a, int varsym)
{
    int32_t ev;
    srmech_status_t st;
    assert(c != NULL && out != NULL && a != NULL);
    assert(out->exps != NULL && a->exps != NULL);
    st = srmech_ellbase_mono_copy(c, out, a);
    if (st != SRMECH_OK) { return st; }
    ev = (varsym >= 0) ? a->exps[varsym] : 0;
    if ((ev % 2 != 0) && out->coeff.num.sign != 0) {
        out->coeff.num.sign = -out->coeff.num.sign;      /* (-1)^{var-exp} Class-K */
    }
    return SRMECH_OK;
}

/* Compute shift_r = the canonical EllRatio of the REAL half-beat var -> -var (each
 * monomial negated by var-parity), then er_build (mirrors er_compute_shift). */
static srmech_status_t er_compute_negate(srmech_ell_ctx_t *c, er_work_t *w,
                                         size_t n_num, size_t n_den, int varsym, int psym)
{
    size_t i;
    srmech_status_t st;
    assert(c != NULL && w != NULL);
    assert(n_num <= w->cap_num && n_den <= w->cap_den);
    st = er_negate_arg(c, &w->spref, &w->pref, varsym);
    if (st != SRMECH_OK) { return st; }
    for (i = 0; i < n_num; i++) {
        st = er_negate_arg(c, &w->snum[i], &w->num[i], varsym);
        if (st != SRMECH_OK) { return st; }
    }
    for (i = 0; i < n_den; i++) {
        st = er_negate_arg(c, &w->sden[i], &w->den[i], varsym);
        if (st != SRMECH_OK) { return st; }
    }
    return er_build(c, &w->shift_r, &w->spref, w->snum, n_num, w->sden, n_den, psym,
                    &w->s, w->cn, w->cap_num, w->cd, w->cap_den);
}

/* Emit the edge multiplier = shift_r.pref / self_r.pref into the caller bigints +
 * dense exps row; a non-bare response emits the unit monomial 1. pm[6]/pm[7] are
 * free scratch (er_build's canon fold uses only pm[0..5]). */
static srmech_status_t er_emit_multiplier(srmech_ell_ctx_t *c, er_work_t *w, int bare,
                                          srmech_bigint_t *out_cn,
                                          srmech_bigint_t *out_cd, int32_t *out_exps)
{
    srmech_status_t st;
    srmech_ell_mono_t *mult = &w->s.pm[6];
    srmech_ell_mono_t *binv = &w->s.pm[7];
    assert(c != NULL && w != NULL && out_cn != NULL);
    assert(out_cd != NULL && out_exps != NULL);
    if (!bare) {
        st = srmech_ellbase_mono_set_one(c, mult);
    } else {
        st = srmech_ellbase_mono_div(c, mult, &w->shift_r.pref, &w->self_r.pref,
                                     binv, &w->s.g, &w->s.t0, &w->s.t1);
    }
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(out_cn, &mult->coeff.num);
    if (st == SRMECH_OK) { st = srmech_bigint_copy(out_cd, &mult->coeff.den); }
    if (st != SRMECH_OK) { return st; }
    memcpy(out_exps, mult->exps, c->n_syms * sizeof(int32_t));
    return SRMECH_OK;
}

srmech_status_t srmech_ellratio_half_shift_response(
    size_t n_syms, int varsym, int psym, int axis, size_t n_num, size_t n_den,
    const srmech_bigint_t *coeff_num, const srmech_bigint_t *coeff_den,
    const int32_t *exps_flat, uint32_t coeff_cap, int *out_is_bare,
    srmech_bigint_t *out_coeff_num, srmech_bigint_t *out_coeff_den,
    int32_t *out_exps, void *ws, size_t ws_len)
{
    srmech_ell_ctx_t c = {0};
    er_work_t w = {0};
    srmech_status_t st;
    int bare;
    assert(out_is_bare != NULL && out_exps != NULL);
    assert(out_coeff_num != NULL && out_coeff_den != NULL);
    if (out_is_bare == NULL || out_coeff_num == NULL || out_coeff_den == NULL
        || out_exps == NULL) { return SRMECH_ERR_NULL_ARG; }
    *out_is_bare = 0;
    if (coeff_num == NULL || coeff_den == NULL || exps_flat == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    c.n_syms = (n_syms == 0u) ? 1u : n_syms;
    c.cap = (coeff_cap < 4u) ? 4u : coeff_cap;
    w.cap_num = (n_num == 0u) ? 1u : n_num;
    w.cap_den = (n_den == 0u) ? 1u : n_den;
    st = er_arena_init(&c, ws, ws_len);
    if (st == SRMECH_OK) { st = er_bind_work(&c, &w); }
    if (st == SRMECH_OK) {
        st = er_parse(&c, &w.pref, w.num, n_num, w.den, n_den, coeff_num, coeff_den,
                      exps_flat);
    }
    if (st == SRMECH_OK) {
        st = er_build(&c, &w.self_r, &w.pref, w.num, n_num, w.den, n_den, psym, &w.s,
                      w.cn, w.cap_num, w.cd, w.cap_den);
    }
    if (st == SRMECH_OK) {
        st = (axis == 0)
             ? er_compute_negate(&c, &w, n_num, n_den, varsym, psym)
             : er_compute_shift(&c, &w, n_num, n_den, varsym, psym);
    }
    if (st != SRMECH_OK) { return st; }
    bare = er_args_eq(&c, w.self_r.num, w.self_r.n_num, w.shift_r.num, w.shift_r.n_num)
        && er_args_eq(&c, w.self_r.den, w.self_r.n_den, w.shift_r.den, w.shift_r.n_den);
    *out_is_bare = bare;
    return er_emit_multiplier(&c, &w, bare, out_coeff_num, out_coeff_den, out_exps);
}

/* The minimum `ws_len` BYTES srmech_ellratio_is_elliptic needs for the given shape
 * (n_syms symbols, n_num numerator + n_den denominator theta factors, coeff_limbs the
 * per-coefficient significant-limb estimate). Sized to the inputs -- no compiled-in
 * cap; if RAM balloons the caller mis-encoded the fiber. */
size_t srmech_ellratio_ws_bound(size_t n_syms, size_t n_num, size_t n_den,
                                size_t coeff_limbs)
{
    size_t cap = (coeff_limbs < 4u) ? 4u : coeff_limbs;
    size_t ns = (n_syms == 0u) ? 1u : n_syms;
    size_t cn = (n_num == 0u) ? 1u : n_num;
    size_t cd = (n_den == 0u) ? 1u : n_den;
    size_t mw = er_mono_words(cap, ns);
    /* parsed pref + spref + 6 num/den-sized monomial arrays + 2 ratios (pref+num+den). */
    size_t arrays = (2u * mw)                          /* pref + spref          */
                    + 6u * (cn + cd) * mw              /* num/den/snum/sden/cn/cd */
                    + 2u * (mw + (cn + cd) * mw);      /* self_r + shift_r      */
    size_t scr = ER_SCR_MONOS * mw + (cn + cd) + 3u * cap + 64u;
    size_t scratch_words = cap * 16u + 512u;
    size_t total = arrays + scr + scratch_words + 1024u;
    assert(cap >= 4u);
    assert(total >= scratch_words);
    return total * sizeof(uint32_t);
}

