/* _1653_proto_fold.c — gh #1653 PROTOTYPE: the SURFACE-A (`[[cascade.chain]]`)
 * FOLD step form in C, standalone, JPL Power-of-Ten clean.
 *
 * WHAT THIS IS. At 0.9.0rc444 the C peers of `srmech.cascade.compose`
 * (srmech_compose.c parse / srmech_compose_run.c run) implement exactly ONE of
 * the engine's THREE step forms — the plain `class`+`op`+`args` form. The map
 * and fold forms are UNRECOGNISED: `co_build_step` (srmech_compose.c:299-303)
 * hard-requires class+op+args, and `cr_run_steps` (srmech_compose_run.c:722-724)
 * hard-requires a STRING "op", so a step carrying neither is BAD_INPUT before
 * anything looks at it. MEASURED at rc444 (parse rc=2, run rc=2, with three
 * passing positive controls):
 *   docs/srmech/notes/_1653_path_measure_rc444.ndjson
 *
 * FOLD is the SMALLEST of the two missing forms, and this file is the shape the
 * rcN arm should take inside srmech_compose_run.c:
 *   - a fold has NO body step list, so it needs NO re-entry into the step
 *     runner: ZERO new recursion. (The map form does need a body step list, and
 *     tests/test_jpl_audit.py::test_rule_1_no_new_recursion is STRICT on novel
 *     cycles — see the note at the end of this comment.)
 *   - it reuses the existing reference resolver + value carrier unchanged for
 *     the int case, so the whole added surface is one discriminator + one arm +
 *     one bounded body table.
 *
 * SCOPE, stated so nothing is over-claimed. This prototype implements the fold
 * arm for the INT carrier — which is exactly `net_chirality`, the ONE shipped
 * top-level fold (the other four folds sit INSIDE map bodies and carry
 * float/list accumulators the surface-A carrier `cr_value_t` cannot hold at
 * all; measured: a float anywhere in an arg makes the C run defer, because
 * cr_json_scalar (srmech_compose_run.c:207-220) returns NULL for
 * SRMECH_JSON_DOUBLE). It carries its OWN miniature value carrier + resolver
 * rather than #including srmech_compose_run.c's file-static ones, because those
 * are `static` and this is a standalone driver, not an edit to c/src/.
 *
 * The ONE body op it dispatches is `orientation_compose` — Class C, the shipped
 * net_chirality fold body (srmech/cascade/leaves.py:227). It has NO C symbol of
 * its own at rc444 (measured), but it is a two-line composition over one that
 * does: `orientation == 0 -> 0` (the ABSORBING zero; Class-K pin-slot) else
 * `srmech_cascade_reorient_i64(orientation, acc)` (Class-C sign
 * re-application). No ALU-magnitude idiom, no new math: a real magnitude is the
 * Class-K pin-slot op srmech_cascade_magnitude_* called BY NAME.
 *
 * BUILD (from docs/srmech/c/; one line, no continuation — a trailing backslash
 * in a comment trips the Rule 8 ratchet, which does NOT strip comments):
 *   cc -std=c99 -Wall -Wextra -Wpedantic -O2 -Iinclude ../notes/_1653_proto_fold.c build/libsrmech.a -o /tmp/proto_fold
 * then run /tmp/proto_fold  (exit 0 == all 12 checks pass)
 *
 * JPL Power-of-Ten: caller-arena only (no malloc — one file-scope arena carved
 * bump-forward), NO recursion, NO goto, every function <= 60 lines with >= 2
 * asserts, every loop explicitly bounded (PF_MAX_SEQ) and asserted, no
 * ALU-magnitude idiom (Class-K pin-slot ops are called by name),
 * no libm, every srmech_* return checked.
 *
 * NOT A SHIP. Nothing here edits c/src/ or c/include/. The rcN owner lifts the
 * three named pieces (pf_step_form / pf_fold_body / pf_run_fold) into
 * srmech_compose_run.c + srmech_compose.c.
 */

#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "srmech.h"

/* ------------------------------------------------------------------
 * Bounds (JPL Rule 2 — every loop has an explicit compiled cap).
 * ------------------------------------------------------------------ */
#define PF_MAX_SEQ     (1u << 20)   /* folded sequence length cap        */
#define PF_MAX_STEPS   256u         /* steps per chain                   */
#define PF_ARENA_BYTES (1u << 20)   /* the one caller arena              */

/* Step-form classification — the CLOSED-KEY-SET check rc444's C parse does NOT
 * do. srmech_compose.c:299-303 is a REQUIRED-KEYS check, so a step carrying a
 * valid plain skeleton AND map/fold keys parses in C with the v2 half silently
 * DISCARDED (measured at rc444: parse rc=0, run rc=0, value = the plain step's;
 * Python raises ChainSpecError). Today the only thing preventing that is the
 * PYTHON-side guard compose._chain_has_v2_forms (compose.py:419-474). Any rcN
 * that teaches C a new form MUST land this classification in the same commit,
 * or it removes the reason that guard exists while leaving the hole open. */
typedef enum {
    PF_FORM_PLAIN = 0, PF_FORM_MAP, PF_FORM_FOLD, PF_FORM_MIXED, PF_FORM_NONE
} pf_form_t;

/* ------------------------------------------------------------------
 * Bump arena — forward-only carve (the srmech_compose_run.c idiom verbatim).
 * ------------------------------------------------------------------ */

typedef struct { unsigned char *cur; unsigned char *end; } pf_bump_t;

static unsigned char *pf_align(unsigned char *p)
{
    uintptr_t a = (uintptr_t)sizeof(void *);
    uintptr_t pad;
    assert(p != NULL);
    assert(a >= 4u);
    pad = (a - ((uintptr_t)p % a)) % a;
    return p + pad;
}

static unsigned char *pf_carve(pf_bump_t *b, size_t n)
{
    unsigned char *p;
    assert(b != NULL);
    assert(b->cur <= b->end);
    p = pf_align(b->cur);
    if (p > b->end || n > (size_t)(b->end - p)) { return NULL; }
    b->cur = p + n;
    return p;
}

/* ------------------------------------------------------------------
 * The miniature value carrier. INT / LIST only — the fold arm's int case.
 * srmech_compose_run.c's real cr_value_t adds STR / RATIONAL (bignum) and
 * still has NO FLOAT kind; see the SCOPE note in the file header.
 * ------------------------------------------------------------------ */

typedef enum { PF_NONE = 0, PF_INT, PF_LIST } pf_kind_t;

typedef struct pf_value {
    pf_kind_t kind;
    int64_t   i;
    struct pf_value **items;
    uint32_t  n;
} pf_value_t;

static pf_value_t *pf_new(pf_bump_t *b, pf_kind_t kind)
{
    pf_value_t *v;
    assert(b != NULL);
    assert(kind >= PF_NONE && kind <= PF_LIST);
    v = (pf_value_t *)pf_carve(b, sizeof(pf_value_t));
    if (v == NULL) { return NULL; }
    v->kind = kind; v->i = 0; v->items = NULL; v->n = 0u;
    return v;
}

static pf_value_t *pf_int(pf_bump_t *b, int64_t i)
{
    pf_value_t *v = pf_new(b, PF_INT);
    assert(b != NULL);
    assert(sizeof(i) == 8u);
    if (v == NULL) { return NULL; }
    v->i = i;
    return v;
}

/* ------------------------------------------------------------------
 * THE PIECE 1 — the step-form discriminator (closed key set).
 * ------------------------------------------------------------------ */

/* 1 iff `step` carries ANY of the `n` keys in `keys`. */
static int pf_has_any(const srmech_json_value_t *step, const char *const *keys,
                      uint32_t n)
{
    uint32_t i;
    assert(step != NULL && keys != NULL);
    assert(n > 0u && n <= 8u);
    for (i = 0u; i < n; i++) {
        if (srmech_json_object_get(step, keys[i]) != NULL) { return 1; }
    }
    return 0;
}

/* Classify one step. MIXED is a HARD reject (compose.py:611-623's
 * mutual-exclusion rule); NONE is a step with no discriminator at all. The
 * key lists mirror compose.py:162-163 _MAP_KEYS / _FOLD_KEYS + the plain
 * triple, and a widening on either side must move both. */
static pf_form_t pf_step_form(const srmech_json_value_t *step)
{
    static const char *const map_k[4] = {"map_over", "index", "bind", "body"};
    static const char *const fold_k[5] = {"fold_class", "fold_op", "fold_init",
                                          "over", "fold_args"};
    static const char *const plain_k[3] = {"class", "op", "args"};
    int m, f, p;
    assert(step != NULL);
    assert(step->type == SRMECH_JSON_OBJECT);
    m = pf_has_any(step, map_k, 4u);
    f = pf_has_any(step, fold_k, 5u);
    p = pf_has_any(step, plain_k, 3u);
    if ((m + f + p) > 1) { return PF_FORM_MIXED; }
    if (m) { return PF_FORM_MAP; }
    if (f) { return PF_FORM_FOLD; }
    if (p) { return PF_FORM_PLAIN; }
    return PF_FORM_NONE;
}

/* ------------------------------------------------------------------
 * Reference resolution for the fold's `over` / `fold_init`. Only the three
 * namespaces srmech_compose_run.c's cr_resolve_ref already knows
 * (row. / input. / step[N].output) — @idx / @bind / @op / @catalog stay
 * unrecognised here exactly as they are there (measured at rc444: run rc=2).
 * ------------------------------------------------------------------ */

typedef struct {
    const srmech_json_value_t *row;
    const srmech_json_value_t *inputs;
    const srmech_json_value_t **step_out;   /* raw JSON step outputs (unused
                                             * by the int fold; kept so the
                                             * shape matches the real ctx) */
    uint32_t cur;
} pf_ctx_t;

/* Resolve a `@row.<k>` / `@input.<k>` reference to its raw JSON node. One
 * dotted segment only — enough for the shipped folds (`@input.orientations`)
 * and honest about it: a deeper path returns NULL and the caller defers. */
static const srmech_json_value_t *pf_resolve_ref(const pf_ctx_t *c,
                                                 const char *ref, uint32_t len)
{
    char key[64];
    const char *p; uint32_t kl = 0u;
    const srmech_json_value_t *base = NULL;
    assert(c != NULL && ref != NULL);
    assert(len < 0x7fffffffu);
    if (len < 2u || ref[0] != '@') { return NULL; }
    p = ref + 1;
    if (len >= 5u && memcmp(p, "row.", 4u) == 0) { base = c->row; p += 4; }
    else if (len >= 7u && memcmp(p, "input.", 6u) == 0) {
        base = c->inputs; p += 6;
    } else { return NULL; }              /* step[N]/idx/bind/op -> defer */
    if (base == NULL || base->type != SRMECH_JSON_OBJECT) { return NULL; }
    while (p < ref + len && *p != '.' && *p != '[') {
        if (kl + 1u >= sizeof(key)) { return NULL; }
        key[kl++] = *p++;
    }
    if (p != ref + len || kl == 0u) { return NULL; }   /* one segment only */
    key[kl] = '\0';
    return srmech_json_object_get(base, key);
}

/* ------------------------------------------------------------------
 * THE PIECE 2 — the bounded fold BODY table.
 *
 * `orientation_compose(acc, orientation)`: 0 when orientation == 0 (the
 * ABSORBING zero — Class-K pin-slot), else reorient(acc, orientation) (the
 * Class-C sign re-application, srmech_cascade_reorient_i64). Matches
 * srmech/cascade/leaves.py:227-244. Sign handling stays Class-K pin-slot +
 * Class-C re-orientation, never the ALU-magnitude idiom.
 * ------------------------------------------------------------------ */

/* 1 iff `op` names orientation_compose — bare, or any dotted spelling ending
 * `.orientation_compose` (the descriptor writes the dotted form; the pattern
 * is srmech_dsl_chain_run.c:738-745 dsl_map_body_is_seq_get). */
static int pf_body_is_orientation_compose(const char *op, uint32_t opl)
{
    static const char dotted[21] = ".orientation_compose";
    assert(op != NULL);
    assert(opl > 0u);
    if (opl == 19u && memcmp(op, "orientation_compose", 19u) == 0) { return 1; }
    if (opl > 20u && memcmp(op + (opl - 20u), dotted, 20u) == 0) { return 1; }
    return 0;
}

/* Dispatch one binary fold step. An op outside the table, or an operand shape
 * outside int64, returns NOT_IMPL and the WHOLE chain defers to pure (the
 * rc103 inform-don't-limit contract, never a wrong answer). */
static srmech_status_t pf_fold_body(pf_bump_t *b, const char *op, uint32_t opl,
                                    const pf_value_t *acc,
                                    const pf_value_t *elem, pf_value_t **out)
{
    int64_t r; int8_t o; srmech_status_t st;
    assert(b != NULL && op != NULL && out != NULL);
    assert(acc != NULL && elem != NULL);
    if (!pf_body_is_orientation_compose(op, opl)) {
        return SRMECH_ERR_NOT_IMPL;
    }
    if (acc->kind != PF_INT || elem->kind != PF_INT) {
        return SRMECH_ERR_NOT_IMPL;
    }
    if (elem->i < -128 || elem->i > 127) { return SRMECH_ERR_NOT_IMPL; }
    o = (int8_t)elem->i;
    if (o == 0) {                       /* the ABSORBING zero (Class K)     */
        *out = pf_int(b, 0);
        return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
    }
    st = srmech_cascade_reorient_i64(o, acc->i, &r);   /* Class C           */
    if (st != SRMECH_OK) { return st; }
    *out = pf_int(b, r);
    return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* ------------------------------------------------------------------
 * THE PIECE 3 — the fold ARM. NO body step list => NO recursion.
 * ------------------------------------------------------------------ */

/* Read `fold_init` as an INT carrier. A float / string / container seed →
 * NULL → the caller defers (the shipped float + list seeds are exactly the
 * four in-map-body folds this arm does not claim). */
static pf_value_t *pf_seed(pf_bump_t *b, const srmech_json_value_t *fi)
{
    assert(b != NULL);
    assert(b->cur <= b->end);
    if (fi == NULL || fi->type != SRMECH_JSON_INT) { return NULL; }
    return pf_int(b, fi->u.i);
}

/* acc = fold_init; for elem in resolve(over): acc = fold_op(acc, elem).
 * The exact compose.py:1351-1365 iteration contract for the fold_args-absent
 * (positional) case. Empty sequence -> the seed, unchanged. */
static srmech_status_t pf_run_fold(const srmech_json_value_t *step,
                                   const pf_ctx_t *c, pf_bump_t *b,
                                   pf_value_t **out)
{
    const srmech_json_value_t *fo = srmech_json_object_get(step, "fold_op");
    const srmech_json_value_t *ov = srmech_json_object_get(step, "over");
    const srmech_json_value_t *fi = srmech_json_object_get(step, "fold_init");
    const srmech_json_value_t *seq; pf_value_t *acc; uint32_t i;
    srmech_status_t st;
    assert(step != NULL && c != NULL);
    assert(b != NULL && out != NULL);
    if (srmech_json_object_get(step, "fold_args") != NULL) {
        return SRMECH_ERR_NOT_IMPL;      /* kw-named fold: not this arm    */
    }
    if (fo == NULL || fo->type != SRMECH_JSON_STRING) { return SRMECH_ERR_BAD_INPUT; }
    if (ov == NULL || ov->type != SRMECH_JSON_STRING) { return SRMECH_ERR_BAD_INPUT; }
    if (srmech_json_object_get(step, "fold_class") == NULL) {
        return SRMECH_ERR_BAD_INPUT;
    }
    acc = pf_seed(b, fi);
    if (acc == NULL) { return SRMECH_ERR_NOT_IMPL; }
    seq = pf_resolve_ref(c, ov->u.str.ptr, ov->u.str.len);
    if (seq == NULL || seq->type != SRMECH_JSON_ARRAY) { return SRMECH_ERR_NOT_IMPL; }
    if (seq->u.arr.n > (uint32_t)PF_MAX_SEQ) { return SRMECH_ERR_NOT_IMPL; }
    for (i = 0u; i < seq->u.arr.n; i++) {
        const srmech_json_value_t *e = seq->u.arr.items[i];
        pf_value_t *ev; pf_value_t *nxt = NULL;
        assert(i < (uint32_t)PF_MAX_SEQ);              /* JPL Rule 2 bound  */
        if (e == NULL || e->type != SRMECH_JSON_INT) { return SRMECH_ERR_NOT_IMPL; }
        ev = pf_int(b, e->u.i);
        if (ev == NULL) { return SRMECH_ERR_OVERFLOW; }
        st = pf_fold_body(b, fo->u.str.ptr, fo->u.str.len, acc, ev, &nxt);
        if (st != SRMECH_OK) { return st; }
        acc = nxt;
    }
    *out = acc;
    return SRMECH_OK;
}

/* ------------------------------------------------------------------
 * The mini step runner — plain steps DEFER here (this prototype only claims
 * the fold arm), so the loop shows exactly where the arm slots into
 * cr_run_steps (srmech_compose_run.c:713-730).
 * ------------------------------------------------------------------ */

static srmech_status_t pf_run_steps(const srmech_json_value_t *chain,
                                    const pf_ctx_t *ctx_in, pf_bump_t *b,
                                    pf_value_t **final_out)
{
    const srmech_json_value_t *steps = srmech_json_object_get(chain, "steps");
    pf_ctx_t c = *ctx_in; uint32_t i; srmech_status_t st;
    pf_value_t *last = NULL;
    assert(chain != NULL && b != NULL);
    assert(final_out != NULL && ctx_in != NULL);
    if (steps == NULL || steps->type != SRMECH_JSON_ARRAY ||
        steps->u.arr.n == 0u) { return SRMECH_ERR_BAD_INPUT; }
    if (steps->u.arr.n > PF_MAX_STEPS) { return SRMECH_ERR_NOT_IMPL; }
    for (i = 0u; i < steps->u.arr.n; i++) {
        const srmech_json_value_t *step = steps->u.arr.items[i];
        assert(i < PF_MAX_STEPS);                     /* JPL Rule 2 bound  */
        if (step == NULL || step->type != SRMECH_JSON_OBJECT) {
            return SRMECH_ERR_BAD_INPUT;
        }
        c.cur = i;
        switch (pf_step_form(step)) {
        case PF_FORM_FOLD:
            st = pf_run_fold(step, &c, b, &last);
            break;
        case PF_FORM_MIXED:
        case PF_FORM_NONE:
            return SRMECH_ERR_BAD_INPUT;   /* the closed-key-set reject     */
        default:
            return SRMECH_ERR_NOT_IMPL;    /* plain / map: not this arm     */
        }
        if (st != SRMECH_OK) { return st; }
    }
    *final_out = last;
    return SRMECH_OK;
}

/* ------------------------------------------------------------------
 * Driver.
 * ------------------------------------------------------------------ */

static unsigned char g_arena[PF_ARENA_BYTES];

/* Parse chain + ctx JSON, run, return the final int through *out_i.
 * `*out_kind` reports the carrier kind so a NONE result is distinguishable. */
static srmech_status_t pf_drive(const char *chain_json, const char *ctx_json,
                                int64_t *out_i)
{
    pf_bump_t b; srmech_json_value_t *chain = NULL; srmech_json_value_t *ctx = NULL;
    pf_value_t *final_v = NULL; pf_ctx_t c; srmech_status_t st;
    unsigned char *pa, *ca;
    assert(chain_json != NULL && ctx_json != NULL);
    assert(out_i != NULL);
    b.cur = g_arena; b.end = g_arena + sizeof(g_arena);
    pa = pf_carve(&b, 65536u); ca = pf_carve(&b, 65536u);
    if (pa == NULL || ca == NULL) { return SRMECH_ERR_OVERFLOW; }
    st = srmech_json_parse(chain_json, strlen(chain_json), pa, 65536u, &chain);
    if (st != SRMECH_OK) { return st; }
    st = srmech_json_parse(ctx_json, strlen(ctx_json), ca, 65536u, &ctx);
    if (st != SRMECH_OK) { return st; }
    c.row = srmech_json_object_get(ctx, "row");
    c.inputs = srmech_json_object_get(ctx, "inputs");
    c.step_out = NULL; c.cur = 0u;
    st = pf_run_steps(chain, &c, &b, &final_v);
    if (st != SRMECH_OK) { return st; }
    if (final_v == NULL || final_v->kind != PF_INT) { return SRMECH_ERR_BAD_INPUT; }
    *out_i = final_v->i;
    return SRMECH_OK;
}

/* net_chirality's OWN step, verbatim from
 * srmech/cascade/catalogs/cascade_catalog/net_chirality.toml. */
static const char *const NET_CHIRALITY_CHAIN =
    "{\"name\":\"net_chirality\",\"summary\":\"s\",\"returns\":\"int\","
    "\"on_error\":\"raise\",\"steps\":[{"
    "\"fold_class\":\"C\","
    "\"fold_op\":\"srmech.cascade.leaves.orientation_compose\","
    "\"fold_init\":1,\"over\":\"@input.orientations\"}]}";

/* The seven proof cases the descriptor declares, and the value the SHIPPED
 * Python projection returns for each. PROVENANCE: measured on this worktree at
 * 0.9.0rc444 with
 *   srmech.dsl.run_cascade_chain('net_chirality', orientations=<case>)
 * and cross-checked against srmech.cascade.net_chirality(<case>) — the two
 * agree on all seven. NOT hand-derived. */
static const char *const CASES[7] = {
    "{\"row\":null,\"inputs\":{\"orientations\":[]}}",
    "{\"row\":null,\"inputs\":{\"orientations\":[0]}}",
    "{\"row\":null,\"inputs\":{\"orientations\":[0,-1]}}",
    "{\"row\":null,\"inputs\":{\"orientations\":[-1,0,-1]}}",
    "{\"row\":null,\"inputs\":{\"orientations\":[-1,-1]}}",
    "{\"row\":null,\"inputs\":{\"orientations\":[1,-1,1]}}",
    "{\"row\":null,\"inputs\":{\"orientations\":[-1,-1,-1,1]}}"
};
static const int64_t EXPECT[7] = { 1, 0, 0, 0, 1, -1, -1 };
static const char *const COVERS[7] = {
    "empty", "single_zero", "single_zero", "single_zero",
    "sweep", "sweep", "sweep"
};

/* The negative controls: each MUST be declined, and with the stated status. */
static const char *const NEG[5] = {
    /* mixed v1+v2 on one step — the closed-key-set reject (rc444 C ACCEPTS
     * this and silently drops the fold half; measured run rc=0) */
    "{\"name\":\"n\",\"summary\":\"s\",\"returns\":\"r\",\"on_error\":"
    "\"raise\",\"steps\":[{\"class\":\"C\",\"op\":\"reorient\",\"args\":{},"
    "\"fold_class\":\"C\",\"fold_op\":\"orientation_compose\","
    "\"fold_init\":1,\"over\":\"@input.xs\"}]}",
    /* an unknown fold body -> NOT_IMPL (defer, never a wrong answer) */
    "{\"name\":\"n\",\"summary\":\"s\",\"returns\":\"r\",\"on_error\":"
    "\"raise\",\"steps\":[{\"fold_class\":\"C\",\"fold_op\":\"no_such_op\","
    "\"fold_init\":1,\"over\":\"@input.xs\"}]}",
    /* a FLOAT seed -> NOT_IMPL (the carrier has no float kind) */
    "{\"name\":\"n\",\"summary\":\"s\",\"returns\":\"r\",\"on_error\":"
    "\"raise\",\"steps\":[{\"fold_class\":\"M\",\"fold_op\":"
    "\"orientation_compose\",\"fold_init\":0.0,\"over\":\"@input.xs\"}]}",
    /* an unrecognised reference namespace in `over` -> NOT_IMPL */
    "{\"name\":\"n\",\"summary\":\"s\",\"returns\":\"r\",\"on_error\":"
    "\"raise\",\"steps\":[{\"fold_class\":\"C\",\"fold_op\":"
    "\"orientation_compose\",\"fold_init\":1,\"over\":\"@bind.xs\"}]}",
    /* fold_args present (the kw-named fold) -> NOT_IMPL, declared not silent */
    "{\"name\":\"n\",\"summary\":\"s\",\"returns\":\"r\",\"on_error\":"
    "\"raise\",\"steps\":[{\"fold_class\":\"C\",\"fold_op\":"
    "\"orientation_compose\",\"fold_init\":1,\"over\":\"@input.xs\","
    "\"fold_args\":[\"acc\",\"elem\"]}]}"
};
static const srmech_status_t NEG_EXPECT[5] = {
    SRMECH_ERR_BAD_INPUT, SRMECH_ERR_NOT_IMPL, SRMECH_ERR_NOT_IMPL,
    SRMECH_ERR_NOT_IMPL, SRMECH_ERR_NOT_IMPL
};
static const char *const NEG_WHAT[5] = {
    "mixed v1+v2 step (closed-key-set reject)",
    "unknown fold body op",
    "float fold_init (no FLOAT carrier kind)",
    "@bind namespace in `over`",
    "fold_args present (kw-named fold)"
};

int main(void)
{
    int failures = 0; uint32_t i;
    printf("srmech %s  ABI %d  — #1653 surface-A FOLD step-form prototype\n\n",
           srmech_version(), (int)srmech_abi_version());
    printf("POSITIVE: net_chirality's own fold step, its own 7 proof cases\n");
    for (i = 0u; i < 7u; i++) {
        int64_t got = 0; srmech_status_t st;
        assert(i < 7u);
        st = pf_drive(NET_CHIRALITY_CHAIN, CASES[i], &got);
        if (st != SRMECH_OK || got != EXPECT[i]) { failures++; }
        printf("  [%u] covers=%-11s rc=%d  C=%3lld  python=%3lld  %s\n",
               i, COVERS[i], (int)st, (long long)got, (long long)EXPECT[i],
               (st == SRMECH_OK && got == EXPECT[i]) ? "MATCH" : "*** FAIL");
    }
    printf("\nNEGATIVE: every one must DECLINE, with the stated status\n");
    for (i = 0u; i < 5u; i++) {
        int64_t got = 0; srmech_status_t st;
        assert(i < 5u);
        st = pf_drive(NEG[i], "{\"row\":null,\"inputs\":{\"xs\":[1,-1]}}",
                      &got);
        if (st != NEG_EXPECT[i]) { failures++; }
        printf("  [%u] rc=%d (want %d)  %-42s %s\n", i, (int)st,
               (int)NEG_EXPECT[i], NEG_WHAT[i],
               (st == NEG_EXPECT[i]) ? "OK" : "*** FAIL");
    }
    printf("\n%d failure(s)\n", failures);
    return (failures == 0) ? 0 : 1;
}
