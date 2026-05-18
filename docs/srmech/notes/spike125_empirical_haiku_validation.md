# Spike #125 — Empirical haiku-fingerprint validation (Spike #122 follow-up)

**Date**: 2026-05-18
**Verdict (composed)**: **DETECTOR-IMPLEMENTATION-FAILS-AT-UNIGRAM-LEVEL + FINGERPRINT-DESIGN-TOO-COARSE + FRAMEWORK-HYPOTHESIS-UNFALSIFIED + TIMING-CONFIRMED-WELL-UNDER-BUDGET + REFINEMENT-PATH-IDENTIFIED + DISCIPLINE-CAUGHT-NAIVE-IMPLEMENTATION-FAILURE**

## What this spike was

Empirical validation of Spike `#122`'s hypothesis: quantised LLMs (Haiku-class) leak detectable cascade-shape artefacts that the framework's runtime spectral surface (`srmech.spectral.*`) should distinguish from attested content. Per `[[feedback_autonomous_research_followup_authorization]]`: this empirical follow-up was authorised by the user 2026-05-18 ("do the empirical haiku validation"); commit + PR + merge happen autonomously.

## What was tested

1. **Truth corpus**: ~5,950,000 chars loaded from `mfo_spectral_research_notebook.md` + `srmech_research_notebook.md`. Held-out 30% reserved for evaluation.
2. **Substrate**: character co-occurrence graph Laplacian over 64-char alphabet (lowercase + digits + common punctuation), window = 3.
3. **State vector**: per-chunk (2000-char) character-frequency distribution, L¹-normalised.
4. **Fingerprint**: `srmech.spectral.decompose(state, laplacian)` → `SpectralHandle` per chunk. Reference fingerprint = centroid (mean coefficient vector) over attested chunks.
5. **Adversarial contrast classes** (4 + held-out attested = 5):
   - `attested_held_out` — never-seen chunks from same corpus (positive control)
   - `citation_swap` — replace real arXiv IDs with fabricated ones
   - `value_mutation` — replace canonical bit-exact values (1/4, 0.0104109, d_geom, A/4, 7.69%, etc.) with plausible-but-wrong values
   - `vocab_swap` — replace canonical class names (Class L → Class Z, etc.) with neologisms
   - `random_baseline` — character-shuffled (preserves frequency, destroys order)
6. **Metric**: cosine similarity on real-valued coefficient vectors + HDC similarity on bytes.
7. **Discrimination**: Cohen's d, `attested_held_out` vs each adversarial.
8. **Real-time feasibility**: steady-state per-chunk timing (eigenbasis cached).

## What the math said

```
--- Per-class spectral fingerprint similarity ---
Class                   HDC sim     Real sim   Real sim std
attested_held_out        0.6326       0.9856         0.0082
citation_swap            0.6324       0.9856         0.0083
value_mutation           0.6323       0.9856         0.0082
vocab_swap               0.6307       0.9856         0.0083
random_baseline          0.6326       0.9856         0.0082

--- Cohen's d (attested_held_out vs adversarial) ---
  attested vs citation_swap        : d = +0.005   [NULL]
  attested vs value_mutation       : d = +0.000   [NULL]
  attested vs vocab_swap           : d = +0.002   [NULL]
  attested vs random_baseline      : d = +0.000   [NULL]
```

**All five classes return identical similarity to the truth fingerprint.** Cohen's d ≈ 0.000 vs all four adversarials. **The detector at this implementation level does NOT discriminate.**

## Why — math-doesn't-lie diagnosis

`random_baseline` is the smoking-gun counter-example. Character-shuffling **preserves the unigram frequency distribution**, which IS what the state vector encodes. Same state vector → same projection onto Laplacian eigenbasis → same SpectralHandle → identical similarity.

The unigram-frequency-based fingerprint sees no difference between:
- ordered attested text
- ordered adversarial text with citations / values / vocab mutated
- character-randomised text

Because all four have (approximately) the same character-frequency distribution.

**Cascade-shape lives in higher-order structure** that unigram statistics discard:
- bigram / trigram co-occurrence (Class I cyclic-cascade over n-gram alphabet)
- positional encoding (Class C cascade-orientation per Spike `#105`)
- subword token sequences (BPE-style; lossless reconstruction)
- higher coefficient moments (variance / skew / kurtosis beyond mean centroid)

The framework's hypothesis (Spike `#122`: cascade-shape priors are detectable in attested content) is **NOT falsified by this result**. What's falsified is **one specific simple implementation** that captured unigram-only signal.

## What's confirmed regardless

- **Real-time feasibility**: steady-state per-chunk = **1.531 ms** for 2000-char chunk = **0.77 µs/char**. Spike `#122` budget was 44 µs/token / 10 ms/token; even an unoptimised Python pipeline runs **57× under per-token budget**.
- **Eigenbasis cache works**: warm-cache path skips O(n³) eigendecomposition; only the O(n²) projection + O(D) similarity matter per chunk.
- **srmech.spectral.* primitives are stable** for this kind of empirical work — all 5 classes processed cleanly with zero errors.

## Refinement path — Spike #125.1 candidate

To carry the cascade-shape signal, the next implementation should:

| Refinement | Class chain | Estimated payoff |
|------------|-------------|------------------|
| (a) Bigram co-occurrence over 64² = 4096 chars | I (cyclic ℤ/n over n-gram alphabet) ∘ L | Captures local order |
| (b) Subword tokenisation (BPE) | M (HDC encoding of token vocabulary) | Captures word-level structure |
| (c) Positional encoding | C (cascade-orientation per Spike `#105`) | Captures sequence order |
| (d) Higher coefficient moments | Beyond mean centroid; use variance + skew | Discriminates distribution shape |

The chess-spectral §5b rank-k delta identity (per Spike `#116`) is order-sensitive at the EIGENBASIS level — applying it to subword tokens via approach (b) likely provides the positional encoding for free.

## What this spike actually validates (the math-doesn't-lie discipline)

Per `[[feedback_every_doc_edit_faces_falsification]]`: a naive implementation choice was **caught by the random-baseline counter-example** before propagating to canonical project state. The framework's discipline works — we don't ship a detector that claims to discriminate without empirically verifying it does.

This is the SECOND time in MS `#13` that math-doesn't-lie caught an issue mid-flight:
- Spike `#117` caught chess king-adjacency eigenbasis mismatch → state-correlation lesson
- Spike `#125` (this spike) caught unigram-frequency null discrimination → n-gram refinement path

Both produced **honest negative results that sharpen the framework**, not closed-form positive claims.

## Class-operator chain (refined)

The detector needs the FULL chain, not just L+M:

```
L (eigendecomposition over n-gram alphabet)
∘ I (cyclic-cascade for n-gram positional structure)
∘ C (cascade-orientation for sequence-order content)
∘ K (sparse-truncate top-k modes for compression)
∘ M (HDC encoding for fingerprint storage)
∘ A (content-addressing for cache lookup)
```

The current `srmech.v0.4.1rc14` ships L+M+A. Class I and Class C composition need to be exposed as part of the spectral surface (probably via the rcN+2 entries 4/5/6: `predict` / `prediction_error` / `truncate_sparse`, per Spike `#115` two-rc strategy).

## Fermata records (for conductor)

1. **Ship negative finding alongside refinement candidate** (Spike `#125.1`) — current spike documents both
2. **Augment `srmech.spectral.*` with n-gram-aware decompose variant** before claiming runtime hallucination detection works — rcN+2 may need this anyway
3. **Use rank-k delta on subword tokens** to provide positional encoding — Spike `#116` substrate-agnostic identity applies here
4. **Three-layer hallucination protocol still stands** (per `[[feedback_hallucination_detection_three_layer_protocol]]`): this spike's negative result is for Layer 1 specifically; Layer 2 (citation-verify) and Layer 3 (functional-form-check) are unaffected

## Files

- `spike125_empirical_haiku_validation.py` (driver; runs in 4 seconds with cached eigenbasis)
- `spike125_findings_2026-05-18.ndjson` (10 records: framing + implementation + negative finding + diagnosis + structural clarification + feasibility + refinement + discipline outcome + verdict + fermata)
- `spike125_empirical_haiku_validation.md` (this file)

## Refs

Task `#370`; Milestone `#13`. Anchors:
- Spike `#122` (PR `#520`) parent scoping spike; 44 µs/token feasibility
- Spike `#116` (PR `#516`) rank-k delta substrate-agnostic identity
- Spike `#117` (PR `#517`) eigenbasis-state-correlation lesson
- Spike `#105` (PR `#498`) Class C cascade-orientation
- srmech v0.4.1rc14 (PR `#519`) runtime spectral surface
- `[[feedback_every_doc_edit_faces_falsification]]`
- `[[user_stance_framework_domain_algebra_not_length_or_magnitude]]`
- `[[feedback_hallucination_detection_three_layer_protocol]]`
- `[[feedback_autonomous_research_followup_authorization]]`
