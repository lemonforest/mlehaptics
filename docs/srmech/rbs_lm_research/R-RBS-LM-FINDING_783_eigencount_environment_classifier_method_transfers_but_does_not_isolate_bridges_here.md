# F783 — the cosmic-web eigenvalue-COUNT environment classifier (F781's proposed reading-tool) BUILT + RUN: the reading method transfers and is Class-L-native, but on the 32-word dense seed graph it does NOT cleanly isolate the F780 bridges (honest partial/null). The real gradient it surfaces is inverted from the naive guess.

**Date:** 2026-06-16 · **srmech:** 0.7.5rc165 · **Composes / TESTS:** F781 (the proposed eigen-count environment classifier — this is its empirical test; the prediction "bridges = filaments" is NOT cleanly borne out → F781's reading-tool section caveated), F780 (the bridges it tried to isolate), F779 (same demo graph) · **Discipline:** `[[feedback_dont_pre_commit_spike_query_operators]]` (null findings count; don't lean toward the expected result — the script's first "CONFIRMED" was a too-lenient test, corrected) · **Provenance:** `R-RBS-LM-WEBENV_eigencount_environment_classifier_void_sheet_filament_knot.py` · **User direction (2026-06-16):** "build that eigenvalue-count environment classifier on the demo graph next."

## What was built (exactly F781's proposal, Class-L-native)
1. co-occurrence graph over the 4-topic seed vocab (F779; 12k articles, 383 edges).
2. **spectral embedding** into ℝ³ — the 3 smallest non-trivial Laplacian eigenvectors (`symmetric_eigendecompose`) → each word a coordinate in "knowledge space" (the 4 topics → 4 clusters).
3. **local structure tensor** at each word: M_w = Σ_neighbours w·(x_j−x_w)(x_j−x_w)ᵀ (3×3).
4. **eigen-COUNT** of M_w (`jacobi_eigvals`, trace-normalised): # axes ≥ τ (the literal cosmology read) + participation ratio PR=1/Σλ² (effective dimension, magic-number-free) → **void / sheet / filament / knot**. (Class-K `cascade.magnitude`, no `abs()`.)

## What it shows — honestly
**The reading METHOD transfers (the F781 claim that matters):** every word gets a void/sheet/filament/knot environment from its local structure-tensor eigenvalues, Class-L throughout — the cosmology eigen-count read is mechanically portable to the knowledge graph. ✓

**But the specific F781 PREDICTION ("the F780 bridges read as a distinct low-dimensional / filament class") is NOT confirmed:**
- bridge words `singer`/`star` → filament, `song` → sheet (low-dim, yes) — **but so are many topically-PURE words** (`melody`/`concert`/`lion` are the *most extreme* filaments, PR≈1.03).
- bridge mean PR **1.52** vs core mean PR **1.54** → **gap +0.02, negligible against the core spread 1.03–2.92.** Bridges are **not** a distinct class on this graph. (A too-lenient `pr_br<pr_core` test first printed "CONFIRMED"; corrected to the margin-vs-spread test → NOT confirmed.)

**The real gradient is inverted from the naive guess:** the **isotropic KNOTS (3D)** are the most *generic / broadly-connected* words (`vegetable`, `species` — they point toward all clusters ~evenly), and the **filaments (1D)** are the *topically-concentrated* words (one dominant neighbour-direction). So on this graph the structure tensor reads **global 4-cluster geometry**, not **local bridge-role** — a real and sensible signal, just not the bridge-detector F781 hoped for.

## Why (the mechanism)
The 3D embedding is dominated by the 4-cluster separation (embedding eigenvalues 92/141/222). A word's neighbours are mostly its own tight cluster (≈one point) + a few cross-edges; for almost every word that yields ONE dominant displacement axis → filament. The bridge's "points toward 2 clusters" signal is not geometrically distinct from a pure word's "points toward its 1 nearest cluster" at this scale/density. The F780 3.1× within/cross density is real but too shallow a contrast for the structure tensor to flag bridges in 3D.

## Honest next test (queued #224)
- **(a) the COMPONENT-COUNT variant** — the *nullity* of the neighbour-subgraph Laplacian (multiplicity of eigenvalue 0 = # connected components among a word's neighbours = # distinct communities it touches). This is the textbook eigen-count structural reader and a **more direct bridge-detector** (a true bridge's neighbours split into ≥2 components); needs an edge-threshold to de-densify the seed clique.
- **(b) a larger / sparser real vocab** where bridges aren't swamped by a near-complete 32-word seed clique.
The method transfers; the **bridge=filament mapping needs the right operator (component-count) + the right scale.**

## Honest scope
- Partial / mostly-null result, reported as-is (no leaning). The transferable *method* is the positive; the *bridge-isolation prediction* is the negative.
- srmech-native Class-L (`symmetric_eigendecompose`/`jacobi_eigvals`/`dense_laplacian`) + Class-K `magnitude`; no numpy, no `abs()`, no CAD; data outside the repo; CC-BY-SA.
- τ=0.20 is an illustrative/swept operating point (PR is the threshold-free corroborator), not a tuned magic number.

## Verdict
F781's proposed eigen-count environment classifier is **built and run**: the cosmology void/sheet/filament/knot reading **transfers and is Class-L-native** (the method works), but on the 32-word dense seed graph it **does not isolate the F780 bridges** (bridge–core PR gap +0.02, within noise) — the structure tensor reads global cluster geometry, with the *generic* words as isotropic knots and *topically-pure* words as filaments (inverted from the naive guess). The honest next step is the **component-count variant** (neighbour-subgraph Laplacian nullity = communities-touched) on a sparser/larger vocab — the more direct bridge-detector. The reading language transfers; the bridge-detector needs the right operator + scale. (F781 reading-tool section caveated accordingly.)
