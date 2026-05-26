"""R-RBS-LM-46b — Pure fp16-only merge depths 1→3 (uniform + obs-weighted).

Validates R-RBS-LM-46a's Finding 13 ("uniform-weight + fp32 sources is
the operational recipe") on a controlled-precision axis. ALL sources are
fp16-or-better; no Q4 in the mix.

Sources (3 available fp16+ instruments):
  1. v25b GPT-2 byte fp32 (124M) — 647 obs
  2. v29 TinyLlama 1.1B fp32 (intermediate) — 443 obs
  3. v29 TinyLlama 1.1B fp16 (Chat) — 442 obs

Depths: 1, 2, 3. Both tracks (uniform + obs-weighted) for each depth.

Predictions per R-RBS-LM-46a:
  - depth-1 uniform: chi² ~5 (single source baseline)
  - depth-2 uniform: chi² ~12.5 (matches 46a depth-2 result)
  - depth-3 uniform: ODD-voter count → no tie-breaking parity bias.
    If chi² climbs further: real precision-stacking effect.
    If chi² collapses: parity bias was dominant in 46a depth-2.
  - depth-3 obs-weighted: comparable mix (all fp16+); no v35-dominance
    artifact; should show signal if fp16-stacking helps.

Falsifies in either direction:
  - chi² grows monotonically with fp16 depth → fp16-stacking is real lever
  - chi² flat or oscillating → R-RBS-LM-46a parity bias was the headline
"""

import json
import re
import sys
import tempfile
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
from rbs_lm_merge import merge_instruments  # noqa: E402


SOURCES = [
    ("v25b GPT-2 fp32 (124M)",
     "docs/srmech/rbs_lm_research/rbs_lm_instrument_v25b_distill_gpt2.bin",
     "docs/srmech/rbs_lm_research/rbs_lm_instrument_v25b_distill_gpt2.corpus.txt",
     647),
    ("v29 TinyLlama 1.1B fp32 (intermediate)",
     "docs/srmech/rbs_lm_research/rbs_lm_instrument_v29_distill_TinyLlama__TinyLlama-1.1B-intermediate-step-1431k-3T.bin",
     "docs/srmech/rbs_lm_research/rbs_lm_instrument_v29_distill_TinyLlama__TinyLlama-1.1B-intermediate-step-1431k-3T.corpus.txt",
     443),
    ("v29 TinyLlama 1.1B fp16 (Chat)",
     "docs/srmech/rbs_lm_research/rbs_lm_instrument_v29_distill_TinyLlama__TinyLlama-1.1B-Chat-v1.0.bin",
     "docs/srmech/rbs_lm_research/rbs_lm_instrument_v29_distill_TinyLlama__TinyLlama-1.1B-Chat-v1.0.corpus.txt",
     442),
]


def make_phrase_corpus(text, max_phrases=80, min_len=15, max_len=180):
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


def make_probes_from_corpus(text, n_probes=30, seed=42):
    rng = np.random.default_rng(seed)
    sentences = [s.strip() for s in re.split(r'[.!?]\s+', text)
                 if 20 < len(s.strip()) < 200]
    rng.shuffle(sentences)
    probes = []
    for sent in sentences[:n_probes * 3]:
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


def run_one(label, merged_bytes, phrase_corpus, probes, vocab_table):
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
        f.write(merged_bytes)
        tmp = f.name
    try:
        instrument = load_instrument_bytes(tmp)
    finally:
        Path(tmp).unlink(missing_ok=True)

    baseline = baseline_random_phrase_sim(phrase_corpus, vocab_table, D, n_samples=200)
    rank_results = []
    for query, expected in probes:
        ranked = phrase_match_retrieval(instrument, query, phrase_corpus, vocab_table, D)
        try:
            rank = next(i for i, (phr, _) in enumerate(ranked) if phr == expected)
        except StopIteration:
            try:
                rank = next(i for i, (phr, _) in enumerate(ranked)
                            if expected[:30] in phr or phr in expected)
            except StopIteration:
                rank = -1
        rank_results.append(rank)
    stats = rank_stats(rank_results, len(phrase_corpus))
    print(f"  [{label}] rank-1={stats.get('rank_1_count', 0)}/{stats['n_probes']} "
          f"({100*stats.get('rank_1_rate', 0):.1f}%), "
          f"top-d={100*stats.get('top_decile_rate', 0):.1f}%, "
          f"top-q={100*stats.get('top_quartile_rate', 0):.1f}%, "
          f"mean={stats.get('mean_rank_percentile', 50.0):.1f}%, "
          f"chi²={stats.get('chi2_5bins', 0):.2f} ({stats.get('p_estimate', '?')})")
    return {"label": label, "corpus_size": len(phrase_corpus),
            "n_probes": len(probes), "baseline": baseline, "stats": stats}


def main():
    print("=== R-RBS-LM-46b — Pure fp16+ merge depths 1→3 ===\n")

    instruments, obs_counts, all_text = [], [], []
    for label, ipath, cpath, n in SOURCES:
        with open(ipath, "rb") as f:
            instruments.append(f.read())
        obs_counts.append(n)
        all_text.append(Path(cpath).read_text())
        print(f"  loaded {label} ({n} obs)")

    union_text = "\n\n".join(all_text)
    phrase_corpus = make_phrase_corpus(union_text, max_phrases=80)
    probes = make_probes_from_corpus(union_text, n_probes=30, seed=42)
    print(f"\nUnion corpus: {len(phrase_corpus)} phrases; {len(probes)} probes")

    vocab_table = compute_byte_vocab_table(D)
    results = {}

    print(f"\n{'='*72}\n=== Uniform-weight merge\n{'='*72}\n")
    for depth in [1, 2, 3]:
        merged = merge_instruments(instruments[:depth], n_obs=None)
        label = f"depth-{depth}-uniform"
        results[label] = run_one(label, merged, phrase_corpus, probes, vocab_table)

    print(f"\n{'='*72}\n=== Obs-weighted merge\n{'='*72}\n")
    for depth in [1, 2, 3]:
        merged = merge_instruments(instruments[:depth], n_obs=obs_counts[:depth])
        label = f"depth-{depth}-obsw"
        results[label] = run_one(label, merged, phrase_corpus, probes, vocab_table)

    # Summary + reading
    print(f"\n\n{'='*72}\n=== R-RBS-LM-46b SUMMARY\n{'='*72}\n")
    print(f"  {'track':<12s} {'depth':>6s} {'rank-1%':>8s} {'top-d%':>7s} "
          f"{'top-q%':>7s} {'mean%':>7s} {'chi²':>7s} {'p-est':>7s}")
    print(f"  {'-'*12} {'-'*6} {'-'*8} {'-'*7} {'-'*7} {'-'*7} {'-'*7} {'-'*7}")
    for depth in [1, 2, 3]:
        for track in ["uniform", "obsw"]:
            r = results[f"depth-{depth}-{track}"]
            s = r["stats"]
            print(f"  {track:<12s} {depth:>6d} "
                  f"{100*s.get('rank_1_rate', 0):>7.1f}% "
                  f"{100*s.get('top_decile_rate', 0):>6.1f}% "
                  f"{100*s.get('top_quartile_rate', 0):>6.1f}% "
                  f"{s.get('mean_rank_percentile', 50.0):>6.1f}% "
                  f"{s.get('chi2_5bins', 0):>7.2f} "
                  f"{s.get('p_estimate', '?'):>7s}")

    out = {
        "partition": "R-RBS-LM-46b",
        "sources_used": [s[0] for s in SOURCES],
        "results": results,
        "n_corpus_phrases": len(phrase_corpus),
        "n_probes": len(probes),
    }
    out_path = Path("docs/srmech/rbs_lm_research/R-RBS-LM-46b_results.json")
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"\nResults: {out_path}")

    # Quick reading
    uniform_chi2s = [results[f"depth-{d}-uniform"]["stats"].get("chi2_5bins", 0)
                     for d in [1, 2, 3]]
    obsw_chi2s = [results[f"depth-{d}-obsw"]["stats"].get("chi2_5bins", 0)
                  for d in [1, 2, 3]]
    uniform_means = [results[f"depth-{d}-uniform"]["stats"].get("mean_rank_percentile", 50)
                     for d in [1, 2, 3]]

    print(f"\n=== Reading ===")
    print(f"  Uniform chi² [1, 2, 3]: {uniform_chi2s}")
    print(f"  Obs-w   chi² [1, 2, 3]: {obsw_chi2s}")
    print(f"  Uniform mean rank pct:  {uniform_means}")

    if uniform_chi2s[2] >= uniform_chi2s[1]:
        print(f"  → depth-3 uniform ≥ depth-2 uniform: fp16-stacking SCALES (odd voters; no parity).")
    elif uniform_chi2s[2] < uniform_chi2s[1] - 3:
        print(f"  → depth-3 < depth-2 uniform: fp16-stacking DOES NOT scale; 46a's parity bias was dominant.")
    else:
        print(f"  → depth-3 ≈ depth-2 uniform: comparable. Modest fp16-stacking effect.")


if __name__ == "__main__":
    main()
