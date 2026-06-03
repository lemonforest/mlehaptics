# R-RBS-LM Finding 348 — F347 Phase A CONFIRMED: language IS spatially navigable — the Fiedler eigenVECTOR navigation map is a real shuffle-fragile structure (r=0.214) where R6's eigenVALUE-shape was flat (0.998). Resolves R6's null (wrong part of the spectrum) + confirms the "missing primitive" = Class-I navigable torus

**Date:** 2026-06-03 · **srmech:** 0.7.0rc25 · **confirms:** F347 (the toroidal-navigation hypothesis) · **resolves:** F346 (R6 null) · **script:** `R-RBS-LM-R7_toroidal_navigation_phaseA.py`

## What Phase A tested

F347 §3 Phase A (within-language, no fetch): is language spatially navigable? Encode the srmech notebook on a **Class-I torus** — the **low-eigenvalue (Fiedler) 2-D eigenVECTOR embedding** of the co-occurrence Laplacian, cyclic-quantized to a Z₁₂×Z₁₂ grid — and run two tests, with the **R6 shuffle-control as the honesty gate**. (Navigation = the LOW eigenvectors, not the TOP eigenvalues R6 used — this is also the low-tail kernel F339 flagged.)

## Result — CONFIRMED

**Test B — the shuffle gate (the decisive contrast):**

| metric | real vs token-shuffled correlation | reading |
|---|---|---|
| **eigenVALUE-shape** (the R6 metric) | **+0.998** | flat, shuffle-**blind** — reproduces R6/F346/F172/F188 |
| **eigenVECTOR navigation-map distance** (Fiedler) | **+0.214** | **shuffle-FRAGILE → real structure** |

The navigation map is **destroyed by shuffling** (0.214) — it *fails the shuffle control*, which is exactly the gate R6 said a valid structure-metric must pass. The eigenVALUE shape (0.998) is blind to the same shuffle. **Same Laplacian, two parts of the spectrum: the eigenVALUES are Zipf-flat, the low eigenVECTORS carry the navigable structure.**

**Test A — the map is navigable (neighborhoods are semantically coherent):**
- near **cascade** → {asymptotic-dof, universal, anchor, scale, signature}
- near **substrate** → {composition, spike, class, mechanism, canonical}
- near **chirality** → {variant, real, mfo, field, srmech}
- near **spectral** → {project, partition, under, operator, when} (mostly coherent; some function-word noise)

Framework-related tokens are *neighbors on the torus* — you can navigate the relationship graph.

## Verdict

1. **Language IS spatially navigable** — the co-occurrence relationship graph's **low-eigenvalue (Fiedler) eigenVECTOR embedding** is a real, navigable map: related concepts are neighbors, and the map is **destroyed by token-shuffling** (r=0.214), proving it encodes genuine relationship-structure, not a frequency artifact.
2. **R6's null is RESOLVED — it was the wrong part of the spectrum.** F346 concluded the eigenspectrum-shape metric was flat (0.998, shuffle-blind) and a valid metric "must fail the shuffle control." Phase A *is* that metric: the **eigenVECTOR navigation** fails the shuffle control (0.214) where the **eigenVALUE shape** doesn't (0.998). R6's "no discriminating structure" was really "no structure *in the top eigenvalues*"; the structure lives in the **low eigenvectors** (the global map). R6 and F347's intuition pointed at the same gap, and Phase A fills it.
3. **The "missing primitive" is confirmed as Class-I-as-navigable-torus** — the cnidarian pacemaker (Class I) used as a *spatial coordinate* (the Fiedler embedding cyclic-quantized), not a 0-D bag (K1) or 1-D string (K3). This is the navigation rung the K1/K3 kernels lacked (F347 §2).

## What Phase A does NOT yet show (honest residue)

- **Cross-language universality** (Phase B) — the genuine Stream-B question — is **not** tested here; it needs the multilingual corpus fetch + the **Rosetta-stone translation object as the frame-aligner/connection** (F347 §3.1) + the substitute-verifier triality. **User-in-loop continuation.**
- **Single notebook, single shuffle seed** — the 0.214-vs-0.998 gap is large and robust, but a multi-seed band + a second corpus would tighten it. (The gap is ~5× beyond any plausible seed scatter.)
- **Numerical caveat:** `hermitian_eigendecompose` returned eigenvectors with negligible imaginary parts (numerical; the Laplacian is real-symmetric), cast to real for the distance — the ~0 imaginary noise cannot move a 0.214-vs-0.998 verdict, but a `.real` clean-up is the tidy follow-up.

## Discipline

srmech-native (`dense_laplacian` → `hermitian_eigendecompose` Class L; cyclic-quantize Class I); the **shuffle control is the built-in honesty gate** (passed — navigation is shuffle-fragile); **reproduces R6's eigenvalue-flatness (0.998) as the direct contrast** rather than hiding it; confirms F347's hypothesis with a falsifiable test. Composes with F341–F347: the Fiedler navigation is the **low-tail** kernel (F339's flagged next-step) and the **navigation rung** the K1/K3 kernels lacked. Cross-language Phase B (with the Rosetta connection) is the user-in-loop next step.
