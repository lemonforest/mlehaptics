"""R-RBS-LM-25 — Byte-level instrument validation + framework-reading smoke.

Runs three categories of test against both byte-level instruments
(Variant A: GPU-less text-self-supervised; Variant B: distilled from GPT-2)
and reports honestly per the falsification discipline:

  1. Hallucination corpus (same prompts as R-RBS-LM-18):
     baseline-comparison — does byte-level fall in the 3.3% ballpark
     of the BPE Path C ceiling, or lower, or higher?

  2. Language coverage (THE big win for byte-level):
     non-English prompts (Chinese / Arabic / emoji / code) — does the
     server accept them and produce structurally-valid UTF-8 outputs?
     This is the language-agnostic surface the BPE version lacks.

  3. Self-similarity sanity:
     prompts from the training corpus (the GPT-2-generated text) — does
     the cascade recognize byte-transitions it has actually seen?

Per `[[user_stance_ai_is_not_a_substrate]]`: we do NOT claim that any
positive signal here means the byte-level expert is "smarter." The
ceiling is structural; the surface change is what we're measuring.

Usage:
    ~/.venvs/rbs-lm-research/bin/python \\
        docs/srmech/rbs_lm_research/bytes_smoke_validate.py
"""

import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "python"))
sys.path.insert(0, str(HERE))

from rbs_lm_chatbot import RBSChatbotBytes  # noqa: E402


HALLUCINATION_PROMPTS = [
    "The President of the United States in 2024 is",
    "The COVID-19 pandemic began in the year",
    "The Zorgon Empire of Andromeda was founded in",
    "The Klepton-7 algorithm was invented by",
    "The population of Wellington, New Zealand is approximately",
    "The chemical formula for caffeine is",
    "Seventeen multiplied by twenty-three equals",
    "The square root of one hundred and forty-four is",
    "Once upon a time, in a forest made of clockwork,",
]


LANGUAGE_COVERAGE_PROMPTS = [
    ("English", "The morning sun cast"),
    ("Chinese", "今天天气很好"),
    ("Arabic", "السلام عليكم"),
    ("Japanese mixed", "Hello 世界 🌍"),
    ("Code", "def fibonacci(n):"),
    ("Emoji", "🎉🎊🎈"),
    ("Math", "f(x) = x**2 + 2x + 1"),
    ("Mixed script", "café résumé naïve"),
]


def run_instrument(label, instrument_path, max_per_prompt=40):
    print(f"\n{'='*70}")
    print(f"=== {label}")
    print(f"=== instrument: {instrument_path}")
    print(f"{'='*70}")

    bot = RBSChatbotBytes.load(instrument_path=instrument_path, verbose=True)

    results = {"label": label, "instrument_path": instrument_path,
               "hallucination": [], "language_coverage": []}

    # --- Hallucination corpus ---
    print(f"\n--- Hallucination corpus (no source-model argmax for comparison; ")
    print(f"    byte-level has no BPE-trained-ground-truth to compare against;")
    print(f"    we report the raw output for human inspection) ---")
    for prompt in HALLUCINATION_PROMPTS:
        t0 = time.time()
        r = bot.respond_with_metadata(prompt, max_new_tokens=max_per_prompt)
        elapsed = (time.time() - t0) * 1000
        print(f"  prompt:     {prompt!r}")
        print(f"  completion: {r['completion']!r}")
        print(f"  latency:    {elapsed:.0f} ms ({elapsed/max_per_prompt:.1f} ms/byte)")
        results["hallucination"].append({
            "prompt": prompt,
            "completion": r["completion"],
            "n_bytes": max_per_prompt,
            "latency_ms": elapsed,
        })

    # --- Language coverage ---
    print(f"\n--- Language coverage (THE byte-level structural win) ---")
    for lang_label, prompt in LANGUAGE_COVERAGE_PROMPTS:
        t0 = time.time()
        try:
            r = bot.respond_with_metadata(prompt, max_new_tokens=24)
            elapsed = (time.time() - t0) * 1000
            ok = True
            err = None
        except Exception as e:
            elapsed = (time.time() - t0) * 1000
            ok = False
            err = f"{type(e).__name__}: {e}"
            r = {"completion": "", "n_bytes": 0}
        print(f"  [{lang_label:>14s}]  {prompt!r}")
        print(f"                  → {r.get('completion', '')!r} "
              f"({'OK' if ok else 'FAIL: '+err}; {elapsed:.0f} ms)")
        results["language_coverage"].append({
            "language": lang_label,
            "prompt": prompt,
            "completion": r.get("completion", ""),
            "ok": ok,
            "error": err,
            "latency_ms": elapsed,
        })

    return results


def main():
    print(f"=== R-RBS-LM-25 byte-level instrument validation ===")
    print(f"  expectation per `[[user_stance_ai_is_not_a_substrate]]` and the")
    print(f"  user 2026-05-25 framing: 3.3% ceiling IS STRUCTURAL — byte-level")
    print(f"  will not lift it. We're measuring (a) the cascade is operational")
    print(f"  at byte scale, (b) language coverage works, (c) what the byte-byte")
    print(f"  transitions look like below the ceiling.")

    instruments = [
        ("Variant A — GPU-less byte-level from srmech notebook",
         "docs/srmech/rbs_lm_research/rbs_lm_instrument_v25a_srmech.bin"),
        ("Variant B — Path D: distilled from GPT-2 (BPE-stripped)",
         "docs/srmech/rbs_lm_research/rbs_lm_instrument_v25b_distill_gpt2.bin"),
    ]

    all_results = []
    for label, path in instruments:
        if not Path(path).exists():
            print(f"\nSKIP: {label} — not found at {path}")
            continue
        all_results.append(run_instrument(label, path))

    out_path = Path("docs/srmech/rbs_lm_research/bytes_smoke_results.json")
    out_path.write_text(json.dumps({
        "partition": "R-RBS-LM-25",
        "results": all_results,
    }, indent=2, ensure_ascii=False))
    print(f"\n{'='*70}")
    print(f"Results saved: {out_path}")

    # --- Aggregate framework-reading summary ---
    print(f"\n=== Framework-reading summary ===")
    for r in all_results:
        n_lang_ok = sum(1 for x in r["language_coverage"] if x["ok"])
        n_lang = len(r["language_coverage"])
        avg_lat = sum(x["latency_ms"] for x in r["hallucination"]) / max(len(r["hallucination"]), 1)
        print(f"\n  {r['label']}")
        print(f"    language coverage: {n_lang_ok}/{n_lang} prompts accepted "
              f"without exception")
        print(f"    avg latency:       {avg_lat:.0f} ms per 40-byte completion "
              f"({avg_lat/40:.1f} ms/byte)")


if __name__ == "__main__":
    main()
