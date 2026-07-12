/*
 * srmech_op_provenance.c — the canonical op-provenance record hasher
 * (0.9.0rc117; the op-carrying carrier, dives #718/#719).
 *
 * `srmech_op_provenance_hash` is a Class-A COMPOSITE over the existing
 * kernels — it writes no new parser, no new writer, no new hash:
 *
 *   digest = sha256( canonical_json( record MINUS "chain_sha256" ) )
 *
 * Kernels reused (no re-implementation here):
 *   - srmech_json_parse / srmech_json_write_ws   (the §41 canonical JSON
 *     module — writer byte-identical to CPython json.dumps(obj,
 *     sort_keys=True, ensure_ascii=False) for float-free trees)
 *   - srmech_sha256_hex                          (Class A, FIPS 180-4)
 *
 * The record's cached self-hash field "chain_sha256" is stripped from the
 * top-level object before the canonical rewrite, so the pre-image never
 * contains it (a record hashes the same with or without its cache).
 *
 * FLOAT-FREE BY CONSTRUCTION: the op-provenance canonical image tags any
 * float as {"__float64__": "<float.hex>"} (Python side does the tagging).
 * A raw JSON float here would render %.17g — NOT byte-identical to Python
 * repr(float) — silently forking the hash across the mirror, so any
 * number token containing '.', 'e', or 'E' is REJECTED with
 * SRMECH_ERR_BAD_INPUT (a lexical pre-scan; mirrors the Python wrapper's
 * raw-float rejection exactly).
 *
 * Standalone-complete honor: all scratch is bump-carved from the CALLER
 * arena `ws` (no malloc, JPL Rule 3) — front half parses, tail half holds
 * the writer scratch + the canonical bytes. Size `ws` from
 * srmech_op_provenance_hash_arena_bytes(record_len). The Python op
 * `srmech.amsc.op_provenance.op_provenance_hash` is the COMPLETE
 * alternative implementation for no-C hosts (value-parity, not a rescue).
 *
 * JPL Power-of-Ten compliance:
 *   - Rule 1 (no goto / recursion) : OK (the float scan + strip are loops)
 *   - Rule 3 (no malloc)           : OK (caller arena only)
 *   - Rule 4 (<= 60-line fns)      : OK
 *   - Rule 5 (>= 2 asserts per fn) : OK
 *   - Rule 8 (single-line macros)  : OK (none defined)
 */

#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

#include "srmech.h"

/* Lexical float rejection: outside strings, any number token containing
 * '.', 'e', or 'E' would parse to SRMECH_JSON_DOUBLE (whose %.17g
 * rendering is not byte-identical to Python repr) — reject it so the
 * hash can never silently fork. Strings are skipped with \-escape
 * awareness; JSON number tokens start only with '-' or a digit. */
static srmech_status_t opp_reject_floats(const char *src, size_t len)
{
    assert(src != NULL);
    assert(len > 0u);
    int in_str = 0;
    size_t i = 0u;
    while (i < len) {
        char c = src[i];
        if (in_str) {
            if (c == '\\') { i += 2u; continue; }
            if (c == '"') { in_str = 0; }
            i++;
            continue;
        }
        if (c == '"') { in_str = 1; i++; continue; }
        if (c == '-' || (c >= '0' && c <= '9')) {
            int has_frac = 0;
            while (i < len) {
                char d = src[i];
                if ((d >= '0' && d <= '9') || d == '-' || d == '+') {
                    i++;
                } else if (d == '.' || d == 'e' || d == 'E') {
                    has_frac = 1;
                    i++;
                } else {
                    break;
                }
            }
            if (has_frac) { return SRMECH_ERR_BAD_INPUT; }
            continue;
        }
        i++;
    }
    return SRMECH_OK;
}

/* Remove the top-level "chain_sha256" member (the record's cached
 * self-hash) from a parsed OBJECT in place, compacting the key/value
 * arrays — the canonical pre-image never contains it. A non-object root
 * passes through untouched (the hash-any-record contract). */
static void opp_strip_chain(srmech_json_value_t *root)
{
    assert(root != NULL);
    if (root->type != SRMECH_JSON_OBJECT) { return; }
    uint32_t n = root->u.obj.n;
    assert(n == 0u || root->u.obj.keys != NULL);
    uint32_t w = 0u;
    for (uint32_t i = 0u; i < n; i++) {
        if (strcmp(root->u.obj.keys[i], "chain_sha256") == 0) { continue; }
        root->u.obj.keys[w] = root->u.obj.keys[i];
        root->u.obj.vals[w] = root->u.obj.vals[i];
        w++;
    }
    root->u.obj.n = w;
}

size_t srmech_op_provenance_hash_arena_bytes(size_t record_len)
{
    assert(sizeof(srmech_json_value_t) <= 64u);
    assert(sizeof(void *) <= 16u);
    /* Parse side: <= 1 value node per 2 raw bytes (every value spends at
     * least 2 input bytes with its separator) x (node + alignment pad),
     * decoded string/key copies <= raw + NUL each (<= 2x raw total), and
     * container staging arrays with doubling-grow abandonment (<= 4x the
     * final two-pointer-per-child arrays). Each term traces to a real
     * srmech_json_parse allocation. */
    size_t values = record_len / 2u + 8u;
    size_t nodes = values * (sizeof(srmech_json_value_t) + sizeof(void *));
    size_t strings = 2u * record_len + 64u;
    size_t staging = values * 8u * sizeof(void *);
    size_t parse = nodes + strings + staging + 256u;
    /* Writer side: key-sort permutation scratch (<= 2 pointers per key,
     * <= 1 key per value, x2 slop) + the emit-frame stack (bounded by
     * SRMECH_JSON_MAX_DEPTH) — a static over-approximation of
     * srmech_json_write_arena_bytes on any tree this record parses to. */
    size_t writer = values * 4u * sizeof(void *)
                    + (size_t)SRMECH_JSON_MAX_DEPTH * 64u;
    /* Canonical output: sort_keys re-spacing adds <= 1 byte per ':' or
     * ',' (fewer than half the input bytes), so 2x input + slack bounds
     * the emitted bytes. */
    size_t emit = 2u * record_len + 128u;
    /* srmech_op_provenance_hash splits the arena in half (front = parse,
     * tail = writer scratch + canonical bytes): return double the larger
     * side so both halves are sufficient. */
    size_t half = parse;
    if (writer + emit + 64u > half) { half = writer + emit + 64u; }
    return 2u * half + 128u;
}

srmech_status_t srmech_op_provenance_hash(const char *record_json,
                                          size_t record_len,
                                          void *ws, size_t ws_len,
                                          char *out_hex)
{
    assert(record_json != NULL || record_len == 0u);
    assert(ws != NULL || ws_len == 0u);
    if (record_json == NULL || ws == NULL || out_hex == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (record_len == 0u || ws_len < 128u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    srmech_status_t st = opp_reject_floats(record_json, record_len);
    if (st != SRMECH_OK) { return st; }
    /* Front half: the parse arena; tail half: writer scratch + canonical
     * bytes. Both bounded by the caller's arena, never a compiled-in cap. */
    size_t parse_len = ws_len / 2u;
    srmech_json_value_t *root = NULL;
    st = srmech_json_parse(record_json, record_len, ws, parse_len, &root);
    if (st != SRMECH_OK) { return st; }
    opp_strip_chain(root);
    size_t jws_len = srmech_json_write_arena_bytes(root);
    unsigned char *tail = (unsigned char *)ws + parse_len;
    size_t tail_len = ws_len - parse_len;
    size_t pad = (size_t)((uintptr_t)tail % (uintptr_t)sizeof(void *));
    pad = (sizeof(void *) - pad) % sizeof(void *);
    if (pad + jws_len >= tail_len) { return SRMECH_ERR_OVERFLOW; }
    void *jws = tail + pad;
    char *buf = (char *)(tail + pad + jws_len);
    size_t buf_cap = tail_len - pad - jws_len;
    size_t out_len = 0u;
    st = srmech_json_write_ws(root, buf, buf_cap, &out_len, jws, jws_len);
    if (st != SRMECH_OK) { return st; }
    return srmech_sha256_hex((const uint8_t *)buf, out_len, out_hex);
}

/* ==================================================================
 * rc171 — the op-provenance VERDICT / RECORD / RE-VERIFY logic in C.
 *
 * A bare-C host (no Python) builds + compares op-provenance records with
 * these peers, each COMPOSING the existing kernels (no new parser, no new
 * hash): the srmech_json parser / canonical writer / builder,
 * srmech_sha256_hex (Class A), and srmech_op_provenance_hash (the rc117
 * canonical chain hasher). They back
 *   srmech.amsc.op_provenance.op_verdict              -> srmech_op_verdict
 *   srmech.amsc.op_provenance.family_verdict          -> srmech_family_verdict
 *   srmech.amsc.op_provenance.carry (the RECORD)      -> srmech_op_carry
 *   srmech.amsc.op_provenance.lossy_projection_record -> srmech_lossy_projection_record
 *   srmech.amsc.op_provenance.reproject (the RE-VERIFY)-> srmech_op_reproject
 * The Python ops dispatch to these under HAS_NATIVE (hasattr-guarded) and
 * carry the COMPLETE alternative pure path for no-C hosts (value-parity,
 * never a rescue). JPL-clean: caller-arena only (no malloc), <=60-line
 * functions, >=2 asserts, no goto/recursion/abs/libm.
 * ================================================================== */

/* Round a workspace pointer up to void*-alignment (the srmech_json arena
 * bump allocator aligns RELATIVE to its base, so a sub-arena base must be
 * aligned for strict-alignment hosts). Callers reserve alignment slop. */
static unsigned char *opp_align_ptr(unsigned char *p)
{
    assert(p != NULL);
    assert(sizeof(void *) >= 4u);
    uintptr_t a = (uintptr_t)sizeof(void *);
    uintptr_t pad = (a - ((uintptr_t)p % a)) % a;
    return p + pad;
}

/* Carve `n` void*-aligned bytes from *cursor within [*cursor, end); advance
 * the cursor. Returns NULL (no partial carve) if the region does not fit. */
static unsigned char *opp_carve(unsigned char **cursor, unsigned char *end,
                                size_t n)
{
    assert(cursor != NULL);
    assert(end != NULL);
    unsigned char *p = opp_align_ptr(*cursor);
    if (p > end || n > (size_t)(end - p)) { return NULL; }
    *cursor = p + n;
    return p;
}

/* Canonical-JSON + SHA-256 of a value node into out_hex (>=65 bytes) — the
 * op-provenance canonical-image hash of any float-free tree. `ws` is scratch
 * for the writer key-sort + the canonical bytes; bounded by the caller. */
static srmech_status_t opp_hash_node(const srmech_json_value_t *node,
                                     unsigned char *ws, size_t ws_len,
                                     char *out_hex)
{
    assert(node != NULL);
    assert(out_hex != NULL);
    if (ws == NULL) { return SRMECH_ERR_NULL_ARG; }
    unsigned char *jws = opp_align_ptr(ws);
    size_t off = (size_t)(jws - ws);
    if (off >= ws_len) { return SRMECH_ERR_OVERFLOW; }
    size_t avail = ws_len - off;
    size_t jws_len = srmech_json_write_arena_bytes(node);
    if (jws_len + 64u >= avail) { return SRMECH_ERR_OVERFLOW; }
    char *buf = (char *)jws + jws_len;
    size_t buf_cap = avail - jws_len;
    size_t out_len = 0u;
    srmech_status_t st = srmech_json_write_ws(node, buf, buf_cap, &out_len,
                                              jws, jws_len);
    if (st != SRMECH_OK) { return st; }
    return srmech_sha256_hex((const uint8_t *)buf, out_len, out_hex);
}

/* Byte-equality of two JSON string nodes. */
static int opp_str_eq(const srmech_json_value_t *a,
                      const srmech_json_value_t *b)
{
    assert(a != NULL);
    assert(b != NULL);
    if (a->u.str.len != b->u.str.len) { return 0; }
    if (a->u.str.len == 0u) { return 1; }
    return memcmp(a->u.str.ptr, b->u.str.ptr, a->u.str.len) == 0 ? 1 : 0;
}

/* SHA-256 of canonical([key, value]) — one input_sha256 element, matching
 * Python sha256_bytes(_canon_bytes([k, canon_inputs[k]])). `bws` seats a
 * fresh builder for the [key,value] pair; `hws` is opp_hash_node scratch. */
static srmech_status_t opp_input_hash(const char *key,
                                      srmech_json_value_t *val,
                                      unsigned char *bws, size_t bws_len,
                                      unsigned char *hws, size_t hws_len,
                                      char *out_hex)
{
    assert(key != NULL);
    assert(val != NULL);
    srmech_json_builder_t b;
    srmech_status_t st = srmech_json_builder_init(&b, bws, bws_len);
    if (st != SRMECH_OK) { return st; }
    srmech_json_value_t *items[2];
    items[0] = srmech_json_new_string(&b, key, (uint32_t)strlen(key));
    items[1] = val;
    srmech_json_value_t *pair = srmech_json_new_array(&b, items, 2u);
    if (b.failed || pair == NULL) { return SRMECH_ERR_OVERFLOW; }
    return opp_hash_node(pair, hws, hws_len, out_hex);
}

/* Sort object key indices into `order` by byte-wise key comparison (== the
 * CPython sorted(dict) order over UTF-8 keys). Insertion sort (n is the tiny
 * operand-arity). */
static void opp_sort_key_indices(const char *const *keys, uint32_t n,
                                 uint32_t *order)
{
    assert(keys != NULL || n == 0u);
    assert(order != NULL || n == 0u);
    for (uint32_t i = 0u; i < n; i++) { order[i] = i; }
    for (uint32_t i = 1u; i < n; i++) {
        uint32_t cur = order[i];
        uint32_t j = i;
        while (j > 0u && strcmp(keys[order[j - 1u]], keys[cur]) > 0) {
            order[j] = order[j - 1u];
            j--;
        }
        order[j] = cur;
    }
}

/* leaves_exact = NO leaf is an INEXACT tag ({"__float64__"} / {"__complex128__"}).
 * Iterative (JPL Rule 1): a caller worklist `stack` of node pointers. Matches
 * Python _canon's exact flag (float/complex leaves are the only inexact ones). */
static srmech_status_t opp_leaves_exact(srmech_json_value_t *root,
                                        srmech_json_value_t **stack,
                                        size_t stack_cap, int *out_exact)
{
    assert(root != NULL);
    assert(out_exact != NULL);
    if (stack == NULL || stack_cap == 0u) { return SRMECH_ERR_OVERFLOW; }
    size_t sp = 0u;
    stack[sp++] = root;
    *out_exact = 1;
    while (sp > 0u) {
        srmech_json_value_t *v = stack[--sp];
        if (v == NULL) { continue; }
        if (v->type == SRMECH_JSON_OBJECT) {
            const char *k0 = v->u.obj.n == 1u ? v->u.obj.keys[0] : NULL;
            if (k0 != NULL && (strcmp(k0, "__float64__") == 0 ||
                               strcmp(k0, "__complex128__") == 0)) {
                *out_exact = 0;
                return SRMECH_OK;
            }
            for (uint32_t k = 0u; k < v->u.obj.n; k++) {
                if (sp >= stack_cap) { return SRMECH_ERR_OVERFLOW; }
                stack[sp++] = v->u.obj.vals[k];
            }
        } else if (v->type == SRMECH_JSON_ARRAY) {
            for (uint32_t k = 0u; k < v->u.arr.n; k++) {
                if (sp >= stack_cap) { return SRMECH_ERR_OVERFLOW; }
                stack[sp++] = v->u.arr.items[k];
            }
        }
    }
    return SRMECH_OK;
}

/* Build the input_sha256 ARRAY node (sorted-key order) into builder `b`, from
 * the parsed canonical inputs OBJECT. `hx` holds the alive hex strings + the
 * order/items scratch; `pws`/`hws` back the per-key pair build + hash. */
static srmech_status_t opp_build_input_sha256(
    srmech_json_builder_t *b, srmech_json_value_t *inputs,
    unsigned char *hx, size_t hx_len,
    unsigned char *pws, size_t pws_len,
    unsigned char *hws, size_t hws_len,
    srmech_json_value_t **out_array)
{
    assert(b != NULL);
    assert(inputs != NULL);
    if (inputs->type != SRMECH_JSON_OBJECT) { return SRMECH_ERR_BAD_INPUT; }
    uint32_t n = inputs->u.obj.n;
    unsigned char *cur = hx;
    unsigned char *end = hx + hx_len;
    uint32_t *order = (uint32_t *)opp_carve(&cur, end, (n + 1u) * 4u);
    srmech_json_value_t **items =
        (srmech_json_value_t **)opp_carve(&cur, end, (n + 1u) * sizeof(void *));
    char *hexbuf = (char *)opp_carve(&cur, end, (size_t)(n + 1u) * 65u);
    if (order == NULL || items == NULL || hexbuf == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    opp_sort_key_indices(inputs->u.obj.keys, n, order);
    for (uint32_t i = 0u; i < n; i++) {
        uint32_t idx = order[i];
        char *hex = hexbuf + (size_t)i * 65u;
        srmech_status_t st = opp_input_hash(inputs->u.obj.keys[idx],
                                            inputs->u.obj.vals[idx],
                                            pws, pws_len, hws, hws_len, hex);
        if (st != SRMECH_OK) { return st; }
        items[i] = srmech_json_new_string(b, hex, 64u);
        if (items[i] == NULL) { return SRMECH_ERR_OVERFLOW; }
    }
    *out_array = srmech_json_new_array(b, items, n);
    return (*out_array == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* Assemble the record {base keys...} then APPEND chain_sha256 (== the record's
 * own canonical hash, the rc117 op_provenance_hash of the chain-less image) and
 * emit canonical JSON into out_json. `keys`/`vals` hold `n` base members and
 * MUST have room for one more (the chain). `hws` is hash + write scratch. */
static srmech_status_t opp_finalize_record(
    srmech_json_builder_t *b, const char **keys, srmech_json_value_t **vals,
    uint32_t n, unsigned char *hws, size_t hws_len,
    char *out_json, size_t out_cap, size_t *out_len)
{
    assert(b != NULL);
    assert(keys != NULL && vals != NULL);
    srmech_json_value_t *rec0 = srmech_json_new_object(b, keys, vals, n);
    if (rec0 == NULL) { return SRMECH_ERR_OVERFLOW; }
    char chain_hex[65];
    srmech_status_t st = opp_hash_node(rec0, hws, hws_len, chain_hex);
    if (st != SRMECH_OK) { return st; }
    keys[n] = "chain_sha256";
    vals[n] = srmech_json_new_string(b, chain_hex, 64u);
    srmech_json_value_t *rec1 = srmech_json_new_object(b, keys, vals, n + 1u);
    if (vals[n] == NULL || rec1 == NULL) { return SRMECH_ERR_OVERFLOW; }
    unsigned char *jws = opp_align_ptr(hws);
    size_t off = (size_t)(jws - hws);
    if (off >= hws_len) { return SRMECH_ERR_OVERFLOW; }
    size_t jws_len = srmech_json_write_arena_bytes(rec1);
    if (jws_len >= hws_len - off) { return SRMECH_ERR_OVERFLOW; }
    return srmech_json_write_ws(rec1, out_json, out_cap, out_len, jws, jws_len);
}

/* ------------------------------------------------------------------
 * srmech_op_verdict — EQUAL / UNKNOWN over the canonical chain hash.
 * ------------------------------------------------------------------ */
size_t srmech_op_verdict_arena_bytes(size_t r1_len, size_t r2_len)
{
    assert(sizeof(srmech_json_value_t) <= 64u);
    assert(sizeof(void *) <= 16u);
    size_t m = (r1_len > r2_len) ? r1_len : r2_len;
    return srmech_op_provenance_hash_arena_bytes(m);
}

srmech_status_t srmech_op_verdict(const char *r1_json, size_t r1_len,
                                  const char *r2_json, size_t r2_len,
                                  void *ws, size_t ws_len, int *out_equal)
{
    assert(r1_json != NULL || r1_len == 0u);
    assert(out_equal != NULL);
    if (r1_json == NULL || r2_json == NULL || ws == NULL ||
        out_equal == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    char hex1[65];
    char hex2[65];
    srmech_status_t st = srmech_op_provenance_hash(r1_json, r1_len, ws, ws_len,
                                                   hex1);
    if (st != SRMECH_OK) { return st; }
    st = srmech_op_provenance_hash(r2_json, r2_len, ws, ws_len, hex2);
    if (st != SRMECH_OK) { return st; }
    *out_equal = (strcmp(hex1, hex2) == 0) ? 1 : 0;
    return SRMECH_OK;
}

/* ------------------------------------------------------------------
 * srmech_family_verdict — SAME_TARGET / UNKNOWN over the family address.
 * ------------------------------------------------------------------ */
size_t srmech_family_verdict_arena_bytes(size_t r1_len, size_t r2_len)
{
    assert(sizeof(srmech_json_value_t) <= 64u);
    assert(sizeof(void *) <= 16u);
    return 200u * (r1_len + r2_len) + 16384u;
}

/* The family string member `key` of a record's "family" object, or NULL.
 * `rec` is a parsed root (non-NULL); a non-object / missing family / missing
 * or non-string member all return NULL. */
static const srmech_json_value_t *opp_family_member(
    const srmech_json_value_t *rec, const char *key)
{
    assert(rec != NULL);
    assert(key != NULL);
    if (rec->type != SRMECH_JSON_OBJECT) { return NULL; }
    const srmech_json_value_t *fam = srmech_json_object_get(rec, "family");
    if (fam == NULL || fam->type != SRMECH_JSON_OBJECT) { return NULL; }
    const srmech_json_value_t *m = srmech_json_object_get(fam, key);
    if (m == NULL || m->type != SRMECH_JSON_STRING) { return NULL; }
    return m;
}

srmech_status_t srmech_family_verdict(const char *r1_json, size_t r1_len,
                                      const char *r2_json, size_t r2_len,
                                      void *ws, size_t ws_len, int *out_same)
{
    assert(r1_json != NULL || r1_len == 0u);
    assert(out_same != NULL);
    if (r1_json == NULL || r2_json == NULL || ws == NULL ||
        out_same == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    unsigned char *cur = (unsigned char *)ws;
    unsigned char *end = cur + ws_len;
    size_t half = ws_len / 2u;
    unsigned char *a1 = opp_carve(&cur, end, half);
    unsigned char *a2 = opp_carve(&cur, end, (size_t)(end - cur));
    if (a1 == NULL || a2 == NULL) { return SRMECH_ERR_OVERFLOW; }
    srmech_json_value_t *r1 = NULL;
    srmech_json_value_t *r2 = NULL;
    srmech_status_t st = srmech_json_parse(r1_json, r1_len, a1, half, &r1);
    if (st != SRMECH_OK) { return st; }
    st = srmech_json_parse(r2_json, r2_len, a2, (size_t)(end - a2), &r2);
    if (st != SRMECH_OK) { return st; }
    const srmech_json_value_t *t1 = opp_family_member(r1, "target_id");
    const srmech_json_value_t *t2 = opp_family_member(r2, "target_id");
    const srmech_json_value_t *k1 = opp_family_member(r1, "tower_kind");
    const srmech_json_value_t *k2 = opp_family_member(r2, "tower_kind");
    int named = (t1 != NULL && t1->u.str.len > 0u && t2 != NULL &&
                 opp_str_eq(t1, t2));
    int tower = ((k1 == NULL && k2 == NULL) ||
                 (k1 != NULL && k2 != NULL && opp_str_eq(k1, k2)));
    *out_same = (named && tower) ? 1 : 0;
    return SRMECH_OK;
}

/* ------------------------------------------------------------------
 * srmech_op_carry — build the CARRIED-op provenance record (the provenance
 * face of carry(); the numeric `value` is the Python/C runner's job). Parses
 * the canonical inputs / params / family / rung, hashes the inputs, derives
 * leaves_exact, and appends the chain hash.
 * ------------------------------------------------------------------ */
enum { OPP_CARRY_NREG = 7 };

/* Region sizes for srmech_op_carry's caller arena, shared by the sizer and the
 * builder so they never drift: 0 inputs / 1 params / 2 family / 3 rung parse
 * arenas, 4 builder, 5 hex+order+items, 6 hash/write/leaves scratch. */
static void opp_carry_regions(size_t il, size_t pl, size_t fl, size_t rl,
                              size_t out[OPP_CARRY_NREG])
{
    assert(out != NULL);
    assert(il + pl + fl + rl >= il);
    size_t s = il + pl + fl + rl;
    out[0] = 96u * il + 8192u;
    out[1] = 96u * pl + 8192u;
    out[2] = 96u * fl + 8192u;
    out[3] = 96u * rl + 8192u;
    out[4] = 256u * il + 16384u;
    out[5] = 160u * il + 4096u;
    out[6] = 512u * s + 131072u;
}

size_t srmech_op_carry_arena_bytes(size_t inputs_len, size_t params_len,
                                   size_t family_len, size_t rung_len)
{
    assert(sizeof(srmech_json_value_t) <= 64u);
    assert(sizeof(void *) <= 16u);
    size_t reg[OPP_CARRY_NREG];
    opp_carry_regions(inputs_len, params_len, family_len, rung_len, reg);
    size_t total = 256u;
    for (int i = 0; i < OPP_CARRY_NREG; i++) { total += reg[i] + 16u; }
    return total;
}

/* Assemble + emit the carry record given the 4 parsed trees + arenas. `sc`
 * is the scratch region (leaves stack + per-key pair + hash/write). */
static srmech_status_t opp_carry_emit(
    const char *op, size_t op_len, srmech_json_value_t *inputs,
    srmech_json_value_t *params, srmech_json_value_t *family,
    srmech_json_value_t *rung, unsigned char *bd, size_t bd_len,
    unsigned char *hx, size_t hx_len, unsigned char *sc, size_t sc_len,
    char *out_json, size_t out_cap, size_t *out_len)
{
    assert(inputs != NULL);
    assert(out_len != NULL);
    unsigned char *scur = sc;
    unsigned char *send = sc + sc_len;
    size_t leaf_len = sc_len / 8u;
    size_t pair_len = sc_len / 4u;
    unsigned char *lstk = opp_carve(&scur, send, leaf_len);
    unsigned char *pws = opp_carve(&scur, send, pair_len);
    size_t hws_len = (size_t)(send - scur);
    unsigned char *hws = opp_carve(&scur, send, hws_len);
    if (lstk == NULL || pws == NULL || hws == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    int le = 1;
    srmech_status_t st = opp_leaves_exact(
        inputs, (srmech_json_value_t **)lstk, leaf_len / sizeof(void *), &le);
    if (st != SRMECH_OK) { return st; }
    srmech_json_builder_t b;
    st = srmech_json_builder_init(&b, bd, bd_len);
    if (st != SRMECH_OK) { return st; }
    srmech_json_value_t *arr = NULL;
    st = opp_build_input_sha256(&b, inputs, hx, hx_len, pws, pair_len,
                                hws, hws_len, &arr);
    if (st != SRMECH_OK) { return st; }
    const char *keys[8] = {"op", "params", "input_sha256", "family", "rung",
                           "leaves_exact", NULL, NULL};
    srmech_json_value_t *vals[8];
    vals[0] = srmech_json_new_string(&b, op, (uint32_t)op_len);
    vals[1] = params;
    vals[2] = arr;
    vals[3] = family;
    vals[4] = rung;
    vals[5] = srmech_json_new_bool(&b, le);
    if (b.failed) { return SRMECH_ERR_OVERFLOW; }
    return opp_finalize_record(&b, keys, vals, 6u, hws, hws_len,
                               out_json, out_cap, out_len);
}

srmech_status_t srmech_op_carry(
    const char *op, size_t op_len,
    const char *inputs_json, size_t inputs_len,
    const char *params_json, size_t params_len,
    const char *family_json, size_t family_len,
    const char *rung_json, size_t rung_len,
    void *ws, size_t ws_len,
    char *out_json, size_t out_cap, size_t *out_len)
{
    assert(op != NULL || op_len == 0u);
    assert(out_len != NULL);
    if (op == NULL || inputs_json == NULL || params_json == NULL ||
        family_json == NULL || rung_json == NULL || ws == NULL ||
        out_json == NULL || out_len == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    srmech_status_t st = opp_reject_floats(inputs_json, inputs_len);
    if (st == SRMECH_OK) { st = opp_reject_floats(params_json, params_len); }
    if (st == SRMECH_OK) { st = opp_reject_floats(rung_json, rung_len); }
    if (st != SRMECH_OK) { return st; }
    size_t reg[OPP_CARRY_NREG];
    opp_carry_regions(inputs_len, params_len, family_len, rung_len, reg);
    unsigned char *cur = (unsigned char *)ws;
    unsigned char *end = cur + ws_len;
    unsigned char *ain = opp_carve(&cur, end, reg[0]);
    unsigned char *apa = opp_carve(&cur, end, reg[1]);
    unsigned char *afa = opp_carve(&cur, end, reg[2]);
    unsigned char *aru = opp_carve(&cur, end, reg[3]);
    unsigned char *abd = opp_carve(&cur, end, reg[4]);
    unsigned char *ahx = opp_carve(&cur, end, reg[5]);
    unsigned char *asc = opp_carve(&cur, end, reg[6]);
    if (ain == NULL || apa == NULL || afa == NULL || aru == NULL ||
        abd == NULL || ahx == NULL || asc == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    srmech_json_value_t *in = NULL;
    srmech_json_value_t *pa = NULL;
    srmech_json_value_t *fa = NULL;
    srmech_json_value_t *ru = NULL;
    st = srmech_json_parse(inputs_json, inputs_len, ain, reg[0], &in);
    if (st == SRMECH_OK) {
        st = srmech_json_parse(params_json, params_len, apa, reg[1], &pa);
    }
    if (st == SRMECH_OK) {
        st = srmech_json_parse(family_json, family_len, afa, reg[2], &fa);
    }
    if (st == SRMECH_OK) {
        st = srmech_json_parse(rung_json, rung_len, aru, reg[3], &ru);
    }
    if (st != SRMECH_OK) { return st; }
    return opp_carry_emit(op, op_len, in, pa, fa, ru, abd, reg[4], ahx,
                          reg[5], asc, reg[6], out_json, out_cap, out_len);
}

/* ------------------------------------------------------------------
 * srmech_lossy_projection_record — the exact-in/exact-out LOSSY-PROJECTION
 * record (rc125): family=null, params={}, rung={}, a projection_kind string,
 * and the derived leaves_exact + chain hash. Only the canonical inputs parse.
 * ------------------------------------------------------------------ */

/* Assemble + emit the lossy-projection record given the parsed inputs tree. */
static srmech_status_t opp_lossy_emit(
    const char *op, size_t op_len, srmech_json_value_t *inputs,
    const char *projection_kind, size_t pk_len,
    unsigned char *bd, size_t bd_len, unsigned char *hx, size_t hx_len,
    unsigned char *sc, size_t sc_len,
    char *out_json, size_t out_cap, size_t *out_len)
{
    assert(inputs != NULL);
    assert(out_len != NULL);
    unsigned char *scur = sc;
    unsigned char *send = sc + sc_len;
    size_t leaf_len = sc_len / 8u;
    size_t pair_len = sc_len / 4u;
    unsigned char *lstk = opp_carve(&scur, send, leaf_len);
    unsigned char *pws = opp_carve(&scur, send, pair_len);
    size_t hws_len = (size_t)(send - scur);
    unsigned char *hws = opp_carve(&scur, send, hws_len);
    if (lstk == NULL || pws == NULL || hws == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    int le = 1;
    srmech_status_t st = opp_leaves_exact(
        inputs, (srmech_json_value_t **)lstk, leaf_len / sizeof(void *), &le);
    if (st != SRMECH_OK) { return st; }
    srmech_json_builder_t b;
    st = srmech_json_builder_init(&b, bd, bd_len);
    if (st != SRMECH_OK) { return st; }
    srmech_json_value_t *arr = NULL;
    st = opp_build_input_sha256(&b, inputs, hx, hx_len, pws, pair_len,
                                hws, hws_len, &arr);
    if (st != SRMECH_OK) { return st; }
    const char *keys[8] = {"op", "params", "input_sha256", "family", "rung",
                           "projection_kind", "leaves_exact", NULL};
    srmech_json_value_t *vals[8];
    vals[0] = srmech_json_new_string(&b, op, (uint32_t)op_len);
    vals[1] = srmech_json_new_object(&b, NULL, NULL, 0u);
    vals[2] = arr;
    vals[3] = srmech_json_new_null(&b);
    vals[4] = srmech_json_new_object(&b, NULL, NULL, 0u);
    vals[5] = srmech_json_new_string(&b, projection_kind, (uint32_t)pk_len);
    vals[6] = srmech_json_new_bool(&b, le);
    if (b.failed) { return SRMECH_ERR_OVERFLOW; }
    return opp_finalize_record(&b, keys, vals, 7u, hws, hws_len,
                               out_json, out_cap, out_len);
}

size_t srmech_lossy_projection_record_arena_bytes(size_t inputs_len)
{
    assert(sizeof(srmech_json_value_t) <= 64u);
    assert(sizeof(void *) <= 16u);
    size_t il = inputs_len;
    size_t total = 256u;
    total += (96u * il + 8192u) + 16u;      /* inputs parse   */
    total += (256u * il + 16384u) + 16u;    /* builder        */
    total += (160u * il + 4096u) + 16u;     /* hex+order+items*/
    total += (512u * il + 131072u) + 16u;   /* scratch        */
    return total;
}

srmech_status_t srmech_lossy_projection_record(
    const char *op, size_t op_len,
    const char *inputs_json, size_t inputs_len,
    const char *projection_kind, size_t pk_len,
    void *ws, size_t ws_len,
    char *out_json, size_t out_cap, size_t *out_len)
{
    assert(op != NULL || op_len == 0u);
    assert(out_len != NULL);
    if (op == NULL || inputs_json == NULL || projection_kind == NULL ||
        ws == NULL || out_json == NULL || out_len == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    srmech_status_t st = opp_reject_floats(inputs_json, inputs_len);
    if (st != SRMECH_OK) { return st; }
    unsigned char *cur = (unsigned char *)ws;
    unsigned char *end = cur + ws_len;
    unsigned char *ain = opp_carve(&cur, end, 96u * inputs_len + 8192u);
    unsigned char *abd = opp_carve(&cur, end, 256u * inputs_len + 16384u);
    unsigned char *ahx = opp_carve(&cur, end, 160u * inputs_len + 4096u);
    unsigned char *asc = opp_carve(&cur, end, (size_t)(end - cur));
    if (ain == NULL || abd == NULL || ahx == NULL || asc == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    srmech_json_value_t *in = NULL;
    st = srmech_json_parse(inputs_json, inputs_len, ain,
                           96u * inputs_len + 8192u, &in);
    if (st != SRMECH_OK) { return st; }
    return opp_lossy_emit(op, op_len, in, projection_kind, pk_len, abd,
                          256u * inputs_len + 16384u, ahx,
                          160u * inputs_len + 4096u, asc,
                          (size_t)(end - asc), out_json, out_cap, out_len);
}

/* ------------------------------------------------------------------
 * srmech_op_reproject — MPM re-verification: do the supplied canonical inputs
 * re-hash to the record's input_sha256 array (element-wise, sorted order)?
 * out_ok = 1 if so (a re-projection may proceed), 0 if not (broken provenance
 * or different inputs). Composes the srmech_json parser + srmech_sha256_hex.
 * ------------------------------------------------------------------ */

/* Re-hash the sorted canonical inputs and compare element-wise against the
 * record's input_sha256 array (out_ok=1 iff every element + the count match). */
static srmech_status_t opp_reproject_check(
    srmech_json_value_t *rec, srmech_json_value_t *inputs,
    unsigned char *hx, size_t hx_len, unsigned char *pws, size_t pws_len,
    unsigned char *hws, size_t hws_len, int *out_ok)
{
    assert(rec != NULL);
    assert(inputs != NULL);
    assert(out_ok != NULL);
    *out_ok = 0;
    if (rec->type != SRMECH_JSON_OBJECT ||
        inputs->type != SRMECH_JSON_OBJECT) {
        return SRMECH_ERR_BAD_INPUT;
    }
    const srmech_json_value_t *arr =
        srmech_json_object_get(rec, "input_sha256");
    if (arr == NULL || arr->type != SRMECH_JSON_ARRAY) {
        return SRMECH_ERR_BAD_INPUT;
    }
    uint32_t n = inputs->u.obj.n;
    if (arr->u.arr.n != n) { return SRMECH_OK; }   /* count mismatch -> 0 */
    unsigned char *cur = hx;
    uint32_t *order = (uint32_t *)opp_carve(&cur, hx + hx_len, (n + 1u) * 4u);
    if (order == NULL) { return SRMECH_ERR_OVERFLOW; }
    opp_sort_key_indices(inputs->u.obj.keys, n, order);
    for (uint32_t i = 0u; i < n; i++) {
        uint32_t idx = order[i];
        char hex[65];
        srmech_status_t st = opp_input_hash(inputs->u.obj.keys[idx],
                                            inputs->u.obj.vals[idx],
                                            pws, pws_len, hws, hws_len, hex);
        if (st != SRMECH_OK) { return st; }
        const srmech_json_value_t *e = arr->u.arr.items[i];
        if (e == NULL || e->type != SRMECH_JSON_STRING ||
            e->u.str.len != 64u || memcmp(e->u.str.ptr, hex, 64u) != 0) {
            return SRMECH_OK;   /* element mismatch -> out_ok stays 0 */
        }
    }
    *out_ok = 1;
    return SRMECH_OK;
}

size_t srmech_op_reproject_arena_bytes(size_t record_len, size_t inputs_len)
{
    assert(sizeof(srmech_json_value_t) <= 64u);
    assert(sizeof(void *) <= 16u);
    return 200u * (record_len + inputs_len) + 131072u;
}

srmech_status_t srmech_op_reproject(const char *record_json, size_t record_len,
                                    const char *inputs_json, size_t inputs_len,
                                    void *ws, size_t ws_len, int *out_ok)
{
    assert(record_json != NULL || record_len == 0u);
    assert(out_ok != NULL);
    if (record_json == NULL || inputs_json == NULL || ws == NULL ||
        out_ok == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    *out_ok = 0;
    srmech_status_t rf = opp_reject_floats(inputs_json, inputs_len);
    if (rf != SRMECH_OK) { return rf; }
    unsigned char *cur = (unsigned char *)ws;
    unsigned char *end = cur + ws_len;
    unsigned char *arc = opp_carve(&cur, end, 96u * record_len + 8192u);
    unsigned char *ain = opp_carve(&cur, end, 96u * inputs_len + 8192u);
    unsigned char *ahx = opp_carve(&cur, end, 160u * inputs_len + 4096u);
    unsigned char *pws = opp_carve(&cur, end, 96u * inputs_len + 8192u);
    size_t hws_len = (size_t)(end - cur);
    unsigned char *hws = opp_carve(&cur, end, hws_len);
    if (arc == NULL || ain == NULL || ahx == NULL || pws == NULL ||
        hws == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    srmech_json_value_t *rec = NULL;
    srmech_json_value_t *in = NULL;
    srmech_status_t st = srmech_json_parse(record_json, record_len, arc,
                                           96u * record_len + 8192u, &rec);
    if (st == SRMECH_OK) {
        st = srmech_json_parse(inputs_json, inputs_len, ain,
                               96u * inputs_len + 8192u, &in);
    }
    if (st != SRMECH_OK) { return st; }
    return opp_reproject_check(rec, in, ahx, 160u * inputs_len + 4096u,
                               pws, 96u * inputs_len + 8192u, hws, hws_len,
                               out_ok);
}
