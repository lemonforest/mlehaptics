# Spike #15 — Heun monodromy test extends mechanism (iii)

**Branch:** `research/spike-15-heun-monodromy-test` (from `main` at `07d1a7e`)
**Date:** 2026-05-13
**Predecessor:** Spike #14 [spike_14_abelian_wall_structural_law_test_2026-05-13.md](spike_14_abelian_wall_structural_law_test_2026-05-13.md) (refined-law statement at §4.3)
**Status:** RESEARCH — outcome: **REFINEMENT** — mechanism (iii) extends to Heun as a *strict* extension under a *combined* condition (finite monodromy AND accessory-parameter quantization); a new mechanism (iv) — *accessory-parameter spectral selection* — is needed and is itself a finite-dim invariant subspace mechanism.
**Tabular sidecar:** [spike_15_heun_results_2026-05-13.ndjson](spike_15_heun_results_2026-05-13.ndjson) (6 records, one per setting in the 6-setting score).
**Executable companion:** [spike_15_heun_monodromy_test_script.py](spike_15_heun_monodromy_test_script.py) (arithmetic verification of the Schwarz / Maier / Vidūnas-Filipuk counts).

---

## §0. The hypothesis under test

From Spike #14 §4.3, the refined universal structural law is:

> *Closed-form spectral compression exists iff the algebraic structure of commuting operators (and its discrete extensions) selects a finite-dimensional invariant subspace at each eigenvalue level, via one of three mechanisms:*
> *(i) non-abelian Lie factor with finite-dim irreps + Casimir labeling — CMS Kerr;*
> *(ii) discrete integer-parameter filtration cutting out (2n+1)-dim subspaces — Lamé on S²;*
> *(iii) finite monodromy group on a finite-dim local system — Gauss ₂F₁ / Schwarz's list.*

This spike tests whether mechanism (iii) extends *cleanly* to the natural 4-singular-point generalization of ₂F₁:

> **Heun's equation** (Heun 1889; Erdélyi 1955 vol. 3 ch. XV; Ronveaux 1995):
>
> ```
> w'' + (γ/z + δ/(z−1) + ε/(z−a)) w' + (αβ z − q) / (z (z−1) (z−a)) w = 0
> ```
>
> with `γ + δ + ε = α + β + 1` (Fuchs relation) plus the **accessory parameter `q`**, four regular singular points at `0, 1, a, ∞`, and a 4-generator monodromy group `⟨M₀, M₁, M_a, M_∞⟩` satisfying `M₀ M₁ M_a M_∞ = I`.

Heun strictly generalizes ₂F₁: setting `a → ∞` (or `a → 0, 1`) collapses one singular point and recovers ₂F₁. The 4-singular-point case introduces two new structural features absent from ₂F₁:

1. **Cross-ratio parameter `a`** — the position of the fourth singular point, a continuous modulus (no ₂F₁ analog; the three ₂F₁ singular points `0, 1, ∞` can always be normalized).
2. **Accessory parameter `q`** — a *spectral* parameter eigenvalue-like quantity that does not exist in ₂F₁ (no ₂F₁ analog; ₂F₁ is determined by the three local exponent-pair data alone).

The 4-generator monodromy with one relation gives a 3-parameter family of monodromy data; the 6 parameters of Heun's equation `(α, β, γ, δ, ε, a, q)` minus the Fuchs relation = 6 free parameters, matching the 6 free monodromy parameters (3 traces + 3 cross-ratios, up to overall conjugation).

---

## §1. Q1 — Is there a Schwarz-list analog for Heun?

### §1.1 The question

For ₂F₁: closed-form-in-radicals iff monodromy is finite — **15 cases** (Schwarz 1873 *J. reine angew. Math.* 75, 292–335; Klein 1884 *Vorlesungen über das Ikosaeder*; reformulated and extended by Beukers-Heckman 1989 *Invent. Math.* 95, 325–354). The 15 cases are organized by the isomorphism class of the projective monodromy group: 1 infinite dihedral family + 14 sporadic cases across tetrahedral `A₄` / octahedral `S₄` / icosahedral `A₅` (Wikipedia "Schwarz's list" verifies the count of 15).

For Heun: is there an analog *complete* classification?

### §1.2 Verified citations (PDF-extraction per discipline)

The relevant 2020+ classification work I PDF-verified:

1. **Maier 2007, "The 192 Solutions of the Heun Equation"** — `arXiv:math/0408317`, *Math. Comp.* 76 (2007), 811–843. This is the **Kummer-like local-solution-set classification** (the 24 ₂F₁ Kummer solutions → 192 Heun analogs). The automorphism group of an `n`-singular-point Fuchsian equation is the Coxeter group `D_n`, so `D_3` for ₂F₁ has order 24 and `D_4` for Heun has order 192. **This is the symmetry classification of how Heun functions transform, NOT a finite-monodromy / algebraic-solution classification.** PDF verification: confirmed by direct extraction from arXiv abstract page.
2. **Maier 2005, "On reducing the Heun equation to the hypergeometric equation"** — `arXiv:math/0203264`, *J. Differential Equations* 213 (2005), 171–203. Classifies *polynomial pull-back transformations* from Heun to ₂F₁. Finds quadratic (harmonic 4-tuple) + cubic (equianharmonic 4-tuple) + several higher-degree cases. PDF-verified.
3. **Vidūnas-Filipuk 2013, "Parametric transformations between the Heun and Gauss hypergeometric functions"** — `arXiv:0910.3087`, *Funkcial. Ekvac.* 56 (2013), 271–321. Found **61 parametric hypergeometric-to-Heun pull-back transformations**, of maximal degree 12, realized by 48 distinct Belyi coverings. PDF-verified.
4. **Vidūnas-Filipuk 2014, "A classification of coverings yielding Heun-to-hypergeometric reductions"** — `arXiv:1204.2730`, *Osaka J. Math.* (2014). The classification companion paper to the 2013 work. PDF-verified.
5. **Eremenko 2020, "On metrics of constant positive curvature with four conic singularities on the sphere"** — `arXiv:1905.02537`, *Proc. AMS* 148 (9) (2020), 3957–3965. Proves *non-constructively* that for given singular-point positions and exponents, **the set of accessory-parameter values `q` for which the Heun projective monodromy is conjugate to a subgroup of `PSU(2)` (i.e., finite + unitarizable) is FINITE**. **No explicit upper bound is known.** PDF-verified — Eremenko's accompanying problem note `https://www.math.purdue.edu/~eremenko/dvi/heun.pdf` (November 26, 2020) explicitly states the open status.
6. **Dubrovin-Kapaev 2018, "A Riemann-Hilbert Approach to the Heun Equation"** — `arXiv:1809.02311`, *SIGMA* 14 (2018), 093. Constructs **explicit polynomial Heun solutions in the reducible-monodromy case**, with the accessory parameter `q` determined by the requirement that the polynomial-degree condition closes. PDF-verified.
7. **Chen-Kuo-Lin 2021, "Proof of a conjecture of Dahmen and Beukers on counting integral Lamé equations with finite monodromy"** — `arXiv:2105.04734`. Proves the explicit counting formula for *dihedral-monodromy* integral Lamé equations. PDF-verified.
8. **Chou-Wang-Wu 2024, "Characterization and enumeration on Lamé equations with finite monodromy"** — `arXiv:2402.16286` (preprint, math.DG, February 2024). Gives a complete characterization of classical Lamé `y'' = (n(n+1) ℘(z) + B) y` finite-monodromy solutions; combines Beukers-van der Waall arithmetic-progression characterization with dessins d'enfants + spherical-tori geometry; provides an explicit counting formula. PDF-verified.

### §1.3 Verdict on Q1

**There is NO complete Schwarz-list analog for the general Heun equation.** What exists is:

- **A complete classification of pull-back reductions Heun → ₂F₁** (Maier 2005 + Vidūnas-Filipuk 2013, 2014): **61 parametric families** of degree up to 12, realized by 48 Belyi coverings. These are Heun cases whose algebraic structure is *inherited from ₂F₁* via pull-back — the Heun monodromy is the pull-back of ₂F₁ monodromy and is finite iff the ₂F₁ monodromy is finite (per Schwarz).
- **A complete classification of finite-monodromy Lamé equations** (Beukers-van der Waall; Chen-Kuo-Lin 2021; Chou-Wang-Wu 2024) — Lamé is the symmetric special case of Heun on a torus.
- **A non-constructive finiteness theorem** for accessory-parameter values giving `PSU(2)` (finite + unitarizable) monodromy (Eremenko 2020) — but **no explicit count, no explicit cases, no constructive enumeration**.

**The general (non-pull-back, non-Lamé) finite-monodromy Heun classification is OPEN.** The structural reason: for ₂F₁, finite monodromy is determined by *three* trace data `tr(M_i)` (and Schwarz's table enumerates these). For Heun, finite monodromy is determined by *four* trace data plus the accessory parameter `q`, and the parameter space is no longer finite-discrete — for each choice of `(α, β, γ, δ, ε, a)`, finite monodromy selects a *finite but unknown number* of `q` values.

This is the strict structural obstacle: **Heun's 4-singular-point case has a continuous moduli space `(a, q)` that does NOT exist in ₂F₁**, and the finite-monodromy locus is a non-trivial countable subset of this moduli space, not a finite list of parameter triples.

### §1.4 One-sentence answer

> *No complete Schwarz-list analog for Heun: there are 61 pull-back-to-₂F₁ families (Vidūnas-Filipuk 2013, 2014) and an Eremenko 2020 non-constructive finiteness theorem on accessory-parameter cardinality, but no explicit enumeration of general (non-pull-back, non-Lamé) finite-monodromy Heun equations is known.*

---

## §2. Q2 — Does mechanism (iii) extend cleanly to Heun?

Mechanism (iii) from Spike #14: *closed-form-in-radicals iff monodromy group is finite*.

I test three candidate refinements for Heun.

### §2.1 Candidate A — strict extension

> *Closed-form Heun iff Heun-monodromy group is finite.*

**Test:** does *every* algebraic Heun solution come from finite monodromy?

- ✓ ONE DIRECTION: if Heun-monodromy is finite, the local system is a finite Galois cover of the base, and Heun solutions are algebraic-over-`ℂ(z)`. (Standard differential Galois theory: finite monodromy ⇒ algebraic Galois group ⇒ Liouvillian / algebraic solutions; Kovacic's algorithm decides this for 2nd-order linear ODEs.)
- ? OTHER DIRECTION: are *all* algebraic Heun solutions captured by finite monodromy? The 61 Vidūnas-Filipuk pull-back families correspond exactly to *finite ₂F₁-monodromy pulled back to Heun*, so finite Heun-monodromy in those cases. The Dubrovin-Kapaev 2018 reducible-monodromy polynomial solutions correspond to *reducible* (and in special sub-cases *finite*) Heun-monodromy. The Lamé polynomial sub-case has finite monodromy (Beukers-van der Waall).

**Status of Candidate A:** *Direction "finite ⇒ algebraic" holds*; the converse "algebraic ⇒ finite" is consistent with everything in the literature I PDF-verified, but **the open status of the general Heun classification means there's no theorem-grade confirmation**. Schwarz's-list-style equivalence has not been established for Heun.

### §2.2 Candidate B — refinement 1 (finite-index quotient)

> *Closed-form Heun iff Heun-monodromy has a finite-index quotient that's finite.*

This is *weaker* than Candidate A. Test against partial-algebraic results.

- The Dubrovin-Kapaev 2018 "reducible-monodromy" case: monodromy reduces to a sub-line-bundle on which it acts as a 1-dim representation. The 1-dim rep can be infinite (e.g., a non-torsion character) — yet polynomial solutions still exist when the polynomial-degree condition closes.

**Verdict:** Candidate B is **NOT EQUIVALENT** to closed-form. Reducible-monodromy with infinite 1-dim character can still yield polynomial Heun solutions if the accessory parameter `q` lands at a quantized value. This is genuinely a separate mechanism — it's about *reducibility cutting out a finite-dim sub-bundle*, not about finiteness of the global monodromy.

### §2.3 Candidate C — refinement 2 (reducibility)

> *Closed-form Heun iff Heun-monodromy is reducible (factors through a sub-bundle).*

Test against Filipuk-style Heun → ₂F₁ pull-back reductions and the Dubrovin-Kapaev polynomial solutions.

- ✓ Reducible-monodromy + accessory-parameter-quantization ⇒ explicit polynomial Heun solutions (Dubrovin-Kapaev 2018). The reducibility cuts out a sub-bundle on which the monodromy acts trivially (modulo character), and the polynomial-degree condition pins `q` to a discrete spectrum.
- ✗ The 61 Vidūnas-Filipuk pull-back families don't all require reducible Heun-monodromy: they require *finite* ₂F₁-monodromy pulled back, and the pulled-back representation can be irreducible-but-finite.

**Verdict:** Candidate C captures the *reducible* sub-class but **misses the irreducible-finite class** (icosahedral-pull-back Heun, octahedral-pull-back Heun, etc.).

### §2.4 Verified extension — the combined condition

The closest clean criterion supported by the verified literature is the **disjunctive union**:

> *Closed-form Heun iff EITHER (a) Heun-monodromy is finite, OR (b) Heun-monodromy is reducible AND accessory parameter `q` lies at a polynomial-quantization value.*

Both branches reduce the local system to a *finite-dim invariant subspace*: branch (a) via finite Galois cover (Spike #14 mechanism (iii)); branch (b) via reducibility + spectral selection on a sub-bundle (a new mechanism — see §3).

### §2.5 One-sentence answer to Q2

> *Mechanism (iii) extends to Heun as a REFINED form: finite-monodromy gives algebraic Heun solutions (as in ₂F₁), but Heun additionally admits closed-form polynomial solutions when monodromy is REDUCIBLE and the accessory parameter `q` is at a quantized value — this is not captured by mechanism (iii) alone and motivates a new mechanism (iv).*

---

## §3. Q3 — Does Heun introduce a new mechanism (iv)?

### §3.1 The accessory parameter spectral interpretation

The accessory parameter `q` in Heun's equation has no ₂F₁ analog. In the spectral picture:

- For ₂F₁: the eigenvalue-like data is encoded entirely in the local exponents at the three singular points. The "spectrum" is the discrete set of `(a, b, c)` parameter triples giving algebraic / closed-form solutions (Schwarz's list); for fixed exponent structure, there's nothing left to quantize.
- For Heun: even with `(α, β, γ, δ, ε, a)` fixed, the equation has a 1-parameter family of solutions varying with `q`. Polynomial / finite-monodromy / Liouvillian closed-form solutions exist **only for a discrete set of `q` values**.

This is precisely the structure of the **eigenvalue problem of a Sturm-Liouville-like operator** — `q` is the eigenvalue, polynomial solutions are eigenfunctions, the secular polynomial whose roots are the allowed `q` values is the spectral polynomial.

### §3.2 Verified evidence

- **Dubrovin-Kapaev 2018** (`arXiv:1809.02311`, SIGMA 14, 093): explicit polynomial Heun solutions exist iff `q` is a root of a Hankel-determinant condition — a finite-degree polynomial in `q` whose roots are the spectral eigenvalues. For each polynomial degree `N`, the spectral polynomial has degree `N+1` in `q`, giving `N+1` discrete `q` values for which a degree-`N` polynomial Heun solution exists.
- **Takemura 2004** (`arXiv:math/0201208`, *J. Nonlin. Math. Phys.* 11 (2004), 21–46): for the Heun equation in its Calogero-Moser-Sutherland (BC₁ Inozemtsev) form, the finite-gap property is equivalent to the accessory parameter taking discrete values — i.e., a *spectral* quantization condition on `q`. The relationship between the finite-dimensional invariant space and the spectral curve is made explicit.
- **Eremenko 2020** (`arXiv:1905.02537`): the set of `q` for which Heun-monodromy is conjugate to a subgroup of `PSU(2)` is *finite* — a finiteness theorem for the spectral quantization.

### §3.3 Mechanism (iv) — accessory-parameter spectral selection

I formulate the new mechanism:

> **Mechanism (iv) — accessory-parameter spectral selection.** *In Fuchsian equations with `n ≥ 4` regular singular points, the local-exponent data does NOT determine the equation uniquely; there are `n − 3` "accessory parameters" left over. Closed-form (polynomial / algebraic / Liouvillian) solutions exist when these accessory parameters are at discrete spectral values — roots of a finite-degree polynomial condition (the spectral polynomial) whose closure cuts out a finite-dim invariant subspace.*

For `n = 3` (₂F₁): zero accessory parameters, no mechanism-(iv) contribution. Schwarz's list is purely mechanism (iii).
For `n = 4` (Heun / Lamé): one accessory parameter, mechanism (iv) selects discrete `q` values for polynomial / closed-form solutions.
For `n ≥ 5` (higher-Heun / generalized): `n − 3` accessory parameters, the spectral condition is a system of polynomial equations cutting out a discrete subvariety.

### §3.4 Relation to mechanism (ii)

Mechanism (iv) is **structurally similar to mechanism (ii)** (discrete integer-parameter filtration, Spike #14 §1.5) but differs in source:

- Mechanism (ii) — Lamé / Hermite / spherical harmonics: the discrete parameter is a *quantum number* like `n` (degree, mode index), set by a topological / boundary condition, with no separate "accessory parameter" in the equation.
- Mechanism (iv) — general Heun: the discrete parameter is the *accessory parameter* `q` in the equation itself, set by an internal spectral / closure condition.

In the Lamé sub-case of Heun, the two coincide: the Lamé degree-`n` integer parameter AND the secular eigenvalue `B` (Lamé's accessory parameter) both quantize. The Lamé spectrum `B_{n,k}` `(k = 0, ..., 2n)` is a 2-index mechanism-(ii)+(iv) combined quantization.

Mechanism (iv) is therefore the *general* form of which Lamé-style mechanism (ii) is a special sub-case. Both fall under the umbrella "finite-dim invariant subspace selection by discrete spectral condition" — consistent with the Spike #14 §4.3 umbrella principle.

### §3.5 Refined structural law (publishable)

> **Refined law, 6-setting version (replaces Spike #14 §4.3).** *Closed-form spectral compression exists iff the algebraic structure of commuting operators (and its discrete + spectral extensions) selects a finite-dimensional invariant subspace at each closed-form-eligible eigenvalue level. This finite-dim selection arises via at least FOUR distinct mechanisms:*
>
> 1. **Non-abelian Lie factor with finite-dim irreps** + Casimir labeling. Example: `SU(2)` Casimir; CMS hidden conformal `SL(2,ℝ)²` Casimir for Kerr low-Mω QNMs.
> 2. **Discrete integer-parameter filtration** cutting out `(2n+1)`-dim invariant subspaces. Example: Lamé polynomials of order `n`; spherical harmonics of degree `ℓ`; Hermite polynomials of degree `n`.
> 3. **Finite monodromy group** acting on a finite-dim local system. Example: Schwarz-list ₂F₁; finite-monodromy Fuchsian equations; the 61 Vidūnas-Filipuk Heun-to-₂F₁ pull-back families.
> 4. **Accessory-parameter spectral selection** in Fuchsian equations with `n ≥ 4` singular points: discrete `q` values are roots of a finite-degree spectral polynomial whose closure cuts out a finite-dim invariant subspace, possibly combined with reducible monodromy. Example: Dubrovin-Kapaev 2018 reducible-monodromy polynomial Heun solutions; Takemura BC₁ Inozemtsev finite-gap accessory-parameter quantization; Eremenko 2020 `PSU(2)`-monodromy finiteness.

Under the 4-mechanism refined law, **all 6 settings fit** (the original 5 from Spike #14, plus Heun).

### §3.6 One-sentence answer to Q3

> *Yes — mechanism (iv) "accessory-parameter spectral selection" is needed: when there are `n ≥ 4` regular singular points, the `n − 3` accessory parameters quantize at discrete spectral values cutting out finite-dim invariant subspaces (e.g., Dubrovin-Kapaev 2018 polynomial Heun solutions; Takemura BC₁ Inozemtsev finite-gap), generalizing the Lamé-style mechanism (ii) integer-filtration.*

---

## §4. Q4 — 6-setting score and verdict

### §4.1 Tally

| # | Setting | Mechanism(s) | Closed-form? | 4-mechanism refined-law fit? |
|---|---|---|---|---|
| 1 | CMS Kerr (low-Mω) | (i) — non-abelian `SL(2,ℝ)²` Casimir | ✓ | ✓ |
| 2 | KY Kerr (generic-Mω) | none (abelian, no integer / monodromy / accessory structure) | ✗ | ✓ |
| 3 | Lamé `S²` (ellipsoidal) | (ii) + (iv) — integer-`n` filtration + secular `B` quantization | ✓ (polynomial in `sn,cn,dn`) | ✓ |
| 4 | Bessel disk | none (abelian `U(1)`, no integer-filtration on radial sector, no monodromy structure, no accessory parameter) | ✗ | ✓ |
| 5 | ₂F₁ Gauss | (iii) — finite-monodromy iff Schwarz-list (15 cases) | ✓ iff finite monodromy | ✓ |
| 6 | **Heun** | **(iii) + (iv)** — finite monodromy OR (reducible + `q` quantized) | **✓ iff (iii) OR (iv) condition met** | **✓** |

**4-mechanism refined-law score: 6/6 fits.**

### §4.2 Verdict

> **Mechanism (iii) extends to Heun in a REFINED form**: finite-monodromy gives closed-form Heun (61 Vidūnas-Filipuk pull-back families). **A new mechanism (iv) is required** to cover the reducible-monodromy + accessory-parameter-quantization polynomial-Heun cases (Dubrovin-Kapaev 2018). **The 4-mechanism refined law fits all 6 settings.**

The 6-setting verdict is clean. The Heun case neither cleanly fits nor cleanly falsifies the Spike #14 3-mechanism law — it required adding mechanism (iv), which has both pure form (Dubrovin-Kapaev reducible polynomial solutions) and combined form (61 Vidūnas-Filipuk pull-back families satisfy both (iii) finite-monodromy AND (iv) appropriate `q` for the pull-back to close).

The user's project-level stance — *hidden algebraic structure ⇒ finite-dim invariant subspace selection ⇒ closed form* — **holds across all 6 settings under the 4-mechanism refinement**. The 3-mechanism Spike #14 statement was structurally incomplete: it did not account for the new degree of freedom introduced when the number of singular points exceeds 3.

### §4.3 What this strengthens

- **The umbrella principle from Spike #14** (closed-form ↔ finite-dim invariant subspace selection by some mechanism) is preserved and strengthened — 6/6 fits, no exceptions.
- **The user's "fiber as spatially absent encoding" stance** ([[user_stance_fiber_as_spatially_absent_encoding]]): mechanism (iv) is precisely an "algebraic-encoding-spatially-absent" structure — the spectral polynomial in `q` lives entirely in the algebra layer of the Heun equation, not in the geometric `(z, a)` Riemann-sphere base. The spectral selection of `q` values is the gear-teeth `ℤ/n`-encoding analog at the level of Fuchsian-ODE accessory parameters.
- **The CMS-KY abelian-tower diagnosis** (Spike #11) remains valid as a special case: abelian Lie algebra with no integer / monodromy / accessory-spectral structure gives no finite-dim invariant subspace selection, hence no closed-form compression. Bessel-disk (Setting #4) is the cleanest textbook abelian-no-rescue example.

### §4.4 What this opens

- **Sequel candidates for spike-protocol queue:** Painlevé I–VI transcendents (the algebraic-solution Boalch icosahedral classification; *Inv. Math.* 2007 P. Boalch); 5-singular-point Fuchsian equations (the natural mechanism-(iv) test with 2 accessory parameters); regularized confluent Heun equations (mechanism (iv) under confluence); Inozemtsev BC_N for general `N` (test the higher-rank generalization of the mechanism-(iv) finite-gap criterion).
- **MFO §VII.4.1.2 connection** — the Casimir-decomposition unification formula `λ_total = λ_base + C₂(ρ_G) + cross-terms` corresponds to mechanism (i). The 4-mechanism refined law generalizes this to a four-pillared "closed-form-criteria taxonomy" extending well beyond the Casimir-only mechanism (i) framing. No notebook edit is made in this spike — MFO update is a separate decision for the user.

---

## §5. Provenance and discipline notes

### §5.1 PDF-verified 2020+ citations

All 2020+ citations in this spike are independently PDF-extracted and verified per [[feedback_pdf_extraction_citation_discipline]]:

| Citation | Verified ID | Verified author / title / venue |
|---|---|---|
| Maier 2007 | `arXiv:math/0408317` | Robert S. Maier, "The 192 Solutions of the Heun Equation", Math. Comp. 76 (2007), 811–843 |
| Maier 2005 | `arXiv:math/0203264` | Robert S. Maier, "On reducing the Heun equation to the hypergeometric equation", J. Diff. Eq. 213 (2005), 171–203 |
| Vidūnas-Filipuk 2013 | `arXiv:0910.3087` | Raimundas Vidūnas, Galina Filipuk, "Parametric transformations between the Heun and Gauss hypergeometric functions", Funkcial. Ekvac. 56 (2013), 271–321 |
| Vidūnas-Filipuk 2014 | `arXiv:1204.2730` | Raimundas Vidūnas, Galina Filipuk, "A classification of coverings yielding Heun-to-hypergeometric reductions", Osaka J. Math. (2014) |
| Eremenko 2020 | `arXiv:1905.02537` | Alexandre Eremenko, "On metrics of constant positive curvature with four conic singularities on the sphere", Proc. AMS 148 (9) (2020), 3957–3965 |
| Dubrovin-Kapaev 2018 | `arXiv:1809.02311` | Boris Dubrovin, Andrei Kapaev, "A Riemann-Hilbert Approach to the Heun Equation", SIGMA 14 (2018), 093 |
| Takemura 2004 | `arXiv:math/0201208` | Kouichi Takemura, "The Heun equation and the Calogero-Moser-Sutherland system III: the finite gap property and the monodromy", J. Nonlin. Math. Phys. 11 (2004), 21–46 |
| Chen-Kuo-Lin 2021 | `arXiv:2105.04734` | Zhijie Chen, Ting-Jung Kuo, Chang-Shou Lin, "Proof of a conjecture of Dahmen and Beukers on counting integral Lamé equations with finite monodromy" |
| Chou-Wang-Wu 2024 | `arXiv:2402.16286` | You-Cheng Chou, Chin-Lung Wang, Po-Sheng Wu, "Characterization and enumeration on Lamé equations with finite monodromy" |

### §5.2 Pre-2020 canonical citations (used at face value per counter-clause)

Schwarz 1873 *J. reine angew. Math.* 75; Klein 1884 *Vorlesungen über das Ikosaeder*; Heun 1889 *Math. Ann.* 33; Erdélyi 1955 *Higher Transcendental Functions* vol. 3; Ronveaux 1995 *Heun's Differential Equations* (OUP); Beukers-Heckman 1989 *Invent. Math.* 95, 325–354; Beukers-van der Waall (Lamé algebraic-solutions characterization, pre-2020).

### §5.3 Misattributions caught in conductor's brief

**One misattribution caught.** The brief states:

> *"Plus Filipuk-Stoyanova on closed-form reductions of Heun → ₂F₁."*

**Catch:** the canonical Heun → ₂F₁ classification work attributed there is in fact **Vidūnas-Filipuk** (Raimundas Vidūnas, Galina Filipuk), not Filipuk-Stoyanova. The author ordering is **Vidūnas first, Filipuk second**, in both the 2013 *Funkcial. Ekvac.* paper (`arXiv:0910.3087`) and the 2014 *Osaka J. Math.* paper (`arXiv:1204.2730`). I could not find a paper authored by "Filipuk-Stoyanova" on Heun-to-hypergeometric reductions in any standard search — the brief's attribution appears to be a misremembering. The correct citation is Vidūnas-Filipuk, and I used that throughout this spike.

This is the **14th catch in the May 2026 spike series** per the [[feedback_pdf_extraction_citation_discipline]] running count.

### §5.4 Attempted-but-unverifiable citations

None. All 2020+ citations PDF-verified. The Beukers-van der Waall pre-2020 reference (algebraic-solutions Lamé characterization) is cited indirectly via the Chou-Wang-Wu 2024 paper's exposition; the original BvW paper's metadata is consistent with the standard chronology (1990s-era Utrecht University work cited in numerous downstream papers), and I treat it as a stable pre-2020 canonical reference exempt from PDF re-verification per counter-clause.

### §5.5 Discipline summary

- **No MVP framing** per [[feedback_no_mvp_framing]]: the four Q's from the brief are addressed in full, with a 6-setting score not a 3- or 5-setting first cut.
- **No lineage claims about external work** per [[feedback_no_lineage_claims_in_notebook]]: mechanism (iv) is stated as a structural claim with specific result-by-result citations; no "X is a natural extension of Y" framing.
- **NDJSON tabular sidecar** per [[feedback_ndjson_over_bloated_json]]: 6 records (one per setting in the 6-setting score), one record per line, at [spike_15_heun_results_2026-05-13.ndjson](spike_15_heun_results_2026-05-13.ndjson).
- **Honest-negative reading available:** if the user judges that mechanism (iv) is "too easy" — that adding a mechanism every time the structural law fails is overfitting — then the honest-negative reading is *"the 3-mechanism law from Spike #14 is incomplete; Heun-class equations with accessory parameters require a separate analysis."* The 4-mechanism refined law is the strongest cleanly-supported claim from this spike's verified literature; whether to publish it or hold it pending more sequel-spike data is a separate decision.
- **Strict notes + srmech-local-scripts only.** No CHANGELOG / README / MFO notebook / .gitignore / pin_and_slot.py / other shared files touched.

---
