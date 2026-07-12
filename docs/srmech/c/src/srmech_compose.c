/* srmech_compose.c — the amsc.compose LINEAR CHAIN-RUNNER parse + validate
 * foundation in C (0.9.0rc173; the ORCHESTRATION→C spine, batch 3).
 *
 * A bare-C host (no Python) reads an operator-chain descriptor and must
 * PARSE + VALIDATE its `[[catalog.operator_chain]]` blocks before it can
 * run them. These two peers do exactly that, COMPOSING the existing
 * srmech_json parser / builder / canonical writer — NO new parser, NO new
 * math. They back the Python ops
 *   srmech.amsc.compose.parse_chain_spec     -> srmech_chain_spec_parse
 *   srmech.amsc.compose.parse_catalog_chains -> srmech_chain_catalog_parse
 *
 * SCOPE (honest split, rc173): PARSE + VALIDATE only. The chain RUN loop
 * (resolve_chain / run_chain) is NOT here — it dispatches ARBITRARY srmech
 * ops (heterogeneous kwargs signatures) over the LIVE Python object graph
 * (importlib + getattr + reference resolution against runtime step
 * outputs), which needs a bounded-op FFI + a uniform value carrier — a
 * multi-part foundation, scoped as rc174 (NOT the bounded ~10 cascade
 * atoms; those are a SEPARATE srmech.dsl surface).
 *
 * CONTRACT: input is JSON (the Python dict, json.dumps'd). On success each
 * peer writes the normalized spec(s) as canonical JSON — byte-identical to
 * CPython json.dumps(obj, sort_keys=True, ensure_ascii=False) — into `out`
 * (NO trailing NUL) and sets *out_len. `args` are OMITTED from the output:
 * the Python caller re-attaches them from the ORIGINAL dict so arg-object
 * identity/type is preserved exactly. On ANY validation failure or non-JSON
 * input the peer returns non-OK so the Python caller runs the COMPLETE pure
 * path (value-parity, never a rescue; the specific ChainSpecError message is
 * raised there). All scratch is bump-carved from the caller arena `ws`
 * (size it with the matching *_arena_bytes). Output is float-free.
 *
 * JPL Power-of-Ten: caller-arena only (no malloc), <=60-line functions,
 * >=2 asserts per function, no goto/recursion/abs/libm. Additive symbols →
 * SRMECH_ABI_VERSION stays 3 (the Python ctypes shim hasattr-guards them).
 */

#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

#include "srmech.h"

/* ------------------------------------------------------------------
 * Arena helpers (the rc172 catalog convention: align-then-remainder).
 * ------------------------------------------------------------------ */

/* Round a workspace pointer up to void*-alignment (json sub-arenas align
 * relative to their base, so a sub-arena base must be aligned). */
static unsigned char *co_align_ptr(unsigned char *p)
{
    assert(p != NULL);
    assert(sizeof(void *) >= 4u);
    uintptr_t a = (uintptr_t)sizeof(void *);
    uintptr_t pad = (a - ((uintptr_t)p % a)) % a;
    return p + pad;
}

/* Carve `n` void*-aligned bytes from *cursor within [*cursor, end); advance
 * the cursor. Returns NULL (no partial carve) if the region does not fit. */
static unsigned char *co_carve(unsigned char **cursor, unsigned char *end,
                               size_t n)
{
    assert(cursor != NULL);
    assert(end != NULL);
    unsigned char *p = co_align_ptr(*cursor);
    if (p > end || n > (size_t)(end - p)) { return NULL; }
    *cursor = p + n;
    return p;
}

/* Canonical-JSON write of `node` into `out` using caller scratch `ws` —
 * byte-identical to json.dumps(obj, sort_keys=True, ensure_ascii=False). */
static srmech_status_t co_write_node(const srmech_json_value_t *node,
                                     unsigned char *ws, size_t ws_len,
                                     char *out, size_t out_cap,
                                     size_t *out_len)
{
    assert(node != NULL);
    assert(out_len != NULL);
    if (ws == NULL || out == NULL) { return SRMECH_ERR_NULL_ARG; }
    unsigned char *jws = co_align_ptr(ws);
    size_t off = (size_t)(jws - ws);
    if (off >= ws_len) { return SRMECH_ERR_OVERFLOW; }
    size_t jws_len = srmech_json_write_arena_bytes(node);
    if (jws_len >= ws_len - off) { return SRMECH_ERR_OVERFLOW; }
    return srmech_json_write_ws(node, out, out_cap, out_len, jws, jws_len);
}

/* ------------------------------------------------------------------
 * Scalar validators (mirror compose.py's constants + regex grammar).
 * ------------------------------------------------------------------ */

/* A legal chain / step error policy (LEGAL_ERROR_POLICIES). */
static int co_legal_on_error(const char *s, uint32_t len)
{
    assert(s != NULL || len == 0u);
    assert(len < 0x7fffffffu);
    if (len == 5u && memcmp(s, "raise", 5u) == 0) { return 1; }
    if (len == 16u && memcmp(s, "warn_return_none", 16u) == 0) { return 1; }
    if (len == 4u && memcmp(s, "skip", 4u) == 0) { return 1; }
    return 0;
}

/* A legal class id: a single letter A..N (DEFAULT_CLASS_REGISTRY keys). */
static int co_class_valid(const char *s, uint32_t len)
{
    assert(s != NULL || len == 0u);
    assert(len < 0x7fffffffu);
    return (len == 1u && s[0] >= 'A' && s[0] <= 'N') ? 1 : 0;
}

/* Fetch OBJECT member `key` as a string; 1 on present-and-string. */
static int co_get_string(const srmech_json_value_t *obj, const char *key,
                         const char **out_ptr, uint32_t *out_len)
{
    assert(obj != NULL);
    assert(key != NULL);
    const srmech_json_value_t *m = srmech_json_object_get(obj, key);
    if (m == NULL || m->type != SRMECH_JSON_STRING) { return 0; }
    *out_ptr = m->u.str.ptr;
    *out_len = m->u.str.len;
    return 1;
}

/* ------------------------------------------------------------------
 * Reference-DSL grammar: @<namespace>.<path> where namespace is one of
 * row/input/step/catalog and path is one-or-more of `.<ident>` or `[N]`.
 * @step must start with [N]; N must be < the current step index. Mirrors
 * compose._REFERENCE_PATTERN + _validate_reference. Hand-rolled (no regex
 * lib, no recursion).
 * ------------------------------------------------------------------ */

/* Match the namespace token at *pp (up to the first '.' / '['); advance *pp
 * to the path start; set *is_step. 1 on a known namespace. */
static int co_match_namespace(const char **pp, const char *e, int *is_step)
{
    assert(pp != NULL && *pp != NULL);
    assert(is_step != NULL);
    const char *s = *pp;
    const char *p = s;
    while (p < e && *p != '.' && *p != '[') { p++; }
    size_t nl = (size_t)(p - s);
    *is_step = 0;
    if (nl == 3u && memcmp(s, "row", 3u) == 0) { *pp = p; return 1; }
    if (nl == 5u && memcmp(s, "input", 5u) == 0) { *pp = p; return 1; }
    if (nl == 4u && memcmp(s, "step", 4u) == 0) { *pp = p; *is_step = 1; return 1; }
    if (nl == 7u && memcmp(s, "catalog", 7u) == 0) { *pp = p; return 1; }
    return 0;
}

/* Consume a `.<ident>` segment at *pp (ident = [A-Za-z_][A-Za-z0-9_]*).
 * 1 on a well-formed segment; advances *pp. */
static int co_scan_dot(const char **pp, const char *e)
{
    assert(pp != NULL && *pp != NULL);
    assert(e != NULL);
    const char *p = *pp + 1;   /* skip '.' */
    if (p >= e) { return 0; }
    char c = *p;
    if (!((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || c == '_')) {
        return 0;
    }
    p++;
    while (p < e && (((*p >= 'A') && (*p <= 'Z')) || ((*p >= 'a') && (*p <= 'z'))
           || ((*p >= '0') && (*p <= '9')) || *p == '_')) { p++; }
    *pp = p;
    return 1;
}

/* Consume a `[N]` segment at *pp; store N in *idx. 1 on a well-formed
 * segment; advances *pp. */
static int co_scan_index(const char **pp, const char *e, int64_t *idx)
{
    assert(pp != NULL && *pp != NULL);
    assert(idx != NULL);
    const char *p = *pp + 1;   /* skip '[' */
    if (p >= e || *p < '0' || *p > '9') { return 0; }
    int64_t num = 0;
    while (p < e && *p >= '0' && *p <= '9') {
        if (num < 1000000000) { num = num * 10 + (*p - '0'); }
        p++;
    }
    if (p >= e || *p != ']') { return 0; }
    *pp = p + 1;
    *idx = num;
    return 1;
}

/* Validate the path portion [p, e) + (for @step) the leading-index bound. */
static int co_scan_path(const char *p, const char *e, int is_step,
                        int64_t step_index)
{
    assert(p != NULL);
    assert(e != NULL);
    if (p >= e) { return 0; }                /* path non-empty (regex `+`) */
    if (is_step && *p != '[') { return 0; }  /* @step must start with [N] */
    int first = 1;
    int64_t first_idx = -1;
    while (p < e) {
        if (*p == '.') {
            if (!co_scan_dot(&p, e)) { return 0; }
        } else if (*p == '[') {
            int64_t idx = 0;
            if (!co_scan_index(&p, e, &idx)) { return 0; }
            if (is_step && first) { first_idx = idx; }
        } else {
            return 0;
        }
        first = 0;
    }
    if (is_step && (first_idx < 0 || first_idx >= step_index)) { return 0; }
    return 1;
}

/* Full reference validation for a single `@...` string. */
static int co_ref_valid(const char *ref, uint32_t len, int64_t step_index)
{
    assert(ref != NULL);
    assert(step_index >= 0);
    if (len < 2u || ref[0] != '@') { return 0; }
    const char *p = ref + 1;
    const char *e = ref + len;
    int is_step = 0;
    if (!co_match_namespace(&p, e, &is_step)) { return 0; }
    return co_scan_path(p, e, is_step, step_index);
}

/* Walk an args value tree (non-recursive, explicit stack); validate every
 * string that begins with '@'. Mirrors compose._walk_args (dict VALUES +
 * list items only). BAD_INPUT on a bad ref; OVERFLOW if the stack is short. */
static srmech_status_t co_args_refs_status(
    const srmech_json_value_t *root, int64_t step_index,
    const srmech_json_value_t **stack, size_t cap)
{
    assert(stack != NULL || cap == 0u);
    assert(step_index >= 0);
    size_t sp = 0u;
    if (root == NULL) { return SRMECH_OK; }
    if (sp >= cap) { return SRMECH_ERR_OVERFLOW; }
    stack[sp++] = root;
    while (sp > 0u) {
        const srmech_json_value_t *nd = stack[--sp];
        if (nd == NULL) { continue; }
        if (nd->type == SRMECH_JSON_STRING) {
            if (nd->u.str.len > 0u && nd->u.str.ptr[0] == '@' &&
                !co_ref_valid(nd->u.str.ptr, nd->u.str.len, step_index)) {
                return SRMECH_ERR_BAD_INPUT;
            }
        } else if (nd->type == SRMECH_JSON_ARRAY) {
            for (uint32_t i = 0u; i < nd->u.arr.n; i++) {
                if (sp >= cap) { return SRMECH_ERR_OVERFLOW; }
                stack[sp++] = nd->u.arr.items[i];
            }
        } else if (nd->type == SRMECH_JSON_OBJECT) {
            for (uint32_t i = 0u; i < nd->u.obj.n; i++) {
                if (sp >= cap) { return SRMECH_ERR_OVERFLOW; }
                stack[sp++] = nd->u.obj.vals[i];
            }
        }
    }
    return SRMECH_OK;
}

/* ------------------------------------------------------------------
 * Step + chain assembly (build the normalized canonical-JSON nodes).
 * ------------------------------------------------------------------ */

/* Resolve a step's optional on_error into a JSON node (null when absent /
 * JSON-null, mirroring raw_step.get("on_error")). NULL out on illegal. */
static srmech_json_value_t *co_step_on_error(srmech_json_builder_t *b,
                                             const srmech_json_value_t *step)
{
    assert(b != NULL);
    assert(step != NULL);
    const srmech_json_value_t *oe = srmech_json_object_get(step, "on_error");
    if (oe == NULL || oe->type == SRMECH_JSON_NULL) {
        return srmech_json_new_null(b);
    }
    if (oe->type == SRMECH_JSON_STRING &&
        co_legal_on_error(oe->u.str.ptr, oe->u.str.len)) {
        return srmech_json_new_string(b, oe->u.str.ptr, oe->u.str.len);
    }
    return NULL;   /* illegal on_error -> caller returns BAD_INPUT */
}

/* Validate + build one step object {class_id, on_error, op}. */
static srmech_status_t co_build_step(
    srmech_json_builder_t *b, const srmech_json_value_t *step,
    int64_t step_index, const srmech_json_value_t **stack, size_t stack_cap,
    srmech_json_value_t **out_node)
{
    assert(b != NULL);
    assert(out_node != NULL);
    if (step == NULL || step->type != SRMECH_JSON_OBJECT) {
        return SRMECH_ERR_BAD_INPUT;
    }
    const char *cls_p, *op_p;
    uint32_t cls_l, op_l;
    if (!co_get_string(step, "class", &cls_p, &cls_l) ||
        !co_class_valid(cls_p, cls_l) ||
        !co_get_string(step, "op", &op_p, &op_l)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    const srmech_json_value_t *args = srmech_json_object_get(step, "args");
    if (args == NULL || args->type != SRMECH_JSON_OBJECT) {
        return SRMECH_ERR_BAD_INPUT;
    }
    srmech_json_value_t *oe = co_step_on_error(b, step);
    if (oe == NULL) { return SRMECH_ERR_BAD_INPUT; }
    srmech_status_t st = co_args_refs_status(args, step_index, stack, stack_cap);
    if (st != SRMECH_OK) { return st; }
    const char *keys[3] = {"class_id", "on_error", "op"};
    srmech_json_value_t *vals[3];
    vals[0] = srmech_json_new_string(b, cls_p, cls_l);
    vals[1] = oe;
    vals[2] = srmech_json_new_string(b, op_p, op_l);
    *out_node = srmech_json_new_object(b, keys, vals, 3u);
    return (*out_node == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* Validate the chain scalar head; fill the name/summary/returns/on_error
 * string spans + the steps array node. Mirrors parse_chain_spec's field
 * checks (present-and-string; on_error default "raise", present-null->error;
 * steps a non-empty list). */
static srmech_status_t co_chain_head(
    const srmech_json_value_t *chain,
    const char **nm, uint32_t *nml, const char **sm, uint32_t *sml,
    const char **rt, uint32_t *rtl, const char **oe, uint32_t *oel,
    const srmech_json_value_t **steps_out)
{
    assert(chain != NULL);
    assert(steps_out != NULL);
    if (!co_get_string(chain, "name", nm, nml) ||
        !co_get_string(chain, "summary", sm, sml) ||
        !co_get_string(chain, "returns", rt, rtl)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    const srmech_json_value_t *steps = srmech_json_object_get(chain, "steps");
    if (steps == NULL || steps->type != SRMECH_JSON_ARRAY ||
        steps->u.arr.n == 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    *steps_out = steps;
    const srmech_json_value_t *o = srmech_json_object_get(chain, "on_error");
    *oe = "raise";
    *oel = 5u;
    if (o != NULL) {   /* present (incl. JSON-null) -> must be a legal string */
        if (o->type != SRMECH_JSON_STRING ||
            !co_legal_on_error(o->u.str.ptr, o->u.str.len)) {
            return SRMECH_ERR_BAD_INPUT;
        }
        *oe = o->u.str.ptr;
        *oel = o->u.str.len;
    }
    return SRMECH_OK;
}

/* Build the steps array (each step validated + assembled). `items_ws` is a
 * pointer-scratch region carved fresh from its base each call (safe to reuse
 * across chains since new_array copies). */
static srmech_status_t co_build_steps(
    srmech_json_builder_t *b, const srmech_json_value_t *steps,
    const srmech_json_value_t **stack, size_t stack_cap,
    unsigned char *items_ws, size_t items_ws_len,
    srmech_json_value_t **out_arr)
{
    assert(b != NULL);
    assert(out_arr != NULL);
    uint32_t ns = steps->u.arr.n;
    unsigned char *ic = items_ws;
    srmech_json_value_t **items = (srmech_json_value_t **)co_carve(
        &ic, items_ws + items_ws_len, (size_t)ns * sizeof(void *));
    if (items == NULL) { return SRMECH_ERR_OVERFLOW; }
    for (uint32_t i = 0u; i < ns; i++) {
        srmech_json_value_t *snode = NULL;
        srmech_status_t st = co_build_step(b, steps->u.arr.items[i],
                                           (int64_t)i, stack, stack_cap, &snode);
        if (st != SRMECH_OK) { return st; }
        items[i] = snode;
    }
    *out_arr = srmech_json_new_array(b, items, ns);
    return (*out_arr == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* Validate + build one chain into the normalized spec object
 * {name, on_error, returns, steps, summary}. */
static srmech_status_t co_build_chain(
    srmech_json_builder_t *b, const srmech_json_value_t *chain,
    const srmech_json_value_t **stack, size_t stack_cap,
    unsigned char *items_ws, size_t items_ws_len,
    srmech_json_value_t **out_node)
{
    assert(b != NULL);
    assert(out_node != NULL);
    if (chain == NULL || chain->type != SRMECH_JSON_OBJECT) {
        return SRMECH_ERR_BAD_INPUT;
    }
    const char *nm, *sm, *rt, *oe;
    uint32_t nml, sml, rtl, oel;
    const srmech_json_value_t *steps = NULL;
    srmech_status_t st = co_chain_head(chain, &nm, &nml, &sm, &sml,
                                       &rt, &rtl, &oe, &oel, &steps);
    if (st != SRMECH_OK) { return st; }
    srmech_json_value_t *steps_arr = NULL;
    st = co_build_steps(b, steps, stack, stack_cap, items_ws, items_ws_len,
                        &steps_arr);
    if (st != SRMECH_OK) { return st; }
    const char *keys[5] = {"name", "on_error", "returns", "steps", "summary"};
    srmech_json_value_t *vals[5];
    vals[0] = srmech_json_new_string(b, nm, nml);
    vals[1] = srmech_json_new_string(b, oe, oel);
    vals[2] = srmech_json_new_string(b, rt, rtl);
    vals[3] = steps_arr;
    vals[4] = srmech_json_new_string(b, sm, sml);
    *out_node = srmech_json_new_object(b, keys, vals, 5u);
    return (*out_node == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* ------------------------------------------------------------------
 * srmech_chain_spec_parse — parse_chain_spec: one chain block JSON ->
 * one normalized spec (canonical JSON) or non-OK.
 * ------------------------------------------------------------------ */
size_t srmech_chain_spec_parse_arena_bytes(size_t chain_len)
{
    assert(sizeof(srmech_json_value_t) <= 64u);
    assert(sizeof(void *) <= 16u);
    size_t parse = 96u * chain_len + 16384u;
    size_t build = 96u * chain_len + 16384u;
    size_t stack = sizeof(void *) * (2u * chain_len + 512u);
    size_t items = sizeof(void *) * (chain_len + 64u);
    size_t writer = 200u * chain_len + 16384u;
    return parse + build + stack + items + writer + 512u;
}

srmech_status_t srmech_chain_spec_parse(
    const char *chain_json, size_t chain_len,
    void *ws, size_t ws_len, char *out, size_t out_cap, size_t *out_len)
{
    assert(out_len != NULL);
    assert(chain_json != NULL || chain_len == 0u);
    if (chain_json == NULL || ws == NULL || out == NULL || out_len == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    unsigned char *cur = (unsigned char *)ws;
    unsigned char *end = cur + ws_len;
    size_t parse_len = 96u * chain_len + 16384u;
    size_t stack_cap = 2u * chain_len + 512u;
    size_t items_bytes = sizeof(void *) * (chain_len + 64u);
    unsigned char *ain = co_carve(&cur, end, parse_len);
    unsigned char *abd = co_carve(&cur, end, 96u * chain_len + 16384u);
    unsigned char *ast = co_carve(&cur, end, sizeof(void *) * stack_cap);
    unsigned char *ait = co_carve(&cur, end, items_bytes);
    unsigned char *aws = co_align_ptr(cur);
    if (aws > end) { return SRMECH_ERR_OVERFLOW; }
    size_t wr_len = (size_t)(end - aws);
    if (ain == NULL || abd == NULL || ast == NULL || ait == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    srmech_json_value_t *tree = NULL;
    srmech_status_t st = srmech_json_parse(chain_json, chain_len, ain,
                                           parse_len, &tree);
    if (st != SRMECH_OK) { return st; }
    srmech_json_builder_t b;
    st = srmech_json_builder_init(&b, abd, 96u * chain_len + 16384u);
    if (st != SRMECH_OK) { return st; }
    srmech_json_value_t *spec = NULL;
    st = co_build_chain(&b, tree, (const srmech_json_value_t **)ast, stack_cap,
                        ait, items_bytes, &spec);
    if (st != SRMECH_OK) { return st; }
    if (b.failed) { return SRMECH_ERR_OVERFLOW; }
    return co_write_node(spec, aws, wr_len, out, out_cap, out_len);
}

/* ------------------------------------------------------------------
 * srmech_chain_catalog_parse — parse_catalog_chains: an object
 * {chain_schema_version, operator_chain:[...]} -> [spec, ...] canonical
 * JSON, or non-OK. Composes co_build_chain. The Python caller returns []
 * for an empty operator_chain BEFORE dispatch (so nc >= 1 here in practice).
 * ------------------------------------------------------------------ */
size_t srmech_chain_catalog_parse_arena_bytes(size_t cat_len)
{
    assert(sizeof(srmech_json_value_t) <= 64u);
    assert(sizeof(void *) <= 16u);
    size_t parse = 96u * cat_len + 16384u;
    size_t build = 96u * cat_len + 16384u;
    size_t stack = sizeof(void *) * (2u * cat_len + 512u);
    size_t items = sizeof(void *) * (cat_len + 64u);
    size_t specs = sizeof(void *) * (cat_len + 64u);
    size_t writer = 200u * cat_len + 16384u;
    return parse + build + stack + items + specs + writer + 512u;
}

/* Version-check + per-chain build + array assembly + write (kept out of the
 * entry point so it stays under the JPL 60-line bound). */
static srmech_status_t co_catalog_body(
    const srmech_json_value_t *tree,
    unsigned char *abd, size_t abd_len,
    const srmech_json_value_t **stack, size_t stack_cap,
    unsigned char *ait, size_t items_bytes,
    unsigned char *asp, size_t specs_bytes,
    unsigned char *aws, size_t wr_len,
    char *out, size_t out_cap, size_t *out_len)
{
    assert(tree != NULL);
    assert(out_len != NULL);
    const srmech_json_value_t *chains =
        srmech_json_object_get(tree, "operator_chain");
    if (chains == NULL || chains->type != SRMECH_JSON_ARRAY) {
        return SRMECH_ERR_BAD_INPUT;
    }
    const srmech_json_value_t *ver =
        srmech_json_object_get(tree, "chain_schema_version");
    if (ver == NULL || ver->type != SRMECH_JSON_INT || ver->u.i != 1) {
        return SRMECH_ERR_BAD_INPUT;
    }
    srmech_json_builder_t b;
    srmech_status_t st = srmech_json_builder_init(&b, abd, abd_len);
    if (st != SRMECH_OK) { return st; }
    uint32_t nc = chains->u.arr.n;
    unsigned char *sc = asp;
    srmech_json_value_t **specs = (srmech_json_value_t **)co_carve(
        &sc, asp + specs_bytes, (size_t)nc * sizeof(void *));
    if (specs == NULL) { return SRMECH_ERR_OVERFLOW; }
    for (uint32_t i = 0u; i < nc; i++) {
        srmech_json_value_t *spec = NULL;
        st = co_build_chain(&b, chains->u.arr.items[i], stack, stack_cap,
                            ait, items_bytes, &spec);
        if (st != SRMECH_OK) { return st; }
        specs[i] = spec;
    }
    srmech_json_value_t *arr = srmech_json_new_array(&b, specs, nc);
    if (arr == NULL || b.failed) { return SRMECH_ERR_OVERFLOW; }
    return co_write_node(arr, aws, wr_len, out, out_cap, out_len);
}

srmech_status_t srmech_chain_catalog_parse(
    const char *cat_json, size_t cat_len,
    void *ws, size_t ws_len, char *out, size_t out_cap, size_t *out_len)
{
    assert(out_len != NULL);
    assert(cat_json != NULL || cat_len == 0u);
    if (cat_json == NULL || ws == NULL || out == NULL || out_len == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    unsigned char *cur = (unsigned char *)ws;
    unsigned char *end = cur + ws_len;
    size_t parse_len = 96u * cat_len + 16384u;
    size_t stack_cap = 2u * cat_len + 512u;
    size_t items_bytes = sizeof(void *) * (cat_len + 64u);
    size_t specs_bytes = sizeof(void *) * (cat_len + 64u);
    unsigned char *ain = co_carve(&cur, end, parse_len);
    unsigned char *abd = co_carve(&cur, end, 96u * cat_len + 16384u);
    unsigned char *ast = co_carve(&cur, end, sizeof(void *) * stack_cap);
    unsigned char *ait = co_carve(&cur, end, items_bytes);
    unsigned char *asp = co_carve(&cur, end, specs_bytes);
    unsigned char *aws = co_align_ptr(cur);
    if (aws > end) { return SRMECH_ERR_OVERFLOW; }
    size_t wr_len = (size_t)(end - aws);
    if (ain == NULL || abd == NULL || ast == NULL || ait == NULL ||
        asp == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    srmech_json_value_t *tree = NULL;
    srmech_status_t st = srmech_json_parse(cat_json, cat_len, ain, parse_len,
                                           &tree);
    if (st != SRMECH_OK) { return st; }
    if (tree->type != SRMECH_JSON_OBJECT) { return SRMECH_ERR_BAD_INPUT; }
    return co_catalog_body(tree, abd, 96u * cat_len + 16384u,
                           (const srmech_json_value_t **)ast, stack_cap,
                           ait, items_bytes, asp, specs_bytes,
                           aws, wr_len, out, out_cap, out_len);
}

/* ------------------------------------------------------------------
 * srmech_catalog_list_chains — list_catalog_chains: an object
 * {chain_schema_version, operator_chain:[...]} -> a chain-summary array
 * [{classes, n_steps, name, on_error, returns, summary}, ...] canonical JSON,
 * or non-OK (0.9.0rc175; the ORCHESTRATION→C spine, batch 5).
 *
 * COMPOSES co_build_chain (the rc173 parse+validate) and PROJECTS each
 * normalized spec to its summary: the per-step class_id sequence (``classes``),
 * the step count (``n_steps``), plus name / on_error / returns / summary. A
 * bare-C host lists a catalog's registered operator chains with this peer + the
 * srmech_toml parser (Python passes the descriptor's [catalog] table json.dumps'd
 * as {chain_schema_version, operator_chain}). Any validation failure or non-JSON
 * input -> non-OK so the Python caller runs the COMPLETE pure path.
 * ------------------------------------------------------------------ */

/* Reuse a builder-owned OBJECT member node as a value (the summary references
 * the spec's already-built string nodes; new_object copies the pointer + the
 * write walk only reads it). De-const is safe: the node lives in the builder
 * arena for the whole build->write and is never mutated. */
static srmech_json_value_t *co_member(const srmech_json_value_t *obj,
                                      const char *key)
{
    assert(obj != NULL);
    assert(key != NULL);
    return (srmech_json_value_t *)srmech_json_object_get(obj, key);
}

/* Validate + build one chain, then PROJECT it to the summary object
 * {classes, n_steps, name, on_error, returns, summary}. Composes co_build_chain
 * (full validation) + reads back the normalized spec's members. `items_ws` is
 * reused for the classes pointer array AFTER co_build_chain (its steps array is
 * already copied into the spec, so the region is free). */
static srmech_status_t co_build_chain_summary(
    srmech_json_builder_t *b, const srmech_json_value_t *chain,
    const srmech_json_value_t **stack, size_t stack_cap,
    unsigned char *items_ws, size_t items_ws_len,
    srmech_json_value_t **out_node)
{
    assert(b != NULL);
    assert(out_node != NULL);
    srmech_json_value_t *spec = NULL;
    srmech_status_t st = co_build_chain(b, chain, stack, stack_cap,
                                        items_ws, items_ws_len, &spec);
    if (st != SRMECH_OK) { return st; }
    const srmech_json_value_t *steps = srmech_json_object_get(spec, "steps");
    if (steps == NULL || steps->type != SRMECH_JSON_ARRAY) {
        return SRMECH_ERR_BAD_INPUT;
    }
    uint32_t ns = steps->u.arr.n;
    unsigned char *ic = items_ws;
    srmech_json_value_t **cls = (srmech_json_value_t **)co_carve(
        &ic, items_ws + items_ws_len, (size_t)ns * sizeof(void *) + 1u);
    if (cls == NULL) { return SRMECH_ERR_OVERFLOW; }
    for (uint32_t i = 0u; i < ns; i++) {
        cls[i] = co_member(steps->u.arr.items[i], "class_id");
        if (cls[i] == NULL) { return SRMECH_ERR_BAD_INPUT; }
    }
    const char *keys[6] = {"classes", "n_steps", "name", "on_error",
                           "returns", "summary"};
    srmech_json_value_t *vals[6];
    vals[0] = srmech_json_new_array(b, cls, ns);
    vals[1] = srmech_json_new_int(b, (int64_t)ns);
    vals[2] = co_member(spec, "name");
    vals[3] = co_member(spec, "on_error");
    vals[4] = co_member(spec, "returns");
    vals[5] = co_member(spec, "summary");
    if (vals[0] == NULL || vals[1] == NULL || vals[2] == NULL ||
        vals[3] == NULL || vals[4] == NULL || vals[5] == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    *out_node = srmech_json_new_object(b, keys, vals, 6u);
    return (*out_node == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

size_t srmech_catalog_list_chains_arena_bytes(size_t cat_len)
{
    assert(sizeof(srmech_json_value_t) <= 64u);
    assert(sizeof(void *) <= 16u);
    return srmech_chain_catalog_parse_arena_bytes(cat_len);
}

/* Version-check + per-chain summary + array assembly + write (kept out of the
 * entry point so it stays under the JPL 60-line bound). */
static srmech_status_t co_list_body(
    const srmech_json_value_t *tree,
    unsigned char *abd, size_t abd_len,
    const srmech_json_value_t **stack, size_t stack_cap,
    unsigned char *ait, size_t items_bytes,
    unsigned char *asp, size_t specs_bytes,
    unsigned char *aws, size_t wr_len,
    char *out, size_t out_cap, size_t *out_len)
{
    assert(tree != NULL);
    assert(out_len != NULL);
    const srmech_json_value_t *chains =
        srmech_json_object_get(tree, "operator_chain");
    if (chains == NULL || chains->type != SRMECH_JSON_ARRAY) {
        return SRMECH_ERR_BAD_INPUT;
    }
    const srmech_json_value_t *ver =
        srmech_json_object_get(tree, "chain_schema_version");
    if (ver == NULL || ver->type != SRMECH_JSON_INT || ver->u.i != 1) {
        return SRMECH_ERR_BAD_INPUT;
    }
    srmech_json_builder_t b;
    srmech_status_t st = srmech_json_builder_init(&b, abd, abd_len);
    if (st != SRMECH_OK) { return st; }
    uint32_t nc = chains->u.arr.n;
    unsigned char *sc = asp;
    srmech_json_value_t **specs = (srmech_json_value_t **)co_carve(
        &sc, asp + specs_bytes, (size_t)nc * sizeof(void *) + 1u);
    if (specs == NULL) { return SRMECH_ERR_OVERFLOW; }
    for (uint32_t i = 0u; i < nc; i++) {
        srmech_json_value_t *sm = NULL;
        st = co_build_chain_summary(&b, chains->u.arr.items[i], stack, stack_cap,
                                    ait, items_bytes, &sm);
        if (st != SRMECH_OK) { return st; }
        specs[i] = sm;
    }
    srmech_json_value_t *arr = srmech_json_new_array(&b, specs, nc);
    if (arr == NULL || b.failed) { return SRMECH_ERR_OVERFLOW; }
    return co_write_node(arr, aws, wr_len, out, out_cap, out_len);
}

srmech_status_t srmech_catalog_list_chains(
    const char *cat_json, size_t cat_len,
    void *ws, size_t ws_len, char *out, size_t out_cap, size_t *out_len)
{
    assert(out_len != NULL);
    assert(cat_json != NULL || cat_len == 0u);
    if (cat_json == NULL || ws == NULL || out == NULL || out_len == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    unsigned char *cur = (unsigned char *)ws;
    unsigned char *end = cur + ws_len;
    size_t parse_len = 96u * cat_len + 16384u;
    size_t stack_cap = 2u * cat_len + 512u;
    size_t items_bytes = sizeof(void *) * (cat_len + 64u);
    size_t specs_bytes = sizeof(void *) * (cat_len + 64u);
    unsigned char *ain = co_carve(&cur, end, parse_len);
    unsigned char *abd = co_carve(&cur, end, 96u * cat_len + 16384u);
    unsigned char *ast = co_carve(&cur, end, sizeof(void *) * stack_cap);
    unsigned char *ait = co_carve(&cur, end, items_bytes);
    unsigned char *asp = co_carve(&cur, end, specs_bytes);
    unsigned char *aws = co_align_ptr(cur);
    if (aws > end) { return SRMECH_ERR_OVERFLOW; }
    size_t wr_len = (size_t)(end - aws);
    if (ain == NULL || abd == NULL || ast == NULL || ait == NULL ||
        asp == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    srmech_json_value_t *tree = NULL;
    srmech_status_t st = srmech_json_parse(cat_json, cat_len, ain, parse_len,
                                           &tree);
    if (st != SRMECH_OK) { return st; }
    if (tree->type != SRMECH_JSON_OBJECT) { return SRMECH_ERR_BAD_INPUT; }
    return co_list_body(tree, abd, 96u * cat_len + 16384u,
                        (const srmech_json_value_t **)ast, stack_cap,
                        ait, items_bytes, asp, specs_bytes,
                        aws, wr_len, out, out_cap, out_len);
}
