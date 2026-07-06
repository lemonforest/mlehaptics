/*
 * srmech_coder.c — EXACT signal-processing coder / quantizer C peers.
 *
 * BATCH B6a (v0.9.0rc143): the five simpler EXACT sp_coder_dp ops earn their
 * same-rc C twins. These are integer / exact coders (entropy codes, codebook
 * lookup, run-length, threshold quantize), so the C is BYTE-IDENTICAL to the
 * pure-Python kernels — no float tolerance, no libm, no abs (Class-K sign is a
 * pin-slot boundary, never abs()). Additive symbols -> SRMECH_ABI_VERSION stays 3.
 *
 * The four C symbols (five ops; the two sign_quantise paths share one twin):
 *   - srmech_sign_quantise           <- closed_form + path_b sign_quantise.op
 *                                       (Class-K threshold {-1,0,+1} projection)
 *   - srmech_vector_quantise_encode  <- vector_quantisation.op encode
 *                                       (Class-K squared-distance nearest-code
 *                                        argmin; ties -> lowest index)
 *   - srmech_rle_encode              <- rle.op encode ((symbol, count) runs)
 *   - srmech_huffman_build_codes     <- huffman.op encode (canonical prefix
 *                                       codes; deterministic (freq, counter)
 *                                       node ordering identical to the Python
 *                                       heapq tree build)
 *
 * BATCH B6b (v0.9.0rc144) EXTENDS this file with the 4 harder sp_coder_dp ops:
 * LZ77 dictionary match (exact integer), the Viterbi / MLSE trellis DP (float
 * path metrics — byte-identical by reproducing the EXACT float accumulation
 * order + first-maximal argmax tie-break, deterministic double, no libm), and
 * the exact arithmetic (range) coder ENCODE (exact rational interval narrowing
 * via a srmech_bigint COMMON-DENOMINATOR integer recurrence — the fraction
 * arithmetic reduces to a single terminal gcd, byte-identical to the Python
 * fractions.Fraction encode). jpeg is DEFERRED (its DCT basis is the float
 * rational.cos cascade -> a NUMERIC differential-tested batch, NOT this exact
 * byte-identical one). All additive symbols -> SRMECH_ABI_VERSION stays 3.
 *
 * Canonical SSoT per [[feedback_science_is_ssot_not_project]]:
 *   - Donoho & Johnstone (1994) DOI 10.1093/biomet/81.3.425 (sign thresholding)
 *   - Linde, Buzo & Gray (1980) DOI 10.1109/TCOM.1980.1094577 (VQ)
 *   - Salomon (2007) Data Compression: The Complete Reference §1.4 (RLE)
 *   - Huffman (1952) DOI 10.1109/JRPROC.1952.273898 (prefix codes)
 *   - Ziv & Lempel (1977) DOI 10.1109/TIT.1977.1055714 (LZ77)
 *   - Viterbi (1967) DOI 10.1109/TIT.1967.1054010 + Forney (1973) (Viterbi)
 *   - Forney (1972) DOI 10.1109/TIT.1972.1054829 (MLSE)
 *   - Rissanen (1976) + Witten, Neal & Cleary (1987) DOI 10.1145/214762.214771
 *     (arithmetic coding)
 */

#include "srmech.h"

#include <assert.h>
#include <stddef.h>
#include <stdint.h>

/* ------------------------------------------------------------------ *
 * Class K — sign-quantise (closed_form + path_b share this twin)
 *
 * out[i] = sign(in[i] - threshold) with an optional dead-band around the
 * threshold. dead_band <= 0: two-level {+1 (in >= threshold), -1 (in <
 * threshold)}. dead_band > 0: three-level {+1 (in > threshold+dead_band),
 * -1 (in < threshold-dead_band), 0 (in the acceptance band)}. The threshold
 * IS the sign boundary — a Class-K pin-slot decision, no abs().
 * ------------------------------------------------------------------ */
srmech_status_t srmech_sign_quantise(const double *in,
                                     uint32_t      n,
                                     double        threshold,
                                     double        dead_band,
                                     int8_t       *out)
{
    assert(out != NULL);
    assert(n == 0u || in != NULL);
    if (out == NULL || (n > 0u && in == NULL)) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (dead_band <= 0.0) {
        for (uint32_t i = 0; i < n; i++) {
            out[i] = (in[i] >= threshold) ? (int8_t)1 : (int8_t)(-1);
        }
        return SRMECH_OK;
    }
    {
        double hi = threshold + dead_band;   /* single add, IEEE-deterministic */
        double lo = threshold - dead_band;
        for (uint32_t i = 0; i < n; i++) {
            if (in[i] > hi) {
                out[i] = (int8_t)1;
            } else if (in[i] < lo) {
                out[i] = (int8_t)(-1);
            } else {
                out[i] = (int8_t)0;          /* the dead-band (acceptance) zone */
            }
        }
    }
    return SRMECH_OK;
}

/* ------------------------------------------------------------------ *
 * Class K — vector-quantise encode (nearest-code argmin)
 *
 * For each input row, the index of the codebook entry minimising the SQUARED
 * Euclidean distance Sum_j (x_j - c_j)^2 (sqrt is monotone -> unnecessary for
 * an argmin). Accumulated left-to-right in a double so the result is bit-
 * identical to the pure-Python fold; ties resolve to the LOWEST index via a
 * strict `<` (a Class-K exact argmin, never a float abs).
 * ------------------------------------------------------------------ */
srmech_status_t srmech_vector_quantise_encode(const double *vectors,
                                              uint32_t      n_vec,
                                              const double *codebook,
                                              uint32_t      n_codes,
                                              uint32_t      dim,
                                              uint32_t     *out_idx)
{
    assert(codebook != NULL && out_idx != NULL);
    assert(n_codes > 0u && dim > 0u);
    if (codebook == NULL || out_idx == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n_codes == 0u || dim == 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (n_vec > 0u && vectors == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    for (uint32_t iv = 0; iv < n_vec; iv++) {
        const double *x = vectors + (size_t)iv * dim;
        uint32_t      best_k = 0u;
        double        best = 0.0;
        int           have = 0;
        for (uint32_t k = 0; k < n_codes; k++) {
            const double *c = codebook + (size_t)k * dim;
            double        dist = 0.0;
            for (uint32_t j = 0; j < dim; j++) {
                double diff = x[j] - c[j];
                dist += diff * diff;
            }
            if (have == 0 || dist < best) {   /* strict < keeps the lowest k */
                best = dist;
                best_k = k;
                have = 1;
            }
        }
        out_idx[iv] = best_k;
    }
    return SRMECH_OK;
}

/* ------------------------------------------------------------------ *
 * Class B/G — run-length encode
 *
 * Emits (symbol, count) run records; a run stops at a symbol change OR at
 * max_run (longer runs split across records). out_sym / out_count are caller
 * arenas of >= n entries (worst case: n singleton runs); out_npairs receives
 * the number of records written. Pure integer, byte-identical.
 * ------------------------------------------------------------------ */
srmech_status_t srmech_rle_encode(const uint8_t *data,
                                  uint32_t       n,
                                  uint32_t       max_run,
                                  uint8_t       *out_sym,
                                  uint32_t      *out_count,
                                  uint32_t      *out_npairs)
{
    uint32_t np = 0u;
    uint32_t i = 0u;
    assert(out_sym != NULL && out_count != NULL && out_npairs != NULL);
    assert(n == 0u || data != NULL);
    if (out_sym == NULL || out_count == NULL || out_npairs == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n > 0u && data == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    while (i < n) {
        uint8_t  sym = data[i];
        uint32_t count = 1u;
        while ((size_t)i + count < (size_t)n
               && data[(size_t)i + count] == sym
               && count < max_run) {
            count++;
        }
        out_sym[np] = sym;
        out_count[np] = count;
        np++;
        i += count;
    }
    *out_npairs = np;
    return SRMECH_OK;
}

/* ------------------------------------------------------------------ *
 * Class E/B — Huffman canonical prefix codes
 *
 * The tree build reproduces the Python heapq exactly: leaves carry a counter =
 * first-appearance index; each merge pops the two smallest (freq, counter)
 * nodes (all counters unique -> a total order, so "smallest" is unambiguous and
 * matches heapq's pop order), the first-popped taking bit '0' and the second
 * '1'; the merged node takes the next counter. Codes are read leaf->root and
 * reversed. No float, deterministic, byte-identical to _build_codes.
 * ------------------------------------------------------------------ */

/* Build the distinct-symbol frequency table in FIRST-APPEARANCE order (the
 * Python freq-dict order). Returns k = distinct-symbol count; fills sym[0..k-1]
 * and freq[0..k-1]. */
static uint32_t coder_huffman_freq_order(const uint8_t *data, uint32_t n,
                                         uint8_t *sym, uint32_t *freq)
{
    int32_t  slot[256];
    uint32_t k = 0u;
    assert(sym != NULL && freq != NULL);
    assert(data != NULL || n == 0u);
    for (uint32_t s = 0; s < 256u; s++) {
        slot[s] = -1;
    }
    for (uint32_t i = 0; i < n; i++) {
        uint8_t b = data[i];
        if (slot[b] < 0) {
            slot[b] = (int32_t)k;
            sym[k] = b;
            freq[k] = 1u;
            k++;
        } else {
            freq[slot[b]]++;
        }
    }
    return k;
}

/* Locate the two ACTIVE nodes with the smallest (freq, counter) lexicographic
 * key (a = smallest -> bit '0', b = 2nd smallest -> bit '1'). */
static void coder_huffman_min2(const uint32_t *nfreq, const uint32_t *ncnt,
                               const uint8_t *active, uint32_t nnodes,
                               uint32_t *a, uint32_t *b)
{
    uint32_t m1 = UINT32_MAX;
    uint32_t m2 = UINT32_MAX;
    assert(nfreq != NULL && ncnt != NULL && active != NULL);
    assert(a != NULL && b != NULL);
    for (uint32_t i = 0; i < nnodes; i++) {
        if (active[i] != 0u) {
            uint32_t fi = nfreq[i];
            uint32_t ci = ncnt[i];
            int less1 = (m1 == UINT32_MAX)
                        || (fi < nfreq[m1])
                        || (fi == nfreq[m1] && ci < ncnt[m1]);
            if (less1) {
                m2 = m1;
                m1 = i;
            } else {
                int less2 = (m2 == UINT32_MAX)
                            || (fi < nfreq[m2])
                            || (fi == nfreq[m2] && ci < ncnt[m2]);
                if (less2) {
                    m2 = i;
                }
            }
        }
    }
    *a = m1;
    *b = m2;
}

/* Merge k leaves into a binary tree via k-1 (freq, counter)-min merges. Fills
 * parent[]/side[] (for the leaf->root code walk) + left[]/right[] (for the DFS
 * ordering). Returns the root node index. */
static uint32_t coder_huffman_build_tree(uint32_t k, uint32_t *nfreq,
                                         uint32_t *ncnt, uint8_t *active,
                                         int32_t *parent, uint8_t *side,
                                         int32_t *left, int32_t *right)
{
    uint32_t counter = k;
    uint32_t nnodes = k;
    assert(k >= 2u);
    assert(nfreq != NULL && ncnt != NULL && active != NULL);
    for (uint32_t m = 0; m + 1u < k; m++) {
        uint32_t a = 0u;
        uint32_t b = 0u;
        coder_huffman_min2(nfreq, ncnt, active, nnodes, &a, &b);
        active[a] = 0u;
        active[b] = 0u;
        parent[a] = (int32_t)nnodes;
        side[a] = 0u;                         /* first-popped -> '0' */
        parent[b] = (int32_t)nnodes;
        side[b] = 1u;                         /* second-popped -> '1' */
        left[nnodes] = (int32_t)a;
        right[nnodes] = (int32_t)b;
        nfreq[nnodes] = nfreq[a] + nfreq[b];
        ncnt[nnodes] = counter;
        parent[nnodes] = -1;
        active[nnodes] = 1u;
        nnodes++;
        counter++;
    }
    return nnodes - 1u;                        /* last created node = root */
}

/* For each leaf, walk parent pointers to the root collecting side bits (leaf-
 * first), then reverse into out_code_str[sym*256 ..] with length out_code_len. */
static void coder_huffman_emit_codes(uint32_t k, const uint8_t *sym,
                                     const int32_t *parent, const uint8_t *side,
                                     uint32_t *out_code_len, char *out_code_str)
{
    assert(sym != NULL && parent != NULL && side != NULL);
    assert(out_code_len != NULL && out_code_str != NULL);
    for (uint32_t i = 0; i < k; i++) {
        char     tmp[256];
        uint32_t depth = 0u;
        int32_t  cur = (int32_t)i;
        uint8_t  s = sym[i];
        while (parent[cur] >= 0) {
            tmp[depth] = (side[cur] != 0u) ? '1' : '0';
            depth++;
            cur = parent[cur];
        }
        out_code_len[s] = depth;
        for (uint32_t j = 0; j < depth; j++) {
            out_code_str[(size_t)s * 256u + j] = tmp[depth - 1u - j];
        }
    }
}

/* Left-first DFS over the tree collecting leaf symbols in the order the Python
 * merged code-dict lists them (left subtree fully, then right subtree). No
 * recursion — an explicit index stack (<= 2*256 deep). */
static void coder_huffman_dfs_order(uint32_t root, uint32_t k,
                                    const int32_t *left, const int32_t *right,
                                    const uint8_t *sym, uint8_t *out_order,
                                    uint32_t *out_count)
{
    uint32_t stack[512];
    uint32_t top = 0u;
    uint32_t cnt = 0u;
    assert(left != NULL && right != NULL && sym != NULL);
    assert(out_order != NULL && out_count != NULL);
    stack[top++] = root;
    while (top > 0u) {
        uint32_t node = stack[--top];
        if (node < k) {
            out_order[cnt++] = sym[node];      /* leaf */
        } else {
            stack[top++] = (uint32_t)right[node];   /* push right first ... */
            stack[top++] = (uint32_t)left[node];    /* ... so left pops first */
        }
    }
    *out_count = cnt;
}

/* Build the canonical Huffman code table for `data`. out_code_len[256] is the
 * per-symbol code length (0 = symbol absent); out_code_str[256*256] holds each
 * present symbol's '0'/'1' code at [sym*256 ..]; out_order[256] lists the
 * present symbols in the Python code-dict order (out_order_count of them). */
srmech_status_t srmech_huffman_build_codes(const uint8_t *data,
                                           uint32_t       n,
                                           uint32_t      *out_code_len,
                                           char          *out_code_str,
                                           uint8_t       *out_order,
                                           uint32_t      *out_order_count)
{
    uint8_t  sym[256];
    uint32_t freq[512];
    uint32_t cnt[512];
    uint8_t  active[512];
    int32_t  parent[512];
    uint8_t  side[512];
    int32_t  left[512];
    int32_t  right[512];
    uint32_t k;
    uint32_t root;
    uint32_t order_count = 0u;
    assert(out_code_len != NULL && out_code_str != NULL);
    assert(out_order != NULL && out_order_count != NULL);
    if (out_code_len == NULL || out_code_str == NULL
        || out_order == NULL || out_order_count == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n > 0u && data == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    for (uint32_t s = 0; s < 256u; s++) {
        out_code_len[s] = 0u;
    }
    k = coder_huffman_freq_order(data, n, sym, freq);
    if (k == 0u) {
        *out_order_count = 0u;
        return SRMECH_OK;
    }
    if (k == 1u) {
        out_code_len[sym[0]] = 1u;             /* single-symbol special case */
        out_code_str[(size_t)sym[0] * 256u] = '0';
        out_order[0] = sym[0];
        *out_order_count = 1u;
        return SRMECH_OK;
    }
    for (uint32_t i = 0; i < k; i++) {
        cnt[i] = i;
        active[i] = 1u;
        parent[i] = -1;
    }
    root = coder_huffman_build_tree(k, freq, cnt, active,
                                    parent, side, left, right);
    coder_huffman_emit_codes(k, sym, parent, side, out_code_len, out_code_str);
    coder_huffman_dfs_order(root, k, left, right, sym, out_order, &order_count);
    *out_order_count = order_count;
    return SRMECH_OK;
}

/* ================================================================== *
 * BATCH B6b (v0.9.0rc144) — LZ77, Viterbi / MLSE trellis DP, arithmetic
 * coder ENCODE. See the file banner. jpeg deferred (float DCT -> numeric).
 * ================================================================== */

/* ------------------------------------------------------------------ *
 * Class A/G/B — LZ77 sliding-window encode
 *
 * For each position i, the longest match in the window [max(0,i-window),i)
 * is found; ties keep the FIRST ws scanned (largest offset), matching the
 * Python `if length > best_length` strict-greater update. Pure integer,
 * byte-identical.
 * ------------------------------------------------------------------ */

/* Longest match for position i over window [window_start, i); ties keep the
 * first ws (largest offset), as the Python strict `>` update does. */
static void coder_lz77_match(const uint8_t *data, uint32_t i,
                             uint32_t window_start, uint32_t max_match,
                             uint32_t *best_len, uint32_t *best_off)
{
    uint32_t bl = 0u;
    uint32_t bo = 0u;
    assert(data != NULL && best_len != NULL && best_off != NULL);
    assert(window_start <= i);
    for (uint32_t ws = window_start; ws < i; ws++) {
        uint32_t length = 0u;
        while (length < max_match
               && ws + length < i
               && data[ws + length] == data[i + length]) {
            length++;
        }
        if (length > bl) {
            bl = length;
            bo = i - ws;
        }
    }
    *best_len = bl;
    *best_off = bo;
}

/* Encode `data` to (offset, length, literal) tokens. out_literal[t] = -1 marks
 * the Python `None` literal (a match that runs to end-of-input). out_* are
 * caller arenas of >= n entries; *out_ntokens receives the token count. */
srmech_status_t srmech_lz77_encode(const uint8_t *data,
                                   uint32_t       n,
                                   uint32_t       window_size,
                                   uint32_t       lookahead_size,
                                   uint32_t      *out_offset,
                                   uint32_t      *out_length,
                                   int32_t       *out_literal,
                                   uint32_t      *out_ntokens)
{
    uint32_t nt = 0u;
    uint32_t i = 0u;
    assert(out_offset != NULL && out_length != NULL);
    assert(out_literal != NULL && out_ntokens != NULL);
    if (out_offset == NULL || out_length == NULL
        || out_literal == NULL || out_ntokens == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    if (n > 0u && data == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    while (i < n) {
        uint32_t window_start = (i > window_size) ? (i - window_size) : 0u;
        uint32_t rem = n - i;
        uint32_t max_match = (lookahead_size < rem) ? lookahead_size : rem;
        uint32_t best_len = 0u;
        uint32_t best_off = 0u;
        coder_lz77_match(data, i, window_start, max_match, &best_len, &best_off);
        out_offset[nt] = best_off;
        out_length[nt] = best_len;
        if (best_len > 0u && (size_t)i + best_len < (size_t)n) {
            out_literal[nt] = (int32_t)data[i + best_len];
            i += best_len + 1u;
        } else if (best_len > 0u) {
            out_literal[nt] = -1;                 /* Python None literal */
            i += best_len;
        } else {
            out_offset[nt] = 0u;
            out_literal[nt] = (int32_t)data[i];
            i += 1u;
        }
        nt++;
    }
    *out_ntokens = nt;
    return SRMECH_OK;
}

/* ------------------------------------------------------------------ *
 * Class L/K — Viterbi trellis DP (shared by MLSE)
 *
 * Log-probability forward sweep + argmax backtrace. The per-merge argmax is
 * the Class-K pin-slot expressed as a first-maximal scan (strict `>` keeps the
 * lowest index on ties, matching Python max(range(n), key=...)). All float
 * adds are accumulated in the SAME ORDER as the pure kernel so native == pure
 * bit-for-bit. No libm, no abs.
 * ------------------------------------------------------------------ */

/* First-maximal argmax over score[0..m-1] (Python max(range(m), key=...)). */
static uint32_t coder_argmax(const double *score, uint32_t m)
{
    uint32_t best = 0u;
    assert(score != NULL);
    assert(m > 0u);
    for (uint32_t i = 1u; i < m; i++) {
        if (score[i] > score[best]) {
            best = i;
        }
    }
    return best;
}

/* Backtrace: path[T-1] = argmax delta[T-1]; path[t] = psi[t+1][path[t+1]]. */
static void coder_viterbi_backtrace(const double *delta, const int32_t *psi,
                                    uint32_t T, uint32_t n_states,
                                    int32_t *out_path)
{
    const double *dlast = delta + (size_t)(T - 1u) * n_states;
    assert(delta != NULL && psi != NULL && out_path != NULL);
    assert(T > 0u);
    out_path[T - 1u] = (int32_t)coder_argmax(dlast, n_states);
    for (uint32_t t = T - 1u; t > 0u; t--) {
        int32_t nxt = out_path[t];
        out_path[t - 1u] = psi[(size_t)t * n_states + (uint32_t)nxt];
    }
}

/* The trellis DP + backtrace. delta / psi are caller scratch of T*n_states
 * each; out_path receives the T-state Viterbi path. */
static srmech_status_t coder_viterbi_dp(const int32_t *obs, uint32_t T,
                                        const double *A, const double *B,
                                        const double *pi, uint32_t n_states,
                                        uint32_t n_obs, double *delta,
                                        int32_t *psi, int32_t *out_path)
{
    assert(obs != NULL && A != NULL && B != NULL && pi != NULL);
    assert(delta != NULL && psi != NULL && out_path != NULL);
    if (T == 0u || n_states == 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    for (uint32_t s = 0u; s < n_states; s++) {
        delta[s] = pi[s] + B[(size_t)s * n_obs + (uint32_t)obs[0]];
    }
    for (uint32_t t = 1u; t < T; t++) {
        const double *dprev = delta + (size_t)(t - 1u) * n_states;
        double       *dcur = delta + (size_t)t * n_states;
        int32_t      *pcur = psi + (size_t)t * n_states;
        for (uint32_t s = 0u; s < n_states; s++) {
            uint32_t best = 0u;
            double   bsc = dprev[0] + A[s];
            for (uint32_t i = 1u; i < n_states; i++) {
                double sc = dprev[i] + A[(size_t)i * n_states + s];
                if (sc > bsc) {
                    bsc = sc;
                    best = i;
                }
            }
            pcur[s] = (int32_t)best;
            dcur[s] = bsc + B[(size_t)s * n_obs + (uint32_t)obs[t]];
        }
    }
    coder_viterbi_backtrace(delta, psi, T, n_states, out_path);
    return SRMECH_OK;
}

/* Public Viterbi: ws_delta / ws_psi are caller scratch of T*n_states each. */
srmech_status_t srmech_viterbi(const int32_t *obs, uint32_t T,
                               const double *A, const double *B,
                               const double *pi, uint32_t n_states,
                               uint32_t n_obs, double *ws_delta,
                               int32_t *ws_psi, int32_t *out_path)
{
    assert(ws_delta != NULL && ws_psi != NULL && out_path != NULL);
    assert(A != NULL && B != NULL && pi != NULL);
    if (obs == NULL || A == NULL || B == NULL || pi == NULL
        || ws_delta == NULL || ws_psi == NULL || out_path == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    return coder_viterbi_dp(obs, T, A, B, pi, n_states, n_obs,
                            ws_delta, ws_psi, out_path);
}

/* ------------------------------------------------------------------ *
 * Class L/K — MLSE (maximum-likelihood sequence estimation over an ISI
 * channel). Builds the finite-state trellis from the channel taps + alphabet
 * then runs the SAME Viterbi DP. log_a / log_nstates are the Class-N rational
 * log CONSTANTS computed once in Python (passed as exact doubles) so the trellis
 * float values — and hence the path — are byte-identical. Complex arithmetic
 * reproduces Python's complex __mul__ (ac-bd, ad+bc). No libm, no abs.
 * ------------------------------------------------------------------ */

/* Complex multiply: (ar+ai i)(br+bi i) = (ar*br-ai*bi) + (ar*bi+ai*br) i. */
static void coder_cmul(double ar, double ai, double br, double bi,
                       double *o_re, double *o_im)
{
    assert(o_re != NULL && o_im != NULL);
    assert(o_re != o_im);
    *o_re = ar * br - ai * bi;
    *o_im = ar * bi + ai * br;
}

/* state -> base-A digits (little-endian) into tup[0..memory-1]. */
static void coder_mlse_state_to_tuple(uint32_t s, uint32_t A, uint32_t memory,
                                      uint32_t *tup)
{
    uint32_t x = s;
    assert(tup != NULL);
    assert(A > 0u);
    for (uint32_t k = 0u; k < memory; k++) {
        tup[k] = x % A;
        x /= A;
    }
}

/* base-A digits -> state (Python tuple_to_state: s = s*A + tup[i], i high->low). */
static uint32_t coder_mlse_tuple_to_state(const uint32_t *tup, uint32_t A,
                                          uint32_t memory)
{
    uint32_t s = 0u;
    assert(tup != NULL);
    assert(A > 0u);
    for (uint32_t i = memory; i > 0u; i--) {
        s = s * A + tup[i - 1u];
    }
    return s;
}

/* The no-ISI (memory == 0) fast path: per-sample nearest-symbol argmin over
 * |obs - taps[0]*alpha[i]|^2 (strict `<` keeps the first minimum). */
static void coder_mlse_no_isi(const double *obs_re, const double *obs_im,
                              uint32_t T, double t0_re, double t0_im,
                              const double *alpha_re, const double *alpha_im,
                              uint32_t A, int32_t *out_path)
{
    assert(obs_re != NULL && obs_im != NULL && out_path != NULL);
    assert(alpha_re != NULL && alpha_im != NULL);
    for (uint32_t t = 0u; t < T; t++) {
        uint32_t best_i = 0u;
        double   best_d2 = 0.0;
        int      have = 0;
        for (uint32_t i = 0u; i < A; i++) {
            double pr, pit, er, ei, d2;
            coder_cmul(t0_re, t0_im, alpha_re[i], alpha_im[i], &pr, &pit);
            er = obs_re[t] - pr;
            ei = obs_im[t] - pit;
            d2 = er * er + ei * ei;
            if (have == 0 || d2 < best_d2) {
                best_d2 = d2;
                best_i = i;
                have = 1;
            }
        }
        out_path[t] = (int32_t)best_i;
    }
}

/* A_log[prev*n+next] = -log_a for the A reachable next-states, else neg_inf. */
static void coder_mlse_trans(double *A_log, uint32_t n_states, uint32_t A,
                             uint32_t memory, double neg_log_a, double neg_inf,
                             uint32_t *tup, uint32_t *ntup)
{
    assert(A_log != NULL && tup != NULL && ntup != NULL);
    assert(memory > 0u);
    for (uint32_t p = 0u; p < n_states; p++) {
        for (uint32_t q = 0u; q < n_states; q++) {
            A_log[(size_t)p * n_states + q] = neg_inf;
        }
    }
    for (uint32_t prev = 0u; prev < n_states; prev++) {
        coder_mlse_state_to_tuple(prev, A, memory, tup);
        for (uint32_t inp = 0u; inp < A; inp++) {
            uint32_t ns;
            ntup[0] = inp;                        /* new_tup = [inp] + prev[:-1] */
            for (uint32_t k = 1u; k < memory; k++) {
                ntup[k] = tup[k - 1u];
            }
            ns = coder_mlse_tuple_to_state(ntup, A, memory);
            A_log[(size_t)prev * n_states + ns] = neg_log_a;
        }
    }
}

/* B_log[s*T+t] = -|obs[t] - expected(s)|^2, expected = sum_k taps[k+1]*alpha[
 * tup[k]] (k=0..memory-1, in order) then += taps[0]*alpha[tup[0]]. */
static void coder_mlse_emit(double *B_log, uint32_t n_states, uint32_t T,
                            const double *obs_re, const double *obs_im,
                            const double *taps_re, const double *taps_im,
                            const double *alpha_re, const double *alpha_im,
                            uint32_t A, uint32_t memory, uint32_t *tup)
{
    assert(B_log != NULL && tup != NULL);
    assert(memory > 0u);
    for (uint32_t s = 0u; s < n_states; s++) {
        double e_re = 0.0, e_im = 0.0, pr, pit;
        coder_mlse_state_to_tuple(s, A, memory, tup);
        for (uint32_t k = 0u; k < memory; k++) {
            coder_cmul(taps_re[k + 1u], taps_im[k + 1u],
                       alpha_re[tup[k]], alpha_im[tup[k]], &pr, &pit);
            e_re += pr;
            e_im += pit;
        }
        coder_cmul(taps_re[0], taps_im[0], alpha_re[tup[0]], alpha_im[tup[0]],
                   &pr, &pit);
        e_re += pr;
        e_im += pit;
        for (uint32_t t = 0u; t < T; t++) {
            double er = obs_re[t] - e_re;
            double ei = obs_im[t] - e_im;
            B_log[(size_t)s * T + t] = -(er * er + ei * ei);
        }
    }
}

/* Public MLSE. L = memory+1 (tap count); n_states = A^memory (caller-computed).
 * dscratch carves A_log(n^2) | B_log(n*T) | pi(n) | delta(T*n); iscratch carves
 * psi(T*n) | obs_idx(T); uscratch carves tup(memory) | ntup(memory). out_path
 * receives the T input-symbol indices (0..A-1). */
srmech_status_t srmech_mlse(const double *obs_re, const double *obs_im,
                            uint32_t T, const double *taps_re,
                            const double *taps_im, uint32_t L,
                            const double *alpha_re, const double *alpha_im,
                            uint32_t A, uint32_t n_states, double log_a,
                            double log_nstates, double *dscratch,
                            int32_t *iscratch, uint32_t *uscratch,
                            int32_t *out_path)
{
    uint32_t memory;
    srmech_status_t st;
    assert(obs_re != NULL && obs_im != NULL && out_path != NULL);
    assert(taps_re != NULL && alpha_re != NULL);
    if (L == 0u || A == 0u || n_states == 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    if (T == 0u) {
        return SRMECH_OK;                         /* empty -> empty path */
    }
    memory = L - 1u;
    if (memory == 0u) {
        coder_mlse_no_isi(obs_re, obs_im, T, taps_re[0], taps_im[0],
                          alpha_re, alpha_im, A, out_path);
        return SRMECH_OK;
    }
    {
        double *A_log = dscratch;
        double *B_log = A_log + (size_t)n_states * n_states;
        double *pi = B_log + (size_t)n_states * T;
        double *delta = pi + n_states;
        int32_t *psi = iscratch;
        int32_t *obs_idx = psi + (size_t)T * n_states;
        uint32_t *tup = uscratch;
        uint32_t *ntup = uscratch + memory;
        coder_mlse_trans(A_log, n_states, A, memory, -log_a, -1e18, tup, ntup);
        coder_mlse_emit(B_log, n_states, T, obs_re, obs_im, taps_re, taps_im,
                        alpha_re, alpha_im, A, memory, tup);
        for (uint32_t s = 0u; s < n_states; s++) {
            pi[s] = -log_nstates;
        }
        for (uint32_t t = 0u; t < T; t++) {
            obs_idx[t] = (int32_t)t;
        }
        st = coder_viterbi_dp(obs_idx, T, A_log, B_log, pi, n_states, T,
                              delta, psi, out_path);
        if (st != SRMECH_OK) {
            return st;
        }
        for (uint32_t t = 0u; t < T; t++) {
            out_path[t] = (int32_t)((uint32_t)out_path[t] % A);
        }
    }
    return SRMECH_OK;
}

/* ------------------------------------------------------------------ *
 * Class N — arithmetic (range) coder ENCODE, exact rational
 *
 * The Python encode narrows a fractions.Fraction interval [lo, hi). Carrying a
 * COMMON DENOMINATOR D_k = total^k makes the whole loop EXACT INTEGER
 * (srmech_bigint) — nl_{k+1} = nl_k*total + (nh_k-nl_k)*c_lo,  nh likewise —
 * and the only rational step is a SINGLE terminal gcd reduction of nl/D and
 * nh/D. A reduced fraction is canonical, so the (num, den) pair is byte-
 * identical to the Python Fraction regardless of intermediate reduction. No
 * float, no libm, no abs; all limb storage is carved from the caller arena.
 * ------------------------------------------------------------------ */

typedef struct arith_ctx {
    srmech_bigint_t nl, nh;      /* running numerators over D_k            */
    srmech_bigint_t diff, base;  /* nh-nl ; nl*total                       */
    srmech_bigint_t tlo, thi;    /* diff*c_lo ; diff*c_hi                  */
    srmech_bigint_t nl2, nh2;    /* next numerators                        */
    srmech_bigint_t D, tmp;      /* denominator total^k ; mul/quot temp    */
    srmech_bigint_t gg, qq;      /* gcd ; quotient                         */
    srmech_bigint_t ctot, cval;  /* small-int constants total ; c_lo/c_hi  */
    uint32_t cap;
    void   *ws;
    size_t  ws_len;
} arith_ctx_t;

/* Limb count of a uint64 (>=1). */
static uint32_t arith_total_limbs(uint64_t total)
{
    uint32_t limbs = 0u;
    uint64_t t = total;
    assert(sizeof(t) == 8u);
    if (t == 0u) {
        return 1u;
    }
    while (t > 0u) {
        limbs++;
        t >>= 32;
    }
    assert(limbs >= 1u);
    return limbs;
}

/* Bump `count` uint32 limbs out of base[*cur..]; NULL on exhaustion. */
static uint32_t *arith_take(uint32_t *base, size_t words, size_t *cur,
                            size_t count)
{
    uint32_t *p;
    assert(base != NULL && cur != NULL);
    assert(*cur <= words);
    if (count > words || *cur > words - count) {
        return NULL;
    }
    p = base + *cur;
    *cur += count;
    return p;
}

/* Bind one carrier `b` to a fresh cap-limb slice of the arena. */
static srmech_status_t arith_bind(srmech_bigint_t *b, uint32_t *base,
                                  size_t words, size_t *cur, uint32_t cap)
{
    uint32_t *limbs = arith_take(base, words, cur, cap);
    assert(b != NULL);
    assert(cap > 0u);
    if (limbs == NULL) {
        return SRMECH_ERR_OVERFLOW;
    }
    b->limbs = limbs;
    b->cap = cap;
    b->n = 0u;
    b->sign = 0;
    return SRMECH_OK;
}

/* Carve all 14 carriers + the divmod/gcd scratch tail from `ws`. */
static srmech_status_t arith_ctx_init(arith_ctx_t *c, uint32_t n,
                                      uint64_t total, void *ws, size_t ws_len)
{
    uint32_t *base = (uint32_t *)ws;
    size_t words = ws_len / sizeof(uint32_t), cur = 0u;
    uint32_t lt = arith_total_limbs(total);
    size_t cap_sz = (size_t)lt * n + 16u;
    srmech_status_t st = SRMECH_OK;
    assert(c != NULL);
    assert((uintptr_t)ws % sizeof(uint32_t) == 0u || ws == NULL);
    if (cap_sz > 0x3FFFFFFFu) {
        return SRMECH_ERR_OVERFLOW;               /* absurd size -> pure path */
    }
    c->cap = (uint32_t)cap_sz;
    st |= arith_bind(&c->nl, base, words, &cur, c->cap);
    st |= arith_bind(&c->nh, base, words, &cur, c->cap);
    st |= arith_bind(&c->diff, base, words, &cur, c->cap);
    st |= arith_bind(&c->base, base, words, &cur, c->cap);
    st |= arith_bind(&c->tlo, base, words, &cur, c->cap);
    st |= arith_bind(&c->thi, base, words, &cur, c->cap);
    st |= arith_bind(&c->nl2, base, words, &cur, c->cap);
    st |= arith_bind(&c->nh2, base, words, &cur, c->cap);
    st |= arith_bind(&c->D, base, words, &cur, c->cap);
    st |= arith_bind(&c->tmp, base, words, &cur, c->cap);
    st |= arith_bind(&c->gg, base, words, &cur, c->cap);
    st |= arith_bind(&c->qq, base, words, &cur, c->cap);
    st |= arith_bind(&c->ctot, base, words, &cur, c->cap);
    st |= arith_bind(&c->cval, base, words, &cur, c->cap);
    if (st != SRMECH_OK) {
        return SRMECH_ERR_OVERFLOW;
    }
    c->ws = (void *)(base + cur);
    c->ws_len = (words - cur) * sizeof(uint32_t);
    assert(cur <= words);
    return SRMECH_OK;
}

/* One interval-narrowing step: nl,nh <- the D_{k+1} numerators; D <- D*total. */
static srmech_status_t arith_step(arith_ctx_t *c, uint32_t c_lo, uint32_t c_hi)
{
    srmech_status_t st;
    assert(c != NULL);
    assert(c->cap > 0u);
    st = srmech_bigint_sub(&c->diff, &c->nh, &c->nl);          /* nh - nl     */
    if (st == SRMECH_OK) { st = srmech_bigint_mul(&c->base, &c->nl, &c->ctot); }
    if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&c->cval, (int64_t)c_lo); }
    if (st == SRMECH_OK) { st = srmech_bigint_mul(&c->tlo, &c->diff, &c->cval); }
    if (st == SRMECH_OK) { st = srmech_bigint_add(&c->nl2, &c->base, &c->tlo); }
    if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&c->cval, (int64_t)c_hi); }
    if (st == SRMECH_OK) { st = srmech_bigint_mul(&c->thi, &c->diff, &c->cval); }
    if (st == SRMECH_OK) { st = srmech_bigint_add(&c->nh2, &c->base, &c->thi); }
    if (st == SRMECH_OK) { st = srmech_bigint_copy(&c->nl, &c->nl2); }
    if (st == SRMECH_OK) { st = srmech_bigint_copy(&c->nh, &c->nh2); }
    if (st == SRMECH_OK) { st = srmech_bigint_mul(&c->tmp, &c->D, &c->ctot); }
    if (st == SRMECH_OK) { st = srmech_bigint_copy(&c->D, &c->tmp); }
    return st;
}

/* Reduce num/D to lowest terms + render both as decimal into num_str/den_str
 * (D preserved for the sibling endpoint). num >= 0, D > 0. */
static srmech_status_t arith_render(arith_ctx_t *c, const srmech_bigint_t *num,
                                    char *num_str, char *den_str, size_t str_cap,
                                    size_t *num_len, size_t *den_len)
{
    srmech_status_t st;
    assert(c != NULL && num != NULL);
    assert(num_str != NULL && den_str != NULL);
    if (srmech_bigint_is_zero(num)) {             /* 0 -> 0/1 (Fraction canon) */
        num_str[0] = '0'; num_str[1] = '\0'; *num_len = 1u;
        den_str[0] = '1'; den_str[1] = '\0'; *den_len = 1u;
        return SRMECH_OK;
    }
    st = srmech_bigint_gcd(&c->gg, num, &c->D, c->ws, c->ws_len);
    if (st == SRMECH_OK) {
        st = srmech_bigint_divmod(&c->qq, NULL, num, &c->gg, c->ws, c->ws_len);
    }
    if (st == SRMECH_OK) {
        st = srmech_bigint_to_dec(&c->qq, num_str, str_cap, num_len,
                                  c->ws, c->ws_len);
    }
    if (st == SRMECH_OK) {
        st = srmech_bigint_divmod(&c->tmp, NULL, &c->D, &c->gg, c->ws, c->ws_len);
    }
    if (st == SRMECH_OK) {
        st = srmech_bigint_to_dec(&c->tmp, den_str, str_cap, den_len,
                                  c->ws, c->ws_len);
    }
    return st;
}

/* Public arithmetic-coder encode. clo[k], chi[k] are the cumulative bounds of
 * the k-th symbol; total is the frequency sum. lo_num/lo_den/hi_num/hi_den are
 * caller char buffers (>= str_cap) filled with the reduced-fraction decimals
 * (NUL-terminated); ws is the caller uint32 arena. n >= 1. */
srmech_status_t srmech_arithmetic_encode(const uint32_t *clo,
                                         const uint32_t *chi, uint32_t n,
                                         uint64_t total, char *lo_num,
                                         char *lo_den, char *hi_num,
                                         char *hi_den, size_t str_cap,
                                         size_t *lo_num_len, size_t *lo_den_len,
                                         size_t *hi_num_len, size_t *hi_den_len,
                                         void *ws, size_t ws_len)
{
    arith_ctx_t c;
    srmech_status_t st;
    assert(lo_num != NULL && lo_den != NULL && hi_num != NULL && hi_den != NULL);
    assert(lo_num_len != NULL && hi_num_len != NULL);
    if (clo == NULL || chi == NULL || ws == NULL || n == 0u || total == 0u) {
        return SRMECH_ERR_BAD_INPUT;
    }
    st = arith_ctx_init(&c, n, total, ws, ws_len);
    if (st != SRMECH_OK) {
        return st;
    }
    st = srmech_bigint_set_i64(&c.nl, 0);
    if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&c.nh, 1); }
    if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&c.D, 1); }
    if (st == SRMECH_OK) { st = srmech_bigint_set_i64(&c.ctot, (int64_t)total); }
    for (uint32_t k = 0u; k < n && st == SRMECH_OK; k++) {
        st = arith_step(&c, clo[k], chi[k]);
    }
    if (st == SRMECH_OK) {
        st = arith_render(&c, &c.nl, lo_num, lo_den, str_cap,
                          lo_num_len, lo_den_len);
    }
    if (st == SRMECH_OK) {
        st = arith_render(&c, &c.nh, hi_num, hi_den, str_cap,
                          hi_num_len, hi_den_len);
    }
    return st;
}
