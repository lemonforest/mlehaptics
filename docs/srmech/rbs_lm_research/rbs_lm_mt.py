"""R-RBS-LM-11 — Multi-threaded harvest + encode for the 2009 Xeon E5530 envelope.

Implements the three opportunities from HARDWARE_AND_THREADING.md §2:

  Opp 1 — torch.set_num_threads(16) — use all 16 hyperthreads (HT-aware)
  Opp 2 — multiprocessing.Pool over encode_observation across CPU cores
  Opp 3 — batched GPT-2 forward pass during harvest

Used by R-RBS-LM-11 to re-run at ~10× corpus scale where R-RBS-LM-9
Path α stopped at 3× scale due to wall-time budget.

Usage:
    from rbs_lm_mt import harvest_corpus_mt, encode_corpus_mt
    ...

The module is a wrapper around the original rbs_lm_encoder API; the
encode_observation / hierarchical_bundle / vocab_vec primitives are
unchanged.
"""

import os
import sys
import time
from typing import Sequence

import numpy as np
import torch

sys.path.insert(0, "docs/srmech/python")
sys.path.insert(0, "docs/srmech/rbs_lm_research")

# Set torch threads early — before model load — so BLAS picks it up.
# HW: 16 hyperthreads (8 physical cores × 2 HT) per HARDWARE_AND_THREADING.md §1.
TORCH_THREADS = 16
torch.set_num_threads(TORCH_THREADS)

from rbs_lm_encoder import (  # noqa: E402
    CONTEXT_WINDOW,
    D,
    encode_observation,
    hierarchical_bundle,
)


# -- Opp 3: batched GPT-2 forward pass --------------------------------------
def harvest_corpus_mt(text, tokenizer, model, stride=8, batch_size=32, label=""):
    """Harvest (context, argmax_next_token) observations from source model
    using batched forward passes.

    Per HARDWARE_AND_THREADING.md §2.2 Opp 3: batching N contexts into
    a single (B, seq_len, d) tensor lets torch fuse the forward passes
    via BLAS multi-threading on this Xeon E5530's 16 HW threads.

    Expected speedup: ~5× vs sequential (5 obs/sec → 25 obs/sec).
    """
    all_tokens = tokenizer.encode(text)
    # The GPT-2 tokenizer issues a warning if encode is given > 1024 tokens;
    # the actual forward pass handles arbitrary windows of ≤ 1024. So the
    # warning is cosmetic for our case (we slice 64-token windows).
    print(f"  [{label}] corpus: {len(all_tokens)} tokens")
    n_obs = (len(all_tokens) - CONTEXT_WINDOW) // stride
    print(f"  [{label}] target observations: {n_obs} (batch_size={batch_size})")

    # Build all 64-token contexts as a list of lists
    contexts = [
        all_tokens[i:i + CONTEXT_WINDOW]
        for i in range(0, len(all_tokens) - CONTEXT_WINDOW, stride)
    ]
    contexts = contexts[:n_obs]
    observations = []
    t0 = time.time()
    for batch_start in range(0, len(contexts), batch_size):
        batch = contexts[batch_start: batch_start + batch_size]
        # Stack into a (B, 64) tensor; uniform shape per slice
        input_ids = torch.tensor(batch)
        with torch.no_grad():
            logits = model(input_ids).logits  # (B, 64, vocab_size)
        # argmax over the LAST position only — same as the unbatched path
        next_tokens = logits[:, -1, :].argmax(dim=-1).tolist()
        for ctx, nxt in zip(batch, next_tokens):
            observations.append((ctx, int(nxt)))
        if len(observations) % 200 == 0 or len(observations) == len(contexts):
            elapsed = time.time() - t0
            print(f"  [{label}] {len(observations):4d}/{n_obs} obs "
                  f"({elapsed:.0f}s; {len(observations)/elapsed:.1f}/s)")
    harvest_time = time.time() - t0
    rate = len(observations) / harvest_time
    print(f"  [{label}] harvest complete: {len(observations)} obs in {harvest_time:.0f}s "
          f"({rate:.1f}/s, batch_size={batch_size})")
    return observations, harvest_time


# -- Opp 2: multiprocessing.Pool over encode_observation ------------------
# Worker function must be at module scope for pickling
def _encode_obs_chunk(args):
    """Worker process: encode a chunk of observations. Returns list of
    bound hypervectors (raw bytes; pickle-safe)."""
    chunk_observations, D_param = args
    # Re-import inside worker — multiprocessing fork carries the modules but
    # explicit import is defensive against spawn-mode startup.
    import sys as _sys
    _sys.path.insert(0, "docs/srmech/python")
    _sys.path.insert(0, "docs/srmech/rbs_lm_research")
    from rbs_lm_encoder import encode_observation as _enc
    return [_enc(ctx, nxt, D_param) for ctx, nxt in chunk_observations]


def encode_corpus_mt(observations, D=D, n_workers=8, chunk_size=None):
    """Encode a behavioral corpus via multiprocessing.Pool.

    Per HARDWARE_AND_THREADING.md §2.2 Opp 2: 8 workers (physical cores)
    over independent encode_observation calls. Expected ~8× speedup vs
    single-threaded encoding.

    Args:
        observations: list of (context_tokens, next_token) tuples
        D: hypervector dimension
        n_workers: pool size (default 8 = physical core count)
        chunk_size: observations per chunk (default n_obs / (n_workers * 4))

    Returns: list of binding bytes (length == len(observations)).
    """
    if chunk_size is None:
        chunk_size = max(1, len(observations) // (n_workers * 4))
    chunks = [
        observations[i: i + chunk_size]
        for i in range(0, len(observations), chunk_size)
    ]
    # Each chunk gets the D parameter alongside
    args = [(chunk, D) for chunk in chunks]

    print(f"  [mt-encode] {len(observations)} obs → {len(chunks)} chunks of "
          f"~{chunk_size}; {n_workers} workers")
    t0 = time.time()

    # Use spawn start method explicitly — fork can deadlock with torch loaded
    import multiprocessing as mp
    ctx = mp.get_context("spawn")
    with ctx.Pool(n_workers) as pool:
        results = pool.map(_encode_obs_chunk, args)

    # Flatten chunks back into a single list (preserves order)
    bindings = []
    for r in results:
        bindings.extend(r)
    encode_time = time.time() - t0
    rate = len(bindings) / encode_time
    print(f"  [mt-encode] {len(bindings)} bindings in {encode_time:.1f}s "
          f"({rate:.1f}/s with {n_workers} workers)")
    return bindings, encode_time


# -- Combined pipeline -----------------------------------------------------
def encode_source_model_mt(
    corpus_text,
    tokenizer,
    model,
    D=D,
    stride=8,
    batch_size=32,
    n_workers=8,
    label="mt",
):
    """Full multi-threaded pipeline: harvest + encode + hierarchically bundle.

    Returns: (instrument_bytes, observations, timings_dict).
    """
    print(f"=== Multi-threaded encode pipeline ({label}) ===")
    print(f"  torch threads: {torch.get_num_threads()}")

    observations, harvest_time = harvest_corpus_mt(
        corpus_text, tokenizer, model,
        stride=stride, batch_size=batch_size, label=label,
    )

    bindings, encode_time = encode_corpus_mt(
        observations, D=D, n_workers=n_workers,
    )

    print(f"  [mt-bundle] hierarchical bundling {len(bindings)} bindings...")
    t0 = time.time()
    instrument = hierarchical_bundle(bindings)
    bundle_time = time.time() - t0
    print(f"  [mt-bundle] done in {bundle_time:.2f}s; instrument = {len(instrument)} bytes")

    timings = {
        "harvest_s": harvest_time,
        "encode_s": encode_time,
        "bundle_s": bundle_time,
        "total_s": harvest_time + encode_time + bundle_time,
    }
    return instrument, observations, timings


if __name__ == "__main__":
    # Smoke test on a small corpus to verify the pipeline composes.
    from transformers import GPT2LMHeadModel, GPT2Tokenizer

    print(f"=== rbs_lm_mt smoke test ===")
    print(f"torch {torch.__version__} on {torch.get_num_threads()} threads")
    tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
    model = GPT2LMHeadModel.from_pretrained("gpt2")
    model.eval()

    test_text = "The morning sun cast long shadows across the cobblestones. " * 20
    inst, obs, timings = encode_source_model_mt(
        test_text, tokenizer, model,
        stride=8, batch_size=32, n_workers=8,
        label="smoke",
    )
    print(f"\nSmoke test result:")
    print(f"  n_obs: {len(obs)}")
    print(f"  instrument bytes: {len(inst)}")
    print(f"  timings: {timings}")
