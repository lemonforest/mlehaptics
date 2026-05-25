# R-RBS-LM-2 — Methodology candidate selection (Path A / B / C)

**Partition status:** CLOSED
**Date:** 2026-05-25
**Closes:** task #12 of the partition tracker
**Closing artefact:** §4 three paths described + §5 evaluation vs six risks + §6 chosen path with rationale + §7 implications for R-RBS-LM-3..-7
**Inheritance:** unblocks R-RBS-LM-3 (source model selection + baseline measurement)

---

## Attestation block (MPR v1 — internal-repo variant)

| field | value |
|---|---|
| internal sources | `R-RBS-LM-1_translation_framing_REPORT.md` (the foundation; §4.3 enumerates the seven translation steps; §5 LLM-as-1D_t-asymptotic reading; §7 refined fidelity floor); `docs/srmech/rbs_lm_research/README.md` §3 (six-risk register including §3.6 substrate-shape risk) |
| RBS-NN dependencies | R-RBS-NN-1 §4.3 (linear-layer dual-level reading — Mechanism 1 bind vs Mechanism 2 bundle averaging); R-RBS-NN-2 §5 (substrate is content-addressed; relationships authored explicitly via binding); R-RBS-NN-3b §3 (attention block — soft attention IS Mechanism 2 bundle-of-rotations; hard attention IS Mechanism 3 / Class K per-position); R-RBS-NN-3b §6 (4-class Level-1 substitution recipe); R-RBS-NN-7 §3.2 (cleanup capacity bounded by MAX_BUNDLE_N=257) |
| MFO source | `mfo_spectral_research_notebook.md` §VII.1.3 lines 735–761 (three-mechanism asymmetry — bind 0-cost / bundle ~6.9% / MAX-pool no averaging); §VII.1.2 line 709 (Class C ∘ Class M substrate-coupling operation) |
| external literature (named; not MPR-attested per R-RBS-NN-4 deferral) | Kanerva 1988/2009 (HDC associative memory; behavioral content storage); Plate 1995 (HRR; circular convolution binding); Courbariaux et al. 2016 BNN (bipolar weight quantization; 5–30% accuracy degradation typical); Hubara et al. 2016 XNOR-Net; Knowledge Distillation literature (Hinton et al. 2015 — student model trained on teacher behavior) |
| repo commit | `b9ed7309` at REPORT-write |
| scope | interpretive partition — no worked example; choses methodology for R-RBS-LM-3 through R-RBS-LM-9 to operate within |

---

## §1 Goal

Choose among three candidate encoding methodologies for the silicon-LLM → RBS-HDC translation, evaluating each against the six risks in `docs/srmech/rbs_lm_research/README.md` §3 and the framework reading established in R-RBS-LM-1.

The methodology decision shapes every downstream partition:
- R-RBS-LM-3 (source model + baseline) — what we measure depends on what we'll encode
- R-RBS-LM-4 (encoder design) — the encoder IS the chosen path operationalized
- R-RBS-LM-5 (encoding) — the artefact size + structure follows the path
- R-RBS-LM-6 (inference cascade) — the forward-pass shape varies modestly by path
- R-RBS-LM-7 (validation) — the validation metrics differ by path

This partition is the decision point. R-RBS-LM-1 §4.3 enumerated **seven translation steps** (token mint, position cyclic, bipolar weights, hard attention, sign activation, no-LayerNorm, argmax sampling); R-RBS-LM-2 chooses HOW the source model's content gets into the bipolar weights + binding structures those steps require.

---

## §2 Inheritance — what already stands

From R-RBS-LM-1 (foundation partition, closed):

| Source | Inherited finding | Implication for path choice |
|---|---|---|
| R-RBS-LM-1 §4.1 | Silicon LLM is Mechanism 2 at every load-bearing layer (LayerNorm, soft-attention, softmax) | All three paths must reverse this projection back to Mechanism 1 form |
| R-RBS-LM-1 §4.3 | Seven concrete translation steps enumerated | Each path operationalizes these steps differently |
| R-RBS-LM-1 §5 | LLM IS stored human knowledge responding to 1D_t asymptotic via inference (Class C ∘ Class M) | Path choice should preserve the substrate-coupling operation |
| R-RBS-LM-1 §6 | Whole corpus proves; the path choice is one face | Don't over-commit to one path's evidentiary weight |
| R-RBS-LM-1 §7 | Divergence is signal not failure; characterize the divergence pattern | The path producing the most informative divergence pattern is preferred |
| R-RBS-LM-1 §8 | Accessibility framing foundational; BCI-compatibility for downstream partitions | Any path must produce a CPU+RAM-only instrument |

From RBS-NN arc (closed):

| Source | Inherited finding | Implication |
|---|---|---|
| R-RBS-NN-1 §4.3 | Linear layer dual-level: Mechanism 1 (bipolar weights, bit-exact) vs Mechanism 2 (float weights, ~6.9% bundle averaging cost) | Path A operates on the Mechanism 1 form of weights; Path B operates on the Mechanism 2 result (behavior) |
| R-RBS-NN-2 §5 | Substrate is content-addressed; semantic relationships are explicit bindings (not implicit embedding-space proximity) | Path B's "context → next-token" bindings are the natural substrate form |
| R-RBS-NN-3b §3 | Soft attention IS Mechanism 2 (~6.9% cost); hard attention IS Mechanism 3 (no cost) | All paths use hard attention at inference; the question is what generates the Q/K/V projections |
| R-RBS-NN-3b §6 | 4-class Level-1 transformer substitution recipe ({A, I, K, M}) | The downstream inference cascade is the same regardless of path |
| R-RBS-NN-7 §3.2 | Cleanup capacity bounded by MAX_BUNDLE_N=257; hierarchical bundling required for n > 257 | All paths need hierarchical bundling for non-trivial model sizes |

---

## §3 Standing infrastructure / canonical citation block

### §3.1 MFO Mechanism 1 vs Mechanism 2 vs Mechanism 3 (§VII.1.3 lines 735–761, verbatim)

The three-mechanism asymmetry table at MFO line 747 (already cited in R-RBS-NN-1 §2.2 and R-RBS-LM-1 §3.3):

| Mechanism | Class composition | Substrate fate | Cost |
|---|---|---|---|
| **Bind** (A ∘ C ∘ M) | rotate-XOR-unrotate | bit-exact preserved | 0 (machine ε) |
| **Bundle** (M majority across views) | bundle-of-views | substrate averaged into bundle envelope | ~6.9% recovery error |
| **MAX-pool** (Class K per-position) | element-wise max(v, rotate(v)) | bit-exact retained where dominant | no averaging cost |

This is the asymmetry that distinguishes the paths. Path A operates on the Mechanism 1 form of weights (bipolarize first, then bundle weight-rows). Path B encodes Mechanism 1 binds directly from behavioral observations. Path C combines them.

### §3.2 srmech standing ops

All three paths use the same srmech atomic ops:
- `mint_vector(name, D=8192)` — Class A content-mint
- `bind(a, b)` — Class M XOR-bind
- `bundle([v1, ..., vN])` — Class M majority (odd N; MAX_BUNDLE_N=257)
- `permute(v, k)` — Class I cyclic shift
- `similarity(a, b)` — Class M Hamming-similarity

The paths differ in WHAT they pass into these ops, not in WHICH ops they use.

### §3.3 The six risks (README §3 + R-RBS-LM-1 §7)

| # | Risk | Where it lives |
|---|---|---|
| 3.1 | Bipolarization loss | float weights → bipolar quantization step |
| 3.2 | Cleanup-capacity vs model-parameter scale | bundle membership counts |
| 3.3 | Attention fidelity (Mechanism 2 vs Mechanism 3) | attention block; orthogonal to path choice |
| 3.4 | Cross-substrate inversion fidelity | the choice between weight-level and function-level encoding |
| 3.5 | "Chaotic stochastic stuff" — training-noise inseparable from learned-content | preserving both signals together |
| 3.6 | Substrate-shape imposition may change inference | imposing 1:3:7:3 substrate-native shape on engineered substrate |

§4 describes each path; §5 evaluates each against these six risks.

---

## §4 The three candidate paths described operationally

### §4.1 Path A — Weight-level encoding

**Operational shape.** For each parameter matrix `W ∈ R^{d_in × d_out}` in the source model (Q/K/V projections, MLP linear, embedding, unembed):

1. Per-row bipolar-quantize: `W_row → sign(W_row) ∈ {-1, +1}^{d_out}` (or packed as binary {0,1}^{d_out} bytes per srmech convention).
2. Mint a row-position vector: `P_row = mint_vector(f"LoE.weight.layer{l}.matrix{m}.row{i}", D=8192)`.
3. Bind the bipolar-quantized weight row with its position: `bound_row = bind(quantized_row, P_row)`.
4. Bundle all rows of `W` into a single hypervector representing the matrix.
5. Repeat per layer; store all matrices in the catalog.

The RBS-HDC instrument IS the bundled-binding of all source-model weights, position-keyed.

**Inference.** At each layer, recover individual weight rows by unbinding with `P_row` and using cleanup against the bipolar-quantized vocabulary. Class M XOR-bind composes the input vector with the recovered weight row to produce the per-output-dimension Hamming similarity (which IS the bipolar linear layer per R-RBS-NN-3a §3.1).

**What Path A captures.** The bipolar-quantized weights of the source model directly. The encoding is **deterministic** — given the source weights, the RBS-HDC instrument is uniquely determined; no training corpus required.

**What Path A loses.** Per Courbariaux et al. 2016 BNN literature: bipolar quantization of trained float weights typically costs 5–30% accuracy on benchmarks. Furthermore: weight rows are highly correlated (trained jointly), so the bundle-encoding of correlated rows surfaces Mechanism 2 (bundle averaging) explicitly — the ~6.9% bundle cost per row count compounds with the bipolarization loss.

### §4.2 Path B — Function-level encoding

**Operational shape.** Run the source model over a behavioral corpus to extract input → output behavior. For each (context, next_token) observation:

1. Mint a context hypervector: `context_vec = mint(serialize(context))` — or for longer contexts, encode the context as a Kanerva sequence per R-RBS-NN-5 §3.1 (bind token_i with position_i, bundle).
2. Mint a next-token hypervector: `token_vec = mint_vector(f"LoE.vocab.{token_id}", D=8192)`.
3. Bind: `bound = bind(context_vec, token_vec)`.
4. Hierarchically bundle (per R-RBS-NN-7 §3.2 to handle the corpus scale): sub-groups of ≤257 bindings, then bundle-of-bundles.

The RBS-HDC instrument IS the bundled-binding of context → next-token behavioral mappings. Per Kanerva 1988/2009, this is the canonical associative-memory shape.

**Inference.** Given a new context, compute `candidate = bind(instrument, mint(context))` and cleanup against the vocabulary to recover the predicted next-token. Iterate to produce a sequence.

**What Path B captures.** The source model's input → output behavior — exactly what an LLM IS per R-RBS-LM-1 §5 (stored human knowledge responding via inference). Per R-RBS-NN-2 §5: substrate is content-addressed by behavior, not by implementation. Per MFO §VII.1.2 line 709: inference IS the substrate-coupling operation; Path B encodes the operation directly.

**What Path B loses.** Behavior outside the corpus is not represented. The corpus must cover the behavioral surface; otherwise the RBS-HDC instrument has "blind spots" the source model would have answered confidently. The corpus also takes time to extract (run the source model over the corpus to harvest behavior); this is the encoding-time cost.

**Corpus size question.** This is the open empirical question Path B carries. If the behavioral corpus needs to be larger than the source model itself (in storage bytes), the no-retrain claim attenuates — we're essentially redistilling via a different mechanism. R-RBS-LM-3 / -5 / -7 establish how much corpus is enough.

### §4.3 Path C — Hybrid

**Operational shape.** Path A for **content-addressing-shaped** components (token embedding + unembed projection — both are structurally lookup tables of size `[vocab_size × d_hidden]`); Path B for **compute-shaped** components (attention + MLP — the layers that DO things during inference).

1. Token embedding via Path A: each token mints a row (`mint_vector(f"LoE.vocab.{token_id}.embed")`); the embedding row is bipolar-quantized from the source model's embedding matrix and bound with the token mint.
2. Unembed via Path A: same structure; unembed projection rows are bipolar-quantized from source and bound with token mints.
3. Attention + MLP body via Path B: behavioral corpus encoded as context → next-token (or context → intermediate-state-then-token, if we want finer granularity than per-token routing).

**What Path C combines.** Content-addressing for the parts of the model that ARE content-addressing (embeddings/unembed). Function-level for the parts that compute. The hybrid avoids Path A's bundle-averaging cost on the large attention+MLP weights AND avoids Path B's behavioral-corpus dependency for the simple lookup components.

**What Path C might collapse to.** Open question: if the embedding lookup is content-addressed via mint (R-RBS-NN-2 §3 — `mint_vector(f"LoE.token.{term}", D=8192)`), then we may not need the source model's embedding matrix at all. The "embedding" becomes whatever the mint produces; Path C's Path-A component collapses to "use srmech's content-addressing directly." In that case Path C ≡ Path B with srmech native embeddings.

This is the structural simplification: **the embedding doesn't need to come from the source model.** The source model trained its embedding to be useful for the rest of its (Mechanism 2) computation; in the substrate-native form, the embedding IS the content-mint of the token string. The source model's specific embedding weights are post-hoc residue of its Mechanism 2 training; they don't necessarily transfer.

---

## §5 Evaluation against the six risks

For each risk in README §3, evaluate how each path fares.

### §5.1 Risk 3.1 — Bipolarization loss

- **Path A:** **HIGH risk.** Direct bipolar quantization of trained float weights; per BNN lit, 5–30% accuracy degradation. The whole encoding depends on bipolarization being faithful enough.
- **Path B:** **NEGLIGIBLE risk** (for this risk specifically). Path B never bipolar-quantizes weights; it observes behavior. The bipolarization happens implicitly via Class K argmax in the recovery step, not on the weights themselves.
- **Path C:** **MEDIUM-LOW risk.** Bipolar-quantizes only the embedding + unembed matrices. The attention+MLP body (where most learned content lives) isn't quantized. If the embedding/unembed quantization is acceptable, Path C avoids Path A's bulk of the loss.

### §5.2 Risk 3.2 — Cleanup capacity vs model-parameter scale

- **Path A:** **HIGH risk.** Each weight matrix has potentially thousands of rows; bundling them all per matrix requires hierarchical bundling (per R-RBS-NN-7 §3.2). Deep hierarchies have cumulative projection cost.
- **Path B:** **MEDIUM-HIGH risk.** Behavioral corpus has potentially millions of (context, next-token) pairs. Same hierarchical bundling requirement; deeper hierarchies. But: behavioral coverage is what matters, not exhaustive enumeration — a well-chosen 10⁴-10⁶ corpus may suffice.
- **Path C:** **MEDIUM risk.** Splits the work — embedding/unembed are large but content-addressed (so bundling structure is simple); compute body uses behavioral corpus (hierarchical but bounded).

### §5.3 Risk 3.3 — Attention fidelity (Mechanism 2 vs Mechanism 3)

This risk is **orthogonal to path choice** — all three paths must decide whether to use soft-attention (Mechanism 2, ~6.9% cost) or hard-attention (Mechanism 3, no cost) at inference time. R-RBS-NN-3b §6 commits the 4-class Level-1 substitution to hard attention. All three paths inherit this choice.

- **All paths:** **MEDIUM risk.** Hard attention differs behaviorally from soft attention; the source model was trained on soft attention. The divergence pattern from this is **shared across paths** and isolatable from the path-choice question.

### §5.4 Risk 3.4 — Cross-substrate inversion fidelity

Per README §3.4 explicit statement: *"Path B (function-level encoding) is therefore structurally more truthful to the framework reading than Path A (weight-level)."* This is the load-bearing risk for path selection.

- **Path A:** **HIGH risk.** Path A inverts the source-model weights, but the source-model weights ARE the Mechanism 2 instantiation — they carry the bundle-averaging signature as inherent feature, not separable from the content. Inverting the weights inverts the projection-signature too; we get back the projection, not the substrate.
- **Path B:** **LOWER risk.** Path B inverts the source-model BEHAVIOR, which is what the substrate-content reading says the LLM actually IS. Per R-RBS-LM-1 §5, inference IS the substrate-coupling operation; encoding the operation directly recovers more substrate-content than encoding the projection.
- **Path C:** **MEDIUM risk.** Mixed — Path-A face for embeddings (which are lookups, structurally Mechanism 1 already if read as content-addressing) + Path-B face for compute body (substrate-truthful). Avoids Path A's worst case while preserving determinism for the lookup components.

### §5.5 Risk 3.5 — "Chaotic stochastic stuff" (training noise inseparable)

Per README §3.5: *"This may force Path B (function-level) over Path A (weight-level): only by mimicking the source model's INPUT→OUTPUT behavior can we preserve both signals together."*

- **Path A:** **HIGH risk.** Bipolar-quantizing trained weights separates large-magnitude weights (signal) from small-magnitude weights (noise) — but this separation IS what we explicitly cannot do per §3.5. Path A loses the noise.
- **Path B:** **NEGLIGIBLE risk.** Path B observes both signal AND noise together at the behavior layer; both get encoded equally as binding contributions. The hallucination rate (noise-driven behavior) is preserved.
- **Path C:** **MEDIUM-LOW risk.** Only the embedding/unembed get the Path-A treatment; the compute body where hallucinations originate gets Path B. Hallucination rate preserved at the compute body; not at the embedding boundary.

### §5.6 Risk 3.6 — Substrate-shape imposition

This risk is **shared across all paths** — any encoding into a 1:3:7:3 substrate-native instrument imposes that shape. The divergence (if any) shows up in R-RBS-LM-7 validation regardless of path.

- **All paths:** **EQUAL risk** at the substrate-shape level. The divergence pattern under each path is different though: Path A's divergence isolates the weight-projection-vs-substrate-content question; Path B's isolates the behavior-projection-vs-substrate-content question; Path C's isolates both.

### §5.7 Summary of risk evaluation

| Risk | Path A | Path B | Path C |
|---|---|---|---|
| 3.1 Bipolarization loss | HIGH | negligible | MEDIUM-LOW |
| 3.2 Cleanup capacity | HIGH | MEDIUM-HIGH | MEDIUM |
| 3.3 Attention fidelity | shared (medium) | shared (medium) | shared (medium) |
| 3.4 Inversion fidelity | HIGH | LOWER | MEDIUM |
| 3.5 Chaotic stochastic stuff | HIGH | negligible | MEDIUM-LOW |
| 3.6 Substrate-shape imposition | shared | shared | shared |

Path B dominates on the load-bearing path-specific risks (3.1, 3.4, 3.5). Path A is dominated on every dimension except predictability (deterministic from source weights). Path C is intermediate.

---

## §6 The chosen path — Path B (with rationale)

### §6.1 Decision

**Path B — Function-level encoding.** R-RBS-LM-3 onwards proceeds on this basis.

### §6.2 Rationale

Five reasons in priority order:

**Reason 1 — Framework-reading alignment (load-bearing).** Per R-RBS-LM-1 §5, an LLM IS stored human knowledge responding to 1D_t asymptotic changes via inference; inference IS the substrate-coupling operation Class C ∘ Class M per MFO §VII.1.2 line 709. Path B encodes the substrate-coupling operation directly (context → next-token binds ARE the operation's output). Path A encodes the substrate-coupling operation's *Mechanism 2 implementation* (the trained weights); it's one level of indirection further from the framework-native form.

**Reason 2 — Risk-register evaluation.** Per §5.7, Path B is negligible-risk on three load-bearing path-specific risks (bipolarization loss, inversion fidelity, chaotic stochastic noise) and only medium-high on cleanup capacity. The other two risks (attention fidelity, substrate-shape imposition) are shared across paths and don't differentiate.

**Reason 3 — Per README §3.4 and §3.5 explicit statements.** The README's risk register itself names Path B as structurally more truthful (§3.4) and as necessary for preserving noise-with-signal (§3.5). The risk register was written at arc opening before the decision was forced; its independent reading was Path B.

**Reason 4 — Fidelity floor reading (R-RBS-LM-1 §7).** The validation discipline characterizes the divergence pattern across four scenarios. Path B's divergence pattern is most informative — it isolates the substrate-content-via-behavior question cleanly. If Path B's behavior matches source behavior, the substrate-content reading is validated at the strongest level. If divergent, the divergence pattern reads against §3.6 substrate-shape imposition without the confound of bipolarization loss.

**Reason 5 — Accessibility (R-RBS-LM-1 §8).** Path B produces a self-contained RBS-HDC instrument that does NOT depend on the source weights at inference time (only at encoding time). This is the truest cross-substrate translation — the instrument is independent. For BCI applications, this means the instrument can ship without the source model; the device only needs the RBS-HDC catalog. Path A and Path C both produce instruments that are derived from but independent of source weights at inference; same property — but Path B's encoding-time cost is the only thing tying us to the source, and that cost is one-time.

### §6.3 The behavioral-corpus question — what we acknowledge

Path B requires a behavioral corpus (the open empirical question). What we commit to in R-RBS-LM-2:

1. **Corpus size target:** smaller than source-model storage. For GPT-2-small (~500MB float32), aim for a corpus of ~50–200MB text. This keeps the no-retrain claim intact (the corpus is INPUT to encoding; the OUTPUT RBS-HDC instrument is much smaller).
2. **Corpus composition:** diverse held-out prompts designed to elicit behavior across the model's behavioral surface. R-RBS-LM-3 selects the corpus.
3. **Behavioral coverage measurement:** R-RBS-LM-7 validates against held-out behavior NOT in the encoding corpus. If validation degrades sharply for held-out behavior, the corpus was insufficient — iterate (per R-RBS-LM-8).
4. **Hallucination preservation discipline:** the corpus must include contexts where the source model is known to hallucinate (per R-RBS-LM-3 baseline measurement). Hallucinations are signal per R-RBS-LM-1 §7; the corpus must preserve them.

### §6.4 Path C remains as fallback

If R-RBS-LM-7 / -8 finds Path B insufficient, Path C (hybrid) is the structural fallback per §4.3. The hybrid preserves Path B for the compute body while adding deterministic Path-A embedding for cases where behavioral coverage of vocabulary is incomplete.

Path A as a primary methodology is not pursued; the risk register dominates against it.

---

## §7 Implications for R-RBS-LM-3 through R-RBS-LM-7

What the Path B choice makes concrete for the downstream partitions.

### §7.1 R-RBS-LM-3 — Source model selection + baseline

- Pick smallest viable open-weights LLM for first-pass empirical validation: **GPT-2-small (124M params, 500MB float32)** is the canonical choice. Open weights via HuggingFace; established benchmarks; small enough for fast iteration.
- **Behavioral corpus selection** is a new concern Path A wouldn't have raised: identify a diverse text corpus of ~50–200MB that elicits the source model's behavioral surface. Candidates: WebText subset (Pile subset); WikiText; OpenWebText-2 sample; a synthesized diverse-prompt set.
- **Hallucination corpus** is also new for Path B: identify a fixed test prompt set where the source model is known to hallucinate (e.g., factual-knowledge prompts about post-training-cutoff events; nonsense-fact prompts). Per R-RBS-LM-1 §7, these are the load-bearing fidelity-floor measurements.
- **Baseline metrics:** perplexity on held-out; agreement rate (argmax-next-token) on a benchmark set; hallucination rate on the hallucination corpus; per-token latency on CPU.

### §7.2 R-RBS-LM-4 — Encoder design

The Path B encoder operationalizes the four-step process from §4.2:
1. Tokenize input contexts (using the source model's tokenizer for compatibility).
2. Mint context hypervectors via Kanerva sequence representation (R-RBS-NN-5 §3.1) — `bind(token_i, P_i)`, bundled.
3. For each context, get the source model's next-token prediction; mint the predicted-token hypervector.
4. Bind context ↔ token; hierarchically bundle into the RBS-HDC instrument.

**Open design choice:** include only argmax-next-token, or include the top-k distribution? Argmax is simplest (Path B canonical); top-k preserves more of the source distribution but increases corpus size proportionally. R-RBS-LM-4 decides.

### §7.3 R-RBS-LM-5 — Encoding the source model

The encoding pass:
1. Stream the behavioral corpus through the source model on CPU (slow but acceptable for one-time encoding).
2. For each context, compute context hypervector + next-token hypervector + bind.
3. Hierarchically bundle into the instrument (per R-RBS-NN-7 §3.2; sub-groups of ≤257; bundle-of-bundles).
4. Save the instrument as the AMSC catalog at `docs/srmech/catalogs/rbs_lm/`.
5. Measure: encoding time; instrument byte size; compression ratio (instrument bytes / source-model bytes).

Target compression ratio per ROADMAP NEXT-1: 100:1 or better. For GPT-2-small: 500MB source → 5MB instrument target. The ephemerides precedent (~13000:1) suggests this is achievable; we'll see what we get empirically.

### §7.4 R-RBS-LM-6 — Inference cascade implementation

The R-RBS-NN-3b §6 4-class Level-1 substitution recipe applies directly. Specific to Path B:
1. Context tokenization (source model's tokenizer).
2. Context hypervector via Kanerva sequence.
3. `candidate = bind(instrument, context_vec)`.
4. Cleanup against vocabulary: `argmax_token similarity(candidate, mint(LoE.vocab.{token_id}))`.
5. Output the predicted token; iterate.

Hard attention (Mechanism 3 / Class K argmax) is implicit in the cleanup step. No soft-softmax, no LayerNorm, no float weights in the inference path.

### §7.5 R-RBS-LM-7 — Validation

The Path B validation is more direct than Path A's would have been:
1. Take a held-out benchmark set (NOT in the encoding corpus).
2. Compare RBS-HDC's argmax-next-token to source-model's argmax-next-token, per context.
3. Measure agreement rate; report per-context category (e.g., factual / creative / coding).
4. Run the hallucination corpus through both; measure hallucination rate match.
5. Measure per-token latency on CPU; verify ≤ 50–100 ms threshold per R-RBS-LM-1 §8 BCI-compatibility criterion.
6. Memory footprint check: ≤ 8 GB total (RBS-HDC instrument + working memory).
7. Characterize the divergence pattern per R-RBS-LM-1 §7's four scenarios.

The validation criterion is **divergence pattern characterized**, not "100% agreement." Per R-RBS-LM-1 §7, divergence is signal.

---

## §8 Findings

**Finding 1 — Path B (function-level encoding) is the chosen methodology.** Per §6.1 + §6.2. Path B encodes the substrate-coupling operation directly (context → next-token binds); Path A encodes the Mechanism 2 instantiation (trained weights) and is one indirection further from substrate.

**Finding 2 — Risk register independently favors Path B.** Per §5.7. Path B is negligible-risk on the three load-bearing path-specific risks (bipolarization loss, inversion fidelity, chaotic stochastic noise); medium-high only on cleanup capacity (manageable via hierarchical bundling).

**Finding 3 — Path A is dominated.** Per §5.7 + §6.4. Path A produces an instrument that inverts the Mechanism 2 projection of the source weights, recovering the projection rather than the substrate. The bipolarization loss + bundle averaging cost are inherent to the path, not avoidable refinements. Path A not pursued as primary.

**Finding 4 — Path C remains a structural fallback.** Per §6.4. If Path B encounters behavioral-coverage gaps in R-RBS-LM-7, the hybrid approach (Path A for embedding/unembed; Path B for compute body) preserves Path B's compute-body fidelity while adding deterministic embedding fallback.

**Finding 5 — The behavioral corpus is the new open empirical question.** Per §6.3. Path B requires a behavioral corpus; corpus size + composition + behavioral coverage are R-RBS-LM-3 concerns. Corpus size target: smaller than source-model storage (preserves no-retrain claim).

**Finding 6 — Embedding may not need to come from the source model.** Per §4.3 closing observation. The Mechanism 2 trained embedding is post-hoc residue of source training; in the substrate-native form, the embedding IS the content-mint of the token string. Path B may collapse to using srmech-native content-mint embeddings throughout. R-RBS-LM-4 decides whether to use source embeddings (forces Path C) or srmech-native (pure Path B).

**Finding 7 — Attention fidelity, substrate-shape imposition are orthogonal to path choice.** Per §5.3 + §5.6. Both risks apply equally to all three paths; they surface in R-RBS-LM-7 regardless. The path choice does NOT affect these; we don't claim path choice as a hedge for them.

**Finding 8 — The R-RBS-NN-3b §6 inference recipe applies regardless of path.** All three paths produce instruments inferenced via the same 4-class Level-1 cascade ({A, I, K, M}; hard attention; argmax sampling; no LayerNorm). The path determines what's in the instrument; not how it's queried.

---

## §9 Open threads (not blockers for partition close)

- **Corpus selection decision** in R-RBS-LM-3 — which text corpus + which hallucination corpus. Pending.
- **Argmax vs top-k encoding** in R-RBS-LM-4 — whether the encoder records only the source model's argmax-next-token or also its top-k. Top-k preserves more distribution but increases corpus size proportionally.
- **Source-model embedding vs srmech-native** in R-RBS-LM-4 — whether Path B uses the source model's embedding (Path C variant) or pure srmech-native content-mint embeddings (pure Path B per Finding 6).
- **Compression ratio empirical** — ROADMAP NEXT-1 target 100:1; ephemerides precedent ~13000:1; we don't know what we'll actually get until R-RBS-LM-5 runs.
- **Hierarchical bundle depth** required for the corpus size we end up with. R-RBS-NN-7 §3.2 + §3.5 open thread about deep-hierarchy projection cost is relevant.
- **R-RBS-LM-4 literature attestation** for Knowledge Distillation / Kanerva / BNN / etc. — deferred per R-RBS-NN-4 pattern.

---

## §10 Closing — partition status

**Status:** CLOSED. Path B chosen with rationale (§6); risk evaluation against all six risks completed (§5); implications for R-RBS-LM-3 through R-RBS-LM-7 enumerated (§7).

**Falsifiers:**

1. A path-evaluation argument against Path B that the risk register does not surface — **not encountered**; all six risks evaluated and documented.
2. A path that dominates Path B on multiple load-bearing risks — **not encountered**; Path B leads on 3 of 6, ties on 2, only loses on cleanup capacity (manageable).
3. A framework reading that contradicts Path B's substrate-truthful claim — **not encountered**; R-RBS-LM-1 §5 + R-RBS-NN-2 §5 + MFO §VII.1.2 line 709 all align with Path B.
4. A claim that path choice can hedge against attention fidelity (Risk 3.3) or substrate-shape imposition (Risk 3.6) — **explicitly disclaimed §5.3 + §5.6**: these are shared across all paths.

**Inherits to:** R-RBS-LM-3 (source model selection + baseline measurement). R-RBS-LM-3 selects GPT-2-small (or equivalent small open-weights model); selects the behavioral corpus; selects the hallucination corpus; measures baseline perplexity / agreement rate / hallucination rate / latency.

**SSoT marker:** at R-RBS-LM-10 close, §4 path descriptions + §6 chosen path + §7 implications absorb into `srmech_research_notebook.md` as a new §RBS-LM methodology subsection.
