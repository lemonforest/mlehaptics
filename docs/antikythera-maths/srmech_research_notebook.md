# Stored-Relationship Mechanism (srmech) — Research Notebook

**Status:** Active. Architecture-naming + experiment-scaffold notebook for the unified mechanism that absorbs domain-specific kernels.
**Version:** v0 (inception ship of the dedicated notebook; prior to this, srmech framing lived in PR #294 spike + ephemerides §22).
**Started:** 2026-05-10.

---

## Cross-references

- **[PR #294 spike](research-spikes/stored-relationship-mechanism-spike.md)** — research spike establishing the cross-domain framing across the eight spectral-research-collection notebooks. Path A / B / C / D options with four pre-v1.0 spike experiments.
- **ephemerides-spectral §22** — single-domain codification of the three-layer architecture (attestation / heavy-store / spectral scaffold).
- **Memory: `project_stored_relationship_mechanism_spike.md`** — spike pointer + recommended sequence (Spike 1 first; conditional on pass, run Spikes 2/3/4 in parallel).
- **Memory: `project_inkscape_skia_gegl_kernel_candidates.md`** — graphics-domain kernel candidates investigation (2026-05-09 subagent run).

---

## §0 What is srmech

Three-layer architecture (the notebook §22 framing made cross-domain):

1. **L1 — AMSC attestation envelope.** Provenance / SHA-256 / descriptor hash / per-mode attestation. Where each piece of data came from, when it was fetched, what the parse rules were.
2. **L2 — Heavy-store substrate.** The actual data: JPL ephemeris kernels, hand-coded catalogues, raster pixels, board states, gear ratios, fractal eigenvalue structures. Provides `state(...)` for every registered entity.
3. **L3 — Spectral scaffold.** Graph-Laplacian eigenbasis + channel decomposition + kinematics layer (state → ψ) + dynamics dispatcher + HDC / cyclic-group binding + bridge surfaces. Independent of which heavy-store provided which entity's state.

**Mechanism not computer.** Antikythera echo: the bronze antikythera *is* a stored-relationship mechanism (gear ratios encode period relations; pointers compute against them). srmech is the algebraic / spectral generalisation. Software pattern on existing CPUs/GPUs; ASIC/FPGA realisations conceivable for specific kernel shapes but future work.

---

## §1 Status as of inception

### Sister projects (kernels-or-future-kernels)

| Project | Status as kernel candidate |
|---|---|
| chess-spectral | foundational — provides the channel-decomposition + kinematics + dynamics shape ephemerides ports verbatim |
| chess-spectral-4d | sibling — extends 2D Z_8² to 4D Z_8⁴ |
| othello-spectral | sibling — instantiates chess §10's framework on a simpler domain at machine precision |
| doom-spectral | sibling — first end-to-end existence proof of cross-disciplinary methodology (§7.4) |
| antikythera-spectral | sibling — gear-DAG / cyclic-group / Diophantine-approximation framing |
| ephemerides-spectral | most mature — phase A AMSC backfill complete (12 v0.24.x catalogues), v0.27.0 banner partially shipped |
| MFO | foundational-ontology layer — *not* a kernel candidate; sits above srmech as physics-meta-framing |
| logo-HDC | sibling — split-object pattern (atoms × productions × geometry); L7b critical negative result on partial-trace fibers |
| **Inkscape** (graphics) | future kernel — orphan upstream; this branch absorbs |
| **Skia** (graphics) | future kernel — orphan upstream; this branch absorbs |
| **GEGL/GIMP** (graphics) | future kernel — recommended fresh venue per 2026-05-09 subagent investigation |

### Spike experiments (PR #294 §"Pre-v1.0 spike experiments") — not started

| Spike | Description | Priority |
|---|---|---|
| Spike 1 | Channel-shape abstraction Protocol unifying chess 11-channel D4 with ephemerides per-body action-angle | Highest-information; gates Paths C/D |
| Spike 2 | Cross-kernel regime classifier (add chess crisis-ply + doom sector-tension to v0.24.9 corpus) | Conditional on Spike 1 |
| Spike 3 | Single-bridge multi-kernel demo (`srmech encode --kernel chess/ephem/doom`) | Conditional on Spike 1 |
| Spike 4 | Spectral RDB on real data (Path D foundation) | Independent — could parallel |

---

## §2 Architectural commitments inherited from spike + ephemerides §22

The four paths from PR #294:

- **Path A — Status quo** (no unification). Each project ships independently; discipline shared via MPM doctrine.
- **Path B — Extract a shared utility layer** (modest factoring). AMSC framework + MPM-screening discipline + frozen-snapshot codegen pulled into a `spectral-substrate` package both projects depend on.
- **Path C — srmech (full unification of computation).** Kernel-driven core; each domain registers channel decomposition + kinematics + dynamics + state loader + constraints; core provides graph-Laplacian eigenbasis + HDC binding + bridge / CLI / codegen.
- **Path D — Spectral index over the heavy store.** Path C plus a unified spectral-index layer above each kernel's authoritative store; precomputed hypervector projections answer similarity / regime / configuration queries in O(D) cosine time.

The index pattern: **heavy stores stay; spectral scaffold is the index.** DE441 stays as source of truth; AMSC NDJSON stays as source of truth; SQL would stay if applicable. The spectral layer is structurally identical to pgvector / ElasticSearch / Druid / Neo4j applied to project-domain kernels.

---

## §3 Graphics-domain kernel candidates

This section's substantive content lands via the inbound doc the user is dropping. Pre-existing context (from the 2026-05-09 subagent investigation, memory `project_inkscape_skia_gegl_kernel_candidates.md`):

### Inkscape kernel — orphan upstream

`lemonforest/inkscape` `spectral-faithful` branch. Three SVG filter primitives:

- `feSpectralBilateral` — Perona-Malik state-dependent diffusion preserving step edges
- `feSpectralDistance` — Varadhan asymptotic distance field
- `feSpectralNoise` — power-spectrum noise (white / pink / brown / blue) synthesised in DCT eigenbasis

5-point lattice Laplacian; eigenbasis = 2D DCT-II; `e^{-tL}` heat-kernel application. Did not land upstream because primitives aren't in W3C SVG Filter Effects spec + 22–50× slowdown vs default at small radii. Vector roundtrip degrades because other SVG renderers don't ship the filters.

### Skia kernel — orphan upstream

`lemonforest/spectral-skai` `spectral-faithful` branch. More substantive than Inkscape:

- `SkLatticeDCT.{h,cpp}` — DCT-II/III + heat-kernel application
- `SkSpectralBlur`, `SkSpectralBilateral`, `SkSpectralDistanceField` — operator family
- `SkShaders::SpectralNoise` — White / Pink / Brown / Blue noise profiles
- **`SkPhase9BIP.h`** — 32×uint32 residue vectors, cyclic-group binding via coprime-roll. **This is HDC**, structurally identical to the BIP encoder in chess + ephemerides. Slots into the L3 HDC layer alongside chess D4 and ephemerides BIP D=32.
- `SkRadix2FFT` — Makhoul real-input DCT via FFT
- Parity tests at residual ≤ 1.4e-14

Did not land upstream because Google Gerrit's FIDO2 contribution gate, NOT technical reasons (per the repo's README).

### GEGL/GIMP venue — recommended fresh target

GEGL is the graph-based image-processing engine GIMP uses; its node graph is an architectural 1:1 fit with the L3 scaffold. New `gegl:spectral-*` operations consume the same DCT/heat-kernel substrate. GIMP auto-picks-up new GEGL ops; distribution via standalone repo + `~/.local/share/gegl-0.4/plug-ins/` (no GIMP recompile). Wider raster-editor reach than Inkscape because the spectral filters' visible effect manifests at raster-render time, not vector-edit time.

### Pyodide PWA "no-install" demo

Complement to GEGL/GIMP. Static-HTML PWA: drag-drop a PNG, pick filter + parameters, apply via the project's existing `ephemerides-spectral` wheel (the BIP encoder is `SkPhase9BIP`'s cousin in math), download the result. Maximum reach — anyone with a browser tries it.

---

## §4 Open research questions

### 4.1 Additional spectral graphic operations the architecture should learn to absorb

*Inbound doc to populate this section.*

Pre-known operator family from existing forks (DCT/heat-kernel/Perona-Malik/Varadhan/power-spectrum-noise/HDC binding). The question is what *additional* operations the user wants the architecture to absorb beyond these.

### 4.2 Config-driven special operations: which can / cannot be configured

*Inbound doc to populate this section.*

Pre-known: AMSC framework is config-driven at the data-source level (descriptor.toml + adapter dispatch). Open question: how far does config-driven extend to *operation* level (not just data-source level)? Some operations are stable + parameter-driven (e.g., heat-kernel σ); others may need code-level per-kernel implementation. The split is the design question.

---

## §5 To absorb (inbound doc)

*Placeholder. The user is dropping a doc into `docs/antikythera-maths/` once this scaffold is in place; that doc populates §3 / §4 and informs the v0.28.x+ kernel-loading design work.*

The user has noted: the session generating that doc may not realise that some items have already been delivered or discussed. Items already delivered or discussed will be skipped during absorption.

---

## §6 Cross-references

- PR #294 — research spike (cross-domain framing across the eight-notebook collection)
- PR #296 — ephemerides §22 architecture-naming section
- PR #297 — v0.27.0 ROADMAP entry
- PR #299 — phase C part 1 body→kernel registry abstraction (the layer-2-to-layer-3 interface)
- PRs #303 / #306 / #308 / #309 / #311 / #312 / #313 / #314 / #315 / #316 / #317 / #319 — phase A AMSC backfill of all 12 v0.24.x catalogues
- Task `#168` — v0.28.x+ exploration of Inkscape + Skia + GEGL/GIMP graphics kernels
- Memory: `feedback_subagent_dispatch_pattern.md` — the mint-first-then-subagent-rest workflow used for phase A
- Memory: `feedback_run_wsl_smoke_before_amsc_push.md` — cross-platform float discipline

---

## §7 Future work

- **Spike 1** — Channel-shape abstraction Protocol. Highest-information experiment; gates Paths C/D.
- **Spikes 2 / 3 / 4** — conditional on Spike 1 outcome.
- **v0.27.0 banner close** — phase B (`binary_archive` adapter) + phase C part 2 (orbital-mechanics surface plumbing) + phase D (`use_local_kernel` extension).
- **Graphics-domain kernel absorption** — this branch's primary work; details land via the inbound doc.
- **Pedantic A+B+C integration testing** — gated on B + C-part-2 done.
