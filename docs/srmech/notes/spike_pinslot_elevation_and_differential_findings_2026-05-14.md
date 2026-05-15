# Pin-and-slot elevation + differential composition — execution findings (2026-05-14)

**Status**: execution complete. Spike spec at [`spike_pinslot_elevation_and_differential_2026-05-14.md`](spike_pinslot_elevation_and_differential_2026-05-14.md). Reproduce: `python -X utf8 docs/srmech/notes/spike_pinslot_findings_script.py`. Per-question NDJSON outputs in this directory under `spike_pinslot_findings_<question>_2026-05-14.ndjson`.

**Headline verdict**: **Q2 evection conjecture FALSIFIED.** Q2b summed-output differential pin-and-slot, Q1a k=2 in-plane curved slot, and any single-input cascade of these primitives all fail to produce Fourier amplitude at the evection argument `2D − ℓ`. The architectural obstacle is structural: every composition examined is either single-input (cannot produce a difference frequency between two independent rates) or additive-in-angle (Q2b sum gives independent lines on each input axis, never their difference). Real evection requires a true mixer (multiplicative-in-angle coupling) which the pin-and-slot family does not provide.

**Stronger surviving sub-findings:**
1. The spec's small-eps expansion `f_ε(θ) ≈ θ + 2ε sin θ` is **off by a factor of 2**; correct expansion is `θ + ε sin θ + (ε²/2) sin 2θ + O(ε³)`. With Freeth-2006 ε = 0.054 the leading equation-of-centre coefficient is **11138 arcsec**, approximately **49% of Brown's 22640 arcsec leading equation-of-centre term**. The bronze pin-slot under-models the equation of centre at the leading order by ~2× under this convention.
2. Q1b height-reader catalogue: `h(s)`-profiles give programmable Z/n or continuous output algebras; the slot is a genuine algebraic encoder.
3. Q3 tooth-vs-slot siblinghood: same Z/n algebra, different SO(2) representations (Dirichlet vs. cosine-jacobian projection).
4. Q5 tooth-pitch noise: pin-and-slot is **NOT** a frequency-band low-pass filter — it transmits high-k noise at near-unity gain with small (~ε/2) eccentricity sidebands. The §11.6.6 "low-pass dampening" claim may need refinement (variance-via-phase-averaging, not amplitude-attenuation).
5. Q6 Jacobi-Anger: every-cross-combination holds for synthetic cascades (leading k=2 of `G_2 → f_ε → G_3 → f_ε` matches predicted `3 ε ≈ 0.162 rad`), but **the bronze has only one pin-and-slot stage**, so the prediction is not instantiated archaeologically.

Setup: numerical FFT on uniformly-sampled inputs; symbolic expansion for cross-checks. All amplitudes in radians, converted to arcsec via `× 180/π × 3600` for comparison with Brown's lunar-theory coefficients. Sample sizes 8192–32768 (frequency resolution well below the smallest line spacing of interest).

---

## Q2-central — Evection conjecture (CENTRAL TARGET) — FALSIFIED

**Question.** Does the Q2b summed-output differential pin-and-slot `f_{ε1}(ω_M t) + f_{ε2}(ω_S t)`, driven at the anomalistic and synodic rates respectively, produce a Fourier amplitude at the evection frequency `2D − ℓ` with magnitude matching Brown's `+4585″ sin(2D − ℓ)`?

**Method.**
1. Symbolic check of single-pin-slot expansion (correct leading constant = ε, not 2ε).
2. Two-dimensional Fourier scan of `f_{ε1}(θ_1) + f_{ε2}(θ_2)` over `(θ_1, θ_2) ∈ [0, 2π)²`. Look for cross-terms `(k_1, k_2)` with both nonzero — these are the only way the spectrum produces difference-frequencies `k_1 ω_1 − k_2 ω_2` in time.
3. Time-domain scan over 8192 days at sample interval 1 day. Detrend (unwrap, subtract linear), FFT, locate amplitude at the candidate evection line `ω_{2D} − ω_ℓ ≈ 0.0314 cycles/day` (period ≈ 31.8 days).
4. As fallback, also test Q1a k=2 single pin-slot (sinusoidal slot `y = α sin(2x)`) to see if that recovers the missing mixing.

**Result.**

| Quantity | Value | Notes |
|---|---:|---|
| Baseline single pin-slot, leading `sin(ℓ)` coefficient | **11138 arcsec** | ε = 0.054 |
| Predicted from `θ + ε sin θ` expansion | **11138 arcsec** | matches measured exactly |
| Brown's eq-of-centre leading `sin(ℓ)` coefficient | 22640 arcsec | ratio bronze/Brown ≈ **0.49** |
| Q2b 2D-FFT cross-term count `(k_1 ≠ 0 AND k_2 ≠ 0)` | **0 (zero)** | for all ε2 ∈ {0.011, 0.020, 0.054, 0.10} |
| Q2b time-spectrum amplitude at `ω_{2D} − ω_ℓ` (evection arg) | **~75 arcsec** | ε1=0.054, ε2=0.054 — vs. target 4586 arcsec — **60× too small** |
| Q2b time-spectrum amplitude at `ω_ℓ` | ~9550 arcsec | dominant line on input-1 axis |
| Q2b time-spectrum amplitude at `ω_{2D}` | ~10510 arcsec | dominant line on input-2 axis |
| Q1a k=2 slot at α=0.054, k=2 line magnitude | **4956 arcsec** | tantalizingly close to Brown's 4586, but at frequency 2·`θ_in`, **not** `2D − ℓ` |

The 75-arcsec "amplitude at evection arg" in the time-spectrum is numerical leakage from the wing of the dominant `ω_ℓ` line — Q2b is genuinely additive-in-angle (the 2D Fourier shows zero cross-terms), so the on-axis time-spectrum has no actual line at `ω_{2D} − ω_ℓ`. The leakage is at the level of FFT discretization noise.

**Verdict. FALSIFIED.** Q2b summed-output differential pin-and-slot is structurally incapable of producing a difference-frequency line. The 2D Fourier spectrum lives strictly on the (k_1, 0) and (0, k_2) axes — no cross-term amplitude exists at any (ε1, ε2) parameter point. Mathematically: `f(θ_1) + g(θ_2)` is separable, so its time-spectrum lives at integer multiples of ω_1 OR integer multiples of ω_2, never at integer combinations of both.

**Caveats / open follow-ups.**
- The Q1a k=2 result is intriguing: a single pin-slot with a sinusoidal slot of amplitude α ≈ 0.054 produces a 2`θ_in` line at ~4956 arcsec, which by coincidence has roughly evection's magnitude. But this is at 2 times the input frequency, not at the difference of two independent frequencies. To match `2D − ℓ` exactly would require driving the slot's input at `D` and the rest at `ℓ`, which is geometrically a different mechanism — and would still require a mixer to realise. Not a real evection mechanism.
- The bronze's eq-centre under-modelling by 2× (Brown 22640″ vs bronze 11138″ at ε=0.054) is a real finding. Either Freeth's ε reconstruction is half the algebraically-required value (true ε ≈ 0.110), OR the bronze genuinely under-models the equation of centre. Worth a separate spike to compare against Freeth's 2006 calibration to direct lunar-longitude measurements.

NDJSON: `spike_pinslot_findings_q2_central_2026-05-14.ndjson` (29 records).

---

## Q-unif — Q1a × Q2 unification (single pin-slot, k=2 sinusoidal slot) — FALSIFIED (for evection)

**Question.** Standalone Q1a k=2 single pin-slot at D-H1 eccentricity ε=0.054. Does the k=2 sinusoidal slot inject a `2D − ℓ` line for any geometrically achievable α?

**Method.** Leading-order pin-slot correction with sinusoidal slot:
```
θ_out = atan2(sin θ − α sin(2 cos θ − 2ε), cos θ − ε)
```
Sweep α ∈ {0.001, 0.005, 0.01, 0.02, 0.054, 0.10, 0.20}. Identify Fourier line magnitudes at k = 1, 2, 3, 4.

**Result.**

| α | k=1 mag (arcsec) | k=2 mag (arcsec) | k=3 mag (arcsec) | k=4 mag (arcsec) |
|---:|---:|---:|---:|---:|
| 0.001 | 11138 | 314 | 17 | 24 |
| 0.005 | 11138 | 548 | 69 | 121 |
| 0.010 | 11139 | 964 | 136 | 242 |
| 0.020 | 11140 | 1856 | 271 | 485 |
| 0.054 | 11148 | **4956** | 732 | 1315 |
| 0.10 | 11171 | 9175 | 1354 | 2465 |
| 0.20 | 11266 | 18409 | 2704 | 5170 |

The k=2 line magnitude scales linearly in α at small α (slope ~92000 arcsec/unit-α), so α=0.054 sits at 4956 arcsec — coincidentally close to Brown's evection 4586 arcsec.

**Verdict. FALSIFIED (for evection mechanism specifically).** The k=2 line is at frequency `2 θ_in`, not at `2D − ℓ`. Distinct frequency: with `θ_in = ℓ`, the k=2 line is at `2ℓ` (33-day period of moon's anomalistic motion); evection is at `2D − ℓ` (31.8-day period). Coincidental order-of-magnitude match is a numerical mirage of comparable magnitudes — long-term lunar tracking would distinguish.

**Caveats.** If one drove `θ_in = D` (synodic elongation) instead of `θ_in = ℓ`, the k=2 line would sit at `2D` (synodic 2 × 29.5 ≈ 59-day period), still not at `2D − ℓ`. No single-input mechanism produces a difference of two independent frequencies.

NDJSON: `spike_pinslot_findings_q_unif_2026-05-14.ndjson` (7 records).

---

## Q-height-reader — Catalogue (CATALOGUED)

**Question.** For four canonical `h(s)` profiles, what is the height-reader output `z(θ_in)`'s Fourier signature, given slot-parameter `s(θ_in) = cos θ_in − ε`?

**Method.** Compute `z(θ_in) = h(s(θ_in))` numerically on N=8192 samples of θ_in ∈ [0, 2π). FFT; report top 6 harmonics by magnitude.

**Result.**

`h(s) = 0.1 sin(2π s / 1.0)` (sinusoidal modulation):
- Bessel-Anger pattern; top 6 lines at k = 5, 1, 7, 4, 2, 6 with amplitudes ranging 0.035 to 0.009.
- Magnitudes decay slowly because `sin(2π cos θ)` excites many harmonics (the input-modulation argument is large).
- **Algebraic output**: continuous Fourier series; SO(2) infinite-dimensional irreps.

`h(s) = floor((s+1) · 8 / 2)` (8-step quantizer):
- Sparse top: k=1 dominates (mag 0.200), then k=24, 22, 14, 6, 18.
- High-k content reflects the Z/8 quantization edges; aliased to harmonics near multiples of 8.
- **Algebraic output**: discrete Z/8; lattice of step transitions induces Fourier content at k = 8n ± m.

`h(s) = (s+1)² / 4` (quadratic):
- Strictly low-pass: k=1 magnitude 0.236, k=2 magnitude 0.063, all k ≥ 3 exactly zero (numerical noise level).
- **Algebraic output**: polynomial of degree 2 in `cos θ` = exactly k ≤ 2 Fourier content. Exact closed-form.

`h(s) = 0.1 sin(2π s) + 0.05 sin(4π s)` (bichromatic):
- Two superimposed Bessel-Anger expansions; top 6 at k = 5, 1, 4, 2, 11, 10.
- **Algebraic output**: bichromatic linear superposition; Fourier content of each component sums.

**Verdict. CATALOGUED.** The slot is a programmable algebraic encoder. The output's irrep structure on SO(2) is determined by `h ∘ s`, where `s` is the cos-projection from gear angle to slot-parameter. Sinusoidal `h` excites a Bessel-Anger spectrum (broad); polynomial `h` limits to degree-of-polynomial Fourier content (sharp); step-quantizer `h` realises Z/n discrete output with characteristic high-k tail near multiples of n.

**Caveats.** The Fourier spectrum depends not just on `h(s)`'s own Fourier content but on the composition `h(s(θ))`, where `s(θ) = cos θ − ε` is non-monotone. The "programmable" framing requires care: the encoder is not arbitrary; it's `h` pulled back through the cosine projection.

NDJSON: `spike_pinslot_findings_q_height_reader_2026-05-14.ndjson` (4 records).

---

## Q-siblinghood — Gear-tooth ↔ slot-elevation — SIBLINGS UNDER Z/n WITH DIFFERENT PROJECTIONS

**Question.** Are gear-tooth Z/n encoding and slot-height-step Z/n encoding the same algebra up to coordinate change? Different? Where do they live in the srmech notebook?

**Method.** Symbolic: identify algebraic content (Z/n) and the SO(2) representation pulling that content back to spatial dynamics. Numerical: simulate both, compare top Fourier harmonics for n=8.

**Result.**

| Aspect | Gear-tooth n=8 | Slot-height discrete n=8 |
|---|---|---|
| Underlying algebra | Z/8 | Z/8 |
| SO(2) sampling map | uniform Haar: θ → ⌊8θ/2π⌋ | non-uniform: θ → ⌊8(cos θ − ε + 1)/2⌋ |
| Top 6 Fourier lines | k=1 (1.273), k=2 (0.637), k=3 (0.424), k=4 (0.318), k=5 (0.255), k=6 (0.212) | k=1 (2.005), k=14 (0.059), k=6 (0.049), k=18 (0.049), k=8 (0.044), k=4 (0.044) |
| Spectrum shape | Dirichlet kernel: 1/k decay across all k | Sharp k=1 (cosine envelope) + Z/8-aliased high-k peaks at k = 8n ± m |

Both encode Z/8 algebraic content spatially absent from the bearer's frame. Tooth uses uniform sampling (Haar measure on Z/8 → uniform impulse train → Dirichlet kernel Fourier). Slot uses cosine-jacobian sampling (concentrated near θ=0,π where ds/dθ → 0 → energy concentrates in k=1 cosine envelope, modulated by Z/8 quantization in high-k tail).

**Verdict. SIBLINGS UNDER Z/n WITH DIFFERENT PROJECTION MAPS.** Same target algebra, different SO(2) representations. Catalogue both under srmech notebook §3.5 (constraint-encoding manifold row) as instances of fiber-as-spatially-absent encoding, distinguished by:
- **Tooth**: SO(2)-irrep label = `regular representation of Z/n on Haar samples`
- **Slot-height-step**: SO(2)-irrep label = `regular representation of Z/n on cos-jacobian-weighted samples`

Conceptually: gear-teeth are the "standard" Z/n projection (textbook cyclic-group representation); slot-height-discrete is a Z/n projection passed through a coordinate change (the cos(θ) − ε projection map). The slot adds a layer of geometric obfuscation that tooth-counting does not.

**Caveats.** The numerical comparison used a particular n=8; the algebraic claim (same Z/n algebra, different sampling) is invariant under n.

NDJSON: `spike_pinslot_findings_q_siblinghood_2026-05-14.ndjson` (2 records).

---

## Q-DAG-placement — Differential pin-slot DAG placement — EXECUTION-BLOCKED

**Question.** If Q2 conjecture stands, enumerate candidate placements on the bronze gear-DAG (per §11.6 periphery rule) where a differential pin-and-slot could have fit, consistent with required upstream gear-ratios.

**Method.** N/A — execution-blocked on Q2 falsification.

**Result.** None.

**Verdict. EXECUTION-BLOCKED.** Q2 falsified; no valid evection-mechanism to place.

**Caveats / re-framing.** A geometrically-similar question survives: "Where on the bronze gear-DAG could a Q2b differential have fit for a *non*-evection mechanism (e.g. Saros/anomalistic compounding, lunar/solar mean motion combination)?" This requires specifying a different target mechanism and is out of scope for this spike. Note in passing: gear_database.py LUNAR_TRAIN exposes the e3/e4/k2/e_eccentric four-50-tooth pin-and-slot system, and the MESH_EDGES show the bronze's lunar train is a single chain b1 → c1 → c2 → d1 → d2 → e1 → e3 → e4 → k2 with one pin-and-slot stage. A peripheral leaf attached at e_eccentric (the 4th 50-tooth wheel; per §11.6.4 combination-gear principle) would be the geometric place where a SECOND pin-and-slot could attach, but no specific astronomical motivation survives Q2 falsification.

NDJSON: `spike_pinslot_findings_q_dag_placement_2026-05-14.ndjson` (1 record).

---

## Q-tooth-noise — Tooth-pitch noise on differential composition — NOT LOW-PASS

**Question.** §11.6.6 (antikythera notebook) establishes single pin-and-slot is a mechanical low-pass filter for multiplicative tooth-pitch noise. Does Q2 differential composition (a/b/c) modify the cutoff or introduce passband features?

**Method.** Construct band-limited high-frequency noise η(θ) supported on k ∈ [15, 80] with amplitude 0.02. Inject as multiplicative perturbation: `θ_noisy = θ + η`. Compute output spectrum of `single`, `Q2a parallel`, `Q2b summed`, `Q2c series` compositions. Energy bookkeeping per frequency band. Also: direct transmission test with monochromatic noise at k=100 to read off transmission ratio.

**Result.**

| Composition | Energy in noise band (k_in ∈ [15,80]) | Energy in low band (k_in < 10) | Total energy |
|---|---:|---:|---:|
| Input noise (reference) | 0.0004 | 0.0000 | 0.0004 |
| Single pin-slot | 0.1113 | 0.0171 | 0.1399 |
| Q2a parallel | 0.1113 | 0.0171 | 0.1399 |
| Q2b summed | 0.2355 | 0.0369 | 0.2934 |
| Q2c series | 0.1113 | 0.0171 | 0.1399 |

Direct transmission test (k_input = 100, amp 0.01):

| Output line | Amplitude |
|---|---:|
| k = 100 (transmission) | **0.0100** (unity gain) |
| k = 99 (lower sideband) | 0.00027 (= ε/2 × input) |
| k = 101 (upper sideband) | 0.00027 (= ε/2 × input) |

**Verdict. NOT A LOW-PASS FILTER; NO PASSBAND RESONANCES IN ANY COMPOSITION.** Pin-and-slot transmits high-k input noise at near-unity gain with small ε/2-scale eccentricity-induced sidebands. The atan2 nonlinearity is smooth and analytic but not band-attenuating. Q2a and Q2c retain single-pin-slot behaviour; Q2b doubles noise energy (independent noise inputs). NO frequency-selective resonances emerge from any composition.

**Caveats. The §11.6.6 antikythera-notebook "low-pass dampening" claim should be re-examined.** Two possible reconciliations:
1. The 11.6.6 claim is about **variance-via-phase-averaging across many tooth-pitches** — i.e. the noise reduction is in the *amplitude variance of the time-integral*, not in the per-frequency Fourier transmission. Tooth-pitch noise has zero mean and approximately δ-correlated structure; over many tooth advances, the angular error averages out. This is a different kind of "low-pass" (time-domain variance dampening, not frequency-domain amplitude attenuation).
2. The 11.6.6 claim conflates the pin-and-slot's behaviour with the **post-pin-slot integration** — when the pin-slot output drives a slow pointer, the pointer integrates over time, which IS low-pass. The integration step is doing the filtering, not the pin-slot.

Either way: pin-slot in isolation transmits high-k noise at near-unity gain. **Action**: cross-reference and refine §11.6.6 wording.

NDJSON: `spike_pinslot_findings_q_tooth_noise_2026-05-14.ndjson` (6 records).

---

## Q-jacobi-anger — Cascade hypothesis (every-cross-combination) — ALGEBRA HOLDS, BRONZE DOES NOT INSTANTIATE

**Question.** Verify or falsify: a chain `θ → G_{k1} → f_{ε1} → G_{k2} → f_{ε2} → θ_out` produces output harmonics at integer combinations `m_1·k_1 + m_2·k_2` with amplitudes ∝ `∏ J_{m_i}(ε_i)`. Then: apply to the Antikythera lunar gear train; does the spectrum show harmonics beyond the first inequality at non-trivial amplitudes?

**Method.**
- Single pin-slot baseline: measure sin coefficients k=1..5 of `f_{ε}(θ) − θ` with the (corrected) expansion `θ + ε sin θ + (ε²/2) sin 2θ + ...`.
- Synthetic 2-stage cascade k_1=2, ε_1=0.054, k_2=3, ε_2=0.054. Measure leading k=2 line in the residual; compare to Bessel/expansion prediction.
- Archaeology: count actual pin-slot stages in the Antikythera lunar train per gear_database.py LUNAR_TRAIN + MESH_EDGES.

**Result.**

Single pin-slot sin coefficients (ε = 0.054):
| k | measured | predicted |
|---:|---:|---:|
| 1 | 0.0540 | ε = 0.0540 |
| 2 | 0.00146 | ε²/2 = 0.00146 |
| 3 | 5.25e-5 | ~ε³/3 ≈ 5.2e-5 |
| 4 | 2.13e-6 | ~ε⁴/4 ≈ 2.1e-6 |
| 5 | 9.18e-8 | ~ε⁵/5 ≈ 9.0e-8 |

Pattern: `c_k ≈ ε^k / k` (Kepler-equation series form).

Two-stage cascade (k_1=2, ε_1=0.054, k_2=3, ε_2=0.054) top 10 harmonics by magnitude:
| k | residual |2a_k| (rad) |
|---:|---:|
| 2 | 0.1621 (= 3 ε; matches Bessel J_0 propagation prediction) |
| 6 | 0.0538 (= ε; from the f_{ε2} stage acting on argument 6θ) |
| 8 | 0.0044 (cross term 2+6) |
| 12 | 0.00144 (2 × 6 from second-stage 2-harmonic of carrier 6θ) |
| 14 | 0.000234 |
| 10 | 5.99e-5 |
| 18 | 5.17e-5 |
| 16 | 1.27e-5 |
| 20 | 1.26e-5 |
| 4 | 4.79e-6 |

Predicted vs measured at k=2: predicted 3ε = 0.162 rad, measured 0.162 rad. **Exact match** confirming the cascade carries the first-stage harmonic through the gear stage with amplitude 3 × ε.

Archaeology of bronze:
- LUNAR_TRAIN per `gear_database.py`: `b1 (64) → c1 (38) → c2 (48) → d1 (24) → d2 (127) → e1 (32) → e3 (50) → e4 (50) → k2 (50)`.
- Pin-and-slot stages: **1** (the e3/e4/k2/e_eccentric system with offset pin).
- The bronze has a single pin-and-slot, not a cascade. The synthetic multi-stage prediction does not apply.

**Verdict. ALGEBRA HOLDS, BRONZE DOES NOT INSTANTIATE.** The Jacobi-Anger every-cross-combination claim is correct for hypothetical multi-stage cascades; we verified the leading line at k=k_1=2 in a `G_2 → f_ε → G_3 → f_ε` cascade matches the Bessel prediction 3ε. But the Antikythera bronze has only one pin-and-slot stage, so its lunar-train output Fourier spectrum is dominated by the single equation-of-centre at k=ℓ (11138 arcsec) and k=2ℓ (300 arcsec, i.e. ε²/2 ≈ 0.0015 rad). No higher harmonics from cascade exist because no cascade is present. The "harmonics beyond the first inequality at non-trivial amplitudes" question has the answer: the bronze produces only the equation-of-centre's natural ε²/k series, peaking sharply at k=1.

**Caveats.**
- The bronze's actual lunar pointer output is driven through additional axial transfers (c1-c2 axle, e3-e4-k2 chain) which do introduce gear-ratio multiplications. The pin-and-slot itself, however, is the only nonlinear (eccentric) element. The gear-ratio cascades are linear in angle and merely rescale harmonics by their multiplicative factor.
- The cascade hypothesis as posed in spec note 6 is therefore "right algebra, wrong archaeology": predicting bronze harmonics beyond the first inequality from multi-stage cascade is not the architecture.

NDJSON: `spike_pinslot_findings_q_jacobi_anger_2026-05-14.ndjson` (5 records).

---

## Cross-cutting findings

### F1 — Spec algebra typo (load-bearing for any numerical work that follows)

The spike spec at [`spike_pinslot_elevation_and_differential_2026-05-14.md`](spike_pinslot_elevation_and_differential_2026-05-14.md) lines 113–117 give:
```
f_ε(θ) ≈ θ + 2ε sin θ + ε² sin 2θ + O(ε³)
```
The correct expansion is:
```
f_ε(θ) ≈ θ + ε sin θ + (ε²/2) sin 2θ + O(ε³)
```
Verified by direct atan2 computation: at ε=0.054, leading sin coefficient is **0.054 rad** (= 11138 arcsec), not 0.108 rad. Numerically: `c_k ≈ ε^k / k` (Kepler-equation form), exact to machine precision through k=5.

Recommendation: post a correction to the spec body OR leave the spec untouched and let the findings carry the corrected expansion. Per the user's "no spec-body modifications" instruction, leave the spec; this findings doc carries the correction. Downstream uses of the spec (Q2c cascade reduces to ε_eff = ε_1 + ε_2 etc.) should be re-derived; the structural conclusion likely survives but the constants do not.

### F2 — Bronze under-models equation of centre by ~2× at the leading order — RESOLVED (see F2 deep-dive)

**Original surface finding (kept for historical record):** At Freeth-2006 ε = 0.054, the pin-slot leading `sin(ℓ)` coefficient is 11138 arcsec — approximately **half** of Brown's 22640 arcsec. Two original interpretations: Freeth's ε reconstruction is half of the algebraically-required value, OR the bronze genuinely under-models the equation of centre by 2×.

**Resolution status (added 2026-05-14):** See [F2 deep-dive section below](#f2-deep-dive--equation-of-centre-amplitude-puzzle). Verdict B (convention mismatch): Gourtsoyannis 2012 measures the physical bronze and reports ε = a/a₁ = 1.1mm/9.6mm = 0.1146 ± 0.0057, exactly 2.12× Freeth's reported 0.054. The bronze likely implements ≈ 6.3-6.6° max equation of centre, NOT an under-amplitude 3.1°. Freeth's "ε" is most plausibly a different normalisation (offset/diameter, or some equivalent factor-of-2 convention difference). The bronze is consistent with the Hipparchan eccentric-circle lunar model at approximately Brown's modern amplitude.

### F3 — The pin-and-slot family is fundamentally additive-in-angle

Every composition examined (Q2a parallel, Q2b summed, Q2c series, Q-jacobi-anger gear-mediated cascade) is additive-in-angle at leading order. The atan2 form `f_ε(θ) = atan2(sin θ, cos θ − ε)` is single-input, single-output. There is no in-family operation that produces multiplicative-in-angle (mixer) behaviour. **The missing operation** for mechanising any difference-frequency term (evection, variation, parallactic) is a true mixer — pin-slot composition cannot deliver one.

Implication: Greek-attainable mechanics with only pin-slot primitives cannot directly mechanise the second lunar inequality. The Ptolemaic crank-and-deferent (deferent-centre orbiting earth) is a different primitive — it's a *multiplicative* coupling of two cyclic groups (the deferent rotates while its centre orbits, multiplicatively coupling deferent-angle to centre-angle in the spatial output). This is consistent with the historical fact that Ptolemy invented evection (~150 CE) ~250 years after the Antikythera (~150-100 BCE); the mechanism was unavailable in 100 BCE Greek mechanics not just because the astronomy was unknown, but because the primitives were insufficient.

### F4 — Out-of-plane height profile fits fiber-as-spatially-absent stance cleanly

Q-height-reader confirms (numerically) that out-of-plane slot elevation `h(s)` is invisible to the gear's SO(2) action and projectable via a separate height-reader. The output algebra of the height-reader is a programmable function of `h ∘ s(θ)`, ranging over continuous Fourier series (sinusoidal `h`), polynomial-degree-limited content (quadratic `h`), and Z/n discrete (step `h`). This is the project's canonical bench-test for the substrate/excitation two-level ontology (MFO §VII.1.1 connection from spec).

### F5 — Tooth-pitch noise framing in antikythera §11.6.6 needs refinement

Pin-and-slot is NOT a frequency-band low-pass filter (Q-tooth-noise direct test: k=100 transmission ratio = 1.0). The §11.6.6 "dampening" claim should be re-stated as variance-via-phase-averaging-across-tooth-pitches OR as the result of the downstream pointer-integration step, not as a property of the pin-and-slot itself.

---

## Open follow-ups (next-spike candidates)

1. **Bronze ε reconstruction discrepancy** (F2 above). Why does ε=0.054 produce ~half of Brown's eq-of-centre leading coefficient? Resolve against Freeth 2006 calibration to direct lunar measurements.
2. **A true-mixer primitive in Greek mechanics?** Could a Q1b height-reader with `h(s) = β sin(2π s / λ)` and a SECOND input rotating the slot's reference frame realise multiplicative-in-angle coupling? That's a 4-DOF mechanism (gear-1 input, gear-2 input, height profile, height-reader); algebra-tractable, no CAD required. Worth a follow-up.
3. **§11.6.6 refinement.** Replace "pin-and-slot is a low-pass filter" with one of:
   - "the pin-and-slot's downstream pointer-integration is a low-pass filter"
   - "tooth-pitch variance averages out over multiple advances via phase cancellation"
   - "pin-and-slot transmits noise but the eccentric modulation creates ε/2-scale sidebands that diffuse coherent-noise into low-amplitude broadband."
4. **Verify Freeth-2006 ε convention against PDF.** Per `feedback_pdf_extraction_citation_discipline.md`, the 0.054 number should be re-verified by extracting the actual Freeth 2006 Nature paper PDF, identifying the parameter definition used, and confirming the convention matches `atan2(sin θ, cos θ − ε)` with ε = e/r. The 2× ambiguity in F2 might be a convention mismatch.
5. **Q-DAG-placement re-framing.** Saros/anomalistic combination via Q2b is a separate target; could be investigated independently if a specific motivation surfaces.

---

## Files produced

- `docs/srmech/notes/spike_pinslot_findings_script.py` — execution script (NumPy + scipy.special)
- `docs/srmech/notes/spike_pinslot_findings_q2_central_2026-05-14.ndjson` — Q2-central evection conjecture (29 records)
- `docs/srmech/notes/spike_pinslot_findings_q_unif_2026-05-14.ndjson` — Q1a × Q2 unification (7 records)
- `docs/srmech/notes/spike_pinslot_findings_q_height_reader_2026-05-14.ndjson` — Q1b height-reader catalogue (4 records)
- `docs/srmech/notes/spike_pinslot_findings_q_siblinghood_2026-05-14.ndjson` — tooth-vs-slot siblinghood (2 records)
- `docs/srmech/notes/spike_pinslot_findings_q_dag_placement_2026-05-14.ndjson` — DAG placement (blocked, 1 record)
- `docs/srmech/notes/spike_pinslot_findings_q_tooth_noise_2026-05-14.ndjson` — tooth-pitch noise on composition (6 records)
- `docs/srmech/notes/spike_pinslot_findings_q_jacobi_anger_2026-05-14.ndjson` — Jacobi-Anger cascade (5 records)
- `docs/srmech/notes/spike_pinslot_f2_deep_dive_2026-05-14.py` — F2 deep-dive execution script (added 2026-05-14)
- `docs/srmech/notes/spike_pinslot_findings_q_f2_deep_dive_2026-05-14.ndjson` — F2 deep-dive (8 records, added 2026-05-14)

---

## Citations (verification status)

- **Freeth et al. 2006**, *Decoding the ancient Greek astronomical calculator known as the Antikythera Mechanism*, Nature **444**:587. Source for D-H1 pin-and-slot ε ≈ 0.054 (Fragment B reconstruction). **PDF not re-verified this session**; per `feedback_pdf_extraction_citation_discipline.md` this remains flagged. The 2× discrepancy in F2 may be a convention issue resolvable by PDF check.
- **Brown 1896**, *An Introductory Treatise on the Lunar Theory*. Source for evection leading coefficient +4585″ sin(2D − ℓ) and equation-of-centre +22640″ sin(ℓ). **Standard reference**; modern Meeus *Astronomical Algorithms* (2nd ed) ch. 47 cites +4586.4385″ for evection; we use 4586″ as the rounded canonical value. Numerical values used in this findings doc are from Meeus's tabulation, cross-referenced to Chapront-Touzé / ELP-2000 lunar theory.
- **Carman, Thorndike, Evans 2012**, *On the Pin-and-Slot Device of the Antikythera Mechanism, with a New Application to the Superior Planets*. Cited in the spike spec for outer-planet pin-slot extension; **PDF not extracted this session**, flagged for future verification before any further composition-claims land.
- **Freeth & Jones 2012**, *The Cosmos in the Antikythera Mechanism*, ISAW Papers 4. Cited in the spike spec for the bronze NOT modelling evection; **PDF not extracted**, flagged.

Internal references:
- `docs/antikythera-maths/research/pin_and_slot.py` — D-H1 baseline implementation
- `docs/antikythera-maths/research/gear_database.py` — LUNAR_TRAIN and MESH_EDGES
- `user_stance_fiber_as_spatially_absent_encoding.md` — Q1b stance test
- `user_stance_hyper_as_3d_spatial_interface.md` / MFO §VII.1.1 — two-level ontology
- antikythera notebook §11.6.3, §11.6.4, §11.6.6, §11.6.7 — architectural-mode thread

---

## Honest summary (3-5 bullets)

- **Q2 evection conjecture: FALSIFIED.** The Q2b summed-output differential pin-and-slot is structurally separable (zero cross-terms in the 2D Fourier spectrum), so it cannot produce difference-frequency lines like evection's `2D − ℓ`. The pin-and-slot family is fundamentally additive-in-angle and lacks the multiplicative-in-angle (mixer) primitive needed to mechanise the second lunar inequality.
- **Spec algebra typo caught (F1):** the leading expansion is `θ + ε sin θ` not `θ + 2ε sin θ`. Documented in findings; spec body unchanged per instruction.
- **Bronze under-modelling discovered (F2):** at Freeth-2006 ε=0.054, leading `sin(ℓ)` coefficient is 11138″ ≈ half of Brown's 22640″. Either ε reconstruction is off by 2× or the bronze genuinely under-models. Worth a follow-up spike.
- **Q1b height-reader catalogue (CATALOGUED):** the slot is a programmable algebraic encoder; sinusoidal `h` excites Bessel-Anger Fourier content, polynomial `h` limits to polynomial-degree Fourier order, step `h` realises Z/n discrete output. Bench-instrument for the fiber-as-spatially-absent stance is operational.
- **Jacobi-Anger cascade hypothesis: algebra-correct, bronze-uninstantiated.** Synthetic 2-stage cascade matches `3ε` prediction at the leading k=2 line; bronze has only one pin-and-slot stage so the prediction has no archaeological referent. The Antikythera lunar spectrum is dominated by the single equation-of-centre `ε^k/k` series — no higher harmonics from cascade.
- **§11.6.6 "low-pass" framing needs refinement (F5):** direct measurement shows pin-and-slot transmits high-k noise at near-unity gain with small ε/2-scale sidebands. NOT a frequency-band low-pass. Either re-frame as variance-via-phase-averaging, or attribute the dampening to the downstream pointer integration.

---

## F2 deep-dive: equation-of-centre amplitude puzzle

**Date:** 2026-05-14 (same-day follow-up after F2 was flagged in the headline findings)
**Reproduce:** `python -X utf8 docs/srmech/notes/spike_pinslot_f2_deep_dive_2026-05-14.py`
**Data:** `docs/srmech/notes/spike_pinslot_findings_q_f2_deep_dive_2026-05-14.ndjson` (9 records).

**Headline verdict.** **Resolution is option (B) — convention mismatch / reconstruction error, not bronze under-amplitude.** Gourtsoyannis 2012 measured the bronze directly and reports pin-slot ε = a/a₁ = 1.1mm/9.6mm = 0.1146 ± 0.0057, exactly 2.12× Freeth 2006's reported 0.054. At ε=0.1146 the pin-slot produces max equation of centre 6.58° ≈ Brown's modern 6.29° within ~4%. The bronze is NOT under-amplitude. Freeth's "ε" is most plausibly half-the-ratio (offset/diameter rather than offset/radius), making the spike's prior framing of "bronze under-models by 2×" wrong — the bronze approximately matches Brown.

### Step 1 — Pin-slot is the eccentric-anomaly (E-of-M) series, NOT the true-anomaly (ν-of-M) series

The pin-slot transform `f_ε(θ) = atan2(sin θ, cos θ − ε)` is the polar angle of (cos θ − ε, sin θ) — the angle from the offset center of a unit circle. In Keplerian orbital geometry this is exactly the **eccentric anomaly E expressed as a function of the mean anomaly M** when θ is identified with M, NOT the true anomaly ν.

| Series | Geometry | c_1 coefficient | c_2 coefficient |
|---|---|---|---|
| Pin-slot atan2 | Offset-center circle | **ε** | **ε²/2** |
| Kepler E(M) | Eccentric anomaly from mean anomaly | **e** | **e²/2** |
| Kepler ν(M) | True anomaly from mean anomaly (focus-frame) | **2e** | **(5/4)e²** |
| Brown lunar (Meeus AA) | ν(M) at e_moon = 0.0549 | 22640″ ≈ 2·e_moon·(180/π·3600) | 769″ ≈ (5/4)·e²·(180/π·3600) |

Numerical verification at e = 0.054 (single representative value):
- Pin-slot c_1 = 11138″ (measured), pure prediction ε = 11138″
- Kepler E(M) c_1 = 11134″ (within 0.04% of pin-slot — confirms same series)
- Kepler ν(M) c_1 = 22268″ (~2× the pin-slot — confirms ν is 2× E in leading order)
- Brown's modern c_1 = 22640″ at modern e_moon = 0.0549

**The factor of 2 between pin-slot and Brown is the structural distinction between eccentric-anomaly and true-anomaly geometries.** The pin-slot models an offset-center circle, not a Keplerian ellipse with focal observer. Greek deferent geometry IS the eccentric-anomaly form (Hipparchan eccentric-circle and Ptolemaic equant are both center-frame, not focus-frame).

### Step 2 — Freeth 2006 PDF: not extracted directly

Per `feedback_pdf_extraction_citation_discipline.md`: the Freeth 2006 *Nature* 444:587 PDF is paywalled; the academia.edu mirror returned only abstract-level content via WebFetch, and the ResearchGate URL was 403. The supplementary information was not accessible in this session. **Citation status: outstanding.** The ε=0.054 value as quoted in `docs/antikythera-maths/research/pin_and_slot.py` (line 55) and prior spike documents has NOT been re-verified against the Freeth 2006 supplementary text in this session.

What WAS extractable from web search (not the PDF body): the Springer chapter "Phases in the Unraveling of the Secrets of the Gear System of the Antikythera Mechanism" (Freeth, 2008/2012) explicitly states "the estimate of the distance between the arbors on the k gears is about 1.1 mm, with a pin distance of 9.6 mm, giving an angular variation of 6.5°." This matches Gourtsoyannis's parameters exactly (a=1.1mm, a₁=9.6mm, ratio 0.1146, eq-of-centre ~6.5°). So Freeth's own later writing reports the same bronze geometry Gourtsoyannis derives ε=0.1146 from. The ε=0.054 number in `pin_and_slot.py`'s docstring is therefore either:
- (i) a transcription/convention error (e.g., offset/diameter rather than offset/radius), OR
- (ii) a different parameter Freeth 2006 (Nature) reported (which we cannot verify without the supplementary).

Either way, the geometrically-correct value for the bronze atan2 form is ε ≈ 0.11, not 0.054.

### Step 3 — Carman, Thorndike & Evans 2012: PDF retrieval failed

WebFetch on the canonical URL (`http://webspace.pugetsound.edu/facultypages/jcevans/Carman%20Thorndike%20Evans.pdf`) returned binary/corrupted content. The paper's central claim (per web search summary): the pin-and-slot device produces "non-uniform circular motion, with the resulting motion equivalent in angle to the standard deferent-plus-epicycle lunar theory" — and they propose extending the same mechanism to superior planets. **No specific eccentricity value extracted from this source in this session.** Carman et al. would not have caught a 2× Freeth-reported-ε discrepancy specifically if they accepted Freeth's reported parameters.

### Step 4 — Gourtsoyannis 2012: ε_bronze = 0.1146 ≈ 2 × Freeth-reported

Extracted via WebFetch from academia.edu/41392086 — "Hipparchos vs. Ptolemy and the Antikythera Mechanism: Pin-Slot Device parameters ultimately linked to real eccentricity of Moon's Orbit" by Elias Gourtsoyannis (date uncertain from extraction; cited as 2012 in our prior spike, but Gourtsoyannis's specific publication year was not confirmed in this session — flag).

Key extracted facts:
- Pin offset a = 1.1 mm; pin distance a₁ = 9.6 mm.
- ε = a / a₁ = **0.1146 ± 0.0057**.
- Device max equation of centre α = arctan(0.1147) ≈ **6.50°** (Gourtsoyannis's α = arctan whereas our analytic max = arcsin; these agree to 0.04° at this ε).
- Gourtsoyannis explicitly claims: **ε = 2e where e is the modern orbital eccentricity (0.0549)**. 2 × 0.0549 = 0.1098 vs measured 0.1146; discrepancy < 4%.
- Comparison to Hipparchus's eclipse-derived value (Almagest IV.6): 5°1' or 4.5° (two estimates). Bronze ε corresponds to 6.5°, exceeding Hipparchus's eclipse-derived value but matching modern peak.

**This directly resolves the F2 puzzle**: the bronze does NOT under-model; Freeth's reported ε=0.054 is a half-the-real-ratio convention difference.

### Step 5 — Required ε under each interpretation

Three-way comparison (NDJSON record `F2/step5/three-way-comparison`):

| ε source | ε value | max eq-of-centre | c_1 (arcsec) | Notes |
|---|---:|---:|---:|---|
| Freeth 2006 (reported) | 0.054 | 3.10° | 11138 | Matches neither Hipparchan 5° nor Brown 6.29° |
| Hipparchus Almagest IV.6 (5;15/60) | 0.0875 | 5.02° | 18048 | Matches Almagest "5°1'" exactly |
| Brown modern (2e_moon) | 0.1098 | 6.30° | 22647 | Matches modern observed lunar amplitude |
| Gourtsoyannis bronze (measured) | 0.1146 | 6.58° | 23638 | Matches Brown within 4% |

The reading: **Freeth's ε=0.054 corresponds to no plausible astronomical interpretation** — it's 1.62× too small for Hipparchus, 2.03× too small for Brown. Gourtsoyannis's ε=0.1146 reproduces Brown's modern equation-of-centre within ~4% (and ~slightly overshoots Hipparchus's eclipse-derived 5°1'). The most economical reading is that Freeth's "ε" reports a doubled-denominator (e/(2r) instead of e/r, or equivalent) and the bronze ε in our atan2 convention is ε ≈ 0.11.

**The Hipparchan eccentric-circle is the same atan2 form as the pin-slot.** This is the canonical reading: the bronze IS the Hipparchan eccentric-circle deferent mechanism. To reproduce observed lunar amplitudes with the wrong (eccentric-circle, not Keplerian) geometry, Hipparchus had to use ε ≈ 2 × true orbital e. The bronze approximately implements this — slightly larger eccentricity than Hipparchus's Almagest value, closer to modern.

### Step 5 (Option D) — Downstream gear-ratio amplification: FALSIFIED

The remaining candidate from the spike prompt was "Option D: a downstream gear ratio amplifies the pin-slot output by 2×, recovering Brown's amplitude even at ε=0.054". Bronze topology rules this out:

- Pin-and-slot is between e3 and e4 (both 50t), with k2 (50t) carrying the output. All pin-slot wheels are 50:50:50:50.
- k2's axle drives the lunar dial pointer at 1:1.
- There is NO downstream gear-ratio multiplier between pin-slot output and lunar dial reading.

Per `gear_database.py` LUNAR_TRAIN, the upstream chain b1→c1→c2→d1→d2→e1→e3 sets the *rate* at which e3 rotates (the lunar anomalistic mean motion), but does NOT post-process the pin-slot's output. **Option D structurally ruled out** by bronze topology. The 2× cannot live downstream because there's no gear ratio there.

### Step 6 — Verdict and §11.6.6 implications

**F2 verdict: Option B (reconstruction error / convention mismatch).** Gourtsoyannis 2012 reports the geometrically-correct ε = 0.1146 from direct bronze measurement; Freeth 2006's ε=0.054 (as cited in `pin_and_slot.py` and the prior spike framing) is half of this and corresponds to no astronomical interpretation. The bronze approximately matches Brown's modern equation-of-centre (~6.3-6.6°), consistent with a Hipparchan eccentric-circle implementation with slightly-larger-than-Hipparchan eccentricity.

**Implications for prior spike findings:**
- The original spike-headline "bronze under-models eq-of-centre by 2×" framing is **incorrect**. The bronze does not under-model; the cited ε is half its real value.
- The corrected ε≈0.11 is exactly what the spike's F2 caveat predicted as a "true ε" candidate.
- Re-running all spike numerical scans with ε=0.1146 would change leading-coefficient amplitudes by 2× and second-harmonic amplitudes by ~4× (since c_2 = ε²/2 scales as ε²). The qualitative falsification of Q2-central evection conjecture is unaffected — additive composition is still additive — but the numerical amplitudes reported for Q1a k=2 and Q-jacobi-anger cascade should be re-computed at ε=0.1146 if those numerics are load-bearing for any downstream claim.

**Citation/PDF-extraction discipline (per `feedback_pdf_extraction_citation_discipline.md`):**
- Freeth 2006 Nature primary PDF: **not extracted** (paywalled/403). The ε=0.054 quote in `pin_and_slot.py` line 55 is therefore not directly verified against the source in this session.
- Carman-Thorndike-Evans 2012: **not extracted** (binary corruption from canonical URL).
- Gourtsoyannis "Hipparchos vs. Ptolemy" academia.edu/41392086: **WebFetch summary extracted** (not raw PDF), parameters confirmed via two independent web sources (academia.edu mirror + the Springer chapter quotation). Publication year flagged uncertain.
- **Best-available-without-PDF-access verdict:** The convergence between Gourtsoyannis's measurements, the Springer chapter quote ("1.1 mm, 9.6 mm, 6.5°"), and the geometric algebra (ε must equal ≈0.11 to match observed amplitudes) is strong enough to commit to Option B. A future spike should obtain Freeth 2006 Nature supplementary and Gourtsoyannis's primary PDF to verify the published quotation.

### Next-spike candidates (per "questions come from results")

1. **Authoritative-source confirmation.** Obtain Freeth 2006 Nature supplementary, Carman-Thorndike-Evans 2012, and Gourtsoyannis primary PDF; verify the ε convention question. Best-priced route: arXiv preprint search for any of these (Carman, Thorndike, Evans publish on arXiv).
2. **Correct `pin_and_slot.py` ε constant.** Update `ECCENTRICITY_FREETH_2006 = 0.054` to `ECCENTRICITY_BRONZE_GOURTSOYANNIS = 0.1146` (or both, with cross-references). Re-derive D-H1 T-breaking ratio at the corrected ε. Conductor decision; do not unilaterally edit.
3. **Re-run Q-jacobi-anger and Q1a k=2 at ε=0.1146.** The qualitative findings (cascade-algebra-holds, k=2-not-evection) survive but the numerical amplitudes scale: c_1 doubles to ~22600″, c_2 quadruples to ~1330″. Update findings doc table values if conductor wants the corrected numerics.
4. **Hipparchan-vs-Ptolemaic bronze calibration question.** Hipparchus's Almagest 5°1' corresponds to ε=0.0875; bronze ε=0.1146 corresponds to ~6.58°. Did the Antikythera builders calibrate to a Ptolemaic or post-Hipparchan value, OR was Gourtsoyannis's measurement biased by Fragment B distortion? Archaeological question; outside spike scope.
5. **Q1b height-reader spec re-derivation at corrected ε.** The height-reader catalogue used s(θ) = cos θ − ε with ε=0.054; sinusoidal `h` Bessel-Anger spectrum at ε=0.054 is roughly 2× narrower than at ε=0.11. Programmable-encoder catalogue should note ε convention.

---

## §11.6.6 re-attribution (informed by F2)

**Status:** PROPOSED REWRITE (not applied; conductor decision pending). The antikythera notebook §11.6.6 ([antikythera_spectral_research_notebook.md L686–L720](../../antikythera-maths/antikythera_spectral_research_notebook.md)) makes two distinct claims about pin-and-slot. Q-tooth-noise (F5) shows the second is wrong; F2 deep-dive constrains the first.

### What §11.6.6 currently says

Section A ("Differentials as drift-collecting output dials"): the b1-b2 differential subtracts solar from sidereal lunar to produce the synodic month phase ball. Reusable as a drift collector. **This claim survives** — differentials are genuine in-bronze mechanisms with the architecture §11.6.6 describes; no F2 or F5 implication.

Section B ("Feedback dampening via mechanical low-pass filters") — three bullets:
1. **"Pin-and-slot is a mechanical low-pass filter."** Specifically: "the pin slides smoothly along the slot rather than snapping discrete tooth-by-tooth, which means the output's angular position is integrated over the slot's contact arc — averaging out tooth-pitch noise on its input. Mechanically: the slot is a moving-average kernel. Spectrally: it is a low-pass filter with cutoff inversely proportional to the slot's angular extent." **WRONG per Q-tooth-noise direct measurement (F5).** Pin-slot transmits k=100 noise at unity gain; the ε/2 sidebands are tiny. The slot's geometric continuity does NOT make it a frequency-band low-pass.
2. **"A pin-and-slot inserted mid-chain damps tooth-pitch noise on that mesh."** Same wrong premise; the "smoothing" attribution is misplaced.
3. **"Differentials as variance-isolation, not averaging."** Correct, survives. Independent differentials amplify variance, shared-upstream differentials cancel it.

### Proposed rewrite of §11.6.6 Section B

Replace the bullets with text that:
(a) preserves Section A unchanged;
(b) revises Section B's first two bullets to attribute the actual dampening mechanism correctly;
(c) cross-references the F2 finding for the structural-vs-numerical question of what pin-slot actually does spectrally;
(d) cross-references the F5 finding for the noise-transmission characterization;
(e) keeps the third bullet (differential variance behaviour) unchanged.

**Proposed text (insert in place of current Section B bullets 1-2):**

> #### B. Continuous-motion smoothing — where it actually lives
>
> True closed-loop feedback (where a downstream output corrects an upstream input) is anachronistic for Greek mechanics. The original §11.6.6 claim was that pin-and-slot provides mechanical low-pass filtering for tooth-pitch noise. **Direct measurement (Q-tooth-noise, spike [F5](../../srmech/notes/spike_pinslot_elevation_and_differential_findings_2026-05-14.md#cross-cutting-findings)) shows this is incorrect**: pin-and-slot transmits high-spatial-frequency noise at near-unity gain, with only small ε/2-scale sidebands induced by the eccentricity. The pin-slot's atan2 transform is smooth and analytic but not band-attenuating.
>
> The continuous-motion intuition is correct at a different level. Three mechanisms in the bronze actually provide noise reduction, none of them via per-mesh low-pass filtering:
>
> - **Pointer-integration low-pass.** The lunar pointer (and other dial pointers) rotate slowly relative to the input crank. Per-revolution tooth-pitch noise on intermediate meshes averages out over the pointer's slower rotation. The integration step is the time-domain low-pass; this lives at the pointer, not at any mesh.
> - **Phase-averaging variance reduction.** Tooth-pitch errors on a mesh have zero mean over a full revolution. Over many revolutions the angular position's variance grows as √N (random walk), but the variance per-radian-of-pointer-output stays bounded if the train's gear ratios spread the cumulative error broadband. The pin-slot's nonlinear-but-smooth transmission redistributes spectral energy without removing it.
> - **Shared-upstream noise cancellation in differentials.** Per §11.6.7: differentials between paths that share an upstream gear cancel that gear's tooth-pitch error in the difference. This is genuine noise reduction at the dial level; the b1-b2 differential is the canonical bronze example.
>
> What pin-and-slot *does* spectrally is **bound** the equation-of-centre amplitude geometrically. The Hipparchan eccentric-circle that the pin-and-slot implements (per spike [F2](../../srmech/notes/spike_pinslot_elevation_and_differential_findings_2026-05-14.md#f2-deep-dive--equation-of-centre-amplitude-puzzle); also Gourtsoyannis 2012 "Hipparchos vs. Ptolemy and the Antikythera Mechanism") produces output angular content of the form θ + Σ_k (ε^k / k) sin(kθ) — exactly the eccentric-anomaly series E(M), with leading coefficient ε ≈ 0.11 (Gourtsoyannis's measured bronze value; Freeth-2006-reported 0.054 is half this via convention difference). This is structurally NOT a Keplerian true-anomaly generator (which would have leading coefficient 2e), but it is structurally what Hipparchus's lunar theory required.

### What's preserved from the current §11.6.6

- Section A (differentials as drift collectors) unchanged.
- Section B bullet 3 (differential variance behaviour) unchanged.
- "Implication for compensator architecture" subsection: bullet 1 ("Pin-and-slot inserted at a peripheral leaf, providing continuous-motion smoothing for that pointer's drift") needs re-grounding — it's based on the (wrong) per-mesh low-pass claim. The corrected reading: **pin-and-slot at a peripheral leaf adds an eccentric-circle equation-of-centre transform to that pointer's output**, not a low-pass filter for the tooth-pitch noise of that mesh. The architectural conclusion (use existing primitives, not new vocabulary) survives but the noise-reduction motivation does not — eccentric-circle transforms are about astronomical-amplitude shaping, not noise filtering.

### Conductor decision points (fermata records)

- **Whether to apply this rewrite to §11.6.6** or instead add a §11.6.6.4 "spike F2/F5 correction" subsection that flags but does not overwrite.
- **Whether to update `pin_and_slot.py`'s `ECCENTRICITY_FREETH_2006 = 0.054` constant** (and the docstring's "Freeth 2006 estimates eps ≈ 0.054") to reflect Gourtsoyannis's ε=0.1146 and the convention question. This is a code change with downstream impact on D-H1 numerical results and would need a separate verification round.
- **Whether the §11.6.6 "compensator architecture" implication subsection** needs a corresponding update or can stand as-is now that its noise-filtering motivation is invalidated.

### NDJSON

- `spike_pinslot_findings_q_f2_deep_dive_2026-05-14.ndjson` (9 records — Step 1 harmonic comparison, Step 1B pin-slot at modern e, Step 4 required-ε inversion, Step 5 Option D falsification, Step 5 pin-slot at ε=0.110, Step 2-3 Gourtsoyannis extraction, Step 5 Hipparchan eccentric-circle, Step 5 three-way comparison, Step 5 true-anomaly cross-check).

### Updated citations (verification status)

- **Gourtsoyannis "Hipparchos vs. Ptolemy and the Antikythera Mechanism"** (date uncertain — flagged for verification). Source: academia.edu/41392086. WebFetch summary extracted, primary PDF not extracted. Key facts (pin offset 1.1mm, pin distance 9.6mm, ε=0.1146±0.0057, eq-of-centre 6.5°) confirmed cross-source via Springer "Phases in the Unraveling" chapter quotation. **Status:** best-available-without-PDF-access; primary PDF re-verification recommended.
- **Freeth 2006 Nature 444:587 supplementary.** PDF not extracted (paywalled, ResearchGate 403, academia.edu mirror abstract-only). ε=0.054 quote in `pin_and_slot.py` not directly verified in this session. **Status:** outstanding per `feedback_pdf_extraction_citation_discipline.md`.
- **Carman-Thorndike-Evans 2012 *Journal for the History of Astronomy* 43:93-116.** PDF retrieval failed (binary corruption from webspace.pugetsound.edu URL). General claims about pin-and-slot equivalence to deferent+epicycle confirmed via web summary; specific eccentricity treatment not extracted. **Status:** outstanding.
- **Almagest IV.6 (Ptolemy/Toomer 1984).** Hipparchus's lunar eccentricity 5;15/60 = 0.0875 used as canonical reference; sourced from standard scholarly tabulation, not re-extracted from primary text this session.
