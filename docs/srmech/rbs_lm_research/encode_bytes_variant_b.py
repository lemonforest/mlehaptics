"""R-RBS-LM-25 — Variant B: Distill BPE source to byte-level (Path D).

Per user direction 2026-05-25: *"if we can make every existing BPE model
become byte level is what I'm hoping to find out because we remove
english privilage."*

The procedure:

  1. Load a BPE-trained source model (GPT-2 here; same procedure works for
     any BPE-trained model). The source model contributes generation
     content; its tokenization is stripped in step 2.
  2. Generate a corpus from the source model across diverse prompts.
  3. RETOKENIZE the generated text as UTF-8 bytes — BPE tokens are
     dropped; the byte stream IS the training signal.
  4. Encode (byte_context, next_byte) bindings into an RBS-HDC instrument
     using the byte-level vocab (256 Class A mints) — NO WTE projection,
     NO BPE tokens, NO source-model dependency at inference time.

The resulting instrument:
  - Has byte-level vocab (256 rows, 256 KB)
  - Has byte-level inference (no GPT-2 dependency at serve time)
  - Carries content from a BPE-trained model but WITHOUT its tokenization
    privilege — the English-distribution bias baked into BPE merges is
    structurally absent.

Honest expectations per `[[user_stance_ai_is_not_a_substrate]]` and the
discrete-cascade structural ceiling (R-RBS-LM-19 falsification):
  - 3.3%-style agreement ceiling will hold (rotation in wet nets isn't
    replicable in discrete cascades; byte-level doesn't change that)
  - What changes: LANGUAGE COVERAGE + smaller vocab + zero serve-time
    teacher-model dependency
  - What we learn: whether the byte-byte transition signal from GPT-2's
    GENERATED text is encodable + recoverable at our scale

Usage:
    ~/.venvs/rbs-lm-research/bin/python \\
        docs/srmech/rbs_lm_research/encode_bytes_variant_b.py \\
        --gen-bytes 10000
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
    bytes_to_text,
)


# Diverse prompts to elicit varied byte transitions from the source model.
# Intentionally mix topics + structures (narrative, technical, dialogue, code)
# so the byte stream covers a range of patterns rather than mode-collapsing.
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


def generate_corpus(model, tokenizer, target_bytes, max_per_prompt=200, verbose=True):
    """Generate a byte-stream corpus from a BPE-trained source model.

    Cycles through GENERATION_PROMPTS, generating max_per_prompt new tokens
    each, until we have at least target_bytes worth of byte-encoded output.
    """
    pieces = []
    n_bytes = 0
    prompt_idx = 0
    while n_bytes < target_bytes:
        prompt = GENERATION_PROMPTS[prompt_idx % len(GENERATION_PROMPTS)]
        prompt_idx += 1
        if verbose:
            print(f"  generating from prompt: {prompt[:50]!r}...")
        prompt_ids = tokenizer.encode(prompt)
        with torch.no_grad():
            out = model.generate(
                torch.tensor([prompt_ids]),
                max_new_tokens=max_per_prompt,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
            )
        new_tokens = out[0][len(prompt_ids):].tolist()
        new_text = tokenizer.decode(new_tokens)
        piece = prompt + new_text
        pieces.append(piece)
        n_bytes += len(piece.encode("utf-8"))
        if verbose:
            print(f"    produced {len(new_text)} chars; "
                  f"cumulative bytes: {n_bytes}/{target_bytes}")

    full_text = "\n\n".join(pieces)
    return full_text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-model", default="gpt2",
                        help="HF BPE-trained source model (default gpt2)")
    parser.add_argument("--gen-bytes", type=int, default=10000,
                        help="Target byte count for the generated corpus")
    parser.add_argument("--stride", type=int, default=16)
    parser.add_argument("--max-per-prompt", type=int, default=200,
                        help="Max new tokens per generation call")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    print(f"=== R-RBS-LM-25 Variant B — Distill {args.source_model} to byte-level (Path D) ===")
    print(f"  D = {D}; CONTEXT_WINDOW = {CONTEXT_WINDOW} bytes; V = {BYTE_VOCAB_SIZE}")
    print(f"  target gen bytes: {args.gen_bytes}")

    # ---- 1. Load source model (only to generate; no WTE projection) -----
    print(f"\n=== Load source model + tokenizer ===")
    from transformers import GPT2LMHeadModel, GPT2Tokenizer
    tokenizer = GPT2Tokenizer.from_pretrained(args.source_model)
    model = GPT2LMHeadModel.from_pretrained(args.source_model)
    model.eval()
    print(f"  loaded {args.source_model}")

    # ---- 2. Generate corpus from source model -------------------------
    print(f"\n=== Generate corpus from source ===")
    t0 = time.time()
    full_text = generate_corpus(model, tokenizer,
                                 target_bytes=args.gen_bytes,
                                 max_per_prompt=args.max_per_prompt)
    gen_t = time.time() - t0
    print(f"  total chars: {len(full_text):,}")
    print(f"  total bytes: {len(full_text.encode('utf-8')):,}")
    print(f"  generation time: {gen_t:.1f}s")

    # We don't need the source model anymore (only used it for generation;
    # tokenizer dropped too — the resulting instrument is BPE-free)
    del model, tokenizer

    # ---- 3. Retokenize as UTF-8 bytes (BPE tokens DROPPED) ------------
    all_bytes = text_to_bytes(full_text)
    print(f"\n=== Retokenize as UTF-8 bytes (no BPE) ===")
    print(f"  byte stream: {len(all_bytes):,} bytes")

    # ---- 4. Build byte vocab table (256 Class A mints) ----------------
    print(f"\n=== Build byte vocab table ===")
    vocab_table = compute_byte_vocab_table(D)
    print(f"  vocab table: {vocab_table.shape}; {vocab_table.nbytes/1024:.1f} KB")

    # ---- 5. Harvest (byte_context, next_byte) pairs --------------------
    print(f"\n=== Harvest byte-transition pairs (stride {args.stride}) ===")
    observations = []
    for i in range(0, len(all_bytes) - CONTEXT_WINDOW, args.stride):
        ctx = all_bytes[i:i + CONTEXT_WINDOW]
        nxt = all_bytes[i + CONTEXT_WINDOW]
        observations.append((ctx, nxt))
    print(f"  observations: {len(observations)}")

    # ---- 6. Encode + bundle into instrument ---------------------------
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

    out = args.out or f"docs/srmech/rbs_lm_research/rbs_lm_instrument_v25b_distill_{args.source_model}.bin"
    out_path = Path(out)
    out_path.write_bytes(instrument)
    print(f"  saved: {out_path}")

    # ---- 7. Save generated corpus + metadata ---------------------------
    corpus_path = out_path.with_suffix(".corpus.txt")
    corpus_path.write_text(full_text)
    print(f"  corpus: {corpus_path}")

    meta = {
        "partition": "R-RBS-LM-25",
        "variant": "B_distill_bpe_to_byte_level_path_d",
        "source_model": args.source_model,
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
        "tokenizer_at_inference_time": "utf-8 (no BPE, no GPT-2)",
        "tokenizer_used_for_generation_only": args.source_model + " BPE",
        "framework_reading": (
            "Path D — BPE source distilled to byte-level instrument. "
            "Source model used to PRODUCE corpus; its tokenization is "
            "stripped via retokenize_as_utf8_bytes. The resulting "
            "instrument has zero dependency on BPE tokenization at "
            "inference time — English privilege removed."
        ),
        "encode_seconds": enc_t,
        "bundle_seconds": bnd_t,
        "generation_seconds": gen_t,
    }
    Path(out_path.with_suffix(".meta.json")).write_text(json.dumps(meta, indent=2))
    print(f"  metadata: {out_path.with_suffix('.meta.json')}")

    print(f"\n=== Done. Load this BPE-stripped instrument via: ===")
    print(f"  RBS_LM_INSTRUMENT={out_path} \\")
    print(f"    RBS_LM_BYTE_MODE=1 \\")
    print(f"    ~/.venvs/rbs-lm-research/bin/python "
          f"docs/srmech/rbs_lm_research/rbs_lm_server.py")


if __name__ == "__main__":
    main()
