"""Sol Rotational Constraint Catalog — query surface for the v0.21.4
cross-channel coupling ship (interior model ↔ rotation).

Promotes the v0.21.4 architectural commitment from research notebook
§17.4.2 to a stable ship surface — the **fourth cross-channel coupling
surface**, opening the post-trio sequence after v0.21.1-v0.21.3
shipped the trio explicitly named in §17.4.2.

**Not a re-derivation.** Constraint values stored here are the
published inversions from the cited papers; this catalog is the
navigation layer.

Two bridge surfaces:

* :func:`compute_rotational_constraint` — per-body query.
* :func:`list_rotational_constraints` — full catalog enumeration.

Reference: research notebook §17.4.2.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .rotational_constraint_data import (
    OBS_DEEP_ROTATION_REVISION,
    OBS_FREE_CORE_NUTATION,
    OBS_INSIGHT_NUTATION,
    OBS_RING_SEISMOLOGY,
    OBS_TIDAL_DISSIPATION_Q,
    OBS_ZONAL_WIND_DEPTH,
    PRECISION_HIGH,
    PRECISION_LOW,
    PRECISION_MEDIUM,
    PRECISION_NONE,
    ROTATIONAL_CONSTRAINTS,
    RotationalConstraint,
    SOURCES,
)


# ---- Memoised lookups (built at module load) -------------------------

_BY_BODY: Dict[str, RotationalConstraint] = {
    m.body: m for m in ROTATIONAL_CONSTRAINTS
}
_ALL_BODIES: List[str] = sorted(_BY_BODY.keys())


def _to_dict(m: RotationalConstraint) -> Dict[str, Any]:
    return {
        "body": m.body,
        "observation_type": m.observation_type,
        "constraint_value": m.constraint_value,
        "units": m.units,
        "surface_radius_km": m.surface_radius_km,
        "constrains_interior_property": m.constrains_interior_property,
        "precision_flag": m.precision_flag,
        "notes": m.notes,
        "source_key": m.source_key,
    }


def compute_rotational_constraint(
    body: Optional[str] = None,
) -> Dict[str, Any]:
    """Per-body interior ↔ rotation cross-channel constraint.

    For a body with a published interior model (v0.20.0
    ``INTERIOR_MODELS``), the constraint connects the interior
    structure (moment-of-inertia, core size, tidal viscosity) to
    observed rotational behaviour:

    * Earth — Mathews 2002 free-core-nutation period (430.21 days)
      constrains liquid outer-core / mantle boundary friction.
    * Mars — Le Maistre 2023 InSight RISE nutation gives core radius
      1830 ± 40 km, revising pre-InSight estimates downward.
    * Jupiter — Kaspi 2018 zonal-wind decomposition from Juno J6/J8/J10
      places wind base at ~3000 km depth (~4% of radius).
    * Saturn — Mankovich & Fuller 2021 ring-seismology revises rotation
      period from Voyager 10:39 → ring-seismology 10:33 (cloud-deck
      vs deep-interior distinction). The headline.
    * Io / Europa / Ganymede — Lainey 2009 / 2020 tidal Q from
      astrometric fits.

    Parameters
    ----------
    body : str, optional. Single-body lookup; else full roster.

    Returns
    -------
    dict
        Single body: ``{ok, body, constraint: {...}}``.
        Full roster: ``{ok, n_bodies, bodies: {name: {...}}}``.
    """
    if body is not None:
        name = str(body).lower().strip()
        if name not in _BY_BODY:
            return {
                "ok": False,
                "error": (
                    f"unknown body {body!r} in Sol Rotational "
                    f"Constraint Catalog; known bodies are {_ALL_BODIES}"
                ),
            }
        return {
            "ok": True,
            "body": name,
            "constraint": _to_dict(_BY_BODY[name]),
        }

    bodies: Dict[str, Dict[str, Any]] = {
        name: _to_dict(_BY_BODY[name]) for name in _ALL_BODIES
    }
    return {
        "ok": True,
        "n_bodies": len(_ALL_BODIES),
        "bodies": bodies,
    }


def list_rotational_constraints() -> Dict[str, Any]:
    """Full catalog enumeration of every published rotational constraint."""
    return {
        "ok": True,
        "n_bodies": len(_ALL_BODIES),
        "n_sources": len(SOURCES),
        "bodies": list(_ALL_BODIES),
        "constraints": [_to_dict(m) for m in ROTATIONAL_CONSTRAINTS],
    }


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "OBS_FREE_CORE_NUTATION",
    "OBS_RING_SEISMOLOGY",
    "OBS_INSIGHT_NUTATION",
    "OBS_TIDAL_DISSIPATION_Q",
    "OBS_DEEP_ROTATION_REVISION",
    "OBS_ZONAL_WIND_DEPTH",
    "ROTATIONAL_CONSTRAINTS",
    "SOURCES",
    "RotationalConstraint",
    "compute_rotational_constraint",
    "list_rotational_constraints",
]
