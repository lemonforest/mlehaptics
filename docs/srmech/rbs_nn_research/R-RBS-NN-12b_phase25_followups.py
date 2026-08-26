"""R-RBS-NN-12b — Phase 2.5 follow-ups

Three sub-tests:
  S1: Latency optimization — bucket-local + neighbor scoring (fast=True)
      vs flat scoring (fast=False). Same correctness, target O(K) vs O(N).
  S2: Bucket strategy comparison — hash vs sector_then_hash.
      Tests whether chirality-sector-based bucketing affects retrieval
      when associations are mixed-sector vs same-sector.
  S3: Sculpted decay validation in hierarchical mode — does
      forget_step_coupling work per-bucket as designed?
"""
import json
import time
from pathlib import Path
import sys
import importlib.util

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

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


def measure_retrieval_subset(storage, pairs, top_k=3, max_pairs=200, fast=True):
    if len(pairs) > max_pairs:
        sampled_idx = np.random.default_rng(0).choice(len(pairs), size=max_pairs, replace=False)
        sampled = [pairs[i] for i in sampled_idx]
    else:
        sampled = pairs

    correct_top_k = 0
    sims_correct = []
    for a, b in sampled:
        retrieved = storage.retrieve_associated(a, top_k=top_k, threshold=0.0, fast=fast)
        if not retrieved:
            continue
        tokens = [t for t, _ in retrieved]
        if b in tokens:
            idx = tokens.index(b)
            correct_top_k += 1
            sims_correct.append(retrieved[idx][1])
    return {
        "p_at_top_k": correct_top_k / len(sampled) if sampled else 0.0,
        "mean_sim_correct": float(np.mean(sims_correct)) if sims_correct else 0.0,
        "n_evaluated": len(sampled),
    }


def build_storage(D, N, n_buckets, bucket_strategy="hash", chirality_mix=False, seed=42):
    """Build hierarchical storage with optional cross-sector chirality."""
    tokens = synthetic_lexicon(N)
    pairs = random_association_graph(tokens, degree=2, seed=N * 7)
    storage = HierarchicalTwoTierRBSNNStorage(
        D=D, n_buckets=n_buckets, seed=seed, bucket_strategy=bucket_strategy
    )
    if chirality_mix:
        # Assign chirality sectors round-robin (forces cross-sector associations)
        for i, tok in enumerate(tokens):
            storage.encode_concept(tok, chirality_sector=i % 4)
    else:
        for tok in tokens:
            storage.encode_concept(tok, chirality_sector=0)
    storage.batch_learn(pairs, plasticity_density=0.67)
    return storage, pairs


def main():
    D = 8192
    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}; D={D}")
    print()

    # ============================================================
    # S1: Latency optimization
    # ============================================================
    print("=" * 80)
    print("S1 — Latency: bucket-local fast=True vs flat fast=False")
    print("=" * 80)
    s1_results = []
    for N in [500, 1000, 2000]:
        n_buckets = recommend_n_buckets(N)
        storage, pairs = build_storage(D, N, n_buckets)

        # Fast retrieval (O(K))
        t = time.time()
        fast_metrics = measure_retrieval_subset(storage, pairs, max_pairs=200, fast=True)
        t_fast = time.time() - t

        # Flat retrieval (O(N))
        t = time.time()
        flat_metrics = measure_retrieval_subset(storage, pairs, max_pairs=200, fast=False)
        t_flat = time.time() - t

        speedup = t_flat / t_fast if t_fast > 0 else float("inf")
        agreement = abs(fast_metrics["p_at_top_k"] - flat_metrics["p_at_top_k"])

        print(
            f"  N={N:>4}: fast={t_fast:.2f}s p@3={fast_metrics['p_at_top_k']:.3f} | "
            f"flat={t_flat:.2f}s p@3={flat_metrics['p_at_top_k']:.3f} | "
            f"speedup={speedup:.1f}x | quality_diff={agreement:.3f}"
        )
        s1_results.append({
            "N": N,
            "n_buckets": n_buckets,
            "fast_time_sec": t_fast,
            "flat_time_sec": t_flat,
            "speedup": speedup,
            "fast_p3": fast_metrics["p_at_top_k"],
            "flat_p3": flat_metrics["p_at_top_k"],
            "quality_diff": agreement,
        })

    # ============================================================
    # S2: Bucket strategy — hash vs sector_then_hash
    # ============================================================
    print()
    print("=" * 80)
    print("S2 — Bucket strategy: hash vs sector_then_hash (chirality-mixed concepts)")
    print("=" * 80)
    s2_results = []
    for N in [500, 1000]:
        n_buckets = recommend_n_buckets(N)
        # Force chirality-mixed concepts (sectors round-robin)
        hash_storage, hash_pairs = build_storage(
            D, N, n_buckets, bucket_strategy="hash", chirality_mix=True
        )
        sector_storage, sector_pairs = build_storage(
            D, N, n_buckets, bucket_strategy="sector_then_hash", chirality_mix=True
        )

        t = time.time()
        hash_metrics = measure_retrieval_subset(hash_storage, hash_pairs, max_pairs=200, fast=True)
        t_hash = time.time() - t

        t = time.time()
        sector_metrics = measure_retrieval_subset(sector_storage, sector_pairs, max_pairs=200, fast=True)
        t_sector = time.time() - t

        hash_dist = hash_storage.bucket_distribution()
        sector_dist = sector_storage.bucket_distribution()

        print(f"  N={N:>4}:")
        print(
            f"    hash:              p@3={hash_metrics['p_at_top_k']:.3f}  "
            f"max_bucket={hash_dist['max_bucket']}  time={t_hash:.2f}s"
        )
        print(
            f"    sector_then_hash:  p@3={sector_metrics['p_at_top_k']:.3f}  "
            f"max_bucket={sector_dist['max_bucket']}  time={t_sector:.2f}s"
        )
        s2_results.append({
            "N": N,
            "n_buckets": n_buckets,
            "hash_p3": hash_metrics["p_at_top_k"],
            "sector_p3": sector_metrics["p_at_top_k"],
            "hash_max_bucket": hash_dist["max_bucket"],
            "sector_max_bucket": sector_dist["max_bucket"],
            "hash_time_sec": t_hash,
            "sector_time_sec": t_sector,
        })

    # ============================================================
    # S3: Sculpted decay in hierarchical mode
    # ============================================================
    print()
    print("=" * 80)
    print("S3 — Sculpted decay in hierarchical (per-bucket coupling-informed)")
    print("=" * 80)
    s3_results = []
    N = 500
    n_buckets = recommend_n_buckets(N)
    for strategy in ["random", "noise_floor", "redundant", "middle"]:
        storage, pairs = build_storage(D, N, n_buckets)
        # Baseline measurement
        base = measure_retrieval_subset(storage, pairs, max_pairs=200, fast=True)
        # Apply 30% decay via specified strategy
        if strategy == "random":
            storage.forget_step(decay_rate=0.30)
        else:
            storage.forget_step_coupling(decay_rate=0.30, strategy=strategy)
        after = measure_retrieval_subset(storage, pairs, max_pairs=200, fast=True)
        att = storage.density_attestation()

        delta = after["p_at_top_k"] - base["p_at_top_k"]
        print(
            f"  {strategy:<15}: base p@3={base['p_at_top_k']:.3f} → after p@3={after['p_at_top_k']:.3f} | "
            f"Δ={delta:+0.3f} | syn_density={att.get('mean_synapse_density', 0):.3f}"
        )
        s3_results.append({
            "strategy": strategy,
            "base_p3": base["p_at_top_k"],
            "after_p3": after["p_at_top_k"],
            "delta": delta,
            "mean_synapse_density_after": att.get("mean_synapse_density"),
            "mean_composite_density_after": att.get("mean_composite_density"),
        })

    # Hypothesis check
    print()
    print("=" * 80)
    print("Phase 2.5 hypothesis check")
    print("=" * 80)
    s1_avg_speedup = float(np.mean([r["speedup"] for r in s1_results]))
    s1_max_quality_diff = max(r["quality_diff"] for r in s1_results)
    s3_strategies = {r["strategy"]: r for r in s3_results}
    s3_noise_floor = s3_strategies["noise_floor"]["delta"]
    s3_redundant = s3_strategies["redundant"]["delta"]
    s3_random = s3_strategies["random"]["delta"]

    print(f"  S1 fast scoring speedup > 5×:          {s1_avg_speedup > 5} (avg {s1_avg_speedup:.1f}×)")
    print(f"  S1 fast/flat quality diff < 0.05:      {s1_max_quality_diff < 0.05} (max {s1_max_quality_diff:.3f})")
    print(f"  S3 hierarchical sculpted decay holds F149 ordering:")
    print(f"    noise_floor Δ ({s3_noise_floor:+0.3f}) > random Δ ({s3_random:+0.3f}): {s3_noise_floor > s3_random}")
    print(f"    noise_floor Δ ({s3_noise_floor:+0.3f}) > redundant Δ ({s3_redundant:+0.3f}): {s3_noise_floor > s3_redundant}")

    out = {
        "srmech_version": SRMECH_VERSION,
        "has_native": HAS_NATIVE,
        "D": D,
        "S1_latency_optimization": s1_results,
        "S2_bucket_strategy": s2_results,
        "S3_sculpted_decay_hierarchical": s3_results,
    }
    out_path = Path(__file__).parent / "R-RBS-NN-12b_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
