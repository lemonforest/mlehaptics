/* srmech_mcp_marshal.c — the MCP tool-call MARSHALLING FOUNDATION in C
 * (0.9.0rc187; the HOST-GLUE JSON-args<->typed-C-args value carrier).
 *
 * The shared bedrock the rc188+ invoke_tool DISPATCH + the #796 nested
 * marshal build on. It generalises the rc181 dsl_chain_run dv_value_t
 * tagged union into a uniform marshalling carrier (`srmech_mval_t`) and
 * mirrors the private Python srmech.mcp._coercion coerce_param /
 * serialise_native for the bucket-(a) CLEAN families (scalar / str / list /
 * bytes / complex).
 *
 * TWO STAGES (the MCP wire form is NOT self-describing — the param TYPE
 * comes from the rc184 registry, not the value):
 *   (1) srmech_mval_from_json  — parse a JSON value tree -> a tagged carrier
 *       (the raw stage-1 form: null/bool/int/double/string/array/object).
 *   (2) srmech_mcp_marshal_arg — typed-lower keyed on the registry type
 *       string (the INVERSE of rc185's MCP_TYPE_LEXICON): a "bytes" param's
 *       base64 STR -> BYTES, a "complex" param's [re,im] -> COMPLEX, the
 *       list/mapping container families recurse the same leaf coercers.
 * srmech_mcp_serialise_result is the OUTBOUND inverse: a (typed) carrier ->
 * canonical JSON BYTE-IDENTICAL to CPython json.dumps(x, separators=
 * (",", ":")) (insertion-order keys, default ensure_ascii=True, bytes ->
 * base64, complex -> [re,im]) — the mirror of serialise_native + json.dumps.
 *
 * A type OUTSIDE bucket-(a) (Mat/Vec/HV/np.ndarray float carriers = rc190
 * (c); by-reference handle / operator_name = later; any unknown type) ->
 * srmech_mcp_marshal_arg returns SRMECH_ERR_NOT_IMPL and the caller DEFERS
 * to the pure Python coerce_param (rc103 inform-don't-limit). A JSON null
 * ALWAYS passes through (coerce_param's null-first rule) for any type.
 *
 * The rc187 DoD surface is srmech_mcp_marshal_roundtrip — a JSON-in/JSON-out
 * prover (ctypes-drivable) that composes stage-1 + marshal_arg +
 * serialise_result: it proves the round-trip lands on the SAME canonical JSON
 * as the Python coerce_param -> serialise_native path.
 *
 * JPL Power-of-Ten: caller-arena only (no malloc), <=60-line functions, >=2
 * asserts/function, no goto, DEPTH-BOUNDED recursion (SRMECH_MVAL_MAX_DEPTH),
 * no abs/libm (base64 is pure integer arithmetic; floats format via snprintf
 * %.17g like srmech_json.c). Additive symbols + types -> SRMECH_ABI_VERSION
 * stays 4 (the ctypes shim hasattr-guards). NO Python dispatch is wired THIS
 * rc (foundation only). */

#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>   /* strtod / strtol — the shortest-repr round-trip (rc190) */
#include <string.h>

#include "srmech.h"

/* ------------------------------------------------------------------
 * Bump arena — forward-only carve, void*-aligned (the compose_run idiom).
 * ------------------------------------------------------------------ */

static unsigned char *mm_align(unsigned char *p)
{
    uintptr_t a = (uintptr_t)sizeof(void *);
    uintptr_t pad;
    assert(p != NULL);
    assert(a >= 4u);
    pad = (a - ((uintptr_t)p % a)) % a;
    return p + pad;
}

/* Carve `n` aligned bytes; NULL (no partial carve) if it does not fit. */
static unsigned char *mm_carve(srmech_marshal_arena_t *a, size_t n)
{
    unsigned char *p;
    assert(a != NULL);
    assert(a->cur <= a->end);
    p = mm_align(a->cur);
    if (p > a->end || n > (size_t)(a->end - p)) { return NULL; }
    a->cur = p + n;
    return p;
}

void srmech_marshal_arena_init(srmech_marshal_arena_t *a, void *ws, size_t ws_len)
{
    assert(a != NULL);
    assert(ws != NULL || ws_len == 0u);
    a->cur = (unsigned char *)ws;
    a->end = a->cur + ws_len;
}

/* ------------------------------------------------------------------
 * Carrier constructors — one node per call, zeroed then set.
 * ------------------------------------------------------------------ */

static srmech_mval_t *mm_new(srmech_marshal_arena_t *a, srmech_mval_kind_t kind)
{
    srmech_mval_t *v;
    assert(a != NULL);
    assert(kind >= SRMECH_MVAL_NONE && kind <= SRMECH_MVAL_MAT);
    v = (srmech_mval_t *)mm_carve(a, sizeof(srmech_mval_t));
    if (v == NULL) { return NULL; }
    v->kind = kind; v->i = 0; v->re = 0.0; v->im = 0.0;
    v->s = NULL; v->slen = 0u; v->b = NULL; v->blen = 0u;
    v->items = NULL; v->keys = NULL; v->n = 0u; v->is_tuple = 0;
    return v;
}

static srmech_mval_t *mm_int(srmech_marshal_arena_t *a, int64_t x)
{
    srmech_mval_t *v = mm_new(a, SRMECH_MVAL_INT);
    assert(a != NULL);
    assert(a->cur <= a->end);
    if (v != NULL) { v->i = x; }
    return v;
}

static srmech_mval_t *mm_bool(srmech_marshal_arena_t *a, int truth)
{
    srmech_mval_t *v = mm_new(a, SRMECH_MVAL_BOOL);
    assert(a != NULL);
    assert(a->cur <= a->end);
    if (v != NULL) { v->i = truth ? 1 : 0; }
    return v;
}

static srmech_mval_t *mm_float(srmech_marshal_arena_t *a, double x)
{
    srmech_mval_t *v = mm_new(a, SRMECH_MVAL_FLOAT);
    assert(a != NULL);
    assert(a->cur <= a->end);
    if (v != NULL) { v->re = x; }
    return v;
}

static srmech_mval_t *mm_complex(srmech_marshal_arena_t *a, double re, double im)
{
    srmech_mval_t *v = mm_new(a, SRMECH_MVAL_COMPLEX);
    assert(a != NULL);
    assert(a->cur <= a->end);
    if (v != NULL) { v->re = re; v->im = im; }
    return v;
}

static srmech_mval_t *mm_str(srmech_marshal_arena_t *a, const char *s, uint32_t len)
{
    srmech_mval_t *v = mm_new(a, SRMECH_MVAL_STR);
    assert(a != NULL);
    assert(s != NULL || len == 0u);
    if (v != NULL) { v->s = s; v->slen = len; }
    return v;
}

static srmech_mval_t *mm_bytes(srmech_marshal_arena_t *a,
                               const unsigned char *buf, uint32_t len)
{
    srmech_mval_t *v = mm_new(a, SRMECH_MVAL_BYTES);
    assert(a != NULL);
    assert(buf != NULL || len == 0u);
    if (v != NULL) { v->b = buf; v->blen = len; }
    return v;
}

/* A fresh LIST (or tuple) node with an item-pointer array sized for `n`. */
static srmech_mval_t *mm_list(srmech_marshal_arena_t *a, uint32_t n, int is_tuple)
{
    srmech_mval_t *v = mm_new(a, SRMECH_MVAL_LIST);
    assert(a != NULL);
    assert(a->cur <= a->end);
    if (v == NULL) { return NULL; }
    v->is_tuple = is_tuple ? 1 : 0;
    v->n = n;
    if (n > 0u) {
        v->items = (srmech_mval_t **)mm_carve(a, (size_t)n * sizeof(void *));
        if (v->items == NULL) { return NULL; }
    }
    return v;
}

/* A real MAT carrier (rc190): rows*cols row-major doubles carved into the arena.
 * n=rows, i=cols, blen=#doubles, b aliases the (8-aligned) double buffer; the
 * caller fills it via (double *)(void *)v->b. is_tuple=0 (real — matches the
 * "Mat" coerce_param, which builds Mat.from_rows(is_complex=False)). */
static srmech_mval_t *mm_mat(srmech_marshal_arena_t *a, uint32_t rows, uint32_t cols)
{
    srmech_mval_t *v = mm_new(a, SRMECH_MVAL_MAT);
    size_t nd = (size_t)rows * cols;
    assert(a != NULL);
    assert(a->cur <= a->end);
    if (v == NULL) { return NULL; }
    v->n = rows; v->i = (int64_t)cols; v->is_tuple = 0; v->blen = (uint32_t)nd;
    if (nd > 0u) {
        v->b = mm_carve(a, nd * sizeof(double));         /* 8-aligned by mm_carve */
        if (v->b == NULL) { return NULL; }
    }
    return v;
}

/* ------------------------------------------------------------------
 * base64 — standard alphabet, '=' padding (Python base64.b64{en,de}code).
 * ------------------------------------------------------------------ */

static const char MM_B64[] =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

/* One base64 char -> its 0..63 value, or -1 if not an alphabet char. */
static int mm_b64_val(unsigned char c)
{
    assert(MM_B64[0] == 'A');
    assert(sizeof MM_B64 == 65u);
    if (c >= 'A' && c <= 'Z') { return (int)(c - 'A'); }
    if (c >= 'a' && c <= 'z') { return (int)(c - 'a') + 26; }
    if (c >= '0' && c <= '9') { return (int)(c - '0') + 52; }
    if (c == '+') { return 62; }
    if (c == '/') { return 63; }
    return -1;
}

/* Decode `s[0..slen)` (validate=True semantics) into an arena buffer.
 * len%4 must be 0; '=' only as 1-2 trailing pad chars; any other non-
 * alphabet char -> SRMECH_ERR_BAD_INPUT. */
static srmech_status_t mm_b64_decode(const char *s, uint32_t slen,
                                     srmech_marshal_arena_t *a,
                                     const unsigned char **out, uint32_t *olen)
{
    unsigned char *dst; uint32_t pad = 0u, groups, dlen, gi, di = 0u;
    assert(a != NULL && out != NULL && olen != NULL);
    assert(s != NULL || slen == 0u);
    if (slen == 0u) { *out = (const unsigned char *)MM_B64; *olen = 0u; return SRMECH_OK; }
    if ((slen & 3u) != 0u) { return SRMECH_ERR_BAD_INPUT; }
    if (s[slen - 1u] == '=') { pad = (s[slen - 2u] == '=') ? 2u : 1u; }
    groups = slen / 4u;
    dlen = groups * 3u - pad;
    dst = (unsigned char *)mm_carve(a, (dlen == 0u) ? 1u : dlen);
    if (dst == NULL) { return SRMECH_ERR_OVERFLOW; }
    for (gi = 0u; gi < groups; gi++) {
        int q[4]; uint32_t k; int last = (gi + 1u == groups);
        for (k = 0u; k < 4u; k++) {
            unsigned char c = (unsigned char)s[gi * 4u + k];
            if (c == '=' && last && k >= 4u - pad) { q[k] = 0; continue; }
            q[k] = mm_b64_val(c);
            if (q[k] < 0) { return SRMECH_ERR_BAD_INPUT; }
        }
        dst[di++] = (unsigned char)((q[0] << 2) | (q[1] >> 4));
        if (!(last && pad >= 2u)) { dst[di++] = (unsigned char)((q[1] << 4) | (q[2] >> 2)); }
        if (!(last && pad >= 1u)) { dst[di++] = (unsigned char)((q[2] << 6) | q[3]); }
    }
    assert(di == dlen);
    *out = dst; *olen = dlen;
    return SRMECH_OK;
}

/* ------------------------------------------------------------------
 * STAGE 1 — srmech_json value tree -> carrier tree (raw form).
 * ------------------------------------------------------------------ */

static srmech_status_t mm_from_json(const srmech_json_value_t *j,
                                    srmech_marshal_arena_t *a, uint32_t depth,
                                    srmech_mval_t **out);

static srmech_status_t mm_from_json_array(const srmech_json_value_t *j,
                                          srmech_marshal_arena_t *a,
                                          uint32_t depth, srmech_mval_t **out)
{
    srmech_mval_t *lst; uint32_t i, n;
    assert(j != NULL && a != NULL && out != NULL);
    assert(j->type == SRMECH_JSON_ARRAY);
    n = j->u.arr.n;
    lst = mm_list(a, n, 0);
    if (lst == NULL) { return SRMECH_ERR_OVERFLOW; }
    for (i = 0u; i < n; i++) {
        srmech_status_t st = mm_from_json(j->u.arr.items[i], a, depth + 1u, &lst->items[i]);
        if (st != SRMECH_OK) { return st; }
    }
    *out = lst;
    return SRMECH_OK;
}

static srmech_status_t mm_from_json_object(const srmech_json_value_t *j,
                                           srmech_marshal_arena_t *a,
                                           uint32_t depth, srmech_mval_t **out)
{
    srmech_mval_t *d; uint32_t i, n;
    assert(j != NULL && a != NULL && out != NULL);
    assert(j->type == SRMECH_JSON_OBJECT);
    n = j->u.obj.n;
    d = mm_new(a, SRMECH_MVAL_DICT);
    if (d == NULL) { return SRMECH_ERR_OVERFLOW; }
    d->n = n;
    if (n > 0u) {
        d->keys = (srmech_mval_t **)mm_carve(a, (size_t)n * sizeof(void *));
        d->items = (srmech_mval_t **)mm_carve(a, (size_t)n * sizeof(void *));
        if (d->keys == NULL || d->items == NULL) { return SRMECH_ERR_OVERFLOW; }
    }
    for (i = 0u; i < n; i++) {
        const char *key = j->u.obj.keys[i];
        srmech_status_t st;
        d->keys[i] = mm_str(a, key, (uint32_t)strlen(key));
        if (d->keys[i] == NULL) { return SRMECH_ERR_OVERFLOW; }
        st = mm_from_json(j->u.obj.vals[i], a, depth + 1u, &d->items[i]);
        if (st != SRMECH_OK) { return st; }
    }
    *out = d;
    return SRMECH_OK;
}

static srmech_status_t mm_from_json(const srmech_json_value_t *j,
                                    srmech_marshal_arena_t *a, uint32_t depth,
                                    srmech_mval_t **out)
{
    srmech_mval_t *v = NULL;
    assert(a != NULL && out != NULL);
    assert(depth <= (uint32_t)SRMECH_MVAL_MAX_DEPTH + 1u);
    if (j == NULL) { return SRMECH_ERR_BAD_INPUT; }
    if (depth > (uint32_t)SRMECH_MVAL_MAX_DEPTH) { return SRMECH_ERR_OVERFLOW; }
    if (j->type == SRMECH_JSON_ARRAY) { return mm_from_json_array(j, a, depth, out); }
    if (j->type == SRMECH_JSON_OBJECT) { return mm_from_json_object(j, a, depth, out); }
    if (j->type == SRMECH_JSON_NULL) { v = mm_new(a, SRMECH_MVAL_NONE); }
    else if (j->type == SRMECH_JSON_BOOL) { v = mm_bool(a, j->u.b); }
    else if (j->type == SRMECH_JSON_INT) { v = mm_int(a, j->u.i); }
    else if (j->type == SRMECH_JSON_DOUBLE) { v = mm_float(a, j->u.f); }
    else if (j->type == SRMECH_JSON_STRING) { v = mm_str(a, j->u.str.ptr, j->u.str.len); }
    else { return SRMECH_ERR_BAD_INPUT; }
    if (v == NULL) { return SRMECH_ERR_OVERFLOW; }
    *out = v;
    return SRMECH_OK;
}

srmech_status_t srmech_mval_from_json(const srmech_json_value_t *j,
                                      srmech_marshal_arena_t *a,
                                      srmech_mval_t **out)
{
    /* Runtime-checked entry params return NULL_ARG BEFORE any assert fires —
     * a contractually-handled NULL is not an invariant violation (rc715). */
    if (j == NULL || a == NULL || out == NULL) { return SRMECH_ERR_NULL_ARG; }
    assert(a->cur <= a->end);                       /* genuine arena invariant */
    assert(j->type >= SRMECH_JSON_NULL && j->type <= SRMECH_JSON_OBJECT);
    return mm_from_json(j, a, 0u, out);
}

/* ------------------------------------------------------------------
 * SHORTEST double->repr formatter (rc190) — CPython repr(float)/json.dumps.
 * ------------------------------------------------------------------ */

/* Shortest %.*e (p=0..16) that strtod-round-trips `m` (m>0, finite). Fills the
 * significant decimal digits into `digs` (>=18 chars) + *ndig, and the base-10
 * exponent of the leading digit into *exp10. Returns SRMECH_ERR_BAD_INPUT if
 * snprintf overruns (never for a finite m). glibc/msvc/macOS printf + strtod
 * are correctly-rounded, so this yields the same digit string CPython's dtoa
 * (mode 0) does on the same platform. */
static srmech_status_t dr_shortest(double m, char *digs, int *ndig, int *exp10)
{
    char tmp[40]; int p, i, dn; long e;
    assert(m > 0.0);
    assert(digs != NULL && ndig != NULL && exp10 != NULL);
    for (p = 0; p <= 16; p++) {
        int nn = snprintf(tmp, sizeof tmp, "%.*e", p, m);
        if (nn < 0 || (size_t)nn >= sizeof tmp) { return SRMECH_ERR_BAD_INPUT; }
        if (strtod(tmp, NULL) == m) { break; }
    }
    if (p > 16) { p = 16; }                             /* 17 sig digits always round-trip */
    dn = 0;
    for (i = 0; tmp[i] != 'e' && tmp[i] != 'E' && tmp[i] != '\0'; i++) {
        if (tmp[i] >= '0' && tmp[i] <= '9') { digs[dn++] = tmp[i]; }
    }
    if (tmp[i] != 'e' && tmp[i] != 'E') { return SRMECH_ERR_BAD_INPUT; }
    e = strtol(tmp + i + 1, NULL, 10);
    *ndig = dn; *exp10 = (int)e;
    return SRMECH_OK;
}

/* Append `n` '0' chars into out at *pos (bounded by the ndig<=17 / decpt<=16
 * fixed-format geometry — the caller sizes cap >= 32). */
static void dr_zeros(char *out, size_t *pos, int n)
{
    int i;
    assert(out != NULL && pos != NULL);
    assert(n >= 0);
    for (i = 0; i < n; i++) { out[(*pos)++] = '0'; }
}

/* Render the exponential form (use_exp): D[.DDDD]e{+-}XX (>=2 exponent digits). */
static void dr_exp(char *out, size_t *pos, const char *digs, int ndig, int exp10)
{
    int i, ea; char es;
    assert(out != NULL && pos != NULL && digs != NULL);
    assert(ndig >= 1);
    out[(*pos)++] = digs[0];
    if (ndig > 1) {
        out[(*pos)++] = '.';
        for (i = 1; i < ndig; i++) { out[(*pos)++] = digs[i]; }
    }
    out[(*pos)++] = 'e';
    es = (exp10 < 0) ? '-' : '+'; ea = (exp10 < 0) ? -exp10 : exp10;
    out[(*pos)++] = es;
    if (ea < 10) { out[(*pos)++] = '0'; out[(*pos)++] = (char)('0' + ea); }
    else { char eb[8]; int en = snprintf(eb, sizeof eb, "%d", ea);
           if (en > 0) { memcpy(out + *pos, eb, (size_t)en); *pos += (size_t)en; } }
}

/* Render the fixed form from digits + decimal-point position `decpt`. */
static void dr_fixed(char *out, size_t *pos, const char *digs, int ndig, int decpt)
{
    int i;
    assert(out != NULL && pos != NULL && digs != NULL);
    assert(ndig >= 1);
    if (decpt <= 0) {                                   /* 0.<zeros><digits> */
        out[(*pos)++] = '0'; out[(*pos)++] = '.';
        dr_zeros(out, pos, -decpt);
        for (i = 0; i < ndig; i++) { out[(*pos)++] = digs[i]; }
    } else if (decpt >= ndig) {                          /* <digits><zeros>.0 */
        for (i = 0; i < ndig; i++) { out[(*pos)++] = digs[i]; }
        dr_zeros(out, pos, decpt - ndig);
        out[(*pos)++] = '.'; out[(*pos)++] = '0';
    } else {                                             /* <digits>.<digits> */
        for (i = 0; i < decpt; i++) { out[(*pos)++] = digs[i]; }
        out[(*pos)++] = '.';
        for (i = decpt; i < ndig; i++) { out[(*pos)++] = digs[i]; }
    }
}

srmech_status_t srmech_double_repr(double v, char *out, size_t cap, size_t *out_len)
{
    char digs[20]; int ndig = 0, exp10 = 0, decpt; size_t pos = 0u;
    uint64_t bits; int neg; double m; srmech_status_t st;
    /* NULL/too-small buffer returns NULL_ARG BEFORE any assert (rc715). */
    if (out == NULL || out_len == NULL || cap < 32u) { return SRMECH_ERR_NULL_ARG; }
    if (v != v) { return SRMECH_ERR_BAD_INPUT; }        /* NaN -> defer */
    if (v != 0.0 && v * 0.5 == v) { return SRMECH_ERR_BAD_INPUT; }  /* +-Inf -> defer */
    memcpy(&bits, &v, sizeof bits);                     /* libm-free sign (incl. -0.0) */
    neg = (int)(bits >> 63);
    assert(cap >= 32u);
    if (v == 0.0) {
        const char *z = neg ? "-0.0" : "0.0";
        memcpy(out, z, strlen(z) + 1u); *out_len = strlen(z); return SRMECH_OK;
    }
    m = neg ? -v : v;
    st = dr_shortest(m, digs, &ndig, &exp10);
    if (st != SRMECH_OK) { return st; }
    decpt = exp10 + 1;
    if (neg) { out[pos++] = '-'; }
    if (decpt <= -4 || decpt > 16) { dr_exp(out, &pos, digs, ndig, exp10); }
    else { dr_fixed(out, &pos, digs, ndig, decpt); }
    assert(pos < cap);
    out[pos] = '\0'; *out_len = pos;
    return SRMECH_OK;
}

/* ------------------------------------------------------------------
 * OUTBOUND serialiser — bounded emit sink, ensure_ascii=True, insertion
 * order (BYTE-IDENTICAL to json.dumps(x, separators=(",", ":"))).
 * ------------------------------------------------------------------ */

typedef struct { char *buf; size_t cap; size_t used; int overflow; } mm_emit_t;

/* Append `n` raw bytes; in size-query / overflow modes only `used` advances. */
static void mm_raw(mm_emit_t *e, const char *s, size_t n)
{
    size_t i;
    assert(e != NULL);
    assert(s != NULL || n == 0u);
    if (e->buf != NULL) {
        if (e->overflow || e->used + n > e->cap) { e->overflow = 1; return; }
        for (i = 0u; i < n; i++) { e->buf[e->used + i] = s[i]; }
    }
    e->used += n;
}

static void mm_cstr(mm_emit_t *e, const char *s)
{
    assert(e != NULL);
    assert(s != NULL);
    mm_raw(e, s, strlen(s));
}

/* Decode one UTF-8 code point at p[*i] (bounded by len), advancing *i. Input
 * is trusted valid UTF-8 (a Python str -> utf-8 slice from srmech_json). */
static uint32_t mm_utf8_next(const unsigned char *p, uint32_t len, uint32_t *i)
{
    uint32_t b0, j;
    assert(p != NULL && i != NULL);
    assert(*i < len);
    j = *i; b0 = p[j];
    if (b0 < 0x80u) { *i = j + 1u; return b0; }
    if ((b0 & 0xE0u) == 0xC0u && j + 1u < len) {
        *i = j + 2u; return ((b0 & 0x1Fu) << 6) | (p[j + 1u] & 0x3Fu);
    }
    if ((b0 & 0xF0u) == 0xE0u && j + 2u < len) {
        *i = j + 3u;
        return ((b0 & 0x0Fu) << 12) | ((p[j + 1u] & 0x3Fu) << 6) | (p[j + 2u] & 0x3Fu);
    }
    *i = (j + 4u <= len) ? j + 4u : len;
    return ((b0 & 0x07u) << 18) | ((p[j + 1u] & 0x3Fu) << 12)
           | ((p[j + 2u] & 0x3Fu) << 6) | (p[j + 3u] & 0x3Fu);
}

/* Emit \uXXXX (lowercase hex) for a single BMP code unit. */
static void mm_u_escape(mm_emit_t *e, uint32_t cu)
{
    static const char hexd[] = "0123456789abcdef";
    char b[6];
    assert(e != NULL);
    assert(cu <= 0xFFFFu);
    b[0] = '\\'; b[1] = 'u';
    b[2] = hexd[(cu >> 12) & 0xFu]; b[3] = hexd[(cu >> 8) & 0xFu];
    b[4] = hexd[(cu >> 4) & 0xFu]; b[5] = hexd[cu & 0xFu];
    mm_raw(e, b, 6u);
}

/* Emit one code point per the json.dumps default (ensure_ascii=True) rules. */
static void mm_emit_cp(mm_emit_t *e, uint32_t cp)
{
    assert(e != NULL);
    assert(cp <= 0x10FFFFu);
    if (cp == 0x22u) { mm_raw(e, "\\\"", 2u); }
    else if (cp == 0x5Cu) { mm_raw(e, "\\\\", 2u); }
    else if (cp == 0x08u) { mm_raw(e, "\\b", 2u); }
    else if (cp == 0x09u) { mm_raw(e, "\\t", 2u); }
    else if (cp == 0x0Au) { mm_raw(e, "\\n", 2u); }
    else if (cp == 0x0Cu) { mm_raw(e, "\\f", 2u); }
    else if (cp == 0x0Du) { mm_raw(e, "\\r", 2u); }
    else if (cp < 0x20u) { mm_u_escape(e, cp); }
    else if (cp <= 0x7Eu) { char c = (char)cp; mm_raw(e, &c, 1u); }
    else if (cp <= 0xFFFFu) { mm_u_escape(e, cp); }
    else {
        uint32_t v = cp - 0x10000u;
        mm_u_escape(e, 0xD800u + (v >> 10));
        mm_u_escape(e, 0xDC00u + (v & 0x3FFu));
    }
}

/* Emit `s[0..len)` as a quoted JSON string (ensure_ascii=True). */
static void mm_json_string(mm_emit_t *e, const char *s, uint32_t len)
{
    const unsigned char *p = (const unsigned char *)s;
    uint32_t i = 0u;
    assert(e != NULL);
    assert(s != NULL || len == 0u);
    mm_raw(e, "\"", 1u);
    while (i < len) { mm_emit_cp(e, mm_utf8_next(p, len, &i)); }
    mm_raw(e, "\"", 1u);
}

/* Emit a byte buffer as a QUOTED base64 string (streamed 3->4, no scratch). */
static void mm_json_b64(mm_emit_t *e, const unsigned char *p, uint32_t n)
{
    uint32_t i; char q[4];
    assert(e != NULL);
    assert(p != NULL || n == 0u);
    mm_raw(e, "\"", 1u);
    for (i = 0u; i + 3u <= n; i += 3u) {
        uint32_t v = ((uint32_t)p[i] << 16) | ((uint32_t)p[i + 1u] << 8) | p[i + 2u];
        q[0] = MM_B64[(v >> 18) & 0x3Fu]; q[1] = MM_B64[(v >> 12) & 0x3Fu];
        q[2] = MM_B64[(v >> 6) & 0x3Fu]; q[3] = MM_B64[v & 0x3Fu];
        mm_raw(e, q, 4u);
    }
    if (n - i == 1u) {
        uint32_t v = (uint32_t)p[i] << 16;
        q[0] = MM_B64[(v >> 18) & 0x3Fu]; q[1] = MM_B64[(v >> 12) & 0x3Fu];
        q[2] = '='; q[3] = '='; mm_raw(e, q, 4u);
    } else if (n - i == 2u) {
        uint32_t v = ((uint32_t)p[i] << 16) | ((uint32_t)p[i + 1u] << 8);
        q[0] = MM_B64[(v >> 18) & 0x3Fu]; q[1] = MM_B64[(v >> 12) & 0x3Fu];
        q[2] = MM_B64[(v >> 6) & 0x3Fu]; q[3] = '='; mm_raw(e, q, 4u);
    }
    mm_raw(e, "\"", 1u);
}

/* Emit an int64 in decimal (mirrors srmech_json.c json_write_int). */
static void mm_emit_int(mm_emit_t *e, int64_t v)
{
    char tmp[24]; int n;
    assert(e != NULL);
    assert(sizeof tmp >= 21u);
    n = snprintf(tmp, sizeof tmp, "%lld", (long long)v);
    if (n < 0) { return; }
    mm_raw(e, tmp, (size_t)n);
}

/* Emit a double as CPython repr(float)/json.dumps do — the SHORTEST round-trip
 * decimal via srmech_double_repr (rc190 repr-parity). A non-finite double (never
 * produced by the exact tools) falls back to the %.17g(+".0") best-effort form. */
static void mm_emit_double(mm_emit_t *e, double v)
{
    char rep[40]; size_t rlen = 0u;
    assert(e != NULL);
    assert(sizeof rep >= 32u);
    if (srmech_double_repr(v, rep, sizeof rep, &rlen) == SRMECH_OK) {
        mm_raw(e, rep, rlen);
    } else {
        int n = snprintf(rep, sizeof rep, "%.17g", v);   /* NaN/Inf best-effort */
        if (n > 0) { mm_raw(e, rep, (size_t)n); }
    }
}

static void mm_serialise(mm_emit_t *e, const srmech_mval_t *v, uint32_t depth);

/* A real MAT carrier -> a nested [[d,d,...],...] float array (compact, no space
 * separator) — byte-identical to json.dumps(serialise_native(Mat), separators=
 * (",",":")). Each double via mm_emit_double (the shortest-repr form). */
static void mm_serialise_mat(mm_emit_t *e, const srmech_mval_t *v)
{
    uint32_t rows, cols, r, c; const double *d;
    assert(e != NULL && v != NULL);
    assert(v->kind == SRMECH_MVAL_MAT);
    rows = v->n; cols = (uint32_t)v->i; d = (const double *)(const void *)v->b;
    mm_raw(e, "[", 1u);
    for (r = 0u; r < rows; r++) {
        if (r > 0u) { mm_raw(e, ",", 1u); }
        mm_raw(e, "[", 1u);
        for (c = 0u; c < cols; c++) {
            if (c > 0u) { mm_raw(e, ",", 1u); }
            mm_emit_double(e, d[(size_t)r * cols + c]);
        }
        mm_raw(e, "]", 1u);
    }
    mm_raw(e, "]", 1u);
}

/* [re,im] for a COMPLEX; each part via mm_emit_double. */
static void mm_serialise_complex(mm_emit_t *e, const srmech_mval_t *v)
{
    assert(e != NULL && v != NULL);
    assert(v->kind == SRMECH_MVAL_COMPLEX);
    mm_raw(e, "[", 1u);
    mm_emit_double(e, v->re);
    mm_raw(e, ",", 1u);
    mm_emit_double(e, v->im);
    mm_raw(e, "]", 1u);
}

/* A LIST or tuple -> a JSON array (insertion order). */
static void mm_serialise_list(mm_emit_t *e, const srmech_mval_t *v, uint32_t depth)
{
    uint32_t k;
    assert(e != NULL && v != NULL);
    assert(v->kind == SRMECH_MVAL_LIST);
    mm_raw(e, "[", 1u);
    for (k = 0u; k < v->n; k++) {
        if (k > 0u) { mm_raw(e, ",", 1u); }
        mm_serialise(e, v->items[k], depth + 1u);
    }
    mm_raw(e, "]", 1u);
}

/* A DICT -> a JSON object (insertion order; a BYTES key -> base64 string). */
static void mm_serialise_dict(mm_emit_t *e, const srmech_mval_t *v, uint32_t depth)
{
    uint32_t k;
    assert(e != NULL && v != NULL);
    assert(v->kind == SRMECH_MVAL_DICT);
    mm_raw(e, "{", 1u);
    for (k = 0u; k < v->n; k++) {
        const srmech_mval_t *key = v->keys[k];
        if (k > 0u) { mm_raw(e, ",", 1u); }
        if (key->kind == SRMECH_MVAL_BYTES) { mm_json_b64(e, key->b, key->blen); }
        else { mm_json_string(e, key->s, key->slen); }
        mm_raw(e, ":", 1u);
        mm_serialise(e, v->items[k], depth + 1u);
    }
    mm_raw(e, "}", 1u);
}

static void mm_serialise(mm_emit_t *e, const srmech_mval_t *v, uint32_t depth)
{
    assert(e != NULL);
    assert(depth <= (uint32_t)SRMECH_MVAL_MAX_DEPTH + 2u);
    if (v == NULL || depth > (uint32_t)SRMECH_MVAL_MAX_DEPTH + 1u) {
        e->overflow = 1; return;
    }
    switch (v->kind) {
    case SRMECH_MVAL_NONE:    mm_cstr(e, "null"); break;
    case SRMECH_MVAL_BOOL:    mm_cstr(e, v->i ? "true" : "false"); break;
    case SRMECH_MVAL_INT:     mm_emit_int(e, v->i); break;
    case SRMECH_MVAL_FLOAT:   mm_emit_double(e, v->re); break;
    case SRMECH_MVAL_STR:     mm_json_string(e, v->s, v->slen); break;
    case SRMECH_MVAL_BYTES:   mm_json_b64(e, v->b, v->blen); break;
    case SRMECH_MVAL_COMPLEX: mm_serialise_complex(e, v); break;
    case SRMECH_MVAL_LIST:    mm_serialise_list(e, v, depth); break;
    case SRMECH_MVAL_DICT:    mm_serialise_dict(e, v, depth); break;
    case SRMECH_MVAL_MAT:     mm_serialise_mat(e, v); break;
    default:                  e->overflow = 1; break;
    }
}

srmech_status_t srmech_mcp_serialise_result(const srmech_mval_t *v,
                                            char *buf, size_t buf_len,
                                            size_t *out_len)
{
    mm_emit_t e;
    /* NULL_ARG returns BEFORE any assert — a runtime-checked NULL (the two-pass
     * size-query passes buf==NULL; the caller may pass out_len==NULL) is
     * contractually handled, not an invariant violation (rc715). */
    if (v == NULL || out_len == NULL) { return SRMECH_ERR_NULL_ARG; }
    assert(v->kind >= SRMECH_MVAL_NONE && v->kind <= SRMECH_MVAL_MAT);
    e.buf = buf; e.cap = (buf == NULL) ? 0u : buf_len; e.used = 0u; e.overflow = 0;
    assert(e.overflow == 0 && e.used == 0u);        /* sink starts empty/clean  */
    mm_serialise(&e, v, 0u);
    *out_len = e.used;
    return e.overflow ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* ------------------------------------------------------------------
 * STAGE 2 — srmech_mcp_marshal_arg: typed-lower keyed on the registry type.
 * ------------------------------------------------------------------ */

typedef enum {
    MM_ACT_NOTIMPL = 0,     /* not bucket-(a); caller defers to pure       */
    MM_ACT_IDENTITY,        /* JSON-native passthrough                     */
    MM_ACT_BYTES,           /* base64 STR -> BYTES                         */
    MM_ACT_COMPLEX,         /* number | [re,im] -> COMPLEX                 */
    MM_ACT_INT_TUPLE,       /* LIST -> tuple (is_tuple bit)                */
    MM_ACT_SEQ_BYTES,       /* LIST of base64 STR -> LIST of BYTES         */
    MM_ACT_SEQ_COMPLEX,     /* LIST of complex leaves -> LIST of COMPLEX   */
    MM_ACT_SEQ_SEQ_COMPLEX, /* LIST of LIST of complex                     */
    MM_ACT_MAP_BYTES_BYTES, /* DICT of base64 key/value -> BYTES/BYTES     */
    MM_ACT_PAIR_BYTES_INT,  /* LIST of [base64, int] pairs                 */
    MM_ACT_PAIR_BYTES_BYTES,/* LIST of [base64, base64] pairs              */
    MM_ACT_MAT              /* rc190: nested LIST of numbers -> real MAT    */
} mm_action_t;

typedef struct { const char *type; mm_action_t action; } mm_type_rule_t;

/* Bucket-(a) CLEAN dispatch (mirrors srmech.mcp._coercion._PARAM_COERCERS).
 * Any type NOT here -> MM_ACT_NOTIMPL (the Mat/Vec/HV/ndarray float carriers
 * = rc190, the SpectralHandle/operator_name by-ref grammar = later). */
static const mm_type_rule_t MM_TYPE_RULES[] = {
    /* transforming families */
    {"bytes", MM_ACT_BYTES},
    {"complex", MM_ACT_COMPLEX},
    {"tuple[int, int]", MM_ACT_INT_TUPLE},
    {"Sequence[bytes]", MM_ACT_SEQ_BYTES},
    {"list[bytes]", MM_ACT_SEQ_BYTES},
    {"list[complex]", MM_ACT_SEQ_COMPLEX},
    {"list[list[complex]]", MM_ACT_SEQ_SEQ_COMPLEX},
    {"Mapping[bytes, bytes]", MM_ACT_MAP_BYTES_BYTES},
    {"list[tuple[bytes, int]]", MM_ACT_PAIR_BYTES_INT},
    {"list[tuple[bytes, bytes]]", MM_ACT_PAIR_BYTES_BYTES},
    /* rc190 float carriers. "Mat" builds a real MAT carrier (coerce_param =
     * Mat.from_rows(is_complex=False) — int/float leaves -> f64); "Vec" is
     * IDENTITY (coerce_param(_to_vec) passes the flat list through unchanged,
     * ints kept), the same passthrough shape as list[int]. */
    {"Mat", MM_ACT_MAT},
    {"Vec", MM_ACT_IDENTITY},
    /* JSON-native / passthrough families (coerce is _identity) */
    {"int", MM_ACT_IDENTITY}, {"Optional[int]", MM_ACT_IDENTITY},
    {"float", MM_ACT_IDENTITY}, {"Optional[float]", MM_ACT_IDENTITY},
    {"number", MM_ACT_IDENTITY}, {"bool", MM_ACT_IDENTITY},
    {"str", MM_ACT_IDENTITY}, {"Optional[str]", MM_ACT_IDENTITY},
    {"dict", MM_ACT_IDENTITY}, {"Optional[dict]", MM_ACT_IDENTITY},
    {"list", MM_ACT_IDENTITY}, {"list[int]", MM_ACT_IDENTITY},
    {"list[list[int]]", MM_ACT_IDENTITY}, {"Optional[list[float]]", MM_ACT_IDENTITY},
    {"iterable[int]", MM_ACT_IDENTITY}, {"sequence", MM_ACT_IDENTITY},
    {"int | float | str | list | dict", MM_ACT_IDENTITY},
    {"Sequence[str]", MM_ACT_IDENTITY}, {"list[list[list[float]]]", MM_ACT_IDENTITY},
    {"list[tuple[int, int]]", MM_ACT_IDENTITY},
    {"list[tuple[list[int], list[int]]]", MM_ACT_IDENTITY},
    {"ChainSpec", MM_ACT_IDENTITY},
    {"callable", MM_ACT_IDENTITY}, {"numpy.random.Generator", MM_ACT_IDENTITY},
    {"array('I')", MM_ACT_IDENTITY}, {"array('I')|None", MM_ACT_IDENTITY}
    /* NOTE: `pathlib.Path` is DELIBERATELY absent -> MM_ACT_NOTIMPL (defer to
     * pure). Its coerce->serialise round-trip goes through an OS-aware Path
     * object (str(WindowsPath) normalises '/'->'\\' on Windows; PosixPath keeps
     * '/'), so a portable C data-marshal CANNOT be byte-identical to Python on
     * every OS. Path separator normalisation is a host-runtime/OS concern, not a
     * platform-invariant bucket-(a) data type — the pure coerce_param does the
     * OS-correct thing; a bare-C host uses its own path convention. */
};

static mm_action_t mm_action_for(const char *type)
{
    size_t i, n = sizeof MM_TYPE_RULES / sizeof MM_TYPE_RULES[0];
    assert(type != NULL);
    assert(n > 0u);
    for (i = 0u; i < n; i++) {
        if (strcmp(MM_TYPE_RULES[i].type, type) == 0) { return MM_TYPE_RULES[i].action; }
    }
    return MM_ACT_NOTIMPL;
}

/* One complex leaf: a bare number -> (n, 0); a 2-list [re,im] -> (re, im). */
static srmech_status_t mm_leaf_complex(const srmech_mval_t *v,
                                       srmech_marshal_arena_t *a, srmech_mval_t **out)
{
    assert(v != NULL && a != NULL && out != NULL);
    assert(out != NULL);
    if (v->kind == SRMECH_MVAL_INT) { *out = mm_complex(a, (double)v->i, 0.0); }
    else if (v->kind == SRMECH_MVAL_FLOAT) { *out = mm_complex(a, v->re, 0.0); }
    else if (v->kind == SRMECH_MVAL_LIST && v->n == 2u) {
        const srmech_mval_t *r = v->items[0], *m = v->items[1];
        double re, im;
        if (r->kind != SRMECH_MVAL_INT && r->kind != SRMECH_MVAL_FLOAT) { return SRMECH_ERR_BAD_INPUT; }
        if (m->kind != SRMECH_MVAL_INT && m->kind != SRMECH_MVAL_FLOAT) { return SRMECH_ERR_BAD_INPUT; }
        re = (r->kind == SRMECH_MVAL_INT) ? (double)r->i : r->re;
        im = (m->kind == SRMECH_MVAL_INT) ? (double)m->i : m->re;
        *out = mm_complex(a, re, im);
    } else { return SRMECH_ERR_BAD_INPUT; }
    return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* One bytes leaf: a base64 STR -> a decoded BYTES node. */
static srmech_status_t mm_leaf_bytes(const srmech_mval_t *v,
                                     srmech_marshal_arena_t *a, srmech_mval_t **out)
{
    const unsigned char *buf; uint32_t blen; srmech_status_t st;
    assert(v != NULL && a != NULL && out != NULL);
    assert(out != NULL);
    if (v->kind != SRMECH_MVAL_STR) { return SRMECH_ERR_BAD_INPUT; }
    st = mm_b64_decode(v->s, v->slen, a, &buf, &blen);
    if (st != SRMECH_OK) { return st; }
    *out = mm_bytes(a, buf, blen);
    return (*out == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK;
}

/* Map a per-element leaf coercer over a LIST -> a fresh LIST. */
static srmech_status_t mm_map_seq(const srmech_mval_t *v, srmech_marshal_arena_t *a,
                                  int want_complex, srmech_mval_t **out)
{
    srmech_mval_t *lst; uint32_t i;
    assert(v != NULL && a != NULL && out != NULL);
    assert(out != NULL);
    if (v->kind != SRMECH_MVAL_LIST) { return SRMECH_ERR_BAD_INPUT; }
    lst = mm_list(a, v->n, 0);
    if (lst == NULL) { return SRMECH_ERR_OVERFLOW; }
    for (i = 0u; i < v->n; i++) {
        srmech_status_t st = want_complex
            ? mm_leaf_complex(v->items[i], a, &lst->items[i])
            : mm_leaf_bytes(v->items[i], a, &lst->items[i]);
        if (st != SRMECH_OK) { return st; }
    }
    *out = lst;
    return SRMECH_OK;
}

/* LIST of LIST of complex -> a fresh nested LIST. */
static srmech_status_t mm_map_seq_seq_complex(const srmech_mval_t *v,
                                              srmech_marshal_arena_t *a,
                                              srmech_mval_t **out)
{
    srmech_mval_t *lst; uint32_t i;
    assert(v != NULL && a != NULL && out != NULL);
    assert(out != NULL);
    if (v->kind != SRMECH_MVAL_LIST) { return SRMECH_ERR_BAD_INPUT; }
    lst = mm_list(a, v->n, 0);
    if (lst == NULL) { return SRMECH_ERR_OVERFLOW; }
    for (i = 0u; i < v->n; i++) {
        srmech_status_t st = mm_map_seq(v->items[i], a, 1, &lst->items[i]);
        if (st != SRMECH_OK) { return st; }
    }
    *out = lst;
    return SRMECH_OK;
}

/* DICT of base64 key/value -> a DICT of BYTES key/value. */
static srmech_status_t mm_map_map_bytes(const srmech_mval_t *v,
                                        srmech_marshal_arena_t *a, srmech_mval_t **out)
{
    srmech_mval_t *d; uint32_t i;
    assert(v != NULL && a != NULL && out != NULL);
    assert(out != NULL);
    if (v->kind != SRMECH_MVAL_DICT) { return SRMECH_ERR_BAD_INPUT; }
    d = mm_new(a, SRMECH_MVAL_DICT);
    if (d == NULL) { return SRMECH_ERR_OVERFLOW; }
    d->n = v->n;
    if (v->n > 0u) {
        d->keys = (srmech_mval_t **)mm_carve(a, (size_t)v->n * sizeof(void *));
        d->items = (srmech_mval_t **)mm_carve(a, (size_t)v->n * sizeof(void *));
        if (d->keys == NULL || d->items == NULL) { return SRMECH_ERR_OVERFLOW; }
    }
    for (i = 0u; i < v->n; i++) {
        srmech_status_t st = mm_leaf_bytes(v->keys[i], a, &d->keys[i]);
        if (st != SRMECH_OK) { return st; }
        st = mm_leaf_bytes(v->items[i], a, &d->items[i]);
        if (st != SRMECH_OK) { return st; }
    }
    *out = d;
    return SRMECH_OK;
}

/* LIST of [base64, X] pairs -> LIST of tuple[BYTES, X] (X = int or base64). */
static srmech_status_t mm_map_pairs(const srmech_mval_t *v, srmech_marshal_arena_t *a,
                                    int snd_is_bytes, srmech_mval_t **out)
{
    srmech_mval_t *lst; uint32_t i;
    assert(v != NULL && a != NULL && out != NULL);
    assert(out != NULL);
    if (v->kind != SRMECH_MVAL_LIST) { return SRMECH_ERR_BAD_INPUT; }
    lst = mm_list(a, v->n, 0);
    if (lst == NULL) { return SRMECH_ERR_OVERFLOW; }
    for (i = 0u; i < v->n; i++) {
        const srmech_mval_t *pr = v->items[i]; srmech_mval_t *tup, *fst, *snd;
        srmech_status_t st;
        if (pr->kind != SRMECH_MVAL_LIST || pr->n != 2u) { return SRMECH_ERR_BAD_INPUT; }
        st = mm_leaf_bytes(pr->items[0], a, &fst);
        if (st != SRMECH_OK) { return st; }
        if (snd_is_bytes) { st = mm_leaf_bytes(pr->items[1], a, &snd); }
        else if (pr->items[1]->kind == SRMECH_MVAL_INT) { snd = mm_int(a, pr->items[1]->i); st = (snd == NULL) ? SRMECH_ERR_OVERFLOW : SRMECH_OK; }
        else { return SRMECH_ERR_BAD_INPUT; }
        if (st != SRMECH_OK) { return st; }
        tup = mm_list(a, 2u, 1);
        if (tup == NULL) { return SRMECH_ERR_OVERFLOW; }
        tup->items[0] = fst; tup->items[1] = snd; lst->items[i] = tup;
    }
    *out = lst;
    return SRMECH_OK;
}

/* tuple[int, int]: a 2-element LIST re-tagged as a tuple (shallow, ints kept). */
static srmech_status_t mm_int_tuple(const srmech_mval_t *v, srmech_marshal_arena_t *a,
                                    srmech_mval_t **out)
{
    srmech_mval_t *tup; uint32_t i;
    assert(v != NULL && a != NULL && out != NULL);
    assert(out != NULL);
    if (v->kind != SRMECH_MVAL_LIST) { return SRMECH_ERR_BAD_INPUT; }
    tup = mm_list(a, v->n, 1);
    if (tup == NULL) { return SRMECH_ERR_OVERFLOW; }
    for (i = 0u; i < v->n; i++) { tup->items[i] = v->items[i]; }
    *out = tup;
    return SRMECH_OK;
}

/* "Mat": a rectangular nested LIST of plain numbers -> a real MAT carrier
 * (int/float leaves -> f64; matches coerce_param -> Mat.from_rows(is_complex=
 * False)). A non-LIST / non-rectangular / non-numeric leaf (e.g. a nested
 * [re,im] complex leaf) -> BAD_INPUT so the caller DEFERS to the pure
 * coerce_param (which builds the odd Mat / the op raises) — never a wrong
 * answer. An empty Mat (rows==0 or cols==0) marshals to a 0-element MAT. */
static srmech_status_t mm_mat_arg(const srmech_mval_t *v,
                                  srmech_marshal_arena_t *a, srmech_mval_t **out)
{
    uint32_t rows, cols, r, c; srmech_mval_t *mat; double *d;
    assert(v != NULL && a != NULL && out != NULL);
    assert(a->cur <= a->end);
    if (v->kind != SRMECH_MVAL_LIST) { return SRMECH_ERR_BAD_INPUT; }
    rows = v->n; cols = 0u;
    if (rows > 0u) {
        const srmech_mval_t *r0 = v->items[0];
        if (r0 == NULL || r0->kind != SRMECH_MVAL_LIST) { return SRMECH_ERR_BAD_INPUT; }
        cols = r0->n;
    }
    mat = mm_mat(a, rows, cols);
    if (mat == NULL) { return SRMECH_ERR_OVERFLOW; }
    d = (double *)(void *)mat->b;                       /* NULL iff rows*cols==0 */
    for (r = 0u; r < rows; r++) {
        const srmech_mval_t *row = v->items[r];
        if (row == NULL || row->kind != SRMECH_MVAL_LIST || row->n != cols) {
            return SRMECH_ERR_BAD_INPUT;
        }
        for (c = 0u; c < cols; c++) {
            const srmech_mval_t *el = row->items[c];
            if (el == NULL) { return SRMECH_ERR_BAD_INPUT; }
            if (el->kind == SRMECH_MVAL_INT) { d[(size_t)r * cols + c] = (double)el->i; }
            else if (el->kind == SRMECH_MVAL_FLOAT) { d[(size_t)r * cols + c] = el->re; }
            else { return SRMECH_ERR_BAD_INPUT; }        /* bool/[re,im]/nested -> defer */
        }
    }
    *out = mat;
    return SRMECH_OK;
}

srmech_status_t srmech_mcp_marshal_arg(const char *type_string,
                                       const srmech_mval_t *v,
                                       srmech_marshal_arena_t *a,
                                       srmech_mval_t **out)
{
    mm_action_t act;
    /* NULL_ARG returns BEFORE any assert — a runtime-checked NULL param is
     * contractually handled, not an invariant violation (rc715). */
    if (type_string == NULL || v == NULL || a == NULL || out == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    assert(a->cur <= a->end);                       /* genuine arena invariant */
    assert(v->kind >= SRMECH_MVAL_NONE && v->kind <= SRMECH_MVAL_MAT);
    if (v->kind == SRMECH_MVAL_NONE) { *out = (srmech_mval_t *)v; return SRMECH_OK; }
    act = mm_action_for(type_string);
    switch (act) {
    case MM_ACT_NOTIMPL:         return SRMECH_ERR_NOT_IMPL;
    case MM_ACT_IDENTITY:        *out = (srmech_mval_t *)v; return SRMECH_OK;
    case MM_ACT_BYTES:           return mm_leaf_bytes(v, a, out);
    case MM_ACT_COMPLEX:         return mm_leaf_complex(v, a, out);
    case MM_ACT_INT_TUPLE:       return mm_int_tuple(v, a, out);
    case MM_ACT_SEQ_BYTES:       return mm_map_seq(v, a, 0, out);
    case MM_ACT_SEQ_COMPLEX:     return mm_map_seq(v, a, 1, out);
    case MM_ACT_SEQ_SEQ_COMPLEX: return mm_map_seq_seq_complex(v, a, out);
    case MM_ACT_MAP_BYTES_BYTES: return mm_map_map_bytes(v, a, out);
    case MM_ACT_PAIR_BYTES_INT:  return mm_map_pairs(v, a, 0, out);
    case MM_ACT_PAIR_BYTES_BYTES:return mm_map_pairs(v, a, 1, out);
    case MM_ACT_MAT:             return mm_mat_arg(v, a, out);
    default:                     return SRMECH_ERR_NOT_IMPL;
    }
}

/* ------------------------------------------------------------------
 * FOUNDATION ROUND-TRIP PROVER — parse -> stage-1 -> marshal_arg -> serialise.
 * ------------------------------------------------------------------ */

size_t srmech_mcp_marshal_roundtrip_arena_bytes(size_t value_len)
{
    assert(sizeof(srmech_mval_t) <= 128u);
    assert(sizeof(srmech_json_value_t) <= 128u);
    return 256u * value_len + 65536u;
}

srmech_status_t srmech_mcp_marshal_roundtrip(const char *type_string,
                                             const char *value_json,
                                             size_t value_len,
                                             void *ws, size_t ws_len,
                                             char *out, size_t out_cap,
                                             size_t *out_len)
{
    srmech_marshal_arena_t a; srmech_json_value_t *jroot = NULL;
    srmech_mval_t *raw = NULL, *typed = NULL; unsigned char *parse_ws;
    size_t pj; srmech_status_t st;
    /* NULL_ARG returns BEFORE any assert — the test drives out_len==NULL here,
     * which is contractually handled, not an invariant violation (rc715). */
    if (type_string == NULL || value_json == NULL || ws == NULL ||
        out == NULL || out_len == NULL) { return SRMECH_ERR_NULL_ARG; }
    assert(jroot == NULL && raw == NULL && typed == NULL);  /* clean pipeline start */
    srmech_marshal_arena_init(&a, ws, ws_len);
    assert(a.cur <= a.end);                         /* genuine arena invariant */
    pj = 128u * value_len + 16384u;
    parse_ws = mm_carve(&a, pj);
    if (parse_ws == NULL) { return SRMECH_ERR_OVERFLOW; }
    st = srmech_json_parse(value_json, value_len, parse_ws, pj, &jroot);
    if (st != SRMECH_OK) { return st; }
    st = srmech_mval_from_json(jroot, &a, &raw);
    if (st != SRMECH_OK) { return st; }
    st = srmech_mcp_marshal_arg(type_string, raw, &a, &typed);
    if (st != SRMECH_OK) { return st; }
    return srmech_mcp_serialise_result(typed, out, out_cap, out_len);
}
