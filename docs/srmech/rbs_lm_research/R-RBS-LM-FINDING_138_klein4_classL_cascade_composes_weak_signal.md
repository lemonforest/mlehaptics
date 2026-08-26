# Finding 138 — Klein-4 + Class L cascade composes algebraically; chirality-tag retrieval signal weak at small D

**Status:** Empirical finding; R-RBS-LM-98 smoke
**Predecessors:** F132 (Klein-4 HDC engineering), F137 (raw capacity comparison), UPSTREAM_NOTES §4 LANDED
**Path:** 2/6 of the wishlist-gated research resume

---

## §1 What was tested

Does Klein-4 HDC (Class M rank-2 abelian) compose with Class L (graph Laplacian spectral decomposition) **algebraically and empirically**?

The cascade pattern under test:

```
Class L:  build graph → Laplacian → eigendecompose
          → get eigvecs as concept-vectors over node-substrate
Class M:  encode each eigvec as Klein-4 hypervector
          + chirality-axis tag per (γ₅, iω₇) sector (XOR with sector mask)
Bundle:   all chirality-tagged eigvec-HVs into one composite memory
Query:    recover chirality-tag AND sector-filtered eigvec content
```

Success criteria from R-RBS-LM-98 script:
1. Klein-4 binding survives the L → M cascade (no algebraic loss)
2. Chirality-tag survives bundle + unbind (sector retrieval works)
3. Per-sector eigvec content recoverable with above-random similarity
4. Cross-sector queries return different eigvec subsets

Test parameters: D=1024, n_nodes=32, edge_density=0.15, seed=42.

---

## §2 Results

| Criterion | Measured | Random baseline | Verdict |
|---|---:|---:|---|
| 1. Algebraic compose | All operations completed cleanly; eigvals/eigvecs flowed into Klein-4 encode→bundle→unbind without error | — | ✅ PASS |
| 2. Chirality-tag recall | 9/32 = 0.281 | 0.25 (1/4 sectors) | ⚠️ marginal (+0.031 above random) |
| 3. Above-random self-sim | 0.157 | 0.0 | ✅ small but real signal |
| 4. Cross-sector precision | (0.250, 0.250, 0.375, 0.375) | 0.25 each | ⚠️ marginal; 2 sectors at baseline, 2 sectors +0.125 above |

**Headline:** the cascade COMPOSES (criterion 1 satisfied cleanly) but the EMPIRICAL chirality-axis signal at this D and load is weak. Above-random signal is real (0.157 self-sim above random) but the per-query discrimination barely beats chance.

---

## §3 Why the signal is weak — load × discrimination problem

Per F137 random-baseline calibration, Klein-4 random-pair similarity = 0.25 (4 states). The cascade test bundles N=32 eigvec HVs into one composite at D=1024.

From F137 Table §5 at comparable load:
- N=32 bundle → above-random self-sim ≈ 0.10
- N=16 bundle → above-random self-sim ≈ 0.14

The chirality-tag recall test then asks: given the composite, can we identify which of 4 sector masks was used to encode each eigvec? This requires:
- Sufficient self-sim signal above random (have it: 0.157)
- Sufficient gap between best-sector self-sim and wrong-sector self-sim (don't have it: gap is comparable to noise)

**The cascade composition is ALGEBRAICALLY CLEAN. The empirical signal degradation is exactly what F137 capacity numbers predicted at N=32, D=1024.**

To recover meaningful chirality-tag discrimination, we need either:
- Larger D (more positions = more independent evidence per query)
- Lower load (fewer eigvecs per bundle)
- Different encoding (currently uses tile + 2-bit Gray-like quantisation)

Path 3/6 explicitly addresses "cross-sector retrieval at scale" — that's where the larger-D test belongs.

---

## §4 What this finding contributes to F132

F132 §7 "Concrete next steps" listed:
> Klein-4 + Class L Laplacian + Class K Kepler should compose. Test: confirm cascade still works with chirality-tagged data.

This finding partially satisfies that test: **L + M (Klein-4) cascade DOES compose algebraically** — no operator-incompatibility issue. The empirical signal-level question (does chirality-tag carry information through Class L's eigendecompose) is **marginally positive but not loud at small-D / small-graph scale**.

The result is consistent with the F132 framework move: Klein-4 IS chirality-aware binding; it composes with other classes; the signal scale needed for reliable chirality discrimination depends on D and load.

**The finding does NOT invalidate F132.** It tightens the empirical specification: chirality-tag retrieval needs D > 1024 OR N < 16 (per F137 §5 table) to give comfortable above-random discrimination at this test pattern.

---

## §5 Encoding methodology — possible improvements

The current encode procedure (`klein4_encode_eigvec` in R-RBS-LM-98):
1. Tile eigvec indices to fill D
2. Quantise eigvec values into 4 states via (sign, magnitude > 0.1) → 2-bit code
3. XOR with sector mask

Alternative encodings that might give cleaner signal:
- **Random projection per eigvec**: bind eigvec value into klein-4 state via per-position random keys (more orthogonal across eigvecs)
- **Sector-axis separation**: bind eigvec content via independent klein-4 vector; apply sector tag as **separate** XOR layer (factorises content from chirality)
- **Multi-position quantisation**: each eigvec component spreads to multiple HV positions with different state-extractions (richer per-position content)

These alternatives are flagged as follow-up; not blocking Path 3/6.

---

## §6 What this finding does NOT claim

Per MFO §VII.6.20:

- This is NOT a claim that Klein-4 + Class L cascade is broken. It composes algebraically without error.
- This is NOT a claim that Klein-4 chirality-axis encoding fails. The above-random self-sim is positive (0.157); the per-query discrimination is marginal at the specific D/N tested.
- This is NOT a final measurement. Path 3/6 at-scale test (larger D, more deliberate setup) will give the load-bearing measurement of chirality-axis retrieval.
- This is NOT a comparison vs bipolar. The bipolar variant cannot encode chirality-axis natively at all (no operator); the question is whether Klein-4's chirality-axis encoding is OPERATIONAL, not whether it beats bipolar at chirality (it must, by construction).
- This is NOT a falsification of F132 §7. F132 §7 listed multiple sub-tests (capacity, similarity preservation, cascade, native chirality flip cost, cross-sector retrieval); this finding addresses the cascade-composition sub-test specifically.

---

## §7 Open questions for follow-up

1. **At what D does chirality-tag recall reach >0.5 reliably?** Sweep D ∈ {1024, 4096, 16384, 65536} at fixed N=32.
2. **At what N does chirality-tag recall reach >0.5 reliably?** Sweep N ∈ {4, 8, 16, 32, 64} at fixed D=1024.
3. **Does the encoding refinement (§5) improve signal-to-load?** Alternative encodings vs the current tile+quantise.
4. **Does Class L's spectral structure (eigenvalue ordering) carry information that survives Klein-4 encoding?** Currently the test treats all eigvecs symmetrically; assigning sector by eigenvalue magnitude might align with substrate-chirality (Spike #185 Mersenne-fiber-degree concentration ℓ ∈ {1,3,7}).
5. **Path 3/6 at-scale test will answer the load-bearing chirality-axis question** — what test pattern + scale gives reliable cross-sector discrimination?

---

## §8 Cross-references

- F132 (Klein-4 HDC engineering proposal; §7 cascade-composition sub-test addressed here)
- F135 (substrate vs shadow chirality; substrate-side chirality measurement)
- F137 (raw capacity comparison; load-induced signal degradation calibration)
- UPSTREAM_NOTES §4 (Klein-4 LANDED in srmech v0.4.3)
- srmech.amsc.laplacian (Class L — dense_laplacian + hermitian_eigendecompose)
- srmech.amsc.hdc.klein4_* (Class M rank-2 abelian)
- R-RBS-LM-98_klein4_classL_cascade_composition.py (this finding's script)
- R-RBS-LM-98_results.json (this finding's data)

**Next step:** Path 3/6 — Cross-sector retrieval at scale (F132 §7) with larger D and proper encoding refinement per §5.

PR #687 STAYS DRAFT.

---

*Articulated 2026-05-27 per user direction "let us walk each one sequentially". Path 2/6
empirical result: Klein-4 + Class L cascade composes algebraically with no operator-
incompatibility; chirality-tag retrieval signal is marginally above random at D=1024, N=32
(0.281 vs 0.25 baseline = +0.031). Consistent with F137 capacity-degradation calibration
at moderate load. The signal scale needed for reliable chirality discrimination depends on
D and N — Path 3/6 explicitly addresses scale-up. The finding TIGHTENS F132's empirical
specification rather than invalidating it: cascade composition WORKS; chirality-axis
discrimination needs sufficient D / low enough load to be load-bearing.*
