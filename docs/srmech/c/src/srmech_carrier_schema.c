/*
 * srmech_carrier_schema.c — accessors + canonical JSON assembler over the
 * generated `srmech_carrier_registry` const table (0.9.0rc205; gh #1293 —
 * the CARRIER / operand introspection surface, the noun-side dual of the
 * rc184 tool-schema registry).
 *
 * The table + `srmech_carrier_registry_len` are DEFINED in the generated
 * translation unit `srmech_carrier_registry.c` (regenerate with
 * c/tools/gen_carrier_registry.py). This file provides the public
 * accessors declared in srmech.h and the whole-schema assembler
 * `srmech_carrier_schema`, whose output is BYTE-IDENTICAL to CPython
 *   json.dumps(srmech.amsc.carrier_schema._pure_carrier_schema(),
 *              sort_keys=True, separators=(",", ":"))
 * — each per-carrier entry payload is baked in the table as its
 * already-canonical compact-ASCII JSON fragment, and the table rows are in
 * byte-sorted name order (== the sort_keys top-level key order), so the
 * assembler is plain concatenation:
 *   { "name" : <fragment> , ... }
 * with no runtime escaping. That byte-identity IS the hash-ratchet
 * contract: srmech_sha256_hex(this) == sha256 of the Python SSoT payload
 * (tests/test_carrier_schema_rc205.py).
 *
 * JPL-clean: no malloc (the caller supplies the output buffer; a NULL
 * buffer is a size-query), no goto, no recursion, no libm, no abs.
 * ABI-additive (SRMECH_ABI_VERSION stays 4).
 *
 * License: MIT.
 */

#include <assert.h>
#include <stddef.h>
#include <string.h>

#include "srmech.h"

/* Defined in the generated srmech_carrier_registry.c. */
extern const srmech_carrier_entry_t srmech_carrier_registry_table[];
extern const size_t srmech_carrier_registry_len;

/* ------------------------------------------------------------------
 * Accessors
 * ------------------------------------------------------------------ */

size_t srmech_carrier_registry_count(void)
{
    assert(srmech_carrier_registry_table != NULL);
    assert(srmech_carrier_registry_len > 0u);
    return srmech_carrier_registry_len;
}

const srmech_carrier_entry_t *srmech_carrier_registry_get(size_t index)
{
    assert(srmech_carrier_registry_table != NULL);
    assert(srmech_carrier_registry_len > 0u);
    if (index >= srmech_carrier_registry_len) {
        return NULL;
    }
    return &srmech_carrier_registry_table[index];
}

const srmech_carrier_entry_t *srmech_carrier_registry_find(const char *name)
{
    size_t i;
    if (name == NULL) {
        return NULL;
    }
    assert(srmech_carrier_registry_table != NULL);
    assert(srmech_carrier_registry_len > 0u);
    for (i = 0u; i < srmech_carrier_registry_len; i++) {
        if (strcmp(srmech_carrier_registry_table[i].name, name) == 0) {
            return &srmech_carrier_registry_table[i];
        }
    }
    return NULL;
}

/* ------------------------------------------------------------------
 * Whole-schema canonical JSON assembler (bounded, no allocation)
 * ------------------------------------------------------------------ */

typedef struct {
    char  *buf;       /* NULL for a size-query                        */
    size_t cap;       /* capacity of buf (bytes), 0 when buf == NULL  */
    size_t used;      /* bytes produced so far                        */
    int    overflow;  /* set once a write would exceed cap            */
} cs_emit_t;

/* Append `n` raw bytes; in size-query / overflow modes only `used`
 * advances (on overflow the caller returns SRMECH_ERR_OVERFLOW). */
static void cs_raw(cs_emit_t *e, const char *s, size_t n)
{
    size_t i;
    assert(e != NULL);
    assert(s != NULL || n == 0u);
    if (e->buf != NULL) {
        if (e->overflow || e->used + n > e->cap) {
            e->overflow = 1;
            return;
        }
        for (i = 0u; i < n; i++) {
            e->buf[e->used + i] = s[i];
        }
    }
    e->used += n;
}

/* Append a NUL-terminated literal / pre-canonical fragment. */
static void cs_cstr(cs_emit_t *e, const char *s)
{
    assert(e != NULL);
    assert(s != NULL);
    cs_raw(e, s, strlen(s));
}

/* Emit the whole registry as the canonical (sorted-key) JSON object:
 * `{"<name>":<entry_json>,...}`. The carrier names are ASCII identifiers
 * (nothing to escape) and the fragments are pre-canonical, so this is
 * plain concatenation in the table's byte-sorted name order. */
static void cs_emit_schema_sorted(cs_emit_t *e)
{
    size_t n, i;
    const srmech_carrier_entry_t *c;
    assert(e != NULL);
    n = srmech_carrier_registry_count();
    assert(n > 0u);
    cs_cstr(e, "{");
    for (i = 0u; i < n; i++) {
        c = srmech_carrier_registry_get(i);
        assert(c != NULL);
        if (i > 0u) {
            cs_cstr(e, ",");
        }
        cs_cstr(e, "\"");
        cs_cstr(e, c->name);
        cs_cstr(e, "\":");
        cs_raw(e, c->entry_json, c->entry_len);
    }
    cs_cstr(e, "}");
}

srmech_status_t srmech_carrier_schema(char *buf, size_t buf_len,
                                      size_t *out_len)
{
    cs_emit_t e;
    if (out_len == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(buf != NULL || buf_len == 0u);
    assert(out_len != NULL);  /* guaranteed by the early NULL-arg return */
    e.buf = buf;
    e.cap = buf_len;
    e.used = 0u;
    e.overflow = 0;
    cs_emit_schema_sorted(&e);
    *out_len = e.used;
    return e.overflow ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}
