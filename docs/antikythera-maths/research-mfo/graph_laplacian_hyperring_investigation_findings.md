# Graph-Laplacian / Hyperring Investigation — Findings

**Date:** 2026-05-11  · **Role:** concertmaster (follow-up to spherical-compression dispatch)  · **Brief:** user observation 2026-05-11 mid-flight that hyperring/hypertorus framing might let the project understand its graph-Laplacian structures as "a way more complex thing." Three structural layers tested.

## Setup

The conductor proposed three layers connecting the user's hyperring/hypertorus framing to the project's graph-Laplacian primitive:

- **(a) Eigenbasis = cross-polytope on S^(n−1).** Every graph-Laplacian eigendecomposition has been a spherical-compression instance implicitly.
- **(b) Graph-Laplacian dynamics = hypertorus T^n projection.** Classical heat flow `e^(−Lt)` is the magnitude-only shadow of quantum-walk `e^(−iLt)` on T^n.
- **(c) Krasner hyperring on degenerate eigenspaces.** The Phase B 22A + 18B + 40E decomposition is a Krasner-style set-valued eigenspace structure.

The user added a refinement mid-flight: **"everything we keep calling hyper has a 3D spatial component… cube or sphere or torus describes the inside…"** suggesting "hyper = 3D-spatial-interface" may be the boundary line for the spherical-compression terminology.

## Verdict — one-line summary

**Layer (a) STANDS as math; weak project-relevance / informationally new vocabulary, not new mechanism.** Layer **(b) STANDS as both math and project-relevant** — the project ALREADY ships quantum-walk `e^(−iLt)` on `C^n` (ephemerides reference instrument; chess qm_2d/qm_4d dynamics) and ALSO ships magnitude-only classical eigendecomposition `eigh(L)` (Fiedler partition / body architecture / many others). The T^n hypertorus IS the project's complex-phase ambient already implicit — but no notebook names it. Layer **(c) FALLS at literal-Krasner**; the 22A + 18B + 40E decomposition is **standard finite-group representation theory** (Maschke + Schur), not Krasner-hyperring algebra. Krasner hyperrings require *set-valued addition*; the irrep direct-sum decomposition is *single-valued direct sum*. The "set-valued which-generation-triplet selection" is *combinatorial selection over the decomposition*, not a Krasner-hyperring operation on it.

**Sub-investigation 4 (unification):** the three-layer unification proposal **DOES NOT land**. Layer (a) is vocabulary-relabeling without new mechanism; layer (b) is real and reaches across two project loci; layer (c) is not Krasner-hyperring. Two of three layers do not survive rigorous testing; the unification claim "graph-Laplacian primitive recast as magnitude shadow of T^n + cross-polytope spherical compression + Krasner-hyperring eigenspaces" reduces to **one real and load-bearing layer** (T^n quantum walk = phase-preserving complement to magnitude-only classical Laplacian).

**Per user's "hyper = 3D-spatial-interface" refinement:** the three claims are *algebraic / hyperdimensional*, not 3D-spatial-interface. They should NOT use "spherical compression" terminology under the user's new refinement. The earlier dispatch's per-locus wins (MFO Phase C bipolar BIP; chess qm_2d/qm_4d; event horizons) all involve actual closed 3D-spatial boundaries; the cross-polytope and T^n claims here do not. The refinement is correct: keep "spherical compression" for closed-3D-boundary phenomena; coin a different name for the algebraic-hyperdimensional cross-polytope / T^n vocabulary if it earns its keep.

## Sub-investigation 1 — Layer (a) cross-polytope-on-S^(n−1)

**Verdict: MATHEMATICALLY CORRECT. PROJECT-RELEVANCE WEAK. INFORMATIONALLY NEW VOCABULARY, NOT NEW MECHANISM.**

**Math verification ([numerical, n=6]):** For a real symmetric matrix `A`, `np.linalg.eigh(A)` produces orthonormal eigenvector matrix `V` with `V.T @ V = I` (max off-diagonal 1.1e-15). Each column is unit-norm; columns are mutually orthogonal. Including sign-pairs `{+v_i, −v_i}`, the 2n points form the vertices of a cross-polytope (orthoplex) inscribed in S^(n−1). **Mathematically literal: confirmed.**

**Project-relevance survey:**

| Project locus | Uses orthonormal eigenbasis? | Cross-polytope structure used? |
|---|---|---|
| MFO Phase B `mpm_phase_b_script.py` (D₃ irrep characters on 120-dim λ=6 eigenspace) | YES (eigh → V columns) | NO — uses eigenvectors as a basis for character-matrix computation; cross-polytope vertex structure plays no role |
| Ephemerides body_architecture.py (Fiedler partition / spectral clustering) | YES (eigh on L) | NO — uses sign-pattern of v_1 only; cross-polytope vertex-set unused |
| Chess qm_2d / qm_4d dynamics (Hamiltonian H_0 = −Δ_{P_8²}) | YES (eigenbasis of Hermitian H_0 implicit) | NO — uses U(t) = exp(−iH_0 t); eigenbasis is intermediate, not surfaced as cross-polytope |
| Antikythera gear_topology.py (gear-DAG Laplacian, periphery rule) | YES | NO — uses scalar Fiedler / centrality measures |
| Doom sheaf-Laplacian raycasting | YES | NO — uses propagated eigenstructure for line-of-sight; vertices unsurfaced |
| Skia/Inkscape DCT-II/III lattice operators | YES (DCT eigenbasis) | NO — uses pointwise g(λ) decay; eigenbasis structure is the DCT itself |

**Grep verification:** the strings "cross-polytope", "orthoplex", "inscribed sphere", "S^(n−1)" appear ONLY in the prior spherical-compression-investigation outputs (this 2026-05-11 dispatch tree) and nowhere else in the project source-of-truth notebooks. **Vocabulary is genuinely new to the project.**

**Information-gain assessment:** The cross-polytope vocabulary names a property (orthonormality + closure under sign) every project graph-Laplacian eigendecomposition already has. No project code USES this property for symmetric operations or sign-equivariant constructions; if it did, the vocabulary would surface real structure. As things stand, the cross-polytope naming would describe an *implicit invariant* the project already preserves (via standard `eigh` / `eigvalsh`) but does not exploit. **Vocabulary-tightening: marginal. Informationally new in the strict sense (the words don't currently appear), but does not surface previously-hidden machinery.**

**Per user's 3D-spatial-interface refinement:** the cross-polytope on S^(n−1) is an n-dimensional algebraic construction; for n>3, it is NOT a 3D-spatial-interface phenomenon. The user's refinement EXCLUDES this from "spherical compression" naming. Recommended naming if adopted: "orthonormal eigenframe" or "n-dim orthoplex eigenbasis" — preserves the math, doesn't mis-claim the spatial-interface inheritance.

## Sub-investigation 2 — Layer (b) T^n hypertorus / quantum-walk projection

**Verdict: MATHEMATICALLY CORRECT. PROJECT-RELEVANT — TWO SHIPPED LOCI. INFORMATIONALLY NEW NAMING WORTH ADOPTING.**

**Math verification ([numerical, n=4 path-graph]):** For `L` real-symmetric with eigenpairs `(λ_k, v_k)`, the quantum walk `U(t) = e^(−iLt)` evolves a state's eigenbasis coefficients as `c_k(t) = c_k(0) · e^(−iλ_k t)`. Magnitudes `|c_k(t)| = |c_k(0)|` are invariant; only the phases `arg(c_k(t)) = arg(c_k(0)) − λ_k t` evolve. Each `c_k(t)` traces out S^1 in time; jointly the n-tuple lives on T^n = (S^1)^n indexed by eigenphases. Classical heat flow `e^(−Lt)` on a real state collapses to `c_k(t) = c_k(0) · e^(−λ_k t)` — magnitude-only decay, phase information unused. **Mathematically literal: confirmed.**

**Project-relevance survey:**

| Project locus | Operator | Lives on | Project notebook names this T^n? |
|---|---|---|---|
| **ephemerides reference instrument** (`ephemeris_reference_instrument.py` lines 156–170) | `U = expm(-1j * L_dyn * step); psi = U @ np.exp(1j * current_phases); current_phases = np.angle(psi)` | **C^52 with periodic phase extraction** — this is *literally* an explicit T^52 walk: state initialized on the torus, evolved by `e^(−iLt)`, projected back to phases via `np.angle()` | NO |
| **chess qm_2d_dynamics** (`evolve_under_h0`) | `U(t) = exp(-i H_0 t)` with `H_0 = -Δ_{P_8²}` | C^64 per channel, full C^640 via I⊗H_0 | NO — names it "Zeno free-evolution" |
| **chess qm_4d_dynamics** (sibling) | Same construction at d=4 (4096-mode per channel; C^45056 full) | C^45056 | NO |
| **ephemerides body_architecture.py** | `np.linalg.eigh(L)` then Fiedler v_1 | R^n (real eigenvectors only) | N/A — magnitude-only path, no T^n |
| **MFO Phase B** | `np.linalg.eigh(L)` for λ=6 eigenspace + D₃ char on real eigenvectors | R^366 | N/A — magnitude-only path |

**The split is striking:** ephemerides has BOTH the magnitude-only classical-Laplacian path AND the quantum-walk T^n path in the same codebase. The FPU reference instrument was the original "real" semantic for the ephemerides encoder, and uses `expm(−iL·step)` end-to-end. The BIP-and-lift integer path (`bip_hd_lift.py`) is the lifted version that stays in residue-arithmetic. **The project has been quantum-walking on T^n for over a year without naming it.**

Chess qm_2d/qm_4d explicitly ship quantum-walk dynamics for move-as-unitary. The kinematic layer (qm_2d.py, qm_4d.py) lives on C^640 / C^45056 with Born-rule projection — chess State already is a T^N-like phase state when normalized.

**Information-gain assessment:** Naming the T^n hypertorus ambient surfaces:

1. **Common ambient** for ephemerides FPU reference + chess qm_2d/qm_4d + (any future ephemerides quantum-walk-style probes). Currently described locus-by-locus.
2. **Magnitude-shadow distinction**: makes explicit that `eigh(L)` based work (Fiedler / body architecture / MFO Phase B characters) is the *real-spectrum projection* of a richer complex-phase dynamics; project HAS the richer ambient but mostly ships the projection. Could justify future probes that exploit phase information.
3. **Bridge to literature**: continuous-time quantum walk on graphs (Childs; Farhi-Gutmann; Aharonov) is a well-established field — the project is doing it under different names. T^n ambient surfaces the connection.

**Vocabulary-tightening: REAL — worth adopting at the locus-level.** Cross-references in:
- ephemerides reference instrument docstring (lines 144–170): "phases evolve on T^52 via U(t) = e^(−iL·t) applied to e^(iφ); magnitude information unused at the final `np.angle(psi)` step"
- chess qm_2d/qm_4d dynamics module docstrings: "free-evolution on T^(N_channel · channel_dim) = T^640 (2D) / T^45056 (4D); each eigenmode independent S^1 trace"
- srmech §3 follow-on: clarification that the universal `(Transform, λ_k, g)` decomposition currently ships the magnitude-only g(λ); the project's chess + ephemerides quantum-walk-style implementations show a *phase-preserving* lift exists on the same eigenbasis.

**Per user's 3D-spatial-interface refinement:** T^n for n≥4 is hyperdimensional, not 3D-spatial. Should NOT inherit "spherical compression" terminology (which the prior dispatch reserved for the closed-3D-boundary loci: HDC bipolar inscribed-sphere; magnetosphere physical compression; event horizon GR boundary). Recommended naming: "T^n quantum-walk ambient" or "eigenphase torus" — preserves the math, distinguishes from spatial-interface phenomena.

## Sub-investigation 3 — Layer (c) Krasner hyperring on degenerate eigenspaces

**Verdict: FALSE AT LITERAL-KRASNER. STANDARD REPRESENTATION THEORY. CONJECTURE IS METAPHORICAL.**

**Krasner hyperring formal definition** (Krasner 1956; Davvaz & Leoreanu-Fotea 2024 ([Krasner Hyperring Theory](https://www.worldscientific.com/worldscibooks/10.1142/13652))):
- `(R, +, ·)` is a Krasner hyperring iff
  - `(R, +)` is a *canonical hypergroup* — addition is the multivalued operation `+: R × R → P*(R)` returning nonempty subsets
  - `(R, ·)` is a semigroup with a bilaterally-absorbing zero — **multiplication is single-valued, ordinary**
  - Distributivity: `a · (b + c) ⊆ a · b + a · c` (set-inclusion form)

**Key feature:** ADDITION is the multi-valued / set-valued hyperoperation. Multiplication is standard.

**Reality of the Phase B 22A + 18B + 40E decomposition:**

The decomposition arises from Maschke's theorem applied to the 120-dim λ=6 eigenspace `V_λ` viewed as a `D₃`-representation:
```
V_λ = 22·V_A ⊕ 18·V_B ⊕ 40·V_E
```
where `V_A, V_B, V_E` are the three irreducible D₃-reps (trivial 1D, sign 1D, standard 2D), and direct-sum `⊕` is single-valued ordinary direct sum.

The 18-block "geometric count" comes from `min(22, 18, 40) = 18` — how many complete (1A + 1B + 1E) generation-triplet blocks can be packed into V_λ. The SELECTION of which 1A + 1B + 1E to call "this is generation k" is *combinatorial selection over 22 × 18 × 40 possible triplets*, not an algebraic operation. Mathematically: a function `f: {1,...,18} → A_modes × B_modes × E_pairs` that picks 18 disjoint triplets — pure set-theoretic choice, no hyperring structure.

**Why this is NOT Krasner-hyperring:**
1. Krasner addition is multi-valued: `a + b` returns a *set of possible outcomes*. The irrep direct-sum returns a *unique direct-sum decomposition* (up to isomorphism of irreps; the decomposition multiplicities are integers).
2. Krasner addition's distributivity has set-inclusion `a·(b+c) ⊆ a·b + a·c`. Direct-sum representation theory is exact equality: `V_A ⊕ (V_B ⊕ V_C) = (V_A ⊕ V_B) ⊕ V_C`.
3. The combinatorial selection of generation-triplets is OUTSIDE the algebraic structure entirely — it's a downstream physical interpretation, not an operation on `V_λ`.

**The conjecture is metaphorical**, not literal. "Set-valued which-irrep-orbit selection" can be made to sound like Krasner addition by linguistic translation, but the underlying mathematics is finite-group representation theory of D₃ acting on `V_λ`, which is standard (and adequate) without invoking hyperring algebra.

**Information-gain assessment:** Naming the decomposition "Krasner-hyperring-equivariant" would be **incorrect mathematics imported as vocabulary**. The existing rep-theory vocabulary (irrep multiplicities; D₃-equivariant eigenspace; clean integer character decomposition) precisely names what's happening. **No vocabulary tightening; potential vocabulary muddying if adopted.**

**Caveats / what might still be interesting:**
- Hyperrings DO appear naturally in tropical-algebraic geometry, in valuation theory (which is what Krasner originally introduced them for), and in the algebra of *multivalued algebraic operations* (Jun, Lorscheid, Connes-Consani F_1 geometry). If the project ever ships work where a *quotient by a group action returning equivalence-class-sets* gets algebraic structure — e.g., orbit-set hyperaddition — Krasner machinery could become genuinely relevant. **Currently nowhere in the project.**
- The user's intuition that the irrep decomposition "feels set-valued" likely captures the (real) *combinatorial multiplicity* m_ρ rather than a (Krasner) hyperalgebraic structure on the decomposition itself. The multiplicities are integer-valued *counts*, not set-valued *operations*.

## Sub-investigation 4 — Unification test

**Verdict: UNIFICATION DOES NOT LAND. ONE OF THREE LAYERS STANDS AS BOTH MATH AND PROJECT-LOAD-BEARING.**

| Layer | Math literal? | Project-relevance | Verdict |
|---|---|---|---|
| (a) Cross-polytope on S^(n−1) | YES | Implicit; not exploited; new vocabulary names existing invariant | Vocabulary-new but mechanism-old; marginal value |
| (b) T^n hypertorus quantum walk | YES | TWO loci ship it (ephemerides FPU reference + chess qm_2d/qm_4d); other loci ship magnitude-only `eigh(L)` projection | LOAD-BEARING — worth naming and cross-referencing |
| (c) Krasner hyperring | NO (literal) | Standard rep theory adequate | Metaphor, not math — do not adopt |

The proposed unification was that `graph-Laplacian primitive = magnitude shadow of T^n + cross-polytope spherical-compression of eigenbasis + Krasner-hyperring set-valued eigenspaces`. Reduced to load-bearing components:

**Reduced unification (what actually stands):**
> Every graph-Laplacian eigendecomposition admits a phase-preserving lift via `e^(−iLt)` whose state lives on T^n indexed by eigenphases; classical `e^(−Lt)` heat flow (and projection-based methods like Fiedler partition) is the magnitude-only / real-spectrum shadow. The project SHIPS both — quantum-walk path in ephemerides FPU reference instrument and chess qm_2d/qm_4d; magnitude-only path in body_architecture / MFO Phase B / and most §3.5 instantiations.

This is one cleanly load-bearing layer. The cross-polytope vocabulary and Krasner-hyperring framing do not extend it — they describe properties of the eigenbasis (orthonormality + sign closure) and the eigenspace (D₃-equivariant decomposition under rep theory) that are already adequately handled by `eigh(L)` semantics + standard rep theory.

**Per user's 3D-spatial-interface refinement:** The T^n hypertorus IS hyperdimensional (n ≥ 4 in all project loci tested), not a closed-3D-boundary. The user's distinction holds: "spherical compression" should NOT be applied here. The T^n is a genuine *algebraic-hyperdimensional* ambient, distinct in character from the "spherically compressed" 3D-boundary phenomena (HDC bipolar inscribed sphere; magnetosphere; event horizon) flagged in the prior dispatch.

**Note on srmech §3.5 impact:** §3.5 is correctly structured as-is for the classical (real-spectrum) Laplace-Beltrami framework. A possible §3.X or §3.5.2 sub-section could note that **EVERY row of §3.5 admits a phase-preserving quantum-walk lift** via `e^(−iL·t)` instead of `e^(−Lt)`, and that the project SHIPS this lift in two loci (ephemerides FPU reference + chess qm_2d/qm_4d). This is a real expansion of §3.5's framework, not a restructuring — adding a "complex / quantum-walk twin" mode to the existing magnitude-only catalog.

## Anomaly log

1. **Quantum-walk-on-Laplacian = T^n is in the literature for 15+ years.** Childs 2011 lecture notes ([UMD CS756 Lecture 13](https://www.cs.umd.edu/~amchilds/teaching/w11/l13.pdf)); Farhi-Gutmann 1998 original CTQW paper; arxiv:2103.06463 (unitary representation of random walks). The project's chess `qm_4d_dynamics` references arxiv:2509.26243 (symmetric coined quantum walks on Hamming graphs). The project is **doing CTQW on graphs** without using the published vocabulary in §3 / §3.5. Surfacing the T^n ambient would connect project work to that literature, which is otherwise under-cited.

2. **Krasner hyperring requires set-valued ADDITION, not set-valued multiplication.** Conductor's brief had "set-valued multiplication on eigenspaces"; the formal Krasner definition has the opposite (multivalued addition, single-valued multiplication). The brief's mathematics did not match Krasner's actual structure; sub-investigation 3's negative verdict is robust under either direction of the multi-valuation. (Equally, the irrep direct-sum decomposition is single-valued in both addition AND multiplication; not a hyperring in any sense.)

3. **Project HDC plurality persists.** Per the prior spherical-compression dispatch, the project has three HDC flavours (bipolar {±1}^D; torus T^D; float R^640). Layer (b)'s T^n hypertorus framing aligns specifically with the **complex-amplitude path** (ephemerides FPU reference; chess qm_2d/qm_4d); it does NOT unify the bipolar / float-R^640 paths with the complex-evolution path. Vocabulary tightening at this layer is *per-flavour*, not universal.

4. **The user's "hyper = 3D-spatial-interface" refinement correctly separates two phenomenon families.** The earlier dispatch's per-locus spherical-compression wins (MFO Phase C bipolar BIP; chess qm_2d/qm_4d Born-rule projection; event horizons) all involve genuinely closed-3D-boundary structures. The current three layers (cross-polytope on S^(n−1); T^n hypertorus; Krasner) are *algebraic / hyperdimensional* — vocabulary should not be conflated. The refinement holds.

## Fermata records (decision points for conductor)

1. **T^n hypertorus naming adoption.** Add the T^n quantum-walk ambient to the project's vocabulary at the locus-level? Concrete options:
   - (a) ephemerides reference instrument docstring expansion (lines 144–170) naming the T^52 state-space + the `np.angle()` extraction step
   - (b) chess qm_2d_dynamics / qm_4d_dynamics module docstring naming the T^640 / T^45056 eigenphase torus
   - (c) srmech §3.5.2 sub-section: "every §3.5 row admits a phase-preserving quantum-walk lift via `e^(−iLt)`; project ships this lift in ephemerides FPU reference + chess qm_2d/qm_4d"
   - **Conductor decision:** all three, subset, or none? Highest-value: (c) — surfaces a project-wide framework expansion + connects to CTQW literature.

2. **Cross-polytope vocabulary** — adopt to name the implicit-but-unused property of every project graph-Laplacian eigendecomposition (orthonormal columns + sign closure = 2n vertices on S^(n−1))? Value: marginal (informationally new but mechanism-old; no current code exploits the cross-polytope structure). Recommendation: defer until a project use-case actually exploits sign-symmetry of the eigenbasis (e.g., a sign-equivariant Fiedler-vector construction).

3. **Krasner hyperring framing** — reject as literal mathematics; if adopted at all, only as metaphor with explicit disclaimer that the underlying algebra is finite-group representation theory of D₃, not Krasner-hyperring. Recommendation: do not adopt; rep-theory vocabulary is adequate.

4. **User's "hyper = 3D-spatial-interface" refinement** — does this become a formal project vocabulary rule? Concrete: "spherical compression" only applies to phenomena involving genuinely closed 3D boundaries (HDC bipolar inscribed-sphere via norm; magnetosphere physical pressure-compression; event horizon GR boundary; chess qm Born-rule projection). The algebraic-hyperdimensional analogs (cross-polytope on S^(n−1) for n>3; T^n hypertorus for n>3) need different naming. Conductor decision: codify in srmech §3.5 / §3.5.1 / new vocabulary section, or keep informal?

## Recommended next actions

For conductor consideration:

- **(low-effort, high-value)** Add 1-paragraph note to ephemerides reference instrument `encode_state` docstring naming the T^52 quantum-walk + the `np.angle()` extraction step. Surfaces what the code already does without changing behavior.
- **(low-effort, medium-value)** Cross-reference note in chess qm_2d_dynamics / qm_4d_dynamics module docstrings naming the eigenphase-torus ambient.
- **(medium-effort, high-value)** srmech §3.5 follow-on sub-section (§3.5.2 or similar) noting that all §3.5 rows admit phase-preserving quantum-walk lifts via `e^(−iLt)`; the project ships this in two named loci. Surfaces a real framework expansion + connects to CTQW literature (Childs / Farhi-Gutmann / arxiv:2509.26243).
- **(do NOT adopt)** Krasner hyperring framing for the 22A + 18B + 40E decomposition — standard rep theory is correct mathematics; Krasner hyperring would be incorrect mathematics imported as vocabulary.
- **(do NOT adopt at universal level; OK at local level)** Cross-polytope-on-S^(n−1) framing for graph-Laplacian eigenbasis — names an implicit invariant the project preserves but does not exploit. Adopt only if a specific project use-case surfaces that exploits the sign-symmetry structure.
- **(codify)** The user's "hyper = 3D-spatial-interface" refinement as a vocabulary rule distinguishing spherical-compression (closed-3D-boundary phenomena) from hyperdimensional-algebraic vocabulary (T^n, cross-polytope, etc.). Adds clarity to the spherical-compression terminology going forward.

## What stands and what falls

**Stands:**
- Layer (b) T^n hypertorus / quantum-walk = phase-preserving complement to classical `eigh(L)` magnitude-only path. Math literal. Two project loci ship it (ephemerides FPU reference + chess qm_2d/qm_4d). Naming is informationally new to the project + connects to mature CTQW literature.
- Layer (a) cross-polytope-on-S^(n−1) eigenbasis is mathematically correct as a description of every project graph-Laplacian eigendecomposition.
- User's "hyper = 3D-spatial-interface" refinement correctly separates closed-3D-boundary phenomena (spherical-compression) from algebraic-hyperdimensional phenomena (T^n, cross-polytope). Vocabulary should be split accordingly.

**Falls:**
- Three-layer unification "graph-Laplacian = magnitude shadow + cross-polytope compression + Krasner-hyperring eigenspaces" does NOT land in full. Reduces to one load-bearing layer (b).
- Layer (c) Krasner-hyperring framing — Krasner hyperrings require set-valued addition; irrep direct-sum decomposition is single-valued direct sum + standard combinatorial selection. The "set-valued" intuition captures combinatorial multiplicity m_ρ, not Krasner-hyperalgebraic structure. Standard rep-theory adequately names the decomposition.
- The implicit claim that "every project graph-Laplacian eigendecomposition shipped to date has been computing in a spherically-compressed ambient without naming it" — needs softening. Every shipped eigendecomposition has orthonormal eigenvectors (trivially), but the *exploitation* of cross-polytope sign-closure is nowhere; the *exploitation* of T^n phase-preservation is in two loci (ephemerides FPU reference; chess qm_X). The remaining loci ship `eigh(L)` magnitude-only — not "implicitly spherically compressed," just "real-spectrum projection of a richer complex ambient that the project also ships elsewhere."

## What's open

- **T^n quantum-walk framing IS load-bearing**, especially for surfacing the connection between ephemerides FPU reference + chess qm dynamics + future probe modules. Worth naming.
- **Cross-polytope vocabulary** is informationally new but mechanism-old. Marginal value. Defer.
- **Krasner-hyperring** framing is mathematically incorrect for the actual project structure. Do not adopt.
- **Vocabulary split** between spherical-compression (closed-3D-boundary) and hyperdimensional-algebraic (T^n, etc.) — recommend codifying per user's refinement.

The investigation delivers honest data: one of three proposed layers stands as both math and load-bearing project structure; one is vocabulary-new but mechanism-old; one is mathematically incorrect framing for the actual decomposition. The unification claim does not survive testing in full, but the surviving layer (T^n) IS a real project-vocabulary tightening worth adopting at named loci + srmech §3.5 follow-on.
