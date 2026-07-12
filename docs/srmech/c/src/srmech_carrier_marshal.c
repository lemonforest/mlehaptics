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
 * TriPoly (3-level) reader — PUBLIC (rc223 srmech_infer.c reuse). The
 * j-ascending ARRAY of k-ascending ARRAYs of ascending-n coefficient arrays
 * (the apagodu_zeilberger._tri_pairs bridge form), lowered to the FLAT
 * (j-major, k, n) num/den arrays + nlen[dj*kdeg + dk] the srmech_
 * apagodu_zeilberger encoding. A ragged j-block pads to the max k-count with
 * empty runs (the Python _az_tri_flatten rectangularisation).
 * ------------------------------------------------------------------ */

/* Shape pass: *out_total = the flat coefficient count over the RECTANGULAR
 * (jdeg x kdeg) grid; *out_kdeg = the max k-count over j-blocks. BAD_INPUT on
 * a non-array j-block / k-run. Split off so the reader stays <= 60 lines. */
static srmech_status_t cm_tripoly_shape(const srmech_json_value_t *node,
                                        uint32_t *out_total, uint32_t *out_kdeg)
{
    uint32_t dj, dk, kdeg = 0u, total = 0u;
    assert(node != NULL && out_total != NULL);
    assert(node->type == SRMECH_JSON_ARRAY);
    for (dj = 0u; dj < node->u.arr.n; dj++) {
        const srmech_json_value_t *kgrid = node->u.arr.items[dj];
        if (kgrid == NULL || kgrid->type != SRMECH_JSON_ARRAY) {
            return SRMECH_ERR_BAD_INPUT;
        }
        if (kgrid->u.arr.n > kdeg) { kdeg = kgrid->u.arr.n; }
        for (dk = 0u; dk < kgrid->u.arr.n; dk++) {
            const srmech_json_value_t *run = kgrid->u.arr.items[dk];
            if (run == NULL || run->type != SRMECH_JSON_ARRAY) {
                return SRMECH_ERR_BAD_INPUT;
            }
            total += run->u.arr.n;
        }
    }
    *out_total = total;
    *out_kdeg = kdeg;
    return SRMECH_OK;
}

srmech_status_t srmech_carrier_read_tripoly(const srmech_json_value_t *node,
                                            srmech_marshal_arena_t *a, uint32_t cap,
                                            srmech_bigint_t **out_num,
                                            srmech_bigint_t **out_den,
                                            size_t **out_nlen, size_t *out_jdeg,
                                            size_t *out_kdeg)
{
    srmech_bigint_t *fn, *fd; size_t *nl;
    uint32_t dj, dk, jdeg, kdeg = 0u, total = 0u, idx = 0u, cells;
    srmech_status_t st;
    if (node == NULL || a == NULL || out_num == NULL || out_den == NULL ||
        out_nlen == NULL || out_jdeg == NULL || out_kdeg == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(cap > 0u);
    assert(a->cur <= a->end);
    if (node->type != SRMECH_JSON_ARRAY) { return SRMECH_ERR_BAD_INPUT; }
    jdeg = node->u.arr.n;
    st = cm_tripoly_shape(node, &total, &kdeg);
    if (st != SRMECH_OK) { return st; }
    cells = jdeg * kdeg;
    fn = cm_bigint_array(a, (total == 0u) ? 1u : total, cap);
    fd = cm_bigint_array(a, (total == 0u) ? 1u : total, cap);
    nl = (size_t *)cm_carve(a, (size_t)((cells == 0u) ? 1u : cells) * sizeof(size_t));
    if (fn == NULL || fd == NULL || nl == NULL) { return SRMECH_ERR_OVERFLOW; }
    for (dj = 0u; dj < jdeg; dj++) {
        const srmech_json_value_t *kgrid = node->u.arr.items[dj];
        for (dk = 0u; dk < kdeg; dk++) {
            const srmech_json_value_t *run =
                (dk < kgrid->u.arr.n) ? kgrid->u.arr.items[dk] : NULL;
            uint32_t i, rn = (run == NULL) ? 0u : run->u.arr.n;
            nl[dj * kdeg + dk] = (size_t)rn;      /* the pad run is EMPTY      */
            for (i = 0u; i < rn; i++) {
                st = cm_read_coeff(run->u.arr.items[i], &fn[idx], &fd[idx]);
                if (st != SRMECH_OK) { return st; }
                idx++;
            }
        }
    }
    *out_num = fn; *out_den = fd; *out_nlen = nl;
    *out_jdeg = (size_t)jdeg; *out_kdeg = (size_t)kdeg;
    return SRMECH_OK;
}

/* ------------------------------------------------------------------
 * QBiPoly (Laurent bivariate-q) reader — PUBLIC (rc223 srmech_infer.c reuse).
 * The Y-ascending ARRAY of [x_low, rows] pairs (the qbipoly._qb_pairs bridge
 * form as JSON: x_low a JSON int; rows an x-ascending ARRAY of ascending-q
 * coefficient arrays), lowered to flat (Y-major, X-major) q-run num/den
 * arrays + qlen[] per (Y,X) cell + xlow[]/xcells[] per Y cell + ycells — the
 * bridge srmech_q_zeilberger / srmech_q_wz_verify / srmech_q_gosper consume.
 * ------------------------------------------------------------------ */

/* Shape pass: *out_total = the flat q-coefficient count; *out_cells = the
 * total (Y,X) cell count. Validates every Y entry is a [int, array] pair
 * whose rows are arrays. Split off so the reader stays <= 60 lines. */
static srmech_status_t cm_qbipoly_shape(const srmech_json_value_t *node,
                                        uint32_t *out_total, uint32_t *out_cells)
{
    uint32_t dy, dx, total = 0u, cells = 0u;
    assert(node != NULL && out_total != NULL);
    assert(node->type == SRMECH_JSON_ARRAY);
    for (dy = 0u; dy < node->u.arr.n; dy++) {
        const srmech_json_value_t *pair = node->u.arr.items[dy];
        const srmech_json_value_t *rows;
        if (pair == NULL || pair->type != SRMECH_JSON_ARRAY ||
            pair->u.arr.n != 2u || pair->u.arr.items[0] == NULL ||
            pair->u.arr.items[0]->type != SRMECH_JSON_INT) {
            return SRMECH_ERR_BAD_INPUT;
        }
        rows = pair->u.arr.items[1];
        if (rows == NULL || rows->type != SRMECH_JSON_ARRAY) {
            return SRMECH_ERR_BAD_INPUT;
        }
        cells += rows->u.arr.n;
        for (dx = 0u; dx < rows->u.arr.n; dx++) {
            const srmech_json_value_t *run = rows->u.arr.items[dx];
            if (run == NULL || run->type != SRMECH_JSON_ARRAY) {
                return SRMECH_ERR_BAD_INPUT;
            }
            total += run->u.arr.n;
        }
    }
    *out_total = total;
    *out_cells = cells;
    return SRMECH_OK;
}

srmech_status_t srmech_carrier_read_qbipoly(const srmech_json_value_t *node,
                                            srmech_marshal_arena_t *a, uint32_t cap,
                                            srmech_bigint_t **out_num,
                                            srmech_bigint_t **out_den,
                                            size_t **out_qlen, int64_t **out_xlow,
                                            size_t **out_xcells,
                                            size_t *out_ycells)
{
    srmech_bigint_t *fn, *fd; size_t *ql, *xc; int64_t *xl;
    uint32_t dy, dx, ycells, total = 0u, cells = 0u, cell = 0u, idx = 0u;
    srmech_status_t st;
    if (node == NULL || a == NULL || out_num == NULL || out_den == NULL ||
        out_qlen == NULL || out_xlow == NULL || out_xcells == NULL ||
        out_ycells == NULL) { return SRMECH_ERR_NULL_ARG; }
    assert(cap > 0u);
    assert(a->cur <= a->end);
    if (node->type != SRMECH_JSON_ARRAY) { return SRMECH_ERR_BAD_INPUT; }
    ycells = node->u.arr.n;
    st = cm_qbipoly_shape(node, &total, &cells);
    if (st != SRMECH_OK) { return st; }
    fn = cm_bigint_array(a, (total == 0u) ? 1u : total, cap);
    fd = cm_bigint_array(a, (total == 0u) ? 1u : total, cap);
    ql = (size_t *)cm_carve(a, (size_t)((cells == 0u) ? 1u : cells) * sizeof(size_t));
    xl = (int64_t *)cm_carve(a, (size_t)((ycells == 0u) ? 1u : ycells) * sizeof(int64_t));
    xc = (size_t *)cm_carve(a, (size_t)((ycells == 0u) ? 1u : ycells) * sizeof(size_t));
    if (fn == NULL || fd == NULL || ql == NULL || xl == NULL || xc == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    for (dy = 0u; dy < ycells; dy++) {
        const srmech_json_value_t *pair = node->u.arr.items[dy];
        const srmech_json_value_t *rows = pair->u.arr.items[1];
        xl[dy] = pair->u.arr.items[0]->u.i;
        xc[dy] = (size_t)rows->u.arr.n;
        for (dx = 0u; dx < rows->u.arr.n; dx++) {
            const srmech_json_value_t *run = rows->u.arr.items[dx];
            uint32_t i;
            ql[cell] = (size_t)run->u.arr.n;
            cell++;
            for (i = 0u; i < run->u.arr.n; i++) {
                st = cm_read_coeff(run->u.arr.items[i], &fn[idx], &fd[idx]);
                if (st != SRMECH_OK) { return st; }
                idx++;
            }
        }
    }
    *out_num = fn; *out_den = fd; *out_qlen = ql; *out_xlow = xl;
    *out_xcells = xc; *out_ycells = (size_t)ycells;
    return SRMECH_OK;
}

/* ------------------------------------------------------------------
 * EllRatio (pre-interned wire) reader — PUBLIC (rc223 srmech_infer.c reuse).
 * The JSON OBJECT with n_syms / xsym / psym / qsym / ysym / nsym / ksym /
 * n_num / n_den int fields + coeff_num / coeff_den scalar arrays + exps int
 * rows (the interning done Python-side in the sorted-symbol order), lowered
 * to the srmech_elliptic_* wire form struct.
 * ------------------------------------------------------------------ */

/* Read a required int field into *out (int64). BAD_INPUT if missing or not
 * a JSON int. */
static srmech_status_t cm_int_field(const srmech_json_value_t *node,
                                    const char *key, int64_t *out)
{
    const srmech_json_value_t *v;
    assert(node != NULL && key != NULL);
    assert(out != NULL);
    v = srmech_json_object_get(node, key);
    if (v == NULL || v->type != SRMECH_JSON_INT) { return SRMECH_ERR_BAD_INPUT; }
    *out = v->u.i;
    return SRMECH_OK;
}

/* Validate + read the seven interned-index / shape int fields. A symbol index
 * must sit in [-1, n_syms); n_syms >= 1. Split off for the <= 60-line rule. */
static srmech_status_t cm_ellratio_ints(const srmech_json_value_t *node,
                                        srmech_ellratio_wire_t *w)
{
    static const char *const keys[6] = {"xsym", "psym", "qsym", "ysym",
                                        "nsym", "ksym"};
    int *slots[6]; int64_t v; size_t i; srmech_status_t st;
    assert(node != NULL && w != NULL);
    assert(node->type == SRMECH_JSON_OBJECT);
    slots[0] = &w->xsym; slots[1] = &w->psym; slots[2] = &w->qsym;
    slots[3] = &w->ysym; slots[4] = &w->nsym; slots[5] = &w->ksym;
    st = cm_int_field(node, "n_syms", &v);
    if (st != SRMECH_OK || v < 1 || v > 4096) { return SRMECH_ERR_BAD_INPUT; }
    w->n_syms = (size_t)v;
    for (i = 0u; i < 6u; i++) {
        st = cm_int_field(node, keys[i], &v);
        if (st != SRMECH_OK || v < -1 || v >= (int64_t)w->n_syms) {
            return SRMECH_ERR_BAD_INPUT;
        }
        *slots[i] = (int)v;
    }
    st = cm_int_field(node, "n_num", &v);
    if (st != SRMECH_OK || v < 0 || v > 4096) { return SRMECH_ERR_BAD_INPUT; }
    w->n_num = (size_t)v;
    st = cm_int_field(node, "n_den", &v);
    if (st != SRMECH_OK || v < 0 || v > 4096) { return SRMECH_ERR_BAD_INPUT; }
    w->n_den = (size_t)v;
    return SRMECH_OK;
}

srmech_status_t srmech_carrier_read_ellratio(const srmech_json_value_t *node,
                                             srmech_marshal_arena_t *a,
                                             uint32_t cap,
                                             srmech_ellratio_wire_t *out)
{
    const srmech_json_value_t *jcn, *jcd, *jex;
    size_t n_mono, i, s;
    srmech_status_t st;
    if (node == NULL || a == NULL || out == NULL) { return SRMECH_ERR_NULL_ARG; }
    assert(cap > 0u);
    assert(a->cur <= a->end);
    if (node->type != SRMECH_JSON_OBJECT) { return SRMECH_ERR_BAD_INPUT; }
    st = cm_ellratio_ints(node, out);
    if (st != SRMECH_OK) { return st; }
    n_mono = 1u + out->n_num + out->n_den;
    jcn = srmech_json_object_get(node, "coeff_num");
    jcd = srmech_json_object_get(node, "coeff_den");
    jex = srmech_json_object_get(node, "exps");
    if (jcn == NULL || jcn->type != SRMECH_JSON_ARRAY || jcn->u.arr.n != n_mono ||
        jcd == NULL || jcd->type != SRMECH_JSON_ARRAY || jcd->u.arr.n != n_mono ||
        jex == NULL || jex->type != SRMECH_JSON_ARRAY || jex->u.arr.n != n_mono) {
        return SRMECH_ERR_BAD_INPUT;
    }
    out->coeff_num = cm_bigint_array(a, n_mono, cap);
    out->coeff_den = cm_bigint_array(a, n_mono, cap);
    out->exps_flat = (int32_t *)cm_carve(a, n_mono * out->n_syms * sizeof(int32_t));
    if (out->coeff_num == NULL || out->coeff_den == NULL ||
        out->exps_flat == NULL) { return SRMECH_ERR_OVERFLOW; }
    for (i = 0u; i < n_mono; i++) {
        const srmech_json_value_t *row = jex->u.arr.items[i];
        st = cm_fill_scalar(jcn->u.arr.items[i], &out->coeff_num[i]);
        if (st != SRMECH_OK) { return st; }
        st = cm_fill_scalar(jcd->u.arr.items[i], &out->coeff_den[i]);
        if (st != SRMECH_OK) { return st; }
        if (row == NULL || row->type != SRMECH_JSON_ARRAY ||
            row->u.arr.n != out->n_syms) { return SRMECH_ERR_BAD_INPUT; }
        for (s = 0u; s < out->n_syms; s++) {
            const srmech_json_value_t *e = row->u.arr.items[s];
            if (e == NULL || e->type != SRMECH_JSON_INT ||
                e->u.i < INT32_MIN || e->u.i > INT32_MAX) {
                return SRMECH_ERR_BAD_INPUT;
            }
            out->exps_flat[i * out->n_syms + s] = (int32_t)e->u.i;
        }
    }
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

/* Emit an int64 as a decimal JSON literal (bounded digit loop, Class-K sign
 * branch — never abs()). */
static void cm_emit_i64(cm_emit_t *e, int64_t v)
{
    char rev[24]; char fwd[24]; size_t n = 0u, i;
    uint64_t m;
    assert(e != NULL);
    assert(sizeof(v) == 8u);
    m = (v < 0) ? ((uint64_t)(-(v + 1)) + 1u) : (uint64_t)v;
    do {
        rev[n] = (char)('0' + (char)(m % 10u));
        n++;
        m /= 10u;
    } while (m != 0u && n < 21u);
    i = 0u;
    if (v < 0) { fwd[0] = '-'; i = 1u; }
    while (n > 0u) { n--; fwd[i] = rev[n]; i++; }
    cm_raw(e, fwd, i);
}

/* Emit a TriPoly's rectangular (jdeg x kdeg) grid as the canonical nested
 * [[[..run..], ..]_k, ..]_j (a padded cell emits []). */
static void cm_emit_tripoly(cm_emit_t *e, const srmech_bigint_t *num,
                            const srmech_bigint_t *den, const size_t *nlen,
                            size_t jdeg, size_t kdeg, srmech_marshal_arena_t *a)
{
    size_t dj, dk, idx = 0u;
    assert(e != NULL && a != NULL);
    assert(nlen != NULL || jdeg * kdeg == 0u);
    cm_raw(e, "[", 1u);
    for (dj = 0u; dj < jdeg; dj++) {
        if (dj > 0u) { cm_raw(e, ",", 1u); }
        cm_raw(e, "[", 1u);
        for (dk = 0u; dk < kdeg; dk++) {
            size_t ln = nlen[dj * kdeg + dk];
            if (dk > 0u) { cm_raw(e, ",", 1u); }
            cm_emit_poly(e, &num[idx], &den[idx], ln, a);
            idx += ln;
        }
        cm_raw(e, "]", 1u);
    }
    cm_raw(e, "]", 1u);
}

/* Emit a QBiPoly as the canonical Y-list of [x_low, [[..run..], ..]] pairs. */
static void cm_emit_qbipoly(cm_emit_t *e, const srmech_bigint_t *num,
                            const srmech_bigint_t *den, const size_t *qlen,
                            const int64_t *xlow, const size_t *xcells,
                            size_t ycells, srmech_marshal_arena_t *a)
{
    size_t dy, dx, cell = 0u, idx = 0u;
    assert(e != NULL && a != NULL);
    assert(ycells == 0u || (xlow != NULL && xcells != NULL));
    cm_raw(e, "[", 1u);
    for (dy = 0u; dy < ycells; dy++) {
        if (dy > 0u) { cm_raw(e, ",", 1u); }
        cm_raw(e, "[", 1u);
        cm_emit_i64(e, xlow[dy]);
        cm_raw(e, ",[", 2u);
        for (dx = 0u; dx < xcells[dy]; dx++) {
            if (dx > 0u) { cm_raw(e, ",", 1u); }
            cm_emit_poly(e, &num[idx], &den[idx], qlen[cell], a);
            idx += qlen[cell];
            cell++;
        }
        cm_raw(e, "]]", 2u);
    }
    cm_raw(e, "]", 1u);
}

/* Emit an EllRatio wire as the canonical flat array
 * [n_syms,xsym,psym,qsym,ysym,nsym,ksym,n_num,n_den,[[cn,cd],..],[[e,..],..]]. */
static void cm_emit_ellratio(cm_emit_t *e, const srmech_ellratio_wire_t *w,
                             srmech_marshal_arena_t *a)
{
    size_t n_mono, i, s;
    int64_t hdr[9];
    assert(e != NULL && w != NULL);
    assert(a != NULL);
    n_mono = 1u + w->n_num + w->n_den;
    hdr[0] = (int64_t)w->n_syms; hdr[1] = w->xsym; hdr[2] = w->psym;
    hdr[3] = w->qsym; hdr[4] = w->ysym; hdr[5] = w->nsym; hdr[6] = w->ksym;
    hdr[7] = (int64_t)w->n_num; hdr[8] = (int64_t)w->n_den;
    cm_raw(e, "[", 1u);
    for (i = 0u; i < 9u; i++) {
        if (i > 0u) { cm_raw(e, ",", 1u); }
        cm_emit_i64(e, hdr[i]);
    }
    cm_raw(e, ",", 1u);
    cm_emit_poly(e, w->coeff_num, w->coeff_den, n_mono, a);
    cm_raw(e, ",[", 2u);
    for (i = 0u; i < n_mono; i++) {
        if (i > 0u) { cm_raw(e, ",", 1u); }
        cm_raw(e, "[", 1u);
        for (s = 0u; s < w->n_syms; s++) {
            if (s > 0u) { cm_raw(e, ",", 1u); }
            cm_emit_i64(e, (int64_t)w->exps_flat[i * w->n_syms + s]);
        }
        cm_raw(e, "]", 1u);
    }
    cm_raw(e, "]]", 2u);
}

/* Route the rc223 kinds (TRIPOLY / QBIPOLY / ELLRATIO): read via the public
 * reader, then emit the canonical form. Split from cm_roundtrip_emit so both
 * stay <= 60 lines. */
static srmech_status_t cm_roundtrip_emit_rc223(int kind,
                                               const srmech_json_value_t *root,
                                               srmech_marshal_arena_t *a,
                                               uint32_t cap, cm_emit_t *e)
{
    srmech_bigint_t *num, *den;
    srmech_status_t st;
    assert(root != NULL && a != NULL && e != NULL);
    assert(kind >= SRMECH_CARRIER_TRIPOLY && kind <= SRMECH_CARRIER_ELLRATIO);
    if (kind == SRMECH_CARRIER_TRIPOLY) {
        size_t *nlen, jdeg, kdeg;
        st = srmech_carrier_read_tripoly(root, a, cap, &num, &den, &nlen,
                                         &jdeg, &kdeg);
        if (st != SRMECH_OK) { return st; }
        cm_emit_tripoly(e, num, den, nlen, jdeg, kdeg, a);
        return e->overflow ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
    }
    if (kind == SRMECH_CARRIER_QBIPOLY) {
        size_t *qlen, *xcells, ycells; int64_t *xlow;
        st = srmech_carrier_read_qbipoly(root, a, cap, &num, &den, &qlen,
                                         &xlow, &xcells, &ycells);
        if (st != SRMECH_OK) { return st; }
        cm_emit_qbipoly(e, num, den, qlen, xlow, xcells, ycells, a);
        return e->overflow ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
    }
    {
        srmech_ellratio_wire_t w;
        st = srmech_carrier_read_ellratio(root, a, cap, &w);
        if (st != SRMECH_OK) { return st; }
        cm_emit_ellratio(e, &w, a);
    }
    return e->overflow ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
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
    assert(kind >= SRMECH_CARRIER_POLY && kind <= SRMECH_CARRIER_ELLRATIO);
    if (kind >= SRMECH_CARRIER_TRIPOLY) {
        return cm_roundtrip_emit_rc223(kind, root, a, cap, e);
    }
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
    if (kind < SRMECH_CARRIER_POLY || kind > SRMECH_CARRIER_ELLRATIO) {
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
