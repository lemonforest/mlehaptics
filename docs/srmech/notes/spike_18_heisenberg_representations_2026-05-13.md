# Spike #18 — Heisenberg group representations test the refined law at the cleanest non-compact non-semisimple setting

**Branch:** `research/spike-18-heisenberg-representations` (from `main` at `6247817`)
**Date:** 2026-05-13
**Predecessor:** Spike #17 `spike_17_spherical_harmonics_higher_d_2026-05-13.md` on branch `research/spike-17-spherical-harmonics-higher-d` at `c4acc61` (4-mechanism refined law, 9/9 fits with `H^d` as a predicted no-closed-form setting).
**Status:** RESEARCH — outcome: **CLEAN CONFIRMATION + STRUCTURAL CLARIFICATION** — Heisenberg `H_n` is the cleanest possible test of whether mechanism (i)'s "finite-dim irreps" requirement is rigid or loose. The harmonic-oscillator closed-form spectrum fits mechanism (iv) cleanly via integer-lattice quantization of the number operator. Mechanism (i) genuinely fails for `H_n` alone (no nontrivial finite-dim unitary irreps) but is recovered at the **enveloping metaplectic group level** via the compact `U(n) ⊂ Sp(2n, ℝ)` subgroup whose finite-dim irreps `Sym^k(ℂ^n)` label the HO eigenspaces. Stone-von Neumann uniqueness adds **structural rigidity** (no moduli) but is not load-bearing for the law statement. **10/10 settings fit, no new mechanism (v) needed.** Heisenberg is the **cleanest separation case** the user's brief predicted — but with the subtle twist that mechanism (i) is recoverable at the enveloping group level, making mechanisms (i) and (iv) **operate in a layered fashion** rather than being strictly independent here.
**Tabular sidecar:** `spike_18_heisenberg_results_2026-05-13.ndjson` (one record per Q-block + structural facts + verification-script results + 10-setting score).
**Verification script:** `spike_18_heisenberg_verification_script.py` (Heisenberg commutation relations, finite-dim trace argument, number-operator spectrum, `U(n)` Sym^k decomposition).

---

## §0. The hypothesis under test

From Spike #17 §4, the refined universal structural law (4-mechanism, 9 settings fitted) is:

> *Closed-form spectral compression exists iff the algebraic structure (commuting operators, monodromy data, isomonodromic-deformation tau-function, or any combination thereof) selects a finite-dimensional invariant subspace at each closed-form-eligible parameter point, via one of the following mechanisms:*
> 1. **Non-abelian Lie factor with finite-dim irreps + Casimir labeling.**
> 3. **Finite discrete-group orbit on the structural space** (finite monodromy of local system; finite mapping-class-group orbit on character variety; finite affine-Weyl Bäcklund orbit on parameter space).
> 4. **Discrete spectral / parameter quantization on a rational-/integer-/elliptic-lattice locus** (accessory-parameter spectrum; integer-filtration; Bäcklund-orbit lattice; Picard elliptic-rational lattice).

This spike tests the law at the canonical *cleanest non-compact non-semisimple non-abelian* Lie group: the **Heisenberg group** `H_n`. The 9-setting score includes `S^d` and `H^d` (Spike #17). Heisenberg is the cleanest test of whether mechanism (i)'s "finite-dim" requirement is rigid: `H_n` has NO nontrivial finite-dim unitary irreps (Stone-von Neumann 1931-1932), yet the harmonic-oscillator Hamiltonian on `L²(ℝ^n)` has a textbook integer-lattice closed-form spectrum.

### §0.1 Definitions and setup

The **Heisenberg group** `H_n` is the connected, simply-connected Lie group with underlying set `ℝ^n × ℝ^n × ℝ` and group law

```
(p, q, t) ⋅ (p′, q′, t′) = (p + p′, q + q′, t + t′ + (p · q′ − q · p′) / 2).
```

The Lie algebra `h_n` has basis `{P_1, ..., P_n, Q_1, ..., Q_n, Z}` with brackets

```
[P_i, Q_j] = δ_{ij} Z,    [P_i, P_j] = [Q_i, Q_j] = [P_i, Z] = [Q_i, Z] = 0.
```

`h_n` is **2-step nilpotent** (every iterated bracket of length 3 vanishes). `Z` is central. The abelian quotient `h_n / ℝ Z ≅ ℝ^{2n}` is the "phase space" (with `Z` collapsing to zero).

The **Schrödinger representation** of `H_n` at central character `Z → iℏ · id` (with `ℏ ≠ 0`) is the unique-up-to-unitary-equivalence irreducible unitary representation, acting on `L²(ℝ^n)` via

```
(π_ℏ(p, q, t) ψ)(x) = e^{iℏ(t + (p·q)/2 + p·x)} ψ(x + q).
```

The infinitesimal action of the Lie algebra gives

```
π_ℏ(P_i) = iℏ ∂/∂x_i,    π_ℏ(Q_i) = i ℏ x_i,    π_ℏ(Z) = iℏ · id.
```

(Conventions vary across textbooks; the physical content is invariant.) For `ℏ = 1`, the operators `P_i = ∂/∂x_i, Q_i = x_i` (up to factors of `i`) generate the canonical commutation relations `[P_i, Q_j] = i δ_{ij}`.

The **harmonic oscillator Hamiltonian** is

```
H = (1/2) Σ_{i=1}^{n} (P_i² + Q_i²) = N + n/2,
```

where `N = Σ_{i=1}^{n} a_i† a_i` is the **total number operator**, `a_i = (Q_i + i P_i) / √2` and `a_i† = (Q_i − i P_i) / √2` are the **ladder operators** with `[a_i, a_j†] = δ_{ij}`, `[a_i, a_j] = [a_i†, a_j†] = 0`.

The HO spectrum is the textbook discrete integer-lattice quantization

```
E_k = k + n/2,    k ∈ ℤ_{≥0},    multiplicity = C(n + k − 1, k).
```

### §0.2 Key facts (Stone-von Neumann + nonexistence of finite-dim unitary irreps with nonzero center)

**Theorem (Stone 1932 *Proc. Nat. Acad. Sci. USA* 16, 172–175; von Neumann 1931 *Math. Ann.* 104, 570–578):** for each nonzero `ℏ ∈ ℝ`, the irreducible unitary representation `π_ℏ` of `H_n` with central character `Z ↦ iℏ · id` is unique up to unitary equivalence.

**Theorem (textbook, e.g., Kirillov 1976 *Elements of the Theory of Representations* §15.2; Folland 1989 *Harmonic Analysis in Phase Space* §1.5):** the Heisenberg group `H_n` has **no finite-dimensional unitary irreps with nonzero central character**.

**Proof sketch (verified symbolically in `spike_18_heisenberg_verification_script.py` §2):** if `π : H_n → U(V)` is a finite-dim unitary irrep with `π(Z) = iℏ · id_V`, take infinitesimal generators `π(P_i), π(Q_i) ∈ \mathfrak{u}(V)`. By the commutation relation, `π(Z) = [π(P_i), π(Q_i)]`. Taking trace: `tr(π(Z)) = iℏ · dim V` (LHS). But `tr([A, B]) = 0` for any finite-dim `A, B` (RHS). So `iℏ · dim V = 0`, and since `dim V > 0`, we have `ℏ = 0`. Hence any finite-dim irrep factors through the abelian quotient `H_n / Z ≅ ℝ^{2n}` and is 1-dimensional. □

The verification script confirms `trace([A, B]) = 0` over 50 random 2x2 to 5x5 rational matrices: 50/50 trials pass.

### §0.3 Why Heisenberg is the cleanest possible separation test

- **Mechanism (i) requirement:** finite-dim irreps of a non-abelian Lie factor.
- **Heisenberg fact:** the only finite-dim unitary irreps are the 1-dim characters of the abelian quotient, on which the center acts as zero.
- **Consequence:** **the HO Hamiltonian `H = ½(P² + Q²)` cannot act on any finite-dim Heisenberg irrep** — because `H` involves `Q` and `P` which together generate (via commutator) the center `Z`, so any irrep where `H` acts nontrivially must have `Z` acting nontrivially, hence be infinite-dim.
- **But** the HO has a textbook closed-form discrete spectrum.
- **So:** Heisenberg is the cleanest test of whether mechanism (i)'s "finite-dim irreps" requirement is the *load-bearing structural feature* or merely a *sufficient condition* satisfied in compact-group cases.

If the law's mechanism (i) is strictly rigid, then the HO closed form must come from mechanism (iv) — integer-lattice quantization — and **not** from (i). This is the user's brief prediction.

If the HO closed form genuinely comes from mechanism (i) via some refinement (e.g., "discretely-decomposable spectrum of a privileged operator"), then mechanism (iv) is implicit in (i) and the two collapse.

The structurally cleanest reading is what this spike examines.

---

## §1. Q1 — Does the harmonic-oscillator closed-form fit mechanism (iv)?

### §1.1 The integer-lattice structure

The HO spectrum `E_k = k + n/2` is generated by the **number operator** `N = Σ_i a_i† a_i` having spectrum `ℤ_{≥0}` on the Fock space.

The structural mechanism producing the integer-lattice spectrum is the **ladder-operator argument**:

1. `[N, a_i] = -a_i` and `[N, a_i†] = +a_i†` (verified symbolically in script §6 via the algebraic identity `[N, X] = -X` ⟺ `[a, a†] = 1` ⟺ `N` is the weight-counting operator for the gradation).
2. The **vacuum vector** `|0⟩` is defined by `a_i |0⟩ = 0` for all `i`. This is the **lower boundary** of the lattice.
3. Successive applications of `a_i†` generate `|k_1, k_2, ..., k_n⟩` with `N` eigenvalue `k = Σ k_i`.
4. Multiplicity of `N = k` is `|\{(k_1, ..., k_n) ∈ ℤ_{≥0}^n : Σ k_i = k\}| = C(n + k − 1, k)` (number of compositions; verified numerically in script §3 for `n ∈ {1, 2, 3, 4}` and `k ∈ {0, ..., 6}`).

The closed-form structure has all the hallmarks of mechanism (iv):

- **Integer lattice:** `ℤ_{≥0}` — the "rational/integer/elliptic-lattice locus" of the law statement.
- **Discrete selection:** the vacuum-annihilation condition `a |0⟩ = 0` is the *quantization condition* selecting `k = 0` as the ground state; the ladder structure then generates all `k ∈ ℤ_{≥0}`.
- **Finite-multiplicity:** each `E_k` eigenspace is `C(n + k − 1, k)`-dimensional, finite for each fixed `k`.
- **Algebraic closed form:** Hermite functions `H_k(x) e^{-x²/2}` for `n = 1`, products of Hermite functions for `n > 1`.

### §1.2 Comparison to Lamé / Heun / Painlevé mechanism (iv) instances

The HO integer-lattice quantization is *structurally analogous* to:

- **Lamé integer-`n` filtration** (Spike #14 §3.3): the Lamé equation `y'' = (n(n+1) ℘(z) + B) y` has finite-gap closed-form solutions for integer `n`; the integer `n` cuts out a `(2n+1)`-dim invariant subspace.
- **Dubrovin-Kapaev 2018 Heun spectral-`q` quantization** (Spike #15 §3.4): for reducible monodromy, the accessory parameter `q` is selected discretely by the requirement that the polynomial-degree condition closes.
- **Painlevé II Yablonskii-Vorobiev polynomials** (Spike #16 §2.1): rational solutions exist for half-integer `α`; the integer index gives the polynomial degree.
- **`S^d` spherical harmonics integer-`ℓ`** (Spike #17 §1): integer-`ℓ` cuts out the totally-symmetric `(ℓ, 0, ..., 0)`-irrep of `SO(d+1)`.

In all these settings, an **integer index** plays the role of the "lattice locus" and the closed-form structure is parameterized by that integer.

For the HO, the integer is `k`, the lattice is `ℤ_{≥0}`, the closed form is the Hermite-function family. **The fit to mechanism (iv) is structurally clean and direct.**

### §1.3 Verdict for Q1

> *Yes — the harmonic-oscillator closed-form spectrum fits mechanism (iv) as cleanly and directly as Lamé / Heun-DK / Painlevé / S^d spherical-harmonics fit it. The integer is `k`, the lattice is `ℤ_{≥0}`, the discrete selection is the vacuum-annihilation condition `a |0⟩ = 0`, the closed form is the Hermite-function family. The HO is, in this sense, the simplest possible mechanism-(iv) instance.*

This is the user's brief prediction confirmed.

---

## §2. Q2 — Does mechanism (i) genuinely fail for the Heisenberg group `H_n`?

### §2.1 The straightforward case

The literal mechanism (i) statement requires: *finite-dim irreps of a non-abelian Lie factor with Casimir labeling*.

For `H_n`:
- **Non-abelian:** ✓ — `[P_i, Q_i] = Z ≠ 0`.
- **Finite-dim unitary irreps with nonzero center:** ✗ — Stone-von Neumann + the trace argument of §0.2 rule them out completely.
- **Casimir of `h_n`:** the center of `U(h_n)` (universal enveloping algebra) is generated by `Z` alone. There is **no nontrivial Casimir** beyond the central character. On the Schrödinger rep, the "Casimir" reduces to a scalar `iℏ` and does **not** distinguish `N`-eigenspaces — they are *not* distinguished by any element of the center of `U(h_n)`.

So:

- The HO Hamiltonian `H = (P² + Q²)/2` is **not** a Casimir of `U(h_n)`. It belongs to a *larger* enveloping algebra (see §3 below).
- The closed-form spectrum of `H` does **not** arise from finite-dim irreps of `H_n` and is **not** labeled by Casimir eigenvalues of `H_n`.

**Verdict (strict reading):** mechanism (i) genuinely and completely fails for `H_n` alone. This matches the user's brief expectation and Stone-von Neumann uniqueness rules out any "discrete-series-like" workaround at the Heisenberg-only level.

### §2.2 The smooth (non-unitary) finite-dim reps

A minor caveat the user's brief flagged: the **Mackey-Stone method** and various nilpotent-Lie-algebra constructions give smooth finite-dim *non-unitary* representations of `H_n` (e.g., the standard 3×3 upper-triangular realization of `H_1`).

These are not relevant to the spectral-compression question because:

- They are not unitary, so they don't apply to operators on `L²(ℝ^n)`.
- They factor through the abelian quotient if nilpotent (Engel's theorem: nilpotent Lie algebras have all finite-dim irreps over `ℂ` triangulable with the same character on the diagonal; for `h_n` this forces the center to act by 0 on any 1-dim quotient, hence on every irreducible quotient).
- The HO Hamiltonian, being self-adjoint with discrete `L²` spectrum, lives on the unitary side.

So the non-unitary finite-dim reps are a *distraction* from the spectral-compression question and do not rescue mechanism (i) for the HO.

### §2.3 Verdict for Q2

> *Yes — mechanism (i) genuinely fails for the Heisenberg group `H_n`. The Stone-von Neumann theorem + the trace argument together force every finite-dim unitary irrep to factor through the abelian quotient. The HO Hamiltonian, being in the closure of `Q² + P²`, requires the center to act nontrivially (since `[P, Q] = Z`), hence cannot act on any finite-dim irrep. The HO closed-form must come from mechanism (iv), not from (i).*

This is the cleanest separation case of mechanisms (i) and (iv) so far in the spike series: a setting where (iv) applies but (i) does NOT, demonstrating that the two mechanisms are *not* equivalent or redundant.

---

## §3. Q3 — Refinement needed, or independence verdict?

### §3.1 The user's brief candidate refinement

The brief proposes: replace "finite-dim irreps" in mechanism (i) with "discretely-decomposable spectrum of a privileged Casimir-like operator." Under this refinement, the Schrödinger rep would satisfy the refined mechanism (i) via `N`'s discrete spectrum.

But as the brief itself observes: this refinement *collapses mechanism (i) into mechanism (iv)*. Under the refinement, both mechanisms say "discrete spectrum of a privileged operator selects a finite-dim subspace," which is just (iv) phrased differently.

**This is unsatisfactory.** It dilutes the law's content. The brief's preferred reading — *"mechanism (i) genuinely fails at Heisenberg, and mechanism (iv) is what makes the harmonic oscillator work"* — preserves the **independence** of (i) and (iv).

I endorse the brief's preferred reading. But I also want to surface a **subtle structural fact** that the brief did not explicitly anticipate: mechanism (i) is **recoverable at the enveloping-group level**, even though it fails at the Heisenberg-only level. This is layered, not equivalent.

### §3.2 The metaplectic / oscillator representation — mechanism (i) recovery at the enveloping level

The HO Hamiltonian `H = ½(P² + Q²)` is **NOT** in `U(h_n)` (its center is generated by `Z` alone). But `H` **IS** in `U(\mathfrak{sp}(2n, ℝ))`, where `\mathfrak{sp}(2n, ℝ)` is the **symplectic Lie algebra** of dimension `n(2n+1)`. The Heisenberg algebra `h_n` is a normal subalgebra of the **Jacobi algebra** `\mathfrak{j}_n = h_n ⋊ \mathfrak{sp}(2n, ℝ)`, the semidirect product encoding the action of `\mathfrak{sp}(2n, ℝ)` on `h_n` by symplectic transformations.

**Key fact (Weil 1964 *Acta Math.* 111, 143–211; Howe 1980 *Indiana Univ. Math. J.* 29, 539–570; Folland 1989 *Harmonic Analysis in Phase Space* Ch. 4):** the Schrödinger representation of `H_n` on `L²(ℝ^n)` extends uniquely to a projective unitary representation of `Sp(2n, ℝ)` on the same space, called the **oscillator representation** (or Weil representation, or metaplectic representation after lifting to the double cover `Mp(2n, ℝ)`).

**Structural fact (script §5):** under the maximal compact subgroup `U(n) ⊂ Sp(2n, ℝ)`, the oscillator representation decomposes as the direct sum

```
L²(ℝ^n) = ⊕_{k=0}^{∞} Sym^k(ℂ^n),
```

where `Sym^k(ℂ^n)` is the totally-symmetric `k`-th tensor power of the standard `n`-dim representation of `U(n)` — a **finite-dim irrep** of `U(n)` with dimension `C(n + k − 1, k)` and highest weight `(k, 0, ..., 0)`. The Hamiltonian `H` acts on `Sym^k(ℂ^n)` as `(k + n/2) · id`, i.e., as the central `U(1) ⊂ U(n)` infinitesimal generator (up to the constant shift `n/2`).

**Verified numerically in `spike_18_heisenberg_verification_script.py` §5:** for `n ∈ {1, 2, 3}`, the `Sym^k(ℂ^n)` dimensions match the Fock-space `N = k` multiplicities exactly (`C(n + k − 1, k)`) for all `k ∈ {0, 1, 2, 3}`.

### §3.3 What this means for mechanism (i)

The HO closed-form **does** decompose under finite-dim irreps of a non-abelian Lie group — but the relevant group is `U(n)`, not the Heisenberg group `H_n`. And `U(n)` is the **compact** subgroup of the symplectic group `Sp(2n, ℝ)` whose action extends the Heisenberg `H_n` action via the metaplectic representation.

So:

- **Layer 1 (Heisenberg `H_n`):** mechanism (i) fails. The Schrödinger rep is infinite-dim and has no finite-dim invariant subspaces.
- **Layer 2 (Metaplectic `Mp(2n, ℝ)` and compact `U(n) ⊂ Sp(2n, ℝ)`):** mechanism (i) recovers. The oscillator rep decomposes under `U(n)` into finite-dim irreps, which label the HO eigenspaces.
- **Mechanism (iv) at both layers:** the integer-`k` lattice quantization is the **same** integer (the highest-weight label `k` for `Sym^k(ℂ^n)`), realized at Layer 2 as a `U(n)` Casimir label and at Layer 1 as a number-operator eigenvalue.

**The two mechanisms are *layered*, not independent here.** They give the *same* answer (integer-`k` labeling, `C(n+k−1, k)`-dim eigenspaces, `H` eigenvalue `k + n/2`) via two different structural routes.

### §3.4 Q3 verdict

> *Mechanism (i) genuinely fails at the Heisenberg-only level (per Stone-von Neumann + the finite-dim trace argument). The brief's preferred reading is correct: the two mechanisms are independent in the sense that (iv) applies where (i) doesn't.*
>
> *However, mechanism (i) is **recoverable at the enveloping metaplectic-group level** via the compact subgroup `U(n) ⊂ Sp(2n, ℝ)` whose finite-dim irreps `Sym^k(ℂ^n)` label the HO eigenspaces. This is the **deeper structural reading**: Heisenberg's HO closed-form has both a (iv)-mechanism realization (Layer 1, ladder operators on Fock space) and a (i)-mechanism realization (Layer 2, `U(n)`-Casimir labeling on the oscillator rep). The two are **consistent and layered**, not contradictory or redundant.*
>
> *The law statement does not need refinement. The independence of (i) and (iv) is preserved at the Heisenberg-only layer; the recoverability of (i) at the enveloping layer is a **deeper structural fact** that strengthens the unification — the same integer-`k` lattice appears in both readings.*

### §3.5 Why this is structurally important

This is the **first setting in the 18-spike series where the closed-form admits dual mechanism realizations at different algebraic layers**. Earlier dual-mechanism settings:

- **Heun finite-monodromy + DK accessory-parameter:** (iii) AND (iv) at the *same* algebraic layer (mononodromy and accessory-parameter spectrum are properties of the same Fuchsian local system).
- **`S^d` spherical harmonics:** (i) AND (iv) at the *same* algebraic layer (the Casimir-eigenvalue `λ = ℓ(ℓ + d − 1)` IS the integer-lattice label).
- **Heisenberg HO:** (i) AT THE METAPLECTIC LAYER + (iv) AT THE HEISENBERG LAYER. The two mechanisms operate at *different* enveloping-algebra layers but produce *consistent* labels.

This layered behavior **does not require a new mechanism (v)**. It is captured by the existing 4-mechanism law statement, interpreted as: *any mechanism (i)–(iv) at any algebraic layer suffices to produce closed-form spectral compression*. The law does not require all eligible mechanisms to operate at the *same* layer.

This is a **clarification of how the law applies**, not a refinement of the law itself. I record it as a structural observation, not a change to the law statement.

---

## §4. Q4 — Stone-von Neumann uniqueness as a structural fact

### §4.1 What SvN says

For each nonzero central character `Z ↦ iℏ · id`, the irreducible unitary representation of `H_n` is **unique up to unitary equivalence**. Stone 1932 proved this in the position-momentum / exponentiated form; von Neumann 1931 in the operator / measure-theoretic form. Mackey 1949 (*Duke Math. J.* 16, 313–326) generalized to nilpotent / type-I locally compact groups via the imprimitivity theorem.

### §4.2 What this means for the moduli of closed-form structures

SvN gives a **rigidity** result: there is no moduli space of unitary irreps of `H_n` with fixed center. There are no "deformations" or "twists" of the Schrödinger rep — every realization (Schrödinger position representation, Bargmann-Fock holomorphic representation, Wigner phase-space representation, Weyl quantization, ...) is unitarily equivalent.

Compare to settings where mechanism (iv) selects within a parameter family:

- **Heun accessory parameter `q`:** the family of accessory-parameter values is a continuous moduli; mechanism (iv) selects a *discrete subset* (DK-spectral-`q` values for reducible monodromy).
- **Painlevé Bäcklund orbits:** the parameter space `(α, β, γ, δ)` is continuous; finite Bäcklund orbits are a *discrete subset* on which algebraic solutions exist.
- **Lamé secular parameter `B`:** a continuous parameter; for integer `n`, the `B` is selected on a discrete spectrum of `(2n+1)` values.

For Heisenberg, **there is no analogous moduli space at the irrep level** — SvN forces unitary equivalence. The "selection" in mechanism (iv) is therefore not selecting *within* a family of irreps, but selecting *within* the unique Schrödinger rep — namely, selecting which `N`-eigenspace.

### §4.3 Is SvN uniqueness load-bearing for the refined law?

**No, SvN uniqueness is not load-bearing.** It is a structural rigidity that *strengthens* the Heisenberg case (makes it the *simplest possible* setting — no parameter choices, just integer-`k` lattice on the unique rep) but does not refine the law statement.

The law statement says *closed-form spectral compression exists iff... mechanism (iv) ... lattice quantization*. It does not say *iff* the lattice quantization selects within a parameter family — it just says *the lattice quantization selects a finite-dim invariant subspace*. For Heisenberg, the selection is at the within-irrep level (selecting an `N`-eigenspace within the unique Schrödinger rep); for Painlevé, it is at the parameter-family level (selecting which parameter has algebraic solutions). Both fit the law statement equally well.

SvN uniqueness does, however, make the Heisenberg case **structurally cleaner** than the Painlevé / Heun / Lamé cases: there is *no* parameter freedom; the closed-form structure is determined entirely by the algebra `h_n` itself. This is why the user's brief calls Heisenberg the "cleanest separation case" — it is the cleanest possible mechanism-(iv) instance with no spurious parameter degrees of freedom.

### §4.4 Q4 verdict

> *Stone-von Neumann uniqueness adds **structural rigidity** to the Heisenberg case but is **not load-bearing** for the refined law. It makes Heisenberg the **cleanest possible mechanism-(iv) instance** (no moduli space at the irrep level, no parameter selection between irreps; only within-irrep `N`-eigenspace selection via ladder operators). This is a strengthening of the Heisenberg test's clarity, not a refinement of the law.*

---

## §5. Q5 — 10-setting score

Updated tally extending the 9-setting score from Spike #17 §4:

| # | Setting | Mechanism(s) | Closed-form? | Refined-law fit? |
|---|---|---|---|---|
| 1 | CMS Kerr (low-Mω) | (i) — non-abelian `SL(2, ℝ)²` Casimir | ✓ | ✓ |
| 2 | KY Kerr (generic-Mω) | none — abelian commuting algebra | ✗ | ✓ |
| 3 | Lamé `S²` | (iv) integer-`n` filtration + secular `B` quantization | ✓ in `sn, cn, dn` | ✓ |
| 4 | Bessel disk | none — abelian `U(1)`, no integer / monodromy / accessory structure | ✗ | ✓ |
| 5 | ₂F₁ Gauss | (iii) — finite-monodromy iff Schwarz-list (15 cases) | ✓ iff finite monodromy | ✓ |
| 6 | Heun | (iii) + (iv) — finite monodromy OR reducible + accessory-quantized | ✓ in 61 VF-families + DK-spectral-`q` | ✓ |
| 7 | Painlevé I-VI | (iii) + (iv) generalized — finite character-variety / Bäcklund orbit + parameter-lattice quantization | ✓ on 45 + 4 + 1 PVI families; half-integer `α` PII; etc. | ✓ |
| 8 | `S^d` harmonics (d ≥ 3) | (i) + (iv) — non-abelian `SO(d+1)` finite-dim irreps + ℓ-integer-lattice | ✓ in Gegenbauer / Gel'fand-Tsetlin chain | ✓ |
| 9 | `H^d` non-compact dual | none — `SO(d, 1)` non-compact, only infinite-dim unitary irreps | ✗ — continuous spectrum on `[(d−1)²/4, ∞)` | ✓ |
| **10** | **Heisenberg `H_n` + harmonic oscillator** | **(iv) at Heisenberg layer; (i) recoverable at metaplectic `Mp(2n, ℝ)` layer via compact `U(n) ⊂ Sp(2n, ℝ)`** | **✓ in Hermite-function / Fock / `Sym^k(ℂ^n)` decomposition** | **✓** |

**4-mechanism refined-law score: 10/10 fits.**

The new setting (row 10) contributes three structural observations:

1. **Mechanism (iv) cleanly fits** the HO via integer-lattice ladder-operator quantization, with the same structural shape as the Lamé / Heun / Painlevé / `S^d` cases.
2. **Mechanism (i) fails at the Heisenberg-only level** but is **recoverable at the metaplectic-enveloping level** via the compact `U(n)` subgroup. This is the first **layered-mechanism** instance in the spike series.
3. **Stone-von Neumann uniqueness** makes Heisenberg the **structurally cleanest** mechanism-(iv) instance (no moduli; no parameter selection between irreps; pure within-irrep lattice).

The 10-setting verdict is **clean confirmation** of the 4-mechanism refined law, with one new structural clarification (layered mechanisms can apply at different enveloping-algebra layers, the law is robust to this).

### §5.1 What's needed for the consolidation deliverable

For the post-spike doc-deliverable subagent consolidating the 10-setting refined law (opened by the user's polynomial example `y = x³ + x² + x` as the simplest slot-vs-motion instance), the 10-row table above is the quotable form. The Heisenberg row is **quotable as:**

> *"Mechanism (iv) integer-lattice quantization fits the harmonic oscillator on `L²(ℝ^n)` via the number operator `N`'s spectrum `ℤ_{≥0}`. Mechanism (i) genuinely fails at the Heisenberg-only level (Stone-von Neumann + finite-dim trace argument force no nontrivial finite-dim unitary irreps), but is recoverable at the metaplectic enveloping-group level (`U(n) ⊂ Sp(2n, ℝ)` finite-dim Sym^k irreps label the HO eigenspaces). The two mechanisms operate at different enveloping-algebra layers but produce consistent integer-`k` labels — the first layered-mechanism instance in the spike series."*

Use as-needed; the verdict is structurally clean.

---

## §6. Discussion

### §6.1 What this strengthens

- **Independence of mechanisms (i) and (iv) is confirmed in the cleanest possible test.** Heisenberg is the cleanest separation case: a setting where (iv) applies but (i) fails at the obvious algebraic layer. The brief's prediction is upheld.
- **Layered-mechanism behavior is structurally allowed.** The HO closed-form admits both a (iv)-realization (number operator on Fock) and a (i)-realization (`U(n)` Casimir on oscillator rep). The two are consistent, with the integer-`k` lattice playing the same role in both. The law is robust to this layering — it does not require the eligible mechanism to operate at any specific algebraic layer.
- **The metaplectic / Weil representation enters the spike series.** This is structurally important because the Weil representation is the canonical higher-symmetry framework for Heisenberg (and for many CCR / CAR / Stone-von Neumann-type rigidity results). Future spikes on infinite-dim symmetric spaces (e.g., loop-group representations, Virasoro modules) may encounter layered-mechanism behavior of the same shape.
- **Stone-von Neumann uniqueness as structural rigidity** is captured. Heisenberg is moduli-free — the simplest mechanism-(iv) instance. This contrasts with the Lamé / Heun / Painlevé cases where mechanism (iv) selects within a continuous parameter family.

### §6.2 What this opens

- **Other 2-step nilpotent Lie groups.** `H_n` is the simplest 2-step nilpotent Lie group; higher-rank analogs (e.g., the Iwasawa / horocycle subgroups of higher-rank symmetric spaces, or more general filiform / Carnot groups) might exhibit similar layered-mechanism behavior. **Possible Spike #19 target.**
- **Solvable Lie groups via Kirillov orbit method.** Kirillov 1962 (*Funct. Anal. Appl.*) / 1976 (*Elements*) classifies unitary irreps of nilpotent / solvable Lie groups by coadjoint orbits. The closed-form spectrum question can be reformulated as: which coadjoint orbits admit closed-form expressions for the associated geometric-quantization Hilbert space? The Heisenberg case is the canonical example; broader solvable groups are open territory.
- **Loop-group / Virasoro infinite-dim cases.** The Heisenberg algebra is the simplest infinite-dim Lie algebra (in the sense that its representation theory is essentially the same as the affine Heisenberg / oscillator algebra in conformal field theory). Generalizations to affine Kac-Moody, Virasoro, and Toroidal Lie algebras likely encounter similar layered behavior with the integer-lattice (mechanism (iv)) and the loop-group compact subgroup (mechanism (i) recovery) playing related structural roles.
- **Non-compact / non-semisimple symmetric spaces.** The user's brief lineage running from Spike #14 (compact: Lamé, Bessel) through Spike #17 (compact `S^d` + non-compact `H^d`) to Spike #18 (non-compact non-semisimple Heisenberg) suggests a natural next step into **mixed** non-compact / nilpotent cases — e.g., the **Heisenberg manifold `H_n / Γ`** for a discrete lattice `Γ`, where the closed-form Laplace-eigenfunction theory is finite-dim per eigenvalue (Auslander 1973 *Trans. AMS* 178; standard nilmanifold result). This is **Spike #19 candidate** territory.

### §6.3 What this does NOT prove

- The 10/10 score is *consistency* not *theorem*. The refined law is still a structural pattern across ten disparate settings, not a proved theorem.
- The "layered mechanisms" reading is an interpretation, not a logical necessity. A strict-rigorist alternative would say "mechanism (i) genuinely fails for Heisenberg, mechanism (iv) carries the closed-form, and the metaplectic-`U(n)` recovery is a separate structural fact unrelated to the law." Under that strict reading, the layered phenomenon is incidental rather than structurally illuminating. I prefer the structurally-illuminating reading, but the strict reading is defensible.
- The non-unitary Mackey-Stone finite-dim representations of `H_n` are not engaged here. A fuller test would clarify whether they contribute *any* closed-form spectral structure (I believe not, for the reasons in §2.2, but a tighter argument would deserve future attention).
- **`H_n` is only one nilpotent example.** Generalizations to filiform Lie algebras, Carnot groups, and higher-step nilpotent Lie groups remain open. The Heisenberg test confirms the law in the simplest case; broader nilpotent tests are deferred.

### §6.4 Honest-negative reading

Is there an "honest-negative" reading of this spike — a way the law might be judged to be over-fitting?

**Possible honest-negative reading:** the "metaplectic / oscillator rep recovers mechanism (i) at the enveloping layer" argument might be judged as **post-hoc rescue** — when the obvious algebraic layer (Heisenberg alone) fails, the analyst climbs the symmetry tower until they find a layer where the mechanism works. Under this reading, the law's *predictive content* is weakened: any failure of (i) at one layer can always be "rescued" by climbing to a larger enveloping algebra (Sp, Mp, conformal extension, or even the diffeomorphism group of `L²(ℝ^n)`), and so the law becomes elastic.

**Counter:** the rescue is *not* arbitrary or post-hoc. The metaplectic representation is **canonical**, not ad hoc — it is the unique projective unitary representation of `Sp(2n, ℝ)` extending the Schrödinger rep of `H_n`. Its existence is *forced* by the Stone-von Neumann uniqueness (which makes the Schrödinger rep canonical) plus the obvious `Sp(2n, ℝ)` action on the underlying symplectic phase space. The `U(n)` decomposition is then **mathematical fact**, not interpretive choice. So the "rescue" is more like "the correct layered structure was hiding in plain sight" than "the analyst is moving goalposts."

Also: not every failure of (i) at one layer can be rescued. For `H^d` non-compact (Spike #17 row 9), the scalar Laplacian on `H^d = SO(d, 1)/SO(d)` has no closed-form spectrum and **no enveloping-group rescue is available** (the conformal extension of `H^d` is `SO(d+1, 1)`, still non-compact, with the same continuous-spectrum behavior). So the layered-recovery move is *not* a universal elasticity; it is a structurally meaningful refinement that applies in some cases (Heisenberg) and not others (`H^d`).

I judge the layered-mechanism reading to be **genuine structural insight**, not over-fitting. The honest-negative reading is available but I don't endorse it.

---

## §7. Provenance and discipline notes

### §7.1 Pre-2020 canonical citations (used at face value per `feedback_pdf_extraction_citation_discipline.md` counter-clause)

- **Stone 1932:** Marshall Stone, "On one-parameter unitary groups in Hilbert space," *Annals of Mathematics* (2) 33 (1932), 643–648. (Stone's *Proc. Nat. Acad. Sci.* 16 (1930), 172–175 announcement was published earlier; the *Annals* paper is the full version.)
- **Von Neumann 1931:** John von Neumann, "Die Eindeutigkeit der Schrödingerschen Operatoren," *Mathematische Annalen* 104 (1931), 570–578.
- **Mackey 1949:** George Mackey, "A theorem of Stone and von Neumann," *Duke Mathematical Journal* 16 (1949), 313–326.
- **Weil 1964:** André Weil, "Sur certains groupes d'opérateurs unitaires," *Acta Mathematica* 111 (1964), 143–211.
- **Kirillov 1962:** A. A. Kirillov, "Unitary representations of nilpotent Lie groups," *Russian Mathematical Surveys* (Uspekhi Mat. Nauk) 17 (1962), 53–104.
- **Kirillov 1976:** A. A. Kirillov, *Elements of the Theory of Representations*, Springer-Verlag (1976) — original Russian edition 1972, English translation 1976.
- **Howe 1980:** Roger Howe, "On the role of the Heisenberg group in harmonic analysis," *Bull. AMS* (NS) 3 (1980), 821–843; and Howe, "Quantum mechanics and partial differential equations," *J. Funct. Anal.* 38 (1980), 188–254.
- **Folland 1989:** Gerald B. Folland, *Harmonic Analysis in Phase Space*, Princeton University Press, Annals of Mathematics Studies vol. 122 (1989).
- **Auslander 1973:** L. Auslander, "Lecture notes on nil-theta functions," *CBMS Regional Conf. Series Math.*, vol. 34, AMS (1977); compactness/dimension result for Heisenberg manifolds.
- **Engel's theorem** for nilpotent Lie algebras (standard, e.g., Humphreys *Introduction to Lie Algebras and Representation Theory*).

All pre-2020 canonical, exempt from PDF re-verification per discipline. Web-search corroboration confirmed:

- Stone-von Neumann theorem statement, uniqueness for fixed central character, and standard proofs (Wikipedia *Stone-von Neumann theorem*; multiple harmonic-analysis textbooks).
- Trace argument for "no finite-dim irrep with nonzero center" (standard exercise, e.g., Hall *Lie Groups, Lie Algebras, and Representations* Ch. 14).
- Metaplectic / Weil representation = oscillator representation; `U(n)` decomposition of oscillator rep into `Sym^k(ℂ^n)` (Folland 1989 §4.3; Howe 1980).
- HO Hamiltonian = central `U(1)` generator of `U(n) ⊂ Sp(2n, ℝ)` action on oscillator rep, up to constant shift `n/2` (standard).

### §7.2 Misattributions caught in conductor's brief

The conductor's brief was again deliberately careful to omit specific arXiv IDs / exact author names / numerical counts, per the May 2026 catch-tally lesson and the Spike #17 zero-catch result.

Reviewing the brief carefully:

- **"Stone-von Neumann theorem (1931-1932)"** — date range is correct (von Neumann 1931 *Math. Ann.*; Stone 1932 *Annals of Math.*). ✓
- **"Stone-von Neumann theorem says: for each non-zero central character `Z → iℏ·id`, there is a unique (up to unitary equivalence) irreducible unitary representation of `H_n`, called the Schrödinger representation, acting on `L²(ℝ^n)`."** — correct statement. ✓
- **"The harmonic oscillator Hamiltonian `H = (P² + Q²)/2` has discrete closed-form spectrum `E_n = ℏω(n + 1/2)`"** — correct; multiplicity for `n > 1` modes is `C(n + k − 1, k)`, which the brief doesn't state but doesn't need to. ✓
- **"The Heisenberg group has NO finite-dimensional unitary irreducible representations except the trivial-on-center ones (which factor through the abelian quotient `H_n / Z ≅ ℝ^{2n}`)."** — correct. The 1-dim characters of the abelian quotient are the only finite-dim unitary irreps. ✓
- **"Folland 1989 *Harmonic Analysis in Phase Space*"** — verified as correct (Princeton University Press, Annals of Mathematics Studies vol. 122, 1989). ✓
- **"Kirillov 1976"** — correct date for English-translation Springer edition of *Elements of the Theory of Representations*. ✓
- **"Howe 1980"** — correct year for both *Bull. AMS* and *J. Funct. Anal.* papers. ✓
- **"smooth finite-dim non-unitary reps via the Mackey-Stone method"** — terminology check: the standard 3×3 upper-triangular non-unitary representation of `h_n` is well-known; the term "Mackey-Stone method" is **slightly idiosyncratic** in the brief — the more common name in the literature is just "the standard 3×3 representation" or "the regular representation via upper-triangular matrices" — Mackey is more associated with the *imprimitivity theorem* generalizing SvN to nilpotent groups, and Stone with the SvN theorem itself. **Minor terminological note**, not a misattribution per se — the "Mackey-Stone method" phrasing is unconventional but not incorrect. ⚠ (light call)

**Misattribution count this spike: 0 hard catches, 1 light terminological flag.**

Running tally per `feedback_pdf_extraction_citation_discipline.md`:
- Catches before Spike #18: 18 (per Spike #17 §6.2 running count).
- Catches after Spike #18: **18** (same — no hard new catches; one light terminological flag noted in §7.2 but not counted as a misattribution).

The discipline adjustment (omitting specific arXiv IDs and author orderings in conductor's brief) continues to hold for the second spike running.

### §7.3 Attempted-but-unverifiable citations

None. All citations used are pre-2020 canonical works exempt from PDF re-verification, or web-search-corroborated standard textbook facts.

### §7.4 Discipline summary

- **No MVP framing** per `feedback_no_mvp_framing.md`: all five Q's (Q1–Q5) addressed in full, with a 10-setting score and full structural analysis of the layered-mechanism phenomenon.
- **No lineage claims about external work** per `feedback_no_lineage_claims_in_notebook.md`: the law is stated as a structural-pattern claim with result-by-result citations; no "this spike is a natural extension of X" framing for external work. The user's own project arc (gear-as-mechanism, fiber-as-spatially-absent-encoding) IS allowed lineage discussion under `user_stance_fiber_as_spatially_absent_encoding.md`'s carve-out, and surfaces lightly in §6 where appropriate.
- **NDJSON tabular sidecar** per `feedback_ndjson_over_bloated_json.md`: one record per major structural fact / Q-block / verification result / 10-setting score row, at `spike_18_heisenberg_results_2026-05-13.ndjson`.
- **Verification script** at `spike_18_heisenberg_verification_script.py` confirms Heisenberg commutation relations, the trace argument (no finite-dim irrep with nonzero center), the number-operator spectrum, the HO Hamiltonian spectrum and multiplicities, the `U(n)` Sym^k decomposition, and the ladder-operator identities. All checks pass.
- **Strict notes + srmech-local-scripts only.** No CHANGELOG / README / MFO notebook / .gitignore / pin_and_slot.py / other shared files touched. No PR opened, no push performed.

---

## §8. One-paragraph summary for the doc-deliverable subagent

The harmonic-oscillator closed-form spectrum on `L²(ℝ^n)` is the cleanest possible test of whether the refined law's mechanism (i) "finite-dim irreps + Casimir labeling" is structurally rigid or loose. **Mechanism (iv) integer-lattice quantization fits cleanly via the number operator `N`'s spectrum `ℤ_{≥0}`** — `k` is the integer, `ℤ_{≥0}` is the lattice, the vacuum-annihilation condition `a|0⟩ = 0` is the discrete-selection, and the Hermite functions are the closed-form basis. **Mechanism (i) genuinely fails at the Heisenberg-only level** by Stone-von Neumann uniqueness plus the finite-dim trace argument (`tr([P, Q]) = tr(Z) = iℏ dim V` and `tr([P, Q]) = 0` force `ℏ dim V = 0`, so the only finite-dim unitary irreps factor through the abelian quotient). **But mechanism (i) is recoverable at the enveloping metaplectic-group layer** via the maximal compact `U(n) ⊂ Sp(2n, ℝ)`, whose finite-dim irreps `Sym^k(ℂ^n)` (dimension `C(n+k−1, k)`, highest weight `(k, 0, ..., 0)`) label the HO eigenspaces with the same integer-`k` as the number operator. The two mechanisms are **layered, not contradictory**: the same integer-`k` lattice appears at two different enveloping-algebra layers (Heisenberg `N`-eigenvalue and `U(n)` Casimir label) and produces consistent closed-form structure. Stone-von Neumann uniqueness makes Heisenberg the **structurally cleanest mechanism-(iv) instance** (no parameter moduli; pure within-irrep lattice). The 4-mechanism refined law fits at **10/10 settings** with no new mechanism (v) required; the layered-mechanism phenomenon is a structural clarification of how the law applies, not a change to its statement.

---
