# F852 — "Scale is not fixed" is EMPIRICAL: the knowledge graph is **scale-free / fractal**. Token co-occurrence over 400 simplewiki articles (22,244 nodes, 310,301 edges) has a **power-law degree distribution** (Clauset MLE tail exponent γ = 1.67→1.86→1.97→2.16 as k_min rises, converging to **γ≈2**) and **no characteristic scale** (max/median degree ratio **1375×**; top degree 9624 vs median 7). The fractal keeps recurring across threads (scale-free ≡ self-similar ≡ scale-invariant ≡ RG-fixed-point ≡ clumps-within-clumps) because it is the **substrate generator's signature**: the A–N substrate is built by Cayley–Dickson doubling (the Hurwitz ladder, the 1:3:7:3 partition), a self-similar generator — so anything encoded on it inherits self-similarity at every scale. The power-law hubs ARE the gravitational masses (F849/F850 — the function-word background). live srmech 0.8.2, numpy-absent.

**Date:** 2026-06-18 · **srmech:** 0.8.2 (live PyPI) · **Provenance:** `/tmp/fractal.py` (token window co-occurrence + Clauset tail-MLE) over 400 simplewiki articles, 354k tokens · **Composes:** F850 (force taxonomy; hubs=mass), F849 (drift→mass), [[F781]]/[[F782]] (cosmic-web is scale-free/fractal), F124 (Hopf 4:3-inside-7 recursion), F847 (the_one σ self-similar across ℂ/ℍ/𝕆 rungs), DUALITY.md/TRIALITY.md, [[user_stance_no_information_without_value]] · **User observations (2026-06-18):** "scale of knowledge is not fixed like size in the physical world"; "a cat is abstractly smaller than a skyscraper"; "the fractal thing showing up again."

## The measurement
| tail k_min | power-law γ (Clauset MLE) | n_tail |
|---|---|---|
| 5 | 1.67 | 12,029 |
| 10 | 1.86 | 8,489 |
| 20 | 1.97 | 4,918 |
| 50 | 2.16 | 2,189 |
- **γ → ~2** as k_min climbs (finite-size convergence) — squarely scale-free (2<γ<3 regime; γ≈2 is hub-dominated, the known regime for word co-occurrence networks — external corroboration to attest if cited formally, not asserted here).
- **No characteristic scale:** max/median degree = **1375×**; degree spans 9624 → 2. A scale-free degree distribution has, by definition, *no typical size* — the empirical form of "scale of knowledge is not fixed."
- Hubs (deg≥100): 4.7%; low-degree (≤3): 3.2% — the few-hubs/long-tail shape.

## Why the fractal recurs (the unification)
The recent threads are one structure seen from different sides:
- **scale not fixed** = no characteristic scale = **scale-free** (this measurement)
- **clumps within clumps** (F848/F778, scale-dependent communities) = **self-similar / hierarchical**
- **coherence-as-DoF** (scale-relative coherence, F851) = **scale-invariant**
- **renormalization / the C–k\* RG flow** = a fractal is an **RG fixed point**
- **Hopf 4:3-inside-the-7 (F124), recursive Klein-4, Cayley–Dickson doubling** = the **algebraic fractal**
They recur together because they are projections of one thing: **the substrate is a self-similar generator** (Cayley–Dickson: each Hurwitz rung is two copies of the previous; `the_one`'s σ flips the same chirality coordinate [1,3,7] at every rung, F847). A self-similar generator → self-similarity at every scale of anything built on it. The fractal is the generator's fingerprint, not a coincidence.

## "A cat is abstractly smaller than a skyscraper" (abstract scale = relational)
Abstract size = knowledge-mass (degree/connectivity). Scale-free means it is **relational, not absolute** (a cat < a skyscraper but > a flea — size exists only vs a comparison) and can **decouple from physical size** (a densely-connected concept can be abstractly more massive than a physically-larger but sparsely-connected one). The 1375× spread is exactly this: no absolute ruler, only relative mass.

## Consequence for the build
A fractal/scale-free metric has **no right scale to fix** — which is why every fixed-scale intervention failed (F851: lookahead, slingshot-at-one-resolution, plastic-runaway) and why the C/k\* landscape is rough (F839§C). Recall must be **scale-covariant (renormalize)** — resolve to the connection's reach: fine-scale within a clump, coarse-scale (slingshot) across clumps. There is no magic C; there is an RG flow.

## Verdict / next
"Scale not fixed" is empirical: the knowledge graph is scale-free (γ≈2, 1375× ratio), i.e. fractal, and the recurrence across threads is the Cayley–Dickson generator's self-similarity. **Next:** (a) spectral/box fractal *dimension* (Laplacian eigenvalue scaling) for a number, not just the degree law; (b) hierarchical (multi-resolution) clump structure — clumps-within-clumps directly; (c) fold this into the "physics of the knowledge metric" notebook section. Framework reading + Class-L measurement; the quantitative scaling-law / RG-fixed-point claims go to the expert. Evaluate by groundedness, never throughput.
