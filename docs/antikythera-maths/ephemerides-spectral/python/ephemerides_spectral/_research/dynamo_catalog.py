"""Sol Dynamo Region Catalog — query surface for the v0.21.2
cross-channel coupling ship.

Promotes the v0.21.2 architectural commitment from research notebook
§17.4.2 to a stable ship surface — the **second cross-channel coupling
surface** in the v0.21.x sequence (per §17.4.2: "v0.21.1+ Cross-channel
coupling surfaces, one per minor version: topography ↔ gravity
admittance [v0.21.1], magnetic-multipole-derived dynamo constraints
[v0.21.2], orographic forcing of atmospheric standing waves [v0.21.3]").

**Not a re-derivation.** The dynamo-radius values stored here are the
published inversions from the cited papers. Per-degree Lowes-
Mauersberger spectrum tables remain in those papers; this catalog is
the navigation layer.

Two bridge surfaces:

* :func:`compute_dynamo_region` — per-body dynamo-region query.
* :func:`list_dynamo_regions` — full catalog enumeration.

The data tables are in :mod:`dynamo_catalog_data`. Citations live in
its `SOURCES` dict; every numeric value carries a `source_key` pointing
into that dict.

Reference: research notebook §17.4.2 (the cross-channel coupling
sequence).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .dynamo_catalog_data import (
    DYNAMO_REGIONS,
    DynamoRegion,
    PRECISION_HIGH,
    PRECISION_LOW,
    PRECISION_MEDIUM,
    PRECISION_NONE,
    SOURCES,
)


# ---- Memoised lookups (built at module load) -------------------------

_BY_BODY: Dict[str, DynamoRegion] = {m.body: m for m in DYNAMO_REGIONS}
_ALL_BODIES: List[str] = sorted(_BY_BODY.keys())


def _to_dict(m: DynamoRegion) -> Dict[str, Any]:
    return {
        "body": m.body,
        "dynamo_radius_fraction": m.dynamo_radius_fraction,
        "dynamo_radius_km": m.dynamo_radius_km,
        "surface_radius_km": m.surface_radius_km,
        "dynamo_pressure_GPa": m.dynamo_pressure_GPa,
        "conductivity_S_per_m": m.conductivity_S_per_m,
        "conducting_material": m.conducting_material,
        "lowes_mauersberger_decay": m.lowes_mauersberger_decay,
        "precision_flag": m.precision_flag,
        "notes": m.notes,
        "source_key": m.source_key,
    }


def compute_dynamo_region(
    body: Optional[str] = None,
) -> Dict[str, Any]:
    """Return per-body magnetic-multipole-derived dynamo-region constraint.

    For a body with a published spherical-harmonic magnetic-field
    expansion (v0.20.1 ``MAGNETIC_MULTIPOLE_MODELS``), the Lowes-
    Mauersberger spectrum's log-slope inverts directly for the dynamo
    radius:

        R(n) ∝ (R_dynamo / R_surface)^(2n + 4)

    For Earth this gives the canonical CMB depth at 2891 km, matching
    seismology to better than 1%. For the giants (Jupiter, Saturn) it
    gives deep metallic-H dynamos. For Mercury, standard Lowes-
    Mauersberger fails because of stable stratification; the depth
    comes from the Christensen 2006 weak-field model. For Ganymede,
    only the dipole is published (max_degree=1), so the depth comes
    from Schubert 1996 thermal-evolution models.

    Parameters
    ----------
    body : str, optional. If given, return that body's record;
        else return the full per-body catalog.

    Returns
    -------
    dict
        Single body: ``{ok, body, region: {...}}``.
        Full roster: ``{ok, n_bodies, bodies: {name: {...}}}``.
    """
    if body is not None:
        name = str(body).lower().strip()
        if name not in _BY_BODY:
            return {
                "ok": False,
                "error": (
                    f"unknown body {body!r} in Sol Dynamo Catalog; "
                    f"known bodies are {_ALL_BODIES}"
                ),
            }
        return {
            "ok": True,
            "body": name,
            "region": _to_dict(_BY_BODY[name]),
        }

    bodies: Dict[str, Dict[str, Any]] = {
        name: _to_dict(_BY_BODY[name]) for name in _ALL_BODIES
    }
    return {
        "ok": True,
        "n_bodies": len(_ALL_BODIES),
        "bodies": bodies,
    }


def list_dynamo_regions() -> Dict[str, Any]:
    """Full catalog enumeration of every published dynamo-region
    constraint."""
    return {
        "ok": True,
        "n_bodies": len(_ALL_BODIES),
        "n_sources": len(SOURCES),
        "bodies": list(_ALL_BODIES),
        "regions": [_to_dict(m) for m in DYNAMO_REGIONS],
    }


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "DYNAMO_REGIONS",
    "SOURCES",
    "DynamoRegion",
    "compute_dynamo_region",
    "list_dynamo_regions",
]
