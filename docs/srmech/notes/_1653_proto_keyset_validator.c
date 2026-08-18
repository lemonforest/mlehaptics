/* _1653_proto_keyset_validator.c — gh #1653 `#T1146` PROTOTYPE: the CLOSED-KEY-SET
 * validator the C DSL stage surface does not have. Standalone, JPL Power-of-Ten clean.
 *
 * WHAT IT CLOSES. Round 1 measured 24 of 34 probes where the C leaf path silently
 * ACCEPTS AND COMPUTES a stage Python REJECTS
 * (docs/srmech/notes/_1653_t1146_rejection_parity_rc444.ndjson). Both halves of the
 * root cause are read from source:
 *   - dsl/_chain.py:111-124 `_then_native_desc` gates on VALUE TYPE
 *     (`_is_c_scalar`) and copies every scalar kwarg into the stage dict with its
 *     NAME UNCHECKED. There is no KEY-NAME gate on that path.
 *   - srmech_dsl_chain_run.c:537-565 `dsl_leaf_dispatch` reads the keys it WANTS
 *     (`orientation`, `max_denominator`, `fine_scale`) and never asks what OTHER
 *     keys the stage carries. A REQUIRED-key read is not a CLOSED-key-set check.
 * Round 1 also measured that the two apparently clean ops (cyclic_gcd,
 * pin_slot_at_zero) reject only INCIDENTALLY — they fall back to Python. So there
 * is no in-tree pattern to copy, and this file is the missing mechanism.
 *
 * THE MECHANISM. A stage is accepted iff every key it carries is either a
 * STRUCTURAL key of its form (`op` for a leaf; `fold_init`/`fold_op`/`fold_args`
 * for a fold; `reduce_op`; `map_op`) or a DECLARED parameter of its op BEYOND the
 * positionals the runner itself supplies. That PIPED COUNT is form-dependent and
 * measured, not assumed:
 *   leaf   `.then(op, **kw)`        -> op_fn(value, **kw)          piped = 1
 *   fold   `.fold(init, op, **kw)`  -> body(acc, elem, **kw)       piped = 2
 *   reduce `.reduce(op, **kw)`      -> body(acc, elem, **kw)       piped = 2
 *   map    `.map_indexed(op, **kw)` -> body(input_seq, k, **kw)    piped = 2
 * A stage naming a piped operand is Python's "got multiple values for argument"
 * reject — measured on all four forms, and the leaf case
 * (`.then('magnitude', x=3)` -> C returns 3.5) is a 25th defect round 1 did not
 * probe. A validator that skipped only the first parameter would accept
 * `fold(1,'cyclic_gcd', b=5)`, which Python rejects.
 *
 * WHERE THE KEY SET COMES FROM — the load-bearing part. NOT a hand-written C
 * table: the parameter names are READ AT RUNTIME from the already-shipped
 * `srmech_tool_registry_find()->params[]`. That table is GENERATED from
 * `srmech.introspect.tool_schema` by c/tools/gen_tool_registry.py (driven by
 * tools/regen_all.py + codegen_manifest.py), and the Python side it is generated
 * from is pinned to the live callable signature in BOTH directions by two ratchets
 * that are green on this worktree at rc444 (measured, 5 passed in 0.97s):
 *   tests/test_mcp.py::test_schema_signature_alignment_no_drift   (declared subset of real)
 *   tests/test_declared_param_completeness_rc408.py               (declared superset of real)
 * Together they make the registry's parameter-name set EQUAL to
 * inspect.signature's, so reading it in C cannot drift from the Python reject.
 * Measured agreement over all 9 C-named leaf/body ops: 9/9 on names, 9/9 on the
 * `required` flag, and the C-side defaults in leaf_best_rational (100, 1000000)
 * equal Python's DEFAULT_MAX_DENOMINATOR / DEFAULT_FINE_SCALE.
 *
 * THE ONE NEW DATUM is the op-name -> registry-name LINK (KS_LINK below). It is
 * needed because no string rule derives it: the registry uses the PUBLIC
 * re-export path (`srmech.cascade.reorient`) while chain descriptors write
 * submodule paths (`srmech.cascade.atoms.reorient`) or class-scoped bare names
 * (`gcd`, `mod_add`). MEASURED over the 48 op names the 21 shipped descriptors
 * reference: a "prefix with srmech.cascade." rule resolves 2/48; resolving in
 * PYTHON by callable identity resolves 35/48 (the 10 remaining bare names need
 * the step's `class` too, and 3 dotted names have no registry entry at all). So
 * the link belongs in a GENERATED artifact or under a source-parsing bijection
 * ratchet — see the DESIGN NOTE at the end of this file. The KEY NAMES are never
 * copied, only the identity of the row to read them from.
 *
 * The link table doubles as a CLOSED OP-NAME set, which closes round 1's
 * divergence D3 as a side effect: `seq_get` bare is matched by C's
 * dsl_map_body_is_seq_get but is NOT a name `lookup_cascade_op` accepts
 * (measured: ValueError "unknown cascade op 'seq_get'"; the dotted
 * `srmech.cascade.leaves.seq_get` is what resolves). The link table must
 * therefore be generated from what PYTHON accepts, never from what the C
 * matcher accepts, or it re-opens that divergence.
 *
 * WHY REJECT == DEFER. A rejected stage returns SRMECH_ERR_NOT_IMPL, not
 * BAD_INPUT: deferring hands the call to Python, which raises the authoritative
 * TypeError with its exact text. That is how the two incidentally-clean ops
 * already achieve byte-identical messages, and it means this gate needs no error
 * strings of its own. The VERDICT enum keeps the reason legible for a caller that
 * wants it; the STATUS stays the rc103 inform-don't-limit defer.
 *
 * BUILD (one line; no continuation — a trailing backslash in a comment trips the
 * Rule 8 ratchet, which does not strip comments):
 *   cc -std=c99 -Wall -Wextra -Wpedantic -O2 -Iinclude ../notes/_1653_proto_keyset_validator.c build/libsrmech.a -o /tmp/proto_keyset
 * then run /tmp/proto_keyset  (exit 0 == every probe matched its measured Python verdict)
 *
 * JPL Power-of-Ten: no malloc (two file-scope arenas), no recursion, no goto,
 * every function <= 60 lines with >= 2 asserts, every loop explicitly bounded and
 * asserted, no libm, every srmech_* return checked. Sign handling never uses the
 * ALU idiom — a real magnitude is the Class-K pin-slot op called by name.
 *
 * NOT A SHIP. Nothing here edits c/src/ or c/include/. The rcN owner lifts
 * ks_entry_for / ks_key_is_declared / ks_keys_closed / ks_required_present /
 * ks_check_stage into srmech_dsl_chain_run.c as the first thing
 * dsl_leaf_dispatch and dsl_run_combinator do.
 */

#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <time.h>

#include "srmech.h"

/* Bounds (JPL Rule 2 — every loop has an explicit compiled cap). */
#define KS_MAX_KEYS   64u         /* keys inspected on one stage object   */
#define KS_MAX_PARAMS 32u         /* declared params inspected per op     */
#define KS_MAX_OPL    96u         /* longest stage op string accepted     */
#define KS_ARENA      (1u << 16)  /* the one JSON workspace               */
#define KS_JSON_CAP   256u        /* probe stage-JSON staging buffer      */

typedef enum {
    KS_ACCEPT = 0,
    KS_REJECT_UNDECLARED_KEY = 1,   /* a key no structural slot / param owns */
    KS_REJECT_MISSING_REQUIRED = 2, /* a required declared param absent      */
    KS_UNKNOWN_OP = 3,              /* not linked for this ROLE              */
    KS_DEFER_NAMED_BIND = 4         /* fold_args rebinds: piped count is data */
} ks_verdict_t;

/* The ROLE a stage plays. A leaf `op` and a fold/reduce/map BODY are different
 * name spaces (see the D3 note in the header), so a single flat name set would
 * accept a body-only name as a leaf and lose that reject. */
#define KS_ROLE_LEAF 1u
#define KS_ROLE_BODY 2u

/* ------------------------------------------------------------------
 * The stage FORM table — structural keys + piped-positional count per form.
 * Mirrors dsl/_toml_chain.py:_RESERVED_STAGE_KEYS and the C dispatcher's own
 * discriminator array (srmech_dsl_chain_run.c:636-638). Widening either side
 * must move both; tests/test_combinator_kernel_closure.py
 * ::test_c_discriminator_table_matches_python is the existing ratchet shape
 * for exactly that bijection.
 * ------------------------------------------------------------------ */

typedef struct {
    const char        *label;
    const char        *op_key;       /* where the op NAME lives             */
    const char *const *struct_keys;  /* keys the FORM itself owns           */
    uint32_t           nstruct;
    uint32_t           piped;        /* positionals the runner supplies     */
    unsigned           role;
} ks_form_t;

#define KS_FORM_LEAF   0u
#define KS_FORM_FOLD   1u
#define KS_FORM_REDUCE 2u
#define KS_FORM_MAP    3u
#define KS_FORM_N      4u

static const char *const KS_SK_LEAF[1]   = { "op" };
static const char *const KS_SK_FOLD[3]   = { "fold_init", "fold_op", "fold_args" };
static const char *const KS_SK_REDUCE[1] = { "reduce_op" };
static const char *const KS_SK_MAP[1]    = { "map_op" };

static const ks_form_t KS_FORM[KS_FORM_N] = {
    { "leaf",   "op",        KS_SK_LEAF,   1u, 1u, KS_ROLE_LEAF },
    { "fold",   "fold_op",   KS_SK_FOLD,   3u, 2u, KS_ROLE_BODY },
    { "reduce", "reduce_op", KS_SK_REDUCE, 1u, 2u, KS_ROLE_BODY },
    { "map",    "map_op",    KS_SK_MAP,    1u, 2u, KS_ROLE_BODY }
};

/* ------------------------------------------------------------------
 * The op-name -> registry-name LINK. The ONLY hand-written datum here, and it
 * carries NO key names — just the identity of the registry row whose params[]
 * are read at runtime. Rows cover srmech_dsl_chain_run.c:537-565's
 * dsl_leaf_dispatch plus the binary/map body names, spelled the way
 * lookup_cascade_op accepts them (measured).
 * ------------------------------------------------------------------ */

typedef struct {
    const char *stage_op;       /* the name as a stage / descriptor writes it */
    const char *registry_name;  /* the srmech_tool_registry_find key          */
    unsigned    roles;          /* KS_ROLE_LEAF | KS_ROLE_BODY                */
} ks_link_t;

#define KS_LINK_N 10u

static const ks_link_t KS_LINK[KS_LINK_N] = {
    { "magnitude",            "srmech.cascade.magnitude",            KS_ROLE_LEAF },
    { "reorient",             "srmech.cascade.reorient",             KS_ROLE_LEAF },
    { "pin_slot_at_zero",     "srmech.cascade.pin_slot_at_zero",     KS_ROLE_LEAF },
    { "best_rational_signed", "srmech.cascade.best_rational_signed", KS_ROLE_LEAF },
    { "chiral_flip",          "srmech.cascade.chiral_flip",          KS_ROLE_LEAF },
    { "net_chirality",        "srmech.cascade.net_chirality",        KS_ROLE_LEAF },
    { "autocorrelation",      "srmech.cascade.autocorrelation",      KS_ROLE_LEAF },
    /* cyclic_gcd is BOTH: the C-backed fold/reduce binary body, and a legal
     * catalog leaf in Python (`.then('cyclic_gcd', b=18)` -> 6). The C leaf
     * table has no kernel for it, so a leaf stage still defers — but for a
     * MISSING KERNEL, not an invalid declaration. Different reasons, and the
     * verdict enum keeps them apart. */
    { "cyclic_gcd",           "srmech.cascade.cyclic_gcd",           KS_ROLE_LEAF | KS_ROLE_BODY },
    /* Body-only names, in the DOTTED spelling Python resolves. The bare
     * spellings `seq_get` / `orientation_compose` are deliberately ABSENT:
     * lookup_cascade_op rejects them (measured), and C's own matchers accept
     * bare — the D3 divergence this table closes. */
    { "srmech.cascade.leaves.seq_get",
      "srmech.cascade.seq_get",             KS_ROLE_BODY },
    { "srmech.cascade.leaves.orientation_compose",
      "srmech.cascade.orientation_compose", KS_ROLE_BODY }
};

/* ------------------------------------------------------------------
 * PIECE 1 — resolve a stage op name (bounded, length-delimited) to its
 * registry entry for the requested ROLE.
 * ------------------------------------------------------------------ */

static const ks_link_t *ks_link_for(const char *op, uint32_t opl, unsigned role)
{
    uint32_t i;
    assert(op != NULL);
    assert(role == KS_ROLE_LEAF || role == KS_ROLE_BODY);
    if (opl == 0u || opl > KS_MAX_OPL) { return NULL; }
    for (i = 0u; i < KS_LINK_N; i++) {
        const char *nm = KS_LINK[i].stage_op;
        assert(i < KS_LINK_N);                         /* JPL Rule 2 bound  */
        if (strlen(nm) == (size_t)opl && memcmp(nm, op, (size_t)opl) == 0) {
            return ((KS_LINK[i].roles & role) != 0u) ? &KS_LINK[i] : NULL;
        }
    }
    return NULL;
}

/* The registry row for `op` in `role`, or NULL. A linked name whose registry
 * row is MISSING is a codegen-drift alarm, not a silent pass: the caller
 * reports it (ks_report_link_health) and the verdict stays UNKNOWN_OP. */
static const srmech_tool_entry_t *ks_entry_for(const char *op, uint32_t opl,
                                               unsigned role)
{
    const ks_link_t *lk = ks_link_for(op, opl, role);
    assert(op != NULL);
    assert(role != 0u);
    if (lk == NULL) { return NULL; }
    return srmech_tool_registry_find(lk->registry_name);
}

/* ------------------------------------------------------------------
 * PIECE 2 — is `key` a declared parameter BEYOND the piped positionals?
 * ------------------------------------------------------------------ */

static int ks_key_is_declared(const srmech_tool_entry_t *e, const char *key,
                              uint32_t piped)
{
    uint32_t i, n;
    assert(e != NULL && key != NULL);
    assert(piped >= 1u && piped <= 2u);
    n = e->param_count;
    if (n > KS_MAX_PARAMS) { n = KS_MAX_PARAMS; }      /* JPL Rule 2 clamp  */
    for (i = piped; i < n; i++) {
        const char *pn = e->params[i].name;
        assert(i < KS_MAX_PARAMS);
        if (pn != NULL && strcmp(pn, key) == 0) { return 1; }
    }
    return 0;
}

/* 1 iff `key` is one of the form's own structural keys. */
static int ks_key_is_structural(const ks_form_t *f, const char *key)
{
    uint32_t i;
    assert(f != NULL && key != NULL);
    assert(f->nstruct >= 1u && f->nstruct <= 3u);
    for (i = 0u; i < f->nstruct; i++) {
        assert(i < 3u);                                /* JPL Rule 2 bound  */
        if (strcmp(f->struct_keys[i], key) == 0) { return 1; }
    }
    return 0;
}

/* ------------------------------------------------------------------
 * PIECE 3 — the closed-key-set check over one parsed stage object.
 * ------------------------------------------------------------------ */

/* Every key present must be structural for the form, or declared beyond the
 * piped positionals. `*bad` names the first offender (borrowed from the parsed
 * tree; never freed). */
static ks_verdict_t ks_keys_closed(const srmech_tool_entry_t *e,
                                   const ks_form_t *f,
                                   const srmech_json_value_t *stage,
                                   const char **bad)
{
    uint32_t i, n;
    assert(e != NULL && f != NULL);
    assert(stage != NULL && bad != NULL);
    if (stage->type != SRMECH_JSON_OBJECT) { return KS_REJECT_UNDECLARED_KEY; }
    n = stage->u.obj.n;
    if (n > KS_MAX_KEYS) { return KS_REJECT_UNDECLARED_KEY; }
    for (i = 0u; i < n; i++) {
        const char *k = stage->u.obj.keys[i];
        assert(i < KS_MAX_KEYS);                       /* JPL Rule 2 bound  */
        if (k == NULL) { return KS_REJECT_UNDECLARED_KEY; }
        if (ks_key_is_structural(f, k)) { continue; }
        if (!ks_key_is_declared(e, k, f->piped)) {
            *bad = k;
            return KS_REJECT_UNDECLARED_KEY;
        }
    }
    return KS_ACCEPT;
}

/* Every declared param beyond the piped positionals that is marked required
 * must be present on the stage. */
static ks_verdict_t ks_required_present(const srmech_tool_entry_t *e,
                                        const ks_form_t *f,
                                        const srmech_json_value_t *stage,
                                        const char **bad)
{
    uint32_t i, n;
    assert(e != NULL && f != NULL);
    assert(stage != NULL && bad != NULL);
    n = e->param_count;
    if (n > KS_MAX_PARAMS) { n = KS_MAX_PARAMS; }
    for (i = f->piped; i < n; i++) {
        const srmech_tool_param_t *p = &e->params[i];
        assert(i < KS_MAX_PARAMS);
        if (p->required == 0 || p->name == NULL) { continue; }
        if (srmech_json_object_get(stage, p->name) == NULL) {
            *bad = p->name;
            return KS_REJECT_MISSING_REQUIRED;
        }
    }
    return KS_ACCEPT;
}

/* The whole gate for one stage in one form. This is what dsl_leaf_dispatch and
 * dsl_run_combinator should call FIRST, before any kernel runs. */
static ks_verdict_t ks_check_stage(uint32_t form_idx,
                                   const srmech_json_value_t *stage,
                                   const char **bad)
{
    const ks_form_t *f;
    const srmech_json_value_t *opn;
    const srmech_tool_entry_t *e;
    ks_verdict_t v;
    assert(stage != NULL && bad != NULL);
    assert(form_idx < KS_FORM_N);
    f = &KS_FORM[form_idx];
    *bad = "";
    if (form_idx == KS_FORM_FOLD &&
        srmech_json_object_get(stage, "fold_args") != NULL) {
        return KS_DEFER_NAMED_BIND;      /* arg_names rebinds the positionals */
    }
    opn = srmech_json_object_get(stage, f->op_key);
    if (opn == NULL || opn->type != SRMECH_JSON_STRING) { return KS_UNKNOWN_OP; }
    e = ks_entry_for(opn->u.str.ptr, opn->u.str.len, f->role);
    if (e == NULL) { return KS_UNKNOWN_OP; }
    if (e->param_count < f->piped) { return KS_UNKNOWN_OP; }  /* arity mismatch */
    v = ks_keys_closed(e, f, stage, bad);
    if (v != KS_ACCEPT) { return v; }
    return ks_required_present(e, f, stage, bad);
}

/* A rejected stage DEFERS (rc103 inform-don't-limit) so Python raises the
 * authoritative TypeError / ValueError text. See the file header. */
static srmech_status_t ks_verdict_status(ks_verdict_t v)
{
    assert(v >= KS_ACCEPT);
    assert(v <= KS_DEFER_NAMED_BIND);
    return (v == KS_ACCEPT) ? SRMECH_OK : SRMECH_ERR_NOT_IMPL;
}

static const char *ks_verdict_name(ks_verdict_t v)
{
    assert(v >= KS_ACCEPT);
    assert(v <= KS_DEFER_NAMED_BIND);
    if (v == KS_ACCEPT) { return "ACCEPT"; }
    if (v == KS_REJECT_UNDECLARED_KEY) { return "REJECT(undeclared key)"; }
    if (v == KS_REJECT_MISSING_REQUIRED) { return "REJECT(missing required)"; }
    if (v == KS_UNKNOWN_OP) { return "DEFER(op not linked for role)"; }
    return "DEFER(fold_args named bind)";
}

/* ------------------------------------------------------------------
 * Driver.
 * ------------------------------------------------------------------ */

static unsigned char g_arena[KS_ARENA];

/* Parse one stage JSON string into the arena and run the gate. */
static ks_verdict_t ks_drive(const char *stage_json, uint32_t form_idx,
                             const char **bad, srmech_status_t *parse_st)
{
    srmech_json_value_t *stage = NULL;
    srmech_status_t st;
    assert(stage_json != NULL && bad != NULL);
    assert(parse_st != NULL && form_idx < KS_FORM_N);
    st = srmech_json_parse(stage_json, strlen(stage_json), g_arena,
                           sizeof(g_arena), &stage);
    *parse_st = st;
    if (st != SRMECH_OK) { return KS_UNKNOWN_OP; }
    return ks_check_stage(form_idx, stage, bad);
}

/* Section 0 — LINK HEALTH. Every linked name must resolve to a registry row
 * with >= 1 declared param, else the generated table drifted from the link. */
static int ks_report_link_health(void)
{
    uint32_t i, j;
    int bad = 0;
    printf("SECTION 0 — link health (the key names are READ, never copied)\n");
    for (i = 0u; i < KS_LINK_N; i++) {
        const srmech_tool_entry_t *e =
            srmech_tool_registry_find(KS_LINK[i].registry_name);
        assert(i < KS_LINK_N);
        assert(KS_LINK[i].registry_name != NULL);
        if (e == NULL || e->param_count == 0u) { bad++; }
        printf("  %-44s params=", KS_LINK[i].stage_op);
        if (e == NULL) { printf("*** NO REGISTRY ROW (codegen drift)\n"); continue; }
        for (j = 0u; j < e->param_count && j < KS_MAX_PARAMS; j++) {
            printf("%s%s", e->params[j].name,
                   (e->params[j].required != 0) ? "!" : "?");
            if ((j + 1u) < e->param_count) { printf(","); }
        }
        printf("  roles=%s%s\n",
               ((KS_LINK[i].roles & KS_ROLE_LEAF) != 0u) ? "leaf" : "",
               ((KS_LINK[i].roles & KS_ROLE_BODY) != 0u) ? "+body" : "");
    }
    printf("  registry rows: %lu ; link rows: %u ; broken links: %d\n"
           "  ('!' = required, '?' = optional; the leading params are the PIPED\n"
           "   positionals the runner supplies, never stage keys)\n\n",
           (unsigned long)srmech_tool_registry_count(), (unsigned)KS_LINK_N, bad);
    return bad;
}

/* The 5 round-1 defective ops with their round-1 bogus kwargs. `base` is the
 * op's VALID kwarg text, so a probe isolates the bogus key. */
typedef struct { const char *op; const char *base; } ks_defop_t;

static const ks_defop_t KS_DEFOPS[5] = {
    { "magnitude",       "" },
    { "reorient",        ",\"orientation\":-1" },
    { "chiral_flip",     "" },
    { "net_chirality",   "" },
    { "autocorrelation", "" }
};
static const char *const KS_BOGUS[5] = {
    "bogus", "nonexistent_kwarg", "max_denominator", "orientation", "index"
};

/* Section 1 — the 24 round-1 DEFECT probes: every one must now REJECT. */
static int ks_run_defect_probes(void)
{
    uint32_t o, g;
    int fails = 0, run = 0;
    printf("SECTION 1 — the 24 round-1 DEFECT probes (C computed a value; Python raised)\n");
    for (o = 0u; o < 5u; o++) {
        for (g = 0u; g < 5u; g++) {
            char js[KS_JSON_CAP];
            const char *bad = ""; srmech_status_t pst; ks_verdict_t v; int nw;
            assert(o < 5u && g < 5u);                  /* JPL Rule 2 bound  */
            if (strcmp(KS_DEFOPS[o].op, "reorient") == 0 &&
                strcmp(KS_BOGUS[g], "orientation") == 0) { continue; }
            nw = snprintf(js, sizeof(js), "{\"op\":\"%s\"%s,\"%s\":1}",
                          KS_DEFOPS[o].op, KS_DEFOPS[o].base, KS_BOGUS[g]);
            assert(nw > 0 && (size_t)nw < sizeof(js));
            v = ks_drive(js, KS_FORM_LEAF, &bad, &pst);
            run++;
            if (pst != SRMECH_OK || v != KS_REJECT_UNDECLARED_KEY) { fails++; }
            printf("  [%02d] %-16s +%-18s %-26s rc=%d bad=%-18s %s\n",
                   run, KS_DEFOPS[o].op, KS_BOGUS[g], ks_verdict_name(v),
                   (int)ks_verdict_status(v), bad,
                   (v == KS_REJECT_UNDECLARED_KEY) ? "OK" : "*** FAIL");
        }
    }
    printf("  probes run: %d (round 1 measured 24)  failures: %d\n\n", run, fails);
    return fails + ((run == 24) ? 0 : 1);
}

/* Section 2 — POSITIVE controls. A validator that rejects everything is not a
 * fix. Every row is a call MEASURED to succeed on both projections at rc444. */
#define KS_POS_N 11u
static const char *const KS_POS[KS_POS_N] = {
    "{\"op\":\"magnitude\"}",
    "{\"op\":\"reorient\",\"orientation\":-1}",
    "{\"op\":\"reorient\",\"orientation\":1}",
    "{\"op\":\"pin_slot_at_zero\"}",
    "{\"op\":\"chiral_flip\"}",
    "{\"op\":\"net_chirality\"}",
    "{\"op\":\"autocorrelation\"}",
    "{\"op\":\"best_rational_signed\"}",
    "{\"op\":\"best_rational_signed\",\"max_denominator\":10}",
    "{\"op\":\"best_rational_signed\",\"max_denominator\":10,\"fine_scale\":1000000}",
    "{\"op\":\"cyclic_gcd\",\"b\":18}"
};

static int ks_run_positive_controls(void)
{
    uint32_t i;
    int fails = 0;
    printf("SECTION 2 — POSITIVE controls: valid leaf stages must still be ACCEPTED\n");
    for (i = 0u; i < KS_POS_N; i++) {
        const char *bad = ""; srmech_status_t pst;
        ks_verdict_t v = ks_drive(KS_POS[i], KS_FORM_LEAF, &bad, &pst);
        assert(i < KS_POS_N);                          /* JPL Rule 2 bound  */
        assert(KS_POS[i] != NULL);
        if (pst != SRMECH_OK || v != KS_ACCEPT) { fails++; }
        printf("  [%02u] %-66s %-9s %s\n", i, KS_POS[i], ks_verdict_name(v),
               (v == KS_ACCEPT) ? "OK" : "*** FAIL");
    }
    printf("  failures: %d\n\n", fails);
    return fails;
}

/* Section 3 — the whole grammar, each row paired with the MEASURED Python
 * verdict it must agree with (measured on this worktree at rc444 through
 * srmech.dsl.chain().then / .fold / .reduce / .map_indexed). */
typedef struct {
    const char  *json;
    uint32_t     form;
    ks_verdict_t want;
    const char  *python;
} ks_edge_t;

#define KS_EDGE_N 20u
static const ks_edge_t KS_EDGE[KS_EDGE_N] = {
  /* leaf */
  { "{\"op\":\"magnitude\",\"x\":3}", KS_FORM_LEAF, KS_REJECT_UNDECLARED_KEY,
    "TypeError multiple values for 'x'   [C RETURNED 3.5 — 25th defect]" },
  { "{\"op\":\"best_rational_signed\",\"denom\":6}", KS_FORM_LEAF,
    KS_REJECT_UNDECLARED_KEY,
    "TypeError unexpected keyword 'denom' [C RETURNED (1, 2)]" },
  { "{\"op\":\"reorient\"}", KS_FORM_LEAF, KS_REJECT_MISSING_REQUIRED,
    "TypeError missing 'orientation'      [C already defers — parity held]" },
  { "{\"op\":\"cyclic_gcd\"}", KS_FORM_LEAF, KS_REJECT_MISSING_REQUIRED,
    "TypeError missing 'b'                [C already defers — parity held]" },
  { "{\"op\":\"no_such_op\"}", KS_FORM_LEAF, KS_UNKNOWN_OP,
    "ValueError unknown cascade op 'no_such_op'" },
  { "{\"op\":\"seq_get\",\"i\":2}", KS_FORM_LEAF, KS_UNKNOWN_OP,
    "ValueError unknown cascade op 'seq_get' (body name, not a leaf)" },
  /* fold — piped = 2, so BOTH operands are un-nameable */
  { "{\"fold_init\":1,\"fold_op\":\"cyclic_gcd\"}", KS_FORM_FOLD, KS_ACCEPT,
    "fold(1,'cyclic_gcd').run([12,18]) -> 1" },
  { "{\"fold_init\":1,\"fold_op\":\"cyclic_gcd\",\"b\":5}", KS_FORM_FOLD,
    KS_REJECT_UNDECLARED_KEY, "TypeError multiple values for 'b'" },
  { "{\"fold_init\":1,\"fold_op\":\"cyclic_gcd\",\"a\":1}", KS_FORM_FOLD,
    KS_REJECT_UNDECLARED_KEY, "TypeError multiple values for 'a'" },
  { "{\"fold_init\":1,\"fold_op\":\"cyclic_gcd\",\"bogus\":5}", KS_FORM_FOLD,
    KS_REJECT_UNDECLARED_KEY, "TypeError unexpected keyword 'bogus'" },
  { "{\"fold_init\":1,\"fold_op\":\"srmech.cascade.leaves.orientation_compose\"}",
    KS_FORM_FOLD, KS_ACCEPT, "fold(1, dotted).run([1,-1]) -> -1" },
  { "{\"fold_init\":1,\"fold_op\":\"srmech.cascade.leaves.orientation_compose\","
    "\"orientation\":1}", KS_FORM_FOLD, KS_REJECT_UNDECLARED_KEY,
    "TypeError multiple values for 'orientation'" },
  { "{\"fold_init\":1,\"fold_op\":\"srmech.cascade.leaves.orientation_compose\","
    "\"bogus\":1}", KS_FORM_FOLD, KS_REJECT_UNDECLARED_KEY,
    "TypeError unexpected keyword 'bogus'" },
  { "{\"fold_init\":1,\"fold_op\":\"orientation_compose\"}", KS_FORM_FOLD,
    KS_UNKNOWN_OP, "ValueError unknown cascade op 'orientation_compose' (bare)" },
  { "{\"fold_init\":1,\"fold_op\":\"cyclic_gcd\",\"fold_args\":[\"acc\",\"elem\"]}",
    KS_FORM_FOLD, KS_DEFER_NAMED_BIND,
    "arg_names rebinds the positionals — piped count is DATA, so defer" },
  /* reduce — piped = 2 */
  { "{\"reduce_op\":\"cyclic_gcd\"}", KS_FORM_REDUCE, KS_ACCEPT,
    "reduce('cyclic_gcd').run([12,18]) -> 6" },
  { "{\"reduce_op\":\"cyclic_gcd\",\"bogus\":1}", KS_FORM_REDUCE,
    KS_REJECT_UNDECLARED_KEY, "TypeError unexpected keyword 'bogus'" },
  /* map_indexed — piped = 2 (input_seq, k) */
  { "{\"map_op\":\"srmech.cascade.leaves.seq_get\"}", KS_FORM_MAP, KS_ACCEPT,
    "map_indexed(dotted).run([5,6,7]) -> [5, 6, 7]" },
  { "{\"map_op\":\"srmech.cascade.leaves.seq_get\",\"i\":2}", KS_FORM_MAP,
    KS_REJECT_UNDECLARED_KEY, "TypeError multiple values for 'i'" },
  { "{\"map_op\":\"seq_get\"}", KS_FORM_MAP, KS_UNKNOWN_OP,
    "ValueError unknown cascade op 'seq_get' — C's own matcher accepts bare (D3)" }
};

static int ks_run_edges(void)
{
    uint32_t i;
    int fails = 0;
    printf("SECTION 3 — the whole stage grammar, vs the MEASURED Python verdict\n");
    for (i = 0u; i < KS_EDGE_N; i++) {
        const char *bad = ""; srmech_status_t pst;
        ks_verdict_t v = ks_drive(KS_EDGE[i].json, KS_EDGE[i].form, &bad, &pst);
        assert(i < KS_EDGE_N);                         /* JPL Rule 2 bound  */
        assert(KS_EDGE[i].json != NULL);
        if (pst != SRMECH_OK || v != KS_EDGE[i].want) { fails++; }
        printf("  [%02u] form=%-6s %s\n       C: %-28s bad=%-14s %s\n"
               "       py: %s\n", i, KS_FORM[KS_EDGE[i].form].label,
               KS_EDGE[i].json, ks_verdict_name(v), bad,
               (v == KS_EDGE[i].want) ? "OK" : "*** FAIL", KS_EDGE[i].python);
    }
    printf("  failures: %d\n\n", fails);
    return fails;
}

/* Section 4 — COST, because the rcN objection is "you added a 663-row scan to
 * every stage". Two shapes measured: the WHOLE gate including
 * srmech_tool_registry_find's bounded linear scan, and the same gate with the
 * entry pointer already in hand — which is the shape the rcN should ship,
 * because dsl_leaf_dispatch has ALREADY matched the op name when it calls the
 * gate, so the row can travel with the branch instead of being re-found. */
static unsigned char g_bench_arena[KS_ARENA];

static int ks_run_cost(void)
{
    srmech_json_value_t *stage = NULL;
    const srmech_tool_entry_t *e;
    const char *bad = "";
    const unsigned long n = 200000ul;
    unsigned long i; clock_t t0, t1; double full, pre; long acc = 0;
    srmech_status_t st;
    assert(sizeof(g_bench_arena) == KS_ARENA);
    assert(n > 0ul);
    st = srmech_json_parse("{\"op\":\"reorient\",\"orientation\":-1}", 34u,
                           g_bench_arena, sizeof(g_bench_arena), &stage);
    if (st != SRMECH_OK) { printf("SECTION 4 — parse rc=%d\n", (int)st); return 1; }
    t0 = clock();
    for (i = 0ul; i < n; i++) {
        acc += (long)ks_check_stage(KS_FORM_LEAF, stage, &bad);
    }
    t1 = clock();
    full = (double)(t1 - t0) / (double)CLOCKS_PER_SEC;
    e = srmech_tool_registry_find("srmech.cascade.reorient");
    if (e == NULL) { printf("SECTION 4 — registry row missing\n"); return 1; }
    t0 = clock();
    for (i = 0ul; i < n; i++) {
        acc += (long)ks_keys_closed(e, &KS_FORM[KS_FORM_LEAF], stage, &bad);
        acc += (long)ks_required_present(e, &KS_FORM[KS_FORM_LEAF], stage, &bad);
    }
    t1 = clock();
    pre = (double)(t1 - t0) / (double)CLOCKS_PER_SEC;
    printf("SECTION 4 — cost per validated stage (%lu iterations, acc=%ld)\n", n, acc);
    printf("  with srmech_tool_registry_find : %8.0f ns/stage\n", full * 1e9 / (double)n);
    printf("  entry pointer already in hand  : %8.0f ns/stage\n", pre * 1e9 / (double)n);
    printf("  => ship the second shape: the op-name branch that matched already\n"
           "     identifies the row, so the gate is a walk of <= 3 keys.\n\n");
    return 0;
}

int main(void)
{
    int fails = 0;
    assert(sizeof(g_arena) == KS_ARENA);
    assert(KS_LINK_N == 10u);
    printf("srmech %s  ABI %d  — #1653 `#T1146` closed-key-set validator prototype\n\n",
           srmech_version(), (int)srmech_abi_version());
    fails += ks_report_link_health();
    fails += ks_run_defect_probes();
    fails += ks_run_positive_controls();
    fails += ks_run_edges();
    fails += ks_run_cost();
    printf("TOTAL failures: %d\n", fails);
    return (fails == 0) ? 0 : 1;
}

/* ==================================================================
 * DESIGN NOTE — WHERE THE DECLARED KEY SET LIVES SO IT CANNOT DRIFT
 * ==================================================================
 *
 * 1. THE KEY NAMES: already solved, no new artifact. `srmech_tool_registry.c`
 *    is GENERATED from `srmech.introspect.tool_schema` by
 *    c/tools/gen_tool_registry.py (run through tools/regen_all.py with an
 *    idempotence test), and the Python declaration it is generated from is
 *    pinned to the live callable signature in both directions by
 *    test_mcp.py::test_schema_signature_alignment_no_drift and
 *    test_declared_param_completeness_rc408.py. Read params[] at runtime and
 *    the C gate is the Python gate BY CONSTRUCTION. A hand-written C key table
 *    would rot; this one cannot, because three existing ratchets already hold
 *    it. (Measured: 9/9 name + required agreement over the C-named ops.)
 *
 * 2. THE PIPED COUNT: derive it from the FORM, never per-op. It is a property
 *    of the builder (`then` pipes 1, `fold`/`reduce`/`map_indexed` pipe 2 —
 *    _chain.py:556 `op_fn(value, **kwargs)` and the make_*_stage bodies), so
 *    one integer per form belongs next to the discriminator table, under the
 *    same bijection ratchet as test_combinator_kernel_closure.py
 *    ::test_c_discriminator_table_matches_python.
 *
 * 3. THE OP-NAME -> REGISTRY-NAME LINK: this is the ONE genuinely new datum,
 *    and it needs a generated home. No string rule derives it (measured 2/48
 *    with a prefix rule). Two acceptable homes, in preference order:
 *      (a) NEW GENERATED TABLE — c/tools/gen_cascade_op_registry_map.py,
 *          registered in codegen_manifest.py so tools/regen_all.py owns the
 *          write and the existing idempotence gate covers it. Emit one row per
 *          name `lookup_cascade_op` accepts (bare catalog names + the dotted
 *          spellings the descriptors use), each with its resolved registry name
 *          and its role mask. Python-side resolution by callable identity
 *          covers 35/48 of the descriptor-referenced names today; the residue
 *          is 10 class-scoped bare names (surface A carries `class` next to
 *          `op`, so the generator must key on the PAIR) plus 3 dotted names
 *          with no registry row at all (srmech.amsc.descriptor.render_template,
 *          srmech.signal_processing.encode_loe_content,
 *          srmech.signal_processing.rbs_hdc_instrument.mint_vector) — those are
 *          a declared-surface gap to file, not something to paper over with a
 *          default-accept.
 *      (b) PAIRED LITERAL IN dsl_leaf_dispatch under a source-parsing bijection
 *          test, in the exact shape of
 *          test_combinator_kernel_closure.py::test_c_discriminator_table_matches_python
 *          (which already parses a C string array and compares it with the
 *          Python side). Cheaper to land; still a hand-maintained table, so it
 *          only stays honest because the test reads the C source.
 *    Whichever home is chosen, generate it from what PYTHON accepts. Generating
 *    from the C matchers would re-open divergence D3: C's
 *    dsl_map_body_is_seq_get accepts the bare `seq_get` that lookup_cascade_op
 *    rejects (edge probe 19).
 *
 * 4. THE PARITY RATCHET THAT MUST LAND IN THE SAME COMMIT. None of the above
 *    proves the two projections agree; it only makes agreement possible. The
 *    rcN needs a test that RE-RUNS the round-1 census
 *    (notes/_1653_t1146_rejection_parity_rc444.py) as a gate and asserts the
 *    DEFECT_pure_rejects_native_accepts cell is 0, with the control cell
 *    non-empty so a validator that rejects everything cannot pass it. That is
 *    the only artifact that would have caught this class of defect, and its
 *    absence is why 24 probes shipped.
 *
 * ==================================================================
 * THE PYTHON HALF — SPECIFIED ONLY (this round edits no shipped source)
 * ==================================================================
 *
 * WHERE. srmech/dsl/_chain.py. `functools` is already imported at :27,
 * `Optional` at :28 and `lookup_cascade_op` at :30; `inspect` is NOT imported
 * and must be added. The change is ADDITIVE — the VALUE-TYPE gate stays exactly
 * as it is and a KEY-NAME gate goes in FRONT of it:
 *
 *   _PIPED = {"then": 1, "fold": 2, "reduce": 2, "map_indexed": 2}
 *
 *   @functools.lru_cache(maxsize=256)
 *   def _declared_kwarg_names(op_name, piped):
 *       "The kwarg names op_name accepts once `piped` positionals are supplied."
 *       try:
 *           fn = lookup_cascade_op(op_name)
 *       except ValueError:
 *           return None            # unknown name -> pure raises the ValueError
 *       try:
 *           params = list(inspect.signature(fn).parameters.values())
 *       except (TypeError, ValueError):
 *           return None            # unreadable signature -> decline
 *       if any(p.kind is p.VAR_KEYWORD for p in params):
 *           return None            # OPEN namespace: the callable owns the check
 *       return frozenset(p.name for p in params[piped:])
 *
 *   def _then_native_desc(op_name, kwargs):
 *       allowed = _declared_kwarg_names(op_name, _PIPED["then"])
 *       if allowed is None or not (kwargs.keys() <= allowed):
 *           return None            # THE KEY-NAME GATE (the missing half)
 *       stage = {"op": op_name}
 *       for kk, vv in kwargs.items():
 *           if not _is_c_scalar(vv):
 *               return None        # the VALUE-TYPE gate, unchanged
 *           stage[kk] = vv
 *       return stage
 *
 * The same one-line gate belongs on the three combinator native-desc builders
 * (_chain.py:284-332 fold, :326-334 reduce, :315-322 map_indexed) with
 * piped = 2, and `fold` must ALSO decline whenever `arg_names is not None` —
 * that rebinds the positionals, so the piped count becomes DATA and the closed
 * set is no longer derivable from the signature. That is the Python twin of
 * this prototype's KS_DEFER_NAMED_BIND arm (edge probe 14).
 *
 * WHY DECLINE AND NOT RAISE. Declining routes the whole chain to the pure
 * runner, which calls the real callable and raises the real TypeError with its
 * real text. So the fix adds NO new exception type, NO new message to keep in
 * sync, and the observable behaviour becomes byte-identical to the pure
 * projection — which is exactly how the two incidentally-clean ops
 * (cyclic_gcd, pin_slot_at_zero) already behave. Raising a new ChainSpecError
 * here would instead invent a THIRD message that neither projection has today.
 *
 * WHY THE TWO HALVES CANNOT DISAGREE. Python reads `inspect.signature`
 * directly; C reads the generated registry mirror of it. The two ratchets named
 * in point 1 pin the mirror to the signature in both directions, so the two
 * gates compute the same closed set from the same source. The MISSING-REQUIRED
 * arm needs no Python change at all (measured: `.then('reorient')` and
 * `.then('cyclic_gcd')` already reject on both projections) — it is in the C
 * gate for symmetry and because a future C kernel with its own defaulting could
 * otherwise re-open exactly that hole, which is what leaf_best_rational's
 * hardcoded (100, 1000000) would have done had they not matched Python's
 * DEFAULT_MAX_DENOMINATOR / DEFAULT_FINE_SCALE (they do; measured).
 */
