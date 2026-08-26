# F883 — Inverse-coupling rotation sandwich `q·p·q̄` does NOT raise the routing ceiling: it flattens to 0.79 and LOSES the octonion's 0.81. The single-sided ODFT twiddle stays the ceiling. The user asked: couple the two sides of the QDFT twiddle as **inverses** (the genuine rotation sandwich `q·p·q̄` — left `q`, right `conj(q)` = the inverse for unit `q`) to push past 0.81. Built it (`cd_mult`/`cd_conjugate`, exact-rational `cos/sin`). Measured @ N=1000: sandwich ℂ/ℍ/𝕆 all = **0.79** (flat across the algebras), reproduction 1.000 — vs the single-sided literal 0.78 / 0.79 / **0.81**. So inverse coupling **lifts ℂ slightly** (0.78→0.79) but **loses 𝕆's 0.81 advantage**, and does not raise the ceiling. The mechanism is the lesson: the genuine rotation `q·p·q̄` is **norm- and scalar-part-preserving** — it rotates only the imaginary subspace by 2θ about μ, which spreads positions *less* than the single-sided `q·p` (which mixes real↔imaginary and spreads more). **Routing rewards maximal position-distinctness, so a structure-preserving rotation is the wrong objective** — the spreading single-sided ODFT remains best at 0.81.

**Date:** 2026-06-20 · **srmech:** 0.9.0rc9 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Provenance:** `R-RBS-LM-883_inverse_coupling_sandwich.py`, 1000 `simplewiki_v082` sequences · **Composes:** F882 (the single-sided literal twiddle this tries to beat — 0.81 ceiling stands), F862 (cd_mult non-commutativity; the sandwich uses both sides), the cascade `cd_conjugate` (Class-K conjugate), §0 duality · **User direction (2026-06-20):** "if we DFT each piece of our 3 axis QDFT but in an inverse coupling way maybe? to see if we can raise routing ceiling."

## Measured (sparse, srmech-native; N=1000)
| twiddle | ℂ (1 axis) | ℍ (3 axis) | 𝕆 (7 axis) | reproduction |
|---|---|---|---|---|
| single-sided `q·p` (F882) | 0.78 | 0.79 | **0.81** | 1.000 |
| **sandwich `q·p·q̄` (inverse coupling)** | 0.79 | 0.79 | 0.79 | 1.000 |
- Inverse coupling **flattens** the algebra dependence (all → 0.79) and **does not raise the 0.81 ceiling**. It is a small win for ℂ, a loss for 𝕆.

## Why (the honest mechanism)
- `q·p·q̄` with unit `q` is the genuine **SO rotation**: it fixes the scalar part of `p` and rotates the imaginary part by 2θ about μ, **preserving |p|**. Structure-preserving = positions stay *closer together* in the projected key (less spread).
- Single-sided `q·p` is **not** a pure rotation — it mixes the scalar and imaginary parts (the real part bleeds into the imaginary and vice-versa), so distinct positions land *further apart* after projection. For routing-by-distinctness that extra spread is exactly the win, and the octonion's 7 imaginary axes maximize it (F882's 0.81).
- So "inverse coupling" answers a different objective (faithful rotation) than the one routing wants (maximal address-spread). The ceiling-raise needs *more* spread, not a norm-preserving rotation.

## Honest scope
- A clean **negative** for the ceiling-raise: 0.81 stands (single-sided ODFT, F882). Inverse coupling is not the lever.
- Octonion non-associativity: the sandwich was computed as `(q·p)·q̄` (one fixed grouping); a different grouping/Moufang variant could differ, but the spreading argument holds for any norm-preserving rotation.
- N=1000; reproduction 1.000 throughout (the within-page recall is untouched by any twiddle choice — only routing discriminates).
- Sparse held: `cd_mult`/`cd_conjugate` + exact-rational series + Klein-4 resonance + `Q`; no dense/numpy/bag.

## Verdict / next
Inverse coupling (`q·p·q̄`) does **not** raise the routing ceiling — it flattens to 0.79 and loses the octonion advantage, because a norm-preserving rotation spreads positions *less* than the single-sided twiddle. **The 0.81 ceiling (single-sided ODFT, F882) stands.** The real lesson for raising it: routing wants **maximal position-distinctness**, so the lever is a *more* spreading transform, or — the deeper move — escaping bundle-addressing's saturation entirely (the storage-density arc). **Next:** the cavity/standing-wave reading (user 2026-06-20: geodesic nulls = resonant-cavity nodes; music theory as the discrete-mode lens). Framework → srmech measurement; clean negative recorded; the spread-vs-rotation distinction is the takeaway.
