/*
 * srmech_dispatch.c — Class D primitive: late-binding / dispatch.
 *
 * Task #217 Phase C1 rc5 — Class D earns its C surface (not an
 * acknowledgment ship; binding-layer framing rejected per
 * [[feedback_no_binding_layer_carveout]]).
 *
 * The Class D primitive operation: given an input byte sequence and a
 * collection of (pattern, tag) rules, find the first rule whose
 * pattern occurs in the input and return its tag. Multi-needle
 * byte-pattern dispatcher; the "select an implementation at runtime"
 * primitive expressed as a flat C operation.
 *
 * Class D appears in Spike #24's cross-substrate audit at five of six
 * bonus substrates (tactical / SHA-256 / NN / MFO 3+7+1 / RNG) as the
 * choose-which-branch-to-take primitive. Internally builds on Class G
 * (srmech_byte_search) for each rule's pattern lookup.
 *
 * Pi-free integer arithmetic; no LAPACK; no malloc; bounded loops
 * (n_rules × input_len × pattern_len, all caller-supplied).
 *
 * JPL Power-of-Ten compliance: Rules 1/3/4/5/7/10 OK.
 *
 * License: GPL-3.0-or-later.
 */

#include "srmech.h"

#include <assert.h>
#include <stdbool.h>
#include <stdint.h>

srmech_status_t srmech_dispatch_match(const uint8_t  *input,
                                      uint32_t        input_len,
                                      const uint8_t  *patterns_buffer,
                                      const uint32_t *pattern_offsets,
                                      const uint32_t *pattern_lengths,
                                      const uint32_t *tags,
                                      uint32_t        n_rules,
                                      bool           *out_matched,
                                      uint32_t       *out_tag)
{
    assert(out_matched != NULL);
    assert(out_tag != NULL);
    if (out_matched == NULL || out_tag == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    *out_matched = false;
    *out_tag = 0;
    if (n_rules > 0 && (pattern_offsets == NULL || pattern_lengths == NULL
                        || tags == NULL)) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (input_len > 0 && input == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    /* For each rule i, look for pattern in input. First match wins. */
    for (uint32_t i = 0; i < n_rules; i++) {
        uint32_t plen = pattern_lengths[i];
        const uint8_t *p = (plen > 0)
                           ? patterns_buffer + pattern_offsets[i]
                           : NULL;
        uint32_t offset = 0;
        srmech_status_t st = srmech_byte_search(input, input_len,
                                                p, plen, &offset);
        if (st != SRMECH_OK) {
            return st;
        }
        if (offset != UINT32_MAX) {
            *out_matched = true;
            *out_tag = tags[i];
            return SRMECH_OK;
        }
    }
    return SRMECH_OK;
}

srmech_status_t srmech_mirror_pattern(const uint8_t *pattern,
                                      uint32_t       pattern_len,
                                      uint8_t       *out)
{
    assert(pattern_len == 0 || pattern != NULL);
    assert(pattern_len == 0 || out != NULL);
    if (pattern_len > 0 && (pattern == NULL || out == NULL)) {
        return SRMECH_ERR_NULL_ARG;
    }
    /* Harmonic-2 chiral mirror (F150): reverse the needle byte order.
     * out[i] = pattern[pattern_len - 1 - i]. out must NOT alias pattern. */
    for (uint32_t i = 0; i < pattern_len; i++) {
        out[i] = pattern[pattern_len - 1u - i];
    }
    return SRMECH_OK;
}
