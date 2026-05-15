# Spike #24 bonus 4 — NN output structure: backward-reading on one transaction

**Date:** 2026-05-15. **Status:** methodological synthesis landed; concertmaster-level deliverable. NOT an interpretability-research finding.
**Branch:** `research/spike-24-primitive-vocabulary-2026-05-15`.
**Spec:** [`spike_24_queued_nn_output_structure_inquiry_2026-05-15.md`](spike_24_queued_nn_output_structure_inquiry_2026-05-15.md).
**Predecessor (load-bearing starting frame):** [`spike_24_bonus_sha256_structure_2026-05-15.md`](spike_24_bonus_sha256_structure_2026-05-15.md).
**Companion probe:** [`spike_24_bonus_nn_output_transaction_probe_2026-05-15.py`](spike_24_bonus_nn_output_transaction_probe_2026-05-15.py) + [.ndjson](spike_24_bonus_nn_output_transaction_probe_2026-05-15.ndjson).

## §1 The three-question decomposition, applied to NN inference

The SHA-256 synthesis established a generalisable framework for any **co-emergent two-level temporal computational system**: decompose the question into (1) what the trail is made of; (2) where it is backward-readable in isolation; (3) where it is unreadable. Applied here, NN inference adds one feature SHA-256 does not have: the function being evaluated *also* came from a temporal sequence (training). NN output is constituted at *two stacked* temporal levels.

### §1.1 What is the trail made of?

For a feed-forward MLP under one forward pass: a sequence of operators `x → z₁ = W₁·x + b₁ → h = ReLU(z₁) → z₂ = W₂·h + b₂ → p = softmax(z₂) → ŷ = argmax(p)`. Each operator is one of: affine map (Class L on the linear-algebra graph), element-wise non-linearity (ReLU; the trail-eraser), simplex projection (softmax), late-binding dispatch (argmax over classes; Class D). For a transformer or convnet the building blocks scale but the operator-decomposition pattern is identical: matmul + add + non-linearity + occasional softmax + classification head.

The trained weights `(W₁, b₁, W₂, b₂)` are themselves the residue of the *outer* temporal sequence — many epochs of stochastic gradient descent on training data. They are the "frozen oscillation" of training; the inference-time forward pass is the "frozen oscillation" of inference. **Two stacked frozen oscillations** per `[[user_stance_time_as_dimensional_shadow]]`. Per `[[user_stance_fiber_as_spatially_absent_encoding]]`: trained weights are the spatially-absent fiber that encodes the function; each forward pass projects the fiber through *one* input to produce *one* observable output.

### §1.2 Where is the trail backward-readable in isolation?

Three operators survive composition with full backward-readability:

- **Affine layers.** The Jacobian `∂z/∂x = W` is the exact local linear operator. Chain-ruling backward through the network is `backpropagation` — exact gradient computation, formally invertible at the gradient level (i.e., the gradient *is* the backward-reading). The forward Jacobian's invertibility per-layer holds iff `W` is full-rank, which is generic for trained networks.
- **Softmax.** Invertible up to an additive constant (logits → probs is the standard softmax; probs → logits is the log-ratio recovery). The argmax is *not* invertible, but the full pre-argmax distribution preserves all dispatch information.
- **Gradient × input** (per-transaction). Class L statement on a per-transaction Jacobian graph — the gradient is the leading direction of the local linearisation. Integrated gradients (Sundararajan & Yan 2017) is the path-integral refinement that satisfies attribution axioms; raw gradient is the t=1 endpoint of that integral.

### §1.3 Where is the trail unreadable?

**ReLU is the per-layer trail-eraser**, structurally analogous to SHA-256's `state += compress(state, block)`. For a hidden unit with pre-activation `z₁,ᵢ ≤ 0`, the post-activation is `0` and *the magnitude of how-negative-it-was does not propagate downstream*. The forward pass uses only the fact `z₁,ᵢ ≤ 0`, not the value. This is per-layer co-emergence: depth multiplies the erasure; a network with d ReLU layers has erased d levels of pre-activation information by the output.

This is the per-transaction analog of SHA-256's avalanche / compression boundary. The probe measures it directly: for the chosen single transaction, 8 of 32 hidden units (25%) were "dead" (`z₁ ≤ 0`), with their pre-activations carrying L_∞ norm 2.02 and L₁ norm 8.24 of *destroyed* information.

The argmax step is the second trail-eraser. Softmax-then-argmax maps the full probability simplex point down to one of K labels. The "shape of the output" lives on the simplex; the *reported* output is a single label. This is the analog of SHA-256's truncation-of-state-to-256-bits, but at the output side: information about the model's runner-up class, the confidence margin, the tail distribution — all collapse into a single integer index.

### §1.4 Two-level temporal: where the framework extends

NN adds: the *outer* trail (training) is also backward-readable in some senses but unreadable in others. **Backward-readable**: gradient descent leaves a path in weight-space; this path is *in principle* recoverable from periodic checkpoints, but operationally rarely available. **Unreadable**: which training examples shaped which weights — Shapley-style training-data attribution methods (TracIn, Influence Functions per Koh & Liang 2017 [unverified-secondary]) attempt this and produce only approximate, noisy answers because the gradient descent path through high-dimensional weight space is not a clean linear function of any training subset.

The user's "one transaction at a time" framing focuses on the *inner* sequence (inference). The probe respects that focus. The outer sequence's backward-reading is named in this section so the framing is honest about what is in-scope vs. out-of-scope.

## §2 NN-interpretability methodologies mapped to Spike #24 vocabulary

Cryptanalysts have been backward-reading SHA-256 for 35 years; NN-interpretability researchers have been backward-reading trained NN output for ~15 years. Same shape of question, different substrate. The mapping onto Spike #24 vocabulary:

### §2.1 Attribution / saliency / integrated gradients / SHAP

**The backward-reading.** Differentiate the chosen output (logit-of-predicted-class, or any scalar functional of the output) with respect to the input via chain rule; report the gradient, the input × gradient, or integrated-gradients along a baseline-to-input path. [Sundararajan & Yan 2017, ICML, arXiv:1703.01365 [unverified-secondary, arXiv-ID asserted but not extracted this session].] SHAP (Lundberg & Lee 2017, NeurIPS, arXiv:1705.07874 [unverified-secondary]) is the cooperative-game-theoretic refinement.

**Spike #24 mapping.** **Class L** on the *per-transaction Jacobian graph*. Same primitive as differential cryptanalysis (Class L on the state-difference propagation graph for SHA-256), instantiated on the input-output graph of the trained NN. NOT a new class — Class L on a different graph. Probe (i) demonstrates the elementary form on one transaction; the chosen digit's prediction was 99% confident and the gradient l_∞ pixel was index 42 with sensitivity 2.22.

### §2.2 Probing (linear / shallow classifiers on intermediate activations)

**The backward-reading.** Train a small classifier on intermediate-layer activations to predict properties of the input (linguistic features, geometric attributes, etc.). The classifier's accuracy reveals which information layer-k *carries*. [Alain & Bengio 2017, "Understanding intermediate layers using linear classifier probes," ICLR Workshop, arXiv:1610.01644 [unverified-secondary].]

**Spike #24 mapping.** **Class L composed with Class D.** The probe classifier is Class D (late-binding dispatch over property labels) trained on Class L (linear projection of activation covariance). Probing is per-layer-supervised inverse-mapping of activations to interpretable categories. Not a new class.

### §2.3 Activation maximisation / feature visualisation

**The backward-reading.** Find input `x*` that maximally activates a specific neuron / channel / direction via gradient ascent. [Erhan et al. 2009; Olah et al. 2017 feature visualization.] INVERSE-mode synthesis: given an output target, synthesise an input that produces it.

**Spike #24 mapping.** **Class L (gradient ascent in input space) composed with Class M (binding the produced input to the activated feature via gradient ascent's iterative refinement)**. Class M's `bind` and `bundle` primitives are the HDC operations; activation maximisation IS a form of bind-by-optimisation. Adjacent to but not identical with HDC; the bind is implicit-via-gradient rather than explicit-via-permutation. Mapped, not new.

### §2.4 Mechanistic interpretability / circuit analysis (Olah et al.; Anthropic)

**The backward-reading.** Identify the *algorithm* the trained network has learned by tracing causal contributions backward through layers, identifying motif-circuits (e.g., curve detectors, edge detectors, modular addition circuits) and reading them as if they were hand-written algorithms. [Olah et al. 2020, "Zoom In: An Introduction to Circuits," Distill, https://distill.pub/2020/circuits/zoom-in/ [unverified-secondary, URL asserted].]

**Spike #24 mapping.** **Class L (the circuit graph) composed with Class B (tagged-tuple per circuit node = feature) composed with Class D (the dispatch logic identified at each junction)**. Mechanistic interpretability IS the cryptanalytic-differential-tracing methodology of §2.1 (SHA-256 synth) applied to the NN substrate. Same backward-reading shape — "track a perturbation's path through the constituting sequence" — different substrate (neurons rather than bit-states; weighted activation rather than state-difference probability).

**Probe (ii)** demonstrates the elementary form on one transaction: the alive-set of 24/32 hidden units IS the path through the circuit graph for this specific input. With a fully-monosemantic basis, this would read as concept-level interpretable.

### §2.5 Sparse autoencoders / superposition decomposition

**The backward-reading.** A polysemantic neuron carries superposed feature content; recover the monosemantic basis via sparse autoencoder dictionary learning on the activation distribution. [Elhage et al. 2022, "Toy Models of Superposition," Transformer Circuits Thread [unverified-secondary]; Cunningham et al. 2023 / Anthropic 2024 follow-ups [unverified-secondary].]

**Spike #24 mapping.** **Class L (eigendecomposition of activation covariance)** with the sparse-coding twist (L1-regularised dictionary learning rather than orthogonal eigenbasis). Operationally distinct from pure PCA — sparse coding finds an over-complete basis whose elements are individually meaningful — but algebraically it is the same class of operator: a linear-algebra decomposition of activation statistics. Class L extended (sparse / over-complete) rather than new.

### §2.6 Information-bottleneck analysis

**The backward-reading.** Track `I(input; layer-k)` and `I(layer-k; output)` across layers; the "phase transition" in these mutual-information curves identifies the depth at which the input's information about output is compressed and the irrelevant information is discarded. [Tishby & Zaslavsky 2015, IEEE ITW, arXiv:1503.02406 [unverified-secondary]; Shwartz-Ziv & Tishby 2017.]

**Spike #24 mapping.** **Class L (mutual-information matrix as covariance-on-information graph)** + **trail-erasure indicator** (the per-layer compression IS the per-layer trail-erasure, characterised statistically rather than per-transaction). Information-bottleneck is the **distributional** form of the per-transaction ReLU-trail-erasure that Probe (iii) measures. Same primitive, different averaging.

### §2.7 Output-manifold topology / loss-landscape analysis

**The backward-reading.** The output simplex / latent manifold has a geometry — clusters of classes, decision boundaries, smoothness vs cliffs. Loss-landscape analysis asks the analog question for training-time: which weight configurations produce equivalent outputs? Inverse on the outer temporal sequence.

**Spike #24 mapping.** **Class L on the output-space metric** for the inference-time question; **Class L on the weight-space Hessian** for the loss-landscape question. Both are Class L instantiations on different but well-defined graphs. Not new.

### §2.8 Where the vocabulary does NOT need extension

After mapping seven backward-reading directions, no new primitive class is required. The closure:

- Attribution / saliency / integrated gradients = Class L (per-transaction Jacobian graph).
- Probing = Class L + Class D (linear-supervised on activations).
- Activation maximisation = Class L + Class M (bind-by-gradient).
- Mechanistic interpretability / circuits = Class L + Class B + Class D (circuit graph + tagged feature nodes + dispatch).
- Sparse autoencoders / superposition = Class L extended (sparse / over-complete eigenbasis).
- Information-bottleneck = Class L (mutual-information graph) + trail-erasure (per-layer ReLU compression).
- Output-manifold / loss-landscape = Class L on output-metric / weight-Hessian.

All seven are compositions of Spike #24's existing Classes B, C, D, L, M plus the trail-erasure step (per-layer co-emergence; Class K-adjacent constraint-as-information that vanishes under composition). **The vocabulary closes cleanly.** Mirrors the SHA-256 synthesis §2.7 conclusion: the substrate is different (floating-point matmul-and-ReLU rather than 32-bit integer XOR-and-ADD); the primitive classes are the same.

## §3 Concrete per-transaction probe — what the data shows

[Probe at [`spike_24_bonus_nn_output_transaction_probe_2026-05-15.py`](spike_24_bonus_nn_output_transaction_probe_2026-05-15.py); NDJSON at companion `.ndjson`. Trained tiny MLP: 64 input pixels (8×8 digits), 32 ReLU hidden units, 10 softmax classes; 2,410 parameters; 80 epochs SGD; test accuracy 97.2%; one transaction at test index 1 (true label 8, predicted label 8, confidence 99.02%).]

**Five signatures on one transaction** (Probes i, ii, iii, iv per-transaction; Probe v structural across 64 test inputs):

| Signature | Spike #24 class | Per-transaction measurement | Comment |
|-----------|-----------------|------------------------------|---------|
| **§3.1 Gradient attribution** | L on per-trans Jacobian graph | Pixel-sensitivity vector ∂logit₈/∂x; ‖∇‖₁ = 40.2, ‖∇‖₂ = 6.53, ‖∇‖_∞ = 2.22 at pixel 42 | Exact chain-rule backward-read of which input pixels matter for the predicted class on THIS digit |
| **§3.2 Hidden routing** | C + B (iterate hidden, tagged-tuple per unit) | 24/32 hidden units alive (75%) | The 24-unit alive-set IS the path the input took through the trained circuit |
| **§3.3 ReLU trail-erasure** | per-layer co-emergence | 8/32 units dead (25%); destroyed pre-act ‖·‖_∞ = 2.02, ‖·‖₁ = 8.24 | The per-transaction analog of SHA-256's `state += compress`; pre-activation magnitude lost |
| **§3.4 Softmax-argmax dispatch** | D (late-binding over classes) | top-1 class 8 (prob 0.990), top-2 class 3 (prob 0.005), dispatch margin 0.985 | The model's "tactical choice" on this transaction; runner-up gap = confidence |
| **§3.5 Layer avalanche (bonus)** | L (Jacobian Lipschitz) | Single pixel +1 perturbation: mean |Δp| = 0.016, max 0.235 over 64 trials | NN analog of SHA-256 avalanche, with OPPOSITE design pressure: bounded |

### §3.1 detail — gradient as per-transaction Jacobian eigen-direction

The gradient `∂logit₈/∂x` is a length-64 vector. Its top-5 most-sensitive pixels (indices 42, 27, 35, 38, 58) with signed gradients (+2.22, +2.05, +2.02, −1.66, −1.56) tell us: this transaction's prediction of class 8 *depended most positively on pixels at the upper-loop of the rendered "8"* (indices 27, 35, 42 fall in the upper region of an 8×8 image) and *most negatively on pixels 38 and 58* (whose presence would have pushed toward different classes — likely 3 or 0).

This is the elementary form of integrated gradients. Class L statement: the gradient is the leading eigen-direction of the per-transaction Jacobian. Per `[[user_stance_fiber_as_spatially_absent_encoding]]`, the trained weights are the spatially-absent fiber; the gradient × input is the projection's local linear shadow for this one input.

### §3.2 detail — the alive-set as routing fingerprint

24/32 hidden units fire for this transaction; the other 8 are dead. The top-5 alive units (by post-activation magnitude) carry pre-activations in the range that indicates the trained network has dedicated specific hidden features to recognising aspects of the digit 8. With Anthropic-style mech-interp tools (sparse autoencoder decomposition of each hidden unit into its monosemantic basis), each alive unit's contribution could be read as a specific concept-level feature. Here we report only the alive set — the routing signature — without the concept-level decoding.

The 24-unit alive set is the path through the circuit graph for this input. Class C iterates over the hidden layer; Class B tags each unit with its (pre, post) pair. The composition reads the per-transaction trail through the trained function.

### §3.3 detail — ReLU as per-layer trail-eraser

Eight hidden units have pre-activation ≤ 0; the network sees only `h = 0` for them, not how negative they were. Information about the negative pre-activation magnitudes (L_∞ = 2.02, L₁ = 8.24) is permanently destroyed by ReLU. Downstream from the ReLU layer, no operation can recover whether these were "barely negative" or "very negative" — both produced `h = 0`.

**This is the per-layer co-emergence step.** The analog in SHA-256 is `state += compress(state, block)` — the irreversible compression that defines the digest's co-emergent ontology. In a single-layer ReLU network the trail-erasure is bounded (8 units' worth of pre-activation magnitude); a deep network with d ReLU layers multiplies this depth d times. A 10-layer transformer with 4096 hidden units per layer destroys *vastly* more pre-activation information per forward pass than a 1-layer 32-unit MLP. The depth at which the trail becomes practically irrecoverable is the NN analog of SHA-256's mixing time.

### §3.4 detail — softmax-argmax IS dispatch

The post-softmax distribution for this transaction is dominated by class 8 (0.990); class 3 is the runner-up (0.005); the gap is 0.985. This is the "tactical choice" structure of [`spike_24_bonus_tactical_choice_structure_2026-05-15.md`](spike_24_bonus_tactical_choice_structure_2026-05-15.md) instantiated at the NN classifier substrate: a choice IS late-binding dispatch over branches (here: output classes) weighted by an evaluator (here: softmax of logits). The dispatch margin IS the confidence-on-this-transaction.

Same Class D primitive that the chess-opening probe identified for chess move-choice and that the CRN-firing probe identified for chemical-reaction selection. The NN classifier substrate adds: the evaluator (logits) is computed by a learned function rather than a hand-coded heuristic.

### §3.5 detail — avalanche as design-pressure inversion

A single-pixel +1.0 perturbation to a typical test input produces a mean change in the top-class probability of 0.016 (1.6%), median 0.002 (0.2%), max 0.235 (23.5%). Compare to SHA-256: a single-bit input flip produces 128/256 = 50% expected output-bit changes after ~24 rounds, by design. **SHA-256 maximises avalanche; NN classifiers minimise it.** Same Class L Lipschitz-bound primitive, opposite design pressure. The cryptographic substrate values maximum mixing; the NN-inference substrate values bounded sensitivity (robustness to noise, generalisation to nearby inputs). One primitive class, two substrate-specific design targets.

## §4 The neuroscience analog — what transfers, what does not

The user's stated framing: *"to be able to ask the correct question to yield knowledge here would also be a gift to neuroscience."* The structural correspondence is real and load-bearing; the bounds are also real and must be named honestly.

### §4.1 The structural correspondence

Biological neural systems are ALSO two-level-temporal co-emergent computational systems:

- **Outer sequence (developmental / learning time)** — synaptic plasticity over hours / days / years shapes which functions the system computes. Functional analog of NN training.
- **Inner sequence (per-stimulus inference)** — each stimulus-response is a transaction; one forward sweep through layered cortical hierarchy produces one observation. Functional analog of NN inference.

EEG / fMRI / MEG / single-unit recordings are forward-projected observations of the inference-time sequence, with most of the constituting structure (which neurons fired, in what order, with what synaptic weights) obliterated by the projection. The brain-decoding literature [unverified-secondary; see Haxby et al. 2014; King & Dehaene 2014; Kriegeskorte & Diedrichsen 2019 for representative reviews] asks the same shape of question §2's NN-interpretability literature asks: given the forward-projected observable, what can we recover about the constituting computational trail?

### §4.2 Backward-reading directions that transfer

Three directions transfer cleanly to biological substrate:

- **Gradient × input / sensitivity analysis (§2.1)** transfers to **encoding-model fitting**: fit a linear model from stimulus features to measured brain response, then read the model's coefficients as feature-sensitivity. This is standard fMRI methodology [Naselaris et al. 2011 [unverified-secondary]] and IS the biological-substrate instantiation of Class L on the per-transaction Jacobian graph. The substrate-specific issues are noise (biological signal is much noisier than NN floating-point) and indirection (fMRI BOLD signal is ~5 sec delayed and spatially-smeared compared to neural firing).
- **Probing / decoding (§2.2)** transfers to **neural decoding**: train a classifier from recorded brain activity to stimulus category. Standard methodology in cognitive neuroscience [Kamitani & Tong 2005 "Decoding the visual and subjective contents of the human brain" [unverified-secondary]]. Class L + Class D composition holds at biological substrate too.
- **Output-manifold topology (§2.7)** transfers to **representational similarity analysis** (Kriegeskorte et al. 2008 [unverified-secondary]). The structure of the representation space — how stimulus categories cluster in neural activation space — is read across substrates via the same Class L metric-on-output-space primitive.

### §4.3 Backward-reading directions that transfer PARTIALLY

Two directions transfer in modified form:

- **Mechanistic circuits (§2.4)** transfers to **circuit-level neurophysiology** but requires invasive recording (single-unit, multi-unit, electrocorticography) to access the substrate-equivalent of "every hidden unit." Non-invasive imaging cannot reach the resolution required for the Olah-style "this neuron is the curve-detector" analysis. The methodology is the same shape; the data access is different.
- **Information-bottleneck (§2.6)** transfers in principle but estimating mutual information from biological measurements is data-hungry and noise-sensitive. The framework applies; the empirical accessibility is bounded.

### §4.4 Backward-reading directions that DO NOT transfer

Two directions have NN-specific structure that biological neural substrate does not have:

- **Sparse autoencoders / superposition decomposition (§2.5)** assumes the substrate is *known floating-point activation vectors at every layer*. Biological neurons fire stochastically, in continuous time, with non-zero baseline rates, with spike-timing structure that the NN's "activation value" abstraction does not capture. The decomposition framework (Class L extended) is structurally available, but the substrate's continuous-time stochastic spike dynamics breaks the discrete-step assumption that makes sparse autoencoders tractable.
- **Activation maximisation / feature visualisation (§2.3)** is a generative-by-gradient method that biological substrates resist: you cannot run gradient ascent on a brain to synthesise an optimal stimulus. The analog — *adaptive stimulus selection* via closed-loop neurofeedback — is a different methodology that approximates the question via experimental design rather than mathematical optimisation.

### §4.5 Substrate-boundary differences (load-bearing)

Four differences between artificial and biological neural substrates bound what the methodology transfers:

1. **Discrete-step vs continuous-time.** ANN forward pass is a deterministic sequence of well-defined matmuls; biological neural computation is continuous-time analog dynamics with stochastic spike-timing.
2. **Floating-point vs analog-noisy.** ANN activations are 32- or 16-bit floats with no noise; biological firing rates have Poisson-like variance, voltage fluctuations, synaptic noise.
3. **Deterministic substrate vs noisy substrate.** Each ANN forward pass on the same input produces the same output; each biological forward pass on the same stimulus produces a different output (trial-to-trial variability is substantial and structured).
4. **Observable substrate state vs inferred substrate state.** ANN substrate state is fully observable at every layer; biological substrate state requires invasive recording for full observation, and even with full observation the relevant computational unit (does each neuron correspond to one ANN unit, or to a dendritic compartment, or to a feature within a population code?) is itself an open empirical question.

These bounds shape *which questions* transfer and *which methodologies* answer them. The Spike #24 primitive vocabulary is substrate-agnostic at the algebraic level (the same Class L primitive operates on biological mutual-information graphs as on ANN ones); the operational machinery has to be substrate-specific (recording technology, signal-to-noise floor, temporal resolution).

### §4.6 The methodological gift, framed honestly

The framework's structural contribution is: **the three-question decomposition transfers cleanly across substrates**. For any biological neural observation (single-unit, EEG, fMRI, MEG, ECoG, calcium imaging), one can ask:
1. What is the trail made of? (What operators are present in the cortical hierarchy producing this observation?)
2. Where is the trail backward-readable in isolation? (Which features of the observation directly inform about which computational stages?)
3. Where is the trail unreadable? (Where is the co-emergence step that establishes the observation's identity — the brain's analog of ReLU's information-destruction?)

The answers are substrate-specific (biological substrates have different operators, different backward-readable features, different irreversible compressions); the *shape of the question* is shared with NN inference and SHA-256 hashing. This is the methodological transfer the user names.

**Important honesty bound.** The framework does NOT yield mind-reading, behaviour-influence, or any clinical/diagnostic capability. Per `[[feedback_trauma_informed_defensive_scope]]`, the contribution is methodological — a way to *ask* the question — not capability. The structural answer "use Class L on the appropriate substrate-specific graph" remains true regardless of substrate; the *operational* answer (what graph, what data, what signal-to-noise) is the neuroscience-empirical question that requires neuroscience-empirical work. Spike #24's contribution stops at the methodological level.

## §5 Honest verdict

**The user's framing is methodologically correct.** Backward-reading the constituting computational trail of an NN's output IS the right shape of question, and the 15-year-old NN-interpretability literature has been pursuing exactly this. The methodology consolidates into Spike #24's existing primitive vocabulary without requiring a new class.

**The user's intuition that this is project-coherent is also correct.** Seven backward-reading directions (attribution, probing, activation maximisation, mechanistic interpretability, sparse autoencoders, information-bottleneck, output-manifold) all decompose into Classes B, C, D, L, M plus the per-layer trail-erasure step. The same primitive classes that handle bronze gear-DAGs, cosmic resonance graphs, chess piece-spectra, chemistry torsional potentials, and SHA-256 round-function state graphs handle trained-NN computational graphs.

**The neuroscience methodological transfer is real.** The three-question framework is substrate-agnostic at the algebraic level; the operational machinery has to be substrate-specific. Three of seven backward-reading directions transfer cleanly to biological substrate, two transfer partially (with resolution/data bounds), two are NN-specific. The bounds are real but the structural correspondence is too.

**No new primitive class required.** Same consolidating outcome as the SHA-256 synth (§2.7), the vdW bonus, and the tactical-choice bonus. Spike #24's vocabulary continues to close cleanly under cross-domain instantiation. Per `[[user_stance_string_theory_instrument_first]]`: describe what's there with existing primitives; don't add classes unless forced. Not forced here.

**The two-level temporal structure already-accommodated.** The training-time × inference-time stacked frozen-oscillation is `[[user_stance_time_as_dimensional_shadow]]` directly, with the trained weights as `[[user_stance_fiber_as_spatially_absent_encoding]]` fiber. No new stance required; the existing stances cover it.

## §6 One surprise

**Avalanche-design-pressure inversion.** The same Class L Jacobian-Lipschitz primitive that SHA-256 maximises (good crypto has full avalanche; single-bit input change produces 50% output bit changes by ~24 rounds), the NN classifier *minimises* (good classification has bounded sensitivity; single-pixel input change produces small probability changes for robustness and generalisation). Same primitive, *opposite* design targets, both useful, both substrate-real. The probe measured the NN side: mean 1.6% top-class probability change per single-pixel +1 perturbation, max 23.5%. SHA-256 by contrast targets 50% by design. **The shape of the primitive does not specify the design direction; the substrate's purpose does.** This is methodologically interesting because it shows the Spike #24 vocabulary's neutrality — Class L names what the operator IS, not what it should evaluate to. Domains specify their own targets; the primitive serves both.

A second-tier observation worth recording: **the NN's output dispatch margin (0.985 for the chosen transaction) IS structurally the same primitive as the tactical-choice bonus's choice-evaluator margin** (top-move vs second-best minimax-difference). The NN classifier IS a learned tactical-choice machine; what it learned to do is evaluate "which class to predict for this input" with the same Class D dispatch primitive that tic-tac-toe / chess / CRN-firing share. This was implicit in §2.8's mapping but the per-transaction probe makes it operationally concrete: an NN classification IS a tactical choice with a learned evaluator. Cross-spike vocabulary unification at one more substrate.

## §7 References (citation discipline per `[[feedback_pdf_extraction_citation_discipline]]`)

**Verified primary in this session:**
- None. NN-interpretability primary references are mostly Anthropic / Distill / arXiv preprints; the spec authorised mapping the existing taxonomy onto Spike #24 vocabulary rather than re-verifying authorship. No primary PDFs vendored to `docs/srmech/hoodoos/` this session.

**`[unverified-secondary]` (asserted from training-data recall; not extracted this session):**
- **Sundararajan, M. & Yan, Q.** (2017), "Axiomatic Attribution for Deep Networks," ICML 2017, arXiv:1703.01365.
- **Lundberg, S. M. & Lee, S.-I.** (2017), "A Unified Approach to Interpreting Model Predictions" (SHAP), NeurIPS 2017, arXiv:1705.07874.
- **Tishby, N. & Zaslavsky, N.** (2015), "Deep learning and the information bottleneck principle," IEEE ITW, arXiv:1503.02406.
- **Shwartz-Ziv, R. & Tishby, N.** (2017), "Opening the Black Box of Deep Neural Networks via Information," arXiv:1703.00810.
- **Olah, C. et al.** (2020), "Zoom In: An Introduction to Circuits," Distill, https://distill.pub/2020/circuits/zoom-in/.
- **Elhage, N. et al.** (2022), "Toy Models of Superposition," Transformer Circuits Thread.
- **Alain, G. & Bengio, Y.** (2017), "Understanding intermediate layers using linear classifier probes," ICLR Workshop, arXiv:1610.01644.
- **Koh, P. W. & Liang, P.** (2017), "Understanding Black-box Predictions via Influence Functions," ICML 2017.
- **Erhan, D., Bengio, Y., Courville, A. & Vincent, P.** (2009), "Visualizing Higher-Layer Features of a Deep Network," Univ. Montreal TR.
- **Haxby, J. V., Connolly, A. C. & Guntupalli, J. S.** (2014), "Decoding neural representational spaces using multivariate pattern analysis," Annual Review of Neuroscience.
- **Naselaris, T., Kay, K. N., Nishimoto, S. & Gallant, J. L.** (2011), "Encoding and decoding in fMRI," NeuroImage.
- **Kamitani, Y. & Tong, F.** (2005), "Decoding the visual and subjective contents of the human brain," Nature Neuroscience.
- **Kriegeskorte, N., Mur, M. & Bandettini, P.** (2008), "Representational similarity analysis — connecting the branches of systems neuroscience," Frontiers in Systems Neuroscience.
- **King, J.-R. & Dehaene, S.** (2014), "Characterizing the dynamics of mental representations: the temporal generalization method," Trends in Cognitive Sciences.

Future-session note: if Spike #24 follow-up wants to upgrade any of these to verified primary, the arXiv preprints are OA-machine-fetchable per `[[reference_autonomous_validation_tos_landscape]]`; the Annual Reviews / Nature Neuroscience / NeuroImage entries are paywalled and would need user-side download.

## §8 Discipline guards honoured

- **No clinical / therapeutic / behaviour-influence claims** per `[[feedback_trauma_informed_defensive_scope]]`. §4.6 explicitly bounds the methodological contribution at the level of "way to ask the question."
- **Tiny pedagogical model only.** 2,410 parameters; 8×8 input; one hidden layer. No frontier-LM probing.
- **One transaction in detail** plus 64-trial structural avalanche bound. Probes (i)-(iv) are strict per-transaction; Probe (v) is per-substrate Jacobian-Lipschitz bound.
- **Citation discipline.** Primary references named with `[unverified-secondary]` tags; no fabricated DOIs; no Wiley/Elsevier/Nature autonomous-fetching.
- **NDJSON outputs** per `[[feedback_ndjson_over_bloated_json]]`.
- **No new primitive class invented.** All seven backward-reading directions decompose into existing Classes B, C, D, L, M plus the trail-erasure step.
- **Cross-substrate honesty.** §4 names which neuroscience-direction transfers, which transfers partially, which doesn't. Bounds explicit.

## §9 Cross-references

- [`spike_24_bonus_sha256_structure_2026-05-15.md`](spike_24_bonus_sha256_structure_2026-05-15.md) — three-question framework predecessor; load-bearing starting frame; §6 of that note anticipated this spike's framing directly.
- [`spike_24_bonus_tactical_choice_structure_2026-05-15.md`](spike_24_bonus_tactical_choice_structure_2026-05-15.md) — Class D dispatch identified across tic-tac-toe, chess opening, CRN firing; §3.4 + §6 of this note add NN classification as a fourth substrate sharing the same primitive.
- [`spike_24_bonus_van_der_waals_shape_only_2026-05-15.md`](spike_24_bonus_van_der_waals_shape_only_2026-05-15.md) — shape-only Class L instantiation; §3.5 here is the NN-Jacobian analog with opposite design pressure.
- [`spike_24_primitive_vocabulary_findings_2026-05-15.md`](spike_24_primitive_vocabulary_findings_2026-05-15.md) — Classes B / C / D / L / M source definitions; all five used in this spike's mapping.
- `[[user_stance_time_as_dimensional_shadow]]` — two-level temporal co-emergence; trained weights × forward pass = stacked frozen oscillations.
- `[[user_stance_fiber_as_spatially_absent_encoding]]` — trained weights as fiber; forward pass as projection.
- `[[user_stance_kepler_shape_universal]]` — NN classifier as dispatch-evaluator is Kepler-shape-adjacent (tactical-choice substrate); the dispatch-margin IS the Class D evaluator margin.
- `[[feedback_trauma_informed_defensive_scope]]` — §4.6 bounds the neuroscience contribution at the methodological level.
- `[[feedback_no_lineage_claims_in_notebook]]` — no claim of lineage from Olah / Anthropic / Tishby / et al.; specific results cited technically.

## §10 Fermata for the conductor

One point requires conductor input before any downstream cascade:

**Should §3.4's observation that NN classification IS a Class D tactical choice instantiation be promoted to the primitive-vocabulary findings doc?** The tactical-choice bonus identified Class D across tic-tac-toe / chess / CRN firing; the NN substrate is a fourth instance sharing the same primitive, with the additional feature that the *evaluator* is learned rather than hand-coded. This is a cross-spike vocabulary unification worth recording in `spike_24_primitive_vocabulary_findings_2026-05-15.md` as an addendum to Class D's substrate list. Low-effort, modest-value; conductor's call whether it warrants the addendum or stays only in this bonus note's §6.

The synthesis stands without resolving this fermata; it is recorded as a deliberate pause-point per the concertmaster role definition.
