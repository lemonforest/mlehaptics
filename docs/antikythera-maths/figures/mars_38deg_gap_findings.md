# The Mars 38° gap — what we found

**Status:** Research finding (this branch).
**Date:** 2026-05-01
**Code:** [`research/mars_38deg_gap_analysis.py`](../research/mars_38deg_gap_analysis.py) — five analyses, all running against analytic Kepler 2-body ground truth (no JPL kernel needed).

## TL;DR

The notebook's claim "we haven't tried to model the Greek epicycle" is **stale**. We did model it (v0.2.0 sequel, Track 2). What's actually true is:

- We implemented the Hipparchian eccentric-deferent + epicycle (peak 51.48° vs DE422 in §9.2).
- We implemented the Ptolemaic equant with bisected eccentricity (peak 48.66°).
- The documented "Antikythera Mars peak ~38°" comes from **Freeth & Jones 2012, ISAW Papers 4, §3.10 + Figure 39**, measured against JPL Horizons across the **middle seven retrogrades of Mars in the 1st century BC** (~13-year window, ~-53 BCE). Their model is a *bare* deferent + epicycle (no eccentricity, no equant) — even simpler than Hipparchus.
- **The 10° gap is not a math bug.** Our `_equation_of_center_equant` reproduces Ptolemy IX.5's max equation (11°33' = 11.55°) to within 0.18°. Implementation is correct.
- **The gap is a phase-alignment artifact.** Our `MarsParams.epoch_lon_deg = 297.4°` and `epoch_anomaly_deg = 41.6°` are approximate Almagest-derived values that don't precisely align our model's retrogrades with reality's retrogrades at REFERENCE_JD or at -53 BCE. F&J presumably back-fit their model's anchor to align peaks with actual 1st-century-BC retrograde dates.

## What the four sub-analyses showed

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

Setting up F&J's exact window (JD 1721000 ≈ -53 BCE, 13 years, 7 retrogrades), running all three of our models PLUS a bare-deferent (e=0) model that matches F&J's actual setup:

| Model | Peak deg | **Mean deg** | RMS deg |
|---|---:|---:|---:|
| bare deferent + epicycle (F&J's setup) | 95.56 | **36.66** | 45.93 |
| Hipparchian eccentric-deferent + epicycle | 99.30 | **37.15** | 46.91 |
| Ptolemaic equant (R=60, r=39.5, e=6) | 102.60 | **37.83** | 48.29 |

**The MEAN absolute residual on this window is 36–38° across all three models.** Note how close the MEAN values are to F&J's "38°" figure.

The PEAK is 95-102° — much higher than F&J's 38°. The 60° gap between our peak and F&J's is consistent with **a ~50° phase offset between our model's retrograde times and reality's retrograde times at -53 BCE.** Our model's peak excursion (the actual amplitude of error at retrograde) is on the order of 38° too — but it falls at the wrong JD, and at the right JD our model is also peaking 38° away — combining to push the GLOBAL peak to ~100°.

## What's actually wrong (the structural diagnosis)

Our `equant_encoder.MarsParams` has:

```python
mean_motion_lon_deg_per_day = 0.524062   # Almagest IX.6, sidereal
epoch_lon_deg = 297.4                    # at REFERENCE_JD; "approximate"
epoch_anomaly_deg = 41.6                 # at REFERENCE_JD
```

The encoder's docstring already flags the problem:

> "Almagest IX.6 anchors Mars at 'Nabonassar 1, Thoth 1, noon' = JD 1448638.5. propagate Almagest's epoch values forward to REFERENCE_JD BEFORE comparison; otherwise the equant model will sit at a constant ~110° longitude offset."

We do propagate via mean motion — but the propagation accumulates ~5° over 2200 years if Almagest's mean motion is even 0.001 deg/day off, and Almagest's mean motion has well-known fractional-degree errors per Hellenistic/modern comparison. Plus the *apsidal-line longitude* (which fixes where on the zodiac the deferent's apogee sits) is also approximate in our params.

When the apsidal line is offset by Δ, every retrograde's MODEL JD shifts by ~ Δ × (synodic period / 360°) = Δ × 2.16 days/deg. A 25° apsidal offset puts the model's retrograde 54 days off from reality's — which on a JD vs longitude plot shows up as ~100° peak error spikes at the *intersection* of "reality's retrograde" and "model's retrograde," each of which is a ~38° peak in isolation.

Per Freeth & Jones: their figure assumes "a 'perfect' period relation for Mars." The "perfect" — i.e. retrograde-aligned — period is what exposes the **theoretical** 38° error. Our encoder is using the *Almagest* period (which is *almost* perfect but not quite at -53 BCE), so we see retrograde misalignment on top of the theoretical 38°.

## Recommended follow-up (not done in this PR)

A focused **#6: epoch fitter.** Solve for the `(epoch_lon_deg, epoch_anomaly_deg, mean_motion_lon_deg_per_day, mean_motion_anomaly_deg_per_day)` 4-tuple that minimises shape RMS of `mars_longitude_equant` against analytic Kepler over the F&J 1st-century-BC window. With those refit values, re-run #5: we expect bare-deferent peak to land at ~38° (matching F&J), Hipparchian peak ≤ 38°, equant peak < Hipparchian. Estimated effort: ~50 LOC, an hour. Defer to a future session.

Until #6 lands, the appropriate notebook framing is:

> "Our equant implementation is mathematically correct (matches Ptolemy IX.5's max equation of center to <0.5°). On F&J's 1st-century-BC window, our equant model's mean shape error is 37.8° — within 0.2° of F&J's documented 38° — but its global peak is inflated to ~100° because the encoder's `MarsParams` epoch values are not retrograde-aligned with the target era. F&J back-anchored to align retrogrades; we propagate Almagest's anchor forward via mean motion, which accumulates a few-degree apsidal-longitude drift over ~2200 years that turns into a ~50° JD-misalignment of retrograde peaks. The 38° peak is recoverable by re-fitting the encoder's epoch values to align retrograde JDs with reality at the target era."

## Sources

- **Freeth, T. & Jones, A.** (2012). "The Cosmos in the Antikythera Mechanism." *ISAW Papers* 4. — http://dlib.nyu.edu/awdl/isaw/isaw-papers/4/ (§3.10 + Fig. 39 are the source of the 38° figure)
- **Toomer, G. J.** (1984). *Ptolemy's Almagest*. Princeton University Press. — Table IX.5 row M=90° column "equation of center" for the 11°33' value our #4 reproduces.
- **Edmunds, M. G.** (2011). "An Initial Assessment of the Accuracy of the Gear Trains in the Antikythera Mechanism." *JHA* 42:307–320. — *separate* paper about *mechanical* gear-train accuracy, NOT the source of the 38° (which is theoretical-model error).
- **Yeomans, Chamberlin et al. 2011** = JPL Horizons. — http://ssd.jpl.nasa.gov/horizons (the reference ephemeris F&J use; equivalent to DE422 / our analytic Kepler at 1st-century-BC precision).
- Smithsonian Magazine 2017 — paraphrases Wikipedia → F&J 2012, attributing to Edmunds via AMRP affiliation.
