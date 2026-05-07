"""Sol Ballistic Trajectory Catalog — query surface for the v0.22.0
trajectory + sensing ship (Layer A: short-range ballistic propagation).

Promotes the v0.22.0 architectural commitment from research notebook
§17.5 to a stable ship surface — **Layer A** of the four-layer
trajectory + sensing surface (followed by Layer B ICBM, Layer C
sensor access + decoy discrimination).

Cross-channel reach: connects v0.20.2 climatology (atmosphere
composition, T, P) + v0.20.0 geodetic (g, R) into a single ballistic
propagator. Atmosphere parameters cross-reference the existing
v0.20.2 fluid_instrument; surface gravity cross-references v0.20.0
geodetic_catalog.

**Not a re-derivation.** Vacuum-case range/apex/ToF use the textbook
closed-form solutions (Vallado §8.6.2 / Curtis Ch. 12). With-drag
trajectories integrate the standard equations of motion under
exponential atmosphere (BC = m/(C_d·A) parameterization); the
ballistic-coefficient differential is the publishable physics that
closes the four-layer surface.

Three bridge surfaces:

* :func:`compute_ballistic_trajectory` — per-shot propagator (vacuum
  or with-drag).
* :func:`get_ballistic_atmosphere` — per-body atmosphere lookup.
* :func:`list_ballistic_atmospheres` — full catalog enumeration.

Reference: research notebook §17.5.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

from .ballistic_trajectory_data import (
    BALLISTIC_ATMOSPHERES,
    PRECISION_HIGH,
    PRECISION_LOW,
    PRECISION_MEDIUM,
    PRECISION_NONE,
    SOURCES,
    BallisticAtmosphere,
)


# ---- Memoised lookups (built at module load) -------------------------

_BY_BODY: Dict[str, BallisticAtmosphere] = {
    a.body: a for a in BALLISTIC_ATMOSPHERES
}
_ALL_BODIES: List[str] = sorted(_BY_BODY.keys())


def _atmos_to_dict(a: BallisticAtmosphere) -> Dict[str, Any]:
    return {
        "body": a.body,
        "surface_gravity_m_s2": a.surface_gravity_m_s2,
        "body_radius_km": a.body_radius_km,
        "rho_0_kg_m3": a.rho_0_kg_m3,
        "scale_height_m": a.scale_height_m,
        "atmosphere_top_km": a.atmosphere_top_km,
        "has_atmosphere": a.has_atmosphere,
        "precision_flag": a.precision_flag,
        "notes": a.notes,
        "source_key": a.source_key,
    }


# ---------------------------------------------------------------------------
# Vacuum closed-form (Vallado §8.6.2 / Curtis Ch. 12)
# ---------------------------------------------------------------------------


def _vacuum_trajectory(
    g: float,
    v_m_s: float,
    angle_deg: float,
    n_samples: int,
) -> Dict[str, Any]:
    """Closed-form vacuum ballistic trajectory (flat target).

    range = v² · sin(2θ) / g
    apex  = v² · sin²(θ) / (2g)
    T     = 2 v · sin(θ) / g
    """
    theta = math.radians(angle_deg)
    s, c = math.sin(theta), math.cos(theta)

    range_m = (v_m_s * v_m_s) * math.sin(2 * theta) / g
    apex_m = (v_m_s * v_m_s) * (s * s) / (2.0 * g)
    tof_s = 2.0 * v_m_s * s / g

    samples: List[Tuple[float, float, float, float, float]] = []
    if n_samples > 1:
        for i in range(n_samples):
            t = tof_s * i / (n_samples - 1)
            x = v_m_s * c * t
            y = v_m_s * s * t - 0.5 * g * t * t
            vx = v_m_s * c
            vy = v_m_s * s - g * t
            samples.append((t, x, y, vx, vy))

    return {
        "range_m": range_m,
        "peak_altitude_m": apex_m,
        "time_of_flight_s": tof_s,
        "impact_velocity_m_s": v_m_s,  # vacuum: |v| conserved
        "impact_angle_deg": angle_deg,
        "n_samples": len(samples),
        "samples": samples,
        "with_drag": False,
    }


# ---------------------------------------------------------------------------
# With-drag RK4 (exponential atmosphere)
# ---------------------------------------------------------------------------


def _drag_accel(
    vx: float,
    vy: float,
    y: float,
    g: float,
    rho_0: float,
    H: float,
    bc: float,
) -> Tuple[float, float]:
    """Compute (ax, ay) under gravity + exponential-atmosphere drag.

    ρ(h) = ρ₀ · exp(-h / H)
    a_drag = -½ · ρ · v · (v / BC)  (vector form: -½ρv²/BC · v̂)

    BC = m / (C_d · A), kg/m².
    """
    rho = rho_0 * math.exp(-max(y, 0.0) / H) if H > 0.0 else 0.0
    speed = math.sqrt(vx * vx + vy * vy)
    if speed < 1e-12:
        return 0.0, -g
    drag_factor = 0.5 * rho * speed / bc
    ax = -drag_factor * vx
    ay = -g - drag_factor * vy
    return ax, ay


def _drag_trajectory(
    g: float,
    rho_0: float,
    H: float,
    bc: float,
    v_m_s: float,
    angle_deg: float,
    altitude_m: float,
    dt_s: float,
    max_steps: int,
) -> Dict[str, Any]:
    """RK4-integrated trajectory under exponential atmosphere drag.

    State: (x, y, vx, vy). Stops when y crosses zero from above OR
    max_steps reached.
    """
    theta = math.radians(angle_deg)
    x, y = 0.0, max(altitude_m, 0.0)
    vx = v_m_s * math.cos(theta)
    vy = v_m_s * math.sin(theta)

    samples: List[Tuple[float, float, float, float, float]] = [
        (0.0, x, y, vx, vy)
    ]
    peak_y = y
    t = 0.0
    impact_velocity = v_m_s

    for _ in range(max_steps):
        # RK4 step
        ax1, ay1 = _drag_accel(vx, vy, y, g, rho_0, H, bc)
        kx1, ky1 = vx, vy
        kvx1, kvy1 = ax1, ay1

        ax2, ay2 = _drag_accel(
            vx + 0.5 * dt_s * kvx1,
            vy + 0.5 * dt_s * kvy1,
            y + 0.5 * dt_s * ky1,
            g, rho_0, H, bc,
        )
        kx2, ky2 = vx + 0.5 * dt_s * kvx1, vy + 0.5 * dt_s * kvy1
        kvx2, kvy2 = ax2, ay2

        ax3, ay3 = _drag_accel(
            vx + 0.5 * dt_s * kvx2,
            vy + 0.5 * dt_s * kvy2,
            y + 0.5 * dt_s * ky2,
            g, rho_0, H, bc,
        )
        kx3, ky3 = vx + 0.5 * dt_s * kvx2, vy + 0.5 * dt_s * kvy2
        kvx3, kvy3 = ax3, ay3

        ax4, ay4 = _drag_accel(
            vx + dt_s * kvx3,
            vy + dt_s * kvy3,
            y + dt_s * ky3,
            g, rho_0, H, bc,
        )
        kx4, ky4 = vx + dt_s * kvx3, vy + dt_s * kvy3
        kvx4, kvy4 = ax4, ay4

        x_new = x + (dt_s / 6.0) * (kx1 + 2 * kx2 + 2 * kx3 + kx4)
        y_new = y + (dt_s / 6.0) * (ky1 + 2 * ky2 + 2 * ky3 + ky4)
        vx_new = vx + (dt_s / 6.0) * (kvx1 + 2 * kvx2 + 2 * kvx3 + kvx4)
        vy_new = vy + (dt_s / 6.0) * (kvy1 + 2 * kvy2 + 2 * kvy3 + kvy4)
        t_new = t + dt_s

        # Impact detection: y crosses zero from above. Linear-
        # interpolate the precise impact moment.
        if y_new <= 0.0 and y > 0.0:
            frac = y / (y - y_new) if (y - y_new) != 0.0 else 0.0
            x = x + frac * (x_new - x)
            y = 0.0
            vx = vx + frac * (vx_new - vx)
            vy = vy + frac * (vy_new - vy)
            t = t + frac * dt_s
            impact_velocity = math.sqrt(vx * vx + vy * vy)
            samples.append((t, x, y, vx, vy))
            break

        x, y, vx, vy, t = x_new, y_new, vx_new, vy_new, t_new
        if y > peak_y:
            peak_y = y
        samples.append((t, x, y, vx, vy))
    else:
        # max_steps hit without impact
        impact_velocity = math.sqrt(vx * vx + vy * vy)

    impact_angle_rad = math.atan2(-vy, vx) if vx != 0.0 else math.pi / 2
    impact_angle_deg = math.degrees(impact_angle_rad)

    return {
        "range_m": x,
        "peak_altitude_m": peak_y,
        "time_of_flight_s": t,
        "impact_velocity_m_s": impact_velocity,
        "impact_angle_deg": impact_angle_deg,
        "n_samples": len(samples),
        "samples": samples,
        "with_drag": True,
    }


# ---------------------------------------------------------------------------
# Public bridge surfaces
# ---------------------------------------------------------------------------


def compute_ballistic_trajectory(
    body: str,
    v_m_s: float,
    angle_deg: float,
    altitude_m: float = 0.0,
    with_drag: bool = False,
    ballistic_coefficient: Optional[float] = None,
    dt_s: float = 0.5,
    max_steps: int = 100000,
    n_vacuum_samples: int = 33,
) -> Dict[str, Any]:
    """Per-body short-range ballistic-projectile propagator.

    Vacuum case (``with_drag=False``) is the textbook closed-form
    solution (Vallado §8.6.2):

        range = v² · sin(2θ) / g
        apex  = v² · sin²(θ) / (2g)
        T     = 2 v · sin(θ) / g

    With-drag case (``with_drag=True``) integrates the standard
    equations of motion under exponential atmosphere
    (ρ(h) = ρ₀ · exp(-h/H)) using RK4. Drag force is parameterized
    by the ballistic coefficient BC = m / (C_d · A) (kg/m²).

    For airless bodies (luna, mercury), ``with_drag`` is silently
    forced to ``False``.

    Parameters
    ----------
    body : str
        Lower-case body name (terra, mars, venus, titan, luna,
        mercury, jupiter).
    v_m_s : float
        Initial speed (m/s).
    angle_deg : float
        Launch angle above local horizontal (degrees).
    altitude_m : float, default 0.0
        Initial altitude above surface (m). Vacuum case ignores.
    with_drag : bool, default False
        Whether to include atmospheric drag.
    ballistic_coefficient : float, optional
        BC = m/(C_d·A) (kg/m²). Required when ``with_drag=True``.
        Typical values: rifle bullet 50-200, artillery shell 1500,
        ICBM RV 5000-15000, unguided decoy 10-50.
    dt_s : float, default 0.5
        RK4 timestep (seconds). Smaller → more accurate, slower.
    max_steps : int, default 100000
        Maximum RK4 steps before truncation.
    n_vacuum_samples : int, default 33
        Number of trajectory samples in vacuum mode.

    Returns
    -------
    dict
        ``{ok, body, atmosphere, trajectory: {range_m, peak_altitude_m,
        time_of_flight_s, impact_velocity_m_s, impact_angle_deg,
        n_samples, samples, with_drag}}``.

    References
    ----------
    Vallado D. A. (2013). *Fundamentals of Astrodynamics and
    Applications*, 4th ed., §8.6.2.

    Curtis H. D. (2014). *Orbital Mechanics for Engineering
    Students*, 3rd ed., Ch. 12.

    Tewari A. (2011). *Atmospheric and Space Flight Dynamics*,
    Birkhäuser (body-parameterized atmospheres).
    """
    if v_m_s <= 0.0:
        return {"ok": False, "error": f"v_m_s must be positive; got {v_m_s}"}
    if not (0.0 < angle_deg < 90.0):
        return {
            "ok": False,
            "error": f"angle_deg must be in (0, 90); got {angle_deg}",
        }

    name = str(body).lower().strip()
    if name not in _BY_BODY:
        return {
            "ok": False,
            "error": (
                f"unknown body {body!r}; known bodies are {_ALL_BODIES}"
            ),
        }
    atmos = _BY_BODY[name]
    g = atmos.surface_gravity_m_s2

    use_drag = with_drag and atmos.has_atmosphere
    if use_drag:
        if ballistic_coefficient is None or ballistic_coefficient <= 0.0:
            return {
                "ok": False,
                "error": (
                    "ballistic_coefficient (kg/m²) is required when "
                    "with_drag=True"
                ),
            }
        traj = _drag_trajectory(
            g=g,
            rho_0=atmos.rho_0_kg_m3,
            H=atmos.scale_height_m,
            bc=ballistic_coefficient,
            v_m_s=v_m_s,
            angle_deg=angle_deg,
            altitude_m=altitude_m,
            dt_s=dt_s,
            max_steps=max_steps,
        )
    else:
        traj = _vacuum_trajectory(
            g=g,
            v_m_s=v_m_s,
            angle_deg=angle_deg,
            n_samples=n_vacuum_samples,
        )

    return {
        "ok": True,
        "body": name,
        "atmosphere": _atmos_to_dict(atmos),
        "trajectory": traj,
    }


def get_ballistic_atmosphere(body: Optional[str] = None) -> Dict[str, Any]:
    """Per-body ballistic-atmosphere lookup.

    Parameters
    ----------
    body : str, optional. Single-body lookup; else full roster.

    Returns
    -------
    dict
        Single body: ``{ok, body, atmosphere: {...}}``.
        Full roster: ``{ok, n_bodies, atmospheres: {name: {...}}}``.
    """
    if body is not None:
        name = str(body).lower().strip()
        if name not in _BY_BODY:
            return {
                "ok": False,
                "error": (
                    f"unknown body {body!r} in Sol Ballistic Atmosphere "
                    f"Catalog; known bodies are {_ALL_BODIES}"
                ),
            }
        return {
            "ok": True,
            "body": name,
            "atmosphere": _atmos_to_dict(_BY_BODY[name]),
        }

    return {
        "ok": True,
        "n_bodies": len(_ALL_BODIES),
        "atmospheres": {
            name: _atmos_to_dict(_BY_BODY[name]) for name in _ALL_BODIES
        },
    }


def list_ballistic_atmospheres() -> Dict[str, Any]:
    """Full catalog enumeration of every per-body ballistic-atmosphere
    record."""
    return {
        "ok": True,
        "n_bodies": len(_ALL_BODIES),
        "n_sources": len(SOURCES),
        "bodies": list(_ALL_BODIES),
        "atmospheres": [_atmos_to_dict(a) for a in BALLISTIC_ATMOSPHERES],
    }


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "BALLISTIC_ATMOSPHERES",
    "SOURCES",
    "BallisticAtmosphere",
    "compute_ballistic_trajectory",
    "get_ballistic_atmosphere",
    "list_ballistic_atmospheres",
]
