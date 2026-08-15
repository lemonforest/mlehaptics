# F1347 — **the slow test is a TRIDIAGONAL held in a DENSE container, and the Euclidean smuggle is in the CARRIER, not the maths.** `hydrogen_radial` builds a real-symmetric tridiagonal Hamiltonian — **1198 nonzeros in 160,000 cells at the shipped default `n_grid=400`, 99.25% structural zero** — promotes it to **complex** although it is provably real-symmetric (then discards the imaginary part), and hands the whole dense block to a **general** Hermitian eigendecomposition. The cost curve is superlinear and the default is 3.3× beyond the largest size I timed. The contrast case is one module over: **`lattice_momentum` is CIRCULANT**, its eigenvectors *are* the characters of ℤ/n, and its spectrum matches the closed form `sin(2πk/n)` to **4.66e-15** — **no eigensolver needed at all**. `hydrogen_radial`'s operator is **not** circulant. But the honest verdict splits: the *physics* genuinely needs a general solve (a bound state is exactly the thing whose operator shares an eigenbasis with neither its kinetic nor its potential term), while **three costs the structure does not require** are paid by the carrier. And it declares **no cascade descriptor, no lane, no frame scope**.

**User (2026-08-15):** *"we want to inspect what this is and how it does what it does… find out if it's not following an A-N grammar correctly… make sure that it's not smuggling in euclidian space geometry when cyclic group relational stuff is what makes those euclidian rules emergent."*

srmech 0.9.0rc434 (pulled this session; rc432 → rc434). Generating code: `R-RBS-LM-HYDROGEN_*.py` (exit 0). Descriptor: `cascade_catalog/radial_potential_diagonal.toml`.

## 1 — what it is `[DEMONSTRABLE]`

```
  n_grid=40    nonzeros 118    of 1600     density 59/800
  n_grid=120   nonzeros 358    of 14400    density 9/362
  n_grid=400   nonzeros 1198   of 160000   density 7/935      <- the DEFAULT
```
Tridiagonal, exactly `3n−2` nonzeros. **99.25% of the container is structural zero at the shipped default, and a dense eigendecomposition visits every one of those zeros.**

## 2 — and it is carried as COMPLEX on provably REAL data `[DEMONSTRABLE]`

The built Hamiltonian is **entirely real** and **symmetric** (both verified). Yet:
```python
potentials.py:119   H = Mat.from_rows(rows, is_complex=True)
potentials.py:127   [[eigvecs_mat[i, j].real for j in ...] ...]
```
Promoted to complex to enter `mat_hermitian_eigendecompose`, then the imaginary part is thrown away. **The docstring says so itself** — *"H here is real-symmetric, so the eigenvectors are real."* Every multiply inside the solve is a complex multiply on a zero imaginary part.

## 3 — the contrast that answers the question `[DEMONSTRABLE]`

| | `lattice_momentum` | `hydrogen_radial` |
|---|---|---|
| boundary | **periodic** | **Dirichlet** |
| circulant? | **True** | **False** |
| spectrum | closed form `sin(2πk/n)`, **dev 4.66e-15** | no closed form |
| solve needed | **none** — diagonalisation *is* the ℤ/n structure | general O(n³) |

`lattice_momentum`'s shipped explanation states the framework position outright: *"Per `[[user_stance_pi_as_projection]]` it is the discrete-cyclic **UPSTREAM** of the continuous derivative, not an approximation to it."* When the cyclic group acts, **the eigenbasis is free** — it is the character table, not a computation.

## 4 — but be precise about which part is smuggled `[the verdict]`

**T (kinetic)** — tridiagonal, **constant** diagonal. A Dirichlet box is *not* acyclic: it is the **antisymmetric sector of ℤ/2(n+1)**, eigenvectors `sin(ijπ/(n+1))` — the discrete sine transform. **T is cyclic-group native, one folding down. Closed form.**

**V (potential)** — diagonal, **non-constant**: `l(l+1)/(2r²) − 1/r`.

**H = T + V** — diagonal in **neither** basis. That is not a modelling failure; **it is what makes hydrogen hydrogen rather than a free particle.** A bound state is precisely the object whose operator shares no eigenbasis with its kinetic term.

> **So the maths is clean. The smuggle is in the CARRIER.** Three costs the structure does not require:
> **(a)** a tridiagonal in a dense `n×n` container; **(b)** complex arithmetic on real-symmetric data; **(c)** a general dense eigensolver where the operator is tridiagonal (Sturm-sequence bisection gets eigenvalues without touching the zeros).
>
> None of (a)–(c) is Euclidean *geometry* smuggled into the maths. All three are **Euclidean-shaped STORAGE** smuggled into the carrier — a dense grid-of-cells standing in for a relational object with `3n−2` relationships.

## 5 — the A-N grammar gap, and the descriptor `[DEMONSTRABLE]`

Measured: **no cascade descriptor** for it, `reads_lane` **None**, `frame_scope` **None**, `composes` naming exactly one Class-L primitive. It is a physics op that builds a **Class-I object (a cyclic difference stencil) wearing a Class-L coat** and declares none of it.

`cascade_catalog/radial_potential_diagonal.toml` declares the part that *is* a cascade — the Class-N exact-rational radial potential — with `proof_cases`, and returns exact ℚ (`(40/401)² = 1600/160801`, no float). It states in-file which parts are **not** per-element cascades (the stencil constant; the eigensolve), because declaring those would be decorative.

## 6 — the projection-from-resonance reading `[SPECULATIVE — one instance, not a law]`

The pattern this instance exhibits, stated so it can be tested elsewhere rather than admired here:

> **A resonance rule is closed under a cyclic group, so its spectrum is READ. A projection rule imposes a boundary that breaks the cycle, so its spectrum must be SOLVED. The computational cost of the solve is a measure of how much cyclic structure the projection destroyed.**

Here that is exact and measured: periodic → circulant → free eigenbasis; Dirichlet → not circulant → O(n³). **This is ONE instance.** I have not tested it in biology or cosmology, and the cross-domain claim in the user's framing — that projection rules are emergent from resonance rules generally — is **not** established by a single operator pair. What this finding supplies is a **falsifiable shape** for that search: find a domain pair where one member is closed under a cyclic group and the other is the same object with a boundary, and check whether the cost gap tracks the broken symmetry. Candidate probes, none run: closed vs. open reading frames; periodic vs. bounded cosmological modes; a ring vs. a bar resonator.

## Honest scope

- `[DEMONSTRABLE]`: §1–§3, §5. Live on rc434.
- **§4's T/V split is standard spectral theory**, not a measurement of this code — I did not numerically verify the DST diagonalisation of the constant-diagonal T here. The claim that H needs a general solve *is* verified by the code's behaviour, but the reason given is textbook.
- **Cost curve sampled at n_grid ∈ {40,60,80,120}**; the shipped default is 400 and I did **not** time it — the extrapolation is stated as "superlinear, and the default is 3.3× beyond the largest sampled," not as a number.
- **Three fix directions named, none built or benchmarked.** (a)/(b)/(c) are structural observations; I have not demonstrated that a sparse tridiagonal path or a real-symmetric solver is actually faster *in this codebase*, only that the current one does provably unnecessary work.
- **The descriptor declares V, not H.** It is not a replacement for `hydrogen_radial` and does not reproduce its spectrum.
- **§6 is [SPECULATIVE] and single-instance.** Marked so it is not later cited as a cross-domain result.
- **One bug of mine, fixed:** the first probe called `build_H(400)` *inside* a 160,000-iteration comprehension, rebuilding a 400×400 matrix per cell. Hoisted. The measurement was never wrong, only unrunnable.

Composes **F1337** (index lane = abelian/order-blind — *the circulant case is the index lane in its pure form*), **F1338** (`(frame, lane)` — *this op declares neither*), `[[user_stance_pi_as_projection]]`, `[[feedback_prefer_config_driven_toml_classes]]`, gh **#1530**.
