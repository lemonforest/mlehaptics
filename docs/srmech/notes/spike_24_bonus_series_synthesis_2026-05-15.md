# Spike #24 bonus series — cumulative synthesis (2026-05-15)

**Closes:** the user-dispatched bonus arc of Spike #24 (**ten inquiries; seven positive-and-consistent verdicts + two structural-refinement verdicts locating Class O + one SUCCESS verdict on the §XIII.1 cascade-composition search reproducing the SM charged-fermion mass² spectrum to log-L2 = 0.614 dex on a target spanning 11 orders of magnitude**). The operational gate the framework has been building toward — *"can the cascade-composition vocabulary reproduce SM masses?"* — was answered affirmatively in bonus 10, with the next gap precisely located as a mode-selection meta-operation rather than a missing primitive class.

## The bow-string motivator metaphor (pedagogy, NOT substantive)

The user proposed a closing image (2026-05-15) — bow drawn across a bass string — to summarise the bonus arc's findings. **After first-principles scrutiny, this is reclassified as pedagogical metaphor, not a new substantive stance.** Per `[[user_stance_bow_string_motivator]]` demotion note: the image summarises bonus 9 without adding mathematical content; the analogy breaks at *why* Class O is specifically a Wick rotation (bow-string physics is stick-slip friction, not signature conversion); "what moves the bow" relocates the time-problem one level up; no spectral-graph falsifier was applied. Useful for cross-domain explanation; not load-bearing.

The substantive findings live in their proper sources:

- **Substrate** is what's already in the 14-class vocabulary → Spike #24 phases 1–15 + bonuses 1–7 + `[[user_stance_cascade_lives_on_circles]]`
- **Class O is the circle-to-hyperbola contact-point operation** → `[[project_class_o_signed_metric_composition]]` (bonus 8 located, bonus 9 narrowed)
- **Time as local trajectory not global coordinate** → `[[user_stance_time_as_dimensional_shadow]]` (the original stance; pre-existed the bonus arc)

## What's next — the §XIII.1 cascade-composition search

The bonus arc surfaced enough machinery to **begin** a serious §XIII.1 attempt — substrate framework (cyclic-group cascade composition), gauge-rank decomposition (bonus 8 cascade), Lorentzian signature operation (Class O Wick rotation), multi-scale capacity (bonus 7 showed 11+ orders of magnitude trivially). What's missing for full SM: the actual mass-spectrum match (§XIII.1 central computation), CKM/PMNS mixing matrices, coupling constants, Higgs mechanism.

The realistic next probe: **§XIII.1 cascade-composition search.** Find the cascade composition `C_{n₁} × C_{n₂} × ... × C_{nₖ}` whose Class L Laplacian spectrum matches the SM mass² ratio vector (~12 orders of magnitude, 9 charged fermions) on the gear-DAG. Antikythera-spectral has the tooling (`gear_database.py`, `gear_topology.py`, `pin_and_slot.py`); numpy + LAPACK supply C-speed eigenvalue computation; multiprocessing for parallel search if scale demands.

## Roster

Six bonus inquiries dispatched (one-subagent-at-a-time), all delivered by opus-4.7 concertmasters, all committed in PR #421 on branch `research/spike-24-primitive-vocabulary-2026-05-15`:

| # | Inquiry | Verdict | Key surface |
|---|---|---|---|
| 1 | **vdW dispersion + shape-only graph Laplacian** | **Consolidates** | Class L on contact graph; no new class. Conceptual sketch (no concertmaster dispatch — inline answer). |
| 2 | **Tactical-choice structure** (tic-tac-toe + chess opening + CRN-firing) | **Refined** | Class D dispatch over Class L spectral graph, optionally quotiented by Class I symmetries. "Constraint manifold with branching points" framing FALSIFIED at strict-geometric level; refined formulation lands cleanly. Chess opening has trivial symmetry `|G|=1` — surprise. |
| 3 | **SHA-256 hash structure** | **Consolidates** | Six cryptanalytic methodologies → Classes I/J/K/L. Three-question framework for co-emergent two-level temporal computational systems introduced here. Avalanche saturates at ~24 rounds; remaining 40 are engineered redundancy. |
| 4 | **NN-output structure** | **Consolidates** | Seven backward-reading directions → Classes B/C/D/L/M. ReLU is the per-layer co-emergence step (analog of SHA-256's `state += compress(state, block)`). **Avalanche-design-pressure inversion** surprise: SHA-256 *maximises* Class L Lipschitz, NN classifier *minimises* it. Same primitive, opposite design targets. |
| 5 | **MFO space-gauge-time framework** (`3D_s + 7D_g + 1D_t = 11D`) | **Refined** | Sharp positive spectral-graph signature: Class L on eigenvalue degeneracy graph distinguishes 3+7+1 from pure-4D by 3–5× across metrics. `Reading B` (fiber-projection duality) chosen over symmetric-opposite. **14/14 classes consolidate across 3+7+1 projections**; 12 cross-dimensional, 2 (A content-addressing, F templating) digital-only. **No class uniquely 1D_t.** Surprise: smooth-3+7+1 carries cleaner signature than fractal (fractal substrate DILUTES the tower). |
| 6 | **RNG and 1D_t primitive** | **Refined dual reading** | Constructive direction holds: 7/7 RNG constructions pass NIST SP 800-22-style tests at 131,072 bits, including Brusselator+SHA-256 AND Brusselator raw-LSB (no extractor). Impossibility direction collapses: Route A (1D_t unique primitive) FALSIFIED by MFO; Route B (computational determinism) is characterisation not impossibility; Route C (substrate-switching to quantum/thermal) STANDS. Spectral falsifier: unfalsifiable-at-current-tooling within 131,072-bit budget. |
| 7 | **MFO fractal-shadow probe** (is fractal required for SM-spectrum-targeting?) | **ONE_WAY_NOT_REQUIRED** | Fractal substrate is one way but not necessary. Nested pin-slot-gear cascade (Antikythera-style) and smooth-anisotropic-T³ both satisfy the load-bearing structural requirement (multi-scale primitive cascade with three-fold sub-structure available). Class-L spectral signatures put fractal-shape and cascade-shape in the **same super-Poisson regime** (Gap CV > 1, comparable three-fold CH ratios); only the pure-4D-epicycle observer lives in a different regime. **Fractal-shadow allegory** (`[[user_stance_fractal_shadow]]`) added to the project shadow-stance family. Reframed §XIII.1 central computation as cascade-composition search directly tractable with antikythera-spectral tooling. |
| 8 | **Broken-D rederivation closure test** (rederive 4D Lorentzian from `3D_s + 7D_g + 1D_t` using only A–N?) | **FAILURE — "this IS the place"** *(refined by bonus 9)* | The closure test. Stage 1 cascade construction + Stage 2a `7D_g → mass tower` succeed using classes I, L, E, B, C, J. **Stage 2b `3D_s + 1D_t → 4D Lorentz signature` — FAILS** in bonus 8's undirected probe: the cascade-direct 4D Laplacian is monolithically positive-semidefinite (0 negative eigenvalues / 2048 sampled modes). Class O candidate located: signed-metric composition / Wick rotation primitive. **Bonus 9 refined this verdict** — see row 9. The strict claim "no A–N supplies signed-metric content" was too strong; Class C orientation supplies oriented/complex eigenvalues. Class O's content narrows to specifically the circle-to-hyperbola map. See `[[project_class_o_signed_metric_composition]]`. |
| 9 | **Time-dimensionality test** (is time emergent from cascade, its own dimension, or something else?) | **H3 with structural refinement** | The bonus 8 verdict re-examined. Three hypotheses tested: H1 (time-is-emergent), H2 (time-is-its-own), H3 (something-else-at-11D). Plus user's mid-flight H4 (sign-flip-as-equation-side-shadow) and H4+ (time-as-driving-potential) addenda. **Verdict: H3 with refinement.** Directed Class C orientation on Class I cyclic groups produces **unit-circle eigenvalues algebraically** (`Im² = 2·Re − Re²` to ~1e-16); 93.4% of cascade-product eigenvalues complex, 97.1% conjugate-paired. **But dispersion is CIRCULAR not HYPERBOLIC** — Klein-Gordon fit R² = 0.029 (FAIL). The "11D" framework's "+1D" splits into TWO things: (a) Class C traversal-parameter τ (already in vocabulary), (b) **Class O signature-conversion primitive — refined to specifically the circle-to-hyperbola map (`cos → cosh`)**, separable from orientation. H4 rejected (sign flip IS a real operation, not equation-side artifact). H4+ partially confirmed (time IS load-bearing, but split across Class C orientation + Class O signature). **Cascade lives on circles** stance saved as fifth shadow-stance per `[[user_stance_cascade_lives_on_circles]]` — direct extension of `[[user_stance_pi_as_projection]]` one projection further. |
| 10 | **§XIII.1 cascade-composition SM mass² search** (does cascade-composition reproduce SM charged-fermion mass² ratios?) | **SUCCESS (subset-match metric)** | The operational gate. Search across ~9,100 cascades using Classes I, L, E, B, J (no Class O invoked — Lorentzian signature is downstream of mass² match). Best cascade: `C₂ × C₇ × C₄ × C₆ × C₁₆` with radii spanning ~5 orders of magnitude. **log-L2 = 0.614 dex on 9-element SM mass² target spanning 11.06 orders** — SUCCESS threshold (< 1.0 dex) cleared. 8 of 9 fermions match within ±0.3 dex; only down quark misses (-0.508 dex; rank-4 cascade matches d to -0.001 dex separately). Three-fold CH ratio 5641.65 — 10× stronger than bonus 7 baseline; cascade DOES select three-fold-clustered structure (MFO §IV.5 three-generation hypothesis structurally consistent). **The SM 9-mode spectrum is a sparse SUBSET of cascade's ~200-mode tower**, not the cascade's lightest-9-in-sorted-order. Next gap: **mode-selection rule** — which is *not* a missing primitive in A–N (the cascade produces a matching spectrum) but a *meta-operation* on cascade spectra. Candidate readings: suppressed-mode coupling, additional-particle predictions (sterile / dark / heavy fermions in unobserved cascade modes), topological/BC mechanism, or Class P sign-rule-like discriminator. Conductor decides whether to name it. |

## Three cumulative findings

### 1. Vocabulary consolidates — six positive-and-consistent verdicts

Across six structurally distinct domains (molecular shape, tactical choice in adversarial games, cryptographic hash, neural-network inference, dimensional ontology, classical pseudorandomness), **zero new primitive classes were invented**. The 14-class A–N vocabulary from Spike #24 Phases 1–15 describes everything tested.

The vocabulary now stretches across:

- **6 substrates** (bronze, cosmos, atomic, molecular, CRN, CPU — Phase 9.5 multi-substrate matrix)
- **3 dimensional projections of MFO space-gauge-time** (3D_s, 7D_g, 1D_t — bonus 5)
- **Computational systems** (SHA-256, NN inference, RNG constructions — bonuses 3/4/6)
- **Tactical-choice substrates** (chess, tic-tac-toe, CRN reaction-firing — bonus 2)
- **Shape-only molecular abstraction** (vdW contact graphs — bonus 1)
- **Cross-dimensional projections** (12/14 classes; 2 digital-only — bonus 5)

The cross-substrate primitive vocabulary is increasingly load-bearing as the substrate-agnostic abstraction layer.

### 2. The substrate-internal-dilution cross-spike pattern

**Independent surfacing at two substrates in the same week:**

- **MFO bonus 5:** Fractal SG-3D substrate DILUTES the 3+7+1 spectral signature by filling product-structure gaps with its decimation eigenvalues. Smooth `T³ × T⁷ × S¹` carries the *cleanest* tower fingerprint; the MFO §IV-preferred fractal substrate *obscures* it.
- **RNG bonus 6:** Brusselator's raw-LSB extraction (NO SHA-256) destroys the Kepler-shape integer-harmonic signature by itself. DFT peak-to-floor ratio: trajectory `u(t) = 18,600`, after LSB extraction `= 3.99` (slightly *below* urandom's 4.20). A **~4,660× collapse**. The chaotic-substrate floating-point-precision-amplification at extraction step flattens the Phase 9.2 / Phase 15 integer-harmonic signature. SHA-256 windowing is engineered margin on top of an already-mostly-flat distribution.

**Same shape of finding:** the substrate's *own* internal structure (fractal decimation eigenvalues / floating-point precision amplification) destroys the upstream spectral signature you might hope to read off. This is a structural prediction the bonus series surfaced: *if you want clean spectral signature of structure-X to survive into a substrate's observable output, you need the substrate's internal dynamics to NOT have its own competing-spectrum machinery.*

Stated as a working hypothesis for future spikes: **Class L spectral signatures are substrate-internally-dilutable. Reading them off downstream-observable signals requires either a substrate whose internal dynamics don't compete, OR an extraction step engineered to bypass the substrate's competing-spectrum machinery.**

This is genuinely cumulative: neither MFO nor RNG would have noticed this without the other.

### 3. The three-question framework transfers across domains

The SHA-256 inquiry (bonus 3) introduced a three-question decomposition for co-emergent two-level temporal computational systems:

1. **What is the trail made of?** (operators whose composition constitutes the output)
2. **Where is it backward-readable in isolation?** (components that survive composition)
3. **Where is it unreadable?** (the trail-erasing step that establishes the co-emergent ontology)

Transfer record:

- **SHA-256** (origin): trail = 64 rounds (XOR + ADD-mod-2³² + ROL); backward-readable = schedule recursion (invertible in ℤ/2³²) + round bijectivity; trail-erasing = `state += compress(state, block)` (768→256 bits; 512 bits become spatially-absent fiber).
- **NN-output** (direct transfer): trail = affine + ReLU + softmax + argmax; backward-readable = chain-rule gradients + affine invertibility + softmax-up-to-constant; trail-erasing = **ReLU per layer** (negative pre-activations collapse to 0).
- **MFO space-gauge-time** (adapted for ontological inquiry): structure = product-manifold per MFO §IV.4; spectrally readable = multiplicity-profile carries factor-structure signature; unreadable = Weyl-law coarse statistics.
- **RNG** (direct transfer): trail = state-update operator sequence; backward-readable varies per construction; trail-erasing = HMAC reseeding / LSB extraction (or absent in LFSR, hence non-CSPRNG).

The framework is **substrate-agnostic at the algebraic level; substrate-specific machinery handles operational details.** This is itself a finding: the right cognitive tool for analyzing co-emergent computational structure is the three-question decomposition; the specific operators / observables / erasure steps depend on substrate.

## Canonical tagline (per `[[project_space_gauge_time_framework]]`)

```
The 14 primitive classes (A–N) govern
  ⤷ spatial modes        (3D_s)
  ⤷ gauge interactions   (7D_g)
  ⤷ the temporal crank   (1D_t)
            ─────────────────────────
            3D_s + 7D_g + 1D_t = 11D
                  ≡ 1D (compressed)
  12/14 cross-dimensional · 2/14 digital-only (A: content-addressing, F: templating)
```

## Cumulative cross-substrate audit (where each bonus instantiates Spike #24 classes)

| Class | vdW | Tactical | SHA-256 | NN | MFO 3+7+1 | RNG | Status |
|:-:|:-:|:-:|:-:|:-:|:-:|:-:|---|
| A content-addressing | — | — | ✓ | — | digital-only | ✓ | Confirmed digital-substrate-only |
| B tagged-tuple | — | ✓ | ✓ | ✓ | ✓ | ✓ | Universal |
| C iterator/streaming | — | ✓ | ✓ | ✓ | ✓ | ✓ | Universal |
| D late-binding/dispatch | — | **✓** | ✓ | ✓ | ✓ | ✓ | The "dispatch" primitive that unified bonuses 2+4+6 |
| E catalog/naming | — | ✓ | — | ✓ | ✓ | — | Mostly universal |
| F substitution/templating | — | — | — | — | digital-only | — | Confirmed digital-substrate-only |
| G discovery/search | — | ✓ | — | — | ✓ | — | Project-internal |
| H self-introspection | — | ✓ | ✓ | ✓ | ✓ | ✓ | Universal |
| I cyclic-group/modular arith | — | ✓ | ✓ | — | ✓ | ✓ | Universal |
| J prime-factorisation/period | — | — | ✓ | — | ✓ | ✓ | Cross-substrate (6 native instantiations per Phase 9.6) |
| K equation-of-centre/pin-slot | — | — | ✓ | — | ✓ | ✓ | 4-substrate confirmation (Phase 9.2, 6.1, 15) |
| L graph-Laplacian | **✓** | **✓** | **✓** | **✓** | **✓** | **✓** | **Most-instantiated; the structural workhorse** |
| M HDC bind/bundle/permute | — | — | — | ✓ | ✓ | — | Distributed-representation primitive |
| N rational-approximation | — | — | — | — | — | — | (Mode-specific; not surfaced this series) |

Key reading: **Class L is the structural workhorse** of the bonus series — every one of six bonuses instantiates it. Class D dispatch unifies the choice-instantiating bonuses (tactical-choice + NN classifier + RNG output). Classes A and F are confirmed digital-substrate-only by MFO bonus 5.

## Three fermatas for conductor

1. **MFO-notebook landing (now scoped):** the bonus 5 finding lands in MFO §VIII.6 (Convergent Independent Results) — the space-gauge-time spectral signature is a convergent positive result, structurally a peer of §VIII.1 (topological defect hierarchy) and §VIII.4 (Ibarra-Vempati fractal flavor physics). The smooth-vs-fractal independent-discriminability finding sharpens MFO §XIII.1.
2. **Class O substrate-external entropy** (RNG fermata): defer. Quantum measurement + thermal noise are external-to-vocabulary substrates; can stay as boundary readings without a Class O label unless future project work needs the explicit class.
3. **Substrate-internal-dilution cumulative pattern:** record in srmech §3.8 as a sub-finding from the bonus series; cross-reference from this synthesis note. The two-substrate independent surfacing (MFO fractal + RNG Brusselator LSB) is the load-bearing evidence.

## Status of Spike #24 PR

- **Phases 1–15** complete (committed earlier in the PR).
- **Six bonus inquiries** complete; this note is the cumulative synthesis.
- **Memory** captures: `project_space_gauge_time_framework`, `feedback_antiquity_not_greek` (cross-linked).
- **Notebook updates** landing alongside this synthesis: MFO §VIII.6 + §IX status note; chess-spectral chess-opening findings; srmech §3.8 cross-reference to this synthesis.

PR #421 is ready for review/merge per `[[feedback_no_squash_merges]]` — use `gh pr merge --merge` (preferred) or `--rebase`; never `--squash`.

## Cross-references

- `[[project_space_gauge_time_framework]]` — canonical framework name + notation + tagline.
- `[[feedback_antiquity_not_greek]]` — methodological discriminator (modern physics in antiquity-geocentric position).
- `[[user_stance_kepler_shape_universal]]` — driving stance behind Spike #24.
- `[[user_stance_string_theory_instrument_first]]` — vocabulary-consolidates pattern aligned (no new dimensions invented).
- `[[user_stance_fiber_as_spatially_absent_encoding]]` — Reading B operationalisation in MFO bonus 5.
- `[[user_stance_time_as_dimensional_shadow]]` — the "temporal crank" language.
- `[[user_stance_pi_as_projection]]` — asymmetry honoured throughout.
- `[[feedback_trauma_informed_defensive_scope]]` — discipline preserved across all bonuses.
- `[[feedback_ndjson_over_bloated_json]]` — tabular output discipline.
- Spike #24 Phase 13 §3.8 — the canonical landing of Phases 1–12.
- Spike #24 Phase 15 + cross-comparison — chemistry-dynamics oscillator expansion (Phase 9.2 + 15).
- Six bonus synthesis docs in `docs/srmech/notes/spike_24_bonus_*.md`.
