/* srmech_invoke.c — the MCP tools/call DISPATCH SPINE in C (0.9.0rc188 spine;
 * 0.9.0rc189 widens the thunk vtable — CLEAN BATCH 2).
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
 * rc189 CLEAN BATCH 2 widens the SAME vtable with 12 more bucket-(a) tools in
 * new signature shapes (all reusing the rc187 marshal + the DEFER contract):
 *
 *   (int,int)->list[int]              : rational.continued_fraction
 *   list[int]->list[(int,int)]        : rational.continued_fraction_convergents
 *   (pair,pair)->pair / (pair,int)->pair : rational.rational_{add,mul,div,pow_uint}
 *   (int,int,int)->int                : primes.cyclic_period
 *   Sequence[bytes]->bytes            : hdc.bundle
 *   list[bytes]->list[str]            : format.sha256_batch  (hex digests)
 *   (bytes,list[(bytes,int)])->(bool,int) : dispatch.match
 *   (bytes,list[(bytes,bytes)])->bytes|null : naming.lookup
 *   (bytes,Mapping[bytes,bytes])->bytes   : template.render  (sorted keys)
 *
 * The rational / cyclic kernels DEFER on overflow (Python's bignum path), on
 * an out-of-domain input the pure wrapper would raise on (den<=0, n<2, a not
 * coprime to n, a negative arg), and on any value exceeding int64.
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

/* A signed INT carrier -> int64 (JSON ints parse to int64, so any INT fits).
 * Returns 0 (defer) for a non-INT / absent carrier. */
static int iv_arg_i64(const srmech_mval_t *v, int64_t *out)
{
    assert(out != NULL);
    if (v == NULL || v->kind != SRMECH_MVAL_INT) { return 0; }
    assert(v->kind == SRMECH_MVAL_INT);                 /* post-guard invariant */
    *out = v->i;
    return 1;
}

/* A 2-element INT tuple carrier (a marshalled tuple[int, int]) -> a rational
 * (num int64, den uint64 with den > 0). Mirrors the Python rational wrappers'
 * "denominators must be positive" pre-C guard; returns 0 (defer) otherwise. */
static int iv_arg_rat(const srmech_mval_t *v, int64_t *num, uint64_t *den)
{
    assert(num != NULL && den != NULL);
    if (v == NULL || v->kind != SRMECH_MVAL_LIST || v->n != 2u) { return 0; }
    if (v->items[0] == NULL || v->items[0]->kind != SRMECH_MVAL_INT) { return 0; }
    if (v->items[1] == NULL || v->items[1]->kind != SRMECH_MVAL_INT) { return 0; }
    if (v->items[1]->i <= 0) { return 0; }              /* den must be positive */
    assert(v->items[1]->i > 0);                         /* post-guard invariant */
    *num = v->items[0]->i;
    *den = (uint64_t)v->items[1]->i;
    return 1;
}

/* Build a reduced-rational (num, den) result as a 2-tuple [num, den] carrier
 * (the same shape best_rational emits). DEFERS if the uint64 den does not fit
 * int64 (Python serialises the big den exactly; the int64 carrier cannot). */
static srmech_status_t iv_result_rat(srmech_marshal_arena_t *a, int64_t num,
                                     uint64_t den, srmech_mval_t **out)
{
    srmech_mval_t *tup, *n0, *n1;
    assert(a != NULL && out != NULL);
    if (den > (uint64_t)INT64_MAX) { return SRMECH_ERR_NOT_IMPL; }
    assert(den <= (uint64_t)INT64_MAX);                 /* post-guard: fits int64 */
    tup = iv_list(a, 2u, 1);
    n0 = iv_int(a, num); n1 = iv_int(a, (int64_t)den);
    if (tup == NULL || n0 == NULL || n1 == NULL) { return SRMECH_ERR_OVERFLOW; }
    tup->items[0] = n0; tup->items[1] = n1; *out = tup;
    return SRMECH_OK;
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

/* ==================================================================
 * rc189 CLEAN BATCH 2 — more bucket-(a) c_dispatched tools, new shapes.
 * Each thunk marshals the typed argv, calls the bespoke C kernel, and
 * serialises byte-identically to serialise_result(invoke_tool(...)); a miss
 * / kernel-error / >int64 / arity mismatch DEFERS (out_kind=DEFER).
 * ================================================================== */

/* Carve an n-element uint32 array (offset / length / tag parallel arrays). */
static uint32_t *iv_carve_u32(srmech_marshal_arena_t *a, uint32_t n)
{
    assert(a != NULL);
    assert(n >= 1u);
    return (uint32_t *)iv_carve(a, (size_t)n * sizeof(uint32_t));
}

/* Write the 32-byte digest `dig` as 64 lowercase hex chars into out64 (NOT
 * NUL-terminated; the caller copies exactly 64 bytes). Mirrors bytes.hex(). */
static void iv_hex32(const unsigned char *dig, char *out64)
{
    static const char H[] = "0123456789abcdef";
    uint32_t i;
    assert(dig != NULL && out64 != NULL);
    assert(H[15] == 'f');
    for (i = 0u; i < 32u; i++) {
        out64[2u * i] = H[(dig[i] >> 4) & 0xFu];
        out64[2u * i + 1u] = H[dig[i] & 0xFu];
    }
}

/* Byte-lex compare of two BYTES carriers (memcmp with shorter-is-less prefix
 * tiebreak) -> <0 / 0 / >0 — Python bytes ordering / the catalog lex order. */
static int iv_bytes_cmp(const srmech_mval_t *x, const srmech_mval_t *y)
{
    uint32_t m, i; int c;
    assert(x != NULL && y != NULL);
    assert(x->b != NULL || x->blen == 0u);          /* a byte buffer is valid-or-empty */
    m = (x->blen < y->blen) ? x->blen : y->blen;
    for (i = 0u; i < m; i++) {
        c = (int)x->b[i] - (int)y->b[i];
        if (c != 0) { return c; }
    }
    if (x->blen < y->blen) { return -1; }
    return (x->blen > y->blen) ? 1 : 0;
}

/* Stable insertion-sort of n indices into `order` by their key carriers'
 * byte-lex order — matches Python sorted(items, key=lambda kv: kv[0]). */
static void iv_sort_order(const srmech_mval_t *const *keys, uint32_t n,
                          uint32_t *order)
{
    uint32_t i, j, key;
    assert(keys != NULL);
    assert(order != NULL);
    for (i = 0u; i < n; i++) { order[i] = i; }
    for (i = 1u; i < n; i++) {
        key = order[i]; j = i;
        while (j > 0u && iv_bytes_cmp(keys[order[j - 1u]], keys[key]) > 0) {
            order[j] = order[j - 1u]; j--;
        }
        order[j] = key;
    }
}

/* Pack n (key, value) BYTES carriers -> a keys buffer + a values buffer + the
 * (caller-carved, length-n) offset/length arrays, emitted in `order` (NULL =
 * identity). 0 (defer) on a non-BYTES leaf or arena exhaustion. */
static int iv_pack_kv(srmech_marshal_arena_t *a, uint32_t n,
                      const srmech_mval_t *const *keys,
                      const srmech_mval_t *const *vals, const uint32_t *order,
                      const unsigned char **kbuf, uint32_t *koff, uint32_t *klen,
                      const unsigned char **vbuf, uint32_t *voff, uint32_t *vlen)
{
    uint32_t i, kt = 0u, vt = 0u, kc = 0u, vc = 0u, idx; unsigned char *kb, *vb;
    assert(a != NULL && keys != NULL && vals != NULL);
    assert(kbuf != NULL && vbuf != NULL);
    for (i = 0u; i < n; i++) {
        idx = order ? order[i] : i;
        if (keys[idx] == NULL || keys[idx]->kind != SRMECH_MVAL_BYTES) { return 0; }
        if (vals[idx] == NULL || vals[idx]->kind != SRMECH_MVAL_BYTES) { return 0; }
        kt += keys[idx]->blen; vt += vals[idx]->blen;
    }
    kb = iv_carve(a, (kt == 0u) ? 1u : kt);
    vb = iv_carve(a, (vt == 0u) ? 1u : vt);
    if (kb == NULL || vb == NULL) { return 0; }
    for (i = 0u; i < n; i++) {
        const srmech_mval_t *k, *v; idx = order ? order[i] : i;
        k = keys[idx]; v = vals[idx];
        koff[i] = kc; klen[i] = k->blen;
        if (k->blen > 0u) { memcpy(kb + kc, k->b, k->blen); kc += k->blen; }
        voff[i] = vc; vlen[i] = v->blen;
        if (v->blen > 0u) { memcpy(vb + vc, v->b, v->blen); vc += v->blen; }
    }
    *kbuf = kb; *vbuf = vb;
    return 1;
}

/* Split a LIST of 2-tuple[BYTES, BYTES] carriers into parallel key / value
 * carrier-pointer arrays (arena-carved). 0 (defer) on a non-2-tuple / miss. */
static int iv_split_pairs(const srmech_mval_t *pairs, srmech_marshal_arena_t *a,
                          const srmech_mval_t ***keys, const srmech_mval_t ***vals)
{
    uint32_t n, i; const srmech_mval_t **k, **v;
    assert(pairs != NULL && a != NULL);
    assert(keys != NULL && vals != NULL);
    n = pairs->n;
    k = (const srmech_mval_t **)iv_carve(a, (size_t)(n ? n : 1u) * sizeof(void *));
    v = (const srmech_mval_t **)iv_carve(a, (size_t)(n ? n : 1u) * sizeof(void *));
    if (k == NULL || v == NULL) { return 0; }
    for (i = 0u; i < n; i++) {
        const srmech_mval_t *p = pairs->items[i];
        if (p == NULL || p->kind != SRMECH_MVAL_LIST || p->n != 2u) { return 0; }
        k[i] = p->items[0]; v[i] = p->items[1];
    }
    *keys = k; *vals = v;
    return 1;
}

/* Pack a LIST of tuple[BYTES, INT] rules -> a patterns buffer + the (caller-
 * carved) offset/length/tag arrays. 0 (defer) on shape / tag-range miss. */
static int iv_pack_rules(const srmech_mval_t *rules, srmech_marshal_arena_t *a,
                         const unsigned char **pbuf, uint32_t *offs,
                         uint32_t *lens, uint32_t *tags)
{
    uint32_t n, i, total = 0u, cur = 0u; unsigned char *buf;
    assert(rules != NULL && a != NULL);
    assert(pbuf != NULL && offs != NULL && lens != NULL && tags != NULL);
    n = rules->n;
    for (i = 0u; i < n; i++) {
        const srmech_mval_t *r = rules->items[i];
        if (r == NULL || r->kind != SRMECH_MVAL_LIST || r->n != 2u) { return 0; }
        if (r->items[0] == NULL || r->items[0]->kind != SRMECH_MVAL_BYTES) { return 0; }
        if (r->items[1] == NULL || r->items[1]->kind != SRMECH_MVAL_INT) { return 0; }
        if (r->items[1]->i < 0 || r->items[1]->i > (int64_t)0xFFFFFFFF) { return 0; }
        total += r->items[0]->blen;
    }
    buf = iv_carve(a, (total == 0u) ? 1u : total);
    if (buf == NULL) { return 0; }
    for (i = 0u; i < n; i++) {
        const srmech_mval_t *r = rules->items[i]; uint32_t bl = r->items[0]->blen;
        offs[i] = cur; lens[i] = bl; tags[i] = (uint32_t)r->items[1]->i;
        if (bl > 0u) { memcpy(buf + cur, r->items[0]->b, bl); cur += bl; }
    }
    *pbuf = buf;
    return 1;
}

/* ------------------------------------------------------------------
 * Shape thunk: (tuple[int,int], tuple[int,int]) -> tuple[int,int]
 *   rational.rational_{add,mul,div}   (int64 kernels; overflow -> pure bignum).
 * ------------------------------------------------------------------ */

static srmech_status_t iv_call_rat2(const char *nm, int64_t an, uint64_t ad,
                                    int64_t bn, uint64_t bd,
                                    int64_t *rn, uint64_t *rd)
{
    assert(nm != NULL && rn != NULL && rd != NULL);
    assert(ad > 0u && bd > 0u);                     /* positive denominators (pre-guarded) */
    if (strcmp(nm, "srmech.amsc.rational.rational_add") == 0) {
        return srmech_rational_add(an, ad, bn, bd, rn, rd);
    }
    if (strcmp(nm, "srmech.amsc.rational.rational_mul") == 0) {
        return srmech_rational_mul(an, ad, bn, bd, rn, rd);
    }
    if (strcmp(nm, "srmech.amsc.rational.rational_div") == 0) {
        return srmech_rational_div(an, ad, bn, bd, rn, rd);
    }
    return SRMECH_ERR_NOT_IMPL;
}

static srmech_status_t iv_shape_rat2_to_rat(const srmech_tool_entry_t *e,
                                            srmech_mval_t **argv, uint32_t argc,
                                            srmech_marshal_arena_t *a,
                                            srmech_mval_t **out)
{
    int64_t an = 0, bn = 0, rn = 0; uint64_t ad = 0u, bd = 0u, rd = 0u;
    srmech_status_t st;
    assert(e != NULL && argv != NULL && a != NULL && out != NULL);
    assert(argc >= 1u);
    if (argc != 2u) { return SRMECH_ERR_NOT_IMPL; }
    if (!iv_arg_rat(argv[0], &an, &ad) || !iv_arg_rat(argv[1], &bn, &bd)) {
        return SRMECH_ERR_NOT_IMPL;
    }
    st = iv_call_rat2(e->name, an, ad, bn, bd, &rn, &rd);
    if (st != SRMECH_OK) { return SRMECH_ERR_NOT_IMPL; }  /* overflow / div0 -> pure */
    return iv_result_rat(a, rn, rd, out);
}

/* ------------------------------------------------------------------
 * Shape thunk: (tuple[int,int], int) -> tuple[int,int]
 *   rational.rational_pow_uint  (exp 1..64 in C; 0 / <0 / >64 -> pure).
 * ------------------------------------------------------------------ */

static srmech_status_t iv_shape_rat_pow(const srmech_tool_entry_t *e,
                                        srmech_mval_t **argv, uint32_t argc,
                                        srmech_marshal_arena_t *a,
                                        srmech_mval_t **out)
{
    int64_t bn = 0, rn = 0, exp = 0; uint64_t bd = 0u, rd = 0u; srmech_status_t st;
    assert(e != NULL && argv != NULL && a != NULL && out != NULL);
    assert(argc >= 1u);
    if (argc != 2u
        || strcmp(e->name, "srmech.amsc.rational.rational_pow_uint") != 0) {
        return SRMECH_ERR_NOT_IMPL;
    }
    if (!iv_arg_rat(argv[0], &bn, &bd) || !iv_arg_i64(argv[1], &exp)) {
        return SRMECH_ERR_NOT_IMPL;
    }
    if (exp < 1 || exp > 64) { return SRMECH_ERR_NOT_IMPL; } /* 0->(1,1) / >64 bignum -> pure */
    st = srmech_rational_pow_uint(bn, bd, (uint32_t)exp, &rn, &rd);
    if (st != SRMECH_OK) { return SRMECH_ERR_NOT_IMPL; }
    return iv_result_rat(a, rn, rd, out);
}

/* ------------------------------------------------------------------
 * Shape thunk: (int, int) -> list[int]   rational.continued_fraction.
 * ------------------------------------------------------------------ */

static srmech_status_t iv_shape_cf(const srmech_tool_entry_t *e,
                                   srmech_mval_t **argv, uint32_t argc,
                                   srmech_marshal_arena_t *a, srmech_mval_t **out)
{
    uint64_t p = 0u, q = 0u; uint64_t terms[128]; uint32_t cnt = 0u, i;
    srmech_mval_t *lst; srmech_status_t st;
    assert(e != NULL && argv != NULL && a != NULL && out != NULL);
    assert(argc >= 1u);
    if (argc != 2u
        || strcmp(e->name, "srmech.amsc.rational.continued_fraction") != 0) {
        return SRMECH_ERR_NOT_IMPL;
    }
    if (!iv_arg_u64(argv[0], &p) || !iv_arg_u64(argv[1], &q)) { return SRMECH_ERR_NOT_IMPL; }
    if (q == 0u) { return SRMECH_ERR_NOT_IMPL; }         /* den==0 -> pure raises */
    st = srmech_continued_fraction(p, q, terms, 128u, &cnt);
    if (st != SRMECH_OK) { return SRMECH_ERR_NOT_IMPL; }
    lst = iv_list(a, cnt, 0);
    if (lst == NULL) { return SRMECH_ERR_OVERFLOW; }
    for (i = 0u; i < cnt; i++) {
        if (terms[i] > (uint64_t)INT64_MAX) { return SRMECH_ERR_NOT_IMPL; }
        lst->items[i] = iv_int(a, (int64_t)terms[i]);
        if (lst->items[i] == NULL) { return SRMECH_ERR_OVERFLOW; }
    }
    *out = lst;
    return SRMECH_OK;
}

/* ------------------------------------------------------------------
 * Shape thunk: list[int] -> list[(int, int)]
 *   rational.continued_fraction_convergents (int64 ladder; overflow -> pure).
 * ------------------------------------------------------------------ */

static srmech_status_t iv_shape_cf_convergents(const srmech_tool_entry_t *e,
                                               srmech_mval_t **argv, uint32_t argc,
                                               srmech_marshal_arena_t *a,
                                               srmech_mval_t **out)
{
    const srmech_mval_t *lin; int64_t *coefs, *nums, *dens; srmech_mval_t *lst;
    uint32_t n, i; srmech_status_t st;
    assert(e != NULL && argv != NULL && a != NULL && out != NULL);
    assert(argc >= 1u);
    if (argc != 1u
        || strcmp(e->name, "srmech.amsc.rational.continued_fraction_convergents") != 0) {
        return SRMECH_ERR_NOT_IMPL;
    }
    lin = argv[0];
    if (lin == NULL || lin->kind != SRMECH_MVAL_LIST) { return SRMECH_ERR_NOT_IMPL; }
    n = lin->n;
    if (n == 0u || n > 256u) { return SRMECH_ERR_NOT_IMPL; } /* empty / > cap -> pure raises */
    coefs = (int64_t *)iv_carve(a, (size_t)n * sizeof(int64_t));
    nums = (int64_t *)iv_carve(a, (size_t)n * sizeof(int64_t));
    dens = (int64_t *)iv_carve(a, (size_t)n * sizeof(int64_t));
    if (coefs == NULL || nums == NULL || dens == NULL) { return SRMECH_ERR_OVERFLOW; }
    for (i = 0u; i < n; i++) {
        const srmech_mval_t *c = lin->items[i];
        if (c == NULL || c->kind != SRMECH_MVAL_INT) { return SRMECH_ERR_NOT_IMPL; }
        if (i > 0u && c->i <= 0) { return SRMECH_ERR_NOT_IMPL; } /* a_k>0 (k>0) -> pure raises */
        coefs[i] = c->i;
    }
    st = srmech_cf_convergents_int64(coefs, (size_t)n, nums, dens);
    if (st != SRMECH_OK) { return SRMECH_ERR_NOT_IMPL; }
    lst = iv_list(a, n, 0);
    if (lst == NULL) { return SRMECH_ERR_OVERFLOW; }
    for (i = 0u; i < n; i++) {
        srmech_mval_t *pr = iv_list(a, 2u, 1);
        srmech_mval_t *h = iv_int(a, nums[i]); srmech_mval_t *k = iv_int(a, dens[i]);
        if (pr == NULL || h == NULL || k == NULL) { return SRMECH_ERR_OVERFLOW; }
        pr->items[0] = h; pr->items[1] = k; lst->items[i] = pr;
    }
    *out = lst;
    return SRMECH_OK;
}

/* ------------------------------------------------------------------
 * Shape thunk: (int, int, int) -> int   primes.cyclic_period. Replicates the
 * Python pre-C guards (n>=2, gcd(a mod n, n)==1, max_k default n) so a defer
 * lands exactly where the pure raises ValueError / OverflowError.
 * ------------------------------------------------------------------ */

static srmech_status_t iv_shape_cyclic_period(const srmech_tool_entry_t *e,
                                              srmech_mval_t **argv, uint32_t argc,
                                              srmech_marshal_arena_t *a,
                                              srmech_mval_t **out)
{
    uint64_t av = 0u, nv = 0u, mk = 0u, g = 0u, period = 0u; srmech_status_t st;
    assert(e != NULL && argv != NULL && a != NULL && out != NULL);
    assert(argc >= 1u);
    if (argc != 3u || strcmp(e->name, "srmech.amsc.primes.cyclic_period") != 0) {
        return SRMECH_ERR_NOT_IMPL;
    }
    if (!iv_arg_u64(argv[0], &av) || !iv_arg_u64(argv[1], &nv)) { return SRMECH_ERR_NOT_IMPL; }
    if (nv < 2u) { return SRMECH_ERR_NOT_IMPL; }         /* pure raises ValueError */
    st = srmech_gcd(av % nv, nv, &g);
    if (st != SRMECH_OK || g != 1u) { return SRMECH_ERR_NOT_IMPL; } /* not coprime -> pure raises */
    if (argv[2] != NULL && !iv_arg_u64(argv[2], &mk)) { return SRMECH_ERR_NOT_IMPL; }
    if (mk == 0u) { mk = nv; }                           /* max_k default: use n */
    st = srmech_cyclic_period(av, nv, mk, &period);
    if (st != SRMECH_OK) { return SRMECH_ERR_NOT_IMPL; } /* period>max_k -> pure OverflowError */
    return iv_result_u(a, period, out);
}

/* ------------------------------------------------------------------
 * Shape thunk: Sequence[bytes] -> bytes   hdc.bundle (odd count, equal len).
 * ------------------------------------------------------------------ */

static srmech_status_t iv_shape_bundle(const srmech_tool_entry_t *e,
                                       srmech_mval_t **argv, uint32_t argc,
                                       srmech_marshal_arena_t *a, srmech_mval_t **out)
{
    const srmech_mval_t *lst; const unsigned char **vecs; unsigned char *ob;
    uint32_t n, nb, i; srmech_status_t st;
    assert(e != NULL && argv != NULL && a != NULL && out != NULL);
    assert(argc >= 1u);
    if (argc != 1u || strcmp(e->name, "srmech.amsc.hdc.bundle") != 0) {
        return SRMECH_ERR_NOT_IMPL;
    }
    lst = argv[0];
    if (lst == NULL || lst->kind != SRMECH_MVAL_LIST || lst->n == 0u) { return SRMECH_ERR_NOT_IMPL; }
    n = lst->n;
    if ((n & 1u) == 0u) { return SRMECH_ERR_NOT_IMPL; }  /* even count -> pure raises */
    if (lst->items[0] == NULL || lst->items[0]->kind != SRMECH_MVAL_BYTES) { return SRMECH_ERR_NOT_IMPL; }
    nb = lst->items[0]->blen;
    if (nb == 0u) { return SRMECH_ERR_NOT_IMPL; }
    vecs = (const unsigned char **)iv_carve(a, (size_t)n * sizeof(void *));
    if (vecs == NULL) { return SRMECH_ERR_OVERFLOW; }
    for (i = 0u; i < n; i++) {
        const srmech_mval_t *v = lst->items[i];
        if (v == NULL || v->kind != SRMECH_MVAL_BYTES || v->blen != nb || v->b == NULL) {
            return SRMECH_ERR_NOT_IMPL;                  /* len mismatch -> pure raises */
        }
        vecs[i] = v->b;
    }
    ob = iv_carve(a, nb);
    if (ob == NULL) { return SRMECH_ERR_OVERFLOW; }
    st = srmech_hdc_bundle(vecs, n, nb, ob);
    if (st != SRMECH_OK) { return SRMECH_ERR_NOT_IMPL; }
    *out = iv_bytes(a, ob, nb);
    return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* ------------------------------------------------------------------
 * Shape thunk: list[bytes] -> list[str]   format.sha256_batch (hex digests).
 * ------------------------------------------------------------------ */

static srmech_status_t iv_shape_sha256_batch(const srmech_tool_entry_t *e,
                                             srmech_mval_t **argv, uint32_t argc,
                                             srmech_marshal_arena_t *a,
                                             srmech_mval_t **out)
{
    const srmech_mval_t *lst; const unsigned char **msgs; size_t *lens;
    unsigned char *digs; srmech_mval_t *result; uint32_t n, i; srmech_status_t st;
    assert(e != NULL && argv != NULL && a != NULL && out != NULL);
    assert(argc >= 1u);
    if (argc != 1u || strcmp(e->name, "srmech.amsc.format.sha256_batch") != 0) {
        return SRMECH_ERR_NOT_IMPL;
    }
    lst = argv[0];
    if (lst == NULL || lst->kind != SRMECH_MVAL_LIST) { return SRMECH_ERR_NOT_IMPL; }
    n = lst->n;
    if (n == 0u) { *out = iv_list(a, 0u, 0); return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK; }
    msgs = (const unsigned char **)iv_carve(a, (size_t)n * sizeof(void *));
    lens = (size_t *)iv_carve(a, (size_t)n * sizeof(size_t));
    digs = iv_carve(a, (size_t)n * 32u);
    if (msgs == NULL || lens == NULL || digs == NULL) { return SRMECH_ERR_OVERFLOW; }
    for (i = 0u; i < n; i++) {
        const srmech_mval_t *v = lst->items[i];
        if (v == NULL || v->kind != SRMECH_MVAL_BYTES) { return SRMECH_ERR_NOT_IMPL; }
        msgs[i] = (v->blen > 0u) ? v->b : NULL; lens[i] = (size_t)v->blen;
    }
    st = srmech_sha256_batch(msgs, lens, (size_t)n, digs);
    if (st != SRMECH_OK) { return SRMECH_ERR_NOT_IMPL; }
    result = iv_list(a, n, 0);
    if (result == NULL) { return SRMECH_ERR_OVERFLOW; }
    for (i = 0u; i < n; i++) {
        char hx[64]; srmech_mval_t *s;
        iv_hex32(digs + (size_t)i * 32u, hx);
        s = iv_str_copy(a, hx, 64u);
        if (s == NULL) { return SRMECH_ERR_OVERFLOW; }
        result->items[i] = s;
    }
    *out = result;
    return SRMECH_OK;
}

/* ------------------------------------------------------------------
 * Shape thunk: (bytes, list[tuple[bytes,int]]) -> (bool, int)
 *   dispatch.match (first-match tag; the (matched, tag) tuple).
 * ------------------------------------------------------------------ */

static srmech_status_t iv_shape_dispatch_match(const srmech_tool_entry_t *e,
                                               srmech_mval_t **argv, uint32_t argc,
                                               srmech_marshal_arena_t *a,
                                               srmech_mval_t **out)
{
    const unsigned char *inp = NULL, *pbuf = NULL; uint32_t il = 0u, n;
    uint32_t *offs, *lens, *tags; bool matched = false; uint32_t tag = 0u;
    srmech_mval_t *tup, *bn, *tn; srmech_status_t st;
    assert(e != NULL && argv != NULL && a != NULL && out != NULL);
    assert(argc >= 1u);
    if (argc != 2u || strcmp(e->name, "srmech.amsc.dispatch.match") != 0) {
        return SRMECH_ERR_NOT_IMPL;
    }
    if (!iv_arg_bytes(argv[0], &inp, &il)) { return SRMECH_ERR_NOT_IMPL; }
    if (argv[1] == NULL || argv[1]->kind != SRMECH_MVAL_LIST) { return SRMECH_ERR_NOT_IMPL; }
    n = argv[1]->n;
    offs = iv_carve_u32(a, n ? n : 1u); lens = iv_carve_u32(a, n ? n : 1u);
    tags = iv_carve_u32(a, n ? n : 1u);
    if (offs == NULL || lens == NULL || tags == NULL) { return SRMECH_ERR_OVERFLOW; }
    if (!iv_pack_rules(argv[1], a, &pbuf, offs, lens, tags)) { return SRMECH_ERR_NOT_IMPL; }
    st = srmech_dispatch_match(inp, il, pbuf, offs, lens, tags, n, &matched, &tag);
    if (st != SRMECH_OK) { return SRMECH_ERR_NOT_IMPL; }
    tup = iv_list(a, 2u, 1); bn = iv_bool(a, matched ? 1 : 0); tn = iv_int(a, (int64_t)tag);
    if (tup == NULL || bn == NULL || tn == NULL) { return SRMECH_ERR_OVERFLOW; }
    tup->items[0] = bn; tup->items[1] = tn; *out = tup;
    return SRMECH_OK;
}

/* ------------------------------------------------------------------
 * Shape thunk: (bytes, list[tuple[bytes,bytes]]) -> bytes | null
 *   naming.lookup (binary search over the caller-sorted catalog).
 * ------------------------------------------------------------------ */

static srmech_status_t iv_shape_naming_lookup(const srmech_tool_entry_t *e,
                                              srmech_mval_t **argv, uint32_t argc,
                                              srmech_marshal_arena_t *a,
                                              srmech_mval_t **out)
{
    const srmech_mval_t *pairs; const srmech_mval_t **keys, **vals;
    const unsigned char *kbuf = NULL, *vbuf = NULL, *kp = NULL;
    uint32_t *koff, *klen, *voff, *vlen; uint32_t n, kl = 0u, vo = 0u, vl = 0u;
    bool found = false; srmech_status_t st;
    assert(e != NULL && argv != NULL && a != NULL && out != NULL);
    assert(argc >= 1u);
    if (argc != 2u || strcmp(e->name, "srmech.amsc.naming.lookup") != 0) {
        return SRMECH_ERR_NOT_IMPL;
    }
    if (!iv_arg_bytes(argv[0], &kp, &kl)) { return SRMECH_ERR_NOT_IMPL; }
    pairs = argv[1];
    if (pairs == NULL || pairs->kind != SRMECH_MVAL_LIST) { return SRMECH_ERR_NOT_IMPL; }
    n = pairs->n;
    if (n == 0u) { *out = iv_new(a, SRMECH_MVAL_NONE); return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK; }
    if (!iv_split_pairs(pairs, a, &keys, &vals)) { return SRMECH_ERR_NOT_IMPL; }
    koff = iv_carve_u32(a, n); klen = iv_carve_u32(a, n);
    voff = iv_carve_u32(a, n); vlen = iv_carve_u32(a, n);
    if (koff == NULL || klen == NULL || voff == NULL || vlen == NULL) { return SRMECH_ERR_OVERFLOW; }
    if (!iv_pack_kv(a, n, keys, vals, NULL, &kbuf, koff, klen, &vbuf, voff, vlen)) {
        return SRMECH_ERR_NOT_IMPL;
    }
    st = srmech_catalog_lookup(kp, kl, kbuf, koff, klen, voff, vlen, n, &found, &vo, &vl);
    if (st != SRMECH_OK) { return SRMECH_ERR_NOT_IMPL; }
    if (!found) { *out = iv_new(a, SRMECH_MVAL_NONE); return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK; }
    *out = iv_bytes(a, vbuf + vo, vl);
    return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* ------------------------------------------------------------------
 * Shape thunk: (bytes, Mapping[bytes,bytes]) -> bytes   template.render.
 * The mapping is SORTED by key (the Python wrapper's binary-search contract)
 * before packing; an unknown key / unterminated brace -> BAD_INPUT -> defer.
 * ------------------------------------------------------------------ */

static srmech_status_t iv_shape_template_render(const srmech_tool_entry_t *e,
                                                srmech_mval_t **argv, uint32_t argc,
                                                srmech_marshal_arena_t *a,
                                                srmech_mval_t **out)
{
    const srmech_mval_t *dict; const unsigned char *tp = NULL, *kbuf = NULL, *vbuf = NULL;
    unsigned char *ob; uint32_t *koff, *klen, *voff, *vlen, *order;
    uint32_t tl = 0u, n, i, cap, vt = 0u, written = 0u; srmech_status_t st;
    assert(e != NULL && argv != NULL && a != NULL && out != NULL);
    assert(argc >= 1u);
    if (argc != 2u || strcmp(e->name, "srmech.amsc.template.render") != 0) {
        return SRMECH_ERR_NOT_IMPL;
    }
    if (!iv_arg_bytes(argv[0], &tp, &tl)) { return SRMECH_ERR_NOT_IMPL; }
    dict = argv[1];
    if (dict == NULL || dict->kind != SRMECH_MVAL_DICT) { return SRMECH_ERR_NOT_IMPL; }
    n = dict->n;
    order = iv_carve_u32(a, n ? n : 1u);
    koff = iv_carve_u32(a, n ? n : 1u); klen = iv_carve_u32(a, n ? n : 1u);
    voff = iv_carve_u32(a, n ? n : 1u); vlen = iv_carve_u32(a, n ? n : 1u);
    if (order == NULL || koff == NULL || klen == NULL || voff == NULL || vlen == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    if (n > 0u) {                                        /* n==0: dict->keys is NULL */
        iv_sort_order((const srmech_mval_t *const *)dict->keys, n, order);
        if (!iv_pack_kv(a, n, (const srmech_mval_t *const *)dict->keys,
                        (const srmech_mval_t *const *)dict->items, order,
                        &kbuf, koff, klen, &vbuf, voff, vlen)) {
            return SRMECH_ERR_NOT_IMPL;
        }
    }
    for (i = 0u; i < n; i++) { vt += vlen[i]; }
    cap = tl + vt + 64u;
    ob = iv_carve(a, cap);
    if (ob == NULL) { return SRMECH_ERR_OVERFLOW; }
    st = srmech_template_render(tp, tl, kbuf, koff, klen, vbuf, voff, vlen, n,
                                ob, cap, &written);
    if (st != SRMECH_OK) { return SRMECH_ERR_NOT_IMPL; } /* bad key / overflow -> pure */
    *out = iv_bytes(a, ob, written);
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
    /* rc189 CLEAN BATCH 2 */
    { "srmech.amsc.rational.rational_add",   iv_shape_rat2_to_rat },
    { "srmech.amsc.rational.rational_mul",   iv_shape_rat2_to_rat },
    { "srmech.amsc.rational.rational_div",   iv_shape_rat2_to_rat },
    { "srmech.amsc.rational.rational_pow_uint", iv_shape_rat_pow },
    { "srmech.amsc.rational.continued_fraction", iv_shape_cf },
    { "srmech.amsc.rational.continued_fraction_convergents", iv_shape_cf_convergents },
    { "srmech.amsc.primes.cyclic_period",    iv_shape_cyclic_period },
    { "srmech.amsc.hdc.bundle",              iv_shape_bundle },
    { "srmech.amsc.format.sha256_batch",     iv_shape_sha256_batch },
    { "srmech.amsc.dispatch.match",          iv_shape_dispatch_match },
    { "srmech.amsc.naming.lookup",           iv_shape_naming_lookup },
    { "srmech.amsc.template.render",         iv_shape_template_render },
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

/* Emit `s[0..len)` as a quoted JSON string. The batch-2 str leaves (sha256 hex
 * digests) are printable ASCII, so only " and \ need escaping; any control /
 * non-ASCII byte latches overflow -> the caller DEFERS (full ensure_ascii /
 * UTF-8 string emission is the pure path's job, never a wrong answer). */
static void iv_emit_str(iv_emit_t *e, const char *s, uint32_t len)
{
    uint32_t i;
    assert(e != NULL);
    assert(s != NULL || len == 0u);
    iv_raw(e, "\"", 1u);
    for (i = 0u; i < len; i++) {
        unsigned char c = (unsigned char)s[i];
        if (c == (unsigned char)'"') { iv_raw(e, "\\\"", 2u); }
        else if (c == (unsigned char)'\\') { iv_raw(e, "\\\\", 2u); }
        else if (c >= 0x20u && c <= 0x7Eu) { char cc = (char)c; iv_raw(e, &cc, 1u); }
        else { e->overflow = 1; return; }
    }
    iv_raw(e, "\"", 1u);
}

/* Emit an INT / BOOL / STR / null leaf, or a nested LIST, with the json.dumps
 * DEFAULT ", " separator. Depth is bounded (<= 2: a list-of-int-pairs is the
 * deepest shape the thunks produce); a deeper / unsupported node latches
 * overflow (the caller defers). BYTES / FLOAT / DICT are NOT list leaves in
 * any batch result, so they latch overflow too. */
static void iv_emit_node(iv_emit_t *e, const srmech_mval_t *v, uint32_t depth)
{
    uint32_t k;
    assert(e != NULL);
    assert(depth <= 2u);
    if (v == NULL || depth > 2u) { e->overflow = 1; return; }
    if (v->kind == SRMECH_MVAL_INT) { iv_emit_i64(e, v->i); return; }
    if (v->kind == SRMECH_MVAL_BOOL) {
        if (v->i) { iv_raw(e, "true", 4u); } else { iv_raw(e, "false", 5u); }
        return;
    }
    if (v->kind == SRMECH_MVAL_STR) { iv_emit_str(e, v->s, v->slen); return; }
    if (v->kind == SRMECH_MVAL_NONE) { iv_raw(e, "null", 4u); return; }
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
