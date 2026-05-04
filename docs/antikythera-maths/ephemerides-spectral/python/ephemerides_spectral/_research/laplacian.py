"""Solar System Graph Laplacian construction.

Implements the first-principles phase-space model where orbits are diagonal
content and gravitational interactions are off-diagonal fiber couplings.
"""

import numpy as np
from typing import Dict, List, Tuple
from .bodies import BODIES, Body

class SolarSystemLaplacian:
    """Graph Laplacian of the Sol Star System."""

    def __init__(self):
        self.body_names = sorted(BODIES.keys())
        self.n = len(self.body_names)
        self.body_to_idx = {name: i for i, name in enumerate(self.body_names)}
        
        # 1. Base Mean Motions (Diagonal)
        self.L_trunk = self._build_trunk_diagonal()
        
        # 2. Relativistic "Friction" (PN Corrections)
        self.L_pn = self._calculate_pn_corrections()
        
        # 3. Static Fiber couplings
        self.L_static = self._build_static_couplings()

    def _build_trunk_diagonal(self) -> np.ndarray:
        L = np.zeros((self.n, self.n), dtype=np.complex128)
        for i, name in enumerate(self.body_names):
            body = BODIES[name]
            if body.period_days > 0:
                L[i, i] = 2.0 * np.pi / body.period_days
        return L

    def _calculate_pn_corrections(self) -> np.ndarray:
        """Calculate Post-Newtonian frequency shifts (Subtle frequency drag)."""
        L = np.zeros((self.n, self.n), dtype=np.complex128)
        # Relativistic precession of Mercury is the classic example
        # (Approx. 43 arcseconds per century)
        # 43 arcsec / century = 43 * (pi / 180 / 3600) / (100 * 365.25) rad/day
        mercury_precession = 43 * (np.pi / 180 / 3600) / (36525.0)
        if "mercury" in self.body_to_idx:
            idx = self.body_to_idx["mercury"]
            L[idx, idx] = mercury_precession
        return L

    def _build_static_couplings(self) -> np.ndarray:
        L = np.zeros((self.n, self.n), dtype=np.complex128)
        couplings = self._define_couplings()
        for b1, b2, weight in couplings:
            idx1 = self.body_to_idx[b1]
            idx2 = self.body_to_idx[b2]
            L[idx1, idx2] = -weight
            L[idx2, idx1] = -weight
        return L

    def get_dynamic_laplacian(self, current_phases: np.ndarray) -> np.ndarray:
        """Modulate couplings based on current phase-space geometry (Breathing Laplacian)."""
        L = self.L_trunk + self.L_pn + self.L_static
        
        # Add Dynamic Modulation:
        # Strength of coupling between jupiter and saturn varies with phase diff
        if "jupiter" in self.body_to_idx and "saturn" in self.body_to_idx:
            idx_j = self.body_to_idx["jupiter"]
            idx_s = self.body_to_idx["saturn"]
            # 5:2 Resonance modulation (breathing)
            res_phase = (5 * current_phases[idx_j] - 2 * current_phases[idx_s])
            modulation = 1.0 + 0.1 * np.cos(res_phase) # 10% breathing
            L[idx_j, idx_s] *= modulation
            L[idx_s, idx_j] *= modulation
            
        return L

    def _define_couplings(self) -> List[Tuple[str, str, float]]:
        """Define the interaction topology of the solar system."""
        couplings = []
        
        # Primary: All planets to the Sun
        sun_mass = BODIES["sun"].mass_earth
        for name, body in BODIES.items():
            if body.category == "planet":
                # Interaction strength proportional to sqrt(m1*m2)
                # scaled to be a perturbation (e.g. 0.01% of mean motion)
                weight = 1e-6 * np.sqrt(body.mass_earth * sun_mass)
                couplings.append(("sun", name, weight))
                
        # Secondary: Moons to their parent planets
        moon_map = {
            "moon": "earth",
            "phobos": "mars", "deimos": "mars",
            "io": "jupiter", "europa": "jupiter", "ganymede": "jupiter", "callisto": "jupiter",
            "titan": "saturn", "enceladus": "saturn", "rhea": "saturn",
            "titania": "uranus",
            "triton": "neptune"
        }
        for moon, planet in moon_map.items():
            weight = 1e-4 * np.sqrt(BODIES[moon].mass_earth * BODIES[planet].mass_earth)
            couplings.append((planet, moon, weight))
            
        # Tertiary: Resonances and major perturbations
        # Jupiter-Saturn (The Great Conjunction)
        couplings.append(("jupiter", "saturn", 1e-5 * np.sqrt(BODIES["jupiter"].mass_earth * BODIES["saturn"].mass_earth)))
        
        # Asteroids to Jupiter
        for ast in ["ceres", "vesta", "pallas", "hygiea"]:
            couplings.append(("jupiter", ast, 1e-7 * np.sqrt(BODIES["jupiter"].mass_earth * BODIES[ast].mass_earth)))
            
        return couplings

    @property
    def L_lti(self) -> np.ndarray:
        """LTI snapshot: trunk + PN + static couplings, no breathing.

        Provided for reference / regression baselines (the Phase 8 propagator).
        For Phase 9 evolution, use ``get_dynamic_laplacian(current_phases)``
        and integrate iteratively in chunks.
        """
        return self.L_trunk + self.L_pn + self.L_static

    def get_propagator(self, delta_days: float) -> np.ndarray:
        """Compute the LTI unitary propagator U = exp(-i * L_lti * delta_days).

        Note: this is the static (Phase 8) propagator. For Phase 9 breathing
        dynamics, callers should iterate ``get_dynamic_laplacian`` in chunks
        rather than relying on a single matrix exponential.
        """
        from scipy.linalg import expm
        return expm(-1j * self.L_lti * delta_days)

    def evolve_state(self, initial_phases: np.ndarray, delta_days: float) -> np.ndarray:
        """Evolve phases using the LTI propagator (Phase 8 baseline).

        Returns the evolved phases in radians. For Phase 9 dynamics the BIP
        and reference instruments do their own chunked integration over
        ``get_dynamic_laplacian`` — this method is kept for the LTI baseline.
        """
        psi_0 = np.exp(1j * initial_phases)
        U = self.get_propagator(delta_days)
        psi_t = U @ psi_0
        return np.angle(psi_t)
