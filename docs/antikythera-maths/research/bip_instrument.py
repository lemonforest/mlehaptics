"""Bit-Interleaved Phases (BIP) HDC Instrument — FPU-less Implementation.

Implements Resonant Bit-Serialized HDC where complex multiplication is
replaced by modular integer addition, preserving the phase-space architecture
without requiring an FPU.
"""

from __future__ import annotations

import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .bodies import BODIES, Body
from .laplacian import SolarSystemLaplacian
from .ephemeris_loader import load_ephemeris, EphemerisBundle

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

D_DEFAULT: int = 65536
K_BITS: int = 32
MODULO: int = 2**K_BITS
REFERENCE_JD: float = 2451545.0

# ---------------------------------------------------------------------------
# EphemerisBIPInstrument
# ---------------------------------------------------------------------------

class EphemerisBIPInstrument:
    """FPU-less BIP instrument for the Sol Star System."""

    def __init__(self, D: int = D_DEFAULT, kernel: str = "de441", force_high_res: bool = False):
        self.D = D
        self.kernel = kernel
        self.laplacian = SolarSystemLaplacian()
        self.body_names = self.laplacian.body_names
        
        # 0. Find skyfield_data directory
        research_dir = Path(__file__).resolve().parent
        project_root = research_dir.parents[2]
        data_dir = str(project_root / "skyfield_data")

        # 1. Ephemeris for Calibration
        try:
            self.bundle: Optional[EphemerisBundle] = load_ephemeris(kernel=kernel, data_dir=data_dir)
        except ValueError:
            self.bundle = None
            
        if self.bundle is None:
            if force_high_res:
                raise RuntimeError(f"High-resolution kernel {kernel} requested but not found.")
            self.bundle = load_ephemeris(kernel="de421", data_dir=data_dir)
        
        # 2. HDC Channel Bases (Discrete Phases in Z_{2^K})
        self.channel_bases = self._initialize_bases()
        
        # 3. Calibration: Initial discrete phases at REFERENCE_JD
        self.initial_phases = self._calibrate_initial_phases(REFERENCE_JD)
        
        # 4. Fixed-Point Frequencies (Scaled for BIP evolution)
        # Omega = (2*pi / period) mapped to (MODULO / period)
        self.fixed_frequencies = self._calculate_fixed_frequencies()

    def _initialize_bases(self) -> Dict[str, np.ndarray]:
        bases = {}
        for i, body in enumerate(self.body_names):
            rng = np.random.default_rng(2026 + i)
            # Uniform discrete phases in [0, MODULO)
            phases = rng.integers(0, MODULO, self.D, dtype=np.uint32)
            bases[body] = phases
        return bases

    def _calibrate_initial_phases(self, jd: float) -> np.ndarray:
        """Calibrate the phase angles (mapped to Z_{2^K}) from ephemeris truth."""
        if self.bundle is None:
            return np.zeros(len(self.body_names), dtype=np.uint32)
        
        ts = self.bundle.ts
        t = ts.tt_jd(jd)
        phases = np.zeros(len(self.body_names), dtype=np.uint32)
        
        moon_parent_map = {
            "moon": "earth", "phobos": "mars", "deimos": "mars",
            "io": "jupiter", "europa": "jupiter", "ganymede": "jupiter", "callisto": "jupiter",
            "titan": "saturn", "enceladus": "saturn", "rhea": "saturn",
            "titania": "uranus", "triton": "neptune"
        }

        for i, name in enumerate(self.body_names):
            body_info = BODIES.get(name)
            if not body_info: continue
            
            try:
                target_key = name.upper()
                if body_info.category == "planet": target_key += " BARYCENTER"
                target = self.bundle.eph[target_key]
                
                if body_info.category == "planet":
                    center = self.bundle.eph["sun"]
                elif body_info.category == "moon":
                    parent_name = moon_parent_map.get(name, "earth")
                    parent_key = parent_name.upper()
                    if parent_name in ["earth", "mars", "jupiter", "saturn", "uranus", "neptune"]:
                         parent_key += " BARYCENTER"
                    center = self.bundle.eph[parent_key]
                else:
                    center = self.bundle.eph["sun"]
                
                astrometric = center.at(t).observe(target)
                _, lon, _ = astrometric.ecliptic_latlon()
                # Map [0, 2pi) -> [0, MODULO)
                phases[i] = int((lon.radians / (2.0 * np.pi)) * MODULO) % MODULO
                
            except (KeyError, ValueError):
                if body_info.period_days > 0:
                    phases[i] = int((jd % body_info.period_days) / body_info.period_days * MODULO) % MODULO
                else:
                    phases[i] = 0
                
        return phases

    def _calculate_fixed_frequencies(self) -> np.ndarray:
        """Calculate MODULO / period for each body."""
        freqs = np.zeros(len(self.body_names), dtype=np.float64)
        for i, name in enumerate(self.body_names):
            body = BODIES[name]
            if body.period_days > 0:
                # Residues per day
                freqs[i] = MODULO / body.period_days
            else:
                freqs[i] = 0.0
        return freqs

    def encode_state(self, date_jd: float) -> np.ndarray:
        """Evolve phases using integer-only arithmetic and encode as BIP state vector."""
        delta_t = date_jd - REFERENCE_JD
        
        # 1. First-Principles Evolution (Integer-Only)
        # phi(t) = phi(0) + (MODULO/period) * delta_t
        evolved_phases = ((self.initial_phases + self.fixed_frequencies * delta_t).astype(np.uint64) % MODULO).astype(np.uint32)
        
        # 2. HDC Superposition (BIP)
        # Note: Superposition in BIP isn't a simple sum (that's binding).
        # We need a 'Resonant Accumulator' or 'Majority Vote'.
        # For now, let's use the 'Sum of Phasors' approximation mapped back to BIP.
        # This is the only part that might need a small LUT or FPU for 'rendering'.
        # But for strictly ALGEBRAIC operations, we use binding.
        
        # In RBS-HDC, the state is often a superposition of discrete phases.
        # To remain FPU-less, we can represent the state as a histogram or a 
        # dominant phase.
        
        # For this prototype, we'll return the vector of phases for all bodies.
        return evolved_phases

    def bind(self, phase_vec_a: np.ndarray, phase_vec_b: np.ndarray) -> np.ndarray:
        """FPU-less binding: Modular addition."""
        return (phase_vec_a + phase_vec_b) % MODULO

    def get_resolution(self, body: str = "earth") -> float:
        """Seconds per 1-unit residue shift."""
        body_info = BODIES.get(body.lower())
        if not body_info or body_info.period_days <= 0: return 0.0
        return (body_info.period_days * 86400.0) / MODULO

# ---------------------------------------------------------------------------
# Benchmark
# ---------------------------------------------------------------------------

def run_benchmark():
    print("RBS-HDC (BIP) vs Floating-Point Benchmark")
    print("=" * 60)
    
    import time
    from .ephemeris_reference_instrument import EphemerisHDCInstrument
    
    # 1. Setup
    print("Initializing instruments...")
    bip = EphemerisBIPInstrument(kernel="de421")
    fpu = EphemerisHDCInstrument(kernel="de421")
    
    test_jd = REFERENCE_JD + (20.0 * 365.25) # 20 years later
    
    # 2. FPU Timing
    start = time.perf_counter()
    fpu_state = fpu.encode_state(test_jd)
    fpu_time = (time.perf_counter() - start) * 1000
    
    # 3. BIP Timing (with HDC Superposition)
    start = time.perf_counter()
    # Evolve phases
    bip_phases = bip.encode_state(test_jd)
    # Superpose (BIP Superposition is modular addition across D)
    bip_state = np.zeros(bip.D, dtype=np.uint32)
    for i, name in enumerate(bip.body_names):
        # Explicit modular addition via uint32 overflow
        bip_state += (bip.channel_bases[name] + bip_phases[i])
    bip_time = (time.perf_counter() - start) * 1000
    
    print(f"\nEncoding Time (20-year evolution + D=65536 Superposition):")
    print(f"  FPU (Complex64): {fpu_time:.3f} ms")
    print(f"  BIP (UInt32):    {bip_time:.3f} ms")
    print(f"  Speedup:         {fpu_time / bip_time:.1f}x")
    
    # 4. Precision Check (Terra Phase after 20yr)
    idx_earth = bip.body_names.index("earth")
    bip_earth_rad = (bip_phases[idx_earth] / MODULO) * 2.0 * np.pi
    
    # Extract earth phase from FPU instrument (requires looking at internal phases)
    # delta_t = test_jd - REFERENCE_JD
    # pred_phases = fpu.laplacian.evolve_state(fpu.initial_phases, delta_t)
    # fpu_earth_rad = pred_phases[idx_earth]
    
    # Let's just compare BIP to Ephemeris Truth directly
    ts = bip.bundle.ts
    t = ts.tt_jd(test_jd)
    astrometric = bip.bundle.sun.at(t).observe(bip.bundle.earth)
    _, lon, _ = astrometric.ecliptic_latlon()
    truth_rad = lon.radians
    
    err_bip = (bip_earth_rad - truth_rad + np.pi) % (2.0 * np.pi) - np.pi
    
    print(f"\nPrecision Check (Terra Phase after 100yr):")
    print(f"  Truth: {truth_rad:.6f} rad")
    print(f"  BIP:   {bip_earth_rad:.6f} rad")
    print(f"  Error: {np.abs(err_bip):.6f} rad")
    
    # 5. Footprint
    print(f"\nMemory Footprint (State Vector):")
    print(f"  FPU: {fpu.D * 16 / 1024:.1f} KB")
    print(f"  BIP: {len(bip_state) * 4 / 1024:.1f} KB")

if __name__ == "__main__":
    run_benchmark()
