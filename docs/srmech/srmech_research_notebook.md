# Stored-Relationship Mechanism (srmech) — Research Notebook

**Status:** Active. **Master architecture notebook for the spectral-research collection.** Cross-domain pollination layer above the per-domain notebooks (chess / ephemerides / antikythera / doom / othello / logo / MFO); home for domains without their own notebook (currently: graphics-domain Inkscape / Skia / GEGL).
**Version:** v0.1 (master-architecture framing; was v0 inception-only).
**Started:** 2026-05-09. Promoted to master architecture notebook same day per user direction.
**Location:** `docs/srmech/` — top-level home, separate from any single domain.

---

## Cross-references

- **[PR #294 spike](research-spikes/stored-relationship-mechanism-spike.md)** — research spike establishing the cross-domain framing across the eight spectral-research-collection notebooks. Path A / B / C / D options with four pre-v1.0 spike experiments.
- **ephemerides-spectral §22** — single-domain codification of the three-layer architecture (attestation / heavy-store / spectral scaffold).
- **Memory: `project_stored_relationship_mechanism_spike.md`** — spike pointer + recommended sequence (Spike 1 first; conditional on pass, run Spikes 2/3/4 in parallel).
- **Memory: `project_inkscape_skia_gegl_kernel_candidates.md`** — graphics-domain kernel candidates investigation (2026-05-09 subagent run).

---

## §0 What is srmech

The master architecture notebook for the eight-notebook spectral-research collection. Each per-domain notebook (chess / ephemerides / antikythera / doom / othello / logo / MFO) is the authoritative home for its domain; this notebook is the cross-pollination layer where shared abstractions are surfaced — Laplace-Beltrami across manifolds, HDC binding via cyclic-group representations, the AMSC attestation envelope, the `(Transform, λ_k, g)` decomposition. Domains that do not yet have their own research notebook are temporarily homed here (currently §3 hosts graphics-domain Inkscape / Skia / GEGL/GIMP knowledge until/unless that work spawns a dedicated notebook).

Three-layer architecture (the ephemerides-spectral §22 framing made cross-domain):

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

## §1.5 Cross-domain pollination map

The eight-notebook collection plus this srmech notebook. Each per-domain notebook is the authoritative home for its domain; srmech surfaces what generalises across them and hosts knowledge for domains that do not yet have their own home.

| Domain | Notebook | Manifold / structure | Spectral primitive shared with srmech | Status |
|---|---|---|---|---|
| chess-spectral | [`../chess-maths/chess_spectral_research_notebook.md`](../chess-maths/chess_spectral_research_notebook.md) | 8×8 board adjacency graph + cyclic group `Z_640` | Graph-Laplacian eigenbasis; 11-channel D₄ decomposition; HDC binding (BIP — sibling of `SkPhase9BIP`) | independent notebook; foundational for the phase-operator framework |
| chess-spectral 4D | (chess notebook §38+) | 4D `Z_8⁴` cyclic group | 4D extension of the 2D framework | sibling section in chess notebook |
| ephemerides-spectral | [`../antikythera-maths/ephemerides_spectral_research_notebook.md`](../antikythera-maths/ephemerides_spectral_research_notebook.md) | 52-body resonance graph + per-body modular `Z_{2^32}` | Graph-Laplacian + resonance-weighted gateway-graph Fiedler partition; per-body action-angle dynamical spectra | independent notebook; most mature; AMSC framework lives here (§18 / §22) |
| antikythera-spectral | [`../antikythera-maths/antikythera_spectral_research_notebook.md`](../antikythera-maths/antikythera_spectral_research_notebook.md) | gear DAG + cyclic-group ratios | `Z/nℤ` representations; gear-DAG Laplacian eigenbasis projected to spatial pointer motion; Diophantine-approximation framing | independent notebook; the bronze antikythera is the original stored-relationship mechanism |
| doom-spectral | [`../antikythera-maths/doom_spectral_research_notebook.md`](../antikythera-maths/doom_spectral_research_notebook.md) | sector graph (BSP) + sheaf structure | Sheaf-Laplacian raycasting; end-to-end existence proof of the chess-spectral §42 procedure | independent notebook; first cross-disciplinary methodological capstone |
| othello-spectral | [`../othello-maths/othello_spectral_research_notebook.md`](../othello-maths/othello_spectral_research_notebook.md) | 8×8 board adjacency graph (different ruleset than chess) | Sheaf-port reference encoder; spectral fingerprints | independent notebook; instantiates chess §10 framework on simpler domain |
| logo-spectral | [`../logo-maths/logo_research_notebook.md`](../logo-maths/logo_research_notebook.md) | turtle-graphics geometry; non-board cyclic-group framing | Split-object pattern (atoms × productions × geometry); L7b critical negative result on partial-trace fibers | independent notebook; non-board generalisation |
| MFO (Metric Field Ontology) | [`../antikythera-maths/mfo_spectral_research_notebook.md`](../antikythera-maths/mfo_spectral_research_notebook.md) | metric-field manifolds | Foundational ontology layer — sits *above* srmech as physics-meta-framing | sister notebook; **not a kernel candidate** per memory `project_mfo_sister_notebook.md` |
| **graphics-domain (Inkscape / Skia / GEGL/GIMP)** | **homed here, §3** | Euclidean grid + Neumann BC | DCT-II/III; Laplace-Beltrami on regular pixel lattice; same `(Transform, λ_k, g)` decomposition | **no independent notebook yet** — knowledge collected in §3 of this notebook |

### What generalises across domains

- **Laplace-Beltrami operator** — graph Laplacians (chess / ephemerides / antikythera / doom / othello / logo) and lattice Laplacians (graphics) are the same architectural slot, parameterised by manifold. Same `g(λ)` decomposition; manifold-specific eigenvalue formula. See §3.5.
- **HDC binding via cyclic-group representations** — chess BIP, ephemerides BIP, `SkPhase9BIP` (graphics) are siblings under one math. See `project_inkscape_skia_gegl_kernel_candidates.md` and ephemerides §22.
- **AMSC attestation envelope (L1)** — provenance / SHA-256 / descriptor-hash framework. Currently homed in ephemerides-spectral; the discipline is portable to any domain with literature- or archive-sourced data.
- **The `(Transform, λ_k, g)` decomposition** — how every closed-form spectral effect factors into three components: which transform, which manifold's eigenvalues, which weighting function. The catalogue layer this notebook is sketching expresses any such operator as a YAML/TOML config entry. See §3.0.

### What is domain-specific (does not generalise)

- Per-domain semantics of what the eigenbasis *means* (chess: piece-mobility; ephemerides: orbital-resonance; antikythera: gear-period; doom: visibility-sector; etc.).
- Per-domain encoding choices (modulus, quantisation policy, dimensionality).
- Per-domain decay / weight functions `g(λ)` (problem-specific).
- Per-domain heavy-store substrates (DE441 kernels, hand-coded gear ratios, board-state lookups, etc.).

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

> **Note on homing.** The graphics-domain content in this section (Inkscape / Skia / GEGL/GIMP / Pyodide PWA) lives here — in the master srmech notebook — because graphics-domain work does not yet have its own per-domain research notebook. Per the cross-domain pollination map (§1.5), domains without their own notebook are temporarily collected here. If the graphics-domain work spawns a dedicated `docs/<graphics-domain>/` notebook in the future, this section moves there and §1.5 updates accordingly.

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

Beyond the four existing primitives in §3.1, seven candidate effects are worth absorbing into the catalogue. All but two fit the universal `(Transform, λ_k, g)` decomposition cleanly:

| Effect | Spectral form g(λ) | Fits pure config? | Why include |
|---|---|---|---|
| Sharpen / Laplacian / band-pass | `g(λ) = α·λ` (high-pass) or `λ·exp(-σ²λ/2)` (band-pass) | **yes** | One-line addition to existing DCT path. Every photo editor has these. |
| Difference of Gaussians (DoG) / unsharp mask | `exp(-σ₁²λ/2) − exp(-σ₂²λ/2)`; variant `1 + α·(1 − exp(-σ²λ/2))` | **yes** | Heavily used in astrophotography; tests the catalogue's ability to compose two heat kernels |
| Wave / ripple (Helmholtz) | `cos(c·t·√λ)` | **yes** | Standing waves on the manifold; ripple-pool effects. `c, t` parameterise wave speed and elapsed time |
| Reaction-diffusion (Gray-Scott / Turing) | coupled PDE; diffusion part `exp(-D·t·λ)` per field; reaction part real-space pointwise nonlinear | **no — substrate primitive** | Pattern formation: animal coats, sand ripples, dendrites, mineral zoning, vegetation banding. Strongest candidate for the Perlin-replacement stretch goal |
| Cahn-Hilliard phase separation | linearised `g(λ) ≈ exp((λ − λ²)·t)` | **partially** — linearised form fits config; full nonlinear form is substrate-primitive | Blobby phase-separated patterns reminiscent of cosmic-web large-scale structure |
| Log-normal cosmological field | Gaussian random field with chosen `P(λ)`, then real-space `exp()` | **yes** (sequenced ops) | Galaxy-density filaments and voids: a single nonlinearity converts Gaussian noise into observed bias/clustering |
| Anisotropic diffusion (true tensor) | scalar λ replaced by eigenvalues of a per-pixel structure tensor; per-direction decay | **yes** | Vector-field-aware smoothing; directional blur along edges instead of across them. Linear with variable coefficients (distinct from state-dependent bilateral) |

The reaction-diffusion entry is load-bearing for the Perlin-replacement stretch goal (`task #104`): Perlin gives "natural-looking gradient noise," reaction-diffusion gives patterns that *literally are* the math behind real biological/geological pattern formation. See §3.7 for the full static-vs-dynamic discussion.

### 4.2 Config-driven special operations — the closed-form-vs-substrate-primitive split

The architectural rule that falls out of §3.0 + §3.1 + §4.1:

**Config-driven (catalogue entries fully express the operation):**

Any effect that closes under `Transform → g(λ) → InverseTransform` is pure config. The catalogue ships three component types — transforms, eigenvalue tables, decay functions — and effects compose by referencing combinations. Authoring a new such effect requires zero C++; it's a YAML/TOML entry. Examples: heat-kernel blur, Varadhan SDF, sharpen, DoG, Helmholtz waves, log-normal field, anisotropic diffusion.

**Substrate primitives (config sequences them but doesn't define them):**

State-dependent or coupled-PDE operations don't close under pure spectral form. The substrate library ships them as named primitives; the catalogue invokes them by name and supplies parameters. Examples: Perona-Malik bilateral (state-dependent diffusion), reaction-diffusion (coupled PDE with real-space nonlinear reaction), full nonlinear Cahn-Hilliard, future iterative or feedback-driven operators.

**The boundary is the math, not the implementation.** An operator is config-driven iff its spectral form `g(λ)` is a pure function of `λ` and a fixed parameter set — no dependence on the field's current real-space state, no coupling to a second field whose evolution feeds back. As soon as state-dependence or coupling appears, the operator becomes a substrate primitive.

**Pedagogically: bilateral is the load-bearing example.** Perona-Malik weights diffusion by `exp(-Δ²/2σ_r²)` where Δ is the local gradient — that's a function of the *current pixel state*, not just the eigenvalue index. No closed-form `g(λ)` captures it. So the substrate ships `srmech_bilateral_iter()` as a primitive; the catalogue entry for "edge-preserving blur" calls that primitive with a parameter dict, but the loop body itself is C++ in the substrate.

**Pragmatic implication.** The catalogue covers most of the user-facing operator menu (probably 80%+ in a typical photo editor), and the substrate library exposes the few exceptions as named hooks. The split is stable: bilateral and reaction-diffusion will always be substrate primitives because the underlying math doesn't reduce to a single `g(λ)`. Adding more operators of the same closed-form kind is config-only work.

This answers the earlier question ("are we going to be able to have config-driven special operations in some or all cases?") concretely: **most cases yes, a small set of mathematically-imperative outliers no.** The split is principled and has a sharp boundary.

---

## §5 Sources / inbound-doc absorption

The 2026-05-09 inbound research brief (`srmech-art-knowledge-subsume.md`, since deleted per the user's "exclude from tracking, delete when done" instruction) contributed:

- The universal `(Transform, λ_k, g)` decomposition framing now in §3.0
- The four-existing-primitives table in §3.1
- The Laplace-Beltrami cross-manifold table in §3.5
- The selection-shape host-side discipline in §3.6
- The Perlin-replacement static-vs-dynamic split in §3.7
- The seven additional candidate effects in §4.1
- The closed-form-vs-substrate-primitive answer in §4.2

The brief proposed a 3000–5000-word standalone notebook chapter and detailed file-by-file repo references; we absorbed the architectural insights into this notebook's existing structure rather than writing a separate chapter, per the user's "don't do exactly what it says if it's against what we've already been doing" framing. Where the brief and the existing srmech work overlap (Inkscape + Skia + GEGL framing, three-layer architecture, SkPhase9BIP-as-HDC), we deferred to what was already in §0–§3 of this notebook and the 2026-05-09 subagent investigation memorialised in `project_inkscape_skia_gegl_kernel_candidates.md`.

---

## §6 Cross-references

### Per-domain notebooks

The authoritative homes for each domain's research. Cross-pollination summary in §1.5; this section is the link map.

- [`../chess-maths/chess_spectral_research_notebook.md`](../chess-maths/chess_spectral_research_notebook.md) — chess-spectral (2D + 4D)
- [`../antikythera-maths/ephemerides_spectral_research_notebook.md`](../antikythera-maths/ephemerides_spectral_research_notebook.md) — ephemerides-spectral
- [`../antikythera-maths/antikythera_spectral_research_notebook.md`](../antikythera-maths/antikythera_spectral_research_notebook.md) — antikythera-spectral
- [`../antikythera-maths/doom_spectral_research_notebook.md`](../antikythera-maths/doom_spectral_research_notebook.md) — doom-spectral
- [`../othello-maths/othello_spectral_research_notebook.md`](../othello-maths/othello_spectral_research_notebook.md) — othello-spectral
- [`../logo-maths/logo_research_notebook.md`](../logo-maths/logo_research_notebook.md) — logo-spectral
- [`../antikythera-maths/mfo_spectral_research_notebook.md`](../antikythera-maths/mfo_spectral_research_notebook.md) — MFO (Metric Field Ontology, foundational layer)

### PRs / tasks / memories (project state)

- PR #294 — research spike (cross-domain framing across the eight-notebook collection)
- PR #296 — ephemerides §22 architecture-naming section
- PR #297 — v0.27.0 ROADMAP entry
- PR #299 — phase C part 1 body→kernel registry abstraction (the layer-2-to-layer-3 interface)
- PRs #303 / #306 / #308 / #309 / #311 / #312 / #313 / #314 / #315 / #316 / #317 / #319 — phase A AMSC backfill of all 12 v0.24.x catalogues
- Task `#168` — v0.28.x+ exploration of Inkscape + Skia + GEGL/GIMP graphics kernels
- Memory: `project_stored_relationship_mechanism_spike.md` — spike-test sequence + Path A/B/C/D recap
- Memory: `project_inkscape_skia_gegl_kernel_candidates.md` — graphics-domain investigation
- Memory: `project_mfo_sister_notebook.md` — MFO as foundational ontology layer
- Memory: `feedback_subagent_dispatch_pattern.md` — mint-first-then-subagent-rest workflow
- Memory: `feedback_run_wsl_smoke_before_amsc_push.md` — cross-platform float discipline

---

## §7 Future work

- **Spike 1** — Channel-shape abstraction Protocol. Highest-information experiment; gates Paths C/D.
- **Spikes 2 / 3 / 4** — conditional on Spike 1 outcome.
- **v0.27.0 banner close** — phase B (`binary_archive` adapter) + phase C part 2 (orbital-mechanics surface plumbing) + phase D (`use_local_kernel` extension).
- **Graphics-domain kernel absorption** — this branch's primary work; details land via the inbound doc.
- **Pedantic A+B+C integration testing** — gated on B + C-part-2 done.
