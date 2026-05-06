# ephemerides-spectral

> **High-precision HDC reference instrument for the Sol Star System.**

**Status: v0.13.4 — production-ready.** Three interchangeable backends (BIP integer ALU, native C, FPU complex128); 38-body roster; full Sol Symphony Times; **Sol Terra-Luna Time (STLT)** with Meton's 432 BCE solstice as the default epoch; **Sol Proper Time (SPrT)** with `--proper`; **Sol Kinematics** (v0.12.0) with `--state` and `kinematics` query; **Sol Dynamics** (v0.13.0) with `--dynamics` and `dynamics` query — system energy / per-body energy budgets / pair-wise gravitational forces, validated against the textbook 3.54×10²² N Earth-Sun figure to 0.01 % and the virial theorem to 0.5 %; adaptive ("breathing") couplings under their mainstream-literature name (Gross & Blasius 2008); JPL Power-of-Ten audit baseline (v0.11.2) with **Rule 1 + Rule 3 cleared** (v0.13.4 — 33% of audit-baseline violations down in one ship); pre-merge docs+parity hygiene check (v0.13.3) as a soft-warning GitHub Actions workflow. See the [Status](#status) section below for the version-by-version landing record.

## Overview

`ephemerides-spectral` is a hyperdimensional-computing instrument that encodes the barycentric state of our star system using high-precision ephemeris data (NASA JPL DE441 / DE442) as resonant phases over a graph Laplacian.

Three interchangeable backends ship with the package:

* **`bip`** *(default)* — bit-serialised integer ALU in pure Python. Phase composition lives in the cyclic group `Z_{2^32}`; binding is `(φ_1 + φ_2) mod 2^32`, which is implicit `uint32` overflow — no FPU in the hot path. 305× faster than the FPU reference; 256 KB state at `D=65536`. Always available.
* **`c`** *(v0.3.1+)* — native C library (`libephemerides_spectral.{so,dll,dylib}`) bundled in the platform wheel under `_native/`, loaded via ctypes. **Byte-for-byte identical** phase residues to `bip`; **~1000× speedup** on the chunk loop (encode at +20 yr: 46 ms Python → 0.04 ms C). Falls back transparently to `bip` if the binary isn't loadable (sdist installs without a C toolchain, Pyodide / WASM, the pure-Python fallback wheel).
* **`complex128`** — FPU reference encoder with unit-norm complex Gaussian bases. Used for the algebraic identities (Syzygy operator, observer binding) and as a regression baseline.

Both backends implement the same algebraic substrate (cyclic-group representation of celestial phase-space, graph-Laplacian eigenbasis); they trade precision for speed.

### Companion Project

`ephemerides-spectral` lives in the same `docs/antikythera-maths/` folder as **antikythera-spectral** because the two share the spectral / cyclic-group framing and the Pyodide bridge contract. They are *not* consolidated: antikythera-spectral encodes a specific bronze-age mechanism (940-tooth Callippic gear DAG) while ephemerides-spectral encodes the live JPL DE441 ephemeris with phase-dependent (breathing) gravitational couplings. The chess-spectral notebook §20.13–§20.17 calls out the cross-pollination — chess uses `Z_{640}` (paying an explicit `% 640` per op); ephemerides uses `Z_{2^32}` (free `uint32` overflow).

### Key Capabilities

- **Graph Laplacian Propagator:** Diagonal content = Newtonian mean motions + Mercury 43"/century post-Newtonian correction. Off-diagonal = gravitational fiber couplings (planet-sun, moon-planet, mean-motion resonances, asteroid-Jupiter).
- **Phase 9 Adaptive Couplings (a.k.a. "breathing") (v0.9.2 CLI rename):** Off-diagonal weights modulate with the resonant phase difference `cos(n_a·φ_a − n_b·φ_b)`. Formally a **state-dependent (non-autonomous) graph Laplacian** / **adaptive Kuramoto-family network with phase-difference-dependent coupling** (Gross & Blasius 2008, "Adaptive coevolutionary networks") — see the [research notebook §1.4](https://mlehaptics.readthedocs.io/en/latest/antikythera-maths/ephemerides_spectral_research_notebook/#14-mathematical-positioning-of-the-breathing-laplacian) for the full positioning across spectral-graph-theory / dynamical-systems / DNLS-on-a-graph vocabularies. CLI: `ephemerides-spectral adaptive --jd ...` (canonical) or `ephemerides-spectral breathing --jd ...` (visual-metaphor synonym; same handler, identical output). Implemented end-to-end without FPU using a 1024-entry `int32` cosine LUT (Q1.14 amplitude, 4 KB).
- **Sol Star System Roster (v0.5.0+):** **38 bodies** — Sun, 9 planets (incl. Pluto), 24 moons, 4 main-belt asteroids. The moon set covers Earth's Moon, Mars's Phobos / Deimos, **all 4 Galileans (Io, Europa, Ganymede, Callisto) plus the 4 inner regulars (Metis, Adrastea, Amalthea, Thebe)**, **the canonical 9 Saturnians (Mimas, Enceladus, Tethys, Dione, Rhea, Titan, Hyperion, Iapetus, Phoebe) plus the Janus / Epimetheus co-orbitals**, Uranus's Titania, and Neptune's Triton.
- **Mean-motion resonances (v0.5.0+):** 7 entries in `RESONANCES` — Jupiter–Saturn 5:2, Neptune–Pluto 3:2, Io–Europa 2:1, Europa–Ganymede 2:1, **Mimas–Tethys 4:2 (Cassini Division), Enceladus–Dione 2:1 (powers Enceladus tidal heating), Titan–Hyperion 4:3 (Hyperion's chaotic rotation)**. Natural-resonance gear group: `Z_60 = Z_4 × Z_3 × Z_5`.
- **Runtime kernel patching (v0.4.0+):** Diagnosed-fiber overlay — patches sit beside the published kernel as DATA, not code edits, and contribute per-body residue deltas at encode time. Inspired by Linux ksplice / kpatch; the kernel's published bytes never change. Bridge surface: `apply_patch(name)` / `apply_custom_patch(...)` / `clear_patches()`. Three patches in the bundled CATALOG authored from the v0.3.1 FFT residual analysis. **v0.5.1 patch-shrinks-residual benchmark** measured the catalog and showed **partial vindication**: J–S coupled patch shrinks both bodies' residuals by ~77% with phase-recovered authoring (research-side; stays out of the v0.5.x catalog until ≥80% on every body); Mars stays stuck at 3% due to FFT bin leakage. v0.5.2 adds windowed FFT + multi-bin patches for full predictive power.
- **SPICE-free runtime (v0.5.0+):** `pip install` works out of the box — both backends use codegen-baked initial phases shipped in `_data/initial_phases.json`. No SPICE kernel staging required for basic encoding. Skyfield + jplephem stay as optional `[ephemeris]` extras for callers who want runtime recalibration against custom kernels.
- **Observer-Agnostic Views:** Unitary binding to generate topocentric "Local View" hypervectors at any (lat, lon) on any body.
- **Spectral Syzygy Window Search (v0.3.1+):** `find-syzygies --from-jd ... --to-jd ...` enumerates candidate syzygies in closed form via the natural cyclic-group decomposition (synodic + draconic month), then confirms each by spectral projection. ~1000× faster than the v0.3.0 point-evaluation `eclipse --jd` pattern for window queries.
- **ITN Pathway / Lagrange-Tube Query (v0.8.1+):** `find-tubes --from-jd ... --to-jd ... --departure terra --target mars` enumerates Hohmann transfer windows via the same closed-form `find-syzygies` discipline. "Surfing the perturbations" — the natural cyclic structure tells you when launch windows open without integrating any trajectories. First-cut Hohmann math; future versions layer low-energy / heteroclinic-tube candidates under the same surface (`transfer_kind` field reserves room). References: Koon-Lo-Marsden-Ross 2011; Lo's Genesis trajectory work.
- **Sol Symphony Times (v0.3.0 + v0.5.4 + v0.8.0 + v0.9.1):** every body in the Sol Star System has a "Sol Time" exposing its rotational + orbital cycles anchored to a conventional epoch — Mars Sol Date / Mars Coordinated Time (Allison & McEwen 2000), Sol Lunar Time (Luna's synodic + sidereal phase observed from Terra), Sol Uranian Time (USD/SUT, anchored at the 2007 northern equinox), Sol Venus / Sol Mercury / Sol Pluto / Sol Terra / Sol Luna (rocky bodies + Sun + Luna in direct Latin proper-noun form), Sol Sol (the Sun, Carrington rotation system), Sol Jovian / Sol Saturnian / Sol Neptunian (gas/ice giants in established adjective form). **The Solar System is a natural symphony of overlapping clocks**; Sol Time is just the package telling you what time it is on each body so you can correlate that body's local clock with JD. Naming hierarchy for future moon ports: `Sol <Parent>-<Body> Time` (e.g., Sol Pluto-Charon Time).

### Naming convention (v0.9.x)

The body-identity strings use Latin proper nouns: `terra`, `luna`. The generic English words `earth` (= soil, ground) and `moon` (= any natural satellite) return to their generic meanings.

> *"Returning to the giants whose shoulders we stand on. We've always had a lunar orbit and a lunar eclipse. We've all had terrain and terrestrial animals. We're just putting the books back in their dewey decimal spot. We no longer kow tow for the sake of leaning forward."*

The adjective forms `lunar`, `terran`, `terrestrial` always derived from `Luna` and `Terra` — the language already carried the convention. v0.9.0 made the body-identity strings reflect what the language always implied. v0.9.1 extends this to the Sol Time series itself: rocky bodies + Sun + Luna use direct Latin proper nouns; gas/ice giants keep the established astronomical adjective forms (Jovian, Saturnian, Uranian, Neptunian).

| Body | Sol Time | Abbrev | CLI |
|---|---|---|---|
| Mercury | Sol Mercury Time | SMeT | `time-mercury` |
| Venus | Sol Venus Time | SVT | `time-venus` |
| Terra | Sol Terra Time | STT | `time-terra` |
| Mars | Sol Mars Time (= MSD/MTC) | SMaT | `time-mars` |
| Luna | Sol Terra-Luna Time | STLT | `time-terra-luna` |
| Jupiter | Sol Jovian Time | SJT | `time-jupiter` |
| Saturn | Sol Saturnian Time | SST | `time-saturn` |
| Uranus | Sol Uranian Time | SUT | `time-uranus` |
| Neptune | Sol Neptunian Time | SNT | `time-neptune` |
| Pluto | Sol Pluto Time | SPT | `time-pluto` |
| Sol | Sol Sol Time | SSoT | `time-sol` |

**Moons follow the `Sol <Parent>-<Body> Time` convention** — Luna's primary Sol Time is *Sol Terra-Luna Time* (STLT) because Luna is gravitationally bound to Terra; the Parent-Body name keeps the moon-stuck-to-parent relationship visible in the time hierarchy. STLT counts synodic months from a historically-significant epoch (default: Meton's 432 BCE summer solstice). The future Pluto-Charon, Jupiter-Io, Saturn-Titan, etc. moon Sol Times will follow the same `Sol <Parent>-<Body> Time` pattern — see task #86.

A separate, lower-level **Sol Luna Time (SLT)** also exists — Luna's tidally-locked surface clock (sidereal=orbital=27.32 d, solar=synodic=29.53 d) anchored at J2000. SLT is queryable via `time-luna` and `bridge.jd_to_sol_luna_time`; it's the right surface for "what time is it on Luna's prime meridian" rather than "how many synodic months since a Greek-historical event." The two are complementary, not redundant: STLT is anchored Lunar *time* (count); SLT is Luna's *clock* (rate).

### Resolution Scaling

Temporal resolution of a residue shift scales inversely with hypervector dimension `D`:

| `D`     | Earth resolution | Use case                    |
| :------ | :--------------- | :-------------------------- |
| `2^16`  | ~8 minutes       | default; long-term mapping  |
| `2^19`  | ~1 minute        | medium-cadence events       |
| `2^25`  | ~1 second        | high-cadence local readout  |

## Installation

```bash
pip install ephemerides-spectral
```

For full ephemeris support (skyfield + JPL DE-kernels):
```bash
pip install "ephemerides-spectral[ephemeris]"
```

## CLI Usage

The package ships a rich `ephemerides-spectral` console script. Use `--help` on the top-level or any sub-command:

```bash
ephemerides-spectral --help
ephemerides-spectral encode --help
ephemerides-spectral adaptive --help
```

### Sub-command Cheat-Sheet

```bash
# Package version + frozen-data manifest
ephemerides-spectral version

# All 38 bodies in the Sol Star System Laplacian
ephemerides-spectral bodies

# Earth temporal resolution at the default D=65536
ephemerides-spectral resolution --body terra

# Encode J2000 with the integer ALU backend (default)
ephemerides-spectral encode --jd 2451545.0

# Same JD with the FPU complex128 reference encoder
ephemerides-spectral encode --jd 2451545.0 --backend complex128

# Topocentric view from London at J2000
ephemerides-spectral local-view --jd 2451545.0 --body terra --lat 51.5 --lon -0.1

# Syzygy alignment probability AT a JD (point evaluation; encode-then-check).
# For window queries, see `find-syzygies` below (closed-form spectral search,
# ~1000× faster than encode-then-check across long windows).
ephemerides-spectral eclipse --jd 2451545.0

# Off-diagonal couplings (Laplacian fiber bundle)
ephemerides-spectral couplings

# Phase 9 adaptive (a.k.a. "breathing") coupling modulation
# (Jupiter-Saturn 5:2 by default). Both `adaptive` and `breathing`
# work — `adaptive` is the canonical name (matches the adaptive-
# networks / adaptive-Kuramoto literature, Gross & Blasius 2008);
# `breathing` is the visual-metaphor synonym, kept for users who
# learned the couplings as inhaling/exhaling with the resonant phase.
ephemerides-spectral adaptive --jd 2458850.0

# Override resonance: 3:2 Neptune-Pluto
ephemerides-spectral adaptive --jd 2451545.0 \
    --pair-a neptune --pair-b pluto --n-a 3 --n-b 2

# Synonym (same handler, identical output):
ephemerides-spectral breathing --jd 2458850.0

# Mars Sol Date / Mars Coordinated Time at a JD (v0.3.0)
ephemerides-spectral time-mars --jd 2451549.5     # → MSD ≈ 44795.99
ephemerides-spectral time-mars --msd 50000        # invert: MSD → JD_UTC

# Mean lunar synodic + sidereal age/phase at a JD (v0.3.0)
ephemerides-spectral time-lunar --jd 2451545.0

# Sol Uranian Time (v0.5.4) — third planetary time system alongside Mars + Lunar
# USD (sidereal-day count since 2007 northern equinox), SUT (Uranian time-of-day),
# orbital phase + season, retrograde flag.
ephemerides-spectral time-uranus --jd 2454451.0   # → USD = 0.0 at SUT epoch
ephemerides-spectral time-uranus --usd 4046       # invert: USD → JD_TDB

# Sol Symphony Times (v0.8.0) — Venus, Mercury, Pluto, Sol (the Sun!),
# Jupiter, Saturn, Neptune each have their own "Sol Time" exposing rotational + orbital phase.
# Each handles its body's quirks: Mercury's 3:2 spin-orbit resonance, Venus's
# retrograde rotation (sidereal day > year!), Sol's differential rotation
# (Carrington system), Jupiter System III, Saturn Cassini-revised System III.
ephemerides-spectral time-venus --jd 2451545.0
ephemerides-spectral time-mercury --jd 2451545.0  # 3:2 resonance: solar day = 2 × year
ephemerides-spectral time-pluto --jd 2457217.0    # New Horizons closest approach
ephemerides-spectral time-sol --jd 2451545.0      # Sun's own Carrington Rotation Number
ephemerides-spectral time-jupiter --jd 2444000.5
ephemerides-spectral time-saturn --jd 2451545.0
ephemerides-spectral time-neptune --jd 2451545.0

# Sol Terra Time (v0.9.1) — Terra's surface clock
# Sidereal day 23h 56m 4s (rotation rel. stars), solar day 24h (rel. Sun)
ephemerides-spectral time-terra --jd 2451545.0    # J2000 anchor

# Sol Luna Time (v0.9.1) — Luna's surface clock
# Tidally locked: sidereal=orbital=27.32d, solar=synodic=29.53d
# DISTINCT from Sol Lunar Time (time-lunar) which gives Luna's phase observed from Terra
ephemerides-spectral time-luna --jd 2451545.0     # J2000 anchor

# ITN pathway / Lagrange-tube query (v0.8.1) — Hohmann transfer windows
# "surfing the perturbations" via closed-form synodic enumeration
ephemerides-spectral find-tubes --from-jd 2451545.0 --to-jd 2470000.0 \
    --departure terra --target mars
# Output: 23 Terra->Mars windows over ~50 years, each with transfer time
# (~258.9 days) + total Δv (~5.59 km/s)

# Lunar-time kernel metadata (LTE440 + LTC status; v0.3.0)
ephemerides-spectral lunar-kernels

# Resonance-derived natural cyclic group (v0.3.0; expanded to Z_60 in v0.5.0)
ephemerides-spectral natural-group     # → Z_60 = Z_4 × Z_3 × Z_5

# Spectral-native syzygy window search (v0.3.1+)
# Replaces the v0.3.0 point-evaluation `eclipse --jd` for window queries.
# ~1000× faster than encode-then-check; uses the closed-form Saros /
# Metonic / synodic / draconic-month enumeration.
ephemerides-spectral find-syzygies --from-jd 2460311 --to-jd 2460676

# Diagnosed-fiber runtime kernel patching (v0.4.0+)
# Patches sit beside the published kernel as DATA, not code edits, and
# contribute per-body residue deltas at encode time. The kernel's
# published bytes never change. Bundled catalog (11 patches as of v0.5.5):
#   v0.4.0 originals (3): mars-7.96yr-diagonal, mercury-10.69yr-diagonal,
#                         jupiter-saturn-9.56yr-coupled
#   v0.5.2 LS-fit recovered (3, planets ≥96% shrinkage): same names with -v2 suffix
#   v0.5.5 LS-fit moons (5, ≥93% shrinkage): dione/tethys/enceladus/titan/iapetus -v2
ephemerides-spectral patches catalog
ephemerides-spectral patches apply --name jupiter-saturn-9.56yr-coupled-v2
ephemerides-spectral patches active
ephemerides-spectral patches clear
```

All sub-commands emit JSON to stdout; pass `--no-pretty` (top-level flag, before the sub-command) for compact single-line output suitable for piping into `jq` or downstream tooling. Every response carries an `ok` field; `ok: false` returns exit code 1 with an `error` message.

## Python API

```python
from ephemerides_spectral import default_encode, bridge

# One-liner: encode a JD as a system state under the default backend.
state = default_encode(jd=2451545.0)            # uint32[38] residues (BIP)
state = default_encode(jd=2451545.0, backend="complex128")  # complex128[D]

# JSON-friendly bridge surface (Pyodide / web frontend)
bridge.get_version()                             # version + manifest
bridge.list_bodies()                             # 38-body roster (v0.5.0+)
bridge.get_resolution(body="mars", D=65536)      # sec/residue
bridge.get_system_state(jd_tdb=2451545.0)        # encode + per-body residues
bridge.get_local_view(jd_tdb=2451545.0, body="terra", lat=51.5, lon=-0.1)
bridge.get_eclipse_probability(jd_tdb=2451545.0)
bridge.list_couplings()                          # Laplacian fibers
bridge.get_breathing_modulation(jd_tdb=2451545.0)  # Phase 9 LUT inspector

# v0.3.0 surface
bridge.jd_to_mars_time(jd_utc=2451549.5)         # MSD + MTC (Allison & McEwen 2000)
bridge.mars_time_to_jd(msd=50000)                # MSD → JD_UTC inverse
bridge.get_lunar_phase(jd_tdb=2451545.0)         # mean synodic + sidereal phase
bridge.list_lunar_kernels()                      # LTE440 metadata + LTC status
bridge.get_natural_resonance_group()             # Z_60 = Z_4 × Z_3 × Z_5 (v0.5.0+)

# v0.4.0 surface — runtime kernel patching (overlay on the spectral kernel)
# Catalog grows over time; v0.6.1 ships 11 entries:
#   v0.4.0 originals (3): mars/mercury/jupiter-saturn at FFT-magnitude amplitudes
#   v0.5.2 LS-fit recovered (3, planets at ≥96% shrinkage): -v2 suffix
#   v0.5.5 LS-fit moons (5, ≥93% shrinkage): dione/tethys/enceladus/titan/iapetus -v2
bridge.list_catalog_patches()                    # bundled CATALOG (11 patches)
bridge.apply_patch("jupiter-saturn-9.56yr-coupled-v2")  # vindicated v0.5.2 entry
bridge.apply_custom_patch(name="my-patch", kind="sinusoid",
                          body="terra", amplitude_deg=0.93,
                          period_days=1940.2)    # FFT-diagnosed custom patch
bridge.list_active_patches()                     # what's currently overlaid
bridge.clear_patches()                           # wipe back to byte-exact baseline

# v0.5.4 surface — Sol Uranian Time
bridge.jd_to_sol_uranian_time(jd_tdb=2454451.0)  # USD + SUT + season + retrograde
bridge.sol_uranian_time_to_jd(usd=4046.0)        # USD → JD_TDB inverse

# v0.6.0 Tier 1 parity surface — both methods accept backend={"auto","bip","c"}
bridge.find_syzygies(jd_lo=2451545.0, jd_hi=2451545.0+365.25, backend="c")
bridge.get_breathing_modulation(jd_tdb=2451545.0, pair=("jupiter","saturn"),
                                n_lobes=(5, 2), backend="c")
```

Every bridge method returns a Pyodide-JSON-serialisable dict with `ok: True/False`. Caller-side errors return `{ok: False, error: "..."}` rather than raising — designed for crossing the Python/JS boundary cleanly.

## Performance & Footprint

`ephemerides-spectral` is designed for high-performance galactic mapping on edge devices where large SPICE kernels (the 3.3 GB DE441) are prohibitive.

### Memory Footprint

| Component               | Format       | RAM / Flash | Description                                  |
| :---------------------- | :----------- | :---------- | :------------------------------------------- |
| **State (BIP)**         | `uint32[D]`  | **256 KB**  | At `D=65536`; pure cyclic-group residues.    |
| **State (complex128)**  | `complex128` | **1.0 MB**  | At `D=65536`; FPU reference encoder.         |
| **Channel Bases**       | mixed        | **~38 MB**  | Full 38-body roster (v0.5.0+); pageable from Flash. |
| **Laplacian (`L`)**     | `complex128` | **< 25 KB** | 38 × 38 interaction matrix.                  |
| **Cosine LUT (Phase 9)** | `int32[1024]` | **4 KB**    | Off-diagonal adaptive ("breathing") modulation. |
| **DE441 Truth**         | BSP          | **3,300 MB** | Original JPL source (calibration only).     |

**Compression vs DE441:** > 100:1. Once calibrated, the HDC instrument functions as standalone algebraic truth — no kernel needed for propagation, local-view extraction, or syzygy detection.

### Microcontroller Compatibility

The BIP backend is the natural production target for embedded use:

- **ESP32-S3 / ESP32-C6** (8 MB+ PSRAM): full 38-body BIP state in PSRAM, microsecond-latency phase updates via `uint32` adds.
- **ARM Cortex-M7** (Teensy 4.1, etc.): integer multiply-accumulate suits the `omega * delta_t` step path natively; cosine LUT fits in tightly-coupled memory.
- **RISC-V / Edge AI accelerators:** `(φ_1 + φ_2) mod 2^32` is a single uint32 add — directly mappable to vector-extension lanes.

Instead of searching 3.3 GB of Chebyshev coefficients, these devices evolve the entire Sol Star System phase-space using integer additions and a 4 KB cosine table.

## Honest accuracy: DE441 full-epoch sweep (v0.3.0)

`research/de441_sweep.py` runs the BIP integer-ALU encoder at 15 sample points spanning **J2000 ± 14,000 yr** (just inside DE441's ~30,000-yr coverage window) and compares per-body ecliptic-longitude residues against DE441 ground truth. Results — sorted by max error, descending:

| Body | n | median (rad) | p95 (rad) | max (rad) | max (deg) |
| :--- | --: | --: | --: | --: | --: |
| jupiter | 15 | 1.357 | 2.937 | 3.070 | 175.92 |
| saturn  | 15 | 1.415 | 2.990 | 3.062 | 175.46 |
| neptune | 15 | 0.691 | 2.748 | 2.778 | 159.18 |
| pluto   | 15 | 0.791 | 2.524 | 2.721 | 155.92 |
| moon    | 15 | 1.084 | 2.559 | 2.670 | 153.00 |
| mercury | 15 | 0.356 | 1.444 | 1.461 |  83.74 |
| mars    | 15 | 0.117 | 0.250 | 0.253 |  14.52 |
| uranus  | 15 | 0.047 | 0.120 | 0.141 |   8.06 |
| venus   | 15 | 0.024 | 0.114 | 0.124 |   7.11 |
| earth   | 15 | 0.011 | 0.104 | 0.115 |   6.59 |

Earth phase error scales roughly linearly with horizon:

| Δt (yr) | Earth err (deg) |
| --: | --: |
| 0     | 0.000  |
| ±1    | 0.001–0.004 |
| ±10   | 0.006–0.008 |
| ±100  | 0.065–0.069 |
| ±1000 | 0.65–0.68   |
| ±5000 | 2.93–3.31   |
| ±10000 | 4.70–5.71  |
| ±14000 | 5.48–6.59  |

### Three regimes, honestly named

- **Sub-10° at multi-millennium horizons (Earth, Venus, Uranus):** bodies whose mean motion + small eccentricity + the static gravitational fiber couplings approximate the actual orbit well. Earth benefits from being the calibration body for Mercury's PN diagonal.
- **Tens of degrees (Mars 14.5°, Mercury 83.7°):** dynamics include eccentricity + long-period perturbations the Phase-9 model captures only partially. Mars has no resonance entry; Mercury's PN diagonal is *linear* whereas its actual perihelion precession at multi-millennium scales has higher-order terms.
- **Phase-scrambled (Jupiter, Saturn, Neptune, Pluto, Moon all hit >150°):** bodies whose secular drift is dominated by resonant perturbations the Phase-9 model approximates phenomenologically. The `α = 0.1` modulation depth is the right *order of magnitude* but wrong-in-detail; over ±14,000 yr that wrong-detail accumulates to a ~3 rad phase deficit.

This measures **how much of multi-millennium ephemeris our v0.3.0 model captures**, not how accurate the BIP encoder is at its design horizon. v0.3.0 is calibrated for the ±20-yr horizon (0.0002 rad ≈ 0.012° Earth phase floor); the multi-millennium errors are the cost of running a model trained for short-horizon dynamics far past its design point. **The v0.4+ first-principles per-resonance α derivation is the planned fix** — see ROADMAP.

## Encoding timings (BIP integer-ALU path, default `D = 65536`)

| Δt (yr) | encode wall time |
| --: | --: |
| 0      | 0.2 ms |
| ±1     | 0.7–1.3 ms |
| ±10    | 4.2–6.8 ms |
| ±100   | 44.7–45.8 ms |
| ±1000  | 447–483 ms |
| ±5000  | 2.38–2.44 s |
| ±10000 | 4.34–4.44 s |
| ±14000 | 6.18–6.37 s |

Linear in `|Δt|` — one 30-day chunk per integration step. At the v0.1.0 design horizon (±20 yr, ~243 chunks) the encode is ~1.85 ms; at ±14,000 yr (~170k chunks) it's ~6.4 s. Median across the sweep: **447 ms**; max: **6.4 s**.

**v0.4.1+ C native path** drops these by ~1000× (encode at +20 yr: 46 ms BIP → 0.04 ms C). The full DE441 FFT-residual sweep (1024 samples) takes ~14 seconds on the C native path versus ~5 minutes on Python BIP — the truth-lookup against skyfield is the new bottleneck.

## Patch-shrinks-residual benchmark — VINDICATED on planets (v0.5.2)

> *Earn the right to predict the missing data.* — measured.

The v0.4.0 catalog patches **claimed** to predict missing physics; v0.5.1 audited them and surfaced two authoring bugs (amplitude off by 2×, phase=0 assumption wrong); v0.5.2 fixed both with **least-squares fitting at the exact target period**. Result: **VINDICATED** on every targeted planet body.

| Patch | v0.4.0 (mag-only) | v0.5.1 (phase-recovered) | **v0.5.2 (LS-fit)** |
|---|---|---|---|
| Mars 7.96 yr | +2.5% | +2.7% | **+99.2%** |
| Mercury 10.69 yr | **−49.9% (peak GREW)** | +39.6% | **+99.9%** |
| Jupiter 9.56 yr | +30.9% | +77.1% | **+97.6%** |
| Saturn 9.56 yr | −0.4% | +76.4% | **+96.0%** |

The vindicated patches ship as **`CATALOG_V2`** alongside the original v0.4.0 `CATALOG`. Use the `-v2` suffix:

```python
bridge.apply_patch("mars-7.96yr-diagonal-v2")              # 99.2% shrinkage
bridge.apply_patch("mercury-10.69yr-diagonal-v2")          # 99.9%
bridge.apply_patch("jupiter-saturn-9.56yr-coupled-v2")     # 97.6% J / 96.0% S
```

Empirical findings worth noting:
- **J–S `correlation = +1` (in-phase)**, not −1 as v0.4.0 assumed. Anti-correlated-libration intuition was empirically wrong.
- **LS-fit amplitudes are 25–55% larger** than FFT-bin extraction — the energy that was leaking into adjacent bins.
- **Mars's true residual amplitude is 10.69° (LS) vs 3.45° (FFT-bin rank-1)** — a 3× underestimate, the worst leakage case in the catalog.

See [the v0.5.2 patch-shrinks-residual analysis](https://mlehaptics.readthedocs.io/en/latest/antikythera-maths/figures/patch_shrinks_residual_v0.5.2/) on the project docs for the full math derivation, methodology, and moon-residual open question.

## Status

See the [project CHANGELOG](https://mlehaptics.readthedocs.io/en/latest/antikythera-maths/ephemerides-spectral/CHANGELOG/) and [package CHANGELOG](https://mlehaptics.readthedocs.io/en/latest/antikythera-maths/ephemerides-spectral/python/CHANGELOG/) for the authoritative version-by-version detail. Headline summary:

* **v0.13.4** *(current)* — **JPL Power-of-Ten Rule 1 + Rule 3 fixes — first code-quality patch in the v0.13.4-v0.13.8 rule-fix sequence.** Caller-supplied-scratch refactor of `c/src/es_hd_state.c` eliminates both classes of violation in a single pass: `goto` count drops 5 → **0** (Rule 1 cleared) and `malloc`/`free` count drops 29 → **0** (Rule 3 cleared). The C library no longer calls dynamic allocators after init; `<stdlib.h>` is no longer included. The HD pipeline's three entry points (`es_encode_state_hd`, `es_bind_observer`, `es_get_eclipse_probability`) gain caller-supplied scratch-buffer parameters; the Python ctypes shim allocates them alongside the existing `out_state` buffer (no observable heap-pressure change — Python was already heap-allocating the output). **ABI v5 → v6** (mechanical wire-format change; encoder math byte-identical to v0.13.3 — parity smoke pins both backends to within float-ULP). **Total mechanically-detectable violations: 102 → 68** (33% of audit baseline cleared in one ship). Remaining: Rule 4 long functions (v0.13.5), Rule 5 assertion density (v0.13.6), Rule 10 pedantic-build matrix (v0.13.7), Rules 6+7 manual audits (v0.13.8). User-facing Python bridge surface unchanged. 250 tests pass, 5 skipped.
* **v0.13.3** — **Pre-merge docs+parity hygiene check (soft-warning GitHub Actions workflow).** Closes task `` `#98` `` (consolidated; absorbs `` `#87` `` + `` `#88` ``). New `.github/workflows/ephemerides-spectral-docs-check.yml` runs on every PR touching the package; classifies code-side changes (version bumps, `bridge.py`, `cli.py`, `_research/*.py`, `c/src/*.c` / `c/include/*.h`) against the five PyPI-facing docs files (`python/README.md`, `python/CHANGELOG.md`, `CHANGELOG.md`, `ROADMAP.md`, `ephemerides_spectral_research_notebook.md`); posts (or updates in place) a single PR comment summarising the gap. **Soft-warning, never fails the build** — the existing pytest freshness ratchet (`test_native_version_string_matches`, `test_parity_smoke::PARITY_TARGETS`, `test_readme_freshness`, `test_jpl_audit`) hard-fails on the highest-value drift modes; this workflow surfaces the *next tier* — prose-and-narrative drift that humans should review but a regex can't authoritatively adjudicate. **Opt-out**: `[skip-docs-check]` in the PR body silences on cosmetic / typo / formatting-only diffs. **Comment idempotence**: `peter-evans/find-comment` + `peter-evans/create-or-update-comment` update one advisory in place rather than spamming the PR. **Concurrency**: `cancel-in-progress: true` keyed by workflow + ref absorbs the `opened`+`labeled` double-fire pattern documented in `ephemerides-spectral-ci.yml`. CI-only addition; 250 tests pass, 5 skipped.
* **v0.13.2** — **Add `_native/` to repo `.gitignore`; renumber JPL rule-fix roadmap to v0.13.4-v0.13.8.** Quick-win patch addressing task `` `#85` `` (`_native/` directory holds compiled DLL/SO files that rebuild on every `cmake --build`; never belongs in source control). One line added to `.gitignore`. Also patches `c/JPL_AUDIT.md`'s roadmap section: the original v0.11.3-v0.11.7 numbering is obsolete since the project moved past v0.11.x; the rule-fix patches are renumbered to **v0.13.4 (Rule 1+3)**, **v0.13.5 (Rule 4)**, **v0.13.6 (Rule 5)**, **v0.13.7 (Rule 10)**, **v0.13.8 (Rules 6+7)**. v0.13.3 reserved for `` `#98` `` (consolidated docs+parity hygiene check; absorbs `` `#87` `` + `` `#88` ``). 248 tests pass, 5 skipped.
* **v0.13.1** — **SPICE feature-gap audit + STLT-naming hygiene.** Docs-only release; no API / encoder / ABI changes. New `figures/spice_feature_audit.md` answers *"what does SPICE do that we don't, and is a compat bridge worth shipping?"* — three-column comparison + recommendation (skip the compat-bridge; document the gap). Spawns a v0.14.x backlog: light-time + stellar-aberration corrections, frame transformations, full Kepler elements, per-body pole orientation. **STLT naming hygiene:** the abbreviation table promotes Luna's primary Sol Time from SLT (surface clock) to STLT (anchored Lunar synodic count) per the moons-stuck-to-parent `Sol <Parent>-<Body> Time` convention; SLT is preserved as a secondary alternative for the surface-clock case. Drops "system clock for the Terra-Luna pair" framing throughout active code (CHANGELOG history entries preserved as artefacts of how v0.10.0 was framed at the time). Tests unchanged at 248 + 5 skipped.
* **v0.13.0** — **Sol Dynamics — system energy budget, per-body energies, pair-wise gravitational forces. Augmented onto every `time-*` subcommand via `--dynamics`.** Counterpart to v0.12.0's Kinematics; mirrors chess-spectral's `qm_*_dynamics.py` *dynamics* layer (Hamiltonian + evolution + force/energy queries). New `bridge.get_dynamics()` (system aggregate), `bridge.get_force_between(a, b)` (Newtonian pair force, validated against the textbook **3.54×10²² N Earth-Sun figure to 0.01 %**), `bridge.get_body_energies(body)` (per-body KE + PE + total), and `bridge.apply_dynamics_correction()` (CLI post-processor). New standalone `dynamics` CLI subcommand with three modes: system aggregate (default), per-body (`--body X`), pair-force (`--body X --from Y`). **Total system energy −1.98×10³⁵ J (gravitationally bound; virial theorem holds to 0.5 %)**. All three augmenting flags `--proper` + `--state` + `--dynamics` compose without conflict. 248 tests pass (was 212 + 34 new dynamics tests + 2 freshness drift catches).
* **v0.12.0** — **Sol Kinematics — per-body orbital state, transparently augmented onto every `time-*` subcommand via `--state`.** Mirrors chess-spectral's `qm_*.py` *kinematics* layer (static observables, no time-evolution; the dynamics counterpart ships as v0.13.0). New `bridge.get_kinematic_state(body, ...)` + `bridge.get_full_system_state(...)` primitives + standalone `kinematics --body X` / `kinematics --all` CLI subcommand. **Validated against NASA fact-sheet orbital velocities**: Mercury 47.87 vs. 47.36 (1.1 %), Earth 29.785 vs. 29.78 (0.02 %), Mars 24.13 vs. 24.07 (0.25 %), Jupiter 13.06 vs. 13.07 (0.08 %), Pluto 4.741 vs. 4.74 (0.02 %). System totals reproduce the famous **"Jupiter holds 61 % of total angular momentum"** and **"outer planets hold 99.84 % of planetary L"** facts to within 0.02-2.5 %. Phase A research script + markdown report (`figures/kinematics_dynamics_audit.md`) committed first; Phase B canonical primitive ships with two independent implementations agreeing on the 9 published values. New `_research/kinematics.py` codegened into the package alongside `proper_time.py`. 212 tests pass (was 182 + 30 new kinematics tests).
* **v0.11.2** — **JPL Power-of-Ten audit baseline for the C library (audit-only; no code changes yet).** Documents 102 mechanically-detectable violations rule-by-rule in `c/JPL_AUDIT.md`: 5 `goto` (Rule 1), 29 `malloc`/`free` (Rule 3), 4 functions over 60 lines (Rule 4), 64-assertion shortfall (Rule 5). Pins the counts in `tests/test_jpl_audit.py` as a one-way ratchet — counts can only go DOWN; PRs that increase them fail loudly. Same modular discipline as `test_native_version_string_matches_package_version`, `test_parity_smoke.py::PARITY_TARGETS`, and `test_readme_freshness.py`. Rules 2 (fixed loop bounds), 8 (limited preprocessor), 9 (no function pointers) already pass clean. Rule-by-rule fixes ship in v0.11.3+ as separate code-quality minors. Reference: Holzmann 2006, *IEEE Computer*. 182 tests pass.
* **v0.11.1** — **Research notebook hygiene: backfill §7.4 (STLT) and §7.5 (SPrT) sections + refresh Status banner.** v0.10.0 STLT and v0.11.0 SPrT shipped without their notebook subsections; this is the doc-only catch-up. Triggered by user noticing the gap. Task #98 captures the broader follow-on (a soft "docs probably need updating" warning on PRs that touch code without touching docs — would have caught this gap automatically). 171 active tests pass; identical to v0.11.0.
* **v0.11.0** — **Sol Proper Time (SPrT) — `--proper` flag on every `time-*` subcommand applies gravitational + orbital-kinematic time dilation transparently.** New `bridge.get_proper_time_rate(body, ...)` and `bridge.compare_proper_times(a, b, ...)` primitives; new `time-proper` standalone subcommand for the rate-only query. Same physics as Mercury's existing 43″/century PN diagonal correction, applied per-body to all 38 bodies in the roster — the user's framing was *"gravitational time dilation fiber so users don't even need to know anything extra had to happen in the back end."* Six published values (Earth GR, Sun GR, Mars GR, Pluto GR, Earth orbital kinematic, Mars-vs-Earth GR difference) reproduced to within 0.30%; the 0.0175 s/Earth-year Curiosity-rover Mars-Terra clock-rate figure verified inline. New `surface_radius_km` per body in `bodies.py`. 32+ new tests in `test_sprt.py` pin every component + the CLI surfaces. Phase A research: `research/proper_time_rates.py` + `figures/proper_time_rates.md`.
* **v0.10.0** — **Sol Terra-Luna Time (STLT) — anchored Lunar time using the synodic month, with Meton's 432 BCE summer solstice as the default epoch.** First Sol Time member with a non-J2000 default anchor; primary lunar-time entry per the moons-stuck-to-parent `Sol <Parent>-<Body> Time` naming convention. New `bridge.jd_to_sol_terra_luna_time(jd_tdb, *, epoch="meton")` + `sol_terra_luna_time_to_jd(...)`; new CLI `time-terra-luna` with `--epoch {meton, antikythera, hipparchus, mardokempad, j2000}`. Synodic month is the natural unit; Saros (18.03 yr) and Metonic (19.00 yr) cycle counts come along for free. Anchor choice is empirically validated: the Hipparchus-Babylonian eclipse-archive midpoint (Mardokempad 721 BCE + Hipparchus 141 BCE) lands within +240 days of Meton's solstice — *same year*, eight months later — confirming Meton sits at the center of mass of Greek astronomical tradition (the "combo" candidate test from `research/lunar_epoch_candidates.py`). Also fixes the `find_syzygies(backend="auto")` latent bug class (same as v0.9.2's `get_breathing_modulation` fix). House-epoch design choice; not a claim to be NASA's eventual LCT.
* **v0.9.3** — **PyPI-facing README staleness sweep + CI freshness check.** Status section refreshed (8 versions of accumulated drift); Roadmap section pruned of items that have already shipped (Tier 2b, Sol Venusian/Mercurian Time, ITN pathway / `find-tubes`); leftover earth-body CLI examples corrected to `terra`; "Phase 9 'Breathing' Couplings" heading inverted to "Phase 9 Adaptive Couplings (a.k.a. 'breathing')" matching the v0.9.2 CLI rename. New `tests/test_readme_freshness.py` enforces three drift-prevention invariants: every CHANGELOG version must appear in this Status section; the banner under the H1 must equal `__version__`; every CLI body-name flag in an example must reference a name in `SUPPORTED_BODIES`. Same discipline as `test_native_version_string_matches_package_version` and `test_parity_smoke.py::PARITY_TARGETS` — enumerate the truth, fail on drift.
* **v0.9.2** — **CLI: `adaptive` is the primary subcommand for state-dependent coupling modulation; `breathing` retained as a hidden synonym (`help=argparse.SUPPRESS`).** Matches the adaptive-networks vocabulary (Gross & Blasius 2008; adaptive Kuramoto family). Both names work; new users discover `adaptive` via `--help`, visual-metaphor users keep typing `breathing`. Latent bug fixed in passing: `bridge.get_breathing_modulation(backend="auto")` was rejected by `_validate_backend` (sentinel not in `SUPPORTED_BACKENDS`); resolved before validation now, matching the docstring contract. The `breathing` CLI subcommand has been broken since v0.8.0 — now fixed.
* **v0.9.1** — **Sol Time naming convention overhaul + Sol Terra Time + Sol Luna Time.** Direct Latin proper noun (Mercury, Venus, Pluto, Terra, Luna, Sol) for rocky bodies + Sun + Luna; established adjective form (Jovian, Saturnian, Uranian, Neptunian) for gas/ice giants. Renames (BREAKING): `jd_to_sol_mercurian_time` → `jd_to_sol_mercury_time`; same for venusian → venus, plutonian → pluto. New (additive): Sol Terra Time (STT, Terra's surface clock) + Sol Luna Time (SLT, Luna's tidally-locked surface clock; distinct from Sol Lunar Time which gives Luna's phase observed from Terra).
* **v0.9.0** — **Body identity rename: `moon` → `luna`, `earth` → `terra`. BREAKING.** Latin proper nouns for body identity strings; generic English `moon` (= any natural satellite) and `earth` (= soil/ground) return to their generic meanings. `BODIES["luna"]` / `BODIES["terra"]` replace the old keys. `_data/initial_phases.json` re-keyed (encoded phase residues unchanged at any JD). C-side `es_bodies` table re-emitted via codegen. JPL/skyfield kernel boundary handled via `EphemerisBundle.lookup()` translation map. Encoder hot path byte-identical to v0.8.1.
* **v0.8.1** — **ITN pathway / Lagrange-tube query — `find-tubes` first cut.** "Surfing the perturbations": closed-form Hohmann transfer-window enumeration mirroring v0.3.1's `find-syzygies` discipline. Earth → Mars sanity: 23 windows over J2000 + 50 yr at threshold 0.02; 258.87-d transfer time and 5.594 km/s Δv match textbook Hohmann to 0.01% / 0.1%.
* **v0.8.0** — **Sol Symphony Times: 7 new planetary/stellar time systems.** Venus, Mercury, Pluto, Sol (the Sun!), Jupiter, Saturn, Neptune join Mars / Lunar / Uranian. Special quirks honored: Mercury 3:2 spin-orbit resonance (solar day = 2 Mercury-years exactly); Venus retrograde with sidereal day longer than year; Sol differential rotation (Carrington Rotation Number); Saturn Cassini-revised rotation (Mankovich 2019).
* **v0.7.0** — **C/Python parity Tier 2b — full HD pipeline in C (ABI v5).** Three new C entry points: `es_encode_state_hd`, `es_bind_observer`, `es_get_eclipse_probability`. Bridge dispatches `get_local_view` and `get_eclipse_probability` on `backend={"auto","bip","c","fpu-ref"}`. Every encoder-touching bridge method now has a paired C path; the v0.6.0 parity discipline is fully realised.
* **v0.6.1** — **Tier 2a foundation: portable channel-basis PRNG (ABI v4).** Splitmix64 PRNG bit-identical between Python + C; `es_channel_basis(seed, out, D)` produces byte-identical complex64 hypervectors on both sides. Foundation for v0.7.0's HD encode pipeline.
* **v0.6.0** — **C/Python parity Tier 1 + always-on parity smoke test (ABI v3).** `find_syzygies` and `get_breathing_modulation` now have C twins; bridge dispatches on `backend={"auto","bip","c"}`. New `tests/test_parity_smoke.py` enumerates every encoder-touching `bridge.*` method in a `PARITY_TARGETS` table — adding a new bridge method without a parity classification fails CI.
* **v0.5.5** — **Moon catalog patches (Phase C).** Five LS-fit-vindicated moon entries join `CATALOG_V2`: dione (98.2%), tethys (93.8%), enceladus (98.9%), titan (95.5%), iapetus (98.6%). Methodology vindicated **twice** on independent body sets: planets at 96-99%, moons at 93-99%.
* **v0.5.4** — **Sol Uranian Time (SUT)** — third planetary time system alongside Mars / Lunar. CLI `--help` audit across all subcommands.
* **v0.5.3** — **Moon residuals: 13 of 17 fixed.** Period-truncation root cause confirmed via per-orbital-period diagnostic. Fix: 9+-decimal sidereal periods from JPL HORIZONS / NASA fact sheets. Galileans drop from 100°→<1° RMS.
* **v0.5.2** — Patch-shrinks-residual benchmark **VINDICATED** on planets via LS-fit catalog (Mars 99.2%, Mercury 99.9%, J–S 97.6/96.0%). `CATALOG_V2` ships alongside v0.4.0. Moon-kernel infrastructure added.
* **v0.5.1** — Patch-shrinks-residual benchmark: PARTIAL vindication (J–S 77%, Mercury 40%, Mars stuck on FFT leakage); two v0.4.0 authoring bugs surfaced.
* **v0.5.0** — All major Jovian + Saturnian moons join the encoder (26 → 38 bodies). Three new resonances (Cassini Division, Enceladus tidal heating, Hyperion chaos). SPICE-free runtime via codegen-baked initial phases.
* **v0.4.1** — C-side runtime kernel patching (ABI v2). 237× speedup on patched encodes vs BIP.
* **v0.4.0** — Diagnosed-fiber runtime overlay (Python side). Patches as data, ksplice/kpatch-style.
* **v0.3.1** — C-in-wheel + spectral syzygy window search + DE441 error-spectrum FFT.
* **v0.3.0** — Mars Sol Date / Mars Coordinated Time, mean lunar primitives, LTE440 awareness, DE441 full-epoch sweep, natural-resonance gear group.
* **v0.2.0** — Phase 9 coverage extension to four resonance pairs (J–S 5:2, N–P 3:2, Io–Europa 2:1, Europa–Ganymede 2:1).
* **v0.1.0** — first PyPI release. 26-body Sol Star System Laplacian + Phase 9 adaptive ("breathing") couplings + ALU-native BIP encoder.

## Roadmap

Items genuinely still ahead (everything previously listed under "in progress" v0.7.0, "Sol Venusian/Mercurian Time," and "ITN pathway / Lagrange-tube query" has shipped — see [Status](#status) above for landing versions):

* **First-principles per-resonance α** — replaces phenomenological `α = 0.1` with values derived from a Hamilton/Delaunay-variable Lagrangian (Lie-series perturbation theory around each resonance). The DE441 sweep is the empirical motivation: bodies inside the resonance set phase-scramble at multi-millennium horizons because their `α` values are wrong-in-detail. The v0.5.5 LS-fit catalog patches are the *empirical* analog — Fourier-correction overlays that first-principles `α` should ultimately make redundant for bodies inside the resonance set.
* **Hyperion follow-up** — multi-component patch or coupled `titan-hyperion-4to3-coupled-v2`. The single-sinusoid Hyperion patch hits 75% (chaos ceiling); a coupled / multi-component patch should clear the 80% gate.
* **Remaining 4 broken moons** (metis / thebe / rhea / phoebe). Phoebe needs sign-aware retrograde encoder; Metis needs an authoritative period; Thebe + Rhea look perturbation-driven.
* **Sol Moon Times completion** — time reference for every moon in the roster, mirroring the planetary Sol Times. Naming convention already established for ports: `Sol <Parent>-<Body> Time` (e.g., Sol Pluto-Charon Time).
* **DE441 vs DE442 spectral error signature** *(experiment)* — build two BIP instruments, one calibrated only from DE441, one only from DE442; encode the same JD on both; project the per-body residue deltas onto the encoder's eigenbasis. If the deltas have a coherent spectral signature, DE442's corrections to DE441 live in a specific eigenmode subspace — which means we could *predict* where ephemeris error correction is structurally needed without needing the corrected kernel.
* **Heteroclinic-tube extension to `find-tubes`** — the v0.8.1 first-cut ships closed-form Hohmann math under a `transfer_kind` field that reserves room for low-energy / heteroclinic-tube candidates from the Interplanetary Transport Network proper (stable/unstable manifolds of Lyapunov / halo orbits around L1/L2/L3 of each Sun-planet CR3BP). References: Koon, Lo, Marsden, Ross 2011; Lo's Genesis / WMAP trajectory work; Conley's 1968 manifold-connection theorems.
* **LTC (Lunar Coordinated Time)** — pending NASA + international space-agency standardisation (target ~2026–2028 per April 2024 White House directive). LTE440 (Lin et al. 2025) ships the underlying SPICE-format conversion ephemeris with 0.15 ns accuracy through 2050; the bridge gains an `LTC` namespace mirroring `MarsTime` once the LTC epoch + day-length convention are formalised.
* **Phase 10 resonance coverage** — Jupiter–Uranus 7:1, Saturn–Uranus 3:1, Saros / Metonic / Terra–Luna precession entries. Each adds a row to the `RESONANCES` table; the integer-LUT machinery is shared.
* **Multi-millennium DE441 sweep** with the v0.5+ resonance-corrected encoder. Re-derive Metonic and Saros anchors against the full 3.3 GB DE441 with adaptive ("breathing") couplings active.
* **Doxygen for ephemerides-spectral C public API** — every entry point in `c/include/ephemerides_spectral.h` documented in the standard Doxygen style for downstream embedded / WASM consumers.
* **Bit-serial hardware port** (Verilog/SystemC) — the cosine LUT becomes block RAM, the `omega * step` becomes a fixed-precision multiplier.

## License

GPL-3.0-or-later.
