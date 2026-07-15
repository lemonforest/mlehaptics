/*
 * srmech_eulerian.c — Eulerian walk reconstruction over a DIRECTED edge
 * multiset (0.9.0rc245, gh #1390 item 3). The byte-exact C twin of
 * srmech.amsc.laplacian._hierholzer_walk (+ the degree validation / start
 * selection): rebuild the ordered node walk of a directed Eulerian path or
 * circuit — the sandroing round-trip (F1080/F1213).
 *
 * Iterative Hierholzer: a per-node CSR adjacency consumed from the TOP down, so
 * the LAST-inserted out-edge is taken first — the exact LIFO order the pure
 * `avail[v].pop()` uses, so the recovered walk is byte-identical. Caller-arena
 * only (no malloc); no abs. ADDITIVE symbol — SRMECH_ABI_VERSION stays 5.
 */
#include "srmech.h"

#include <assert.h>

/* Fill out/in degrees of the directed edge multiset into deg / indeg
 * (both nn-wide, pre-zeroed by the caller). */
static void eul_degrees(const uint32_t *edges, size_t ne,
                        uint32_t *deg, uint32_t *indeg)
{
    size_t e;
    assert(edges != NULL);
    assert(deg != NULL && indeg != NULL);
    for (e = 0u; e < ne; e++) {
        deg[edges[2u * e]] += 1u;
        indeg[edges[2u * e + 1u]] += 1u;
    }
}

/* Validate the Eulerian degree condition and select the start node into
 * *out_start. circuit != 0: every node balanced; start = `start` (has_start) or
 * the smallest node with an out-edge. circuit == 0 (path): at most one node
 * with out−in=+1 (the start) and one with −1, all others balanced; start = the
 * +1 node, else the smallest node with an out-edge. SRMECH_ERR_BAD_INPUT on any
 * violation or when no node has an out-edge. */
static srmech_status_t eul_start(const uint32_t *deg, const uint32_t *indeg,
                                 size_t nn, int circuit, int has_start,
                                 uint32_t start, uint32_t *out_start)
{
    size_t i;
    int n_plus = 0, n_minus = 0, have = 0;
    uint32_t s = 0u;
    assert(deg != NULL && indeg != NULL);
    assert(out_start != NULL);
    if (circuit) {
        for (i = 0u; i < nn; i++) {
            if (deg[i] != indeg[i]) { return SRMECH_ERR_BAD_INPUT; }
        }
        if (has_start) {
            if (start >= nn || deg[start] == 0u) { return SRMECH_ERR_BAD_INPUT; }
            *out_start = start; return SRMECH_OK;
        }
    } else {
        for (i = 0u; i < nn; i++) {
            if (deg[i] == indeg[i] + 1u) {
                n_plus++;
                if (!have) { s = (uint32_t)i; have = 1; }
            } else if (indeg[i] == deg[i] + 1u) {
                n_minus++;
            } else if (deg[i] != indeg[i]) {
                return SRMECH_ERR_BAD_INPUT;
            }
        }
        if (n_plus > 1 || n_minus > 1 || n_plus != n_minus) {
            return SRMECH_ERR_BAD_INPUT;
        }
        if (have) { *out_start = s; return SRMECH_OK; }
    }
    for (i = 0u; i < nn; i++) {                 /* smallest node with an out-edge */
        if (deg[i] != 0u) { *out_start = (uint32_t)i; return SRMECH_OK; }
    }
    return SRMECH_ERR_BAD_INPUT;                /* no edges reachable */
}

srmech_status_t srmech_eulerian_walk(
    const uint32_t *edges, size_t ne, int circuit, int has_start, uint32_t start,
    uint32_t *out_walk, size_t walk_cap, size_t *out_len, void *ws, size_t ws_len)
{
    uint32_t *deg, *indeg, *off, *ptr, *adj, *stack;
    size_t nn = 0u, need, e, i, sp = 0u, pl = 0u;
    uint32_t s = 0u, v;
    srmech_status_t st;
    assert(out_len != NULL);
    assert(ws != NULL || ws_len == 0u);
    if (out_len == NULL || (ne > 0u && edges == NULL) || ws == NULL) {
        return SRMECH_ERR_NULL_ARG;
    }
    *out_len = 0u;
    if (ne == 0u) { return SRMECH_OK; }         /* empty multiset -> empty walk */
    for (i = 0u; i < 2u * ne; i++) {            /* nn = max node id + 1 */
        if ((size_t)edges[i] + 1u > nn) { nn = (size_t)edges[i] + 1u; }
    }
    need = (4u * nn + 1u + 2u * ne + 1u) * sizeof(uint32_t);
    if (ws_len < need) { return SRMECH_ERR_OVERFLOW; }
    deg = (uint32_t *)ws;
    indeg = deg + nn;
    off = indeg + nn;
    ptr = off + nn + 1u;
    adj = ptr + nn;
    stack = adj + ne;
    for (i = 0u; i < nn; i++) { deg[i] = 0u; indeg[i] = 0u; }
    eul_degrees(edges, ne, deg, indeg);
    st = eul_start(deg, indeg, nn, circuit, has_start, start, &s);
    if (st != SRMECH_OK) { return st; }
    off[0] = 0u;                                /* CSR prefix sums */
    for (i = 0u; i < nn; i++) { off[i + 1u] = off[i] + deg[i]; }
    for (i = 0u; i < nn; i++) { ptr[i] = off[i]; }        /* fill cursor */
    for (e = 0u; e < ne; e++) {
        uint32_t a = edges[2u * e];
        adj[ptr[a]] = edges[2u * e + 1u];
        ptr[a] += 1u;
    }
    for (i = 0u; i < nn; i++) { ptr[i] = off[i + 1u]; }   /* consume top-down = LIFO */
    stack[sp++] = s;
    while (sp > 0u) {
        v = stack[sp - 1u];
        if (ptr[v] > off[v]) {
            ptr[v] -= 1u;
            stack[sp++] = adj[ptr[v]];
        } else {
            if (pl >= walk_cap) { return SRMECH_ERR_OVERFLOW; }
            out_walk[pl++] = stack[--sp];
        }
    }
    if (pl != ne + 1u) { return SRMECH_ERR_BAD_INPUT; }   /* not connected */
    for (i = 0u; i < pl / 2u; i++) {            /* reverse in place */
        uint32_t t = out_walk[i];
        out_walk[i] = out_walk[pl - 1u - i];
        out_walk[pl - 1u - i] = t;
    }
    *out_len = pl;
    return SRMECH_OK;
}
