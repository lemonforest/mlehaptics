"""Sol Orographic Forcing Catalog — query surface for the v0.21.3
cross-channel coupling ship (topography → atmospheric standing waves).

Promotes the v0.21.3 architectural commitment from research notebook
§17.4.2 to a stable ship surface — the **third cross-channel coupling
surface** in the v0.21.x sequence (per §17.4.2: topography ↔ gravity
admittance [v0.21.1], magnetic-multipole-derived dynamo constraints
[v0.21.2], orographic forcing of atmospheric standing waves [v0.21.3]).

**Not a re-derivation.** The standing-wave decompositions stored here
are the published GCM-derived summaries from the cited papers; this
catalog is the navigation layer.

Two bridge surfaces:

* :func:`compute_orographic_forcing` — per-body forcing query.
* :func:`list_orographic_forcings` — full catalog enumeration.

The data tables are in :mod:`orographic_forcing_data`.

Reference: research notebook §17.4.2 (the cross-channel coupling
sequence).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .orographic_forcing_data import (
    OROGRAPHIC_FORCINGS,
    OrographicForcing,
    PRECISION_HIGH,
    PRECISION_LOW,
    PRECISION_MEDIUM,
    PRECISION_NONE,
    SOURCES,
)


# ---- Memoised lookups (built at module load) -------------------------

_BY_BODY: Dict[str, OrographicForcing] = {m.body: m for m in OROGRAPHIC_FORCINGS}
_ALL_BODIES: List[str] = sorted(_BY_BODY.keys())


def _to_dict(m: OrographicForcing) -> Dict[str, Any]:
    return {
        "body": m.body,
        "dominant_orographic_feature_name": m.dominant_orographic_feature_name,
        "feature_height_km": m.feature_height_km,
        "feature_width_km": m.feature_width_km,
        "dominant_zonal_wavenumber": m.dominant_zonal_wavenumber,
        "forcing_amplitude_relative": m.forcing_amplitude_relative,
        "is_stationary_wave_observed": m.is_stationary_wave_observed,
        "standing_wave_layer": m.standing_wave_layer,
        "precision_flag": m.precision_flag,
        "notes": m.notes,
        "source_key": m.source_key,
    }


def compute_orographic_forcing(
    body: Optional[str] = None,
) -> Dict[str, Any]:
    """Return per-body orographic-forcing summary.

    For a body with both a topography model (v0.20.0
    TOPOGRAPHY_MODELS) AND an atmosphere (v0.20.2 BODY_CLIMATOLOGY
    with `has_atmosphere=True`), surface topography acts as a lower-
    boundary forcing on the global circulation. The forcing
    generates downstream stationary Rossby waves (planetary waves
    with zero phase speed in the body-rotating frame).

    This is an **emerging research area** — published quantitative
    GCM-derived stationary-wave decompositions exist for terra
    (Hoskins & Karoly 1981 / Held 2002 reviews), mars (Hollingsworth
    1997 + MGS observations), venus (Lebonnois 2010 GCM), and titan
    (Charnay & Lebonnois 2012 GCM). 4-body roster total.

    Bodies in super-rotation regimes (venus, titan) suppress classic
    stationary-wave physics; these entries carry LOW precision flags
    and `is_stationary_wave_observed=False`.

    Parameters
    ----------
    body : str, optional. If given, return that body's record;
        else return the full per-body catalog.

    Returns
    -------
    dict
        Single body: ``{ok, body, forcing: {...}}``.
        Full roster: ``{ok, n_bodies, bodies: {name: {...}}}``.
    """
    if body is not None:
        name = str(body).lower().strip()
        if name not in _BY_BODY:
            return {
                "ok": False,
                "error": (
                    f"unknown body {body!r} in Sol Orographic Forcing "
                    f"Catalog; known bodies are {_ALL_BODIES}"
                ),
            }
        return {
            "ok": True,
            "body": name,
            "forcing": _to_dict(_BY_BODY[name]),
        }

    bodies: Dict[str, Dict[str, Any]] = {
        name: _to_dict(_BY_BODY[name]) for name in _ALL_BODIES
    }
    return {
        "ok": True,
        "n_bodies": len(_ALL_BODIES),
        "bodies": bodies,
    }


def list_orographic_forcings() -> Dict[str, Any]:
    """Full catalog enumeration of every published orographic-forcing
    decomposition."""
    return {
        "ok": True,
        "n_bodies": len(_ALL_BODIES),
        "n_sources": len(SOURCES),
        "bodies": list(_ALL_BODIES),
        "forcings": [_to_dict(m) for m in OROGRAPHIC_FORCINGS],
    }


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "OROGRAPHIC_FORCINGS",
    "SOURCES",
    "OrographicForcing",
    "compute_orographic_forcing",
    "list_orographic_forcings",
]
