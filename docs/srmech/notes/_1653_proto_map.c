/* _1653_proto_map.c — gh #1653 PROTOTYPE: the SURFACE-A (`[[cascade.chain]]`)
 * MAP step form in C, standalone, JPL Power-of-Ten clean, EXPLICIT FRAME STACK.
 *
 * WHY THIS FILE EXISTS. The round-1 report (notes/_1653_PRERCN_REPORT.md)
 * section 6.2 SPECIFIES the map arm as four sub-problems and then says, in
 * writing, that its "60-line / 2-assert" JPL feasibility is reasoned from
 * shipped idioms and NOT measured. This file closes that admission by being the
 * thing: a compiled, executed map arm whose function lengths and assert counts
 * are then measured with the SHIPPED ratchet's own scanner —
 * notes/_1653_proto_map_jpl_rc444.py imports `_scan_functions` /
 * `_function_bodies` out of python/tests/test_jpl_audit.py and runs them over
 * this exact file, including the recursion pass.
 *
 * NO RECURSION, BY CONSTRUCTION. `srmech_dsl_chain_run.c` runs a map body by
 * mutual recursion, and that cycle is one of the 9 SEEDED entries in
 * tests/test_jpl_audit.py RULE_1_RECURSION_SEEDED; test_rule_1_no_new_recursion
 * fails on any cycle NOT in that set, INCLUDING an existing cycle that gains a
 * member. So surface B is prior art to READ, not to copy. Here the body walk is
 * a TRAMPOLINE over an explicit `pm_frame_t` stack: `pm_run` loops,
 * `pm_step_once` advances the top frame, `pm_frame_close` retires it. The call
 * graph is a DAG.
 *
 * WHAT IT EXECUTES — a REAL shipped map step, not a toy.
 *   POSITIVE 1: `klein4_from_one`'s variant-"rest" map step, VERBATIM from
 *   srmech/cascade/catalogs/cascade_catalog/klein4_from_one.toml — the
 *   catalog's LARGEST map (19 body steps, 8 binds, 64 iterations). Steps 0..8
 *   (render_template / utf8_encode / sha256_bytes / str_concat / seq_get) are
 *   outside the map arm, so their MEASURED outputs are injected as the root
 *   frame's pre-seeded step outputs and the root cursor starts past them. All
 *   64 crumbs must match the shipped Python projection EXACTLY.
 *   POSITIVE 2: a NESTED map (depth 2 => 3 live frames) whose inner body step
 *   is verbatim autocorrelation.toml's own
 *   `mod_add(a=@idx.i, b=@idx.k, n=@bind.n)` — the layered-@idx read that a
 *   flat (non-stacked) design cannot express at all.
 *   POSITIVE 3: a TRIPLE-nested map (depth 3 => 4 live frames), the frame-cap
 *   boundary. Synthetic shape, stated as such: it exists to prove the cap
 *   BOUNDARY behaves, since the deepest shipped map is depth 2.
 *   POSITIVE 4: the arena sweep — the nested map at n = 4..256, reporting the
 *   arena high-water for each, which MEASURES the growth law that report
 *   section 6.2 sub-problem 3 carried as an inherited, un-rerun figure.
 *
 * PROVENANCE. Every expected value comes from
 * notes/_1653_map_groundtruth_rc444.py run on this worktree at 0.9.0rc444
 * (`srmech.dsl.run_cascade_chain('klein4_from_one', variant='rest', ...)`,
 * cross-checked True against the shipped op
 * `srmech.math.hdc.klein4_from_one(one, 64)`). The chain / ctx / expected-value
 * literals are GENERATED into _1653_proto_map_data.h by
 * notes/_1653_map_emit_data_rc444.py straight out of the descriptor TOML, whose
 * sha256 that header records — no table in this prototype was transcribed by
 * hand. The frame / body / bind bounds come from
 * notes/_1653_map_frames_rc444.py over all 21 descriptors.
 *
 * SCOPE, stated so nothing is over-claimed.
 *   - The carrier here is INT / STR / LIST / borrowed-JSON. There is NO FLOAT
 *     kind — deliberately, because srmech_compose_run.c's real `cr_value_t` has
 *     none either (cr_json_scalar returns NULL for SRMECH_JSON_DOUBLE). A float
 *     anywhere in an arg DECLINES with SRMECH_ERR_NOT_IMPL and the chain defers
 *     to pure. MEASURED at rc444: 12 of the catalog's 14 map steps sit in a
 *     chain whose own proof-case inputs carry floats; only klein4_from_one's 2
 *     are int-only. That is the one thing this arm cannot reach without a
 *     carrier widening.
 *   - `byte_slice` / `int_parse_le` read a STR carrier here, which is
 *     byte-faithful for the ASCII hex the shipped chain feeds them and is NOT a
 *     general bytes carrier.
 *   - The 6-op body table is bounded and CLOSED: seq_get (E), mod_add /
 *     mod_mul (I), byte_slice / int_parse_le / pair (B). Every other op
 *     DECLINES with NOT_IMPL.
 *   - Nothing here edits c/src/, c/include/ or python/. It is a standalone
 *     driver linking build/libsrmech.a; the rcN owner lifts the named pieces.
 *
 * BUILD (one line; a trailing backslash in a comment trips the Rule 8 ratchet,
 * which does not strip comments):
 *   cc -std=c99 -Wall -Wextra -Wpedantic -O2 -Iinclude ../notes/_1653_proto_map.c build/libsrmech.a -o /tmp/proto_map
 * then run /tmp/proto_map  (exit 0 == every check passes)
 *
 * JPL Power-of-Ten: caller-arena only (one file-scope arena, carved
 * bump-forward; no malloc), NO recursion, NO goto, every function <= 60 lines
 * with >= 2 asserts, every loop explicitly bounded AND asserted, no libm, every
 * srmech_* return checked. There is no sign work in this arm at all; a real
 * magnitude is the Class-K pin-slot op srmech_cascade_magnitude_* called BY
 * NAME, and no ALU-magnitude idiom appears anywhere in this file.
 */

#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "srmech.h"

/* ------------------------------------------------------------------
 * Bounds (JPL Rule 2 — every loop has an explicit compiled cap).
 * MEASURED sources, from notes/_1653_map_frames_rc444.ndjson over all 21
 * shipped descriptors: max map nesting depth 1 (two levels) => frames_needed
 * 3; max body length 19; max binds 9.
 * ------------------------------------------------------------------ */
#define PM_MAX_FRAMES  4u         /* 3 needed; 1 spare so the cap is probeable */
#define PM_MAX_STEPS   32u        /* per step list (19 measured)               */
#define PM_MAX_ENV     32u        /* layered idx + bind entries (9 measured)   */
#define PM_MAX_SEQ     4096u      /* map n / sequence length cap               */
#define PM_MAX_TURNS   (1u << 24) /* trampoline turn cap                       */
#define PM_ARENA_BYTES (48u << 20)/* the one file-scope arena                  */
#define PM_JSON_WS     131072u    /* per-document JSON parse workspace         */
#define PM_KEY_MAX     64u        /* reference-segment name cap                */

/* ------------------------------------------------------------------
 * Bump arena — forward-only carve (the srmech_compose_run.c idiom verbatim).
 * ------------------------------------------------------------------ */

typedef struct { unsigned char *base; unsigned char *cur; unsigned char *end; }
    pm_bump_t;

static unsigned char *pm_align(unsigned char *p)
{
    uintptr_t a = (uintptr_t)sizeof(void *);
    uintptr_t pad;
    assert(p != NULL);
    assert(a >= 4u);
    pad = (a - ((uintptr_t)p % a)) % a;
    return p + pad;
}

static unsigned char *pm_carve(pm_bump_t *b, size_t n)
{
    unsigned char *p;
    assert(b != NULL);
    assert(b->cur <= b->end);
    p = pm_align(b->cur);
    if (p > b->end || n > (size_t)(b->end - p)) { return NULL; }
    b->cur = p + n;
    return p;
}

/* ------------------------------------------------------------------
 * The value carrier. INT / STR / LIST, plus PM_JSON — a BORROWED parsed
 * JSON node.
 *
 * PM_JSON IS A FINDING, not a shortcut. Report section 6.2 sub-problem 3
 * sizes the map arena from a per-iteration JSON->carrier COPY, which is what
 * makes it blow up. klein4_from_one's map binds eight literal tables (one
 * 64-entry, one 55-entry) and runs 64 iterations: copying them per iteration
 * is a 64x waste of arena for values that never change. A carrier kind that
 * BORROWS the parsed node makes the copy unnecessary AND removes the only
 * place a JSON->carrier conversion would want to recurse — a nested literal
 * like xor4 = [[..],[..]] is indexed IN PLACE, never rebuilt.
 * srmech_compose_run.c's real cr_value_t has no such kind today.
 * ------------------------------------------------------------------ */

typedef enum { PM_NONE = 0, PM_INT, PM_STR, PM_LIST, PM_JSON } pm_kind_t;

typedef struct pm_value {
    pm_kind_t kind;
    int64_t   i;                              /* PM_INT                     */
    const char *sp; uint32_t sl;              /* PM_STR (borrowed bytes)    */
    struct pm_value **items; uint32_t n;      /* PM_LIST                    */
    const srmech_json_value_t *j;             /* PM_JSON (borrowed node)    */
} pm_value_t;

static pm_value_t *pm_new(pm_bump_t *b, pm_kind_t kind)
{
    pm_value_t *v;
    assert(b != NULL);
    assert(kind >= PM_NONE && kind <= PM_JSON);
    v = (pm_value_t *)pm_carve(b, sizeof(pm_value_t));
    if (v == NULL) { return NULL; }
    v->kind = kind; v->i = 0; v->sp = NULL; v->sl = 0u;
    v->items = NULL; v->n = 0u; v->j = NULL;
    return v;
}

static pm_value_t *pm_int(pm_bump_t *b, int64_t i)
{
    pm_value_t *v = pm_new(b, PM_INT);
    assert(b != NULL);
    assert(sizeof(i) == 8u);
    if (v == NULL) { return NULL; }
    v->i = i;
    return v;
}

static pm_value_t *pm_str(pm_bump_t *b, const char *p, uint32_t len)
{
    pm_value_t *v;
    assert(b != NULL);
    assert(p != NULL || len == 0u);
    v = pm_new(b, PM_STR);
    if (v == NULL) { return NULL; }
    v->sp = p; v->sl = len;
    return v;
}

static pm_value_t *pm_json(pm_bump_t *b, const srmech_json_value_t *j)
{
    pm_value_t *v;
    assert(b != NULL);
    assert(j != NULL);
    v = pm_new(b, PM_JSON);
    if (v == NULL) { return NULL; }
    v->j = j;
    return v;
}

/* ------------------------------------------------------------------
 * Carrier accessors — the ONE place PM_LIST and PM_JSON unify, so no op
 * below has to know which it got.
 * ------------------------------------------------------------------ */

/* Element count of a sized carrier; -1 when the carrier is NOT sized. That
 * -1 is the map form's entry contract: compose.py:1299-1306 raises exactly
 * here, because an unsized iterable would make n data-DEPENDENT rather than
 * data-SIZED. */
static int64_t pm_len(const pm_value_t *v)
{
    assert(v != NULL);
    assert(v->kind >= PM_NONE && v->kind <= PM_JSON);
    if (v->kind == PM_LIST) { return (int64_t)v->n; }
    if (v->kind == PM_STR)  { return (int64_t)v->sl; }
    if (v->kind == PM_JSON && v->j->type == SRMECH_JSON_ARRAY) {
        return (int64_t)v->j->u.arr.n;
    }
    if (v->kind == PM_JSON && v->j->type == SRMECH_JSON_STRING) {
        return (int64_t)v->j->u.str.len;
    }
    return -1;
}

/* seq[i] for a sized carrier. Out of range returns NULL and the caller
 * declines — Python raises IndexError, so parity is a REJECT, never a wrap. */
static pm_value_t *pm_elem(pm_bump_t *b, const pm_value_t *v, int64_t i)
{
    int64_t n = pm_len(v);
    assert(b != NULL);
    assert(v != NULL);
    if (n < 0 || i < 0 || i >= n) { return NULL; }
    if (v->kind == PM_LIST) { return v->items[i]; }
    if (v->kind == PM_JSON && v->j->type == SRMECH_JSON_ARRAY) {
        return pm_json(b, v->j->u.arr.items[i]);
    }
    return NULL;                     /* a STR is sized but not indexable   */
}

/* The int reading of a carrier: PM_INT, or a borrowed JSON int. A DOUBLE
 * declines — the measured carrier gap, reported rather than papered over. */
static int pm_as_i64(const pm_value_t *v, int64_t *out)
{
    assert(v != NULL);
    assert(out != NULL);
    if (v->kind == PM_INT) { *out = v->i; return 1; }
    if (v->kind == PM_JSON && v->j->type == SRMECH_JSON_INT) {
        *out = v->j->u.i; return 1;
    }
    return 0;
}

/* The byte reading of a carrier: PM_STR or a borrowed JSON string. */
static int pm_as_bytes(const pm_value_t *v, const char **p, uint32_t *len)
{
    assert(v != NULL);
    assert(p != NULL && len != NULL);
    if (v->kind == PM_STR) { *p = v->sp; *len = v->sl; return 1; }
    if (v->kind == PM_JSON && v->j->type == SRMECH_JSON_STRING) {
        *p = v->j->u.str.ptr; *len = v->j->u.str.len; return 1;
    }
    return 0;
}

/* ------------------------------------------------------------------
 * The frame + the machine state. Everything is caller-arena or file-scope;
 * nothing is malloc'd and nothing is per-call static, so the machine is
 * reentrant on disjoint arenas (the rc306 caller-arena pattern).
 * ------------------------------------------------------------------ */

typedef struct {
    const srmech_json_value_t *steps;    /* the step list this frame runs   */
    uint32_t si;                         /* cursor within it               */
    uint32_t so_base;                    /* base into st->so               */
    uint32_t idx_mark;                   /* env sizes to restore on pop    */
    uint32_t bnd_mark;
    const srmech_json_value_t *map_step; /* non-NULL => a map BODY frame   */
    uint32_t map_si;                     /* parent step index it fills     */
    uint32_t k;                          /* current map iteration          */
    uint32_t n;                          /* the totality pin, FIXED at entry */
    pm_value_t **acc;                    /* n result slots                 */
} pm_frame_t;

typedef struct {
    const srmech_json_value_t *row;
    const srmech_json_value_t *inputs;
    const char *idx_name[PM_MAX_ENV]; uint32_t idx_nlen[PM_MAX_ENV];
    int64_t     idx_val[PM_MAX_ENV];  uint32_t idx_n;
    const char *bnd_name[PM_MAX_ENV]; uint32_t bnd_nlen[PM_MAX_ENV];
    pm_value_t *bnd_val[PM_MAX_ENV];  uint32_t bnd_n;
    pm_value_t *so[PM_MAX_FRAMES * PM_MAX_STEPS];
    pm_frame_t  fr[PM_MAX_FRAMES];
    uint32_t    nfr;
    uint32_t    peak_frames;
    pm_bump_t  *b;
} pm_state_t;

/* Step-form classification — the CLOSED-KEY-SET check rc444's C parse does
 * NOT do (srmech_compose.c:299-303 is a REQUIRED-keys check, so a step
 * carrying a valid plain skeleton AND map keys parses in C with the v2 half
 * silently DISCARDED). Key lists mirror compose.py:162-163, and a widening on
 * either side must move both. */
typedef enum {
    PM_FORM_PLAIN = 0, PM_FORM_MAP, PM_FORM_FOLD, PM_FORM_MIXED, PM_FORM_NONE
} pm_form_t;

static int pm_has_any(const srmech_json_value_t *step,
                      const char *const *keys, uint32_t n)
{
    uint32_t i;
    assert(step != NULL && keys != NULL);
    assert(n > 0u && n <= 8u);
    for (i = 0u; i < n; i++) {
        if (srmech_json_object_get(step, keys[i]) != NULL) { return 1; }
    }
    return 0;
}

static pm_form_t pm_step_form(const srmech_json_value_t *step)
{
    static const char *const map_k[4] = {"map_over", "index", "bind", "body"};
    static const char *const fold_k[5] = {"fold_class", "fold_op", "fold_init",
                                          "over", "fold_args"};
    static const char *const plain_k[3] = {"class", "op", "args"};
    int m, f, p;
    assert(step != NULL);
    assert(step->type == SRMECH_JSON_OBJECT);
    m = pm_has_any(step, map_k, 4u);
    f = pm_has_any(step, fold_k, 5u);
    p = pm_has_any(step, plain_k, 3u);
    if ((m + f + p) > 1) { return PM_FORM_MIXED; }
    if (m) { return PM_FORM_MAP; }
    if (f) { return PM_FORM_FOLD; }
    if (p) { return PM_FORM_PLAIN; }
    return PM_FORM_NONE;
}

/* ------------------------------------------------------------------
 * PIECE 1 — reference resolution, including the two namespaces the shipped
 * C resolver does not know: @idx and @bind. Both are NAME-CHECKED against the
 * layered environment, which is the parity behaviour — compose.py:303-322
 * REJECTS an @idx / @bind name no enclosing map binds. The round-1 census
 * measured that NO key-set or name-set validator exists anywhere in the C
 * leaf surface (#T1146); this is one.
 * ------------------------------------------------------------------ */

/* Copy the single dotted segment starting at `pos` into `key`. 0 on any shape
 * the grammar does not allow: empty, over-long, or a second segment. */
static int pm_seg(const char *ref, uint32_t len, uint32_t pos,
                  char *key, uint32_t *klen)
{
    uint32_t kl = 0u;
    assert(ref != NULL && key != NULL);
    assert(klen != NULL);
    while (pos < len && ref[pos] != '.' && ref[pos] != '[') {
        if (kl + 1u >= PM_KEY_MAX) { return 0; }        /* JPL Rule 2 bound */
        key[kl++] = ref[pos++];
    }
    if (pos != len || kl == 0u) { return 0; }      /* one segment only      */
    key[kl] = '\0';
    *klen = kl;
    return 1;
}

/* Innermost-wins scan of the layered @idx environment. compose.py builds
 * inner_idx = dict(idx_env) then sets its OWN name, so a shadowing inner
 * index wins; scanning backwards reproduces that exactly. */
static int pm_idx_lookup(const pm_state_t *st, const char *key, uint32_t kl,
                         int64_t *out)
{
    uint32_t i;
    assert(st != NULL && key != NULL);
    assert(out != NULL && st->idx_n <= PM_MAX_ENV);
    for (i = st->idx_n; i > 0u; i--) {
        assert(i - 1u < PM_MAX_ENV);                    /* JPL Rule 2 bound */
        if (st->idx_nlen[i - 1u] == kl &&
            memcmp(st->idx_name[i - 1u], key, kl) == 0) {
            *out = st->idx_val[i - 1u];
            return 1;
        }
    }
    return 0;
}

static pm_value_t *pm_bind_lookup(const pm_state_t *st, const char *key,
                                  uint32_t kl)
{
    uint32_t i;
    assert(st != NULL && key != NULL);
    assert(st->bnd_n <= PM_MAX_ENV);
    for (i = st->bnd_n; i > 0u; i--) {
        assert(i - 1u < PM_MAX_ENV);                    /* JPL Rule 2 bound */
        if (st->bnd_nlen[i - 1u] == kl &&
            memcmp(st->bnd_name[i - 1u], key, kl) == 0) {
            return st->bnd_val[i - 1u];
        }
    }
    return NULL;
}

/* `@step[N].output` -> the CURRENT frame's own N-th step output. Body-local by
 * construction (the rc420 scoping decision: a body is a chain in miniature
 * with its OWN step_outputs). A forward reference is REJECTED, matching
 * compose.py:297-301. */
static srmech_status_t pm_ref_step(const pm_state_t *st, const char *p,
                                   uint32_t rem, pm_value_t **out)
{
    static const char tail[9] = "].output";
    const pm_frame_t *f;
    uint32_t d = 0u, nn = 0u;
    assert(st != NULL && p != NULL);
    assert(out != NULL && st->nfr > 0u);
    f = &st->fr[st->nfr - 1u];
    while (d < rem && p[d] >= '0' && p[d] <= '9') {
        nn = (nn * 10u) + (uint32_t)(p[d] - '0');
        if (nn >= PM_MAX_STEPS) { return SRMECH_ERR_LIMIT; }
        d++;
    }
    if (d == 0u || (rem - d) != 8u || memcmp(p + d, tail, 8u) != 0) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (nn >= f->si) { return SRMECH_ERR_BAD_INPUT; }   /* forward ref      */
    *out = st->so[f->so_base + nn];
    return (*out == NULL) ? SRMECH_ERR_BAD_INPUT : SRMECH_OK;
}

/* The five namespaces this arm resolves. @catalog / @op stay unrecognised,
 * exactly as they are in cr_resolve_ref (measured at rc444: run rc=2). */
static srmech_status_t pm_resolve_ref(pm_state_t *st, const char *ref,
                                      uint32_t len, pm_value_t **out)
{
    char key[PM_KEY_MAX];
    uint32_t kl = 0u;
    const srmech_json_value_t *base = NULL;
    int64_t iv = 0;
    assert(st != NULL && ref != NULL);
    assert(out != NULL && len < 0x7fffffffu);
    if (len < 2u || ref[0] != '@') { return SRMECH_ERR_BAD_INPUT; }
    if (len > 6u && memcmp(ref + 1, "step[", 5u) == 0) {
        return pm_ref_step(st, ref + 6, len - 6u, out);
    }
    if (len > 5u && memcmp(ref + 1, "idx.", 4u) == 0) {
        if (!pm_seg(ref, len, 5u, key, &kl)) { return SRMECH_ERR_BAD_INPUT; }
        if (!pm_idx_lookup(st, key, kl, &iv)) { return SRMECH_ERR_BAD_INPUT; }
        *out = pm_int(st->b, iv);
        return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
    }
    if (len > 6u && memcmp(ref + 1, "bind.", 5u) == 0) {
        if (!pm_seg(ref, len, 6u, key, &kl)) { return SRMECH_ERR_BAD_INPUT; }
        *out = pm_bind_lookup(st, key, kl);
        return (*out == NULL) ? SRMECH_ERR_BAD_INPUT : SRMECH_OK;
    }
    if (len > 5u && memcmp(ref + 1, "row.", 4u) == 0) { base = st->row; kl = 5u; }
    else if (len > 7u && memcmp(ref + 1, "input.", 6u) == 0) {
        base = st->inputs; kl = 7u;
    } else { return SRMECH_ERR_NOT_IMPL; }        /* @catalog / @op -> defer */
    if (base == NULL || base->type != SRMECH_JSON_OBJECT) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (!pm_seg(ref, len, kl, key, &kl)) { return SRMECH_ERR_BAD_INPUT; }
    base = srmech_json_object_get(base, key);
    if (base == NULL) { return SRMECH_ERR_BAD_INPUT; }
    *out = pm_json(st->b, base);
    return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* One arg node -> one carrier. A DOUBLE declines: the measured carrier gap
 * (cr_json_scalar returns NULL for SRMECH_JSON_DOUBLE), and the reason 12 of
 * the catalog's 14 map steps stay out of reach. */
static srmech_status_t pm_eval(pm_state_t *st, const srmech_json_value_t *nd,
                               pm_value_t **out)
{
    assert(st != NULL && out != NULL);
    assert(st->b != NULL);
    if (nd == NULL) { return SRMECH_ERR_BAD_INPUT; }
    if (nd->type == SRMECH_JSON_STRING && nd->u.str.len > 0u &&
        nd->u.str.ptr[0] == '@') {
        return pm_resolve_ref(st, nd->u.str.ptr, nd->u.str.len, out);
    }
    if (nd->type == SRMECH_JSON_DOUBLE) { return SRMECH_ERR_NOT_IMPL; }
    if (nd->type == SRMECH_JSON_NULL || nd->type == SRMECH_JSON_BOOL ||
        nd->type == SRMECH_JSON_OBJECT) {
        return SRMECH_ERR_NOT_IMPL;
    }
    *out = pm_json(st->b, nd);
    return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

static srmech_status_t pm_arg(pm_state_t *st, const srmech_json_value_t *args,
                              const char *key, pm_value_t **out)
{
    assert(st != NULL && key != NULL);
    assert(out != NULL);
    if (args == NULL || args->type != SRMECH_JSON_OBJECT) {
        return SRMECH_ERR_BAD_INPUT;
    }
    return pm_eval(st, srmech_json_object_get(args, key), out);
}

/* ------------------------------------------------------------------
 * PIECE 2 — the BOUNDED body-op table. Six ops, CLOSED. Everything else
 * declines with SRMECH_ERR_NOT_IMPL and the whole chain defers to pure (the
 * rc103 inform-don't-limit contract: never a wrong answer).
 * ------------------------------------------------------------------ */

typedef enum {
    PM_OP_NONE = 0, PM_OP_SEQ_GET, PM_OP_MOD_ADD, PM_OP_MOD_MUL,
    PM_OP_BYTE_SLICE, PM_OP_INT_PARSE_LE, PM_OP_PAIR
} pm_op_t;

/* Bare name, or any dotted spelling ending `.<bare>` — the descriptors write
 * both (`mod_add` bare, `srmech.cascade.leaves.seq_get` dotted). The idiom is
 * srmech_dsl_chain_run.c:738-745 dsl_map_body_is_seq_get. */
static int pm_name_is(const char *op, uint32_t opl, const char *bare)
{
    uint32_t bl = (uint32_t)strlen(bare);
    assert(op != NULL && bare != NULL);
    assert(bl > 0u && bl < 64u);
    if (opl == bl && memcmp(op, bare, bl) == 0) { return 1; }
    if (opl > bl + 1u && op[opl - bl - 1u] == '.' &&
        memcmp(op + (opl - bl), bare, bl) == 0) { return 1; }
    return 0;
}

static pm_op_t pm_op_id(const char *op, uint32_t opl)
{
    assert(op != NULL);
    assert(opl > 0u);
    if (pm_name_is(op, opl, "seq_get"))      { return PM_OP_SEQ_GET; }
    if (pm_name_is(op, opl, "mod_add"))      { return PM_OP_MOD_ADD; }
    if (pm_name_is(op, opl, "mod_mul"))      { return PM_OP_MOD_MUL; }
    if (pm_name_is(op, opl, "byte_slice"))   { return PM_OP_BYTE_SLICE; }
    if (pm_name_is(op, opl, "int_parse_le")) { return PM_OP_INT_PARSE_LE; }
    if (pm_name_is(op, opl, "pair"))         { return PM_OP_PAIR; }
    return PM_OP_NONE;
}

/* Class E — seq_get(seq, i): the degenerate catalog lookup (the catalog is
 * the sequence, the key is the index). */
static srmech_status_t pm_do_seq_get(pm_state_t *st,
                                     const srmech_json_value_t *args,
                                     pm_value_t **out)
{
    pm_value_t *sq = NULL, *ix = NULL;
    srmech_status_t rc;
    int64_t i = 0;
    assert(st != NULL && out != NULL);
    assert(st->b != NULL);
    rc = pm_arg(st, args, "seq", &sq);
    if (rc != SRMECH_OK) { return rc; }
    rc = pm_arg(st, args, "i", &ix);
    if (rc != SRMECH_OK) { return rc; }
    if (!pm_as_i64(ix, &i)) { return SRMECH_ERR_NOT_IMPL; }
    *out = pm_elem(st->b, sq, i);
    return (*out == NULL) ? SRMECH_ERR_BAD_INPUT : SRMECH_OK;
}

/* Class I — mod_add / mod_mul(a, b, n), routed through the SHIPPED kernels
 * srmech_mod_add / srmech_mod_mul (overflow-safe; n == 0 declines there). */
static srmech_status_t pm_do_mod(pm_state_t *st,
                                 const srmech_json_value_t *args,
                                 int is_mul, pm_value_t **out)
{
    pm_value_t *va = NULL, *vb = NULL, *vn = NULL;
    int64_t a = 0, b = 0, n = 0;
    uint64_t r = 0u;
    srmech_status_t rc;
    assert(st != NULL && out != NULL);
    assert(st->b != NULL);
    rc = pm_arg(st, args, "a", &va);
    if (rc == SRMECH_OK) { rc = pm_arg(st, args, "b", &vb); }
    if (rc == SRMECH_OK) { rc = pm_arg(st, args, "n", &vn); }
    if (rc != SRMECH_OK) { return rc; }
    if (!pm_as_i64(va, &a) || !pm_as_i64(vb, &b) || !pm_as_i64(vn, &n)) {
        return SRMECH_ERR_NOT_IMPL;
    }
    if (a < 0 || b < 0 || n < 0) { return SRMECH_ERR_NOT_IMPL; }
    rc = is_mul ? srmech_mod_mul((uint64_t)a, (uint64_t)b, (uint64_t)n, &r)
                : srmech_mod_add((uint64_t)a, (uint64_t)b, (uint64_t)n, &r);
    if (rc != SRMECH_OK) { return rc; }
    *out = pm_int(st->b, (int64_t)r);
    return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* Class B — byte_slice(data, start, stop): data[start:stop], BORROWED. */
static srmech_status_t pm_do_byte_slice(pm_state_t *st,
                                        const srmech_json_value_t *args,
                                        pm_value_t **out)
{
    pm_value_t *vd = NULL, *v0 = NULL, *v1 = NULL;
    const char *p = NULL; uint32_t len = 0u;
    int64_t s0 = 0, s1 = 0;
    srmech_status_t rc;
    assert(st != NULL && out != NULL);
    assert(st->b != NULL);
    rc = pm_arg(st, args, "data", &vd);
    if (rc == SRMECH_OK) { rc = pm_arg(st, args, "start", &v0); }
    if (rc == SRMECH_OK) { rc = pm_arg(st, args, "stop", &v1); }
    if (rc != SRMECH_OK) { return rc; }
    if (!pm_as_bytes(vd, &p, &len)) { return SRMECH_ERR_NOT_IMPL; }
    if (!pm_as_i64(v0, &s0) || !pm_as_i64(v1, &s1)) {
        return SRMECH_ERR_NOT_IMPL;
    }
    if (s0 < 0 || s1 < s0 || s1 > (int64_t)len) {
        return SRMECH_ERR_BAD_INPUT;
    }
    *out = pm_str(st->b, p + s0, (uint32_t)(s1 - s0));
    return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* Class B — int_parse_le(data): int.from_bytes(data, "little"), unsigned. */
static srmech_status_t pm_do_int_parse_le(pm_state_t *st,
                                          const srmech_json_value_t *args,
                                          pm_value_t **out)
{
    pm_value_t *vd = NULL;
    const char *p = NULL; uint32_t len = 0u, i;
    uint64_t acc = 0u;
    srmech_status_t rc;
    assert(st != NULL && out != NULL);
    assert(st->b != NULL);
    rc = pm_arg(st, args, "data", &vd);
    if (rc != SRMECH_OK) { return rc; }
    if (!pm_as_bytes(vd, &p, &len)) { return SRMECH_ERR_NOT_IMPL; }
    if (len > 8u) { return SRMECH_ERR_NOT_IMPL; }    /* wider than int64    */
    for (i = 0u; i < len; i++) {
        assert(i < 8u);                              /* JPL Rule 2 bound   */
        acc |= ((uint64_t)(unsigned char)p[i]) << (8u * i);
    }
    if (acc > (uint64_t)INT64_MAX) { return SRMECH_ERR_OVERFLOW; }
    *out = pm_int(st->b, (int64_t)acc);
    return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* Class B — pair(first, second): the 2-element frame. */
static srmech_status_t pm_do_pair(pm_state_t *st,
                                  const srmech_json_value_t *args,
                                  pm_value_t **out)
{
    pm_value_t *a = NULL, *b2 = NULL, *v;
    pm_value_t **cells;
    srmech_status_t rc;
    assert(st != NULL && out != NULL);
    assert(st->b != NULL);
    rc = pm_arg(st, args, "first", &a);
    if (rc == SRMECH_OK) { rc = pm_arg(st, args, "second", &b2); }
    if (rc != SRMECH_OK) { return rc; }
    cells = (pm_value_t **)pm_carve(st->b, 2u * sizeof(pm_value_t *));
    v = pm_new(st->b, PM_LIST);
    if (cells == NULL || v == NULL) { return SRMECH_ERR_OVERFLOW; }
    cells[0] = a; cells[1] = b2;
    v->items = cells; v->n = 2u;
    *out = v;
    return SRMECH_OK;
}

static srmech_status_t pm_dispatch(pm_state_t *st,
                                   const srmech_json_value_t *step,
                                   pm_value_t **out)
{
    const srmech_json_value_t *o = srmech_json_object_get(step, "op");
    const srmech_json_value_t *a = srmech_json_object_get(step, "args");
    assert(st != NULL && step != NULL);
    assert(out != NULL);
    if (srmech_json_object_get(step, "class") == NULL) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (o == NULL || o->type != SRMECH_JSON_STRING) {
        return SRMECH_ERR_BAD_INPUT;
    }
    switch (pm_op_id(o->u.str.ptr, o->u.str.len)) {
    case PM_OP_SEQ_GET:      return pm_do_seq_get(st, a, out);
    case PM_OP_MOD_ADD:      return pm_do_mod(st, a, 0, out);
    case PM_OP_MOD_MUL:      return pm_do_mod(st, a, 1, out);
    case PM_OP_BYTE_SLICE:   return pm_do_byte_slice(st, a, out);
    case PM_OP_INT_PARSE_LE: return pm_do_int_parse_le(st, a, out);
    case PM_OP_PAIR:         return pm_do_pair(st, a, out);
    default:                 return SRMECH_ERR_NOT_IMPL;
    }
}

/* ------------------------------------------------------------------
 * PIECE 3 — the MAP ARM proper: bind-push, frame-open, push, iterate, close,
 * trampoline. Six functions, one explicit stack, zero recursion.
 * ------------------------------------------------------------------ */

/* Resolve the map's `bind` table ONCE at map entry, in the OUTER environment
 * (compose.py:1307-1313 — binds are resolved before the first body run and are
 * the same for every k). Layered: these entries shadow outer ones. */
static srmech_status_t pm_bind_push(pm_state_t *st,
                                    const srmech_json_value_t *bind)
{
    uint32_t i;
    assert(st != NULL);
    assert(st->bnd_n <= PM_MAX_ENV);
    if (bind == NULL) { return SRMECH_OK; }
    if (bind->type != SRMECH_JSON_OBJECT) { return SRMECH_ERR_BAD_INPUT; }
    if (bind->u.obj.n > (PM_MAX_ENV - st->bnd_n)) { return SRMECH_ERR_LIMIT; }
    for (i = 0u; i < bind->u.obj.n; i++) {
        pm_value_t *v = NULL;
        srmech_status_t rc;
        assert(i < PM_MAX_ENV);                       /* JPL Rule 2 bound   */
        rc = pm_eval(st, bind->u.obj.vals[i], &v);
        if (rc != SRMECH_OK) { return rc; }
        st->bnd_name[st->bnd_n] = bind->u.obj.keys[i];
        st->bnd_nlen[st->bnd_n] = (uint32_t)strlen(bind->u.obj.keys[i]);
        st->bnd_val[st->bnd_n] = v;
        st->bnd_n++;
    }
    return SRMECH_OK;
}

/* An n == 0 map: no frame, no body run, the empty list. Split out so
 * pm_push_map stays a pure discriminator. */
static srmech_status_t pm_map_empty(pm_state_t *st)
{
    pm_frame_t *f = &st->fr[st->nfr - 1u];
    pm_value_t *lv;
    assert(st != NULL && st->nfr > 0u);
    assert(f->si < PM_MAX_STEPS);
    lv = pm_new(st->b, PM_LIST);
    if (lv == NULL) { return SRMECH_ERR_OVERFLOW; }
    st->so[f->so_base + f->si] = lv;
    f->si++;
    return SRMECH_OK;
}

/* Carve the accumulator, layer the environments, make the new top frame.
 * Split out of pm_push_map so both stay under the 60-line rule. n >= 1 here:
 * pm_push_map routes n == 0 to pm_map_empty. */
static srmech_status_t pm_frame_open(pm_state_t *st,
                                     const srmech_json_value_t *step,
                                     const srmech_json_value_t *body,
                                     const srmech_json_value_t *ix,
                                     uint32_t n)
{
    static const char dflt[2] = "k";    /* compose.py's default @idx name  */
    pm_frame_t *p = &st->fr[st->nfr - 1u];
    pm_frame_t *f = &st->fr[st->nfr];
    srmech_status_t rc;
    assert(st != NULL && step != NULL);
    assert(body != NULL && st->nfr < PM_MAX_FRAMES && n >= 1u);
    f->idx_mark = st->idx_n; f->bnd_mark = st->bnd_n;
    rc = pm_bind_push(st, srmech_json_object_get(step, "bind"));
    if (rc != SRMECH_OK) { return rc; }
    if (st->idx_n >= PM_MAX_ENV) { return SRMECH_ERR_LIMIT; }
    st->idx_name[st->idx_n] = (ix != NULL) ? ix->u.str.ptr : dflt;
    st->idx_nlen[st->idx_n] = (ix != NULL) ? ix->u.str.len : 1u;
    st->idx_val[st->idx_n] = 0;
    st->idx_n++;
    f->acc = (pm_value_t **)pm_carve(st->b,
                                     (size_t)n * sizeof(pm_value_t *));
    if (f->acc == NULL) { return SRMECH_ERR_OVERFLOW; }
    f->steps = body; f->si = 0u; f->k = 0u; f->n = n;
    f->map_step = step; f->map_si = p->si;
    f->so_base = st->nfr * PM_MAX_STEPS;
    st->nfr++;
    if (st->nfr > st->peak_frames) { st->peak_frames = st->nfr; }
    return SRMECH_OK;
}

/* Push one map-body frame. n is FIXED HERE — the totality pin: exactly n body
 * runs, no predicate, n never re-read (compose.py:1300). n == 0 needs no frame
 * at all: the map's value is the empty list. */
static srmech_status_t pm_push_map(pm_state_t *st,
                                   const srmech_json_value_t *step)
{
    const srmech_json_value_t *mo = srmech_json_object_get(step, "map_over");
    const srmech_json_value_t *bd = srmech_json_object_get(step, "body");
    const srmech_json_value_t *ix = srmech_json_object_get(step, "index");
    pm_value_t *seq = NULL; int64_t n; srmech_status_t rc;
    assert(st != NULL && step != NULL);
    assert(st->nfr > 0u && st->nfr <= PM_MAX_FRAMES);
    if (mo == NULL || mo->type != SRMECH_JSON_STRING) {
        return SRMECH_ERR_BAD_INPUT;            /* map_over is REQUIRED     */
    }
    if (bd == NULL || bd->type != SRMECH_JSON_ARRAY || bd->u.arr.n == 0u) {
        return SRMECH_ERR_BAD_INPUT;            /* body is REQUIRED         */
    }
    if (bd->u.arr.n > PM_MAX_STEPS) { return SRMECH_ERR_LIMIT; }
    if (ix != NULL && ix->type != SRMECH_JSON_STRING) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (st->nfr >= PM_MAX_FRAMES) { return SRMECH_ERR_NOT_IMPL; }
    rc = pm_resolve_ref(st, mo->u.str.ptr, mo->u.str.len, &seq);
    if (rc != SRMECH_OK) { return rc; }
    n = pm_len(seq);
    if (n < 0) { return SRMECH_ERR_BAD_INPUT; }    /* the unsized reject    */
    if (n > (int64_t)PM_MAX_SEQ) { return SRMECH_ERR_LIMIT; }
    if (n == 0) { return pm_map_empty(st); }
    return pm_frame_open(st, step, bd, ix, (uint32_t)n);
}

/* Advance the top frame by exactly one step. */
static srmech_status_t pm_step_once(pm_state_t *st)
{
    pm_frame_t *f = &st->fr[st->nfr - 1u];
    const srmech_json_value_t *step;
    pm_value_t *v = NULL;
    srmech_status_t rc;
    assert(st != NULL && st->nfr > 0u);
    assert(f->si < f->steps->u.arr.n);
    step = f->steps->u.arr.items[f->si];
    if (step == NULL || step->type != SRMECH_JSON_OBJECT) {
        return SRMECH_ERR_BAD_INPUT;
    }
    switch (pm_step_form(step)) {
    case PM_FORM_MAP:
        return pm_push_map(st, step);
    case PM_FORM_PLAIN:
        rc = pm_dispatch(st, step, &v);
        if (rc != SRMECH_OK) { return rc; }
        st->so[f->so_base + f->si] = v;
        f->si++;
        return SRMECH_OK;
    case PM_FORM_MIXED:
    case PM_FORM_NONE:
        return SRMECH_ERR_BAD_INPUT;        /* the closed-key-set reject    */
    default:
        return SRMECH_ERR_NOT_IMPL;         /* fold: the OTHER arm          */
    }
}

/* An exhausted frame retires: a map-body frame either starts iteration k+1 or
 * POPS with its n results as one list; the root frame yields the chain value. */
static srmech_status_t pm_frame_close(pm_state_t *st, pm_value_t **out)
{
    pm_frame_t *f = &st->fr[st->nfr - 1u];
    pm_value_t *last, *lv;
    uint32_t i;
    assert(st != NULL && out != NULL);
    assert(st->nfr > 0u && f->si == f->steps->u.arr.n);
    last = st->so[f->so_base + f->si - 1u];
    if (f->map_step == NULL) { *out = last; st->nfr--; return SRMECH_OK; }
    if (f->k >= f->n) { return SRMECH_ERR_INTERNAL; }
    f->acc[f->k] = last;
    f->k++;
    if (f->k < f->n) {                       /* next iteration, same frame  */
        for (i = 0u; i < f->si; i++) {
            assert(i < PM_MAX_STEPS);                  /* JPL Rule 2 bound */
            st->so[f->so_base + i] = NULL;
        }
        st->idx_val[f->idx_mark] = (int64_t)f->k;
        f->si = 0u;
        return SRMECH_OK;
    }
    lv = pm_new(st->b, PM_LIST);
    if (lv == NULL) { return SRMECH_ERR_OVERFLOW; }
    lv->items = f->acc; lv->n = f->n;
    st->idx_n = f->idx_mark; st->bnd_n = f->bnd_mark;
    st->nfr--;
    st->so[st->fr[st->nfr - 1u].so_base + f->map_si] = lv;
    st->fr[st->nfr - 1u].si++;
    return SRMECH_OK;
}

/* The trampoline. This is the whole of "no recursion": one bounded loop over
 * an explicit frame stack, where surface B re-enters its step runner. */
static srmech_status_t pm_run(pm_state_t *st, pm_value_t **out)
{
    uint32_t turns = 0u;
    srmech_status_t rc;
    assert(st != NULL && out != NULL);
    assert(st->nfr > 0u);
    while (st->nfr > 0u) {
        pm_frame_t *f = &st->fr[st->nfr - 1u];
        assert(turns < PM_MAX_TURNS);                  /* JPL Rule 2 bound */
        turns++;
        if (turns >= PM_MAX_TURNS) { return SRMECH_ERR_LIMIT; }
        rc = (f->si < f->steps->u.arr.n) ? pm_step_once(st)
                                         : pm_frame_close(st, out);
        if (rc != SRMECH_OK) { return rc; }
    }
    return SRMECH_OK;
}

/* ------------------------------------------------------------------
 * Driver.
 * ------------------------------------------------------------------ */

static unsigned char g_arena[PM_ARENA_BYTES];

/* Seed the root frame: `pre` supplies the step outputs of steps this prototype
 * does NOT claim, and the cursor starts past them. That is how the
 * klein4_from_one positive case RESUMES the shipped chain at its map step. */
static srmech_status_t pm_root_open(pm_state_t *st,
                                    const srmech_json_value_t *chain,
                                    const srmech_json_value_t *pre)
{
    const srmech_json_value_t *steps = srmech_json_object_get(chain, "steps");
    uint32_t i, np = 0u;
    assert(st != NULL && chain != NULL);
    assert(st->b != NULL);
    if (steps == NULL || steps->type != SRMECH_JSON_ARRAY ||
        steps->u.arr.n == 0u) { return SRMECH_ERR_BAD_INPUT; }
    if (steps->u.arr.n > PM_MAX_STEPS) { return SRMECH_ERR_LIMIT; }
    if (pre != NULL && pre->type == SRMECH_JSON_ARRAY) { np = pre->u.arr.n; }
    if (np >= steps->u.arr.n) { return SRMECH_ERR_BAD_INPUT; }
    for (i = 0u; i < np; i++) {
        assert(i < PM_MAX_STEPS);                      /* JPL Rule 2 bound */
        st->so[i] = pm_json(st->b, pre->u.arr.items[i]);
        if (st->so[i] == NULL) { return SRMECH_ERR_OVERFLOW; }
    }
    st->fr[0].steps = steps; st->fr[0].si = np; st->fr[0].so_base = 0u;
    st->fr[0].idx_mark = 0u; st->fr[0].bnd_mark = 0u;
    st->fr[0].map_step = NULL; st->fr[0].map_si = 0u;
    st->fr[0].k = 0u; st->fr[0].n = 0u; st->fr[0].acc = NULL;
    st->nfr = 1u; st->peak_frames = 1u;
    return SRMECH_OK;
}

typedef struct {
    pm_value_t *value;
    uint32_t    peak_frames;
    size_t      arena_used;
} pm_result_t;

/* Parse chain + ctx, run, report the final carrier plus the two numbers the
 * round-2 measurement needs: peak LIVE frames, and the arena high-water. */
static srmech_status_t pm_drive(const char *chain_json, const char *ctx_json,
                                size_t arena_bytes, pm_result_t *res)
{
    pm_bump_t b;                         /* the one arena cursor            */
    pm_state_t *st;
    srmech_json_value_t *chain = NULL; srmech_json_value_t *ctx = NULL;
    unsigned char *pa, *ca; srmech_status_t rc;
    assert(chain_json != NULL && ctx_json != NULL);
    assert(res != NULL && arena_bytes <= PM_ARENA_BYTES);
    res->value = NULL; res->peak_frames = 0u; res->arena_used = 0u;
    b.base = g_arena; b.cur = g_arena; b.end = g_arena + arena_bytes;
    st = (pm_state_t *)pm_carve(&b, sizeof(pm_state_t));
    pa = pm_carve(&b, PM_JSON_WS); ca = pm_carve(&b, PM_JSON_WS);
    if (st == NULL || pa == NULL || ca == NULL) { return SRMECH_ERR_OVERFLOW; }
    memset(st, 0, sizeof(*st));
    st->b = &b;
    rc = srmech_json_parse(chain_json, strlen(chain_json), pa,
                           PM_JSON_WS, &chain);
    if (rc != SRMECH_OK) { return rc; }
    rc = srmech_json_parse(ctx_json, strlen(ctx_json), ca, PM_JSON_WS, &ctx);
    if (rc != SRMECH_OK) { return rc; }
    st->row = srmech_json_object_get(ctx, "row");
    st->inputs = srmech_json_object_get(ctx, "inputs");
    rc = pm_root_open(st, chain, srmech_json_object_get(ctx, "pre"));
    if (rc != SRMECH_OK) { return rc; }
    rc = pm_run(st, &res->value);
    res->peak_frames = st->peak_frames;
    res->arena_used = (size_t)(b.cur - b.base);
    return rc;
}

/* ==================================================================
 * PROBES.
 * ================================================================== */

#include "_1653_proto_map_data.h"

/* --- POSITIVE 1: klein4_from_one's own map step, 64 crumbs -------- */

static int pm_case_klein4(void)
{
    pm_result_t res;
    srmech_status_t rc;
    uint32_t j; int bad = 0;
    assert(sizeof(PM_K4_EXPECT) == 64u * sizeof(int64_t));
    assert(PM_MAX_SEQ >= 64u);
    rc = pm_drive(PM_K4_CHAIN, PM_K4_CTX, PM_ARENA_BYTES, &res);
    printf("POSITIVE 1 — klein4_from_one variant=rest, its OWN map step\n");
    printf("  rc=%d  peak_frames=%u  arena_used=%zu bytes\n",
           (int)rc, res.peak_frames, res.arena_used);
    if (rc != SRMECH_OK || res.value == NULL || pm_len(res.value) != 64) {
        printf("  *** FAIL: no 64-element result\n\n");
        return 1;
    }
    for (j = 0u; j < 64u; j++) {
        pm_value_t *e; int64_t got = -1;
        assert(j < 64u);                                /* JPL Rule 2 bound */
        e = res.value->items[j];
        if (e == NULL || !pm_as_i64(e, &got) || got != PM_K4_EXPECT[j]) {
            bad++;
        }
    }
    printf("  crumbs matching the shipped Python projection: %d / 64  %s\n\n",
           64 - bad, (bad == 0) ? "MATCH" : "*** FAIL");
    return (bad == 0) ? 0 : 1;
}

/* --- POSITIVE 2: a NESTED map (depth 2 => 3 live frames) ---------- */

/* Outer map over @input.xs binding n; inner map over @bind.xs; the inner body
 * step is autocorrelation.toml's own inner body step VERBATIM:
 *   class = "I", op = "mod_add", args = {a = "@idx.i", b = "@idx.k",
 *                                       n = "@bind.n"}
 * Result[k][i] = (i + k) mod n — the layered-@idx read. */
static const char PM_N2_CHAIN[] =
    "{\"steps\":[{\"map_over\":\"@input.xs\",\"index\":\"k\","
    "\"bind\":{\"xs\":\"@input.xs\",\"n\":4},"
    "\"body\":[{\"map_over\":\"@bind.xs\",\"index\":\"i\","
    "\"body\":[{\"class\":\"I\",\"op\":\"mod_add\","
    "\"args\":{\"a\":\"@idx.i\",\"b\":\"@idx.k\",\"n\":\"@bind.n\"}}]}]}]}";
static const char PM_N2_CTX[] =
    "{\"row\":null,\"inputs\":{\"xs\":[0,1,2,3]}}";
/* MEASURED with srmech's own Class-I mod_add — see
 * _1653_map_groundtruth_rc444.ndjson record nested_map_mod_add_table. */
static const int64_t PM_N2_EXPECT[4][4] = {
    {0, 1, 2, 3}, {1, 2, 3, 0}, {2, 3, 0, 1}, {3, 0, 1, 2}
};

static int pm_case_nested2(void)
{
    pm_result_t res;
    srmech_status_t rc;
    uint32_t k, i; int bad = 0;
    assert(PM_MAX_FRAMES >= 3u);
    assert(sizeof(PM_N2_EXPECT) == 16u * sizeof(int64_t));
    rc = pm_drive(PM_N2_CHAIN, PM_N2_CTX, PM_ARENA_BYTES, &res);
    printf("POSITIVE 2 — NESTED map, depth 2 (autocorrelation's own inner "
           "body step)\n");
    printf("  rc=%d  peak_frames=%u  arena_used=%zu bytes\n",
           (int)rc, res.peak_frames, res.arena_used);
    if (rc != SRMECH_OK || res.value == NULL || pm_len(res.value) != 4) {
        printf("  *** FAIL: no 4-row result\n\n");
        return 1;
    }
    for (k = 0u; k < 4u; k++) {
        pm_value_t *row = res.value->items[k];
        assert(k < 4u);                                 /* JPL Rule 2 bound */
        if (row == NULL || pm_len(row) != 4) { bad += 4; continue; }
        for (i = 0u; i < 4u; i++) {
            int64_t got = -1;
            if (!pm_as_i64(row->items[i], &got) ||
                got != PM_N2_EXPECT[k][i]) { bad++; }
        }
    }
    printf("  cells matching srmech's Class-I mod_add: %d / 16  %s\n\n",
           16 - bad, (bad == 0) ? "MATCH" : "*** FAIL");
    return (bad == 0) ? 0 : 1;
}

/* --- POSITIVE 3: TRIPLE-nested map, the frame-cap BOUNDARY -------- */

/* SYNTHETIC, stated as such: the deepest SHIPPED map is depth 2, so this
 * exists only to prove the cap boundary behaves. Result[k][i][m] =
 * (m + k) mod 2 — independent of the middle index, which is the point: it
 * proves the MIDDLE frame's @idx is layered and skippable, not consumed. */
static const char PM_N3_CHAIN[] =
    "{\"steps\":[{\"map_over\":\"@input.xs\",\"index\":\"k\","
    "\"bind\":{\"xs\":\"@input.xs\",\"n\":2},"
    "\"body\":[{\"map_over\":\"@bind.xs\",\"index\":\"i\","
    "\"body\":[{\"map_over\":\"@bind.xs\",\"index\":\"m\","
    "\"body\":[{\"class\":\"I\",\"op\":\"mod_add\","
    "\"args\":{\"a\":\"@idx.m\",\"b\":\"@idx.k\",\"n\":\"@bind.n\"}}]}]}]}]}";
static const char PM_N3_CTX[] =
    "{\"row\":null,\"inputs\":{\"xs\":[0,1]}}";

static int pm_case_nested3(void)
{
    pm_result_t res;
    srmech_status_t rc;
    uint32_t k, i, m; int bad = 0;
    assert(PM_MAX_FRAMES >= 4u);
    assert(PM_MAX_ENV >= 3u);
    rc = pm_drive(PM_N3_CHAIN, PM_N3_CTX, PM_ARENA_BYTES, &res);
    printf("POSITIVE 3 — TRIPLE-nested map, depth 3 (frame-cap boundary)\n");
    printf("  rc=%d  peak_frames=%u (cap %u)  arena_used=%zu bytes\n",
           (int)rc, res.peak_frames, PM_MAX_FRAMES, res.arena_used);
    if (rc != SRMECH_OK || res.value == NULL || pm_len(res.value) != 2) {
        printf("  *** FAIL: no 2-row result\n\n");
        return 1;
    }
    for (k = 0u; k < 2u; k++) {
        pm_value_t *a = res.value->items[k];
        assert(k < 2u);                                 /* JPL Rule 2 bound */
        for (i = 0u; i < 2u && a != NULL && pm_len(a) == 2; i++) {
            pm_value_t *bb = a->items[i];
            for (m = 0u; m < 2u && bb != NULL && pm_len(bb) == 2; m++) {
                int64_t got = -1;
                if (!pm_as_i64(bb->items[m], &got) ||
                    got != (int64_t)((m + k) % 2u)) { bad++; }
            }
        }
    }
    printf("  cells matching (m + k) mod 2: %d / 8  %s\n\n",
           8 - bad, (bad == 0) ? "MATCH" : "*** FAIL");
    return (bad == 0) ? 0 : 1;
}

/* --- NEGATIVE probes: each MUST decline, with the stated status --- */

#define PM_NEG 12

static const char *const PM_NEG_CHAIN[PM_NEG] = {
    /* 0 — MIXED v1 + v2 keys on one step: the closed-key-set reject. rc444's
     * C parse ACCEPTS this shape and silently drops the v2 half. */
    "{\"steps\":[{\"class\":\"I\",\"op\":\"mod_add\",\"args\":{},"
    "\"map_over\":\"@input.xs\",\"body\":[]}]}",
    /* 1 — a map with no `body`: compose.py:667-672 requires map_over + body. */
    "{\"steps\":[{\"map_over\":\"@input.xs\",\"index\":\"k\"}]}",
    /* 2 — an EMPTY body array. */
    "{\"steps\":[{\"map_over\":\"@input.xs\",\"body\":[]}]}",
    /* 3 — map_over resolves to an INT: the unsized reject (compose.py:1301). */
    "{\"steps\":[{\"map_over\":\"@input.scalar\",\"index\":\"k\","
    "\"body\":[{\"class\":\"I\",\"op\":\"mod_add\","
    "\"args\":{\"a\":\"@idx.k\",\"b\":0,\"n\":4}}]}]}",
    /* 4 — @idx.q: no enclosing map binds q (compose.py:310-315). */
    "{\"steps\":[{\"map_over\":\"@input.xs\",\"index\":\"k\","
    "\"body\":[{\"class\":\"I\",\"op\":\"mod_add\","
    "\"args\":{\"a\":\"@idx.q\",\"b\":0,\"n\":4}}]}]}",
    /* 5 — @bind.nope: no enclosing map binds it (compose.py:316-322). */
    "{\"steps\":[{\"map_over\":\"@input.xs\",\"index\":\"k\","
    "\"body\":[{\"class\":\"E\",\"op\":\"seq_get\","
    "\"args\":{\"seq\":\"@bind.nope\",\"i\":0}}]}]}",
    /* 6 — a FLOAT in a body arg: the carrier has no float kind. */
    "{\"steps\":[{\"map_over\":\"@input.xs\",\"index\":\"k\","
    "\"body\":[{\"class\":\"I\",\"op\":\"mod_add\","
    "\"args\":{\"a\":\"@idx.k\",\"b\":0.5,\"n\":4}}]}]}",
    /* 7 — nesting one level DEEPER than the frame cap. */
    "{\"steps\":[{\"map_over\":\"@input.xs\",\"index\":\"k\","
    "\"bind\":{\"xs\":\"@input.xs\"},"
    "\"body\":[{\"map_over\":\"@bind.xs\",\"index\":\"i\","
    "\"body\":[{\"map_over\":\"@bind.xs\",\"index\":\"m\","
    "\"body\":[{\"map_over\":\"@bind.xs\",\"index\":\"p\","
    "\"body\":[{\"class\":\"I\",\"op\":\"mod_add\","
    "\"args\":{\"a\":\"@idx.p\",\"b\":0,\"n\":2}}]}]}]}]}]}",
    /* 8 — a body op outside the closed 6-op table. */
    "{\"steps\":[{\"map_over\":\"@input.xs\",\"index\":\"k\","
    "\"body\":[{\"class\":\"L\",\"op\":\"srmech.cascade.composites."
    "correlation_product\",\"args\":{\"i\":\"@idx.k\"}}]}]}",
    /* 9 — @catalog in map_over: a namespace the C runner does not resolve. */
    "{\"steps\":[{\"map_over\":\"@catalog.thing\",\"index\":\"k\","
    "\"body\":[{\"class\":\"I\",\"op\":\"mod_add\","
    "\"args\":{\"a\":\"@idx.k\",\"b\":0,\"n\":4}}]}]}",
    /* 10 — seq_get index out of range: Python raises IndexError. */
    "{\"steps\":[{\"map_over\":\"@input.xs\",\"index\":\"k\","
    "\"bind\":{\"t\":[7,8]},"
    "\"body\":[{\"class\":\"E\",\"op\":\"seq_get\","
    "\"args\":{\"seq\":\"@bind.t\",\"i\":\"@idx.k\"}}]}]}",
    /* 11 — a FORWARD @step reference inside a body. */
    "{\"steps\":[{\"map_over\":\"@input.xs\",\"index\":\"k\","
    "\"body\":[{\"class\":\"I\",\"op\":\"mod_add\","
    "\"args\":{\"a\":\"@step[1].output\",\"b\":0,\"n\":4}},"
    "{\"class\":\"I\",\"op\":\"mod_add\","
    "\"args\":{\"a\":\"@idx.k\",\"b\":0,\"n\":4}}]}]}"
};
static const srmech_status_t PM_NEG_WANT[PM_NEG] = {
    SRMECH_ERR_BAD_INPUT, SRMECH_ERR_BAD_INPUT, SRMECH_ERR_BAD_INPUT,
    SRMECH_ERR_BAD_INPUT, SRMECH_ERR_BAD_INPUT, SRMECH_ERR_BAD_INPUT,
    SRMECH_ERR_NOT_IMPL,  SRMECH_ERR_NOT_IMPL,  SRMECH_ERR_NOT_IMPL,
    SRMECH_ERR_NOT_IMPL,  SRMECH_ERR_BAD_INPUT, SRMECH_ERR_BAD_INPUT
};
static const char *const PM_NEG_WHAT[PM_NEG] = {
    "mixed v1+v2 step (closed-key-set reject)",
    "map with no `body`",
    "map with an EMPTY body",
    "map_over resolves to an INT (unsized reject)",
    "@idx.q — no enclosing map binds it",
    "@bind.nope — no enclosing map binds it",
    "float in a body arg (no FLOAT carrier kind)",
    "nesting one level past the frame cap",
    "body op outside the closed 6-op table",
    "@catalog namespace in map_over",
    "seq_get index out of range",
    "forward @step reference inside a body"
};

static int pm_case_negatives(void)
{
    static const char ctx[] =
        "{\"row\":null,\"inputs\":{\"xs\":[0,1,2,3],\"scalar\":7}}";
    uint32_t i; int bad = 0;
    assert(PM_NEG == 12);
    assert(sizeof(PM_NEG_WANT) / sizeof(PM_NEG_WANT[0]) == (size_t)PM_NEG);
    printf("NEGATIVE — every one must DECLINE, with the stated status\n");
    for (i = 0u; i < (uint32_t)PM_NEG; i++) {
        pm_result_t res;
        srmech_status_t rc;
        assert(i < (uint32_t)PM_NEG);                   /* JPL Rule 2 bound */
        rc = pm_drive(PM_NEG_CHAIN[i], ctx, PM_ARENA_BYTES, &res);
        if (rc != PM_NEG_WANT[i]) { bad++; }
        printf("  [%2u] rc=%d (want %d)  %-44s %s\n", i, (int)rc,
               (int)PM_NEG_WANT[i], PM_NEG_WHAT[i],
               (rc == PM_NEG_WANT[i]) ? "OK" : "*** FAIL");
    }
    printf("  %d of %d declined as stated\n\n", PM_NEG - bad, PM_NEG);
    return bad;
}

/* --- POSITIVE 4: the ARENA SWEEP -------------------------------- */

/* Build the depth-2 nested chain + ctx for a given n, so the arena growth law
 * is MEASURED across n rather than asserted. */
static int pm_build_n2(char *chain, size_t ccap, char *ctx, size_t xcap,
                       uint32_t n)
{
    size_t at = 0u; uint32_t i; int w;
    assert(chain != NULL && ctx != NULL);
    assert(n >= 1u && n <= PM_MAX_SEQ);
    w = snprintf(chain, ccap,
                 "{\"steps\":[{\"map_over\":\"@input.xs\",\"index\":\"k\","
                 "\"bind\":{\"xs\":\"@input.xs\",\"n\":%u},"
                 "\"body\":[{\"map_over\":\"@bind.xs\",\"index\":\"i\","
                 "\"body\":[{\"class\":\"I\",\"op\":\"mod_add\","
                 "\"args\":{\"a\":\"@idx.i\",\"b\":\"@idx.k\","
                 "\"n\":\"@bind.n\"}}]}]}]}", n);
    if (w < 0 || (size_t)w >= ccap) { return 0; }
    w = snprintf(ctx, xcap, "{\"row\":null,\"inputs\":{\"xs\":[");
    if (w < 0 || (size_t)w >= xcap) { return 0; }
    at = (size_t)w;
    for (i = 0u; i < n; i++) {
        assert(i < PM_MAX_SEQ);                         /* JPL Rule 2 bound */
        w = snprintf(ctx + at, xcap - at, "%s%u", (i == 0u) ? "" : ",", i);
        if (w < 0 || (size_t)w >= (xcap - at)) { return 0; }
        at += (size_t)w;
    }
    w = snprintf(ctx + at, xcap - at, "]}}");
    return (w > 0 && (size_t)w < (xcap - at)) ? 1 : 0;
}

static char g_chain[1024];
static char g_ctx[32768];

static int pm_case_arena_sweep(void)
{
    static const uint32_t NS[7] = {4u, 8u, 16u, 32u, 64u, 128u, 256u};
    uint32_t s; int bad = 0;
    assert(sizeof(NS) / sizeof(NS[0]) == 7u);
    assert(PM_MAX_SEQ >= 256u);
    printf("POSITIVE 4 — arena sweep on the depth-2 nested map "
           "(n outer x n inner)\n");
    printf("      n   rc   peak_frames   arena_used   bytes/cell\n");
    for (s = 0u; s < 7u; s++) {
        pm_result_t res;
        srmech_status_t rc;
        uint32_t n = NS[s];
        assert(s < 7u);                                 /* JPL Rule 2 bound */
        if (!pm_build_n2(g_chain, sizeof(g_chain), g_ctx, sizeof(g_ctx), n)) {
            printf("   %4u   build-failed\n", n);
            bad++;
            continue;
        }
        rc = pm_drive(g_chain, g_ctx, PM_ARENA_BYTES, &res);
        if (rc != SRMECH_OK || res.value == NULL ||
            pm_len(res.value) != (int64_t)n) { bad++; }
        printf("   %4u   %2d   %11u   %10zu   %10zu\n", n, (int)rc,
               res.peak_frames, res.arena_used,
               res.arena_used / (size_t)(n * n));
    }
    printf("  %s\n\n", (bad == 0) ? "all n ran" : "*** FAIL");
    return bad;
}

/* --- the arena CROSSOVER: the smallest total arena that runs n --- */

static size_t pm_min_arena(uint32_t n)
{
    size_t lo = 1u << 18, hi = PM_ARENA_BYTES, mid;
    uint32_t guard = 0u;
    assert(n >= 1u && n <= PM_MAX_SEQ);
    assert(hi > lo);
    while (lo < hi) {
        pm_result_t res;
        assert(guard < 64u);                            /* JPL Rule 2 bound */
        guard++;
        if (guard >= 64u) { return 0u; }
        mid = lo + ((hi - lo) / 2u);
        if (!pm_build_n2(g_chain, sizeof(g_chain), g_ctx, sizeof(g_ctx), n)) {
            return 0u;
        }
        if (pm_drive(g_chain, g_ctx, mid, &res) == SRMECH_OK) { hi = mid; }
        else { lo = mid + 1u; }
    }
    return lo;
}

static int pm_case_crossover(void)
{
    static const uint32_t NS[4] = {32u, 64u, 128u, 256u};
    uint32_t s; int bad = 0;
    assert(sizeof(NS) / sizeof(NS[0]) == 4u);
    assert(PM_ARENA_BYTES > (1u << 18));
    printf("POSITIVE 4b — minimum TOTAL arena that runs the depth-2 map\n");
    printf("      n   min_arena_bytes\n");
    for (s = 0u; s < 4u; s++) {
        size_t mn;
        assert(s < 4u);                                 /* JPL Rule 2 bound */
        mn = pm_min_arena(NS[s]);
        if (mn == 0u) { bad++; }
        printf("   %4u   %15zu\n", NS[s], mn);
    }
    printf("  (%u bytes of that is fixed: state + two %u-byte JSON "
           "workspaces)\n\n",
           (unsigned)(sizeof(pm_state_t) + 2u * PM_JSON_WS),
           (unsigned)PM_JSON_WS);
    return bad;
}

int main(void)
{
    int fails = 0;
    assert(PM_MAX_FRAMES >= 3u);
    assert(PM_ARENA_BYTES > 2u * PM_JSON_WS);
    printf("srmech %s  ABI %d  — #1653 surface-A MAP step-form prototype\n",
           srmech_version(), (int)srmech_abi_version());
    printf("explicit frame stack, cap %u frames; no recursion\n\n",
           PM_MAX_FRAMES);
    fails += pm_case_klein4();
    fails += pm_case_nested2();
    fails += pm_case_nested3();
    fails += pm_case_negatives();
    fails += pm_case_arena_sweep();
    fails += pm_case_crossover();
    printf("%d failure(s)\n", fails);
    return (fails == 0) ? 0 : 1;
}
