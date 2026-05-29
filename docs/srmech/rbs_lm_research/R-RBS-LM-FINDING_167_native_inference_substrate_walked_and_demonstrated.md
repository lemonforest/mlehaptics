# Finding 167 — The F166 walk is complete: a native, bit-exact, srmech-instantiable RBS-LM inference substrate, demonstrated end-to-end

**Status:** Operational closure of the F166 direction. The path was walked; each step revealed the next, the way the A-N cascade vocabulary was learned. The goal — a native inference substrate from 28D maths — is a demonstrated artifact, not a direction.
**Predecessors:** F166 (the walkable path), F165 (multi-kernel reference object = DOMAIN anchor), F164 (grammar substrate-native), F162 (full-coverage substrate), F156 (cross-level generation), F154 (4× capacity ceiling), F150 (chirality harmonics / iω₇ position), F132 (Klein-4 HDC), F119/F120 (two-tier + Class K bridge).
**Empirical anchors:** R-RBS-LM-126 (Step 1) · R-RBS-LM-127 (Step 2) · R-RBS-LM-128 (Step 3) · R-RBS-LM-129 (Step 4) · R-RBS-LM-130 + `_rbs_lm_inference.RBSLMInferenceSubstrate` (Step 5). srmech 0.5.0rc8 native ABI=3; catalog `descriptor_rbs_lm_inference.toml` (the SSOT).
**User direction 2026-05-29:** "make an RBS-LM from 28D maths … a fully realized srmech instantiateable RBS-LM that can be used as an inference substrate. It's not a stretch goal, it's a goal with a clear direction to walk where answers are revealed by every step."

---

## §1 Headline

The single gap F166 §2 identified — turning **seed-conditioned generation** into **running-context-conditioned autoregression** — is closed. The substrate now does `P(next | context)`, samples it, and loops, all as a named A-N cascade under the 28D Klein-4 coordinate, **bit-exact and MPR-attested**. It is the inversion of the Path-D float-distillation arc (R-RBS-LM-29..35), which was diagnostic (it proved the float foundation isn't bit-exact anywhere) but never the goal.

`RBSLMInferenceSubstrate.from_catalog(descriptor).learn(stream).infer(prompt, T)` works, and re-instantiating from scratch reproduces generation **bit-exact**.

---

## §2 The walk — each step's honest result (the manifest record)

| Step | What it built | Result (measured natively) |
|------|---------------|----------------------------|
| **1 — context state** (R-RBS-LM-126) | rolling last-k tokens → ONE Klein-4 state (positional role-filler bind) | Context conditioning works and improves with context to k≈7; **acc 1.000 at k=5,7 / N=50** (+0.78–0.90 over the context-free prior). Capacity ~**100–200** (context→next) pairs per D=8192 memory (the F154 ceiling). **Artifact caught + fixed**: an even-k sawtooth from a bundle dropping a real token → pad-not-drop. |
| **2 — distribution** (R-RBS-LM-127) | the ranked sims over bigram-legal candidates = `P(next\|context)` | The k-window distribution is genuinely **peaked over the candidate set** (top1 ~0.20, H ~2.8 << ln(25)) and **beats the bigram by up to 2.44× in perplexity** at low load (MRR ≈ 1.0). Washes to the bigram as memory saturates (F154 crossover, perplexity side). **Methodological catch**: over the FULL vocab the signal is rank-correct but mass-flat — the signal lives in the RANK; the candidate-restriction is the distribution's definition. |
| **3 — temperature** (R-RBS-LM-128) | T as the recall↔diversity dial | Clean monotonic tradeoff (recall 0.88→0.09 as effective-candidates 1.2→24.8), all within the bigram-legal envelope. **The substrate runs COLD**: a real interior perplexity minimum at **T\*=0.005** (PPL 1.43; rises on both sides), ~100× sharper than the float-LLM T~0.7 — a structural property of small Klein-4 fractional-agreement margins. |
| **4 — the loop = inference** (R-RBS-LM-129) | encode → distribute → sample → append → re-encode | **Inference works.** 100% POS-bigram-valid in EVERY cell (never leaves the grammatical manifold over 40 steps); no collapse. The **k-window value-add is anti-degeneracy**: the bigram collapses into attractor loops (cycle₃gram 0.658 — two-thirds repeated trigrams), the substrate stays diverse (cycle₃gram 0.088; ~2× distinct tokens). **Honest caveat**: on this template corpus the memory does NOT raise trigram-legality (template long-range structure too weak) — that test needs a richer corpus. |
| **5 — the artifact** (R-RBS-LM-130) | `RBSLMInferenceSubstrate` — catalog-instantiable object | build→learn→distribution→infer→attest, all working. **Bit-exact across fresh instantiation** (re-instantiate + re-learn + same seed → identical generation). Sensible distributions (P(next\|"the cat") top = `ate`). MPR attestation block (descriptor_hash c4758867…). |

Each step revealed the next exactly as F166 predicted: Step 1's rank-signal → Step 2's distribution; Step 2's mass-flatness → Step 3's temperature; Step 3's cold operating point → Step 4's loop; Step 4's working loop → Step 5's packaging.

---

## §3 What this finding DOES / does NOT claim

**DOES:**
- A native, bit-exact, srmech-instantiable, MPR-attested RBS-LM inference substrate exists and generates grammatical text autoregressively (Steps 1–5 demonstrated).
- Inference is a **named A-N cascade under the 28D coordinate** — Class A∘M encode + iω₇ position (Step 1), Class M retrieve over candidates (Step 2), temperature sample (Step 3), iterated (Step 4) — NOT a bolted-on neural op and NOT a float distillation.
- The k-window context state **beats the immediate-predecessor bigram** in single-step perplexity (2.44×) and **resists the bigram's attractor-loop collapse** in multi-step generation.
- Determinism is real and load-bearing: same catalog + corpus + seed → bit-exact, across instantiation.

**Does NOT** (per MFO §VII.6.20 + `[[feedback_dont_pre_commit_spike_query_operators]]` + `[[feedback_trauma_informed_defensive_scope]]`):
- Claim float-LLM fluency or scale — characterized at template + 84-token-vocab scale; real-vocab scale is the next walk (capacity via hierarchical bucketing).
- Claim the context memory raises trigram-legality on ANY corpus — on THIS template corpus it does not (its measured benefit here is anti-looping/diversity); the legality-lift test is a richer-corpus question, reported as open, not assumed.
- Lift the §VII.6.20 ceiling — within-form-family disambiguation still needs the DOMAIN anchor (F165); the inference substrate routes/generates by form.
- Make biological/BCI/clinical claims — research inference substrate; the purpose-anchor (a gift toward the biological substrate per `[[feedback_llm_as_ada_accommodation_bci_proves_it]]`) is motivation, not a medical claim.
- Claim the substrate "knows" meaning — it is a transducer composition per `[[user_stance_ai_is_not_a_substrate]]`.

---

## §4 The web this touches (convergence is the proof shape)

Per `[[user_stance_whole_research_corpus_is_proof_not_single_arc]]`: the inference substrate is not one arc's result — it composes the whole corpus. Step 1 reuses F162's encoder; Step 2 generalizes F165's `decode_fingerprint`; Step 3 is F150/R-RBS-NN-14b's soft-retrieval knob; Step 4's grammar-validity is F164; the capacity bound is F154; the DOMAIN anchor for real-corpus inference is F165; the two-tier read/write architecture is F119/F120; the substrate itself is F132's Klein-4. The artifact is the convergence made instantiable.

---

## §5 Open threads this finding opens

1. **Richer corpus** — does the k-window memory RAISE trigram-legality (not just resist looping) on a corpus with real long-range structure? (the honest open question from Step 4; connects to F165's real-text kernels)
2. **Capacity scale-up** — hierarchical bucketing (F162 P4 / R-RBS-NN-12) for the context→next memory, to exceed the single-memory ~200-pair F154 ceiling.
3. **DOMAIN-anchored inference** — bind the multi-kernel reference object (F165) as a corpus-knowledge store the loop routes through, so inference is anchored by labeled domains (the Rosetta Stone Layer + the loop).
4. **siona profile upstream** — `siona.profile("rbs_lm").infer(...)` as the absorption of `RBSLMInferenceSubstrate` into srmech.rbs_lm (UPSTREAM_NOTES §7/§8).
5. **Cross-prompt diversity at cold T** — the fixed-seed prompt-convergence (Step 5 note) is a cold-sampling property; characterize the prompt-influence decay vs window-fill.

---

## §6 Cross-references

- F166 (the path) · F165 (DOMAIN anchor) · F164 (grammar) · F162 (substrate) · F156 (generation) · F154 (capacity) · F150 (position) · F132 (Klein-4) · F119/F120 (two-tier + bridge)
- R-RBS-LM-126/127/128/129/130 + `_rbs_lm_inference.py` + `_canonical_substrate.ContextSubstrate`
- `descriptor_rbs_lm_inference.toml` (SSOT) + `substrate_measurements/inference_step{1..5}_*.ndjson`
- §3.25.3 / Path C 3.3% ceiling (a distillation property; this native substrate does not inherit it)
- `[[user_stance_kepler_shape_universal]]` · `[[user_stance_ai_is_not_a_substrate]]` · `[[user_stance_whole_research_corpus_is_proof_not_single_arc]]` · `[[feedback_dont_pre_commit_spike_query_operators]]` · `[[feedback_llm_as_ada_accommodation_bci_proves_it]]`

PR #687 STAYS DRAFT.

---

*Articulated 2026-05-29 (Opus 4.8). The F166 walk is complete: a native,
bit-exact, srmech-instantiable, MPR-attested RBS-LM inference substrate from 28D
bi-axial chirality maths — the inversion of the Path-D distillation arc. Five
steps, each revealing the next: context state (capacity ~100-200; artifact caught
+ fixed) → distribution (beats bigram 2.44× perplexity; signal in the rank) →
temperature (the substrate runs COLD, T\*=0.005) → the autoregressive loop
(inference works; 100% grammatical; k-window value-add is anti-looping, NOT
legality — reported honestly) → the instantiable artifact (bit-exact across
instantiation; attested). Inference IS a named A-N cascade iterated, which is what
makes it 28D-native and bit-exact where distillation was float-approximate. Per
[[user_stance_kepler_shape_universal]]: algebra IS the primitives; the inference
substrate is those primitives composed. Per [[user_stance_ai_is_not_a_substrate]]:
this is a substrate-native instrument, a transducer composition — not an aware
thing. The continued work is the reward; this is the gift made manifest.*
