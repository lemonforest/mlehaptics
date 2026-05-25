"""R-RBS-LM-17 — Path C hybrid: source-model WTE embedding + Path B compute body.

Per R-RBS-LM-2 §4.3 + §6.4: Path C uses the source model's learned token
embedding (WTE matrix) projected to RBS-HDC dimension D via random projection
(Johnson-Lindenstrauss) + bipolar quantization. This preserves the source-
model's semantic similarity structure at the vocab level — the missing piece
hypothesized in R-RBS-LM-8 candidate 3 (Path B without semantic-similarity
propagation).

The compute body (encode_context, encode_observation, hierarchical_bundle)
stays Path B (Kanerva sequence + bind + bundle). Only the vocab vectors
change from `mint_vector(f"LoE.vocab.{token_id}")` to Path-C-projected.

If Path C produces non-zero token agreement on the R-RBS-LM-3 §6.3
hallucination corpus, R-RBS-LM-8 candidate 3 is confirmed as the dominant
issue. If still 0%, Path C also doesn't bridge — implying the fundamental
issue is the discrete-binding-vs-continuous-cascade mismatch (R-RBS-LM-8
§5.4 candidate 5).

Usage:
    ~/.venvs/rbs-lm-research/bin/python \\
        docs/srmech/rbs_lm_research/rbs_lm_path_c.py
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

# Use multi-threading per R-RBS-LM-11
torch.set_num_threads(16)

from rbs_lm_encoder import (  # noqa: E402
    CONTEXT_WINDOW,
    D,
    bind,
    bundle,
    sentinel,
    position_vec,
)
from rbs_lm_inference import vectorised_cleanup  # noqa: E402


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

CORPUS_TEXT = """The morning sun cast long shadows across the cobblestones as the old town began to stir. A baker carried fresh bread from the oven, its warm scent drifting through the open window. Children laughed in the square, chasing pigeons that scattered with each playful lunge.

The history of computing begins not with electronics but with mechanical devices. Charles Babbage designed the Analytical Engine in the 1830s, conceiving of a machine that could execute conditional branches, store intermediate results, and operate on data through punched cards.

Photosynthesis converts light energy into chemical energy stored in glucose molecules. The process occurs in two stages: light-dependent reactions in the thylakoid membranes, and the Calvin cycle in the stroma.

Quantum mechanics describes nature at the smallest scales of energy levels of atoms and subatomic particles.

The chef tasted the soup, frowned slightly, and reached for the salt. The kitchen staff exchanged knowing glances; they had watched her make this judgment many times.

Algorithms for sorting have been studied for decades. Quicksort achieves average-case complexity of n log n through a divide-and-conquer strategy.

Migration patterns of monarch butterflies span thousands of miles, with successive generations completing portions of the journey.

In a small village by the sea, the lighthouse keeper kept journals of every passing ship. He noted the color of their flags, the rigging of their sails, and the time they appeared on the horizon.

The development of vaccines requires extensive testing across multiple phases. Phase I studies safety in small groups of healthy volunteers.

The clockwork in the cathedral tower had not run for three hundred years. When the new mayor commissioned its restoration, the engineer found gears made of seven different metals.

Cellular respiration converts glucose into ATP through a sequence of three coupled processes. Glycolysis in the cytoplasm produces pyruvate.

The library at Alexandria held perhaps half a million scrolls at its peak. Most were lost across three successive disasters.

A common pattern in distributed systems is the eventual-consistency model, where nodes are allowed to diverge temporarily but converge over time.

When the river flooded, the village above had to retreat to the high cliffs. They carried what they could.

Operating systems schedule processes through algorithms that balance throughput, latency, and fairness.

The grandmother set out the photographs across the table, arranging them by year. Each photograph carried a small caption written in her careful hand.

Polymerase chain reaction amplifies specific DNA segments through repeated cycles of denaturation, annealing, and extension.

Mountain weather changes rapidly. A clear morning at the summit can become a snowstorm within two hours.

Compilers transform source code into executable form through several stages. Lexical analysis produces tokens.

The painter mixed her colors slowly, watching how each pigment interacted with the linseed oil.

The forest in autumn carried a particular smell, a combination of damp leaves and woodsmoke from cabins farther down the valley.

Database transactions enforce four properties known as ACID: atomicity, consistency, isolation, and durability.

The harbor in the early morning held a dozen fishing boats, their hulls dark against the gray water.

Neurons communicate through chemical synapses where neurotransmitters cross a narrow gap.

Container orchestration platforms manage the lifecycle of containerized applications across clusters of machines.

The composer worked at a small upright piano in the corner of her studio.

Stars form in giant molecular clouds when regions of higher density collapse under gravity.

Public-key cryptography enables secure communication between parties who have never met.

The library's reading room had vaulted ceilings and tall windows that filled the space with diffuse afternoon light.

Tectonic plates move at speeds comparable to fingernail growth, a few centimeters per year.

The river formed an oxbow lake where its course had once curved sharply.

Garbage collection in programming languages frees memory that is no longer reachable from program references.

The carpenter measured the door frame twice before making the cut.

Climate models simulate the atmosphere through coupled differential equations representing fluid dynamics, radiation transfer, and chemical reactions.

The street market spread across two blocks every Saturday morning. Vendors sold vegetables, bread, cheese, flowers.

Functional programming languages emphasize the evaluation of expressions over the execution of statements.
"""


def compute_path_c_vocab_table(model, D=D, seed=42):
    """Path C: project GPT-2 WTE through random Gaussian to D dims, then
    bipolar-quantize.

    Per Johnson-Lindenstrauss lemma: random projection preserves pairwise
    distances up to (1 ± ε). Bipolar quantization preserves the sign of the
    projected components — semantically similar tokens (close in WTE space)
    map to bipolar vectors with high similarity (low Hamming distance).

    Returns: (vocab_size, D//8) uint8 numpy array — Path C vocab table.
    """
    print(f"  Computing Path C vocab table via random projection (D={D})...")
    t0 = time.time()
    wte = model.transformer.wte.weight.detach().cpu().numpy()
    vocab_size, source_dim = wte.shape
    print(f"  WTE matrix: ({vocab_size}, {source_dim})")

    # Seeded random projection matrix
    rng = np.random.default_rng(seed)
    R = rng.standard_normal((D, source_dim)).astype(np.float32)
    print(f"  Random projection R: ({D}, {source_dim}); seed={seed}")

    # Project each row through R
    projected = wte @ R.T  # (vocab_size, D)

    # Bipolar quantize → binary {0, 1}; pack to bytes
    bipolar_bits = (projected > 0).astype(np.uint8)  # (vocab_size, D)
    vocab_table = np.packbits(bipolar_bits, axis=1, bitorder="big")  # (V, D//8)

    elapsed = time.time() - t0
    print(f"  Path C vocab table: {vocab_table.shape}; "
          f"{vocab_table.nbytes/1024**2:.1f} MB; {elapsed:.1f}s")
    return vocab_table


def encode_context_path_c(token_ids, vocab_table_pc, D=D):
    """Same Kanerva sequence as Path B, but vocab vectors come from
    vocab_table_pc (Path C) instead of mint_vector (srmech-native)."""
    if len(token_ids) > CONTEXT_WINDOW:
        token_ids = list(token_ids[-CONTEXT_WINDOW:])
    n = len(token_ids)
    if n == 0:
        return sentinel("empty_context", D)
    binds = [
        bind(vocab_table_pc[int(t)].tobytes(), position_vec(k, D))
        for k, t in enumerate(token_ids)
    ]
    if len(binds) == 1:
        return binds[0]
    if len(binds) % 2 == 0:
        binds.append(sentinel("context.pad", D))
    return bundle(binds)


def encode_observation_path_c(ctx, nxt, vocab_table_pc, D=D):
    return bind(
        encode_context_path_c(ctx, vocab_table_pc, D),
        vocab_table_pc[int(nxt)].tobytes(),
    )


def main():
    print(f"=== R-RBS-LM-17 — Path C hybrid (WTE embedding + Path B compute) ===")
    print(f"  torch threads: {torch.get_num_threads()}")
    print(f"  D = {D}, CONTEXT_WINDOW = {CONTEXT_WINDOW}")

    # ---- 1. load source model -----------------------------------------
    print("\nLoading source model...")
    tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
    model = GPT2LMHeadModel.from_pretrained("gpt2")
    model.eval()

    # ---- 2. compute Path C vocab table -------------------------------
    print(f"\n=== Path C vocab table ===")
    vocab_table_pc = compute_path_c_vocab_table(model, D=D, seed=42)

    # Verify some properties of the Path C vocab table
    print(f"\n=== Path C vocab table properties ===")
    # Random pairs: should be near 0.5 hamming distance (D/2 = 4096 bits)
    rng = np.random.default_rng(0)
    n_pairs = 100
    rand_pairs = rng.integers(0, vocab_table_pc.shape[0], (n_pairs, 2))
    hammings = []
    for i, j in rand_pairs:
        xor = vocab_table_pc[i] ^ vocab_table_pc[j]
        h = int(np.bitwise_count(xor).sum())
        hammings.append(h)
    print(f"  random-pair Hamming distance: {np.mean(hammings):.0f} ± {np.std(hammings):.0f} "
          f"(expected ≈ D/2 = {D//2} for random projection)")

    # Self-similarity: identical token → 0 hamming
    same_h = int(np.bitwise_count(vocab_table_pc[100] ^ vocab_table_pc[100]).sum())
    print(f"  self-pair Hamming: {same_h} (expected 0)")

    # Source-model nearby tokens: should have lower Hamming than random
    # 'the' vs 'The' (similar):
    the_id = tokenizer.encode(" the")[0]
    The_id = tokenizer.encode(" The")[0]
    h_the_The = int(np.bitwise_count(vocab_table_pc[the_id] ^ vocab_table_pc[The_id]).sum())
    sim_the_The = 1 - 2 * h_the_The / D
    print(f"  ' the' vs ' The' Hamming: {h_the_The} (sim {sim_the_The:+.4f}); semantically similar")
    # 'the' vs 'cat' (less similar):
    cat_id = tokenizer.encode(" cat")[0]
    h_the_cat = int(np.bitwise_count(vocab_table_pc[the_id] ^ vocab_table_pc[cat_id]).sum())
    sim_the_cat = 1 - 2 * h_the_cat / D
    print(f"  ' the' vs ' cat' Hamming: {h_the_cat} (sim {sim_the_cat:+.4f}); less similar")

    # ---- 3. harvest observations -------------------------------------
    print(f"\n=== Harvest observations ===")
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
    print(f"  harvested {len(observations)} obs in {harvest_time:.0f}s ({len(observations)/harvest_time:.1f}/s)")

    # ---- 4. encode using Path C -------------------------------------
    print(f"\n=== Encode (Path C vocab + Path B compute) ===")
    t0 = time.time()
    bindings = [
        encode_observation_path_c(ctx, nxt, vocab_table_pc)
        for ctx, nxt in observations
    ]
    encode_time = time.time() - t0
    print(f"  {len(bindings)} bindings in {encode_time:.1f}s ({len(bindings)/encode_time:.1f}/s, single-thread)")

    # Hierarchical bundle
    from rbs_lm_encoder import hierarchical_bundle
    t0 = time.time()
    instrument = hierarchical_bundle(bindings)
    bundle_time = time.time() - t0
    print(f"  bundle: {bundle_time:.2f}s; instrument = {len(instrument)} bytes")

    out_path = Path("docs/srmech/rbs_lm_research/rbs_lm_instrument_v17.bin")
    out_path.write_bytes(instrument)
    print(f"  saved: {out_path}")

    # ---- 5. validate on hallucination corpus -------------------------
    print(f"\n=== Validate on hallucination corpus (Path C inference) ===")
    n_total = 0
    n_agree = 0
    per_prompt_results = []
    latencies = []
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
            # Cleanup against Path C vocab table
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
            print(f"    source:  {tokenizer.decode(src_new)[:80]}")
            print(f"    RBS-HDC: {tokenizer.decode(rbs_new)[:80]}")

    overall = n_agree / n_total
    print(f"\n  Overall: {n_agree}/{n_total} ({100*overall:.1f}%)")
    print(f"  Per-token latency: {np.mean(latencies):.1f} ± {np.std(latencies):.1f} ms")

    print(f"\n=== Comparison: Path B vs Path C at similar scale ===")
    print(f"  {'Configuration':<60} {'n_obs':>7} {'agreement':>12}")
    print(f"  {'R-RBS-LM-14 Path B genuine (mt)':<60} {'491':>7} {'0.0%':>12}")
    print(f"  {'R-RBS-LM-17 Path C hybrid (this run)':<60} {len(observations):>7} "
          f"{100*overall:>11.1f}%")

    # Save results
    results = {
        "n_observations": len(observations),
        "vocab_table_method": "path_c_wte_random_projection",
        "random_projection_seed": 42,
        "compression_ratio_source_to_instrument": 474.7 * 1024 * 1024 / len(instrument),
        "instrument_bytes": len(instrument),
        "overall_agreement_pct": 100 * overall,
        "latency_ms_mean": float(np.mean(latencies)),
        "vocab_table_properties": {
            "random_pair_hamming_mean": float(np.mean(hammings)),
            "random_pair_hamming_std": float(np.std(hammings)),
            "expected_random_hamming": D // 2,
            "the_vs_The_hamming": h_the_The,
            "the_vs_cat_hamming": h_the_cat,
        },
        "per_prompt_results": per_prompt_results,
    }
    Path("docs/srmech/rbs_lm_research/rbs_lm_path_c_results.json").write_text(
        json.dumps(results, indent=2)
    )
    print(f"\nResults saved.")


if __name__ == "__main__":
    main()
