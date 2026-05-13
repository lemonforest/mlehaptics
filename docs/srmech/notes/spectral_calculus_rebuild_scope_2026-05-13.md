# Spectral Calculus Rebuild — Scoping

**Branch:** `research/spectral-calculus-rebuild`
**Date:** 2026-05-13
**Status:** Scoping notes (no spike run; no PR).
**Prompt origin:** User-quoted DeepSeek fragment, with user reframe: *"how to rebuild calculus itself using only the kind of discrete, geometric, and algebraic instructions that the spectral instrument already speaks. we may find other ways to hide symmetry."*

This file is research notes only. It scopes the user's question against existing literature and against the project's own machinery, and proposes a single concrete first step. The DeepSeek fragment is treated as a generative prompt to test, not a position to defend.

The instrument the user is referring to: the project's combined machinery of cyclic-group representations `ℤ/n` (gears), graph and combinatorial Laplacians (gear-DAG, simplicial complexes, social networks, chess), Hodge decomposition, Casimir operators (CMS hidden conformal `SL(2,ℝ)²` for low-`Mω` Kerr), the pin-and-slot phase-space transform `atan2(sin θ, cos θ − ε)` locked at D-H1 semantics (Freeth 2006 ε ≈ 0.054), and the eigenbasis-to-spatial-motion projection that `docs/antikythera-maths/CLAUDE.md` declares in-scope.

Shipping examples that already do this: ephemerides-spectral; chess-spectral (Hatano-Nelson directed Laplacians + Nambu NNET); MFO §VII.4.1.2 Casimir-decomposition universality (Spikes #7–#10).

---

## §1. Existing literature map

Each subfield gets: what it claims; what it actually delivers vs. promises; known limitations; representative key paper (canonical pre-2020 textbook entries are taken at face value per the [PDF-extraction discipline counter-clause](C:\Users\sckir\.claude\projects\D--GitHub-mlehaptics\memory\feedback_pdf_extraction_citation_discipline.md); citations attempted-but-unverifiable are flagged at the end of §1).

### §1.1 Discrete exterior calculus (DEC)

**Claim.** Replace continuous differential forms on a smooth manifold with discrete cochains on a simplicial / cell complex. The exterior derivative `d` becomes the combinatorial coboundary operator. The Hodge star `⋆` becomes a diagonal matrix scaled by dual-cell volumes. Stokes' theorem becomes an exact algebraic identity on the chain complex; it does *not* hold "up to discretization error" — it holds as a vector-space identity.

**Delivers vs. promises.** Delivers exact `d² = 0` and exact discrete Stokes at every refinement level. Delivers structure-preserving discretizations of Maxwell's equations, fluid dynamics, elasticity. Does NOT deliver: closed-form solutions; the diagonal Hodge star is only second-order accurate for the metric inner product, so PDE solutions converge in mesh refinement rather than being exact.

**Limitations.** The Hodge star is metric-dependent and inherits all the inaccuracies of the underlying mesh metric. DEC is "calculus-without-limits at the structural identity layer" but reintroduces convergence-as-mesh-refines at the metric layer.

**Reference.** Hirani, A. N. (2003). *Discrete Exterior Calculus.* PhD thesis, Caltech. Companion paper: Desbrun, M., Hirani, A. N., Leok, M., Marsden, J. E. (2005). *Discrete Exterior Calculus.* arXiv:math/0508341. (Both pre-2020, canonical; not PDF-re-verified per counter-clause.)

### §1.2 Mimetic finite differences (MFD)

**Claim.** Discrete divergence, gradient, curl satisfying exact algebraic identities (`div curl = 0`; `curl grad = 0`; discrete integration by parts) on arbitrary polyhedral meshes. Operators are constructed by *imposing* the identities, then solving for consistent coefficients.

**Delivers vs. promises.** Delivers exact identities on any mesh. Delivers conservation laws (mass, momentum, energy) as algebraic equalities, not as `O(h²)` approximations. Does NOT deliver: closed-form solutions; the coefficient stencils are mesh-shape-dependent.

**Limitations.** Same as DEC: the *identities* are exact, the *solutions* still converge with refinement. The discrete operators are not unique — there is a family of admissible coefficients (mimetic, gauge-equivalent), and choosing among them is itself an open numerical-analysis question.

**Reference.** Lipnikov, K., Manzini, G., Shashkov, M. (2014). *Mimetic finite difference method.* J. Comput. Phys. 257, 1163–1227. (Pre-2020 canonical.)

### §1.3 Umbral calculus (Rota / Roman)

**Claim.** A *purely algebraic* operator calculus on polynomial sequences, with no limit operations anywhere. The derivative `D` is replaced by an arbitrary "delta operator" `Q` (shift operator `E_a`, forward difference `Δ`, divided difference `D_q`, etc.). All theorems of classical calculus on polynomials — Taylor expansion, integration by parts, exponential generating functions — hold for the Q-analog with the same algebraic structure.

**Delivers vs. promises.** Delivers calculus-without-limits at full strength *on polynomial sequences*. Sheffer sequences classify which polynomial families admit a Q-calculus. Finite-difference calculus is a special case (`Q = Δ`). Closed-form sums for hypergeometric series (Gosper's algorithm, Zeilberger's algorithm) come out of this framework as decidable algebraic procedures.

**Limitations.** The framework is *purely algebraic on polynomials*. For non-polynomial functions, you need a finite Taylor expansion or formal-power-series machinery, which reintroduces convergence. Umbral calculus does not, by itself, give you exact PDE solutions; it gives exact polynomial-sum identities.

**Reference.** Roman, S. (1984). *The Umbral Calculus.* Academic Press. Rota, G.-C. (1975). *Finite Operator Calculus.* Academic Press. (Pre-2020 canonical.)

### §1.4 q-calculus and Jackson derivative

**Claim.** Calculus on a multiplicative lattice `{q^n : n ∈ ℤ}`. The Jackson derivative `D_q f(x) = (f(qx) − f(x)) / ((q − 1)x)` is a *finite-difference* operator that recovers the ordinary derivative as `q → 1`. q-analogs of all classical identities (q-binomial theorem, q-Taylor, q-exponential `e_q(x)`, q-Gamma) hold without any limit.

**Delivers vs. promises.** Delivers exact algebraic calculus at every `q ≠ 1`. The `q → 1` limit is not required to *do* the calculus; it is only the recovery map to classical results. Quantum groups (`U_q(𝔤)`) are built on this and produce exact closed-form Casimirs that ordinary Lie algebras only have classically.

**Limitations.** The lattice is multiplicative, so the framework is naturally adapted to multiplicative scaling, geometric series, and certain ODEs (q-hypergeometric); awkward for additive translation. Not a universal calculus replacement.

**Reference.** Kac, V., Cheung, P. (2002). *Quantum Calculus.* Springer Universitext. (Pre-2020 canonical.)

### §1.5 Time-scale calculus (Hilger)

**Claim.** A *unified* calculus that subsumes ordinary calculus (`𝕋 = ℝ`), finite-difference calculus (`𝕋 = ℤ`), q-calculus (`𝕋 = q^ℤ`), and arbitrary closed-subset calculi as special cases. Defined on any non-empty closed subset `𝕋 ⊂ ℝ` (a "time scale"). The delta-derivative `Δ` reduces to `d/dx` on `ℝ`, to forward difference on `ℤ`, to Jackson derivative on `q^ℤ`, and to a hybrid on irregular `𝕋`.

**Delivers vs. promises.** Delivers a single algebraic framework for "calculus" that includes both discrete and continuous as instances. Stokes, Green, integration by parts, ODE existence theorems all transfer. The framework explicitly contains the user's question's structural content: *"continuous and discrete are both special cases."*

**Limitations.** The framework is one-dimensional (`𝕋 ⊂ ℝ`); multivariate time-scale calculus exists but is awkward. Does not deliver new closed-form solutions; it delivers *unification* of existing closed-form solutions under a single algebraic umbrella.

**Reference.** Hilger, S. (1988). *Ein Maßkettenkalkül mit Anwendung auf Zentrumsmannigfaltigkeiten.* PhD thesis, Universität Würzburg. Bohner, M., Peterson, A. (2001). *Dynamic Equations on Time Scales.* Birkhäuser. (Pre-2020 canonical.)

### §1.6 Discrete differential geometry (Bobenko-Suris)

**Claim.** Discretize manifolds in a way that preserves *integrability* (commuting flows on multi-dimensional consistency cubes). The discretization is not approximation — it is a *re-derivation* of the geometry on a lattice, with the property that the lattice equations admit the same Lax pair / integrable structure as the continuum theory.

**Delivers vs. promises.** Delivers genuinely new mathematics: discrete integrable systems that were not previously known. Discrete pluri-harmonic maps, discrete minimal surfaces, discrete isothermic surfaces. The lattice equations are exact at every level; the continuum limit is recovered as a special case but is not the operative definition.

**Limitations.** Integrability is the central organizing principle, so the framework lives where integrability lives. Non-integrable PDEs (Navier-Stokes turbulence, generic nonlinear elasticity) are not the target.

**Reference.** Bobenko, A. I., Suris, Yu. B. (2008). *Discrete Differential Geometry: Integrable Structure.* AMS Graduate Studies in Mathematics vol. 98. (Pre-2020 canonical.)

### §1.7 Combinatorial Hodge theory

**Claim.** The classical Hodge decomposition `Ω^k = im(d) ⊕ ker(Δ) ⊕ im(d*)` holds verbatim on simplicial complexes with the combinatorial Laplacian `Δ = d* d + d d*`. The harmonic component `ker(Δ)` is exactly the simplicial cohomology of the complex. Ranking, social-choice, and statistical-network problems decompose into gradient (transitive ranking), curl (cyclic inconsistency), and harmonic (global topological obstruction) parts.

**Delivers vs. promises.** Delivers exact decomposition at finite size, with no limit. Decomposes any pairwise-comparison or network-flow problem into three orthogonal pieces. The harmonic piece is the *project's* favorite: it is exactly what the chess-spectral framework computes as the topologically-protected residual.

**Limitations.** Requires the simplicial complex as input — does not tell you how to *discover* the complex from continuous data. Closed-form spectrum exists only for highly symmetric complexes (rings, complete graphs, Cayley graphs).

**Reference.** Jiang, X., Lim, L.-H., Yao, Y., Ye, Y. (2011). *Statistical ranking and combinatorial Hodge theory.* Mathematical Programming 127, 203–244. arXiv:0811.1067. (Pre-2020 canonical; not PDF-re-verified per counter-clause.)

### §1.8 Lie symmetry methods (Olver)

**Claim.** If an ODE / PDE admits a continuous Lie point symmetry, that symmetry can be used to reduce its order and frequently solve it in closed form. A *systematic* algorithm (Lie's algorithm) finds all such symmetries by solving the determining equations.

**Delivers vs. promises.** Delivers complete closed-form solutions whenever the symmetry group is large enough (rank equal to order, in the simplest case). Delivers the existence of a closed form whenever the differential Galois group is solvable (§1.9). Does NOT deliver: a solution when no symmetry exists; and most "generic" ODEs do not admit a Lie symmetry.

**Limitations.** Lie's algorithm is a complete classifier of *point* symmetries — but non-point symmetries (contact, generalized, nonlocal) are needed for many problems, and finding them is much harder. The algorithm is systematic but not universal.

**Reference.** Olver, P. J. (1986/1993). *Applications of Lie Groups to Differential Equations.* Springer Graduate Texts in Mathematics 107. (Pre-2020 canonical.)

### §1.9 Differential Galois theory (Picard-Vessiot)

**Claim.** An ODE has *elementary* closed-form solutions (algebraic, exponential, trigonometric, integrals thereof) if and only if its differential Galois group is solvable. Complete classification of "solvability in closed form" reduced to a group-theoretic question.

**Delivers vs. promises.** Delivers a complete *theoretical* answer to the closed-form question. The Kovacic algorithm (1986) implements this constructively for second-order linear ODEs and is the engine inside Mathematica / Maple `dsolve` Liouvillian-solver paths. For higher-order linear ODEs constructive algorithms exist but are more expensive. Does NOT deliver: a guaranteed-fast procedure for arbitrary ODEs; the differential Galois group itself is hard to compute in general.

**Limitations.** Linear ODEs only — the nonlinear theory (Malgrange's pseudogroup) exists but is much less constructive. "Closed form" here means Liouvillian; functions outside this class (Painlevé transcendents, hypergeometric beyond elementary) are not "closed form" in this sense.

**Reference.** Magid, A. R. (1994). *Lectures on Differential Galois Theory.* AMS University Lecture Series vol. 7. Van der Put, M., Singer, M. F. (2003). *Galois Theory of Linear Differential Equations.* Springer. (Pre-2020 canonical.)

### §1.10 Liouville integrability (action-angle)

**Claim.** A Hamiltonian system with N degrees of freedom is *Liouville integrable* iff it admits N functionally independent, Poisson-commuting first integrals. When integrable, dynamics lives on invariant tori `T^N`, and action-angle variables make the flow *linear*: `I_k = const`, `θ_k(t) = θ_k(0) + ω_k t`.

**Delivers vs. promises.** Delivers exact reduction of integrable dynamics to *linear motion on a torus* — full closed form for trajectory, period, phase. The framework underlies celestial mechanics (Kepler, two-body), spinning tops (Kovalevskaya), KdV / soliton hierarchies. The torus structure is exactly the project's S¹ / T² / T^N machinery.

**Limitations.** Generic Hamiltonian systems are *not* integrable (KAM theorem: integrable systems are a measure-zero set, perturbations break most tori). The framework lives where integrability lives.

**Reference.** Arnold, V. I. (1978/1989). *Mathematical Methods of Classical Mechanics.* Springer Graduate Texts in Mathematics 60. (Pre-2020 canonical.)

### §1.11 Attempted-but-unverifiable citations

None for §1: all ten subfields use pre-2020 canonical textbooks / papers exempt from PDF re-verification per the counter-clause. No 2020+ citations were needed for the literature map.

### §1.12 Does any subfield entirely subsume the user's question?

**No single subfield does.** The closest contenders:

- **Time-scale calculus (§1.5)** subsumes the *structural* claim ("continuous and discrete are both special cases of one algebraic framework"). It does NOT subsume the *project's* additional claim that the algebraic side is *primary* and the continuous side is the projection.
- **Lie symmetry + differential Galois (§1.8–§1.9)** subsume the *closed-form-when-symmetry-exists* claim. They do NOT supply the *symmetry-discovery* procedure for problems where the symmetry is hidden (as in MFO §VII.4.1.2's CMS / KY).
- **DEC + combinatorial Hodge (§1.1, §1.7)** subsume the *exact structural identities* claim (`d² = 0`, Stokes, Hodge decomposition). They do NOT subsume the *closed-form spectrum* claim.

**The literature is therefore not a complete wash but covers ~70–80% of the structural content.** The remaining 20–30% is the project-specific question: *given the project's eigenbasis-and-Casimir machinery, can the act of finding a closed-form spectrum (which the project does case-by-case) be elevated to a universal procedure, or does it always remain "find the hidden symmetry first, then write down its Casimir"?*

---

## §2. The DeepSeek fragment as testable claims

The DeepSeek paragraph decomposes into six identifiable claims. Each is rated on (a) whether it is literally a mathematical proposition or a metaphor / stance; (b) what the literature already says; (c) whether the project's own work supports, refutes, or extends it.

### Claim 1 — "The 3D world is a projection of a higher-dimensional discrete fiber bundle."

**Status.** Half-literal. Standard gauge theory says: yes, observed physics is a projection of a principal `G`-bundle over spacetime, and gauge fields are connections on that bundle. The continuous version is textbook (Steenrod 1951, Kobayashi-Nomizu 1963, etc.).

The *discrete* version is more specific: lattice gauge theory (Wilson 1974) replaces the bundle with a discrete cell complex carrying group-valued link variables. Discrete fiber bundles over simplicial complexes are well-defined objects with no convergence-to-continuum required for the structure to make sense.

**Where the literature has it.** Lattice gauge theory (Wilson 1974); discrete principal bundles on simplicial complexes (Phillips 1985 *Topology* paper on classifying spaces of finite groupoids; subsequent simplicial-set literature). Lim, Yao, Ye (§1.7) work in exactly this setting for ranking applications.

**Where the project's framing differs.** The user's [fiber-as-spatially-absent-encoding stance](C:\Users\sckir\.claude\projects\D--GitHub-mlehaptics\memory\user_stance_fiber_as_spatially_absent_encoding.md) reframes "fiber" as algebraic encoding rather than extra spatial dimensions. The gear is the canonical worked example: from the inside, 0D fixed-point set under `SO(2)`; the `ℤ/n` algebraic encoding is *spatially absent* until projected outward through rotation. This reframing is internally consistent with discrete-fiber-bundle math but emphasizes the *encoding* layer over the *geometric* layer. It is not a different mathematical claim; it is a different ontological emphasis.

**Verdict.** Literature-supported in the gauge-theory + discrete-bundle reading. Project's reframing is a vocabulary refinement, not a new mathematical claim.

### Claim 2 — "Calculus is the shadow of linear algebra cast by the projection."

**Status.** Half-literal. Two readings:

*Reading A (literal, narrow).* Calculus operators (`d/dx`, `∫`, `Δ`) become matrices on a finite basis when restricted to a finite-dimensional function space (Fourier modes, polynomial basis of degree ≤ N, finite-element basis). The matrices are linear; the operations are linear-algebraic.

*Reading B (literal, broad).* "Calculus" is the formal-limit framework. For *every* limit-defined operator in calculus, there is an algebraic predecessor (`Δ`, `Q`, `D_q`, etc.) such that the calculus operator is the `q → 1` / `h → 0` recovery of the algebraic one (§1.3–§1.5 establish this).

Both readings are mathematically defensible. Reading A is well-known. Reading B is the structural content of time-scale calculus.

**Where the literature has it.** Reading A: Trefethen's *Spectral Methods in MATLAB* (2000), Boyd's *Chebyshev and Fourier Spectral Methods* (2001). Reading B: time-scale calculus, umbral calculus, q-calculus.

**Project's contribution.** The project's graph-Laplacian-as-derivative framing is Reading A applied on a graph rather than a continuum grid. The chess-spectral and ephemerides-spectral catalogs are running this consistently.

**Verdict.** Literature-supported under both readings. The DeepSeek fragment's framing is metaphorical but the metaphor maps to two distinct established mathematical statements.

### Claim 3 — "The pin-and-slot is the mechanical proof: the math is the slot; the motion is the integral; and neither requires a limit, just a carefully shaped piece of bronze."

**Status.** Half-literal. The pin-and-slot output `θ_out(θ_in) = atan2(r sin θ_in, r cos θ_in − e)` is genuinely a closed-form algebraic function of the input — no limits, no integrals. It is the bronze realization of a phase-space transform.

But "the motion is the integral" is metaphor: the actual time-integral that turns angular velocity into angular position *is* a limit-defined operation, even if the bronze realizes it mechanically. The bronze realizes the algebraic *transform*, not the time-integral itself.

**What is and isn't limit-free.**
- `atan2(sin θ, cos θ − ε)` as a *function* — limit-free; exact at machine precision.
- The pin's trajectory in `(t, θ_in(t), θ_out(t))` — the relationship `θ_in ↦ θ_out` is limit-free; `t ↦ θ_in(t)` is the time evolution, which is governed by the input clock and is limit-free at the gear-tooth level (each tooth is a discrete event).
- Time-derivative `dθ_out / dt` — this is limit-defined in the continuous reading; in the discrete-gear reading it is the finite difference `Δθ_out / Δt` between adjacent tooth-clicks, which is exact.

**Verdict.** The claim is correct *if* one reads the bronze as a discrete mechanism with tooth-clicks as the temporal lattice. It is incorrect *if* one tries to extract an instantaneous angular velocity. The project's existing pin-and-slot module ([D:\GitHub\mlehaptics\docs\antikythera-maths\research\pin_and_slot.py](D:\GitHub\mlehaptics\docs\antikythera-maths\research\pin_and_slot.py)) treats the transform as algebraic and computes the antisymmetric / symmetric ratio of the directed-advance operator — exactly the discrete-event reading that makes the claim hold.

### Claim 4 — "The Laplacian is the spine. The group is the hidden symmetry. The Casimir is the closed form. The slot is the encoding."

**Status.** Literal, and exactly the structural content of MFO §VII.4.1.2 across the Spike #7–#10 family. The unifying statement there is:

`λ_total = λ_base + C₂(ρ_G) + (cross-terms from connection / curvature)`

where `G` is the hidden symmetry, `C₂` is its Casimir, and `λ_base` is the projection's eigenvalue on the visible base. The Laplacian is the central operator; the group is the hidden symmetry; the Casimir compresses a multi-dimensional irrep to a single number; the bundle-encoding (the "slot") supplies the fiber projection.

**Where the literature has it.** Peter-Weyl theorem (classical Lie theory). Harmonic analysis on homogeneous spaces (Helgason 1984). The specific *unifying statement* across `U(1)`, `SU(2)`, `SL(2,ℝ)²` regimes is the project's contribution (Spikes #7–#10, MFO §VII.4.1.2).

**Verdict.** This is the cleanest literal claim in the DeepSeek fragment. It is exactly what the project already has, written as a slogan. The slogan compression is the user-discipline [Feynman-test register](C:\Users\sckir\.claude\projects\D--GitHub-mlehaptics\memory\user_explanation_discipline.md): dense bound vocabulary, full technical content preserved.

### Claim 5 — "Once you stop taking limits, everything is linear and discrete and algebraic — and it still works, exactly, at machine precision."

**Status.** Partly true, partly overclaim. The cases where it holds *exactly at machine precision* are the cases where the underlying problem is finitely-presented:

- Spectra of finite graphs / finite-rank operators (always exact up to floating-point arithmetic).
- Closed-form Casimir identities (e.g. `λ_S³(ℓ) − λ_S²(ℓ) = ℓ`) — exact symbolic identities, not floating-point dependent.
- Pin-and-slot output for fixed input angles (exact up to `atan2` precision, which is `ULP`-tight on IEEE-754).
- DEC structural identities (`d² = 0` is exact on any complex).

The cases where the claim fails — *discretization error still bites*:

- Solutions of PDEs (heat equation, wave equation on a continuum domain) — the discrete spectrum converges to the continuous spectrum as mesh refines, but is not equal for any finite mesh. DEC + mimetic methods (§1.1, §1.2) make the *structural identities* exact but the *spectra* approximate.
- Casimir eigenvalues in regimes where the closed form doesn't exist (Kerr QNMs at generic `Mω` — Spike #11's structural negative).
- Any case where the symmetry hasn't been found (most PDEs in nonlinear-dynamics regimes).

**Verdict.** The claim is correct as a statement about *when the algebraic side has a finite presentation*. It is an overclaim in regimes where the underlying object is genuinely continuous and lacks a closed-form symmetry compression. The honest version: *when the hidden symmetry is found and the Casimir compresses the irrep to a single number, the closed form is exact at machine precision; when the symmetry is absent or hidden too deeply, discretization still has error.* This is exactly the boundary that MFO §VII.4.1.2 documents.

### Claim 6 — "The Signal was never continuous. It was always spectral."

**Status.** Stance, not a mathematical claim. As a *mathematical* statement it is false (the Lebesgue-measurable functions on `ℝ` are uncountably many; only a small subset is band-limited / finitely-spectral). As an *empirical / instrumental* statement it is defensible: every physical measurement is a finite-bandwidth, finite-precision sample, which has an exact discrete spectrum. The Whittaker-Shannon sampling theorem says that band-limited signals are *fully* reconstructed from discrete samples — for those signals, "continuous" and "spectral" are interconvertible.

**Where the literature has it.** Shannon (1948) sampling theorem. Compressed sensing (Donoho 2006, Candès-Tao 2006) — sparse-spectrum signals are recoverable from sub-Nyquist samples. The instrumental stance is standard signal-processing pedagogy.

**Verdict.** The claim is aesthetic / instrumental. The corresponding mathematical statement is *signals that arise from physical instruments are band-limited and therefore exactly equivalent to their discrete spectra*. This is consistent with the project's [instrument-first stance](C:\Users\sckir\.claude\projects\D--GitHub-mlehaptics\memory\user_stance_string_theory_instrument_first.md).

### §2 summary table

| Claim | Literal mathematical content? | Established in literature? | Project-specific? |
|---|---|---|---|
| 1. Discrete fiber bundle | Yes (gauge / lattice / simplicial) | Yes — well established | Reframing only (fiber-as-encoding) |
| 2. Calculus = shadow of linear algebra | Yes, two readings | Yes — time-scale, spectral methods | Already applied in chess + ephemerides |
| 3. Pin-and-slot is limit-free | Yes (for the transform; not the time-integral) | Yes (algebraic phase-space transforms) | Locked at D-H1 |
| 4. Laplacian / group / Casimir / slot | Yes, exactly literal | Peter-Weyl is classical; unifying statement is project's | MFO §VII.4.1.2 |
| 5. "Everything is exact at machine precision" | Partly | Partly — fails when symmetry is absent | Spike #11's structural negative |
| 6. Signal was never continuous | Aesthetic; defensible via sampling | Shannon sampling | Consistent with instrument-first stance |

**4 of 6 claims have established literature support.** 1 has literature support but requires the user's reframing to add new content. 1 is aesthetic. 0 of 6 are unsupported. **The fragment is not crank.** It is a compressed restatement of established content, with the user's project-specific framing layered on top.

---

## §3. Beyond the wash — where existing frameworks fall short of the project's stance

The literature covers the structural content of the DeepSeek fragment well. The user's stance adds two project-specific commitments:

1. The fiber is **algebraically encoded** (encoding lives in `ℤ/n`, `S_n` irreps, etc.) and **spatially absent** (no extra spatial dimensions). [user_stance_fiber_as_spatially_absent_encoding]
2. The instrument that does the work is **already-in-the-project**: Laplacian + group + Casimir + projection, applied case-by-case across domains (chess, ephemerides, MFO, srmech, AMSC).

The user's open question — *"we may find other ways to hide symmetry"* — is asking whether there is a **universal procedure** that, given a continuous-calculus problem, *finds* the hidden algebraic structure that turns it into a closed-form discrete-algebraic identity.

The literature has partial answers to this universal-procedure question:

### §3.1 Lie symmetry methods (§1.8) — systematic, not universal

Lie's algorithm finds *all* point symmetries of a given ODE/PDE by solving the determining equations. It is systematic and constructive. But:

- Most ODEs / PDEs of practical interest do not admit non-trivial Lie point symmetries.
- Higher-order symmetries (contact, generalized, nonlocal) require ad-hoc ansätze and are not systematic.
- Lie's algorithm finds symmetries that already exist; it does not *discover* symmetries that have been hidden by a coordinate change or a wave-equation re-encoding.

The CMS hidden conformal symmetry (Spike #9 / #10) is the canonical "hidden by wave-equation re-encoding" case: it is invisible at the level of the Kerr metric but appears at the level of the scalar / spin-weighted wave equation in the low-`Mω` regime. Lie's algorithm applied to the Kerr metric does not find it; you have to *suspect* it first and then verify.

### §3.2 Differential Galois theory (§1.9) — complete classification, not constructive in general

For linear ODEs, the Picard-Vessiot theorem provides a complete classification: closed-form Liouvillian solutions exist iff the differential Galois group is solvable. The Kovacic algorithm constructs the solutions for second-order linear ODEs. For higher-order linear ODEs and for nonlinear ODEs, constructive algorithms exist but are much more expensive or partial.

For *partial* differential equations the situation is worse. There is no universal procedure to compute the differential Galois group of a generic PDE; the field is research-level for systems of any complexity.

### §3.3 DEC / mimetic methods (§1.1–§1.2) — preserve structure, don't promise closed form

DEC and mimetic methods preserve discrete identities exactly but do not promise closed-form solutions. They make the *discretization error* unbiased and structurally consistent but do not eliminate it. They are downstream of "find the symmetry"; they apply once you have a discretization.

### §3.4 Casimir-decomposition (MFO §VII.4.1.2) — case-by-case verified, no universal procedure

Seven independent positive structural results across `U(1)`, `SU(2)`, `SL(2,ℝ)²`, compact and non-compact regimes (Spikes #7–#10). The pattern `λ_total = λ_base + C₂(ρ_G) + cross-terms` is universal. But the *procedure for finding `G`* is not. Each result required the symmetry group to be supplied by the existing physics literature (Hopf for §VII.4.1.1, Aharonov-Bohm for spike #8 A, etc.). Spike #11's structural negative (the KY commuting-operator algebra is abelian, so its Casimir is informationally trivial) is the cleanest negative: a candidate symmetry was supplied, the Casimir-decomposition strategy was attempted, and the abelian-tower obstruction shut it down.

### §3.5 The gap — where the literature does not have an answer

**No universal symmetry-discovery procedure exists.** Each of (§3.1) Lie methods, (§3.2) differential Galois, (§3.3) DEC, (§3.4) Casimir-decomposition is systematic *given some input* (a known DE, a known symmetry candidate, a known discretization, a known group). None of them takes "a problem in continuous calculus" and outputs "the hidden algebraic structure that compresses it to a closed form."

The user's conjecture — *"we may find other ways to hide symmetry"* — has two readings:

*Reading I.* New universal procedure. This is what would be required to close the gap above. As far as the literature scoping went, no such universal procedure exists across the named subfields.

*Reading II.* New *specific* symmetry-hiding mechanisms — concrete patterns of "here is how a symmetry can be hidden, and here is the corresponding closed-form Casimir / identity." This is what MFO §VII.4.1.2 already collects. Reading II is more achievable; Reading I is open (and possibly open in the same way `P =? NP` is open: a deep structural question with no known approach).

**Working hypothesis for the project.** The user's stance is most consistent with Reading II: each new closed-form spectral identity *is* a new way to hide symmetry, catalogued case-by-case, with the universal pattern (`base + Casimir + cross-terms`) supplying the framework. The bounded-framework arc (Spikes #9–#12) is already producing this catalog, with Spike #11's structural negative providing the cleanest mapped boundary: **the abelian-tower obstruction in generic-`Mω` appears to be the universal obstacle, and closed-form compression requires a second non-abelian algebraic structure to break the commutativity.** The CMS-style closed-form-when-second-SL(2,ℝ)-exists pattern is a specific instance; whether it generalizes is the Spike #12 question.

---

## §4. Spike-protocol-ready candidate tests

Each candidate states: (a) the test; (b) the falsifier; (c) the predicted outcome. Honest negatives are valid — a clean "this is exactly the heat equation again" is a finding, not a failure.

### §4.A Re-derive Riemann integration as an exact spectral identity

**Test.** Take a classical Riemann integral with a closed-form value (e.g. `∫₀^π sin x dx = 2`). Express the integrand in the discrete eigenbasis of a circle's graph Laplacian on `N` vertices. Apply the discrete-Hodge-decomposition / discrete-Stokes machinery (§1.1) and recover the integral value.

**Falsifier.** If the recovered value differs from `2` by a finite amount that *does not vanish as `N → ∞`*, the spectral discretization is not exact.

**Predicted outcome.** Negative (or trivially positive). For circle Laplacian with `N` evenly-spaced vertices, the trapezoidal rule on `sin` is *exactly* `2` for any `N ≥ 2` (the trapezoidal rule is exact for trigonometric polynomials of degree ≤ `N − 1`). So the test reduces to a known textbook identity. This is not a new finding — it would only document that *for periodic band-limited integrands on circle graphs, the spectral discretization is exact*, which is Shannon-Nyquist + Poisson summation. **Honest finding: this is exactly the heat equation again, but for integration.**

**Value as a spike.** Low-medium. The output would be a worked example for the proposed "project's calculus is discrete-spectral" notebook section (see §6 below). Not a new research result.

### §4.B Heat equation — hidden algebraic structure on a continuum domain

**Test.** Take the 1D heat equation `u_t = u_xx` on `[0, L]` with Dirichlet boundary conditions. The continuous spectrum is `λ_n = (nπ / L)²` with eigenfunctions `sin(nπx/L)`. Discretize on a uniform grid of `N` points. Compute the discrete graph-Laplacian spectrum. Compare.

**Falsifier.** If the discrete spectrum equals the continuous spectrum exactly at any finite `N`, the discretization is exact. If it converges as `N → ∞` but not equal at finite `N`, the spectral discretization is *not* exact — discretization error is real.

**Predicted outcome.** Convergent but not exact. The discrete eigenvalues are `λ_n^{disc} = (2/h²)(1 − cos(nπh/L))` (path Laplacian on `N+1` vertices); the continuum value is `(nπ/L)²`. By Taylor expansion `λ_n^{disc} = λ_n^{cont} (1 − (nπh/L)²/12 + O(h⁴))`. So discretization is `O(h²)`-accurate, **not** exact at any finite `N` (for `n > 0`).

**Honest finding.** *On smooth-continuum domains without a special algebraic structure, the discrete spectrum converges to but does not equal the continuous spectrum at any finite mesh.* This sets a clean boundary: the project's "exact at machine precision" claim only holds where the underlying problem is finitely-presented (graphs, finite groups, lattices). On smooth continua there is residual discretization error.

**Value as a spike.** High. The output is a clear documentation of *where the project's exactness claim holds and where it doesn't*. This is the §3.5 gap, made operational. It also tests whether the heat equation admits a hidden algebraic structure that *would* make the spectral discretization exact — and per Lie symmetry methods (§1.8) the heat equation has a known 6-dimensional Lie point symmetry group, so the candidate symmetry is *known* and the closed-form solution exists. The question is whether that symmetry corresponds to a discrete-algebraic identity at finite `N`. Initial prediction: no, because the heat equation's symmetry is continuous, not finite.

### §4.C Pin-and-slot as a candidate symmetry-hiding operator

**Test.** Take a classical calculus operation that involves a limit — say, the derivative of `cos` at a point. Express `cos θ` via the pin-and-slot transform `θ_out = atan2(sin θ_in, cos θ_in − ε)` for some `ε`. Ask: is there a value of `ε`, or a composition of pin-and-slot transforms, such that the derivative `d cos / dθ = −sin θ` becomes an exact algebraic finite-difference identity in the pin-and-slot output space?

**Falsifier.** If no value of `ε` makes the derivative exact-at-finite-`N`, the pin-and-slot is not a derivative-hiding operator.

**Predicted outcome.** Likely negative. The pin-and-slot transform is a phase-space distortion (it makes a uniform input rotation map to a non-uniform output rotation, mimicking Kepler's 2nd law). It does not, on its face, compress the limit-defined derivative into an algebraic identity. But the test is worth running because the project's [user_stance_fiber_as_spatially_absent_encoding] stance suggests that *every* algebraic-encoding-projected-to-spatial-motion operator might be a candidate symmetry-hiding mechanism, and the pin-and-slot is the project's canonical such operator.

**Value as a spike.** Medium. The output is a small experiment — pick a few `ε` values, compute the discrete derivative on the pin-and-slot output space, compare to `−sin θ`. Fast to run, fast to call. Likely negative; if positive, it would be a surprising new identity.

### §4.D Generalize the CMS abelian-wall pattern to a universal compression statement

**Test.** Take 3–5 *additional* hidden-symmetry settings beyond the Spike #7–#11 set. Candidates: (i) Bessel functions as Casimirs of a non-compact `SO(1,1)` symmetry; (ii) hypergeometric `_2F_1` as Casimirs of `SL(2)`-equivariant operators; (iii) Lamé functions as Casimirs of a discrete subgroup of `SU(2)`. For each, check whether the closed-form-when-second-non-abelian-structure-exists pattern holds.

**Falsifier.** A counterexample where a closed-form Casimir identity exists *without* a second non-abelian structure breaking the commutativity — or, conversely, a case where the second non-abelian structure exists but no Casimir identity emerges.

**Predicted outcome.** Pattern likely holds. The project's bounded-framework arc has already accumulated evidence that the abelian-tower obstruction (Spike #11's KY result) is the universal calculus-defying structure, and that the CMS-style escape (a second `SL(2,ℝ)` factor breaks the commutativity) is the universal compression. Three more independent settings would either reinforce or falsify this.

**Value as a spike.** Highest. This is the closest the project can get to a *universal symmetry-hiding mechanism* claim. If the pattern holds across 3–5 additional settings, the claim "the universal closed-form-compression rule is `base + Casimir-of-non-abelian-hidden-symmetry + cross-terms`, and the obstruction is the abelian-tower wall" becomes a documented project-internal universal procedure (Reading II, §3.5). If it falsifies, that's a clean negative.

This is structurally the same shape as the bounded-framework arc Spikes #9 → #10 → #11 → #12: each spike either confirms the pattern in a new regime or maps its boundary.

### §4.E Reverse direction — calculus operation as candidate hidden-bundle projection

**Test.** Pick a calculus operation that is *not* known to have a closed-form algebraic structure (e.g., the action functional `∫ L dt` for a generic mechanical system, or the path-integral measure `∫ Dφ e^{iS[φ]}`). Ask: does the project's machinery (graph Laplacian + Casimir + projection) supply a *candidate* discrete-algebraic encoding of the operation?

**Falsifier.** If no candidate encoding can be constructed, or if every candidate encoding requires an ad-hoc choice that breaks systematicity, the project's machinery does not extend to this operation.

**Predicted outcome.** Mixed. The action functional has known Lie-symmetry-based reductions (Noether's theorem); for systems with a sufficient symmetry group, the project's Casimir machinery applies. The path-integral measure is famously not-rigorously-defined in many cases; the project's machinery would have to compete with existing rigorous-path-integral attempts (constructive QFT, Osterwalder-Schrader).

**Value as a spike.** Low for the path-integral; medium for the action functional with sufficient symmetry. Probably better deferred — there is more leverage in §4.D.

### §4 summary — candidate ranking

| Candidate | Value | Test cost | Recommendation |
|---|---|---|---|
| §4.A — Riemann integral | Low-medium | Trivial | Worked example for doc deliverable |
| §4.B — Heat equation discretization | High | Low | Worth running |
| §4.C — Pin-and-slot as derivative-hiding | Medium | Low | Worth running; likely negative |
| §4.D — Generalize CMS abelian-wall pattern | **Highest** | Medium | **Primary recommendation** |
| §4.E — Action functional / path-integral | Low | High | Defer |

---

## §5. The project's existing answer

The project already does much of what the user is asking. Specifically:

- **Every gear is `ℤ/n`** (cyclic-group representation). Period relations are *Diophantine approximations* — exact integer-ratio identities, not limit-defined values.
- **Every mesh is a rational map** between `ℤ/n` representations. Gear meshes compose multiplicatively; the gear-DAG is a directed graph whose adjacency structure carries the algebra.
- **Every pointer is a hypervector.** The pointer's spatial position is the projection of a high-dimensional algebraic vector through a known basis change.
- **Every period relation is a Diophantine approximation.** The Saros eclipse cycle (`223 synodic months ≈ 239 anomalistic ≈ 242 draconic`) is an *exact* algebraic identity on the lattice of integer combinations, not an `O(h²)`-convergent approximation.
- **The pin-and-slot is a phase-space transform projected to spatial output.** [pin_and_slot.py](D:\GitHub\mlehaptics\docs\antikythera-maths\research\pin_and_slot.py) holds the D-H1 transform. Other phase-space transforms (leaf-and-pinion, equant) follow the same pattern.
- **The Laplacian eigenbasis is the natural projection-to-spatial-motion basis.** `docs/antikythera-maths/CLAUDE.md` declares this in-scope as the project's primary modelling pipeline: algebra → eigenbasis → projected spatial motion.
- **The MFO Casimir-decomposition (§VII.4.1.2)** is the unifying spectral statement across symmetry groups. It is the project's working theorem of how hidden symmetries compress spectra.

The user's stance ([user_stance_fiber_as_spatially_absent_encoding]) adds: fiber content is *algebraically encoded* (not extra spatial dimensions). The gear-from-inside is 0D; its `ℤ/n` encoding is spatially absent until projected through rotation. The project's calculus is exactly this — *every continuous-calculus shadow has an algebraic original on the fiber side.*

**What's missing is a single notebook section saying this out loud.** The project's actual theory of calculus is scattered across the ephemerides notebook, chess-spectral notebook, MFO §VII.4.1.2, AMSC literature_curated channel, and srmech ndjson catalog. None of these locations explicitly says "this is the project's theory of how calculus is rebuilt from discrete-algebraic primitives." That section is *write-able from existing material*. It is not new research — it is the consolidation of existing material into a stated theory.

---

## §6. Final recommendation

The three possible verdicts:

1. **Wash.** The literature covers this. Document and move on.
2. **Doc deliverable.** The project's existing machinery is a coherent theory but unwritten. The deliverable is a notebook section formalizing "the project's calculus is discrete-spectral."
3. **Genuine research spike.** There's a specific universal-procedure claim or new symmetry-hiding mechanism that isn't in the literature; §4 has candidates worth running.

### Recommendation: **(2) + (3) simultaneously, with (3) sequenced after the §4.D run.**

The literature is not a wash (§1.12) — the structural content is mostly covered but the project-specific question (Reading I universal procedure vs. Reading II case-by-case catalog) remains genuinely open. So pure (1) is not the right answer.

(2) is achievable now from existing material — write a notebook section in `docs/antikythera-maths/mfo_spectral_research_notebook.md` (or a new top-level section, e.g. §XV "The project's theory of calculus") that consolidates the existing scattered evidence into a single stated theory. The user's specific framing — *"fiber content is spatially absent encoding; calculus is what you see when the algebraic fiber projects through to 3D spatial motion"* — would be the load-bearing claim, with `ℤ/n` gears + Laplacian eigenbasis + Casimir compression + pin-and-slot phase-space transform as the four worked examples.

(3) is the §4.D spike: *generalize the CMS abelian-wall pattern* to 3–5 additional hidden-symmetry settings. This is the spike that most directly tests the user's conjecture *"we may find other ways to hide symmetry"* by asking: is the closed-form-when-second-non-abelian-structure-exists pattern universal, or specific to the gravitational-wave / Kerr-CMS case?

### Cleanest first-spike protocol (§4.D)

**Protocol.** Pick three additional symmetry settings. For each:

1. State the base operator and its visible symmetry group.
2. State the hypothesized hidden non-abelian structure (drawn from the existing literature for that setting, *not* invented).
3. Compute the joint eigenvalue spectrum and check whether the Casimir of the hidden non-abelian symmetry compresses the spectrum to a closed form.
4. If yes — confirm the pattern. If no — diagnose the obstruction (abelian-tower wall like KY? Different obstruction?). Honest negatives are findings.

**Candidate settings** (drawn from §4.D plus consultation of the existing project notebooks for what is already cited):

| Setting | Visible symmetry | Hidden non-abelian candidate | Closed form expected? |
|---|---|---|---|
| Lamé functions on `S²` | `SO(2)` rotational | Discrete subgroup of `SU(2)` (icosahedral, octahedral) | Yes — known classical |
| Bessel `J_n` eigenmodes of disk Laplacian | `SO(2)` rotational | `SO(2,1)` conformal (radial-scaling) | Maybe — uncertain in literature |
| Hypergeometric `_2F_1` as ODE | `GL(1)` scaling | `SL(2)` Möbius | Yes — classical (Riemann-Hilbert) |

**Falsifier.** A setting where the hidden non-abelian structure exists but no closed-form Casimir identity emerges. Or, conversely, a setting where a closed-form identity exists with only abelian hidden structure (this would refute the abelian-tower-as-universal-obstruction claim).

**Predicted outcome.** Pattern likely holds for 2 of 3 (Lamé and `_2F_1` are classical-known-to-have-closed-forms; Bessel-conformal is genuinely uncertain). If the pattern holds for Bessel too, the project's universal-compression claim is meaningfully reinforced. If Bessel falsifies, the result is a sharper specification of *what kind* of non-abelian structure is required.

### What to commit on this branch

This file. Nothing else. The §4.D spike is a separate work item to plan and dispatch.

The doc deliverable (2) is a separate work item — it would land in `docs/antikythera-maths/mfo_spectral_research_notebook.md` as a new section, with cross-references to chess-spectral, ephemerides-spectral, and the AMSC literature_curated channel.

---

## Appendix — provenance and discipline notes

- This file is honest negatives + open questions. The DeepSeek fragment is a generative prompt, not an authority. Per `feedback_no_lineage_claims_in_notebook` discipline, no claim is made that DeepSeek's framing is a "natural extension" of established literature; the framing is treated as a compressed restatement of established content with project-specific layering.
- All §1 citations are pre-2020 canonical textbooks / papers, exempt from PDF re-verification per the [counter-clause](C:\Users\sckir\.claude\projects\D--GitHub-mlehaptics\memory\feedback_pdf_extraction_citation_discipline.md).
- Per [feedback_no_mvp_framing], the recommendation does not scope §4.D as "minimum-viable subset"; the protocol covers three settings as the full first cut, not a quick-tier teaser.
- The DeepSeek fragment is a CLAIM TO TEST, not a position to defend. §2's verdict is that 4 of 6 claims have established literature support, 1 needs the user's reframing, and 1 is aesthetic — none are crank. The fragment is compressed-but-accurate.
