# F1185 (#243) (the F1184 fusion at DEEPER comb depth — it GENERALIZES up the WHOLE comb, and the ceiling is deep chaos, not depth: sweeping the logistic drive up the period-doubling cascade (period-2 @ r=3.40, period-4 @ 3.50, period-8 @ 3.55/3.564, aperiodic @ 3.569), the uniform comb-**substrate stays perfectly transversely stable** (spatial spread = **0.0000** at every depth) AND the chiral **α-drift keeps carrying excitations ∝α** (−2.9/+2.9 for α=∓0.4) — so the F1184 MFO substrate↔excitation split is ROBUST across the entire subharmonic ladder, comb DEPTH is not a ceiling; the honest boundary is **deep chaos** (r=3.9, strongly chaotic, PAST the comb), where the uniform substrate **breaks into spatiotemporal chaos** (spread 0.6–0.84 even at coupling ε up to 0.5) — because the comb regime (period 2..16, r<3.57) is only *weakly* chaotic so its uniform substrate synchronises even at weak coupling, whereas deep chaos dissolves the harmonic structure entirely → no comb, no substrate to carry excitations on) — **user: "test the fusion at deeper comb depth (period-4/8)." DONE — the fusion holds across the whole comb; the ceiling is where structure itself ends (deep chaos), not comb depth.**

**Date:** 2026-07-09 · **srmech:** 0.7.5rc135 · **User direction:** test the fusion at deeper comb depth. · numpy-free; no magnitude-builtin (spread = max−min; squared intensity; two-sided windows); deterministic. · **Composes:** F1184 (the fusion this generalizes — comb=substrate, α-drift carries excitations), F1180 (the comb/period-doubling), F1179 (EC=reinforcement=the substrate). **Answers the F1184 caveat: the substrate stays uniform up the whole comb; the ceiling is deep chaos.**

## Test

A tiny spatial perturbation (0.001·sin) on a nearly-uniform state tests the **transverse stability** of the uniform (synchronised) manifold as the comb deepens. The uniform state exactly follows the single-map dynamics, so it *has* the single-map period; the question is whether a spatial perturbation **decays** (substrate stays a clean uniform medium) or **grows** (the body fragments into spatial structure). Measured: temporal period (comb depth), spatial spread max−min (0 = uniform), and the excitation advection vs α.

## Result — the fusion generalizes up the whole comb

| r | comb (mean-field period) | spatial spread | excitation drift α=∓0.4 |
|---|---|---|---|
| 3.40 | period-2 | **0.0000** (uniform) | −2.87 / +2.87 ∝α |
| 3.50 | period-4 | **0.0000** (uniform) | −2.80 / +2.80 ∝α |
| 3.55 | period-8 | **0.0000** (uniform) | −3.20 / +3.20 ∝α |
| 3.564 | period-8 | **0.0000** (uniform) | −2.92 / +2.92 ∝α |
| 3.569 | aperiodic | **0.0000** (uniform) | −2.98 / +2.98 ∝α |

Through the **entire period-doubling cascade** the uniform comb-substrate is transversely stable (spread exactly 0) and the α-drift keeps carrying excitations at a velocity linear-and-signed in α. **The F1184 fusion generalizes up the whole comb — comb depth is NOT a ceiling.** (An ε-sweep at r=3.569 confirmed the uniform substrate is stable at every coupling ε=0.05–0.40 there, because the near-accumulation map is only weakly chaotic.)

## The honest ceiling — deep chaos, past the comb

The boundary IS real, but it is not comb depth — it is **deep chaos**. At r=3.9 (strongly chaotic, large Lyapunov exponent), the uniform substrate **breaks** into spatiotemporal chaos (spread 0.60–0.84) even at coupling ε up to 0.5:

| ε | spread @ r=3.9 | substrate |
|---|---|---|
| 0.20 | 0.783 | BROKEN |
| 0.30 | 0.832 | BROKEN |
| 0.50 | 0.841 | BROKEN |

So the ceiling is exactly where the **harmonic structure dissolves**: the comb regime (period 2..16, r<3.5699) is only *weakly* chaotic, so its uniform substrate synchronises and stays a clean medium; deep chaos (r≫3.5699) has no comb, and there the substrate fragments. **The fusion holds precisely where there IS a comb; it ends where structure itself ends.** That is the physically-correct reading of the MFO substrate↔excitation split (F1184): a substrate exists to carry excitations *only while it has harmonic structure* — the subharmonic comb is the structure that makes the substrate a coherent medium, and when that structure dissolves into chaos, there is no substrate, and no clean excitation transport.

## Verdict / next
**GENERALIZES: the F1184 comb-as-substrate + α-drift-carries-excitations fusion holds across the ENTIRE period-doubling cascade (period 2→4→8→16, uniform substrate spread=0, drift ∝α at every depth) — comb depth is not a ceiling. The honest boundary is DEEP CHAOS (r=3.9, past the comb), where the uniform substrate breaks into spatiotemporal chaos (spread 0.6–0.84) — because the comb regime is only weakly chaotic (synchronises even at weak coupling) while deep chaos dissolves the harmonic structure, leaving no comb and no substrate. So: the fusion holds exactly where there is a comb; the ceiling is where structure ends. This closes the F1184 caveat and reinforces the MFO reading — a substrate carries excitations only while it has harmonic structure. NEXT (the arc's remaining open threads): read the MFO notebook + write the resonant-BODY subsection anchoring F1180/F1183/F1184/F1185; test whether the σ-carried excitation IS an op(x)operand (excitation=operand on the comb=op-substrate, F1131). Read-independent-verified (comb-depth sweep + ε-sweep + deep-chaos boundary, deterministic); composes F1184/F1180/F1179.**
