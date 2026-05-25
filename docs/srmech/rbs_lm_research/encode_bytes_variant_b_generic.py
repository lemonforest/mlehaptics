"""R-RBS-LM-29 — Generic Path D distillation: any HuggingFace CausalLM source.

Generalizes R-RBS-LM-25's encode_bytes_variant_b.py (GPT2-specific) to any
HuggingFace `AutoModelForCausalLM` + `AutoTokenizer` source. Same Path D
discipline: model is used ONLY to generate; its tokenization is stripped
when we re-tokenize the generated text as UTF-8 bytes.

Per user direction 2026-05-25: *"could these also be due to the small
model we are starting with? like maybe it's time to grab a llama model
that will fit on our storage device until we can delete it when we
finish making it RBS-LM?"*

The hypothesis under test: does a modern small-LLM source (TinyLlama 1.1B,
Llama 3.2 1B, Phi-2, etc.) lift the cascade out of the single-byte mode-
collapse pattern observed in R-RBS-LM-25 with GPT-2 124M source? Either
outcome informative:

  - YES (different mode-collapse pattern): source-model richness matters;
    the cascade was source-starved, not structurally bounded.
  - NO (same mode-collapse pattern): cascade IS the bottleneck per R-RBS-LM-19;
    source-model scaling is orthogonal to cascade limits at this scale.

Per `[[user_stance_ai_is_not_a_substrate]]`: the cascade stays a transducer
regardless of source. We're testing what TRAINING CORPUS shape the cascade
can absorb, not making the cascade smarter.

Usage:
    ~/.venvs/rbs-lm-research/bin/python \\
        docs/srmech/rbs_lm_research/encode_bytes_variant_b_generic.py \\
        --source-model TinyLlama/TinyLlama-1.1B-intermediate-step-1431k-3T \\
        --gen-bytes 3500
"""

import argparse
import json
import sys
import time
from pathlib import Path

import torch

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "python"))
sys.path.insert(0, str(HERE))

torch.set_num_threads(16)

from rbs_lm_encoder import CONTEXT_WINDOW, D, hierarchical_bundle  # noqa: E402
from rbs_lm_bytes import (  # noqa: E402
    BYTE_VOCAB_SIZE,
    compute_byte_vocab_table,
    encode_observation_bytes,
    text_to_bytes,
)
from storage_management import precheck_fetch  # noqa: E402


GENERATION_PROMPTS = [
    "The history of computing begins not with electronics but with",
    "Photosynthesis converts light energy into chemical energy stored in",
    "Algorithms for sorting have been studied for decades. Quicksort",
    "The chef tasted the soup, frowned slightly, and reached for the salt",
    "Migration patterns of monarch butterflies span thousands of miles",
    "Public-key cryptography enables secure communication between",
    "Climate models simulate the atmosphere through coupled differential",
    "The library at Alexandria held perhaps half a million scrolls",
    "Once upon a time, in a forest made of clockwork, lived a small",
    "Container orchestration platforms manage the lifecycle of",
    "def fibonacci(n):",
    "Database transactions enforce four properties known as ACID",
]


def generate_corpus_generic(model, tokenizer, target_bytes, max_per_prompt=80,
                              verbose=True):
    """Generic generation from any HuggingFace AutoModelForCausalLM."""
    pieces = []
    n_bytes = 0
    prompt_idx = 0
    eos_id = (tokenizer.eos_token_id
              if tokenizer.eos_token_id is not None
              else tokenizer.pad_token_id)
    while n_bytes < target_bytes:
        prompt = GENERATION_PROMPTS[prompt_idx % len(GENERATION_PROMPTS)]
        prompt_idx += 1
        if verbose:
            t0 = time.time()
            print(f"  [{prompt_idx:>2d}] generating from: {prompt[:50]!r}...")
        input_ids = tokenizer.encode(prompt, return_tensors="pt")
        with torch.no_grad():
            out = model.generate(
                input_ids,
                max_new_tokens=max_per_prompt,
                do_sample=False,
                pad_token_id=eos_id,
            )
        new_tokens = out[0][input_ids.shape[1]:].tolist()
        new_text = tokenizer.decode(new_tokens, skip_special_tokens=True)
        piece = prompt + new_text
        pieces.append(piece)
        n_bytes += len(piece.encode("utf-8"))
        if verbose:
            elapsed = time.time() - t0
            print(f"      produced {len(new_text)} chars in {elapsed:.0f}s; "
                  f"cumulative: {n_bytes}/{target_bytes}")
    full_text = "\n\n".join(pieces)
    return full_text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-model", required=True,
                        help="HuggingFace model id (e.g., TinyLlama/TinyLlama-1.1B-...)")
    parser.add_argument("--gen-bytes", type=int, default=3500,
                        help="Target byte count for the generated corpus")
    parser.add_argument("--stride", type=int, default=8)
    parser.add_argument("--max-per-prompt", type=int, default=80)
    parser.add_argument("--out", default=None)
    parser.add_argument("--est-model-gb", type=float, default=3.0,
                        help="Estimated model size in GB for precheck (default 3.0)")
    args = parser.parse_args()

    print(f"=== R-RBS-LM-29 — Generic Path D distillation ===")
    print(f"  source-model: {args.source_model}")
    print(f"  D = {D}; CONTEXT_WINDOW = {CONTEXT_WINDOW} bytes; V = {BYTE_VOCAB_SIZE}")
    print(f"  target gen bytes: {args.gen_bytes}")

    # ---- 0. Disk precheck per R-RBS-LM-22 ----------------------------
    print(f"\n=== Disk precheck ({args.est_model_gb} GB + 1 GB margin) ===")
    precheck_fetch(
        estimated_bytes=int(args.est_model_gb * 1024**3),
        safety_margin_gb=1.0,
        label=f"fetch of {args.source_model}",
    )
    print(f"  PASS")

    # ---- 1. Fetch source + tokenizer ---------------------------------
    print(f"\n=== Fetch {args.source_model} ===")
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(args.source_model)
    model = AutoModelForCausalLM.from_pretrained(args.source_model,
                                                  torch_dtype=torch.float32)
    model.eval()
    n_params = sum(p.numel() for p in model.parameters())
    print(f"  loaded: {n_params/1e6:.0f}M params")

    # ---- 2. Generate corpus ------------------------------------------
    print(f"\n=== Generate corpus ===")
    t0 = time.time()
    full_text = generate_corpus_generic(
        model, tokenizer, target_bytes=args.gen_bytes,
        max_per_prompt=args.max_per_prompt,
    )
    gen_t = time.time() - t0
    print(f"  total chars: {len(full_text):,}")
    print(f"  total bytes: {len(full_text.encode('utf-8')):,}")
    print(f"  generation time: {gen_t:.0f}s ({gen_t/60:.1f} min)")

    # Drop source — Path D principle: BPE tokenization stripped
    del model, tokenizer

    # ---- 3. Retokenize as UTF-8 bytes (source's tokens dropped) -------
    all_bytes = text_to_bytes(full_text)
    print(f"\n=== Retokenize as UTF-8 bytes (source tokenization stripped) ===")
    print(f"  byte stream: {len(all_bytes):,} bytes")

    # ---- 4. Build byte vocab + harvest -------------------------------
    print(f"\n=== Build byte vocab table ===")
    vocab_table = compute_byte_vocab_table(D)
    print(f"  vocab table: {vocab_table.shape}; {vocab_table.nbytes/1024:.1f} KB")

    print(f"\n=== Harvest (stride {args.stride}) ===")
    observations = []
    for i in range(0, len(all_bytes) - CONTEXT_WINDOW, args.stride):
        ctx = all_bytes[i:i + CONTEXT_WINDOW]
        nxt = all_bytes[i + CONTEXT_WINDOW]
        observations.append((ctx, nxt))
    print(f"  observations: {len(observations)}")

    # ---- 5. Encode + bundle -------------------------------------------
    print(f"\n=== Encode + bundle ===")
    t0 = time.time()
    bindings = [
        encode_observation_bytes(ctx, nxt, vocab_table, D)
        for ctx, nxt in observations
    ]
    enc_t = time.time() - t0
    print(f"  {len(bindings)} bindings in {enc_t:.1f}s ({len(bindings)/enc_t:.1f}/s)")

    t0 = time.time()
    instrument = hierarchical_bundle(bindings)
    bnd_t = time.time() - t0
    print(f"  bundle: {bnd_t:.2f}s; instrument = {len(instrument)} bytes")

    # ---- 6. Save -----------------------------------------------------
    safe_src = args.source_model.replace("/", "__")
    out = args.out or f"docs/srmech/rbs_lm_research/rbs_lm_instrument_v29_distill_{safe_src}.bin"
    out_path = Path(out)
    out_path.write_bytes(instrument)
    print(f"\n  saved: {out_path}")

    corpus_path = out_path.with_suffix(".corpus.txt")
    corpus_path.write_text(full_text)
    print(f"  corpus: {corpus_path}")

    meta = {
        "partition": "R-RBS-LM-29",
        "variant": "generic_path_d_distillation",
        "source_model": args.source_model,
        "source_n_params": n_params,
        "gen_target_bytes": args.gen_bytes,
        "gen_actual_bytes": len(all_bytes),
        "n_generation_prompts": len(GENERATION_PROMPTS),
        "max_new_tokens_per_prompt": args.max_per_prompt,
        "n_observations": len(observations),
        "stride": args.stride,
        "instrument_bytes": len(instrument),
        "D": D,
        "context_window_bytes": CONTEXT_WINDOW,
        "vocab_size": BYTE_VOCAB_SIZE,
        "vocab_method": "class_a_content_mint_byte_<n>",
        "tokenizer_at_inference_time": "utf-8 (no source-model BPE/SentencePiece)",
        "tokenizer_used_for_generation_only": args.source_model + " (stripped)",
        "encode_seconds": enc_t,
        "bundle_seconds": bnd_t,
        "generation_seconds": gen_t,
        "framework_reading": (
            "Path D distillation from a modern small-LLM source. The "
            "source model was loaded, used to generate corpus, then "
            "dropped. The resulting instrument has byte-level inference "
            "with ZERO dependency on the source's tokenization. Per "
            "[[user_stance_ai_is_not_a_substrate]]: the cascade is still "
            "a transducer; this experiment tests whether source-model "
            "richness affects the cascade's mode-collapse pattern."
        ),
    }
    Path(out_path.with_suffix(".meta.json")).write_text(json.dumps(meta, indent=2))
    print(f"  metadata: {out_path.with_suffix('.meta.json')}")


if __name__ == "__main__":
    main()
