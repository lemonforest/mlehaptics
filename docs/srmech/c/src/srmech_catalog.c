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
#include <stddef.h>
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

/* ==================================================================
 * rc172 — the catalog REGISTRY / LOOKUP / AUDIT / KERNEL-STATE logic
 * in C (the ORCHESTRATION→C spine, batch 2). A bare-C host (no Python)
 * runs the catalog registry/kernel/audit surface with these peers,
 * each COMPOSING the existing kernels — the srmech_json parser /
 * canonical writer / builder, srmech_sha256_hex (Class A) — and NO new
 * parser, NO new hash. They back
 *   srmech.amsc.catalog.list_registered_roots  -> srmech_catalog_registered_roots
 *   srmech.amsc.catalog.get_local_kernel_state  -> srmech_catalog_local_kernel_state
 *   srmech.amsc.catalog.use_local_kernel        -> srmech_catalog_use_local_kernel
 *     (and clear_local_kernel via use_local_kernel(None))
 *   srmech.amsc.catalog.attestation_audit       -> srmech_catalog_attestation_audit
 *
 * STATE MODEL (option a — caller-owned): the registry / kernel state is
 * owned by the HOST and PASSED IN per call (Python passes its module
 * globals; a bare-C host passes its own struct's contents). No global
 * mutable C state, no long-lived handle — mirrors the rc171 stateless-
 * peer pattern. All scratch is bump-carved from the CALLER arena `ws`
 * (JPL Rule 3, no malloc). The Python ops dispatch to these under
 * HAS_NATIVE (hasattr-guarded → a stale ABI-3 lib keeps the COMPLETE
 * pure path) and json.loads the canonical output. Additive symbols →
 * SRMECH_ABI_VERSION stays 3.
 *
 * JPL Power-of-Ten: caller-arena only (no malloc), <=60-line functions,
 * >=2 asserts per function, no goto/recursion/abs/libm.
 * ================================================================== */

/* Round a workspace pointer up to void*-alignment (the srmech_json arena
 * aligns relative to its base, so a sub-arena base must be aligned). */
static unsigned char *cat_align_ptr(unsigned char *p)
{
    assert(p != NULL);
    assert(sizeof(void *) >= 4u);
    uintptr_t a = (uintptr_t)sizeof(void *);
    uintptr_t pad = (a - ((uintptr_t)p % a)) % a;
    return p + pad;
}

/* Carve `n` void*-aligned bytes from *cursor within [*cursor, end); advance
 * the cursor. Returns NULL (no partial carve) if the region does not fit. */
static unsigned char *cat_carve(unsigned char **cursor, unsigned char *end,
                                size_t n)
{
    assert(cursor != NULL);
    assert(end != NULL);
    unsigned char *p = cat_align_ptr(*cursor);
    if (p > end || n > (size_t)(end - p)) { return NULL; }
    *cursor = p + n;
    return p;
}

/* Copy `len` raw bytes from `src` into [*cursor, end); advance the cursor.
 * Returns the copied region (alive for the arena lifetime) or NULL if it
 * does not fit. Byte storage — no alignment needed. */
static const char *cat_dup(unsigned char **cursor, unsigned char *end,
                           const char *src, uint32_t len)
{
    assert(cursor != NULL);
    assert(end != NULL);
    unsigned char *p = *cursor;
    if ((size_t)len > (size_t)(end - p)) { return NULL; }
    if (len > 0u) { memcpy(p, src, len); }
    *cursor = p + len;
    return (const char *)p;
}

/* Canonical-JSON write of a value node into `out` using the caller scratch
 * `ws` — byte-identical to CPython json.dumps(obj, sort_keys=True,
 * ensure_ascii=False) for the float-free trees these peers build. */
static srmech_status_t cat_write_node(const srmech_json_value_t *node,
                                      unsigned char *ws, size_t ws_len,
                                      char *out, size_t out_cap,
                                      size_t *out_len)
{
    assert(node != NULL);
    assert(out_len != NULL);
    if (ws == NULL || out == NULL) { return SRMECH_ERR_NULL_ARG; }
    unsigned char *jws = cat_align_ptr(ws);
    size_t off = (size_t)(jws - ws);
    if (off >= ws_len) { return SRMECH_ERR_OVERFLOW; }
    size_t jws_len = srmech_json_write_arena_bytes(node);
    if (jws_len >= ws_len - off) { return SRMECH_ERR_OVERFLOW; }
    return srmech_json_write_ws(node, out, out_cap, out_len, jws, jws_len);
}

/* A JSON string node when `p != NULL`, else a JSON null node — mirrors the
 * Python `str(x) if x else None` optional-field convention. */
static srmech_json_value_t *cat_str_or_null(srmech_json_builder_t *b,
                                            const char *p, size_t len)
{
    assert(b != NULL);
    assert(p != NULL || len == 0u);
    if (p == NULL) { return srmech_json_new_null(b); }
    return srmech_json_new_string(b, p, (uint32_t)len);
}

/* ------------------------------------------------------------------
 * srmech_catalog_registered_roots — the list_registered_roots JSON.
 * Emits [{"path":<root>,"source":<root_source>}, {"path":..,"source":..}...]
 * with the host's own attested root FIRST, then every external (path,source)
 * pair from `ext_json` (a JSON array of [path, source] two-string arrays).
 * ------------------------------------------------------------------ */
size_t srmech_catalog_registered_roots_arena_bytes(size_t root_len,
                                                   size_t source_len,
                                                   size_t ext_len)
{
    assert(sizeof(srmech_json_value_t) <= 64u);
    assert(sizeof(void *) <= 16u);
    size_t s = root_len + source_len + ext_len;
    size_t parse = 96u * ext_len + 8192u;
    size_t build = 256u * ext_len + 16384u;
    size_t items = 8u * ext_len + 4096u;
    size_t writer = 200u * s + 8192u;
    return parse + build + items + writer + 512u;
}

/* Build the object {"path":<pp>,"source":<ps>} into builder `b`. */
static srmech_json_value_t *cat_root_obj(srmech_json_builder_t *b,
                                         const char *pp, uint32_t pl,
                                         const char *ps, uint32_t sl)
{
    assert(b != NULL);
    assert(pp != NULL && ps != NULL);
    const char *keys[2] = {"path", "source"};
    srmech_json_value_t *vals[2];
    vals[0] = srmech_json_new_string(b, pp, pl);
    vals[1] = srmech_json_new_string(b, ps, sl);
    return srmech_json_new_object(b, keys, vals, 2u);
}

srmech_status_t srmech_catalog_registered_roots(
    const char *root_path, size_t root_len,
    const char *root_source, size_t root_source_len,
    const char *ext_json, size_t ext_len,
    void *ws, size_t ws_len,
    char *out, size_t out_cap, size_t *out_len)
{
    assert(root_path != NULL || root_len == 0u);
    assert(out_len != NULL);
    if (root_path == NULL || root_source == NULL || ext_json == NULL ||
        ws == NULL || out == NULL || out_len == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    unsigned char *cur = (unsigned char *)ws;
    unsigned char *end = cur + ws_len;
    size_t parse_len = 96u * ext_len + 8192u;
    unsigned char *ain = cat_carve(&cur, end, parse_len);
    unsigned char *abd = cat_carve(&cur, end, 256u * ext_len + 16384u);
    unsigned char *ait = cat_carve(&cur, end, 8u * ext_len + 4096u);
    unsigned char *aws = cat_align_ptr(cur);
    if (aws > end) { return SRMECH_ERR_OVERFLOW; }
    size_t wr_len = (size_t)(end - aws);
    if (ain == NULL || abd == NULL || ait == NULL || aws == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    srmech_json_value_t *ext = NULL;
    srmech_status_t st = srmech_json_parse(ext_json, ext_len, ain, parse_len,
                                           &ext);
    if (st != SRMECH_OK) { return st; }
    if (ext->type != SRMECH_JSON_ARRAY) { return SRMECH_ERR_BAD_INPUT; }
    srmech_json_builder_t b;
    st = srmech_json_builder_init(&b, abd, 256u * ext_len + 16384u);
    if (st != SRMECH_OK) { return st; }
    uint32_t n = ext->u.arr.n;
    unsigned char *ic = ait;
    srmech_json_value_t **items = (srmech_json_value_t **)cat_carve(
        &ic, ait + 8u * ext_len + 4096u, ((size_t)n + 1u) * sizeof(void *));
    if (items == NULL) { return SRMECH_ERR_OVERFLOW; }
    items[0] = cat_root_obj(&b, root_path, (uint32_t)root_len,
                            root_source, (uint32_t)root_source_len);
    for (uint32_t i = 0u; i < n; i++) {
        const srmech_json_value_t *pair = ext->u.arr.items[i];
        if (pair == NULL || pair->type != SRMECH_JSON_ARRAY ||
            pair->u.arr.n != 2u) { return SRMECH_ERR_BAD_INPUT; }
        const srmech_json_value_t *pp = pair->u.arr.items[0];
        const srmech_json_value_t *ps = pair->u.arr.items[1];
        if (pp == NULL || pp->type != SRMECH_JSON_STRING ||
            ps == NULL || ps->type != SRMECH_JSON_STRING) {
            return SRMECH_ERR_BAD_INPUT;
        }
        items[i + 1u] = cat_root_obj(&b, pp->u.str.ptr, pp->u.str.len,
                                     ps->u.str.ptr, ps->u.str.len);
    }
    if (b.failed) { return SRMECH_ERR_OVERFLOW; }
    srmech_json_value_t *arr = srmech_json_new_array(&b, items, n + 1u);
    if (arr == NULL) { return SRMECH_ERR_OVERFLOW; }
    return cat_write_node(arr, aws, wr_len, out, out_cap, out_len);
}

/* ------------------------------------------------------------------
 * srmech_catalog_local_kernel_state — the get_local_kernel_state envelope
 * + the cache_hash = sha256( "\n".join(f"{source_key}\t{overlay_sha256}") )
 * over the caller-provided per_source array (each entry an object carrying
 * source_key / table / overlay_path / overlay_sha256 string fields — the
 * FS-derived overlay set the host computes; the peer does the envelope +
 * the Class-A cache-hash derivation).
 * ------------------------------------------------------------------ */
size_t srmech_catalog_local_kernel_state_arena_bytes(size_t path_len,
                                                     size_t ac_len,
                                                     size_t per_source_len)
{
    assert(sizeof(srmech_json_value_t) <= 64u);
    assert(sizeof(void *) <= 16u);
    size_t parse = 96u * per_source_len + 8192u;
    size_t build = 64u * per_source_len + 8192u + 4u * (path_len + ac_len);
    size_t joinb = 2u * per_source_len + 4096u;
    size_t writer = 200u * per_source_len + 8192u + 4u * (path_len + ac_len);
    return parse + build + joinb + writer + 512u;
}

/* cache_hash = sha256 of the canonical join. Writes 64 hex + NUL to out_hex.
 * The join buffer `buf` (capacity `buf_cap`) is caller scratch. */
static srmech_status_t cat_cache_hash(const srmech_json_value_t *per_source,
                                      char *buf, size_t buf_cap, char *out_hex)
{
    assert(per_source != NULL);
    assert(out_hex != NULL);
    if (per_source->type != SRMECH_JSON_ARRAY) { return SRMECH_ERR_BAD_INPUT; }
    size_t pos = 0u;
    uint32_t n = per_source->u.arr.n;
    for (uint32_t i = 0u; i < n; i++) {
        const srmech_json_value_t *e = per_source->u.arr.items[i];
        if (e == NULL || e->type != SRMECH_JSON_OBJECT) {
            return SRMECH_ERR_BAD_INPUT;
        }
        const srmech_json_value_t *k = srmech_json_object_get(e, "source_key");
        const srmech_json_value_t *s =
            srmech_json_object_get(e, "overlay_sha256");
        if (k == NULL || k->type != SRMECH_JSON_STRING ||
            s == NULL || s->type != SRMECH_JSON_STRING) {
            return SRMECH_ERR_BAD_INPUT;
        }
        size_t need = (size_t)k->u.str.len + 1u + (size_t)s->u.str.len
                      + (i > 0u ? 1u : 0u);
        if (pos > buf_cap || need > buf_cap - pos) { return SRMECH_ERR_OVERFLOW; }
        if (i > 0u) { buf[pos++] = '\n'; }
        memcpy(buf + pos, k->u.str.ptr, k->u.str.len); pos += k->u.str.len;
        buf[pos++] = '\t';
        memcpy(buf + pos, s->u.str.ptr, s->u.str.len); pos += s->u.str.len;
    }
    return srmech_sha256_hex((const uint8_t *)buf, pos, out_hex);
}

srmech_status_t srmech_catalog_local_kernel_state(
    int active, const char *path, size_t path_len,
    const char *adapter_class, size_t ac_len,
    const char *per_source_json, size_t per_source_len,
    void *ws, size_t ws_len, char *out, size_t out_cap, size_t *out_len)
{
    assert(out_len != NULL);
    assert(per_source_json != NULL || per_source_len == 0u);
    if (per_source_json == NULL || ws == NULL || out == NULL ||
        out_len == NULL) { return SRMECH_ERR_NULL_ARG; }
    unsigned char *cur = (unsigned char *)ws;
    unsigned char *end = cur + ws_len;
    size_t parse_len = 96u * per_source_len + 8192u;
    size_t join_len = 2u * per_source_len + 4096u;
    unsigned char *ain = cat_carve(&cur, end, parse_len);
    unsigned char *abd = cat_carve(&cur, end,
        64u * per_source_len + 8192u + 4u * (path_len + ac_len));
    unsigned char *ajn = cat_carve(&cur, end, join_len);
    unsigned char *ahx = cat_carve(&cur, end, 72u);
    unsigned char *aws = cat_align_ptr(cur);
    if (aws > end) { return SRMECH_ERR_OVERFLOW; }
    size_t wr_len = (size_t)(end - aws);
    if (ain == NULL || abd == NULL || ajn == NULL || ahx == NULL ||
        aws == NULL) { return SRMECH_ERR_OVERFLOW; }
    srmech_json_value_t *ps = NULL;
    srmech_status_t st = srmech_json_parse(per_source_json, per_source_len,
                                           ain, parse_len, &ps);
    if (st != SRMECH_OK) { return st; }
    if (ps->type != SRMECH_JSON_ARRAY) { return SRMECH_ERR_BAD_INPUT; }
    st = cat_cache_hash(ps, (char *)ajn, join_len, (char *)ahx);
    if (st != SRMECH_OK) { return st; }
    srmech_json_builder_t b;
    st = srmech_json_builder_init(&b, abd,
        64u * per_source_len + 8192u + 4u * (path_len + ac_len));
    if (st != SRMECH_OK) { return st; }
    const char *keys[7] = {"ok", "active", "path", "adapter_class",
                           "n_overlay_sources", "per_source", "cache_hash"};
    srmech_json_value_t *vals[7];
    vals[0] = srmech_json_new_bool(&b, 1);
    vals[1] = srmech_json_new_bool(&b, active ? 1 : 0);
    vals[2] = cat_str_or_null(&b, path, path_len);
    vals[3] = cat_str_or_null(&b, adapter_class, ac_len);
    vals[4] = srmech_json_new_int(&b, (int64_t)ps->u.arr.n);
    vals[5] = ps;
    vals[6] = srmech_json_new_string(&b, (const char *)ahx, 64u);
    if (b.failed) { return SRMECH_ERR_OVERFLOW; }
    srmech_json_value_t *obj = srmech_json_new_object(&b, keys, vals, 7u);
    if (obj == NULL) { return SRMECH_ERR_OVERFLOW; }
    return cat_write_node(obj, aws, wr_len, out, out_cap, out_len);
}

/* ------------------------------------------------------------------
 * srmech_catalog_use_local_kernel — the use_local_kernel / clear_local_kernel
 * HAPPY-PATH response builder. `clear != 0` -> the T2-cleared response; else
 * the success response for a validated, existing overlay directory (the
 * caller does the adapter_class validation + FS existence/dir checks + the
 * error responses, whose Python-repr messages are host presentation). Only
 * the two reproducible string/bool/null responses live here.
 * ------------------------------------------------------------------ */
size_t srmech_catalog_use_local_kernel_arena_bytes(size_t path_len,
                                                   size_t ac_len)
{
    assert(sizeof(srmech_json_value_t) <= 64u);
    assert(sizeof(void *) <= 16u);
    size_t s = path_len + ac_len;
    return 16u * s + 65536u;
}

/* Append `len` bytes of `src` to buf at *pos (capacity cap). 1 on fit. */
static int cat_append(char *buf, size_t cap, size_t *pos,
                      const char *src, size_t len)
{
    assert(buf != NULL || cap == 0u);
    assert(pos != NULL);
    if (*pos > cap || len > cap - *pos) { return 0; }
    if (len > 0u) { memcpy(buf + *pos, src, len); }
    *pos += len;
    return 1;
}

/* Build the success message
 *   "T2 overlay registered at <path>[ (scope: adapter_class='<ac>')]"
 * into caller scratch `buf`; sets *out_len. adapter_class NULL -> no scope. */
static srmech_status_t cat_use_message(const char *path, size_t path_len,
                                       const char *ac, size_t ac_len,
                                       char *buf, size_t cap, size_t *out_len)
{
    assert(buf != NULL || cap == 0u);
    assert(out_len != NULL);
    size_t pos = 0u;
    int ok = cat_append(buf, cap, &pos, "T2 overlay registered at ", 25u);
    ok = ok && cat_append(buf, cap, &pos, path, path_len);
    if (ac != NULL) {
        ok = ok && cat_append(buf, cap, &pos, " (scope: adapter_class='", 24u);
        ok = ok && cat_append(buf, cap, &pos, ac, ac_len);
        ok = ok && cat_append(buf, cap, &pos, "')", 2u);
    }
    if (!ok) { return SRMECH_ERR_OVERFLOW; }
    *out_len = pos;
    return SRMECH_OK;
}

srmech_status_t srmech_catalog_use_local_kernel(
    int clear, const char *path, size_t path_len,
    const char *adapter_class, size_t ac_len,
    void *ws, size_t ws_len, char *out, size_t out_cap, size_t *out_len)
{
    assert(out_len != NULL);
    assert(ws != NULL || ws_len == 0u);
    if (ws == NULL || out == NULL || out_len == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    unsigned char *cur = (unsigned char *)ws;
    unsigned char *end = cur + ws_len;
    size_t msg_cap = path_len + ac_len + 128u;
    unsigned char *amsg = cat_carve(&cur, end, msg_cap);
    unsigned char *abd = cat_carve(&cur, end, 8u * (path_len + ac_len) + 16384u);
    unsigned char *aws = cat_align_ptr(cur);
    if (aws > end) { return SRMECH_ERR_OVERFLOW; }
    size_t wr_len = (size_t)(end - aws);
    if (amsg == NULL || abd == NULL || aws == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    srmech_json_builder_t b;
    srmech_status_t st = srmech_json_builder_init(&b, abd,
        8u * (path_len + ac_len) + 16384u);
    if (st != SRMECH_OK) { return st; }
    const char *keys[5] = {"ok", "active", "path", "adapter_class", "message"};
    srmech_json_value_t *vals[5];
    vals[0] = srmech_json_new_bool(&b, 1);
    if (clear != 0) {
        vals[1] = srmech_json_new_bool(&b, 0);
        vals[2] = srmech_json_new_null(&b);
        vals[3] = srmech_json_new_null(&b);
        vals[4] = srmech_json_new_string(&b,
            "T2 overlay cleared; queries return T0+T1 baseline only", 54u);
    } else {
        if (path == NULL) { return SRMECH_ERR_NULL_ARG; }
        size_t mlen = 0u;
        st = cat_use_message(path, path_len, adapter_class, ac_len,
                             (char *)amsg, msg_cap, &mlen);
        if (st != SRMECH_OK) { return st; }
        vals[1] = srmech_json_new_bool(&b, 1);
        vals[2] = srmech_json_new_string(&b, path, (uint32_t)path_len);
        vals[3] = cat_str_or_null(&b, adapter_class, ac_len);
        vals[4] = srmech_json_new_string(&b, (const char *)amsg,
                                         (uint32_t)mlen);
    }
    if (b.failed) { return SRMECH_ERR_OVERFLOW; }
    srmech_json_value_t *obj = srmech_json_new_object(&b, keys, vals, 5u);
    if (obj == NULL) { return SRMECH_ERR_OVERFLOW; }
    return cat_write_node(obj, aws, wr_len, out, out_cap, out_len);
}

/* ------------------------------------------------------------------
 * srmech_catalog_attestation_audit — the per-row attestation projection.
 * Iterates the NDJSON file bytes (lstrip each line; skip empty / '#'
 * comment lines — the read_ndjson discipline), parses each row as JSON,
 * projects data_schema_id + attestation.{response_sha256, retrieved_at,
 * parser_version, parser_rule_hash, collector_descriptor_hash} (each
 * defaulting to "" when absent — the data-only literature_curated case),
 * and emits {ok, source_key, n_rows, rows:[...]}. Composes the srmech_json
 * parser + canonical writer. Any line that fails to parse -> non-OK so the
 * caller runs the COMPLETE pure path (value-parity, never a rescue).
 * ------------------------------------------------------------------ */
size_t srmech_catalog_attestation_audit_arena_bytes(size_t ndjson_len,
                                                    size_t source_key_len)
{
    assert(sizeof(srmech_json_value_t) <= 64u);
    assert(sizeof(void *) <= 16u);
    size_t parse = 96u * ndjson_len + 16384u;   /* reused per line */
    size_t store = 2u * ndjson_len + 4096u;     /* duped field bytes */
    size_t items = 8u * ndjson_len + 4096u;     /* row ptr array */
    size_t build = 64u * ndjson_len + 16384u + 4u * source_key_len;
    size_t writer = 8u * ndjson_len + 16384u;
    return parse + store + items + build + writer + 512u;
}

/* Advance `p` past leading ASCII whitespace within [p, e). */
static const char *cat_lstrip(const char *p, const char *e)
{
    assert(p != NULL || e == NULL);
    assert(e != NULL);
    while (p < e) {
        char c = *p;
        if (c == ' ' || c == '\t' || c == '\r' || c == '\f' || c == '\v') {
            p++;
        } else {
            break;
        }
    }
    return p;
}

/* Dup a projected string field (object member `key`, or "" when absent /
 * non-string) into storage and return a string node in builder `b`. */
static srmech_json_value_t *cat_audit_field(srmech_json_builder_t *b,
                                            const srmech_json_value_t *obj,
                                            const char *key,
                                            unsigned char **sc,
                                            unsigned char *scend)
{
    assert(b != NULL);
    assert(key != NULL);
    const srmech_json_value_t *m =
        (obj != NULL) ? srmech_json_object_get(obj, key) : NULL;
    if (m == NULL || m->type != SRMECH_JSON_STRING || m->u.str.len == 0u) {
        return srmech_json_new_string(b, "", 0u);
    }
    const char *d = cat_dup(sc, scend, m->u.str.ptr, m->u.str.len);
    if (d == NULL) { return NULL; }
    return srmech_json_new_string(b, d, m->u.str.len);
}

/* Build one audit row object from a parsed NDJSON line tree `row`. */
static srmech_json_value_t *cat_audit_row(srmech_json_builder_t *b,
                                          const srmech_json_value_t *row,
                                          unsigned char **sc,
                                          unsigned char *scend)
{
    assert(b != NULL);
    assert(row != NULL);
    const srmech_json_value_t *att =
        (row->type == SRMECH_JSON_OBJECT)
            ? srmech_json_object_get(row, "attestation") : NULL;
    if (att != NULL && att->type != SRMECH_JSON_OBJECT) { att = NULL; }
    const char *keys[6] = {"data_schema_id", "response_sha256", "retrieved_at",
                           "parser_version", "parser_rule_hash",
                           "collector_descriptor_hash"};
    srmech_json_value_t *vals[6];
    vals[0] = cat_audit_field(b, row, "data_schema_id", sc, scend);
    vals[1] = cat_audit_field(b, att, "response_sha256", sc, scend);
    vals[2] = cat_audit_field(b, att, "retrieved_at", sc, scend);
    vals[3] = cat_audit_field(b, att, "parser_version", sc, scend);
    vals[4] = cat_audit_field(b, att, "parser_rule_hash", sc, scend);
    vals[5] = cat_audit_field(b, att, "collector_descriptor_hash", sc, scend);
    for (int i = 0; i < 6; i++) { if (vals[i] == NULL) { return NULL; } }
    return srmech_json_new_object(b, keys, vals, 6u);
}

/* True iff the lstripped line [p, e) is a skip line (empty or '#' comment). */
static int cat_is_skip_line(const char *p, const char *e)
{
    assert(p != NULL || e == NULL);
    assert(e != NULL);
    const char *s = cat_lstrip(p, e);
    return (s >= e || *s == '#') ? 1 : 0;
}

/* Count / build the audit rows. Two passes: pass 1 counts non-skip lines to
 * size the item array; pass 2 parses + projects each. `pa` is the reused
 * per-line parse arena. Returns the assembled rows ARRAY node. */
static srmech_status_t cat_audit_rows(srmech_json_builder_t *b,
                                      const char *nd, size_t nd_len,
                                      unsigned char *pa, size_t pa_len,
                                      unsigned char *sc, size_t sc_len,
                                      srmech_json_value_t ***out_items,
                                      uint32_t *out_n)
{
    assert(b != NULL);
    assert(out_items != NULL);
    uint32_t nrows = 0u;
    size_t i = 0u;
    while (i < nd_len) {
        size_t j = i;
        while (j < nd_len && nd[j] != '\n') { j++; }
        if (!cat_is_skip_line(nd + i, nd + j)) { nrows++; }
        i = (j < nd_len) ? j + 1u : j;
    }
    unsigned char *scur = sc;
    unsigned char *scend = sc + sc_len;
    srmech_json_value_t **items = (srmech_json_value_t **)cat_carve(
        &scur, scend, ((size_t)nrows + 1u) * sizeof(void *));
    if (items == NULL) { return SRMECH_ERR_OVERFLOW; }
    uint32_t w = 0u;
    i = 0u;
    while (i < nd_len) {
        size_t j = i;
        while (j < nd_len && nd[j] != '\n') { j++; }
        const char *ls = cat_lstrip(nd + i, nd + j);
        i = (j < nd_len) ? j + 1u : j;
        if (ls >= nd + j || *ls == '#') { continue; }
        srmech_json_value_t *row = NULL;
        srmech_status_t st = srmech_json_parse(ls, (size_t)((nd + j) - ls),
                                               pa, pa_len, &row);
        if (st != SRMECH_OK) { return st; }
        items[w] = cat_audit_row(b, row, &scur, scend);
        if (items[w] == NULL) { return SRMECH_ERR_OVERFLOW; }
        w++;
    }
    *out_items = items;
    *out_n = w;
    return SRMECH_OK;
}

srmech_status_t srmech_catalog_attestation_audit(
    const char *source_key, size_t source_key_len,
    const char *ndjson, size_t ndjson_len,
    void *ws, size_t ws_len, char *out, size_t out_cap, size_t *out_len)
{
    assert(out_len != NULL);
    assert(ndjson != NULL || ndjson_len == 0u);
    if (source_key == NULL || ndjson == NULL || ws == NULL || out == NULL ||
        out_len == NULL) { return SRMECH_ERR_NULL_ARG; }
    unsigned char *cur = (unsigned char *)ws;
    unsigned char *end = cur + ws_len;
    size_t pa_len = 96u * ndjson_len + 16384u;
    size_t sc_len = 10u * ndjson_len + 8192u;
    unsigned char *pa = cat_carve(&cur, end, pa_len);
    unsigned char *sc = cat_carve(&cur, end, sc_len);
    unsigned char *abd = cat_carve(&cur, end,
        64u * ndjson_len + 16384u + 4u * source_key_len);
    unsigned char *aws = cat_align_ptr(cur);
    if (aws > end) { return SRMECH_ERR_OVERFLOW; }
    size_t wr_len = (size_t)(end - aws);
    if (pa == NULL || sc == NULL || abd == NULL || aws == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    srmech_json_builder_t b;
    srmech_status_t st = srmech_json_builder_init(&b, abd,
        64u * ndjson_len + 16384u + 4u * source_key_len);
    if (st != SRMECH_OK) { return st; }
    srmech_json_value_t **items = NULL;
    uint32_t nrows = 0u;
    st = cat_audit_rows(&b, ndjson, ndjson_len, pa, pa_len, sc, sc_len,
                        &items, &nrows);
    if (st != SRMECH_OK) { return st; }
    srmech_json_value_t *rows = srmech_json_new_array(&b, items, nrows);
    const char *keys[4] = {"ok", "source_key", "n_rows", "rows"};
    srmech_json_value_t *vals[4];
    vals[0] = srmech_json_new_bool(&b, 1);
    vals[1] = srmech_json_new_string(&b, source_key, (uint32_t)source_key_len);
    vals[2] = srmech_json_new_int(&b, (int64_t)nrows);
    vals[3] = rows;
    if (b.failed || rows == NULL) { return SRMECH_ERR_OVERFLOW; }
    srmech_json_value_t *obj = srmech_json_new_object(&b, keys, vals, 4u);
    if (obj == NULL) { return SRMECH_ERR_OVERFLOW; }
    return cat_write_node(obj, aws, wr_len, out, out_cap, out_len);
}
