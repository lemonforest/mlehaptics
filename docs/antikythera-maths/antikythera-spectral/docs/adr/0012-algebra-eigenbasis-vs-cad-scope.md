# ADR 0012: Algebra/eigenbasis modelling, not CAD/fabrication

**Status:** Accepted (2026-05-02, v0.3.0)

## Context

`v0.3.0` introduces a new public model — `mars_longitude_bronze` — and three named Mars parameter sets (`PTOLEMY_MARS_PARAMS`, `FREETH_2012_MARS_PARAMS`, `FREETH_2021_MARS_PARAMS`). The bronze model is described as "the projection from the cyclic-group / graph-Laplacian eigenbasis representation of the Mars deferent gear ratios back to the pointer's spatial longitude."

That's a strong claim. It collides with a tempting alternative framing: "the bronze model is what the *physical* Antikythera mechanism would output if you simulated it kinematically." The two framings sound similar but lead to very different code.

This ADR pins which framing the package is built around, so future contributions stay coherent.

## The line

Two extreme positions:

1. **Pure algebra / phase space.** Every gear is a faithful representation of ℤ/nℤ. Every mesh is a rational map. Every pointer state is a hypervector in cyclic-group algebra. Spatial pointer motion is recovered by *projection* from the eigenbasis. The mechanism is studied at the level of period relations, prime spectra, Diophantine approximation, and graph-Laplacian eigenstructure. Nothing in the package's modelling runs continuous-time kinematics in (x, y, t).
2. **CAD / mechanical-engineering fabrication.** Gear teeth have profiles. Mesh contact has finite area. Axles wobble. Lubricant matters. Tolerance stack accumulates. Every motion is a consequence of physical forces and constraints in 3D.

These two framings model the same object — the bronze mechanism — but they produce different artefacts and answer different questions. Position (1) produces the H-battery, the period-relation Pareto fronts, the cyclic-group encoders. Position (2) produces tolerance Monte Carlo, fragment-alignment 3D reconstructions, finite-element stress analysis.

Position (2) is well-served by existing literature (Freeth 2006, 2012, 2021; Wright; AMRP) and proper CAD tooling. Duplicating it inside this package under the rubric of "bronze fidelity" doesn't earn its complexity, and conflates two distinct disciplines under one API surface.

## Decision

`antikythera-spectral` is a **position-(1) package**: algebra, phase space, cyclic groups, graph-Laplacian eigenbasis, projected to spatial pointer motion. Modelling gears, leaves, slots, pins, and their spatial output is in scope — done from the algebra/spectral side, not from the CAD side.

The line we draw is the modelling *approach*, not the *objects modelled*:

**In scope:**

- Cyclic-group / HDC encoders (`encode_ant`, `encoder` facade)
- Phase-space transforms — including the pin-and-slot transform `atan2(sin θ, cos θ + ε)` used in `mars_longitude_bronze`
- Graph-Laplacian eigenbasis projections of the gear DAG
- Projection from algebraic representations to spatial pointer angles
- Statistical perturbation of cyclic-group ratios (`manufacturing_tolerance.py`)
- Closed-form geometric quantities expressed via law of cosines / pure trig of angles + side lengths (no Cartesian decomposition required)

**Out of scope:**

- CAD-grade mesh-contact, tooth-profile, or axle-precession modelling
- Continuous-time kinematic simulation of bronze gear trains
- Reuse of `_research.pin_and_slot` (the lunar D-H1 module) as a general planetary primitive — derive the same shape inline from the planet's gear-ratio algebra instead
- Fragment-alignment 3D / fabrication geometry
- Wear / stiction / lubricant kinematics

## Implementation discipline

Two concrete coding rules follow:

1. **No (x, y) Cartesian decomposition where law-of-cosines / pure-trig forms suffice.** Distances and angles in the deferent geometry are expressed algebraically: `R_eff = sqrt(e² + R² + 2eR cos M)` rather than `sqrt((e + R cos M)² + (R sin M)²)`. Same number, cleaner framing — the algebra-first form makes the "model what the bronze does, project from algebra" claim transparent at the implementation level. Applied throughout `mars_longitude_epicycle_only`, `mars_longitude_equant`, and `mars_longitude_bronze` in v0.3.0.
2. **The pin-and-slot transform `atan2(sin θ, cos θ + ε)` is in scope for `mars_models.py`; the `_research.pin_and_slot` module's lunar D-H1 semantics are not.** When `mars_longitude_bronze` needs the same mathematical shape as the lunar pin-and-slot, it constructs the transform inline rather than importing the lunar module under another name. The lunar module stays scoped to its T-symmetry-breaking analysis.

Reference truth (`compare_ephemerides`, `_research.astronomical_ground_truth`) sits *outside* this scope — JPL DE-series ephemerides are the ground truth we measure our algebraic models against, not models of the bronze. They legitimately use spatial geometry; that's their job.

## Consequences

- ✅ The bronze model's framing in `mars_models.py` is internally consistent.
- ✅ Future contributors know where to add new planetary models (algebra-first) and where they would NOT fit (CAD).
- ✅ The package's API surface stays in one discipline; users with CAD-adjacent questions know to look elsewhere.
- ⚠ If a future project needs a true CAD / mechanical-engineering model of the mechanism, it lives in a separate workspace (`docs/antikythera-physical/` or similar), not here. The `_research/CLAUDE.md` memo and this ADR both flag the boundary.

## Cross-references

- Research-tree memo: `docs/antikythera-maths/CLAUDE.md` (LLM-facing scope guidance for the research scaffold)
- `mars_models.py` docstring (audience-facing scope summary for package consumers)
- `figures/mars_38deg_gap_findings.md` (the audit that motivated this ADR — ten analyses of the F&J 2012 38° Mars peak error, all conducted under position (1) discipline)
- `_research/equant_encoder.py` (`mars_longitude_bronze` and the named param sets implementing the position-(1) discipline for Mars)
