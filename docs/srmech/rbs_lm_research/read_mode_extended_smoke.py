"""R-RBS-LM-45 extended — Read-mode rank-distribution smoke across 7 instruments + 20+ probes each.

Per user direction 2026-05-26: "read mode against multiple and let the math
talk to us." The R-RBS-LM-45 first smoke ran 5 probes × 4 instruments — small
N. This extended smoke runs ALL byte-mode instruments (7 total) with 15-20
probes each, captures full rank distributions, and computes:

  - Rank-1 hit rate (probe whose expected answer is the literal top match)
  - Top-quartile hit rate (expected in top 25% of corpus)
  - Top-decile hit rate (expected in top 10%)
  - Chi-square goodness-of-fit vs uniform (null: cascade rank dist is random)
  - Average rank percentile

Discipline: absolute similarities are in-noise across all instruments (per
R-RBS-LM-45 §4.1); load-bearing metric is rank order. Report rank-based
statistics + raw rank arrays per instrument so the math itself surfaces what
the cascade does.
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
    load_instrument_bytes, phrase_match_retrieval,
    baseline_random_phrase_sim,
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


def make_probes_from_corpus(text, n_probes=20, min_len=10, max_len=80, seed=42):
    """Extract probe queries from the corpus — short fragments that should
    retrieve content semantically near. Use the FIRST few words of various
    sentences as probes."""
    rng = np.random.default_rng(seed)
    sentences = [s.strip() for s in re.split(r'[.!?]\s+', text) if 20 < len(s.strip()) < 200]
    if not sentences:
        return []
    probes = []
    # Use first ~5 words of each candidate sentence as probe; expected = the rest
    candidates = sentences.copy()
    rng.shuffle(candidates)
    for sent in candidates[:n_probes * 2]:
        words = sent.split()
        if len(words) < 5:
            continue
        n_prefix = min(rng.integers(3, 6), len(words) - 1)
        probe = " ".join(words[:n_prefix])
        expected = " ".join(words[:n_prefix + 5])  # what we'd expect a retrieval to return as close
        if min_len <= len(probe) <= max_len:
            probes.append((probe, sent))  # match against the full sentence
        if len(probes) >= n_probes:
            break
    return probes


def rank_stats(rank_results, corpus_size):
    """Compute rank-based statistics. rank_results is a list of ranks (0-indexed)
    or -1 if not-found. Returns dict with:
      - n_probes, n_found
      - rank_1_count: count of probes where expected was top match
      - top_quartile_count: count of probes where expected was in top 25%
      - top_decile_count: count of probes where expected was in top 10%
      - mean_rank_percentile: average rank as % of corpus size
      - chi2_vs_uniform_p: rough chi-square p-value for "is rank dist uniform"
    """
    n = len(rank_results)
    found = [r for r in rank_results if r >= 0]
    n_found = len(found)
    if not found:
        return {
            "n_probes": n, "n_found": 0,
            "rank_1_count": 0, "rank_1_rate": 0.0,
            "top_quartile_count": 0, "top_quartile_rate": 0.0,
            "top_decile_count": 0, "top_decile_rate": 0.0,
            "mean_rank_percentile": None,
            "rank_array": list(rank_results),
        }

    q_threshold = max(1, corpus_size // 4)
    d_threshold = max(1, corpus_size // 10)
    rank_1 = sum(1 for r in found if r == 0)
    top_q = sum(1 for r in found if r < q_threshold)
    top_d = sum(1 for r in found if r < d_threshold)
    mean_pct = float(np.mean(found)) / max(corpus_size, 1) * 100

    # Chi-square vs uniform: bin ranks into 5 buckets; expected count per bucket = n/5
    # If cascade is uniform, all buckets get ~n/5
    bins = [0] * 5
    bucket_size = max(corpus_size // 5, 1)
    for r in found:
        b = min(r // bucket_size, 4)
        bins[b] += 1
    expected_per_bin = n_found / 5
    chi2 = sum(((b - expected_per_bin) ** 2) / expected_per_bin for b in bins)
    # df=4; rough p-value lookup:
    # chi2 < 7.78: p > 0.10 (no signal)
    # chi2 7.78-9.49: 0.05 < p < 0.10
    # chi2 9.49-13.28: 0.01 < p < 0.05 (signal)
    # chi2 > 13.28: p < 0.01 (strong signal)
    if chi2 > 13.28:
        p_estimate = "<0.01"
    elif chi2 > 9.49:
        p_estimate = "<0.05"
    elif chi2 > 7.78:
        p_estimate = "<0.10"
    else:
        p_estimate = ">0.10"

    return {
        "n_probes": n,
        "n_found": n_found,
        "rank_1_count": rank_1,
        "rank_1_rate": rank_1 / n,
        "top_quartile_count": top_q,
        "top_quartile_rate": top_q / n,
        "top_decile_count": top_d,
        "top_decile_rate": top_d / n,
        "mean_rank_percentile": round(mean_pct, 1),
        "chi2_5bins": round(chi2, 2),
        "p_estimate": p_estimate,
        "rank_bins": bins,
        "rank_array": list(rank_results),
    }


def run_one(label, instrument_path, phrase_corpus, probes, vocab_table, D=D):
    if not Path(instrument_path).exists():
        return None
    print(f"\n{'='*72}")
    print(f"=== {label}")
    print(f"=== corpus={len(phrase_corpus)}, probes={len(probes)}")
    print(f"{'='*72}")

    instrument = load_instrument_bytes(instrument_path)
    baseline = baseline_random_phrase_sim(phrase_corpus, vocab_table, D, n_samples=200)
    print(f"  Baseline rand-pair sim: mean={baseline['mean']:+.4f}, "
          f"std={baseline['std']:.4f}, max={baseline['max']:+.4f}")

    rank_results = []
    for query, expected in probes:
        ranked = phrase_match_retrieval(instrument, query, phrase_corpus, vocab_table, D)
        # rank by exact match first, then by containment
        try:
            rank = next(idx for idx, (phr, _) in enumerate(ranked) if phr == expected)
        except StopIteration:
            try:
                rank = next(idx for idx, (phr, _) in enumerate(ranked)
                             if expected[:30] in phr or phr in expected)
            except StopIteration:
                rank = -1
        rank_results.append(rank)

    stats = rank_stats(rank_results, len(phrase_corpus))
    print(f"  Rank statistics:")
    print(f"    n_probes={stats['n_probes']}; n_found={stats['n_found']}")
    print(f"    rank-1 hits:        {stats['rank_1_count']}/{stats['n_probes']} ({100*stats['rank_1_rate']:.1f}%)")
    print(f"    top-decile hits:    {stats['top_decile_count']}/{stats['n_probes']} ({100*stats['top_decile_rate']:.1f}%)")
    print(f"    top-quartile hits:  {stats['top_quartile_count']}/{stats['n_probes']} ({100*stats['top_quartile_rate']:.1f}%)")
    if stats['mean_rank_percentile'] is not None:
        print(f"    mean rank percentile: {stats['mean_rank_percentile']:.1f}%  (chance=50%)")
    print(f"    chi-square (5 bins): {stats.get('chi2_5bins', 'n/a')}; "
          f"p-estimate: {stats.get('p_estimate', 'n/a')}")
    print(f"    rank bucket distribution: {stats.get('rank_bins', [])}")

    return {
        "label": label,
        "instrument": instrument_path,
        "corpus_size": len(phrase_corpus),
        "n_probes": len(probes),
        "baseline": baseline,
        "stats": stats,
    }


def main():
    vocab_table = compute_byte_vocab_table(D)

    instruments_to_test = []

    # 1. v25b GPT-2 byte
    p = "docs/srmech/rbs_lm_research/rbs_lm_instrument_v25b_distill_gpt2.bin"
    c = "docs/srmech/rbs_lm_research/rbs_lm_instrument_v25b_distill_gpt2.corpus.txt"
    if Path(c).exists():
        text = Path(c).read_text()
        instruments_to_test.append((
            "v25b GPT-2 byte (124M; 647 obs from 10k bytes)", p,
            make_phrase_corpus(text, max_phrases=50),
            make_probes_from_corpus(text, n_probes=20),
        ))

    # 2. v29 TinyLlama 1.1B fp32
    p = "docs/srmech/rbs_lm_research/rbs_lm_instrument_v29_distill_TinyLlama__TinyLlama-1.1B-intermediate-step-1431k-3T.bin"
    c = "docs/srmech/rbs_lm_research/rbs_lm_instrument_v29_distill_TinyLlama__TinyLlama-1.1B-intermediate-step-1431k-3T.corpus.txt"
    if Path(c).exists():
        text = Path(c).read_text()
        instruments_to_test.append((
            "v29 TinyLlama 1.1B fp32 (443 obs from 3.5k bytes)", p,
            make_phrase_corpus(text, max_phrases=50),
            make_probes_from_corpus(text, n_probes=20),
        ))

    # 3. v31 Llama-3.2-1B Q4 GGUF
    p = "docs/srmech/rbs_lm_research/rbs_lm_instrument_v31_gguf_llama32-1b-q4.bin"
    c = "docs/srmech/rbs_lm_research/rbs_lm_instrument_v31_gguf_llama32-1b-q4.corpus.txt"
    if Path(c).exists():
        text = Path(c).read_text()
        instruments_to_test.append((
            "v31 Llama-3.2-1B Q4 GGUF (448 obs from 3.6k bytes)", p,
            make_phrase_corpus(text, max_phrases=50),
            make_probes_from_corpus(text, n_probes=20),
        ))

    # 4. v35 Llama-3.1-8B Q4 GGUF
    p = "docs/srmech/rbs_lm_research/rbs_lm_instrument_v31_gguf_llama31-8b-q4.bin"
    c = "docs/srmech/rbs_lm_research/rbs_lm_instrument_v31_gguf_llama31-8b-q4.corpus.txt"
    if Path(c).exists():
        text = Path(c).read_text()
        instruments_to_test.append((
            "v35 Llama-3.1-8B Q4 GGUF (1317 obs from 10k bytes)", p,
            make_phrase_corpus(text, max_phrases=50),
            make_probes_from_corpus(text, n_probes=20),
        ))

    # 5. v33 3-source merged (use union of v25b + v29 + v31 corpora)
    p = "docs/srmech/rbs_lm_research/rbs_lm_instrument_v33_merged_3source.bin"
    c1 = Path("docs/srmech/rbs_lm_research/rbs_lm_instrument_v25b_distill_gpt2.corpus.txt")
    c2 = Path("docs/srmech/rbs_lm_research/rbs_lm_instrument_v29_distill_TinyLlama__TinyLlama-1.1B-intermediate-step-1431k-3T.corpus.txt")
    c3 = Path("docs/srmech/rbs_lm_research/rbs_lm_instrument_v31_gguf_llama32-1b-q4.corpus.txt")
    if Path(p).exists() and c1.exists():
        text = c1.read_text()
        if c2.exists():
            text += "\n\n" + c2.read_text()
        if c3.exists():
            text += "\n\n" + c3.read_text()
        instruments_to_test.append((
            "v33 3-source merged", p,
            make_phrase_corpus(text, max_phrases=50),
            make_probes_from_corpus(text, n_probes=20),
        ))

    # 6. v27 ASL gloss (custom corpus format — pairs of english + gloss)
    p = "docs/srmech/rbs_lm_research/rbs_lm_instrument_v27_asl_gloss.bin"
    corpus_path = Path("docs/srmech/rbs_lm_research/asl_corpus.json")
    if Path(p).exists() and corpus_path.exists():
        pairs = json.load(open(corpus_path))["pairs"]
        gloss_corpus = list(set(p["asl_gloss"] for p in pairs))
        v27_probes = [(p["english"], p["asl_gloss"]) for p in pairs[:20]]
        instruments_to_test.append((
            "v27 ASL gloss (74 pairs / 1324 obs)", p,
            gloss_corpus,
            v27_probes,
        ))

    # 7. v44 turtle-walk (already tested in initial smoke; include for comparison)
    p = "docs/srmech/rbs_lm_research/rbs_lm_instrument_v44_turtle_walk.bin"
    corpus_path = Path("docs/srmech/rbs_lm_research/turtle_walk_corpus.json")
    if Path(p).exists() and corpus_path.exists():
        pairs = json.load(open(corpus_path))["pairs"]
        logo_corpus = list(set(p["logo"] for p in pairs))
        v44_probes = [(p["english"], p["logo"]) for p in pairs[:20]]
        instruments_to_test.append((
            "v44 turtle-walk (51 pairs / 443 obs)", p,
            logo_corpus,
            v44_probes,
        ))

    print(f"=== R-RBS-LM-45 extended read-mode smoke: {len(instruments_to_test)} instruments ===")
    all_results = {}
    for label, p, corpus, probes in instruments_to_test:
        r = run_one(label, p, corpus, probes, vocab_table, D)
        if r is not None:
            all_results[label] = r

    # ===== Final cross-instrument summary =====
    print(f"\n\n{'='*72}")
    print(f"=== CROSS-INSTRUMENT RANK SIGNAL SUMMARY")
    print(f"{'='*72}\n")
    print(f"  {'instrument':<55s} {'rank-1%':>8s} {'top-d%':>7s} {'top-q%':>7s} {'mean%':>7s} {'p-est':>7s}")
    print(f"  {'-'*55} {'-'*8} {'-'*7} {'-'*7} {'-'*7} {'-'*7}")
    for label, r in all_results.items():
        s = r["stats"]
        label_short = label[:55]
        print(f"  {label_short:<55s} {100*s['rank_1_rate']:>7.1f}% {100*s['top_decile_rate']:>6.1f}% "
              f"{100*s['top_quartile_rate']:>6.1f}% {s['mean_rank_percentile'] or 50.0:>6.1f}% "
              f"{s.get('p_estimate', '?'):>7s}")

    print(f"\n  Chance values: rank-1 = 100/corpus_size%; top-decile = 10%; top-quartile = 25%; mean = 50%")
    print(f"  Strong signal = rank-1 >> chance, mean << 50%, p-estimate <0.05 or <0.01")

    out_path = Path("docs/srmech/rbs_lm_research/read_mode_extended_results.json")
    out_path.write_text(json.dumps(all_results, indent=2, ensure_ascii=False))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
