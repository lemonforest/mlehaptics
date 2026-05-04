# DE441 error spectrum — interpretation of the FFT peaks

**Companion to:** [`results/de441_error_spectrum.md`](../results/de441_error_spectrum.md)
**Tool:** `research/de441_error_spectrum.py`
**Date:** 2026-05-04 (v0.3.1)

The v0.3.0 DE441 sweep showed nearly-linear per-body error against
DE441 truth across J2000 ± 14,000 yr. The linear slope is the
*systematic* drift; the *modulation* on top of it is the signal of
dynamics the Phase-9 model isn't capturing. v0.3.1's
`de441_error_spectrum.py` FFTs the (linear-detrended) per-body
residual and reports the dominant modulation peaks.

This document interprets those peaks — what physical mode each
fingers, and (where applicable) which Phase-9 resonance entry the
peak amplitude empirically motivates.

## Sample-grid + Nyquist caveat

1024 samples at 900-day cadence → Nyquist period ≈ 4.93 yr. Modes
with periods *below* 4.93 yr alias to apparent periods above
Nyquist. The most important alias to keep in mind: the lunar synodic
month (29.53 d ≈ 0.081 yr) and the Earth-Moon sidereal month (0.075 yr)
are far below Nyquist and will appear at near-aliased peaks. This
sweep is *coarse* — useful for the slow-mode structure (which is
where the real residual lives), but a finer-cadence companion sweep
is the natural follow-up to resolve the lunar / Mercury-synodic
modes properly.

## The headline finding: Jupiter–Saturn at 9.56 yr, ±45° amplitude

| Body | Top peak (yr) | Amplitude (deg) | RMS detrended (deg) |
| :--- | --: | --: | --: |
| jupiter | 9.558 | **44.6** | 104.1 |
| saturn  | 9.558 | **45.0** | 104.2 |

Jupiter and Saturn have **identical top peaks** at 9.56 yr —
identical structure, identical amplitude (to within 1%). That's
the fingerprint of a single shared mode driving both: the
Jupiter–Saturn 5:2 mean-motion resonance. The Phase-9 model has
this resonance wired (`(jupiter, saturn, 5, 2)`) with α = 0.1
phenomenologically, but the residual amplitude says **the actual
modulation depth is much larger than the model captures**. ±45°
is enormous; the static Laplacian + uniform-α-0.1 leaves most of
the J–S libration unmodelled.

This is the empirical α the v0.4+ first-principles Hamilton/
Delaunay derivation needs to reproduce. Concretely: a residual
amplitude of 45° at a 9.56-yr period implies the breathing
modulation should be ~5× larger than v0.3.1's α = 0.1 setting,
*and* the period is half what we'd naïvely expect for the J–S
5:2 (which has a slow-mode period of ~883 yr in the libration
picture and a fast 1.85-yr commensurability). 9.56 yr ≈ 1/3 ×
28.95 yr (the 5:2-commensurate period itself), suggesting a
third-harmonic structure the simple cosine LUT can't represent.

## Outer planets: residuals at their own orbital periods

| Body | Top peak (yr) | Body period (yr) | Amplitude (deg) |
| :--- | --: | --: | --: |
| uranus  | 84.107  | 84.0   | 2.69 |
| neptune | 168.214 | 164.8  | 0.43 |
| pluto   | 252.320 | 247.9  | 13.12 |

Neptune, Uranus, Pluto each have their dominant peak **at their
own orbital period**. That's the classic signature of a body whose
mean motion has a small *systematic* offset from truth — the BIP
encoder's discretised `omega_int = round(omega_rad/(2π) × 2³²)`
introduces a few-residue rounding per revolution, and 14,000 yr of
those accumulates into a phase wave at the body's own period.

Pluto's 13° amplitude is large but the body's category is
"planet" with `mass_earth = 0.00218` — so its rounding error
compounds visibly, but it's not a *model-missing* signal; it's a
**Q-format precision floor** signal. The fix is K_BITS > 32 (e.g.
Q1.62 in `int128` or fixed-point with extended precision); not
something Phase-9 itself can address.

## Mars: 7.96 yr (≈ Mars-orbital × 4 OR Mars-Saturn synodic × 2)

Mars peaks at 7.96 yr with amplitude 3.45°. Two physical
candidates:

* **4 × Mars sidereal year** (4 × 1.88 yr = 7.52 yr) — Mars's own
  period sub-harmonic, like the outer-planet case above.
* **2 × Mars-Saturn synodic period** (Mars-Saturn synodic ≈ 4.0 yr,
  doubled = 8.0 yr).

The doubling pattern in both candidates is suspicious. Most likely
this is a Mars–Saturn 2:1 near-resonance (Saturn's period is
~29.5 yr ≈ 14.7 × Mars's 1.88 yr; the 14.7:1 isn't a clean small-
integer resonance, but the 2:1 of synodics is). Worth a v0.4+
candidate: add `(mars, saturn, ?, ?)` to the RESONANCES table and
re-measure the FFT.

## Mercury: 10.69 yr — relativistic-PN signature

Mercury's top peak at 10.69 yr with 9.19° amplitude has no obvious
small-integer match to any orbital period. Mercury's perihelion
precesses at 43"/century in our linear PN diagonal, but the actual
PN expansion has higher-order terms. Mercury's eccentricity
(0.205) and the Sun's gravity-well curvature give a rich set of
post-Newtonian sub-harmonics. The 10.69-yr period is a candidate
for a higher-order PN term (Mercury's actual perihelion-precession
beat with one of the larger planets — most likely Jupiter, whose
mean motion is 11.86 yr).

If 10.69 yr is the Mercury-Jupiter synodic-precession beat, that's
the empirical motivation for adding a non-linear PN entry to the
diagonal Laplacian, OR adding a `(mercury, jupiter, n, m)`
resonance pair. Either gets us off the linear PN approximation
that v0.3.1 ships.

## Moon: 7.29 yr — possible Saros sub-harmonic

The Moon peaks at 7.29 yr with 2.44° amplitude. Saros = 18.03 yr;
7.29 yr ≈ 18.03 / 2.47 ≈ Saros / 2.47. That's not a clean
sub-harmonic (Saros / 2 = 9.02 yr; Saros / 3 = 6.01 yr). More
likely candidates:

* **Earth-Moon nodal regression × 0.39** ≈ 18.6 × 0.39 = 7.25 yr
  (the inclination-mode precession sub-harmonic).
* **2.47 × lunar Saros** appearing as Saros — but that's the
  same number from another direction, suggesting we don't have a
  clean physical interpretation yet.

The Moon's linear-slope of **0.1165°/yr** (largest of any body) is
the actually-concerning number — at 14,000 yr that's 1631° = 4.5
revolutions of accumulated drift. The Moon needs explicit
treatment in Phase 10's coverage extension; v0.3.1 doesn't have
the lunar-precession + lunar-nodes resonance entries the residual
spectrum is asking for.

## Earth: 5.3 yr aliased; need finer cadence

Earth's top peak at 5.31 yr is *just above* the 4.93-yr Nyquist
limit. Five neighbouring peaks (5.29 / 5.30 / 5.31 / 5.32 / 5.33)
within 0.04 yr of each other suggest **aliasing of a sub-Nyquist
mode** rather than a single physical peak. The lunar synodic
month (29.5 d) at this cadence aliases prominently; so does
Earth-Moon sidereal (27.3 d).

Diagnostic for v0.3.x or v0.4+: re-run `de441_error_spectrum.py`
with `cadence_days=10.0`, `n_samples=4096` to resolve the lunar
modes. Expected outcome: Earth's peak relocates to ~0.08 yr
(synodic month) with amplitude that names the missing
Earth–Moon coupling — the Phase-10 ROADMAP item.

## What we'd add to the RESONANCES table given this spectrum

Rough priority ordering by residual-amplitude-to-fix:

1. **Strengthen Jupiter–Saturn 5:2** (currently α = 0.1; spectrum
   suggests α ≈ 0.5 needed; or add a 3rd-harmonic term that the
   simple cosine LUT can't represent).
2. **Add Mars–Saturn coupling** (period 7.96 yr, amplitude 3.45°
   on Mars). Best guess at the integer pair: figure out from the
   actual mass ratio + period ratio.
3. **Add Mercury–Jupiter beat term** for the PN-correction (period
   10.69 yr, amplitude 9.19°). May want a non-linear PN diagonal
   instead.
4. **Add lunar-nodes / Saros** entries (Moon period 7.29 yr,
   amplitude 2.44° — but that's multi-body, will need a 3-body
   resonance support v0.3.x doesn't have yet).

This is the practical bridge from the v0.3.1 spectrum to the v0.4+
first-principles α derivation: instead of deriving every α from
first principles, *measure* the residual amplitudes and focus the
derivation work on the ones that actually matter empirically.

## Reproducibility

```bash
cd docs/antikythera-maths
python -m research.de441_error_spectrum
# (uses native C path if `pip install ephemerides-spectral` is
#  available; ~6 s total. Falls back to pure Python at ~315 s.)
```

For finer-cadence companion sweeps (resolves lunar modes):

```python
from research.de441_error_spectrum import run_spectrum, write_outputs
summary = run_spectrum(kernel="de441", n_samples=4096, cadence_days=10.0)
```

Outputs land at `results/de441_error_spectrum.{json,md}`; this
analysis document hand-interprets the table.
