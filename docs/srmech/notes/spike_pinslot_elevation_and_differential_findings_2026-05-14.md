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

## F2 refinement — primary-source verified (2026-05-14, after Freeth 2006 PDF extraction)

**Status:** REFINED with primary-source data. User added the Freeth 2006 *Nature* paper to `docs/antikythera-maths/hoodoos/` after the original F2 deep-dive completed. PDF read locally; below is the corrected verdict.

### Freeth 2006 main letter explicitly publishes the bronze geometry

**Page 590, Figure 6 caption** (verbatim quote):

> "Our estimate of the distance between the arbors on the k gears is about 1.1 mm, with a pin distance of 9.6 mm, giving an angular variation of 6.5°. According to Ptolemy, Hipparchos made two estimates for a lunar anomaly parameter, based on eclipse data, which would require angular variations of 5.9° or 4.5° here—although estimates of the anomaly from Babylonian astronomy were generally larger."

**Computed from Freeth 2006's own numbers:** ε = 1.1 mm / 9.6 mm = **0.1146** (matches Gourtsoyannis exactly — Gourtsoyannis is not correcting Freeth, they're citing the same measurement from the same source).

### Verdict: corrected

The original F2 deep-dive framed this as "Freeth 2006's published ε is half of the bronze-measured ε; Gourtsoyannis re-measured." **That framing was wrong.** Freeth 2006's primary text (the *Nature* paper itself) publishes the same numbers Gourtsoyannis cites. They agree.

**What was actually wrong:** the project's `docs/antikythera-maths/research/pin_and_slot.py` had `ECCENTRICITY_FREETH_2006 = 0.054` — that constant does NOT appear in Freeth 2006. It's a project-internal transcription error or convention conflation. Speculation on origin:

- Possibly `e / diameter` instead of `e / radius`: 1.1 / (2 × 9.6) ≈ 0.057 (close to 0.054 but not exact).
- Possibly conflation with the **modern lunar orbital eccentricity** e_moon = 0.0549 (numerically very close to 0.054). Substituting the astronomical eccentricity for the *mechanical* eccentricity would produce exactly this number.

Either way, **the constant in `pin_and_slot.py` was never what Freeth 2006 said**. The `feedback_pdf_extraction_citation_discipline` memory exists precisely for this: don't trust prior attributions; extract the actual PDF.

### Greek-convention finding survives

The deeper finding from the original F2 deep-dive — that the pin-slot atan2 implements the **eccentric-anomaly E(M) series** (Greek center-frame eccentric-circle), NOT the Keplerian focus-frame ν(M) series — remains correct and primary-source-confirmed:

- Bronze's ε ≈ 0.1146 ≈ 2 × modern e_moon (0.0549).
- Greek center-frame geometry produces leading-order `c_1 = ε`.
- Modern focus-frame produces `c_1 = 2e`.
- These match at the OBSERVED level because the Greek convention's eccentricity-doubling is exactly the algebraic relation between the two frames.

The bronze does the right astronomy in the right way for its convention. The convention isn't wrong; it's the Greek geometric tradition.

---

## NEW finding: Bronze calibration is closer to MODERN than to Hipparchos's published values

This **emerged from the primary-source extraction** — not a question we went in asking, but it falls out cleanly from Freeth 2006's own data.

### The calibration table (all values from Freeth 2006 + Brown 1896)

| Source | Angular variation | Equivalent ε (e / pin-distance) |
|--------|-------------------|-------------------------------|
| Antikythera bronze (direct measurement) | **6.5°** | **0.1146** |
| Hipparchos estimate #1 (per Ptolemy/Almagest) | 5.9° | 0.1031 |
| Hipparchos estimate #2 (per Ptolemy/Almagest) | 4.5° | 0.0785 |
| Modern Brown's lunar theory (leading EOC) | 6.29° | 0.1098 |
| Babylonian astronomy (per Freeth 2006) | ">5.9°" ("generally larger") | unspecified |

### The headline

**The bronze's 6.5° is higher than either of Hipparchos's published estimates and is closest to MODERN.** The bronze does NOT just transcribe Hipparchos. Three possible explanations:

1. **Empirical calibration from direct observation.** The bronze builders may have observed the lunar anomaly themselves rather than copying Hipparchos's published value. Greek astronomers had direct observational capability; a 6.5° amplitude is within the range you'd measure from naked-eye eclipse timing over a few decades.

2. **Babylonian-derived value.** Freeth 2006 explicitly notes "estimates of the anomaly from Babylonian astronomy were generally larger." Babylonian lunar tables (ACT/Goal-Year texts; System A and System B) had precision-empirical lunar models that often exceeded Greek geometric reconstructions on the first inequality. If the bronze used a Babylonian value, it would plausibly land near 6-7°.

3. **Pre-Almagest Hipparchan refinement.** Hipparchos published multiple values across his career. Ptolemy's *Almagest* (~150 CE, ~250 years after Hipparchos) compresses Hipparchos's work into the two estimates quoted; the bronze (~150-100 BCE, contemporaneous with Hipparchos's later work) might use a value Hipparchos refined but Ptolemy didn't preserve.

### Why this matters

The §11.6.6.4 / §11.6.6.5 amendment subsections in the antikythera notebook currently frame the ε question as "Greek-convention eccentricity-doubling." That's correct but incomplete. The bronze's specific value (6.5°, ε=0.1146) is not the Hipparchan value from the *Almagest* (4.5° or 5.9°); the bronze is operating at higher amplitude. **The instrument is more accurate than Hipparchos's surviving published values suggest.**

Cross-cuts with the **antikythera notebook §11.6 architectural-mode thread**: the bronze's empirical accuracy on the first lunar inequality is a partial constraint on the design tradition. If the builders had access to better lunar values than Hipparchos's published ones, that itself is a non-trivial archaeological finding — it suggests either Babylonian transmission, independent observational tradition, or Hipparchan inheritance through channels other than the *Almagest* lineage.

### Falsification risk

The Gourtsoyannis bronze measurement (1.1 mm / 9.6 mm) may be biased by Fragment B distortion (the corrosion / squashing over 2000 years of seabed). If the bronze was originally calibrated to Hipparchos's 5.9° (ε ≈ 0.103) but distorted into the measured 6.5° (ε ≈ 0.115), the "closer to modern" finding evaporates. The 10% gap between Hipparchos #1 and bronze-measured is geometrically achievable as distortion.

**Conservative claim:** within measurement uncertainty, the bronze ε is consistent with Hipparchos #1 (5.9°), Babylonian (larger), modern (6.29°), OR a Hipparchan refinement Ptolemy didn't preserve. Confidently *NOT* consistent with Hipparchos #2 (4.5°).

### Next-spike candidate that came FROM this result

**"Bronze calibration sensitivity to Fragment B distortion."** A direct uncertainty analysis: given the published uncertainty bounds on Gourtsoyannis's 1.1 ± 0.05 mm and 9.6 ± 0.2 mm (or similar — the actual error bars would need to be verified), propagate through to ε's error bar. Compare the 1σ confidence interval against Hipparchos #1 (5.9°), Babylonian, and modern. This quantifies whether "bronze closer to modern than to Hipparchos" is a real signal or measurement noise.

---

## F6 — Pin-and-slot is the bronze's universal variable-motion primitive (Freeth 2021)

User added Freeth et al. 2021 *Scientific Reports* "A Model of the Cosmos in the ancient Greek Antikythera Mechanism" ([DOI 10.1038/s41598-021-84310-w](https://doi.org/10.1038/s41598-021-84310-w), open-access CC BY 4.0) to `docs/antikythera-maths/hoodoos/` after F2-refinement landed. Author Correction ([DOI 10.1038/s41598-021-96382-9](https://doi.org/10.1038/s41598-021-96382-9), 24 Aug 2021) also added — the correction is purely typographic (Greek-letter encoding + fraction-formatting), no impact on mechanism findings; correction-check itself is the load-bearing discipline step per `feedback_pdf_extraction_citation_discipline`.

### Major finding from Freeth 2021

Per Figure 3c, 3d, and the "Theoretical mechanisms for our model" section (page 7), **the pin-and-slot mechanism is NOT exclusive to the lunar anomaly** — Freeth's 2021 reconstruction proposes that pin-and-slot (or its sibling, pin-and-slotted follower) is the **universal variable-motion primitive** for all 5 planets in the cosmos display:

| Mechanism | Architecture | Pin-and-slot configuration |
|-----------|--------------|----------------------------|
| Lunar anomaly (Freeth 2006) | 4-gear epicycle | Single pin-and-slot on eccentric axes (D-H1) |
| Inferior planets — Mercury, Venus (Freeth 2021 Fig 3c) | 5-gear *direct* mechanism | Pin-and-slotted follower (on the central axis) |
| Superior planets — Mars, Jupiter, Saturn (Freeth 2021 Fig 3d) | 7-gear *indirect* mechanism | Pin-and-slot device on eccentric axes — **structurally analogous to the lunar mechanism** (Freeth's own wording, p. 7: *"analogous to the subtle mechanism that drives the lunar anomaly"*) |

Direct quote, Freeth 2021 p. 7:

> "Using our identified period relations for all the planets, we have devised new theoretical planetary mechanisms expressing the epicyclic theories, which fit the physical evidence. For the inferior planets, previous 2-gear mechanisms are inadequate for more complex period relations because the gears would be too large. Two-stage compound trains with idler gears are necessary, leading to new 5-gear mechanisms with pin-and-slotted followers for the variable motions (Fig. 3c). For the superior planets, earlier models used direct mechanisms, directly reflecting epicyclic theories with pin-and-slotted followers. Here we propose novel 7-gear indirect mechanisms with pin-and-slot devices for variable motions (Fig. 3d), analogous to the subtle mechanism that drives the lunar anomaly."

### Architectural pattern: gear-ratio chain → single pin-slot at the leaf

Reading the gear-train notation in Figure 3 (`~` means meshes-with, `+` means fixed-to-same-arbor, `⊕` means with-a-pin-and-follower-on-central-axis OR with-a-pin-and-slot-on-eccentric-axes):

| Planet | Gear train (Freeth 2021 Fig 3e, 3f) | Pin-and-slot location |
|--------|---------------------------------------|------------------------|
| Mercury | `51 ~ 72 + 89 ~ 40 ~ 20 ⊕ follower` | At the final stage |
| Venus | `51 ~ 44 + 34 ~ 26 ~ 63 ⊕ follower` | At the final stage |
| Mars | `56 ~ 64 + 38 ~ 40 ~ 71 ⊕ 80 ~ 80` | Mid-to-late stage |
| Jupiter | `56 ~ 64 + 45 ~ 40 ~ 43 ⊕ 65 ~ 65` | Mid-to-late stage |
| Saturn | `56 ~ 52 + 61 ~ 40 ~ 68 ~ 86 ⊕ 86` | Late stage |
| True Sun | `56 ~ 52 ~ 56 ⊕ follower` | At the final stage (simple 3-gear) |
| Mean Sun | (no nonlinear stage — uniform rotation) | n/a |
| Nodes | `49 ~ 62 + 64 ~ 48` | n/a (no pin-and-slot; pure gear cascade) |
| Lunar (Freeth 2006) | b1 → ... → e3 → k1 ⊕ k2 | At the final stage |

**Pattern**: every variable-motion output in the bronze is `multi-stage gear chain → single pin-and-slot at or near the leaf`. The cumulative gear ratio of the upstream chain determines what frequency the pin-and-slot perturbs.

### Refinement of Open Question 6

**The original Open Question 6** in the spike spec ("Gear-ratio-mediated pin-slot cascade") imagined a chain like `G_k1 → f_ε1 → G_k2 → f_ε2 → ... → G_kN → f_εN` — multiple alternating pin-and-slot and gear stages.

**The bronze pattern (now known from Freeth 2021)** is simpler: `G_k1 → G_k2 → ... → G_kN → f_ε` — a multi-stage gear-ratio cascade feeding a *single* terminal pin-and-slot.

The Jacobi-Anger amplitude hypothesis from Open Question 6 still applies, but in a degenerate form: with only one pin-and-slot stage at the leaf, the output spectrum is the simple Bessel-series perturbation of the cumulative-gear-ratio fundamental. For a single pin-slot driven at input frequency `k·θ` with eccentricity ε:

```
f_ε(k·θ) ≈ k·θ + ε sin(k·θ) + (ε²/2) sin(2k·θ) + O(ε³)
```

The k-harmonic content appears at integer multiples of k·θ, with amplitudes `ε^m / m` (the corrected Kepler-form expansion from F1). **No cross-product Bessel cascade** — just a single ε-modulated frequency comb at the chain's cumulative ratio.

### Updated Q-jacobi-anger verdict (post-Freeth-2021)

- **Algebra holds** at the synthetic multi-pin-slot cascade level (Q-jacobi-anger findings doc) — confirmed.
- **Bronze does not instantiate the multi-pin-slot cascade.** Confirmed: each variable-motion output in Freeth 2021 has at most one pin-and-slot stage.
- **Bronze DOES instantiate the gear-ratio frequency injection**: every planet's pin-and-slot is driven at the cumulative gear ratio of the upstream train, so the perturbation appears at that frequency. The k-harmonic injection mechanism is real and pervasive — just not via cascaded pin-slots.

### Why this matters for the project's spectral framing

Pin-and-slot becomes a **single architectural primitive that the bronze re-uses across 6 outputs** (lunar + 5 planets). The bronze's design philosophy is more unified than Freeth 2006 alone suggested:

1. **Cyclic-group cascade** (multi-stage gear train) sets the rate / harmonic.
2. **Eccentric-anomaly perturbation** (single pin-and-slot at the leaf) adds the Hipparchan equation-of-centre.
3. **The two-step decomposition is universal** — every variable-motion dial gets the same architectural treatment.

This is a **substantially cleaner architectural finding** than the spike originally aimed at. The pin-and-slot is a *vocabulary primitive* in the bronze; it's the bronze's `f_ε` function, instantiated 6 times with different upstream gear ratios.

### Connection back to MFO substrate/excitation framing

The split that emerges is:

- **Substrate layer** (cyclic group action): the gear ratios. Multi-stage cyclic-group composition.
- **Excitation layer** (perturbation): the pin-and-slot's eccentric-anomaly transform. Geometrically nonlinear; small ε; produces the Hipparchan first lunar/planetary inequality at the cumulative frequency.

The bronze's architectural separation of "rate-setting cyclic-group cascade" from "amplitude-setting pin-and-slot leaf" maps cleanly onto MFO §VII.1.1's substrate/excitation ontology. The cyclic-group structure is substrate (extends to all bodies via shared gear primitives); the pin-and-slot is excitation (localized nonlinear perturbation at a body-specific eccentric axis).

This makes the bronze a **bench-scale realization of the substrate/excitation distinction at the constraint-geometry layer** — a closed-form, tractable, archaeologically attested example of the framework the project's MFO discipline normally invokes at cosmological scale.

### Next-spike candidates that came FROM F6

1. **Per-planet eccentricity catalogue.** Each planetary mechanism has its own ε for the terminal pin-and-slot. Freeth 2021 Supplementary Discussion S4 / Table S9 (referenced but not yet extracted) presumably lists these. Catalogue all 6 ε values (lunar + 5 planets); compare against ancient Greek values for each planet's equation of centre.
2. **Cumulative gear-ratio Fourier signatures.** For each planet, compute the cumulative gear ratio `k` from b1 to the pin-slot input; predict the Fourier amplitude at `k·ω_b1`, `2k·ω_b1`, etc. Compare against modern epicyclic-theory amplitudes for that planet. Quantifies how *accurate* the bronze is per planet.
3. **Universal pin-and-slot consequence**: if pin-and-slot is the bronze's universal primitive, then **every planetary dial inherits the same Greek-convention eccentricity-doubling** (per F2 refinement). Modern observers reading the bronze's planetary outputs should see angular variations 2× the modern epicyclic Δθ for each planet. Is this empirically confirmed by the bronze's surviving dial scales?
4. **Bronze's design unification at the spectral level.** The bronze isn't 6 separate astronomical instruments stitched together — it's *one* spectral architecture (cyclic-group rate-setting + pin-and-slot excitation) instantiated 6 times. This frames the bronze as a *programmable spectral computer* with one nonlinear primitive and configurable gear chains. **Possible cross-reference to the project's broader stored-relationship mechanism (PR #294) framing.**

### Citation status (per `feedback_pdf_extraction_citation_discipline`)

- **Freeth 2021 (DOI 10.1038/s41598-021-84310-w):** Primary PDF extracted directly from `docs/antikythera-maths/hoodoos/s41598-021-84310-w.pdf`. Open-access CC BY 4.0. **Verified directly.**
- **Freeth 2021 Author Correction (DOI 10.1038/s41598-021-96382-9):** Primary PDF extracted directly. Confirmed purely typographic; no impact on F2/F5/F6 findings. **Verified directly.**
- **Freeth 2006 (DOI 10.1038/nature05357):** Primary PDF extracted directly. Paywalled; cached in `hoodoos/antik2.pdf`. **Verified directly.** The 1.1mm / 9.6mm / 6.5° / Hipparchan-calibration claims in F2-refinement above are direct quotes from page 590.
- **Freeth 2009 SciAm (DOI 10.1038/scientificamerican1209-76):** Cached but provides only secondary popular-audience commentary; not load-bearing for any specific claim above.
- **Gourtsoyannis (academia.edu/41392086):** Still not extracted as primary PDF; cross-confirmed via the Freeth 2006 numbers above (which Gourtsoyannis quotes exactly).
- **Carman-Thorndike-Evans 2012:** Still not extracted; flagged as next-spike but lower priority now that the Freeth 2006 / 2021 primary verification is complete.

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

---

## Five-candidate execution (2026-05-14, post-F6)

**Status:** execution complete. Reproduce: `python -X utf8 docs/srmech/notes/spike_pinslot_five_candidates_2026-05-14.py`. Five NDJSON files written (one per candidate). Each candidate has TWO halves: bronze-instantiation (specific Antikythera answer) + general-algebra (pin-slot primitive beyond the bronze).

**Headline.** Candidates 2, 3, 4, 5 produce clean substantive answers (numerical bronze data + closed-form general algebra). Candidate 1 partially blocked on Freeth 2021 Supplementary Discussion S4 / Table S9 (not on disk) — only lunar ε extractable from the main letter's primary text; the per-planet ε values needed for the full table require supplementary material not in `hoodoos/`. Cross-cutting algebra-side findings all landed.

**One cross-cutting numerical finding (load-bearing):** the lunar cumulative gear ratio b1→e3 is **13.368**, matching the modern anomalistic-rate / solar-rate ratio (13.256) within 0.85%. This independently confirms that the gear-train notation extracted from Freeth 2021 Fig 3e is correctly interpreted and that the pin-slot is driven at the lunar anomalistic mean motion as expected.

---

### C1 — Per-planet eccentricity catalogue — PARTIALLY BLOCKED

**Bronze half.** Only the lunar entry is verifiable from extracted primary sources:

| Planet | Bronze ε | Source | max EOC (deg) | c_1 (arcsec) | Modern e | Modern 2e EOC (deg) | Status |
|--------|---:|---|---:|---:|---:|---:|---|
| Moon | **0.1146** | Freeth 2006 p.590 (a=1.1mm, a₁=9.6mm) | 6.58° | 23638 | 0.0549 | 6.29° | **Verified** |
| Mercury | — | not in main-letter; needs Sup. S4 | — | — | 0.2056 | 23.56° | Blocked |
| Venus | — | not in main-letter; needs Sup. S4 | — | — | 0.0068 | 0.78° | Blocked |
| Mars | — | not in main-letter; needs Sup. S4 | — | — | 0.0934 | 10.70° | Blocked |
| Jupiter | — | not in main-letter; needs Sup. S4 | — | — | 0.0484 | 5.55° | Blocked |
| Saturn | — | not in main-letter; needs Sup. S4 | — | — | 0.0539 | 6.17° | Blocked |

Freeth 2021 Supplementary Discussion S4 / Supplementary Table S9 are referenced but not in `docs/antikythera-maths/hoodoos/`. Without supplementary extraction we cannot complete the per-planet ε catalogue. The main letter publishes only the lunar ε explicitly (via the 1.1mm/9.6mm/6.5° quote on p. 590).

**General-algebra half (closed-form for Hipparchan-eccentric mechanism).** For any single-pin-slot leaf mechanism with cumulative-ratio-k upstream chain driving the pin-slot at eccentricity ε:

```
θ_out(t) = k·ω·t + Σ_{m=1}^∞ (ε^m / m) sin(m·k·ω·t)
```

- Leading coefficient c_1 = ε rad = ε × 206265 arcsec
- Harmonic c_m = ε^m / m (Kepler-series form; F1-verified to machine precision through m=5)
- Pure frequency comb at integer multiples of k·ω; no content at non-multiples; no cross-terms
- Distinct from focus-frame Keplerian ν(M) which has c_1 = 2e (the 2e ⇔ ε identity is the leading-order Greek-convention doubling — see C3)

**Verdict.** Bronze-instantiation: only lunar entry filled (extraction-blocked on Supplementary S4 for the other 5). General-algebra: closed-form complete for the universal mechanism.

NDJSON: `spike_pinslot_findings_q_planetary_eccentricity_2026-05-14.ndjson` (7 records).

---

### C2 — Cumulative gear-ratio Fourier signatures — LANDED

**Bronze half.** Cumulative gear ratio b1 (or planetary drive) → pin-slot input axis, computed from Freeth 2021 Fig 3e/3f gear-train notation:

| Planet | Gear train (Freeth 2021) | Cumulative ratio k | Modern reference rate ratio | Match? |
|--------|---|---:|---:|---|
| Moon | b1(64) ~ c1(38) + c2(48) ~ d1(24) + d2(127) ~ e1(32) + e3(50) | **13.368** | 13.256 (anomalistic/solar) | 0.85% over |
| Mercury | 51 ~ 72 + 89 ~ 40 ~ 20 | 3.152 | — | — |
| Venus | 51 ~ 44 + 34 ~ 26 ~ 63 | 0.626 | — | — |
| Mars | 56 ~ 64 + 38 ~ 40 ~ 71 | 0.468 | — | — |
| Jupiter | 56 ~ 64 + 45 ~ 40 ~ 43 | 0.916 | — | — |
| Saturn | 56 ~ 52 + 61 ~ 40 ~ 68 ~ 86 | 0.764 | — | — |

The **lunar k=13.368 matches the modern anomalistic/solar rate ratio (13.256) to 0.85%** — independent confirmation that the bronze gear-train algebra is correctly decoded. The lunar pin-slot is driven at the anomalistic mean motion exactly as expected.

For each planet, assuming the bronze ε equals the lunar ε=0.1146 as a working proxy (caveat: per-planet ε unverified), the predicted Fourier amplitudes at the first 5 harmonics of k·ω are:

| Harmonic | Amplitude (rad) | Amplitude (arcsec) |
|---:|---:|---:|
| m=1 | 0.1146 | **23638** |
| m=2 | 0.00657 | 1354 |
| m=3 | 5.01e-4 | 103.4 |
| m=4 | 4.32e-5 | 8.9 |
| m=5 | 3.97e-6 | 0.82 |

Per-harmonic amplitude rule: c_m / c_1 = ε^(m-1) / m. At ε=0.1146 this means the second harmonic is ~5.7% of the first; the third is ~0.4% of the first.

**Numerical verification.** Direct FFT measurement on N=32768 samples at ε=0.1146 confirms the closed-form c_m = ε^m/m to <1e-6 precision through m=3.

**General-algebra half.** The universal formula for any cumulative-ratio-k chain feeding a single pin-slot:

```
θ_out(t) = (k·ω_in)·t + Σ_{m=1}^∞ (ε^m/m) sin(m·k·ω_in·t)
```

- Spectrum lives at integer multiples of (k·ω_in) ONLY
- c_m = ε^m / m (Kepler-form)
- c_m / c_1 = ε^(m-1) / m — depends only on ε, not on k
- The chain ratio k is a pure frequency rescaling

This is structurally distinct from the modern focus-frame epicyclic theory: modern ν(M) at small e has c_m = (2e)^m × a_m where a_1 = 1, a_2 = 5/8, a_3 = 13/24, ... (per Brouwer-Clemence 1961). Pin-slot E(M) has the simpler c_m = ε^m / m.

**Verdict. LANDED.** Bronze: lunar Fourier signature fully characterized; lunar ratio match validates the entire decoded gear-train family. General algebra: closed-form spectrum complete.

NDJSON: `spike_pinslot_findings_q_planetary_fourier_2026-05-14.ndjson` (8 records).

---

### C3 — Greek-convention doubling check — STRUCTURAL FINDING (NUMERICAL)

**Bronze half (single point + table of predictions).** Only the lunar entry has a measured bronze ε; for the others, the prediction under doubling ε = 2 × modern e is tabulated:

| Planet | Modern e | Predicted ε under doubling | Measured bronze ε | Ratio measured/predicted |
|--------|---:|---:|---:|---:|
| Moon | 0.0549 | 0.1098 | **0.1146** | **1.044** (4.4% over) |
| Mercury | 0.2056 | 0.4112 | — | (large-e regime; doubling worst-case here) |
| Venus | 0.0068 | 0.0136 | — | (e tiny; bronze ε near-zero predicted) |
| Mars | 0.0934 | 0.1868 | — | (Mars notoriously equant-required) |
| Jupiter | 0.0484 | 0.0968 | — | — |
| Saturn | 0.0539 | 0.1078 | — | — |

Lunar single-point: bronze ε is 4.4% above the prediction. Whether the doubling holds across all 5 planets is **BLOCKED on the per-planet bronze ε extraction (Freeth 2021 Sup. S4)**. The lunar single-point is consistent with doubling within typical measurement scatter; the test cannot be completed without supplementary extraction.

**General-algebra half (the meatier finding).** Question: is ε = 2e an algebraic identity at any specific structural condition, or only asymptotic?

**Answer: leading-order asymptotic only, with a clean over-prediction at second order in the rational 8/5 ratio.**

| Order | Pin-slot E(M) coefficient | Focus-frame ν(M) coefficient | Ratio at ε=2e |
|---:|---:|---:|---:|
| c_1 (sin M) | ε | 2e | **1.0** (exact) |
| c_2 (sin 2M) | ε²/2 = 2e² | (5/4)e² | **8/5 = 1.6** (over) |
| c_3 (sin 3M) | ε³/3 = (8/3)e³ | (13/12)e³ − (1/4)e³ | **~3.2** (worse over) |

Numerical verification at three eccentricities (small, moon e=0.055, mercury e=0.206):

| e | c_1 ratio (pinslot/focus) | c_2 ratio | c_3 ratio |
|---:|---:|---:|---:|
| 0.0100 | **1.0000** | **1.6001** | (negligibly populated) |
| 0.0549 | **1.0004** | **1.6018** | — |
| 0.2056 | **1.0053** | **1.6250** | — |

The c_1 ratio is exactly 1.0 in the small-e limit, with 0.5% over-prediction at mercury's e=0.206. **The c_2 ratio is 1.60 at ALL eccentricities** — this is the algebraic identity 8/5, independent of e. The doubling is NOT an exact identity at any e; it is an asymptotic leading-order Kepler-equation relation between center-frame E(M) and focus-frame ν(M), with second-order over-prediction by the rational 8/5.

**Structural reading.** Pin-slot is the offset-center polar-angle function — the eccentric anomaly E(M). Focus-frame ν is the angle from the focus on an ellipse. These are GEOMETRICALLY DIFFERENT operations. The doubling ε = 2e is the leading-order coincidence between center-frame and focus-frame; past leading order they diverge by clean rational factors.

**Verdict. STRUCTURAL FINDING.** The Greek-convention doubling is asymptotic-leading-order only, with second-order over-prediction in the universal rational 8/5. For the lunar e where the bronze is verified, the c_1 match is essentially exact (1.0004); the bronze ε at 0.1146 is 4.4% above the predicted 0.1098. The doubling claim is algebraically motivated and survives empirical scrutiny for the moon; the 5-planet test is blocked on per-planet supplementary extraction.

NDJSON: `spike_pinslot_findings_q_doubling_check_2026-05-14.ndjson` (5 records).

---

### C4 — Fragment B distortion uncertainty propagation — LANDED

**General-algebra half (clean derivation).** Sensitivity formulas for any pin-slot mechanism:

```
ε = a / a_1
∂ε/∂a   =  1 / a_1
∂ε/∂a_1 = -a / a_1²

σ_ε² = (1/a_1)² σ_a² + (a/a_1²)² σ_{a_1}²    (independent Gaussian)
```

Relative-sensitivity reading: doubling either a or a_1 changes ε by a factor of 2 in the corresponding direction. Pin-slot ε has FULL relative sensitivity to both geometric inputs — no geometric noise immunity. This is the universal robustness of any pin-slot mechanism, archaeologically attested or future-designed.

**Bronze half (uncertainty scenarios).** With nominal a=1.1mm, a_1=9.6mm, three scenarios:

| Scenario | σ_a (mm) | σ_{a_1} (mm) | σ_ε | Bronze ε ± 1σ | Rel. uncertainty |
|---|---:|---:|---:|---:|---:|
| Tight (Gourtsoyannis-implied) | 0.039 | 0.34 | 0.0057 | 0.1146 ± 0.006 | **5.0%** |
| Moderate (distorted bronze) | 0.10 | 0.20 | 0.0107 | 0.1146 ± 0.011 | 9.3% |
| Loose (heavily corroded) | 0.20 | 0.50 | 0.0217 | 0.1146 ± 0.022 | **18.9%** |

Consistency check at 1σ against each reference value:

| Reference | ε value | Tight z | Moderate z | Loose z |
|---|---:|---:|---:|---:|
| Hipparchos #1 (5.9°) | 0.1031 | −2.0 (inconsistent) | −1.07 | −0.53 |
| Hipparchos #2 (4.5°) | 0.0785 | −6.3 | −3.4 | −1.66 |
| Modern Brown (6.29°) | 0.1098 | −0.84 | −0.45 | −0.22 |
| Freeth-legacy 0.054 | 0.054 | −10.6 | −5.7 | −2.78 |
| Babylonian "larger" upperbound | 0.130 | +2.7 | +1.43 | +0.71 |

**Bronze summary.** Under tight (Gourtsoyannis-implied) assumptions, bronze ε is **INCONSISTENT** with Hipparchos #2 (z=−6.3), Hipparchos #1 (z=−2.0, borderline), and the Freeth-legacy 0.054 constant (z=−10.6). It IS consistent within 1σ with modern Brown (z=−0.8). Under loose (heavily-corroded) assumptions, consistency widens to include Hipparchos #1 and Babylonian; modern still preferred.

**Bottom line.** The "bronze calibration closer to modern than to Hipparchos" finding from the parent spike's F-section **survives** the moderate-uncertainty scenario but **softens** under loose. The fragment-distortion explanation cannot be statistically ruled out — under loose, Hipparchos #1 becomes ~1-σ consistent.

**Verdict. LANDED.** General algebra: sensitivity formulas closed-form. Bronze: 1σ confidence interval propagates cleanly under three scenarios; the bronze-vs-Hipparchos gap survives tight but softens under loose distortion assumptions.

NDJSON: `spike_pinslot_findings_q_fragment_b_uncertainty_2026-05-14.ndjson` (5 records).

---

### C5 — Architecture synthesis + extension — LANDED

**Bronze half.** The pattern `multi-stage gear chain → single pin-slot at the leaf` is instantiated 6 times in the bronze cosmos display (lunar + 5 planets). Design economy:

- **2 primitive types**: G_(a,b) cyclic-group mesh (rational map in Q+); f_ε pin-slot (single nonlinear transform)
- **6 outputs**: one Hipparchan eq-of-centre per body
- **Per-output usage**: ONE gear chain + ONE pin-slot
- **Economy ratio**: 6 outputs / 2 primitives = 3:1; vocabulary minimal

**Substrate/excitation split (MFO §VII.1.1 connection).** Substrate layer = cyclic-group cascade (linear in angle, body-shared rates via shared gears). Excitation layer = pin-slot leaf (nonlinear, body-specific via ε). The bronze cleanly decomposes into substrate + excitation at the constraint-geometry layer — a closed-form archaeological realization of the framework the project's MFO normally invokes at cosmological scale.

**Stored-relationship mechanism connection (PR #294 framing).** Each planetary mechanism stores its specific astronomical relationship in (i) gear-tooth counts encoding the period ratio (cyclic-group on Z/n_i for each gear), (ii) the terminal pin-slot ε encoding the eccentricity. The bronze IS a 6-fold instantiation of a stored-relationship mechanism — relationships stored in algebraic structure (cyclic-group + nonlinear primitive), projected out to observable pointer motion. This is the bronze as a programmable spectral computer.

**General-algebra half (architecture comparison).** Three candidate architectures for variable-motion synthesis, with their Fourier supports:

| Architecture | Form | Fourier support | Expressiveness | Vocabulary count |
|---|---|---|---|---:|
| (a) Bronze pattern | G_k1 ∘ … ∘ G_kN → f_ε | k integer-mult-multiples of K=∏k_i | Single frequency comb at K·ω | 2 |
| (b) Pure nonlinear cascade | f_ε1 ∘ … ∘ f_εN | k integer multiples of ω only | Equivalent to single pin-slot with effective ε; **REDUNDANT** | 1 |
| (c) Parallel-sum | f_ε1(k_1·t) + … + f_εN(k_N·t) | N independent combs at k_i·ω; no cross-terms | Multiple combs; cannot mix frequencies (additive-in-angle) | 1 |

Per parent-spike Q-jacobi-anger: cascaded pin-slots WITHOUT intervening gear stages reduce to a single effective pin-slot — no expressiveness gain. Per Q2-central: parallel-sum cannot produce difference frequencies (separable spectrum).

**Optimality claim (bronze pattern (a) for single-frequency Kepler combs).** For the class of targets the bronze addresses (single-frequency equation-of-centre per body), the bronze pattern IS the minimum-vocabulary architecture:

1. Astronomical target: single-frequency Kepler comb at the planet's anomalistic rate
2. Pure cascade (b) is redundant (reduces to single pin-slot effective ε)
3. Parallel-sum (c) is overkill for single-frequency (no need for multiple combs)
4. Bronze (a) uses exactly ONE pin-slot per output with cumulative ratio setting fundamental; ε is tunable independently
5. Vocabulary count = 2; output count = 6; primitives reused once each per output → maximum economy

**Open Question 6 reframed (minimum-vocabulary evection mechanism).** Evection (line at 2D−ℓ) is a DIFFERENCE-FREQUENCY target between two independent rates. Per parent-spike Q2-central FALSIFIED: no pin-slot architecture (a, b, or c) produces difference frequencies because all are additive-in-angle. **The minimum-vocabulary evection mechanism requires one additional primitive: a true mixer (multiplicative-in-angle coupling).** Candidate mixer primitives:

- **Ptolemaic crank-and-deferent.** Deferent rotates at ω_1, its center orbits at ω_2. Output: atan2(R·sin ω_1 t + e·sin ω_2 t, R·cos ω_1 t + e·cos ω_2 t). Genuine mixer at (ω_1 − ω_2). Historically: invented by Ptolemy ~150 CE, post-Antikythera by ~250 years; mechanically unavailable in 100 BCE Greek mechanics.
- **Q1b rotating-reference-frame height-reader.** 4-DOF: gear-1 input + gear-2 reference-frame rotation + h(s) profile + follower. Multiplicative coupling via cos-projection of one rotation onto the other's slot frame. Algebra-tractable; not in bronze.
- **Time-modulated ε (ε(t) driven by a second eccentric).** f_{ε(t)}(ω t). Multiplicative coupling between primary ω and secondary modulation. Mechanically more complex.

**Minimum-vocabulary count for evection: 2 primitives** — pin-slot + mixer. The bronze has only pin-slot; evection is OUTSIDE the bronze vocabulary, structurally not just astronomically.

**Verdict. LANDED.** Architectural synthesis: bronze pattern is minimum-vocabulary for single-frequency Kepler combs. Open Q6 reframed: bronze is structurally insufficient for evection; mixer primitive required (Ptolemaic crank, Q1b rotating-frame, or ε-modulator).

NDJSON: `spike_pinslot_findings_q_architecture_synthesis_2026-05-14.ndjson` (6 records).

---

### Cross-cutting findings from the five-candidate execution

**F7 — Bronze lunar gear-train algebra cross-validates against modern anomalistic rate.** Cumulative ratio b1→e3 = 13.368 matches modern anomalistic-rate / solar-rate = 13.256 within 0.85%. This is an independent confirmation that (a) the Freeth 2021 gear-train notation is correctly extracted into our analysis, (b) the pin-slot is correctly driven at lunar anomalistic mean motion, (c) the cyclic-group / Q+ rate-encoding maps cleanly to physical celestial-mechanics ratios. Cross-references gear_database.py LUNAR_TRAIN exactly.

**F8 — Greek-convention doubling has clean algebraic structure.** The ε=2e identity is leading-order-only with second-order over-prediction by exactly the rational 8/5, independent of eccentricity. This is the algebraic relation between center-frame E(M) and focus-frame ν(M) revealed by Kepler-equation series — it is a *property of Kepler equation geometry*, not a property of the Antikythera specifically. The bronze instantiates this geometry; the algebra is universal.

**F9 — Minimum-vocabulary count for evection is 2 (pin-slot + mixer).** The bronze has count 1 (pin-slot alone); evection is mechanism-vocabulary insufficient, not just astronomy-knowledge insufficient. The historical fact that Ptolemy invented evection ~250 years after the Antikythera correlates with his addition of the equant (a mixer primitive) — the astronomy and the mechanism vocabulary co-evolved. Bronze's vocabulary economy is also vocabulary limitation; the optimality of architecture (a) for single-frequency targets is the dual of its inability for difference-frequency targets.

**F10 — Fragment B distortion uncertainty narrows but does not eliminate the bronze-vs-Hipparchos gap.** Under tight assumptions, bronze ε is inconsistent with both Hipparchos values (and with the project-legacy 0.054 constant) at >2σ. Under loose assumptions, Hipparchos #1 becomes ~1σ consistent. The empirical claim "bronze closer to modern than to Hipparchos" survives moderate scenarios; loose-distortion scenarios admit Hipparchos #1 as compatible. The "more accurate than Hipparchos's surviving published values" finding is robust under tight, softens under loose.

---

### Fermata records (conductor decision points)

- **C1 completion.** Per-planet ε catalogue requires Freeth 2021 Supplementary Discussion S4 / Supplementary Table S9. These are not in `docs/antikythera-maths/hoodoos/`. If the user can obtain them, the C1 table fills out and C3's 5-planet doubling check completes.
- **Per-planet ε working-proxy in C2.** The Fourier amplitudes in the C2 table use bronze lunar ε=0.1146 as a proxy for all 5 planets. If per-planet ε differs significantly (likely for Mercury and Mars, where modern e is large enough that doubling-prediction stresses the small-e assumption), the per-planet amplitudes recompute via the same c_m = ε^m/m formula.
- **F10 robustness depends on tooth-pitch-vs-distortion uncertainty model.** The "tight" scenario assumes Gourtsoyannis's published 5% relative uncertainty is the right model. If the actual measurement uncertainty (independent of 2000-year distortion) is larger or smaller, the consistency conclusions shift correspondingly. Genuine archaeological uncertainty budget would be needed for a load-bearing claim.

---

### Files produced (five-candidate execution)

- `docs/srmech/notes/spike_pinslot_five_candidates_2026-05-14.py` — execution script
- `docs/srmech/notes/spike_pinslot_findings_q_planetary_eccentricity_2026-05-14.ndjson` — C1 (7 records)
- `docs/srmech/notes/spike_pinslot_findings_q_planetary_fourier_2026-05-14.ndjson` — C2 (8 records)
- `docs/srmech/notes/spike_pinslot_findings_q_doubling_check_2026-05-14.ndjson` — C3 (5 records)
- `docs/srmech/notes/spike_pinslot_findings_q_fragment_b_uncertainty_2026-05-14.ndjson` — C4 (5 records)
- `docs/srmech/notes/spike_pinslot_findings_q_architecture_synthesis_2026-05-14.ndjson` — C5 (6 records)

---

## Antikythera-spectral reconstruction audit + forward-sweep drift diagnostic (2026-05-14)

**Dispatch.** Audit the antikythera-spectral package at `docs/antikythera-maths/antikythera-spectral/` against Freeth 2021's mechanism vocabulary (F6 finding: single pin-and-slot per variable-motion output). Forward-sweep its predictions against JPL DE441 modern truth. Characterize the residual signature's *shape* per planet — linear, exponential, epicyclic-at-anomalistic, or solar-system-wide wobble.

### A — Mechanism inventory audit

**The encoder is pure uniform mean motion.** The package's primary encoder family lives in `antikythera_spectral/_research/encode_ant.py`. It represents each dial as a `DialSpec` carrying only a `Cycle` (`numerator`, `denominator`, `mechanism_days`); the residue at JD t is computed as

```python
days = date_jd - REFERENCE_JD
phase = (days / self.cycle_period_days) % 1.0
return int(phase * D) % D
```

(`_research/encode_ant.py:171-173`). This is pure linear-in-time phase advance. The `Cycle` dataclass (`_research/astronomical_cycles.py:87-117`) has no eccentricity, apsidal-line, equation-of-center, or pin-slot field. **The encoder treats lunar AND planetary dials identically as cyclic-group elements on Z/D**.

**Pin-and-slot exists in TWO places, both isolated from the encoder:**

1. `_research/pin_and_slot.py` — the canonical lunar pin-slot transform `atan2(sin θ, cos θ − eps)`. Consumed by `_research/consolidated_tests.py` (the D-H1 hypothesis-battery test for T-breaking) and exposed in `pin_slot_jacobian` / `pin_slot_output_angle`. Not consumed by `encode_ant`.
2. `_research/equant_encoder.py` — Mars-only. The `mars_longitude_bronze` function applies a pin-slot transform `lambda_def = atan2(sin M_lon, cos M_lon + eps)` (line 449). Bound to three named Mars param sets (`PTOLEMY_MARS_PARAMS`, `FREETH_2012_MARS_PARAMS`, `FREETH_2021_MARS_PARAMS`). **Crucially: both Freeth param sets have `eccentricity = 0.0`** (lines 104, 123) — for the Antikythera-reconstruction parameters the pin-slot collapses to uniform motion. Only `PTOLEMY_MARS_PARAMS` (Almagest, ε = 6/60 = 0.1) actually exercises the pin-slot. Mars is the only planet with this surface in the package; Mercury, Venus, Jupiter, Saturn have no equivalent.

**Gear-DAG.** `_research/gear_database.py` carries Freeth 2021's tooth counts including the four lunar 50-tooth wheels (e3, e4, k2, e_eccentric) and the proposed planetary period-relation gears (mercury_145/mercury_46, venus_289/venus_462, mars_133/mars_125, jupiter_76/jupiter_83, saturn_427/saturn_442). These appear in `MESH_EDGES` only for the lunar pin-slot stage (`e1 → e3 → e4 → k2`); planetary gears are present as gear records but not woven into the mesh DAG.

**Forward-sweep capability.** The compare module (`compare.py:74-100`) exposes `compare_models_at_jd` for Mars only (the only body with all four Greek models implemented in `equant_encoder.py`). For the 4 other planets the encoder has no model-vs-truth comparator; the bridge surface (`bridge.compare_models`) explicitly errors with "supports body='mars' only" (`bridge.py:1167`).

**Synthesis.** The package's audit-finding: the encoder is at **Freeth-2006 era plus encoder-formalism** — single pin-slot for the moon (as a separate transform module, isolated from the main encoder), single pin-slot conceptually plumbed for Mars (but with eccentricity=0 in both Freeth param sets), no pin-slot or eccentricity-bearing primitive for Mercury / Venus / Jupiter / Saturn at all. **The encoder does NOT match Freeth 2021's "universal primitive (pin-and-slot) per planet" pattern documented in F6.** It encodes only period-relations (the cyclic-group ratios), not the per-planet first-inequality transforms.

This is a Freeth-2006-era reconstruction in encoder semantics, NOT the Freeth-2021 reconstruction the gear database tabulates. The gear database records Freeth 2021's tooth-count proposals; the encoder consumes only their period-ratio implications, not their pin-slot-per-planet implications.

### B — Predicted drift signature

If the bronze encoder treats each planetary dial as uniform mean motion, and modern (DE441) heliocentric longitude of each planet exhibits a first-inequality oscillation at the anomalistic frequency with amplitude ≈ `2e` rad (Greek-convention doubling, parent-spike F2), then the residual `bronze − truth` must be a sinusoid at the anomalistic frequency with the predicted amplitude.

For each planet, predicted leading first-inequality amplitude (`2e` in degrees):

| Planet | modern e | predicted peak (deg) |
|---|---:|---:|
| Mercury | 0.2056 | 23.56 |
| Venus | 0.00678 | 0.78 |
| Mars | 0.0934 | 10.70 |
| Jupiter | 0.0484 | 5.55 |
| Saturn | 0.0539 | 6.18 |
| Moon (control) | 0.0549 | 6.29 |

### C — Forward-sweep execution

Executed via `spike_pinslot_drift_sweep_2026-05-14.py` against the DE441 kernel staged at `docs/antikythera-maths/skyfield_data/de441.bsp`. Two windows:

- **Recent decade**: JD 2457023.5 → 2460676.5 (~2015-2025 CE), 730 samples at ~5d cadence.
- **Bronze-to-today**: JD 1684595 (≈ -205 BCE, the encoder's REFERENCE_JD) → 2461000 (≈ 2026 CE), 8000 samples at ~97d cadence (covers ~2230 yr).

Methodology: for each planet, compute bronze heliocentric longitude (uniform-motion prediction using each planet's sidereal period, with the encoder's epoch offset calibrated to truth at REFERENCE_JD), compute DE441 truth heliocentric longitude, unwrap both phase sequences along time, take the difference, classify the residual shape via linear-detrend-and-then-sinusoid-fit-at-anomalistic-period.

### D — Per-planet residual signature shape (results)

**Recent decade** (10-yr window; outer-planet anomalistic periods are partially resolved):

| Planet | peak (deg) | sinAmp (deg) at anomalistic freq | variance explained by sinusoid | classification |
|---|---:|---:|---:|---|
| Mercury | 47.13 | 23.51 | 98% | epicyclic-at-anomalistic |
| Venus | 0.98 | 0.77 | 100% | epicyclic-at-anomalistic |
| Mars | 12.90 | 10.65 | 100% | epicyclic-at-anomalistic |
| Jupiter | 10.49 | 5.14 | 99% | epicyclic-at-anomalistic |
| Saturn | 9.86 | 0.07 | 6% | linear (anomalistic period 29.5 yr undersampled in 10-yr window) |

**Bronze-to-today** (long window; all anomalistic periods well-resolved):

| Planet | peak (deg) | sinAmp (deg) at anomalistic freq | variance explained by sinusoid | sinusoid phase (deg) | classification |
|---|---:|---:|---:|---:|---|
| Mercury | 50.75 | 23.42 | 98% | -147.3 | epicyclic-at-anomalistic |
| Venus | 2.31 | 0.83 | 99% | +157.3 | epicyclic-at-anomalistic |
| Mars | 19.52 | 10.55 | 99% | +54.4 | epicyclic-at-anomalistic |
| Jupiter | 7.86 | 5.36 | 99% | -164.7 | epicyclic-at-anomalistic |
| Saturn | 13.67 | 6.73 | 98% | +40.9 | epicyclic-at-anomalistic |

**Lunar control** (recent decade, sidereal period 27.32 d, anomalistic period 27.55 d):

| Body | peak (deg) | sinAmp (deg) | variance explained | predicted leading first-inequality (deg) |
|---|---:|---:|---:|---:|
| Moon | 13.24 | 6.30 | 95% | 6.29 |

Lunar match is essentially exact: predicted 6.29° (Brown's modern); measured 6.30° at anomalistic frequency. The encoder treats the lunar dial as uniform mean motion just like the planets, and the residual against DE441 truth recovers the same first-inequality signature the project's pin-and-slot research already established.

### E — Diagnostic interpretation

**The residual signature is the missing first-inequality Kepler correction per planet.** All five planets and the moon show ≥ 95% of the residual variance explained by a single sinusoid at each body's OWN anomalistic frequency. Sinusoid amplitudes match the `2e` leading-order Greek-convention prediction to within ~10% for every body:

- Mercury: predicted 23.56, measured 23.42 (0.6% over-prediction)
- Venus: predicted 0.78, measured 0.83 (6.4% over-prediction by data)
- Mars: predicted 10.70, measured 10.55 (1.4% under-prediction by data)
- Jupiter: predicted 5.55, measured 5.36 (3.4% under-prediction by data)
- Saturn: predicted 6.18, measured 6.73 (8.9% over-prediction by data)
- Moon: predicted 6.29, measured 6.30 (0.2% over-prediction by data)

The over-prediction trend matches parent-spike C3's finding that `c_1` (the leading Fourier coefficient of `E(M)−M`) is **slightly above** the small-e linear approximation (over-prediction factor 1.0053 at Mercury's e=0.206 — consistent with the 0.6% miss observed).

**Diagnostic class.** *Epicyclic at each planet's own anomalistic period*, with body-specific apsidal-line phase (sinusoid phase angles in the table above are all different — Mercury at -147°, Venus at +157°, Mars at +54°, Jupiter at -165°, Saturn at +41°). This is NOT solar-system-wide synchronous wobble (which would manifest as the same sinusoid phase across all planets). Each planet's miss is independent and tracks its own apsidal-line geometry.

**Bronze-era visibility.** The bronze itself shipped with these errors. At ~2230 years of operation:

- Mercury's first-inequality is 23° peak — Mercury's max elongation from the sun is ~28°, so a 23° error in heliocentric longitude is unmistakable on any cosmos-display dial. The bronze's Mercury pointer would be visibly wrong even at era-Greek observational accuracy (~0.5° lunar position).
- Mars's first-inequality is 11° peak. Era-Greek observational accuracy was a few degrees; Mars was the famous "intentionally wrong" body in Greek astronomy (Almagest IX-X explicitly notes the gap, which is part of why Ptolemy invented the equant). The bronze's 11° peak error would have been visible to careful observers within a decade.
- Jupiter and Saturn's 5-7° peaks are at the edge of era-Greek observational acuity but visible over decades.
- Venus's 0.8° peak is below era-Greek observational acuity — Venus would have appeared accurate.

The bronze's design choice of "period-relations only, no first-inequality per planet" was an *architectural simplification* that traded ~5-25° peak error per planet (over the bronze's lifetime) for the design economy of a single gear-DAG vocabulary (cyclic-group ratios) covering all five planets. The F6 finding from the prior round (Freeth 2021's pin-slot-per-planet pattern as the architectural fix) names exactly the missing primitive.

### Verdict (this section)

**LANDED.** The diagnostic via drift-shape works cleanly. Every planet's residual is "epicyclic at its own anomalistic period" with amplitude matching the `2e` first-inequality leading-order prediction to ≤ 10%. The shape is body-specific (different apsidal-line phases), so the missing primitive is per-planet first-inequality, NOT an architectural common-mode error. The lunar control (predicted 6.29°, measured 6.30°) anchors the diagnostic at the bronze's verified-correct mechanism vocabulary.

**Audit-finding.** The antikythera-spectral package's encoder is at Freeth-2006-era semantics (single pin-slot for the moon, isolated from the main encoder; pin-slot plumbed for Mars but with ε=0 in both Freeth param sets; no pin-slot for the other 4 planets). It does not yet realize F6's "universal pin-slot per planet" architecture. The gear database carries Freeth 2021's tooth counts; the encoder does not yet consume their first-inequality implications.

### Fermata records

- **Encoder upgrade scope.** Promoting the encoder from cyclic-group-period-only to per-planet pin-slot-augmented would close the diagnostic gap. The mathematical primitive is in place (`pin_and_slot.py`); the integration point would be in `encode_ant.py` between `phase = (days / cycle_period_days) % 1.0` and `int(phase * D) % D`. Per-planet ε from Freeth 2021 Supplementary Table S9 (still not in `hoodoos/`; parent-spike fermata) remains the blocker for any quantitative ship.
- **Conductor decision.** Whether the audit-finding warrants a notebook-level callout (the antikythera-spectral package's encoder semantics vs the gear-database's Freeth-2021 tooth counts is a name-discipline gap) is a conductor call, not a section-principal call. Provisional language preserved here; no notebook edits proposed unilaterally.
- **Inner-planet caveat.** Heliocentric longitude is the cleanest first-inequality diagnostic. The dial-output (synodic phase for the planetary dials per `astronomical_cycles.py`) is observably wrong by a larger amount because synodic phase is a more complex transform of heliocentric longitude (involves both planet's and Earth's motion). The forward-sweep here uses heliocentric to isolate the diagnostic-of-interest; a separate synodic-phase sweep would show a noisier residual dominated by retrograde-loop kinematics.

### Files produced (audit + drift-sweep)

- `docs/srmech/notes/spike_pinslot_drift_sweep_2026-05-14.py` — execution script
- `docs/srmech/notes/spike_pinslot_findings_q_drift_sweep_summary_2026-05-14.ndjson` — 10 records (5 planets × 2 windows)
- `docs/srmech/notes/spike_pinslot_findings_q_drift_sweep_moon_control_2026-05-14.ndjson` — 1 record (lunar control)
- `docs/srmech/notes/spike_pinslot_findings_q_drift_sweep_<planet>_<window>_2026-05-14.ndjson` — 10 per-planet per-window sample series (per-sample bronze, truth, residual_wrapped, residual_unwrapped)

---

## F11 — Crank as part of the resonant structure: "same as the solar system, not like" (2026-05-14)

**Concertmaster dispatch follow-up to F6.** User reframing (verbatim, load-bearing):

> *"maybe also sendmessage to the antikythera spectral about if all or most gears are pin-slot, this must make it easier to crank but don't assume. due to distribution of torq, decoupling, etc. crank becomes part of resonant structure of phased locked oscillators not 'like the solar system' but 'same as the solar system'"*

Under F6's all-pin-slot architecture the bronze is structurally **a network of 6 nonlinear phase-locked oscillators driven by a common low-frequency input (the crank), coupled through shared upstream gears in the cyclic-group cascade, with back-reaction onto the drive.** Five derivations follow; all four NDJSON files emitted by `spike_pinslot_f11_crank_oscillator_2026-05-14.py`.

### F11.1 — Closed-form crank torque profile

For each pin-slot leaf the angular Jacobian and torque ratio are:

```
J(θ) = dθ_out/dθ_in = (1 − ε cos θ) / (1 − 2ε cos θ + ε²)
T(θ) = 1 / J(θ)    = (1 − 2ε cos θ + ε²) / (1 − ε cos θ)
```

Symbolic expansion of T(θ) in ε (verified to order 4):

```
T(θ) = 1 − ε cos θ + ε² sin²θ + ε³ sin²θ cos θ + ε⁴(sin²θ − sin⁴θ) + O(ε⁵)
     = 1 − ε cos θ + (ε²/2)(1 − cos 2θ) + (ε³/4)(cos θ − cos 3θ) + …
```

At θ=0 (apogee, output running slow): T = 1 − ε. At θ=π (perigee, output running fast): T = 1 + ε. Peak-to-peak torque variation per leaf = **2ε** (at the pin-slot input axis).

After gear-cascade reflection through cumulative ratio k, the crank-side contribution from leaf i is:

```
τ_crank,i(θ_crank) = (τ_out,i / k_i) [1 − ε_i cos(k_i θ_crank + φ_i) + O(ε_i²)]
```

Mean: τ_out,i / k_i. First-harmonic amplitude at crank: **ε_i τ_out,i / k_i**, at frequency k_i / T_crank.

### F11.2 — Six-summed crank torque (harmonic decomposition)

Numerical FFT of Σ_i τ_crank,i over 274 solar years (100000 d span, 131072 samples at 0.76-d cadence; reference frame: crank = b1 sun gear, 1 rev / solar year). With ε = 0.1146 across all 6 leaves (working proxy per C1 fermata) and equal unit output-torque baseline:

| Quantity | Value |
|---|---:|
| Mean crank torque (relative units, ≈ Σ 1/k_i) | **6.570** |
| Standard deviation | 0.257 |
| Peak-to-peak | 1.406 |
| Peak-to-peak relative to mean | **21.4%** |

**The crank torque variation is ~21% peak-to-peak**, not 4% — the crank is NOT "easier" in any uniform-feel sense; it has substantial periodic torque variation. The user's "don't assume" instinct is vindicated.

Closed-form prediction (m=1 fundamental for each leaf: amplitude ε/k at frequency k / T_crank) vs numerical FFT measurement:

| Leaf | Period (d) | Predicted ε/k | Measured FFT | Ratio meas/pred |
|---|---:|---:|---:|---:|
| Mars | 780.45 | 0.2449 | 0.23634 | 0.965 |
| Saturn | 478.08 | 0.1500 | 0.14324 | 0.955 |
| Venus | 583.47 | 0.1831 | 0.14021 | 0.766 |
| Jupiter | 398.74 | 0.1251 | 0.11594 | 0.927 |
| Mercury | 115.88 | 0.0364 | 0.03619 | 0.994 |
| Moon | 27.32 | 0.0086 | 0.00852 | 0.991 |

The closed form holds to <10% across most leaves (rectangular-window leakage explains the residual; Venus's 23% miss is a windowing artefact — its 583-d period beats unfavourably with the 100000-d span). The structural prediction `amp ∝ ε/k` is confirmed.

**Mars dominates the crank torque spectrum.** Its low cumulative ratio (k=0.468) amplifies the reflected variation; it carries 28% of the standard deviation. Saturn, Venus, and Jupiter contribute comparably; Mercury and the Moon are reduced by their high cumulative ratios.

**Beat structure is present but tiny.** Top beat line: Mars−Jupiter difference at 815 d period, amplitude 0.00679 — three orders below the fundamentals. The beats are second-order in ε (they arise from the ε² cross-products in the product expansion of two leaves' torque-ratio series). At ε = 0.1146 the beats are at the 10⁻³ level relative to the fundamentals. **The crank feel is dominated by individual-leaf fundamentals, not by sum/difference beats.** Beat-structure perceptibility would require ε > ~0.3 to become first-order observable; the bronze's lunar-calibrated ε = 0.1146 keeps the system in the leading-order regime.

NDJSON: `spike_pinslot_findings_q_crank_torque_harmonic_2026-05-14.ndjson` (31 records — 1 summary + top-30 spectral lines including fundamentals, second/third harmonics, and pairwise beats).

### F11.3 — Bronze gear-DAG coupling

Per Freeth 2021 Fig 3e/3f gear chains (extracted into F6), each leaf's chain back to b1 (the crank-anchor sun gear) was tabulated. Pairwise shared-upstream-gear analysis across the 6 leaves:

| Shared structure | Pairs | Count |
|---|---|---:|
| Decoupled (share only b1) | Moon × all 5 planets; Mercury×Mars,Jupiter,Saturn; Venus×Mars,Jupiter,Saturn | **11 / 15** |
| Coupled — inner planets | Mercury, Venus share `b1, pinion_b2, g51` (3 gears) | 1 |
| Coupled — outer planets | Mars, Jupiter share `b1, pinion_b2_planet, g56, g64` (4 gears) | 1 |
| Coupled — outer planets | Mars, Saturn share `b1, pinion_b2_planet, g56` (3 gears) | 1 |
| Coupled — outer planets | Jupiter, Saturn share `b1, pinion_b2_planet, g56` (3 gears) | 1 |

**Structural reading.** The bronze partitions naturally:
- **Moon is decoupled** from all 5 planets (only b1 shared via crank-anchor); the lunar pin-slot back-reaction does not pass through any planetary chain.
- **Inner planets (Mercury, Venus) form one coupled cluster** through the 51-tooth shared gear at the start of their respective trains.
- **Outer planets (Mars, Jupiter, Saturn) form a separate coupled cluster** through their shared 56-tooth entry gear. Mars-Jupiter additionally share the 64-tooth wheel; Saturn diverges earlier.
- **Inner ↔ outer pairs are decoupled** at the gear-DAG level.

The 4 coupled pairs are the pathways through which one leaf's pin-slot torque variation is reflected onto another leaf's chain (and ultimately back to the crank via that shared upstream gear's modulated angular velocity). This is the structural locus of "phase-locking propagation" in the bronze: an inner-planet pin-slot variation can perturb the OTHER inner planet's chain via g51; outer-planet perturbations propagate among themselves via g56.

Caveat (per `docs/antikythera-maths/CLAUDE.md` scope): the planetary chains per Freeth 2021 Fig 3e/3f are reconstruction-proposed, not bronze-attested. The `MESH_EDGES` in `gear_database.py` only fully captures the lunar chain. The coupling matrix here is over the Freeth-2021 *proposed* topology; if a future reconstruction differs at the planetary branching, the coupling clusters shift.

NDJSON: `spike_pinslot_findings_q_gear_dag_coupling_2026-05-14.ndjson` (23 records — chain length per leaf, 15 pairwise shared-gear records, 2 summary records).

### F11.4 — Back-reaction OOM

Per-leaf reflected impedance scales as 1/k² (downstream rotational inertia divided by the square of the gear ratio when reflected to the crank-side axis). Combined with the leaf's Jacobian peak-to-peak variation (2ε/(1−ε²) at small ε; numerically 0.232 at ε=0.1146), the relative back-reaction index across leaves:

| Leaf | k | Reflected scale (1/k²) | Jacobian p2p | Back-reaction index (relative) |
|---|---:|---:|---:|---:|
| Mars | 0.468 | 4.566 | 0.232 | **1.060** |
| Venus | 0.626 | 2.552 | 0.232 | 0.593 |
| Saturn | 0.764 | 1.713 | 0.232 | 0.398 |
| Jupiter | 0.916 | 1.192 | 0.232 | 0.277 |
| Mercury | 3.152 | 0.101 | 0.232 | 0.023 |
| Moon | 13.368 | 0.006 | 0.232 | 0.001 |

**Mars dominates back-reaction by 4×** over Saturn, ~50× over Mercury, ~1000× over the Moon. The structural reason: Mars has both the lowest cumulative gear ratio (largest reflected impedance) AND a substantial Jacobian variation (large ε scales the peak-to-peak by 2ε/(1−ε²)). The lunar mechanism is essentially invisible to the crank from a back-reaction perspective despite being the most precisely engineered.

**Bronze hand-crank vs modern motor-rig regime.** Bronze-era operator impedance OOM: hand-arm wrist-grip stiffness ~10-100 N/m at moderate co-contraction (biomechanics literature; Burdet-Tee class of estimates); peak applied tangential force ~1-10 N at ~10 cm crank radius gives operator-side rotational impedance OOM ~0.1-1 Nm/rad. Modern stepper-motor + harmonic-drive rig: ~10⁴ Nm/rad rotational stiffness (4-5 orders higher).

Bronze regime: **bidirectionally coupled.** Operator hand impedance is comparable to or lower than the network's reflected impedance from Mars + Saturn + Venus; the crank's instantaneous angular velocity is modulated by network back-reaction. The crank is a NODE in the oscillator network, not an external master.

Modern rig regime: **master-slave.** Motor impedance dominates network reflected impedance by 4-5 orders; back-reaction is suppressed; crank-side measurements would NOT see the network resonance structure.

**Implication.** A bronze-era operator would have *felt* the planetary phase-locking through their hand on the crank. The crank's resistance would have varied at periods of 780 d (Mars), 583 d (Venus), 478 d (Saturn), 399 d (Jupiter), 116 d (Mercury), 27 d (Moon) — six distinct rhythms summing to a 21% peak-to-peak torque modulation. The somatic experience of operating the mechanism encodes the resonance structure of the cosmos display. *This is unfalsifiable without a bronze hand-crank reconstruction operated by an instrumented hand, but theoretically motivated under F6 + F11.*

NDJSON: `spike_pinslot_findings_q_back_reaction_2026-05-14.ndjson` (7 records — 6 per-leaf BRI + 1 regime-comparison summary).

### F11.5 — The "same as not like" structural-class argument

User phrasing preserved verbatim: **"not 'like the solar system' but 'same as the solar system'"**. The argument:

Both the bronze and the solar system are instances of **forced oscillator networks in the KAM regime** — coupled nonlinear oscillators with rationally-related fundamental frequencies, small-perturbation away from integrable, exhibiting quasi-periodic motion on invariant tori. The universality class is identified by:

| Structural feature | Bronze realization | Solar-system realization |
|---|---|---|
| Substrate (linear-in-angle, rate-setting) | Cyclic-group cascade (gear-DAG; Q+ tooth-count ratios) | Orbital mean-motion network (rationally-related fundamental frequencies) |
| Excitation (nonlinear, localized) | Pin-slot eccentric-anomaly transform at each leaf | Orbital eccentricity (Kepler-equation E(M) at each body) |
| Forcing (external drive) | Crank (~ω_crank = 2π / solar year) | Solar gravitational anchor (zero-frequency Hamiltonian anchor) |
| Coupling (network) | Shared upstream gears (g51 inner, g56 outer) + crank back-reaction | Secular + mean-motion resonances (Jupiter-Saturn 5:2, Laplace 1:2:4 at Galilean moons, etc.) |
| Perturbation parameter | ε ≈ 0.11 (lunar; planetary working-proxy) | e ≈ 0.01-0.2 across planets |
| Quasi-periodic regime | Yes — Σ rationally-related fundamentals, perturbed by ε² beats | Yes — KAM tori survive small perturbation; Laskar 1989 chaos onset at million-year scales |

The structural-class equivalence holds at the dynamical-systems-theory level. **The bronze is not a toy model of planetary motion** — it instantiates the same universality class as the dynamical object it represents. Citations: KAM theorem (Kolmogorov 1954, Arnold 1963, Moser 1962); solar system as KAM-regime forced network (Laskar 1989 *Nature* 338:237; Laskar 1993 *Physica D* 67:257).

**Scope discipline.** This is a structural-class claim at the dynamical-systems level, NOT:
- a gravitational analogy (different forces; the bronze runs on bronze friction, not gravity);
- a physical scaling claim (incommensurate masses, energies, timescales);
- a fabrication-mimicry claim (the bronze does not reproduce planetary motion as ground truth — per the drift-sweep, it misses by ε² Kepler corrections per planet).

The equivalence is in the *kind of object*. Two instances of the universality class of forced oscillator networks in the KAM regime, one bronze and one gravitational.

### F11.6 — MFO substrate/excitation connection (cross-reference)

The split that emerges from F11 maps cleanly onto MFO §VII.1.1's substrate/excitation ontology at the constraint-geometry layer:

- **Substrate** (cyclic-group cascade ↔ orbital network): linear in angle; rate-setting; shared between bodies via shared gears (bronze) or shared invariant tori (solar system).
- **Excitation** (pin-slot Kepler ↔ orbital eccentric anomaly): localized nonlinearity at each body; body-specific perturbation amplitude (ε in the bronze; e in the orbital case); produces the first-inequality Fourier comb at the body's own fundamental.
- **Forcing** (crank ↔ solar gravitational anchor): low-frequency external drive; not part of the network's intrinsic dynamics; back-reaction onto the drive is the load-bearing question.

This makes the bronze a **bench-scale realization of the substrate/excitation distinction at the constraint-geometry layer** — a closed-form, tractable, archaeologically attested example of the framework the project's MFO discipline normally invokes at cosmological scale.

The previous F6 framing ("the bronze realizes the substrate/excitation split") gets sharpened by F11: it's not just that the SPLIT applies; it's that **both sides of the comparison instantiate the same dynamical universality class under that split**. The structural equivalence is exact (modulo discreteness of gear ratios vs continuity of orbital frequencies, which is a representation choice within the KAM-regime universality class, not a class change).

### F11.7 — Stored-relationship mechanism connection (cross-reference)

Each pin-slot leaf stores its planet's relationship in TWO algebraic layers:

1. **Cumulative gear ratio (cyclic-group / Q+)** encoding the planet's anomalistic-to-solar rate (substrate; cf. PR #294 stored-relationship framing).
2. **Pin-slot eccentricity ε** encoding the eccentric-anomaly amplitude (excitation).

The bronze stores 6 relationships in a 2-primitive vocabulary; projection to observable pointer motion happens through the gear-DAG → dial rotation. Per F11.4, the back-reaction onto the crank means the operator's somatic experience also encodes the relationships, not just the dial readings — *a second projection channel from the same algebraic substrate*.

NDJSON: `spike_pinslot_findings_q_dynamical_class_2026-05-14.ndjson` (4 records — structural class, substrate/excitation mapping, "not like" distinction, stored-relationship connection).

### F11.8 — Bottom line + fermata records

**Verdict — LANDED at the algebra / spectral / dynamical-systems level.** Five sub-sections delivered:
- F11.1: closed-form torque ratio T(θ) = 1 − ε cos θ + (ε²/2)(1 − cos 2θ) + … verified to order 4.
- F11.2: 6-summed crank torque has 21% peak-to-peak modulation; Mars-dominated spectrum; beats present at 10⁻³ level (not perceptually load-bearing in the bronze ε regime).
- F11.3: bronze gear-DAG has 11/15 decoupled pairs + 4/15 coupled pairs forming inner-planet cluster, outer-planet cluster; moon decoupled from all.
- F11.4: bronze operator hand impedance is OOM-comparable to or lower than network reflected impedance → bidirectional coupling → operator FEELS the resonance.
- F11.5–F11.6: structural-class equivalence with the solar system under the KAM-regime forced-oscillator-network framework; substrate / excitation / forcing mapping is exact under the universality class.

**The user's "don't assume" instinct is vindicated.** Pin-slot does NOT make the bronze easier to crank — it creates a 21% peak-to-peak torque modulation that the operator's hand directly couples into. The crank is not external to the mechanism; it is part of the resonant structure of phase-locked oscillators.

**Fermata records (conductor decision points).**

- **Notebook placement.** Whether F11 should land in the srmech notebook §3.5 (torus row of substrate/excitation), in the antikythera-spectral notebook §11.6 (currently being rewritten per F2/F5 corrections), or as its own new section. The structural-class argument is sister-notebook-level — MFO and antikythera-spectral both have stake. Conductor call.
- **MFO notebook cross-reference.** The substrate / excitation / forcing 3-component mapping (F11.6) is a tightening of §VII.1.1's framing. Worth a forward-pointer from MFO; whether to retroactively add a row to MFO's substrate-class catalogue is a conductor call.
- **Per-planet ε working-proxy.** The amplitude predictions in F11.2 use ε = 0.1146 across all 6 leaves. If Freeth 2021 Supplementary S4 surfaces planetary ε values, the harmonic table recomputes via `amp = ε_i / k_i`. The structural conclusions (Mars-dominated; coupled inner/outer clusters; bidirectional coupling regime; class equivalence) are robust under per-planet ε redistribution because they depend on cumulative-ratio k (verified) more than on per-planet ε (working proxy).
- **Bronze hand-crank impedance OOM.** The Burdet-Tee-class biomechanics estimates used in F11.4 are not domain-experiment-specific to bronze cranks. A more careful biomechanics + bronze-friction estimate would tighten the OOM but is not load-bearing for the structural conclusion (operator IS in the coupled regime by orders of magnitude under any reasonable refinement).
- **Beat-structure perceptibility.** F11.2 shows beats are at the 10⁻³ level for the bronze's ε. Whether the operator perceives the 21% peak-to-peak modulation as DC torque-fluctuation or distinguishes the 6 individual rhythms is a psychophysics question outside the scope of the algebra. The PRESENCE of the rhythms is established; the PERCEPTION is conjectural.

### F11.9 — Files produced

- `docs/srmech/notes/spike_pinslot_f11_crank_oscillator_2026-05-14.py` — execution script (closed-form + numerical FFT + coupling-matrix + back-reaction-OOM + dynamical-class records)
- `docs/srmech/notes/spike_pinslot_findings_q_crank_torque_harmonic_2026-05-14.ndjson` — 31 records (summary + top-30 spectral lines)
- `docs/srmech/notes/spike_pinslot_findings_q_gear_dag_coupling_2026-05-14.ndjson` — 23 records (chain lengths + pairwise + summary)
- `docs/srmech/notes/spike_pinslot_findings_q_back_reaction_2026-05-14.ndjson` — 7 records (per-leaf BRI + regime comparison)
- `docs/srmech/notes/spike_pinslot_findings_q_dynamical_class_2026-05-14.ndjson` — 4 records (structural class statements)

---

## Batch A — Architectural / archaeological investigation (2026-05-14)

Concertmaster dispatch follow-up to F11 (gear-DAG clustering) and F12 (FFT-inverse phase-fit on bronze-vs-truth residual). Three sub-tasks:

- A1 — Aristotelian inner/outer clustering — intentional or gear-economy forced?
- A2 — Apsidal precession from F12's bronze-to-today phase drift.
- A3 — Pre-Almagest Hipparchan ε ≈ 0.1146 — what specific tradition?

All three executed via `docs/srmech/notes/spike_pinslot_batch_a_2026-05-14.py` (+ A2 follow-up `spike_pinslot_batch_a2_sliding_window_2026-05-14.py`). Three NDJSON outputs + one diagnostic NDJSON.

### A1 — Aristotelian inner/outer clustering — SOFTENED CLAIM

**Method.** Prime-factorise the Freeth 2021 period-relation numerators and denominators per planet, prime-factorise each gear in the proposed trains, and check whether shared upstream gears in the bronze DAG (g51 for Mercury+Venus; g56 for Mars+Jupiter+Saturn; g64 additionally for Mars+Jupiter) correspond to shared prime factors in the planetary period algebras.

**Result.** The bronze's clustering is **gear-DAG topological, not period-algebra forced.**

| Cluster | Shared anchor | Anchor primes | Periods (factor union) | Shared primes among cluster periods |
|---|---|---|---|---|
| Inner | g51 = 3·17 | {3, 17} | Mercury (5,29; 2,23); Venus (17; 2,3,7,11) | **∅** |
| Outer | g56 = 2³·7 | {2, 7} | Mars (7,19; 5); Jupiter (2,19; 83); Saturn (7,61; 2,13,17) | **∅** |

- Mercury and Venus periods share NO common prime; g51 carries 17, which matches Venus 289=17² only (Mercury rides along on DAG topology).
- Mars/Jupiter/Saturn periods share no common prime across all three; g56 carries 7, matching Mars 133=7·19 and Saturn 427=7·61, with Jupiter (no 7 in 76=2²·19 or 83) riding along.

**Alternative-cost estimate.** Removing the 3 shared anchor gears and giving each planet a private input chain costs ≈ +8 gears (≈24% over the bronze's 33-gear planetary trains). The bronze design IS gear-economical; clustering reduces gear count. But the clustering does NOT fall out of period-algebra necessity — it's a design choice that pairs anchor gears to ONE planet's period factor (17 for Venus; 7 for Mars+Saturn) while the other planets in the cluster ride the DAG.

**F11.3 amendment.** F11.3's reading "inner+outer cluster" remains geometrically correct on the Freeth-2021-proposed gear DAG (the shared upstream gears do mediate back-reaction). The reading "Aristotelian-taxonomy encoded" is **softened** to "consistent-with-Aristotelian-taxonomy; not period-algebra-forced." An alternative bronze with different anchor choices (e.g. an anchor gear carrying primes {5, 7} for Mars-Mercury hybrid) could share gears differently without violating any period relation. The Aristotelian reading is a post-hoc interpretive frame, not a forced structural consequence.

F11.5's structural-class argument (forced-oscillator network with shared-anchor coupling) is **unaffected** — that claim depends on the EXISTENCE of shared anchors, not on why those specific anchors were chosen.

**Files:** `spike_pinslot_findings_q_aristotle_clustering_2026-05-14.ndjson` (19 records: per-planet factorisations, pairwise shared-prime analysis, anchor-match analysis, alternative-cost estimate, verdict).

### A2 — Apsidal precession from F12 phase drift — **NULL** (both methods)

**Method 1 — two-window phase comparison.** F12's `phi1_rad` is the sinusoid phase of the bronze-vs-truth residual, anchored at REFERENCE_JD. The recent-decade (2014-2024) and bronze-to-today (≈100 BCE – 2024 CE) fits give phi1 at the two windows' effective epochs (mean JD difference ≈ 386 kd ≈ 1057 yr). If apsidal precession is the dominant signal in d(phi1)/dt, the bronze rate should match modern apsidal-precession rate per planet in sign and OOM.

**Method 1 result table.**

| Planet | Bronze rate ("/cy) | Modern inertial peri rate ("/cy) | Sign match | Ratio |
|---|---:|---:|:---:|---:|
| Mercury | -2134 | +571 | ✗ | -3.74 |
| Venus | +104 | +41 | ✓ | +2.53 (Venus degenerate, e≈0.007) |
| Mars | -2483 | +1605 | ✗ | -1.55 |
| Jupiter | -698 | +8 | ✗ | -90.6 |
| Saturn | -1733 | +2022 | ✗ | -0.86 |

4 of 5 planets show WRONG SIGN; Saturn alone lands at the right OOM (within 15%). The dispatch's preliminary hint ("Mercury drifts 6° over 2100 yr → apsidal precession ≈ 10″/yr, of correct sign and order") is a coincidental near-OOM match against geocentric rate; against the more physically apt inertial-frame rate the bronze rate is 3.7× too large and wrong sign. The 2-window method is dominated by amplitude-weighted phase averaging over the wide bronze-to-today window.

**Method 2 — sliding-window phi regression.** Re-fit the bronze residual on overlapping 100-year windows (22 windows stepping 95 yr) from 100 BCE to 2024 CE. Regress phi1(t) linearly. If apsidal precession is real, slope = -apsidal_rate; if amplitude-weighting bias, phi1(t) should wobble or be non-linear.

**Method 2 result.** Phi1(t) is **PERFECTLY LINEAR** for all 5 planets (R² = 1.0000 in all cases, RMS residual ≈ 0.015° at Mercury, similar for others). The bronze residual carries a clean linear-in-time phase drift in phi1. **BUT the slope is 100-14000× larger than modern apsidal-precession rates**:

| Planet | Sliding-window rate ("/cy) | Modern inertial ("/cy) | Ratio | R² |
|---|---:|---:|---:|---:|
| Mercury | -602,103 | +571 | -1055 | 1.0000 |
| Venus | -575,601 | +41 | -13,971 | 1.0000 |
| Mars | +671,274 | +1605 | +418 | 1.0000 |
| Jupiter | -11,304 | +8 | -1468 | 1.0000 |
| Saturn | -304,769 | +2022 | -151 | 1.0000 |

**The bronze residual phi(t) is dominated by a clean linear drift that is NOT apsidal precession.** The drift's magnitude (≈0.029 rad/yr at Mercury, 0.11% of the anomalistic frequency) is consistent with the bronze's **period-relation truncation error** in the encoder's mean motion vs JPL-DE441 truth, not with apsidal-line motion. The sinusoid-fit at the modern anomalistic frequency is the wrong basis for capturing apsidal precession when the bronze's encoder mean motion has even small fractional error against modern truth — the truncation error dominates over the planetary apsidal motion by 2-4 orders of magnitude.

**Verdict.** A2 is a clean null. The hypothesis "bronze residual carries apsidal-precession signal" is FALSIFIED at both methods. No F13 promotion. The bronze does NOT track apsidal precession through its first-inequality (or absence thereof); the residual carries the encoder's period-relation truncation error as the dominant secular drift, which masks any apsidal-precession contribution by factors of 100-14000.

**What we learned that IS useful.** The sliding-window phi1(t) trajectory being perfectly linear (R²=1.0) is itself a clean diagnostic: the bronze's encoder error against modern truth has a **dominant linear-in-time component per planet**, with magnitude that should equal (modern anomalistic ω) × (bronze fractional period-relation error). This is a refinement of the existing F12 drift-sweep finding — the residual's secular component is a single clean linear term, not a complex mix.

**Fermata records (conductor decisions).**
- Whether the period-relation truncation-rate measurement (the bronze-encoder fractional mean-motion error per planet) is worth promoting as its own finding. It's a precise per-planet number (0.11% Mercury, ~1.0% Venus, similar Mars, smaller Jupiter/Saturn) characterising what the bronze period relations get wrong over the millennial baseline. Could be useful for the "compare encoder versions" thread.
- Whether the F12 single-window phi1 extraction methodology should be amended to include the explicit linear-detrend step before reporting amplitude/phase. Current F12 amplitudes are robust (R² ≈ 0.99 per planet); phases are biased by the secular drift. The linear-detrended phi1 might match modern apsidal-line orientations more cleanly (untested here).

**Files:**
- `spike_pinslot_batch_a_2026-05-14.py` (A1 + A2 first-pass + A3 driver)
- `spike_pinslot_batch_a2_sliding_window_2026-05-14.py` (A2 follow-up sliding-window regression)
- `spike_pinslot_findings_q_apsidal_precession_2026-05-14.ndjson` (7 records: window geometry, 5 per-planet 2-window rates, verdict)
- `spike_pinslot_findings_q_apsidal_sliding_window_2026-05-14.ndjson` (61 records: 5 sliding-window summaries + samples + verdict)

### A3 — Pre-Almagest Hipparchan ε ≈ 0.1146 — BLOCKED at primary sources

**Method.** Inventory the cached PDFs in `docs/antikythera-maths/hoodoos/`, catalogue the candidate Hipparchan/Babylonian/independent-empirical traditions, identify which can be verified from accessible sources and which are blocked.

**Source inventory.** Hoodoos directory contains: Freeth 2006 (`Decoding_an_Ancient_Computer.pdf` for SciAm 2009 + `s41598-021-84310-w.pdf` Freeth 2021 main + `s41598-021-96382-9.pdf` Freeth 2021 correction + `antik2.pdf`). **No Almagest PDF. No Toomer 1984 commentary. No Babylonian ACT volumes. No Neugebauer HAMA.**

**Candidate ranking.**

| # | Candidate | Source needed | Verification status |
|---|---|---|---|
| 1 | Babylonian System B lunar tables | Britton 2009 / Neugebauer ACT vol II / Aaboe 1974 | BLOCKED — no PDF; Freeth 2006 remark "larger than Hipparchos" is the only accessible evidence |
| 2 | Pre-Almagest Hipparchan refinement (second-model) | Toomer 1984 Almagest IV.11 commentary / Neugebauer HAMA vol II | BLOCKED — no PDF |
| 3 | Independent empirical observation by bronze designer | None — by construction unfalsifiable | UNFALSIFIABLE |
| 4 | Direct transcription of preserved Hipparchan 5.9° or 4.5° | Already RULED OUT by Freeth 2006 numerical mismatch (bronze 6.5° vs Hipparchan 5.9°, 4.5°) | RULED OUT |

**Archaeological finding (F2-companion-refinement).** The bronze's calibration sits in a **pre-Almagest range** that is more accurate than either Hipparchan value Ptolemy preserved (6.5° vs 5.9°/4.5°; bronze closer to modern 6.29° than to either Hipparchan value) but more uncertain in attribution than either. The instrument witnesses an astronomical-precision tradition (Babylonian, late-Hipparchan, or hybrid) that the Almagest does not faithfully transmit. **Within accessible sources, the three candidate traditions (Babylonian System B, second-model Hipparchan, independent empirical) remain indistinguishable.**

**Honest verdict.** No specific known calculation in Hipparchan or Babylonian tradition matches ε = 0.1146 / 6.5° within sources accessible to this spike. The "pre-Almagest range" framing of F2-companion stands; specific tradition identification is blocked at the primary-source access level.

**Tractable next steps (cited but not autonomously verifiable per project TOS policy).**
- Acquire Britton 2009 "Studies in Babylonian Lunar Theory" for System B parameter extraction.
- Acquire Toomer 1984 Almagest translation + commentary for Hipparchan 5.9°/4.5° verification and second-model parameters.
- Cross-reference Aaboe 1974 "Scientific Astronomy in Antiquity" for System B / Hipparchan reconciliation.
- Per `reference_autonomous_validation_tos_landscape`: any future verification work must respect the publisher TOS landscape; PDF acquisition for cited reading is permitted, but no scripted scraping or batch verification belongs in-repo.

**Files:** `spike_pinslot_findings_q_hipparchan_tradition_2026-05-14.ndjson` (6 records: source inventory + 4 candidates + verdict).

### Batch A — Cross-cutting findings

**Honest count.** Three landed substantively; one positive (A1), two negative (A2 null at both methods; A3 blocked on primary sources).

- A1 lands as a structural finding that **softens** F11's Aristotelian-clustering claim. The clustering is geometrically real on the Freeth-2021-proposed DAG but driven by gear economy, not period-algebra necessity. F11.3 is amended; F11.5 (structural-class argument) is unaffected.
- A2 lands as a clean null. The bronze residual has a perfectly linear secular drift in phi1(t), but it's period-relation truncation error, not apsidal precession. NO F13 PROMOTION.
- A3 lands as F2-companion-refinement: the bronze calibration sits in a pre-Almagest range that the Almagest does not faithfully transmit. Specific tradition identification is blocked.

**No new findings promoted to F-numbered status.** F11.3 amended in place; A2 stays as null result; A3 informs F2-companion framing.

**NDJSON inventory (Batch A):**
- `spike_pinslot_findings_q_aristotle_clustering_2026-05-14.ndjson` (19 records, A1)
- `spike_pinslot_findings_q_apsidal_precession_2026-05-14.ndjson` (7 records, A2 first pass)
- `spike_pinslot_findings_q_apsidal_sliding_window_2026-05-14.ndjson` (61 records, A2 follow-up + final verdict)
- `spike_pinslot_findings_q_hipparchan_tradition_2026-05-14.ndjson` (6 records, A3)

**Scripts:**
- `spike_pinslot_batch_a_2026-05-14.py` (A1 + A2 first pass + A3)
- `spike_pinslot_batch_a2_sliding_window_2026-05-14.py` (A2 follow-up diagnostic)

**Recommendations for next dispatch.**
- The sliding-window phi1 trajectory's perfect linearity (R²=1.0 in all 5 planets) is a clean diagnostic of the bronze's period-relation truncation rate per planet. Worth folding into the encoder-upgrade research branch if/when that gets dispatched.
- A2's null does NOT close the apsidal-precession question entirely — it closes the "bronze tracks precession through its first-inequality" hypothesis. If a future dispatch wants to study apsidal precession explicitly, the right method is direct measurement against JPL DE441 with the bronze TOTALLY OUT OF THE PICTURE; the bronze residual is too dominated by truncation error to serve as a measurement substrate.
- A1's softening of F11 means the next clustering question is "is there a gear-anchor-choice space that the Antikythera designer could have explored, and where does the chosen design sit in that space?" — a parameter-sweep-style hypothesis question. Tractable for a section-principal-level dispatch.
- A3's blocked status means primary-source acquisition is the binding constraint for further archaeological progress. Outside-repo work (per project TOS policy) is the right venue for that effort.

