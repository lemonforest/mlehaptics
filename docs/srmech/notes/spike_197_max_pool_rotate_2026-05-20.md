# Spike #197 — MAX-pool of (v, rotate(v)) empirical projection signature

**Date:** 2026-05-20
**Branch:** `research/spike-197-max-pool-rotate-fiber-projection`
**Status:** DISSOLVE (empirical evidence + stance-refinement-already-banked)
**Companion stance:** `[[user_stance_fiber_as_spatially_absent_encoding]]` (three-mechanism subsection, 2026-05-20)
**Anchor spikes:** #194 (rotation FFT bit-exact), #195 (bundle-of-views +3.7%), #196 (wet-net A∘C∘M)
**Composition stance:** `[[user_stance_rotation_is_class_k_pin_slot]]` (rotation IS Class K)

---

## Origin

User direction 2026-05-20, after refining the wet-net rotate framing
through three iterations (rotate-then-permute → bit-exact-under-twist
→ MAX-pool of rotated views):

> "my thinking was that it rotates a state out of bit exact and into
> fiber space and couples with bit exact as well, even if it's just
> mathematically, like we do. not summed but like max values of bit
> exact and rotated"

The user's framing distinguishes three operations on rotated views,
all of which are now empirically characterised across the spike series:

1. **Bind** (Class M XOR rotation) — bit-exact preservation
   (Spike #196 0-bit recovery; Spike #194 DFT shift theorem 1.42e-13)
2. **Bundle** (Class M majority across views) — lossy projection
   (Spike #195 +3.7% bundle-loss signature)
3. **MAX-pool of (v, rotate(v))** ← THIS SPIKE — per-position selection
   between bit-exact and rotated views

H1: MAX-pool IS a Class K projection that surfaces substrate fiber
content into visible cross-bin coupling; projection signature differs
from both bind and bundle; cross-substrate coupling carries substrate-
specific structural signature.

H0: MAX-pool is indistinguishable from bundle (or noise) at the
cross-bin coupling level; projection signature is generic.

---

## Methodology

7-cell research script (`spike197_max_pool_rotate_fiber_projection.py`).
5 substrates × 3 stride classes; all D=8192 BSC. Open-access citations
only per `[[feedback_paywalled_doi_cannot_be_attested]]`.

| Cell | Test |
| ---- | ---- |
| 1 | Per-substrate MAX-pool computation across 3 stride classes |
| 2 | Three-way projection-signature comparison (bind vs bundle vs MAX-pool) |
| 3 | Cross-substrate signature stability (CV summary, pairwise Frobenius distances) |
| 4 | Fiber-content reveal test (residual M_max − M_plain vs M_rotated − M_plain) |
| 5 | Wet-net NN-invariance test (8 distinct strides; activity-rate model validation) |
| 6 | Three-way composition table (Spike #195 + #196 + #197) |
| 7 | DISSOLVE / PROMOTE / DEFER verdict |

Substrates:
- `synthetic_random_bsc` (control)
- `wet_net_shape` (7.5% sparsity per Spike #196 cortical-pyramidal regime)
- `dna_helical_pitch` (B/A/Z strides per Spike #172)
- `chess_natural_stride` ({5, 7, −8} per Spike #173)
- `ephemerides_rbs_hdc` (SHA-keyed strides per Spike #194)

---

## Key findings

### Cell 2 — Three-way projection-signature comparison

| Substrate | Bind err % | Bundle err % | MAX-pool cos→v | d(max,bundle) | d(max,bind) |
| --------- | ---------- | ------------ | -------------- | ------------- | ----------- |
| synthetic_random_bsc | 0.000 | 0.241 | 0.509 | 0.997 | 1.000 |
| wet_net_shape | 0.000 | 0.071 | 0.861 | 0.846 | 0.057 |
| dna_helical_pitch | 0.000 | 0.252 | 0.499 | 0.993 | 0.997 |
| chess_natural_stride | 0.000 | 0.245 | 0.505 | 0.987 | 0.998 |
| ephemerides_rbs_hdc | 0.000 | 0.247 | 0.504 | 1.007 | 1.007 |

Confirms the three-mechanism asymmetry:
- **Bind** PRESERVES bit-exact (0% recovery error across all substrates).
- **Bundle** PROJECTS with ~24% recovery error in random-baseline regime;
  wet-net's 7.1% reflects sparse-substrate inclusion-exclusion effect.
- **MAX-pool** has a coupling-matrix distance from bundle near 1.0 and
  from bind near 1.0 for random-shape substrates — i.e. **MAX-pool
  produces a projection signature SEPARATE from both bind and bundle**.
- Wet-net exception is striking: `d(max, bind) = 0.057` (MAX-pool and
  bind coupling matrices align) — because sparse {+1} bits dominate in
  both operations under low active-bit fraction.

### Cell 3 — Cross-substrate signature stability

- **MAX-pool coupling-matrix CV across substrates: 0.343**
- Spike #194 plain-rotation universal-coupling CV reference: 0.0031
- **Ratio: ~110×** — MAX-pool is **substrate-specific**, NOT universal.

This is exactly what H1 predicts: plain rotation is universal (DFT shift
theorem preserves magnitude spectrum); MAX-pool surfaces substrate-
fiber content, which IS substrate-specific by construction.

### Cell 4 — Fiber-content reveal test

Residual `M_max − M_plain` cross-bin off-diagonal magnitude vs
`M_rotated − M_plain` reference:

| Substrate | offdiag(M_max−M_plain) | offdiag(M_rot−M_plain) | Surfacing ratio |
| --------- | ---------------------- | ---------------------- | --------------- |
| synthetic_random_bsc | 0.253 | 0.140 | 1.81 |
| wet_net_shape | 0.215 | 0.095 | 2.25 |
| dna_helical_pitch | 0.242 | 0.080 | 3.03 |
| chess_natural_stride | 0.247 | 0.038 | **6.54** |
| ephemerides_rbs_hdc | 0.259 | 0.139 | 1.86 |

**Chess natural-stride passes the 5× surfacing threshold** for explicit
fiber-content reveal (offdiag ratio 6.54). Others surface fiber but
the ratio is more moderate (1.8–3.0). The differential ranking
substrate-by-substrate IS substrate-specific signal: chess's compact
natural strides {5, 7, −8} create cleaner per-bin selectivity than
DNA's larger {21, 11, −12} or wet-net's mixed {1024, 5, 2048}.

### Cell 5 — Wet-net NN-invariance test

- 8 distinct strides on wet-net-shaped substrate
- **MAX-pool +1 fraction observed mean: 0.1442**
- **Inclusion-exclusion model prediction: 0.1444** (i.e. `1 − (1 − 0.075)²`)
- **Math-doesn't-lie verification: 0.0002 deviation across 8 strides**
- Cross-stride pairwise similarity mean: **0.7436** (moderately invariant)

The inclusion-exclusion prediction confirms the operation is correctly
implemented at the BSC layer; the 0.74 cross-stride similarity says
MAX-pool retains a substrate-shape fingerprint across stride variation
while still being stride-sensitive — consistent with convolutional-NN
max-pooling translation-invariance literature (Boureau-Ponce-LeCun
2010; Scherer-Müller-Behnke 2010, both open-access via NYU-CILVR /
Bonn / arXiv).

### Cell 7 — DISSOLVE verdict

Per `[[feedback_no_privileged_primitive_classes]]` default DISSOLVE-
before-PROMOTE:

- **Q1:** Is MAX-pool(v, rotate(v)) structurally irreducible from
  {Class K, Class C}? **NO** — it is Class K per-position projection
  across two views (one plain, one Class K-rotated). Composable.
- **Q2:** Does it produce a signature distinct from bind / bundle?
  **YES** — Cell 2 coupling distances:
  - mean d(max-pool, bundle) = **0.9658**
  - mean d(max-pool, bind) = **0.8116**
- **Disposition:** DISSOLVE — extend existing
  `[[user_stance_fiber_as_spatially_absent_encoding]]` three-mechanism
  subsection (already done 2026-05-20) with empirical evidence from
  this spike. **No new canonical stance file; no new primitive class.**

---

## Composition with framework

### `[[user_stance_fiber_as_spatially_absent_encoding]]` three-mechanism subsection

The stance file already recorded the user's articulation 2026-05-20:

> Bind preserves but doesn't project (fiber stays spatially-absent);
> bundle projects but the projection signature is the operation's own
> averaging; **MAX-pool IS the canonical projection that surfaces
> substrate fiber content into visible cross-bin coupling without
> lossy averaging**.

Spike #197 confirms this asymmetry empirically:

1. **Bind**: 0% recovery error (Cell 2) — preserves bit-exact substrate.
2. **Bundle**: ~24% recovery error (Cell 2) — lossy projection.
3. **MAX-pool**: CV=0.343 cross-substrate (Cell 3); separable from bind
   and bundle in coupling space (Cell 2, distances ~0.97 / 0.81); chess
   surfaces fiber at 6.54× ratio (Cell 4); wet-net NN-invariance
   pattern at math-ε accuracy (Cell 5).

The three-mechanism subsection is now reinforced as empirically grounded
across the bind / bundle / MAX-pool axis, with Spike #194 (bind),
#195 (bundle), #196 (wet-net A∘C∘M bind direction), and now #197
(MAX-pool) as four anchored spikes spanning the asymmetry.

### `[[user_stance_rotation_is_class_k_pin_slot]]`

MAX-pool of (v, rotate(v)) IS Class K applied per-position across two
views. Same Class K identity as plain rotation (Spike #176); the
2-view input topology distinguishes MAX-pool from single-view Class K
operations like `srmech.spectral.truncate_sparse` (magnitude-band
keep-top-k).

### `[[user_stance_form_function_rotation_is_a_c_m_composition]]`

`form_function_rotate` (A∘C∘M cascade) IS the bind direction. MAX-pool
is a DIFFERENT cascade composition: it uses Class K twice
(rotate + per-position-max) but does NOT include Class M bind. So the
three mechanisms span THREE structurally distinct cascade compositions
over the same 14-class vocabulary, all reusing Class C / Class K /
Class M primitives in different arrangements. No new class needed
across all three.

### `[[user_stance_cascade_length_is_substrate_time_scale_coupling]]`

Cascade lengths:
- Bind A∘C∘M: 3-class short cascade
- Bundle (M-extended): 3-class with multi-view
- MAX-pool (K∘K per-position): 2-class compositional

Cascade-length tracks operation timescale per the stance — wet-net
biology: bind ~ms (synaptic), MAX-pool ~100ms (NMDA-spike compartment-
alization), bundle ~longer-window population-readout.

---

## Open-access citations used

- Boureau, Y.-L., Ponce, J. & LeCun, Y. (2010). "A theoretical analysis
  of feature pooling in visual recognition." ICML. Open-access at NYU
  CILVR archive: `https://cs.nyu.edu/~yann/research/pooling/index.html`.
- Scherer, D., Müller, A. & Behnke, S. (2010). "Evaluation of pooling
  operations in convolutional architectures." ICANN. Open-access via
  the authors' Bonn page.
- Larkum, M.E. (2013). PMC4051148 (open-access manuscript copy) — wet-net
  NMDA-spike compartmentalization analog for MAX-pool-like winner-take-
  all per dendritic compartment.

---

## Limits / not-tested

- Magnitude-spectrum MAX-pool (FFT magnitude) variant not run — Cell 1
  ran on BSC bipolar; complex-spectrum extension is a follow-up.
- Only one wet-net sparsity (7.5%) tested. Spike #196's 6-variant
  sparsity sweep (2%–30%) would also be informative for MAX-pool but
  not required for this DISSOLVE verdict.
- Cell 4's "surfacing ratio" 5× threshold was a hand-picked criterion;
  chess passes cleanly, others surface at 1.8–3.0× which is real signal
  but below the threshold. Threshold-calibration left as fermata.
- MAX-pool of magnitude spectra (not BSC values directly) — a complex-
  valued MAX variant — left as candidate Spike #198 if user calls for
  it (different invariance regime, more native to convolutional-NN
  practice).

---

## Fermatas

1. **Chess's outlier 6.54× surfacing** — Why does chess natural-stride
   produce a sharper fiber-reveal than DNA or wet-net? Hypothesis: chess
   strides {5, 7, −8} are small + co-prime, producing maximal per-bin
   selectivity; DNA {21, 11, −12} and ephemerides {257, 4099, −1031}
   create more overlap between original and rotated views. A follow-up
   spike could parameterise the surfacing ratio as a function of
   gcd(stride, D) and stride-magnitude.

2. **MAX-pool ≈ bind on sparse substrate** — Cell 2 row `wet_net_shape`:
   `d(max-pool, bind) = 0.057`. At sparsity 7.5%, MAX-pool's coupling
   matrix is near-identical to bind's. This is mathematically expected
   (sparse {+1} bits dominate both operations) but worth recording: at
   sparse regimes the three-mechanism asymmetry partially collapses.
   For cortical-pyramidal-cell-realistic sparsity (5–10%), bind and
   MAX-pool may be near-interchangeable in their projection footprint
   — distinguishable only by the recovery-error axis (bind 0%, MAX-pool
   information-destroying).

3. **D=8192 lock** — At smaller D the per-bin selectivity may shift the
   substrate-specific signature CV. Conductor decision #6 locks D=8192
   for Phase 1; relaxing it would re-run Cell 3 across D∈{512, 2048,
   8192, 32768} to characterise scale-dependence.

---

## Recommended next steps

1. **DO NOT MERGE PR AUTONOMOUSLY** (per spike-dispatch instructions
   composing with fiber-spatially-absent stance refinement scope).
2. **Stance file update review** — confirm the existing 2026-05-20
   three-mechanism subsection in `user_stance_fiber_as_spatially_absent_encoding.md`
   adequately captures the empirical evidence; if not, augment.
3. **Spike #198 candidate**: complex-magnitude MAX-pool variant
   (FFT-magnitude space) — different invariance regime more native to
   convolutional-NN practice. Optional.
4. **Spike #199 candidate**: surfacing-ratio parameterisation as
   `f(gcd(stride, D), |stride|, substrate)` — explains chess's outlier
   per Fermata #1. Optional.

---

## Computational provenance

- Script: `docs/srmech/notes/spike197_max_pool_rotate_fiber_projection.py`
- Output: `docs/srmech/notes/spike197_findings_2026-05-20.ndjson`
- Seed: 20260520 (deterministic)
- D=8192 BSC bipolar substrate per conductor decision #6
- 29 NDJSON records across 7 cells

---

## Discipline checklist

- [x] 14 A-N intact; no class promotion
- [x] Identity-not-implementation (MAX-pool IS Class K per-position;
      not a new class)
- [x] Asymptotic-ring vocabulary (cyclic shift on Z/D; no math.pi)
- [x] Computational provenance committed (script + seed + NDJSON)
- [x] Open-access citations only (NYU CILVR / Bonn / PMC4051148)
- [x] NDJSON output format
- [x] Trauma-informed defensive scope (structural neuroscience research only)
- [x] No `--no-verify`; no `--squash`
- [x] DISSOLVE-before-PROMOTE default applied
