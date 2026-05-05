"""Solar System Graph Laplacian construction.

Implements the first-principles phase-space model where orbits are diagonal
content and gravitational interactions are off-diagonal fiber couplings.

Phase 9 vocabulary
------------------

The breathing Laplacian is a *state-dependent (non-autonomous) graph
Laplacian* — the off-diagonal weights `W_{ij}(phi)` are functions of the
current phase state. Equivalently, in the dynamical-systems literature
this is an adaptive Kuramoto-family network with phase-difference-
dependent (PDDP) coupling. See the research notebook §1.4 for the full
positioning across spectral graph theory / dynamical systems / DNLS-on-
a-graph vocabularies.

Resonance table (v0.2.0)
------------------------

The Phase 9 modulation is parameterised as

    W_{ij}(phi) = W_{ij}^{(0)} * (1 + alpha * cos(n_a * phi_a - m_b * phi_b))

with `(n_a, m_b)` chosen by convention so that *n_a orbits of body a
correspond to m_b orbits of body b* over the resonance period. The
RESONANCES table at module level is the SSOT for all four wired pairs.

Convention: for a mean-motion ratio `P_b / P_a = n_a / m_b` (with body a
faster than body b, i.e. larger ω_a), the resonant angle is canonically
`m_b * phi_a - n_a * phi_b` (slow combination). The cosine is symmetric,
so for the breathing modulation we use `n_a * phi_a - m_b * phi_b` —
mathematically equivalent under cos(), and consistent with the v0.1.0
Jupiter-Saturn 5:2 wiring (n_J = 5, m_S = 2).
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple
from .bodies import BODIES, Body


@dataclass(frozen=True)
class Resonance:
    """A Phase 9 breathing-coupling entry.

    `cos(n_a * phi_a - m_b * phi_b)` modulates the static coupling
    weight `W[a, b]` from `L_static`. Modulation depth is global
    (10% in v0.2.0); v0.3.x will derive per-resonance depths from a
    Hamilton/Delaunay-variable Lagrangian.
    """
    body_a: str
    body_b: str
    n_a: int
    m_b: int
    label: str


# Resonance table — single source of truth for the Phase 9 dynamic
# couplings. Wired in laplacian.get_dynamic_laplacian, bip_instrument's
# encode_state, and the C codegen (c/codegen/emit_c_tables.py).
#
# Each entry must have a corresponding non-zero entry in L_static (the
# breathing modulation scales an existing static weight, it does not
# create coupling out of nothing). _define_couplings below ensures
# every resonance pair has a static weight.
RESONANCES: List[Resonance] = [
    Resonance("jupiter",  "saturn",   5, 2, "Jupiter-Saturn 5:2 (Great Conjunction)"),
    Resonance("neptune",  "pluto",    3, 2, "Neptune-Pluto 3:2 (orbital resonance)"),
    Resonance("io",       "europa",   2, 1, "Io-Europa 2:1 (Laplace pair 1)"),
    Resonance("europa",   "ganymede", 2, 1, "Europa-Ganymede 2:1 (Laplace pair 2)"),
    # v0.5.0: famous Saturnian resonances now that the bodies are wired.
    # `(n_a, m_b)` chosen so n_a × P_a = m_b × P_b expresses the
    # mean-motion lock (a faster than b -> n_a > m_b).
    Resonance("mimas",     "tethys",   4, 2, "Mimas-Tethys 4:2 (Cassini Division)"),
    Resonance("enceladus", "dione",    2, 1, "Enceladus-Dione 2:1 (powers Enceladus tidal heating)"),
    Resonance("titan",     "hyperion", 4, 3, "Titan-Hyperion 4:3 (Hyperion chaotic rotation source)"),
]

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
        """State-dependent (non-autonomous) graph Laplacian.

        Walks the module-level RESONANCES table and applies the
        `1 + alpha * cos(n_a * phi_a - m_b * phi_b)` modulation to each
        pair's static coupling weight. Modulation depth `alpha = 0.1`
        is global in v0.2.0; per-resonance depths are deferred to
        v0.3.x's first-principles derivation.

        Returns the combined Hermitian matrix
        `L_trunk + L_pn + L_static * modulation`.
        """
        L = self.L_trunk + self.L_pn + self.L_static.copy()

        alpha = 0.1
        for r in RESONANCES:
            if r.body_a not in self.body_to_idx or r.body_b not in self.body_to_idx:
                continue
            idx_a = self.body_to_idx[r.body_a]
            idx_b = self.body_to_idx[r.body_b]
            res_phase = r.n_a * current_phases[idx_a] - r.m_b * current_phases[idx_b]
            modulation = 1.0 + alpha * np.cos(res_phase)
            L[idx_a, idx_b] *= modulation
            L[idx_b, idx_a] *= modulation

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
        # v0.5.0: Jovian inner regulars + classical Saturnians + co-orbitals.
        moon_map = {
            "moon": "earth",
            "phobos": "mars", "deimos": "mars",
            # Jovian moons
            "metis": "jupiter", "adrastea": "jupiter",
            "amalthea": "jupiter", "thebe": "jupiter",
            "io": "jupiter", "europa": "jupiter",
            "ganymede": "jupiter", "callisto": "jupiter",
            # Saturnian moons (classical + co-orbitals)
            "mimas": "saturn", "enceladus": "saturn",
            "tethys": "saturn", "dione": "saturn", "rhea": "saturn",
            "titan": "saturn", "hyperion": "saturn",
            "iapetus": "saturn", "phoebe": "saturn",
            "janus": "saturn", "epimetheus": "saturn",
            # Uranus / Neptune
            "titania": "uranus",
            "triton": "neptune",
        }
        for moon, planet in moon_map.items():
            if moon not in BODIES:
                continue
            weight = 1e-4 * np.sqrt(BODIES[moon].mass_earth * BODIES[planet].mass_earth)
            couplings.append((planet, moon, weight))
            
        # Tertiary: Resonances and major perturbations.
        # Each pair listed in RESONANCES needs a non-zero static weight
        # here — the Phase 9 breathing modulation scales these weights
        # rather than creating coupling out of nothing.

        # Jupiter-Saturn 5:2 (Great Conjunction)
        couplings.append(("jupiter", "saturn",
            1e-5 * np.sqrt(BODIES["jupiter"].mass_earth * BODIES["saturn"].mass_earth)))

        # Neptune-Pluto 3:2 (orbital resonance). Pluto is in a stable
        # 3:2 mean-motion resonance with Neptune; smaller mass-product
        # than J-S so the coupling is correspondingly smaller.
        if "pluto" in BODIES:
            couplings.append(("neptune", "pluto",
                1e-5 * np.sqrt(BODIES["neptune"].mass_earth * BODIES["pluto"].mass_earth)))

        # Laplace resonance — three-body 4:2:1 mean-motion lock among
        # Io, Europa, Ganymede. Wired here as two pairwise Phase 9
        # modulations (Io-Europa 2:1, Europa-Ganymede 2:1). Inter-moon
        # couplings are stronger than moon-planet because the moons sit
        # close together in their parent's gravity well.
        couplings.append(("io", "europa",
            1e-3 * np.sqrt(BODIES["io"].mass_earth * BODIES["europa"].mass_earth)))
        couplings.append(("europa", "ganymede",
            1e-3 * np.sqrt(BODIES["europa"].mass_earth * BODIES["ganymede"].mass_earth)))

        # v0.5.0: famous Saturnian mean-motion resonances. The static
        # weight here is what the Phase 9 breathing modulation scales;
        # without a non-zero entry the breathing path would be a no-op
        # (and bip_instrument's _encode_state_impl would silently
        # discard the resonance). Inter-moon weights use the same 1e-3
        # scaling factor as the Galileans.
        if "mimas" in BODIES and "tethys" in BODIES:
            couplings.append(("mimas", "tethys",
                1e-3 * np.sqrt(BODIES["mimas"].mass_earth * BODIES["tethys"].mass_earth)))
        if "enceladus" in BODIES and "dione" in BODIES:
            couplings.append(("enceladus", "dione",
                1e-3 * np.sqrt(BODIES["enceladus"].mass_earth * BODIES["dione"].mass_earth)))
        if "titan" in BODIES and "hyperion" in BODIES:
            couplings.append(("titan", "hyperion",
                1e-3 * np.sqrt(BODIES["titan"].mass_earth * BODIES["hyperion"].mass_earth)))

        # Asteroids to Jupiter (no Phase 9 modulation; static perturbation only)
        for ast in ["ceres", "vesta", "pallas", "hygiea"]:
            couplings.append(("jupiter", ast,
                1e-7 * np.sqrt(BODIES["jupiter"].mass_earth * BODIES[ast].mass_earth)))

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
