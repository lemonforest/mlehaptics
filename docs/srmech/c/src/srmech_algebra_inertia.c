/*
 * srmech_algebra_inertia.c — is an algebra ORDERABLE? Read off its
 * multiplication table, exactly.
 *
 * The R->C rung of the Hurwitz loss ladder (rc349). In an ordered ring every
 * square is >= 0, so an element whose square has a NEGATIVE real part is a
 * certificate that no compatible order exists. x -> Re(x*x) is a QUADRATIC
 * FORM, so the complete answer is its Sylvester inertia signature
 * (n_plus, n_minus, n_zero); the orderability boolean (n_minus == 0) is a
 * strictly weaker shadow of it. This peer returns the signature AND a concrete
 * failing element, so it is an instrument rather than a lookup.
 *
 * IT READS THE TABLE, NEVER A DECLARED DIMENSION. The input is the rank-3
 * structure-constant tensor table[(i*dim + j)*dim + k] = the coefficient of
 * e_k in e_i * e_j; dim is len(table) and nothing else supplies it. So the op
 * runs unchanged on split algebras (split-O answers (5,3,0), NOT the (1,7,0)
 * of O) and on structure tables that are not algebras at all -- inputs where
 * the answer is not forced by the classical theorem.
 *
 * METHOD. Re(x*x) = sum_ij x_i x_j c_ij0, whose symmetric integer Gram is
 * G_ij = c_ij0 + c_ji0 (so x^T G x = 2*Re(x*x); the factor 2 is positive and
 * moves no sign). Symmetric Gaussian elimination over Z then carries the
 * invariant  A_ij = c * (P_i)^T G (P_j)  for one scalar c shared by the live
 * block, of tracked sign s. The pivot-scaled Schur step
 * A_ij <- p*A_ij - A_ik*A_jk keeps every entry an exact integer and multiplies
 * c by 1/p, which is exactly why s flips when the pivot is negative. The true
 * sign at pivot k is s*sign(p) -- that is what is counted, and when negative,
 * column k of P is a genuine witness. Sylvester's law of inertia is what makes
 * the answer independent of every pivot choice taken along the way.
 *
 * Rosetta peer of srmech.cascade.cayley_dickson.inertia_signature --
 * attested bit-exact by tests/test_algebra_inertia_rc349.py.
 *
 * EXACTNESS + THE int64 CEILING. No float, no epsilon, no division except the
 * inertia-invariant positive-gcd strip: the verdict is a comparison of two
 * integer sums. Intermediates grow (measured worst |entry| over random tables:
 * 6 bits at dim 4, 13 at dim 8, 22 at dim 16, 62 at dim 32), so every multiply
 * is overflow-guarded and a genuinely large one returns SRMECH_ERR_OVERFLOW
 * -- never a silent wrap. Python then routes to its ceiling-free bignum path,
 * which is exact at any magnitude. Same contract as srmech_qmat.
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto/recursion): OK
 *   - Rule 2 (bounded loops)    : OK -- every loop bounded by dim <= 256
 *   - Rule 3 (no malloc)        : OK -- caller arena `ws` + caller-owned outs
 *   - Rule 4 (<=60 lines/func)  : OK
 *   - Rule 5 (>=2 asserts/fn)   : OK
 *   - Rule 7 (return-value)     : OK -- srmech_status_t checked at every call
 *   - Rule 10 (warnings clean)  : OK under -Wall -Wextra -Wpedantic
 *
 * License: MIT.
 */

#include "srmech.h"

#include <assert.h>
#include <stddef.h>
#include <stdint.h>

/* The working state, all carved from the caller arena. */
typedef struct {
    int64_t *mat;        /* dim*dim -- the live symmetric integer form   */
    int64_t *cong;       /* dim*dim -- the accumulated congruence matrix */
    int64_t *pivot_col;  /* dim     -- snapshot of mat[.][k]             */
    int64_t *cong_col;   /* dim     -- snapshot of cong[.][k]            */
    int64_t *alive;      /* dim     -- still-live column indices         */
    size_t   n_alive;
    size_t   dim;
} inertia_ctx_t;

/* Class K pin-slot at zero, then Class C re-orientation: the exact magnitude
 * of v as u64. INT64_MIN is representable here because the magnitude leaves
 * the signed domain -- that is the whole reason to compute it in u64, and why
 * this is not a bare abs(). */
static uint64_t inertia_magnitude(int64_t v)
{
    assert(sizeof(uint64_t) == 8u);
    assert(sizeof(int64_t) == 8u);
    if (v < 0) {
        return (uint64_t)(-(v + 1)) + 1u;
    }
    return (uint64_t)v;
}

/* Signed multiply with an overflow guard. Mirrors rational_smul_i64: build the
 * magnitude in u64 (INT64_MIN-safe), check against INT64_MAX, then re-apply
 * the sign. A product that will not fit reports OVERFLOW -- never wraps. */
static srmech_status_t inertia_smul(int64_t a, int64_t b, int64_t *out)
{
    assert(out != NULL);
    assert(sizeof(*out) == 8u);
    if (a == 0 || b == 0) {
        *out = 0;
        return SRMECH_OK;
    }
    uint64_t mag_a = inertia_magnitude(a);
    uint64_t mag_b = inertia_magnitude(b);
    int negative = ((a < 0) != (b < 0));
    uint64_t ceiling = negative ? (uint64_t)INT64_MAX + 1u
                                : (uint64_t)INT64_MAX;
    if (mag_a > ceiling / mag_b) {
        return SRMECH_ERR_OVERFLOW;
    }
    uint64_t product = mag_a * mag_b;
    if (product > ceiling) { return SRMECH_ERR_OVERFLOW; }
    if (negative) {
        *out = (product == (uint64_t)INT64_MAX + 1u)
                   ? INT64_MIN : -(int64_t)product;
    } else {
        *out = (int64_t)product;
    }
    return SRMECH_OK;
}

/* out <- a*b - c*d, every step guarded (the one arithmetic shape the whole
 * elimination is built from: the Schur step, the congruence update, the
 * hyperbolic fold and the Gram load are all instances of it). */
static srmech_status_t inertia_cross(int64_t a, int64_t b, int64_t c,
                                     int64_t d, int64_t *out)
{
    assert(out != NULL);
    assert(sizeof(*out) == 8u);
    int64_t left = 0;
    int64_t right = 0;
    srmech_status_t st = inertia_smul(a, b, &left);
    if (st != SRMECH_OK) { return st; }
    st = inertia_smul(c, d, &right);
    if (st != SRMECH_OK) { return st; }
    if (right < 0 && left > INT64_MAX + right) { return SRMECH_ERR_OVERFLOW; }
    if (right > 0 && left < INT64_MIN + right) { return SRMECH_ERR_OVERFLOW; }
    *out = left - right;
    return SRMECH_OK;
}

/* Binary-free Euclid on u64 magnitudes (the Class-I cyclic gcd). */
static uint64_t inertia_gcd(uint64_t a, uint64_t b)
{
    assert(sizeof(a) == 8u);
    assert(sizeof(b) == 8u);
    while (b != 0u) {
        uint64_t r = a % b;
        a = b;
        b = r;
    }
    return a;
}

/* Divide the live block by its positive gcd. Scaling a symmetric matrix by a
 * POSITIVE rational leaves every eigenvalue's sign alone, so the signature is
 * untouched; this exists purely to hold the exact integers down (and is what
 * keeps dim <= 16 comfortably inside int64). */
static void inertia_strip(inertia_ctx_t *c)
{
    assert(c != NULL);
    assert(c->dim >= 1u);
    uint64_t g = 0u;
    for (size_t a = 0; a < c->n_alive; a++) {
        for (size_t b = 0; b < c->n_alive; b++) {
            size_t i = (size_t)c->alive[a];
            size_t j = (size_t)c->alive[b];
            g = inertia_gcd(g, inertia_magnitude(c->mat[i * c->dim + j]));
        }
    }
    if (g <= 1u) { return; }
    for (size_t a = 0; a < c->n_alive; a++) {
        for (size_t b = 0; b < c->n_alive; b++) {
            size_t i = (size_t)c->alive[a];
            size_t j = (size_t)c->alive[b];
            c->mat[i * c->dim + j] /= (int64_t)g;
        }
    }
}

/* The zero-diagonal escape: e_k <- e_k + e_l as a determinant-1 congruence.
 * Both live diagonals vanish in this branch, so it lands
 * mat[k][k] = 2*mat[k][l] != 0 without disturbing the form. */
static srmech_status_t inertia_hyperbolic(inertia_ctx_t *c, size_t k, size_t l)
{
    assert(c != NULL);
    assert(k != l);
    const size_t dim = c->dim;
    for (size_t r = 0; r < dim; r++) {
        int64_t sum = 0;
        srmech_status_t st = inertia_cross(1, c->cong[r * dim + k],
                                           -1, c->cong[r * dim + l], &sum);
        if (st != SRMECH_OK) { return st; }
        c->cong[r * dim + k] = sum;
    }
    for (size_t t = 0; t < dim; t++) {
        int64_t sum = 0;
        srmech_status_t st = inertia_cross(1, c->mat[k * dim + t],
                                           -1, c->mat[l * dim + t], &sum);
        if (st != SRMECH_OK) { return st; }
        c->mat[k * dim + t] = sum;
    }
    for (size_t r = 0; r < dim; r++) {
        int64_t sum = 0;
        srmech_status_t st = inertia_cross(1, c->mat[r * dim + k],
                                           -1, c->mat[r * dim + l], &sum);
        if (st != SRMECH_OK) { return st; }
        c->mat[r * dim + k] = sum;
    }
    return SRMECH_OK;
}

/* Snapshot column k of mat and cong, then drop k from the live set. */
static void inertia_take_column(inertia_ctx_t *c, size_t slot)
{
    assert(c != NULL);
    assert(slot < c->n_alive);
    const size_t dim = c->dim;
    const size_t k = (size_t)c->alive[slot];
    for (size_t r = 0; r < dim; r++) {
        c->pivot_col[r] = c->mat[r * dim + k];
        c->cong_col[r] = c->cong[r * dim + k];
    }
    for (size_t t = slot + 1; t < c->n_alive; t++) {
        c->alive[t - 1] = c->alive[t];
    }
    c->n_alive -= 1u;
}

/* One pivot-scaled Schur step on the live block, plus the matching congruence
 * update: cong[.][i] <- p*cong[.][i] - mat[i][k]*cong[.][k] and
 * mat[i][j] <- p*mat[i][j] - mat[i][k]*mat[j][k]. Column k is already out of
 * the live set, so the in-place writes cannot alias the snapshots. */
static srmech_status_t inertia_step(inertia_ctx_t *c, int64_t pivot)
{
    assert(c != NULL);
    assert(pivot != 0);
    const size_t dim = c->dim;
    for (size_t a = 0; a < c->n_alive; a++) {
        const size_t i = (size_t)c->alive[a];
        for (size_t r = 0; r < dim; r++) {
            int64_t v = 0;
            srmech_status_t st = inertia_cross(pivot, c->cong[r * dim + i],
                                               c->pivot_col[i], c->cong_col[r],
                                               &v);
            if (st != SRMECH_OK) { return st; }
            c->cong[r * dim + i] = v;
        }
    }
    for (size_t a = 0; a < c->n_alive; a++) {
        const size_t i = (size_t)c->alive[a];
        for (size_t b = 0; b < c->n_alive; b++) {
            const size_t j = (size_t)c->alive[b];
            int64_t v = 0;
            srmech_status_t st = inertia_cross(pivot, c->mat[i * dim + j],
                                               c->pivot_col[i],
                                               c->pivot_col[j], &v);
            if (st != SRMECH_OK) { return st; }
            c->mat[i * dim + j] = v;
        }
    }
    return SRMECH_OK;
}

/* The first live slot carrying a nonzero diagonal entry, or c->n_alive. */
static size_t inertia_find_pivot(const inertia_ctx_t *c)
{
    assert(c != NULL);
    assert(c->dim >= 1u);
    for (size_t a = 0; a < c->n_alive; a++) {
        const size_t i = (size_t)c->alive[a];
        if (c->mat[i * c->dim + i] != 0) { return a; }
    }
    return c->n_alive;
}

/* The first live (k, l), k != l, with mat[k][l] != 0. Returns 1 on success. */
static int inertia_find_offdiag(const inertia_ctx_t *c, size_t *k, size_t *l)
{
    assert(c != NULL);
    assert(k != NULL && l != NULL);
    for (size_t a = 0; a < c->n_alive; a++) {
        for (size_t b = a + 1u; b < c->n_alive; b++) {
            const size_t i = (size_t)c->alive[a];
            const size_t j = (size_t)c->alive[b];
            if (c->mat[i * c->dim + j] != 0) {
                *k = i;
                *l = j;
                return 1;
            }
        }
    }
    return 0;
}

/* Build the exact integer Gram, reading ONLY the k == 0 (real-part) slice of
 * the structure-constant tensor, and seed the congruence accumulator with the
 * identity.
 *
 *   form 0 (TRACE, q(x) = Re(x*x)) : G_ij = c_ij0 + c_ji0
 *   form 1 (NORM,  N(x) = Re(x*x~)): G_ij = s_j*c_ij0 + s_i*c_ji0,
 *                                    s_k = +1 for k == 0 else -1
 *
 * The norm read's conjugation x~ = x_0 e_0 - sum_{i>0} x_i e_i is a NAMED
 * CONVENTION, not something a bare structure tensor determines. Naming the
 * form matters: the literature quotes split-O as (4,4), which is the NORM
 * form; the TRACE form answers (5,3,0) for the same algebra. */
static srmech_status_t inertia_load(inertia_ctx_t *c, const int64_t *table,
                                    int form)
{
    assert(c != NULL);
    assert(table != NULL);
    const size_t dim = c->dim;
    for (size_t i = 0; i < dim; i++) {
        const int64_t si = (form == 0 || i == 0u) ? 1 : -1;
        for (size_t j = 0; j < dim; j++) {
            const int64_t sj = (form == 0 || j == 0u) ? 1 : -1;
            const int64_t a = table[(i * dim + j) * dim];
            const int64_t b = table[(j * dim + i) * dim];
            int64_t left = 0;
            int64_t sum = 0;
            srmech_status_t st = inertia_smul(sj, a, &left);
            if (st != SRMECH_OK) { return st; }
            st = inertia_cross(si, b, -1, left, &sum);
            if (st != SRMECH_OK) { return st; }
            c->mat[i * dim + j] = sum;
            c->cong[i * dim + j] = (i == j) ? 1 : 0;
        }
        c->alive[i] = (int64_t)i;
    }
    c->n_alive = dim;
    return SRMECH_OK;
}

size_t srmech_algebra_inertia_ws_bound(size_t dim)
{
    /* The bound is exact arithmetic over the element width, and the max-dim
     * cap is what keeps 2*dim*dim from overflowing size_t. Both are the
     * preconditions this bound is only correct under. */
    assert(sizeof(int64_t) == 8u);
    assert(SRMECH_ALGEBRA_INERTIA_MAX_DIM >= 1u);
    if (dim < 1u || dim > SRMECH_ALGEBRA_INERTIA_MAX_DIM) { return 0u; }
    const size_t slots = 2u * dim * dim + 3u * dim;
    return slots * sizeof(int64_t) + 2u * sizeof(int64_t);
}

/* Carve the working state out of the caller arena (8-byte-aligned bump). */
static srmech_status_t inertia_carve(inertia_ctx_t *c, void *ws, size_t ws_len)
{
    assert(c != NULL);
    assert(ws != NULL);
    const size_t need = srmech_algebra_inertia_ws_bound(c->dim);
    if (need == 0u || ws_len < need) { return SRMECH_ERR_OVERFLOW; }
    unsigned char *base = (unsigned char *)ws;
    size_t pad = ((size_t)0u - (size_t)((uintptr_t)base)) & 7u;
    int64_t *cur = (int64_t *)(void *)(base + pad);
    c->mat = cur;        cur += c->dim * c->dim;
    c->cong = cur;       cur += c->dim * c->dim;
    c->pivot_col = cur;  cur += c->dim;
    c->cong_col = cur;   cur += c->dim;
    c->alive = cur;
    return SRMECH_OK;
}

/* Divide a witness by the positive gcd of its entries. (lambda*x)^T G (lambda*x)
 * = lambda^2 * x^T G x and lambda^2 > 0, so rescaling cannot change the sign a
 * witness certifies; the primitive representative is the canonical one. */
static void inertia_primitive(int64_t *vec, size_t dim)
{
    assert(vec != NULL);
    assert(dim >= 1u);
    uint64_t g = 0u;
    for (size_t r = 0; r < dim; r++) {
        g = inertia_gcd(g, inertia_magnitude(vec[r]));
    }
    if (g <= 1u) { return; }
    for (size_t r = 0; r < dim; r++) {
        vec[r] /= (int64_t)g;
    }
}

/* The elimination loop proper, split out so the entry point stays inside the
 * JPL 60-line rule. Counts the signature and captures the first witness. */
static srmech_status_t inertia_run(inertia_ctx_t *c, int *n_plus, int *n_minus,
                                   int *n_zero, int *has_witness,
                                   int64_t *out_witness)
{
    assert(c != NULL);
    assert(out_witness != NULL);
    const size_t dim = c->dim;
    int scale_orientation = 1;
    while (c->n_alive > 0u) {
        size_t slot = inertia_find_pivot(c);
        if (slot == c->n_alive) {
            size_t k = 0;
            size_t l = 0;
            if (inertia_find_offdiag(c, &k, &l) == 0) {
                *n_zero += (int)c->n_alive;
                return SRMECH_OK;
            }
            srmech_status_t st = inertia_hyperbolic(c, k, l);
            if (st != SRMECH_OK) { return st; }
            continue;
        }
        const size_t k = (size_t)c->alive[slot];
        const int64_t pivot = c->mat[k * dim + k];
        const int pivot_orientation = (pivot > 0) ? 1 : -1;
        const int true_orientation = scale_orientation * pivot_orientation;
        if (true_orientation > 0) {
            *n_plus += 1;
        } else {
            *n_minus += 1;
            if (*has_witness == 0) {
                for (size_t r = 0; r < dim; r++) {
                    out_witness[r] = c->cong[r * dim + k];
                }
                *has_witness = 1;
            }
        }
        inertia_take_column(c, slot);
        srmech_status_t st = inertia_step(c, pivot);
        if (st != SRMECH_OK) { return st; }
        scale_orientation = true_orientation;
        inertia_strip(c);
    }
    return SRMECH_OK;
}

srmech_status_t srmech_algebra_inertia_signature(const int64_t *table,
                                                 size_t dim, int form,
                                                 void *ws, size_t ws_len,
                                                 int *out_n_plus,
                                                 int *out_n_minus,
                                                 int *out_n_zero,
                                                 int *out_has_witness,
                                                 int64_t *out_witness)
{
    assert(out_n_plus != NULL && out_n_minus != NULL);
    assert(out_n_zero != NULL && out_has_witness != NULL);
    if (table == NULL || ws == NULL || out_n_plus == NULL ||
        out_n_minus == NULL || out_n_zero == NULL ||
        out_has_witness == NULL || out_witness == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (dim < 1u || dim > SRMECH_ALGEBRA_INERTIA_MAX_DIM) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (form != 0 && form != 1) { return SRMECH_ERR_BAD_INPUT; }
    inertia_ctx_t ctx;
    ctx.dim = dim;
    ctx.n_alive = 0u;
    ctx.mat = NULL;
    ctx.cong = NULL;
    ctx.pivot_col = NULL;
    ctx.cong_col = NULL;
    ctx.alive = NULL;
    srmech_status_t st = inertia_carve(&ctx, ws, ws_len);
    if (st != SRMECH_OK) { return st; }
    st = inertia_load(&ctx, table, form);
    if (st != SRMECH_OK) { return st; }
    *out_n_plus = 0;
    *out_n_minus = 0;
    *out_n_zero = 0;
    *out_has_witness = 0;
    for (size_t r = 0; r < dim; r++) { out_witness[r] = 0; }
    st = inertia_run(&ctx, out_n_plus, out_n_minus, out_n_zero,
                     out_has_witness, out_witness);
    if (st != SRMECH_OK) { return st; }
    if (*out_has_witness != 0) {
        inertia_primitive(out_witness, dim);
    }
    return SRMECH_OK;
}
