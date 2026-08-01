/*
 * srmech_eulerian.c — #1390 item 3: the Hierholzer walk-reconstruction the
 * directed Class-L genome store recovers a sequence with. A node-agnostic
 * Eulerian trail / circuit over a DIRECTED edge multiset, integer nodes
 * [0, n_nodes). Byte-identical to the pure srmech.math.laplacian.eulerian_path
 * / eulerian_circuit: the SAME feasibility test (degree balance + full-edge-
 * consumption connectivity — infeasible => out_feasible = 0, the pure `None`)
 * AND the SAME deterministic order (adjacency filled in edge order, consumed
 * from the END — the pure `avail[v].pop()`). No malloc (caller arenas), no
 * abs(), no float, no libm. ADDITIVE symbol — SRMECH_ABI_VERSION stays 5.
 */
#include <assert.h>
#include <stddef.h>
#include <stdint.h>

#include "srmech.h"

/* Determine the start node + feasibility (the pure plus/minus/imbalanced test).
 * circuit == balanced start (min out-bearing node, or the caller's start);
 * a valid path forces the unique out=in+1 node; anything else is not an
 * Eulerian trail (out_ok = 0). circuit_only rejects a non-circuit. */
static void eul_start(const uint64_t *outdeg, const uint64_t *indeg,
                      uint64_t n_nodes, int64_t start, int circuit_only,
                      int64_t *out_s, int *out_ok)
{
    uint64_t n_plus = 0, n_minus = 0, n_imb = 0;
    int64_t plus_node = -1, min_out = -1;
    assert(outdeg != NULL && indeg != NULL);
    assert(out_s != NULL && out_ok != NULL);
    for (uint64_t u = 0; u < n_nodes; u++) {
        if (outdeg[u] > 0u && min_out < 0) { min_out = (int64_t)u; }
        if (outdeg[u] == indeg[u]) { continue; }
        n_imb++;
        if (outdeg[u] == indeg[u] + 1u) { n_plus++; plus_node = (int64_t)u; }
        else if (indeg[u] == outdeg[u] + 1u) { n_minus++; }
    }
    if (n_imb == 0u) {
        *out_s = (start >= 0) ? start : min_out;
        *out_ok = 1;
    } else if (!circuit_only && n_plus == 1u && n_minus == 1u && n_imb == 2u) {
        *out_s = plus_node;
        *out_ok = 1;
    } else {
        *out_ok = 0;
    }
}

srmech_status_t srmech_eulerian_walk(
    const uint64_t *edge_u, const uint64_t *edge_v, size_t n_edges,
    uint64_t n_nodes, int64_t start, int circuit_only,
    uint64_t *outdeg, uint64_t *indeg, size_t *adj_start, size_t *cur,
    uint64_t *adj, uint64_t *stack, uint64_t *out_walk, size_t *out_walk_len,
    int *out_feasible)
{
    int64_t s = -1;
    int ok = 0;
    size_t top = 0, wl = 0;
    assert(edge_u != NULL || n_edges == 0u);
    assert(out_walk != NULL && out_feasible != NULL && out_walk_len != NULL);
    if (out_walk == NULL || out_feasible == NULL || out_walk_len == NULL ||
        outdeg == NULL || indeg == NULL || adj_start == NULL || cur == NULL ||
        (n_edges > 0u && (edge_u == NULL || edge_v == NULL || adj == NULL ||
                          stack == NULL))) {
        return SRMECH_ERR_NULL_ARG;
    }
    for (uint64_t u = 0; u < n_nodes; u++) { outdeg[u] = 0u; indeg[u] = 0u; }
    for (size_t e = 0; e < n_edges; e++) {
        if (edge_u[e] >= n_nodes || edge_v[e] >= n_nodes) {
            return SRMECH_ERR_BAD_INPUT;
        }
        outdeg[edge_u[e]]++;
        indeg[edge_v[e]]++;
    }
    eul_start(outdeg, indeg, n_nodes, start, circuit_only, &s, &ok);
    if (!ok) { *out_feasible = 0; *out_walk_len = 0; return SRMECH_OK; }
    adj_start[0] = 0u;                                   /* CSR offsets */
    for (uint64_t u = 0; u < n_nodes; u++) {
        adj_start[u + 1u] = adj_start[u] + (size_t)outdeg[u];
        cur[u] = adj_start[u];
    }
    for (size_t e = 0; e < n_edges; e++) {              /* fill in edge order */
        adj[cur[edge_u[e]]++] = edge_v[e];
    }
    for (uint64_t u = 0; u < n_nodes; u++) { cur[u] = adj_start[u + 1u]; }
    stack[top++] = (uint64_t)s;                         /* Hierholzer (pop END) */
    while (top > 0u) {
        uint64_t v = stack[top - 1u];
        if (cur[v] > adj_start[v]) {
            cur[v]--;
            stack[top++] = adj[cur[v]];
        } else {
            out_walk[wl++] = stack[--top];
        }
    }
    if (wl != n_edges + 1u) { *out_feasible = 0; *out_walk_len = 0; return SRMECH_OK; }
    for (size_t a = 0, b = wl - 1u; a < b; a++, b--) {  /* reverse in place */
        uint64_t t = out_walk[a]; out_walk[a] = out_walk[b]; out_walk[b] = t;
    }
    *out_walk_len = wl;
    *out_feasible = 1;
    return SRMECH_OK;
}
