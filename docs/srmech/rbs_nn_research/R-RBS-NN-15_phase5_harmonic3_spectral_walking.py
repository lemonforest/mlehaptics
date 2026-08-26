"""R-RBS-NN-15 — Phase 5: validate F150 harmonic-3 reading on R-RBS-NN-13a testbed

Phase 5 first walk per R-RBS-NN-10_FOLLOWUP_PHASED_PLAN.md.

Tests whether F150's harmonic-3 reading of Class L (3-fold eigvec partition)
gives sharper multi-step retrieval than the uniform top-K approach from R13a.

R13a result baseline (chain N=100, query chain_000):
  Direct unbind:  finds chain_001 only (1-hop)
  Uniform top-K:  finds chain_002..chain_006 spectral sim 0.93-0.998

This test:
  Partition eigvecs into 3 groups by eigenvalue magnitude:
    Low group:  eigvecs of smallest eigenvalues (slowest diffusion)
    Mid group:  middle eigenvalues
    High group: largest eigenvalues (fastest oscillation)
  Walk each group separately; combine by group; compare vs uniform.

Hypothesis (F150 §6.1):
  H1: harmonic-3 partitioning preserves or sharpens multi-step retrieval
  H2: the low-eigval group dominates short-step retrieval (1-2 hops)
  H3: the mid-eigval group dominates mid-step (3-5 hops)
  H4: the high-eigval group dominates long-step or shows incoherence

Per [[feedback_no_lineage_claims_in_notebook]]: this validates F150's H3
candidate reading empirically; result-positive confirms; result-negative
refines but doesn't invalidate F150 framework.
"""
import json
import time
from pathlib import Path
import sys
import importlib.util

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

_spec = importlib.util.spec_from_file_location(
    "two_tier_storage", Path(__file__).parent / "R-RBS-NN-10_two_tier_storage.py"
)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["two_tier_storage"] = _mod
_spec.loader.exec_module(_mod)
TwoTierRBSNNStorage = _mod.TwoTierRBSNNStorage

from srmech.amsc import laplacian
from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION


def build_chain_graph(N: int):
    tokens = [f"chain_{i:03d}" for i in range(N)]
    pairs = [(tokens[i], tokens[i + 1]) for i in range(N - 1)]
    return tokens, pairs


def adjacency_from_synapses(storage, tokens):
    token_to_idx = {tok: i for i, tok in enumerate(tokens)}
    edges = []
    weights = []
    for key, synapse in storage.tier2.items():
        a, b = key
        if a in token_to_idx and b in token_to_idx:
            ia, ib = token_to_idx[a], token_to_idx[b]
            if ia < ib:
                edges.append((ia, ib))
                weights.append(float(synapse.current_density))
    return edges, weights


def spectral_partition_h3(L, n_per_group=8):
    """Compute Class L Laplacian eigendecompose and partition into 3 groups
    per F150 harmonic-3 reading.

    Returns:
      dict with 'low', 'mid', 'high' keys, each holding (eigvals, eigvecs)
      for that group; eigvecs shape (n_nodes, n_per_group).
    """
    eigvals, eigvecs = laplacian.hermitian_eigendecompose(L)
    eigvecs = eigvecs.real
    n_eigs = len(eigvals)

    # Skip eigval_0 (trivial constant); partition remaining into 3 groups
    available = n_eigs - 1
    if available < 3 * n_per_group:
        # Adjust group size if not enough eigenvalues
        n_per_group = max(1, available // 3)

    # Indexes 1..3*n_per_group, partition by THIRD
    low_idx = slice(1, 1 + n_per_group)
    mid_idx = slice(1 + n_per_group, 1 + 2 * n_per_group)
    high_idx = slice(1 + 2 * n_per_group, 1 + 3 * n_per_group)

    return {
        "low": (eigvals[low_idx], eigvecs[:, low_idx]),
        "mid": (eigvals[mid_idx], eigvecs[:, mid_idx]),
        "high": (eigvals[high_idx], eigvecs[:, high_idx]),
    }


def spectral_uniform(L, top_k=24):
    """Uniform top-K eigvec embedding (baseline R13a approach)."""
    eigvals, eigvecs = laplacian.hermitian_eigendecompose(L)
    eigvecs = eigvecs.real
    return eigvals[1 : top_k + 1], eigvecs[:, 1 : top_k + 1]


def cosine_similarity(a, b):
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def walk_uniform(eigvecs, tokens, query_idx, top_k=20):
    """Uniform top-K spectral walk."""
    query_emb = eigvecs[query_idx]
    scores = []
    for i, tok in enumerate(tokens):
        if i == query_idx:
            continue
        scores.append((tok, i, cosine_similarity(query_emb, eigvecs[i])))
    scores.sort(key=lambda x: x[2], reverse=True)
    return scores[:top_k]


def walk_h3(groups, tokens, query_idx, top_k_per_group=8):
    """Harmonic-3 partitioned spectral walk — walk each eigvec group separately."""
    out = {}
    for group_name, (eigvals, eigvecs) in groups.items():
        query_emb = eigvecs[query_idx]
        scores = []
        for i, tok in enumerate(tokens):
            if i == query_idx:
                continue
            scores.append((tok, i, cosine_similarity(query_emb, eigvecs[i])))
        scores.sort(key=lambda x: x[2], reverse=True)
        out[group_name] = scores[:top_k_per_group]
    return out


def analyze_chain_retrieval(retrieved, query_idx):
    """Analyze chain-step structure of retrievals."""
    by_step = {}
    for tok, idx, sim in retrieved:
        if tok.startswith("chain_"):
            steps = abs(idx - query_idx)
            if steps not in by_step:
                by_step[steps] = []
            by_step[steps].append((tok, sim))
    return by_step


def main():
    D = 8192
    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}; D={D}")
    print()

    results_by_N = {}
    for N in [50, 100, 200]:
        print("=" * 80)
        print(f"Chain N={N}")
        print("=" * 80)

        tokens, pairs = build_chain_graph(N)
        storage = TwoTierRBSNNStorage(D=D, seed=42)
        for tok in tokens:
            storage.encode_concept(tok)
        storage.batch_learn(pairs, plasticity_density=0.67)

        edges, weights = adjacency_from_synapses(storage, tokens)
        if not edges:
            continue
        L = laplacian.dense_laplacian(N, edges, weights)

        # Uniform baseline
        _, uniform_eigvecs = spectral_uniform(L, top_k=24)
        # H3 partition
        h3_groups = spectral_partition_h3(L, n_per_group=8)

        # Test queries at different positions in chain
        query_indices = [0, N // 4, N // 2, 3 * N // 4]
        n_results = []

        for query_idx in query_indices:
            query_token = tokens[query_idx]
            print(f"\n  Query: {query_token} (idx={query_idx})")

            # Uniform walk
            uniform_retrieved = walk_uniform(uniform_eigvecs, tokens, query_idx, top_k=15)
            uniform_by_step = analyze_chain_retrieval(uniform_retrieved, query_idx)
            print(f"    Uniform top-15 by chain step:")
            for step in sorted(uniform_by_step.keys())[:8]:
                items = uniform_by_step[step]
                top_sim = items[0][1] if items else 0.0
                print(f"      step {step:>3}: {len(items)} retrievals, top sim = {top_sim:+0.3f}")

            # H3 partitioned walk
            h3_retrieved = walk_h3(h3_groups, tokens, query_idx, top_k_per_group=6)
            print(f"    H3 partitioned (low/mid/high):")
            for group_name in ["low", "mid", "high"]:
                group_results = h3_retrieved[group_name]
                by_step = analyze_chain_retrieval(group_results, query_idx)
                steps_str = ", ".join(
                    f"s{s}({len(by_step[s])}, top={by_step[s][0][1]:+0.2f})"
                    for s in sorted(by_step.keys())[:5]
                )
                print(f"      {group_name:<5}: {steps_str}")

            n_results.append({
                "query_idx": int(query_idx),
                "query_token": query_token,
                "uniform_by_step": {str(s): {"count": len(items), "top_sim": items[0][1] if items else 0.0}
                                     for s, items in uniform_by_step.items()},
                "h3_by_group_step": {
                    group: {str(s): {"count": len(items), "top_sim": items[0][1] if items else 0.0}
                            for s, items in analyze_chain_retrieval(h3_retrieved[group], query_idx).items()}
                    for group in ["low", "mid", "high"]
                },
            })
        results_by_N[N] = n_results

    # Aggregate analysis
    print()
    print("=" * 80)
    print("Hypothesis check across all N + query positions")
    print("=" * 80)

    # H2: low-eigval dominates short-step (1-2 hops)
    # H3: mid-eigval dominates mid-step (3-5 hops)
    # H4: high-eigval shows incoherence at long-step
    aggregate_h3_groups = {"low": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [], 8: []},
                            "mid": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [], 8: []},
                            "high": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [], 8: []}}
    aggregate_uniform = {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [], 8: []}

    for N, nres in results_by_N.items():
        for q in nres:
            for step_str, info in q["uniform_by_step"].items():
                step = int(step_str)
                if step in aggregate_uniform:
                    aggregate_uniform[step].append(info["top_sim"])
            for group in ["low", "mid", "high"]:
                for step_str, info in q["h3_by_group_step"].get(group, {}).items():
                    step = int(step_str)
                    if step in aggregate_h3_groups[group]:
                        aggregate_h3_groups[group][step].append(info["top_sim"])

    print(f"\n  Average top-similarity per chain-step (across all N + queries):")
    print(f"  {'step':>4} | {'uniform':>10} | {'h3 low':>10} | {'h3 mid':>10} | {'h3 high':>10}")
    for step in range(1, 8):
        u = float(np.mean(aggregate_uniform[step])) if aggregate_uniform[step] else 0.0
        l = float(np.mean(aggregate_h3_groups["low"][step])) if aggregate_h3_groups["low"][step] else 0.0
        m = float(np.mean(aggregate_h3_groups["mid"][step])) if aggregate_h3_groups["mid"][step] else 0.0
        h = float(np.mean(aggregate_h3_groups["high"][step])) if aggregate_h3_groups["high"][step] else 0.0
        print(f"  {step:>4} | {u:>+8.3f}  | {l:>+8.3f}  | {m:>+8.3f}  | {h:>+8.3f}")

    print(f"\n  Hypothesis verdicts:")
    # H1: H3 preserves or sharpens retrieval
    # Compute mean top-sim across all retrievals for each method
    uniform_overall = float(np.mean([s for step_list in aggregate_uniform.values() for s in step_list]))
    h3_low_overall = float(np.mean([s for step_list in aggregate_h3_groups["low"].values() for s in step_list]))
    h3_mid_overall = float(np.mean([s for step_list in aggregate_h3_groups["mid"].values() for s in step_list]))
    h3_high_overall = float(np.mean([s for step_list in aggregate_h3_groups["high"].values() for s in step_list]))
    print(f"    Uniform overall mean top-sim: {uniform_overall:+0.3f}")
    print(f"    H3 low overall:               {h3_low_overall:+0.3f}")
    print(f"    H3 mid overall:               {h3_mid_overall:+0.3f}")
    print(f"    H3 high overall:              {h3_high_overall:+0.3f}")

    # H2: low dominates short-step (1-2 hops)
    short_step_low = float(np.mean(aggregate_h3_groups["low"][1] + aggregate_h3_groups["low"][2])) if aggregate_h3_groups["low"][1] or aggregate_h3_groups["low"][2] else 0.0
    short_step_mid = float(np.mean(aggregate_h3_groups["mid"][1] + aggregate_h3_groups["mid"][2])) if aggregate_h3_groups["mid"][1] or aggregate_h3_groups["mid"][2] else 0.0
    short_step_high = float(np.mean(aggregate_h3_groups["high"][1] + aggregate_h3_groups["high"][2])) if aggregate_h3_groups["high"][1] or aggregate_h3_groups["high"][2] else 0.0
    print(f"\n  H2: low-eigval dominates short-step (1-2 hops):")
    print(f"    low: {short_step_low:+0.3f}, mid: {short_step_mid:+0.3f}, high: {short_step_high:+0.3f}")
    print(f"    Verdict: {'PASS' if short_step_low > short_step_mid and short_step_low > short_step_high else 'NEEDS REFINEMENT'}")

    # H3: mid-eigval dominates mid-step (3-5 hops)
    mid_step_low = float(np.mean(aggregate_h3_groups["low"][3] + aggregate_h3_groups["low"][4] + aggregate_h3_groups["low"][5])) if any(aggregate_h3_groups["low"][s] for s in [3, 4, 5]) else 0.0
    mid_step_mid = float(np.mean(aggregate_h3_groups["mid"][3] + aggregate_h3_groups["mid"][4] + aggregate_h3_groups["mid"][5])) if any(aggregate_h3_groups["mid"][s] for s in [3, 4, 5]) else 0.0
    mid_step_high = float(np.mean(aggregate_h3_groups["high"][3] + aggregate_h3_groups["high"][4] + aggregate_h3_groups["high"][5])) if any(aggregate_h3_groups["high"][s] for s in [3, 4, 5]) else 0.0
    print(f"\n  H3: mid-eigval dominates mid-step (3-5 hops):")
    print(f"    low: {mid_step_low:+0.3f}, mid: {mid_step_mid:+0.3f}, high: {mid_step_high:+0.3f}")
    print(f"    Verdict: {'PASS' if mid_step_mid > mid_step_low and mid_step_mid > mid_step_high else 'NEEDS REFINEMENT'}")

    # Output JSON
    out = {
        "srmech_version": SRMECH_VERSION,
        "D": D,
        "results_by_N": {str(k): v for k, v in results_by_N.items()},
        "aggregate": {
            "uniform_per_step_mean_top_sim": {str(s): float(np.mean(v)) if v else 0.0 for s, v in aggregate_uniform.items()},
            "h3_low_per_step": {str(s): float(np.mean(v)) if v else 0.0 for s, v in aggregate_h3_groups["low"].items()},
            "h3_mid_per_step": {str(s): float(np.mean(v)) if v else 0.0 for s, v in aggregate_h3_groups["mid"].items()},
            "h3_high_per_step": {str(s): float(np.mean(v)) if v else 0.0 for s, v in aggregate_h3_groups["high"].items()},
        },
        "hypothesis_metrics": {
            "uniform_overall": uniform_overall,
            "h3_low_overall": h3_low_overall,
            "h3_mid_overall": h3_mid_overall,
            "h3_high_overall": h3_high_overall,
            "h2_short_step": {"low": short_step_low, "mid": short_step_mid, "high": short_step_high},
            "h3_mid_step": {"low": mid_step_low, "mid": mid_step_mid, "high": mid_step_high},
        },
    }
    out_path = Path(__file__).parent / "R-RBS-NN-15_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
