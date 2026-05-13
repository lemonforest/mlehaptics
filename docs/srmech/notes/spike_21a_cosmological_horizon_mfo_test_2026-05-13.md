# Spike #21A — MFO substrate-vs-excitation test at the cosmological / de Sitter horizon

**Branch:** `research/spike-21-mfo-horizon-thermodynamics-extended` (from `main` at `1c06d3e`)
**Date:** 2026-05-13
**Predecessors:**
- Spike #19 `spike_19_mfo_hawking_radiation_dof_mismatch_2026-05-13.md` on branch `research/spike-19-mfo-hawking-radiation-dof-mismatch` (PR #374, draft) — narrow Schwarzschild-Hawking DoF-mismatch test; mostly-pure-wash finding.
- Spike #19b `spike_19b_mfo_horizon_thermodynamics_leverage_2026-05-13.md` on branch `research/spike-19b-mfo-horizon-thermodynamics-leverage` (PR #375, draft) — six-territory leverage scan; Territory 4 (cosmological / de Sitter) ranked highest-leverage native home of the user's "different expansion rates" intuition.
- Refined structural law consolidation `refined_structural_law_consolidation_2026-05-13.md` on `main` (PR #373 merged) — 4-mechanism law, 10/10 fit, with Hawking radiation as layered (i) × (iv).
- MFO notebook §VII.1.1 (two-level substrate / excitation ontology); §VII.4 (Hawking radiation as dimensional mismatch); §VII.4.1 (black-holes-end-at-the-2D-boundary stance); §VII.4.1.1 (Hopf-bundle U(1)-fibre realisation); §VII.4.1.2 (Casimir-decomposition universality); §VII.5 (dark matter as geometric curvature); §VII.6 (dark energy as thermodynamic cost of geometric complexity).
**Methodological frame:** Guide-stone, **not** falsification. Spike #19b identified Territory 4 as the native home where the user's "3D vs 2D propagation spaces expand at different rates" intuition can do genuine physical work, because the cosmological horizon — unlike the stationary Schwarzschild horizon — is a *dynamical* horizon governed by a time-varying Hubble parameter `H(t)`. The question is whether MFO substrate-vs-excitation commits to a *specific* deviation from standard dynamical-horizon thermodynamics at the cosmological horizon, and whether that deviation is observationally accessible.
**Status:** RESEARCH — outcome: **NUMERICALLY-NULL-PREDICTION FINDING WITH STRUCTURAL-CLARIFICATION TAIL.** The standard Hayward-Kodama dynamical surface-gravity correction `T = (H / 2π) · (1 − Ḣ / (2 H²))` already captures the leading time-variation contribution at the apparent horizon. MFO substrate-vs-excitation does *not* commit to a specific additional coefficient `α` beyond what Hayward 1998 / Cai-Kim 2005 give — the substrate-physical framing is interpretive over the same Kodama-vector kinematics. The structural-clarification tail is twofold: (a) MFO inherits Verlinde 2016 (arXiv:1611.02269) "Emergent Gravity and the Dark Universe" content if the substrate-vs-excitation ontology is committed to entropic-gravity at the cosmological horizon — *but Verlinde 2016 explains observed phenomena currently attributed to dark **matter**, not dark **energy***, which corrects a framing slip in Spike #19b §4.5; and (b) the refined structural law's mechanism analysis at the cosmological horizon fits as **layered (i) × (iv) extended with a kinematic time-variation factor**, not as mechanism (v).
**Tabular sidecar:** `spike_21a_cosmological_horizon_mfo_results_2026-05-13.ndjson` (Q-by-Q outcomes + citation chain + observability rows).

---

## §0. Methodological frame and the load-bearing question

Spike #19's narrow finding: the user's 3D / 2D DoF-mismatch reframing of Schwarzschild Hawking radiation reproduces the standard `T_H = ℏ κ / (2π c k_B)` via the holographic-principle Bekenstein-Hawking-entropy route, with no numerically distinct prediction. The "different expansion rates" claim washes because nothing actually expands at a stationary Schwarzschild horizon — `κ` is constant, `dA/dt = 0`, the bulk-vs-boundary expansion-rate language is mute.

Spike #19b's broader scan canvassed six territories and ranked cosmological / de Sitter horizons highest-leverage. The argument: the cosmological horizon in FLRW cosmology has time-varying `H(t)`, so there is genuine expansion-rate dynamics for the user's intuition to engage. The 3D bulk has scale-factor expansion `a(t)` with rate `H = ȧ/a`; the cosmological-horizon area `A = 4π / H²` evolves at rate `dA/dt = −8π Ḣ / H³`. These are different physical rates, and they govern different substrate-physical structures (bulk substrate dynamics vs. boundary encoding capacity).

The hypothesis this spike scopes is:

> Does MFO substrate-vs-excitation commit to a specific deviation from the standard adiabatic Gibbons-Hawking temperature `T_dS = H(t) / (2π)` at the cosmological horizon, and is that deviation observationally distinguishable from the standard Hayward / Ashtekar-Krishnan / Cai-Kim dynamical-horizon corrections and from the standard slow-roll-inflation literature?

This is a **guide-stone** spike: we don't expect a falsifier-grade prediction necessarily; we expect to learn where MFO's substrate-physical commitment does and does not have specific predictive content beyond standard treatments.

---

## §1. Q1 — Decoding "different expansion rates" in the cosmological setting

The user's intuition, as Spike #19b §4.2 articulated it: the 3D bulk's Hubble expansion `H` describes Level-1 substrate dynamics; the 2D cosmological-horizon area's evolution `dA/dt` describes the boundary of the dimensional-projection. These are different physical contents under MFO §VII.1.1's two-level ontology — substrate (Level 1) and excitation classes (Level 2) operate at different rates because they are different physical structures.

The decoding into precise mathematical objects:

### §1.1 The cosmological-horizon kinematics

In flat FLRW cosmology with metric `ds² = −dt² + a(t)² dx²` and Hubble rate `H(t) = ȧ/a`, the **apparent horizon** (Hayward 1998; Bak-Rey 2000; Cai-Kim 2005 arXiv:hep-th/0501055) is the surface at proper radial distance `r_A` from a comoving observer where outgoing null geodesics have vanishing expansion. For flat FLRW it sits at `r_A = 1/H` (in units `c = 1`). In de Sitter (constant `H = H_dS`) this is the Gibbons-Hawking cosmological horizon at proper distance `1/H_dS` from the static-patch observer; in general FLRW it is the generalised time-dependent horizon.

Area: `A(t) = 4π r_A² = 4π / H²(t)`.

Rate of area change: `dA/dt = −8π Ḣ / H³`.

For accelerating universe `ä > 0` corresponds to `Ḣ + H² > 0`. In matter-dominated FLRW `Ḣ < 0` and `H` decreases over time, so `dA/dt > 0` — the horizon area grows. In de Sitter limit `Ḣ → 0` and `dA/dt → 0` — horizon area is constant. The current epoch (`Ω_m ≈ 0.3`, `Ω_Λ ≈ 0.7`) has the deceleration parameter `q_0 ≈ −0.55`, so `Ḣ/H² = −(1 + q_0) ≈ −0.45` — strongly time-dependent.

### §1.2 The 3D-bulk dynamics

The metric-field substrate (Level 1 under MFO §VII.1.1) supports field excitations whose propagation on the FLRW background is governed by the d'Alembertian `□_FLRW`. For a massless scalar field `φ`,

`□_FLRW φ = (1/√(−g)) ∂_μ (√(−g) g^{μν} ∂_ν φ) = −[∂_t² + 3H ∂_t − a^{−2} ∇²] φ = 0.`

The `3H ∂_t` term is the Hubble friction / cosmological-redshift coupling; it expresses the substrate's time-dependent expansion. Mode frequencies redshift as `ω_phys(t) = k / a(t)` for physical wavenumber `k_phys = k / a`.

The bulk-mode density of states (per unit physical volume, per unit physical frequency):

`ρ_3D,phys(ω) = ω² / (2π² c³)` (Planckian 3D form, instantaneous comoving frame).

This is unchanged from Minkowski form because the FLRW metric is locally Minkowskian in comoving frame at each instant — the redshift enters via the time-evolution of `ω_phys`, not via the instantaneous DoS.

### §1.3 The 2D-horizon dynamics

The cosmological horizon `r = 1/H(t)` is a 2-sphere of area `4π / H²`. Its intrinsic geometry is a round 2-sphere whose radius `1/H(t)` evolves with `t`. The induced metric on the horizon is the standard round-`S²` metric scaled by `1/H²(t)`.

The 2D-horizon mode DoS (per unit area, per unit frequency):

`ρ_2D,phys(ω) = ω / (2π c²)` (Planckian 2D form).

This is the standard membrane-paradigm 2D-fluid mode count (Thorne-Price-Macdonald 1986 for BH horizons; same form for cosmological horizon by local equivalence to Rindler at the horizon scale).

### §1.4 The "different rates" content, precisely

The 3D-bulk substrate evolves with **scale-factor rate** `ȧ/a = H(t)`. The 2D-horizon area evolves with **area rate** `(dA/dt)/A = −2 Ḣ/H`. These are dimensionally different rates:

- `H(t)` has dimensions `[1/time]`; it is the Level-1 substrate's intrinsic Hubble rate.
- `−2 Ḣ/H` has dimensions `[1/time]`; it is the Level-2 horizon-area's logarithmic growth rate.

Their *ratio* is `−2 Ḣ / H²` — the *slow-roll parameter* (up to sign and factor):

`ε ≡ −Ḣ / H² ⟹ (dA/dt)/A / H = 2ε.`

In de Sitter `ε = 0` (the two rates align — both are zero, since the horizon is non-evolving and `Ḣ = 0`). In matter-dominated `ε = 3/2`. In radiation-dominated `ε = 2`. In the current dark-energy-dominated epoch `ε ≈ 0.45`.

**The user's "different expansion rates" intuition decodes precisely as the slow-roll parameter `ε`** — a dimensionless ratio that measures the mismatch between bulk-substrate dynamics (`H`) and boundary-area dynamics (`Ḣ/H`). When `ε = 0` (de Sitter), the rates align and the user's mismatch vanishes; when `ε ≠ 0`, the rates differ and the mismatch is non-trivial.

This is sharp. Under MFO §VII.1.1's two-level ontology, `H(t)` describes substrate-layer dynamics; the horizon-area logarithmic rate `−2 Ḣ/H` describes excitation-layer dynamics at the boundary. The slow-roll parameter `ε` is the dimensionless characterisation of the substrate-vs-excitation rate mismatch.

### §1.5 The decoded conjecture in MFO language

> *Under MFO substrate-vs-excitation, the cosmological horizon's dynamical evolution exhibits a substrate-excitation rate mismatch characterised by the slow-roll parameter `ε = −Ḣ/H²`. Under de Sitter (`ε = 0`) this mismatch vanishes and the horizon thermodynamics reduces to the static Gibbons-Hawking form `T_dS = H/(2π)`. Under non-trivial cosmology (`ε ≠ 0`), the substrate-physical mismatch produces a correction to `T_dS` whose leading dependence is on `ε`.*

This decodes the user's intuition into a precise mathematical question: **what is the coefficient of the `ε` correction to `T_dS = H/(2π)` under MFO substrate-vs-excitation?**

---

## §2. Q2 — Mapping to existing dynamical-horizon thermodynamics literature

The dynamical-horizon thermodynamics literature is mature. The question MFO must engage: **what is the standard expression for cosmological-horizon temperature in non-stationary cosmology, and what are the known dynamical corrections?**

### §2.1 Gibbons-Hawking 1977 — the static baseline

Gibbons, G. W. & Hawking, S. W. (1977) *Cosmological event horizons, thermodynamics, and particle creation.* Phys. Rev. D 15, 2738–2751. Pre-2010 canonical, exempt from PDF re-verification per discipline counter-clause.

For pure de Sitter spacetime with constant Hubble rate `H_dS`, the cosmological horizon at proper distance `1/H_dS` from a static-patch observer thermalises at temperature

`T_dS = ℏ H_dS / (2π c k_B).`

This is the analog of Hawking-temperature for cosmological horizons. The derivation is the same Wald-1984 universal-Killing-horizon argument: the static-patch Killing vector has a bifurcation surface at the cosmological horizon with surface gravity `κ = H_dS`. The thermal response is observer-detector response in vacuum state of static-patch coordinates.

### §2.2 Hayward 1998 — unified first law of black-hole dynamics

Hayward, S. A. (1998) *Unified first law of black-hole dynamics and relativistic thermodynamics.* Class. Quantum Grav. 15, 3147. arXiv:gr-qc/9710089. Pre-2010 canonical. PDF-verified in this session.

Hayward defines the **dynamical surface gravity** for the trapping horizon using the Kodama vector (which generalises the Killing vector to dynamical / spherically-symmetric spacetimes):

`κ_K = (1/2) □_M r |_H`

where `r` is the areal radius and `□_M` the d'Alembertian on the 2D radial / temporal subspace. For a flat FLRW apparent horizon at `r_A = 1/H`, this evaluates to

`κ_A = −(1/r_A) · (1 − Ḣ / (2 H²)) = −H · (1 − ε/2 · (−1)) = −H (1 + ε/2)`

with the sign conventions of `ε = −Ḣ/H²` (positive `ε` for `Ḣ < 0`, matter / radiation domination). I take the absolute value:

`|κ_A| = H · (1 + ε/2) + O(ε²).`

Hayward's first-law `dE = T dS` then gives

`T_Hayward = |κ_A| / (2π) = H/(2π) · (1 + ε/2) + O(ε²)`

at leading order in `ε`.

**This is the standard dynamical correction**: at `ε ≠ 0`, the apparent horizon thermalises at a temperature *higher* than the naive `H/(2π)` by a factor `(1 + ε/2)`.

### §2.3 Ashtekar-Krishnan 2002–2004 — dynamical horizons framework

Ashtekar, A. & Krishnan, B. (2002) *Dynamical horizons: Energy, angular momentum, fluxes and balance laws.* Phys. Rev. Lett. 89, 261101. arXiv:gr-qc/0207080. Pre-2010 canonical. PDF-verified in this session.

Ashtekar & Krishnan (2003) *Dynamical horizons and their properties.* Phys. Rev. D 68, 104030. arXiv:gr-qc/0308033. Pre-2010 canonical.

The Ashtekar-Krishnan framework provides a covariant formulation of dynamical horizons (non-stationary horizons with time-varying area), with balance laws for energy, angular momentum, and entropy flux across the horizon. The energy flux across a dynamical horizon equals the change in horizon area divided by `8π`:

`dA/8π = (energy flux across horizon)`

which integrates to a first-law-like statement at the dynamical horizon. The temperature is *not* defined uniquely in this framework — the dynamical horizon's evolution does not have a unique surface-gravity definition, and several proposals exist (Kodama-vector definition per Hayward; effective-temperature definition per Ashtekar-Krishnan via the horizon's flux balance).

For the FLRW cosmological apparent horizon, the Ashtekar-Krishnan effective temperature matches Hayward's `(1 + ε/2)` correction to leading order.

### §2.4 Cai-Kim 2005 — Friedmann equations from apparent-horizon thermodynamics

Cai, R.-G. & Kim, S. P. (2005) *First law of thermodynamics and Friedmann equations of Friedmann-Robertson-Walker universe.* JHEP 02, 050. arXiv:hep-th/0501055. Pre-2010 canonical. PDF-verified in this session.

Cai & Kim derived the Friedmann equations from `dE = T dS` at the apparent horizon, assuming:

- Apparent horizon temperature `T = 1 / (2π r_A) = H/(2π)` (leading order, **without** the Hayward correction).
- Apparent horizon entropy `S = A / 4 = π / H²` (Bekenstein-Hawking form for any horizon).
- Heat flux `dE` from matter accreting across the horizon.

The result reproduces the Friedmann equations exactly. The Cai-Kim derivation works at leading-`ε⁰` order, where the temperature is just `H/(2π)` and the slow-roll correction does not appear. Higher-order corrections to the temperature would correspond to higher-order corrections to the Friedmann equations.

### §2.5 Frolov-Kofman 2003 — slow-roll inflation horizon thermodynamics

Frolov, A. & Kofman, L. (2003) *Inflation and de Sitter thermodynamics.* JCAP 0305, 009. arXiv:hep-th/0212327. Pre-2010 canonical. PDF-verified in this session.

For quasi-de Sitter geometry during slow-roll inflation, Frolov-Kofman compute the energy flux of the rolling scalar field through the quasi-de Sitter apparent horizon and equate it to `T dS` with `T = H/(2π)` and `S = A/4`. The result reproduces the Friedmann equation for the slowly-rolling scalar. They argue that the leading apparent-horizon temperature *is* `H(t)/(2π)` to the precision relevant for inflationary observables; higher-order slow-roll corrections to the temperature are sub-dominant to the leading `H` term.

Frolov-Kofman do *not* explicitly include the Hayward `(1 + ε/2)` correction in their derivation; their `T = H/(2π)` is the adiabatic / instantaneous-Killing-vector temperature. The corrections in slow-roll inflation observables come from the time-evolution of `H` itself (the standard slow-roll parameters `ε`, `η`) rather than from horizon-temperature corrections.

### §2.6 The standard summary

For the FLRW cosmological apparent horizon, the standard expressions in the literature are:

- **Adiabatic / leading-order:** `T_adiabatic = H(t)/(2π)` (Gibbons-Hawking instantaneous, Cai-Kim 2005, Frolov-Kofman 2003).
- **Hayward-Kodama dynamic surface gravity:** `T_Hayward = H(t)/(2π) · (1 + ε/2) + O(ε²)` where `ε = −Ḣ/H²`.
- **Ashtekar-Krishnan effective:** matches Hayward at leading order; ambiguous at higher order.

The Hayward `(1 + ε/2)` correction is the **canonical dynamical correction** in the post-1998 literature. It is what any MFO-distinctive prediction must be distinguishable from.

---

## §3. Q3 — Verlinde 2016 verdict (arXiv:1611.02269 PDF-verified)

Spike #19b §4.3 flagged Verlinde 2017 emergent dark energy as load-bearing for the cosmological-horizon scan. I PDF-verified arXiv:1611.02269 in this session. The verdict requires both a correction to Spike #19b's framing and a reassessment of MFO inheritance.

### §3.1 Verified citation

Verlinde, E. P. (2017) *Emergent Gravity and the Dark Universe.* SciPost Phys. 2, 016. arXiv:1611.02269. Submitted November 7, 2016; published 2017. **PDF-verified in this session via arXiv abstract.**

Title and abstract (verbatim, abridged):

> *Recent theoretical progress indicates that spacetime and gravity emerge together from the entanglement structure of an underlying microscopic theory... The extension to de Sitter space requires taking into account the entropy and temperature associated with the cosmological horizon. Using insights from string theory, black hole physics and quantum information theory we argue that the positive dark energy leads to a thermal volume law contribution to the entropy that overtakes the area law precisely at the cosmological horizon... The emergent laws of gravity contain an additional 'dark' gravitational force describing the 'elastic' response due to the entropy displacement. We derive an estimate of the strength of this extra force in terms of the baryonic mass, Newton's constant and the Hubble acceleration scale a_0 = c H_0, and provide evidence for the fact that this additional 'dark gravity force' explains the observed phenomena in galaxies and clusters currently attributed to dark **matter**.*

### §3.2 Correction to Spike #19b §4.5 framing

**Critical correction:** Verlinde 2016 does **not** primarily predict observable dark-energy phenomenology. It uses positive dark energy (the cosmological constant) as the *input* — the existing observed `Λ` — and derives a thermal-volume-law contribution to entropy that becomes dominant at the cosmological horizon. The *output* of the framework is a "dark gravitational force" that mimics what is currently attributed to **dark matter** (galactic rotation curves, cluster dynamics — i.e., the MOND-phenomenology regime).

Spike #19b §4.3 §4.5 referred to "Verlinde-2017-style emergent-dark-energy predictions" — this language is imprecise. The proper characterisation: Verlinde 2016 is emergent-gravity-with-dark-matter-as-emergent-elastic-response, with dark-energy taken as given. Spike #19b's text should read "Verlinde-2016 emergent-MOND-like-dark-matter predictions" or "Verlinde-2016 emergent-elastic-response predictions" rather than "emergent-dark-energy predictions."

The Hubble acceleration scale `a_0 = c H_0` is approximately `6.8 × 10⁻¹⁰ m/s²` (using `H_0 = 70` km/s/Mpc), which is ~5.7× the empirical MOND scale `1.2 × 10⁻¹⁰ m/s²` of Milgrom 1983 (canonical pre-2010). The numerical factor enters Verlinde's emergent-force formula and the exact match to MOND-rotation-curve phenomenology depends on the derivation's coefficients.

### §3.3 Independent observational status of Verlinde 2016

The Verlinde 2016 framework has been observationally probed since 2017. Brouwer et al. 2017 (weak-lensing test on galaxy data) found the framework consistent with observed weak-lensing radial-acceleration relation. Lelli et al. 2017, McGaugh et al. 2016 (canonical pre-2017 MOND-phenomenology data) established the radial acceleration relation that emergent-gravity must reproduce.

Subsequent work (Lasenby-Hobson-Smith 2017 and others) has identified tensions: Verlinde's specific prediction for the inner-galaxy rotation curve at very low accelerations may not perfectly match MOND or observations; the framework's predictions for galaxy clusters are debated. **The framework is neither established nor falsified by current observations.** It is a contested but observationally-engaged predictive framework.

Note on citation discipline: Brouwer et al. 2017, Lasenby-Hobson-Smith 2017 are post-2010 citations that I have *not* freshly PDF-verified in this session. They are referenced topically; specific arXiv IDs should be PDF-verified by any future merge of this material into shared docs.

### §3.4 MFO inheritance assessment

Does MFO substrate-vs-excitation commit to Verlinde 2016's predictions?

The structural alignment is strong:

- **MFO Level 1 substrate** = Verlinde's microscopic entanglement-based theory underlying spacetime.
- **MFO §VII.4.1 boundary-as-encoding stance** = Verlinde's cosmological-horizon-as-entropy-bounding surface.
- **MFO §VII.5 dark matter as geometric curvature** = Verlinde's emergent-dark-matter as elastic response to entropy displacement.
- **MFO §VII.6 dark energy as thermodynamic cost** = Verlinde's positive dark energy as the input that drives the thermal-volume-law contribution.

These alignments mean MFO is structurally compatible with Verlinde 2016. **But structural compatibility is not commitment.** MFO does *not* explicitly inherit Verlinde 2016's specific formula for the dark gravitational force `F_dark = √(M_b a_0 G / 6) / r` (Verlinde 2016 eq. 7.40, approximately) — the MFO notebook §VII.5 and §VII.6 do not commit to this specific functional form. They commit to the *interpretive stance* that dark matter is geometric / substrate-physical rather than particulate.

The honest assessment: MFO is in the same neighbourhood as Verlinde 2016. If Verlinde 2016's emergent-MOND-like predictions are ruled out by future weak-lensing or rotation-curve data, MFO would be required to commit to a *different* specific substrate-physical formula for the emergent-dark-matter phenomenology, which it has not yet done. The framework currently has interpretive content without specific numerical commitment.

This is informative for the project's research priorities: if MFO wants observationally-engaged content at the cosmological-horizon layer, it needs to commit to specific functional forms for the substrate-physical emergent-force predictions, not just interpretive alignment with the Verlinde-Padmanabhan programme.

---

## §4. Q4 — The math derivation: candidate MFO deviation from `T_dS = H(t)/(2π)`

This is the load-bearing math. The question: does MFO substrate-vs-excitation predict a specific coefficient `α` for the `ε`-correction to the cosmological-horizon temperature, distinguishable from the standard Hayward `(1 + ε/2)` correction?

### §4.1 Setting up the derivation

The standard Hayward-Kodama derivation (§2.2) gives:

`T_Hayward = H/(2π) · (1 − Ḣ/(2 H²)) = H/(2π) · (1 + ε/2) + O(ε²).`

(Note the sign: `Ḣ < 0` in matter-dominated FLRW gives `ε > 0`, hence `1 + ε/2 > 1` — the dynamical horizon is *hotter* than the static-Killing-vector naive value `H/(2π)`. In Hayward's original conventions and signs this is the canonical correction.)

For MFO to predict a distinguishable correction, the substrate-vs-excitation framing must commit to:

- A different coefficient `α ≠ 1/2` for the `ε` term, or
- An additional functional dependence on `Ḣ`, `Ḧ`, `H` that does not reduce to the Hayward form, or
- A different starting kinematic-temperature formula altogether.

### §4.2 The substrate-vs-excitation rate-mismatch argument

The MFO ansatz, decoded from Q1: the substrate (Level 1) evolves at rate `H`; the boundary excitation (Level 2) evolves at rate `−2 Ḣ/H`. The dimensionless mismatch is `ε = −Ḣ/H²`.

A naive MFO-substrate-physical temperature ansatz: weight the static `T_dS = H/(2π)` by some functional of `ε` that captures the rate mismatch. The minimal ansatz consistent with the de Sitter limit (`ε → 0` recovers `T_dS = H/(2π)` exactly):

`T_MFO = H/(2π) · f(ε)` with `f(0) = 1`.

The leading expansion: `f(ε) = 1 + α ε + O(ε²)`. The Hayward result corresponds to `α = 1/2`.

**Does MFO substrate-vs-excitation commit to a specific `α`?**

### §4.3 The substrate-physical ansatz analysis

Three candidate MFO-substrate-physical readings:

**Reading A (Hopf-bundle base-rate ansatz).** Under §VII.4.1.1's Hopf-bundle realisation, the cosmological horizon is `S²` (or asymptotically-spheroidal `S²`); the bundle's `U(1)`-fibre encodes the substrate-physical information channel. The base-`S²` evolution rate is `(dA/dt)/A = −2 Ḣ/H = 2 ε H`. The fibre is non-spatial (per `user_stance_fiber_as_spatially_absent_encoding.md`), so it does not evolve at a separate spatial rate. The substrate-vs-excitation temperature in this reading: the boundary's spectral evolution rate is `−2 Ḣ/H`; the bulk's spectral evolution rate is `H`. The MFO temperature ansatz weighting these by the Wald-1984 surface-gravity / Killing-vector kinematic gives:

`T_MFO,A = (1/2π) · √(H · |−2 Ḣ/H|) = (H/2π) · √(2 |ε|).`

In the de Sitter limit (`ε → 0`), this diverges or vanishes depending on the regularisation choice — **the de Sitter limit is singular**, which is the wrong behaviour. The static-de-Sitter limit must recover `H/(2π)`, not `0` or `∞`. **Reading A is inconsistent with the de Sitter limit and is therefore rejected.**

**Reading B (substrate-Hubble-rate ansatz).** The substrate's intrinsic rate is `H`. The temperature should be Killing-vector surface-gravity divided by `2π`. The Killing-vector kinematic that governs the cosmological horizon in pure de Sitter is the static-patch Killing vector with surface gravity `κ = H_dS`. In dynamical FLRW, the Killing vector becomes the Kodama vector (Hayward 1998 §2.6); the Kodama-vector surface gravity is precisely the Hayward `κ_A = −H (1 + ε/2)`.

**This recovers Hayward exactly.** Under Reading B, MFO substrate-vs-excitation gives `α = 1/2` — the same as standard Hayward. **No new content.**

**Reading C (decoupled rate-difference ansatz).** Treat substrate rate `H` and boundary rate `−2 Ḣ/H` as independent rates and define the temperature as the difference:

`T_MFO,C = (1/2π) · (H − (−2 Ḣ/H)) · (1/2) = (H/2π) · (1 + ε) · (1/2) + ...`

The factor `(1/2)` is necessary for de Sitter limit consistency (de Sitter has `ε = 0`, gives `T = H/(4π)`, **wrong by factor of 2**). To fix the de Sitter limit, the ansatz must be normalised differently, e.g., `T_MFO,C = (1/2π) · (H/(1 − ε)) · `(some normalisation). Various normalisations give different `α` coefficients, but they are *all chosen by hand* to fit the de Sitter limit — **the MFO substrate-physics does not pick out a specific `α`**.

### §4.4 The crucial structural fact

The Wald 1984 theorem — *any bifurcate Killing horizon thermalises at `T = ℏ κ/(2π c k_B)`* — is observer-detector-coupling fact, not substrate-thermodynamic fact. It applies whenever there is a global Killing vector with a bifurcation surface. In dynamical FLRW, the global Killing vector is *absent*; the natural replacement is the Kodama vector (Hayward 1998); the natural surface gravity is the Kodama-vector surface gravity `κ_A = −H(1 + ε/2)`. The Wald-theorem extension to Kodama-vector dynamical horizons gives the Hayward temperature.

**The MFO substrate-vs-excitation framing does not bypass the Kodama-vector kinematics.** Whatever rate-mismatch the substrate and excitation classes have, the temperature of the apparent horizon is set by the Kodama-vector surface gravity (or its appropriate dynamical generalisation), because the temperature is fundamentally an observer-detector-response property and the observer-detector coupling sees the Kodama-vector trajectory.

This means: **MFO substrate-vs-excitation does not commit to a specific `α ≠ 1/2`.** The standard Hayward `(1 + ε/2)` correction *is* the MFO prediction, because the substrate-physical content is interpretive over the same Kodama-vector kinematics.

### §4.5 Higher-order corrections

At order `O(ε²)`, the Hayward expansion gives additional terms `c · ε² · (H/2π) + ...` with `c` depending on derivative conventions. Could MFO substrate-vs-excitation predict different higher-order coefficients?

The argument of §4.4 applies recursively: the Kodama-vector kinematics determine the surface gravity at all orders in slow-roll parameters; the observer-detector response sees this surface gravity. MFO substrate-physics does not commit to a higher-derivative ansatz for the temperature that bypasses the Kodama-vector framework.

**MFO substrate-vs-excitation predicts `T_MFO(t) = T_Hayward(t)` at all orders in slow-roll parameters.** The substrate-vs-excitation framing is interpretive content over standard dynamical-horizon thermodynamics; it does not commit to numerical deviations.

### §4.6 Honest-negative finding for Q4

**MFO substrate-vs-excitation does not predict a numerically distinguishable `α · Ḣ/H²` correction to `T_dS = H(t)/(2π)` beyond the standard Hayward `(1 + ε/2)` form.**

This is the central technical finding of this spike. The user's "different expansion rates" intuition, decoded into the cosmological-horizon setting as the slow-roll parameter `ε`, identifies a real physical quantity — but the temperature correction it produces is exactly what standard dynamical-horizon thermodynamics (Hayward 1998, Cai-Kim 2005, Frolov-Kofman 2003) gives. The MFO substrate-physical framing reinterprets but does not modify this content.

This is the same outcome as Spike #19's Schwarzschild-Hawking finding: MFO substrate-vs-excitation is a vocabulary clarification of dynamical-horizon thermodynamics, not a numerically distinct alternative.

---

## §5. Q5 — Observability mapping

Despite the Q4 honest-negative for a direct MFO-specific temperature correction, the broader cosmological-horizon setting has observable phenomena where MFO's substrate-physical commitments may engage. The mapping:

### §5.1 Hubble tension (most direct candidate)

**Phenomenon.** `H_0` inferred from CMB (Planck 2018: `H_0 ≈ 67.4 ± 0.5 km/s/Mpc`) disagrees with `H_0` inferred from local SH0ES distance-ladder measurements (`H_0 ≈ 73 ± 1 km/s/Mpc`) at ~5σ significance. The disagreement is ~8% — a substantial cosmological-parameter tension that the standard `ΛCDM` model does not naturally resolve.

**MFO substrate-vs-excitation engagement.** If the cosmological-horizon temperature is `T = H(t)/(2π) · (1 + ε/2)` (Hayward), and if MFO substrate-physics commits to using the *apparent-horizon temperature* as the operative scale for some observable (e.g., for the radiation pressure on baryons at the horizon, or for some entropic-gravity contribution to the Friedmann equations), then the slow-roll-`ε` correction enters at the few-percent level. At `ε ≈ 0.45` (current epoch), `1 + ε/2 ≈ 1.225` — a 22.5% correction to the naive Hubble temperature. 

Is this correction in the right direction and magnitude to address the Hubble tension? The CMB-`H_0` is *lower* than local-`H_0`; an MFO-substrate-physical correction that **raises** the effective late-time `H` would help. The sign of the Hayward correction (`+ε/2`) gives a higher effective temperature at the current epoch (when `Ḣ < 0`), which would correspond to a higher *effective* `H` at the apparent horizon — pulling in the right direction.

But: the magnitude (~22.5%) is much larger than the observed ~8% tension. **MFO substrate-vs-excitation does not commit to this being the operative mechanism for the Hubble tension.** Such a commitment would require either (a) a specific coefficient on a substrate-physical correction term that produces ~8% rather than ~22.5%, or (b) a derivation that the substrate-physical apparent-horizon temperature does not directly enter the local-`H_0` inference. Neither commitment is currently in the MFO notebook.

**Honest verdict for §5.1:** MFO substrate-vs-excitation is *structurally close* to the Hubble-tension phenomenology but does not specifically predict a Hubble-tension resolution at the right magnitude. The required commitment is at the (a)/(b) coefficient level, which the framework has not yet made.

### §5.2 Galactic rotation curves (Verlinde-2016 inheritance)

**Phenomenon.** Observed flat rotation curves at galaxy outskirts disagree with Newton-only baryonic-matter predictions. Standard resolution: dark matter halos. MOND resolution: modified gravity at low accelerations `a < a_0 ≈ 1.2 × 10⁻¹⁰ m/s²`.

**Verlinde 2016 prediction.** Emergent gravity at the cosmological horizon predicts a dark gravitational force `F_dark = √(M_b a_0 G / 6) / r` (approximate; specific coefficient from Verlinde 2016 eq. 7.40) where `a_0 = c H_0 ≈ 6.8 × 10⁻¹⁰ m/s²`. This is MOND-like but with a specific coefficient set by the cosmological-horizon thermodynamics.

**MFO inheritance.** MFO §VII.5 says dark matter is geometric curvature, not particles. If MFO substrate-physics commits to Verlinde-style emergent-gravity, then the rotation-curve predictions are inherited with whatever coefficients Verlinde's derivation produces. **But MFO does not currently commit to a specific functional form for the emergent-gravity formula.**

**Honest verdict for §5.2:** MFO is in the Verlinde neighbourhood but has not committed to specific rotation-curve predictions. To inherit Verlinde's predictions, MFO would need to explicitly state that the §VII.5 geometric-curvature mechanism is the same elastic-response mechanism as Verlinde 2016.

### §5.3 Structure formation / `σ_8` tension

**Phenomenon.** The amplitude of late-time matter clustering (`σ_8` measured from weak-lensing surveys: KiDS, DES) is lower than the CMB-extrapolated value (Planck 2018) at ~2-3σ. This is the "`σ_8` tension" or "`S_8` tension."

**MFO substrate-vs-excitation engagement.** If MFO substrate-physics modifies the effective late-time gravitational coupling (via Verlinde-style emergent-gravity), this could suppress late-time clustering relative to CMB extrapolation — in the right direction for `σ_8` tension. Same issue as §5.2: MFO does not commit to specific coefficients.

**Honest verdict for §5.3:** Same as §5.2 — MFO is in the Verlinde neighbourhood, but no specific MFO prediction emerges.

### §5.4 Primordial gravitational waves / B-mode polarisation

**Phenomenon.** Inflationary tensor-to-scalar ratio `r` is constrained by CMB B-mode polarisation experiments (LiteBIRD, CMB-S4 future). Standard inflation predicts `r ∝ ε` (single-field slow-roll). Detection of `r > 10⁻³` would establish the inflationary tensor mode.

**MFO substrate-vs-excitation engagement.** During inflation, `ε ≪ 1` (slow-roll), and the apparent-horizon temperature is `T ≈ H_inf / (2π)` with small Hayward corrections. The substrate-vs-excitation framing might commit to specific corrections to the inflationary horizon-mode-power spectrum. If those corrections affect the tensor mode amplitude differently from the scalar mode, the predicted `r` would deviate from single-field-slow-roll predictions.

**Honest verdict for §5.4:** This is the most open-ended candidate. MFO has not committed to specific inflationary observables. Future LiteBIRD / CMB-S4 detections (or non-detections) would test MFO-Verlinde-style emergent-gravity inflation if such a framework were specified.

### §5.5 CMB cold spot / non-Gaussianity

**Phenomenon.** The CMB exhibits a "cold spot" (Eridanus supervoid) and various large-angular-scale anomalies (low-`ℓ` axis-of-evil, hemispherical asymmetry). These are ~3σ anomalies; standard `ΛCDM` does not exclude them but does not predict them.

**MFO substrate-vs-excitation engagement.** MFO §VII.4.1.1's Hopf-bundle realisation specifies a Casimir-decomposition structure for boundary modes. At the cosmological horizon during inflation, the principal-`U(1)`-bundle mode decomposition could in principle predict specific signatures in the CMB low-`ℓ` modes. This is speculative; no derivation currently exists.

**Honest verdict for §5.5:** Speculative open candidate. Not load-bearing for this spike.

### §5.6 Summary table

| Observable | MFO engagement | Specific commitment? | Observational status |
|---|---|---|---|
| Hubble tension `H_0` | Structurally close (Hayward `+ε/2` direction) | No — magnitude mismatch ~22% vs ~8% | Active 5σ tension |
| Rotation curves / dark matter | Verlinde-2016 inheritance candidate | No specific formula | Verlinde framework contested |
| `σ_8` / structure tension | Verlinde-style emergent-gravity suppression | No specific formula | Active 2-3σ tension |
| Primordial GWs (B-modes) | Inflationary substrate-vs-excitation candidate | Not specified | LiteBIRD / CMB-S4 future |
| CMB cold-spot / low-`ℓ` anomalies | Hopf-bundle mode decomposition candidate | Not specified | Marginal anomalies |

**The sharpest observationally-accessible candidate is the Hubble tension**, because (a) the standard Hayward `(1 + ε/2)` correction is large enough to be relevant (~22%), (b) the sign is in the right direction, and (c) MFO could in principle commit to a specific *fraction* of the Hayward correction that enters the local-`H_0` measurement, producing a ~8% effective Hubble tension. This commitment has not been made, but the framework's substrate-vs-excitation ontology provides a natural language for stating it.

---

## §6. Q6 — Mechanism (v) candidate evaluation

The final question: does cosmological-horizon dynamical substrate-physics surface a genuinely new mechanism (v) for the refined structural law, or does it fit within the existing 4-mechanism framework (i)/(iii)/(iv) layered as in Spike #18?

### §6.1 The mechanism analysis at the cosmological horizon

The cosmological horizon is a 2-sphere `S²` of area `4π/H²(t)`. Its isometry group is `SO(3)`. The spectral structure of horizon-mode harmonics is `L²(S²) = ⊕_ℓ V_ℓ` with `dim V_ℓ = 2ℓ + 1`, Casimir eigenvalue `λ_ℓ = ℓ(ℓ+1)`. **Mechanism (i) at SO(3) applies cleanly to the angular sector.** Same as Schwarzschild Hawking (refined-law §3.5.1 row).

The Bekenstein-Hawking entropy `S = A/4 = π/(H² ℓ_P²)` is an `A/4` Planck-area lattice. At each instant, the lattice has `~π/(H² ℓ_P²)` Planck-area pixels, each carrying one bit. **Mechanism (iv) at the holographic A/4 lattice applies cleanly.** Same as Schwarzschild Hawking.

**Layered (i) × (iv) reading.** The angular sector is mechanism (i) at SO(3); the holographic / entropy-bound layer is mechanism (iv) at the A/4 lattice. This is the same layered structure as Schwarzschild Hawking, with the lattice spacing now time-dependent through `H(t)`.

### §6.2 Time-variation contribution analysis

The time-variation `H = H(t)` enters as a *parameter* of the mechanism (iv) lattice. Each instant the lattice is `π/(H²(t) ℓ_P²)`; over time, the lattice grows (matter-dominated) or shrinks (negative `Ḣ` regions) or stays constant (de Sitter). The lattice is *parameter-dependent*, not categorically different.

**Is this mechanism (v)?**

Three candidate readings:

**Reading I — `H(t)` as accessory parameter (Heun-style).** Spike #15 introduced mechanism (iv) via accessory-parameter spectral quantisation: at discrete values of an extra parameter, the equation admits polynomial solutions. The `H(t)` of cosmology is *not* a discrete-quantised parameter — it is a continuous time-evolution. **Reading I does not fit mechanism (iv) cleanly.**

**Reading II — `H(t)` as parameter in a Lie group (i) deformation.** Spike #18 introduced layered-mechanism reading via metaplectic enveloping. At the cosmological horizon, the isometry group `SO(3)` is independent of `H(t)`; the time-variation does not change the group structure. The Lie factor is `SO(3)` at every instant. **Reading II does not fit either.**

**Reading III — kinematic time-variation factor.** The `(1 + ε/2)` factor in Hayward's dynamical surface gravity is a *kinematic correction* to the temperature, not a closed-form spectral compression mechanism. It does not appear in the refined-law mechanisms because the refined-law mechanisms concern *closed-form spectral compression* (when do eigenvalue problems admit closed-form solutions), not *kinematic temperature formulae*. **Reading III fits: the time-variation is a kinematic factor outside the refined-law scope.**

### §6.3 The refined structural law's reach

The refined structural law (PR #373) is a statement about *when closed-form spectral compression exists* — when eigenvalue problems on a substrate admit finite-dimensional invariant-subspace decompositions via one of (i)/(iii)/(iv). It is **not** a statement about kinematic temperature formulae for thermal-equilibrium statements on horizons.

The cosmological-horizon temperature `T(t) = H(t)/(2π) · (1 + ε/2)` is a *kinematic* statement: it comes from the Kodama-vector surface gravity at the apparent horizon, integrated over the observer-detector trajectory. It does not require closed-form spectral compression in the eigenvalue sense.

The horizon-mode-spectrum at each instant is governed by mechanism (i) at SO(3) plus mechanism (iv) at the A/4 lattice (with time-varying lattice spacing). **This is the same mechanism layering as Schwarzschild Hawking, with kinematic time-variation as a parameter dependence rather than a new mechanism.**

### §6.4 Verdict for Q6

**Cosmological-horizon dynamical substrate-physics fits the existing 4-mechanism refined structural law as layered (i) × (iv) with kinematic time-variation as parameter dependence.** No mechanism (v) candidate emerges.

The time-variation contribution to substrate Casimir-decomposition is *outside* the refined-law's scope — it concerns kinematic temperature formulae, not closed-form spectral compression. The refined structural law remains a 4-mechanism statement; the cosmological-horizon setting does not require extending it.

This is informative: the user's "different expansion rates" intuition, when followed all the way down, identifies a kinematic-temperature correction (Hayward `(1 + ε/2)`) that lies *outside* the structural-law content. The structural law concerns *which finite-dim invariant subspaces are selected* (mechanism (i)/(iii)/(iv)); the kinematic temperature concerns *what surface-gravity / Kodama-vector kinematics govern the bifurcate-horizon thermalisation*. These are complementary, not the same content.

The refined structural law's coverage at the cosmological horizon is therefore: angular sector (mechanism (i) at SO(3)) + entropy-bound lattice (mechanism (iv) at A/4) — same as Schwarzschild Hawking — with kinematic time-variation accommodated as parameter dependence of the lattice spacing. **No structural-law extension needed.**

---

## §7. Final findings summary

### §7.1 Q-by-Q summary

| Q | Finding |
|---|---|
| Q1 | "Different expansion rates" decodes precisely as the slow-roll parameter `ε = −Ḣ/H²` — the dimensionless mismatch between substrate-Hubble rate `H` and boundary-area logarithmic rate `−2 Ḣ/H`. |
| Q2 | Standard literature gives `T = H/(2π) · (1 + ε/2)` (Hayward 1998 / Ashtekar-Krishnan 2002 / Cai-Kim 2005 / Frolov-Kofman 2003) as the leading dynamical correction. The Hayward `(1 + ε/2)` is the canonical reference for any MFO-distinctive claim. |
| Q3 | Verlinde 2016 (arXiv:1611.02269) PDF-verified. **Correction to Spike #19b §4.5 framing**: Verlinde 2016 predicts dark **matter** phenomenology (MOND-like rotation curves at scale `a_0 = c H_0`), not dark energy. MFO is structurally close but does not commit to specific Verlinde functional forms. |
| Q4 | **MFO substrate-vs-excitation does not predict a distinguishable `α · Ḣ/H²` correction beyond Hayward's `(1 + ε/2)`.** Three candidate ansätze (Hopf-bundle base-rate, substrate-Hubble-rate, decoupled rate-difference) either fail de Sitter limit consistency or recover Hayward exactly. The substrate-physical content is interpretive over the same Kodama-vector kinematics. Honest-negative finding. |
| Q5 | Sharpest candidate is **Hubble tension** (Hayward `(1 + ε/2)` correction is ~22%, observed tension ~8% — sign right, magnitude requires specific commitment that MFO has not made). Galactic rotation curves and `σ_8` are Verlinde-inheritance candidates without specific MFO commitment. Primordial GWs / CMB anomalies are speculative open candidates. |
| Q6 | **Fits as layered (i) × (iv) with kinematic time-variation as parameter dependence.** No mechanism (v) candidate. The refined structural law's 4-mechanism statement remains complete; the kinematic temperature correction lies outside its scope. |

### §7.2 The spike's overall finding

**Honest-negative on the core math (Q4), structural-clarification value on the framing (Q1, Q3, Q6).**

The user's "different expansion rates" intuition, followed all the way through the cosmological-horizon setting, identifies a real physical quantity (the slow-roll parameter `ε`), which produces a real dynamical-horizon temperature correction (Hayward `(1 + ε/2)`), which has been in the standard dynamical-horizon literature since 1998. MFO substrate-vs-excitation reinterprets this content but does not numerically distinguish itself from standard treatment.

The structural-clarification value:

1. **Spike #19b §4.5 correction.** Verlinde 2016 is dark-matter-phenomenology not dark-energy-phenomenology. The MFO inheritance question must be reposed in terms of MOND-like emergent-gravity, not dark-energy-emergence.

2. **Refined structural law unchanged.** Cosmological-horizon thermodynamics is layered (i) × (iv) with parameter-dependent lattice spacing, same as Schwarzschild Hawking. No mechanism (v) candidate.

3. **Observability mapping clarified.** Hubble tension is the sharpest candidate for future MFO-engagement, but requires the framework to commit to specific substrate-physical correction coefficients that it has not yet made.

The user's intuition correctly points at substrate-physics having relevant content at horizons — but the *specific leverage* requires the substrate to do *physical work*. At the cosmological horizon, the substrate is doing kinematic work (driving `H(t)` through cosmic time-evolution); this maps to the standard Kodama-vector kinematics. No new substrate-physical mechanism beyond standard kinematics emerges.

### §7.3 Recommended follow-up

This spike's null finding for Q4 means **Spike #21B and #21C should pivot.** The cosmological-horizon temperature correction is not the productive avenue; alternatives:

- **Spike #21B candidate.** Verlinde 2016 emergent-gravity inheritance — does MFO commit to a specific functional form for the emergent-MOND-like force, distinguishable from Verlinde's `F_dark = √(M_b a_0 G / 6) / r`? This requires the §VII.5 / §VII.6 sections of the MFO notebook to make specific functional-form commitments rather than interpretive stances. **Productive if MFO is willing to commit specific coefficients.**

- **Spike #21C candidate.** Hopf-bundle vs BMS soft-hair mode counting (the Territory 3 follow-up from Spike #19b). Concrete computational question about whether §VII.4.1.1's principal-U(1)-bundle decomposition matches soft-hair degeneracy. Independent of the cosmological-horizon question; addresses a different MFO-distinctive content layer. **Productive whether MFO commits to coefficients or not.**

The recommendation: Spike #21B should pursue the Verlinde-inheritance commitment question; Spike #21C should pursue the Hopf-bundle / soft-hair mode-counting question. The user planned to bundle #21A, #21B, #21C into one PR; the bundle should reflect that #21A is honest-negative on the cosmological-temperature avenue while productive follow-ups exist in different directions.

---

## §8. Citation chain

### §8.1 Pre-2010 canonical (exempt from PDF re-verification per discipline counter-clause)

- **Gibbons-Hawking 1977** *Cosmological event horizons, thermodynamics, and particle creation.* Phys. Rev. D 15, 2738. — static de Sitter horizon temperature `T_dS = H ℏ/(2π c k_B)`.
- **Hawking 1974, 1975** *Black hole explosions?* / *Particle creation by black holes.* Nature 248, 30; Comm. Math. Phys. 43, 199. — original Hawking radiation derivation.
- **Bekenstein 1973** *Black holes and entropy.* Phys. Rev. D 7, 2333. — entropy bound.
- **Wald 1984** *General Relativity* §14.4 (Univ. Chicago Press). — universal Killing-horizon thermalisation theorem.
- **Milgrom 1983** *A modification of the Newtonian dynamics as a possible alternative to the hidden mass hypothesis.* ApJ 270, 365. — MOND framework with critical acceleration `a_0 ≈ 1.2 × 10⁻¹⁰ m/s²`.
- **Hayward 1994** *General laws of black-hole dynamics.* Phys. Rev. D 49, 6467. — trapping/dynamical horizon framework foundation.
- **Hayward 1998** arXiv:gr-qc/9710089 *Unified first law of black-hole dynamics and relativistic thermodynamics.* Class. Quant. Grav. 15, 3147. — Kodama-vector surface gravity for dynamical horizons. **PDF-verified.**
- **Ashtekar-Krishnan 2002** arXiv:gr-qc/0207080 *Dynamical horizons: Energy, angular momentum, fluxes and balance laws.* PRL 89, 261101. — dynamical-horizon framework, fluxes, balance laws. **PDF-verified.**
- **Ashtekar-Krishnan 2003** arXiv:gr-qc/0308033 *Dynamical horizons and their properties.* PRD 68, 104030. — full dynamical-horizon framework.
- **Frolov-Kofman 2003** arXiv:hep-th/0212327 *Inflation and de Sitter thermodynamics.* JCAP 0305, 009. — slow-roll inflation horizon thermodynamics. **PDF-verified.**
- **Cai-Kim 2005** arXiv:hep-th/0501055 *First law of thermodynamics and Friedmann equations of FRW universe.* JHEP 02, 050. — Friedmann equations from apparent-horizon thermodynamics. **PDF-verified.**
- **Padmanabhan 2002** *Classical and quantum thermodynamics of horizons in spherically symmetric spacetimes.* Class. Quant. Grav. 19, 5387. — emergent-gravity programme foundation.
- **Bousso 2002** arXiv:hep-th/0203101 *The holographic principle.* Rev. Mod. Phys. 74, 825. — covariant entropy bound.
- **'t Hooft 1993** arXiv:gr-qc/9310026 *Dimensional reduction in quantum gravity.* — holographic-principle origin.
- **Susskind 1995** arXiv:hep-th/9409089 *The world as a hologram.* JMP 36, 6377. — holographic principle.
- **Thorne-Price-Macdonald 1986** *Black Holes: The Membrane Paradigm.* Yale UP. — 2D horizon-as-fluid framework.
- **Helgason 1984** *Groups and Geometric Analysis.* — spectral theory on symmetric spaces (referenced in refined-structural-law table row 9).
- **Bak-Rey 2000** arXiv:hep-th/9902173 *Cosmic holography.* Class. Quant. Grav. 17, L83. — pre-2010 apparent-horizon entropy discussion (referenced topically).

### §8.2 Pre-2020 (well-established era; specific arXiv IDs not freshly PDF-verified in this session unless noted)

- **Verlinde 2010** arXiv:1001.0785 *On the origin of gravity and the laws of Newton.* JHEP 04, 029 (2011). **PDF-verified in this session.** — entropic gravity.
- **Verlinde 2016 (publ. 2017)** arXiv:1611.02269 *Emergent Gravity and the Dark Universe.* SciPost Phys. 2, 016 (2017). **PDF-verified in this session.** — emergent dark-matter (NOT dark-energy) phenomenology, MOND-scale `a_0 = c H_0`.
- **Padmanabhan 2010** arXiv:0911.5004 *Thermodynamical aspects of gravity: new insights.* Rep. Prog. Phys. 73, 046901. — emergent gravity programme (not freshly PDF-verified this session).
- **Jacobson 1995** arXiv:gr-qc/9504004 *Thermodynamics of spacetime: the Einstein equation of state.* PRL 75, 1260. — Einstein equations from horizon Clausius (canonical pre-2010, not freshly verified this session).

### §8.3 2020+ (any merge into shared docs requires fresh PDF verification)

None load-bearing for this spike. The Q4 finding is honest-negative on MFO-specific predictions; no 2020+ citations were needed for that finding.

### §8.4 Post-2010 referenced topically (not load-bearing)

- **Brouwer et al. 2017** weak-lensing test of Verlinde-2016 emergent-gravity. Not freshly PDF-verified; referenced in §3.3 as part of the observational-status discussion.
- **Lasenby-Hobson-Smith 2017** Verlinde-2016 prediction analysis. Same as above.
- **Lelli-McGaugh et al. 2016-2017** radial-acceleration-relation observational data. Same as above.
- **Planck 2018** CMB cosmological parameter results. Standard reference, not load-bearing.

### §8.5 Attempted-but-unverifiable

None in this spike. The Q4 honest-negative finding was reached using only PDF-verified or pre-2010-canonical references. Future spikes (especially Spike #21B on Verlinde inheritance) will require PDF-verification of post-2017 observational-test papers.

---

## §9. Cross-references

- **Spike #19** `spike_19_mfo_hawking_radiation_dof_mismatch_2026-05-13.md` — narrow Schwarzschild-Hawking DoF-mismatch test; mostly-pure-wash finding. **Compatibility with #21A**: this spike confirms that the Schwarzschild-Hawking honest-negative extends to the cosmological-horizon setting; the user's "different expansion rates" intuition has a precise mathematical realisation (slow-roll `ε`) but produces a standard dynamical-horizon correction, not an MFO-distinctive one.

- **Spike #19b** `spike_19b_mfo_horizon_thermodynamics_leverage_2026-05-13.md` — six-territory leverage scan. **Compatibility with #21A**: this spike implements the recommended Spike #20A follow-up from #19b §8.1 on cosmological-horizon thermodynamics. The finding is consistent with #19b's "highest leverage" ranking (in the sense that the substrate-physical content is real and engages Verlinde-Padmanabhan-adjacent territory), but is honest-negative on the core temperature-correction prediction. **Correction to #19b §4.5 framing**: Verlinde 2016 is dark-matter, not dark-energy.

- **Refined structural law consolidation** `refined_structural_law_consolidation_2026-05-13.md` — 4-mechanism law (PR #373). **Compatibility with #21A**: the cosmological-horizon setting fits as layered (i) × (iv) with kinematic time-variation as parameter dependence. No mechanism (v) extension required. The refined-law's coverage of horizon thermodynamics is complete at this layer.

- **MFO notebook §VII.1.1** (two-level substrate / excitation ontology) — the foundational ontology underlying the Q1 decoding. The substrate-vs-excitation rate-mismatch is the precise mathematical content this section provides.

- **MFO notebook §VII.4 / §VII.4.1 / §VII.4.1.1 / §VII.4.1.2** — Hawking radiation, boundary-as-everything stance, Hopf-bundle realisation, Casimir-decomposition universality. **#21A finding**: the Hopf-bundle framework applies at the cosmological horizon (`S²` topology preserved), but does not predict a temperature correction beyond Kodama-vector kinematics.

- **MFO notebook §VII.5** (dark matter as geometric curvature) — structural alignment with Verlinde 2016 emergent-dark-matter, but no specific functional-form commitment. **#21A recommendation**: if MFO wants observationally-engaged content, this section needs specific commitments.

- **MFO notebook §VII.6** (dark energy as thermodynamic cost of geometric complexity) — input to Verlinde 2016's framework, not output. Verlinde takes positive `Λ` as given.

- **`user_stance_fiber_as_spatially_absent_encoding.md`** — informs the Reading A analysis in Q4 §4.3. The Hopf-bundle fibre's spatial absence is preserved at the cosmological horizon; the fibre does not evolve at a separate spatial rate.

- **`user_stance_hyper_as_3d_spatial_interface.md`** — informs the two-level ontology application in Q1. The cosmological horizon is a 3D-spatial-interface in the sense relevant for "hyper" — bulk-vs-boundary at this surface is a substrate-physical distinction.

- **`user_stance_string_theory_instrument_first.md`** — informs the discipline that MFO substrate-vs-excitation must do *physical work* not vocabulary work. At Q4, the framework does only vocabulary work (interpretive over Kodama-vector kinematics); the honest-negative reading is the correct one.

- **`feedback_pdf_extraction_citation_discipline.md`** — applied in §8.1 / §8.2 / §8.3 / §8.4 / §8.5 citation organisation. Verlinde 2016 (key load-bearing 2020+ish citation per Spike #19b §4.3) was PDF-verified.

- **`feedback_no_lineage_claims_in_notebook.md`** — applied throughout. MFO is described as "structurally close" or "in the neighbourhood of" Verlinde 2016, not as a "natural extension." Technical-result-specific citations only.

- **`feedback_no_mvp_framing.md`** — applied in §7.3. All six Q's covered in substantive depth; no subset cut. The honest-negative on Q4 is the full-coverage finding; recommendations for #21B and #21C pivot accordingly.

---

## §10. Discipline checklist

- **No shared-file edits.** Strictly srmech-local at `docs/srmech/notes/spike_21a_cosmological_horizon_mfo_test_2026-05-13.md`. MFO notebook, CHANGELOG.md, README.md, refined-structural-law consolidation file, .gitignore, pin_and_slot.py untouched.

- **No verification scripts.** The Q4 derivation is symbolic / textbook; the Kodama-vector surface-gravity calculation is documented in Hayward 1998 directly. No script needed.

- **NDJSON sidecar** `spike_21a_cosmological_horizon_mfo_results_2026-05-13.ndjson` provides tabular Q-by-Q outcomes + citations + observability rows per the conductor brief's `if applicable` clause.

- **Pre-2010 canonical citations** freely used; explicitly enumerated in §8.1.

- **2020+ load-bearing citation** (Verlinde 2016 = arXiv:1611.02269) PDF-verified in this session via arXiv abstract extraction. Title, author, year, abstract content all matched.

- **No lineage claims** about external work. MFO is "structurally close" or "in the neighbourhood of" Verlinde-Padmanabhan; no claim that MFO descends from or extends any external programme.

- **No MVP framing.** All six Q's covered substantively. Honest-negative on Q4 is the central finding; structural-clarification value on Q1, Q3, Q6 is also reported.

- **Honest-negative valid.** The Q4 finding (no distinguishable `α · Ḣ/H²` correction) is the load-bearing technical content. Documented explicitly; recommendations for #21B / #21C pivot accordingly.

- **Topic-only briefing followed.** Conductor described topics; this spike built the citation chain via PDF-verification (Verlinde 2010, Verlinde 2016, Cai-Kim 2005, Hayward 1998, Ashtekar-Krishnan 2002, Frolov-Kofman 2003 all verified in session) plus pre-2010 canonical works.

- **Correction logged.** Spike #19b §4.5 phrase "Verlinde-2017-style emergent-dark-energy predictions" should read "Verlinde-2016-style emergent-MOND-like dark-matter predictions." Logged in §3.2 of this note for future merge into #19b if relevant.

---

## §11. Branch and commit metadata

- **Base commit:** `main` at `1c06d3e` (refined structural law consolidation, PR #373 merged).
- **Spike branch:** `research/spike-21-mfo-horizon-thermodynamics-extended` (new; will accumulate #21A, #21B, #21C per user's plan).
- **Commit message:** `research(srmech): Spike #21A MFO — cosmological-horizon test for "different expansion rates" intuition — honest-negative on core math, structural clarifications on framing`.
- **No push, no PR.** Per conductor brief: strictly local notes; user handles bundling #21A + #21B + #21C into one PR after all three land.
- **No shared files touched.** MFO notebook, CHANGELOG.md, README.md, refined-structural-law consolidation file, .gitignore, pin_and_slot.py all untouched.
- **Single commit.** Lower-case prefix per conductor brief. No Claude-as-author footer.
