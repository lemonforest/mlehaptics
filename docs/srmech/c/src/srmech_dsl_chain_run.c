/* srmech_dsl_chain_run.c — the srmech.dsl Chain LINEAR RUN-LOOP in C
 * (0.9.0rc181; ANNEX Batch B pt1; the F1 carrier-FFI FOUNDATION).
 *
 * The DSL `Chain.run` is a SIBLING interpreter to the amsc.compose chain-runner
 * (srmech_compose_run.c / srmech_chain_run) — it VALUE-THREADS: each stage's
 * output feeds the next stage's input, with NO @row/@input/@step references (the
 * compose runner resolves those; this one does not). It runs the LEAN cascade
 * ATOMS on f64/i64 carriers.
 *
 * This file ships srmech_dsl_chain_run — the LINEAR (`then`-only) run loop over a
 * BOUNDED leaf-dispatch table of the C-backed cascade atoms. It is a NEW symbol
 * reusing the srmech_compose_run.c SCAFFOLD IDIOMS (a forward-only bump arena, the
 * srmech_json parse/build, a small tagged-union value carrier, the rc103 defer-to
 * -pure gate) WITHOUT touching srmech_chain_run.
 *
 *   chain_json  : {"chain":{"name":..},"stage":[{"op":..,<kwargs>..}, ...]} — the
 *                 build_chain_from_dict discriminator grammar. Only `op` (linear)
 *                 stages run here; a loop/fold/reduce/parallel discriminator → the
 *                 whole chain DEFERS to pure (rc182 adds the combinators).
 *   input_json  : an F1 VALUE DESCRIPTOR for the seed value (see below).
 *   out         : the F1 VALUE DESCRIPTOR for the final value.
 *
 * THE F1 CARRIER (the shared carrier-FFI bedrock #796's F2/F3/F4 extend). A tagged
 * union dv_value_t {NONE, INT (i64), FLOAT (f64), STR, LIST} — LIST carries an
 * is_tuple bit (Python list vs tuple) and holds BOUNDED-depth children (<=
 * DV_MAX_DEPTH; JPL Rule 1 — the nesting recursion is depth-guarded + asserted,
 * never unbounded). Marshalled as a canonical-JSON value descriptor:
 *   {"k":"n"} | {"k":"i","v":<int>} | {"k":"f","v":<num>} | {"k":"s","v":<str>} |
 *   {"k":"l","v":[<desc>,..]}  (list) | {"k":"t","v":[<desc>,..]}  (tuple).
 * FLOAT round-trips at %.17g (NOT byte-identical — the numeric atoms' parity is
 * WITHIN-TOL; exact/structural stages are exact).
 *
 * THE LEAF-DISPATCH TABLE (lookup_cascade_op → C kernel): magnitude, reorient,
 * pin_slot_at_zero, best_rational_signed, chiral_flip, net_chirality,
 * autocorrelation — the unary value→value C-backed atoms. Any other op
 * (cyclic_gcd / chiral_dual — 2-ary / higher-order; kuramoto_step / quaternion_dft
 * / octonion_dft — heavier multi-array carriers; any user composite) → the leaf
 * returns SRMECH_ERR_NOT_IMPL and the WHOLE chain defers to the pure path (rc103
 * inform-don't-limit — never a wrong answer).
 *
 * ARENA: ONE caller arena `ws`, bump-allocated FORWARD (size with
 * srmech_dsl_chain_run_arena_bytes). Each stage's output carrier persists (the
 * next stage reads it); a too-small arena → SRMECH_ERR_OVERFLOW → pure.
 *
 * JPL Power-of-Ten: caller-arena only (no malloc), <=60-line functions, >=2
 * asserts/function, no goto, DEPTH-BOUNDED recursion (DV_MAX_DEPTH), no abs/libm.
 * Additive symbols → SRMECH_ABI_VERSION stays 4 (the ctypes shim hasattr-guards).
 */

#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

#include "srmech.h"

/* ------------------------------------------------------------------
 * Bump arena — forward-only carve, void*-aligned (the compose_run idiom).
 * ------------------------------------------------------------------ */

typedef struct { unsigned char *cur; unsigned char *end; } dcr_bump_t;

static unsigned char *dcr_align(unsigned char *p)
{
    uintptr_t a = (uintptr_t)sizeof(void *);
    uintptr_t pad;
    assert(p != NULL);
    assert(a >= 4u);
    pad = (a - ((uintptr_t)p % a)) % a;
    return p + pad;
}

/* Carve `n` aligned bytes; NULL (no partial carve) if it does not fit. */
static unsigned char *dcr_carve(dcr_bump_t *b, size_t n)
{
    unsigned char *p;
    assert(b != NULL);
    assert(b->cur <= b->end);
    p = dcr_align(b->cur);
    if (p > b->end || n > (size_t)(b->end - p)) { return NULL; }
    b->cur = p + n;
    return p;
}

/* ------------------------------------------------------------------
 * F1 carrier — the tagged-union value threaded between stages. LIST carries an
 * is_tuple bit + BOUNDED-depth children (DV_MAX_DEPTH). This is the shared
 * carrier-FFI bedrock #796's F2/F3/F4 (mat/vec/hv/complex carriers) extend by
 * adding new kinds to the union + new "k" descriptor tags — the union grows, the
 * marshal contract stays.
 * ------------------------------------------------------------------ */

#define DV_MAX_DEPTH 6

typedef enum {
    DV_NONE = 0, DV_INT, DV_FLOAT, DV_STR, DV_LIST
} dv_kind_t;

typedef struct dv_value {
    dv_kind_t kind;
    int64_t   i;                           /* DV_INT                        */
    double    f;                           /* DV_FLOAT                      */
    const char *s; uint32_t slen;          /* DV_STR (aliases parse arena)  */
    struct dv_value **items; uint32_t n;   /* DV_LIST children              */
    int is_tuple;                          /* DV_LIST: 1 => tuple, 0 => list */
} dv_value_t;

static dv_value_t *dv_new(dcr_bump_t *b, dv_kind_t kind)
{
    dv_value_t *v;
    assert(b != NULL);
    assert(kind >= DV_NONE && kind <= DV_LIST);
    v = (dv_value_t *)dcr_carve(b, sizeof(dv_value_t));
    if (v == NULL) { return NULL; }
    v->kind = kind; v->i = 0; v->f = 0.0;
    v->s = NULL; v->slen = 0u; v->items = NULL; v->n = 0u; v->is_tuple = 0;
    return v;
}

static dv_value_t *dv_int(dcr_bump_t *b, int64_t v)
{
    dv_value_t *out;
    assert(b != NULL);
    assert(b->cur <= b->end);
    out = dv_new(b, DV_INT);
    if (out == NULL) { return NULL; }
    out->i = v;
    return out;
}

static dv_value_t *dv_float(dcr_bump_t *b, double v)
{
    dv_value_t *out;
    assert(b != NULL);
    assert(b->cur <= b->end);
    out = dv_new(b, DV_FLOAT);
    if (out == NULL) { return NULL; }
    out->f = v;
    return out;
}

/* ------------------------------------------------------------------
 * F1 descriptor PARSE — {"k":..,"v":..} JSON node -> value carrier. Depth-bounded
 * recursion (DV_MAX_DEPTH); NULL -> defer to pure. `dv_from_list` is the list
 * arm (kept a separate <=60-line function).
 * ------------------------------------------------------------------ */

static dv_value_t *dv_from_desc(dcr_bump_t *b, const srmech_json_value_t *j,
                                uint32_t depth);

static dv_value_t *dv_from_list(dcr_bump_t *b, const srmech_json_value_t *arr,
                                int is_tuple, uint32_t depth)
{
    dv_value_t *out; dv_value_t **items; uint32_t i;
    assert(b != NULL && arr != NULL);
    assert(arr->type == SRMECH_JSON_ARRAY);
    out = dv_new(b, DV_LIST);
    if (out == NULL) { return NULL; }
    out->is_tuple = is_tuple ? 1 : 0;
    out->n = arr->u.arr.n;
    items = (dv_value_t **)dcr_carve(b, (size_t)out->n * sizeof(void *) + 1u);
    if (items == NULL) { return NULL; }
    for (i = 0u; i < out->n; i++) {
        items[i] = dv_from_desc(b, arr->u.arr.items[i], depth + 1u);
        if (items[i] == NULL) { return NULL; }
    }
    out->items = items;
    return out;
}

static dv_value_t *dv_from_desc(dcr_bump_t *b, const srmech_json_value_t *j,
                                uint32_t depth)
{
    const srmech_json_value_t *kn, *vn; const char *k; dv_value_t *out;
    assert(b != NULL);
    assert(depth <= (uint32_t)DV_MAX_DEPTH + 1u);
    if (j == NULL || j->type != SRMECH_JSON_OBJECT) { return NULL; }
    if (depth > (uint32_t)DV_MAX_DEPTH) { return NULL; }   /* bound the nesting */
    kn = srmech_json_object_get(j, "k");
    if (kn == NULL || kn->type != SRMECH_JSON_STRING || kn->u.str.len != 1u) {
        return NULL;
    }
    k = kn->u.str.ptr;
    if (k[0] == 'n') { return dv_new(b, DV_NONE); }
    vn = srmech_json_object_get(j, "v");
    if (vn == NULL) { return NULL; }
    if (k[0] == 'i') {
        if (vn->type != SRMECH_JSON_INT) { return NULL; }
        return dv_int(b, vn->u.i);
    }
    if (k[0] == 'f') {
        if (vn->type == SRMECH_JSON_DOUBLE) { return dv_float(b, vn->u.f); }
        if (vn->type == SRMECH_JSON_INT) { return dv_float(b, (double)vn->u.i); }
        return NULL;
    }
    if (k[0] == 's') {
        if (vn->type != SRMECH_JSON_STRING) { return NULL; }
        out = dv_new(b, DV_STR);
        if (out == NULL) { return NULL; }
        out->s = vn->u.str.ptr; out->slen = vn->u.str.len;
        return out;
    }
    if ((k[0] == 'l' || k[0] == 't') && vn->type == SRMECH_JSON_ARRAY) {
        return dv_from_list(b, vn, k[0] == 't', depth);
    }
    return NULL;
}

/* ------------------------------------------------------------------
 * F1 descriptor EMIT — value carrier -> {"k":..,"v":..} via the json builder.
 * `dv_list_to_desc` is the list arm; item-pointer scratch comes from `tmp` (the
 * run bump — transient, since new_array COPIES the array into the builder arena).
 * Depth-bounded recursion (DV_MAX_DEPTH).
 * ------------------------------------------------------------------ */

static srmech_json_value_t *dv_to_desc(srmech_json_builder_t *bd,
                                       const dv_value_t *v, dcr_bump_t *tmp,
                                       uint32_t depth);

static srmech_json_value_t *dv_list_to_desc(srmech_json_builder_t *bd,
                                            const dv_value_t *v, dcr_bump_t *tmp,
                                            uint32_t depth)
{
    const char *keys[2]; srmech_json_value_t *vals[2]; srmech_json_value_t **kids;
    uint32_t i;
    assert(bd != NULL && v != NULL && tmp != NULL);
    assert(v->kind == DV_LIST);
    kids = (srmech_json_value_t **)dcr_carve(tmp, (size_t)v->n * sizeof(void *) + 1u);
    if (kids == NULL) { return NULL; }
    for (i = 0u; i < v->n; i++) {
        kids[i] = dv_to_desc(bd, v->items[i], tmp, depth + 1u);
        if (kids[i] == NULL) { return NULL; }
    }
    keys[0] = "k"; keys[1] = "v";
    vals[0] = srmech_json_new_string(bd, v->is_tuple ? "t" : "l", 1u);
    vals[1] = srmech_json_new_array(bd, kids, v->n);
    return srmech_json_new_object(bd, keys, vals, 2u);
}

static srmech_json_value_t *dv_to_desc(srmech_json_builder_t *bd,
                                       const dv_value_t *v, dcr_bump_t *tmp,
                                       uint32_t depth)
{
    const char *keys[2]; srmech_json_value_t *vals[2];
    assert(bd != NULL && tmp != NULL);
    assert(depth <= (uint32_t)DV_MAX_DEPTH + 1u);
    if (depth > (uint32_t)DV_MAX_DEPTH) { return NULL; }
    if (v == NULL || v->kind == DV_NONE) {
        keys[0] = "k"; vals[0] = srmech_json_new_string(bd, "n", 1u);
        return srmech_json_new_object(bd, keys, vals, 1u);
    }
    if (v->kind == DV_LIST) { return dv_list_to_desc(bd, v, tmp, depth); }
    keys[0] = "k"; keys[1] = "v";
    if (v->kind == DV_INT) {
        vals[0] = srmech_json_new_string(bd, "i", 1u);
        vals[1] = srmech_json_new_int(bd, v->i);
        return srmech_json_new_object(bd, keys, vals, 2u);
    }
    if (v->kind == DV_FLOAT) {
        vals[0] = srmech_json_new_string(bd, "f", 1u);
        vals[1] = srmech_json_new_double(bd, v->f);
        return srmech_json_new_object(bd, keys, vals, 2u);
    }
    vals[0] = srmech_json_new_string(bd, "s", 1u);           /* DV_STR */
    vals[1] = srmech_json_new_string(bd, v->s, v->slen);
    return srmech_json_new_object(bd, keys, vals, 2u);
}

/* ------------------------------------------------------------------
 * Leaf helpers — one per C-backed cascade atom. Each unpacks the threaded value
 * (+ any stage kwargs), calls the EXISTING C kernel, wraps the result as a fresh
 * persisting carrier, and returns SRMECH_OK — or SRMECH_ERR_NOT_IMPL to DEFER the
 * WHOLE chain to pure (an input shape / kwarg the strict path does not cover,
 * matching the Python wrapper's own native-vs-pure gate).
 * ------------------------------------------------------------------ */

static srmech_status_t leaf_magnitude(dcr_bump_t *b, const dv_value_t *in,
                                      dv_value_t **out)
{
    double m; srmech_status_t st;
    assert(b != NULL && out != NULL);
    assert(in != NULL);
    if (in->kind != DV_FLOAT) { return SRMECH_ERR_NOT_IMPL; }  /* int -> pure */
    st = srmech_cascade_magnitude_f64(in->f, &m);
    if (st != SRMECH_OK) { return st; }
    *out = dv_float(b, m);
    return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

static srmech_status_t leaf_reorient(dcr_bump_t *b, const srmech_json_value_t *stage,
                                     const dv_value_t *in, dv_value_t **out)
{
    const srmech_json_value_t *ori = srmech_json_object_get(stage, "orientation");
    int64_t o; srmech_status_t st;
    assert(b != NULL && out != NULL);
    assert(stage != NULL && in != NULL);
    if (ori == NULL || ori->type != SRMECH_JSON_INT) { return SRMECH_ERR_NOT_IMPL; }
    o = ori->u.i;
    if (o < -128 || o > 127) { return SRMECH_ERR_NOT_IMPL; }
    if (in->kind == DV_INT) {
        int64_t r;
        if (in->i == INT64_MIN) { return SRMECH_ERR_NOT_IMPL; }  /* negate ovf -> pure */
        st = srmech_cascade_reorient_i64((int8_t)o, in->i, &r);
        if (st != SRMECH_OK) { return st; }
        *out = dv_int(b, r);
    } else if (in->kind == DV_FLOAT) {
        double r;
        st = srmech_cascade_reorient_f64((int8_t)o, in->f, &r);
        if (st != SRMECH_OK) { return st; }
        *out = dv_float(b, r);
    } else {
        return SRMECH_ERR_NOT_IMPL;
    }
    return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* A 2-element Python TUPLE carrier [a, b] (pin_slot / best_rational output). */
static srmech_status_t dv_pair(dcr_bump_t *b, dv_value_t *a, dv_value_t *bb,
                               dv_value_t **out)
{
    dv_value_t *t; dv_value_t **items;
    assert(b != NULL && out != NULL);
    assert(a != NULL && bb != NULL);
    t = dv_new(b, DV_LIST);
    if (t == NULL) { return SRMECH_ERR_OVERFLOW; }
    items = (dv_value_t **)dcr_carve(b, 2u * sizeof(void *) + 1u);
    if (items == NULL) { return SRMECH_ERR_OVERFLOW; }
    t->is_tuple = 1; t->n = 2u; items[0] = a; items[1] = bb; t->items = items;
    *out = t;
    return SRMECH_OK;
}

static srmech_status_t leaf_pin_slot(dcr_bump_t *b, const dv_value_t *in,
                                     dv_value_t **out)
{
    int8_t ori; double mag; srmech_status_t st; dv_value_t *a, *m;
    assert(b != NULL && out != NULL);
    assert(in != NULL);
    if (in->kind != DV_FLOAT) { return SRMECH_ERR_NOT_IMPL; }  /* int -> pure */
    st = srmech_cascade_pin_slot_at_zero_f64(in->f, &ori, &mag);
    if (st != SRMECH_OK) { return st; }
    a = dv_int(b, (int64_t)ori); m = dv_float(b, mag);
    if (a == NULL || m == NULL) { return SRMECH_ERR_OVERFLOW; }
    return dv_pair(b, a, m, out);
}

static srmech_status_t leaf_best_rational(dcr_bump_t *b,
                                          const srmech_json_value_t *stage,
                                          const dv_value_t *in, dv_value_t **out)
{
    const srmech_json_value_t *md = srmech_json_object_get(stage, "max_denominator");
    const srmech_json_value_t *fs = srmech_json_object_get(stage, "fine_scale");
    int64_t maxd = 100, fine = 1000000, num, den; srmech_status_t st;
    dv_value_t *n, *d;
    assert(b != NULL && out != NULL);
    assert(stage != NULL && in != NULL);
    if (in->kind != DV_FLOAT) { return SRMECH_ERR_NOT_IMPL; }
    if (md != NULL) {
        if (md->type != SRMECH_JSON_INT) { return SRMECH_ERR_NOT_IMPL; }
        maxd = md->u.i;
    }
    if (fs != NULL) {
        if (fs->type != SRMECH_JSON_INT) { return SRMECH_ERR_NOT_IMPL; }
        fine = fs->u.i;
    }
    if (maxd < 1 || fine < 1) { return SRMECH_ERR_NOT_IMPL; }  /* pure raises ValueError */
    st = srmech_cascade_best_rational_signed_f64(in->f, maxd, fine, &num, &den);
    if (st != SRMECH_OK) { return st; }
    n = dv_int(b, num); d = dv_int(b, den);
    if (n == NULL || d == NULL) { return SRMECH_ERR_OVERFLOW; }
    return dv_pair(b, n, d, out);
}

/* homogeneity of a non-empty DV_LIST: 1 => all DV_INT, 2 => all DV_FLOAT, 0 else. */
static int dv_list_numeric_kind(const dv_value_t *v)
{
    uint32_t i; int all_int = 1, all_float = 1;
    assert(v != NULL);
    assert(v->kind == DV_LIST && v->n > 0u);
    for (i = 0u; i < v->n; i++) {
        const dv_value_t *e = v->items[i];
        if (e == NULL) { return 0; }
        if (e->kind != DV_INT) { all_int = 0; }
        if (e->kind != DV_FLOAT) { all_float = 0; }
    }
    if (all_int) { return 1; }
    if (all_float) { return 2; }
    return 0;
}

static srmech_status_t flip_i64(dcr_bump_t *b, const dv_value_t *in, dv_value_t **out)
{
    int64_t *buf, *rev; dv_value_t *r; dv_value_t **items; uint32_t i, n = in->n;
    srmech_status_t st;
    assert(b != NULL && in != NULL && out != NULL);
    assert(n > 0u);
    buf = (int64_t *)dcr_carve(b, (size_t)n * sizeof(int64_t));
    rev = (int64_t *)dcr_carve(b, (size_t)n * sizeof(int64_t));
    items = (dv_value_t **)dcr_carve(b, (size_t)n * sizeof(void *) + 1u);
    r = dv_new(b, DV_LIST);
    if (buf == NULL || rev == NULL || items == NULL || r == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    for (i = 0u; i < n; i++) { buf[i] = in->items[i]->i; }
    st = srmech_cascade_chiral_flip_i64(buf, (size_t)n, rev);
    if (st != SRMECH_OK) { return st; }
    for (i = 0u; i < n; i++) {
        items[i] = dv_int(b, rev[i]);
        if (items[i] == NULL) { return SRMECH_ERR_OVERFLOW; }
    }
    r->is_tuple = in->is_tuple; r->n = n; r->items = items; *out = r;
    return SRMECH_OK;
}

static srmech_status_t flip_f64(dcr_bump_t *b, const dv_value_t *in, dv_value_t **out)
{
    double *buf, *rev; dv_value_t *r; dv_value_t **items; uint32_t i, n = in->n;
    srmech_status_t st;
    assert(b != NULL && in != NULL && out != NULL);
    assert(n > 0u);
    buf = (double *)dcr_carve(b, (size_t)n * sizeof(double));
    rev = (double *)dcr_carve(b, (size_t)n * sizeof(double));
    items = (dv_value_t **)dcr_carve(b, (size_t)n * sizeof(void *) + 1u);
    r = dv_new(b, DV_LIST);
    if (buf == NULL || rev == NULL || items == NULL || r == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    for (i = 0u; i < n; i++) { buf[i] = in->items[i]->f; }
    st = srmech_cascade_chiral_flip_f64(buf, (size_t)n, rev);
    if (st != SRMECH_OK) { return st; }
    for (i = 0u; i < n; i++) {
        items[i] = dv_float(b, rev[i]);
        if (items[i] == NULL) { return SRMECH_ERR_OVERFLOW; }
    }
    r->is_tuple = in->is_tuple; r->n = n; r->items = items; *out = r;
    return SRMECH_OK;
}

static srmech_status_t leaf_chiral_flip(dcr_bump_t *b, const dv_value_t *in,
                                        dv_value_t **out)
{
    int kind; dv_value_t *r;
    assert(b != NULL && out != NULL);
    assert(in != NULL);
    if (in->kind != DV_LIST) { return SRMECH_ERR_NOT_IMPL; }
    if (in->n == 0u) {                                   /* reversal of [] is [] */
        r = dv_new(b, DV_LIST);
        if (r == NULL) { return SRMECH_ERR_OVERFLOW; }
        r->is_tuple = in->is_tuple; *out = r;
        return SRMECH_OK;
    }
    kind = dv_list_numeric_kind(in);
    if (kind == 1) { return flip_i64(b, in, out); }
    if (kind == 2) { return flip_f64(b, in, out); }
    return SRMECH_ERR_NOT_IMPL;                          /* mixed -> pure seq[::-1] */
}

static srmech_status_t leaf_net_chirality(dcr_bump_t *b, const dv_value_t *in,
                                          dv_value_t **out)
{
    int8_t *buf, r; uint32_t i, n; srmech_status_t st;
    assert(b != NULL && out != NULL);
    assert(in != NULL);
    if (in->kind != DV_LIST) { return SRMECH_ERR_NOT_IMPL; }
    n = in->n;
    if (n == 0u) {
        *out = dv_int(b, 1);                             /* empty product = +1 */
        return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
    }
    buf = (int8_t *)dcr_carve(b, (size_t)n);
    if (buf == NULL) { return SRMECH_ERR_OVERFLOW; }
    for (i = 0u; i < n; i++) {
        const dv_value_t *e = in->items[i];
        if (e->kind != DV_INT || e->i < -128 || e->i > 127) {
            return SRMECH_ERR_NOT_IMPL;                  /* bool/float/oob -> pure */
        }
        buf[i] = (int8_t)e->i;
    }
    st = srmech_cascade_net_chirality_i8(buf, (size_t)n, &r);
    if (st != SRMECH_OK) { return st; }
    *out = dv_int(b, (int64_t)r);
    return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

static srmech_status_t leaf_autocorrelation(dcr_bump_t *b, const dv_value_t *in,
                                            dv_value_t **out)
{
    double *x, *r; dv_value_t *lst; dv_value_t **items; uint32_t i, n;
    srmech_status_t st;
    assert(b != NULL && out != NULL);
    assert(in != NULL);
    if (in->kind != DV_LIST) { return SRMECH_ERR_NOT_IMPL; }
    n = in->n;
    lst = dv_new(b, DV_LIST);                            /* always a list, never tuple */
    if (lst == NULL) { return SRMECH_ERR_OVERFLOW; }
    if (n == 0u) { *out = lst; return SRMECH_OK; }
    x = (double *)dcr_carve(b, (size_t)n * sizeof(double));
    r = (double *)dcr_carve(b, (size_t)n * sizeof(double));
    items = (dv_value_t **)dcr_carve(b, (size_t)n * sizeof(void *) + 1u);
    if (x == NULL || r == NULL || items == NULL) { return SRMECH_ERR_OVERFLOW; }
    for (i = 0u; i < n; i++) {
        const dv_value_t *e = in->items[i];
        if (e->kind == DV_FLOAT) { x[i] = e->f; }
        else if (e->kind == DV_INT) { x[i] = (double)e->i; }
        else { return SRMECH_ERR_NOT_IMPL; }
    }
    st = srmech_autocorrelation_f64(x, (size_t)n, r);
    if (st != SRMECH_OK) { return st; }
    for (i = 0u; i < n; i++) {
        items[i] = dv_float(b, r[i]);
        if (items[i] == NULL) { return SRMECH_ERR_OVERFLOW; }
    }
    lst->n = n; lst->items = items; *out = lst;
    return SRMECH_OK;
}

/* ------------------------------------------------------------------
 * The leaf-dispatch table (lookup_cascade_op -> C kernel). An op NOT here → the
 * caller defers the whole chain to pure (rc103 inform-don't-limit).
 * ------------------------------------------------------------------ */

static srmech_status_t dsl_leaf_dispatch(dcr_bump_t *b, const char *op, uint32_t opl,
                                         const srmech_json_value_t *stage,
                                         const dv_value_t *in, dv_value_t **out)
{
    assert(b != NULL && op != NULL && out != NULL);
    assert(stage != NULL && in != NULL);
    if (opl == 9u && memcmp(op, "magnitude", 9u) == 0) {
        return leaf_magnitude(b, in, out);
    }
    if (opl == 8u && memcmp(op, "reorient", 8u) == 0) {
        return leaf_reorient(b, stage, in, out);
    }
    if (opl == 16u && memcmp(op, "pin_slot_at_zero", 16u) == 0) {
        return leaf_pin_slot(b, in, out);
    }
    if (opl == 20u && memcmp(op, "best_rational_signed", 20u) == 0) {
        return leaf_best_rational(b, stage, in, out);
    }
    if (opl == 11u && memcmp(op, "chiral_flip", 11u) == 0) {
        return leaf_chiral_flip(b, in, out);
    }
    if (opl == 13u && memcmp(op, "net_chirality", 13u) == 0) {
        return leaf_net_chirality(b, in, out);
    }
    if (opl == 15u && memcmp(op, "autocorrelation", 15u) == 0) {
        return leaf_autocorrelation(b, in, out);
    }
    return SRMECH_ERR_NOT_IMPL;   /* non-C leaf (cyclic_gcd/chiral_dual/dft/...) -> pure */
}

/* ------------------------------------------------------------------
 * build_chain_from_dict-in-C: parse the stage array + thread the value. A
 * loop/fold/reduce/parallel discriminator, or a missing `op`, → SRMECH_ERR_NOT_IMPL
 * (defer to pure — rc182 adds the combinators).
 * ------------------------------------------------------------------ */

/* 1 iff `stage` carries a combinator discriminator (loop/fold/reduce/parallel). */
static int dsl_stage_is_combinator(const srmech_json_value_t *stage)
{
    static const char *disc[6] = { "loop_n", "sub_chain", "fold_init",
                                   "fold_op", "reduce_op", "parallel_body" };
    uint32_t i;
    assert(stage != NULL);
    assert(stage->type == SRMECH_JSON_OBJECT);
    for (i = 0u; i < 6u; i++) {
        if (srmech_json_object_get(stage, disc[i]) != NULL) { return 1; }
    }
    return 0;
}

static srmech_status_t dsl_run_stages(const srmech_json_value_t *chain,
                                      dv_value_t *input, dcr_bump_t *b,
                                      dv_value_t **final_out)
{
    const srmech_json_value_t *stages = srmech_json_object_get(chain, "stage");
    dv_value_t *cur = input; uint32_t i, ns; srmech_status_t st;
    assert(chain != NULL && b != NULL && final_out != NULL);
    assert(input != NULL);
    if (stages == NULL || stages->type != SRMECH_JSON_ARRAY) {
        return SRMECH_ERR_BAD_INPUT;
    }
    ns = stages->u.arr.n;
    for (i = 0u; i < ns; i++) {
        const srmech_json_value_t *stage = stages->u.arr.items[i];
        const srmech_json_value_t *opn; dv_value_t *nxt = NULL;
        if (stage == NULL || stage->type != SRMECH_JSON_OBJECT) {
            return SRMECH_ERR_BAD_INPUT;
        }
        if (dsl_stage_is_combinator(stage)) { return SRMECH_ERR_NOT_IMPL; }
        opn = srmech_json_object_get(stage, "op");
        if (opn == NULL || opn->type != SRMECH_JSON_STRING) {
            return SRMECH_ERR_NOT_IMPL;
        }
        st = dsl_leaf_dispatch(b, opn->u.str.ptr, opn->u.str.len, stage, cur, &nxt);
        if (st != SRMECH_OK) { return st; }
        cur = nxt;
    }
    *final_out = cur;                 /* empty stage array -> input (identity chain) */
    return SRMECH_OK;
}

/* ------------------------------------------------------------------
 * srmech_dsl_chain_run — the entry point. Parse chain + input-descriptor trees,
 * thread the value, marshal the final value back as an F1 descriptor.
 * ------------------------------------------------------------------ */

/* Run + write: parse the input desc, run the linear stages, emit the output desc.
 * Reserves a writer arena at the TAIL of `b` (builder half | write-scratch half);
 * the middle backs the run carriers + the emit item-pointer scratch. Both writer
 * bases are void*-aligned. Kept < 60 lines (mirrors cr_run_and_write). */
static srmech_status_t dsl_run_and_write(const srmech_json_value_t *chain,
                                         const srmech_json_value_t *input_desc,
                                         dcr_bump_t *b, size_t wsz,
                                         char *out, size_t out_cap, size_t *out_len)
{
    dcr_bump_t wb; dv_value_t *input, *final_v = NULL; srmech_json_builder_t bd;
    srmech_json_value_t *desc; unsigned char *tail_end, *wa; size_t region, half;
    srmech_status_t st;
    assert(chain != NULL && b != NULL && out_len != NULL);
    assert(b->cur <= b->end);
    input = dv_from_desc(b, input_desc, 0u);
    if (input == NULL) { return SRMECH_ERR_NOT_IMPL; }   /* unsupported seed -> pure */
    tail_end = b->end;
    if ((size_t)(b->end - b->cur) <= wsz + 4096u) { return SRMECH_ERR_OVERFLOW; }
    b->end = tail_end - wsz;                              /* shrink run bump */
    st = dsl_run_stages(chain, input, b, &final_v);
    if (st != SRMECH_OK) { return st; }
    wa = dcr_align(b->end);                               /* builder base, aligned */
    if (wa >= tail_end) { return SRMECH_ERR_OVERFLOW; }
    region = (size_t)(tail_end - wa); half = region / 2u;
    st = srmech_json_builder_init(&bd, wa, half);
    if (st != SRMECH_OK) { return st; }
    desc = dv_to_desc(&bd, final_v, b, 0u);              /* item scratch from run bump */
    if (desc == NULL || bd.failed) { return SRMECH_ERR_OVERFLOW; }
    wb.cur = dcr_align(wa + half); wb.end = tail_end;     /* write scratch */
    { size_t need = srmech_json_write_arena_bytes(desc);
      if (wb.cur >= wb.end || need > (size_t)(wb.end - wb.cur)) {
          return SRMECH_ERR_OVERFLOW;
      }
      return srmech_json_write_ws(desc, out, out_cap, out_len, wb.cur, need); }
}

size_t srmech_dsl_chain_run_arena_bytes(size_t chain_len, size_t input_len)
{
    size_t parse = 128u * chain_len + 128u * input_len + 65536u;
    size_t run = 256u * (chain_len + input_len) + (1u << 20);
    size_t writer = 32768u + 16u * (chain_len + input_len);
    assert(sizeof(dv_value_t) <= 128u);
    assert(sizeof(srmech_json_value_t) <= 128u);
    return parse + run + writer;
}

srmech_status_t srmech_dsl_chain_run(const char *chain_json, size_t chain_len,
                                     const char *input_json, size_t input_len,
                                     void *ws, size_t ws_len,
                                     char *out, size_t out_cap, size_t *out_len)
{
    dcr_bump_t b; srmech_json_value_t *chain = NULL, *input_desc = NULL;
    srmech_status_t st; size_t pj, ij; unsigned char *pa, *ia;
    assert(out_len != NULL);
    assert(chain_json != NULL || chain_len == 0u);
    if (chain_json == NULL || input_json == NULL || ws == NULL || out == NULL ||
        out_len == NULL) { return SRMECH_ERR_NULL_ARG; }
    b.cur = (unsigned char *)ws; b.end = b.cur + ws_len;
    pj = 128u * chain_len + 16384u; ij = 128u * input_len + 16384u;
    pa = dcr_carve(&b, pj); ia = dcr_carve(&b, ij);
    if (pa == NULL || ia == NULL) { return SRMECH_ERR_OVERFLOW; }
    st = srmech_json_parse(chain_json, chain_len, pa, pj, &chain);
    if (st != SRMECH_OK) { return st; }
    st = srmech_json_parse(input_json, input_len, ia, ij, &input_desc);
    if (st != SRMECH_OK) { return st; }
    if (chain->type != SRMECH_JSON_OBJECT) { return SRMECH_ERR_BAD_INPUT; }
    return dsl_run_and_write(chain, input_desc, &b,
                             16384u + 8u * (chain_len + input_len),
                             out, out_cap, out_len);
}
