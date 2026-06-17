/*
 * srmech_template.c — Class F primitive: substitution / templating.
 *
 * Task #217 Phase C1 rc5 — Class F earns its C surface per the
 * no-binding-layer-carve-out discipline
 * ([[feedback_no_binding_layer_carveout]]).
 *
 * The Class F primitive operation: render a template byte sequence
 * containing `{key}` placeholders into an output buffer, substituting
 * each `{key}` with the corresponding value from a sorted key→value
 * catalog. Builds on Class E (srmech_catalog_lookup) for the lookup.
 *
 * Format:
 *   - Plain bytes pass through verbatim.
 *   - `{key}` (literal `{`, key bytes not containing `{` or `}`,
 *     literal `}`) substitutes with the looked-up value.
 *   - `{{` and `}}` are NOT recognised as escapes (kept simple for
 *     JPL discipline); to include a literal `{` or `}` in output,
 *     the caller can substitute a key that has the brace as its value.
 *   - Unmatched `{` with no closing `}` before end of template:
 *     SRMECH_ERR_BAD_INPUT.
 *   - Key not found in catalog: SRMECH_ERR_BAD_INPUT (caller must
 *     supply all referenced keys).
 *
 * Pi-free integer arithmetic; no LAPACK; no malloc; bounded loops
 * (template_len iterations for the outer scan; each `{...}` resolved
 * via O(log n_entries) catalog lookup).
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

/* Helper: append `n` bytes from `src` to `out_buf` at `*pos`,
 * respecting capacity. Returns SRMECH_ERR_OVERFLOW on overflow. */
static srmech_status_t srmech_template_append(const uint8_t *src,
                                              uint32_t       n,
                                              uint8_t       *out_buf,
                                              uint32_t       capacity,
                                              uint32_t      *pos)
{
    assert(out_buf != NULL);
    assert(pos != NULL);
    if (n == 0) {
        return SRMECH_OK;
    }
    if (*pos > capacity || (capacity - *pos) < n) {
        return SRMECH_ERR_OVERFLOW;
    }
    memcpy(out_buf + *pos, src, n);
    *pos += n;
    return SRMECH_OK;
}

srmech_status_t srmech_template_render(const uint8_t  *tmpl,
                                       uint32_t        tmpl_len,
                                       const uint8_t  *keys_buffer,
                                       const uint32_t *key_offsets,
                                       const uint32_t *key_lengths,
                                       const uint8_t  *values_buffer,
                                       const uint32_t *value_offsets,
                                       const uint32_t *value_lengths,
                                       uint32_t        n_pairs,
                                       uint8_t        *out_buf,
                                       uint32_t        out_capacity,
                                       uint32_t       *out_written)
{
    assert(out_buf != NULL);
    assert(out_written != NULL);
    if (out_buf == NULL || out_written == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    *out_written = 0;
    if (tmpl_len > 0 && tmpl == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    /* Scan template byte-by-byte. Bounded by tmpl_len. */
    uint32_t pos = 0;
    uint32_t i = 0;
    for (uint32_t guard = 0; guard < tmpl_len + 1; guard++) {
        if (i >= tmpl_len) {
            break;
        }
        if (tmpl[i] != (uint8_t)'{') {
            srmech_status_t st = srmech_template_append(&tmpl[i], 1,
                                                        out_buf,
                                                        out_capacity,
                                                        &pos);
            if (st != SRMECH_OK) {
                return st;
            }
            i++;
            continue;
        }
        /* Found `{`; scan forward for matching `}`. */
        uint32_t key_start = i + 1;
        uint32_t key_end = key_start;
        while (key_end < tmpl_len && tmpl[key_end] != (uint8_t)'}') {
            key_end++;
        }
        if (key_end >= tmpl_len) {
            return SRMECH_ERR_BAD_INPUT;  /* unterminated `{...` */
        }
        /* key spans [key_start, key_end); look up in catalog. */
        bool found = false;
        uint32_t v_off = 0;
        uint32_t v_len = 0;
        srmech_status_t st = srmech_catalog_lookup(
            &tmpl[key_start], key_end - key_start,
            keys_buffer, key_offsets, key_lengths,
            value_offsets, value_lengths,
            n_pairs, &found, &v_off, &v_len);
        if (st != SRMECH_OK) {
            return st;
        }
        if (!found) {
            return SRMECH_ERR_BAD_INPUT;  /* unknown key */
        }
        st = srmech_template_append(values_buffer + v_off, v_len,
                                    out_buf, out_capacity, &pos);
        if (st != SRMECH_OK) {
            return st;
        }
        i = key_end + 1;  /* skip past `}` */
    }
    assert(pos <= out_capacity);
    *out_written = pos;
    return SRMECH_OK;
}
