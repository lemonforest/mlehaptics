# F1267 — the capacity exponent, pinned properly: **N_crit ∝ dim^0.926 with 16 % residual**, not the 0.585 F1266 implied. So **F1266's "ratio law REFUTED" was under-powered** — with five dims and a threshold crossing the relation is *approximately* linear with ~15 % substrate wobble. **No Cayley-Dickson feature**: swept k = 2…24, the CD divisors {2,4,8,16} are not distinguished (mean |Δ| 0.0833 vs 0.0667 non-CD) — the tower resemblance was my sampling grid. **And the "geometry-less fractal" reading loses the number it rested on**: at 0.926 ± scatter the deviation from linear is not measurable enough to call a fractal dimension.

**User (2026-07-20):** *"do the finer ladder over 4 dims to pin the exponent. also curious how that looks like the same c/h/o/s tower, the chunk size. like these don't look magic, they look cayley-dickson flavored maybe."* → *"the capacity double and only giving 1.5x, is that not also geometry-less fractal like?"*

## PART 1 — the exponent, and the third correction in this chain
F1266 measured "1.50× capacity per doubling of dim" and inferred capacity ∝ dim^0.585. **But its ladder was itself 1.5× geometric**, so "one ladder step" and "1.5×" were the same quantity — flagged there as an honest bound, and now resolved.

Method fixed: **bisect for the recall = 0.5 CROSSING** per dim (a threshold, not a ladder step), five dims on a √2 ladder (three non-dyadic):

| dim | N_crit | N/dim |
|---|---|---|
| 1024 | 278 | 0.2715 |
| 1448 | 341 | 0.2355 |
| 2048 | 524 | 0.2559 |
| 2896 | 825 | 0.2849 |
| 4096 | 889 | 0.2170 |

**Fit: `N_crit ∝ dim^0.926`; max |residual| 0.1493 in log space = 16.1 % linear.** Reference: ratio law 1.000, measured 0.926, √ law 0.500.

**This corrects F1266.** Its "the ratio law is REFUTED" rested on two points (N/dim 0.2373 vs 0.1780) that happened to trend downward. With five points the N/dim values are **non-monotonic** (0.2715, 0.2355, 0.2559, 0.2849, 0.2170) — that is **scatter, not a trend**. The exponent 0.926 is consistent with 1.0 given 16 % residual. **F1266's refutation is withdrawn as under-powered.**

**What survives, and it is the user's original point:** N/dim is **≈ 0.25 ± 0.03 with ~15 % substrate-dependent wobble**, and a single power law does not fit it (the harness flags this itself). It is *not* a pi-like constant to be pinned to more decimals. The "magic number" framing is still wrong; the correction is that the relation is nearer to linear than F1266 claimed.

## PART 2 — the "geometry-less fractal" reading loses its number
The form of the reasoning is right: **a non-integer scaling exponent is the fingerprint of self-similar structure and needs no embedding geometry** — that is exactly what a Hausdorff dimension is, a scaling relation rather than a shape. If capacity scaled robustly as dim^0.585, "fractal" would be the natural reading and 0.585 would *be* the dimension.

**The problem is that the number moved.** At **0.926 with 16 % scatter**, the deviation from linear is not measured well enough to call fractal — asserting it would be reading structure into noise, which is precisely the error made twice already in this chain (dyadic N/dim in F1265; ceiling-as-plateau in F1266). **To claim it you would need the exponent stable, reproducibly ≠ 1, across more dims and at a second threshold level.** That is a concrete experiment, not a refusal.

## PART 3 — Cayley-Dickson: NOT supported
F1266's working chunk divisors were 16, 8, 4 — which coincide with C/H/O/S = 2/4/8/16. **But I chose those divisors.** Swept k = 2…24 including the non-CD values (dim 2048, M 3000):

| k | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 12 | 14 | 16 | 20 | 24 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| recall | 0.417 | 0.583 | **0.750** | 0.917 | 0.917 | 1.000 | **0.917** | 1.000 | 0.917 | 1.000 | 1.000 | **1.000** | 1.000 | 1.000 |

| | mean \|Δ\| entering |
|---|---|
| CD divisors {2,4,8,16} | **0.0833** (n=3) |
| non-CD divisors | **0.0667** (n=10) |

A 1.25× difference, well under the 1.8× bar. **The curve is smooth in k and saturates near k = 7.** No feature at the CD points. **The tower resemblance was the sampling grid** — the same trap as the dyadic N/dim, one level up, and the user flagged it in the same breath as raising it (*"these don't look magic"*).

## The methodological thread — this is the fourth instance
F1265 (dyadic sampling → false thresholds) → F1266 (ceiling read as plateau; 2-point trend read as a law) → F1267 (coarse ladder → wrong exponent; chosen divisors → false CD structure). **The recurring failure is reading structure out of a grid I chose.** The fix that has worked every time is the same: **sample off the grid the hypothesis lives on**, and prefer a threshold crossing to a ladder step. Worth treating as standing method, not four separate lessons.

## Verdict / next
`N_crit ∝ dim^0.926`, residual 16 %, no clean power law. N/dim ≈ 0.25 ± 0.03 — **a rough relation with substrate wobble, not a constant**. No Cayley-Dickson structure in chunk size. The fractal reading is **not refuted** — it is **un-measured**, because the exponent it depended on was an artifact.

**NEXT:** (a) exponent at a second threshold (recall 0.25 and 0.75) across the same five dims — if the exponent is *threshold-dependent*, no single power law exists and that is itself the answer; (b) more dims (512 … 16384) to see whether 0.926 is stable or drifts; (c) only if the exponent proves stable and ≠ 1, revisit the fractal-dimension reading with a number that can carry it.

Composes **F1266** (its ratio-law refutation withdrawn as under-powered; its CD-divisor coincidence explained as sampling), **F1265**, **F1264**, **F1263**, `[[feedback_read_independent_structure_check_first]]`, `[[feedback_dont_pre_commit_spike_query_operators]]` (don't lean the query toward the expected result — the grid was doing exactly that), DUALITY.md / TRIALITY.md (the CD ladder tested and not found here), #231/PKG-3.
