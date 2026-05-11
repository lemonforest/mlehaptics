# Stored-Relationship Mechanism (srmech) — Research Notebook

**Status:** Active. **Master architecture notebook for the spectral-research collection.** Cross-domain pollination layer above the per-domain notebooks (chess / ephemerides / antikythera / doom / othello / logo / MFO); home for domains without their own notebook (currently: graphics-domain Inkscape / Skia / GEGL).
**Version:** v0.1 (master-architecture framing; was v0 inception-only).
**Started:** 2026-05-09. Promoted to master architecture notebook same day per user direction.
**Location:** `docs/srmech/` — top-level home, separate from any single domain.

---

## Cross-references

- **[PR #294 spike](../research-spikes/stored-relationship-mechanism-spike.md)** — research spike establishing the cross-domain framing across the eight spectral-research-collection notebooks. Path A / B / C / D options with four pre-v1.0 spike experiments.
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

## §1.5 Cross-domain pollination map + absorption rounds

The eight-notebook collection plus this srmech notebook. Each per-domain notebook is the authoritative home for its domain; srmech surfaces what generalises across them and hosts knowledge for domains that do not yet have their own home.

| Domain | Notebook | Manifold / structure | Spectral primitive shared with srmech | Status |
|---|---|---|---|---|
| chess-spectral | [`../chess-maths/chess_spectral_research_notebook.md`](../chess-maths/chess_spectral_research_notebook.md) | 8×8 board adjacency graph + cyclic group `Z_640` | Graph-Laplacian eigenbasis; 11-channel D₄ decomposition; HDC binding (BIP — sibling of `SkPhase9BIP`) | independent notebook; foundational for the phase-operator framework |
| chess-spectral 4D | (chess notebook §38+) | 4D `Z_8⁴` cyclic group | 4D extension of the 2D framework | sibling section in chess notebook |
| ephemerides-spectral | [`../antikythera-maths/ephemerides_spectral_research_notebook.md`](../antikythera-maths/ephemerides_spectral_research_notebook.md) | 52-body resonance graph + per-body modular `Z_{2^32}` | Graph-Laplacian + resonance-weighted gateway-graph Fiedler partition; per-body action-angle dynamical spectra | independent notebook; most mature; AMSC framework lives here (§18 / §22) |
| antikythera-spectral | [`../antikythera-maths/antikythera_spectral_research_notebook.md`](../antikythera-maths/antikythera_spectral_research_notebook.md) | gear DAG + cyclic-group ratios | `Z/nZ` representations; gear-DAG Laplacian eigenbasis projected to spatial pointer motion; Diophantine-approximation framing | independent notebook; the bronze antikythera is the original stored-relationship mechanism |
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

### Future-notebook candidates from cross-domain absorption rounds

Domains scoped via the dual-agent research pattern (memory: `feedback_dual_agent_research_pattern.md`) but not yet committed to dedicated notebooks. Detailed scoping reports in `notes/`; headline findings landed in §3.5, §4.2, §5.

| Domain | Status | Round date | Detailed scoping | Project-mission relevance |
|---|---|---|---|---|
| **Audio (DSP / music / speech / spatial / EMDR-bilateral)** | scoped; strongest project-mission *modality* fit | 2026-05-09 | [`notes/audio-scoping-2026-05-09.md`](notes/audio-scoping-2026-05-09.md) | **Direct** — bilateral audio extends EMDR pulser as peer modality alongside motor + LED |
| **Protein folding (NMA / GNM / contact-map / coevolution / AlphaFold-era)** | scoped; strongest cross-domain *validation* (NMA = ephemerides Fiedler-partition primitive identity) | 2026-05-09 | [`notes/protein-scoping-2026-05-09.md`](notes/protein-scoping-2026-05-09.md) | **None direct** — cross-domain stretch test for srmech universality |
| **Telecom (terrestrial cellular/Wi-Fi/cable/fibre/mesh + orbital satellite-constellation/TT&C)** | scoped; **strongest project-mission *infrastructure* fit** — UTLP IS a telecom protocol; RFIP IS Path D in radio; OFDM IS the (Transform, λ_k, g) decomposition (identity, not analogy) | 2026-05-09 | [`notes/telecom-scoping-2026-05-09.md`](notes/telecom-scoping-2026-05-09.md) | **Direct** — UTLP / RFIP / BLE+ESP-NOW are project-internal telecom protocols; Path D over UTLP beacon history is concrete v0.27.x demo candidate |
| **Power grid (terrestrial AC + DC + microgrid + orbital SBSP / lunar / Mars)** | scoped; **fifth-instantiation cross-domain validation** (Y-bus = graph-Laplacian; inter-area mode = NMA harmonic time evolution) | 2026-05-09 | [`notes/power-grid-scoping-2026-05-09.md`](notes/power-grid-scoping-2026-05-09.md) | **None direct** — cross-domain stretch test; **PMU/IEEE 1588 literature directly informs UTLP doctrine** (genuine cross-pollination win) |

For domains in this state: the per-domain notebook may be created when cross-pollination warrants dedicated scope. Until then, the scoping report in `notes/` is the home; master architectural learnings (§3.5 manifold instantiations, §4.2 calibration ratios, §5 absorption-round subsections) land in this notebook directly.

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
| **Euclidean grid + Neumann BC** | DCT-II/III | `2(1−cos πk_x/W) + 2(1−cos πk_y/H)` | Inkscape / Skia / GEGL/GIMP graphics-domain kernels; **audio spectrograms (STFT-domain)**; **protein contact maps** + **distance maps**; **telecom OFDM resource grid** (subcarrier × OFDM-symbol) + **modulation symbol constellation 2D**; **power-grid demand × time** |
| **Sphere S²** | spherical-harmonic projection | `l(l+1)` | **audio HRTF + ambisonics**; **globular protein surface (genus-0)**; **telecom antenna far-field radiation pattern** + **ground-station hemispheric visibility**; **power-grid solar irradiance + SBSP antenna beam-pattern**; future planetary topography |
| **Flat torus T²** | 2D Fourier | `(2πm/L_x)² + (2πn/L_y)²` | **protein backbone Ramachandran (φ, ψ)**; **audio periodic-loop / circular-buffer**; **telecom OFDM cyclic-prefix subcarrier basis** (DFT *is* the eigenbasis of the periodic-CP boundary); **power-grid multi-bus phasor on T^N**; future periodic-tile graphics kernels |
| **Triangle mesh** | cotangent Laplacian + sparse Lanczos | (eigendecomposition output) | **protein solvent-accessible-surface mesh**; **3D acoustic-cavity meshes**; **telecom reflector-antenna mesh + indoor 3D propagation environment**; future — 3D mesh-domain graphics kernels |
| **General graph** | graph Laplacian `L = D − A`, eigendecomposition by SVD | (eigendecomposition output) | **ephemerides-spectral** — 52-body resonance graph (gateway-graph Fiedler partition). **Antikythera-spectral** — gear-DAG. **Doom-spectral** — sector graph + sheaf-Laplacian raycasting. **Chess-spectral** — 8×8 board adjacency. **Protein folding** — residue-interaction network (GNM / ANM / NMA — *literally the same primitive* as ephemerides Fiedler partition). **Audio** — microphone-array beamforming; Tonnetz key-relationship graph. **Telecom terrestrial** — cell-tower handover graph; mesh-network routing (BLE-Mesh / ESP-NOW / Thread); BGP AS topology; submarine fibre cable graph. **Telecom orbital** — satellite ISL constellation (Starlink / Iridium NEXT / OneWeb / Telesat) — *direct sibling of ephemerides 52-body resonance graph*. **Power grid** — Y-bus admittance matrix on transmission graph (5th instantiation; identical primitive). |

The point: chess's 8×8 board Laplacian and ephemerides' resonance-graph Laplacian and Inkscape's pixel-lattice Laplacian are **the same architectural slot**, parameterised differently. The config catalogue's `eigenvalues:` field selects which manifold; the same `decay:` (heat kernel, sharpen, Helmholtz, etc.) works on any of them.

This is the deepest answer to the unification question: srmech is not "the project's seven projects glued together" — it's "the Laplace-Beltrami spectral pattern instantiated on whichever manifold the domain provides." The graph-Laplacian and the lattice-Laplacian are siblings, not strangers.

The **protein-folding absorption round** (see §5.3 + [`notes/protein-scoping-2026-05-09.md`](notes/protein-scoping-2026-05-09.md)) supplied the strongest evidence for this claim to date: GNM / ANM / NMA on the residue-interaction network is graph-Laplacian eigendecomposition — *literally the same primitive* ephemerides uses on the 52-body resonance graph (§13 gateway-graph Fiedler partition; Matthews φ = +0.336, Spearman ρ = +0.743 vs empirical Δv). Same math, different graph. Not analogy — identity. The **audio absorption round** (§5.2 + [`notes/audio-scoping-2026-05-09.md`](notes/audio-scoping-2026-05-09.md)) instantiates *every row* of the table above (spectrogram → Euclidean grid; HRTF / ambisonics → sphere; periodic loops → torus; acoustic-cavity meshes → triangle mesh; mic-array + Tonnetz → general graph), the cleanest cross-pollination test the framing has faced.

### §3.5.1 Algebraic-hyperdimensional layer — eigenbasis ambient geometry

The six §3.5 rows describe **manifolds the Laplace-Beltrami operator acts on** — substrate geometries for the eigenbasis itself. A separate ambient-geometry layer lives **above** the substrate manifold, on the eigenbasis itself: orthonormal eigenvectors are points in an algebraic-hyperdimensional space of dimension `n = |V|` (or grid-size, or mesh-vertex-count, etc.), and that space has its own geometric structure independent of which substrate manifold the rows above name.

Per the **`hyper = 3D-spatial-interface` distinction** (`memory/user_stance_hyper_as_3d_spatial_interface.md`): this layer is **algebraic-hyperdimensional**, not 3D-spatial-interface — distinct from the spherical-compression operator applied to 3D-bound matter/information at event horizons, gravitational figures, and HDC similarity metrics. Different ontological domain, different vocabulary.

Two project-relevant algebraic-hyperdimensional structures live at this layer:

**(a) Eigenbasis cross-polytope on S^(n−1).** For any graph Laplacian L acting on n vertices, the orthonormal eigenvectors `{v_1, …, v_n}` together with their negatives `{−v_1, …, −v_n}` form **2n vertices of a cross-polytope inscribed in the unit sphere S^(n−1)** (verified numerically; off-diagonal residual 1.1×10⁻¹⁵ at n=6 via `numpy.linalg.eigh`). Vocabulary is informationally new but no current project code exploits the sign-closure structure — `eigh` / `eigvalsh` already preserve orthonormality. Named here for future use; deferred until a use case (e.g., sign-symmetry-aware similarity, antipodal averaging, dyadic group action on eigenspaces) needs it.

**(b) Eigenphase torus T^n — phase-preserving quantum-walk lift.** Quantum walk `U(t) = exp(−i L t)` on `C^n` (complex n-space) evolves eigencomponents as phases `exp(−i λ_k t)` on S¹; the time-evolved state in eigenbasis lives on **T^n indexed by eigenphases**. Classical heat flow `exp(−L t)` is the magnitude-only projection of this richer dynamics (the "magnitude shadow"). Two project loci already ship phase-preserving quantum walks without naming the T^n ambient explicitly:

| Locus | Substrate | Walk type | Ambient |
|---|---|---|---|
| `ephemerides_spectral/_research/ephemeris_reference_instrument.py:156-170` | 52-body resonance graph | `U = expm(-1j * L_dyn * step); psi = U @ exp(1j * φ)` | T^52 |
| `chess_spectral/qm_2d_dynamics.py` + `qm_4d_dynamics.py` `evolve_under_h0` | board-spectral C^640 / C^45056 | `U(t) = exp(−i H_0 t)` projective Hilbert ray | T^640 / T^45056 (via inscribed S^(2N−1) ⊂ C^N) |

Every §3.5 row admits this lift: replace the classical evolution operator `exp(−Δ_g t)` with the unitary quantum-walk operator `exp(−i Δ_g t)`. The substrate manifold is unchanged; the dynamics gain phase information that classical evolution discards. **The project has been quantum-walking on T^n in two loci for over a year without naming the ambient.** Naming surfaces what's already shipped, without new code.

Connects to continuous-time quantum walk (CTQW) literature: Childs (2011) `https://www.cs.umd.edu/~amchilds/teaching/w11/l13.pdf`; Farhi & Gutmann (1998); arxiv:2509.26243 (already cited in `chess_spectral_research_notebook.md` for spectral coverage). Future ships that need phase-coherent evolution on any §3.5 row can read this section as the project's canonical name for the operator.

**MPM provenance:** structural-layer claims investigated 2026-05-11 in `docs/antikythera-maths/research-mfo/graph_laplacian_hyperring_investigation_findings.md`. Layer (a) cross-polytope STANDS as math; project-marginal at present. Layer (b) eigenphase torus STANDS as both math and load-bearing project structure. A third candidate (Krasner hyperring on degenerate eigenspaces) was investigated and FALSIFIED — MFO Phase B's `22A + 18B + 40E` decomposition under D₃ is standard Maschke + Schur direct-sum representation theory, not Krasner's set-valued algebra. Vocabulary discipline: this section names the algebraic-hyperdimensional ambient layer; the 3D-spatial-interface spherical-compression operator (`memory/user_stance_hyper_as_3d_spatial_interface.md`) is a separate scope and the two should not be conflated.

The cross-polytope eigenbasis and eigenphase torus are **math-instruments** that describe spectral structure (per the project's instrument-vs-phenomenon discipline; see MFO `§VII.1.1`'s two-level ontology and `memory/user_stance_string_theory_instrument_first.md`). They are not field-domain excitations, not matter-wave-domain excitations — they sit outside the physical-domain dichotomy as mathematical descriptions of physical-system structure. Adopting them as project canon for naming spectral-decomposition ambient geometry does not require commitment about the underlying physics of the systems they describe.

### §3.5.2 Empirical anchors of cross-manifold rows — MFO MPM orchestration findings (2026-05-11)

The §3.5 cross-manifold rows are not just architecturally compatible — they have been empirically anchored across the project's domain catalogues by the MFO MPM orchestration arc on `feat/mfo-mpm-srmech-review` (15-commit sequence `251fcc6` → `bcd24f5`). Full provenance in [`docs/antikythera-maths/research-mfo/`](../antikythera-maths/research-mfo/). All findings under math-doesn't-lie MPM discipline: closed-form / standard-library deterministic computation; no SGD; no fit-parameters except where explicitly named; ground-proof against canonical references.

**Row 1 (general graph) — 4-tier d_S/2 classification.** Bottom-up cross-spectrum survey (no external target fitting) sorted 15 srmech-collection domains by graph-Laplacian eigenvalue-density slope into four tiers:

| Tier | Domains | d_S/2 |
|---|---|---|
| Chain/tree | P₂ • ephemerides 52-body • antikythera gear-DAG • Hawaii σ=500km | 0.49–0.55 |
| SG fractal | L=5 SG levels 3, 4, 5 | 1.00–1.09 |
| 2-3D lattice | Chess king-move • P₄ tetrahedral | 1.44–1.55 |
| Near-complete | Othello line-of-sight | 3.25 |

Within-tier agreement at the chain endpoint is within 10% across **four fundamentally different construction methods** (integer mesh, integer tree, integer DAG, Gaussian proximity kernel). Cross-domain validation of the graph-Laplacian primitive producing a sortable structural fingerprint independent of construction method. Provenance: [`mpm_survey_findings.md`](../antikythera-maths/results-mfo/mpm_survey_findings.md) + [`mpm_survey_v2_findings.md`](../antikythera-maths/results-mfo/mpm_survey_v2_findings.md).

**Row 2 (sphere S²) — 3-fingerprint cross-body anchor.** Sphere-S² parallel survey on the ephemerides `SolGeodeticCatalog` + `MagneticMultipoleCatalog` (gravity: 11 bodies; magnetic: 7 bodies) found three reproducible cross-body fingerprints: Kaula-scaling slope α in `power(l) ~ l^{−α}`, l-vs-(l+1) power partition, and dipole-vs-higher-multipole ratio. Magnetic-archetype clusters (axisymmetric Saturn/Mercury; aligned Earth/Jupiter/Ganymede; extreme-tilt Uranus/Neptune) reproduce in scalar-SH structure. Provenance: [`mpm_sh_survey_findings.md`](../antikythera-maths/results-mfo/mpm_sh_survey_findings.md).

**Row 3 (flat torus T²) — 3-fingerprint magnetospheric anchor.** T² L-shell magnetospheric survey on the 7-body magnetic-catalogue intersection (Mercury / Ganymede / Earth / Saturn / Neptune / Uranus / Jupiter). Three reproducible fingerprints: Chapman-Ferraro derived `R_mp/R_p = (4 B²/(μ₀ P_sw))^(1/6)` reproducing published spacecraft values to factor-of-2 (7/7 bodies; Jupiter at 0.54× is the worst case due to Io-plasma-torus mass-loading outside the vacuum-dipole assumption); dayside-vs-nightside compression ratio (small-tier 1.6–3.1×, moderate 21×, giant 43–124×, ice-giant short-tail 0.42×); inner-boundary spherical-departure proxy (ice giants ~1.0 vs ≤0.2 for all other bodies, five orders of magnitude separation). Ice-giant 2-body cluster (Uranus/Neptune) agrees to 1% on R_mp/R_p and compression, 11% on distortion proxy — tightest within-cluster anchor in the survey. **Three §3.5 T² instantiations now empirically populated**: audio periodic loops + protein Ramachandran (φ, ψ) + planetary magnetospheric L-shell. Provenance: [`mpm_t2_lshell_survey_findings.md`](../antikythera-maths/results-mfo/mpm_t2_lshell_survey_findings.md).

**Hawaii bend triple-channel decomposition** (bounded-local graph-Laplacian instantiation of row 1). The Hawaiian-Emperor chain bend (Pacific-plate direction change at 47.5 Myr; ephemerides-spectral v0.24.5 catalogue) decomposes into three complementary channels:

1. **Subtle Fiedler-monotonicity reversal at the bend marker** (yuryaku → daikakuji has `dF = +5.5×10⁻⁴`, factor-1000 deviation from neighbouring ~10⁻² to 10⁻¹ steps, localised right at the bend). The user-intuited "stick-slip from slightly curving" maps specifically to this channel.
2. **Strong age-vs-arc-length non-spectral residual** (Meiji at −1265 km — the catalogue's documented non-spectral diagnostic).
3. **NOT** a single eigenvalue-gap signature (largest gap is dominated by post-bend isolated pair Midway / Pearl-and-Hermes).

Geometric direction-change → spectral signature is a generalisable pattern; the magnetospheric analog appears in ice-giant 3-way axis mismatch (dipole vs rotation vs orbital) producing patchy / partial / time-variable auroral signatures. Different physical systems, same math-identity family. Provenance: [`mpm_survey_v2_hawaii_bend.ndjson`](../antikythera-maths/results-mfo/mpm_survey_v2_hawaii_bend.ndjson).

**SG self-similarity quantitative spectral signature.** L=5 SG levels 3, 4, 5 are the **only multi-domain match** under 5%-tolerance gap-fingerprint clustering across the 15 cataloged domains. Levels 4 and 5 fingerprints agree to 4 decimal places. Empirical support for fractal-self-similarity claims (MFO notebook §IV.2 decimation-tree). Provenance: [`mpm_survey_cross_spectrum.ndjson`](../antikythera-maths/results-mfo/mpm_survey_cross_spectrum.ndjson).

### §3.5.3 Cross-cutting math-identity motifs (project-wide)

The MFO orchestration surfaced math-identity motifs that span multiple §3.5 rows and multiple project domains. These are the abstract claims srmech holds for the spectral collection:

**(A) Rotational compression breaks pure sphericity.** Same mechanism family identified across three independent project loci:

- **Saturn J₂ gravitational figure** — most-oblate-Solar-System body co-occurring with most-axisymmetric magnetic dipole (Cao 2020 `<0.007°` tilt). Same rotational-alignment mechanism governs both gravitational and magnetic axisymmetry. Matter-wave domain (gravitational figure of mass distribution).
- **Kerr event-horizon oblateness** — rotation parameter `a = J/(Mc)` deforms static Schwarzschild S² into oblate spheroid. Matter-wave domain (mass-information compressed to inscribed 2-boundary per MFO §VII.4.1 spherical-compression operator).
- **Ice-giant magnetospheric inner-boundary distortion** — Uranus/Neptune inner-boundary distortion proxy `tilt/90 + offset/R ~ 1.0` vs `≤0.2` for all other surveyed bodies (T² survey). Matter-bound planet × field-domain magnetic-structure coupling (per MFO §VII.1.1 two-level ontology).

Rotation-breaks-roundness is a substrate-level mechanism that manifests at both the matter-wave layer and the matter-bound × field-domain coupling layer. The "spherical compression" operator (MFO §VII.4.1) accepts a rotational-deformation parameter that converts static S² boundaries into oblate spheroids while preserving the closed-2-manifold topology.

**(B) HDC architecture is plural.** Project HDC is not a single substrate — surfaced by spherical-compression concertmaster investigation (commit `8fc973c`):

| Flavour | Substrate | Bind operation | Similarity metric | Inscribed-sphere geometry? |
|---|---|---|---|---|
| **MFO Phase C bipolar BIP** | `{−1,+1}^D` | element-wise multiplication | `⟨a,b⟩/D` | YES — vertices on inscribed S^(D−1) at radius √D |
| **Ephemerides BIP / SkPhase9BIP** | `(Z_{2^K})^D = T^D` (flat torus) | modular phase addition mod `2^K` | post-superposition Born-rule norm | PARTIAL — appears at lift-and-normalize step only |
| **Chess-spectral production encoder** | `R^640` float | spectral channel projection + value lookup | cosine in R^640 | NO — substrate is R^640 directly |

When discussing HDC in formal contexts, distinguish which flavour is operative; cross-flavour properties do not automatically inherit. Provenance: [`spherical_compression_investigation_findings.md`](../antikythera-maths/research-mfo/spherical_compression_investigation_findings.md).

**(C) Closed-form group-theoretic eigenvalue prediction at machine precision.** A graph or correlation matrix with a known symmetry group `G` admits a closed-form decomposition of its eigenspace via rep theory of `G`. The decomposition predicts integer multiplicities AND/OR specific eigenvalue formulas; empirical eigendecomposition matches these predictions to machine precision (15-digit float). The motif's strength comes from cross-domain instantiation under different symmetry groups, all matching exactly. Two project instances stand:

1. **MFO Phase B — L=5 SG `λ=6` eigenspace under D₃** (canonical first instance). The `λ=6` eigenspace of the L=5 Sierpinski-Gasket decimation Laplacian at level 5 has dimension `120`, decomposing cleanly under D₃ as `22A + 18B + 40E` (integer-exact, machine precision). `min(22A, 18B, 40E) = 18` is the number of distinct `(1A + 1B + 1E)` "generation blocks" the eigenspace can host. The Standard Model has 3 generations × 6 charged-fermion components per generation = 18. **Match exact, structural prediction from rep theory** (not fit-parameter). Selection mechanism among the 18 candidate blocks remains the central open computation per MFO §XIII.1. Provenance: [`mpm_phase_b_findings.md`](../antikythera-maths/results-mfo/mpm_phase_b_findings.md) + [`mpm_phase_f_findings.md`](../antikythera-maths/results-mfo/mpm_phase_f_findings.md).

2. **Finance — block-correlation matrix under `S_k × S_m`** (Fiedler-vs-HRP-vs-GICS spike, 2026-05-11). For a synthetic `k`-sector × `m`-stocks-per-sector block-correlation matrix `C` with permutation symmetry `S_k × S_m` (intra-block correlation `ρ_in`, inter-block correlation `ρ_out`), the eigenvalue spectrum is closed-form: market mode (1 mode) at `1 + (m−1)·ρ_in + (k−1)·m·ρ_out`; sector contrast (k−1 modes) at `1 + (m−1)·ρ_in − m·ρ_out`; idiosyncratic (k(m−1) modes) at `1 − ρ_in`. Empirical match to 15-digit float precision against `numpy.linalg.eigh` on the noiseless 50×50 block-correlation matrix (k=10 sectors, m=5 stocks/sector). **Match exact, structural prediction from rep theory of permutation symmetries on block matrices** (not fit-parameter). The same spike test established the project's Fiedler partition decisively outperforms López-de-Prado 2016 HRP on this benchmark (Fiedler 20/20 wins in moderate-to-weak SNR scenarios; mechanism: HRP single-linkage chaining failure under weak block signal; Fiedler's spectral gap is an integrated whole-graph property). Synthetic-only caveat: real-equity benchmarks have noise, non-stationarity, and broken-permutation symmetry; the machine-precision match is the math identity, not a universality claim about real markets. Cardinality-sensitivity footnote: HRP single-linkage gracefully handles over-partitioning (k_requested > k_true) where Fiedler k-means re-splits correct clusters; this is a ship-mode design consideration, not a math-identity failure. Provenance: [`fiedler-vs-hrp-vs-gics-spike-2026-05-11.md`](notes/fiedler-vs-hrp-vs-gics-spike-2026-05-11.md) + [`fiedler-vs-hrp-vs-gics-spike-per-metric-2026-05-11.ndjson`](notes/fiedler-vs-hrp-vs-gics-spike-per-metric-2026-05-11.ndjson) + reproducible script [`fiedler-vs-hrp-vs-gics-spike-script.py`](notes/fiedler-vs-hrp-vs-gics-spike-script.py) (30s runtime, seed `20260511`).

**Motif strength**: the two instances live in fundamentally different domains (Sierpinski-Gasket fractal QFT vs equity correlation network) under different symmetry groups (D₃ vs `S_k × S_m`) but share the same math identity. Future instances should adopt the same provenance pattern: named group, closed-form decomposition, machine-precision empirical match, honest caveats. Candidate future instances (untested): chess move-graph eigenvalues under D₄ / B₄ (per Rinaldi-Unciuleanu & Chiru 2026 product-graph structure); ephemerides resonance-graph eigenvalues under Solar-System orbital-resonance symmetries; protein NMA eigenvalues under chain or topological symmetries.

**(D) Math-identity orthogonality**: graph-Laplacian eigendecomposition (row 1) admits the phase-preserving quantum-walk lift via `e^(−iLt)` to T^n eigenphase ambient (§3.5.1 layer b) on any §3.5 row. Standard CTQW. Two project loci already ship this lift unnamed: `ephemerides_spectral/_research/ephemeris_reference_instrument.py:156-170` (T^52) and `chess_spectral/qm_2d_dynamics.py` + `qm_4d_dynamics.py` (T^640 / T^45056 via inscribed S^(2N−1) ⊂ C^N). Provenance: [`graph_laplacian_hyperring_investigation_findings.md`](../antikythera-maths/research-mfo/graph_laplacian_hyperring_investigation_findings.md).

**(E) Ontological commitment delegation.** srmech is the math-identity layer; foundational ontology (metric-field substrate, particle-matter-wave vs field-domain excitation classes, spherical-compression operator scope, holographic-principle commitment) is held in **MFO §VII.1.1 + §VII.4.1 + §VIII.1**. Cross-reference to MFO is mandatory when invoking the two-level ontology; srmech does not duplicate it.

**(F) Product-graph universality.** For graphs `G_1, ..., G_d`, both the **Cartesian product** (graph-theory `\square` operator) and the **strong product** (graph-theory `\boxtimes` operator) give closed-form access to composed-system spectra: adjacency and Laplacian eigenvalues of the product are sums of eigenvalues of the factors (Imrich-Klavžar *Product Graphs*). This is a math-identity that applies anywhere the project has a composed-graph structure:

- **Chess-spectral 4D** (formalized in [hoodoos/rinaldi-unciuleanu-chiru-2026.xml](hoodoos/rinaldi-unciuleanu-chiru-2026.xml) — Rinaldi-Unciuleanu & Chiru 2026, DOI `10.3390/appliedmath6030048`): rook graph is the Hamming graph `H(4,8)`, equivalently the Cartesian product of four `K_8` factors (uniform mobility 28; diameter 4); king graph is the strong product of four `P_8` factors (interior degree 80; Chebyshev-metric diameter 7); bishop graph is parity-stratified by `π(x,y,z,w) = (x+y+z+w) mod 2`; knight is `(2,1)`-leaper with interior max degree 48.
- **Coding theory**: Hamming graphs `H(n,q)` underlie Hamming-distance codes — direct sibling of the project's HDC bipolar flavour (`{−1,+1}^D` per §3.5.3(B)).
- **Telecom MIMO**: Cartesian-product channel matrices (Tx × Rx antenna arrays) admit Kronecker / Cartesian-product eigendecomposition.
- **Power grid**: Cartesian-product transmission/distribution coupling on hierarchical bus graphs.
- **Future extension candidate**: any project domain with a composed-system structure benefits from invoking this identity rather than computing the full eigendecomposition directly. **Provenance for chess-4D**: Rinaldi-Unciuleanu & Chiru 2026 explicitly names "spectral analysis of move graphs" as future work; chess-spectral's [qm_2d](../chess-maths/chess-spectral/python/chess_spectral/qm_2d.py) + [qm_4d](../chess-maths/chess-spectral/python/chess_spectral/qm_4d.py) modules are the implemented spectral analysis of those move graphs.

### §3.5.4 Fiber-bundle structure — rich features over a discrete base

A distinct manifold structure not captured by the six §3.5 rows: **a fiber bundle over a discrete base manifold**. The base is some n-dim space (2D grid, 4D hypercube lattice, residue chain, resource grid, bus graph); the fiber is a k-dim vector space at each base point holding semantic content (piece types, feature channels, modulation symbols, measurement types); the total space is the section bundle of rank `k` over the base. Math identity: `total_dim = |base| × k`.

| Instance | Base manifold | `|base|` | Fiber rank `k` | Total dim |
|---|---|---|---|---|
| **chess-spectral 2D** | 8×8 grid | 64 | 10 (piece types + game-state) | 640 |
| **chess-spectral 4D** | `{1,...,8}^4` hypercube | 4096 | 11 (piece types + game-state) | 45056 |
| **Protein folding** | residue chain | `N_residues` | per-residue feature channels | `N × k` |
| **Telecom OFDM** | (subcarrier × OFDM-symbol) grid | `N_c × N_s` | modulation symbol | `N_c · N_s · k` |
| **Power grid** | bus / generator / load graph | `N_nodes` | measurement type (voltage / current / phase / power) | `N · 4` |
| **CNN feature maps** | spatial position | `H × W` | feature channel | `H · W · C` |

**Anchor citations**: chess-spectral 4D's spatial base is the Rinaldi-Unciuleanu & Chiru 2026 hypercube (`{1,...,8}^4`, Chebyshev metric, interior degree `3^4 − 1 = 80`) — vendored at [`hoodoos/rinaldi-unciuleanu-chiru-2026.xml`](hoodoos/rinaldi-unciuleanu-chiru-2026.xml). chess-spectral 2D's 64×10 = 640D and 4D's 4096×11 = 45056D structures are explicit in [`qm_2d.py`](../chess-maths/chess-spectral/python/chess_spectral/qm_2d.py:103) and [`qm_4d.py`](../chess-maths/chess-spectral/python/chess_spectral/qm_4d.py).

**A third distinct sense of "hyper" surfaces here.** Project usage of "hyper" now has three documented senses:

1. **Algebraic-hyperdimensional** (§3.5.1) — high-dim vector space for spectral representation; HDC hypervectors, eigenphase T^n, cross-polytope on S^(n−1). Math-instrument layer.
2. **Hyper-as-3D-spatial-interface** (MFO §VII.4.1 + [`memory/user_stance_hyper_as_3d_spatial_interface.md`](../../memory)) — higher-dim phenomenon whose 3D-spatial boundary is a closed n-manifold; event horizons, magnetospheres, gravitational figures. Physics-layer scoped operator.
3. **Hyper-dimensional-spatial-base** (this section) — a discrete base manifold whose intrinsic dimensionality exceeds 3; chess-4D's `{1,...,8}^4` is the load-bearing project instance. Mathematical-geometry-of-the-base layer.

When discussing "hyper" anywhere in the project, distinguish which of the three senses is operative; they are mathematically distinct and should not be conflated.

**Operator orthogonality**: the §3.5.4 fiber bundle decomposes as `total = base × fiber` (tensor product). The graph-Laplacian + eigenphase-torus lift (§3.5.1 layer b) applies to the **base** factor; HDC bind/bundle operations apply to the **fiber** factor; group-theoretic symmetry actions (D₄ on chess-2D base, B₄ on chess-4D base, signed-permutation groups generally) act on the base. The total-space `C^N` quantum state in chess-spectral is `psi ∈ C^|base| × C^k` (tensor product), with the channel-projector `P_c` (sparse `I_k × I_|base|` Kronecker slice) reading the per-fiber-component probability via Born-rule measurement. Math identity: this is **standard fibered representation theory**, applied to the chess move-graph base.

**MPM provenance**: chess-spectral's qm_4d implementation directly addresses Rinaldi-Unciuleanu & Chiru's future-work bullet "spectral analysis of move graphs." The project does not claim invention of 4D chess (cite Rinaldi-Unciuleanu & Chiru for the spatial rules); the project contributes the spectral-analysis implementation of the open direction those authors named.

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

### Calibration update from cross-domain absorption rounds (2026-05-09)

The config-vs-substrate ratio **varies by domain**. From the audio (§5.2), protein-folding (§5.3), telecom (§5.4), and power-grid (§5.5) rounds:

- **Graphics ~80/20.** Most operators are closed-form `g(λ)`; bilateral / reaction-diffusion / full Cahn-Hilliard are the imperative outliers.
- **Audio ~80/20.** Same profile. EQ family, denoising (Wiener / spectral subtraction / MMSE-LSA), reverb, pitch-shift, ambisonic encoding all close. Compressors / auto-tune / neural vocoders / source separation are substrate.
- **Telecom ~70/30.** Intermediate. OFDM equalisation, MIMO precoding (SVD), beamforming weights, filter design, error-correction algebra, CSI-based positioning all close. Iterative decoders (Turbo / LDPC / Polar SCL), adaptive equalisers, cognitive-radio ML, satellite station-keeping are substrate.
- **Power grid ~30/70.** Closed-form menu meaningful (modal damping, harmonic filtering, voltage regulation, stability margins) but Newton-Raphson power flow, OPF, unit commitment, dynamic simulation, EMS / DERMS dominate.
- **Protein folding ~20/80** — *most inverted*. NMA / GNM / ANM family, contact-map smoothing, Ramachandran-T² priors, surface heat-kernel signatures close; molecular dynamics / AlphaFold / Rosetta / Monte Carlo / docking dominate.

The architectural framing must accommodate **all** ratios. srmech's value proposition is *not* "everything fits in config" — it's:

> **The closed-form portion fits in config. The substrate portion is named primitives invoked by config. The ratio depends on the domain's underlying physics.**

**The pattern across five rounds** (2026-05-09 articulation, surfaced by the power-grid round): substrate dominates where physics is **nonlinearly state-coupled** (proteins, power grid); closed-form dominates in **passive signal-processing** domains (graphics, audio); **telecom is intermediate** because both apply (OFDM is closed-form; channel tracking and iterative decoding are substrate). The ratio is a property of the domain's underlying physics, not a design choice.

In substrate-dominated domains (proteins, power grid), the **Path D** pattern from §2 (spectral *index* over heavy substrate work) is more relevant than the **Path C** pure-unification pattern. In config-dominated domains (graphics, audio), Path C's full unification carries the work. Telecom is mixed; both Paths apply at different layers. **Path C and Path D are both first-class srmech offerings; which dominates depends on which side of the ratio the domain falls.**

---

## §5 Sources & cross-domain absorption rounds

### §5.1 Original inbound brief — graphics-domain (2026-05-09)

The original 2026-05-09 inbound research brief (`srmech-art-knowledge-subsume.md`, since deleted per "exclude from tracking, delete when done") contributed:

- The universal `(Transform, λ_k, g)` decomposition framing now in §3.0
- The four-existing-primitives table in §3.1
- The Laplace-Beltrami cross-manifold table in §3.5
- The selection-shape host-side discipline in §3.6
- The Perlin-replacement static-vs-dynamic split in §3.7
- The seven additional candidate effects in §4.1
- The closed-form-vs-substrate-primitive answer in §4.2

The brief proposed a 3000–5000-word standalone notebook chapter and detailed file-by-file repo references; we absorbed the architectural insights into this notebook's existing structure rather than writing a separate chapter, per the user's "don't do exactly what it says if it's against what we've already been doing" framing. Where the brief and the existing srmech work overlap (Inkscape + Skia + GEGL framing, three-layer architecture, SkPhase9BIP-as-HDC), we deferred to what was already in §0–§3 of this notebook and the 2026-05-09 subagent investigation memorialised in `project_inkscape_skia_gegl_kernel_candidates.md`.

### §5.2 Audio absorption round (2026-05-09)

Cross-domain scoping run via the dual-agent research pattern. **Detailed report:** [`notes/audio-scoping-2026-05-09.md`](notes/audio-scoping-2026-05-09.md).

**Headline findings:**

- **Audio instantiates every row of §3.5 cross-manifold table** — spectrogram → Euclidean grid; HRTF / ambisonics → sphere S² (`l(l+1)`); periodic loops → torus T²; acoustic meshes → triangle mesh; mic-array + Tonnetz → general graph. Cleanest cross-pollination test the framing has faced.
- **Spectrogram is a 2D image** → all graphics primitives port directly. Heat-kernel blur on spectrogram = noise reduction; Perona-Malik on spectrogram = harmonic-percussive separation (Fitzgerald 2010); DoG on spectrogram = onset detection.
- **Music theory IS cyclic-group theory.** Z₁₂ chromatic, D₁₂ key+transposition, Tonnetz Z₁₂×Z₁₂. **`AudioPhase12BIP` is the audio-domain `SkPhase9BIP` cousin** — same architecture, different alphabet.
- **Bilateral audio is directly load-bearing for the EMDR project's mission.** Audio as a peer modality alongside motor + LED, under the same UTLP-coordinated catalogue. Operators (alternating tones, binaural beats, isochronic tones, music-driven panning, cardiac-coherence pacing) are all closed-form `g(λ)` entries. Hardware: ~$2–5 BOM (PCM5102 / MAX98357 / UDA1334 I²S DAC). Potentially the shortest-path proof-of-concept for srmech on the project's actual mission.
- **AMSC `literature_curated` already covers DSP knowledge** (RBJ EQ Cookbook, ISO 226, ERB/Bark/A-weighting, Moore-Glasberg masking, codec specs); `binary_archive` covers HRTF / RIR / speech / music corpora.
- **Operator counts:** ~75 closed-form `g(λ)` operators across 11 thematic groups; ~26 substrate primitives. Config-vs-substrate ratio ~80/20.

### §5.3 Protein-folding absorption round (2026-05-09)

Cross-domain scoping run via the dual-agent research pattern. **Detailed report:** [`notes/protein-scoping-2026-05-09.md`](notes/protein-scoping-2026-05-09.md).

**Headline findings:**

- **GNM / ANM / NMA on the residue-interaction network is graph-Laplacian eigendecomposition — literally the same primitive** ephemerides uses on the 52-body resonance graph (§13 gateway-graph Fiedler partition; Matthews φ = +0.336, Spearman ρ = +0.743 vs empirical Δv). Same math, different graph. **Not analogy — identity.** Strongest cross-domain validation evidence to date that srmech's manifold-parameterised Laplace-Beltrami framing is load-bearing rather than aesthetic.
- **Helmholtz wave on RIN = NMA harmonic time evolution.** `g(λ_k) = cos(c·t·√λ_k)` where `√λ_k = ω_k`. The §4.1 Helmholtz-wave row *is* the harmonic time evolution of vibrational modes on a protein. Same equation; not metaphor.
- **Contact / distance map = 2D image** → all graphics primitives port verbatim. Perona-Malik on contact map preserves α-helix and β-sheet diagonal-band structure (state-dependent diffusion preserving edges).
- **Ramachandran (φ, ψ) torus T²** = first non-graphics use of §3.5 torus row. **Protein surface** = sphere + triangle-mesh rows (3D Zernike, Sun-Ovsjanikov-Guibas heat-kernel signature).
- **Foldseek 3Di alphabet = `SkPhase9BIP` structural cousin** — 20-letter learned structural alphabet, cyclic-group-amenable HDC binding.
- **Sheaf-Laplacian on RIN ↔ doom-spectral §3 sheaf-Laplacian raycasting** — cross-pollination beyond graphics.
- **AMSC binary_archive scaling forcing function:** AlphaFold DB ~25 TB; ESM Atlas ~100 TB. 4000–20000× larger than JPL DE441 (~5 GB). Forces streaming-download / partial-fetch / content-addressed dedup design.
- **Config-vs-substrate ratio inverts to ~20/80.** Substrate dominates (MD, AlphaFold, Rosetta, Monte Carlo, docking). **Calibration update for §4.2** — see calibration block above.
- **EMDR-project connection: none direct.** Cross-domain stretch test for srmech's universality, not productisation target. Honest framing.

### §5.4 Telecom absorption round (2026-05-09)

Cross-domain scoping run via the dual-agent research pattern. **Detailed report:** [`notes/telecom-scoping-2026-05-09.md`](notes/telecom-scoping-2026-05-09.md).

**Headline findings:**

- **OFDM IS the `(Transform=DFT, λ_k=subcarrier-frequency, g(λ_k)=channel-equaliser-coefficient)` decomposition.** §3.0's universal decomposition is the operating principle of every modern wireless standard (5G NR / Wi-Fi 6/6E/7 / DVB-T2 / LTE / ADSL / DOCSIS 3.1). Transmitter applies IDFT, receiver applies DFT, channel equaliser is exactly `g(λ_k) = 1/H(λ_k)` per-subcarrier. **Identity, not analogy.** Comparable strength to GNM/NMA-on-RIN identity in protein round.
- **MIMO precoding via SVD = PCA sibling.** Channel `H = U Σ V*`; same primitive as protein-ensemble PCA, ephemerides Fiedler eigendecomposition.
- **Satellite ISL constellation graph is direct sibling of ephemerides 52-body resonance graph.** Starlink ~6500 sats × 4 lasers; Iridium NEXT 66 × 4. Time-varying graph; Fiedler vector predicts congested gateways. **Path D spectral index is the natural pattern for satellite-constellation queries.**
- **UTLP IS a telecom protocol** (per `UTLP_Specification.md`). The project has been shipping a connectionless distributed-coordination telecom protocol since v0.3.0-beta.1 without using the word.
- **RFIP IS Path D in the radio domain.** RSSI / CSI / TDoA / FTM / UWB / AoA observations form a heavy-store; CSI fingerprint mode is most spectrally direct.
- **`SpectrumPhase4096BIP` + `OfdmGridPhaseBIP` + `IPMACPhaseBIP` + `TLEPhaseBIP`** — multiple `SkPhase9BIP` cousins. Most cyclic-group-rich domain scoped to date.
- **Operator counts:** 80+ closed-form `g(λ)` operators across 11 thematic groups; 52 substrate primitives. Config-vs-substrate ratio **~70/30** — intermediate between graphics/audio and protein/power.
- **AMSC `literature_curated` corpus** is largest scoped (ITU-T / ITU-R / 3GPP TS+TR / IEEE 802 / IETF RFC / DVB / ETSI / CCSDS / FCC).
- **Project-mission relevance: STRONGEST INFRASTRUCTURE FIT.** Telecom is the substrate underneath audio, motor, LED, BLE, ESP-NOW, UTLP, RFIP, every coordinated bilateral pulse.
- **Path-D-on-UTLP-beacon-history is a concrete v0.27.x demo candidate** — same primitive as ephemerides 52-body Path D, applied to project's operating infrastructure.

### §5.5 Power-grid absorption round (2026-05-09)

Cross-domain scoping run via the dual-agent research pattern. **Detailed report:** [`notes/power-grid-scoping-2026-05-09.md`](notes/power-grid-scoping-2026-05-09.md).

**Headline findings:**

- **Y-bus admittance matrix IS a weighted graph Laplacian** on the transmission graph. **Fifth instantiation** of the same architectural slot: chess board-adjacency → ephemerides 52-body resonance graph → protein RIN GNM → audio mic-array → power transmission. **Five domains; no analogy — identity.** Strongest cumulative validation of §3.5 to date.
- **Inter-area electromechanical oscillation modes (0.1–1 Hz) ARE NMA on the rotor-swing graph.** Linearised swing equation `M ẍ + D ẋ + K x = 0` has eigenvalues `√λ_k = ω_k` — *literally* protein NMA on a different graph. Same Helmholtz-wave row of §4.1 instantiated for the third domain.
- **Fiedler partition for islanding analysis = ephemerides §13 + protein domain decomposition.** **Concrete falsifiable spike test:** run Fiedler partition on IEEE 39-bus / 118-bus benchmarks; compare to Chow-Kokotović slow-coherency. If Matthews φ and Spearman ρ comparable to ephemerides §13 (φ = +0.336, ρ = +0.743), srmech's universality claim acquires a fourth quantitative datapoint. **A real testable cross-domain prediction.**
- **PMU / IEEE C37.118 + IEEE 1588 PTP literature is the gold-standard reference for distributed-time-coordination.** PMU delivers ~1 μs across continental-scale grids; UTLP delivers ~100 μs across two BLE peers. Same protocol class, three orders of magnitude tighter, 30+ years operational. **Genuine cross-pollination win for UTLP doctrine.**
- **`Phase60HzBIP` + `PhaseHarmonicBIP` + `PhaseEventBIP`** — direct cousins of `SkPhase9BIP`.
- **Cascade-failure spread is reaction-diffusion-on-graph** — sibling of graphics §3.7 dynamic generators.
- **Operator counts:** 55+ closed-form `g(λ)` operators across 9 thematic groups; 39 substrate primitives. Config-vs-substrate ratio **~30/70** — substrate-dominated, similar to proteins.
- **Project-mission relevance: none direct.** Cross-domain stretch test for srmech universality. Genuine wins: (a) Y-bus = Laplacian validates §3.5 for the fifth time; (b) PMU/IEEE 1588 literature directly informs UTLP doctrine; (c) Fiedler-partition falsifiable cross-domain prediction.

### §5.6 Standard practice — dual-agent research pattern

Going forward, cross-domain absorption rounds use the dual-agent research pattern (memory: `feedback_dual_agent_research_pattern.md`):

- **Main agent** (with conversation history + project context) produces analysis informed by conversation-context sharpness on framework edges.
- **Sub-agent** (independent fresh-read of srmech notebook; general-purpose `Agent` tool, run_in_background=true) produces breadth-first enumeration with stronger citation discipline and (counterintuitively) often better memory application.
- **Comparison** identifies convergent load-bearing claims (high-confidence) and divergent margin findings. Combined > either alone.
- Headline findings land in this notebook (§3.5 manifold examples, §4.2 calibration ratios, new §5.X subsection); detailed scoping reports preserved in `notes/`.

The dedicated-updates gate (`project_srmech_dedicated_updates_gate.md`) was lifted 2026-05-09; cross-domain absorption is the primary srmech work, not a side thread.

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
