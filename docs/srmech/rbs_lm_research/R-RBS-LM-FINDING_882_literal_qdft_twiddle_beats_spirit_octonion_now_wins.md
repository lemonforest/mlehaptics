# F882 — The LITERAL exp(μθ) QDFT/ODFT twiddle beats the F881 multi-axis spirit, and the octonion verdict REVERSES: 𝕆 now WINS (routing ceiling 0.78 → **0.81**). Built the genuine hypercomplex twiddle `q(pos) = cos θ + μ·sin θ` (μ a **unit** pure imaginary; ℂ=1 axis, ℍ=3, 𝕆=7) and applied it where a hypercomplex value actually lives in the pipeline — the **octonion-valued context** (`word_oct`/`ctx` is an octonion *before* it's hashed to Klein-4) — by Cayley-Dickson multiply, *then* projected. Head-to-head at N=1000 (rc9, exact-rational `cos/sin_series_truncate`, `Q`-returning similarity): **literal ℂ 0.78 = the spirit's whole ℍ rung** (one genuine rotation ≥ three composed scalar `phase_bind`s); **literal ℍ 0.79; literal 𝕆 0.81 — a new high**, reproduction held at 1.000 throughout. The reversal is the finding: in the F881 *spirit* (composed scalar phase-binds) 𝕆 **underperformed** ℍ (0.75 < 0.78, the phases over-spread the Klein-4 key); in the *literal* twiddle 𝕆 **outperforms** monotonically (0.78 → 0.79 → 0.81) because a single unit-norm rotation in the algebra **does not dilute** the carrier — it just uses more of the octonion's 7 imaginary dimensions to make positions distinct. **"Do the transform in the algebra, then project" beats "compose phase ops on the carrier."**

**Date:** 2026-06-20 · **srmech:** 0.9.0rc9 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Provenance:** `R-RBS-LM-882_literal_qdft_twiddle.py`, 1000 `simplewiki_v082` sequences, 6 conditions · **Composes:** F881 (the multi-axis spirit this beats + reverses), F880 (the routing ceiling it raises 0.70→0.81), F862 (θ abelian; cd_mult non-abelian — now the literal rotation IS in the cd_mult algebra), F868/§64 (exact-rational `Q` end-to-end), tasks #203–205 (the `exp(μθ)` twiddle — now validated *useful*, motivates graduation), §0 k=3/k=7 ladder · **User direction (2026-06-20):** "build the literal exp(μθ) QDFT twiddle and re-test against the ℍ rung."

## Measured (sparse, srmech-native; N=1000)
| condition | routing | reproduction |
|---|---|---|
| no phase (baseline) | 0.59 | 0.896 |
| F881 spirit — scalar `phase_bind` ℂ (1 axis) | 0.73 | 1.000 |
| F881 spirit — scalar `phase_bind` ℍ (3 axis, the rung) | 0.78 | 1.000 |
| **literal exp(μθ) ℂ (1 axis)** | **0.78** | 1.000 |
| **literal exp(μθ) ℍ / QDFT (3 axis)** | **0.79** | 1.000 |
| **literal exp(μθ) 𝕆 / ODFT (7 axis)** | **0.81** | 1.000 |
- **Literal ℂ (0.78) = spirit ℍ (0.78):** one genuine `exp(μθ)` rotation matches three composed scalar phases — the literal twiddle is *more efficient per operation*.
- **Literal is monotonic in axes (0.78 → 0.79 → 0.81); the spirit was not (0.73 → 0.78 → 0.75).** Same algebras, opposite trend at 𝕆.

## Why the reversal (the mechanism)
- **Spirit** = compose k scalar `klein4_phase_bind`s at distinct frequencies on the Klein-4 key. Each bind spends capacity; k=7 over-spreads the key (the F871 wall on the carrier) → 𝕆 worse than ℍ.
- **Literal** = build one **unit** element `cos θ + μ sin θ` (|q|=1, μ spanning k imaginary axes) and rotate the octonion context by it *in the algebra*, projecting once. The carrier is hashed once (same cost as baseline); more axes = a richer rotation that separates positions better, with **no dilution** → 𝕆 best. The octonion's full 7-dimensional imaginary space is an asset when used as one rotation, a liability when used as seven phase-binds.
- This is the **transform-then-readout** principle: the QDFT/ODFT belongs *in* ℍ/𝕆 (the `cd_mult` algebra, F862's order-carrier), not approximated by stacking abelian phase ops on the projected carrier.

## Honest scope
- **Still single-sided** `cd_mult(q, p)` — a left twiddle, not the full rotation `q p q̄` (that is the inverse-coupling sandwich, the next test — does it raise 0.81?).
- μ made unit via a **rational** `1/√k` (`1/√3 ≈ 57735/100000`, `1/√7 ≈ 37796/100000`) — attested rational constants, not floats; `cos/sin` are exact `*_series_truncate`. No `math`/numpy.
- 0.81 still **saturates** below the toy's 1.0 — the twiddle sharpens the address, it does not abolish the bundle wall (the storage-density arc). N=1000.
- Sparse held: `cd_mult` + exact-rational series + Klein-4 resonance + `Q` ranking; no dense, no bag.

## Verdict / next
The user's instinct is doubly confirmed: the **literal** `exp(μθ)` twiddle beats the multi-axis spirit, and — unlike the spirit — **the octonion (ODFT, full 7 axes) is the winner**, the new routing ceiling **0.81** (from 0.70 flat, 0.78 spirit), reproduction 1.000. The lesson: run the transform *in* ℍ/𝕆, then project. **Next:** (1) the **inverse-coupling sandwich** `q p q̄` (user 2026-06-20 — does the genuine rotation push past 0.81?); (2) graduate `exp(μθ)` to srmech #205 (now validated useful); (3) carry the ODFT twiddle into the full grid generator (F879/F880). Framework → srmech measurement; the spirit-vs-literal reversal is the headline; saturation stated honestly.
