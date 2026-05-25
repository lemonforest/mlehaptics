"""R-RBS-LM-29 — A/B compare cascade behavior across source-model size.

Loads multiple byte-level instruments distilled from different source models
and runs the SAME smoke prompts through each. Goal: detect whether source-
model richness changes the cascade's mode-collapse pattern.

Per `[[user_stance_ai_is_not_a_substrate]]` + R-RBS-LM-19 structural ceiling:
the cascade is the same code; same vocab table; same encoding. Only the
training corpus's BYTE-TRANSITION STATISTICS differ. If we see materially
different cascade output between v25b (GPT-2) and v29 (TinyLlama), that's
evidence source-model size matters. If we see the same single-byte mode-
collapse, that's evidence the cascade is the structural bottleneck.

Honest framework reading per the falsification discipline:
  - Most likely outcome: same structural ceiling holds; mode-collapse to
    single bytes regardless of source. Source-model scaling is orthogonal.
  - Possible positive outcome: richer source → varied output bytes; the
    cascade lifts out of single-byte fixed-point even if total agreement
    stays bounded.

Usage:
    ~/.venvs/rbs-lm-research/bin/python \\
        docs/srmech/rbs_lm_research/source_model_comparison_smoke.py
"""

import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "python"))
sys.path.insert(0, str(HERE))

from rbs_lm_chatbot import RBSChatbotBytes  # noqa: E402


SMOKE_PROMPTS = [
    "The morning sun",
    "Once upon a time",
    "Algorithms for sorting",
    "The President of the United States",
    "Photosynthesis converts light",
    "I beat the eggs",
    "Hello, world!",
    "What is the topic?",
]

MAX_NEW = 24


def byte_diversity_stats(byte_list):
    """Measure mode-collapse vs varied output. Returns:
      - n_unique: distinct byte values in the output
      - max_run: longest run of the same byte
      - entropy_bits: Shannon entropy of byte distribution
    """
    import math
    if not byte_list:
        return {"n_unique": 0, "max_run": 0, "entropy_bits": 0.0}
    n_unique = len(set(byte_list))
    max_run = 1
    cur_run = 1
    for i in range(1, len(byte_list)):
        if byte_list[i] == byte_list[i - 1]:
            cur_run += 1
            max_run = max(max_run, cur_run)
        else:
            cur_run = 1
    from collections import Counter
    counts = Counter(byte_list)
    total = len(byte_list)
    entropy = -sum((c / total) * math.log2(c / total) for c in counts.values())
    return {"n_unique": n_unique, "max_run": max_run,
            "entropy_bits": round(entropy, 3)}


def run_smoke(instrument_path):
    if not Path(instrument_path).exists():
        return None
    bot = RBSChatbotBytes.load(instrument_path=instrument_path, verbose=False)

    results = []
    for prompt in SMOKE_PROMPTS:
        t0 = time.time()
        r = bot.respond_with_metadata(prompt, max_new_tokens=MAX_NEW)
        elapsed = (time.time() - t0) * 1000
        stats = byte_diversity_stats(r["new_token_ids"])
        results.append({
            "prompt": prompt,
            "completion": r["completion"],
            "byte_ids": r["new_token_ids"],
            "stats": stats,
            "latency_ms": elapsed,
        })
    return results


def main():
    # Instruments to compare
    instruments = [
        ("v25b GPT-2 (124M; ~10k bytes)",
         "docs/srmech/rbs_lm_research/rbs_lm_instrument_v25b_distill_gpt2.bin"),
        ("v29 TinyLlama (1.1B; ~3.5k bytes)",
         "docs/srmech/rbs_lm_research/rbs_lm_instrument_v29_distill_TinyLlama__TinyLlama-1.1B-intermediate-step-1431k-3T.bin"),
    ]

    print(f"=== R-RBS-LM-29 — Source-model comparison smoke ===\n")

    all_results = {}
    for label, path in instruments:
        print(f"{'='*72}")
        print(f"=== {label}")
        print(f"=== {path}")
        print(f"{'='*72}")
        r = run_smoke(path)
        if r is None:
            print(f"  SKIP — instrument file not found")
            continue
        for x in r:
            print(f"  prompt: {x['prompt']!r}")
            print(f"    completion: {x['completion']!r}")
            print(f"    stats: unique={x['stats']['n_unique']:>2d}, "
                  f"max_run={x['stats']['max_run']:>2d}, "
                  f"entropy={x['stats']['entropy_bits']:.2f} bits")
            print()
        all_results[label] = r

    # ---- Aggregate ---------------------------------------------------
    if len(all_results) >= 2:
        print(f"{'='*72}")
        print(f"=== Aggregate byte-diversity comparison ===")
        print(f"{'='*72}\n")
        print(f"  {'instrument':<40s}  {'avg unique':>10s}  {'avg max_run':>11s}  {'avg entropy':>11s}")
        for label, results in all_results.items():
            n_uniques = [r["stats"]["n_unique"] for r in results]
            max_runs = [r["stats"]["max_run"] for r in results]
            entropies = [r["stats"]["entropy_bits"] for r in results]
            print(f"  {label:<40s}  {sum(n_uniques)/len(n_uniques):>10.1f}  "
                  f"{sum(max_runs)/len(max_runs):>11.1f}  "
                  f"{sum(entropies)/len(entropies):>11.2f}")

        # Pairwise byte-by-byte agreement
        print(f"\n=== Pairwise output agreement (byte-by-byte over MAX_NEW={MAX_NEW}) ===")
        labels = list(all_results.keys())
        for i in range(len(labels)):
            for j in range(i + 1, len(labels)):
                pair_matches = []
                for ri, rj in zip(all_results[labels[i]], all_results[labels[j]]):
                    m = sum(1 for a, b in zip(ri["byte_ids"], rj["byte_ids"]) if a == b)
                    pair_matches.append(m)
                avg_match = sum(pair_matches) / len(pair_matches)
                print(f"  {labels[i]:<40s} vs")
                print(f"  {labels[j]:<40s}: avg {avg_match:.1f}/{MAX_NEW} matching bytes")

    out_path = Path("docs/srmech/rbs_lm_research/source_model_comparison_results.json")
    out_path.write_text(json.dumps(all_results, indent=2, ensure_ascii=False))
    print(f"\nResults: {out_path}")

    print(f"\n=== Honest framework reading ===")
    if len(all_results) >= 2:
        labels = list(all_results.keys())
        avg_unique_a = sum(r["stats"]["n_unique"] for r in all_results[labels[0]]) / len(all_results[labels[0]])
        avg_unique_b = sum(r["stats"]["n_unique"] for r in all_results[labels[1]]) / len(all_results[labels[1]])
        if abs(avg_unique_a - avg_unique_b) >= 2.0:
            print(f"  Byte-diversity DIFFERS materially between sources.")
            print(f"  → Source-model size IS affecting cascade mode-collapse pattern.")
            print(f"  → Hypothesis 'cascade is the bottleneck regardless of source' is")
            print(f"    weakened; richer source DOES change output.")
        else:
            print(f"  Byte-diversity is COMPARABLE across sources.")
            print(f"  → Evidence that source-model size is orthogonal to cascade limits.")
            print(f"  → R-RBS-LM-19 structural-ceiling argument holds.")


if __name__ == "__main__":
    main()
