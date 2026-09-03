/*
 * srmech_cd_register.c — the GENERAL N-slot Cayley–Dickson address layer in C.
 *
 * Standalone-complete C peer of the general-rung addressable register
 * (Python srmech.cascade.cd_register): the same navigation surface
 * srmech_sedenion.c provides at the hard-coded 16 slots, generalised to any
 * power-of-two dim in [1, SRMECH_CD_MAX_DIM].
 *
 *   - srmech_cd_navmap    : the signed pointer-advance permutation for
 *                           right-multiply-by-e_j over `dim` slots
 *                           (mirror of CDRegister.navmap).
 *   - srmech_cd_navigate  : route a set of occupied (slot, sign) records
 *                           through that permutation, composing the Class-C
 *                           signs (mirror of CDRegister.navigate).
 *   - srmech_cd_navmap_is_signed_permutation : the STRUCTURAL INVARIANT the
 *                           whole addressing mechanism rides on (F1274/F1275) —
 *                           for every direction j, i -> (dest, sign) is a
 *                           bijection on [0, dim) with every sign in {+1,-1}.
 *
 * WHY A GENERAL REGISTER IS SOUND ABOVE THE HURWITZ WALL (F1274 / F1275).
 * Addressing does NOT need the division property. It needs only that a basis
 * product be a SIGNED PERMUTATION: e_i . e_j = +/- e_k. Zero divisors — the
 * thing the Hurwitz boundary introduces at dim 16 and worsens at 32 — are built
 * from SUMS of basis elements (e.g. e1 + e10), never from a single basis pair.
 * The two properties are therefore DISJOINT, and the boundary that destroys
 * composition leaves addressing untouched. srmech_cd_navmap_is_signed_permutation
 * is that premise made CHECKABLE at runtime rather than assumed: a bare-C host
 * can verify its own address layer before trusting it.
 *
 * SCOPE OF THE INVARIANT CHECK, stated so it is not over-read. This function
 * verifies the BIJECTION + sign-domain property of the navmap as computed by
 * the srmech_cd_basis_product cocycle. It does NOT independently re-derive
 * e_i . e_j from a full Cayley–Dickson multiplication — that cross-path check
 * (the cocycle shortcut vs the full product, 4096/4096 at dim 64) lives in the
 * Python test suite, which has an exact-rational cd_mult to check against.
 *
 * The slot bound is the ONLY thing that generalises. Every sign rule, every
 * index rule, and the cocycle itself are shared verbatim with the 16-slot peer
 * via srmech_cd_basis_product — there is no second algebra here.
 *
 * NO MALLOC: the only scratch is a bounded seen[] of SRMECH_CD_MAX_DIM ints
 * (1024 B at the rc298 cap of 256 -- this line said "(256 B)" from rc297, when
 * the cap WAS 64 and the arithmetic held, and stayed unrevised through the
 * rc298 raise; corrected rc464). Nothing here scales quadratically in dim, so
 * this file imposes no new ceiling on SRMECH_CD_MAX_DIM.
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto/recursion): OK — bounded loops only
 *   - Rule 2 (bounded loops)    : OK — <= SRMECH_CD_MAX_DIM
 *   - Rule 3 (no malloc)        : OK — caller arrays + bounded stack scratch
 *   - Rule 4 (<=60 lines/func)  : OK
 *   - Rule 5 (>=2 asserts/fn)   : OK
 *   - Rule 7 (return-value)     : OK — srmech_status_t
 *   - Rule 10 (warnings clean)  : OK under -Wall -Wextra -Wpedantic -Werror
 *
 * License: MIT.
 */

#include "srmech.h"

#include <assert.h>
#include <stdint.h>

/* A power of two in [1, SRMECH_CD_MAX_DIM] — the shared dim gate.
 * The two asserts pin the CAP's own shape: the power-of-two test below is only
 * a meaningful ceiling if the ceiling is itself a positive power of two. If
 * SRMECH_CD_MAX_DIM is ever raised (task `#933`) to a non-power-of-two, this
 * fires rather than silently admitting a dim with no basis table. */
static int cdr_dim_ok(int dim)
{
    assert(SRMECH_CD_MAX_DIM > 0);
    assert(((unsigned)SRMECH_CD_MAX_DIM &
            ((unsigned)SRMECH_CD_MAX_DIM - 1u)) == 0u);
    return (dim >= 1 && dim <= SRMECH_CD_MAX_DIM &&
            ((unsigned)dim & ((unsigned)dim - 1u)) == 0u);
}

srmech_status_t srmech_cd_navmap(int dim, int j, int *out_dest, int *out_sign)
{
    assert(out_dest != NULL);
    assert(out_sign != NULL);
    if (out_dest == NULL || out_sign == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (!cdr_dim_ok(dim) || j < 0 || j >= dim) {
        return SRMECH_ERR_BAD_INPUT;
    }
    for (int i = 0; i < dim; i++) {
        int idx = 0;
        int sign = 1;
        srmech_status_t st = srmech_cd_basis_product(dim, i, j, &idx, &sign);
        if (st != SRMECH_OK) { return st; }
        out_dest[i] = idx;
        out_sign[i] = sign;
    }
    return SRMECH_OK;
}

srmech_status_t srmech_cd_navigate(int dim, int j,
                                   const int *in_slots,
                                   const int *in_signs,
                                   size_t count,
                                   int *out_slots,
                                   int *out_signs)
{
    assert(out_slots != NULL && out_signs != NULL);
    assert(count == 0u || (in_slots != NULL && in_signs != NULL));
    if (out_slots == NULL || out_signs == NULL ||
        (count != 0u && (in_slots == NULL || in_signs == NULL))) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (!cdr_dim_ok(dim) || j < 0 || j >= dim) {
        return SRMECH_ERR_BAD_INPUT;
    }
    for (size_t m = 0; m < count; m++) {
        int s_in = in_slots[m];
        int sgn = in_signs[m];
        if (s_in < 0 || s_in >= dim || (sgn != 1 && sgn != -1)) {
            return SRMECH_ERR_BAD_INPUT;
        }
        int idx = 0;
        int sign = 1;
        srmech_status_t st = srmech_cd_basis_product(dim, s_in, j, &idx, &sign);
        if (st != SRMECH_OK) { return st; }
        out_slots[m] = idx;
        out_signs[m] = sgn * sign;          /* compose the Class-C signs */
    }
    return SRMECH_OK;
}

/* One direction j: is i -> (dest, sign) a bijection on [0,dim) with every sign
 * in {+1,-1}?  `seen` is caller-owned bounded scratch (>= dim ints). */
static srmech_status_t cdr_dir_is_signed_perm(int dim, int j, int *seen,
                                              int *out_ok)
{
    assert(seen != NULL);
    assert(out_ok != NULL);
    for (int i = 0; i < dim; i++) {
        seen[i] = 0;
    }
    for (int i = 0; i < dim; i++) {
        int idx = 0;
        int sign = 1;
        srmech_status_t st = srmech_cd_basis_product(dim, i, j, &idx, &sign);
        if (st != SRMECH_OK) { return st; }
        if (idx < 0 || idx >= dim || (sign != 1 && sign != -1)) {
            *out_ok = 0;                    /* outside the signed-basis domain */
            return SRMECH_OK;
        }
        if (seen[idx] != 0) {
            *out_ok = 0;                    /* collision => not a bijection */
            return SRMECH_OK;
        }
        seen[idx] = 1;
    }
    *out_ok = 1;
    return SRMECH_OK;
}

srmech_status_t srmech_cd_navmap_is_signed_permutation(int dim, int *out_ok)
{
    assert(out_ok != NULL);
    if (out_ok == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (!cdr_dim_ok(dim)) {
        return SRMECH_ERR_BAD_INPUT;      /* out-of-range is a REPORTED error */
    }
    /* rc299: this assert used to sit ABOVE the guard, where it contradicted
     * both the documented contract and the rc298 test that calls this with
     * CD_MAX_DIM*2 expecting SRMECH_ERR_BAD_INPUT — an out-of-range dim cannot
     * be simultaneously "a reported error" and "impossible". With asserts live
     * (any non-NDEBUG build, including the default `make lib`) that aborted the
     * process; CI only stayed green because the wheel build defines NDEBUG and
     * compiles the assert out. Below the guard the bound is genuinely
     * invariant, which is what makes the `seen[]` extent safe to claim. The two
     * sibling entries here already had this shape. */
    assert(dim <= SRMECH_CD_MAX_DIM);
    int seen[SRMECH_CD_MAX_DIM];
    for (int j = 0; j < dim; j++) {
        int ok = 0;
        srmech_status_t st = cdr_dir_is_signed_perm(dim, j, seen, &ok);
        if (st != SRMECH_OK) { return st; }
        if (!ok) {
            *out_ok = 0;                    /* the premise FAILS at this rung */
            return SRMECH_OK;
        }
    }
    *out_ok = 1;
    return SRMECH_OK;
}
