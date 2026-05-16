/*
 * srmech_search.c — Class G primitive: discovery / search.
 *
 * Task #217 Phase C1 rc4 — lightweight trio (B + G + H). Class G
 * appears in Spike #24's cross-substrate audit ("G discovery/search")
 * as the pattern-matching / element-lookup primitive (chess opening
 * search in tactical, eigenvalue-degeneracy search in MFO 3+7+1).
 *
 * srmech's Class G C surface ships a single byte-pattern search
 * (naive O(n*m); fast for the small-haystack cases srmech actually
 * encounters — descriptor lookups, fingerprint matching, small
 * tagged-record discovery). Boyer-Moore or KMP would be faster
 * asymptotically but their constant factor is worse for the small
 * inputs srmech sees; naive search is correct and JPL-clean.
 *
 * Pi-free integer arithmetic; no LAPACK; no malloc; bounded loops
 * (haystack_len × needle_len, both caller-supplied).
 *
 * JPL Power-of-Ten compliance: Rules 1/3/4/5/7/10 OK.
 *
 * License: GPL-3.0-or-later.
 */

#include "srmech.h"

#include <assert.h>
#include <stdbool.h>
#include <stdint.h>

/* Sentinel: when needle is not found, *out_offset is set to this
 * value (UINT32_MAX). Callers should check the return status
 * (SRMECH_OK with offset == UINT32_MAX means "not found" vs
 * SRMECH_OK with offset < haystack_len means "found at that offset"). */
#define SRMECH_SEARCH_NOT_FOUND UINT32_MAX

srmech_status_t srmech_byte_search(const uint8_t *haystack,
                                   uint32_t       haystack_len,
                                   const uint8_t *needle,
                                   uint32_t       needle_len,
                                   uint32_t      *out_offset)
{
    assert(out_offset != NULL);
    assert(needle_len == 0 || needle != NULL);
    if (out_offset == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (needle_len > 0 && needle == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (haystack_len > 0 && haystack == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    /* Empty needle matches at offset 0 by convention (Python's
     * `s.find("")` returns 0). */
    if (needle_len == 0) {
        *out_offset = 0;
        return SRMECH_OK;
    }
    /* Needle longer than haystack cannot match. */
    if (needle_len > haystack_len) {
        *out_offset = SRMECH_SEARCH_NOT_FOUND;
        return SRMECH_OK;
    }
    /* Naive search: for each candidate offset i in [0, haystack_len -
     * needle_len], compare needle_len bytes. Bounded by
     * haystack_len × needle_len. */
    uint32_t last = haystack_len - needle_len;
    for (uint32_t i = 0; i <= last; i++) {
        bool match = true;
        for (uint32_t j = 0; j < needle_len; j++) {
            if (haystack[i + j] != needle[j]) {
                match = false;
                break;
            }
        }
        if (match) {
            *out_offset = i;
            return SRMECH_OK;
        }
    }
    *out_offset = SRMECH_SEARCH_NOT_FOUND;
    return SRMECH_OK;
}
