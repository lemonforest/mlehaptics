"""R-RBS-LM-9 — Scale-up test: Path α (10x corpus).

Per R-RBS-LM-8 §6.1: final empirical test of Path B at deployable scale.
Encode ~10x larger behavioral corpus than R-RBS-LM-5 baseline (76 obs) →
target ~700-1000 obs. Re-validate on the R-RBS-LM-3 §6.3 hallucination
corpus. Compare against:
  - R-RBS-LM-7 baseline (76 obs, bind-with-position): 0%
  - R-RBS-LM-8 V2 (158 obs, bind-with-position): 0%

If R-RBS-LM-9 yields >0%, Path B is viable at scale (scenario (c) or
better). If 0%, scenario (d) confirmed at any deployable scale —
R-RBS-LM-10 closes the arc with the structural-limitation finding.

Usage:
    ~/.venvs/rbs-lm-research/bin/python \\
        docs/srmech/rbs_lm_research/scale_up_rbs_lm.py
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

from rbs_lm_encoder import (  # noqa: E402
    CONTEXT_WINDOW,
    D,
    bind,
    encode_context,
    encode_observation,
    hierarchical_bundle,
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


# ~30 KB corpus (10× R-RBS-LM-5 base) — diverse content spanning prose,
# technical, narrative, factual, descriptive. Goal: rich sliding-window
# coverage with stride=8.
CORPUS_TEXT = """The morning sun cast long shadows across the cobblestones as the old town began to stir. A baker carried fresh bread from the oven, its warm scent drifting through the open window. Children laughed in the square, chasing pigeons that scattered with each playful lunge. Old men sat on benches reading newspapers, their reading glasses perched on the ends of their noses.

The history of computing begins not with electronics but with mechanical devices. Charles Babbage designed the Analytical Engine in the 1830s, conceiving of a machine that could execute conditional branches, store intermediate results, and operate on data through punched cards. Ada Lovelace, working with Babbage, wrote what is considered the first computer program, an algorithm to compute Bernoulli numbers. The machine was never built in Babbage's lifetime, though working partial replicas have been constructed since.

Photosynthesis converts light energy into chemical energy stored in glucose molecules. The process occurs in two stages: light-dependent reactions in the thylakoid membranes, and the Calvin cycle in the stroma. Chlorophyll absorbs primarily red and blue wavelengths, reflecting green light, which is why plants appear green to human eyes. The byproduct oxygen is released into the atmosphere through small openings on the leaf surface called stomata.

The bridge crossed the river at its narrowest point, where two cliffs faced each other across a shallow gorge. Travelers had used the same crossing for centuries, leaving their stories carved into the wooden planks. Some carvings were names; others were dates; a few were brief prayers asking for safe passage. The bridge keeper lived in a small stone house on the eastern side, collecting a small toll from those who could pay and waving through those who could not.

Quantum mechanics describes nature at the smallest scales of energy levels of atoms and subatomic particles. Classical physics, the description of physics that existed before the theory of relativity and quantum mechanics, describes many aspects of nature at an ordinary macroscopic scale, but is not sufficient for describing them at small atomic and subatomic scales. The uncertainty principle establishes a fundamental limit on the precision with which complementary observables can simultaneously be known.

The chef tasted the soup, frowned slightly, and reached for the salt. After a moment of hesitation, she added a pinch of pepper instead. The change was subtle but decisive, and the kitchen staff exchanged knowing glances. They had watched her make this judgment many times, and the result was always worth the wait. Tonight's tasting menu featured seven courses, each paired with a wine from a different region, and the dining room was already filling with guests.

Algorithms for sorting have been studied for decades. Quicksort, developed by Tony Hoare in 1959, achieves average-case complexity of n log n through a divide-and-conquer strategy. Despite worst-case quadratic behavior, its cache-friendly access patterns and small constant factors make it one of the most widely used sorting algorithms in practice. Mergesort, by contrast, guarantees n log n in the worst case but typically uses more memory.

Migration patterns of monarch butterflies span thousands of miles, with successive generations completing portions of the journey. The fall migration from northern habitats to overwintering sites in central Mexico involves butterflies that have never made the trip before, yet they navigate with remarkable precision. Scientists continue to investigate the mechanisms that guide them, with magnetic field detection and polarized-light cues among the leading hypotheses.

In a small village by the sea, the lighthouse keeper kept journals of every passing ship. He noted the color of their flags, the rigging of their sails, and the time they appeared on the horizon. His grandfather had begun the practice, and his father had continued it, and now he wrote in the same leather-bound books, sometimes adding observations of the weather and the changing seasons. The journals filled a small bookshelf in his attic, each volume covering five years.

The development of vaccines requires extensive testing across multiple phases. Phase I studies safety in small groups of healthy volunteers. Phase II examines efficacy and dosing in larger populations. Phase III involves thousands of participants to confirm effectiveness, monitor side effects, and compare against existing treatments. The process typically takes years, though emergency authorizations during pandemic situations can compress the timeline considerably.

The clockwork in the cathedral tower had not run for three hundred years. When the new mayor commissioned its restoration, the engineer found gears made of seven different metals, each calibrated for a different rate of expansion. The tower's bells had once kept time for ships at sea, their chimes audible for fifteen miles. The mayor's grandchildren would grow up hearing those bells again, the engineer promised, if the restoration could be funded through the harvest season.

Cellular respiration converts glucose into ATP through a sequence of three coupled processes. Glycolysis in the cytoplasm produces pyruvate. The citric acid cycle in mitochondrial matrix releases electrons and carbon dioxide. The electron transport chain on the inner mitochondrial membrane drives ATP synthesis through chemiosmosis. The total ATP yield from a single glucose molecule varies depending on the efficiency of the electron transport chain.

The library at Alexandria held perhaps half a million scrolls at its peak. Most were lost across three successive disasters: the burning during Caesar's siege, the persecution of pagan scholarship by Theodosius, and the final collapse under Arab rule. What survived made its way through Byzantine copyists and Arabic translators to medieval European universities. Scholars in Toledo and Salerno translated Greek philosophy and Arabic medical texts back into Latin, preserving knowledge that would otherwise have been lost.

A common pattern in distributed systems is the eventual-consistency model, where nodes are allowed to diverge temporarily but converge over time. CRDTs (conflict-free replicated data types) provide mathematical guarantees that concurrent updates can be merged without conflict, which makes them well-suited for systems where network partitions are unavoidable. Riak, Redis modules, and Automerge all implement variants of CRDT semantics.

When the river flooded, the village above had to retreat to the high cliffs. They carried what they could; what they could not, they tied to trees in the hopes that the water would recede before too much was damaged. Three days later the river fell, and the families returned to find half their belongings ruined and the other half merely soaked through. The blacksmith's anvil had remained where it was, dark and unmoved, and somehow this felt like a small victory.

Operating systems schedule processes through algorithms that balance throughput, latency, and fairness. Round-robin scheduling assigns fixed time slices to each process. Priority-based scheduling allows high-priority work to preempt others. Modern systems combine these approaches with feedback to adapt to changing workloads. Real-time operating systems add hard deadlines and provide guarantees that critical tasks complete within bounded time.

The grandmother set out the photographs across the table, arranging them by year. Each photograph carried a small caption written in her careful hand, with names and places and sometimes a brief note about what was happening in the scene. The youngest grandchildren had never seen most of these images before; they listened as she explained each one, their attention shifting from face to face on the table, occasionally pointing and asking who someone was.

Polymerase chain reaction amplifies specific DNA segments through repeated cycles of denaturation, annealing, and extension. The technique relies on heat-stable polymerase enzymes from thermophilic bacteria, particularly Thermus aquaticus from Yellowstone hot springs. PCR transformed molecular biology, enabling forensic analysis, disease diagnosis, and ancient DNA studies. Modern variants such as RT-PCR and qPCR add quantitative and reverse-transcription capabilities.

Mountain weather changes rapidly. A clear morning at the summit can become a snowstorm within two hours, particularly in the shoulder seasons. Experienced climbers carry equipment for conditions they hope they will not encounter, and they turn back when conditions exceed their margin of safety, even if the summit is in sight. The mountain will be there next year, but the climber will not be unless they make sound decisions today.

Compilers transform source code into executable form through several stages. Lexical analysis produces tokens. Parsing builds an abstract syntax tree. Semantic analysis verifies type correctness. Code generation produces target code, often through intermediate representations. Optimization passes can be inserted at multiple points along the pipeline, with different trade-offs between compile time and runtime performance.

The painter mixed her colors slowly, watching how each pigment interacted with the linseed oil. Some yellows dried with a faint green tint; some reds darkened over weeks into a deep maroon. The canvases in her studio reflected this knowledge: paintings from twenty years ago, restored with careful attention to the original color values, alongside new work where she was still learning the materials. Each painting represented a conversation with light.
"""


def harvest(text, tokenizer, model, stride=8, label=""):
    """Harvest (context, argmax_next_token) observations from source model."""
    all_tokens = tokenizer.encode(text)
    print(f"  [{label}] corpus: {len(all_tokens)} tokens")
    observations = []
    t0 = time.time()
    n_target = (len(all_tokens) - CONTEXT_WINDOW) // stride
    for i in range(0, len(all_tokens) - CONTEXT_WINDOW, stride):
        ctx = all_tokens[i:i + CONTEXT_WINDOW]
        input_ids = torch.tensor([ctx])
        with torch.no_grad():
            logits = model(input_ids).logits[0, -1, :]
        nxt = int(logits.argmax())
        observations.append((ctx, nxt))
        if len(observations) % 50 == 0:
            elapsed = time.time() - t0
            print(f"  [{label}] {len(observations):4d}/{n_target} obs ({elapsed:.0f}s; "
                  f"{len(observations)/elapsed:.1f}/s)")
    print(f"  [{label}] harvested {len(observations)} obs in {time.time()-t0:.0f}s")
    return observations


def main():
    print(f"=== R-RBS-LM-9 — Path α scale-up (10× corpus) ===")
    print(f"D = {D}, CONTEXT_WINDOW = {CONTEXT_WINDOW}")

    print("\nLoading source model + vocab table...")
    tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
    model = GPT2LMHeadModel.from_pretrained("gpt2")
    model.eval()
    vocab_table = precompute_vocab_table(vocab_size=50257, D=D)
    print(f"  vocab table: {vocab_table.shape}")

    # ---- 1. harvest 10× corpus -----------------------------------------
    print(f"\n=== Step 1: harvest 10× behavioral corpus ===")
    obs = harvest(CORPUS_TEXT, tokenizer, model, stride=8, label="10x")
    source_state_bytes = sum(p.numel() * p.element_size() for p in model.parameters())

    # ---- 2. encode (bind-with-position; original encoder) -------------
    print(f"\n=== Step 2: encode {len(obs)} observations ===")
    t0 = time.time()
    bindings = [encode_observation(ctx, nxt) for ctx, nxt in obs]
    inst = hierarchical_bundle(bindings)
    encode_t = time.time() - t0
    print(f"  encoded in {encode_t:.1f}s")
    print(f"  instrument: {len(inst)} bytes")
    ratio = source_state_bytes / len(inst)
    print(f"  compression: {ratio:,.0f}:1 (source {source_state_bytes/1024**2:.1f} MB → instrument {len(inst)/1024:.1f} KB)")

    # Save the scaled-up instrument separately
    instrument_path = Path("docs/srmech/rbs_lm_research/rbs_lm_instrument_v9.bin")
    instrument_path.write_bytes(inst)

    # ---- 3. validate on hallucination corpus ---------------------------
    print(f"\n=== Step 3: validate against source-model baseline ===")
    n_total = 0
    n_agree = 0
    per_prompt_results = []
    per_position_agreement = np.zeros(20)
    latencies = []
    for prompt in HALLUCINATION_PROMPTS:
        prompt_ids = tokenizer.encode(prompt)
        # Source
        with torch.no_grad():
            src_out = model.generate(
                torch.tensor([prompt_ids]),
                max_new_tokens=20,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
            )
        src_new = src_out[0][len(prompt_ids):].tolist()
        # RBS-HDC
        rbs_tokens = list(prompt_ids)
        prompt_latencies = []
        for _ in range(20):
            t0 = time.time()
            ctx = rbs_tokens[-CONTEXT_WINDOW:] if len(rbs_tokens) > CONTEXT_WINDOW else rbs_tokens
            ctx_vec = encode_context(ctx)
            cand = bind(inst, ctx_vec)
            res = vectorised_cleanup(cand, vocab_table, D, top_k=1)
            rbs_tokens.append(res[0][0])
            prompt_latencies.append((time.time() - t0) * 1000)
        rbs_new = rbs_tokens[len(prompt_ids):]
        latencies.extend(prompt_latencies)
        agreement = [int(s == r) for s, r in zip(src_new, rbs_new)]
        per_position_agreement += np.array(agreement)
        n_total += len(agreement)
        n_agree += sum(agreement)
        per_prompt_results.append({
            "prompt": prompt,
            "source_decoded": tokenizer.decode(src_new),
            "rbs_decoded": tokenizer.decode(rbs_new),
            "agreement": sum(agreement),
        })
        print(f"  '{prompt[:40]}...' → agreement {sum(agreement)}/20")

    overall = n_agree / n_total
    per_position_agreement /= len(HALLUCINATION_PROMPTS)
    print(f"\n=== Results ===")
    print(f"  Overall agreement: {n_agree}/{n_total} ({100*overall:.1f}%)")
    print(f"  Per-position agreement (avg over {len(HALLUCINATION_PROMPTS)} prompts):")
    print(f"    " + " ".join(f"{p:4.2f}" for p in per_position_agreement))
    print(f"  Per-token latency: {np.mean(latencies):.1f} ± {np.std(latencies):.1f} ms")

    # ---- Comparison vs prior partitions --------------------------------
    print(f"\n=== Comparison ===")
    print(f"  {'Partition':<55} {'n_obs':>7} {'agreement':>12}")
    print(f"  {'R-RBS-LM-7 baseline (76 obs)':<55} {'76':>7} {'0.0%':>12}")
    print(f"  {'R-RBS-LM-8 V2 (158 obs, 2× scale)':<55} {'158':>7} {'0.0%':>12}")
    print(f"  {'R-RBS-LM-9 Path α (this run, ~10× scale)':<55} {len(obs):>7} "
          f"{100*overall:>11.1f}%")

    # ---- Save results ---------------------------------------------------
    results = {
        "n_observations": len(obs),
        "compression_ratio": ratio,
        "instrument_bytes": len(inst),
        "overall_agreement_pct": 100 * overall,
        "per_position_agreement": per_position_agreement.tolist(),
        "latency_ms_mean": float(np.mean(latencies)),
        "latency_ms_std": float(np.std(latencies)),
        "per_prompt_results": per_prompt_results,
        "comparison": {
            "r_rbs_lm_7_76obs_pct": 0.0,
            "r_rbs_lm_8_v2_158obs_pct": 0.0,
            "r_rbs_lm_9_scaled_pct": 100 * overall,
        },
    }
    Path("docs/srmech/rbs_lm_research/rbs_lm_scaleup_results.json").write_text(
        json.dumps(results, indent=2)
    )
    print(f"\n  Results saved.")


if __name__ == "__main__":
    main()
