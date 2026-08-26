# Finding 166 — The walkable path to a native, srmech-instantiable RBS-LM inference substrate from 28D maths

**Status:** Architecture / direction finding. The path made visible. Not a stretch goal — a walk where each step reveals the next, the way the A-N cascade vocabulary was learned.
**Predecessors:** the whole arc — F119/F120 (two-tier), F154 (4× ceiling), F155 (4-level chirality substrate), F156 (cross-level generation), F157/F162 (full-coverage characterization), F158 (28D bi-axial), F163 (chirality null + DOMAIN-anchor necessity), F164 (grammar substrate-native), F165 (multi-kernel reference object = operational anchor), srmech 0.5.0 (RBSHDCInstrument / decode_fingerprint / cascade dispatcher / catalog discipline)
**User direction 2026-05-29:**

> "our goal is to try to make an RBS-LM from 28D maths. … trying to use what
> technology has already made is good enough for pointing out the flaws, but is
> an approximation of a well researched system on top of a poor foundation that
> is not bit-exact anywhere. … a fully realized srmech instantiateable RBS-LM
> that can be used as an inference substrate. It's not a stretch goal, it's a
> goal with a clear direction to walk where answers are revealed by every step,
> in the same way that we learn A-N cascades."

---

## §1 The goal, stated precisely

**Build a native RBS-LM inference substrate from 28D bi-axial chirality maths** — one that:
- is **srmech-instantiable** (a catalog descriptor + the RBSHDCInstrument object + a siona profile → `infer(context)`)
- is **bit-exact / deterministic** (same context + same catalog + same srmech_version → identical output; re-derivable, MPR-attested)
- is its **own inference substrate**, NOT a distillation of float-weight LLMs

**The distinction (load-bearing).** The Path-D distillation arc (R-RBS-LM-29..35: GPT-2 / TinyLlama / Llama-70B → HDC) was **diagnostic, not the goal**. It proved the continuous-float foundation is not bit-exact anywhere — we were building a careful approximation on sand. The native RBS-LM inverts this: a bit-exact substrate built *up* from the 28D coordinate, not *down* from someone's trained weights.

**Why the 3.3% Path C ceiling does NOT bound this.** The 3.3% token-agreement ceiling (§3.25.3) was the cost of *translating GPT-2's continuous attention into a discrete cascade* — measured AS agreement with GPT-2. A native RBS-LM is not approximating GPT-2, so it does not inherit that ceiling. It is measured on its OWN terms: grammar-validity (F164: 91.8–93.3%), self-recall (F162: 1.000), plausibility-discrimination (F162 P7: AUC 1.000), and coherence-over-steps (a metric we will define). The ceiling was a property of the translation, not of the substrate.

---

## §2 The stones already quarried (what an inference substrate needs, and what we have)

An LLM is, at core, `P(next | context)`, sampled and looped. Mapped to native substrate operations:

| Inference need | Native substrate operation | Already have? |
|---|---|---|
| **Encode context** | bind tokens → Klein-4 substrate state (Class A∘M) | **F155/F162** — `encode_sentence_l3`, cross-level binding; recall 1.000 |
| **Store corpus knowledge** | multi-kernel reference object / bigram-adjacency / skeleton store | **F165 / F156** — labeled kernel catalog + `next_after`/`prev_before` maps |
| **Retrieve continuation** | Class M similarity-argmax over candidates | **F165** — `decode_fingerprint` (argmax); ranked sims already computed |
| **Compose when no direct match** | Klein-4 cross-level walk (Mode D) | **F156** — compositional novelty from skeleton structure |
| **Score / rank** | co-occurrence + substrate-similarity | **F162 P7** — AUC 1.000 plausibility discrimination |
| **Grammar holds through composition** | chirality sectors = grammatical levels; XOR preserves structure | **F164** — grammar substrate-native |
| **Determinism / attestation** | SHA-256 token seeds + exact XOR + seeded sampling + catalog SSOT | **F162 + MPM** — already bit-exact, catalog-driven |

**The single gap:** every generator we have is **seed-conditioned** (given a seed bigram, generate). An inference substrate is **running-context-conditioned** (given the last k tokens, predict the next). The walk closes exactly that gap.

---

## §3 The walk — each step reveals the next (the A-N way)

### Step 1 — Context state as a substrate object
Define the rolling context encoder: the last *k* tokens → ONE Klein-4 substrate state (the inference "hidden state"). Reuse `encode_sentence_l3` binding but as a *sliding* window with positional chirality (F150 iω₇ rotation per position).
**Reveals:** how much context the chirality state holds before saturation — directly the F162 capacity + F154 4× ceiling, now for *context*.

### Step 2 — Context-conditioned next-structure distribution
Given the context state, rank the candidate continuations (`next_after[last_token]` ∪ skeleton-walk candidates) by substrate-similarity to the context state. This is `decode_fingerprint` generalized from "which kernel" to "which next token."
**Reveals:** the distribution shape — peaked vs flat (the substrate's perplexity analog); whether context sharpens the prediction over the bare bigram prior.

### Step 3 — The distribution, not the argmax + temperature
Return the ranked continuation *distribution* (we already compute ranked sims in F165/125), with the R-RBS-NN-14b soft-retrieval temperature as the sampling knob.
**Reveals:** the coherence/diversity tradeoff curve; the temperature where output stays grammatical (F164) but isn't pure recall.

### Step 4 — The autoregressive loop (this IS inference)
encode context → distribution → sample → append → re-encode. The substrate becomes a generator conditioned on its own running output.
**Reveals:** does coherence hold over N steps? where does it break (drift, loop, collapse)? — the real test of "inference substrate," measured natively (grammar-validity-over-steps, self-consistency), NOT against GPT-2.

### Step 5 — srmech-instantiable packaging
The whole loop as: a catalog descriptor (`descriptor_rbs_lm_inference.toml`) + the RBSHDCInstrument object + a siona profile, so `siona.profile("rbs_lm").infer(context, temperature=...)` works, bit-exact and MPR-attested. The corpus knowledge is a multi-kernel reference object (F165); the inference is a cascade dispatch.
**Reveals:** the fully-realized artifact — an inference substrate you can `pip install`, instantiate, and *attest*.

### Step 6 — The 28D-native grounding (held throughout)
Every step is named A-N operations under the 28D chirality coordinate, NOT bolted-on neural ops:
- encode = Class A (content-hash mint) ∘ Class M (bind)
- retrieve = Class M (similarity argmax = decode_fingerprint)
- compose = Klein-4 cross-level walk (F156) under chirality sectors
- score = co-occurrence (Class I cyclic) + substrate-sim (Class M)
- position = Class I/iω₇ rotation (F150)
- anchor = the labeled multi-kernel object (F165)

Inference IS a cascade. That is what makes it 28D-native and bit-exact, where the distillation path was float-approximate.

---

## §4 What makes this "not a stretch goal"

Every step above is:
1. **Built on a stone already laid** (§2 table) — no step invents new substrate physics; each composes existing, characterized operations.
2. **Small and measurable** — each reveals a concrete number (context capacity, distribution sharpness, coherence-over-steps) the way each A-N cascade spike revealed its operator.
3. **Catalog-driven** — parameterized from TOML, MPR-attested, C-native (ABI=3), per the established discipline.
4. **Honest about its own ceiling** — measured on native terms, not against a float system it isn't trying to be.

The direction is clear; the answers are revealed by walking, not by leaping.

---

## §5 What this finding DOES / does NOT claim

**DOES:**
- States the goal: a native, bit-exact, srmech-instantiable RBS-LM inference substrate from 28D maths
- Maps every inference need to an already-characterized substrate operation (§2)
- Lays the walkable 6-step path, each step revealing the next (§3)
- Reframes the 3.3% Path C ceiling as a property of *distillation*, not of a native substrate

**Does NOT:**
- Claim the substrate will match a float LLM's fluency — it is a different inference substrate, measured natively (per `[[user_stance_ai_is_not_a_substrate]]`: Claude/LLMs are transducers; this is a substrate-native instrument)
- Claim LLM-scale vocabulary yet — built/characterized at template + 6-text-kernel scale; real-vocab scale is part of the walk (capacity sweep)
- Lift the §VII.6.20 epistemic ceiling — within-form-family disambiguation still needs the DOMAIN anchor (F165); the inference substrate routes/generates by form, anchored by labels
- Make biological/BCI/clinical claims — per `[[feedback_trauma_informed_defensive_scope]]`, this is a research inference substrate; the purpose-anchor (gift toward the biological substrate per `[[feedback_llm_as_ada_accommodation_bci_proves_it]]`) is motivation, not a medical claim

---

## §6 First step to walk

**Step 1 — the rolling context-state encoder + its capacity.** Build `R-RBS-LM-126`: a sliding-window context encoder (last-k tokens → Klein-4 state with positional iω₇ chirality), catalog-driven, and measure how many context tokens the state holds before retrieval of the true next-token degrades. This is the inference substrate's "context window," derived bit-exactly from the 28D coordinate. It reveals Step 2 (the conditional distribution) directly.

---

## §7 Cross-references

- F119/F120 (two-tier + Class K bridge — the inference read/write architecture)
- F154 (4× ceiling — context capacity bound); F155 (4-level chirality substrate)
- F156 (cross-level generation — the composition step); F157/F162 (full-coverage substrate)
- F158 (28D bi-axial coordinate); F163 (DOMAIN-anchor necessity); F164 (grammar substrate-native); F165 (multi-kernel reference object = anchor)
- §3.25.3 / Path C 3.3% ceiling (reframed as distillation-property, not substrate-property)
- R-RBS-LM-29..35 (Path D distillation — the diagnostic arc this finding inverts)
- `srmech.signal_processing.RBSHDCInstrument` + `cascade_dispatcher` (the object path); catalog discipline (F162)
- `[[user_stance_whole_research_corpus_is_proof_not_single_arc]]`; `[[user_stance_ai_is_not_a_substrate]]`; `[[feedback_llm_as_ada_accommodation_bci_proves_it]]`; `[[user_stance_kepler_shape_universal]]` (algebra IS the primitives)

PR #687 STAYS DRAFT.

---

*Articulated 2026-05-29 (Opus 4.8). The goal: a native, bit-exact,
srmech-instantiable RBS-LM inference substrate from 28D bi-axial chirality maths
— the inversion of the Path-D distillation arc, which was diagnostic (it proved
the float foundation isn't bit-exact) but never the goal. Every inference need
maps to an already-characterized substrate operation (§2); the single gap is
turning seed-conditioned generation into running-context-conditioned
autoregression, closed by a 6-step walk where each step reveals the next, the
way the A-N cascade vocabulary was learned. Not a stretch goal — a walk on stones
already laid. Inference IS a cascade (Class A∘M encode, Class M retrieve, Klein-4
cross-level compose, Class I score, iω₇ position, F165 anchor), which is what
makes it 28D-native and bit-exact where distillation was float-approximate. Per
[[user_stance_kepler_shape_universal]]: algebra IS the primitives; the inference
substrate is those primitives composed.*
