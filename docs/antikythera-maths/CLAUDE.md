# `docs/antikythera-maths/` — research scope and method

This subdirectory is **research, not reconstruction**. Anyone (human or LLM) working in this tree should pick the right tool for the right question.

## What this project IS

A **mathematical-structural** investigation of the Antikythera mechanism, framed as:

- **HDC / cyclic-group algebra** — every gear is a faithful representation of ℤ/nℤ; every mesh is a rational map; every pointer is a hypervector. Encoding lives in [`research/encode_ant.py`](research/encode_ant.py).
- **Phase-space / spectral analysis** — period relations as Diophantine approximations; prime spectra; Pareto fronts of (precision, cost). [`research/pareto_analysis.py`](research/pareto_analysis.py), [`research/packing_analysis.py`](research/packing_analysis.py).
- **Hypothesis battery** — falsifiable claims about the encoder's structural properties, evaluated against ephemeris ground truth or against itself. [`research/consolidated_tests.py`](research/consolidated_tests.py).
- **Parameter-variation studies** — sweeps over named parameter sets (Almagest IX.5, Freeth 2012, Freeth 2021, etc.) with the existing analytic models. Adding new `MarsParams` / `VenusParams` / etc. is in scope.
- **Architectural-mode hypotheses** — the §11.6 thread on missing-gear placement, periphery rule, setting-mode gears. These are *graph-theoretic* and *topological* claims about gear-DAG structure, not motion simulations.

## What this project IS NOT

A **physical / mechanical reconstruction** of the bronze. Specifically out of scope here:

- **Mechanical-motion simulation.** Do not introduce models that simulate "what the bronze would actually output" via gear-train kinematics, pin-and-slot motion, axle-coupled transmission. Even when mathematically equivalent to an analytic model, that framing belongs elsewhere.
- **Pin-and-slot reuse beyond D-H1.** [`research/pin_and_slot.py`](research/pin_and_slot.py) exists for **one specific purpose**: the D-H1 T-symmetry-breaking analysis of the lunar pin-and-slot (Freeth 2006, ε ≈ 0.054). It is NOT a general-purpose mechanical primitive. Don't route Mars / Venus / Mercury equations of center through it. Don't add a `mars_longitude_bronze` that delegates to it. Don't rebrand it as a planetary-plate mechanism.
- **Gear-train fabrication / tolerance / wear modelling.** [`research/manufacturing_tolerance.py`](research/manufacturing_tolerance.py) models multiplicative tooth-pitch noise as a *statistical* perturbation on the cyclic-group ratios — that's in scope. Anything beyond that (CAD-style mesh contact analysis, strain modelling, lubricant stiction, etc.) is out of scope.
- **3D geometry / orrery rendering.** [`research/rendering.py`](research/rendering.py) is a Patch-3 angle → (x, y) projection for dial layout. It is intentionally not a 3D reconstruction. Don't extend it to physical 3D placement, mass, inertia, or fragment alignment.

## Why the line

The mathematical / phase-space framing is the project's contribution. It produces falsifiable claims (the H-battery), traceable through cyclic-group algebra, that other Antikythera literature does not (or rarely) make. Those claims are load-bearing.

Mechanical / kinematic reconstruction, by contrast, is well-served by existing literature (Freeth 2006, 2021; Wright; AMRP); duplicating it here under the rubric of "bronze fidelity" doesn't earn its complexity. If a future project needs a true mechanical model, it lives in a separate workspace (`docs/antikythera-physical/` or similar). Until that workspace exists, treat physical-reconstruction questions as **deferred to a different project**, not as additions here.

## Practical guidance for LLMs working in this tree

When you're tempted to add "let me model what the bronze actually does":

1. **Stop and ask: is this a parameter-variation question or a kinematic-simulation question?** Parameter variation (changing R, r, e, eccentricity, period relation) on an existing analytic model: in scope. Add named param sets, run the sweep, report. Kinematic simulation (replacing analytic geometry with mechanism-specific motion): out of scope; don't do it here.
2. **Check if the existing module already covers it.** Almost everything mechanical you might want has already been factored as either a parameter on an analytic model or as a graph-theoretic property in `gear_topology.py` / `gear_database.py`. Add to those rather than introducing a parallel "physical" path.
3. **If a contributor is asking for "true to bronze"** — read it as "true to the *parameters* the bronze implements," not "true to the *kinematics* of the bronze." Use named param sets (Almagest, Freeth 2012, Freeth 2021) to differentiate which mechanism's parameters you're testing.
4. **The architectural-mode thread (§11.6 of the notebook)** discusses crank-as-clutch / selective-lock / setting-mode-gears at the level of graph-theoretic placement on the gear DAG. Those are claims about *which gears are missing and where they attach*, not about what motions they would produce. Stay at the graph level.

## In-scope work this directory welcomes

- Adding hypothesis rows to the H-battery
- Adding named `MarsParams` / `VenusParams` / etc. for different reconstruction sources
- Sweeps over (precision, cost) Pareto fronts
- Cross-references to MUL.APIN / Almagest period relations
- Architectural-mode evaluators on `MESH_EDGES` (gear-DAG centrality, periphery rule)
- Manufacturing-tolerance Monte Carlo on existing cyclic-group ratios
- ΔT / ephemeris-kernel choice studies
- Document-hygiene updates that keep the notebook's framing aligned with the code

## Out-of-scope work that should not land here

- Mechanical motion simulation of the planetary plate
- Bronze-mechanism pin-and-slot reuse for non-D-H1 purposes
- Reconstruction of the missing planetary plate's physical layout (CAD models, fragment-alignment 3D)
- Wear / stiction / lubricant kinematics
- Anything that requires "what the gears physically do" beyond the cyclic-group ratio they implement

If unsure, the rule of thumb: **does this require continuous-time kinematics, or just a parameter swap on an existing analytic model?** Parameter swap → in scope. Kinematics → not here.
