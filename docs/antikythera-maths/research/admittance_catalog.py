"""Sol Topography-Gravity Admittance Catalog — query surface for the
v0.21.1 cross-channel coupling ship.

Promotes the v0.21.1 architectural commitment from research notebook
§17.4.2 to a stable ship surface — the **first cross-channel coupling
surface** in the v0.21.x sequence (per §17.4.2: "v0.21.1+ Cross-channel
coupling surfaces, one per minor version: topography ↔ gravity
admittance, magnetic-multipole-derived dynamo constraints, orographic
forcing of atmospheric standing waves").

**Not a re-derivation.** The Z(n) values stored here are the published
integrated admittance summaries from the cited papers. Per-degree
spectra remain in those papers' supplementary materials; this catalog
is the navigation layer.

Two bridge surfaces shape consumer access:

* :func:`compute_topography_gravity_admittance` — per-body admittance
  query (or full-roster query if body is omitted).
* :func:`list_admittance_spectra` — full catalog enumeration.

The data tables are in :mod:`admittance_catalog_data`. Citations live
in its `SOURCES` dict; every numeric value carries a `source_key`
pointing into that dict.

Reference: research notebook §17.4.2 (the cross-channel coupling
sequence) and §17.2 (the spectral admittance physics).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .admittance_catalog_data import (
    ADMITTANCE_SPECTRA,
    AdmittanceSpectrum,
    PRECISION_HIGH,
    PRECISION_LOW,
    PRECISION_MEDIUM,
    PRECISION_NONE,
    SOURCES,
)


# ---- Memoised lookups (built at module load) --------------------------------

_BY_BODY: Dict[str, AdmittanceSpectrum] = {m.body: m for m in ADMITTANCE_SPECTRA}
_ALL_BODIES: List[str] = sorted(_BY_BODY.keys())


def _to_dict(m: AdmittanceSpectrum) -> Dict[str, Any]:
    return {
        "body": m.body,
        "degree_min": m.degree_min,
        "degree_max": m.degree_max,
        "mean_admittance_mGal_per_km": m.mean_admittance_mGal_per_km,
        "inferred_crustal_density_kg_per_m3": m.inferred_crustal_density_kg_per_m3,
        "inferred_crustal_thickness_km": m.inferred_crustal_thickness_km,
        "isostatic_model": m.isostatic_model,
        "reference_radius_km": m.reference_radius_km,
        "full_admittance_archive": m.full_admittance_archive,
        "precision_flag": m.precision_flag,
        "notes": m.notes,
        "source_key": m.source_key,
    }


def compute_topography_gravity_admittance(
    body: Optional[str] = None,
) -> Dict[str, Any]:
    """Return per-body topography-gravity admittance summary.

    For a body with both a published gravity multipole expansion (from
    v0.20.0 :mod:`geodetic_catalog_data`) and a topography model, the
    spectral admittance Z(n) constrains crustal density and crustal
    thickness via isostatic compensation theory.

    This surface returns the *integrated* Z summary published in the
    refereed literature (mean Z over the fitted degree range, plus
    inferred crustal density + crustal thickness if reported), not a
    re-derivation. Per-degree Z(n) tables remain in the cited paper's
    supplementary materials.

    Parameters
    ----------
    body : str, optional. If given, return just that body's record.
        If omitted, return the full per-body catalog.

    Returns
    -------
    dict
        Single body (`body=name`):
            ``{"ok": True, "body": str, "spectrum": {...}}``
        Full roster (`body=None`):
            ``{"ok": True, "n_bodies": int, "bodies": {name: {...}}}``
        On error:
            ``{"ok": False, "error": "..."}``
    """
    if body is not None:
        name = str(body).lower().strip()
        if name not in _BY_BODY:
            return {
                "ok": False,
                "error": (
                    f"unknown body {body!r} in Sol Admittance Catalog; "
                    f"known bodies are {_ALL_BODIES}"
                ),
            }
        return {
            "ok": True,
            "body": name,
            "spectrum": _to_dict(_BY_BODY[name]),
        }

    bodies: Dict[str, Dict[str, Any]] = {
        name: _to_dict(_BY_BODY[name]) for name in _ALL_BODIES
    }
    return {
        "ok": True,
        "n_bodies": len(_ALL_BODIES),
        "bodies": bodies,
    }


def list_admittance_spectra() -> Dict[str, Any]:
    """Full catalog enumeration of every published admittance spectrum.

    Returns every body's `AdmittanceSpectrum` record + the citation
    dict so consumers can verify the provenance of every Z(n) value.
    """
    return {
        "ok": True,
        "n_bodies": len(_ALL_BODIES),
        "n_sources": len(SOURCES),
        "bodies": list(_ALL_BODIES),
        "spectra": [_to_dict(m) for m in ADMITTANCE_SPECTRA],
    }


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "ADMITTANCE_SPECTRA",
    "SOURCES",
    "AdmittanceSpectrum",
    "compute_topography_gravity_admittance",
    "list_admittance_spectra",
]
