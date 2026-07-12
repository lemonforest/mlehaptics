/*
 * srmech_responsion_schema.c — accessors + canonical JSON assembler over
 * the generated `srmech_responsion_registry` const table (0.9.0rc225 —
 * the RESPONSION / stored-relationship introspection surface, the k=3
 * EDGE face binding the rc184 tool registry (the ops/verbs) and the
 * rc205 carrier registry (the operands/nouns); user design 2026-07-12).
 *
 * The table + `srmech_responsion_registry_len` are DEFINED in the
 * generated translation unit `srmech_responsion_registry.c` (regenerate
 * with c/tools/gen_responsion_registry.py). This file provides the public
 * accessors declared in srmech.h and the whole-schema assembler
 * `srmech_responsion_schema`, whose output is BYTE-IDENTICAL to CPython
 *   json.dumps(srmech.amsc.responsion_schema._pure_responsion_schema(),
 *              sort_keys=True, separators=(",", ":"))
 * — each per-edge payload is baked in the table as its already-canonical
 * compact-ASCII JSON array fragment, and the table rows are in
 * byte-sorted key order (== the sort_keys top-level key order), so the
 * assembler is plain concatenation:
 *   { "key" : <fragment> , ... }
 * with no runtime escaping (edge keys are pure-ASCII dotted identifiers
 * joined by '|'). That byte-identity IS the hash-ratchet contract:
 * srmech_sha256_hex(this) == sha256 of the Python SSoT payload
 * (tests/test_responsion_schema_rc225.py).
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

/* Defined in the generated srmech_responsion_registry.c. */
extern const srmech_responsion_entry_t srmech_responsion_registry_table[];
extern const size_t srmech_responsion_registry_len;

/* ------------------------------------------------------------------
 * Accessors
 * ------------------------------------------------------------------ */

size_t srmech_responsion_registry_count(void)
{
    assert(srmech_responsion_registry_table != NULL);
    assert(srmech_responsion_registry_len > 0u);
    return srmech_responsion_registry_len;
}

const srmech_responsion_entry_t *srmech_responsion_registry_get(size_t index)
{
    assert(srmech_responsion_registry_table != NULL);
    assert(srmech_responsion_registry_len > 0u);
    if (index >= srmech_responsion_registry_len) {
        return NULL;
    }
    return &srmech_responsion_registry_table[index];
}

const srmech_responsion_entry_t *srmech_responsion_registry_find(
    const char *key)
{
    size_t i;
    if (key == NULL) {
        return NULL;
    }
    assert(srmech_responsion_registry_table != NULL);
    assert(srmech_responsion_registry_len > 0u);
    for (i = 0u; i < srmech_responsion_registry_len; i++) {
        if (strcmp(srmech_responsion_registry_table[i].key, key) == 0) {
            return &srmech_responsion_registry_table[i];
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
} rs_emit_t;

/* Append `n` raw bytes; in size-query / overflow modes only `used`
 * advances (on overflow the caller returns SRMECH_ERR_OVERFLOW). */
static void rs_raw(rs_emit_t *e, const char *s, size_t n)
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
static void rs_cstr(rs_emit_t *e, const char *s)
{
    assert(e != NULL);
    assert(s != NULL);
    rs_raw(e, s, strlen(s));
}

/* Emit the whole registry as the canonical (sorted-key) JSON object:
 * `{"<key>":<entry_json>,...}`. The edge keys are pure-ASCII dotted
 * identifiers joined by '|' (nothing to escape) and the fragments are
 * pre-canonical, so this is plain concatenation in the table's
 * byte-sorted key order. */
static void rs_emit_schema_sorted(rs_emit_t *e)
{
    size_t n, i;
    const srmech_responsion_entry_t *r;
    assert(e != NULL);
    n = srmech_responsion_registry_count();
    assert(n > 0u);
    rs_cstr(e, "{");
    for (i = 0u; i < n; i++) {
        r = srmech_responsion_registry_get(i);
        assert(r != NULL);
        if (i > 0u) {
            rs_cstr(e, ",");
        }
        rs_cstr(e, "\"");
        rs_cstr(e, r->key);
        rs_cstr(e, "\":");
        rs_raw(e, r->entry_json, r->entry_len);
    }
    rs_cstr(e, "}");
}

srmech_status_t srmech_responsion_schema(char *buf, size_t buf_len,
                                         size_t *out_len)
{
    rs_emit_t e;
    if (out_len == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(buf != NULL || buf_len == 0u);
    assert(out_len != NULL);  /* guaranteed by the early NULL-arg return */
    e.buf = buf;
    e.cap = buf_len;
    e.used = 0u;
    e.overflow = 0;
    rs_emit_schema_sorted(&e);
    *out_len = e.used;
    return e.overflow ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}
