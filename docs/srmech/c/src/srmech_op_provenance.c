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
