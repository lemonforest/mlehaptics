/*
 * srmech_hdc.c — Class M primitive: HDC binary spatter codes (BSC).
 *
 * Task #217 Phase C1 rc8 — Class M earns its C surface. Completes the
 * 14-class C parity roster (A + C + I + L + J + B + G + H + D + E + F + N
 * + K + M).
 *
 * Per [[user_stance_1d_collapse_to_loe_identity_not_action]]: Class M is
 * the BINDING OPERATION that uncompresses LoE-content along its compression
 * axis. Not "the storage primitive" — the operation that takes a compressed-
 * cascade snippet and binds it into substrate-localised form. Substrate-
 * coupling operation per [[user_stance_identity_not_implementation_discipline]];
 * Class C ∘ Class M composes the full LoE-uncompression kernel.
 *
 * Four BSC operations on byte-buffer hyperdimensional vectors. D bits =
 * 8 * n_bytes. Standard HDC dimension is 1024-10000 bits (n_bytes = 128 -
 * 1250); canonical default per [[reference_loe_plural_canonical]]'s plurality
 * is n_bytes = 128 (D = 1024).
 *
 *   - bind        : component-wise XOR (commutative, associative,
 *                   self-inverse: bind(a, bind(a, b)) = b)
 *   - bundle      : majority across n_vectors (odd-count required;
 *                   sum-and-threshold per bit position)
 *   - permute     : cyclic bit-rotation by rotate_bits (signed; negative
 *                   = rotate other direction)
 *   - similarity  : 1 - 2 * hamming(a,b) / D in [-1, 1]
 *
 * Canonical SSoT per [[feedback_science_is_ssot_not_project]]:
 *   - Kanerva (2009) "Hyperdimensional Computing"
 *     Cognitive Computation 1, 139-159.
 *   - Plate (1995) "Holographic Reduced Representations"
 *     IEEE Trans Neural Networks 6, 623-641.
 *   - Rachkovskij (2001) "Representation and processing of structures..."
 *     Neural Comput Appl 9, 322-345.
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto)        : OK
 *   - Rule 2 (bounded loops)  : OK — loops bounded by n_bytes / n_vectors / D
 *   - Rule 3 (no malloc)      : OK
 *   - Rule 4 (≤60 lines/func) : OK
 *   - Rule 5 (≥2 asserts/fn)  : OK — entry-pointer assert + precondition
 *                              (per [[feedback_jpl_rule_5_two_assert_habit]])
 *   - Rule 7 (return-value)   : OK — srmech_status_t throughout
 *   - Rule 10 (warnings clean): OK
 *
 * License: GPL-3.0-or-later.
 */

#include "srmech.h"

#include <assert.h>
#include <stddef.h>
#include <stdint.h>

/* Popcount lookup table for byte values 0..255. Used by srmech_hdc_similarity
 * and srmech_hdc_bundle. Portable across compilers without relying on
 * __builtin_popcount (GCC/Clang) or __popcnt (MSVC). */
static const uint8_t SRMECH_HDC_POPCOUNT8[256] = {
    0,1,1,2,1,2,2,3,1,2,2,3,2,3,3,4,
    1,2,2,3,2,3,3,4,2,3,3,4,3,4,4,5,
    1,2,2,3,2,3,3,4,2,3,3,4,3,4,4,5,
    2,3,3,4,3,4,4,5,3,4,4,5,4,5,5,6,
    1,2,2,3,2,3,3,4,2,3,3,4,3,4,4,5,
    2,3,3,4,3,4,4,5,3,4,4,5,4,5,5,6,
    2,3,3,4,3,4,4,5,3,4,4,5,4,5,5,6,
    3,4,4,5,4,5,5,6,4,5,5,6,5,6,6,7,
    1,2,2,3,2,3,3,4,2,3,3,4,3,4,4,5,
    2,3,3,4,3,4,4,5,3,4,4,5,4,5,5,6,
    2,3,3,4,3,4,4,5,3,4,4,5,4,5,5,6,
    3,4,4,5,4,5,5,6,4,5,5,6,5,6,6,7,
    2,3,3,4,3,4,4,5,3,4,4,5,4,5,5,6,
    3,4,4,5,4,5,5,6,4,5,5,6,5,6,6,7,
    3,4,4,5,4,5,5,6,4,5,5,6,5,6,6,7,
    4,5,5,6,5,6,6,7,5,6,6,7,6,7,7,8
};

srmech_status_t srmech_hdc_bind(const uint8_t *a,
                                const uint8_t *b,
                                uint32_t       n_bytes,
                                uint8_t       *out)
{
    assert(a != NULL && b != NULL && out != NULL);
    assert(n_bytes > 0);
    if (a == NULL || b == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n_bytes == 0) {
        return SRMECH_ERR_BAD_INPUT;
    }
    for (uint32_t i = 0; i < n_bytes; i++) {
        out[i] = (uint8_t)(a[i] ^ b[i]);
    }
    return SRMECH_OK;
}

srmech_status_t srmech_hdc_bundle(const uint8_t * const *vectors,
                                  uint32_t                n_vectors,
                                  uint32_t                n_bytes,
                                  uint8_t                *out)
{
    assert(vectors != NULL && out != NULL);
    assert(n_vectors > 0 && n_bytes > 0);
    if (vectors == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n_vectors == 0 || n_bytes == 0) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (n_vectors > SRMECH_HDC_MAX_BUNDLE_N) {
        return SRMECH_ERR_OVERFLOW;
    }
    /* BSC bundle requires odd-count for clean majority; reject even
     * (caller can pad with a tie-breaker vector if needed). */
    if ((n_vectors & 1u) == 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    uint32_t threshold = (n_vectors + 1u) / 2u;
    for (uint32_t byte_i = 0; byte_i < n_bytes; byte_i++) {
        uint8_t result = 0;
        for (uint32_t bit = 0; bit < 8; bit++) {
            uint32_t count = 0;
            for (uint32_t v = 0; v < n_vectors; v++) {
                if (vectors[v] == NULL) {
                    return SRMECH_ERR_NULL_ARG;
                }
                count += (uint32_t)((vectors[v][byte_i] >> bit) & 1u);
            }
            if (count >= threshold) {
                result = (uint8_t)(result | (1u << bit));
            }
        }
        out[byte_i] = result;
    }
    return SRMECH_OK;
}

srmech_status_t srmech_hdc_permute(const uint8_t *a,
                                   uint32_t       n_bytes,
                                   int32_t        rotate_bits,
                                   uint8_t       *out)
{
    assert(a != NULL && out != NULL);
    assert(n_bytes > 0);
    if (a == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n_bytes == 0) {
        return SRMECH_ERR_BAD_INPUT;
    }
    uint64_t D = (uint64_t)n_bytes * 8u;
    /* Positive modulo: handle negative rotate via signed-modulo dance. */
    int64_t r = (int64_t)rotate_bits % (int64_t)D;
    if (r < 0) {
        r += (int64_t)D;
    }
    uint64_t eff = (uint64_t)r;
    /* Zero output first. */
    for (uint32_t i = 0; i < n_bytes; i++) {
        out[i] = 0;
    }
    /* Bit-by-bit copy: out[i] = a[(i - eff) mod D]. */
    for (uint64_t i = 0; i < D; i++) {
        uint64_t src_bit_idx = (i + D - eff) % D;
        uint64_t src_byte = src_bit_idx / 8u;
        uint64_t src_bit_in_byte = src_bit_idx % 8u;
        uint8_t  bit_value = (uint8_t)((a[src_byte] >> src_bit_in_byte) & 1u);
        if (bit_value != 0) {
            uint64_t dst_byte = i / 8u;
            uint64_t dst_bit_in_byte = i % 8u;
            out[dst_byte] = (uint8_t)(out[dst_byte] | (1u << dst_bit_in_byte));
        }
    }
    return SRMECH_OK;
}

srmech_status_t srmech_hdc_similarity(const uint8_t *a,
                                      const uint8_t *b,
                                      uint32_t       n_bytes,
                                      double        *out)
{
    assert(a != NULL && b != NULL && out != NULL);
    assert(n_bytes > 0);
    if (a == NULL || b == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n_bytes == 0) {
        return SRMECH_ERR_BAD_INPUT;
    }
    uint64_t hamming = 0;
    for (uint32_t i = 0; i < n_bytes; i++) {
        hamming += (uint64_t)SRMECH_HDC_POPCOUNT8[a[i] ^ b[i]];
    }
    double D = (double)(n_bytes * 8u);
    *out = 1.0 - 2.0 * (double)hamming / D;
    return SRMECH_OK;
}
