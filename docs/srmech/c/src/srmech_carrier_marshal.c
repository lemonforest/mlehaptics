/* srmech_carrier_marshal.c — the NESTED exact-ℚ carrier OPERAND marshal
 * (0.9.0rc191; the #796 LINCHPIN foundation, batch: carrier-FFI widening).
 *
 * The bignum-safe reader that lowers the MCP nested-ℚ wire form of the §76
 * "telescope" reducer operands (the exact-ℚ carriers Poly / BiPoly) into
 * arena-backed srmech_bigint coefficient arrays — extending the rc176
 * srmech_infer.c `inf_read_poly` pattern ONE nesting level per carrier, in a
 * REUSABLE (external-linkage) form the rc192 srmech_infer.c wiring calls to
 * dispatch the deferred exact #796 infer rows (sigma-definite / q / elliptic)
 * for a bare-C host.
 *
 * WHY THIS IS A SEPARATE SURFACE (the rc191 SCOPE finding). The task framed
 * these reducers as dispatching through the rc188 invoke_tool VTABLE, but two
 * measured facts make the vtable the WRONG home for the §76 reducers:
 *   (1) ARENA SCALE. The reducer C kernels need MB–GB caller workspaces
 *       (srmech_gosper ~9 MB, srmech_wz_verify ~32 MB, srmech_zeilberger
 *       ~470 MB for their exact-ℚ RREF / creative-telescoping scratch), sized
 *       by srmech_infer_arena_bytes (~41 MB). The invoke_tool marshalling
 *       arena is srmech_invoke_tool_arena_bytes = 256*params_len + 65536
 *       (~114 KB) and JPL Rule 3 forbids malloc — so a reducer thunk carving
 *       its ws from the vtable arena ALWAYS overflows → always defers. The
 *       reducers already run in the srmech_infer.c path, which sizes the arena
 *       correctly; THAT is their home (rc176 sigma-gosper; rc192 the rest).
 *   (2) RESULT SHAPE. The reducer MCP results serialise (json.dumps default=
 *       repr) to Python repr() STRINGS carrying only metadata — e.g.
 *       {"num":"Poly(degree=1, exact-rational)", ...} / {"order":1,"coeffs":
 *       [...],"certificate":"BiPoly(k_degree=1, exact-ℚ[n,k])"} — NOT exact-ℚ
 *       coefficient structures. The infer ROUTER emits a small DECISION
 *       literal instead (the rc176 form), which IS byte-reproducible.
 * So rc191 ships the OPERAND MARSHAL FOUNDATION (this file) + a round-trip
 * prover; rc192 wires it into srmech_infer.c (the arena-correct DECISION path).
 *
 * WIRE FORM (mirrors srmech.mcp._coercion _to_poly / _to_bipoly + the reducer
 * carriers' Poly.from_coeffs / BiPoly.coerce acceptance):
 *   * a COEFFICIENT is an exact rational — a bare integer c (den 1) OR a
 *     [num, den] 2-list; each scalar is a JSON int64 OR a decimal STRING (the
 *     rc176 bignum transport, since srmech_json's strtoll clamps a >int64
 *     literal — a bignum coefficient rides as a decimal string, never clamped).
 *   * a Poly  is an ascending-degree LIST of coefficients.
 *   * a BiPoly is a k-ascending LIST of Poly-in-n (each a coefficient LIST),
 *     lowered to FLAT (k-then-n) num/den arrays + a per-k length array klen[]
 *     + the k-degree slot count kdeg — the exact encoding srmech_zeilberger /
 *     srmech_wz_verify consume.
 *
 * The reader NEVER reduces / normalises a coefficient (it lands the operand
 * verbatim, as the reducers expect); a malformed node -> SRMECH_ERR_BAD_INPUT
 * and the Python caller runs the COMPLETE pure path (rc103 inform-don't-limit).
 *
 * JPL Power-of-Ten: caller-arena only (no malloc), <=60-line functions, >=2
 * asserts/function, no goto/recursion (the nesting is a bounded 2-deep loop,
 * NOT recursion), no abs/libm. Additive symbols -> SRMECH_ABI_VERSION stays 4
 * (the Python ctypes shim hasattr-guards them). License: MIT. */

#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

#include "srmech.h"

/* ------------------------------------------------------------------
 * Bump arena — carve forward off the PUBLIC srmech_marshal_arena_t (rc187),
 * void*-aligned (the srmech_infer / compose_run idiom). NULL (no partial
 * carve) if a request does not fit.
 * ------------------------------------------------------------------ */

static unsigned char *cm_align(unsigned char *p)
{
    uintptr_t a = (uintptr_t)sizeof(void *);
    uintptr_t pad;
    assert(p != NULL);
    assert(a >= 4u);
    pad = (a - ((uintptr_t)p % a)) % a;
    return p + pad;
}

static unsigned char *cm_carve(srmech_marshal_arena_t *a, size_t n)
{
    unsigned char *p;
    assert(a != NULL);
    assert(a->cur <= a->end);
    p = cm_align(a->cur);
    if (p > a->end || n > (size_t)(a->end - p)) { return NULL; }
    a->cur = p + n;
    return p;
}

/* Carve `count` zeroed srmech_bigint carriers of `cap` limbs each. NULL on
 * arena exhaustion (count >= 1 by contract). */
static srmech_bigint_t *cm_bigint_array(srmech_marshal_arena_t *a,
                                        size_t count, uint32_t cap)
{
    srmech_bigint_t *arr;
    size_t i;
    assert(a != NULL);
    assert(cap > 0u && count > 0u);
    arr = (srmech_bigint_t *)cm_carve(a, count * sizeof(srmech_bigint_t));
    if (arr == NULL) { return NULL; }
    for (i = 0u; i < count; i++) {
        uint32_t *limbs = (uint32_t *)cm_carve(a, (size_t)cap * sizeof(uint32_t));
        if (limbs == NULL) { return NULL; }
        arr[i].sign = 0; arr[i].n = 0u; arr[i].cap = cap; arr[i].limbs = limbs;
    }
    return arr;
}

/* ------------------------------------------------------------------
 * Coefficient reading — a scalar (int64 or decimal string) or a [num,den].
 * ------------------------------------------------------------------ */

/* Fill an EXISTING bigint from a JSON scalar: an int64 (SRMECH_JSON_INT) OR a
 * non-empty decimal STRING (the bignum transport). BAD_INPUT otherwise. */
static srmech_status_t cm_fill_scalar(const srmech_json_value_t *j,
                                      srmech_bigint_t *dest)
{
    assert(dest != NULL);
    assert(dest->limbs != NULL);
    if (j == NULL) { return SRMECH_ERR_BAD_INPUT; }
    if (j->type == SRMECH_JSON_INT) { return srmech_bigint_set_i64(dest, j->u.i); }
    if (j->type == SRMECH_JSON_STRING && j->u.str.len > 0u) {
        return srmech_bigint_from_dec(dest, j->u.str.ptr, j->u.str.len);
    }
    return SRMECH_ERR_BAD_INPUT;
}

/* Read one coefficient node into (num, den): a bare scalar -> (scalar, 1); a
 * [num, den] 2-array -> the two scalars (each an int64 or a decimal string).
 * A nested / wrong-arity / non-scalar leaf -> BAD_INPUT (defer to pure). */
static srmech_status_t cm_read_coeff(const srmech_json_value_t *j,
                                     srmech_bigint_t *num, srmech_bigint_t *den)
{
    srmech_status_t st;
    assert(num != NULL && den != NULL);
    assert(num != den);
    if (j == NULL) { return SRMECH_ERR_BAD_INPUT; }
    if (j->type == SRMECH_JSON_ARRAY) {
        if (j->u.arr.n != 2u) { return SRMECH_ERR_BAD_INPUT; }
        st = cm_fill_scalar(j->u.arr.items[0], num);
        if (st != SRMECH_OK) { return st; }
        return cm_fill_scalar(j->u.arr.items[1], den);
    }
    st = cm_fill_scalar(j, num);
    if (st != SRMECH_OK) { return st; }
    return srmech_bigint_set_i64(den, 1);
}

/* ------------------------------------------------------------------
 * Poly (1-level) + BiPoly (2-level) readers — PUBLIC (rc192 reuse).
 * ------------------------------------------------------------------ */

srmech_status_t srmech_carrier_read_poly(const srmech_json_value_t *node,
                                         srmech_marshal_arena_t *a, uint32_t cap,
                                         srmech_bigint_t **out_num,
                                         srmech_bigint_t **out_den,
                                         size_t *out_len)
{
    srmech_bigint_t *ns, *ds;
    uint32_t i, n;
    /* runtime NULL-check BEFORE any assert (rc187 NULL-first contract). */
    if (node == NULL || a == NULL || out_num == NULL || out_den == NULL ||
        out_len == NULL) { return SRMECH_ERR_NULL_ARG; }
    assert(cap > 0u);
    assert(a->cur <= a->end);
    if (node->type != SRMECH_JSON_ARRAY) { return SRMECH_ERR_BAD_INPUT; }
    n = node->u.arr.n;
    ns = cm_bigint_array(a, (n == 0u) ? 1u : n, cap);
    ds = cm_bigint_array(a, (n == 0u) ? 1u : n, cap);
    if (ns == NULL || ds == NULL) { return SRMECH_ERR_OVERFLOW; }
    for (i = 0u; i < n; i++) {
        srmech_status_t st = cm_read_coeff(node->u.arr.items[i], &ns[i], &ds[i]);
        if (st != SRMECH_OK) { return st; }
    }
    *out_num = ns; *out_den = ds; *out_len = (size_t)n;
    return SRMECH_OK;
}

/* Sum the coefficient counts over a BiPoly's k-slots (each must be a Poly
 * array). *out_total is the flat length; SRMECH_ERR_BAD_INPUT on a non-array
 * slot. A separate pass keeps srmech_carrier_read_bipoly <= 60 lines. */
static srmech_status_t cm_bipoly_total(const srmech_json_value_t *node,
                                       uint32_t *out_total)
{
    uint32_t dk, total = 0u;
    assert(node != NULL && out_total != NULL);
    assert(node->type == SRMECH_JSON_ARRAY);
    for (dk = 0u; dk < node->u.arr.n; dk++) {
        const srmech_json_value_t *slot = node->u.arr.items[dk];
        if (slot == NULL || slot->type != SRMECH_JSON_ARRAY) {
            return SRMECH_ERR_BAD_INPUT;
        }
        total += slot->u.arr.n;
    }
    *out_total = total;
    return SRMECH_OK;
}

srmech_status_t srmech_carrier_read_bipoly(const srmech_json_value_t *node,
                                           srmech_marshal_arena_t *a, uint32_t cap,
                                           srmech_bigint_t **out_num,
                                           srmech_bigint_t **out_den,
                                           size_t **out_klen, size_t *out_kdeg)
{
    srmech_bigint_t *fn, *fd; size_t *kl; uint32_t dk, kdeg, total = 0u, idx = 0u;
    srmech_status_t st;
    if (node == NULL || a == NULL || out_num == NULL || out_den == NULL ||
        out_klen == NULL || out_kdeg == NULL) { return SRMECH_ERR_NULL_ARG; }
    assert(cap > 0u);
    assert(a->cur <= a->end);
    if (node->type != SRMECH_JSON_ARRAY) { return SRMECH_ERR_BAD_INPUT; }
    kdeg = node->u.arr.n;
    st = cm_bipoly_total(node, &total);
    if (st != SRMECH_OK) { return st; }
    fn = cm_bigint_array(a, (total == 0u) ? 1u : total, cap);
    fd = cm_bigint_array(a, (total == 0u) ? 1u : total, cap);
    kl = (size_t *)cm_carve(a, (size_t)((kdeg == 0u) ? 1u : kdeg) * sizeof(size_t));
    if (fn == NULL || fd == NULL || kl == NULL) { return SRMECH_ERR_OVERFLOW; }
    for (dk = 0u; dk < kdeg; dk++) {
        const srmech_json_value_t *slot = node->u.arr.items[dk];
        uint32_t i;
        kl[dk] = (size_t)slot->u.arr.n;
        for (i = 0u; i < slot->u.arr.n; i++) {
            st = cm_read_coeff(slot->u.arr.items[i], &fn[idx], &fd[idx]);
            if (st != SRMECH_OK) { return st; }
            idx++;
        }
    }
    *out_num = fn; *out_den = fd; *out_klen = kl; *out_kdeg = (size_t)kdeg;
    return SRMECH_OK;
}

/* ------------------------------------------------------------------
 * Round-trip PROVER — marshal a carrier from JSON + re-serialise it to a
 * CANONICAL nested-ℚ JSON (each coefficient as [num,den] decimal, compact
 * separators). Proves the reader landed every (bignum) coefficient value +
 * the nesting structure, byte-identical to the Python carrier's coefficient
 * view — with a SMALL arena (no MB-scale reducer scratch needed).
 * ------------------------------------------------------------------ */

typedef struct { char *buf; size_t cap; size_t used; int overflow; } cm_emit_t;

static void cm_raw(cm_emit_t *e, const char *s, size_t n)
{
    size_t i;
    assert(e != NULL);
    assert(s != NULL || n == 0u);
    if (e->buf != NULL) {                               /* buf==NULL is a size-query */
        if (e->overflow || e->used + n > e->cap) { e->overflow = 1; return; }
        for (i = 0u; i < n; i++) { e->buf[e->used + i] = s[i]; }
    }
    e->used += n;
}

/* Emit one bigint's decimal expansion (a JSON integer literal, bignum-safe).
 * Carves the to_dec buffer + ws off `a`; arena exhaustion latches overflow. */
static void cm_emit_bigint(cm_emit_t *e, const srmech_bigint_t *v,
                           srmech_marshal_arena_t *a)
{
    size_t bound, len = 0u, wsn; char *buf; unsigned char *ws;
    assert(e != NULL && v != NULL && a != NULL);
    assert(a->cur <= a->end);
    bound = srmech_bigint_to_dec_bound(v->n) + 2u;
    wsn = bound * 4u + 256u;
    buf = (char *)cm_carve(a, bound);
    ws = cm_carve(a, wsn);
    if (buf == NULL || ws == NULL) { e->overflow = 1; return; }
    if (srmech_bigint_to_dec(v, buf, bound, &len, ws, wsn) != SRMECH_OK) {
        e->overflow = 1; return;
    }
    cm_raw(e, buf, len);
}

/* Emit a Poly's num/den arrays as [[num,den],...] (compact separators). */
static void cm_emit_poly(cm_emit_t *e, const srmech_bigint_t *num,
                         const srmech_bigint_t *den, size_t len,
                         srmech_marshal_arena_t *a)
{
    size_t i;
    assert(e != NULL && a != NULL);
    assert(num != NULL || len == 0u);
    cm_raw(e, "[", 1u);
    for (i = 0u; i < len; i++) {
        if (i > 0u) { cm_raw(e, ",", 1u); }
        cm_raw(e, "[", 1u);
        cm_emit_bigint(e, &num[i], a);
        cm_raw(e, ",", 1u);
        cm_emit_bigint(e, &den[i], a);
        cm_raw(e, "]", 1u);
    }
    cm_raw(e, "]", 1u);
}

/* Route the round-trip by kind + emit the canonical JSON. `cap` is the
 * per-coefficient limb cap (sized from the JSON length so any bignum
 * coefficient fits). Split from the public entry so that stays <= 60 lines. */
static srmech_status_t cm_roundtrip_emit(int kind, const srmech_json_value_t *root,
                                         srmech_marshal_arena_t *a, uint32_t cap,
                                         cm_emit_t *e)
{
    srmech_bigint_t *num, *den; size_t len, kdeg, dk, idx = 0u; size_t *klen;
    srmech_status_t st;
    assert(root != NULL && a != NULL && e != NULL);
    assert(kind >= SRMECH_CARRIER_POLY && kind <= SRMECH_CARRIER_SCALAR);
    if (kind == SRMECH_CARRIER_SCALAR) {
        srmech_bigint_t *n1 = cm_bigint_array(a, 1u, cap);
        srmech_bigint_t *d1 = cm_bigint_array(a, 1u, cap);
        if (n1 == NULL || d1 == NULL) { return SRMECH_ERR_OVERFLOW; }
        st = cm_read_coeff(root, n1, d1);
        if (st != SRMECH_OK) { return st; }
        cm_raw(e, "[", 1u); cm_emit_bigint(e, n1, a); cm_raw(e, ",", 1u);
        cm_emit_bigint(e, d1, a); cm_raw(e, "]", 1u);
        return e->overflow ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
    }
    if (kind == SRMECH_CARRIER_POLY) {
        st = srmech_carrier_read_poly(root, a, cap, &num, &den, &len);
        if (st != SRMECH_OK) { return st; }
        cm_emit_poly(e, num, den, len, a);
        return e->overflow ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
    }
    st = srmech_carrier_read_bipoly(root, a, cap, &num, &den, &klen, &kdeg);
    if (st != SRMECH_OK) { return st; }
    cm_raw(e, "[", 1u);
    for (dk = 0u; dk < kdeg; dk++) {
        if (dk > 0u) { cm_raw(e, ",", 1u); }
        cm_emit_poly(e, &num[idx], &den[idx], klen[dk], a);
        idx += klen[dk];
    }
    cm_raw(e, "]", 1u);
    return e->overflow ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

size_t srmech_carrier_marshal_arena_bytes(size_t json_len)
{
    assert(sizeof(srmech_bigint_t) <= 64u);
    assert(sizeof(srmech_json_value_t) <= 128u);
    return 160u * json_len + 262144u;
}

srmech_status_t srmech_carrier_marshal_roundtrip(int kind, const char *json,
                                                 size_t json_len,
                                                 void *ws, size_t ws_len,
                                                 char *out, size_t out_cap,
                                                 size_t *out_len)
{
    srmech_marshal_arena_t a; srmech_json_value_t *root = NULL;
    unsigned char *parse_ws; size_t pj, cap; srmech_status_t st; cm_emit_t e;
    if (json == NULL || ws == NULL || out == NULL || out_len == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (kind < SRMECH_CARRIER_POLY || kind > SRMECH_CARRIER_SCALAR) {
        return SRMECH_ERR_BAD_INPUT;
    }
    assert(ws_len > 0u);
    srmech_marshal_arena_init(&a, ws, ws_len);
    assert(a.cur <= a.end);                         /* genuine arena invariant */
    pj = 160u * json_len + 65536u;
    parse_ws = cm_carve(&a, pj);
    if (parse_ws == NULL) { return SRMECH_ERR_OVERFLOW; }
    st = srmech_json_parse(json, json_len, parse_ws, pj, &root);
    if (st != SRMECH_OK) { return st; }
    if (root == NULL) { return SRMECH_ERR_BAD_INPUT; }
    cap = srmech_bigint_from_dec_bound(json_len) + 8u;  /* any bignum coeff fits */
    e.buf = out; e.cap = out_cap; e.used = 0u; e.overflow = 0;
    st = cm_roundtrip_emit(kind, root, &a, (uint32_t)cap, &e);
    if (st != SRMECH_OK) { return st; }
    *out_len = e.used;
    return e.overflow ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}
