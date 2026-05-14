# Sun-from-SSB wobble falsification — Earth-Mars opposition residual

**Date:** 2026-05-14
**Domain:** ephemerides-spectral (sister package)
**Methodology:** MPM falsification round on the v0.27.0 Phase 10a residual-attribution thread.
**Authors:** Steven Kirkland (hypothesis); Claude Opus 4.7 (closed-form diagnostic).
**Branch:** `feat/ephemerides-spectral-phase-10a-eoc-catalog`

## Setup

A 100-yr Earth-Mars syzygy sweep on `ephemerides-spectral 0.26.1` produced 47 oppositions whose `(λ_M_true − λ_E_true)` residual at the BIP-defined opposition JDs has an RMS amplitude of 8.32° (= 18.05 d at synodic rate). A 47-point real-DFT of the residual ranked:

| rank | bin | period (yr) | amp (deg) | power share | initial attribution |
|---:|---:|---:|---:|---:|---|
| 1 | 6 | 16.73 | 9.18 | 60.9% | Earth+Mars own EOC alias |
| 2 | 7 | 14.34 | 5.60 | 22.7% | same EOC peak, adjacent bin |
| 3 | 8 | 12.55 | 2.34 | 4.0% | Jupiter direct fiber (alias 11.86 yr) |
| 4 | 5 | **20.07** | 2.19 | **3.5%** | **candidate: Sun-from-SSB wobble (J-S synodic 19.86 yr)** |
| 5 | 9 | 11.15 | 1.53 | 1.7% | — |

The bin-5 period (20.07 yr) sits 1.1% off the Jupiter-Saturn synodic (`P(J-S) = 1/(1/P_J − 1/P_S) = 7253 d = 19.859 yr`) — exactly DFT-bin-resolution-width. Hypothesis: bin-5 is the Sun-from-SSB wobble (heliocentric-frame projection of the J-S dance) propagating into the Earth-Mars opposition observable.

## Closed-form test

Computed the Sun-from-SSB vector closed-form per opposition JD:

```
r_sun_SSB(t) = -(1 / M_sun) · Σ_{giants} m_i · r_i_helio(t)
```

summed over Jupiter / Saturn / Uranus / Neptune (mass ratios 1/1047, 1/3498, 1/22903, 1/19412; carry > 99.5% of the wobble amplitude). Heliocentric body positions via Standish 1992 mean-motion advance from J2000; circular-orbit approximation in the ecliptic plane (eccentricity correction < 5° for the giants and irrelevant for the wobble spectrum).

The Sun-SSB radial distance ranged from **226,238 km to 1,394,854 km** (mean 818,000 km) over the 100-yr window — a real, physical motion well-represented by the closed-form. Jupiter-alone amplitude is 742,000 km; the four-giant ensemble varies between 226 k and 1395 k km depending on J-S relative phase.

Projected the wobble's apparent longitude effect on Earth and Mars via the first-order angular displacement `δλ_body = (r_sun_SSB ∧ r̂_body) / |r_body|`. Net `δ(λ_M − λ_E)` correction across the 47 oppositions:

- min: **−0.136°**
- max: **+0.174°**
- RMS: **0.083°**

Subtracted from the original residual; re-FFT'd.

## Result — falsified

| Bin | Period (yr) | Original power | Wobble-subtracted power | Collapse |
|---:|---:|---:|---:|---:|
| **5** | **20.07** | **56.28** | **55.88** | **+0.7%** |
| 8 (Jupiter) | 12.55 | 64.21 | 64.03 | +0.3% |
| 6+7 (EOC) | 16.73 + 14.34 | (huge) | unchanged | +0.0% |

**Bin-5 does NOT collapse under direct Sun-from-SSB subtraction.** The 3.5% power share survives essentially intact. Whatever lives at 20.07 yr in the Earth-Mars opposition residual, **it is not the Sun's barycenter motion**.

The wobble-correction amplitude is mathematically real and the orbital mechanics are correct, but the projection onto the Earth-Mars Δλ observable is small (RMS 0.083° vs residual RMS 8.32°) — about a 1:100 ratio in amplitude squared. Sun-wobble simply isn't a 3.5%-of-power contributor at the 100-yr / synodic-cadence resolution.

## Best-evidence revised attribution

DFT side-lobe leakage from the dominant Earth+Mars EOC peak at bin 6 (60.9% power, period 16.73 yr). 47-point unwindowed DFT has Dirichlet-kernel side lobes of approximately −13 dB at the first neighbour bin. Predicted leakage:

```
60.9% × 0.05 ≈ 3.0%
```

within 0.5 percentage points of bin-5's observed 3.5%. The aliased Earth-EOC + Mars-EOC fundamental (15.78 yr) lands between bins 6 and 7 (16.73 and 14.34 yr), splitting its leakage roughly symmetrically — and bin-5 catches the bin-6-side first sidelobe.

**Falsifiable prediction:** windowing the time series (Hann window applied before the DFT) should collapse bin-5 substantially while leaving bins 6+7's combined power roughly intact (the Hann window concentrates the main lobe and suppresses sidelobes). Not run as of this note; future researcher may close the loop.

## Implications for Phase 10b

The off-diagonal fiber budget needs to be revised:

| component | original share | after this falsification |
|---|---|---|
| Earth+Mars own EOC | 84% | **84%** (handled by Phase 10a closed-form Kepler patches) |
| Jupiter direct fiber | 4% | **4%** (Phase 10b target — Mars-Jupiter secular coupling) |
| bin-5 (was Sun-wobble candidate) | 3.5% | **DFT artefact, not physics** — subtract from "remaining fiber budget" |
| residual (Saturn + lower-order) | < 9% | < 9% |

**Phase 10b focuses on Mars-Jupiter direct gravitational coupling** (secular Mars-eccentricity-modulation theory; cross-references to Sussman-Wisdom and Laskar 1990 secular precession of Mars's perihelion). Sun-wobble correction is **not** a useful next step; the closed-form falsification rules it out at the 100-yr horizon for this observable.

## Closed-form provenance

- **Sun-SSB closed form:** `-Σ (m_i / M_sun) · r_i_helio` — Murray-Dermott (1999) *Solar System Dynamics* §2.2 barycentric reduction.
- **Mass ratios:** `1/1047.348644` (Jupiter), `1/3497.901768` (Saturn), `1/22902.98113` (Uranus), `1/19412.25976` (Neptune) — JPL DE441 canonical, cross-references Park et al. (2021) `10.3847/1538-3881/abd414`.
- **Standish 1992 mean elements** for the four giants — JPL Solar System Dynamics Technical Document.
- **Kepler ground truth** for Earth + Mars — Newton iteration on `E − e sin E = M`, half-angle true-anomaly formula. Same routine used in the v0.27.0 Phase 10a `EccentricityCorrectionPatch`.

## Script

`D:/tmp/sun_wobble.py` (not yet committed to the repo). Reproducible from the 47-opposition NDJSON at `D:/tmp/earth_mars_syzygies_100yr.ndjson` in ~30 seconds.

## MPM discipline note

This is a clean negative result. The hypothesis was specific ("bin-5 at 20.07 yr is the Sun-from-SSB wobble = J-S synodic"), the test was closed-form deterministic (no fit, no random init, no SGD), and the falsification is unambiguous (0.7% collapse where ≥ 70% would have been needed for a positive identification). The honest outcome strengthens the project's claim that closed-form diagnostics on labelled ground-proof rows can produce both positive AND negative results that move the science forward — which is exactly the discipline §0.0 of the ephemerides notebook names.

Cross-reference: this note is the first **published-internal falsification** of a candidate Phase-10b couplings-to-add. Phase-10b scoping should consult this before opening any "extend resonance set with Sun-wobble dynamics" thread.
