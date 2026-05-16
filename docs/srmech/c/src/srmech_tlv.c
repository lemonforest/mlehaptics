/*
 * srmech_tlv.c — Class B primitive: tagged-tuple (TLV) byte-canonical form.
 *
 * Task #217 Phase C1 rc4 — lightweight trio (B + G + H). Class B
 * appears in Spike #24's cross-substrate audit ("B tagged-tuple") at
 * five of six bonus substrates as the structured-record primitive
 * (move records in tactical, message blocks in SHA-256, tensor
 * descriptors in NN, dimension tags in MFO 3+7+1, state-update
 * descriptors in RNG).
 *
 * srmech's Class B C surface ships a minimal TLV (Type-Length-Value)
 * encoder for producing deterministic byte-canonical forms of typed
 * records, suitable for hashing / fingerprinting. JSON parsing of
 * MPRRecord stays Python-side per srmech CLAUDE.md operational-
 * scope-clarification (binding-layer concern); Class B's *primitive
 * class operation* is the byte concatenation discipline used for
 * the canonical form, not the JSON parsing.
 *
 * Format:
 *   [u8 tag][u32 length, big-endian][value bytes]
 *
 * Total prefix is 5 bytes; the rest is the value verbatim. Big-endian
 * length avoids platform-specific byte-order ambiguity and is the
 * conventional choice for wire-format / fingerprint records.
 *
 * Per [[feedback_struct_field_ordering_big_first]]: no structs here;
 * the TLV format is wire-spec ordering (tag-first) per the format
 * definition above. That's the documented exception.
 *
 * JPL Power-of-Ten compliance: Rules 1/3/4/5/7/10 OK. Single function,
 * fixed prefix size, bounded by caller-supplied capacity.
 *
 * License: GPL-3.0-or-later.
 */

#include "srmech.h"

#include <assert.h>
#include <stdint.h>
#include <string.h>

/* TLV prefix is 1 (tag) + 4 (length, big-endian uint32) = 5 bytes. */
#define SRMECH_TLV_PREFIX_BYTES 5

srmech_status_t srmech_tlv_pack(uint8_t        tag,
                                const uint8_t *value,
                                uint32_t       value_len,
                                uint8_t       *out_buffer,
                                uint32_t       out_capacity,
                                uint32_t      *out_written)
{
    assert(out_buffer != NULL);
    assert(out_written != NULL);
    if (out_buffer == NULL || out_written == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (value_len > 0 && value == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    /* Capacity must hold the prefix + the entire value. */
    uint64_t total = (uint64_t)SRMECH_TLV_PREFIX_BYTES + (uint64_t)value_len;
    if (total > (uint64_t)out_capacity) {
        return SRMECH_ERR_OVERFLOW;
    }
    /* Write tag, then big-endian length, then value bytes. */
    out_buffer[0] = tag;
    out_buffer[1] = (uint8_t)((value_len >> 24) & 0xFFu);
    out_buffer[2] = (uint8_t)((value_len >> 16) & 0xFFu);
    out_buffer[3] = (uint8_t)((value_len >>  8) & 0xFFu);
    out_buffer[4] = (uint8_t)( value_len        & 0xFFu);
    if (value_len > 0) {
        memcpy(out_buffer + SRMECH_TLV_PREFIX_BYTES, value, value_len);
    }
    *out_written = (uint32_t)total;
    return SRMECH_OK;
}
