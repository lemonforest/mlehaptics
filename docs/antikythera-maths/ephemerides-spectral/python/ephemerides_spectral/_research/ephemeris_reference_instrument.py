"""DE441 Reference HDC Instrument — First-Principles Implementation.

Encodes celestial bodies and their gravitational perturbations as resonant 
HDC states via a Solar System Graph Laplacian.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from .bodies import BODIES, Body
from .laplacian import SolarSystemLaplacian
from .ephemeris_loader import load_ephemeris, EphemerisBundle

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

D_DEFAULT: int = 65536
REFERENCE_JD: float = 2451545.0  # J2000.0 epoch

COPRIME_LAT = 67
COPRIME_LON = 7

# ---------------------------------------------------------------------------
# CelestialHDCInstrument
# ---------------------------------------------------------------------------

class EphemerisHDCInstrument:
    """First-principles HDC instrument for the Sol Star System."""

    def __init__(self, D: int = D_DEFAULT, kernel: str = "de441", force_high_res: bool = False):
        self.D = D
        self.kernel = kernel
        self.laplacian = SolarSystemLaplacian() # Internal name remains, description changes
        self.body_names = self.laplacian.body_names
        
        # 0. Find skyfield_data directory (Monorepo root)
        research_dir = Path(__file__).resolve().parent
        project_root = research_dir.parents[2]
        data_dir = str(project_root / "skyfield_data")

        # 1. Ephemeris for Calibration and Validation
        try:
            self.bundle: Optional[EphemerisBundle] = load_ephemeris(kernel=kernel, data_dir=data_dir)
        except ValueError:
            self.bundle = None
            
        if self.bundle is None:
            if force_high_res:
                raise RuntimeError(f"High-resolution kernel {kernel} requested but not found in {data_dir}.")
            print(f"WARNING: Kernel {kernel} not loadable from {data_dir}. Falling back to de421 for calibration.")
            self.bundle = load_ephemeris(kernel="de421", data_dir=data_dir)
        
        # 2. HDC Channel Bases (Circular Complex)
        self.channel_bases = self._initialize_bases()
        
        # 3. Calibration: Initial phases at REFERENCE_JD
        self.initial_phases = self._calibrate_initial_phases(REFERENCE_JD)

    def get_body_temporal_resolution(self, body: str = "earth") -> float:
        """Returns the temporal duration of 1 residue shift (pluck+rotate) in seconds.
        
        For Terra (Earth), at D=65536, this is ~481.4 seconds (~8.02 minutes).
        """
        body_info = BODIES.get(body.lower())
        if not body_info or body_info.period_days <= 0:
            return 0.0
        return (body_info.period_days * 86400.0) / self.D

    def _initialize_bases(self) -> Dict[str, np.ndarray]:
        bases = {}
        for i, body in enumerate(self.body_names):
            rng = np.random.default_rng(2026 + i)
            phases = rng.uniform(0, 2 * np.pi, self.D)
            v = np.exp(1j * phases).astype(np.complex128)
            bases[body] = v / np.sqrt(self.D)
        return bases

    def _calibrate_initial_phases(self, jd: float) -> np.ndarray:
        """Calibrate the phase angles (radians) from ephemeris truth at epoch."""
        if self.bundle is None:
            return np.zeros(len(self.body_names))
        
        ts = self.bundle.ts
        t = ts.tt_jd(jd)
        phases = np.zeros(len(self.body_names))
        
        # Center points for categories
        # Planets orbit the Sun
        # Moons orbit their parents
        moon_parent_map = {
            "moon": "earth",
            "phobos": "mars", "deimos": "mars",
            "io": "jupiter", "europa": "jupiter", "ganymede": "jupiter", "callisto": "jupiter",
            "titan": "saturn", "enceladus": "saturn", "rhea": "saturn",
            "titania": "uranus",
            "triton": "neptune"
        }

        for i, name in enumerate(self.body_names):
            body_info = BODIES.get(name)
            if not body_info: continue
            
            try:
                # 1. Resolve Target Body
                target_key = name.upper()
                if body_info.category == "planet":
                    target_key += " BARYCENTER"
                target = self.bundle.eph[target_key]
                
                # 2. Resolve Observer (Center of Orbit)
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
                
                # 3. Observe
                astrometric = center.at(t).observe(target)
                _, lon, _ = astrometric.ecliptic_latlon()
                phases[i] = lon.radians
                
            except (KeyError, ValueError):
                if body_info.period_days > 0:
                    phases[i] = (2.0 * np.pi * (jd % body_info.period_days) / body_info.period_days)
                else:
                    phases[i] = 0.0
                
        return phases

    def encode_state(self, date_jd: float) -> np.ndarray:
        """Evolve phases using Laplacian and encode as HDC state vector."""
        delta_t = date_jd - REFERENCE_JD
        
        # 1. First-Principles Evolution (Algebraic)
        # psi(t) = exp(-i L t) psi(0)
        evolved_phases = self.laplacian.evolve_state(self.initial_phases, delta_t)
        
        # 2. HDC Superposition
        state = np.zeros(self.D, dtype=np.complex128)
        for i, name in enumerate(self.body_names):
            # Phase to residue
            residue = int((evolved_phases[i] / (2.0 * np.pi)) * self.D) % self.D
            basis = self.channel_bases[name]
            state += np.roll(basis, residue)
            
        norm = np.linalg.norm(state)
        if norm > 0:
            state /= norm
        return state

    def bind_observer(self, state: np.ndarray, body: str, lat: float, lon: float) -> np.ndarray:
        """Unitary observer binding."""
        body_basis = self.channel_bases.get(body.lower())
        if body_basis is None:
            raise ValueError(f"Body {body} not supported.")
            
        lat_res = int(((lat + 90) / 180) * self.D) % self.D
        lon_res = int(((lon + 180) / 360) * self.D) % self.D
        
        rng = np.random.default_rng(9999)
        coord_phases = rng.uniform(0, 2 * np.pi, self.D)
        coord_basis = np.exp(1j * coord_phases).astype(np.complex128)
        coord_op = np.roll(coord_basis, (lat_res * COPRIME_LAT + lon_res * COPRIME_LON) % self.D)
        
        observer_op = body_basis * coord_op
        # Unitary binding
        return state * observer_op * np.sqrt(self.D)

    def get_syzygy_operator(self) -> np.ndarray:
        """Construct Syzygy Operator."""
        rng = np.random.default_rng(777)
        node_basis = np.exp(1j * rng.uniform(0, 2*np.pi, self.D)) / np.sqrt(self.D)
        # Alignment of Sun and Moon
        s_op = self.channel_bases["sun"] + self.channel_bases["moon"] + node_basis
        s_op /= np.linalg.norm(s_op)
        return s_op

    def get_eclipse_probability(self, state: np.ndarray) -> float:
        s_op = self.get_syzygy_operator()
        return float(np.abs(np.vdot(state, s_op)))

# ---------------------------------------------------------------------------
# Main / Demo
# ---------------------------------------------------------------------------

def main():
    print("Ephemerides HDC Reference Instrument — Sol Star System Phase Space")
    print("=" * 60)
    
    # 1. Initialize
    instrument = EphemerisHDCInstrument(D=D_DEFAULT, kernel="de441")
    print(f"Instrument calibrated with {len(instrument.body_names)} bodies.")
    
    # 2. Modern Snapshot
    test_jd = REFERENCE_JD + 365.25 # 1 year later
    print(f"\nEncoding state at JD {test_jd} (1 year from J2000)...")
    h_state = instrument.encode_state(test_jd)
    print(f"Terra Resolution: {instrument.get_body_temporal_resolution('earth'):.2f} sec/residue")
    
    # 3. Phase 5: Historical Anchor Validation (The Metonic Resonance)
    print(f"\n[Phase 5] Metonic Cycle Validation (19-year Lunar Resonance)")
    print("-" * 60)
    # 19 solar years is almost exactly 235 lunar months.
    # We check if the lunar phase at t and t + 19yr aligns.
    h_start = instrument.encode_state(REFERENCE_JD)
    h_metonic = instrument.encode_state(REFERENCE_JD + 19 * 365.25)
    
    # Extract Lunar component alignment
    luna_basis = instrument.channel_bases["moon"]
    # (Simplified alignment check via dot product projection)
    proj_start = np.abs(np.vdot(h_start, luna_basis))
    proj_metonic = np.abs(np.vdot(h_metonic, luna_basis))
    print(f"Lunar Resonance (t=0): {proj_start:.4f}")
    print(f"Lunar Resonance (t=19yr): {proj_metonic:.4f}")
    print(f"Resonance Delta: {np.abs(proj_metonic - proj_start):.6f}")

    # 4. Phase 6: Higher-Order Perturbations (The Jupiter-Saturn Fiber)
    print(f"\n[Phase 6] Higher-Order Perturbations (Gas Giant Couplings)")
    print("-" * 60)
    # Inspect the off-diagonal coupling in the Laplacian
    idx_j = instrument.laplacian.body_to_idx["jupiter"]
    idx_s = instrument.laplacian.body_to_idx["saturn"]
    coupling = instrument.laplacian.L[idx_j, idx_s]
    print(f"Jupiter-Saturn Fiber Strength: {np.abs(coupling):.2e} rad/day")
    
    print("\nObserver View: Mars (0°N, 0°E)")
    v_local = instrument.bind_observer(h_state, "mars", 0.0, 0.0)
    print(f"V_local norm: {np.linalg.norm(v_local):.4f}")

if __name__ == "__main__":
    main()
