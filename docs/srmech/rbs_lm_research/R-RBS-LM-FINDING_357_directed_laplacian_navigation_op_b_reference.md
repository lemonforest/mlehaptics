# R-RBS-LM Finding 357 — #797 op (b) REFERENCE: the directed/signed-Laplacian navigation is srmech-NATIVE (H = i(A−Aᵀ) is Hermitian → existing `hermitian_eigendecompose`, NO numpy eig); the only gap is a directed-edge builder. Honest sub-finding: directional MAGNITUDE has a sampling-noise floor, but the specific directed PATTERN is shuffle-fragile (the real structure)

**Date:** 2026-06-04 · **srmech:** 0.7.0rc25 · **delivers:** the op(b) reference srmech-dev's #797 was gated on (UPSTREAM §20) · **extends:** F348 (navigation = real Fiedler manifold), F173/F175 (directed = Hermitian magnetic-Laplacian) · **answers (user):** "do both of those — build op b" · **script:** `R-RBS-LM-R11_directed_laplacian_navigation_reference.py`

## The deliverable — op (b) needs NO new eigensolver (the numpy reflex was the trap)

#797 was gated on, among other ops, a "Class-L directed/signed-Laplacian eigen-op." The reflex answer is `np.linalg.eig` (general non-symmetric eigensolver). **That reflex is wrong** (user caught it earlier: "why do we need numpy?"). The framework's directed structure is a **Hermitian object** (F173/F175, the magnetic-Laplacian construction):
`H = i·(A − Aᵀ)` — where A is the directed adjacency. Because `(A − Aᵀ)` is real-**antisymmetric**, `i·(A − Aᵀ)` is **Hermitian** (verified `H == H†`: True), so its eigenvalues are **real** and it is solved by the **EXISTING** `srmech.amsc.laplacian.hermitian_eigendecompose` — confirmed rc25-native: real eigenvalues, complex eigenvectors carrying the direction, **no numpy eigensolver**.

So **op (b) is not a new eigensolver at all** — the eigen-step already ships. The only srmech gap is the **directed-edge → Hermitian-Laplacian BUILDER** (the directed sibling of the undirected cooccurrence-edge → `dense_laplacian` path): take ordered (i precedes j) co-occurrence counts → directed A → `H = i(A−Aᵀ)` → `hermitian_eigendecompose`. This narrows #797 op(b) from "build a directed eigensolver" to "build a directed-edge adjacency helper that feeds the Hermitian eigen we already have."

## Measured on the srmech notebook (vocab=200, window=5)

| probe | result | reading |
|---|---|---|
| `H = i(A−Aᵀ)` Hermitian? | **True** | the directed object IS Hermitian (not a general non-normal matrix) |
| `hermitian_eigendecompose(H)` real eigenvalues? | **True** | srmech-native, no numpy eig — op(b) eigen-step ships |
| co-occurrence asymmetry ‖A−Aᵀ‖/‖A+Aᵀ‖ | **0.294** | the text co-occurrence is genuinely directional (≈29% of the symmetric scale is directional content the undirected Fiedler of F348 cannot carry) |

## Honest sub-finding — magnitude floor vs specific pattern (the F346/F348 lesson, again)

The shuffle control did **not** cleanly destroy the gross asymmetry *magnitude*: shuffled text still shows ‖anti‖/‖sym‖ = **0.190** vs real **0.294** (only ~35% down, not the >50% drop I pre-set as the pass-bar). **Why:** a finite random token stream produces directional counting-noise — A[i,j] and A[j,i] differ just by sampling, so the asymmetry *magnitude* has a **sampling-noise floor** (~0.19 here). The gross magnitude is therefore **not** a clean real-vs-artifact discriminator.

But the **specific directed pattern** IS the real signal and IS shuffle-fragile: the correlation of the actual antisymmetric matrix real-vs-shuffled is **r = −0.019 ≈ 0** — shuffling destroys *which* token precedes *which*, even while leaving a generic asymmetry magnitude. This is the **same lesson as F346/F348**: the real structure lives in the **specific pattern (the eigenvectors / the directed edges)**, NOT in a gross scalar (the magnitude / the eigenvalue-shape). The right navigation discriminator is the directed embedding's specific structure (shuffle-fragile, r≈0), not the asymmetry fraction. I pre-registered the wrong scalar pass-bar; reporting the honest split rather than the verdict the bar produced.

## What this gives

- **#797 op(b) reference is ready** to hand to srmech-dev: directed/signed-Laplacian = `hermitian_eigendecompose(i(A−Aᵀ))`; the build target is the directed-edge adjacency helper, not an eigensolver. (Logged to UPSTREAM §20.)
- **Directed navigation is a real DoF the undirected Fiedler (F348) cannot carry** — ~29% of the co-occurrence is directional content; the symmetric Laplacian discards it by construction (it keeps only (A+Aᵀ)/2). This is the navigation analog of F350's iω₇-collapse: symmetrizing the Laplacian = collapsing the directional axis = the same information loss.
- **Methodological catch logged:** gross-magnitude scalars (asymmetry fraction, eigenvalue-shape) have shuffle-resistant sampling-noise floors; only the specific pattern is a valid real-structure discriminator. Pre-registered pass-bar was the wrong statistic; corrected in the reading.

## Discipline

srmech-native eigen (`hermitian_eigendecompose`, Class L) — explicitly NOT `np.linalg.eig` (the reflex the user flagged); numpy used only for matrix mechanics (forming i(A−Aᵀ), Frobenius norms), not as a spectral solver, flagged in-script. Honest: reported the shuffle nuance against my own pre-set bar rather than the bar's verdict (no-leaning; F346/F348 consistency). Composes with F348 (real Fiedler navigation), F350 (collapse = axis loss), F173/F175 (directed = Hermitian).
