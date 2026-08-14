/* srmech_chemistry.c — the chemistry domain's C parity surface (0.9.0rc379,
 * task T1050).
 *
 * srmech_parse_formula: parse a chemical formula string into element counts —
 * the C twin of srmech.chemistry.formula.parse_formula (Class F/G, a bounded
 * placeholder/byte scan, the srmech_template_render family). Multi-letter
 * element symbols ([A-Z][a-z]*), implicit/explicit ASCII-digit counts, and
 * arbitrarily NESTED parenthesised groups with a trailing multiplier
 * ("Ca3(PO4)2" -> {Ca:3, P:2, O:8}).
 *
 * ALGORITHM (JPL-clean: no goto, no malloc, no recursion; caller arena): a
 * single left-to-right scan emits RAW (element, count) tokens into the ws
 * arena, applying each ')' multiplier to the contiguous token range opened by
 * its '(' (a group-start-index stack, also in ws — so nested multipliers
 * compound). A final pass accumulates the raw tokens into the DISTINCT-element
 * output in first-seen order (matching the pure-Python body byte-for-byte).
 *
 * NEW symbol — ABI stays 10 (additive; the Python body is the complete,
 * byte-identical alternative and the parity oracle). */

#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

#include "srmech.h"

/* SRMECH_ELEM_SYM_CAP (the output symbol-buffer stride) is defined in srmech.h
 * so the Python ctypes marshal and this kernel agree on the stride. */

/* Non-negative a*b with an int64 overflow guard (counts are never negative
 * here, so a magnitude-only check suffices). SRMECH_ERR_OVERFLOW past MAX. */
static srmech_status_t sr_pf_mul(int64_t a, int64_t b, int64_t *out)
{
    assert(out != NULL);
    assert(a >= 0 && b >= 0);
    if (a == 0 || b == 0) {
        *out = 0;
        return SRMECH_OK;
    }
    if (a > INT64_MAX / b) {
        return SRMECH_ERR_OVERFLOW;
    }
    *out = a * b;
    return SRMECH_OK;
}

/* Read an ASCII-digit run at s[i..len); an absent run is the implicit
 * multiplicity 1. Writes the value to *out_count and the new index to *out_i.
 * SRMECH_ERR_OVERFLOW if the value leaves the int64 range. */
static srmech_status_t sr_pf_read_count(const char *s, size_t len, size_t i,
                                        int64_t *out_count, size_t *out_i)
{
    int64_t value = 0;
    size_t start = i;
    assert(s != NULL);
    assert(out_count != NULL && out_i != NULL);
    while (i < len && s[i] >= '0' && s[i] <= '9') {
        int64_t digit = (int64_t)(s[i] - '0');
        if (value > (INT64_MAX - digit) / 10) {
            return SRMECH_ERR_OVERFLOW;
        }
        value = value * 10 + digit;
        i++;
    }
    *out_count = (i == start) ? (int64_t)1 : value;
    *out_i = i;
    return SRMECH_OK;
}

/* Append a raw (symbol, count) token at index *rn (< cap). The symbol bytes
 * s[a..b) must fit SRMECH_ELEM_SYM_CAP-1; longer -> SRMECH_ERR_OVERFLOW. */
static srmech_status_t sr_pf_emit(char *raw_syms, int64_t *raw_counts,
                                  size_t *rn, size_t cap, const char *s,
                                  size_t a, size_t b, int64_t count)
{
    size_t sym_len = b - a;
    char *slot;
    assert(raw_syms != NULL && raw_counts != NULL && rn != NULL);
    assert(s != NULL && b >= a);
    if (*rn >= cap || sym_len + 1u > SRMECH_ELEM_SYM_CAP) {
        return SRMECH_ERR_OVERFLOW;
    }
    slot = raw_syms + (*rn) * SRMECH_ELEM_SYM_CAP;
    memcpy(slot, s + a, sym_len);
    slot[sym_len] = '\0';
    raw_counts[*rn] = count;
    (*rn)++;
    return SRMECH_OK;
}

/* Multiply raw_counts[start..end) in place by mult (the ')' group multiplier),
 * with per-entry overflow guard. Nested groups compound (an outer ')' re-scales
 * an already-inner-scaled range). */
static srmech_status_t sr_pf_group_close(int64_t *raw_counts, size_t start,
                                         size_t end, int64_t mult)
{
    size_t k;
    assert(raw_counts != NULL);
    assert(end >= start);
    for (k = start; k < end; k++) {
        srmech_status_t st = sr_pf_mul(raw_counts[k], mult, &raw_counts[k]);
        if (st != SRMECH_OK) {
            return st;
        }
    }
    return SRMECH_OK;
}

/* Accumulate raw tokens (first-seen order) into the distinct-element output.
 * A repeated symbol adds into its existing slot; a new one appends. */
static srmech_status_t sr_pf_accumulate(const char *raw_syms,
                                        const int64_t *raw_counts, size_t rn,
                                        char *out_syms, int64_t *out_counts,
                                        size_t out_cap, size_t *out_n)
{
    size_t i, j;
    assert(raw_syms != NULL && raw_counts != NULL);
    assert(out_syms != NULL && out_counts != NULL && out_n != NULL);
    *out_n = 0;
    for (i = 0; i < rn; i++) {
        const char *sym = raw_syms + i * SRMECH_ELEM_SYM_CAP;
        size_t hit = *out_n;
        for (j = 0; j < *out_n; j++) {
            if (strcmp(out_syms + j * SRMECH_ELEM_SYM_CAP, sym) == 0) {
                hit = j;
                break;
            }
        }
        if (hit == *out_n) {
            if (*out_n >= out_cap) {
                return SRMECH_ERR_OVERFLOW;
            }
            memcpy(out_syms + hit * SRMECH_ELEM_SYM_CAP, sym, SRMECH_ELEM_SYM_CAP);
            out_counts[hit] = raw_counts[i];
            (*out_n)++;
        } else {
            if (out_counts[hit] > INT64_MAX - raw_counts[i]) {
                return SRMECH_ERR_OVERFLOW;
            }
            out_counts[hit] += raw_counts[i];
        }
    }
    return SRMECH_OK;
}

/* Scan s[0..len) into raw tokens (with paren multipliers applied). raw_syms /
 * raw_counts / grp_stack are ws scratch of >= len entries. Writes the raw token
 * count to *rn. SRMECH_ERR_BAD_INPUT on malformed input (unbalanced parens,
 * unexpected byte, empty). */
static srmech_status_t sr_pf_scan(const char *s, size_t len, char *raw_syms,
                                  int64_t *raw_counts, size_t *grp_stack,
                                  size_t cap, size_t *rn)
{
    size_t i = 0, depth = 0;
    srmech_status_t st;
    assert(s != NULL || len == 0);
    assert(raw_syms != NULL && raw_counts != NULL && grp_stack != NULL && rn != NULL);
    *rn = 0;
    while (i < len) {
        char c = s[i];
        if (c == '(') {
            grp_stack[depth++] = *rn;
            i++;
        } else if (c == ')') {
            int64_t mult;
            i++;
            st = sr_pf_read_count(s, len, i, &mult, &i);
            if (st != SRMECH_OK) { return st; }
            if (depth == 0) { return SRMECH_ERR_BAD_INPUT; }
            depth--;
            st = sr_pf_group_close(raw_counts, grp_stack[depth], *rn, mult);
            if (st != SRMECH_OK) { return st; }
        } else if (c >= 'A' && c <= 'Z') {
            size_t a = i++;
            size_t b;
            int64_t count;
            while (i < len && s[i] >= 'a' && s[i] <= 'z') { i++; }
            b = i;                         /* symbol ends BEFORE the count digits */
            st = sr_pf_read_count(s, len, i, &count, &i);
            if (st != SRMECH_OK) { return st; }
            st = sr_pf_emit(raw_syms, raw_counts, rn, cap, s, a, b, count);
            if (st != SRMECH_OK) { return st; }
        } else if (c == ' ' || c == '\t') {
            i++;
        } else {
            return SRMECH_ERR_BAD_INPUT;
        }
    }
    return (depth == 0) ? SRMECH_OK : SRMECH_ERR_BAD_INPUT;
}

/* Minimum ws_len BYTES for srmech_parse_formula given a formula of `len`
 * bytes: room for <= len raw tokens (symbols + counts) and a group-start stack
 * of depth <= len. */
size_t srmech_parse_formula_ws_bound(size_t len)
{
    size_t tokens, syms, counts, stack;
    assert(len < SIZE_MAX);               /* tokens = len + 1 must not wrap */
    assert(SRMECH_ELEM_SYM_CAP >= 2u);    /* room for a 1-char symbol + NUL */
    tokens = len + 1u;
    syms = tokens * SRMECH_ELEM_SYM_CAP;
    counts = tokens * sizeof(int64_t);
    stack = tokens * sizeof(size_t);
    return syms + counts + stack + 32u;   /* +align/rounding headroom */
}

/* Public: parse a chemical formula into DISTINCT element counts.
 *   s, len        : the formula bytes.
 *   ws, ws_len    : caller arena (>= srmech_parse_formula_ws_bound(len)).
 *   out_syms      : out_cap * SRMECH_ELEM_SYM_CAP bytes; NUL-terminated symbols.
 *   out_counts    : int64[out_cap]; the accumulated count per element.
 *   out_cap       : capacity in ELEMENTS (>= distinct-element count; len+1 is
 *                   always enough).
 *   out_n         : the number of distinct elements written.
 * Returns SRMECH_OK, SRMECH_ERR_BAD_INPUT (malformed / empty), or
 * SRMECH_ERR_OVERFLOW (arena/out capacity or count overflow -> caller falls to
 * the pure-Python bignum body). */
srmech_status_t srmech_parse_formula(const char *s, size_t len, void *ws,
                                     size_t ws_len, char *out_syms,
                                     int64_t *out_counts, size_t out_cap,
                                     size_t *out_n)
{
    size_t tokens = len + 1u;
    size_t rn = 0;
    char *raw_syms;
    int64_t *raw_counts;
    size_t *grp_stack;
    srmech_status_t st;
    assert(out_syms != NULL && out_counts != NULL && out_n != NULL);
    assert(ws != NULL || ws_len == 0);
    *out_n = 0;
    if (s == NULL && len != 0) { return SRMECH_ERR_NULL_ARG; }
    if (ws == NULL || ws_len < srmech_parse_formula_ws_bound(len)) {
        return SRMECH_ERR_OVERFLOW;
    }
    /* Carve ws: int64 counts + size_t stack first (aligned), then symbol bytes. */
    raw_counts = (int64_t *)ws;
    grp_stack = (size_t *)(void *)(raw_counts + tokens);
    raw_syms = (char *)(void *)(grp_stack + tokens);
    st = sr_pf_scan(s, len, raw_syms, raw_counts, grp_stack, tokens, &rn);
    if (st != SRMECH_OK) { return st; }
    if (rn == 0) { return SRMECH_ERR_BAD_INPUT; }   /* no element parsed */
    return sr_pf_accumulate(raw_syms, raw_counts, rn, out_syms, out_counts,
                            out_cap, out_n);
}
