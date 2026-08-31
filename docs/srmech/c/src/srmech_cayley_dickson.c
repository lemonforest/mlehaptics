/*
 * srmech_cayley_dickson.c — Cayley-Dickson basis-unit cocycle.
 *
 * The integer structural core of the open-exterior boundary-demonstrator
 * (#915 / MFO §VII.6.23): the product of two unit basis elements
 * e_i * e_j = sign * e_index in the dim-D Cayley-Dickson algebra
 * (R -> C -> H -> O -> S(16) -> ...). The result index is always i XOR j;
 * the sign carries the Fano/orientation structure that, past dim 8, makes the
 * algebra non-division (zero divisors at 16). Integer-only: no float, no libm,
 * no malloc.
 *
 * The Python recursion (cayley_dickson._mult on basis elements) makes exactly
 * one recursive doubling-call per level; this peer unrolls that single chain
 * into a bounded loop (no recursion; JPL Rule 1). At each level the top bit of
 * (p, q) selects which Cayley-Dickson cross-term survives for unit operands,
 * possibly swapping the operands and flipping the sign via the conjugation.
 *
 * Rosetta peer of srmech.cascade.cayley_dickson.cd_basis_product —
 * attested bit-exact by tests/test_cascade_cayley_dickson_parity.py.
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto/recursion): OK — single bounded loop
 *   - Rule 2 (bounded loops)    : OK — <= SRMECH_CD_MAX_LEVELS iterations
 *   - Rule 3 (no malloc)        : OK — caller-owned out params only
 *   - Rule 4 (<=60 lines/func)  : OK
 *   - Rule 5 (>=2 asserts/fn)   : OK
 *   - Rule 7 (return-value)     : OK — srmech_status_t
 *   - Rule 10 (warnings clean)  : OK under -Wall -Wextra -Wpedantic
 *
 * License: MIT.
 */

#include "srmech.h"

#include <assert.h>
#include <stdint.h>

/* log2(dim) for a power-of-two dim in [1, SRMECH_CD_MAX_DIM] — the number of
 * doublings on the ladder, so also the number of gamma parameters. */
static int cd_levels(int dim)
{
    int n = 0;
    int c = dim;
    assert(dim >= 1);
    assert(((unsigned int)dim & ((unsigned int)dim - 1u)) == 0u);
    while (c > 1) { c >>= 1; n++; }
    return n;
}

/* The GAMMA-PARAMETERISED basis-unit cocycle — the single engine behind both
 * srmech_cd_basis_product and srmech_algebra_table (rc352, `#T997`).
 *
 * The generalised Cayley-Dickson doubling is
 *     (a1, a2)(b1, b2) = (a1 b1 + gamma * b2~ a2,  b2 a1 + a2 b1~)
 * with one gamma in {-1, +1} PER DOUBLING. gamma == -1 is the definite ladder
 * srmech ships (R -> C -> H -> O -> S ...); a +1 at any level makes the algebra
 * SPLIT from that level up. `gammas` is in LADDER ORDER — gammas[0] is R->C,
 * gammas[1] is C->H, and so on — and `gammas == NULL` means -1 at every level,
 * which reproduces srmech_cd_basis_product bit-for-bit.
 *
 * The gamma touches EXACTLY ONE branch: the (ph, qh) == (1, 1) cross term,
 * whose first component is gamma * conj(b2) * a2. conj contributes +1 at
 * ql == 0 and -1 otherwise, so the coefficient this level composes in is
 * exactly gamma at ql == 0 and -gamma otherwise — a MULTIPLICATION by the
 * parameter, not a decision about it. Class-K sign composition throughout —
 * no abs, no magnitude.
 *
 * rc462 (`#T1179`): this was written as a two-arm branch on (gamma < 0), a
 * dichotomy standing in for a parameter with three values in its natural
 * domain. gamma == 0 fails (gamma < 0) and took the +1 arm, so the gamma == 0
 * table came back bit-identical to the SPLIT table (MEASURED at dims 2, 4, 8
 * and on the mixed (0, -1) vector, in the Python peer where it is reachable).
 * It was LATENT, never live — cd_check_gammas below refuses gamma == 0 at the
 * only two call sites — but the validator was doing correctness work while
 * presenting as input hygiene. The multiplicative form cannot alias: it IS the
 * coefficient, so gamma == 0 vanishes the cross term and yields sign 0 (the
 * degenerate/dual-number rung), absorbing across levels. On +-1 it is a no-op,
 * VERIFIED over 127 gamma vectors / 299593 cells at dims 1..64, 0 mismatches.
 * The public contract did NOT open: see the sign assert at the tail. */
static srmech_status_t cd_gamma_basis(int dim, const int *gammas, int i, int j,
                                      int *out_index, int *out_sign)
{
    int sign = 1;
    int index = 0;
    int p = i;
    int q = j;
    int cur = dim;
    int nlev = cd_levels(dim);
    assert(out_index != NULL && out_sign != NULL);
    assert(i >= 0 && i < dim && j >= 0 && j < dim);
    /* One doubling-step per level; bounded by log2(SRMECH_CD_MAX_DIM). */
    for (int level = 0; level < SRMECH_CD_MAX_LEVELS && cur > 1; level++) {
        int m = cur >> 1;
        int ph = (p >= m) ? 1 : 0;
        int qh = (q >= m) ? 1 : 0;
        int pl = ph ? (p - m) : p;
        int ql = qh ? (q - m) : q;
        int gpos = nlev - 1 - level;         /* ladder index of THIS doubling */
        int gamma = (gammas == NULL) ? -1 : gammas[gpos];
        int top;
        if (ph == 0 && qh == 0) {            /* (a1 b1) — first half */
            top = 0; p = pl; q = ql;
        } else if (ph == 0 && qh == 1) {     /* (b2 a1) — second half, swap */
            top = 1; p = ql; q = pl;
        } else if (ph == 1 && qh == 0) {     /* (a2 b1*) — second half */
            top = 1; p = pl; q = ql;
            if (ql != 0) { sign = -sign; }   /* conj(b1) sign-flip (Class K) */
        } else {                             /* (gamma b2* a2) — first, swap */
            top = 0; p = ql; q = pl;
            /* The coefficient gamma*conj(b2) contributes, verbatim: gamma at
             * ql == 0, -gamma otherwise. Class-K sign composition (a multiply,
             * not an abs). */
            sign = sign * ((ql == 0) ? gamma : -gamma);
        }
        if (top != 0) { index += m; }
        cur = m;
    }
    assert(index >= 0 && index < dim);
    /* TRIPWIRE, not a redundant restatement (rc462, `#T1179`). The kernel above
     * is correct at gamma == 0 and yields sign 0 there; this assert says that
     * value is UNREACHABLE, because cd_check_gammas still admits only +-1 at
     * both call sites. Open that contract and this fires first, in a debug
     * build, at the one place that then needs revisiting: srmech_algebra_table
     * writes exactly one coefficient per (i, j) cell and calls the table
     * MONOMIAL, and a zero sign makes that cell all-zero. Do not relax this
     * assert without deciding what the table means at a degenerate rung. */
    assert(sign == 1 || sign == -1);
    *out_index = index;
    *out_sign = sign;
    return SRMECH_OK;
}

srmech_status_t srmech_cd_basis_product(int dim, int i, int j,
                                        int *out_index, int *out_sign)
{
    assert(out_index != NULL);
    assert(out_sign != NULL);
    if (out_index == NULL || out_sign == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    /* dim must be a power of two in [1, SRMECH_CD_MAX_DIM]. */
    if (dim < 1 || dim > SRMECH_CD_MAX_DIM ||
        ((unsigned int)dim & ((unsigned int)dim - 1u)) != 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (i < 0 || i >= dim || j < 0 || j >= dim) {
        return SRMECH_ERR_BAD_INPUT;
    }
    /* gammas == NULL is gamma = -1 at every level — the DEFINITE ladder this
     * op has always computed. Not a new convention: the shared engine below
     * reduces to the previous body exactly, verified over every (dim, i, j)
     * up to dim 64 by tests/test_algebra_table_rc352.py. */
    return cd_gamma_basis(dim, NULL, i, j, out_index, out_sign);
}

/* Validate a gammas vector against `dim`: NULL means the definite ladder, and
 * a non-NULL vector must carry exactly log2(dim) entries, each +1 or -1.
 *
 * This is the PUBLIC CONTRACT, not input hygiene (rc462, `#T1179`). The kernel
 * above is defined at gamma == 0 — the degenerate rung — and this function is
 * what keeps that rung out of srmech_algebra_table. Peer of the Python
 * cayley_dickson._normalise_gammas, which refuses the same value. */
static srmech_status_t cd_check_gammas(int dim, const int *gammas,
                                       size_t n_gammas)
{
    size_t k;
    assert(dim >= 1);
    assert(gammas != NULL || n_gammas == 0u);
    if (gammas == NULL) {
        return (n_gammas == 0u) ? SRMECH_OK : SRMECH_ERR_BAD_INPUT;
    }
    if (n_gammas != (size_t)cd_levels(dim)) { return SRMECH_ERR_BAD_INPUT; }
    for (k = 0u; k < n_gammas; k++) {
        if (gammas[k] != 1 && gammas[k] != -1) { return SRMECH_ERR_BAD_INPUT; }
    }
    return SRMECH_OK;
}

srmech_status_t srmech_algebra_table(int dim, const int *gammas,
                                     size_t n_gammas, int64_t *out_table)
{
    size_t d, i, j, cells;
    int idx = 0;
    int sgn = 1;
    srmech_status_t st;
    assert(out_table != NULL);
    assert(gammas != NULL || n_gammas == 0u);
    if (out_table == NULL || (gammas == NULL && n_gammas > 0u)) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (dim < 1 || dim > (int)SRMECH_ALGEBRA_TABLE_MAX_DIM ||
        ((unsigned int)dim & ((unsigned int)dim - 1u)) != 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    st = cd_check_gammas(dim, gammas, n_gammas);
    if (st != SRMECH_OK) { return st; }
    d = (size_t)dim;
    cells = d * d * d;
    for (i = 0u; i < cells; i++) { out_table[i] = 0; }
    for (i = 0u; i < d; i++) {
        for (j = 0u; j < d; j++) {
            st = cd_gamma_basis(dim, gammas, (int)i, (int)j, &idx, &sgn);
            if (st != SRMECH_OK) { return st; }
            /* The table is MONOMIAL by construction: e_i*e_j = sign*e_{i^j},
             * so exactly one of the dim coefficients in cell (i, j) is set. */
            out_table[(i * d + j) * d + (size_t)idx] = (int64_t)sgn;
        }
    }
    return SRMECH_OK;
}

/* ==================================================================
 * Cayley-Dickson loop NAVIGATION (v0.9.0rc158; Qalg TAIL Batch 2).
 * INTEGER-only signed-basis-unit machinery COMPOSED over the cocycle above.
 * A signed unit is (sign, index); its canonical slot in [0, 2*dim) is
 * index for sign +1, index + dim for sign -1.
 * ================================================================== */

/* One signed-unit product (s_a, i_a)*(s_b, i_b) = (out_sign, out_index) via the
 * cocycle (note srmech_cd_basis_product returns (index, sign)). Mirror of the
 * Python cayley_dickson._loop_mult. */
static srmech_status_t cd_loop_mult(int dim, int sa, int ia, int sb, int ib,
                                    int *out_sign, int *out_index)
{
    assert(out_sign != NULL && out_index != NULL);
    assert((sa == 1 || sa == -1) && (sb == 1 || sb == -1));
    int idx = 0;
    int sgn = 1;
    srmech_status_t st = srmech_cd_basis_product(dim, ia, ib, &idx, &sgn);
    if (st != SRMECH_OK) { return st; }
    *out_sign = sa * sb * sgn;
    *out_index = idx;
    return SRMECH_OK;
}

/* The sub-loop fixpoint shared by srmech_cd_closure + srmech_cd_min_generating_
 * set: seed {(+1,e0)} + each (+1,e_g), close under all pairwise products until
 * no new signed unit appears. Fills el_sign[]/el_index[] (caller arrays, length
 * >= cap) with the spanned units; *out_count is the cardinality (<= 2*dim). */
static srmech_status_t cd_closure_impl(int dim, const int *gens, int n_gens,
                                       int *el_sign, int *el_index,
                                       int cap, int *out_count)
{
    assert(el_sign != NULL && el_index != NULL && out_count != NULL);
    assert(dim >= 1 && dim <= SRMECH_CD_MAX_DIM);
    int seen[2 * SRMECH_CD_MAX_DIM];
    for (int s = 0; s < 2 * dim; s++) { seen[s] = 0; }
    if (cap < 1) { return SRMECH_ERR_OVERFLOW; }
    int count = 0;
    el_sign[count] = 1; el_index[count] = 0; seen[0] = 1; count++;
    for (int g = 0; g < n_gens; g++) {
        int gi = gens[g];
        if (gi < 0 || gi >= dim) { return SRMECH_ERR_BAD_INPUT; }
        if (seen[gi] == 0) {
            if (count >= cap) { return SRMECH_ERR_OVERFLOW; }
            seen[gi] = 1;
            el_sign[count] = 1; el_index[count] = gi; count++;
        }
    }
    int changed = 1;
    while (changed != 0) {
        changed = 0;
        int cur = count;
        for (int a = 0; a < cur; a++) {
            for (int b = 0; b < cur; b++) {
                int ps = 1;
                int pidx = 0;
                srmech_status_t st = cd_loop_mult(dim, el_sign[a], el_index[a],
                                                  el_sign[b], el_index[b],
                                                  &ps, &pidx);
                if (st != SRMECH_OK) { return st; }
                int slot = (ps > 0) ? pidx : (pidx + dim);
                if (seen[slot] == 0) {
                    if (count >= cap) { return SRMECH_ERR_OVERFLOW; }
                    seen[slot] = 1;
                    el_sign[count] = ps; el_index[count] = pidx; count++;
                    changed = 1;
                }
            }
        }
    }
    *out_count = count;
    return SRMECH_OK;
}

srmech_status_t srmech_cd_closure(int dim, const int *gen_idxs, size_t n_gens,
                                  int *out_signs, int *out_indices,
                                  size_t out_cap, size_t *out_count)
{
    assert(out_signs != NULL && out_indices != NULL);
    assert(out_count != NULL);
    if (out_signs == NULL || out_indices == NULL || out_count == NULL ||
        (gen_idxs == NULL && n_gens > 0)) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (dim < 1 || dim > SRMECH_CD_MAX_DIM ||
        ((unsigned int)dim & ((unsigned int)dim - 1u)) != 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (n_gens > (size_t)(2 * SRMECH_CD_MAX_DIM)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    int cap = (out_cap > (size_t)(2 * SRMECH_CD_MAX_DIM))
                  ? (2 * SRMECH_CD_MAX_DIM) : (int)out_cap;
    int cnt = 0;
    srmech_status_t st = cd_closure_impl(dim, gen_idxs, (int)n_gens,
                                         out_signs, out_indices, cap, &cnt);
    if (st != SRMECH_OK) { return st; }
    *out_count = (size_t)cnt;
    return SRMECH_OK;
}

srmech_status_t srmech_cd_left_orbit(int dim, int start_idx, int gen_idx,
                                     int *out_signs, int *out_indices,
                                     size_t out_cap, size_t *out_count)
{
    assert(out_signs != NULL && out_indices != NULL);
    assert(out_count != NULL);
    if (out_signs == NULL || out_indices == NULL || out_count == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (dim < 1 || dim > SRMECH_CD_MAX_DIM ||
        ((unsigned int)dim & ((unsigned int)dim - 1u)) != 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (start_idx < 0 || start_idx >= dim || gen_idx < 0 || gen_idx >= dim) {
        return SRMECH_ERR_BAD_INPUT;
    }
    int seen[2 * SRMECH_CD_MAX_DIM];
    for (int s = 0; s < 2 * dim; s++) { seen[s] = 0; }
    int cur_sign = 1;
    int cur_index = start_idx;
    int count = 0;
    /* At most 2*dim distinct signed units -> the cycle closes within one over-
     * bound iteration (JPL Rule 2 explicit bound). */
    for (int step = 0; step < 2 * dim + 1; step++) {
        int slot = (cur_sign > 0) ? cur_index : (cur_index + dim);
        if (seen[slot] != 0) { break; }
        if ((size_t)count >= out_cap) { return SRMECH_ERR_OVERFLOW; }
        seen[slot] = 1;
        out_signs[count] = cur_sign;
        out_indices[count] = cur_index;
        count++;
        int ns = 1;
        int ni = 0;
        srmech_status_t st = cd_loop_mult(dim, 1, gen_idx, cur_sign, cur_index,
                                          &ns, &ni);
        if (st != SRMECH_OK) { return st; }
        cur_sign = ns;
        cur_index = ni;
    }
    *out_count = (size_t)count;
    return SRMECH_OK;
}

/* Advance the ascending k-combination odometer c[0..k-1] over [0, n); returns 1
 * if advanced, 0 if the last combination was already reached. */
static int cd_next_combination(int *c, int k, int n)
{
    assert(c != NULL);
    assert(k >= 1 && n >= k);
    int i = k - 1;
    while (i >= 0 && c[i] == n - k + i) { i--; }
    if (i < 0) { return 0; }
    c[i]++;
    for (int j = i + 1; j < k; j++) { c[j] = c[j - 1] + 1; }
    return 1;
}

/* Does the k-subset `gens` span the full loop (closure cardinality == full)? */
static srmech_status_t cd_subset_spans(int dim, const int *gens, int k,
                                       int full, int *out_spans)
{
    assert(out_spans != NULL);
    assert(dim >= 1 && k >= 1);
    int es[2 * SRMECH_CD_MAX_DIM];
    int ei[2 * SRMECH_CD_MAX_DIM];
    int cnt = 0;
    srmech_status_t st = cd_closure_impl(dim, gens, k, es, ei,
                                         2 * SRMECH_CD_MAX_DIM, &cnt);
    if (st != SRMECH_OK) { return st; }
    *out_spans = (cnt == full) ? 1 : 0;
    return SRMECH_OK;
}

/* De-duplicate unit_idxs preserving order, validating each in [0, dim). */
static srmech_status_t cd_dedup_units(int dim, const int *unit_idxs,
                                      size_t n_units, int *units, int *out_nu)
{
    assert(units != NULL && out_nu != NULL);
    assert(dim >= 1 && dim <= SRMECH_CD_MAX_DIM);
    int nu = 0;
    for (size_t t = 0; t < n_units; t++) {
        int u = unit_idxs[t];
        if (u < 0 || u >= dim) { return SRMECH_ERR_BAD_INPUT; }
        int dup = 0;
        for (int e = 0; e < nu; e++) { if (units[e] == u) { dup = 1; } }
        if (dup == 0) {
            if (nu >= SRMECH_CD_MAX_DIM) { return SRMECH_ERR_OVERFLOW; }
            units[nu] = u;
            nu++;
        }
    }
    *out_nu = nu;
    return SRMECH_OK;
}

srmech_status_t srmech_cd_min_generating_set(int dim, const int *unit_idxs,
                                             size_t n_units, int *out_k)
{
    assert(out_k != NULL);
    assert(unit_idxs != NULL || n_units == 0);
    if (out_k == NULL || (unit_idxs == NULL && n_units > 0)) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (dim < 1 || dim > SRMECH_CD_MAX_DIM ||
        ((unsigned int)dim & ((unsigned int)dim - 1u)) != 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    int units[SRMECH_CD_MAX_DIM];
    int nu = 0;
    srmech_status_t st = cd_dedup_units(dim, unit_idxs, n_units, units, &nu);
    if (st != SRMECH_OK) { return st; }
    if (nu > SRMECH_CD_MGS_MAX_UNITS) { return SRMECH_ERR_OVERFLOW; }
    int full = 2 * dim;
    int subset[SRMECH_CD_MAX_DIM];
    int sub_gens[SRMECH_CD_MAX_DIM];
    long budget = SRMECH_CD_MGS_MAX_SUBSETS;
    for (int k = 1; k <= nu; k++) {
        for (int i = 0; i < k; i++) { subset[i] = i; }
        int more = 1;
        while (more != 0) {
            budget--;
            if (budget < 0) { return SRMECH_ERR_OVERFLOW; }
            for (int i = 0; i < k; i++) { sub_gens[i] = units[subset[i]]; }
            int spans = 0;
            st = cd_subset_spans(dim, sub_gens, k, full, &spans);
            if (st != SRMECH_OK) { return st; }
            if (spans != 0) { *out_k = k; return SRMECH_OK; }
            more = cd_next_combination(subset, k, nu);
        }
    }
    *out_k = 0;                                  /* no spanning subset */
    return SRMECH_OK;
}

/* (rc395, task #T1000) cd_pair_product_is_zero + srmech_cd_zero_divisor_witness
 * were REMOVED here: the dedicated dim-16 brute-force export is subsumed by the
 * dim-general Python cd_zero_divisor_witness / cd_zero_divisor_witnesses, a
 * composition_of_c over the GF(2) gf_rref + cd_basis_product. The removal bumped
 * SRMECH_ABI_VERSION 10 -> 11 (see c/include/srmech.h). */
