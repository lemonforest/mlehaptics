"""R-RBS-LM-6 — Optimized inference cascade for the RBS-HDC instrument.

Wraps the saved instrument from R-RBS-LM-5 in an iterative-generation loop
with a vectorised cleanup step using numpy.bitwise_count (popcount).

Per R-RBS-LM-4 §9 + R-RBS-LM-5 §9: pure-Python O(vocab_size) cleanup is
the inference bottleneck (~5 sec/token at vocab=50257). This module
precomputes the vocabulary table as a (vocab_size, D/8) bytes array and
performs XOR + popcount + argmin in vectorised numpy.

Per R-RBS-NN-8 §3: at CPU compute envelope, this is the K class
per-position selection + M class XOR-bind primitives composed in
hardware-friendly form. Target ≤ 100 ms/token per R-RBS-LM-1 §8
BCI-compatibility criterion.

Usage:
    ~/.venvs/rbs-lm-research/bin/python \\
        docs/srmech/rbs_lm_research/rbs_lm_inference.py
"""

import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, "docs/srmech/python")
sys.path.insert(0, "docs/srmech/rbs_lm_research")

from rbs_lm_encoder import (  # noqa: E402
    CONTEXT_WINDOW,
    D,
    bind,
    encode_context,
    vocab_vec,
)


INSTRUMENT_PATH = Path("docs/srmech/rbs_lm_research/rbs_lm_instrument.bin")
VOCAB_TABLE_PATH = Path("docs/srmech/rbs_lm_research/vocab_table.npy")


def precompute_vocab_table(vocab_size: int = 50257, D: int = D) -> np.ndarray:
    """Mint all vocabulary vectors into a (vocab_size, D/8) uint8 numpy array.

    One-time cost (~25 sec for vocab=50257 in pure-Python srmech).
    Cached on disk at VOCAB_TABLE_PATH for re-use across sessions.
    """
    if VOCAB_TABLE_PATH.exists():
        print(f"  loading cached vocab table from {VOCAB_TABLE_PATH}")
        arr = np.load(VOCAB_TABLE_PATH)
        if arr.shape == (vocab_size, D // 8):
            return arr
        print(f"  cached shape {arr.shape} mismatch; rebuilding...")

    print(f"  precomputing vocab table ({vocab_size} mints at D={D})...")
    n_bytes = D // 8
    arr = np.zeros((vocab_size, n_bytes), dtype=np.uint8)
    t0 = time.time()
    for tid in range(vocab_size):
        v = vocab_vec(tid, D)
        arr[tid] = np.frombuffer(v, dtype=np.uint8)
        if (tid + 1) % 10000 == 0:
            print(f"    minted {tid+1}/{vocab_size} ({time.time()-t0:.0f}s)")
    np.save(VOCAB_TABLE_PATH, arr)
    print(f"  saved {arr.shape} table to {VOCAB_TABLE_PATH} "
          f"({arr.nbytes/1024**2:.1f} MB)")
    return arr


def vectorised_cleanup(
    candidate_bytes: bytes,
    vocab_table: np.ndarray,
    D: int = D,
    top_k: int = 1,
) -> list[tuple[int, float]]:
    """Vectorised K-class cleanup: argmin Hamming over all vocab vectors.

    Returns top-k (token_id, similarity) sorted by similarity descending.
    """
    candidate = np.frombuffer(candidate_bytes, dtype=np.uint8)
    # XOR candidate (n_bytes,) against vocab_table (V, n_bytes)
    xor = vocab_table ^ candidate
    # Popcount per byte; sum across bytes per row → Hamming distance per token
    hamming = np.bitwise_count(xor).sum(axis=1)
    # argmin Hamming = argmax similarity (since sim = 1 - 2*h/D)
    if top_k == 1:
        best_tid = int(np.argmin(hamming))
        best_sim = 1.0 - 2.0 * float(hamming[best_tid]) / D
        return [(best_tid, best_sim)]
    # top_k > 1: find smallest k Hammings (argpartition is faster than full sort)
    if top_k >= len(hamming):
        idx = np.argsort(hamming)
    else:
        idx = np.argpartition(hamming, top_k)[:top_k]
        idx = idx[np.argsort(hamming[idx])]
    return [(int(t), 1.0 - 2.0 * float(hamming[t]) / D) for t in idx]


def generate(
    instrument: bytes,
    prompt_tokens: list[int],
    max_new_tokens: int,
    vocab_table: np.ndarray,
    D: int = D,
    return_per_token_timing: bool = False,
) -> tuple[list[int], list[float]]:
    """Iterative generation: predict one token at a time via the cascade.

    Per the R-RBS-NN-3b §6 4-class Level-1 recipe:
      1. encode_context(tokens[-CONTEXT_WINDOW:]) — Class A mint + Class M bind/bundle (Kanerva)
      2. bind(instrument, ctx_vec) — Class M unbind
      3. vectorised_cleanup → argmin Hamming over vocab — Class K per-position selection
      4. append predicted token; loop

    Returns (token_sequence, per_token_latencies_ms).
    """
    tokens = list(prompt_tokens)
    latencies = []
    for _ in range(max_new_tokens):
        t0 = time.time()
        ctx = tokens[-CONTEXT_WINDOW:] if len(tokens) > CONTEXT_WINDOW else tokens
        ctx_vec = encode_context(ctx, D)
        candidate = bind(instrument, ctx_vec)
        result = vectorised_cleanup(candidate, vocab_table, D, top_k=1)
        next_tid = result[0][0]
        tokens.append(next_tid)
        latencies.append((time.time() - t0) * 1000)
    return tokens, latencies


def main() -> None:
    print(f"=== R-RBS-LM-6 — Inference cascade on RBS-HDC instrument ===")
    print(f"D = {D}, CONTEXT_WINDOW = {CONTEXT_WINDOW}")

    # Load instrument
    if not INSTRUMENT_PATH.exists():
        print(f"ERROR: instrument not found at {INSTRUMENT_PATH}")
        print("       Run R-RBS-LM-5 encode_gpt2_small.py first.")
        sys.exit(1)
    instrument = INSTRUMENT_PATH.read_bytes()
    print(f"\nLoaded instrument: {len(instrument)} bytes")

    # Precompute vocab table
    print(f"\nPrecomputing vocab table (one-time)...")
    t0 = time.time()
    vocab_table = precompute_vocab_table(vocab_size=50257, D=D)
    print(f"  vocab table ready in {time.time()-t0:.1f}s; shape {vocab_table.shape}")
    print(f"  memory footprint: {vocab_table.nbytes/1024**2:.1f} MB")

    # Sanity: query an in-corpus context (from R-RBS-LM-5 corpus first sentence)
    # The first context of the encoding corpus
    from transformers import GPT2Tokenizer
    tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
    # Re-tokenize a snippet that was in the corpus
    snippet = "The morning sun cast long shadows across the cobblestones"
    test_tokens = tokenizer.encode(snippet)
    print(f"\nSanity check — generate from in-corpus prompt:")
    print(f"  prompt: '{snippet}' ({len(test_tokens)} tokens)")

    n_new = 20
    out_tokens, latencies = generate(instrument, test_tokens, n_new, vocab_table, D)
    new_part = out_tokens[len(test_tokens):]
    print(f"  generated {n_new} tokens")
    print(f"  per-token latency: {np.mean(latencies):.1f} ± {np.std(latencies):.1f} ms")
    print(f"  min/max:           {np.min(latencies):.1f} / {np.max(latencies):.1f} ms")
    bci_threshold = 100
    bci_pass = np.mean(latencies) <= bci_threshold
    print(f"  BCI threshold (≤ {bci_threshold} ms): {'PASS' if bci_pass else 'FAIL'}")
    print(f"  generated tokens (raw):  {new_part}")
    print(f"  decoded:                 '{tokenizer.decode(new_part)}'")

    # Sanity: query an OUT-OF-CORPUS prompt
    print(f"\nSanity check — generate from OUT-OF-CORPUS prompt:")
    snippet_ooc = "The quick brown fox jumps over the"  # from R-RBS-LM-3 baseline
    test_tokens_ooc = tokenizer.encode(snippet_ooc)
    print(f"  prompt: '{snippet_ooc}' ({len(test_tokens_ooc)} tokens)")
    out_tokens_ooc, latencies_ooc = generate(instrument, test_tokens_ooc, n_new, vocab_table, D)
    new_part_ooc = out_tokens_ooc[len(test_tokens_ooc):]
    print(f"  per-token latency: {np.mean(latencies_ooc):.1f} ± {np.std(latencies_ooc):.1f} ms")
    print(f"  generated tokens (raw):  {new_part_ooc}")
    print(f"  decoded:                 '{tokenizer.decode(new_part_ooc)}'")
    print(f"\n  Note: OOC generation is expected to be noisy at this corpus size (76 obs).")
    print(f"  R-RBS-LM-7 does the full comparison vs source-model baseline.")


if __name__ == "__main__":
    main()
