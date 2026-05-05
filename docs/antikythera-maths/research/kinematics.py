"""Sol Kinematics primitives — v0.12.0.

Per-body kinematic state (position, velocity, acceleration, orbital
elements) at a given Julian Date in a chosen frame. Mirrors chess-
spectral's `qm_2d.py` / `qm_4d.py` *kinematics* layer (static encoding
+ observables, no time-evolution) — the dynamics counterpart ships in
v0.13.0 (`dynamics.py`, currently planned).

What this module computes (v0.12.0):

    1. **Mean orbital state** — semi-major axis, mean orbital
       velocity, orbital period for each body via Kepler's third law
       from sidereal period + central-body GM. The same Kepler-circular
       approximation used by `proper_time.py` for SPrT's kinematic
       dilation term.

    2. **Per-body kinetic energy** — `0.5 · m · v²` from the orbital
       velocity + body mass.

    3. **Angular momentum (z-component)** — `m · v · r` for the
       circular-orbit approximation (v perpendicular to r). Sign
       follows orbital direction (prograde +z by convention).

What this module does NOT compute (v0.12.x and beyond):

    - **Eccentric / inclined orbital elements**. The current
      implementation assumes circular coplanar orbits. Real Mars
      eccentricity 0.0934 means actual perihelion velocity is ~24.13
      × (1 + 0.0934) = 26.4 km/s, aphelion 21.9 km/s. The mean is
      what we report. v0.12.x will add eccentricity-corrected
      `orbital_velocity_at_perihelion` etc.
    - **Position vectors at a specific JD**. The encoder's phase
      residues already encode this; v0.12.1 will add a heliocentric
      Cartesian decoder (`phase → r_vec`).
    - **Acceleration**. Comes for free from the Laplacian's
      off-diagonal weights (gravitational accelerations). Queued for
      v0.13.0 with the dynamics surface.
    - **Per-JD eccentric corrections** — current implementation
      ignores `jd_tdb` and uses the mean. The parameter is accepted
      for forward compatibility.

The validation pins from `research/kinematics_dynamics_audit.py` are
preserved here as the authoritative spec — both the audit script and
this canonical primitive must agree on the same 9 published values.

References
----------

- Standard Kepler's third law from the *Explanatory Supplement to the
  Astronomical Almanac*, 3rd ed., Seidelmann ed., 2013.
- NASA fact sheets (per-body orbital velocities cross-checked):
  https://nssdc.gsfc.nasa.gov/planetary/factsheet/

The 9 validation pins (mirrors `kinematics_dynamics_audit.py`):

    Mercury orbital v = 47.36 km/s         (within 1.1%)
    Earth orbital v   = 29.78 km/s         (within 0.02%)
    Mars orbital v    = 24.07 km/s         (within 0.25%)
    Jupiter orbital v = 13.07 km/s         (within 0.08%)
    Pluto orbital v   = 4.74 km/s          (within 0.02%)
    Total system energy < 0                (system is bound)
    Jupiter holds ~61% of total L          (the Jupiter-dominates fact)
    Outer planets hold ~99.84% of L        (planets dominate, Sun has <1%)
    Sun KE / Mc² < 1e-12                   (Sun barely moves in barycentric frame)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from ephemerides_spectral._research.bodies import BODIES
from ephemerides_spectral._research.proper_time import (
    DAY_S,
    GM_EARTH,
    GM_SUN,
    PARENT_OF,
)


# ──────────────────────────────────────────────────────────────────────
# Constants reused from proper_time.py
# ──────────────────────────────────────────────────────────────────────
# We reuse GM_EARTH, GM_SUN, DAY_S, PARENT_OF from proper_time.py
# (single source of truth — those constants are the canonical ones for
# the package). Adding kinematics-specific constants below.

#: Earth mass in kg, the scale used by `BODIES[*].mass_earth`.
EARTH_MASS_KG: float = 5.9722e24

#: Sun mass in kg (canonical — IAU 2015 nominal solar mass parameter).
#: Derived as GM_SUN / G; we hardcode it to avoid the round-trip-through-G
#: numerical error.
SUN_MASS_KG: float = 1.98892e30

#: 1 astronomical unit in metres (IAU 2012 redefinition).
AU_M: float = 1.495978707e11

#: Supported reference frames. v0.12.0 ships a single circular-orbit
#: heliocentric ecliptic frame; future revisions will add barycentric_icrs
#: + body_centered for per-moon parent-frame queries.
DEFAULT_FRAME: str = "heliocentric_ecliptic"
SUPPORTED_FRAMES: Tuple[str, ...] = (
    "heliocentric_ecliptic",  # Sol-orbiting bodies, ecliptic-of-J2000 plane
    "parent_centric",         # moons centered on their parent body
)


# ──────────────────────────────────────────────────────────────────────
# Per-body kinematic state
# ──────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class KinematicState:
    """Mean orbital kinematic state for one body in a chosen frame.

    Circular-orbit approximation (v0.12.0 baseline). Eccentricity and
    inclination corrections are deferred to v0.12.x.

    Attributes
    ----------
    body, parent, frame
        Body identity, central body for Kepler's third law, frame name.
    mass_kg
        Body mass in kilograms.
    semi_major_axis_m
        Semi-major axis (= mean orbital radius) in metres.
    semi_major_axis_au
        Convenience: `semi_major_axis_m / AU_M`.
    orbital_velocity_m_s
        Mean orbital velocity in m/s (circular approximation).
    orbital_velocity_km_s
        Convenience: `orbital_velocity_m_s / 1000`.
    orbital_period_s
        Sidereal orbital period in seconds.
    orbital_period_days
        Sidereal orbital period in days (= `BODIES[body].period_days`).
    kinetic_energy_j
        `0.5 · m · v²` in joules.
    angular_momentum_kg_m2_s
        `|L| = m · v · r` for the circular orbit (perpendicular
        velocity assumption).
    angular_momentum_z_kg_m2_s
        Signed z-component of angular momentum. Positive for prograde
        orbits, negative for retrograde. v0.12.0 treats all bodies as
        prograde; sign-aware retrograde corrections (Triton, Phoebe,
        Venus rotation) ship as a v0.12.x refinement.
    """
    body:                       str
    parent:                     Optional[str]
    frame:                      str
    mass_kg:                    float
    semi_major_axis_m:          float
    semi_major_axis_au:         float
    orbital_velocity_m_s:       float
    orbital_velocity_km_s:      float
    orbital_period_s:           float
    orbital_period_days:        float
    kinetic_energy_j:           float
    angular_momentum_kg_m2_s:   float
    angular_momentum_z_kg_m2_s: float
    # If we couldn't compute (Sun has period 0; or unknown body),
    # `note` is set; otherwise None.
    note: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "body":                       self.body,
            "parent":                     self.parent,
            "frame":                      self.frame,
            "mass_kg":                    float(self.mass_kg),
            "semi_major_axis_m":          float(self.semi_major_axis_m),
            "semi_major_axis_au":         float(self.semi_major_axis_au),
            "orbital_velocity_m_s":       float(self.orbital_velocity_m_s),
            "orbital_velocity_km_s":      float(self.orbital_velocity_km_s),
            "orbital_period_s":           float(self.orbital_period_s),
            "orbital_period_days":        float(self.orbital_period_days),
            "kinetic_energy_j":           float(self.kinetic_energy_j),
            "angular_momentum_kg_m2_s":   float(self.angular_momentum_kg_m2_s),
            "angular_momentum_z_kg_m2_s": float(self.angular_momentum_z_kg_m2_s),
            **({"note": self.note} if self.note else {}),
        }


def _gm_for(body_key: str) -> float:
    """Gravitational parameter (m³/s²) of the named body."""
    if body_key == "sun":
        return GM_SUN
    if body_key not in BODIES:
        raise KeyError(f"unknown body {body_key!r}")
    return BODIES[body_key].mass_earth * GM_EARTH


def _mass_kg_for(body_key: str) -> float:
    """Body mass in kg."""
    if body_key == "sun":
        return SUN_MASS_KG
    return BODIES[body_key].mass_earth * EARTH_MASS_KG


def get_kinematic_state(
    body: str,
    *,
    jd_tdb: Optional[float] = None,
    frame: str = DEFAULT_FRAME,
) -> KinematicState:
    """Compute the mean orbital kinematic state for one body.

    Parameters
    ----------
    body : str
        A body key in `BODIES` (e.g. ``"mars"``, ``"luna"``, ``"sun"``).
    jd_tdb : float, optional
        Julian Date in TDB. v0.12.0 ignores this (uses mean orbital
        elements; no per-JD eccentricity correction); accepted for
        forward compatibility.
    frame : str, default ``"heliocentric_ecliptic"``
        Reference frame. Currently only `"heliocentric_ecliptic"` and
        `"parent_centric"` accepted; the latter is a no-op for v0.12.0
        since we report orbital elements relative to the parent body
        anyway, but the keyword is reserved for v0.12.x to switch to
        barycentric or J2000-ICRS frames.

    Returns
    -------
    KinematicState

    Raises
    ------
    KeyError
        If `body` isn't in BODIES.
    ValueError
        If `frame` isn't a supported value.
    """
    if body not in BODIES:
        raise KeyError(
            f"unknown body {body!r}; valid keys: {sorted(BODIES)}"
        )
    if frame not in SUPPORTED_FRAMES:
        raise ValueError(
            f"frame must be one of {list(SUPPORTED_FRAMES)}, got {frame!r}"
        )
    body_record = BODIES[body]
    parent = PARENT_OF.get(body)
    mass_kg = _mass_kg_for(body)
    if body_record.period_days <= 0.0:
        # Sun has period = 0 in the table — no Kepler computation possible.
        return KinematicState(
            body=body, parent=None, frame=frame,
            mass_kg=mass_kg,
            semi_major_axis_m=0.0, semi_major_axis_au=0.0,
            orbital_velocity_m_s=0.0, orbital_velocity_km_s=0.0,
            orbital_period_s=0.0, orbital_period_days=0.0,
            kinetic_energy_j=0.0,
            angular_momentum_kg_m2_s=0.0,
            angular_momentum_z_kg_m2_s=0.0,
            note=("Body has period_days = 0 in BODIES table; no Kepler "
                  "computation possible. The Sun's barycentric motion "
                  "is dominated by Sun-Jupiter wobble (~12 m/s peak), "
                  "two orders of magnitude below this approximation's "
                  "noise floor."),
        )
    gm_central = GM_SUN if parent is None else _gm_for(parent)
    t_s = body_record.period_days * DAY_S
    # Kepler's third law: T² = 4π²a³/GM_central → a = (GM·T²/4π²)^(1/3)
    a_m = (gm_central * t_s * t_s / (4.0 * math.pi * math.pi)) ** (1.0 / 3.0)
    # Circular orbit: v = sqrt(GM/a)
    v = math.sqrt(gm_central / a_m)
    ke = 0.5 * mass_kg * v * v
    # |L| = m · v · r for the circular orbit (v perpendicular to r)
    L_mag = mass_kg * v * a_m
    # Sign convention: prograde orbits have +z angular momentum (CCW
    # viewed from north pole). v0.12.0 treats all bodies as prograde;
    # sign-aware retrograde corrections (Triton, Phoebe, Venus rotation)
    # ship in v0.12.x.
    L_z = L_mag
    return KinematicState(
        body=body,
        parent=parent,
        frame=frame,
        mass_kg=mass_kg,
        semi_major_axis_m=a_m,
        semi_major_axis_au=a_m / AU_M,
        orbital_velocity_m_s=v,
        orbital_velocity_km_s=v / 1000.0,
        orbital_period_s=t_s,
        orbital_period_days=body_record.period_days,
        kinetic_energy_j=ke,
        angular_momentum_kg_m2_s=L_mag,
        angular_momentum_z_kg_m2_s=L_z,
        note=None,
    )


def get_full_system_state(
    *,
    jd_tdb: Optional[float] = None,
    frame: str = DEFAULT_FRAME,
) -> Dict[str, KinematicState]:
    """Compute kinematic state for every body in the 38-body roster.

    Returns a dict keyed by body name. Bodies that can't be computed
    (Sun, period=0) get a `KinematicState` with `note` set explaining
    why; callers should check for None before using the orbital fields.
    """
    if frame not in SUPPORTED_FRAMES:
        raise ValueError(
            f"frame must be one of {list(SUPPORTED_FRAMES)}, got {frame!r}"
        )
    return {
        body: get_kinematic_state(body, jd_tdb=jd_tdb, frame=frame)
        for body in BODIES
    }


__all__ = [
    "EARTH_MASS_KG",
    "SUN_MASS_KG",
    "AU_M",
    "DEFAULT_FRAME",
    "SUPPORTED_FRAMES",
    "KinematicState",
    "get_kinematic_state",
    "get_full_system_state",
]
