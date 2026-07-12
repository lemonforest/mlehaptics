/*
 * srmech_tripoly.c — EXACT-RATIONAL TRIVARIATE polynomial over srmech_bigint
 * (the C peer of srmech.amsc.tripoly.TriPoly; the multivariate "sums of sums"
 * creative-telescoping foundation, the 3-variable sibling of the BiPoly the
 * srmech_zeilberger orchestration carries internally).
 *
 * A TriPoly is an exact-Q polynomial in the free variable n and two summation
 * variables j, k. It is carried as a ROW-MAJOR (j, k) GRID of n-polynomials:
 * the grid has aj = (j-degree + 1) rows and ak = (k-degree + 1) columns, and the
 * cell (dj, dk) at flat index `dj*ak + dk` is itself an n-polynomial — a run of
 * exact-rational coefficients in ASCENDING n-degree. The cell n-runs are stored
 * CONCATENATED in a single pair of caller-owned srmech_bigint arrays (nums[] /
 * dens[], ascending n within each cell, cells in row-major (j,k) order), with a
 * parallel `nlen[]` array (length aj*ak) giving each cell's n-run length. A cell
 * coefficient nums[..]/dens[..] is the exact rational of n^dn (dens > 0,
 * gcd(|nums|, dens) == 1; zero coefficient = 0/1).
 *
 * Each op computes the SAME exact rational coefficients the Python TriPoly
 * computes — Class-N rational arithmetic over Class-J reduction — over
 * caller-arena srmech_bigint (NO malloc, JPL Rule 3), each output coefficient
 * reduced to lowest terms with positive denominator. Byte-identical to Python's
 * (num, den) at ANY magnitude (full bignum; no int64/Q61 ceiling).
 *
 *   add/sub : cellwise (j,k)-aligned, coefficientwise exact-Q add/sub of the
 *             two cells' n-runs, then trim
 *   mul     : 2-D (j,k) convolution; each output cell accumulates the exact-Q
 *             n-run convolution (an n-polynomial multiply) of the input cells
 *
 * The C is STANDALONE-COMPLETE: every working carrier is carved from the caller
 * arena `ws` (sized via the matching srmech_tripoly_ws_bound), so the magnitude
 * bound is the CALLER's RAM, not a compiled-in cap. A too-small arena or an out
 * coefficient capacity returns SRMECH_ERR_OVERFLOW (never a silent wrap), and the
 * Python TriPoly falls back to its ceiling-free pure-Python path.
 *
 * Carrier-internal, like srmech_poly.c / srmech_bigexp.c: NOT a Rosetta ledger
 * op (no ToolEntry, no count-test). Additive symbols -> ABI unchanged (stays 3).
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto/recursion): OK — iterative, flat helpers
 *   - Rule 2 (bounded loops)    : OK — bounds are the grid + coefficient counts
 *   - Rule 3 (no malloc)        : OK — caller arena + caller out only
 *   - Rule 4 (<=60 lines/func)  : OK — factored into static helpers
 *   - Rule 5 (>=2 asserts/fn)   : OK — entry-pointer + pre/postcondition
 *   - Rule 7 (return-value)     : OK — srmech_status_t propagated
 *   - Rule 8 (no multi-line mac): OK — no function-like macros
 *   - Rule 10 (warnings clean)  : OK under -Wall -Wextra -Wpedantic -Werror
 *
 * License: MIT.
 */

#include "srmech.h"

#include <assert.h>
#include <stdint.h>

/* A roster of working bigints carved from the caller arena `ws`. qa/qb hold
 * running exact-Q values; the tN are integer scratch for the Q ops; g/rem/rs0/
 * rs1 are the reducer's private gcd + divmod sinks; z0/z1 are read-only 0 / 1.
 * Every carrier is `cap` limbs. (Mirrors srmech_poly.c's poly_ctx_t.) */
typedef struct tri_ctx {
    srmech_bigint_t qa_n;   /* accumulator rational numerator   */
    srmech_bigint_t qa_d;   /* accumulator rational denominator */
    srmech_bigint_t qb_n;   /* second operand numerator         */
    srmech_bigint_t qb_d;   /* second operand denominator       */
    srmech_bigint_t t0;     /* integer scratch                  */
    srmech_bigint_t g;      /* gcd sink (reduce-private)        */
    srmech_bigint_t rem;    /* divmod remainder sink (reduce)   */
    srmech_bigint_t rs0;    /* reduce-private quotient scratch  */
    srmech_bigint_t rs1;    /* reduce-private quotient scratch  */
    srmech_bigint_t z0;     /* read-only 0 (missing-term num)   */
    srmech_bigint_t z1;     /* read-only 1 (missing-term den)   */
    uint32_t limb_cap;      /* per-carrier limb capacity        */
    void  *scratch;         /* divmod/gcd scratch arena tail    */
    size_t scratch_len;     /* its length in BYTES              */
} tri_ctx_t;

#define TRI_N_CARRIERS 11u  /* qa_n,qa_d,qb_n,qb_d,t0,g,rem,rs0,rs1,z0,z1 */

/* ---- forward declarations (Rule 1: no recursion) ------------------- */

static uint32_t *tri_take(uint32_t *base, size_t words, size_t *cur,
                          size_t count);
static srmech_status_t tri_bind(srmech_bigint_t *b, uint32_t *base,
                                size_t words, size_t *cur, uint32_t cap);
static srmech_status_t tri_ctx_init(tri_ctx_t *c, uint32_t cap,
                                    void *ws, size_t ws_len);
static srmech_status_t tri_q_reduce(tri_ctx_t *c, srmech_bigint_t *num,
                                    srmech_bigint_t *den);
static srmech_status_t tri_q_add(tri_ctx_t *c, srmech_bigint_t *out_num,
                                 srmech_bigint_t *out_den,
                                 const srmech_bigint_t *an,
                                 const srmech_bigint_t *ad,
                                 const srmech_bigint_t *bn,
                                 const srmech_bigint_t *bd, int sub);
static srmech_status_t tri_q_mul(tri_ctx_t *c, srmech_bigint_t *out_num,
                                 srmech_bigint_t *out_den,
                                 const srmech_bigint_t *an,
                                 const srmech_bigint_t *ad,
                                 const srmech_bigint_t *bn,
                                 const srmech_bigint_t *bd);
static size_t tri_trim_len(const srmech_bigint_t *nums, size_t n);
static size_t tri_cap_for(size_t coeff_limbs, size_t accum_terms);
static size_t tri_grid_max_limbs(const srmech_bigint_t *nums,
                                 const srmech_bigint_t *dens, size_t total);
static size_t tri_n_total(const size_t *nlen, size_t cells);
static srmech_status_t tri_addsub_cell(tri_ctx_t *c,
                                       const srmech_bigint_t *a_n,
                                       const srmech_bigint_t *a_d, size_t na,
                                       const srmech_bigint_t *b_n,
                                       const srmech_bigint_t *b_d, size_t nb,
                                       int sub, srmech_bigint_t *o_n,
                                       srmech_bigint_t *o_d, size_t *o_len);
static srmech_status_t tri_mac_cell(tri_ctx_t *c,
                                    const srmech_bigint_t *a_n,
                                    const srmech_bigint_t *a_d, size_t na,
                                    const srmech_bigint_t *b_n,
                                    const srmech_bigint_t *b_d, size_t nb,
                                    srmech_bigint_t *o_n, srmech_bigint_t *o_d,
                                    size_t *o_len);

/* ---- caller-arena carve (mirrors poly_take / poly_bind) ------------ */

static uint32_t *tri_take(uint32_t *base, size_t words, size_t *cur,
                          size_t count)
{
    uint32_t *p;
    assert(base != NULL && cur != NULL);
    assert(*cur <= words);
    if (count > words || *cur > words - count) {
        return NULL;
    }
    p = base + *cur;
    *cur += count;
    return p;
}

static srmech_status_t tri_bind(srmech_bigint_t *b, uint32_t *base,
                                size_t words, size_t *cur, uint32_t cap)
{
    uint32_t *limbs = tri_take(base, words, cur, cap);
    assert(b != NULL);
    assert(cap > 0u);
    if (limbs == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    b->limbs = limbs;
    b->cap = cap;
    b->n = 0u;
    b->sign = 0;
    return SRMECH_OK;
}

static srmech_status_t tri_ctx_init(tri_ctx_t *c, uint32_t cap,
                                    void *ws, size_t ws_len)
{
    uint32_t *base = (uint32_t *)ws;
    size_t words = ws_len / sizeof(uint32_t), cur = 0u;
    srmech_status_t st = SRMECH_OK;
    assert(c != NULL);
    assert((uintptr_t)ws % sizeof(uint32_t) == 0u || ws == NULL);
    c->limb_cap = cap;
    st |= tri_bind(&c->qa_n, base, words, &cur, cap);
    st |= tri_bind(&c->qa_d, base, words, &cur, cap);
    st |= tri_bind(&c->qb_n, base, words, &cur, cap);
    st |= tri_bind(&c->qb_d, base, words, &cur, cap);
    st |= tri_bind(&c->t0, base, words, &cur, cap);
    st |= tri_bind(&c->g, base, words, &cur, cap);
    st |= tri_bind(&c->rem, base, words, &cur, cap);
    st |= tri_bind(&c->rs0, base, words, &cur, cap);
    st |= tri_bind(&c->rs1, base, words, &cur, cap);
    st |= tri_bind(&c->z0, base, words, &cur, cap);
    st |= tri_bind(&c->z1, base, words, &cur, cap);
    if (st != SRMECH_OK) {
        return SRMECH_ERR_OVERFLOW;
    }
    st = srmech_bigint_set_i64(&c->z0, 0);     /* read-only unit 0 */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_set_i64(&c->z1, 1);     /* read-only unit 1 */
    if (st != SRMECH_OK) { return st; }
    c->scratch = (void *)(base + cur);
    c->scratch_len = (words - cur) * sizeof(uint32_t);
    assert(cur <= words);
    return SRMECH_OK;
}

/* ---- exact-Q helpers (reduce / add / mul) over the context scratch -- */

/* Reduce num/den IN PLACE to lowest terms, positive denominator. den must be
 * nonzero; 0/d normalizes to 0/1. Uses ONLY the reduce-private carriers (g,
 * rem, rs0, rs1) + the scratch tail. (Mirrors poly_q_reduce.) */
static srmech_status_t tri_q_reduce(tri_ctx_t *c, srmech_bigint_t *num,
                                    srmech_bigint_t *den)
{
    srmech_status_t st;
    assert(c != NULL && num != NULL && den != NULL);
    assert(den->sign != 0);
    if (den->sign < 0) {                     /* force positive denominator */
        num->sign = (num->sign == 0) ? 0 : -num->sign;
        den->sign = -den->sign;
    }
    if (srmech_bigint_is_zero(num)) {
        return srmech_bigint_set_i64(den, 1);
    }
    st = srmech_bigint_gcd(&c->g, num, den, c->scratch, c->scratch_len);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_divmod(&c->rs0, &c->rem, num, &c->g,
                              c->scratch, c->scratch_len);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_divmod(&c->rs1, &c->rem, den, &c->g,
                              c->scratch, c->scratch_len);
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(num, &c->rs0);
    if (st != SRMECH_OK) { return st; }
    return srmech_bigint_copy(den, &c->rs1);
}

/* out = a +/- b (exact Q), reduced. sub != 0 selects subtraction. out_* may
 * NOT alias the four input carriers. Uses t0 (cross product). (Mirrors
 * poly_q_add.) */
static srmech_status_t tri_q_add(tri_ctx_t *c, srmech_bigint_t *out_num,
                                 srmech_bigint_t *out_den,
                                 const srmech_bigint_t *an,
                                 const srmech_bigint_t *ad,
                                 const srmech_bigint_t *bn,
                                 const srmech_bigint_t *bd, int sub)
{
    srmech_status_t st;
    assert(c != NULL && out_num != NULL && out_den != NULL);
    assert(an != NULL && ad != NULL && bn != NULL && bd != NULL);
    st = srmech_bigint_mul(&c->t0, an, bd);           /* t0 = an*bd      */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_mul(out_num, bn, ad);          /* out_num = bn*ad */
    if (st != SRMECH_OK) { return st; }
    if (sub) {
        st = srmech_bigint_sub(out_den, &c->t0, out_num);   /* an*bd - bn*ad */
    } else {
        st = srmech_bigint_add(out_den, &c->t0, out_num);   /* an*bd + bn*ad */
    }
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_copy(out_num, out_den);        /* num = combined  */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_mul(out_den, ad, bd);          /* den = ad*bd     */
    if (st != SRMECH_OK) { return st; }
    return tri_q_reduce(c, out_num, out_den);
}

/* out = a * b (exact Q), reduced. out_* may NOT alias the inputs. (Mirrors
 * poly_q_mul.) */
static srmech_status_t tri_q_mul(tri_ctx_t *c, srmech_bigint_t *out_num,
                                 srmech_bigint_t *out_den,
                                 const srmech_bigint_t *an,
                                 const srmech_bigint_t *ad,
                                 const srmech_bigint_t *bn,
                                 const srmech_bigint_t *bd)
{
    srmech_status_t st;
    assert(c != NULL && out_num != NULL && out_den != NULL);
    assert(an != NULL && ad != NULL && bn != NULL && bd != NULL);
    st = srmech_bigint_mul(out_num, an, bn);          /* num = an*bn */
    if (st != SRMECH_OK) { return st; }
    st = srmech_bigint_mul(out_den, ad, bd);          /* den = ad*bd */
    if (st != SRMECH_OK) { return st; }
    return tri_q_reduce(c, out_num, out_den);
}

/* ---- trim + sizing helpers ----------------------------------------- */

/* The trimmed n-run length: drop trailing-zero (high-n-degree) coefficients. A
 * coefficient is zero iff its numerator is zero. */
static size_t tri_trim_len(const srmech_bigint_t *nums, size_t n)
{
    size_t k = n;
    assert(nums != NULL || n == 0u);
    while (k > 0u && srmech_bigint_is_zero(&nums[k - 1u])) {
        k--;
    }
    assert(k <= n);                          /* trim never grows the length */
    return k;
}

/* The largest significant limb count across a CONCATENATED grid's num/den
 * coefficient arrays (`total` coefficients in all). */
static size_t tri_grid_max_limbs(const srmech_bigint_t *nums,
                                 const srmech_bigint_t *dens, size_t total)
{
    size_t k, cl = 1u;
    assert(nums != NULL || total == 0u);
    assert(dens != NULL || total == 0u);
    for (k = 0u; k < total; k++) {
        if (nums[k].n > cl) { cl = nums[k].n; }
        if (dens[k].n > cl) { cl = dens[k].n; }
    }
    return cl;
}

/* The total coefficient count across all cells (sum of nlen[]). */
static size_t tri_n_total(const size_t *nlen, size_t cells)
{
    size_t k, tot = 0u;
    assert(nlen != NULL || cells == 0u);
    for (k = 0u; k < cells; k++) {
        tot += nlen[k];
    }
    assert(k == cells);                      /* the bounded loop ran to the end */
    return tot;
}

/* ---- arena bound --------------------------------------------------- *
 * Each output cell coefficient is an exact-Q combination (sum of products) of
 * input coefficients, reduced after every op. The UNREDUCED intermediate reaches
 * the PRODUCT of input num+den magnitudes accumulated over the longest n-run
 * convolution (`accum_terms` products into one output coefficient). We size each
 * carrier to hold that worst-case product. `coeff_limbs` is the largest input
 * coefficient limb count; `accum_terms` is the convolution depth (the max output
 * n-run length, plus one). (Mirrors poly_cap_for.) */
static size_t tri_cap_for(size_t coeff_limbs, size_t accum_terms)
{
    size_t cl = (coeff_limbs == 0u) ? 1u : coeff_limbs;
    size_t at = (accum_terms == 0u) ? 1u : accum_terms;
    size_t common = cl * at + 2u;            /* common-denominator scale  */
    size_t prod = common * 2u + cl * 2u;     /* unreduced cross-product    */
    size_t cap = prod + 16u;
    assert(cap >= common);
    assert(cap >= cl);
    return cap;
}

/* Bytes the caller hands every srmech_tripoly_* op for inputs of `coeff_limbs`
 * significant limbs per coefficient and a worst-case output n-run of `n_terms`
 * coefficients. Covers TRI_N_CARRIERS carriers of `cap` limbs each, plus a divmod
 * scratch tail (the heaviest scratch is divmod over two `cap`-limb values:
 * 8*cap + 256 is a safe envelope). 8-byte-aligned uint32. (Mirrors
 * srmech_poly_ws_bound.) */
size_t srmech_tripoly_ws_bound(size_t coeff_limbs, size_t n_terms)
{
    size_t cap = tri_cap_for(coeff_limbs, n_terms == 0u ? 1u : n_terms);
    size_t carriers = cap * (size_t)TRI_N_CARRIERS;
    size_t scratch = cap * 8u + 256u;
    size_t words = carriers + scratch;
    assert(cap >= 2u);
    assert(words >= carriers);
    return words * sizeof(uint32_t);
}

/* ---- per-cell n-run kernels ---------------------------------------- */

/* o = a +/- b for two n-runs (lengths na, nb), each cell coefficient exact-Q +
 * reduced; *o_len is the TRIMMED output length. The o arrays hold max(na, nb)
 * coefficients (pre-trim). Missing high-degree terms read as 0/1. */
static srmech_status_t tri_addsub_cell(tri_ctx_t *c,
                                       const srmech_bigint_t *a_n,
                                       const srmech_bigint_t *a_d, size_t na,
                                       const srmech_bigint_t *b_n,
                                       const srmech_bigint_t *b_d, size_t nb,
                                       int sub, srmech_bigint_t *o_n,
                                       srmech_bigint_t *o_d, size_t *o_len)
{
    srmech_status_t st;
    size_t k, m = (na > nb) ? na : nb;
    assert(c != NULL && o_n != NULL && o_d != NULL && o_len != NULL);
    assert(sub == 0 || sub == 1);
    for (k = 0u; k < m; k++) {
        const srmech_bigint_t *an, *ad, *bn, *bd;
        an = (k < na) ? &a_n[k] : &c->z0;  ad = (k < na) ? &a_d[k] : &c->z1;
        bn = (k < nb) ? &b_n[k] : &c->z0;  bd = (k < nb) ? &b_d[k] : &c->z1;
        st = tri_q_add(c, &o_n[k], &o_d[k], an, ad, bn, bd, sub);
        if (st != SRMECH_OK) { return st; }
    }
    *o_len = tri_trim_len(o_n, m);
    return SRMECH_OK;
}

/* o += a * b for two n-runs (a multiply-ACCUMULATE: the output cell o already
 * holds a partial sum of length *o_len, and the product of the two n-run
 * polynomials is added in). o arrays must hold na+nb-1 coefficients (and at least
 * the prior *o_len). *o_len is updated to the trimmed length. */
static srmech_status_t tri_mac_cell(tri_ctx_t *c,
                                    const srmech_bigint_t *a_n,
                                    const srmech_bigint_t *a_d, size_t na,
                                    const srmech_bigint_t *b_n,
                                    const srmech_bigint_t *b_d, size_t nb,
                                    srmech_bigint_t *o_n, srmech_bigint_t *o_d,
                                    size_t *o_len)
{
    srmech_status_t st;
    size_t i, jj, prod_len, new_len;
    assert(c != NULL && o_n != NULL && o_d != NULL && o_len != NULL);
    assert(a_n != NULL || na == 0u);
    if (na == 0u || nb == 0u) { return SRMECH_OK; }
    prod_len = na + nb - 1u;
    new_len = (prod_len > *o_len) ? prod_len : *o_len;
    for (i = *o_len; i < new_len; i++) {     /* extend the accumulator with 0/1 */
        st = srmech_bigint_set_i64(&o_n[i], 0);
        if (st != SRMECH_OK) { return st; }
        st = srmech_bigint_set_i64(&o_d[i], 1);
        if (st != SRMECH_OK) { return st; }
    }
    for (i = 0u; i < na; i++) {
        if (srmech_bigint_is_zero(&a_n[i])) { continue; }
        for (jj = 0u; jj < nb; jj++) {
            if (srmech_bigint_is_zero(&b_n[jj])) { continue; }
            st = tri_q_mul(c, &c->qa_n, &c->qa_d, &a_n[i], &a_d[i],
                           &b_n[jj], &b_d[jj]);            /* term = a_i*b_j */
            if (st != SRMECH_OK) { return st; }
            st = srmech_bigint_copy(&c->qb_n, &o_n[i + jj]);
            if (st != SRMECH_OK) { return st; }
            st = srmech_bigint_copy(&c->qb_d, &o_d[i + jj]);
            if (st != SRMECH_OK) { return st; }
            st = tri_q_add(c, &o_n[i + jj], &o_d[i + jj],
                           &c->qb_n, &c->qb_d, &c->qa_n, &c->qa_d, 0);
            if (st != SRMECH_OK) { return st; }
        }
    }
    *o_len = tri_trim_len(o_n, new_len);
    return SRMECH_OK;
}

/* ---- add / sub ----------------------------------------------------- *
 * The two grids must have the SAME (aj, ak) shape (the caller pre-pads the
 * smaller grid's missing cells to empty n-runs and the smaller j/k extent to the
 * max — mirroring how the Python TriPoly aligns block(d) over the max j-degree
 * and each BiPoly over the max k-degree). Each output cell is the cellwise
 * exact-Q add/sub of the two input cells' n-runs; *out_nlen[cell] gets the
 * trimmed n-run length. */

static srmech_status_t tri_addsub(const srmech_bigint_t *a_n,
                                  const srmech_bigint_t *a_d,
                                  const size_t *a_nlen, size_t cells,
                                  const srmech_bigint_t *b_n,
                                  const srmech_bigint_t *b_d,
                                  const size_t *b_nlen, int sub,
                                  srmech_bigint_t *out_n, srmech_bigint_t *out_d,
                                  size_t *out_nlen, void *ws, size_t ws_len)
{
    tri_ctx_t c;
    srmech_status_t st;
    size_t cell, a_off = 0u, b_off = 0u, o_off = 0u, atot, btot, cl;
    uint32_t cap;
    assert(out_n != NULL && out_d != NULL && out_nlen != NULL);
    assert(sub == 0 || sub == 1);
    atot = tri_n_total(a_nlen, cells);
    btot = tri_n_total(b_nlen, cells);
    cl = tri_grid_max_limbs(a_n, a_d, atot);
    { size_t cb = tri_grid_max_limbs(b_n, b_d, btot); if (cb > cl) { cl = cb; } }
    cap = (uint32_t)tri_cap_for(cl, 2u);
    st = tri_ctx_init(&c, cap, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    for (cell = 0u; cell < cells; cell++) {
        size_t na = a_nlen[cell], nb = b_nlen[cell], olen = 0u;
        st = tri_addsub_cell(&c, &a_n[a_off], &a_d[a_off], na,
                             &b_n[b_off], &b_d[b_off], nb, sub,
                             &out_n[o_off], &out_d[o_off], &olen);
        if (st != SRMECH_OK) { return st; }
        out_nlen[cell] = olen;
        a_off += na;
        b_off += nb;
        o_off += (na > nb) ? na : nb;       /* the pre-trim cell stride */
    }
    return SRMECH_OK;
}

srmech_status_t srmech_tripoly_add(const srmech_bigint_t *a_n,
                                   const srmech_bigint_t *a_d,
                                   const size_t *a_nlen, size_t cells,
                                   const srmech_bigint_t *b_n,
                                   const srmech_bigint_t *b_d,
                                   const size_t *b_nlen,
                                   srmech_bigint_t *out_n,
                                   srmech_bigint_t *out_d, size_t *out_nlen,
                                   void *ws, size_t ws_len)
{
    assert(out_n != NULL && out_d != NULL && out_nlen != NULL);
    assert(a_nlen != NULL || cells == 0u);
    if (out_n == NULL || out_d == NULL || out_nlen == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    return tri_addsub(a_n, a_d, a_nlen, cells, b_n, b_d, b_nlen, 0,
                      out_n, out_d, out_nlen, ws, ws_len);
}

srmech_status_t srmech_tripoly_sub(const srmech_bigint_t *a_n,
                                   const srmech_bigint_t *a_d,
                                   const size_t *a_nlen, size_t cells,
                                   const srmech_bigint_t *b_n,
                                   const srmech_bigint_t *b_d,
                                   const size_t *b_nlen,
                                   srmech_bigint_t *out_n,
                                   srmech_bigint_t *out_d, size_t *out_nlen,
                                   void *ws, size_t ws_len)
{
    assert(out_n != NULL && out_d != NULL && out_nlen != NULL);
    assert(a_nlen != NULL || cells == 0u);
    if (out_n == NULL || out_d == NULL || out_nlen == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    return tri_addsub(a_n, a_d, a_nlen, cells, b_n, b_d, b_nlen, 1,
                      out_n, out_d, out_nlen, ws, ws_len);
}

/* ---- mul (2-D (j,k) convolution; each cell an n-run convolution) --- *
 * Input grids: A is (aj x ak), B is (bj x bk). The product grid is
 * (aj+bj-1) x (ak+bk-1). Output cell (dj, dk) = Σ over (ai,aj_,bi,bj_) with
 * ai+bi == dj, aj_+bj_ == dk of A[ai][aj_] * B[bi][bj_] (an n-run convolution,
 * multiply-accumulated). The caller pre-zeros the output (n_total slots) and
 * passes the per-output-cell n-run capacity in out_nlen[cell] on ENTRY (the
 * caller-sized stride); the op fills + trims each, writing the final trimmed
 * length back into out_nlen[cell]. */

static srmech_status_t tri_mul_body(tri_ctx_t *c,
                                    const srmech_bigint_t *a_n,
                                    const srmech_bigint_t *a_d,
                                    const size_t *a_nlen, size_t aj, size_t ak,
                                    const srmech_bigint_t *b_n,
                                    const srmech_bigint_t *b_d,
                                    const size_t *b_nlen, size_t bj, size_t bk,
                                    srmech_bigint_t *out_n,
                                    srmech_bigint_t *out_d, size_t *out_nlen,
                                    const size_t *out_off, size_t ocols)
{
    srmech_status_t st;
    size_t ai, aj_, bi, bj_;
    assert(c != NULL && out_n != NULL && out_nlen != NULL);
    assert(out_off != NULL);
    for (ai = 0u; ai < aj; ai++) {
        for (aj_ = 0u; aj_ < ak; aj_++) {
            size_t a_cell = ai * ak + aj_, a_o = 0u, t;
            for (t = 0u; t < a_cell; t++) { a_o += a_nlen[t]; }
            for (bi = 0u; bi < bj; bi++) {
                for (bj_ = 0u; bj_ < bk; bj_++) {
                    size_t b_cell = bi * bk + bj_, b_o = 0u, ocell, u;
                    for (u = 0u; u < b_cell; u++) { b_o += b_nlen[u]; }
                    ocell = (ai + bi) * ocols + (aj_ + bj_);
                    st = tri_mac_cell(c, &a_n[a_o], &a_d[a_o], a_nlen[a_cell],
                                      &b_n[b_o], &b_d[b_o], b_nlen[b_cell],
                                      &out_n[out_off[ocell]],
                                      &out_d[out_off[ocell]], &out_nlen[ocell]);
                    if (st != SRMECH_OK) { return st; }
                }
            }
        }
    }
    return SRMECH_OK;
}

srmech_status_t srmech_tripoly_mul(const srmech_bigint_t *a_n,
                                   const srmech_bigint_t *a_d,
                                   const size_t *a_nlen, size_t aj, size_t ak,
                                   const srmech_bigint_t *b_n,
                                   const srmech_bigint_t *b_d,
                                   const size_t *b_nlen, size_t bj, size_t bk,
                                   srmech_bigint_t *out_n,
                                   srmech_bigint_t *out_d, size_t *out_nlen,
                                   const size_t *out_off, size_t ocols,
                                   size_t accum_terms, void *ws, size_t ws_len)
{
    tri_ctx_t c;
    srmech_status_t st;
    size_t acells, bcells, atot, btot, cl;
    uint32_t cap;
    assert(out_n != NULL && out_d != NULL && out_nlen != NULL);
    assert(out_off != NULL);
    if (out_n == NULL || out_d == NULL || out_nlen == NULL || out_off == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (aj == 0u || ak == 0u || bj == 0u || bk == 0u) { return SRMECH_OK; }
    acells = aj * ak;
    bcells = bj * bk;
    atot = tri_n_total(a_nlen, acells);
    btot = tri_n_total(b_nlen, bcells);
    cl = tri_grid_max_limbs(a_n, a_d, atot);
    { size_t cb = tri_grid_max_limbs(b_n, b_d, btot); if (cb > cl) { cl = cb; } }
    cap = (uint32_t)tri_cap_for(cl, accum_terms + 1u);
    st = tri_ctx_init(&c, cap, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    return tri_mul_body(&c, a_n, a_d, a_nlen, aj, ak, b_n, b_d, b_nlen, bj, bk,
                        out_n, out_d, out_nlen, out_off, ocols);
}
