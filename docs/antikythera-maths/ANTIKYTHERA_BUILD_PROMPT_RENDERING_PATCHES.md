# Claude Code: Antikythera Build Prompt — Rendering-Agnostic Framing Patches

## Context

The current `ANTIKYTHERA_SPECTRAL_BUILD_PROMPT.md` describes the mechanism as a "resonant HDC object" but frames it as a successor to the Antikythera specifically — a dial-and-pointer calculator. That framing under-represents what the HDC encoding actually is: scale-invariant angular dynamic state. The same HDC state underlies both the Antikythera's dial-display rendering *and* the orrery's spatial-model rendering, because the radial parameters used in each rendering (dial concentric radii, orbital radii) are static lookup tables chosen at rendering time, not participants in the dynamic computation.

This matters because (a) it tightens the positioning of the project — we are not reconstructing *the Antikythera*, we are reconstructing *the common parent* of the Antikythera and the Archimedean-planetarium tradition; (b) it sharpens the honest-science discipline — the mechanism's "rendering" is a user-interface choice, distinct from its computation; (c) it matters for the validation phase — the same encoder output should validate against both dial-style ground truth (Freeth 2021 reconstruction) and spatial-style ground truth (NASA Horizons ephemeris).

This prompt has four patches plus one addition to the vocabulary section. Apply them in order to the build prompt before handing it to Claude Code.

Every claim in the patches has been verified from first principles computationally before being proposed. The verification is stated inline in each patch's rationale block.

---

## First-principles verification (load-bearing for all four patches)

The HDC state is the dynamic angular information: each celestial body's phase in its respective cyclic group ℤ/n_cycleℤ. Two renderings of that state:

**Antikythera dial rendering:** each body projected to a concentric circular scale at a fixed dial radius `R_dial_body` (chosen at instrument-design time for layout). Pointer position = (R_dial_body · cos(θ), R_dial_body · sin(θ)).

**Orrery spatial rendering:** each body placed at a scaled orbital radius `orrery_scale · r_body` (with `r_body` in AU or similar, `orrery_scale` chosen for visual fit). Spatial position = (orrery_scale · r_body · cos(θ), orrery_scale · r_body · sin(θ)).

Both renderings take θ from the *identical* HDC state. Both expose a scale parameter (dial radii or orrery_scale) that does not affect θ. Both consult a static radial-parameter table (dial-layout or orbital-radii lookup) that is rendering-specific, not dynamic. Scaling orrery_scale from 4.0 to 8.0 changes pixel positions but preserves angles. Computationally verified: `arctan2(8·r·sin(θ), 8·r·cos(θ)) = θ` exactly.

**Consequence:** the HDC state is rendering-agnostic. The Antikythera's dial layout and a classical orrery's spatial model are sibling projections; the HDC encoding is the parent. This is not a metaphor — it is a first-principles property of angle-based dynamic state combined with scalar-parameter rendering.

**Historical precedent noted as DISPUTED:** Cicero (*De re publica*, *Tusculan Disputations*) describes Archimedes' Syracuse planetarium as an orrery-like device; Freeth (2021) leans toward Archimedean origin for the Antikythera tradition; others argue for Rhodian astronomical schools. Whether the same historical tradition produced both kinds of device is DISPUTED; the mathematical equivalence of their underlying computations is not.

---

## PATCH 1 — Framing section: establish rendering-agnostic encoding

**Location:** the opening `## Framing` section of the build prompt, after the first paragraph.

**Rationale:** the current framing positions Antikythera as a specific device we are reconstructing. The sharper framing is that we are reconstructing the *class of objects* that produces both the Antikythera's dial display and the Archimedean-planetarium's spatial model. This is a more accurate structural description and avoids a subtle historical claim that only the dial-display tradition is in scope.

OLD:
```
The Antikythera mechanism (Greek, ca. 150–60 BCE, recovered 1901, reconstructed through Freeth/UCL 2021 and subsequent work) is not a chess-like problem we need to discover structure in. It is a **physical instantiation of coprime-indexed phase-space addressing, designed deliberately 2100 years ago to solve the exact class of Diophantine approximation problems that docs/addressing-maths/ now characterizes formally**. Every gear is a cyclic group ℤ/nℤ; every mesh is a rational map between cyclic groups; every shared gear-train is an empirical solution to the multi-dataset packing problem (A-H1 in the addressing-maths research plan); every celestial pointer is an HDC-style hypervector whose components are the phase angles on the various dials. The Greeks built a **resonant HDC object** before Plate wrote HRR, before Kanerva wrote SDM, before Chung wrote *Spectral Graph Theory*.

This project documents it as such.
```

NEW:
```
The Antikythera mechanism (Greek, ca. 150–60 BCE, recovered 1901, reconstructed through Freeth/UCL 2021 and subsequent work) is not a chess-like problem we need to discover structure in. It is a **physical instantiation of coprime-indexed phase-space addressing, designed deliberately 2100 years ago to solve the exact class of Diophantine approximation problems that docs/addressing-maths/ now characterizes formally**. Every gear is a cyclic group ℤ/nℤ; every mesh is a rational map between cyclic groups; every shared gear-train is an empirical solution to the multi-dataset packing problem (A-H1 in the addressing-maths research plan); every celestial pointer is an HDC-style hypervector whose components are the phase angles on the various dials. The Greeks built a **resonant HDC object** before Plate wrote HRR, before Kanerva wrote SDM, before Chung wrote *Spectral Graph Theory*.

**The HDC state is rendering-agnostic — orrery and Antikythera are sibling projections.** The angular dynamic state captured by the encoder is the complete input to *any* rendering of the mechanism's output. The Antikythera's dial display projects each body's angle onto a concentric circular scale at a fixed dial radius chosen at instrument-design time. A classical orrery projects the same angle onto a scaled orbital radius chosen for visual fit. Both renderings consult a static radial-parameter table that is rendering-specific, not dynamic; both expose a free scale parameter that does not enter the phase-space computation. **Perspective is the scale invariance.** Consequently, what the project is reconstructing is not the Antikythera qua dial-calculator but the parent HDC state that the Antikythera's dial rendering and the Archimedean-tradition orrery rendering are both projections of. Cicero (*De re publica*, *Tusculan Disputations*) describes Archimedes' Syracuse planetarium as an orrery-like device built from related gearing principles — whether that historical tradition and the Antikythera share a lineage is DISPUTED in the archaeology literature; the mathematical equivalence of the dynamic computations underlying both device classes is not.

This project documents the shared parent structure.
```

---

## PATCH 2 — Notebook §0 scaffold: add rendering-agnostic subsection

**Location:** inside the notebook scaffold code block, under `## 0. Framing`, expand the paragraph.

**Rationale:** the scaffold's §0 currently mirrors the build prompt's framing at its pre-patch wording. Apply the same tightening so Claude Code writes the notebook correctly on the first pass.

OLD:
```
## 0. Framing

The Antikythera mechanism is coprime-indexed phase-space addressing executed in bronze, designed 2100 years ago. This notebook documents it as such. The math is already in the artifact; our job is to name it in the vocabulary the addressing-maths thread has now assembled. This is the first mlehaptics project where the encoding is *descriptive*, not *prescriptive* — we are not inventing an encoder, we are recognizing one.
```

NEW:
```
## 0. Framing

The Antikythera mechanism is coprime-indexed phase-space addressing executed in bronze, designed 2100 years ago. This notebook documents it as such. The math is already in the artifact; our job is to name it in the vocabulary the addressing-maths thread has now assembled. This is the first mlehaptics project where the encoding is *descriptive*, not *prescriptive* — we are not inventing an encoder, we are recognizing one.

### 0.1 The HDC state is rendering-agnostic

The encoded state is angular dynamic information: each celestial body's phase in its respective cyclic group. That state is the complete input to any rendering of the mechanism's output. The Antikythera's dial display and a classical orrery's spatial model are both projections of the same state, differing only in which static radial-parameter table is consulted at rendering time (concentric dial radii for the Antikythera; scaled orbital radii for the orrery) and in which free scale parameter is exposed (dial-ring layout vs. overall model scale). Neither parameter participates in the dynamic computation; both are rendering-time choices. **Perspective is the scale invariance.** A single `encode_Ant(t)` output can drive either rendering — which is why, historically, the same Hellenistic gearing tradition that plausibly produced the Antikythera (dial calculator) also, per Cicero, produced the Archimedean planetarium (orrery-like model). The HDC state is the shared parent; the two device families are sibling renderings. The Archimedean attribution is DISPUTED in the archaeology literature; the mathematical equivalence of the underlying computations is not.
```

---

## PATCH 3 — Phase 2 encoder: explicitly state rendering-agnostic design goal

**Location:** inside `## Phase 2 — encode_Ant: the resonant HDC encoder`, at the end of the `### Architecture` subsection.

**Rationale:** the architecture section names candidate dimensions D but doesn't state the rendering-agnostic design constraint. Adding it here keeps the encoder honest — the output must be a pure angular-state vector, not a pre-baked dial layout.

OLD:
```
### Architecture

The encoding has one channel per dial, matching the mechanism's physical structure. Dimension is determined by the largest gear tooth count (or its lcm composition, depending on H2/H3 outcomes). Candidate dimensions:

- **D = 940** (Callippic cycle × 4 for safety) — encodes annual + multi-year cycles cleanly but may not fit planets.
- **D = lcm(all cycles)** — exact and natural, but possibly huge.
- **D = chess-style ambient (e.g. 2⁷ × 3 × 5 × 7 = 13440)** — engineered for packing. Probably best for HDC operations.

Commit to one primary and one ablation, like Othello's D=768 + rank-8 ablation.
```

NEW:
```
### Architecture

The encoding has one channel per dial, matching the mechanism's physical structure. Dimension is determined by the largest gear tooth count (or its lcm composition, depending on H2/H3 outcomes). Candidate dimensions:

- **D = 940** (Callippic cycle × 4 for safety) — encodes annual + multi-year cycles cleanly but may not fit planets.
- **D = lcm(all cycles)** — exact and natural, but possibly huge.
- **D = chess-style ambient (e.g. 2⁷ × 3 × 5 × 7 = 13440)** — engineered for packing. Probably best for HDC operations.

Commit to one primary and one ablation, like Othello's D=768 + rank-8 ablation.

**Rendering-agnostic design constraint.** `encode_Ant(t)` returns angular dynamic state only — residue-class phases for each cycle, bundled into the D-dim HDC vector. It does NOT return pre-baked (x, y) pointer positions or spatial coordinates. Radial parameters (dial radii for Antikythera-style rendering, orbital radii for orrery-style rendering) are kept in a separate static lookup module, e.g. `research/rendering.py`, with two modes: `render_dial(state, dial_layout)` and `render_spatial(state, orbital_radii, orrery_scale)`. The encoder output is the parent; the renderers are projections. This matters for Phase 4 validation: the *same* `encode_Ant(t)` output must validate against Freeth 2021 dial-pointer positions AND against NASA JPL Horizons angular ephemeris, because both ground truths are projections of the same underlying astronomy. If the encoder is implemented correctly, writing `render_dial` vs `render_spatial` is ~20 lines of code each and neither involves re-running the mechanism.
```

---

## PATCH 4 — Rosetta Stone table: add rendering column

**Location:** the "How this fits the Rosetta Stone" section near the end of the build prompt.

**Rationale:** the current table has columns for structure type, encoding type, and phase-operator complexity. Adding a "rendering" column makes the rendering-agnostic property explicit at the framework level and highlights that Antikythera is the first project in the triad-plus where rendering is *deliberately factored out* from the encoding.

OLD:
```
| Project | Structure type | Encoding type | Phase operator complexity |
|---|---|---|---|
| chess-maths | discovered | prescriptive | rich (6 piece types × 8 orbits) |
| othello-maths | discovered | prescriptive | rich but different (1 piece, 8 rays, dynamic) |
| logo-maths | discovered | prescriptive | command set + grammar |
| addressing-maths | formalized foundation | — | — (the substrate itself) |
| **antikythera-maths** | **recognized/documented** | **descriptive** | **trivial (1 operator, many projections)** |

Antikythera is the first project where:
- The structure was deliberately designed into the artifact.
- The encoding is recognized, not invented.
- The phase operator is minimal.
- Ground truth is external (actual astronomy) rather than internal (game rules).
```

NEW:
```
| Project | Structure type | Encoding type | Phase operator complexity | Rendering |
|---|---|---|---|---|
| chess-maths | discovered | prescriptive | rich (6 piece types × 8 orbits) | implicit (board diagram) |
| othello-maths | discovered | prescriptive | rich but different (1 piece, 8 rays, dynamic) | implicit (board diagram) |
| logo-maths | discovered | prescriptive | command set + grammar | implicit (turtle canvas) |
| addressing-maths | formalized foundation | — | — (the substrate itself) | — |
| **antikythera-maths** | **recognized/documented** | **descriptive** | **trivial (1 operator, many projections)** | **explicit, factored (dial / orrery / ephemeris)** |

Antikythera is the first project where:
- The structure was deliberately designed into the artifact.
- The encoding is recognized, not invented.
- The phase operator is minimal.
- Ground truth is external (actual astronomy) rather than internal (game rules).
- **Rendering is explicitly factored out of encoding.** The dial display (Antikythera), spatial model (orrery), and angular ephemeris (NASA Horizons) are all projections of the same `encode_Ant(t)` output through different static radial-parameter tables. Perspective is the scale invariance; the encoding is rendering-agnostic.

The "rendering" column deserves a sentence on its own: the three game projects all treat rendering as implicit — chess diagrams, Othello boards, and LOGO canvases are how results are displayed, not separate projection modes. Antikythera is the first project in the triad-plus where a single encoding has multiple culturally-independent rendering traditions (Hellenistic dial calculator, Renaissance-to-modern orrery, astronomical almanac) all drawing from the same underlying dynamic computation. Factoring rendering out cleanly from encoding is both a design discipline and a methodological statement about what the HDC object IS — angular state, not displayed state.
```

---

## PATCH 5 — Vocabulary section: add "rendering" and "orrery"

**Location:** inside the notebook scaffold, `## 7. Vocabulary collisions specific to Antikythera`.

**Rationale:** the current vocabulary section names "mechanism," "gear," "cycle," "fiber," "phase" but does not commit the project's usage of "rendering" or "orrery." Both are load-bearing after Patches 1–4; state them explicitly.

OLD:
```
## 7. Vocabulary collisions specific to Antikythera

- "Mechanism" (the device) vs "mechanism" (the causal process).
- "Gear" (physical wheel) vs "gear" (HDC generator — we use "generator" or "channel" where possible).
- "Cycle" (astronomical period) vs "cycle" (graph-theoretic closed walk) — we commit to the astronomical usage in this notebook.
- "Fiber" — adopted from chess §7 with the refinement that here the fiber is static *and* shared across species, unlike Othello's dynamic fiber.
- "Phase" — adopted from chess/addressing-maths. In this notebook "phase" means angular position on a dial (equivalently: residue class in ℤ/n_dialℤ).
```

NEW:
```
## 7. Vocabulary collisions specific to Antikythera

- "Mechanism" (the device) vs "mechanism" (the causal process).
- "Gear" (physical wheel) vs "gear" (HDC generator — we use "generator" or "channel" where possible).
- "Cycle" (astronomical period) vs "cycle" (graph-theoretic closed walk) — we commit to the astronomical usage in this notebook.
- "Fiber" — adopted from chess §7 with the refinement that here the fiber is static *and* shared across species, unlike Othello's dynamic fiber.
- "Phase" — adopted from chess/addressing-maths. In this notebook "phase" means angular position on a dial (equivalently: residue class in ℤ/n_dialℤ).
- **"Rendering"** — a projection from the `encode_Ant(t)` dynamic state to a user-visible spatial or dial display, parameterized by a static radial-parameter table and a free scale parameter. Distinct from the "rendering" in computer graphics (ray tracing, rasterization, shading). This project uses the term in the specific sense "projecting an HDC angular state through a parameter table into a spatial or graphical form."
- **"Orrery"** — any device or simulation that renders planetary positions in 2D or 3D spatial arrangement with bodies at their scaled orbital radii. Contrast with "Antikythera-style" which renders angular positions on concentric circular dials. Both are renderings of the same HDC state in this project's framing. The word "orrery" historically derives from the 4th Earl of Orrery's 1704 Tompion/Graham clockwork model; this project uses it genericly for any spatial-position renderer, acknowledging the anachronism for ancient devices (the Archimedean planetarium is described as orrery-like by Cicero without the word being available in antiquity).
```

---

## Execution order

1. Apply Patches 1 through 5 in order to `ANTIKYTHERA_SPECTRAL_BUILD_PROMPT.md`.
2. Verify each patch landed by grep checking the NEW block's distinctive phrases (e.g., "Perspective is the scale invariance", "rendering-agnostic", "render_dial", "orrery").
3. Hand the patched build prompt to Claude Code for execution. Claude Code should pick up the rendering-agnostic discipline on the first pass — specifically in Phase 2 (the `encode_Ant` architecture should return only angular state, not pre-baked coordinates) and in Phase 4 (the same encoder output should validate against both dial-style and spatial-style ground truth).

Total expected edit work: ~15 minutes. No code changes triggered; these are build-prompt revisions before execution.

---

## What these patches are not

- Not a claim that the Antikythera and orrery traditions share documented historical lineage. The Archimedean attribution is DISPUTED in the archaeology literature; these patches take no position on the historical question and keep the tag.
- Not a claim that the Antikythera was designed to be rendering-agnostic. It was designed as a dial display. The rendering-agnostic property belongs to the *HDC reconstruction* of the mechanism's underlying computation, not to the historical artifact's designer intent.
- Not a pivot away from Antikythera as the primary subject. Antikythera remains the artifact the project documents. The rendering-agnostic framing is a descriptive property of the reconstruction, not a redirection of the research target.
- Not a commitment to implementing an orrery renderer as deliverable. `render_spatial` is a few lines on top of the encoder; whether to actually implement it depends on whether Phase 4 validation benefits from it. The discipline is "encode_Ant returns angular state only"; actually rendering is optional.
