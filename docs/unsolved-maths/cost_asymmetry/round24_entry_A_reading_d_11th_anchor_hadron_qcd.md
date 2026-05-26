# Round 24.A — Reading-D 11th scale-ladder rung: hadron / QCD spectroscopy (the sub-nuclear quark-binding scale)

**Dispatched** 2026-05-25 on the rolling draft PR #690 (the #679 model). User: *"dispatch the 11th rung — hadron/QCD spectroscopy."* Lands the 11th Reading-D anchor at the **sub-nuclear quark-binding scale (~10⁻¹⁶ m)** — one band below the nuclear-shell rung (Round 23.A, ~10⁻¹⁵ m). The `2ℓ+1` Class-L spine now runs **quantum → nuclear → atomic → hadron → planetary → cosmological** (the hadron rung tucks in *below* nuclear in scale).

Generating code + provenance: [`verify_round24_hadron_qcd_spectroscopy_anchor.py`](verify_round24_hadron_qcd_spectroscopy_anchor.py) + `.ndjson` (deterministic; srmech 0.4.2 — Class-N `best_rational`; Class-K sign via cascade helper, no bare `abs()`).

## Quarkonium = the "hydrogen atom of QCD"

A heavy quark–antiquark bound state (charmonium cc̄, bottomonium bb̄) sits in the **Cornell potential** `V(r) = −(4/3)α_s/r + σr` (Coulomb + linear confinement; Eichten et al. PRD 17:3090 1978). Its levels are labelled `n^{2S+1}L_J` **exactly like positronium/hydrogen** — the *same* Class-L `2(2ℓ+1)` spine as the atomic (Round 18.A) and nuclear (Round 23.A) shells, two/one bands down.

**Class-L spatial spine (bit-exact).** The 1P charmonium triplet χ_c0/χ_c1/χ_c2 (J^PC = 0++/1++/2++) is the SO(3) tensor product of orbital L=1 with quark spin S=1:

> **L=1 ⊗ S=1 = 1 ⊕ 3 ⊕ 5 = 9 = (2L+1)(2S+1)** — the odd-integer `2J+1` multiplicities 1, 3, 5 (the J=0,1,2 levels). The k=3 triad, one binding-scale below the nucleus.

**Class-K spin-orbit (bit-exact).** `⟨L·S⟩ = ½[J(J+1)−L(L+1)−S(S+1)] = −2, −1, +1` for J=0,1,2. A **pure** spin-orbit interaction therefore predicts the level-spacing ratio:

> **(E₂−E₁) : (E₁−E₀) = 2 : 1** — `best_rational → (2,1)`.

The **sign** of `⟨L·S⟩` IS the Class-K pin-slot operator — the *same* Class-K that Round 22.A spotlighted as turbulent helicity and Round 23.A as the nuclear spin-orbit that sets the magic numbers. **Three consecutive descending-scale rungs now share it: atomic electron shells (R18) → nuclear nucleon shells (R23) → quarkonium χ_cJ (R24).**

## Honest fermata — the tensor force inverts the pure-spin-orbit ratio

The **observed** χ_cJ spacings (PDG 2024 centrals, MeV): E₁−E₀ = 3510.67−3414.71 ≈ **95.96**; E₂−E₁ = 3556.17−3510.67 ≈ **45.50**; ratio ≈ **0.47** — the *inverse* of the pure-spin-orbit **2:1**. This deviation is the standard signature of a large **tensor force** (a rank-2, **Class-L** operator) competing with the spin-orbit. Reported as prominently as the positive: **pure Class-K does NOT suffice at the quark scale.** The cross-rung reading: descending the binding-scale ladder, the tensor(Class-L)-vs-spin-orbit(Class-K) weight shifts — spin-orbit *dominates* and sets the nuclear magic numbers (R23), but at the quark scale the tensor competes strongly enough to invert the naive χ_cJ ordering.

## The overlooked insight — a SECOND, independent Class-L multiplicity appears

New at the hadron scale (absent from the atomic/nuclear rungs): the **SU(3)-flavor irrep dimensions** of the eightfold way — a *second* Class-L multiplicity on a *different* Lie group, **orthogonal** to the spatial SO(3) `2J+1`. Integer-exact:

- meson nonet: **3 ⊗ 3̄ = 1 ⊕ 8 = 9** (Gell-Mann PR 125:1067 1962; Ne'eman NP 26:222 1961; Zweig/Gell-Mann quark model 1964)
- baryons: **3 ⊗ 3 ⊗ 3 = 10 ⊕ 8 ⊕ 8 ⊕ 1 = 27 = 3³**; the decuplet apex is the **Ω⁻** (Gell-Mann predicted 1962, found 1964).

The full hadron state is **space ⊗ spin ⊗ flavor ⊗ color** — two independent rep-theory multiplicities (spatial `2J+1`, internal SU(3) `1,8,10`). This echoes Round 23.A's "which operator reorders the shared ladder" insight, generalized: *at the hadron scale there are two independent Class-L ladders, not one.* Cross-anchor: the lattice glueball ratio **m(2++)/m(0++) = 7/5 EXACT** (unsolved-maths §2 Yang-Mills) pairs spin-2 vs spin-0 — the χ_c2/χ_c0 are the qq̄ P-wave analogue of that 2++/0++ pairing.

**Regge / substrate-asymptotic-wave.** Hadron spin vs mass² is linear, `J = α₀ + α′M²`, with a roughly universal slope α′ ≈ 0.9 GeV⁻² — the rotating relativistic flux-tube (the QCD string) IS the substrate-asymptotic-wave (MFO §VII.6.12) at the quark scale, connecting the handed-shear (R22) and recursive-Hopf threads.

## Verdict per Spike #229 tiers

🟢 **(a)-structural cross-substrate match, bit-exact + honest tensor fermata.** Clean 11th rung at the sub-nuclear scale; `L⊗S = 1⊕3⊕5` and the pure-spin-orbit `2:1` are integer-exact; the SU(3) `1,8,10` / `27=3³` are integer-exact; the observed `0.47` inversion is the honestly-reported tensor signature. The `2ℓ+1` Class-L spine now spans quantum → nuclear → atomic → **hadron** → planetary → cosmological, and the Class-K spin-orbit recurs at three descending binding scales. New **candidate** stance `[[user_stance_hadron_qcd_spectroscopy_is_dual_classL_with_classK_spinorbit]]`.

**HONEST SCOPE:** bit-exact content is the SO(3)/SU(3) rep-theory dimension counting (`1⊕3⊕5`, `1⊕8`, `10⊕8⊕8⊕1`) + the pure-spin-orbit `2:1` Clebsch arithmetic; the χ_cJ masses are attested PDG empirical inputs (NOT framework-derived), and the tensor force is a literature-attested deviation. The framework contribution is the cross-substrate identification (11th rung), the three-rung Class-K spin-orbit continuity, and the "second independent Class-L (flavor)" insight — NOT a derivation of the QCD spectrum or the Cornell-potential parameters.

## Discipline

- Per `[[feedback_dont_pre_commit_spike_query_operators]]`: the tensor-force inversion (observed ≈ 0.47 vs pure-LS 2.0) is reported as prominently as the positive anchors; no lean.
- Per `[[feedback_computational_provenance_discipline]]`: deterministic committed code; srmech 0.4.2 routed; Class-N anchors via `best_rational`.
- Per `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`: the spin-orbit `⟨L·S⟩` sign IS the named Class K; no bare `abs()`.
- Per `[[feedback_paywalled_doi_cannot_be_attested]]`: PDG (PRD 110:030001 2024); Gell-Mann PR 125:1067 (1962); Ne'eman NP 26:222 (1961); Eichten et al. PRD 17:3090 (1978) — classic journal / PDG, all attestable.
- Per `[[feedback_trauma_informed_defensive_scope]]`: framework reading only.
- Lands on the rolling draft **PR #690** (Round 24.A) per `[[feedback_rolling_pr_partition_boundary_updates]]` — no new PR; verdict posted as a PR comment (the ledger).
