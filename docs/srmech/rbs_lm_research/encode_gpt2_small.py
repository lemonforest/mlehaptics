"""R-RBS-LM-5 — Encode GPT-2-small behavior as an RBS-HDC instrument.

Generates a behavioral corpus by running GPT-2-small over diverse text,
harvesting (context, argmax_next_token) observations, and encoding them
into a single hypervector via rbs_lm_encoder.encode_corpus().

Measures:
  - Number of observations harvested
  - Encoding wall time
  - Compression ratio (source state bytes / RBS-HDC instrument bytes)
  - In-corpus query recovery rate (sanity check)

Output: instrument bytes saved to rbs_lm_instrument.bin; results to JSON.

Usage:
    ~/.venvs/rbs-lm-research/bin/python \\
        docs/srmech/rbs_lm_research/encode_gpt2_small.py
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, "docs/srmech/python")
sys.path.insert(0, "docs/srmech/rbs_lm_research")

import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer

from rbs_lm_encoder import (  # noqa: E402
    CONTEXT_WINDOW,
    D,
    bind,
    encode_context,
    encode_observation,
    hierarchical_bundle,
    similarity,
    vocab_vec,
)


INSTRUMENT_PATH = Path("docs/srmech/rbs_lm_research/rbs_lm_instrument.bin")
RESULTS_PATH = Path("docs/srmech/rbs_lm_research/rbs_lm_encoding_results.json")

# Diverse hardcoded corpus (~3 KB; ~700 tokens; ~80 obs at stride=8)
# Mix of styles: prose, technical, narrative, factual
CORPUS_TEXT = """The morning sun cast long shadows across the cobblestones as the old town began to stir. A baker carried fresh bread from the oven, its warm scent drifting through the open window. Children laughed in the square, chasing pigeons that scattered with each playful lunge.

The history of computing begins not with electronics but with mechanical devices. Charles Babbage designed the Analytical Engine in the 1830s, conceiving of a machine that could execute conditional branches, store intermediate results, and operate on data through punched cards. Ada Lovelace, working with Babbage, wrote what is considered the first computer program.

Photosynthesis converts light energy into chemical energy stored in glucose molecules. The process occurs in two stages: light-dependent reactions in the thylakoid membranes, and the Calvin cycle in the stroma. Chlorophyll absorbs primarily red and blue wavelengths, reflecting green light, which is why plants appear green to human eyes.

The bridge crossed the river at its narrowest point, where two cliffs faced each other across a shallow gorge. Travelers had used the same crossing for centuries, leaving their stories carved into the wooden planks. Some carvings were names; others were dates; a few were brief prayers asking for safe passage.

Quantum mechanics describes nature at the smallest scales of energy levels of atoms and subatomic particles. Classical physics, the description of physics that existed before the theory of relativity and quantum mechanics, describes many aspects of nature at an ordinary macroscopic scale, but is not sufficient for describing them at small atomic and subatomic scales.

The chef tasted the soup, frowned slightly, and reached for the salt. After a moment of hesitation, she added a pinch of pepper instead. The change was subtle but decisive, and the kitchen staff exchanged knowing glances. They had watched her make this judgment many times, and the result was always worth the wait.

Algorithms for sorting have been studied for decades. Quicksort, developed by Tony Hoare in 1959, achieves average-case complexity of n log n through a divide-and-conquer strategy. Despite worst-case quadratic behavior, its cache-friendly access patterns and small constant factors make it one of the most widely used sorting algorithms in practice.

Migration patterns of monarch butterflies span thousands of miles, with successive generations completing portions of the journey. The fall migration from northern habitats to overwintering sites in central Mexico involves butterflies that have never made the trip before, yet they navigate with remarkable precision. Scientists continue to investigate the mechanisms that guide them.

In a small village by the sea, the lighthouse keeper kept journals of every passing ship. He noted the color of their flags, the rigging of their sails, and the time they appeared on the horizon. His grandfather had begun the practice, and his father had continued it, and now he wrote in the same leather-bound books, sometimes adding observations of the weather and the changing seasons.

The development of vaccines requires extensive testing across multiple phases. Phase I studies safety in small groups of healthy volunteers. Phase II examines efficacy and dosing in larger populations. Phase III involves thousands of participants to confirm effectiveness, monitor side effects, and compare against existing treatments. The process typically takes years.
"""


def main():
    print(f"=== R-RBS-LM-5 — Encoding GPT-2-small as RBS-HDC ===")
    print(f"D = {D}, CONTEXT_WINDOW = {CONTEXT_WINDOW}")

    # ---- 1. load source model -------------------------------------------
    print("\nLoading GPT-2-small...")
    t0 = time.time()
    tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
    model = GPT2LMHeadModel.from_pretrained("gpt2")
    model.eval()
    print(f"  loaded in {time.time() - t0:.1f}s")
    source_bytes = sum(p.numel() * p.element_size() for p in model.parameters())
    print(f"  source state: {source_bytes:,} bytes ({source_bytes / 1024**2:.1f} MB)")

    # ---- 2. tokenize corpus ---------------------------------------------
    all_tokens = tokenizer.encode(CORPUS_TEXT)
    print(f"\ncorpus: {len(CORPUS_TEXT):,} chars, {len(all_tokens):,} tokens")

    # ---- 3. harvest observations via sliding window ---------------------
    stride = 8
    print(f"\nHarvesting (context, argmax_next_token) via sliding window")
    print(f"  window = {CONTEXT_WINDOW}, stride = {stride}")
    observations = []
    t0 = time.time()
    for i in range(0, len(all_tokens) - CONTEXT_WINDOW, stride):
        context = all_tokens[i:i + CONTEXT_WINDOW]
        input_ids = torch.tensor([context])
        with torch.no_grad():
            logits = model(input_ids).logits[0, -1, :]
        next_token = int(logits.argmax())
        observations.append((context, next_token))
        if len(observations) % 20 == 0:
            elapsed = time.time() - t0
            rate = len(observations) / elapsed
            print(f"  {len(observations):4d} obs ({elapsed:.0f}s; {rate:.1f}/s)")
    harvest_time = time.time() - t0
    print(f"  harvest complete: {len(observations)} obs in {harvest_time:.1f}s "
          f"({len(observations) / harvest_time:.1f}/s)")

    # ---- 4. encode via RBS-HDC ------------------------------------------
    print(f"\nEncoding {len(observations)} observations via Path B...")
    t0 = time.time()
    bindings = [encode_observation(ctx, nxt) for ctx, nxt in observations]
    bind_time = time.time() - t0
    print(f"  {len(bindings)} bindings in {bind_time:.1f}s ({len(bindings)/bind_time:.1f}/s)")

    t0 = time.time()
    instrument = hierarchical_bundle(bindings)
    bundle_time = time.time() - t0
    print(f"  hierarchical bundle in {bundle_time:.2f}s")
    print(f"  instrument: {len(instrument):,} bytes ({len(instrument)*8} bits = D)")

    # ---- 5. compression ratio -------------------------------------------
    ratio = source_bytes / len(instrument)
    print(f"\nCompression ratio:")
    print(f"  source:     {source_bytes:,} bytes ({source_bytes/1024**2:.1f} MB)")
    print(f"  RBS-HDC:    {len(instrument):,} bytes ({len(instrument)/1024:.1f} KB)")
    print(f"  ratio:      {ratio:,.0f}:1")

    # ---- 6. save instrument --------------------------------------------
    INSTRUMENT_PATH.parent.mkdir(parents=True, exist_ok=True)
    INSTRUMENT_PATH.write_bytes(instrument)
    print(f"\nInstrument saved: {INSTRUMENT_PATH}")

    # ---- 7. sanity check: in-corpus query recovery ----------------------
    # Cleanup against union of observed next-tokens + 30 random distractors
    print(f"\nSanity check — in-corpus query recovery")
    seen_tokens = sorted({nxt for _, nxt in observations})
    print(f"  observed unique next-tokens: {len(seen_tokens)}")
    import random
    random.seed(0)
    # 30 random distractor token IDs (not in observed set)
    distractor_pool = [t for t in range(tokenizer.vocab_size) if t not in set(seen_tokens)]
    distractors = random.sample(distractor_pool, min(30, len(distractor_pool)))
    cleanup_vocab = sorted(set(seen_tokens) | set(distractors))
    print(f"  cleanup vocab size: {len(cleanup_vocab)} (observed + 30 distractors)")

    # Test on 20 randomly chosen in-corpus contexts
    n_test = min(20, len(observations))
    test_indices = random.sample(range(len(observations)), n_test)
    n_correct = 0
    detail_lines = []
    for i, idx in enumerate(test_indices):
        ctx, expected = observations[idx]
        ctx_vec = encode_context(ctx)
        candidate = bind(instrument, ctx_vec)
        scored = [(t, similarity(candidate, vocab_vec(t))) for t in cleanup_vocab]
        scored.sort(key=lambda x: -x[1])
        predicted, top_sim = scored[0]
        ok = predicted == expected
        n_correct += ok
        detail_lines.append({
            "context_last10": ctx[-10:],
            "expected_token": expected,
            "expected_decoded": tokenizer.decode([expected]),
            "predicted_token": predicted,
            "predicted_decoded": tokenizer.decode([predicted]),
            "top_sim": top_sim,
            "ok": ok,
        })
    accuracy = n_correct / n_test
    print(f"  in-corpus query accuracy: {n_correct}/{n_test} ({100*accuracy:.0f}%)")
    print(f"  expected: high (these contexts were in the encoding corpus)")
    for d in detail_lines[:5]:
        flag = "OK" if d["ok"] else "FAIL"
        print(f"    ...{d['context_last10']} → pred '{d['predicted_decoded']}'"
              f" (expected '{d['expected_decoded']}'; sim {d['top_sim']:+.4f}) [{flag}]")

    # ---- 8. save structured results -------------------------------------
    results = {
        "model_name": "gpt2",
        "context_window": CONTEXT_WINDOW,
        "stride": stride,
        "D": D,
        "n_observations": len(observations),
        "n_corpus_tokens": len(all_tokens),
        "source_bytes": source_bytes,
        "instrument_bytes": len(instrument),
        "compression_ratio": ratio,
        "timing": {
            "harvest_s": harvest_time,
            "bind_s": bind_time,
            "bundle_s": bundle_time,
        },
        "sanity_check": {
            "n_test": n_test,
            "cleanup_vocab_size": len(cleanup_vocab),
            "n_correct": n_correct,
            "accuracy": accuracy,
            "details_sample": detail_lines[:5],
        },
    }
    RESULTS_PATH.write_text(json.dumps(results, indent=2))
    print(f"\nResults saved: {RESULTS_PATH}")


if __name__ == "__main__":
    main()
