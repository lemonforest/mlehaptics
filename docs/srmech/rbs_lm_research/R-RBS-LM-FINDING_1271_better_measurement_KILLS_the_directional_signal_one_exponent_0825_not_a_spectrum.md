# F1271 — TAILFIX (n=80 probes, 13-point ladder to 4.3×) **kills the directional signal**: adjacent-pairs-in-direction goes **6/8 → 4/8**, p **0.042 → 0.715** (4/8 is exactly chance), and the α spread **halves** (0.084 → 0.043) to sit **well inside** the max residual (0.101). **The threshold-dependence / multifractal-spectrum reading is NOT supported by this object. What survives is cleaner: ONE exponent, α ≈ 0.825, flat across all nine thresholds.** F1269's turn-up is gone — and so is the "well-measured" monotone run I said I trusted most.

**User (2026-07-20):** chose *"2"* — measure better rather than trim the band post-hoc — and *"report both p-values side by side."*

## Both runs, identical thresholds
| threshold | OLD n=50 / 8-pt | NEW n=80 / 13-pt | shift |
|---|---|---|---|
| 0.91 | 0.896 (r 0.154) | **0.832** (r 0.068) | −0.064 |
| 0.84 | 0.876 (r 0.073) | **0.805** (r 0.038) | −0.071 |
| 0.76 | 0.871 (r 0.057) | **0.803** (r 0.040) | −0.068 |
| 0.69 | 0.857 (r 0.042) | **0.810** (r 0.032) | −0.047 |
| 0.62 | 0.828 (r 0.035) | **0.840** (r 0.092) | +0.012 |
| 0.55 | 0.812 (r 0.048) | **0.843** (r 0.086) | +0.031 |
| 0.48 | 0.817 (r 0.078) | **0.846** (r 0.076) | +0.029 |
| 0.40 | 0.853 (r 0.075) | **0.834** (r 0.067) | −0.019 |
| 0.33 | 0.830 (r 0.067) | **0.816** (r 0.101) | −0.014 |

| run | adjacent-in-direction | **p(≥)** | spread | max resid | monotone |
|---|---|---|---|---|---|
| OLD (n=50, 8-pt) | 6/8 | **0.0416** | 0.084 | 0.154 | NO |
| **NEW (n=80, 13-pt)** | **4/8** | **0.7152** | **0.043** | 0.101 | NO |

**4/8 is exactly chance.** The signal is gone.

## The check I most needed also failed
F1269 recorded: *"the clean monotone run (0.896 → 0.812 across the top six) is the part I trust most … if it doesn't reproduce, the whole directional signal was noise."* **It did not reproduce.** All four top thresholds dropped 0.05–0.07. The monotone run was an artefact of the coarser ladder, exactly as the pre-registered falsifier specified — and the falsifier fired against the hypothesis, which is what makes it worth having written down in advance.

## What survives — and it is a better result than the spectrum
**α ≈ 0.825, constant across thresholds.** Spread 0.043 vs max residual 0.101: the variation is *entirely* inside the noise. There is **one exponent**, not a spectrum.

Sequence of this quantity across the chain — every move a measurement fix, never new structure:
| | α | why it moved |
|---|---|---|
| assumed | 1.000 | the ratio law, never measured |
| F1266 | 0.585 | 2 points on a 1.5× ladder (inseparable from sampling) |
| F1267 | 0.926 | n=6 probes (sd 0.204) |
| F1268 | 0.801 | n=50, 5 dims, 3 thresholds |
| **F1271** | **≈0.825** | n=80, 13-pt ladder, 9 thresholds, threshold-independent |

## Scope of the negative, stated precisely
This falsifies the **directional consequence** — that α should order with threshold — **for this object**. It does **not** touch the partial-excitation frame generally: a *constant* α is fully consistent with excitation being uniform across the load range this particular observable spans. **What died is a prediction, not the frame**, and the distinction matters because the frame did real work — it retired my 11/14 value-hunt (F1269), which was numerology in framework clothing, and it correctly reframed the pooled read as fixed-vs-varying excitation.

## The methodological pattern — seventh instance
F1265 (dyadic grid → false thresholds) → F1266 (ceiling read as plateau; 2-point trend read as a law) → F1267 (coarse ladder → wrong exponent; chosen divisors → false CD structure) → F1268 (n=6 → non-monotone curves) → **F1271 (8-pt ladder → false directional trend)**. **Every single one dissolved under better measurement.** Not one apparent structure in this chain has survived being measured properly.

The standing method that has worked every time: **sample off the grid the hypothesis lives on; prefer a threshold crossing to a ladder step; pre-register the falsifier; and when the spread is comparable to the residual, decline to call it.** F1269 declined the harness's own "NO single power law" verdict on exactly that basis — and was right to.

## Honest bound, still standing
Both p-values are **optimistic upper bounds**: α's within a run are not independent (one curve per dim, overlapping interpolation intervals). And the tail remains the flat part of a sigmoid — TAILFIX made it *better* measured, not *well* measured (dim=2048 tail deltas still read `+0.020 −0.012 +0.122 −0.049` at n=80). Neither caveat changes the verdict, since the negative is driven by the *well*-measured region reversing.

## Verdict / next
**Directional prediction: NOT SUPPORTED.** Spectrum reading: **dead for this object.** Settled: **α ≈ 0.825, one exponent, threshold-independent.**

**NEXT:** (a) treat α ≈ 0.825 as the settled capacity scaling and stop re-measuring it — the sequence above is five revisions of one number and further precision has diminishing value against its actual use (sizing chunked stores, F1266); (b) the **𝕊-boundary probe** from F1270, which is a structural question rather than a fitted one and therefore not vulnerable to this failure mode; (c) if the spectrum question is ever reopened, it needs an observable with a *wider dynamic range*, not more probes on this one.

Composes **F1269** (whose 6/8 p=0.042 is withdrawn here, by its own pre-registered falsifier), **F1268**, **F1267**, **F1266**, **F1265**, **F1270** (lodged together), `[[feedback_read_independent_structure_check_first]]`, `[[feedback_dont_pre_commit_spike_query_operators]]`, `[[feedback_computational_provenance_discipline]]`, #231/PKG-3.
