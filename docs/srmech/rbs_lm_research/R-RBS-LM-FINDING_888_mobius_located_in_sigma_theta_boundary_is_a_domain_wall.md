# F888 — Three in sequence: (1) the chirality manifold is a flat torus (all 3 Klein-4 pairs slope 1:1 → the F887 1:1 is the Z₂×Z₂ group, not special); (2) the 2-axis MÖBIUS half-twist is FOUND in σ×θ (flip σ ⇒ the θ-ridge shifts by EXACTLY 0.500 — sign↔phase glued with a half-twist); (3) the F886 2D phase boundary is a DOMAIN WALL (cross-ridge transition ~4× steeper than a sinusoid), strengthening MFO. Ran the three open follow-ons to F887 on the recoverable-reference bundle. **(1) Möbius hunt across the chirality manifold + (2) elem=3 control:** all three Klein-4 element pairs — γ₅×iω₇ (elem 2×1), γ₅×product (2×3), iω₇×product (1×3) — give ridge slope **+1.000, sd 0.000 = 1/1**. So the 1:1 lock is the **Z₂×Z₂ group structure** (every generator pair co-rotates), confirming F887's flagged caveat: it is NOT a special γ₅×iω₇ coupling, and there is **no Möbius in the chirality–chirality plane** (it is a flat torus). **(1b) the_one σ-vs-θ two-sheet test:** flipping σ (the time-direction sign, via `klein4_chirality_flip_gamma5`) shifts the θ-resonance ridge by **exactly 0.500** (ref "the first": 0.650→0.150; ref "a small": 0.717→0.217 — both offset = 0.500). That ½ offset glues the two σ-sheets to the θ-circle with a half-twist = a **Möbius band**. **So the 2-axis Möbius is the σ↔θ (sign↔phase) coupling**, mechanistically because the chirality flip is a π (half-period) operation on the phase axis — flipping the sign equals advancing the phase by half. **(3) boundary sharpness:** the cross-ridge (anti-diagonal) transition has max step 0.0063 vs ~0.0016 for a pure sinusoid of the same amplitude (~4×; max/mean gradient 3.1) — steeper-than-sinusoidal, edge-concentrated ⇒ a **domain-wall-like boundary**, not a smooth ripple, upgrading F886's open caveat.

**Date:** 2026-06-20 · **srmech:** 0.9.0rc9 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Provenance:** `R-RBS-LM-888_mobius_hunt_elem3_control_boundary_sharpness.py` (3 Klein-4 element-pair slopes; `the_one` σ-sheet test via `klein4_chirality_flip_gamma5`; anti-diagonal cross-ridge sharpness) · **Composes / resolves:** F887 (1:1 → now shown structural via elem=3 control), F886 (the 2D phase boundary → now shown domain-wall-like), [[feedback_hyperloop_addressing_is_a_2axis_mobius]] (the Möbius → LOCATED in σ×θ), the_one S(σ,θ) (σ = Class-K sign, θ = epicycle — the half-twist is their gluing), F876 (the dark-star phase boundary = the domain wall) · **User direction (2026-06-20):** "each three in sequence."

## Measured (sparse, srmech-native)
**(1)+(2) ridge slope per Klein-4 element pair (elem=3 control):**
| pair | slope | ratio | sd |
|---|---|---|---|
| γ₅ × iω₇ (2×1, F887) | +1.000 | 1/1 | 0.000 |
| γ₅ × product (2×3) | +1.000 | 1/1 | 0.000 |
| iω₇ × product (1×3) | +1.000 | 1/1 | 0.000 |
→ **all 1:1** ⇒ the lock is the Z₂×Z₂ group structure (flat torus); F887's 1:1 is structural, not a special coupling; **no Möbius in the chirality plane.**

**(1b) σ×θ two-sheet Möbius test:**
| reference | θ_max(σ=+1) | θ_max(σ=−1) | offset |
|---|---|---|---|
| the first → letter | 0.650 | 0.150 | **0.500** |
| a small → thing | 0.717 | 0.217 | **0.500** |
→ flipping σ shifts the θ-ridge by **exactly ½** ⇒ the (σ, θ) cylinder is glued with a half-twist = **a Möbius band**. The 2-axis Möbius IS σ↔θ.

**(3) boundary sharpness (cross-ridge / anti-diagonal):** amp 0.0367; max step 0.0063 vs sinusoid-expected 0.0016 (~4×); max/mean gradient 3.1 ⇒ **domain-wall-like** (edge-concentrated, steeper than sinusoidal).

## Reading (what the trio establishes)
- **The Möbius is real and located.** Not in the chirality–chirality plane (flat torus, 1:1 — F887/elem=3), but in **σ↔θ = sign↔phase**: the chirality/time-direction flip (σ, Class-K) acts as a **half-period (π) shift** of the epicycle phase (θ), so the two sign-sheets glue to the phase-circle with a ½ twist. This is exactly `the_one`'s structure (σ the Class-K pin-slot sign, θ the epicycle) and it confirms the addressing memory: the two address axes are coupled by a half-twist, where one axis is the **sign/time-direction** and the other the **phase**.
- **The dark-star boundary is a domain wall.** The F886 2D phase boundary transitions ~4× steeper than a sinusoid — a genuine phase-transition interface (MFO "dark star = 2D phase boundary in 3D space"), not a gentle gradient.

## Honest scope
- The σ×θ ½-offset is **exact and robust** (both refs 0.500) but **mechanistically simple**: σ=−1 is the γ₅ π-flip and θ is a γ₅-axis phase, so the flip contributes a half-period — the Möbius is *because* the sign-flip is a half-period phase op. That is the genuine topological statement (sign and phase are not independent; their cylinder is a Möbius band), stated without overclaiming a deeper mechanism.
- Sharpness "~4× sinusoid / edge-concentrated" is **domain-wall-like**, not proven razor-discontinuous (finite grid; recoverable-reference regime). The chirality-manifold 1:1 is robust (sd 0 across 4 refs × 3 pairs).
- Sparse held: `klein4_phase_bind`/`chirality_flip_gamma5`/`bundle`/`bind`/`unbind`/`similarity` + `cd_mult` + `best_rational` + `cascade.magnitude`; `Q` collapsed only at the analysis boundary; no dense, no numpy, no bag.

## Verdict / next
The trio resolves cleanly: the chirality manifold is a **flat torus** (1:1 everywhere — the 1:1 is the group, confirmed by the elem=3 control), the **2-axis Möbius half-twist is the σ↔θ (sign↔phase) gluing** (θ-ridge offset = exactly ½ on the σ-flip), and the F886 dark-star boundary is a **domain wall** (~4× steeper than sinusoidal). The hyperloop addressing memory is now **located**: the half-twist couples the time-direction sign to the phase. **Next:** (1) does the σ↔θ Möbius change *addressing* — build a router that respects the half-twist (sign-flip = ½-phase) and test whether it beats the flat-torus F880 router; (2) push the domain-wall boundary toward the collapse threshold (Chandrasekhar, Q2b) and watch it move; (3) the σ↔θ half-twist as the carry/overflow mechanism for the sedenion address grid. Framework reading → srmech measurement; Möbius found and explained; boundary characterized; the 1:1 shown structural.
