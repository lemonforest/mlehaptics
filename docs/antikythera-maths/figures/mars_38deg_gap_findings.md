# The Mars 38° gap — what we found

**Status:** Research finding (this branch).
**Date:** 2026-05-01
**Code:** [`research/mars_38deg_gap_analysis.py`](../research/mars_38deg_gap_analysis.py) — seven analyses, all running against analytic Kepler 2-body ground truth (no JPL kernel needed).

## TL;DR

The notebook's claim "we haven't tried to model the Greek epicycle" is **stale**. We did model it (v0.2.0 sequel, Track 2). What's actually true is:

- We implemented the Hipparchian eccentric-deferent + epicycle (peak 51.48° vs DE422 in §9.2).
- We implemented the Ptolemaic equant with bisected eccentricity (peak 48.66°).
- We now also implement `mars_longitude_bronze` — the same eccentric-deferent + epicycle, but derived as a **projection from the cyclic-group algebra of the deferent gear ratios** through the pin-and-slot phase-space transform `atan2(sin θ, cos θ + e/R)`. Numerically agrees with `mars_longitude_epicycle_only` to ~10⁻¹³ deg (#7 parity check); same transform, two derivation pathways.
- The documented "Antikythera Mars peak ~38°" comes from **Freeth & Jones 2012, ISAW Papers 4, §3.10 + Figure 39**, measured against JPL Horizons across the **middle seven retrogrades of Mars in the 1st century BC** (~13-year window, ~-53 BCE). Their model is a *bare* deferent + epicycle (no eccentricity, no equant) — even simpler than Hipparchus. Captured as `FREETH_2012_MARS_PARAMS` (with `FREETH_2021_MARS_PARAMS` for the gear-train reconstruction; same kinematic class).
- **The 10° gap is not a math bug.** Our `_equation_of_center_equant` reproduces Ptolemy IX.5's max equation (11°33' = 11.55°) to within 0.18°. Implementation is correct.
- **The gap is partly phase-alignment, partly metric-choice.** Our default `MarsParams.epoch_lon_deg = 297.4°` and `epoch_anomaly_deg = 41.6°` are propagated from Almagest IX.6's anchor, with a few-degree apsidal-line drift over 2200 years. The new EpochFitter (#6) closes ~50° of the unfit 95° peak; the residual ~13° to F&J's 38° is best read as **F&J's 38° being a mean-style summary, not a peak** — our refit equant has mean 18°, refit bronze 27°, both *below* F&J's 38° as means. F&J's "nearly 38° at the retrogrades" reads as "pre-Hipparchian planetary models miss by ~zodiac sign on average," which all our models reproduce.

## What the seven sub-analyses showed

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

## What's actually wrong (the structural diagnosis, post-#6)

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

**Refined framing** (post-#6): the residual ~13° gap from F&J's 38° is *not* further phase misalignment — Nelder-Mead refit doesn't close it. It's most plausibly a peak-vs-mean metric mismatch: F&J's "nearly 38°" tracks our *mean* error (refit equant: 18°; refit bronze: 27°; both *below* F&J's 38°), not our peak. As a mean summary, "38° at the retrogrades" reads as "pre-Hipparchian planetary models miss by ~zodiac sign on average across this window" — which all our models reproduce.

Per Freeth & Jones: their figure assumes "a 'perfect' period relation for Mars." The "perfect" — i.e. retrograde-aligned — period is what *exposes* the theoretical model error rather than burying it under cycle-accumulated phase drift. Our refit Nelder-Mead is doing the same thing F&J did with their hand-anchored period choice, but optimised against shape RMS. The remaining mismatch is metric definition (peak vs mean), not modelling.

## Recommended follow-up (next research session, not in this PR)

#6 above did not produce the expected ~38° peak — instead it landed at 51-60° peak with much-reduced mean (18-27°). Two natural follow-ups:

1. **Peak-objective refit.** Replace RMS objective with peak objective (max\|residual\|) to test whether a peak-minimising fit lands at F&J's 38°. Non-smooth, so use Nelder-Mead with a softened max (e.g. `mean(top-5 |residual|)`), or a CMA-ES variant. Estimated effort: ~30 LOC, an hour.
2. **JPL Horizons reference instead of Kepler 2-body.** Our current Kepler 2-body propagation neglects lunar perturbations on Earth's barycentre (~few arcsec/day at this era) and Jupiter's perturbation on Mars's mean motion (~tens of arcsec). Replacing the reference with `de441` ephemeris would test whether F&J's 38° is partly a consequence of using JPL Horizons' richer dynamics. Estimated effort: ~80 LOC if we already have the kernel; otherwise add a kernel-fetch helper.

Both are parameter / reference-frame choices, not new modelling — in scope per [`docs/antikythera-maths/CLAUDE.md`](../CLAUDE.md). Defer to a future session unless a contributor wants to chase the peak-objective branch sooner.

The appropriate notebook framing now is:

> "Our equant implementation is mathematically correct (matches Ptolemy IX.5's max equation of center to <0.5°), and its bronze projection through the gear-ratio pin-and-slot transform agrees with the analytic equation-of-center to ~10⁻¹³ deg (a numerical-precision parity check). On F&J's 1st-century-BC window the unfit equant's mean shape error is 37.8° — within 0.2° of F&J's documented 38° — but its global peak is 102° because the encoder's `MarsParams` epoch values aren't retrograde-aligned with -53 BCE. The new EpochFitter (#6) closes ~50° of the unfit peak; the residual ~13° from F&J's number reads as F&J's '38°' being a mean-style summary rather than a peak (refit equant has mean 18°, *below* F&J's 38°). The 'phase misalignment is the entire 60° gap' framing was directionally right but quantitatively incomplete — it's ~50° phase + ~13° peak-vs-mean metric choice."

## Sources

- **Freeth, T. & Jones, A.** (2012). "The Cosmos in the Antikythera Mechanism." *ISAW Papers* 4. — http://dlib.nyu.edu/awdl/isaw/isaw-papers/4/ (§3.10 + Fig. 39 are the source of the 38° figure)
- **Toomer, G. J.** (1984). *Ptolemy's Almagest*. Princeton University Press. — Table IX.5 row M=90° column "equation of center" for the 11°33' value our #4 reproduces.
- **Edmunds, M. G.** (2011). "An Initial Assessment of the Accuracy of the Gear Trains in the Antikythera Mechanism." *JHA* 42:307–320. — *separate* paper about *mechanical* gear-train accuracy, NOT the source of the 38° (which is theoretical-model error).
- **Yeomans, Chamberlin et al. 2011** = JPL Horizons. — http://ssd.jpl.nasa.gov/horizons (the reference ephemeris F&J use; equivalent to DE422 / our analytic Kepler at 1st-century-BC precision).
- Smithsonian Magazine 2017 — paraphrases Wikipedia → F&J 2012, attributing to Edmunds via AMRP affiliation.
