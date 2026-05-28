"""R-RBS-NN-11 — Phase 1: Capacity characterization sweep

Resolves Phase 1 of R-RBS-NN-10_FOLLOWUP_PHASED_PLAN.md.

Tasks per plan §1:
  T1.1: N-sweep ∈ {10, 25, 50, 100, 200, 256, 512}
  T1.2: density sweep at fixed N
  T1.3: decay-depth sweep
  T1.4: rehearsal frequency study
  T1.5: density-attestation early-warning threshold

Decision point at close:
  If ceiling N < 257: Phase 2 hierarchical bundling becomes BLOCKER
  If ceiling N ≥ 257: Phase 2 is enhancement; Phase 3/4 can run in parallel
"""
import json
import time
from pathlib import Path
import sys
import importlib.util

import numpy as np

# Local module load (the storage class)
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


def synthetic_lexicon(n: int) -> list[str]:
    """Generate N synthetic token names."""
    return [f"concept_{i:04d}" for i in range(n)]


def random_association_graph(tokens: list[str], degree: int, seed: int) -> list[tuple[str, str]]:
    """Build a random association graph with avg degree `degree`.

    Each concept gets `degree` random associations (deduplicated by
    canonical (sorted) key).
    """
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


def measure_retrieval(storage, pairs, top_k: int = 3, threshold: float = 0.50):
    """Measure precision@top_k across all known pairs.

    For each (a, b) in pairs, query a and check if b appears in top_k.
    """
    correct_at_1 = 0
    correct_at_top_k = 0
    sim_correct = []
    sim_random = []
    for a, b in pairs:
        retrieved = storage.retrieve_associated(a, top_k=top_k, threshold=0.0)
        if not retrieved:
            sim_random.append(0.0)
            continue
        tokens_only = [t for t, _ in retrieved]
        sims_only = [s for _, s in retrieved]
        if b in tokens_only:
            idx = tokens_only.index(b)
            sim_correct.append(sims_only[idx])
            if idx == 0:
                correct_at_1 += 1
            correct_at_top_k += 1
        else:
            sim_random.append(sims_only[0] if sims_only else 0.0)
    return {
        "precision_at_1": correct_at_1 / len(pairs) if pairs else 0.0,
        "precision_at_top_k": correct_at_top_k / len(pairs) if pairs else 0.0,
        "mean_sim_correct": float(np.mean(sim_correct)) if sim_correct else 0.0,
        "mean_sim_random": float(np.mean(sim_random)) if sim_random else 0.0,
        "n_pairs": len(pairs),
    }


# ============================================================
# T1.1 — N sweep
# ============================================================
def task_T1_1_n_sweep(D: int):
    """Sweep N ∈ {10, 25, 50, 100, 200, 256, 512} at fixed degree=2, density=0.67."""
    print("=" * 72)
    print("T1.1 — N-sweep (concepts) at degree=2, density=0.67")
    print("=" * 72)
    N_values = [10, 25, 50, 100, 200, 256, 512]
    results = []
    for N in N_values:
        tokens = synthetic_lexicon(N)
        pairs = random_association_graph(tokens, degree=2, seed=N * 7)
        storage = TwoTierRBSNNStorage(D=D, seed=42)
        # Encode all concepts
        t_enc = time.time()
        for tok in tokens:
            storage.encode_concept(tok)
        t_enc_done = time.time() - t_enc

        # Batch-learn associations
        t_lrn = time.time()
        storage.batch_learn(pairs, plasticity_density=0.67)
        t_lrn_done = time.time() - t_lrn

        # Measure retrieval
        t_ret = time.time()
        metrics = measure_retrieval(storage, pairs, top_k=3, threshold=0.0)
        t_ret_done = time.time() - t_ret

        att = storage.density_attestation()
        result = {
            "N": N,
            "n_pairs": len(pairs),
            "precision_at_1": metrics["precision_at_1"],
            "precision_at_top_k": metrics["precision_at_top_k"],
            "mean_sim_correct": metrics["mean_sim_correct"],
            "composite_density": att.get("composite_density"),
            "mean_synapse_density": att.get("mean_synapse_density"),
            "encode_sec": t_enc_done,
            "learn_sec": t_lrn_done,
            "retrieve_sec": t_ret_done,
        }
        results.append(result)
        print(
            f"  N={N:>4} | pairs={len(pairs):>4} | p@1={metrics['precision_at_1']:.3f} | "
            f"p@{3}={metrics['precision_at_top_k']:.3f} | "
            f"sim={metrics['mean_sim_correct']:+0.3f} | "
            f"density={att.get('composite_density', 0):.3f} | "
            f"enc={t_enc_done:.2f}s lrn={t_lrn_done:.2f}s ret={t_ret_done:.2f}s"
        )
    return results


# ============================================================
# T1.2 — density sweep at fixed N
# ============================================================
def task_T1_2_density_sweep(D: int):
    """At N=100, sweep plasticity_density ∈ {0.3, 0.5, 0.67, 0.85, 1.0}."""
    print()
    print("=" * 72)
    print("T1.2 — Density sweep at N=100")
    print("=" * 72)
    N = 100
    densities = [0.3, 0.5, 0.67, 0.85, 1.0]
    results = []
    tokens = synthetic_lexicon(N)
    pairs = random_association_graph(tokens, degree=2, seed=N * 7)
    for density in densities:
        storage = TwoTierRBSNNStorage(D=D, seed=42)
        for tok in tokens:
            storage.encode_concept(tok)
        storage.batch_learn(pairs, plasticity_density=density)
        metrics = measure_retrieval(storage, pairs, top_k=3, threshold=0.0)
        att = storage.density_attestation()
        results.append({
            "density_target": density,
            "n_pairs": len(pairs),
            "precision_at_1": metrics["precision_at_1"],
            "precision_at_top_k": metrics["precision_at_top_k"],
            "mean_sim_correct": metrics["mean_sim_correct"],
            "composite_density": att.get("composite_density"),
        })
        print(
            f"  density={density:.2f} | p@1={metrics['precision_at_1']:.3f} | "
            f"p@3={metrics['precision_at_top_k']:.3f} | "
            f"sim={metrics['mean_sim_correct']:+0.3f} | "
            f"composite_density={att.get('composite_density', 0):.3f}"
        )
    return results


# ============================================================
# T1.3 — decay-depth sweep
# ============================================================
def task_T1_3_decay_depth(D: int):
    """At N=100, apply 1/3/5/10 forget cycles at decay_rate=0.10."""
    print()
    print("=" * 72)
    print("T1.3 — Decay-depth sweep at N=100 (decay_rate=0.10/step)")
    print("=" * 72)
    N = 100
    tokens = synthetic_lexicon(N)
    pairs = random_association_graph(tokens, degree=2, seed=N * 7)
    storage = TwoTierRBSNNStorage(D=D, seed=42)
    for tok in tokens:
        storage.encode_concept(tok)
    storage.batch_learn(pairs, plasticity_density=0.67)

    cycles_checkpoints = [0, 1, 3, 5, 10]
    results = []
    cycles_done = 0
    for target in cycles_checkpoints:
        while cycles_done < target:
            storage.forget_step(decay_rate=0.10)
            cycles_done += 1
        metrics = measure_retrieval(storage, pairs, top_k=3, threshold=0.0)
        att = storage.density_attestation()
        results.append({
            "decay_cycles": target,
            "precision_at_1": metrics["precision_at_1"],
            "precision_at_top_k": metrics["precision_at_top_k"],
            "mean_sim_correct": metrics["mean_sim_correct"],
            "composite_density": att.get("composite_density"),
            "mean_synapse_density": att.get("mean_synapse_density"),
        })
        print(
            f"  cycles={target:>2} | p@1={metrics['precision_at_1']:.3f} | "
            f"p@3={metrics['precision_at_top_k']:.3f} | "
            f"sim={metrics['mean_sim_correct']:+0.3f} | "
            f"composite_density={att.get('composite_density', 0):.3f} | "
            f"syn_density={att.get('mean_synapse_density', 0):.3f}"
        )
    return results


# ============================================================
# T1.4 — rehearsal frequency
# ============================================================
def task_T1_4_rehearsal_frequency(D: int):
    """At N=50, apply decay then rehearse 1/2/4 times per pair."""
    print()
    print("=" * 72)
    print("T1.4 — Rehearsal frequency at N=50 after 3 decay cycles")
    print("=" * 72)
    N = 50
    tokens = synthetic_lexicon(N)
    pairs = random_association_graph(tokens, degree=2, seed=N * 7)
    rehearsal_counts = [0, 1, 2, 4]
    results = []
    for n_rehearse in rehearsal_counts:
        storage = TwoTierRBSNNStorage(D=D, seed=42)
        for tok in tokens:
            storage.encode_concept(tok)
        storage.batch_learn(pairs, plasticity_density=0.67)
        # Decay 3 cycles
        for _ in range(3):
            storage.forget_step(decay_rate=0.15)
        # Rehearse n_rehearse times for each pair
        for _ in range(n_rehearse):
            for a, b in pairs:
                storage.rehearse(a, b, recovery_fraction=0.5)
        metrics = measure_retrieval(storage, pairs, top_k=3, threshold=0.0)
        att = storage.density_attestation()
        results.append({
            "rehearsal_count": n_rehearse,
            "precision_at_1": metrics["precision_at_1"],
            "precision_at_top_k": metrics["precision_at_top_k"],
            "mean_sim_correct": metrics["mean_sim_correct"],
            "composite_density": att.get("composite_density"),
            "mean_synapse_density": att.get("mean_synapse_density"),
        })
        print(
            f"  rehearses={n_rehearse:>2} | p@1={metrics['precision_at_1']:.3f} | "
            f"p@3={metrics['precision_at_top_k']:.3f} | "
            f"sim={metrics['mean_sim_correct']:+0.3f} | "
            f"syn_density={att.get('mean_synapse_density', 0):.3f}"
        )
    return results


def main():
    D = 8192
    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}; D={D}")
    print()

    t_total = time.time()
    r_t1_1 = task_T1_1_n_sweep(D)
    r_t1_2 = task_T1_2_density_sweep(D)
    r_t1_3 = task_T1_3_decay_depth(D)
    r_t1_4 = task_T1_4_rehearsal_frequency(D)
    t_total_sec = time.time() - t_total

    # === Decision point analysis ===
    print()
    print("=" * 72)
    print("DECISION POINT ANALYSIS (per phased plan §1)")
    print("=" * 72)
    # Find ceiling: highest N where p@1 >= 0.50
    ceiling = None
    for r in r_t1_1:
        if r["precision_at_1"] >= 0.50:
            ceiling = r["N"]
    if ceiling is None:
        print("  Ceiling NOT FOUND in tested range (p@1 < 0.50 at smallest N)")
        verdict = "PHASE_2_HIERARCHICAL_BLOCKER"
    elif ceiling < 257:
        verdict = "PHASE_2_HIERARCHICAL_BLOCKER"
        print(f"  Ceiling at N={ceiling} < 257 → Phase 2 (hierarchical bundling) is BLOCKER")
    else:
        verdict = "PHASE_3_4_PARALLEL_OK"
        print(f"  Ceiling at N={ceiling} ≥ 257 → Phase 2 is enhancement; Phase 3/4 OK to run")
    print(f"  Verdict: {verdict}")

    # T1.5: density early-warning threshold
    # Look at T1.3 results for the point where retrieval crashes
    print()
    print("  T1.5 — Density early-warning threshold (from T1.3 decay data):")
    for r in r_t1_3:
        marker = ""
        if r["precision_at_1"] < 0.50:
            marker = "  ← p@1 dropped below 0.50"
        print(
            f"    composite_density={r['composite_density']:.3f}, p@1={r['precision_at_1']:.3f}{marker}"
        )

    print()
    print(f"Total sweep time: {t_total_sec:.1f}s")

    # Write results JSON
    out_path = Path(__file__).parent / "R-RBS-NN-11_results.json"
    out_path.write_text(json.dumps({
        "srmech_version": SRMECH_VERSION,
        "has_native": HAS_NATIVE,
        "abi": NATIVE_ABI_VERSION,
        "D": D,
        "seed": 42,
        "verdict": verdict,
        "ceiling_N": ceiling,
        "T1_1_n_sweep": r_t1_1,
        "T1_2_density_sweep": r_t1_2,
        "T1_3_decay_depth": r_t1_3,
        "T1_4_rehearsal_frequency": r_t1_4,
        "total_sweep_seconds": t_total_sec,
    }, indent=2))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
