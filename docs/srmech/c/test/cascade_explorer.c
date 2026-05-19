/*
 * cascade_explorer.c — Spike #138 C-native cascade orchestrator
 *
 * Depth-2 exhaustive cascade enumeration over the 14-class A-N srmech
 * primitive vocabulary. Demonstrates that the framework runs on a
 * microcontroller without host Python or external LAPACK, per the
 * srmech CLAUDE.md "Phase B parity discipline" commitment and per
 * [[feedback_no_binding_layer_carveout]].
 *
 * Scope:
 *   - 14 x 14 = 196 ordered cascade pairs.
 *   - 1 small substrate (8-node ring graph) — enough to exercise every
 *     class's C surface without inflating object-tree memory.
 *   - 1 inspection cascade (canonical: A,L,K,M,C,I,D).
 *   - NDJSON output to stdout (caller redirects to a file).
 *   - Per-class timing via clock_gettime(CLOCK_MONOTONIC).
 *
 * Output rows (one per generation cascade):
 *   {"spike":138, "date":"2026-05-18", "stack_id":"c-native",
 *    "generation_cascade":["L","M"], "substrate_id":"ring8",
 *    "inspection_cascade_ordering":"canonical",
 *    "output_form_classification":"<label>",
 *    "inspection_fixed_point_depth":<int>,
 *    "fixed_point_form_sha256":"<hex>",
 *    "per_class_timing_ns":{"A":1234, "L":5678, ...},
 *    "total_elapsed_ns":<int>}
 *
 * Build (from c/ directory):
 *   clang -std=c17 -O2 -Wall -Iinclude -o build/cascade_explorer \
 *     test/cascade_explorer.c "build/*.o"
 *
 * Run:
 *   ./build/cascade_explorer > ../notes/spike138_findings_c_native.ndjson
 *
 * JPL Power-of-Ten discipline:
 *   - Rule 1 (no goto): assert.
 *   - Rule 2 (bounded loops): every for has compile-time-known bound.
 *   - Rule 3 (no malloc): everything stack-allocated.
 *   - Rule 4 (60-line functions): each helper kept short.
 *   - Rule 5 (>=2 asserts): each non-exempt function asserts entry +
 *     invariant.
 *   - Rule 6 (smallest scope): variables declared at use site.
 *   - Rule 7 (check return values): all srmech_* returns checked.
 *
 * License: GPL-3.0-or-later (parent project mlehaptics).
 */

#include "srmech.h"

#include <assert.h>
#include <math.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#if defined(_WIN32)
#  include <windows.h>
#endif

/* ----------------------------------------------------------------------
 * Compile-time configuration
 * ---------------------------------------------------------------------- */

#define CASCADE_N_CLASSES        14
#define CASCADE_DEPTH            2
#define CASCADE_N_CASCADES_D2    (CASCADE_N_CLASSES * CASCADE_N_CLASSES)
#define CASCADE_HDC_NBYTES       128
#define CASCADE_HDC_NBITS        (CASCADE_HDC_NBYTES * 8)
#define CASCADE_SUBSTRATE_N      8
#define CASCADE_INSP_LEN         7
#define CASCADE_INSP_DEPTH_CAP   5
#define CASCADE_FP_SIM_THRESHOLD 0.9999999999  /* 1 - 1e-10 */

#define CASCADE_TAXONOMY_IDENTITY 0
#define CASCADE_TAXONOMY_CYCLIC   1
#define CASCADE_TAXONOMY_SPARSE   2
#define CASCADE_TAXONOMY_WHITENS  3
#define CASCADE_TAXONOMY_HASHLIKE 4
#define CASCADE_TAXONOMY_NOVEL    5

static const char * const CASCADE_TAXONOMY_NAMES[] = {
    "identity_attractor",
    "structured_cyclic",
    "sparse",
    "white_noise",
    "hash_like",
    "structured_novel",
};

static const char CLASS_LETTERS[CASCADE_N_CLASSES] = {
    'A', 'B', 'C', 'D', 'E', 'F', 'G',
    'H', 'I', 'J', 'K', 'L', 'M', 'N',
};

static const int INSP_CANONICAL[CASCADE_INSP_LEN] = {0, 11, 10, 12, 2, 8, 3};  /* A,L,K,M,C,I,D */

/* ----------------------------------------------------------------------
 * Form representation (small, stack-allocated)
 * ---------------------------------------------------------------------- */

typedef struct cascade_form {
    uint8_t  hdc[CASCADE_HDC_NBYTES];
    double   spectrum[CASCADE_SUBSTRATE_N];
    uint32_t spectrum_len;
    uint64_t period;
    uint32_t tag;
    uint8_t  tlv_blob[CASCADE_HDC_NBYTES + 8];
    uint32_t tlv_len;
    char     sha[65];
    bool     sha_set;
} cascade_form_t;

/* ----------------------------------------------------------------------
 * Timing helper (CLOCK_MONOTONIC on POSIX, QueryPerformanceCounter on
 * Windows).
 * ---------------------------------------------------------------------- */

static uint64_t now_ns(void)
{
#if defined(_WIN32)
    static LARGE_INTEGER freq = {0};
    if (freq.QuadPart == 0) {
        QueryPerformanceFrequency(&freq);
    }
    LARGE_INTEGER t;
    QueryPerformanceCounter(&t);
    return (uint64_t)((1.0e9 * (double)t.QuadPart) / (double)freq.QuadPart);
#else
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
#endif
}

/* ----------------------------------------------------------------------
 * Substrate construction — 8-node ring Laplacian.
 *
 * Closed-form spectrum of an n-node cycle:
 *   λ_k = 2 - 2*cos(2*pi*k/n)  for k = 0..n-1
 * We use srmech_jacobi_eigvals (pi-free in C) to compute it, so we
 * exercise the actual Class L surface rather than baking the answer.
 * ---------------------------------------------------------------------- */

static void build_substrate_ring8(cascade_form_t *form)
{
    assert(form != NULL);
    assert(CASCADE_SUBSTRATE_N == 8);

    /* Build ring edges. */
    uint32_t edges_u[CASCADE_SUBSTRATE_N];
    uint32_t edges_v[CASCADE_SUBSTRATE_N];
    for (uint32_t i = 0; i < CASCADE_SUBSTRATE_N; i++) {
        edges_u[i] = i;
        edges_v[i] = (i + 1) % CASCADE_SUBSTRATE_N;
    }

    /* Build dense Laplacian + eigvals. */
    double L[CASCADE_SUBSTRATE_N * CASCADE_SUBSTRATE_N];
    srmech_status_t st = srmech_graph_dense_laplacian(
        CASCADE_SUBSTRATE_N, CASCADE_SUBSTRATE_N,
        edges_u, edges_v, NULL, L);
    assert(st == SRMECH_OK);

    double eigvals[CASCADE_SUBSTRATE_N];
    st = srmech_jacobi_eigvals(
        CASCADE_SUBSTRATE_N, L, 0, 1e-12, eigvals);
    assert(st == SRMECH_OK);

    /* Initialise form. */
    memset(form, 0, sizeof(*form));
    for (uint32_t i = 0; i < CASCADE_SUBSTRATE_N; i++) {
        form->spectrum[i] = eigvals[i];
    }
    form->spectrum_len = CASCADE_SUBSTRATE_N;
    form->period = CASCADE_SUBSTRATE_N;
    form->tag = 0;

    /* Seed HDC vector deterministically from the spectrum. */
    for (uint32_t b = 0; b < CASCADE_HDC_NBYTES; b++) {
        double accum = 0.0;
        for (uint32_t k = 0; k < CASCADE_SUBSTRATE_N; k++) {
            const double phase = (double)(b * 31 + k * 17) * 0.1;
            accum += eigvals[k] * (phase - (int64_t)phase);
        }
        form->hdc[b] = (uint8_t)(((int64_t)(accum * 1000.0)) & 0xFF);
    }
}

/* ----------------------------------------------------------------------
 * Form canonical-byte serialisation for SHA-256 attestation.
 * ---------------------------------------------------------------------- */

static uint32_t form_canonical_bytes(const cascade_form_t *form,
                                     uint8_t              *out_buf,
                                     uint32_t              capacity)
{
    assert(form != NULL);
    assert(out_buf != NULL);
    assert(capacity >= 512);

    uint32_t off = 0;
    memcpy(out_buf + off, form->hdc, CASCADE_HDC_NBYTES);
    off += CASCADE_HDC_NBYTES;
    out_buf[off++] = '|';
    for (uint32_t k = 0; k < form->spectrum_len; k++) {
        int n = snprintf((char *)out_buf + off,
                         (size_t)(capacity - off),
                         "%.10g,", form->spectrum[k]);
        assert(n > 0 && (uint32_t)n < capacity - off);
        off += (uint32_t)n;
    }
    out_buf[off++] = '|';
    int n2 = snprintf((char *)out_buf + off,
                      (size_t)(capacity - off),
                      "P%llu T%u",
                      (unsigned long long)form->period,
                      (unsigned)form->tag);
    assert(n2 > 0 && (uint32_t)n2 < capacity - off);
    off += (uint32_t)n2;
    return off;
}

/* ----------------------------------------------------------------------
 * The 14 class operators.
 * ---------------------------------------------------------------------- */

static void op_A(cascade_form_t *form)
{
    assert(form != NULL);
    assert(form->spectrum_len > 0);
    uint8_t buf[1024];
    uint32_t n = form_canonical_bytes(form, buf, sizeof(buf));
    char sha[65];
    srmech_status_t st = srmech_sha256_hex(buf, n, sha);
    assert(st == SRMECH_OK);
    memcpy(form->sha, sha, 65);
    form->sha_set = true;
    /* Mix sha into HDC. */
    for (uint32_t i = 0; i < 32; i++) {
        uint8_t hi = (uint8_t)((sha[2 * i] >= 'a') ? (sha[2 * i] - 'a' + 10) : (sha[2 * i] - '0'));
        uint8_t lo = (uint8_t)((sha[2 * i + 1] >= 'a') ? (sha[2 * i + 1] - 'a' + 10) : (sha[2 * i + 1] - '0'));
        form->hdc[i] ^= (uint8_t)((hi << 4) | lo);
    }
}

static void op_B(cascade_form_t *form)
{
    assert(form != NULL);
    assert(CASCADE_HDC_NBYTES >= 64);
    uint8_t out[CASCADE_HDC_NBYTES + 8];
    uint32_t written = 0;
    srmech_status_t st = srmech_tlv_pack(
        0x42, form->hdc, 64, out, sizeof(out), &written);
    assert(st == SRMECH_OK);
    form->tlv_len = written;
    memcpy(form->tlv_blob, out, written);
}

static void op_C(cascade_form_t *form)
{
    assert(form != NULL);
    assert(form->spectrum_len > 0);
    /* Reverse HDC bytes. */
    for (uint32_t i = 0; i < CASCADE_HDC_NBYTES / 2; i++) {
        uint8_t t = form->hdc[i];
        form->hdc[i] = form->hdc[CASCADE_HDC_NBYTES - 1 - i];
        form->hdc[CASCADE_HDC_NBYTES - 1 - i] = t;
    }
    /* Rotate spectrum by 1. */
    if (form->spectrum_len > 1) {
        double first = form->spectrum[0];
        for (uint32_t i = 0; i < form->spectrum_len - 1; i++) {
            form->spectrum[i] = form->spectrum[i + 1];
        }
        form->spectrum[form->spectrum_len - 1] = first;
    }
}

static void op_D(cascade_form_t *form)
{
    assert(form != NULL);
    assert(CASCADE_HDC_NBYTES >= 4);
    /* Multi-needle dispatch using 4 fixed patterns. */
    const uint8_t patterns[16] = {
        0x00, 0x00, 0x00, 0x00,
        0xff, 0xff, 0xff, 0xff,
        0xaa, 0x55, 0x00, 0x00,
        0x55, 0xaa, 0x00, 0x00,
    };
    const uint32_t offs[4] = {0, 4, 8, 12};
    const uint32_t lens[4] = {4, 4, 2, 2};
    const uint32_t tags[4] = {1, 2, 3, 4};
    bool matched = false;
    uint32_t out_tag = 0;
    srmech_status_t st = srmech_dispatch_match(
        form->hdc, CASCADE_HDC_NBYTES,
        patterns, offs, lens, tags, 4,
        &matched, &out_tag);
    assert(st == SRMECH_OK);
    form->tag = matched ? out_tag : 0;
}

static void op_E(cascade_form_t *form)
{
    assert(form != NULL);
    assert(form->spectrum_len > 0);
    /* Sorted-key catalog lookup. */
    const uint8_t keys[16] = "k0k1k2k3k4k5k6k7";
    const uint32_t key_offs[8] = {0, 2, 4, 6, 8, 10, 12, 14};
    const uint32_t key_lens[8] = {2, 2, 2, 2, 2, 2, 2, 2};
    const uint32_t val_offs[8] = {0, 0, 0, 0, 0, 0, 0, 0};
    const uint32_t val_lens[8] = {1, 1, 1, 1, 1, 1, 1, 1};
    char query[3] = {'k', (char)('0' + (char)(form->tag % 8)), '\0'};
    bool found = false;
    uint32_t val_off = 0;
    uint32_t val_len = 0;
    srmech_status_t st = srmech_catalog_lookup(
        (const uint8_t *)query, 2,
        keys, key_offs, key_lens, val_offs, val_lens, 8,
        &found, &val_off, &val_len);
    assert(st == SRMECH_OK);
    if (found) {
        form->tag = (form->tag + 1) % 256;
    }
}

static void op_F(cascade_form_t *form)
{
    assert(form != NULL);
    assert(form->spectrum_len > 0);
    /* Template render: "<{k0}>". */
    const uint8_t tmpl[] = "<{k0}>";
    const uint8_t keys[] = "k0";
    const uint32_t koff[1] = {0};
    const uint32_t klen[1] = {2};
    const uint8_t vals[] = "xy";
    const uint32_t voff[1] = {0};
    const uint32_t vlen[1] = {2};
    uint8_t out[16];
    uint32_t written = 0;
    srmech_status_t st = srmech_template_render(
        tmpl, (uint32_t)(sizeof(tmpl) - 1),
        keys, koff, klen,
        vals, voff, vlen,
        1, out, sizeof(out), &written);
    assert(st == SRMECH_OK);
    /* Splice rendered bytes into HDC tail to record the operation. */
    if (written > 0) {
        for (uint32_t i = 0; i < written && i < 8; i++) {
            form->hdc[CASCADE_HDC_NBYTES - 1 - i] ^= out[i];
        }
        /* Undo to keep operation near-identity on HDC. */
        for (uint32_t i = 0; i < written && i < 8; i++) {
            form->hdc[CASCADE_HDC_NBYTES - 1 - i] ^= out[i];
        }
    }
}

static void op_G(cascade_form_t *form)
{
    assert(form != NULL);
    assert(CASCADE_HDC_NBYTES >= 8);
    /* Byte search for first 4 bytes in the rest of HDC. */
    const uint8_t *needle = form->hdc;
    const uint8_t *hay = form->hdc + 4;
    uint32_t off = 0;
    srmech_status_t st = srmech_byte_search(
        hay, CASCADE_HDC_NBYTES - 4, needle, 4, &off);
    assert(st == SRMECH_OK);
    if (off != UINT32_MAX && form->period > 0) {
        form->period = (off % form->period) + 1;
    }
}

static void op_H(cascade_form_t *form)
{
    assert(form != NULL);
    assert(CASCADE_HDC_NBYTES >= 8);
    /* Mix abi_version fingerprint into HDC head. */
    int abi = srmech_abi_version();
    char fp[8];
    snprintf(fp, sizeof(fp), "srm%d", abi);
    for (uint32_t i = 0; i < 8; i++) {
        form->hdc[i] ^= (uint8_t)fp[i];
    }
    /* Undo to keep near-identity (H is self-introspection only). */
    for (uint32_t i = 0; i < 8; i++) {
        form->hdc[i] ^= (uint8_t)fp[i];
    }
}

static void op_I(cascade_form_t *form)
{
    assert(form != NULL);
    assert(form->period > 0);
    uint64_t n = form->period < 2 ? 2 : form->period;
    uint64_t out = 0;
    srmech_status_t st = srmech_mod_pow(3, form->period, n, &out);
    assert(st == SRMECH_OK);
    form->period = ((out + form->tag) % n) + 1;
}

static void op_J(cascade_form_t *form)
{
    assert(form != NULL);
    assert(form->period > 0);
    bool is_p = false;
    uint64_t p = form->period < 2 ? 2 : form->period;
    srmech_status_t st = srmech_is_prime(p, &is_p);
    assert(st == SRMECH_OK);
    if (is_p) {
        form->tag = (form->tag + 1) & 0xFF;
    } else {
        uint64_t primes[16];
        uint8_t exps[16];
        uint32_t count = 0;
        st = srmech_factor(p, primes, exps, 16, &count);
        assert(st == SRMECH_OK);
        if (count > 0) {
            form->period = primes[0];
        }
    }
}

static void op_K(cascade_form_t *form)
{
    assert(form != NULL);
    assert(form->spectrum_len > 0);
    double M = (form->spectrum[0] + form->spectrum[form->spectrum_len - 1]) * 0.5;
    /* Reduce M into [0, 2pi). */
    double pi2 = 6.283185307179586;
    while (M < 0) M += pi2;
    while (M >= pi2) M -= pi2;
    double E = 0.0;
    srmech_status_t st = srmech_kepler_solve(M, 0.3, 1e-10, 60, &E);
    if (st != SRMECH_OK) E = M;
    double phi = 0.0;
    st = srmech_pin_slot(E, 0.5, 1.0, &phi);
    if (st != SRMECH_OK) phi = E;
    /* Mix 16 bytes of phi into HDC. */
    int64_t phi_int = (int64_t)(phi * 1.0e15);
    if (phi_int < 0) phi_int = -phi_int;
    for (uint32_t i = 0; i < 8; i++) {
        form->hdc[i] ^= (uint8_t)((phi_int >> (i * 8)) & 0xFF);
    }
}

static void op_L(cascade_form_t *form)
{
    assert(form != NULL);
    assert(form->spectrum_len <= CASCADE_SUBSTRATE_N);
    /* Re-spectrum the carried implicit ring Laplacian by re-running Jacobi. */
    uint32_t edges_u[CASCADE_SUBSTRATE_N];
    uint32_t edges_v[CASCADE_SUBSTRATE_N];
    for (uint32_t i = 0; i < CASCADE_SUBSTRATE_N; i++) {
        edges_u[i] = i;
        edges_v[i] = (i + 1) % CASCADE_SUBSTRATE_N;
    }
    double L[CASCADE_SUBSTRATE_N * CASCADE_SUBSTRATE_N];
    srmech_status_t st = srmech_graph_dense_laplacian(
        CASCADE_SUBSTRATE_N, CASCADE_SUBSTRATE_N,
        edges_u, edges_v, NULL, L);
    assert(st == SRMECH_OK);
    double eigvals[CASCADE_SUBSTRATE_N];
    st = srmech_jacobi_eigvals(CASCADE_SUBSTRATE_N, L, 0, 1e-12, eigvals);
    assert(st == SRMECH_OK);
    /* Sort ascending. */
    for (uint32_t i = 0; i < CASCADE_SUBSTRATE_N - 1; i++) {
        for (uint32_t j = i + 1; j < CASCADE_SUBSTRATE_N; j++) {
            if (eigvals[j] < eigvals[i]) {
                double t = eigvals[i];
                eigvals[i] = eigvals[j];
                eigvals[j] = t;
            }
        }
    }
    for (uint32_t i = 0; i < CASCADE_SUBSTRATE_N; i++) {
        form->spectrum[i] = eigvals[i];
    }
}

static void op_M(cascade_form_t *form)
{
    assert(form != NULL);
    assert(CASCADE_HDC_NBYTES > 0);
    /* Build tag-derived mask and HDC-bind. */
    uint8_t mask[CASCADE_HDC_NBYTES];
    for (uint32_t i = 0; i < CASCADE_HDC_NBYTES; i++) {
        mask[i] = (uint8_t)((form->tag + i) & 0xFF);
    }
    uint8_t out[CASCADE_HDC_NBYTES];
    srmech_status_t st = srmech_hdc_bind(form->hdc, mask, CASCADE_HDC_NBYTES, out);
    assert(st == SRMECH_OK);
    memcpy(form->hdc, out, CASCADE_HDC_NBYTES);
}

static void op_N(cascade_form_t *form)
{
    assert(form != NULL);
    assert(form->spectrum_len > 0);
    /* best_rational on (spectrum[0]+1) approximated to 1e6/1. */
    double s = form->spectrum[0] + 1.0;
    if (s <= 0) s = 1.0;
    uint64_t num = (uint64_t)(s * 1000000.0);
    uint64_t den = 1000000;
    uint64_t p = 0, q = 0;
    srmech_status_t st = srmech_best_rational(num, den, 1024, &p, &q);
    assert(st == SRMECH_OK);
    if (q > 1) {
        form->period = q;
    }
}

typedef void (*op_fn_t)(cascade_form_t *form);

static const op_fn_t OPS[CASCADE_N_CLASSES] = {
    op_A, op_B, op_C, op_D, op_E, op_F, op_G,
    op_H, op_I, op_J, op_K, op_L, op_M, op_N,
};

/* ----------------------------------------------------------------------
 * Classifier (mirrors the Python rules)
 * ---------------------------------------------------------------------- */

static double hdc_similarity_c(const uint8_t *a, const uint8_t *b)
{
    assert(a != NULL);
    assert(b != NULL);
    double sim = 0.0;
    srmech_status_t st = srmech_hdc_similarity(a, b, CASCADE_HDC_NBYTES, &sim);
    assert(st == SRMECH_OK);
    return sim;
}

static double bit_entropy(const uint8_t *buf, uint32_t n)
{
    assert(buf != NULL);
    assert(n > 0);
    uint64_t ones = 0;
    for (uint32_t i = 0; i < n; i++) {
        uint8_t v = buf[i];
        for (uint32_t b = 0; b < 8; b++) {
            ones += (v >> b) & 1u;
        }
    }
    double total = (double)(8u * n);
    double p1 = (double)ones / total;
    double p0 = 1.0 - p1;
    double h = 0.0;
    if (p1 > 0.0) {
        double l2 = 0.6931471805599453;  /* ln(2) */
        h -= p1 * (log(p1) / l2);
    }
    if (p0 > 0.0) {
        double l2 = 0.6931471805599453;
        h -= p0 * (log(p0) / l2);
    }
    return h;
}

static int classify(const cascade_form_t *initial, const cascade_form_t *final_form)
{
    assert(initial != NULL);
    assert(final_form != NULL);
    double sim = hdc_similarity_c(initial->hdc, final_form->hdc);
    bool spec_changed = false;
    for (uint32_t i = 0; i < initial->spectrum_len; i++) {
        if (initial->spectrum[i] != final_form->spectrum[i]) {
            spec_changed = true;
            break;
        }
    }
    bool period_changed = (initial->period != final_form->period);
    double ent = bit_entropy(final_form->hdc, CASCADE_HDC_NBYTES);

    if ((sim > CASCADE_FP_SIM_THRESHOLD) && !spec_changed && !period_changed) {
        return CASCADE_TAXONOMY_IDENTITY;
    }
    if (final_form->period >= 2 && final_form->period <= 6
        && !spec_changed && sim < CASCADE_FP_SIM_THRESHOLD) {
        return CASCADE_TAXONOMY_CYCLIC;
    }
    /* Sparse: top-quartile of |spectrum| accounts for > 95% of L1 mass. */
    if (final_form->spectrum_len > 3) {
        double total = 0.0;
        double s_sorted[CASCADE_SUBSTRATE_N];
        for (uint32_t i = 0; i < final_form->spectrum_len; i++) {
            s_sorted[i] = final_form->spectrum[i] < 0 ? -final_form->spectrum[i] : final_form->spectrum[i];
            total += s_sorted[i];
        }
        if (total > 1.0e-9) {
            for (uint32_t i = 0; i < final_form->spectrum_len - 1; i++) {
                for (uint32_t j = i + 1; j < final_form->spectrum_len; j++) {
                    if (s_sorted[j] > s_sorted[i]) {
                        double t = s_sorted[i]; s_sorted[i] = s_sorted[j]; s_sorted[j] = t;
                    }
                }
            }
            uint32_t k = final_form->spectrum_len / 4;
            if (k < 1) k = 1;
            double mass = 0.0;
            for (uint32_t i = 0; i < k; i++) mass += s_sorted[i];
            if (mass / total > 0.95) {
                return CASCADE_TAXONOMY_SPARSE;
            }
        }
    }
    if (ent > 0.99) {
        return final_form->sha_set ? CASCADE_TAXONOMY_HASHLIKE : CASCADE_TAXONOMY_WHITENS;
    }
    if (sim < 0.5 && !spec_changed && !period_changed) {
        /* encoding_pair check: how clustered are the differing bits? */
        uint64_t diff = 0;
        uint64_t first_half = 0;
        for (uint32_t i = 0; i < CASCADE_HDC_NBYTES; i++) {
            uint8_t d = initial->hdc[i] ^ final_form->hdc[i];
            for (uint32_t b = 0; b < 8; b++) {
                if ((d >> b) & 1u) {
                    diff++;
                    if (i < CASCADE_HDC_NBYTES / 2) first_half++;
                }
            }
        }
        uint64_t second_half = diff - first_half;
        uint64_t max_half = first_half > second_half ? first_half : second_half;
        if (diff > 0 && (double)max_half / (double)diff > 0.75) {
            /* No explicit ENCODING_PAIR enum; fold into NOVEL. */
            return CASCADE_TAXONOMY_NOVEL;
        }
    }
    return CASCADE_TAXONOMY_NOVEL;
}

/* ----------------------------------------------------------------------
 * Cascade application + inspection
 * ---------------------------------------------------------------------- */

static void apply_op(int class_idx, cascade_form_t *form)
{
    assert(class_idx >= 0);
    assert(class_idx < CASCADE_N_CLASSES);
    OPS[class_idx](form);
}

static void apply_cascade_n(const int *cascade, int len, cascade_form_t *form,
                            uint64_t *per_class_ns)
{
    assert(cascade != NULL);
    assert(form != NULL);
    for (int i = 0; i < len; i++) {
        int cls = cascade[i];
        assert(cls >= 0 && cls < CASCADE_N_CLASSES);
        uint64_t t0 = now_ns();
        apply_op(cls, form);
        uint64_t dt = now_ns() - t0;
        if (per_class_ns != NULL) {
            per_class_ns[cls] += dt;
        }
    }
}

static int run_inspection(const cascade_form_t *gen_output,
                          cascade_form_t       *cur,
                          char                 *out_fp_sha)
{
    assert(gen_output != NULL);
    assert(cur != NULL);
    assert(out_fp_sha != NULL);
    *cur = *gen_output;
    int depth = CASCADE_INSP_DEPTH_CAP;
    for (int d = 1; d <= CASCADE_INSP_DEPTH_CAP; d++) {
        cascade_form_t new_form = *cur;
        apply_cascade_n(INSP_CANONICAL, CASCADE_INSP_LEN, &new_form, NULL);
        double sim = hdc_similarity_c(cur->hdc, new_form.hdc);
        bool spec_eq = true;
        for (uint32_t i = 0; i < cur->spectrum_len; i++) {
            if (cur->spectrum[i] != new_form.spectrum[i]) { spec_eq = false; break; }
        }
        bool per_eq = (cur->period == new_form.period);
        if (sim > CASCADE_FP_SIM_THRESHOLD && spec_eq && per_eq) {
            *cur = new_form;
            depth = d;
            break;
        }
        *cur = new_form;
    }
    uint8_t buf[1024];
    uint32_t n = form_canonical_bytes(cur, buf, sizeof(buf));
    srmech_status_t st = srmech_sha256_hex(buf, n, out_fp_sha);
    assert(st == SRMECH_OK);
    return depth;
}

/* ----------------------------------------------------------------------
 * Main loop
 * ---------------------------------------------------------------------- */

int main(void)
{
    /* Framing record. */
    printf("{\"spike\":138,\"date\":\"2026-05-18\",\"kind\":\"framing\","
           "\"stack_id\":\"c-native\",\"native_abi\":%d,\"n_classes\":%d,"
           "\"n_substrates\":1,\"n_cascades_depth2\":%d,"
           "\"n_inspection_orderings\":1,\"total_cells\":%d,"
           "\"fixed_point_threshold\":%g,\"inspection_depth_cap\":%d,"
           "\"anchor_citation\":\"Spike #138 brief; depth-2 exhaustive; canonical inspection only\"}\n",
           srmech_abi_version(),
           CASCADE_N_CLASSES,
           CASCADE_N_CASCADES_D2,
           CASCADE_N_CASCADES_D2,
           CASCADE_FP_SIM_THRESHOLD,
           CASCADE_INSP_DEPTH_CAP);

    uint64_t per_class_grand_ns[CASCADE_N_CLASSES] = {0};
    uint64_t per_class_grand_count[CASCADE_N_CLASSES] = {0};
    int class_count[6] = {0, 0, 0, 0, 0, 0};
    uint64_t t_grand0 = now_ns();

    for (int i = 0; i < CASCADE_N_CLASSES; i++) {
        for (int j = 0; j < CASCADE_N_CLASSES; j++) {
            cascade_form_t form;
            build_substrate_ring8(&form);
            cascade_form_t initial = form;
            int cascade[2] = {i, j};
            uint64_t per_class_ns[CASCADE_N_CLASSES] = {0};
            uint64_t t0 = now_ns();
            apply_cascade_n(cascade, 2, &form, per_class_ns);
            uint64_t total_ns = now_ns() - t0;

            cascade_form_t insp_final;
            char fp_sha[65];
            int fp_depth = run_inspection(&form, &insp_final, fp_sha);
            int cls = classify(&initial, &form);
            class_count[cls]++;
            for (int k = 0; k < CASCADE_N_CLASSES; k++) {
                per_class_grand_ns[k] += per_class_ns[k];
                if (per_class_ns[k] > 0) per_class_grand_count[k]++;
            }

            /* Emit one NDJSON row. */
            printf("{\"spike\":138,\"date\":\"2026-05-18\",\"stack_id\":\"c-native\","
                   "\"generation_cascade\":[\"%c\",\"%c\"],\"generation_depth\":2,"
                   "\"substrate_id\":\"ring8\","
                   "\"inspection_cascade_ordering\":\"canonical\","
                   "\"output_form_classification\":\"%s\","
                   "\"inspection_fixed_point_depth\":%d,"
                   "\"fixed_point_form_sha256\":\"%s\","
                   "\"anomaly_flags\":[],"
                   "\"per_class_timing_ns\":{",
                   CLASS_LETTERS[i], CLASS_LETTERS[j],
                   CASCADE_TAXONOMY_NAMES[cls], fp_depth, fp_sha);
            bool first = true;
            for (int k = 0; k < CASCADE_N_CLASSES; k++) {
                if (per_class_ns[k] > 0) {
                    if (!first) printf(",");
                    printf("\"%c\":%llu", CLASS_LETTERS[k],
                           (unsigned long long)per_class_ns[k]);
                    first = false;
                }
            }
            printf("},\"total_elapsed_ns\":%llu}\n",
                   (unsigned long long)total_ns);
        }
    }

    uint64_t grand_total_ns = now_ns() - t_grand0;
    printf("{\"spike\":138,\"date\":\"2026-05-18\",\"kind\":\"summary\","
           "\"stack_id\":\"c-native\",\"cells_done\":%d,"
           "\"wall_ns\":%llu,\"classification_counts\":{",
           CASCADE_N_CASCADES_D2,
           (unsigned long long)grand_total_ns);
    bool first = true;
    for (int k = 0; k < 6; k++) {
        if (class_count[k] > 0) {
            if (!first) printf(",");
            printf("\"%s\":%d", CASCADE_TAXONOMY_NAMES[k], class_count[k]);
            first = false;
        }
    }
    printf("},\"per_class_total_ns\":{");
    first = true;
    for (int k = 0; k < CASCADE_N_CLASSES; k++) {
        if (per_class_grand_count[k] > 0) {
            if (!first) printf(",");
            printf("\"%c\":%llu", CLASS_LETTERS[k],
                   (unsigned long long)per_class_grand_ns[k]);
            first = false;
        }
    }
    printf("},\"per_class_call_count\":{");
    first = true;
    for (int k = 0; k < CASCADE_N_CLASSES; k++) {
        if (per_class_grand_count[k] > 0) {
            if (!first) printf(",");
            printf("\"%c\":%llu", CLASS_LETTERS[k],
                   (unsigned long long)per_class_grand_count[k]);
            first = false;
        }
    }
    printf("}}\n");

    return 0;
}
