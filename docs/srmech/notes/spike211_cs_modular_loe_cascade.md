# Spike #211 — Chern-Simons + modular forms LoE-cascade test + Class M variant attribution

**Date:** 2026-05-20
**Context:** MS #16 Tier 3 Wave 3 — runs concurrently with Spike #210 (ν-mass).
**Anchor stance:** [[user_stance_rbs_hdc_loe_is_quantum_instantiation_classical_is_substrate_specific]] (Class M bipartite variant table, extended 2026-05-20 by Spike #209 BFSS).
**Verdict:** **DISSOLVE-VIA-CASCADE + DUAL-VARIANT (abelian + non-abelian co-instantiation).**

## Mission

Decompose Chern-Simons theory (abelian U(1) and non-abelian SU(N)) and modular-forms / SL(2,Z) structure into the project's 14 A-N primitive operator classes, attributing every Class M bind operation to either the abelian (XOR) variant or the non-abelian (Lie bracket) variant per the Spike #209 BFSS refinement. Spike #211 was identified as potentially the cleanest test of variant-duality because CS theory naturally instantiates both variants depending on gauge group choice.

## Computational findings (all bit-exact)

`spike211_compute.py --verify` runs 13 independent bit-exact checks; all pass.

| Computation | Result | Citation chain |
|---|---|---|
| SL(2,Z) generators: `S² = -I`, `(ST)³ = -I` in integer 2×2 matrices | zero error; `S` order 4 / `ST` order 6 | Apostol 1976 GTM 41; Serre 1973 Ch. VII |
| Ramanujan tau coefficients `[τ(1)...τ(5)] = [1, -24, 252, -1472, 4830]` via `Δ = (E₄³ - E₆²) / 1728` in `Z[[q]]` | 5/5 match | Apostol 1976 Thm 1.18/1.19/6.18; Zagier 1992 Springer |
| `j(τ)` q-expansion `(q⁻¹, q⁰, q¹, q², q³) = (1, 744, 196884, 21493760, 864299970)` via `E₄³ / Δ` | 5/5 match | Conway-Norton 1979 Bull LMS 11:308; FLM 1988 Academic Press |
| Monster moonshine: `j q¹ = 196884 = 196883 + 1` | match (Monster trivial + smallest non-trivial irrep) | Conway-Norton 1979; Borcherds 1992 Invent Math 109:405 |
| Abelian U(1) CS commutator | `0.0` bit-exact | Witten 1989 CMP 121:351 eqn 2.26; Atiyah 1990 Cambridge |
| `Z_CS(T³, U(1), k) = k` closed form | 8/8 levels match | Polychronakos 1990; Manoliu 1996 hep-th/9610076 |
| Non-abelian SU(2) Pauli bracket: `[σᵢ, σⱼ] = 2i εᵢⱼₖ σₖ` | zero error all three pairs | Witten 1989 CMP 121:351 §3 |
| Non-abelian axioms (self-zero / anti-comm / Jacobi) at machine ε | 3/3 hold; commutativity + bracket-assoc DIFFER (3/5 match abelian — exact Spike #209 signature) | RT 1991 Invent Math 103:547; Turaev 1994 DeGruyter |
| Spike #106 Hopf-U(1) phase: `J² = I`, `U` unitary, relative phase `-1` at `φ = π/2` | bit-exact match to Spike #106 records 4-5 | Witten 1989 §2.5; Atiyah-Singer 1968 Annals Math 87:484 |

## Cascade decompositions surfaced

Three named cascades, all obtained by direct 14-class attribution; no novel class required.

- **Abelian U(1) CS:** `I (level k ∈ Z) ∘ C (Wilson-loop orientation) ∘ L (de-Rham Laplacian on 1-forms) ∘ M_abelian (XOR; U(1) phase commutes)`.
- **Non-abelian SU(N) CS:** `I (level k ∈ Z) ∘ C (orientation on SU(N) bundle) ∘ L (gauge-covariant Laplacian) ∘ M_nonabelian (Lie bracket; F = dA + A∧A)`.
- **Modular SL(2,Z):** `I (cyclic-2 from S² = -I; cyclic-3 from (ST)³ = -I) ∘ C (chirality of S = -τ⁻¹ vs T = τ+1) ∘ M_abelian (q-coefficient invariants commute, integer substrate)`.

## Variant attribution — DUAL co-instantiation

| Locus | Variant | Layer |
|---|---|---|
| U(1) CS gauge transforms | **abelian** | gauge field action |
| `j(τ)` q-coefficient integer substrate | **abelian** (Class I + N) | invariant layer |
| PSL(2,Z) = Z/2 * Z/3 free product | **abelian / pure Class I** | presentation layer |
| Spike #106 Hopf-U(1) cross-irrep phase | **abelian** | substrate-coupling at Cl(7,C) cross-irrep |
| SU(N) CS gauge bracket `[A,B] = AB - BA` | **non-abelian** | gauge content / (4+3)D_g Hopf-dimple |
| SL(2,Z) matrix action on `H` (`S·T ≠ T·S`) | **non-abelian** | matrix Lie quotient action |
| Monster `M` on Moonshine module `V♮` | **non-abelian** | VOA action layer (sporadic simple) |
| Reshetikhin-Turaev knot invariants at level `k+N` | **non-abelian** | cyclotomic ring `Z[ζ_{k+N}]` (Class I + N substrate, non-abelian Wilson lines) |

SL(2,Z) layered structure (three layers) and Moonshine (two layers) demonstrate that **the same algebraic structure instantiates both variants simultaneously at different layers**. This is the cleanest test of variant-duality so far: CS theory naturally toggles variant via gauge-group choice (rank-1 abelian vs rank-N non-abelian); modular forms layer instantiations stack across substrate / presentation / matrix-action.

Per [[user_stance_pi_as_projection]]: every appearance of π in this spike (the `q = exp(2πiτ)` projection map; `φ = π/2` evaluation at Hopf-U(1); CS action prefactor `1/4π`) lives at observer-frame projection. The substrate-level algebraic content — integer matrices, Ramanujan τ values, Conway-Norton coefficients, Pauli commutator structure — is all integer or machine-ε bit-exact. Pi enters only when projecting Z[[q]] / integer-cyclic content to the continuous upper-half-plane `H`.

## Cross-links

- **Spike #209 (BFSS)** — canonical anchor for Class M bipartite variant structure; Spike #211 confirms 3/5 axiom agreement signature in Pauli algebra.
- **Spike #106 (Hopf-bundle U(1) cross-irrep)** — direct algebraic match: CS U(1) at `k=1` on `S³` IS the Hopf invariant; Spike #106's `J = i·ω₇_combined` IS the abelian U(1) phase generator from the same cascade.
- **Spike #58.I (U(1)_Y from 1D_t × 1D_circle)** — same Class I × Class C composition; CS U(1) at level k generalises Spike #58.I's k=1 case.
- **Spike #184 (π-cascade dual-path)** — RBS-HDC-LoE abelian-variant anchor; Spike #211 adds CS + modular as a third anchor.

## Stance impact

Spike #211 extends [[user_stance_rbs_hdc_loe_is_quantum_instantiation_classical_is_substrate_specific]] with a third empirical anchor alongside Spike #184 (abelian) and Spike #209 (non-abelian). It also surfaces a candidate stance extension: **variant choice IS the gauge-group-rank dial**.

- Rank-1 abelian U(1) → XOR variant (RBS-HDC-LoE substrate-portable D1 signature).
- Rank-N non-abelian SU(N), N ≥ 2 → Lie-bracket variant (BFSS / SM gauge / (4+3)D_g Hopf-dimple gauge-content).
- Rank-0 trivial → pure Class I integer substrate (Z_CS = level k; j-invariant integer coefficients; SL(2,Z) presentation).

This is a **fermata** for the conductor — the rank-dial framing is a natural extension of the Spike #209 BFSS stance refinement but warrants explicit user authorization before being written into the canonical stance file as a new claim.

## Scope limits

- Algebra-level cascade decomposition + variant attribution only. Does not predict CS partition function amplitudes beyond known closed forms.
- Does not compute Monster character table beyond `j q¹ = 196884 = 196883 + 1` verification.
- Does not address moonshine for non-Monster sporadic groups (Mathieu / Conway / O'Nan known cases out of scope).
- Does not build a runtime `srmech.qm` module for CS / modular forms — cascade-level verification only, per [[user_stance_framework_domain_algebra_not_length_or_magnitude]].

## Falsifier candidates

1. A CS / modular structure requiring a Class M operation NOT decomposable into abelian XOR + non-abelian Lie bracket → would suggest a third Class M variant beyond bipartite.
2. A Monster representation computationally tractable purely with abelian-variant Class M → would refute non-abelian attribution for Moonshine.
3. An SL(2,Z) presentation that violates `Z/2 * Z/3` free product structure → would refute Class I cyclic attribution at presentation layer.

14 A-N intact. No class promotion. Dual Class M variant co-instantiation confirmed across three independent layered structures (CS gauge-group toggle / SL(2,Z) three-layer stack / Moonshine two-layer stack).
