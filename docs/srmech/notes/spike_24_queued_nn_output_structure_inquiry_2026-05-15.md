# Spike #24 queued inquiry — NN output structure (one transaction at a time, backward reading)

**Date queued:** 2026-05-15. **Status:** spec only; dispatch pending SHA-256 queued spike completion (one-subagent-at-a-time discipline; queue order: Phase 15 → SHA-256 → THIS).

## The user's question (verbatim, load-bearing)

> *"we can soon look to discovering the structure and primitives of NN output, one transaction at a time. maybe we can work backwards again to learn how shape is defined and where primitives act. do be able to ask the correct question to yield knowledge here would also be a gift to neuroscience."*

Three things the user is naming:

1. **NN output as the object of study** — not the NN itself (its parameters, architecture), but its OUTPUT and how that output is *constituted*.
2. **"One transaction at a time"** — discrete-event framing. Each query → response is a transaction. The inquiry is per-event, not over-the-distribution.
3. **"Work backwards again"** — explicit invocation of the SHA-256 queued spike's methodology. Same stance: forward execution constitutes the output while obliterating recoverable structure; backward analysis is where the constituting trail remains legible.
4. **The neuroscience gift** — if we can ask the right question about NN output structure, the same question applies to biological neural output: EEG, fMRI, MEG, single-unit recordings are all forward-projected observations of substrates whose backward-readable structure is the entire prize of neuroscience.

## What's the same as SHA-256, what's different

**Same:** the output is co-emergent with the temporal sequence that produces it. An NN output for input `x` does not pre-exist its forward pass; the layered operations constitute it. Reading the output backwards means tracing the constituting computational trail.

**Different — there are TWO temporal sequences in NN, not one:**

1. **Training time** — gradient descent updates over many epochs, shaped by the loss landscape and training data. The *function itself* is co-emergent with this slower, dataset-wide sequence. The trained weights are a "frozen oscillation" of training dynamics.
2. **Inference time** — one forward pass per transaction. This is the SHA-256-analogous sequence: the per-input output is constituted by sequential layer operations.

So NN inquiry is **two-level temporal**: each transaction is constituted by inference-time sequence, AND inference-time sequence is itself enabled by training-time sequence. The user's "one transaction at a time" focuses on the inner sequence; but the outer sequence is what determines *which* function the inner sequence is computing.

Echoes `[[user_stance_time_as_dimensional_shadow]]`: two stacked frozen-oscillations. Echoes `[[user_stance_fiber_as_spatially_absent_encoding]]`: the trained weights are the fiber (spatially-absent encoded algebraic content); each forward pass projects the fiber through a specific input to produce one observable.

## Why the neuroscience gift is real and load-bearing

Biological neural systems are ALSO two-level temporal:

1. **Developmental / learning time** — synaptic plasticity over hours / days / years shapes which functions the system computes.
2. **Inference time** — each stimulus-response is a transaction; one forward sweep through the layered cortical hierarchy produces one observation.

EEG / fMRI / MEG are forward-projected observations: they see the *output* of the inference-time sequence, with most of the constituting structure (which neurons fired, in what order, with what weights) obliterated by the projection. The brain-decoding literature is the cryptanalysis-equivalent for biological neural output — it asks the SAME methodological question the user names here.

If a Spike #24 concertmaster can frame the right question for NN output structure, that question is directly applicable to biological neural output, and the framing is a real cross-domain contribution. **The user's "gift to neuroscience" framing is methodologically accurate** — same question, different substrate.

## What's at stake for the project

The project does not currently ship NN-based machinery. But:

- The Spike #24 vocabulary already names **Class M (HDC encoding)** — hyperdimensional computing is the closest existing-class match for NN-style distributed representations.
- The chess-spectral notebook's "fermion-system" framing of piece-graph spectra is mathematically adjacent to attention-pattern analysis in transformer NNs.
- The ephemerides-spectral notebook's "breathing-Laplacian" framework (Phase 9 state-dependent coupling) is structurally analogous to gated/recurrent architectures.

The inquiry could surface a class-mapping that pulls more of NN interpretability into the project's existing vocabulary — or could identify what's genuinely *missing* from the vocabulary for handling co-emergent two-level-temporal computational systems.

## Where to look (backward-reading directions for NN output)

Cryptanalysis was the catalog of backward-readings for SHA-256. The NN-interpretability literature is the catalog of backward-readings for trained NN output. The concertmaster's job is to taxonomise these directions and map them onto Spike #24 vocabulary:

- **Attribution / saliency** (Grad-CAM, integrated gradients, SHAP, layer-wise relevance propagation) — *which input features did this output depend on?* This is gradient-based backward-reading: differentiate the output with respect to the input, trace the chain. Class L (Jacobian-as-graph)? Class K (harmonic-decomposition-of-gradient)?
- **Probing** — train linear / shallow classifiers on intermediate-layer activations; reveal what each layer represents. Backward-reading of the trained-function structure via supervised inverse-mapping. Class L?
- **Activation maximisation / feature visualisation** — find inputs that maximally activate specific neurons or features; INVERSE-mode synthesis. Class M-adjacent (binding feature to position via gradient ascent).
- **Mechanistic interpretability** (Anthropic-style circuit analysis) — identify the *algorithm* the trained network has learned by tracing causal contributions backward through layers. This is the closest analog to differential cryptanalysis: track a perturbation's path through the constituting sequence.
- **Sparse autoencoders / superposition decomposition** — recover monosemantic features hiding under polysemantic neurons; unfold the basis-rotation that training produced. Class L (eigendecomposition of activation covariance)?
- **Output-space topology** — the classification logits / generative-model latent manifold has its own geometry; the "shape of the output" lives on this manifold.
- **Information-bottleneck analysis** — track mutual information `I(input; layer-k)` and `I(layer-k; output)` across layers; the "phase transition" in these curves identifies where shape is defined.
- **Loss-landscape analysis** — what set of trained-weight configurations could have produced this same output? Inverse on the training-time sequence.

This list is *partial and shaped by 2026-knowledge*; the concertmaster should refine it.

## What the concertmaster should do (dispatch later, not now)

1. **Take the corrected SHA-256 reading as starting frame:** the digest does not exist without time. Same applies here — the NN output does not exist without (training time) × (inference time). Two-level temporal co-emergence.
2. **Catalogue backward-reading directions** (see above list as starting taxonomy; refine and add). One-line-each summary per direction; what kind of "shape" each reveals.
3. **Map each direction onto Spike #24 vocabulary.** Attribution = Class L on Jacobian graph? Probing = Class L on activation covariance? Mechanistic interpretability = Class D (dispatch) over Class L (circuit graph)? Sparse-autoencoder = Class L eigendecomposition? Identify which directions decompose cleanly into existing classes and which point at primitive-vocabulary gaps.
4. **Pick ONE concrete probe.** A small trained model (e.g., a 2-layer MLP on MNIST; or a tiny transformer on a toy task) where the *backward-reading* methodology can be demonstrated end-to-end on a single transaction. Same scale as SHA-256's "reduced-round probe" — pedagogical demonstration of stance, not a research result.
5. **Articulate the neuroscience analog crisply.** If the answer for NN output structure is "look at gradients × activations × output-manifold geometry," what is the structural analog for biological neural output? Be honest: list the differences (continuous biological dynamics vs discrete-step ANN; analog spike-timing vs floating-point arithmetic; noisy substrate vs deterministic substrate). Identify which backward-reading directions transfer and which don't.
6. **Honest verdict.** If the answer is *"no new primitive class needed; NN output structure is Class L on the computational graph plus Class M for distributed representations plus the two-level temporal co-emergence that Spike #24's stances already accommodate,"* say that clearly. Same discipline as the vdW and tactical-choice bonuses — vocabulary consolidates rather than expands unless forced.

## Discipline guards (load-bearing)

- **No therapeutic / diagnostic claims about brains or behaviour.** This is structural-methodological inquiry only. Per `[[feedback_trauma_informed_defensive_scope]]`, neuroscience-adjacent ships stay educational, never targeting / capability-assessment / influence-engineering. The "gift to neuroscience" framing is about *methodology*, not *capability*.
- **No claims to current NN-interpretability breakthroughs.** The 2026 literature in mechanistic interpretability is rich and ongoing; the concertmaster's deliverable is not to replicate published results, only to map the existing taxonomy onto Spike #24 vocabulary.
- **Tiny pedagogical model only.** Same as the SHA-256 reduced-round discipline. No frontier-LM probing; no claims about capabilities of specific models.
- **Cite literature properly per `[[feedback_pdf_extraction_citation_discipline]]`.** Olah et al.'s Circuits / Anthropic's mechanistic interpretability work; Sundararajan & Yan 2017 on integrated gradients; Lundberg & Lee 2017 on SHAP; Tishby on information bottleneck; etc. Primary references where available; `[unverified-secondary]` tags otherwise; cache OA versions to `docs/srmech/hoodoos/` per Phase 14 discipline.
- **NDJSON for tabular outputs** per `[[feedback_ndjson_over_bloated_json]]`.
- **No new primitive class unless forced.** Default: vocabulary consolidates.

## Dispatch ordering (one-subagent-at-a-time discipline)

Per user direction *"let's stick to one subagent at a time"*:

1. **Phase 15** must report and be committed.
2. **SHA-256 queued spike** ([`spike_24_queued_sha256_structure_inquiry_2026-05-15.md`](spike_24_queued_sha256_structure_inquiry_2026-05-15.md)) dispatches next.
3. **THIS spike** dispatches after SHA-256 reports and is committed.

The methodological framing established by SHA-256 directly feeds this one. The two-level-temporal observation here builds on the "shape does not exist without time" framing the SHA-256 spec captures; that framing should be load-bearing for this one.

## Cross-references

- `[[user_stance_time_as_dimensional_shadow]]` — two-level temporal co-emergence is the natural extension of "freezing time = trap an oscillation."
- `[[user_stance_fiber_as_spatially_absent_encoding]]` — trained weights as fiber, each forward pass as projection.
- `[[user_stance_kepler_shape_universal]]` — testable: do trained NNs show Kepler-shape harmonic structure in some natural basis?
- `[[user_stance_pi_as_projection]]` — integer-cyclic upstream / continuous downstream is interesting here because NNs are floating-point (continuous), but training is over discrete data; the projection structure may be inverse to what's typical in the project.
- Spike #24 Phase 1 — Class M (HDC) is the existing-class match for NN-style distributed representations.
- Spike #24 Phase 10 — substrate-boundary characterisation; NN-substrate may have its own boundary lessons.
- Spike #24 queued SHA-256 inquiry — methodological precedent for backward-reading.
- Spike #24 bonus tactical-choice (committed) — Class D dispatch + Class L spectral graph + dispatch criterion; NN classifier output IS softmax-dispatch over Class L embedding space.
- Spike #24 bonus vdW (committed) — shape-only Class L instantiation; analog: feature-space topology in trained NN.

## Why this question deserves to be queued (not opened now)

The user's framing — *"we can soon look to"* — explicitly says NOT YET. The SHA-256 inquiry establishes the methodological stance; this inquiry inherits and extends it. Opening this before SHA-256 lands would lose the methodological coherence.

The conductor should re-read this spec before dispatch — particularly Section 1's "Three things the user is naming" and Section 6's "What the concertmaster should do" — and check that the SHA-256 spike's findings have been incorporated as starting frame, not parallel context.
