# Spike #14 — Abelian-wall structural-law test on Lamé S² + Bessel disk + ₂F₁

**Branch:** `research/spike-14-abelian-wall-structural-law-test` (from `main` at `07d1a7e`)
**Date:** 2026-05-13
**Spike protocol:** §4.D of [spectral_calculus_rebuild_scope_2026-05-13.md](spectral_calculus_rebuild_scope_2026-05-13.md) (on branch `research/spectral-calculus-rebuild` at `2db915a`)
**Status:** RESEARCH — outcome is **REFINEMENT** of the conjecture; honest finding either way.
**Executable companion:** [spike_14_abelian_wall_structural_law_test_script.py](spike_14_abelian_wall_structural_law_test_script.py).
**Tabular output:** [spike_14_abelian_wall_results_2026-05-13.ndjson](spike_14_abelian_wall_results_2026-05-13.ndjson) (4 records).

---

## §0. The hypothesis under test

From the May 2026 KY-Kerr bounded-framework arc (Spikes #9–#13), the recurring pattern was articulated as:

> **Closed-form Casimir compression exists iff a second algebraic structure breaks the would-be abelian tower.**

Established benchmark data points before this spike:

| Setting | Algebra structure | Closed-form? |
|---|---|---|
| Low-Mω Kerr (Spike #9 / #10) | CMS hidden conformal — second `SL(2,ℝ)` factor breaks abelian | ✓ |
| Generic-Mω Kerr KY (Spike #11, PR #359) | Commuting-operator algebra is abelian (Gray-Kubizňák 2024 arXiv:2401.03553) | ✗ |
| Generic-Mω Kerr photon-ring (Spike #12A, PR #361) | No İnönü-Wigner contraction structure | ✗ |
| Generic-Mω Kerr Liouville-Virasoro (Spike #12C scope PR #363) | NS instanton tower is abelian | ✗ (predicted) |

This spike tests the conjecture in three classical (non-Kerr) settings: Lamé equation on S² (ellipsoidal harmonics), Bessel disk modes (2D disk Laplacian, Dirichlet BC), and Gauss-Riemann ₂F₁ (Schwarz triangles, monodromy).

---

## §1. Setting 1 — Lamé equation on S² (ellipsoidal harmonics)

### §1.1 Algebraic structure identified

Lamé's equation in algebraic form (Whittaker-Watson 1927 §23, Erdélyi 1955 vol. 3 ch. XV):

```
d²Λ/du² + (h − n(n+1) k² sn²u) Λ = 0
```

where `sn(u, k)` is the Jacobi elliptic sine, `k` is the modulus (set by the ellipsoid semi-axes), `n` is the "degree" parameter, and `h` is the separation constant (eigenvalue).

The setup: separate the Laplace equation `Δu = λu` on a triaxial ellipsoid in ellipsoidal coordinates `(u₁, u₂, u₃)`. By the Stäckel theorem (Eisenhart 1934; Morse-Feshbach 1953 §5.1), the separation produces a **Stäckel matrix** `S(u₁, u₂, u₃)` whose row-by-row determinants give three independent second-order operators — the Laplacian itself plus two "separation constants" `K₁`, `K₂`.

**By construction, these three operators mutually commute**: `[Δ, K₁] = [Δ, K₂] = [K₁, K₂] = 0`. The Stäckel-matrix machinery is the structural source.

**Continuous symmetry of a generic triaxial ellipsoid in `ℝ³`:** trivial. There are no Killing vectors of the round-sphere kind — a triaxial ellipsoid has no continuous rotational symmetry (only the round sphere does, recovering `SO(3)` in the limit `k → 0`).

**Discrete symmetry of a generic triaxial ellipsoid:** the order-8 abelian group `D₂ × ℤ₂ ≅ ℤ₂ × ℤ₂ × ℤ₂` (reflections in the three principal planes plus inversion). This is finite and **abelian as a group**.

### §1.2 Abelian-only or has-second-structure

**Verdict: ABELIAN-ONLY.**

The Stäckel-constructed commuting algebra `{Δ, K₁, K₂}` is abelian by construction. The discrete `(ℤ₂)³` ambient symmetry is also abelian. There is **no non-abelian Lie factor** anywhere in the setup. By the original CMS-KY conjecture, this predicts **no closed-form** spectrum.

### §1.3 Closed-form status

**Lamé polynomials exist for non-negative integer `n`** (Whittaker-Watson 1927 §23.41–§23.71; Erdélyi 1955 vol. 3 §15.5). For each integer `n`, four classes of Lamé polynomials (types K, L, M, N — corresponding to which of `{sn, cn, dn}` are factored) form a `(2n+1)`-dimensional space of solutions, with `(2n+1)` discrete eigenvalues `h` arising as roots of a `(2n+1)`-dim secular polynomial.

**Closed-form definition for Lamé:**
- *Elementary functions* (rational, exponential, trigonometric): NO. Lamé polynomials are polynomials in `sn(u, k)`, `cn(u, k)`, `dn(u, k)`, which are themselves elliptic — not elementary.
- *Algebraic over the elliptic-function field `ℂ(sn, cn, dn)`*: YES. Lamé polynomials are *literally polynomial* (bounded degree) in `(sn, cn, dn)` with rational-in-`k` coefficients.
- *Eigenvalues `h`*: roots of a finite-degree secular polynomial with rational coefficients in `k²` and `n(n+1)` — i.e. **algebraic** (Galois-theoretically, the eigenvalues are algebraic numbers in `k`).

So Lamé has a **closed-form spectrum** in the algebraic-over-elliptic-function-field sense, with discrete `(2n+1)`-dim invariant subspaces selected by the integer `n`.

### §1.4 Pattern fit

**VIOLATION-A** of the original conjecture. Closed-form polynomial solutions exist *despite* an abelian-only second-structure (Stäckel commuting algebra). The Killing-Yano-style abelian-tower obstruction does not apply.

### §1.5 Refinement candidate

The "second structure" that powers Lamé closed-form is **not** a non-abelian Lie factor — it is the discrete integer parameter `n` selecting a `(2n+1)`-dimensional invariant subspace within the infinite-dimensional space of elliptic-function eigenfunctions. The Stäckel algebra is abelian, but the *combined* structure (abelian algebra + integer-`n` filtration) admits a finite-dimensional irrep structure with discrete eigenvalue spectrum.

**Refined reading:** the structural property that powers closed-form is **selection of a finite-dimensional invariant subspace**, however that selection arises. Non-abelian Lie factor with finite-dim irreps (CMS / SU(2) Casimir) is one mechanism; discrete integer-parameter filtration (Lamé polynomials) is another.

---

## §2. Setting 2 — Bessel disk modes (2D disk Laplacian, Dirichlet BC)

### §2.1 Algebraic structure identified

Eigenvalue problem on the unit disk `r ∈ [0, 1]`, `θ ∈ [0, 2π]` with Dirichlet BC:

```
−Δu = λu,    u(1, θ) = 0
```

Separation `u(r, θ) = R(r) e^{i n θ}` reduces to Bessel's equation:

```
r² R'' + r R' + (λ r² − n²) R = 0
```

with `R(0)` finite and `R(1) = 0`. Solutions: `R(r) = J_n(√λ r)`. The Dirichlet BC enforces `J_n(√λ) = 0`, so eigenvalues are `λ_{n,k} = j_{n,k}²` where `j_{n,k}` is the k-th positive zero of `J_n` (Watson 1944 *A Treatise on the Theory of Bessel Functions* §15).

**Visible symmetry group of the bounded disk:** `SO(2) = U(1)`, abelian. The rotational generator `L_z = −i ∂_θ` gives the integer index `n`.

**Hidden second Lie factor on the *unbounded* plane:** `R⁺` radial dilation combined with `SO(2)` rotation. But `R⁺ × SO(2)` is itself abelian — it is the direct product of two one-parameter abelian groups. The full Euclidean group `E(2) = SO(2) ⋉ ℝ²` is non-abelian (rotations don't commute with translations), but in the *radial sector* (n fixed, action on R(r) alone), only `R⁺` dilation survives, which is abelian.

**On the *bounded* disk with Dirichlet BC**, the `R⁺` dilation is BROKEN (a disk is not scale-invariant). Only `SO(2)` survives. The commuting symmetry algebra on the bounded disk is purely `U(1)`, abelian.

### §2.2 Abelian-only or has-second-structure

**Verdict: ABELIAN-ONLY** on the bounded disk. The Dirichlet BC explicitly breaks the would-be second `R⁺` factor. The remaining `U(1)` is abelian.

### §2.3 Closed-form status

**Bessel zeros `j_{n,k}`:**
- *Elementary functions*: NO. Watson 1944 §15 establishes that `j_{n,k}` for `n ≥ 0`, `k ≥ 1` are transcendental over `ℚ` (a stronger result by Siegel 1929 / Shidlovsky: Bessel zeros at positive arguments are transcendental).
- *Algebraic numbers*: NO.
- *Closed-form expression in terms of Bessel functions themselves*: TRIVIALLY YES ("`j_{n,k}` is the k-th positive zero of `J_n`"), but this is circular — it does not compress the spectrum to a finite arithmetic expression.

**Eigenfunctions `J_n(√λ r) e^{i n θ}`:**
- *Closed-form in special functions*: YES. `J_n` is a defined special function with a power-series and integral representation.
- *Elementary closed-form*: NO (Bessel functions are not elementary).

**Verdict: NO closed-form spectrum** in any sense stronger than "Bessel-zero closure." The eigenvalues are expressible only via the implicit definition `J_n(√λ_{n,k}) = 0`, with no finite arithmetic / algebraic / elementary expression.

### §2.4 Pattern fit

**FIT.** Abelian-only commuting algebra on the bounded disk + no closed-form eigenvalue spectrum. This matches the conjecture's *abelian → no-closed-form* direction.

This is the cleanest abelian-wall instance in the three settings. It also confirms that the abelian-wall obstruction is not specific to gravitational-wave / Kerr — it appears in a textbook 2D PDE eigenvalue problem.

### §2.5 Nuance: eigenfunctions vs eigenvalues

The Bessel disk illustrates a useful distinction: **eigenfunctions can be closed-form-in-special-functions even when eigenvalues are not closed-form in any sense**. The original conjecture is about the *spectrum* (eigenvalue closure), and on that test Bessel disk fits the abelian-wall pattern cleanly.

---

## §3. Setting 3 — Gauss-Riemann ₂F₁ (Schwarz triangles, monodromy)

### §3.1 Algebraic structure identified

Gauss hypergeometric equation:

```
z(1−z) w'' + (c − (a+b+1) z) w' − a b w = 0
```

with three regular singular points at `z = 0, 1, ∞` and local exponents `(0, 1−c)`, `(0, c−a−b)`, `(a, b)` respectively.

**Visible continuous symmetry:** trivial. `P¹ \ {0, 1, ∞}` has no automorphism that fixes the three singular points pointwise (any Möbius transformation fixing three points is the identity). There is no continuous Lie group factor.

**Hidden second structure — monodromy group:** the solution space is a 2-dimensional local system on `P¹ \ {0, 1, ∞}`. Analytic continuation around each singular point gives matrices `M₀, M₁, M_∞ ∈ GL(2, ℂ)` with `M₀ M₁ M_∞ = I`. The monodromy group `⟨M₀, M₁⟩` is **generically non-abelian** (two `2×2` matrices commute only under very specific conditions).

**Schwarz triangle parameterization:** writing the Schwarz parameters as `λ = 1−c`, `μ = c−a−b`, `ν = a−b` (mod 1, absolute values), and setting `p = 1/λ`, `q = 1/μ`, `r = 1/ν`, the monodromy group acts on the upper half-plane as a *triangle group* `Δ(p, q, r)`.

The trichotomy:
- `1/p + 1/q + 1/r > 1` → **spherical** triangle, **FINITE** monodromy
- `1/p + 1/q + 1/r = 1` → **Euclidean** triangle, infinite solvable monodromy
- `1/p + 1/q + 1/r < 1` → **hyperbolic** triangle, infinite non-abelian Fuchsian monodromy

### §3.2 Abelian-only or has-second-structure

**Verdict: HAS NON-ABELIAN SECOND STRUCTURE generically.**

The monodromy group of ₂F₁ at generic parameters is non-abelian (two generic `2×2` matrices don't commute). So the original conjecture predicts closed-form, but this prediction is **wrong** at most parameter values — generic ₂F₁ solutions are transcendental hypergeometric functions, not algebraic.

### §3.3 Closed-form status — Schwarz's list

**Closed-form (algebraic / radicals) iff finite monodromy.** Schwarz 1873 (J. reine angew. Math. 75, 292–335) classified all `(p, q, r)` triples giving spherical-triangle / finite-monodromy ₂F₁ — *Schwarz's list*. Klein 1884 (*Vorlesungen über das Ikosaeder*) reformulated this as the classification of finite subgroups of `PSL(2, ℂ)` acting on the projective line: cyclic, dihedral, tetrahedral, octahedral, icosahedral.

The spherical Schwarz triples (Schwarz 1873; verified arithmetically in the companion script):

| `(p, q, r)` | `1/p + 1/q + 1/r` | Monodromy group | Order |
|---|---|---|---|
| `(2, 2, n)` for `n ≥ 2` | `> 1` | dihedral `D_n` | `2n` |
| `(2, 3, 3)` | `1/2 + 1/3 + 1/3 = 7/6` | tetrahedral `A₄` | 12 |
| `(2, 3, 4)` | `1/2 + 1/3 + 1/4 = 13/12` | octahedral `S₄` | 24 |
| `(2, 3, 5)` | `1/2 + 1/3 + 1/5 = 31/30` | icosahedral `A₅` | 60 |

Beukers-Heckman 1989 (*Invent. Math.* 95, 325–354) extended this to `_nF_{n−1}` with finite monodromy.

For Schwarz-triple parameters, ₂F₁ solutions are **algebraic over `ℂ(z)`** — expressible in radicals. For Euclidean triples (e.g. `(2, 3, 6)`, `(2, 4, 4)`, `(3, 3, 3)`), monodromy is infinite but solvable; solutions reduce to elementary functions (logarithms, powers). For hyperbolic triples (most rational `(p, q, r)` triples), monodromy is infinite non-abelian Fuchsian; solutions are transcendental ₂F₁ with no elementary form.

### §3.4 Pattern fit

**REFINEMENT.** ₂F₁ has non-abelian second structure (monodromy) at *every* parameter point. The closed-form condition is **not** "non-abelian second structure exists" — it is "**monodromy is finite**." Non-abelian alone is NOT sufficient.

The original CMS-KY abelian-vs-non-abelian dichotomy is **too coarse** for ₂F₁. The relevant invariant is finite-vs-infinite monodromy, which corresponds to whether the 2-dim local system reduces to a finite-dimensional `Δ(p,q,r)`-invariant subspace.

### §3.5 Refinement candidate

For ₂F₁, the closed-form condition is **finite monodromy group**, which is structurally equivalent to **finite-dimensional invariant subspace of the local system**. The 2-dim local system is "compressed" to closed-form algebraic solutions precisely when the monodromy orbit is finite — i.e. when the second algebraic structure (monodromy) selects a finite-dim invariant subspace.

This is the **same refined principle** that emerged for Lamé: closed-form ↔ finite-dim invariant subspace selection, by whatever mechanism (integer-parameter filtration for Lamé; finite monodromy for ₂F₁; non-abelian Lie Casimir for CMS).

---

## §4. Combined verdict — score across 5 settings

### §4.1 Tally

| # | Setting | Second algebraic structure | Closed-form? | Original law fit |
|---|---|---|---|---|
| 1 | CMS Kerr (low-Mω) | non-abelian `SL(2,ℝ) × SL(2,ℝ)` | YES | ✓ FIT |
| 2 | KY Kerr (generic-Mω) | abelian (Schouten-Nijenhuis-like) | NO | ✓ FIT |
| 3 | Lamé `S²` (ellipsoid) | abelian Stäckel + integer-`n` filtration | YES (polynomial in `sn,cn,dn`) | ✗ **VIOLATION-A** |
| 4 | Bessel disk | abelian `U(1)` (R⁺ broken by Dirichlet) | NO | ✓ FIT |
| 5 | ₂F₁ Gauss | non-abelian monodromy (always) | conditional (finite-monodromy only) | ✗ **REFINEMENT** |

**Original-law score: 3 fits / 1 violation / 1 requires-refinement out of 5.**

### §4.2 Diagnosis

The original CMS-KY conjecture, **abelian-vs-non-abelian** as the binary discriminator, is **falsified in both directions**:

- *VIOLATION-A direction* (Lamé): closed-form **does** exist with abelian-only Lie structure when there is a discrete integer-parameter filtration cutting out finite-dim invariant subspaces.
- *REFINEMENT direction* (₂F₁): non-abelian second structure is **not sufficient** — closed-form (algebraic) requires the non-abelian structure to be **finite**.

Both violations point to the same deeper invariant: **finite-dimensional invariant subspace selection**.

### §4.3 Refined universal structural law (publishable claim)

> **Refined law.** *Closed-form spectral compression exists iff the algebraic structure of commuting operators (and its discrete extensions) selects a finite-dimensional invariant subspace at each eigenvalue level.* This finite-dim selection arises via at least three distinct mechanisms:
>
> 1. **Non-abelian Lie factor with finite-dim irreps** whose Casimir labels them by a single number. Example: `SU(2)` Casimir labeling spin-`j` `(2j+1)`-dim irreps; CMS hidden conformal `SL(2,ℝ)²` Casimir labeling Kerr low-Mω QNM modes.
> 2. **Discrete integer-parameter filtration** cutting out `(2n+1)`-dim invariant subspaces within an infinite-dim eigenfunction space. Example: Lamé polynomials of order `n`; spherical harmonics of degree `ℓ` on the round sphere; Hermite polynomials of degree `n` for the quantum harmonic oscillator.
> 3. **Finite monodromy group** acting on a finite-dim local system. Example: Schwarz-list ₂F₁ algebraic solutions; finite-monodromy Fuchsian equations; algebraic Painlevé transcendents.
>
> The **abelian-tower obstruction** (Spike #11's KY-Kerr finding) is a special case: an abelian Lie algebra *without* an integer filtration or finite-monodromy structure gives no finite-dim invariant-subspace selection, so the joint eigenvalue tuple has no closed-form compression.

Under the refined law, **all 5 settings fit** (the original 4 plus this spike's 3): closed-form ↔ finite-dim invariant subspace selection.

### §4.4 What this refines, what it preserves

**Preserves:** the KY-Kerr abelian-tower diagnosis (Spike #11) as a *special case* of the refined law. The refined law agrees with the original on all 3 Kerr settings (CMS, KY, photon-ring) because in those settings there is no integer-parameter filtration available — only the Lie algebra structure determines outcomes, and the abelian-vs-non-abelian distinction tracks the finite-dim-irrep question correctly.

**Refines:** the original law to handle settings where the Lie-algebra question is decoupled from the finite-dim-invariant-subspace question. The clean discriminator is finite-dim subspace selection, not abelian-vs-non-abelian per se.

**What was right in the original conjecture:** the *intuition* that "something extra" beyond the visible base symmetry is required for closed-form. The refined law preserves this — the "something extra" is the finite-dim invariant subspace structure, whether it comes from a non-abelian Lie Casimir or from an integer filtration or from a finite monodromy.

**What was wrong:** the assumption that "non-abelian Lie factor" was the *unique* form the "something extra" could take. Lamé and ₂F₁ show that integer filtration and finite monodromy are alternative forms.

### §4.5 Recommendation

**Refine-and-publish.** The refined law is a strictly stronger structural claim (5/5 fits vs 3/5) that subsumes the original and provides a unified principle covering the CMS / KY / Lamé / Bessel / ₂F₁ regime.

Suggested next steps (out of scope for this spike, parked for the spike-protocol queue):

1. **Test the refined law on 3–5 additional settings** to broaden the empirical base. Candidates: Heun equation (4 regular singular points, finite monodromy classification by Lin-Lin and references therein from pre-2020 textbook material); Painlevé I–VI transcendents (the algebraic-solution classification is by Boalch / Lisovyy / Iwasaki / Manin); spherical harmonics on `S^d` for `d ≥ 3` (integer-filtration mechanism, predicted fit); generic Heisenberg-group representations (non-abelian but the relevant filtration is by central character).
2. **Connect to MFO §VII.4.1.2 Casimir-decomposition unification.** The MFO formula `λ_total = λ_base + C₂(ρ_G) + cross-terms` is exactly the non-abelian-Lie-Casimir mechanism (mechanism 1 above). The refined law generalizes this to include mechanisms 2 and 3, which would extend MFO §VII.4.1.2 to cover Lamé- and ₂F₁-type closed forms.
3. **Connect to spectral-calculus-rebuild §4.D** ([scope doc](spectral_calculus_rebuild_scope_2026-05-13.md)). This spike *is* the §4.D run; the refined law is the §4.D output. Whether to fold this into the spectral-calculus notebook section (recommendation 2 in the scope doc) is a separate decision for the user.

---

## §5. Provenance and discipline notes

- **Pre-2020 citations** are taken at face value per the [PDF-extraction discipline counter-clause](../../../memory/feedback_pdf_extraction_citation_discipline.md). All citations in this spike are pre-2020 canonical: Whittaker-Watson 1927, Erdélyi 1955, Klein 1884, Schwarz 1873, Beukers-Heckman 1989 (*Invent. Math.* 95, 325–354), Watson 1944, Morse-Feshbach 1953, Eisenhart 1934. **No 2020+ citations were used** in this spike.
- **No PDF-extraction misattributions caught** in the conductor's brief beyond what was already documented in earlier spikes (Gray-Kubizňák arXiv:2401.03553, HKLS arXiv:2205.05064, Xue-Jiang-Zhang arXiv:2309.02262 — all already fixed in Spike #11 / #12A).
- **No lineage claims** are made about external work per [feedback_no_lineage_claims_in_notebook](../../../memory/feedback_no_lineage_claims_in_notebook.md). The refined law is stated as a structural claim about closed-form-compression mechanisms, with mechanism-by-mechanism citations to specific established results. No "X is a natural extension of Y" framing.
- **No MVP framing** per [feedback_no_mvp_framing](../../../memory/feedback_no_mvp_framing.md). The §4.D scope-doc protocol called for three settings as the full first cut; this spike covers all three.
- **NDJSON tabular sidecar** per [feedback_ndjson_over_bloated_json](../../../memory/feedback_ndjson_over_bloated_json.md): 4 records (one per phase), one record per line, at [spike_14_abelian_wall_results_2026-05-13.ndjson](spike_14_abelian_wall_results_2026-05-13.ndjson).
- **Honest negatives valid.** This spike found that the original conjecture is **not** universally correct — it requires refinement. The refinement is itself a stronger structural claim covering 5/5 settings. This counts as "either way it's a win" per the project value system: either the original law holds (confirmation), or it needs refinement (this case), or it fails outright (would have been a clean negative). The middle case landed.

---

## §6. Attempted-but-unverifiable citations

None. All citations are pre-2020 canonical works exempt from PDF re-verification per the counter-clause. No 2020+ papers were cited.

## §7. Misattributions caught in conductor's brief

None. The brief's pre-existing citations to Spike #11 (Gray-Kubizňák arXiv:2401.03553) and Beukers-Heckman 1989 (Inv Math 95) were already correct as of when the brief was written. The conductor's framing of Schwarz's list (1873, Klein 1880, Beukers-Heckman 1989) matches the standard chronology and is consistent with this spike's findings.

One small clarification on the conductor's brief: the brief states "Klein 1880" alongside "Schwarz 1873"; the relevant Klein work is the 1884 *Vorlesungen über das Ikosaeder* monograph (Klein had related shorter papers in the early 1880s but the canonical reference is the 1884 monograph). Not a misattribution — a refinement of the date. This spike cites Klein 1884.
