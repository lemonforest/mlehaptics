# Refined structural law for closed-form spectral compression — consolidation of Spikes #14–#18

**Branch:** `research/refined-structural-law-consolidation` (from `main` at `ede9f75`)
**Date:** 2026-05-13
**Predecessor spikes:**
- Spike #14 [`spike_14_abelian_wall_structural_law_test_2026-05-13.md`](spike_14_abelian_wall_structural_law_test_2026-05-13.md) at `77cf6af` — original 3-mechanism law, 5 settings
- Spike #15 [`spike_15_heun_monodromy_test_2026-05-13.md`](spike_15_heun_monodromy_test_2026-05-13.md) at `0ba297a` — mechanism (iv) introduction
- Spike #16 [`spike_16_painleve_algebraic_classification_2026-05-13.md`](spike_16_painleve_algebraic_classification_2026-05-13.md) at `efa4dea` — nonlinear extension
- Spike #17 [`spike_17_spherical_harmonics_higher_d_2026-05-13.md`](spike_17_spherical_harmonics_higher_d_2026-05-13.md) at `c4acc61` — compactness paired test
- Spike #18 [`spike_18_heisenberg_representations_2026-05-13.md`](spike_18_heisenberg_representations_2026-05-13.md) at `ac345e2` — layered-mechanism finding
**Status:** SRMECH-LOCAL CONSOLIDATION — synthesizes the May 2026 abelian-wall arc into a single near-publishable structural-law statement. **10/10 fit across 5 mathematical domains**: general relativity, linear special-function ODEs, nonlinear integrable systems, higher-dimensional representation theory, non-compact non-semisimple Lie groups. No new mechanism beyond the 4-mechanism refined law (with (ii) absorbed into (iv)) is required.

---

## §1. The slot and the motion

Consider the polynomial expression

```
y = x³ + x² + x
```

The user's framing, 2026-05-13: *"this is pure pin-slot until a value is placed upon x and it becomes more than just a statement."*

This is the conceptual frame for everything below. The polynomial as written is algebra — a slot. Nothing moves until a value of `x` is substituted; then `y` is a number. The derivative `dy/dx = 3x² + 2x + 1` is a shift operator on the polynomial-coefficient sequence — purely algebraic, no limit invoked. Umbral calculus and finite-difference calculus take this stance directly: the calculus is the algebra of how the slot rearranges itself; the motion is what happens when the algebra is projected onto values. *"The math is the slot; the motion is the integral."*

The gear is the same idea, concretized in three dimensions (per `user_stance_fiber_as_spatially_absent_encoding.md`). The teeth encode `ℤ/n` algebraically. From the gear's own coordinates, the rotation axis is a 0D fixed-point set — the gear does not move from its own frame. What "comes out" externally — gear ratios, period content, phase relationships — is the projection of the hidden algebraic content through rotation. The teeth are the slot; the rotation is the motion; the algebra is spatially absent.

This consolidation reports a structural law that operates at the same level of generality across **ten distinct mathematical settings** at increasing levels of sophistication: when does a hidden algebraic encoding admit a closed-form spectral compression — i.e., when does the algebra-as-slot admit finite-arithmetic motion?

---

## §2. The refined structural law

After five spikes, the cleanly-supported statement is:

> **Refined structural law (4-mechanism form, with (ii) absorbed into (iv)).** *Closed-form spectral compression exists iff the algebraic structure (commuting operators, monodromy data, isomonodromic-deformation tau-function, or any combination thereof) selects a finite-dimensional invariant subspace at each closed-form-eligible parameter point, via one of the following mechanisms:*
>
> 1. **Non-abelian Lie factor with finite-dim irreps + Casimir labeling.**
> 3. **Finite discrete-group orbit on the structural space** — finite monodromy of a finite-dim local system; finite mapping-class-group orbit on the character variety; finite affine-Weyl Bäcklund orbit on parameter space.
> 4. **Discrete spectral / parameter quantization on a rational-/integer-/elliptic-lattice locus** — accessory-parameter spectrum; integer-filtration; Bäcklund-orbit lattice; Picard elliptic-rational lattice.

Mechanism (ii) of Spike #14 — *discrete integer-parameter filtration cutting out (2n+1)-dim subspaces* — was identified in Spike #15 §3.4 as a special case of (iv) at integer accessory-parameter values, and the numbering is preserved with (ii) absorbed.

**Layered-mechanism clarification (Spike #18).** Mechanism (i) may apply at the *enveloping-algebra layer* even when it fails at the base group, with the same integer-lattice index running through both layers. The law statement does not require the eligible mechanism to operate at any specific algebraic layer — any mechanism at any layer suffices. The Heisenberg + harmonic-oscillator setting is the canonical example: mechanism (i) fails at the Heisenberg group `H_n` itself (no non-trivial finite-dim unitary irreps, by Stone–von Neumann and the finite-dim trace argument) but is recovered at the metaplectic enveloping group via the compact `U(n) ⊂ Sp(2n, ℝ)` whose finite-dim `Sym^k(ℂ^n)` irreps label the harmonic-oscillator eigenspaces. The same integer `k` indexes both the Heisenberg-layer mechanism-(iv) number-operator eigenvalue and the metaplectic-layer mechanism-(i) `U(n)`-Casimir highest weight.

The unifying principle the law expresses, in compressed form: **closed-form spectral compression exists iff the algebraic structure selects a finite-dimensional invariant subspace via one of (i), (iii), (iv) at some enveloping-algebra layer.** This is the structural realization of the user's "fiber-as-spatially-absent-encoding" stance — the hidden algebraic encoding (Lie-irrep label, monodromy data, accessory-parameter spectrum) is the substrate; closed-form expressions are its projection into a finite arithmetic form.

---

## §3. The ten worked examples

The 10 settings, grouped by mathematical domain:

| # | Setting | Mechanism(s) | Closed-form? |
|---|---|---|---|
| 1 | CMS Kerr (low-Mω) | (i) `SL(2,ℝ)²` Casimir | ✓ |
| 2 | KY Kerr (generic-Mω) | none — abelian commuting algebra | ✗ |
| 3 | Lamé `S²` | (iv) integer-`n` + secular-`B` quantization | ✓ in `sn, cn, dn` |
| 4 | Bessel disk | none — abelian `U(1)` after Dirichlet BC | ✗ |
| 5 | ₂F₁ Gauss | (iii) finite monodromy iff Schwarz-list | ✓ iff finite monodromy |
| 6 | Heun | (iii) + (iv) | ✓ in 61 VF-families + DK-spectral-q |
| 7 | Painlevé I–VI | (iii) + (iv) generalized | ✓ on 45 + 4 + 1 PVI families; half-integer α PII; etc. |
| 8 | `S^d` harmonics (d ≥ 3) | (i) + (iv) | ✓ in Gegenbauer / Gel'fand-Tsetlin chain |
| 9 | `H^d` non-compact dual | none — `SO(d, 1)` only infinite-dim unitary irreps | ✗ |
| 10 | Heisenberg `H_n` + HO | (iv) at base + (i) at metaplectic layer | ✓ in Hermite / Fock / `Sym^k(ℂ^n)` |

### §3.1 General relativity — Kerr quasi-normal modes (Spikes #11–#13 background, scored in #14)

**CMS Kerr (low-Mω, row 1).** The CFT-like hidden-conformal `SL(2, ℝ) × SL(2, ℝ)` structure of Kerr near-extremal quasi-normal modes is a non-abelian Lie factor with finite-dim irreps and a Casimir that labels the modes by a single conformal weight (per Spike #14 §0 background and the May 2026 KY-Kerr arc Spikes #9–#13). **Mechanism (i) applies cleanly**; closed-form spectrum exists in the low-Mω regime.

**KY Kerr (generic-Mω, row 2).** Gray–Kubizňák 2024 (`arXiv:2401.03553`) established that the Killing–Yano commuting-operator algebra of generic-Mω Kerr is **abelian** — three commuting operators with no second non-abelian factor. None of mechanisms (i), (iii), (iv) operate. The refined law predicts **no closed-form spectrum**, consistent with the empirical absence of any known closed-form expression for generic Kerr QNM frequencies. This is the **abelian-wall obstruction** the spike series was named after.

### §3.2 Linear special-function ODEs (Spikes #14 + #15)

**Lamé on `S²` (row 3).** Lamé's equation `Λ'' + (h − n(n+1)k² sn²u)Λ = 0` (Whittaker–Watson 1927 §23; Erdélyi 1955 vol. 3 ch. XV) admits Lamé polynomials for non-negative integer `n`, forming a `(2n+1)`-dim space of solutions with `(2n+1)` discrete eigenvalues `h` that are roots of a finite-degree secular polynomial. The Stäckel commuting algebra on the triaxial ellipsoid is purely abelian (Eisenhart 1934; Morse–Feshbach 1953 §5.1); the closed-form mechanism is **integer-`n` filtration + secular-`B` quantization** — mechanism (iv). The closed form is polynomial in the elliptic functions `sn, cn, dn`, with eigenvalues algebraic over `ℚ(k², n(n+1))`.

**Bessel disk (row 4).** The Dirichlet eigenvalue problem `−Δu = λu, u(1, θ) = 0` separates into Bessel equations with eigenvalues `λ_{n,k} = j_{n,k}²` where `j_{n,k}` are the Bessel-zero numbers. Watson 1944 (*A Treatise on the Theory of Bessel Functions* §15) and Siegel-class transcendence theorems establish `j_{n,k}` is transcendental over `ℚ`. The remaining symmetry is purely `U(1)` (abelian); the `R⁺` dilation that would otherwise pair with `SO(2)` is broken by the Dirichlet BC. **No mechanism applies**, the law correctly predicts no closed-form eigenvalue spectrum.

**₂F₁ Gauss (row 5).** The Gauss hypergeometric equation has a 2-dim local system on `ℙ¹ \ {0, 1, ∞}` with 3-generator monodromy `⟨M₀, M₁, M_∞⟩`. Closed-form-in-radicals exists iff monodromy is **finite**, with the 15 cases of Schwarz 1873 (*J. reine angew. Math.* 75, 292–335) — cyclic, dihedral, tetrahedral `A₄`, octahedral `S₄`, icosahedral `A₅` — extended to `_nF_{n−1}` by Beukers–Heckman 1989 (*Invent. Math.* 95, 325–354). **Mechanism (iii) applies cleanly**; this is the canonical instance.

**Heun (row 6).** Heun's equation with 4 regular singular points introduces an **accessory parameter `q`** absent from ₂F₁. The refined law splits the closed-form locus into two branches: (iii) finite-monodromy Heun-to-₂F₁ pull-backs — **61 parametric families** of degree up to 12 realized by 48 Belyi coverings (Vidūnas–Filipuk 2013 `arXiv:0910.3087`, *Funkcial. Ekvac.* 56, 271–321; Vidūnas–Filipuk 2014 `arXiv:1204.2730`, *Osaka J. Math.*); and (iv) reducible-monodromy polynomial solutions with accessory-parameter spectral quantization (Dubrovin–Kapaev 2018 `arXiv:1809.02311`, *SIGMA* 14, 093). Takemura 2004 (`arXiv:math/0201208`, *J. Nonlin. Math. Phys.* 11, 21–46) realizes the same structure for the BC₁ Inozemtsev finite-gap form. Eremenko 2020 (`arXiv:1905.02537`, *Proc. AMS* 148(9), 3957–3965) gives a non-constructive finiteness theorem for `PSU(2)`-monodromy values of `q`. **Mechanisms (iii) and (iv) apply, sometimes both at once.**

### §3.3 Nonlinear integrable systems — Painlevé I–VI (Spike #16)

**Painlevé I–VI (row 7).** The six Painlevé equations are the "nonlinear special-function ODEs" characterized by the Painlevé property (Painlevé 1900–1902 *Acta Math.*; Gambier 1910 *Acta Math.*). Algebraic-solution loci are the closed-form question for nonlinear isomonodromic deformations.

For PVI, Lisovyy–Tykhyy 2014 (`arXiv:0809.4873`, *J. Geom. Phys.* 85, 124–163) gives the **complete classification of algebraic solutions**: 45 isolated equivalence classes plus 4 continuous families (Riccati I, dihedral II, tetrahedral III, octahedral IV) plus the Picard family — algebraic-solution existence equivalent to **finite-orbit of the extended modular group `Λ̄`** acting on the `SL₂(ℂ)`-character variety of the rank-2 Fuchsian system. Boalch 2006 (`arXiv:math/0406281`, *Crelle* 596, 183–214) classifies the 52 icosahedral cases under Okamoto's affine `F₄` Weyl-group equivalence. Cantat–Loray 2009 (`arXiv:0711.1579`, *Ann. Inst. Fourier* 59, 2927–2978) reads the same condition as finite orbits of the mapping class group `MCG(Σ_{0,4})` on the character variety — a holomorphic-dynamical-system framing. **This is mechanism (iii) lifted to nonlinear isomonodromic deformation.**

For PII rational solutions, Yablonskii 1959 / Vorobiev 1965 (both *Vestsi Akad. Navuk BSSR*) established existence iff `α = n + 1/2`, generated by the affine `A₁` Bäcklund-orbit recursion. For PIV, Okamoto 1986 gives three families of integer-lattice rational solutions generated by the affine `A₂` Weyl-group orbit (Noumi–Yamada 1998–2004 *Comm. Math. Phys.* / *Funkcial. Ekvac.*). For PIII / PV / PVI, Umemura 1996 (*Nagoya Math. J.* 148, 151–198) gives the rational-solution polynomials. **All are mechanism (iv) realized as Bäcklund-orbit lattice quantization.**

The Picard family of PVI (Picard 1889 *J. Math. Pures Appl.*; Fuchs 1907) is the most subtle (iv) instance — a continuous 2-parameter family of elliptic-function solutions parameterized by `(ν₁, ν₂)`, algebraic on the rational-points subset `ℚ²`. The seed solution is literally a Weierstrass elliptic function — a Lamé solution of PVI — making Picard mechanism (ii) ⊂ (iv) lifted to nonlinear via the isomonodromic Riemann–Hilbert correspondence. **Mechanism (iv) extends to the elliptic-rational lattice variant.**

### §3.4 Higher-dimensional representation theory (Spike #17)

**`S^d` harmonics for d ≥ 3 (row 8).** The scalar Laplace–Beltrami operator on `S^d ⊂ ℝ^{d+1}` has eigenvalues `λ(d, ℓ) = ℓ(ℓ + d − 1)` with eigenspaces of dimension `D(d, ℓ) = (2ℓ + d − 1)(ℓ + d − 2)! / (ℓ! (d − 1)!)`. These are `SO(d+1)`-irreps of highest weight `(ℓ, 0, ..., 0)` (Vilenkin 1968 *Special Functions and the Theory of Group Representations*; Müller 1966 *Spherical Harmonics*; Stein–Weiss 1971 *Introduction to Fourier Analysis on Euclidean Spaces* Ch. 4; Atkinson–Han 2012 *Spherical Harmonics and Approximations on the Unit Sphere*). Closed-form basis: iterated Gegenbauer / Jacobi polynomials along the Gel'fand–Tsetlin chain `SO(d+1) ⊃ SO(d) ⊃ ... ⊃ SO(2)` (Gel'fand–Tsetlin 1950 *Dokl. Akad. Nauk SSSR* 71, 825–828; Želobenko 1973 *Compact Lie Groups and Their Representations*). Verified at `d ∈ {3, 4, 5, 6, 7}`, `ℓ ∈ {0, ..., 5}` via `spike_17_spherical_harmonics_verification_script.py` — 30/30 multiplicity-free branching identities `D(d, ℓ) = Σ_{k=0}^{ℓ} D(d−1, k)` check.

**Mechanism (i) + (iv) apply redundantly.** Mechanism (i) via `SO(d+1)` finite-dim irreps + quadratic-Casimir labeling; mechanism (iv) via the integer-`ℓ` lattice quantization. The exceptional embeddings `S^3 = SU(2)` and `S^7` parallelizable (Adams 1960 *Ann. Math.* 72, 20–104; Bott–Milnor 1958 *Bull. AMS* 64, 87–89) do not introduce a new mechanism — `S^3`'s bi-regular structure is captured by `SO(4)`-isometry, and `S^7`'s octonion multiplication is not a Lie-group action and does not enter scalar-SH theory.

**`H^d` non-compact dual (row 9).** Hyperbolic space `H^d = SO(d, 1)/SO(d)` is the non-compact dual rank-1 symmetric space. `SO(d, 1)` is non-compact and has only infinite-dim unitary irreps (principal series, complementary series, discrete series — all infinite-dim). The scalar Laplacian on `H^d` has **purely continuous spectrum** on `[(d−1)²/4, ∞)` with no `L²` eigenfunctions (Helgason 1984 *Groups and Geometric Analysis* Ch. III; Borthwick 2007 *Spectral Theory of Infinite-Area Hyperbolic Surfaces*). The refined law correctly predicts **no closed-form spectral compression**; the compactness restriction of mechanism (i) is genuine, not framing elasticity.

### §3.5 Non-compact non-semisimple Lie — Heisenberg + harmonic oscillator (Spike #18)

**Heisenberg `H_n` + HO (row 10).** The harmonic-oscillator Hamiltonian `H = ½(P² + Q²) = N + n/2` on `L²(ℝ^n)` has the textbook integer-lattice spectrum `E_k = k + n/2` with multiplicity `C(n + k − 1, k)`. The closed-form basis is Hermite functions on Fock space, generated by the ladder operators `a_i, a_i†` with the vacuum-annihilation condition `a_i |0⟩ = 0` as discrete-selection. **Mechanism (iv) fits cleanly** — integer is `k`, lattice is `ℤ_{≥0}`, the structurally simplest mechanism-(iv) instance.

**Mechanism (i) fails at the Heisenberg-only level.** Stone 1932 (*Annals of Mathematics* 33, 643–648) and von Neumann 1931 (*Math. Ann.* 104, 570–578) established uniqueness of the Schrödinger rep up to unitary equivalence for each non-zero central character. The finite-dim trace argument (`tr([P, Q]) = tr(Z) = iℏ · dim V` and `tr([A, B]) = 0` for finite-dim) forces every finite-dim unitary irrep of `H_n` to factor through the abelian quotient with `ℏ = 0` (Kirillov 1976 *Elements of the Theory of Representations* §15.2; Folland 1989 *Harmonic Analysis in Phase Space* §1.5). The HO Hamiltonian cannot act on any finite-dim Heisenberg irrep.

**Mechanism (i) is recoverable at the metaplectic enveloping layer.** The Schrödinger rep of `H_n` extends uniquely to a projective unitary representation of `Sp(2n, ℝ)` on the same `L²(ℝ^n)` — the **oscillator (Weil) representation** (Weil 1964 *Acta Math.* 111, 143–211; Howe 1980 *Bull. AMS* (NS) 3, 821–843; Folland 1989 Ch. 4). Under the maximal compact `U(n) ⊂ Sp(2n, ℝ)`, the oscillator rep decomposes as `L²(ℝ^n) = ⊕_{k=0}^∞ Sym^k(ℂ^n)`, a direct sum of finite-dim `U(n)`-irreps of dimension `C(n + k − 1, k)` and highest weight `(k, 0, ..., 0)`. The HO Hamiltonian acts on `Sym^k(ℂ^n)` as `(k + n/2) · id` — the central `U(1) ⊂ U(n)` infinitesimal generator. Verified numerically in `spike_18_heisenberg_verification_script.py` §5 for `n ∈ {1, 2, 3}`, `k ∈ {0, 1, 2, 3}`.

**This is the first layered-mechanism instance in the spike series.** The same integer `k` indexes the mechanism-(iv) Fock-space number-operator eigenvalue (Layer 1, Heisenberg) and the mechanism-(i) `U(n)`-Casimir highest-weight label (Layer 2, metaplectic). The two mechanisms are not contradictory or redundant — they produce consistent closed-form structure at different enveloping-algebra layers, with the integer lattice carrying through both readings.

---

## §4. The three no-mechanism cases

The law makes a sharp prediction in the negative direction: where no mechanism (i), (iii), or (iv) applies, no closed-form spectral compression exists. Three settings test this:

**KY Kerr (row 2).** Gray–Kubizňák 2024 (`arXiv:2401.03553`) shows the commuting-operator algebra of generic-Mω Kerr is abelian. The Killing–Yano two-form generates an abelian tower with no second non-abelian factor; no integer filtration or finite-monodromy structure is available either. Mechanism (i) fails (no non-abelian Lie factor); no Fuchsian-local-system or accessory-parameter structure is present that would invoke (iii) or (iv). **The law predicts no closed-form; this matches.**

**Bessel disk (row 4).** The Dirichlet BC breaks the `R⁺` dilation that would otherwise pair with `SO(2)` to form a non-abelian semidirect product; what remains is abelian `U(1)`. No integer-`n` lattice quantizes the eigenvalue beyond mode-counting (`j_{n,k}` is not an integer-lattice value of `λ`). No monodromy structure relevant to the Fuchsian sense. **Mechanisms (i), (iii), (iv) all fail. Bessel zeros are transcendental over `ℚ`.**

**`H^d` non-compact dual (row 9).** `SO(d, 1)` non-compact has no non-trivial finite-dim unitary irreps — mechanism (i) fails by compactness obstruction. No monodromy structure in the relevant sense. No accessory-parameter spectral quantization — the spectrum is the continuous-Plancherel parameter. **All three mechanisms fail; the scalar Laplacian has purely continuous spectrum.**

These are not coincidences. The law's content is precisely that closed-form ↔ one of three structural mechanisms operating at some enveloping-algebra layer. Where none operate, the spectrum is either transcendental (Bessel), continuous (`H^d`), or has no known closed-form (KY Kerr). The negative-direction confirmations make the law's predictive content sharp — it is not "always-fits-by-elasticity."

---

## §5. The compactness restriction is real (paired test)

Spike #17's `S^d` / `H^d` pairing is structurally important. Both settings live in the same Lie-group framework — rank-1 symmetric spaces `G/K`, scalar Laplace–Beltrami operator on a homogeneous Riemannian manifold, irreducible-representation decomposition of `L²(G/K)` via Plancherel / Peter–Weyl. The only difference is **compactness**: `S^d` is the compact form (`G = SO(d+1)` compact); `H^d` is the non-compact dual (`G = SO(d, 1)` non-compact). Same framework, opposite outcomes.

- **Compact (`S^d`)**: `SO(d+1)` has finite-dim unitary irreps; mechanism (i) applies; integer-`ℓ` lattice gives mechanism (iv); closed-form basis via Gegenbauer / Gel'fand–Tsetlin polynomials.
- **Non-compact (`H^d`)**: `SO(d, 1)` has only infinite-dim unitary irreps; mechanism (i) fails; no mechanism (iii) or (iv) replacement available; scalar Laplacian has purely continuous spectrum.

This is the first cleanly-paired positive/negative test in the spike series (CMS / KY Kerr was paired but on the same compact base manifold). It demonstrates the law has *sharp structural content* rather than being framing-elasticity: the compactness restriction is a *load-bearing feature of the law*, not an artifact of how it is phrased. If `H^d` admitted closed-form `L²` eigenfunctions on a discrete spectrum, mechanism (i) would need refinement. It does not, and the prediction holds.

---

## §6. The layered-mechanism finding

Spike #18 surfaced a structural clarification: mechanisms can apply at *different enveloping-algebra layers* and produce *consistent labels*. The Heisenberg + HO setting is the first instance.

At the **Heisenberg layer**: mechanism (i) genuinely fails. Stone–von Neumann uniqueness + the finite-dim trace argument together force every finite-dim unitary irrep to factor through the abelian quotient. The HO Hamiltonian, requiring `[P, Q] = Z` to act non-trivially, cannot live on any finite-dim Heisenberg irrep.

At the **metaplectic enveloping layer**: mechanism (i) recovers. The Weil representation of `Sp(2n, ℝ)` extends the Schrödinger rep, and under the maximal compact `U(n)` decomposes into finite-dim `Sym^k(ℂ^n)` irreps that label the HO eigenspaces. The same integer `k` indexes both the Heisenberg-layer number-operator eigenvalue (mechanism (iv)) and the metaplectic-layer `U(n)`-Casimir highest weight (mechanism (i)).

**The law statement does not need amendment.** What is new is recognition that mechanisms operate at any algebraic layer at which they apply; the law does not require all eligible mechanisms to act at the *same* layer. This is a clarification of how the law applies, not a refinement of what it says.

The honest-negative reading is available: if the metaplectic-`U(n)` recovery is judged as post-hoc rescue — climbing the symmetry tower until a mechanism works — then the layered phenomenon weakens the law's content. The counter is that the metaplectic extension is **canonical** rather than ad hoc: it is the unique projective unitary representation of `Sp(2n, ℝ)` extending the Schrödinger rep, forced by Stone–von Neumann uniqueness plus the obvious `Sp(2n, ℝ)` action on the underlying symplectic phase space. The `U(n)` decomposition is mathematical fact, not interpretive choice. Furthermore, not every failure of mechanism (i) admits an enveloping-layer rescue: `H^d` non-compact (row 9) does not — the conformal extension `SO(d+1, 1)` is still non-compact, with the same continuous-spectrum behavior. The layered phenomenon is selective, not universal, which is why it has structural content.

---

## §7. Connection to the project's methodology

The polynomial `y = x³ + x² + x` of §1 was the simplest possible instance. Pure algebra; pure slot; no motion until `x` takes a value. The derivative as shift operator on coefficients is purely algebraic; the integral over a slot is a value not a process. *"The math is the slot; the motion is the integral."*

The 10-setting refined law is the same idea at increasing levels of mathematical sophistication. In every case:

- The algebra encodes a finite-dimensional invariant-subspace selection — Lie-irrep label, monodromy data, accessory-parameter spectrum, integer-lattice index, character-variety orbit.
- The closed-form expression is the projection of that hidden algebraic structure into a finite arithmetic form — radicals, polynomials in special functions, Gegenbauer-along-Gel'fand–Tsetlin-chain, Hermite functions, Yablonskii–Vorobiev polynomials.
- The Lie-group / monodromy / Bäcklund structure is the **slot**; the closed-form spectrum is the **motion**.

The Antikythera-maths methodology declared at [`docs/antikythera-maths/CLAUDE.md`](../../antikythera-maths/CLAUDE.md) — *algebra → eigenbasis → projected to spatial motion* — is the same operator. The gear (per `user_stance_fiber_as_spatially_absent_encoding.md`) is the simplest mechanical instance: teeth encode `ℤ/n` algebraically; rotation projects that algebraic content outward as gear ratios and phase relationships. The MFO §VII.4.1.2 Casimir-decomposition universality `λ_total = λ_base + C₂(ρ_G) + cross-terms` is the mechanism-(i) special case — a direct realization of the law at the non-abelian-Lie-Casimir-only layer, scoped to the universal-symmetry-discovery framework of MFO.

The refined law operationalizes the user's *"hidden algebraic encoding is spatially absent"* stance. The algebra layer carries the closed-form content; the spatial / spectral / dynamical projection is what comes out when the algebraic slot is evaluated at a value. Whether the setting is a 4-singular-point Fuchsian ODE (Heun), a nonlinear isomonodromic deformation (Painlevé), a higher-dimensional PDE (`S^d` harmonics), or a non-compact non-semisimple representation (Heisenberg metaplectic), the same structural-law principle holds. **The fiber is the slot; closed form is the motion.**

---

## §8. Open questions and future spike candidates

The 10/10 score is *consistency* not *theorem*. The law remains a structural pattern across ten disparate settings, not a proved necessary-and-sufficient theorem. Several open directions:

- **Eremenko 2020 finiteness of `PSU(2)`-monodromy `q`-values for Heun.** The non-constructive bound has no explicit upper bound. Even an effective bound would strengthen mechanism (iv) at row 6.
- **General Heun finite-monodromy classification** (non-pull-back, non-Lamé). OPEN. The 61 Vidūnas–Filipuk pull-back families and the Dubrovin–Kapaev reducible-monodromy polynomial solutions cover known cases; the irreducible-finite-monodromy non-pull-back Heun classification remains absent. A Schwarz-list-style enumeration would settle row 6 completely.
- **Picard family of PVI.** Elliptic-modular lattice quantization is the most subtle (iv) instance — continuous 2-parameter family with algebraic specializations on `ℚ²`. The seed solution is literally a Lamé solution lifted to nonlinear via Riemann–Hilbert. Worth a dedicated treatment.
- **Possible mechanism (v) candidates.** Settings with *transcendental hidden structure* — modular / quasi-modular Eisenstein content (Mahler-equation hidden modular dynamics); anabelian fundamental-group / Galois-theoretic structure beyond classical differential Galois; quantum-integrable-systems TBA equations; BLLT Liouville/Nekrasov instanton sums. A future spike on any of these could refute the 4-mechanism completeness — finding a closed-form-admitting setting where none of (i), (iii), (iv) operates at any layer would constitute mechanism (v).
- **Higher-rank symmetric spaces.** `Gr(k, n)`, `U(n)`, Lie groups themselves as Riemannian manifolds — the analog of SH theory is Peter–Weyl / Plancherel; the refined law predicts closed-form via mechanism (i) extended to multi-Casimir labeling at higher rank. A natural Spike #19 target.
- **2-step nilpotent Lie groups beyond `H_n`.** Filiform Lie algebras, Carnot groups, higher-step nilpotent Lie groups — whether layered-mechanism behavior persists. The Heisenberg case is the simplest test; higher-rank nilpotent tests are open.
- **Connection to differential Galois theory and integrable-systems classification.** The refined law is *structurally* what classical differential Galois theory does for linear ODEs (Kovacic's algorithm; Picard–Vessiot extensions) and what integrability classifications do for nonlinear ODEs (Painlevé property; isomonodromic deformation). A formal-language unification of the 4-mechanism refined law with these established frameworks would convert "structural pattern across 10 settings" into "theorem about closed-form-existence."

---

## §9. Provenance and discipline

All citations in this consolidation are PDF-verified or pre-2020 canonical, drawn from the citation chains established in the five predecessor spikes. No new arXiv IDs or author orderings are introduced beyond those verified in the prior notes. Specifically:

- **Spike #14 citations** (Whittaker–Watson 1927, Erdélyi 1955, Schwarz 1873, Klein 1884, Beukers–Heckman 1989, Watson 1944, Morse–Feshbach 1953, Eisenhart 1934) are pre-2020 canonical per the `feedback_pdf_extraction_citation_discipline.md` counter-clause.
- **Spike #15 citations** (Maier 2007 `arXiv:math/0408317`; Vidūnas–Filipuk 2013 `arXiv:0910.3087`; Vidūnas–Filipuk 2014 `arXiv:1204.2730`; Eremenko 2020 `arXiv:1905.02537`; Dubrovin–Kapaev 2018 `arXiv:1809.02311`; Takemura 2004 `arXiv:math/0201208`) are PDF-verified.
- **Spike #16 citations** (Lisovyy–Tykhyy 2014 `arXiv:0809.4873`; Boalch 2006 `arXiv:math/0406281`; Boalch 2005 `arXiv:math/0308221`; Cantat–Loray 2009 `arXiv:0711.1579`; Okamoto 1987; Yablonskii 1959; Vorobiev 1965; Okamoto 1986; Umemura 1996; Noumi–Yamada 1998–2004) are PDF-verified for 2020+ and pre-2020 canonical for the rest.
- **Spike #17 citations** (Vilenkin 1968; Müller 1966; Stein–Weiss 1971; Helgason 1978, 1984; Atkinson–Han 2012; Gel'fand–Tsetlin 1950; Adams 1960; Bott–Milnor 1958; Želobenko 1973; Borthwick 2007) are pre-2020 canonical.
- **Spike #18 citations** (Stone 1932; von Neumann 1931; Mackey 1949; Weil 1964; Kirillov 1962, 1976; Howe 1980; Folland 1989; Auslander 1973) are pre-2020 canonical.
- **Gray–Kubizňák 2024** `arXiv:2401.03553` (KY Kerr abelian-tower diagnosis) was PDF-verified in Spike #11.

Per `feedback_no_lineage_claims_in_notebook.md`: no academic-lineage claims about external work; all citations are technical and result-specific. The user's own project through-line — polynomial-as-slot → gear-as-mechanism → 10-setting refined law — is the natural extension framing this consolidation is built around, scoped to the user's own intellectual arc per the carve-out at `user_stance_fiber_as_spatially_absent_encoding.md`.

Per `feedback_no_mvp_framing.md`: full-coverage consolidation of all 10 settings, all 5 spikes, all 5 mathematical domains. No subset cut.

**No shared-file edits.** This consolidation is strictly srmech-local. CHANGELOG.md, README.md, the MFO notebook, the Antikythera `pin_and_slot.py` D-H1 semantics lock, and `.gitignore` are untouched.

---
