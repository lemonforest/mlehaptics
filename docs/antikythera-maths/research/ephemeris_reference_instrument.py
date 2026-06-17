"""DE441 Reference HDC Instrument — First-Principles Implementation.

Encodes celestial bodies and their gravitational perturbations as resonant 
HDC states via a Solar System Graph Laplacian.
"""

from __future__ import annotations

import argparse
import cmath
import math
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .bodies import BODIES, Body
from .laplacian import SolarSystemLaplacian, expm_neg_i_hermitian, _matvec
from .ephemeris_loader import load_ephemeris, EphemerisBundle
from .portable_prng import splitmix64_phases


def _roll(v: List[complex], k: int) -> List[complex]:
    """``numpy.roll(v, k)`` semantics for a Python list (verified equal)."""
    n = len(v)
    k %= n
    return v[-k % n:] + v[:-k % n]


def _norm(v: List[complex]) -> float:
    """Euclidean norm of a complex vector (``numpy.linalg.norm`` for 1-D)."""
    return math.sqrt(sum((z.real * z.real + z.imag * z.imag) for z in v))

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

    def _initialize_bases(self) -> Dict[str, List[complex]]:
        """Per-body complex128 channel bases (unit phasors / sqrt(D)).

        v0.31.0rc4: numpy-free. The legacy path seeded these via
        ``numpy.random.default_rng(2026+i).uniform(0, 2π, D)`` (PCG64),
        a stream that can't be reproduced without numpy. The reference
        instrument is the ``backend="fpu-ref"`` backwards-compat path;
        no byte-exact test pins these base bytes (the BIP-and-lift
        bases live in ``bip_hd_lift`` and stay byte-identical). The
        portable splitmix64 stream supplies a deterministic numpy-free
        phase source, matching the BIP-and-lift basis-seeding scheme.
        """
        bases: Dict[str, List[complex]] = {}
        inv = 1.0 / math.sqrt(self.D)
        for i, body in enumerate(self.body_names):
            phases = splitmix64_phases((2026 + i) & ((1 << 64) - 1), self.D)
            bases[body] = [cmath.exp(1j * p) * inv for p in phases]
        return bases

    def _calibrate_initial_phases(self, jd: float) -> List[float]:
        """Calibrate the phase angles (radians) from ephemeris truth at epoch."""
        if self.bundle is None:
            return [0.0] * len(self.body_names)

        ts = self.bundle.ts
        t = ts.tt_jd(jd)
        phases = [0.0] * len(self.body_names)
        
        # Center points for categories
        # Planets orbit the Sun
        # Moons orbit their parents
        moon_parent_map = {
            "luna": "terra",
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
                # v0.9.0: bundle.lookup translates internal terra/luna
                # to JPL-side EARTH/MOON; eph[] direct access doesn't.
                target = self.bundle.lookup(target_key)

                # 2. Resolve Observer (Center of Orbit)
                if body_info.category == "planet":
                    center = self.bundle.lookup("sun")
                elif body_info.category == "moon":
                    parent_name = moon_parent_map.get(name, "terra")
                    parent_key = parent_name.upper()
                    if parent_name in ["terra", "mars", "jupiter", "saturn", "uranus", "neptune"]:
                         parent_key += " BARYCENTER"
                    center = self.bundle.lookup(parent_key)
                else:
                    center = self.bundle.lookup("sun")
                
                # 3. Observe
                astrometric = center.at(t).observe(target)
                _, lon, _ = astrometric.ecliptic_latlon()
                phases[i] = lon.radians
                
            except (KeyError, ValueError):
                if body_info.period_days > 0:
                    phases[i] = (2.0 * math.pi * (jd % body_info.period_days) / body_info.period_days)
                else:
                    phases[i] = 0.0

        return phases

    def encode_state(self, date_jd: float) -> List[complex]:
        """Evolve phases using Breathing Laplacian and encode as HDC state vector.

        v0.31.0rc4: numpy-free. The breathing Laplacian is Hermitian, so
        the per-chunk propagator ``expm(-1j L dt)`` is computed by
        Hermitian eigendecomposition (``expm_neg_i_hermitian``) instead
        of ``scipy.linalg.expm`` — matches the previous path to ~1e-12.
        """
        delta_t = date_jd - REFERENCE_JD

        # 1. First-Principles Evolution (Iterative Breathing)
        # We evolve in chunks to update the dynamic couplings
        # 365.25 / 12 ~= 30 day chunks
        chunk_size = 30.0
        num_chunks = int(abs(delta_t) / chunk_size)
        step = chunk_size if delta_t > 0 else -chunk_size

        current_phases = list(self.initial_phases)

        for _ in range(num_chunks):
            L_dyn = self.laplacian.get_dynamic_laplacian(current_phases)
            U = expm_neg_i_hermitian(L_dyn, step)
            psi = _matvec(U, [cmath.exp(1j * p) for p in current_phases])
            current_phases = [cmath.phase(z) for z in psi]

        # Final partial step
        remainder = delta_t - (num_chunks * step)
        if abs(remainder) > 1e-6:
            L_dyn = self.laplacian.get_dynamic_laplacian(current_phases)
            U = expm_neg_i_hermitian(L_dyn, remainder)
            psi = _matvec(U, [cmath.exp(1j * p) for p in current_phases])
            current_phases = [cmath.phase(z) for z in psi]

        # 2. HDC Superposition
        state: List[complex] = [0j] * self.D
        for i, name in enumerate(self.body_names):
            residue = int((current_phases[i] / (2.0 * math.pi)) * self.D) % self.D
            basis = self.channel_bases[name]
            rolled = _roll(basis, residue)
            for k in range(self.D):
                state[k] += rolled[k]

        norm = _norm(state)
        if norm > 0:
            state = [z / norm for z in state]
        return state

    def bind_observer(self, state: List[complex], body: str, lat: float,
                      lon: float) -> List[complex]:
        """Unitary observer binding.

        v0.31.0rc4: numpy-free. The observer coord basis is seeded from
        the portable splitmix64 stream (seed 9999), matching the
        instrument's numpy-free base-seeding scheme.
        """
        body_basis = self.channel_bases.get(body.lower())
        if body_basis is None:
            raise ValueError(f"Body {body} not supported.")

        lat_res = int(((lat + 90) / 180) * self.D) % self.D
        lon_res = int(((lon + 180) / 360) * self.D) % self.D

        coord_phases = splitmix64_phases(9999 & ((1 << 64) - 1), self.D)
        coord_basis = [cmath.exp(1j * p) for p in coord_phases]
        coord_op = _roll(coord_basis, (lat_res * COPRIME_LAT + lon_res * COPRIME_LON) % self.D)

        sqrt_D = math.sqrt(self.D)
        return [state[k] * (body_basis[k] * coord_op[k]) * sqrt_D
                for k in range(self.D)]

    def get_syzygy_operator(self) -> List[complex]:
        """Construct Syzygy Operator.

        v0.31.0rc4: numpy-free. Node basis seeded from splitmix64 (777).
        """
        node_phases = splitmix64_phases(777 & ((1 << 64) - 1), self.D)
        inv = 1.0 / math.sqrt(self.D)
        node_basis = [cmath.exp(1j * p) * inv for p in node_phases]
        # Alignment of Sun and Moon
        sun_b = self.channel_bases["sun"]
        luna_b = self.channel_bases["luna"]
        s_op = [sun_b[k] + luna_b[k] + node_basis[k] for k in range(self.D)]
        norm = _norm(s_op)
        if norm > 0:
            s_op = [z / norm for z in s_op]
        return s_op

    def get_eclipse_probability(self, state: List[complex]) -> float:
        """|<state, syzygy_operator>|.

        v0.31.0rc4: numpy-free. ``vdot`` conjugates the first argument.
        """
        s_op = self.get_syzygy_operator()
        acc = sum(state[k].conjugate() * s_op[k] for k in range(self.D))
        return math.hypot(acc.real, acc.imag)

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
    luna_basis = instrument.channel_bases["luna"]
    # (Simplified alignment check via dot product projection)
    def _vdot_abs(a, b):
        acc = sum(a[k].conjugate() * b[k] for k in range(len(a)))
        return math.hypot(acc.real, acc.imag)
    proj_start = _vdot_abs(h_start, luna_basis)
    proj_metonic = _vdot_abs(h_metonic, luna_basis)
    print(f"Lunar Resonance (t=0): {proj_start:.4f}")
    print(f"Lunar Resonance (t=19yr): {proj_metonic:.4f}")
    print(f"Resonance Delta: {abs(proj_metonic - proj_start):.6f}")

    # 4. Phase 6: Higher-Order Perturbations (The Jupiter-Saturn Fiber)
    print(f"\n[Phase 6] Higher-Order Perturbations (Gas Giant Couplings)")
    print("-" * 60)
    # Inspect the off-diagonal coupling in the Laplacian
    idx_j = instrument.laplacian.body_to_idx["jupiter"]
    idx_s = instrument.laplacian.body_to_idx["saturn"]
    coupling = instrument.laplacian.L_static[idx_j][idx_s]
    print(f"Jupiter-Saturn Fiber Strength: {abs(coupling):.2e} rad/day")

    print("\nObserver View: Mars (0°N, 0°E)")
    v_local = instrument.bind_observer(h_state, "mars", 0.0, 0.0)
    print(f"V_local norm: {_norm(v_local):.4f}")

if __name__ == "__main__":
    main()
