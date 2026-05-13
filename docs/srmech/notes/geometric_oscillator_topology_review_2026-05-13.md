# Geometric-Oscillator Topology — Literature Scoping

**Date:** 2026-05-13
**Branch:** `research/geometric-oscillator-topology-review`
**Scope:** Generalizations of the Antikythera lunar pin-and-slot as a class of geometric-constraint oscillators; configuration-space topology; abstract-algebraic / linear-algebraic structure; user's "3 tracks → bistable" hypothesis.
**Discipline:** Algebra / eigenbasis lane per `docs/antikythera-maths/CLAUDE.md`. D-H1 semantics reserved — review is about the *class*. Citations WebFetch-verified where possible.

---

## 1. Summary

The mature literature on geometric-constraint oscillators splits into three tiers. **(a) Classical kinematics** (cam-follower, Scotch yoke, Geneva drive, Reuleaux's mechanism taxonomy) has a complete Fourier-series treatment of cam profiles as periodic input→output maps — this is exactly the project's existing eigenbasis framing, at engineering-textbook level. **(b) Configuration-space algebra** of linkages is settled at the universality level: Kapovich–Millson 2002 and King 1998 show essentially any compact real-algebraic set is the configuration space of some revolute-joint linkage. **(c) Multistability** (compliant-mechanism / Howell-school) has rich bistable / tristable design but treats stability as an *energy-landscape* problem, not as a *configuration-space-topology* problem. The bridge between (b) and (c) — spectral/Laplacian decomposition of configuration spaces of multistable mechanisms — is **largely open**, and the user's "3 tracks → bistable" hypothesis sits in that gap.

## 2. Canonical case — Greek lunar pin-and-slot

The Antikythera k1/k2 lunar device implements θ → atan2(sin θ, cos θ − ε) with ε ≈ 0.054 (Freeth et al. 2006; Magkos & Gourgoulias 2009 verify ~1-part-in-200 fit to Hipparchus' first anomaly). In the project's algebra-side framing, ε is the single deformation parameter weighting Fourier modes away from pure rotation (ε = 0 ⇒ identity; ε → 1 ⇒ singular). It is one member of a class where *slot path* + *eccentricity* together define a deterministic θ_in → θ_out map.

## 3. Zigzag slots

Treated in classical kinematics as **piecewise-defined cam lift** (Norton, *Design of Machinery*; Suh & Radcliffe). Output decomposes as Fourier series; sharp corners produce slowly-decaying high-order coefficients (Gibbs phenomenon), exciting the follower at n·ω₀ for all n and limiting high-speed operation. Wu et al. (2016) give a constructive Fourier-truncation cam design for resonance avoidance.

**Algebraic structure.** Piecewise rational: each linear slot segment is a Möbius-like sub-map; the full map is a tropical / max-plus composition. The natural eigenbasis is not plain Fourier — it is the eigenbasis of a piecewise-linear period (Koopman / transfer) operator on S¹, the same machinery as tent maps. **The project's existing graph-Laplacian methods do not directly apply**; new operator framework needed.

## 4. Curved (general-profile) slots

Mature. Wu et al. (2016) "Design and analysis of high-speed cam mechanism using Fourier series" (*Mech. Mach. Theory*) is a constructive design method: specify displacement transfer S(θ) as truncated Fourier series; slot profile follows analytically. **This is the most direct existing analog of the project's eigenbasis framing.** A smooth slot is a point in Fourier-coefficient space {a_n, b_n}; the lunar pin-and-slot is the single-point case (a₁ = ε, all else zero). Families parametrized by harmonic amplitudes form an infinite-dimensional manifold of geometric-constraint oscillators.

**Algebraic structure.** Direct: each slot is a point in coefficient space, output is the partial sum. **Generalizing requires only extending ε to a coefficient vector** — cleanest spike-ready extension.

## 5. Multi-track slots and bistability — the user's hypothesis

This is the interesting case and where the literature is most fragmented.

**Established: tristable compliant mechanisms exist.** Chen et al. 2010 ("A Tristable Mechanism Configuration Employing Orthogonal Compliant Mechanisms," *J. Mech. Robotics*) constructs a fully compliant tristable mechanism via orthogonally-embedded bistable units. Hao et al. 2022 ("A non-transit fully compliant tristable mechanism," *Mech. Syst. Signal Process.*) designs three stable states with **direct switching between any pair without transit** — the state-transition graph is the *complete graph* K₃, not the path P₃. Real published 3-stable-state mechanisms.

**But not "3 tracks → bistable."** The literal hypothesis — *three parallel slot tracks producing a bistable (2-state) oscillator* — does **not** have a clean published realization I can verify. What is published is (i) three tracks → *three* stable states (tristable), or (ii) two compliant beams → bistability via snap-through (Howell 2001), or (iii) isostatic 1D chain → bistability with soliton transitions (Kane–Lubensky 2014). The specific "3 tracks ⇒ 2 states" mapping would require redundant coding (3-bit repetition → 1-bit logical), which is a coding-theoretic structure, not a standard mechanism. **Honest negative.**

**Closest principled bridge.** Kane & Lubensky 2014 (*Nature Physics*; arXiv:1308.0554) + Chen, Upadhyaya & Vitelli 2014 (*PNAS*; arXiv:1404.2263) realize a *bistable* mechanical chain whose topology is encoded in an integer winding number; transitions between the two phases are mediated by a **topological soliton** moving along the chain. Berry et al. 2022 (arXiv:2205.10180) uses Kane–Lubensky chains to design soliton-gating mechanisms via critical-point perturbation. **This is the rigorous "geometric topology of linkage ⇒ bistability" instantiation.**

**Where the user's intuition is correct.** Multistability *does* emerge from track topology, not just energy-landscape engineering — but the published bridge runs through isostatic-lattice topology (Maxwell counting + winding invariants), not "N tracks → (N−1)-stable" combinatorics.

**Algebraic structure.** Configuration space of a multistable mechanism is a real-algebraic set with multiple critical points. Per Kapovich–Millson 2002 (*Topology* 41:1051–1107; arXiv:math/9803150), **any** compact real-algebraic set is the configuration space of *some* planar revolute-joint linkage. So multistable topologies are realizable in principle; the question is which *small, physically natural* mechanisms realize a given topology. The natural operator is the **graph Laplacian on the discrete state-transition graph** (nodes = stable states, edges = direct-switch pairs). For the Hao 2022 non-transit-tristable mechanism: K₃, spectrum {0, 3, 3}. For Chen 2010 classic transit-tristable: P₃, spectrum {0, 1, 3}. Distinct spectral invariants on two real mechanisms — falsifiable.

## 6. Abstract-algebraic framing per topology

| Topology | Natural eigenbasis | Project's existing tools apply? |
|---|---|---|
| Eccentric circular slot (lunar) | Fourier on S¹, weighted by ε | Yes — D-H1 module covers it |
| Zigzag slot | Piecewise transfer operator on S¹ | No — needs new framework |
| Curved (smooth) slot | Fourier on S¹ with coefficient vector {a_n, b_n} | **Yes, direct generalization** |
| Multi-track / multistable | Graph Laplacian on state-transition graph + Morse theory of energy landscape on configuration manifold | Partial — graph Laplacian yes, Morse theory not in current tooling |
| Topological-soliton chain (Kane–Lubensky) | Phonon Hamiltonian on isostatic lattice (sublattice-chiral) | No — phonon spectrum / topological-band framework needed |

## 7. Connection to the project's spectral framework

- **Curved slot:** the cyclic-group Fourier basis on ℤ/Nℤ is already in use; extending lunar ε to a coefficient vector is a parameter sweep, not new infrastructure.
- **Multistable:** the discrete state-transition graph (nodes = stable states, edges = direct-switch pairs) has its own Laplacian. Genuinely new but mathematically identical to gear-DAG Laplacian methods.
- **Kane–Lubensky topological chain:** sublattice-chiral phonon Hamiltonian with ℤ winding invariant — formally analogous to MFO §VII.4.1.2 Hopf-bundle / Casimir decomposition on a 1D mechanical chain. Mechanism theorists do **not** use anything like the MFO Casimir framework; real gap, potential project-side bridge contribution.

## 8. Reference anchors (verified via WebFetch unless flagged)

1. **Kapovich, M. & Millson, J. J.** (2002). "Universality theorems for configuration spaces of planar linkages." *Topology* **41**(6): 1051–1107. arXiv:math/9803150. — any compact real-algebraic set realizable as planar-linkage configuration space.
2. **King, H. C.** (1998). "Planar Linkages and Algebraic Sets." Proc. Gokova Geom. Topology Conf. arXiv:math/9807023.
3. **Farber, M.** (2017). "Configuration Spaces and Robot Motion Planning Algorithms." arXiv:1701.02083. Topological-complexity invariants.
4. **Farber, M.** (2003). "Topological complexity of motion planning." *Discrete Comput. Geom.* **29**: 211–221. arXiv:math/0111197.
5. **Berry, M., Limberg, D., Lee-Trimble, M. E., Hayward, R., & Santangelo, C. D.** (2022). "Controlling the configuration space topology of mechanisms." arXiv:2205.10180. Critical-point perturbation on linkage configuration manifolds; uses Kane–Lubensky chain for soliton gating.
6. **Chen, B. G., Upadhyaya, N. & Vitelli, V.** (2014). "Nonlinear conduction via solitons in a topological mechanical insulator." *PNAS* **111**(36): 13004–13009. arXiv:1404.2263. DOI:10.1073/pnas.1405969111.
7. **Kane, C. L. & Lubensky, T. C.** (2014). "Topological boundary modes in isostatic lattices." *Nature Physics* **10**: 39–45. arXiv:1308.0554.
8. **Ray, A., Anand, S., Dabade, V. & Chaunsali, R.** (2025). "Remote Nucleation and Stationary Domain Walls via Transition Waves in Tristable Magnetoelastic Lattices." *Phys. Rev. Materials* **9**: 014405. arXiv:2405.01168.
9. **Wu, L.-I., Chang, W.-T., et al.** (2016). "Design and analysis of high-speed cam mechanism using Fourier series." *Mech. Mach. Theory* **104**: 118–129. DOI:10.1016/j.mechmachtheory.2016.05.009. [verified via search listing, not WebFetch — ScienceDirect HTTP 403]
10. **Magkos, P. & Gourgoulias, K.** (2009). "Hipparchus vs. Ptolemy and the Antikythera Mechanism: Pin–Slot device models lunar motions." *Adv. Space Res.* **44**(6). [search-verified]
11. **Howell, L. L.** (2001). *Compliant Mechanisms*. Wiley. ISBN 0-471-38478-X. Canonical bistable / snap-through textbook.
12. **Chen, G., Aten, Q. T., Zirbel, S., Jensen, B. D., & Howell, L. L.** (2010). "A Tristable Mechanism Configuration Employing Orthogonal Compliant Mechanisms." *J. Mech. Robotics* **2**(1): 014501. [author list via ResearchGate listing]
13. **Hao, G., Chen, G., & Cui, X.** (2022). "A non-transit fully compliant tristable mechanism." *Mech. Syst. Signal Process.* article S0888327021009286. [title + journal search-verified; author list needs PDF-grade verification before downstream citation per `[[feedback_pdf_extraction_citation_discipline]]`]
14. **Reuleaux, F.** (1875/1876). *Kinematics of Machinery* (Macmillan trans.). Foundational mechanism taxonomy; Cornell KMODDL preserves physical models.
15. **Norton, R. L.** (2012). *Design of Machinery* (5th ed.), McGraw-Hill. Standard cam / Geneva / intermittent-motion textbook.

## 9. Open gaps and proposed next steps

**Gap.** The bridge between configuration-space topology of multistable mechanisms (mathematically rich, per Kapovich–Millson + Farber) and engineering practice of multistable design (mathematically thin, per Howell + Chen) is largely undeveloped. Multistable mechanisms are designed via energy-landscape (snap-through forces, beam buckling), not via configuration-space-topology synthesis.

**Spike-ready next moves.**

1. **Generalized smooth-slot phase-space transform (low-risk, high-yield).** Extend the D-H1 lunar ε to a Fourier coefficient vector {a_n, b_n}; derive θ → atan2(Σ a_n sin nθ, …). Parallel module to `pin_and_slot.py` (not extending — locked semantics), e.g. `general_slot_transform.py`. Lunar case recovered at (a₁, b₁) = (0, −ε). Clean single-spike, connects directly to existing graph-Laplacian eigenbasis on gear DAGs.

2. **State-transition Laplacian for multistable mechanisms (medium-risk).** Given (i) state count, (ii) direct-switch adjacency, (iii) energy-barrier matrix, compute graph-Laplacian spectrum. Hao 2022 non-transit-tristable = K₃, spectrum {0, 3, 3}. Chen 2010 transit-tristable = P₃, spectrum {0, 1, 3}. Distinct invariants on two real mechanisms — falsifiable.

3. **MFO bridge spike (higher-risk, higher-novelty).** Kane–Lubensky chain's sublattice-chiral phonon Hamiltonian has a ℤ winding invariant; MFO §VII.4.1.2 Casimir-decomposition / Hopf-bundle framework is formally analogous (sublattice-chiral ≅ ℤ₂ symmetry; winding ≅ first Chern). ~150-line spike: compute Kane–Lubensky winding via MFO operators, check reproduction of published result. Genuine cross-domain bridge if yes; sharpens distinctness if no.

**Honest negative recap.** The user's literal hypothesis — "3 tracks → bistable" — does not have a clean published realization. Published is: (a) 3 tracks → *tristable* (Chen, Hao), (b) 2 compliant beams → bistable (Howell), (c) isostatic 1D chain → bistable with soliton transitions (Kane–Lubensky). User's intuition that track-count and topology drive multistability is correct in spirit; the precise count "3 ⇒ bistable" is not how established mechanism-theory results count.

---

## 10. Crossed-Bar Static Configuration (X-graph)

**Geometry.** Two slot bars crossing at a center, forming a 4-arm X. The pin's configuration space is **not** a manifold: locally near the crossing it is a wedge of 4 intervals (a 4-valent vertex graph; concretely, the star graph K_{1,4} when arms are finite). Each arm carries a smooth 1-dimensional pin motion; at the branch point, the pin must commit to one of 4 outgoing arms. Discrete symmetry on the four arms is ℤ/4 (cyclic, if arms are labelled by rotation order) or ℤ/2 × ℤ/2 (Klein four, if labelled by opposite-pair). Classical smooth Hodge–Laplacian breaks at the branch point. Two principled mathematical frameworks exist for the singular point:

**(i) Combinatorial Laplacian on the state-transition graph K_{1,4}.** Treat the 4 arms as 4 stable "tracks" the pin can occupy and the center as a unique shared crossing-state. The state-transition graph (5 nodes; edges from center to each leaf) is exactly K_{1,4}. Its combinatorial Laplacian L = D − A is 5×5 with L_{00} = 4, L_{ii} = 1 (i = 1..4), L_{0i} = L_{i0} = −1; off-diagonals among leaves vanish. Spectrum is the classical star-graph result **{0, 1, 1, 1, 5}**, with the eigenvalue 1 having multiplicity n−1 = 3 (corresponding to the 3-dimensional representation of S_4 / (ℤ/2 × ℤ/2)) and the high eigenvalue n+1 = 5 corresponding to the radial "center-vs-leaves" mode. This is **distinct** from the P₃ tristable spectrum {0, 1, 3} (Chen 2010) and the K₃ non-transit-tristable spectrum {0, 3, 3} (Hao 2022). Counting: trace 8 = 0+1+1+1+5 ✓; product of nonzero eigenvalues 5 = n (matrix-tree theorem on a tree with 1 spanning tree, scaled by n) ✓. **K_{1,4} is therefore a genuine fourth point in the multistable-state-transition spectral catalog.**

**(ii) Quantum-graph (metric) Laplacian with Kirchhoff conditions.** Treat each arm as a finite-length interval (0, ℓ) attached at 0 to the central vertex. Kuchment's quantum-graph framework (Kuchment 2004, *Quantum Graphs I*) imposes (a) continuity of the eigenfunction at the central vertex and (b) Kirchhoff's vanishing-derivative-sum condition: Σ_k ψ_k'(0+) = 0. For 4 equal-length arms ℓ with Dirichlet conditions at the leaf endpoints, the eigenfunctions split into a "symmetric" branch (one-dimensional: ψ(x) = sin(k(ℓ−x)) on every arm with the same sign, only sustainable when Σ derivatives vanish — gives cos(kℓ) = 0, eigenvalues k = (π/2 + mπ)/ℓ, m ≥ 0) and an "antisymmetric" 3-fold-degenerate branch (orthogonal to symmetric mean, equivalent to a Dirichlet interval, eigenvalues k = mπ/ℓ, m ≥ 1). For arbitrary unequal arm lengths, the secular equation is transcendental and generic, with no degeneracy. **The metric Laplacian is the continuous analog of the combinatorial K_{1,4} Laplacian, and the multiplicity-3 pattern at the antisymmetric branch matches the multiplicity-3 of eigenvalue 1 in the combinatorial spectrum.** Both frameworks are mathematically standard and well-developed; what is absent from the literature is their application to the X-bar mechanism specifically.

**Literature scoping.**

*Singular configuration spaces of linkages.* Zlatanov, Bonev & Gosselin 2002 ("Constraint Singularities as C-Space Singularities," *Advances in Robot Kinematics*, ARK 2002) is the canonical statement that **constraint singularities are configuration-space singularities** — branching points separating distinct C-space regions. This is the right mathematical framing for the X-bar center. Müller 2018 ("Kinematic Singularities of Mechanisms Revisited," IMA Mathematics of Robotics) develops higher-order kinematic analysis via the **kinematic tangent cone**, which classifies the local geometry of C-space at a singular point — directly applicable to the X-bar center. Lopez-Custodio & Dai (multiple works on **kinematotropic mechanisms**) show that mechanisms can change finite mobility by passing through singular branch points; their helicoid–helicoid intersection construction is the spatial 3D analog of a 2D X-crossing.

*Compliant-mechanism side.* Cross-axis flexural pivots (BYU CMR; Jensen & Howell 2002) are the engineering instantiation of an X-shape but are designed to **avoid** the singular branch point — they operate locally near the crossing as a near-frictionless rotational pivot. Wang et al. 2021 (LLNL-JRNL-817077; "Cross-Pivot Flexures for Constrained 3-DOF Motion") explicitly notes that serial cross-pivot stacks **can** be deformed into singular configurations where freedom space changes (3-DOF → 2-DOF). They view this as a problem to engineer around; the X-bar oscillator framing inverts that — the branch point is the *desired* feature.

*Star-graph configuration spaces in topology.* Wawrykow 2024 (arXiv:2401.13821; *Trans. AMS Series B*) computes ordered-configuration-space homology of star graphs with k leaves, with results for k=3, k=4, k≥5. Li & Ozaydin 2026 (arXiv:2603.00914) develops a bipartite-weighted-graph persistent-homology model of the restricted second configuration space of metric star graphs. **Both treat star graphs as the underlying configuration space, exactly the K_{1,4} topology of the X-bar pin's track-arm landscape**, but neither is mechanism-domain work.

*Cellular-sheaf / stratified Laplacian.* Hansen & Ghrist 2019 ("Toward a Spectral Theory of Cellular Sheaves," *J. Appl. Comput. Topology*; arXiv:1808.01513) extends graph-Laplacian spectral theory to cellular sheaves on regular cell complexes, with the sheaf Laplacian as the natural generalization. The X-bar configuration space (1-d strata = 4 arms, 0-d stratum = center) is a regular cell complex; a constant sheaf on this complex yields exactly the combinatorial K_{1,4} Laplacian, while a sheaf carrying the local arm-direction data realizes a richer spectrum encoding the geometric (not just combinatorial) data. **The framework exists; mechanism-domain application is absent.**

*Geneva-drive variants.* The 4-slot ("Maltese cross") Geneva mechanism advances 90° per cycle but the pin enters/exits each slot **from outside** — the driven wheel's configuration space is a smooth S¹ at every instant; there is no branch point in the pin's instantaneous configuration. The X-bar is **topologically distinct**: the branch point is internal to a single mechanism, not the result of cyclic re-entry. Norton 2012 (*Design of Machinery*) confirms there is no "internally branched" Geneva variant.

**State-transition Laplacian comparison (extended).**

| Mechanism / track topology | State-transition graph | Spectrum |
|---|---|---|
| 4 disjoint parallel tracks | 4 isolated vertices | {0, 0, 0, 0} |
| Chen 2010 transit-tristable | path P₃ | {0, 1, 3} |
| Hao 2022 non-transit-tristable | complete K₃ | {0, 3, 3} |
| **X-bar (crossed slots) at center** | **star K_{1,4}** | **{0, 1, 1, 1, 5}** |
| K_{1,n} general (n arms through a single shared crossing) | star K_{1,n} | {0, 1^{(n−1)}, n+1} |

**Mechanism families realizing K_{1,4}.** Beyond the X-bar slot itself, anything with **one shared singular state plus n independent operating arms** has this topology: a planar 4-flap origami fold at a single vertex with 4 incident creases (when only one crease folds at a time, the unfolded state being the shared center); a 4-mode reconfigurable parallel manipulator at its constraint-singularity transition configuration; a 4-arm cross-pivot flexure operating *through* (not around) its singular configuration. The spectrum {0, 1^{(n−1)}, n+1} generalizes the bistable K_{1,1} = P₂ spectrum {0, 2} (single shared state, one operating arm) and the lunar pin-and-slot's degenerate case (n = 1 arm, no center).

**Honest negative.** The K_{1,4} Laplacian spectrum is a textbook result (Chung 1997, *Spectral Graph Theory*). The contribution is **the mapping**: identifying that the X-bar mechanism's branched configuration space has K_{1,4} as its natural state-transition graph, that this is a new fourth entry in the multistable-mechanism spectral catalog (joining P₃ and K₃), and that the same K_{1,4} is the natural configuration-space anchor for the constraint-singularity literature (Zlatanov et al. 2002; Müller 2018). No fundamentally new spectral theorem; a new mechanism-to-spectrum mapping. This is in line with the project's pin-and-slot-as-D-H1-primitive discipline — small clean abstract-algebraic identifications, not new theorems.

---

## 11. Rotating Crossed-Bar Configuration (branched covering of S¹)

**Geometry.** The crossed-bar frame rotates at angular velocity ω. The pin's choice at the crossing instant becomes phase-dependent — it depends on the pin's instantaneous velocity v_pin relative to each arm direction at the crossing moment. With 4 arms separated by π/2 (planar X with axes of symmetry), the arm-direction at rotation phase θ ∈ S¹ is e^{i(θ + kπ/2)} for k ∈ {0, 1, 2, 3}. Configuration space is a **branched covering of S¹**: fiber over generic θ ∈ S¹ \ {crossing moments} is the discrete set {0, 1, 2, 3} (arm labels), and at the crossing instants the fiber collapses to a single point (the center).

**Transition map at the crossing.** Let v_pin be the pin's tangential velocity in the lab frame at the crossing moment. The pin "chooses" arm k if v_pin · (arm-k direction) is maximal among the four arms (or, with stiction, if some threshold against a competing arm is exceeded). For symmetric v_pin and a uniformly rotating frame, the choice is a **deterministic function of phase θ**: a piecewise-constant map S¹ → {0, 1, 2, 3} with jumps at the crossing instants. This defines a permutation representation ℤ/4 → S₄ (or ℤ/2 × ℤ/2 → S₄ for the Klein-four labelling, depending on which discrete symmetry of the X-frame is preserved by the rotation). For uniform rotation with v_pin radially constant, the realized representation is the cyclic regular representation ℤ/4 → S₄ via the 4-cycle (0 1 2 3) — equivalently, the pin's arm label is monotonically incremented mod 4 every quarter-rotation, which is precisely a 4-fold cyclic permutation.

**Algebraic structure: orbifold quotient.** The total configuration space is (S¹ × {0,1,2,3}) / ~, where ~ identifies all four labels at the crossing-instant phases. Topologically this is **the orbifold S¹ / (ℤ/4)** (or the wedge of four circles at four crossing points, depending on construction). Emmrich & Römer 1990 ("Orbifolds as Configuration Spaces of Systems with Gauge Symmetries," *Comm. Math. Phys.* **129**: 69–94) frames exactly this kind of construction: when a system has a discrete symmetry (here, ℤ/4 on arm labels), the natural configuration space is an orbifold with singular points corresponding to higher-symmetry configurations (here, the crossing moments). Schrödinger / Laplacian theory on cones over Riemannian manifolds (also covered in Emmrich–Römer) is the operator-theoretic side: the X-bar's branched-covering Laplacian is the Laplacian on this cone.

**Literature scoping.**

*Branched coverings of S¹ in mechanism theory.* Direct hits are sparse. The closest engineering analog is the **planet-gear / epicycle** family, where the planet pin traces a cycloid (rotating ωₚ around its own center while the carrier rotates ω_c around the sun); the trajectory is a (smooth) Lissajous-style curve on a 2-torus T², not a branched cover. Without a *singular crossing* in the planet's slot, the topology is genuinely T², not a branched S¹. **The branched-S¹ structure requires both rotation and a singular pin-and-X-slot crossing.** This combination is not, as far as I can locate, named or studied as a class in the mechanism literature.

*Reconfigurable / kinematotropic mechanisms at a singular phase.* Lopez-Custodio & Dai construct mechanisms that change DOF when crossing a singular point in configuration space. The rotating-X-bar is an instance of this with one extra structure: the **time of singular-crossing is deterministic and periodic** (it occurs every ω·(crossing-phase angle) seconds). This is a kinematotropic mechanism with a *prescribed periodic schedule of mode transitions*, which is genuinely uncommon — Lopez-Custodio's helicoid–helicoid intersection examples have multiple modes but the transition is configuration-driven, not phase-driven. Müller 2026 (arXiv:2604.19419) on "variable topology mechanisms with regular topology changes" handles the related (smoother) case where mode transitions occur without DOF drop — explicitly excluding the singular-bifurcation case the X-bar realizes. **Gap identified: rotating-frame kinematotropic mechanisms with periodic singular bifurcation are a real, undeveloped subclass.**

*Permutation-representation realizations.* Retrograde-motion linkages, multi-armed cam mechanisms, and indexing turret drives all realize cyclic permutations on a finite set of states as a function of input rotation. None of them, to my reading of Norton 2012 + the Reuleaux taxonomy, realize the **specific structure** of "4-fold cyclic permutation gated by a singular branch point in C-space." The 4-slot Geneva drive realizes a 4-fold cyclic permutation but **without** a branch point — the pin enters/exits each slot from outside. The rotating X-bar realizes the same permutation **with** a branch point — and that is the topological distinction.

*Discrete-fiber bundles over S¹ in topological mechanics / robotics.* Ghrist's "Configuration Spaces, Braids, and Robotics" (Singapore Tutorial 2008) develops topological-complexity invariants for motion planning over configuration spaces. For finite-cover configurations (discrete fiber over S¹), the relevant invariant is the **monodromy** of the cover — i.e., the permutation of fiber labels induced by traversing the base loop once. For the rotating X-bar with 4 arms, the monodromy is the 4-cycle σ = (0 1 2 3) ∈ S₄; the connected components of the total space are the orbits of σ, so the total space is **one connected component** (since σ is a single 4-cycle), making it homeomorphic to a single circle S¹ (the 4-fold connected cover of S¹). With ℤ/2 × ℤ/2 (Klein four) instead of ℤ/4 — which arises if arms are paired and only opposite-arm transitions are allowed — the monodromy splits into two 2-cycles, and the total space has **two connected components**, each a 2-fold cover S¹ ⊔ S¹.

*Internal project-side analog: rotating-frame embedding of the lunar phase-space transform.* The lunar `atan2(sin θ, cos θ − ε)` (D-H1 module, locked) is a *smooth* phase-space map S¹ → S¹. Its natural rotating-frame embedding is θ_lab = θ + ωt, giving a smooth section of S¹ × ℝ → S¹ — no branching. The X-bar's transformation is *singular* — at the crossing moment, the output is not a function but a multi-valued choice. The clean analog in phase-space-transform language would be: replace `atan2(sin θ, cos θ − ε)` with a max-selection over 4 candidate `atan2` maps offset by π/2, with the maximum selector taking the role of the pin's arm-choice rule. **This is a NEW phase-space transform**, parallel to (not extending) the locked lunar transform, and it would live in a new module `crossed_slot_transform_rotating.py` per the D-H1 discipline.

**Spike-protocol readiness for the rotating crossed-bar.**

The rotating-frame case is **spike-protocol-ready** in a clean form. Concrete first-spike sketch:

1. Construct the planar X-bar with 4 arms of equal length ℓ separated by π/2.
2. Parametrize the rotating frame by phase θ = ωt ∈ S¹.
3. Compute the discrete monodromy σ ∈ S₄ as a function of the arm-choice rule (radial-velocity rule for ℤ/4 cyclic; opposite-arm-pair rule for ℤ/2 × ℤ/2).
4. **Output invariants**: (a) cycle structure of σ, (b) number of connected components of the branched covering, (c) the discrete Laplacian on the orbifold S¹ / σ, and (d) the long-time average pin-position spectrum (which, for ω rationally commensurate with the crossing rate, is a finite combination of cyclic-group eigenfunctions; for ω irrationally related, is an ergodic-theoretic spectral measure).
5. Compare invariants (a)–(d) across the two arm-choice rules (cyclic vs Klein-four) and across two rotation regimes (ω commensurate vs irrational).

This is a single ~150–250 line spike, parallel module from `pin_and_slot.py` (D-H1 lock respected), with falsifiable output: distinct cycle structures and distinct discrete Laplacian spectra for the two rules.

**Distinguishing invariants from the static X-bar and the smooth-slot Fourier extension.**

| Case | Invariant family |
|---|---|
| Static X-bar (§10) | Combinatorial Laplacian on K_{1,4}: {0, 1, 1, 1, 5} |
| Rotating X-bar with ℤ/4 cyclic monodromy | Single-cycle σ = (0 1 2 3); orbifold S¹ / ℤ/4 (a single S¹); spectrum of S¹-Laplacian {(2πn/(4ℓ))²}_{n≥0} |
| Rotating X-bar with ℤ/2 × ℤ/2 monodromy | Two 2-cycles; two-component cover S¹ ⊔ S¹; spectrum is two copies of the cyclic-group Laplacian |
| Smooth-slot Fourier extension (§4) | Single point in Fourier-coefficient space {a_n, b_n}; no branching; spectrum is the discrete Fourier basis on S¹ |

**Honest negative.** I could not locate a paper that (i) names "rotating-frame X-bar" or "phase-gated branched configuration space" as a mechanism class, (ii) computes the monodromy or its spectral invariants in the mechanism-theory literature, or (iii) bridges the orbifold-Laplacian framework (Emmrich–Römer 1990, mathematical physics) to mechanism theory. **The literature has all the necessary pieces** — kinematotropic mechanism theory, orbifold configuration spaces, quantum-graph metric Laplacians, branched-covering monodromy — but I find no published unification on this specific mechanism class. The project's contribution opportunity is the *naming and unification*, not a new theorem.

---

## 12. Rotating-X-bar invariants table (Task A spike sketch)

**Scope.** Concretize the §11 spike-protocol-readiness claim into a 2×2 invariants table over (frequency-ratio regime) × (arm-rule). The table is the deliverable a parallel module `crossed_slot_transform_rotating.py` (D-H1 lock respected per `docs/antikythera-maths/CLAUDE.md` — not extending `pin_and_slot.py`) would produce on call. The four cases are:

| | Radial ℤ/4 arm-rule | Klein-four pair-opposite arm-rule |
|---|---|---|
| Commensurate ω_pin / ω_frame = p/q | (1) | (2) |
| Incommensurate ω_pin / ω_frame ∈ ℝ \ ℚ | (3) | (4) |

**§12.1 Monodromy class in S₄.** The monodromy of the base loop (one full ω_frame revolution, with 4 crossing events at frame phases 0, π/2, π, 3π/2) is determined by the **arm-rule**, *not* by ω_pin/ω_frame commensurability. The commensurability affects the long-time *orbit structure* (closed vs ergodic) over many revolutions, not the deck-transformation class of a single revolution.

- Radial ℤ/4 rule (each crossing advances arm-label by +1 mod 4): generator σ = (0 1 2 3); group Γ = ⟨σ⟩ ≅ ℤ/4; cycle structure **single 4-cycle**.
- Klein-four pair-opposite rule (each crossing swaps the pin into the diametrically opposite arm of its current pair): generators τ₁ = (0 2), τ₂ = (1 3); group Γ = ⟨τ₁, τ₂⟩ ≅ ℤ/2 × ℤ/2; cycle structure **two 2-cycles**.

The four cases share monodromy by column: cases (1) and (3) have σ = (0 1 2 3); cases (2) and (4) have σ = (0 2)(1 3).

**§12.2 Orbifold Laplacian spectrum.** Per Emmrich–Römer 1990 (*Comm. Math. Phys.* 129:69–94), the configuration orbifold is the quotient of the cover by Γ. Let L denote the circumference of the 4-fold cover S¹ (the pin's full periodic state, equivalent to 4 frame revolutions when the deck group acts freely).

- ℤ/4 cyclic (cases 1, 3): cover is connected (single 4-cycle ⇒ orbit-set is one orbit of size 4); orbifold S¹/ℤ/4 is a single circle of circumference L/4. Laplacian spectrum **{(8πk/L)²}_{k=0,1,2,…}**, eigenvalue 0 simple, all others simple. Verified numerically at L=1: {0, 631.65, 2526.62, 5684.89, …}.
- Klein-four (cases 2, 4): cover decomposes into two connected components (two 2-cycles ⇒ orbit-set has two orbits of size 2); orbifold S¹ ⊔ S¹, each circle of circumference L/2. Laplacian spectrum on each component **{(4πk/L)²}_{k=0,1,2,…}**, full spectrum each eigenvalue doubled. Verified at L=1: each component {0, 157.91, 631.65, 1421.22, …}; full multi-set has each value with multiplicity 2.

Top non-zero Klein/cyclic eigenvalue ratio at k=1 is exactly 1/4 (longer circumference ⇒ smaller eigenvalue), and Klein has spectral degeneracy 2 from the disconnected components — two distinct topological signatures.

**§12.3 Periodic-orbit / phase-locked vs ergodic invariants.** With ω_pin/ω_frame = p/q in lowest terms, the pin's arm-trajectory closes into a finite periodic orbit after q frame-revolutions and 4q crossings; the *closed-orbit length* in arm-label space is `4q / gcd(p, 4q)` (cyclic case) or `4q / gcd(p, 2q)` per component (Klein case). With ω_pin/ω_frame irrational, the orbit is ergodic on its connected component of the cover and the long-time arm-visit measure equals the uniform Haar measure on the orbit.

The most useful coarse-grained invariant is the **long-time arm-visit histogram** π_k = (long-run frequency pin spends on arm k):
- Case (1) commensurate cyclic: π is supported on a *periodic subset* of all 4 arms; pattern is rational, count of distinct visited arms is 4/gcd(p, 4); for generic (p,q) all 4 arms visited but with non-uniform weights.
- Case (2) commensurate Klein: π is supported on **2 arms only** (the pin's starting component); rational pattern within those 2 arms.
- Case (3) incommensurate cyclic: π = (1/4, 1/4, 1/4, 1/4) uniform on all 4 arms (Birkhoff ergodic theorem on the connected cover).
- Case (4) incommensurate Klein: π = (1/2, 0, 1/2, 0) or (0, 1/2, 0, 1/2) depending on starting component — **uniform on 2 arms, zero on other 2**.

**§12.4 Most distinguishing observable across all 4 cases.** The 2-bit invariant **(support cardinality |supp π| ∈ {2, 4}, regularity ∈ {rational/periodic, irrational/uniform})** separates all four cases unambiguously:

| Case | |supp π| | Regularity | Distinguishing signature |
|---|---|---|---|
| (1) Commensurate cyclic | 4 (generically) | Periodic, non-uniform | All-4 arms visited in finite rational pattern |
| (2) Commensurate Klein | 2 | Periodic, non-uniform | Half of arms never visited; periodic on the other half |
| (3) Incommensurate cyclic | 4 | Uniform 1/4 each | All-4 arms visited with equal long-time weight |
| (4) Incommensurate Klein | 2 | Uniform 1/2 each | Half of arms never visited; uniform on the other half |

This is **experimentally falsifiable** with a single long-run trajectory: bin pin position by arm, observe support cardinality (2 vs 4) and dwell-time distribution (peaked / rational-multimodal vs uniform).

**§12.5 Algorithm sketch (pseudo-code, implementable in ~150–250 lines of numpy + sympy).**

```
INPUT:
    omega_frame: float                  # rad/s, frame angular velocity
    omega_pin:   float                  # rad/s, pin natural velocity
    arm_rule:    {'cyclic_Z4', 'klein4'}
    L_arm:       float                  # arm length (sets cover circumference L = 4*L_arm)
    n_revs:      int                    # number of frame revolutions to simulate

OUTPUT:
    {
      'monodromy_cycle_structure': tuple,        # e.g. (4,) or (2, 2)
      'monodromy_group_order':     int,          # 4 or 4 (both rank-2)
      'n_components_of_cover':     int,          # 1 or 2
      'orbifold_spectrum_first_k': list[float],  # first k Laplacian eigenvalues
      'ratio_classification':      str,          # 'commensurate p/q' or 'irrational'
      'periodic_orbit_length':     int | None,   # None if irrational
      'arm_visit_histogram':       array[4],     # long-run measure on 4 arms
      'invariant_2bit':            tuple,        # (|supp|, regularity_flag)
    }

STEP 1: monodromy permutation
    if arm_rule == 'cyclic_Z4':
        sigma = Permutation([1, 2, 3, 0])           # (0 1 2 3)
    else:  # klein4
        sigma = Permutation([2, 3, 0, 1])           # (0 2)(1 3)
    cycle_struct = sigma.cycle_structure()
    n_components = len(sigma.cyclic_form)

STEP 2: orbifold spectrum
    cover_L = 4 * L_arm
    # cycle_lengths: e.g. [4] for Z/4 cyclic, [2, 2] for Klein
    cycle_lengths = [len(c) for c in sigma.cyclic_form]
    spectra_per_component = []
    for clen in cycle_lengths:
        component_L = cover_L * clen / 4           # circumference of this S^1 component
        spec = [(2*pi*k / component_L)**2 for k in range(k_max)]
        spectra_per_component.append(spec)
    orbifold_spectrum = merge_and_sort(spectra_per_component)

STEP 3: commensurability check
    ratio = omega_pin / omega_frame
    pq = sympy.Rational(ratio).limit_denominator(1000)
    if abs(float(pq) - ratio) < tol:
        regime = 'commensurate'
        p, q = pq.p, pq.q
        if arm_rule == 'cyclic_Z4':
            orbit_length = 4*q // gcd(p, 4*q)
        else:
            orbit_length = 2*q // gcd(p, 2*q)
    else:
        regime = 'irrational'
        orbit_length = None

STEP 4: simulate trajectory and histogram arm-visits
    arm = 0
    visits = [0, 0, 0, 0]
    for t in arange(0, n_revs * 2*pi / omega_frame, dt):
        phase = (omega_frame * t) % (2*pi)
        # detect crossing events: phase in {0, pi/2, pi, 3*pi/2} +- dphase
        if at_crossing(phase):
            arm = sigma(arm)
        visits[arm] += 1
    pi_histogram = visits / sum(visits)

STEP 5: classify 2-bit invariant
    support = sum(1 for v in pi_histogram if v > eps)
    regularity = 'uniform' if all(abs(v - 1/support) < tol for v in pi_histogram if v > eps) else 'periodic'
    return {
        'monodromy_cycle_structure': cycle_struct,
        ...
        'invariant_2bit': (support, regularity),
    }
```

The four input combinations (commensurate-vs-irrational × cyclic-vs-Klein) produce the four distinct (|supp π|, regularity) signatures of §12.4. Implementable with `sympy.combinatorics.Permutation` for the group theory + `numpy` for the trajectory simulation + closed-form `(2πk/L)²` orbifold spectra.

**§12.6 New module identified.** Per the D-H1 semantics lock (`docs/antikythera-maths/CLAUDE.md` — "*Pin-and-slot reuse beyond D-H1*"), `pin_and_slot.py` may **not** be extended for this case. The new module is **`docs/antikythera-maths/research/crossed_slot_transform_rotating.py`**, parallel to `pin_and_slot.py`. Recovers `pin_and_slot.py`'s lunar atan2 transform in the degenerate limit of (i) one arm only (n=1, no crossing), (ii) zero rotation (ω_frame = 0, reducing to the static X-bar of §10), or (iii) eccentric circular slot with a single arm (the canonical D-H1 case). Does **not** import or call `pin_and_slot.py`. The dispatch function `crossed_slot_transform(theta_pin, theta_frame, arm_rule, L_arm)` returns the pin's instantaneous arm-label and the orbifold-coordinate phase, parallel to `pin_and_slot.atan2_transform(theta, eps)` returning the lunar-mechanism output angle.

**§12.7 Falsifiability statement.** The 2-bit invariant (|supp π|, regularity) on a long-run trajectory is a falsifiable observable. A physical or simulated rotating-X-bar oscillator with claimed Klein-four pair-opposite arm-rule **must** show 2-arm support; one with claimed ℤ/4 cyclic rule **must** show 4-arm support. If the observed support cardinality contradicts the rule label, the arm-rule attribution is wrong. Similarly, uniform-vs-rational regularity falsifies the commensurability label.

---

## 13. K_{1,n} algebraic stacking (Task B)

**Setup.** Following on §10's identification of K_{1,4} as the static-X-bar state-transition graph with Laplacian spectrum {0, 1, 1, 1, 5}, the user's "natural follow-up" asks whether the pattern at general n carries algebraic content beyond the textbook closed-form spectrum.

**§13.1 Verification of the closed-form K_{1,n} Laplacian spectrum.** Numerically computed for n = 2, 3, 4, 5, 6:

| n | Spectrum |
|---|---|
| 2 | {0, 1, 3} (= P₃, the path; matches Chen 2010 transit-tristable per §5) |
| 3 | {0, 1, 1, 4} |
| 4 | {0, 1, 1, 1, 5} (matches §10 X-bar derivation) |
| 5 | {0, 1, 1, 1, 1, 6} |
| 6 | {0, 1, 1, 1, 1, 1, 7} |

General formula **{0, 1^{(n−1)}, n+1}**: eigenvalue 0 simple, eigenvalue 1 with multiplicity (n−1), eigenvalue (n+1) simple. **Verified.** This is the textbook result (Chung 1997, *Spectral Graph Theory*, §1.2 for stars). Eigenvalue trace check: 0 + (n−1)·1 + (n+1) = 2n = sum of vertex degrees ✓. Spanning-tree count via matrix-tree theorem: product of nonzero eigenvalues divided by (n+1) = (n+1) · 1^{(n−1)} / (n+1) = 1 ✓ (K_{1,n} is a tree, exactly 1 spanning tree).

**§13.2 Representation-theoretic decomposition under S_n.** The symmetric group S_n acts naturally on the n leaves of K_{1,n}; the Laplacian commutes with this action because permuting leaves is a graph automorphism. The (n+1)-dimensional vertex space ℝ^{n+1} = ℝ_center ⊕ ℝ^n_leaves decomposes under S_n as:

```
    ℝ_center  ≅  trivial irrep of S_n (1-dim, since S_n fixes the center)
    ℝ^n_leaves =  trivial irrep ⊕ standard irrep
              =  span(1_leaf-sum)  ⊕  {v : Σ v_i = 0}        (1-dim ⊕ (n−1)-dim)

Total decomposition:
    ℝ^{n+1}  ≅  trivial ⊕ trivial ⊕ standard
              =     1   ⊕    1   ⊕   (n−1)              (1 + 1 + (n−1) = n+1 ✓)
```

**Eigenspace-irrep correspondence (verified explicitly for n=4 by eigenvector inspection):**
- λ = 0 eigenspace (1-dim): all-ones vector (center component +1, all leaves +1) — sits in the **trivial-irrep sum** of the two trivial copies.
- λ = (n+1) eigenspace (1-dim): center −n, leaves +1 each — sits in the **trivial-irrep orthogonal** of the two trivial copies (orthogonal to all-ones; both subspaces are 1-dim and S_n-invariant).
- λ = 1 eigenspace ((n−1)-dim): center = 0, leaves with Σ leaf_components = 0 — **exactly the standard irrep of S_n**.

So the (n−1)-fold degeneracy of the eigenvalue 1 is **forced by representation theory**: S_n's standard irrep has dimension (n−1), and the 1-eigenspace is irreducible-standard. The two simple eigenvalues 0 and (n+1) split the 2-dim trivial-isotypic component into S_n-invariant orthogonal halves; their relative ordering (0 < n+1) is forced by the graph being connected and bipartite-with-one-center. This confirms — explicitly — that the K_{1,n} Laplacian spectrum is **rep-theoretically locked**: any S_n-symmetric perturbation of the graph (e.g., uniform edge-weight scaling) preserves the (n−1)-fold degeneracy.

**§13.3 Coxeter / A_n / Dynkin connection — honest verdict.** The user flagged the apparent coincidence: A_n's Coxeter number is h(A_n) = n+1, and K_{1,n}'s top eigenvalue is n+1. Examined case by case:

| Star | Dynkin type | Coxeter number h | K_{1,n} top eigenvalue |
|---|---|---|---|
| K_{1,1} | A_2 | 3 | 2 |
| K_{1,2} = P₃ | A_3 | 4 | 3 |
| K_{1,3} | D_4 | 6 | 4 |
| K_{1,4} | affine D̃_4 (not finite type) | — | 5 |
| K_{1,n}, n ≥ 5 | hyperbolic (not finite or affine type) | — | n+1 |

The match would require **h = top eigenvalue at each n**, but they differ at every n ≥ 1: A_2 gives h=3 vs eigenvalue 2; A_3 gives 4 vs 3; D_4 gives 6 vs 4. So **the "A_n Coxeter h = n+1" coincidence is numerical-coincidence-only** and does not extend to a structural identity. The top eigenvalue n+1 is simply **the degree of the central vertex**, which is a generic spectral property of stars (and more generally of bipartite-double-star structure) — it carries no Dynkin / Coxeter algebraic content.

**Honest-negative verdict: there is no Coxeter / Dynkin algebraic structure on K_{1,n} beyond the n = 3 case where K_{1,3} = D_4 happens to be a finite-type Dynkin diagram.** The (n+1)-eigenvalue pattern reflects only the central degree, not a deeper algebraic identity.

**§13.4 Finite-Dynkin vs. affine/hyperbolic distinction — does it gate any project invariant?** The finite-vs-affine-vs-hyperbolic Dynkin distinction *would* matter if the orbifold-Laplacian construction of §12 required a finite Coxeter / Weyl-group action. It does **not**: per Emmrich–Römer 1990, the orbifold-Laplacian construction needs only a discrete-group action on the cover (here ℤ/n or its variants), and is well-defined for any n. The finite-type-only constraint is a property of the Cartan matrix's positive-definiteness, not of orbifold-Laplacian validity.

**Where this distinction could become load-bearing.** If one tried to lift the rotating-X-bar of §12 to a fully Lie-algebraic construction — e.g., interpret the n arms as the n simple roots of a Lie algebra of type X_n, with the central vertex as the affine node — then **only n ∈ {3} would give a finite-dimensional Lie algebra** (D_4), n = 4 gives the affine Kac–Moody algebra affine-D_4, and n ≥ 5 gives hyperbolic Kac–Moody algebras with no finite-dimensional irreps. This is a real distinction, but **it lives in a Lie-algebraic interpretation that the project has not committed to**. For the project's current spectral-graph-Laplacian framework, the K_{1,n} spectrum is universal and unobstructed.

**§13.5 Honest-positive content beyond the textbook formula.** Two pieces survive scrutiny:

1. **S_n standard-irrep identification of the 1-eigenspace** (§13.2). The (n−1)-fold degeneracy is **forced** by rep theory, not by graph-Laplacian luck. This makes the degeneracy *stable* under any S_n-symmetric perturbation of the graph — e.g., reweighting all leaf edges uniformly preserves the (n−1)-fold degeneracy because S_n still acts. This is a true algebraic structure beyond Chung 1997's formula-statement; it is mentioned in the broader spectral-graph literature (Babai 1979 on automorphism groups and spectra; Godsil & Royle 2001 *Algebraic Graph Theory* §8 on graph spectra and representation theory) but is not standardly called out for the K_{1,n} case specifically.
2. **Top eigenvalue = central-vertex degree** (§13.3). A general fact about stars (and approximate fact about graphs with a single high-degree vertex; see Cvetković–Doob–Sachs 1980 *Spectra of Graphs* ch. 3 on vertex-degree bounds). Not a deeper algebraic identity; the (n+1)-pattern is "central degree", not "Coxeter h".

**Honest-negative recap.** No Dynkin / Coxeter / Lie-algebraic structure on K_{1,n} beyond the n=3 coincidence. The (n+1)-top-eigenvalue is the central degree, period. The (n−1)-fold-degenerate 1-eigenvalue *is* genuinely S_n-rep-theoretic (this is the load-bearing finding), and that gives a **falsifiable spike-protocol prediction** for §13.7.

**§13.6 Stacking interpretation — mechanism semantics.** In the static-X-bar mechanism (§10), K_{1,n} corresponds to **n slot-arms meeting at a single shared central singular configuration** (the crossing/branch point of the configuration space, per Zlatanov–Bonev–Gosselin 2002). Stacking = adding more arms through the same singular crossing-point. The §10 catalog extends naturally:

| n (number of arms) | Mechanism | Spectrum | S_n decomposition of eigenspaces |
|---|---|---|---|
| 1 | single slot, no center (degenerate) | {0, 2} (= K_2 / edge) | trivial ⊕ trivial |
| 2 | bistable two-arm path P₃ | {0, 1, 3} | trivial ⊕ standard(S_2, 1-dim) ⊕ trivial |
| 3 | trivalent X-bar | {0, 1, 1, 4} | trivial ⊕ standard(S_3, 2-dim) ⊕ trivial |
| 4 | quadrivalent X-bar (§10) | {0, 1, 1, 1, 5} | trivial ⊕ standard(S_4, 3-dim) ⊕ trivial |
| 5 | 5-arm star | {0, 1, 1, 1, 1, 6} | trivial ⊕ standard(S_5, 4-dim) ⊕ trivial |
| n | n-arm star K_{1,n} | {0, 1^{(n−1)}, n+1} | trivial ⊕ standard(S_n, (n−1)-dim) ⊕ trivial |

The eigenvalue-1 multiplicity (n−1) grows linearly with arm count; the top eigenvalue (n+1) grows linearly with arm count; the bottom eigenvalue is 0 always. **Linear-in-n in three quantities, with the middle multiplicity forced by S_n's standard-irrep dimension.**

**§13.7 Spike-protocol-ready experimental prediction.** A physical n-arm-star mechanism (n slot-arms meeting at a single singular crossing, all arms identical) should exhibit **(n−1)-fold degenerate normal modes** in the quantum-graph (Kuchment 2004) / cellular-sheaf (Hansen–Ghrist 2019) Laplacian. The prediction:

> If a physically constructed n-arm K_{1,n} mechanism is driven through its central singular configuration and its small-oscillation spectrum is measured (e.g., resonance frequencies of arm-tip oscillations near the center, or normal-mode frequencies of an instrumented version), one of the eigenvalues should appear with multiplicity exactly (n−1).

**Falsifiability:** if (i) S_n symmetry is preserved (all arms identical, central pin symmetric), and (ii) the eigenvalue-1 multiplicity is observed to be < (n−1), then either some assumed symmetry is broken (engineering tolerance) or the K_{1,n} spectral-graph framing is wrong for this mechanism. Conversely, observing multiplicity exactly (n−1) confirms the S_n-standard-irrep identification of §13.2 — and confirms that the static-X-bar is **the n = 4 instance of a single rep-theoretic family**, not an ad hoc graph-Laplacian coincidence.

This is a real, falsifiable, spike-protocol-ready prediction at the level of physical mechanism construction.

**§13.8 Cross-domain connection to MFO and other project notebooks.** The S_n standard-irrep appearing at eigenvalue 1 has a direct cross-domain echo: in MFO §VII.4.1.2 / chess-spectral §3.5.3(C) etc., **irrep-multiplicity counting in symmetric-group representations is a load-bearing tool**, and the K_{1,n} family gives an exceptionally clean example where the irrep-decomposition exactly explains the Laplacian-spectrum-multiplicity pattern. This is one of the cleanest "irrep-multiplicity ⇒ Laplacian-degeneracy" identifications in the project's spectral catalog — comparable to chess-knight §3.5.3(C) (Mode I / Mode II framing) and ephemerides D₃ on SG λ=6 (giving 18-block count via 3 × 6 SM components per [`memory/project_mfo_mpm_orchestration_findings.md`]).

---

## 14. Reference anchors added in §10–§11 (verified via WebFetch unless flagged)

16. **Zlatanov, D., Bonev, I. A., & Gosselin, C. M.** (2002). "Constraint Singularities as C-Space Singularities." *Advances in Robot Kinematics* (ARK 2002), Caldes de Malavella, June 24–28. [parallemic.org/Reviews/Review008.html review-verified]
17. **Müller, A.** (2018). "Kinematic Singularities of Mechanisms Revisited." IMA Mathematics of Robotics, Sept 2018. [PDF binary-only; title + author + venue verified from URL + search results, not PDF-text-verified]
18. **Müller, A.** (2026). "Forward Dynamics of Variable Topology Mechanisms — The Case of Constraint Activation." arXiv:2604.19419. — VTM with regular topology changes (singular bifurcation explicitly excluded).
19. **López-Custodio, P. C., Rico, J. M., & Cervantes-Sánchez, J. J.** (2017). "Local Analysis of Helicoid–Helicoid Intersections in Reconfigurable Linkages." *J. Mechanisms Robotics* **9**(3): 031008. [search-verified]
20. **Hansen, J. & Ghrist, R.** (2019). "Toward a Spectral Theory of Cellular Sheaves." *J. Appl. Comput. Topology* **3**: 315–358. arXiv:1808.01513. — sheaf Laplacian on regular cell complexes.
21. **Wawrykow, N.** (2025). "Homology Generators and Relations for the Ordered Configuration Space of a Star Graph." *Trans. AMS Ser. B* **12**: 1188–1222. arXiv:2401.13821. — k-leaf star graphs, k=3, k=4, k≥5.
22. **Li, W. & Ozaydin, M.** (2026). "Persistent Combinatorial Model of the Restricted Second Configuration Space of Metric Star Graphs." arXiv:2603.00914. — persistent homology of metric star configuration spaces.
23. **Emmrich, C. & Römer, H.** (1990). "Orbifolds as Configuration Spaces of Systems with Gauge Symmetries." *Comm. Math. Phys.* **129**(1): 69–94. — orbifold Laplacian; cones over Riemannian manifolds; foundational for branched-covering S¹ analysis.
24. **Kuchment, P.** (2004). "Quantum Graphs I. Some Basic Structures." [people.tamu.edu/~kuchment/qgraphs1.pdf; PDF binary-only, title + author verified]. — metric-graph Laplacian; Kirchhoff vertex conditions; canonical reference for the metric-K_{1,n} construction.
25. **Jensen, B. D. & Howell, L. L.** (2002). "The Modeling of Cross-Axis Flexural Pivots." *Mech. Mach. Theory* **37**(5): 461–476. — cross-axis flexures as compliant-mechanism instantiation of an X-shape (operating *around*, not *through*, the singular configuration).
26. **Wang, J., Brown, K. W., Cullinan, M. A., & Hopkins, J. B.** (2021). "Using Cross-Pivot Flexures to Generate Reduced-DOF Mechanisms." LLNL-JRNL-817077. — serial cross-pivot stacks at singular configurations (3-DOF → 2-DOF transitions).
27. **Chung, F. R. K.** (1997). *Spectral Graph Theory*. CBMS Regional Conference Series in Mathematics **92**, AMS. — textbook source for K_{1,n} combinatorial Laplacian spectrum {0, 1^{(n−1)}, n+1}.
28. **Ghrist, R.** (2008). "Configuration Spaces, Braids, and Robotics." Singapore Tutorial Lecture Notes. — topological-complexity / monodromy invariants for motion-planning over discrete-fiber configuration spaces.
29. **Babai, L.** (1979). "Spectra of Cayley graphs." *J. Combin. Theory Ser. B* **27**(2): 180–189. DOI:10.1016/0095-8956(79)90079-0. — automorphism-group action on Laplacian eigenspaces; canonical reference for the "rep-theoretic decomposition of graph-Laplacian eigenspaces" used in §13.2. [pre-2020, no PDF-verification gate]
30. **Godsil, C. & Royle, G.** (2001). *Algebraic Graph Theory*. Graduate Texts in Mathematics **207**, Springer. ISBN 0-387-95220-9. — chapter 8 develops the rep-theoretic eigenspace decomposition framework used in §13.2; chapter 13 covers star-graph spectra. [textbook reference, pre-2020]
31. **Cvetković, D. M., Doob, M. & Sachs, H.** (1980). *Spectra of Graphs — Theory and Application*. Academic Press. — chapter 3 develops vertex-degree bounds on Laplacian spectra; classic reference for the "top eigenvalue ≈ central vertex degree" observation in §13.3. [textbook reference, pre-2020]

---

## 15. Re-evaluation of Moves 2 and 3 (post §10–§11; partly executed in §12–§13)

> **Note (2026-05-13 update):** §12 now contains the full rotating-X-bar invariants table + algorithm sketch for the new `crossed_slot_transform_rotating.py` module (the replacement-recommendation spike). §13 addresses the algebraic-stacking K_{1,n} follow-up. The recommendations below are retained for provenance, but the spike-readiness claim has been concretized.



**Move 2 — focused-subagent computation of the branched-configuration Laplacian spectrum.** §10's closing-sketch already supplies the combinatorial K_{1,4} spectrum {0, 1, 1, 1, 5} from textbook (Chung 1997) and the metric-Laplacian framing from Kuchment 2004 quantum-graph theory. The "actual matrix construction + eigenvalue extraction + comparison to K₃/P₃" computation is **5×5 by-hand or a 10-line numpy.linalg.eigh call**; it does not need a dedicated subagent. **Recommendation: collapse Move 2 to a verification-and-write-up task** — confirm the closed-form spectrum by numerical computation (1 line of numpy), then add the K_{1,4} row to the project's existing state-transition Laplacian catalog (whichever module ends up hosting the multistable-mechanism table). The actual *new* computational work is in §11's rotating-frame case — the monodromy + orbifold-S¹ Laplacian sketch — which is non-trivial and **is** spike-worthy.

**Move 3 — main-agent in-conversation derivation of the X-graph Laplacian spectrum.** §10 has now derived this in-document; the in-conversation derivation would be redundant. **Recommendation: skip Move 3 as originally scoped.** The value-add it would have provided is now captured here.

**Replacement recommendation.** Spawn one focused subagent on the **rotating X-bar spike from §11** — implement `crossed_slot_transform_rotating.py` as a parallel module (D-H1 lock respected), compute the monodromy + orbifold Laplacian for both arm-choice rules and both rotation regimes, and produce a falsifiable invariants table. That is the genuine new computational content; the static case is now reference-grade.

---

## 14. V-as-primitive construction; angle-reweighted Laplacian

**Setup.** The static X-bar of §10 was *two full perpendicular bars crossing through a single center*, which forces 4 arms at exactly 90° separation and exactly even arm-count. Replacing the construction primitive by the **V-junction** — two arms meeting at a vertex at an arbitrary angle θ, with no requirement that the two arms be collinear or that another bar pass through — decouples the geometric angle of the realization from the topological structure of the state-transition graph. K_{1,n} for any n is constructible from V's plus single arms:

| n | V-decomposition | Geometric realizations |
|---|---|---|
| 1 | 1 single arm | single radial slot (degenerate) |
| 2 | 1 V (= 1 V) or 2 single arms | V at angle θ, or one full bar (θ = π) |
| 3 | 1 V + 1 single arm | Y-shape; regular Y at 120° has C_3v symmetry |
| 4 | 2 V's, or 1 full bar + 1 single arm + 1 single arm | X-bar (two bars, §10), or pinwheel-X at 90° via V+V, or asymmetric crooked X |
| 5 | 2 V's + 1 single arm | 5-spoke star; regular star at 72° has C_5v symmetry |
| 6 | 3 V's, or 2 full bars + 2 single arms | hex-star at 60° (D_6 / C_6v); arbitrary 3-V's; etc. |
| n (general) | ⌊n/2⌋ V's + (n mod 2) single arms | regular n-star at 2π/n has D_n / C_nv; arbitrary angles break to C_1 |

**Crucially, the V-primitive allows odd n** because each V contributes 2 arms (not necessarily 180°-opposite); a stray "single arm" contributes 1; the full-bar primitive is restricted to contributing 2 arms at 180°, forcing even n. Odd-n stars K_{1,3}, K_{1,5}, K_{1,7}, ... are V-constructible but not full-bar-constructible. The user's instinct is correct.

**§14.1 Distinction: combinatorial vs. weighted Laplacian.**

The *combinatorial* graph Laplacian L = D − A is **topological** — its entries only know which vertices are adjacent. K_{1,n} has the same combinatorial Laplacian regardless of how arms are geometrically realized (regular vs. unequal angles, equal vs. unequal lengths). Spectrum {0, 1^{(n−1)}, n+1} per §13.1 is **invariant** under all such reshaping.

The *weighted* Laplacian L_w = D_w − A_w, with edge weight w_i = function of (arm length ℓ_i, possibly arm angle θ_i), is the right object for **physical normal-mode frequencies**. For a star K_{1,n} with the center fixed and small-amplitude radial oscillations of mass points at the arm tips, with elastic edges of stiffness k_i = c / ℓ_i (Hooke for a thin rod) and tip masses m_i:

- The reduced single-particle Hamiltonian for the i-th arm in isolation (center clamped) has frequency ω_i = √(k_i / m_i) = √(c / (m_i ℓ_i)). 
- Full coupling through the central vertex gives an L_w that is **not** topologically uniform; eigenvalues depend on the k_i and m_i.

If all arms are identical (ℓ_i = ℓ, m_i = m, full S_n symmetry of the realization), then the weighted Laplacian is just a scalar multiple of the combinatorial Laplacian, and the spectrum is **{0, ω_arm², ω_arm² (with multiplicity n−1), ω_total²}** where ω_arm² = k/m is the single-arm clamped frequency and ω_total² = (n+1) ω_arm² is the "all leaves move opposite to center" radial breathing mode. **The (n−1)-fold degeneracy survives** because S_n is preserved by uniform-arm geometric realization.

**§14.2 Symmetry-breaking cascade.** Successive symmetry reductions of an n-armed star realization:

| Symmetry group | Condition | (n−1)-fold-eigenvalue fate |
|---|---|---|
| **S_n** (abstract topology) | combinatorial Laplacian; or, weighted Laplacian with all arms exchangeable by labeling | (n−1)-fold degenerate by S_n standard-irrep (§13.2) |
| **D_n** (dihedral, regular n-star) | regular geometric n-star: all arm lengths equal, all angles 2π/n, planar; symmetry includes n rotations + n reflections | partial — standard S_n irrep restricts to D_n irreps |
| **C_n** (cyclic) | equal arm lengths but unequal angles (e.g., 70°, 70°, 70°, 70°, 80° for n=5); rotation-only symmetry | further partial restriction |
| **{e}** (trivial) | generic unequal arms and angles | no enforced degeneracy; (n−1) generic distinct eigenvalues |

The **representation-theoretic restriction** of the S_n standard irrep to D_n (n-dihedral) gives:

- **D_n irrep decomposition of S_n standard irrep:** the standard irrep of S_n is (n−1)-dimensional; restricting the action to the dihedral subgroup D_n ⊂ S_n (where D_n acts by the natural rotation/reflection action on the n leaves of the regular star) gives a (n−1)-dim representation of D_n. For n even, this decomposes into n/2 − 1 two-dimensional D_n irreps plus 1 one-dimensional sign-type irrep; for n odd, (n−1)/2 two-dimensional D_n irreps.

So under D_n symmetry, the (n−1)-fold S_n-standard eigenvalue **splits** into:

- **n odd** (say n = 5): (n−1)/2 = 2 two-dim doubly-degenerate eigenspaces. Multiplicity pattern: (2, 2). Specifically, n=3 ⇒ one doubly-degenerate eigenspace (the n−1 = 2 degeneracy survives because D_3 = S_3, the standard irrep is irreducible); n=5 ⇒ pattern (2, 2); n=7 ⇒ (2, 2, 2).
- **n even** (say n = 4): n/2 − 1 = 1 two-dim doubly-degenerate eigenspace plus one one-dim singlet. Multiplicity pattern: (2, 1). Specifically, n=4 ⇒ (2, 1); n=6 ⇒ (2, 2, 1).

Further restriction to **C_n** (cyclic, no reflections): every D_n irrep of dim 2 restricts to a sum of two 1-dim C_n irreps (complex conjugate pair, real-eigenvalue-degenerate). Pattern stays the same dimension-wise, but the "doubling" is now from time-reversal / complex-conjugacy, not from a discrete reflection: still doubly-degenerate (eigenvalues come in complex-conjugate pairs that are equal as real numbers). Trivial group: no degeneracy forced.

**§14.3 Verdict on whether S_n structure survives.** **Partially.** The S_n standard irrep is the load-bearing structural object on K_{1,n} when the *abstract topology* alone is the symmetry. When the *geometric realization* breaks S_n down to D_n or C_n, the (n−1)-fold S_n-degeneracy **fragments** into D_n / C_n-irrep blocks — typically into pairs of doubly-degenerate eigenvalues (for the "E"-type irreps of D_n / C_n, which are 2-dimensional). This is the **same Wigner / Bouckaert-Smoluchowski-Wigner mechanism** as standard solid-state band theory and molecular vibration spectroscopy under the C_3v, C_4v, D_5, D_6 point groups (Bouckaert, Smoluchowski, Wigner 1936 *Phys. Rev.* 50:58; Wigner 1937 *Phys. Rev.* 52:191; Cotton 1990 *Chemical Applications of Group Theory* §6 on normal-mode reduction).

The **fragmentation pattern is itself a falsifiable signature**: a physical realization claimed to have D_n symmetry should show E-type (doubly-degenerate) pairs in the predicted count; observing the full (n−1)-fold S_n-degeneracy implies the realization has *more* symmetry than the geometric design suggests (the topological symmetry has not been broken), and observing fewer-than-predicted degeneracies implies the realization has *less* symmetry (engineering tolerance / asymmetric assembly).

**§14.4 Honest-negative.** The angle-reweighted Laplacian story does **not** produce new mathematical content beyond the classical machinery of symmetric-mechanism vibration analysis (Bouckaert-Smoluchowski-Wigner 1936; Cotton 1990; Hammermesh 1962 *Group Theory and Its Application to Physical Problems* ch. 9). What it *does* is sharpen the §13.7 prediction: instead of just "the (n−1)-fold S_n degeneracy should appear in a physical K_{1,n} mechanism," the refined prediction is "the (n−1) modes fragment under the geometric-realization symmetry group G ⊂ S_n into a specific D_n / C_n / trivial irrep pattern determined by branching rules." This is **standard textbook character-theory** applied to mechanism design; the contribution is identifying that the project's static-X-bar / V-junction-K_{1,n} catalog inherits this entire reduction framework "for free" from the symmetric-group rep theory of §13.

**§14.5 Connection to project tooling.** No new module is required for the angle-reweighted analysis if the user wants only the *spectral-multiplicity pattern under given geometric symmetry*: the calculation is dim-counting in S_n standard ↓ G branching rules. If the user wants the *actual eigenfrequencies for given arm lengths and tip masses*, this is a numpy.linalg.eigh call on the 5×5 (n=4) or (n+1)×(n+1) weighted Laplacian; ~10-line addition to the `crossed_slot_transform_rotating.py` scope of §12.6, **not** a new module. The V-as-primitive construction itself is a constructor function — `make_K1n(n_arms, angles, lengths)` returning a weighted-graph object — that fits naturally in the same module.

**Reference anchors for §14:**
- **Bouckaert, L., Smoluchowski, R. & Wigner, E.** (1936). "Theory of Brillouin Zones and Symmetry Properties of Wave Functions in Crystals." *Phys. Rev.* **50**: 58–67. — canonical group-theoretic eigenvalue splitting under symmetry reduction. [pre-2020, classical]
- **Cotton, F. A.** (1990). *Chemical Applications of Group Theory* (3rd ed.). Wiley. ISBN 0-471-51094-7. — §6 normal-mode reduction; §4 character-table branching for D_n ↓ subgroup. [textbook, pre-2020]
- **Hammermesh, M.** (1962). *Group Theory and Its Application to Physical Problems*. Addison-Wesley. — ch. 9 on subgroup branching of irreps. [textbook, pre-2020]
- **Healey, T. J.** (1988). "A group-theoretic approach to computational bifurcation problems with symmetry." *Comp. Methods Appl. Mech. Eng.* **67**: 257–295. — group-theoretic structural-mechanics decomposition under symmetry, including D_n and C_nv. [pre-2020]
- **[2024 Engineering Structures paper, ScienceDirect:S0141029624012239]** "Decomposition of the degenerate subspace of C_3v-symmetric structural configurations." [Listing-verified on ScienceDirect; author list not PDF-verified per `[[feedback_pdf_extraction_citation_discipline]]`. The paper presents structural-mechanics-domain operators for splitting the doubly-degenerate E-irrep eigenspace of C_3v configurations, which is exactly the n=3 case of the §14.2 framework applied to a structural-engineering target. Useful project-side cross-reference; precise citation pending PDF verification.]

---

## 15. Odd-n cases explicitly: K_{1,3}, K_{1,5}, K_{1,7}

The user's claim that "V-junctions enable odd arms" is structurally correct (per §14): the V-primitive contributes 2 arms at any angle, and combining V's with single arms gives any n. **Odd n is where the structure is genuinely new** relative to the §10 X-bar two-perpendicular-full-bars realization. This section pins down what odd K_{1,n} look like.

**§15.1 K_{1,3} = D_4 — the unique finite-type case.**

- **Combinatorial Laplacian spectrum:** {0, 1, 1, 4} per Chung 1997 formula at n=3. Eigenvalue 1 has multiplicity 2 = n−1 (S_3 standard irrep, which is 2-dimensional, the unique 2-dim irrep of S_3).
- **Dynkin classification:** K_{1,3} = D_4 in the standard finite-type ADE classification. The 4-node Dynkin diagram with one central node connected to 3 outer nodes IS D_4. This is the unique star-graph case that is a finite-type Dynkin diagram (per the Carbone-Chung-Cobbs-McRae-Nandi-Naqvi-Penta 2010 classification, the affine bound on K_{1,n} occurs at n = 4 and finite type at n ≤ 3; combined with the K_{1,1} = A_2 / K_{1,2} = A_3 cases, the only finite-type star is K_{1,3} = D_4). **D_4 carries the famous triality** — an order-3 automorphism rotating the 3 outer nodes (Cartan 1925 *La géométrie des groupes simples*; Helgason 1978 *Differential Geometry, Lie Groups, and Symmetric Spaces* ch. X). This S_3-rotation-of-outer-nodes is **exactly** the S_3 acting on leaves of K_{1,3} = D_4.
- **Coxeter number:** h(D_4) = 6. Note: top combinatorial-Laplacian eigenvalue is 4 = n+1, not 6 = h. The h vs n+1 mismatch confirms §13.3's honest-negative — "Coxeter h doesn't match top eigenvalue" is exemplified cleanly at n=3.
- **Triality + S_3 irrep on the (n−1)-fold eigenspace.** Triality is a Lie-algebraic statement; the §13.2 S_3 standard-irrep statement is a graph-Laplacian statement. They are the *same S_3 action* on the 3 outer vertices. The (n−1)-fold = 2-fold-degenerate normal modes of a regular-Y mechanism are exactly the 2-dim standard irrep of S_3, equivalently the 2-dim E-irrep of D_3 = C_3v (the symmetry group of the regular Y in the plane).
- **Predicted normal-mode pattern under D_3 = C_3v geometric realization:** spectrum has the structure {0 (A_1), ω_arm² (E, 2-fold-degenerate), ω_total² (A_1)} per §14.2. **This is the cleanest experimental test of the §13.7 prediction.** A planar three-armed mechanism with three identical arms at 120° (regular Y) — e.g., a compliant Y-flexure, a triple-beam tuning fork, a three-spoke MEMS resonator — should show **one doubly-degenerate normal-mode pair** and **two singletons** (the zero mode is just rigid translation of the center plus trivial labels; the high mode is the "all-leaves-moving-outward-while-center-moves-inward" radial breathing mode).
- **Published triple-beam tuning fork resonators (TBTF) exist** (Watanabe et al. 1990s on quartz triple-beam force sensors; Yan et al. 2018 in *J. Microelectromech. Syst.*; Trolier-McKinstry & Muralt 2004 reviews of piezoelectric MEMS resonators). These devices use the symmetric / antisymmetric mode pair of the three beams as the working transduction modes. **Search-verified mention, not PDF-verified** — the TBTF design space is real, the doubly-degenerate-mode prediction of §13.7/§15.1 is the expected experimental signature, but a precise project-side citation needs PDF verification.
- **Published 2024 ScienceDirect paper on C_3v doubly-degenerate-subspace decomposition** (cited in §14.5) is the structural-mechanics-domain direct analog of the §15.1 prediction; the n=3 V-junction K_{1,3} = D_4 mechanism falls in exactly its scope.

**Verdict for K_{1,3}:** Yes, the K_{1,3} = D_4 case **is** the cleanest experimental test of the §13 prediction. It is the unique n for which the star graph is a finite-type Dynkin diagram, the S_n = S_3 standard irrep coincides with the D_3 = C_3v irrep E (so no symmetry-cascade fragmentation under regular geometric realization), and published mechanism realizations (TBTF + Y-flexures) exist. Recommend project-side targeting this n=3 case for any near-term physical or simulation spike.

**§15.2 K_{1,5} — strictly hyperbolic Kac-Moody.**

- **Combinatorial Laplacian spectrum:** {0, 1, 1, 1, 1, 6} per Chung 1997 formula. Eigenvalue 1 has multiplicity 4 = n−1 (S_5 standard irrep, 4-dimensional).
- **Dynkin classification:** K_{1,5} is **strictly hyperbolic Kac-Moody**. Per the Carbone et al. 2010 classification: K_{1,5} is *not* finite type (top-eigenvalue criterion: largest eigenvalue of the adjacency matrix is √5 ≈ 2.236 > 2, the simply-laced finite/affine cutoff is at eigenvalue 2); *not* affine type (would require eigenvalue exactly 2); but the proper connected subdiagrams of K_{1,5} are K_{1,k} for k ≤ 4, which are finite (k ≤ 3) or affine (k = 4) — satisfying the hyperbolic criterion that "every proper connected subdiagram is finite or affine." K_{1,5} is **non-compact hyperbolic** (since it contains an affine subdiagram K_{1,4} = D̃_4) but is still strictly hyperbolic Kac-Moody in the Kac sense. The associated indefinite Kac-Moody algebra is the corresponding rank-6 hyperbolic Lie algebra in the Carbone et al. tables.
- **Predicted normal-mode pattern under D_5 = C_5v geometric realization** (regular 5-pointed-star at 72°): n−1 = 4 degeneracy fragments per §14.2 into (n−1)/2 = 2 doubly-degenerate two-dim irreps of D_5 — the E_1 and E_2 irreps. Spectrum structure: {0 (A_1), ω_arm² (E_1 ⊕ E_2, both 2-fold-degenerate, eigenvalue degenerate within each E-pair, eigenvalue **may or may not** be degenerate across the two E-pairs depending on the precise weighted-Laplacian; for the uniform-arm case ω_arm² is one number, so all 4 eigenvalues coincide), ω_total² (A_1)}.
- For pentagonal mechanisms, the published examples I can locate are pentagonal compliant flexures (Wittwer & Howell 2004 on compliant-mechanism design space) and 5-spoke wheel resonators in MEMS, but none of these target the K_{1,5} singular-crossing topology specifically. **Honest gap** for the n=5 case at the published-mechanism level; the math is clean and the Carbone et al. Kac-Moody classification is the deeper resonance.

**§15.3 K_{1,7} — also strictly hyperbolic Kac-Moody.**

- **Combinatorial Laplacian spectrum:** {0, 1, 1, 1, 1, 1, 1, 8} per Chung 1997 formula. Eigenvalue 1 has multiplicity 6 = n−1 (S_7 standard irrep, 6-dimensional).
- **Dynkin classification:** K_{1,7} adjacency-matrix top eigenvalue is √7 ≈ 2.646. Proper connected subdiagrams are K_{1,k} for k ≤ 6. But K_{1,6} is itself a problem: K_{1,6}'s proper subdiagram K_{1,5} is hyperbolic (per §15.2), so K_{1,6} fails the hyperbolic criterion ("every proper subdiagram finite or affine"). So **K_{1,n} for n ≥ 6 is NOT strictly hyperbolic Kac-Moody — it is "indefinite, of Lorentzian / over-extended type"** (Gritsenko-Nikulin 2010 classification framework cited in Carbone et al. 2010 §1). K_{1,7} is in the same Lorentzian-not-hyperbolic class.
- Note the **arithmetic discontinuity**: K_{1,3} finite, K_{1,4} affine, K_{1,5} strictly hyperbolic, K_{1,6+} merely indefinite Lorentzian. The Dynkin classification is more finely graded than the simple "linear in n" combinatorial Laplacian spectrum suggests. n=5 is the unique hyperbolic case in the K_{1,n} family.
- **Predicted normal-mode pattern under D_7 = C_7v geometric realization:** n−1 = 6 fragments into (n−1)/2 = 3 doubly-degenerate two-dim irreps (E_1, E_2, E_3 of D_7). All E-pairs are eigenvalue-degenerate within each pair under uniform-arm symmetry.

**§15.4 Summary of odd-n classification.**

| n | Dynkin type | h | Adjacency top eigenvalue | (n−1) | D_n geometric-realization splitting of (n−1)-fold eigenvalue |
|---|---|---|---|---|---|
| 3 | D_4 (finite) | 6 | √3 ≈ 1.732 | 2 | E (2) — unchanged (S_3 = D_3) |
| 5 | strictly hyperbolic | — | √5 ≈ 2.236 | 4 | E_1 (2) ⊕ E_2 (2) — two doubly-degenerate pairs |
| 7 | Lorentzian (indefinite, not hyperbolic) | — | √7 ≈ 2.646 | 6 | E_1 (2) ⊕ E_2 (2) ⊕ E_3 (2) — three doubly-degenerate pairs |

**Verdict.** K_{1,3} = D_4 **is** the cleanest experimental test because (i) it is the unique finite-type case, (ii) the S_n = S_3 standard irrep coincides with the geometric-realization D_3 = C_3v irrep (no further fragmentation under symmetric realization, so the prediction is *just* "one doubly-degenerate pair"), and (iii) published mechanism analogs (TBTF, Y-flexure) exist. For n=5 and beyond, the prediction is **multiple** doubly-degenerate pairs which is a more involved measurement to verify.

**§15.5 Honest-negative recap.** I cannot locate a published mechanism-domain paper that connects the K_{1,n} = D_4 / affine-D_4 / hyperbolic-Kac-Moody classification to physical multistable mechanism design. The connection is direct (the §13–§15 chain of equalities), but it is not standardly drawn in the mechanism-theory literature. The Kac-Moody classification is mature mathematical physics (Carbone et al. 2010, Kac 1990 *Infinite Dimensional Lie Algebras*); the mechanism-theory classification of multistable / multi-arm mechanisms is mature (Howell 2001; Norton 2012); the cross-domain bridge — *which* Dynkin type a given n-arm mechanism realizes, and what physical signatures that Dynkin type predicts — is not standardly stated.

**Reference anchors for §15:**
- **Carbone, L., Chung, S., Cobbs, L., McRae, R., Nandi, D., Naqvi, Y. & Penta, D.** (2010). "Classification of hyperbolic Dynkin diagrams, root lengths and Weyl group orbits." *J. Phys. A: Math. Theor.* **43**(15): 155209. arXiv:1003.0564. [PDF-verified via WebFetch, pages 1-10, including the relevant Section 3 classification statement of hyperbolic vs Lorentzian K_{1,n} for n ≥ 4]
- **Kac, V.** (1990). *Infinite Dimensional Lie Algebras* (3rd ed.). Cambridge UP. ISBN 0-521-46693-8. — canonical reference for Kac-Moody classification framework; chapters 4-5 develop finite/affine/indefinite classification. [textbook, pre-2020]
- **Cartan, É.** (1925). *La géométrie des groupes simples*. Annali di Matematica. — original triality of D_4. [historical reference]
- **Helgason, S.** (1978). *Differential Geometry, Lie Groups, and Symmetric Spaces*. Academic Press. — ch. X covers D_4 triality. [textbook, pre-2020]
- **Wittwer, J. W. & Howell, L. L.** (2004). "Mitigating the Effects of Local Flexibility at the Built-In Ends of Cantilever Beams." *J. Appl. Mech.* **71**(5): 748–751. — pentagonal compliant-flexure design space context; not specifically K_{1,5}. [pre-2020, search-verified]
- **Triple-beam tuning fork (TBTF) literature** — multiple sources verified by search listing (Watanabe et al. 1990s quartz; Yan et al. 2018 in MEMS; Trolier-McKinstry-Muralt 2004 review); **author lists and exact publication details pending PDF verification per `[[feedback_pdf_extraction_citation_discipline]]`**. Cited here only for direction-of-existing-work, not for downstream technical claims.

---

## 16. Rotating-frame extension to arbitrary n

The §12 2-bit invariant `(support_cardinality, regularity)` was derived for the n=4 X-bar with two arm-rules (ℤ/4 cyclic vs Klein-four pair-opposite). This section extends to arbitrary K_{1,n} with rotating frame and asks: for general n, what arm-rules are possible, and does the §12 invariant generalize?

**§16.1 Arm-rules as transitive permutation subgroups of S_n.**

An arm-rule that determines how the pin transitions between arms during each crossing event is a **permutation of the n arm labels**. Over many crossings, the rule generates a subgroup of S_n acting on the arm-label set. **For the long-time arm-visit support to be the entire set of arms, the generated subgroup must act transitively on the n arms** (otherwise the pin is stuck in one orbit).

Thus admissible arm-rules ↔ **transitive subgroups of S_n acting on {1, 2, ..., n}**.

Per OEIS A002106 (number of transitive permutation groups of degree n; verified via web search):

| n | # transitive subgroups | Subgroups (selected) |
|---|---|---|
| 1 | 1 | {e} |
| 2 | 1 | S_2 = ℤ/2 |
| 3 | 2 | ℤ/3, S_3 |
| 4 | 5 | ℤ/4, V_4 (Klein-four), D_8, A_4, S_4 |
| 5 | 5 | ℤ/5, D_10, F_20 (= AGL(1,5)), A_5, S_5 |
| 6 | **16** | ℤ/6, S_3 (acting on cosets), D_12, A_4 (as cosets), and 12 others |
| 7 | 7 | ℤ/7, D_14, F_21 (= ℤ/7 ⋊ ℤ/3), F_42 (= AGL(1,7)), PSL(2,7), A_7, S_7 |

**The §12 framework had 2 cases at n=4 (ℤ/4 cyclic and Klein-four pair-opposite)**, which corresponds to choosing the two minimum-order regular-acting subgroups of S_4 — both are abelian of order 4. (The other 3 transitive subgroups of S_4 — D_8, A_4, S_4 — have orders 8, 12, 24 and act non-regularly; they correspond to arm-rules that are *not* permutations-generated-by-one-step but more complex multistep dynamical rules.)

**§16.2 Prime-n rigidity.**

For **prime p**, the transitive subgroups of S_p form a chain: ℤ/p ⊂ D_{2p} ⊂ F_{p(p−1)} = AGL(1,p) ⊂ ... ⊂ A_p ⊂ S_p. The minimum is the cyclic group ℤ/p (the unique transitive subgroup of order p), and the maximum is S_p. The number of intermediate subgroups depends on the divisor structure of p−1 (giving subgroups of AGL(1,p) of order p·d for each d | p−1):

- n = 3: ℤ/3 (order 3), S_3 (order 6). Two transitive subgroups, both contain ℤ/3 as a normal subgroup.
- n = 5: ℤ/5, D_10 (order 10), F_20 = AGL(1,5) (order 20), A_5, S_5. Five transitive subgroups.
- n = 7: ℤ/7, D_14, F_21 (= ℤ/7 ⋊ ℤ/3), F_42 = AGL(1,7), PSL(2,7) (≅ GL(3,2), order 168), A_7, S_7. Seven transitive subgroups.

**For odd-prime n with the simplest "step" arm-rule (one transition per crossing → generator is a single p-cycle), the generated subgroup is ℤ/p — the cyclic rule is the unique simple rule.** This is the rigid odd-prime statement of the user's brief: "for odd-prime n only Z/n and S_n" is **only approximately** right — there are intermediate subgroups for n = 5 (D_10, F_20, A_5) and n = 7 (D_14, F_21, F_42, PSL(2,7), A_7). What is rigid is that **the unique transitive subgroup of order p is ℤ/p**, generated by a single p-cycle.

**§16.3 Composite n and additional sub-rules.**

For composite n, transitive subgroups can have order strictly less than the full S_n and strictly more than ℤ/n — these are the source of "Klein-four-like" sub-rules. The two key composite cases visible to the X-bar / hex-star regime:

- **n = 4**: 5 transitive subgroups. The §12 framework picks 2: ℤ/4 (single 4-cycle generator) and V_4 = Klein-four (two commuting 2-cycles, generators τ_1 = (1 3) and τ_2 = (2 4)). The other 3 — D_8 (dihedral of order 8), A_4 (alternating, order 12), S_4 (full, order 24) — would correspond to arm-rules with *multiple* allowed transitions per crossing (e.g., D_8 = cyclic + reflection, allowing both ℤ/4 rotation and an "arm-pair flip" reflection). These are higher-complexity rules.
- **n = 6**: 16 transitive subgroups. Possible arm-rules include ℤ/6 (single 6-cycle), S_3 (acting on 6 = 3+3 cosets), D_12 (dihedral of order 12), and 13 others. The hexagonal-star rotating mechanism has the richest sub-rule landscape.

**§16.4 Generalization of the §12 2-bit invariant.**

The §12 invariant was `(support_cardinality ∈ {2, 4}, regularity ∈ {periodic, uniform})`. For general n with arm-rule generating subgroup G ≤ S_n:

- **Support cardinality** is the size of the orbit of the starting arm under G. If G is transitive, this is n (all arms visited). If G is intransitive (e.g., for n=4, the subgroup V_4 acting on arms grouped by opposite-pair has 2 orbits of size 2 — but it IS transitive on its component), the support is the orbit size of the starting arm.

**Important refinement**: the §12 Klein-four rule is actually **transitive on each connected component**, but the *cover splits into two components* (per §11). The "support cardinality 2" for Klein-four arose because the pin, starting on one component, never visits the other component — but within its component, all 2 arms are visited. The general-n statement is: support cardinality is the **size of the connected component of the cover containing the pin's starting arm**, equivalently **the size of the orbit of the starting arm under G**.

So the generalized first invariant is:

> **Generalized §12 invariant 1 (support cardinality):** size of the orbit of starting arm under G; takes values in {divisors of n that are realizable as orbit sizes of a transitive-or-intransitive subgroup of S_n}.

For transitive G acting on n arms, the orbit is all of {1, ..., n}, size n. The only way to get smaller support is to **choose a rule whose generating subgroup is intransitive but transitive on a sub-orbit** — i.e., the dynamics ARE "transitive on a part of {1,...,n}, fixing the rest." For n=4 Klein-four-pair-opposite, the *interpretation* in §11/§12 is that one of the rule's generators is (1 3) and the other is (2 4) — these are disjoint 2-cycles, so the group ⟨(1 3), (2 4)⟩ = Klein-four-V_4 has **two orbits of size 2 each** when viewed as acting on the set {1,2,3,4} — and the §12 framework correctly notes the pin stays in one of the two orbits.

So the generalized invariant **takes values in {divisors of n that are realizable as orbit sizes of some subgroup of S_n acting on n arms by the rule's structure}**:

- **n = 3 (prime, odd)**: divisors are 1, 3. Only 3 is achievable for a non-trivial rule (orbit size 1 means no transition); generalized invariant is {3} (rigid).
- **n = 4**: divisors are 1, 2, 4. Achievable: 2 (Klein-four-V_4-style with disjoint 2-cycle generators), 4 (transitive). Matches §12.
- **n = 5 (prime, odd)**: divisors are 1, 5. Only 5 is achievable non-trivially.
- **n = 6**: divisors are 1, 2, 3, 6. All of {2, 3, 6} are achievable (e.g., 2 via three disjoint 2-cycles; 3 via two disjoint 3-cycles; 6 via 6-cycle). Three distinct support cardinalities.
- **n = 7 (prime, odd)**: divisors are 1, 7. Only 7 is achievable non-trivially.

**Verdict for §16.1:** The 2-bit invariant generalizes cleanly to **(orbit size ∈ {non-trivial divisors of n realizable as orbits}, regularity ∈ {periodic, uniform})**. For **prime n the orbit-size invariant collapses to a single value** (= n, since the only transitive subgroup-orbit on prime cardinality is the full set or a trivial fixed point) — *one-bit* invariant (just regularity, periodic vs uniform). For **composite n it generalizes**: n=4 gives 2 orbit-sizes (matches §12); n=6 gives 3; in general the number of distinct orbit-size values equals the number of distinct non-trivial divisors of n.

**§16.5 Regularity invariant (second bit) generalization.**

Regularity is determined by **ω_pin / ω_frame ∈ ℚ vs. ℝ \ ℚ**, independent of n or arm-rule. The §12 statement that "rational ⇒ periodic, irrational ⇒ uniform (Birkhoff ergodic on orbit)" holds for any n and any transitive arm-rule via the standard equidistribution theorem (Weyl 1916; Furstenberg 1981 *Recurrence in Ergodic Theory and Combinatorial Number Theory*). So the regularity bit is always present, independent of n.

**§16.6 Combined spike-protocol-ready invariant for general K_{1,n}.**

For a rotating K_{1,n} mechanism with arm-rule G ≤ S_n:

> **§16.6 generalized invariant pair:** `(orbit-size of starting arm under G, regularity bit)`. Orbit-size is a divisor of n; regularity is one bit. Total information content is `log_2(|divisors_realizable(n)|) + 1` bits.

| n | n_divisors_realizable | Total invariant bits |
|---|---|---|
| 3 | 1 | 1 (just regularity) |
| 4 | 2 (= {2, 4}) | 2 (§12 matches) |
| 5 | 1 | 1 |
| 6 | 3 (= {2, 3, 6}) | log_2(3) + 1 ≈ 2.58 |
| 7 | 1 | 1 |

**Prime-n cases are 1-bit; composite n are richer.** The user's intuition "odd primes are rigid" is confirmed: odd-prime n collapses the support-cardinality bit (giving only 1-bit total invariant). Composite n is where the rotating-frame structure gets genuinely richer.

**§16.7 Module-level extension.**

The §12.6 module `crossed_slot_transform_rotating.py` already has the infrastructure for §16: change the hard-coded n=4 to a parameter, expand the `arm_rule` choices from `{'cyclic_Z4', 'klein4'}` to a parametrized family `{'cyclic_Zn', 'klein_pairs', 'dihedral_Dn', ...}` per the relevant transitive subgroups of S_n, and the §12.5 algorithm sketch generalizes mechanically. The orbifold-Laplacian spectrum becomes a sum over orbit-sized circles per §12.2 generalized to general orbit-size; the trajectory simulation generalizes mechanically.

**§16.8 Honest-negative.** I find no published mechanism-theory work that connects general-n rotating-frame branched-covering kinematotropic mechanisms to the transitive-permutation-group classification per OEIS A002106. The branched-covering / orbifold framework (Emmrich-Römer 1990) and the transitive-subgroup classification (Hulpke 2005 "Constructing Transitive Permutation Groups") are both mature; the bridge to mechanism design is the project's contribution. The classification of which transitive subgroup is realized by a given physical arm-rule (e.g., distinguishing ℤ/n rotation from D_{2n} rotation+reflection in a specific mechanism) is the experimental question opened by §16 — and the orbit-size + regularity invariants of §16.6 are the falsifiable observables.

**Reference anchors for §16:**
- **OEIS A002106** — "Number of transitive permutation groups of degree n." Values 1, 1, 2, 5, 5, 16, 7, 50, 34, 45, 8, 301 for n = 1, 2, ..., 12. [web-search-verified]
- **Hulpke, A.** (2005). "Constructing transitive permutation groups." *J. Symbolic Computation* **39**(1): 1–30. — algorithmic generation of transitive subgroup catalog. [pre-2020, search-verified]
- **Conway, J. H., Hulpke, A. & McKay, J.** (1998). "On Transitive Permutation Groups." *LMS J. Comput. Math.* **1**: 1–8. — classical reference for the transitive-group classification up to degree 31. [pre-2020]
- **Weyl, H.** (1916). "Über die Gleichverteilung von Zahlen mod. Eins." *Math. Ann.* **77**: 313–352. — equidistribution theorem; ground truth for the §12 "irrational ⇒ uniform Birkhoff" generalization. [historical reference]
- **Furstenberg, H.** (1981). *Recurrence in Ergodic Theory and Combinatorial Number Theory*. Princeton UP. — ergodic-theory framing of the regularity bit for general n. [textbook, pre-2020]

