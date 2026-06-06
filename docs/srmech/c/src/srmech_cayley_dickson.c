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
 * Rosetta peer of srmech.amsc.cascade.cayley_dickson.cd_basis_product —
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
 * License: GPL-3.0-or-later.
 */

#include "srmech.h"

#include <assert.h>

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
    int sign = 1;
    int index = 0;
    int p = i;
    int q = j;
    int cur = dim;
    /* One doubling-step per level; bounded by log2(SRMECH_CD_MAX_DIM). */
    for (int level = 0; level < SRMECH_CD_MAX_LEVELS && cur > 1; level++) {
        int m = cur >> 1;
        int ph = (p >= m) ? 1 : 0;
        int qh = (q >= m) ? 1 : 0;
        int pl = ph ? (p - m) : p;
        int ql = qh ? (q - m) : q;
        int top;
        if (ph == 0 && qh == 0) {            /* (a1 b1) — first half */
            top = 0; p = pl; q = ql;
        } else if (ph == 0 && qh == 1) {     /* (b2 a1) — second half, swap */
            top = 1; p = ql; q = pl;
        } else if (ph == 1 && qh == 0) {     /* (a2 b1*) — second half */
            top = 1; p = pl; q = ql;
            if (ql != 0) { sign = -sign; }   /* conj(b1) sign-flip (Class K) */
        } else {                             /* (- b2* a2) — first half, swap */
            top = 0; p = ql; q = pl;
            if (ql == 0) { sign = -sign; }   /* -conj(b2): flip only when ql==0 */
        }
        if (top != 0) { index += m; }
        cur = m;
    }
    assert(index >= 0 && index < dim);
    assert(sign == 1 || sign == -1);
    *out_index = index;
    *out_sign = sign;
    return SRMECH_OK;
}
