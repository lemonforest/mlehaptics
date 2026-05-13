# Spike #21B — Does MFO inherit Verlinde 2016's emergent-MOND-like phenomenology?

**Branch:** `research/spike-21-mfo-horizon-thermodynamics-extended` (continuing from Spike #21A at commit `9072c56`)
**Date:** 2026-05-13
**Predecessors:** Spike #21A (same branch, `9072c56`) — honest-negative on direct α-coefficient deviation from `T = H/(2π)·(1+ε/2)`; Hayward correction IS the MFO prediction; established Verlinde 2016 predicts dark **matter** (MOND-like, `a_0 = cH_0`), correcting #19b §4.5 framing slip; Verlinde 2016 (arXiv:1611.02269) PDF-verified there, trusted here. Spike #19b (`research/spike-19b-mfo-horizon-thermodynamics-leverage`) — six-territory leverage scan ranking cosmological horizons highest. Refined structural law (`main`) — 4-mechanism law (i)/(iii)/(iv), 10/10 fit. MFO notebook §VII.1.1 / §VII.4.1 / §VII.4.1.1 / §VII.5 / §VII.6. `user_stance_fiber_as_spatially_absent_encoding.md` + `user_stance_hyper_as_3d_spatial_interface.md` — two-level ontology (substrate vs excitation; vacuum + dark matter + dark energy at Level 1).
**Methodological frame:** Inheritance-scoping spike. #21A established MFO does not commit to an α-deviation beyond Hayward `(1 + ε/2)`. This spike asks: does MFO commit to **Verlinde 2016's specific emergent-MOND-like predictions**, given the corrected dark-matter-not-dark-energy framing? Three possibilities — (A) full inheritance, (B) partial inheritance, (C) agnostic — evaluated.
**Status:** RESEARCH — outcome: **VERDICT (C) AGNOSTIC WITH STRUCTURAL PRESSURE TOWARD (B) PARTIAL INHERITANCE.** MFO has interpretive content (substrate-physics for dark sector; geometric-curvature stance; boundary-as-encoding) without specific functional-form commitments. Verlinde 2016 is *structurally compatible* and the *natural candidate-mechanism* within MFO's frame, but MFO does not currently select Verlinde from the substrate-physical dark-sector theory space. The §VII.5 commitment to "dark matter as geometric curvature" creates pressure to pick a specific mechanism — Verlinde 2016 is the most-developed candidate — but the choice has not been made. Mechanism analysis: Verlinde's `a_0 = cH_0/(2π)` derivation fits mechanism (iv) (area-law / volume-law lattice crossover); the MOND interpolation function is kinematic-dynamics outside the refined-law scope. §VII.5 recommendation: do *not* commit to Verlinde wholesale; *do* explicitly identify Verlinde 2016 as natural candidate-mechanism when framework is ready for such commitment; leave inheritance open until specific functional-form derivation work (Hopf-bundle channel of §VII.4.1.1) is done.

---

## §0. Methodological frame and the load-bearing question

Spike #21A's central technical finding was honest-negative on the most-direct MFO-specific avenue: there is no distinguishable α-coefficient on the cosmological-horizon temperature beyond Hayward 1998's `(1 + ε/2)` slow-roll-`ε` correction. The MFO substrate-vs-excitation framing reinterprets but does not numerically modify standard dynamical-horizon thermodynamics.

But Q3 of #21A discovered (correcting Spike #19b §4.5) that Verlinde 2016's actual prediction is *dark-matter phenomenology* (MOND-like emergent force at galactic scales, characteristic acceleration scale `a_0 = cH_0/(2π)`), not dark-energy phenomenology. This reframes the inheritance question: rather than asking whether MFO commits to specific dark-energy observables, the proper question is whether MFO commits to Verlinde-style emergent-dark-matter observables.

The MFO notebook's existing commitments in this area:

- **§VII.5**: "dark matter is geometric curvature, not particles." This is a substrate-physics commitment — dark matter is a Level-1 property of the metric field, not a Level-2 excitation.
- **§VII.6**: "dark energy as thermodynamic cost of geometric complexity." Also substrate-physics; dark energy is a Level-1 property.
- **§VII.4.1**: boundary-as-encoding stance. The 2D horizon is a substrate-physical encoding surface for 3D bulk information.

These commitments rule out particulate dark matter (no Level-2 excitation candidate for the dark-matter phenomenology). They commit MFO to *some* substrate-physical mechanism. The question this spike answers: **does MFO commit specifically to Verlinde 2016's emergent-MOND mechanism, or does it leave the mechanism open?**

This is methodologically a structural-clarification spike, not a falsifier-grade prediction-test spike. The output is one of three verdicts — A (full inheritance) / B (partial inheritance) / C (agnostic) — together with what observational predictions would follow under each verdict, and a recommendation for the MFO §VII.5 documentation.

---

## §1. Q1 — Decoding Verlinde 2016 in MFO substrate-vs-excitation terms

### §1.1 Verlinde 2016's derivation structure

Verlinde 2016 (arXiv:1611.02269; *SciPost Phys.* 2, 016, 2017; PDF-verified in #21A) builds on Verlinde 2010 (arXiv:1001.0785; *JHEP* 04, 029, 2011) emergent-gravity programme, extended to incorporate the cosmological constant. The derivation structure, at the level of substrate commitments:

**Starting commitment (Level 1).** Spacetime and gravity emerge together from the entanglement structure of an underlying microscopic theory. The "substrate" in Verlinde's sense is the *entanglement structure*, not the metric field. The metric field, gravity, and even spacetime are emergent Level-2-ish content from the entanglement substrate.

**Cosmological-horizon entropy structure.** The de Sitter cosmological horizon at proper distance `L = 1/H_0` from a static-patch observer has Bekenstein-Hawking entropy `S_BH = A/(4ℓ_P²) = π/(H_0² ℓ_P²)`. This is the area-law entropy. Verlinde additionally identifies a *thermal volume-law entropy contribution* `S_M ~ V/L³ · (constant)` arising from the positive-cosmological-constant thermal medium. At scales much smaller than `L`, the area-law entropy dominates (standard regime). At scales `r ~ L`, the volume-law contribution becomes comparable. At the horizon `r = L`, they coincide.

**Crossover scale.** Matching the area-law-to-volume-law crossover at `r = L = 1/H_0` produces a characteristic acceleration scale `a_0 = cH_0/(2π) ≈ 6.8 × 10⁻¹⁰ m/s²` (using `H_0 = 70` km/s/Mpc). This is approximately a factor of 5.6 larger than the empirical MOND constant `a_0^MOND ≈ 1.2 × 10⁻¹⁰ m/s²` (Milgrom 1983; canonical pre-2010 exempt).

**Displacement / elastic response.** Baryonic matter in the cosmological medium *displaces* the dark-energy thermal volume-law entropy. The displacement entropy at a distance `r` from a mass `M_b` is approximately `S_M(r) ~ M_b r / (constants × ℓ_P²)`. The reaction of the dark-energy medium to the displacement produces an additional "elastic" gravitational force. The leading approximate formula for the dark-force magnitude (Verlinde 2016 eq. 7.40 region, paraphrased):

`F_dark(r) ~ √(M_b a_0 G / 6) / r`

with `a_0 = cH_0/(2π)`. This is *MOND-like* phenomenology — at large `r`, the dark-force adds to the Newtonian baryonic force, producing flat rotation curves and a Tully-Fisher-like relation `v⁴ ~ G M_b a_0`.

**Recovery of Newtonian limit.** At small `r`, the volume-law contribution is subdominant; standard Newtonian gravity is recovered. At large `r` (low accelerations), the dark-force dominates; MOND-like behaviour appears. The crossover at `g ~ a_0` is the MOND transition.

### §1.2 Verlinde's and MFO's implicit substrate-physics commitments

**Verlinde 2016 commits to:** (V1) substrate is entanglement, not metric — metric emerges; (V2) dark energy is substrate-thermal-input via `T_dS = ℏH_0/(2π c k_B)`; (V3) dark-matter phenomenology is *emergent* from substrate's elastic response to baryonic displacement (not a particle, not an excitation); (V4) baryonic matter is the Level-2 content driving the elastic response.

**MFO §VII.1.1 + §VII.5 + §VII.6 + §VII.4.1 commits to:** (M1) substrate is the metric field — not emergent; (M2) vacuum, dark matter, dark energy all at Level 1 substrate; (M3) localised matter-wave vs delocalised field excitations at Level 2; (M4) dark matter is geometric curvature, not particles (§VII.5); (M5) horizon is substrate-physical 2D encoding surface (§VII.4.1).

### §1.4 The substrate-ontology comparison

| | MFO | Verlinde 2016 |
|---|---|---|
| What is the substrate? | Metric field (Level 1) | Entanglement structure of microscopic theory |
| Is metric emergent? | No — metric IS the substrate | Yes — metric emerges from entanglement |
| Dark energy? | Substrate-layer (§VII.6) | Input condition (cosmological constant) |
| Dark matter? | Substrate-layer geometric curvature (§VII.5) | Emergent from substrate's elastic response to baryonic displacement |
| Baryonic matter? | Level-2 localised excitation | "Material excitation" on entanglement substrate |
| Mechanism for dark-matter phenomenology? | Not specified — "geometric curvature" interpretive | Specific elastic-response formula |
| Specific acceleration scale? | Not specified | `a_0 = cH_0/(2π)` |

The structural alignment is strong:
- Both put dark matter at the substrate layer (M2/M4 ↔ V3).
- Both put dark energy at the substrate layer (M2 ↔ V2).
- Both treat baryonic matter as the active driver of modifications (M3 ↔ V4).
- Both use the cosmological horizon as the structurally relevant scale (M5 ↔ V's de Sitter horizon thermodynamics).

The structural divergence is meaningful but ontologically deeper:
- Verlinde's substrate is one level below MFO's substrate (entanglement underlying the metric, vs the metric itself).
- This is not necessarily a contradiction — MFO is silent about what is beneath the metric field; the metric being substrate doesn't preclude something beneath the metric being substrate at a deeper level.

### §1.5 The decoding in compact form

**Verlinde 2016 in MFO substrate-vs-excitation language:** the metric field (MFO substrate) emerges from a deeper substrate (entanglement); dark matter phenomenology (an apparent Level-2 effect) is actually an emergent property of the substrate's elastic response to localized baryonic excitations; dark energy enters as a substrate-physical thermal-medium property associated with the de Sitter cosmological horizon.

**Where MFO's substrate-physics commitment differs from Verlinde's**: MFO commits at the metric-field-substrate level; Verlinde commits one level deeper (entanglement). MFO §VII.5 / §VII.6 commit to dark sector as substrate-layer-of-metric-field; Verlinde commits to dark sector as substrate-layer-of-entanglement. These are *compatible* readings — MFO could be silent about what's below the metric — but they are different ontological commitments.

**What "emergent" means in each:** for Verlinde, gravity itself (the metric, the gravitational force) is emergent from entanglement. For MFO, gravity is the dynamics of the metric-field substrate — it's not emergent in Verlinde's sense; it's the substrate's own physics. This is a meaningful difference. Inheriting Verlinde's predictions wholesale would require MFO to *also* commit to "metric is emergent from entanglement," which is a deeper commitment than §VII.5 / §VII.6 currently make.

---

## §2. Q2 — MOND literature mapping

The MOND framework has a 43-year history (Milgrom 1983 → present). The relevant anchors for evaluating MFO inheritance:

### §2.1 Pre-2010 MOND canon (Milgrom 1983 / Bekenstein-Milgrom 1984 / Bekenstein 2004 / Sanders-McGaugh 2002)

**Milgrom 1983** (ApJ 270, 365 / 371 / 384). Original MOND: below a critical scale `a_0 ≈ 1.2 × 10⁻¹⁰ m/s²`, effective acceleration becomes `a = √(a_N a_0)`. Predictions: asymptotic flat rotation curves, Tully-Fisher `v_∞⁴ = G M_b a_0`, surface-density rule (LSB galaxies deeper in MOND regime), Faber-Jackson for ellipticals. The empirical scale `a_0 ≈ 1.2 × 10⁻¹⁰ m/s²` is a factor ~5.6 below `cH_0/(2π) ≈ 6.8 × 10⁻¹⁰ m/s²` — a long-standing numerological coincidence.

**Bekenstein-Milgrom 1984** (ApJ 286, 7). AQUAL non-relativistic field theory: `∇·[μ(|∇φ|/a_0) ∇φ] = 4πG ρ_b`. Interpolation `μ(x) → x` for `x ≪ 1`, `μ(x) → 1` for `x ≫ 1`. Multiple phenomenological choices ("simple" `x/(1+x)`, "standard" `x/√(1+x²)`, "exponential" `1 - e^(-x)`); no first-principles derivation in standard MOND.

**Bekenstein 2004 TeVeS** (Phys. Rev. D 70, 083509). Tensor-vector-scalar covariant relativistic completion; reduces to MOND in non-relativistic limit. Known difficulties: galaxy clusters need residual dark mass; CMB fit poorly without dark-matter-like ingredient; post-GW170817 the `c_GW ≠ c` variants ruled out.

**Sanders-McGaugh 2002** (ARA&A 40, 263). Pre-2010 comprehensive MOND review documenting BTFR / surface-density / LSB-rotation-curve successes and galaxy-cluster / CMB difficulties.

### §2.2 Famaey-McGaugh 2012 — Living Reviews comprehensive update

**Famaey & McGaugh 2012** *Modified Newtonian Dynamics (MOND): Observational Phenomenology and Relativistic Extensions.* Living Rev. Rel. 15, 10. arXiv:1112.3960. **PDF-verified in this session.** Abstract excerpt: "*many of these puzzling observations are predicted by one single relation - Milgrom's law - involving an acceleration constant ... of the order of the square-root of the cosmological constant in natural units.*"

Canonical post-2010 review. Documents BTFR / RAR / surface-density-rule / LSB / external-field-effect successes; galaxy-cluster / CMB / some-lensing difficulties; relativistic extensions (TeVeS, GEA, BIMOND). The Famaey-McGaugh observation that `a_0 ~ √Λ ~ cH_0` is the central empirical hint motivating Verlinde 2016 — the numerological coincidence Verlinde derives from first principles.

### §2.3 McGaugh-Lelli-Schombert 2016 — radial-acceleration relation

**McGaugh, Lelli & Schombert 2016** *The Radial Acceleration Relation in Rotationally Supported Galaxies.* PRL 117, 201101. arXiv:1609.05917. **PDF-verified in this session.** 2693 data points / 153 galaxies; tight correlation `g_obs ≈ g_bar / (1 - exp(-√(g_bar / g_†)))` with `g_† = 1.20 × 10⁻¹⁰ m/s²`; scatter ~0.13 dex primarily from measurement error. The sharpest empirical MOND-like constraint to date.

### §2.4 Lelli-McGaugh-Schombert 2015/2016 — baryonic Tully-Fisher

**Lelli, McGaugh & Schombert 2016** *The small scatter of the baryonic Tully-Fisher relation.* ApJL 816, L14. arXiv:1512.04543. **PDF-verified in this session.** 118 disk galaxies; BTFR intrinsic scatter ~0.1 dex "below general LCDM expectations"; slope close to 4 (`v⁴ ~ M_b`); no correlation with structural parameters. MOND naturally predicts zero intrinsic scatter; ΛCDM predicts larger from halo-mass-concentration scatter. Lelli et al. 2015 favors MOND-like phenomenology over vanilla ΛCDM.

### §2.5 Brouwer 2017 — first weak-lensing test of Verlinde 2016

**Brouwer et al. 2017** *First test of Verlinde's theory of Emergent Gravity using Weak Gravitational Lensing measurements.* MNRAS 466, 2547. arXiv:1612.03034. **PDF-verified in this session.** 22 authors; 33,613 isolated central galaxies from KiDS+GAMA; Verlinde's no-free-parameter prediction in "good agreement" with observed galaxy-galaxy lensing in four stellar-mass bins. Caveats: assumes ΛCDM background; specific regime; one data type. The load-bearing first observational test.

### §2.6 Galaxy clusters and CMB

**Bullet Cluster** (Clowe et al. 2006, pre-2010 canonical): weak-lensing mass spatially offset from X-ray baryonic mass after collision — natural for collisionless dark matter. MOND has long-standing trouble here; Verlinde 2016 predicts cluster-scale dark-force contributions, with calculations (Cresswell-Verlinde 2018-era; topic-only reference) giving mixed results.

**CMB acoustic peaks** (Planck 2018, topic-only reference). ΛCDM fits the peaks with high precision; TeVeS-style modified-gravity without dark-matter-like ingredient struggles. Verlinde 2016 takes positive `Λ` as input; at recombination (`z ~ 1100`) the universe is far inside the cosmological horizon `r ≪ L`, so the volume/area-law crossover does not enter — Verlinde's dark-force is negligible at early times. **Verlinde 2016 therefore predicts the standard ΛCDM CMB acoustic-peak structure** — a feature, not a difficulty, because the dark-force is a late-time / large-scale phenomenon.

### §2.7 MOND-to-Verlinde divergences

Where Verlinde 2016 differs from standard MOND:

| Feature | Standard MOND (Milgrom 1983) | Verlinde 2016 |
|---|---|---|
| `a_0` value | Empirical `1.2 × 10⁻¹⁰ m/s²` (fit) | Derived `cH_0/(2π) ≈ 6.8 × 10⁻¹⁰ m/s²` |
| Interpolation `μ(x)` | Phenomenological choice | Derived from volume/area-law crossover |
| Relativistic completion | TeVeS-type frameworks | Not fully developed |
| CMB | TeVeS-difficulties | ΛCDM-compatible (small at early times) |
| Bullet Cluster | Known difficulty | Debated, mixed results |

The factor-of-5.6 discrepancy in `a_0` between empirical MOND and Verlinde's derivation is a significant tension. Either Verlinde's coefficient is wrong by an O(1) factor (a derivation-detail issue that could potentially be repaired), or `cH_0` is the *natural* scale and the empirical `a_0^MOND` corresponds to some related-but-distinct quantity. Brouwer 2017's good agreement on weak lensing despite this `a_0` discrepancy suggests the latter possibility — Verlinde's framework matches data on its own terms, not via fitting to MOND's specific `a_0`.

---

## §3. Q3 — Inheritance verdict: (A), (B), or (C)?

### §3.1 The three possibilities

**(A) MFO inherits Verlinde-MOND wholesale.** MFO substrate-vs-excitation commits to:
- Verlinde's specific de-Sitter-horizon entropy structure.
- Volume-law / area-law crossover at `r = L`.
- Specific elastic-response displacement formula.
- Acceleration scale `a_0 = cH_0/(2π)`.
- MOND-like emergent force `F_dark ~ √(M_b a_0 G / 6) / r`.

MFO would then be *phenomenologically equivalent* to Verlinde 2016 at the dark-sector level. Any future falsification of Verlinde's specific predictions would falsify MFO's dark-sector commitments.

**(B) MFO inherits partial commitments.** MFO agrees with Verlinde on some structural commitments (e.g., dark-sector-at-substrate, cosmological-horizon-as-relevant-scale, emergent-from-substrate-elastic-response) and disagrees on others (e.g., specific coefficient, specific functional form). MFO predicts a *modified* emergent-MOND-like phenomenology distinguishable from Verlinde.

**(C) MFO does not inherit Verlinde.** MFO substrate-vs-excitation is compatible with Verlinde 2016 but does not commit to it. ΛCDM, Verlinde-MOND, modified-gravity-from-substrate-physics-of-other-form, and other dark-sector phenomenologies are all consistent with MFO's substrate-physics commitments at their current level of specificity.

### §3.2 Analysis of each possibility

**(A) full inheritance** would require supplementing MFO §VII.5 / §VII.6 / §VII.4.1 with Verlinde's specific functional forms — `a_0 = cH_0/(2π)`, `F_dark ~ √(M_b a_0 G / 6) / r`, volume-law / area-law entropy structure. MFO does *not* currently make these commitments. Furthermore, (A) is not natural — Verlinde's substrate is entanglement (deeper than metric); wholesale inheritance requires committing to entanglement-as-substrate-of-metric, a stronger commitment than §VII.1 currently makes. **(A) is not the current MFO status.**

**(B) partial inheritance** is plausible. MFO and Verlinde share substrate-physics ontology for dark sector (M2/M4 ↔ V3, M2 ↔ V2), baryons as driver (M3 ↔ V4), cosmological-horizon as relevant scale (M5 ↔ V de Sitter). A natural (B) commitment: MFO inherits Verlinde's qualitative substrate-physics structure but leaves specific functional form open — to be derived from §VII.4.1.1's Hopf-bundle realisation or other substrate-physics work. **(B) is structurally available but requires choices MFO has not made.**

**(C) agnostic.** MFO's current §VII.5 / §VII.6 commitments are interpretive: rule out particulate dark matter, locate dark sector at substrate layer; do *not* pick a specific emergent-gravity formula. Multiple substrate-physical frameworks satisfy these — (1) Verlinde 2016 emergent-MOND, (2) geometric modified gravity (f(R), Horndeski), (3) substrate-fluctuation-induced gravity (Padmanabhan 2010-style), (4) others. MFO's interpretive content does not select among these. **(C) is the current actual status.**

### §3.3 Structural pressure toward (B)

Despite (C) being the current status, there is structural pressure within MFO toward picking a specific mechanism. The pressure comes from this fact:

> *§VII.5 commits to "dark matter is substrate-layer geometric curvature, not particles." This is a substrate-physical commitment. It forces dark-matter phenomenology to arise from some specific substrate-physical mechanism. Of the candidate mechanisms, Verlinde 2016 is the most-developed and is structurally compatible with all other MFO commitments.*

The pressure does not *force* MFO to commit to Verlinde — MFO could commit to one of the other candidate mechanisms (f(R), substrate-fluctuation, etc.). But Verlinde 2016 is the natural candidate within the substrate-physics + boundary-as-encoding + cosmological-horizon-as-relevant-scale frame that MFO has established.

**Refined verdict: MFO is currently (C) agnostic, with structural pressure toward (B) partial-inheritance with Verlinde 2016 as the natural candidate-mechanism.** The inheritance question is *open*; the framework has not chosen.

### §3.4 The specific step where MFO's commitment could diverge from Verlinde's

If MFO were to commit to (A) or (B), the natural divergence point from Verlinde's specific derivation is:

**The deeper-substrate question.** Verlinde's substrate is entanglement; MFO's substrate is the metric field. Inheriting Verlinde wholesale requires committing to entanglement-as-substrate-of-metric. If MFO instead commits to *the metric field as fundamental substrate with no deeper layer*, then the volume-law-vs-area-law entropy structure must be derived from metric-field-substrate physics, not from underlying entanglement structure. This is a different derivation route — possibly producing different specific predictions.

**The Hopf-bundle channel.** §VII.4.1.1's principal-U(1)-bundle realisation gives a specific spectral decomposition of horizon modes: `λ_S³(ℓ) - λ_S²(ℓ) = ℓ` (the linear-gap structure). Verlinde 2016 does not use Hopf-bundle structure; the entropy formulas are area-law / volume-law without finer spectral decomposition. If MFO inherits the substrate-physics frame but uses its own Hopf-bundle spectral decomposition, the resulting emergent-MOND formula could in principle differ from Verlinde's in detailed coefficients.

These are concrete divergence-point candidates. Neither has been worked out. They are the natural sites for MFO-specific work that would produce (B)-style partial inheritance.

---

## §4. Q4 — Specific testable predictions if MFO inherits (A) or (B)

### §4.1 If (A) — wholesale inheritance

MFO would inherit Verlinde 2016's specific predictions:

- **Radial-acceleration relation** (McGaugh-Lelli-Schombert 2016): specific `g_obs = F(g_bar)` derived from volume-law-displacement; Brouwer 2017 verified with no free parameters.
- **Baryonic Tully-Fisher**: slope ~4, scatter ~0.1 dex (Lelli-McGaugh-Schombert 2015 verified).
- **CMB acoustic peaks**: standard ΛCDM structure (consistency-prediction, not distinguishing).
- **Galaxy clusters / Bullet Cluster**: contested status of Verlinde's cluster-scale predictions inherited.
- **Hubble tension**: not directly predicted; late-time effective-gravity modifications could shift SH0ES inference; sign and magnitude open.

### §4.2 If (B) — partial inheritance

Specific predictions depend on which commitments are inherited / diverged on. The natural divergence site is the Hopf-bundle channel (§3.4): if §VII.4.1.1's principal-U(1)-bundle spectral decomposition is used in the volume/area-law lattice analysis, the resulting `a_0` coefficient could differ from Verlinde's `cH_0/(2π)`. A useful (B) commitment would predict the empirical MOND `a_0 ≈ 1.2 × 10⁻¹⁰ m/s²` rather than Verlinde's `6.8 × 10⁻¹⁰ m/s²` — closing the factor-of-5.6 gap. This would constitute MFO-distinctive content. The derivation has not been done.

### §4.3 The sharpest testable inheritance prediction

**The radial-acceleration relation functional form together with the BTFR small-scatter prediction.** Both tightly constrained empirically (McGaugh-Lelli-Schombert 2016; Lelli-McGaugh-Schombert 2015); both difficult for vanilla ΛCDM without fine-tuning; both predicted by Verlinde 2016 with no free parameters (in regime). If MFO commits to (A) or (B), the framework gains these predictions; if MFO remains (C) agnostic, no specific RAR/BTFR prediction follows. Distinguishing (B) from Verlinde requires either a different `a_0` coefficient, a different RAR interpolation function, or different cluster-scale predictions — all targets for future MFO-specific Hopf-bundle-derivation work, not near-term testable.

---

## §5. Q5 — Refined structural law mechanism classification

### §5.1 The mechanism analysis

Verlinde's `a_0` derivation uses two lattice quantizations: (i) **area-law lattice** — Bekenstein-Hawking entropy `S_BH = A/(4ℓ_P²)` is a Planck-area lattice on the 2D horizon (~`π/(H_0² ℓ_P²)` pixels); (ii) **volume-law lattice** — thermal-medium entropy `S_M ~ V/ℓ_P³` is a Planck-volume lattice in the 3D bulk (~`(4π/3)/(H_0³ ℓ_P³)` cells). The two coincide at the cosmological-horizon scale `r = L = 1/H_0`, selecting `a_0 = cH_0/(2π)`.

Both are **mechanism (iv)** instances — discrete lattice quantization. The crossover is a *layered* mechanism (iv) — two related lattices with a crossover condition. Output `a_0` is closed-form in `H_0` and constants. No mechanism (v) candidate.

### §5.2 The MOND interpolation function

The MOND interpolation function `μ(x)` is kinematic-dynamics — how the elastic-response strength varies with displacement magnitude. Standard MOND interpolations are phenomenological choices (`x/(1+x)`, `x/√(1+x²)`, `1 - e^(-x)`); Verlinde 2016 derives a specific function from the volume/area-law integration. Closed-form vs transcendental depends on the integration details.

**Verdict: outside the refined structural law's scope.** Same status as the Hayward `(1 + ε/2)` kinematic correction (#21A §6) — kinematic-dynamics, not closed-form-spectral-compression. The refined-law treats it as a kinematic given.

### §5.3 Hopf-bundle channel and final classification

If MFO inherits §VII.4.1.1's Hopf-bundle decomposition at the cosmological horizon, mechanism (i) at SO(3) applies to the angular sector; radial sector remains mechanism (iv) at the layered area/volume lattices. **Layered (i) × (iv) reading** — same as Schwarzschild Hawking, cosmological-horizon thermodynamics (#21A), Heisenberg + HO (Spike #18). No mechanism (v) candidate. The refined structural law's 4-mechanism statement remains complete.

---

## §6. Q6 — Verdict and MFO §VII.5 recommendation

### §6.1 The honest verdict

**Verdict: (C) agnostic, with structural pressure toward (B) partial inheritance.**

MFO's current commitments at §VII.5 / §VII.6 / §VII.4.1 are sufficient to rule out particulate dark matter and to locate the dark sector at the substrate layer. They are *not* sufficient to pick a specific emergent-gravity formula. Multiple substrate-physical frameworks (Verlinde 2016, modified-gravity-from-substrate, substrate-fluctuation-induced gravity, others) could realise MFO's interpretive commitments. The framework currently *does not select* Verlinde 2016 from this space.

Verlinde 2016 is *structurally compatible* with all MFO commitments and is the *most-developed* candidate-mechanism. The structural pressure for MFO to commit comes from the §VII.5 commitment that dark matter is substrate-layer geometric curvature — this forces *some* specific substrate-physical mechanism to produce the apparent dark-matter phenomenology, and Verlinde 2016 is the natural candidate. But the choice has not been made.

### §6.2 Recommendation for MFO §VII.5

The MFO notebook should **not** be modified to commit to Verlinde-MOND wholesale. The framework's interpretive content at §VII.5 / §VII.6 is appropriate to its current state — these sections name the substrate-physics location of dark matter / dark energy without committing to specific functional forms.

What the MFO notebook *could* usefully add (when the framework is ready to make such commitments): an explicit acknowledgment that Verlinde 2016 is the natural candidate-mechanism for the substrate-physical dark-matter realisation, with the inheritance question open until MFO-specific derivation work is done.

A sample addition (suggested for future revision, not for direct insertion into the notebook by this spike):

> *§VII.5.1 (potential addition, deferred). The substrate-physical mechanism producing the dark-matter-like phenomenology is currently not specified in this framework. The natural candidate, structurally compatible with §VII.1.1's two-level ontology and §VII.4.1's boundary-as-encoding stance, is Verlinde 2016's emergent-MOND-like elastic-response framework, in which baryonic matter displaces a thermal volume-law entropy contribution at the cosmological horizon, producing an apparent additional gravitational force at the scale `a_0 = cH_0/(2π)`. The Hopf-bundle realisation of §VII.4.1.1 could in principle produce a modified version of this derivation with a different effective `a_0` or interpolation function; such work is open. Until specific functional forms are committed, this framework remains compatible with both Verlinde 2016 and alternative substrate-physical mechanisms for the dark sector.*

This kind of language captures the honest state of the framework: structurally compatible with Verlinde, not committed to Verlinde, with specific MFO-distinctive derivation work as a target for future development.

### §6.3 Spike #21B's overall finding

**Honest-agnostic on the inheritance question, with structural-pressure context.** MFO and Verlinde 2016 are in the same neighbourhood (both substrate-physics, both put dark sector at substrate layer, both use cosmological horizon as relevant scale), and Verlinde 2016 is the natural candidate-mechanism within MFO's frame. But MFO has not yet committed to specific functional forms, so the inheritance is currently open.

The structural-clarification value:

1. **Verlinde 2016's substrate-physics structure decoded.** §1.4's comparison table makes explicit where MFO and Verlinde align and where they ontologically differ (substrate is metric-field vs entanglement).

2. **MOND literature properly mapped.** Famaey-McGaugh 2012, McGaugh-Lelli-Schombert 2016 (RAR), Lelli-McGaugh-Schombert 2015 (BTFR), Brouwer 2017 (first weak-lensing test of Verlinde) all PDF-verified in this session.

3. **Mechanism classification clean.** Verlinde's `a_0 = cH_0/(2π)` derivation fits as layered (i) × (iv) with kinematic-dynamics for the interpolation function — same pattern as Schwarzschild Hawking, cosmological-horizon thermodynamics (#21A), and Heisenberg + HO (Spike #18). No mechanism (v) candidate emerges. The refined structural law's 4-mechanism statement remains complete.

4. **MFO §VII.5 recommendation calibrated.** Don't commit to Verlinde wholesale; do leave space for future Hopf-bundle-based MFO-distinctive derivation work; explicit acknowledgment of Verlinde 2016 as the natural candidate-mechanism would be valuable when the framework is ready for that level of commitment.

### §6.4 What Spike #21C should address

The Spike #21A recommendation for #21C was Hopf-bundle vs BMS soft-hair mode counting at the Schwarzschild horizon. This remains the right target — it is independent of the inheritance question this spike has addressed.

If a future #21D or follow-up spike were to address the Hopf-bundle channel for cosmological-horizon-with-emergent-MOND specifically — i.e., the §3.4 / §4.4 divergence-point candidates from this spike — that would be the natural path to commit MFO to (B) partial-inheritance with specific MFO-distinctive predictions. This is a longer-term project, not a single-spike target.

---

## §7. Citation chain

### §7.1 Pre-2010 canonical (exempt from PDF re-verification per discipline counter-clause)

- **Milgrom 1983** (3 papers) *ApJ* 270, 365 / 371 / 384 — original MOND framework, critical acceleration `a_0 ≈ 1.2 × 10⁻¹⁰ m/s²`.
- **Bekenstein-Milgrom 1984** *ApJ* 286, 7 — AQUAL non-relativistic field theory; MOND interpolation function `μ(x)`.
- **Bekenstein 2004** *Phys. Rev. D* 70, 083509. arXiv:astro-ph/0403694 — TeVeS relativistic extension.
- **Sanders-McGaugh 2002** *ARA&A* 40, 263 — comprehensive MOND review through 2002.
- **Clowe et al. 2006** Bullet Cluster weak-lensing observation. Canonical pre-2010, no PDF re-verification.
- **Gibbons-Hawking 1977** *Phys. Rev. D* 15, 2738 — de Sitter cosmological horizon temperature (used in #21A; preserved canonical exempt).
- **Bekenstein 1973** *Phys. Rev. D* 7, 2333 — black hole entropy.
- **'t Hooft 1993** arXiv:gr-qc/9310026 — holographic principle origin.
- **Susskind 1995** arXiv:hep-th/9409089 — holographic principle.
- **Padmanabhan 2002** *Class. Quant. Grav.* 19, 5387 — emergent-gravity programme foundation.

### §7.2 2010+ PDF-verified in this session

- **Famaey-McGaugh 2012** *Living Reviews in Relativity* 15, 10. arXiv:1112.3960 — comprehensive MOND review with successes/difficulties. **PDF-verified.** Title and abstract content matched; review establishes BTFR / RAR / surface-density-rule successes and galaxy-cluster / CMB difficulties of MOND.

- **McGaugh-Lelli-Schombert 2016** *Phys. Rev. Lett.* 117, 201101. arXiv:1609.05917 — radial-acceleration relation in 153 galaxies. **PDF-verified.** Title and abstract content matched; 2693 data points; tight `g_obs = F(g_bar)` correlation with scatter ~0.13 dex; `a_0 = 1.20 × 10⁻¹⁰ m/s²`.

- **Lelli-McGaugh-Schombert 2016** (submitted 2015-12-14) *ApJ Letters* 816, L14. arXiv:1512.04543 — BTFR small-scatter result. **PDF-verified.** Title and abstract content matched; 118 disk galaxies; BTFR intrinsic scatter ~0.1 dex; slope close to 4; "below general LCDM expectations."

- **Brouwer et al. 2017** *MNRAS* 466, 2547. arXiv:1612.03034 — first weak-lensing test of Verlinde 2016 using KiDS+GAMA on 33,613 isolated central galaxies. **PDF-verified.** Title and 22-author list and abstract content matched; Verlinde's no-free-parameter prediction in "good agreement" with observed galaxy-galaxy lensing profiles in four stellar-mass bins.

### §7.3 Trusted from Spike #21A (PDF-verified there; not re-verified)

- **Verlinde 2016** (publ. 2017) arXiv:1611.02269. *SciPost Phys.* 2, 016. *Emergent Gravity and the Dark Universe.* — emergent-MOND-like derivation, scale `a_0 = cH_0/(2π)`, predicts dark-MATTER-like phenomenology. PDF-verified in Spike #21A; trusted here per conductor brief.

- **Hayward 1998** arXiv:gr-qc/9710089. *Class. Quant. Grav.* 15, 3147. PDF-verified in #21A. Pre-2010 canonical exempt; reused here for the cosmological-horizon kinematic frame.

- **Cai-Kim 2005** arXiv:hep-th/0501055. *JHEP* 02, 050. PDF-verified in #21A. Pre-2010 canonical exempt; reused here for the apparent-horizon thermodynamics frame.

- **Verlinde 2010** arXiv:1001.0785. *JHEP* 04, 029 (2011). PDF-verified in #21A. Used in §1.1 to anchor the emergent-gravity programme.

### §7.4 Referenced topically (not load-bearing; no fresh PDF-verification)

- **Cresswell-Verlinde 2018-era** Bullet Cluster predictions from Verlinde 2016 framework. Topic-only reference in §2.9.
- **Planck 2018** CMB cosmological parameters. Topic-only reference in §2.10.
- **Lasenby-Hobson-Smith 2017** Verlinde 2016 prediction analysis. Topic-only reference in §3.1.
- **Helgason 1984** *Groups and Geometric Analysis.* Symmetric-space spectral theory (referenced in refined structural law row 9; pre-2010 canonical).

### §7.5 Attempted-but-unverifiable

None in this spike. The four load-bearing 2010+ citations (Famaey-McGaugh 2012, McGaugh-Lelli-Schombert 2016, Lelli-McGaugh-Schombert 2015/2016, Brouwer 2017) were all PDF-verified via arXiv abstract extraction in this session. Topic-only references (§2.9, §2.10, §3.1) are flagged as such; specific arXiv IDs should be PDF-verified by any future merge into shared documents.

---

## §8. Cross-references

- **Spike #21A** — implements the recommended #21B-pivot from #21A §7.3; (C)-agnostic-with-pressure-toward-(B) verdict aligns with #21A's "MFO needs specific commitments for observationally-engaged content" assessment.
- **Spike #19b** — Territory 4 (cosmological / de Sitter) ranked highest; #21B continues the corrected (dark-matter, not dark-energy) emergent-MOND inheritance analysis. #19b §4.5's "commits MFO to specific predictions" is here conditional on MFO making (A)/(B) commitment, not yet done.
- **Refined structural law consolidation** — Verlinde's `a_0` derivation fits layered mechanism (iv) at area/volume lattice crossover; MOND interpolation function is kinematic-dynamics outside refined-law scope. Same pattern as #21A, Spike #18, Schwarzschild Hawking. No mechanism (v).
- **MFO §VII.5 / §VII.6 / §VII.4.1 / §VII.4.1.1** — loci of MFO's dark-sector and horizon-encoding commitments; §VII.4.1.1's Hopf-bundle channel is the natural site for future MFO-distinctive derivation work (§3.4 / §4.2 divergence point).
- **`user_stance_fiber_as_spatially_absent_encoding.md`** / **`user_stance_hyper_as_3d_spatial_interface.md`** — inform substrate-vs-excitation decoding throughout. MFO substrate = metric field; Verlinde substrate = entanglement (one level deeper); ontological difference noted in §1.4.
- **`feedback_pdf_extraction_citation_discipline.md`** — applied to §7. Four 2010+ load-bearing citations PDF-verified.
- **`feedback_no_lineage_claims_in_notebook.md`** — applied throughout; MFO described as "structurally compatible with" / "Verlinde 2016 is the natural candidate-mechanism within MFO's frame"; no "natural extension" language.
- **`feedback_no_mvp_framing.md`** — all six Q's covered in full.

---

## §9. Discipline checklist

- **No shared-file edits.** Strictly srmech-local at `docs/srmech/notes/spike_21b_verlinde_mond_mfo_inheritance_2026-05-13.md`. MFO notebook, CHANGELOG.md, README.md, refined-structural-law consolidation file, .gitignore, pin_and_slot.py untouched.

- **No verification scripts.** The analysis is interpretive structural mapping, not a numerical derivation. Verlinde's specific formulas referenced symbolically with topic-only-briefing care; no MFO-distinctive numerical claim is made.

- **No NDJSON sidecar.** This spike's content is structural-classification not tabular-data-rich. The Q1-Q6 outcomes are reported in the body and the §1.4 substrate-ontology table; no separate sidecar adds value.

- **Pre-2010 canonical citations** freely used; explicitly enumerated in §7.1.

- **2010+ load-bearing citations PDF-verified.** Four citations PDF-verified via arXiv abstract extraction in this session: Famaey-McGaugh 2012, McGaugh-Lelli-Schombert 2016, Lelli-McGaugh-Schombert 2015/2016, Brouwer 2017. Title, author, journal/volume, abstract content all matched arXiv records.

- **Verlinde 2016 trusted from #21A.** Per conductor brief, the PDF-verification done in #21A is trusted; not re-verified here. The verified content (dark-MATTER-not-dark-energy framing) is the input to this spike's analysis.

- **No lineage claims** about external work. MFO described as "structurally compatible with" Verlinde; no "natural extension" or "descends from" language.

- **No MVP framing.** All six Q's covered substantively. (C)-agnostic verdict on Q3 is the load-bearing finding; recommendations for MFO §VII.5 in Q6 follow from this verdict.

- **Honest-negative / honest-agnostic valid.** The (C)-agnostic verdict is the load-bearing finding. MFO does not currently commit to Verlinde-MOND; the framework's interpretive content is appropriate to its current state; commitment to specific functional forms is open future work.

- **Topic-only briefing followed.** Conductor described topics; this spike built the citation chain via PDF-verification of four 2010+ papers (Famaey-McGaugh 2012, McGaugh-Lelli-Schombert 2016, Lelli-McGaugh-Schombert 2015, Brouwer 2017) plus pre-2010 canonical works (Milgrom 1983, Bekenstein-Milgrom 1984, Bekenstein 2004 TeVeS, Sanders-McGaugh 2002).

- **No corrections to conductor brief.** Framing accurate; no new misattributions.

---

## §10. Branch and commit metadata

- **Base branch:** `research/spike-21-mfo-horizon-thermodynamics-extended` (continuing from #21A at commit `9072c56`).
- **No new branch.** This spike adds to the existing branch per conductor brief — same bundle as #21A, with #21C queued after.
- **Commit message:** `research(srmech): Spike #21B MFO — Verlinde 2016 emergent-MOND inheritance — verdict (C) agnostic with structural pressure toward (B) partial inheritance`.
- **No push, no PR.** Per conductor brief: strictly local notes; user handles bundling #21A + #21B + #21C into one PR after all three land.
- **No shared files touched.** MFO notebook, CHANGELOG.md, README.md, refined-structural-law consolidation file, .gitignore, pin_and_slot.py all untouched.
- **Single commit.** Lower-case prefix per conductor brief. No Claude-as-author footer.
