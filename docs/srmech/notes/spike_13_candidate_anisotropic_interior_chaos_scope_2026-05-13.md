# Spike #13 Candidate — Anisotropic Interior Chaos Scope

**Date:** 2026-05-13
**Author:** Concertmaster subagent, dispatched by main conductor
**Branch:** `research/spike-13-anisotropic-interior-chaos` (branched from `main` @ `07d1a7e`)
**Status:** Scoping document only. No computation run. User to decide whether this becomes Spike #13.
**Discipline notes:**
- PDF-verified all 2020+ citations per `memory/feedback_pdf_extraction_citation_discipline.md`.
- No lineage claims per `memory/feedback_no_lineage_claims_in_notebook.md`.
- Honest-negative possibility is given equal weight to positive-result possibility.
- The user-prompt-named references "Cardoso-Cavaglià 2008" and "Stanish-Iglesias 2010" did **not** verify as direct anchors for *interior* Kerr chaos — corrected below.

---

## 0. Source — task and stance

Task `#174` of the project queue: *"Future research — interior anisotropic forcing from spinning boundary → non-Killing perturbation → chaotic bulk regime."*

User stance (paraphrased): the **topology** of the Kerr interior stays closed (no donut opens), but the **interior dynamics** receive anisotropic forcing sourced by the spinning outer surface; this forcing breaks Killing-tensor conservation laws (so Carter separability dies); the bulk regime becomes chaotic. The proposed spike asks: does this open a *fourth side* of the framework reach diagram, alongside the three sides established by Spikes #9/#10, #11, #12A?

This document scopes that question. It does not pre-commit to a positive outcome.

---

## 1. Math precision of "non-Killing perturbation"

Killing tensors `K_{ab}` satisfy
$$\nabla_{(a} K_{bc)} = 0$$
(symmetric covariant-derivative-vanishing). The rank-2 Killing tensor of Kerr is `K_{ab} = k_{ac}\,k_b{}^c` where `k_{ab}` is the principal conformal-Killing-Yano (CKY) 2-form (Penrose-Floyd 1973; Frolov-Krtouš-Kubizňák 2017, *Living Rev. Rel.* 20:6, arXiv:1705.05482). The Carter constant on geodesics is the conserved quantity `K = K_{ab} \dot x^a \dot x^b`. For wave perturbations the operator `K̂ = \nabla_a K^{ab} \nabla_b` is the rank-2 symmetry operator whose eigenvalue is the Teukolsky angular separation constant `λ_{s,ℓm}(aω)`.

**Three distinct precise senses of "non-Killing perturbation":**

**(i) Metric perturbation breaks the Killing tensor.** Take δg_{ab} sourced by an anisotropic stress-energy δT_{ab} (linearized Einstein: `δG_{ab}[δg] = 8πG\,δT_{ab}`). The induced perturbation δK_{ab} of the would-be Killing tensor generically satisfies `\nabla_{(a} (K + δK)_{bc)} ≠ 0`. The Carter constant ceases to be conserved; geodesics become a 4-dof Hamiltonian system with only 3 conserved quantities (`E`, `L_z`, mass-shell `g^{ab} p_a p_b = -μ²`), which is **provably non-integrable in the Liouville-Arnold sense** for generic δK_{ab}. This is the Lukes-Gerakopoulos-Apostolatos-Contopoulos 2010 setup (arXiv:1003.3120) and the entire "bumpy black hole" / EMRI non-Kerr literature.

**(ii) Source-driven anisotropic forcing without metric back-reaction.** Treat `δg = 0` but add an anisotropic external force `F^a(x)` to the geodesic equation: `\ddot x^a + Γ^a{}_{bc} \dot x^b \dot x^c = F^a`. Carter-conservation now fails because `\dot K = 2 K_{ab} F^a \dot x^b ≠ 0`. This is the "spinning boundary drives anisotropic interior force" picture in its cleanest form. It is the **Bombelli-Calzetta 1992** setup (CQG 9:2573 — chaos under periodic external forcing of Schwarzschild geodesics, via Melnikov method).

**(iii) Stress-energy backreaction at the inner boundary.** Quantum or matter flux at the **inner horizon** (Cauchy horizon `r_-`) sources anisotropic δT_{ab} in the interior. McMaken 2024 (PRD 110:045019, arXiv:2405.13221) explicitly: *"the initial backreaction from the RSET does not evolve the spacetime toward any known regular or extremal configuration, but instead it brings the local interior geometry toward a chaotic, spacelike singularity."* This is the **closest published match** to the user's "spinning boundary → anisotropic forcing → chaotic interior" framing.

**Math-precision verdict (one sentence):** A "non-Killing perturbation" can be made precise in three inequivalent ways — (i) δg-induced δK ≠ Killing, (ii) external Carter-violating force F^a, (iii) stress-energy-backreaction-sourced δT_{ab} in the interior — and the user's conjecture maps cleanest onto (iii), where there *is* a 2024 published result (McMaken) confirming chaotic-singularity outcome from rotation-sensitive quantum flux, though the *spectral* / *Lie-algebraic* statement of the conjecture remains unformalised.

---

## 2. Literature scoping — PDF-verified anchors

### 2a. Verified-strong anchors (load-bearing for spike design)

| # | Citation | arXiv / DOI | Verification | Why it matters |
|---|---|---|---|---|
| 1 | **Bombelli & Calzetta 1992**, "Chaos around a black hole" | Class. Quantum Grav. **9**:2573 | Title + authors + journal verified via WebSearch 2026-05-13; abstract retrieved | Melnikov-method canonical paper for *periodic-external-perturbation → homoclinic chaos* on Schwarzschild geodesics. The original "non-Killing perturbation produces chaos" demonstration. |
| 2 | **Lukes-Gerakopoulos, Apostolatos, Contopoulos 2010**, "An observable signature of a background deviating from Kerr" | Phys. Rev. D **81**:124005, arXiv:1003.3120 | PDF abstract retrieved 2026-05-13; authors verified (NOTE: user prompt's "Stanish-Iglesias 2010" does NOT match — actual canonical 2010 reference is L-G-A-C) | Generic non-axisymmetric perturbation of Kerr → Hamiltonian non-integrability diagnosed by Poincaré sections + Birkhoff chains of islands. The methodological exemplar for the spike. |
| 3 | **Frolov, Krtouš, Kubizňák 2017**, "Black holes, hidden symmetries, and complete integrability" | Living Rev. Rel. **20**:6, arXiv:1705.05482 | Title + authors verified 2026-05-13; matches Spike #11 KY-review record | Definitive reference for the principal-CKY-tensor mechanism behind Kerr integrability. Sets the baseline that "non-Killing perturbation" deviates from. |
| 4 | **McMaken 2024**, "Backreaction from quantum fluxes at the Kerr inner horizon" | Phys. Rev. D **110**:045019, arXiv:2405.13221 | PDF abstract retrieved 2026-05-13; chaotic-singularity claim verbatim | **Closest published match to user's conjecture.** Quantum stress-energy backreaction at the rotating inner horizon → chaotic spacelike singularity, with spin parameter `a` central. |
| 5 | **Destounis, Angeloni, Vaglio, Pani 2023**, "Extreme-mass-ratio inspirals into rotating boson stars: nonintegrability, chaos, and transient resonances" | Phys. Rev. D **108**:084062, arXiv:2305.05691 | PDF abstract retrieved 2026-05-13; all four authors verified | State-of-art methodology: Poincaré sections, rotation-number curves, transient resonances, and the gravitational-wave-glitch falsifier. Methods-import target for the spike protocol. |
| 6 | **Destounis & Fernandes 2026**, "Environmentally-induced chaos: Extreme-mass-ratio systems of rotating black holes in astrophysical environments" | Phys. Rev. D **113**:044040, arXiv:2508.20191 | PDF abstract retrieved 2026-05-13; verbatim *"loss of a Carter-like constant leads to geodesic non-integrability and the onset of chaos"* | Most recent (2026) explicit statement of Carter-constant loss → chaos in spinning-BH setting. Closest published phrasing of the conjecture. |
| 7 | **Tavlayan & Tekin 2025**, "Instability and Information Production Around Kerr Black Holes" | arXiv:2504.20876 (preprint, v2 Oct 2025) | PDF abstract retrieved 2026-05-13 | EXTERIOR chaos via Lyapunov + Kolmogorov-Sinai entropy of unstable orbits. Methodological comparator (exterior, not interior). |

### 2b. Frequently invoked but **not** directly load-bearing

- **Cardoso, Miranda, Berti, Witek, Zanchin 2008** (arXiv:0812.1806, "Geodesic stability, Lyapunov exponents and quasinormal modes"). User prompt called this "Cardoso-Cavaglià 2008"; correct authors verified. Paper is about the **eikonal exterior** Lyapunov-QNM correspondence, *not* interior chaos. Useful for the Lyapunov-as-QNM-imaginary-part bridge in protocol section 3c, but the "Cavaglià" co-author attribution is wrong.
- **Tang 2020** (arXiv:2008.10050, Chinese Phys. C, "Temporal and spatial chaos in the Kerr-AdS black hole in an extended phase space"). Melnikov method on Kerr-AdS thermodynamic phase space. Tangentially relevant; not interior-spacetime chaos but P-V thermodynamic chaos in the extended phase space.

### 2c. User-prompt references that did NOT verify

- **"Cardoso-Cavaglià 2008 ish"** — closest match is arXiv:0812.1806 (Cardoso-Miranda-Berti-Witek-Zanchin 2008, on eikonal QNM-Lyapunov correspondence). Cavaglià co-authored a 2008 PoS paper with Cardoso on ergoregion instability of BH mimickers, not on interior chaos. **Substitute reference #1 (Bombelli-Calzetta 1992) and reference #7 (Tavlayan-Tekin 2025) for the periodic-perturbation-→-chaos and Lyapunov-of-Kerr-geodesics topics respectively.**
- **"Stanish-Iglesias 2010 Lyapunov-exponent computation in BL coordinates"** — no such paper located. The canonical 2010 reference for non-Kerr Hamiltonian chaos in BL-style coordinates is **Lukes-Gerakopoulos-Apostolatos-Contopoulos 2010** (reference #2 above).
- **"Pretorius-Stein on interior chaos"** — Pretorius is known for numerical-relativity merger simulations; Stein is known for ringdown / scattering. No joint paper on interior chaos located via WebSearch 2026-05-13. **Do not cite this combination.** The closest actual interior-chaos anchor is McMaken 2024 (reference #4).

---

## 3. Spike protocol — concrete first-spike computation

The user prompt offers four candidate observables (Lyapunov, Poincaré section, KAM-breakdown, level-spacing statistics). The protocol below picks the **minimally expensive** test that is also **maximally diagnostic**, with explicit falsifiers. Spike-test-first discipline (per project memory entry on stored-relationship-mechanism spike pattern): we run a small computation that either licenses or refutes the conjecture before committing to a full numerical-relativity programme.

### 3a. Concrete perturbation (one specific choice)

Adopt **mass-quadrupole bumpy perturbation** δg_{ab} parameterised by a single small dimensionless number `ε`, sourcing an anisotropic interior δT_{ab} via linearized Einstein. Following Lukes-Gerakopoulos-Apostolatos-Contopoulos 2010 (arXiv:1003.3120) and the manko-novikov / bumpy-BH family:

- Background: Kerr `(M, a)` in Boyer-Lindquist `(t, r, θ, φ)`.
- Perturbation: add a **mass quadrupole excess** `Q_2 = ε · M^3` not allowed by Kerr (the Kerr quadrupole is fixed at `Q_2^{Kerr} = -Ma²`).
- This is a non-axisymmetric breaking only at higher multipoles; at quadrupole level the perturbation is still axisymmetric but breaks the principal-CKY structure (per F-K-K 2017 review §§5-6: Kerr is the **unique** axisymmetric vacuum metric admitting a non-degenerate principal CKY 2-form; any deformation away from Kerr-NUT-(A)dS family kills the CKY).

**Why this perturbation:** (i) clean published baseline (1003.3120 has explicit Poincaré sections for this family); (ii) one-parameter — easy to scan ε from 0 (Kerr) to ε ~ 0.1 (testably non-Kerr); (iii) maps onto the user's conjecture (the "anisotropic interior forcing" is δT_{ab} with non-Killing-tensor-preserving structure); (iv) one published method already exists to confirm/refute, so we can sanity-check our pipeline against L-G-A-C 2010 results before declaring novelty.

### 3b. Diagnostic observable (one specific choice)

**Poincaré surface-of-section + rotation-number curve** on equatorial-plane bound geodesics, following Destounis-Angeloni-Vaglio-Pani 2023 (arXiv:2305.05691) methodology. Specifically:

1. Pick an energy `E` and angular momentum `L_z` admitting bound orbits in the perturbed background.
2. Generate the Poincaré section `Σ = {θ = π/2, p_θ > 0}` in the `(r, p_r)` plane.
3. For each initial condition, integrate ~10³ orbital periods.
4. Plot the intersections.

**Signature of integrability (Kerr, ε = 0):** Closed invariant curves filling the section (KAM tori, integrable).

**Signature of weak non-integrability (small ε > 0):** Birkhoff chains of islands appearing at low-order resonances `ω_r : ω_θ = p : q`, with thin chaotic layers in between (per L-G-A-C 2010 + Destounis et al. 2023).

**Signature of strong non-integrability (ε beyond some threshold ε*):** Wide-area chaotic scattering, KAM-torus destruction, no surviving invariant curves.

### 3c. Falsifier — what kills the conjecture

The conjecture is "anisotropic interior forcing from spinning boundary produces chaotic bulk regime." Three falsifier classes:

- **Falsifier A (perturbative integrability):** If the perturbed system admits a *generalised* Killing tensor `K(ε) = K^{Kerr} + ε K^{(1)} + O(ε²)` such that `\nabla_{(a} K(ε)_{bc)} = O(ε^n)` with `n ≥ 2`, then geodesic motion is *approximately* integrable to order `ε^{n-1}` and the Poincaré sections show no islands at small ε. **Outcome: conjecture fails at the perturbative level.** This is a known phenomenon for special "Cotton-flat" or "type-D-preserving" perturbations (per F-K-K 2017 §6.3).
- **Falsifier B (boundary insensitivity):** If the chaotic signature depends only on `M` and `ε` (not on the spin parameter `a`), then the chaos is **not** sourced by the spinning boundary — it would emerge equally for a non-rotating Schwarzschild perturbation. The conjecture's load-bearing claim that *the spin* drives the anisotropic forcing would be refuted. (This is the falsifier most likely to distinguish "spinning-boundary-induced" from "generic bumpy" chaos.)
- **Falsifier C (no fourth side):** If the chaotic regime, when characterised by level-spacing statistics of the perturbed angular-eigenvalue spectrum `Λ_{ℓm}(a, ε)`, shows **Poisson** rather than **GOE** statistics, then the spectrum remains "as if integrable" despite the Poincaré signature — and the framework-reach diagram does **not** gain a fourth side, because the *spectral* manifestation of the chaos is absent. (Spike #13 would then have produced a phase-space chaos that has no spectral counterpart, leaving the bounded-framework arc unchanged. Honest-negative outcome.)

**One-sentence spike protocol:** Generate Poincaré sections + rotation-number curves for equatorial bound geodesics in a Kerr + ε·mass-quadrupole bumpy background at ε ∈ {0, 0.01, 0.05, 0.1}, sanity-check against published L-G-A-C 2010 + Destounis et al. 2023 results, and report whether the chaotic signature **(a)** appears, **(b)** depends on the spin `a`, and **(c)** is accompanied by GOE-type level-spacing statistics in the perturbed `Λ_{ℓm}(a, ε)` spectrum.

---

## 4. Honest-negative possibility

The conjecture may **dissolve** under closer inspection. Four ways this could happen:

**(i) Already-computed-for-decades.** The bumpy-BH / non-Kerr / EMRI literature (Manko-Novikov, Brink, Apostolatos, Glampedakis-Babak, Lukes-Gerakopoulos-Apostolatos-Contopoulos, Destounis-Angeloni-Vaglio-Pani, Destounis-Fernandes, and ~20 other groups) has been computing exactly this — Poincaré sections, KAM-breakdown, transient resonances, GW glitch signatures — since the mid-2000s. The result is **established**: any δg breaking the principal-CKY structure produces non-integrable geodesics. The user's conjecture in its weak form is **trivially true and published**.

**(ii) Interior-vs-exterior framing fragility.** Almost all published bumpy-BH / non-Kerr chaos work is on the **exterior** geodesics (where EMRIs live). The user prompt emphasises **interior**. Interior Kerr dynamics are dominated by **Cauchy-horizon mass-inflation** physics — and the published interior result (McMaken 2024) is that *quantum* backreaction sources interior chaos. If the user's "anisotropic interior forcing" maps onto this, then **McMaken 2024 has already published the conjecture** (in slightly different language). Spike #13 would replicate, not extend.

**(iii) "Non-Killing perturbation" is a 60-year-old observation.** The statement "Carter constant fails under generic perturbation → integrability breaks" is **trivially true** by the dimension-counting argument: 4 dof, 4 conserved quantities (Kerr) → integrable; lose one → generically non-integrable (Liouville-Arnold). The non-trivial science is in *which* perturbations preserve a generalised Killing tensor (the Falsifier-A class) — and there is **published work on this** (Geroch 1970; F-K-K 2017 §6.3). Spike #13's contribution-to-knowledge would have to be in the *specific* spin-induced anisotropic-forcing class, which requires the conjecture to be sharpened past "non-Killing perturbation breaks integrability."

**(iv) The "fourth side" framing may be over-claimed.** Spikes #11 + #12A established that the *spectral-algebra Casimir-decomposition framework* is bounded by KY-abelian (Spike #11) and contraction-non-existence (Spike #12A). Adding "anisotropic interior chaos" as a fourth side conflates *spectral algebra* (the actual framework arc) with *phase-space dynamics* (Hamiltonian non-integrability). These are different mathematical objects. A positive Spike #13 result would be a *phase-space* finding, not a *spectral-algebra* finding. The framework-reach diagram would gain a fourth side only if (Falsifier C above) the chaos has a level-statistics signature in the QNM spectrum. Otherwise, Spike #13 produces a parallel-but-orthogonal finding, not a contiguous fourth boundary.

**Verdict on honest-negative possibility:** The conjecture in its weakest form (any non-Killing perturbation breaks integrability) is **published and trivial**. The conjecture's *novel content* — that *spin-induced anisotropic interior forcing* produces a chaos signature *distinguishable from generic bumpy-BH chaos* and *manifest in the spectral algebra (not just phase space)* — is **plausible but unconfirmed**. Spike #13 is worth running **only if** the protocol includes Falsifier B (spin-dependence) and Falsifier C (level-statistics), because those are the two pieces that aren't already published.

---

## 5. Connection to the bounded-framework arc

The framework-reach diagram established by Spikes #9–#12A has three sides:

| Side | Established by | Result |
|---|---|---|
| Low-`Mω` regime (CMS hidden conformal) | Spike #9, Spike #10 | `C_L + C_R = 2 λ_S²(ℓ, s) + 4 s²` closed-form |
| Generic-`Mω` regime via KY tower | Spike #11 | **KY algebra is abelian — no Casimir compression possible** |
| Interpolation regime KY ⊕ photon-ring | Spike #12A | **No contraction structure exists — three independent obstructions** |

**Could Spike #13 open a fourth side?**

The fourth side would have to be a *different mathematical question*, not a deeper attempt at the same one. The three sides above are all about **closed-form spectral identities** for Kerr QNMs. Spike #13 asks about **chaotic vs integrable dynamics** under perturbation — which is a *different* observable (phase-space measure or level-spacing statistics rather than eigenvalue identity).

Two possible framings:

**Framing P (positive opens fourth side):** If Falsifier C is *not* triggered (i.e., the perturbed spectrum *does* show GOE level statistics), then the framework-reach diagram gains a fourth boundary: *spectral algebra closes Kerr QNMs in the integrable regime (sides 1–3) but transitions to random-matrix universality (GOE) at the spinning-boundary-induced chaos threshold*. This would be a **clean** result connecting the algebraic-spectral framework to quantum-chaos universality. **Publishable as physics.** Maps onto well-established BH/random-matrix correspondence (Cotler-Penington-Saad-Shenker / Maldacena-Stanford SYK / spectral form factor literature).

**Framing N (negative does not open fourth side):** If Falsifier C *is* triggered (Poisson statistics survive despite phase-space chaos), or if Falsifier A triggers (perturbative integrability re-emerges), then Spike #13 produces a phase-space-only finding orthogonal to the spectral-algebra arc. Honest negative.

**No-lineage discipline note:** Framing P would be a *technical claim* about the perturbed Kerr spectrum's statistics. It would **not** be a claim that the framework "extends naturally to chaos," nor that the spectral-algebra arc *predicted* the chaos. Just: side 1–3 say where closed-form Casimir works; side 4 (if it exists) says where it transitions to random-matrix universality. These are coordinated technical findings, not a unified theory.

---

## 6. Recommendation

The spike protocol in §3 is **spike-worthy** under the following conditions, ordered by decreasing rigor:

1. **Spike-worthy if Falsifier B + Falsifier C are both included.** The novel content (vs published bumpy-BH literature) is exactly the spin-dependence test (B) and the level-statistics test (C). Without both, Spike #13 replicates known work.
2. **Lower-value if only Falsifier A is tested** — that is a verification exercise against L-G-A-C 2010 + Destounis 2023.
3. **Honest-negative-only if neither novel test is included** — the literature already says non-Killing perturbations of Kerr → non-integrable geodesics.

Recommended pre-spike action: **dual-agent counterpoint scan** (per project memory entry on dual-agent research pattern) on the specific question *"Is there a published result computing level-spacing statistics (GOE vs Poisson) of the angular-separation-constant spectrum `Λ_{ℓm}(a)` for bumpy-BH / non-Kerr backgrounds?"* If yes, Spike #13's novel content shrinks; if no, the test is publishable.

**Decision deferred to user.** This document scopes; it does not pre-commit.

---

## 7. Files in this scope-only commit

- `docs/srmech/notes/spike_13_candidate_anisotropic_interior_chaos_scope_2026-05-13.md` (this file)

No NDJSON / no script / no plot — this is scoping, not computation. Per project preference (`memory/feedback_ndjson_over_bloated_json.md`), if the spike is approved and runs, the result-style outputs will be NDJSON.
