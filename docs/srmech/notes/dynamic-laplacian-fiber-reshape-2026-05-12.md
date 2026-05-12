# Dynamic Laplacian via fiber-driven edge weights — FALSIFIED (2026-05-12)

**Origin**: user question following PR #334 merge: *"Now that we can draw our hypervector as voxels, does that mean we could also use fiber content to 'reshape' voxels for dynamic graph-laplacian things?"*

**Pre-flighted as**: "might yield nothing." Falsification spike.

**Headline verdict**: **FALSIFIED at natural voxelization parameters.** The dynamic Laplacian via fiber phase coherence is vacuous for the protein-bipartition use case because the voxelization step *itself* pre-encodes the bipartition into the voxel-grid topology — positive and negative Fiedler regions form geometrically-separated voxel blobs that don't share neighbors, so the dynamic Laplacian has nothing to discover. The "reshape" the user proposed has already happened in the encoding step.

Reproduce: `python -X utf8 docs/srmech/notes/dynamic_laplacian_fiber_reshape_script.py`. Runtime ~10s. Deterministic seed `20260512`.

---

## Setup

Voxel grid as base manifold; HDC phase per voxel as U(1) fiber. Dynamic edge weights:

$$w_{ij}(\psi) = \cos^2\left(\frac{\theta_i - \theta_j}{2}\right) = \frac{1 + \cos(\theta_i - \theta_j)}{2}$$

Same phase → strong edge (w=1); opposite phase → weak edge (w=0).

Iterative fixed-point loop:
1. Build dynamic weights from current phases
2. Compute Fiedler eigenvector of L(ψ)
3. Update phases from new Fiedler via tanh-smooth map → [0, π]
4. Sign-align Fiedler against *previous Fiedler* (not previous phases — avoids spurious sign-flip cycles)
5. Check convergence

**Test protein**: 1UBQ (ubiquitin, 76 Cα). Voxel grid 32³, σ=3.5Å, active threshold |field|>0.05.

---

## Diagnostic finding — the active voxel region is disconnected

Connectivity check on the 6-connected lattice over active voxels:

| Statistic | Value |
|---|---:|
| Total voxels (32³) | 32,768 |
| Active voxels (|field| > 0.05) | 4,621 |
| Edges in 6-connected active subgraph | 12,442 |
| **BFS reachable from voxel 0** | **2,532** |
| **Unreachable** | **2,089** |
| Phase positive (>π/2) count | 2,532 |
| Phase negative (<π/2) count | 2,089 |

**The numbers match exactly**: 2532 + 2089 = 4621 active voxels split into two BFS components matching the positive/negative phase bipartition counts. The Fiedler partition is **baked into the voxel topology** by the Gaussian-smear + threshold step itself.

Why this happens: with σ=3.5Å smear, the positive Fiedler region (β-strand cluster) and negative Fiedler region (α-helix cluster) form separated 3D blobs. The zero contour of the Fiedler eigenvector in real space passes through "low-density" voxels which fall below the |field|>0.05 threshold and are excluded. Result: two non-touching blobs in the active subgraph.

---

## Iteration results — trivial convergence in 2 steps

With sign-aligned Fiedler against previous iteration's Fiedler:

| Variant | Weight floor ε | Steps to convergence | Final ||Δphase|| | λ_Fiedler |
|---|---:|---:|---:|---:|
| A (naive) | 0.0 | 2 | 0.0006 | 0.0 |
| B (small floor) | 0.1 | 2 | 0.0001 | 0.0 |
| C (large floor) | 0.3 | 2 | 0.0001 | 0.0 |

**λ_Fiedler = 0 across all variants** because the active subgraph is disconnected → multiple zero eigenvalues in the kernel of L(ψ). The "Fiedler" eigenvector eigsh returns is just the indicator function of one component vs the other — exactly the initial bipartition. Trivially self-consistent. Nothing learned.

**All three variants behave identically** because edge weights don't matter when the graph topology is already disconnected: zero weights and floor=0.3 weights give the same disconnected-component structure.

---

## What was actually tested vs what we thought we were testing

| We thought | Reality |
|---|---|
| Dynamic Laplacian discovers self-consistent partition through iteration | Initial voxelization already separates the bipartition into geometric components |
| Fiber phase coherence reshapes the graph | Graph was already "reshaped" by Gaussian-smear + threshold |
| Need weight floor to keep graph connected | Active subgraph itself is disconnected; weights are irrelevant |
| Period-2 cycle from first run was dynamical | Period-2 cycle was sign-flip artifact in Fiedler eigsh on degenerate spectrum (fixed with sign-align to previous Fiedler) |

The **alignment-fix moved the outcome from "limit cycle" to "trivial fixed point in 2 steps."** Both diagnoses describe the same underlying issue — *the active voxel region is geometrically partitioned before the iteration starts.*

---

## What this falsifies

The naive form of *"use fiber content to reshape voxels for dynamic graph-Laplacian"* — i.e., compute fiber-derived edge weights and recompute Fiedler iteratively — is **vacuous for any voxelization where the Fiedler positive/negative regions don't share voxels**. This includes:

- Protein bipartitions at natural σ and threshold (PR #333 setup)
- Any sparsely-supported scalar field where positive and negative regions are geometrically separated
- Any HDC encoding where the encoded data IS the partition (sign-only encoding from PR #333)

The user's intuition was sound at the architectural level (fiber feedback to base is a real category) but the **specific instantiation** with naive phase-coherence weights on the protein bipartition is a degenerate case.

---

## What the falsification rules OUT for the catalog

- Sign-only encoded bipartitions on naturally-thresholded voxel grids will **never** support non-trivial dynamic-Laplacian iteration. The geometry has done the work the iteration was supposed to do.
- Don't add a "dynamic Fiedler-driven Laplacian" primitive to srmech §3.5.4 catalog. It's a vacuous operator at the bipartition level.

---

## What might still work — flagged but not tested here

To actually test the user's deeper intuition, one would need:

1. **Connected substrate**: lower threshold or full 32³ grid. The transition zone between positive and negative regions would then be in the graph, giving the iteration something to do. Predicted outcome: either a softened bipartition fixed point (with smooth zero contour) or a non-trivial sub-partition emerging within each region.

2. **Smoother phase function**: don't use tanh saturation. Linear `phase = π * (Fiedler − Fiedler_min) / (Fiedler_max − Fiedler_min)` keeps phase continuous and ambiguous in low-Fiedler regions where the iteration could find structure.

3. **Different weight functional**: `w_{ij} = α + β·cos((θ_i − θ_j)/2)` with α > 0 keeps the graph connected regardless of phase pattern. The α/β ratio is a "coupling strength" knob — α=1, β=0 gives static Laplacian; α=0, β=1 gives naive case; intermediate gives a real test.

4. **Non-bipartition test**: try the dynamic Laplacian on a non-bipartition field (e.g., the L₁ edge Fiedler from PR #333 Hodge spike, or a random scalar field) where the geometry doesn't pre-partition.

5. **Gauge-theoretic connection** (most ambitious): instead of edge weights, use the phase as a gauge connection — `(ψ_i, ψ_j) → ⟨ψ_i, U_{ij} ψ_j⟩` for some link variable U_{ij}. This is the discrete Wilson-line setup from lattice gauge theory; gives a complex Hermitian Laplacian whose spectrum captures *holonomy* not just *coherence*. Would be a genuinely different primitive.

None of these are this PR's scope. Falsifying the naive form is the load-bearing content here.

---

## Connection to architectural framework

**§4.2 substrate-vs-config split** (srmech notebook): state-dependent operators are substrate primitives (don't close under pure spectral form). The dynamic Laplacian was the project's first attempt at this category for a *graph* operator (graphics-domain Perona-Malik is the existing example). **This spike showed: even substrate primitives need to be non-degenerate to be interesting.** Adding "state-dependence" to an operator doesn't automatically buy you anything if the state already determines the geometry the operator computes against.

**PR #333 encoding lesson**: sign-only encoding matches sign-valued bipartition data → preserves partition cleanly. **This spike showed the corollary**: when encoding does its job *too well* (perfect bipartition preservation in geometry), there's nothing left for downstream operators to discover. Encoding is information-preserving; downstream processing requires information to be **non-redundant** at the substrate level for any new finding to emerge.

**MFO §VII.4.1.1** (PR #332 Hopf bundle): connection (= fiber feedback to base curvature) is the continuum analog of what the user proposed. The Hopf bundle's curvature is *non-zero* (Chern class 1) — that's what gives the Δ_{S³} = Δ_{S²} + fiber-harmonics decomposition real content. For our voxel substrate at natural parameters, the "curvature" is degenerate (graph disconnects) → no content. This spike instantiates the boundary case where the framework gives nothing.

---

## Honest summary

User asked an architecturally sound question; the specific instantiation we tested falsifies *for the natural protein-bipartition setup at PR #333 voxelization parameters*. Three weight-floor variants confirm: the issue is geometric (active-voxel-region disconnection), not numerical. The architectural slot remains live but needs a non-degenerate substrate.

**Falsified specifically**: naive cos²(Δθ/2) edge weights on Fiedler-bipartition-derived phases over standard PR #333 voxelization.

**Not falsified**: gauge-theoretic dynamic Laplacian, connected substrate variants, non-bipartition initial conditions. These are flagged as separable future spikes.

---

## Files

- `dynamic_laplacian_fiber_reshape_script.py` — three-variant spike (~10s)
- `dynamic-laplacian-fiber-reshape-per-step-2026-05-12.ndjson` — per-step + final outcomes
- `dynamic-laplacian-trajectory-2026-05-12.png` — convergence plot + phase-field snapshots

---

## Citations

- Perona-Malik 1990: anisotropic diffusion with state-dependent weights — the canonical substrate-primitive precedent
- Imrich-Klavžar: Cartesian product graph spectra (factor-sum identity used in PR #331)
- Bohigas-Giannoni-Schmit 1984 + Wigner-Dyson universality (PR #334 connection)
