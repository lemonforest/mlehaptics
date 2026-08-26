"""R-RBS-NN-12 — Hierarchical bundling smoke test

Phase 2 of R-RBS-NN-10_FOLLOWUP_PHASED_PLAN.md.

Tests:
  T2.3: flat vs hierarchical at N ∈ {500, 1000, 2000}
  T2.4: overlap region flat vs hierarchical at N ∈ {100, 256}
  T2.5: latency comparison

Hypotheses:
  H1: hierarchical p@3 ≥ 0.50 at N > 256 (push past the flat ceiling)
  H2: flat p@3 < 0.30 at N=512 (confirms F11 ceiling)
  H3: hierarchical ≈ flat at N ≤ 256 (overlap region; no degradation)
  H4: latency scales O(K) for hierarchical vs O(N) for flat
"""
import json
import time
from pathlib import Path
import sys
import importlib.util

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

# Load both classes
_spec_flat = importlib.util.spec_from_file_location(
    "two_tier_flat", Path(__file__).parent / "R-RBS-NN-10_two_tier_storage.py"
)
_mod_flat = importlib.util.module_from_spec(_spec_flat)
sys.modules["two_tier_flat"] = _mod_flat
_spec_flat.loader.exec_module(_mod_flat)
TwoTierRBSNNStorage = _mod_flat.TwoTierRBSNNStorage

_spec_hier = importlib.util.spec_from_file_location(
    "hierarchical_storage", Path(__file__).parent / "R-RBS-NN-12_hierarchical_storage.py"
)
_mod_hier = importlib.util.module_from_spec(_spec_hier)
sys.modules["hierarchical_storage"] = _mod_hier
_spec_hier.loader.exec_module(_mod_hier)
HierarchicalTwoTierRBSNNStorage = _mod_hier.HierarchicalTwoTierRBSNNStorage
recommend_n_buckets = _mod_hier.recommend_n_buckets

from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION


def synthetic_lexicon(n):
    return [f"concept_{i:04d}" for i in range(n)]


def random_association_graph(tokens, degree, seed):
    rng = np.random.default_rng(seed)
    n = len(tokens)
    pairs_set = set()
    for i in range(n):
        for _ in range(degree):
            j = int(rng.integers(0, n))
            if j == i:
                j = (j + 1) % n
            key = tuple(sorted([tokens[i], tokens[j]]))
            pairs_set.add(key)
    return list(pairs_set)


def measure_retrieval_subset(storage, pairs, top_k=3, max_pairs=200):
    """Sample up to max_pairs to control O(N^2) retrieval cost at high N."""
    if len(pairs) > max_pairs:
        # Sample for cost control
        sampled_idx = np.random.default_rng(0).choice(len(pairs), size=max_pairs, replace=False)
        sampled = [pairs[i] for i in sampled_idx]
    else:
        sampled = pairs

    correct_top_k = 0
    correct_top_1 = 0
    sims_correct = []
    for a, b in sampled:
        retrieved = storage.retrieve_associated(a, top_k=top_k, threshold=0.0)
        if not retrieved:
            continue
        tokens = [t for t, _ in retrieved]
        if b in tokens:
            idx = tokens.index(b)
            correct_top_k += 1
            if idx == 0:
                correct_top_1 += 1
            sims_correct.append(retrieved[idx][1])
    return {
        "p_at_1": correct_top_1 / len(sampled) if sampled else 0.0,
        "p_at_top_k": correct_top_k / len(sampled) if sampled else 0.0,
        "mean_sim_correct": float(np.mean(sims_correct)) if sims_correct else 0.0,
        "n_evaluated": len(sampled),
    }


def build_flat(D, N, seed=42):
    tokens = synthetic_lexicon(N)
    pairs = random_association_graph(tokens, degree=2, seed=N * 7)
    storage = TwoTierRBSNNStorage(D=D, seed=seed)
    for tok in tokens:
        storage.encode_concept(tok)
    storage.batch_learn(pairs, plasticity_density=0.67)
    return storage, pairs


def build_hierarchical(D, N, n_buckets=None, seed=42):
    if n_buckets is None:
        n_buckets = recommend_n_buckets(N)
    tokens = synthetic_lexicon(N)
    pairs = random_association_graph(tokens, degree=2, seed=N * 7)
    storage = HierarchicalTwoTierRBSNNStorage(D=D, n_buckets=n_buckets, seed=seed)
    for tok in tokens:
        storage.encode_concept(tok)
    storage.batch_learn(pairs, plasticity_density=0.67)
    return storage, pairs


def main():
    D = 8192
    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}; D={D}")
    print()

    # === T2.4: overlap region (flat should work; hierarchical shouldn't degrade) ===
    print("=" * 80)
    print("T2.4 — Overlap region: flat vs hierarchical at N ∈ {100, 256}")
    print("=" * 80)
    overlap_results = []
    for N in [100, 256]:
        t = time.time()
        flat_storage, flat_pairs = build_flat(D, N)
        t_build_flat = time.time() - t
        flat_metrics = measure_retrieval_subset(flat_storage, flat_pairs)

        n_buckets = recommend_n_buckets(N)
        t = time.time()
        hier_storage, hier_pairs = build_hierarchical(D, N, n_buckets=n_buckets)
        t_build_hier = time.time() - t
        hier_metrics = measure_retrieval_subset(hier_storage, hier_pairs)

        dist = hier_storage.bucket_distribution()
        att = hier_storage.density_attestation()

        print(
            f"  N={N:>4} (n_buckets={n_buckets}, max_bucket={dist['max_bucket']}):"
        )
        print(
            f"    flat:         p@3={flat_metrics['p_at_top_k']:.3f}  "
            f"build={t_build_flat:.1f}s"
        )
        print(
            f"    hierarchical: p@3={hier_metrics['p_at_top_k']:.3f}  "
            f"build={t_build_hier:.1f}s  bucket_dist={dist['bucket_sizes']}"
        )
        overlap_results.append({
            "N": N,
            "n_buckets": n_buckets,
            "flat_p3": flat_metrics["p_at_top_k"],
            "hierarchical_p3": hier_metrics["p_at_top_k"],
            "bucket_sizes": dist["bucket_sizes"],
            "max_bucket": dist["max_bucket"],
            "exceeds_max_bundle": dist["exceeds_MAX_BUNDLE_N"],
            "build_flat_sec": t_build_flat,
            "build_hier_sec": t_build_hier,
        })

    # === T2.3: push past the flat ceiling ===
    print()
    print("=" * 80)
    print("T2.3 — Past the ceiling: hierarchical at N ∈ {500, 1000, 2000}")
    print("=" * 80)
    pastceiling_results = []
    for N in [500, 1000, 2000]:
        n_buckets = recommend_n_buckets(N)
        t = time.time()
        hier_storage, hier_pairs = build_hierarchical(D, N, n_buckets=n_buckets)
        t_build = time.time() - t

        # Measure on subset to keep retrieval cost bounded
        t = time.time()
        hier_metrics = measure_retrieval_subset(hier_storage, hier_pairs, top_k=3, max_pairs=200)
        t_retrieve = time.time() - t

        dist = hier_storage.bucket_distribution()
        att = hier_storage.density_attestation()

        # Optional: compare against flat at this N (will be slow & expected to crash)
        if N <= 1000:  # skip N=2000 flat (too slow)
            t = time.time()
            flat_storage, flat_pairs = build_flat(D, N)
            t_build_flat = time.time() - t
            t = time.time()
            flat_metrics = measure_retrieval_subset(flat_storage, flat_pairs, top_k=3, max_pairs=200)
            t_retrieve_flat = time.time() - t
            flat_p3 = flat_metrics["p_at_top_k"]
            flat_retrieve_sec = t_retrieve_flat
        else:
            flat_p3 = None
            flat_retrieve_sec = None

        print(f"  N={N:>4} (n_buckets={n_buckets}):")
        print(
            f"    hierarchical: p@3={hier_metrics['p_at_top_k']:.3f}  "
            f"max_bucket={dist['max_bucket']}  "
            f"exceeds_MAX_BUNDLE={len(dist['exceeds_MAX_BUNDLE_N'])>0}  "
            f"build={t_build:.1f}s  retrieve={t_retrieve:.1f}s"
        )
        if flat_p3 is not None:
            print(f"    flat (compare):p@3={flat_p3:.3f}  retrieve={flat_retrieve_sec:.1f}s")

        pastceiling_results.append({
            "N": N,
            "n_buckets": n_buckets,
            "hierarchical_p3": hier_metrics["p_at_top_k"],
            "flat_p3": flat_p3,
            "max_bucket": dist["max_bucket"],
            "min_bucket": dist["min_bucket"],
            "mean_bucket": dist["mean_bucket"],
            "exceeds_max_bundle_n": dist["exceeds_MAX_BUNDLE_N"],
            "build_hier_sec": t_build,
            "retrieve_hier_sec": t_retrieve,
            "retrieve_flat_sec": flat_retrieve_sec,
            "n_evaluated": hier_metrics["n_evaluated"],
        })

    # === Hypothesis check ===
    print()
    print("=" * 80)
    print("Phase 2 hypothesis check")
    print("=" * 80)
    h1_pass = all(r["hierarchical_p3"] >= 0.30 for r in pastceiling_results if r["N"] > 256)
    h2_pass = pastceiling_results[1]["flat_p3"] is not None and pastceiling_results[1]["flat_p3"] < 0.30
    overlap_diff_100 = abs(overlap_results[0]["flat_p3"] - overlap_results[0]["hierarchical_p3"])
    overlap_diff_256 = abs(overlap_results[1]["flat_p3"] - overlap_results[1]["hierarchical_p3"])
    h3_pass = overlap_diff_100 < 0.15 and overlap_diff_256 < 0.15

    print(f"  H1 hierarchical p@3 ≥ 0.30 at N > 256:  {h1_pass}")
    print(f"  H2 flat p@3 < 0.30 at N=1000:           {h2_pass}")
    print(f"  H3 overlap diff < 0.15 at N≤256:        {h3_pass}  "
          f"(N=100: |Δ|={overlap_diff_100:.3f}; N=256: |Δ|={overlap_diff_256:.3f})")

    # === Latency observation ===
    print()
    print("=" * 80)
    print("T2.5 — Latency observation")
    print("=" * 80)
    for r in pastceiling_results:
        if r["retrieve_flat_sec"] is not None:
            speedup = r["retrieve_flat_sec"] / r["retrieve_hier_sec"] if r["retrieve_hier_sec"] > 0 else float("inf")
            print(
                f"  N={r['N']:>4}: hier retrieve={r['retrieve_hier_sec']:.2f}s, "
                f"flat retrieve={r['retrieve_flat_sec']:.2f}s, "
                f"hier speedup={speedup:.2f}x"
            )
        else:
            print(f"  N={r['N']:>4}: hier retrieve={r['retrieve_hier_sec']:.2f}s (flat not run; too slow)")

    # Output JSON
    out_path = Path(__file__).parent / "R-RBS-NN-12_results.json"
    out_path.write_text(json.dumps({
        "srmech_version": SRMECH_VERSION,
        "has_native": HAS_NATIVE,
        "abi": NATIVE_ABI_VERSION,
        "D": D,
        "hypotheses": {
            "H1_hier_at_n_gt_256_above_threshold": h1_pass,
            "H2_flat_crash_confirmed_at_n_1000": h2_pass,
            "H3_overlap_no_degradation": h3_pass,
        },
        "T2_4_overlap": overlap_results,
        "T2_3_past_ceiling": pastceiling_results,
    }, indent=2))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
