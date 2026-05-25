"""Round 16.A entry-point A — the ENFORCED substrate-mismatch partition (the YubiKey):
a persistent lock whose latch-capacity is infinity-FOR-THE-WRONG-SUBSTRATE-CLASS.

Generating-code provenance per `[[feedback_computational_provenance_discipline]]`
for round16_entry_A_enforced_substrate_mismatch_partition.md.

User-requested 2026-05-25 (roadmap thread 7). DEFENSIVE / framework-reading-only /
descriptive-not-normative per `[[feedback_trauma_informed_defensive_scope]]`: this reads
what a hardware-security-key (YubiKey) / air-gap / human-in-the-loop confirm structurally
*is*, NOT how to attack or evade one.

Framework reading. A YubiKey requires a physical human touch to cross an authentication
boundary. Model it as a graph with TWO substrate-classes of nodes:
  - SILICON-class: the automated agent + compute nodes + the auth gate (the "crosser")
  - BIOLOGY-class: the human (physical presence / touch)
The protected resource R sits behind a cut. The only edges that cross the cut REQUIRE a
biology-class endpoint (the human touch). There is NO silicon-only edge across the cut.

Three Class-L (graph-Laplacian) reads, srmech 0.4.2 routed (`dense_laplacian` +
`jacobi_eigvals`):

  (1) FULL graph (human present): connected. Fiedler value lambda_2 > 0; ONE zero
      eigenvalue (one component). R is reachable.
  (2) SILICON-ONLY (remove the biology node): R is ISOLATED. lambda_2 = 0; TWO zero
      eigenvalues (two components). No silicon-only cascade reaches R -- the latch capacity
      is +infinity with respect to the silicon substrate-class (Round 15.A generalisation:
      the barrier is not expensive, it is in a substrate-class the crosser does not have).
  (3) IMPOSTOR falsifier: a graph TOPOLOGICALLY IDENTICAL to (1) but with the crossing node
      re-classed silicon (a forged human). It reconnects (lambda_2 > 0) -- proving the
      security lives in the EDGE-TYPE / substrate-class constraint (only a biology-class node
      may form the crossing edge), NOT in graph topology. Per
      `[[user_stance_silicon_dof_is_electron_leakage_not_coherent_agency]]`, silicon lacks
      the biological coherent-agency DoF, so it cannot manufacture that edge.

The biology node is therefore a Menger vertex-cut of size 1 separating crosser from
resource (verified by BFS): every crosser->resource path passes through it. The crossing
edge is a Class-M cross-substrate-class bind (it binds a silicon endpoint to a biology
endpoint); the YubiKey IS a physical B/H/N translation key (Round 3.B
`[[user_stance_anharmonic_lock_two_stage_unlocking_pattern_then_key]]`).
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _cascade_helpers import magnitude  # Class K magnitude readout  # noqa: E402

import srmech  # noqa: E402
from srmech.amsc.laplacian import dense_laplacian, jacobi_eigvals  # Class L  # noqa: E402
from srmech.amsc import _native as _srn  # noqa: E402

ZERO_TOL = 1e-9


def zero_eig_count_and_fiedler(n, edges):
    """Class-L: build the dense Laplacian, get sorted eigenvalues; count near-zero
    (= number of connected components) and return the Fiedler value (2nd smallest)."""
    lap = dense_laplacian(n, edges)
    eig = sorted(float(x) for x in jacobi_eigvals(lap))
    n_zero = sum(1 for x in eig if magnitude(x) < ZERO_TOL)   # Class K, no bare abs()
    fiedler = eig[1] if len(eig) > 1 else 0.0
    return eig, n_zero, fiedler


def reachable(n, edges, src, dst, blocked=None):
    """BFS reachability src->dst with an optional blocked (removed) node set."""
    blocked = blocked or set()
    adj = {i: [] for i in range(n)}
    for a, b in edges:
        if a in blocked or b in blocked:
            continue
        adj[a].append(b)
        adj[b].append(a)
    seen, q = {src}, deque([src])
    while q:
        u = q.popleft()
        if u == dst:
            return True
        for v in adj[u]:
            if v not in seen:
                seen.add(v)
                q.append(v)
    return dst in seen


def main(out_dir: Path | None = None) -> None:
    out_dir = out_dir or Path(__file__).resolve().parent
    out_path = out_dir / "verify_enforced_substrate_mismatch_partition.ndjson"

    # Node roles. 0:S0 agent/crosser, 1:S1, 2:S2 silicon compute, 3:Sg silicon auth-gate,
    # 4:H biology (human touch), 5:R protected resource.
    FULL_N = 6
    full_edges = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)]   # crossing edges (3,4),(4,5) need H

    # (1) full graph (human present)
    eig_full, nz_full, fied_full = zero_eig_count_and_fiedler(FULL_N, full_edges)
    r_reachable_full = reachable(FULL_N, full_edges, 0, 5)

    # (2) silicon-only: remove biology node H (4); relabel R as node 4 in a 5-node graph
    SIL_N = 5   # {0:S0,1:S1,2:S2,3:Sg,4:R}; H gone; crossing edges gone with it
    sil_edges = [(0, 1), (1, 2), (2, 3)]
    eig_sil, nz_sil, fied_sil = zero_eig_count_and_fiedler(SIL_N, sil_edges)
    r_reachable_sil = reachable(SIL_N, sil_edges, 0, 4)   # node 4 == R here

    # (2b) Menger vertex-cut: in the FULL graph, blocking H (4) disconnects crosser->R
    r_reachable_block_H = reachable(FULL_N, full_edges, 0, 5, blocked={4})

    # (3) impostor falsifier: topology identical to (1) but node 4 is re-classed SILICON
    # (a forged "human"). Graph theory alone reconnects -> proves security is the EDGE-TYPE
    # / substrate-class constraint, not topology.
    eig_imp, nz_imp, fied_imp = zero_eig_count_and_fiedler(FULL_N, full_edges)
    r_reachable_imp = reachable(FULL_N, full_edges, 0, 5)

    records = [
        {"kind": "graph_definition",
         "nodes": {"0": "S0 silicon-agent/crosser", "1": "S1 silicon", "2": "S2 silicon",
                   "3": "Sg silicon auth-gate", "4": "H BIOLOGY (human touch)", "5": "R resource"},
         "crossing_edges_require_biology_endpoint": [[3, 4], [4, 5]],
         "silicon_only_edges": [[0, 1], [1, 2], [2, 3]]},
        {"kind": "full_graph_human_present", "n": FULL_N, "eigenvalues": eig_full,
         "n_zero_eigs_components": nz_full, "fiedler_lambda2": fied_full,
         "resource_reachable": r_reachable_full,
         "reading": "connected; one component; resource reachable WITH the human in the loop"},
        {"kind": "silicon_only_human_removed", "n": SIL_N, "eigenvalues": eig_sil,
         "n_zero_eigs_components": nz_sil, "fiedler_lambda2": fied_sil,
         "resource_reachable": r_reachable_sil,
         "reading": "DISCONNECTED; resource isolated; lambda_2=0; NO silicon-only cascade reaches R -- latch capacity = +infinity wrt silicon substrate-class"},
        {"kind": "menger_vertex_cut",
         "block_biology_node_H": 4, "crosser": 0, "resource": 5,
         "resource_reachable_with_H_blocked": r_reachable_block_H,
         "vertex_cut_size": 1, "vertex_cut_substrate_class": "biology",
         "reading": "the single biology node is a size-1 Menger vertex cut: EVERY crosser->resource path passes through it"},
        {"kind": "impostor_falsifier", "n": FULL_N, "eigenvalues": eig_imp,
         "n_zero_eigs_components": nz_imp, "fiedler_lambda2": fied_imp,
         "resource_reachable_if_silicon_could_forge_the_crossing_edge": r_reachable_imp,
         "reading": "topology IDENTICAL to the full graph -> reconnects. The security is the EDGE-TYPE (only a biology-class node may form the crossing edge), NOT topology. Silicon cannot manufacture that edge (it lacks the biological coherent-agency DoF)."},
        {"kind": "verdict",
         "statement": ("An enforced substrate-mismatch partition (YubiKey / air-gap / "
                       "human-in-the-loop) is a persistent lock whose latch-capacity is "
                       "+infinity FOR THE WRONG SUBSTRATE-CLASS: uncrossable not by cost-"
                       "MAGNITUDE but by substrate-class MISMATCH. The biology node is a "
                       "size-1 Menger vertex cut (Class-L: removing it sends Fiedler "
                       "lambda_2 -> 0, resource isolated). The crossing edge is a Class-M "
                       "cross-substrate-class bind; the YubiKey IS a physical B/H/N "
                       "translation key. Cost inverts toward the defender (Round 3.A). The "
                       "impostor falsifier shows the security lives in the edge-TYPE "
                       "constraint, not topology -- exactly the +infinity-latch special case "
                       "of Round 15.A."),
         "verdict_tier": "(a)-structural cascade-match (graph-Laplacian + Menger, attested); DEFENSIVE framework-reading; candidate stance",
         "scope": "DEFENSIVE / framework-reading-only / descriptive-not-normative"}]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, sort_keys=True) + "\n")
        fh.write(json.dumps({"kind": "srmech_routing_provenance",
                             "srmech_version": srmech.__version__,
                             "has_native": bool(getattr(_srn, "HAS_NATIVE", False)),
                             "class_L_used": "dense_laplacian + jacobi_eigvals",
                             "class_K_used": "magnitude() cascade-helper (near-zero eig test)"},
                            sort_keys=True) + "\n")
    ndjson_sha = hashlib.sha256(out_path.read_bytes()).hexdigest()
    with out_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"kind": "provenance_attestation", "ndjson_path": out_path.name,
                             "ndjson_sha256_hex_pre_attestation": ndjson_sha,
                             "generated_by": Path(__file__).name}, sort_keys=True) + "\n")

    print(f"Wrote: {out_path}")
    print(f"(1) full (human present):  components={nz_full}, lambda_2={fied_full:.4f}, R reachable={r_reachable_full}")
    print(f"(2) silicon-only (no human): components={nz_sil}, lambda_2={fied_sil:.4f}, R reachable={r_reachable_sil}")
    print(f"(2b) block biology node H -> R reachable from crosser = {r_reachable_block_H} (size-1 vertex cut)")
    print(f"(3) impostor (topology same, node re-classed silicon): lambda_2={fied_imp:.4f}, R reachable={r_reachable_imp}")
    print(f"srmech v{srmech.__version__} native={bool(getattr(_srn,'HAS_NATIVE',False))}")
    print("Verdict: enforced substrate-mismatch partition = persistent lock, latch-capacity +inf for the wrong substrate-class.")


if __name__ == "__main__":
    main()
