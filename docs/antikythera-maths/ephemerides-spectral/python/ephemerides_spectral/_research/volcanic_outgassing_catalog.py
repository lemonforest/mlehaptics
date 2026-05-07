"""Sol Volcanic Outgassing Catalog — query surface for the v0.21.9
cross-channel coupling ship (volcanic outgassing ↔ atmospheric
composition).

Promotes the v0.21.9 architectural commitment from research notebook
§17.4.2 to a stable ship surface — the **ninth cross-channel coupling
surface**, sixth in the post-trio sequence.

Cross-channel reach: forms the **supply-side** of the atmospheric
mass-balance equation, with v0.21.7 atmospheric escape as the
**demand-side**. v0.21.8 heat flow provides the energy budget that
drives outgassing in the first place.

**Not a re-derivation.** Outgassing rates stored here are the
published measurements / model fits from cited papers.

Two bridge surfaces:

* :func:`compute_volcanic_outgassing` — per-body query.
* :func:`list_volcanic_outgassings` — full catalog enumeration.

Reference: research notebook §17.4.2.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .volcanic_outgassing_data import (
    PRECISION_HIGH,
    PRECISION_LOW,
    PRECISION_MEDIUM,
    PRECISION_NONE,
    SOURCES,
    SRC_DORMANT,
    SRC_MAGNETOSPHERIC_INJECTION,
    SRC_PLUME_VENTING,
    SRC_SUBAERIAL_VOLCANISM,
    SRC_SUBMARINE_VOLCANISM,
    SRC_TIDAL_VOLCANISM,
    VOLCANIC_OUTGASSINGS,
    VolcanicOutgassing,
)


# ---- Memoised lookups (built at module load) -------------------------

_BY_BODY: Dict[str, VolcanicOutgassing] = {
    m.body: m for m in VOLCANIC_OUTGASSINGS
}
_ALL_BODIES: List[str] = sorted(_BY_BODY.keys())


def _to_dict(m: VolcanicOutgassing) -> Dict[str, Any]:
    return {
        "body": m.body,
        "outgassing_rate_kg_per_s": m.outgassing_rate_kg_per_s,
        "dominant_outgassed_species": m.dominant_outgassed_species,
        "source_mechanism": m.source_mechanism,
        "is_active": m.is_active,
        "balance_with_escape_kg_per_s": m.balance_with_escape_kg_per_s,
        "precision_flag": m.precision_flag,
        "notes": m.notes,
        "source_key": m.source_key,
    }


def compute_volcanic_outgassing(
    body: Optional[str] = None,
) -> Dict[str, Any]:
    """Per-body volcanic-outgassing ↔ atmospheric-composition coupling.

    Volcanic outgassing rate sets atmospheric-inventory dynamics
    through steady-state mass balance: outgassing rate (SOURCE) =
    escape rate (SINK from v0.21.7) + sequestration rate (frost,
    weathering, ocean dissolution).

    The cross-channel observation: **v0.21.7 escape + v0.21.9
    outgassing form the supply-and-demand sides of atmospheric mass
    balance**. v0.21.8 heat flow provides the energy budget that
    drives outgassing in the first place.

    **Io headline**: 1 ton/s SO₂ outgassing from tidal-driven
    volcanism (cross-references v0.21.8 100 TW heating); SO₂ is
    injected into Jupiter's Io plasma torus at ~1 ton/s — matching
    v0.21.7's 1000 kg/s Jupiter pickup-ion escape rate downstream.

    **Not a re-derivation.** Values shipped are published
    measurements / model fits from cited papers.

    6-body roster.

    Parameters
    ----------
    body : str, optional. Single-body lookup; else full roster.

    Returns
    -------
    dict
        Single body: ``{ok, body, outgassing: {...}}``.
        Full roster: ``{ok, n_bodies, bodies: {name: {...}}}``.
    """
    if body is not None:
        name = str(body).lower().strip()
        if name not in _BY_BODY:
            return {
                "ok": False,
                "error": (
                    f"unknown body {body!r} in Sol Volcanic Outgassing "
                    f"Catalog; known bodies are {_ALL_BODIES}"
                ),
            }
        return {
            "ok": True,
            "body": name,
            "outgassing": _to_dict(_BY_BODY[name]),
        }

    bodies: Dict[str, Dict[str, Any]] = {
        name: _to_dict(_BY_BODY[name]) for name in _ALL_BODIES
    }
    return {
        "ok": True,
        "n_bodies": len(_ALL_BODIES),
        "bodies": bodies,
    }


def list_volcanic_outgassings() -> Dict[str, Any]:
    """Full catalog enumeration of every published outgassing rate."""
    return {
        "ok": True,
        "n_bodies": len(_ALL_BODIES),
        "n_sources": len(SOURCES),
        "bodies": list(_ALL_BODIES),
        "outgassings": [_to_dict(m) for m in VOLCANIC_OUTGASSINGS],
    }


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "SRC_SUBAERIAL_VOLCANISM",
    "SRC_SUBMARINE_VOLCANISM",
    "SRC_TIDAL_VOLCANISM",
    "SRC_PLUME_VENTING",
    "SRC_MAGNETOSPHERIC_INJECTION",
    "SRC_DORMANT",
    "VOLCANIC_OUTGASSINGS",
    "SOURCES",
    "VolcanicOutgassing",
    "compute_volcanic_outgassing",
    "list_volcanic_outgassings",
]
