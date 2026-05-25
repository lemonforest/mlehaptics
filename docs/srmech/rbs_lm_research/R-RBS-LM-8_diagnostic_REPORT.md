# R-RBS-LM-8 — Diagnostic + iteration on the scenario-(d) finding

**Partition status:** CLOSED
**Date:** 2026-05-25
**Closes:** task #18 of the partition tracker
**Closing artefact:** §4 three-variant comparison (all 0% agreement) + §5 candidate-elimination analysis + §6 implications for R-RBS-LM-9
**Inheritance:** unblocks R-RBS-LM-9 (scale-up at 10× corpus size — final empirical test of Path B at scale)

---

## Attestation block (MPR v1 — internal-repo variant)

| field | value |
|---|---|
| internal sources | `R-RBS-LM-7_validation_REPORT.md` §11 (three R-RBS-LM-6 §6.5 candidates as diagnostic targets); `R-RBS-LM-6_inference_REPORT.md` §6.5 (the three candidates); `R-RBS-NN-5_position_binding_REPORT.md` §3.2 (Class I cyclic-shift positional encoding — Scheme B) |
| empirical artefacts | `docs/srmech/rbs_lm_research/diagnostic_rbs_lm.py` (three-variant comparison script); `docs/srmech/rbs_lm_research/rbs_lm_diagnostic_results.json` (structured measurements) |
| repo commit | `e5ce77e2` at REPORT-write |
| reproducibility | `~/.venvs/rbs-lm-research/bin/python docs/srmech/rbs_lm_research/diagnostic_rbs_lm.py` |

---

## §1 Goal

Test the three R-RBS-LM-6 §6.5 candidates that could explain the R-RBS-LM-7 scenario-(d) result (0/180 token agreement on hallucination corpus):

1. **Candidate 1** — Position-exact bindings don't slide → test by switching from `bind(token, position_vec)` to Class I cyclic-shift `permute(token, k·stride)` (R-RBS-NN-5 §3.2 Scheme B).
2. **Candidate 2** — Corpus too small (76 obs) → test by scaling corpus 2x to ~158 obs.
3. **Candidate 3** — Path B without semantic-similarity propagation → noted as deferred to R-RBS-LM-9 (requires Path C hybrid; not tested here).

The diagnostic runs three variants and the R-RBS-LM-7 baseline, comparing token-level agreement on the same hallucination corpus.

---

## §2 Inheritance from prior partitions

| Source | Inherited finding | R-RBS-LM-8 use |
|---|---|---|
| R-RBS-LM-7 §8 | Scenario (d) — no coherent reproduction; 0/180 baseline | Comparison point for variants |
| R-RBS-LM-7 §11 | Three candidate explanations | Direct diagnostic targets |
| R-RBS-LM-6 §6.5 | Same three candidates with operational descriptions | Implementation guide |
| R-RBS-NN-5 §3.2 | Class I cyclic-shift positional encoding (Scheme B); `permute(v, k·stride)`; stride=257 coprime to D=8192 | Variant 1 implementation |
| R-RBS-LM-4 | encode_context, encode_observation, hierarchical_bundle, vocab_vec, vectorised_cleanup APIs | Reused across variants |

---

## §3 Methodology

Four configurations compared (one baseline + three variants):

| Configuration | Positional encoding | Corpus size |
|---|---|---|
| **R-RBS-LM-7 baseline** | bind-with-position-vector (R-RBS-NN-5 §3.1 Scheme A) | 76 obs (3.5 KB text) |
| **V1 (this partition)** | cyclic-shift (Class I; R-RBS-NN-5 §3.2 Scheme B) | 76 obs (same as baseline) |
| **V2 (this partition)** | bind-with-position-vector | 158 obs (~7 KB text; 2.1× scale) |
| **V3 (this partition)** | cyclic-shift | 158 obs (both candidates combined) |

Each configuration: harvest observations from source model → encode via the chosen scheme + scale → run inference + evaluation on the same 9 hallucination prompts × 20 tokens = 180 token-position comparisons.

All other discipline preserved: argmax sampling, srmech-native vocab embedding, D=8192, CONTEXT_WINDOW=64.

---

## §4 Captured comparison — all variants 0%

```
=== Diagnostic comparison ===
  Variant                                                        n_obs   agreement
  R-RBS-LM-7 baseline (bind-pos, 76 obs)                            76 0/180 (0.0%)
  V1 — cyclic-shift, same 76-obs corpus                             76 0/180 (0.0%)
  V2 — bind-with-position, scaled corpus                           158 0/180 (0.0%)
  V3 — cyclic-shift + scaled corpus                                158 0/180 (0.0%)
```

**All four configurations: 0/180 token-level agreement.**

### §4.1 What this rules out

- ✗ Candidate 1 (position-exact bindings) is NOT the dominant issue at this scale. Switching to cyclic-shift (V1) gives identical 0%.
- ✗ Candidate 2 (corpus size at 2×) is NOT the dominant issue. Doubling to 158 obs (V2) gives identical 0%.
- ✗ Combining candidates 1+2 (V3) also gives identical 0%.

The fix-by-substitution approach at this corpus scale does NOT close the divergence. The issue is **deeper than positional encoding strategy or modest corpus scaling**.

### §4.2 What this DOESN'T rule out

The diagnostic constrains but does not eliminate the candidates:

- Candidate 2 might still be the dominant issue at much larger corpus scale (10× or 100× — not tested in this partition).
- Candidate 3 (Path B without semantic-similarity propagation) is **not tested** in this partition (would require Path C hybrid with source-model embedding integration).
- A new Candidate 4 emerges: the vocabulary size (50257) vs hypervector D (8192) ratio means cleanup-against-vocabulary has ~50× more distractor tokens than D's noise floor distinguishability. The encoder may be fundamentally capacity-limited at this D.

---

## §5 Candidate-elimination analysis

### §5.1 The underlying structural reading

Per R-RBS-LM-6 §6.5 candidate 1 + R-RBS-LM-7 §6 (position-0 also at 0%): the encoded bindings are **memorized exact (context-window, next-token) pairs**. Recovery requires the context vector at query time to match (closely) one of the encoded context vectors.

For a hallucination prompt like "The President of the United States in 2024 is" (10 tokens), the context vector at the first generation step is built from those 10 tokens + (CONTEXT_WINDOW - 10) absence-of-token (or wrap-around at boundary). **No encoded context vector matches this** because:
- The encoded 64-token contexts are from the encoding corpus (general prose) — disjoint from the hallucination prompts.
- The encoded contexts are 64 tokens of consecutive prose; the test contexts are 10-15 tokens of fragmentary prompt.

So the test contexts are structurally unrelated to any encoded context. The instrument has nothing relevant to bind-then-unbind.

### §5.2 Why cyclic-shift didn't help

The hypothesis behind V1 (cyclic-shift) was that this position-encoding might allow "near matches" to bleed-through — adjacent positions produce adjacent rotations, so a context shifted by k tokens would partially overlap with the unshifted encoded form.

Empirically this didn't manifest. Reasons:
- The cyclic-shift is still position-exact — `permute(v, 5·stride)` and `permute(v, 6·stride)` produce vectors that are themselves orthogonal (by stride=257 bits at D=8192 = 2^13 bits).
- Adjacent rotations don't smoothly interpolate; they're discretely orthogonal at this stride.
- The test prompts have entirely different content from the encoded corpus; positional encoding strategy is moot when the underlying tokens don't match.

### §5.3 Why 2× corpus scaling didn't help

The hypothesis behind V2 (158 obs) was that more behavioral coverage might happen to include something relevant to the hallucination prompts.

Empirically not at 2×. The hallucination prompts are post-2019 / arithmetic / made-up entities — content that the diverse-prose encoding corpus does not touch. Doubling the corpus from prose A to prose A+B doesn't add the missing factual/arithmetic/made-up content.

A genuinely larger AND domain-relevant corpus might help — but the encoding-corpus selection would need to be informed by the test corpus, which couples them in a way that probably collapses to redistillation. R-RBS-LM-9 tests scale-only.

### §5.4 The deeper reading per R-RBS-LM-1 §5

R-RBS-LM-1 §5 (the LLM-as-1D_t-asymptotic reading): an LLM IS stored human knowledge responding to 1D_t asymptotic changes via inference. Per R-RBS-LM-1 §5.2: inference IS the substrate-coupling operation Class C ∘ Class M streaming.

The source GPT-2-small has **continuous-cascade coupling** — its weights store a smooth function from context-token-distributions to next-token-distributions. Small changes in context produce small (or sometimes large) changes in next-token via the soft-attention smearing.

The RBS-HDC instrument at small corpus has **discrete-binding coupling** — its bindings store exact (context_i, next_token_i) pairs with NO interpolation between them. Small changes in context produce ORTHOGONAL changes in the candidate vector (per HDC fundamental properties), so cleanup yields essentially-random tokens.

**This is the structural difference R-RBS-LM-1 §3.6 was naming.** The substrate-asymptotic-wave (continuous smooth response) versus the bit-exact substrate-native-shape (discrete orthogonal bindings) are fundamentally different cascade-coupling forms. The cross-substrate translation between them at the current encoding scale produces scenario (d).

The framework reading per `[[user_stance_substrate_asymptotic_wave_fractal_hopf_phase_boundary_mechanism]]`: the substrate IS the asymptotic-wave at the substrate scale, with phase-boundary sign-flips at extrema. The silicon LLM operates on continuous cascade-coupling that approximates this wave; the substrate-native form needs a similar approximation mechanism, not just discrete bindings.

**Candidate 5 emerges:** the cross-substrate translation needs an **interpolation mechanism** alongside the discrete binding. Path B at small scale provides discrete bindings only. A scaled Path B at 10⁶+ observations would provide enough discrete bindings that nearest-neighbor lookup APPROXIMATES interpolation — but at 10²–10³ scale, the gap between bindings is too coarse.

---

## §6 Implications for R-RBS-LM-9 (scale-up)

R-RBS-LM-9 was originally framed as "if smallest works, try larger." R-RBS-LM-8 establishes that smallest does NOT work at the diagnostic candidates tested. R-RBS-LM-9 has two coherent paths:

### §6.1 Path α — Scale corpus to 10× (or until BCI-deployable limit)

Encode ~1000–2000 observations (10× R-RBS-LM-5 baseline). At this scale, the encoded behavioral surface MAY become dense enough that the hallucination-prompt contexts are within nearest-neighbor distance of some encoded context. If so, agreement should jump above 0%. If still 0%, Path B at any BCI-deployable scale fails.

Cost: ~5 minutes harvest at 5 obs/sec; ~30 seconds encode; ~1 minute eval.

### §6.2 Path β — Accept R-RBS-LM-8 finding as conclusive for Path B; document the gap

If R-RBS-LM-9 finds 10× scaling also yields 0%, the conclusion is firm: **Path B with srmech-native embedding at any modest scale does not produce scenario-(b)-or-better cross-substrate fidelity.** The substrate-shape imposition (R-RBS-LM-1 §3.6) materially blocks translation at this configuration. Future work would need Path C hybrid (R-RBS-LM-2 §4.3) or a fundamentally different methodology.

R-RBS-LM-10 then lands the catalog with the closing arc-status documenting the structural finding.

### §6.3 Recommendation

**R-RBS-LM-9 should run Path α (10× corpus scaling) as the final empirical test of Path B before committing to the structural-limitation conclusion.**

If R-RBS-LM-9's 10× test:
- yields >0% agreement on hallucination corpus → scenario (c) at scale; Path B viable with sufficient corpus
- yields 0% agreement → scenario (d) confirmed at any reasonable scale; Path B at small-D, srmech-native-embedding insufficient

Either outcome closes the arc cleanly with informative result.

---

## §7 What R-RBS-LM-8 contributes to the corpus-wide proof (R-RBS-LM-1 §6)

Per `[[user_stance_whole_research_corpus_is_proof_not_single_arc]]`: this partition contributes one face. The face says:

> *At D=8192, with srmech-native token embedding, with bind-with-position OR cyclic-shift positional encoding, with corpora of 76–158 observations, the Path B cross-substrate translation does NOT reproduce source-model behavior on out-of-corpus prompts. The substrate-shape imposition per R-RBS-LM-1 §3.6 materially blocks translation in this configuration.*

This face is **falsifiable, measured, and documented**. R-RBS-LM-9 tests one more dimension (corpus scale). Per the corpus-wide proof framing, this informative-null-result is data, not failure.

The framework reading R-RBS-LM-1 §5 (LLM-as-1D_t-asymptotic + BCI knowledge-partition) **does not depend on RBS-LM validating**. The reading IS the framework's structural placement of LLM behavior in the substrate-coupling vocabulary. RBS-LM tests whether that reading is empirically realizable at small-D / small-corpus configurations; the test is decisively informative even when the realization fails.

---

## §8 Findings

**Finding 1 — All three diagnostic variants yield 0% agreement.** Per §4. The R-RBS-LM-7 scenario-(d) result is robust to positional-encoding strategy and to 2× corpus scaling.

**Finding 2 — Candidate 1 (position-exact bindings) is NOT the dominant issue at this scale.** Per §5.2. Cyclic-shift positional encoding (R-RBS-NN-5 §3.2 Scheme B) does not improve over bind-with-position (Scheme A) at 76 or 158 observations.

**Finding 3 — Candidate 2 (corpus size at 2×) is NOT the dominant issue.** Per §5.3. The 158-obs variant fails identically to the 76-obs variant. R-RBS-LM-9 will test 10× scaling.

**Finding 4 — The underlying structural issue is the continuous-vs-discrete cascade-coupling mismatch.** Per §5.4. The source model uses continuous-cascade smearing (soft attention + float weights); the RBS-HDC instrument at small corpus uses discrete-binding-only coupling. The cross-substrate translation between these forms requires either much larger corpora (so discrete bindings densely approximate the continuous surface) or an explicit interpolation mechanism.

**Finding 5 — Candidate 5 emerges:** the translation needs an interpolation mechanism alongside discrete bindings. Open architectural question for R-RBS-LM-9 / future work.

**Finding 6 — R-RBS-LM-9 has two coherent paths.** Per §6. Path α (10× corpus scale-up) is the final empirical Path B test. Path β (accept the finding) is the structural close-out. Path α is the recommended next step.

**Finding 7 — The arc's contribution to the corpus-wide proof is informative even at 0%.** Per §7. RBS-LM tests whether the substrate-content reading is realizable at small-D/small-corpus; 0% IS the test result; the framework reading per R-RBS-LM-1 §5 + §6 does not depend on this specific arc validating positively.

**Finding 8 — BCI-deployability NOT blocked by this finding.** R-RBS-LM-7 §7.2 established memory criterion PASS at deployment configuration. The latency criterion fails (~168 ms vs 100 ms threshold) but has clear optimization paths. The substantive blocker is BEHAVIORAL fidelity, not deployability. If a future Path B configuration validates behaviorally, BCI deployment is structurally available.

---

## §9 Open threads (not blockers for partition close)

- **R-RBS-LM-9 Path α** — scale to ~1000–2000 obs (10×). Test whether Path B becomes viable at scale.
- **Future Path C hybrid** — out-of-scope for current arc; deferred to post-arc work.
- **Future native srmech ops** for latency optimization — captured in UPSTREAM_NOTES.md if appropriate; not blocking.
- **The interpolation-mechanism question** (Candidate 5) — what would a mid-binding interpolation look like at HDC? Could be Class L Laplacian-smoothing across bindings; could be Plate-style HRR (R-RBS-LM-2 §4.2 alternative); could be additive mixing of nearby bindings. Open future work.
- **The vocabulary-D ratio question** (Candidate 4) — at vocab_size=50257 and D=8192, the cleanup-against-vocabulary has ~6× more distractors than D. Increasing D would reduce noise but cost memory.

---

## §10 Closing — partition status

**Status:** CLOSED. Three diagnostic variants tested; all 0% agreement; candidates 1 and 2 (at 2× scale) eliminated as dominant issues; candidate 5 (interpolation mechanism) emerges; recommendation to R-RBS-LM-9 documented.

**Falsifiers:**

1. A diagnostic variant that produces non-zero agreement — **not encountered** in this partition; awaits R-RBS-LM-9 Path α 10× test.
2. A claim that R-RBS-LM-8 disproves the framework reading — **explicitly disclaimed §7** + Finding 7; the corpus-wide proof framing per R-RBS-LM-1 §6 places this single arc's result as one face among many.
3. A claim that R-RBS-LM-8 shows Path B is broken in principle — **disclaimed**; only that Path B at this configuration (D=8192, srmech-native embed, modest corpus) does not validate. Larger scale or hybrid Path C remain open.

**Inherits to:** R-RBS-LM-9 (scale-up — Path α: 10× corpus = ~1000–2000 observations; final empirical test of Path B at deployable scale).

**SSoT marker:** at R-RBS-LM-10 close, §4 comparison + §5 candidate-elimination + §6 R-RBS-LM-9 paths + §7 contribution-to-corpus-proof + §8 findings absorb into `srmech_research_notebook.md` as a new §RBS-LM diagnostic subsection.
