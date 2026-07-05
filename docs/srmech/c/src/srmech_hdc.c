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
 * License: MIT.
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
    /* No n_vectors cap: the count accumulator is uint32 and the vectors are
     * caller-resident, so the bound is the caller's RAM (standalone-complete). */
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

/* hdc_hamming(a, b, n_bytes, out): the EXACT integer bit-Hamming distance — the
 * count of differing BITS across the two BSC byte buffers (popcount of the XOR),
 * the F868 stay-rational recall key BEFORE the float divide (UPSTREAM §61).
 * similarity = 1 - 2*hamming/D with D = 8*n_bytes; collapse to a double only at
 * the display boundary, in srmech_hdc_similarity. Additive symbol — no ABI bump. */
srmech_status_t srmech_hdc_hamming(const uint8_t *a,
                                   const uint8_t *b,
                                   uint32_t       n_bytes,
                                   uint32_t      *out)
{
    assert(a != NULL && b != NULL && out != NULL);
    assert(n_bytes > 0);
    if (a == NULL || b == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n_bytes == 0) {
        return SRMECH_ERR_BAD_INPUT;
    }
    uint32_t hamming = 0;
    for (uint32_t i = 0; i < n_bytes; i++) {
        hamming += (uint32_t)SRMECH_HDC_POPCOUNT8[a[i] ^ b[i]];
    }
    *out = hamming;
    return SRMECH_OK;
}

/* hdc_similarity = the F868 display-boundary collapse of the exact bit-Hamming
 * distance: 1 - 2*hamming/D in [-1, 1], D = 8*n_bytes. Composes over
 * srmech_hdc_hamming so the integer key and the float view share one definition. */
srmech_status_t srmech_hdc_similarity(const uint8_t *a,
                                      const uint8_t *b,
                                      uint32_t       n_bytes,
                                      double        *out)
{
    assert(out != NULL);
    assert(n_bytes > 0);
    if (out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    uint32_t hamming = 0;
    srmech_status_t st = srmech_hdc_hamming(a, b, n_bytes, &hamming);
    if (st != SRMECH_OK) {
        return st;
    }
    double D = (double)(n_bytes * 8u);
    *out = 1.0 - 2.0 * (double)hamming / D;
    return SRMECH_OK;
}

/* hdc_bundle_with_ties(vectors, n_vectors, n_bytes): bitwise majority across ANY
 * number of BSC vectors, with the tie state surfaced explicitly (rbs_nn Note 1).
 * Unlike srmech_hdc_bundle (odd-count only), this accepts ANY n_vectors:
 *   - out_majority bit = 1 where STRICTLY more than half the inputs are set (a
 *     tie -> 0; for odd n_vectors this byte equals srmech_hdc_bundle exactly);
 *   - out_ties bit = 1 where the set / unset counts are EXACTLY equal (only
 *     possible for even n_vectors), else 0.
 * A tie is a Class-K event (the bundle accumulator crosses zero); counts only,
 * no abs. No n_vectors cap -- bound is the caller's RAM. Additive symbol -- no
 * ABI bump. */
srmech_status_t srmech_hdc_bundle_with_ties(const uint8_t * const *vectors,
                                            uint32_t                n_vectors,
                                            uint32_t                n_bytes,
                                            uint8_t                *out_majority,
                                            uint8_t                *out_ties)
{
    assert(vectors != NULL && out_majority != NULL && out_ties != NULL);
    assert(n_vectors > 0 && n_bytes > 0);
    if (vectors == NULL || out_majority == NULL || out_ties == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n_vectors == 0 || n_bytes == 0) {
        return SRMECH_ERR_BAD_INPUT;
    }
    for (uint32_t byte_i = 0; byte_i < n_bytes; byte_i++) {
        uint8_t maj = 0;
        uint8_t tie = 0;
        for (uint32_t bit = 0; bit < 8; bit++) {
            uint32_t count = 0;
            for (uint32_t v = 0; v < n_vectors; v++) {
                if (vectors[v] == NULL) {
                    return SRMECH_ERR_NULL_ARG;
                }
                count += (uint32_t)((vectors[v][byte_i] >> bit) & 1u);
            }
            uint32_t two = count * 2u;              /* strict-majority test */
            if (two > n_vectors) {
                maj = (uint8_t)(maj | (1u << bit));
            } else if (two == n_vectors) {          /* exact tie: Class-K event */
                tie = (uint8_t)(tie | (1u << bit));
            }
        }
        out_majority[byte_i] = maj;
        out_ties[byte_i] = tie;
    }
    return SRMECH_OK;
}

/* ------------------------------------------------------------------ *
 * Class M — polar {-1, 0, +1} variant (v0.4.3rc1)
 *
 * int8 hypervectors with elements in {-1, 0, +1}; 0 is the absorbing
 * dead-band (Class M ∘ Class K). bind = multiplicative sign-product
 * (0 absorbing); bundle = sticky majority (ties → 0). No ABI bump.
 * ------------------------------------------------------------------ */

srmech_status_t srmech_polar_bind(const int8_t *a,
                                  const int8_t *b,
                                  uint32_t      n,
                                  int8_t       *out)
{
    assert(a != NULL && b != NULL && out != NULL);
    assert(n > 0);
    if (a == NULL || b == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n == 0) {
        return SRMECH_ERR_BAD_INPUT;
    }
    for (uint32_t i = 0; i < n; i++) {
        if (a[i] < -1 || a[i] > 1 || b[i] < -1 || b[i] > 1) {
            return SRMECH_ERR_BAD_INPUT;
        }
        out[i] = (int8_t)(a[i] * b[i]);  /* 0 absorbing: 0 * x = 0 */
    }
    return SRMECH_OK;
}

srmech_status_t srmech_polar_bundle(const int8_t * const *vectors,
                                    uint32_t              n_vectors,
                                    uint32_t              n,
                                    int8_t               *out)
{
    assert(vectors != NULL && out != NULL);
    assert(n_vectors > 0 && n > 0);
    if (vectors == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n_vectors == 0 || n == 0) {
        return SRMECH_ERR_BAD_INPUT;
    }
    /* No n_vectors cap: the sticky-majority accumulator is int32 and the
     * vectors are caller-resident — bound is caller RAM (standalone-complete). */
    for (uint32_t i = 0; i < n; i++) {
        int32_t sum = 0;
        for (uint32_t v = 0; v < n_vectors; v++) {
            if (vectors[v] == NULL) {
                return SRMECH_ERR_NULL_ARG;
            }
            int8_t e = vectors[v][i];
            if (e < -1 || e > 1) {
                return SRMECH_ERR_BAD_INPUT;
            }
            sum += e;
        }
        /* sign(sum): +1 / 0 / -1 — ties (sum == 0) resolve to 0. */
        out[i] = (int8_t)((sum > 0) - (sum < 0));
    }
    return SRMECH_OK;
}

srmech_status_t srmech_polar_similarity(const int8_t *a,
                                        const int8_t *b,
                                        uint32_t      n,
                                        int32_t       skip_zero,
                                        double       *out)
{
    assert(a != NULL && b != NULL && out != NULL);
    assert(n > 0);
    if (a == NULL || b == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n == 0) {
        return SRMECH_ERR_BAD_INPUT;
    }
    uint32_t matches = 0;
    uint32_t denom = 0;
    for (uint32_t i = 0; i < n; i++) {
        if (a[i] < -1 || a[i] > 1 || b[i] < -1 || b[i] > 1) {
            return SRMECH_ERR_BAD_INPUT;
        }
        if (skip_zero != 0 && (a[i] == 0 || b[i] == 0)) {
            continue;
        }
        denom++;
        if (a[i] == b[i]) {
            matches++;
        }
    }
    *out = (denom == 0) ? 0.0 : (double)matches / (double)denom;
    return SRMECH_OK;
}

srmech_status_t srmech_polar_density(const int8_t *v,
                                     uint32_t      n,
                                     double       *out)
{
    assert(v != NULL && out != NULL);
    assert(n > 0);
    if (v == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n == 0) {
        return SRMECH_ERR_BAD_INPUT;
    }
    uint32_t nz = 0;
    for (uint32_t i = 0; i < n; i++) {
        if (v[i] < -1 || v[i] > 1) {
            return SRMECH_ERR_BAD_INPUT;
        }
        if (v[i] != 0) {
            nz++;
        }
    }
    *out = (double)nz / (double)n;
    return SRMECH_OK;
}

/* ------------------------------------------------------------------ *
 * Class M — Klein-4 {0,1,2,3} variant (v0.4.3rc2)
 *
 * Rank-2 abelian Class M over (F₂)² = Z₂×Z₂. uint8 elements in
 * {0,1,2,3}; bind = component-wise XOR; bundle = per-bit majority
 * (ties → 0). No ABI bump.
 * ------------------------------------------------------------------ */

srmech_status_t srmech_klein4_bind(const uint8_t *a,
                                   const uint8_t *b,
                                   uint32_t       n,
                                   uint8_t       *out)
{
    assert(a != NULL && b != NULL && out != NULL);
    assert(n > 0);
    if (a == NULL || b == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n == 0) {
        return SRMECH_ERR_BAD_INPUT;
    }
    for (uint32_t i = 0; i < n; i++) {
        if (a[i] > 3u || b[i] > 3u) {
            return SRMECH_ERR_BAD_INPUT;
        }
        out[i] = (uint8_t)(a[i] ^ b[i]);  /* (F2)^2 XOR */
    }
    return SRMECH_OK;
}

srmech_status_t srmech_klein4_phase_key(uint32_t  D,
                                        uint32_t  start,
                                        uint32_t  width,
                                        uint8_t   elem,
                                        uint8_t  *out)
{
    /* §59 / F861: the V4 code `elem` on the circular slot-window
     * [start, start+width) mod D, identity (0) elsewhere — the population-code
     * continuous-phase key. No caps: bound is the caller's `out` of length D. */
    assert(out != NULL);
    assert(D > 0u);
    if (out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (D == 0u || start >= D || width > D || elem > 3u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    for (uint32_t i = 0; i < D; i++) {
        out[i] = 0u;
    }
    for (uint32_t j = 0; j < width; j++) {
        out[(start + j) % D] = elem;  /* circular slot window */
    }
    return SRMECH_OK;
}

srmech_status_t srmech_klein4_chunk_resolve(const uint8_t *chunks,
                                            uint32_t       n_chunks,
                                            const uint8_t *key,
                                            uint32_t       D,
                                            const uint8_t *candidates,
                                            uint32_t       n_candidates,
                                            uint32_t      *out_counts)
{
    /* §58 / F837: max-resonance read over a capacity-bounded chunk-set. For
     * each candidate, out_counts[j] = MAX over chunks of the integer match-
     * count between (chunk XOR key) and the candidate — the F868 stay-rational
     * recall key before the /D divide. No caps: bound is the caller's arrays. */
    assert(chunks != NULL && key != NULL && candidates != NULL);
    assert(out_counts != NULL && D > 0u && n_chunks > 0u && n_candidates > 0u);
    if (chunks == NULL || key == NULL || candidates == NULL
            || out_counts == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (D == 0u || n_chunks == 0u || n_candidates == 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    for (uint32_t j = 0; j < n_candidates; j++) {
        const uint8_t *cand = candidates + (size_t)j * D;
        uint32_t best = 0u;
        for (uint32_t i = 0; i < n_chunks; i++) {
            const uint8_t *chunk = chunks + (size_t)i * D;
            uint32_t mc = 0u;
            for (uint32_t p = 0; p < D; p++) {
                if ((uint8_t)(chunk[p] ^ key[p]) == cand[p]) {
                    mc++;
                }
            }
            if (mc > best) {
                best = mc;
            }
        }
        out_counts[j] = best;
    }
    return SRMECH_OK;
}

srmech_status_t srmech_klein4_bundle(const uint8_t * const *vectors,
                                     uint32_t               n_vectors,
                                     uint32_t               n,
                                     uint8_t               *out)
{
    assert(vectors != NULL && out != NULL);
    assert(n_vectors > 0 && n > 0);
    if (vectors == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n_vectors == 0 || n == 0) {
        return SRMECH_ERR_BAD_INPUT;
    }
    /* No n_vectors cap: the per-bit 1-counts are uint32 and the vectors are
     * caller-resident — bound is caller RAM (standalone-complete). */
    uint32_t half = n_vectors / 2u;
    for (uint32_t i = 0; i < n; i++) {
        uint32_t bit0 = 0;
        uint32_t bit1 = 0;
        for (uint32_t v = 0; v < n_vectors; v++) {
            if (vectors[v] == NULL) {
                return SRMECH_ERR_NULL_ARG;
            }
            uint8_t e = vectors[v][i];
            if (e > 3u) {
                return SRMECH_ERR_BAD_INPUT;
            }
            bit0 += (uint32_t)(e & 1u);
            bit1 += (uint32_t)((e >> 1) & 1u);
        }
        /* majority per bit; exact tie (== half) resolves to 0. */
        uint8_t r0 = (bit0 > half) ? 1u : 0u;
        uint8_t r1 = (bit1 > half) ? 1u : 0u;
        out[i] = (uint8_t)((r1 << 1) | r0);
    }
    return SRMECH_OK;
}

/* klein4_match_count(a, b, n, out): the EXACT integer count of coordinates
 * where a[i] == b[i] — the Class-M recall-ranking key BEFORE the float divide
 * (UPSTREAM §61; F868 stay-rational: similarity = match_count / n is an exact
 * rational, so the integer count is what the kernel computes; collapse to a
 * double only at the display boundary, in srmech_klein4_similarity). Both
 * buffers carry V4 tokens in {0,1,2,3}; out of range -> ERR_BAD_INPUT. */
srmech_status_t srmech_klein4_match_count(const uint8_t *a,
                                          const uint8_t *b,
                                          uint32_t       n,
                                          uint32_t      *out)
{
    assert(a != NULL && b != NULL && out != NULL);
    assert(n > 0);
    if (a == NULL || b == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n == 0) {
        return SRMECH_ERR_BAD_INPUT;
    }
    uint32_t matches = 0;
    for (uint32_t i = 0; i < n; i++) {
        if (a[i] > 3u || b[i] > 3u) {
            return SRMECH_ERR_BAD_INPUT;
        }
        if (a[i] == b[i]) {
            matches++;
        }
    }
    *out = matches;
    return SRMECH_OK;
}

/* klein4_similarity = the F868 display-boundary collapse of the exact
 * match_count: count / n as a double. Composes over srmech_klein4_match_count
 * so the integer key and the float view share one definition. */
srmech_status_t srmech_klein4_similarity(const uint8_t *a,
                                         const uint8_t *b,
                                         uint32_t       n,
                                         double        *out)
{
    assert(out != NULL);
    assert(n > 0);
    if (out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    uint32_t matches = 0;
    srmech_status_t st = srmech_klein4_match_count(a, b, n, &matches);
    if (st != SRMECH_OK) {
        return st;
    }
    *out = (double)matches / (double)n;
    return SRMECH_OK;
}

/* klein4_triality_cycle(in, n, inverse, out): the order-3 S3 = Aut(V4)
 * cycle of the three non-identity involutions iw7(1) -> g5(2) -> CPT(3) ->
 * iw7(1), identity(0) fixed; the V4-carrier image of the so(8) 8v->8s->8c
 * triality. inverse != 0 applies the reverse 3-cycle (T^2 = T^-1). Class I
 * (cyclic order-3 relabel; no sign). Out of {0,1,2,3} -> ERR_BAD_INPUT. */
srmech_status_t srmech_klein4_triality_cycle(const uint8_t *in,
                                             uint32_t       n,
                                             int            inverse,
                                             uint8_t       *out)
{
    static const uint8_t fwd[4] = {0u, 2u, 3u, 1u};
    static const uint8_t inv[4] = {0u, 3u, 1u, 2u};
    const uint8_t *table = (inverse != 0) ? inv : fwd;
    assert(in != NULL && out != NULL);
    assert(n > 0);
    if (in == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n == 0) {
        return SRMECH_ERR_BAD_INPUT;
    }
    for (uint32_t i = 0; i < n; i++) {
        if (in[i] > 3u) {
            return SRMECH_ERR_BAD_INPUT;
        }
        out[i] = table[in[i]];
    }
    return SRMECH_OK;
}

/* klein4_bundle_accumulate(acc, v, dim): fold ONE Klein-4 vector v (dim bytes,
 * each in {0..3}) into the fixed-width accumulator acc — the STREAMING form of
 * srmech_klein4_bundle (UPSTREAM §50; F758). The batch bundle needs every vector
 * resident; this folds one at a time, so a holographic store never materialises
 * its inputs and stays fixed-width. acc is (1 + 2*dim) uint32: acc[0] = n (count
 * of folded vectors), acc[1 .. dim] = per-coordinate 1-counts of bit 0, and
 * acc[1+dim .. 2*dim] = 1-counts of bit 1. The CALLER owns acc — its width is the
 * architecture (1 + 2*dim uint32), no compiled-in cap. Class M (HDC superposition
 * tally); no abs(). Out-of-range element -> SRMECH_ERR_BAD_INPUT. */
srmech_status_t srmech_klein4_bundle_accumulate(uint32_t      *acc,
                                                const uint8_t *v,
                                                size_t         dim)
{
    assert(acc != NULL && v != NULL);
    assert(dim > 0u);
    if (acc == NULL || v == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (dim == 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    for (size_t i = 0; i < dim; i++) {
        uint8_t e = v[i];
        if (e > 3u) {
            return SRMECH_ERR_BAD_INPUT;
        }
        acc[1u + i]       += (uint32_t)(e & 1u);
        acc[1u + dim + i] += (uint32_t)((e >> 1) & 1u);
    }
    acc[0] += 1u;
    return SRMECH_OK;
}

/* klein4_bundle_resolve(acc, out, dim): resolve the accumulator to the bundled
 * Klein-4 vector — strict per-bit majority over n = acc[0] folded vectors (an
 * exact tie == n/2 resolves to 0 for that bit), BIT-IDENTICAL to
 * srmech_klein4_bundle over the same vectors. out is dim bytes. The Class-K
 * sign/phase-boundary read-out of the §50 accumulator; no abs(). */
srmech_status_t srmech_klein4_bundle_resolve(const uint32_t *acc,
                                             uint8_t        *out,
                                             size_t          dim)
{
    assert(acc != NULL && out != NULL);
    assert(dim > 0u);
    if (acc == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (dim == 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    uint32_t half = acc[0] / 2u;
    for (size_t i = 0; i < dim; i++) {
        uint8_t r0 = (acc[1u + i] > half) ? 1u : 0u;
        uint8_t r1 = (acc[1u + dim + i] > half) ? 1u : 0u;
        out[i] = (uint8_t)((r1 << 1) | r0);
    }
    return SRMECH_OK;
}

/* The position-namespaced seed base for klein4_compose / klein4_encode_bytes
 * role keys (byte-identical to the Python _KLEIN4_POS_SEED_BASE): 0x10000, so
 * pos-key seeds never collide with the 256-byte alphabet (seeds 0..255). */
#define SRMECH_KLEIN4_POS_SEED_BASE 0x10000u

/* klein4_compose (UPSTREAM §60 / F900; rc18): the scale-invariant role-filler
 * compositor — bundle_i( klein4_bind(part_i, klein4_pos_key(D, i)) ) over n
 * pre-composed D-byte Klein-4 `parts` (row-major, codes {0,1,2,3}). The pos key
 * for slot i is klein4_random over SRMECH_KLEIN4_POS_SEED_BASE + i (byte-
 * identical to the Python _klein4_pos_key). The native peer of hdc.klein4_compose
 * (the RECURSIVE rung above klein4_encode_bytes): one C call folds the whole
 * role-filler bundle via srmech_klein4_bundle_accumulate, so a single part
 * resolves to its position-bound self (bundle of one = itself), matching the
 * Python shortcut. `acc` is a caller-owned (1 + 2*D) uint32 accumulator;
 * `scratch` is 2*D caller-owned bytes (pos-key [0,D) + bound [D,2D)). Width is
 * the architecture (caller's RAM) — no compiled-in cap, no malloc. n >= 1,
 * D >= 1. Additive symbol — no ABI bump. */
srmech_status_t srmech_klein4_compose(const uint8_t *parts,
                                      uint32_t       n,
                                      uint32_t       D,
                                      uint32_t      *acc,
                                      uint8_t       *scratch,
                                      uint8_t       *out)
{
    assert(parts != NULL && acc != NULL && scratch != NULL && out != NULL);
    assert(n >= 1u && D >= 1u);
    if (parts == NULL || acc == NULL || scratch == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n == 0u || D == 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    uint8_t *poskey = scratch;
    uint8_t *bound  = scratch + D;
    for (size_t k = 0; k < (size_t)1u + (size_t)2u * D; k++) {
        acc[k] = 0u;
    }
    for (uint32_t i = 0; i < n; i++) {
        uint32_t key = (uint32_t)SRMECH_KLEIN4_POS_SEED_BASE + i;
        srmech_status_t rc = srmech_klein4_random(&key, (size_t)1, D, poskey);
        if (rc != SRMECH_OK) {
            return rc;
        }
        rc = srmech_klein4_bind(parts + (size_t)i * D, poskey, D, bound);
        if (rc != SRMECH_OK) {
            return rc;
        }
        rc = srmech_klein4_bundle_accumulate(acc, bound, (size_t)D);
        if (rc != SRMECH_OK) {
            return rc;
        }
    }
    return srmech_klein4_bundle_resolve(acc, out, (size_t)D);
}

/* klein4_cooccurrence_fold (UPSTREAM §50; rc165): the §50 holographic
 * co-occurrence fold with the corpus-linear inner loop fully native — the
 * per-token windowed accumulation, no Python callback (the per-token string→code
 * mapping + vocab stay Python, sublinear). For every corpus position i, each
 * neighbour code within ±window (excluding i) folds into the accumulator of the
 * token at i; the fold of one neighbour reuses srmech_klein4_bundle_accumulate
 * (same 2-bit tally + byte validation). out_accs is n_codes * (1 + 2*dim) uint32,
 * caller-owned, zeroed here then folded — the width is the architecture, no cap.
 * window >= 1; bad code byte / out-of-range index -> SRMECH_ERR_BAD_INPUT. */
srmech_status_t srmech_klein4_cooccurrence_fold(const uint8_t  *codes,
                                                uint32_t        n_codes,
                                                const uint32_t *tok_idx,
                                                uint32_t        n_tokens,
                                                uint32_t        window,
                                                size_t          dim,
                                                uint32_t       *out_accs)
{
    assert(codes != NULL && tok_idx != NULL && out_accs != NULL);
    assert(dim > 0u && window > 0u);
    if (codes == NULL || tok_idx == NULL || out_accs == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (dim == 0u || window == 0u || n_codes == 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    size_t stride = 1u + 2u * dim;          /* per-token accumulator width */
    for (size_t k = 0; k < (size_t)n_codes * stride; k++) {
        out_accs[k] = 0u;                   /* zero the caller's accumulators */
    }
    for (uint32_t i = 0; i < n_tokens; i++) {
        uint32_t ti = tok_idx[i];
        if (ti >= n_codes) { return SRMECH_ERR_BAD_INPUT; }
        uint32_t lo = (i > window) ? (i - window) : 0u;
        uint32_t hi = n_tokens;             /* exclusive; no overflow (i<n_tokens) */
        if (window < n_tokens - i) { hi = i + window + 1u; }
        uint32_t *acc = &out_accs[(size_t)ti * stride];
        for (uint32_t j = lo; j < hi; j++) {
            if (j == i) { continue; }
            uint32_t tj = tok_idx[j];
            if (tj >= n_codes) { return SRMECH_ERR_BAD_INPUT; }
            srmech_status_t st = srmech_klein4_bundle_accumulate(
                acc, &codes[(size_t)tj * dim], dim);
            if (st != SRMECH_OK) { return st; }
        }
    }
    return SRMECH_OK;
}

/* ------------------------------------------------------------------ *
 * Class M — Klein-4 EXACT sector ops (v0.9.0rc142; BATCH B1)
 *
 * Seven byte-exact ops over the (F2)^2 Klein-4 carrier that compose /
 * extend the srmech_klein4 foundation above. All integer / sector — no
 * float, no abs (Class-K sign is a pin-slot, never abs()). Byte-identical
 * to the pure-Python hdc.klein4_* ops. Additive symbols -> ABI stays 3.
 * ------------------------------------------------------------------ */

/* k4_argmax4(counts): the argmax over the 4 Klein-4 sector counts, ties broken
 * toward the LOWEST sector index — the shared per-position majority read-out
 * used by the holographic (blind) decode + the triality corrector. No abs. */
static uint8_t srmech_k4_argmax4(const uint32_t counts[4])
{
    uint8_t  best = 0u;
    uint32_t best_c;
    assert(counts != NULL);
    best_c = counts[0];
    for (uint8_t s = 1u; s < 4u; s++) {
        if (counts[s] > best_c) {   /* strict > keeps the lowest index on a tie */
            best = s;
            best_c = counts[s];
        }
    }
    assert(best < 4u);
    return best;
}

/* klein4_sector_flip(in, n, mask): XOR every element with a constant sector mask
 * in {0,1,2,3} — the chirality flips: gamma5 = mask 2 (bit 1), iomega7 = mask 1
 * (bit 0), CPT = mask 3 (both). out[i] = in[i] ^ mask. Class C axis flip; no
 * abs. Out of {0,1,2,3} -> SRMECH_ERR_BAD_INPUT. Additive symbol — no ABI bump. */
srmech_status_t srmech_klein4_sector_flip(const uint8_t *in,
                                          uint32_t       n,
                                          uint8_t        mask,
                                          uint8_t       *out)
{
    assert(in != NULL && out != NULL);
    assert(n > 0u);
    if (in == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n == 0u || mask > 3u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    for (uint32_t i = 0; i < n; i++) {
        if (in[i] > 3u) {
            return SRMECH_ERR_BAD_INPUT;
        }
        out[i] = (uint8_t)(in[i] ^ mask);
    }
    return SRMECH_OK;
}

/* klein4_sector_count(in, n): per-sector occupancy [n0,n1,n2,n3] — the substrate
 * attestation of the chirality-sector distribution. out_counts is 4 uint32
 * (caller-owned). Class-K sector tally; no abs. Out of {0,1,2,3} ->
 * SRMECH_ERR_BAD_INPUT. Additive symbol — no ABI bump. */
srmech_status_t srmech_klein4_sector_count(const uint8_t *in,
                                           uint32_t       n,
                                           uint32_t      *out_counts)
{
    assert(in != NULL && out_counts != NULL);
    assert(n > 0u);
    if (in == NULL || out_counts == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n == 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    out_counts[0] = 0u; out_counts[1] = 0u;
    out_counts[2] = 0u; out_counts[3] = 0u;
    for (uint32_t i = 0; i < n; i++) {
        if (in[i] > 3u) {
            return SRMECH_ERR_BAD_INPUT;
        }
        out_counts[in[i]] += 1u;
    }
    return SRMECH_OK;
}

/* klein4_holographic_encode(in, n, replicas): replicate the store into `replicas`
 * copies (replica-major) — out is n*replicas bytes = the input repeated `replicas`
 * times. Any one 1/replicas subregion reconstructs the whole (#797 op (a2),
 * F353). replicas >= 2. Class M replication bind; no abs. Additive — no ABI
 * bump. */
srmech_status_t srmech_klein4_holographic_encode(const uint8_t *in,
                                                 uint32_t       n,
                                                 uint32_t       replicas,
                                                 uint8_t       *out)
{
    assert(in != NULL && out != NULL);
    assert(n > 0u && replicas >= 2u);
    if (in == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n == 0u || replicas < 2u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    for (uint32_t r = 0; r < replicas; r++) {
        for (uint32_t i = 0; i < n; i++) {
            if (in[i] > 3u) {
                return SRMECH_ERR_BAD_INPUT;
            }
            out[(size_t)r * n + i] = in[i];
        }
    }
    return SRMECH_OK;
}

/* klein4_holographic_decode(store, n, replicas, erased): reconstruct a Klein-4
 * store from its holographic erasure encoding. D = n/replicas (block r is
 * store[r*D : (r+1)*D], replica-major). Two modes:
 *   - erased == NULL: BLIND per-position majority over the `replicas` copies
 *     (ties -> lowest sector index; via srmech_k4_argmax4);
 *   - erased != NULL: KNOWN-location erasure (a length-n mask, nonzero = erased):
 *     per position the FIRST surviving replica — all-erased at a position ->
 *     SRMECH_ERR_BAD_INPUT (unrecoverable, > (replicas-1)/replicas).
 * out is D bytes. Class M ∘ Class C; no abs. n % replicas == 0, replicas >= 2.
 * Additive symbol — no ABI bump. */
srmech_status_t srmech_klein4_holographic_decode(const uint8_t *store,
                                                 uint32_t       n,
                                                 uint32_t       replicas,
                                                 const uint8_t *erased,
                                                 uint8_t       *out)
{
    assert(store != NULL && out != NULL);
    assert(n > 0u && replicas >= 2u);
    if (store == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n == 0u || replicas < 2u || (n % replicas) != 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    uint32_t D = n / replicas;
    for (uint32_t i = 0; i < D; i++) {
        if (erased == NULL) {                       /* blind majority */
            uint32_t counts[4] = {0u, 0u, 0u, 0u};
            for (uint32_t r = 0; r < replicas; r++) {
                uint8_t e = store[(size_t)r * D + i];
                if (e > 3u) {
                    return SRMECH_ERR_BAD_INPUT;
                }
                counts[e] += 1u;
            }
            out[i] = srmech_k4_argmax4(counts);
        } else {                                    /* first surviving replica */
            uint32_t r;
            for (r = 0; r < replicas; r++) {
                if (erased[(size_t)r * D + i] == 0u) {
                    out[i] = store[(size_t)r * D + i];
                    break;
                }
            }
            if (r == replicas) {
                return SRMECH_ERR_BAD_INPUT;         /* all replicas erased */
            }
        }
    }
    return SRMECH_OK;
}

/* klein4_triality_encode(in, n): encode the store as its order-3 triality orbit
 * [v, T(v), T^2(v)] (orbit-major) — out is 3*n bytes (#797 op (a1); F359). T is
 * srmech_klein4_triality_cycle (the order-3 S3 = Aut(V4) relabel); this COMPOSES
 * it: out[0,n) = v, out[n,2n) = T(out[0,n)), out[2n,3n) = T(out[n,2n)). Class M
 * orbit bind ∘ Class I order-3 cycle; no abs. Additive symbol — no ABI bump. */
srmech_status_t srmech_klein4_triality_encode(const uint8_t *in,
                                              uint32_t       n,
                                              uint8_t       *out)
{
    srmech_status_t rc;
    assert(in != NULL && out != NULL);
    assert(n > 0u);
    if (in == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n == 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    for (uint32_t i = 0; i < n; i++) {
        if (in[i] > 3u) {
            return SRMECH_ERR_BAD_INPUT;
        }
        out[i] = in[i];
    }
    rc = srmech_klein4_triality_cycle(out, n, 0, out + n);           /* T(v) */
    if (rc != SRMECH_OK) {
        return rc;
    }
    return srmech_klein4_triality_cycle(out + n, n, 0,
                                        out + (size_t)2u * n);       /* T(T(v)) */
}

/* klein4_triality_correct(store, n, scratch): correct a Klein-4 store via the
 * order-3 triality 2-of-3 majority (#797 op (a1)). D = n/3; the three orbit-
 * blocks [b0,b1,b2] are brought to the common v-frame — b0, T^-1(b1),
 * T^-2(b2) = T(b2) — and the per-position 2-of-3 majority (ties -> lowest sector,
 * via srmech_k4_argmax4) recovers v, correcting one error. COMPOSES
 * srmech_klein4_triality_cycle for the two inverse-frame relabels; `scratch` is
 * 2*D caller-owned bytes (frame1 [0,D), frame2 [D,2D)). Class M ∘ Class C ∘
 * Class C; no abs. n % 3 == 0. Additive symbol — no ABI bump. */
srmech_status_t srmech_klein4_triality_correct(const uint8_t *store,
                                               uint32_t       n,
                                               uint8_t       *scratch,
                                               uint8_t       *out)
{
    srmech_status_t rc;
    uint32_t D;
    uint8_t *frame1;
    uint8_t *frame2;
    assert(store != NULL && scratch != NULL && out != NULL);
    assert(n > 0u && (n % 3u) == 0u);
    if (store == NULL || scratch == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n == 0u || (n % 3u) != 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    D = n / 3u;
    frame1 = scratch;
    frame2 = scratch + D;
    rc = srmech_klein4_triality_cycle(store + D, D, 1, frame1);      /* T^-1(b1) */
    if (rc != SRMECH_OK) {
        return rc;
    }
    rc = srmech_klein4_triality_cycle(store + (size_t)2u * D, D, 0, frame2); /* T(b2) */
    if (rc != SRMECH_OK) {
        return rc;
    }
    for (uint32_t i = 0; i < D; i++) {
        uint32_t counts[4] = {0u, 0u, 0u, 0u};
        uint8_t v0 = store[i];
        if (v0 > 3u) {
            return SRMECH_ERR_BAD_INPUT;
        }
        counts[v0] += 1u;
        counts[frame1[i]] += 1u;
        counts[frame2[i]] += 1u;
        out[i] = srmech_k4_argmax4(counts);
    }
    return SRMECH_OK;
}

/* ------------------------------------------------------------------ *
 * Class M — Klein-4 deterministic random (v0.9.0rc6)
 *
 * srmech_klein4_random reproduces CPython random.Random(seed).randrange(4),
 * D times, BYTE-IDENTICAL: an MT19937 generator seeded by init_by_array over
 * the seed's little-endian uint32 words, each draw = getrandbits(3)
 * (= genrand_uint32() >> 29) with rejection of values >= 4. This makes the §60
 * byte/glyph encoder — and its 256-byte vocab + position keys — fully native
 * (klein4_random was the last python_only_debt klein4 op). The seeding,
 * tempering, and rejection match CPython's _randommodule.c + random.py exactly
 * (proven byte-for-byte against random.Random in the Python parity test).
 *
 * Standalone-complete (no caps, no Python fallback): the 624-word MT state is
 * stack-resident; the caller supplies the seed key — a C-only / MCU host seeds
 * from its own entropy and passes the words, exactly as the Python wrapper
 * splits the seed int. Reference: Matsumoto & Nishimura (1998) "Mersenne
 * Twister", ACM TOMACS 8(1), 3-30.
 * ------------------------------------------------------------------ */

#define SRMECH_MT_N        624u
#define SRMECH_MT_M        397u
#define SRMECH_MT_MATRIX_A 0x9908b0dfu
#define SRMECH_MT_UPPER    0x80000000u
#define SRMECH_MT_LOWER    0x7fffffffu

typedef struct srmech_mt {
    uint32_t state[SRMECH_MT_N];
    uint32_t index;
} srmech_mt_t;

/* init_genrand(s): seed the 624-word state from a single 32-bit value (CPython
 * _randommodule init_genrand). The non-linear recurrence is integer-exact. */
static void srmech_mt_init_genrand(srmech_mt_t *st, uint32_t s)
{
    uint32_t i;
    assert(st != NULL);
    st->state[0] = s;
    for (i = 1u; i < SRMECH_MT_N; i++) {
        uint32_t prev = st->state[i - 1u];
        st->state[i] = 1812433253u * (prev ^ (prev >> 30)) + i;
    }
    st->index = SRMECH_MT_N;
    assert(st->index == SRMECH_MT_N);
}

/* init_by_array(key, key_length): seed from an array of 32-bit words — the
 * path random.Random(int) takes after splitting the seed into little-endian
 * words (CPython init_by_array). Bit-exact non-linear mixing. */
static void srmech_mt_init_by_array(srmech_mt_t    *st,
                                    const uint32_t *key,
                                    size_t          key_length)
{
    size_t i = 1u;
    size_t j = 0u;
    size_t k;
    assert(st != NULL && key != NULL);
    assert(key_length > 0u);
    srmech_mt_init_genrand(st, 19650218u);
    k = (SRMECH_MT_N > key_length) ? (size_t)SRMECH_MT_N : key_length;
    for (; k != 0u; k--) {
        uint32_t prev = st->state[i - 1u];
        st->state[i] = (st->state[i] ^ ((prev ^ (prev >> 30)) * 1664525u))
                       + key[j] + (uint32_t)j;
        i++; j++;
        if (i >= SRMECH_MT_N) { st->state[0] = st->state[SRMECH_MT_N - 1u]; i = 1u; }
        if (j >= key_length) { j = 0u; }
    }
    for (k = SRMECH_MT_N - 1u; k != 0u; k--) {
        uint32_t prev = st->state[i - 1u];
        st->state[i] = (st->state[i] ^ ((prev ^ (prev >> 30)) * 1566083941u))
                       - (uint32_t)i;
        i++;
        if (i >= SRMECH_MT_N) { st->state[0] = st->state[SRMECH_MT_N - 1u]; i = 1u; }
    }
    st->state[0] = 0x80000000u;  /* MSB = 1 assures a non-zero initial array */
}

/* regenerate(): refresh the full 624-word block (the twist) — split out of
 * genrand_uint32 to keep both under JPL Rule 4 (≤60 lines). */
static void srmech_mt_regenerate(srmech_mt_t *st)
{
    static const uint32_t mag01[2] = { 0u, SRMECH_MT_MATRIX_A };
    uint32_t kk;
    uint32_t *mt;
    assert(st != NULL);
    assert(st->index >= SRMECH_MT_N);
    mt = st->state;
    for (kk = 0u; kk < SRMECH_MT_N - SRMECH_MT_M; kk++) {
        uint32_t y = (mt[kk] & SRMECH_MT_UPPER) | (mt[kk + 1u] & SRMECH_MT_LOWER);
        mt[kk] = mt[kk + SRMECH_MT_M] ^ (y >> 1) ^ mag01[y & 1u];
    }
    for (; kk < SRMECH_MT_N - 1u; kk++) {
        uint32_t y = (mt[kk] & SRMECH_MT_UPPER) | (mt[kk + 1u] & SRMECH_MT_LOWER);
        mt[kk] = mt[kk - (SRMECH_MT_N - SRMECH_MT_M)] ^ (y >> 1) ^ mag01[y & 1u];
    }
    {
        uint32_t y = (mt[SRMECH_MT_N - 1u] & SRMECH_MT_UPPER) | (mt[0] & SRMECH_MT_LOWER);
        mt[SRMECH_MT_N - 1u] = mt[SRMECH_MT_M - 1u] ^ (y >> 1) ^ mag01[y & 1u];
    }
    st->index = 0u;
}

/* genrand_uint32(): one tempered 32-bit word (CPython genrand_uint32). */
static uint32_t srmech_mt_genrand_uint32(srmech_mt_t *st)
{
    uint32_t y;
    assert(st != NULL);
    assert(st->index <= SRMECH_MT_N);
    if (st->index >= SRMECH_MT_N) {
        srmech_mt_regenerate(st);
    }
    y = st->state[st->index];
    st->index++;
    y ^= (y >> 11);
    y ^= (y << 7) & 0x9d2c5680u;
    y ^= (y << 15) & 0xefc60000u;
    y ^= (y >> 18);
    return y;
}

/* below4(): random._randbelow(4) = getrandbits(3) with rejection of >= 4. The
 * top 3 bits give 0..7; reject 4..7 and redraw. Reject probability 1/2 per
 * draw; the 64-try bound (JPL Rule 2) is unreachable in practice (2^-64) and
 * keeps the consumed word-stream byte-identical to CPython. */
static uint32_t srmech_mt_below4(srmech_mt_t *st)
{
    uint32_t tries;
    assert(st != NULL);
    assert(st->index <= SRMECH_MT_N);
    for (tries = 0u; tries < 64u; tries++) {
        uint32_t r = srmech_mt_genrand_uint32(st) >> 29;  /* getrandbits(3) */
        if (r < 4u) {
            return r;
        }
    }
    return 0u;  /* unreachable; statically-bounded fallback for Rule 2 */
}

srmech_status_t srmech_klein4_random(const uint32_t *key,
                                     size_t          key_length,
                                     uint32_t        D,
                                     uint8_t        *out)
{
    srmech_mt_t st;
    uint32_t i;
    assert(key != NULL && out != NULL);
    assert(D > 0u && key_length > 0u);
    if (key == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (D == 0u || key_length == 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    srmech_mt_init_by_array(&st, key, key_length);
    for (i = 0u; i < D; i++) {
        out[i] = (uint8_t)srmech_mt_below4(&st);
    }
    return SRMECH_OK;
}
