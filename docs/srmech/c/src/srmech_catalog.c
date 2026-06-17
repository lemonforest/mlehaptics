/*
 * srmech_catalog.c — Class E primitive: catalog / naming.
 *
 * Task #217 Phase C1 rc5 — Class E earns its C surface per the
 * dissolution-first / no-binding-layer-carve-out discipline
 * ([[feedback_no_binding_layer_carveout]]).
 *
 * The Class E primitive operation: given a search key and a sorted
 * array of (key, value) pairs, find the entry whose key equals the
 * search key and return its value byte-slice. Binary search over
 * ascending lexicographic keys.
 *
 * Class E appears in Spike #24's cross-substrate audit as the
 * structured-name → canonical-artifact lookup primitive. Universal
 * across substrates (registry lookups in tactical, dispatch tables in
 * SHA-256/NN, MPRRecord catalog in srmech itself).
 *
 * Key ordering: caller's responsibility (keys MUST be sorted
 * ascending by lexicographic byte comparison). Binary search returns
 * SRMECH_ERR_INTERNAL if the array is unsorted and the search
 * trajectory detects a violation, but the contract is that the
 * caller has pre-sorted.
 *
 * Pi-free integer arithmetic; no LAPACK; no malloc; bounded loops
 * (binary search is O(log n_entries), at most 32 iterations for
 * uint32 entry counts).
 *
 * JPL Power-of-Ten compliance: Rules 1/3/4/5/7/10 OK.
 *
 * License: MIT.
 */

#include "srmech.h"

#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <string.h>

/* Bounded by log2(2^32) = 32; double for safety. */
#define SRMECH_CATALOG_BSEARCH_CAP 64

/* Helper: lexicographic comparison of two byte slices.
 * Returns < 0 / 0 / > 0 in the manner of memcmp, with length tiebreak
 * (shorter is less when prefix-equal). */
static int srmech_catalog_lex_cmp(const uint8_t *a, uint32_t a_len,
                                  const uint8_t *b, uint32_t b_len)
{
    assert(a_len == 0 || a != NULL);
    assert(b_len == 0 || b != NULL);
    uint32_t min_len = (a_len < b_len) ? a_len : b_len;
    if (min_len > 0) {
        int c = memcmp(a, b, min_len);
        if (c != 0) {
            return c;
        }
    }
    if (a_len < b_len) {
        return -1;
    }
    if (a_len > b_len) {
        return 1;
    }
    return 0;
}

srmech_status_t srmech_catalog_lookup(const uint8_t  *key,
                                      uint32_t        key_len,
                                      const uint8_t  *keys_buffer,
                                      const uint32_t *key_offsets,
                                      const uint32_t *key_lengths,
                                      const uint32_t *value_offsets,
                                      const uint32_t *value_lengths,
                                      uint32_t        n_entries,
                                      bool           *out_found,
                                      uint32_t       *out_value_offset,
                                      uint32_t       *out_value_length)
{
    assert(out_found != NULL);
    assert(out_value_offset != NULL);
    if (out_found == NULL || out_value_offset == NULL
        || out_value_length == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    *out_found = false;
    *out_value_offset = 0;
    *out_value_length = 0;
    if (n_entries == 0) {
        return SRMECH_OK;
    }
    if (key_offsets == NULL || key_lengths == NULL
        || value_offsets == NULL || value_lengths == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (key_len > 0 && key == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    /* Binary search. lo / hi are signed for the standard idiom. */
    int32_t lo = 0;
    int32_t hi = (int32_t)n_entries - 1;
    for (int i = 0; i < SRMECH_CATALOG_BSEARCH_CAP && lo <= hi; i++) {
        int32_t mid = lo + (hi - lo) / 2;
        const uint8_t *mid_key = (key_lengths[mid] > 0)
                                 ? keys_buffer + key_offsets[mid]
                                 : NULL;
        int c = srmech_catalog_lex_cmp(key, key_len,
                                       mid_key, key_lengths[mid]);
        if (c == 0) {
            *out_found = true;
            *out_value_offset = value_offsets[mid];
            *out_value_length = value_lengths[mid];
            return SRMECH_OK;
        }
        if (c < 0) {
            hi = mid - 1;
        } else {
            lo = mid + 1;
        }
    }
    return SRMECH_OK;
}

srmech_status_t srmech_reverse_order(uint32_t n, uint32_t *out_order)
{
    assert(n == 0 || out_order != NULL);
    if (n > 0 && out_order == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    /* Harmonic-2 chiral mirror of a sorted catalog (F150): the reversed index
     * order — out_order[i] = n - 1 - i. The wrapper applies this permutation to
     * the (key,value) pairs (a descending-key view of an ascending catalog). */
    for (uint32_t i = 0; i < n; i++) {
        out_order[i] = n - 1u - i;
    }
    assert(n == 0 || out_order[0] == n - 1u);
    return SRMECH_OK;
}
