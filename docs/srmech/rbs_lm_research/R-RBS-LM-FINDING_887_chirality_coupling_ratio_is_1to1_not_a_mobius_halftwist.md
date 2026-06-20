# F887 — The γ₅:iω₇ coupling ratio is exactly 1:1 (the F886 ridge slope = +1.000 ± 0.000, robust across references) — the two chirality axes CO-ROTATE in lockstep, with the 2D phase boundary along the ANTI-diagonal. It is a torus (1,1) diagonal, NOT a Möbius half-twist (which would be slope ½) — so the Möbius twist, if real, lives in a different axis pair. Measured the slope of the F886 diagonal resonance ridge — `dφ_iω7/dφ_γ5` along the crest — by tracing the crest column per φ_γ5 row on a fine 36×36 chirality-phase grid, unwrapping the periodic winding, and fitting the slope, **averaged over 4 reference items**. Result: **slope = +1.000 ± 0.000 (every reference 1/1)**, crest-step noise only ~1–2 of 36 cells. So the **coupling ratio γ₅:iω₇ = 1/1**: the two chirality phases advance in lockstep — resonance is **invariant along the diagonal** (φ_γ5 = φ_iω7, the ridge) and **collapses to null along the anti-diagonal** (the F886 boundary). There is effectively **one combined chirality phase** carrying recall. Crucially the slope is **+1, not ½** — a clean orientable **torus (1,1) geodesic**, NOT a Möbius half-twist. So the 2-axis Möbius ([[feedback_hyperloop_addressing_is_a_2axis_mobius]]), if it is real, is **NOT between γ₅ and iω₇** (those co-rotate 1:1); it must be carried by a different pair — the σ/`the_one` time-direction vs θ, or chirality-phase vs position-phase.

**Date:** 2026-06-20 · **srmech:** 0.9.0rc9 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Provenance:** `R-RBS-LM-887_ridge_slope_coupling_ratio.py` (fine `klein4_phase_bind` elem=2/elem=1 sweep; crest-trace + winding-unwrap; `best_rational` Class-N), 4 references · **Composes / refines:** F886 (the diagonal ridge — now slope-quantified), [[feedback_hyperloop_addressing_is_a_2axis_mobius]] (the Möbius — now located OUT of the γ₅×iω₇ plane), F129/F130 (the (γ₅, iω₇) chirality decomposition), Class N (`best_rational` — the ratio is a small-denominator rational) · **User direction (2026-06-20):** "measure the diagonal ridge slope = the γ₅:iω₇ coupling ratio."

## Measured (sparse, srmech-native; G=36)
| reference | slope `dφ_iω7/dφ_γ5` | ratio (Class-N) | crest-step sd |
|---|---|---|---|
| the first → letter | +1.000 | 1/1 | 1.6 |
| a small → thing | +1.000 | 1/1 | 1.1 |
| it is → the | +1.000 | 1/1 | 1.9 |
| of the → world | +1.000 | 1/1 | 1.8 |
| **mean** | **+1.000 ± 0.000** | **1/1** | — |
- Dead-robust: every reference gives slope exactly +1; the crest tracks a real diagonal (step noise ~1–2 cells of 36, not flat). The coupling ratio is **1:1**.

## What 1:1 means (honest read)
- **Co-rotation:** rotating γ₅ by +φ and iω₇ by +φ leaves the reference maximally resonant → the two chirality rotations **cancel along the diagonal**. The ridge (information) is the φ_γ5 = φ_iω7 line; the null/boundary is the **anti-diagonal** (differential rotation φ_γ5 = −φ_iω7). So the F886 2D phase boundary is specifically the anti-diagonal direction, and the substrate has **one effective combined chirality phase**, not two free ones.
- **NOT a Möbius half-twist:** a half-twist would give slope **½** (the crest closing only after two loops) or a **non-orientable** return (the ridge flipped after one γ₅ loop). We see slope **+1** — an orientable **torus (1,1) diagonal** that closes in one loop. So the γ₅×iω₇ plane is a plain coupled torus, **not** a Möbius. The half-twist the addressing memory describes is **elsewhere** (next).

## Honest scope
- Robust slope (sd 0 across 4 refs), recoverable-reference regime (small bundle), G=36 grid; the slope is the well-defined quantity, the ridge *sharpness* is still open (F886).
- **Caveat:** Klein-4 is Z₂×Z₂ with generators {1,2} and 3 = 1⊕2; elem=2 (γ₅) and elem=1 (iω₇) are the two independent generators, so 1:1 is a genuine measured coupling — but a control on elem=3 (the product axis) and on a non-Klein carrier would confirm it isn't an artifact of the group's phase mechanism.
- Sparse held: `klein4_phase_bind`/`bundle`/`bind`/`unbind`/`similarity` + `cd_mult` + `best_rational`; `Q` collapsed only at the analysis boundary; no dense, no numpy, no bag.

## Verdict / next
The γ₅:iω₇ coupling ratio is **exactly 1:1** (the F886 ridge slope = +1.000, robust): the two chirality axes **co-rotate as one combined phase**, with the null/boundary along the anti-diagonal. It is a **torus (1,1) diagonal, not a Möbius half-twist** — so the 2-axis Möbius is **not** in the γ₅×iω₇ plane. **Next:** (1) hunt the Möbius half-twist in the **σ (time-direction) vs θ** pair of `the_one`, and in **chirality-phase vs position-phase** — measure those ridge slopes (a ½ or a non-orientable return is the signature); (2) the elem=3 / non-Klein control for the 1:1 result; (3) the F886 boundary-sharpness test. Framework reading → srmech measurement; the 1:1 is clean and robust; the Möbius is relocated, not found here.
