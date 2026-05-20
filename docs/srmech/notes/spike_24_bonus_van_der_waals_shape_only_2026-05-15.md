# Spike #24 bonus — van der Waals dispersion + shape-only graph Laplacian

**Date:** 2026-05-15. **Status:** conceptual sketch, not investigation. Possible Spike #25/#26 spec material.

User asked three connected questions during Spike #24 close-out:

1. *"Can we find primitives that govern van der Waals dispersion?"*
2. *"Can bond angles and polar/non-polar tails of different compounds carry the same graph Laplacian because all we care about is what does this shape look like vs how many different compounds can make this shape?"*
3. *"How do those structure shapes influence and interact with other structural shapes?"*

The Spike #24 vocabulary (14 primitive classes A–N) covers all three. The answer is short — **shape-only molecular abstraction IS Class L (graph Laplacian) instantiated at the molecular substrate**, and vdW dispersion factors cleanly through it with one polarisability projection.

## Q2 first (cleanest answer): same shape = same graph Laplacian

For a molecule represented as atoms-as-nodes + bonds-as-edges, the molecular graph Laplacian `L = D − A` (where `D` is the degree matrix and `A` is the adjacency matrix) is determined ENTIRELY by:

- Number of nodes (atom count)
- Edge structure (which atoms bond to which)
- Edge weights (optional bond-order weighting; pure-topology uses uniform weights)

Two molecules with the **same skeleton graph** — same node count, same adjacency, same edge weights — are **graph-isomorphic** and have **identical Laplacian eigenvalue spectra**. This is exactly what cheminformatics tools (RDKit, OpenBabel) compute when they hash molecules by topology, independent of which atoms occupy which nodes.

For the user's framing — *"bond angles and polar/non-polar tails of different compounds carry the same graph Laplacian"* — the answer is **yes**, with caveats:

- **Yes:** if "shape" means *skeleton graph topology* (which atoms are bonded, vertex degree pattern, loop structure), shape-graph-Laplacian is identical across compounds with that skeleton. Hexane and cyclohexane have different graphs; n-hexane and n-pentanol-with-OH-at-C1 have *similar but not identical* graphs.
- **Caveat:** "shape" in 3D conformational space adds bond-angle constraints + torsional preferences (the `Vτ(φ) = (V₃/2)(1 + cos(3φ))` Class K thing from Phase 6.1). 3D-shape equivalence is stricter than 2D-graph equivalence.
- **Caveat:** "polar/non-polar tails" carry atom-type information, which graph Laplacian by default ignores. If you weight nodes by *partial charge* or *polarisability*, you get a weighted Laplacian that distinguishes polar/non-polar — but this no longer is purely-shape.

The PURE-SHAPE primitive is `unweighted_graph_Laplacian(molecular_skeleton)` = **Class L**.

This connects to `[[user_stance_fiber_as_spatially_absent_encoding]]`: chemical identity (carbon vs nitrogen vs oxygen) is the *spatially-absent fiber over the molecular skeleton*; pure-topology projects to the same graph regardless of which atoms decorate the nodes. The graph Laplacian sees the shape but not the chemistry.

## Q1: primitives for vdW dispersion

London dispersion (the attractive vdW component from instantaneous-dipole / induced-dipole) has the form

```
U_vdW(r) ≈ −C_6(α_A, α_B; E_excitation) / r^6
```

where `C_6` depends on polarisabilities `α_A` and `α_B` of interacting atoms and their characteristic excitation energies (effectively molecular-size / electron-distribution metrics).

This does NOT factor through pure-topology Class L because it requires three non-topology ingredients:

1. **Polarisability `α`** — atom-specific (carbon ≠ neon ≠ argon), depends on electron-cloud fluctuation amplitude.
2. **Distance `r`** — 3D-geometry quantity, requires knowing actual coordinates, not just adjacency.
3. **`1/r^6` falloff** — continuous-distance function, lives in the *downstream-continuous-projection* class (per `[[user_stance_pi_as_projection]]`).

But vdW's *shape-only* component IS Class L on the **contact graph** (not the bond graph):

- **Contact graph:** atoms-as-nodes; edges between atoms that are within vdW distance (~3–5 Å) but NOT bonded.
- **Contact-graph Laplacian:** eigenvalue structure tells you the *modes of collective vdW interaction* — how many independent attractive-stabilisation modes the molecule has.

For shape-only vdW primitives:

- **Class L (contact graph)** captures *which* vdW interactions exist (topology of close-range non-bonded contacts).
- **Class J (period relations)** would capture *coordination numbers* (how many vdW contacts per atom, ratios across atom types).
- **Class K (equation-of-centre / pin-slot)** would apply if vdW-coupled rotational modes (librations in molecular crystals, methyl-rotor coupling) show Kepler-shape — testable, not tested.

The polarisability-weighting that gives actual interaction *strength* is downstream of these — `α_A · α_B` lives in continuous-quantity land per `[[user_stance_pi_as_projection]]`.

## Q3: shape × shape interaction

Two molecular shapes interact through the **bipartite contact graph** between them — atoms of molecule A linked by edges to atoms of molecule B that are within vdW range. The eigenvalue structure of THAT bipartite Laplacian determines:

- **Binding strength** — sum of `C_6 / r^6` over all contact edges. Atom-specific (polarisability-weighted), but the *edge structure* is shape-determined.
- **Binding specificity** — Fiedler partition robustness on the bipartite contact graph. Lock-and-key complementarity is a near-zero Fiedler eigenvalue.
- **Conformational complementarity** — kernel structure of the bipartite Laplacian indicates rigid-body modes of relative rotation/translation that preserve contact pattern.
- **Self-assembly** — when a molecule's shape generates a periodic contact pattern with copies of itself, that's *tiling*: the contact graph becomes a Cayley graph of the symmetry group, Class L eigenvalues match the regular-lattice spectrum.

This is **Class L instantiated at a higher level** — Class L on the contact graph between shapes, where the shapes themselves are Class L objects. The primitive doesn't multiply; it composes.

## What this is and isn't

**Is:** a recognition that the user's bonus questions point at a clean Class L instantiation at the molecular substrate that Spike #24's Phase 6 (chemistry) didn't explicitly catalog. Worth recording as confirmed-but-unverified-by-investigation.

**Isn't:** a new primitive class. No "Class O? — vdW dispersion" needed. The decomposition uses existing classes:

- Class L (contact graph) for *which* vdW interactions
- Class J (coordination numbers) for *how many* per atom
- Class K (collective rotational modes) for *whether* vdW-coupled librations show Kepler-shape — *testable*
- continuous-projection (`α_A · α_B / r^6`) for *interaction strength* — *not a primitive, downstream*

## Possible Spike #25 / #26 candidate scope

If the user wants to formalize this:

- **Spike candidate A:** Class L instantiation on the contact graph of representative molecules (alkanes, aromatics, peptide segments); validate that isoshape compounds have identical contact-graph Laplacian spectra; falsify if not.
- **Spike candidate B:** Test whether vdW-coupled torsional modes (e.g., methyl rotors in propane, ethane V₃ thermalization) show Kepler-shape harmonic structure under thermal forcing. Phase 6.1 already showed *static* ethane V₃ ≡ F24 cross-bar pin-slot at N=3; this candidate asks whether thermally-driven *dynamic* methyl rotor populations show the same Kepler signature as Brusselator/Oregonator/etc. did in Phase 9.2.
- **Spike candidate C:** Bipartite contact-graph spectra as binding-affinity predictor across a small ligand-receptor dataset. Cheminformatics already does this for QSAR; the spike would be validating the user's framing within the project's primitive-vocabulary lens.

Not opened now. Recorded for the conductor to decide on after Spike #24 closes.

## Cross-references

- `[[user_stance_kepler_shape_universal]]` — vdW-coupled libration test (candidate B) would extend Kepler-shape to molecular-crystal substrate.
- `[[user_stance_fiber_as_spatially_absent_encoding]]` — chemical identity is the spatially-absent fiber over molecular shape.
- `[[user_stance_pi_as_projection]]` — `1/r^6` and `α_A · α_B` are continuous-projection quantities, downstream of integer-cyclic shape primitives.
- Spike #24 Phase 6 — chemistry-substrate primitive instantiation (V₃ torsional potential = F24 cross-bar pin-slot).
- Spike #24 Phase 7.6.2 — Hückel 4n+2 rule = Class L on the π-orbital path graph; same primitive structure as this bonus question.
- Spike #24 Phase 9.5 — multi-substrate matrix update; CRN column added. Molecular-shape contact-graph would be a separate column if formalized.
