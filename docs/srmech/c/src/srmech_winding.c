/*
 * srmech_winding.c — the One's winding-surface readouts (siona gh#1276; rc137).
 *
 * The winding w lifts SO -> Spin (the double cover). These are the exact
 * INTEGER readouts of the winding TRIAD carried WHOLE by
 * srmech.amsc.cascade.one.One. They do NOT touch the S(sigma,theta) adjoint
 * generator (a separate owed-C item; the winding ops are independent of it).
 * Every op here is exact-integer -> BYTE-IDENTICAL to the Python (no float,
 * in contrast to the numeric srmech_eph_propagate).
 *
 * The chirality is a READOUT of w's binary TOWER via divmod (the Z/2 GRADING
 * KEPT), NOT sigma = w mod 2 (the quotient map that throws the carry away and
 * MELDS w=5 == w=7 == 1). No abs(): sigma is the Class-K pin/sign, and a
 * retrograde winding is the Class-C orientation reversal (-w), computed via
 * defined unsigned wraparound (no INT64_MIN undefined behaviour).
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto)        : OK
 *   - Rule 2 (bounded loops)  : OK — 64 (int64 bit-width)
 *   - Rule 3 (no malloc)      : OK
 *   - Rule 4 (<=60 lines/func): OK
 *   - Rule 5 (>=2 asserts/fn) : OK — arg pointer + post-condition each
 *   - Rule 7 (return-value)   : OK — srmech_status_t throughout
 *   - Rule 10 (warnings clean): OK under -Wall -Wextra -Wpedantic
 *
 * ABI: additive symbols only -> SRMECH_ABI_VERSION stays 3.
 * License: MIT.
 */

#include "srmech.h"

#include <assert.h>
#include <stdint.h>

/* int64 bit-width — the bound for every winding-tower / popcount loop. */
#define SRMECH_WINDING_INT64_BITS 64

/* Population count of |w| — the number of set bits of the Class-K magnitude
 * (no abs(); a retrograde winding negates via defined unsigned wrap). Used by
 * srmech_sigma_effective to grade sigma by the FULL tower (every bit counts),
 * NOT the bare low bit `w mod 2`. */
static srmech_status_t srmech_winding_popcount(int64_t w, int32_t *out)
{
    assert(out != NULL);
    if (out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    uint64_t m = (w >= 0) ? (uint64_t)w : ((uint64_t)0 - (uint64_t)w);
    int32_t count = 0;
    for (int i = 0; i < SRMECH_WINDING_INT64_BITS; i++) {
        count += (int32_t)(m & 1u);
        m >>= 1;
    }
    *out = count;
    assert(*out >= 0 && *out <= SRMECH_WINDING_INT64_BITS);
    return SRMECH_OK;
}

srmech_status_t srmech_winding_tower(int64_t w, uint8_t *bits_out,
                                     int32_t bits_cap, int32_t *n_bits_out)
{
    assert(bits_out != NULL);
    assert(n_bits_out != NULL);
    if (bits_out == NULL || n_bits_out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (bits_cap < 0) {
        return SRMECH_ERR_BAD_INPUT;
    }
    /* Class-K magnitude of the WHOLE winding (no abs()); the tower is over the
     * magnitude, its orientation carried by sigma / sigma_effective. */
    uint64_t m = (w >= 0) ? (uint64_t)w : ((uint64_t)0 - (uint64_t)w);
    int32_t n = 0;
    for (int i = 0; i < SRMECH_WINDING_INT64_BITS; i++) {
        if (m == 0) {
            break;
        }
        if (n >= bits_cap) {
            return SRMECH_ERR_OVERFLOW;
        }
        bits_out[n] = (uint8_t)(m & 1u);   /* divmod(.,2): the grading bit */
        m >>= 1;                            /* divmod(.,2): the retained carry */
        n++;
    }
    *n_bits_out = n;                        /* LSB-first; w=0 -> empty tower */
    assert(n >= 0 && n <= SRMECH_WINDING_INT64_BITS);
    return SRMECH_OK;
}

srmech_status_t srmech_sigma_effective(int32_t sigma, int64_t w0, int64_t w1,
                                       int64_t w2, int32_t *out)
{
    assert(out != NULL);
    if (out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (sigma != 1 && sigma != -1) {
        return SRMECH_ERR_BAD_INPUT;
    }
    int32_t p0 = 0;
    int32_t p1 = 0;
    int32_t p2 = 0;
    srmech_status_t st = srmech_winding_popcount(w0, &p0);
    if (st != SRMECH_OK) {
        return st;
    }
    st = srmech_winding_popcount(w1, &p1);
    if (st != SRMECH_OK) {
        return st;
    }
    st = srmech_winding_popcount(w2, &p2);
    if (st != SRMECH_OK) {
        return st;
    }
    /* sigma modulated by the parity of the FULL popcount over the triad's
     * towers (the anti-collapse: 5 has popcount 2, 7 has popcount 3 -> they
     * are DISTINGUISHED, where bare `w mod 2` would meld them). */
    int32_t total = p0 + p1 + p2;
    *out = ((total & 1) == 0) ? sigma : -sigma;
    assert(*out == 1 || *out == -1);
    return SRMECH_OK;
}

srmech_status_t srmech_spinor_sign(int64_t w0, int64_t w1, int64_t w2,
                                   int32_t *out)
{
    assert(out != NULL);
    if (out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    /* The double-cover sign (-1)^(w0+w1+w2). Parity of the sum = XOR of the
     * three low bits (addition mod 2); the two's-complement low bit equals the
     * Python `w % 2` parity for negative w too. This IS Z/2 on the SIGN (the
     * genuine Spin->SO 2:1 lift), while w stays WHOLE in the winding field. */
    uint64_t parity = ((uint64_t)w0 ^ (uint64_t)w1 ^ (uint64_t)w2) & 1u;
    *out = (parity == 0u) ? 1 : -1;
    assert(*out == 1 || *out == -1);
    return SRMECH_OK;
}

srmech_status_t srmech_unwrapped_phase(int64_t w0, int64_t w1, int64_t w2,
                                       int64_t *turns_out)
{
    assert(turns_out != NULL);
    if (turns_out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    /* The per-metacycle-scale unwrapped-phase TURNS (2*pi*w_k + theta): the
     * full integer turns a theta-only (2π-periodic) object folds away. The
     * turns ARE the winding triad, whole; theta is a pass-through rational the
     * caller carries alongside (pi stays a cascade, never a float here). */
    turns_out[0] = w0;
    turns_out[1] = w1;
    turns_out[2] = w2;
    assert(turns_out[0] == w0 && turns_out[2] == w2);
    return SRMECH_OK;
}
