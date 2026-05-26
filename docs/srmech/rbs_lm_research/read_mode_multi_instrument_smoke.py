"""R-RBS-LM-45 — Multi-instrument read-mode smoke.

Tests phrase-match retrieval + recognition score across 4 byte-mode instruments
(v25b GPT-2 / v29 TinyLlama / v31 Llama-3.2 1B Q4 / v35 Llama-3.1 8B Q4 /
v33 3-source merged / v44 turtle-walk). For each instrument:

  1. Build phrase corpus from its training data (corpus.txt or pair file)
  2. Run phrase_match_retrieval for a fixed set of probes
  3. Measure expected-rank distribution + recognition score vs baseline

If ANY instrument shows read-mode signal (expected ranks << random; recognition
sim >> baseline), Branch A is partially supported. If ALL fail, write-mode
mode-collapse reflects substrate-bound state across the entire byte-mode
family.
"""

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "python"))
sys.path.insert(0, str(HERE))

from rbs_lm_encoder import D  # noqa: E402
from rbs_lm_bytes import compute_byte_vocab_table  # noqa: E402
from rbs_lm_read_mode import (  # noqa: E402
    load_instrument_bytes, phrase_match_retrieval, recognition_score,
    baseline_random_phrase_sim, top_k_distribution, distribution_stats,
)


def make_phrase_corpus_from_text(corpus_text, max_phrases=50, min_len=20, max_len=200):
    """Extract candidate phrases from a corpus.txt file. Splits on sentence
    boundaries; filters by length; deduplicates."""
    import re
    sentences = re.split(r'[.!?]\s+', corpus_text)
    phrases = []
    seen = set()
    for s in sentences:
        s = s.strip()
        if min_len <= len(s) <= max_len and s not in seen:
            phrases.append(s)
            seen.add(s)
            if len(phrases) >= max_phrases:
                break
    return phrases


def run_instrument(label, instrument_path, phrase_corpus, probes, vocab_table, D=D):
    print(f"\n{'='*72}")
    print(f"=== {label}")
    print(f"=== {instrument_path}")
    print(f"=== phrase corpus: {len(phrase_corpus)} candidates")
    print(f"{'='*72}")

    if not Path(instrument_path).exists():
        print(f"  SKIP — not found")
        return None

    instrument = load_instrument_bytes(instrument_path)

    # Baseline
    baseline = baseline_random_phrase_sim(phrase_corpus, vocab_table, D, n_samples=100)
    print(f"  Baseline (random pairwise sim across phrase corpus):")
    print(f"    mean={baseline['mean']:+.4f}, std={baseline['std']:.4f}, "
          f"max={baseline['max']:+.4f}")

    # Probes: top-1 sim and rank of best phrase
    n_probes = len(probes)
    rank_results = []
    top1_sims = []
    print(f"\n  Phrase-match for {n_probes} probes:")
    for query, expected in probes:
        ranked = phrase_match_retrieval(instrument, query, phrase_corpus, vocab_table, D)
        top1_sims.append(ranked[0][1])
        # Find rank of expected (if specified)
        if expected is not None:
            try:
                rank = next(idx for idx, (phr, _) in enumerate(ranked) if expected in phr)
            except StopIteration:
                rank = -1
            rank_results.append(rank)
            top3_label = ranked[0][0][:40]
            print(f"    query: {query[:30]!r:35s} expected: {expected[:30]!r:35s} "
                  f"rank: {rank if rank >= 0 else 'not-found'}/{len(phrase_corpus)} "
                  f"top1: {top3_label}")
        else:
            top3_label = ranked[0][0][:40]
            print(f"    query: {query[:30]!r:35s} top1: {top3_label!r}")

    # Top-k stats summary
    top_k_stats = []
    for query, _ in probes[:3]:
        tk = top_k_distribution(instrument, query, vocab_table, D, k=20)
        top_k_stats.append(distribution_stats(tk))

    # Aggregate
    if rank_results:
        avg_rank = sum(rank_results) / len(rank_results)
        avg_rank_pct = 100 * avg_rank / max(len(phrase_corpus), 1)
        # Chance is at len(corpus)/2 expected if random
        n_signal = sum(1 for r in rank_results if 0 <= r < len(phrase_corpus) / 4)
        print(f"\n  Aggregate:")
        print(f"    avg rank: {avg_rank:.1f}/{len(phrase_corpus)} ({avg_rank_pct:.0f}%)")
        print(f"    (chance would be ~{len(phrase_corpus)//2}; lower-is-better)")
        print(f"    n probes with expected in top-quartile: "
              f"{n_signal}/{len(rank_results)}")

    avg_top1 = float(np.mean(top1_sims))
    print(f"    avg top-1 sim: {avg_top1:+.4f} "
          f"(vs baseline {baseline['mean']:+.4f}; "
          f"{'SIGNAL' if avg_top1 > baseline['mean'] + 2 * baseline['std'] else 'no signal'})")

    return {
        "label": label,
        "instrument": instrument_path,
        "baseline_mean": baseline["mean"],
        "baseline_std": baseline["std"],
        "n_probes": n_probes,
        "avg_top1_sim": avg_top1,
        "rank_results": rank_results,
        "n_corpus": len(phrase_corpus),
        "top_k_stats": top_k_stats,
    }


def main():
    vocab_table = compute_byte_vocab_table(D)
    all_results = {}

    # --- v44 turtle-walk (clean test; small known mapping) ---
    print(f"\n###  PART 1: v44 turtle-walk (51-pair English↔LOGO)")
    corpus_v44 = json.load(open("docs/srmech/rbs_lm_research/turtle_walk_corpus.json"))
    v44_phrases = list(set(p["logo"] for p in corpus_v44["pairs"]))
    v44_probes = [(p["english"], p["logo"]) for p in corpus_v44["pairs"][:10]]
    all_results["v44"] = run_instrument(
        "v44 turtle-walk (51 pairs)",
        "docs/srmech/rbs_lm_research/rbs_lm_instrument_v44_turtle_walk.bin",
        v44_phrases, v44_probes, vocab_table, D,
    )

    # --- v25b GPT-2 byte-mode (10k bytes; ~647 obs) ---
    print(f"\n###  PART 2: v25b GPT-2 byte-mode")
    corpus_path = "docs/srmech/rbs_lm_research/rbs_lm_instrument_v25b_distill_gpt2.corpus.txt"
    if Path(corpus_path).exists():
        v25b_phrases = make_phrase_corpus_from_text(Path(corpus_path).read_text(), max_phrases=50)
        # Probes: prompts that should retrieve something semantically near
        v25b_probes = [
            ("The history of computing", "computing"),
            ("Photosynthesis converts", "photosynth"),
            ("The morning sun cast",     "morning"),
            ("Algorithms for sorting",   "sorting"),
            ("Once upon a time",         "time"),
        ]
        all_results["v25b"] = run_instrument(
            "v25b GPT-2 byte (647 obs from 10k bytes)",
            "docs/srmech/rbs_lm_research/rbs_lm_instrument_v25b_distill_gpt2.bin",
            v25b_phrases, v25b_probes, vocab_table, D,
        )

    # --- v35 Llama 8B Q4 ---
    print(f"\n###  PART 3: v35 Llama-3.1-8B Q4")
    corpus_path = "docs/srmech/rbs_lm_research/rbs_lm_instrument_v31_gguf_llama31-8b-q4.corpus.txt"
    if Path(corpus_path).exists():
        v35_phrases = make_phrase_corpus_from_text(Path(corpus_path).read_text(), max_phrases=50)
        v35_probes = [
            ("The history of computing", "computing"),
            ("Algorithms for sorting",   "algorithm"),
            ("def fibonacci(n):",        "fibonacci"),
            ("The chef tasted the soup", "chef"),
            ("Public-key cryptography",  "crypto"),
        ]
        all_results["v35"] = run_instrument(
            "v35 Llama-3.1-8B Q4 (1317 obs from 10k bytes)",
            "docs/srmech/rbs_lm_research/rbs_lm_instrument_v31_gguf_llama31-8b-q4.bin",
            v35_phrases, v35_probes, vocab_table, D,
        )

    # --- v33 3-source merged ---
    print(f"\n###  PART 4: v33 3-source merged")
    # Use union of v25b + v31 corpora for the phrase corpus
    corpus_v25b = Path("docs/srmech/rbs_lm_research/rbs_lm_instrument_v25b_distill_gpt2.corpus.txt")
    corpus_v31 = Path("docs/srmech/rbs_lm_research/rbs_lm_instrument_v31_gguf_llama32-1b-q4.corpus.txt")
    if corpus_v25b.exists():
        text = corpus_v25b.read_text()
        if corpus_v31.exists():
            text += "\n\n" + corpus_v31.read_text()
        v33_phrases = make_phrase_corpus_from_text(text, max_phrases=50)
        v33_probes = [
            ("The morning sun cast",  "morning"),
            ("def fibonacci(n):",     "fibonacci"),
            ("Algorithms for sorting","sorting"),
            ("I beat the eggs",       "eggs"),
            ("Once upon a time",      "time"),
        ]
        all_results["v33"] = run_instrument(
            "v33 3-source merged",
            "docs/srmech/rbs_lm_research/rbs_lm_instrument_v33_merged_3source.bin",
            v33_phrases, v33_probes, vocab_table, D,
        )

    # ===== Final summary =====
    print(f"\n\n{'='*72}")
    print(f"=== FINAL SUMMARY")
    print(f"{'='*72}\n")
    print(f"  {'instrument':<35s}  {'baseline_mean':>13s}  {'avg_top1_sim':>13s}  {'signal?':>10s}")
    print(f"  {'-'*35}  {'-'*13}  {'-'*13}  {'-'*10}")
    for key, r in all_results.items():
        if r is None:
            continue
        signal = (r["avg_top1_sim"] > r["baseline_mean"] + 2 * r["baseline_std"])
        label = r["label"][:35]
        print(f"  {label:<35s}  {r['baseline_mean']:>+13.4f}  {r['avg_top1_sim']:>+13.4f}  {'YES' if signal else 'no':>10s}")

    out_path = Path("docs/srmech/rbs_lm_research/read_mode_multi_instrument_results.json")
    out_path.write_text(json.dumps(all_results, indent=2, ensure_ascii=False))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
