"""R-RBS-LM-18 — Path C at 491-obs scale.

Tests whether the 3.3% Path C agreement signal from R-RBS-LM-17 (109 obs)
scales monotonically with corpus size. Uses the R-RBS-LM-14 corpus
(~20 KB / 491 obs) which Path B failed (0%).

Three possible outcomes:
  - Agreement > 3.3% → Path C scales; cross-substrate translation viable
  - Agreement ≈ 3.3% → plateau; need additional architecture
  - Agreement < 3.3% → scale hurts (unexpected); diagnose

Reuses the rbs_lm_path_c module's encode + cleanup + WTE-projection
infrastructure; only the corpus changes.

Usage:
    ~/.venvs/rbs-lm-research/bin/python \\
        docs/srmech/rbs_lm_research/run_path_c_scale.py
"""

import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer

sys.path.insert(0, "docs/srmech/python")
sys.path.insert(0, "docs/srmech/rbs_lm_research")

torch.set_num_threads(16)

from rbs_lm_encoder import CONTEXT_WINDOW, D, bind, hierarchical_bundle  # noqa: E402
from rbs_lm_inference import vectorised_cleanup  # noqa: E402
from rbs_lm_path_c import (  # noqa: E402
    compute_path_c_vocab_table,
    encode_context_path_c,
    encode_observation_path_c,
)

# Pull the larger corpus from R-RBS-LM-14's runner
from run_scale_genuine_mt import CORPUS_TEXT, HALLUCINATION_PROMPTS  # noqa: E402


def main():
    print(f"=== R-RBS-LM-18 — Path C at scale (corpus from R-RBS-LM-14) ===")
    print(f"  torch threads: {torch.get_num_threads()}")
    print(f"  D = {D}, CONTEXT_WINDOW = {CONTEXT_WINDOW}")
    print(f"  Corpus chars: {len(CORPUS_TEXT):,}")

    print("\nLoading source model...")
    tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
    model = GPT2LMHeadModel.from_pretrained("gpt2")
    model.eval()

    print(f"\nComputing Path C vocab table...")
    vocab_table_pc = compute_path_c_vocab_table(model, D=D, seed=42)

    # ---- harvest -----------------------------------------------------
    print(f"\n=== Harvest (batched) ===")
    all_tokens = tokenizer.encode(CORPUS_TEXT)
    print(f"  corpus: {len(all_tokens)} tokens")
    stride = 8
    contexts = [
        all_tokens[i:i + CONTEXT_WINDOW]
        for i in range(0, len(all_tokens) - CONTEXT_WINDOW, stride)
    ]
    print(f"  target observations: {len(contexts)}")
    observations = []
    t0 = time.time()
    batch_size = 32
    for batch_start in range(0, len(contexts), batch_size):
        batch = contexts[batch_start: batch_start + batch_size]
        input_ids = torch.tensor(batch)
        with torch.no_grad():
            logits = model(input_ids).logits
        nexts = logits[:, -1, :].argmax(dim=-1).tolist()
        for ctx, nxt in zip(batch, nexts):
            observations.append((ctx, int(nxt)))
    harvest_time = time.time() - t0
    print(f"  harvested {len(observations)} obs in {harvest_time:.0f}s "
          f"({len(observations)/harvest_time:.1f}/s)")

    # ---- encode using Path C -----------------------------------------
    print(f"\n=== Encode (Path C vocab + Path B compute, single-thread) ===")
    t0 = time.time()
    bindings = [
        encode_observation_path_c(ctx, nxt, vocab_table_pc)
        for ctx, nxt in observations
    ]
    encode_time = time.time() - t0
    print(f"  {len(bindings)} bindings in {encode_time:.1f}s "
          f"({len(bindings)/encode_time:.1f}/s)")

    t0 = time.time()
    instrument = hierarchical_bundle(bindings)
    bundle_time = time.time() - t0
    print(f"  bundle: {bundle_time:.2f}s; instrument = {len(instrument)} bytes")

    out_path = Path("docs/srmech/rbs_lm_research/rbs_lm_instrument_v18.bin")
    out_path.write_bytes(instrument)
    print(f"  saved: {out_path}")

    # ---- validate ----------------------------------------------------
    print(f"\n=== Validate on hallucination corpus ===")
    n_total = 0
    n_agree = 0
    latencies = []
    per_prompt_results = []
    for prompt in HALLUCINATION_PROMPTS:
        prompt_ids = tokenizer.encode(prompt)
        with torch.no_grad():
            src_out = model.generate(
                torch.tensor([prompt_ids]),
                max_new_tokens=20,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
            )
        src_new = src_out[0][len(prompt_ids):].tolist()

        rbs_tokens = list(prompt_ids)
        prompt_lats = []
        for _ in range(20):
            t0 = time.time()
            ctx = rbs_tokens[-CONTEXT_WINDOW:] if len(rbs_tokens) > CONTEXT_WINDOW else rbs_tokens
            ctx_vec = encode_context_path_c(ctx, vocab_table_pc)
            cand = bind(instrument, ctx_vec)
            res = vectorised_cleanup(cand, vocab_table_pc, D, top_k=1)
            rbs_tokens.append(res[0][0])
            prompt_lats.append((time.time() - t0) * 1000)
        rbs_new = rbs_tokens[len(prompt_ids):]
        latencies.extend(prompt_lats)
        agreement = [int(s == r) for s, r in zip(src_new, rbs_new)]
        n_total += len(agreement)
        n_agree += sum(agreement)
        per_prompt_results.append({
            "prompt": prompt,
            "source_decoded": tokenizer.decode(src_new),
            "rbs_decoded": tokenizer.decode(rbs_new),
            "agreement": sum(agreement),
        })
        print(f"  '{prompt[:40]}...' → agreement {sum(agreement)}/20")
        if sum(agreement) > 0:
            print(f"    src:  {tokenizer.decode(src_new)[:80]}")
            print(f"    RBS:  {tokenizer.decode(rbs_new)[:80]}")

    overall = n_agree / n_total
    print(f"\n  Overall: {n_agree}/{n_total} ({100*overall:.1f}%)")
    print(f"  Per-token latency: {np.mean(latencies):.1f} ± {np.std(latencies):.1f} ms")

    print(f"\n=== Path B vs Path C scaling ===")
    print(f"  {'Configuration':<60} {'n_obs':>7} {'agreement':>12}")
    print(f"  {'Path B at 491 obs (R-RBS-LM-14)':<60} {'491':>7} {'0.0%':>12}")
    print(f"  {'Path C at 109 obs (R-RBS-LM-17)':<60} {'109':>7} {'3.3%':>12}")
    print(f"  {'Path C at 491 obs (R-RBS-LM-18, this run)':<60} {len(observations):>7} "
          f"{100*overall:>11.1f}%")

    # Save results
    results = {
        "partition": "R-RBS-LM-18",
        "n_observations": len(observations),
        "instrument_bytes": len(instrument),
        "overall_agreement_pct": 100 * overall,
        "latency_ms_mean": float(np.mean(latencies)),
        "per_prompt_results": per_prompt_results,
        "comparison": {
            "path_b_491obs_pct": 0.0,
            "path_c_109obs_pct": 3.3,
            "path_c_491obs_pct": 100 * overall,
        },
    }
    Path("docs/srmech/rbs_lm_research/rbs_lm_path_c_scale_results.json").write_text(
        json.dumps(results, indent=2)
    )
    print(f"\nResults saved.")


if __name__ == "__main__":
    main()
