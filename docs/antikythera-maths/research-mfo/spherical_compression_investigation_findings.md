# Spherical Compression Investigation — Findings

**Date:** 2026-05-11  · **Role:** concertmaster (cross-cutting / framework-edge)  · **Dispatch:** post-T²-survey worklist next-item

## Setup

User insight 2026-05-11, in-flight during the T² L-shell magnetospheric survey: **"spherical compression is the project's natural ambient geometry, not flat Euclidean."** Sparked from the question "is there ever a reason that we might want to spherically compress a hypercube?" — answered constructively by the conductor: HDC bit-serialized hypervector lattice IS a spherically compressed hypercube, planetary magnetosphere IS a spherically compressed torus.

Load-bearing question: is "spherical compression" a real project-canonical operator that, when made explicit, tightens the srmech-collection geometric vocabulary — or is it pattern-match without substance?

Math-doesn't-lie discipline: verify against actual project HDC implementations and project geometric usage; don't paper over differences.

## Verdict — one-line summary

The user's framing is **correct as stated for ONE specific project locus** (MFO Phase C bipolar BIP at D=512) and **partially-correct via a different mathematical mechanism for another** (chess-spectral qm_2d / qm_4d quantum-state projective Hilbert sphere). The **broader claim that "spherical compression" is the project's universal natural ambient geometry needs refinement**: the project's HDC architecture is **plural** (three distinct flavours), and the "spherically compressed torus" magnetospheric phrasing names a different mathematical mechanism than the "spherically compressed hypercube" HDC phrasing despite the natural-language parallel.

Vocabulary-tightening prediction is **weak**: the existing §3.5 cross-manifold table is correct as-is, and adoption of "spherical compression" as a universal operator would not improve clarity. **Per-locus value: real.** Universal-operator value: marginal.

## Sub-investigation 1 — Formalise the HDC-hypervector = spherically-compressed-hypercube claim

**Verdict: PROJECT HDC IS PLURAL; user's framing applies to one flavour, not all.**

Three distinct HDC architectures coexist in the project:

| Flavour | Substrate | Bind operation | Similarity metric | Spherical compression applies? |
|---|---|---|---|---|
| **MFO Phase C bipolar BIP** | {-1,+1}^D (vertices of hypercube) | element-wise multiplication | cos(a,b) = <a,b>/D | **YES** — bipolar vertices inscribe S^(D-1) at radius √D; cosine sim IS inner product on the sphere |
| **Ephemerides BIP / SkPhase9BIP** | (Z_{2^K})^D = flat torus T^D | modular phase addition mod 2^K | unit-norm lift to S^(2D-1) post-superposition | **PARTIALLY** — base substrate is T^D not S^(D-1); the inscribed-sphere structure appears at the POST-superposition normalization step, not in the base lattice |
| **Chess-spectral production encoder** | float-valued signed magnitudes in R^640 | spectral channel projection + value lookup | cosine similarity in R^640 | **NO** — substrate is R^640 directly; no hypercube or torus structure to compress |

**Evidence:**
- **MFO Phase C** ([mpm_phase_c_script.py line 137](../research-mfo/mpm_phase_c_script.py)): `rng.choice([-1, 1], size=D)` for each of 5 QN-axis bases at D=512. Bind via `h_color * h_T3 * h_Y * h_gen`. Cosine equals dot-product divided by D. **The user's framing maps cleanly here:** vertices of {-1,+1}^512 are 2^512 points; all live at distance √512 from origin; their pairwise inner-product geometry is identical to angular geometry on the inscribed S^511. Plate-style HRR is canonically a "hypercube vertices inscribe a sphere" construction.
- **Ephemerides BIP** ([bip_hd_lift.py](../research/bip_hd_lift.py) + [resonant_bit_serialized_hdc_evaluation.md](../research/resonant_bit_serialized_hdc_evaluation.md) §2): state vector H ∈ (Z_{2^K})^D where K=16 or 32 and D=65536. Each component is a phase residue (point on S^1). The full vector lives on T^D (flat torus, NOT hypercube). Bind is `(φ_1 + φ_2) mod 2^K` — modular addition, not element-wise sign multiplication. After superposition of multiple body contributions and unit-norm normalization (`state /= np.linalg.norm(state)` at line 138-139), the state lifts to S^(2D-1) ⊂ C^D. The inscribed-sphere structure is real but APPLIED post-superposition, not as a base-substrate property.
- **Chess-spectral production encoder** ([chess_spectral_research_notebook.md line 3321](../../chess-maths/chess_spectral_research_notebook.md)): explicit "§3 / §9 float32 encoder — outputs the 640-dim signed magnitudes. **Not BIP.**" Random bipolar {-1,+1}^512 was used as the ORIGINAL baseline (§1486) and explicitly demoted in favour of spectral impulse-response coordinates (§1494). The production encoder works in R^640 with cosine similarity; there is no hypercube-or-sphere substrate to project.

**Refined formal claim that survives:**
- **MFO Phase C bipolar BIP** at D=512: vertices of {±1}^D inscribe S^(D-1) at radius √D; bind via element-wise multiplication; cosine similarity equals the standard angular distance on the inscribed sphere up to monotonic rescaling. This IS literal hypercube-to-sphere compression, and is canonical in HDC literature (Plate 2003 HRR, Kanerva's binary spatter codes).
- **Ephemerides BIP / SkPhase9BIP**: substrate is T^D not S^(D-1); inscribed-sphere structure appears after the lift-and-normalize step, not as a base property. Closer to "torus phase residues, then projective embedding onto complex hypersphere" than to "hypercube vertices inscribing sphere."
- **Chess production encoder**: float-valued; spherical-compression vocabulary does not apply.

**Literature check:** "Hypercube vertices inscribe sphere" framing is implicit in classical HRR / binary-spatter-code literature (Plate 2003, Kanerva 2009) but is not consistently named as "spherical compression" of the hypercube. The phrase "spherical compression" is the **user's own coinage**; it does correctly name the operation for the MFO Phase C case. **Not a published HDC term to cite — a candidate project-canonical neologism for the MFO Phase C locus specifically.**

## Sub-investigation 2 — §3.5 cross-manifold table — sixth row or S²-row generalization?

**Verdict: Option C (neither) at first reading, with optional §3.5.1 sub-section if conductor wants to surface the per-locus insight formally.**

Considered three options:
- **A — sixth row "spherically-compressed-X":** would duplicate existing rows (sphere S², flat torus T², general graph) under a different name. The substrate manifold of MFO Phase C bipolar BIP is the hypercube — which is NOT in §3.5 currently, but adding it as a new row would introduce inconsistency: HDC substrates aren't natively in §3.5, which catalogs ambient manifolds for the Laplace-Beltrami spectral framework. Mixing similarity-metric substrates with PDE-eigenbasis substrates would muddy the table.
- **B — generalize S² row to "manifolds whose ambient geometry is governed by an inscribed sphere":** would expand S² beyond its current sense (sphere as the manifold of spherical harmonics). The HDC similarity case is fundamentally different — the inscribed sphere isn't WHERE the PDE eigenbasis lives; it's where the similarity metric is computed. Conflating these would weaken §3.5's clarity.
- **C — neither; keep §3.5 as-is:** the existing rows correctly describe ambient manifolds for the project's Laplace-Beltrami spectral framework. The user's insight about HDC similarity living on inscribed spheres is real but operates at a DIFFERENT layer than §3.5: it's about similarity-metric topology, not eigenbasis topology. Adding it to §3.5 would mix layers.

**Optional path (§3.5.1 cross-reference subsection):** if the user's insight should be preserved in the formal project record, a small **§3.5.1 "Inscribed-sphere geometry of HDC similarity metrics"** subsection in srmech could note that the §3.5 table describes substrate manifolds for the Laplace-Beltrami spectral framework, while HDC similarity metrics (cosine in chess float encoder; Born-rule |<ψ|σ>| in chess qm_2d/qm_4d; bipolar inner-product/D in MFO Phase C) operate on INSCRIBED unit spheres of those substrates after norm-normalization. This is a one-paragraph addition; it surfaces the user's insight without restructuring §3.5.

**Fermata 1:** conductor decides whether §3.5.1 is worth adding, whether a cross-reference comment in chess qm_2d/qm_4d is sufficient, or whether the finding lives only in memory + this report.

## Sub-investigation 3 — Survey other project instances

**Surveyed candidates: 4 confirmed (1 added mid-flight by user), 2 absent.**

| Candidate | Present in project? | Locus | Verdict |
|---|---|---|---|
| **E_8 / Leech lattice / sphere packing** | NO | — | Absent; not project vocabulary. Future-scope candidate, not unification opportunity. |
| **Quantum-state-space CP^(2^n-1) reduction** | YES (different N) | chess qm_2d (CP^639), chess qm_4d (CP^45055) | Present, but dimensions are NOT 2^n; they come from spectral channel decomposition × board-cell count, not from n-qubit tensor products. Born-rule projective measurement lifts onto inscribed unit S^(2N-1). **This IS a real second locus of spherical compression in the project**, mathematically parallel to MFO Phase C bipolar BIP (both project onto inscribed sphere of substrate) but with different substrate (complex Hilbert C^N rather than real hypercube R^N). |
| **Cosmological-shell density (CMB, large-scale structure)** | NO | — | Absent; not project vocabulary. Future-scope candidate. |
| **T² L-shell magnetosphere** (raised by user) | YES | T² survey, ephemerides | Present but DIFFERENT mathematical mechanism: physical solar-wind pressure compression (dayside) + magnetotail elongation (nightside) — asymmetric pressure-driven deformation of dipole foliation, NOT inscribed-sphere construction. Phrasing parallels but mechanism diverges. |
| **Event horizons / black holes** (raised by user mid-flight) | YES | MFO §VII.4.1, §VIII.1; ephemerides §14 holographic principle (task #91) | **STRONGEST per-locus win.** MFO §VII.4.1 explicit: "the black hole ends at the horizon. There is no interior. The event horizon is the 2D phase boundary between matter bound in 3D space and information bound to a 2D surface — the dimensional reduction is real." MFO §VIII.1 names event horizons as "2D surfaces where spectral dimension transitions sharply." Ephemerides §14 ports the holographic principle to macro scale. The user's spherical-compression vocabulary names what MFO §VII.4.1 commits to but does not currently have a name for: 3D bulk → inscribed 2D sphere (Birkhoff makes static horizon round; Kerr rotation makes it oblate — **direct parallel to Saturn J₂ rotational compression** documented in T² survey). |

**User's mid-flight question — answered:** *"is this the math for why it's round?"* No. GR (Birkhoff's theorem for static + no-hair theorem for stationary) imposes roundness on Schwarzschild horizons independently. The user's "spherical compression" is the **project-canonical vocabulary FOR the 2D-boundary-from-3D-bulk phenomenon** that GR independently makes round in the static case and oblate-via-rotation in the Kerr case. Same mechanism family as Saturn J₂ rotational compression (T² survey) — rotation breaks pure sphericity in BOTH the magnetospheric case AND the black-hole horizon case.

**Anomaly: "spherical compression" is two different mathematical operations under one English phrase.**

- **HDC bipolar / quantum-state projective**: substrate is hypercube {±1}^D or Hilbert C^N; inscribed-sphere structure is induced by the norm-normalization (mathematical/induced-metric construction). Symmetric, well-defined.
- **Magnetospheric L-shell torus**: substrate is dipole-field-line foliation; compression is asymmetric pressure-driven (solar wind dayside, vacuum nightside). Physical, not induced-metric.

The natural-language phrase "spherical compression" covers both cases correctly, but no single mathematical operator does. Conductor-level decision (fermata 2): canonicalize the user's phrasing while distinguishing the two mechanisms in formal writeups, or keep "spherical compression" informal and avoid technical conflation.

## Sub-investigation 4 — Vocabulary-tightening test

**Test passages and verdicts:**

**Test 1 — srmech §3.5 row 1 (Euclidean grid + Neumann BC).**

Current text: *"DCT-II/III, λ_k = 2(1−cos πk_x/W) + 2(1−cos πk_y/H), Inkscape / Skia / GEGL/GIMP graphics-domain kernels."*

With spherical-compression operator explicit: *"DCT-II/III on the inscribed-sphere image of the unit-square lattice with Neumann BC; eigenbasis cosine modes; ..."* — **adds noise, no information gain.** The Neumann lattice isn't naturally a hypercube-compressed-onto-sphere. **Verdict: no improvement.**

**Test 2 — MFO Phase C bipolar BIP description.**

Current text (from mfo_mpm_notes.ndjson and Phase C findings): *"D=512 bipolar Phase-N BIP; coprime-roll cyclic shifts; element-wise multiplication bind; cosine similarity argmax assignment."*

With spherical-compression explicit: *"Hypercube vertices {-1,+1}^512 inscribe S^511 at radius √512; bind by element-wise multiplication (HRR / binary-spatter codes; closed under hypercube vertex set); cosine similarity is angular distance on inscribed sphere; argmax assignment per fermion."* — **adds real information.** Names the substrate manifold cleanly; surfaces what the similarity metric is actually measuring (angle on the inscribed sphere); makes connection to Plate / Kanerva literature explicit. **Verdict: real improvement.**

**Test 3 — chess qm_2d module docstring.**

Current text (qm_2d.py line 5): *"Wraps the existing 640-dim float32 encoder output as a quantum state psi in C^640, exposes Hermitian piece-reach observables ..."*

With spherical-compression explicit: *"Normalizes 640-dim float32 encoder output to inscribed unit S^1279 ⊂ R^1280 = C^640; physical state lives in projective Hilbert space CP^639 (rays not vectors); Born-rule |<ψ|σ>| computes inner products on the inscribed sphere; D_4 unitary group action preserves the sphere."* — **adds real information.** Surfaces parallel to MFO Phase C (both project onto inscribed sphere of substrate); names the Born-rule machinery in geometric terms. **Verdict: real improvement.**

**Test 4 — ephemerides-spectral §1.4 (multi-vocabulary breathing Laplacian).**

§1.4 already names four vocabularies (state-dependent Laplacian / adaptive Kuramoto / Ricci-in-motion / parametric coupling). Adding "spherical-compression / inscribed-sphere ambient geometry" as a fifth vocabulary: **incremental, not unifying.** §1.4's framing is about the Laplacian's STATE dependence, not its ambient geometry. The inscribed-sphere geometry would belong in a different section if added. **Verdict: low-value; do not add to §1.4.**

**Aggregate verdict on tightening prediction:** **PARTIAL CONFIRMATION.** Tightening works for HDC-similarity-metric loci (MFO Phase C, chess qm_2d/qm_4d) — two real per-locus wins. Does NOT work as a §3.5-wide unification or as fifth vocabulary in §1.4. The user's framing IS load-bearing as an MPM observation about HDC similarity-metric topology, but is NOT a universal project-canonical operator across the §3.5 cross-manifold framework.

## Anomaly log

1. **Project HDC is plural (3 flavours), not single.** Dispatch brief assumed "HDC bit-serialized hypervector lattice" applied universally; finding is that the project has bipolar {±1}^D (MFO Phase C), torus T^D (ephemerides BIP, SkPhase9BIP), and float-valued R^640 (chess production) flavours. Investigated and surfaced; not in dispatch brief.

2. **"Spherical compression" names two distinct mathematical operations.** HDC bipolar inscribed-sphere = induced-metric construction; magnetospheric L-shell = physical asymmetric pressure deformation. Same English phrase, different mechanisms. Both correct in their loci; no unifying mathematical operator.

3. **Quantum-state-space CP^(2^n-1) is in project at non-2^n dimensions.** Chess qm_2d uses CP^639, qm_4d uses CP^45055 — both come from spectral-channel × board-cell decomposition, not from n-qubit tensor products. Worth documenting that the project's projective-Hilbert constructions are board-spectral-derived, not qubit-derived.

## Fermata records (decision points for conductor)

1. **§3.5.1 placement** (sub-investigation 2): add subsection in srmech, add cross-reference in chess qm_2d/qm_4d, both, or neither?
2. **"Spherical compression" terminology canonicalization** (anomaly 2): canonicalize the user's natural-language phrase while distinguishing two mechanisms in formal writeups, or keep informal and avoid technical conflation?
3. **HDC-plurality documentation** (anomaly 1): does the project's project-canonical work in srmech §3 and ephemerides §22 already adequately treat HDC as "cyclic-group representation across multiple cyclic groups (Z_2, Z_{2^K})"? Or should the float-encoder chess path be explicitly distinguished from the BIP/bipolar paths in the formal record?
4. **Event-horizon → spherical-compression naming in MFO §VII.4.1 / §VIII.1** (sub-investigation 3 extension): 1-2 sentence addition naming "spherical compression" as the operation that takes 3D bulk to MFO §VII.4.1's "2D phase boundary" — with rotational oblateness (Kerr horizon) as the standard deviation, paralleling Saturn J₂ rotational compression from T² survey. This is arguably **higher value** than fermata 1 because event horizons are an existing committed-stance with a vocabulary gap the user's framing precisely fills.

## Recommended next actions

For conductor consideration:

- **(low-effort)** Capture user's framing in a memory file (e.g., `user_stance_spherical_compression_ambient_geometry.md`) so it propagates into future project work even if no notebook edits land.
- **(medium-effort)** Add 1-paragraph srmech §3.5.1 cross-reference subsection if conductor wants the formal record updated.
- **(medium-effort)** Add cross-reference comment in chess qm_2d.py module docstring naming MFO Phase C parallel.
- **(higher-effort)** Document the three HDC flavours explicitly in srmech §3 (project's HDC architecture is plural, not single; the cyclic-group-representation framing already partially unifies but the float-encoder chess path is distinct).
- **(scope expansion, not unification)** If user wants project to incorporate E_8/Leech-sphere-packing or cosmological-shell-density as new domains, those would be additive scoping work, not unification of existing material.

## What stands and what falls

**Stands:**
- The user's "spherically compressed hypercube" phrasing for **MFO Phase C bipolar BIP** is mathematically correct and a candidate project-canonical neologism for that specific locus.
- The user's "spherically compressed torus" phrasing for **planetary magnetosphere** is geometrically apt for the physical asymmetric-compression mechanism.
- The user's "spherically compressed thing" framing for **event-horizon 2D-boundary-from-3D-bulk** lands cleanly, fills a vocabulary gap in MFO §VII.4.1, and integrates with the holographic-principle commitment in MFO §VII.4.1 + §VIII.1 + ephemerides §14.
- **All three** are legitimate Feynman-test compressions of technical content per user_explanation_discipline.md.
- The project ALREADY has TWO real induced-metric inscribed-sphere constructions in HDC code (MFO Phase C bipolar BIP; chess qm_2d/qm_4d projective Hilbert state), PLUS the physical-asymmetric-compression magnetospheric instance, PLUS the GR-imposed event-horizon instance — four distinct project loci where 3D-or-higher bulk reduces to inscribed-sphere or oblate-sphere boundary.
- Three §3.5 T² instantiations (audio periodic loops, protein Ramachandran, planetary magnetospheric L-shell) confirm T² row is well-populated post-T²-survey.
- The **rotational-compression mechanism is cross-cutting**: Saturn J₂ (gravity), Kerr black-hole horizon (GR), ice-giant magnetospheric oblateness (T²-survey) all share the family "rotation breaks pure sphericity." Worth noting as a project-cross-cutting motif.

**Falls:**
- The claim that "spherical compression is the project's universal natural ambient geometry, not flat Euclidean" — too strong. The project's HDC is plural; the §3.5 framework correctly catalogs multiple ambient manifolds (Euclidean grid, sphere S², flat torus T², triangle mesh, general graph), each in active use; no single ambient geometry is universal.
- The claim that the user's framing tightens the §3.5 vocabulary universally — not supported. Tightens at TWO per-locus points; does not unify §3.5.
- The premise that "HDC bit-serialized hypervector lattice" universally describes the project's HDC — partially incorrect; applies cleanly to MFO Phase C bipolar BIP, partially to ephemerides BIP post-superposition, not at all to chess production float encoder.

## What's open

- **Per-locus wins are real**: MFO Phase C and chess qm_2d/qm_4d gain clarity from "inscribed-sphere ambient geometry" framing.
- **Universal operator is not real**: §3.5 is correctly structured as-is; no proliferation justified.
- **Asymmetric pressure-compression** (magnetosphere) and **induced-metric inscribed-sphere** (HDC) share the user's English phrase but not the underlying mathematics; conductor decides whether to canonicalize the phrase across distinct mechanisms.

The finding gives the user real signal: the framing IS load-bearing for two specific project loci, while NOT being the universal ambient geometry of the project. That's honest data, not papered-over disagreement.
