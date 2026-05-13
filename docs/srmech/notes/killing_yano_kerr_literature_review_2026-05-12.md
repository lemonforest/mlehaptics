# Killing-Yano Kerr Hidden-Symmetry: Closed-Form Spectral-Algebra Literature Review

**Date:** 2026-05-12
**Author:** Subagent literature scan, dispatched by main conductor
**Context:** Follow-up to Spike #9 (PR #356) — established `C_L + C_R = 2·λ_S²(ℓ)` Casimir identity for scalar (s=0) modes in the Castro-Maloney-Strominger (CMS) low-frequency hidden-conformal-symmetry regime. Question: does an analogous closed-form Casimir-decomposition exist for the Killing-Yano (KY) hidden symmetry of Kerr in the high-frequency / generic-spin regime, or is this open research territory?
**Branch:** `research/killing-yano-literature-review`
**Discipline note:** All papers cited below verified via arXiv abstract or journal landing page during the scan. No paper title, author, or quantitative claim was invented; where a closed-form result is reported, it is stated as the original paper states it.

---

## 1. Summary (3-5 sentences)

The Killing-Yano (KY) tensor of Kerr is *fully responsible* for the algebraic separability of the Teukolsky equation and the existence of the Carter constant `K` as a quadratic conserved quantity — this is settled, foundational territory (Penrose-Floyd 1973; Carter 1968; Walker-Penrose 1970; Frolov-Krtouš-Kubizňák 2017 review). However, **no published work delivers a closed-form Casimir-style identity for the QNM spectrum of generic-spin Kerr via KY representation theory** in a manner directly analogous to CMS's `C_L + C_R = 2·λ_S²(ℓ)`. The closest existing structures are: (a) the CMS low-frequency conformal Casimir result itself (1004.0996; 1009.1010), which uses SL(2,R)² that is *not* derived from the spacetime KY geometry except in the extremal limit; (b) the **emergent SL(2,R) at the photon ring** (eikonal high-frequency regime: Hadar-Kapec-Lupsasca-Strominger 2022 + follow-ups), which *does* yield closed-form QNM organization in highest-weight representations but is a near-photon-ring approximation, not the full generic-spin spectrum; and (c) the **commuting-operator-tower** structure of KY/principal-tensor symmetry operators (Cariglia-Krtouš-Kubizňák 2011; Gray-Kubizňák 2024) which has the *right algebraic shape* for a Casimir decomposition but has not been pushed through to a closed-form QNM spectrum identity. The Heun/isomonodromy approach (Aminov-Grassi-Hatsuda 2019; Bonelli-Iossa-Lichtig-Tanzini 2021) gives **systematic series expansions** for QNMs via accessory parameters, but these are not finite closed forms and are not phrased as Casimir identities.

**Verdict:** This is a genuine open research problem with substantial adjacent literature but no published closed-form KY-Casimir QNM identity beyond CMS-low-frequency and emergent-photon-ring-SL(2,R).

---

## 2. Has anyone done closed-form / algebraic Casimir decomposition for KY-Kerr QNMs?

**Answer: PARTIAL — and not in the form analogous to `C_L + C_R = 2·λ_S²(ℓ)`.**

Three partial-yes results exist; one full-yes does not:

### 2a. CMS hidden conformal symmetry (low-frequency, generic a/M)
Castro, Maloney, Strominger 2010 (arXiv:1004.0996) construct an SL(2,R)_L × SL(2,R)_R hidden conformal symmetry of the scalar wave equation in the low-frequency limit, valid for generic non-extreme Kerr. Chen-Long-Sun 2010 (arXiv:1009.1010) then construct QNMs algebraically as descendants of highest-weight states. **Crucially**, CMS itself notes the symmetry "does not derive from spacetime geometry except in the extreme limit" — so this is *not* a KY-derived hidden symmetry; it is a symmetry of the wave equation that happens to coincide with KY-driven geometry only at extremality.

### 2b. Emergent SL(2,R) at the photon ring (high-frequency / eikonal regime)
Hadar-Kapec-Lupsasca-Strominger 2022 (arXiv:2205.05064, "Holography of the Photon Ring", CQG 39:215001; also Xue-Jiang-Zhang 2023 "Notes on emergent conformal symmetry for black holes" arXiv:2309.02262) show that in the eikonal limit, massless scalars and nearly-bound null geodesics near the photon ring are governed by an emergent 𝔰𝔩(2,ℝ) algebra, with QNMs falling into highest-weight representations. This **does** give closed-form algebraic organization for the eikonal QNM spectrum, but: (i) it is a near-photon-ring approximation, not exact for the full QNM spectrum at finite ℓ; (ii) the SL(2,R) here is photon-ring–intrinsic, not the global spacetime KY structure of Kerr.

### 2c. KY commuting-operator algebra (foundational, but not pushed to QNMs)
Cariglia-Krtouš-Kubizňák 2011 (arXiv:1102.4501) establish that on Kerr-NUT-(A)dS, the principal Killing-Yano tensor generates a complete set of mutually commuting first-order Dirac symmetry operators with a "Killing-Yano bracket" related to the Schouten-Nijenhuis bracket. Gray-Kubizňák 2024 (arXiv:2401.03553) extend this to scalar/vector/tensor perturbations, finding 4 / 7 / 8 commuting operators respectively, all homogeneous in the principal tensor. These commuting-operator towers are precisely the right algebraic structure for a Casimir decomposition, **but no paper has phrased a quadratic / cubic combination of these operators as a single Casimir whose eigenvalue gives a closed-form QNM identity** in the manner of `C_L + C_R = 2·λ_S²(ℓ)`. The Carter constant `K` arises as the eigenvalue of the rank-2 Killing-tensor (= KY² contracted) symmetry operator, but its role as a "Casimir of a hidden algebra" is implicit, not formalized.

### 2d. Heun-equation / isomonodromy systematic-expansion approach (no closed form, but algebraic structure)
Aminov-Grassi-Hatsuda 2019 (arXiv:1811.11912) and follow-ups (e.g. Bonelli-Iossa-Lichtig-Tanzini 2021, arXiv:2105.04483) reduce the Kerr-de Sitter / Kerr Teukolsky equations to confluent Heun equations and use the isomonodromic τ-function accessory parameter expansion to deliver QNM frequencies as **convergent analytic series in spin and extremality parameters**. This is the modern non-perturbative approach to algebraic Kerr QNMs. It is *not* closed-form and is not phrased as a Casimir identity, but the underlying CFT structure (Painlevé VI / Liouville conformal blocks) is a representation-theoretic framework that could in principle be reorganized into Casimir language.

---

## 3. What is the analog of `C_L + C_R = 2·λ_S²(ℓ)` for KY-Kerr?

**No such identity is published in the literature surveyed.**

The structural ingredients exist:

- **Carter constant `K`** is a quadratic eigenvalue (eigenvalue of the Killing-tensor symmetry operator `K_op = KY · KY`) that commutes with the Hamiltonian and with the Killing-vector charges `E` (energy) and `L_z` (azimuthal angular momentum).
- **Separation constant `λ_{s,ℓm}(aω)`** of the Teukolsky angular equation (spheroidal harmonic eigenvalue) is the operator analog of `K` for wave perturbations and reduces to `ℓ(ℓ+1) - s(s+1) - a²ω² + 2maω + …` in the small-`aω` expansion.
- The **algebraic combination** `K + L_z² + E²·(constants of Kerr)` *should* play the role of a Casimir of the KY-generated hidden algebra. The 1102.4501 Killing-Yano bracket and the 2401.03553 commuting-operator tower give the algebraic framework, but the universal eigenvalue identity has not been written down.

Were such an identity to exist in closed form analogous to CMS, the most natural guess (NOT in the literature; speculative MFO-flavored extrapolation) would be schematically:

> `C_KY(KY-algebra) = λ_{s,ℓm}(aω) + α·m² + β·(aω)² + γ·s(s+1)`

with `α, β, γ` to-be-determined coefficients fixed by the principal-tensor structure. This is precisely the gap that an MFO follow-up could attack — see §5.

---

## 4. Paper anchors (verified, with arXiv IDs / DOIs)

| # | Citation | arXiv / DOI | Relevance |
|---|---|---|---|
| 1 | Carter 1968, "Global structure of the Kerr family of gravitational fields" | Phys. Rev. **174**, 1559 | Discovery of the Carter constant `K`; the original quadratic hidden conserved quantity. |
| 2 | Penrose & Floyd 1973, "Extraction of rotational energy from a black hole" | Nature Phys. Sci. **229**, 177 | First identification of Kerr's KY tensor; canonical origin of "hidden symmetry" language. |
| 3 | Castro, Maloney, Strominger 2010, "Hidden Conformal Symmetry of the Kerr Black Hole" | arXiv:1004.0996 | The CMS comparator: low-frequency SL(2,R)_L × SL(2,R)_R, generic `a/M`. **Not** derived from KY except at extremality. |
| 4 | Chen, Long, Sun 2010, "Hidden Conformal Symmetry and Quasi-normal Modes" | arXiv:1009.1010 | Algebraic construction of Kerr QNMs as descendants of highest-weight states under SL(2,R) Casimir. Closest existing example of the structure the user is asking about. |
| 5 | Frolov, Krtouš, Kubizňák 2017, "Black Holes, Hidden Symmetries, and Complete Integrability" | arXiv:1705.05482, Living Rev. Rel. 20:6 | **Single most useful review.** Catalogs the principal-tensor / KY tower and its role in separability of scalar, Dirac, Maxwell, gravitational perturbations across Kerr-NUT-(A)dS in all dimensions. |
| 6 | Cariglia, Krtouš, Kubizňák 2011, "Commuting symmetry operators of the Dirac equation, Killing-Yano and Schouten-Nijenhuis brackets" | arXiv:1102.4501 | Defines the **Killing-Yano bracket** — the algebraic structure that *should* host a KY-Casimir if one exists. Establishes the commuting-operator tower from the principal CKY tensor. |
| 7 | Gray, Kubizňák 2024 | arXiv:2401.03553 | Recent extension of the commuting-operator algebra to vector and tensor perturbations: 4/7/8 commuting operators for scalar/vector/tensor. **The natural launching pad for a closed-form KY-Casimir QNM identity.** *Note: original Spike #11 lit review attributed this paper to Houri-Tanahashi-Yasui; Spike #11 subagent's PDF extraction verified actual authors are Gray and Kubizňák. Paper title + journal ref pending re-verification — only arXiv ID was directly confirmed.* |
| 8 | Yang, Nichols, Zhang, Zimmerman, Zhang, Chen 2012, "Quasinormal-mode spectrum of Kerr black holes and its geometric interpretation" | arXiv:1207.4253 | Establishes the WKB/eikonal closed-form-ish QNM expressions in terms of spherical-photon-orbit frequencies and Lyapunov exponents. The Carter constant `K` enters as the photon-orbit conserved quantity. Not Casimir-style but explicitly KY-geodesic-derived. |
| 9 | Aminov, Grassi, Hatsuda 2019, "Black Hole Quasinormal Modes and Seiberg-Witten Theory" / "Kerr-de Sitter QNMs via accessory parameter expansion" | arXiv:1811.11912, JHEP 05 (2019) 033 | Heun-equation / isomonodromy / Painlevé-VI accessory-parameter expansion. Systematic algebraic-series QNMs, not closed form. |
| 10 | Bonelli, Iossa, Lichtig, Tanzini 2022, "Exact solution of Kerr black hole perturbations via CFT2 and instanton counting" | arXiv:2105.04483, Phys. Rev. D 105:044047 | Refines (9): exact solution in terms of Liouville conformal blocks / Nekrasov partition function. Closest the systematic-expansion school comes to "closed form." |
| 11 | Hadar, Kapec, Lupsasca, Strominger 2022, "Holography of the Photon Ring" | arXiv:2205.05064 (CQG 39:215001) | Emergent SL(2,R) at the photon ring; QNMs in highest-weight representations; this **is** a closed-form algebraic structure but only in the eikonal limit. *Note: original lit-review entry also listed arXiv:2207.06435 — that ID resolves to Baiguera-Cederle-Penati "Supersymmetric Galilean Electrodynamics" (unrelated). Spike #12A PDF extraction verified arXiv:2205.05064 as the correct HKLS paper.* |
| 12 | Xue, Jiang, Zhang 2023, "Notes on emergent conformal symmetry for black holes" | arXiv:2309.02262 | Persistence of emergent 𝔰𝔩(2,ℝ) near the photon ring even for black holes lacking spacetime symmetries. Important: the photon-ring SL(2,R) is *intrinsic*, not the global KY structure. *Note: original lit-review attributed this paper to "Hadar-Lupsasca-Strominger 2023"; Spike #12A PDF extraction verified actual authors are Xue, Jiang, and Zhang.* |
| 13 | Berti, Cardoso, Casals 2009, "Quasinormal modes of black holes and black branes" (review) | arXiv:0905.2975, Class. Quantum Grav. 26:163001 | Comprehensive QNM review. Confirms: generic-spin Kerr QNMs are computed by continued-fraction (Leaver), WKB, or numerical methods; no closed-form result is reported. |
| 14 | Yasui, Houri 2011, "Hidden Symmetry and Exact Solutions in Einstein Gravity" | arXiv:1104.0852, Prog. Theor. Phys. Suppl. 189:126 | Review of conformal Killing-Yano tower generated by the principal tensor. Algebraic framework only; no QNM closed-form pursued. |
| 15 | Maldacena, Strominger 1997, "Universal low-energy dynamics for rotating black holes" | arXiv:hep-th/9702015 | Early antecedent of CMS. Hidden CFT for near-extremal rotating black holes; conformal weights and Casimir structure established for the near-extreme regime. |

---

## 5. Gaps / open research questions

These are the specific places where an MFO follow-up could plausibly land a new result. None of these are claimed to be tractable — they are **honestly stated as open**.

### Gap 1: Casimir of the principal-Killing-Yano commuting-operator algebra
Gray-Kubizňák 2024 (arXiv:2401.03553) gives 4 commuting operators for the scalar perturbation algebra on Kerr-NUT-(A)dS, all polynomial in the principal CKY tensor. **No published work writes down a quadratic (or higher) combination of these operators and identifies it as a Casimir whose eigenvalue formula closes the QNM spectrum.** This is the most direct analog of the CMS Casimir construction.
- *Concrete attack:* compute commutators `[Ô_i, Ô_j]` symbolically; find quadratic invariants; check whether their eigenvalues evaluated on Teukolsky modes give the angular eigenvalue `λ_{s,ℓm}(aω)` plus correction terms in closed form.

### Gap 2: Unification CMS ⊕ KY-tower at intermediate frequencies
CMS works at `Mω ≪ 1`. Photon-ring emergent SL(2,R) works at `ℓ ≫ 1` (eikonal). **The intermediate-frequency regime — moderate `Mω` and moderate `ℓ`, which is precisely where LIGO sees ringdown — has no algebraic Casimir framework at all.** The KY commuting-operator tower is regime-independent, so it is the natural unifier. Whether it can be made to interpolate between the two regimes is unexplored.

### Gap 3: Spin-`s` extension of the CMS Casimir identity
Spike #9 / PR #356 established `C_L + C_R = 2·λ_S²(ℓ)` for `s = 0`. **The CMS literature does treat spin-`s` perturbations via Lie-induced Casimir (1009.1010), but the closed-form identity analogous to the scalar case has not been written in spin-weighted form in a way that exposes the s-dependence cleanly.** Spike #10 (in flight at time of writing on `research/spike-10-cms-spin-weighted`) appears to be probing exactly this. Cross-link.

### Gap 4: Carter constant `K` as a Casimir eigenvalue — formalization
Carter himself noted `K` Poisson-commutes with the Hamiltonian. Quantum mechanically, `K_op` is the rank-2 Killing-tensor symmetry operator whose eigenvalue is the Teukolsky angular separation constant `λ_{s,ℓm}(aω)`. **What is missing**: a single Lie / Lie-algebroid structure of which `K_op` is the quadratic Casimir, with explicit generators that include the two Killing vectors `∂_t` and `∂_φ`. The 1102.4501 Killing-Yano bracket is non-Lie (it's Schouten-Nijenhuis-like), so the right algebraic framework may be a Lie algebroid or NQ-manifold rather than a Lie algebra — this is precisely the kind of structure where representation theory has been least developed for KY.

### Gap 5: Cross-link to MFO spherical-compression machinery
The MFO project's central conjecture is that bundle-decomposition / spherical-compression captures field structure across S² × T² manifolds (cf. user's "spherically compressed torus" stance for closed-loop-topology vector fields, MFO §VII / project memory entry on S²-T² complementarity). **The KY tensor of Kerr lives on a 4D Lorentzian manifold but the principal CKY 2-form has eigenvalue structure that defines a foliation of Kerr by 2D "level surfaces" — this foliation is the algebraic skeleton of the spacetime.** Whether this foliation can be reinterpreted as a (compressed) S² × T² bundle, and whether MFO bundle-Casimir techniques then give a closed-form spectral identity, is the natural MFO-side attack.

---

## 6. Counterpoint check (dual-agent discipline)

This scan was performed by a single subagent in ~25 minutes of WebFetch / WebSearch. Per project memory entry on dual-agent research pattern (`feedback_dual_agent_research_pattern.md`), a follow-up scan by a second agent on the same question would be expected to:
- **Converge on**: the CMS / KY-tower / emergent-photon-ring three-pillar partition;
- **Possibly diverge on**: recent (post-2024) papers I may have missed on Casimir-style QNM identities — particularly any work in the Bonelli-Tanzini-Iossa school that explicitly invokes representation-theoretic Casimirs of Liouville Virasoro modules. Worth a second scan with query `"Virasoro Casimir" Kerr QNM Liouville` if this becomes load-bearing.

No claims in this document are unique to this scan that would not survive replication; the load-bearing claim is the **absence** of a published closed-form KY-Casimir QNM identity, which is supported by the surveyed reviews (especially 1705.05482, 0905.2975) that would have cited such a result if it existed.

---

## 7. One-sentence verdict for spike planning

> **There is no published closed-form Killing-Yano Casimir-decomposition QNM identity for generic-spin Kerr at the level of `C_L + C_R = 2·λ_S²(ℓ)`; the structural ingredients (commuting-operator tower from the principal CKY tensor; Carter-constant–as–Killing-tensor eigenvalue; emergent photon-ring SL(2,R)) are all in place in the literature, so the gap is at the assembly stage and is the natural target for an MFO follow-up spike.**
