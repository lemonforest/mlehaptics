/* srmech_make_class.c — the make_class OBJECT-MODEL ENGINE in C (0.9.0rc201;
 * the make_class -> C arc, #887). The C peer of the compute half of
 * srmech.dsl._class_catalog.CatalogClass: a bare-C host (no Python) constructs a
 * DSL [class] instance from its packaged TOML descriptor + a field-state map and
 * RUNS its declared methods natively.
 *
 * ================================================================
 * DESIGN (scope-then-build; the rc201 = ENGINE CORE + a PROVEN vtable batch).
 * ================================================================
 *
 * The rc194-200 arc made all 31 make_class LEAF ops C-realizable (One:
 * srmech_the_one/one_scalar/one_matrix + the 5 inline constants; genome:
 * srmech_genome_* ; sedenion: srmech_sedenion_* + sed_slots + hamming + the HDC
 * storage leaves over srmech_mint_vector + srmech_hdc_*). rc201 builds the
 * ORCHESTRATION on top: the descriptor->field-state->dispatch->route ENGINE that
 * a bare-C host uses to RUN the object model, with a leaf VTABLE that returns
 * LIVE srmech_mval_t carriers (distinct from the rc188 invoke_tool text-
 * serialising vtable — this one keeps carriers live so the chain/routes compose).
 *
 * THE ENGINE (mirrors CatalogClass, one layer down):
 *   (1) DESCRIPTOR PARSE  — srmech_toml_parse over the packaged [class] TOML ->
 *       the [class] table; srmech_toml_table_get walks .field / .method / .<m>.
 *   (2) FIELD-STATE DICT   — an srmech_mval_t DICT (field-name STR -> value),
 *       seeded from [class.field] defaults (list*->[], dict*->{}, else NONE) then
 *       overlaid with the supplied fields (mirrors CatalogClass.__init__).
 *   (3) METHOD DISPATCH    — resolve method spec; a single `op` marshals its
 *       `binds` positionally from (args -> fields), calls the vtable thunk;
 *       (the `chain` multi-op pipeline is rc201b — a chain method DEFERS here).
 *   (4) STATE ROUTES       — rc201 realises the PLAIN (no route) + returns="self"
 *       routes; a method carrying appends/sets/mutates/chain DEFERS to pure
 *       (rc201b wires the genome appends + the sed mutates/chain).
 *   (5) LEAF VTABLE        — mc_vtable_call: op dotted-name -> a bespoke C thunk
 *       that marshals (bind carriers -> typed C args), calls the leaf's C symbol,
 *       and returns a live carrier.
 *
 * THE rc201 PROVEN BATCH (the leaves whose thunks ship + are proven byte-
 * identical to the pure CatalogClass by tests/test_make_class_engine_c_rc201.py):
 *   One (plain op):
 *     one_dim/one_imag_dims/one_partition/one_plane_counts/one_grammar_slots
 *       — the 5 INLINE-CONSTANT accessors (the `one` bind is w-invariant substrate
 *         structure, so the constant carriers 14 / (1,3,7) / (1,3,7,3) / (0,1,3)
 *         / ('B','H','N') are emitted with NO leaf call).
 *   SedenionRegister (plain op):
 *     navmap  -> srmech_sedenion_navmap (the 16-slot signed permutation DICT)
 *     slots   -> srmech_sed_slots       (the occupied (slot,sign) reshape DICT)
 *     is_navigable -> srmech_sedenion_is_navigable (the reversibility bool)
 *   SedenionRegister (returns="self"):
 *     navigate -> srmech_sedenion_navigate (route every slot name by x e_j -> a
 *       NEW register's {D, codebook, slots} field-state DICT; the returns="self"
 *       route builds a fresh instance, self untouched).
 *
 * DEFER (rc201b, the heavy-carrier leaf batch — inform-don't-limit, rc103): the
 * One bignum leaves (flat/matrix/scalar/the_one over srmech_bigint theta) +
 * Hurwitz.generate; the genome byte/HV leaves (chromosome/recall/genome/partition
 * + shape/cap) + the disk-persistence quartet (save/load/catalog/append, host-
 * glue); the sedenion HDC-storage leaves (write=mutates, read=chain,
 * materialize) that C-compose srmech_mint_vector + srmech_hdc_bind/bundle/
 * similarity; couple/uncouple/carry/correct. A method whose op is not in the
 * vtable, whose route is appends/sets/mutates, or which is a chain, sets
 * *out_kind = SRMECH_MAKE_CLASS_DEFER and the caller runs the COMPLETE pure
 * CatalogClass (never a wrong answer). A user (register_class_dir) class DEFERS
 * for the same reason (no host op-resolver callback -> SRMECH_ABI_VERSION stays 4).
 *
 * WHY NOT DISCHARGE make_class -> composes_c THIS rc: the ledger row is honest
 * only when the engine GENUINELY runs the object model across ALL its route types
 * (appends/mutates/chain, exercised only by the genome HV + sed HDC leaves) — that
 * heavy-carrier vtable is a clean second rc (rc201b), so make_class stays owed
 * this rc. rc201 lands the engine + the plain + returns="self" spine PROVEN.
 *
 * PROVER: srmech_make_class_run is the ctypes-drivable JSON-in/JSON-out surface —
 * (class_toml, method, fields_json, args_json) -> {"result": ..., "fields": ...}
 * (for returns="self", "result" is the NEW instance's field-state DICT). Fields /
 * args parse via srmech_json_parse + srmech_mval_from_json; the output serialises
 * via srmech_mcp_serialise_result (byte-identical to json.dumps(serialise_native)).
 *
 * JPL Power-of-Ten: caller-arena only (no malloc), <=60-line functions, >=2
 * asserts on INVARIANTS (runtime-NULL-checked params return NULL_ARG BEFORE any
 * assert), no goto, no abs/libm, bounded recursion. Additive symbols ->
 * SRMECH_ABI_VERSION stays 4. */

#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

#include "srmech.h"

/* A [class] descriptor has a small, bounded method/field/bind surface. */
#define MC_MAX_FIELDS 16
#define MC_MAX_BINDS  8
#define MC_SED_SLOTS  16

/* ------------------------------------------------------------------
 * Arena carve (void*-aligned bump over the public srmech_marshal_arena_t).
 * ------------------------------------------------------------------ */

static unsigned char *mc_align(unsigned char *p)
{
    uintptr_t a = (uintptr_t)sizeof(void *);
    uintptr_t pad;
    assert(p != NULL);
    assert(a >= 4u);
    pad = (a - ((uintptr_t)p % a)) % a;
    return p + pad;
}

static unsigned char *mc_carve(srmech_marshal_arena_t *a, size_t n)
{
    unsigned char *p;
    assert(a != NULL);
    assert(a->cur <= a->end);
    p = mc_align(a->cur);
    if (p > a->end || n > (size_t)(a->end - p)) { return NULL; }
    a->cur = p + n;
    return p;
}

/* ------------------------------------------------------------------
 * Carrier constructors — one node per call, zeroed then set (mval builders).
 * ------------------------------------------------------------------ */

static srmech_mval_t *mc_new(srmech_marshal_arena_t *a, srmech_mval_kind_t kind)
{
    srmech_mval_t *v;
    assert(a != NULL);
    assert(kind >= SRMECH_MVAL_NONE && kind <= SRMECH_MVAL_MAT);
    v = (srmech_mval_t *)mc_carve(a, sizeof(srmech_mval_t));
    if (v == NULL) { return NULL; }
    v->kind = kind; v->i = 0; v->re = 0.0; v->im = 0.0;
    v->s = NULL; v->slen = 0u; v->b = NULL; v->blen = 0u;
    v->items = NULL; v->keys = NULL; v->n = 0u; v->is_tuple = 0;
    return v;
}

static srmech_mval_t *mc_int(srmech_marshal_arena_t *a, int64_t x)
{
    srmech_mval_t *v = mc_new(a, SRMECH_MVAL_INT);
    assert(a != NULL);
    assert(a->cur <= a->end);
    if (v != NULL) { v->i = x; }
    return v;
}

static srmech_mval_t *mc_bool(srmech_marshal_arena_t *a, int truth)
{
    srmech_mval_t *v = mc_new(a, SRMECH_MVAL_BOOL);
    assert(a != NULL);
    assert(a->cur <= a->end);
    if (v != NULL) { v->i = truth ? 1 : 0; }
    return v;
}

/* A STR node copying `len` bytes of `src` INTO the arena (persists). */
static srmech_mval_t *mc_str_copy(srmech_marshal_arena_t *a,
                                  const char *src, uint32_t len)
{
    srmech_mval_t *v; unsigned char *buf;
    assert(a != NULL);
    assert(src != NULL || len == 0u);
    v = mc_new(a, SRMECH_MVAL_STR);
    if (v == NULL) { return NULL; }
    if (len > 0u) {
        buf = mc_carve(a, len);
        if (buf == NULL) { return NULL; }
        memcpy(buf, src, len);
        v->s = (const char *)buf;
    }
    v->slen = len;
    return v;
}

/* A LIST (list or tuple) node with an item-pointer array sized for `n`. */
static srmech_mval_t *mc_list(srmech_marshal_arena_t *a, uint32_t n, int is_tuple)
{
    srmech_mval_t *v = mc_new(a, SRMECH_MVAL_LIST);
    assert(a != NULL);
    assert(a->cur <= a->end);
    if (v == NULL) { return NULL; }
    v->is_tuple = is_tuple ? 1 : 0;
    v->n = n;
    if (n > 0u) {
        v->items = (srmech_mval_t **)mc_carve(a, (size_t)n * sizeof(void *));
        if (v->items == NULL) { return NULL; }
    }
    return v;
}

/* A DICT node with key + value pointer arrays sized for `n` (caller fills). */
static srmech_mval_t *mc_dict(srmech_marshal_arena_t *a, uint32_t n)
{
    srmech_mval_t *v = mc_new(a, SRMECH_MVAL_DICT);
    assert(a != NULL);
    assert(a->cur <= a->end);
    if (v == NULL) { return NULL; }
    v->n = n;
    if (n > 0u) {
        v->keys = (srmech_mval_t **)mc_carve(a, (size_t)n * sizeof(void *));
        v->items = (srmech_mval_t **)mc_carve(a, (size_t)n * sizeof(void *));
        if (v->keys == NULL || v->items == NULL) { return NULL; }
    }
    return v;
}

/* A small (num, den) TUPLE carrier (the exact-rational leaf shape). */
static srmech_mval_t *mc_pair(srmech_marshal_arena_t *a, int64_t x, int64_t y)
{
    srmech_mval_t *t = mc_list(a, 2u, 1);
    srmech_mval_t *n0 = mc_int(a, x), *n1 = mc_int(a, y);
    assert(a != NULL);
    assert(a->cur <= a->end);
    if (t == NULL || n0 == NULL || n1 == NULL) { return NULL; }
    t->items[0] = n0; t->items[1] = n1;
    return t;
}

/* ------------------------------------------------------------------
 * DICT lookup (linear scan over STR keys — the field-state / args maps are
 * tiny). Returns the value carrier, or NULL if absent / not a DICT.
 * ------------------------------------------------------------------ */

static const srmech_mval_t *mc_dict_get(const srmech_mval_t *d, const char *key)
{
    uint32_t i, klen;
    assert(key != NULL);
    assert(d == NULL || d->keys != NULL || d->n == 0u);  /* DICT keys invariant */
    if (d == NULL || d->kind != SRMECH_MVAL_DICT) { return NULL; }
    klen = (uint32_t)strlen(key);
    for (i = 0u; i < d->n; i++) {
        const srmech_mval_t *k = d->keys[i];
        if (k != NULL && k->kind == SRMECH_MVAL_STR && k->slen == klen
            && memcmp(k->s, key, klen) == 0) {
            return d->items[i];
        }
    }
    return NULL;
}

/* Reduce a TOML string value to (ptr, len); NULL for a non-string. */
static int mc_toml_str(const srmech_toml_value_t *v, const char **s, uint32_t *n)
{
    assert(s != NULL && n != NULL);
    assert(v == NULL || v->type <= SRMECH_TOML_TABLE);   /* valid TOML type */
    if (v == NULL || v->type != SRMECH_TOML_STRING) { return 0; }
    *s = v->u.str.ptr; *n = v->u.str.len;
    return 1;
}

/* ------------------------------------------------------------------
 * Field-state build — [class.field] defaults overlaid with supplied fields.
 * list*->empty LIST, dict*->empty DICT, else supplied-or-NONE (CatalogClass
 * __init__). `fields` is the JSON-parsed supplied map (may be NULL/empty).
 * ------------------------------------------------------------------ */

static srmech_mval_t *mc_field_default(srmech_marshal_arena_t *a,
                                       const srmech_toml_value_t *ftype)
{
    const char *s = NULL; uint32_t n = 0u;
    assert(a != NULL);
    assert(a->cur <= a->end);
    if (mc_toml_str(ftype, &s, &n)) {
        if (n >= 4u && memcmp(s, "list", 4u) == 0) { return mc_list(a, 0u, 0); }
        if (n >= 4u && memcmp(s, "dict", 4u) == 0) { return mc_dict(a, 0u); }
    }
    return mc_new(a, SRMECH_MVAL_NONE);
}

static srmech_mval_t *mc_build_fields(srmech_marshal_arena_t *a,
                                      const srmech_toml_value_t *field_tbl,
                                      const srmech_mval_t *supplied)
{
    srmech_mval_t *state; uint32_t i, n;
    assert(a != NULL);
    assert(a->cur <= a->end);
    n = (field_tbl != NULL && field_tbl->type == SRMECH_TOML_TABLE)
        ? field_tbl->u.tbl.n : 0u;
    if (n > MC_MAX_FIELDS) { return NULL; }
    state = mc_dict(a, n);
    if (state == NULL) { return NULL; }
    for (i = 0u; i < n; i++) {
        const char *fname = field_tbl->u.tbl.keys[i];
        const srmech_mval_t *sup = mc_dict_get(supplied, fname);
        srmech_mval_t *key = mc_str_copy(a, fname, (uint32_t)strlen(fname));
        srmech_mval_t *val = (sup != NULL)
            ? (srmech_mval_t *)sup
            : mc_field_default(a, field_tbl->u.tbl.vals[i]);
        if (key == NULL || val == NULL) { return NULL; }
        state->keys[i] = key; state->items[i] = val;
    }
    return state;
}

/* ------------------------------------------------------------------
 * Bind resolution — a single-op method's `binds` come positionally from the
 * call args first, then the instance fields (CatalogClass._invoke). Returns 0
 * (defer) if a bind cannot resolve. `out` holds up to MC_MAX_BINDS carriers.
 * ------------------------------------------------------------------ */

static int mc_resolve_binds(const srmech_toml_value_t *binds,
                            const srmech_mval_t *args, const srmech_mval_t *fields,
                            const srmech_mval_t **out, uint32_t *n_out)
{
    uint32_t i, n;
    assert(out != NULL && n_out != NULL);
    assert(binds == NULL || binds->type <= SRMECH_TOML_TABLE);
    n = (binds != NULL && binds->type == SRMECH_TOML_ARRAY) ? binds->u.arr.n : 0u;
    if (n > MC_MAX_BINDS) { return 0; }
    for (i = 0u; i < n; i++) {
        const char *bs = NULL; uint32_t bl = 0u; char name[64];
        const srmech_mval_t *v;
        if (!mc_toml_str(binds->u.arr.items[i], &bs, &bl) || bl >= sizeof(name)) {
            return 0;
        }
        memcpy(name, bs, bl); name[bl] = '\0';
        v = mc_dict_get(args, name);
        if (v == NULL) { v = mc_dict_get(fields, name); }
        if (v == NULL) { return 0; }
        out[i] = v;
    }
    *n_out = n;
    return 1;
}

/* ------------------------------------------------------------------
 * arg accessors — a carrier -> a typed C value, or 0 (defer to pure).
 * ------------------------------------------------------------------ */

static int mc_arg_i64(const srmech_mval_t *v, int64_t *out)
{
    assert(out != NULL);
    if (v == NULL || v->kind != SRMECH_MVAL_INT) { return 0; }
    assert(v->kind == SRMECH_MVAL_INT);
    *out = v->i;
    return 1;
}

/* A slots DICT {STR "0".."15" -> [key_str, sign_int]} -> parallel arrays, in
 * the DICT's stored order (order-preserving, as CatalogClass keeps it). Returns
 * 0 (defer) on a malformed entry. keys_out receives the STR value carriers. */
static int mc_read_slots(const srmech_mval_t *slots, int *slot_out, int *sign_out,
                         const srmech_mval_t **key_out, uint32_t *count)
{
    uint32_t i, n;
    assert(slot_out != NULL && sign_out != NULL && key_out != NULL && count != NULL);
    assert(slots == NULL || slots->keys != NULL || slots->n == 0u);
    if (slots == NULL || slots->kind != SRMECH_MVAL_DICT) { return 0; }
    n = slots->n;
    if (n > MC_SED_SLOTS) { return 0; }
    for (i = 0u; i < n; i++) {
        const srmech_mval_t *k = slots->keys[i], *pair = slots->items[i];
        char kb[8]; long sv;
        if (k == NULL || k->kind != SRMECH_MVAL_STR || k->slen == 0u
            || k->slen >= sizeof(kb)) { return 0; }
        memcpy(kb, k->s, k->slen); kb[k->slen] = '\0';
        sv = 0; { uint32_t j; for (j = 0u; j < k->slen; j++) {
            if (kb[j] < '0' || kb[j] > '9') { return 0; }
            sv = sv * 10 + (kb[j] - '0'); } }
        if (pair == NULL || pair->kind != SRMECH_MVAL_LIST || pair->n != 2u) { return 0; }
        if (pair->items[1] == NULL || pair->items[1]->kind != SRMECH_MVAL_INT) { return 0; }
        slot_out[i] = (int)sv; sign_out[i] = (int)pair->items[1]->i;
        key_out[i] = pair->items[0];
    }
    *count = n;
    return 1;
}

/* Build a slots DICT {STR itoa(slot) -> [key_carrier, sign]} from parallel
 * arrays, emitted in array order (the caller controls the order for byte
 * identity). Returns NULL (defer) on arena exhaustion. */
static srmech_mval_t *mc_build_slots(srmech_marshal_arena_t *a, const int *slots,
                                     const int *signs, const srmech_mval_t **keys,
                                     uint32_t count)
{
    srmech_mval_t *d; uint32_t i;
    assert(a != NULL);
    assert(slots != NULL && signs != NULL && keys != NULL);
    d = mc_dict(a, count);
    if (d == NULL) { return NULL; }
    for (i = 0u; i < count; i++) {
        char kb[8]; int m = slots[i], p = 0; srmech_mval_t *pair;
        if (m < 0 || m >= 100) { return NULL; }
        if (m >= 10) { kb[p++] = (char)('0' + m / 10); }
        kb[p++] = (char)('0' + m % 10); kb[p] = '\0';
        pair = mc_list(a, 2u, 1);
        if (pair == NULL || keys[i] == NULL) { return NULL; }
        pair->items[0] = (srmech_mval_t *)keys[i];
        pair->items[1] = mc_int(a, signs[i]);
        d->keys[i] = mc_str_copy(a, kb, (uint32_t)p);
        d->items[i] = pair;
        if (d->keys[i] == NULL || pair->items[1] == NULL) { return NULL; }
    }
    return d;
}

/* Ascending insertion-sort of `count` indices by slot value (mirrors Python
 * sorted(slots.items()) for the navigate route). */
static void mc_sort_by_slot(const int *slots, uint32_t count, uint32_t *order)
{
    uint32_t i, j, key;
    assert(slots != NULL && order != NULL);
    assert(count <= (uint32_t)MC_SED_SLOTS);
    for (i = 0u; i < count; i++) { order[i] = i; }
    for (i = 1u; i < count; i++) {
        key = order[i]; j = i;
        while (j > 0u && slots[order[j - 1u]] > slots[key]) {
            order[j] = order[j - 1u]; j--;
        }
        order[j] = key;
    }
}

/* ==================================================================
 * The LEAF VTABLE — op dotted-name -> a live-carrier thunk. rc201 batch.
 * ================================================================== */

/* One inline-constant accessors: the `one` bind is ignored (the constants are
 * w-invariant substrate structure). Emits 14 / (1,3,7) / (1,3,7,3) / (0,1,3) /
 * ('B','H','N'). Returns NULL (defer) on arena exhaustion. */
static srmech_mval_t *mc_one_const(srmech_marshal_arena_t *a, const char *op)
{
    static const int TRIPLE[3] = { 1, 3, 7 };
    static const int PART[4] = { 1, 3, 7, 3 };
    static const int PLANES[3] = { 0, 1, 3 };
    static const char *GRAM[3] = { "B", "H", "N" };
    srmech_mval_t *lst; uint32_t i;
    assert(a != NULL && op != NULL);
    assert(a->cur <= a->end);
    if (strcmp(op, "srmech.amsc.cascade.one.one_dim") == 0) { return mc_int(a, 14); }
    if (strcmp(op, "srmech.amsc.cascade.one.one_grammar_slots") == 0) {
        lst = mc_list(a, 3u, 1);
        if (lst == NULL) { return NULL; }
        for (i = 0u; i < 3u; i++) {
            lst->items[i] = mc_str_copy(a, GRAM[i], 1u);
            if (lst->items[i] == NULL) { return NULL; }
        }
        return lst;
    }
    if (strcmp(op, "srmech.amsc.cascade.one.one_imag_dims") == 0) {
        lst = mc_list(a, 3u, 1);
        for (i = 0u; lst != NULL && i < 3u; i++) { lst->items[i] = mc_int(a, TRIPLE[i]); }
    } else if (strcmp(op, "srmech.amsc.cascade.one.one_partition") == 0) {
        lst = mc_list(a, 4u, 1);
        for (i = 0u; lst != NULL && i < 4u; i++) { lst->items[i] = mc_int(a, PART[i]); }
    } else if (strcmp(op, "srmech.amsc.cascade.one.one_plane_counts") == 0) {
        lst = mc_list(a, 3u, 1);
        for (i = 0u; lst != NULL && i < 3u; i++) { lst->items[i] = mc_int(a, PLANES[i]); }
    } else {
        return NULL;
    }
    return lst;
}

/* sed navmap -> {STR "0".."15" -> [dest, sign]} for x e_j. */
static srmech_mval_t *mc_sed_navmap(srmech_marshal_arena_t *a, int64_t j)
{
    int dest[MC_SED_SLOTS], sign[MC_SED_SLOTS]; uint32_t i;
    srmech_mval_t *d;
    assert(a != NULL);
    assert(a->cur <= a->end);
    if (j < 0 || j >= MC_SED_SLOTS) { return NULL; }
    if (srmech_sedenion_navmap((int)j, dest, sign) != SRMECH_OK) { return NULL; }
    d = mc_dict(a, MC_SED_SLOTS);
    if (d == NULL) { return NULL; }
    for (i = 0u; i < MC_SED_SLOTS; i++) {
        char kb[4]; int p = 0, m = (int)i; srmech_mval_t *pr;
        if (m >= 10) { kb[p++] = (char)('0' + m / 10); }
        kb[p++] = (char)('0' + m % 10); kb[p] = '\0';
        pr = mc_pair(a, dest[i], sign[i]);
        d->keys[i] = mc_str_copy(a, kb, (uint32_t)p);
        d->items[i] = pr;
        if (pr == NULL || d->keys[i] == NULL) { return NULL; }
    }
    return d;
}

/* sed slots -> the (slot,sign) reshape DICT via srmech_sed_slots, in input
 * order (mirrors sed_slots: list(d.items()) order). */
static srmech_mval_t *mc_sed_slots(srmech_marshal_arena_t *a,
                                   const srmech_mval_t *slots)
{
    int in_s[MC_SED_SLOTS], in_g[MC_SED_SLOTS], out_s[MC_SED_SLOTS], out_g[MC_SED_SLOTS];
    const srmech_mval_t *keys[MC_SED_SLOTS]; uint32_t count = 0u;
    assert(a != NULL);
    assert(a->cur <= a->end);
    if (!mc_read_slots(slots, in_s, in_g, keys, &count)) { return NULL; }
    if (srmech_sed_slots(in_s, in_g, count, out_s, out_g) != SRMECH_OK) { return NULL; }
    return mc_build_slots(a, out_s, out_g, keys, count);
}

/* sed is_navigable -> bool over an int direction vector (power-of-two length). */
static srmech_mval_t *mc_sed_is_navigable(srmech_marshal_arena_t *a,
                                          const srmech_mval_t *dir)
{
    int64_t buf[SRMECH_CD_MAX_DIM]; uint32_t i, n; int inv = 0;
    assert(a != NULL);
    assert(a->cur <= a->end);
    if (dir == NULL || dir->kind != SRMECH_MVAL_LIST) { return NULL; }
    n = dir->n;
    if (n == 0u || n > (uint32_t)SRMECH_CD_MAX_DIM) { return NULL; }
    for (i = 0u; i < n; i++) {
        if (!mc_arg_i64(dir->items[i], &buf[i])) { return NULL; }
    }
    if (srmech_sedenion_is_navigable(buf, n, &inv) != SRMECH_OK) { return NULL; }
    return mc_bool(a, inv);
}

/* sed navigate (returns="self") -> a NEW register's {D, codebook, slots} field-
 * state DICT: route every slot name by x e_j (sorted-input order, mirroring
 * SedenionRegister.navigate). D + codebook pass through unchanged. */
static srmech_mval_t *mc_sed_navigate(srmech_marshal_arena_t *a, int64_t j,
                                      const srmech_mval_t *dfield,
                                      const srmech_mval_t *codebook,
                                      const srmech_mval_t *slots)
{
    int in_s[MC_SED_SLOTS], in_g[MC_SED_SLOTS], os[MC_SED_SLOTS], og[MC_SED_SLOTS];
    int ss[MC_SED_SLOTS], sg[MC_SED_SLOTS];
    const srmech_mval_t *keys[MC_SED_SLOTS], *sk[MC_SED_SLOTS];
    uint32_t count = 0u, i, order[MC_SED_SLOTS]; srmech_mval_t *out, *routed;
    assert(a != NULL);
    assert(a->cur <= a->end);
    if (j < 0 || j >= MC_SED_SLOTS) { return NULL; }
    if (!mc_read_slots(slots, in_s, in_g, keys, &count)) { return NULL; }
    mc_sort_by_slot(in_s, count, order);
    for (i = 0u; i < count; i++) { ss[i] = in_s[order[i]]; sg[i] = in_g[order[i]];
        sk[i] = keys[order[i]]; }
    if (srmech_sedenion_navigate((int)j, ss, sg, count, os, og) != SRMECH_OK) { return NULL; }
    routed = mc_build_slots(a, os, og, sk, count);
    out = mc_dict(a, 3u);
    if (out == NULL || routed == NULL) { return NULL; }
    out->keys[0] = mc_str_copy(a, "D", 1u); out->items[0] = (srmech_mval_t *)dfield;
    out->keys[1] = mc_str_copy(a, "codebook", 8u); out->items[1] = (srmech_mval_t *)codebook;
    out->keys[2] = mc_str_copy(a, "slots", 5u); out->items[2] = routed;
    if (out->keys[0] == NULL || out->keys[1] == NULL || out->keys[2] == NULL) { return NULL; }
    return out;
}

/* The vtable dispatch: op dotted-name + resolved bind carriers -> a live result
 * carrier, or NULL (the op is not in the rc201 batch -> DEFER). */
static srmech_mval_t *mc_vtable_call(srmech_marshal_arena_t *a, const char *op,
                                     const srmech_mval_t **binds, uint32_t nb)
{
    int64_t j;
    assert(a != NULL && op != NULL);
    assert(binds != NULL || nb == 0u);
    if (strncmp(op, "srmech.amsc.cascade.one.one_", 28) == 0) {
        return mc_one_const(a, op);
    }
    if (strcmp(op, "srmech.amsc.cascade.sedenion_register.sed_navmap") == 0) {
        if (nb != 1u || !mc_arg_i64(binds[0], &j)) { return NULL; }
        return mc_sed_navmap(a, j);
    }
    if (strcmp(op, "srmech.amsc.cascade.sedenion_register.sed_slots") == 0) {
        if (nb != 1u) { return NULL; }
        return mc_sed_slots(a, binds[0]);
    }
    if (strcmp(op, "srmech.amsc.cascade.sedenion_register.sed_is_navigable") == 0) {
        if (nb != 1u) { return NULL; }
        return mc_sed_is_navigable(a, binds[0]);
    }
    if (strcmp(op, "srmech.amsc.cascade.sedenion_register.sed_navigate") == 0) {
        if (nb != 4u || !mc_arg_i64(binds[0], &j)) { return NULL; }
        return mc_sed_navigate(a, j, binds[1], binds[2], binds[3]);
    }
    return NULL;
}

/* ------------------------------------------------------------------
 * The method engine — dispatch one method + apply its state route. rc201
 * realises PLAIN (no route) + returns="self"; appends/sets/mutates/chain DEFER.
 * *out_result is the value to serialise; *self_unchanged stays the field state.
 * Returns 1 (dispatched, *out_result set) or 0 (DEFER).
 * ------------------------------------------------------------------ */

static int mc_run_method(srmech_marshal_arena_t *a,
                         const srmech_toml_value_t *spec,
                         const srmech_mval_t *args, const srmech_mval_t *fields,
                         srmech_mval_t **out_result)
{
    const srmech_toml_value_t *opv, *ret; const srmech_mval_t *binds[MC_MAX_BINDS];
    const char *op = NULL; uint32_t op_len = 0u, nb = 0u; char opbuf[128];
    srmech_mval_t *res;
    assert(a != NULL && out_result != NULL);
    assert(a->cur <= a->end);
    if (spec == NULL || spec->type != SRMECH_TOML_TABLE) { return 0; }
    if (srmech_toml_table_get(spec, "chain") != NULL) { return 0; }   /* rc201b */
    if (srmech_toml_table_get(spec, "appends") != NULL) { return 0; }  /* rc201b */
    if (srmech_toml_table_get(spec, "sets") != NULL) { return 0; }     /* rc201b */
    if (srmech_toml_table_get(spec, "mutates") != NULL) { return 0; }  /* rc201b */
    opv = srmech_toml_table_get(spec, "op");
    if (!mc_toml_str(opv, &op, &op_len) || op_len >= sizeof(opbuf)) { return 0; }
    memcpy(opbuf, op, op_len); opbuf[op_len] = '\0';
    if (!mc_resolve_binds(srmech_toml_table_get(spec, "binds"), args, fields,
                          binds, &nb)) { return 0; }
    res = mc_vtable_call(a, opbuf, binds, nb);
    if (res == NULL) { return 0; }
    /* returns="self": the op already produced the new instance's field DICT —
     * that IS the emitted result (self is untouched; _apply_returns). */
    ret = srmech_toml_table_get(spec, "returns");
    if (ret != NULL) {
        const char *rs = NULL; uint32_t rl = 0u;
        if (!mc_toml_str(ret, &rs, &rl) || rl != 4u || memcmp(rs, "self", 4u) != 0) {
            return 0;
        }
        if (res->kind != SRMECH_MVAL_DICT) { return 0; }
    }
    *out_result = res;
    return 1;
}

/* ------------------------------------------------------------------
 * Descriptor navigation — root TOML -> the [class.method.<name>] spec table.
 * ------------------------------------------------------------------ */

static const srmech_toml_value_t *mc_method_spec(const srmech_toml_value_t *root,
                                                 const char *method,
                                                 const srmech_toml_value_t **field_tbl)
{
    const srmech_toml_value_t *cls, *methods;
    assert(method != NULL && field_tbl != NULL);
    assert(root == NULL || root->type == SRMECH_TOML_TABLE);
    if (root == NULL) { return NULL; }
    cls = srmech_toml_table_get(root, "class");
    if (cls == NULL) { return NULL; }
    *field_tbl = srmech_toml_table_get(cls, "field");
    methods = srmech_toml_table_get(cls, "method");
    if (methods == NULL) { return NULL; }
    return srmech_toml_table_get(methods, method);
}

/* ------------------------------------------------------------------
 * Emit {"result": <result>, "fields": <post-self-fields>} as canonical JSON.
 * ------------------------------------------------------------------ */

static srmech_status_t mc_emit(srmech_marshal_arena_t *a, srmech_mval_t *result,
                               const srmech_mval_t *fields,
                               char *out, size_t out_cap, size_t *out_len)
{
    srmech_mval_t *obj;
    assert(a != NULL && result != NULL && out_len != NULL);
    assert(out != NULL || out_cap == 0u);
    obj = mc_dict(a, 2u);
    if (obj == NULL) { return SRMECH_ERR_OVERFLOW; }
    obj->keys[0] = mc_str_copy(a, "result", 6u); obj->items[0] = result;
    obj->keys[1] = mc_str_copy(a, "fields", 6u);
    obj->items[1] = (srmech_mval_t *)fields;
    if (obj->keys[0] == NULL || obj->keys[1] == NULL) { return SRMECH_ERR_OVERFLOW; }
    return srmech_mcp_serialise_result(obj, out, out_cap, out_len);
}

/* ------------------------------------------------------------------
 * The workspace bound + the PUBLIC prover entry.
 * ------------------------------------------------------------------ */

size_t srmech_make_class_run_arena_bytes(size_t toml_len, size_t fields_len,
                                         size_t args_len)
{
    /* The TOML tree (32x, the srmech_toml builder's node overhead) + the two
     * JSON trees + two mval trees + the result carriers, generously over-
     * allocated plus a fixed floor. */
    size_t base = 32768u;
    assert(base > 0u);
    assert(base >= 32768u);
    return base + 48u * (toml_len + fields_len + args_len);
}

/* Parse `json`[0..len) into an mval DICT (or NONE for empty). Returns 0 on a
 * parse error / non-object. */
static int mc_parse_map(const char *json, size_t len, srmech_marshal_arena_t *a,
                        srmech_mval_t **out)
{
    srmech_json_value_t *jroot; unsigned char *jws; size_t jws_len;
    assert(a != NULL && out != NULL);
    assert(a->cur <= a->end);
    if (json == NULL || len == 0u) { *out = mc_new(a, SRMECH_MVAL_DICT); return *out != NULL; }
    jws_len = 8u * len + 4096u;
    jws = mc_carve(a, jws_len);
    if (jws == NULL) { return 0; }
    if (srmech_json_parse(json, len, jws, jws_len, &jroot) != SRMECH_OK) { return 0; }
    return srmech_mval_from_json(jroot, a, out) == SRMECH_OK;
}

srmech_status_t srmech_make_class_run(const char *class_toml, size_t toml_len,
                                      const char *method,
                                      const char *fields_json, size_t fields_len,
                                      const char *args_json, size_t args_len,
                                      void *ws, size_t ws_len,
                                      char *out, size_t out_cap, size_t *out_len,
                                      int *out_kind)
{
    srmech_marshal_arena_t a; srmech_toml_value_t *root; const srmech_toml_value_t *spec;
    const srmech_toml_value_t *field_tbl = NULL; srmech_mval_t *fields, *args, *state, *res;
    unsigned char *tws; size_t tws_len;
    if (class_toml == NULL || method == NULL || ws == NULL || out == NULL
        || out_len == NULL || out_kind == NULL) { return SRMECH_ERR_NULL_ARG; }
    assert(ws_len > 0u);
    assert(out_cap > 0u);
    *out_kind = SRMECH_MAKE_CLASS_DEFER;
    srmech_marshal_arena_init(&a, ws, ws_len);
    tws_len = 32u * toml_len + 8192u;
    tws = mc_carve(&a, tws_len);
    if (tws == NULL) { return SRMECH_ERR_OVERFLOW; }
    if (srmech_toml_parse(class_toml, toml_len, tws, tws_len, &root) != SRMECH_OK) {
        return SRMECH_OK;                          /* unparseable -> DEFER to pure */
    }
    spec = mc_method_spec(root, method, &field_tbl);
    if (spec == NULL) { return SRMECH_OK; }        /* unknown method -> DEFER */
    if (!mc_parse_map(fields_json, fields_len, &a, &fields)) { return SRMECH_OK; }
    if (!mc_parse_map(args_json, args_len, &a, &args)) { return SRMECH_OK; }
    state = mc_build_fields(&a, field_tbl, fields);
    if (state == NULL) { return SRMECH_OK; }
    if (!mc_run_method(&a, spec, args, state, &res)) { return SRMECH_OK; }
    if (mc_emit(&a, res, state, out, out_cap, out_len) != SRMECH_OK) {
        return SRMECH_OK;                          /* serialise overflow -> DEFER */
    }
    *out_kind = SRMECH_MAKE_CLASS_DISPATCHED;
    return SRMECH_OK;
}
