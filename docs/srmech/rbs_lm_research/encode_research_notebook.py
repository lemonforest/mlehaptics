"""R-RBS-LM-24 — GPU-less learning: encode research-notebook text directly.

Per `[[user_stance_learning_without_gpu_compute]]`: the harvest bottleneck
disappears when the (context, next_token) signal comes from the actual
notebook text rather than from a teacher model's argmax. No `model.generate()`
calls during harvest — just tokenize + slide window.

Distinction from R-RBS-LM-17/-18/-20:
  - Path C (R-RBS-LM-17): teacher-model argmax labels each context → bind
  - GPU-less (this script): actual next-token in notebook text labels each
    context → bind

Both share the Path C vocab table (WTE-projected; preserves semantic
similarity at the token level) — the WTE matmul is CPU-side, no GPU needed.
The only place GPT-2 was load-bearing during harvest was the per-context
forward pass; this script drops that.

Structural framing per `[[user_stance_ai_is_not_a_substrate]]`: the
local expert remains a transducer. Encoding the notebook as training
material does NOT make it "know" the framework in any substrate sense —
it stores statistical structure of token sequences. The framework
reading IS unchanged.

Usage:
    ~/.venvs/rbs-lm-research/bin/python \\
        docs/srmech/rbs_lm_research/encode_research_notebook.py \\
        --notebook docs/srmech/srmech_research_notebook.md \\
        --max-tokens 5000
"""

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "python"))
sys.path.insert(0, str(HERE))

torch.set_num_threads(16)

from rbs_lm_encoder import CONTEXT_WINDOW, D, hierarchical_bundle  # noqa: E402
from rbs_lm_path_c import (  # noqa: E402
    compute_path_c_vocab_table,
    encode_observation_path_c,
)


def harvest_from_text(text, tokenizer, max_tokens, stride, verbose=True):
    """Tokenize text + slide context window. Each window position yields a
    (context, next_token) pair where next_token IS the actual next token in
    the text (no teacher model forward pass).
    """
    all_tokens = tokenizer.encode(text)
    if verbose:
        print(f"  notebook tokens: {len(all_tokens)} total")
    all_tokens = all_tokens[:max_tokens]
    if verbose:
        print(f"  using first {len(all_tokens)} tokens (--max-tokens cap)")

    observations = []
    for i in range(0, len(all_tokens) - CONTEXT_WINDOW, stride):
        ctx = all_tokens[i:i + CONTEXT_WINDOW]
        nxt = all_tokens[i + CONTEXT_WINDOW]
        observations.append((ctx, nxt))
    if verbose:
        print(f"  observations (stride {stride}): {len(observations)}")
    return observations, all_tokens


def main():
    parser = argparse.ArgumentParser(description="GPU-less learning from a research notebook")
    parser.add_argument("--notebook", default="docs/srmech/srmech_research_notebook.md",
                        help="Path to notebook .md file")
    parser.add_argument("--max-tokens", type=int, default=5000,
                        help="Cap on notebook tokens to encode (default 5000)")
    parser.add_argument("--stride", type=int, default=8,
                        help="Stride between contexts (default 8)")
    parser.add_argument("--out", default=None,
                        help="Output instrument path (default derives from notebook name)")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    print(f"=== R-RBS-LM-24 — GPU-less learning from {args.notebook} ===")
    print(f"  torch threads: {torch.get_num_threads()}; D = {D}; CONTEXT_WINDOW = {CONTEXT_WINDOW}")

    if not Path(args.notebook).exists():
        raise FileNotFoundError(f"notebook not found: {args.notebook}")
    text = Path(args.notebook).read_text()
    print(f"  notebook chars: {len(text):,}")

    notebook_slug = Path(args.notebook).stem.replace("_research_notebook", "").replace("_", "-")
    if args.out is None:
        args.out = f"docs/srmech/rbs_lm_research/rbs_lm_instrument_v24_{notebook_slug}.bin"

    # ---- 1. load tokenizer + GPT-2 for WTE matrix (CPU only) -----------
    print(f"\nLoading tokenizer + WTE (no .generate() calls — GPU-less harvest)...")
    tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
    model = GPT2LMHeadModel.from_pretrained("gpt2")
    model.eval()

    # ---- 2. compute Path C vocab table (CPU matmul) --------------------
    vocab_table_pc = compute_path_c_vocab_table(model, D=D, seed=args.seed)
    del model  # drop weights; we only needed WTE for the projection
    print(f"  source model dropped; only tokenizer + vocab table held")

    # ---- 3. harvest from notebook text (no model forward) --------------
    print(f"\n=== Harvest (GPU-less; next-token from actual text) ===")
    observations, all_tokens = harvest_from_text(text, tokenizer, args.max_tokens, args.stride)

    # ---- 4. encode + bundle into instrument ----------------------------
    print(f"\n=== Encode + bundle ===")
    t0 = time.time()
    bindings = [
        encode_observation_path_c(ctx, nxt, vocab_table_pc, D)
        for ctx, nxt in observations
    ]
    encode_time = time.time() - t0
    print(f"  {len(bindings)} bindings in {encode_time:.1f}s "
          f"({len(bindings)/encode_time:.1f}/s, single-thread)")

    t0 = time.time()
    instrument = hierarchical_bundle(bindings)
    bundle_time = time.time() - t0
    print(f"  bundle: {bundle_time:.2f}s; instrument = {len(instrument)} bytes")

    out_path = Path(args.out)
    out_path.write_bytes(instrument)
    print(f"  saved: {out_path}")

    # ---- 5. metadata snapshot ------------------------------------------
    meta = {
        "partition": "R-RBS-LM-24",
        "experiment": "gpu_less_learning_from_notebook",
        "notebook_path": args.notebook,
        "notebook_chars": len(text),
        "notebook_tokens_used": len(all_tokens),
        "max_tokens_cap": args.max_tokens,
        "stride": args.stride,
        "n_observations": len(observations),
        "instrument_bytes": len(instrument),
        "D": D,
        "context_window": CONTEXT_WINDOW,
        "vocab_table_method": "path_c_wte_random_projection_seed42",
        "harvest_method": "text_self_supervised_no_teacher_forward_pass",
        "encode_seconds": encode_time,
        "bundle_seconds": bundle_time,
    }
    meta_path = out_path.with_suffix(".meta.json")
    meta_path.write_text(json.dumps(meta, indent=2))
    print(f"  metadata: {meta_path}")

    print(f"\n=== Done. Load via: ===")
    print(f"  RBS_LM_INSTRUMENT={out_path} \\")
    print(f"    ~/.venvs/rbs-lm-research/bin/python "
          f"docs/srmech/rbs_lm_research/rbs_lm_server.py")


if __name__ == "__main__":
    main()
