# Spike #19b — MFO horizon-thermodynamics leverage scan (six-territory canvass)

**Branch:** `research/spike-19b-mfo-horizon-thermodynamics-leverage` (from `main`)
**Date:** 2026-05-13
**Predecessor:** Spike #19 `spike_19_mfo_hawking_radiation_dof_mismatch_2026-05-13.md` on branch `research/spike-19-mfo-hawking-radiation-dof-mismatch` (PR #374, draft) — narrow DoF-mismatch test that found mostly-pure-wash with small MFO-distinctive tail; standard Schwarzschild Hawking absorbs the user's literal conjecture via the holographic principle + Bekenstein-Hawking-entropy route.
**Methodological frame:** This is **not** a hypothesis-falsification spike. It uses the user's 2026-05-13 DoF-mismatch intuition as a **guide-stone** to ask the broader question: *where in horizon-thermodynamics / black-hole physics might MFO substrate-vs-excitation ontology predict effects that standard QFT-in-curved-spacetime + holographic principle does not?* Six territories canvassed; each evaluated against five criteria; ranked output is the deliverable. Honest-negative on the whole scan is valid; honest-negative per-territory is also valid and informative.
**Refined structural law context:** `refined_structural_law_consolidation_2026-05-13.md` on `main` (PR #373 merged) — 4-mechanism law (i) / (iii) / (iv); Hawking radiation in §3.5.1 row of the 10-setting table is layered mechanism (i) × (iv) (SO(3) at horizon angular sector × A/4 area-entropy lattice at holographic layer).
**MFO foundational sections:** §VII.1.1 two-level ontology (substrate field + excitation classes); §VII.4 Hawking radiation as dimensional mismatch; §VII.4.1 black-holes-end-at-the-2D-boundary stance; §VII.4.1.1 Hopf-bundle U(1)-fibre realisation; §VII.4.1.2 Casimir-decomposition universality.

---

## §0. The methodological frame

Spike #19's narrow test failed in a particular informative way: the user's literal 3D / 2D DoF-mismatch reframing of Hawking radiation reproduces the standard Hawking flux exactly via the Bekenstein-Hawking entropy bound, with the temperature obtained from `dS/dE = 1/T_H` and the Stefan-Boltzmann × area giving the flux. The MFO substrate-vs-excitation framing is an interpretive clarification of the holographic-principle / emergent-gravity program ('t Hooft 1993, Susskind 1995, Verlinde 2010-2011, Padmanabhan 2010 — pre-2020 work, characterisation per Spike #19 §2 with care-flags) rather than a numerically distinct alternative.

The user's correction — *"was the research spike done in the spirit of only because of DoF mismatch or did you take it in the spirit of one example of a condition for this cause as a guide stone to asking the correct question?"* — relocates the question. The conjecture's load-bearing claim is **substrate-physics as the source of Hawking-like radiation**. The narrow form (3D-bulk vs 2D-horizon mode counting at a stationary Schwarzschild horizon) is one realisation. Other realisations may exist where the substrate-vs-excitation commitment translates to predictions that standard treatments do not capture.

The scan canvasses six territories where one or more of MFO's structural commitments — (a) two-level substrate/excitation ontology, (b) dimensional-projection as substrate-physical-condition rather than coordinate-dependent computation, (c) Hopf-bundle U(1)-fibre information-encoding channel (§VII.4.1.1), (d) Casimir-decomposition universality (§VII.4.1.2), (e) "metric field is real ring-up/ring-down medium" stance (per `user_stance_string_theory_instrument_first.md`) — might plausibly produce numerically or structurally distinguishable content from standard treatment.

Each territory is evaluated on five criteria: (1) standard treatment topic-level summary; (2) where MFO's commitment might say something different; (3) leverage assessment (numerical distinguishability + observational accessibility); (4) mechanism implication for the refined structural law (stress-test on (i)/(iii)/(iv); mechanism-(v) candidate?); (5) honest-negative per-territory verdict.

Topic-only briefing was used: I describe topics and structural facts; I do not cite specific arXiv IDs for post-2020 work without in-session PDF verification. Pre-2010 canonical works are exempt per `feedback_pdf_extraction_citation_discipline.md` counter-clause and are named below.

---

## §1. Territory 1 — Extremal / near-extremal black holes (T_H → 0)

### §1.1 Standard treatment

At extremality (Reissner-Nordström `Q = M`, Kerr `a = M`, or analogous in higher-charge / higher-spin cases), the surface gravity `κ` vanishes. The Hawking temperature `T_H = ℏκ/(2π c k_B)` is therefore zero — extremal black holes do not radiate by the standard formula. The horizon area remains macroscopic, so the Bekenstein-Hawking entropy `S = A/(4ℓ_P²)` is nonzero. Strominger-Vafa 1996 (canonical pre-2010) gave a microscopic state count for a particular family of supersymmetric extremal BHs that matches `A/4` exactly, validating the entropy formula at zero temperature.

The third law of black-hole thermodynamics (Israel 1986; canonical pre-2010) states that the extremal limit is unreachable in a finite number of physical processes — analogous to the unreachability of `T = 0` in ordinary thermodynamics. This is structurally tight: extremal BHs are limiting states, not generic states.

Near-extremal regimes have been intensively studied in recent decades. The geometry near the horizon factorises as `AdS₂ × S²` (Bertotti-Robinson 1959 throat geometry; pre-2010 canonical). The near-extremal dynamics is governed by Jackiw-Teitelboim (JT) gravity on `AdS₂` — a two-dimensional dilaton-gravity theory whose boundary dynamics is the Schwarzian quantum mechanics (Maldacena-Stanford-Yang 2016, pre-2020 well-established; broader programme uses standard SYK / chaos-bound literature). At low temperatures, the entropy receives corrections of the form `S = S_0 + c · T + ...` with the Schwarzian-mode contribution dominant. Post-2020 work on near-extremal corrections (which would require PDF verification to cite specifically, hence not done here) extends this in several directions including the breakdown of Bekenstein-Hawking semiclassical thermodynamics in the deep-IR regime.

### §1.2 Where MFO might say something different

The MFO commitment is: the horizon is a substrate-physical 2D phase boundary. At extremality, the horizon area is large; the substrate's dimensional-projection IS happening. The "temperature" `T_H` is the rate at which mismatch dissipates outward — at extremality this rate vanishes, but the dimensional-projection itself does not.

The Hopf-bundle U(1)-fibre realisation (§VII.4.1.1) operates at the angular sector and is unaffected by surface-gravity vanishing — the principal-bundle topology is geometric, not thermodynamic. The first Chern class `c₁ = 1` is preserved; the linear gap `ℓ(ℓ+2) − ℓ(ℓ+1) = ℓ` is preserved.

The genuinely substrate-physical question at extremality is: **does the substrate continue to encode information on the horizon when no thermal radiation is escaping?** The MFO answer is yes — the boundary-as-encoding-channel commitment is independent of the dissipation rate. This aligns with the standard answer: extremal BHs are stable, non-radiating, but have entropy and horizon area.

The `AdS₂ × S²` throat geometry has its own substrate-physics interpretation under MFO. The `AdS₂` factor is a non-compact symmetric space whose isometry group is `SL(2, ℝ)`. The refined structural law (PR #373) treats CMS Kerr's hidden conformal `SL(2, ℝ) × SL(2, ℝ)` structure as mechanism (i) at a non-abelian Lie factor. The near-extremal throat's `SL(2, ℝ)` symmetry is the same mechanism at a different scale — the throat-local mechanism-(i) realisation, distinct from the horizon-S²-global SO(3) realisation.

### §1.3 Leverage assessment

The standard near-extremal corrections are computed in the JT-gravity / Schwarzian-quantum-mechanics framework. MFO substrate-vs-excitation does not appear to predict different numerical corrections. The throat-`SL(2, ℝ)` substrate-physical reading is structurally consistent with the JT/Schwarzian programme but does not extend it.

Observationally: extremal and near-extremal astrophysical BHs are accessible via gravitational-wave observations (the dimensionless spin parameter `a/M ≈ 0.98` for the highest-spin LIGO events; nature does not produce many extremal BHs because Thorne 1974 — pre-2010 canonical — argued accretion limits `a/M` to `≈ 0.998`). No measured anomaly from standard near-extremal thermodynamics has been reported. The corrections themselves (low-temperature breakdown of Bekenstein-Hawking) are at scales `T ~ 1/M_BH` — utterly inaccessible for astrophysical BHs (`T_H` of solar-mass BH is ~10⁻⁷ K; the Schwarzian-correction regime would be at exponentially smaller temperatures still).

### §1.4 Mechanism implication

The refined structural law accommodates Territory 1 by adding the throat-`SL(2, ℝ)` mechanism-(i) realisation as a layered instance over the horizon-`SO(3)` realisation. This is consistent with Spike #18's layered-mechanism finding for Heisenberg + metaplectic. No mechanism (v) candidate emerges.

The closed-form near-extremal entropy `S = S_0 + c · T` is mechanism-(i) at the throat layer plus mechanism-(iv) corrections (integer-quantised throat-modes? — depends on detailed JT-gravity content; not pursued here). Layered (i) × (iv) reading is the cleanest mapping.

### §1.5 Verdict for Territory 1

**No-leverage.** The substrate-vs-excitation framing is consistent with standard extremal / near-extremal thermodynamics. The throat-`SL(2, ℝ)` substrate-physical reading is interpretively natural but does not predict numerical deviations. The refined structural law accommodates near-extremal corrections as layered (i) × (iv) mechanisms; no mechanism (v) candidate.

This is informative: MFO does not add to the well-developed extremal-BH literature. The user's "different expansion rates" claim is mute at extremality because the horizon-generator expansion vanishes by construction — the standard third-law-of-BH-thermodynamics frame already encapsulates the relevant content.

---

## §2. Territory 2 — Modified gravity (Lovelock, Gauss-Bonnet, higher-curvature)

### §2.1 Standard treatment

In Lovelock gravity (Lovelock 1971; canonical pre-2010) and its Gauss-Bonnet subcase (the lowest non-trivial higher-curvature term in Lovelock's series), the action includes terms `R²` of various contractions of the Riemann tensor. The equations of motion remain second-order, evading Ostrogradski instability. The horizon-area law `S = A/4` is replaced by Wald entropy (Wald 1993 — canonical pre-2010; Iyer-Wald 1994 generalisation — canonical pre-2010):

$$S = -2\pi \oint \frac{\partial L}{\partial R_{abcd}} \, \varepsilon_{ab} \varepsilon_{cd}$$

For Gauss-Bonnet specifically, this gives `S = A/4 + α · ∫ R_horizon` where `α` is the Gauss-Bonnet coupling.

Temperature in modified gravity is still defined via `T = ℏκ/(2π c k_B)` from the surface gravity; the entropy is modified. The first law `dM = T dS + Ω dJ + Φ dQ` continues to hold with the Wald-entropy `S`.

In `D ≥ 5` spatial dimensions, Lovelock theories admit non-spherical horizon topologies. Galloway-Schoen 2006 (canonical pre-2010) classified the allowed horizon topologies — `S^(D−2)`, `S^(D−3) × S^1` (black rings), Lens spaces in `D = 5`, and more exotic topologies for larger `D`. Each topology has its own Bekenstein-Hawking / Wald entropy structure and corresponding Hawking spectrum.

### §2.2 Where MFO might say something different

The MFO substrate-vs-excitation framing makes two structural commitments that touch modified gravity:

**Commitment A (Hopf-bundle realisation).** The §VII.4.1.1 mechanism uses the principal-`U(1)`-bundle structure of `S³ → S²` to realise the dimensional-projection encoding. In `D = 4` Schwarzschild, the horizon is `S²` and the natural higher-dimensional total-space candidate is `S³`. In `D = 5` Lovelock with a `S³` horizon, the Hopf-fibration framing is even more direct: the horizon IS the Hopf total space `S³`, and the U(1)-fibre structure is intrinsic.

This is a constructive structural fact, not a numerically distinct prediction. MFO under §VII.4.1.1 reads a `D = 5` Gauss-Bonnet `S³` horizon as already a Hopf-fibered surface — the entropy can be decomposed mode-by-mode using the principal-bundle spectral decomposition `λ_S³(ℓ) = λ_S²(ℓ) + ℓ`. Whether the entropy count matches Wald entropy term-by-term is a computable question.

**Commitment B (Casimir-decomposition universality, §VII.4.1.2).** The unified statement `λ_total = λ_M + C_2(ρ_G) + (cross-terms)` should hold for the modified-gravity horizon Laplacian as well, with the same group `G`-Casimir structure but modified base-Laplacian eigenvalues reflecting the higher-curvature corrections to the horizon geometry. The Spike series #7–#10 verified this universally across compact `U(1)` Hopf, compact `SU(2)` flat-bundle, and non-compact `SL(2, ℝ)²` CMS regimes; the modified-gravity case extends the family but does not introduce a new mechanism type.

### §2.3 Leverage assessment

In `D = 4` (standard observational regime): Gauss-Bonnet coupling `α` constrained by post-Newtonian and gravitational-wave observations to `α^(1/2) ≲ few km` (in dilatonic-Gauss-Bonnet variants probed by LIGO-Virgo-KAGRA). Standard astrophysical BHs in `D = 4` have negligible Gauss-Bonnet corrections to Hawking thermodynamics — corrections of order `(α/M²)` relative to leading `A/4` term. MFO does not predict different `α`-corrections from Wald entropy, so no observational distinction.

In `D ≥ 5` (theoretical regime, no astrophysical access): the Hopf-fibration framing has constructive content. A spike could compute the principal-`U(1)`-bundle spectral decomposition of a `D = 5` Lovelock `S³` horizon and compare to Wald-entropy term-by-term. If they agree mode-by-mode, this is a structural success for §VII.4.1.1's framework. If they disagree at any mode, that is a falsifier for MFO's specific Hopf-bundle realisation in higher-D.

Wider relevance: higher-D BH thermodynamics is an active theoretical area (black rings, Saturns, helical black strings — all `D ≥ 5` objects; no astrophysical access but structural content for AdS/CFT and string-theory programmes). MFO's principal-bundle framework could plug in here as a constructive route.

### §2.4 Mechanism implication

In `D = 4` Gauss-Bonnet: mechanism (i) at the horizon SO(3) is preserved; mechanism (iv) at the holographic / Wald-entropy lattice is the modified version of the A/4 lattice. Layered (i) × (iv) reading continues to apply with the lattice spacing shifted by Gauss-Bonnet corrections.

In `D ≥ 5` modified gravity with non-trivial horizon topology: mechanism (i) at the horizon's isometry group (`SO(D − 1)` for `S^(D − 2)`; modified for black rings) is the angular-sector mechanism; mechanism (iv) at the modified entropy formula. No mechanism (v) candidate; layered (i) × (iv) accommodates everything.

Spectral verification in higher-D: the Spike #17 result already verified the `SO(d + 1)` Casimir structure for `S^d` harmonics at `d ∈ {3, 4, 5, 6, 7}`. Extending to a Lovelock-modified Laplacian (which differs from the round-sphere Laplacian by curvature-correction terms) is a tractable computation.

### §2.5 Verdict for Territory 2

**Limited leverage in `D = 4`; potentially-constructive leverage in `D ≥ 5`.** MFO does not predict numerically distinct `D = 4` thermodynamics from Wald entropy. In higher-D modified-gravity contexts with non-trivial horizon topology, the §VII.4.1.1 Hopf-bundle framework provides a structurally natural way to organise the principal-bundle spectral decomposition that Wald entropy reaches by a different route. Whether they agree term-by-term in `D = 5` Gauss-Bonnet `S³` horizons is a computable spike question.

Observationally: no astrophysical access to higher-D BHs, so this is theoretical-structural-leverage only. Worth a small spike to settle constructively but not high-priority for the project's instrument-first stance.

---

## §3. Territory 3 — Page curve / islands / soft hair

### §3.1 Standard treatment

Page 1976 (canonical pre-2010) argued that for unitary BH evaporation, the entanglement entropy of the radiation must follow a "Page curve" — rising linearly to the Page time (half the radiation has been emitted), then falling linearly back to zero as the BH evaporates. The original Hawking 1975 (canonical pre-2010) calculation of thermal radiation gave a monotonically rising entropy, in contradiction with unitarity.

The islands-formula resolution (Penington 2019/2020, Almheiri-Engelhardt-Marolf-Maxfield 2019/2020 — flagged in Spike #19 §2.9 as **attempted-but-unverifiable** for specific arXiv IDs in this session; the structural claim is well-established in post-2020 literature) recovers the Page curve by adding island contributions to the entanglement entropy via quantum extremal surfaces (QES). The semiclassical formula `S(R) = min_{islands} [S_bulk(R ∪ Island) + Area(∂Island)/4G]` reproduces the Page curve.

A separate but related programme — soft hair (Hawking-Perry-Strominger 2016, well-known pre-2020 era; Donnay-Giribet-González-Pino 2016 and subsequent work on horizon soft-hair) — argues that BHs carry information in BMS asymptotic-symmetry charges (supertranslations, super-rotations) and in horizon-localised soft gauge / graviton modes. The asymptotic-symmetry group `bms₄` is infinite-dimensional, providing nominally infinite room for information.

### §3.2 Where MFO might say something different

The MFO §VII.4.1 commitment is sharp: "the black hole ends at the 2D boundary; there is no interior." Information is on the boundary by construction, throughout evaporation. The Page curve is **automatic** under MFO — there is no "interior to fall into," hence no source of late-time entanglement-entropy divergence. The boundary-locality bound on entanglement is structural, not derived.

The §VII.4.1.1 Hopf-bundle U(1)-fibre encoding specifies the **mechanism** by which the boundary carries information: each S² eigenmode at angular momentum `ℓ` receives a U(1)-phase channel of multiplicity `ℓ` (the spectral gap `λ_S³(ℓ) − λ_S²(ℓ) = ℓ`). The total information capacity of the boundary is `Σ_ℓ ℓ · (2ℓ + 1) = ` (formal divergence regulated by Planck-scale UV cutoff giving `A/4` Planck-area pixels — this matches Bekenstein-Hawking).

**The sharp distinguishing question:** does the Hopf-bundle U(1)-fibre mode-counting match the soft-hair / BMS-asymptotic-charge degeneracy bookkeeping mode-by-mode? Specifically:

- Soft-hair counting (Hawking-Perry-Strominger 2016 and follow-ups) gives mode-by-mode multiplicity per BMS-supertranslation generator at angular harmonic `(ℓ, m)`.
- Hopf-bundle counting (§VII.4.1.1 / Casimir-decomposition §VII.4.1.2) gives mode-by-mode multiplicity per U(1)-fibre harmonic over S²-base mode `(ℓ, m)`.
- These are **a priori** different objects: BMS supertranslations are asymptotic (at `ℐ⁺`); U(1)-fibre is local at the horizon.

But they may match. There is a strand of post-2010 literature (Haco-Hawking-Perry-Strominger 2018, which would require PDF verification to cite specifically; structural content: Kerr's hidden conformal symmetry algebra links horizon-local and asymptotic-charge structures) that proposes a structural relation between horizon-local and asymptotic-charge degrees of freedom. The MFO §VII.4.1.1 + §VII.4.1.2 framework, by its Casimir-decomposition universality, predicts that the principal-bundle spectral decomposition determines the mode counting at both layers, with the same `C_2(ρ_G)` structure linking them.

### §3.3 Leverage assessment

This is the **most concrete falsifiable spike candidate** in the scan. The question — do Hopf-bundle U(1)-fibre harmonics match soft-hair / BMS-supertranslation degeneracy mode-by-mode? — is computable.

- **Falsifier:** mode-by-mode discrepancy at any `(ℓ, m)` between principal-bundle decomposition and BMS / soft-hair counting.
- **Value if MFO is right:** §VII.4.1.1's principal-bundle framework provides a constructive route to soft-hair degeneracy counting, with the same Casimir structure that the refined structural law (PR #373) governs more broadly. This unifies the boundary-locality bound on information with the asymptotic-charge information bookkeeping.
- **Value if MFO is wrong:** a precise location for where §VII.4.1.1 fails. The principal-bundle framing would need refinement.

Observational accessibility: the soft-hair degeneracy is not directly observable, but it has consequences for Hawking-radiation entanglement structure. If a future high-precision Hawking-radiation entanglement measurement could be made (no current experimental access for astrophysical BHs; possibly accessible for analogue Hawking-radiation systems in BECs or fluid-mechanical setups — Unruh 1981; Steinhauer 2016 analog Hawking experiment, pre-2020 well-established), the entanglement-pattern predictions of MFO vs standard soft-hair could distinguish.

### §3.4 Mechanism implication

If MFO's Hopf-bundle counting matches soft-hair degeneracy: this is mechanism (i) at the SO(3) horizon × U(1) fibre, with the Casimir-decomposition `λ_total = λ_S² + ℓ` controlling the mode count. The refined structural law accommodates this via layered (i) × (iv) reading.

If MFO's Hopf-bundle counting disagrees: this is a candidate for **mechanism (v) refinement** — the bulk-boundary information channel might need a different organising principle than the principal-bundle decomposition. Or alternatively, mechanism (v) might be needed to mediate between horizon-local and asymptotic-charge layers.

Either outcome refines the structural law. The current 4-mechanism statement (PR #373) is consistent with the layered-(i)×(iv) reading; this spike would test it sharply.

### §3.5 Verdict for Territory 3

**Moderate-to-high leverage.** The Hopf-bundle vs soft-hair mode-counting comparison is concrete, falsifiable, and refines the refined structural law's content. It does not predict observationally-distinct content from standard treatments at the level of current observability, but it has structural-mathematical content that distinguishes MFO's specific principal-bundle realisation from alternative information-encoding frameworks (fuzzball, ER=EPR, AMPSS-style QES).

This is the strongest candidate for a follow-up **computational** spike — the comparison can be done with Lie-group representation theory and BMS-algebra mode counting, both of which are textbook.

---

## §4. Territory 4 — Cosmological horizons / de Sitter

### §4.1 Standard treatment

Gibbons-Hawking 1977 (canonical pre-2010): a static-patch observer in de Sitter spacetime with Hubble rate `H` sees a cosmological horizon at proper distance `c/H`, with temperature `T_dS = H ℏ / (2π k_B)` and entropy `S_dS = A_dS / (4 ℓ_P²) = π / (H² ℓ_P²)`.

For time-varying cosmologies (FLRW with non-constant `H(t)`), the situation is more subtle. Dynamical-horizon frameworks (Hayward 1994, 1998 isolated and dynamical horizons; Ashtekar-Krishnan 2002, 2004 generalisations — all canonical pre-2010) define horizons that evolve with the cosmological dynamics. The temperature and entropy generalise via the first law and Bousso 2002 (canonical pre-2010) covariant entropy bound to time-varying contexts.

The adiabatic limit gives `T_dS(t) = H(t) / (2π)` at leading order; higher-order corrections from `dH/dt` have been computed in various contexts (Frolov-Kofman 2003 horizon thermodynamics in slow-roll inflation — canonical pre-2010; subsequent literature on dynamical-horizon thermodynamics, pre-2020).

A separate active programme — Verlinde 2017 emergent dark energy (would require PDF verification for specific arXiv ID; arXiv:1611.02269 from memory of the field but not freshly verified in this session) — proposes that the observed late-time accelerated expansion (dark-energy era) is a consequence of an information-displacement effect at the cosmological horizon. The framework is entropic-gravity-based and predicts modifications to galactic rotation curves and large-scale-structure dynamics that are observationally testable (and contested).

### §4.2 Where MFO might say something different

This is the **native home** for the user's "different expansion rates" claim from Spike #19. In Schwarzschild Hawking, nothing was actually expanding; the conjecture washed because the framing didn't fit the setting. Cosmological-horizon thermodynamics is the setting where the framing fits cleanly: the 3D bulk has Hubble expansion rate `H`; the cosmological horizon (proper area `4π c²/H²`) has its own rate of change `dA/dt = -8π c² (dH/dt)/H³`. These **are** different rates.

The MFO substrate-vs-excitation commitment reads cosmological-horizon thermodynamics as follows:

- **Level 1 (substrate)**: the metric-field substrate has time-varying scale factor `a(t)`. The "vacuum" is a non-stationary state.
- **Level 2 (excitations)**: matter, radiation, and dark-energy components are localised / extended excitations of the substrate.
- **Cosmological horizon**: the 2D surface beyond which causal contact is lost from the static-patch observer. Under MFO §VII.4.1's "horizon ends the 3D" stance, the cosmological horizon is **literally** where 3D ends — the substrate's dimensional-projection condition applies here just as at a BH horizon.
- **"Different expansion rates" content**: the bulk Hubble expansion `H` describes Level-1 substrate dynamics; the cosmological-horizon area evolution `dA/dt` describes the boundary of the dimensional-projection. These are governed by different physical contents (substrate-dynamics vs boundary-encoding).

The Hopf-bundle U(1)-fibre realisation (§VII.4.1.1) at the cosmological horizon: the cosmological horizon is `S²`; the Hopf-fibration framework gives the same encoding-channel structure as at a BH horizon. The encoding capacity per unit horizon-area is the same `A/4` per Planck-area; the total encoding capacity scales with `1/H²`.

### §4.3 Leverage assessment

**This is the highest-leverage territory in the scan.** Three concrete avenues for MFO-distinctive content:

**Avenue A — modified-time-variation corrections to `T_dS`.** Standard adiabatic gives `T_dS(t) = H(t)/(2π)`. Substrate-physics might predict corrections at order `(dH/dt)/H²` that differ from standard slow-roll inflation calculations. The substrate's "ring-up/ring-down" timescale relative to `H` is the relevant scale; if substrate-physics says the ring-down is rapid compared to `H`, the adiabatic result holds; if slow, corrections appear. Whether MFO specifies this timescale is a question for the next spike.

**Avenue B — Verlinde 2017 emergent dark energy inheritance.** The substrate-vs-excitation framing is structurally close to Verlinde-Padmanabhan entropic / emergent gravity (Spike #19 §2.5–§2.6). Verlinde 2017 specifically extends the framework to predict late-time accelerated expansion as an information-displacement effect; this gives modifications to galactic rotation curves and large-scale-structure dynamics that are observationally probed. MFO inherits these predictions (positive or negative) by virtue of the structural alignment. The MFO substrate-physical commitment makes the framework-inheritance explicit; standard QFT-in-curved-spacetime + holographic-principle does not necessarily commit to the entropic-gravity interpretation.

**Avenue C — CMB and primordial gravitational-wave signatures.** Inflationary cosmological-horizon thermodynamics imprints on the CMB power spectrum and on the primordial GW background. If MFO predicts substrate-physical modifications to the inflationary horizon dynamics, these would be observationally probed by LiteBIRD / CMB-S4 / future CMB-polarisation experiments. Whether MFO actually predicts a measurable modification is the question; the avenue is at minimum observationally accessible.

### §4.4 Mechanism implication

The cosmological-horizon mechanism analysis:
- Angular sector at the horizon (S²): mechanism (i) at SO(3), same as Schwarzschild Hawking.
- Holographic / Bekenstein-Hawking entropy lattice: mechanism (iv) at `A/4` lattice, modified for time-varying `H`.
- **Possible mechanism (v) candidate**: if the substrate's time-variation rate enters the closed-form analysis in a way that does not reduce to mechanisms (i), (iii), (iv), this is a candidate. The classical inflationary cosmology already has accommodations for time-varying `H` (slow-roll parameters, etc.), and these reduce to integer-/rational-lattice quantisations in many cases — likely mechanism (iv) at a different lattice. Unclear whether MFO substrate-physics predicts a genuinely new mechanism (v) here.

The refined structural law's predictive content for Territory 4 is the same as for Schwarzschild Hawking (layered (i) × (iv)) at lowest order. Corrections from time-variation might activate further mechanisms; this is the spike's question.

### §4.5 Verdict for Territory 4

**Highest leverage of all six territories.** Cosmological-horizon thermodynamics under MFO substrate-vs-excitation is the native home for the user's "different expansion rates" intuition. The substrate-physics framing inherits Verlinde-Padmanabhan-style entropic/emergent-gravity content, which has testable observational predictions (contested but probed). The mechanism analysis is open — a possible mechanism (v) candidate cannot be ruled out at this scan level.

The cleanest spike-#20 candidate: **does MFO substrate-physics predict numerically distinct cosmological-horizon thermodynamics under time-varying `H` that disagrees with standard adiabatic Hayward / Ashtekar-Krishnan dynamical-horizon predictions, and does the substrate-physical commitment commit MFO to specific Verlinde-2017-style observable predictions?**

This is the strongest candidate for follow-up.

---

## §5. Territory 5 — Unruh effect (accelerating observer in Minkowski)

### §5.1 Standard treatment

Unruh 1976 (canonical pre-2010): an observer accelerating with proper acceleration `a` in Minkowski spacetime registers a thermal flux of Rindler-mode quanta at temperature `T_U = ℏ a / (2π c k_B)`. The Rindler horizon — the future causal boundary visible to the accelerating observer — has surface gravity `κ_R = a`, recovering the universal formula `T = ℏκ/(2π c k_B)`.

Crispino-Higuchi-Matsas 2008 (canonical pre-2010 review, Rev. Mod. Phys. 80, 787): comprehensive review of Unruh effect.

Closely related: Bisognano-Wichmann 1975-76 (canonical pre-2010 — Bisognano & Wichmann, J. Math. Phys. 17 (1976) 303 — modular Hamiltonian of the Rindler wedge equals the boost generator); Hartle-Hawking 1976 thermofield-double vacuum (canonical pre-2010 — Hartle & Hawking, Phys. Rev. D 13 (1976) 2188); Bell-Leinaas 1983 (canonical pre-2010 — observable thermal-bath spin-polarisation in storage rings) — well-established consequences of the Unruh effect in spin physics.

Wald's theorem (1984 *General Relativity*, §14.4; canonical pre-2010): any bifurcate Killing horizon thermalises with temperature `T = ℏκ/(2π c k_B)`. This is the universal framework underlying Hawking + Unruh + de-Sitter thermalisation; the boost generator in Minkowski is a global Killing vector with the Rindler horizon as its bifurcation surface.

### §5.2 Where MFO might say something different

The MFO commitment is: substrate-physics is global and Lorentz-invariant in flat space. The metric-field substrate is the Minkowski vacuum; this is observer-independent.

The Rindler horizon is **observer-dependent** — it exists only for accelerating observers and at the location dictated by the acceleration. Is the Rindler horizon a substrate-physical object under MFO?

A naive reading would say no: the Minkowski substrate doesn't care about the observer's acceleration; the Rindler horizon is a coordinate-dependent surface. Under this reading, the Unruh thermal response is a property of the detector-substrate **coupling** (the detector's history along an accelerated trajectory thermalises with respect to the substrate vacuum), not a substrate thermalisation. The substrate remains in vacuum throughout.

But this is too quick. The correct substrate-physical reading uses Killing-vector structure: the boost generator in Minkowski is a global Killing vector of the substrate. Its bifurcation surface (the Rindler horizon for a given acceleration) is a substrate-physical structure once the boost-orbit is selected. The accelerating observer is a probe that follows a boost-orbit; the Rindler horizon is then the natural substrate-physical thermalisation surface for that orbit.

Under this reading, MFO substrate-physics recovers Unruh exactly: the Killing-vector structure is substrate-physical; thermalisation on a bifurcate Killing horizon is universal (Wald's theorem); the result is the same as standard.

### §5.3 Leverage assessment

The substrate-vs-excitation framing accommodates Unruh via the Killing-vector reading. No numerically distinct prediction emerges. The "probe-coupling vs substrate-thermalisation" interpretive distinction does not yield testable difference — the detector response is the same observable in both readings.

The Hopf-bundle U(1)-fibre realisation does not naturally apply at the Rindler horizon: Rindler horizon topology is `ℝ²` (or `ℝ × ℝ`), not `S²`. The principal-bundle framework would need a different organising structure (perhaps a `U(1)` bundle over the Rindler plane). The §VII.4.1.1 framework's content is not directly transferable.

The Casimir-decomposition universality (§VII.4.1.2): the Rindler-wedge isometry group is the Poincaré group restricted to the wedge. The boost subgroup `SO(1, 1)` is the relevant Killing-vector group. `SO(1, 1)` is non-compact and abelian; the §VII.4.1.2 framework's `C_2(ρ_G)` content is degenerate (no quadratic Casimir for abelian group). This is the "abelian-wall obstruction" (per refined structural law row 2, KY Kerr): closed-form spectral compression is not available via mechanism (i) at this abelian Lie factor.

Interestingly, this means: Unruh's thermal-spectrum closed form (Planck distribution at `T_U`) does **not** arise from mechanism (i) at the Rindler-horizon angular sector. Instead, it arises directly from the Wald-theorem Killing-vector thermalisation argument — which is a thermal-equilibrium statement, not a closed-form-spectral-compression statement in the refined-law sense.

### §5.4 Mechanism implication

Unruh's closed-form Planck spectrum: the Planck distribution `1/(e^{ℏω/k_B T} − 1)` is universal — it appears whenever a system thermalises at temperature `T`. This is a mechanism-(iv) instance (integer-lattice mode occupation in thermal equilibrium), or more precisely a thermal-equilibrium statement that the closed-form-spectral-compression framework treats as a kinematic given.

The refined structural law's content for Unruh is: the **temperature** is determined by Killing-vector surface gravity (kinematic); the thermalised spectrum is mechanism (iv) at the Bose-Einstein lattice. Mechanism (i) is degenerate at the Rindler-horizon abelian boost group; no mechanism (v) candidate emerges.

### §5.5 Verdict for Territory 5

**No-leverage.** MFO substrate-physics, properly applied via Killing-vector boost-orbit structure, recovers Unruh exactly. The interpretive distinction between "probe-coupling thermalisation" and "substrate thermalisation" does not yield numerically distinct predictions. The Hopf-bundle U(1)-fibre framework does not naturally apply at Rindler horizons (topology mismatch). The refined structural law accommodates Unruh as kinematic-temperature × mechanism-(iv) thermal lattice; no mechanism (v) candidate.

The user's "different expansion rates" claim does not apply meaningfully to Rindler: there is no expansion in Minkowski space. The Rindler horizon's "surface gravity" is the acceleration `a`, not an expansion rate.

---

## §6. Territory 6 — Black-hole interior / firewall paradox

### §6.1 Standard treatment

Almheiri-Marolf-Polchinski-Sully (AMPS) 2013 (canonical pre-2020 era; well-established): the firewall paradox identifies an apparent contradiction among (a) unitarity of evaporation, (b) equivalence-principle smoothness for infalling observers, and (c) validity of QFT in EFT regime outside the horizon. Original AMPS resolution: drop (b), have a firewall (high-energy radiation barrier) at the horizon.

Alternative resolutions: ER=EPR (Maldacena-Susskind 2013, well-established pre-2020 era — geometric duality between Einstein-Rosen bridge and Einstein-Podolsky-Rosen entangled state); fuzzball proposal (Mathur 2005 onwards — pre-2010 canonical for the proposal, ongoing development); holographic complexity (Susskind 2014 and onwards); islands-formula resolution (Penington 2019-2020 + AEMM 2019-2020, flagged as attempted-but-unverifiable per Spike #19 §2.9). The dominant post-2020 consensus is islands-formula-based, with ER=EPR providing a geometric heuristic.

### §6.2 Where MFO might say something different

The MFO §VII.4.1 commitment — "the black hole ends at the 2D boundary; there is no interior" — sidesteps the firewall paradox structurally. The contradiction among (a)–(c) requires positing an interior with its own dynamics; MFO denies that. The infalling observer's "experience" of crossing the horizon is, under MFO, a coordinate description of the dimensional-projection encoding process — the matter being projected from 3D-bulk localisation to 2D-boundary encoding. There is no "smooth crossing into an interior" because the interior is not a substrate-physical region; the observer's clock-time description of the encoding is what coordinate-Schwarzschild calls "crossing the horizon."

This is interpretive, not numerical. The standard firewall-resolution proposals (fuzzball, ER=EPR, islands) all share the broad commitment that the naive QFT-in-curved-spacetime interior picture is structurally wrong. MFO is one specific commitment among these alternatives; it does not predict numerically distinct content from them.

### §6.3 Leverage assessment

Observable consequences of firewall-resolution alternatives:
- **Gravitational-wave signatures of mergers**: standard models (with interior) match LIGO-Virgo-KAGRA observations of binary BH mergers. MFO no-interior models would presumably reproduce the same GW signatures because the GW emission is from bulk dynamics outside the horizon. No observational distinction.
- **Hawking-radiation entanglement structure**: MFO predicts boundary-locality bound from the start; standard requires QES / islands construction. Same numerical predictions for the entanglement spectrum (Territory 3 covered this).
- **Horizon-scale shadow imaging (EHT)**: the M87* and Sgr A* shadow images are consistent with Kerr-metric predictions to within current resolution. MFO no-interior models would presumably reproduce the same images because the shadow is determined by null-geodesic structure outside the horizon. No observational distinction.

The firewall paradox's resolution by MFO is structurally compatible with the dominant alternatives, and the observational tests are the same as Territory 3.

### §6.4 Mechanism implication

No mechanism (v) candidate emerges. The dimensional-projection encoding is mechanism (i) at the SO(3) horizon × mechanism (iv) at the A/4 lattice, same as Schwarzschild Hawking. The firewall paradox's resolution is interpretive, not a closed-form-spectral-compression question.

### §6.5 Verdict for Territory 6

**No-leverage beyond Territory 3.** The firewall paradox is resolved structurally by MFO's no-interior stance, but this resolution is one among several (fuzzball, ER=EPR, islands) that share the broad commitment. No numerically distinct testable prediction. The interpretive distinction does not yield observational content beyond what Territory 3's mode-counting questions cover.

The user's "different expansion rates" claim is not directly relevant at the firewall scale — the firewall is about quantum-information structure across the horizon, not about expansion-rate dynamics.

---

## §7. Final ranking

### §7.1 Ranked list

1. **Territory 4 (cosmological horizons / de Sitter)** — highest leverage. Native home for the user's "different expansion rates" intuition. Substrate-physics framing inherits Verlinde-Padmanabhan-style entropic / emergent-gravity content that is observationally probed (CMB power spectrum, galactic-rotation tests, large-scale-structure). Possible mechanism (v) candidate from time-variation contributions to closed-form analysis. The cleanest follow-up spike candidate.

2. **Territory 3 (Page curve / islands / soft hair)** — moderate-to-high leverage. Concrete computational question: does §VII.4.1.1's Hopf-bundle U(1)-fibre mode count match soft-hair / BMS-asymptotic-charge degeneracy bookkeeping mode-by-mode? Refines the refined structural law via either layered-(i)×(iv) confirmation or mechanism-(v) candidate.

3. **Territory 2 (modified gravity, higher-D)** — limited leverage in `D = 4`; potentially-constructive leverage in `D ≥ 5` where horizon topologies become non-trivial (`S³`, `S² × S¹`, Lens spaces). The Hopf-bundle framework provides a structurally natural decomposition that might or might not match Wald-entropy term-by-term. Low observational priority; theoretical-structural priority only.

### §7.2 No-leverage territories

- **Territory 1 (extremal / near-extremal)** — standard third-law BH thermodynamics + JT-gravity / Schwarzian-mode framework already covers it. MFO's `AdS₂ × S²` throat substrate-reading is interpretively natural but does not predict numerical deviations.

- **Territory 5 (Unruh effect)** — properly applied substrate-physics via global-Killing-vector boost-orbit structure recovers Unruh exactly. Hopf-bundle framework does not naturally apply at Rindler horizons (topology mismatch). The user's "different expansion rates" claim is mute in Minkowski space.

- **Territory 6 (firewall paradox)** — structurally compatible resolution to standard alternatives (fuzzball, ER=EPR, islands), but no numerically distinct prediction. Observational content covered by Territory 3.

### §7.3 Honest-negative tally

Three of six territories are no-leverage. This is informative: MFO substrate-physics is **not** universally productive of distinguishing content. It has bite in cosmological-horizon settings (where genuine time-variation makes the "different expansion rates" content meaningful), in soft-hair / mode-counting settings (where the Hopf-bundle framework specifies a concrete decomposition that may or may not match standard counting), and in higher-D modified-gravity contexts (where horizon topology becomes nontrivial). It does **not** have bite at extremal limits (where no expansion exists), in flat-space accelerating-observer settings (where global Killing-vector structure covers everything), or in firewall-paradox-resolution settings beyond what Territory 3 covers.

The user's intuition correctly points at substrate-physics as a relevant content layer, but the **specific** leverage requires the substrate to be doing **physical** work (Verlinde-Padmanabhan emergent-gravity coupling; Hopf-bundle mode counting). Where the substrate is doing only kinematic work (extremal limits, Rindler boost-orbits), MFO recovers the standard treatment exactly.

---

## §8. Recommended follow-up spikes

### §8.1 Spike #20A — Cosmological-horizon thermodynamics under MFO (highest priority)

**Question:** Does MFO substrate-vs-excitation predict deviations from the adiabatic Hawking-Gibbons formula `T_dS(t) = H(t) / (2π)` when `dH/dt ≠ 0`, that are distinguishable from standard Hayward / Ashtekar-Krishnan dynamical-horizon predictions and from standard slow-roll-inflation corrections? Does the substrate-physical commitment commit MFO to specific Verlinde-2017-style observable predictions on galactic-rotation-curve / large-scale-structure dynamics?

**Falsifier:** any explicit numerical disagreement with standard adiabatic + dynamical-horizon dHC predictions in regimes where `dH/dt` is non-negligible. If MFO predicts (e.g.) larger primordial-GW amplitude in inflation than standard slow-roll calculations, and observation rules this out, MFO substrate-physics in cosmology is falsified.

**Value if MFO is right:** cosmological-horizon thermodynamics under substrate-physics provides a constructive route to Verlinde-2017-style emergent-dark-energy predictions, with §VII.4.1.1's Hopf-bundle framework giving the spectral realisation. This is the strongest candidate for genuinely-new predictive content from the MFO framework, since the holographic / emergent-gravity programmes are observationally probed.

### §8.2 Spike #20B — Hopf-bundle vs soft-hair / BMS mode counting (moderate priority)

**Question:** Does the §VII.4.1.1 principal-`U(1)`-bundle spectral decomposition of the BH horizon's mode content match the soft-hair / BMS-asymptotic-supertranslation degeneracy bookkeeping mode-by-mode, for the same `(ℓ, m)` angular harmonic structure?

**Falsifier:** mode-by-mode discrepancy between Hopf-bundle counting (`λ_S³(ℓ) − λ_S²(ℓ) = ℓ` per §VII.4.1.1) and BMS-supertranslation degeneracy per `(ℓ, m)` (from BMS-algebra mode counting; pre-2020 well-established structure).

**Value if MFO is right:** §VII.4.1.1's principal-bundle framework supplies a constructive route to soft-hair degeneracy counting that unifies horizon-local and asymptotic-charge information bookkeeping under the Casimir-decomposition universality of §VII.4.1.2. Adds to the refined-structural-law evidence base as a structural test.

### §8.3 Spike #20C — Higher-D Lovelock horizon spectral decomposition (low priority, exploratory)

**Question:** In `D = 5` Gauss-Bonnet gravity with `S³` horizon topology, does the §VII.4.1.1 principal-`U(1)`-bundle Hopf-fibration spectral decomposition match the Wald-entropy formula mode-by-mode? More generally, in higher-D Lovelock theories with various horizon topologies (`S³`, `S² × S¹`, Lens spaces), does the principal-bundle framework reproduce Wald-entropy term-by-term?

**Falsifier:** explicit mode-by-mode discrepancy between Hopf-bundle decomposition and Wald entropy in `D = 5` Gauss-Bonnet.

**Value if MFO is right:** principal-bundle framework provides a structurally natural decomposition for higher-D modified-gravity entropy formulae. Limited observational consequence (no astrophysical access to higher-D BHs), but theoretical-structural content for the refined structural law's reach.

---

## §9. Citation discipline note

Per `feedback_pdf_extraction_citation_discipline.md` and Spike #19's discipline counter-clause:

**Pre-2010 canonical works (cited freely, exempt from PDF re-verification):**

- Hawking 1974, 1975 (Hawking radiation)
- Bekenstein 1973 (entropy bound)
- Page 1976 (Page curve, Hawking flux per species)
- Unruh 1976 (Unruh effect)
- Bisognano-Wichmann 1975-76 (modular Hamiltonian of Rindler wedge)
- Hartle-Hawking 1976 (thermofield-double vacuum)
- Gibbons-Hawking 1977 (de Sitter horizon thermodynamics)
- Bell-Leinaas 1983 (storage-ring Unruh spin-polarisation)
- Wald 1984 *General Relativity* §14.4 (universal Killing-horizon thermalisation)
- Israel 1986 (third law of BH thermodynamics)
- Lovelock 1971 (Lovelock gravity)
- Bertotti-Robinson 1959 (throat geometry — pre-2010 canonical)
- Wald 1993 `gr-qc/9307038` (BH entropy as Noether charge; canonical pre-2010, also cited in Spike #19)
- Iyer-Wald 1994 `gr-qc/9403028` (Wald entropy generalisation; canonical pre-2010)
- Jacobson 1995 `gr-qc/9504004` (Einstein equations from horizon thermodynamics; cited in Spike #19)
- Strominger-Vafa 1996 `hep-th/9601029` (microscopic BPS state count for extremal BHs; canonical pre-2010)
- Hayward 1994 / 1998 (isolated and dynamical horizons; pre-2010 canonical)
- Ashtekar-Krishnan 2002, 2004 (dynamical-horizon framework; pre-2010 canonical)
- Bousso 2002 `hep-th/0203101` (holographic-principle review; cited in Spike #19)
- Frolov-Kofman 2003 (slow-roll horizon thermodynamics; pre-2010 canonical)
- Crispino-Higuchi-Matsas 2008 (Unruh effect review *Rev. Mod. Phys.* 80, 787; pre-2010 canonical)
- Galloway-Schoen 2006 (horizon-topology classification; pre-2010 canonical)
- Mathur fuzzball proposal (2005 onwards; pre-2010 canonical for the foundational papers)
- Steinhauer 2016 analog Hawking experiment (referenced for analog-system observability; pre-2020 well-established at the time)

**Pre-2020 referenced works (well-established era; specific arXiv IDs not freshly verified in this session):**

- 't Hooft 1993 `gr-qc/9310026` (holographic principle — cited in Spike #19 as exempted per discipline counter-clause)
- Susskind 1995 `hep-th/9409089` (world as hologram — cited in Spike #19)
- Maldacena-Stanford-Yang 2016 (JT gravity / Schwarzian programme — pre-2020 era; well-established; specific arXiv ID not freshly verified)
- Hawking-Perry-Strominger 2016 (soft-hair on BHs — pre-2020 era; well-established; arXiv:1601.00921 from memory but not freshly verified)
- Donnay-Giribet-González-Pino 2016 (horizon-soft-hair; pre-2020 era)
- AMPS 2013 (firewall paradox — pre-2020 era; well-established)
- Maldacena-Susskind 2013 (ER=EPR; pre-2020 era; well-established)
- Verlinde 2010 / 2011 `arXiv:1001.0785` (entropic gravity — characterised in Spike #19 §2.5 with care-flag; not freshly PDF-verified in this session)
- Padmanabhan 2010 `arXiv:0911.5004` (emergent gravity — characterised in Spike #19 §2.6 with care-flag; not freshly PDF-verified in this session)
- Anninos-Hartman-Strominger 2011 (dS/CFT; pre-2020 era, not freshly verified)

**Attempted-but-unverifiable in this session (2020+ refs requiring PDF verification before merge):**

- Penington 2019/2020 + Almheiri-Engelhardt-Marolf-Maxfield 2019/2020 (islands-formula / quantum-extremal-surface Page-curve resolution) — flagged in Spike #19 §2.9 as attempted-but-unverifiable; same flag applies here. Specific arXiv IDs not given.
- Verlinde 2017 emergent dark energy — possibly arXiv:1611.02269 from memory, but **not freshly PDF-verified** in this session. Any merged content citing this paper authoritatively must PDF-verify.
- Haco-Hawking-Perry-Strominger 2018 (Kerr hidden-conformal soft-hair) — pre-2020 in publication year, but late enough to warrant verification; not freshly verified.
- Iliesiu-Turiaci 2020 (near-extremal corrections in JT-gravity / Schwarzian) — post-2020, not freshly verified; only referenced topically.

The scan's conclusions (territory rankings, leverage assessments, recommended spikes) do not depend on the specific arXiv IDs of the post-2020 works. The structural claims (islands-formula Page-curve resolution; Verlinde-2017-style emergent dark energy; JT-gravity Schwarzian near-extremal corrections) are well-established in the post-2020 literature; the specific citations should be PDF-verified at the time of any spike-#20 work that would lift this content into MFO notebook sections or other shared documents.

---

## §10. Cross-references

- **Spike #19** `spike_19_mfo_hawking_radiation_dof_mismatch_2026-05-13.md` on branch `research/spike-19-mfo-hawking-radiation-dof-mismatch` (PR #374, draft) — the narrow DoF-mismatch test whose mostly-pure-wash finding seeded this broader leverage scan. Verdict-compatibility: Spike #19's finding holds (Schwarzschild Hawking is mostly-pure-wash under MFO); Spike #19b extends the question to six territories and identifies Territory 4 (cosmological / de Sitter) as the highest-leverage candidate where the user's "different expansion rates" intuition gains genuine bite.

- **Refined structural law consolidation** `refined_structural_law_consolidation_2026-05-13.md` on `main` (PR #373) — 4-mechanism law with layered (i) × (iv) reading. The scan's Territory 4 raises a possible mechanism (v) candidate from substrate-physical time-variation contributions; spike #20A would test this.

- **MFO notebook §VII.1.1** (two-level substrate / excitation ontology) at `docs/antikythera-maths/mfo_spectral_research_notebook.md` — the foundational ontology underlying all six territories' MFO analyses.

- **MFO notebook §VII.4** (Hawking radiation as dimensional mismatch); **§VII.4.1** (black-holes-end-at-the-2D-boundary stance); **§VII.4.1.1** (Hopf-bundle U(1)-fibre realisation); **§VII.4.1.2** (Casimir-decomposition universality) — sections directly engaged by the scan; Territory 3 and 4 test the Hopf-bundle and Casimir-decomposition machinery.

- **`user_stance_string_theory_instrument_first.md`** — informs the leverage assessment: numerical predictions are "ring-up / ring-down on real substrate," not vocabulary games. The scan applies this test territory-by-territory; the three no-leverage territories (1, 5, 6) are no-leverage precisely because the substrate-physical content reduces to known kinematic / interpretive content.

- **`user_stance_hyper_as_3d_spatial_interface.md`** — informs the application of "spherical compression" operator across the six territories: it applies cleanly to Schwarzschild (S² horizon), Kerr (oblate-S²), cosmological-horizon (S²), but not to Rindler (no spherical-interface topology). The application is consistent across territories.

- **`user_stance_fiber_as_spatially_absent_encoding.md`** — informs the Hopf-bundle interpretation: the U(1) fibre is spatially absent from 3D perspective, encoded algebraically via the principal-bundle structure. Territories 2, 3, 4 engage this content most directly.

- **`feedback_pdf_extraction_citation_discipline.md`** — informs §9's citation discipline. Pre-2010 canonical works exempt; 2020+ refs flagged as attempted-but-unverifiable.

- **`feedback_no_mvp_framing.md`** — informs the scan's structure: full coverage of all six territories with substantive evaluation per territory, not subset coverage. Honest-negative on three of six is itself the full-coverage finding.

- **`feedback_no_lineage_claims_in_notebook.md`** — informs the scan's treatment of Verlinde-Padmanabhan / fuzzball / ER=EPR / islands programmes: technical / result-specific citations only; no lineage claims about "MFO is the natural extension of Verlinde-Padmanabhan." The scan locates MFO substrate-physics as structurally close to entropic / emergent gravity, not as descended from it.

---

## §11. Discipline checklist

- **No shared-file edits.** This spike note is strictly srmech-local at `docs/srmech/notes/spike_19b_mfo_horizon_thermodynamics_leverage_2026-05-13.md`. MFO notebook, CHANGELOG.md, README.md, refined-structural-law consolidation file, and all other shared documents are untouched. Per `project_srmech_dedicated_updates_gate.md` (lifted 2026-05-09), srmech absorption findings land freely without shared-file impact.

- **No verification scripts written.** The scan is a leverage-scan + literature-overlap analysis; no novel numerical content requiring a script. The proposed spike #20A / #20B / #20C would each generate scripts if executed.

- **No NDJSON sidecar.** This is a literature-and-structural-analysis spike with ranked output; no tabular outputs emerged. If a future spike formalises the literature-overlap mapping for the recommended spike #20 candidates, NDJSON sidecars would be warranted then.

- **Pre-2010 canonical citations** are exempt from PDF re-verification per the discipline counter-clause; explicitly enumerated in §9.

- **2020+ citations** (Penington / AEMM islands-formula, Verlinde 2017 emergent dark energy, Iliesiu-Turiaci 2020 near-extremal JT corrections, Haco-Hawking-Perry-Strominger 2018 Kerr soft-hair) are flagged in §9 as **attempted-but-unverifiable** in this session. The scan's verdict does not depend on the specific arXiv IDs; structural claims are widely-established. Any merge of this content into MFO notebook sections must PDF-verify these citations.

- **No lineage claims** about external work, per `feedback_no_lineage_claims_in_notebook`. MFO substrate-physics is positioned as structurally adjacent to entropic / emergent gravity programmes (Verlinde-Padmanabhan), not as a "natural extension" of any author's programme.

- **No MVP framing.** Full coverage of all six territories at substantive depth per territory, plus ranked output, plus three recommended follow-up spike candidates. No subset cut.

- **Honest-negative valid.** Three of six territories are no-leverage; this is the full-coverage finding. The user's intuition correctly points at substrate-physics, but the specific leverage requires the substrate to be doing physical work — concentrated in Territory 4 (cosmological), Territory 3 (mode-counting), and Territory 2 (higher-D modified gravity).

- **Topic-only briefing followed.** The conductor's brief described topics; the spike built citation chains from pre-2010 canonical works freely, flagged 2020+ works as attempted-but-unverifiable per Spike #19's pattern, and described post-2010 borderline works (Hawking-Perry-Strominger 2016, AMPS 2013, ER=EPR 2013, Maldacena-Stanford-Yang 2016) by topic with care-flags where freshness was uncertain.

---

## §12. Branch and commit metadata

- **Base commit:** `main` (HEAD at spike start — refined structural law consolidation merged via PR #373).
- **Spike branch:** `research/spike-19b-mfo-horizon-thermodynamics-leverage`.
- **Commit message:** `research(srmech): Spike #19b MFO — horizon-thermodynamics leverage scan — Territory 4 (cosmological / de Sitter) top-ranked`.
- **No push, no PR.** Per conductor brief: strictly local notes for review; the conductor decides whether to PR.
- **No shared files touched.** MFO notebook, CHANGELOG.md, README.md, refined-structural-law consolidation file all untouched.
