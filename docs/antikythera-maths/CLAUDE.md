# `docs/antikythera-maths/` — research scope and method

This subdirectory is **research, not fabrication**. Anyone (human or LLM) working in this tree should pick the right tool for the right question.

The line here is the **modelling approach**, not the **objects modelled**. We absolutely do model gears, leaves, slots, pins, pointers, and their spatial motion. We just do it from the algebra / spectral side — phase space, cyclic groups, graph-Laplacian eigenbasis, projected back out to spatial movement — not from the CAD / mechanical-engineering side.

## What this project IS

A **mathematical-structural** investigation of the Antikythera mechanism, framed as:

- **HDC / cyclic-group algebra** — every gear is a faithful representation of ℤ/nℤ; every mesh is a rational map; every pointer is a hypervector. Encoding lives in [`research/encode_ant.py`](research/encode_ant.py).
- **Phase-space / spectral analysis** — period relations as Diophantine approximations; prime spectra; Pareto fronts of (precision, cost). [`research/pareto_analysis.py`](research/pareto_analysis.py), [`research/packing_analysis.py`](research/packing_analysis.py).
- **Graph-Laplacian eigenbasis → projected spatial movement.** The gear-DAG Laplacian spectrum is the natural basis for projecting from the cyclic-group algebra back out to spatial pointer motion. A pin-and-slot's output, a leaf-and-pinion engagement, an equant pointer's longitude — all are phase-space transforms, projected. Modelling those mechanisms this way (algebra + eigenbasis + projection) is exactly in scope.
- **Hypothesis battery** — falsifiable claims about the encoder's structural properties, evaluated against ephemeris ground truth or against itself. [`research/consolidated_tests.py`](research/consolidated_tests.py).
- **Parameter-variation studies** — sweeps over named parameter sets (Almagest IX.5, Freeth 2012, Freeth 2021, etc.) with the existing analytic models. Adding new `MarsParams` / `VenusParams` / etc. is in scope.
- **Architectural-mode hypotheses** — the §11.6 thread on missing-gear placement, periphery rule, setting-mode gears. These are *graph-theoretic* claims about gear-DAG structure, expressible in the same Laplacian eigenbasis.

## What this project IS NOT

A **CAD-grade / fabrication-level reconstruction** of the bronze. Specifically out of scope here:

- **CAD-grade mesh-contact / tooth-profile / axle-precession modelling.** Don't introduce mechanical-engineering models of physical gear-tooth engagement, axle wobble, lubricant behaviour, strain, or fabrication-tolerance geometry. That's CAD work; it belongs in a CAD / mechanical workspace, not here. (Projecting phase-space / eigenbasis representations to spatial pointer motion is **not this** — that's the project's primary mode of getting to spatial behaviour, and it's welcome.)
- **Pin-and-slot reuse beyond D-H1.** [`research/pin_and_slot.py`](research/pin_and_slot.py) is the **D-H1 T-symmetry primitive** for the lunar pin-and-slot (Freeth 2006, ε ≈ 0.054). The transform itself — `atan2(sin θ, cos θ - eps)` — is a perfectly fine phase-space map, and modelling pin-and-slot mechanisms via phase-space transforms is exactly in scope. The module's *semantics* aren't general: it asserts "this is the D-H1 lunar mechanism." Don't import it under `mars_pin_and_slot`, don't add a `mars_longitude_bronze` that delegates to it. If you want a planetary pin-and-slot phase-space transform, derive it cleanly from the gear ratios in `equant_encoder.py` / `gear_database.py` — same math, clean provenance.
- **Gear-train fabrication / wear / lubricant modelling.** [`research/manufacturing_tolerance.py`](research/manufacturing_tolerance.py) models multiplicative tooth-pitch noise as a *statistical* perturbation on the cyclic-group ratios — that's in scope. Anything beyond that (CAD-style mesh contact analysis, strain modelling, lubricant stiction, etc.) is out of scope.
- **Fragment-alignment / 3D fabrication geometry / orrery CAD.** [`research/rendering.py`](research/rendering.py) is a Patch-3 angle → (x, y) projection for dial layout. It is intentionally not a fabrication 3D reconstruction. Don't extend it to physical 3D placement, mass, inertia, fragment alignment, or CAD-grade gear geometry.

## Why the line

The algebra / phase-space / eigenbasis framing is the project's contribution. It produces falsifiable claims (the H-battery), traceable through cyclic-group algebra and graph-Laplacian spectra, that other Antikythera literature does not (or rarely) make. Crucially, this framing *does* reach spatial pointer motion — by projection from the eigenbasis, not by CAD.

CAD-grade reconstruction is a different discipline: mechanical engineering, fabrication tolerance, fragment-alignment 3D. It is well-served by existing literature (Freeth 2006, 2021; Wright; AMRP) and proper CAD tooling. Duplicating that here under the rubric of "bronze fidelity" doesn't earn its complexity. If a future project needs a true CAD / mechanical-engineering model, it lives in a separate workspace (`docs/antikythera-physical/` or similar). Until that workspace exists, treat CAD-level questions as **deferred to a different project**, not as additions here.

## Practical guidance for LLMs working in this tree

When you're tempted to add "let me model what the bronze actually does":

1. **First — yes, model it.** Modelling gears, leaves, slots, pins, and their spatial output is in scope. Cyclic-group ratios, period relations, rational maps between ℤ/nℤ representations, graph-Laplacian eigenbasis, projection from the eigenbasis to spatial pointer motion — all welcome.
2. **Stop and ask: am I modelling at the algebra / eigenbasis level (then projecting to spatial motion), or am I modelling at the CAD level (mesh contact, tooth profiles, axle wobble, fabrication geometry)?** The first is in scope, even when the output is spatial. The second belongs in a separate workspace.
3. **Check if the existing module already covers it.** Almost everything you might want has already been factored as either a parameter on an analytic model, a graph-theoretic property in `gear_topology.py` / `gear_database.py`, or an algebraic encoding in `equant_encoder.py` / `encode_ant.py`. Add to those rather than introducing a parallel "CAD" path.
4. **If a contributor is asking for "true to bronze"** — read it as "true to the *cyclic-group ratios* and *parameters* the bronze implements, projected back to spatial motion via the eigenbasis," not "true to the *CAD-level fabrication geometry* of the bronze." Use named param sets (Almagest, Freeth 2012, Freeth 2021) to differentiate which mechanism's parameters you're testing.
5. **The architectural-mode thread (§11.6 of the notebook)** discusses crank-as-clutch / selective-lock / setting-mode-gears at the level of graph-theoretic placement on the gear DAG. Those are claims about *which gears are missing and where they attach*, expressible in the Laplacian eigenbasis — not CAD claims about mechanical fabrication.

## In-scope work this directory welcomes

- Adding hypothesis rows to the H-battery
- Adding named `MarsParams` / `VenusParams` / etc. for different reconstruction sources
- Phase-space / cyclic-group encodings of new or hypothesised gear ratios
- Graph-Laplacian eigenbasis analyses of the gear DAG
- Projection-to-spatial-motion pipelines that derive pointer behaviour from the eigenbasis (including pin-and-slot, leaf-and-pinion, equant — when derived cleanly from algebra)
- Sweeps over (precision, cost) Pareto fronts
- Cross-references to MUL.APIN / Almagest period relations
- Architectural-mode evaluators on `MESH_EDGES` (gear-DAG centrality, periphery rule)
- Manufacturing-tolerance Monte Carlo on existing cyclic-group ratios
- ΔT / ephemeris-kernel choice studies
- Document-hygiene updates that keep the notebook's framing aligned with the code

## Out-of-scope work that should not land here

- CAD-grade mesh-contact / tooth-profile / axle-precession / lubricant modelling
- Reuse of the D-H1 pin-and-slot **module** (its lunar semantics) for non-lunar mechanisms — derive a parallel phase-space transform from algebra instead
- Fragment-alignment 3D / physical layout reconstruction of the missing planetary plate
- Wear / stiction / lubricant kinematics
- Anything that requires *fabrication-level* fidelity beyond the cyclic-group ratios and Laplacian-eigenbasis projection

If unsure, the rule of thumb: **am I modelling at the algebra / eigenbasis level (then projecting to spatial motion), or am I modelling at the CAD / fabrication level (mesh contact, tooth profiles, axle wobble)?** Algebra / eigenbasis → in scope, even when the result is spatial pointer motion. CAD / fabrication → not here.
