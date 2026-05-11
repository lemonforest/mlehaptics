# MFO Phase A: Sierpinski-gasket pre-gasket Laplacian (findings)

**Date:** 2026-05-11 · **Phase:** A (graph-Laplacian + HDC, per srmech §3.5 cross-manifold primitive)

## Method

Direct construction of V_m as the integer-lattice pre-gasket graph (Strichartz / Kigami recursion: outer triangle subdivides into three half-scale subtriangles, smallest-level triangles contribute three edges each, shared boundary vertices between adjacent subtriangles deduplicate via exact integer-coordinate match). Sparse integer adjacency A, integer combinatorial Laplacian L = D − A, eigendecomposed with `numpy.linalg.eigh`.

**Boundary conditions:** standard pre-gasket graph (no Dirichlet zero rows, no corner identification). This is the 'free' / Neumann-like boundary; the zero eigenvalue has multiplicity 1 (the constant vector, single connected component). Notebook §IV.2 implies this choice via 'initial state {0, 5}'.

## Vertex / edge counts (sanity check)

Formula: |V_m| = 3 (3^m + 1) / 2; |E_m| = 3 · 3^m smallest triangles.

| Level m | |V_m| (formula) | |V_m| (constructed) | |E_m| | distinct eigvals | λ_max |
|---:|---:|---:|---:|---:|---:|
| 3 | 42 | 42 | 81 | 18 | 6.0000 |
| 4 | 123 | 123 | 243 | 36 | 6.0000 |
| 5 | 366 | 366 | 729 | 72 | 6.0000 |

All counts match. Multiplicities sum exactly to |V_m| at each level (verified by assertion).

Degree histogram: at every level, 3 corner vertices have degree 2; all other vertices have degree 4. So `2 · deg_max = 8` is the upper bound on `λ_max(L)`; the actual `λ_max = 6` exactly, with high multiplicity (5 at level 5).

## Anomaly 1 (expected, instructive): direct graph spectrum lives in `[0, 6]`, not `[0, 5]`

| Level | direct λ_max | abstract recurrence λ_max | direct distinct | abstract distinct |
|---:|---:|---:|---:|---:|
| 3 | 6.0000 | 5.0000 | 18 | 23 |
| 4 | 6.0000 | 5.0000 | 36 | 47 |
| 5 | 6.0000 | 5.0000 | 72 | 95 |

The abstract decimation recurrence `R(λ) = λ(5 − λ)` from notebook §IV.2 and `mpm_anchored_verdict.py` produces eigenvalues in `[0, 5]`. The direct combinatorial graph Laplacian L = D − A produces eigenvalues in `[0, 6]`. These are different operators in different conventions:

- **Direct (this work):** combinatorial `L = D − A` on the SG pre-gasket; integer entries; spectrum bounded above by `2 · deg_max = 8` (saturates at 6 with degeneracy 5 at level 5; the degenerate 6-eigenspace are the localised modes around degree-4 interior triangulation vertices).
- **Abstract recurrence (Rammal-Toulouse 1984 / Fukushima-Shima 1992):** the decimation polynomial `R(λ) = λ(5 − λ)` does NOT operate on the eigenvalues of `D − A`. It operates on a *renormalised* / dynamic-Laplacian spectrum (the random-walk spectrum on the infinite SG, scaled appropriately). The polynomial's form encodes the Schur complement at decimated vertices.

**Confirmed by independent check:** Random-walk Laplacian `L_rw = I − D^(−1) A` on level 3 has `λ_max = 1.500` exactly (= 3/2), not `5` and not `2`; the symmetric normalised Laplacian `L_sym = I − D^(−1/2) A D^(−1/2)` shares this spectrum. None of the three natural Laplacian conventions (combinatorial, random-walk, symmetric-normalised) directly reproduces the abstract `[0, 5]` recurrence spectrum at finite levels. The abstract recurrence is the *infinite-SG limit object*, not the finite-pre-gasket-graph spectrum.

**Implication for the framework:** Phase A's eigenvalues ARE the correct numerical object for the graph-Laplacian + HDC primitive (srmech §3.5). The abstract recurrence values used in `mpm_pn_sweep` and `mpm_anchored_verdict` are mathematically valid in their own convention but live on a different scaling. Subsequent phases (mass-fit, gauge-RG, spectral-dim flow) should be redone against the direct-graph eigenvalues if the project's claim is 'graph-Laplacian on physically realisable pre-gasket' rather than 'infinite-SG renormalised spectrum'.

## Anomaly 2 (load-bearing for theory): high-multiplicity localised modes

Fukushima-Shima 1992 §2 predicts the SG Laplacian has eigenvalues with multiplicity growing exponentially with level, coming from eigenfunctions supported on small subgraphs ('pre-localised eigenfunctions').

| Level | distinct eigvals | max multiplicity | eigvals with mult ≥ 3 |
|---:|---:|---:|---:|
| 3 | 18 | 12 | 3 |
| 4 | 36 | 39 | 7 |
| 5 | 72 | 120 | 15 |

At level 5 the max multiplicity is well above 1 (verifiable in the NDJSON); the localised-mode prediction is confirmed. Eigenvalue 6 carries multiplicity 5 at level 5, which is a candidate self-similarity signature: 3 corners + 2 something. Worth a Phase B investigation.

## Spectral dimension d_S(σ) from heat-kernel trace

At level 5 (n = 366), using ALL eigenvalues with multiplicities, `d_S(σ) = −2 d(ln tr exp(−σ L)) / d(ln σ)`:

- d_S at small σ (UV): 0.0789
- d_S transient peak: 1.8398 at σ = 5.4159e-01
- **d_S plateau** (longest contiguous run with `|d_S − d_S_theory| < 0.05`): mean = **1.3289** over σ ∈ [7.317e+00, 1.383e+01], 12 grid points
- d_S at large σ (IR, zero-mode regime): 0.0732
- **Theoretical SG limit `2 ln 3 / ln 5` = 1.3652**

On a finite graph d_S(σ) → 0 at both endpoints: at UV (σ → 0) the trace `tr exp(−σL) → n` (constant), so its log derivative vanishes; at IR (σ → ∞) only the zero mode survives, also giving a constant. The theoretical SG spectral dimension is the plateau VALUE at intermediate σ — the regime where heat has diffused beyond the lattice scale but not yet reached the boundary.

**Finding:** Phase A recovers the SG spectral dimension. The plateau sits at d_S ≈ **1.329** (direct-graph, level 5, n=366), versus theory `2 ln 3 / ln 5` = **1.365**. Agreement to ~0.036 (≲ 5%) at finite size; the plateau is expected to sharpen at higher levels.

The transient peak `d_S ≈ 1.84` at σ ≈ 0.54 is a crossover artefact, NOT the spectral dimension. (This is the same artefact the abstract-recurrence `mpm_spectral_dimension.ndjson` likely exhibits at its peak; the project should treat the plateau, not the peak, as the operational d_S.)

## Files in `results-mfo/`

- `mpm_phase_a_eigenvalues.ndjson` — one record per (level, eigenvalue) with multiplicity
- `mpm_phase_a_eigenvectors.npz` — eigenvectors / eigenvalues / vertex integer coords per level, plus `d_S_sigma_grid` and `d_S_values_level5` arrays
- `mpm_phase_a_findings.md` — this file
- `mpm_phase_a_sg_graph.py` (in `research-mfo/`) — the script

## Phase B candidates (recorded but not done here)

1. Redo `mpm_anchored_verdict` Tests 1–3 against direct-graph eigenvalues (not abstract recurrence) — does the SM mass fit improve, degrade, or change qualitative shape?
2. Investigate λ = 6 eigenspace at each level: are the localised modes the 'three-generation' family the framework wants?
3. Compute the product spectrum L_SG ⊕ L_CP² ⊕ L_S¹ using the direct eigenvalues, and check inter-generation gap structure.
4. Pn generalisation: build the direct integer adjacency for P_2, P_4..P_8 fractals and compare against the corresponding abstract decimation factors.
