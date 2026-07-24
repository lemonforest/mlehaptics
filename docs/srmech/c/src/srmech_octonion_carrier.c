/*
 * srmech_octonion_carrier.c — the DISCRETE octonion Moufang loop
 * {+-e0, +-e1, ..., +-e7} as 4-bit bytes (0.9.0rc324): the Cayley-Dickson rung
 * ABOVE the Q8 group in srmech_q8.c, the byte-exact discrete peer of the
 * CONTINUOUS O surface in srmech_octonion.c (that TU carries float64 octonions
 * for the ODFT; THIS one carries a signed basis unit in a single byte and
 * multiplies it in pure integer bit-arithmetic — no floats, so no FMA /
 * FP-contraction concern). Distinct TU (and distinct symbol prefix
 * srmech_oct_*) so it never collides with the float srmech_octonion_* family.
 *
 * THE ENCODING. A byte o in {0..15} is o = (sign_bit << 3) | index, where
 *   index    = o & 7   in {0..7} = the basis unit e0..e7 (the FULL octonion;
 *                                  indices 4..7 are the non-quaternionic units)
 *   sign_bit = o >> 3  in {0,1}  = the center {+, -}
 * so 0=+e0(=+1) ... 7=+e7, 8=-e0(=-1) ... 15=-e7. The 16 values ARE the
 * Moufang loop {+-e0..+-e7}.
 *
 * THE PRODUCT. The signed basis-unit product factors like Q8's central
 * extension, one Cayley-Dickson rung up:
 *   (sa . e_xa)(sb . e_xb) = (sa xor sb xor F[xa][xb]) . e_(xa xor xb)
 * where F[xa][xb] = 1 iff the Cayley-Dickson basis product e_xa . e_xb carries
 * the -1 sign. Rather than hand-enter a 64-entry table (a drift risk),
 * srmech_oct_mult calls the SAME iterative cocycle srmech_cd_basis_product at
 * dim 8 that srmech_q8_mult's F is the dim-4 restriction of — so this carrier
 * cannot diverge from the octonion algebra. The result index is ALWAYS
 * xa xor xb (the Fano orientation lives entirely in the sign).
 *
 * NON-ASSOCIATIVE, by design. Unlike Q8, the octonions are non-associative, but
 * this per-slot carrier holds ONE signed basis unit per slot and the Moufang
 * loop has the inverse property ((x.y).inv(y) == x), so the right-conjugate
 * decouple round-trips byte-exact. Non-associativity bites only for products of
 * >= 3 independent units (the associator/fiber channel a LATER rc reads).
 *
 * THE CONJUGATE. conj(a) = a for the real center (index 0, self-inverse), else
 * a xor 8 (flip an imaginary unit's sign bit). It is the loop inverse:
 * srmech_oct_mult(a, srmech_oct_conjugate(a)) == 0 for every a.
 *
 * HONEST CASCADE SHAPE. srmech_oct_mult is a Class-M loop bind whose sign is a
 * Class-I Z2 xor of the two center bits and the cocycle bit (never an abs();
 * the sign is a group-encoding bit computed by xor). conj is a Class-C
 * orientation flip.
 *
 * THREAD/STATE. Pure functions over caller buffers; no shared static state,
 * reentrant. The buffer op documents its out-aliasing contract (each slot i is
 * read-then-written before any later slot needs it, so in-place is safe).
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto / recursion): straight-line code + one bounded loop
 *     (srmech_cd_basis_product is iterative, not recursive).
 *   - Rule 2 (bounded loops)       : the bind loop is bounded by the caller's n.
 *   - Rule 3 (no malloc)           : caller buffers + fixed-size locals only.
 *   - Rule 4 (<=60 lines/func)     : each function is a handful of lines.
 *   - Rule 5 (>=2 asserts/fn)      : domain / pointer pre-conditions.
 *   - Rule 7 (return-value)        : srmech_status_t on the buffer op; the
 *                                    cocycle status is asserted (inputs masked
 *                                    to a valid dim-8 pair, so it cannot fail).
 *   - Rule 10 (warnings clean)     : -Wall -Wextra -Wpedantic -Werror / /WX.
 *
 * ABI: new INTEGER symbols only (no callback typedef) — SRMECH_ABI_VERSION
 * stays 10 (additive). GENOME_FORMAT_VERSION unchanged (no on-disk format —
 * this is the carrier; the octonion on-disk turn packing is a later rc).
 *
 * License: MIT.
 */

#include "srmech.h"

#include <assert.h>
#include <stddef.h>
#include <stdint.h>

/* The octonion carrier dimension (the dim-8 Cayley-Dickson rung). */
#define SRMECH_OCT_CARRIER_DIM 8

uint8_t srmech_oct_mult(uint8_t a, uint8_t b)
{
    assert(a < 16u);
    assert(b < 16u);
    const int xa = (int)(a & 7u);
    const int xb = (int)(b & 7u);
    int idx = 0;
    int sgn = 1;
    /* The SAME cocycle srmech_q8_mult's F is the dim-4 restriction of — masked
     * inputs are always a valid (dim=8, xa, xb) triple, so the status is an
     * asserted invariant, never a runtime error path. */
    const srmech_status_t st =
        srmech_cd_basis_product(SRMECH_OCT_CARRIER_DIM, xa, xb, &idx, &sgn);
    assert(st == SRMECH_OK);
    assert(idx == (xa ^ xb));
    (void)st;
    const uint8_t sbit =
        (uint8_t)((uint8_t)(a >> 3) ^ (uint8_t)(b >> 3) ^ (sgn < 0 ? 1u : 0u));
    return (uint8_t)((uint8_t)(sbit << 3) | (uint8_t)idx);
}

uint8_t srmech_oct_conjugate(uint8_t a)
{
    assert(a < 16u);
    /* real center (index 0) is self-inverse; an imaginary unit flips its sign
     * bit (a xor 8). The basis index is preserved either way (only the center
     * sign moves). */
    const uint8_t out = (uint8_t)(((a & 7u) == 0u) ? a : (uint8_t)(a ^ 8u));
    assert((out & 7u) == (a & 7u));
    return out;
}

srmech_status_t srmech_oct_bind(const uint8_t *turn, const uint8_t *one,
                                uint32_t n, uint8_t *out)
{
    if (turn == NULL || one == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(turn != NULL && one != NULL);
    assert(out != NULL);
    /* Elementwise octonion product. `out` MAY alias `turn` and/or `one`: slot i
     * is read from turn[i]/one[i] and written to out[i] before slot i+1 is
     * touched, so an in-place bind (out == turn) is well defined. */
    for (uint32_t i = 0u; i < n; ++i) {
        out[i] = srmech_oct_mult(turn[i], one[i]);
    }
    return SRMECH_OK;
}
