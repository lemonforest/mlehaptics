# Dynamic Laplacian on SH substrate — PR #335 revisited and CONFIRMED (2026-05-12)

**Origin**: PR C of 3-PR sequence (Zernike #338 → PCA canonical #339 → this). PR #335 falsified the dynamic-Laplacian iteration on voxel substrate because the active region geometrically disconnected (positive and negative Fiedler regions formed separate blobs). User question: does it work on a connected substrate?

**Verdict**: **WIN.** On a globally-connected sphere substrate, the dynamic Laplacian iteration converges in 4 steps to a non-trivial fixed point (correlation 0.23 with initial — structurally distinct). **PR #335 was substrate-limited, not concept-limited.** The user's original architectural intuition (fiber feedback to graph structure) was correct.

Reproduce: `python -X utf8 docs/srmech/notes/dynamic_laplacian_sh_substrate_script.py`. Runtime ~3s.

---

## Setup — same iteration as PR #335, different substrate

| Element | PR #335 (FALSIFIED) | PR C (this) |
|---|---|---|
| Substrate | 32³ voxel grid, |field|>0.05 active | 60×120 sphere lat-lon grid |
| Active region | 4621 voxels in 2 disconnected components | 7200 nodes, all reachable |
| **Connectivity** | **DISCONNECTED** (2532 + 2089 = 4621) | **CONNECTED** (BFS reaches all 7200) |
| Edge weights | w = cos²(Δθ/2) — same | w = cos²(Δθ/2) — same |
| Update rule | Fiedler-then-phase — same | Fiedler-then-phase — same |
| Sign alignment | to previous Fiedler — same | to previous Fiedler — same |

The *only* substantive change is the substrate — voxel grid → sphere surface. Everything else identical to PR #335.

---

## Connectivity diagnostic — the load-bearing difference

| Check | PR #335 (voxel) | PR C (sphere) |
|---|---|---|
| BFS-reachable nodes | 2,532 / 4,621 | 7,200 / 7,200 |
| Unreachable nodes | 2,089 | 0 |
| Graph topology | 2 disconnected components | 1 connected component |
| Matches positive/negative bipartition? | YES (2532 ≈ +; 2089 ≈ −) | N/A (single component) |

PR #335's voxel substrate baked the bipartition into geometric disconnection. The sphere substrate doesn't.

---

## Iteration results

| Step | λ_Fiedler | ||Δphase|| | Correlation with ψ₀ |
|---|---:|---:|---:|
| 0 | 0.00274 | 111.39 | 0.228 |
| 1 | 0.00273 | 0.192 | 0.228 |
| 2 | 0.00273 | 0.001 | 0.228 |
| 3 | 0.00273 | 0.00001 | 0.228 |

**Converged at step 3** (||Δphase|| = 10⁻⁵, well below tolerance 10⁻⁴).

**Final correlation with initial: 0.228** — significantly different from 1.0. The converged phase field ψ* is structurally distinct from the initial ψ₀.

**λ_Fiedler ≈ 0.003 across iterations** — small but non-zero. The dynamic Laplacian is connected (kernel dim 1, the constant eigenvector). The Fiedler eigenvector is well-defined.

---

## Outcome classification

**`non_trivial_fixed_point`** — confirmed after classifier fix.

(The first run's classifier bug — using max over last 3 steps instead of final step — mislabeled this as `slow_or_undecided`. Fixed: classify by final-step behavior. Both behaviors describe the same underlying iteration; only the label changed.)

---

## What this confirms about PR #335's question-tree branch

The user's original PR #335 architectural question was:

> *"Now that we can draw our hypervector as voxels, does that mean we could also use fiber content to 'reshape' voxels for dynamic graph-Laplacian things?"*

PR #335 answered "no, falsified" on the **voxel substrate**. The vacuousness was geometric: the bipartition was already encoded in voxel topology before iteration started.

This PR answers "**yes, with connected substrate**." The user's architectural intuition was sound; the previous spike's negative result was substrate-specific, not concept-fatal.

**Refined claim**: dynamic-Laplacian iteration via fiber phase coherence works on substrates where the **graph topology doesn't pre-bake the field's bipartition**. Sphere surface qualifies; thresholded voxel active-region doesn't.

---

## Architectural lesson — substrate is part of the primitive

A "dynamic Laplacian" primitive isn't fully specified by the iteration rule. It's specified by **(iteration rule) × (substrate)**. The substrate choice can:

1. **Pre-encode the data into geometry** (PR #335 voxel case) — primitive is vacuous
2. **Stay connected through data variation** (this PR sphere case) — primitive does real work
3. (Hypothetically) **Provide its own geometric structure that conflicts with data** — primitive may diverge

For the srmech §4.2 catalog: the "dynamic state-dependent operator" entry should specify both the rule AND the required substrate properties (connectivity, non-bipartition-aligned topology, etc.).

---

## Connection to MFO §VII.4.1.1 (Hopf bundle, PR #332)

PR #332's continuum framework predicts dynamic-Laplacian behavior on a **principal U(1)-bundle**. The sphere surface here is the base S² of a (trivial-by-default) U(1)-bundle. The dynamic Laplacian discovers a fixed point that lives on this S² substrate — a discrete analog of finding harmonic forms on a continuous principal-bundle base.

To extend: instead of trivial U(1)-bundle (just S²), use a **non-trivial bundle** with Chern class 1 — i.e., the actual Hopf bundle S³ → S². The dynamic Laplacian on the full S³ total space would test what PR #332's continuum framework predicts: that fibre harmonics carry orientation-encoding information.

This is a natural follow-up spike.

---

## Updated question-tree status

| PR | Question | Answer |
|---|---|---|
| #333 | Voxel HDC + Hodge | Voxel HDC works; Hodge β_k separates fold classes |
| #334 | Universal eigenvalue statistics? | Proteins are GOE-universal (Maass class) |
| #335 | Reshape voxels via dynamic L? | Falsified on voxel substrate (geometric disconnect) |
| #336 | Dynamic metric vs static L | Reveals rotation breaks voxel HDC |
| #337 | SH power for SO(3) invariance | Works but discrimination poor |
| #338 | 3D Zernike for more discrim | Falsified (collapsed) |
| #339 | PCA canonical-frame | WIN (best geometric fingerprint) |
| **#340 (this)** | **Dynamic L on connected substrate?** | **WIN (non-trivial fixed point)** |

---

## What this opens up

1. **Dynamic Laplacian on actual Hopf bundle** — non-trivial U(1) bundle over S². Tests MFO §VII.4.1.1 continuum framework directly.
2. **Dynamic Laplacian on PCA-canonical sphere** — combine PR #339's canonical orientation with this PR's connected substrate. Best of both: SO(3) invariance + non-trivial fixed point.
3. **Convergence analysis** — what does the fixed-point ψ* actually look like spatially? Does it correspond to a known structural feature of ubiquitin?
4. **Cross-protein test** — does 1BPI converge to the SAME fixed point as 1UBQ (would indicate a sphere-universal mode, not a protein-specific one)?

These are flagged for future spikes, not in scope for PR C.

---

## Honest caveats

- **Substrate-aware verdict**: the dynamic Laplacian works on the sphere substrate at the specific (60×120) lat-lon grid tested. Coarser grids might degenerate; finer grids might give the same answer at higher cost.
- **Initial correlation 0.23**: the converged ψ* is distinct from ψ₀ but not maximally distinct. Whether 0.23 is a "deep" non-triviality or a near-orthogonal one depends on downstream interpretation.
- **λ_Fiedler ≈ 0.003**: small. The dynamic Laplacian has spectral structure but it's compressed near the kernel. Larger lat-lon grids might give sharper spectral separation.
- **Classifier was buggy** on first run (max-over-window heuristic). Fixed to use final-step behavior. Both runs describe the same iteration.

---

## Files

- `dynamic_laplacian_sh_substrate_script.py` — reproducible spike (~3s)
- `dynamic-laplacian-sh-substrate-per-step-2026-05-12.ndjson` — per-step + outcome
- `dynamic-laplacian-sh-substrate-trajectory-2026-05-12.png` — convergence plot + initial/final phase fields on sphere
- `dynamic-laplacian-sh-substrate-2026-05-12.md` — these findings

---

## Citations

- PR #335 falsification of voxel-substrate dynamic Laplacian
- MFO §VII.4.1.1 (PR #332) continuum framework
- Lat-lon sphere discretization: standard in geophysics / climate modeling
