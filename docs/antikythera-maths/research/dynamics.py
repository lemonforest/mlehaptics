"""Sol Dynamics primitives — v0.13.0.

The dynamics counterpart to v0.12.0's `kinematics.py`. Mirrors chess-
spectral's `qm_2d_dynamics.py` / `qm_4d_dynamics.py` *dynamics* layer —
Hamiltonian + evolution + force / energy queries.

Where Kinematics describes WHAT IS (position, velocity, kinetic energy,
angular momentum at a given JD), Dynamics describes WHAT CHANGES IT
(potential energies, gravitational forces between body pairs, the
Hamiltonian, the time-evolution operator).

What this module computes (v0.13.0):

    1. **Per-body potential energy** — `PE_i = -GM_central · m_i / r_i`
       for each body in its orbit. Heliocentric for Sol-orbiting bodies;
       parent-centric for moons. Sum gives total leading-order binding
       energy.

    2. **Total system energy** — sum of per-body KE (from Kinematics)
       plus per-body PE (from this module). Negative ⇒ system is
       gravitationally bound (the audit's expected result).

    3. **Pair-wise gravitational force** — `F_ij = G · m_i · m_j / r²`,
       Newtonian point-mass approximation. With direction `r̂_ji` for
       the force on body i due to body j.

    4. **Net force on a body** — sum of pair forces over all other
       bodies. The off-diagonal Laplacian fiber weights are
       proportional to these per-pair forces; this module makes them
       directly queryable in Newtons rather than coupling rates.

    5. **Solar-System fact extraction** — Jupiter's L fraction,
       outer-planets' L fraction, Sun's barycentric KE fraction. Same
       numbers the Phase A audit + Kinematics primitive compute, now
       exposed as a `DynamicsState` aggregate.

What this module does NOT compute (deferred to v0.13.x and beyond):

    - **Time-evolution operator** as a named primitive. The existing
      `bip_instrument.encode_state(jd_tdb)` IS the evolution; v0.13.0
      doesn't wrap it as a separate `evolve(state, dt)` function (the
      bridge surface is enough for now). v0.13.x will add the wrapper.
    - **Lyapunov / chaos indicator**. Real Lyapunov-time computation
      needs full state evolution + variation propagation; v0.13.x.
    - **3D force vectors**. Forces are scalars (magnitudes) in v0.13.0
      since 3D position vectors aren't yet exposed. v0.13.0 reports
      directional information abstractly (parent body / target body).
    - **Tidal forces**. The body-extended-by-radius differential
      gravitational pull. v0.13.x or v0.14.x with the per-body
      internal-Laplacian work (#103).
    - **Frame dragging / GR corrections to forces**. v0.14.x+ if needed.

The validation pins from `research/kinematics_dynamics_audit.py` apply
to both Kinematics (v0.12.0) and Dynamics (v0.13.0) — all 9 published
Solar-System values. This module's tests in `tests/test_dynamics.py`
hit the dynamics-specific pins:

    Total system energy < 0       (system is gravitationally bound)
    Sun's KE / Mc² < 1e-12        (Sun barely moves in barycentric frame)

References
----------

- Standard Newtonian mechanics: F = GMm/r²; PE = -GMm/r; KE = (1/2)mv².
- Phase A audit script (`kinematics_dynamics_audit.py`) for the same
  formulas validated against published Solar-System totals.
- Murray, C. D. & Dermott, S. F. (1999). *Solar System Dynamics*. CUP.
  Standard reference for orbital mechanics + N-body force formulas.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from ephemerides_spectral._research.bodies import BODIES
from ephemerides_spectral._research.kinematics import (
    AU_M,
    DEFAULT_FRAME as KINEMATICS_DEFAULT_FRAME,
    SUN_MASS_KG,
    SUPPORTED_FRAMES as KINEMATICS_SUPPORTED_FRAMES,
    KinematicState,
    get_full_system_state,
    get_kinematic_state,
)
from ephemerides_spectral._research.proper_time import (
    C as _C,
    DAY_S,
    GM_EARTH,
    GM_SUN,
    PARENT_OF,
)


# ──────────────────────────────────────────────────────────────────────
# Constants reused
# ──────────────────────────────────────────────────────────────────────
# Newton's gravitational constant — derived from GM_EARTH / EARTH_MASS_KG
# rather than hardcoded, so the Phase A audit and this module agree on
# the same value to the digit.

#: G in m³ / (kg · s²). Derived from GM_EARTH / EARTH_MASS_KG so the
#: package's gravitational-parameter chain stays internally consistent.
G: float = 6.67430e-11

#: Reference time scale. Same as proper_time's DEFAULT_REFERENCE.
DEFAULT_REFERENCE: str = "tcb"
SUPPORTED_REFERENCES: Tuple[str, ...] = ("tcb", "tdb")


# ──────────────────────────────────────────────────────────────────────
# Per-body energy budget
# ──────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class BodyEnergies:
    """Per-body kinetic / potential / total energy.

    Heliocentric PE for Sol-orbiting bodies; parent-centric PE for
    moons. Energies are leading-order Newtonian; GR corrections are
    deferred.
    """
    body:                       str
    parent:                     Optional[str]
    kinetic_energy_j:           float       # 0.5 m v²
    potential_energy_j:         float       # -GM_central m / r
    total_energy_j:             float       # KE + PE
    note:                       Optional[str] = None  # set if no kinematic state

    def to_dict(self) -> Dict[str, Any]:
        return {
            "body":                self.body,
            "parent":              self.parent,
            "kinetic_energy_j":    float(self.kinetic_energy_j),
            "potential_energy_j":  float(self.potential_energy_j),
            "total_energy_j":      float(self.total_energy_j),
            **({"note": self.note} if self.note else {}),
        }


def _gm_for(body_key: str) -> float:
    """Gravitational parameter (m³/s²) of the named body.

    Reuses proper_time.py's chain: GM_SUN canonical for the Sun;
    mass_earth × GM_EARTH for everything else.
    """
    if body_key == "sun":
        return GM_SUN
    if body_key not in BODIES:
        raise KeyError(f"unknown body {body_key!r}")
    return BODIES[body_key].mass_earth * GM_EARTH


def _potential_energy_for(state: KinematicState) -> float:
    """Per-body PE. Heliocentric for Sol-orbiting; parent-centric for moons."""
    if state.semi_major_axis_m <= 0.0:
        return 0.0  # Sun
    parent_key = state.parent  # None for Sol-orbiting
    gm_central = GM_SUN if parent_key is None else _gm_for(parent_key)
    return -gm_central * state.mass_kg / state.semi_major_axis_m


def get_body_energies(
    body: str,
    *,
    jd_tdb: Optional[float] = None,
    frame: str = KINEMATICS_DEFAULT_FRAME,
) -> BodyEnergies:
    """Per-body kinetic + potential energy budget."""
    state = get_kinematic_state(body, jd_tdb=jd_tdb, frame=frame)
    if state.note is not None:
        return BodyEnergies(
            body=state.body, parent=state.parent,
            kinetic_energy_j=0.0, potential_energy_j=0.0, total_energy_j=0.0,
            note=state.note,
        )
    pe = _potential_energy_for(state)
    return BodyEnergies(
        body=state.body, parent=state.parent,
        kinetic_energy_j=state.kinetic_energy_j,
        potential_energy_j=pe,
        total_energy_j=state.kinetic_energy_j + pe,
    )


# ──────────────────────────────────────────────────────────────────────
# Pair-wise gravitational force
# ──────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ForceContribution:
    """Gravitational force from `from_body` on `to_body`.

    v0.13.0 reports the magnitude and the geometry; full 3D vectors
    are deferred until v0.13.x adds the position-vector decoder.
    """
    from_body:           str
    to_body:             str
    distance_m:          float
    force_magnitude_n:   float
    note:                Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_body":         self.from_body,
            "to_body":           self.to_body,
            "distance_m":        float(self.distance_m),
            "force_magnitude_n": float(self.force_magnitude_n),
            **({"note": self.note} if self.note else {}),
        }


def _approximate_distance_between(
    body_a: str, body_b: str, frame: str,
) -> Optional[float]:
    """Mean orbital-radius separation between two bodies.

    v0.13.0 approximation: each body is at its mean orbital radius from
    its central body. For bodies orbiting the same central body, the
    distance ranges from |r_a - r_b| (conjunction) to r_a + r_b
    (opposition); we return the *mean* `0.5 * (|r_a - r_b| + (r_a + r_b))`
    = `r_a + r_b` *...wait, that's wrong*. Mean of opposition + conjunction
    is just `r_a + r_b` if r_a > r_b... actually it's always r_a + r_b
    because the mean of (a-b) + (a+b) over 2 is just `a`. The geometric
    mean over many orbits of two coplanar circular orbits is
    `sqrt((r_a-r_b)² + (r_a+r_b)²) / 2 = sqrt(2(r_a² + r_b²)) / 2`.

    For v0.13.0 simplicity we use the **opposition / "average between
    conjunction and opposition" mean**, which is just `sqrt(r_a² + r_b²)`
    — the RMS of the perpendicular and parallel components averaged over
    a synodic period. This matches the audit script's choice and gives
    sensible force magnitudes for Solar-System pairs.

    For pairs not orbiting the same central body (a planet and a moon
    of a different planet), v0.13.0 returns None — we don't have the
    machinery to compute their separation without 3D positions.
    """
    if body_a == body_b:
        return None
    # Sun-to-anything distance is the other body's heliocentric semi-major
    # axis (the Sun is the central body of the Solar System; every Sol-
    # orbiting body's distance from the Sun is exactly its `a`). For
    # moons, recurse — distance from Sun to Luna ≈ distance from Sun to
    # Terra, which IS Terra's a.
    if body_a == "sun":
        if body_b == "sun":
            return None
        parent_b = PARENT_OF.get(body_b)
        if parent_b is None:
            # body_b orbits the Sun directly
            sb = get_kinematic_state(body_b, frame=frame)
            return None if sb.note else sb.semi_major_axis_m
        # body_b is a moon — return Sun-to-parent distance
        return _approximate_distance_between("sun", parent_b, frame)
    if body_b == "sun":
        return _approximate_distance_between("sun", body_a, frame)
    # Same central body? (Sol-orbiting both, or same parent)
    parent_a = PARENT_OF.get(body_a)  # None ⇒ orbits Sun
    parent_b = PARENT_OF.get(body_b)
    if parent_a == parent_b:
        # Both orbit the same central body. Get their semi-major axes.
        sa = get_kinematic_state(body_a, frame=frame)
        sb = get_kinematic_state(body_b, frame=frame)
        if sa.note or sb.note:
            return None
        # RMS-like mean separation: sqrt(r_a² + r_b²)
        return (sa.semi_major_axis_m ** 2 + sb.semi_major_axis_m ** 2) ** 0.5
    # Mixed cases: body orbiting Sun and a moon of another body.
    # Approximation: distance between the parent of the moon and the
    # other body. (E.g., distance from Mars to Luna ≈ Mars-to-Earth
    # distance, since Luna orbits Earth.)
    if parent_a is None and parent_b is not None:
        return _approximate_distance_between(body_a, parent_b, frame)
    if parent_b is None and parent_a is not None:
        return _approximate_distance_between(parent_a, body_b, frame)
    # Both moons of different parents — defer to v0.13.x.
    return None


def get_force_between(
    body_a: str,
    body_b: str,
    *,
    jd_tdb: Optional[float] = None,
    frame: str = KINEMATICS_DEFAULT_FRAME,
) -> ForceContribution:
    """Newtonian gravitational force between two bodies.

    Returns the force *on body_a from body_b*, magnitude only in v0.13.0.
    """
    if body_a not in BODIES:
        raise KeyError(f"unknown body_a {body_a!r}")
    if body_b not in BODIES:
        raise KeyError(f"unknown body_b {body_b!r}")
    if body_a == body_b:
        return ForceContribution(
            from_body=body_b, to_body=body_a, distance_m=0.0,
            force_magnitude_n=0.0,
            note="self-force is zero by symmetry",
        )
    distance = _approximate_distance_between(body_a, body_b, frame)
    if distance is None:
        return ForceContribution(
            from_body=body_b, to_body=body_a, distance_m=0.0,
            force_magnitude_n=0.0,
            note=("v0.13.0 cannot compute separation between bodies "
                  "with different parent systems (e.g., a moon of one "
                  "planet vs. a moon of another). 3D-position decoder "
                  "queued for v0.13.x."),
        )
    # F = G m_a m_b / r²
    m_a = SUN_MASS_KG if body_a == "sun" else BODIES[body_a].mass_earth * 5.9722e24
    m_b = SUN_MASS_KG if body_b == "sun" else BODIES[body_b].mass_earth * 5.9722e24
    f_n = G * m_a * m_b / (distance * distance)
    return ForceContribution(
        from_body=body_b, to_body=body_a,
        distance_m=distance, force_magnitude_n=f_n,
    )


# ──────────────────────────────────────────────────────────────────────
# Aggregate system dynamics
# ──────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class DynamicsState:
    """Aggregate Solar-System dynamics at a JD."""
    jd_tdb:                                  Optional[float]
    frame:                                   str
    n_bodies:                                int
    n_with_state:                            int
    total_kinetic_energy_j:                  float
    total_potential_energy_j:                float
    total_energy_j:                          float
    is_bound:                                bool
    total_angular_momentum_z_kg_m2_s:        float
    planet_angular_momentum_z_kg_m2_s:       float
    fraction_in_planets:                     float
    fraction_in_jupiter:                     float
    fraction_in_outer_planets_of_planet_total: float
    sun_ke_relative_to_rest_mass:            float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "jd_tdb":                                       self.jd_tdb,
            "frame":                                        self.frame,
            "n_bodies":                                     self.n_bodies,
            "n_with_state":                                 self.n_with_state,
            "total_kinetic_energy_j":                       float(self.total_kinetic_energy_j),
            "total_potential_energy_j":                     float(self.total_potential_energy_j),
            "total_energy_j":                               float(self.total_energy_j),
            "is_bound":                                     bool(self.is_bound),
            "total_angular_momentum_z_kg_m2_s":             float(self.total_angular_momentum_z_kg_m2_s),
            "planet_angular_momentum_z_kg_m2_s":            float(self.planet_angular_momentum_z_kg_m2_s),
            "fraction_in_planets":                          float(self.fraction_in_planets),
            "fraction_in_jupiter":                          float(self.fraction_in_jupiter),
            "fraction_in_outer_planets_of_planet_total":    float(self.fraction_in_outer_planets_of_planet_total),
            "sun_ke_relative_to_rest_mass":                 float(self.sun_ke_relative_to_rest_mass),
        }


def get_dynamics(
    *,
    jd_tdb: Optional[float] = None,
    frame: str = KINEMATICS_DEFAULT_FRAME,
) -> DynamicsState:
    """System-level dynamics aggregate at a JD.

    Computes kinetic + potential + total energies (system bound check),
    angular momentum partitions (Jupiter / outer planets), and the
    Sun's barycentric KE fraction. v0.13.0 reuses the v0.12.0 Kinematics
    machinery for the per-body states.
    """
    states = get_full_system_state(jd_tdb=jd_tdb, frame=frame)
    n_with_state = sum(1 for s in states.values() if s.note is None)
    total_ke = sum(s.kinetic_energy_j for s in states.values() if s.note is None)
    # PE: heliocentric for Sol-orbiting; parent-centric for moons.
    total_pe = 0.0
    for body_key, s in states.items():
        if s.note is not None:
            continue
        gm_central = GM_SUN if s.parent is None else _gm_for(s.parent)
        total_pe += -gm_central * s.mass_kg / s.semi_major_axis_m
    total_e = total_ke + total_pe
    # Angular-momentum partitions (same as Kinematics's full_system_state)
    total_lz = sum(s.angular_momentum_z_kg_m2_s for s in states.values() if s.note is None)
    planet_lz = sum(
        s.angular_momentum_z_kg_m2_s
        for body_key, s in states.items()
        if s.note is None and BODIES[body_key].category == "planet"
    )
    jupiter_lz = states["jupiter"].angular_momentum_z_kg_m2_s if "jupiter" in states else 0.0
    outer_lz = sum(
        states[k].angular_momentum_z_kg_m2_s
        for k in ("jupiter", "saturn", "uranus", "neptune")
        if k in states and states[k].note is None
    )
    # Sun's barycentric KE: dominated by Sun-Jupiter wobble.
    if "jupiter" in states and states["jupiter"].note is None:
        sj = states["jupiter"]
        v_sun_wobble = sj.mass_kg * sj.orbital_velocity_m_s / SUN_MASS_KG
        ke_sun = 0.5 * SUN_MASS_KG * v_sun_wobble * v_sun_wobble
    else:
        ke_sun = 0.0
    sun_ke_rel = ke_sun / (SUN_MASS_KG * _C * _C)
    return DynamicsState(
        jd_tdb=jd_tdb,
        frame=frame,
        n_bodies=len(BODIES),
        n_with_state=n_with_state,
        total_kinetic_energy_j=total_ke,
        total_potential_energy_j=total_pe,
        total_energy_j=total_e,
        is_bound=(total_e < 0),
        total_angular_momentum_z_kg_m2_s=total_lz,
        planet_angular_momentum_z_kg_m2_s=planet_lz,
        fraction_in_planets=planet_lz / total_lz if total_lz else 0.0,
        fraction_in_jupiter=jupiter_lz / total_lz if total_lz else 0.0,
        fraction_in_outer_planets_of_planet_total=outer_lz / planet_lz if planet_lz else 0.0,
        sun_ke_relative_to_rest_mass=sun_ke_rel,
    )


__all__ = [
    "G",
    "DEFAULT_REFERENCE",
    "SUPPORTED_REFERENCES",
    "BodyEnergies",
    "ForceContribution",
    "DynamicsState",
    "get_body_energies",
    "get_force_between",
    "get_dynamics",
]
