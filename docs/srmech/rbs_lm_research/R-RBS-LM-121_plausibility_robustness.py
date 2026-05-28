"""R-RBS-LM-121 — Plausibility scoring robustness full coverage extension

Extends R-RBS-LM-116's hand-picked-weights / 3-category measurement to:
  - Weight-sensitivity sweep: vary each component weight, measure
    discrimination effect
  - Multiple perturbation categories (not just full-random junk):
    * single-token swap (one word replaced with random vocab)
    * type-violation (subject in object slot)
    * partial-shuffle (50% of tokens permuted)
    * full-random (R-RBS-LM-116 baseline)
  - ROC analysis for valid-vs-junk classification
  - Per-length plausibility breakdown
  - AUC summary across perturbation types

Per [[feedback_no_mvp_framing]] + [[feedback_full_coverage_shipping_mpm_way]]:
characterizes the metric's robustness across the (weight × perturbation × length)
volume, not just one slice.
"""
import json
import math
from collections import defaultdict, Counter
from pathlib import Path
import importlib.util
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
for spec_name, fname in [
    ("vl_memory", "R-RBS-LM-112_variable_length_sentences.py"),
    ("corpus_gen", "R-RBS-LM-113_larger_corpus_scaling.py"),
    ("hier_memory", "R-RBS-LM-114_hierarchical_scale_up.py"),
    ("plaus_v1", "R-RBS-LM-116_semantic_plausibility_scoring.py"),
]:
    _spec = importlib.util.spec_from_file_location(
        spec_name, Path(__file__).parent / fname
    )
    _mod = importlib.util.module_from_spec(_spec)
    sys.modules[spec_name] = _mod
    _spec.loader.exec_module(_mod)

import corpus_gen
import hier_memory
import plaus_v1

generate_corpus = corpus_gen.generate_corpus
HierarchicalVariableLengthMemory = hier_memory.HierarchicalVariableLengthMemory
PlausibilityScorer = plaus_v1.PlausibilityScorer

from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION


D = 8192


class WeightedPlausibilityScorer(PlausibilityScorer):
    """PlausibilityScorer with configurable weights for robustness analysis."""

    def __init__(self, corpus, weights=None):
        super().__init__(corpus)
        # Default weights from R-RBS-LM-116
        self.weights = weights or {
            "bigram_freq": 0.4,
            "skip_gram": 0.2,
            "token_known": 0.1,
            "substrate_skel_sim": 0.3,
        }

    def score(self, tokens, substrate_skel_sim=1.0):
        """Score override using self.weights."""
        if len(tokens) < 2:
            return {"combined": 0.0, "reason": "too_short"}

        # Compute components (same as parent)
        bigram_scores = []
        for i in range(len(tokens) - 1):
            count = self.bigram_counts.get((tokens[i], tokens[i + 1]), 0)
            bigram_scores.append(math.log(count + 1))
        avg_bigram = sum(bigram_scores) / len(bigram_scores)
        max_log = math.log(max(self.bigram_counts.values()) + 1)
        bigram_norm = avg_bigram / max_log if max_log > 0 else 0

        skip_scores = []
        for i in range(len(tokens) - 2):
            count = self.skip2_counts.get((tokens[i], tokens[i + 2]), 0)
            skip_scores.append(math.log(count + 1))
        for i in range(len(tokens) - 3):
            count = self.skip3_counts.get((tokens[i], tokens[i + 3]), 0)
            skip_scores.append(math.log(count + 1))
        if skip_scores:
            avg_skip = sum(skip_scores) / len(skip_scores)
            max_log_skip = math.log(max(
                max(self.skip2_counts.values(), default=1),
                max(self.skip3_counts.values(), default=1)
            ) + 1)
            skip_norm = avg_skip / max_log_skip if max_log_skip > 0 else 0
        else:
            skip_norm = 0

        n_known = sum(1 for t in tokens if t in self.token_counts)
        token_score = n_known / len(tokens)

        components = {
            "bigram_freq": bigram_norm,
            "skip_gram": skip_norm,
            "token_known": token_score,
            "substrate_skel_sim": substrate_skel_sim,
        }
        eps = 1e-6
        log_combined = sum(
            self.weights[k] * math.log(components[k] + eps) for k in self.weights
        )
        combined = math.exp(log_combined)
        return {**components, "combined": combined}


def gen_perturbation(category, in_training_set, all_words, rng):
    """Generate a perturbation sentence from a training sentence."""
    base = list(rng.choice(in_training_set))
    if category == "single_swap":
        # Replace one token with random vocab
        idx = rng.integers(len(base))
        base[idx] = rng.choice(all_words)
    elif category == "type_violation":
        # Swap subject and object positions if both identifiable
        if len(base) >= 4:
            # Swap pos 1 (typically SUBJ) and pos -1 (typically OBJ)
            base[1], base[-1] = base[-1], base[1]
    elif category == "partial_shuffle":
        # Shuffle ~50% of tokens
        n_shuffle = max(2, len(base) // 2)
        idxs = list(rng.choice(len(base), size=n_shuffle, replace=False))
        permuted = list(rng.permutation([base[i] for i in idxs]))
        for i, p in zip(idxs, permuted):
            base[i] = p
    elif category == "full_random":
        L = len(base)
        base = list(rng.choice(all_words, size=L, replace=True))
    return tuple(base)


def compute_auc_simple(scores_pos, scores_neg):
    """Simple AUC via empirical CDF; no sklearn dependency."""
    pos = np.array(scores_pos)
    neg = np.array(scores_neg)
    if len(pos) == 0 or len(neg) == 0:
        return 0.5
    # AUC = P(score_pos > score_neg)
    # Mann-Whitney U statistic / (n_pos * n_neg)
    n_pos = len(pos)
    n_neg = len(neg)
    n_correct = sum(p > n for p in pos for n in neg)
    n_ties = sum(p == n for p in pos for n in neg)
    return (n_correct + 0.5 * n_ties) / (n_pos * n_neg)


def measure_with_weights(memory, scorer, in_training_set, all_words):
    """Compute scores across all perturbation categories at fixed weights."""
    rng_p = np.random.default_rng(7)
    # In-training samples
    in_train_sample = [in_training_set[i] for i in
                       rng_p.choice(len(in_training_set), size=80, replace=False)]
    in_train_scores = [scorer.score(list(s), 1.0)["combined"] for s in in_train_sample]

    # Compositional from substrate
    seeds = []
    for b in memory.buckets:
        seeds.extend(list(b.bigrams_l1.keys()))
    seeds = list(set(seeds))[:30]
    comp_scores = []
    comp_per_length = defaultdict(list)
    for seed in seeds:
        gen = memory.generate_from_seed(seed, top_k=5)
        for entry in gen:
            score = scorer.score(entry["sentence"], entry["skeleton_sim"])["combined"]
            comp_scores.append(score)
            comp_per_length[len(entry["sentence"])].append(score)

    # Perturbations (50 each)
    perturbed = {}
    for category in ["single_swap", "type_violation", "partial_shuffle", "full_random"]:
        sample = [gen_perturbation(category, in_training_set, all_words, rng_p)
                  for _ in range(80)]
        # Substrate-sim hint: full_random gets 0.1, others 0.3 (degraded but not zero)
        sub_hint = 0.1 if category == "full_random" else 0.3
        perturbed[category] = [scorer.score(list(s), sub_hint)["combined"] for s in sample]

    return {
        "in_training": in_train_scores,
        "compositional": comp_scores,
        "compositional_per_length": dict(comp_per_length),
        **perturbed,
    }


def main():
    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}; D={D}\n")

    # Build substrate + scorer
    rng = np.random.default_rng(42)
    corpus = generate_corpus(2000, rng)
    actual_n = len(corpus)
    print(f"Corpus: {actual_n} sentences\n")

    memory = HierarchicalVariableLengthMemory(D=D, n_buckets=16)
    for tokens in corpus:
        memory.learn_sentence(tokens)
    print(f"Memory: {memory.total_sentences()} sentences across 16 buckets, "
          f"{memory.total_words()} unique words\n")

    # PHASE 1: baseline weights + full perturbation panel
    print("=" * 110)
    print("PHASE 1: baseline weights (R-RBS-LM-116) × full perturbation panel")
    print("=" * 110)
    scorer = WeightedPlausibilityScorer(corpus)
    all_words = list(scorer.token_counts.keys())
    in_train_set = [tuple(s) for s in corpus]

    p1 = measure_with_weights(memory, scorer, in_train_set, all_words)

    def stats(arr):
        a = np.array(arr)
        return {"n": len(a), "mean": float(a.mean()), "std": float(a.std()),
                "min": float(a.min()), "max": float(a.max())}

    print(f"{'category':>20} | {'n':>4} | {'mean':>6} | {'std':>5} | {'min':>6} | {'max':>6}")
    print("-" * 70)
    category_stats = {}
    for cat in ["in_training", "compositional", "single_swap", "type_violation",
                "partial_shuffle", "full_random"]:
        s = stats(p1[cat])
        category_stats[cat] = s
        print(f"{cat:>20} | {s['n']:>4} | {s['mean']:>6.3f} | {s['std']:>5.3f} | "
              f"{s['min']:>6.3f} | {s['max']:>6.3f}")

    # Discrimination ratios + AUCs
    print()
    print("=" * 110)
    print("PHASE 1b: pairwise AUC (in_training-vs-X) — receiver-operator characteristic")
    print("=" * 110)
    print(f"{'comparison':>30} | {'AUC':>5} | {'mean_pos':>8} | {'mean_neg':>8} | {'ratio':>6}")
    print("-" * 90)
    aucs = {}
    for cat in ["compositional", "single_swap", "type_violation",
                "partial_shuffle", "full_random"]:
        auc = compute_auc_simple(p1["in_training"], p1[cat])
        ratio = (np.mean(p1["in_training"]) / np.mean(p1[cat]) if np.mean(p1[cat]) > 0 else float('inf'))
        aucs[f"in_training_vs_{cat}"] = auc
        print(f"{'in_training_vs_' + cat:>30} | {auc:>5.3f} | "
              f"{np.mean(p1['in_training']):>8.3f} | {np.mean(p1[cat]):>8.3f} | "
              f"{ratio:>6.2f}×")

    # PHASE 2: weight sensitivity sweep
    print()
    print("=" * 110)
    print("PHASE 2: weight sensitivity sweep — does discrimination depend on weights?")
    print("=" * 110)
    weight_configs = [
        ("baseline", {"bigram_freq": 0.4, "skip_gram": 0.2, "token_known": 0.1, "substrate_skel_sim": 0.3}),
        ("bigram_only", {"bigram_freq": 1.0, "skip_gram": 0.0, "token_known": 0.0, "substrate_skel_sim": 0.0}),
        ("skip_only", {"bigram_freq": 0.0, "skip_gram": 1.0, "token_known": 0.0, "substrate_skel_sim": 0.0}),
        ("token_only", {"bigram_freq": 0.0, "skip_gram": 0.0, "token_known": 1.0, "substrate_skel_sim": 0.0}),
        ("substrate_only", {"bigram_freq": 0.0, "skip_gram": 0.0, "token_known": 0.0, "substrate_skel_sim": 1.0}),
        ("balanced", {"bigram_freq": 0.25, "skip_gram": 0.25, "token_known": 0.25, "substrate_skel_sim": 0.25}),
        ("co_occur_heavy", {"bigram_freq": 0.6, "skip_gram": 0.3, "token_known": 0.05, "substrate_skel_sim": 0.05}),
        ("substrate_heavy", {"bigram_freq": 0.1, "skip_gram": 0.1, "token_known": 0.1, "substrate_skel_sim": 0.7}),
    ]

    print(f"{'config':>20} | {'AUC(train|junk)':>15} | {'AUC(train|swap)':>15} | "
          f"{'AUC(train|type)':>15} | {'AUC(train|shuf)':>15}")
    print("-" * 100)
    phase2_results = []
    for name, weights in weight_configs:
        scorer_w = WeightedPlausibilityScorer(corpus, weights)
        pw = measure_with_weights(memory, scorer_w, in_train_set, all_words)
        auc_junk = compute_auc_simple(pw["in_training"], pw["full_random"])
        auc_swap = compute_auc_simple(pw["in_training"], pw["single_swap"])
        auc_type = compute_auc_simple(pw["in_training"], pw["type_violation"])
        auc_shuf = compute_auc_simple(pw["in_training"], pw["partial_shuffle"])
        phase2_results.append({
            "config_name": name,
            "weights": weights,
            "auc_in_training_vs_full_random": auc_junk,
            "auc_in_training_vs_single_swap": auc_swap,
            "auc_in_training_vs_type_violation": auc_type,
            "auc_in_training_vs_partial_shuffle": auc_shuf,
        })
        print(f"{name:>20} | {auc_junk:>15.3f} | {auc_swap:>15.3f} | "
              f"{auc_type:>15.3f} | {auc_shuf:>15.3f}")

    # PHASE 3: per-length plausibility breakdown
    print()
    print("=" * 110)
    print("PHASE 3: compositional plausibility by sentence length")
    print("=" * 110)
    print(f"{'L':>3} | {'n':>4} | {'mean':>6} | {'std':>5}")
    print("-" * 40)
    phase3 = {}
    for L, scores in sorted(p1["compositional_per_length"].items()):
        s = stats(scores)
        phase3[L] = s
        print(f"{L:>3} | {s['n']:>4} | {s['mean']:>6.3f} | {s['std']:>5.3f}")

    out = {
        "srmech_version": SRMECH_VERSION,
        "D": D,
        "corpus_n": actual_n,
        "phase1_baseline_category_stats": category_stats,
        "phase1b_baseline_aucs": aucs,
        "phase2_weight_sensitivity": phase2_results,
        "phase3_per_length_plausibility": phase3,
    }
    out_path = Path(__file__).parent / "R-RBS-LM-121_results.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
