/* _1653_wedge_optable_rc444.c — gh #1653 ROUND-2: PROVE THE WEDGE.
 *
 * THE QUESTION. Round 1 measured that 11 of the 18 executable
 * cascade-catalog chains are rejected by the shipped C chain-runner for
 * ONE reason only: the 10-entry op table in `cr_dispatch`
 * (srmech_compose_run.c:616). The C PARSE half already ACCEPTS all 11.
 * So: is the math for those 11 chains ALREADY in libsrmech.a — making the
 * rcN a dispatch-table edit — or is real C implementation owed?
 *
 * WHAT THIS FILE IS. A STANDALONE bare-C host. It links
 * c/build/libsrmech.a and NOTHING else (no libm, no Python, no ctypes).
 * It re-implements the chain-run loop LOCALLY (this file never edits
 * c/src) with an EXTENDED op table covering all 23 ops those 11 chains
 * name, calling the EXISTING srmech_* exports wherever one exists. It
 * then runs every declared proof case of all 11 chains from the SHIPPED
 * descriptor inputs and prints each final value in the same canonical
 * spelling `_1653_wedge_pycheck_rc444.py` prints, so the comparison is a
 * byte diff.
 *
 * THREE MEASUREMENTS IT MAKES, not three claims it repeats:
 *   (1) per-op: does a callable srmech_* symbol exist, is the op a
 *       composition of existing exports, or is nothing there;
 *   (2) per-case: does a bare-C host even INGEST the descriptor input
 *       (srmech_json_parse rc), then does the extended-table run produce
 *       a value;
 *   (3) the SHIPPED-SURFACE ABLATION: whether `@step[N].output[K]`
 *       element indexing — which two of the eleven chains need — is a
 *       SECOND C-side blocker independent of the op table. It probes the
 *       real srmech_chain_run with two chains built from IN-TABLE ops
 *       only, differing solely in that one ref.
 *
 * SIGN HANDLING. Every sign split here is the named Class-K pin-slot op
 * (srmech_cascade_pin_slot_at_zero_f64) and every sign re-application is
 * the named Class-C op (srmech_cascade_reorient_i64/_f64). No ALU
 * magnitude idiom appears anywhere in this file.
 *
 * JPL Power-of-Ten: no recursion, no goto, no malloc (two file-scope
 * static arenas are carved forward by the caller-arena discipline; every
 * op receives its scratch from the arena it is handed), every function
 * <= 60 lines with >= 2 asserts, srmech_status_t returns checked.
 *
 * BUILD (from the worktree root, WT):
 *   gcc -std=c11 -O2 -I$WT/docs/srmech/c/include \
 *       -o /tmp/wedge $WT/docs/srmech/notes/_1653_wedge_optable_rc444.c \
 *       $WT/docs/srmech/c/build/libsrmech.a
 * RUN:
 *   /tmp/wedge $WT/docs/srmech/notes/_1653_wedge_barec
 * (that directory is written by _1653_wedge_pycheck_rc444.py).
 */

#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "srmech.h"

/* ------------------------------------------------------------------
 * Arenas. Two file-scope static regions; everything is bump-carved
 * forward out of them. No dynamic allocation anywhere.
 * ------------------------------------------------------------------ */

#define WA_JSON_BYTES   (4u * 1024u * 1024u)
#define WA_RUN_BYTES    (24u * 1024u * 1024u)
#define WA_FILE_BYTES   (1u * 1024u * 1024u)

static unsigned char wa_json_arena[WA_JSON_BYTES];
static unsigned char wa_run_arena[WA_RUN_BYTES];
static char          wa_file_buf[WA_FILE_BYTES];
static char          wa_file_buf2[WA_FILE_BYTES];

typedef struct { unsigned char *cur; unsigned char *end; } wa_bump_t;

static unsigned char *wa_align(unsigned char *p)
{
    uintptr_t a = (uintptr_t)sizeof(void *);
    uintptr_t pad;
    assert(p != NULL);
    assert(a >= 4u);
    pad = (a - ((uintptr_t)p % a)) % a;
    return p + pad;
}

static unsigned char *wa_carve(wa_bump_t *b, size_t n)
{
    unsigned char *p;
    assert(b != NULL);
    assert(b->cur <= b->end);
    p = wa_align(b->cur);
    if (p > b->end || n > (size_t)(b->end - p)) { return NULL; }
    b->cur = p + n;
    return p;
}

/* ------------------------------------------------------------------
 * Value carrier. Wider than the shipped cr_value_t because the wedge
 * chains carry doubles, byte buffers and a dense matrix as well as
 * integers — that WIDTH is itself one of the findings.
 * ------------------------------------------------------------------ */

typedef enum {
    WV_NONE = 0, WV_INT, WV_UINT, WV_DBL, WV_STR, WV_BYTES, WV_LIST, WV_MAT
} wv_kind_t;

typedef struct wv {
    wv_kind_t kind;
    int64_t   i;                       /* WV_INT                       */
    uint64_t  u;                       /* WV_UINT                      */
    double    d;                       /* WV_DBL                       */
    const char *s; uint32_t slen;      /* WV_STR   (arena or json)     */
    const unsigned char *by; uint32_t bylen;   /* WV_BYTES             */
    struct wv **items; uint32_t n;     /* WV_LIST                      */
    const double *m; uint32_t rows, cols;      /* WV_MAT row-major     */
} wv_t;

static wv_t *wv_new(wa_bump_t *b, wv_kind_t k)
{
    wv_t *v;
    assert(b != NULL);
    assert(k >= WV_NONE && k <= WV_MAT);
    v = (wv_t *)wa_carve(b, sizeof(wv_t));
    if (v == NULL) { return NULL; }
    memset(v, 0, sizeof(*v));
    v->kind = k;
    return v;
}

static wv_t *wv_int(wa_bump_t *b, int64_t x)
{
    wv_t *v = wv_new(b, WV_INT);
    assert(b != NULL);
    assert(sizeof(x) == 8u);
    if (v != NULL) { v->i = x; }
    return v;
}

static wv_t *wv_uint(wa_bump_t *b, uint64_t x)
{
    wv_t *v = wv_new(b, WV_UINT);
    assert(b != NULL);
    assert(sizeof(x) == 8u);
    if (v != NULL) { v->u = x; }
    return v;
}

static wv_t *wv_dbl(wa_bump_t *b, double x)
{
    wv_t *v = wv_new(b, WV_DBL);
    assert(b != NULL);
    assert(sizeof(x) == 8u);
    if (v != NULL) { v->d = x; }
    return v;
}

/* A 2-element list — the shape pin_slot_at_zero / best_rational / pair
 * all return. */
static wv_t *wv_pair(wa_bump_t *b, wv_t *a, wv_t *c)
{
    wv_t *v = wv_new(b, WV_LIST);
    wv_t **it;
    assert(b != NULL);
    assert(a != NULL && c != NULL);
    if (v == NULL) { return NULL; }
    it = (wv_t **)wa_carve(b, 2u * sizeof(wv_t *));
    if (it == NULL) { return NULL; }
    it[0] = a; it[1] = c;
    v->items = it; v->n = 2u;
    return v;
}

/* Read an integral value out of an INT / UINT carrier. 0 on a non-int. */
static int wv_as_u64(const wv_t *v, uint64_t *out)
{
    assert(v != NULL);
    assert(out != NULL);
    if (v->kind == WV_UINT) { *out = v->u; return 1; }
    if (v->kind == WV_INT && v->i >= 0) { *out = (uint64_t)v->i; return 1; }
    return 0;
}

/* Read a real value out of a DBL / INT carrier. 0 on anything else. */
static int wv_as_dbl(const wv_t *v, double *out)
{
    assert(v != NULL);
    assert(out != NULL);
    if (v->kind == WV_DBL) { *out = v->d; return 1; }
    if (v->kind == WV_INT) { *out = (double)v->i; return 1; }
    return 0;
}

/* Materialise a WV_LIST of reals as a contiguous double array. */
static int wv_as_dbl_arr(wa_bump_t *b, const wv_t *v, double **out, uint32_t *n)
{
    uint32_t k; double *p;
    assert(b != NULL && v != NULL);
    assert(out != NULL && n != NULL);
    if (v->kind != WV_LIST) { return 0; }
    *n = v->n;
    p = (double *)wa_carve(b, (size_t)v->n * sizeof(double) + 8u);
    if (p == NULL) { return 0; }
    for (k = 0u; k < v->n; k++) {
        if (v->items[k] == NULL || !wv_as_dbl(v->items[k], &p[k])) { return 0; }
    }
    *out = p;
    return 1;
}

/* ------------------------------------------------------------------
 * JSON -> value carrier, and reference resolution.
 * ------------------------------------------------------------------ */

static wv_t *wr_scalar(wa_bump_t *b, const srmech_json_value_t *j)
{
    wv_t *v;
    assert(b != NULL);
    assert(j == NULL || j->type <= SRMECH_JSON_OBJECT);
    if (j == NULL) { return NULL; }
    if (j->type == SRMECH_JSON_INT) { return wv_int(b, j->u.i); }
    if (j->type == SRMECH_JSON_DOUBLE) { return wv_dbl(b, j->u.f); }
    if (j->type == SRMECH_JSON_NULL) { return wv_new(b, WV_NONE); }
    if (j->type != SRMECH_JSON_STRING) { return NULL; }
    v = wv_new(b, WV_STR);
    if (v == NULL) { return NULL; }
    v->s = j->u.str.ptr; v->slen = j->u.str.len;
    return v;
}

/* An array of arrays of reals -> WV_MAT (row-major). NULL if not that. */
static wv_t *wr_mat(wa_bump_t *b, const srmech_json_value_t *j)
{
    uint32_t r, c, cols; double *buf; wv_t *v;
    assert(b != NULL && j != NULL);
    assert(j->type == SRMECH_JSON_ARRAY);
    if (j->u.arr.n == 0u) { return NULL; }
    if (j->u.arr.items[0] == NULL ||
        j->u.arr.items[0]->type != SRMECH_JSON_ARRAY) { return NULL; }
    cols = j->u.arr.items[0]->u.arr.n;
    buf = (double *)wa_carve(b, (size_t)j->u.arr.n * cols * sizeof(double) + 8u);
    if (buf == NULL) { return NULL; }
    for (r = 0u; r < j->u.arr.n; r++) {
        const srmech_json_value_t *row = j->u.arr.items[r];
        if (row == NULL || row->type != SRMECH_JSON_ARRAY ||
            row->u.arr.n != cols) { return NULL; }
        for (c = 0u; c < cols; c++) {
            const srmech_json_value_t *e = row->u.arr.items[c];
            if (e == NULL) { return NULL; }
            if (e->type == SRMECH_JSON_DOUBLE) { buf[r * cols + c] = e->u.f; }
            else if (e->type == SRMECH_JSON_INT) {
                buf[r * cols + c] = (double)e->u.i;
            } else { return NULL; }
        }
    }
    v = wv_new(b, WV_MAT);
    if (v == NULL) { return NULL; }
    v->m = buf; v->rows = j->u.arr.n; v->cols = cols;
    return v;
}

/* An array node -> WV_MAT (nested) or a flat WV_LIST. No recursion. */
static wv_t *wr_array(wa_bump_t *b, const srmech_json_value_t *j)
{
    wv_t *v; wv_t **it; uint32_t k;
    assert(b != NULL && j != NULL);
    assert(j->type == SRMECH_JSON_ARRAY);
    if (j->u.arr.n > 0u && j->u.arr.items[0] != NULL &&
        j->u.arr.items[0]->type == SRMECH_JSON_ARRAY) {
        return wr_mat(b, j);
    }
    v = wv_new(b, WV_LIST);
    if (v == NULL) { return NULL; }
    v->n = j->u.arr.n;
    it = (wv_t **)wa_carve(b, (size_t)v->n * sizeof(wv_t *) + 8u);
    if (it == NULL) { return NULL; }
    for (k = 0u; k < v->n; k++) {
        it[k] = wr_scalar(b, j->u.arr.items[k]);
        if (it[k] == NULL) { return NULL; }
    }
    v->items = it;
    return v;
}

static wv_t *wr_json_to_wv(wa_bump_t *b, const srmech_json_value_t *j)
{
    assert(b != NULL);
    assert(j == NULL || j->type <= SRMECH_JSON_OBJECT);
    if (j != NULL && j->type == SRMECH_JSON_ARRAY) { return wr_array(b, j); }
    return wr_scalar(b, j);
}

typedef struct {
    const srmech_json_value_t *inputs;
    wv_t     **step_out;
    uint32_t   cur;
    wa_bump_t *b;
    int        used_output_index;   /* 1 once a @step[N].output[K] was seen */
} wr_ctx_t;

/* Resolve "@input.KEY" / "@step[N].output" / "@step[N].output[K]".
 * The last form is the one the SHIPPED cr_resolve_ref rejects outright. */
static wv_t *wr_resolve_ref(wr_ctx_t *c, const char *ref, uint32_t len)
{
    const char *e = ref + len; const char *p; char key[96]; size_t kl = 0u;
    assert(c != NULL && ref != NULL);
    assert(c->b != NULL);
    if (len < 2u || ref[0] != '@') { return NULL; }
    p = ref + 1;
    if (len >= 7u && memcmp(p, "input.", 6u) == 0) {
        const char *k = p + 6;
        while (k < e) {
            if (kl + 1u >= sizeof(key)) { return NULL; }
            key[kl++] = *k++;
        }
        key[kl] = '\0';
        if (c->inputs == NULL || c->inputs->type != SRMECH_JSON_OBJECT) {
            return NULL;
        }
        return wr_json_to_wv(c->b, srmech_json_object_get(c->inputs, key));
    }
    if (len >= 6u && memcmp(p, "step[", 5u) == 0) {
        const char *k = p + 5; uint32_t idx = 0u; const char *rest; wv_t *sv;
        while (k < e && *k >= '0' && *k <= '9') {
            idx = idx * 10u + (uint32_t)(*k++ - '0');
        }
        if (k >= e || *k != ']') { return NULL; }
        if (idx >= c->cur) { return NULL; }
        rest = k + 1;
        if (rest + 7 <= e && memcmp(rest, ".output", 7u) == 0) { rest += 7; }
        sv = c->step_out[idx];
        if (rest == e) { return sv; }
        if (*rest != '[' || sv == NULL || sv->kind != WV_LIST) { return NULL; }
        { uint32_t ei = 0u; const char *q = rest + 1;
          while (q < e && *q >= '0' && *q <= '9') {
              ei = ei * 10u + (uint32_t)(*q++ - '0');
          }
          if (q >= e || *q != ']' || q + 1 != e) { return NULL; }
          if (ei >= sv->n) { return NULL; }
          c->used_output_index = 1;
          return sv->items[ei]; }
    }
    return NULL;
}

static wv_t *wr_arg(wr_ctx_t *c, const srmech_json_value_t *args,
                    const char *keyname)
{
    const srmech_json_value_t *j;
    assert(c != NULL && args != NULL);
    assert(keyname != NULL);
    j = srmech_json_object_get(args, keyname);
    if (j == NULL) { return NULL; }
    if (j->type == SRMECH_JSON_STRING && j->u.str.len > 0u &&
        j->u.str.ptr[0] == '@') {
        return wr_resolve_ref(c, j->u.str.ptr, j->u.str.len);
    }
    return wr_json_to_wv(c->b, j);
}

/* ------------------------------------------------------------------
 * Class I — the five DIRECT modular exports plus the one composition.
 * ------------------------------------------------------------------ */

static srmech_status_t wo_class_i(wr_ctx_t *c, const char *op, uint32_t ol,
                                  const srmech_json_value_t *args, wv_t **out)
{
    uint64_t a = 0u, b2 = 0u, n = 0u, r = 0u;
    wv_t *va, *vb, *vn;
    srmech_status_t st = SRMECH_ERR_NOT_IMPL;
    assert(c != NULL && op != NULL);
    assert(args != NULL && out != NULL);
    va = wr_arg(c, args, "a");
    if (va == NULL || !wv_as_u64(va, &a)) { return SRMECH_ERR_BAD_INPUT; }
    if (ol == 3u && memcmp(op, "gcd", 3u) == 0) {
        vb = wr_arg(c, args, "b");
        if (vb == NULL || !wv_as_u64(vb, &b2)) { return SRMECH_ERR_BAD_INPUT; }
        st = srmech_gcd(a, b2, &r);
    } else if (ol == 7u && memcmp(op, "mod_inv", 7u) == 0) {
        vn = wr_arg(c, args, "n");
        if (vn == NULL || !wv_as_u64(vn, &n)) { return SRMECH_ERR_BAD_INPUT; }
        st = srmech_mod_inv(a, n, &r);
    } else if (ol == 7u && memcmp(op, "mod_pow", 7u) == 0) {
        vb = wr_arg(c, args, "k"); vn = wr_arg(c, args, "n");
        if (vb == NULL || vn == NULL || !wv_as_u64(vb, &b2) ||
            !wv_as_u64(vn, &n)) { return SRMECH_ERR_BAD_INPUT; }
        st = srmech_mod_pow(a, b2, n, &r);
    } else if ((ol == 7u && memcmp(op, "mod_add", 7u) == 0) ||
               (ol == 7u && memcmp(op, "mod_mul", 7u) == 0)) {
        vb = wr_arg(c, args, "b"); vn = wr_arg(c, args, "n");
        if (vb == NULL || vn == NULL || !wv_as_u64(vb, &b2) ||
            !wv_as_u64(vn, &n)) { return SRMECH_ERR_BAD_INPUT; }
        st = (op[4] == 'a') ? srmech_mod_add(a, b2, n, &r)
                            : srmech_mod_mul(a, b2, n, &r);
    }
    if (st != SRMECH_OK) { return st; }
    *out = wv_uint(c->b, r);
    return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* mod_mul_wide: NOT a single export. Composed exactly as Python composes
 * it — srmech_bigint_mul for the wide product, srmech_bigint_divmod for
 * the reduction (Python-floor remainder, matching the `% n`). */
static srmech_status_t wo_mod_mul_wide(wr_ctx_t *c,
                                        const srmech_json_value_t *args,
                                        wv_t **out)
{
    uint64_t a = 0u, b2 = 0u, n = 0u; wv_t *va, *vb, *vn;
    srmech_bigint_t ba, bb, bn, bp, br;
    uint32_t la[4], lb[4], ln[4], lp[16], lr[8];
    unsigned char ws[4096];
    srmech_status_t st;
    assert(c != NULL && args != NULL);
    assert(out != NULL);
    va = wr_arg(c, args, "a"); vb = wr_arg(c, args, "b");
    vn = wr_arg(c, args, "n");
    if (va == NULL || vb == NULL || vn == NULL) { return SRMECH_ERR_BAD_INPUT; }
    if (!wv_as_u64(va, &a) || !wv_as_u64(vb, &b2) || !wv_as_u64(vn, &n)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (n == 0u || a > (uint64_t)INT64_MAX || b2 > (uint64_t)INT64_MAX ||
        n > (uint64_t)INT64_MAX) { return SRMECH_ERR_BAD_INPUT; }
    ba.sign = 0; ba.n = 0u; ba.cap = 4u; ba.limbs = la;
    bb.sign = 0; bb.n = 0u; bb.cap = 4u; bb.limbs = lb;
    bn.sign = 0; bn.n = 0u; bn.cap = 4u; bn.limbs = ln;
    bp.sign = 0; bp.n = 0u; bp.cap = 16u; bp.limbs = lp;
    br.sign = 0; br.n = 0u; br.cap = 8u; br.limbs = lr;
    st = srmech_bigint_set_i64(&ba, (int64_t)a);
    if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&bb, (int64_t)b2); }
    if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&bn, (int64_t)n); }
    if (st == SRMECH_OK) { st = srmech_bigint_mul(&bp, &ba, &bb); }
    if (st == SRMECH_OK) {
        st = srmech_bigint_divmod(NULL, &br, &bp, &bn, ws, sizeof(ws));
    }
    if (st != SRMECH_OK) { return st; }
    { uint64_t r = 0u; uint32_t k = br.n;
      while (k > 0u) { k--; r = (r << 32) | (uint64_t)br.limbs[k]; }
      *out = wv_uint(c->b, r); }
    return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* ------------------------------------------------------------------
 * Classes K / C / N — the named pin-slot + orientation + anchor ops.
 * ------------------------------------------------------------------ */

/* The libm-free round-half-to-even kernel. The identical arithmetic
 * already runs inside srmech_cascade_best_rational_signed_f64, but it is
 * a file-static there — there is NO callable export, so a chain step
 * naming `scale_round_half_even` has nothing to dispatch to. This is the
 * measurement, not a preference. */
static int64_t wo_round_half_even(double v)
{
    int64_t t; double frac; int64_t r;
    assert(v >= 0.0);
    assert(v < 9223372036854775808.0);
    t = (int64_t)v;
    frac = v - (double)t;
    r = t;
    if (frac > 0.5) { r = t + 1; }
    else if (frac == 0.5) { r = t + (t & (int64_t)1); }
    return r;
}

/* pin_slot_at_zero -> (orientation:int, magnitude:float), the shipped
 * Class-K export called by name. */
static srmech_status_t wo_pin_slot(wr_ctx_t *c, const srmech_json_value_t *args,
                                    wv_t **out)
{
    wv_t *vx; double x = 0.0, mag = 0.0; int8_t ori = 0; srmech_status_t st;
    assert(c != NULL && args != NULL);
    assert(out != NULL);
    vx = wr_arg(c, args, "x");
    if (vx == NULL || !wv_as_dbl(vx, &x)) { return SRMECH_ERR_BAD_INPUT; }
    st = srmech_cascade_pin_slot_at_zero_f64(x, &ori, &mag);
    if (st != SRMECH_OK) { return st; }
    *out = wv_pair(c->b, wv_int(c->b, (int64_t)ori), wv_dbl(c->b, mag));
    return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* dead_band(value, band): value when value >= band, else value's own
 * zero. A pure comparison on an already-non-negative Class-K magnitude —
 * no export exists and none is needed. */
static srmech_status_t wo_dead_band(wr_ctx_t *c,
                                     const srmech_json_value_t *args,
                                     wv_t **out)
{
    wv_t *vv, *vb; double v = 0.0, band = 0.0;
    assert(c != NULL && args != NULL);
    assert(out != NULL);
    vv = wr_arg(c, args, "value"); vb = wr_arg(c, args, "band");
    if (vv == NULL || vb == NULL) { return SRMECH_ERR_BAD_INPUT; }
    if (!wv_as_dbl(vv, &v) || !wv_as_dbl(vb, &band)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    *out = wv_dbl(c->b, (v >= band) ? v : (v * 0.0));
    return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* reorient(orientation, value): the named Class-C op, type-preserving —
 * the i64 export for an integer carrier, the f64 export for a real one,
 * exactly as the Python reference preserves int vs float. */
static srmech_status_t wo_reorient(wr_ctx_t *c, const srmech_json_value_t *args,
                                    wv_t **out)
{
    wv_t *vo, *vv; uint64_t ou = 0u; int8_t ori; srmech_status_t st;
    assert(c != NULL && args != NULL);
    assert(out != NULL);
    vo = wr_arg(c, args, "orientation"); vv = wr_arg(c, args, "value");
    if (vo == NULL || vv == NULL) { return SRMECH_ERR_BAD_INPUT; }
    if (vo->kind == WV_INT) { ori = (int8_t)vo->i; }
    else if (wv_as_u64(vo, &ou)) { ori = (int8_t)ou; }
    else { return SRMECH_ERR_BAD_INPUT; }
    if (vv->kind == WV_INT || vv->kind == WV_UINT) {
        int64_t r = 0, iv = (vv->kind == WV_INT) ? vv->i : (int64_t)vv->u;
        st = srmech_cascade_reorient_i64(ori, iv, &r);
        if (st != SRMECH_OK) { return st; }
        *out = wv_int(c->b, r);
    } else {
        double r = 0.0, dv = 0.0;
        if (!wv_as_dbl(vv, &dv)) { return SRMECH_ERR_BAD_INPUT; }
        st = srmech_cascade_reorient_f64(ori, dv, &r);
        if (st != SRMECH_OK) { return st; }
        *out = wv_dbl(c->b, r);
    }
    return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* scale_round_half_even(value, scale) — int(round(value * scale)). */
static srmech_status_t wo_scale_round(wr_ctx_t *c,
                                       const srmech_json_value_t *args,
                                       wv_t **out)
{
    wv_t *vv, *vs; double v = 0.0; uint64_t sc = 0u; double scaled;
    assert(c != NULL && args != NULL);
    assert(out != NULL);
    vv = wr_arg(c, args, "value"); vs = wr_arg(c, args, "scale");
    if (vv == NULL || vs == NULL) { return SRMECH_ERR_BAD_INPUT; }
    if (!wv_as_dbl(vv, &v) || !wv_as_u64(vs, &sc)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    scaled = v * (double)sc;
    if (!(scaled >= 0.0) || !(scaled < 9223372036854775808.0)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    *out = wv_int(c->b, wo_round_half_even(scaled));
    return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* best_rational(numerator, denominator, max_denominator) -> (p, q). */
static srmech_status_t wo_best_rational(wr_ctx_t *c,
                                         const srmech_json_value_t *args,
                                         wv_t **out)
{
    wv_t *vn, *vd, *vm; uint64_t num = 0u, den = 0u, mx = 0u, p = 0u, q = 0u;
    srmech_status_t st;
    assert(c != NULL && args != NULL);
    assert(out != NULL);
    vn = wr_arg(c, args, "numerator"); vd = wr_arg(c, args, "denominator");
    vm = wr_arg(c, args, "max_denominator");
    if (vn == NULL || vd == NULL || vm == NULL) { return SRMECH_ERR_BAD_INPUT; }
    if (!wv_as_u64(vn, &num) || !wv_as_u64(vd, &den) || !wv_as_u64(vm, &mx)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    st = srmech_best_rational(num, den, mx, &p, &q);
    if (st != SRMECH_OK) { return st; }
    *out = wv_pair(c->b, wv_int(c->b, (int64_t)p), wv_int(c->b, (int64_t)q));
    return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* ------------------------------------------------------------------
 * Class C / L on sequences — chiral_flip + autocorrelation.
 * ------------------------------------------------------------------ */

static wv_t *wo_dbl_list(wa_bump_t *b, const double *src, uint32_t n)
{
    wv_t *v; wv_t **it; uint32_t k;
    assert(b != NULL);
    assert(src != NULL || n == 0u);
    v = wv_new(b, WV_LIST);
    if (v == NULL) { return NULL; }
    v->n = n;
    it = (wv_t **)wa_carve(b, (size_t)n * sizeof(wv_t *) + 8u);
    if (it == NULL) { return NULL; }
    for (k = 0u; k < n; k++) {
        it[k] = wv_dbl(b, src[k]);
        if (it[k] == NULL) { return NULL; }
    }
    v->items = it;
    return v;
}

static srmech_status_t wo_chiral_flip(wr_ctx_t *c,
                                       const srmech_json_value_t *args,
                                       wv_t **out)
{
    wv_t *vs; double *in = NULL, *dst; uint32_t n = 0u; srmech_status_t st;
    assert(c != NULL && args != NULL);
    assert(out != NULL);
    vs = wr_arg(c, args, "seq");
    if (vs == NULL || !wv_as_dbl_arr(c->b, vs, &in, &n)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    dst = (double *)wa_carve(c->b, (size_t)n * sizeof(double) + 8u);
    if (dst == NULL) { return SRMECH_ERR_OVERFLOW; }
    st = srmech_cascade_chiral_flip_f64(in, (size_t)n, dst);
    if (st != SRMECH_OK) { return st; }
    *out = wo_dbl_list(c->b, dst, n);
    return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

static srmech_status_t wo_autocorr(wr_ctx_t *c, const srmech_json_value_t *args,
                                    wv_t **out)
{
    wv_t *vx; double *in = NULL, *dst; uint32_t n = 0u; srmech_status_t st;
    assert(c != NULL && args != NULL);
    assert(out != NULL);
    vx = wr_arg(c, args, "x");
    if (vx == NULL || !wv_as_dbl_arr(c->b, vx, &in, &n)) {
        return SRMECH_ERR_BAD_INPUT;
    }
    dst = (double *)wa_carve(c->b, (size_t)n * sizeof(double) + 8u);
    if (dst == NULL) { return SRMECH_ERR_OVERFLOW; }
    st = srmech_autocorrelation_f64(in, (size_t)n, dst);
    if (st != SRMECH_OK) { return st; }
    *out = wo_dbl_list(c->b, dst, n);
    return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* ------------------------------------------------------------------
 * Class L — schur_complement, composed over srmech_dense_solve_f64_ws.
 * The accumulation order mirrors the Python generator exactly:
 *   S[a][c] = L_dd[a][c] - ( ((0 + t0) + t1) + ... )
 * ------------------------------------------------------------------ */

static srmech_status_t wo_schur_solve(wa_bump_t *b, uint32_t ni, uint32_t nb,
                                       const double *Lii, const double *Lib,
                                       double **out_X)
{
    size_t need; void *ws; double *X;
    assert(b != NULL);
    assert(Lii != NULL && Lib != NULL && out_X != NULL);
    need = srmech_dense_solve_arena_bytes(ni, nb);
    ws = (void *)wa_carve(b, need + 64u);
    X  = (double *)wa_carve(b, (size_t)ni * nb * sizeof(double) + 8u);
    if (ws == NULL || X == NULL) { return SRMECH_ERR_OVERFLOW; }
    *out_X = X;
    return srmech_dense_solve_f64_ws(ni, nb, Lii, Lib, X, ws, need);
}

static srmech_status_t wo_schur(wr_ctx_t *c, const srmech_json_value_t *args,
                                 wv_t **out)
{
    wv_t *vL, *vb; uint32_t n, nb, ni = 0u, r, k, cc;
    uint32_t bidx[64], iidx[64]; const double *L; double *S = NULL, *X = NULL;
    double *Lii, *Lib, *Lbi; srmech_status_t st; wv_t *res;
    assert(c != NULL && args != NULL);
    assert(out != NULL);
    vL = wr_arg(c, args, "L"); vb = wr_arg(c, args, "boundary_idx");
    if (vL == NULL || vb == NULL || vL->kind != WV_MAT ||
        vb->kind != WV_LIST) { return SRMECH_ERR_BAD_INPUT; }
    n = vL->rows; L = vL->m; nb = vb->n;
    if (n == 0u || n != vL->cols || nb == 0u || nb > 64u || n > 64u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    for (k = 0u; k < nb; k++) {
        uint64_t t = 0u;
        if (vb->items[k] == NULL || !wv_as_u64(vb->items[k], &t) ||
            t >= (uint64_t)n) { return SRMECH_ERR_BAD_INPUT; }
        bidx[k] = (uint32_t)t;
    }
    for (k = 0u; k < n; k++) {
        uint32_t j, hit = 0u;
        for (j = 0u; j < nb; j++) { if (bidx[j] == k) { hit = 1u; } }
        if (hit == 0u) { iidx[ni++] = k; }
    }
    S = (double *)wa_carve(c->b, (size_t)nb * nb * sizeof(double) + 8u);
    if (S == NULL) { return SRMECH_ERR_OVERFLOW; }
    for (r = 0u; r < nb; r++) {
        for (cc = 0u; cc < nb; cc++) { S[r * nb + cc] = L[bidx[r] * n + bidx[cc]]; }
    }
    if (ni > 0u) {
        Lii = (double *)wa_carve(c->b, (size_t)ni * ni * sizeof(double) + 8u);
        Lib = (double *)wa_carve(c->b, (size_t)ni * nb * sizeof(double) + 8u);
        Lbi = (double *)wa_carve(c->b, (size_t)nb * ni * sizeof(double) + 8u);
        if (Lii == NULL || Lib == NULL || Lbi == NULL) {
            return SRMECH_ERR_OVERFLOW;
        }
        for (r = 0u; r < ni; r++) {
            for (cc = 0u; cc < ni; cc++) { Lii[r * ni + cc] = L[iidx[r] * n + iidx[cc]]; }
            for (cc = 0u; cc < nb; cc++) { Lib[r * nb + cc] = L[iidx[r] * n + bidx[cc]]; }
        }
        for (r = 0u; r < nb; r++) {
            for (cc = 0u; cc < ni; cc++) { Lbi[r * ni + cc] = L[bidx[r] * n + iidx[cc]]; }
        }
        st = wo_schur_solve(c->b, ni, nb, Lii, Lib, &X);
        if (st != SRMECH_OK) { return st; }
        for (r = 0u; r < nb; r++) {
            for (cc = 0u; cc < nb; cc++) {
                double acc = 0.0;
                for (k = 0u; k < ni; k++) { acc += Lbi[r * ni + k] * X[k * nb + cc]; }
                S[r * nb + cc] = S[r * nb + cc] - acc;
            }
        }
    }
    res = wv_new(c->b, WV_MAT);
    if (res == NULL) { return SRMECH_ERR_OVERFLOW; }
    res->m = S; res->rows = nb; res->cols = nb;
    *out = res;
    return SRMECH_OK;
}

/* ------------------------------------------------------------------
 * Classes A / B / F / M — the framing + content-addressing leaves.
 * ------------------------------------------------------------------ */

static wv_t *wv_bytes(wa_bump_t *b, const unsigned char *src, uint32_t n)
{
    wv_t *v; unsigned char *p;
    assert(b != NULL);
    assert(src != NULL || n == 0u);
    v = wv_new(b, WV_BYTES);
    if (v == NULL) { return NULL; }
    p = wa_carve(b, (size_t)n + 8u);
    if (p == NULL) { return NULL; }
    if (n > 0u) { memcpy(p, src, n); }
    v->by = p; v->bylen = n;
    return v;
}

/* The str/bytes boundary: a WV_STR already holds decoded UTF-8 bytes, so
 * utf8_encode is a re-tag, and byte_slice / int_parse_le / str_concat /
 * pair are pure framing. NONE of the four has a C export. */
static srmech_status_t wo_framing(wr_ctx_t *c, const char *op,
                                   const srmech_json_value_t *args, wv_t **out)
{
    wv_t *v1, *v2;
    assert(c != NULL && op != NULL);
    assert(args != NULL && out != NULL);
    v1 = NULL; v2 = NULL;
    if (strcmp(op, "srmech.cascade.leaves.pair") == 0) {
        v1 = wr_arg(c, args, "first"); v2 = wr_arg(c, args, "second");
        if (v1 == NULL || v2 == NULL) { return SRMECH_ERR_BAD_INPUT; }
        *out = wv_pair(c->b, v1, v2);
    } else if (strcmp(op, "srmech.cascade.leaves.str_concat") == 0) {
        char *p; uint32_t tot;
        v1 = wr_arg(c, args, "prefix"); v2 = wr_arg(c, args, "text");
        if (v1 == NULL || v2 == NULL || v1->kind != WV_STR ||
            v2->kind != WV_STR) { return SRMECH_ERR_BAD_INPUT; }
        tot = v1->slen + v2->slen;
        p = (char *)wa_carve(c->b, (size_t)tot + 8u);
        if (p == NULL) { return SRMECH_ERR_OVERFLOW; }
        memcpy(p, v1->s, v1->slen); memcpy(p + v1->slen, v2->s, v2->slen);
        *out = wv_new(c->b, WV_STR);
        if (*out != NULL) { (*out)->s = p; (*out)->slen = tot; }
    } else if (strcmp(op, "srmech.cascade.leaves.utf8_encode") == 0) {
        v1 = wr_arg(c, args, "text");
        if (v1 == NULL || v1->kind != WV_STR) { return SRMECH_ERR_BAD_INPUT; }
        *out = wv_bytes(c->b, (const unsigned char *)v1->s, v1->slen);
    } else {
        return SRMECH_ERR_NOT_IMPL;
    }
    return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

static srmech_status_t wo_framing2(wr_ctx_t *c, const char *op,
                                    const srmech_json_value_t *args,
                                    wv_t **out)
{
    wv_t *vd, *v2, *v3;
    assert(c != NULL && op != NULL);
    assert(args != NULL && out != NULL);
    if (strcmp(op, "srmech.cascade.leaves.byte_slice") == 0) {
        uint64_t s = 0u, e = 0u;
        vd = wr_arg(c, args, "data"); v2 = wr_arg(c, args, "start");
        v3 = wr_arg(c, args, "stop");
        if (vd == NULL || v2 == NULL || v3 == NULL || vd->kind != WV_BYTES ||
            !wv_as_u64(v2, &s) || !wv_as_u64(v3, &e)) {
            return SRMECH_ERR_BAD_INPUT;
        }
        if (e > (uint64_t)vd->bylen || s > e) { return SRMECH_ERR_BAD_INPUT; }
        *out = wv_bytes(c->b, vd->by + s, (uint32_t)(e - s));
    } else if (strcmp(op, "srmech.cascade.leaves.int_parse_le") == 0) {
        uint64_t acc = 0u; uint32_t k;
        vd = wr_arg(c, args, "data");
        if (vd == NULL || vd->kind != WV_BYTES || vd->bylen > 8u) {
            return SRMECH_ERR_BAD_INPUT;
        }
        k = vd->bylen;
        while (k > 0u) { k--; acc = (acc << 8) | (uint64_t)vd->by[k]; }
        *out = wv_uint(c->b, acc);
    } else {
        return SRMECH_ERR_NOT_IMPL;
    }
    return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

static srmech_status_t wo_hash_hdc(wr_ctx_t *c, const char *op,
                                    const srmech_json_value_t *args,
                                    wv_t **out)
{
    wv_t *v1, *v2; unsigned char *buf; srmech_status_t st;
    assert(c != NULL && op != NULL);
    assert(args != NULL && out != NULL);
    if (strcmp(op, "sha256_raw") == 0) {
        v1 = wr_arg(c, args, "data");
        if (v1 == NULL || v1->kind != WV_BYTES) { return SRMECH_ERR_BAD_INPUT; }
        buf = wa_carve(c->b, 40u);
        if (buf == NULL) { return SRMECH_ERR_OVERFLOW; }
        st = srmech_sha256_shani(v1->by, (size_t)v1->bylen, buf);
        if (st != SRMECH_OK) { return st; }
        *out = wv_bytes(c->b, buf, 32u);
    } else if (strcmp(op,
        "srmech.signal_processing.rbs_hdc_instrument.mint_vector") == 0) {
        uint64_t D = 0u; uint32_t nby;
        v1 = wr_arg(c, args, "name"); v2 = wr_arg(c, args, "D");
        if (v1 == NULL || v2 == NULL || v1->kind != WV_STR ||
            !wv_as_u64(v2, &D) || D == 0u || (D % 8u) != 0u) {
            return SRMECH_ERR_BAD_INPUT;
        }
        nby = (uint32_t)(D / 8u);
        buf = wa_carve(c->b, (size_t)nby + 8u);
        if (buf == NULL) { return SRMECH_ERR_OVERFLOW; }
        st = srmech_mint_vector((const uint8_t *)v1->s, (size_t)v1->slen,
                                nby, buf);
        if (st != SRMECH_OK) { return st; }
        *out = wv_bytes(c->b, buf, nby);
    } else {
        return SRMECH_ERR_NOT_IMPL;
    }
    return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

static srmech_status_t wo_hdc(wr_ctx_t *c, const char *op,
                               const srmech_json_value_t *args, wv_t **out)
{
    wv_t *v1, *v2; unsigned char *buf; srmech_status_t st;
    assert(c != NULL && op != NULL);
    assert(args != NULL && out != NULL);
    if (strcmp(op, "srmech.math.hdc.permute") == 0) {
        uint64_t rot = 0u;
        v1 = wr_arg(c, args, "a"); v2 = wr_arg(c, args, "rotate_bits");
        if (v1 == NULL || v2 == NULL || v1->kind != WV_BYTES ||
            !wv_as_u64(v2, &rot) || rot > 2147483647u) {
            return SRMECH_ERR_BAD_INPUT;
        }
        buf = wa_carve(c->b, (size_t)v1->bylen + 8u);
        if (buf == NULL) { return SRMECH_ERR_OVERFLOW; }
        st = srmech_hdc_permute(v1->by, v1->bylen, (int32_t)rot, buf);
        if (st != SRMECH_OK) { return st; }
        *out = wv_bytes(c->b, buf, v1->bylen);
    } else if (strcmp(op, "srmech.math.hdc.bind") == 0) {
        v1 = wr_arg(c, args, "a"); v2 = wr_arg(c, args, "b");
        if (v1 == NULL || v2 == NULL || v1->kind != WV_BYTES ||
            v2->kind != WV_BYTES || v1->bylen != v2->bylen) {
            return SRMECH_ERR_BAD_INPUT;
        }
        buf = wa_carve(c->b, (size_t)v1->bylen + 8u);
        if (buf == NULL) { return SRMECH_ERR_OVERFLOW; }
        st = srmech_hdc_bind(v1->by, v2->by, v1->bylen, buf);
        if (st != SRMECH_OK) { return st; }
        *out = wv_bytes(c->b, buf, v1->bylen);
    } else {
        return SRMECH_ERR_NOT_IMPL;
    }
    return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* ------------------------------------------------------------------
 * THE EXTENDED DISPATCH TABLE — 23 ops. This is the whole experiment:
 * the shipped cr_dispatch has 10 entries and rejects all 23.
 * ------------------------------------------------------------------ */

static srmech_status_t wo_dispatch(wr_ctx_t *c, const char *op, uint32_t ol,
                                    const srmech_json_value_t *args,
                                    wv_t **out)
{
    char name[128];
    srmech_status_t st;
    assert(c != NULL && op != NULL);
    assert(args != NULL && out != NULL);
    if (ol + 1u > sizeof(name)) { return SRMECH_ERR_BAD_INPUT; }
    memcpy(name, op, ol); name[ol] = '\0';
    if (strcmp(name, "gcd") == 0 || strcmp(name, "mod_add") == 0 ||
        strcmp(name, "mod_mul") == 0 || strcmp(name, "mod_pow") == 0 ||
        strcmp(name, "mod_inv") == 0) {
        return wo_class_i(c, name, ol, args, out);
    }
    if (strcmp(name, "mod_mul_wide") == 0) {
        return wo_mod_mul_wide(c, args, out);
    }
    if (strcmp(name, "srmech.cascade.atoms.pin_slot_at_zero") == 0) {
        return wo_pin_slot(c, args, out);
    }
    if (strcmp(name, "srmech.cascade.leaves.dead_band") == 0) {
        return wo_dead_band(c, args, out);
    }
    if (strcmp(name, "srmech.cascade.atoms.reorient") == 0) {
        return wo_reorient(c, args, out);
    }
    if (strcmp(name, "scale_round_half_even") == 0) {
        return wo_scale_round(c, args, out);
    }
    if (strcmp(name, "best_rational") == 0) {
        return wo_best_rational(c, args, out);
    }
    if (strcmp(name, "srmech.cascade.atoms.chiral_flip") == 0) {
        return wo_chiral_flip(c, args, out);
    }
    if (strcmp(name, "srmech.cascade.composites.autocorrelation") == 0) {
        return wo_autocorr(c, args, out);
    }
    if (strcmp(name, "schur_complement") == 0) {
        return wo_schur(c, args, out);
    }
    st = wo_framing(c, name, args, out);
    if (st != SRMECH_ERR_NOT_IMPL) { return st; }
    st = wo_framing2(c, name, args, out);
    if (st != SRMECH_ERR_NOT_IMPL) { return st; }
    st = wo_hash_hdc(c, name, args, out);
    if (st != SRMECH_ERR_NOT_IMPL) { return st; }
    return wo_hdc(c, name, args, out);
}

/* ------------------------------------------------------------------
 * The local run loop — the same shape as cr_run_steps, extended table.
 * ------------------------------------------------------------------ */

typedef struct {
    srmech_status_t st;
    uint32_t        failed_step;
    const char     *failed_op;
    int             used_output_index;
    uint32_t        kind_mask;      /* bit k set iff carrier kind k appeared */
    wv_t           *value;
} wr_result_t;

/* The names the kind_mask bits stand for — the shipped cr_value_t has
 * only NONE / INT / STR / RATIONAL / LIST, so DBL / UINT / BYTES / MAT
 * mark a CARRIER-WIDTH gap distinct from the op-table gap. */
static const char *WR_KIND_NAME[] = {
    "none", "int", "uint", "dbl", "str", "bytes", "list", "mat"
};

static void wr_kinds_str(uint32_t mask, char *buf, size_t cap)
{
    size_t pos = 0u; uint32_t k;
    assert(buf != NULL);
    assert(cap > 8u);
    buf[0] = '\0';
    for (k = 0u; k < 8u; k++) {
        if ((mask & (1u << k)) != 0u) {
            pos += (size_t)snprintf(buf + pos, cap - pos, "%s%s",
                                    (pos > 0u) ? "+" : "", WR_KIND_NAME[k]);
        }
    }
    if (pos == 0u) { snprintf(buf, cap, "-"); }
}

static void wr_run(const srmech_json_value_t *chain,
                   const srmech_json_value_t *ctx, wa_bump_t *b,
                   wr_result_t *res)
{
    const srmech_json_value_t *steps; wr_ctx_t c; uint32_t i, ns;
    assert(chain != NULL && b != NULL);
    assert(res != NULL);
    res->st = SRMECH_ERR_BAD_INPUT; res->failed_step = 0u;
    res->failed_op = ""; res->value = NULL; res->used_output_index = 0;
    res->kind_mask = 0u;
    steps = srmech_json_object_get(chain, "steps");
    if (steps == NULL || steps->type != SRMECH_JSON_ARRAY ||
        steps->u.arr.n == 0u) { return; }
    ns = steps->u.arr.n;
    c.inputs = (ctx != NULL) ? srmech_json_object_get(ctx, "inputs") : NULL;
    c.b = b; c.cur = 0u; c.used_output_index = 0;
    c.step_out = (wv_t **)wa_carve(b, (size_t)ns * sizeof(wv_t *) + 8u);
    if (c.step_out == NULL) { res->st = SRMECH_ERR_OVERFLOW; return; }
    for (i = 0u; i < ns; i++) {
        const srmech_json_value_t *step = steps->u.arr.items[i];
        const srmech_json_value_t *args, *o; wv_t *out = NULL;
        if (step == NULL || step->type != SRMECH_JSON_OBJECT) {
            res->failed_step = i; return;
        }
        o = srmech_json_object_get(step, "op");
        args = srmech_json_object_get(step, "args");
        if (o == NULL || o->type != SRMECH_JSON_STRING || args == NULL ||
            args->type != SRMECH_JSON_OBJECT) { res->failed_step = i; return; }
        c.cur = i;
        res->st = wo_dispatch(&c, o->u.str.ptr, o->u.str.len, args, &out);
        res->used_output_index = c.used_output_index;
        if (res->st != SRMECH_OK) {
            res->failed_step = i; res->failed_op = o->u.str.ptr; return;
        }
        res->kind_mask |= (uint32_t)1u << (uint32_t)out->kind;
        if (out->kind == WV_LIST) {
            uint32_t e;
            for (e = 0u; e < out->n; e++) {
                if (out->items[e] != NULL) {
                    res->kind_mask |= (uint32_t)1u <<
                                      (uint32_t)out->items[e]->kind;
                }
            }
        }
        c.step_out[i] = out;
    }
    res->used_output_index = c.used_output_index;
    res->value = c.step_out[ns - 1u];
    res->st = SRMECH_OK;
}

/* ------------------------------------------------------------------
 * Canonical spelling — byte-for-byte the Python `_spell` output.
 * ------------------------------------------------------------------ */

static void wr_spell_scalar(const wv_t *v, char *buf, size_t cap)
{
    assert(v != NULL);
    assert(buf != NULL && cap > 24u);
    if (v->kind == WV_NONE) { snprintf(buf, cap, "none"); }
    else if (v->kind == WV_INT) { snprintf(buf, cap, "%lld", (long long)v->i); }
    else if (v->kind == WV_UINT) {
        snprintf(buf, cap, "%llu", (unsigned long long)v->u);
    } else if (v->kind == WV_DBL) { snprintf(buf, cap, "%.17g", v->d); }
    else { snprintf(buf, cap, "?"); }
}

/* Emit into a caller buffer without recursion: WV_MAT is the only nested
 * shape and it is exactly two levels, WV_LIST is exactly one. */
static void wr_spell(const wv_t *v, char *buf, size_t cap)
{
    size_t pos = 0u; uint32_t k, r; char tmp[64];
    assert(buf != NULL && cap > 8u);
    assert(v != NULL);
    buf[0] = '\0';
    if (v->kind == WV_STR) { snprintf(buf, cap, "s:%.*s", (int)v->slen, v->s); return; }
    if (v->kind == WV_BYTES) {
        for (k = 0u; k < v->bylen && pos + 3u < cap; k++) {
            snprintf(buf + pos, cap - pos, "%02x", v->by[k]); pos += 2u;
        }
        return;
    }
    if (v->kind == WV_MAT) {
        pos += (size_t)snprintf(buf + pos, cap - pos, "[");
        for (r = 0u; r < v->rows; r++) {
            pos += (size_t)snprintf(buf + pos, cap - pos, "%s[",
                                    (r > 0u) ? "," : "");
            for (k = 0u; k < v->cols; k++) {
                pos += (size_t)snprintf(buf + pos, cap - pos, "%s%.17g",
                                        (k > 0u) ? "," : "", v->m[r * v->cols + k]);
            }
            pos += (size_t)snprintf(buf + pos, cap - pos, "]");
        }
        snprintf(buf + pos, cap - pos, "]");
        return;
    }
    if (v->kind == WV_LIST) {
        pos += (size_t)snprintf(buf + pos, cap - pos, "[");
        for (k = 0u; k < v->n; k++) {
            wr_spell_scalar(v->items[k], tmp, sizeof(tmp));
            pos += (size_t)snprintf(buf + pos, cap - pos, "%s%s",
                                    (k > 0u) ? "," : "", tmp);
        }
        snprintf(buf + pos, cap - pos, "]");
        return;
    }
    wr_spell_scalar(v, buf, cap);
}

/* ------------------------------------------------------------------
 * File + JSON loading.
 * ------------------------------------------------------------------ */

static long wr_read_file(const char *path, char *dst, size_t cap)
{
    FILE *f; size_t got;
    assert(path != NULL);
    assert(dst != NULL && cap > 1u);
    f = fopen(path, "rb");
    if (f == NULL) { return -1; }
    got = fread(dst, 1u, cap - 1u, f);
    fclose(f);
    dst[got] = '\0';
    return (long)got;
}

/* ------------------------------------------------------------------
 * The eleven wedge chains and their declared case counts (from the
 * shipped descriptors, via _1653_wedge_pycheck_rc444.py).
 * ------------------------------------------------------------------ */

typedef struct { const char *base; uint32_t n_cases; } wr_entry_t;

static const wr_entry_t WR_WEDGE[] = {
    { "best_rational_signed__0", 10u },
    { "chiral_dual__0",           4u },
    { "cyclic_gcd__0",            7u },
    { "cyclic_mod_add__0",        4u },
    { "cyclic_mod_inv__0",        3u },
    { "cyclic_mod_mul__0",        3u },
    { "cyclic_mod_mul_wide__0",   2u },
    { "cyclic_mod_pow__0",        4u },
    { "encode_loe_content__0",    4u },
    { "magnitude__0",             8u },
    { "schur_complement__0",      3u }
};
#define WR_N_WEDGE  (sizeof(WR_WEDGE) / sizeof(WR_WEDGE[0]))

typedef struct {
    uint32_t cases_total;
    uint32_t cases_ingested;      /* ctx JSON parsed OK                  */
    uint32_t cases_ran;           /* extended-table run returned OK      */
    uint32_t chains_all_ran;      /* every ingestable case ran           */
    uint32_t chains_any_ran;
    uint32_t chains_needing_output_index;
    uint32_t chains_needing_wide_carrier;
} wr_tally_t;

/* The carrier kinds the SHIPPED cr_value_t genuinely cannot hold: DBL,
 * BYTES, MAT. It holds NONE / INT / STR / RATIONAL / LIST.
 *
 * WV_UINT is DELIBERATELY EXCLUDED and that exclusion is a measurement,
 * not a courtesy: the shipped CR_INT is a srmech_bigint, so it holds any
 * uint64 the modular ops return. WV_UINT exists only because THIS
 * harness chose a fixed-width slot; counting it would have inflated the
 * carrier-gap verdict from 5 chains to 11. */
#define WR_WIDE_KINDS  (((uint32_t)1u << WV_DBL) \
                        | ((uint32_t)1u << WV_BYTES) \
                        | ((uint32_t)1u << WV_MAT))

typedef struct { int ok; int any; int idx_ref; uint32_t kinds; } wr_cstate_t;

static void wr_run_one_case(const char *dir, const wr_entry_t *ent,
                            const srmech_json_value_t *chain, uint32_t ci,
                            wr_tally_t *t, wr_cstate_t *cs)
{
    char path[512]; static char sp[65536]; wa_bump_t rb; wr_result_t res;
    srmech_json_value_t *ctx = NULL; srmech_status_t pst; long got;
    static unsigned char ctx_arena[1u << 20];
    assert(dir != NULL && ent != NULL);
    assert(t != NULL && cs != NULL);
    t->cases_total++;
    snprintf(path, sizeof(path), "%s/%s.case%u.ctx.json", dir, ent->base, ci);
    got = wr_read_file(path, wa_file_buf2, sizeof(wa_file_buf2));
    if (got < 0) {
        printf("    case%-2u  READ_FAIL %s\n", ci, path); cs->ok = 0; return;
    }
    pst = srmech_json_parse(wa_file_buf2, (size_t)got, ctx_arena,
                            sizeof(ctx_arena), &ctx);
    if (pst != SRMECH_OK) {
        printf("    case%-2u  INGEST_REJECT srmech_json_parse rc=%d\n",
               ci, (int)pst);
        cs->ok = 0;
        return;
    }
    t->cases_ingested++;
    rb.cur = wa_run_arena; rb.end = wa_run_arena + WA_RUN_BYTES;
    wr_run(chain, ctx, &rb, &res);
    if (res.used_output_index) { cs->idx_ref = 1; }
    cs->kinds |= res.kind_mask;
    if (res.st != SRMECH_OK) {
        printf("    case%-2u  RUN_FAIL rc=%d at step %u op=%s\n", ci,
               (int)res.st, res.failed_step,
               (res.failed_op != NULL) ? res.failed_op : "?");
        cs->ok = 0;
        return;
    }
    t->cases_ran++; cs->any = 1;
    wr_spell(res.value, sp, sizeof(sp));
    printf("    case%-2u  C_VALUE %s\n", ci, sp);
}

static void wr_run_chain(const char *dir, const wr_entry_t *ent,
                         wr_tally_t *t)
{
    char path[512]; char kn[96]; wa_bump_t jb;
    srmech_json_value_t *chain = NULL;
    srmech_status_t pst; long got; uint32_t ci; wr_cstate_t cs;
    assert(dir != NULL && ent != NULL);
    assert(t != NULL);
    cs.ok = 1; cs.any = 0; cs.idx_ref = 0; cs.kinds = 0u;
    printf("  == %s (%u cases)\n", ent->base, ent->n_cases);
    snprintf(path, sizeof(path), "%s/%s.chain.json", dir, ent->base);
    got = wr_read_file(path, wa_file_buf, sizeof(wa_file_buf));
    if (got < 0) { printf("    CHAIN_READ_FAIL %s\n", path); return; }
    jb.cur = wa_json_arena; jb.end = wa_json_arena + WA_JSON_BYTES;
    pst = srmech_json_parse(wa_file_buf, (size_t)got, jb.cur,
                            (size_t)(jb.end - jb.cur), &chain);
    if (pst != SRMECH_OK) {
        printf("    CHAIN_PARSE_REJECT rc=%d\n", (int)pst);
        return;
    }
    for (ci = 0u; ci < ent->n_cases; ci++) {
        wr_run_one_case(dir, ent, chain, ci, t, &cs);
    }
    if (cs.ok && cs.any) { t->chains_all_ran++; }
    if (cs.any) { t->chains_any_ran++; }
    if (cs.idx_ref) { t->chains_needing_output_index++; }
    if ((cs.kinds & WR_WIDE_KINDS) != 0u) { t->chains_needing_wide_carrier++; }
    wr_kinds_str(cs.kinds, kn, sizeof(kn));
    printf("    -> chain verdict: all_cases_ran=%d any_case_ran=%d "
           "needs_output_index_ref=%d carrier_kinds=%s wide_carrier=%d\n",
           cs.ok && cs.any, cs.any, cs.idx_ref, kn,
           ((cs.kinds & WR_WIDE_KINDS) != 0u) ? 1 : 0);
}

/* ------------------------------------------------------------------
 * The SHIPPED-SURFACE ABLATION. Two chains built ONLY from ops already
 * in the shipped 10-entry table; they differ solely in whether step 1
 * reads `@step[0].output` or `@step[0].output[0]`. Whatever the second
 * one returns is a property of the shipped ref grammar, not of the op
 * table — which is the point.
 * ------------------------------------------------------------------ */

static const char *WR_ABL_PLAIN =
    "{\"name\":\"abl_plain\",\"on_error\":\"raise\",\"steps\":["
    "{\"class\":\"N\",\"op\":\"rational_add\",\"args\":{\"a\":[1,2],"
    "\"b\":[1,3]}},"
    "{\"class\":\"N\",\"op\":\"rational_mul\",\"args\":"
    "{\"a\":\"@step[0].output\",\"b\":[2,1]}}]}";

static const char *WR_ABL_INDEX =
    "{\"name\":\"abl_index\",\"on_error\":\"raise\",\"steps\":["
    "{\"class\":\"N\",\"op\":\"rational_add\",\"args\":{\"a\":[1,2],"
    "\"b\":[1,3]}},"
    "{\"class\":\"N\",\"op\":\"rational_mul\",\"args\":"
    "{\"a\":\"@step[0].output[0]\",\"b\":[2,1]}}]}";

/* Ablation 2 — the REAL-NUMBER LITERAL. Same op, same arg SHAPE, the only
 * change is that one element of the accepted 2-list is spelled 1.0 instead
 * of 1. The shipped cr_json_scalar returns NULL for a JSON DOUBLE, so a
 * chain carrying a real literal cannot run even with its op in the table —
 * and `band = 1e-12` is a literal in one of the eleven descriptors. */
static const char *WR_ABL_INTLIT =
    "{\"name\":\"abl_intlit\",\"on_error\":\"raise\",\"steps\":["
    "{\"class\":\"N\",\"op\":\"rational_add\",\"args\":{\"a\":[1,2],"
    "\"b\":[1,3]}}]}";

static const char *WR_ABL_DBLLIT =
    "{\"name\":\"abl_dbllit\",\"on_error\":\"raise\",\"steps\":["
    "{\"class\":\"N\",\"op\":\"rational_add\",\"args\":{\"a\":[1,2],"
    "\"b\":[1.0,3]}}]}";

static void wr_ablate_one(const char *label, const char *chain_json)
{
    static char out[8192];
    size_t out_len = 0u, need;
    static unsigned char ws[1u << 22];
    srmech_status_t st;
    assert(label != NULL);
    assert(chain_json != NULL);
    need = srmech_chain_run_arena_bytes(strlen(chain_json), 32u);
    if (need > sizeof(ws)) { printf("  %-10s ARENA_TOO_SMALL\n", label); return; }
    st = srmech_chain_run(chain_json, strlen(chain_json),
                          "{\"row\":null,\"inputs\":{}}",
                          strlen("{\"row\":null,\"inputs\":{}}"),
                          ws, need, out, sizeof(out), &out_len);
    printf("  %-10s srmech_chain_run rc=%d out=%.*s\n", label, (int)st,
           (st == SRMECH_OK) ? (int)out_len : 0, out);
}

int main(int argc, char **argv)
{
    const char *dir; wr_tally_t t; size_t k;
    assert(argc >= 0);
    assert(argv != NULL);
    dir = (argc > 1) ? argv[1] : ".";
    memset(&t, 0, sizeof(t));
    printf("srmech %s  ABI %d\n", srmech_version(), srmech_abi_version());
    printf("=== A. SHIPPED-SURFACE ABLATIONS: are there blockers BESIDES the "
           "op table?\n");
    printf("    (every chain below uses ONLY ops already in the shipped "
           "10-entry table)\n");
    printf("    A1 ref grammar: bare `.output` vs `.output[K]`\n");
    wr_ablate_one("bare",  WR_ABL_PLAIN);
    wr_ablate_one("indexed", WR_ABL_INDEX);
    printf("    A2 arg carrier: an integer 2-list vs the same list with one "
           "real element\n");
    wr_ablate_one("intlit", WR_ABL_INTLIT);
    wr_ablate_one("dbllit", WR_ABL_DBLLIT);
    printf("=== B. EXTENDED-TABLE RUN of the 11 wedge chains (%u chains)\n",
           (unsigned)WR_N_WEDGE);
    for (k = 0u; k < WR_N_WEDGE; k++) {
        wr_run_chain(dir, &WR_WEDGE[k], &t);
    }
    printf("=== C. TALLY\n");
    printf("    chains                    : %u\n", (unsigned)WR_N_WEDGE);
    printf("    chains with EVERY case run : %u\n", t.chains_all_ran);
    printf("    chains with ANY case run   : %u\n", t.chains_any_ran);
    printf("    chains needing @step[N].output[K] : %u\n",
           t.chains_needing_output_index);
    printf("    chains needing a WIDER value carrier : %u\n",
           t.chains_needing_wide_carrier);
    printf("    cases total / ingested / ran : %u / %u / %u\n",
           t.cases_total, t.cases_ingested, t.cases_ran);
    return 0;
}
