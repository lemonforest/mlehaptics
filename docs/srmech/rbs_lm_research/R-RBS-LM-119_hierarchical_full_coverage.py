"""R-RBS-LM-119 — Hierarchical full coverage extension

Extends R-RBS-LM-114's single-strategy / single-bucket-grid measurement to:
  - BOTH bucket strategies: 'hash' (R-RBS-LM-114) + 'sentence_first_bigram'
    (analog of R-RBS-NN-12's 'sector_then_hash' — but sentence-level)
  - bucket-count sweep {4, 8, 16, 32, 64, 128, 256}
  - N up to where hierarchical breaks (16000+)
  - per-bucket load distribution analysis at each (N, n_buckets, strategy)
  - cross-bucket retrieval correctness for generation at scale

Per [[feedback_no_mvp_framing]] + [[feedback_full_coverage_shipping_mpm_way]]:
characterizes the hierarchical substrate across the (strategy × bucket-count × N)
volume, not just one slice.
"""
import json
import time
from collections import defaultdict
from pathlib import Path
import importlib.util
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
for spec_name, fname in [
    ("vl_memory", "R-RBS-LM-112_variable_length_sentences.py"),
    ("corpus_gen", "R-RBS-LM-113_larger_corpus_scaling.py"),
]:
    _spec = importlib.util.spec_from_file_location(
        spec_name, Path(__file__).parent / fname
    )
    _mod = importlib.util.module_from_spec(_spec)
    sys.modules[spec_name] = _mod
    _spec.loader.exec_module(_mod)

import vl_memory as _vl
import corpus_gen as _cg
VariableLengthSentenceMemory = _vl.VariableLengthSentenceMemory
encode_sentence_l3 = _vl.encode_sentence_l3
sim_k4_batch = _vl.sim_k4_batch
generate_corpus = _cg.generate_corpus

from srmech.amsc import format as amsc_format
from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION


D = 8192


class HierarchicalVariableLengthMemoryFullCov:
    """Hierarchical VL memory with selectable routing strategy."""

    def __init__(self, D: int = 8192, n_buckets: int = 16, strategy: str = "hash"):
        if strategy not in ("hash", "first_bigram_hash"):
            raise ValueError(f"strategy must be 'hash' or 'first_bigram_hash'; got {strategy}")
        self.D = D
        self.n_buckets = n_buckets
        self.strategy = strategy
        self.buckets: list[VariableLengthSentenceMemory] = [
            VariableLengthSentenceMemory(D=D) for _ in range(n_buckets)
        ]

    def _bucket_for_sentence(self, tokens: list[str]) -> int:
        if self.strategy == "hash":
            text = " ".join(tokens).encode("utf-8")
            digest = amsc_format.sha256_bytes(text)
            return int(digest[:8], 16) % self.n_buckets
        elif self.strategy == "first_bigram_hash":
            # Route by first-bigram hash; sentences sharing a head cluster
            if len(tokens) < 2:
                key = tokens[0].encode("utf-8") if tokens else b""
            else:
                key = f"{tokens[0]}_{tokens[1]}".encode("utf-8")
            digest = amsc_format.sha256_bytes(key)
            return int(digest[:8], 16) % self.n_buckets

    def learn_sentence(self, tokens: list[str]):
        b = self._bucket_for_sentence(tokens)
        self.buckets[b].learn_sentence(tokens)
        return b

    def recall_sentence(self, tokens: list[str]) -> bool:
        b = self._bucket_for_sentence(tokens)
        bucket = self.buckets[b]
        if not bucket.sentences_l3:
            return False
        target = encode_sentence_l3(tokens)
        sentences_matrix = np.stack(list(bucket.sentences_l3.values()))
        sentence_keys = list(bucket.sentences_l3.keys())
        sims = sim_k4_batch(target, sentences_matrix)
        return sentence_keys[int(sims.argmax())] == tuple(tokens)

    def bucket_load_stats(self) -> dict:
        loads = [len(b.sentences_l3) for b in self.buckets]
        arr = np.array(loads)
        return {
            "n_buckets": self.n_buckets,
            "min": int(arr.min()),
            "max": int(arr.max()),
            "mean": float(arr.mean()),
            "std": float(arr.std()),
            "cv": float(arr.std() / arr.mean()) if arr.mean() > 0 else 0,  # coeff of variation
            "empty_buckets": int((arr == 0).sum()),
        }

    def total_sentences(self) -> int:
        return sum(len(b.sentences_l3) for b in self.buckets)


def measure_config(N: int, n_buckets: int, strategy: str) -> dict:
    """Full FULL-corpus recall measurement at one (N, n_buckets, strategy) point."""
    rng = np.random.default_rng(42)
    corpus = generate_corpus(N, rng)
    actual_n = len(corpus)

    t_build_start = time.time()
    memory = HierarchicalVariableLengthMemoryFullCov(D=D, n_buckets=n_buckets, strategy=strategy)
    for tokens in corpus:
        memory.learn_sentence(tokens)
    t_build = time.time() - t_build_start

    # FULL-corpus self-recall (deterministic-bucket routing)
    t_recall_start = time.time()
    correct = sum(1 for tokens in corpus if memory.recall_sentence(tokens))
    t_recall = time.time() - t_recall_start

    stats = memory.bucket_load_stats()
    return {
        "N_target": N,
        "N_actual": actual_n,
        "n_buckets": n_buckets,
        "strategy": strategy,
        "n_correct": correct,
        "self_recall": correct / actual_n,
        "build_seconds": t_build,
        "recall_seconds": t_recall,
        "build_per_sentence_ms": t_build / actual_n * 1000,
        "recall_per_sentence_ms": t_recall / actual_n * 1000,
        **{f"bucket_{k}": v for k, v in stats.items()},
    }


def main():
    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}; D={D}\n")

    # PHASE 1: full strategy × bucket-count × N grid at moderate scale
    n_buckets_sweep = [4, 8, 16, 32, 64, 128, 256]
    n_corpus_sweep = [1000, 4000, 16000]
    strategies = ["hash", "first_bigram_hash"]

    print("=" * 130)
    print(f"PHASE 1: strategy × n_buckets × N full grid (FULL-corpus recall)")
    print("=" * 130)
    print(f"{'strategy':>18} | {'n_buckets':>9} | {'N_actual':>8} | "
          f"{'recall':>6} | {'b_min':>5} | {'b_max':>5} | {'b_mean':>7} | "
          f"{'b_std':>5} | {'b_cv':>5} | {'empty':>5} | {'build_s':>7} | {'recall_s':>8}")
    print("-" * 130)

    phase1_results = []
    for strategy in strategies:
        for N in n_corpus_sweep:
            for nb in n_buckets_sweep:
                # Skip configs where each bucket would have <2 sentences (degenerate)
                if N / nb < 4:
                    continue
                r = measure_config(N, nb, strategy)
                phase1_results.append(r)
                print(
                    f"{r['strategy']:>18} | {r['n_buckets']:>9} | {r['N_actual']:>8} | "
                    f"{r['self_recall']:>6.3f} | {r['bucket_min']:>5} | "
                    f"{r['bucket_max']:>5} | {r['bucket_mean']:>7.1f} | "
                    f"{r['bucket_std']:>5.1f} | {r['bucket_cv']:>5.3f} | "
                    f"{r['bucket_empty_buckets']:>5} | {r['build_seconds']:>7.1f} | "
                    f"{r['recall_seconds']:>8.2f}"
                )

    # PHASE 2: comparison summary of strategies
    print()
    print("=" * 130)
    print("PHASE 2: strategy comparison summary (mean across bucket counts per N)")
    print("=" * 130)

    by_strat_N = defaultdict(list)
    for r in phase1_results:
        by_strat_N[(r["strategy"], r["N_actual"])].append(r)

    print(f"{'strategy':>18} | {'N':>5} | {'mean_recall':>11} | {'mean_build_s':>12} | {'mean_cv':>7} | {'configs':>7}")
    print("-" * 80)
    phase2_summary = {}
    for (strat, N), rs in sorted(by_strat_N.items()):
        m_recall = float(np.mean([r["self_recall"] for r in rs]))
        m_build = float(np.mean([r["build_seconds"] for r in rs]))
        m_cv = float(np.mean([r["bucket_cv"] for r in rs]))
        n_configs = len(rs)
        phase2_summary[f"{strat}_N{N}"] = {
            "mean_recall": m_recall,
            "mean_build_s": m_build,
            "mean_bucket_cv": m_cv,
            "n_configs": n_configs,
        }
        print(f"{strat:>18} | {N:>5} | {m_recall:>11.3f} | {m_build:>12.1f} | {m_cv:>7.3f} | {n_configs:>7}")

    out = {
        "srmech_version": SRMECH_VERSION,
        "D": D,
        "phase1_full_grid": phase1_results,
        "phase2_strategy_comparison": phase2_summary,
    }
    out_path = Path(__file__).parent / "R-RBS-LM-119_results.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
