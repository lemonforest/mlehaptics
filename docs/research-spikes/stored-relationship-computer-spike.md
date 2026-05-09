# Stored-relationship computer — research spike

**Date:** 2026-05-09
**Status:** Research spike. Pre-v1.0 architectural-review artifact. Not a ship.
**Related:** PR #284 ROADMAP entry (pre-v1.0 backfill review). Saturn ring three-phase exercise (PRs #286 / #289 / #290 / #291) was the empirical prompt.

---

## The question

> *"What is really so different about chess-spectral and ephemerides-spectral that we couldn't have the same stored-relationship computer thing? I think there is probably no reason that we cannot have everything config-driven such that we are a chess engine if we load chess-kernel things or we are a massive ephemeris if we add cosmic kernels."*

The hypothesis: the project's eight spectral-domain notebooks — chess-spectral, chess-spectral-4d, othello-spectral, doom-spectral, antikythera-spectral, ephemerides-spectral, MFO, logo-HDC — are not actually eight different things. They're eight **instantiations** of a deeper substrate that the project has been building incrementally without naming. Each domain is a *kernel* loaded against a shared **stored-relationship computer**. v1.0 of the unified work would be to pull the substrate out from under all eight projects and let them be **plug-ins**.

This spike checks the hypothesis empirically. It does not commit to a unification — it surfaces what would need to be true for the unification to be load-bearing, and what concrete next steps would test the proposition.

A second question, posed mid-spike: **can the storage layer also be spectral?** If the project has been building a spectral *computer* over relationship data, can the *storage* of that data also live in the same eigenbasis? The two questions interact; answering one changes the design surface for the other. Both are addressed below.

---

## Multi-domain substrate evidence

Reading the eight notebooks reveals a substrate that's already domain-agnostic in shape, just not yet extracted as code. The empirical pattern across all eight projects:

| Layer | chess | chess-4d | othello | doom | antikythera | ephemerides | MFO | logo |
|---|---|---|---|---|---|---|---|---|
| **Graph-Laplacian eigenbasis** | 8×8 board | `Z_8^4` 4D path-graph | P₈□P₈ DCT-II | Blockmap + Sector | gear-DAG | 52-body resonance | fractal Sierpinski/Pn | reuses chess's D4 only for geometry channel |
| **Channel decomposition** | 11 (1 A1 + 4 STD4 + 3 FIB + 2 FA_PAWN + 1 FD_DIAG) | 11 (v1.1.1 adds Y/W pawn split) | D₄×Z₂ irreps {A1±, A2±, B1±, B2±, E±} | 5 tracks (base graph + Z-fiber + sheaf raycast + sound diffusion + BIP encoder) | 13 dials with dense complex bases | per-body action-angle | eigenvalue gaps as channels | vocab × syntax × geometry split-object |
| **Kinematics (state→ψ)** | `qm_4d.state_to_psi` | pending (qm_4d) | character projection at 1e−10 | BIP encoder, Phase-9 | encode_ant.py three D variants | `_research/kinematics.py` (port from chess #99) | KK mode decomposition | turtle interpreter (no explicit ψ) |
| **Dynamics layer** | `qm_4d_dynamics` (Hatano-Nelson, KAM, Nambu) | phase-operator framework | sheaf-Laplacian + bracket-aware restriction | heat-equation diffusion, 8-step Euler | equant (Hipparchian + Ptolemaic) | `_research/dynamics.py` (port from chess #100) | spectral dimension flow | partial-trace fibers |
| **HDC / cyclic-group binding** | channel-by-mode 11×4096 | B_4 = (Z_2)^4 ⋊ S_4 | not used at kinematics level | BIP D=512, Z_{2^32} ALU, coprime shifts (67, 7) | encode_ant.py, three D variants (940, 13440, ~10²⁷) | BIP D=32, Z_{2^32} ALU | not HDC; geometric/topological | MAP-B bipolar D=10000 |
| **Bridge surface pattern** | qm_4d_bridge | n/a (pre-merge) | encoder pipeline v0.3.2 | (existence proof, no bridge yet) | (no bridge yet) | bridge.py | (no bridge yet) | (no bridge yet) |
| **MPM discipline** | discipline born here (§42) | inherits | inherits | cited | cited | formalised in §0.0 | "joins as first-class MPM target" | cited |
| **AMSC framework** | not yet | not yet | not yet | not yet | shared infra (cyclic-group + ephemeris kernels) | shipped v0.25.x | not yet | not yet |
| **Frozen-snapshot codegen** | source→wheel byte-exact | inherits | C17 reference encoder bit-identical | n/a | inherits | source→wheel byte-exact | three deterministic Python scripts | inherits |

**Reading**: the substrate is shared across all eight notebooks at the **mathematical-tool** level (graph-Laplacian eigenbasis, character projection, irrep decomposition, HDC binding, MPM discipline). The shape of the kinematics + dynamics modules is shared between chess and ephemerides directly (tasks #99 and #100 ported chess-spectral's `qm_*.py` / `qm_*_dynamics.py` into ephemerides). doom-spectral cites chess-spectral as the **Rosetta Stone** (§7.4) and is the **first end-to-end existence proof** of cross-disciplinary methodology. othello-spectral instantiates chess §10's framework on a simpler domain at machine precision (eigenbasis transfers at 5.86e−16). chess-spectral §15.4 explicitly names the cross-domain transfer template.

---

## Per-domain unique contributions

What each domain *adds* that the others don't address — these are the architectural dimensions a unified core would have to subsume:

**chess-spectral**: Hatano-Nelson asymmetric pawn dynamics; KAM small-denominator structure across the channel decomposition; Nambu non-equilibrium thermodynamics integration; D4 irreps + fiber-bundle pawn split.

**chess-spectral-4d**: dimension-sensitive king decomposition (HD ∈ {1,2,3,4} reveals unnamed trihedral/tetrahedral steppers); pawn Y↔W mirror axis split via `I⊗I⊗I⊗W_ANTI_DCT`; rank-3 fiber structure holds across both 2D and 4D (representation-specific, not graph-intrinsic); B_4 = (Z_2)^4 ⋊ S_4 irrep group with 384 elements / 20 irreps.

**othello-spectral**: exact Z₂ symmetry (no pawn-fiber breaks); sheaf-Laplacian λ₂ tracks legal-move count (Spearman ρ = +0.765, p = 1.1e−12) — a per-move dynamic discriminant chess doesn't report; bracket-aware restriction maps depending on R2_COMPLETE / R3_PENDING ray-segment status; disc-count monotone as global T-breaker; **same eigenbasis as chess at machine precision** (the cleanest evidence that the substrate is shared).

**doom-spectral**: 2.5D fiber-bundle gating (elevation as trivial scalar fiber on 2D base manifold; Z-fiber state-dependent edge gating); directed sheaf-Laplacian raycasting for LoS/hitscan with Bresenham 1D ray composition; topological sound diffusion (heat-equation on Sector graph, 8-step Euler); haptic manifold binding (per-sector anchor hypervectors → motor tension via Q16 cosine similarity); IDSPECTRAL cheat as end-to-end ALU-only integer pipeline. **Three new architectural layers** absent from chess+ephemerides.

**antikythera-spectral**: gear-DAG topology + Diophantine-approximation framing; (precision, cost) Pareto-front analysis for missing-gear-placement inversion; periphery rule (graph-centrality constraint on missing-gear placement); seasonal-observability + field-programmability rationale (mechanism designed for re-anchoring during heliacal-rising windows, not drift-free continuous operation); setting-mode gears + crank-as-clutch + selective-lock per-cluster engagement. T-symmetry (pointer backward yields valid past predictions) as reversible-operator framing.

**ephemerides-spectral**: AMSC framework (descriptor + adapter + MPRRecord + bridge surfaces, T0/T1/T2/T3 reproducibility tiers); MPM discipline formalisation (the four screens, ratchet conventions, T-tier reproducibility); dynamical-regime classifier (eigenbasis projection over labelled regime training rows, v0.24.9); dual-author validation pattern (AMSC NDJSON ↔ hand-coded `@dataclass + List` byte-exact diff, Saturn ring exercise PR #291); J₂-corrected Kepler closing the 0.13% Mimas residual via FFT-untruncation discipline.

**MFO**: fractal metric field as fundamental (matter and force fields as harmonic excitations of a single fractal geometry; spatial/internal dimensions as the same geometry at different resolutions); KK reinterpretation as electromagnetic waveguide physics with `v_g · v_p = c²` proven exactly; mass = waveguide cutoff frequency `ω_c = mc²/ℏ`; spectral dimension flow `d_S` non-monotonic (4 IR → 2 UV, peaking ~6–8 intermediate scales) — distinct from string theory's `d_S → 11`; non-Killing perturbation breaks Atiyah-Hirzebruch chirality no-go theorem. **MFO explicitly disclaims being a kernel** ("not the project's endorsed answer over alternatives"); it's a candidate foundational-ontology framing, not a domain plug-in.

**logo-HDC**: split-object pattern (atoms × productions × geometry as F₁, F₂ fibers); structured atoms from quantum-number 5-tuples composed via `bundle_sum` (preserves role-swap linearity); F₁ rank-7 (vs. predicted 3–4) reveals seven crisp atom↔rule modes; **L7b critical negative result**: partial-trace fibers built at trace-segment N **fail to predict** geometry at N+Δ (cos −0.125 vs. snapshot baseline +0.730, gain −0.855). This negative result is load-bearing: it says that **trajectory prediction requires per-move fibers, recurrent formulation, or time-coordinate explicit keying** — fiber summary alone is not enough. Any unified core that wants to predict trajectories will hit this wall.

---

## What's genuinely domain-specific

The domain-specific surfaces across all eight projects:

| Layer | Domain-specific content |
|---|---|
| **Channel content** | chess: 11 channels named after D4 / pawn / fiber-bundle structure. othello: D4×Z2 irreps. doom: 5 tracks per-engine-subsystem. antikythera: 13 dials with per-period dense bases. ephemerides: per-body action-angle. MFO: eigenvalue gaps. logo: vocab × syntax × geometry split-object. |
| **Per-channel builders** | chess: `u_move_*` operators. ephemerides: orbital propagation + perturbation theory + J₂. othello: bracket-aware sheaf restriction. doom: Bresenham raycaster + heat-equation + BIP encoder. antikythera: equant + epicycle + pin-and-slot. MFO: KK mode decomposition + product-geometry eigenvalue addition. logo: per-row L1-normalized fiber matrices. |
| **State-update semantics** | chess/othello: discrete legal-move-bound transitions. ephemerides: continuous-time Hamiltonian flow + driven coupling. doom: continuous spatial motion + portal traversal. antikythera: clockwork rotation. MFO: scale-flow (no states, no updates — RG-style). logo: turtle execution. |
| **Loader / parser** | chess/4d: PGN/FEN/EPD. othello: PGN + Takizawa archive. doom: WAD parser. antikythera: gear database. ephemerides: JPL DE441 + AMSC NDJSON. MFO: Sympy proofs + JSON results. logo: AST parser + interpreter. |
| **Constraints** | chess/4d: 50-move, threefold, en passant. othello: D4×Z2 invariance + bracket validity. doom: map-registration gate (E1M1 only). antikythera: cyclic-group ratios + periphery rule + Pareto frontier. ephemerides: physical conservation + J₂ ≥ 0. MFO: d_S → 2 at UV; SM mass² ratios. logo: AST grammar. |

**These are not architectural divergences.** They are *content* differences riding on the same machinery. A unified core would expose hooks for each; the kernels stay domain-specific.

---

## Can a relationship database be spectral?

The user asked this mid-spike. The short answer is **yes, three times over**. The nuance is *which* yes the project should claim.

### Yes (1) — trivially: any DB is a graph

Every relational schema is a graph (tables = nodes, foreign keys = typed edges). Every property graph (Neo4j) and every triple store (RDF, SPARQL) is a graph by construction. Every graph admits a Laplacian. Every Laplacian admits an eigenbasis. So in the literal "is spectral analysis applicable to this data shape" sense, the answer has been yes for thirty years (Fiedler 1973; Chung 1997; Spielman ongoing). What the project would do here is no different in *kind* from what spectral graph clustering, query-plan optimisation via graph-cut, or PageRank-style spectral ranking already do. Nothing novel, but the framing fits.

### Yes (2) — already exists in the literature

A whole class of databases has, in fact, been **spectral storage from day one**:

- **Vector databases** — FAISS (Johnson 2017), Pinecone, Weaviate, Chroma, pgvector, Milvus. Store high-dim embeddings; query via cosine similarity / approximate-nearest-neighbour. ANN over normalised vectors is exactly the cosine-similarity-in-eigenbasis primitive the project uses (see chess `transport(N) = M_hi.T · e_N`; doom Q16 `<player_HV, sector_anchor>`; ephemerides BIP cosine).
- **Knowledge graph embeddings** — TransE (Bordes 2013), TransR, RotatE (Sun 2019), ComplEx (Trouillon 2016), DistMult, ConvE. Embed every entity + every relation into a continuous space; queries become linear-algebra operations. Multi-hop joins become vector composition. This is structurally identical to the project's HDC encoders.
- **Hyperdimensional computing** — Pentti Kanerva 1988 (sparse distributed memory); Plate 1995 (HRR); Gayler 2003 (VSA); Kanerva 2009 (BSC). The project's BIP encoder, MAP-B encoder (logo), encode_ant (antikythera), and 11-channel chess encoder are all instantiations of the HDC family. HDC *is* spectral relationship storage; the project has been building HDC databases without naming them as such.

The verdict on "is the spectral relationship database a real category": yes, and the project is already building one across eight domains. The novelty isn't the category — it's the unification of one HDC encoder per domain into a single substrate.

### Yes (3) — the project's own evidence

Each of the project's eight notebooks already encodes domain relationships as spectral hypervectors:

- chess: `pos4 → ψ ∈ ℂ^{45056}` (11 channels × 4096 modes). Board state stored spectrally; queries (move classification, complexity, depth-gap correlation) run via inner products in the eigenbasis.
- doom: `(x, y) → BIP-512 hypervector`; per-sector anchor hypervectors; queries (which sector is the player in? sound-propagation tension?) via Q16 cosine.
- antikythera: `date → resonant superposition Σ_dial roll(channel_basis_dial, residue_dial(date))`; queries (which dials align? what's the eclipse prediction?) via FFT circular correlation.
- ephemerides: `body × time → action-angle hypervector`; queries (find_syzygies, get_breathing_modulation) via spectral projection.
- logo: atom-quantum-number-tuple → MAP-B D=10000 bipolar; queries (role-swap, character-class recovery) via cosine + role-level unbind.

**The storage layer is already spectral in seven of eight projects.** What's missing is a **unified spectral-storage primitive** that all kernels share — today, each project rolls its own encoder + its own dimension + its own binding scheme.

### What the unification would look like (Path D, below)

A spectral relationship database that subsumes the AMSC layer would:

1. **Write path**: at AMSC ingestion time, project each row onto a domain-relationship-graph Laplacian eigenbasis. The descriptor declares the graph topology + the eigenbasis dimension; the adapter emits row hypervectors instead of (or alongside) the current data-dict NDJSON.
2. **Read path**: bridge surface returns hypervectors directly; queries are cosine-similarity searches in eigenbasis.
3. **Multi-relation joins**: become **product-eigenbasis searches** — bind two hypervectors via cyclic-group binding, query result via cosine in the product space.
4. **Per-mode attestation**: instead of per-row `response_sha256`, emit per-eigenmode SHA-256 over the projection coefficient vector. AMSC's MPM discipline survives the spectral encoding because each mode's coefficient is reproducibly derived from raw bytes through a published projection operator.

### Architectural tensions

- **Lossy vs lossless**: spectral storage is naturally lossy when truncated; AMSC's MPM discipline requires byte-exact provenance. The fix: store both (raw NDJSON + spectral projection); the spectral layer is a derived index, not a replacement. The dual-author pattern (PR #291) is precedent for this — two authoritative encodings of the same data, asserted equal.
- **Schema evolution**: eigenbasis depends on graph topology; topology depends on schema. Adding a foreign-key relation changes the Laplacian → existing hypervectors stop matching. RDBMS `ADD COLUMN` is cheap; spectral re-projection is not. The fix: kernel-versioned eigenbases (cf. `_research/saturn_rings_data.py` v0.27.x rolling); old hypervectors live until kernel version bumps; new hypervectors use the new basis.
- **Query expressiveness**: cosine similarity is great for "find similar"; SQL JOIN with predicate filters is harder. The fix: spectral DB augments, doesn't replace. SQL stays for predicate filters; spectral layer answers "which rows resemble this configuration" / "which dynamical regime is this" / "which sector cluster does this player belong to" — questions SQL can't ask cheaply.
- **Cross-kernel queries**: chess hypervectors live in ℂ^{45056}; doom hypervectors live in ℝ^{512} (BIP); ephemerides hypervectors live in BIP D=32. They are not directly comparable. The fix: per-kernel hypervector spaces stay disjoint; cross-kernel queries route through a kernel-router that knows how to translate (or refuse). Path D doesn't promise universal cross-kernel queries — it promises that *each kernel* shares the substrate.

---

## Four architectural paths forward

### Path A — Status quo (no unification)

Each project ships independently. Discipline shared via the MPM doctrine + cross-references in the notebook collection.

- **Pros**: zero migration cost; each project remains independently shippable; project boundaries already proven.
- **Cons**: every new domain instantiation re-derives architecture; the §15.4 cross-domain transfer template stays aspirational.

### Path B — Extract a shared utility layer (modest factoring)

Pull the genuinely-shared infrastructure into a small `spectral-substrate` package both projects depend on:
- AMSC framework (descriptor + adapter + MPR + bridge surfaces)
- MPM-screening discipline (four screens; ratchet conventions; codegen-determinism harness)
- Frozen-snapshot codegen (`research/` → `_research/` byte-exact mirror)
- Bridge / CLI scaffolding

Each project depends on `spectral-substrate>=1.0`; each retains its own kinematics + dynamics + channel decomposition.

- **Pros**: bounded scope; immediate de-duplication of AMSC + MPM + codegen machinery; can be staged across multiple ships.
- **Cons**: doesn't actualise §15.4's cross-domain template; doesn't enable runtime kernel composition.

### Path C — Stored-relationship computer (full unification of computation)

Build a unified core whose surface is **kernel-driven**:

```python
import stored_relationship_computer as src

src.load_kernel("chess-kernel")
# bridge surfaces are now: encode_fen, apply_move, analyze, etc.

src.load_kernel("cosmic-kernel")
# bridge surfaces are now: list_bodies, get_system_state, find_syzygies, etc.

src.load_kernel("doom-kernel")
# bridge surfaces are now: encode_player, sound_diffuse, sector_tension, etc.
```

Each kernel registers: channel decomposition; per-channel builder dispatch; state loader; state-update operator; optional AMSC descriptors + dynamical-regime rows. The core provides: Laplacian eigenbasis on registered graph(s); kinematics layer (state→ψ; Born-rule); dynamics dispatcher; HDC / cyclic-group binding (with kernel-declared dim); AMSC framework; MPM screening; bridge / CLI; codegen.

- **Pros**: actualises §15.4 literally; new domains require kernel-registration only; doom-spectral's existence proof + othello-spectral's machine-precision substrate transfer + the chess→ephemerides v0.12/v0.13 port are all independent evidence the unification is feasible.
- **Cons**: substantial migration cost; channel-shape abstraction needs careful design (chess 11-channel D4 vs ephemerides per-body action-angle vs doom's 5 tracks vs antikythera's 13 dials is not trivially unified); doom's three new layers (fiber-bundle gating, sheaf raycasting, sound diffusion) need to be hooks on the core, not chess-specific.

### Path D — Spectral relationship database (unify storage + computation)

Path C, plus: AMSC's row-level data store becomes a **spectral hypervector store**. Each ingested row is projected onto the kernel's Laplacian eigenbasis at write time; queries are cosine-similarity searches in eigenbasis.

- **Pros**: collapses two layers (current AMSC NDJSON + per-domain HDC encoder) into one substrate; per-mode attestation extends MPM into spectral storage; the project becomes a fully-fledged HDC database, not a collection of HDC encoders + a relational data layer that don't talk to each other.
- **Cons**: significant new design surface; lossy/lossless tension (mitigated by storing both); schema-evolution cost (mitigated by kernel-versioning); doesn't eliminate SQL/relational queries (they coexist).

Path D is the strongest version of the user's framing. It's also the largest scope. **Path D depends on Path C succeeding.** A standalone Path D without Path C is a different project (a spectral RDB without the kernel-loading abstraction), already partially served by existing vector DBs + KG-embedding libraries.

---

## Pre-v1.0 spike experiments

Before committing to Paths C or D, four spike experiments would tell us whether the unifications are empirically the right factorings. Each is bounded, ships in a feature branch, and carries its own MPM-screening test.

### Spike 1: Channel-shape abstraction (Path C foundation)

Define a single `ChannelDecomposition` Protocol that both chess-spectral's 11-channel D4-decomposition and ephemerides-spectral's per-body action-angle could implement. Express each as a registration against the same Protocol. Test: round-trip a chess board state through the unified interface, then a Mercury action-angle state, and verify both produce valid ψ vectors of the right per-domain dimension.

If pass → unified core's kernel-registration interface has a concrete shape; Path C is feasible.
If fail → divergence is real architectural divergence; Path B is the most we can sensibly factor.

### Spike 2: Cross-kernel classifier (Path C validation)

Take the v0.24.9 dynamical-regime classifier. Add chess-spectral's channel-energy "crisis ply" rows + doom-spectral's sector-tension distributions as additional labelled corpora. Run all three through the same eigenbasis projection. Does the classifier still partition rows sensibly when the corpus spans three domains?

If pass → cross-pollination works at classifier level; the §18.9 hypothesis ("more domains → more discriminative classifier") gets concrete evidence.
If fail → regime taxonomy is per-domain; unified-classifier idea needs nuance.

### Spike 3: Single-bridge multi-kernel demo (Path C runtime)

Author a small `stored_relationship_computer/` package that exposes one bridge surface and loads any of: chess-spectral, ephemerides-spectral, doom-spectral. Goal: prove the load-kernel mechanic works for three existing kernels without modifying any of them.

If `srcomp encode --kernel chess --fen "..."` and `srcomp encode --kernel ephemerides --jd 2451545` and `srcomp encode --kernel doom --player "352,1136"` all work through the same CLI: unification is real, not theoretical. Time to plan the v0.30.x or v1.0 ship.

### Spike 4: Spectral RDB on real data (Path D foundation)

Take a small dataset (Saturn rings 12 rows; or doom E1M1's 85 sectors; or chess test suite). Build the relationship graph from the dataset's foreign-key / typed-edge structure. Compute the Laplacian eigenbasis. Encode each row as a projection onto eigenbasis modes. Implement spectral-cosine-similarity query. Validate that the spectral query returns the same rows as a SQL/Cypher/SPARQL query against the same dataset.

If pass on one dataset → Path D's primitive is real; try a second dataset to confirm portability.
If pass on three datasets across three domains → Path D's unification claim has empirical legs.
If fail → the storage-as-spectral angle is conceptually right but expressively limited; Path D becomes a research curiosity, not a v1.0 ship target.

---

## Naming

The user's phrasing — **"stored-relationship computer"** — fits. Each domain is a corpus of *relationships* (chess piece adjacency, satellite resonance, ring shepherd modulation, doom sector portals, antikythera gear ratios, othello bracket validity, MFO fractal eigenvalue gaps, logo atom↔rule couplings) that gets *stored* in the catalogue layer and *computed against* via the spectral substrate.

Path D extends the metaphor: storage is *also* in the eigenbasis. Then "stored-relationship computer" means: relationships are stored as hypervectors, and computations are inner products in the same basis. That's exactly the HDC / VSA / vector-DB family of architectures, applied to the project's domain-specific substrates as kernels.

**Recommendation: stored-relationship-computer (or `srcomp` in code).**

Other candidates considered + why they're worse:
- *Spectral lattice computer* — accurate but sells short the relationship aspect.
- *Cross-domain spectral substrate* — descriptive but bland.
- *Universal Time Lord Protocol* (UTLP) extended — already used for the EMDR project's sync layer; would conflate two contributions.

---

## What this spike does *not* claim

- It does **not** claim Path C or Path D is the right answer. It claims they are *feasible* and *worth a four-spike test* before being committed to.
- It does **not** propose a v0.27.x or earlier ship. The spike experiments come first; the architectural commitment comes after.
- It does **not** propose deprecating any project. Even under Path C/D, each project remains shippable as a kernel-on-the-core; existing PyPI consumers don't need to change.
- It does **not** depend on the v0.24.x → AMSC backfill question (PR #284 ROADMAP entry). Those are separate decisions; either could happen without the other.
- It does **not** claim cross-kernel queries are universal. Per-kernel hypervector spaces stay disjoint by default; cross-kernel routing is a separate research question (a v0.30.x or later thing, if at all).
- MFO is **not** a kernel candidate at the same level as chess / ephemerides / doom. MFO is a foundational-ontology layer; per the MFO notebook, it explicitly disclaims being the project's endorsed answer. If Paths C or D ship, MFO sits *above* the substrate as a physics-level meta-framing, not *inside* it as a domain plug-in.

---

## Recommendation

1. **Do not commit to a path yet.** This is genuinely a research spike, not a ship.
2. **Run Spike 1 first** (~1 PR's worth of work). Highest-information experiment — failure rules out Path C; success makes the rest worth doing.
3. **Conditional on Spike 1**: run Spikes 2 and 3 in parallel.
4. **Run Spike 4 in parallel with Spikes 2 and 3** if Spike 1 passes. Spike 4 is independent of Spikes 2 and 3 conceptually (it tests Path D's storage primitive, not Path C's computation primitive); running it concurrently surfaces Path D evidence on the same calendar.
5. **After all four spikes**: re-read this document, decide A / B / C / D with empirical evidence in hand.
6. **Do not let this delay merging the open Saturn ring PRs** (#290, #291). The spike is informed by them, not blocked on them.

The user framed this as *"the culmination of our work."* That's worth taking seriously without rushing it. The spike is the way.

---

## References

### Project-internal — chess-spectral
- §15.4 (cross-domain transfer template; the seed of this spike)
- §1b.1 / §1b.2 / §1b.6 (Hatano-Nelson / KAM / Nambu NNET — shared literature anchors)
- §20.20 (sibling-project framing of ephemerides-spectral)
- §10 (the spectral-lattice framework Othello reproduces at machine precision)

### Project-internal — ephemerides-spectral
- §0.0 (MPM discipline formalisation)
- §17–§21 (per-body catalogue + AMSC + applicability + tool-rejection)
- §18.9 (cross-pollination via classifier corpus widening)
- §20.2.1 / §20.4.0 / §20.7 (where MFO is cited as a worked example, without endorsement)
- ROADMAP "later" entry (pre-v1.0 backfill review; PR #284)
- Tasks `#99` / `#100` (chess-spectral qm_*.py / qm_*_dynamics.py port)

### Project-internal — sister notebooks
- chess-spectral-4d: §13 phase-operator framework; §15 cross-disciplinary application routes
- othello-spectral: §0 chess §10 verification target; §2d.e cross-game comparison; §3 dynamic sheaf
- doom-spectral: §0 chess-spectral Rosetta Stone framing; §4.1 ephemerides BIP encoder reuse; §7 generic procedure; §7.4 first end-to-end existence proof
- antikythera-spectral: §0.2 chess HDC second instance; §11.6 architectural-mode hypotheses (periphery rule, setting-mode gears, crank-as-clutch)
- MFO: §I.2 explicit foundational-ontology disclaimer; §V spectral dimension flow; §VIII.2 HDC architectural convergence
- logo: §0 chess split-object pattern generalisation; §39 enumerable-domain framing; L7b critical negative result on partial-trace fibers

### Code touchpoints (load-bearing)
- chess-spectral: `chess_spectral/qm_4d.py`, `qm_4d_dynamics.py`, `tables.py`, `encoder_4d.py`, `qm_4d_bridge.py`
- ephemerides-spectral: `_research/kinematics.py`, `_research/dynamics.py`, `_research/attested_collector_*.py`, `bridge.py`, `_research/saturn_rings_data.py`
- antikythera-spectral: `research/encode_ant.py`, `gear_database.py`, `gear_topology.py`, `equant_encoder.py`
- doom-spectral: `wad_parser.py`, BIP encoder track, sheaf-Laplacian raycaster, sector-graph diffusion
- othello-spectral: encoder pipeline v0.3.2, faithful_sheaf.py, C17 reference encoder

### External — spectral graph theory
- Fiedler 1973 (algebraic connectivity)
- Chung 1997, *Spectral Graph Theory* (canonical reference)
- Spielman ongoing (forthcoming book; eigenvector decomposition for grid graphs)
- Merris 1994, *Linear Algebra and its Applications* (Laplacian eigenvector basis)

### External — dynamical literature anchors
- Hatano & Nelson 1996, *PRL* 77:570 (asymmetric lattice dynamics)
- Katagiri et al. 2025, arXiv:2508.00207 (Nambu non-equilibrium thermodynamics)
- Sekizawa, Ito & Oizumi 2024, *Phys. Rev. X* 14:041003 (spectral decomposition of entropy production)

### External — spectral relationship databases (Path D context)
- Kanerva 1988, *Sparse Distributed Memory* (HDC origin)
- Plate 1995, *IEEE Transactions on Neural Networks* (HRR — Holographic Reduced Representations)
- Gayler 2003 (VSA — Vector Symbolic Architectures)
- Bordes et al. 2013, *NeurIPS* (TransE — knowledge-graph embeddings)
- Trouillon et al. 2016, *ICML* (ComplEx)
- Sun et al. 2019, *ICLR* (RotatE)
- Johnson et al. 2017, arXiv:1702.08734 (FAISS)
- Pinecone / Weaviate / Chroma / pgvector / Milvus (production vector DBs)
