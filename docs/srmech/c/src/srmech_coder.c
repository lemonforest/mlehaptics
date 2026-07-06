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
 * Canonical SSoT per [[feedback_science_is_ssot_not_project]]:
 *   - Donoho & Johnstone (1994) DOI 10.1093/biomet/81.3.425 (sign thresholding)
 *   - Linde, Buzo & Gray (1980) DOI 10.1109/TCOM.1980.1094577 (VQ)
 *   - Salomon (2007) Data Compression: The Complete Reference §1.4 (RLE)
 *   - Huffman (1952) DOI 10.1109/JRPROC.1952.273898 (prefix codes)
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
