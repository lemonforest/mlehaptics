"""R-RBS-LM-24 — Context compaction by truncation experiment.

Per user direction: *"if we're some how able to provide a way to compact
context by truncation instead of rebuilding."*

The Path C inference cascade already truncates to CONTEXT_WINDOW=64 each
step (`tokens[-CONTEXT_WINDOW:]`). This experiment measures: when we
deliberately truncate further (window = 8, 16, 32, 48), how much does the
generated sequence diverge from the full-window-64 baseline?

If outputs are stable under aggressive truncation, then upstream
orchestrators can compact context to the local expert cheaply — pass a
short window's worth of tokens rather than rebuilding context from a long
session. If outputs differ wildly, truncation is not a free compaction
move.

We measure the divergence at the *generation* level, not against any
teacher model. The question is whether the cascade is *robust* to
truncation, not whether it's *accurate* against GPT-2's argmax (we already
know the 3.3% ceiling exists from R-RBS-LM-18).

Metrics:
  - First-token divergence: at generation step k, does token-k match the
    full-window baseline?
  - Cumulative agreement: fraction of tokens that match across the run

Usage:
    ~/.venvs/rbs-lm-research/bin/python \\
        docs/srmech/rbs_lm_research/truncation_experiment.py
"""

import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "python"))
sys.path.insert(0, str(HERE))

from rbs_lm_chatbot import RBSChatbot  # noqa: E402


PROMPTS = [
    "The morning sun cast long shadows across the cobblestones as the old town began to stir",
    "Charles Babbage designed the Analytical Engine in the 1830s, conceiving of a machine",
    "Photosynthesis converts light energy into chemical energy stored in glucose molecules",
    "Algorithms for sorting have been studied for decades. Quicksort achieves average-case",
    "Database transactions enforce four properties known as ACID: atomicity, consistency",
]

WINDOWS = [8, 16, 32, 48, 64]  # 64 = baseline (CONTEXT_WINDOW)
MAX_NEW = 15


def run_experiment(instrument_path):
    print(f"=== R-RBS-LM-24 — Truncation experiment ===")
    print(f"  instrument: {instrument_path}")
    print(f"  windows tested: {WINDOWS}")
    print(f"  max_new_tokens: {MAX_NEW}")
    print(f"  prompts: {len(PROMPTS)} (each long enough to engage truncation)")

    bot = RBSChatbot.load(instrument_path=instrument_path, use_path_c=True, verbose=True)

    results = []
    for prompt in PROMPTS:
        print(f"\n--- prompt: '{prompt[:60]}...' ---")
        # Baseline at window=64
        base = bot.respond_with_metadata(prompt, max_new_tokens=MAX_NEW,
                                          context_truncation=64)
        base_tokens = base["new_token_ids"]
        print(f"  window=64 (baseline): {base['completion']!r}")
        print(f"    latency: {base['total_ms']:.0f} ms")

        prompt_results = {
            "prompt": prompt,
            "baseline_window_64": {
                "completion": base["completion"],
                "tokens": base_tokens,
                "latency_ms": base["total_ms"],
            },
            "by_window": {},
        }

        for w in [w for w in WINDOWS if w != 64]:
            t0 = time.time()
            run = bot.respond_with_metadata(prompt, max_new_tokens=MAX_NEW,
                                            context_truncation=w)
            agreement = [int(b == r) for b, r in zip(base_tokens, run["new_token_ids"])]
            n_agree = sum(agreement)
            # First-divergence step (0 = first token already diverges)
            first_div = next((i for i, a in enumerate(agreement) if a == 0), MAX_NEW)
            elapsed = (time.time() - t0) * 1000
            print(f"  window={w:2d}: {run['completion']!r}")
            print(f"    agreement vs baseline: {n_agree}/{MAX_NEW} "
                  f"({100*n_agree/MAX_NEW:.0f}%); first-div@step {first_div}; "
                  f"latency {elapsed:.0f} ms")
            prompt_results["by_window"][str(w)] = {
                "completion": run["completion"],
                "tokens": run["new_token_ids"],
                "agreement_vs_baseline": n_agree,
                "first_divergence_step": first_div,
                "latency_ms": elapsed,
            }

        results.append(prompt_results)

    # Aggregate stats
    print(f"\n=== Aggregate ===")
    print(f"  {'window':>8}  {'avg agreement':>15}  {'avg first-div':>15}  {'avg latency':>15}")
    for w in [w for w in WINDOWS if w != 64]:
        agrs = [r["by_window"][str(w)]["agreement_vs_baseline"] for r in results]
        divs = [r["by_window"][str(w)]["first_divergence_step"] for r in results]
        lats = [r["by_window"][str(w)]["latency_ms"] for r in results]
        avg_agr = sum(agrs) / len(agrs) / MAX_NEW
        avg_div = sum(divs) / len(divs)
        avg_lat = sum(lats) / len(lats)
        print(f"  {w:>8d}  {100*avg_agr:>14.1f}%  {avg_div:>14.1f}  {avg_lat:>12.0f} ms")

    out_path = Path("docs/srmech/rbs_lm_research/truncation_experiment_results.json")
    out_path.write_text(json.dumps({
        "partition": "R-RBS-LM-24",
        "instrument_path": instrument_path,
        "windows": WINDOWS,
        "max_new_tokens": MAX_NEW,
        "results": results,
    }, indent=2))
    print(f"\nResults saved: {out_path}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--instrument",
                        default="docs/srmech/rbs_lm_research/rbs_lm_instrument_v18.bin")
    args = parser.parse_args()
    run_experiment(args.instrument)
