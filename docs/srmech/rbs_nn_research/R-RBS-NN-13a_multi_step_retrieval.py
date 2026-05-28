"""R-RBS-NN-13a — Multi-step retrieval via Class L spectral walking

Phase 3a of R-RBS-NN-10_FOLLOWUP_PHASED_PLAN.md.

Tests whether spectral structure of the Tier 2 association graph
(via Class L Laplacian eigendecompose) enriches retrieval beyond
single-hop unbind.

Approach:
  1. Build adjacency matrix from Tier 2 synapse keys
  2. Compute Class L Laplacian + eigendecompose
  3. Use top-K eigvectors as a spectral embedding
  4. For multi-step retrieval: combine direct unbind (1-hop) with
     spectral-neighbor scoring (2-hop, 3-hop via eigenvector proximity)

Hypothesis:
  Multi-step retrieval recovers concepts associated via INTERMEDIATE
  bindings (e.g., A↔B and B↔C → 2-step retrieval(A) finds C even though
  A and C have no direct binding).

This extends the storage's retrieval semantics from "find direct
associates" to "find concepts in the local neighborhood of the
association graph".
"""
import json
import time
from pathlib import Path
import sys
import importlib.util

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

_spec_flat = importlib.util.spec_from_file_location(
    "two_tier_flat", Path(__file__).parent / "R-RBS-NN-10_two_tier_storage.py"
)
_mod_flat = importlib.util.module_from_spec(_spec_flat)
sys.modules["two_tier_flat"] = _mod_flat
_spec_flat.loader.exec_module(_mod_flat)
TwoTierRBSNNStorage = _mod_flat.TwoTierRBSNNStorage

from srmech.amsc import laplacian
from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION


def build_chain_graph(N: int) -> tuple[list[str], list[tuple[str, str]]]:
    """Build a deliberately CHAIN-structured association graph.

    Chain: c_0 ↔ c_1 ↔ c_2 ↔ ... ↔ c_{N-1}

    Multi-step retrieval should work well here because:
    - 1-hop from c_0 → c_1
    - 2-hop from c_0 → c_2 (via c_1)
    - 3-hop from c_0 → c_3 (via c_1, c_2)
    """
    tokens = [f"chain_{i:03d}" for i in range(N)]
    pairs = [(tokens[i], tokens[i + 1]) for i in range(N - 1)]
    return tokens, pairs


def build_star_graph(N: int) -> tuple[list[str], list[tuple[str, str]]]:
    """Build a star graph with one hub and N-1 spokes."""
    tokens = [f"star_{i:03d}" for i in range(N)]
    hub = tokens[0]
    pairs = [(hub, tokens[i]) for i in range(1, N)]
    return tokens, pairs


def adjacency_from_synapses(storage, tokens: list[str]) -> tuple[list[tuple[int, int]], list[float]]:
    """Build a symmetric adjacency edge list + weights from Tier 2 synapses."""
    token_to_idx = {tok: i for i, tok in enumerate(tokens)}
    edges = []
    weights = []
    for key, synapse in storage.tier2.items():
        a, b = key  # canonical sorted tuple
        if a in token_to_idx and b in token_to_idx:
            ia, ib = token_to_idx[a], token_to_idx[b]
            if ia < ib:
                edges.append((ia, ib))
                # Weight: current synapse density (≈ binding strength)
                weights.append(float(synapse.current_density))
    return edges, weights


def spectral_embedding(n_nodes: int, edges, weights, top_k: int = 8):
    """Compute Class L Laplacian eigendecompose and return top-K non-trivial eigvectors."""
    L = laplacian.dense_laplacian(n_nodes, edges, weights)
    eigvals, eigvecs = laplacian.hermitian_eigendecompose(L)
    eigvecs = eigvecs.real
    # Skip the trivial 0-eigenvalue eigvector (constant); take next K
    return eigvals[1 : top_k + 1], eigvecs[:, 1 : top_k + 1]


def multi_step_retrieve(
    storage,
    tokens: list[str],
    eigvecs: np.ndarray,
    query: str,
    max_step: int,
    top_k: int = 5,
):
    """Multi-step retrieval combining direct unbind + spectral proximity.

    Step 1 (direct): use existing retrieve_associated
    Step 2+ (spectral): rank concepts by eigenvector proximity in spectral
            embedding space; weight by step depth
    """
    token_to_idx = {tok: i for i, tok in enumerate(tokens)}
    query_idx = token_to_idx.get(query)
    if query_idx is None:
        return []

    # 1-hop: direct retrieval
    direct = storage.retrieve_associated(query, top_k=top_k * 2, threshold=0.0)
    direct_set = {t for t, _ in direct}

    # Multi-hop: spectral proximity in eigvec space
    query_embedding = eigvecs[query_idx]  # shape (top_k,)
    # Score each other concept by cosine similarity in spectral space
    sims = []
    for tok, idx in token_to_idx.items():
        if tok == query:
            continue
        other_embedding = eigvecs[idx]
        num = float(np.dot(query_embedding, other_embedding))
        denom = float(np.linalg.norm(query_embedding) * np.linalg.norm(other_embedding))
        if denom == 0:
            spec_sim = 0.0
        else:
            spec_sim = num / denom
        sims.append((tok, spec_sim))

    # Sort by spectral similarity; spectral nearest is the most-likely 2+hop
    sims.sort(key=lambda x: x[1], reverse=True)

    # Combine: direct 1-hop comes first, then spectral neighbors not in direct
    combined = []
    seen = set()
    for tok, score in direct[:top_k]:
        combined.append(("direct", tok, score))
        seen.add(tok)
    for tok, spec_sim in sims:
        if tok in seen or len(combined) >= top_k * (max_step + 1):
            continue
        combined.append((f"spectral_step{max_step}", tok, spec_sim))
        seen.add(tok)
    return combined


def test_multi_step_chain(D, N, max_step):
    """On a chain graph, test if multi-step retrieval finds c_{k} when starting at c_0."""
    tokens, pairs = build_chain_graph(N)
    storage = TwoTierRBSNNStorage(D=D, seed=42)
    for tok in tokens:
        storage.encode_concept(tok)
    storage.batch_learn(pairs, plasticity_density=0.67)

    # Compute spectral embedding
    edges, weights = adjacency_from_synapses(storage, tokens)
    if not edges:
        return {}
    _, eigvecs = spectral_embedding(len(tokens), edges, weights, top_k=8)

    # Test: starting at c_0, retrieve top-K. Check which c_k are found.
    results = []
    for query_idx in [0, len(tokens) // 2]:
        query = tokens[query_idx]
        retrieved = multi_step_retrieve(storage, tokens, eigvecs, query, max_step=max_step, top_k=10)
        found_indices = []
        for kind, tok, score in retrieved:
            if tok.startswith("chain_"):
                other_idx = int(tok.split("_")[1])
                steps_away = abs(other_idx - query_idx)
                found_indices.append((steps_away, tok, kind, score))
        found_indices.sort()
        results.append({
            "query": query,
            "query_idx": query_idx,
            "retrievals": [
                {"steps_away": s, "token": t, "kind": k, "score": float(sc)}
                for s, t, k, sc in found_indices[:8]
            ],
        })
    return results


def main():
    D = 8192
    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}; D={D}")
    print()

    print("=" * 80)
    print("Multi-step retrieval on chain graph (c_0 ↔ c_1 ↔ c_2 ↔ ...)")
    print("=" * 80)
    print()

    chain_results = []
    for N in [20, 50, 100]:
        print(f"Chain N={N}:")
        result = test_multi_step_chain(D, N, max_step=3)
        for entry in result:
            print(f"  Query '{entry['query']}' (idx {entry['query_idx']}):")
            for r in entry["retrievals"]:
                print(
                    f"    steps={r['steps_away']:>2}  {r['token']:<14} {r['kind']:<18} score={r['score']:+0.3f}"
                )
        chain_results.append({"N": N, "results": result})
        print()

    # Hypothesis check: did spectral retrieval find concepts 2+ hops away
    # that direct retrieval missed?
    print("=" * 80)
    print("Hypothesis check")
    print("=" * 80)
    spectral_found_count = 0
    direct_found_count = 0
    for entry in chain_results:
        for sub in entry["results"]:
            for r in sub["retrievals"]:
                if r["kind"] == "direct" and r["steps_away"] >= 2:
                    direct_found_count += 1
                if r["kind"].startswith("spectral") and r["steps_away"] >= 2:
                    spectral_found_count += 1
    print(f"  Direct retrievals at 2+ steps: {direct_found_count}")
    print(f"  Spectral retrievals at 2+ steps: {spectral_found_count}")
    if spectral_found_count > direct_found_count:
        print(f"  → Spectral walking ADDS multi-hop retrieval capability")
    elif spectral_found_count == direct_found_count:
        print(f"  → Spectral walking matches direct (no marginal gain)")
    else:
        print(f"  → Spectral walking underperforms direct (unexpected)")

    out = {
        "srmech_version": SRMECH_VERSION,
        "D": D,
        "chain_results": chain_results,
        "spectral_found_2plus": spectral_found_count,
        "direct_found_2plus": direct_found_count,
    }
    out_path = Path(__file__).parent / "R-RBS-NN-13a_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
