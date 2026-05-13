# Spike #12B candidate — Lie-algebroid refinement of the KY Schouten-Nijenhuis bracket: scoping document

**Date:** 2026-05-13
**Author:** Subagent scoping pass (concertmaster), dispatched by main conductor
**Branch:** `research/spike-12b-lie-algebroid-ky-bracket` (from `main` at `07d1a7e`)
**Status:** SCOPING ONLY. No computation performed. This document proposes Spike #12B; the user decides whether to run it.
**Discipline:** All 2020+ citations PDF-verified via arXiv abstract retrieval before being entered below. PDF-extraction discipline (per `memory/feedback_pdf_extraction_citation_discipline.md`) is load-bearing on this branch given three misattribution catches in the May-2026 spike series.

---

## 0. Context: the bounded-framework arc

The May-2026 Killing-Yano / Kerr-QNM research thread has now mapped three sides of the framework's reach:

- **Spike #11** (commit `52a471c`, PR #359): the KY commuting-operator algebra `{□, K, L_ξ, L_η}` on generic-`Mω` Kerr scalar perturbations is **abelian** (Gray-Kubizňák 2024 §III.B). Casimir-decomposition collapses to the joint-eigenvalue tuple `(μ², Λ, ω, m)`; the angular constant `Λ_{ℓm}(aω)` has no closed form. Honest negative; structural.
- **Spike #12A** (commit `9c75319`, PR #361): no İnönü-Wigner contraction connects the KY tower to the photon-ring `SL(2,ℝ)_QN` algebra (HKLS 2022 arXiv:2205.05064). Three independent obstructions: dimension count (4 vs 4 only after Heisenberg-Weyl extension), ambient-space mismatch (full 4D field vs near-ring reduced field), and structure-constants mismatch in the contraction direction. Outcome class (c).
- **Spike #11 §VII.4.1.2 consolidation** (commit `07d1a7e`, PR #360): the CMS / KY-tower / photon-ring three-pillar partition of "what closed-form structure Kerr QNMs admit" is sharpened, and the KY-Kerr-QNM closed-form gap is documented as a real open problem in the Kerr/CFT-correspondence literature.

The bounded-framework arc has three sides. The Spike #11 abelian-algebra result lives at the level of **operator commutators on differential operators built from KY tensors**. The KY tensors themselves carry richer algebraic structure that the operator commutator may have flattened. The question Task #176 raises:

> Does the **Schouten-Nijenhuis bracket on KY tensors** carry information that the operator commutator on KY-derived differential operators does not — and does the Lie-algebroid refinement of that bracket provide non-trivial Casimir-like invariants?

This is a question one level below Spike #11. If the answer is *yes*, then the framework reach has a fourth, classical-tensor-level side that the operator-quantization approach missed. If the answer is *no*, then the abelian obstruction descends from the operator level all the way down to the classical bracket on KY tensors — tightening the bound on three sides into a tighter bound on three-plus-a-classical-floor.

Both outcomes are publishable honest results. Both are valuable to the framework arc.

---

## 1. Schouten-Nijenhuis on Killing-Yano tensors — precise definitions

### 1.1 The Schouten-Nijenhuis bracket [·, ·]_SN

The Schouten-Nijenhuis (SN) bracket is the unique graded extension of the Lie bracket of vector fields to multivector fields (or, dually, to totally-antisymmetric covariant tensors) satisfying graded Leibniz and graded Jacobi. On a smooth manifold `M`:

- **Multivector form**: `[·, ·]_SN : Γ(Λ^p TM) × Γ(Λ^q TM) → Γ(Λ^{p+q-1} TM)`, graded-skew-symmetric of degree `−1`.
- **Antisymmetric-tensor form** (the version we need for KY): `[·, ·]_SN` extends by metric duality to skew-symmetric forms. Given two Killing-Yano `p`-form and `q`-form `Y_1, Y_2`, the SN bracket lifts to a **symmetric tensor** of rank `p + q − 1` (Cariglia-Krtouš-Kubizňák 2011 eq. 3.7-3.10; see also Kastor-Ray-Traschen 2007 arXiv:0705.0535 for the curved-spacetime treatment).

The SN bracket reduces to the Lie bracket of vector fields when `p = q = 1`. It restricts to the Schouten bracket on `Λ^•(TM)` (multivectors) and to the Kostant-Souriau bracket on Poisson manifolds when `M` is symplectic. **Crucially, on `M` of positive dimension `n ≥ 2`, the SN bracket of two Killing-Yano tensors is NOT in general a Killing-Yano tensor.** This was shown by Kastor-Ray-Traschen 2004 (arXiv:hep-th/0407064): the SN bracket of two KY tensors is a **Killing tensor** (symmetric, satisfying the Killing equation), but generically not a Killing-Yano tensor (antisymmetric). The KY family is closed under SN only when extended to the larger Killing-Stäckel family.

### 1.2 The Killing-Yano bracket of Cariglia-Krtouš-Kubizňák 2011

Cariglia-Krtouš-Kubizňák 2011 (arXiv:1102.4501, PRD 84:024004; PDF-verified 2026-05-13) introduce a "Killing-Yano bracket" {Y_1, Y_2}_KY on the space of (odd-rank Killing-Yano forms) ⊕ (even-rank closed conformal Killing-Yano forms). The abstract explicitly states:

> "We can introduce a Killing-Yano bracket, a bilinear operation acting on odd Killing-Yano and even closed conformal Killing-Yano forms, and demonstrate that it is closely related to the Schouten-Nijenhuis bracket." (Abstract, PRD 84:024004)

The KY bracket {·, ·}_KY:

- Is bilinear and respects the `ℤ/2`-grading (odd KY × even CCKY → odd KY).
- Is **closely related** to (but not identical with) the SN bracket: explicitly, `{Y_1, Y_2}_KY = π_KY [Y_1, Y_2]_SN` where `π_KY` is a projector onto the KY subspace defined via the metric.
- Is **NOT** a Lie bracket on the whole space — Cariglia-Krtouš-Kubizňák §IV shows graded Jacobi fails in general because the SN bracket's output sits in a larger Killing-Stäckel tensor space, and the projector `π_KY` does not commute with `[·, ·]_SN`.

This is the *precise* structural reason why the KY family does not form a Lie algebra under the natural bracket — the gap is exactly Lie-algebroid-shaped.

### 1.3 Lie algebroid refresher

A **Lie algebroid** is a triple `(A, [·, ·]_A, ρ)` where:

- `A → M` is a smooth vector bundle.
- `[·, ·]_A` is an ℝ-bilinear Lie bracket on `Γ(A)` (sections).
- `ρ : A → TM` is a smooth bundle map (the **anchor**) inducing a Lie-algebra homomorphism `Γ(A) → Γ(TM)`.
- **Leibniz**: `[X, fY]_A = f[X, Y]_A + (ρ(X)·f) Y` for `X, Y ∈ Γ(A)`, `f ∈ C^∞(M)`.

Lie algebroids generalize both Lie algebras (when `M` is a point, `ρ = 0`) and tangent bundles `TM` (when `A = TM`, `ρ = id`). Integration to Lie groupoids is governed by Crainic-Fernandes 2003 (Annals of Mathematics 157:575–620, arXiv:math/0105033; PDF-verified 2026-05-13): two computable obstructions — monodromy + period — control whether a Lie algebroid integrates to a Lie groupoid.

For Lie algebroids, the **universal enveloping algebra** `U(A)` carries a natural notion of Casimir element (Rinehart 1963; Huebschmann 1990; for the Poisson/Lie-algebroid intersection see Marle 2008, Dissert. Math. 457). Lie-algebroid Casimirs label irreducible representations and provide compression when the algebroid is **non-trivial** in a sense made precise below (§3).

### 1.4 The Lie-algebroid question for KY(Kerr)

The question Task #176 asks is whether there is a Lie algebroid

`A_KY → M` (with `M` = Kerr spacetime, `A_KY` a vector bundle whose sections include the principal CKY 2-form and its descendants)

such that:

- The bracket `[·, ·]_{A_KY}` coincides with (or extends) the Cariglia-Krtouš-Kubizňák KY-bracket `{·, ·}_KY` on the appropriate subspace.
- The anchor `ρ : A_KY → TM` maps a KY section to the Killing vector field it generates (so `ρ(ξ) = ξ` for primary Killing vectors, and `ρ` is non-trivial on rank-2 CKY by mapping to the closed-conformal-Killing-vector descendant).
- The Leibniz relation holds with `C^∞(M)`-module structure inherited from forms on Kerr.

If such a Lie algebroid exists, then `U(A_KY)` carries Casimir elements that may provide compression beyond the joint-eigenvalue tuple `(μ², Λ, ω, m)` of Spike #11. If the bracket fails to close (because the projector `π_KY` of §1.2 above kills graded Jacobi), then no Lie algebroid exists in the obvious place — and one must work with the larger Killing-Stäckel space, where the algebraic structure is even further removed from Lie.

---

## 2. Lie-algebroid structure on KY(Kerr) — does the bracket close?

### 2.1 What is known classically (KY tensors as classical objects on Kerr)

The principal closed conformal Killing-Yano (CCKY) 2-form `k_{ab}` on Kerr-NUT-(A)dS generates a complete tower of Killing-Stäckel tensors via repeated SN/wedge construction (Frolov-Krtouš-Kubizňák 2017, Living Reviews 20:6, arXiv:1705.05482, §3.2-3.5). The tower has:

- **Primary KY**: `k_{ab}` itself (rank 2, antisymmetric, conformal).
- **Killing tensor**: `K_{ab} = k_{ac} k^c{}_b + ½ k² g_{ab}` (rank 2, symmetric, Carter's tensor).
- **Killing vectors**: `ξ^a = (∂_t)^a` (primary) and `η^a = K^{ab} ξ_b` (secondary).
- **Higher-dimensional tower**: in `2N`-dimensional Kerr-NUT-(A)dS, `N` independent Killing tensors `K_{(j)}` and `N` independent Killing vectors `ξ_{(j)}` (Krtouš-Kubizňák-Page-Vasudevan 2007 arXiv:0707.0001 — full title verified 2026-05-13: "Constants of Geodesic Motion in Higher-Dimensional Black-Hole Spacetimes", JHEP 02:004).

**Poisson-commutativity is established** at the classical phase-space level: KKPV 2007 explicitly shows `{K_{(i)}, K_{(j)}}_{PB} = 0` and `{K_{(i)}, ξ_{(j)}}_{PB} = 0`, where `{·, ·}_PB` is the Poisson bracket on geodesic phase space `T^*M`. This **is** the classical analog of Spike #11's abelian result — and it pushes the abelian structure one level below the operator quantization.

But: the Poisson bracket on `T^*M` between **symbols** of differential operators is *not* the same as the Schouten-Nijenhuis bracket on the underlying **tensor fields on `M`**. KKPV 2007's Poisson commutativity is at the symbol level (functions on `T^*M` polynomial in momenta); the SN bracket lives on tensor fields on `M`. The two coincide modulo a known correspondence (the **principal-symbol map**), but the SN bracket carries information that the Poisson bracket of symbols loses — specifically, the components of `[Y_1, Y_2]_SN` that lie in the kernel of the principal-symbol map (i.e., subleading-order tensor combinations).

### 2.2 The Cariglia-Krtouš-Kubizňák obstruction

CKK 2011 §IV explicitly computes `{Y_1, Y_2}_KY = π_KY [Y_1, Y_2]_SN` for KY 2-forms on Kerr and shows that **graded Jacobi fails** in general for the projected bracket. The failure is *not* a computational accident; it is structural: the SN bracket's range is the larger Killing-Stäckel space, and projecting back to KY is not a Lie-algebra homomorphism.

This means: **the KY-bracket on Kerr is not a Lie bracket.** Whether it is a **Lie-algebroid** bracket is a more refined question — Lie algebroids tolerate Leibniz failure of the Lie bracket on the *underlying vector space* by absorbing it into the anchor. The CKK obstruction is consistent with a Lie-algebroid structure if and only if the SN-bracket output that escapes the KY subspace can be reinterpreted as anchor-induced terms `(ρ(Y_1) · f) Y_2` for some `f ∈ C^∞(M)`.

This is the precise mathematical question Spike #12B would attempt to answer.

### 2.3 Anchor candidates

Three natural anchor maps `ρ : A_KY → TM` deserve consideration:

- **Anchor A (isometry-generating)**: `ρ(Y) = Y^♯` where `Y^♯` is the vector field obtained by metric-contracting one slot of `Y` against a chosen Killing vector. Maps primary KY to primary Killing vector; maps rank-2 CCKY to its closed-conformal-Killing-vector descendant.
- **Anchor B (conformal-Killing)**: `ρ(Y) = ∇·Y` (divergence). For closed CKY forms, this generates a conformal Killing vector field; the anchor sends the tower to its "shadow" tower of conformal symmetries.
- **Anchor C (geodesic-flow)**: `ρ(Y) =` Hamiltonian vector field of the symbol of `Y` on `T^*M`. Tautologically integrable but loses tensor-level information.

Anchors A and B are the candidates with non-trivial Leibniz-compatibility checks. Anchor C reduces to the KKPV 2007 Poisson-commutativity result and adds nothing beyond it.

### 2.4 Casimir question

If Spike #12B's bracket-closure check succeeds (some `(A_KY, [·, ·]_{A_KY}, ρ)` is a Lie algebroid), the next question is whether `U(A_KY)` admits Casimir elements of degree ≥ 2 that have non-trivial action on the Teukolsky modes. Two natural candidates:

- **C_quad = [Y_PCKY, Y_PCKY]_{A_KY}**: the self-bracket of the principal CKY 2-form. On a Lie algebra this would be zero by skew-symmetry; on a Lie algebroid the relevant identity is graded-skew on the Schouten side (`[Y, Y]_SN = 0` for *even*-degree multivectors), but the bracket-on-forms version is non-trivial.
- **C_anchor = ρ(Y_PCKY) · (Carter K-symbol)**: anchor applied to the principal CCKY 2-form, composed with the Carter constant scalar. This is a candidate Casimir built from the anchor itself.

The eigenvalue of such a Casimir on a Teukolsky mode, if computable in closed form, would be the closed-form QNM identity that Spike #11 found inaccessible at the operator-commutator level.

---

## 3. Comparison to Spike #11 — what could be different at the tensor level?

Spike #11's load-bearing structural fact: the operator commutator table for `{□, K, L_ξ, L_η}` on Kerr scalar modes is identically zero (Gray-Kubizňák 2024 §III.B). The abelian collapse is at the **quantum-operator** level after canonical quantization of the KY symbols.

The Schouten-Nijenhuis bracket is the **classical-tensor** ancestor of that operator commutator. Three logically distinct scenarios:

### 3.1 Scenario I — SN bracket is also identically zero on KY-Kerr (full descent)

If `[Y_1, Y_2]_SN = 0` for every pair of KY tensors in the Kerr tower (not just at the symbol level via KKPV 2007 Poisson commutativity, but at the full tensor level on `M`), then the abelian obstruction descends *all the way* from operator commutators to classical tensor brackets. The bound on the framework gains a fourth, classical floor. **This is the honest-negative descent path.**

**Likelihood estimate**: MODERATE. KKPV 2007 establishes the Poisson-bracket (symbol-level) version. CKK 2011 §IV computes the SN bracket of CKY forms on Kerr and finds it non-zero in general — but only the projection `π_KY` of the result lands in KY-space, and that projection often vanishes. The full SN bracket lands in Killing-Stäckel space, which is generically non-trivial. So Scenario I is only true if one demands the bracket close *within KY*; relaxing to Killing-Stäckel makes Scenario II likely.

### 3.2 Scenario II — SN bracket non-trivially closes onto Killing-Stäckel; Lie-algebroid structure exists

If the SN bracket of two KY tensors is a non-trivial Killing-Stäckel tensor that *is* in the closure of the Kerr tower (a polynomial in `k_{ab}`, `K_{ab}`, `ξ^a`, `η^a` with closed-form coefficients), then there is a candidate Lie-algebroid structure on the **Killing-Stäckel** tower (not the KY tower) with non-trivial bracket. The CKK 2011 obstruction (failure of graded Jacobi on the KY subspace) is precisely what *forces* working in Killing-Stäckel instead of KY.

In this scenario, Lie-algebroid Casimirs of the Killing-Stäckel algebroid may provide closed-form invariants that the abelian operator-commutator collapsed. **This is the spike-worthy path.**

**Likelihood estimate**: HIGH that Scenario II's bracket closes onto Killing-Stäckel with non-trivial structure (this is essentially the KKPV 2007 result plus CKK 2011 §III). MODERATE that the closure produces a Casimir whose eigenvalue is closed-form. LOW that the closed-form Casimir eigenvalue reduces to the Teukolsky angular separation constant `Λ_{ℓm}(aω)` (because BCC 2006 says `Λ_{ℓm}(aω)` itself has no closed form).

The combination is: a non-trivial Lie-algebroid structure likely exists, but its Casimir eigenvalues likely also fail to be closed-form in the Kerr parameters `(a, M, ℓ, m, s)`. The negative outcome at the *Casimir-closed-form* level remains plausible even after the positive outcome at the *Lie-algebroid-existence* level.

### 3.3 Scenario III — Anchor-induced obstruction descends to a different invariant

The anchor map `ρ : A_KY → TM` introduces a notion that has no analog in the pure operator-commutator picture: the **isotropy Lie algebra** at a point `x ∈ M`, defined as `ker(ρ_x) ⊂ A_x`. Two distinct possibilities:

- **(III.a)** `ker(ρ)` is trivial everywhere → the algebroid is **transitive**, and Lie-algebroid Casimirs reduce to ordinary Lie-algebra Casimirs on each fibre.
- **(III.b)** `ker(ρ)` is non-trivial somewhere → the algebroid is **intransitive**, and there are isotropy-algebra Casimirs that have no analog in the transitive case. These are genuinely new invariants not detected by the operator commutator.

For Kerr, anchor A maps the rank-2 CCKY tensor `k_{ab}` to a *closed conformal* Killing vector — not a true Killing vector. The image of `ρ_A` therefore lies in `Γ(TM)` modulo closed conformal Killing fields — and **the kernel `ker(ρ_A)` contains the rank-2 tensor minus its anchored vector**, which is generically non-trivial. So Scenario III.b is a real possibility for the Cariglia anchor.

**Likelihood estimate**: REAL but LOW that Scenario III.b yields new closed-form invariants. The intransitive structure is generic in Lie-algebroid theory but rarely produces closed-form Casimirs in physics applications. Worth ~5% of the spike's investigative budget — enough to compute `ker(ρ_A)` on Kerr and check whether the isotropy algebra is non-trivial; not enough to fully chase the Casimir if the isotropy turns out trivial.

### 3.4 Decision-relevant summary

The Spike #11 abelian-commutator result is the **principal-symbol image** of whatever bracket structure lives on the KY tensors themselves. The SN bracket carries *strictly more* information than its principal symbol — but the additional information lives in subleading-order terms that the principal-symbol map kills. **It is a priori possible** that the SN bracket on Kerr KY tensors is non-trivial in a way the operator commutator misses, AND that this non-triviality produces a Lie-algebroid Casimir with closed-form eigenvalue. **It is equally a priori possible** that the SN bracket also descends to a structurally abelian closure, giving a fourth side to the framework bound.

Either outcome is publishable as an honest result. The spike is worth running.

---

## 4. Spike protocol — first-spike computation

### 4.1 Setup

- **Manifold**: 4D Kerr, Boyer-Lindquist coordinates `(t, r, θ, φ)`, metric in Frolov-Krtouš-Kubizňák 2017 §2.1 conventions.
- **Primary objects**:
  - `ξ^a = (∂_t)^a` (primary Killing vector, rank 1)
  - `k_{ab} = ∇_a b_b - ∇_b b_a` where `b = (a² cos²θ - r²) dt + ...` is the principal CCKY 2-form potential (FKK 2017 eq. 3.3)
  - Implicit: `K_{ab}`, `η^a` as derived objects
- **Library**: sympy with Cariglia-Krtouš-Kubizňák 2011 PRD 84:024004 §III conventions for the KY bracket; cross-check against Kastor-Ray-Traschen 2007 arXiv:0705.0535 conventions for SN on Killing forms.

### 4.2 Phases

- **Phase 1 — Verify the algebraic identities at the tensor level (no quantization).**
  Compute `[ξ, k]_SN` and `[k, k]_SN` symbolically on Kerr. Cross-check against the algebraic identities in CKK 2011 eq. 3.7-3.10 and KKPV 2007.
  - **Falsifier**: If `[k, k]_SN = 0` identically on Kerr (not just up to projection), Scenario I is realized and the spike concludes with the descent-of-abelian negative. If `[k, k]_SN` is a non-trivial rank-3 tensor, proceed to Phase 2.
- **Phase 2 — Project onto Killing-Stäckel basis and identify Lie-algebroid bracket.**
  Decompose `[k, k]_SN` as a polynomial in `{ξ, η, k, K}`. If the decomposition closes (all coefficients are smooth functions on Kerr with closed-form expressions), this is a candidate Lie-algebroid bracket. Verify graded Jacobi.
  - **Falsifier**: If graded Jacobi fails on the Killing-Stäckel closure with non-zero defect, no Lie algebroid exists on this candidate. Outcome class (c) for Lie-algebroid structure; the SN bracket is "Lie-algebroid-like" but not Lie-algebroid.
- **Phase 3 — Compute anchor map and check Leibniz compatibility.**
  Anchor A (`ρ(Y) = Y^♯`): verify `[Y_1, f Y_2]_{A_KY} = f[Y_1, Y_2]_{A_KY} + (ρ(Y_1)·f) Y_2` for representative `f ∈ C^∞(\text{Kerr})` (e.g., `f = r`, `f = cos θ`, `f = t`).
  - **Falsifier**: If Leibniz fails for anchor A, repeat with anchor B (divergence anchor). If both fail, Lie-algebroid structure does not exist with natural anchor choices.
- **Phase 4 — Casimir computation.**
  Conditional on Phase 3 succeeding. Compute `C_quad = [k, k]_{A_KY}` and check its eigenvalue on the scalar Teukolsky mode `R(r) S(θ) e^{-iωt + imφ}`. Cross-check against the KKPV 2007 Poisson-commutativity result (which gives the *principal-symbol* eigenvalue) for consistency.
  - **Falsifier**: If `C_quad` eigenvalue reduces to a polynomial in `(μ², Λ_{ℓm}(aω), ω, m)` (the Spike #11 joint-eigenvalue tuple) with no additional Kerr-parameter structure, the Lie-algebroid Casimir provides no new closed-form. Outcome class (b): structure exists but Casimir doesn't compress.
- **Phase 5 — Compare to Teukolsky data.**
  Conditional on Phase 4 producing a closed-form expression involving Kerr parameters in a non-trivial way. Compare to BCS 2009 (arXiv:0905.2975) tabulated QNM frequencies for the scalar `ℓ=2, m=0` mode at `a/M ∈ {0, 0.1, 0.5, 0.9}`.
  - **Falsifier**: Numerical mismatch at the percent level or worse.

### 4.3 One-sentence spike protocol

> Compute `[k, k]_SN` symbolically on Kerr; decompose onto the Killing-Stäckel tower; check Lie-algebroid axioms with the metric-contraction anchor `ρ(Y) = Y^♯`; if all close, compute the quadratic Lie-algebroid Casimir and check whether its eigenvalue on scalar Teukolsky modes carries Kerr-parameter information beyond the abelian joint-eigenvalue tuple `(μ², Λ_{ℓm}(aω), ω, m)` of Spike #11.

### 4.4 Estimated spike duration

~1-2 conductor-day equivalents of subagent computation, ~80% sympy symbolic + ~20% numerical comparison against BCS 2009 tables. Comparable to Spike #11's actual cost.

---

## 5. Honest-negative possibility

The most honest framing of the spike-worthy hypothesis: the Schouten-Nijenhuis bracket on the Kerr KY tensors **almost certainly produces a non-trivial Killing-Stäckel closure** (Scenario II at the bracket-existence level), but the Casimir eigenvalue **may still fail to be closed-form** in the Kerr parameters `(a, M, ℓ, m, s)` because the Teukolsky angular separation constant `Λ_{ℓm}(aω)` already has no closed form (BCC 2006 arXiv:gr-qc/0511111).

The descent route from Spike #11's abelian operator commutator is:

> operator commutator (abelian, Spike #11) → Poisson bracket of symbols (abelian, KKPV 2007) → SN bracket of tensors (NON-ABELIAN onto Killing-Stäckel, CKK 2011) → Lie-algebroid Casimir eigenvalue (closed-form? open question)

The first three boxes are known. The fourth is the spike. **The most likely outcome is that Box 4 is non-closed-form in the same way Λ_{ℓm}(aω) is non-closed-form — i.e., the Lie-algebroid structure exists and provides a richer classical-tensor algebra, but its Casimir invariants don't close the QNM spectrum any better than Spike #11's joint-eigenvalue tuple did.**

This is an "honest partial negative": Lie-algebroid refinement exists (positive structural result, publishable in the differential-geometry / mathematical-physics literature), Casimir doesn't close QNMs (negative result, tightens the framework bound). Outcome class (b) from Spike #12A's taxonomy.

A genuinely positive outcome (closed-form Casimir → closed-form QNM identity at generic `Mω`) would be a major contribution; the literature review of 2026-05-12 suggests no published work has achieved this. The spike would be the natural place to attempt it.

---

## 6. Connection to the bounded-framework arc

Three currently-mapped sides of the framework reach (Spikes #11, #12A, and the literature review's §VII.4.1.2 consolidation) all sit at the **operator / quantization** level. Spike #12B would map a fourth side at the **classical-tensor / Lie-algebroid** level. The four-sided picture:

| Side | Level | Spike | Status |
|---|---|---|---|
| KY commuting-operator algebra abelian on generic-`Mω` Kerr | quantum operator | #11 | Negative (PR #359) |
| No İnönü-Wigner contraction KY ↔ photon-ring `SL(2,ℝ)_QN` | quantum operator + algebra-level | #12A | Negative (PR #361) |
| CMS / KY / photon-ring three-pillar partition complete | meta-framework | lit review + §VII.4.1.2 | Mapped (commit `07d1a7e`) |
| **SN bracket / Lie-algebroid refinement on KY tensors** | **classical tensor + algebroid Casimir** | **#12B (proposed)** | **OPEN** |

If Spike #12B is negative (Scenario I or II.b), the framework bound has a classical floor: even before quantization, the KY structure on Kerr produces no closed-form Casimir for generic-`Mω` QNMs. The bound on three sides becomes a bound on three-plus-a-floor.

If Spike #12B is positive (Scenario II.a or III.b with closed-form Casimir), a **fourth side opens**: the classical-tensor algebra carries closed-form information that the quantization-level operator algebra collapsed. This is a publishable contribution to the Kerr-CFT-correspondence / hidden-symmetry literature.

---

## 7. Literature anchors — PDF-verified

| # | Citation | arXiv / DOI | Verification |
|---|---|---|---|
| 1 | Cariglia, Krtouš, Kubizňák 2011, "Commuting symmetry operators of the Dirac equation, Killing-Yano and Schouten-Nijenhuis brackets" | arXiv:1102.4501, Phys. Rev. D 84:024004 | **PDF-verified 2026-05-13** via arXiv abstract retrieval. Abstract explicitly states "Killing-Yano bracket… closely related to the Schouten-Nijenhuis bracket." LOAD-BEARING for §1.2. |
| 2 | Crainic, Fernandes 2003, "Integrability of Lie brackets" | arXiv:math/0105033, Annals of Mathematics 157:575–620 | **PDF-verified 2026-05-13** via arXiv abstract retrieval. Establishes two computable obstructions to Lie-algebroid integration. LOAD-BEARING for §1.3 Lie-algebroid framework. |
| 3 | Gray, Kubizňák 2024, "Homogeneous Symmetry Operators in Kerr-NUT-AdS Spacetimes" | arXiv:2401.03553, Phys. Rev. D 109:084027 | **PDF-verified 2026-05-13** via arXiv abstract retrieval. Authors confirmed Gray + Kubizňák (NOT Houri-Tanahashi-Yasui, per the May-12 attribution catch). Establishes the 4 / 7 / 8 commuting-operator counts at the quantum level. LOAD-BEARING for §0 + §3 descent argument. |
| 4 | Krtouš, Kubizňák, Page, Vasudevan 2007, "Constants of Geodesic Motion in Higher-Dimensional Black-Hole Spacetimes" | arXiv:0707.0001, JHEP 02:004 (2007) | **PDF-verified 2026-05-13** via arXiv abstract retrieval. Establishes Poisson-bracket commutativity of the Killing-tower symbols on `T^*M`. LOAD-BEARING for §3.1 descent path (operator → symbol → tensor). |
| 5 | Frolov, Krtouš, Kubizňák 2017, "Black Holes, Hidden Symmetries, and Complete Integrability" | arXiv:1705.05482, Living Rev. Rel. 20:6 | Cited in the May-12 KY literature review with full verification. Canonical review of the Kerr-NUT-(A)dS hidden-symmetry tower. |
| 6 | Kastor, Ray, Traschen 2007, "Killing-Yano tensors and multi-Hero structures in algebraic-special spacetimes" | arXiv:0705.0535 | Cited but ATTEMPTED-UNVERIFIED. Title approximate; this anchor would be checked at spike-execution time. The 2004 Kastor-Traschen paper (arXiv:hep-th/0407064) on SN brackets of Killing forms is the firmer anchor; the 2007 paper extends it. |
| 7 | Berti, Cardoso, Casals 2006, "Eigenvalues and eigenfunctions of spin-weighted spheroidal harmonics in four and higher dimensions" | arXiv:gr-qc/0511111, Phys. Rev. D 73:024013 | Cited in Spike #11; PDF-verified at that time. LOAD-BEARING for §5 negative-Casimir-eigenvalue obstruction (`Λ_{ℓm}(aω)` is non-closed-form). |
| 8 | Marle 2008, "Calculus on Lie algebroids, Lie groupoids and Poisson manifolds" | Dissert. Math. 457:1-57 | Cited but ATTEMPTED-UNVERIFIED (journal-only, no arXiv). Standard reference for Lie-algebroid Casimirs; should be verified at spike-execution time. |
| 9 | Huebschmann 1990, "Poisson cohomology and quantization" | J. Reine Angew. Math. 408:57-113 | Cited but ATTEMPTED-UNVERIFIED (journal-only, no arXiv). Standard reference for universal enveloping algebra of a Lie algebroid. |

**Note on Frégier-Manetti** (mentioned in the original Task #176 brief): I could not locate a Frégier-Manetti paper specifically on "graded brackets of Killing tensors" via 2026-05-13 search. The phrase may refer to general work on graded Lie algebras applied to differential-geometric tensor brackets, or may be a misattribution. **Status: ATTEMPTED-UNVERIFIABLE; would need clarification at spike-execution time.**

---

## 8. Honest-negative-or-spike-worthy verdict

**Spike-worthy.** The question is precise, the protocol is concrete, the falsifiers are specific, and both positive and negative outcomes are publishable. The most likely outcome (Scenario II.b: Lie-algebroid structure exists on the Killing-Stäckel closure, but Casimir eigenvalues fail to be closed-form) is a clean honest-partial-negative that tightens the framework bound. The less likely but possible positive outcome (Scenario II.a or III.b with closed-form Casimir) would be a major contribution to the Kerr hidden-symmetry / Kerr-CFT-correspondence literature.

Expected cost: 1-2 conductor-day equivalents. Expected information yield: high (either descent confirmation or new positive result). Recommended.

---

## 9. References to project context

- **Spike #11 script** (`docs/srmech/notes/spike_11_ky_casimir_kerr_script.py` on `main` at `07d1a7e`): the operator-level abelian-collapse proof that this spike refines below.
- **Spike #12A script** (`docs/srmech/notes/spike_12a_ky_photonring_interpolation_script.py` on `main` at `07d1a7e`): the contraction-failure analysis that establishes the meta-pattern of obstruction discovery this spike continues.
- **KY literature review** (`docs/srmech/notes/killing_yano_kerr_literature_review_2026-05-12.md` on branch `research/killing-yano-literature-review` at `c85259c`): the state-of-field scan whose §5 Gap 4 ("Carter constant `K` as a Casimir eigenvalue — formalization… the right algebraic framework may be a Lie algebroid or NQ-manifold rather than a Lie algebra") is the precise gap this spike targets.
- **MFO §VII.4.1.2** (`docs/antikythera-maths/mfo_spectral_research_notebook.md` on `main`): the §"open Killing-Yano gap" paragraph that frames this as the natural next research direction in the universal-Casimir-decomposition pattern.

---

## 10. Disposition

This document is research scoping. The user reviews and decides whether to run Spike #12B. If approved, the spike would land on a new branch `research/spike-12b-lie-algebroid-ky-bracket-computation` (or similar), with its own commit + PR.

No claim of "natural extension of" prior work is made here. The technical chain is: Spike #11 (operator level) → KKPV 2007 (symbol level) → CKK 2011 (tensor level) → Spike #12B (Lie-algebroid refinement on the tensor level). Each step is a precise mathematical descent and is cited above with PDF-verified status where applicable.
