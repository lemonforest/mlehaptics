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

## 12. Reference anchors added in §10–§11 (verified via WebFetch unless flagged)

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

---

## 13. Re-evaluation of Moves 2 and 3 (post §10–§11)

**Move 2 — focused-subagent computation of the branched-configuration Laplacian spectrum.** §10's closing-sketch already supplies the combinatorial K_{1,4} spectrum {0, 1, 1, 1, 5} from textbook (Chung 1997) and the metric-Laplacian framing from Kuchment 2004 quantum-graph theory. The "actual matrix construction + eigenvalue extraction + comparison to K₃/P₃" computation is **5×5 by-hand or a 10-line numpy.linalg.eigh call**; it does not need a dedicated subagent. **Recommendation: collapse Move 2 to a verification-and-write-up task** — confirm the closed-form spectrum by numerical computation (1 line of numpy), then add the K_{1,4} row to the project's existing state-transition Laplacian catalog (whichever module ends up hosting the multistable-mechanism table). The actual *new* computational work is in §11's rotating-frame case — the monodromy + orbifold-S¹ Laplacian sketch — which is non-trivial and **is** spike-worthy.

**Move 3 — main-agent in-conversation derivation of the X-graph Laplacian spectrum.** §10 has now derived this in-document; the in-conversation derivation would be redundant. **Recommendation: skip Move 3 as originally scoped.** The value-add it would have provided is now captured here.

**Replacement recommendation.** Spawn one focused subagent on the **rotating X-bar spike from §11** — implement `crossed_slot_transform_rotating.py` as a parallel module (D-H1 lock respected), compute the monodromy + orbifold Laplacian for both arm-choice rules and both rotation regimes, and produce a falsifiable invariants table. That is the genuine new computational content; the static case is now reference-grade.
