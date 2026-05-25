"""R-RBS-LM-11 — run the 10× scale test using rbs_lm_mt.

Per R-RBS-LM-9 §7 future-work direction "Path B at 10⁴ scale" — the
combined opportunities from HARDWARE_AND_THREADING.md §2 make this
reachable in ~10 min wall-clock. R-RBS-LM-9 was bound by 5 obs/sec
single-thread harvest + 15 obs/sec single-thread encode; rbs_lm_mt
combines batched harvest (Opp 3) + multiprocessing encode (Opp 2)
+ torch.set_num_threads(16) (Opp 1) for ~5–8× combined speedup.

This run produces a third instrument variant (R-RBS-LM-11) for
comparison against R-RBS-LM-5 (76 obs) and R-RBS-LM-9 (223 obs).

Usage:
    ~/.venvs/rbs-lm-research/bin/python \\
        docs/srmech/rbs_lm_research/run_scale_10x_mt.py
"""

import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, "docs/srmech/python")
sys.path.insert(0, "docs/srmech/rbs_lm_research")

# rbs_lm_mt sets torch threads at import time
from rbs_lm_mt import D, encode_source_model_mt  # noqa: E402
from rbs_lm_encoder import CONTEXT_WINDOW, bind, encode_context  # noqa: E402
from rbs_lm_inference import precompute_vocab_table, vectorised_cleanup  # noqa: E402

from transformers import GPT2LMHeadModel, GPT2Tokenizer  # noqa: E402


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

# Expanded corpus — R-RBS-LM-9 base + additional varied paragraphs.
# Target ~30 KB / ~6000 tokens → ~750 obs at stride=8.
CORPUS_BASE = """The morning sun cast long shadows across the cobblestones as the old town began to stir. A baker carried fresh bread from the oven, its warm scent drifting through the open window. Children laughed in the square, chasing pigeons that scattered with each playful lunge.

The history of computing begins not with electronics but with mechanical devices. Charles Babbage designed the Analytical Engine in the 1830s, conceiving of a machine that could execute conditional branches, store intermediate results, and operate on data through punched cards.

Photosynthesis converts light energy into chemical energy stored in glucose molecules. The process occurs in two stages: light-dependent reactions in the thylakoid membranes, and the Calvin cycle in the stroma.

Quantum mechanics describes nature at the smallest scales of energy levels of atoms and subatomic particles. The uncertainty principle establishes a fundamental limit on the precision with which complementary observables can simultaneously be known.

Algorithms for sorting have been studied for decades. Quicksort achieves average-case complexity of n log n through a divide-and-conquer strategy. Mergesort guarantees n log n in the worst case but typically uses more memory.

Migration patterns of monarch butterflies span thousands of miles, with successive generations completing portions of the journey. Scientists continue to investigate the mechanisms that guide them, with magnetic field detection and polarized-light cues among the leading hypotheses.

Cellular respiration converts glucose into ATP through a sequence of three coupled processes. Glycolysis in the cytoplasm produces pyruvate. The citric acid cycle releases electrons and carbon dioxide.

A common pattern in distributed systems is the eventual-consistency model, where nodes are allowed to diverge temporarily but converge over time. CRDTs provide mathematical guarantees that concurrent updates can be merged without conflict.

Operating systems schedule processes through algorithms that balance throughput, latency, and fairness. Round-robin scheduling assigns fixed time slices to each process. Priority-based scheduling allows high-priority work to preempt others.

Polymerase chain reaction amplifies specific DNA segments through repeated cycles of denaturation, annealing, and extension. The technique relies on heat-stable polymerase enzymes from thermophilic bacteria.

Mountain weather changes rapidly. A clear morning at the summit can become a snowstorm within two hours, particularly in the shoulder seasons. Experienced climbers carry equipment for conditions they hope they will not encounter.

Compilers transform source code into executable form through several stages. Lexical analysis produces tokens. Parsing builds an abstract syntax tree. Semantic analysis verifies type correctness. Code generation produces target code.

The painter mixed her colors slowly, watching how each pigment interacted with the linseed oil. Some yellows dried with a faint green tint; some reds darkened over weeks into a deep maroon.

The forest in autumn carried a particular smell, a combination of damp leaves and woodsmoke from cabins farther down the valley. The light came through the canopy in thin gold columns, picking out the lichen on the rocks.

Database transactions enforce four properties known as ACID: atomicity, consistency, isolation, and durability. Atomicity means a transaction is all-or-nothing. Consistency ensures the database moves between valid states. Isolation prevents concurrent transactions from interfering. Durability guarantees committed changes survive system failures.

The harbor in the early morning held a dozen fishing boats, their hulls dark against the gray water. The crews moved with quiet efficiency, loading nets and ice, exchanging brief greetings. By the time the sun reached the eastern hills, the boats were already past the breakwater.

Neurons communicate through chemical synapses where neurotransmitters cross a narrow gap and bind to receptors on the receiving cell. Common neurotransmitters include glutamate which is excitatory, GABA which is inhibitory, dopamine which is involved in reward and motor control, and serotonin which modulates mood and digestion.

Container orchestration platforms manage the lifecycle of containerized applications across clusters of machines. Kubernetes provides declarative configuration where the user specifies desired state and the platform reconciles actual state toward it. Pods are the smallest deployable units. Services provide stable network endpoints.

The composer worked at a small upright piano in the corner of her studio. She kept a notebook on the music desk and wrote phrases in pencil as they came to her, often crossing them out and rewriting them several times.

Stars form in giant molecular clouds when regions of higher density collapse under gravity. The collapsing material heats up as it falls inward, eventually reaching temperatures sufficient to ignite nuclear fusion of hydrogen into helium.

Public-key cryptography enables secure communication between parties who have never met by relying on mathematical functions that are easy to compute in one direction but infeasible to reverse. RSA depends on the difficulty of factoring large integers. Elliptic curve cryptography uses the discrete logarithm problem on curve groups.

The library's reading room had vaulted ceilings and tall windows that filled the space with diffuse afternoon light. The tables ran in long rows, each fitted with a small lamp. Students hunched over books and laptops.

Tectonic plates move at speeds comparable to fingernail growth, a few centimeters per year. Their interactions produce earthquakes when stuck boundaries suddenly slip, mountain building when plates collide, and volcanic activity where one plate descends beneath another.

The river formed an oxbow lake where its course had once curved sharply. The cutoff happened during a flood, when the river broke through the narrow neck of the meander. Now the lake sat separated from the main channel.

Garbage collection in programming languages frees memory that is no longer reachable from program references. Reference counting tracks how many pointers exist to each object. Tracing collectors start from root references and follow links to mark reachable objects.

The carpenter measured the door frame twice before making the cut. The wood was old oak, dense and unforgiving of mistakes. He held the saw at the angle his grandfather had shown him, beginning the cut with a few light strokes to establish the kerf.

Climate models simulate the atmosphere through coupled differential equations representing fluid dynamics, radiation transfer, and chemical reactions. They divide the atmosphere into a three-dimensional grid and update each cell according to the physical laws governing its evolution.

The street market spread across two blocks every Saturday morning. Vendors sold vegetables, bread, cheese, flowers, and small household items. Regulars knew which stalls had the best produce and arrived early to claim it.

Functional programming languages emphasize the evaluation of expressions over the execution of statements. Pure functions produce the same output for the same input and have no side effects. Higher-order functions take other functions as arguments or return them as results.

The clockmaker examined each gear under a jeweler's loupe before assembly. Even small imperfections in the teeth could throw the timing off by several seconds per day. He had learned this from his father, who had inherited the workshop from his grandfather.

Renewable energy sources include solar, wind, hydroelectric, geothermal, and biomass. Each has different characteristics in terms of intermittency, geographic suitability, capital cost, and environmental impact. Grid integration requires storage or flexible demand to balance variable supply.

The bookstore on the corner had three floors connected by a narrow spiral staircase. The owner sat near the front, drinking tea and reading. Customers wandered the aisles for hours, sometimes leaving without buying anything, sometimes leaving with armfuls of books.

Vision in vertebrates begins with photoreceptors in the retina. Rods are sensitive to low light but do not distinguish color. Cones provide color vision and acuity but require more light. Signals pass through bipolar and ganglion cells before traveling along the optic nerve to the brain.

The hardware shop carried tools that had been discontinued elsewhere for decades. The owner could find anything in the shelving, though the system was apparent only to him. New customers were given patient guidance to whatever they needed.

Recursive algorithms solve problems by breaking them into smaller instances of the same problem. Base cases handle the smallest instances directly. Recursive cases reduce larger instances toward the base. The call stack grows as recursion deepens and unwinds as results return.

The school playground had a fence around it but the children's voices carried across the surrounding streets. Soccer games, hopscotch, jump rope, and groups standing in animated conversation filled the recess period. The lunch monitor watched from a bench by the door.

Magnetic fields permeate the universe at all scales. Earth's magnetic field deflects solar wind and aurora ripple along its field lines. Galactic magnetic fields shape star formation. Cosmological magnetic fields may have been generated in the early universe.

The bakery began work at three in the morning. The baker measured flour by feel as much as by scale, adding water until the dough resisted his hands with the right tension. Loaves rested in proofing baskets while the ovens heated.

Distributed consensus algorithms allow a collection of processes to agree on a value despite failures. Paxos handles asynchronous networks with possible message loss. Raft simplifies the same problem through explicit leader election. Both guarantee safety under specified failure conditions.

The grandparent's house had a garden that the grandchildren explored every summer. Stones in the rock garden hid lizards. The vegetable patch supplied tomatoes and beans. A small pond held goldfish that grew larger each year.
"""


def main():
    print(f"=== R-RBS-LM-11 — multi-threaded 10× scale-up ===")
    print(f"  torch threads: {torch.get_num_threads()}")
    print(f"  D = {D}, CONTEXT_WINDOW = {CONTEXT_WINDOW}")

    print("\nLoading source model + vocab table...")
    tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
    model = GPT2LMHeadModel.from_pretrained("gpt2")
    model.eval()
    vocab_table = precompute_vocab_table(vocab_size=50257, D=D)
    print(f"  vocab table: {vocab_table.shape}")

    # ---- 1. multi-threaded encode pipeline -----------------------------
    print(f"\n=== Encode pipeline (multi-threaded) ===")
    instrument, observations, timings = encode_source_model_mt(
        CORPUS_BASE, tokenizer, model,
        stride=8, batch_size=32, n_workers=8,
        label="10x_mt",
    )
    print(f"\n=== Timings ===")
    print(f"  harvest: {timings['harvest_s']:.1f}s "
          f"({len(observations)/timings['harvest_s']:.1f} obs/s)")
    print(f"  encode:  {timings['encode_s']:.1f}s "
          f"({len(observations)/timings['encode_s']:.1f} obs/s)")
    print(f"  bundle:  {timings['bundle_s']:.2f}s")
    print(f"  total:   {timings['total_s']:.1f}s for {len(observations)} obs")

    # Save instrument
    out_path = Path("docs/srmech/rbs_lm_research/rbs_lm_instrument_v11.bin")
    out_path.write_bytes(instrument)
    print(f"\nInstrument saved: {out_path}")

    # ---- 2. validate on hallucination corpus --------------------------
    print(f"\n=== Validate on hallucination corpus ===")
    n_total = 0
    n_agree = 0
    per_prompt_results = []
    latencies = []
    for prompt in HALLUCINATION_PROMPTS:
        prompt_ids = tokenizer.encode(prompt)
        # Source argmax
        with torch.no_grad():
            src_out = model.generate(
                torch.tensor([prompt_ids]),
                max_new_tokens=20,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
            )
        src_new = src_out[0][len(prompt_ids):].tolist()
        # RBS-HDC argmax
        rbs_tokens = list(prompt_ids)
        prompt_lats = []
        for _ in range(20):
            t0 = time.time()
            ctx = rbs_tokens[-CONTEXT_WINDOW:] if len(rbs_tokens) > CONTEXT_WINDOW else rbs_tokens
            ctx_vec = encode_context(ctx)
            cand = bind(instrument, ctx_vec)
            res = vectorised_cleanup(cand, vocab_table, D, top_k=1)
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

    overall = n_agree / n_total
    print(f"\n  Overall: {n_agree}/{n_total} ({100*overall:.1f}%)")
    print(f"  Per-token latency: {np.mean(latencies):.1f} ± {np.std(latencies):.1f} ms")
    print(f"  Latency w/ 16 torch threads vs prior 8-thread default: comparison in REPORT")

    print(f"\n=== Comparison across scales ===")
    print(f"  {'Scale':<55} {'n_obs':>7} {'agreement':>12}")
    print(f"  {'R-RBS-LM-5 baseline (single-thread)':<55} {'76':>7} {'0.0%':>12}")
    print(f"  {'R-RBS-LM-8 V2 (single-thread)':<55} {'158':>7} {'0.0%':>12}")
    print(f"  {'R-RBS-LM-9 Path α (single-thread)':<55} {'223':>7} {'0.0%':>12}")
    print(f"  {'R-RBS-LM-11 multi-threaded (this run)':<55} {len(observations):>7} "
          f"{100*overall:>11.1f}%")

    # Save results
    results = {
        "n_observations": len(observations),
        "timings": timings,
        "instrument_bytes": len(instrument),
        "torch_threads": torch.get_num_threads(),
        "n_workers_encode": 8,
        "harvest_batch_size": 32,
        "overall_agreement_pct": 100 * overall,
        "latency_ms_mean": float(np.mean(latencies)),
        "latency_ms_std": float(np.std(latencies)),
        "per_prompt_results": per_prompt_results,
        "comparison": {
            "r_rbs_lm_5_76obs_pct": 0.0,
            "r_rbs_lm_8_v2_158obs_pct": 0.0,
            "r_rbs_lm_9_223obs_pct": 0.0,
            "r_rbs_lm_11_scaled_pct": 100 * overall,
        },
    }
    Path("docs/srmech/rbs_lm_research/rbs_lm_mt_results.json").write_text(
        json.dumps(results, indent=2)
    )
    print(f"\nResults saved.")


if __name__ == "__main__":
    main()
