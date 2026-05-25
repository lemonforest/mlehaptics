"""R-RBS-LM-8 — Diagnostic + iteration on the scenario-(d) finding.

Tests the three R-RBS-LM-6 §6.5 candidates that could explain the
R-RBS-LM-7 0% agreement result:

  Candidate 1 — Position-exact bindings don't slide
    → switch from bind(token, position_vec) to cyclic-shift permute
      (R-RBS-NN-5 §3.2 Scheme B)

  Candidate 2 — Corpus too small (76 obs)
    → scale corpus 5x and re-measure

  Candidate 3 — Path B lacks semantic-similarity propagation
    → requires Path C hybrid (out of scope for this partition;
       noted as R-RBS-LM-9 / future work)

Each variant is encoded + validated on the R-RBS-LM-3 §6.3 hallucination
corpus. Token-level agreement compared against R-RBS-LM-7 baseline (0%).

Usage:
    ~/.venvs/rbs-lm-research/bin/python \\
        docs/srmech/rbs_lm_research/diagnostic_rbs_lm.py
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

from srmech.amsc.hdc import permute  # noqa: E402
from rbs_lm_encoder import (  # noqa: E402
    CONTEXT_WINDOW,
    D,
    bind,
    bundle,
    encode_context,
    encode_observation,
    hierarchical_bundle,
    sentinel,
    vocab_vec,
)
from rbs_lm_inference import precompute_vocab_table, vectorised_cleanup  # noqa: E402


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

# Same corpus as R-RBS-LM-5 — but augmented to ~5x for Variant 2
CORPUS_TEXT_BASE = """The morning sun cast long shadows across the cobblestones as the old town began to stir. A baker carried fresh bread from the oven, its warm scent drifting through the open window. Children laughed in the square, chasing pigeons that scattered with each playful lunge.

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

# Augment for Variant 2 — concatenate variations + additional content
CORPUS_TEXT_LARGE = CORPUS_TEXT_BASE + """

The clockwork in the cathedral tower had not run for three hundred years. When the new mayor commissioned its restoration, the engineer found gears made of seven different metals, each calibrated for a different rate of expansion. The tower's bells had once kept time for ships at sea, their chimes audible for fifteen miles.

Cellular respiration converts glucose into ATP through a sequence of three coupled processes. Glycolysis in the cytoplasm produces pyruvate. The citric acid cycle in mitochondrial matrix releases electrons and carbon dioxide. The electron transport chain on the inner mitochondrial membrane drives ATP synthesis through chemiosmosis.

The library at Alexandria held perhaps half a million scrolls at its peak. Most were lost across three successive disasters: the burning during Caesar's siege, the persecution of pagan scholarship by Theodosius, and the final collapse under Arab rule. What survived made its way through Byzantine copyists and Arabic translators to medieval European universities.

A common pattern in distributed systems is the eventual-consistency model, where nodes are allowed to diverge temporarily but converge over time. CRDTs (conflict-free replicated data types) provide mathematical guarantees that concurrent updates can be merged without conflict, which makes them well-suited for systems where network partitions are unavoidable.

When the river flooded, the village above had to retreat to the high cliffs. They carried what they could; what they could not, they tied to trees in the hopes that the water would recede before too much was damaged. Three days later the river fell, and the families returned to find half their belongings ruined and the other half merely soaked through.

Operating systems schedule processes through algorithms that balance throughput, latency, and fairness. Round-robin scheduling assigns fixed time slices to each process. Priority-based scheduling allows high-priority work to preempt others. Modern systems combine these approaches with feedback to adapt to changing workloads.

The grandmother set out the photographs across the table, arranging them by year. Each photograph carried a small caption written in her careful hand, with names and places and sometimes a brief note about what was happening in the scene. The youngest grandchildren had never seen most of these images before; they listened as she explained each one.

Polymerase chain reaction amplifies specific DNA segments through repeated cycles of denaturation, annealing, and extension. The technique relies on heat-stable polymerase enzymes from thermophilic bacteria, particularly Thermus aquaticus from Yellowstone hot springs. PCR transformed molecular biology, enabling forensic analysis, disease diagnosis, and ancient DNA studies.

Mountain weather changes rapidly. A clear morning at the summit can become a snowstorm within two hours, particularly in the shoulder seasons. Experienced climbers carry equipment for conditions they hope they will not encounter, and they turn back when conditions exceed their margin of safety, even if the summit is in sight.

Compilers transform source code into executable form through several stages. Lexical analysis produces tokens. Parsing builds an abstract syntax tree. Semantic analysis verifies type correctness. Code generation produces target code, often through intermediate representations. Optimization passes can be inserted at multiple points along the pipeline.
"""


# Variant 1: cyclic-shift positional encoding (Class I) per R-RBS-NN-5 §3.2
STRIDE = 257  # coprime to D=8192 per Spike #170

def encode_context_cyclic(token_ids, D=D):
    if len(token_ids) > CONTEXT_WINDOW:
        token_ids = list(token_ids[-CONTEXT_WINDOW:])
    n = len(token_ids)
    if n == 0:
        return sentinel("empty_context", D)
    rotated = [permute(vocab_vec(int(tid), D), k * STRIDE)
               for k, tid in enumerate(token_ids)]
    if len(rotated) == 1:
        return rotated[0]
    if len(rotated) % 2 == 0:
        rotated.append(sentinel("context.pad", D))
    return bundle(rotated)


def encode_observation_cyclic(ctx, nxt, D=D):
    return bind(encode_context_cyclic(ctx, D), vocab_vec(int(nxt), D))


def harvest(text, tokenizer, model, stride=8, label=""):
    """Harvest (context, argmax_next_token) observations from source model."""
    all_tokens = tokenizer.encode(text)
    print(f"  [{label}] corpus: {len(all_tokens)} tokens")
    observations = []
    t0 = time.time()
    for i in range(0, len(all_tokens) - CONTEXT_WINDOW, stride):
        ctx = all_tokens[i:i + CONTEXT_WINDOW]
        input_ids = torch.tensor([ctx])
        with torch.no_grad():
            logits = model(input_ids).logits[0, -1, :]
        nxt = int(logits.argmax())
        observations.append((ctx, nxt))
    print(f"  [{label}] harvested {len(observations)} obs in {time.time()-t0:.0f}s")
    return observations


def evaluate(instrument, prompts, tokenizer, vocab_table, encode_ctx_fn, n_new=20):
    """Evaluate instrument on hallucination corpus; return token-level agreement vs source."""
    model = evaluate.model
    n_total = 0
    n_agree = 0
    per_prompt = []
    for prompt in prompts:
        prompt_ids = tokenizer.encode(prompt)
        # Source greedy
        with torch.no_grad():
            src_out = model.generate(
                torch.tensor([prompt_ids]),
                max_new_tokens=n_new,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
            )
        source_new = src_out[0][len(prompt_ids):].tolist()
        # RBS-HDC greedy
        rbs_tokens = list(prompt_ids)
        for _ in range(n_new):
            ctx = rbs_tokens[-CONTEXT_WINDOW:] if len(rbs_tokens) > CONTEXT_WINDOW else rbs_tokens
            ctx_vec = encode_ctx_fn(ctx)
            candidate = bind(instrument, ctx_vec)
            result = vectorised_cleanup(candidate, vocab_table, D, top_k=1)
            rbs_tokens.append(result[0][0])
        rbs_new = rbs_tokens[len(prompt_ids):]
        # Compare
        agreement = [int(s == r) for s, r in zip(source_new, rbs_new)]
        per_prompt.append({
            "prompt": prompt,
            "source_decoded": tokenizer.decode(source_new),
            "rbs_decoded": tokenizer.decode(rbs_new),
            "agreement": sum(agreement),
        })
        n_total += len(agreement)
        n_agree += sum(agreement)
    return n_agree, n_total, per_prompt


def main():
    print(f"=== R-RBS-LM-8 — Diagnostic on scenario-(d) finding ===")
    print(f"D = {D}, CONTEXT_WINDOW = {CONTEXT_WINDOW}, STRIDE (Variant 1) = {STRIDE}")

    print("\nLoading source model + vocab table...")
    tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
    model = GPT2LMHeadModel.from_pretrained("gpt2")
    model.eval()
    evaluate.model = model
    vocab_table = precompute_vocab_table(vocab_size=50257, D=D)
    print(f"  vocab table loaded: {vocab_table.shape}")

    # ---- Variant 1: cyclic-shift positions, same 76-obs corpus ----------
    print(f"\n=== Variant 1: Class I cyclic-shift positions, same 76-obs corpus ===")
    obs_base = harvest(CORPUS_TEXT_BASE, tokenizer, model, stride=8, label="base")
    print(f"\n  encoding with cyclic-shift positions...")
    t0 = time.time()
    bindings_cyclic = [encode_observation_cyclic(ctx, nxt) for ctx, nxt in obs_base]
    inst_cyclic = hierarchical_bundle(bindings_cyclic)
    print(f"  encoded in {time.time()-t0:.1f}s; instrument = {len(inst_cyclic)} bytes")
    print(f"\n  evaluating on hallucination corpus...")
    t0 = time.time()
    n_ag_v1, n_tot_v1, per_v1 = evaluate(
        inst_cyclic, HALLUCINATION_PROMPTS, tokenizer, vocab_table,
        encode_ctx_fn=encode_context_cyclic, n_new=20,
    )
    print(f"  agreement: {n_ag_v1}/{n_tot_v1} ({100*n_ag_v1/n_tot_v1:.1f}%) in {time.time()-t0:.0f}s")

    # ---- Variant 2: bind-with-position (original), scaled corpus --------
    print(f"\n=== Variant 2: bind-with-position (original), SCALED corpus ===")
    obs_large = harvest(CORPUS_TEXT_LARGE, tokenizer, model, stride=8, label="large")
    print(f"\n  encoding {len(obs_large)} observations with bind-with-position...")
    t0 = time.time()
    bindings_large = [encode_observation(ctx, nxt) for ctx, nxt in obs_large]
    inst_large = hierarchical_bundle(bindings_large)
    print(f"  encoded in {time.time()-t0:.1f}s; instrument = {len(inst_large)} bytes")
    print(f"\n  evaluating on hallucination corpus...")
    t0 = time.time()
    n_ag_v2, n_tot_v2, per_v2 = evaluate(
        inst_large, HALLUCINATION_PROMPTS, tokenizer, vocab_table,
        encode_ctx_fn=encode_context, n_new=20,
    )
    print(f"  agreement: {n_ag_v2}/{n_tot_v2} ({100*n_ag_v2/n_tot_v2:.1f}%) in {time.time()-t0:.0f}s")

    # ---- Variant 3: cyclic-shift + scaled corpus -----------------------
    print(f"\n=== Variant 3: cyclic-shift + SCALED corpus (both candidates combined) ===")
    print(f"\n  encoding {len(obs_large)} observations with cyclic-shift...")
    t0 = time.time()
    bindings_v3 = [encode_observation_cyclic(ctx, nxt) for ctx, nxt in obs_large]
    inst_v3 = hierarchical_bundle(bindings_v3)
    print(f"  encoded in {time.time()-t0:.1f}s")
    print(f"\n  evaluating...")
    t0 = time.time()
    n_ag_v3, n_tot_v3, per_v3 = evaluate(
        inst_v3, HALLUCINATION_PROMPTS, tokenizer, vocab_table,
        encode_ctx_fn=encode_context_cyclic, n_new=20,
    )
    print(f"  agreement: {n_ag_v3}/{n_tot_v3} ({100*n_ag_v3/n_tot_v3:.1f}%) in {time.time()-t0:.0f}s")

    # ---- Comparison table ----------------------------------------------
    print(f"\n=== Diagnostic comparison ===")
    print(f"  {'Variant':<60} {'n_obs':>7} {'agreement':>11}")
    print(f"  {'R-RBS-LM-7 baseline (bind-pos, 76 obs)':<60} {'76':>7} "
          f"{'0/180 (0.0%)':>11}")
    print(f"  {'V1 — cyclic-shift, same 76-obs corpus':<60} {len(obs_base):>7} "
          f"{n_ag_v1}/{n_tot_v1} ({100*n_ag_v1/n_tot_v1:.1f}%)")
    print(f"  {'V2 — bind-with-position, scaled corpus':<60} {len(obs_large):>7} "
          f"{n_ag_v2}/{n_tot_v2} ({100*n_ag_v2/n_tot_v2:.1f}%)")
    print(f"  {'V3 — cyclic-shift + scaled corpus':<60} {len(obs_large):>7} "
          f"{n_ag_v3}/{n_tot_v3} ({100*n_ag_v3/n_tot_v3:.1f}%)")

    # Save structured results
    results = {
        "baseline_agreement_pct": 0.0,
        "v1_agreement_pct": 100*n_ag_v1/n_tot_v1,
        "v2_agreement_pct": 100*n_ag_v2/n_tot_v2,
        "v3_agreement_pct": 100*n_ag_v3/n_tot_v3,
        "v1_n_obs": len(obs_base),
        "v2_n_obs": len(obs_large),
        "v3_n_obs": len(obs_large),
        "per_prompt": {
            "v1": per_v1,
            "v2": per_v2,
            "v3": per_v3,
        },
    }
    Path("docs/srmech/rbs_lm_research/rbs_lm_diagnostic_results.json").write_text(
        json.dumps(results, indent=2)
    )
    print(f"\nResults saved.")


if __name__ == "__main__":
    main()
