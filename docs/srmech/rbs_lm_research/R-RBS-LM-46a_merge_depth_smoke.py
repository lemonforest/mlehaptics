"""R-RBS-LM-46a — Merge-depth scaling of cascade read-mode signal.

Per R-RBS-LM-45 extended: v33 (3-source merge) is the ONLY instrument with
chi² > 7.78 across the 7-instrument matrix. R-RBS-LM-46a tests whether
merge-depth scaling pushes that signal further.

Two tracks (to isolate "more sources" from "more observations"):

  Track 1 — obs-weighted merge (canonical, matches v33 line):
    Each source instrument's bits weighted by its observation count.
    Equivalent to bundling all underlying single-bindings.

  Track 2 — uniform-weight merge:
    Each source instrument counts equally. Isolates depth-effect from
    obs-count-effect.

For each track, build merges at depths 1, 2, 3, 4, 5, 6 from the available
byte-mode single-source LLM-distill instruments (v27 ASL + v44 turtle are
pair-mapped domain-specific, excluded for clean LLM-source axis).

Then run read-mode rank smoke against a shared UNION probe corpus.

Outputs:
  - R-RBS-LM-46a_merge_depth_results.json (raw stats per depth × track)
  - Summary table written to stdout

Methodology: rank-based read-mode per R-RBS-LM-45 (`rbs_lm_read_mode`).
Probes drawn from the union of all source corpora (sentence-prefix
shuffle, fixed seed). Same probes apply to every merge depth → isolates
merge-depth effect.
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
from rbs_lm_merge import merge_instruments  # noqa: E402


# Sources for merge-depth scaling (ordered to match v33 at depth 3)
SOURCES = [
    ("v25b GPT-2 fp32 (124M)",
     "docs/srmech/rbs_lm_research/rbs_lm_instrument_v25b_distill_gpt2.bin",
     "docs/srmech/rbs_lm_research/rbs_lm_instrument_v25b_distill_gpt2.corpus.txt",
     647),
    ("v29 TinyLlama 1.1B fp32 (intermediate)",
     "docs/srmech/rbs_lm_research/rbs_lm_instrument_v29_distill_TinyLlama__TinyLlama-1.1B-intermediate-step-1431k-3T.bin",
     "docs/srmech/rbs_lm_research/rbs_lm_instrument_v29_distill_TinyLlama__TinyLlama-1.1B-intermediate-step-1431k-3T.corpus.txt",
     443),
    ("v31 Llama-3.2-1B Q4 (Instruct)",
     "docs/srmech/rbs_lm_research/rbs_lm_instrument_v31_gguf_llama32-1b-q4.bin",
     "docs/srmech/rbs_lm_research/rbs_lm_instrument_v31_gguf_llama32-1b-q4.corpus.txt",
     448),
    ("v29 TinyLlama 1.1B fp16 (Chat)",
     "docs/srmech/rbs_lm_research/rbs_lm_instrument_v29_distill_TinyLlama__TinyLlama-1.1B-Chat-v1.0.bin",
     "docs/srmech/rbs_lm_research/rbs_lm_instrument_v29_distill_TinyLlama__TinyLlama-1.1B-Chat-v1.0.corpus.txt",
     442),
    ("v35 Llama-3.1-8B Q4 (Instruct)",
     "docs/srmech/rbs_lm_research/rbs_lm_instrument_v31_gguf_llama31-8b-q4.bin",
     "docs/srmech/rbs_lm_research/rbs_lm_instrument_v31_gguf_llama31-8b-q4.corpus.txt",
     1317),
    ("v31 TinyLlama 1.1B Q4 (Chat)",
     "docs/srmech/rbs_lm_research/rbs_lm_instrument_v31_gguf_tinyllama-chat-q4.bin",
     "docs/srmech/rbs_lm_research/rbs_lm_instrument_v31_gguf_tinyllama-chat-q4.corpus.txt",
     437),
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


def make_probes_from_corpus_text(text, n_probes=30, seed=42):
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


def run_depth(label, merged_bytes, phrase_corpus, probes, vocab_table):
    """Save merged bytes to a temp instrument file; load via standard path;
    run read-mode rank smoke; return stats."""
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
        f.write(merged_bytes)
        tmp_path = f.name

    try:
        instrument = load_instrument_bytes(tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

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
    return {
        "label": label, "corpus_size": len(phrase_corpus),
        "n_probes": len(probes), "baseline": baseline, "stats": stats,
    }


def main():
    vocab_table = compute_byte_vocab_table(D)

    # ---- Load source instruments + build shared union probe corpus -----
    print("=== R-RBS-LM-46a merge-depth scaling ===\n")
    print("Loading source instruments + building union corpus...")
    instruments = []
    obs_counts = []
    all_text = []
    for label, ipath, cpath, n_obs in SOURCES:
        if not Path(ipath).exists():
            print(f"  SKIP — {ipath} not found")
            continue
        with open(ipath, "rb") as f:
            instruments.append(f.read())
        obs_counts.append(n_obs)
        if Path(cpath).exists():
            all_text.append(Path(cpath).read_text())
        print(f"  loaded {label}  ({n_obs} obs)")

    if len(instruments) < 6:
        print(f"\n  WARNING: only {len(instruments)} sources available; "
              f"depth 6 will be capped.")

    union_text = "\n\n".join(all_text)
    phrase_corpus = make_phrase_corpus(union_text, max_phrases=80)
    probes = make_probes_from_corpus_text(union_text, n_probes=30, seed=42)
    print(f"\nUnion corpus: {len(phrase_corpus)} phrases; {len(probes)} probes")

    # ---- Track 1: obs-weighted merge depths 1..N -----------------------
    print(f"\n{'='*72}")
    print(f"=== Track 1: obs-weighted merge (canonical; matches v33 line)")
    print(f"{'='*72}\n")
    track1 = {}
    for depth in range(1, len(instruments) + 1):
        merged = merge_instruments(instruments[:depth], n_obs=obs_counts[:depth])
        label = f"depth-{depth}-obsw"
        track1[label] = run_depth(label, merged, phrase_corpus, probes, vocab_table)

    # ---- Track 2: uniform-weight merge depths 1..N ---------------------
    print(f"\n{'='*72}")
    print(f"=== Track 2: uniform-weight merge (isolates depth from obs-count)")
    print(f"{'='*72}\n")
    track2 = {}
    for depth in range(1, len(instruments) + 1):
        merged = merge_instruments(instruments[:depth], n_obs=None)
        label = f"depth-{depth}-uniform"
        track2[label] = run_depth(label, merged, phrase_corpus, probes, vocab_table)

    # ---- Final summary -------------------------------------------------
    print(f"\n\n{'='*72}")
    print(f"=== MERGE-DEPTH SUMMARY")
    print(f"{'='*72}\n")
    print(f"  {'track':<12s} {'depth':>6s} {'rank-1%':>8s} {'top-d%':>7s} "
          f"{'top-q%':>7s} {'mean%':>7s} {'chi²':>7s} {'p-est':>7s}")
    print(f"  {'-'*12} {'-'*6} {'-'*8} {'-'*7} {'-'*7} {'-'*7} {'-'*7} {'-'*7}")
    for depth in range(1, len(instruments) + 1):
        for track_name, results in [("obsw", track1), ("uniform", track2)]:
            r = results[f"depth-{depth}-{track_name}"]
            s = r["stats"]
            print(f"  {track_name:<12s} {depth:>6d} "
                  f"{100*s.get('rank_1_rate', 0):>7.1f}% "
                  f"{100*s.get('top_decile_rate', 0):>6.1f}% "
                  f"{100*s.get('top_quartile_rate', 0):>6.1f}% "
                  f"{s.get('mean_rank_percentile', 50.0):>6.1f}% "
                  f"{s.get('chi2_5bins', 0):>7.2f} "
                  f"{s.get('p_estimate', '?'):>7s}")

    # ---- Reading -------------------------------------------------------
    print(f"\n=== Reading ===")
    track1_chi2s = [track1[f"depth-{d}-obsw"]["stats"].get("chi2_5bins", 0)
                    for d in range(1, len(instruments) + 1)]
    track2_chi2s = [track2[f"depth-{d}-uniform"]["stats"].get("chi2_5bins", 0)
                    for d in range(1, len(instruments) + 1)]
    track1_means = [track1[f"depth-{d}-obsw"]["stats"].get("mean_rank_percentile", 50.0)
                    for d in range(1, len(instruments) + 1)]
    track2_means = [track2[f"depth-{d}-uniform"]["stats"].get("mean_rank_percentile", 50.0)
                    for d in range(1, len(instruments) + 1)]
    print(f"  Track 1 (obs-weighted) chi² at depths 1..{len(track1_chi2s)}: {track1_chi2s}")
    print(f"  Track 2 (uniform)      chi² at depths 1..{len(track2_chi2s)}: {track2_chi2s}")
    print(f"  Track 1 mean-rank-percentile: {track1_means}")
    print(f"  Track 2 mean-rank-percentile: {track2_means}")

    # Save results
    output = {
        "track1_obs_weighted": track1,
        "track2_uniform": track2,
        "track1_chi2_by_depth": track1_chi2s,
        "track2_chi2_by_depth": track2_chi2s,
        "track1_mean_pct_by_depth": track1_means,
        "track2_mean_pct_by_depth": track2_means,
        "sources_used": [s[0] for s in SOURCES[:len(instruments)]],
        "n_corpus_phrases": len(phrase_corpus),
        "n_probes": len(probes),
    }
    out_path = Path("docs/srmech/rbs_lm_research/R-RBS-LM-46a_merge_depth_results.json")
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
