# ephemerides-spectral

> **High-precision HDC reference instrument for the Sol Star System.**

## Overview

`ephemerides-spectral` is a hyperdimensional-computing instrument that encodes the barycentric state of our star system using high-precision ephemeris data (NASA JPL DE441 / DE442) as resonant phases over a graph Laplacian.

Two interchangeable backends ship with the package:

* **`bip`** *(default)* — bit-serialised integer ALU. Phase composition lives in the cyclic group `Z_{2^32}`; binding is `(φ_1 + φ_2) mod 2^32`, which is implicit `uint32` overflow — no FPU in the hot path. 305× faster than the FPU reference; 256 KB state at `D=65536`.
* **`complex128`** — FPU reference encoder with unit-norm complex Gaussian bases. Used for the algebraic identities (Syzygy operator, observer binding) and as a regression baseline.

Both backends implement the same algebraic substrate (cyclic-group representation of celestial phase-space, graph-Laplacian eigenbasis); they trade precision for speed.

### Companion Project

`ephemerides-spectral` lives in the same `docs/antikythera-maths/` folder as **antikythera-spectral** because the two share the spectral / cyclic-group framing and the Pyodide bridge contract. They are *not* consolidated: antikythera-spectral encodes a specific bronze-age mechanism (940-tooth Callippic gear DAG) while ephemerides-spectral encodes the live JPL DE441 ephemeris with phase-dependent (breathing) gravitational couplings. The chess-spectral notebook §20.13–§20.17 calls out the cross-pollination — chess uses `Z_{640}` (paying an explicit `% 640` per op); ephemerides uses `Z_{2^32}` (free `uint32` overflow).

### Key Capabilities

- **Graph Laplacian Propagator:** Diagonal content = Newtonian mean motions + Mercury 43"/century post-Newtonian correction. Off-diagonal = gravitational fiber couplings (planet-sun, moon-planet, J–S 5:2 resonance, asteroid-Jupiter).
- **Phase 9 Breathing Couplings:** Off-diagonal weights modulate with the resonant phase difference `cos(n_a·φ_a − n_b·φ_b)`. Implemented end-to-end without FPU using a 1024-entry `int32` cosine LUT (Q1.14 amplitude, 4 KB).
- **Sol Star System Roster:** 26 bodies — Sun, planets (incl. Pluto), 12 major moons, 4 main-belt asteroids.
- **Observer-Agnostic Views:** Unitary binding to generate topocentric "Local View" hypervectors at any (lat, lon) on any body.
- **Spectral Syzygy Detection:** Inner product with the Syzygy Operator (Sun + Moon + lunar Node) gives an eclipse / conjunction probability.

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

# Syzygy alignment probability
ephemerides-spectral eclipse --jd 2451545.0

# Off-diagonal couplings (Laplacian fiber bundle)
ephemerides-spectral couplings

# Phase 9 breathing modulation (Jupiter-Saturn 5:2 by default)
ephemerides-spectral breathing --jd 2458850.0

# Override resonance: 3:2 Neptune-Pluto
ephemerides-spectral breathing --jd 2451545.0 \
    --pair-a neptune --pair-b pluto --n-a 3 --n-b 2
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

## Status

* **v0.1.0 (alpha):** Phase 5–9 research code mirrored into the wheel; CLI + bridge surface stable. RC published to TestPyPI; PyPI release pending broader DE441 kernel validation.
* **Roadmap:**
  - Extend Phase 9 breathing couplings beyond J–S 5:2 (Neptune–Pluto 3:2, Io–Europa 1:2, Earth–Moon precession, Trojans).
  - Bit-serial hardware port (Verilog/SystemC) — the cosine LUT becomes block RAM, the `omega * step` becomes a fixed-precision multiplier.
  - CORDIC topocentric rendering (the cosine LUT is half of a CORDIC kernel).

## License

GPL-3.0-or-later.
