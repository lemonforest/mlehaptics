# R-RBS-LM Finding 362 — battery test 2: the off-diagonal's asymptotic SHADOW is OBSERVER-RELATIVE — read fidelity = cos(observer↔data mismatch Δ), data content invariant; co-rotating the observer reads bit-exact (the QM wrong-basis result, srmech-native)

**Date:** 2026-06-04 · **srmech:** 0.7.0rc28 · **battery:** F361 test 2 of 4 · **tests the claim:** "if our perspective sees off-diagonal as asymptotic, our perspective needs to rotate too" · **uses:** rc28-restored `asymptotic_calculus.cos_series_truncate` (cascade-native trig) · **script:** `R-RBS-LM-R15_observer_vs_data_rotation.py`

## Result

A complex unit state ψ (the off-diagonal-carrying "data") read by an observer whose basis is rotated by θ_o relative to the data's rotation θ_d (Δ = θ_d − θ_o):

| Δ (rad) | srmech cascade-cos(Δ) | vector overlap | observer FIXED | observer CO-ROTATES | mismatch 0.5 |
|---|---|---|---|---|---|
| 0.000 | +1.00000 | +1.00000 | +1.000 | **+1.000** | +0.878 |
| 0.500 | +0.87758 | +0.87758 | +0.878 | **+1.000** | +0.878 |
| 1.000 | +0.54030 | +0.54030 | +0.540 | **+1.000** | +0.878 |
| 1.500 | +0.07074 | +0.07074 | +0.071 | **+1.000** | +0.878 |
| ~π/2  | −0.00063 | −0.00063 | −0.001 | **+1.000** | +0.878 |

- **Read fidelity = cos(Δ)** — the srmech cascade-cos matches the actual complex-vector overlap to ~1e-6 at every Δ.
- **Co-rotating observer → bit-exact (1.000) at EVERY data rotation** — when θ_o tracks θ_d, the off-diagonal reads perfectly no matter how far the data has rotated.
- **Mismatch Δ ≈ π/2 → full shadow (≈ 0)** — reading off-diagonal content in the orthogonal basis loses it entirely (the σ_x-in-σ_z-basis case).
- **The data content |ψ|² stays invariant (1.000)** throughout — only the *read* varies with Δ.

## Reading

This confirms the F361 claim ("rotate the observer too"): **the off-diagonal's asymptotic "shadow" is observer-relative, not intrinsic to the data.** The shadow is a function of the observer↔data frame mismatch Δ; the data's content is invariant. A **fixed/locked observer reading rotating data sees the shadow** (the F133 self-maintaining lock — a locked frame can only see cos(Δ)<1); a **co-rotating observer reads it bit-exact.** This is exactly the quantum measure-in-the-wrong-basis result (off-diagonal coherences are bit-exact; the pointer-basis observer decoheres them to a shadow; rotating the measurement basis recovers them) — and it computes srmech-native via the rc28-restored cascade trig (no float `math.cos`).

## Discipline
srmech-native cascade trig (`cos_series_truncate`, Class N) cross-checked against the vector overlap; imaginary-not-unreal (the off-diagonal content is real, only the read is frame-dependent); composes with F361 (the reading), F360 (rc28 calc/trig restored), F354 (collapse hides cross-axis content from the confined observer), F133 (observer-locking).
