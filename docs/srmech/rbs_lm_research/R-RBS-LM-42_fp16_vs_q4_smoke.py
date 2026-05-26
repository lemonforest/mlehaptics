"""R-RBS-LM-42 — fp16 vs Q4 controlled comparison at SAME model family + corpus scale.

Tests whether source-side projection-layer quantization (fp16 → Q4) propagates
to cascade read-mode signal degradation. The two TinyLlama-1.1B-Chat-v1.0
distills are the controlled pair:

  - v29 fp16 distill: HF transformers, fp16 weights → 3596 bytes / 442 obs
  - v31 Q4   distill: llama.cpp, Q4_K_M GGUF      → 3560 bytes / 437 obs

Same source family. Same 12 prompts. Same byte-mode encoder. Same D=8192.
Same stride=8. Differs ONLY in projection-layer numeric precision.

Per R-RBS-LM-45: ABSOLUTE similarities are in-noise; load-bearing metric is
RANK ORDER. Run rank-based read-mode statistics on the controlled pair, plus
the existing v29-intermediate fp32 (different chat-tune, same family) and
v31-llama32-1b Q4 (different family, same precision) for context.
"""

import json
import re
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "python"))
sys.path.insert(0, str(HERE))

from rbs_lm_encoder import D  # noqa: E402
from rbs_lm_bytes import compute_byte_vocab_table  # noqa: E402
from rbs_lm_read_mode import (  # noqa: E402
    load_instrument_bytes, phrase_match_retrieval, baseline_random_phrase_sim,
)


def make_phrase_corpus(text, max_phrases=60, min_len=15, max_len=180):
    sentences = re.split(r'[.!?]\s+', text)
    out, seen = [], set()
    for s in sentences:
        s = s.strip().rstrip(".")
        if min_len <= len(s) <= max_len and s not in seen:
            out.append(s)
            seen.add(s)
            if len(out) >= max_phrases:
                break
    return out


def make_probes_from_corpus(text, n_probes=20, seed=42):
    rng = np.random.default_rng(seed)
    sentences = [s.strip() for s in re.split(r'[.!?]\s+', text)
                 if 20 < len(s.strip()) < 200]
    rng.shuffle(sentences)
    probes = []
    for sent in sentences[:n_probes * 2]:
        words = sent.split()
        if len(words) < 5:
            continue
        n_prefix = min(rng.integers(3, 6), len(words) - 1)
        probe = " ".join(words[:n_prefix])
        probes.append((probe, sent))
        if len(probes) >= n_probes:
            break
    return probes


def rank_stats(rank_results, corpus_size):
    n = len(rank_results)
    found = [r for r in rank_results if r >= 0]
    n_found = len(found)
    if not found:
        return {"n_probes": n, "n_found": 0}
    q_t = max(1, corpus_size // 4)
    d_t = max(1, corpus_size // 10)
    rank_1 = sum(1 for r in found if r == 0)
    top_q = sum(1 for r in found if r < q_t)
    top_d = sum(1 for r in found if r < d_t)
    mean_pct = float(np.mean(found)) / max(corpus_size, 1) * 100
    bins = [0] * 5
    bucket = max(corpus_size // 5, 1)
    for r in found:
        bins[min(r // bucket, 4)] += 1
    expected = n_found / 5
    chi2 = sum(((b - expected) ** 2) / expected for b in bins)
    p_est = ("<0.01" if chi2 > 13.28 else "<0.05" if chi2 > 9.49 else
             "<0.10" if chi2 > 7.78 else ">0.10")
    return {
        "n_probes": n, "n_found": n_found,
        "rank_1_count": rank_1, "rank_1_rate": rank_1 / n,
        "top_quartile_count": top_q, "top_quartile_rate": top_q / n,
        "top_decile_count": top_d, "top_decile_rate": top_d / n,
        "mean_rank_percentile": round(mean_pct, 1),
        "chi2_5bins": round(chi2, 2), "p_estimate": p_est,
        "rank_bins": bins, "rank_array": list(rank_results),
    }


def run_one(label, instrument_path, corpus_path, vocab_table):
    if not Path(instrument_path).exists():
        return None
    text = Path(corpus_path).read_text()
    corpus = make_phrase_corpus(text, max_phrases=50)
    probes = make_probes_from_corpus(text, n_probes=20)

    print(f"\n{'='*72}")
    print(f"=== {label}")
    print(f"=== corpus={len(corpus)}, probes={len(probes)}")
    print(f"{'='*72}")

    instrument = load_instrument_bytes(instrument_path)
    baseline = baseline_random_phrase_sim(corpus, vocab_table, D, n_samples=200)
    print(f"  Baseline: mean={baseline['mean']:+.4f}, std={baseline['std']:.4f}, "
          f"max={baseline['max']:+.4f}")

    rank_results = []
    for query, expected in probes:
        ranked = phrase_match_retrieval(instrument, query, corpus, vocab_table, D)
        try:
            rank = next(i for i, (phr, _) in enumerate(ranked) if phr == expected)
        except StopIteration:
            try:
                rank = next(i for i, (phr, _) in enumerate(ranked)
                            if expected[:30] in phr or phr in expected)
            except StopIteration:
                rank = -1
        rank_results.append(rank)

    stats = rank_stats(rank_results, len(corpus))
    print(f"  rank-1:        {stats['rank_1_count']}/{stats['n_probes']} "
          f"({100*stats['rank_1_rate']:.1f}%)")
    print(f"  top-decile:    {stats['top_decile_count']}/{stats['n_probes']} "
          f"({100*stats['top_decile_rate']:.1f}%)")
    print(f"  top-quartile:  {stats['top_quartile_count']}/{stats['n_probes']} "
          f"({100*stats['top_quartile_rate']:.1f}%)")
    print(f"  mean percentile: {stats['mean_rank_percentile']:.1f}%  (chance=50%)")
    print(f"  chi-square: {stats['chi2_5bins']}, p-estimate: {stats['p_estimate']}")
    print(f"  rank bins: {stats['rank_bins']}")
    return {
        "label": label, "instrument": instrument_path,
        "corpus_size": len(corpus), "n_probes": len(probes),
        "baseline": baseline, "stats": stats,
    }


def main():
    vocab_table = compute_byte_vocab_table(D)

    pairs = [
        # Controlled fp16 vs Q4: SAME source family + corpus scale
        ("v29 Chat fp16 (1.1B; 442 obs from 3596 bytes)",
         "docs/srmech/rbs_lm_research/rbs_lm_instrument_v29_distill_TinyLlama__TinyLlama-1.1B-Chat-v1.0.bin",
         "docs/srmech/rbs_lm_research/rbs_lm_instrument_v29_distill_TinyLlama__TinyLlama-1.1B-Chat-v1.0.corpus.txt"),
        ("v31 Chat Q4   (1.1B; 437 obs from 3560 bytes)",
         "docs/srmech/rbs_lm_research/rbs_lm_instrument_v31_gguf_tinyllama-chat-q4.bin",
         "docs/srmech/rbs_lm_research/rbs_lm_instrument_v31_gguf_tinyllama-chat-q4.corpus.txt"),
        # Context: same-precision other chat-tune
        ("v29 intermediate fp32 (1.1B; 443 obs from 3.5k bytes)",
         "docs/srmech/rbs_lm_research/rbs_lm_instrument_v29_distill_TinyLlama__TinyLlama-1.1B-intermediate-step-1431k-3T.bin",
         "docs/srmech/rbs_lm_research/rbs_lm_instrument_v29_distill_TinyLlama__TinyLlama-1.1B-intermediate-step-1431k-3T.corpus.txt"),
        # Context: different family, same Q4 precision
        ("v31 Llama-3.2-1B Q4 (different family; 448 obs from 3.6k)",
         "docs/srmech/rbs_lm_research/rbs_lm_instrument_v31_gguf_llama32-1b-q4.bin",
         "docs/srmech/rbs_lm_research/rbs_lm_instrument_v31_gguf_llama32-1b-q4.corpus.txt"),
    ]

    print(f"=== R-RBS-LM-42 fp16-vs-Q4 controlled comparison ===")
    print(f"=== Same source family (TinyLlama-1.1B-Chat); same byte-encoder; same D=8192 ===\n")

    results = {}
    for label, ipath, cpath in pairs:
        r = run_one(label, ipath, cpath, vocab_table)
        if r is not None:
            results[label] = r

    # ---- Summary -----------------------------------------------------
    print(f"\n\n{'='*72}")
    print(f"=== R-RBS-LM-42 SUMMARY: fp16 vs Q4 controlled axis")
    print(f"{'='*72}\n")
    print(f"  {'instrument':<58s} {'rank-1%':>8s} {'top-d%':>7s} {'top-q%':>7s} "
          f"{'mean%':>7s} {'p-est':>7s}")
    print(f"  {'-'*58} {'-'*8} {'-'*7} {'-'*7} {'-'*7} {'-'*7}")
    for label, r in results.items():
        s = r["stats"]
        print(f"  {label[:58]:<58s} {100*s['rank_1_rate']:>7.1f}% "
              f"{100*s['top_decile_rate']:>6.1f}% {100*s['top_quartile_rate']:>6.1f}% "
              f"{s.get('mean_rank_percentile', 50.0):>6.1f}% "
              f"{s.get('p_estimate', '?'):>7s}")

    out_path = Path("docs/srmech/rbs_lm_research/R-RBS-LM-42_fp16_vs_q4_results.json")
    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"\nResults: {out_path}")

    # Falsification reading
    print(f"\n=== Falsification reading ===")
    chat_fp16 = results.get("v29 Chat fp16 (1.1B; 442 obs from 3596 bytes)")
    chat_q4 = results.get("v31 Chat Q4   (1.1B; 437 obs from 3560 bytes)")
    if chat_fp16 and chat_q4:
        m_fp16 = chat_fp16["stats"]["mean_rank_percentile"]
        m_q4 = chat_q4["stats"]["mean_rank_percentile"]
        delta = m_q4 - m_fp16
        print(f"  Controlled (chat fp16 vs Q4): mean percentile {m_fp16:.1f}% vs {m_q4:.1f}%")
        print(f"  Δ = {delta:+.1f}pp (positive = Q4 worse than fp16)")
        if abs(delta) < 3.0:
            print(f"  → Quantization tax is MINOR at this corpus scale (<3pp).")
            print(f"  → Source-side numeric precision does NOT propagate strongly into")
            print(f"    cascade read-mode at byte-mode + 3.5k-byte scale.")
        elif delta > 5.0:
            print(f"  → Quantization tax is MATERIAL (>5pp degradation).")
            print(f"  → fp16 → Q4 source-side precision loss DOES propagate to cascade")
            print(f"    read-mode signal. Use fp16 for read-mode if accuracy matters.")
        else:
            print(f"  → Quantization tax is BORDERLINE (3-5pp). More probes / corpora")
            print(f"    needed to localize.")


if __name__ == "__main__":
    main()
