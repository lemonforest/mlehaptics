# ephemerides-spectral

> **High-precision HDC reference instrument for the Sol Star System.**

## Overview

`ephemerides-spectral` is an implementation of a resonant hyperdimensional computing (HDC) instrument that encodes the barycentric state of our star system using high-precision ephemeris data (NASA JPL DE441).

Built on first-principles algebraic dynamics, it treats celestial bodies not as spatial coordinates, but as resonant phases evolving via a **Solar System Graph Laplacian**. This enables high-performance galactic mapping and temporal cross-referencing on edge devices.

### Key Capabilities

- **Graph Laplacian Propagator:** System evolution driven by $e^{-i L t}$, where diagonal content represents mean motions and off-diagonal fibers model gravitational perturbations.
- **Sol Star System Roster:** Includes the Sun, all planets, major moons (Luna, Galilean moons, Titan, etc.), and the asteroid belt (Ceres, Vesta).
- **Terra Time Resolution:** At the default $D=65536$, provides a temporal granularity of ~8.02 minutes per residue shift.

### Resolution Scaling

The temporal resolution of a "residue shift" (pluck+rotate) is inversely proportional to the hypervector dimension $D$. You can adjust the "tick" size of the instrument by scaling $D$:

- **Minute Resolution ($D \approx 2^{19}$):** 1 residue shift $\approx 1$ Terra minute.
- **Second Resolution ($D \approx 2^{25}$):** 1 residue shift $\approx 1$ Terra second.

This allows the instrument to be tuned for either high-cadence local events or extremely high-performance long-term galactic mapping.
- **Observer-Agnostic Views:** Unitary binding to generate topocentric "Local View" hypervectors from any position in the system.
- **Spectral Syzygy Detection:** Instantaneous eclipse and conjunction probability via dot-product alignment with spectral operators.

## Installation

```bash
pip install ephemerides-spectral
```

For full high-resolution ephemeris support:
```bash
pip install "ephemerides-spectral[ephemeris]"
```

## CLI Usage

The package provides a rich command-line interface for phase-space analysis:

```bash
# Encode global system state at a Julian Date
ephemerides-spectral encode --jd 2451545.0 --force-high-res

# Query temporal resolution for a specific body
ephemerides-spectral resolution --body mars

# Extract a topocentric view from Earth
ephemerides-spectral local-view --jd 2451545.0 --body earth --lat 51.5 --lon -0.1
```

## Performance & Footprint

`ephemerides-spectral` is designed for high-performance galactic mapping on edge devices where large SPICE kernels (like the 3.3GB DE441) are prohibitive.

### Memory Footprint

| Component | Format | RAM/Flash | Description |
| :--- | :--- | :--- | :--- |
| **System State ($H$)** | complex128 | **1.0 MB** | Global barycentric phase state ($D=65536$). |
| **Channel Bases** | complex128 | **~26 MB** | Full roster (26 bodies). Can be paged from Flash. |
| **Laplacian ($L$)** | complex128 | **< 15 KB** | $26 \times 26$ interaction matrix. |
| **DE441 Truth** | BSP | **3,300 MB** | The original JPL source data. |

**Compression Ratio:** > 100:1. Once calibrated, the HDC instrument functions as a standalone "algebraic truth" that does not require the original 3.3GB kernel for propagation or local-view extraction.

### Microcontroller Compatibility

The instrument is highly optimized for modern 32-bit and 64-bit edge platforms:

-   **ESP32-S3 / ESP32-C6:** Platforms with **8MB+ PSRAM** can store the entire system roster in memory for microsecond-latency state updates.
-   **ARM Cortex-M7 (e.g., Teensy 4.1):** Ideal for the vector-matrix operations ($e^{-i L t}$) required for high-cadence temporal cross-referencing.
-   **RISC-V / Edge AI:** The algebraic nature of the HDC operations (complex multiply, circular rolls) maps naturally to vector extensions and neural accelerators.

Instead of searching 3.3GB of Chebyshev coefficients, these devices can evolve the entire Sol Star System phase-space using a single unitary propagator.

## License

GPL-3.0-or-later.
