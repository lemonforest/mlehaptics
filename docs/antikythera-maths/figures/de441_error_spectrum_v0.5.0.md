# DE441 error spectrum — v0.5.0 (38-body roster) vs v0.3.1 (26-body roster)

Re-run of the per-body FFT residual analysis on the v0.5.0 encoder
(38 bodies: original 26 + Jupiter inner regulars + classical
Saturnian moons + Saturn co-orbitals + 3 new Saturnian/Jovian
resonances). User's instruction: "don't ship before we sweep against
DE441 and look for signals to FFT."

## Headline finding: the planet FFT signature is unchanged

For the 10 bodies that JPL DE441 has ephemeris truth for —
**earth, jupiter, mars, mercury, moon, neptune, pluto, saturn,
uranus, venus** — every FFT residual peak amplitude in v0.5.0 is
byte-for-byte identical to the v0.3.1 baseline.

| Body    | Top peak (period yr, amplitude °) | v0.3.1  | v0.5.0  | Δ |
|---|---|---|---|---|
| earth   | 5.31 yr, 0.93°  | 0.93°  | 0.93°  | 0.00 |
| jupiter | 9.56 yr, 44.6°  | 44.63° | 44.63° | 0.00 |
| mars    | 7.96 yr, 3.45°  | 3.45°  | 3.45°  | 0.00 |
| mercury | 10.69 yr, 9.19° | 9.19°  | 9.19°  | 0.00 |
| moon    | 7.29 yr, 2.44°  | 2.44°  | 2.44°  | 0.00 |
| saturn  | 9.56 yr, 45.0°  | 45.02° | 45.02° | 0.00 |
| neptune | 168 yr, 0.43°   | 0.43°  | 0.43°  | 0.00 |
| pluto   | 252 yr, 13.1°   | 13.12° | 13.12° | 0.00 |
| uranus  | 84 yr, 2.69°    | 2.69°  | 2.69°  | 0.00 |
| venus   | 505 yr, 0.27°   | 0.27°  | 0.27°  | 0.00 |

The full per-body table at `results/de441_error_spectrum.md` is
identical to the v0.3.1 baseline aside from two metadata fields
(native-encoder flag flipped from False → True; total encode time
dropped from 314.9 s → **14.6 s**, a **21× speedup** thanks to the
C native path).

## Why the signal is unchanged

v0.5.0's structural changes are:

1. **+12 moons** in `BODIES`. Each gets a new omega_diag entry and
   a new moon–planet static coupling.
2. **+3 resonance entries** in `RESONANCES`: Mimas–Tethys 4:2,
   Enceladus–Dione 2:1, Titan–Hyperion 4:3.

For the 10 DE441-coverable bodies, here's why the spectrum doesn't move:

- **omega_diag for the 10 bodies is unchanged.** Their orbital
  periods didn't change between releases.
- **Planet–planet `L_static` couplings are unchanged.** The new
  couplings are moon–planet, but the FFT'd bodies aren't moons (except
  Earth's Moon, whose moon–earth coupling is unchanged).
- **The new RESONANCES act between moons, not between moons and
  planets.** Mimas, Tethys, Enceladus, Dione, Titan, Hyperion all
  participate in the new entries, but Saturn itself is in NONE of
  them. Saturn's encoded phase therefore receives no breathing
  modulation from the new physics — its 9.56-yr Jupiter-coupling
  signature stays exactly as v0.3.1 recorded it.

This is mathematically expected: the resonances we wired model
**moon-internal** physics (Mimas-Tethys libration shapes the Cassini
Division; Enceladus-Dione 2:1 forces Enceladus's tidal heating;
Titan-Hyperion 4:3 chaos is in Hyperion's rotation). None of these
back-react on Saturn's mean motion in our coupling topology — they'd
need a Saturn–moon entry, but Saturn doesn't participate in those
resonances physically.

## What this means for shipping v0.5.0

The v0.5.0 expansion is **strictly additive on the FFT validation
surface**:

- ✅ **No regressions** on any of the 10 reportable bodies.
- ✅ **No new smoking-gun peaks** to author patches against (for
  these 10 bodies). The v0.4.0 catalog patches (Mars 7.96 yr,
  Mercury 10.69 yr, Jupiter–Saturn 9.56 yr) remain the right targets.
- ✅ **21× faster sweep** thanks to the v0.4.1 C native + the
  v0.5.0 SPICE-free initial-phases path keeping the encoder running
  natively without runtime calibration overhead.
- ⏳ **The new moons themselves are unvalidated.** DE441 only
  contains the planet barycenters + Sun + Earth + Moon. Galilean
  moons, Saturnian moons, Mars's moons, asteroids — all use a
  period-based fallback initial phase at codegen time (not
  ephemeris truth). To FFT-validate them we need supplementary
  kernels (`jup365.bsp`, `sat441.bsp`, `mar097.bsp`); see roadmap.

## Roadmap — supplementary-kernel moon validation (v0.5.x)

Pull supplementary moon ephemerides into the codegen + sweep:

| Kernel       | Bodies                                  | Size   |
|---|---|---|
| `mar097.bsp` | Phobos, Deimos                          | ~10 MB |
| `jup340.bsp` | Galileans + Amalthea / Thebe / Metis    | ~6 MB  |
| `sat441.bsp` | All major Saturnians (Mimas → Phoebe)   | ~70 MB |

With those staged at codegen time:

1. Initial phases for the moons get baked from real ephemeris truth
   (not the period-based fallback).
2. The DE441 sweep can FFT-compare each moon's encoded longitude
   against ephemeris truth.
3. If the v0.5.0 resonance entries have authored the right physics,
   we should see Mimas/Tethys/Enceladus/Dione/Titan/Hyperion FFT
   peaks at the resonance periods. Authoring catalog patches against
   any residuals is then v0.5.x phase-by-phase.

The wheel does NOT need to ship these kernels — they're codegen-time
inputs, used to bake `_data/initial_phases.json` and the C-side
`es_initial_phases[]`. Runtime stays SPICE-free.

## Verdict

**Ship v0.5.0.** The user-visible promise — "all of Jupiter and
Saturn moons join us" — is delivered: the encoder now integrates 38
bodies including Metis through Phoebe, with all three famous
Saturnian resonances (Cassini Division, Enceladus–Dione, Titan–Hyperion)
modeled. The structural commitment is also delivered: byte-exact
backwards compatibility on the FFT validation surface, the C native
path running 21× faster on the sweep, and a clear roadmap for
moon-validation work in v0.5.x.
