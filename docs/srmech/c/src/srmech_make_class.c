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
 *       `binds` positionally from (args -> fields), calls the vtable thunk; a
 *       `chain` method (rc201b) threads each {op,binds,as} stage's result into a
 *       small scope, the last stage being the method result.
 *   (4) STATE ROUTES       — rc201 realised PLAIN + returns="self"; rc201b adds
 *       the full route machinery: appends (list.append one field), sets (replace
 *       one field), mutates (the op returns (ret, {field:new}); each named field
 *       is replaced) — the emitted `fields` is the POST-route state.
 *   (5) LEAF VTABLE        — mc_vtable_call: op dotted-name -> a bespoke C thunk
 *       that marshals (bind carriers -> typed C args), calls the leaf's C symbol,
 *       and returns a live carrier. rc201b adds the heavy-carrier leaves (the sed
 *       HDC-storage batch + the genome byte/HV batch) alongside the rc201 spine.
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
 * rc201b HEAVY BATCH (byte-identical to the pure CatalogClass; composes the
 * shipped C leaves): SedenionRegister write (mutates slots+codebook: srmech_mint_
 * vector), materialize (bundle_k bind(ADDR[k], value_k): srmech_hdc_bind/bundle,
 * chiral_flip=byte-reverse), read (the 2-stage chain: unbind -> nearest-codebook
 * clean by the EXACT integer |D-2*hamming| argmax; NO float), carry/correct
 * (srmech_hamming_encode/decode_correct); Genome add_chromosome (appends:
 * srmech_genome_chromosome), recall/assemble/partition (srmech_genome_recall/
 * genome/partition, the partition dict dedup/labels-order semantics replicated).
 *
 * DEFER (rc103 inform-don't-limit — what the int64/bytes mval carrier CANNOT emit
 * byte-identically): the One bignum leaves flat/scalar (exact rationals overflow
 * int64 — a 249-bit trace numerator) + matrix (float within-tol, not byte-exact);
 * Hurwitz.generate (a live One object, not JSON); the sed couple/uncouple working
 * word (float); the genome disk quartet save/load/catalog/append (host-FS) +
 * shape/cap. A method whose op is not in the vtable (or whose leaf/route the
 * engine cannot represent) sets *out_kind = SRMECH_MAKE_CLASS_DEFER and the caller
 * runs the COMPLETE pure CatalogClass (never a wrong answer). A user
 * (register_class_dir) class DEFERS the same way (no host op-resolver callback).
 *
 * make_class is DISCHARGED owed_orchestration -> composes_c this rc: the engine
 * GENUINELY runs the object model across ALL route types (plain / returns="self" /
 * mutates / appends / chain) over real heavy carriers; the mval-unrepresentable
 * leaves DEFER honestly. Additive leaf wiring -> SRMECH_ABI_VERSION stays 4.
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
#define MC_ONE_DIM    14u  /* One.DIM = 2+4+8; the 14x14 = 196-cell G(sigma,theta) */

/* rc201b heavy-vtable bounds (all caller-arena; JPL Rule 2 loop over-bounds). */
#define MC_MAX_PARTS   (MC_SED_SLOTS + 1)  /* ≤16 slot binds + 1 __pad__ vector   */
#define MC_MAX_SCOPE   8                   /* chain stages / per-method as= names  */
#define MC_MAX_LEAVES  4096                /* genome kernel leaf-block count       */
#define MC_MAX_KERNELS 256                 /* genome assemble kernel count         */
#define MC_ADDR_MAX    24                  /* "SEDENION:e15" + NUL headroom        */
#define MC_HAMMING_MAX 65535               /* 2^16 - 1 codeword ceiling (Hamming)  */

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

/* mc_mat — a real f64 MAT carrier (rc331; #948): rows*cols row-major doubles
 * carved 8-aligned into the arena; *out_buf receives the fillable buffer. Mirrors
 * the marshal mm_mat carrier (n=rows, i=cols, blen=#doubles, is_tuple=0 = real),
 * so srmech_mcp_serialise_result emits the nested [[...]] float array byte-for-byte
 * with json.dumps(serialise_native(Mat)). */
static srmech_mval_t *mc_mat(srmech_marshal_arena_t *a, uint32_t rows, uint32_t cols,
                             double **out_buf)
{
    srmech_mval_t *v; size_t nd = (size_t)rows * cols;
    assert(a != NULL && out_buf != NULL);
    assert(a->cur <= a->end);
    v = mc_new(a, SRMECH_MVAL_MAT);
    if (v == NULL) { return NULL; }
    v->n = rows; v->i = (int64_t)cols; v->is_tuple = 0; v->blen = (uint32_t)nd;
    v->b = mc_carve(a, nd * sizeof(double));         /* 8-aligned by mc_carve */
    if (v->b == NULL) { return NULL; }
    *out_buf = (double *)(void *)v->b;
    return v;
}

/* mc_one_matrix — the One.matrix() vtable thunk (rc331; #948). Reads the `one`
 * field DICT {"sigma": int, "theta": [num, den], "terms": int} (all int64 — the
 * INPUT is not bignum, only srmech_one_matrix's internal series are), regenerates
 * G(sigma,theta) via srmech_one_matrix into a MAT carrier BYTE-IDENTICAL to the
 * pure One.to_matrix (the correctly-rounded cos/sin closes the make_class DEFER).
 * The srmech_one_matrix workspace is carved from the arena. NULL (defer) on a
 * malformed field / out-of-domain input / arena exhaustion. */
static srmech_mval_t *mc_one_matrix(srmech_marshal_arena_t *a,
                                    const srmech_mval_t **binds, uint32_t nb)
{
    const srmech_mval_t *one_d, *theta;
    int64_t sigma, tn, td, terms;
    uint32_t tnl[3], tdl[3];
    srmech_bigint_t tnb, tdb;
    srmech_mval_t *mat; double *buf; unsigned char *ws; size_t ws_len;
    assert(a != NULL);
    assert(binds != NULL || nb == 0u);
    if (nb != 1u) { return NULL; }
    one_d = binds[0];
    theta = mc_dict_get(one_d, "theta");
    if (!mc_arg_i64(mc_dict_get(one_d, "sigma"), &sigma)) { return NULL; }
    if (!mc_arg_i64(mc_dict_get(one_d, "terms"), &terms)) { return NULL; }
    if (theta == NULL || theta->kind != SRMECH_MVAL_LIST || theta->n != 2u) { return NULL; }
    if (!mc_arg_i64(theta->items[0], &tn) || !mc_arg_i64(theta->items[1], &td)) { return NULL; }
    if (terms < 0 || terms > 50 || td <= 0 || (sigma != 1 && sigma != -1)) { return NULL; }
    tnb.limbs = tnl; tnb.cap = 3u; tnb.n = 0u; tnb.sign = 0;
    tdb.limbs = tdl; tdb.cap = 3u; tdb.n = 0u; tdb.sign = 0;
    if (srmech_bigint_set_i64(&tnb, tn) != SRMECH_OK) { return NULL; }
    if (srmech_bigint_set_i64(&tdb, td) != SRMECH_OK) { return NULL; }
    ws_len = srmech_one_matrix_ws_bound(tnb.n, tdb.n, (uint32_t)terms);
    ws = mc_carve(a, ws_len);
    if (ws == NULL) { return NULL; }
    mat = mc_mat(a, MC_ONE_DIM, MC_ONE_DIM, &buf);
    if (mat == NULL) { return NULL; }
    if (srmech_one_matrix((int32_t)sigma, &tnb, &tdb, (uint32_t)terms, buf,
                          (size_t)MC_ONE_DIM * MC_ONE_DIM, ws, ws_len) != SRMECH_OK) {
        return NULL;
    }
    return mat;
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
    /* rc298 (`#933`): sized by the DENSE cap — this buffer feeds
     * srmech_sedenion_is_navigable, which declines anything above it. Sizing it
     * off SRMECH_CD_MAX_DIM would stage direction vectors the callee rejects. */
    int64_t buf[SRMECH_CD_DENSE_MAX_DIM]; uint32_t i, n; int inv = 0;
    assert(a != NULL);
    assert(a->cur <= a->end);
    if (dir == NULL || dir->kind != SRMECH_MVAL_LIST) { return NULL; }
    n = dir->n;
    if (n == 0u || n > (uint32_t)SRMECH_CD_DENSE_MAX_DIM) { return NULL; }
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

/* ==================================================================
 * rc201b heavy-carrier leaves — the sedenion HDC-storage batch (write /
 * materialize / read-chain / carry / correct) + the genome byte/HV batch
 * (chromosome / recall / genome / partition). Every leaf returns a LIVE mval
 * whose canonical-JSON serialisation is BYTE-IDENTICAL to the pure CatalogClass
 * (the srmech_mint_vector + srmech_hdc_* + srmech_genome_* + srmech_hamming_*
 * C peers compose here). The One bignum leaves (flat/scalar exact rationals
 * exceed the int64 mval carrier) + One matrix (float within-tol) + the float
 * couple/uncouple + host-FS save/load DEFER — the mval carrier can't emit them
 * byte-identically, so pure runs them (rc103 inform-don't-limit; see the
 * DEFER note in the file header + tests/test_make_class_engine_c_rc201.py).
 * ================================================================== */

/* Raw bytes of a carrier: a BYTES node passes through; a base64 STR node is
 * decoded via srmech_mcp_marshal_arg("bytes", …) (the public inbound decoder);
 * anything else -> 0 (defer). buf/len alias the arena. */
static int mc_raw_bytes(srmech_marshal_arena_t *a, const srmech_mval_t *v,
                        const unsigned char **buf, uint32_t *len)
{
    srmech_mval_t *dec;
    assert(a != NULL && buf != NULL && len != NULL);
    assert(a->cur <= a->end);
    if (v == NULL) { return 0; }
    if (v->kind == SRMECH_MVAL_BYTES) { *buf = v->b; *len = v->blen; return 1; }
    if (v->kind != SRMECH_MVAL_STR) { return 0; }
    if (srmech_mcp_marshal_arg("bytes", v, a, &dec) != SRMECH_OK) { return 0; }
    if (dec == NULL || dec->kind != SRMECH_MVAL_BYTES) { return 0; }
    *buf = dec->b; *len = dec->blen;
    return 1;
}

/* A BYTES node copying `len` bytes of `src` INTO the arena (persists). */
static srmech_mval_t *mc_bytes_new(srmech_marshal_arena_t *a,
                                   const unsigned char *src, uint32_t len)
{
    srmech_mval_t *v; unsigned char *buf;
    assert(a != NULL);
    assert(src != NULL || len == 0u);
    v = mc_new(a, SRMECH_MVAL_BYTES);
    if (v == NULL) { return NULL; }
    if (len > 0u) {
        buf = mc_carve(a, len);
        if (buf == NULL) { return NULL; }
        memcpy(buf, src, len);
        v->b = buf;
    }
    v->blen = len;
    return v;
}

/* Mint the deterministic RBS-HDC vector named `name`[0..nlen) into a fresh
 * BYTES node of `nbytes` (srmech_mint_vector; byte-identical to the pure
 * srmech.signal_processing.mint_vector). NULL (defer) on any failure. */
static srmech_mval_t *mc_mint(srmech_marshal_arena_t *a, const char *name,
                              size_t nlen, uint32_t nbytes)
{
    srmech_mval_t *v; unsigned char *buf;
    assert(a != NULL && name != NULL);
    assert(nbytes > 0u);
    v = mc_new(a, SRMECH_MVAL_BYTES);
    if (v == NULL) { return NULL; }
    buf = mc_carve(a, nbytes);
    if (buf == NULL) { return NULL; }
    if (srmech_mint_vector((const uint8_t *)name, nlen, nbytes, buf) != SRMECH_OK) {
        return NULL;
    }
    v->b = buf; v->blen = nbytes;
    return v;
}

/* The value vector for (key, sign): codebook[key] decoded, chiral-flipped
 * (Class C = seq[::-1] byte-reverse; never abs()) when sign < 0. NULL on a
 * missing key / width mismatch / arena exhaustion. */
static srmech_mval_t *mc_sed_value_bytes(srmech_marshal_arena_t *a,
                                         const srmech_mval_t *codebook,
                                         const srmech_mval_t *key, int sign,
                                         uint32_t nbytes)
{
    const srmech_mval_t *cv; const unsigned char *raw; uint32_t rl, i;
    unsigned char *buf; char kb[128];
    assert(a != NULL);
    assert(nbytes > 0u);
    if (key == NULL || key->kind != SRMECH_MVAL_STR || key->slen >= sizeof(kb)) {
        return NULL;
    }
    memcpy(kb, key->s, key->slen); kb[key->slen] = '\0';
    cv = mc_dict_get(codebook, kb);
    if (!mc_raw_bytes(a, cv, &raw, &rl) || rl != nbytes) { return NULL; }
    buf = mc_carve(a, nbytes);
    if (buf == NULL) { return NULL; }
    if (sign >= 0) { memcpy(buf, raw, nbytes); }
    else { for (i = 0u; i < nbytes; i++) { buf[i] = raw[nbytes - 1u - i]; } }
    return mc_bytes_new(a, buf, nbytes);
}

/* Build the mint name "SEDENION:e{slot}" into `nm` (>= MC_ADDR_MAX); returns
 * the length. slot in [0, 100). */
static uint32_t mc_addr_name(char *nm, int slot)
{
    uint32_t p;
    assert(nm != NULL);
    assert(slot >= 0 && slot < 100);
    memcpy(nm, "SEDENION:e", 10u); p = 10u;
    if (slot >= 10) { nm[p++] = (char)('0' + slot / 10); }
    nm[p++] = (char)('0' + slot % 10);
    return p;
}

/* One materialise part: bind(mint("SEDENION:e{slot}"), value_vec(key,sign)) ->
 * a fresh nbytes buffer, or NULL (defer). */
static const unsigned char *mc_sed_part(srmech_marshal_arena_t *a, int slot,
                                        const srmech_mval_t *codebook,
                                        const srmech_mval_t *key, int sign,
                                        uint32_t nbytes)
{
    char nm[MC_ADDR_MAX]; uint32_t p; srmech_mval_t *addr, *val; unsigned char *out;
    assert(a != NULL);
    assert(nbytes > 0u);
    p = mc_addr_name(nm, slot);
    addr = mc_mint(a, nm, p, nbytes);
    val = mc_sed_value_bytes(a, codebook, key, sign, nbytes);
    out = mc_carve(a, nbytes);
    if (addr == NULL || val == NULL || out == NULL) { return NULL; }
    if (srmech_hdc_bind(addr->b, val->b, nbytes, out) != SRMECH_OK) { return NULL; }
    return out;
}

/* sed materialize: bundle_k bind(ADDR[k], value_k) over the sorted slots (a
 * __pad__ mint padding an even count to odd). Returns the superposition BYTES,
 * or NULL (an empty register -> pure raises; defer). */
static srmech_mval_t *mc_sed_materialize(srmech_marshal_arena_t *a,
                                         const srmech_mval_t *slots,
                                         const srmech_mval_t *codebook, int64_t D)
{
    int sl[MC_SED_SLOTS], sg[MC_SED_SLOTS]; const srmech_mval_t *keys[MC_SED_SLOTS];
    uint32_t count = 0u, order[MC_SED_SLOTS], i, nbytes, np = 0u;
    const unsigned char *parts[MC_MAX_PARTS]; unsigned char *out; srmech_mval_t *pad;
    assert(a != NULL);
    assert(a->cur <= a->end);
    if (D <= 0 || (D % 8) != 0) { return NULL; }
    nbytes = (uint32_t)(D / 8);
    if (!mc_read_slots(slots, sl, sg, keys, &count) || count == 0u) { return NULL; }
    mc_sort_by_slot(sl, count, order);
    for (i = 0u; i < count; i++) {
        parts[np] = mc_sed_part(a, sl[order[i]], codebook, keys[order[i]],
                                sg[order[i]], nbytes);
        if (parts[np] == NULL) { return NULL; }
        np++;
    }
    if (np == 1u) { return mc_bytes_new(a, parts[0], nbytes); }
    if ((np % 2u) == 0u) {
        pad = mc_mint(a, "__pad__", 7u, nbytes);
        if (pad == NULL) { return NULL; }
        parts[np++] = pad->b;
    }
    out = mc_carve(a, nbytes);
    if (out == NULL || srmech_hdc_bundle(parts, np, nbytes, out) != SRMECH_OK) {
        return NULL;
    }
    return mc_bytes_new(a, out, nbytes);
}

/* Copy `codebook` and, if `key` is absent, append (key -> mint("VAL:"+key)).
 * Insertion order preserved (byte-identical to the pure codebook growth). */
static srmech_mval_t *mc_codebook_add(srmech_marshal_arena_t *a,
                                      const srmech_mval_t *codebook,
                                      const srmech_mval_t *key, uint32_t nbytes)
{
    uint32_t n, i; char kb[128], vn[160]; const srmech_mval_t *exist;
    srmech_mval_t *nd, *mv;
    assert(a != NULL);
    assert(nbytes > 0u);
    if (key == NULL || key->kind != SRMECH_MVAL_STR || key->slen >= sizeof(kb)) {
        return NULL;
    }
    memcpy(kb, key->s, key->slen); kb[key->slen] = '\0';
    n = (codebook != NULL && codebook->kind == SRMECH_MVAL_DICT) ? codebook->n : 0u;
    exist = mc_dict_get(codebook, kb);
    nd = mc_dict(a, (exist != NULL) ? n : n + 1u);
    if (nd == NULL) { return NULL; }
    for (i = 0u; i < n; i++) { nd->keys[i] = codebook->keys[i];
        nd->items[i] = codebook->items[i]; }
    if (exist == NULL) {
        memcpy(vn, "VAL:", 4u); memcpy(vn + 4, key->s, key->slen);
        mv = mc_mint(a, vn, 4u + key->slen, nbytes);
        nd->keys[n] = mc_str_copy(a, kb, key->slen); nd->items[n] = mv;
        if (mv == NULL || nd->keys[n] == NULL) { return NULL; }
    }
    return nd;
}

/* Copy `slots` and set slots[slot] = [key, sign] (overwrite in place if the
 * slot exists, else append). Insertion order preserved. */
static srmech_mval_t *mc_slots_set(srmech_marshal_arena_t *a,
                                   const srmech_mval_t *slots, int slot,
                                   const srmech_mval_t *key, int sign)
{
    uint32_t n, i; int p = 0, m = slot, found = -1; char kb[8];
    srmech_mval_t *nd, *pair;
    assert(a != NULL);
    assert(key != NULL);
    if (m < 0 || m >= 100) { return NULL; }
    if (m >= 10) { kb[p++] = (char)('0' + m / 10); }
    kb[p++] = (char)('0' + m % 10);
    n = (slots != NULL && slots->kind == SRMECH_MVAL_DICT) ? slots->n : 0u;
    for (i = 0u; i < n; i++) { const srmech_mval_t *k = slots->keys[i];
        if (k != NULL && k->kind == SRMECH_MVAL_STR && k->slen == (uint32_t)p
            && memcmp(k->s, kb, (size_t)p) == 0) { found = (int)i; break; } }
    nd = mc_dict(a, (found >= 0) ? n : n + 1u);
    pair = mc_list(a, 2u, 0);
    if (nd == NULL || pair == NULL) { return NULL; }
    pair->items[0] = mc_str_copy(a, key->s, key->slen); pair->items[1] = mc_int(a, sign);
    if (pair->items[0] == NULL || pair->items[1] == NULL) { return NULL; }
    for (i = 0u; i < n; i++) { nd->keys[i] = slots->keys[i]; nd->items[i] = slots->items[i]; }
    if (found >= 0) { nd->items[found] = pair; }
    else { nd->keys[n] = mc_str_copy(a, kb, (uint32_t)p); nd->items[n] = pair;
        if (nd->keys[n] == NULL) { return NULL; } }
    return nd;
}

/* sed write (mutates=["slots","codebook"]): returns the (None, {"slots":…,
 * "codebook":…}) 2-LIST the mutates route applies. `sign` is the leftover call
 * kwarg (default +1, normalised to ±1). */
static srmech_mval_t *mc_sed_write(srmech_marshal_arena_t *a,
                                   const srmech_mval_t *args, int slot,
                                   const srmech_mval_t *key,
                                   const srmech_mval_t *slots,
                                   const srmech_mval_t *codebook, int64_t D)
{
    const srmech_mval_t *sv; int sign = 1; int64_t sraw; uint32_t nbytes;
    srmech_mval_t *ncb, *nsl, *upd, *tuple, *none;
    assert(a != NULL);
    assert(a->cur <= a->end);
    if (D <= 0 || (D % 8) != 0 || slot < 0 || slot >= MC_SED_SLOTS) { return NULL; }
    nbytes = (uint32_t)(D / 8);
    sv = mc_dict_get(args, "sign");
    if (sv != NULL) { if (!mc_arg_i64(sv, &sraw)) { return NULL; }
        sign = (sraw >= 0) ? 1 : -1; }
    ncb = mc_codebook_add(a, codebook, key, nbytes);
    nsl = mc_slots_set(a, slots, slot, key, sign);
    upd = mc_dict(a, 2u); none = mc_new(a, SRMECH_MVAL_NONE); tuple = mc_list(a, 2u, 1);
    if (ncb == NULL || nsl == NULL || upd == NULL || none == NULL || tuple == NULL) {
        return NULL;
    }
    upd->keys[0] = mc_str_copy(a, "slots", 5u); upd->items[0] = nsl;
    upd->keys[1] = mc_str_copy(a, "codebook", 8u); upd->items[1] = ncb;
    if (upd->keys[0] == NULL || upd->keys[1] == NULL) { return NULL; }
    tuple->items[0] = none; tuple->items[1] = upd;
    return tuple;
}

/* sed read CHAIN stage 1 (sed_read_unbind): NONE if the register is empty, else
 * bind(mint("SEDENION:e{slot}"), materialize()) — the noisy vector. */
static srmech_mval_t *mc_sed_read_unbind(srmech_marshal_arena_t *a, int slot,
                                         const srmech_mval_t *slots,
                                         const srmech_mval_t *codebook, int64_t D)
{
    srmech_mval_t *mat, *addr; unsigned char *out; char nm[MC_ADDR_MAX]; uint32_t p, nbytes;
    assert(a != NULL);
    assert(a->cur <= a->end);
    if (D <= 0 || (D % 8) != 0 || slot < 0 || slot >= MC_SED_SLOTS) { return NULL; }
    nbytes = (uint32_t)(D / 8);
    if (codebook == NULL || codebook->kind != SRMECH_MVAL_DICT || codebook->n == 0u
        || slots == NULL || slots->kind != SRMECH_MVAL_DICT || slots->n == 0u) {
        return mc_new(a, SRMECH_MVAL_NONE);
    }
    mat = mc_sed_materialize(a, slots, codebook, D);
    p = mc_addr_name(nm, slot);
    addr = mc_mint(a, nm, p, nbytes);
    out = mc_carve(a, nbytes);
    if (mat == NULL || addr == NULL || out == NULL) { return NULL; }
    if (srmech_hdc_bind(addr->b, mat->b, nbytes, out) != SRMECH_OK) { return NULL; }
    return mc_bytes_new(a, out, nbytes);
}

/* Integer chirality magnitude |D_bits - 2*hamming(noisy, cand)| — the EXACT
 * peer of |similarity| = |1 - 2h/D| (same denom D_bits, so the argmax order is
 * identical without any float). */
static int64_t mc_sed_mag(const unsigned char *noisy, const unsigned char *cand,
                          uint32_t nbytes)
{
    uint32_t h; int64_t d2h;
    assert(noisy != NULL && cand != NULL);
    assert(nbytes > 0u);
    if (srmech_hdc_hamming(noisy, cand, nbytes, &h) != SRMECH_OK) { return -1; }
    d2h = (int64_t)nbytes * 8 - 2 * (int64_t)h;
    return (d2h >= 0) ? d2h : -d2h;      /* Class-K pin-slot magnitude; no abs() */
}

/* sed read CHAIN stage 2 (sed_clean): nearest-codebook clean of `noisy` ->
 * (key, sign). (None, +1) when noisy is NONE (empty register). The argmax
 * replays the pure pos-then-neg tie rule (>= for +, > for −) exactly. */
static srmech_mval_t *mc_sed_clean(srmech_marshal_arena_t *a,
                                   const srmech_mval_t *noisy,
                                   const srmech_mval_t *codebook)
{
    uint32_t i, j, nbytes; const unsigned char *nb; int best_sign = 1;
    const srmech_mval_t *best_key = NULL; int64_t best_mag = -1; srmech_mval_t *tuple, *ks;
    assert(a != NULL);
    assert(a->cur <= a->end);
    tuple = mc_list(a, 2u, 1);
    if (tuple == NULL) { return NULL; }
    if (noisy == NULL || noisy->kind == SRMECH_MVAL_NONE) {
        tuple->items[0] = mc_new(a, SRMECH_MVAL_NONE); tuple->items[1] = mc_int(a, 1);
        return (tuple->items[0] == NULL || tuple->items[1] == NULL) ? NULL : tuple;
    }
    if (noisy->kind != SRMECH_MVAL_BYTES || codebook == NULL
        || codebook->kind != SRMECH_MVAL_DICT) { return NULL; }
    nb = noisy->b; nbytes = noisy->blen;
    for (i = 0u; i < codebook->n; i++) {
        const srmech_mval_t *k = codebook->keys[i]; const unsigned char *vb; uint32_t vl;
        unsigned char *rev; int64_t mp, mn;
        if (k == NULL || k->kind != SRMECH_MVAL_STR) { return NULL; }
        if (k->slen == 7u && memcmp(k->s, "__pad__", 7u) == 0) { continue; }
        if (!mc_raw_bytes(a, codebook->items[i], &vb, &vl) || vl != nbytes) { return NULL; }
        mp = mc_sed_mag(nb, vb, nbytes);
        if (mp >= best_mag) { best_key = k; best_sign = 1; best_mag = mp; }
        rev = mc_carve(a, nbytes);
        if (rev == NULL) { return NULL; }
        for (j = 0u; j < nbytes; j++) { rev[j] = vb[nbytes - 1u - j]; }
        mn = mc_sed_mag(nb, rev, nbytes);
        if (mn > best_mag) { best_key = k; best_sign = -1; best_mag = mn; }
    }
    ks = (best_key != NULL) ? mc_str_copy(a, best_key->s, best_key->slen)
                            : mc_new(a, SRMECH_MVAL_NONE);
    tuple->items[0] = ks; tuple->items[1] = mc_int(a, best_sign);
    return (ks == NULL || tuple->items[1] == NULL) ? NULL : tuple;
}

/* Read a LIST of 0/1 INT carriers into `out` (cap `cap`); *len set. 0 (defer)
 * on a non-list / oversize / non-int / non-bit element. */
static int mc_read_bits(const srmech_mval_t *v, uint8_t *out, uint32_t cap,
                        uint32_t *len)
{
    uint32_t i;
    assert(out != NULL);
    assert(len != NULL && cap > 0u);
    if (v == NULL || v->kind != SRMECH_MVAL_LIST || v->n > cap) { return 0; }
    for (i = 0u; i < v->n; i++) {
        const srmech_mval_t *e = v->items[i];
        if (e == NULL || e->kind != SRMECH_MVAL_INT || (e->i != 0 && e->i != 1)) {
            return 0;
        }
        out[i] = (uint8_t)e->i;
    }
    *len = v->n;
    return 1;
}

/* Build a LIST of `n` INT carriers from a uint8 bit array. */
static srmech_mval_t *mc_bits_list(srmech_marshal_arena_t *a, const uint8_t *bits,
                                   uint32_t n)
{
    srmech_mval_t *lst; uint32_t i;
    assert(a != NULL);
    assert(bits != NULL || n == 0u);
    lst = mc_list(a, n, 0);
    if (lst == NULL) { return NULL; }
    for (i = 0u; i < n; i++) {
        lst->items[i] = mc_int(a, bits[i]);
        if (lst->items[i] == NULL) { return NULL; }
    }
    return lst;
}

/* Infer the Hamming parity-bit count n from a 2^n-1 codeword length, or 0 if
 * `len` is not of that form in [2, MC_HAMMING_MAX_N-cap]. */
static int mc_hamming_n(uint32_t len)
{
    int n;
    assert(SRMECH_HAMMING_MAX_N >= 9);         /* the C path's cap is within range */
    for (n = 2; n <= 9; n++) {                 /* codeword <= 511 (bounded stack) */
        assert(n >= 2 && n <= 9);              /* bounded loop invariant */
        if (len == (uint32_t)((1u << n) - 1u)) { return n; }
    }
    return 0;
}

/* sed carry: srmech_hamming_encode(overflow_bits, k, n) -> the 2^n-1-bit
 * codeword LIST. n is the leftover call kwarg (default 3). */
static srmech_mval_t *mc_sed_carry(srmech_marshal_arena_t *a,
                                   const srmech_mval_t *args,
                                   const srmech_mval_t *bits)
{
    uint8_t data[512], code[512]; uint32_t k = 0u; int n = 3; int64_t nraw;
    const srmech_mval_t *nv; uint32_t code_len;
    assert(a != NULL);
    assert(a->cur <= a->end);
    nv = mc_dict_get(args, "n");
    if (nv != NULL) { if (!mc_arg_i64(nv, &nraw)) { return NULL; } n = (int)nraw; }
    if (n < 2 || n > 9) { return NULL; }
    code_len = (uint32_t)((1u << n) - 1u);
    if (!mc_read_bits(bits, data, sizeof(data), &k)) { return NULL; }
    if (srmech_hamming_encode(data, (size_t)k, n, code) != SRMECH_OK) { return NULL; }
    return mc_bits_list(a, code, code_len);
}

/* sed correct: srmech_hamming_decode_correct -> {"data", "error_position",
 * "corrected_codeword"} (the pure dict shape). */
static srmech_mval_t *mc_sed_correct(srmech_marshal_arena_t *a,
                                     const srmech_mval_t *codeword)
{
    uint8_t code[512], data[512]; uint32_t len = 0u, i; int pos = 0, n;
    srmech_mval_t *d, *dl, *cl;
    assert(a != NULL);
    assert(a->cur <= a->end);
    if (!mc_read_bits(codeword, code, sizeof(code), &len)) { return NULL; }
    n = mc_hamming_n(len);
    if (n == 0) { return NULL; }
    if (srmech_hamming_decode_correct(code, (size_t)len, data, &pos) != SRMECH_OK) {
        return NULL;
    }
    if (pos >= 1 && (uint32_t)pos <= len) { code[pos - 1] ^= 1u; }   /* Class-K flip */
    d = mc_dict(a, 3u);
    dl = mc_bits_list(a, data, len - (uint32_t)n);
    cl = mc_bits_list(a, code, len);
    if (d == NULL || dl == NULL || cl == NULL) { return NULL; }
    d->keys[0] = mc_str_copy(a, "data", 4u); d->items[0] = dl;
    d->keys[1] = mc_str_copy(a, "error_position", 14u); d->items[1] = mc_int(a, pos);
    d->keys[2] = mc_str_copy(a, "corrected_codeword", 18u); d->items[2] = cl;
    for (i = 0u; i < 3u; i++) { if (d->keys[i] == NULL || d->items[i] == NULL) { return NULL; } }
    return d;
}

/* Decode a LIST of leaf carriers into a contiguous `dim`-block buffer; *n_out
 * gets the block count. NULL (defer) on a non-list / oversize / bad width. */
static unsigned char *mc_strand_contig(srmech_marshal_arena_t *a,
                                       const srmech_mval_t *lst, uint32_t dim,
                                       size_t *n_out)
{
    size_t n, i; unsigned char *buf;
    assert(a != NULL && n_out != NULL);
    assert(dim > 0u);
    if (lst == NULL || lst->kind != SRMECH_MVAL_LIST || lst->n > MC_MAX_LEAVES) {
        return NULL;
    }
    n = lst->n;
    buf = mc_carve(a, n * dim);
    if (buf == NULL) { return NULL; }
    for (i = 0u; i < n; i++) {
        const unsigned char *raw; uint32_t rl;
        if (!mc_raw_bytes(a, lst->items[i], &raw, &rl) || rl != dim) { return NULL; }
        memcpy(buf + i * dim, raw, dim);
    }
    *n_out = n;
    return buf;
}

/* Split a contiguous `n_blocks`*`dim` strand into a LIST of `n_blocks` BYTES
 * chunks (the pure list-of-HV shape; each HV serialises as its raw bytes). */
static srmech_mval_t *mc_chunk_list(srmech_marshal_arena_t *a,
                                    const unsigned char *strand, size_t n_blocks,
                                    uint32_t dim)
{
    srmech_mval_t *lst; size_t i;
    assert(a != NULL);
    assert(dim > 0u);
    if (n_blocks > (size_t)MC_MAX_LEAVES) { return NULL; }
    lst = mc_list(a, (uint32_t)n_blocks, 0);
    if (lst == NULL) { return NULL; }
    for (i = 0u; i < n_blocks; i++) {
        lst->items[i] = mc_bytes_new(a, strand + i * dim, dim);
        if (lst->items[i] == NULL) { return NULL; }
    }
    return lst;
}

/* genome chromosome (add_chromosome; appends): a leading CHROM cap over `label`
 * (the leftover call kwarg, default "chromosome") + each leaf coupled through
 * coupling -> a LIST of (1+n_leaves) leaf_dim BYTES chunks. */
static srmech_mval_t *mc_genome_chromosome(srmech_marshal_arena_t *a,
                                           const srmech_mval_t *args,
                                           const srmech_mval_t *leaves_list,
                                           const srmech_mval_t *coupling)
{
    const unsigned char *one; uint32_t dim; unsigned char *leaves, *out;
    size_t nl = 0u, sn; const srmech_mval_t *lbl; const char *lp = "chromosome";
    uint32_t ll = 10u;
    assert(a != NULL);
    assert(a->cur <= a->end);
    if (!mc_raw_bytes(a, coupling, &one, &dim) || dim == 0u || dim > 256u) { return NULL; }
    leaves = mc_strand_contig(a, leaves_list, dim, &nl);
    if (leaves == NULL) { return NULL; }
    lbl = mc_dict_get(args, "label");
    if (lbl != NULL) {
        if (lbl->kind != SRMECH_MVAL_STR) { return NULL; }
        lp = lbl->s; ll = lbl->slen;
    }
    sn = (1u + nl) * dim;
    out = mc_carve(a, sn);
    if (out == NULL) { return NULL; }
    if (srmech_genome_chromosome((const uint8_t *)lp, ll, one, dim, leaves, nl,
                                 out, sn) != SRMECH_OK) { return NULL; }
    return mc_chunk_list(a, out, 1u + nl, dim);
}

/* genome recall: recover a chromosome's leaves (skip caps; re-bind coupling) ->
 * a LIST of leaf_dim BYTES. `telomere` (bind 2) is unused (gate-agnostic). */
static srmech_mval_t *mc_genome_recall(srmech_marshal_arena_t *a,
                                       const srmech_mval_t *strand,
                                       const srmech_mval_t *coupling)
{
    const unsigned char *one; uint32_t dim; unsigned char *blocks, *out;
    size_t nb = 0u, n_leaves = 0u;
    assert(a != NULL);
    assert(a->cur <= a->end);
    if (!mc_raw_bytes(a, coupling, &one, &dim) || dim == 0u || dim > 256u) { return NULL; }
    blocks = mc_strand_contig(a, strand, dim, &nb);
    if (blocks == NULL) { return NULL; }
    out = mc_carve(a, nb * dim);
    if (out == NULL) { return NULL; }
    if (srmech_genome_recall(blocks, nb, dim, one, out, nb * dim, &n_leaves)
        != SRMECH_OK) { return NULL; }
    return mc_chunk_list(a, out, n_leaves, dim);
}

/* genome assemble (genome): pack a {label: [leaves]} DICT into ONE multi-kernel
 * strand -> a LIST of leaf_dim BYTES chunks. */
static srmech_mval_t *mc_genome_genome(srmech_marshal_arena_t *a,
                                       const srmech_mval_t *kernels,
                                       const srmech_mval_t *coupling)
{
    const unsigned char *one; uint32_t dim; size_t nk, i, tot = 0u, off = 0u, nbk = 0u;
    unsigned char *labels, *leaves, *out; size_t lab_off = 0u, lab_tot = 0u;
    size_t label_lens[MC_MAX_KERNELS], leaf_counts[MC_MAX_KERNELS];
    assert(a != NULL);
    assert(a->cur <= a->end);
    if (!mc_raw_bytes(a, coupling, &one, &dim) || dim == 0u || dim > 256u) { return NULL; }
    if (kernels == NULL || kernels->kind != SRMECH_MVAL_DICT
        || kernels->n > MC_MAX_KERNELS) { return NULL; }
    nk = kernels->n;
    for (i = 0u; i < nk; i++) {                        /* size pass */
        const srmech_mval_t *k = kernels->keys[i], *v = kernels->items[i];
        if (k == NULL || k->kind != SRMECH_MVAL_STR
            || v == NULL || v->kind != SRMECH_MVAL_LIST) { return NULL; }
        lab_tot += k->slen; tot += v->n;
    }
    labels = mc_carve(a, lab_tot); leaves = mc_carve(a, tot * dim);
    if ((lab_tot > 0u && labels == NULL) || (tot > 0u && leaves == NULL)) { return NULL; }
    for (i = 0u; i < nk; i++) {                        /* fill pass */
        const srmech_mval_t *k = kernels->keys[i], *v = kernels->items[i]; size_t j;
        memcpy(labels + lab_off, k->s, k->slen); lab_off += k->slen;
        label_lens[i] = k->slen; leaf_counts[i] = v->n;
        for (j = 0u; j < v->n; j++) {
            const unsigned char *raw; uint32_t rl;
            if (!mc_raw_bytes(a, v->items[j], &raw, &rl) || rl != dim) { return NULL; }
            memcpy(leaves + off * dim, raw, dim); off++;
        }
    }
    out = mc_carve(a, (nk + tot) * dim);
    if (out == NULL) { return NULL; }
    if (srmech_genome_genome(labels, label_lens, one, dim, leaves, leaf_counts, nk,
                             out, (nk + tot) * dim, &nbk) != SRMECH_OK) { return NULL; }
    return mc_chunk_list(a, out, nbk, dim);
}

/* Find `lab`[0..ll) among the `nu` (uptr[], ulen[]) label slices; -1 if absent. */
static int mc_uniq_find(const char * const *uptr, const uint32_t *ulen, uint32_t nu,
                        const char *lab, uint32_t ll)
{
    uint32_t m;
    assert(uptr != NULL && ulen != NULL);
    assert(lab != NULL);
    for (m = 0u; m < nu; m++) {
        if (ulen[m] == ll && memcmp(uptr[m], lab, ll) == 0) { return (int)m; }
    }
    return -1;
}

/* Emit the {label: leaves} DICT in the `labels=` STR-LIST order, filtered to
 * those present in the uniq set (dedup — the pure dict-comprehension). */
static srmech_mval_t *mc_part_filter(srmech_marshal_arena_t *a,
                                     const srmech_mval_t *labels,
                                     const char * const *uptr, const uint32_t *ulen,
                                     srmech_mval_t * const *ulst, uint32_t nu)
{
    srmech_mval_t *d; uint32_t p, ne = 0u;
    assert(a != NULL);
    assert(labels != NULL && labels->kind == SRMECH_MVAL_LIST);
    d = mc_dict(a, labels->n);
    if (d == NULL) { return NULL; }
    for (p = 0u; p < labels->n; p++) {
        const srmech_mval_t *e = labels->items[p]; int idx; uint32_t q, dup = 0u;
        if (e == NULL || e->kind != SRMECH_MVAL_STR) { return NULL; }
        idx = mc_uniq_find(uptr, ulen, nu, e->s, e->slen);
        if (idx < 0) { continue; }                     /* label absent from strand */
        for (q = 0u; q < ne; q++) {                    /* already emitted (dedup) */
            if (d->keys[q]->slen == e->slen
                && memcmp(d->keys[q]->s, e->s, e->slen) == 0) { dup = 1u; break; }
        }
        if (dup) { continue; }
        d->keys[ne] = mc_str_copy(a, e->s, e->slen); d->items[ne] = ulst[(uint32_t)idx];
        if (d->keys[ne] == NULL) { return NULL; }
        ne++;
    }
    d->n = ne;
    return d;
}

/* genome partition: recover {label: [leaves]} from a multi-kernel strand. Phase
 * 1 builds the strand-order uniq set (overwrite-on-duplicate-label, keeping the
 * first position); phase 2 emits uniq order (labels=None) or the labels= order
 * (mirrors partition's dict + dict-comprehension). Bounded leaf counts. */
static srmech_mval_t *mc_genome_partition(srmech_marshal_arena_t *a,
                                          const srmech_mval_t *strand,
                                          const srmech_mval_t *coupling,
                                          const srmech_mval_t *labels)
{
    const unsigned char *one; uint32_t dim; unsigned char *blocks, *olv, *olab;
    uint32_t counts[MC_MAX_KERNELS]; size_t nb = 0u, nparts = 0u, nlv = 0u, i, off = 0u;
    const char *uptr[MC_MAX_KERNELS]; uint32_t ulen[MC_MAX_KERNELS]; srmech_mval_t *ulst[MC_MAX_KERNELS];
    uint32_t nu = 0u; srmech_mval_t *d; uint32_t e;
    assert(a != NULL);
    assert(a->cur <= a->end);
    if (!mc_raw_bytes(a, coupling, &one, &dim) || dim == 0u || dim > 256u) { return NULL; }
    blocks = mc_strand_contig(a, strand, dim, &nb);
    olv = mc_carve(a, nb * dim); olab = mc_carve(a, nb * dim);
    if (blocks == NULL || olv == NULL || olab == NULL) { return NULL; }
    if (srmech_genome_partition(blocks, nb, dim, one, olv, nb * dim, olab, nb * dim,
                                counts, MC_MAX_KERNELS, &nparts, &nlv) != SRMECH_OK
        || nparts > MC_MAX_KERNELS) { return NULL; }
    for (i = 0u; i < nparts; i++) {                    /* phase 1: strand-order uniq */
        const char *lab = (const char *)(olab + i * dim); uint32_t ll = 0u; int idx;
        srmech_mval_t *lst;
        while (ll < dim && lab[ll] != '\0') { ll++; }
        lst = mc_chunk_list(a, olv + off * dim, counts[i], dim);
        if (lst == NULL) { return NULL; }
        off += counts[i];
        idx = mc_uniq_find(uptr, ulen, nu, lab, ll);
        if (idx >= 0) { ulst[idx] = lst; }
        else { uptr[nu] = lab; ulen[nu] = ll; ulst[nu] = lst; nu++; }
    }
    if (labels != NULL && labels->kind == SRMECH_MVAL_LIST) {
        return mc_part_filter(a, labels, uptr, ulen, ulst, nu);
    }
    d = mc_dict(a, nu);                                /* phase 2: uniq order (no filter) */
    if (d == NULL) { return NULL; }
    for (e = 0u; e < nu; e++) {
        d->keys[e] = mc_str_copy(a, uptr[e], ulen[e]); d->items[e] = ulst[e];
        if (d->keys[e] == NULL) { return NULL; }
    }
    return d;
}

/* Sedenion leaf sub-dispatch — `suf` is the op suffix after "…sed_". */
static srmech_mval_t *mc_vtable_sed(srmech_marshal_arena_t *a, const char *suf,
                                    const srmech_mval_t **binds, uint32_t nb,
                                    const srmech_mval_t *args)
{
    int64_t j, D, slot;
    assert(a != NULL && suf != NULL);
    assert(binds != NULL || nb == 0u);
    if (strcmp(suf, "navmap") == 0) {
        return (nb == 1u && mc_arg_i64(binds[0], &j)) ? mc_sed_navmap(a, j) : NULL;
    }
    if (strcmp(suf, "slots") == 0) { return (nb == 1u) ? mc_sed_slots(a, binds[0]) : NULL; }
    if (strcmp(suf, "is_navigable") == 0) {
        return (nb == 1u) ? mc_sed_is_navigable(a, binds[0]) : NULL;
    }
    if (strcmp(suf, "navigate") == 0) {
        return (nb == 4u && mc_arg_i64(binds[0], &j))
            ? mc_sed_navigate(a, j, binds[1], binds[2], binds[3]) : NULL;
    }
    if (strcmp(suf, "write") == 0) {
        if (nb != 5u || !mc_arg_i64(binds[0], &slot) || !mc_arg_i64(binds[4], &D)) {
            return NULL;
        }
        return mc_sed_write(a, args, (int)slot, binds[1], binds[2], binds[3], D);
    }
    if (strcmp(suf, "materialize") == 0) {
        return (nb == 3u && mc_arg_i64(binds[2], &D))
            ? mc_sed_materialize(a, binds[0], binds[1], D) : NULL;
    }
    if (strcmp(suf, "read_unbind") == 0) {
        return (nb == 4u && mc_arg_i64(binds[0], &slot) && mc_arg_i64(binds[3], &D))
            ? mc_sed_read_unbind(a, (int)slot, binds[1], binds[2], D) : NULL;
    }
    if (strcmp(suf, "clean") == 0) {
        return (nb == 2u) ? mc_sed_clean(a, binds[0], binds[1]) : NULL;
    }
    if (strcmp(suf, "carry") == 0) { return (nb == 1u) ? mc_sed_carry(a, args, binds[0]) : NULL; }
    if (strcmp(suf, "correct") == 0) { return (nb == 1u) ? mc_sed_correct(a, binds[0]) : NULL; }
    return NULL;
}

/* Genome leaf sub-dispatch — `suf` is the op suffix after "srmech.amsc.genome.". */
static srmech_mval_t *mc_vtable_genome(srmech_marshal_arena_t *a, const char *suf,
                                       const srmech_mval_t **binds, uint32_t nb,
                                       const srmech_mval_t *args)
{
    assert(a != NULL && suf != NULL);
    assert(binds != NULL || nb == 0u);
    if (strcmp(suf, "chromosome") == 0) {
        return (nb == 2u) ? mc_genome_chromosome(a, args, binds[0], binds[1]) : NULL;
    }
    if (strcmp(suf, "recall") == 0) {
        return (nb == 3u) ? mc_genome_recall(a, binds[0], binds[1]) : NULL;
    }
    if (strcmp(suf, "genome") == 0) {
        return (nb == 2u) ? mc_genome_genome(a, binds[0], binds[1]) : NULL;
    }
    if (strcmp(suf, "partition") == 0) {
        return (nb == 3u) ? mc_genome_partition(a, binds[0], binds[1], binds[2]) : NULL;
    }
    return NULL;
}

/* The vtable dispatch: op dotted-name + resolved bind carriers (+ the call-args
 * DICT for leftover kwargs) -> a live result carrier, or NULL (DEFER). */
static srmech_mval_t *mc_vtable_call(srmech_marshal_arena_t *a, const char *op,
                                     const srmech_mval_t **binds, uint32_t nb,
                                     const srmech_mval_t *args)
{
    assert(a != NULL && op != NULL);
    assert(binds != NULL || nb == 0u);
    if (strcmp(op, "srmech.amsc.cascade.one.one_matrix") == 0) {
        return mc_one_matrix(a, binds, nb);        /* rc331: the field-DICT thunk */
    }
    if (strncmp(op, "srmech.amsc.cascade.one.one_", 28) == 0) {
        return mc_one_const(a, op);
    }
    if (strncmp(op, "srmech.amsc.cascade.sedenion_register.sed_", 42) == 0) {
        return mc_vtable_sed(a, op + 42, binds, nb, args);
    }
    if (strncmp(op, "srmech.amsc.genome.", 19) == 0) {
        return mc_vtable_genome(a, op + 19, binds, nb, args);
    }
    return NULL;
}

/* ------------------------------------------------------------------
 * The method engine — dispatch one method (single op OR chain) + apply its
 * state route. rc201b realises ALL routes: PLAIN / returns="self" (rc201) +
 * appends / sets / mutates + the multi-op chain. *out_result is the value to
 * serialise; *out_fields is the POST-route field state (unchanged for a plain /
 * returns=self / read method, grown/replaced for appends / sets / mutates).
 * Returns 1 (dispatched) or 0 (DEFER — a leaf/route the vtable does not cover).
 * ------------------------------------------------------------------ */

/* Build a NEW state DICT copying `state` with the (fname,fnlen) field replaced
 * by `val` (the field MUST already exist — every route target is declared). */
static srmech_mval_t *mc_state_set(srmech_marshal_arena_t *a,
                                   const srmech_mval_t *state, const char *fname,
                                   uint32_t fnlen, srmech_mval_t *val)
{
    uint32_t n, i; int found = -1; srmech_mval_t *nd;
    assert(a != NULL && val != NULL);
    assert(fname != NULL);
    if (state == NULL || state->kind != SRMECH_MVAL_DICT) { return NULL; }
    n = state->n;
    nd = mc_dict(a, n);
    if (nd == NULL) { return NULL; }
    for (i = 0u; i < n; i++) {
        const srmech_mval_t *k = state->keys[i];
        nd->keys[i] = state->keys[i]; nd->items[i] = state->items[i];
        if (k != NULL && k->kind == SRMECH_MVAL_STR && k->slen == fnlen
            && memcmp(k->s, fname, fnlen) == 0) { found = (int)i; }
    }
    if (found < 0) { return NULL; }
    nd->items[found] = val;
    return nd;
}

/* New LIST = `old` items + [item] (the appends route). */
static srmech_mval_t *mc_list_append(srmech_marshal_arena_t *a,
                                     const srmech_mval_t *old, srmech_mval_t *item)
{
    uint32_t n, i; srmech_mval_t *nl;
    assert(a != NULL);
    assert(item != NULL);
    n = (old != NULL && old->kind == SRMECH_MVAL_LIST) ? old->n : 0u;
    nl = mc_list(a, n + 1u, 0);
    if (nl == NULL) { return NULL; }
    for (i = 0u; i < n; i++) { nl->items[i] = old->items[i]; }
    nl->items[n] = item;
    return nl;
}

/* Is `name`[0..len) one of the TOML string ARRAY `arr`'s entries? */
static int mc_name_in_arr(const srmech_toml_value_t *arr, const char *name, uint32_t len)
{
    uint32_t i;
    assert(name != NULL);
    assert(arr == NULL || arr->type <= SRMECH_TOML_TABLE);   /* valid TOML type */
    if (arr == NULL || arr->type != SRMECH_TOML_ARRAY) { return 0; }
    for (i = 0u; i < arr->u.arr.n; i++) {
        const char *s = NULL; uint32_t l = 0u;
        if (mc_toml_str(arr->u.arr.items[i], &s, &l) && l == len
            && memcmp(s, name, len) == 0) { return 1; }
    }
    return 0;
}

/* Resolve a chain stage's `binds` from (1) a prior stage's `as` scope, then (2)
 * the call args, then (3) the fields (mirrors _run_chain). 0 (defer) on miss. */
static int mc_resolve_chain_binds(const srmech_toml_value_t *bindsv,
                                  const char * const *snm, const uint32_t *snl,
                                  const srmech_mval_t * const *sval, uint32_t nsc,
                                  const srmech_mval_t *args, const srmech_mval_t *fields,
                                  const srmech_mval_t **out, uint32_t *n_out)
{
    uint32_t i, n;
    assert(out != NULL);
    assert(n_out != NULL);
    n = (bindsv != NULL && bindsv->type == SRMECH_TOML_ARRAY) ? bindsv->u.arr.n : 0u;
    if (n > MC_MAX_BINDS) { return 0; }
    for (i = 0u; i < n; i++) {
        const char *bs = NULL; uint32_t bl = 0u, m; char nm[64]; const srmech_mval_t *v = NULL;
        if (!mc_toml_str(bindsv->u.arr.items[i], &bs, &bl) || bl >= sizeof(nm)) { return 0; }
        memcpy(nm, bs, bl); nm[bl] = '\0';
        for (m = 0u; m < nsc; m++) { if (snl[m] == bl && memcmp(snm[m], nm, bl) == 0) {
            v = sval[m]; break; } }
        if (v == NULL) { v = mc_dict_get(args, nm); }
        if (v == NULL) { v = mc_dict_get(fields, nm); }
        if (v == NULL) { return 0; }
        out[i] = v;
    }
    *n_out = n;
    return 1;
}

/* Run a multi-op chain method: thread each stage's `as` result into a small
 * scope; the LAST stage's result is the method result. NULL (defer). */
static srmech_mval_t *mc_run_chain(srmech_marshal_arena_t *a,
                                   const srmech_toml_value_t *chain,
                                   const srmech_mval_t *args, const srmech_mval_t *fields)
{
    const char *snm[MC_MAX_SCOPE]; uint32_t snl[MC_MAX_SCOPE]; const srmech_mval_t *sval[MC_MAX_SCOPE];
    uint32_t nsc = 0u, s; srmech_mval_t *last = NULL;
    assert(a != NULL);
    assert(chain != NULL);
    if (chain->type != SRMECH_TOML_ARRAY || chain->u.arr.n == 0u
        || chain->u.arr.n > MC_MAX_SCOPE) { return NULL; }
    for (s = 0u; s < chain->u.arr.n; s++) {
        const srmech_toml_value_t *stage = chain->u.arr.items[s], *opv, *asv;
        const srmech_mval_t *binds[MC_MAX_BINDS]; uint32_t nb = 0u, op_len = 0u;
        const char *op = NULL, *as = NULL; uint32_t al = 0u; char opbuf[128];
        if (stage == NULL || stage->type != SRMECH_TOML_TABLE) { return NULL; }
        opv = srmech_toml_table_get(stage, "op");
        if (!mc_toml_str(opv, &op, &op_len) || op_len >= sizeof(opbuf)) { return NULL; }
        memcpy(opbuf, op, op_len); opbuf[op_len] = '\0';
        if (!mc_resolve_chain_binds(srmech_toml_table_get(stage, "binds"), snm, snl,
                                    sval, nsc, args, fields, binds, &nb)) { return NULL; }
        last = mc_vtable_call(a, opbuf, binds, nb, args);
        if (last == NULL) { return NULL; }
        asv = srmech_toml_table_get(stage, "as");
        if (asv != NULL && mc_toml_str(asv, &as, &al)) {
            if (nsc >= MC_MAX_SCOPE) { return NULL; }
            snm[nsc] = as; snl[nsc] = al; sval[nsc] = last; nsc++;
        }
    }
    return last;
}

/* Apply the mutates route: `res` is (ret, {field: new}); each update key must be
 * in the `mut` declared-field list; the state fields are replaced; ret emitted. */
static int mc_apply_mutates(srmech_marshal_arena_t *a, const srmech_toml_value_t *mut,
                            srmech_mval_t *res, const srmech_mval_t *fields,
                            srmech_mval_t **out_result, const srmech_mval_t **out_fields)
{
    const srmech_mval_t *upd; const srmech_mval_t *state; uint32_t i;
    assert(a != NULL && out_result != NULL && out_fields != NULL);
    assert(res != NULL && mut != NULL);
    if (res->kind != SRMECH_MVAL_LIST || res->n != 2u) { return 0; }
    upd = res->items[1];
    if (upd == NULL || upd->kind != SRMECH_MVAL_DICT || mut->type != SRMECH_TOML_ARRAY) {
        return 0;
    }
    state = fields;
    for (i = 0u; i < upd->n; i++) {
        const srmech_mval_t *k = upd->keys[i]; srmech_mval_t *ns;
        if (k == NULL || k->kind != SRMECH_MVAL_STR
            || !mc_name_in_arr(mut, k->s, k->slen)) { return 0; }
        ns = mc_state_set(a, state, k->s, k->slen, upd->items[i]);
        if (ns == NULL) { return 0; }
        state = ns;
    }
    *out_result = res->items[0];
    *out_fields = state;
    return 1;
}

/* Apply the appends (is_append=1) / sets (0) route: grow/replace one field. */
static int mc_apply_field(srmech_marshal_arena_t *a, const srmech_toml_value_t *route,
                          srmech_mval_t *res, const srmech_mval_t *fields, int is_append,
                          srmech_mval_t **out_result, const srmech_mval_t **out_fields)
{
    const char *fn = NULL; uint32_t fnl = 0u; srmech_mval_t *nv, *nstate;
    assert(a != NULL && out_result != NULL && out_fields != NULL);
    assert(res != NULL && route != NULL);
    if (!mc_toml_str(route, &fn, &fnl)) { return 0; }
    if (is_append) { nv = mc_list_append(a, mc_dict_get(fields, fn), res); }
    else { nv = res; }
    nstate = mc_state_set(a, fields, fn, fnl, nv);
    if (nv == NULL || nstate == NULL) { return 0; }
    *out_result = res; *out_fields = nstate;
    return 1;
}

static int mc_run_method(srmech_marshal_arena_t *a,
                         const srmech_toml_value_t *spec,
                         const srmech_mval_t *args, const srmech_mval_t *fields,
                         srmech_mval_t **out_result, const srmech_mval_t **out_fields)
{
    const srmech_toml_value_t *chain, *opv, *ret, *mut, *app, *set;
    const srmech_mval_t *binds[MC_MAX_BINDS]; const char *op = NULL;
    uint32_t op_len = 0u, nb = 0u; char opbuf[128]; srmech_mval_t *res;
    assert(a != NULL && out_result != NULL && out_fields != NULL);
    assert(a->cur <= a->end);
    if (spec == NULL || spec->type != SRMECH_TOML_TABLE) { return 0; }
    *out_fields = fields;
    chain = srmech_toml_table_get(spec, "chain");
    if (chain != NULL) { res = mc_run_chain(a, chain, args, fields); }
    else {
        opv = srmech_toml_table_get(spec, "op");
        if (!mc_toml_str(opv, &op, &op_len) || op_len >= sizeof(opbuf)) { return 0; }
        memcpy(opbuf, op, op_len); opbuf[op_len] = '\0';
        if (!mc_resolve_binds(srmech_toml_table_get(spec, "binds"), args, fields,
                              binds, &nb)) { return 0; }
        res = mc_vtable_call(a, opbuf, binds, nb, args);
    }
    if (res == NULL) { return 0; }
    ret = srmech_toml_table_get(spec, "returns");
    mut = srmech_toml_table_get(spec, "mutates");
    app = srmech_toml_table_get(spec, "appends");
    set = srmech_toml_table_get(spec, "sets");
    if (ret != NULL) {
        const char *rs = NULL; uint32_t rl = 0u;
        if (!mc_toml_str(ret, &rs, &rl) || rl != 4u || memcmp(rs, "self", 4u) != 0
            || res->kind != SRMECH_MVAL_DICT) { return 0; }
        *out_result = res; return 1;
    }
    if (mut != NULL) { return mc_apply_mutates(a, mut, res, fields, out_result, out_fields); }
    if (app != NULL) { return mc_apply_field(a, app, res, fields, 1, out_result, out_fields); }
    if (set != NULL) { return mc_apply_field(a, set, res, fields, 0, out_result, out_fields); }
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
 * Emit {"class",<name>,"method",<method>,"result",<result>,"fields",<fields>}
 * as canonical JSON — the run_class_method 4-key wrap (rc202). Insertion-order
 * (NOT sorted-key), matching the pure run_class_method dict {"class","method",
 * "result","fields"}.
 * ------------------------------------------------------------------ */

static srmech_status_t mc_emit_named(srmech_marshal_arena_t *a,
                                     const char *class_name, const char *method,
                                     srmech_mval_t *result,
                                     const srmech_mval_t *fields,
                                     char *out, size_t out_cap, size_t *out_len)
{
    srmech_mval_t *obj;
    assert(a != NULL && result != NULL && out_len != NULL);
    assert(class_name != NULL && method != NULL);
    obj = mc_dict(a, 4u);
    if (obj == NULL) { return SRMECH_ERR_OVERFLOW; }
    obj->keys[0] = mc_str_copy(a, "class", 5u);
    obj->items[0] = mc_str_copy(a, class_name, (uint32_t)strlen(class_name));
    obj->keys[1] = mc_str_copy(a, "method", 6u);
    obj->items[1] = mc_str_copy(a, method, (uint32_t)strlen(method));
    obj->keys[2] = mc_str_copy(a, "result", 6u); obj->items[2] = result;
    obj->keys[3] = mc_str_copy(a, "fields", 6u);
    obj->items[3] = (srmech_mval_t *)fields;
    if (obj->keys[0] == NULL || obj->items[0] == NULL || obj->keys[1] == NULL
        || obj->items[1] == NULL || obj->keys[2] == NULL || obj->keys[3] == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    return srmech_mcp_serialise_result(obj, out, out_cap, out_len);
}

/* ------------------------------------------------------------------
 * The workspace bound + the PUBLIC prover entry.
 * ------------------------------------------------------------------ */

size_t srmech_make_class_run_arena_bytes(size_t toml_len, size_t fields_len,
                                         size_t args_len)
{
    /* The TOML tree (32x, the srmech_toml builder's node overhead) + the two
     * JSON trees + two mval trees + the rc201b heavy-leaf working carriers
     * (base64 decodes, minted vectors, bind/bundle parts, split chunk LISTs +
     * the rebuilt route state), generously over-allocated plus a fixed floor.
     * rc331 (#948): the floor also budgets the srmech_one_matrix workspace the
     * One.matrix() thunk carves here (~0.34 MiB at num_terms=50) so it dispatches
     * rather than OVERFLOW-defers. */
    size_t base = 131072u;
    assert(base > 0u);
    assert(base >= 131072u);
    return base + 128u * (toml_len + fields_len + args_len);
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

/* The shared spine of srmech_make_class_run + srmech_run_class_method: parse the
 * [class] TOML, resolve the `method` spec, parse the fields/args JSON maps, build
 * the field-state, dispatch. Writes (res, out_fields) over arena `a`. Returns 1
 * on a clean C dispatch, 0 to DEFER to pure (unparseable descriptor / unknown
 * method / unrepresentable input / a leaf the engine defers). */
static int mc_run_from_toml(srmech_marshal_arena_t *a,
                            const char *class_toml, size_t toml_len,
                            const char *method,
                            const char *fields_json, size_t fields_len,
                            const char *args_json, size_t args_len,
                            srmech_mval_t **res, const srmech_mval_t **out_fields)
{
    srmech_toml_value_t *root; const srmech_toml_value_t *spec;
    const srmech_toml_value_t *field_tbl = NULL;
    srmech_mval_t *fields, *args, *state; unsigned char *tws; size_t tws_len;
    assert(a != NULL && class_toml != NULL && method != NULL);
    assert(res != NULL && out_fields != NULL);
    tws_len = 32u * toml_len + 8192u;
    tws = mc_carve(a, tws_len);
    if (tws == NULL) { return 0; }
    if (srmech_toml_parse(class_toml, toml_len, tws, tws_len, &root) != SRMECH_OK) {
        return 0;                                  /* unparseable -> DEFER */
    }
    spec = mc_method_spec(root, method, &field_tbl);
    if (spec == NULL) { return 0; }                /* unknown method -> DEFER */
    if (!mc_parse_map(fields_json, fields_len, a, &fields)) { return 0; }
    if (!mc_parse_map(args_json, args_len, a, &args)) { return 0; }
    state = mc_build_fields(a, field_tbl, fields);
    if (state == NULL) { return 0; }
    *out_fields = state;
    return mc_run_method(a, spec, args, state, res, out_fields);
}

srmech_status_t srmech_make_class_run(const char *class_toml, size_t toml_len,
                                      const char *method,
                                      const char *fields_json, size_t fields_len,
                                      const char *args_json, size_t args_len,
                                      void *ws, size_t ws_len,
                                      char *out, size_t out_cap, size_t *out_len,
                                      int *out_kind)
{
    srmech_marshal_arena_t a; srmech_mval_t *res; const srmech_mval_t *out_fields;
    if (class_toml == NULL || method == NULL || ws == NULL || out == NULL
        || out_len == NULL || out_kind == NULL) { return SRMECH_ERR_NULL_ARG; }
    assert(ws_len > 0u);
    assert(out_cap > 0u);
    *out_kind = SRMECH_MAKE_CLASS_DEFER;
    srmech_marshal_arena_init(&a, ws, ws_len);
    if (!mc_run_from_toml(&a, class_toml, toml_len, method, fields_json, fields_len,
                          args_json, args_len, &res, &out_fields)) {
        return SRMECH_OK;                          /* DEFER to pure CatalogClass */
    }
    if (mc_emit(&a, res, out_fields, out, out_cap, out_len) != SRMECH_OK) {
        return SRMECH_OK;                          /* serialise overflow -> DEFER */
    }
    *out_kind = SRMECH_MAKE_CLASS_DISPATCHED;
    return SRMECH_OK;
}

/* ------------------------------------------------------------------
 * run_class_method (rc202) — the STATELESS one-shot: RESOLVE a class NAME to its
 * packaged descriptor (the compiled-in registry — no Python, no host-FS), run
 * one method through the engine, WRAP as {"class","method","result","fields"}.
 * The FINAL owed_orchestration row; discharge -> CEIL_NON_COMPUTE_OWED 1 -> 0.
 * ------------------------------------------------------------------ */

const char *srmech_class_descriptor_lookup(const char *name, size_t *out_len)
{
    size_t i;
    if (name == NULL) { return NULL; }
    assert(srmech_class_registry_table != NULL);
    assert(srmech_class_registry_len > 0u);
    for (i = 0u; i < srmech_class_registry_len; i++) {
        if (strcmp(srmech_class_registry_table[i].name, name) == 0) {
            if (out_len != NULL) {
                *out_len = srmech_class_registry_table[i].toml_len;
            }
            return srmech_class_registry_table[i].toml;
        }
    }
    return NULL;                                   /* unknown / user class */
}

size_t srmech_run_class_method_arena_bytes(const char *class_name,
                                           size_t fields_len, size_t args_len)
{
    size_t toml_len = 0u;
    if (class_name != NULL) {
        (void)srmech_class_descriptor_lookup(class_name, &toml_len);
    }
    assert(srmech_class_registry_len > 0u);
    assert(toml_len < ((size_t)1u << 40));         /* a descriptor is small + bounded */
    return srmech_make_class_run_arena_bytes(toml_len, fields_len, args_len);
}

srmech_status_t srmech_run_class_method(const char *class_name,
                                        const char *method,
                                        const char *fields_json, size_t fields_len,
                                        const char *args_json, size_t args_len,
                                        void *ws, size_t ws_len,
                                        char *out, size_t out_cap, size_t *out_len,
                                        int *out_kind)
{
    srmech_marshal_arena_t a; srmech_mval_t *res; const srmech_mval_t *out_fields;
    const char *class_toml; size_t toml_len = 0u;
    if (class_name == NULL || method == NULL || ws == NULL || out == NULL
        || out_len == NULL || out_kind == NULL) { return SRMECH_ERR_NULL_ARG; }
    assert(ws_len > 0u);
    assert(out_cap > 0u);
    *out_kind = SRMECH_MAKE_CLASS_DEFER;
    class_toml = srmech_class_descriptor_lookup(class_name, &toml_len);
    if (class_toml == NULL) { return SRMECH_OK; }  /* unknown / user class -> DEFER */
    srmech_marshal_arena_init(&a, ws, ws_len);
    if (!mc_run_from_toml(&a, class_toml, toml_len, method, fields_json, fields_len,
                          args_json, args_len, &res, &out_fields)) {
        return SRMECH_OK;                          /* method defers -> pure */
    }
    if (mc_emit_named(&a, class_name, method, res, out_fields,
                      out, out_cap, out_len) != SRMECH_OK) {
        return SRMECH_OK;                          /* serialise overflow -> DEFER */
    }
    *out_kind = SRMECH_MAKE_CLASS_DISPATCHED;
    return SRMECH_OK;
}
