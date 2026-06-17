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

import cmath
import math
from dataclasses import dataclass
from typing import Dict, List, Tuple
from .bodies import BODIES, Body


# ---------------------------------------------------------------------------
# numpy-free linear-algebra helpers (v0.31.0rc4)
# ---------------------------------------------------------------------------
#
# These replace the handful of numpy/scipy operations the breathing
# Laplacian needs. Matrices are plain ``list[list[complex]]`` (row-major);
# scalar transcendentals route through stdlib ``math``/``cmath`` so the
# float bytes match the previous numpy path (same libm).


def _zeros(n: int) -> List[List[complex]]:
    """n x n zero matrix as a list-of-lists of complex."""
    return [[0j for _ in range(n)] for _ in range(n)]


def _matvec(M: List[List[complex]], v: List[complex]) -> List[complex]:
    """Dense matrix * vector (complex)."""
    n = len(M)
    out: List[complex] = [0j] * n
    for i in range(n):
        row = M[i]
        s = 0j
        for j in range(n):
            s += row[j] * v[j]
        out[i] = s
    return out


def expm_neg_i_hermitian(L_rows: List[List[complex]], t: float) -> List[List[complex]]:
    """``expm(-1j * L * t)`` for a Hermitian ``L`` via eigendecomposition.

    ``L_rows`` is a Hermitian matrix as ``list[list[complex]]``. Using
    the spectral theorem ``expm(-1j L t) = V diag(exp(-i lambda t)) V^H``
    via srmech's numpy-free Hermitian eigensolver. Matches
    ``scipy.linalg.expm(-1j*L*t)`` to ~1e-12 (validated against the
    pre-flip path).
    """
    from srmech.amsc.mat import Mat
    from srmech.amsc.laplacian import mat_hermitian_eigendecompose

    n = len(L_rows)
    eigvals, eigvecs = mat_hermitian_eigendecompose(Mat.from_rows(L_rows))
    lam = [row[0].real if hasattr(row[0], "real") else float(row[0])
           for row in eigvals.tolist()]
    V = eigvecs.tolist()  # n x n complex; columns are the eigenvectors
    g = [cmath.exp(complex(0.0, -1.0) * lk * t) for lk in lam]
    out = [[0j] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            s = 0j
            for k in range(n):
                s += V[i][k] * g[k] * V[j][k].conjugate()
            out[i][j] = s
    return out


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

    def _build_trunk_diagonal(self) -> List[List[complex]]:
        L = _zeros(self.n)
        for i, name in enumerate(self.body_names):
            body = BODIES[name]
            if body.period_days > 0:
                L[i][i] = 2.0 * math.pi / body.period_days
        return L

    def _calculate_pn_corrections(self) -> List[List[complex]]:
        """Calculate Post-Newtonian frequency shifts (Subtle frequency drag)."""
        L = _zeros(self.n)
        # Relativistic precession of Mercury is the classic example
        # (Approx. 43 arcseconds per century)
        # 43 arcsec / century = 43 * (pi / 180 / 3600) / (100 * 365.25) rad/day
        mercury_precession = 43 * (math.pi / 180 / 3600) / (36525.0)
        if "mercury" in self.body_to_idx:
            idx = self.body_to_idx["mercury"]
            L[idx][idx] = mercury_precession
        return L

    def _build_static_couplings(self) -> List[List[complex]]:
        L = _zeros(self.n)
        couplings = self._define_couplings()
        for b1, b2, weight in couplings:
            idx1 = self.body_to_idx[b1]
            idx2 = self.body_to_idx[b2]
            L[idx1][idx2] = -weight
            L[idx2][idx1] = -weight
        return L

    def get_dynamic_laplacian(self, current_phases) -> List[List[complex]]:
        """State-dependent (non-autonomous) graph Laplacian.

        Walks the module-level RESONANCES table and applies the
        `1 + alpha * cos(n_a * phi_a - m_b * phi_b)` modulation to each
        pair's static coupling weight. Modulation depth `alpha = 0.1`
        is global in v0.2.0; per-resonance depths are deferred to
        v0.3.x's first-principles derivation.

        Returns the combined Hermitian matrix
        `L_trunk + L_pn + L_static * modulation`.
        """
        n = self.n
        L = [
            [self.L_trunk[i][j] + self.L_pn[i][j] + self.L_static[i][j]
             for j in range(n)]
            for i in range(n)
        ]

        alpha = 0.1
        for r in RESONANCES:
            if r.body_a not in self.body_to_idx or r.body_b not in self.body_to_idx:
                continue
            idx_a = self.body_to_idx[r.body_a]
            idx_b = self.body_to_idx[r.body_b]
            res_phase = r.n_a * current_phases[idx_a] - r.m_b * current_phases[idx_b]
            modulation = 1.0 + alpha * math.cos(res_phase)
            L[idx_a][idx_b] *= modulation
            L[idx_b][idx_a] *= modulation

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
                weight = 1e-6 * math.sqrt(body.mass_earth * sun_mass)
                couplings.append(("sun", name, weight))
                
        # Secondary: Moons to their parent planets
        # v0.5.0: Jovian inner regulars + classical Saturnians + co-orbitals.
        moon_map = {
            "luna": "terra",
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
            weight = 1e-4 * math.sqrt(BODIES[moon].mass_earth * BODIES[planet].mass_earth)
            couplings.append((planet, moon, weight))
            
        # Tertiary: Resonances and major perturbations.
        # Each pair listed in RESONANCES needs a non-zero static weight
        # here — the Phase 9 breathing modulation scales these weights
        # rather than creating coupling out of nothing.

        # Jupiter-Saturn 5:2 (Great Conjunction)
        couplings.append(("jupiter", "saturn",
            1e-5 * math.sqrt(BODIES["jupiter"].mass_earth * BODIES["saturn"].mass_earth)))

        # Neptune-Pluto 3:2 (orbital resonance). Pluto is in a stable
        # 3:2 mean-motion resonance with Neptune; smaller mass-product
        # than J-S so the coupling is correspondingly smaller.
        if "pluto" in BODIES:
            couplings.append(("neptune", "pluto",
                1e-5 * math.sqrt(BODIES["neptune"].mass_earth * BODIES["pluto"].mass_earth)))

        # Laplace resonance — three-body 4:2:1 mean-motion lock among
        # Io, Europa, Ganymede. Wired here as two pairwise Phase 9
        # modulations (Io-Europa 2:1, Europa-Ganymede 2:1). Inter-moon
        # couplings are stronger than moon-planet because the moons sit
        # close together in their parent's gravity well.
        couplings.append(("io", "europa",
            1e-3 * math.sqrt(BODIES["io"].mass_earth * BODIES["europa"].mass_earth)))
        couplings.append(("europa", "ganymede",
            1e-3 * math.sqrt(BODIES["europa"].mass_earth * BODIES["ganymede"].mass_earth)))

        # v0.5.0: famous Saturnian mean-motion resonances. The static
        # weight here is what the Phase 9 breathing modulation scales;
        # without a non-zero entry the breathing path would be a no-op
        # (and bip_instrument's _encode_state_impl would silently
        # discard the resonance). Inter-moon weights use the same 1e-3
        # scaling factor as the Galileans.
        if "mimas" in BODIES and "tethys" in BODIES:
            couplings.append(("mimas", "tethys",
                1e-3 * math.sqrt(BODIES["mimas"].mass_earth * BODIES["tethys"].mass_earth)))
        if "enceladus" in BODIES and "dione" in BODIES:
            couplings.append(("enceladus", "dione",
                1e-3 * math.sqrt(BODIES["enceladus"].mass_earth * BODIES["dione"].mass_earth)))
        if "titan" in BODIES and "hyperion" in BODIES:
            couplings.append(("titan", "hyperion",
                1e-3 * math.sqrt(BODIES["titan"].mass_earth * BODIES["hyperion"].mass_earth)))

        # Asteroids to Jupiter (no Phase 9 modulation; static perturbation only)
        for ast in ["ceres", "vesta", "pallas", "hygiea"]:
            couplings.append(("jupiter", ast,
                1e-7 * math.sqrt(BODIES["jupiter"].mass_earth * BODIES[ast].mass_earth)))

        return couplings

    @property
    def L_lti(self) -> List[List[complex]]:
        """LTI snapshot: trunk + PN + static couplings, no breathing.

        Provided for reference / regression baselines (the Phase 8 propagator).
        For Phase 9 evolution, use ``get_dynamic_laplacian(current_phases)``
        and integrate iteratively in chunks.
        """
        n = self.n
        return [
            [self.L_trunk[i][j] + self.L_pn[i][j] + self.L_static[i][j]
             for j in range(n)]
            for i in range(n)
        ]

    def get_propagator(self, delta_days: float) -> List[List[complex]]:
        """Compute the LTI unitary propagator U = exp(-i * L_lti * delta_days).

        Note: this is the static (Phase 8) propagator. For Phase 9 breathing
        dynamics, callers should iterate ``get_dynamic_laplacian`` in chunks
        rather than relying on a single matrix exponential.

        v0.31.0rc4: numpy-free. ``L_lti`` is Hermitian, so the unitary
        propagator is computed by Hermitian eigendecomposition
        (``expm_neg_i_hermitian``) instead of ``scipy.linalg.expm``.
        """
        return expm_neg_i_hermitian(self.L_lti, float(delta_days))

    def evolve_state(self, initial_phases, delta_days: float) -> List[float]:
        """Evolve phases using the LTI propagator (Phase 8 baseline).

        Returns the evolved phases in radians. For Phase 9 dynamics the BIP
        and reference instruments do their own chunked integration over
        ``get_dynamic_laplacian`` — this method is kept for the LTI baseline.
        """
        psi_0 = [cmath.exp(1j * p) for p in initial_phases]
        U = self.get_propagator(delta_days)
        psi_t = _matvec(U, psi_0)
        return [cmath.phase(z) for z in psi_t]
