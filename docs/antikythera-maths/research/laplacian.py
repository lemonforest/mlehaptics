"""Solar System Graph Laplacian construction.

Implements the first-principles phase-space model where orbits are diagonal
content and gravitational interactions are off-diagonal fiber couplings.
"""

import numpy as np
from typing import Dict, List, Tuple
from .bodies import BODIES, Body

class SolarSystemLaplacian:
    """Graph Laplacian of the solar system."""

    def __init__(self):
        self.body_names = sorted(BODIES.keys())
        self.n = len(self.body_names)
        self.body_to_idx = {name: i for i, name in enumerate(self.body_names)}
        
        self.L = self._build_laplacian()

    def _build_laplacian(self) -> np.ndarray:
        """Construct the NxN Laplacian matrix L.
        
        Diagonal L_ii = 2*pi / period (mean motion frequency).
        Off-diagonal L_ij = static coupling weight based on relative masses.
        """
        L = np.zeros((self.n, self.n), dtype=np.complex128)
        
        # 1. Diagonal: Mean Motion (Trunk Orbits)
        for i, name in enumerate(self.body_names):
            body = BODIES[name]
            if body.period_days > 0:
                # Frequency in radians per day
                L[i, i] = 2.0 * np.pi / body.period_days
            else:
                L[i, i] = 0.0 # Sun
                
        # 2. Off-Diagonal: Gravitational Interaction (Fiber Coupling)
        # We define a 'Gravity DAG' where bodies couple to their dominant perturbers.
        couplings = self._define_couplings()
        
        for b1, b2, weight in couplings:
            idx1 = self.body_to_idx[b1]
            idx2 = self.body_to_idx[b2]
            # Symmetrized coupling
            L[idx1, idx2] = -weight
            L[idx2, idx1] = -weight
            # Ensure it remains a Laplacian by adjusting the diagonal?
            # Actually, we want L to be the Hamiltonian, so it doesn't 
            # strictly need to be a zero-row-sum graph Laplacian in the 
            # probability sense, but a 'Spectral Graph Theory' Laplacian.
            # We keep the mean motion as the primary energy scale.
            
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

    def get_propagator(self, delta_days: float) -> np.ndarray:
        """Compute the unitary propagator U = exp(-i * L * delta_days)."""
        from scipy.linalg import expm
        return expm(-1j * self.L * delta_days)

    def evolve_state(self, initial_phases: np.ndarray, delta_days: float) -> np.ndarray:
        """Evolve the vector of phases in radians using the Laplacian propagator."""
        # Initial state as a complex vector of phasors
        psi_0 = np.exp(1j * initial_phases)
        U = self.get_propagator(delta_days)
        psi_t = U @ psi_0
        return np.angle(psi_t) # Return evolved phases in radians
