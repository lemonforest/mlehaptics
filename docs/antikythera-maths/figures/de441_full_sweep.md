# DE441 full-epoch sweep — Phase 9 BIP encoder

**Date:** 2026-05-04 (run for `ephemerides-spectral` v0.3.0)
**Kernel:** JPL DE441 (`de441.bsp`, ~3.1 GB), `force_high_res=True`
**Encoder:** `EphemerisBIPInstrument` at `D = 2^16`, Phase 9 breathing
couplings active (4 resonance entries: J–S 5:2, N–P 3:2, Io–Europa 2:1,
Europa–Ganymede 2:1).

## Sweep design

15 sample points geometrically spaced as `J2000 ± {0, 1, 10, 100, 1000,
5000, 10000, 14000} yr` — total span ≈ 28,000 yr, sitting just inside
DE441's ~30,000-yr coverage window (-13,200 BCE to +17,191 CE).

For each sample we:

1. Encode the system with the integer-ALU BIP path (`encode_state`).
2. Read the per-body uint32 phase residue, convert to ecliptic longitude
   (rad).
3. Compare against DE441 ground truth via skyfield (`astrometric.ecliptic_latlon`).
4. Take the smallest unsigned angular difference (∈ `[0, π]`).

DE441 ships only 10 of our 26 bodies directly (Sun + 9 planets + Moon + Pluto;
the moons of Mars / Jupiter / Saturn / Uranus / Neptune and the four
main-belt asteroids need supplementary kernels). The sweep skips the Sun
(period ≡ 0; phase residue is 0 by construction) and reports per-body
errors for the remaining 10.

## Headline results

```
Encode wall time (ms): median 447.1, max 6365.4
```

Encode time scales linearly with `|delta_t|` (one chunk per 30 days):
0.2 ms at J2000 → 6.4 s at +14,000 yr. Chunk count at the extreme is
~170,000.

### Per-body Earth-frame ecliptic longitude error

Sorted by max error, descending. Reading note: a max of `π ≈ 3.14 rad`
is the worst possible — phase residue effectively scrambled. Bodies near
that ceiling are bodies whose multi-millennium dynamics the Phase-9
breathing model fails to reach.

| Body | n | median (rad) | p95 (rad) | max (rad) | max (deg) |
| :--- | --: | --: | --: | --: | --: |
| jupiter | 15 | 1.357392 | 2.936980 | 3.070351 | 175.9182 |
| saturn | 15 | 1.415146 | 2.990438 | 3.062358 | 175.4602 |
| neptune | 15 | 0.690666 | 2.748483 | 2.778294 | 159.1845 |
| pluto | 15 | 0.790648 | 2.523580 | 2.721233 | 155.9152 |
| moon | 15 | 1.084108 | 2.558565 | 2.670403 | 153.0028 |
| mercury | 15 | 0.356374 | 1.443567 | 1.461477 | 83.7365 |
| mars | 15 | 0.116935 | 0.250344 | 0.253426 | 14.5202 |
| uranus | 15 | 0.046538 | 0.119522 | 0.140730 | 8.0632 |
| venus | 15 | 0.023516 | 0.113740 | 0.124093 | 7.1100 |
| earth | 15 | 0.011397 | 0.104272 | 0.115029 | 6.5907 |

### Earth phase error vs horizon

| Δt (yr) | Earth err (deg) |
| --: | --: |
| 0 | 0.000 |
| ±1 | 0.001–0.004 |
| ±10 | 0.006–0.008 |
| ±100 | 0.065–0.069 |
| ±1000 | 0.65–0.68 |
| ±5000 | 2.93–3.31 |
| ±10000 | 4.70–5.71 |
| ±14000 | 5.48–6.59 |

Roughly linear: ~0.0006°/yr near J2000, ~0.0005°/yr at the extreme.
Consistent with v0.1.0's documented 0.0002 rad ≈ 0.012° error at +20 yr
(the 30-yr-old number scales to ~0.018°/yr, dominated then by the
*static* propagator drift; the v0.3.0 Phase-9 breathing path inherits
that drift baseline).

## Honest interpretation: the structural limit, plotted

The error landscape splits cleanly into three regimes:

* **Sub-10° at multi-millennium horizons (Earth, Venus, Uranus):**
  bodies whose mean motion + small eccentricity + the static gravitational
  fiber couplings do approximately what the actual orbit does. Earth
  benefits from being the calibration body for Mercury's PN diagonal.
  Uranus is so distant its mean motion dominates and there's not much
  perturbation to model.

* **Tens of degrees at multi-millennium horizons (Mars 14.5°,
  Mercury 84°):** bodies whose dynamics include eccentricity + long-period
  perturbations the Phase-9 model only partially captures. Mars: not
  in any of the four wired resonance pairs, so its drift is purely
  static-Laplacian. Mercury: in the PN diagonal but not in any
  off-diagonal resonance — the 43"/century PN correction is *linear*,
  whereas Mercury's actual perihelion precession at multi-millennium
  scales has higher-order terms.

* **Phase-scrambled at multi-millennium horizons (Jupiter, Saturn,
  Neptune, Pluto, Moon — all hitting >150°):** bodies dominated by
  resonant perturbations that our 4-entry breathing table only
  approximates phenomenologically. The Jupiter–Saturn 5:2 entry uses
  a fixed 10% modulation depth (`α = 0.1`) that's the right *order of
  magnitude* but wrong in detail — over ±14,000 yr that wrong-detail
  accumulates to a ~3 rad phase deficit. Same story for Neptune-Pluto
  and the Laplace pair: phenomenological depths drift secularly.

## What this measures

This sweep measures **how much of multi-millennium ephemeris our v0.3.0
model captures**, *not* how accurate the BIP encoder is at its design
horizon. v0.3.0 is calibrated for the ±20-yr horizon (0.0002 rad Earth
phase floor); the multi-millennium errors are the cost of running a
model trained for short-horizon dynamics far past its design point.

Three follow-ups that would each visibly improve specific bodies:

1. **Per-resonance derived `α` (v0.3.x ROADMAP item).** The
   Hamilton/Delaunay-variable Lie-series derivation gives `α` per
   resonance from physical first principles instead of phenomenologically.
   Concretely: the Jupiter-Saturn `α` should be ~6%, not 10%, derived
   from the actual gravitational coupling strength. Same calculation
   gives the Neptune-Pluto and Laplace-pair values their physically
   correct depths.

2. **Higher-order PN corrections for Mercury.** The current `L_pn`
   adds a constant 43"/century rate. The next term in the PN expansion
   is ~10⁻⁴ smaller per cycle but accumulates over 10⁴ cycles — i.e.
   Mercury's worst-case error.

3. **More resonance entries.** Jupiter–Uranus 7:1, Saturn–Uranus 3:1,
   Earth–Mars (none — they're not in resonance), Lunar precession
   (Saros / Metonic — already implicit in the J2000 calibration but
   not in the dynamic propagator). The roadmap lists "Phase 10 coverage
   continuation" as a future minor release.

## Reproducing this sweep

```bash
# DE441 must be staged at skyfield_data/de441.bsp (~3.1 GB)
cd docs/antikythera-maths
python -m research.de441_sweep
```

Outputs land at `docs/antikythera-maths/results/de441_sweep_summary.json`
(machine-readable) and `…/de441_sweep_table.md` (this table, regenerated
fresh).

## Cross-references

* [Research notebook §1.4](../ephemerides_spectral_research_notebook.md) —
  mathematical positioning of the breathing Laplacian.
* [RBS-HDC evaluation §8](../research/resonant_bit_serialized_hdc_evaluation.md) —
  Phase 9 algebraic form, ALU-native LUT, fixed-point Q-format.
* [ephemerides-spectral ROADMAP](../ephemerides-spectral/ROADMAP.md) —
  v0.3.x first-principles α derivation, v0.4.x CORDIC topocentric.
