"""R-RBS-LM-114 — Hierarchical scale-up (Item 4 of 5)

Combine R-RBS-LM-112 variable-length sentence memory with
R-RBS-NN-12 hierarchical bucketing to test substrate at LLM-class
sentence counts (1000 / 2000 / 4000).

Architecture:
  - n_buckets independent VariableLengthSentenceMemory instances
  - Sentence routed to bucket via sha256(sentence_text) mod n_buckets
  - Self-recall queries ONLY the sentence's bucket
    (deterministic routing; we know which bucket a sentence lives in)
  - Generation-from-seed queries ALL buckets in parallel and merges
    candidates

Per F154 4× ceiling + R-RBS-NN-12 hierarchical bundling per F148:
  - Each bucket has its own substrate density attestation
  - Total capacity = n_buckets × per-bucket V_ceiling (~257 with current
    R-RBS-NN-12 defaults; here we set bucket_target=200 sentences each)

Measures:
  - Self-recall as N scales 1000 → 2000 → 4000
  - Build time + memory growth
  - Generation diversity (cross-bucket merge correctness)
"""
import json
import time
from pathlib import Path
import importlib.util
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
_spec_vl = importlib.util.spec_from_file_location(
    "vl_memory", Path(__file__).parent / "R-RBS-LM-112_variable_length_sentences.py"
)
_mod_vl = importlib.util.module_from_spec(_spec_vl)
sys.modules["vl_memory"] = _mod_vl
_spec_vl.loader.exec_module(_mod_vl)
VariableLengthSentenceMemory = _mod_vl.VariableLengthSentenceMemory
encode_sentence_l3 = _mod_vl.encode_sentence_l3
sim_k4_batch = _mod_vl.sim_k4_batch

_spec_corpus = importlib.util.spec_from_file_location(
    "corpus_gen", Path(__file__).parent / "R-RBS-LM-113_larger_corpus_scaling.py"
)
_mod_corpus = importlib.util.module_from_spec(_spec_corpus)
sys.modules["corpus_gen"] = _mod_corpus
_spec_corpus.loader.exec_module(_mod_corpus)
generate_corpus = _mod_corpus.generate_corpus

from srmech.amsc import format as amsc_format
from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION


D = 8192


class HierarchicalVariableLengthMemory:
    """Hierarchically-bucketed variable-length sentence memory.

    Implements R-RBS-NN-12 hierarchical bundling pattern adapted for
    F156 sentence-level substrate (F155 4-level chirality channels).
    """

    def __init__(self, D: int = 8192, n_buckets: int = 16):
        self.D = D
        self.n_buckets = n_buckets
        self.buckets: list[VariableLengthSentenceMemory] = [
            VariableLengthSentenceMemory(D=D) for _ in range(n_buckets)
        ]

    def _bucket_for_sentence(self, tokens: list[str]) -> int:
        text = " ".join(tokens).encode("utf-8")
        digest = amsc_format.sha256_bytes(text)
        return int(digest[:8], 16) % self.n_buckets

    def learn_sentence(self, tokens: list[str]):
        b = self._bucket_for_sentence(tokens)
        self.buckets[b].learn_sentence(tokens)
        return b

    def recall_sentence(self, tokens: list[str]) -> bool:
        """Deterministic-bucket self-recall: encode, route to bucket, check argmax."""
        b = self._bucket_for_sentence(tokens)
        bucket = self.buckets[b]
        if not bucket.sentences_l3:
            return False
        target = encode_sentence_l3(tokens)
        sentences_matrix = np.stack(list(bucket.sentences_l3.values()))
        sentence_keys = list(bucket.sentences_l3.keys())
        sims = sim_k4_batch(target, sentences_matrix)
        return sentence_keys[int(sims.argmax())] == tuple(tokens)

    def generate_from_seed(self, seed: tuple[str, str], top_k: int = 5) -> list:
        """All-bucket generation: query each bucket, merge results."""
        all_results = []
        for bucket in self.buckets:
            if seed in bucket.bigrams_l1:
                results = bucket.generate_variable_length(seed, top_k=top_k)
                all_results.extend(results)
        # Dedupe by sentence tuple
        seen = set()
        unique = []
        for entry in sorted(all_results, key=lambda e: -e["skeleton_sim"]):
            key = tuple(entry["sentence"])
            if key not in seen:
                seen.add(key)
                unique.append(entry)
        return unique[:top_k]

    def total_sentences(self) -> int:
        return sum(len(b.sentences_l3) for b in self.buckets)

    def total_words(self) -> int:
        all_words = set()
        for b in self.buckets:
            all_words.update(b.words_l0.keys())
        return len(all_words)

    def bucket_load_stats(self) -> dict:
        loads = [len(b.sentences_l3) for b in self.buckets]
        return {
            "n_buckets": self.n_buckets,
            "min": min(loads),
            "max": max(loads),
            "mean": sum(loads) / len(loads),
            "std": float(np.std(loads)),
            "loads": loads,
        }


def measure_hierarchical_scaling(target_sizes, n_buckets_list):
    """For each (N, n_buckets) combination, build + measure."""
    results = []
    for n_target in target_sizes:
        for n_buckets in n_buckets_list:
            rng = np.random.default_rng(42)
            corpus = generate_corpus(n_target, rng)
            actual_n = len(corpus)

            t0 = time.time()
            memory = HierarchicalVariableLengthMemory(D=D, n_buckets=n_buckets)
            for tokens in corpus:
                memory.learn_sentence(tokens)
            t_build = time.time() - t0

            # Self-recall on sample of 50
            sample = corpus[:50] if len(corpus) > 50 else corpus
            t0 = time.time()
            correct = sum(1 for tokens in sample if memory.recall_sentence(tokens))
            t_recall = time.time() - t0

            stats = memory.bucket_load_stats()
            results.append({
                "n_target": n_target,
                "n_actual": actual_n,
                "n_buckets": n_buckets,
                "n_words": memory.total_words(),
                "n_sentences": memory.total_sentences(),
                "self_recall_sampled": correct / len(sample),
                "build_seconds": t_build,
                "recall_seconds": t_recall,
                "bucket_min": stats["min"],
                "bucket_max": stats["max"],
                "bucket_mean": stats["mean"],
                "bucket_std": stats["std"],
            })
    return results


def main():
    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}; D={D}\n")

    target_sizes = [1000, 2000, 4000]
    n_buckets_list = [8, 16, 32]

    print(f"{'n_target':>9} | {'n_actual':>9} | {'buckets':>7} | {'words':>5} | "
          f"{'sents':>5} | {'recall':>6} | {'build_s':>7} | {'recall_s':>8} | "
          f"{'b_min':>5} | {'b_max':>5} | {'b_mean':>7} | {'b_std':>6}")
    print("-" * 130)

    results = measure_hierarchical_scaling(target_sizes, n_buckets_list)
    for r in results:
        print(
            f"{r['n_target']:>9} | {r['n_actual']:>9} | {r['n_buckets']:>7} | "
            f"{r['n_words']:>5} | {r['n_sentences']:>5} | "
            f"{r['self_recall_sampled']:.3f}  | {r['build_seconds']:>7.1f} | "
            f"{r['recall_seconds']:>8.2f} | {r['bucket_min']:>5} | "
            f"{r['bucket_max']:>5} | {r['bucket_mean']:>7.1f} | {r['bucket_std']:>6.2f}"
        )

    # Generation diversity at N=4000 with 32 buckets
    print()
    print("=" * 80)
    print("Generation diversity at N=4000, n_buckets=32 — sample seeds")
    print("=" * 80)
    rng = np.random.default_rng(42)
    corpus = generate_corpus(4000, rng)
    memory = HierarchicalVariableLengthMemory(D=D, n_buckets=32)
    for tokens in corpus:
        memory.learn_sentence(tokens)

    sample_seeds = [("the", "cat"), ("the", "scientist"), ("a", "bird"),
                    ("the", "musician"), ("a", "wolf"), ("the", "queen")]
    diversity_results = {}
    for seed in sample_seeds:
        gen = memory.generate_from_seed(seed, top_k=10)
        diversity_results[str(seed)] = len(gen)
        print(f"\n  Seed: {seed} ({len(gen)} unique completions)")
        for entry in gen[:5]:
            sent = " ".join(entry["sentence"])
            length = entry["length"]
            sim = entry["skeleton_sim"]
            print(f"    [L={length}, sim={sim:.2f}] {sent}")

    out = {
        "srmech_version": SRMECH_VERSION,
        "D": D,
        "hierarchical_scaling_results": results,
        "n_4000_generation_diversity": diversity_results,
    }
    out_path = Path(__file__).parent / "R-RBS-LM-114_results.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
