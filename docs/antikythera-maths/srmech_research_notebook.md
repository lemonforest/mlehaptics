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

## §3 The universal spectral pattern + graphics-domain kernel candidates

### §3.0 The universal `(Transform, λ_k, g)` decomposition

The central abstraction of the srmech config layer: every closed-form spectral effect decomposes as

```
1. Project to eigenbasis:      coeffs = Transform(input)
2. Pointwise weight by g(λ):   coeffs *= g(λ_k) for each mode k
3. Project back:               output = InverseTransform(coeffs)
4. Quantize / clamp as needed
```

Three component types fully express the effect: **(a) the transform** (DCT-II/III, FFT, spherical-harmonic projection, graph-Laplacian eigendecomposition), **(b) the eigenvalue formula λ_k** (depends on the manifold — see §3.5), **(c) the decay or weight function g(λ)** that shapes the spectral response. The config catalogue ships these three component types; effects compose by referencing combinations.

This is what makes the catalogue claim concrete: a non-expert can author a new effect in YAML/TOML by picking transform + eigenvalue source + decay function, without writing C++. Sketch:

```yaml
effect: heat_kernel_blur
pipeline:
  - op: srmech.transforms.dct2_2d
  - op: srmech.kernels.heat_decay
    args:
      eigenvalues: srmech.lattices.dirichlet_2d
      decay: "exp(-0.5 * sigma_x**2 * lambda_x - 0.5 * sigma_y**2 * lambda_y)"
  - op: srmech.transforms.dct3_2d
output: { quantize: clamp_uint8 }
```

The schema is not committed yet (ephemerides §22 + PR #294 framing leaves it open); this is the pre-schema sketch. The four-component-type framing — transform / eigenvalue / decay / quantize — is the load-bearing claim, not the YAML-key shape.

### §3.1 Existing primitives in the universal form

The four operators that already exist in the Inkscape and Skia forks, expressed in the `(Transform, λ_k, g)` decomposition:

| Primitive | Transform | λ_k | g(λ) | Notes |
|---|---|---|---|---|
| Heat-kernel blur | DCT-II/III | `2(1−cos πk/W) + 2(1−cos πl/H)` | `exp(-σ²λ/2)` | Anisotropic σ separates by axis |
| Perona-Malik bilateral | (none — real-space iteration) | — | — | **Substrate primitive, not config primitive.** Forward Euler stencil with state-dependent weights `exp(-Δ²/2σ_r²)`; doesn't close under pure spectral form |
| Varadhan SDF | DCT-II/III | (same lattice eigenvalues) | `exp(-σ²λ/2)`, then real-space `σ·√(-2·ln(u))` | Heat kernel + scalar postprocess |
| Power-spectrum noise | DCT-III only | (same lattice eigenvalues) | source: `iid Gaussian × √P(λ)`, then real-space minmax-normalize | P ∈ {1, 1/√λ, 1/λ, √λ} for white / pink / brown / blue |

Three of four fit pure config; bilateral is the imperative outlier (see §4.2 for the broader split).

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

### §3.5 Laplace-Beltrami generalisation across manifolds

The unifying insight that ties **chess-spectral**, **ephemerides-spectral**, and the graphics-domain kernels into a single framework: the Laplace-Beltrami operator `Δ_g f = (1/√|g|) ∂_i(√|g| g^{ij} ∂_j f)` generalises across manifolds. Same `g(λ)` decomposition; different transform, different eigenvalue formula:

| Manifold | Transform | λ_k | Project example |
|---|---|---|---|
| **Euclidean grid + Neumann BC** | DCT-II/III | `2(1−cos πk_x/W) + 2(1−cos πk_y/H)` | Inkscape, Skia, GEGL/GIMP — graphics-domain kernels |
| **Sphere S²** | spherical-harmonic projection | `l(l+1)` | future — full-sky imaging, planetary topography |
| **Flat torus T²** | 2D Fourier | `(2πm/L_x)² + (2πn/L_y)²` | future — periodic-tile kernels |
| **Triangle mesh** | cotangent Laplacian + sparse Lanczos | (eigendecomposition output) | future — 3D mesh-domain kernels |
| **General graph** | graph Laplacian `L = D − A`, eigendecomposition by SVD | (eigendecomposition output) | **ephemerides-spectral** — 52-body resonance graph; the gateway-graph Fiedler partition. **Antikythera-spectral** — gear-DAG. **Doom-spectral** — sector graph + sheaf-Laplacian raycasting |

The point: chess's 8×8 board Laplacian and ephemerides' resonance-graph Laplacian and Inkscape's pixel-lattice Laplacian are **the same architectural slot**, parameterised differently. The config catalogue's `eigenvalues:` field selects which manifold; the same `decay:` (heat kernel, sharpen, Helmholtz, etc.) works on any of them.

This is the deepest answer to the unification question: srmech is not "the project's seven projects glued together" — it's "the Laplace-Beltrami spectral pattern instantiated on whichever manifold the domain provides." The graph-Laplacian and the lattice-Laplacian are siblings, not strangers.

### §3.6 Selection-shape question (host-side masking)

When a user runs a spectral effect on a non-rectangular selection (lasso, magic wand) in Krita / GIMP / Photoshop / Inkscape, who handles the masking?

**Answer: host-side, every time.** The wiring layer rasterizes the bounding rectangle of the selection, runs srmech on a rectangle, and the host composites through its own selection mask. Reasons:

- **DCT / FFT need rectangular grids.** Padding to power-of-two-or-similar is unavoidable for the math.
- **Every host already has a selection compositor** with feathering, anti-aliasing, and partial transparency. Reimplementing that in srmech would duplicate stable, well-tested code.
- **Halo handling is already in wiring.** The wiring decides how much padding to add to the bounding rect to avoid edge-bleed; that lives at the host integration level, not in the spectral substrate.

The "srmech accepts a mask" alternative fights the math. Don't pursue it.

### §3.7 Perlin-replacement: static vs dynamic generators

Perlin gradient noise approximates a band-passed Gaussian random field with `P(k) ~ k^{-2}`. It's already "spectral noise with a particular spectrum" — just dressed up. There are two ways to generalise it:

**Static generators (cosmologically motivated):**

- **Power-law cosmological field.** `P(k) ~ k^n` with appropriate spectral index. White / pink / brown / blue noise are special cases of this; star-system gravitational large-scale structure (matter power spectrum) is another. Suitable for patterns whose source physics changes on Myr–Gyr scales — gravitational filaments, voids, large-scale cosmic structure. A static spectral generator captures these fine.
- **Log-normal cosmological field.** Power-spectrum noise + real-space `exp()` postprocess. A single nonlinearity converts Gaussian noise into the bias / clustering observed in galaxy density. Realistic filaments and voids fall out naturally.

**Dynamic generators (planetary-pattern-shaped):**

- **Reaction-diffusion (Gray-Scott / Turing).** Two coupled scalar fields with cross-coupling: `∂_t u = D_u ∇²u − uv² + F(1 − u)`, `∂_t v = D_v ∇²v + uv² − (F + k) v`. Each field's diffusion uses `exp(-D·t·λ)` spectrally; the reaction term is real-space pointwise nonlinear. Animal coats, sand ripples, dendrites, mineral zoning, vegetation banding — pattern formation that *literally is* the math behind the real patterns.
- **Cahn-Hilliard phase separation.** `∂_t u = -Δ²u + Δ f(u)` with a double-well potential. Linearised spectral form `g(λ) ≈ exp((λ − λ²) · t)`. Produces blobby phase-separated patterns reminiscent of cosmic-web large-scale structure.

**Why the planet-vs-star asymmetry matters.** Star-system patterns operate on Myr–Gyr scales; the system is essentially in equilibrium at any human-timescale snapshot. Static spectral generation captures this well. Planetary patterns (cloud cells, sand dunes, vegetation stripes, river networks) are **dynamic coupled-PDE outputs** at minute-to-decade scales; they don't sit at equilibrium. Reaction-diffusion and Cahn-Hilliard give patterns that *emerge from the same physics that produces the real ones*. That's what "HDC-similar to things in the universe" means: not "looks similar" but "is the same generative process."

For the v0.27.x stretch goal of replacing Perlin, the cosmological-style static path covers the easy case (cosmological-scale gravitational structure for star-system rendering); the dynamic path is the harder, more interesting one (planet-scale climate / biology / geology).

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
