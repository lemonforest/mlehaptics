/* srmech_dsl_chain_run.c — the srmech.dsl Chain RUN-LOOP in C
 * (0.9.0rc182; ANNEX Batch B pt2; COMPLETES the DSL chain interpreter).
 *
 * The DSL `Chain.run` is a SIBLING interpreter to the cascade.compose chain-runner
 * (srmech_compose_run.c / srmech_chain_run) — it VALUE-THREADS: each stage's
 * output feeds the next stage's input, with NO @row/@input/@step references (the
 * compose runner resolves those; this one does not). It runs the LEAN cascade
 * ATOMS on f64/i64 carriers.
 *
 * rc181 (pt1) shipped the F1 carrier-FFI FOUNDATION: the tagged-union value
 * carrier, the leaf-dispatch table of C-backed unary atoms, the
 * build_chain_from_dict stage-IR parse, and the LINEAR (`then`-only) run. It
 * reused the srmech_compose_run.c SCAFFOLD IDIOMS (a forward-only bump arena, the
 * srmech_json parse/build, the rc103 defer-to-pure gate) WITHOUT touching
 * srmech_chain_run.
 *
 * rc182 (pt2 — THIS ship) adds the LOOP / FOLD / REDUCE combinators (the whole
 * chain interpreter, not just the linear spine) + the TOML front-end bridge
 * srmech_dsl_toml_chain_to_json. `parallel_body` (the Klein-4 host-thread fan-out)
 * still DEFERS to pure — a host-runtime affordance, not a C shell violation.
 *
 *   chain_json  : {"chain":{"name":..},"stage":[<stage>, ...]} — the
 *                 build_chain_from_dict discriminator grammar. A stage is one of:
 *                   {"op":..,<kwargs>..}                     — a linear atom
 *                   {"loop_n":N,"sub_chain":[<stage>,..]}    — bounded loop
 *                   {"fold_init":<scalar>,"fold_op":<op>}    — seeded fold
 *                   {"reduce_op":<op>}                       — seedless reduce
 *                 A `parallel_body` stage, a non-C leaf, or a non-C binary body
 *                 → the whole chain DEFERS to pure (rc103 inform-don't-limit).
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
 * FLOAT is emitted through srmech_json_write_ws, so as of rc403 (`#T1071`) the
 * numeric atoms are BYTE-IDENTICAL to CPython repr(float) — this line read
 * "round-trips at %.17g (NOT byte-identical ... WITHIN-TOL)" until then, which
 * was true of the old snprintf writer and is no longer true of the Ryu one.
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
 * asserts/function, no goto, DEPTH-BOUNDED recursion (DV_MAX_DEPTH for the value
 * carrier; DCR_MAX_SUBCHAIN_DEPTH for the loop sub-chain nesting), and BOUNDED
 * iteration (DCR_MAX_LOOP_N loop count / DCR_MAX_SEQ fold-reduce sequence length,
 * each an explicit compiled cap + assert; a data-dependent count past the cap
 * defers cleanly to pure), no abs/libm. Additive symbols → SRMECH_ABI_VERSION
 * stays 4 (the ctypes shim hasattr-guards). */

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
 * STAGE KEY-SET REFUSAL (v0.9.0rc449, `#T1158` — the gh #1653 residual)
 *
 * Every leaf above reads its kwargs by PULL — srmech_json_object_get(stage,
 * "orientation"), srmech_json_object_get(stage, "max_denominator"). Nothing ever
 * ENUMERATES the stage object's keys, so there is no code path that "drops" an
 * unknown one: the drop is the ABSENCE of an iteration. Worse, five of the seven
 * leaves never receive `stage` at all (leaf_magnitude / leaf_pin_slot /
 * leaf_chiral_flip / leaf_net_chirality / leaf_autocorrelation take (b, in, out)),
 * so for those every kwarg is structurally unreachable. The check therefore MUST
 * live at dispatch, not inside the leaves.
 *
 * MEASURED at rc448, bare C, best_rational_signed on 0.3333333333333333:
 *   {"op":"best_rational_signed","max_denominator":2}  -> OK, (0, 1)
 *   {"op":"best_rational_signed","max_denominatr":2}   -> OK, (1, 3)
 * One dropped letter. No crash, no decline — the constraint is silently dropped,
 * the default 100 is used, and a DIFFERENT NUMBER comes back, while Python raises
 * TypeError from the callable's own signature.
 *
 * ⚠️ WHY IN C AND NOT (ONLY) IN PYTHON. rc447 closed this class at the Python IR
 * builder: _then_native_desc now declines to emit a stage whose kwarg the op does
 * not accept. That makes the two projections AGREE, but it leaves C's ACCEPTANCE
 * behaviour untouched — and on a bare-C host there is no IR builder to decline,
 * so the malformed declaration was still accepted and computed. "The projections
 * agree" and "C refuses what it should" are different properties; only the second
 * one protects the host that ADR-0003 makes a first-class deliverable.
 *
 * SRMECH_ERR_BAD_INPUT, never SRMECH_ERR_NOT_IMPL. In this file NOT_IMPL is the
 * DEFER-TO-PURE channel (see the dispatch fall-through below), and saying "this
 * projection doesn't do it yet; the other one might" is false on a bare-C host,
 * where nothing will ever implement `max_denominatr`. An unknown key is malformed
 * against the grammar, which is what BAD_INPUT means — the same side of the line
 * the compose runner already puts its MIXED steps on.
 * ------------------------------------------------------------------ */

/* The C-runnable leaf ops, each paired with its tool-registry entry name.
 *
 * This is a NAME-to-NAME index, NOT a second copy of the key names — those come
 * from the registry entry's own params, which two shipped gates already pin
 * set-equal to the live Python signature from BOTH directions
 * (tests/test_mcp.py::test_schema_signature_alignment_no_drift, rc13, declared
 * subset-of bindable; tests/test_declared_param_completeness_rc408.py, declared
 * superset-of live). A third independent notion of "accepted keys" is exactly the
 * `#T1146` divergence in miniature, so this table does not carry one.
 *
 * Membership here is ALSO the validator's SCOPE. An op absent from this table is
 * one this projection does not run; it must keep DEFERRING, never start refusing,
 * or a bare-C host would reject chains a Python caller runs fine — the
 * stricter-than-Python failure the whole output-parity corpus is blind to.
 * .rodata, so JPL Rule 3 (no malloc) is untouched. */
static const struct {
    const char *bare;
    uint32_t    len;
    const char *full;
} DSL_LEAF_REG[7] = {
    { "magnitude",             9u, "srmech.cascade.magnitude" },
    { "reorient",              8u, "srmech.cascade.reorient" },
    { "pin_slot_at_zero",     16u, "srmech.cascade.pin_slot_at_zero" },
    { "best_rational_signed", 20u, "srmech.cascade.best_rational_signed" },
    { "chiral_flip",          11u, "srmech.cascade.chiral_flip" },
    { "net_chirality",        13u, "srmech.cascade.net_chirality" },
    { "autocorrelation",      15u, "srmech.cascade.autocorrelation" }
};

/* 1 iff `name` is the stage's own discriminator or a LEGAL kwarg of entry `e`.
 *
 * params[0] is the DATA CARRIER — threaded into the leaf as the chain value `in`,
 * never spelled as a stage kwarg — so it is deliberately NOT legal here. Spelling
 * it is the measured 7/7 residual (`.then('magnitude', x=5)` builds a stage the
 * pure path rejects with "got multiple values for argument 'x'"). A params[*] rule
 * would pass every existing test and still accept all seven, which is why
 * test_srmech_chain_run.c pins {"op":"magnitude","x":5} by itself. */
static int dsl_key_is_legal(const char *name, const srmech_tool_entry_t *e)
{
    uint32_t j;
    assert(name != NULL && e != NULL);
    assert(e->param_count > 0u);
    if (strcmp(name, "op") == 0) { return 1; }
    for (j = 1u; j < e->param_count; j++) {
        if (strcmp(name, e->params[j].name) == 0) { return 1; }
    }
    return 0;
}

/* SRMECH_OK when every key of `stage` is legal for `op`, or when `op` is not a
 * C-runnable leaf (the defer channel, untouched). BAD_INPUT on an unknown key. */
static srmech_status_t dsl_leaf_keyset_ok(const char *op, uint32_t opl,
                                          const srmech_json_value_t *stage)
{
    const srmech_tool_entry_t *e = NULL;
    uint32_t i;
    assert(op != NULL && stage != NULL);
    assert(stage->type == SRMECH_JSON_OBJECT);
    for (i = 0u; i < 7u; i++) {
        if (opl == DSL_LEAF_REG[i].len &&
            memcmp(op, DSL_LEAF_REG[i].bare, (size_t)opl) == 0) {
            e = srmech_tool_registry_find(DSL_LEAF_REG[i].full);
            break;
        }
    }
    if (i == 7u) { return SRMECH_OK; }   /* not a C leaf → dispatch defers below */
    /* ⚠️ NOT silent acceptance. A NULL here means an op this file DISPATCHES has
     * no registry entry — a broken library invariant, not a caller error. Falling
     * through to "accept" would let one typo in the table above disable the
     * validator for that op forever while every other op's tests stayed green. */
    if (e == NULL) { return SRMECH_ERR_INTERNAL; }
    for (i = 0u; i < stage->u.obj.n; i++) {
        if (!dsl_key_is_legal(stage->u.obj.keys[i], e)) {
            return SRMECH_ERR_BAD_INPUT;
        }
    }
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
    srmech_status_t kst;
    assert(b != NULL && op != NULL && out != NULL);
    assert(stage != NULL && in != NULL);
    /* `#T1158`: refuse a declared kwarg the op does not have, BEFORE any arm runs.
     * A flat key walk on purpose — re-entering dsl_run_stage_array would mint a
     * new Rule-1 recursion cycle beside the seeded one and fail the JPL audit. */
    kst = dsl_leaf_keyset_ok(op, opl, stage);
    if (kst != SRMECH_OK) { return kst; }
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
    return SRMECH_ERR_NOT_IMPL;   /* non-C UNARY leaf (chiral_dual/dft/...) -> pure */
}

/* ------------------------------------------------------------------
 * Combinator EXECUTION (rc182) — loop / fold / reduce over the F1 carrier. Each
 * combinator BOUNDS its work: the loop count (DCR_MAX_LOOP_N) + fold/reduce
 * sequence length (DCR_MAX_SEQ) are explicit compiled caps (JPL Rule 2 — a count
 * past the cap defers cleanly to pure), and the loop sub-chain nesting is bounded
 * by DCR_MAX_SUBCHAIN_DEPTH (JPL Rule 1 recursion guard).
 * ------------------------------------------------------------------ */

#define DCR_MAX_LOOP_N         (1u << 24)   /* bounded loop count               */
#define DCR_MAX_SEQ            (1u << 24)   /* bounded fold/reduce sequence len  */
#define DCR_MAX_SUBCHAIN_DEPTH 16u          /* bounded loop sub-chain nesting    */

/* Build an F1 carrier from a RAW JSON scalar — fold_init lives inline in the
 * stage dict as a plain JSON int/float/string (NOT an F1 {"k":..} descriptor).
 * A bool / null / container → NULL (the caller defers the whole chain to pure). */
static dv_value_t *dv_from_json_scalar(dcr_bump_t *b, const srmech_json_value_t *j)
{
    dv_value_t *out;
    assert(b != NULL);
    assert(b->cur <= b->end);
    if (j == NULL) { return NULL; }
    if (j->type == SRMECH_JSON_INT) { return dv_int(b, j->u.i); }
    if (j->type == SRMECH_JSON_DOUBLE) { return dv_float(b, j->u.f); }
    if (j->type == SRMECH_JSON_STRING) {
        out = dv_new(b, DV_STR);
        if (out == NULL) { return NULL; }
        out->s = j->u.str.ptr; out->slen = j->u.str.len;
        return out;
    }
    return NULL;                          /* bool / null / array / object -> pure */
}

/* The BINARY body dispatch (fold / reduce). cyclic_gcd is the C-backed binary op;
 * both operands must be non-negative DV_INT (the uint64 gcd surface — matching
 * the Python cascade.cyclic_gcd native-dispatch gate). Any other op / operand
 * shape → SRMECH_ERR_NOT_IMPL → the whole chain defers to the pure runner. */
static srmech_status_t dsl_binary_dispatch(dcr_bump_t *b, const char *op,
                                           uint32_t opl, const dv_value_t *acc,
                                           const dv_value_t *elem, dv_value_t **out)
{
    uint64_t g; srmech_status_t st;
    assert(b != NULL && op != NULL && out != NULL);
    assert(acc != NULL && elem != NULL);
    if (!(opl == 10u && memcmp(op, "cyclic_gcd", 10u) == 0)) {
        return SRMECH_ERR_NOT_IMPL;              /* only cyclic_gcd is C-binary   */
    }
    if (acc->kind != DV_INT || elem->kind != DV_INT) { return SRMECH_ERR_NOT_IMPL; }
    if (acc->i < 0 || elem->i < 0) { return SRMECH_ERR_NOT_IMPL; }  /* uint64 only */
    st = srmech_cascade_cyclic_gcd_u64((uint64_t)acc->i, (uint64_t)elem->i, &g);
    if (st != SRMECH_OK) { return st; }
    if (g > (uint64_t)INT64_MAX) { return SRMECH_ERR_NOT_IMPL; }    /* back to i64 */
    *out = dv_int(b, (int64_t)g);
    return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* ------------------------------------------------------------------
 * build_chain_from_dict-in-C: parse the stage array + thread the value. A plain
 * `op` stage runs the leaf-dispatch atom; a loop/fold/reduce/map_indexed
 * discriminator runs the combinator; a `parallel_body` discriminator, a missing
 * `op`, a non-C leaf, or a non-C binary/map body → SRMECH_ERR_NOT_IMPL (defer
 * to pure).
 * ------------------------------------------------------------------ */

/* 1 iff `stage` carries a combinator discriminator
 * (loop/fold/reduce/parallel/map_indexed). rc420 (`#T1114`): "map_op" is the
 * SIXTH form's key — a widening here must move in lockstep with the Python
 * dispatcher (_toml_chain.py) and the closure ratchet
 * (tests/test_combinator_kernel_closure.py), which now READS this array. */
static int dsl_stage_is_combinator(const srmech_json_value_t *stage)
{
    static const char *disc[7] = { "loop_n", "sub_chain", "fold_init",
                                   "fold_op", "reduce_op", "parallel_body",
                                   "map_op" };
    uint32_t i;
    assert(stage != NULL);
    assert(stage->type == SRMECH_JSON_OBJECT);
    for (i = 0u; i < 7u; i++) {
        if (srmech_json_object_get(stage, disc[i]) != NULL) { return 1; }
    }
    return 0;
}

/* Mutual recursion: the loop combinator re-enters the stage-runner for its
 * sub-chain (depth-bounded by DCR_MAX_SUBCHAIN_DEPTH). Single-line `;` prototype
 * (the named definition is below). */
static srmech_status_t dsl_run_stage_array(const srmech_json_value_t *, dv_value_t *, dcr_bump_t *, uint32_t, dv_value_t **);

/* loop {"loop_n":N,"sub_chain":[<stage>,..]} — value-thread the sub-chain N times
 * (each iteration's output feeds the next). N is BOUNDED by DCR_MAX_LOOP_N; a
 * larger / negative N, or a non-array sub_chain, → NOT_IMPL (defer to pure). */
static srmech_status_t dsl_run_loop(const srmech_json_value_t *stage, dv_value_t *cur,
                                    dcr_bump_t *b, uint32_t depth, dv_value_t **out)
{
    const srmech_json_value_t *ln = srmech_json_object_get(stage, "loop_n");
    const srmech_json_value_t *sc = srmech_json_object_get(stage, "sub_chain");
    dv_value_t *val = cur; int64_t i, n; srmech_status_t st;
    assert(stage != NULL && b != NULL && out != NULL);
    assert(cur != NULL);
    if (ln == NULL || ln->type != SRMECH_JSON_INT) { return SRMECH_ERR_NOT_IMPL; }
    if (sc == NULL || sc->type != SRMECH_JSON_ARRAY) { return SRMECH_ERR_NOT_IMPL; }
    n = ln->u.i;
    if (n < 0 || n > (int64_t)DCR_MAX_LOOP_N) { return SRMECH_ERR_NOT_IMPL; }
    for (i = 0; i < n; i++) {
        dv_value_t *nxt = NULL;
        assert(i < (int64_t)DCR_MAX_LOOP_N);            /* JPL Rule 2 bound */
        st = dsl_run_stage_array(sc, val, b, depth + 1u, &nxt);
        if (st != SRMECH_OK) { return st; }
        val = nxt;
    }
    *out = val;                                         /* loop_n == 0 -> input */
    return SRMECH_OK;
}

/* fold {"fold_init":<scalar>,"fold_op":<op>} — acc = fold_init; for each element
 * of the input LIST, acc = op(acc, elem). Empty list → acc = fold_init. */
static srmech_status_t dsl_run_fold(const srmech_json_value_t *stage, dv_value_t *cur,
                                    dcr_bump_t *b, dv_value_t **out)
{
    const srmech_json_value_t *fi = srmech_json_object_get(stage, "fold_init");
    const srmech_json_value_t *fo = srmech_json_object_get(stage, "fold_op");
    dv_value_t *acc; uint32_t i, n; srmech_status_t st;
    assert(stage != NULL && b != NULL && out != NULL);
    assert(cur != NULL);
    if (fo == NULL || fo->type != SRMECH_JSON_STRING) { return SRMECH_ERR_NOT_IMPL; }
    if (cur->kind != DV_LIST) { return SRMECH_ERR_NOT_IMPL; }   /* fold over a seq */
    acc = dv_from_json_scalar(b, fi);
    if (acc == NULL) { return SRMECH_ERR_NOT_IMPL; }            /* non-scalar seed */
    n = cur->n;
    if (n > (uint32_t)DCR_MAX_SEQ) { return SRMECH_ERR_NOT_IMPL; }
    for (i = 0u; i < n; i++) {
        dv_value_t *nxt = NULL;
        assert(i < (uint32_t)DCR_MAX_SEQ);
        st = dsl_binary_dispatch(b, fo->u.str.ptr, fo->u.str.len,
                                 acc, cur->items[i], &nxt);
        if (st != SRMECH_OK) { return st; }
        acc = nxt;
    }
    *out = acc;
    return SRMECH_OK;
}

/* reduce {"reduce_op":<op>} — acc = list[0]; fold op over the rest. An empty
 * list → NOT_IMPL (the pure functools.reduce raises ValueError; defer to it). */
static srmech_status_t dsl_run_reduce(const srmech_json_value_t *stage, dv_value_t *cur,
                                      dcr_bump_t *b, dv_value_t **out)
{
    const srmech_json_value_t *ro = srmech_json_object_get(stage, "reduce_op");
    dv_value_t *acc; uint32_t i, n; srmech_status_t st;
    assert(stage != NULL && b != NULL && out != NULL);
    assert(cur != NULL);
    if (ro == NULL || ro->type != SRMECH_JSON_STRING) { return SRMECH_ERR_NOT_IMPL; }
    if (cur->kind != DV_LIST || cur->n == 0u) { return SRMECH_ERR_NOT_IMPL; }
    n = cur->n;
    if (n > (uint32_t)DCR_MAX_SEQ) { return SRMECH_ERR_NOT_IMPL; }
    acc = cur->items[0];
    for (i = 1u; i < n; i++) {
        dv_value_t *nxt = NULL;
        assert(i < (uint32_t)DCR_MAX_SEQ);
        st = dsl_binary_dispatch(b, ro->u.str.ptr, ro->u.str.len,
                                 acc, cur->items[i], &nxt);
        if (st != SRMECH_OK) { return st; }
        acc = nxt;
    }
    *out = acc;
    return SRMECH_OK;
}

/* 1 iff a map body name is `seq_get` — bare, or dotted `....seq_get` (the
 * Python IR carries the dotted spelling `srmech.cascade.leaves.seq_get`).
 * The C map-body table is exactly this one entry today; an unknown body
 * defers the whole chain to pure (inform-don't-limit). */
static int dsl_map_body_is_seq_get(const char *op, uint32_t opl)
{
    assert(op != NULL);
    assert(opl > 0u);
    if (opl == 7u && memcmp(op, "seq_get", 7u) == 0) { return 1; }
    if (opl > 8u && memcmp(op + (opl - 8u), ".seq_get", 8u) == 0) { return 1; }
    return 0;
}

/* map_indexed {"map_op":<op>} (rc420, `#T1114` — the SIXTH combinator) —
 * out[k] = body(input, k) for k in 0..n-1 with n = len(input) FIXED AT
 * ENTRY: the map is data-SIZED, never data-DEPENDENT (no predicate decides
 * continuation), the same totality class as fold's element walk. The C body
 * table carries `seq_get` (data-first body(input, k) == input[k] — the
 * identity map); any other body / a non-LIST input / an over-cap length →
 * NOT_IMPL (defer to pure). Items are SHARED with the input carrier — dv
 * values are immutable through this runner, so aliasing is sound. */
static srmech_status_t dsl_run_map_indexed(const srmech_json_value_t *stage,
                                           dv_value_t *cur, dcr_bump_t *b,
                                           dv_value_t **out)
{
    const srmech_json_value_t *mo = srmech_json_object_get(stage, "map_op");
    dv_value_t *res; dv_value_t **items; uint32_t k, n;
    assert(stage != NULL && b != NULL && out != NULL);
    assert(cur != NULL);
    if (mo == NULL || mo->type != SRMECH_JSON_STRING) { return SRMECH_ERR_NOT_IMPL; }
    if (!dsl_map_body_is_seq_get(mo->u.str.ptr, mo->u.str.len)) {
        return SRMECH_ERR_NOT_IMPL;              /* non-C map body -> pure */
    }
    if (cur->kind != DV_LIST) { return SRMECH_ERR_NOT_IMPL; }  /* map over a seq */
    n = cur->n;                                  /* n FIXED AT ENTRY */
    if (n > (uint32_t)DCR_MAX_SEQ) { return SRMECH_ERR_NOT_IMPL; }
    res = dv_new(b, DV_LIST);
    if (res == NULL) { return SRMECH_ERR_OVERFLOW; }
    items = (dv_value_t **)dcr_carve(b, (size_t)n * sizeof(void *) + 1u);
    if (items == NULL) { return SRMECH_ERR_OVERFLOW; }
    for (k = 0u; k < n; k++) {
        assert(k < (uint32_t)DCR_MAX_SEQ);       /* JPL Rule 2 bound */
        items[k] = cur->items[k];                /* seq_get(input, k) */
    }
    res->items = items; res->n = n; res->is_tuple = 0;
    *out = res;
    return SRMECH_OK;
}

/* Run ONE combinator stage. A `parallel_body` fan-out DEFERS to pure (host
 * threads — inform-don't-limit, not a shell violation). */
static srmech_status_t dsl_run_combinator(const srmech_json_value_t *stage,
                                          dv_value_t *cur, dcr_bump_t *b,
                                          uint32_t depth, dv_value_t **out)
{
    assert(stage != NULL && b != NULL && out != NULL);
    assert(cur != NULL);
    if (srmech_json_object_get(stage, "parallel_body") != NULL) {
        return SRMECH_ERR_NOT_IMPL;                     /* host-thread fan-out */
    }
    if (srmech_json_object_get(stage, "map_op") != NULL) {
        return dsl_run_map_indexed(stage, cur, b, out);
    }
    if (srmech_json_object_get(stage, "loop_n") != NULL ||
        srmech_json_object_get(stage, "sub_chain") != NULL) {
        return dsl_run_loop(stage, cur, b, depth, out);
    }
    if (srmech_json_object_get(stage, "fold_init") != NULL ||
        srmech_json_object_get(stage, "fold_op") != NULL) {
        return dsl_run_fold(stage, cur, b, out);
    }
    if (srmech_json_object_get(stage, "reduce_op") != NULL) {
        return dsl_run_reduce(stage, cur, b, out);
    }
    return SRMECH_ERR_NOT_IMPL;
}

/* Run a STAGE ARRAY (the top-level chain's `stage`, or a loop sub-chain), value-
 * threading each stage's output into the next. Depth-bounded for the loop
 * sub-chain recursion (DCR_MAX_SUBCHAIN_DEPTH). */
static srmech_status_t dsl_run_stage_array(const srmech_json_value_t *stages,
                                           dv_value_t *input, dcr_bump_t *b,
                                           uint32_t depth, dv_value_t **final_out)
{
    dv_value_t *cur = input; uint32_t i, ns; srmech_status_t st;
    assert(b != NULL && final_out != NULL);
    assert(input != NULL);
    if (stages == NULL || stages->type != SRMECH_JSON_ARRAY) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (depth > DCR_MAX_SUBCHAIN_DEPTH) { return SRMECH_ERR_NOT_IMPL; }  /* nesting */
    ns = stages->u.arr.n;
    for (i = 0u; i < ns; i++) {
        const srmech_json_value_t *stage = stages->u.arr.items[i];
        const srmech_json_value_t *opn; dv_value_t *nxt = NULL;
        if (stage == NULL || stage->type != SRMECH_JSON_OBJECT) {
            return SRMECH_ERR_BAD_INPUT;
        }
        if (dsl_stage_is_combinator(stage)) {
            st = dsl_run_combinator(stage, cur, b, depth, &nxt);
        } else {
            opn = srmech_json_object_get(stage, "op");
            if (opn == NULL || opn->type != SRMECH_JSON_STRING) {
                return SRMECH_ERR_NOT_IMPL;
            }
            st = dsl_leaf_dispatch(b, opn->u.str.ptr, opn->u.str.len, stage, cur, &nxt);
        }
        if (st != SRMECH_OK) { return st; }
        cur = nxt;
    }
    *final_out = cur;                 /* empty stage array -> input (identity chain) */
    return SRMECH_OK;
}

static srmech_status_t dsl_run_stages(const srmech_json_value_t *chain,
                                      dv_value_t *input, dcr_bump_t *b,
                                      dv_value_t **final_out)
{
    const srmech_json_value_t *stages;
    assert(chain != NULL && b != NULL && final_out != NULL);
    assert(input != NULL);
    stages = srmech_json_object_get(chain, "stage");
    return dsl_run_stage_array(stages, input, b, 0u, final_out);
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

/* ------------------------------------------------------------------
 * srmech_dsl_toml_chain_to_json — the rc182 TOML front-end bridge. Convert a
 * parsed TOML tree into the equivalent canonical-JSON build_chain_from_dict IR:
 * TABLE→object, ARRAY→array, INT→int, FLOAT→double, BOOL→bool, STRING→string.
 * The item-pointer arrays for arrays/objects are carved from a transient
 * `scratch` bump (new_array/new_object COPY them into the builder arena);
 * TABLE keys are the parse arena's NUL-terminated key strings, passed straight
 * to new_object (kept alive by the parse arena). Depth-bounded recursion.
 * ------------------------------------------------------------------ */

/* Single-line `;` prototype (the named definition is below). */
static srmech_json_value_t *toml_to_json(srmech_json_builder_t *, const srmech_toml_value_t *, dcr_bump_t *, uint32_t);

static srmech_json_value_t *toml_arr_to_json(srmech_json_builder_t *bd,
                                             const srmech_toml_value_t *tv,
                                             dcr_bump_t *scratch, uint32_t depth)
{
    srmech_json_value_t **kids; uint32_t i, n;
    assert(bd != NULL && tv != NULL && scratch != NULL);
    assert(tv->type == SRMECH_TOML_ARRAY);
    n = tv->u.arr.n;
    kids = (srmech_json_value_t **)dcr_carve(scratch, (size_t)n * sizeof(void *) + 1u);
    if (kids == NULL) { return NULL; }
    for (i = 0u; i < n; i++) {
        kids[i] = toml_to_json(bd, tv->u.arr.items[i], scratch, depth + 1u);
        if (kids[i] == NULL) { return NULL; }
    }
    return srmech_json_new_array(bd, kids, n);
}

static srmech_json_value_t *toml_tbl_to_json(srmech_json_builder_t *bd,
                                             const srmech_toml_value_t *tv,
                                             dcr_bump_t *scratch, uint32_t depth)
{
    srmech_json_value_t **vals; uint32_t i, n;
    assert(bd != NULL && tv != NULL && scratch != NULL);
    assert(tv->type == SRMECH_TOML_TABLE);
    n = tv->u.tbl.n;
    vals = (srmech_json_value_t **)dcr_carve(scratch, (size_t)n * sizeof(void *) + 1u);
    if (vals == NULL) { return NULL; }
    for (i = 0u; i < n; i++) {
        vals[i] = toml_to_json(bd, tv->u.tbl.vals[i], scratch, depth + 1u);
        if (vals[i] == NULL) { return NULL; }
    }
    return srmech_json_new_object(bd, tv->u.tbl.keys, vals, n);
}

static srmech_json_value_t *toml_to_json(srmech_json_builder_t *bd,
                                         const srmech_toml_value_t *tv,
                                         dcr_bump_t *scratch, uint32_t depth)
{
    assert(bd != NULL && scratch != NULL);
    assert(depth <= (uint32_t)SRMECH_TOML_MAX_DEPTH + 1u);
    if (tv == NULL || depth > (uint32_t)SRMECH_TOML_MAX_DEPTH) { return NULL; }
    if (tv->type == SRMECH_TOML_STRING) {
        return srmech_json_new_string(bd, tv->u.str.ptr, tv->u.str.len);
    }
    if (tv->type == SRMECH_TOML_INT) { return srmech_json_new_int(bd, tv->u.i); }
    if (tv->type == SRMECH_TOML_FLOAT) { return srmech_json_new_double(bd, tv->u.f); }
    if (tv->type == SRMECH_TOML_BOOL) { return srmech_json_new_bool(bd, tv->u.b); }
    if (tv->type == SRMECH_TOML_ARRAY) {
        return toml_arr_to_json(bd, tv, scratch, depth);
    }
    if (tv->type == SRMECH_TOML_TABLE) {
        return toml_tbl_to_json(bd, tv, scratch, depth);
    }
    return NULL;
}

size_t srmech_dsl_toml_chain_to_json_arena_bytes(size_t toml_len)
{
    /* parse tree + json-mirror builder + pointer scratch + writer scratch, all
     * scaling with the source size (the JSON mirror is ~1:1 in node count). */
    assert(sizeof(srmech_toml_value_t) <= 256u);
    assert(sizeof(srmech_json_value_t) <= 256u);
    return 512u * toml_len + 262144u;
}

/* Convert a raw parse root to JSON in the builder + writer regions of `b`; kept
 * < 60 lines (mirrors dsl_run_and_write's writer-tail layout). */
static srmech_status_t toml_build_and_write(const srmech_toml_value_t *root,
                                            dcr_bump_t *b, char *out,
                                            size_t out_cap, size_t *out_len)
{
    dcr_bump_t scratch; srmech_json_builder_t bd; srmech_json_value_t *jroot;
    unsigned char *ba, *wa; size_t rem, sc_len, bd_len, w_len, need;
    srmech_status_t st;
    assert(root != NULL && b != NULL && out_len != NULL);
    assert(b->cur <= b->end);
    rem = (size_t)(b->end - b->cur);
    if (rem < 8192u) { return SRMECH_ERR_OVERFLOW; }
    sc_len = rem / 4u; bd_len = rem / 2u;
    scratch.cur = dcr_align(b->cur); scratch.end = scratch.cur + sc_len;
    ba = dcr_align(scratch.end);
    if (ba >= b->end || bd_len > (size_t)(b->end - ba)) { return SRMECH_ERR_OVERFLOW; }
    st = srmech_json_builder_init(&bd, ba, bd_len);
    if (st != SRMECH_OK) { return st; }
    jroot = toml_to_json(&bd, root, &scratch, 0u);
    if (jroot == NULL || bd.failed) { return SRMECH_ERR_OVERFLOW; }
    wa = dcr_align(ba + bd_len);
    if (wa >= b->end) { return SRMECH_ERR_OVERFLOW; }
    w_len = (size_t)(b->end - wa);
    need = srmech_json_write_arena_bytes(jroot);
    if (need > w_len) { return SRMECH_ERR_OVERFLOW; }
    return srmech_json_write_ws(jroot, out, out_cap, out_len, wa, need);
}

srmech_status_t srmech_dsl_toml_chain_to_json(const char *toml_src, size_t toml_len,
                                              void *ws, size_t ws_len,
                                              char *out, size_t out_cap,
                                              size_t *out_len)
{
    dcr_bump_t b; srmech_toml_value_t *root = NULL; unsigned char *pa;
    size_t pj; srmech_status_t st;
    assert(out_len != NULL);
    assert(toml_src != NULL || toml_len == 0u);
    if (toml_src == NULL || ws == NULL || out == NULL || out_len == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    b.cur = (unsigned char *)ws; b.end = b.cur + ws_len;
    pj = 256u * toml_len + 65536u;
    pa = dcr_carve(&b, pj);
    if (pa == NULL) { return SRMECH_ERR_OVERFLOW; }
    st = srmech_toml_parse(toml_src, toml_len, pa, pj, &root);
    if (st != SRMECH_OK) { return st; }
    if (root == NULL || root->type != SRMECH_TOML_TABLE) {
        return SRMECH_ERR_BAD_INPUT;
    }
    return toml_build_and_write(root, &b, out, out_cap, out_len);
}
