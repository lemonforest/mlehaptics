"""Sol Atmospheric Escape Catalog — query surface for the v0.21.7
cross-channel coupling ship (atmospheric escape ↔ magnetic-field
shielding).

Promotes the v0.21.7 architectural commitment from research notebook
§17.4.2 to a stable ship surface — the **seventh cross-channel coupling
surface**, fourth in the post-trio sequence.

**Not a re-derivation.** Escape rates stored here are the published
measurements / model fits from cited papers; this catalog is the
navigation layer.

Two bridge surfaces:

* :func:`compute_atmospheric_escape` — per-body query.
* :func:`list_atmospheric_escapes` — full catalog enumeration.

Reference: research notebook §17.4.2.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .atmospheric_escape_data import (
    ATMOSPHERIC_ESCAPES,
    AtmosphericEscape,
    ESC_HYDRODYNAMIC,
    ESC_PHOTOCHEMICAL,
    ESC_PICKUP_ION,
    ESC_SPUTTERING,
    ESC_THERMAL_JEANS,
    PRECISION_HIGH,
    PRECISION_LOW,
    PRECISION_MEDIUM,
    PRECISION_NONE,
    SOURCES,
)


# ---- Memoised lookups (built at module load) -------------------------

_BY_BODY: Dict[str, AtmosphericEscape] = {
    m.body: m for m in ATMOSPHERIC_ESCAPES
}
_ALL_BODIES: List[str] = sorted(_BY_BODY.keys())


def _to_dict(m: AtmosphericEscape) -> Dict[str, Any]:
    return {
        "body": m.body,
        "escape_rate_kg_per_s": m.escape_rate_kg_per_s,
        "dominant_escape_mechanism": m.dominant_escape_mechanism,
        "magnetic_shielding_present": m.magnetic_shielding_present,
        "dominant_escaping_species": m.dominant_escaping_species,
        "integrated_loss_4Gyr_kg": m.integrated_loss_4Gyr_kg,
        "precision_flag": m.precision_flag,
        "notes": m.notes,
        "source_key": m.source_key,
    }


def compute_atmospheric_escape(body: Optional[str] = None) -> Dict[str, Any]:
    """Per-body atmospheric escape ↔ magnetic-shielding constraint.

    Atmospheric escape rates depend critically on magnetic-field
    shielding: planets with strong intrinsic dipoles (Earth, Jupiter)
    deflect solar wind at the magnetopause, retaining atmospheres
    against pickup-ion erosion. Unmagnetised planets (Mars, Venus)
    are exposed to direct solar-wind interaction; over Gyr timescales
    this preferentially removes heavier species via pickup-ion escape.

    The cross-channel observation: **the v0.20.2 atmospheric inventory
    diverges by Gyr from the v0.20.1 magnetic-multipole inventory**.
    Mars + Venus diverge from terrestrial inventory because they
    cannot retain atmosphere against solar-wind erosion.

    **Mars-MAVEN headline**: Jakosky 2018 measured ~2 kg/s present-day
    pickup-ion escape; integrated 4-Gyr loss ~10¹⁸ kg = ~50% of
    primordial CO₂ atmosphere.

    **Not a re-derivation.** Values shipped are published measurements
    / model fits from cited papers.

    6-body roster.

    Parameters
    ----------
    body : str, optional. Single-body lookup; else full roster.

    Returns
    -------
    dict
        Single body: ``{ok, body, escape: {...}}``.
        Full roster: ``{ok, n_bodies, bodies: {name: {...}}}``.
    """
    if body is not None:
        name = str(body).lower().strip()
        if name not in _BY_BODY:
            return {
                "ok": False,
                "error": (
                    f"unknown body {body!r} in Sol Atmospheric Escape "
                    f"Catalog; known bodies are {_ALL_BODIES}"
                ),
            }
        return {
            "ok": True,
            "body": name,
            "escape": _to_dict(_BY_BODY[name]),
        }

    bodies: Dict[str, Dict[str, Any]] = {
        name: _to_dict(_BY_BODY[name]) for name in _ALL_BODIES
    }
    return {
        "ok": True,
        "n_bodies": len(_ALL_BODIES),
        "bodies": bodies,
    }


def list_atmospheric_escapes() -> Dict[str, Any]:
    """Full catalog enumeration of every published atmospheric-escape
    rate."""
    return {
        "ok": True,
        "n_bodies": len(_ALL_BODIES),
        "n_sources": len(SOURCES),
        "bodies": list(_ALL_BODIES),
        "escapes": [_to_dict(m) for m in ATMOSPHERIC_ESCAPES],
    }


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "ESC_THERMAL_JEANS",
    "ESC_HYDRODYNAMIC",
    "ESC_PICKUP_ION",
    "ESC_PHOTOCHEMICAL",
    "ESC_SPUTTERING",
    "ATMOSPHERIC_ESCAPES",
    "SOURCES",
    "AtmosphericEscape",
    "compute_atmospheric_escape",
    "list_atmospheric_escapes",
]
