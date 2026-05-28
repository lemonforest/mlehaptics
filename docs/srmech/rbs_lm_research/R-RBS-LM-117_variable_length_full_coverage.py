"""R-RBS-LM-117 — Variable-length L=1..30 full coverage extension

Extends R-RBS-LM-112's L=4..7 demo to full L=1..30 coverage:
  - L=1   edge case (must fail — substrate needs ≥2 tokens)
  - L=2   minimum (single bigram; no skeleton storage)
  - L=3   no skeleton (substrate code gates skeleton at L≥4)
  - L=4..7    R-RBS-LM-112 baseline (already validated)
  - L=8..15   extended length (untested in original)
  - L=20..30  stress test for substrate length-independence

Per [[feedback_no_mvp_framing]] + [[feedback_full_coverage_shipping_mpm_way]]:
documents the substrate's actual length range, not just the 4..7 demo range.

Measures per length:
  - self-recall on encoded sentences
  - build time per sentence
  - retrieval time per sentence
  - skeleton storage count (informational; ≥4 only)
  - generation diversity (where applicable)
"""
import json
import time
from collections import defaultdict
from pathlib import Path
import importlib.util
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
_spec = importlib.util.spec_from_file_location(
    "vl_memory", Path(__file__).parent / "R-RBS-LM-112_variable_length_sentences.py"
)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["vl_memory"] = _mod
_spec.loader.exec_module(_mod)
VariableLengthSentenceMemory = _mod.VariableLengthSentenceMemory
encode_sentence_l3 = _mod.encode_sentence_l3
sim_k4_batch = _mod.sim_k4_batch

_spec_c = importlib.util.spec_from_file_location(
    "corpus_gen", Path(__file__).parent / "R-RBS-LM-113_larger_corpus_scaling.py"
)
_mod_c = importlib.util.module_from_spec(_spec_c)
sys.modules["corpus_gen"] = _mod_c
_spec_c.loader.exec_module(_mod_c)

from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION


D = 8192


# Build a vocabulary pool from corpus_gen
ALL_WORDS = list(set(
    _mod_c.SUBJECTS_DET_THE
    + _mod_c.SUBJECTS_DET_A
    + _mod_c.VERBS_TRANSITIVE_4w
    + _mod_c.OBJECTS
    + _mod_c.PREPOSITIONS
    + _mod_c.DETERMINERS
    + _mod_c.ADJECTIVES
))


def gen_sentences_of_length(L: int, n: int, rng) -> list[list[str]]:
    """Generate n sentences of exactly length L using random vocab from corpus_gen pool.

    Substrate is structure-agnostic — it learns whatever bigram chains we give it.
    We use random sampling here to test length-independence of the substrate,
    not grammar (grammar is tested in R-RBS-LM-115/120).
    """
    out = []
    seen = set()
    attempts = 0
    while len(out) < n and attempts < n * 10:
        attempts += 1
        tokens = list(rng.choice(ALL_WORDS, size=L, replace=True))
        key = tuple(tokens)
        if key not in seen:
            seen.add(key)
            out.append(tokens)
    return out


def measure_length(L: int, n_sentences: int, rng) -> dict:
    """Measure substrate behaviour at fixed length L."""
    corpus = gen_sentences_of_length(L, n_sentences, rng)
    if not corpus:
        return {"L": L, "n_sentences": 0, "error": "could not generate corpus"}

    memory = VariableLengthSentenceMemory(D=D)
    t_build_start = time.time()
    for tokens in corpus:
        try:
            memory.learn_sentence(tokens)
        except Exception as e:
            return {"L": L, "n_sentences": len(corpus), "error": str(e)}
    t_build = time.time() - t_build_start

    if not memory.sentences_l3:
        return {
            "L": L,
            "n_sentences": len(corpus),
            "n_stored_l3": 0,
            "self_recall": 0.0,
            "build_seconds": t_build,
            "note": "no sentences stored (L<2 edge case or all-empty)",
        }

    # Self-recall — full-corpus, not sampled
    t_recall_start = time.time()
    sentences_matrix = np.stack(list(memory.sentences_l3.values()))
    sentence_keys = list(memory.sentences_l3.keys())
    correct = 0
    for tokens in corpus:
        target = encode_sentence_l3(tokens)
        sims = sim_k4_batch(target, sentences_matrix)
        if sentence_keys[int(sims.argmax())] == tuple(tokens):
            correct += 1
    t_recall = time.time() - t_recall_start

    return {
        "L": L,
        "n_sentences": len(corpus),
        "n_stored_words": len(memory.words_l0),
        "n_stored_bigrams": len(memory.bigrams_l1),
        "n_stored_skeletons": len(memory.skeletons_l2),
        "n_stored_l3": len(memory.sentences_l3),
        "self_recall": correct / len(corpus),
        "n_correct": correct,
        "build_seconds": t_build,
        "recall_seconds": t_recall,
        "per_sentence_build_ms": t_build / len(corpus) * 1000,
        "per_sentence_recall_ms": t_recall / len(corpus) * 1000,
    }


def main():
    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}; D={D}")
    print(f"Vocabulary pool: {len(ALL_WORDS)} words\n")

    # L=1 edge case: substrate gates at L≥2 — we expect no storage
    print("=" * 100)
    print("EDGE CASE: L=1 (must fail — substrate requires ≥2 tokens)")
    print("=" * 100)
    rng = np.random.default_rng(42)
    memory_l1 = VariableLengthSentenceMemory(D=D)
    single_tokens = [["word"], ["test"], ["edge"]]
    for tokens in single_tokens:
        memory_l1.learn_sentence(tokens)
    print(f"  Attempted to store {len(single_tokens)} L=1 'sentences'")
    print(f"  n_stored_l3: {len(memory_l1.sentences_l3)} (expected 0 — confirms L<2 gating)")
    l1_correctly_rejected = len(memory_l1.sentences_l3) == 0
    print(f"  L=1 correctly rejected: {l1_correctly_rejected}")
    print()

    # Full sweep L=2..30 with denser packing at lower L (since they're cheaper)
    length_sweep = [2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 18, 20, 25, 30]
    n_per_length = 50  # fixed n per length for apples-to-apples comparison

    print("=" * 100)
    print(f"FULL SWEEP: L=2..30 with {n_per_length} sentences each")
    print("=" * 100)
    print(f"{'L':>3} | {'n_sent':>6} | {'n_words':>7} | {'n_bigrams':>9} | {'n_skel':>6} | "
          f"{'n_l3':>5} | {'recall':>7} | {'build_s':>8} | {'recall_s':>9} | {'b/s_ms':>7} | {'r/s_ms':>7}")
    print("-" * 110)

    results = []
    for L in length_sweep:
        rng = np.random.default_rng(42 + L)
        r = measure_length(L, n_per_length, rng)
        results.append(r)
        if "error" in r:
            print(f"{L:>3} | ERROR: {r['error']}")
        elif r["n_stored_l3"] == 0:
            print(f"{L:>3} | {r['n_sentences']:>6} | (nothing stored: {r.get('note', '')})")
        else:
            print(
                f"{r['L']:>3} | {r['n_sentences']:>6} | "
                f"{r['n_stored_words']:>7} | {r['n_stored_bigrams']:>9} | "
                f"{r['n_stored_skeletons']:>6} | {r['n_stored_l3']:>5} | "
                f"{r['self_recall']:>7.3f} | {r['build_seconds']:>8.2f} | "
                f"{r['recall_seconds']:>9.2f} | {r['per_sentence_build_ms']:>7.2f} | "
                f"{r['per_sentence_recall_ms']:>7.2f}"
            )

    # Mixed-length corpus test (the original R-RBS-LM-112 use case)
    print()
    print("=" * 100)
    print("MIXED-LENGTH STRESS: 200 sentences spanning L=4..15")
    print("=" * 100)
    rng = np.random.default_rng(99)
    mixed_corpus = []
    for L in range(4, 16):
        mixed_corpus.extend(gen_sentences_of_length(L, n=20, rng=rng))
    print(f"Mixed corpus: {len(mixed_corpus)} sentences, lengths: "
          f"{sorted(set(len(s) for s in mixed_corpus))}")
    memory_mixed = VariableLengthSentenceMemory(D=D)
    for tokens in mixed_corpus:
        memory_mixed.learn_sentence(tokens)
    sentences_matrix = np.stack(list(memory_mixed.sentences_l3.values()))
    sentence_keys = list(memory_mixed.sentences_l3.keys())
    # Per-length breakdown of mixed recall
    by_L_correct = defaultdict(int)
    by_L_total = defaultdict(int)
    for tokens in mixed_corpus:
        L = len(tokens)
        by_L_total[L] += 1
        target = encode_sentence_l3(tokens)
        sims = sim_k4_batch(target, sentences_matrix)
        if sentence_keys[int(sims.argmax())] == tuple(tokens):
            by_L_correct[L] += 1
    print(f"  {'L':>3} | {'correct':>7} | {'total':>5} | {'recall':>7}")
    print(f"  {'-'*3} | {'-'*7} | {'-'*5} | {'-'*7}")
    mixed_breakdown = {}
    for L in sorted(by_L_total):
        rec = by_L_correct[L] / by_L_total[L]
        print(f"  {L:>3} | {by_L_correct[L]:>7} | {by_L_total[L]:>5} | {rec:>7.3f}")
        mixed_breakdown[L] = {"correct": by_L_correct[L], "total": by_L_total[L], "recall": rec}
    overall_mixed = sum(by_L_correct.values()) / sum(by_L_total.values())
    print(f"  Overall mixed self-recall: {overall_mixed:.3f}")

    out = {
        "srmech_version": SRMECH_VERSION,
        "D": D,
        "vocabulary_pool_size": len(ALL_WORDS),
        "L1_edge_case_correctly_rejected": l1_correctly_rejected,
        "per_length_sweep": results,
        "mixed_length_overall_recall": overall_mixed,
        "mixed_length_per_L_breakdown": mixed_breakdown,
    }
    out_path = Path(__file__).parent / "R-RBS-LM-117_results.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
