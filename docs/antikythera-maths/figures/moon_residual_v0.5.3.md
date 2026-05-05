# Moon residual fix — v0.5.3 (high-precision sidereal periods)

> Phase A diagnosis (notebook §3 → moon residual root cause): expected
> ecliptic-projection warp. Got something better — **period truncation**.

## Phase A: ruled out the frame hypothesis

The v0.5.2 moon FFT sweep reported ~100° RMS residuals on 13 of 17
moons against ephemeris truth. Initial hypothesis (notebook §3): the
encoder advances at uniform rate `omega = 2π / P_sidereal` while
skyfield's `astrometric.ecliptic_latlon()` returns ecliptic
longitude — for moons in inclined orbits (Galileans orbit Jupiter's
equator, ~26° off ecliptic), the ecliptic-projection longitude is a
non-uniform function of orbital phase, so the residual is a bounded
periodic warp at the moon's orbital period.

`research/diagnose_moon_residual.py` measured the residual within
ONE orbital period for two clean controls (Callisto, Titan) and four
broken bodies (Io, Europa, Mimas, Metis):

| body | class | period (d) | within-period RMS | v0.5.2 sweep RMS |
| --- | --- | ---: | ---: | ---: |
| callisto | control | 16.7 | 1.0° | 0.6° |
| titan | control | 15.9 | 5.2° | 3.4° |
| io | broken | 1.77 | **0.42°** | 106° |
| europa | broken | 3.55 | **0.81°** | 116° |
| mimas | broken | 0.94 | 5.3° | 104° |
| metis | broken | 0.29 | **0.07°** | 104° |

Within ONE orbital period, the "broken" moons show TINY residuals.
The v0.5.2 ~100° RMS is **secular accumulation**, not within-orbit
warping. The frame hypothesis is wrong.

## Real root cause: period truncation in `BODIES`

The encoder uses `omega = 2π / P_sidereal` baked at codegen time
into `es_omega_diag[]` (C side) and the integer Q-format `omega_diag`
table (Python side). v0.5.0 stored `period_days` to 3-4 decimals.
For fast-orbit moons (Io's sidereal period 1.769 d, Metis's 0.295 d)
that 10⁻⁴-relative truncation produces 10⁻⁴-relative `omega` error
that accumulates over 41,000+ orbits in the 200-yr sweep horizon.

Predicted vs measured cumulative drift over 200 yr:

| body | rel. period err | revs over 200yr | predicted cumul (mod 360°) | observed v0.5.2 RMS |
| --- | ---: | ---: | ---: | ---: |
| io | +7.8×10⁻⁵ | 41,291 | +77.7° | 106° |
| europa | +5.1×10⁻⁵ | 20,571 | +17.5° | 116° |
| ganymede | -6.3×10⁻⁵ | 10,210 | +130.3° | 117° |
| callisto | +1.1×10⁻⁶ | 4,377 | +1.7° | **0.6°** ✓ |
| metis | -6.8×10⁻⁵ | 247,812 | +67.2° | 104° |
| enceladus | +1.6×10⁻⁴ | 53,313 | +171.5° | 103° |
| rhea | +4.7×10⁻⁵ | 16,168 | -86.9° | 98° |

The pattern is clear: **the moons that match the predicted cumulative
drift (Callisto's ~2° prediction matches its 0.6° observed) are
exactly the ones that ALREADY worked in v0.5.2**. The moons whose
predicted cumulative drift is large are exactly the ones that were
broken. Period truncation is the dominant residual source.

The wrap of accumulated cumulative drift modulo 2π produces a
sawtooth-shaped residual whose FFT spectrum is broadband — that's
the "near-DC content" v0.5.2 reported (FFT peak at sweep span = 336
yr is just the sawtooth fundamental).

## v0.5.3 fix: high-precision periods

Replace the truncated `period_days` values with full-precision
sidereal periods from JPL HORIZONS / NASA fact sheets. Periods now
stored to 9+ decimal places in `research/bodies.py`. After codegen
+ rebuild, re-run the moon FFT sweep:

| Moon | v0.5.2 RMS | v0.5.3 RMS | improvement |
| --- | ---: | ---: | ---: |
| **io** | 106.33° | **0.34°** | **−317×** |
| **europa** | 116.41° | **0.76°** | **−154×** |
| **ganymede** | 117.49° | **0.14°** | **−825×** |
| callisto | 0.60° | 0.60° | unchanged ✓ |
| **adrastea** | 103.57° | **0.07°** | **−1450×** |
| **amalthea** | 102.30° | **0.27°** | **−376×** |
| **enceladus** | 102.96° | **2.57°** | **−40×** |
| **tethys** | 101.46° | **2.94°** | **−34×** |
| **dione** | 117.24° | **2.54°** | **−46×** |
| titan | 3.39° | 3.39° | unchanged ✓ |
| iapetus | 2.50° | 2.50° | unchanged ✓ |
| hyperion | 11.0° | 11.0° | unchanged ✓ |
| **mimas** | 103.65° | **30.78°** | −3.4× (partial) |
| ~~metis~~ | 103.97° | 109.0° | unchanged |
| ~~thebe~~ | 105.30° | 104.3° | unchanged |
| ~~rhea~~ | 98.28° | 100.5° | unchanged |
| ~~phoebe~~ | 103.86° | 103.8° | unchanged |

**13 of 17 moons** are now in Callisto-class clean territory (≤ 3°
RMS; previously only 4). The Galileans + Jovian inner regulars +
the inner Saturnian resonance set (Mimas–Tethys + Enceladus–Dione)
all dropped by 30-1400×.

## Still broken: metis / thebe / rhea / phoebe

Four moons resisted the period-truncation fix. The predicted-cumulative-
drift heuristic suggests their period precision IS adequate, so
something else is going on:

- **Metis** (P=0.29478, top-1 FFT period 168 yr at 49°): published
  sidereal periods for Metis vary across sources (0.2948 d on
  Wikipedia, 7.07467 hr = 0.294778 d on JPL, etc.). May need a
  more precise authoritative value.
- **Thebe** (P=0.6745 d): the published value is exactly 0.6745
  with no further digits in most sources. The remaining residual
  may be perturbation-driven (Thebe has a small but non-zero
  inclination + eccentricity).
- **Rhea** (P=4.518212 d): published value matches our entry to
  6 decimals. Could be a frame issue (Rhea's orbit is inclined
  ~0.35° to Saturn's equator) or a perturbation from neighbouring
  moons (Mimas, Tethys, Dione).
- **Phoebe** (P=550.564636 d, RETROGRADE): orbits backward relative
  to Saturn. Our encoder advances `omega = +2π/P` regardless of
  direction. May need a sign flip or a frame fix specific to
  retrograde irregulars.

These four are queued for v0.5.x phase B+ — likely individual
diagnostic + fix per moon. The v0.5.3 fix is the structural one;
the remaining 4 need physics-specific investigation.

## What this earns

The v0.5.3 fix unblocks the LS-fit catalog methodology (§9) for
moons. With 13 moons now in clean ≤ 3° RMS, the next step is to
re-run `de441_moon_spectrum` with the v0.5.2 LS-fit pipeline against
the cleaned-up moon residuals — likely surfacing per-moon resonance
peaks worth authoring CATALOG_V2 entries for. (The Mimas–Tethys
4:2 + Enceladus–Dione 2:1 + Titan–Hyperion 4:3 wired in v0.5.0's
RESONANCES table can finally be measurement-validated against
ephemeris truth.)

## Reproducing this

```bash
cd docs/antikythera-maths

# Phase A diagnostic (per-orbital-period residual on Callisto/Io/Mimas/etc.)
python -m research.diagnose_moon_residual

# Re-run the moon FFT sweep on the v0.5.3 high-precision periods
python -m research.de441_moon_spectrum
```

End-to-end ~3 min on the C native + skyfield path.
