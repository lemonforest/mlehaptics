/*
 * srmech_q8.c — the DISCRETE quaternion group Q8 = {+-1, +-i, +-j, +-k} as
 * 3-bit bytes (0.9.0rc310): the discrete peer of the CONTINUOUS H surface in
 * srmech_quaternion.c. Where srmech_quaternion_* carries float64 quaternions,
 * these ops carry a Q8 element in a single byte and multiply it in pure
 * integer bit-arithmetic — no floats, so no FMA / FP-contraction concern.
 *
 * THE ENCODING. A byte q in {0..7} is q = (sign_bit << 2) | v4_coset, where
 *   v4_coset = q & 3   in {0,1,2,3} = the basis coset {1, i, j, k}
 *   sign_bit = q >> 2  in {0,1}     = the center {+, -}
 * so 0=+1 1=+i 2=+j 3=+k 4=-1 5=-i 6=-j 7=-k, and V4 = q & 3 is the abelian
 * projection (the F380 / in-repo R21 homomorphism pi: Q8 -> V4 = Z2 x Z2).
 *
 * THE PRODUCT. Q8 is the central extension 1 -> Z2 -> Q8 -> V4 -> 1. The
 * product of two signed basis units factors through that extension:
 *   (sa . e_xa)(sb . e_xb) = (sa xor sb xor F[xa][xb]) . e_(xa xor xb)
 * where F[xa][xb] is the cocycle sign bit (F = 1 iff the Cayley-Dickson basis
 * product e_xa . e_xb carries the -1 sign). F is the dim-4 restriction of the
 * SAME cocycle srmech_cd_basis_product computes (verified from Python against
 * srmech_cd_basis_product(4, .,.)): non-abelian (q8_mult(1,2)=3 but
 * q8_mult(2,1)=7), i^2 = j^2 = k^2 = 4 (-1), associative over all 8x8x8, and
 * the abelian projection is exact: (a.b) & 3 == (a&3) xor (b&3) for all a,b.
 *
 * THE CONJUGATE. conj(a) = a for the center (coset 0, self-inverse), else
 * a xor 4 (flip the sign bit of an imaginary coset). It is the group inverse:
 * q8_mult(a, conj(a)) == 0 for every a (verified from Python).
 *
 * HONEST CASCADE SHAPE. q8_mult is a Class-M group bind whose sign is a
 * Class-I Z2 xor of the two center bits and the cocycle bit (never an abs();
 * the sign is a group-encoding bit computed by xor, not a magnitude). conj is
 * a Class-C orientation flip. project_v4 is the Class-I abelian coset read.
 *
 * THREAD/STATE. Pure functions over caller buffers; no shared static state
 * (the cocycle table F is a file-scope const), reentrant. The buffer ops
 * document their out-aliasing contract (each slot i is read-then-written
 * before any later slot needs it, so in-place is safe).
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto / recursion): straight-line code + one bounded loop.
 *   - Rule 2 (bounded loops)       : each loop is bounded by the caller's n.
 *   - Rule 3 (no malloc)           : caller buffers + fixed-size locals only.
 *   - Rule 4 (<=60 lines/func)     : each function is a handful of lines.
 *   - Rule 5 (>=2 asserts/fn)      : domain / pointer pre-conditions.
 *   - Rule 7 (return-value)        : srmech_status_t on the buffer ops.
 *   - Rule 10 (warnings clean)     : -Wall -Wextra -Wpedantic -Werror / /WX.
 *
 * ABI: new INTEGER symbols only (no callback typedef) — SRMECH_ABI_VERSION
 * stays 10 (additive). GENOME_FORMAT_VERSION unchanged (no on-disk format).
 *
 * License: MIT.
 */

#include "srmech.h"

#include <assert.h>
#include <stddef.h>
#include <stdint.h>

/* The Q8 central-extension cocycle sign bits, rows/cols indexed by the V4
 * coset (0=1, 1=i, 2=j, 3=k): F[xa][xb] = 1 iff e_xa . e_xb carries the -1
 * sign. IDENTICAL to srmech_cd_basis_product(4, xa, xb)'s sign (verified). */
static const uint8_t SRMECH_Q8_F[4][4] = {
    {0u, 0u, 0u, 0u},   /* 1 . {1,i,j,k}: identity coset, never signs */
    {0u, 1u, 0u, 1u},   /* i . {1,i,j,k}: i^2=-1, i.k=-j              */
    {0u, 1u, 1u, 0u},   /* j . {1,i,j,k}: j.i=-k, j^2=-1              */
    {0u, 0u, 1u, 1u},   /* k . {1,i,j,k}: k.j=-i, k^2=-1              */
};

uint8_t srmech_q8_mult(uint8_t a, uint8_t b)
{
    assert(a < 8u);
    assert(b < 8u);
    const uint8_t xa = (uint8_t)(a & 3u);
    const uint8_t xb = (uint8_t)(b & 3u);
    const uint8_t sa = (uint8_t)(a >> 2);
    const uint8_t sb = (uint8_t)(b >> 2);
    const uint8_t sign = (uint8_t)(sa ^ sb ^ SRMECH_Q8_F[xa][xb]);
    return (uint8_t)((uint8_t)(sign << 2) | (uint8_t)(xa ^ xb));
}

uint8_t srmech_q8_conjugate(uint8_t a)
{
    assert(a < 8u);
    /* center (coset 0) is self-inverse; an imaginary coset flips its sign bit
     * (a xor 4). The V4 coset is preserved either way (only the center moves). */
    const uint8_t out = (uint8_t)(((a & 3u) == 0u) ? a : (uint8_t)(a ^ 4u));
    assert((out & 3u) == (a & 3u));
    return out;
}

srmech_status_t srmech_q8_bind(const uint8_t *turn, const uint8_t *one,
                               uint32_t n, uint8_t *out)
{
    if (turn == NULL || one == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(turn != NULL && one != NULL);
    assert(out != NULL);
    /* Elementwise Q8 product. `out` MAY alias `turn` and/or `one`: slot i is
     * read from turn[i]/one[i] and written to out[i] before slot i+1 is
     * touched, so an in-place bind (out == turn) is well defined. */
    for (uint32_t i = 0u; i < n; ++i) {
        out[i] = srmech_q8_mult(turn[i], one[i]);
    }
    return SRMECH_OK;
}

srmech_status_t srmech_q8_project_v4(const uint8_t *q, uint32_t n, uint8_t *out)
{
    if (q == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(q != NULL);
    assert(out != NULL);
    /* The abelian projection pi: Q8 -> V4 (drop the center sign bit). `out`
     * MAY alias `q` (each slot is read then written in place). */
    for (uint32_t i = 0u; i < n; ++i) {
        out[i] = (uint8_t)(q[i] & 3u);
    }
    return SRMECH_OK;
}
