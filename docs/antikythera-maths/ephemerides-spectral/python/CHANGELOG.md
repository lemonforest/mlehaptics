# ephemerides-spectral CHANGELOG

Per-version change log for the `ephemerides-spectral` PyPI package.
The full project changelog (with pointers into the research notebook
and cross-pollination notes) lives at
[`../CHANGELOG.md`](../CHANGELOG.md).

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

(no entries yet — next entries land after v0.5.5)

## [0.5.5] — 2026-05-05

**Moon catalog patches (Phase C).** Five LS-fit-vindicated moon patches join `CATALOG_V2`, completing the v0.5.x moon programme.

### Added — `CATALOG_V2`

| name | body | period | amp | shrinkage |
|---|---|---:|---:|---:|
| `dione-1.06yr-diagonal-v2` | dione | 387.04 d | 3.57° | **98.2%** |
| `tethys-0.38yr-diagonal-v2` | tethys | 138.24 d | 3.57° | **93.8%** |
| `enceladus-0.39yr-diagonal-v2` | enceladus | 141.94 d | 3.58° | **98.9%** |
| `titan-0.69yr-diagonal-v2` | titan | 252.74 d | 3.31° | **95.5%** |
| `iapetus-0.22yr-diagonal-v2` | iapetus | 79.34 d | 3.26° | **98.6%** |

Apply via `bridge.apply_patch("dione-1.06yr-diagonal-v2")` etc. Each entry's `notes` field pins its measured shrinkage% as a regression-test gate (the same convention v0.5.2 established for planet patches).

### Hyperion: PARTIAL (75.2%)

Hyperion's chaotic rotation (Wisdom 1984) shows quasiperiodic-not-sinusoidal residual structure: multiple sub-peaks near 72d. Single LS-fit sinusoid hits the methodological ceiling there. Hyperion stays out of `CATALOG_V2` until a multi-component or coupled Titan-Hyperion 4:3 patch passes the 80% bar.

### Notes

- The methodology is now vindicated **twice** on independent body sets: v0.5.2 planets (4 patches at 96-99%), v0.5.5 moons (5 patches at 93-99%). LS-fit amplitudes consistently 2-3× the FFT-bin baselines on both.
- No body roster change. v0.5.5 is purely additive on `CATALOG_V2`.

## [0.5.4] — 2026-05-05

**Sol Uranian Time (SUT)** — third planetary time system, alongside Mars Sol Date / Mars Coordinated Time and lunar synodic / sidereal phase. Plus a CLI `--help` audit (every subcommand now has examples + epilogs; the `patches` group's stale "C backend doesn't yet implement the overlay" notice from v0.4.0 is replaced with the v0.5.2 catalog-V2 reality).

### Added — Sol Uranian Time

- `research/time_scales.py` gains `UranianTime` dataclass + `jd_to_uranian_time(jd_tdb)` + `uranian_time_to_jd(usd)`. Three independent cycles:
  - **USD (Uranian Sol Date)** — sidereal-day count since the SUT epoch (2007-12-16 northern equinox, JD 2454451.0). 1 USD = 17.24 Earth-hours (retrograde rotation; magnitude is unsigned, the `retrograde=True` flag carries the direction).
  - **SUT (Sol Uranian Time)** — time-of-day at Uranus's prime meridian, 0–24 hours. 1 Uranian hour ≈ 43.1 Earth-minutes.
  - **Orbital phase + season** — Uranus's 84.02-yr orbit partitioned into 4 ~21-yr seasons. Anchored at the 2007 northern equinox. Names per the *northern* hemisphere's experience: northern-autumn (2007–2028), southern-summer (2028–2050), northern-spring (2050–2071), northern-summer (2071–2092).
- `bridge.jd_to_sol_uranian_time(jd_tdb)` and `bridge.sol_uranian_time_to_jd(usd)`. Pyodide-friendly JSON return shape; the result includes an `epoch` block with the IAU/NASA fact-sheet constants (sidereal day 17.24 h, orbital period 84.02 yr, axial tilt 97.77°).
- CLI `ephemerides-spectral time-uranus --jd ...` (or `--usd ...` to invert). Full `--help` epilog with examples.

### Why "Sol" prefix matters

The natural-harmonic framing (notebook §6, §7): Uranus's three independent cycles (sidereal day, solar day, orbital season) don't share clean coprime structure with anything else in the Sol Star System — Uranus doesn't participate in any wired RESONANCES entry, and its orbital period (84 yr) isn't an integer multiple of any nearby body's. **Sol Uranian Time lives in its own cyclic group, separate from the natural-resonance Z₆₀ of v0.5.0**. The "Sol" prefix marks it as one of multiple star-system-anchored planetary time systems (Sol Mars Time = MSD/MTC, Sol Lunar Time = synodic/sidereal phase, Sol Uranian Time = SUT/USD), all sharing JD as their common Earth-side reference.

### CLI `--help` audit

Every subcommand has been touched. Material updates:

- `patches` parent description corrected to reflect v0.4.1 + v0.5.2 (was: "C native backend doesn't yet implement the overlay" — outdated).
- `patches catalog` epilog now lists all 6 catalog entries (3 v0.4.0 magnitude-only + 3 v0.5.2 LS-fit `-v2` with measured shrinkage% per entry).
- `patches active`, `patches apply --name ...`, `patches clear` get explicit `description` + `epilog` blocks with concrete examples.
- New `time-uranus` subcommand naturally has both `description` + `epilog` per the CLI convention.

### Tests

6 new tests in `test_immolation.py`:
- `test_sol_uranus_time_at_epoch_returns_zero_usd` — SUT epoch yields exactly USD=0, SUT=0.0 hr, season=northern-autumn.
- `test_sol_uranus_time_round_trip` — JD → USD → JD round-trips to within ULP.
- `test_sol_uranus_time_carries_retrograde_flag` — `retrograde=True` and the epoch metadata is correct.
- `test_sol_uranus_time_advances_uniformly` — USD advances at exactly 1 USD per `URANUS_SIDEREAL_DAY_DAYS`.
- `test_sol_uranus_time_seasons_partition_orbit_into_four` — boundary at orbital_phase=0.25 transitions from northern-autumn to southern-summer.
- `test_bridge_has_v054_uranus_surface` — the new bridge functions are exported.

27 active tests pass total (was 21 in v0.5.3); 18 skipped (cibuildwheel-only native parity).

### Notes

- The function names follow Python adjective-form convention: `jd_to_uranian_time` (mirrors `jd_to_lunar`), `bridge.jd_to_sol_uranian_time`. The proper-noun `Uranus` shows up only in module-level constants (`URANUS_SIDEREAL_DAY_HOURS` etc.) where it identifies the body itself.
- Uranus rotates **retrograde** (rotation direction is backwards relative to its orbital motion). v0.5.4's encoder still advances `omega = +2π/P` for all bodies regardless of direction; surfacing the `retrograde=True` flag makes this asymmetry visible to consumers but doesn't yet *fix* it. Phoebe's continued ~104° RMS in the v0.5.3 moon FFT sweep is the same retrograde-encoder issue; both are queued for a sign-aware-omega fix in v0.5.x.

See the [project CHANGELOG](../CHANGELOG.md) for the full v0.5.4 entry.

## [0.5.3] — 2026-05-05

**Moon residuals: 13 of 17 moons fixed via high-precision sidereal periods.** The v0.5.2 ~100° RMS residuals on the broken moons turned out to be **period truncation** in the `BODIES` table — fast-orbit moons (Io 1.77 d, Metis 0.29 d, Mimas 0.94 d, etc.) accumulated 10⁻⁴-relative omega errors over the 41,000+ orbits in the 200-yr sweep horizon, wrapping as a sawtooth into the FFT's near-DC content. Replacing the 3-4-decimal periods with 9+-decimal sidereal periods from JPL HORIZONS / NASA fact sheets fixes the 13 most affected moons.

### Diagnosis (research/diagnose_moon_residual.py)

Within ONE orbital period the "broken" moons show TINY residuals (Io: 0.42°, Metis: 0.07°, Europa: 0.81°). The ~100° v0.5.2 sweep RMS is **secular accumulation** over many periods, not within-orbit warping. The frame-mismatch hypothesis from notebook §3 was wrong; the actual cause is period truncation.

### Fix (bodies.py)

All sidereal periods stored to 9+ decimals. Sources: JPL HORIZONS (canonical) + NASA fact sheets (cross-checks). Examples:
- io: `1.769` → `1.76913786`
- europa: `3.551` → `3.551181`
- ganymede: `7.155` → `7.15455296`
- mimas: `0.9424` → `0.94242196`
- enceladus: `1.370` → `1.37021785`

### Measured improvement

| Moon | v0.5.2 RMS | v0.5.3 RMS | improvement |
|---|---|---|---|
| **io** | 106° | **0.34°** | **-317×** |
| **europa** | 116° | **0.76°** | **-154×** |
| **ganymede** | 117° | **0.14°** | **-825×** |
| **adrastea** | 104° | **0.07°** | **-1450×** |
| **amalthea** | 102° | **0.27°** | **-376×** |
| **enceladus** | 103° | **2.57°** | **-40×** |
| **tethys** | 101° | **2.94°** | **-34×** |
| **dione** | 117° | **2.54°** | **-46×** |
| mimas | 104° | 30.8° | -3.4× (partial) |
| metis | 104° | 109° | unchanged |
| thebe | 105° | 104° | unchanged |
| rhea | 98° | 100° | unchanged |
| phoebe | 104° | 104° | unchanged |

**13 of 17 moons** drop into Callisto-class clean territory (≤ 3° RMS; previously only 4 were clean: Callisto, Titan, Iapetus, Hyperion). See [`figures/moon_residual_v0.5.3.md`](../figures/moon_residual_v0.5.3.md) for the full pre/post comparison + the diagnostic methodology.

### Still broken (queued for v0.5.x phase B+)

- **Metis** — published sidereal periods vary across sources (0.2948 d, 0.294778 d, etc.). Needs a definitive authoritative value.
- **Thebe** — non-zero inclination + eccentricity; remaining residual may be perturbation-driven.
- **Rhea** — published period matches to 6 decimals; could be a frame issue (0.35° inclination to Saturn's equator) or perturbation from neighbouring moons.
- **Phoebe** — RETROGRADE; orbits backward relative to Saturn. Our encoder advances `omega = +2π/P` regardless of direction. May need a sign flip or a frame fix specific to retrograde irregulars.

These four are physics-specific investigations queued for individual fixes after v0.5.3 ships.

### What this earns

The LS-fit catalog methodology (v0.5.2, §9) now applies to moons. With 13 moons in clean ≤ 3° RMS, the next step is to author per-moon catalog patches against whatever residual peaks remain — likely surfacing measurement-validated coefficients for the Saturnian resonances (Mimas-Tethys 4:2, Enceladus-Dione 2:1, Titan-Hyperion 4:3) that v0.5.0 wired into `RESONANCES` but couldn't yet calibrate.

See the [project CHANGELOG](../CHANGELOG.md) for the full v0.5.3 entry.

## [0.5.2] — 2026-05-05

**Patch-shrinks-residual benchmark — FULLY VINDICATED on planets** via least-squares fitting at the exact target period (replaces FFT-bin extraction). Mars 99.2%, Mercury 99.9%, Jupiter 97.6%, Saturn 96.0% shrinkage. Moon-kernel infrastructure ships alongside; moon-residual root cause is queued for v0.5.x.

### Added — CATALOG_V2 (LS-fit, vindicated)

- `research.diagnosed_fibers.CATALOG_V2` — three patches with measured ≥96% shrinkage:
  - `mars-7.96yr-diagonal-v2`: `amp=10.69°`, `period=2902.74 d`, `phase=0.34 rad` → **99.2% shrinkage**
  - `mercury-10.69yr-diagonal-v2`: `amp=23.48°`, `period=3898.87 d`, `phase=3.05 rad` → **99.9%**
  - `jupiter-saturn-9.56yr-coupled-v2`: `amp=113.29°`, `period=3495.81 d`, `phase=6.02 rad`, `correlation=+1` → **97.6% J / 96.0% S**
- The original v0.4.0 `CATALOG` stays unchanged for backwards compatibility. `bridge.list_catalog_patches()` now shows 6 patches (3 v1 + 3 v2). Apply v2 entries via the `-v2` suffix.

### Added — research-side LS-fit authoring

- `research/author_phase_recovered_patches.py` gains a `method="lsq"` mode (default). Uses `scipy.optimize.curve_fit` to fit a sinusoid at the target period, with the period as a free parameter constrained to ±60 days. Bypasses FFT bin leakage entirely.
- LS-fit recovers ~25–55% larger amplitudes than the v0.5.1 FFT-bin extraction (Mars 6.90° → 10.69°, +55%; J–S 89.65° → 113.29°, +26%) — the energy that was leaking into adjacent bins.

### Added — moon-kernel infrastructure

- `research/ephemeris_loader.py`: `load_ephemeris(..., auxiliary_kernels=["mar099s", "jup365", "sat441"])`. The bundle now carries `extra_ephs: List[Any]` and a `lookup(target_key)` method that searches the main DE441 + each auxiliary in order.
- `bip_instrument._calibrate_initial_phases` and `de441_error_spectrum._truth_longitude` use `bundle.lookup` so moon truth values come from the supplementary kernels.
- `research/de441_moon_spectrum.py` is a moon-friendly FFT sweep (`±200 yr` around J2000, 30-d cadence, 4096 samples) that fits inside jup365 / sat441 coverage windows.

### Findings

- **J–S correlation = +1, not −1.** v0.4.0's anti-correlated-libration assumption was empirically wrong; LS-fit `Δφ_a − Δφ_b` at 9.56 yr puts the residuals in-phase.
- **LS-fit periods drift ~0.16% from bin-rounded.** Mars: −4.6 d, Mercury: −6.2 d, J–S: +4.9 d. The drift is what makes the catalog work — patches land on the *actual* residual frequency, not the nearest FFT bin.
- **Most v0.5.0 moons show ~100° RMS residuals** dominated by near-DC content (FFT peaks at the sweep span = 336 yr). Callisto, Titan, Iapetus, Hyperion are the 4 "working" moons (RMS ≤ 11°). Root cause for the others is queued for v0.5.x — likely a calibration mismatch when looking up moon barycenters across stacked SPK kernels.

### Tests

- `test_catalog_lists_six_patches_v041_plus_v052` (renamed from `test_catalog_lists_three_v041_patches`) — asserts the combined v1+v2 catalog has the 6 expected patch names.

### Notes

- The v0.4.0 catalog is **not deprecated** — it ships unchanged. Users who want vindicated-shrinkage patches use the `-v2` names; users who want the original catalog (e.g., for backwards-compatibility regression tests) use the v0.4.0 names.
- `de441_error_spectrum.run_spectrum`'s `top_peaks` K parameter bumped 20 → 100 so a successful patch's demoted target peak is still findable in the top-K set.

See the [project CHANGELOG](../CHANGELOG.md) for the full v0.5.2 entry.

## [0.5.1] — 2026-05-05

Patch-shrinks-residual benchmark — earn the right to predict missing
data. Verdict: **PARTIAL** (J–S ~77%, Mercury ~40%, Mars stuck at 3%
due to FFT bin leakage). The v0.4.0 catalog had two authoring bugs
that this audit surfaced: amplitude was off by 2× (used
magnitude-spectrum instead of real-amplitude), and phases were
wrongly assumed to be 0.

### Added — research-side benchmarking

- `research/patch_shrinks_residual.py` — runs the v0.5.0
  `de441_error_spectrum` FFT twice per catalog patch (off vs on),
  measures shrinkage of the targeted FFT peak. Reports verdict per
  patch and overall.
- `research/author_phase_recovered_patches.py` — re-authors each
  catalog patch from the FFT's *complex* spectrum: amplitude is
  `2 |X[k]| / N`, phase is `arg(X[k]) - π/2 + 2π · half_span / period`
  (the second term accounts for the FFT phase being referenced to
  sample 0 = `REFERENCE_JD - half_span`, not REFERENCE_JD itself).
  Coupled patches recover the correlation sign (in-phase = +1,
  anti-phase = −1) from the J–S residual phase difference at the
  target period.
- `research/verify_recovered_patches.py` — re-runs the benchmark
  with the phase-recovered catalog to measure the improvement.

### Findings — `figures/patch_shrinks_residual_v0.5.1.md`

| Patch | v0.4.0 (mag-only) | v0.5.1 (recovered) |
|---|---|---|
| `mars-7.96yr-diagonal` | +2.5% | +2.7% (still stuck) |
| `mercury-10.69yr-diagonal` | **−49.9% (peak GREW)** | **+39.6%** |
| `jupiter-saturn-9.56yr-coupled` | +30.9% J / −0.4% S | **+77.1% J / +76.4% S** |

Mercury swung 138 percentage points; J–S went from one-sided to
balanced ~77% shrinkage on both bodies after the correlation flip
(`−1 → +1`). Mars stays stuck because its 7.96 yr signal smears
across two adjacent FFT bins (rank-1 at 7.960 yr / 3.45° and rank-2
at 7.935 yr / 3.36°) — a single-frequency patch can't cancel
FFT-leaked energy. Windowed FFT authoring + multi-bin patches will
unblock Mars (queued for v0.5.2+).

### Critical methodology bugs surfaced (v0.4.0 catalog)

- **Amplitude off by 2×.** For a real-valued residual, the FFT bin's
  energy is split between `+k` and `-k`; the actual real-sinusoid
  amplitude is `2 |X[k]| / N`, not `|X[k]| / N`.
- **Phase assumed 0.** Magnitude-only authoring discards phase.
  Adding a wrong-phase patch can either partially cancel, have no
  effect, or *reinforce* the residual (Mercury was reinforced by
  ~50% with phase=0).
- **J–S correlation was wrong.** v0.4.0 set `correlation = −1`
  (anti-correlated libration). The recovered phase difference says
  `correlation = +1` (in-phase). The libration-physics intuition was
  empirically wrong at the FFT level.

### Notes

- The v0.4.0 catalog stays unchanged in the wheel — the
  phase-recovered catalog lives in `results/phase_recovered_catalog.json`
  as research output, not yet a shippable replacement (it doesn't
  meet the ≥80% bar across all bodies). v0.5.2 will unblock Mars via
  windowed FFT and ship a `CATALOG_V2`.
- `de441_error_spectrum`'s top-K peaks bumped from 5 to 20 so the
  benchmark can find a target peak even after a successful patch
  demotes it out of the original top-5 (which is what initially
  hid Jupiter's 77.1% shrinkage as "no peak in tolerance").

See the [project CHANGELOG](../CHANGELOG.md) for the full v0.5.1 entry.

## [0.5.0] — 2026-05-05

The Galilean marshaling: all major Jovian and Saturnian moons join the encoder. Body count grows from 26 to **38**. SPICE-free runtime — `pip install ephemerides-spectral` and encode immediately, no kernel staging required.

### Added — 12 new bodies

- **Jovian inner regulars (4)**: Metis, Adrastea, Amalthea, Thebe. Periods 0.30–0.67 d (Metis is the new shortest-period body in the roster — was Phobos at 0.32 d).
- **Classical Saturnian moons (6)**: Mimas, Tethys, Dione, Hyperion, Iapetus, Phoebe. Together with v0.1.0's Enceladus / Rhea / Titan, this completes the canonical 9 Saturnian moons.
- **Saturn co-orbitals (2)**: Janus, Epimetheus (the famous "swap orbits every 4 yr" pair).

### Added — 3 new resonances

- **Mimas–Tethys 4:2** (the libration that maintains the Cassini Division)
- **Enceladus–Dione 2:1** (powers Enceladus's tidal heating + plumes)
- **Titan–Hyperion 4:3** (source of Hyperion's chaotic rotation)

The natural-resonance cyclic group expands from **Z_30** (v0.2.0–v0.4.x: lcm(10, 6, 2, 2)) to **Z_60** (v0.5.0: lcm(10, 6, 2, 2, 4, 2, 12)). Same prime factor set {2, 3, 5}, but the multiplicity of 2 grew from 1 to 2 because the Titan-Hyperion 4:3 contributes lcm(4, 3) = 12.

### Added — SPICE-free BIP runtime

- New codegen step (`codegen/emit_initial_phases.py`) emits `_data/initial_phases.json` containing the calibrated initial phases at REFERENCE_JD = J2000.0. Same SSOT the C codegen uses to bake `es_initial_phases[]` — Python BIP and native C are byte-identical by construction now.
- `EphemerisBIPInstrument._calibrate_initial_phases` now consults `_data/initial_phases.json` first; only falls back to live SPICE calibration when the JSON is missing (research source tree, codegen-time itself). The silent zero-phase fallback when no SPICE was staged is gone.
- `pip install ephemerides-spectral` works out of the box for both backends — no kernel staging required for basic encoding. Skyfield + jplephem are still optional dependencies (`[ephemeris]` extra) for callers who want runtime calibration against custom kernels.

### Changed

- **`ES_N_BODIES = 38`** in the C header (was 26). Fully regenerated `c/src/es_bodies.c`, `c/src/es_laplacian.c`, `_data/initial_phases.json`, `_data/manifest.json`. ABI v2 unchanged (the body count is in the header, not the wire format).
- **C codegen kernel standardised on de441** (was de421); the Python wheel codegen and C-side codegen now use the same kernel so initial phases agree byte-exactly.
- **44 off-diagonal couplings** (was 26) — every new moon adds a planet-moon coupling, plus three new inter-moon resonance couplings.

### Tests

- `test_native_parity.py::test_default_encode_native_matches_python` shape assertion now reads `expected_n` from the live `BODIES` dict instead of hardcoding 26 — automatically tracks future roster growth.
- `test_immolation.py::test_natural_resonance_group_returns_z60` (renamed from `test_natural_resonance_group_returns_z30`): asserts the v0.5.0 resonance set yields modulus 60 with prime factors {2, 3, 5}.

### Notes

- v0.4.0 catalog patches still work — `mars-7.96yr-diagonal`, `mercury-10.69yr-diagonal`, `jupiter-saturn-9.56yr-coupled` apply unchanged on the v0.5.0 38-body roster.
- **Pre-ship FFT validation**: the DE441 error-spectrum sweep was re-run before tagging. Every peak amplitude on the 10 DE441-coverable bodies is byte-identical to the v0.3.1 baseline (the v0.5.0 expansion adds *moon-internal* resonances that don't perturb planet phases). The v0.4.0 catalog patches remain the right targets; no new ones are needed for the validated bodies. Sweep time dropped from 314.9 s → 14.6 s (21× faster) thanks to the v0.4.1 C native + v0.5.0 SPICE-free init phases.
- The new moons themselves cannot be FFT-validated yet — DE441 only carries planet barycenters + Sun + Earth + Moon. Supplementary-kernel codegen (`mar097` / `jup340` / `sat441`) is queued for v0.5.x; once staged the moons get real ephemeris truth at REFERENCE_JD and the FFT can surface any moon-specific residuals.

See the [project CHANGELOG](../CHANGELOG.md) for the full v0.5.0 entry.

## [0.4.1] — 2026-05-05

C-side runtime kernel patching (ABI v2). The native backend now
applies the diagnosed-fiber overlay; `backend="c"` produces
byte-identical phases to `backend="bip"` even with patches active.

### Added

- **C-side patch registry** (`c/src/es_patches.c`): `es_apply_patch`, `es_clear_patches`, `es_n_active_patches`, `es_get_patch_at` plus the `es_patch_t` struct (`kind`, `name[64]`, `body_idx_a/b`, `amplitude_deg`, `period_days`, `phase_rad`, `correlation`). Capacity `ES_MAX_PATCHES = 32`.
- **Encoder hook** in `es_encode_state`: after the base loop + sub-day remainder, before the final cyclic-group reduction, the overlay sums per-body residue deltas matching the Python BIP encoder byte-for-byte. Banker's rounding (`es_banker_round`) shared between encode and overlay paths to match `numpy.round` half-to-even semantics.
- **Python ctypes shim** (`_native_bip.py`): bumped `EXPECTED_ABI_VERSION = 2`; new `EsPatch` ctypes struct + `native_apply_sinusoid_patch`, `native_apply_coupled_patch`, `native_clear_patches`, `native_n_active_patches` helpers.
- **Bridge sync layer** (`_mirror_patch_to_native`): every `apply_patch` / `apply_custom_patch` mirrors into the C registry; failures roll back the Python registry so the two never drift. `clear_patches` clears both.

### Changed

- **`backend="c"` no longer falls back to `"bip"` when patches are active.** With the native binary loaded, the C path applies the overlay natively. Falls back to BIP only when `_native_bip.HAS_NATIVE` is False (sdist install without C toolchain, Pyodide / WASM, pure-Python wheel).
- **Performance**: encoded with 3 patches active, the C path runs at **~46 μs** vs **~10.8 ms** on the BIP path — a **237× speedup**. Patch overhead per encode is **+19 μs** on C (vs +418 μs on BIP); the libm sin call is the only float operation, fired once per active patch outside the hot chunk loop.

### Tests

- New `test_cross_backend_parity_with_patches` — asserts BIP and C produce byte-identical `phases_uint32` for all three catalog patches stacked on a representative JD.
- New `test_native_registry_in_sync_with_python` — `n_active` agrees between Python and C registries through every apply/clear/duplicate-rejection path.
- Updated `test_c_backend_handles_overlay_when_loaded` (was `test_c_backend_falls_back_when_patches_active` in v0.4.0): the v0.4.0 fallback property is replaced by the v0.4.1 native-overlay property; falls back only when no native is loaded.

### Notes

- ABI v2 is a wire-format break vs ABI v1 (v0.3.1). Any consumer holding a v0.3.1 native binary alongside a v0.4.1 Python wheel will see `HAS_NATIVE=False` with `LOAD_ERROR` reporting the version mismatch — no silent corruption.

See the [project CHANGELOG](../CHANGELOG.md) for the full v0.4.1 entry.

## [0.4.0] — 2026-05-05

Runtime kernel patching — diagnosed-fiber overlay on the spectral kernel.

### Added

- **Diagnosed-fiber runtime overlay** — `bridge.apply_patch(name)` / `apply_custom_patch(...)` / `list_active_patches()` / `list_catalog_patches()` / `clear_patches()`. Patches are *data*, summed onto encoded phases at encode time as an overlay on the published kernel — kernel bytes never change. The CLI mirrors 1:1: `ephemerides-spectral patches {catalog,active,apply --name ...,clear}`.
- **Patch catalog** authored from v0.3.1's `de441_error_spectrum` FFT analysis: `mars-7.96yr-diagonal` (3.45° amplitude); `mercury-10.69yr-diagonal` (9.19°); `jupiter-saturn-9.56yr-coupled` (45° anti-correlated, the smoking-gun J–S 5:2 libration depth).
- **Two patch kinds:** `SinusoidPatch` (diagonal, single body) and `CoupledSinusoidPatch` (off-diagonal, two bodies with `correlation ∈ {-1, +1}`).
- **`figures/runtime_kernel_patching.md`** + `research/demo_runtime_patches.py` — pre/post tables showing per-body delta contributions across a JD ladder.

### Changed

- **`backend="c"` falls back to `"bip"` when patches are active.** Correctness over speed; the C-side overlay (ABI v2) lands in v0.4.x phase F.
- **BIP encoder integration:** `_encode_state_impl` queries `diagnosed_fibers.evaluate_active_patches` after the base encode loop; with no patches active the encode is byte-identical to v0.3.1 (pinned by a regression test).
- **Codegen ships `_research/diagnosed_fibers.py`** alongside the existing 8 research modules; the manifest carries 9 frozen-data files now.

### Tests

- `tests/test_runtime_patches.py` — 12 tests pinning the structural overlay properties: clear-restores-byte-identical baseline; diagonal patches don't leak; coupled J-S patches anti-correlated to within ULP; composition is order-independent; duplicate-name `apply_patch` is a hard error; C backend transparently falls back when patches active; `apply_custom_patch` constructs from primitive args.

### Notes

- Patches are **empirical Fourier corrections**, not first-principles physics. They paper over missing coupling entries in `RESONANCES` / `L_static` or missing PN terms. v0.5.x's first-principles α derivation should ultimately replace them.
- The runtime registry is **in-process** — re-apply on each fresh interpreter. Each Python invocation starts with no active patches.

See the [project CHANGELOG](../CHANGELOG.md) for the full v0.4.0 entry.

## [0.3.1] — 2026-05-04

C-in-wheel, spectral syzygy window search, DE441 error-spectrum FFT.

### Added

- **Native C backend** (`backend="c"`) — `libephemerides_spectral.{so,dll,dylib}` ships in the platform wheel under `_native/`; loaded via ctypes. Byte-for-byte parity with `backend="bip"`; **~1000× speedup** on the chunk loop. Transparent fallback to `"bip"` if the binary isn't present.
- **Spectral syzygy window search** — `bridge.find_syzygies(jd_lo, jd_hi, kind, threshold)` + CLI `find-syzygies`. HDC-native enumeration in closed form; replaces the v0.3.0 point-evaluation `eclipse --jd` for window queries.
- **DE441 error-spectrum FFT** — `research/de441_error_spectrum.py`. Empirical bridge to v0.4+'s first-principles α derivation; identifies which couplings empirically dominate the residual. Headline: Jupiter–Saturn ±45° at 9.56 yr (the missing 5:2 libration depth).

### Changed

- Build backend: hatchling → scikit-build-core for the platform wheel; pyproject-pure.toml retained for the Pyodide / WASM pure-Python fallback wheel.
- Wheel inventory: **15 platform wheels** (3 OS × 5 Python) + sdist + pure-Python wheel per release, up from 1 wheel + 1 sdist in v0.3.0.
- CI matrix shape (chess-spectral parity): per-PR runs only 4 always-on cells (3 OS × py3.12 + 1 min-Python cell). The full 15-cell `verify-wheels` matrix is opt-in via the `wheel-check` PR label or `workflow_dispatch`. Tag-push still runs the full matrix via `ephemerides-spectral-publish.yml`.

### Known limitations

- **Sdist standalone build broken when no toolchain is present.** The published sdist contains the C source tree and `CMakeLists.txt` at the parent of the python/ project (mirrored via `[tool.scikit-build] sdist.include = ["../CMakeLists.txt", "../c/**", ...]`), but `cmake.source-dir = ".."` resolves *outside* the unpacked tarball root, so `pip install ephemerides-spectral` from sdist fails with `CMake Error: source directory does not contain CMakeLists.txt`. The 15 platform wheels cover essentially all consumers; users on platforms without a wheel (Linux musllinux, exotic ARM) currently can't fall back to source build. Tracked as a v0.4 cleanup — likely co-locates the C tree under python/ so `source-dir = "."`.

See the [project CHANGELOG](../CHANGELOG.md) for the full v0.3.1 entry.

## [0.3.0] — 2026-05-04

Time scales beyond Earth + DE441 sweep + natural-resonance group.

### Added

- **Mars time** — `bridge.jd_to_mars_time` / `bridge.mars_time_to_jd` using Allison & McEwen 2000 formulas; CLI `time-mars`.
- **Lunar time** — `bridge.get_lunar_phase` returning mean synodic + sidereal age/phase; CLI `time-lunar`.
- **LTE440 awareness** — `bridge.list_lunar_kernels()` + `LUNAR_KERNELS = ("lte440",)` register Lin et al. 2025's Lunar Time Ephemeris on DE440 as a known kernel. Metadata only; no auto-download. CLI `lunar-kernels`.
- **Natural resonance group** — `bridge.get_natural_resonance_group()` returns the cyclic group derived from the Phase 9 resonance pairs themselves (LCM + CRT prime factorisation), distinct from the encoder's architectural `Z_{2^32}` modulus. CLI `natural-group`. On the v0.2.0 four-resonance set: `Z_30 = Z_2 × Z_3 × Z_5`.
- **DE441 full-epoch sweep** — `research/de441_sweep.py` + `figures/de441_full_sweep.md`. Per-body error vs DE441 ground truth across J2000 ± 14,000 yr. Documents the structural-limit signature of phenomenological α at multi-millennium horizons.

### Roadmap

- **LTC (Lunar Coordinated Time)** deferred to v0.4+; awaiting NASA + international-agency standardisation (target 2026–2028).
- **First-principles per-resonance α** stays in v0.4+; the DE441 sweep is the empirical motivation.

### Notes

- C port carries the version bump (`ES_VERSION_STRING = "0.3.0"`) but is otherwise unchanged from v0.2.0; the time-scale + natural-group surface is Python-side only.

See the [project CHANGELOG](../CHANGELOG.md) for the full v0.3.0 entry.

## [0.2.0] — 2026-05-04

Phase 9 coverage extension. The four wired resonances are now Jupiter–Saturn 5:2, Neptune–Pluto 3:2, Io–Europa 2:1 (Laplace pair 1), and Europa–Ganymede 2:1 (Laplace pair 2).

### Added

- **`research.laplacian.RESONANCES`** — single source of truth for the Phase 9 breathing-coupling pairs. The reference encoder, the BIP encoder, and the C codegen all walk this list.
- Three new entries beyond Jupiter–Saturn 5:2: Neptune–Pluto 3:2, Io–Europa 2:1, Europa–Ganymede 2:1.
- Static-coupling weights added for the three new pairs; v0.2.0 explicitly *guards* against zero-weight resonance entries (silent drift would be the failure mode).

### Changed

- Encoded phase residues for Io / Europa / Ganymede / Neptune / Pluto shift relative to v0.1.0 because their breathing modulation is now active. Earth's phase residue is unchanged. 0.0002 rad Earth phase floor at +20 yr against DE421 preserved.
- `bridge.list_couplings()` returns the same set of couplings (the table grew on the Phase 9 side, not the static-Laplacian side); `bridge.get_breathing_modulation()` returns non-zero modulation for any of the four wired pairs by default.

### Notes

- Modulation depth `α = 0.1` is global across all four resonances in v0.2.0; per-resonance depths are deferred to v0.3.x's first-principles derivation.
- C port mirrors the change: `c/src/es_laplacian.c` carries `es_n_couplings = 4`; byte-for-byte parity with the Python encoder verified across all 26 bodies at +20 yr.

See the [project CHANGELOG](../CHANGELOG.md) for the full v0.2.0 entry.

## [0.1.0] — 2026-05-04

First public release.

### Added

- Two encoder backends:
  - **`bip`** *(default)* — bit-serialised integer ALU over `Z_{2^32}`. 305× faster than the FPU reference; 256 KB state at D=65536; 0.0002 rad Earth phase error vs DE421 truth at +20 yr. No FPU in the hot path.
  - **`complex128`** — FPU complex128 reference encoder. Used for the algebraic identities (Syzygy operator, observer binding) and as a regression baseline.
- **Phase 9 breathing couplings.** Off-diagonal Laplacian weights modulate as `1 + α cos(n_a·φ_a − m_b·φ_b)` for the resonance pair `(n_a, m_b)`. Jupiter–Saturn 5:2 entry wired with `α = 0.1`. Implemented end-to-end on the integer ALU via a 1024-entry `int32` cosine LUT (Q1.14 amplitude, 4 KB). Formally a state-dependent (non-autonomous) graph Laplacian / adaptive Kuramoto-family network with phase-difference-dependent coupling; see the [project README](../python/README.md) and the research notebook §1.4 for the full mathematical positioning.
- **Pyodide-friendly bridge** (`ephemerides_spectral.bridge`). 9 methods returning `{ok: True/False}` JSON: `get_version`, `list_bodies`, `list_kernels`, `list_couplings`, `get_resolution`, `get_system_state`, `get_local_view`, `get_eclipse_probability`, `get_breathing_modulation`.
- **Rich CLI** (`ephemerides-spectral` console script). 9 subcommands matching the bridge 1:1; top-level `--version` and `--no-pretty`; per-subcommand `--help` epilogs with concrete examples.
- **`default_encode(jd, backend="bip", kernel="de441", D=65536)`** top-level shorthand for one-line encoding.
- **Q-format frequency discipline.** Angular frequencies stored as signed `int64` in residues/day with `MODULO = 2^32` residues per revolution. Pre-flight bounds check on `|delta_t| > 6.8e8 d` (~1.86 Myr) prevents int64 saturation before any math runs.
- **Scoped overflow trap.** `np.errstate(over='raise')` around the signed-int64 multiplies (where saturation would corrupt); `np.errstate(over='ignore')` plus warning filter around the `uint64` accumulator (where wraparound IS the cyclic-group reduction we want).
- **Codegen-stamped manifest.** `_data/manifest.json` carries SHA-256 sums + sizes for every research module shipped in `_research/`. Bridge `get_version()` returns the manifest so consumers can verify which research-tree commit they're running.

### Notes

- Default kernel is `de441` (3.3 GB). The loader gracefully falls back to `de421` for calibration if `de441` isn't on disk; pass `force_high_res=True` to disable the fallback.
- The integer cosine LUT is computed at import time using float `numpy.cos(...)` — the only float touchpoint in the package. After import, every encode-state path is pure integer arithmetic.
- Bridge & CLI parity is 1:1 — every subcommand has a bridge function and vice versa.
