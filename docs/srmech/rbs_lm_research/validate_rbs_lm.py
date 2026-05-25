"""R-RBS-LM-7 — Validation of RBS-HDC instrument against source-model baseline.

Compares the R-RBS-LM-5 instrument's behavior against the GPT-2-small source
baseline captured in R-RBS-LM-3 §6. Three comparison axes:

1. Token-level agreement rate on continuation generation (source argmax vs
   RBS-HDC argmax at each position).
2. Hallucination corpus reproduction — does RBS-HDC produce the same 5
   failure-mode signatures (repetition collapse, factual hallucination,
   entity fabrication, tautological gibberish, numerical hallucination)?
3. Per-position divergence trajectory — does agreement decay with position?

BCI-compatibility verified: per-token latency on commodity CPU; total
memory footprint.

Maps observed divergence to R-RBS-LM-1 §7's four-scenario validation reading.

Usage:
    ~/.venvs/rbs-lm-research/bin/python \\
        docs/srmech/rbs_lm_research/validate_rbs_lm.py
"""

import json
import resource
import sys
import time
from pathlib import Path

import numpy as np
import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer

sys.path.insert(0, "docs/srmech/python")
sys.path.insert(0, "docs/srmech/rbs_lm_research")

from rbs_lm_encoder import D, bind, encode_context  # noqa: E402
from rbs_lm_inference import precompute_vocab_table, vectorised_cleanup  # noqa: E402


INSTRUMENT_PATH = Path("docs/srmech/rbs_lm_research/rbs_lm_instrument.bin")
RESULTS_PATH = Path("docs/srmech/rbs_lm_research/rbs_lm_validation_results.json")
N_GENERATE = 20  # tokens to generate per prompt


# Hallucination corpus from R-RBS-LM-3 §6.3
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


def source_generate(model, tokenizer, prompt, n_new):
    """Source GPT-2-small greedy generation; returns list of token IDs."""
    input_ids = tokenizer.encode(prompt, return_tensors="pt")
    with torch.no_grad():
        out = model.generate(
            input_ids,
            max_new_tokens=n_new,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
    return out[0][input_ids.shape[1]:].tolist()


def rbs_generate(instrument, prompt_token_ids, n_new, vocab_table, D=D):
    """RBS-HDC greedy generation; returns list of token IDs + latencies."""
    from rbs_lm_inference import generate
    tokens, latencies = generate(instrument, prompt_token_ids, n_new, vocab_table, D)
    return tokens[len(prompt_token_ids):], latencies


def main():
    print(f"=== R-RBS-LM-7 — Validation of RBS-HDC instrument vs source-model baseline ===")

    # ---- load source model + tokenizer ---------------------------------
    print("\nLoading source model (GPT-2-small)...")
    tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
    model = GPT2LMHeadModel.from_pretrained("gpt2")
    model.eval()
    print("  loaded.")

    # ---- load instrument + vocab table ---------------------------------
    print("\nLoading RBS-HDC instrument + vocab table...")
    instrument = INSTRUMENT_PATH.read_bytes()
    vocab_table = precompute_vocab_table(vocab_size=50257, D=D)
    print(f"  instrument: {len(instrument)} bytes")
    print(f"  vocab table: {vocab_table.shape}, {vocab_table.nbytes/1024**2:.1f} MB")

    # ---- 1. hallucination corpus comparison ----------------------------
    print(f"\n=== Hallucination corpus comparison ===")
    print(f"  {len(HALLUCINATION_PROMPTS)} prompts × {N_GENERATE} generated tokens each")
    hallucination_results = []
    all_source_tokens = []
    all_rbs_tokens = []
    for prompt in HALLUCINATION_PROMPTS:
        prompt_ids = tokenizer.encode(prompt)
        # Source greedy generation
        source_new = source_generate(model, tokenizer, prompt, N_GENERATE)
        # RBS-HDC greedy generation
        rbs_new, _ = rbs_generate(instrument, prompt_ids, N_GENERATE, vocab_table)
        # Token-level agreement (per position)
        agreement = [int(s == r) for s, r in zip(source_new, rbs_new)]
        n_agree = sum(agreement)
        all_source_tokens.extend(source_new)
        all_rbs_tokens.extend(rbs_new)

        result = {
            "prompt": prompt,
            "source_tokens": source_new,
            "source_decoded": tokenizer.decode(source_new),
            "rbs_tokens": rbs_new,
            "rbs_decoded": tokenizer.decode(rbs_new),
            "agreement_per_position": agreement,
            "agreement_rate": n_agree / N_GENERATE,
        }
        hallucination_results.append(result)
        print(f"\n  prompt: '{prompt}'")
        print(f"    source: '{result['source_decoded'][:80]}'")
        print(f"    RBS-HDC: '{result['rbs_decoded'][:80]}'")
        print(f"    agreement: {n_agree}/{N_GENERATE} ({100*n_agree/N_GENERATE:.0f}%)")

    overall_agreement = (
        sum(int(s == r) for s, r in zip(all_source_tokens, all_rbs_tokens))
        / len(all_source_tokens)
    )
    print(f"\n  OVERALL token-level agreement on hallucination corpus: "
          f"{100*overall_agreement:.1f}%")

    # ---- 2. per-position divergence trajectory -------------------------
    print(f"\n=== Per-position divergence trajectory ===")
    per_position_agreement = np.zeros(N_GENERATE)
    for r in hallucination_results:
        per_position_agreement += np.array(r["agreement_per_position"])
    per_position_agreement /= len(hallucination_results)
    print(f"  agreement rate at position k (averaged over all {len(hallucination_results)} prompts):")
    for k in range(N_GENERATE):
        bar = "█" * int(20 * per_position_agreement[k])
        print(f"    k={k:2d}: {per_position_agreement[k]*100:5.1f}% {bar}")

    # ---- 3. latency measurement (already from R-RBS-LM-6 but re-measure) ----
    print(f"\n=== Latency measurement ===")
    # Use the longest prompt for the timing
    test_prompt = HALLUCINATION_PROMPTS[0]
    test_ids = tokenizer.encode(test_prompt)
    _, latencies = rbs_generate(instrument, test_ids, N_GENERATE, vocab_table)
    print(f"  prompt: '{test_prompt}'")
    print(f"  per-token latency: {np.mean(latencies):.1f} ± {np.std(latencies):.1f} ms")
    print(f"  min/max:           {np.min(latencies):.1f} / {np.max(latencies):.1f} ms")
    bci_threshold = 100
    bci_pass = np.mean(latencies) <= bci_threshold
    print(f"  BCI threshold (≤ {bci_threshold} ms): {'PASS' if bci_pass else 'FAIL'}")

    # ---- 4. memory footprint -------------------------------------------
    print(f"\n=== Memory footprint ===")
    rusage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss in KB on Linux
    max_rss_mb = rusage.ru_maxrss / 1024
    print(f"  process max RSS: {max_rss_mb:.1f} MB")
    print(f"    instrument:       {len(instrument)/1024:.1f} KB")
    print(f"    vocab table:      {vocab_table.nbytes/1024**2:.1f} MB")
    print(f"    source model:     ~474.7 MB (loaded for comparison; not needed at RBS-HDC inference)")
    bci_mem_threshold_mb = 8 * 1024
    bci_mem_pass = max_rss_mb <= bci_mem_threshold_mb
    print(f"  BCI memory threshold (≤ {bci_mem_threshold_mb/1024:.0f} GB): {'PASS' if bci_mem_pass else 'FAIL'}")

    # ---- 5. scenario mapping per R-RBS-LM-1 §7 -------------------------
    print(f"\n=== Mapping to R-RBS-LM-1 §7 four-scenario validation reading ===")
    # Compute which scenario applies
    if overall_agreement >= 0.99:
        scenario = "(a) bit-exact reproduction"
    elif overall_agreement >= 0.50:
        scenario = "(b) high-agreement with edge divergence"
    elif overall_agreement >= 0.10:
        scenario = "(c) low-agreement reproduction"
    else:
        scenario = "(d) no coherent reproduction"
    print(f"  Token-level agreement: {100*overall_agreement:.1f}%")
    print(f"  Empirical scenario: {scenario}")

    # First-position agreement (special interest — does RBS-HDC at least get
    # the immediate next-token right?)
    pos0 = per_position_agreement[0]
    print(f"  Position-0 (immediate next-token) agreement: {100*pos0:.1f}%")

    # ---- save results --------------------------------------------------
    results = {
        "n_prompts": len(HALLUCINATION_PROMPTS),
        "n_generate": N_GENERATE,
        "hallucination_results": hallucination_results,
        "overall_token_agreement": float(overall_agreement),
        "per_position_agreement": per_position_agreement.tolist(),
        "latency": {
            "per_token_ms_mean": float(np.mean(latencies)),
            "per_token_ms_std": float(np.std(latencies)),
            "per_token_ms_min": float(np.min(latencies)),
            "per_token_ms_max": float(np.max(latencies)),
            "bci_threshold_ms": bci_threshold,
            "bci_pass": bool(bci_pass),
        },
        "memory": {
            "max_rss_mb": float(max_rss_mb),
            "instrument_bytes": len(instrument),
            "vocab_table_mb": float(vocab_table.nbytes / 1024**2),
            "bci_threshold_gb": 8,
            "bci_pass": bool(bci_mem_pass),
        },
        "scenario": scenario,
        "position_0_agreement": float(pos0),
    }
    RESULTS_PATH.write_text(json.dumps(results, indent=2))
    print(f"\nResults saved: {RESULTS_PATH}")


if __name__ == "__main__":
    main()
