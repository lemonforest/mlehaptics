# F755 — the observer-viewport, run on a SEED-ANCHORED solar surface: near:far is a local section, locality dominates at every scale, and the far tail is holographically held (with honest caveats)

**Date:** 2026-06-15 · **srmech:** 0.7.5rc149 · **Composes:** F750 (the first viewport cut — starved because top-N-by-FREQUENCY has no planets), F748 (uncapped kernel), F754 (the compact assoc graph the surface is built from — no 112MB load), F119/F529 (two-tier: exact near + holographic far), F552 (projection cost / d_S flow), F542/F544 (tome read-out; loop not circle) · **User direction (2026-06-14):** "real caps of what a NOW can encode, but the scale-invariant universe should show us how to make it stretch over a larger surface in some fractal looking way … how do we even begin to research this?" + "yes, those 3 please" · **Provenance:** `R-RBS-LM-VIEWPORT…py` (seed-anchored surface from `simplewiki_assoc.json`; tome routing via `R-RBS-LM-TOMECMP`)

## The fix that made the experiment real (over F750)
F750 took the **400 most frequent** simplewiki words as the surface — which **does not contain the planets** (mars/jupiter aren't top-400 by frequency), so the solar demo got one viewport center and the holographic step was skipped. The fix is itself the thesis: **the viewport is WHERE YOU POINT, not the global top.** The surface is now **seed-anchored** — a BFS from the solar seeds through the compact F754 assoc graph (no 112MB load) — so all 16 solar words are present (`mars, sun, earth, moon, planet, planets, jupiter, saturn, venus, mercury, neptune, uranus, solar, orbit, star, space`). Nested by BFS order, so N=200 ⊂ 300 ⊂ 400 is a genuine zoom.

## Results (400-word seed surface, 3027 edges; dense-eig per load)
**(1) near/far is a LOCAL SECTION — but on this tight cluster it varies more with SIZE than with CENTER.** Centering on mars / sun / earth / jupiter, the NEAR set is essentially the whole solar system and the FAR set is just generic `star` every time. The center's *tome* does shift (mars/earth → tome 0; sun/jupiter → tome 1), but the ±1 window captures the rest of the cluster regardless. **Honest read:** the solar system is ONE coherent viewport at this resolution, so the "re-assigns by center" claim is weak here — `star` (generic stars, not the Sun) being the consistent outlier is the only center-stable split. The local-section behaviour shows up far more cleanly under viewport SIZE, below.

**(2) Locality dominates at every scale (the "fractal stretch"), on TWO axes:**
| axis | setting | near | far | near:far |
|---|---|---|---|---|
| viewport SIZE (NT), fixed N=400 | NT=11 / 14 / 16 | 93/91/90% | 3/6/7% | **28.7 / 15.8 / 13.3** |
| surface SIZE (N), fixed NT=14 | N=200 / 300 / 400 | 80/89/91% | 16/9/6% | **5.0 / 9.8 / 15.8** |

near:far stays in the **O(5–30) band** across both axes — locality always dominates; it never collapses toward 1 (no-locality) or diverges. **Honest caveat:** it is **not a constant ratio** — it trends smoothly (tighter tomes → higher ratio; bigger surface → higher ratio). So "scale-invariant" should be read as *"locality dominates at every scale, with a smooth monotone trend"* — a self-similar regime, **not** a fixed-point invariant. That is the honest form of the user's "fractal stretch": the same *shape* (near ≫ far) holds as you change the viewport, which is what lets a NOW stretch over a larger surface without a phase change.

**(3) The far tail is holographically HELD (modest margin).** From the mars viewport, bundle the strictly-out-of-tome solar words into one Klein-4 holographic store and decode: `sim(recovered, 'sun') = +0.363` vs `sim(recovered, random) = +0.273`. **The sun is recoverable above the random floor — present-but-fuzzy, not erased ("don't forget the sun").** Honest caveat: the **margin is small (~0.09)** because it's a 12-way superposed bundle through a holographic encode — the far tier is genuinely *defocused*, which is the point (exact near + fuzzy far = the F119/F529 two-tier), but don't oversell the separation.

## What this answers (the user's "how do we even begin to research this?")
- **The research handle IS the seed-anchored viewport.** You don't encode a fixed NOW; you POINT a viewport (a seed + a size) at the one uncapped SSoT and take a local section. Two knobs — surface size N and tome count NT — and the near:far shape is stable across both. That is the operational form of the MFO d_S dimensional flow (F552): scale is a knob, not a fixed fidelity.
- **The "real cap of a NOW" is the dense-eig surface size** (pure-Python Jacobi is O(n³) → a few hundred nodes), **but the cap is on the FOCUSED tier only** — the relational/holographic tiers (F754, sparse + holographic) carry the rest uncapped. So the cap doesn't bound what's *held*, only what's *exact-at-once*. That's the two-tier escape from the NOW-cap.

## Honest scope
- Tight-cluster artifact: the solar neighbourhood is so coherent that step (1)'s center-relativity is weak; a better center-relativity test needs a surface spanning *several* unrelated clusters (e.g. seed from solar + cooking + music) so centers land in genuinely different regions. Noted as the next refinement.
- "Scale-invariant" is the loose/honest sense (same dominance shape, monotone trend), not a constant ratio.
- Coarse edge weights (rank-proxy from the top-K assoc, F754) — the tome topology (atan2 of eigvecs 1,2) is robust to this, but the exact ratios would shift with true weights.
- srmech-native (Class-L eig, Klein-4 holographic, Class-K similarity); no `abs()`; no CAD; no re-encode; data outside the repo.

## Verdict
On a seed-anchored solar surface (planets present), **near:far is a local section whose locality-dominant SHAPE is stable across viewport size and surface size** (the honest "fractal stretch" — self-similar regime, not a fixed invariant), and **the far tail is holographically recoverable above the random floor** (present-but-fuzzy, modest margin). The user's observer-viewport reading is supported as the operational form of the MFO d_S flow; the NOW-cap is on the focused dense-eig tier only, with the sparse + holographic tiers carrying the rest uncapped. Next: a multi-cluster surface for a stronger center-relativity test, and the relation-edges rung (F756).
