# ephemerides-spectral

> **High-precision HDC reference instrument for the Sol Star System.**

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

- **Graph Laplacian Propagator:** Diagonal content = Newtonian mean motions + Mercury 43"/century post-Newtonian correction. Off-diagonal = gravitational fiber couplings (planet-sun, moon-planet, J–S 5:2 resonance, asteroid-Jupiter).
- **Phase 9 "Breathing" Couplings:** Off-diagonal weights modulate with the resonant phase difference `cos(n_a·φ_a − n_b·φ_b)`. Formally a **state-dependent (non-autonomous) graph Laplacian** / **adaptive Kuramoto-family network with phase-difference-dependent coupling** — see the [research notebook §1.4](https://github.com/lemonforest/mlehaptics/blob/main/docs/antikythera-maths/ephemerides_spectral_research_notebook.md#14-mathematical-positioning-of-the-breathing-laplacian) for the full positioning across spectral-graph-theory / dynamical-systems / DNLS-on-a-graph vocabularies. Implemented end-to-end without FPU using a 1024-entry `int32` cosine LUT (Q1.14 amplitude, 4 KB).
- **Sol Star System Roster:** 26 bodies — Sun, planets (incl. Pluto), 12 major moons, 4 main-belt asteroids.
- **Observer-Agnostic Views:** Unitary binding to generate topocentric "Local View" hypervectors at any (lat, lon) on any body.
- **Spectral Syzygy Detection (point-evaluation, v0.3.0):** Inner product with the Syzygy Operator (Sun + Moon + lunar Node) gives an eclipse / conjunction probability *at a given JD*. **Limitation:** this is the encode-then-check pattern — the wrong way to use the encoder for searching syzygies in a window. The HDC-native pattern uses the natural cyclic-group decomposition (Saros / Metonic / synodic month) to enumerate candidate JDs *without* per-JD encoding, then confirms via spectral projection. v0.4+ ROADMAP item: replace the point-evaluation surface with a window search.

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
ephemerides-spectral breathing --help
```

### Sub-command Cheat-Sheet

```bash
# Package version + frozen-data manifest
ephemerides-spectral version

# All 26 bodies in the Sol Star System Laplacian
ephemerides-spectral bodies

# Earth temporal resolution at the default D=65536
ephemerides-spectral resolution --body earth

# Encode J2000 with the integer ALU backend (default)
ephemerides-spectral encode --jd 2451545.0

# Same JD with the FPU complex128 reference encoder
ephemerides-spectral encode --jd 2451545.0 --backend complex128

# Topocentric view from London at J2000
ephemerides-spectral local-view --jd 2451545.0 --body earth --lat 51.5 --lon -0.1

# Syzygy alignment probability AT a JD (point evaluation; encode-then-check)
# v0.4+ ROADMAP: window search via the natural cyclic-group decomposition
ephemerides-spectral eclipse --jd 2451545.0

# Off-diagonal couplings (Laplacian fiber bundle)
ephemerides-spectral couplings

# Phase 9 breathing modulation (Jupiter-Saturn 5:2 by default)
ephemerides-spectral breathing --jd 2458850.0

# Override resonance: 3:2 Neptune-Pluto
ephemerides-spectral breathing --jd 2451545.0 \
    --pair-a neptune --pair-b pluto --n-a 3 --n-b 2

# Mars Sol Date / Mars Coordinated Time at a JD (v0.3.0)
ephemerides-spectral time-mars --jd 2451549.5     # → MSD ≈ 44795.99
ephemerides-spectral time-mars --msd 50000        # invert: MSD → JD_UTC

# Mean lunar synodic + sidereal age/phase at a JD (v0.3.0)
ephemerides-spectral time-lunar --jd 2451545.0

# Lunar-time kernel metadata (LTE440 + LTC status; v0.3.0)
ephemerides-spectral lunar-kernels

# Resonance-derived natural cyclic group (v0.3.0)
ephemerides-spectral natural-group     # → Z_30 = Z_2 × Z_3 × Z_5

# Spectral-native syzygy window search (v0.3.1+)
# Replaces the v0.3.0 point-evaluation `eclipse --jd` for window queries.
# ~1000× faster than encode-then-check; uses the closed-form Saros /
# Metonic / synodic / draconic-month enumeration.
ephemerides-spectral find-syzygies --from-jd 2460311 --to-jd 2460676

# Diagnosed-fiber runtime kernel patching (v0.4.0+)
# Patches sit beside the published kernel as DATA, not code edits, and
# contribute per-body residue deltas at encode time. The kernel's
# published bytes never change. Three patches in the bundled CATALOG
# authored from v0.3.1's de441_error_spectrum FFT (Mars 7.96 yr,
# Mercury 10.69 yr, Jupiter–Saturn 9.56 yr coupled).
ephemerides-spectral patches catalog
ephemerides-spectral patches apply --name jupiter-saturn-9.56yr-coupled
ephemerides-spectral patches active
ephemerides-spectral patches clear
```

All sub-commands emit JSON to stdout; pass `--no-pretty` (top-level flag, before the sub-command) for compact single-line output suitable for piping into `jq` or downstream tooling. Every response carries an `ok` field; `ok: false` returns exit code 1 with an `error` message.

## Python API

```python
from ephemerides_spectral import default_encode, bridge

# One-liner: encode a JD as a system state under the default backend.
state = default_encode(jd=2451545.0)            # uint32[26] residues (BIP)
state = default_encode(jd=2451545.0, backend="complex128")  # complex128[D]

# JSON-friendly bridge surface (Pyodide / web frontend)
bridge.get_version()                             # version + manifest
bridge.list_bodies()                             # 26-body roster
bridge.get_resolution(body="mars", D=65536)      # sec/residue
bridge.get_system_state(jd_tdb=2451545.0)        # encode + per-body residues
bridge.get_local_view(jd_tdb=2451545.0, body="earth", lat=51.5, lon=-0.1)
bridge.get_eclipse_probability(jd_tdb=2451545.0)
bridge.list_couplings()                          # Laplacian fibers
bridge.get_breathing_modulation(jd_tdb=2451545.0)  # Phase 9 LUT inspector

# v0.3.0 surface
bridge.jd_to_mars_time(jd_utc=2451549.5)         # MSD + MTC (Allison & McEwen 2000)
bridge.mars_time_to_jd(msd=50000)                # MSD → JD_UTC inverse
bridge.get_lunar_phase(jd_tdb=2451545.0)         # mean synodic + sidereal phase
bridge.list_lunar_kernels()                      # LTE440 metadata + LTC status
bridge.get_natural_resonance_group()             # Z_30 = Z_2 × Z_3 × Z_5

# v0.4.0 surface — runtime kernel patching (overlay on the spectral kernel)
bridge.list_catalog_patches()                    # bundled CATALOG (3 patches)
bridge.apply_patch("mars-7.96yr-diagonal")       # load from CATALOG
bridge.apply_custom_patch(name="my-patch", kind="sinusoid",
                          body="earth", amplitude_deg=0.93,
                          period_days=1940.2)    # FFT-diagnosed custom patch
bridge.list_active_patches()                     # what's currently overlaid
bridge.clear_patches()                           # wipe back to byte-exact baseline
```

Every bridge method returns a Pyodide-JSON-serialisable dict with `ok: True/False`. Caller-side errors return `{ok: False, error: "..."}` rather than raising — designed for crossing the Python/JS boundary cleanly.

## Performance & Footprint

`ephemerides-spectral` is designed for high-performance galactic mapping on edge devices where large SPICE kernels (the 3.3 GB DE441) are prohibitive.

### Memory Footprint

| Component               | Format       | RAM / Flash | Description                                  |
| :---------------------- | :----------- | :---------- | :------------------------------------------- |
| **State (BIP)**         | `uint32[D]`  | **256 KB**  | At `D=65536`; pure cyclic-group residues.    |
| **State (complex128)**  | `complex128` | **1.0 MB**  | At `D=65536`; FPU reference encoder.         |
| **Channel Bases**       | mixed        | **~26 MB**  | Full 26-body roster; pageable from Flash.    |
| **Laplacian (`L`)**     | `complex128` | **< 15 KB** | 26 × 26 interaction matrix.                  |
| **Cosine LUT (Phase 9)** | `int32[1024]` | **4 KB**    | Off-diagonal breathing modulation.           |
| **DE441 Truth**         | BSP          | **3,300 MB** | Original JPL source (calibration only).     |

**Compression vs DE441:** > 100:1. Once calibrated, the HDC instrument functions as standalone algebraic truth — no kernel needed for propagation, local-view extraction, or syzygy detection.

### Microcontroller Compatibility

The BIP backend is the natural production target for embedded use:

- **ESP32-S3 / ESP32-C6** (8 MB+ PSRAM): full 26-body BIP state in PSRAM, microsecond-latency phase updates via `uint32` adds.
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

## Status

* **v0.3.0** *(current)* — Mars Sol Date / Mars Coordinated Time, mean lunar primitives, LTE440 awareness, DE441 full-epoch sweep, natural-resonance gear group. See [`CHANGELOG.md`](https://github.com/lemonforest/mlehaptics/blob/main/docs/antikythera-maths/ephemerides-spectral/CHANGELOG.md) for the full v0.3.0 entry.
* **v0.2.0** — Phase 9 coverage extension to four resonance pairs (J–S 5:2, N–P 3:2, Io–Europa 2:1, Europa–Ganymede 2:1).
* **v0.1.0** — first PyPI release. 26-body Sol Star System Laplacian + Phase 9 breathing couplings + ALU-native BIP encoder.

## Roadmap

* **v0.4+ first-principles per-resonance α** — replaces phenomenological `α = 0.1` with values derived from a Hamilton/Delaunay-variable Lagrangian (Lie-series perturbation theory around each resonance). The DE441 sweep above is the empirical motivation: bodies inside the resonance set phase-scramble at multi-millennium horizons because their `α` values are wrong-in-detail.
* **v0.4+ DE441 vs DE442 spectral error signature** *(experiment)* — build two BIP instruments, one calibrated only from DE441, one only from DE442; encode the same JD on both; project the per-body residue deltas onto the encoder's eigenbasis. If the deltas have a coherent spectral signature, DE442's corrections to DE441 live in a specific eigenmode subspace — which means we could *predict* where ephemeris error correction is structurally needed without needing the corrected kernel.
* **v0.4+ spectral syzygy window search** — replaces the v0.3.0 point-evaluation `eclipse --jd` (encode-then-check) with a `find-syzygies --from-jd ... --to-jd ...` window search that uses the encoder's natural cyclic-group decomposition (Saros 6585.32 d, Metonic 19 yr, synodic month 29.53 d, lunar nodes 18.6 yr). The bronze antikythera's Saros dial doesn't encode-and-check either — it just turns gears whose ratios *are* the Saros cycle. The HDC-native pattern is to enumerate window-multiples of the slow modes in closed form from the Q-format `omega` values, then confirm each candidate by spectral projection. This reduces the cost from `O(window_days × encode_cost)` to `O(n_syzygies × confirmation_cost)`.
* **v0.5+ CORDIC topocentric rendering** — the cosine LUT is half a CORDIC kernel; the rotation half can subsume the topocentric `lat / lon` observer-bind, taking that path off the FPU entirely.
* **v0.5+ LTC (Lunar Coordinated Time)** — pending NASA + international space-agency standardisation (target ~2026–2028 per April 2024 White House directive). LTE440 (Lin et al. 2025) ships the underlying SPICE-format conversion ephemeris with 0.15 ns accuracy through 2050; the bridge gains an `LTC` namespace mirroring `MarsTime` once the LTC epoch + day-length convention are formalised.
* **Phase 10 resonance coverage** — Jupiter–Uranus 7:1, Saturn–Uranus 3:1, Saros / Metonic / Earth–Moon precession entries. Each adds a row to the `RESONANCES` table; the integer-LUT machinery is shared.
* **Bit-serial hardware port** (Verilog/SystemC) — the cosine LUT becomes block RAM, the `omega * step` becomes a fixed-precision multiplier.

## License

GPL-3.0-or-later.
