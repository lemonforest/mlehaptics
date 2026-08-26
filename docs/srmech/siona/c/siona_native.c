/* siona_native.c — Siona's native plugin (the [profile.native] tier). See
 * siona_native.h. JPL Power-of-Ten clean; caller-owned memory only. */
#include "siona_native.h"

#include <assert.h>

/* FNV-1a 64-bit constants (Fowler-Noll-Vo; public-domain algorithm). */
#define SIONA_FNV64_OFFSET_BASIS 14695981039346656037ULL
#define SIONA_FNV64_PRIME        1099511628211ULL

/* Trivial accessor (JPL Rule 5 exempt class: no branches, no memory). */
int siona_native_abi_version(void)
{
    return SIONA_NATIVE_ABI_VERSION;
}

uint64_t siona_native_fnv1a64(const unsigned char *data, size_t len)
{
    assert(data != NULL);              /* contract: non-null buffer */
    assert(len <= SIONA_NATIVE_MAX_INPUT);  /* JPL Rule 2: bounded input */

    uint64_t hash = SIONA_FNV64_OFFSET_BASIS;
    for (size_t i = 0; i < len; i++) {
        hash ^= (uint64_t)data[i];
        hash *= SIONA_FNV64_PRIME;     /* wraps mod 2^64 by C unsigned rules */
    }
    return hash;
}

/* A "word byte": ASCII alnum, or any non-ASCII byte (>=0x80) so UTF-8 multibyte
 * sequences stay inside one token. Trivial predicate (JPL Rule 5 exempt). */
static int siona_is_word_byte(unsigned char c)
{
    return (c >= '0' && c <= '9') || (c >= 'a' && c <= 'z')
        || (c >= 'A' && c <= 'Z') || (c >= 0x80);
}

long siona_native_tokenize(const unsigned char *data, size_t len,
                           int32_t *out, size_t max_tokens)
{
    assert(data != NULL || len == 0);       /* non-null unless empty */
    assert(len <= SIONA_NATIVE_MAX_INPUT);  /* offsets fit in int32 */

    long count = 0;
    size_t i = 0;
    while (i < len) {                        /* bounded by len */
        while (i < len && !siona_is_word_byte(data[i])) {
            i++;                             /* skip separators */
        }
        if (i >= len) {
            break;
        }
        size_t tok_start = i;
        while (i < len && siona_is_word_byte(data[i])) {
            i++;                             /* consume the token */
        }
        if ((size_t)count >= max_tokens) {
            return -1;                       /* output would overflow */
        }
        out[2 * count] = (int32_t)tok_start;
        out[2 * count + 1] = (int32_t)(i - tok_start);
        count++;
    }
    return count;
}

/* Open-addressing insert-or-increment into the caller arena. Returns 1 for a
 * NEW key, 0 for an incremented existing key, -1 if the arena is full. */
static int siona_arena_bump(uint64_t *keys, uint32_t *vals, size_t cap,
                            uint64_t key)
{
    assert(keys != NULL && vals != NULL);
    assert(cap > 0 && (cap & (cap - 1)) == 0);   /* cap is a power of two */

    uint64_t mixed = key * SIONA_FNV64_PRIME;    /* cheap avalanche */
    size_t mask = cap - 1;
    size_t home = (size_t)(mixed >> 24) & mask;
    for (size_t probe = 0; probe < cap; probe++) {
        size_t slot = (home + probe) & mask;
        if (keys[slot] == SIONA_NATIVE_ARENA_EMPTY) {
            keys[slot] = key;
            vals[slot] = 1;
            return 1;
        }
        if (keys[slot] == key) {
            vals[slot] += 1;
            return 0;
        }
    }
    return -1;
}

long siona_native_cooccurrence_accumulate(const int32_t *token_ids,
                                          size_t n_tokens,
                                          const int32_t *doc_ends, size_t n_docs,
                                          int window, uint64_t *arena_keys,
                                          uint32_t *arena_vals, size_t arena_cap)
{
    assert(window >= 1);
    assert(arena_cap > 0 && (arena_cap & (arena_cap - 1)) == 0);

    long n_edges = 0;
    size_t start = 0;
    for (size_t d = 0; d < n_docs; d++) {
        size_t end = (size_t)doc_ends[d];
        if (end > n_tokens) {
            end = n_tokens;                  /* defensive clamp */
        }
        for (size_t a = start; a < end; a++) {
            size_t bmax = a + (size_t)window;
            if (bmax >= end) {
                bmax = end - 1;              /* end>=1 here (a<end) */
            }
            for (size_t b = a + 1; b <= bmax; b++) {
                int32_t ia = token_ids[a];
                int32_t jb = token_ids[b];
                if (ia == jb) {
                    continue;
                }
                int32_t lo = ia < jb ? ia : jb;
                int32_t hi = ia < jb ? jb : ia;
                uint64_t key = ((uint64_t)(uint32_t)lo << 32) | (uint32_t)hi;
                int r = siona_arena_bump(arena_keys, arena_vals, arena_cap, key);
                if (r < 0) {
                    return -1;               /* arena full */
                }
                n_edges += r;
            }
        }
        start = end;
    }
    return n_edges;
}

long siona_native_arena_compact(const uint64_t *arena_keys,
                                const uint32_t *arena_vals, size_t arena_cap,
                                int32_t *out_i, int32_t *out_j, uint32_t *out_w,
                                size_t max_out)
{
    assert(arena_keys != NULL && arena_vals != NULL);
    assert(out_i != NULL && out_j != NULL && out_w != NULL);

    long n = 0;
    for (size_t s = 0; s < arena_cap; s++) {
        if (arena_keys[s] == SIONA_NATIVE_ARENA_EMPTY) {
            continue;
        }
        if ((size_t)n >= max_out) {
            return -1;                       /* output would overflow */
        }
        out_i[n] = (int32_t)(arena_keys[s] >> 32);
        out_j[n] = (int32_t)(arena_keys[s] & 0xffffffffu);
        out_w[n] = arena_vals[s];
        n++;
    }
    return n;
}

/* Map a token's vocab id to a subgraph row index, or -1 if out of the subset. */
static int32_t siona_subset_index(int32_t id, const int32_t *node_map,
                                  size_t vocab_size)
{
    if (id < 0 || (size_t)id >= vocab_size) {
        return -1;
    }
    return node_map[id];
}

/* Accumulate the symmetric adjacency A of the windowed co-occurrence subgraph
 * (only pairs with BOTH endpoints in the subset) into the row-major `A`. */
static void siona_cooc_accumulate_A(const int32_t *token_ids, size_t n_tokens,
                                    const int32_t *doc_ends, size_t n_docs,
                                    int window, const int32_t *node_map,
                                    size_t vocab_size, int32_t n_sub, double *A)
{
    assert(node_map != NULL && A != NULL);
    assert(n_sub >= 0);

    size_t n = (size_t)n_sub;
    size_t start = 0;
    for (size_t d = 0; d < n_docs; d++) {
        size_t end = (size_t)doc_ends[d];
        if (end > n_tokens) {
            end = n_tokens;
        }
        for (size_t a = start; a < end; a++) {
            int32_t si = siona_subset_index(token_ids[a], node_map, vocab_size);
            if (si < 0) {
                continue;
            }
            size_t bmax = a + (size_t)window;
            if (bmax >= end) {
                bmax = end - 1;
            }
            for (size_t b = a + 1; b <= bmax; b++) {
                int32_t sj = siona_subset_index(token_ids[b], node_map, vocab_size);
                if (sj < 0 || sj == si) {
                    continue;
                }
                A[(size_t)si * n + (size_t)sj] += 1.0;   /* symmetric */
                A[(size_t)sj * n + (size_t)si] += 1.0;
            }
        }
        start = end;
    }
}

/* In-place A -> L = D - A: diagonal = row-degree, off-diagonal = -A[i][j]. */
static void siona_A_to_laplacian(double *M, int32_t n_sub)
{
    assert(M != NULL);
    assert(n_sub >= 0);

    size_t n = (size_t)n_sub;
    for (size_t i = 0; i < n; i++) {
        double deg = 0.0;
        for (size_t j = 0; j < n; j++) {
            deg += M[i * n + j];                 /* A[i][i] is 0 (no self-pairs) */
        }
        for (size_t j = 0; j < n; j++) {
            M[i * n + j] = (i == j) ? deg : -M[i * n + j];
        }
    }
}

long siona_native_cooccurrence_laplacian(const int32_t *token_ids, size_t n_tokens,
                                         const int32_t *doc_ends, size_t n_docs,
                                         int window, const int32_t *node_map,
                                         size_t vocab_size, int32_t n_sub,
                                         double *out_L)
{
    assert(window >= 1);
    assert(n_sub >= 0 && (size_t)n_sub <= SIONA_NATIVE_MAX_SUBSET);

    size_t nn = (size_t)n_sub * (size_t)n_sub;
    for (size_t k = 0; k < nn; k++) {
        out_L[k] = 0.0;
    }
    siona_cooc_accumulate_A(token_ids, n_tokens, doc_ends, n_docs, window,
                            node_map, vocab_size, n_sub, out_L);
    siona_A_to_laplacian(out_L, n_sub);
    return (long)n_sub;
}
