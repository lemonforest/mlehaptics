# Moon catalog patches — v0.5.5 (Phase C of the v0.5.x moon programme)

> **Methodology vindicated twice.** v0.5.2 hit 96-99% shrinkage on planet
> patches via LS-fit at the exact target period. v0.5.5 ports the same
> pipeline to moons and lands 93-99% on 5 of 6 targets, with the same
> empirical signature (LS-fit amps 2-3× the FFT-bin baselines) on a
> completely different bodyset.

## What Phase A and Phase B earned

The v0.5.x moon programme split into three phases:

- **Phase A** (v0.5.3 prep): per-orbital-period diagnostic ruled out the
  ecliptic-projection frame hypothesis. Within ONE orbital period the
  "broken" moons showed tiny residuals (Io 0.42°, Metis 0.07°). The
  v0.5.2 ~100° RMS sweep value was secular drift, not within-orbit
  warping.
- **Phase B** (v0.5.3): high-precision sidereal periods (9+ decimals
  from JPL HORIZONS / NASA fact sheets) collapsed the cumulative drift.
  13 of 17 moons dropped 30-1450× in RMS. The remaining 4 (metis,
  thebe, rhea, phoebe) are physics-specific and out of scope.
- **Phase C** (v0.5.5, this writeup): with secular drift gone, the
  remaining residuals are **single-peak-dominated** in their FFT
  spectrum — the regime where LS-fit catalog authoring earns its
  shrinkage.

## Patch targets (from the v0.5.3 moon-friendly FFT sweep)

The v0.5.3 sweep (`results/de441_moon_spectrum.md`) ranks each moon's
top 20 spectral peaks. For Phase C we picked the dominant peak per
moon among the 6 cleanest single-peak signals:

| body | v0.5.3 RMS | top peak (period × FFT amp) |
|---|---:|---|
| dione | 2.53° | 387.6 d × 1.17° |
| tethys | 2.94° | 138.2 d × 1.75° |
| enceladus | 2.57° | 141.9 d × 1.52° |
| titan | 3.39° | 252.8 d × 1.56° |
| iapetus | 2.50° | 79.3 d × 1.58° |
| hyperion | 11.0° | 72.4 d × 5.44° |

Mimas (30.78° RMS, broadband near-DC content) was excluded — its
remaining residual is structural, not a single sinusoid. The four
unfixed-by-Phase-B moons (metis / thebe / rhea / phoebe) are likewise
excluded — period truncation is still in play and LS-fit assumes the
underlying mean motion is correct.

## Pipeline

Two new scripts mirror the v0.5.2 planet pipeline:

- `research/author_moon_patches.py` — moon-targeted LS-fit author. For
  each target, runs the encoder over the moon-friendly window
  (4096 samples × 30d cadence, fits inside `jup365` + `sat441`
  coverage), then `_lsq_fit_sinusoid` (closed-form + scipy refinement)
  recovers `(amplitude_deg, period_days, phase_rad)` directly from
  the residual time series. Bypasses FFT bin leakage entirely.
- `research/verify_moon_patches.py` — patch-shrinks-residual verifier.
  7 sweeps (1 baseline + 6 with each patch active); reports peak
  shrinkage at the target period band.

`research/de441_moon_spectrum.gather_moon_residuals(...)` was extracted
out of `run_moon_spectrum` so both author + verify share the residual-
gathering loop without re-emitting FFT structure each pass.

## Recovered patch parameters

| name | body | period (d) | amp (°) | phase (rad) |
|---|---|---:|---:|---:|
| `dione-1.06yr-diagonal-v2` | dione | 387.04 | 3.5738 | 1.5027 |
| `tethys-0.38yr-diagonal-v2` | tethys | 138.24 | 3.5733 | 1.1054 |
| `enceladus-0.39yr-diagonal-v2` | enceladus | 141.94 | 3.5751 | 1.3156 |
| `titan-0.69yr-diagonal-v2` | titan | 252.74 | 3.3130 | 0.2929 |
| `iapetus-0.22yr-diagonal-v2` | iapetus | 79.34 | 3.2636 | 3.6725 |
| (hyperion-0.20yr-diagonal) | hyperion | 72.42 | 11.6459 | 0.9629 |

**Bin-leakage signature.** LS-fit recovered amplitudes are 2-3× the
FFT-bin baselines (see the v0.5.5 author run summary). Same ratio
v0.5.2 documented on planets (Mars 3×, Mercury 2.6×, J-S 2.5×). The
methodology generalises across body classes.

## Measured shrinkage (vindication run)

| name | base amp | patched | shrinkage | RMS Δ | verdict |
|---|---:|---:|---:|---:|:---|
| dione-1.06yr-diagonal-v2 | 1.168° | 0.021° | **98.2%** | 2.535° → 0.199° | **VINDICATED** |
| tethys-0.38yr-diagonal-v2 | 1.751° | 0.109° | **93.8%** | 2.944° → 1.511° | **VINDICATED** |
| enceladus-0.39yr-diagonal-v2 | 1.520° | 0.016° | **98.9%** | 2.569° → 0.458° | **VINDICATED** |
| titan-0.69yr-diagonal-v2 | 1.564° | 0.071° | **95.5%** | 3.388° → 2.447° | **VINDICATED** |
| iapetus-0.22yr-diagonal-v2 | 1.576° | 0.021° | **98.6%** | 2.497° → 0.954° | **VINDICATED** |
| hyperion-0.20yr-diagonal | 5.439° | 1.351° | 75.2% | 10.987° → 7.272° | PARTIAL |

5 of 6 patches clear the 80% gate by a comfortable margin. The five
vindicated patches ship in `CATALOG_V2`.

## Hyperion: chaos as the methodological ceiling

The Hyperion patch shrinks the targeted 72.4-d peak by 75.2% (5.44° →
1.35°), shy of the 80% gate. **This is physics, not a methodology
bug.** Hyperion's rotation has been the canonical Solar-System chaotic
dynamical system since Wisdom (1984). The FFT spectrum reflects that
directly:

| rank | period (d) | amp (°) |
|---:|---:|---:|
| 1 | 72.4 | 5.44 |
| 3 | 72.5 | 1.39 |
| 5 | 73.2 | 1.30 |
| 6 | 72.4 | 0.93 |
| 8 | 81.6 | 0.61 |
| 9 | 72.5 | 0.61 |

Multiple sub-peaks near the same period — the spectral signature of
quasiperiodic-not-sinusoidal motion. A single LS-fit sinusoid catches
the dominant component but misses the chaotic spread. Two candidate
follow-ups for v0.5.x:

1. **Multi-component sinusoid patch** — one catalog entry expressed
   as a list of `(period, amplitude, phase)` sinusoids covering the
   Hyperion sub-peaks. Originally planned for v0.5.2's Mars
   (motivation: bin leakage); now revived for Hyperion (motivation:
   chaotic rotation). C-side `es_patch_t` would grow an
   `n_components` field.
2. **Titan-Hyperion 4:3 coupled patch** — v0.5.0's `RESONANCES` table
   wired the resonance at the structural level but didn't calibrate.
   A `CoupledSinusoidPatch(body_a="titan", body_b="hyperion", ...)`
   matches the v0.5.2 J-S template; the second body is the resonant
   partner whose chaotic kicks Hyperion's residual reflects.

Either path should beat the 80% gate. Hyperion stays out of
`CATALOG_V2` until one ships.

## Methodology vindicated twice

The cleanest read of v0.5.5: the v0.5.2 LS-fit catalog methodology now
has measured shrinkage on **two completely independent body sets**.

| set | bodies | n patches | shrinkage range |
|---|---|---:|---|
| v0.5.2 planets | Mars, Mercury, J–S coupled | 4 | 96.0–99.9% |
| v0.5.5 moons | Dione, Tethys, Enceladus, Titan, Iapetus | 5 | 93.8–98.9% |

LS-fit amplitudes consistently 2-3× the FFT-bin baselines on both —
the same bin-leakage signature on bodies orbiting the Sun and bodies
orbiting Saturn. The methodology is no longer a planet thing or a moon
thing; it's a Fourier-decomposable-residual thing.

## Reproducing this

```bash
cd docs/antikythera-maths

# Phase A diagnostic (v0.5.3 prereq — already shipped)
python -m research.diagnose_moon_residual

# Phase C author + verify
python -m research.author_moon_patches
python -m research.verify_moon_patches
```

End-to-end ~3 min author + ~17 min verify (7 sweeps) on the C native +
skyfield path.

## Cross-references

- v0.5.3 period-truncation root cause: [`moon_residual_v0.5.3.md`](moon_residual_v0.5.3.md)
- v0.5.2 planet vindication: [`patch_shrinks_residual_v0.5.2.md`](patch_shrinks_residual_v0.5.2.md)
- v0.5.1 audit + math fix: [`patch_shrinks_residual_v0.5.1.md`](patch_shrinks_residual_v0.5.1.md)
- v0.4.0 catalog (the unverified original): [`runtime_kernel_patching.md`](runtime_kernel_patching.md)
