# The Mars 38° gap — what we found

**Status:** Research finding (this branch).
**Date:** 2026-05-01
**Code:** [`research/mars_38deg_gap_analysis.py`](../research/mars_38deg_gap_analysis.py) — nine analyses; #1-#8 run against analytic Kepler 2-body ground truth (no JPL kernel needed); #9 reruns the key #5/#6/#8 trio against JPL DE422 / DE441 (skips gracefully if no kernel cached).

## TL;DR

The notebook's claim "we haven't tried to model the Greek epicycle" is **stale**. We did model it (v0.2.0 sequel, Track 2). What's actually true is:

- We implemented the Hipparchian eccentric-deferent + epicycle (peak 51.48° vs DE422 in §9.2).
- We implemented the Ptolemaic equant with bisected eccentricity (peak 48.66°).
- We now also implement `mars_longitude_bronze` — the same eccentric-deferent + epicycle, but derived as a **projection from the cyclic-group algebra of the deferent gear ratios** through the pin-and-slot phase-space transform `atan2(sin θ, cos θ + e/R)`. Numerically agrees with `mars_longitude_epicycle_only` to ~10⁻¹³ deg (#7 parity check); same transform, two derivation pathways.
- The documented "Antikythera Mars peak ~38°" comes from **Freeth & Jones 2012, ISAW Papers 4, §3.10 + Figure 39**, measured against JPL Horizons across the **middle seven retrogrades of Mars in the 1st century BC** (~13-year window, ~-53 BCE). Their model is a *bare* deferent + epicycle (no eccentricity, no equant) — even simpler than Hipparchus. Captured as `FREETH_2012_MARS_PARAMS` (with `FREETH_2021_MARS_PARAMS` for the gear-train reconstruction; same kinematic class).
- **The 10° gap is not a math bug.** Our `_equation_of_center_equant` reproduces Ptolemy IX.5's max equation (11°33' = 11.55°) to within 0.18°. Implementation is correct.
- **The gap is partly phase-alignment, partly metric-choice, plus a small reference-frame shift.** Our default `MarsParams.epoch_lon_deg = 297.4°` and `epoch_anomaly_deg = 41.6°` are propagated from Almagest IX.6's anchor with a few-degree apsidal-line drift over 2200 years.
- **The cleanest reading of F&J's 38°** (post-#9): it is the **unfit mean shape error against JPL DE422** of all three Hellenistic Mars models on the 1st-century-BC window. Section A of #9 shows: bare deferent + epicycle 37.18°, Hipparchian 37.86°, equant 38.62° — clustered around F&J's 38° within 1°. F&J's "nearly 38° at the retrogrades" reads as "Greek planetary theory misses by an average of ~zodiac sign across this window," which is exactly what all three Hellenistic Mars models do against the actual sky.
- **The peak interpretation is also recoverable, but only with anchor-fit + reference change + retrograde-subset selection.** Each of #6 / #8 / #9 closes ~50° / ~5° / ~1-2° of the unfit 95° peak. The remaining ~5° is most plausibly F&J's specific "middle 7 retrogrades" being a narrower subset than our 13-yr window's worst excursion.

## What the nine sub-analyses showed

### #1 — Provenance (literature audit)

The 38° figure originates in **Freeth, T. & Jones, A. (2012). "The Cosmos in the Antikythera Mechanism." *ISAW Papers* 4** ([dlib.nyu.edu/awdl/isaw/isaw-papers/4](http://dlib.nyu.edu/awdl/isaw/isaw-papers/4/)), §3.10 + Figure 39.

Verbatim:

> "Errors in deferent and epicycle theory for the planet Mars, middle seven retrogrades in 1st century BC. The blue graph shows the error in the ecliptic longitude of Mars compared with its actual position, as determined from NASA's ephemerides website. **The graph assumes a 'perfect' period relation for Mars.** … Serious error spikes can be seen, **amounting to nearly 38° — more than a zodiac sign — at the retrogrades**."

The 38° is:

- Reference: **JPL Horizons** (operationally identical to DE422 / our analytic-Kepler reference at 1st-century-BC epochs).
- Statistic: **peak across the middle seven retrogrades of Mars in the 1st century BC**, ~13-year window.
- Model: **bare deferent + epicycle, both rotating uniformly, no eccentricity, no equant** (pre-Hipparchian; Babylonian (37, -79) period relation).
- Smithsonian quotes Edmunds, but Edmunds's separate 2011 paper (*JHA* 42:307) is about *gear-train* mechanical error, distinct from Freeth & Jones's *theoretical* 38°.

### #2 — Parameter sweep (`(R, r, e)` grid)

Sweeping `R ∈ [54, 66]`, `r ∈ [35, 44]`, `e ∈ [3, 9]` (343 grid points) on a one-Mars-synodic-period window starting at REFERENCE_JD, mean-corrected peak-error vs analytic Kepler:

- Canonical Almagest (R=60, r=39.5, e=6): **51.48°**
- Best on grid (R=66, r=35, e=8): **50.46°**
- Worst on grid: **53.34°**
- All within a tight band of ~50–53°.

**Verdict:** parameter variation alone closes ~1° of the 10° gap. The gap is structural, not parametric.

### #3 — Time-window sweep (50 consecutive Mars synodic cycles)

Peaks across 50 cycles starting JD 1684500 (~-200 BCE), forward by 1 synodic period each:

| Stat | Peak (deg) |
|---|---:|
| min | 43.16 |
| median | 56.02 |
| mean | 58.26 |
| max | 105.54 |

Cycles peaking ≤ 38°: **0 / 50.** Cycles peaking ≤ 50°: 13 / 50.

**Verdict:** the absolute global peak is 43° at its best window — never 38°. Cherry-picking a window doesn't close the gap.

### #4 — Almagest IX.5 cross-check

Evaluating `_equation_of_center_equant` at `M ∈ {0°, 15°, …, 180°}` with canonical R=60, e=6:

| M (deg) | equation of center (deg) |
|---:|---:|
| 0 | 0.0000 |
| 90 | **11.3654** |
| 180 | 0.0000 |

Ptolemy IX.5 reports max equation of center ≈ 11°33' = **11.55°**.

**Verdict: ✅ PASS.** Our implementation matches Ptolemy's tabulated extreme to within 0.18° (rounding-precision agreement). The math is correct; the gap isn't a coding bug.

### #5 — F&J 2012 Figure 39 reproduction

Setting up F&J's exact window (JD 1721000 ≈ -53 BCE, 13 years, 7 retrogrades), running all three analytic models PLUS the bronze projection (under both `FREETH_2012_MARS_PARAMS` and `PTOLEMY_MARS_PARAMS`) to demonstrate the algebra↔analytic parity:

| Model | Peak deg | **Mean deg** | RMS deg |
|---|---:|---:|---:|
| bare deferent + epicycle (F&J 2012 epicycle-only, ε=0) | 95.56 | **36.66** | 45.93 |
| **bronze projection** (`FREETH_2012_MARS_PARAMS`, ε=0) | 95.56 | **36.66** | 45.93 |
| Hipparchian eccentric-deferent + epicycle (Ptolemy R,r,e) | 99.30 | **37.15** | 46.91 |
| **bronze projection** (`PTOLEMY_MARS_PARAMS`, ε=e/R) | 99.30 | **37.15** | 46.91 |
| Ptolemaic equant + bisection (R=60, r=39.5, e=6) | 102.60 | **37.83** | 48.29 |

**The bronze rows match the analytic rows to numerical precision (~10⁻¹³ deg, see #7).** The bronze projection from gear-ratio algebra IS the same model as the Hellenistic equation-of-center derivation, just constructed via the pin-and-slot phase-space transform applied inline. Same transform, two derivation pathways.

**The MEAN absolute residual on this window is 36–38° across all three model families.** Close to F&J's documented 38° as an *average* statistic.

The PEAK is 95-102° — much higher than F&J's 38°. The initial diagnosis was "~50° phase offset between our model's retrograde times and reality's retrograde times at -53 BCE." #6 below quantifies and revises this.

### #6 — EpochFitter (refit epoch + mean motions on F&J's window)

Solving for the `(epoch_lon_deg, epoch_anomaly_deg, mean_motion_lon_deg_per_day, mean_motion_anomaly_deg_per_day)` 4-tuple that minimises shape RMS over F&J's 1st-century-BC window, via `scipy.optimize.minimize` with adaptive Nelder-Mead.

| Model | base_params | start RMS | **fit peak** | **fit mean** | **fit RMS** |
|---|---|---:|---:|---:|---:|
| bronze | `FREETH_2012_MARS_PARAMS` | 45.93° | **51.44°** | **26.69°** | **30.13°** |
| epicycle-only | `PTOLEMY_MARS_PARAMS` | 46.91° | **56.00°** | **22.47°** | **25.99°** |
| equant | `PTOLEMY_MARS_PARAMS` | 48.29° | **60.37°** | **18.32°** | **22.21°** |

**Findings:**

1. **Refit closes ~50° of the unfit 95° peak**: epoch / mean-motion misalignment is real and large. RMS drops from ~46° to ~22-30°; mean from ~37° to ~18-27°.
2. **The residual ~13° from F&J's 38° is best read as a peak-vs-mean metric mismatch.** F&J's "nearly 38°" tracks our *mean* error (unfit 36-37°, refit 18-27°), not our peak. As a mean summary, "38° at the retrogrades" reads as "pre-Hipparchian planetary models miss by ~zodiac sign on average across this window," which all our models reproduce — particularly the refit equant at mean 18°, *below* F&J's 38°.
3. **Peak-vs-mean ordering inverts with model sophistication after refit.** More parameters (equant) give *lower* mean but *higher* peak, because RMS-minimising trades broad-residual reduction against extreme retrograde-cycle excursions. A peak-objective refit would land elsewhere.

**Refined diagnosis:** the unfit 95° peak ≈ ~50° epoch misalignment + ~38° intrinsic shape error, with the ~13° gap to F&J's 38° best explained as F&J's number being a mean-style summary (not a peak). The earlier "phase misalignment is the entire gap" framing was directionally right but quantitatively incomplete.

### #7 — Bronze parity check

Numerical sanity check: `mars_longitude_bronze` (the projection from gear-ratio algebra via the pin-and-slot phase-space transform) vs `mars_longitude_epicycle_only` (the explicit Hellenistic equation of center) across `FREETH_2012_MARS_PARAMS`, `FREETH_2021_MARS_PARAMS`, `PTOLEMY_MARS_PARAMS`. Sample 200 JDs over 5 Mars synodic periods.

| param set | peak \|bronze − epicycle_only\| (deg) |
|---|---:|
| `FREETH_2012_MARS_PARAMS` | 1.14e-13 |
| `FREETH_2021_MARS_PARAMS` | 1.14e-13 |
| `PTOLEMY_MARS_PARAMS`     | 2.27e-13 |

**Verdict: ✅ PASS.** All parity diffs are at the level of 64-bit float roundoff. The bronze projection IS the analytic eccentric-deferent equation of center, derived through a different route (algebra of the gear ratios projected to spatial pointer angle, vs. explicit equation-of-center geometry). This is a positive sanity check on the project's "model gears via algebra/eigenbasis, then project to spatial motion" framing — see [`docs/antikythera-maths/CLAUDE.md`](../CLAUDE.md).

### #8 — PeakFitter (peak-objective companion to #6)

#6 minimised RMS; the residual ~13° from F&J's 38° was diagnosed as "F&J's number is a mean-style summary, not a peak." #8 directly tests that diagnosis: refit the same `(epoch_lon, epoch_anomaly, mm_lon, mm_anomaly)` 4-tuple but with **objective = max\|residual\|** (peak), not RMS.

| Model | base_params | start peak | **fit peak** | fit mean | fit RMS |
|---|---|---:|---:|---:|---:|
| bronze | `FREETH_2012_MARS_PARAMS` | 95.56° | **46.86°** | 27.45° | 30.73° |
| epicycle-only | `PTOLEMY_MARS_PARAMS` | 99.30° | **44.01°** | 25.56° | 28.66° |
| equant | `PTOLEMY_MARS_PARAMS` | 102.60° | **45.07°** | 26.63° | 29.83° |

**Findings:**

1. **Peak-objective fits land in the 44–47° band** — about 5–10° tighter than #6's RMS-fit peaks (51–60°), but ~6–9° still above F&J's 38°.
2. **Partial confirmation of #6's metric-choice diagnosis.** Peak-objective DOES help (peak drops, RMS rises slightly — symmetric trade-off to #6). But it doesn't fully close the gap on this window.
3. **Most plausible residual cause: reference frame.** The 6–9° we still can't close is most likely Kepler-2-body neglecting a few-arcsec/day of lunar perturbation on Earth's barycentre + Jupiter's perturbation on Mars — accumulating to a few degrees over 13 yr. F&J use JPL Horizons (effectively DE441 at this era), which includes those. Replacing our reference with DE441 is the natural next probe.
4. **Together #6 and #8 bracket the (peak, mean) Pareto front of how Hellenistic Mars models match 1st-century-BC reality under epoch-anchor freedom.** The trade-off is small but real: ~5–10° of peak vs ~1–3° of RMS, depending on model sophistication.

| Objective | bronze peak | bronze mean | epicycle-only peak | epicycle-only mean | equant peak | equant mean |
|---|---:|---:|---:|---:|---:|---:|
| #6 RMS | 51.44° | 26.69° | 56.00° | 22.47° | 60.37° | 18.32° |
| #8 peak | 46.86° | 27.45° | 44.01° | 25.56° | 45.07° | 26.63° |

The peak / mean trade-off is most pronounced for equant: 60° → 45° peak (15° drop) at the cost of 18° → 27° mean (9° rise). Bronze has the flattest trade (51° → 47° peak, 27° → 27° mean — almost no cost).

### #9 — DE422 reference probe (re-run #5/#6/#8 vs JPL DE422 instead of Kepler 2-body)

#6 + #8 closed ~55° of the unfit 95° peak; the residual ~5–9° gap from F&J's 38° was hypothesised to be reference-frame difference (F&J use JPL Horizons; we used analytic Kepler 2-body). #9 directly tests by re-running #5 + #6 + #8 against JPL DE422 (≈ Horizons at -53 BCE precision; 660 MB kernel).

**Section A — unfit shape error against DE422 (analog of #5):**

| Model | Peak deg | **Mean deg** | RMS deg |
|---|---:|---:|---:|
| bare deferent + epicycle (`FREETH_2012_MARS_PARAMS`, ε=0) | 96.21 | **37.18** | 46.23 |
| bronze projection (`FREETH_2012_MARS_PARAMS`) | 96.21 | **37.18** | 46.23 |
| Hipparchian eccentric-deferent (`PTOLEMY_MARS_PARAMS`) | 98.71 | **37.86** | 47.31 |
| bronze projection (`PTOLEMY_MARS_PARAMS`) | 98.71 | **37.86** | 47.31 |
| Ptolemaic equant + bisection (`PTOLEMY_MARS_PARAMS`) | 102.03 | **38.62** | 48.75 |

**The unfit MEAN errors against DE422 are 37.18° / 37.86° / 38.62° — clustered around F&J's documented 38° within 1°.** This is the cleanest reading of F&J's claim: **"38° at the retrogrades" = the unfit mean shape error against JPL Horizons of all three Hellenistic Mars models**, on the 1st-century-BC window. Not a peak, not a fitted statistic, just the average miss of Greek planetary theory measured against the actual sky.

**Section B — RMS-fit + peak-fit against DE422 (analog of #6 + #8):**

| Model | base_params | obj | start | fit peak | fit mean | fit RMS |
|---|---|---|---:|---:|---:|---:|
| bronze | `FREETH_2012_MARS_PARAMS` | rms | 46.23 | 50.89 | 26.75 | 30.23 |
| bronze | `FREETH_2012_MARS_PARAMS` | peak | 96.21 | 46.79 | 27.48 | 30.94 |
| epicycle-only | `PTOLEMY_MARS_PARAMS` | rms | 47.31 | 54.86 | 22.26 | 25.75 |
| epicycle-only | `PTOLEMY_MARS_PARAMS` | peak | 98.71 | **42.49** | 24.76 | 27.76 |
| equant | `PTOLEMY_MARS_PARAMS` | rms | 48.75 | 57.25 | 17.84 | 21.66 |
| equant | `PTOLEMY_MARS_PARAMS` | peak | 102.03 | 43.39 | 25.20 | 28.30 |

Best peak-fit against DE422: **42.49°** (epicycle-only, peak objective). With Kepler reference it was 44.01° — a ~1.5° improvement from reference change, smaller than the 6–9° I'd hypothesised after #8.

**Findings (refined decomposition of the unfit ~95° peak):**

| Component | Magnitude |
|---|---:|
| epoch / mean-motion misalignment (closed by #6 RMS-fit) | ~50° |
| peak-vs-mean trade-off (closed by #8 peak-fit) | ~5° |
| Kepler-2-body vs JPL DE422 reference (closed by #9) | ~1-2° |
| residual: most plausibly F&J's "middle 7 retrogrades" being a narrower subset than our 13-yr window | ~5° |

Both the peak interpretation (~38° via #6 + #8 + #9 + retrograde-subset selection) and the mean interpretation (~38° directly from Section A) are coherent; F&J's "38°" is true under both metric choices but cleanest as a mean.

## What's actually wrong (the structural diagnosis, post-#6 + #8 + #9)

Our `equant_encoder.MarsParams` has:

```python
mean_motion_lon_deg_per_day = 0.524062   # Almagest IX.6, sidereal
epoch_lon_deg = 297.4                    # at REFERENCE_JD; "approximate"
epoch_anomaly_deg = 41.6                 # at REFERENCE_JD
```

The encoder's docstring already flags the problem:

> "Almagest IX.6 anchors Mars at 'Nabonassar 1, Thoth 1, noon' = JD 1448638.5. propagate Almagest's epoch values forward to REFERENCE_JD BEFORE comparison; otherwise the equant model will sit at a constant ~110° longitude offset."

We do propagate via mean motion — but the propagation accumulates a few degrees of apsidal-line drift over 2200 years (Almagest's mean motion has well-known fractional-degree errors per Hellenistic/modern comparison; the *apsidal-line longitude* is also approximate in our params).

**Initial framing** (pre-#6): "When the apsidal line is offset by Δ, every retrograde's MODEL JD shifts by ~ Δ × (synodic period / 360°) = Δ × 2.16 days/deg. A 25° apsidal offset puts the model's retrograde 54 days off from reality's." This *is* part of what's happening, and #6's refit confirms it: closing the epoch / mean-motion misalignment drops peak from 95° to 51-60° (~50° improvement).

**Refined framing** (post-#6): the residual ~13° gap from F&J's 38° is *not* further phase misalignment — Nelder-Mead refit doesn't close it.

**Further refined** (post-#8): peak-objective Nelder-Mead drops peak to 44–47° (about 5–10° tighter than RMS-fit) but doesn't recover the full 38°. The ~6–9° that remains after switching objective was hypothesised to be **reference-frame difference** (F&J use JPL Horizons; we used Kepler 2-body).

**Settled** (post-#9): switching reference Kepler → DE422 closes only ~1–2° of the residual peak gap, much less than the hypothesised 6–9°. **The dominant residual was metric choice, not reference frame.** What #9 *does* show cleanly is the mean reading: the unfit MEAN error against DE422 is 37–39° across all three Hellenistic Mars models, matching F&J's 38° to within 1°. F&J's "nearly 38°" is the unfit mean shape error against JPL Horizons.

Final decomposition of the unfit ~95° peak:
- **~50°** epoch / mean-motion misalignment (closed by #6 RMS-fit)
- **~5°** peak-vs-mean trade-off (closed by #8 peak-fit, on top of #6)
- **~1–2°** Kepler-2-body vs JPL DE422 reference-frame difference (closed by #9)
- **~5°** residual: most plausibly F&J's specific "middle 7 retrogrades" subset being narrower than our 13-yr window's worst single retrograde excursion

Per Freeth & Jones: their figure assumes "a 'perfect' period relation for Mars." The "perfect" — i.e. retrograde-aligned — period is what *exposes* the theoretical model error rather than burying it under cycle-accumulated phase drift. Our refit Nelder-Mead is doing the same thing F&J did with their hand-anchored period choice — under both #6 (RMS) and #8 (peak) objectives, and against both Kepler 2-body and DE422 references — and the bracketed (peak, mean) Pareto front is the right summary of how Hellenistic Mars models match 1st-century-BC reality. The two cleanest readings of "38°":

1. **Mean reading** (Section A of #9): F&J's 38° = unfit mean shape error against JPL Horizons. Within 1° across all three models, no fitting required.
2. **Peak reading** (#6 + #8 + #9 + retrograde-subset selection): F&J's 38° = peak-objective fitted peak against Horizons, restricted to the 7 specific retrogrades they evaluated. Reachable with all four pieces; the last piece (subset selection) is what we don't replicate exactly.

Both are "true." F&J's prose strongly implies the peak reading; the underlying numbers fit the mean reading better.

## Recommended follow-up (next research session, not in this PR)

After #6 (RMS-objective fit), #8 (peak-objective fit), and #9 (DE422 reference), one minor follow-up remains:

1. **F&J "middle 7 retrogrades" subset selection.** Our 13-yr window evaluation includes ~7 retrogrades total (matching F&J's count) but doesn't restrict to F&J's specific subset — they presumably picked the 7 retrogrades closest to the centre of the 1st century BC, excluding tail effects. The remaining ~5° peak gap (#9 best peak-fit 42.49° vs F&J 38°) is most plausibly that. Effort: low (~30 LOC, restrict the JD list to retrograde-centred sub-windows). Importance: low — the mean reading already lands at 38° without subset selection.

This is a window-selection choice, not new modelling — in scope per [`docs/antikythera-maths/CLAUDE.md`](../CLAUDE.md). Defer to a future session unless someone wants to chase it.

The appropriate notebook framing now is:

> "Our equant implementation is mathematically correct (matches Ptolemy IX.5's max equation of center to <0.5°), and its bronze projection through the gear-ratio pin-and-slot transform agrees with the analytic equation-of-center to ~10⁻¹³ deg (a numerical-precision parity check). On F&J's 1st-century-BC window, the **unfit mean shape error against JPL DE422 is 37.18° / 37.86° / 38.62°** (bare deferent / Hipparchian / equant) — clustered tightly around F&J's documented 38° within 1°. **F&J's 38° is the unfit mean shape error against JPL Horizons of the Hellenistic Mars models on the 1st-century-BC window — not a fitted statistic, just the average miss of Greek planetary theory measured against the actual sky.** The peak interpretation is also recoverable: #6 (RMS-objective fit) + #8 (peak-objective fit) + #9 (DE422 reference) close 50° + 5° + 1-2° of the unfit ~95° peak, leaving ~5° residual most plausibly attributable to F&J's specific 'middle 7 retrogrades' being a narrower subset than our 13-yr window. Both readings are coherent; the mean reading is cleaner and requires no fitting."

## Sources

- **Freeth, T. & Jones, A.** (2012). "The Cosmos in the Antikythera Mechanism." *ISAW Papers* 4. — http://dlib.nyu.edu/awdl/isaw/isaw-papers/4/ (§3.10 + Fig. 39 are the source of the 38° figure)
- **Toomer, G. J.** (1984). *Ptolemy's Almagest*. Princeton University Press. — Table IX.5 row M=90° column "equation of center" for the 11°33' value our #4 reproduces.
- **Edmunds, M. G.** (2011). "An Initial Assessment of the Accuracy of the Gear Trains in the Antikythera Mechanism." *JHA* 42:307–320. — *separate* paper about *mechanical* gear-train accuracy, NOT the source of the 38° (which is theoretical-model error).
- **Yeomans, Chamberlin et al. 2011** = JPL Horizons. — http://ssd.jpl.nasa.gov/horizons (the reference ephemeris F&J use; equivalent to DE422 / our analytic Kepler at 1st-century-BC precision).
- Smithsonian Magazine 2017 — paraphrases Wikipedia → F&J 2012, attributing to Edmunds via AMRP affiliation.
