# F1268 — the powered re-run (n=50 probes, sd 0.071 instead of 0.20): **the capacity exponent is 0.801, not F1267's 0.926** — third revision of the same number, and each revision came from fixing a measurement defect rather than from new physics. The exponent is **stable across dim** (0.812 lower half / 0.762 upper). The threshold-dependence question is **NOT settled**: exponents 0.867 / 0.801 / 0.767 at thresholds 0.75 / 0.50 / 0.25 are **monotonically ordered** but their spread (0.101) is **comparable to the fit residuals** (up to 0.086), and the harness's binary verdict fired at 0.101 against a pre-set 0.10 bar — **a coin flip, not a finding.** Also: the "sharp transition" I assumed was itself noise; properly measured it is a **gentle sigmoid over ~7× in N**.

**User (2026-07-20):** *"yes, run both"* — the two tests F1267 queued.

## The measurement defect that had to be fixed first
The first attempt used **n≈6 probes per point** → binomial sd **0.204**. The curves came back non-monotonic (`dim=512: 1.00 1.00 1.00 0.80 0.33 0.60 0.33 0.00`), which is exactly what a monotone decay looks like under ±0.20 noise. **I stopped that run rather than fit exponents to it** — it would have been the fifth sampling artifact in this chain (F1265 dyadic grid, F1266 ceiling-as-plateau + 2-point trend, F1267 coarse ladder + chosen divisors).

Power analysis: resolving a 0.10 exponent difference over this dim span needs N_crit to **19 %**; an interpolated crossing with ±0.20 per point is 30–50 % off. **Not enough to separate 0.9 from 1.0**, which is the whole question.

Re-run at **n=50** (sd 0.071). Curves became clean and monotone:
```
dim=512   1.00 0.98 0.96 0.84 0.69 0.58 0.38 0.26
dim=1024  1.00 0.98 0.88 0.86 0.59 0.51 0.26 0.24
dim=2048  1.00 1.00 0.87 0.69 0.57 0.36 0.27 0.19
dim=4096  1.00 0.92 0.92 0.62 0.52 0.40 0.13 0.04
```
**Correcting another of my assumptions:** I had called this a "sharp transition." It is a **gentle sigmoid decaying over ~7× in N** — the sharpness was noise too. (Good news for the method: a gradual transition makes the crossing interpolation well-conditioned.)

## The exponent — third revision
| threshold | exponent | max resid | n_dims |
|---|---|---|---|
| 0.75 | **0.867** | 0.0549 | 5 |
| 0.50 | **0.801** | 0.0863 | 5 |
| 0.25 | **0.767** | 0.0490 | 4 |

**Full-span (0.50 threshold, dims 512…8192): 0.801.** F1267 reported **0.926** over 1024…4096 at n=6. So the headline number has now moved **1.000 (assumed) → 0.585 (F1266) → 0.926 (F1267) → 0.801 (here)** — and *every* move was a measurement fix, not new structure. That history is the finding as much as the number is.

**Stability in dim:** lower half 0.812 (512–2048), upper half 0.762 (2048–8192) — Δ 0.05, inside the 0.12 bar. **The exponent does not drift with scale.**

## Threshold-dependence — NOT settled, and I am not calling it
The harness printed *"NO single power law — the EXPONENT ITSELF moves"*. **I do not trust that verdict and am recording why:**

- spread across thresholds = **0.101**
- pre-set decision bar = **0.10**
- fit residuals = up to **0.086**

The spread is **comparable to the residuals**, and the call fired 0.001 past an arbitrary bar. That is a coin flip.

**What is genuinely suggestive:** the three exponents are **monotonically ordered with threshold** (0.867 > 0.801 > 0.767 as the threshold falls). Three-in-correct-order has p ≈ 1/6 by chance — weak evidence, in the right direction, and not enough. **Three thresholds cannot separate "a spectrum" from "scatter with a lucky ordering."**

**In flight:** `R-RBS-LM-POOLED` — a fixed-candidate-pool read making cost **O(pool·dim), independent of N** (~20× at dim 8192), validated first against the full read to confirm it preserves the *exponent*, then used for **9 thresholds with bootstrap CIs**. That makes the question decidable: if all CIs share a common value there is one exponent and the spectrum reading dies; if none does, the exponent is a function of where you read.

## On the MFO / multifractal connection — the shape, and the missing piece
The user connects this to the MFO **1D…11D-per-excitation** reading with a **UV floor near 2D**, as "the discrete math behind the continuous asymmetrical resonator hyperloop" (the #243/F1070 arc).

**The structural shape genuinely matches.** If the exponent is threshold-dependent, the right object is not a number but a **spectrum indexed by threshold** — which is the multifractal formalism: no single Hausdorff dimension because the object is not self-similar in one way, different parts scale differently. "Geometry-less" is apt: pure scaling relations, no embedding. It also fits **F1063's "scale is a fractal TOWER (nested containment), not a ladder"** — a tower is exactly the thing a single exponent would be the wrong object for.

**The missing piece, stated plainly: there is no defined map from a capacity exponent to an MFO dimension.** Our measured range is **0.767…0.867**; MFO's is 1…11 with a floor near 2. Asserting a correspondence between those without a derivation would be **numerology**, and this finding does not claim one. What the measurement *can* deliver is the shape: **whether a spectrum exists, its extent, and whether it has a floor.** Supplying the exponent→dimension map is the **prior** piece of work, and it belongs to the MFO layer, not to this harness.

## Verdict / next
Exponent **0.801**, stable in dim, residual 0.086. Threshold-dependence **open** — suggestive ordering, insufficient power. The "sharp transition" and the 0.926 both dissolved under proper measurement.

**NEXT:** (a) the pooled-read spectrum (9 thresholds, bootstrap CIs) — in flight, and it settles the open question either way; (b) if a spectrum is confirmed, its **extent and floor** are the measurables to report, *not* a dimensional correspondence; (c) the exponent→dimension map is a separate MFO-layer derivation and should be done before any 1D…11D comparison is attempted.

Composes **F1267** (its 0.926 superseded by 0.801), **F1266**, **F1265**, **F1264**, **F1263**, **F1063** (the fractal-tower reading), **#243/F1070** (the asymmetric-resonator arc this would feed), `[[feedback_read_independent_structure_check_first]]`, `[[feedback_computational_provenance_discipline]]`, #231/PKG-3.
