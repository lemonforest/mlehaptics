"""R-RBS-LM-116 — Semantic plausibility scoring (Item 2 of 5)

Substrate-native plausibility scoring for compositional generation.
No learned semantic model — uses training-corpus co-occurrence
statistics + substrate similarity as the discrimination signal.

Per F156 §5: the substrate already provides a discrimination signal
(training-frame similarity 1.00 for in-training vs ~0.26 for novel
compositions). This script formalises that into a plausibility score.

Score components (all substrate-native):
  1. bigram_freq_score: log-frequency of each adjacent bigram in
     training corpus (sum across bigrams, normalised)
  2. subj_verb_score: how often (subj, verb) appears in training as a
     non-adjacent pair (skip-gram at distance ≤ 2)
  3. verb_obj_score: same for (verb, obj)
  4. substrate_skel_sim: skeleton-frame similarity to nearest training
     skeleton (already computed by VL memory)

Combined plausibility = weighted geometric mean.

Validation:
  - In-training sentences should score HIGH
  - Cross-pattern compositions (F156 Mode D) should score MEDIUM
  - Random word permutations should score LOW
"""
import json
import math
from collections import Counter
from pathlib import Path
import importlib.util
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
for spec_name, fname in [
    ("vl_memory", "R-RBS-LM-112_variable_length_sentences.py"),
    ("corpus_gen", "R-RBS-LM-113_larger_corpus_scaling.py"),
    ("hier_memory", "R-RBS-LM-114_hierarchical_scale_up.py"),
]:
    _spec = importlib.util.spec_from_file_location(
        spec_name, Path(__file__).parent / fname
    )
    _mod = importlib.util.module_from_spec(_spec)
    sys.modules[spec_name] = _mod
    _spec.loader.exec_module(_mod)

import corpus_gen
import hier_memory

generate_corpus = corpus_gen.generate_corpus
HierarchicalVariableLengthMemory = hier_memory.HierarchicalVariableLengthMemory

from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION


D = 8192


class PlausibilityScorer:
    """Substrate-native semantic plausibility from training co-occurrence."""

    def __init__(self, corpus: list[list[str]]):
        # Adjacent bigram counts
        self.bigram_counts: Counter = Counter()
        # Skip-gram counts (distance 1..3)
        self.skip2_counts: Counter = Counter()  # distance 2
        self.skip3_counts: Counter = Counter()  # distance 3
        # Token frequency for smoothing
        self.token_counts: Counter = Counter()

        for tokens in corpus:
            for i in range(len(tokens)):
                self.token_counts[tokens[i]] += 1
                if i + 1 < len(tokens):
                    self.bigram_counts[(tokens[i], tokens[i+1])] += 1
                if i + 2 < len(tokens):
                    self.skip2_counts[(tokens[i], tokens[i+2])] += 1
                if i + 3 < len(tokens):
                    self.skip3_counts[(tokens[i], tokens[i+3])] += 1

        self.n_tokens = sum(self.token_counts.values())
        self.n_bigrams = sum(self.bigram_counts.values())

    def score(self, tokens: list[str], substrate_skel_sim: float = 1.0) -> dict:
        """Compute plausibility components and combined score.

        Returns dict with each component + combined score in [0, 1].
        """
        if len(tokens) < 2:
            return {"combined": 0.0, "reason": "too_short"}

        # 1. Adjacent bigram score: avg log(freq+1) normalised
        bigram_scores = []
        for i in range(len(tokens) - 1):
            count = self.bigram_counts.get((tokens[i], tokens[i+1]), 0)
            bigram_scores.append(math.log(count + 1))
        avg_bigram = sum(bigram_scores) / len(bigram_scores)
        # Normalise by max possible log(N+1)
        max_log = math.log(max(self.bigram_counts.values()) + 1)
        bigram_score_norm = avg_bigram / max_log if max_log > 0 else 0

        # 2. Skip-gram score: distance-2 + distance-3 averaged
        skip_scores = []
        for i in range(len(tokens) - 2):
            count = self.skip2_counts.get((tokens[i], tokens[i+2]), 0)
            skip_scores.append(math.log(count + 1))
        for i in range(len(tokens) - 3):
            count = self.skip3_counts.get((tokens[i], tokens[i+3]), 0)
            skip_scores.append(math.log(count + 1))
        if skip_scores:
            avg_skip = sum(skip_scores) / len(skip_scores)
            max_log_skip = math.log(max(
                max(self.skip2_counts.values(), default=1),
                max(self.skip3_counts.values(), default=1)
            ) + 1)
            skip_score_norm = avg_skip / max_log_skip if max_log_skip > 0 else 0
        else:
            skip_score_norm = 0

        # 3. Token presence: fraction of tokens seen in training
        n_known = sum(1 for t in tokens if t in self.token_counts)
        token_score = n_known / len(tokens)

        # 4. Combined: weighted geometric mean over substrate + co-occurrence
        # Weights tuned to favor co-occurrence (semantic) over substrate (structural)
        eps = 1e-6
        components = {
            "bigram_freq": bigram_score_norm,
            "skip_gram": skip_score_norm,
            "token_known": token_score,
            "substrate_skel_sim": substrate_skel_sim,
        }
        weights = {"bigram_freq": 0.4, "skip_gram": 0.2,
                   "token_known": 0.1, "substrate_skel_sim": 0.3}
        log_combined = sum(
            weights[k] * math.log(components[k] + eps) for k in weights
        )
        combined = math.exp(log_combined)

        return {**components, "combined": combined}


def main():
    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}; D={D}\n")

    # Build memory + scorer from training corpus
    rng = np.random.default_rng(42)
    corpus = generate_corpus(2000, rng)
    actual_n = len(corpus)
    print(f"Building hierarchical memory + scorer: N={actual_n}, n_buckets=16\n")

    memory = HierarchicalVariableLengthMemory(D=D, n_buckets=16)
    for tokens in corpus:
        memory.learn_sentence(tokens)

    scorer = PlausibilityScorer(corpus)
    print(f"Scorer trained: {len(scorer.token_counts)} unique tokens, "
          f"{len(scorer.bigram_counts)} unique bigrams\n")

    # Three test categories
    seeds = [("the", "cat"), ("the", "scientist"), ("a", "wolf"),
             ("the", "musician"), ("a", "bird")]

    # Category 1: In-training sentences (sampled from corpus)
    in_training = [tuple(s) for s in corpus[:50]]

    # Category 2: Generated compositional sentences
    generated = []
    for seed in seeds:
        gen = memory.generate_from_seed(seed, top_k=15)
        for entry in gen:
            generated.append((tuple(entry["sentence"]), entry["skeleton_sim"]))

    # Category 3: Random permutations of same vocabulary (junk control)
    all_words = list(scorer.token_counts.keys())
    rng_perm = np.random.default_rng(7)
    junk = []
    for _ in range(50):
        length = int(rng_perm.choice([4, 5, 6, 7]))
        junk.append(tuple(rng_perm.choice(all_words, size=length, replace=True)))

    # Score each category
    in_training_scores = [scorer.score(list(s), 1.0)["combined"] for s in in_training]
    generated_scores = [scorer.score(list(s), sim)["combined"] for s, sim in generated]
    junk_scores = [scorer.score(list(s), 0.25)["combined"] for s in junk]

    def stats(arr):
        a = np.array(arr)
        return {"n": len(a), "mean": float(a.mean()),
                "std": float(a.std()), "min": float(a.min()), "max": float(a.max())}

    print(f"{'Category':>15} | {'n':>4} | {'mean':>7} | {'std':>6} | {'min':>7} | {'max':>7}")
    print("-" * 70)
    for name, arr in [("in_training", in_training_scores),
                      ("compositional", generated_scores),
                      ("random_junk", junk_scores)]:
        s = stats(arr)
        print(f"{name:>15} | {s['n']:>4} | {s['mean']:>7.3f} | "
              f"{s['std']:>6.3f} | {s['min']:>7.3f} | {s['max']:>7.3f}")

    # Discrimination signal: does the metric separate the categories?
    in_train_mean = np.mean(in_training_scores)
    comp_mean = np.mean(generated_scores)
    junk_mean = np.mean(junk_scores)
    print()
    print(f"Discrimination ratios:")
    print(f"  in_training / random_junk     = {in_train_mean / junk_mean:.2f}×")
    print(f"  in_training / compositional   = {in_train_mean / comp_mean:.2f}×")
    print(f"  compositional / random_junk   = {comp_mean / junk_mean:.2f}×")

    # Print sample top + bottom generated sentences
    print()
    print("=" * 80)
    print("Sample generated sentences ranked by plausibility")
    print("=" * 80)
    scored_gen = [(s, sim, scorer.score(list(s), sim)["combined"])
                  for s, sim in generated]
    scored_gen.sort(key=lambda x: -x[2])
    print("\n  TOP 5 (most plausible):")
    for sent, sim, score in scored_gen[:5]:
        print(f"    [score={score:.3f}, skel={sim:.2f}] {' '.join(sent)}")
    print("\n  BOTTOM 5 (least plausible):")
    for sent, sim, score in scored_gen[-5:]:
        print(f"    [score={score:.3f}, skel={sim:.2f}] {' '.join(sent)}")

    print("\n  SAMPLE JUNK (random permutations):")
    for sent in [tuple(rng_perm.choice(all_words, size=5)) for _ in range(3)]:
        score = scorer.score(list(sent), 0.25)["combined"]
        print(f"    [score={score:.3f}] {' '.join(sent)}")

    out = {
        "srmech_version": SRMECH_VERSION,
        "D": D,
        "corpus_n": actual_n,
        "n_buckets": 16,
        "category_stats": {
            "in_training": stats(in_training_scores),
            "compositional": stats(generated_scores),
            "random_junk": stats(junk_scores),
        },
        "discrimination_ratios": {
            "training_vs_junk": in_train_mean / junk_mean,
            "training_vs_compositional": in_train_mean / comp_mean,
            "compositional_vs_junk": comp_mean / junk_mean,
        },
        "top_5_generated": [
            {"sentence": " ".join(s), "skel_sim": sim, "combined_score": score}
            for s, sim, score in scored_gen[:5]
        ],
        "bottom_5_generated": [
            {"sentence": " ".join(s), "skel_sim": sim, "combined_score": score}
            for s, sim, score in scored_gen[-5:]
        ],
    }
    out_path = Path(__file__).parent / "R-RBS-LM-116_results.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
