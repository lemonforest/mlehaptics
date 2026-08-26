"""R-RBS-NN-11b — Sculpted decay via coupling metric vs random decay

Per user framework direction 2026-05-28:
  "can't we sculpt decay to work how we want by simply comparing coupling
  relationships and finding some metric that shows what's best to drop?
  And it's also possible that this is already how it's done through some
  longer cascade, that neither is decay random."

Tests four decay strategies at MATCHED total decay fraction:
  R) Random — current baseline forget_step (random position selection)
  N) Coupling noise_floor — drop lowest-coupling positions (drop noise)
  H) Coupling redundant — drop highest-coupling positions (drop consensus)
  M) Coupling middle — drop middle-coupling band

Hypothesis (substrate framework reading):
  N (drop noise) should preserve retrieval BEST — drops what carries
    least information across synapses
  H (drop consensus) should DEGRADE retrieval — drops the load-bearing
    common signal
  R (random) should sit between N and H — by construction it averages
    over the coupling distribution
  M (drop middle) less clear — preserves both extremes; tests middle-
    position information hypothesis

Tests at N=100 concepts, D=8192, matched total decay 30%.
"""
import json
import time
from pathlib import Path
import sys
import importlib.util

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
spec = importlib.util.spec_from_file_location(
    "two_tier_storage", Path(__file__).parent / "R-RBS-NN-10_two_tier_storage.py"
)
mod = importlib.util.module_from_spec(spec)
sys.modules["two_tier_storage"] = mod
spec.loader.exec_module(mod)
TwoTierRBSNNStorage = mod.TwoTierRBSNNStorage

from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION


def synthetic_lexicon(n: int):
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


def measure_retrieval(storage, pairs, top_k=3):
    correct_top_k = 0
    correct_top_1 = 0
    sims_correct = []
    for a, b in pairs:
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
        "p_at_1": correct_top_1 / len(pairs) if pairs else 0.0,
        "p_at_top_k": correct_top_k / len(pairs) if pairs else 0.0,
        "mean_sim_correct": float(np.mean(sims_correct)) if sims_correct else 0.0,
    }


def build_baseline(D, N, density, seed=42):
    """Build a fresh storage with N concepts + degree-2 random associations."""
    tokens = synthetic_lexicon(N)
    pairs = random_association_graph(tokens, degree=2, seed=N * 7)
    storage = TwoTierRBSNNStorage(D=D, seed=seed)
    for tok in tokens:
        storage.encode_concept(tok)
    storage.batch_learn(pairs, plasticity_density=density)
    return storage, pairs


def main():
    D = 8192
    N = 100
    DENSITY = 0.67
    TOTAL_DECAY = 0.30  # 30% of D positions decayed

    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}")
    print(f"D={D}, N={N} concepts, density={DENSITY}, total decay={TOTAL_DECAY}")
    print()

    # Baseline retrieval (no decay applied)
    storage, pairs = build_baseline(D, N, DENSITY)
    base_metrics = measure_retrieval(storage, pairs)
    print(f"BASELINE (no decay): p@1={base_metrics['p_at_1']:.3f}  p@3={base_metrics['p_at_top_k']:.3f}  sim={base_metrics['mean_sim_correct']:+0.3f}")
    print()

    # Compare 4 strategies at matched total decay
    strategies = [
        ("random", "R"),
        ("noise_floor", "N (drop low coupling)"),
        ("redundant", "H (drop high coupling)"),
        ("middle", "M (drop middle)"),
    ]

    print(f"{'strategy':>30} | {'p@1':>6} | {'p@3':>6} | {'sim':>7} | {'mean_syn_den':>14} | {'composite_den':>14}")
    print("-" * 100)

    results = []
    for strategy_name, label in strategies:
        # Fresh storage each time
        storage, pairs = build_baseline(D, N, DENSITY)

        # Apply equivalent total decay
        if strategy_name == "random":
            # Random decay applied per-synapse; total positions decayed ≈ decay_rate * n_nonzero * n_synapses
            # To match total_decay fraction of D, we approximate via single forget_step
            # at decay_rate = total_decay
            storage.forget_step(decay_rate=TOTAL_DECAY)
        else:
            storage.forget_step_coupling(decay_rate=TOTAL_DECAY, strategy=strategy_name)

        metrics = measure_retrieval(storage, pairs)
        att = storage.density_attestation()
        results.append({
            "strategy": strategy_name,
            "label": label,
            "p_at_1": metrics["p_at_1"],
            "p_at_top_k": metrics["p_at_top_k"],
            "mean_sim_correct": metrics["mean_sim_correct"],
            "mean_synapse_density": att.get("mean_synapse_density"),
            "composite_density": att.get("composite_density"),
        })
        print(
            f"  {label:<30} | {metrics['p_at_1']:.3f}  | {metrics['p_at_top_k']:.3f}  | "
            f"{metrics['mean_sim_correct']:+0.3f} | "
            f"{att.get('mean_synapse_density', 0):.3f}          | "
            f"{att.get('composite_density', 0):.3f}"
        )

    print()
    print("=" * 80)
    print("Hypothesis check:")
    print("=" * 80)
    by_strategy = {r["strategy"]: r for r in results}
    n_floor = by_strategy["noise_floor"]["p_at_top_k"]
    redundant = by_strategy["redundant"]["p_at_top_k"]
    random_r = by_strategy["random"]["p_at_top_k"]
    middle = by_strategy["middle"]["p_at_top_k"]

    print(f"  H1: noise_floor (drop low) > random      → {n_floor > random_r}  ({n_floor:.3f} vs {random_r:.3f})")
    print(f"  H2: random > redundant (drop high)       → {random_r > redundant}  ({random_r:.3f} vs {redundant:.3f})")
    print(f"  H3: noise_floor > redundant              → {n_floor > redundant}  ({n_floor:.3f} vs {redundant:.3f})")
    print(f"  H4 (open): where does 'middle' sit?      → middle p@3 = {middle:.3f}")
    print()

    # Print coupling distribution stats for insight
    storage_fresh, _ = build_baseline(D, N, DENSITY)
    synapse_stack = np.stack([s.polar_hv for s in storage_fresh.tier2.values()])
    signed_sum = synapse_stack.sum(axis=0).astype(np.int64)
    coupling = signed_sum ** 2
    print(f"  Coupling distribution at N={N}, density={DENSITY}:")
    print(f"    min={coupling.min()}, max={coupling.max()}, mean={coupling.mean():.1f}, median={np.median(coupling):.1f}")
    print(f"    fraction with coupling==0 (perfect balance): {float(np.mean(coupling == 0)):.3f}")
    print(f"    fraction with coupling>=10 (strong signal): {float(np.mean(coupling >= 10)):.3f}")

    # Write JSON results
    out_path = Path(__file__).parent / "R-RBS-NN-11b_results.json"
    out_path.write_text(json.dumps({
        "srmech_version": SRMECH_VERSION,
        "has_native": HAS_NATIVE,
        "abi": NATIVE_ABI_VERSION,
        "D": D, "N": N, "density": DENSITY, "total_decay": TOTAL_DECAY,
        "baseline": base_metrics,
        "results": results,
        "coupling_stats": {
            "min": int(coupling.min()),
            "max": int(coupling.max()),
            "mean": float(coupling.mean()),
            "median": float(np.median(coupling)),
            "frac_zero": float(np.mean(coupling == 0)),
            "frac_strong": float(np.mean(coupling >= 10)),
        },
    }, indent=2))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
