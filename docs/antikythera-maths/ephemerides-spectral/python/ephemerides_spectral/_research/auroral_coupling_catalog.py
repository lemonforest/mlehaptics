"""Sol Auroral Coupling Catalog — query surface for the v0.21.5
cross-channel coupling ship (magnetic ↔ atmosphere via aurorae).

Promotes the v0.21.5 architectural commitment from research notebook
§17.4.2 to a stable ship surface — the **fifth cross-channel coupling
surface**, second in the post-trio sequence after v0.21.4 interior ↔
rotation.

**Not a re-derivation.** Auroral-coupling values stored here are the
published imaging-campaign decompositions from cited papers; per-image
spectra remain in those papers. This catalog is the navigation layer.

Two bridge surfaces:

* :func:`compute_auroral_coupling` — per-body query.
* :func:`list_auroral_couplings` — full catalog enumeration.

Reference: research notebook §17.4.2.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .auroral_coupling_data import (
    ACCEL_COROTATION_ENFORCEMENT,
    ACCEL_MOON_FOOTPRINT,
    ACCEL_SOLAR_WIND_RECONNECTION,
    ACCEL_TILTED_DIPOLE_VARIABLE,
    AURORAL_COUPLINGS,
    AuroralCoupling,
    MORPH_ANNULAR_OVAL,
    MORPH_CIRCULAR_OVAL,
    MORPH_PARTIAL_OVAL,
    MORPH_PATCHY_TIME_VARIABLE,
    PRECISION_HIGH,
    PRECISION_LOW,
    PRECISION_MEDIUM,
    PRECISION_NONE,
    SOURCES,
)


# ---- Memoised lookups (built at module load) -------------------------

_BY_BODY: Dict[str, AuroralCoupling] = {m.body: m for m in AURORAL_COUPLINGS}
_ALL_BODIES: List[str] = sorted(_BY_BODY.keys())


def _to_dict(m: AuroralCoupling) -> Dict[str, Any]:
    return {
        "body": m.body,
        "auroral_morphology": m.auroral_morphology,
        "magnetic_origin_field": m.magnetic_origin_field,
        "dominant_acceleration_mechanism": m.dominant_acceleration_mechanism,
        "total_power_W": m.total_power_W,
        "observation_wavelengths": m.observation_wavelengths,
        "moon_footprint_observed": m.moon_footprint_observed,
        "precision_flag": m.precision_flag,
        "notes": m.notes,
        "source_key": m.source_key,
    }


def compute_auroral_coupling(
    body: Optional[str] = None,
) -> Dict[str, Any]:
    """Per-body magnetic ↔ atmosphere auroral-coupling summary.

    Aurorae are the visible signature of magnetic-field-line topology
    mapping into the upper atmosphere. The morphology of the auroral
    oval directly traces the underlying internal-field geometry:

    * **Circular oval** — dipole + small-quadrupole field (Earth,
      Jupiter, Ganymede).
    * **Annular oval** — axisymmetric field (Saturn — direct trace
      of Cao 2020 dipole tilt < 0.007°).
    * **Partial oval** — strongly tilted offset dipole (Uranus AH5).
    * **Patchy / time-variable** — multipole + tilt mixing (Neptune O8).

    Three families of acceleration mechanisms appear in the catalog:
    solar-wind reconnection (Earth, Saturn), corotation enforcement
    (Jupiter, Ganymede), tilted-dipole variability (Uranus, Neptune).

    **Not a re-derivation.** Values shipped are the published imaging-
    campaign decompositions from cited papers.

    6-body roster.

    Parameters
    ----------
    body : str, optional. Single-body lookup; else full roster.

    Returns
    -------
    dict
        Single body: ``{ok, body, coupling: {...}}``.
        Full roster: ``{ok, n_bodies, bodies: {name: {...}}}``.
    """
    if body is not None:
        name = str(body).lower().strip()
        if name not in _BY_BODY:
            return {
                "ok": False,
                "error": (
                    f"unknown body {body!r} in Sol Auroral Coupling "
                    f"Catalog; known bodies are {_ALL_BODIES}"
                ),
            }
        return {
            "ok": True,
            "body": name,
            "coupling": _to_dict(_BY_BODY[name]),
        }

    bodies: Dict[str, Dict[str, Any]] = {
        name: _to_dict(_BY_BODY[name]) for name in _ALL_BODIES
    }
    return {
        "ok": True,
        "n_bodies": len(_ALL_BODIES),
        "bodies": bodies,
    }


def list_auroral_couplings() -> Dict[str, Any]:
    """Full catalog enumeration of every published auroral-coupling
    summary."""
    return {
        "ok": True,
        "n_bodies": len(_ALL_BODIES),
        "n_sources": len(SOURCES),
        "bodies": list(_ALL_BODIES),
        "couplings": [_to_dict(m) for m in AURORAL_COUPLINGS],
    }


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "MORPH_CIRCULAR_OVAL",
    "MORPH_ANNULAR_OVAL",
    "MORPH_PARTIAL_OVAL",
    "MORPH_PATCHY_TIME_VARIABLE",
    "ACCEL_SOLAR_WIND_RECONNECTION",
    "ACCEL_COROTATION_ENFORCEMENT",
    "ACCEL_MOON_FOOTPRINT",
    "ACCEL_TILTED_DIPOLE_VARIABLE",
    "AURORAL_COUPLINGS",
    "SOURCES",
    "AuroralCoupling",
    "compute_auroral_coupling",
    "list_auroral_couplings",
]
