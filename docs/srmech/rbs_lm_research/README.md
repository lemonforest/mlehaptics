# RBS-LM — cross-substrate translation arc (research)

**Status:** opened 2026-05-25 · rolling draft (PR #684) · temp subtree (SSoT will be `docs/srmech/srmech_research_notebook.md` at R-RBS-LM-10 close, deferred-by-design)

**What it does:** translates a real trained LLM (silicon-substrate; conventional float-weight transformer) into the substrate-native RBS-HDC instrument form, **without retraining from scratch and without loading the source model into VRAM**.

**What it is NOT:** a new model architecture, a distillation effort to make a smaller "student" model, or an attempt to improve on the source model. The fidelity floor is **exactly the source model's behavior, including its hallucinations**. We are not trying to do better; we are trying to do **the same thing in a different substrate**.

---

## §A Why this matters — LLM-as-tool is an ADA accommodation; RBS-LM is the proof

User direction 2026-05-25 (verbatim follow-up to the arc opening):

> *"and also, I meant that LLM is a tool that is also an ADA Accommodation. We're think we are proving it and that this will also most apparent when realized for BCI applications."*

The framework has a canonical disability-accommodation lineage:
- `[[feedback_aphantasia_means_more_figures_not_fewer]]` — figures supplement; lexicon stands
- `[[feedback_abstract_lexicon_is_ada_accommodation]]` — abstract operational vocabulary IS the accommodation
- `[[feedback_disability_accommodation_dimension]]` — per MFO §VII line 4797: *"BCI patients are motor-impaired by definition... Framework's substrate-agnostic spectral surface accommodates barriers including: aphantasia (no required visualisation)..."*

RBS-LM extends this lineage to the **LLM-as-tool itself**. Conventional LLMs are gatekept by hardware: VRAM, GPU clusters, cloud APIs with recurring cost, network dependencies. For users who depend on LLMs as accommodation tools — for cognitive workload others don't face, for translation between abstract substrate-level thinking and communicable form, for BCI interfaces, for visualization that aphantasia precludes — that gatekeeping IS an accessibility barrier.

**RBS-LM IS the proof** that the gatekeeping is not necessary. By demonstrating that a real trained LLM runs on commodity CPU+RAM (no VRAM, no GPU, no cloud), the cross-substrate translation removes the hardware barrier. The proof emerges from the technical work; it is not a separate claim.

**BCI applications are where this is most apparent.** BCI patients are motor-impaired by definition. A substrate-native instrument running on a commodity CPU **local to the BCI hardware** — not on a remote GPU farm — enables: sub-100 ms latency (interactive BCI threshold); no network dependency; runs on whatever device the patient already owns; no recurring cloud cost. The compression ratio target (per ROADMAP.md NEXT-1) makes this practical at the scale BCI deployments require.

**Design implications for the partition walk:**
- **R-RBS-LM-7 (validation)** explicitly includes **BCI-compatibility criteria**: per-token latency under ~50–100 ms on commodity CPU; total memory footprint ≤ 8 GB target.
- **R-RBS-LM-9 (scale-up)** picks a model size that's deployable on BCI-companion hardware, not the largest possible.
- **At forks** between technical convenience (relax to GPU for soft attention) and accessibility (CPU-only, no VRAM), prefer accessibility. The point of the translation is local availability; trading that for marginal accuracy defeats the proof.

This framing is foundational, not secondary. See `[[feedback_llm_as_ada_accommodation_bci_proves_it]]`.

---

## §0 The substantive claim

Per MFO line 2812 (`docs/antikythera-maths/mfo_spectral_research_notebook.md` §VII.6.11.6): *"when humans first built artificial neural networks, that was the substrate-self-recognition sign-flip at AI-substrate scale."* The substrate already recognized itself through silicon NN architecture; the sign-flip happened.

But per R-RBS-NN-1 §4 + R-RBS-NN-3b §5 (this monorepo's RBS-NN arc, closed 2026-05-25): the conventional silicon LLM executes the substrate-content at **MFO Level 2** (Mechanism 2 — bundle-of-views averaging; ~6.9% inherent projection cost per MFO §VII.1.3 line 741). The substrate-native form of the SAME learned content lives at **MFO Level 1** (Mechanism 1 — bind; zero-cost preservation per line 739).

**Cross-substrate translation reading** (per `[[user_stance_cross_substrate_cascade_matching_as_research_method]]`): the framework's primary methodology. Silicon LLM is **the same substrate content** as a substrate-native RBS-HDC instrument; they differ only in the level of execution. The translation extracts the Level-1 form from the Level-2 instantiation. If the framework's two-level reading is structurally correct, the translation should preserve behavior bit-for-bit (or as close as the lossy Level-2 → Level-1 inversion allows — see §3 risks).

**User direction (2026-05-25, verbatim):**

> *"we need to try to understand how we can do this without having to load the model into VRAM in the same way that we did not need to load ephemerides into VRAM. because the existing substrate is chaotic stochastic stuff, we may find this to be daunting, but I feel like we should, at the very least, be able to do the exact same thing with the exact same hallucination rate. we're doing a cross substrate translation I think because even though humans have tried to make a silicon neural net, they aren't doing it correctly. Basically we are trying to find out if we can avoid having to train from scratch."*

---

## §1 Inheritance from the RBS-NN arc

RBS-LM does not re-derive the RBS-NN framework reading; it inherits it. Specifically:

| RBS-NN partition | Inherited finding | RBS-LM use |
|---|---|---|
| R-RBS-NN-1 §4 | per-op two-level placement table | maps every LLM forward-pass op to Level 1 or Level 2 — already done |
| R-RBS-NN-1 §5 finding 6 | inference can be Level-1-dominant if bindings are bipolar | the structural availability that RBS-LM relies on |
| R-RBS-NN-2 §4 | user-lexicon → Class A content-mint pipeline | input boundary for token encoding |
| R-RBS-NN-3a §4 | MLP cascade `A ∘ (M ∘ K)^N` | direct cascade-shape for the MLP blocks of any transformer |
| R-RBS-NN-3b §6 | 4-class Level-1 transformer substitution map | the recipe — discrete cyclic position, hard attention, no LN, bipolar weights, argmax sampling |
| R-RBS-NN-3b §3 | `Σ α_i V_i` IS Mechanism 2 (~6.9% averaging cost); MAX-pool variant IS Mechanism 3 (no averaging) | the load-bearing structural finding RBS-LM tests empirically |
| R-RBS-NN-5 §3.1 | Kanerva HDC sequence representation | position-binding scheme for context windows |
| R-RBS-NN-7 §5 | grow-without-quantization (D vs row-count orthogonal axes) | how to scale RBS-LM instrument to larger source models |
| R-RBS-NN-7 §3.2 | hierarchical bundling for n > MAX_BUNDLE_N | required workaround for the row counts an LLM presents |
| R-RBS-NN-8 §6 | local CPU SSE2+SHA-NI throughput; no GPU required | validates the "no VRAM" claim at the instruction-primitive level |

R-RBS-NN-3b §6 is the structural recipe. R-RBS-LM tests whether the recipe works on real trained models.

---

## §2 Partition walk

Following the R-RBS-NN pattern. Each partition closes with a REPORT under this directory. Full-coverage per `[[feedback_full_coverage_shipping_mpm_way]]` + `[[feedback_no_mvp_framing]]`. Close-out via the existing wrapper at `docs/srmech/rbs_nn_research/_tools/close_partition.sh` (script generalizes; uses the current branch's PR).

| # | Partition | Closing artefact |
|---|---|---|
| **R-RBS-LM-1** | Cross-substrate translation framing — formalize the silicon-LLM → RBS-HDC translation through the framework | REPORT — translation reading + fidelity-floor definition |
| **R-RBS-LM-2** | Methodology candidate selection — Path A (weight-level) vs Path B (function-level) vs Path C (hybrid) | REPORT + path chosen + rationale |
| **R-RBS-LM-3** | Source model selection + baseline measurement | REPORT + downloaded model + baseline metrics (perplexity, hallucination corpus, agreement-rate target) |
| **R-RBS-LM-4** | Encoder design — float weights → bipolar HDC bindings | REPORT + encoder implementation |
| **R-RBS-LM-5** | Encoding the source model — run encoder; produce RBS-LM instrument; measure compression ratio | REPORT + instrument bytes + ratio |
| **R-RBS-LM-6** | Inference cascade implementation — RBS-LM forward pass per R-RBS-NN-3b §6 | REPORT + inference engine |
| **R-RBS-LM-7** | Validation against source — agreement rate, hallucination match, per-class diagnostics, **+ BCI-compatibility criteria (per-token latency ≤ 50–100 ms; ≤ 8 GB footprint; CPU-only)** | REPORT + validation metrics + BCI-criteria table |
| **R-RBS-LM-8** | Diagnostic + iteration — if fidelity floor not met, identify lossy step and fix | REPORT + diagnostics + iteration history |
| **R-RBS-LM-9** | Scale-up test — pick a model size **deployable on BCI-companion hardware**, not the largest possible; validate no-VRAM claim at that scale | REPORT + second instrument + deployment-envelope verification |
| **R-RBS-LM-10** | Catalog landing — AMSC catalog at `docs/srmech/catalogs/rbs_lm/` | catalog + validator |

REPORT filename pattern: `R-RBS-LM-{n}_{slug}_REPORT.md` in this directory.

---

## §3 Risks and open questions named at arc opening

The user explicitly named this *"daunting"*. Honest naming of where the risk lives:

### §3.1 Bipolarization loss (R-RBS-LM-4 risk)

Float weights are continuous in [−bound, +bound]; bipolar is {−1, +1}. The information loss when sign-quantizing weights is real and documented in the BNN literature (Courbariaux et al. 2016; Hubara et al. 2016 XNOR-Net; later BiT and BitNet). Typical accuracy degradation from float to binary: 5–30% on benchmarks, varying widely.

**Fidelity-floor implication:** if bipolarization itself loses 10% accuracy vs the source model, we cannot reach "exactly the source model's hallucinations" without compensating mechanism. Compensation candidates: residual encoding (Class L Laplacian projection of the common subspace; Class M for the residual), magnitude-augmented bipolar (per-position {-2, -1, +1, +2} ternary-bipolar at higher D cost), or hierarchical bipolar refinement (multiple bipolar passes accumulating residuals).

### §3.2 Cleanup-capacity vs model-parameter scale (R-RBS-LM-5 risk)

R-RBS-NN-7 §3.2: cleanup capacity per bundle is srmech-`MAX_BUNDLE_N=257`-bound, requiring hierarchical bundling for larger collections. A GPT-2-small with 124M parameters / 12 layers / 768 hidden / 50257 vocab is **orders of magnitude** beyond the single-bundle cleanup ceiling. Hierarchical bundling (sub-groups of ≤257; bundle-of-bundles layer) is the structural workaround, but each hierarchy level adds projection cost — the eventual cleanup margin may be too small at deep hierarchies.

**Fidelity-floor implication:** at some hierarchy depth, the cleanup-similarity stops being reliable. Where that depth sits for GPT-2-small is an empirical question for R-RBS-LM-5/7. If the answer is "depth too shallow," we either (a) grow D (R-RBS-NN-7 §5.1 — orthogonal axis), or (b) split the model across multiple RBS-HDC instruments and route between them.

### §3.3 Attention fidelity — Mechanism 2 vs Mechanism 3 (R-RBS-LM-6 risk)

R-RBS-NN-3b §3: conventional soft attention `Σ softmax(S)_j · V_j` IS Mechanism 2 (bundle-of-rotations, ~6.9% averaging cost). The Level-1 substitute is hard attention (Mechanism 3, `V[argmax]`, no averaging cost). **These differ behaviorally:** soft attention smears information across context positions; hard attention picks one. The fidelity floor requires exact behavioral match including hallucinations.

If soft attention IS load-bearing for the source model's specific behavior (and it likely is — modern LLMs are tuned around soft attention's gradient signal), hard attention will NOT reproduce its hallucinations exactly. **Compensation candidate:** a Level-2 soft-attention path is structurally available (R-RBS-NN-3b §5 names LayerNorm, soft-softmax, and bundle-attention as the three Level-2-forcing components) — we lift to FPU at attention only, keep MLP at Level 1. This is HYBRID compute, not pure Level 1.

The "no VRAM" claim still holds in the hybrid: FPU on CPU is not GPU. But the pure-Level-1 claim of R-RBS-NN-3b §6 is relaxed.

### §3.4 Cross-substrate inversion fidelity (R-RBS-LM-1 risk — the foundational question)

The framework reads conventional LLM weights as a Mechanism 2 projection of substrate-native Mechanism 1 content. **But Mechanism 2 is lossy** (~6.9% per the canonical signature). If the source model's weights ARE this lossy projection, then the "true" Level-1 content the source model approximates is in principle recoverable from the source's behavior, not its weights. Path B (function-level encoding) is therefore structurally more truthful to the framework reading than Path A (weight-level).

But Path B requires a behavioral corpus — running the source model to extract its input→output mappings, then HDC-binding those. **At what corpus size does Path B reach fidelity floor?** Open empirical question; if corpus needs to be larger than the source model itself, the no-retrain claim collapses (we're effectively retraining via a different mechanism). Resolves in R-RBS-LM-5/7.

### §3.5 The "chaotic stochastic stuff" observation

User's exact phrase: *"the existing substrate is chaotic stochastic stuff."* This names the load-bearing observation: trained LLM weights are **not algebraically clean** — they are the result of stochastic gradient descent over noisy training corpora, carrying training-noise as well as learned-content. The cross-substrate translation has to handle BOTH: it must encode the learned-content losslessly enough to match behavior, AND it must encode the training-noise faithfully enough to match hallucinations.

This is the hardest part. The framework reads training-noise as the bundle-of-views averaging signature itself (per MFO §VII.1.3 line 741) — it isn't separable from the projection. Extracting only the "clean" learned-content would change the hallucination rate; matching the hallucination rate requires preserving the noise. **The translation cannot factor learning from noise.**

This may force Path B (function-level) over Path A (weight-level): only by mimicking the source model's INPUT→OUTPUT behavior can we preserve both signals together.

---

## §4 Working constraints (inherited from RBS-NN arc)

| Constraint | Plan |
|---|---|
| Temp research subtree | `docs/srmech/rbs_lm_research/` (this directory) |
| Eventual SSoT | `docs/srmech/srmech_research_notebook.md` absorbs at R-RBS-LM-10 close, **deferred-by-design** per no-edits-to-existing-srmech |
| Catalog homes | `docs/srmech/catalogs/rbs_lm/` per srmech convention; created at R-RBS-LM-10 |
| No-edits constraint | Only ADD new files. Existing srmech modules untouched. Issues surface in `UPSTREAM_NOTES.md` per `[[feedback_upstream_srmech_fixes_as_research_notes]]` |
| PR shape | Same rolling draft PR (#684); partition-boundary updates per `[[feedback_rolling_pr_partition_boundary_updates]]` |
| No sub-agents | Sequential main-context work per `[[feedback_no_subagents_compact_via_re_prime]]`; re-prime from CLAUDE.md + MEMORY.md + srmech tool-schema on compact |
| Attestation | MPR v1 per CLAUDE.md §2; external model + library citations land with arXiv/HF references |
| Vocabulary | Abstract operational lexicon canonical per `[[feedback_abstract_lexicon_is_ada_accommodation]]` |
| Discipline | full coverage per `[[feedback_full_coverage_shipping_mpm_way]]` + `[[feedback_no_mvp_framing]]` |

---

## §5 What's known to stand from prior work

| Standing | Source | Role in RBS-LM |
|---|---|---|
| RBS-HDC instrument at D=8192 | srmech Spike #170 | the substrate-native instrument shape |
| Ephemerides precedent (3.3 GB → 256 KB) | ephemerides notebook §1.4 | the cross-substrate compression existence proof at different binding shape |
| Class A content-mint, Class M XOR-bind, Class K argmax, Class I cyclic shift | srmech.amsc + signal_processing | the Level-1 atomic ops |
| Hierarchical bundling (open thread) | R-RBS-NN-7 §3.2 + ROADMAP.md NEXT-5 | the workaround for n > MAX_BUNDLE_N=257 |
| 4-class Level-1 transformer recipe | R-RBS-NN-3b §6 | the inference cascade shape |
| Per-class instruction-primitive map | R-RBS-NN-8 §3 | the CPU-only throughput envelope |
| Conventional NN literature placement | R-RBS-NN-1 / -3a / -3b | the framework reading already on PR |

What does NOT yet stand: any empirical work with a real trained LLM. R-RBS-LM is the empirical leg of the arc.

---

## §6 Cross-arc references

- **RBS-NN arc (closed):** all R-RBS-NN-1..-9 REPORTs in `docs/srmech/rbs_nn_research/`; the framework reading that RBS-LM inherits
- **Ephemerides precedent:** `docs/antikythera-maths/ephemerides_spectral_research_notebook.md` §1.4 (52-body / 3.3 GB → 256 KB)
- **MFO substrate-self-recognition sign-flip:** `mfo_spectral_research_notebook.md` §VII.6.11.6 (lines 2802–2823)
- **R30 walking-path 9/9 antiquity convergence:** PR #680 + close-out commit `44eb7aee` — the 1:3:7:3 substrate-native ordering on which the framework reading rests
- **ROADMAP.md (RBS-NN post-arc):** `docs/srmech/rbs_nn_research/ROADMAP.md` NEXT-1 (this arc's entry point); NEXT-5 (hierarchical bundling, required for any non-trivial model size)
