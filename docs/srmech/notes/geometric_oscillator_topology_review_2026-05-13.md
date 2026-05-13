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
