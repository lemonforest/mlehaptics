"""R-RBS-LM-31 — GGUF-aware Path D distillation via llama-cpp-python.

Per user direction 2026-05-25: *"1) do add guff-aware"* (typo: "gguf").

GGUF (formerly GGML) is the file format used by llama.cpp for quantized
weights. A Q4_K_M quantization compresses an N-billion-param model to
~N*0.5 GB (4 bits per weight + overhead) at a small accuracy cost.
Combined with llama.cpp's optimized CPU kernels, this unlocks practical
Path D distillation from 8B / 30B / 70B Llama-class sources on the 2009
Xeon E5530 hardware.

Diff from R-RBS-LM-29's `encode_bytes_variant_b_generic.py`:
  - Uses `llama_cpp.Llama` instead of `transformers.AutoModelForCausalLM`
  - Source identifier is either:
      (a) HuggingFace repo with GGUF files: "user/repo:filename.gguf"
      (b) Local .gguf file path
  - llama-cpp-python downloads from HF Hub automatically when given (a)
  - Same paired-stream output: <prompt> \\x02 <generation> \\x03 (none in
    this script, but the byte stream is identical shape to R-RBS-LM-29)

Per `[[user_stance_ai_is_not_a_substrate]]` continuity: the cascade is
still a transducer. GGUF source is just a different way to read weights;
the model is dropped after corpus is generated; the byte instrument has
zero llama-cpp dependency at serve time.

Hardware tuning:
  - n_ctx: 2048 (default; supports the prompts + max_per_prompt new tokens)
  - n_threads: 16 (matches 8c/16t 2009 Xeon)
  - n_batch: 512 (good default for CPU)

Expected rates on 2009 Xeon E5530 (SSE4.2 only; no AVX):
  - Llama 3.2 1B Q4_K_M:  ~8-12 tok/sec  → 3500 bytes in ~2 min
  - Llama 3.1 8B Q4_K_M:  ~2-3 tok/sec   → 50k bytes in ~50 min
  - Llama 3.1 30B Q4_K_M: ~0.5-1 tok/sec → 50k bytes in ~5 hours
  - Llama 3.1 70B Q4_K_M: ~0.2-0.5 tok/s → 50k bytes in ~11 hours

Usage:
    ~/.venvs/rbs-lm-research/bin/python \\
        docs/srmech/rbs_lm_research/encode_bytes_variant_b_gguf.py \\
        --source-gguf "bartowski/Llama-3.2-1B-Instruct-GGUF:Llama-3.2-1B-Instruct-Q4_K_M.gguf" \\
        --gen-bytes 3500

Or with a local file:
    ~/.venvs/rbs-lm-research/bin/python \\
        docs/srmech/rbs_lm_research/encode_bytes_variant_b_gguf.py \\
        --source-gguf /path/to/model.gguf \\
        --gen-bytes 3500
"""

import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "python"))
sys.path.insert(0, str(HERE))

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


def load_gguf(source_gguf, n_ctx=2048, n_threads=16, verbose=False):
    """Load a GGUF model from either an HF repo:filename spec or a local path."""
    from llama_cpp import Llama

    if ":" in source_gguf and not Path(source_gguf).exists():
        # HF Hub repo:filename pattern
        repo, filename = source_gguf.split(":", 1)
        print(f"  Fetching {filename} from HF repo {repo}...")
        # llama-cpp-python supports from_pretrained for HF GGUF repos
        llm = Llama.from_pretrained(
            repo_id=repo,
            filename=filename,
            n_ctx=n_ctx,
            n_threads=n_threads,
            verbose=verbose,
        )
    else:
        # Local file
        print(f"  Loading local GGUF: {source_gguf}")
        llm = Llama(
            model_path=source_gguf,
            n_ctx=n_ctx,
            n_threads=n_threads,
            verbose=verbose,
        )
    return llm


def generate_corpus_gguf(llm, target_bytes, max_per_prompt=128, verbose=True):
    """Generate a byte-stream corpus using a llama-cpp-python Llama instance."""
    pieces = []
    n_bytes = 0
    prompt_idx = 0
    while n_bytes < target_bytes:
        prompt = GENERATION_PROMPTS[prompt_idx % len(GENERATION_PROMPTS)]
        prompt_idx += 1
        if verbose:
            t0 = time.time()
            print(f"  [{prompt_idx:>2d}] generating from: {prompt[:50]!r}...")
        # llama-cpp-python's call interface — greedy (temperature 0)
        out = llm(
            prompt,
            max_tokens=max_per_prompt,
            temperature=0.0,
            echo=False,
            stop=["</s>", "<|endoftext|>", "<|end_of_text|>"],
        )
        new_text = out["choices"][0]["text"]
        piece = prompt + new_text
        pieces.append(piece)
        n_bytes += len(piece.encode("utf-8"))
        if verbose:
            elapsed = time.time() - t0
            n_new_tokens = out["usage"]["completion_tokens"]
            tok_per_sec = n_new_tokens / max(elapsed, 0.001)
            print(f"      produced {len(new_text)} chars / {n_new_tokens} tok in "
                  f"{elapsed:.0f}s ({tok_per_sec:.1f} tok/sec); "
                  f"cumulative: {n_bytes}/{target_bytes}")
    return "\n\n".join(pieces)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-gguf", required=True,
                        help="HF repo:filename or local .gguf path")
    parser.add_argument("--gen-bytes", type=int, default=3500)
    parser.add_argument("--stride", type=int, default=8)
    parser.add_argument("--max-per-prompt", type=int, default=128)
    parser.add_argument("--n-ctx", type=int, default=2048)
    parser.add_argument("--n-threads", type=int, default=16)
    parser.add_argument("--out", default=None)
    parser.add_argument("--est-model-gb", type=float, default=1.0,
                        help="Estimated GGUF size in GB for precheck (default 1.0)")
    parser.add_argument("--label", default=None,
                        help="Short label for output filename (default derives from source)")
    args = parser.parse_args()

    print(f"=== R-RBS-LM-31 — GGUF Path D distillation ===")
    print(f"  source-gguf: {args.source_gguf}")
    print(f"  n_ctx: {args.n_ctx}; n_threads: {args.n_threads}")
    print(f"  target gen bytes: {args.gen_bytes}")

    # ---- Disk precheck ----
    print(f"\n=== Disk precheck ({args.est_model_gb} GB + 1 GB margin) ===")
    precheck_fetch(
        estimated_bytes=int(args.est_model_gb * 1024**3),
        safety_margin_gb=1.0,
        label=f"GGUF fetch: {args.source_gguf}",
    )
    print(f"  PASS")

    # ---- Load model ----
    print(f"\n=== Load GGUF model ===")
    t0 = time.time()
    llm = load_gguf(args.source_gguf, n_ctx=args.n_ctx, n_threads=args.n_threads)
    print(f"  load time: {time.time() - t0:.1f}s")

    # ---- Generate corpus ----
    print(f"\n=== Generate corpus ===")
    t0 = time.time()
    full_text = generate_corpus_gguf(
        llm, target_bytes=args.gen_bytes, max_per_prompt=args.max_per_prompt,
    )
    gen_t = time.time() - t0
    print(f"  total chars: {len(full_text):,}")
    print(f"  total bytes: {len(full_text.encode('utf-8')):,}")
    print(f"  generation time: {gen_t:.0f}s ({gen_t/60:.1f} min)")

    # Drop model — Path D principle
    del llm

    # ---- Retokenize as UTF-8 bytes ----
    all_bytes = text_to_bytes(full_text)
    print(f"\n=== Retokenize as UTF-8 bytes ===")
    print(f"  byte stream: {len(all_bytes):,} bytes")

    # ---- Build vocab + harvest ----
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

    # ---- Encode + bundle ----
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

    # ---- Save ----
    label = args.label or args.source_gguf.replace("/", "__").replace(":", "__")
    out = args.out or f"docs/srmech/rbs_lm_research/rbs_lm_instrument_v31_gguf_{label}.bin"
    out_path = Path(out)
    out_path.write_bytes(instrument)
    print(f"\n  saved: {out_path}")

    corpus_path = out_path.with_suffix(".corpus.txt")
    corpus_path.write_text(full_text)
    print(f"  corpus: {corpus_path}")

    meta = {
        "partition": "R-RBS-LM-31",
        "variant": "gguf_path_d_distillation",
        "source_gguf": args.source_gguf,
        "n_ctx": args.n_ctx,
        "n_threads": args.n_threads,
        "gen_target_bytes": args.gen_bytes,
        "gen_actual_bytes": len(all_bytes),
        "n_generation_prompts": len(GENERATION_PROMPTS),
        "max_per_prompt": args.max_per_prompt,
        "n_observations": len(observations),
        "stride": args.stride,
        "instrument_bytes": len(instrument),
        "D": D,
        "context_window_bytes": CONTEXT_WINDOW,
        "vocab_size": BYTE_VOCAB_SIZE,
        "tokenizer_at_inference_time": "utf-8 bytes (no GGUF dependency at serve time)",
        "encode_seconds": enc_t,
        "bundle_seconds": bnd_t,
        "generation_seconds": gen_t,
    }
    Path(out_path.with_suffix(".meta.json")).write_text(json.dumps(meta, indent=2))
    print(f"  metadata: {out_path.with_suffix('.meta.json')}")


if __name__ == "__main__":
    main()
