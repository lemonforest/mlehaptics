/* srmech_invoke.c — the MCP tools/call DISPATCH SPINE in C (0.9.0rc188).
 *
 * This is the rc that makes MCP `tools/call` genuinely RUN in C. It is the C
 * peer of the compute half of srmech.mcp._tools.invoke_tool:
 *
 *   registry_find (rc184)                       -- resolve the dotted tool name
 *     -> per-arg srmech_mcp_marshal_arg (rc187)  -- JSON args -> typed carriers
 *       -> a SIGNATURE-SHAPE-batched thunk table  -- tool name -> the C kernel
 *         -> serialise the result carrier          -- typed value -> result text
 *
 * The thunk table batches BY SIGNATURE SHAPE (a thunk per shape switches on the
 * tool name to pick the bespoke C kernel + its exact ws-bound / out-param
 * signature), NOT per op — the clean, extensible pattern rc189+ widens. Batch 1
 * = the CLEAN scalar / hash / byte families whose kernels take only int / bytes
 * and whose result serialises to the SAME text as the pure path:
 *
 *   uN -> u   : cyclic.{gcd,lcm,mod_add,mod_mul,mod_pow,mod_inv,three_cycle},
 *               primes.next_prime, cascade.cyclic_gcd   (int result)
 *   u  -> bool: primes.is_prime
 *   uN -> pair: rational.best_rational                  (tuple[int,int] result)
 *   u  -> list: primes.factor                           (list[[p,e]] result)
 *   bytes -> hex str : format.sha256_bytes
 *   ...   -> bytes   : tlv.tlv_pack, hdc.bind, hdc.permute, dispatch.mirror_pattern
 *   bytes,bytes -> int|null : hdc.hamming, search.byte_search{,_backward}
 *
 * A tool NOT in the thunk table, an unregistered name, an EXTRA or MALFORMED
 * argument, an out-of-domain / kernel-error input, or a result that would not
 * fit int64 -> *out_kind = SRMECH_INVOKE_DEFER and the caller runs the COMPLETE
 * pure Python invoke_tool + attests (rc103 inform-don't-limit — never a wrong
 * answer). A cleanly-dispatched tool -> *out_kind = SRMECH_INVOKE_DISPATCHED and
 * `buf` holds the result TEXT byte-identical to serialise_result(...).
 *
 * RESULT-TEXT PARITY (the subtle bit). The pure serialise_result is
 * json.dumps(serialise_native(x))  with the json.dumps DEFAULT separators
 * (", " and ": "), NOT the compact form. For a SCALAR result (int/bool/string/
 * bytes-as-base64/null) there is no separator, so srmech_mcp_serialise_result
 * (compact) is byte-identical to the default form and is reused. Only the two
 * CONTAINER results (best_rational's pair, factor's list of pairs) carry a
 * separator; those go through iv_emit_spaced, a small default-separator emitter
 * over the integer-only shapes the thunks produce (a ", " between elements).
 *
 * JPL Power-of-Ten: caller-arena only (no malloc), <=60-line functions, >=2
 * asserts on INVARIANTS (runtime-NULL-checked params return NULL_ARG BEFORE any
 * assert), no goto, no recursion past the bounded (depth <= 2) integer-list
 * emitter, no abs/libm. Additive symbols -> SRMECH_ABI_VERSION stays 4. */

#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "srmech.h"

/* The batch-1 tools all have <= 3 parameters; 8 is comfortable headroom. */
#define IV_MAX_PARAMS 8

/* ------------------------------------------------------------------
 * Arena carve (void*-aligned bump; the srmech_marshal_arena_t is public).
 * ------------------------------------------------------------------ */

static unsigned char *iv_align(unsigned char *p)
{
    uintptr_t a = (uintptr_t)sizeof(void *);
    uintptr_t pad;
    assert(p != NULL);
    assert(a >= 4u);
    pad = (a - ((uintptr_t)p % a)) % a;
    return p + pad;
}

static unsigned char *iv_carve(srmech_marshal_arena_t *a, size_t n)
{
    unsigned char *p;
    assert(a != NULL);
    assert(a->cur <= a->end);
    p = iv_align(a->cur);
    if (p > a->end || n > (size_t)(a->end - p)) { return NULL; }
    a->cur = p + n;
    return p;
}

/* ------------------------------------------------------------------
 * Result-carrier constructors — one node per call, zeroed then set.
 * ------------------------------------------------------------------ */

static srmech_mval_t *iv_new(srmech_marshal_arena_t *a, srmech_mval_kind_t kind)
{
    srmech_mval_t *v;
    assert(a != NULL);
    assert(kind >= SRMECH_MVAL_NONE && kind <= SRMECH_MVAL_DICT);
    v = (srmech_mval_t *)iv_carve(a, sizeof(srmech_mval_t));
    if (v == NULL) { return NULL; }
    v->kind = kind; v->i = 0; v->re = 0.0; v->im = 0.0;
    v->s = NULL; v->slen = 0u; v->b = NULL; v->blen = 0u;
    v->items = NULL; v->keys = NULL; v->n = 0u; v->is_tuple = 0;
    return v;
}

static srmech_mval_t *iv_int(srmech_marshal_arena_t *a, int64_t x)
{
    srmech_mval_t *v = iv_new(a, SRMECH_MVAL_INT);
    assert(a != NULL);
    assert(a->cur <= a->end);
    if (v != NULL) { v->i = x; }
    return v;
}

static srmech_mval_t *iv_bool(srmech_marshal_arena_t *a, int truth)
{
    srmech_mval_t *v = iv_new(a, SRMECH_MVAL_BOOL);
    assert(a != NULL);
    assert(a->cur <= a->end);
    if (v != NULL) { v->i = truth ? 1 : 0; }
    return v;
}

/* A STR node copying `len` bytes of `src` INTO the arena (persists). */
static srmech_mval_t *iv_str_copy(srmech_marshal_arena_t *a,
                                  const char *src, uint32_t len)
{
    srmech_mval_t *v; unsigned char *buf;
    assert(a != NULL);
    assert(src != NULL || len == 0u);
    v = iv_new(a, SRMECH_MVAL_STR);
    if (v == NULL) { return NULL; }
    if (len > 0u) {
        buf = iv_carve(a, len);
        if (buf == NULL) { return NULL; }
        memcpy(buf, src, len);
        v->s = (const char *)buf;
    } else {
        v->s = src;
    }
    v->slen = len;
    return v;
}

/* A BYTES node aliasing an arena buffer the kernel already wrote into. */
static srmech_mval_t *iv_bytes(srmech_marshal_arena_t *a,
                               const unsigned char *buf, uint32_t len)
{
    srmech_mval_t *v = iv_new(a, SRMECH_MVAL_BYTES);
    assert(a != NULL);
    assert(buf != NULL || len == 0u);
    if (v != NULL) { v->b = buf; v->blen = len; }
    return v;
}

/* A LIST (list or tuple) node with an item-pointer array sized for `n`. */
static srmech_mval_t *iv_list(srmech_marshal_arena_t *a, uint32_t n, int is_tuple)
{
    srmech_mval_t *v = iv_new(a, SRMECH_MVAL_LIST);
    assert(a != NULL);
    assert(a->cur <= a->end);
    if (v == NULL) { return NULL; }
    v->is_tuple = is_tuple ? 1 : 0;
    v->n = n;
    if (n > 0u) {
        v->items = (srmech_mval_t **)iv_carve(a, (size_t)n * sizeof(void *));
        if (v->items == NULL) { return NULL; }
    }
    return v;
}

/* ------------------------------------------------------------------
 * Argument accessors — a marshalled carrier -> a typed C value, or 0 (defer).
 * ------------------------------------------------------------------ */

/* A non-negative INT carrier -> uint64 (JSON ints parse to int64, so a
 * non-negative one always fits uint64). Returns 0 (defer) otherwise. */
static int iv_arg_u64(const srmech_mval_t *v, uint64_t *out)
{
    assert(out != NULL);
    if (v == NULL || v->kind != SRMECH_MVAL_INT || v->i < 0) { return 0; }
    assert(v->kind == SRMECH_MVAL_INT && v->i >= 0);    /* post-guard invariant */
    *out = (uint64_t)v->i;
    return 1;
}

/* A BYTES carrier -> (ptr, len). An empty buffer yields a NULL ptr (len 0),
 * matching the kernels' "no bytes to read" contract. Returns 0 otherwise. */
static int iv_arg_bytes(const srmech_mval_t *v,
                        const unsigned char **ptr, uint32_t *len)
{
    assert(ptr != NULL && len != NULL);
    if (v == NULL || v->kind != SRMECH_MVAL_BYTES) { return 0; }
    assert(v->kind == SRMECH_MVAL_BYTES);               /* post-guard invariant */
    *len = v->blen;
    *ptr = (v->blen > 0u) ? v->b : NULL;
    return 1;
}

/* Wrap a uint64 kernel result as an INT carrier, DEFERRING if it does not fit
 * int64 (the mval INT is int64; a larger value serialises differently in C
 * than in Python's arbitrary-precision int, so defer to pure). */
static srmech_status_t iv_result_u(srmech_marshal_arena_t *a, uint64_t r,
                                   srmech_mval_t **out)
{
    assert(a != NULL && out != NULL);
    if (r > (uint64_t)INT64_MAX) { return SRMECH_ERR_NOT_IMPL; }
    assert(r <= (uint64_t)INT64_MAX);                   /* post-guard: fits int64 */
    *out = iv_int(a, (int64_t)r);
    return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* ------------------------------------------------------------------
 * Shape thunk: uN -> u  (1-3 non-negative int args -> one int result).
 * ------------------------------------------------------------------ */

static srmech_status_t iv_call_uN(const char *nm, uint64_t x0, uint64_t x1,
                                  uint64_t x2, uint32_t argc, uint64_t *r)
{
    assert(nm != NULL && r != NULL);
    assert(argc >= 1u && argc <= 3u);
    if (argc == 2u && strcmp(nm, "srmech.amsc.cyclic.gcd") == 0) {
        return srmech_gcd(x0, x1, r);
    }
    if (argc == 2u && strcmp(nm, "srmech.amsc.cascade.cyclic_gcd") == 0) {
        return srmech_cascade_cyclic_gcd_u64(x0, x1, r);
    }
    if (argc == 2u && strcmp(nm, "srmech.amsc.cyclic.lcm") == 0) {
        return srmech_lcm(x0, x1, r);
    }
    if (argc == 3u && strcmp(nm, "srmech.amsc.cyclic.mod_add") == 0) {
        return srmech_mod_add(x0, x1, x2, r);
    }
    if (argc == 3u && strcmp(nm, "srmech.amsc.cyclic.mod_mul") == 0) {
        return srmech_mod_mul(x0, x1, x2, r);
    }
    if (argc == 3u && strcmp(nm, "srmech.amsc.cyclic.mod_pow") == 0) {
        return srmech_mod_pow(x0, x1, x2, r);
    }
    if (argc == 2u && strcmp(nm, "srmech.amsc.cyclic.mod_inv") == 0) {
        return srmech_mod_inv(x0, x1, r);
    }
    if (argc == 1u && strcmp(nm, "srmech.amsc.cyclic.three_cycle") == 0) {
        return srmech_three_cycle(x0, r);
    }
    if (argc == 1u && strcmp(nm, "srmech.amsc.primes.next_prime") == 0) {
        return srmech_next_prime(x0, r);
    }
    return SRMECH_ERR_NOT_IMPL;
}

static srmech_status_t iv_shape_uN_to_u(const srmech_tool_entry_t *e,
                                        srmech_mval_t **argv, uint32_t argc,
                                        srmech_marshal_arena_t *a,
                                        srmech_mval_t **out)
{
    uint64_t x[3] = { 0u, 0u, 0u }, r = 0u; uint32_t i; srmech_status_t st;
    assert(e != NULL && argv != NULL && a != NULL && out != NULL);
    assert(argc >= 1u);
    if (argc > 3u) { return SRMECH_ERR_NOT_IMPL; }
    for (i = 0u; i < argc; i++) {
        if (!iv_arg_u64(argv[i], &x[i])) { return SRMECH_ERR_NOT_IMPL; }
    }
    st = iv_call_uN(e->name, x[0], x[1], x[2], argc, &r);
    if (st != SRMECH_OK) { return SRMECH_ERR_NOT_IMPL; } /* kernel error -> pure */
    return iv_result_u(a, r, out);
}

/* ------------------------------------------------------------------
 * Shape thunk: u -> bool  (primes.is_prime).
 * ------------------------------------------------------------------ */

static srmech_status_t iv_shape_u_to_bool(const srmech_tool_entry_t *e,
                                          srmech_mval_t **argv, uint32_t argc,
                                          srmech_marshal_arena_t *a,
                                          srmech_mval_t **out)
{
    uint64_t n = 0u; bool r = false; srmech_status_t st;
    assert(e != NULL && argv != NULL && a != NULL && out != NULL);
    assert(argc >= 1u);
    if (argc != 1u || strcmp(e->name, "srmech.amsc.primes.is_prime") != 0) {
        return SRMECH_ERR_NOT_IMPL;
    }
    if (!iv_arg_u64(argv[0], &n)) { return SRMECH_ERR_NOT_IMPL; }
    st = srmech_is_prime(n, &r);
    if (st != SRMECH_OK) { return SRMECH_ERR_NOT_IMPL; }
    *out = iv_bool(a, r ? 1 : 0);
    return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* ------------------------------------------------------------------
 * Shape thunk: uN -> (int, int) pair  (rational.best_rational).
 * ------------------------------------------------------------------ */

static srmech_status_t iv_shape_u_to_pair(const srmech_tool_entry_t *e,
                                          srmech_mval_t **argv, uint32_t argc,
                                          srmech_marshal_arena_t *a,
                                          srmech_mval_t **out)
{
    uint64_t p = 0u, q = 0u, md = 0u, op = 0u, oq = 0u; srmech_status_t st;
    srmech_mval_t *tup, *n0, *n1;
    assert(e != NULL && argv != NULL && a != NULL && out != NULL);
    assert(argc >= 1u);
    if (argc != 3u || strcmp(e->name, "srmech.amsc.rational.best_rational") != 0) {
        return SRMECH_ERR_NOT_IMPL;
    }
    if (!iv_arg_u64(argv[0], &p) || !iv_arg_u64(argv[1], &q)
        || !iv_arg_u64(argv[2], &md)) { return SRMECH_ERR_NOT_IMPL; }
    st = srmech_best_rational(p, q, md, &op, &oq);
    if (st != SRMECH_OK) { return SRMECH_ERR_NOT_IMPL; }
    if (op > (uint64_t)INT64_MAX || oq > (uint64_t)INT64_MAX) {
        return SRMECH_ERR_NOT_IMPL;
    }
    tup = iv_list(a, 2u, 1);
    n0 = iv_int(a, (int64_t)op); n1 = iv_int(a, (int64_t)oq);
    if (tup == NULL || n0 == NULL || n1 == NULL) { return SRMECH_ERR_OVERFLOW; }
    tup->items[0] = n0; tup->items[1] = n1; *out = tup;
    return SRMECH_OK;
}

/* ------------------------------------------------------------------
 * Shape thunk: u -> list[(int, int)]  (primes.factor).
 * ------------------------------------------------------------------ */

static srmech_status_t iv_shape_u_to_factor(const srmech_tool_entry_t *e,
                                            srmech_mval_t **argv, uint32_t argc,
                                            srmech_marshal_arena_t *a,
                                            srmech_mval_t **out)
{
    uint64_t n = 0u, primes[64]; uint8_t exps[64]; uint32_t cnt = 0u, i;
    srmech_mval_t *lst; srmech_status_t st;
    assert(e != NULL && argv != NULL && a != NULL && out != NULL);
    assert(argc >= 1u);
    if (argc != 1u || strcmp(e->name, "srmech.amsc.primes.factor") != 0) {
        return SRMECH_ERR_NOT_IMPL;
    }
    if (!iv_arg_u64(argv[0], &n)) { return SRMECH_ERR_NOT_IMPL; }
    st = srmech_factor(n, primes, exps, 64u, &cnt);
    if (st != SRMECH_OK) { return SRMECH_ERR_NOT_IMPL; }
    lst = iv_list(a, cnt, 0);
    if (lst == NULL) { return SRMECH_ERR_OVERFLOW; }
    for (i = 0u; i < cnt; i++) {
        srmech_mval_t *pr = iv_list(a, 2u, 1);
        srmech_mval_t *pv = iv_int(a, (int64_t)primes[i]);
        srmech_mval_t *ev = iv_int(a, (int64_t)exps[i]);
        if (pr == NULL || pv == NULL || ev == NULL) { return SRMECH_ERR_OVERFLOW; }
        pr->items[0] = pv; pr->items[1] = ev; lst->items[i] = pr;
    }
    *out = lst;
    return SRMECH_OK;
}

/* ------------------------------------------------------------------
 * Shape thunk: bytes -> hex str  (format.sha256_bytes).
 * ------------------------------------------------------------------ */

static srmech_status_t iv_shape_bytes_to_hex(const srmech_tool_entry_t *e,
                                             srmech_mval_t **argv, uint32_t argc,
                                             srmech_marshal_arena_t *a,
                                             srmech_mval_t **out)
{
    const unsigned char *p = NULL; uint32_t n = 0u; char hex[65]; srmech_status_t st;
    assert(e != NULL && argv != NULL && a != NULL && out != NULL);
    assert(argc >= 1u);
    if (argc != 1u || strcmp(e->name, "srmech.amsc.format.sha256_bytes") != 0) {
        return SRMECH_ERR_NOT_IMPL;
    }
    if (!iv_arg_bytes(argv[0], &p, &n)) { return SRMECH_ERR_NOT_IMPL; }
    st = srmech_sha256_hex(p, (size_t)n, hex);
    if (st != SRMECH_OK) { return SRMECH_ERR_NOT_IMPL; }
    *out = iv_str_copy(a, hex, 64u);
    return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* ------------------------------------------------------------------
 * Shape thunk: ... -> bytes  (tlv_pack / hdc.bind / hdc.permute / mirror).
 * ------------------------------------------------------------------ */

static srmech_status_t iv_shape_to_bytes(const srmech_tool_entry_t *e,
                                         srmech_mval_t **argv, uint32_t argc,
                                         srmech_marshal_arena_t *a,
                                         srmech_mval_t **out)
{
    const char *nm = e->name; const unsigned char *pa = NULL, *pb = NULL;
    uint32_t la = 0u, lb = 0u; unsigned char *ob; uint64_t tag = 0u, rot = 0u;
    srmech_status_t st; uint32_t written = 0u;
    assert(e != NULL && argv != NULL && a != NULL && out != NULL);
    assert(argc >= 1u);
    if (argc == 2u && strcmp(nm, "srmech.amsc.tlv.tlv_pack") == 0) {
        if (!iv_arg_u64(argv[0], &tag) || tag > 255u) { return SRMECH_ERR_NOT_IMPL; }
        if (!iv_arg_bytes(argv[1], &pb, &lb)) { return SRMECH_ERR_NOT_IMPL; }
        ob = iv_carve(a, (size_t)lb + 5u);
        if (ob == NULL) { return SRMECH_ERR_OVERFLOW; }
        st = srmech_tlv_pack((uint8_t)tag, pb, lb, ob, lb + 5u, &written);
        if (st != SRMECH_OK) { return SRMECH_ERR_NOT_IMPL; }
        *out = iv_bytes(a, ob, written);
    } else if (argc == 2u && strcmp(nm, "srmech.amsc.hdc.bind") == 0) {
        if (!iv_arg_bytes(argv[0], &pa, &la) || !iv_arg_bytes(argv[1], &pb, &lb)) {
            return SRMECH_ERR_NOT_IMPL;
        }
        if (la == 0u || la != lb) { return SRMECH_ERR_NOT_IMPL; } /* len mismatch -> pure */
        ob = iv_carve(a, la);
        if (ob == NULL) { return SRMECH_ERR_OVERFLOW; }
        st = srmech_hdc_bind(pa, pb, la, ob);
        if (st != SRMECH_OK) { return SRMECH_ERR_NOT_IMPL; }
        *out = iv_bytes(a, ob, la);
    } else if (argc == 2u && strcmp(nm, "srmech.amsc.hdc.permute") == 0) {
        if (!iv_arg_bytes(argv[0], &pa, &la) || la == 0u) { return SRMECH_ERR_NOT_IMPL; }
        if (!iv_arg_u64(argv[1], &rot) || rot > (uint64_t)INT32_MAX) {
            return SRMECH_ERR_NOT_IMPL;
        }
        ob = iv_carve(a, la);
        if (ob == NULL) { return SRMECH_ERR_OVERFLOW; }
        st = srmech_hdc_permute(pa, la, (int32_t)rot, ob);
        if (st != SRMECH_OK) { return SRMECH_ERR_NOT_IMPL; }
        *out = iv_bytes(a, ob, la);
    } else if (argc == 1u && strcmp(nm, "srmech.amsc.dispatch.mirror_pattern") == 0) {
        if (!iv_arg_bytes(argv[0], &pa, &la) || la == 0u) { return SRMECH_ERR_NOT_IMPL; }
        ob = iv_carve(a, la);
        if (ob == NULL) { return SRMECH_ERR_OVERFLOW; }
        st = srmech_mirror_pattern(pa, la, ob);
        if (st != SRMECH_OK) { return SRMECH_ERR_NOT_IMPL; }
        *out = iv_bytes(a, ob, la);
    } else {
        return SRMECH_ERR_NOT_IMPL;
    }
    return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* ------------------------------------------------------------------
 * Shape thunk: bytes, bytes -> int | null  (hamming / byte_search{,_backward}).
 * ------------------------------------------------------------------ */

static srmech_status_t iv_shape_bytes2_to_int(const srmech_tool_entry_t *e,
                                              srmech_mval_t **argv, uint32_t argc,
                                              srmech_marshal_arena_t *a,
                                              srmech_mval_t **out)
{
    const char *nm = e->name; const unsigned char *pa = NULL, *pb = NULL;
    uint32_t la = 0u, lb = 0u, off = 0u, ham = 0u; srmech_status_t st;
    assert(e != NULL && argv != NULL && a != NULL && out != NULL);
    assert(nm != NULL);
    if (argc != 2u) { return SRMECH_ERR_NOT_IMPL; } /* runtime contract (NDEBUG-safe) */
    if (!iv_arg_bytes(argv[0], &pa, &la) || !iv_arg_bytes(argv[1], &pb, &lb)) {
        return SRMECH_ERR_NOT_IMPL;
    }
    if (strcmp(nm, "srmech.amsc.hdc.hamming") == 0) {
        if (la == 0u || la != lb) { return SRMECH_ERR_NOT_IMPL; }
        st = srmech_hdc_hamming(pa, pb, la, &ham);
        if (st != SRMECH_OK) { return SRMECH_ERR_NOT_IMPL; }
        *out = iv_int(a, (int64_t)ham);
    } else if (strcmp(nm, "srmech.amsc.search.byte_search") == 0) {
        st = srmech_byte_search(pa, la, pb, lb, &off);
        if (st != SRMECH_OK) { return SRMECH_ERR_NOT_IMPL; }
        *out = (off == 0xFFFFFFFFu) ? iv_new(a, SRMECH_MVAL_NONE)
                                    : iv_int(a, (int64_t)off);
    } else if (strcmp(nm, "srmech.amsc.search.byte_search_backward") == 0) {
        st = srmech_byte_search_backward(pa, la, pb, lb, &off);
        if (st != SRMECH_OK) { return SRMECH_ERR_NOT_IMPL; }
        *out = (off == 0xFFFFFFFFu) ? iv_new(a, SRMECH_MVAL_NONE)
                                    : iv_int(a, (int64_t)off);
    } else {
        return SRMECH_ERR_NOT_IMPL;
    }
    return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* ------------------------------------------------------------------
 * The thunk VTABLE — tool name -> the signature-shape thunk. A name NOT here
 * has no C kernel this rc -> the caller defers to pure (inform-don't-limit).
 * ------------------------------------------------------------------ */

typedef srmech_status_t (*iv_thunk_t)(const srmech_tool_entry_t *,
                                      srmech_mval_t **, uint32_t,
                                      srmech_marshal_arena_t *, srmech_mval_t **);

typedef struct { const char *name; iv_thunk_t thunk; } iv_vtable_row_t;

static const iv_vtable_row_t IV_VTABLE[] = {
    { "srmech.amsc.cyclic.gcd",              iv_shape_uN_to_u },
    { "srmech.amsc.cyclic.lcm",              iv_shape_uN_to_u },
    { "srmech.amsc.cyclic.mod_add",          iv_shape_uN_to_u },
    { "srmech.amsc.cyclic.mod_mul",          iv_shape_uN_to_u },
    { "srmech.amsc.cyclic.mod_pow",          iv_shape_uN_to_u },
    { "srmech.amsc.cyclic.mod_inv",          iv_shape_uN_to_u },
    { "srmech.amsc.cyclic.three_cycle",      iv_shape_uN_to_u },
    { "srmech.amsc.cascade.cyclic_gcd",      iv_shape_uN_to_u },
    { "srmech.amsc.primes.next_prime",       iv_shape_uN_to_u },
    { "srmech.amsc.primes.is_prime",         iv_shape_u_to_bool },
    { "srmech.amsc.rational.best_rational",  iv_shape_u_to_pair },
    { "srmech.amsc.primes.factor",           iv_shape_u_to_factor },
    { "srmech.amsc.format.sha256_bytes",     iv_shape_bytes_to_hex },
    { "srmech.amsc.tlv.tlv_pack",            iv_shape_to_bytes },
    { "srmech.amsc.hdc.bind",                iv_shape_to_bytes },
    { "srmech.amsc.hdc.permute",             iv_shape_to_bytes },
    { "srmech.amsc.dispatch.mirror_pattern", iv_shape_to_bytes },
    { "srmech.amsc.hdc.hamming",             iv_shape_bytes2_to_int },
    { "srmech.amsc.search.byte_search",      iv_shape_bytes2_to_int },
    { "srmech.amsc.search.byte_search_backward", iv_shape_bytes2_to_int },
};

static iv_thunk_t iv_vtable_lookup(const char *name)
{
    size_t i, n = sizeof IV_VTABLE / sizeof IV_VTABLE[0];
    assert(name != NULL);
    assert(n > 0u);
    for (i = 0u; i < n; i++) {
        if (strcmp(IV_VTABLE[i].name, name) == 0) { return IV_VTABLE[i].thunk; }
    }
    return NULL;
}

/* ------------------------------------------------------------------
 * Result serialisation. A SCALAR carrier goes through the compact rc187
 * srmech_mcp_serialise_result (byte-identical to the json.dumps default form
 * for a value with no separator); a LIST carrier (best_rational / factor) goes
 * through iv_emit_spaced — the DEFAULT-separator (", ") integer-list emitter
 * that matches serialise_result's json.dumps(...) default form exactly.
 * ------------------------------------------------------------------ */

typedef struct { char *buf; size_t cap; size_t used; int overflow; } iv_emit_t;

static void iv_raw(iv_emit_t *e, const char *s, size_t n)
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

static void iv_emit_i64(iv_emit_t *e, int64_t v)
{
    char tmp[24]; int n;
    assert(e != NULL);
    assert(sizeof tmp >= 21u);
    n = snprintf(tmp, sizeof tmp, "%lld", (long long)v);
    if (n < 0) { e->overflow = 1; return; }
    iv_raw(e, tmp, (size_t)n);
}

/* Emit an INT, or a nested LIST of INT, with the json.dumps DEFAULT ", "
 * separator. Depth is bounded (<= 2: a list-of-int-pairs is the deepest the
 * batch-1 thunks produce); a deeper / non-integer node latches overflow. */
static void iv_emit_node(iv_emit_t *e, const srmech_mval_t *v, uint32_t depth)
{
    uint32_t k;
    assert(e != NULL);
    assert(depth <= 2u);
    if (v == NULL || depth > 2u) { e->overflow = 1; return; }
    if (v->kind == SRMECH_MVAL_INT) { iv_emit_i64(e, v->i); return; }
    if (v->kind != SRMECH_MVAL_LIST) { e->overflow = 1; return; }
    iv_raw(e, "[", 1u);
    for (k = 0u; k < v->n; k++) {
        if (k > 0u) { iv_raw(e, ", ", 2u); }
        iv_emit_node(e, v->items[k], depth + 1u);
    }
    iv_raw(e, "]", 1u);
}

static srmech_status_t iv_emit_spaced(const srmech_mval_t *v, char *buf,
                                      size_t buf_len, size_t *out_len)
{
    iv_emit_t e;
    assert(v != NULL && out_len != NULL);              /* buf==NULL is a size-query */
    assert(v->kind == SRMECH_MVAL_LIST);
    e.buf = buf; e.cap = (buf == NULL) ? 0u : buf_len; e.used = 0u; e.overflow = 0;
    iv_emit_node(&e, v, 0u);
    *out_len = e.used;
    return e.overflow ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

static srmech_status_t iv_serialise(const srmech_mval_t *v, char *buf,
                                    size_t buf_len, size_t *out_len)
{
    assert(v != NULL && out_len != NULL);              /* buf==NULL is a size-query */
    assert(v->kind >= SRMECH_MVAL_NONE && v->kind <= SRMECH_MVAL_DICT);
    if (v->kind == SRMECH_MVAL_LIST) {
        return iv_emit_spaced(v, buf, buf_len, out_len);
    }
    return srmech_mcp_serialise_result(v, buf, buf_len, out_len);
}

/* ------------------------------------------------------------------
 * Argument marshalling — the arguments OBJECT -> a typed carrier per registry
 * param (in registry order). An EXTRA key (not a registry param) defers the
 * whole call; a missing key leaves argv[i] = NULL (the thunk defers if it needs
 * it); a NOT_IMPL / BAD_INPUT marshal defers the whole call.
 * ------------------------------------------------------------------ */

/* 1 iff every key of the arguments object matches a registry param name. */
static int iv_no_extra_keys(const srmech_json_value_t *args,
                            const srmech_tool_entry_t *e)
{
    uint32_t i, j; int found;
    assert(args != NULL && e != NULL);
    assert(args->type == SRMECH_JSON_OBJECT);
    for (i = 0u; i < args->u.obj.n; i++) {
        found = 0;
        for (j = 0u; j < e->param_count; j++) {
            if (strcmp(args->u.obj.keys[i], e->params[j].name) == 0) { found = 1; break; }
        }
        if (!found) { return 0; }
    }
    return 1;
}

static srmech_status_t iv_marshal_args(const srmech_json_value_t *args,
                                       const srmech_tool_entry_t *e,
                                       srmech_marshal_arena_t *a,
                                       srmech_mval_t **argv)
{
    uint32_t i; srmech_status_t st;
    assert(args != NULL && e != NULL && a != NULL && argv != NULL);
    assert(args->type == SRMECH_JSON_OBJECT);
    for (i = 0u; i < e->param_count; i++) {
        const srmech_json_value_t *node =
            srmech_json_object_get(args, e->params[i].name);
        srmech_mval_t *raw = NULL;
        argv[i] = NULL;
        if (node == NULL) { continue; }                 /* absent -> thunk defers */
        st = srmech_mval_from_json(node, a, &raw);
        if (st != SRMECH_OK) { return st; }
        st = srmech_mcp_marshal_arg(e->params[i].type, raw, a, &argv[i]);
        if (st != SRMECH_OK) { return st; }             /* NOT_IMPL/BAD_INPUT -> defer */
    }
    return SRMECH_OK;
}

/* ------------------------------------------------------------------
 * The shared dispatch CORE — name + a (parsed) arguments OBJECT -> registry
 * find -> thunk lookup -> marshal args -> run the thunk -> serialise. A miss at
 * ANY stage sets SRMECH_INVOKE_DEFER (the caller runs the pure invoke_tool).
 * ------------------------------------------------------------------ */

static srmech_status_t iv_dispatch(const char *name,
                                   const srmech_json_value_t *args,
                                   srmech_marshal_arena_t *a,
                                   char *buf, size_t buf_len,
                                   size_t *out_len, int *out_kind)
{
    const srmech_tool_entry_t *entry; iv_thunk_t thunk;
    srmech_mval_t *argv[IV_MAX_PARAMS]; srmech_mval_t *result = NULL;
    srmech_status_t st;
    assert(name != NULL && a != NULL);                 /* buf==NULL is a size-query */
    assert(out_len != NULL && out_kind != NULL);
    *out_len = 0u; *out_kind = SRMECH_INVOKE_DEFER;
    entry = srmech_tool_registry_find(name);
    if (entry == NULL) { return SRMECH_OK; }            /* unregistered -> pure */
    thunk = iv_vtable_lookup(name);
    if (thunk == NULL || entry->param_count > IV_MAX_PARAMS) { return SRMECH_OK; }
    if (args == NULL || args->type != SRMECH_JSON_OBJECT) { return SRMECH_OK; }
    if (!iv_no_extra_keys(args, entry)) { return SRMECH_OK; }
    if (iv_marshal_args(args, entry, a, argv) != SRMECH_OK) { return SRMECH_OK; }
    if (thunk(entry, argv, entry->param_count, a, &result) != SRMECH_OK
        || result == NULL) { return SRMECH_OK; }        /* defer on any thunk miss */
    st = iv_serialise(result, buf, buf_len, out_len);
    if (st != SRMECH_OK) { *out_len = 0u; return st; }  /* OVERFLOW -> caller sizes/defers */
    *out_kind = SRMECH_INVOKE_DISPATCHED;
    return SRMECH_OK;
}

/* ------------------------------------------------------------------
 * Entry points.
 * ------------------------------------------------------------------ */

size_t srmech_invoke_tool_arena_bytes(size_t params_len)
{
    assert(sizeof(srmech_mval_t) <= 128u);
    assert(sizeof(srmech_json_value_t) <= 128u);
    return 256u * params_len + 65536u;
}

/* The PARSED-args entry — the in-process srmech_mcp.c tools/call path passes the
 * already-parsed `arguments` node (no re-serialise / double parse). `ws` backs
 * the marshalled carriers + the result carrier. `arguments` NULL / non-object
 * -> DEFER (a tool with no supplied object cannot dispatch a clean batch-1 op). */
srmech_status_t srmech_invoke_tool_json(const char *name,
                                        const srmech_json_value_t *arguments,
                                        void *ws, size_t ws_len,
                                        char *buf, size_t buf_len,
                                        size_t *out_len, int *out_kind)
{
    srmech_marshal_arena_t a;
    /* buf==NULL is a two-pass SIZE-QUERY, not an error (rc715 NULL-first). */
    if (name == NULL || ws == NULL
        || out_len == NULL || out_kind == NULL) { return SRMECH_ERR_NULL_ARG; }
    assert(ws_len > 0u);                                /* genuine arena invariant */
    assert(name != NULL && ws != NULL);                 /* guaranteed by NULL-check */
    srmech_marshal_arena_init(&a, ws, ws_len);
    return iv_dispatch(name, arguments, &a, buf, buf_len, out_len, out_kind);
}

/* The JSON-string entry — parses the `arguments` OBJECT from
 * `params_json[0..params_len)` into the front of `ws`, then dispatches over the
 * rest. Ctypes-drivable (the Python invoke_tool_c wrapper + the C driver). */
srmech_status_t srmech_invoke_tool(const char *name,
                                   const char *params_json, size_t params_len,
                                   void *ws, size_t ws_len,
                                   char *buf, size_t buf_len,
                                   size_t *out_len, int *out_kind)
{
    srmech_marshal_arena_t a; srmech_json_value_t *jroot = NULL;
    unsigned char *parse_ws; size_t pj; srmech_status_t st;
    /* buf==NULL is a two-pass SIZE-QUERY, not an error (rc715 NULL-first). */
    if (name == NULL || params_json == NULL || ws == NULL
        || out_len == NULL || out_kind == NULL) { return SRMECH_ERR_NULL_ARG; }
    assert(ws_len > 0u);                                /* genuine arena invariant */
    assert(name != NULL && params_json != NULL);        /* guaranteed by NULL-check */
    *out_len = 0u; *out_kind = SRMECH_INVOKE_DEFER;
    srmech_marshal_arena_init(&a, ws, ws_len);
    pj = 128u * params_len + 16384u;
    parse_ws = iv_carve(&a, pj);
    if (parse_ws == NULL) { return SRMECH_OK; }         /* too small -> pure */
    st = srmech_json_parse(params_json, params_len, parse_ws, pj, &jroot);
    if (st != SRMECH_OK) { return SRMECH_OK; }          /* malformed args -> pure */
    return iv_dispatch(name, jroot, &a, buf, buf_len, out_len, out_kind);
}
