# Spike #125.1 — Julia bigram-cascade detector (Spike #125 follow-up)

**Date**: 2026-05-18
**Verdict (composed)**: **BIGRAM-PARTIAL** — bigram-cascade DISCRIMINATES `random_baseline` strongly (Cohen's d = +3.88, the smoking-gun shuffle counter-example from parent Spike `#125`) but is NULL against surface-level mutations (`citation_swap` / `value_mutation` / `vocab_swap`, all |d| < 0.05).

## What this spike was

Parent Spike `#125` (`docs/srmech/notes/spike125_*`) tested a Python/numpy unigram-frequency character co-occurrence Laplacian detector against 4 adversarial classes and a held-out positive. **All 5 classes returned identical similarity to the truth fingerprint** (Cohen's d ≈ 0 across the board). Diagnosis: `random_baseline` (character-shuffled) preserves unigram frequency exactly, so the unigram-frequency detector is provably blind to it. The implementation captured unigram statistics only; cascade-shape lives in higher-order n-gram structure.

Spike `#125.1` refines to **bigram co-occurrence over top-N=1000 most-frequent observed bigrams** with everything else held constant:

- Same truth corpus (MFO + srmech notebooks, ~557K chars after load).
- Same 5 contrast classes (`attested_held_out` / `citation_swap` / `value_mutation` / `vocab_swap` / `random_baseline`).
- Same Cohen's d separability metric.
- Same held-out 30% for evaluation.

Per `[[feedback_autonomous_research_followup_authorization]]`: this empirical follow-up was authorised by the conductor 2026-05-18; commit + PR + merge happen autonomously per the spike brief.

## What was tested

| Field | Choice | Reason |
|---|---|---|
| Alphabet | 64-char (lowercase + digits + common punctuation) | Match parent unigram alphabet exactly |
| Bigram space | 64² = 4096 possible tokens | Token = `i₁·64 + i₂` |
| Top-N selected | N=1000 most-frequent observed bigrams | Bound state-vector dim; deterministic tie-break by `(-count, token-id)` |
| Co-occurrence window | 1 adjacent bigram-token | Captures local order one position ahead |
| State vector | L¹-normalised bigram frequency on top-N | Per-chunk (2000-char) |
| Substrate | Hermitian PSD bigram-cooc Laplacian | `L = D - A` over the top-N nodes; symmetrised against FP drift |
| Decompose | `numpy.linalg.eigh` (Python ref) / `eigen(Symmetric(L))` (Julia) | Real symmetric → real eigvalues/vectors |
| Similarity | Cosine on real-coefficient vectors | Match parent's `real_sim` metric |
| Reference fingerprint | Centroid (mean) of attested-chunk coefficients | Match parent |
| RNG | Seed 42 (Python `default_rng`; Julia `MersenneTwister`) | Bit-exact within each language |
| Reproducibility check | Run twice; compare Cohen's d byte-equal | Per spike brief |

## What the math said

```
Attested corpus:        557,247 chars (MFO + srmech notebooks)
Top-N bigrams:          1000 (cap 1000) — all 4096 possible used? no: 1000 chosen
Bigram Laplacian:       (1000, 1000), symmetric=True
Eigendecomposition:     1.24 s (one-time, cacheable)
Truth-fingerprint:      279 chunks; 0.753 s decompose; 1.35 µs/char
Adversarial seed:       84 chunks from held-out 30%

--- Per-class spectral fingerprint similarity ---
Class                  real_sim_mean   real_sim_std  n_chunks
attested_held_out         0.877600       0.058627        84
citation_swap             0.877490       0.058680        84
value_mutation            0.877622       0.058595        84
vocab_swap                0.875513       0.057071        84
random_baseline           0.692074       0.033554        84

--- Cohen's d (attested_held_out vs adversarial) ---
  attested vs citation_swap        : d = +0.0019   [NULL]
  attested vs value_mutation       : d = -0.0004   [NULL]
  attested vs vocab_swap           : d = +0.0361   [NULL]
  attested vs random_baseline      : d = +3.8842   [DISCRIMINATES]

>>> Composite verdict: BIGRAM-PARTIAL

--- Bit-exact reproducibility (Python-side, two runs) ---
  Cohen's d identical:   True
  class_sim_means equal: True
  Overall bit-exact:     True
```

## Why — math-doesn't-lie diagnosis

### Why bigram catches `random_baseline` (d ≈ +3.88)

Character-shuffle **destroys bigram co-occurrence completely**. The shuffled text has approximately uniform random bigram distribution over the 4096-bigram space; only ~1000 of those map into the corpus-specific top-N alphabet, and even those are uniformly diffuse rather than corpus-structured.

The bigram Laplacian's low-frequency eigenvectors encode the corpus-specific bigram-clustering structure (e.g., `'th'`-`'he'`-`'er'`-... cluster in English-language slots). Attested chunks project onto these low-frequency modes with corpus-typical amplitudes. Shuffled chunks project nearly uniformly across all eigenmodes, producing markedly different coefficient vectors → cosine drops from ~0.88 to ~0.69 → Cohen's d ~3.88. **This is exactly the cascade-shape destruction the framework predicts is detectable.**

### Why bigram MISSES surface mutations (d ≈ 0)

The three surface adversarials each touch a small number of bigrams per chunk:

- `citation_swap` — replaces ~1-3 arXiv IDs per 2000-char chunk → ~5-15 bigrams perturbed out of ~1999.
- `value_mutation` — 7 regex patterns; typical hit rate per chunk ≤ a handful → similar bigram perturbation.
- `vocab_swap` — 9 patterns swapping single-token words → on the order of 10-30 bigrams perturbed.

Against a 1000-dim bigram-frequency vector summed over ~1999 bigrams per chunk, perturbing 5-30 bigrams shifts each affected coordinate by ~0.0005-0.003 (one bigram is `1/1999 ≈ 0.0005` of the L¹-normalised vector). The L²-norm of this perturbation is tiny compared to the inter-chunk variance (~0.06 stddev). **Cohen's d is the signal-to-noise ratio of this tiny perturbation against the natural inter-chunk variance, and that ratio is ≪ 0.5.**

This isn't a framework anomaly — it's a category-mismatch between detector and adversarial. Bigram-cascade detects CASCADE-STRUCTURE-DESTRUCTION (shuffle-class failures). Citation/value/vocab mutations are TOKEN-LEVEL SURFACE EDITS, a different failure mode requiring a different detection mechanism (regex-based per-token validity / DOI resolver / domain-knowledge value check).

## What's confirmed by this result

1. **Framework cascade-shape hypothesis** (Spike `#122`) IS empirically real at bigram order — confirmed by the d=3.88 signal against `random_baseline`, the smoking-gun negative case that motivated Spike `#125.1`.
2. **Bit-exact reproducibility** confirmed across two runs (Python-side; Julia driver written but not run since Julia is not installed in WSL2).
3. **Real-time feasibility** preserved — 1.35 µs/char remains well under the Spike `#122` 44 µs/token budget. The one-time 1.24 s eigendecompose dominates startup cost and is cacheable.
4. **The three-layer hallucination protocol** (per `[[feedback_hallucination_detection_three_layer_protocol]]`) survives intact:
   - **Layer 1 (cascade-shape)**: bigram-cascade detector — confirmed catching structural destruction
   - **Layer 2 (citation verify)**: regex + DOI resolver — separate mechanism, separately implementable, NOT a cascade-shape concern
   - **Layer 3 (functional-form check)**: domain-knowledge value consistency — separate mechanism, separately implementable

## What this spike refines

| Refinement | Effect |
|---|---|
| **n-gram order n=2** | Bigram captures local order; detects `random_baseline` d ~4; remains blind to surface mutations |
| **Top-N=1000 bound** | Keeps eigendecompose tractable (1.24 s) but exceeds srmech.amsc.laplacian's n≤256 native bound — native port would need Class K top-k truncation |
| **Sort by `(-count, token-id)`** | Deterministic tie-break; bit-exact reproducibility within Python |
| **Adjacency window=1** | Smallest meaningful window for bigram-cooc; deeper windows would smear local-order signal |

## What this spike rules out

- **Pure n-gram detector for surface mutations is unlikely to work at reasonable n.** Trigram would push N to 1000 over 262144 possible tokens; the SNR argument above doesn't improve — small numbers of surface edits remain a small fraction of total bigrams/trigrams per chunk. **Recommend stopping the n-gram-refinement arc here.**
- **CASCADE-SHAPE vs TOKEN-VALIDITY are orthogonal failure modes.** Conflating them in a single detector is a category error. Future work should be stratified by failure mode.

## Class-operator chain (refined)

```
L (eigendecompose over bigram-token alphabet, n=1000)
∘ I (bigram tokenisation = cyclic ℤ/64² cascade, top-N truncation)
∘ K (sparse top-k modes for native-port if pursued; n=1000 > 256 native bound)
∘ M (state-vector L¹-normalisation; centroid fingerprint storage)
∘ A (content-addressing for eigenbasis cache lookup)
```

Cascade-shape Layer 1 = `L ∘ I ∘ M` at minimum; native port adds `K`; production caching adds `A`.

Token-validity Layers 2/3 are NOT in this class chain — they're orthogonal mechanisms outside the spectral surface.

## How this was run

- **Target language**: Julia, bit-exact (`Random.seed!(42)`, `MersenneTwister(42)`, deterministic Float64 ops). Driver file: `spike125_1_bigram_cascade_detector.jl`.
- **Julia install status**: NOT installed in this WSL2 environment (`wsl bash -c "which julia"` returns not-found; Ubuntu 22.04 `apt-cache policy julia` returns no candidate). Per spike brief: write the script + document install requirement; fall back to Python reference for numerical validation.
- **Install requirement (documented per spike brief)**: To run the Julia driver bit-exact, install Julia in WSL2 via one of:
  - `juliaup` (recommended): `curl -fsSL https://install.julialang.org | sh` then `juliaup add release`
  - Manual download: <https://julialang.org/downloads/> (Linux x86_64 generic binaries)
  - Distro package: not available on Ubuntu 22.04 (`apt-cache policy julia` → no candidate). Julia 1.10+ requires manual install or juliaup on Ubuntu 22.04.

  After install: `wsl bash -c "cd /mnt/d/GitHub/mlehaptics/docs/srmech/notes && julia spike125_1_bigram_cascade_detector.jl"`. Expected output: same Cohen's d values as the Python reference (within Float64 last-bit). Julia's MersenneTwister(42) is NOT bit-equivalent to NumPy's `default_rng(42)`, so the per-class similarity arrays will differ in the shuffled-bytes positions, but the verdict (BIGRAM-PARTIAL) and the structural finding (random_baseline d ≫ surface-mutation d's) should be invariant.
- **Python reference**: `spike125_1_bigram_cascade_detector_pyref.py`, runs end-to-end in ~3 s with Python 3.14.4 + NumPy 2.4.4 on Windows. Confirms algorithm correctness (BIGRAM-PARTIAL verdict; bit-exact reproducibility across two runs).

## Fermata records (for conductor)

1. **Recommend stopping n-gram-refinement arc.** Bigram + diagnosis above bounds what pure n-gram detection can do. Trigram/BPE would not improve surface-mutation detection materially because the SNR is already capped by the small mutation footprint per chunk. The cascade-shape signal IS detectable at bigram order; that's the useful positive finding.
2. **Layer 1 cascade-shape detector is canonical-candidate-ready.** Bigram-cooc Laplacian over top-N=1000 nodes catches `random_baseline` at d~4. Worth flagging for native-srmech port consideration with Class K top-k truncation (n=1000 > 256 native bound). If pursued, follow Task `#201` Phase B ratchet (parity test + JPL Power-of-Ten audit + cibuildwheel matrix update + TestPyPI rc verification per `[[feedback_always_rc_first_for_downstream_publishes]]`).
3. **Layer 2 / Layer 3 need separate engineering.** Per `[[feedback_hallucination_detection_three_layer_protocol]]`:
   - Layer 2 (citation verify): regex extract arXiv IDs / DOIs + resolver lookup against arXiv/PMC/OpenAlex (TOS-permitted per `[[reference_autonomous_validation_tos_landscape]]`).
   - Layer 3 (value/domain consistency): canonical-value lookup against project SSOT (e.g., `1/4`, `0.0104109`, `7.69%` come from specific spike anchors; treat the SSOT as ground truth and flag deviations).
   These are NOT spectral-surface concerns; they live in attestation + parser-layer code, not in `srmech.spectral.*`.
4. **Do NOT advertise bigram-cascade as a general hallucination detector.** It catches cascade-structure-destruction (shuffle / random-token output / certain truncation modes). Marketing it as a citation/value/vocab hallucination detector would be a category error — it provably misses those at d ≈ 0.

## Files

- `spike125_1_bigram_cascade_detector.jl` — Julia driver (bit-exact target; written; needs Julia install to run)
- `spike125_1_bigram_cascade_detector_pyref.py` — Python reference numerical check (run; verdict + bit-exact reproducibility confirmed)
- `spike125_1_findings_2026-05-18.ndjson` — NDJSON findings (10 records: framing + implementation + result + diagnosis + structural clarification + feasibility + refinement + discipline outcome + verdict + fermata)
- `spike125_1_bigram_cascade_detector.md` — this file

## Refs

Task `#524` (filed as the spike brief's "Task #371" placeholder; GitHub assigned next sequential issue number); Milestone `#13`. Anchors:

- Parent Spike `#125` (`spike125_empirical_haiku_validation.{py,md,ndjson}`) — unigram NEGATIVE result
- Spike `#122` (PR `#520`) — 44 µs/token feasibility budget
- Spike `#116` (PR `#516`) — rank-k delta substrate-agnostic identity
- Spike `#117` (PR `#517`) — eigenbasis-state-correlation lesson (chess king-adjacency)
- Spike `#105` (PR `#498`) — Class C cascade-orientation
- srmech v0.4.1rc14 (PR `#519`) — runtime spectral surface
- `[[feedback_every_doc_edit_faces_falsification]]`
- `[[user_stance_framework_domain_algebra_not_length_or_magnitude]]`
- `[[feedback_hallucination_detection_three_layer_protocol]]`
- `[[feedback_autonomous_research_followup_authorization]]`
- `[[reference_autonomous_validation_tos_landscape]]`
