"""Sol Heat Flow Catalog — query surface for the v0.21.8 cross-channel
coupling ship (heat flow ↔ tidal heating).

Promotes the v0.21.8 architectural commitment from research notebook
§17.4.2 to a stable ship surface — the **eighth cross-channel coupling
surface**, fifth in the post-trio sequence.

Cross-channel reach: combines with v0.21.4 (tidal-Q) + v0.21.6 (orbital
migration) to **close the tidal-energy-budget loop**. For Io, the
v0.21.4 Q ≈ 80 + v0.21.6 +3.6 cm/yr outward migration must match the
v0.21.8 observed surface heat flow ~100 TW (and they do).

**Not a re-derivation.** Heat-flow values stored here are the published
measurements / energy-budget models from cited papers.

Two bridge surfaces:

* :func:`compute_heat_flow` — per-body query.
* :func:`list_heat_flows` — full catalog enumeration.

Reference: research notebook §17.4.2.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .heat_flow_data import (
    HEAT_FLOWS,
    HeatFlow,
    PRECISION_HIGH,
    PRECISION_LOW,
    PRECISION_MEDIUM,
    PRECISION_NONE,
    SOURCES,
)


# ---- Memoised lookups (built at module load) -------------------------

_BY_BODY: Dict[str, HeatFlow] = {m.body: m for m in HEAT_FLOWS}
_ALL_BODIES: List[str] = sorted(_BY_BODY.keys())


def _to_dict(m: HeatFlow) -> Dict[str, Any]:
    return {
        "body": m.body,
        "total_heat_flow_TW": m.total_heat_flow_TW,
        "tidal_fraction": m.tidal_fraction,
        "radiogenic_fraction": m.radiogenic_fraction,
        "primordial_fraction": m.primordial_fraction,
        "observation_method": m.observation_method,
        "precision_flag": m.precision_flag,
        "notes": m.notes,
        "source_key": m.source_key,
    }


def compute_heat_flow(body: Optional[str] = None) -> Dict[str, Any]:
    """Per-body surface heat-flow ↔ tidal-heating decomposition.

    For a body with measured total surface heat flow + measured
    tidal-Q (v0.21.4), the heat flow constrains the energy-budget
    decomposition into tidal / radiogenic / primordial-cooling
    contributions.

    The cross-channel observation: v0.21.4 + v0.21.6 + v0.21.8 close
    the **tidal-energy-budget loop**. For Io, the v0.21.4 Q ≈ 80 +
    v0.21.6 +3.6 cm/yr outward migration imply tidal dissipation
    power that matches the v0.21.8 observed surface heat flow ~100 TW.

    **Io headline**: ~100 TW total — most volcanically active body
    in the solar system; almost entirely tidal heating from Jupiter.

    **Not a re-derivation.** Values shipped are published measurements
    / energy-budget model outputs from cited papers.

    6-body roster.

    Parameters
    ----------
    body : str, optional. Single-body lookup; else full roster.

    Returns
    -------
    dict
        Single body: ``{ok, body, heat_flow: {...}}``.
        Full roster: ``{ok, n_bodies, bodies: {name: {...}}}``.
    """
    if body is not None:
        name = str(body).lower().strip()
        if name not in _BY_BODY:
            return {
                "ok": False,
                "error": (
                    f"unknown body {body!r} in Sol Heat Flow Catalog; "
                    f"known bodies are {_ALL_BODIES}"
                ),
            }
        return {
            "ok": True,
            "body": name,
            "heat_flow": _to_dict(_BY_BODY[name]),
        }

    bodies: Dict[str, Dict[str, Any]] = {
        name: _to_dict(_BY_BODY[name]) for name in _ALL_BODIES
    }
    return {
        "ok": True,
        "n_bodies": len(_ALL_BODIES),
        "bodies": bodies,
    }


def list_heat_flows() -> Dict[str, Any]:
    """Full catalog enumeration of every published heat-flow record."""
    return {
        "ok": True,
        "n_bodies": len(_ALL_BODIES),
        "n_sources": len(SOURCES),
        "bodies": list(_ALL_BODIES),
        "heat_flows": [_to_dict(m) for m in HEAT_FLOWS],
    }


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "HEAT_FLOWS",
    "SOURCES",
    "HeatFlow",
    "compute_heat_flow",
    "list_heat_flows",
]
